import os
from flask import Flask, render_template, session, flash, redirect, url_for, request
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv
from datetime import timedelta
from proveedores.routes import proveedores_bp
from materiales.routes import unidades_bp
from materiales.routes import materias_bp
import time
from sqlalchemy import text
from pedidos import pedidos_bp


from KPIs.routes import dashboard_bp

from caja.routes import compras_bp
from models import db, Usuario, Producto, MateriaPrima, Venta, DetalleVenta, OrdenProduccion, crear_vista_cierre_diario
from werkzeug.utils import secure_filename
import forms
from forms import UserForm
from ventas import ventas_bp
from tiendaCliente.routes import tienda_bp
from productos.routes import productos_bp
from recetas.routes import recetas_bp
from produccion.routes import produccion_bp


load_dotenv()

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/img/productos'

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
    'DATABASE_URL', 
    'mysql+pymysql://vellum_user:vellum_password_123@db/vellum_db'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'clave_segura_vellum_123')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=10)



db.init_app(app)
csrf = CSRFProtect(app)
app.register_blueprint(proveedores_bp)
app.register_blueprint(productos_bp)
app.register_blueprint(recetas_bp)

app.register_blueprint(compras_bp)
app.register_blueprint(unidades_bp)
app.register_blueprint(materias_bp)
app.register_blueprint(produccion_bp)

app.register_blueprint(pedidos_bp)
app.register_blueprint(ventas_bp, url_prefix="/ventas")
app.register_blueprint(dashboard_bp)
app.register_blueprint(tienda_bp, url_prefix="/tienda")

with app.app_context():
    intentos = 0
    while intentos < 2: # Damos 50 segundos totales para que MySQL despierte
        try:
            db.create_all()
            print("Tablas creadas con éxito.")
            crear_vista_cierre_diario()
            print("Vista de cierre diario operativa.")
            break
        except Exception as e:
            intentos += 1
            print(f"Esperando a MySQL (Intento {intentos}/10)...")
            time.sleep(5)

@app.before_request
def verificar_sesion():
    rutas_publicas = ['login', 'static']

    if request.endpoint not in rutas_publicas and 'user_id' not in session:
        return redirect(url_for('login'))
    
@app.route('/')
def index():
    print("Sesion:", dict(session), flush=True)
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = UserForm()
    if form.validate_on_submit():
        user = Usuario.query.filter_by(username=form.username.data).first()
        
        if not user:
            flash("El usuario no existe.", "danger")
            return render_template('login.html', form=form)
            
        if user.esta_bloqueado or user.intentos_fallidos >= 3:
            flash("Cuenta bloqueada por seguridad. Contacte al admin.", "danger")
            return render_template('login.html', form=form)
            
        if check_password_hash(user.password, form.password.data):
            user.intentos_fallidos = 0
            db.session.commit()
            
            session['user_id'] = user.id
            session['user_role'] = user.rol.nombre 
            session.permanent = True
            
            if session['user_role'] == 'Cliente':
                return redirect(url_for('tiendaCliente.index')) 
            else:
                return redirect(url_for('index'))
                
        else:
            user.intentos_fallidos += 1
            if user.intentos_fallidos >= 3:
                user.esta_bloqueado = True
            db.session.commit()
            flash(f"Contraseña incorrecta. Intento {user.intentos_fallidos} de 3.", "warning")

    return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    session.clear()
    flash("Has cerrado sesión correctamente", "info")
    return redirect(url_for('login'))

#CRUD Productos
@app.route("/productos")
def listar_productos():
    productos = Producto.query.all()
    return render_template("productos/index.html", productos=productos)

@app.route("/productos/nuevo", methods=['GET', 'POST'])
def crear_producto():

    form = forms.ProductoForm(request.form)

    if request.method == 'POST' and form.validate():

        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

        f = request.files['imagen']
        filename = secure_filename(f.filename)
        f.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
        nuevo_prod = Producto(
            sku=form.sku.data,
            nombre=form.nombre.data,
            linea=form.linea.data,
            categoria=form.categoria.data,
            precio_venta=form.precio.data,
            stock_actual=form.stock.data,
            imagen=filename
        )
        db.session.add(nuevo_prod)
        db.session.commit()
        flash("Producto registrado con éxito")
        return redirect(url_for('listar_productos'))

    return render_template("productos/crear.html", form=form)

@app.route("/modificar_producto", methods=['GET', 'POST'])
def modificar_producto():
    form = forms.ProductoForm(request.form)
    
    if request.method == 'GET':
        id = request.args.get('id')
        prod = db.session.query(Producto).filter(Producto.id == id).first()
        
        if prod:
            form.id.data = id
            form.nombre.data = prod.nombre
            form.linea.data = prod.linea
            form.categoria.data = prod.categoria
            form.precio.data = prod.precio_venta
        else:
            flash("Producto no encontrado")
            return redirect(url_for('listar_productos'))

    if request.method == 'POST':
        id = form.id.data
        prod = db.session.query(Producto).filter(Producto.id == id).first()

        if prod:
            # Actualizamos los campos con lo que el usuario escribió en el formulario
            prod.nombre = str.rstrip(form.nombre.data)
            prod.linea = form.linea.data
            prod.categoria = form.categoria.data
            prod.precio_venta = form.precio.data
            
            # Lógica opcional: Si subió una nueva imagen, la reemplazamos [cite: 30]
            if 'imagen' in request.files:
                f = request.files['imagen']
                if f.filename != '':
                    filename = secure_filename(f.filename)
                    f.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    prod.imagen = filename
            
            db.session.add(prod)
            db.session.commit()
            flash("Producto actualizado correctamente")
            return redirect(url_for('listar_productos'))
            
    return render_template("productos/modificar.html", form=form)

@app.route("/productos/eliminar", methods=['GET', 'POST'])
def eliminar_producto():
    id = request.args.get('id')
    prod = Producto.query.get(id)
    if request.method == 'POST':
        db.session.delete(prod)
        db.session.commit()
        return redirect(url_for('listar_productos'))
    return render_template("productos/eliminar.html", producto=prod)



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)