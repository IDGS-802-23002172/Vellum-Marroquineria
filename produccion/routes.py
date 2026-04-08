from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models import db, Producto, OrdenProduccion, Receta, MateriaPrima, PiezaMateriaPrima
import forms
from decimal import Decimal


produccion_bp = Blueprint("produccion", __name__)

# ─────────────────────────────────────────────
# LISTADO / MONITOREO (R)
# ─────────────────────────────────────────────
@produccion_bp.route("/produccion")
def listar_ordenes():
    ordenes = OrdenProduccion.query.order_by(OrdenProduccion.fecha_creacion.desc()).all()
    return render_template("produccion/index.html", ordenes=ordenes)

# ─────────────────────────────────────────────
# CREAR ÓRDEN pero filtrando si es una pieza o no
# ─────────────────────────────────────────────
@produccion_bp.route("/produccion/nueva", methods=['GET', 'POST'])
def crear_orden():
    form = forms.OrdenProduccionForm(request.form)
    
    productos_disponibles = Producto.query.join(Receta).all()
    form.id_producto.choices = [(p.id, p.nombre) for p in productos_disponibles]

    if request.method == 'POST' and form.validate():
        insumos = Receta.query.filter_by(id_producto=form.id_producto.data).all()
        
        if not insumos:
            flash("Error: El producto no tiene una receta configurada con materiales.", "danger")
            return render_template("produccion/crear.html", form=form)

        try:
            consumos_agrupados = {}
            for item in insumos:
                consumo = item.area_reticula_corte_dm2 * form.cantidad.data
                if item.id_materia in consumos_agrupados:
                    consumos_agrupados[item.id_materia] += consumo
                else:
                    consumos_agrupados[item.id_materia] = consumo

            for id_materia, consumo_total in consumos_agrupados.items():
                material = MateriaPrima.query.get(id_materia)
                
                if material.tipo_control == "pieza":
                    area_total_disponible = db.session.query(db.func.sum(PiezaMateriaPrima.area).filter_by(
                        id_materia=id_materia, disponible=True)).scalar() or 0
                    
                    if float(area_total_disponible)<float(consumo_total):
                        flash("Area insuficiente para crear {material.nombre}", "danger")
                        return render_template("produccion/crear.html", form=form)
                else:
                    if not material or not material.stock or material.stock.cantidad_actual < consumo_total:
                        stock_actual = material.stock.cantidad_actual if material and material.stock else 0
                        flash(f"Stock insuficiente de {material.nombre}. Se requieren {consumo_total} pero hay {stock_actual}.", "danger")
                        return render_template("produccion/crear.html", form=form)

            # 3. DESCUENTO REAL (Si llegamos aquí, es que hay stock de todo)
            for id_materia, consumo_total in consumos_agrupados.items():
                material = MateriaPrima.query.get(id_materia)
                
                if material.tipo_control == "pieza":
                    resta = Decimal(str(consumo_total))
                    piezas = PiezaMateriaPrima.query.filter_by(id_materia=id_materia, disponible=True).order_by(PiezaMateriaPrima.area.asc()).all()
                    for p in piezas:
                        if resta <= 0:
                            break
                        if p.area <= resta:
                            resta -= p.area
                            p.disponible = False
                        else:
                            p.area -= resta
                            resta = 0
                            p.disponible = False
                    material.stock.cantidad_actual = PiezaMateriaPrima.query.filter_by(id_materia=id_materia, disponible=True).count()
                else:
                    material.stock.cantidad_actual -= Decimal(str(consumo_total))


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
                cantidad_a_devolver = item.area_reticula_corte_dm2 * orden.cantidad
                
                if material.tipo_control == 'pieza':
                    # Si cancelamos corte de cuero, generamos un nuevo pedazo (retal) en el inventario
                    nuevo_retal = PiezaMateriaPrima(
                        id_materia=material.id_materia,
                        area=cantidad_a_devolver,
                        disponible=True
                    )
                    db.session.add(nuevo_retal)
                    # Forzamos flush para que cuente el nuevo retal
                    db.session.flush()
                    material.stock.cantidad_actual = PiezaMateriaPrima.query.filter_by(id_materia=material.id_materia, disponible=True).count()
                else:
                    material.stock.cantidad_actual += cantidad_a_devolver

        db.session.delete(orden)
        db.session.commit()
        flash("Orden cancelada. Insumos y cortes de cuero devueltos al almacén.", "success")
        
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