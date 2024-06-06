import requests
import os
import uuid
from .models import db, File
from flask import current_app, jsonify
from sqlalchemy import exc
from app.extensions import mail
from app.main.functions import generate_filename


def loader(file, bundle: str = ''):
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if not validate_bundle_hash(bundle):
        return jsonify({'error': 'Invalid bundle hash'}), 400

    filename = f'depot_{generate_filename(file)}'
    file_path = os.path.join(current_app.config['BASE_DIR'], current_app.config['UPLOAD_FOLDER'], filename)
    abs_path = os.path.abspath(file_path)
    file_db = db.session.scalar(db.select(File).filter_by(path=abs_path, bundle_hash=bundle))

    if file_db is not None:
        return jsonify({'id': f'{file_db.unique}{file_db.id}'}), 200

    exists = db.session.query(db.session.query(File).filter_by(path=abs_path).exists()).scalar()
    file_db = File(name=file.filename, path=abs_path, bundle_hash=bundle)

    try:
        file.save(str(file_path))
        db.session.add(file_db)
        db.session.commit()
    except IOError as e:
        current_app.logger.error(f"Error saving file: {abs_path}. {str(e)}")
        return jsonify({'error': 'File upload failed'}), 500
    except exc.SQLAlchemyError as e:
        if not exists and os.path.isfile(abs_path):
            os.remove(abs_path)
        current_app.logger.error(f"Error saving the file to the database: {file_path}. {str(e)}")
        return jsonify({'error': 'File upload failed'}), 500

    return jsonify({'id': f'{file_db.unique}{file_db.id}'}), 200


def validate_bundle_hash(bundle_hash: str) -> bool:
    """
    Validate the bundle hash.
    """
    # Assuming the bundle hash should be a string of a specific length
    return isinstance(bundle_hash, str) and len(bundle_hash) == 64


def check_identifier(identifier: str) -> bool:
    if not isinstance(identifier, str) or len(identifier) < 37:
        return False
    try:
        int(identifier[36:])
        return True
    except ValueError:
        return False


def parse_identifier(identifier: str) -> tuple:
    return int(identifier[36:]), uuid.UUID(identifier[0: 36])


def send_email(email, message):
    try:
        if current_app.config['MAILGUN_API_KEY']:
            # Send email using Mailgun API
            response = requests.post(
                f"https://api.mailgun.net/v3/{current_app.config['MAILGUN_DOMAIN']}/messages",
                auth=("api", current_app.config['MAILGUN_API_KEY']),
                data={
                    "from": current_app.config['SENDER_EMAIL'],
                    "to": [email],
                    "subject": message.subject,
                    "html": message.html
                }
            )
            response.raise_for_status()
        else:
            # Send email using the normal mail function
            with current_app.app_context():
                mail.send(message)

        current_app.logger.info(f"Confirmation email sent to {email}")
    except Exception as e:
        current_app.logger.error(f"Error sending confirmation email: {str(e)}")
        raise
