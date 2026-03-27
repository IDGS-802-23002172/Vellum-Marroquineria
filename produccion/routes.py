from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models import db, Producto, OrdenProduccion, Receta, MateriaPrima
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
    
    # Carga dinámica: solo productos que tengan receta técnica definida
    productos_disponibles = Producto.query.join(Receta).all()
    form.id_producto.choices = [(p.id, p.nombre) for p in productos_disponibles]

    if request.method == 'POST' and form.validate():
        # 1. Obtener los insumos necesarios según tu explosión de materiales (Semana 2)
        insumos = Receta.query.filter_by(id_producto=form.id_producto.data).all()
        
        if not insumos:
            flash("Error: El producto seleccionado no tiene una receta configurada.", "danger")
            return render_template("produccion/crear.html", form=form)

        # 2. VALIDACIÓN Y DESCUENTO AUTOMÁTICO (Tarea 2 - Semana 3)
        try:
            for item in insumos:
                # Calculamos el consumo total basado en la retícula (área con merma técnica)
                consumo_necesario = item.area_reticula_corte_dm2 * form.cantidad.data
                
                # Buscamos el material en el inventario de Diego (MateriaPrima)
                material = MateriaPrima.query.get(item.id_materia)
                
                # Verificamos si hay suficiente stock de cuero antes de proceder
                if material.stock.cantidad_actual < consumo_necesario:
                    flash(f"Stock insuficiente de {material.nombre}. Necesitas {consumo_necesario} dm² y solo hay {material.stock.cantidad_actual} dm².", "danger")
                    return render_template("produccion/crear.html", form=form)
                
                # Restamos del inventario de piel
                material.stock.cantidad_actual -= consumo_necesario

            # 3. Registro de la Orden si el inventario fue suficiente
            nueva_orden = OrdenProduccion(
                id_producto=form.id_producto.data,
                id_usuario=session.get('user_id'),
                cantidad=form.cantidad.data,
                estado="En Corte" # Estado inicial por requerimiento
            )
            
            db.session.add(nueva_orden)
            db.session.commit()
            
            flash("Producción iniciada con éxito. El inventario ha sido actualizado.", "success")
            return redirect(url_for('produccion.listar_ordenes'))

        except Exception as e:
            db.session.rollback()
            flash(f"Error técnico al procesar el inventario: {str(e)}", "danger")
    
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
    form = forms.OrdenProduccionForm(obj=orden)
    form.id_producto.choices = [(orden.producto.id, orden.producto.nombre)]

    if request.method == 'POST':
        nuevo_estado = request.form.get('estado')
        
        # LÓGICA DE ENTRADA A ALMACÉN (Tarea 4)
        # Si el estado cambia de "En Corte" a "Terminado"
        if orden.estado == "En Corte" and nuevo_estado == "Terminado":
            producto_almacen = Producto.query.get(orden.id_producto)
            
            # Sumamos las unidades al stock de venta
            producto_almacen.stock_actual += orden.cantidad
            flash(f"¡Éxito! {orden.cantidad} unidades añadidas al catálogo de ventas.", "success")
        
        orden.estado = nuevo_estado
        db.session.commit()
        
        flash(f"Estado de la orden #{orden.id_orden} actualizado.", "info")
        return redirect(url_for('produccion.listar_ordenes'))
        
    return render_template("produccion/modificar.html", form=form, orden=orden)