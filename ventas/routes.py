from flask import render_template, redirect, url_for, request, session, flash
from . import ventas_bp
from models import CarritoTemporal, Venta, DetalleVenta
from models import db
from models import Producto
from decimal import Decimal



IVA_TASA = Decimal("0.16")


@ventas_bp.route("/pos", methods=["GET"])
def punto_venta():

    # Crear session_id si no existe
    session_id = session.get("session_id")
    if not session_id:
        import uuid
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
    if not session_id:
        flash("Sesión no válida")
        return redirect(url_for("ventas.punto_venta"))

    producto_id = request.form.get("producto_id")
    cantidad = int(request.form.get("cantidad"))

    producto = Producto.query.get(producto_id)

    if not producto:
        flash("Producto no encontrado")
        return redirect(url_for("ventas.punto_venta"))

    if cantidad > producto.stock:
        flash("Stock insuficiente")
        return redirect(url_for("ventas.punto_venta"))

    # Verificar si ya está en carrito
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
            precio=producto.precio,
            cantidad=cantidad,
            stock_disponible=producto.stock
        )
        db.session.add(item)

    db.session.commit()

    return redirect(url_for("ventas.punto_venta"))


@ventas_bp.route("/finalizar", methods=["POST"])
def finalizar_venta():

    session_id = session.get("session_id")
    carrito = CarritoTemporal.query.filter_by(session_id=session_id).all()

    if not carrito:
        flash("No hay productos en el carrito")
        return redirect(url_for("ventas.punto_venta"))

    subtotal = sum([item.precio * item.cantidad for item in carrito])
    iva = subtotal * IVA_TASA
    total = subtotal + iva

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

        # Descontar stock
        producto = Producto.query.get(item.producto_id)
        producto.stock -= item.cantidad

    CarritoTemporal.query.filter_by(session_id=session_id).delete()
    db.session.commit()

    flash("Venta finalizada correctamente")
    return redirect(url_for("ventas.punto_venta"))


@ventas_bp.route("/cancelar", methods=["POST"])
def cancelar_venta():
    session_id = session.get("session_id")
    CarritoTemporal.query.filter_by(session_id=session_id).delete()
    db.session.commit()
    flash("Venta cancelada")
    return redirect(url_for("ventas.punto_venta"))