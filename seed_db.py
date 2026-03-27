# seed_db.py
from app import app
from models import db, Usuario, Rol, EstadoMexico
from werkzeug.security import generate_password_hash

# aclaracion, este es un script para generar usuarios con contraseñas hasheadas
# para ejecutarlo, tumben el docker, vuelvanlo a arrancar y peguen el comando que les dejare
# lista de comandos

# ejecutar este script
# docker exec -it vellum_app python seed_db.py

def seed():
    with app.app_context():
        print("--- Sembrando Roles y Usuarios de Vellum ---")

        # 1. Sembrar Roles primero
        roles_necesarios = ['Admin', 'Artesano', 'Cliente']
        for nombre_rol in roles_necesarios:
            if not Rol.query.filter_by(nombre=nombre_rol).first():
                nuevo_rol = Rol(nombre=nombre_rol, descripcion=f'Acceso para {nombre_rol}')
                db.session.add(nuevo_rol)
        db.session.commit()
        print("Roles verificados/creados.")
        
        usuarios_iniciales = [
            {"user": "admin_majo", "pass": "vellum_admin_2026", "rol": "Admin"},
            {"user": "maint_ange", "pass": "angel_mantenimiento_123", "rol": "Admin"}, 
            {"user": "user_emilio", "pass": "emilio_ventas_123", "rol": "Admin"},
            {"user": "maint_diego", "pass": "diego_mantenimiento_456", "rol": "Admin"},
            {"user": "cliente_test", "pass": "Vellum2026*", "rol": "Cliente"},
            {"user": "angel_cliente", "pass": "cliente123", "rol": "Cliente"},
            {"user": "majo_cliente", "pass": "cliente456", "rol": "Cliente"}
        ]

        for u in usuarios_iniciales:
            existente = Usuario.query.filter_by(username=u['user']).first()
            if not existente:
                hash_pw = generate_password_hash(u['pass'])
                rol_db = Rol.query.filter_by(nombre=u['rol']).first()
                
                nuevo_usuario = Usuario(
                    username=u['user'],
                    password=hash_pw,
                    intentos_fallidos=0,
                    esta_bloqueado=False,
                    id_rol=rol_db.id 
                )
                db.session.add(nuevo_usuario)
                print(f"Usuario '{u['user']}' creado con rol {u['rol']}.")
            else:
                print(f"El usuario '{u['user']}' ya existe.")

        db.session.commit()
        print("--- Sembrando Estados de México ---")
        estados_mexico = [
            "Aguascalientes", "Baja California", "Baja California Sur", "Campeche",
            "Chiapas", "Chihuahua", "Ciudad de México", "Coahuila", "Colima",
            "Durango", "Estado de México", "Guanajuato", "Guerrero", "Hidalgo",
            "Jalisco", "Michoacán", "Morelos", "Nayarit", "Nuevo León", "Oaxaca",
            "Puebla", "Querétaro", "Quintana Roo", "San Luis Potosí", "Sinaloa",
            "Sonora", "Tabasco", "Tamaulipas", "Tlaxcala", "Veracruz",
            "Yucatán", "Zacatecas"
        ]

        for estado in estados_mexico:
            existe = EstadoMexico.query.filter_by(nombre=estado).first()
            if not existe:
                nuevo_estado = EstadoMexico(nombre=estado)
                db.session.add(nuevo_estado)

        db.session.commit()
        print("Estados de México verificados/creados.")
        print("--- Proceso terminado ---")

if __name__ == '__main__':
    seed()