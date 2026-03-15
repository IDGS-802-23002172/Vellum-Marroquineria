from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event, text
from datetime import datetime

db = SQLAlchemy()

# --- USUARIOS ---
class Usuario(db.Model):
    __tablename__ = "usuario"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(50), nullable=False)
    intentos_fallidos = db.Column(db.Integer, default=0)
    esta_bloqueado = db.Column(db.Boolean, default=False)
    ventas = db.relationship("Venta", backref="usuario", lazy=True)

# --- PROVEEDORES ---
class SoftDeleteMixin:
    activo = db.Column(db.Boolean, nullable=False, default=True)
    eliminado_en = db.Column(db.DateTime)

class EstadoMexico(SoftDeleteMixin, db.Model):
    __tablename__ = "estados_mexico"
    id_estado = db.Column(db.SmallInteger, primary_key=True, autoincrement=True)
    nombre = db.Column(db.String(60), nullable=False, unique=True)

class Proveedor(SoftDeleteMixin, db.Model):
    __tablename__ = "proveedores"
    id_proveedor = db.Column(db.Integer, primary_key=True, autoincrement=True)
    razon_social = db.Column(db.String(200), nullable=False)
    nombre_contacto = db.Column(db.String(150), nullable=False)
    telefono = db.Column(db.String(20), nullable=False)
    correo = db.Column(db.String(150), unique=True)
    rfc = db.Column(db.String(13))
    direccion = db.Column(db.String(300)) 
    ciudad = db.Column(db.String(100))
    notas = db.Column(db.Text) 
    id_estado = db.Column(db.SmallInteger, db.ForeignKey("estados_mexico.id_estado"))
    materiales = db.relationship("ProveedorTipoMaterial", back_populates="proveedor")
    
class TipoMaterialProveedor(SoftDeleteMixin, db.Model):
    __tablename__ = "tipo_material_proveedor"
    id_tipo = db.Column(db.SmallInteger, primary_key=True, autoincrement=True)
    nombre = db.Column(db.String(80), nullable=False, unique=True)
    descripcion = db.Column(db.String(200))

class ProveedorTipoMaterial(db.Model):
    __tablename__ = "proveedor_tipo_material"
    id_proveedor = db.Column(db.Integer, db.ForeignKey("proveedores.id_proveedor"), primary_key=True)
    id_tipo = db.Column(db.SmallInteger, db.ForeignKey("tipo_material_proveedor.id_tipo"), primary_key=True)
    proveedor = db.relationship("Proveedor", back_populates="materiales")
    tipo_material = db.relationship("TipoMaterialProveedor")

# --- PRODUCTOS (UNIFICADO) ---
class Producto(db.Model):
    __tablename__ = 'productos'
    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(100), unique=True, nullable=False) # Ahora es obligatorio
    nombre = db.Column(db.String(100), nullable=False)
    linea = db.Column(db.String(50)) 
    categoria = db.Column(db.String(50))
    precio_venta = db.Column(db.Numeric(10,2), nullable=False)
    costo_produccion = db.Column(db.Numeric(10,2), nullable=False, default=0) # se agrego el campo para calcular las utilidades
    stock_actual = db.Column(db.Integer, default=0)
    imagen = db.Column(db.String(255))
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    detalles = db.relationship(
        "DetalleVenta",
        back_populates="producto",
        lazy=True
    )
# --- VENTAS ---
class Venta(db.Model):
    __tablename__ = "ventas"
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    subtotal = db.Column(db.Numeric(10, 2))
    iva = db.Column(db.Numeric(10, 2))
    total = db.Column(db.Numeric(10, 2))
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False)
    detalles = db.relationship("DetalleVenta", backref="venta", cascade="all, delete-orphan", lazy=True)

class DetalleVenta(db.Model):
    __tablename__ = "detalle_ventas"
    id = db.Column(db.Integer, primary_key=True)
    venta_id = db.Column(db.Integer, db.ForeignKey("ventas.id"), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey("productos.id"), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    precio_unitario = db.Column(db.Numeric(10,2))
    costo_unitario = db.Column(db.Numeric(10,2))  # costo histórico
    subtotal = db.Column(db.Numeric(10,2))
    producto = db.relationship(
        "Producto",back_populates="detalles")

class CarritoTemporal(db.Model):
    __tablename__ = "carrito_temporal"
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(120), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey("productos.id"), nullable=False)
    nombre = db.Column(db.String(200))
    precio = db.Column(db.Numeric(10, 2))
    cantidad = db.Column(db.Integer)

class AuditoriaVenta(db.Model):
    __tablename__ = "auditoria_ventas"
    
    id = db.Column(db.Integer, primary_key=True)
    venta_id = db.Column(db.Integer)
    usuario_id = db.Column(db.Integer)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    accion = db.Column(db.String(50))


@event.listens_for(Venta, "after_insert")
def registrar_auditoria(mapper, connection, target):

    connection.execute(
        AuditoriaVenta.__table__.insert(),
        {
            "venta_id": target.id,
            "usuario_id": target.usuario_id,
            "fecha": datetime.utcnow(),
            "accion": "VENTA_REGISTRADA"
        }
    )


def crear_vista_cierre_diario():

    sql = """
    CREATE OR REPLACE VIEW vista_cierre_diario AS
    SELECT 
        DATE(v.fecha) AS fecha,

        SUM(d.cantidad) AS articulos_vendidos,

        SUM(d.subtotal) AS total_ventas,

        SUM(
            (d.precio_unitario - d.costo_unitario) * d.cantidad
        ) AS utilidad_total

    FROM ventas v
    JOIN detalle_ventas d ON v.id = d.venta_id

    WHERE DATE(v.fecha) = CURDATE()

    GROUP BY DATE(v.fecha);
    """

    db.session.execute(text(sql))
    db.session.commit()

