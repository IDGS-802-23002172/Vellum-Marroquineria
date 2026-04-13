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
from trazabilidad.routes import trazabilidad_bp


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
app.register_blueprint(trazabilidad_bp)

with app.app_context():
    intentos = 0
    while intentos < 2:
        try:
            db.create_all()
            print("Tablas creadas con éxito.")
            crear_vista_cierre_diario()
            print("Vista de cierre diario operativa.")
            break
        except Exception as e:
            intentos += 1
            print(f"Esperando a MySQL (Intento {intentos}/2)...")
            time.sleep(5)


@app.before_request
def verificar_sesion():
    # Rutas que no requieren sesión activa.
    # 'tiendaCliente.*' permite que el blueprint de tienda maneje su propia auth.
    rutas_publicas = {
        'login',
        'logout',
        'static',
        'tiendaCliente.index',   # ajusta según los endpoints de tu blueprint
        'tiendaCliente.login',
    }

    if request.endpoint in rutas_publicas:
        return  # dejar pasar sin verificar

    if 'user_id' not in session:
        return redirect(url_for('login'))


@app.route('/')
def index():
    print("Sesion:", dict(session), flush=True)
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    # Si ya hay sesión activa, redirigir al destino correcto
    if 'user_id' in session:
        if session.get('user_role') == 'Cliente':
            return redirect(url_for('tiendaCliente.index'))
        return redirect(url_for('index'))

    form = UserForm()

    # login_mode: 'client' (tienda) o 'staff' (gestión interna).
    # Se usa sólo para restaurar el toggle visual cuando hay errores de validación.
    login_mode = request.form.get('login_mode', 'client')

    if form.validate_on_submit():
        user = Usuario.query.filter_by(username=form.username.data).first()

        if not user:
            flash("El usuario no existe.", "danger")
            return render_template('login.html', form=form, login_mode=login_mode)

        if user.esta_bloqueado or user.intentos_fallidos >= 3:
            flash("Cuenta bloqueada por seguridad. Contacte al administrador.", "danger")
            return render_template('login.html', form=form, login_mode=login_mode)

        if check_password_hash(user.password, form.password.data):
            # Credenciales correctas: limpiar intentos y crear sesión
            user.intentos_fallidos = 0
            db.session.commit()

            session['user_id']   = user.id
            session['user_role'] = user.rol.nombre
            session.permanent    = True

            if session['user_role'] == 'Cliente':
                return redirect(url_for('tiendaCliente.index'))
            return redirect(url_for('index'))

        else:
            # Contraseña incorrecta
            user.intentos_fallidos += 1
            if user.intentos_fallidos >= 3:
                user.esta_bloqueado = True
            db.session.commit()

            restantes = max(0, 3 - user.intentos_fallidos)
            if restantes:
                flash(
                    f"Contraseña incorrecta. Te queda{'n' if restantes > 1 else ''} "
                    f"{restantes} intento{'s' if restantes > 1 else ''}.",
                    "warning"
                )
            else:
                flash("Cuenta bloqueada por seguridad. Contacte al administrador.", "danger")

    # GET o form inválido (CSRF, campos vacíos)
    return render_template('login.html', form=form, login_mode=login_mode)


@app.route('/logout')
def logout():
    session.clear()
    flash("Has cerrado sesión correctamente.", "info")
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)