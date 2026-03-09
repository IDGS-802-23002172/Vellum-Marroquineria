from flask import Blueprint

materiales = Blueprint(
    'materiales',
    __name__,
    template_folder='templates',
)
