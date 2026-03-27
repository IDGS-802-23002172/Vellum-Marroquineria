from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import db, Producto, MateriaPrima, Receta
import forms

# Definición del Blueprint independiente
recetas_bp = Blueprint("recetas", __name__)

# ─────────────────────────────────────────────
# LISTADO (R) - Tabla de recetas (Tarea 1)
# ─────────────────────────────────────────────
@recetas_bp.route("/recetas")
def listar_recetas():
    # Obtenemos todos los productos que ya tienen una receta asignada
    recetas = Receta.query.all()
    return render_template("recetas/index.html", recetas=recetas)

# ─────────────────────────────────────────────
# CREAR (C) - Definición de insumos (Tarea 2)
# ─────────────────────────────────────────────
@recetas_bp.route("/recetas/nuevo", methods=['GET', 'POST'])
def crear_receta():
    form = forms.RecetaForm(request.form)
    
    # Validación de existencia de materiales (Tarea 3)
    materiales = MateriaPrima.query.all()
    form.id_materia.choices = [(m.id_materia, f"{m.nombre} ({m.unidad.abreviatura})") for m in materiales]

    if request.method == 'POST' and form.validate():
        nueva_receta = Receta(
            id_producto=form.id_producto.data,
            id_materia=form.id_materia.data,
            area_plantilla_dm2=form.area_plantilla.data, # Área útil
            area_reticula_corte_dm2=form.area_reticula.data # Área con merma
        )
        
        db.session.add(nueva_receta)
        db.session.commit()
        flash("Insumo agregado a la receta exitosamente", "success")
        return redirect(url_for('recetas.listar_recetas'))
    
    return render_template("recetas/crear.html", form=form)

# ─────────────────────────────────────────────
# MODIFICAR (U) - Permitir edición (Tarea 4)
# ─────────────────────────────────────────────
@recetas_bp.route("/recetas/modificar/<int:id>", methods=['GET', 'POST'])
def modificar_receta(id):
    insumo_receta = Receta.query.get_or_404(id)
    form = forms.RecetaForm(obj=insumo_receta)
    
    # Recargar los materiales para el SelectField
    materiales = MateriaPrima.query.all()
    form.id_materia.choices = [(m.id_materia, f"{m.nombre} ({m.unidad.abreviatura})") for m in materiales]
    
    if request.method == 'POST' and form.validate():
        insumo_receta.id_materia = form.id_materia.data
        insumo_receta.area_plantilla_dm2 = form.area_plantilla.data
        insumo_receta.area_reticula_corte_dm2 = form.area_reticula.data
        
        db.session.commit()
        flash("Cantidades de receta actualizadas", "info")
        return redirect(url_for('recetas.listar_recetas'))
        
    return render_template("recetas/modificar.html", form=form, receta=insumo_receta)

# ─────────────────────────────────────────────
# ELIMINAR (D)
# ─────────────────────────────────────────────
@recetas_bp.route("/recetas/eliminar/<int:id>", methods=['POST'])
def eliminar_receta(id):
    insumo_receta = Receta.query.get_or_404(id)
    db.session.delete(insumo_receta)
    db.session.commit()
    flash("Insumo removido de la receta", "warning")
    return redirect(url_for('recetas.listar_recetas'))