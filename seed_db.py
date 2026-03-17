# seed_db.py
from app import app
from models import db, Usuario
from werkzeug.security import generate_password_hash

# aclaracion, este es un script para generar usuarios con contraseñas hasheadas
# para ejecutarlo, tumben el docker, vuelvanlo a arrancar y peguen el comando que les dejare
# lista de comandos


# ejecutar este script
# docker exec -it vellum_app python seed_db.py

def seed():
    with app.app_context():
        #no vayan a ejecutar esto, solo lo dejo por si acaso (es para limpiar por si acaso)
        # db.drop_all() 
        # db.create_all()

        print("--- Sembrando Usuarios de Vellum ---")

        usuarios_iniciales = [
            {"user": "admin_majo", "pass": "vellum_admin_2026"},
            {"user": "maint_ange", "pass": "angel_mantenimiento_123"},
            {"user": "user_emilio", "pass": "emilio_ventas_123"},
            {"user": "maint_diego", "pass": "diego_mantenimiento_456"}
        ]

        for u in usuarios_iniciales:
            existente = Usuario.query.filter_by(username=u['user']).first()
            if not existente:
                hash_pw = generate_password_hash(u['pass'])
                
                nuevo_usuario = Usuario(
                    username=u['user'],
                    password=hash_pw,
                    intentos_fallidos=0,
                    esta_bloqueado=False
                )
                db.session.add(nuevo_usuario)
                print(f"Usuario '{u['user']}' creado.")
            else:
                print(f"El usuario '{u['user']}' ya existe.")

        db.session.commit()
        print("--- Proceso terminado ---")

if __name__ == '__main__':
    seed()