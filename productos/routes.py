import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from werkzeug.utils import secure_filename
from models import db, Producto
import forms

# Definición del Blueprint con nombre único
productos_bp = Blueprint("productos", __name__)

# ─────────────────────────────────────────────
# LISTADO (R)
# ─────────────────────────────────────────────
@productos_bp.route("/productos")
def listar_productos():
    productos = Producto.query.all()
    return render_template("productos/index.html", productos=productos)

# ─────────────────────────────────────────────
# CREAR (C) - Incluye validación de imagen
# ─────────────────────────────────────────────
@productos_bp.route("/productos/nuevo", methods=['GET', 'POST'])
def crear_producto():
    form = forms.ProductoForm(request.form)
    
    if request.method == 'POST' and form.validate():
        filename = None
        if 'imagen' in request.files:
            f = request.files['imagen']
            if f.filename != '':
                # Validación crítica: extensión de archivo [cite: 38]
                filename = secure_filename(f.filename)
                ext = os.path.splitext(filename)[1].lower()
                
                if ext in ['.jpg', '.jpeg', '.png']:
                    os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
                    f.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                else:
                    flash("Error: Solo se permiten archivos .jpg o .png", "danger")
                    return render_template("productos/crear.html", form=form)
        
        nuevo_prod = Producto(
            sku=form.sku.data,
            nombre=form.nombre.data,
            linea=form.linea.data, # Executive, Lifestyle, Essentials [cite: 33]
            categoria=form.categoria.data,
            precio_venta=form.precio.data,
            stock_actual=form.stock.data,
            imagen=filename
        )
        
        db.session.add(nuevo_prod)
        db.session.commit()
        flash("Producto de marroquinería registrado con éxito", "success")
        return redirect(url_for('productos.listar_productos'))
    
    return render_template("productos/crear.html", form=form)

# ─────────────────────────────────────────────
# MODIFICAR (U)
# ─────────────────────────────────────────────
@productos_bp.route("/productos/modificar/<int:id>", methods=['GET', 'POST'])
def modificar_producto(id):
    prod = Producto.query.get_or_404(id)
    form = forms.ProductoForm(obj=prod)
    
    if request.method == 'POST' and form.validate():
        prod.nombre = form.nombre.data
        prod.linea = form.linea.data
        prod.categoria = form.categoria.data
        prod.precio_venta = form.precio.data
        
        if 'imagen' in request.files:
            f = request.files['imagen']
            if f.filename != '':
                filename = secure_filename(f.filename)
                f.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                prod.imagen = filename
        
        db.session.commit()
        flash("Datos de producción actualizados", "info")
        return redirect(url_for('productos.listar_productos'))
        
    return render_template("productos/modificar.html", form=form, prod=prod)

# ─────────────────────────────────────────────
# ELIMINAR (D)
# ─────────────────────────────────────────────
@productos_bp.route("/productos/eliminar/<int:id>", methods=['POST'])
def eliminar_producto(id):
    prod = Producto.query.get_or_404(id)
    db.session.delete(prod)
    db.session.commit()
    flash("Producto removido del catálogo", "warning")
    return redirect(url_for('productos.listar_productos'))