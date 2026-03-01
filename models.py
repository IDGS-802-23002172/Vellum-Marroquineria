from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# ==============================
# USUARIOS
# ==============================

class Usuario(db.Model):
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(50), nullable=False)
    intentos_fallidos = db.Column(db.Integer, default=0)
    ultimo_acceso = db.Column(db.DateTime)
    esta_bloqueado = db.Column(db.Boolean, default=False)

    ventas = db.relationship("Venta", backref="usuario", lazy=True)


# ==============================
# PRODUCTOS
# ==============================

class Producto(db.Model):
    __tablename__ = "productos"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(200), nullable=False)
    sku = db.Column(db.String(100), unique=True, nullable=False)
    precio = db.Column(db.Numeric(10, 2), nullable=False)
    stock = db.Column(db.Integer, default=0)

    detalles = db.relationship("DetalleVenta", backref="producto", lazy=True)


# ==============================
# VENTAS
# ==============================

class Venta(db.Model):
    __tablename__ = "ventas"

    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    subtotal = db.Column(db.Numeric(10, 2))
    iva = db.Column(db.Numeric(10, 2))
    total = db.Column(db.Numeric(10, 2))

    usuario_id = db.Column(
        db.Integer,
        db.ForeignKey("usuarios.id"),
        nullable=False
    )

    detalles = db.relationship(
        "DetalleVenta",
        backref="venta",
        cascade="all, delete-orphan",
        lazy=True
    )


# ==============================
# DETALLE DE VENTA
# ==============================

class DetalleVenta(db.Model):
    __tablename__ = "detalle_ventas"

    id = db.Column(db.Integer, primary_key=True)

    venta_id = db.Column(
        db.Integer,
        db.ForeignKey("ventas.id"),
        nullable=False
    )

    producto_id = db.Column(
        db.Integer,
        db.ForeignKey("productos.id"),
        nullable=False
    )

    cantidad = db.Column(db.Integer, nullable=False)
    precio_unitario = db.Column(db.Numeric(10, 2))
    subtotal = db.Column(db.Numeric(10, 2))


# ==============================
# CARRITO TEMPORAL (PUNTO DE VENTA)
# ==============================

class CarritoTemporal(db.Model):
    __tablename__ = "carrito_temporal"

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(120), nullable=False)

    producto_id = db.Column(
        db.Integer,
        db.ForeignKey("productos.id"),
        nullable=False
    )

    nombre = db.Column(db.String(200))
    precio = db.Column(db.Numeric(10, 2))
    cantidad = db.Column(db.Integer)
    stock_disponible = db.Column(db.Integer)