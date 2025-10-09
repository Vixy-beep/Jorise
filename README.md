# Jorise - Sistema de Análisis de Archivos Sospechosos

Sistema completo de ciberseguridad desarrollado con Django para análisis y detección de amenazas en archivos.

## Versiones Disponibles

### Versión 1.0 - Básica (4 módulos)
- Core: Gestión de archivos
- Scan: Motor de escaneo  
- Reports: Generación de reportes
- Frontend: Interfaz de usuario

### Versión 2.0 - Suite Completa (5 módulos)
- SIEM: Security Information and Event Management
- EDR: Endpoint Detection and Response
- SANDBOX: Análisis en entorno aislado
- WAF: Web Application Firewall
- ANTIVIRUS: Motor antivirus integrado

## Tecnologías

- Python 3.11+
- Django 5.0+
- Bootstrap 5
- Chart.js
- SQLite/PostgreSQL

## Instalación

```bash
# Clonar repositorio
git clone https://github.com/Vixy-beep/Jorise.git
cd Jorise

# Crear entorno virtual
python -m venv .venv
source .venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Configurar base de datos
python manage.py migrate

# Crear superusuario
python manage.py createsuperuser

# Ejecutar servidor
python manage.py runserver
```

## Uso

Acceder a http://localhost:8000 para la suite completa o http://localhost:8001 para la versión básica.

## Licencia

Proyecto desarrollado para análisis de ciberseguridad.