from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import db, Producto, MateriaPrima, Receta
import forms

recetas_bp = Blueprint("recetas", __name__)

# ─────────────────────────────────────────────
# LISTADO (R) - Tabla de recetas (Tarea 1)
# ─────────────────────────────────────────────
@recetas_bp.route("/recetas")
def listar_recetas():
    recetas = Receta.query.all()
    return render_template("recetas/index.html", recetas=recetas)

# ─────────────────────────────────────────────
# CREAR (C) - Definición de insumos (Tarea 2)
# ─────────────────────────────────────────────
@recetas_bp.route("/recetas/nuevo", methods=['GET', 'POST'])
def crear_receta():
    form = forms.RecetaForm(request.form)
    
    materiales = MateriaPrima.query.all()
    form.id_materia.choices = [(m.id_materia, f"{m.nombre} ({m.unidad.abreviatura})") for m in materiales]

    if request.method == 'POST' and form.validate():
        try:
            producto = Producto.query.get(form.id_producto.data)
            if not producto:
                flash("Error: El producto seleccionado no existe", "danger")
                return redirect(url_for('recetas.crear_receta'))

            nueva_receta = Receta(
                id_producto=producto.id,
                id_materia=form.id_materia.data,
                area_plantilla_dm2=producto.area_plantilla_base,
                area_reticula_corte_dm2=form.area_reticula.data
            )
            
            db.session.add(nueva_receta)
            db.session.commit()
            flash("Insumo agregado a la receta exitosamente", "success")
            return redirect(url_for('recetas.listar_recetas'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error al crear receta: {str(e)}", "danger")
            return render_template("recetas/crear.html", form=form)
    
    return render_template("recetas/crear.html", form=form)

# ─────────────────────────────────────────────
# MODIFICAR (U) - Permitir edición (Tarea 4)
# ─────────────────────────────────────────────
@recetas_bp.route("/recetas/modificar/<int:id>", methods=['GET', 'POST'])
def modificar_receta(id):
    insumo_receta = Receta.query.get_or_404(id)
    form = forms.RecetaForm(obj=insumo_receta)
    
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
        flash("Insumo removido de la receta", "warning")
    except Exception as e:
        db.session.rollback()
        flash(f"Error al eliminar: {str(e)}", "danger")
        
    return redirect(url_for('recetas.listar_recetas'))