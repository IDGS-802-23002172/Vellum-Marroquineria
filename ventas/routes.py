from flask import render_template, redirect, url_for, request, session, flash
from . import ventas_bp
from models import CarritoTemporal, Venta, DetalleVenta, db, Producto, MovimientoCaja, CierreCaja
from decimal import Decimal
import uuid
from sqlalchemy import text
from datetime import datetime, date

IVA_TASA = Decimal("0.16")

# ─────────────────────────────────────
# HELPERS
# ─────────────────────────────────────
def _siguiente_folio_venta() -> str:
    """Genera un folio consecutivo tipo VEN-YYYY-NNNN"""
    anio = datetime.utcnow().year
    ultima = Venta.query.filter(Venta.folio.like(f"VEN-{anio}-%")).order_by(Venta.id.desc()).first()
    if ultima:
        try:
            n = int(ultima.folio.split("-")[-1]) + 1
        except ValueError:
            n = 1
    else:
        n = 1
    return f"VEN-{anio}-{n:04d}"

def calcular_totales(detalles):
    """Calcula totales al vuelo para cumplir con la 3NF"""
    subtotal = sum([
        d.precio_unitario * d.cantidad for d in detalles
    ]) if detalles else Decimal("0.00")
    iva = subtotal * IVA_TASA
    total = subtotal + iva
    return subtotal, iva, total

def caja_cerrada_hoy():
    """Verifica si ya se hizo el cierre de caja del día actual"""
    return CierreCaja.query.filter_by(fecha=date.today()).first()


# ─────────────────────────────────────
# POS (PUNTO DE VENTA)
# ─────────────────────────────────────
@ventas_bp.route("/pos", methods=["GET"])
def punto_venta():
    if caja_cerrada_hoy():
        flash("La caja del día ya está cerrada. No se pueden realizar más ventas.", "warning")

    session_id = session.get("session_id")
    if not session_id:
        session_id = str(uuid.uuid4())
        session["session_id"] = session_id

    busqueda = request.args.get("busqueda")

    if busqueda:
        productos = Producto.query.filter(
            (Producto.nombre.ilike(f"%{busqueda}%")) |
            (Producto.sku.ilike(f"%{busqueda}%"))
        ).all()
    else:
        productos = Producto.query.filter(
            Producto.stock_actual > 0
        ).all()

    carrito = CarritoTemporal.query.filter_by(session_id=session_id).all()

    subtotal = sum([item.precio * item.cantidad for item in carrito]) if carrito else Decimal("0.00")
    iva = subtotal * IVA_TASA
    total = subtotal + iva

    return render_template(
        "punto_venta.html",
        productos=productos,
        carrito=carrito,
        subtotal=subtotal,
        iva=iva,
        total=total,
        caja_cerrada=bool(caja_cerrada_hoy())
    )


# ─────────────────────────────────────
# AGREGAR PRODUCTO AL CARRITO
# ─────────────────────────────────────
@ventas_bp.route("/agregar", methods=["POST"])
def agregar_producto():
    if caja_cerrada_hoy():
        flash("No puedes agregar productos. La caja ya está cerrada.", "warning")
        return redirect(url_for("ventas.punto_venta"))

    session_id = session.get("session_id")
    producto_id = request.form.get("producto_id")
    cantidad = int(request.form.get("cantidad"))

    producto = Producto.query.get(producto_id)

    if cantidad > producto.stock_actual:
        flash("Stock insuficiente", "danger")
        return redirect(url_for("ventas.punto_venta"))

    item_existente = CarritoTemporal.query.filter_by(
        session_id=session_id,
        producto_id=producto.id
    ).first()

    if item_existente:
        item_existente.cantidad += cantidad
    else:
        item = CarritoTemporal(
            session_id=session_id,
            producto_id=producto.id,
            nombre=producto.nombre,
            precio=producto.precio_venta,
            cantidad=cantidad
        )
        db.session.add(item)
    
    db.session.commit()
    return redirect(url_for("ventas.punto_venta"))


# ─────────────────────────────────────
# FINALIZAR VENTA (TRANSACCIÓN ACID)
# ─────────────────────────────────────
@ventas_bp.route("/finalizar", methods=["POST"])
def finalizar_venta():
    if caja_cerrada_hoy():
        flash("No se pueden registrar ventas. La caja del día está cerrada.", "danger")
        return redirect(url_for("ventas.punto_venta"))

    session_id = session.get("session_id")
    carrito = CarritoTemporal.query.filter_by(session_id=session_id).all()

    if not carrito:
        flash("No hay productos en el carrito", "info")
        return redirect(url_for("ventas.punto_venta"))

    usuario_id = session.get("user_id")

    if not usuario_id:
        flash("Sesión inválida", "danger")
        return redirect(url_for("login")) 
    
    try:
        # 1. Cabecera de la Venta
        nueva_venta = Venta(
            folio=_siguiente_folio_venta(),
            usuario_id=usuario_id,
            estado="Pagado",
            tipo="POS" # Distinguimos venta de mostrador
        )
        db.session.add(nueva_venta)
        db.session.flush()
        
        total_venta_sin_iva = Decimal("0.00")
        
        # 2. Detalles y descuento de inventario
        for item in carrito: 
            producto = Producto.query.get(item.producto_id)
            
            if producto.stock_actual < item.cantidad:
                raise ValueError(f"Stock insuficiente para producto: {producto.nombre}")
            
            detalle = DetalleVenta(
                venta_id=nueva_venta.id,
                producto_id=item.producto_id,
                cantidad=item.cantidad,
                precio_unitario=item.precio,
                costo_unitario=producto.costo_produccion
            )
            db.session.add(detalle)
            producto.stock_actual -= item.cantidad
            total_venta_sin_iva += (Decimal(str(item.precio)) * item.cantidad)
        
        iva = total_venta_sin_iva * IVA_TASA
        total_con_iva = total_venta_sin_iva + iva
        
        # 3. Flujo de Caja (Generar Ingreso)
        movimiento_caja = MovimientoCaja(
            tipo="ENTRADA",
            concepto=f"Venta en Mostrador - Folio: {nueva_venta.folio}",
            monto=total_con_iva,
            id_venta=nueva_venta.id,
            creado_por=usuario_id,
            fecha=datetime.utcnow()
        )
        db.session.add(movimiento_caja)
        
        # 4. Limpiar Carrito
        CarritoTemporal.query.filter_by(session_id=session_id).delete()
        
        # 5. Confirmar Transacción
        db.session.commit()
        
        session["ultima_venta_id"] = nueva_venta.id
        flash("Venta procesada exitosamente.", "success")
        return redirect(url_for("ventas.ticket"))
        
    except ValueError as ve:
        db.session.rollback()
        flash(str(ve), "warning")
        return redirect(url_for("ventas.punto_venta"))

    except Exception as e:
        db.session.rollback()
        flash(f"Error crítico al procesar la venta: {str(e)}", "danger")
        return redirect(url_for("ventas.punto_venta"))


# ─────────────────────────────────────
# CANCELAR VENTA EN PROCESO
# ─────────────────────────────────────
@ventas_bp.route("/cancelar", methods=["POST"])
def cancelar_venta():
    session_id = session.get("session_id")
    CarritoTemporal.query.filter_by(session_id=session_id).delete()
    db.session.commit()
    flash("Venta cancelada", "info")
    return redirect(url_for("ventas.punto_venta"))


# ─────────────────────────────────────
# GENERAR TICKET
# ─────────────────────────────────────
@ventas_bp.route("/ticket")
def ticket():
    venta_id = session.get("ultima_venta_id")

    if not venta_id:
        flash("No hay ticket disponible", "warning")
        return redirect(url_for("ventas.punto_venta"))

    venta = Venta.query.get(venta_id)

    if not venta:
        flash("Venta no encontrada", "danger")
        return redirect(url_for("ventas.punto_venta"))

    detalles = DetalleVenta.query.filter_by(venta_id=venta.id).all()

    subtotal, iva, total = calcular_totales(detalles)

    return render_template(
        "ticket.html",
        venta=venta,
        detalles=detalles,
        subtotal=subtotal,
        iva=iva,
        total=total
    )


# ─────────────────────────────────────
# CIERRE DIARIO DE CAJA
# ─────────────────────────────────────
@ventas_bp.route("/cierre-diario", methods=["GET", "POST"])
def cierre_diario():
    usuario_id = session.get("user_id")

    if request.method == "POST":
        if not usuario_id:
            flash("Sesión inválida", "danger")
            return redirect(url_for("login"))
        
        resultado = db.session.execute(text("""
            SELECT 
                DATE(v.fecha) AS fecha,
                SUM(dv.cantidad) AS articulos_vendidos,
                SUM(dv.cantidad * dv.precio_unitario) AS total_ventas,
                SUM(dv.cantidad * (dv.precio_unitario - dv.costo_unitario)) AS utilidad_total
            FROM ventas v
            JOIN detalle_ventas dv ON v.id = dv.venta_id
            WHERE DATE(v.fecha) = CURDATE() AND v.tipo = 'POS'
            GROUP BY DATE(v.fecha)
        """))

        cierre_vista = resultado.mappings().first()

        if not cierre_vista:
            flash("No hay ventas de mostrador (POS) registradas hoy para hacer el cierre.", "warning")
            return redirect(url_for("ventas.punto_venta"))

        fecha_cierre = cierre_vista["fecha"]
        existe = CierreCaja.query.filter_by(fecha=fecha_cierre).first()

        if existe:
            flash("El cierre de caja de hoy ya fue realizado previamente.", "info")
            return redirect(url_for("ventas.punto_venta"))

        nuevo_cierre = CierreCaja(
            fecha=fecha_cierre,
            usuario_id=usuario_id,
            articulos_vendidos=cierre_vista["articulos_vendidos"] or 0,
            total_ventas=cierre_vista["total_ventas"] or 0,
            utilidad_total=cierre_vista["utilidad_total"] or 0
        )
        db.session.add(nuevo_cierre)
        db.session.commit()
        
        flash("Cierre de caja realizado correctamente. La caja ha sido bloqueada por hoy.", "success")
        return render_template("cierre_diario.html", cierre=nuevo_cierre)
    cierre = CierreCaja.query.order_by(CierreCaja.fecha.desc()).first()
    return render_template("cierre_diario.html", cierre=cierre)