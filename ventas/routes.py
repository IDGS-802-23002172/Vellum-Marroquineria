from flask import render_template, redirect, url_for, request, session, flash
from . import ventas_bp
from models import CarritoTemporal, Venta, DetalleVenta, db, Producto, MovimientoCaja, CierreCaja
from decimal import Decimal
import uuid
from sqlalchemy import text
from datetime import datetime, date

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

def caja_cerrada_hoy():
    return CierreCaja.query.filter_by(fecha=date.today()).first()

@ventas_bp.route("/pos", methods=["GET"])
def punto_venta():
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


def _siguiente_folio_venta() -> str:
    from datetime import datetime
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
        return redirect(url_for("login")) 
    
    try:
        nueva_venta = Venta(
            folio=_siguiente_folio_venta(),
            usuario_id=usuario_id,
            estado = "Pagado"
        )
        db.sesion.add(nueva_venta)
        db.session.flush()
        total_venta_sin_iva = Decimal("0.00")
        for item in carrito : 
            producto = Producto.query.get(item.producto_id)
            if producto.stock_actual>item.cantidad:
                flash("Stock insuficiente para producto", {producto.nombre})
            
            detalle = DetalleVenta(
                venta_id=nueva_venta.id,
                producto_id=item.producto_id,
                cantidad = item.cantidad,
                precio_unitario = item.precio,
                costo_unitario = producto.costo_produccion
            )
            db.session.add(detalle)
            producto.stock_actual -= item.cantidad
            total_venta_sin_iva += (item.precio*item.cantidad)
        
        iva = total_venta_sin_iva * IVA_TASA
        total_con_iva = total_venta_sin_iva + iva
        
        movimiento_caja = MovimientoCaja(
            tipo = "ENTRADA",
            concepto = f"Venta -  Folio : {nueva_venta.folio}",
            id_venta = nueva_venta.id,
            creado_por=usuario_id,
        )
        db.session.add(movimiento_caja)
        CarritoTemporal.query.filter_by(session_id=session_id).delete()
        db.session.commit()
        session["ultima_venta_id"]=nueva_venta.id
        return redirect(url_for("ventas.ticket"))
    except ValueError as ve:
        db.session.rollback()
        flash(str(ve), "warning")
        return redirect(url_for("ventas.punto_venta"))

    except Exception as e:
        db.session.rollback()
        flash(f"Error crítico al procesar la venta: {str(e)}", "danger")
        return redirect(url_for("ventas.punto_venta"))

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