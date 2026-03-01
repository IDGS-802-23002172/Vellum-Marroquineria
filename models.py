from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event
from datetime import datetime

db = SQLAlchemy()

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username  = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(50), nullable=False)
    intentos_fallidos=  db.Column(db.Integer, default=0)
    ultimo_acceso = db.Column(db.DateTime)
    esta_bloqueado = db.Column(db.Boolean, default=False)
    
    
""" ------------------ CLASES PARA PROOVEDORES -----------------"""
""" ------------------------------------------------------------"""
# ─────────────────────────────────────────────────────────────
#  TABLA AUXILIAR: estados_mexico
# ─────────────────────────────────────────────────────────────

class SoftDeleteMixin:
    activo = db.Column(db.Boolean, nullable=False, default=True)
    eliminado_en = db.Column(db.DateTime)

    def soft_delete(self):
        self.activo = False
        self.eliminado_en = datetime.utcnow()

class EstadoMexico(SoftDeleteMixin, db.Model):
    __tablename__ = "estados_mexico"
    __table_args__ = (
        db.Index("idx_estado_nombre", "nombre"),
    )

    id_estado = db.Column(db.SmallInteger, primary_key=True, autoincrement=True)
    nombre    = db.Column(db.String(60), nullable=False, unique=True)

    def __repr__(self):
        return f"<Estado {self.nombre}>"

    @staticmethod
    def seed():
        if EstadoMexico.query.first():
            return

        estados = [
            "Aguascalientes", "Baja California", "Baja California Sur",
            "Campeche", "Chiapas", "Chihuahua", "Ciudad de México",
            "Coahuila", "Colima", "Durango", "Guanajuato", "Guerrero",
            "Hidalgo", "Jalisco", "México", "Michoacán", "Morelos",
            "Nayarit", "Nuevo León", "Oaxaca", "Puebla", "Querétaro",
            "Quintana Roo", "San Luis Potosí", "Sinaloa", "Sonora",
            "Tabasco", "Tamaulipas", "Tlaxcala", "Veracruz",
            "Yucatán", "Zacatecas",
        ]

        db.session.bulk_insert_mappings(
            EstadoMexico,
            [{"nombre": e} for e in estados]
        )
        db.session.commit()


# Evita DELETE físico
@event.listens_for(EstadoMexico, "before_delete")
def prevent_delete_estado(mapper, connection, target):
    raise Exception("No se permite eliminar estados. Use soft_delete().")


# ─────────────────────────────────────────────────────────────
#  TABLA AUXILIAR: tipo_material_proveedor
# ─────────────────────────────────────────────────────────────
class TipoMaterialProveedor(SoftDeleteMixin, db.Model):
    __tablename__ = "tipo_material_proveedor"
    __table_args__ = (
        db.Index("idx_tipo_material_nombre", "nombre"),
    )

    id_tipo     = db.Column(db.SmallInteger, primary_key=True, autoincrement=True)
    nombre      = db.Column(db.String(80), nullable=False, unique=True)
    descripcion = db.Column(db.String(200))

    def __repr__(self):
        return f"<TipoMaterial {self.nombre}>"

    @staticmethod
    def seed():
        if TipoMaterialProveedor.query.first():
            return

        tipos = [
            ("Piel Bovina", "Cuero de res para portafolios y chamarras"),
            ("Piel Porcina", "Cuero de cerdo, textura fina para forros"),
            ("Piel Napa", "Piel de cordero, suave para carteras y accesorios"),
            ("Piel Gamuza", "Acabado aterciopelado para detalles"),
            ("Cuero Sintético", "PU o vinílico"),
            ("Herrajes", "Broches, cierres, argollas"),
            ("Hilos", "Hilos de nylon o cuero"),
            ("Tintes y Acabados", "Ceras y selladores"),
            ("Pegamentos", "Adhesivos especiales"),
            ("Empaque", "Cajas y bolsas"),
        ]

        db.session.bulk_insert_mappings(
            TipoMaterialProveedor,
            [{"nombre": n, "descripcion": d} for n, d in tipos]
        )
        db.session.commit()


# ─────────────────────────────────────────────────────────────
#  TABLA INTERMEDIA (Association Object Pattern)
# ─────────────────────────────────────────────────────────────
class ProveedorTipoMaterial(db.Model):
    __tablename__ = "proveedor_tipo_material"

    id_proveedor = db.Column(
        db.Integer,
        db.ForeignKey("proveedores.id_proveedor", ondelete="CASCADE"),
        nullable=False
    )

    id_tipo = db.Column(
        db.SmallInteger,
        db.ForeignKey("tipo_material_proveedor.id_tipo", ondelete="CASCADE"),
        nullable=False
    )

    precio_base = db.Column(db.Numeric(10, 2))
    lead_time_dias = db.Column(db.Integer)
    preferente = db.Column(db.Boolean, default=False)

    creado_en = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    actualizado_en = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    __table_args__ = (
        db.PrimaryKeyConstraint("id_proveedor", "id_tipo"),
    )

    proveedor = db.relationship("Proveedor", back_populates="materiales")
    tipo_material = db.relationship("TipoMaterialProveedor")

    def __repr__(self):
        return f"<ProveedorTipoMaterial proveedor={self.id_proveedor} tipo={self.id_tipo}>"


# ─────────────────────────────────────────────────────────────
#  TABLA PRINCIPAL: proveedores
# ─────────────────────────────────────────────────────────────
class Proveedor(SoftDeleteMixin, db.Model):
    __tablename__ = "proveedores"
    __table_args__ = (
        db.Index("idx_prov_activo", "activo"),
        db.Index("idx_prov_razon_social", "razon_social"),
        db.Index("idx_prov_ciudad", "ciudad"),
    )

    id_proveedor    = db.Column(db.Integer, primary_key=True, autoincrement=True)
    razon_social    = db.Column(db.String(200), nullable=False)
    nombre_contacto = db.Column(db.String(150), nullable=False)
    telefono        = db.Column(db.String(20), nullable=False)
    correo          = db.Column(db.String(150), unique=True)
    rfc             = db.Column(db.String(13), unique=True)
    direccion       = db.Column(db.String(300))
    ciudad          = db.Column(db.String(100))

    id_estado = db.Column(
        db.SmallInteger,
        db.ForeignKey("estados_mexico.id_estado", ondelete="SET NULL"),
        nullable=True
    )

    notas = db.Column(db.Text)

    creado_en = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    actualizado_en = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # Relaciones
    estado = db.relationship(
        "EstadoMexico",
        backref="proveedores",
        lazy="selectin",
        passive_deletes=True
    )

    materiales = db.relationship(
        "ProveedorTipoMaterial",
        back_populates="proveedor",
        cascade="all, delete-orphan"
    )

    # Acceso directo a tipos
    @property
    def tipos_material(self):
        return [rel.tipo_material for rel in self.materiales if rel.tipo_material.activo]

    @property
    def materiales_str(self):
        return ", ".join(t.nombre for t in self.tipos_material) or "—"

    @property
    def estado_nombre(self):
        return self.estado.nombre if self.estado else "—"

    def __repr__(self):
        return f"<Proveedor #{self.id_proveedor} {self.razon_social}>"


        
""" ------------- Fin del módulo de modelos para proveedores -------------- """

# Tabla Producto
class Producto(db.Model):
    __tablename__ = 'productos'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    # Líneas: Executive, Lifestyle, Essentials [cite: 27, 110]
    linea = db.Column(db.String(50), nullable=False) 
    # Categorías: Portafolios, carteras, chamarras [cite: 29]
    categoria = db.Column(db.String(50), nullable=False)
    precio_venta = db.Column(db.Numeric(10, 2))
    stock_actual = db.Column(db.Integer, default=0)
    imagen = db.Column(db.String(255)) # Solo JPG y PNG 
    fecha_registro = db.Column(db.DateTime, default=datetime.now)
