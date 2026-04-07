from flask import Blueprint, jsonify, render_template, request
from sqlalchemy import func, extract
from models import db, Venta, DetalleVenta, Producto
from datetime import datetime

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")


@dashboard_bp.route("/", methods=["GET"])
def dashboard_view():
    return render_template("KPIs/dashboard.html")

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

    query = db.session.query(
        func.sum(
            (DetalleVenta.precio_unitario - DetalleVenta.costo_unitario) * DetalleVenta.cantidad
        ),
        func.sum(DetalleVenta.costo_unitario * DetalleVenta.cantidad)
    ).join(Venta)

    query = aplicar_filtro_fecha(query)

    resultados = query.first()

    ganancia = resultados[0] or 0
    inversion = resultados[1] or 0

    roi = (ganancia / inversion * 100) if inversion > 0 else 0

    return jsonify({
        "ganancia": float(ganancia),
        "inversion": float(inversion),
        "roi": round(float(roi), 2)
    })


# -------------------------------
# Helper filtro fechas
# -------------------------------
def aplicar_filtro_fecha(query):
    fecha_inicio = request.args.get("fecha_inicio")
    fecha_fin = request.args.get("fecha_fin")

    if fecha_inicio:
        query = query.filter(Venta.fecha >= datetime.strptime(fecha_inicio, "%Y-%m-%d"))
    if fecha_fin:
        query = query.filter(Venta.fecha <= datetime.strptime(fecha_fin, "%Y-%m-%d"))

    return query


# -------------------------------
# KPI: Ventas totales (FILTRABLE)
# -------------------------------
@dashboard_bp.route("/ventas-totales", methods=["GET"])
def ventas_totales():

    query = db.session.query(func.sum(DetalleVenta.cantidad * DetalleVenta.precio_unitario))\
        .join(Venta)

    query = aplicar_filtro_fecha(query)

    total = query.scalar() or 0

    return jsonify({"ventas_totales": float(total)})


# -------------------------------
# KPI: Producto más vendido
# -------------------------------
@dashboard_bp.route("/producto-top", methods=["GET"])
def producto_top():

    query = db.session.query(
        Producto.nombre,
        func.sum(DetalleVenta.cantidad).label("total_unidades"),
        func.sum(DetalleVenta.cantidad * DetalleVenta.precio_unitario).label("total_ventas")
    ).join(DetalleVenta)\
     .join(Venta)

    query = aplicar_filtro_fecha(query)

    resultado = query.group_by(Producto.id)\
        .order_by(func.sum(DetalleVenta.cantidad).desc())\
        .first()

    if not resultado:
        return jsonify({})

    return jsonify({
        "nombre": resultado[0],
        "unidades": int(resultado[1]),
        "total": float(resultado[2])
    })


# -------------------------------
# KPI: Top 5 productos
# -------------------------------
@dashboard_bp.route("/top-productos", methods=["GET"])
def top_productos():

    query = db.session.query(
        Producto.nombre,
        func.sum(DetalleVenta.cantidad).label("unidades"),
        func.avg(DetalleVenta.precio_unitario).label("precio_promedio")
    ).join(DetalleVenta)\
     .join(Venta)

    query = aplicar_filtro_fecha(query)

    resultados = query.group_by(Producto.id)\
        .order_by(func.sum(DetalleVenta.cantidad).desc())\
        .limit(5)\
        .all()

    data = [
        {
            "nombre": r[0],
            "unidades": int(r[1]),
            "precio": float(r[2])
        }
        for r in resultados
    ]

    return jsonify(data)


# -------------------------------
# Ventas mensuales (MEJORADA)
# -------------------------------
@dashboard_bp.route("/ventas-mensuales", methods=["GET"])
def ventas_mensuales():

    query = db.session.query(
        extract("year", Venta.fecha).label("anio"),
        extract("month", Venta.fecha).label("mes"),
        func.sum(DetalleVenta.cantidad).label("unidades"),
        func.sum(DetalleVenta.cantidad * DetalleVenta.precio_unitario).label("total")
    ).join(DetalleVenta)

    query = aplicar_filtro_fecha(query)

    resultados = query.group_by("anio", "mes")\
        .order_by("anio", "mes")\
        .all()

    return jsonify([
        {
            "anio": int(r.anio),
            "mes": int(r.mes),
            "total": float(r.total),
            "unidades": int(r.unidades)
        }
        for r in resultados
    ])


# -------------------------------
# Ventas por línea (MEJORADA)
# -------------------------------
@dashboard_bp.route("/ventas-por-linea", methods=["GET"])
def ventas_por_linea():

    query = db.session.query(
        Producto.linea,
        func.sum(DetalleVenta.cantidad).label("unidades"),
        func.sum(DetalleVenta.cantidad * DetalleVenta.precio_unitario).label("total")
    ).join(DetalleVenta)\
     .join(Venta)

    query = aplicar_filtro_fecha(query)

    resultados = query.group_by(Producto.linea).all()

    return jsonify([
        {
            "linea": r[0] or "Sin línea",
            "total": float(r.total),
            "unidades": int(r.unidades)
        }
        for r in resultados
    ])