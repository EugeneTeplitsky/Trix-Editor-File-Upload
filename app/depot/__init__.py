from flask import Blueprint

module = Blueprint('depot', __name__, url_prefix='/depot', template_folder='templates')

from . import models, routes
