from flask import Blueprint

module = Blueprint('main', __name__)

from app.main import routes, commands, middleware
