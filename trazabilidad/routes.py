from flask import Blueprint, jsonify, render_template
from models import db, OrdenProduccion, AuditoriaVenta, Venta, Usuario, DetalleVenta, Producto

trazabilidad_bp = Blueprint(
    "trazabilidad",
    __name__,
    url_prefix="/trazabilidad",
    template_folder="../templates"
)

# ================= VISTA =================
@trazabilidad_bp.route("/", methods=["GET"])
def vista_trazabilidad():
    return render_template("trazabilidad/trazabilidad.html")


# ================= PRODUCCIÓN =================
@trazabilidad_bp.route("/ordenes-produccion", methods=["GET"])
def trazabilidad_ordenes_produccion():
    ordenes = db.session.query(OrdenProduccion).all()

    return jsonify([
        {
            "id_orden": o.id_orden,
            "producto": o.producto.nombre if o.producto else "N/A",
            "cantidad": o.cantidad,
            "estado": o.estado,
            "fecha": o.fecha_creacion,
            "creado_por": o.artesano_solicitante.username if o.artesano_solicitante else "N/A",
            "corte_por": o.artesano_corte.username if o.artesano_corte else "Pendiente",
            "finalizado_por": o.artesano_finalizador.username if o.artesano_finalizador else "Pendiente"
        }
        for o in ordenes
    ])


@trazabilidad_bp.route("/orden-produccion/<int:id_orden>", methods=["GET"])
def detalle_orden_produccion(id_orden):
    o = db.session.get(OrdenProduccion, id_orden)

    if not o:
        return jsonify({"error": "Orden no encontrada"}), 404

    return jsonify({
        "id_orden": o.id_orden,
        "producto": {
            "nombre": o.producto.nombre if o.producto else "N/A",
            "sku": o.producto.sku if o.producto else "N/A"
        },
        "solicitado_por": o.artesano_solicitante.username if o.artesano_solicitante else "N/A",
        "corte_por": o.artesano_corte.username if o.artesano_corte else "Pendiente",
        "finalizado_por": o.artesano_finalizador.username if o.artesano_finalizador else "Pendiente",
        "cantidad": o.cantidad,
        "estado": o.estado,
        "fecha": o.fecha_creacion
    })

# ================= AUDITORÍA (LISTADO) =================
@trazabilidad_bp.route("/auditoria-ventas", methods=["GET"])
def auditoria_ventas():

    auditorias = db.session.query(
        AuditoriaVenta.venta_id,
        Venta.folio,
        Usuario.username,
        AuditoriaVenta.accion,
        AuditoriaVenta.fecha
    )\
    .join(Venta, Venta.id == AuditoriaVenta.venta_id)\
    .join(Usuario, Usuario.id == AuditoriaVenta.usuario_id)\
    .all()

    return jsonify([
        {
            "venta_id": a.venta_id,
            "folio": a.folio,
            "usuario": a.username,
            "accion": a.accion,
            "fecha": a.fecha
        }
        for a in auditorias
    ])


# ================= AUDITORÍA (DETALLE) =================
@trazabilidad_bp.route("/auditoria-venta/<int:venta_id>", methods=["GET"])
def auditoria_venta_detalle(venta_id):

    venta = db.session.query(
        Venta.id,
        Venta.folio,
        Venta.fecha
    ).filter(Venta.id == venta_id).first()

    if not venta:
        return jsonify({"error": "Venta no encontrada"}), 404

    productos = db.session.query(
        Producto.nombre,
        DetalleVenta.cantidad,
        DetalleVenta.precio_unitario
    )\
    .select_from(DetalleVenta)\
    .join(Producto, Producto.id == DetalleVenta.producto_id)\
    .filter(DetalleVenta.venta_id == venta_id)\
    .all()

    historial = db.session.query(
        Usuario.username,
        AuditoriaVenta.accion,
        AuditoriaVenta.fecha
    )\
    .join(Usuario, Usuario.id == AuditoriaVenta.usuario_id)\
    .filter(AuditoriaVenta.venta_id == venta_id)\
    .all()

    return jsonify({
        "venta": {
            "id": venta.id,
            "folio": venta.folio,
            "fecha": venta.fecha
        },
        "productos": [
            {
                "nombre": p.nombre,
                "cantidad": p.cantidad,
                "precio": float(p.precio_unitario),
                "subtotal": float(p.cantidad * p.precio_unitario)
            }
            for p in productos
        ],
        "historial": [
            {
                "usuario": h.username,
                "accion": h.accion,
                "fecha": h.fecha
            }
            for h in historial
        ]
    })