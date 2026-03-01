import os
from flask import Flask, render_template, session, flash, redirect, url_for, request
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv
from datetime import timedelta
from proveedores.routes import proveedores_bp


from models import db, Usuario, Producto
from werkzeug.utils import secure_filename
import forms
from forms import UserForm      


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


with app.app_context():
    try:
        db.create_all()
        print("tablas creadas con exito")
    except Exception as e:
        print(f"error al conectar con la bd {e}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = UserForm()
    if form.validate_on_submit():
        user = Usuario.query.filter_by(username=form.username.data).first()
        if user.intentos_fallidos >= 3:
            flash("Cuenta bloqueada por seguridad. Contacte al admin.", "danger")
            return render_template('login.html', form=form)
        if user.password == form.password.data:
            user.intentos_fallidos = 0
            db.session.commit()
            session['user_id'] = user.id
            session.permanent = True 
            return redirect(url_for('index'))
        else:
            user.intentos_fallidos += 1
            db.session.commit()
            flash(f"Contraseña incorrecta. Intento {user.intentos_fallidos} de 3.", "warning")
    else:
        flash("El usuario no existe.", "danger")
    return render_template('login.html', form=form)

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
            nombre=form.nombre.data,
            linea=form.linea.data,
            categoria=form.categoria.data,
            precio_venta=form.precio.data,
            imagen=filename
        )
        db.session.add(nuevo_prod)
        db.session.commit()
        flash("Producto registrado con éxito")
        return redirect(url_for('listar_productos'))
    
    return render_template("productos/crear.html", form=form)

@app.route("/modificar_producto", methods=['GET', 'POST'])
def modificar_producto():
    # Usamos el formulario de productos que ya definimos
    form = forms.ProductoForm(request.form)
    
    if request.method == 'GET':
        id = request.args.get('id')
        # Buscamos el producto en la base de datos por su ID [cite: 93, 111]
        prod = db.session.query(Producto).filter(Producto.id == id).first()
        
        if prod:
            # Llenamos el formulario con los datos actuales para que el usuario los vea
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
        # Obtenemos la referencia al producto original
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