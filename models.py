from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username  = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(50), nullable=False)
    intentos_fallidos=  db.Column(db.Integer, default=0)
    ultimo_acceso = db.Column(db.DateTime)
    esta_bloqueado = db.Column(db.Boolean, default=False)