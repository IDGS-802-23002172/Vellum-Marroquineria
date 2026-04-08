import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from werkzeug.utils import secure_filename
from models import db, Producto
import forms

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
                filename = secure_filename(f.filename)
                ext = os.path.splitext(filename)[1].lower()
                
                if ext in ['.jpg', '.jpeg', '.png']:
                    try:
                        os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
                        f.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                    except Exception as e:
                        flash(f"Error al guardar la imagen: {str(e)}", "danger")
                        return render_template("productos/crear.html", form=form)
                else:
                    flash("Error: Solo se permiten archivos .jpg o .png", "danger")
                    return render_template("productos/crear.html", form=form)
        
        try:
            nuevo_prod = Producto(
                sku=form.sku.data,
                nombre=form.nombre.data,
                linea=form.linea.data, 
                categoria=form.categoria.data,
                precio_venta=form.precio.data,
                stock_actual=0, 
                area_plantilla_base=form.area_plantilla.data, 
                imagen=filename
            )
            
            db.session.add(nuevo_prod)
            db.session.commit()
            flash("Producto de marroquinería registrado con éxito. Stock inicializado en 0.", "success")
            return redirect(url_for('productos.listar_productos'))

        except Exception as e:
            db.session.rollback()
            flash(f"Error crítico de base de datos: {str(e)}", "danger")
            return render_template("productos/crear.html", form=form)
    
    return render_template("productos/crear.html", form=form)

# ─────────────────────────────────────────────
# MODIFICAR (U)
# ─────────────────────────────────────────────
@productos_bp.route("/productos/modificar/<int:id>", methods=['GET', 'POST'])
def modificar_producto(id):
    prod = Producto.query.get_or_404(id)
    form = forms.ProductoForm(obj=prod)
    
    if request.method == 'POST' and form.validate():
        try:
            prod.nombre = form.nombre.data
            prod.linea = form.linea.data
            prod.categoria = form.categoria.data
            prod.precio_venta = form.precio.data
            prod.area_plantilla_base = form.area_plantilla.data
            
            if 'imagen' in request.files:
                f = request.files['imagen']
                if f.filename != '':
                    filename = secure_filename(f.filename)
                    f.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                    prod.imagen = filename
            
            db.session.commit()
            flash("Datos de producción actualizados", "info")
            return redirect(url_for('productos.listar_productos'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error al modificar: {str(e)}", "danger")
            return render_template("productos/modificar.html", form=form, prod=prod)
            
    return render_template("productos/modificar.html", form=form, prod=prod)

# ─────────────────────────────────────────────
# ELIMINAR (D)
# ─────────────────────────────────────────────
@productos_bp.route("/productos/eliminar/<int:id>", methods=['POST'])
def eliminar_producto(id):
    prod = Producto.query.get_or_404(id)
    try:
        db.session.delete(prod)
        db.session.commit()
        flash("Producto removido del catálogo", "warning")
    except Exception as e:
        db.session.rollback()
        flash(f"Error al eliminar: {str(e)}", "danger")
        
    return redirect(url_for('productos.listar_productos'))

# ─────────────────────────────────────────────
# GESTIÓN DE MERMAS (Nueva Funcionalidad)
# ─────────────────────────────────────────────
@productos_bp.route('/productos/merma/<int:id>', methods=['POST'])
def registrar_merma_producto(id):
    producto = Producto.query.get_or_404(id)
    justificacion = request.form.get('justificacion')
    cantidad_str = request.form.get('cantidad_merma')

    if not cantidad_str or not cantidad_str.isdigit():
        flash("Error: Cantidad de merma inválida", "danger")
        return redirect(url_for('productos.listar_productos'))

    cantidad = int(cantidad_str)

    if not justificacion or len(justificacion) < 10:
        flash("Error: Debes proporcionar una justificación detallada (mínimo 10 caracteres)", "warning")
        return redirect(url_for('productos.listar_productos'))

    if cantidad > producto.stock_actual:
        flash("Error: La cantidad de merma no puede ser mayor al stock actual", "danger")
        return redirect(url_for('productos.listar_productos'))

    try:
        producto.stock_actual -= cantidad
        db.session.commit()
        flash(f"Merma registrada exitosamente para {producto.nombre}. Motivo: {justificacion}", "info")
    except Exception as e:
        db.session.rollback()
        flash(f"Error al registrar merma: {str(e)}", "danger")
    
    return redirect(url_for('productos.listar_productos'))

@productos_bp.route("/api/get_area/<int:id>")
def get_area_producto(id):
    p = Producto.query.get_or_404(id)
    return {"area": float(p.area_plantilla_base)}