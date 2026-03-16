from flask_wtf import FlaskForm 
from sqlalchemy import null
from wtforms import StringField, PasswordField, IntegerField, HiddenField, SelectField, DecimalField
from flask_wtf.file import FileField, FileAllowed
from wtforms.validators import DataRequired, Length, Optional, Email

from wtforms import SubmitField
from wtforms.validators import NumberRange

class UserForm(FlaskForm):
    username = StringField('Username', [DataRequired(), Length(min=3, max=10)])
    password = PasswordField('Contraseña', [DataRequired()])

class ProveedorForm(FlaskForm):
    razon_social = StringField('Razón Social', [DataRequired(), Length(max=200)])
    nombre_contacto = StringField('Nombre de Contacto', [DataRequired()])
    rfc = StringField('RFC')
    direccion = StringField('Dirección') 
    ciudad = StringField('Ciudad') or null  
    id_estado = StringField('Estado', validators=[Optional()]) 
    telefono = StringField('Teléfono', [DataRequired()])
    correo = StringField('Correo', [Optional(), Email()])
    notas = StringField('Notas') 

class ProductoForm(FlaskForm):
    id = HiddenField('id')
    sku = StringField('SKU / Código', [DataRequired()])
    nombre = StringField('Nombre del Producto', [DataRequired()])
    linea = SelectField('Línea', choices=[('Executive', 'Executive'), ('Lifestyle', 'Lifestyle'), ('Essentials', 'Essentials')])
    categoria = SelectField('Categoría', choices=[('Portafolios', 'Portafolios'), ('Carteras', 'Carteras'), ('Chamarras', 'Chamarras')])
    precio = DecimalField('Precio de Venta', [DataRequired()])
    stock = IntegerField('Stock Inicial', [DataRequired()])
    imagen = FileField('Imagen', validators=[FileAllowed(['jpg', 'png', 'jpeg'], '¡Solo imágenes!')])

class RecetaForm(FlaskForm):
    id_producto = HiddenField('ID Producto', validators=[DataRequired()])
    id_materia = SelectField('Seleccionar Material', coerce=int, validators=[DataRequired()])
    area_plantilla = DecimalField(
        'Área de Plantilla (dm²)', 
        places=2, 
        validators=[DataRequired(), NumberRange(min=0.01, message="Debe ser mayor a 0")]
    )
    area_reticula = DecimalField(
        'Área de Retícula de Corte (dm²)', 
        places=2, 
        validators=[DataRequired(), NumberRange(min=0.01, message="Debe ser mayor a 0")]
    )
    submit = SubmitField('Asignar a Receta')

# Módulo de Producción - Semana 3
class OrdenProduccionForm(FlaskForm):
    id_producto = SelectField('Producto a Fabricar', coerce=int, validators=[DataRequired()])
    
    cantidad = IntegerField('Cantidad de Unidades', 
                            validators=[DataRequired(), NumberRange(min=1, message="Mínimo 1 unidad")])
    
    submit = SubmitField('Iniciar Producción')