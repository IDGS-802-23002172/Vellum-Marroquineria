from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models import db, Producto, OrdenProduccion, Receta, MateriaPrima, PiezaMateriaPrima
import forms
from decimal import Decimal

produccion_bp = Blueprint("produccion", __name__)

# ─────────────────────────────────────────────
# HELPER: EXPLOSIÓN DE MATERIALES
# ─────────────────────────────────────────────
def ejecutar_explosion_materiales(id_producto, cantidad):
    """Calcula y descuenta los materiales físicos. Lanza ValueError si no hay stock."""
    insumos = Receta.query.filter_by(id_producto=id_producto).all()
    if not insumos:
        raise ValueError("El producto no tiene una receta configurada con materiales.")

    consumos_agrupados = {}
    for item in insumos:
        consumo = item.area_reticula_corte_dm2 * cantidad
        if item.id_materia in consumos_agrupados:
            consumos_agrupados[item.id_materia] += consumo
        else:
            consumos_agrupados[item.id_materia] = consumo

    # 1. VALIDACIÓN ESTRICTA
    for id_materia, consumo_total in consumos_agrupados.items():
        material = MateriaPrima.query.get(id_materia)
        
        if material.tipo_control.lower() in ['piel', 'textil', 'pieza']:
            area_total_disponible = db.session.query(db.func.sum(PiezaMateriaPrima.area)).filter_by(
                id_materia=id_materia, disponible=True
            ).scalar() or 0
            
            if float(area_total_disponible) < float(consumo_total):
                raise ValueError(f"Área insuficiente para {material.nombre}. Se requieren {consumo_total} dm², hay {area_total_disponible} dm².")
        else:
            if not material or not material.stock or material.stock.cantidad_actual < consumo_total:
                stock_actual = material.stock.cantidad_actual if material and material.stock else 0
                raise ValueError(f"Stock insuficiente de {material.nombre}. Se requieren {consumo_total} unidades, hay {stock_actual}.")

    # 2. DESCUENTO REAL DE INVENTARIO
    for id_materia, consumo_total in consumos_agrupados.items():
        material = MateriaPrima.query.get(id_materia)
        
        if material.tipo_control.lower() in ['piel', 'textil', 'pieza']:
            resta = Decimal(str(consumo_total))
            piezas = PiezaMateriaPrima.query.filter_by(id_materia=id_materia, disponible=True).order_by(PiezaMateriaPrima.area.asc()).all()
            for p in piezas:
                if resta <= 0:
                    break
                if p.area <= resta:
                    resta -= p.area
                    p.area = 0
                    p.disponible = False
                else:
                    p.area -= resta
                    resta = 0
            
            area_restante = db.session.query(db.func.sum(PiezaMateriaPrima.area)).filter_by(
                id_materia=id_materia, disponible=True
            ).scalar() or 0                
            material.stock.cantidad_actual = area_restante
        else:
            material.stock.cantidad_actual -= Decimal(str(consumo_total))


# ─────────────────────────────────────────────
# LISTADO / MONITOREO (R)
# ─────────────────────────────────────────────
@produccion_bp.route("/produccion")
def listar_ordenes():
    ordenes = OrdenProduccion.query.order_by(OrdenProduccion.fecha_creacion.desc()).all()
    return render_template("produccion/index.html", ordenes=ordenes)

# ─────────────────────────────────────────────
# CREAR ÓRDEN MANUAL (Nace como Pendiente)
# ─────────────────────────────────────────────
@produccion_bp.route("/produccion/nueva", methods=['GET', 'POST'])
def crear_orden():
    form = forms.OrdenProduccionForm(request.form)
    productos_disponibles = Producto.query.join(Receta).all()
    form.id_producto.choices = [(p.id, p.nombre) for p in productos_disponibles]

    if request.method == 'POST' and form.validate():
        try:
            nueva_orden = OrdenProduccion(
                id_producto=form.id_producto.data,
                id_usuario=session.get('user_id'),
                cantidad=form.cantidad.data,
                estado="Pendiente" # Todas nacen pendientes
            )
            db.session.add(nueva_orden)
            db.session.commit()
            
            flash(f"Orden de {form.cantidad.data} piezas registrada. Cambia el estado a 'En Corte' para iniciarla y descontar material.", "success")
            return redirect(url_for('produccion.listar_ordenes'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error al registrar la orden: {str(e)}", "danger")
    
    return render_template("produccion/crear.html", form=form)

# ─────────────────────────────────────────────
# ACTUALIZAR ESTADO (El Trigger Principal)
# ─────────────────────────────────────────────
@produccion_bp.route("/produccion/actualizar/<int:id>", methods=['GET', 'POST'])
def actualizar_produccion(id):
    orden = OrdenProduccion.query.get_or_404(id)
    
    # BLOQUEO QA: Evitar que se modifique una orden terminada vía backend
    if orden.estado == "Terminado":
        flash("Esta orden ya se encuentra terminada y no puede ser modificada.", "warning")
        return redirect(url_for('produccion.listar_ordenes'))

    if request.method == 'POST':
        nuevo_estado = request.form.get('estado')
        
        try:
            # 1. TRIGGER: De "Pendiente" a "En Corte" (Descuenta Material)
            if orden.estado == "Pendiente" and nuevo_estado == "En Corte":
                ejecutar_explosion_materiales(orden.id_producto, orden.cantidad)
                orden.id_artesano_corte = session.get('user_id')
                flash(f"Materiales descontados exitosamente. Orden enviada a corte.", "success")

            # 2. TRIGGER: De "En Corte" a "Terminado" (Suma Producto Terminado)
            elif orden.estado != "Terminado" and nuevo_estado == "Terminado":
                producto_almacen = Producto.query.get(orden.id_producto)
                producto_almacen.stock_actual += orden.cantidad
                orden.id_artesano_terminado = session.get('user_id')
                flash(f"Producción finalizada: {orden.cantidad} unidades listas para venta.", "success")
            
            # Guardamos el nuevo estado si no hubo errores matemáticos
            orden.estado = nuevo_estado
            db.session.commit()
            return redirect(url_for('produccion.listar_ordenes'))
            
        except ValueError as ve:
            # Capturamos la falta de stock del helper sin que el servidor colapse
            db.session.rollback()
            flash(str(ve), "danger")
            return redirect(url_for('produccion.listar_ordenes'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error al actualizar estado: {str(e)}", "danger")
        
    return render_template("produccion/modificar.html", orden=orden)

# ─────────────────────────────────────────────
# ELIMINAR ÓRDEN (Cancelación inteligente)
# ─────────────────────────────────────────────
@produccion_bp.route("/produccion/cancelar/<int:id>", methods=['POST'])
def cancelar_orden(id):
    orden = OrdenProduccion.query.get_or_404(id)
    estado_original = orden.estado
    
    try:
        # SOLO devolvemos material si la orden ya había pasado de "Pendiente"
        if estado_original != "Pendiente":
            insumos = Receta.query.filter_by(id_producto=orden.id_producto).all()
            
            for item in insumos:
                material = MateriaPrima.query.get(item.id_materia)
                if material and material.stock:
                    cantidad_a_devolver = item.area_reticula_corte_dm2 * orden.cantidad
                    
                    if material.tipo_control.lower() in ['piel', 'textil', 'pieza']:
                        nuevo_retal = PiezaMateriaPrima(
                            id_materia=material.id_materia,
                            area=cantidad_a_devolver,
                            disponible=True
                        )
                        db.session.add(nuevo_retal)
                        db.session.flush()
                        area_restante = db.session.query(db.func.sum(PiezaMateriaPrima.area)).filter_by(
                            id_materia=material.id_materia, disponible=True
                        ).scalar() or 0
                        material.stock.cantidad_actual = area_restante
                    else:
                        material.stock.cantidad_actual += cantidad_a_devolver
            
            flash("Orden cancelada. Insumos devueltos al almacén.", "success")
        else:
            flash("Orden pendiente eliminada del registro.", "info")

        db.session.delete(orden)
        db.session.commit()
        
    except Exception as e: 
        db.session.rollback()
        flash(f"Error al revertir la orden: {str(e)}", "danger")
    
    return redirect(url_for('produccion.listar_ordenes'))