from flask_wtf import FlaskForm 
from wtforms import StringField, PasswordField, IntegerField, HiddenField, SelectField, DecimalField
from flask_wtf.file import FileField, FileAllowed
from wtforms import validators
from wtforms.validators import DataRequired, Length, Optional, Email

class UserForm(FlaskForm):
    id = IntegerField('id')
    username = StringField('Username', [
        validators.DataRequired(message="Este campo es requerido"),
        validators.length(min=3, max=10, message="Longitud de 3 a 10 caracteres")
    ])
    password = PasswordField('Contraseña', [
        validators.DataRequired(message="Este campo es requerido")
    ])
    
class ProveedorForm(FlaskForm):
    razon_social = StringField('Razón Social', [
        validators.DataRequired(message="La razón social es obligatoria"),
        validators.Length(max=200)
    ])
    nombre_contacto = StringField('Nombre de Contacto', [
        validators.DataRequired(message="El nombre de contacto es obligatorio"),
        validators.Length(max=150)
    ])
    telefono = StringField('Teléfono', [
        validators.DataRequired(message="El teléfono es obligatorio"),
        validators.Length(max=20)
    ])
    correo = StringField('Correo Electrónico', [
        validators.Optional(),
        validators.Email(message="Ingrese un correo válido"),
        validators.Length(max=150)
    ])
    rfc = StringField('RFC', [
        validators.Optional(),
        validators.Length(min=12, max=13, message="El RFC debe tener entre 12 y 13 caracteres")
    ])
    direccion = StringField('Dirección', [
        validators.Optional(),
        validators.Length(max=300)
    ])
    ciudad = StringField('Ciudad', [
        validators.Optional(),
        validators.Length(max=100)
    ])
    id_estado = IntegerField('Estado ID', [validators.Optional()])
    notas = StringField('Notas', [validators.Optional()])

class ProductoForm(FlaskForm):
    id = HiddenField('id')
    nombre = StringField('Nombre del Producto', [DataRequired()])
    linea = SelectField('Línea', choices=[
        ('Executive', 'Executive'),
        ('Lifestyle', 'Lifestyle'),
        ('Essentials', 'Essentials')
    ])
    categoria = SelectField('Categoría', choices=[
        ('Portafolios', 'Portafolios'),
        ('Carteras', 'Carteras'),
        ('Chamarras', 'Chamarras')
    ])
    precio = DecimalField('Precio de Venta', [DataRequired()])
    imagen = FileField('Imagen del Producto', validators=[
        FileAllowed(['jpg', 'png'], '¡Solo se permiten imágenes JPG o PNG!')
    ])