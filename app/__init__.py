print("app/__init__.py loaded")
from flask_cors import CORS
from flask import Flask
from .config import db

def create_app():
    app = Flask(__name__)

    CORS(app, origins=["https://frontend-i3fb.onrender.com"])   #spremeni
    from .routes import main
    app.register_blueprint(main)

    return app
