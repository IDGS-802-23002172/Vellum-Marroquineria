"""
Módulo: Proveedores
Blueprint Flask — CRUD completo
Empresa: Marroquinería de Autor, León Gto.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from sqlalchemy import or_
from models import Proveedor, db, UnidadMedida
from models import MateriaPrima, StockMateriaPrima, MovimientoMateriaPrima, PiezaMateriaPrima
from forms import UnidadMedidaForm, MateriaPrimaForm, MovimientoMateriaPrimaForm
import logging

unidades_bp = Blueprint("unidades", __name__, url_prefix="/unidades")
# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def _log(accion: str, id_registro: int = None, detalle: str = None):
    try:
        user_id = session.get("user_id")

        logging.info(
            f"[AUDITORIA] Usuario:{user_id} | Acción:{accion} "
            f"| ID:{id_registro} | Detalle:{detalle} | IP:{request.remote_addr}"
        )

    except Exception as e:
        logging.error(f"Error en auditoría: {e}")
        

@unidades_bp.route("/")
def listar():

    q = request.args.get("q", "").strip()
    pagina = request.args.get("pagina", 1, type=int)

    consulta = UnidadMedida.query

    if q:
        consulta = consulta.filter(
            or_(
                UnidadMedida.nombre.ilike(f"%{q}%"),
                UnidadMedida.abreviatura.ilike(f"%{q}%")
            )
        )

    paginacion = consulta.order_by(UnidadMedida.nombre).paginate(
        page=pagina,
        per_page=10,
        error_out=False
    )

    unidades = paginacion.items

    return render_template(
        "unidades/index.html",
        unidades=unidades,
        paginacion=paginacion,
        q=q
    )
    

@unidades_bp.route("/crear", methods=["GET", "POST"])
def crear():

    form = UnidadMedidaForm()

    if form.validate_on_submit():

        unidad = UnidadMedida(
            nombre=form.nombre.data,
            abreviatura=form.abreviatura.data,
            tipo=form.tipo.data
        )

        db.session.add(unidad)
        db.session.commit()

        _log("CREAR_UNIDAD", unidad.id_unidad, unidad.nombre)

        flash("Unidad creada correctamente", "success")

        return redirect(url_for("unidades.listar"))

    return render_template(
        "unidades/form.html",
        form=form,
        modo="crear",
        titulo="Nueva Unidad de Medida"
    )
    

@unidades_bp.route("/editar/<int:id>", methods=["GET", "POST"])
def editar(id):

    unidad = UnidadMedida.query.get_or_404(id)

    form = UnidadMedidaForm(obj=unidad)

    if form.validate_on_submit():

        unidad.nombre = form.nombre.data
        unidad.abreviatura = form.abreviatura.data
        unidad.tipo = form.tipo.data

        db.session.commit()

        _log("EDITAR_UNIDAD", unidad.id_unidad, unidad.nombre)

        flash("Unidad actualizada correctamente", "success")

        return redirect(url_for("unidades.listar"))

    return render_template(
        "unidades/form.html",
        form=form,
        modo="editar",
        unidad=unidad,
        titulo="Editar Unidad"
        
    )
    

@unidades_bp.route("/eliminar/<int:id>", methods=["POST"])
def eliminar(id):

    unidad = UnidadMedida.query.get_or_404(id)

    try:

        db.session.delete(unidad)
        db.session.commit()

        _log("ELIMINAR_UNIDAD", id, unidad.nombre)

        flash("Unidad eliminada correctamente", "success")

    except Exception:

        db.session.rollback()

        flash(
            "No se puede eliminar porque está en uso por materias primas",
            "danger"
        )

    return redirect(url_for("unidades.listar"))


@unidades_bp.route("/detalle/<int:id>")
def detalle(id):

    unidad = UnidadMedida.query.get_or_404(id)

    return render_template(
        "unidades/detalle.html",
        unidad=unidad
    )
    

materias_bp = Blueprint("materias", __name__, url_prefix="/materias")

@materias_bp.get("/")
def index():

    q = request.args.get("q", "")
    pagina = request.args.get("pagina", 1, type=int)

    query = MateriaPrima.query

    if q:
        query = query.filter(MateriaPrima.nombre.ilike(f"%{q}%"))

    paginacion = query.order_by(
        MateriaPrima.nombre
    ).paginate(
        page=pagina,
        per_page=15
    )

    return render_template(
        "materias/index.html",
        materias=paginacion.items,
        paginacion=paginacion,
        q=q
    )

@materias_bp.route("/nueva", methods=["GET", "POST"])
def crear():

    form = MateriaPrimaForm()

    form.id_unidad.choices = [
        (u.id_unidad, f"{u.nombre} ({u.abreviatura})")
        for u in UnidadMedida.query.order_by(UnidadMedida.nombre)
    ]

    if form.validate_on_submit():

        materia = MateriaPrima(
            nombre=form.nombre.data,
            descripcion=form.descripcion.data,
            id_unidad=form.id_unidad.data,
            tipo_control=form.tipo_control.data
        )

        db.session.add(materia)
        db.session.commit()
        
        stock = StockMateriaPrima(
            id_materia=materia.id_materia,
            cantidad_actual=0,
            punto_reorden=0
        )

        db.session.add(stock)
        db.session.commit()

        flash("Materia prima registrada correctamente", "success")

        return redirect(url_for("materias.index"))

    return render_template(
        "materias/form.html",
        form=form,
        modo="crear"
    )

@materias_bp.get("/<int:id>")
def detalle(id):

    materia = MateriaPrima.query.get_or_404(id)

    movimientos = (
        MovimientoMateriaPrima.query
        .filter_by(id_materia=id)
        .order_by(MovimientoMateriaPrima.fecha.desc())
        .limit(10)
        .all()
    )

    return render_template(
        "materias/detalle.html",
        materia=materia,
        movimientos=movimientos
    )

@materias_bp.route("/<int:id>/editar", methods=["GET", "POST"])
def editar(id):

    materia = MateriaPrima.query.get_or_404(id)

    form = MateriaPrimaForm(obj=materia)

    form.id_unidad.choices = [
        (u.id_unidad, f"{u.nombre} ({u.abreviatura})")
        for u in UnidadMedida.query.order_by(UnidadMedida.nombre)
    ]

    if form.validate_on_submit():

        materia.nombre = form.nombre.data
        materia.descripcion = form.descripcion.data
        materia.id_unidad = form.id_unidad.data
        materia.tipo_control = form.tipo_control.data

        db.session.commit()

        flash("Materia prima actualizada", "success")

        return redirect(url_for("materias.detalle", id=materia.id_materia))

    return render_template(
        "materias/form.html",
        form=form,
        materia=materia,
        modo="editar"
    )
    
@materias_bp.post("/<int:id>/eliminar")
def eliminar(id):

    materia = MateriaPrima.query.get_or_404(id)

    if materia.movimientos:
        flash(
            "No se puede eliminar la materia prima porque tiene movimientos registrados",
            "danger"
        )
        return redirect(url_for("materias.detalle", id=id))

    db.session.delete(materia)
    db.session.commit()

    flash("Materia prima eliminada", "success")

    return redirect(url_for("materias.index"))

@materias_bp.route("/movimiento/<int:id_materia>", methods=["GET", "POST"])
def movimiento(id_materia):
    """
    Solo maneja AJUSTE de inventario (corrección manual de existencias).
    Las compras con proveedor y factura se gestionan en compras_bp.
    La merma se registra automáticamente desde el módulo de Producción.
    """
    materia = MateriaPrima.query.get_or_404(id_materia)
    form    = MovimientoMateriaPrimaForm()

    if form.validate_on_submit():
        cantidad = form.cantidad.data

        if not cantidad or cantidad <= 0:
            flash("La cantidad debe ser mayor a 0.", "danger")
            return render_template("materias/movimientos.html", form=form, materia=materia)

        stock = StockMateriaPrima.query.filter_by(id_materia=id_materia).first()

        if not stock:
            flash("No existe registro de stock para esta materia.", "danger")
            return redirect(url_for("materias.detalle", id=id_materia))

        # ── Materiales controlados por pieza ──────────────────────────────
        if materia.tipo_control == "pieza":
            mov = MovimientoMateriaPrima(
                id_materia=id_materia,
                tipo="AJUSTE",
                cantidad=cantidad,
                referencia=form.referencia.data or None,
            )
            db.session.add(mov)
            db.session.flush()

            pieza = PiezaMateriaPrima(
                id_materia=id_materia,
                area=cantidad,
                id_movimiento_entrada=mov.id_movimiento,
            )
            db.session.add(pieza)

            # Recalcular stock como conteo de piezas disponibles
            stock.cantidad_actual = (
                PiezaMateriaPrima.query
                .filter_by(id_materia=id_materia, disponible=True)
                .count()
            )

        # ── Materiales acumulables ─────────────────────────────────────────
        else:
            mov = MovimientoMateriaPrima(
                id_materia=id_materia,
                tipo="AJUSTE",
                cantidad=cantidad,
                referencia=form.referencia.data or None,
            )
            db.session.add(mov)
            # AJUSTE = sobreescribir la cantidad actual (no sumar)
            stock.cantidad_actual = cantidad

        db.session.commit()
        flash("Ajuste de inventario registrado correctamente.", "success")
        return redirect(url_for("materias.detalle", id=id_materia))

    return render_template("materias/movimientos.html", form=form, materia=materia)