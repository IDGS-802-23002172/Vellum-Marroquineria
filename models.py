from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event, text
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

# --- USUARIOS ---
class Usuario(db.Model):
    __tablename__ = "usuarios"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    intentos_fallidos = db.Column(db.Integer, default=0)
    esta_bloqueado = db.Column(db.Boolean, default=False)
    ventas = db.relationship("Venta", backref="usuarios", lazy=True)
    id_rol = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)

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
class UnidadMedida(db.Model):
    __tablename__ = "unidades_medida"

    id_unidad = db.Column(db.SmallInteger, primary_key=True, autoincrement=True)

    nombre = db.Column(db.String(50), nullable=False, unique=True)
    abreviatura = db.Column(db.String(10), nullable=False, unique=True)

    tipo = db.Column(db.String(30), nullable=False)
    # peso, area, longitud, pieza

    creado_en = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Unidad {self.abreviatura}>"
    
class MateriaPrima(db.Model):
    __tablename__ = "materias_primas"

    __table_args__ = (
        db.Index("idx_mp_nombre", "nombre"),
    )

    id_materia = db.Column(db.Integer, primary_key=True, autoincrement=True)

    nombre = db.Column(db.String(150), nullable=False)
    descripcion = db.Column(db.String(250))

    id_unidad = db.Column(
        db.SmallInteger,
        db.ForeignKey("unidades_medida.id_unidad", ondelete="RESTRICT"),
        nullable=False
    )

    creado_en = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    actualizado_en = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    unidad = db.relationship("UnidadMedida")

    # Control de existencia: 'acumulable' = se suman cantidades, 'pieza' = se registran piezas individuales
    tipo_control = db.Column(
        db.String(20),
        nullable=False,
        default="acumulable"
    )

    def __repr__(self):
        return f"<MateriaPrima {self.nombre}>"
    
class StockMateriaPrima(db.Model):
    __tablename__ = "stock_materia_prima"

    id_materia = db.Column(
        db.Integer,
        db.ForeignKey("materias_primas.id_materia", ondelete="CASCADE"),
        primary_key=True
    )

    cantidad_actual = db.Column(
        db.Numeric(14,2),
        nullable=False,
        default=0
    )

    punto_reorden = db.Column(
        db.Numeric(14,2),
        nullable=False,
        default=0
    )

    actualizado_en = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    materia = db.relationship(
        "MateriaPrima",
        backref=db.backref("stock", uselist=False)
    )


class PiezaMateriaPrima(db.Model):
    __tablename__ = "piezas_materia_prima"

    id_pieza = db.Column(db.Integer, primary_key=True, autoincrement=True)

    id_materia = db.Column(
        db.Integer,
        db.ForeignKey("materias_primas.id_materia", ondelete="CASCADE"),
        nullable=False
    )

    area = db.Column(
        db.Numeric(14,2),
        nullable=False
    )

    disponible = db.Column(db.Boolean, nullable=False, default=True)

    creado_en = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # opcional: referencia al movimiento de entrada que creó la pieza
    id_movimiento_entrada = db.Column(
        db.Integer,
        db.ForeignKey("movimientos_materia_prima.id_movimiento", ondelete="SET NULL"),
        nullable=True
    )

    materia = db.relationship("MateriaPrima", backref=db.backref("piezas", lazy=True))

    
class MovimientoMateriaPrima(db.Model):
    __tablename__ = "movimientos_materia_prima"

    __table_args__ = (
        db.Index("idx_mov_mp_fecha", "fecha"),
        db.Index("idx_mov_mp_materia", "id_materia"),
    )

    id_movimiento = db.Column(db.Integer, primary_key=True)

    id_materia = db.Column(
        db.Integer,
        db.ForeignKey("materias_primas.id_materia", ondelete="RESTRICT"),
        nullable=False
    )

    id_proveedor = db.Column(
        db.Integer,
        db.ForeignKey("proveedores.id_proveedor", ondelete="SET NULL"),
        nullable=True
    )

    tipo = db.Column(
        db.String(20),
        nullable=False
    )
    # COMPRA, PRODUCCION, AJUSTE, MERMA

    cantidad = db.Column(
        db.Numeric(14,2),
        nullable=False
    )
    # positivo = entrada
    # negativo = salida

    costo_unitario = db.Column(
        db.Numeric(12,2)
    )

    referencia = db.Column(
        db.String(150)
    )
    # factura, orden producción, ajuste inventario

    fecha = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    materia = db.relationship(
        "MateriaPrima",
        backref="movimientos"
    )

    proveedor = db.relationship(
        "Proveedor")  
    
##-- FIN DE COSILLAS DE MATERIA PRIMA------------------------------------##

##-- CAJA ----------------------------------------------------------------##
"""
Modelos — Módulo de Compras (Semana 3)
Empresa: Marroquinería de Autor, León Gto.

Agregar estas clases al archivo models.py existente.
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# ── Referencia al db existente ─────────────────────
# from models import db, Proveedor, MateriaPrima, StockMateriaPrima, MovimientoMateriaPrima


# ─────────────────────────────────────────────────────────────────────────────
# ORDEN DE COMPRA
# Una orden agrupa N líneas de materia prima compradas al mismo proveedor.
# Al "confirmar" la orden se generan los MovimientoMateriaPrima y el
# MovimientoCaja correspondiente de forma atómica.
# ─────────────────────────────────────────────────────────────────────────────
class OrdenCompra(db.Model):
    __tablename__ = "ordenes_compra"

    id_orden = db.Column(db.Integer, primary_key=True, autoincrement=True)

    folio = db.Column(db.String(30), unique=True, nullable=False)
    # Ej: "OC-2025-0001"

    id_proveedor = db.Column(
        db.Integer,
        db.ForeignKey("proveedores.id_proveedor", ondelete="RESTRICT"),
        nullable=False
    )

    fecha = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Referencia documental: número de factura, remisión, etc.
    referencia_doc = db.Column(db.String(100), nullable=True)

    estado = db.Column(
        db.String(20),
        nullable=False,
        default="BORRADOR"
    )
    # BORRADOR → CONFIRMADA → CANCELADA

    subtotal   = db.Column(db.Numeric(14, 2), default=0, nullable=False)
    iva        = db.Column(db.Numeric(14, 2), default=0, nullable=False)
    total      = db.Column(db.Numeric(14, 2), default=0, nullable=False)

    notas = db.Column(db.Text, nullable=True)

    creado_por = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=True)
    creado_en  = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    confirmado_en = db.Column(db.DateTime, nullable=True)

    # Relaciones
    proveedor = db.relationship("Proveedor")
    detalles  = db.relationship(
        "DetalleOrdenCompra",
        backref="orden",
        cascade="all, delete-orphan",
        lazy=True
    )
    movimiento_caja = db.relationship(
        "MovimientoCaja",
        backref="orden",
        uselist=False
    )

    def __repr__(self):
        return f"<OrdenCompra {self.folio} | {self.estado}>"


class DetalleOrdenCompra(db.Model):
    __tablename__ = "detalle_ordenes_compra"

    id_detalle  = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_orden    = db.Column(
        db.Integer,
        db.ForeignKey("ordenes_compra.id_orden", ondelete="CASCADE"),
        nullable=False
    )
    id_materia  = db.Column(
        db.Integer,
        db.ForeignKey("materias_primas.id_materia", ondelete="RESTRICT"),
        nullable=False
    )

    cantidad       = db.Column(db.Numeric(14, 2), nullable=False)
    costo_unitario = db.Column(db.Numeric(12, 2),  nullable=False)
    subtotal       = db.Column(db.Numeric(14, 2),  nullable=False)

    # Referencia al movimiento generado al confirmar
    id_movimiento = db.Column(
        db.Integer,
        db.ForeignKey("movimientos_materia_prima.id_movimiento", ondelete="SET NULL"),
        nullable=True
    )

    materia    = db.relationship("MateriaPrima")
    movimiento = db.relationship("MovimientoMateriaPrima")

    def __repr__(self):
        return f"<DetalleOC {self.id_detalle} – {self.cantidad} u>"


# ─────────────────────────────────────────────────────────────────────────────
# MOVIMIENTO DE CAJA
# Registro simplificado de flujo de efectivo (entradas y salidas).
# Las compras generan una SALIDA automática al confirmar la orden.
# ─────────────────────────────────────────────────────────────────────────────
class MovimientoCaja(db.Model):
    __tablename__ = "movimientos_caja"

    id_movimiento_caja = db.Column(db.Integer, primary_key=True, autoincrement=True)

    tipo = db.Column(
        db.String(20),
        nullable=False
    )
    # ENTRADA | SALIDA

    concepto = db.Column(db.String(200), nullable=False)

    monto = db.Column(db.Numeric(14, 2), nullable=False)
    # Siempre positivo; el tipo determina el signo en reportes

    metodo_pago = db.Column(db.String(30), nullable=True)
    # EFECTIVO, TRANSFERENCIA, CHEQUE, TARJETA

    referencia = db.Column(db.String(150), nullable=True)

    # Vínculo opcional con una orden de compra
    id_orden = db.Column(
        db.Integer,
        db.ForeignKey("ordenes_compra.id_orden", ondelete="SET NULL"),
        nullable=True
    )

    fecha      = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    creado_por = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=True)
    notas      = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f"<MovCaja {self.tipo} ${self.monto}>"
 
 
# --- FIN DE CAJA --------------------
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
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
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
    

# --- EXPLOSION-MATERIALES ---
class Receta(db.Model):
    __tablename__ = "recetas"
    id_receta = db.Column(db.Integer, primary_key=True)
    id_producto = db.Column(db.Integer, db.ForeignKey("productos.id"), nullable=False)
    id_materia = db.Column(db.Integer, db.ForeignKey("materias_primas.id_materia"), nullable=False)
    area_plantilla_dm2 = db.Column(db.Numeric(10,2), nullable=False)
    area_reticula_corte_dm2 = db.Column(db.Numeric(10,2), nullable=False)
    producto = db.relationship("Producto", backref="receta_articulos")
    materia = db.relationship("MateriaPrima")

class RetalRecuperado(db.Model):
    __tablename__ = "retales_recuperados"
    id_retal = db.Column(db.Integer, primary_key=True)
    id_materia_origen = db.Column(db.Integer, db.ForeignKey("materias_primas.id_materia"))
    area_disponible_dm2 = db.Column(db.Numeric(10,2), nullable=False)
    es_reusable = db.Column(db.Boolean, default=True)
    fecha_registro = db.Column(db.DateTime, default=db.func.current_timestamp())

# --- ORDENES DE PRODUCCION ---
class OrdenProduccion(db.Model):
    __tablename__ = "ordenes_produccion"
    id_orden = db.Column(db.Integer, primary_key=True)
    id_producto = db.Column(db.Integer, db.ForeignKey("productos.id"), nullable=False)
    id_usuario = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    
    cantidad = db.Column(db.Integer, nullable=False)
    
    estado = db.Column(db.String(50), default="En Corte") 
    
    fecha_creacion = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    producto = db.relationship("Producto")
    artesano = db.relationship("Usuario")
    
    

class AuditoriaVenta(db.Model):
    __tablename__ = "auditoria_ventas"

    id = db.Column(db.Integer, primary_key=True)
    
    venta_id = db.Column(db.Integer, db.ForeignKey("ventas.id"), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    accion = db.Column(db.String(50))
    venta = db.relationship("Venta")
    usuario = db.relationship("Usuario")
    
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


class Rol (db.Model):
    __tablename__ = "roles"
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), unique=True, nullable=False)
    descripcion = db.Column(db.String(200))
    usuarios = db.relationship("Usuario", backref="rol")