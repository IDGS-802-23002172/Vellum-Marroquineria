from flask import Flask
from .ventas import ventas_bp

def create_app():
    app = Flask(__name__)

    app.register_blueprint(ventas_bp, url_prefix="/ventas")

    return app