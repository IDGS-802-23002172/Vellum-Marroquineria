# from models import db
# from datetime import datetime

# class Producto(db.Model):
#     __tablename__ = "productos"

#     id = db.Column(db.Integer, primary_key=True)
#     nombre = db.Column(db.String(200), nullable=False)
#     sku = db.Column(db.String(100), unique=True, nullable=False)
#     precio = db.Column(db.Numeric(10,2), nullable=False)
#     stock = db.Column(db.Integer, default=0)
    

# class Venta(db.Model):
#     __tablename__ = "ventas"

#     id = db.Column(db.Integer, primary_key=True)
#     fecha = db.Column(db.DateTime, default=datetime.utcnow)
#     subtotal = db.Column(db.Numeric(10,2))
#     iva = db.Column(db.Numeric(10,2))
#     total = db.Column(db.Numeric(10,2))
#     usuario_id = db.Column(db.Integer, nullable=False)

#     detalles = db.relationship("DetalleVenta", backref="venta", lazy=True)


# class DetalleVenta(db.Model):
#     __tablename__ = "detalle_ventas"

#     id = db.Column(db.Integer, primary_key=True)
#     venta_id = db.Column(db.Integer, db.ForeignKey("ventas.id"))
#     producto_id = db.Column(db.Integer, nullable=False)
#     cantidad = db.Column(db.Integer, nullable=False)
#     precio_unitario = db.Column(db.Numeric(10,2))
#     subtotal = db.Column(db.Numeric(10,2))


# class CarritoTemporal(db.Model):
#     __tablename__ = "carrito_temporal"

#     id = db.Column(db.Integer, primary_key=True)
#     session_id = db.Column(db.String(120), nullable=False)
#     producto_id = db.Column(db.Integer, nullable=False)
#     nombre = db.Column(db.String(200))
#     precio = db.Column(db.Numeric(10,2))
#     cantidad = db.Column(db.Integer)
#     stock_disponible = db.Column(db.Integer)