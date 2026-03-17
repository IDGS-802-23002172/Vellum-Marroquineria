# VELLUM — Gestión Integral de Marroquinería

**Vellum** es un sistema de gestión empresarial (ERP) diseñado específicamente para la industria del cuero en León, Guanajuato. Integra la cadena de suministro, la ingeniería de producto (explosión de materiales) y el punto de venta final, bajo un esquema de seguridad industrial basado en estándares OWASP.

---

## Inicio Rápido con Docker

Pasos para inicializar el proyecto

### 1. Requisitos Previos
* **Docker Desktop** instalado.
* Archivo `.env` configurado en la raíz con las credenciales de la base de datos.

### 2. Despliegue del Sistema
Ejecuta los siguientes comandos en tu terminal para levantar la infraestructura (Contenedor de App Flask + Contenedor de MySQL):

```powershell
# Detener y limpiar volúmenes anteriores (opcional para reinicio limpio)
docker-compose down -v

# Construir y levantar contenedores en segundo plano
docker-compose up --build -d

# En ocasiones puede ser necesario reiniciar el volumen vellum app para que se generen las tablas
docker restart vellum_app

# Consejo extra con docker, a veces no creara las tablas porque hay que limpiar el cache
docker system prune -f



```

### 3. Sembrado de Datos
Una vez que los contenedores estén activos, ejecuta el script de automatización para generar los roles y usuarios iniciales con contraseñas hasheadas:

```powershell
docker exec -it vellum_app python seed_db.py
```

---

##  Credenciales de Acceso Iniciales
Los siguientes usuarios están pre-registrados en el sistema con permisos:

| Usuario | Contraseña | Rol / Departamento |
| :--- | :--- | :--- |
| **`admin_majo`** | `vellum_admin_2026` | Administrador / DBA |
| **`user_emilio`** | `emilio_ventas_123` | Operador / Ventas |
| **`maint_diego`** | `diego_mantenimientp_456` | Consulta / Mantenimiento / Respaldos |
| **`maint_ange`** | `angel_mantenimiento_123` | Consulta / Mantenimiento / Respaldos |

---

## Medidas de Seguridad Implementadas
* **Hashing de Credenciales:** Implementación de `PBKDF2` con salt aleatorio vía `Werkzeug` para proteger la identidad de los artesanos.
* **Gestión de Sesiones:** Control manual de sesiones con expiración automática tras 10 minutos de inactividad.
* **Protección CSRF:** Blindaje de todos los formularios contra ataques de falsificación de petición en sitios cruzados.
* **Prevención de Inyección SQL:** Uso estricto de **SQLAlchemy ORM** para la parametrización de consultas a la base de datos.
* **Bloqueo de Cuentas:** Sistema automático de bloqueo tras 3 intentos fallidos de inicio de sesión.

---

## Estructura del Proyecto
El sistema utiliza una arquitectura de **Blueprints** para mantener la escalabilidad del código:

* `/proveedores`: Gestión de proveedores y estados de la república.
* `/materiales`: Inventario de materias primas y unidades de medida (dm², ml, pza).
* `/productos`: Catálogo de producto terminado (Executive, Lifestyle, Essentials).
* `/recetas`: Ingeniería de producto y cálculo de merma técnica de piel.
* `/ventas`: Módulo transaccional de punto de venta (POS).

---

## Desarrollado por
* **María José Ramírez Ramírez** — *Lider de proyecto, Integración, Seguridad y DBA*
* **Angel de Jesus Santoyo Muño** — *Encargado de Transformacion y Produccion*
* **Diego Jair Borja Romero** — *Encargado de Suministros y Logística*
* **Emilio Navarro Frausto** — *Encargado de Ventas y Analisis de datos*

* **Equipo Vellum**
