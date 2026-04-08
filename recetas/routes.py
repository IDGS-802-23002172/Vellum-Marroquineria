from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import db, Producto, MateriaPrima, Receta
import forms

recetas_bp = Blueprint("recetas", __name__)

# ─────────────────────────────────────────────
# LISTADO (R)
# ─────────────────────────────────────────────
@recetas_bp.route("/recetas")
def listar_recetas():
    productos_con_receta = Producto.query.filter(Producto.receta_articulos.any()).all()
    return render_template("recetas/index.html", productos=productos_con_receta)

# vista de detalle para mostrar que insumos tiene cada producto

@recetas_bp.route("/recetas/detalle/<int:id_producto>")
def detalle_receta(id_producto):
    producto = Producto.query.get_or_404(id_producto)
    insumos = Receta.query.filter_by(id_producto=id_producto).all()
    return render_template("recetas/detalle.html", producto=producto, insumos=insumos)

# ─────────────────────────────────────────────
# CREAR (C) - Soporta múltiples materiales por producto
# ─────────────────────────────────────────────
@recetas_bp.route("/recetas/nuevo", methods=['GET', 'POST'])
def crear_receta():
    p_id_seleccionado = request.args.get('p_id', type=int)
    form = forms.RecetaForm(request.form)
    
    form.id_producto.choices = [(p.id, f"{p.sku} - {p.nombre}") for p in Producto.query.all()]
    materiales = MateriaPrima.query.all()
    form.id_materia.choices = [(m.id_materia, f"{m.nombre} ({m.unidad.abreviatura})") for m in materiales]
    productos = Producto.query.all()
    form.id_producto.choices = [(p.id, p.nombre) for p in productos]

    insumos_actuales = []
    if p_id_seleccionado:
        form.id_producto.data = p_id_seleccionado
        insumos_actuales = Receta.query.filter_by(id_producto=p_id_seleccionado).all()

    if request.method == 'POST' and form.validate():
        try:
            producto = Producto.query.get(form.id_producto.data)
            
            # Insumo principal (piel)
            nueva_receta = Receta(
                id_producto=producto.id,
                id_materia=form.id_materia.data,
                area_plantilla_dm2=producto.area_plantilla_base,
                area_reticula_corte_dm2=form.area_reticula.data
            )
            db.session.add(nueva_receta)

            # ── Insumos adicionales (forros, herrajes, etc.) ──
            ids_extra    = request.form.getlist('extra_materia[]')
            cantidades   = request.form.getlist('extra_cantidad[]')

            for id_m, cant in zip(ids_extra, cantidades):
                if id_m and cant:
                    insumo_extra = Receta(
                        id_producto=producto.id,
                        id_materia=int(id_m),
                        area_plantilla_dm2=0,          # No aplica
                        area_reticula_corte_dm2=float(cant)
                    )
                    db.session.add(insumo_extra)

            db.session.commit()
            flash("Materiales añadidos.", "success")
            return redirect(url_for('recetas.crear_receta', p_id=producto.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f"Error: {str(e)}", "danger")
    
    return render_template("recetas/crear.html", form=form, insumos=insumos_actuales, materiales=materiales)  
# ─────────────────────────────────────────────
# MODIFICAR (U) - Permitir edición (Tarea 4)
# ─────────────────────────────────────────────
@recetas_bp.route("/recetas/modificar/<int:id>", methods=['GET', 'POST'])
def modificar_receta(id):
    insumo_receta = Receta.query.get_or_404(id)
    form = forms.RecetaForm(obj=insumo_receta)
    productos = Producto.query.all()
    
    materiales = MateriaPrima.query.all()
    form.id_materia.choices = [(m.id_materia, f"{m.nombre} ({m.unidad.abreviatura})") for m in materiales]
    
    if request.method == 'POST' and form.validate():
        try:
            producto = Producto.query.get(insumo_receta.id_producto)
            
            insumo_receta.id_materia = form.id_materia.data
            insumo_receta.area_plantilla_dm2 = producto.area_plantilla_base
            insumo_receta.area_reticula_corte_dm2 = form.area_reticula.data
            
            db.session.commit()
            flash("Cantidades de receta actualizadas", "info")
            return redirect(url_for('recetas.listar_recetas'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error al modificar receta: {str(e)}", "danger")
            return render_template("recetas/modificar.html", form=form, receta=insumo_receta)
            
    return render_template("recetas/modificar.html", form=form, receta=insumo_receta)


# ─────────────────────────────────────────────
# ELIMINAR (D)
# ─────────────────────────────────────────────
@recetas_bp.route("/recetas/eliminar/<int:id>", methods=['POST'])
def eliminar_receta(id):
    insumo_receta = Receta.query.get_or_404(id)
    try:
        db.session.delete(insumo_receta)
        db.session.commit()
        flash("Insumo removido de la receta", "info")
    except Exception as e:
        db.session.rollback()
        flash(f"Error: {str(e)}", "danger")
    return redirect(url_for('recetas.listar_recetas'))