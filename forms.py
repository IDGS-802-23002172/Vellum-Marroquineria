from flask_wtf import FlaskForm 
from sqlalchemy import null
from wtforms import StringField, PasswordField, IntegerField, HiddenField, SelectField, DecimalField
from flask_wtf.file import FileField, FileAllowed
from wtforms.validators import DataRequired, Length, Optional, Email

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