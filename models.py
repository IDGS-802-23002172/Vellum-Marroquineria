from flask_sqlalchemy import SQLAlchemy
import datetime

db = SQLAlchemy()

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username  = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(50), nullable=False)
    intentos_fallidos=  db.Column(db.Integer, default=0)
    ultimo_acceso = db.Column(db.DateTime)
    esta_bloqueado = db.Column(db.Boolean, default=False)

# Tabla Producto
class Producto(db.Model):
    __tablename__ = 'productos'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    # Líneas: Executive, Lifestyle, Essentials [cite: 27, 110]
    linea = db.Column(db.String(50), nullable=False) 
    # Categorías: Portafolios, carteras, chamarras [cite: 29]
    categoria = db.Column(db.String(50), nullable=False)
    precio_venta = db.Column(db.Decimal(10, 2))
    stock_actual = db.Column(db.Integer, default=0)
    imagen = db.Column(db.String(255)) # Solo JPG y PNG 
    fecha_registro = db.Column(db.DateTime, default=datetime.datetime.now)