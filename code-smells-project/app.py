from flask import Flask
from flask_cors import CORS

from config.settings import SECRET_KEY, DEBUG, HOST, PORT
from config.database import init_db
from config.logger import setup_logging
from middlewares.errors import register_error_handlers
from routes.api_routes import api


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = SECRET_KEY

    CORS(app)
    setup_logging()
    init_db(app)
    register_error_handlers(app)
    app.register_blueprint(api)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host=HOST, port=PORT, debug=DEBUG)
