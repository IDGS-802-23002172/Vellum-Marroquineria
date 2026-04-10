from flask import render_template, redirect, url_for, request, session, flash
from . import ventas_bp
from models import CarritoTemporal, Venta, DetalleVenta, db, Producto, MovimientoCaja, CierreCaja
from decimal import Decimal
import uuid
from sqlalchemy import text
from datetime import datetime, date

IVA_TASA = Decimal("0.16")

def _siguiente_folio_venta() -> str:
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
    subtotal = sum([d.precio_unitario * d.cantidad for d in detalles]) if detalles else Decimal("0.00")
    iva = subtotal * IVA_TASA
    return subtotal, iva, subtotal + iva

def obtener_caja_hoy():
    return CierreCaja.query.filter_by(fecha=date.today()).first()

@ventas_bp.route("/abrir-caja", methods=["POST"])
def abrir_caja():
    usuario_id = session.get("user_id")
    monto_inicial = request.form.get("monto_inicial", type=float)
    
    if monto_inicial is None or monto_inicial < 0:
        flash("Monto inicial inválido", "danger")
        return redirect(url_for("ventas.punto_venta"))

    if obtener_caja_hoy():
        flash("La caja ya fue abierta el día de hoy.", "warning")
        return redirect(url_for("ventas.punto_venta"))

    nueva_caja = CierreCaja(
        fecha=date.today(), usuario_id=usuario_id, monto_inicial=monto_inicial,
        estado="abierta", fecha_apertura=datetime.utcnow()
    )
    db.session.add(nueva_caja)
    
    movimiento = MovimientoCaja(
        tipo="ENTRADA", concepto="Apertura de Caja (Fondo Inicial)",
        monto=monto_inicial, creado_por=usuario_id, fecha=datetime.utcnow()
    )
    db.session.add(movimiento)
    db.session.commit()
    
    flash("Caja abierta exitosamente.", "success")
    return redirect(url_for("ventas.punto_venta"))

@ventas_bp.route("/pos", methods=["GET"])
def punto_venta():
    caja = obtener_caja_hoy()
    session_id = session.get("session_id")
    if not session_id:
        session_id = str(uuid.uuid4())
        session["session_id"] = session_id

    busqueda = request.args.get("busqueda", "").strip()

    if busqueda != "":
        productos = Producto.query.filter(
            (Producto.nombre.ilike(f"%{busqueda}%")) | (Producto.sku.ilike(f"%{busqueda}%"))
        ).all()
    else:
        productos = Producto.query.filter(Producto.stock_actual > 0).all()

    carrito = CarritoTemporal.query.filter_by(session_id=session_id).all()
    subtotal = sum([item.precio * item.cantidad for item in carrito]) if carrito else Decimal("0.00")
    iva = subtotal * IVA_TASA
    total = subtotal + iva

    return render_template("punto_venta.html", productos=productos, carrito=carrito, subtotal=subtotal, iva=iva, total=total, caja=caja)

@ventas_bp.route("/agregar", methods=["POST"])
def agregar_producto():
    caja = obtener_caja_hoy()
    if not caja or caja.estado == 'cerrada':
        flash("Operación no permitida. Verifica el estado de la caja.", "danger")
        return redirect(url_for("ventas.punto_venta"))

    session_id = session.get("session_id")
    producto_id = request.form.get("producto_id")
    cantidad = int(request.form.get("cantidad"))
    producto = Producto.query.get(producto_id)

    if cantidad > producto.stock_actual:
        flash("Stock insuficiente", "danger")
        return redirect(url_for("ventas.punto_venta"))

    item_existente = CarritoTemporal.query.filter_by(session_id=session_id, producto_id=producto.id).first()
    if item_existente:
        item_existente.cantidad += cantidad
    else:
        db.session.add(CarritoTemporal(
            session_id=session_id, producto_id=producto.id, nombre=producto.nombre,
            precio=producto.precio_venta, cantidad=cantidad
        ))
    
    db.session.commit()
    return redirect(url_for("ventas.punto_venta"))

@ventas_bp.route("/finalizar", methods=["POST"])
def finalizar_venta():
    caja = obtener_caja_hoy()
    if not caja or caja.estado == 'cerrada':
        flash("Operación no permitida. Verifica el estado de la caja.", "danger")
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
        nueva_venta = Venta(folio=_siguiente_folio_venta(), usuario_id=usuario_id, estado="Pagado", tipo="POS")
        db.session.add(nueva_venta)
        db.session.flush()
        
        total_venta_sin_iva = Decimal("0.00")
        
        for item in carrito: 
            producto = Producto.query.get(item.producto_id)
            if producto.stock_actual < item.cantidad:
                raise ValueError(f"Stock insuficiente para producto: {producto.nombre}")
            
            db.session.add(DetalleVenta(
                venta_id=nueva_venta.id, producto_id=item.producto_id,
                cantidad=item.cantidad, precio_unitario=item.precio, costo_unitario=producto.costo_produccion
            ))
            producto.stock_actual -= item.cantidad
            total_venta_sin_iva += (Decimal(str(item.precio)) * item.cantidad)
        
        total_con_iva = total_venta_sin_iva + (total_venta_sin_iva * IVA_TASA)
        
        db.session.add(MovimientoCaja(
            tipo="ENTRADA", concepto=f"Venta en Mostrador - Folio: {nueva_venta.folio}",
            monto=total_con_iva, id_venta=nueva_venta.id, creado_por=usuario_id, fecha=datetime.utcnow()
        ))
        
        CarritoTemporal.query.filter_by(session_id=session_id).delete()
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
        flash(f"Error crítico: {str(e)}", "danger")
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
    if not venta_id: return redirect(url_for("ventas.punto_venta"))
    venta = Venta.query.get(venta_id)
    detalles = DetalleVenta.query.filter_by(venta_id=venta.id).all()
    subtotal, iva, total = calcular_totales(detalles)
    return render_template("ticket.html", venta=venta, detalles=detalles, subtotal=subtotal, iva=iva, total=total)

@ventas_bp.route("/api/datos-cierre")
def datos_cierre():
    caja = obtener_caja_hoy()
    if not caja or caja.estado == "cerrada":
        return {"error": "No hay caja abierta"}, 400
        
    resultado = db.session.execute(text("""
        SELECT SUM(dv.cantidad * dv.precio_unitario) AS total_ventas
        FROM ventas v
        JOIN detalle_ventas dv ON v.id = dv.venta_id
        WHERE DATE(v.fecha) = CURDATE() AND v.tipo = 'POS'
    """)).mappings().first()
    
    total_ventas = resultado["total_ventas"] or 0
    monto_inicial = caja.monto_inicial
    total_esperado = float(monto_inicial) + (float(total_ventas) * 1.16) 
    
    return {"monto_inicial": float(monto_inicial), "total_ventas": float(total_ventas) * 1.16, "total_esperado": total_esperado}

@ventas_bp.route("/cierre-diario", methods=["GET", "POST"])
def cierre_diario():
    if request.method == "POST":
        caja = obtener_caja_hoy()
        if not caja or caja.estado == 'cerrada':
            flash("No hay caja abierta.", "warning")
            return redirect(url_for("ventas.punto_venta"))

        resultado = db.session.execute(text("""
            SELECT SUM(dv.cantidad) AS articulos_vendidos,
                   SUM(dv.cantidad * dv.precio_unitario) AS total_ventas,
                   SUM(dv.cantidad * (dv.precio_unitario - dv.costo_unitario)) AS utilidad_total
            FROM ventas v
            JOIN detalle_ventas dv ON v.id = dv.venta_id
            WHERE DATE(v.fecha) = CURDATE() AND v.tipo = 'POS'
        """)).mappings().first()

        caja.articulos_vendidos = resultado["articulos_vendidos"] or 0
        caja.total_ventas = resultado["total_ventas"] or 0
        caja.utilidad_total = resultado["utilidad_total"] or 0
        caja.estado = "cerrada"
        caja.fecha_cierre = datetime.utcnow()

        db.session.commit()
        flash("Cierre sellado correctamente.", "success")
        return redirect(url_for("ventas.cierre_diario"))

    cierre = CierreCaja.query.order_by(CierreCaja.fecha.desc()).first()
    return render_template("cierre_diario.html", cierre=cierre)