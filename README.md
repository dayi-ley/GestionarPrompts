# Gestor de Prompts para imagenes

Generador/organizador de prompts, diseñado específicamente para la generación de imágenes.

## Características Principales

### Interfaz de Usuario
- **Layout de tres secciones**: Sidebar izquierda, grid de categorías superior, y sección de prompt inferior
![Vista principal de la aplicación](assets/screenshots/main_window.png)


- **Grid responsivo** con scroll vertical para las categorías
![Vista seccion de grid de categorias](assets/screenshots/category_grid.png)
- **40+ categorías organizadas** en tarjetas individuales
- **Tags visuales** para valores comunes en cada categoría

### Generación de Prompts
- **Combinación automática** de todas las categorías activas
- **Eliminación de duplicados** automática
- **Orden lógico** de términos (Calidad → Estilo → Sujeto → cabello → vestuarios → poses → complementos)
- **Validación de inputs** y limpieza automática

### Gestión de Datos
- **Persistencia local** de configuraciones y datos
- **Historial de prompts** con límite configurable
- **Exportación** en formatos JSON y TXT
- **Gestión de personajes y escenas** con descripciones


## Requisitos del Sistema

### Software
- Python 3.8 o superior
- PyQt6==6.9.1
- Pillow (PIL)
- pyperclip


## 📦 Instalación

1. **Clonar el repositorio**:

git clone <repository-url>
cd AppPrompts

2. **Crear entorno virtual**:

python -m venv appPrompt

3. **Activar el entorno virtual**:

appPrompt\Scripts\activate

4. **Instalar dependencias**:

pip install PyQt6 pillow pyperclip

5. **Ejecutar la aplicación**:

python main.py


## Uso de la Aplicación

### Interfaz Principal
1. **Sidebar izquierda**: Selecciona personajes y escenas predefinidas
2. **Grid de categorías**: Completa los campos para generar tu prompt
3. **Sección de prompt**: Visualiza el resultado en tiempo real

### Generando Prompts
1. **Selecciona categorías**: Haz clic en los inputs de las categorías que desees usar
2. **Escribe valores**: Ingresa términos específicos o usa los tags sugeridos
3. **Observa en tiempo real**: El prompt se actualiza automáticamente
4. **Ajusta el negative prompt**: Expande la sección para personalizar

## 📁 Estructura del Proyecto

```
AppPrompts/
│---appPrompt               # carpeta del entorno virtual del proyecto
│   └── activate.bat        # Activación del entorno virtual
├── main.py                 # Punto de entrada de la aplicación
├── ui/                     # Componentes de interfaz
│   ├── main_window.py      # Ventana principal
│   ├── sidebar.py          # Panel lateral
│   ├── category_grid.py    # Grid de categorías
│   ├── prompt_section.py   # Sección de prompt
│   └── ui_elements.py      # Elementos UI personalizados
├── logic/                 
│   └── prompt_generator.py # Generador de prompts
├── config/                 # Configuración
│   └── settings.py         # Gestión de datos y configuraciones(Implementacion con otro sistema(TODO))
├── data/                   # Datos persistentes 
│   ├── settings.json       # Configuraciones de la app
│   ├── characters          # Personajes guardados
│   ├── categories.json     # Escenas guardadas
│   └── tags.json           # Historial de prompts
└── assets/                 # Recursos (iconos, imágenes)
```

## Reportar Problemas

Si encuentras algún problema o tienes una sugerencia, por favor:

1. Revisa los issues existentes
2. Crea un nuevo issue con:
   - Descripción detallada del problema
   - Pasos para reproducir
   - Información del sistema
   - Capturas de pantalla (si aplica)


---

