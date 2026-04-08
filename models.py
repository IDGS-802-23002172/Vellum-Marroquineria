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
    creado_en = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    actualizado_en = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


##-- COSILLAS PARA MATERIA PRIMA ------------------------##
##-------------------------------------------------------##
class UnidadMedida(db.Model):
    __tablename__ = "unidades_medida"
    id_unidad = db.Column(db.SmallInteger, primary_key=True, autoincrement=True)
    nombre = db.Column(db.String(50), nullable=False, unique=True)
    abreviatura = db.Column(db.String(10), nullable=False, unique=True)
    tipo = db.Column(db.String(30), nullable=False)
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
    creado_en = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    actualizado_en = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    unidad = db.relationship("UnidadMedida")
    tipo_control = db.Column(db.String(20), nullable=False, default="acumulable")

    def __repr__(self):
        return f"<MateriaPrima {self.nombre}>"

class StockMateriaPrima(db.Model):
    __tablename__ = "stock_materia_prima"
    id_materia = db.Column(
        db.Integer,
        db.ForeignKey("materias_primas.id_materia", ondelete="CASCADE"),
        primary_key=True
    )
    cantidad_actual = db.Column(db.Numeric(14, 2), nullable=False, default=0)
    punto_reorden = db.Column(db.Numeric(14, 2), nullable=False, default=0)
    actualizado_en = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    materia = db.relationship("MateriaPrima", backref=db.backref("stock", uselist=False))


class PiezaMateriaPrima(db.Model):
    __tablename__ = "piezas_materia_prima"
    id_pieza = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_materia = db.Column(
        db.Integer,
        db.ForeignKey("materias_primas.id_materia", ondelete="CASCADE"),
        nullable=False
    )
    area = db.Column(db.Numeric(14, 2), nullable=False)
    disponible = db.Column(db.Boolean, nullable=False, default=True)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
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
    tipo = db.Column(db.String(20), nullable=False)
    cantidad = db.Column(db.Numeric(14, 2), nullable=False)
    costo_unitario = db.Column(db.Numeric(12, 2))
    referencia = db.Column(db.String(150))
    fecha = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    materia = db.relationship("MateriaPrima", backref="movimientos")
    proveedor = db.relationship("Proveedor")

##-- FIN DE COSILLAS DE MATERIA PRIMA------------------------------------##

##-- CAJA ----------------------------------------------------------------##

# ─────────────────────────────────────────────────────────────────────────────
# ORDEN DE COMPRA
# ─────────────────────────────────────────────────────────────────────────────
class OrdenCompra(db.Model):
    __tablename__ = "ordenes_compra"
    id_orden   = db.Column(db.Integer, primary_key=True, autoincrement=True)
    folio      = db.Column(db.String(30), unique=True, nullable=False)
    id_proveedor = db.Column(
        db.Integer,
        db.ForeignKey("proveedores.id_proveedor", ondelete="RESTRICT"),
        nullable=False
    )
    estado     = db.Column(db.String(20), nullable=False, default="BORRADOR")
    fecha      = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    total      = db.Column(db.Numeric(14, 2), nullable=False, default=0)
    notas      = db.Column(db.Text)
    creado_por = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=True)
    proveedor  = db.relationship("Proveedor")
    subtotal   = db.Column(db.Numeric(14, 2), nullable=False, default=0)
    iva        = db.Column(db.Numeric(14, 2), nullable=False, default=0)
    referencia_doc = db.Column(db.String(100), nullable=True) # Añade esta línea
    detalles   = db.relationship(
        "DetalleOrdenCompra",
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
# ─────────────────────────────────────────────────────────────────────────────
class MovimientoCaja(db.Model):
    __tablename__ = "movimientos_caja"
    id_movimiento_caja = db.Column(db.Integer, primary_key=True, autoincrement=True)
    tipo = db.Column(db.String(20), nullable=False)
    concepto = db.Column(db.String(200), nullable=False)
    monto = db.Column(db.Numeric(14, 2), nullable=False)
    metodo_pago = db.Column(db.String(30), nullable=True)
    referencia = db.Column(db.String(150), nullable=True)
    id_orden = db.Column(
        db.Integer,
        db.ForeignKey("ordenes_compra.id_orden", ondelete="SET NULL"),
        nullable=True
    )
    id_venta = db.Column(
        db.Integer,
        db.ForeignKey("ventas.id", ondelete="SET NULL"),
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
    sku = db.Column(db.String(100), unique=True, nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    linea = db.Column(db.String(50))
    categoria = db.Column(db.String(50))
    precio_venta = db.Column(db.Numeric(10, 2), nullable=False)
    costo_produccion = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    area_plantilla_base = db.Column(db.Numeric(10, 2), nullable=False)
    stock_actual = db.Column(db.Integer, default=0)
    imagen = db.Column(db.String(255))
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    
    detalles = db.relationship(
        "DetalleVenta",
        back_populates="producto",
        lazy=True
    )
    
    en_carritos = db.relationship(
        "CarritoTemporal",
        back_populates="producto",
        lazy="dynamic"
    )

    @property
    def stock_reservado(self):
        from datetime import timedelta
        hace_30_min = datetime.utcnow() - timedelta(minutes=30)
        return db.session.query(
            db.func.coalesce(db.func.sum(CarritoTemporal.cantidad), 0)
        ).filter(
            CarritoTemporal.producto_id == self.id,
            CarritoTemporal.creado_en >= hace_30_min
        ).scalar()

    @property
    def stock_disponible(self):
        return max(0, self.stock_actual - self.stock_reservado)


# --- VENTAS ---
class Venta(db.Model):
    __tablename__ = "ventas"
    id = db.Column(db.Integer, primary_key=True)
    folio = db.Column(db.String(30), unique=True, nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    estado = db.Column(db.String(50), default="Pagado") 
    
    detalles = db.relationship("DetalleVenta", backref="venta", cascade="all, delete-orphan", lazy=True)
    @property
    def porcentaje_progreso(self):
        """
        Retorna el porcentaje numérico basado en el estatus de fabricación.
        Ideal para el componente de Bootstrap en seguimiento.html
        """
        mapa_estados = {
            "Pagado": 25,
            "En confección": 50,
            "Listo para entrega": 75,
            "Entregado": 100
        }
        return mapa_estados.get(self.estado, 0)

class DetalleVenta(db.Model):
    __tablename__ = "detalle_ventas"
    id = db.Column(db.Integer, primary_key=True)
    venta_id = db.Column(db.Integer, db.ForeignKey("ventas.id"), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey("productos.id"), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    precio_unitario = db.Column(db.Numeric(10,2))
    costo_unitario = db.Column(db.Numeric(10,2))  # costo histórico
    producto = db.relationship(
        "Producto",back_populates="detalles")
    @property
    def subtotal(self):
        if self.cantidad and self.precio_unitario:
            return self.cantidad * self.precio_unitario
        return 0


# ─────────────────────────────────────────────────────────────────────────────
# CARRITO TEMPORAL
# Cada fila = un producto en el carrito de un usuario anónimo o logueado.
# La FK a productos permite eager-loading y el property stock_disponible
# del Producto descuenta automáticamente lo reservado por TODOS los carritos.
# ─────────────────────────────────────────────────────────────────────────────
class CarritoTemporal(db.Model):
    __tablename__ = "carrito_temporal"
    __table_args__ = (
        # Índice para acelerar las búsquedas por session_id
        db.Index("idx_carrito_session", "session_id"),
        # Índice para acelerar el cálculo de reservas por producto
        db.Index("idx_carrito_producto", "producto_id"),
    )

    id         = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(120), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey("productos.id"), nullable=False)
    nombre     = db.Column(db.String(200))
    precio     = db.Column(db.Numeric(10, 2))
    cantidad   = db.Column(db.Integer)
    creado_en  = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    actualizado_en = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # ✅ Relación con Producto — permite articulo.producto en templates
    producto = db.relationship(
        "Producto",
        back_populates="en_carritos",
        lazy="joined"   # joined = un solo JOIN, no N+1 queries
    )


# --- EXPLOSION-MATERIALES ---
class Receta(db.Model):
    __tablename__ = "recetas"
    id_receta = db.Column(db.Integer, primary_key=True)
    id_producto = db.Column(db.Integer, db.ForeignKey("productos.id"), nullable=False)
    id_materia = db.Column(db.Integer, db.ForeignKey("materias_primas.id_materia"), nullable=False)
    area_plantilla_dm2 = db.Column(db.Numeric(10, 2), nullable=False)
    area_reticula_corte_dm2 = db.Column(db.Numeric(10, 2), nullable=False)
    producto = db.relationship("Producto", backref="receta_articulos")
    materia = db.relationship("MateriaPrima")

class RetalRecuperado(db.Model):
    __tablename__ = "retales_recuperados"
    id_retal = db.Column(db.Integer, primary_key=True)
    id_materia_origen = db.Column(db.Integer, db.ForeignKey("materias_primas.id_materia"))
    area_disponible_dm2 = db.Column(db.Numeric(10, 2), nullable=False)
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
        
        -- CÁLCULO DIRECTO EN SQL PARA EVITAR LA REDUNDANCIA
        SUM(d.cantidad * d.precio_unitario) AS total_ventas,
        
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

class Rol(db.Model):
    __tablename__ = "roles"
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), unique=True, nullable=False)
    descripcion = db.Column(db.String(200))
    usuarios = db.relationship("Usuario", backref="rol")
    
class OrdenProduccion(db.Model):
    __tablename__ = 'orden_produccion'

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, nullable=False)
    producto_id = db.Column(db.Integer, nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    estado = db.Column(db.String(20), default='pendiente')
    fecha = db.Column(db.DateTime, default=datetime.utcnow)