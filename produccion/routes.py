from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models import db, Producto, OrdenProduccion, Receta, MateriaPrima
import forms

produccion_bp = Blueprint("produccion", __name__)

# ─────────────────────────────────────────────
# LISTADO / MONITOREO (R)
# ─────────────────────────────────────────────
@produccion_bp.route("/produccion")
def listar_ordenes():
    ordenes = OrdenProduccion.query.order_by(OrdenProduccion.fecha_creacion.desc()).all()
    return render_template("produccion/index.html", ordenes=ordenes)

# ─────────────────────────────────────────────
# CREAR ÓRDEN (C) - Con Explosión de Materiales Completa
# ─────────────────────────────────────────────
@produccion_bp.route("/produccion/nueva", methods=['GET', 'POST'])
def crear_orden():
    form = forms.OrdenProduccionForm(request.form)
    
    productos_disponibles = Producto.query.join(Receta).all()
    form.id_producto.choices = [(p.id, p.nombre) for p in productos_disponibles]

    if request.method == 'POST' and form.validate():
        # 1. Obtener la receta completa
        insumos = Receta.query.filter_by(id_producto=form.id_producto.data).all()
        
        if not insumos:
            flash("Error: El producto no tiene una receta configurada con materiales.", "danger")
            return render_template("produccion/crear.html", form=form)

        try:
            # 2. VALIDACIÓN PREVIA 
            for item in insumos:
                consumo_total = item.area_reticula_corte_dm2 * form.cantidad.data
                material = MateriaPrima.query.get(item.id_materia)
                
                if not material or not material.stock or material.stock.cantidad_actual < consumo_total:
                    flash(f"Stock insuficiente de {material.nombre if material else 'Material desconocido'}. Falta material para completar la orden.", "danger")
                    return render_template("produccion/crear.html", form=form)

            # 3. DESCUENTO REAL (Si llegamos aquí, es que hay stock de todo)
            for item in insumos:
                consumo_total = item.area_reticula_corte_dm2 * form.cantidad.data
                material = MateriaPrima.query.get(item.id_materia)
                material.stock.cantidad_actual -= consumo_total

            # 4. Registro de la Orden
            nueva_orden = OrdenProduccion(
                id_producto=form.id_producto.data,
                id_usuario=session.get('user_id'),
                cantidad=form.cantidad.data,
                estado="En Corte"
            )
            
            db.session.add(nueva_orden)
            db.session.commit()
            
            flash(f"Producción de {form.cantidad.data} piezas iniciada. Inventario de materiales actualizado.", "success")
            return redirect(url_for('produccion.listar_ordenes'))

        except Exception as e:
            db.session.rollback()
            flash(f"Error técnico en la explosión de materiales: {str(e)}", "danger")
    
    return render_template("produccion/crear.html", form=form)

# ─────────────────────────────────────────────
# ELIMINAR ÓRDEN (D) - Retorno de Insumos Integrado
# ─────────────────────────────────────────────
@produccion_bp.route("/produccion/cancelar/<int:id>", methods=['POST'])
def cancelar_orden(id):
    orden = OrdenProduccion.query.get_or_404(id)
    
    try:
        insumos = Receta.query.filter_by(id_producto=orden.id_producto).all()
        
        for item in insumos:
            material = MateriaPrima.query.get(item.id_materia)
            if material and material.stock:
                # Devolvemos exactamente lo que se descontó (Reticula * cantidad)
                cantidad_a_devolver = item.area_reticula_corte_dm2 * orden.cantidad
                material.stock.cantidad_actual += cantidad_a_devolver

        db.session.delete(orden)
        db.session.commit()
        flash("Orden cancelada e insumos devueltos al almacén de materia prima.", "success")
        
    except Exception as e: 
        db.session.rollback()
        flash(f"Error al revertir materiales: {str(e)}", "danger")
    
    return redirect(url_for('produccion.listar_ordenes'))

# ─────────────────────────────────────────────
# ACTUALIZAR ESTADO (U) - Entrada a Almacén de Producto Terminado
# ─────────────────────────────────────────────
@produccion_bp.route("/produccion/actualizar/<int:id>", methods=['GET', 'POST'])
def actualizar_produccion(id):
    orden = OrdenProduccion.query.get_or_404(id)
    
    if request.method == 'POST':
        nuevo_estado = request.form.get('estado')
        
        try:
            # Si el artesano marca como "Terminado", el producto entra al stock de venta
            if orden.estado != "Terminado" and nuevo_estado == "Terminado":
                producto_almacen = Producto.query.get(orden.id_producto)
                producto_almacen.stock_actual += orden.cantidad
                flash(f"Producción finalizada: {orden.cantidad} unidades listas para venta.", "success")
            
            orden.estado = nuevo_estado
            db.session.commit()
            flash(f"Orden #{orden.id_orden} actualizada a: {nuevo_estado}.", "info")
            return redirect(url_for('produccion.listar_ordenes'))
            
        except Exception as e:
            db.session.rollback()
            flash(f"Error al actualizar estado: {str(e)}", "danger")
        
    return render_template("produccion/modificar.html", orden=orden)