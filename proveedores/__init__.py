from flask import Blueprint

proovedores = Blueprint(
    'proovedores',
    __name__,
    template_folder='proovedores_templates',
)
