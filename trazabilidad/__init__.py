from flask import Blueprint

def init_app(app):
    from .routes import trazabilidad_bp
    app.register_blueprint(trazabilidad_bp)