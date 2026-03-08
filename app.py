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
from ventas import ventas_bp
from productos.routes import productos_bp

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


app.register_blueprint(ventas_bp, url_prefix="/ventas")

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


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)