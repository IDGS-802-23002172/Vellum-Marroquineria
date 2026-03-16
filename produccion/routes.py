from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import db, Producto, OrdenProduccion, Receta
import forms

# Definición del Blueprint con nombre único para Producción
produccion_bp = Blueprint("produccion", __name__)

# ─────────────────────────────────────────────
# LISTADO / MONITOREO (R)
# ─────────────────────────────────────────────
@produccion_bp.route("/produccion")
def listar_ordenes():
    # Mostramos el histórico de fabricación (Tarea: Módulo de Producción)
    ordenes = OrdenProduccion.query.order_by(OrdenProduccion.fecha_creacion.desc()).all()
    return render_template("produccion/index.html", ordenes=ordenes)

# ─────────────────────────────────────────────
# CREAR ÓRDEN (C)
# ─────────────────────────────────────────────
@produccion_bp.route("/produccion/nueva", methods=['GET', 'POST'])
def crear_orden():
    form = forms.OrdenProduccionForm(request.form)
    
    # Solo permitimos fabricar productos que tengan una receta definida
    productos_disponibles = Producto.query.join(Receta).all()
    form.id_producto.choices = [(p.id, p.nombre) for p in productos_disponibles]

    if request.method == 'POST' and form.validate():
        nueva_orden = OrdenProduccion(
            id_producto=form.id_producto.data,
            cantidad=form.cantidad.data,
            estado="En Corte" # Estado inicial por requerimiento
        )
        
        db.session.add(nueva_orden)
        db.session.commit()
        
        flash("Orden de producción iniciada: Fase de Corte", "success")
        return redirect(url_for('produccion.listar_ordenes'))
    
    return render_template("produccion/crear.html", form=form)

# ─────────────────────────────────────────────
# ELIMINAR ÓRDEN (D) - Para corrección de errores
# ─────────────────────────────────────────────
@produccion_bp.route("/produccion/cancelar/<int:id>", methods=['POST'])
def cancelar_orden(id):
    orden = OrdenProduccion.query.get_or_404(id)
    db.session.delete(orden)
    db.session.commit()
    flash("Orden de producción cancelada", "warning")
    return redirect(url_for('produccion.listar_ordenes'))

# ─────────────────────────────────────────────
# ACTUALIZAR ESTADO (U) - Tarea: Estados de Proceso
# ─────────────────────────────────────────────
@produccion_bp.route("/produccion/actualizar/<int:id>", methods=['GET', 'POST'])
def actualizar_produccion(id):
    orden = OrdenProduccion.query.get_or_404(id)
    # Usamos un formulario similar al de productos para mantener la simetría
    form = forms.OrdenProduccionForm(obj=orden)
    
    # Recargar opciones de producto (solo lectura en esta fase)
    form.id_producto.choices = [(orden.producto.id, orden.producto.nombre)]

    if request.method == 'POST':
        # Aquí capturamos el cambio de estado solicitado
        nuevo_estado = request.form.get('estado')
        
        if nuevo_estado:
            orden.estado = nuevo_estado
            db.session.commit()
            flash(f"Orden #{orden.id_orden} actualizada a: {nuevo_estado}", "info")
            return redirect(url_for('produccion.listar_ordenes'))
        
    return render_template("produccion/modificar.html", form=form, orden=orden)