import os
from app import app
from models import db, crear_vista_cierre_diario
from sqlalchemy import text

def restauracion_bd():
    with app.app_context():
        db.drop_all()
        db.create_all()
        
        try:
            crear_vista_cierre_diario()
        except Exception as e:
            pass
            
        try:
            db.session.execute(text("SET FOREIGN_KEY_CHECKS=0;"))
            
            with open("Dump20260408.sql", "r", encoding="utf-8") as archivo:
                for linea in archivo:
                    linea = linea.strip()
                    if linea.startswith("INSERT INTO"):
                        db.session.execute(text(linea))
            
            db.session.execute(text("SET FOREIGN_KEY_CHECKS=1;"))
            db.session.commit()
            print("Restauración completada con éxito.")
        
        except FileNotFoundError:
            print("error: No tienes el archivo de respaldo o lo tienes nombrado distinto, checa eso.")
            
        except Exception as e:
            db.session.rollback()
            print(f"error al restaurar la base de datos: {str(e)}, checa eso")           

if __name__ == "__main__":
    restauracion_bd()