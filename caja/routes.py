"""
Blueprint: compras
Módulo de Compras — Semana 3
Empresa: Marroquinería de Autor, León Gto.

Rutas:
  GET  /compras/                    → listado de órdenes
  GET  /compras/nueva               → formulario nueva orden
  POST /compras/nueva               → guardar orden en BORRADOR
  GET  /compras/<id>                → detalle de la orden
  POST /compras/<id>/confirmar      → confirmar orden (actualiza inventario + caja)
  POST /compras/<id>/cancelar       → cancelar orden (solo si BORRADOR)
  GET  /compras/<id>/editar         → editar cabecera (solo BORRADOR)
  POST /compras/<id>/editar         → guardar cambios cabecera
  POST /compras/<id>/linea          → agregar línea de detalle (AJAX / redirect)
  POST /compras/linea/<id>/eliminar → eliminar línea (solo BORRADOR)
  GET  /compras/caja                → historial de movimientos de caja
"""

from flask import (
    Blueprint, render_template, request, redirect,
    url_for, flash, session, jsonify
)
from sqlalchemy import or_
from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import joinedload
from models import (
    db, Proveedor, MateriaPrima,
    StockMateriaPrima, MovimientoMateriaPrima, PiezaMateriaPrima
)

# ── Importar los nuevos modelos (ya deben estar en models.py) ──
from models import OrdenCompra, DetalleOrdenCompra, MovimientoCaja

from forms import OrdenCompraForm, DetalleOrdenCompraForm

import logging

compras_bp = Blueprint("compras", __name__, url_prefix="/compras")


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _log(accion: str, id_registro=None, detalle: str = None):
    try:
        logging.info(
            f"[AUDITORIA] Usuario:{session.get('user_id')} | Acción:{accion} "
            f"| ID:{id_registro} | Detalle:{detalle} | IP:{request.remote_addr}"
        )
    except Exception as e:
        logging.error(f"Error en auditoría: {e}")


def _siguiente_folio() -> str:
    """Genera el siguiente folio OC-YYYY-NNNN."""
    anio = datetime.utcnow().year
    ultima = (
        OrdenCompra.query
        .filter(OrdenCompra.folio.like(f"OC-{anio}-%"))
        .order_by(OrdenCompra.id_orden.desc())
        .first()
    )
    if ultima:
        try:
            n = int(ultima.folio.split("-")[-1]) + 1
        except ValueError:
            n = 1
    else:
        n = 1
    return f"OC-{anio}-{n:04d}"


def _recalcular_totales(orden: OrdenCompra, pct_iva: int = 16):
    """Recalcula subtotal / iva / total de la orden desde sus detalles."""
    subtotal = sum(d.subtotal for d in orden.detalles)
    iva      = subtotal * Decimal(pct_iva) / 100
    orden.subtotal = subtotal
    orden.iva      = iva
    orden.total    = subtotal + iva


def _proveedores_choices():
    return [
        (p.id_proveedor, p.razon_social)
        for p in Proveedor.query.filter_by(activo=True).order_by(Proveedor.razon_social)
    ]


def _materias_choices():
    return [
        (m.id_materia, f"{m.nombre}  [{m.unidad.abreviatura}]")
        for m in MateriaPrima.query.order_by(MateriaPrima.nombre)
    ]


# ─────────────────────────────────────────────────────────────────────────────
# LISTADO
# ─────────────────────────────────────────────────────────────────────────────

@compras_bp.get("/")
def index():
    q      = request.args.get("q", "").strip()
    estado = request.args.get("estado", "")
    pagina = request.args.get("pagina", 1, type=int)

    consulta = OrdenCompra.query

    if q:
        consulta = consulta.join(Proveedor).filter(
            or_(
                OrdenCompra.folio.ilike(f"%{q}%"),
                OrdenCompra.referencia_doc.ilike(f"%{q}%"),
                Proveedor.razon_social.ilike(f"%{q}%"),
            )
        )

    if estado:
        consulta = consulta.filter(OrdenCompra.estado == estado)

    paginacion = consulta.order_by(
        OrdenCompra.fecha.desc()
    ).paginate(page=pagina, per_page=15, error_out=False)

    return render_template(
        "compras/index.html",
        ordenes=paginacion.items,
        paginacion=paginacion,
        q=q,
        estado=estado,
    )


# ─────────────────────────────────────────────────────────────────────────────
# NUEVA ORDEN  (cabecera + líneas en una sola vista dinámica)
# ─────────────────────────────────────────────────────────────────────────────

@compras_bp.route("/nueva", methods=["GET", "POST"])
def crear():
    form = OrdenCompraForm()
    form.id_proveedor.choices = _proveedores_choices()

    detalle_form = DetalleOrdenCompraForm(prefix="det")
    detalle_form.id_materia.choices = _materias_choices()

    if form.validate_on_submit():
        orden = OrdenCompra(
            folio           = _siguiente_folio(),
            id_proveedor    = form.id_proveedor.data,
            referencia_doc  = form.referencia_doc.data or None,
            notas           = form.notas.data or None,
            estado          = "BORRADOR",
            creado_por      = session.get("user_id"),
        )
        # Guardamos el % IVA en notas internas por simplicidad
        # (en producción conviene columna propia)

        db.session.add(orden)
        db.session.commit()

        _log("CREAR_ORDEN_COMPRA", orden.id_orden, orden.folio)
        flash(f"Orden {orden.folio} creada. Ahora agrega los materiales.", "success")
        return redirect(url_for("compras.detalle", id=orden.id_orden))

    return render_template(
        "compras/form.html",
        form=form,
        detalle_form=detalle_form,
        modo="crear",
    )


# ─────────────────────────────────────────────────────────────────────────────
# DETALLE
# ─────────────────────────────────────────────────────────────────────────────

@compras_bp.get("/<int:id>")
def detalle(id):
    orden = OrdenCompra.query.options(
        joinedload(OrdenCompra.proveedor),
        joinedload(OrdenCompra.detalles)
    ).get_or_404(id)
    form = OrdenCompraForm(obj=orden)
    form.id_proveedor.choices = _proveedores_choices()
    detalle_form = DetalleOrdenCompraForm(prefix="det")
    detalle_form.id_materia.choices = _materias_choices()

    return render_template(
        "compras/detalle.html",
        orden=orden,
        form=form,
        detalle_form=detalle_form,
    )


# ─────────────────────────────────────────────────────────────────────────────
# EDITAR CABECERA (solo BORRADOR)
# ─────────────────────────────────────────────────────────────────────────────

@compras_bp.route("/<int:id>/editar", methods=["GET", "POST"])
def editar(id):
    orden = OrdenCompra.query.get_or_404(id)

    if orden.estado != "BORRADOR":
        flash("Solo se pueden editar órdenes en estado BORRADOR.", "warning")
        return redirect(url_for("compras.detalle", id=id))

    form = OrdenCompraForm(obj=orden)
    form.id_proveedor.choices = _proveedores_choices()

    if form.validate_on_submit():
        orden.id_proveedor   = form.id_proveedor.data
        orden.referencia_doc = form.referencia_doc.data or None
        orden.notas          = form.notas.data or None

        _recalcular_totales(orden)

        db.session.commit()
        _log("EDITAR_ORDEN_COMPRA", orden.id_orden, orden.folio)
        flash("Orden actualizada.", "success")
        return redirect(url_for("compras.detalle", id=id))

    return render_template(
        "compras/form.html",
        form=form,
        orden=orden,
        modo="editar",
    )


# ─────────────────────────────────────────────────────────────────────────────
# AGREGAR LÍNEA DE DETALLE
# ─────────────────────────────────────────────────────────────────────────────

@compras_bp.post("/<int:id>/linea")
def agregar_linea(id):
    orden = OrdenCompra.query.get_or_404(id)

    if orden.estado != "BORRADOR":
        flash("No se pueden agregar líneas a una orden ya confirmada o cancelada.", "warning")
        return redirect(url_for("compras.detalle", id=id))

    form = DetalleOrdenCompraForm(prefix="det")
    form.id_materia.choices = _materias_choices()

    if form.validate_on_submit():
        cantidad       = form.cantidad.data
        costo_unitario = form.costo_unitario.data
        subtotal_linea = cantidad * costo_unitario

        linea = DetalleOrdenCompra(
            id_orden       = orden.id_orden,
            id_materia     = form.id_materia.data,
            cantidad       = cantidad,
            costo_unitario = costo_unitario,
            subtotal       = subtotal_linea,
        )
        db.session.add(linea)

        # Recalcular totales de la orden (sin IVA aún; se aplica al confirmar)
        subtotal = sum(d.subtotal for d in orden.detalles)
        orden.subtotal = subtotal
        orden.iva      = subtotal * Decimal("0.16")
        orden.total    = orden.subtotal + orden.iva

        db.session.commit()
        flash("Material agregado a la orden.", "success")
    else:
        for field, errors in form.errors.items():
            for e in errors:
                flash(f"{field}: {e}", "danger")

    return redirect(url_for("compras.detalle", id=id))


# ─────────────────────────────────────────────────────────────────────────────
# ELIMINAR LÍNEA
# ─────────────────────────────────────────────────────────────────────────────

@compras_bp.post("/linea/<int:id_detalle>/eliminar")
def eliminar_linea(id_detalle):
    linea = DetalleOrdenCompra.query.get_or_404(id_detalle)
    id_orden = linea.id_orden
    orden    = OrdenCompra.query.get_or_404(id_orden)

    if orden.estado != "BORRADOR":
        flash("No se pueden eliminar líneas de una orden ya confirmada.", "warning")
        return redirect(url_for("compras.detalle", id=id_orden))

    db.session.delete(linea)

    # Recalcular
    subtotal = sum(
        d.subtotal for d in orden.detalles if d.id_detalle != id_detalle
    )
    orden.subtotal = subtotal
    orden.iva      = subtotal * Decimal("0.16")
    orden.total    = orden.subtotal + orden.iva

    db.session.commit()
    flash("Línea eliminada.", "success")
    return redirect(url_for("compras.detalle", id=id_orden))


# ─────────────────────────────────────────────────────────────────────────────
# CONFIRMAR ORDEN  ← lógica central de la semana 3
#   1. Valida que haya líneas
#   2. Por cada línea → crea MovimientoMateriaPrima (COMPRA) y actualiza stock
#   3. Crea MovimientoCaja (SALIDA) por el total
#   4. Cambia estado a CONFIRMADA
#   Todo en una sola transacción atómica.
# ─────────────────────────────────────────────────────────────────────────────
@compras_bp.post("/<int:id>/confirmar")
def confirmar(id):
    orden = OrdenCompra.query.get_or_404(id)

    if orden.estado != "BORRADOR":
        flash("La orden ya fue confirmada o cancelada.", "warning")
        return redirect(url_for("compras.detalle", id=id))

    if not orden.detalles:
        flash("Agrega al menos un material antes de confirmar.", "danger")
        return redirect(url_for("compras.detalle", id=id))

    try:
        # 1. Movimiento de Caja (SALIDA por pago al proveedor)
        caja = MovimientoCaja(
            tipo="SALIDA",
            concepto=f"Pago OC {orden.folio} – {orden.proveedor.razon_social}",
            monto=orden.total,
            referencia=orden.referencia_doc,
            id_orden=orden.id_orden,
            fecha=datetime.utcnow(),
            creado_por=session.get("user_id"),
            notas=orden.notas,
        )
        db.session.add(caja)

        # 2. Procesar líneas de detalle
        for linea in orden.detalles:
            materia = linea.materia
            
            # Asegurar existencia de registro en StockMateriaPrima
            stock = StockMateriaPrima.query.filter_by(id_materia=linea.id_materia).first()
            if not stock:
                stock = StockMateriaPrima(id_materia=linea.id_materia, cantidad_actual=0)
                db.session.add(stock)
                db.session.flush()

            # Registrar Movimiento de Inventario (Kardex)
            mov = MovimientoMateriaPrima(
                id_materia=linea.id_materia,
                id_proveedor=orden.id_proveedor,
                tipo="COMPRA",
                cantidad=linea.cantidad,
                costo_unitario=linea.costo_unitario,
                referencia=orden.folio,
                fecha=datetime.utcnow(),
            )
            db.session.add(mov)
            db.session.flush() # Para obtener mov.id_movimiento
            
            linea.id_movimiento = mov.id_movimiento
            if materia.tipo_control == 'piel' or materia.tipo_control == 'textil':
                # LA CORRECCIÓN: 
                # La cantidad (ej. 23.5) es el ÁREA de esa pieza específica.
                # Se crea UNA sola pieza con esa área.
                nueva_pieza = PiezaMateriaPrima(
                    id_materia=linea.id_materia,
                    area=linea.cantidad, # Aquí guardamos los 23dm2
                    id_movimiento_entrada=mov.id_movimiento,
                    disponible=True
                )
                db.session.add(nueva_pieza)
                
                # El stock aumenta en 1 unidad física (la hoja de piel)
                stock.cantidad_actual += 1
            else:
                # Químicos/Hilos: Suma normal (litros, metros, etc.)
                stock.cantidad_actual += linea.cantidad

        # 3. Finalizar Orden
        orden.estado = "CONFIRMADA"
        orden.confirmado_en = datetime.utcnow()

        db.session.commit()
        _log("CONFIRMAR_ORDEN_COMPRA", orden.id_orden, orden.folio)
        flash(f"✅ Orden {orden.folio} confirmada. Inventario y Caja actualizados.", "success")

    except Exception as exc:
        db.session.rollback()
        logging.exception("Error al confirmar orden de compra")
        flash(f"Error crítico al confirmar: {exc}", "danger")

    return redirect(url_for("compras.detalle", id=id))

# ─────────────────────────────────────────────────────────────────────────────
# CANCELAR ORDEN (solo BORRADOR)
# ─────────────────────────────────────────────────────────────────────────────

@compras_bp.post("/<int:id>/cancelar")
def cancelar(id):
    orden = OrdenCompra.query.get_or_404(id)

    if orden.estado != "BORRADOR":
        flash("Solo se pueden cancelar órdenes en estado BORRADOR.", "warning")
        return redirect(url_for("compras.detalle", id=id))

    orden.estado = "CANCELADA"
    db.session.commit()

    _log("CANCELAR_ORDEN_COMPRA", orden.id_orden, orden.folio)
    flash(f"Orden {orden.folio} cancelada.", "info")
    return redirect(url_for("compras.index"))


# ─────────────────────────────────────────────────────────────────────────────
# HISTORIAL DE CAJA
# ─────────────────────────────────────────────────────────────────────────────

@compras_bp.get("/caja")
def caja():
    q      = request.args.get("q", "").strip()
    tipo   = request.args.get("tipo", "")
    pagina = request.args.get("pagina", 1, type=int)

    consulta = MovimientoCaja.query

    if q:
        consulta = consulta.filter(
            or_(
                MovimientoCaja.concepto.ilike(f"%{q}%"),
                MovimientoCaja.referencia.ilike(f"%{q}%"),
            )
        )
    if tipo:
        consulta = consulta.filter(MovimientoCaja.tipo == tipo)

    paginacion = consulta.order_by(
        MovimientoCaja.fecha.desc()
    ).paginate(page=pagina, per_page=20, error_out=False)

    # Totales del período visible
    todos    = consulta.all()
    entradas = sum(m.monto for m in todos if m.tipo == "ENTRADA")
    salidas  = sum(m.monto for m in todos if m.tipo in ["SALIDA", "CIERRE"])

    return render_template(
        "compras/caja.html",
        movimientos=paginacion.items,
        paginacion=paginacion,
        q=q,
        tipo=tipo,
        entradas=entradas,
        salidas=salidas,
        saldo=entradas - salidas,
    )