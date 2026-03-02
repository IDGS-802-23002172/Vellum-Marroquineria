from flask import render_template, redirect, url_for, request, session, flash
from . import ventas_bp
from models import CarritoTemporal, Venta, DetalleVenta, db, Producto
from decimal import Decimal
import uuid

IVA_TASA = Decimal("0.16")

@ventas_bp.route("/pos", methods=["GET"])
def punto_venta():
    session_id = session.get("session_id")
    if not session_id:
        session_id = str(uuid.uuid4())
        session["session_id"] = session_id

    busqueda = request.args.get("busqueda")
    productos = []

    if busqueda:
        # Sincronizado con tus modelos de Marroquinería
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
            precio=producto.precio_venta, # Usar precio_venta del modelo Producto
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

    subtotal = sum([item.precio * item.cantidad for item in carrito])
    iva = subtotal * IVA_TASA
    total = subtotal + iva

    # FIX: usuario_id=1 por ahora, luego cámbialo por session.get('user_id')
    nueva_venta = Venta(
        subtotal=subtotal,
        iva=iva,
        total=total,
        usuario_id=1 
    )

    db.session.add(nueva_venta)
    db.session.flush()

    for item in carrito:
        detalle = DetalleVenta(
            venta_id=nueva_venta.id,
            producto_id=item.producto_id,
            cantidad=item.cantidad,
            precio_unitario=item.precio,
            subtotal=item.precio * item.cantidad
        )
        db.session.add(detalle)

        # FIX: Descontar usando el nombre correcto: stock_actual
        producto = Producto.query.get(item.producto_id)
        if producto:
            producto.stock_actual -= item.cantidad

    CarritoTemporal.query.filter_by(session_id=session_id).delete()
    db.session.commit()

    flash("¡Venta exitosa! El inventario se ha actualizado.", "success")
    return redirect(url_for("ventas.punto_venta"))


@ventas_bp.route("/cancelar", methods=["POST"])
def cancelar_venta():
    session_id = session.get("session_id")
    CarritoTemporal.query.filter_by(session_id=session_id).delete()
    db.session.commit()
    flash("Venta cancelada", "info")
    return redirect(url_for("ventas.punto_venta"))