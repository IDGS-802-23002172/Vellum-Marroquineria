import os
from flask import Flask, render_template
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv

from app.models import db, Usuario

load_dotenv()

app = Flask(__name__, template_folder='app/templates', static_folder='app/static')

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
    'DATABASE_URL', 
    'mysql+pymysql://vellum_user:vellum_password_123@db/vellum_db'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'clave_segura_vellum_123')

db.init_app(app)
csrf = CSRFProtect(app)

with app.app_context():
    try:
        db.create_all()
        print("tablas creadas con exito")
    except Exception as e:
        print(f"error al conectar con la bd {e}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login():
    return render_template('login.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)