import json
import os
from PyQt6.QtCore import QObject, pyqtSignal

class SuggestionEngine(QObject):
    """Motor de sugerencias para el sistema de navegación jerárquica
    
    Este motor se encarga de:
    1. Cargar categorías y opciones desde archivos JSON
    2. Mantener el contexto de navegación
    3. Generar sugerencias basadas en el contexto actual
    4. Aplicar reglas de sugerencia según el flujo de navegación
    """
    
    # Señales para comunicar eventos
    suggestions_updated = pyqtSignal(dict)  # Emite cuando hay nuevas sugerencias disponibles
    error_occurred = pyqtSignal(str)  # Emite cuando ocurre un error
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Rutas a archivos de datos
        self.base_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'sugeprompt')
        self.categories_path = os.path.join(self.base_path, 'prompt_categories.json')
        self.category_files_path = os.path.join(self.base_path, 'categories')
        
        # Datos cargados
        self.categories = {}
        self.options = {}
        self.translations = {}
        
        # Estado actual
        self.current_context = {}
        self.category_stack = []
        self.current_selections = {}
        
        # Cargar datos iniciales
        self.load_categories()
    
    def load_categories(self):
        """Carga las categorías desde el archivo JSON"""
        try:
            with open(self.categories_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.categories = data.get('categorias', {})
            
            # Cargar traducciones de categorías
            for category_id, category_data in self.categories.items():
                if 'label' in category_data and 'es' in category_data['label']:
                    self.translations[category_id] = category_data['label']['es']
                else:
                    self.translations[category_id] = category_id.replace('_', ' ').title()
            
            print(f"Categorías cargadas: {list(self.categories.keys())}")
            
        except Exception as e:
            self.error_occurred.emit(f"Error cargando categorías: {e}")
    
    def get_next_categories(self, current_category=None, option_id=None):
        """Obtiene las siguientes categorías disponibles
        
        Args:
            current_category: Categoría actual (opcional)
            option_id: Opción seleccionada en la categoría actual (opcional)
            
        Returns:
            Lista de IDs de categorías siguientes
        """
        if current_category is None:
            # Si no hay categoría actual, devolver todas las categorías de primer nivel
            return list(self.categories.keys())
        
        # Si hay una opción seleccionada, verificar si tiene subcategorías
        if option_id:
            # Cargar datos de la opción si no están cargados
            option_data = self.load_option_data(current_category, option_id)
            if option_data and 'subcategories' in option_data:
                # Devolver las subcategorías definidas en la opción
                return list(option_data['subcategories'].keys())
        
        # Si no hay subcategorías específicas, usar el orden predefinido
        category_order = [
            'vestuario_general',
            'vestuario_superior',
            'vestuario_inferior',
            'angulos_camara',
            'poses',
            'cuerpo',
            'expresiones'
        ]
        
        # Encontrar la posición de la categoría actual
        try:
            current_index = category_order.index(current_category)
            # Devolver la siguiente categoría si existe
            if current_index < len(category_order) - 1:
                return [category_order[current_index + 1]]
        except ValueError:
            pass
        
        # Si no hay siguiente categoría, devolver lista vacía
        return []
    
    def load_option_data(self, category_id, option_id):
        """Carga los datos detallados de una opción
        
        Args:
            category_id: ID de la categoría
            option_id: ID de la opción
            
        Returns:
            Datos de la opción o None si no se encuentra
        """
        import sys
        print(f"DEBUG - load_option_data llamado para {category_id}.{option_id}", flush=True)
        sys.stdout.flush()
        
        # Verificar si ya tenemos los datos cargados
        cache_key = f"{category_id}.{option_id}"
        if cache_key in self.options:
            print(f"DEBUG - Usando datos en caché para {cache_key}", flush=True)
            sys.stdout.flush()
            return self.options[cache_key]
        
        # Intentar cargar desde el archivo específico de la opción
        option_file = os.path.join(self.category_files_path, category_id, f"{option_id}.json")
        print(f"DEBUG - Buscando archivo específico: {option_file}", flush=True)
        sys.stdout.flush()
        
        if os.path.exists(option_file):
            try:
                print(f"DEBUG - Archivo específico encontrado: {option_file}", flush=True)
                sys.stdout.flush()
                with open(option_file, 'r', encoding='utf-8') as f:
                    option_data = json.load(f)
                
                print(f"DEBUG - Datos cargados de archivo específico. Claves: {option_data.keys()}", flush=True)
                sys.stdout.flush()
                
                # Combinar con los datos básicos de la opción desde el archivo de categoría
                category_file = os.path.join(self.category_files_path, f"{category_id}.json")
                if os.path.exists(category_file):
                    try:
                        with open(category_file, 'r', encoding='utf-8') as f:
                            category_data = json.load(f)
                        
                        # Buscar la opción en las opciones de la categoría y combinar datos
                        if 'options' in category_data and option_id in category_data['options']:
                            base_option_data = category_data['options'][option_id]
                            print(f"DEBUG - Combinando con datos básicos. Claves básicas: {base_option_data.keys()}", flush=True)
                            sys.stdout.flush()
                            # Combinar los datos básicos con los datos detallados
                            for key, value in base_option_data.items():
                                if key not in option_data:
                                    option_data[key] = value
                    except Exception as e:
                        print(f"Advertencia: Error al combinar datos de categoría {category_id}: {e}", flush=True)
                        sys.stdout.flush()
                
                print(f"DEBUG - Datos finales combinados. Claves: {option_data.keys()}", flush=True)
                sys.stdout.flush()
                self.options[cache_key] = option_data
                return option_data
            except Exception as e:
                print(f"DEBUG - Error cargando archivo específico: {e}", flush=True)
                sys.stdout.flush()
                self.error_occurred.emit(f"Error cargando opción {option_id}: {e}")
        
        # Si no hay archivo específico, buscar en el archivo de categoría
        category_file = os.path.join(self.category_files_path, f"{category_id}.json")
        print(f"DEBUG - Buscando en archivo de categoría: {category_file}", flush=True)
        sys.stdout.flush()
        
        if os.path.exists(category_file):
            try:
                with open(category_file, 'r', encoding='utf-8') as f:
                    category_data = json.load(f)
                
                # Buscar la opción en las opciones de la categoría
                if 'options' in category_data and option_id in category_data['options']:
                    option_data = category_data['options'][option_id]
                    print(f"DEBUG - Datos cargados de archivo de categoría. Claves: {option_data.keys()}", flush=True)
                    sys.stdout.flush()
                    self.options[cache_key] = option_data
                    return option_data
            except Exception as e:
                print(f"DEBUG - Error cargando archivo de categoría: {e}", flush=True)
                sys.stdout.flush()
                self.error_occurred.emit(f"Error cargando categoría {category_id}: {e}")
        
        print(f"DEBUG - No se encontraron datos para {category_id}.{option_id}", flush=True)
        sys.stdout.flush()
        return None
    
    def get_suggestions_for_category(self, category_id):
        """Obtiene las sugerencias para una categoría específica
        
        Args:
            category_id: ID de la categoría
            
        Returns:
            Diccionario con las opciones disponibles para la categoría
        """
        # Verificar si la categoría existe
        if category_id not in self.categories:
            self.error_occurred.emit(f"Categoría no encontrada: {category_id}")
            return {}
        
        # Cargar opciones desde el archivo de categoría
        category_file = os.path.join(self.category_files_path, f"{category_id}.json")
        if os.path.exists(category_file):
            try:
                with open(category_file, 'r', encoding='utf-8') as f:
                    category_data = json.load(f)
                
                # Devolver las opciones de la categoría
                if 'options' in category_data:
                    # Cargar traducciones para las opciones
                    for option_id, option_data in category_data['options'].items():
                        if 'label' in option_data and 'es' in option_data['label']:
                            self.translations[f"{category_id}.{option_id}"] = option_data['label']['es']
                    
                    return category_data['options']
            except Exception as e:
                self.error_occurred.emit(f"Error cargando categoría {category_id}: {e}")
        
        # Si no hay archivo específico, usar las opciones definidas en el archivo de categorías
        if 'opciones' in self.categories[category_id]:
            # Convertir la lista de opciones en un diccionario
            options = {}
            for option_id in self.categories[category_id]['opciones']:
                # Intentar cargar datos detallados de la opción
                option_data = self.load_option_data(category_id, option_id)
                if option_data:
                    options[option_id] = option_data
                else:
                    # Si no hay datos detallados, crear una opción básica
                    options[option_id] = {
                        'prompt': option_id.replace('_', ' '),
                        'label': {'en': option_id.replace('_', ' ').title(), 'es': option_id.replace('_', ' ').title()}
                    }
                    # Guardar traducción
                    self.translations[f"{category_id}.{option_id}"] = options[option_id]['label']['es']
            
            return options
        
        return {}
    
    def update_context(self, category_id, option_id):
        """Actualiza el contexto con una nueva selección
        
        Args:
            category_id: ID de la categoría
            option_id: ID de la opción seleccionada
        """
        # Guardar selección en el contexto
        self.current_context[category_id] = option_id
        self.current_selections[category_id] = option_id
        
        # Cargar datos de la opción
        option_data = self.load_option_data(category_id, option_id)
        if option_data:
            # Si la opción tiene un prompt definido, guardarlo
            if 'prompt' in option_data:
                self.current_context[f"{category_id}_prompt"] = option_data['prompt']
    
    def get_current_selections(self):
        """Obtiene las selecciones actuales del usuario
        
        Returns:
            Diccionario con las selecciones por categoría
        """
        return self.current_selections.copy()
    
    def generate_prompt_from_selections(self):
        """Genera un texto de prompt basado en las selecciones actuales
        
        Returns:
            Texto del prompt generado
        """
        prompt_parts = []
        
        # Recorrer las selecciones en orden de categoría
        category_order = [
            'vestuario_general',
            'vestuario_superior',
            'vestuario_inferior',
            'angulos_camara',
            'poses',
            'cuerpo',
            'expresiones'
        ]
        
        for category_id in category_order:
            if category_id in self.current_selections:
                option_id = self.current_selections[category_id]
                option_data = self.load_option_data(category_id, option_id)
                
                if option_data and 'prompt' in option_data:
                    prompt_parts.append(option_data['prompt'])
                else:
                    # Si no hay prompt específico, usar el ID de la opción
                    prompt_parts.append(option_id.replace('_', ' '))
        
        # Unir las partes con comas
        return ', '.join(prompt_parts)
    
    def get_translation(self, key):
        """Obtiene la traducción para una clave
        
        Args:
            key: Clave de traducción (category_id o category_id.option_id)
            
        Returns:
            Texto traducido o la clave original si no hay traducción
        """
        return self.translations.get(key, key.replace('_', ' ').title())
    
    def generate_prompt_text(self, selections):
        """Genera un texto de prompt basado en selecciones específicas
        
        Args:
            selections: Diccionario con selecciones por categoría
            
        Returns:
            Texto del prompt generado
        """
        prompt_parts = []
        
        # Recorrer las selecciones proporcionadas
        for category_id, option_id in selections.items():
            option_data = self.load_option_data(category_id, option_id)
            
            if option_data and 'prompt' in option_data:
                prompt_parts.append(option_data['prompt'])
            else:
                # Si no hay prompt específico, usar el ID de la opción
                prompt_parts.append(option_id.replace('_', ' '))
        
        # Unir las partes con comas
        return ', '.join(prompt_parts)