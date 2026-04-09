from flask import Blueprint, render_template, session, redirect, url_for, request, jsonify, make_response, flash
from flask_wtf.csrf import validate_csrf
from wtforms.validators import ValidationError
from models import db, Producto, CarritoTemporal, Venta, DetalleVenta, OrdenProduccion, MovimientoCaja
from sqlalchemy import func
from datetime import datetime, timedelta
from decimal import Decimal
import uuid

tienda_bp = Blueprint('tiendaCliente', __name__)

# ─────────────────────────────────────────────
# HELPER: obtener o crear session_id
# ─────────────────────────────────────────────
def get_or_create_session_id():
    session_id = request.cookies.get('session_id')
    if not session_id:
        session_id = str(uuid.uuid4())
    return session_id

# ─────────────────────────────────────────────
def _redirect_con_cookie(endpoint, session_id=None, **kwargs):
    response = make_response(redirect(url_for(endpoint, **kwargs)))
    if session_id:
        response.set_cookie('session_id', session_id, max_age=86400)
    return response

# ─────────────────────────────────────────────
def limpiar_carritos_expirados():
    hace_30_min = datetime.utcnow() - timedelta(minutes=30)
    db.session.query(CarritoTemporal).filter(
        CarritoTemporal.creado_en < hace_30_min
    ).delete(synchronize_session=False)

# ─────────────────────────────────────────────
@tienda_bp.route('/')
def index():
    if 'user_role' in session and session['user_role'] != 'Cliente':
        return redirect(url_for('dashboard.index')) 
    return render_template('tiendaCliente/index.html')

# ─────────────────────────────────────────────
@tienda_bp.route('/mis-pedidos')
def mis_pedidos():
    usuario_id = session.get('user_id')
    if not usuario_id or session.get('user_role') != 'Cliente':
        return redirect(url_for('login'))
    
    pedidos = Venta.query.filter_by(usuario_id=usuario_id)\
        .order_by(Venta.fecha.desc()).all()
    
    return render_template('tiendaCliente/seguimiento.html', pedidos=pedidos)

# ─────────────────────────────────────────────
@tienda_bp.route('/catalogo')
def catalogo():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '').strip()
    linea = request.args.get('linea', '')
    categoria = request.args.get('categoria', '')
    solo_disponibles = request.args.get('solo_disponibles')

    query = Producto.query

    if search:
        query = query.filter(Producto.nombre.ilike(f"%{search}%"))

    if linea:
        query = query.filter(Producto.linea == linea)

    if categoria:
        query = query.filter(Producto.categoria == categoria)

    if solo_disponibles:
        query = query.filter(Producto.stock_actual > 0)

    productos = query.order_by(Producto.nombre).paginate(
        page=page,
        per_page=12,
        error_out=False
    )

    lineas = db.session.query(Producto.linea).distinct().all()
    categorias = db.session.query(Producto.categoria).distinct().all()

    return render_template(
        'tiendaCliente/catalogo.html',
        productos=productos,
        búsqueda=search,
        líneas=[l[0] for l in lineas if l[0]],
        categorías=[c[0] for c in categorias if c[0]],
        línea_actual=linea,
        categoría_actual=categoria
    )

# ─────────────────────────────────────────────
@tienda_bp.route('/producto/<int:id>')
def detalle_producto(id):
    producto = Producto.query.get_or_404(id)

    limpiar_carritos_expirados()
    db.session.flush()

    return render_template(
        'tiendaCliente/detalle_producto.html',
        producto=producto,
        stock_disponible=producto.stock_disponible
    )

# ─────────────────────────────────────────────
@tienda_bp.route('/carrito')
def ver_carrito():
    session_id = get_or_create_session_id()

    articulos = CarritoTemporal.query.filter_by(session_id=session_id).all()
    total = sum(float(a.precio or 0) * a.cantidad for a in articulos)

    response = make_response(render_template(
        'tiendaCliente/carrito.html',
        articulos=articulos,
        total=total,
        cantidad_articulos=len(articulos)
    ))
    response.set_cookie('session_id', session_id, max_age=86400)
    return response

# ─────────────────────────────────────────────
@tienda_bp.route('/agregar-carrito/<int:producto_id>', methods=['POST'])
def agregar_carrito(producto_id):
    try:
        validate_csrf(request.form.get('csrf_token'))
    except ValidationError:
        flash('Token de seguridad inválido.', 'danger')
        return _redirect_con_cookie('tiendaCliente.detalle_producto', id=producto_id)

    cantidad = request.form.get('cantidad', 1, type=int)

    try:
        if cantidad <= 0:
            flash('Cantidad inválida.', 'danger')
            return _redirect_con_cookie('tiendaCliente.detalle_producto', id=producto_id)

        session_id = get_or_create_session_id()
        limpiar_carritos_expirados()

        producto = Producto.query.get_or_404(producto_id)

        item = CarritoTemporal.query.filter_by(
            session_id=session_id,
            producto_id=producto_id
        ).first()

        if item:
            item.cantidad += cantidad
            item.creado_en = datetime.utcnow()
        else:
            db.session.add(CarritoTemporal(
                session_id=session_id,
                producto_id=producto_id,
                nombre=producto.nombre,
                precio=producto.precio_venta,
                cantidad=cantidad,
                creado_en=datetime.utcnow()
            ))

        db.session.commit()

        total_productos = CarritoTemporal.query.filter_by(session_id=session_id).count()

        flash(f'"{producto.nombre}" agregado ({total_productos} en carrito)', 'success')

        return _redirect_con_cookie('tiendaCliente.detalle_producto', session_id, id=producto_id)

    except Exception as e:
        db.session.rollback()
        print("ERROR agregar_carrito:", e)
        flash('Error interno.', 'danger')
        return _redirect_con_cookie('tiendaCliente.detalle_producto', id=producto_id)

# ─────────────────────────────────────────────
@tienda_bp.route('/checkout', methods=['POST'])
def checkout():
    try:
        csrf_token = request.headers.get("X-CSRFToken")
        validate_csrf(csrf_token)

        if not request.is_json:
            return jsonify({'success': False, 'message': 'JSON requerido'}), 400

        datos = request.get_json()
        session_id = datos.get('session_id')
        usuario_id = session.get('user_id')

        if not usuario_id:
            return jsonify({'success': False, 'message': 'Login requerido'}), 401

        items = CarritoTemporal.query.filter_by(session_id=session_id).all()
        if not items:
            return jsonify({'success': False, 'message': 'Carrito vacío'}), 400

        limpiar_carritos_expirados()

        productos = Producto.query.filter(
            Producto.id.in_([i.producto_id for i in items])
        ).with_for_update().all()

        productos_dict = {p.id: p for p in productos}

        detalles_venta = []
        orden_produccion = []
        total = Decimal("0.00")

        for item in items:
            prod = productos_dict.get(item.producto_id)
            if not prod:
                continue

            stock = prod.stock_actual or 0  # 🔥 evita None

            if item.cantidad <= stock:
                detalles_venta.append((prod, item))
            else:
                orden_produccion.append((prod, item))

            total += Decimal(str(item.precio or 0)) * item.cantidad

        venta = Venta(
            folio=generar_folio(),
            usuario_id=usuario_id,
            fecha=datetime.utcnow(),
            estado="Pagado",
            tipo="ONLINE"
        )

        db.session.add(venta)
        db.session.flush()

        for prod, item in detalles_venta:
            db.session.add(DetalleVenta(
                venta_id=venta.id,
                producto_id=prod.id,
                cantidad=item.cantidad,
                precio_unitario=item.precio,
                costo_unitario=prod.costo_produccion or 0
            ))
            prod.stock_actual = (prod.stock_actual or 0) - item.cantidad

        for prod, item in orden_produccion:
            db.session.add(OrdenProduccion(
                id_usuario=usuario_id,
                id_producto=prod.id,
                cantidad=item.cantidad,
                estado="En Corte"
            ))

        movimiento = MovimientoCaja(
            tipo="ENTRADA",
            concepto=f"Venta {venta.folio}",
            monto=total * Decimal("1.16"),
            id_venta=venta.id,
            creado_por=usuario_id,
            fecha=datetime.utcnow()
        )

        db.session.add(movimiento)

        CarritoTemporal.query.filter_by(session_id=session_id).delete()

        db.session.commit()

        return jsonify({'success': True})

    except Exception as e:
        db.session.rollback()
        import traceback
        traceback.print_exc()
        print("ERROR CHECKOUT:", e)
        return jsonify({'success': False, 'message': str(e)}), 500

# ─────────────────────────────────────────────
def generar_folio():
    fecha = datetime.now().strftime("%Y%m%d")
    ultima = Venta.query.order_by(Venta.id.desc()).first()
    numero = (ultima.id + 1) if ultima else 1
    return f"T-{fecha}-{numero:04d}"