from flask_wtf import FlaskForm 
from sqlalchemy import null
from wtforms import StringField, PasswordField, IntegerField, HiddenField, SelectField, DecimalField, TextAreaField
from flask_wtf.file import FileField, FileAllowed
from wtforms.validators import DataRequired, Length, NumberRange, Optional, Email

from wtforms import SubmitField
from wtforms.validators import NumberRange

class UserForm(FlaskForm):
    username = StringField('Username', [DataRequired(), Length(min=3, max=30)])
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
    
class UnidadMedidaForm(FlaskForm):
    nombre = StringField("Nombre", validators=[DataRequired(), Length(max=50)])
    abreviatura = StringField("Abreviatura", validators=[DataRequired(), Length(max=10)])
    tipo = SelectField("Tipo de Unidad",choices=[("piel", "Piel y cuero"),("quimico", "Quimicos y tintes"),("hilo", "Hilo y cordon")],validators=[DataRequired()])
    
class MateriaPrimaForm(FlaskForm):
    nombre = StringField("Nombre", validators=[DataRequired(), Length(max=150)])
    descripcion = StringField("Descripción", validators=[Optional(), Length(max=250)])
    id_unidad = SelectField("Unidad de Medida", coerce=int, validators=[DataRequired()])
    tipo_control = SelectField(
        "Control de existencia",
        choices=[("piel", "Piel y cuero"),("quimico", "Quimicos y tintes"),("hilo", "Hilo y cordon")],
        validators=[DataRequired()]
    )
    
class AjusteInventarioForm(FlaskForm):
    # Solo lo estrictamente necesario para el HTML que me pasaste
    cantidad = DecimalField("Cantidad/Área", validators=[DataRequired()])
    referencia = StringField("Motivo del ajuste", validators=[DataRequired(), Length(max=150)])
    
class MovimientoMateriaPrimaForm(FlaskForm):
    id_proveedor = SelectField(
        "Proveedor",
        coerce=int,
        validators=[Optional()]
    )

    tipo = SelectField(
        "Tipo de Movimiento",
        choices=[
            ("COMPRA", "Compra"),
            ("AJUSTE", "Ajuste Inventario")
        ],
        validators=[DataRequired()]
    )

    cantidad = DecimalField(
        "Cantidad",
        validators=[DataRequired()]
    )

    costo_unitario = DecimalField(
        "Costo Unitario",
        validators=[Optional()]
    )

    referencia = StringField(
        "Referencia",
        validators=[Optional(), Length(max=150)]
    )

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
    
class OrdenCompraForm(FlaskForm):
    """Cabecera de la orden de compra."""

    id_proveedor = SelectField(
        "Proveedor",
        coerce=int,
        validators=[DataRequired(message="Selecciona un proveedor")]
    )

    referencia_doc = StringField(
        "Folio / Factura del proveedor",
        validators=[Optional(), Length(max=100)]
    )

    notas = TextAreaField(
        "Notas / Observaciones",
        validators=[Optional(), Length(max=500)]
    )


class DetalleOrdenCompraForm(FlaskForm):
    """Una línea dentro de la orden."""

    id_materia = SelectField(
        "Materia Prima",
        coerce=int,
        validators=[DataRequired()]
    )

    cantidad = DecimalField(
        "Cantidad",
        validators=[DataRequired(), NumberRange(min=0.01, message="Debe ser mayor a 0")]
    )

    costo_unitario = DecimalField(
        "Costo Unitario",
        validators=[DataRequired(), NumberRange(min=0.01, message="Debe ser mayor a 0")]
    )

# Módulo de Producción - Semana 3
class OrdenProduccionForm(FlaskForm):
    id_producto = SelectField('Producto a Fabricar', coerce=int, validators=[DataRequired()])
    
    cantidad = IntegerField('Cantidad de Unidades', 
                            validators=[DataRequired(), NumberRange(min=1, message="Mínimo 1 unidad")])
    
    submit = SubmitField('Iniciar Producción')


