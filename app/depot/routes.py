import os
from . import module
from .models import File, db, Download
from flask import request, jsonify, send_file, current_app, render_template
from sqlalchemy import exc
from knishioclient.models import Molecule
from knishioclient.exception import BaseError
from json import JSONEncoder
from .functions import send_email, check_identifier, parse_identifier, validate_bundle_hash, loader
from flask_mail import Message


@module.route('/upload/files', methods=['POST'])
def upload_files():
    if 'molecule' not in request.files:
        return jsonify({'error': 'The molecule has not been transferred'}), 400

    data = request.files['molecule']
    molecule = data.stream.read()

    try:
        molecule = Molecule.json_to_object(molecule.decode())
        molecule.check()
    except BaseError as e:
        current_app.logger.error(f'Error molecule.check(): {type(e)}')
        return jsonify({'error': 'Incorrect molecule'}), 400

    result = {}

    for name, file in request.files.items():
        if name == 'molecule':
            continue

        response, status = loader(file, molecule.bundle)
        json = response.get_json()

        if 'error' in json:
            filename = 'without a name' if file.filename == '' else file.filename

            if 'error' in result.keys():
                result['error'][filename] = json['error']
            else:
                result['error'] = {filename: json['error']}
            continue

        if 'uploaded' in result:
            result['uploaded'][file.filename] = json['id']
        else:
            result['uploaded'] = {file.filename: json['id']}

    return jsonify(result), 200


@module.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    if 'molecule' not in request.files:
        return jsonify({'error': 'The molecule has not been transferred'}), 400

    file = request.files['file']
    data = request.files['molecule']
    molecule = data.stream.read()

    try:
        molecule = Molecule.json_to_object(molecule.decode())
        molecule.check()
    except BaseError as e:
        current_app.logger.error(f'Error molecule.check(): {type(e)}')
        return jsonify({'error': 'Incorrect molecule'}), 400

    return loader(file, molecule.bundle)


@module.route('/removal/<string:identifier>', methods=['DELETE'])
def soft_removal(identifier: str):
    if not check_identifier(identifier):
        return jsonify({'error': 'invalid file ID'}), 400

    main_id, unique_id = parse_identifier(identifier)
    file = db.session.scalar(db.select(File).filter_by(id=main_id, unique=unique_id))

    if file is not None and os.path.isfile(file.path):
        data = request.get_json()

        if not isinstance(data, dict) or 'molecule' not in data:
            return jsonify({'error': 'molecule is a required parameter'}), 400

        try:
            molecule = Molecule.json_to_object(JSONEncoder().encode(data['molecule']))
            molecule.check()
        except BaseError as e:
            current_app.logger.error(f"Error molecule.check(): {type(e)}")
            return jsonify({'error': 'Incorrect molecule'}), 400

        if file.bundle_hash != molecule.bundle:
            return jsonify({'error': 'The file does not belong to the user'}), 400

        isotope = None

        for atom in molecule.atoms:
            if atom.isotope == 'M':
                isotope = atom

        if isotope is None or 'email' not in isotope.meta or 'product_name' not in isotope.meta or\
                'product_link' not in isotope.meta:
            return jsonify({'error': 'Incorrect molecule data'}), 400

        message = Message(
            sender=current_app.config['SENDER_EMAIL'],
            subject='Product change warning.',
            recipients=[isotope.meta['email']]
        )
        message.html = render_template(
            'notifications_changes_email.html',
            product_name=isotope.meta['product_name'],
            product_link=isotope.meta['product_link']
        )

        send_email(isotope.meta['email'], message)
        return jsonify({'status': 'The message has been sent'}), 200

    return jsonify({'error': 'File not found'}), 404


@module.route('/entry', methods=['POST'])
def entry():
    data = request.get_json()

    if not isinstance(data, dict) or 'identifier' not in data or 'bundle' not in data:
        return jsonify({'error': 'identifier and bundle are required parameters'}), 400

    identifier, bundle = str(data['identifier']), str(data['bundle'])

    if not validate_bundle_hash(bundle):
        return jsonify({'error': 'Invalid bundle hash'}), 400
    if not check_identifier(identifier):
        return jsonify({'error': 'invalid file ID'}), 400

    main_id, unique_id = parse_identifier(identifier)
    file = db.session.scalar(db.select(File).filter_by(id=main_id, unique=unique_id))

    if file is None or not os.path.isfile(file.path):
        return jsonify({'error': f'there is no file with this id({identifier})'}), 400


@module.route('/files/<string:bundle>', methods=['GET'])
def get_files(bundle: str):
    if not validate_bundle_hash(bundle):
        return jsonify({'error': 'Invalid bundle hash'}), 400
    files = db.session.scalars(db.select(File).where(File.downloads.any(Download.bundle_hash == bundle)))

    return [f'{file.unique}{file.id}' for file in files], 200


@module.route('/file/<string:bundle>/<string:identifier>', methods=['GET'])
def skip_file(bundle: str, identifier: str):
    if not check_identifier(identifier):
        return jsonify({'error': 'invalid file ID'}), 400
    if not validate_bundle_hash(bundle):
        return jsonify({'error': 'Invalid bundle hash'}), 400

    main_id, unique_id = parse_identifier(identifier)
    file = db.session.scalar(db.select(File).filter_by(id=main_id, unique=unique_id, bundle_hash=bundle))

    if file is not None and os.path.isfile(file.path):
        return send_file(file.path)

    return jsonify({'error': 'File not found'}), 404


@module.route('/file/<string:identifier>', methods=['POST'])
def get_file(identifier: str):
    """Retrieve an uploaded file."""
    if not check_identifier(identifier):
        return jsonify({'error': 'invalid file ID'}), 400

    main_id, unique_id = parse_identifier(identifier)
    file = db.session.scalar(db.select(File).filter_by(id=main_id, unique=unique_id))

    if file is not None and os.path.isfile(file.path):
        data = request.get_json()

        if not isinstance(data, dict) or 'molecule' not in data:
            return jsonify({'error': 'molecule is a required parameter'}), 400

        try:
            molecule = Molecule.json_to_object(JSONEncoder().encode(data['molecule']))
            molecule.check()
        except BaseError as e:
            current_app.logger.error(f"Error molecule.check(): {type(e)}")
            return jsonify({'error': 'Incorrect molecule'}), 400

        for download in db.session.scalars(file.downloads.select()).all():
            if download.bundle_hash == molecule.bundle:
                download.download_count += 1

                if download.download_max is not None and download.download_max < download.download_count:
                    continue
                try:
                    db.session.add(download)
                    db.session.commit()
                except exc.SQLAlchemyError as e:
                    current_app.logger.error(f"Error saving the download model to the database: {str(e)}")
                    return jsonify({'error': 'Error saving to the database'}), 500

                return send_file(file.path)

    return jsonify({'error': 'File not found'}), 404
