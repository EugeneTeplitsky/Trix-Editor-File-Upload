import app
import os
import config
from flask.cli import load_dotenv

load_dotenv()

if __name__ == '__main__':
    conf = config.DevelopmentConfig
    FLASK_ENV = os.environ.get('FLASK_ENV') or ''

    if FLASK_ENV.lower() == 'production':
        conf = config.ProductionConfig

    application = app.create_app(conf)
    application.run()
