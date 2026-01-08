import json
import os
import re
import shutil
from typing import Dict, Any
from datetime import datetime
from PIL import Image

class PresetsManager:
    """Gestor de presets organizados por categorías"""
    
    def __init__(self):
        current_dir = os.path.dirname(os.path.dirname(__file__))
        self.presets_dir = os.path.join(current_dir, "data", "presets")
        self.ensure_base_directory() 
    
    def ensure_base_directory(self):
        """Asegura que existe el directorio base de presets"""
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
    
    def _optimize_image(self, source_path, dest_path, max_size=(512, 512), quality=85):
        """Optimiza una imagen: redimensiona y comprime"""
        try:
            with Image.open(source_path) as img:
                # Corregir orientación EXIF si existe
                try:
                    from PIL import ExifTags, ImageOps
                    img = ImageOps.exif_transpose(img)
                except Exception:
                    pass

                # Calcular nuevo tamaño manteniendo ratio
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
                
                file_ext = os.path.splitext(dest_path)[1].lower()
                
                if file_ext in ['.jpg', '.jpeg']:
                    # Convertir a RGB si es necesario
                    if img.mode in ('RGBA', 'LA', 'P'):
                        img = img.convert('RGB')
                    img.save(dest_path, 'JPEG', quality=quality, optimize=True)
                    
                elif file_ext == '.png':
                    # Para PNG, intentar optimizar
                    # Si no tiene transparencia, convertir a JPG podría ser mejor, pero mantendremos formato
                    img.save(dest_path, 'PNG', optimize=True)
                    
                elif file_ext == '.webp':
                    img.save(dest_path, 'WEBP', quality=quality)
                    
                else:
                    img.save(dest_path)
                    
        except Exception as e:
            print(f"Error optimizando imagen {source_path}: {e}")
            # Fallback: copia simple si falla la optimización
            try:
                shutil.copy2(source_path, dest_path)
            except shutil.SameFileError:
                pass

    def save_preset(self, preset_type, preset_name, preset_data):
        """Guarda un preset con las categorías seleccionadas y las imágenes"""
        category_dir = os.path.join(self.presets_dir, preset_type)
        os.makedirs(category_dir, exist_ok=True)
        
        # Sanitizar nombre de archivo
        safe_filename = re.sub(r'[^\w\s-]', '', preset_name).strip()
        safe_filename = re.sub(r'[-\s]+', '_', safe_filename).lower()
        
        # Gestionar imágenes
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

                # Optimizar imagen al guardar
                if os.path.abspath(image_path) != os.path.abspath(new_image_path):
                    self._optimize_image(image_path, new_image_path)
                else:
                    # Si es el mismo archivo (re-guardado), podríamos intentar re-optimizar 
                    # si es muy grande, pero por ahora asumimos que ya está bien o se optimizará con el script global
                    pass

                desired_names.append(new_image_name)
                images_data.append(new_image_name)

            # Limpiar imágenes obsoletas
            if os.path.isdir(images_dir):
                for fname in os.listdir(images_dir):
                    if fname not in set(desired_names):
                        try:
                            os.remove(os.path.join(images_dir, fname))
                        except Exception:
                            pass
        else:
            if os.path.isdir(images_dir):
                shutil.rmtree(images_dir, ignore_errors=True)
        
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
        
        file_path = os.path.join(category_dir, f"{safe_filename}.json")
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(preset_structure, f, indent=2, ensure_ascii=False)
        
        return True

    def optimize_all_existing_images(self):
        """Recorre todos los presets y optimiza sus imágenes existentes"""
        count = 0
        total_saved_bytes = 0
        
        if not os.path.exists(self.presets_dir):
            return 0, 0
            
        # Recorrer categorías
        for category in os.listdir(self.presets_dir):
            category_path = os.path.join(self.presets_dir, category)
            if not os.path.isdir(category_path):
                continue
                
            # Buscar carpetas de imágenes
            for item in os.listdir(category_path):
                if item.endswith('_images') and os.path.isdir(os.path.join(category_path, item)):
                    images_dir = os.path.join(category_path, item)
                    
                    for img_file in os.listdir(images_dir):
                        if img_file.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                            img_path = os.path.join(images_dir, img_file)
                            
                            try:
                                initial_size = os.path.getsize(img_path)
                                # Si la imagen es pequeña (< 200KB), saltar
                                if initial_size < 200 * 1024:
                                    continue
                                    
                                # Optimizar sobreescribiendo
                                # Usamos un archivo temporal para evitar corrupción
                                temp_path = img_path + ".tmp"
                                self._optimize_image(img_path, temp_path)
                                
                                if os.path.exists(temp_path):
                                    final_size = os.path.getsize(temp_path)
                                    if final_size < initial_size:
                                        os.replace(temp_path, img_path)
                                        saved = initial_size - final_size
                                        total_saved_bytes += saved
                                        count += 1
                                        print(f"Optimizado: {img_file} ({initial_size/1024:.1f}KB -> {final_size/1024:.1f}KB)")
                                    else:
                                        os.remove(temp_path)
                            except Exception as e:
                                print(f"Error procesando {img_file}: {e}")
                                
        return count, total_saved_bytes
    
    def get_all_preset_folders(self):
        """Obtiene todas las carpetas de presets (solo personalizadas)"""
        custom_folders = {}
        if os.path.exists(self.presets_dir):
            for item in os.listdir(self.presets_dir):
                item_path = os.path.join(self.presets_dir, item)
                if os.path.isdir(item_path):
                    display_name = item.replace('_', ' ').title()
                    custom_folders[item] = {
                        "display_name": f"📂 {display_name}",
                        "is_custom": True
                    }
    
        return custom_folders
    
    def create_custom_folder(self, folder_name):
        """Crea una nueva carpeta personalizada de presets"""
        try:
            folder_id = self.sanitize_folder_name(folder_name)
            folder_path = os.path.join(self.presets_dir, folder_id)
            
            if os.path.exists(folder_path):
                return False
            
            os.makedirs(folder_path, exist_ok=True)
            return True
            
        except Exception as e:
            print(f"Error creando carpeta personalizada: {e}")
            return False
    
    def sanitize_folder_name(self, name):
        """Convierte un nombre de carpeta a formato válido para sistema de archivos"""
        sanitized = name.lower().strip()
        sanitized = re.sub(r'[^a-z0-9\s\-_]', '', sanitized)
        sanitized = re.sub(r'\s+', '_', sanitized)
        sanitized = re.sub(r'_+', '_', sanitized)
        return sanitized.strip('_')
    
    def load_preset(self, preset_type, preset_name):
        """Carga un preset específico"""
        safe_filename = re.sub(r'[^\w\s-]', '', preset_name).strip()
        safe_filename = re.sub(r'[-\s]+', '_', safe_filename).lower()
        
        file_path = os.path.join(self.presets_dir, preset_type, f"{safe_filename}.json")
        
        if not os.path.exists(file_path):
            return None
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            preset_data = data.get('presets', {}).get(safe_filename, {})
            
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
        """Elimina el archivo JSON del preset y su carpeta de imágenes asociada"""
        try:
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
        """Elimina por completo una carpeta de presets (incluye JSON e imágenes)"""
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
        """Renombra una carpeta de presets moviendo el directorio"""
        try:
            new_folder_id = self.sanitize_folder_name(new_display_name)
            if not new_folder_id:
                return (False, "")

            old_path = os.path.join(self.presets_dir, old_folder_id)
            new_path = os.path.join(self.presets_dir, new_folder_id)

            if not os.path.isdir(old_path):
                return (False, "")
            if os.path.exists(new_path):
                return (False, "")

            os.rename(old_path, new_path)
            return (True, new_folder_id)
        except Exception as e:
            print(f"Error renombrando carpeta '{old_folder_id}' a '{new_display_name}': {e}")
            return (False, "")