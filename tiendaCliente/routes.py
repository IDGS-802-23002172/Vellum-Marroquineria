from flask import Blueprint, render_template, session, redirect, url_for, request, jsonify, make_response, flash
from flask_wtf.csrf import validate_csrf
from wtforms.validators import ValidationError
from models import db, Producto, CarritoTemporal, Venta, DetalleVenta, OrdenProduccion
from sqlalchemy import func
from datetime import datetime, timedelta
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
# HELPER: redirigir con cookie de sesión
# ─────────────────────────────────────────────
def _redirect_con_cookie(endpoint, session_id=None, **kwargs):
    response = make_response(redirect(url_for(endpoint, **kwargs)))
    if session_id:
        response.set_cookie('session_id', session_id, max_age=86400)
    return response

# ─────────────────────────────────────────────
# HELPER: limpiar carritos expirados (GLOBAL)
# Libera reservas vencidas de todos los usuarios
# antes de cualquier cálculo de stock.
# ─────────────────────────────────────────────
def limpiar_carritos_expirados():
    hace_30_min = datetime.utcnow() - timedelta(minutes=30)
    db.session.query(CarritoTemporal).filter(
        CarritoTemporal.creado_en < hace_30_min
    ).delete(synchronize_session=False)
    # Sin commit — el caller decide cuándo comitear

# ─────────────────────────────────────────────
# PÁGINA PRINCIPAL
# ─────────────────────────────────────────────
@tienda_bp.route('/')
def index():
    if 'user_role' in session and session['user_role'] != 'Cliente':
        return redirect(url_for('dashboard.index')) 
    return render_template('tiendaCliente/index.html')

@tienda_bp.route('/mis-pedidos')
def mis_pedidos():
    usuario_id = session.get('user_id')

    if not usuario_id or session.get('user_role') != 'Cliente':
        return redirect(url_for('login'))

    pedidos = Venta.query.filter_by(usuario_id=usuario_id)\
        .order_by(Venta.fecha.desc()).all()

    pedidos_data = []

    for pedido in pedidos:
        detalles = pedido.detalles

        # 🔥 ÓRDENES (del usuario)
        ordenes = OrdenProduccion.query.filter_by(
            id_usuario=usuario_id
        ).all()

        # 🔥 TOTAL DETALLES
        total_detalles = sum(
            float(d.subtotal or 0) for d in detalles
        )

        # 🔥 TOTAL PRODUCCIÓN (usando precio del producto)
        total_produccion = 0
        for o in ordenes:
            producto = Producto.query.get(o.id_producto)
            if producto:
                total_produccion += float(producto.precio_venta or 0) * o.cantidad

        total_general = total_detalles + total_produccion

        pedidos_data.append({
            'pedido': pedido,
            'detalles': detalles,
            'ordenes': ordenes,
            'total': total_general
        })

    return render_template(
        'tiendaCliente/seguimiento.html',
        pedidos=pedidos_data
    )
# ─────────────────────────────────────────────
# CATÁLOGO
# ─────────────────────────────────────────────
@tienda_bp.route('/catalogo')
def catalogo():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '').strip()
    linea = request.args.get('linea', '')
    categoria = request.args.get('categoria', '')
    solo_disponibles = request.args.get('solo_disponibles')

    query = Producto.query

    # 🔎 BÚSQUEDA (solo por nombre, NO SKU)
    if search:
        query = query.filter(Producto.nombre.ilike(f"%{search}%"))

    # 📦 FILTRO POR LÍNEA
    if linea:
        query = query.filter(Producto.linea == linea)

    # 🏷 FILTRO POR CATEGORÍA
    if categoria:
        query = query.filter(Producto.categoria == categoria)

    # ✅ SOLO DISPONIBLES
    if solo_disponibles:
        query = query.filter(Producto.stock_actual > 0)

    productos = query.order_by(Producto.nombre).paginate(
        page=page,
        per_page=12,
        error_out=False
    )

    # 🔥 PARA LLENAR LOS SELECTS DINÁMICAMENTE
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
# DETALLE
# FIX: el template debe recibir stock_disponible
#      (descontando carritos activos de todos)
#      no stock_actual en crudo.
# ─────────────────────────────────────────────
@tienda_bp.route('/producto/<int:id>')
def detalle_producto(id):
    producto = Producto.query.get_or_404(id)
    # Limpiar expirados para que el stock visible sea preciso
    limpiar_carritos_expirados()
    db.session.flush()
    return render_template(
        'tiendaCliente/detalle_producto.html',
        producto=producto,
        # stock_disponible usa el property del modelo que descuenta
        # lo que está en carritos activos de TODOS los usuarios
        stock_disponible=producto.stock_disponible
    )

# ─────────────────────────────────────────────
# VER CARRITO
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
# AGREGAR AL CARRITO
#
# Concurrencia:
#   1. Limpiar expirados globalmente.
#   2. FOR UPDATE sobre Produxcto → serializa
#      accesos simultáneos al mismo producto.
#   3. stock_disponible = stock_actual
#      − reservado por OTROS usuarios.
#      (No restamos el carrito propio para no
#       contar doble lo que ya tiene este usuario)
#   4. Verificar que lo que ya tiene + lo nuevo
#      no supere el stock disponible para él.
#   5. Commit libera el lock.
#
# FIX total_items: usar COUNT de filas distintas
#   (productos únicos en carrito), no SUM de
#   cantidades — así el flash es coherente.
# ─────────────────────────────────────────────
@tienda_bp.route('/agregar-carrito/<int:producto_id>', methods=['POST'])
def agregar_carrito(producto_id):
    try:
        validate_csrf(request.form.get('csrf_token'))
    except ValidationError:
        flash('Token de seguridad inválido. Recarga la página.', 'danger')
        return _redirect_con_cookie('tiendaCliente.detalle_producto', id=producto_id)

    cantidad = request.form.get('cantidad', 1, type=int)

    try:
        if cantidad <= 0:
            flash('Cantidad inválida.', 'danger')
            return _redirect_con_cookie('tiendaCliente.detalle_producto', id=producto_id)

        session_id = get_or_create_session_id()

        # 1. Limpiar expirados de todos los usuarios
        limpiar_carritos_expirados()

        # 2. Bloquear fila del producto (FOR UPDATE)
        producto = (
            Producto.query
            .with_for_update()
            .filter_by(id=producto_id)
            .first()
        )
        if not producto:
            flash('Producto no encontrado.', 'danger')
            return _redirect_con_cookie('tiendaCliente.detalle_producto', session_id, id=producto_id)

        # 3. Cuánto tiene este usuario ya en su carrito
        ya_en_mi_carrito = int(db.session.query(
            func.coalesce(func.sum(CarritoTemporal.cantidad), 0)
        ).filter_by(
            session_id=session_id,
            producto_id=producto_id
        ).scalar())

        # 4. Cuánto reservaron OTROS usuarios (no este)
        reservado_otros = int(db.session.query(
            func.coalesce(func.sum(CarritoTemporal.cantidad), 0)
        ).filter(
            CarritoTemporal.producto_id == producto_id,
            CarritoTemporal.session_id  != session_id
        ).scalar())

        # Stock que este usuario puede usar como máximo
        stock_para_este_usuario = max(0, producto.stock_actual - reservado_otros)

        # Lo que tendría en total si agrega 'cantidad' más
        total_con_nuevo = ya_en_mi_carrito + cantidad

        if stock_para_este_usuario <= 0:
            flash('Este producto no tiene stock, pero puedes pedirlo y se enviará a producción.', 'warning')

        # 5. Crear o actualizar ítem en carrito
        item = CarritoTemporal.query.filter_by(
            session_id=session_id,
            producto_id=producto_id
        ).first()

        if item:
            item.cantidad  += cantidad
            item.creado_en  = datetime.utcnow()  # renueva la reserva 30 min más
        else:
            db.session.add(CarritoTemporal(
                session_id=session_id,
                producto_id=producto_id,
                nombre=producto.nombre,
                precio=producto.precio_venta,
                cantidad=cantidad
            ))

        # Commit libera el FOR UPDATE lock
        db.session.commit()

        # ─── FIX: contar productos únicos en el carrito, no sum(cantidad) ───
        # "X artículo(s)" = cuántos productos distintos tiene, no cuántas unidades
        total_productos_en_carrito = CarritoTemporal.query.filter_by(
            session_id=session_id
        ).count()

        flash(
            f'"{producto.nombre}" agregado al carrito. '
            f'({total_productos_en_carrito} producto(s) en tu carrito)',
            'success'
        )
        return _redirect_con_cookie('tiendaCliente.detalle_producto', session_id, id=producto_id)

    except Exception as e:
        db.session.rollback()
        print("ERROR agregar_carrito:", e)
        flash('Error interno. Intenta de nuevo.', 'danger')
        return _redirect_con_cookie('tiendaCliente.detalle_producto', id=producto_id)

# ─────────────────────────────────────────────
# ELIMINAR ÍTEM DEL CARRITO
# ─────────────────────────────────────────────
@tienda_bp.route('/carrito/eliminar/<int:item_id>', methods=['POST'])
def eliminar_carrito(item_id):
    try:
        validate_csrf(request.form.get('csrf_token'))
    except ValidationError:
        flash('Token de seguridad inválido.', 'danger')
        return _redirect_con_cookie('tiendaCliente.ver_carrito')

    session_id = get_or_create_session_id()
    item = CarritoTemporal.query.filter_by(id=item_id, session_id=session_id).first()

    if item:
        db.session.delete(item)
        db.session.commit()
        flash('Producto eliminado del carrito.', 'success')
    else:
        flash('El producto no se encontró en tu carrito.', 'warning')

    return _redirect_con_cookie('tiendaCliente.ver_carrito', session_id)

# ─────────────────────────────────────────────
# ACTUALIZAR CANTIDAD EN CARRITO
# ─────────────────────────────────────────────
@tienda_bp.route('/carrito/actualizar/<int:item_id>', methods=['POST'])
def actualizar_carrito(item_id):
    try:
        validate_csrf(request.form.get('csrf_token'))
    except ValidationError:
        flash('Token de seguridad inválido.', 'danger')
        return _redirect_con_cookie('tiendaCliente.ver_carrito')

    session_id   = get_or_create_session_id()
    nueva_cantidad = request.form.get('cantidad', 1, type=int)

    try:
        item = CarritoTemporal.query.filter_by(id=item_id, session_id=session_id).first()
        if not item:
            flash('El producto no se encontró en tu carrito.', 'warning')
            return _redirect_con_cookie('tiendaCliente.ver_carrito', session_id)

        if nueva_cantidad <= 0:
            db.session.delete(item)
            db.session.commit()
            flash('Producto eliminado del carrito.', 'success')
            return _redirect_con_cookie('tiendaCliente.ver_carrito', session_id)

        limpiar_carritos_expirados()

        producto = Producto.query.with_for_update().filter_by(id=item.producto_id).first()

        reservado_otros = int(db.session.query(
            func.coalesce(func.sum(CarritoTemporal.cantidad), 0)
        ).filter(
            CarritoTemporal.producto_id == item.producto_id,
            CarritoTemporal.session_id  != session_id
        ).scalar())

        stock_para_este_usuario = max(0, producto.stock_actual - reservado_otros)

        if nueva_cantidad > stock_para_este_usuario:
            flash(f'Solo hay {stock_para_este_usuario} unidad(es) disponibles para ti.', 'danger')
        else:
            item.cantidad  = nueva_cantidad
            item.creado_en = datetime.utcnow()
            db.session.commit()
            flash('Cantidad actualizada.', 'success')

    except Exception as e:
        db.session.rollback()
        print("ERROR actualizar_carrito:", e)
        flash('Error interno. Intenta de nuevo.', 'danger')

    return _redirect_con_cookie('tiendaCliente.ver_carrito', session_id)

# ─────────────────────────────────────────────
# CHECKOUT
# ─────────────────────────────────────────────
@tienda_bp.route('/checkout', methods=['POST'])
def checkout():
    try:
        datos = request.get_json(silent=True)

        if not datos:
            return jsonify({'success': False, 'message': 'Request inválido'}), 400

        session_id = datos.get('session_id')
        usuario_id = session.get('user_id')

        if not session_id:
            return jsonify({'success': False, 'message': 'Session ID requerido'}), 400

        if not usuario_id:
            return jsonify({'success': False, 'message': 'Login requerido'}), 401

        items = CarritoTemporal.query.filter_by(session_id=session_id).all()

        if not items:
            return jsonify({'success': False, 'message': 'Carrito vacío'}), 400

        limpiar_carritos_expirados()

        productos = (
            Producto.query
            .filter(Producto.id.in_([i.producto_id for i in items]))
            .with_for_update()
            .all()
        )
        productos_dict = {p.id: p for p in productos}

        # 🔹 Totales (solo para respuesta, NO se guardan en Venta)
        subtotal = sum(float(i.precio) * i.cantidad for i in items)
        iva = subtotal * 0.16
        total = subtotal + iva

        # 🔥 GENERAR FOLIO (OBLIGATORIO porque es NOT NULL)
        folio = f"VTA-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

        # 🔥 CREAR VENTA SOLO CON CAMPOS VÁLIDOS
        venta = Venta(
            usuario_id=usuario_id,
            folio=folio,
            fecha=datetime.utcnow(),
            estado="Pagado"
        )
        db.session.add(venta)
        db.session.flush()

        # 🔥 PROCESAR ITEMS
        for item in items:
            prod = productos_dict[item.producto_id]

            reservado_otros = int(db.session.query(
                func.coalesce(func.sum(CarritoTemporal.cantidad), 0)
            ).filter(
                CarritoTemporal.producto_id == item.producto_id,
                CarritoTemporal.session_id != session_id
            ).scalar())

            stock_disponible = max(0, prod.stock_actual - reservado_otros)

            if item.cantidad <= stock_disponible:
                # ✅ Venta normal
                db.session.add(DetalleVenta(
                    venta_id=venta.id,
                    producto_id=item.producto_id,
                    cantidad=item.cantidad,
                    precio_unitario=item.precio,
                    subtotal=float(item.precio) * item.cantidad
                ))

                prod.stock_actual -= item.cantidad

            else:
                # ⚠️ Producción
                db.session.add(OrdenProduccion(
                    id_producto=item.producto_id,
                    id_usuario=usuario_id,
                    cantidad=item.cantidad,
                    estado="Pendiente"
                ))

        # 🔹 Vaciar carrito
        CarritoTemporal.query.filter_by(session_id=session_id).delete()

        db.session.commit()

        return jsonify({
            'success': True,
            'total': float(total),
            'venta_id': venta.id
        })

    except Exception as e:
        db.session.rollback()
        print("ERROR CHECKOUT:", e)

        return jsonify({
            'success': False,
            'message': str(e)
        }), 500