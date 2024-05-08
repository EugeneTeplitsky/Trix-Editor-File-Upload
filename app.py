import os
import hashlib
import datetime
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import click

load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes and origins

app.config.from_pyfile('config.py')

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])


@app.before_request
def validate_security_token():
    """Validate the security token for POST requests."""
    if request.method == 'POST':
        token = request.headers.get('X-Security-Token')
        if token != app.config['SECURITY_TOKEN']:
            return jsonify({'error': 'Invalid security token'}), 401


def allowed_file(filename):
    """Check if the file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


@app.cli.command('clean-temp-files')
def clean_temp_files_command():
    """CLI command to remove temporary files that have expired."""
    clean_temp_files()
    click.echo('Temporary files cleaned successfully.')


def clean_temp_files():
    """Remove temporary files that have expired."""
    now = datetime.datetime.now()
    for filename in os.listdir(app.config['UPLOAD_FOLDER']):
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if os.path.isfile(file_path) and filename.startswith('temp_'):
            file_created_time = datetime.datetime.fromtimestamp(os.path.getctime(file_path))
            if (now - file_created_time).days >= app.config['TEMP_FILE_EXPIRATION']:
                try:
                    os.remove(file_path)
                except OSError as e:
                    app.logger.error(f"Error removing temporary file: {file_path}. {str(e)}")


def generate_filename(file):
    """Generate a unique filename based on the file content."""
    file_hash = hashlib.md5()
    while True:
        chunk = file.read(8192)
        if not chunk:
            break
        file_hash.update(chunk)
    file.seek(0)
    return f"{file_hash.hexdigest()}.{file.filename.rsplit('.', 1)[1].lower()}"


@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and allowed_file(file.filename):
        filename = generate_filename(file)
        temp_filename = f"temp_{filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], temp_filename)
        try:
            file.save(file_path)
        except IOError as e:
            app.logger.error(f"Error saving file: {file_path}. {str(e)}")
            return jsonify({'error': 'File upload failed'}), 500
        return jsonify({'filename': filename}), 200

    return jsonify({'error': 'File type not allowed'}), 400


@app.route('/commit', methods=['POST'])
def commit_files():
    """Migrate temporary files to permanent storage."""
    filenames = request.json.get('filenames', [])
    if not filenames:
        return jsonify({'error': 'Missing filenames'}), 400

    committed_files = []
    for filename in filenames:
        temp_file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"temp_{filename}")
        permanent_file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        if not os.path.isfile(temp_file_path):
            app.logger.warning(f"Temporary file not found: {temp_file_path}")
            continue

        try:
            os.rename(temp_file_path, permanent_file_path)
            committed_files.append(filename)
        except OSError as e:
            app.logger.error(f"Error migrating temporary file: {temp_file_path}. {str(e)}")

    if not committed_files:
        return jsonify({'error': 'No files were committed'}), 500

    return jsonify({'message': 'Files committed successfully', 'committed_files': committed_files}), 200


@app.route('/files/<path:filename>')
def get_file(filename):
    """Retrieve an uploaded file."""
    filename = secure_filename(filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.isfile(file_path):
        return send_file(file_path)
    else:
        return jsonify({'error': 'File not found'}), 404


if __name__ == '__main__':
    app.run()
