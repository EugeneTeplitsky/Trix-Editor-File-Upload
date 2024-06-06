from flask import request, jsonify, current_app
from . import module


@module.before_request
def validate_security_token():
    """Validate the security token for POST requests."""
    if request.method == 'POST':
        token = request.headers.get('X-Security-Token')
        if token != current_app.config['SECURITY_TOKEN']:
            return jsonify({'error': 'Invalid security token'}), 401
