from flask import Blueprint

ventas_bp = Blueprint(
    "ventas",
    __name__,
    template_folder="templates",
    static_folder="static"
)

from . import routes