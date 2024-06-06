import hashlib
import os
import datetime


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


def clean_temp_files(app):
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


def allowed_file(filename, config):
    """Check if the file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in config['ALLOWED_EXTENSIONS']

