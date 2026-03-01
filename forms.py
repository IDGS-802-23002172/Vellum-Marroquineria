from flask_wtf import FlaskForm 
from wtforms import StringField, PasswordField, IntegerField
from wtforms import validators

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
