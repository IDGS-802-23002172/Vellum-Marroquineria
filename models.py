from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event
from datetime import datetime

db = SQLAlchemy()

# --- USUARIOS ---
class Usuario(db.Model):
    __tablename__ = "usuarios"
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

    
##-- COSILLAS PARA MATERIA PRIMA ------------------------##
##-------------------------------------------------------##
class UnidadMedida(SoftDeleteMixin, db.Model):
    __tablename__ = "unidades_medida"

    id_unidad = db.Column(db.SmallInteger, primary_key=True, autoincrement=True)

    nombre = db.Column(db.String(50), nullable=False, unique=True)
    abreviatura = db.Column(db.String(10), nullable=False, unique=True)

    tipo = db.Column(db.String(30), nullable=False)
    # peso, area, longitud, pieza

    def __repr__(self):
        return f"<Unidad {self.abreviatura}>"
    
class MateriaPrima(SoftDeleteMixin, db.Model):
    __tablename__ = "materias_primas"
    __table_args__ = (
        db.Index("idx_mp_nombre", "nombre"),
        db.Index("idx_mp_activo", "activo"),
    )

    id_materia = db.Column(db.Integer, primary_key=True, autoincrement=True)

    nombre = db.Column(db.String(150), nullable=False)
    descripcion = db.Column(db.String(250))

    id_unidad = db.Column(
        db.SmallInteger,
        db.ForeignKey("unidades_medida.id_unidad", ondelete="RESTRICT"),
        nullable=False
    )

    porcentaje_merma = db.Column(db.Numeric(5,2), default=0.00)

    creado_en = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    actualizado_en = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    unidad = db.relationship("UnidadMedida")

    def __repr__(self):
        return f"<MateriaPrima {self.nombre}>"
    
class StockMateriaPrima(db.Model):
    __tablename__ = "stock_materia_prima"

    id_materia = db.Column(
        db.Integer,
        db.ForeignKey("materias_primas.id_materia", ondelete="RESTRICT"),
        primary_key=True
    )

    cantidad_actual = db.Column(db.Numeric(14,2), nullable=False, default=0)

    punto_reorden = db.Column(db.Numeric(14,2), default=0)

    actualizado_en = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    materia = db.relationship("MateriaPrima", backref=db.backref("stock", uselist=False))
    
class MovimientoMateriaPrima(db.Model):
    __tablename__ = "movimientos_materia_prima"
    __table_args__ = (
        db.Index("idx_mov_mp_fecha", "fecha"),
    )

    id_movimiento = db.Column(db.Integer, primary_key=True)

    id_materia = db.Column(
        db.Integer,
        db.ForeignKey("materias_primas.id_materia", ondelete="RESTRICT"),
        nullable=False
    )

    id_proveedor = db.Column(
        db.Integer,
        db.ForeignKey("proveedores.id_proveedor", ondelete="RESTRICT"),
        nullable=True
    )

    tipo = db.Column(db.String(20), nullable=False)
    # COMPRA, PRODUCCION, AJUSTE, MERMA

    cantidad = db.Column(db.Numeric(14,2), nullable=False)

    costo_unitario = db.Column(db.Numeric(12,2))
    # importante para histórico real

    referencia = db.Column(db.String(150))

    fecha = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    materia = db.relationship("MateriaPrima", backref="movimientos")
    proveedor = db.relationship("Proveedor")    
    
##-- FIN DE COSILLAS DE MATERIA PRIMA------------------------------------##

# --- PRODUCTOS (UNIFICADO) ---
class Producto(db.Model):
    __tablename__ = 'productos'
    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(100), unique=True, nullable=False) # Ahora es obligatorio
    nombre = db.Column(db.String(100), nullable=False)
    linea = db.Column(db.String(50)) 
    categoria = db.Column(db.String(50))
    precio_venta = db.Column(db.Numeric(10, 2), nullable=False)
    stock_actual = db.Column(db.Integer, default=0) # Usar este nombre siempre
    imagen = db.Column(db.String(255)) 
    fecha_registro = db.Column(db.DateTime, default=datetime.now)
    detalles = db.relationship("DetalleVenta", backref="producto", lazy=True)

# --- VENTAS ---
class Venta(db.Model):
    __tablename__ = "ventas"
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    subtotal = db.Column(db.Numeric(10, 2))
    iva = db.Column(db.Numeric(10, 2))
    total = db.Column(db.Numeric(10, 2))
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    detalles = db.relationship("DetalleVenta", backref="venta", cascade="all, delete-orphan", lazy=True)

class DetalleVenta(db.Model):
    __tablename__ = "detalle_ventas"
    id = db.Column(db.Integer, primary_key=True)
    venta_id = db.Column(db.Integer, db.ForeignKey("ventas.id"), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey("productos.id"), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    precio_unitario = db.Column(db.Numeric(10, 2))
    subtotal = db.Column(db.Numeric(10, 2))

class CarritoTemporal(db.Model):
    __tablename__ = "carrito_temporal"
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(120), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey("productos.id"), nullable=False)
    nombre = db.Column(db.String(200))
    precio = db.Column(db.Numeric(10, 2))
    cantidad = db.Column(db.Integer)
    
