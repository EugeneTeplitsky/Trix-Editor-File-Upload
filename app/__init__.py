import os
from flask import Flask
from flask_cors import CORS
from config import Config


def create_app(config_class=Config):
    app = Flask(__name__)
    CORS(app)  # Enable CORS for all routes and origins
    app.config.from_object(config_class)
    app.debug = config_class.DEBUG

    if not os.path.exists(os.path.join(config_class.BASE_DIR, config_class.UPLOAD_FOLDER)):
        os.makedirs(os.path.join(config_class.BASE_DIR, config_class.UPLOAD_FOLDER))

    # Initialize Flask extensions here
    from app.extensions import db, migrate, mail
    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)

    # Register blueprints here
    from .main import module as main
    app.register_blueprint(main)

    from .depot import module as depot
    app.register_blueprint(depot)

    return app
