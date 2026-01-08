import os

def load_stylesheet(filename):
    """
    Carga un archivo de hoja de estilo (.qss) desde la carpeta assets/styles.
    
    Args:
        filename (str): Nombre del archivo (ej: 'sidebar.qss')
        
    Returns:
        str: El contenido del archivo CSS o una cadena vacía si hay error.
    """
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(current_dir))
        
        style_path = os.path.join(project_root, "assets", "styles", filename)
        
        if os.path.exists(style_path):
            with open(style_path, "r", encoding="utf-8") as f:
                return f.read()
        else:
            print(f"Advertencia: No se encontró el archivo de estilo: {style_path}")
            return ""
    except Exception as e:
        print(f"Error al cargar estilo {filename}: {str(e)}")
        return ""
