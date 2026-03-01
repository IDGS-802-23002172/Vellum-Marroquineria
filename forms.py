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

class ProductoForm(Form):
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
    # Validación específica para JPG y PNG 
    imagen = FileField('Imagen del Producto', validators=[
        FileAllowed(['jpg', 'png'], '¡Solo se permiten imágenes JPG o PNG!')
    ])