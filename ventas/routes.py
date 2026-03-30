from flask import render_template, redirect, url_for, request, session, flash
from . import ventas_bp
from models import CarritoTemporal, Venta, DetalleVenta, db, Producto
from decimal import Decimal
import uuid
from sqlalchemy import text
from datetime import datetime

IVA_TASA = Decimal("0.16")


def generar_folio():
    fecha = datetime.now().strftime("%Y%m%d")
    ultima_venta = Venta.query.order_by(Venta.id.desc()).first()
    numero = (ultima_venta.id + 1) if ultima_venta else 1
    return f"T-{fecha}-{numero:04d}"



def calcular_totales(detalles):
    subtotal = sum([
        d.precio_unitario * d.cantidad for d in detalles
    ]) if detalles else Decimal("0.00")

    iva = subtotal * IVA_TASA
    total = subtotal + iva

    return subtotal, iva, total



@ventas_bp.route("/pos", methods=["GET"])
def punto_venta():
    session_id = session.get("session_id")
    if not session_id:
        session_id = str(uuid.uuid4())
        session["session_id"] = session_id

    busqueda = request.args.get("busqueda")
    productos = []

    if busqueda:
        productos = Producto.query.filter(
            (Producto.nombre.ilike(f"%{busqueda}%")) |
            (Producto.sku.ilike(f"%{busqueda}%"))
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
        total=total
    )

@ventas_bp.route("/agregar", methods=["POST"])
def agregar_producto():
    session_id = session.get("session_id")
    producto_id = request.form.get("producto_id")
    cantidad = int(request.form.get("cantidad"))

    producto = Producto.query.get(producto_id)

    if cantidad > producto.stock_actual:
        flash("Stock insuficiente")
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


@ventas_bp.route("/finalizar", methods=["POST"])
def finalizar_venta():
    session_id = session.get("session_id")
    carrito = CarritoTemporal.query.filter_by(session_id=session_id).all()

    if not carrito:
        flash("No hay productos en el carrito", "info")
        return redirect(url_for("ventas.punto_venta"))

    usuario_id = session.get("user_id")

    if not usuario_id:
        flash("Sesión inválida", "danger")
        return redirect(url_for("auth.login"))

    folio = generar_folio()
    
    nueva_venta = Venta(
        folio=folio,
        usuario_id=usuario_id
    )

    db.session.add(nueva_venta)
    db.session.flush()

    for item in carrito:
        producto = Producto.query.get(item.producto_id)

        detalle = DetalleVenta(
            venta_id=nueva_venta.id,
            producto_id=item.producto_id,
            cantidad=item.cantidad,
            precio_unitario=item.precio,
            costo_unitario=producto.costo_produccion
        )

        db.session.add(detalle)

        if producto:
            producto.stock_actual -= item.cantidad

    CarritoTemporal.query.filter_by(session_id=session_id).delete()
    db.session.commit()

    session["ultima_venta_id"] = nueva_venta.id
    return redirect(url_for("ventas.ticket"))


@ventas_bp.route("/cancelar", methods=["POST"])
def cancelar_venta():
    session_id = session.get("session_id")
    CarritoTemporal.query.filter_by(session_id=session_id).delete()
    db.session.commit()
    flash("Venta cancelada", "info")
    return redirect(url_for("ventas.punto_venta"))

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

@ventas_bp.route("/cierre-diario")
def cierre_diario():

    resultado = db.session.execute(text("""
        SELECT 
            DATE(v.fecha) AS fecha,
            SUM(d.cantidad) AS articulos_vendidos,
            SUM(d.precio_unitario * d.cantidad) AS total_ventas,
            SUM((d.precio_unitario - d.costo_unitario) * d.cantidad) AS utilidad_total
        FROM ventas v
        JOIN detalle_ventas d ON v.id = d.venta_id
        WHERE DATE(v.fecha) = CURDATE()
        GROUP BY DATE(v.fecha);
    """))

    cierre = resultado.mappings().first()

    return render_template(
        "cierre_diario.html",
        cierre=cierre
    )