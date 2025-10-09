# 🛡️ JORISE V1 BÁSICA - INSTRUCCIONES PARA DEMO ONDA

## 📋 **Resumen del Sistema**
Jorise v1 es la **versión básica** del sistema de análisis de archivos sospechosos, diseñada específicamente como **demostración para ONDA**. Incluye las funcionalidades esenciales de ciberseguridad en un paquete ligero y fácil de presentar.

---

## 🚀 **INSTRUCCIONES DE EJECUCIÓN (Para Capturas)**

### **1. Prerrequisitos**
```bash
# Python 3.11 o superior instalado
python3 --version

# Entorno virtual configurado
source /home/rub1r0za/VScode/Jorise/.venv/bin/activate
```

### **2. Navegar al Directorio de v1**
```bash
cd /home/rub1r0za/VScode/Jorise/Jorise/jorise_v1
```

### **3. Instalar Dependencias (Si es necesario)**
```bash
pip install -r requirements.txt
```

### **4. Aplicar Migraciones**
```bash
python manage.py migrate
```

### **5. INICIAR EL SERVIDOR (LISTO PARA CAPTURAS)**
```bash
python manage.py runserver 0.0.0.0:8001
```

---

## 🌐 **ACCESO AL SISTEMA**

**URL Principal:** `http://localhost:8001/`

### **Páginas Disponibles para Capturas:**

1. **📊 Dashboard Principal**
   - URL: `http://localhost:8001/`
   - Muestra estadísticas generales y estado de módulos

2. **📤 Subir Archivos**
   - URL: `http://localhost:8001/upload/`
   - Interfaz para carga de archivos a analizar

3. **🔍 Análisis de Archivos**
   - URL: `http://localhost:8001/scan/`
   - Resultados simulados de escaneo con múltiples motores

4. **📋 Reportes y Estadísticas**
   - URL: `http://localhost:8001/reports/`
   - Vista de reportes históricos y exportación

---

## 🎯 **FUNCIONALIDADES DEMOSTRADAS (v1 Básica)**

### **✅ Módulos Incluidos:**
- **Core:** Gestión central y configuración
- **Scan:** Motor de escaneo de archivos
- **Reports:** Generación de informes
- **Frontend:** Interfaz de usuario intuitiva

### **🔧 Características Técnicas:**
- Framework: Django 5.2
- Base de datos: SQLite (ligera)
- UI: Bootstrap 5 + Font Awesome
- Responsive: Compatible con móviles y tablets

### **🎨 Elementos Visuales para Capturas:**
- Dashboard con métricas en tiempo real
- Cards de estadísticas coloridas
- Tablas de resultados profesionales
- Formularios de carga intuitivos
- Indicadores de estado en tiempo real

---

## 📸 **GUÍA PARA CAPTURAS ONDA**

### **Secuencia Recomendada:**
1. **Captura 1:** Dashboard principal mostrando métricas
2. **Captura 2:** Formulario de carga de archivos
3. **Captura 3:** Página de análisis con resultados
4. **Captura 4:** Vista de reportes y estadísticas
5. **Captura 5:** Navegación y sidebar del sistema

### **Puntos Destacables:**
- ✅ Interfaz profesional y limpia
- ✅ Funcionalidades específicas de ciberseguridad
- ✅ Integración simulada con VirusTotal
- ✅ Reportes exportables
- ✅ Sistema escalable para v2 completa

---

## 🔧 **Comandos Útiles**

```bash
# Detener servidor (Ctrl+C en terminal)

# Verificar estado
http://localhost:8001/

# Logs en tiempo real (si hay errores)
tail -f logs/jorise_v1.log

# Acceso directo a admin (si necesitas)
python manage.py createsuperuser
http://localhost:8001/admin/
```

---

## 📊 **Diferencias v1 vs v2**

| Característica | v1 Básica | v2 Completa |
|---------------|-----------|-------------|
| **Módulos** | 4 básicos | 10+ avanzados |
| **Propósito** | Demo ONDA | Producción |
| **Tamaño** | <50 MB | >200 MB |
| **Puerto** | 8001 | 8000 |

---

## ⚡ **Estado Actual**
🟢 **SERVIDOR ACTIVO EN:** `http://localhost:8001/`
🟢 **LISTO PARA CAPTURAS DE PANTALLA**
🟢 **TODAS LAS PÁGINAS FUNCIONALES**

**¡El sistema está listo para la presentación a ONDA!** 🎯