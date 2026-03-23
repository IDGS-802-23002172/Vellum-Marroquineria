from flask import Blueprint, jsonify
from sqlalchemy import func, extract
from models import db, Venta, DetalleVenta, Producto
from flask import Blueprint, jsonify, render_template

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")


@dashboard_bp.route("/", methods=["GET"])
def dashboard_view():
    return render_template("KPIs/dashboard.html")

# -------------------------------
# KPI: Ventas totales
# -------------------------------
@dashboard_bp.route("/ventas-totales", methods=["GET"])
def ventas_totales():
    total = db.session.query(
        func.sum(DetalleVenta.subtotal)
    ).scalar() or 0

    return jsonify({"ventas_totales": float(total)})


# -------------------------------
# KPI: Stock crítico
# -------------------------------
@dashboard_bp.route("/stock-critico", methods=["GET"])
def stock_critico():
    productos = Producto.query.filter(Producto.stock_actual <= 5).all()

    data = [
        {
            "id": p.id,
            "nombre": p.nombre,
            "stock": p.stock_actual
        }
        for p in productos
    ]

    return jsonify({
        "total_productos_criticos": len(data),
        "productos": data
    })


# -------------------------------
# KPI: ROI
# -------------------------------
@dashboard_bp.route("/roi", methods=["GET"])
def roi():
    resultados = db.session.query(
        func.sum((DetalleVenta.precio_unitario - DetalleVenta.costo_unitario) * DetalleVenta.cantidad),
        func.sum(DetalleVenta.costo_unitario * DetalleVenta.cantidad)
    ).one()

    ganancia = resultados[0] or 0
    inversion = resultados[1] or 0

    roi = (ganancia / inversion * 100) if inversion > 0 else 0

    return jsonify({
        "ganancia": float(ganancia),
        "inversion": float(inversion),
        "roi": round(float(roi), 2)
    })


# -------------------------------
# KPI: Ventas mensuales
# -------------------------------
@dashboard_bp.route("/ventas-mensuales", methods=["GET"])
def ventas_mensuales():
    resultados = db.session.query(
        extract("year", Venta.fecha).label("anio"),
        extract("month", Venta.fecha).label("mes"),
        func.sum(DetalleVenta.subtotal).label("total")
    ).join(DetalleVenta, DetalleVenta.venta_id == Venta.id)\
    .group_by("anio", "mes")\
    .order_by("anio", "mes")\
    .all()

    data = [
        {
            "anio": int(r.anio),
            "mes": int(r.mes),
            "total": float(r.total)
        }
        for r in resultados
    ]

    return jsonify(data)

# -------------------------------
# KPI: Ventas por línea (gráfica pastel)
# -------------------------------
@dashboard_bp.route("/ventas-por-linea", methods=["GET"])
def ventas_por_linea():
    resultados = db.session.query(
        Producto.linea,
        func.sum(DetalleVenta.subtotal)
    ).join(DetalleVenta, DetalleVenta.producto_id == Producto.id)\
    .group_by(Producto.linea)\
    .all()

    data = [
        {
            "linea": r[0] if r[0] else "Sin línea",
            "total": float(r[1])
        }
        for r in resultados
    ]

    return jsonify(data)