import json
import os
import re
import shutil  # ← AGREGAR ESTE IMPORT
from typing import Dict, Any
from datetime import datetime  # ← AGREGAR ESTE IMPORT

class PresetsManager:
    """Gestor de presets organizados por categorías"""
    
    def __init__(self):
        current_dir = os.path.dirname(os.path.dirname(__file__))
        self.presets_dir = os.path.join(current_dir, "data", "presets")
        self.ensure_base_directory()  # ← Cambiar nombre del método
    
    def ensure_base_directory(self):
        """Asegura que existe el directorio base de presets"""
        # Solo crear el directorio base, no las subcarpetas
        os.makedirs(self.presets_dir, exist_ok=True)
    
    def create_example_preset(self, category, file_path):
        """Crea un preset de ejemplo para cada categoría"""
        examples = {
            "vestuarios": {
                "presets": {
                    "uniforme_escolar": {
                        "name": "Uniforme Escolar",
                        "description": "Uniforme escolar clásico",
                        "categories": {
                            "Vestuario general": "school uniform",
                            "Vestuario superior": "white shirt, blazer",
                            "Vestuario inferior": "pleated skirt"
                        }
                    }
                }
            },
            "expresiones": {
                "presets": {
                    "sonrisa_dulce": {
                        "name": "Sonrisa Dulce",
                        "description": "Expresión tierna y amigable",
                        "categories": {
                            "Expresión": "sweet smile, gentle expression",
                            "Ojos": "bright eyes, sparkling"
                        }
                    }
                }
            }
            # ... más ejemplos para otras categorías
        }
        
        example_data = examples.get(category, {"presets": {}})
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(example_data, f, indent=2, ensure_ascii=False)
    
    def get_presets_by_category(self, category_id: str) -> Dict[str, Any]:
        """Obtiene todos los presets de una categoría"""
        category_dir = os.path.join(self.presets_dir, category_id)
        all_presets = {}
        
        if os.path.exists(category_dir):
            for file_name in os.listdir(category_dir):
                if file_name.endswith('.json'):
                    file_path = os.path.join(category_dir, file_name)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            presets = data.get('presets', {})
                            all_presets.update(presets)
                    except Exception as e:
                        print(f"Error cargando {file_path}: {e}")
        
        return all_presets
    
    def save_preset(self, preset_type, preset_name, preset_data):
        """Guarda un preset con las categorías seleccionadas y las imágenes"""
        # Crear directorio si no existe
        category_dir = os.path.join(self.presets_dir, preset_type)
        os.makedirs(category_dir, exist_ok=True)
        
        # Generar nombre de archivo seguro
        safe_filename = re.sub(r'[^\w\s-]', '', preset_name).strip()
        safe_filename = re.sub(r'[-\s]+', '_', safe_filename).lower()
        
        # Sincronizar carpeta de imágenes con la selección actual
        images_data = []
        images_dir = os.path.join(category_dir, f"{safe_filename}_images")
        selected_images = preset_data.get('images') or []

        if selected_images:
            os.makedirs(images_dir, exist_ok=True)

            desired_names = []
            for i, image_path in enumerate(selected_images):
                if not os.path.exists(image_path):
                    continue
                file_extension = os.path.splitext(image_path)[1]
                new_image_name = f"image_{i+1}{file_extension}"
                new_image_path = os.path.join(images_dir, new_image_name)

                # Evitar SameFileError cuando el origen y el destino son iguales
                try:
                    if os.path.abspath(image_path) != os.path.abspath(new_image_path):
                        shutil.copy2(image_path, new_image_path)
                    # Si son iguales, no copiamos; ya está en el lugar correcto
                except shutil.SameFileError:
                    # Ya es el mismo archivo; no hacer nada
                    pass

                desired_names.append(new_image_name)
                images_data.append(new_image_name)

            # Eliminar archivos sobrantes que no están en la nueva selección
            if os.path.isdir(images_dir):
                for fname in os.listdir(images_dir):
                    if fname not in set(desired_names):
                        try:
                            os.remove(os.path.join(images_dir, fname))
                        except Exception:
                            pass
        else:
            # No hay imágenes seleccionadas: borrar la carpeta de imágenes si existe
            if os.path.isdir(images_dir):
                shutil.rmtree(images_dir, ignore_errors=True)
        
        # Crear estructura del preset
        preset_structure = {
            "presets": {
                safe_filename: {
                    "name": preset_name,
                    "categories": preset_data['categories'],
                    "images": images_data,
                    "created_at": preset_data.get('created_at', datetime.now().isoformat())
                }
            }
        }
        
        # Guardar archivo JSON
        file_path = os.path.join(category_dir, f"{safe_filename}.json")
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(preset_structure, f, indent=2, ensure_ascii=False)
        
        return True
    
    def get_all_preset_folders(self):
        """Obtiene todas las carpetas de presets (solo personalizadas)"""
        # Solo buscar carpetas personalizadas que realmente existen
        custom_folders = {}
        if os.path.exists(self.presets_dir):
            for item in os.listdir(self.presets_dir):
                item_path = os.path.join(self.presets_dir, item)
                if os.path.isdir(item_path):
                    # Todas las carpetas son personalizadas ahora
                    display_name = item.replace('_', ' ').title()
                    custom_folders[item] = {
                        "display_name": f"📂 {display_name}",
                        "is_custom": True
                    }
    
        return custom_folders
    
    def create_custom_folder(self, folder_name):
        """Crea una nueva carpeta personalizada de presets"""
        try:
            # Convertir nombre a formato de carpeta (sin espacios, minúsculas)
            folder_id = self.sanitize_folder_name(folder_name)
            folder_path = os.path.join(self.presets_dir, folder_id)
            
            # Verificar que no exista
            if os.path.exists(folder_path):
                return False
            
            # Crear la carpeta
            os.makedirs(folder_path, exist_ok=True)
            
            # NO crear archivo de información automáticamente
            # Solo crear la carpeta vacía
            
            return True
            
        except Exception as e:
            print(f"Error creando carpeta personalizada: {e}")
            return False
    
    def sanitize_folder_name(self, name):
        """Convierte un nombre de carpeta a formato válido para sistema de archivos"""
        # Convertir a minúsculas y reemplazar espacios con guiones bajos
        sanitized = name.lower().strip()
        sanitized = re.sub(r'[^a-z0-9\s\-_]', '', sanitized)  # Solo letras, números, espacios, guiones
        sanitized = re.sub(r'\s+', '_', sanitized)  # Espacios a guiones bajos
        sanitized = re.sub(r'_+', '_', sanitized)  # Múltiples guiones bajos a uno solo
        return sanitized.strip('_')  # Quitar guiones bajos al inicio/final
    
    def load_preset(self, preset_type, preset_name):
        """Carga un preset específico"""
        # Generar nombre de archivo seguro
        safe_filename = re.sub(r'[^\w\s-]', '', preset_name).strip()
        safe_filename = re.sub(r'[-\s]+', '_', safe_filename).lower()
        
        file_path = os.path.join(self.presets_dir, preset_type, f"{safe_filename}.json")
        
        if not os.path.exists(file_path):
            return None
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            preset_data = data.get('presets', {}).get(safe_filename, {})
            
            # Cargar rutas completas de imágenes
            if preset_data.get('images'):
                images_dir = os.path.join(self.presets_dir, preset_type, f"{safe_filename}_images")
                full_image_paths = []
                for image_name in preset_data['images']:
                    full_path = os.path.join(images_dir, image_name)
                    if os.path.exists(full_path):
                        full_image_paths.append(full_path)
                preset_data['images'] = full_image_paths
                
            return preset_data
            
        except Exception as e:
            print(f"Error al cargar preset: {e}")
            return None

    def delete_preset(self, preset_type: str, preset_name: str) -> bool:
        """Elimina el archivo JSON del preset y su carpeta de imágenes asociada.

        Args:
            preset_type: Carpeta/categoría del preset.
            preset_name: Nombre visible del preset.

        Returns:
            True si se eliminó alguna pieza relevante; False si no existía nada que eliminar.
        """
        try:
            # Nombre de archivo seguro
            safe_filename = re.sub(r'[^\w\s-]', '', preset_name).strip()
            safe_filename = re.sub(r'[-\s]+', '_', safe_filename).lower()

            category_dir = os.path.join(self.presets_dir, preset_type)
            json_path = os.path.join(category_dir, f"{safe_filename}.json")
            images_dir = os.path.join(category_dir, f"{safe_filename}_images")

            removed_any = False

            if os.path.exists(json_path):
                os.remove(json_path)
                removed_any = True

            if os.path.isdir(images_dir):
                shutil.rmtree(images_dir, ignore_errors=True)
                removed_any = True

            return removed_any
        except Exception as e:
            print(f"Error eliminando preset '{preset_name}' en '{preset_type}': {e}")
            return False

    def delete_folder(self, folder_id: str) -> bool:
        """Elimina por completo una carpeta de presets (incluye JSON e imágenes).

        Args:
            folder_id: Identificador de la carpeta (nombre de directorio).

        Returns:
            True si la carpeta existía y fue eliminada; False en caso contrario o error.
        """
        try:
            folder_path = os.path.join(self.presets_dir, folder_id)
            if os.path.isdir(folder_path):
                shutil.rmtree(folder_path, ignore_errors=True)
                return True
            return False
        except Exception as e:
            print(f"Error eliminando carpeta de presets '{folder_id}': {e}")
            return False

    def rename_folder(self, old_folder_id: str, new_display_name: str) -> tuple[bool, str]:
        """Renombra una carpeta de presets moviendo el directorio.

        Args:
            old_folder_id: Nombre actual del directorio.
            new_display_name: Nuevo nombre visible; se sanitiza a id de carpeta.

        Returns:
            (success, new_folder_id) donde new_folder_id es el id sanitizado si success.
        """
        try:
            new_folder_id = self.sanitize_folder_name(new_display_name)
            if not new_folder_id:
                return (False, "")

            old_path = os.path.join(self.presets_dir, old_folder_id)
            new_path = os.path.join(self.presets_dir, new_folder_id)

            if not os.path.isdir(old_path):
                return (False, "")
            if os.path.exists(new_path):
                # Ya existe una carpeta con ese nombre
                return (False, "")

            os.rename(old_path, new_path)
            return (True, new_folder_id)
        except Exception as e:
            print(f"Error renombrando carpeta '{old_folder_id}' a '{new_display_name}': {e}")
            return (False, "")