import os
from . import module
from flask import request, jsonify, send_file, current_app
from werkzeug.utils import secure_filename
from .functions import generate_filename, clean_temp_files, allowed_file


@module.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and allowed_file(file.filename, current_app.config):
        filename = generate_filename(file)
        temp_filename = f"temp_{filename}"
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], temp_filename)
        try:
            file.save(file_path)
        except IOError as e:
            current_app.logger.error(f"Error saving file: {file_path}. {str(e)}")
            return jsonify({'error': 'File upload failed'}), 500
        return jsonify({'filename': filename}), 200

    return jsonify({'error': 'File type not allowed'}), 400


@module.route('/commit', methods=['POST'])
def commit_files():
    """Migrate temporary files to permanent storage."""
    filenames = request.json.get('filenames', [])
    if not filenames:
        return jsonify({'error': 'Missing filenames'}), 400

    committed_files = []
    for filename in filenames:
        temp_file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], f"temp_{filename}")
        permanent_file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)

        if not os.path.isfile(temp_file_path):
            current_app.logger.warning(f"Temporary file not found: {temp_file_path}")
            continue

        try:
            os.rename(temp_file_path, permanent_file_path)
            committed_files.append(filename)
        except OSError as e:
            current_app.logger.error(f"Error migrating temporary file: {temp_file_path}. {str(e)}")

    if not committed_files:
        return jsonify({'error': 'No files were committed'}), 500

    return jsonify({'message': 'Files committed successfully', 'committed_files': committed_files}), 200


@module.route('/files/<path:filename>')
def get_file(filename):
    """Retrieve an uploaded file."""
    filename = secure_filename(filename)
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)

    if os.path.isfile(file_path):
        return send_file(os.path.abspath(file_path))
    else:
        return jsonify({'error': 'File not found'}), 404
