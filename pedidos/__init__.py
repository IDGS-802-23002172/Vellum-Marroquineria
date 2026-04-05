from .routes import pedidos_bp


def init_app(app):
    app.register_blueprint(pedidos_bp)