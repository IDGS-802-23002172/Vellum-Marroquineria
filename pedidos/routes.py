from flask import Blueprint, jsonify, request, session, redirect, url_for, render_template
from models import db, Venta

pedidos_bp = Blueprint("pedidos", __name__, url_prefix="/pedidos")


# ─────────────────────────────────────────────
# VALIDACIÓN DE SESIÓN
# ─────────────────────────────────────────────
def validar_sesion():
    return 'user_id' in session


# ─────────────────────────────────────────────
# VISTA PRINCIPAL (HTML)
# ─────────────────────────────────────────────
@pedidos_bp.route("/view")
def vista_pedidos():
    if not validar_sesion():
        return redirect(url_for('login'))

    user_id = session['user_id']
    id_pedido = request.args.get("pedido_id")

    pedidos = Venta.query.filter_by(usuario_id=user_id)\
                         .order_by(Venta.fecha.desc())\
                         .all()

    pedido_detalle = None

    if id_pedido:
        pedido_detalle = Venta.query.filter_by(
            id=id_pedido,
            usuario_id=user_id
        ).first()

    return render_template(
        "misPedidos/misPedidos.html",
        pedidos=pedidos,
        pedido_detalle=pedido_detalle
    )


# ─────────────────────────────────────────────
# OBTENER TODOS LOS PEDIDOS (API)
# ─────────────────────────────────────────────
@pedidos_bp.route("/", methods=["GET"])
def obtener_pedidos():
    if not validar_sesion():
        return jsonify({"success": False, "message": "No autenticado"}), 401

    try:
        user_id = session['user_id']

        pedidos = Venta.query.filter_by(usuario_id=user_id)\
                             .order_by(Venta.fecha.desc())\
                             .all()

        resultado = []
        for pedido in pedidos:
            resultado.append({
                "id": pedido.id,
                "fecha": pedido.fecha.strftime("%Y-%m-%d %H:%M:%S"),
                "subtotal": float(pedido.subtotal or 0),
                "iva": float(pedido.iva or 0),
                "total": float(pedido.total or 0)
            })

        return jsonify({
            "success": True,
            "pedidos": resultado
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ─────────────────────────────────────────────
# DETALLE DE PEDIDO
# ─────────────────────────────────────────────
@pedidos_bp.route("/<int:id_pedido>", methods=["GET"])
def obtener_detalle_pedido(id_pedido):
    if not validar_sesion():
        return jsonify({"success": False}), 401

    try:
        user_id = session['user_id']

        pedido = Venta.query.filter_by(id=id_pedido, usuario_id=user_id).first()

        if not pedido:
            return jsonify({
                "success": False,
                "message": "Pedido no encontrado"
            }), 404

        detalles = []
        for d in pedido.detalles:
            detalles.append({
                "producto_id": d.producto_id,
                "nombre": d.producto.nombre,
                "cantidad": d.cantidad,
                "precio_unitario": float(d.precio_unitario),
                "subtotal": float(d.subtotal)
            })

        return jsonify({
            "success": True,
            "pedido": {
                "id": pedido.id,
                "fecha": pedido.fecha.strftime("%Y-%m-%d %H:%M:%S"),
                "total": float(pedido.total or 0),
                "detalles": detalles
            }
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500