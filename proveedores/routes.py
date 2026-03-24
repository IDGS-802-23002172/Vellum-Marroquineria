"""
Módulo: Proveedores
Blueprint Flask — CRUD completo
Empresa: Marroquinería de Autor, León Gto.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from sqlalchemy import or_
from models import db, Proveedor, EstadoMexico
from forms import ProveedorForm
import logging

proveedores_bp = Blueprint("proveedores", __name__, url_prefix="/")

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def _get_catalogos():
    """Devuelve catálogos activos para formularios."""
    estados = EstadoMexico.query.filter_by(activo=True) \
                                 .order_by(EstadoMexico.nombre).all()

    return estados


def _log(accion: str, id_registro: int = None, detalle: str = None):
    """Registro básico de auditoría."""
    try:
        user_id = session.get("user_id")

        logging.info(
            f"[AUDITORIA] Usuario:{user_id} | Acción:{accion} "
            f"| ID:{id_registro} | Detalle:{detalle} | IP:{request.remote_addr}"
        )
    except Exception as e:
        logging.error(f"Error en auditoría: {e}")


# ─────────────────────────────────────────────
# R — LISTADO
# URL: /proveedores
# ─────────────────────────────────────────────
@proveedores_bp.route("/proveedores")
def index():
    q = request.args.get("q", "").strip()
    solo_act = request.args.get("activos", "1")
    pagina = request.args.get("pagina", 1, type=int)
    por_pag = 10

    query = Proveedor.query

    if solo_act == "1":
        query = query.filter(Proveedor.activo.is_(True))

    if q:
        like = f"%{q}%"
        query = query.filter(
            or_(
                Proveedor.razon_social.ilike(like),
                Proveedor.nombre_contacto.ilike(like),
                Proveedor.ciudad.ilike(like),
                Proveedor.rfc.ilike(like),
            )
        )

    paginacion = query.order_by(Proveedor.razon_social) \
                      .paginate(page=pagina, per_page=por_pag, error_out=False)

    return render_template(
        "proveedores/index.html",
        proveedores=paginacion.items,
        paginacion=paginacion,
        q=q,
        solo_act=solo_act,
    )


# ─────────────────────────────────────────────
# C — CREAR
# ─────────────────────────────────────────────
@proveedores_bp.route('/proveedor_crear', methods=['GET', 'POST'])
def crear():
    form = ProveedorForm()
    estados = EstadoMexico.query.filter_by(activo=True).all()

    if form.validate_on_submit():
        raw_estado = request.form.get('id_estado')
        id_estado_limpio = int(raw_estado) if raw_estado and raw_estado.isdigit() else None

        nuevo_prov = Proveedor(
            razon_social=form.razon_social.data,
            nombre_contacto=form.nombre_contacto.data,
            telefono=form.telefono.data,
            correo=form.correo.data,
            rfc=form.rfc.data,
            direccion=request.form.get('direccion'),
            ciudad=request.form.get('ciudad'),
            id_estado=id_estado_limpio, 
            activo=True 
        )

        db.session.add(nuevo_prov)
        db.session.commit()
        
        flash("Proveedor registrado con éxito", "success")
        return redirect(url_for('proveedores.index'))
    

    if form.errors:
        print(f"Errores: {form.errors}")

    return render_template('proveedores/form.html', form=form, estados=estados, modo='crear')


# ─────────────────────────────────────────────
# R — DETALLE
# URL: /proveedores/<id>
# ─────────────────────────────────────────────
@proveedores_bp.route("/proveedores/<int:id_proveedor>")
def detalle(id_proveedor):
    prov = Proveedor.query.get_or_404(id_proveedor)
    return render_template("proveedores/detalle.html", prov=prov)


# ─────────────────────────────────────────────
# U — EDITAR
# ─────────────────────────────────────────────
@proveedores_bp.route("/proveedores/<int:id_proveedor>/editar", methods=["GET", "POST"])
def editar(id_proveedor):
    prov = Proveedor.query.get_or_404(id_proveedor)
    estados = _get_catalogos()
    form = ProveedorForm(obj=prov)

    if form.validate_on_submit():
        try:
            prov.razon_social = form.razon_social.data
            prov.nombre_contacto = form.nombre_contacto.data
            prov.telefono = form.telefono.data
            prov.correo = form.correo.data or None
            prov.rfc = (form.rfc.data.upper() if form.rfc.data else None)
            prov.direccion = form.direccion.data or None
            prov.ciudad = form.ciudad.data or None
            prov.id_estado = form.id_estado.data or None
            prov.notas = form.notas.data or None

            db.session.commit()
            _log("EDITAR", id_proveedor, "Proveedor actualizado")
            flash("Proveedor actualizado correctamente.", "success")
            return redirect(url_for('proveedores.detalle', id_proveedor=id_proveedor))

        except Exception as e:
            db.session.rollback()
            flash(f"Error al actualizar: {e}", "danger")

    return render_template(
        "proveedores/form.html",
        modo="editar", prov=prov, estados=estados,
        form=form
    )


# ─────────────────────────────────────────────
# D — SOFT DELETE
# ─────────────────────────────────────────────
@proveedores_bp.route("/proveedores/<int:id_proveedor>/eliminar", methods=["POST"])
def eliminar(id_proveedor):
    prov = Proveedor.query.get_or_404(id_proveedor)
    try:
        prov.activo = False
        db.session.commit()
        _log("DESACTIVAR", id_proveedor, "Proveedor desactivado")
        flash("Proveedor desactivado correctamente.", "warning")
    except Exception as e:
        db.session.rollback()
        flash(f"Error al eliminar: {e}", "danger")
    return redirect(url_for('proveedores.index'))


# ─────────────────────────────────────────────
# REACTIVAR
# ─────────────────────────────────────────────
@proveedores_bp.route("/proveedores/<int:id_proveedor>/reactivar", methods=["POST"])
def reactivar(id_proveedor):
    prov = Proveedor.query.get_or_404(id_proveedor)
    try:
        prov.activo = True
        db.session.commit()
        _log("REACTIVAR", id_proveedor, "Proveedor reactivado")
        flash("Proveedor reactivado.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error al reactivar: {e}", "danger")
    return redirect(url_for('proveedores.detalle', id_proveedor=id_proveedor))



# # D — SOFT DELETE
# # ─────────────────────────────────────────────
# @proveedores_bp.route("/eliminar/<int:id>", methods=["POST"])
# def eliminar(id):
#     proveedor = Proveedor.query.get_or_404(id)

#     try:
#         proveedor.soft_delete()
#         db.session.commit()

#         _log("SOFT_DELETE", id, "Proveedor desactivado")
#         flash("Proveedor desactivado correctamente.", "warning")

#     except Exception as e:
#         db.session.rollback()
#         flash(f"Error al eliminar: {e}", "danger")

#     return redirect(url_for("proveedores.index"))