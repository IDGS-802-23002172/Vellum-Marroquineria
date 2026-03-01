from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SubmitField
from wtforms.validators import DataRequired, NumberRange

class BuscarProductoForm(FlaskForm):
    busqueda = StringField("Buscar producto", validators=[DataRequired()])
    submit = SubmitField("Buscar")

class AgregarProductoForm(FlaskForm):
    producto_id = IntegerField(validators=[DataRequired()])
    cantidad = IntegerField(
        "Cantidad",
        validators=[DataRequired(), NumberRange(min=1)]
    )
    submit = SubmitField("Agregar")