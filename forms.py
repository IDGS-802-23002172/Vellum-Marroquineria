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