from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import db, Producto, MateriaPrima, Receta
import forms

recetas_bp = Blueprint("recetas", __name__)

# ─────────────────────────────────────────────
# LISTADO (R)
# ─────────────────────────────────────────────
@recetas_bp.route("/recetas")
def listar_recetas():
    recetas = Receta.query.all()
    return render_template("recetas/index.html", recetas=recetas)

# ─────────────────────────────────────────────
# CREAR (C) - Soporta múltiples materiales por producto
# ─────────────────────────────────────────────
@recetas_bp.route("/recetas/nuevo", methods=['GET', 'POST'])
def crear_receta():
    # Capturamos el ID de la URL si el usuario ya registró un material previo
    p_id_seleccionado = request.args.get('p_id', type=int)
    
    form = forms.RecetaForm(request.form)
    
    # Llenamos opciones de productos y materiales
    form.id_producto.choices = [(p.id, f"{p.sku} - {p.nombre}") for p in Producto.query.all()]
    materiales = MateriaPrima.query.all()
    form.id_materia.choices = [(m.id_materia, f"{m.nombre} ({m.unidad.abreviatura})") for m in materiales]

    # Si venimos de registrar un insumo, pre-seleccionamos el producto
    if request.method == 'GET' and p_id_seleccionado:
        form.id_producto.data = p_id_seleccionado
        producto_previo = Producto.query.get(p_id_seleccionado)
        if producto_previo:
            form.area_plantilla.data = producto_previo.area_plantilla_base

    if request.method == 'POST' and form.validate():
        try:
            producto = Producto.query.get(form.id_producto.data)
            
            # Validación de duplicados: No repetir material en el mismo producto
            existe = Receta.query.filter_by(id_producto=producto.id, id_materia=form.id_materia.data).first()
            if existe:
                flash(f"Este material ya existe en la receta de {producto.nombre}", "warning")
                return render_template("recetas/crear.html", form=form)

            nueva_receta = Receta(
                id_producto=producto.id,
                id_materia=form.id_materia.data,
                area_plantilla_dm2=producto.area_plantilla_base,
                area_reticula_corte_dm2=form.area_reticula.data
            )
            
            db.session.add(nueva_receta)
            db.session.commit()
            
            flash(f"Insumo añadido con éxito a {producto.nombre}.", "success")
            # Redirigimos a la misma página pasando el ID del producto para seguir agregando
            return redirect(url_for('recetas.crear_receta', p_id=producto.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f"Error al registrar insumo: {str(e)}", "danger")
    
    return render_template("recetas/crear.html", form=form)

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