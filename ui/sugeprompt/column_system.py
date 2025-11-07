import os
import json
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QScrollArea, QFrame, QListWidget,
    QListWidgetItem, QTreeWidget, QTreeWidgetItem
)
from PyQt6.QtCore import Qt, pyqtSignal

class ColumnSystem(QWidget):
    """Sistema de columnas dinámicas basado en la selección de opciones"""
    
    # Señales
    item_selected = pyqtSignal(str, dict)  # Emite el ID del item y sus datos
    column_changed = pyqtSignal(int)  # Emite el índice de la columna actual
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_option_id = None
        self.current_data = None
        self.current_column = 0
        self.columns = []
        self.column_widgets = []
        
        # Configuración de la interfaz
        self.setup_ui()
    
    def setup_ui(self):
        """Configura la interfaz de usuario"""
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Título
        title = QLabel("Sistema de Columnas")
        title.setStyleSheet("""
            QLabel {
                font-size: 12px;
                font-weight: bold;
                color: #e0e0e0;
                margin-bottom: 5px;
            }
        """)
        self.main_layout.addWidget(title)
        
        # Contenedor para las columnas
        self.columns_container = QWidget()
        self.columns_layout = QHBoxLayout(self.columns_container)
        self.columns_layout.setContentsMargins(0, 0, 0, 0)
        self.columns_layout.setSpacing(5)
        
        # Scroll area para las columnas
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.columns_container)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: transparent;
                border: none;
            }
        """)
        
        self.main_layout.addWidget(scroll_area)
    
    def load_option(self, option_id, option_data):
        """Carga una opción y genera las columnas correspondientes"""
        self.current_option_id = option_id
        self.current_data = option_data
        self.current_column = 0
        
        # Limpiar columnas existentes
        self.clear_columns()
        
        # Cargar datos específicos del archivo JSON
        self.load_specific_data(option_id)
        
        # Generar columnas iniciales
        self.generate_initial_columns()
    
    def load_specific_data(self, option_id):
        """Carga datos específicos del archivo JSON"""
        option_file_path = os.path.join('data', 'sugeprompt', 'categories', 'vestuario_general', f"{option_id}.json")
        
        if os.path.exists(option_file_path):
            try:
                with open(option_file_path, 'r', encoding='utf-8') as file:
                    specific_data = json.load(file)
                    
                # Combinar datos específicos con los datos generales
                if isinstance(self.current_data, dict) and isinstance(specific_data, dict):
                    for key, value in specific_data.items():
                        if key not in self.current_data:
                            self.current_data[key] = value
            except Exception as e:
                print(f"Error al cargar datos específicos: {e}")
    
    def generate_initial_columns(self):
        """Genera las columnas iniciales basadas en los datos cargados"""
        if not self.current_data or 'flow_vestuary' not in self.current_data:
            return
        
        # Crear una columna combinada para vestuario superior e inferior
        combined_data = {}
        
        # Agregar datos de vestuario superior
        if 'vestuario_superior' in self.current_data['flow_vestuary']:
            combined_data['vestuario_superior'] = self.current_data['flow_vestuary']['vestuario_superior']
        
        # Agregar datos de vestuario inferior
        if 'vestuario_inferior' in self.current_data['flow_vestuary']:
            combined_data['vestuario_inferior'] = self.current_data['flow_vestuary']['vestuario_inferior']
        
        # Crear una columna combinada si hay datos
        if combined_data:
            self.add_combined_column('vestuario_completo', combined_data)
    
    def add_combined_column(self, column_id, combined_data):
        """Agrega una columna combinada con secciones para vestuario superior e inferior"""
        # Crear widget de columna
        column_widget = QFrame()
        column_widget.setFrameShape(QFrame.Shape.StyledPanel)
        column_widget.setStyleSheet("""
            QFrame {
                background-color: #383838;
                border: 1px solid #555;
                border-radius: 6px;
            }
        """)
        
        column_layout = QVBoxLayout(column_widget)
        column_layout.setContentsMargins(5, 5, 5, 5)
        column_layout.setSpacing(5)
        
        # Título de la columna
        title_label = QLabel("Vestuario Completo")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 11px;
                font-weight: bold;
                color: #e0e0e0;
            }
        """)
        column_layout.addWidget(title_label)
        
        # Lista combinada para ambos tipos de vestuario con estructura de árbol
        items_list = QTreeWidget()
        items_list.setHeaderHidden(True)  # Ocultar cabecera
        items_list.setStyleSheet("""
            QTreeWidget {
                background-color: #2d2d2d;
                border: 1px solid #444;
                border-radius: 4px;
                color: #e0e0e0;
                font-size: 10px;
            }
            QTreeWidget::item {
                padding: 5px;
                border-bottom: 1px solid #444;
            }
            QTreeWidget::item:selected {
                background-color: #4a90e2;
                color: white;
            }
            QTreeWidget::item:hover {
                background-color: #3a3a3a;
            }
            QTreeWidget::branch {
                background-color: #2d2d2d;
            }
            QTreeWidget::branch:selected {
                background-color: #4a90e2;
            }
        """)
        
        # Procesar cada tipo de vestuario
        for section_id, section_data in combined_data.items():
            # Agregar encabezado de sección como elemento padre
            section_title = self.get_column_title(section_id, section_data)
            section_header = QTreeWidgetItem([section_title])
            section_header.setFlags(Qt.ItemFlag.ItemIsEnabled)  # No seleccionable pero visible
            section_header.setBackground(0, Qt.GlobalColor.darkGray)
            section_header.setForeground(0, Qt.GlobalColor.white)
            items_list.addTopLevelItem(section_header)
            
            # Agregar opción "Ninguno" si está habilitada como hijo del encabezado
            none_option_key = f"none_option_{section_id}"
            if none_option_key in section_data and section_data[none_option_key]:
                none_text = self.get_translation(section_data, "none", "Ninguno")
                none_item = QTreeWidgetItem([none_text])
                # Guardar el tipo de vestuario correcto para "Ninguno"
                none_item.setData(0, Qt.ItemDataRole.UserRole, {"id": "none", "type": section_id, "is_none": True})
                section_header.addChild(none_item)
            
            # Agregar items de la sección como hijos del encabezado
            items_key = f"items_{section_id}"
            if items_key in section_data:
                for item in section_data[items_key]:
                    item_id_key = f"item_id_{section_id}"
                    if item_id_key in item:
                        item_id = item[item_id_key]
                        item_text = self.get_item_translation(section_data, item_id, item_id.replace('_', ' '))
                        tree_item = QTreeWidgetItem([item_text])
                        tree_item.setData(0, Qt.ItemDataRole.UserRole, {"id": item_id, "data": item, "type": section_id})
                        section_header.addChild(tree_item)
            
            # Expandir la sección por defecto
            section_header.setExpanded(True)
        
        # Conectar señal de selección
        # Para la columna combinada, pasamos el tipo de vestuario (vestuario_superior o vestuario_inferior)
        # que está almacenado en el UserRole de cada item
        items_list.itemClicked.connect(lambda item: self.on_tree_item_clicked(item, column_id))
        
        column_layout.addWidget(items_list)
        
        # Agregar columna al layout
        self.columns_layout.addWidget(column_widget)
        self.column_widgets.append(column_widget)
        self.columns.append({"id": column_id, "data": combined_data, "list_widget": items_list})
    
    def add_column(self, column_id, column_data):
        """Agrega una nueva columna al sistema"""
        # Crear widget de columna
        column_widget = QFrame()
        column_widget.setFrameShape(QFrame.Shape.StyledPanel)
        column_widget.setStyleSheet("""
            QFrame {
                background-color: #383838;
                border: 1px solid #555;
                border-radius: 6px;
                min-width: 150px;
                max-width: 200px;
            }
        """)
        
        column_layout = QVBoxLayout(column_widget)
        column_layout.setContentsMargins(5, 5, 5, 5)
        column_layout.setSpacing(5)
        
        # Título de la columna
        title = self.get_column_title(column_id, column_data)
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 11px;
                font-weight: bold;
                color: #e0e0e0;
            }
        """)
        column_layout.addWidget(title_label)
        
        # Lista de items con estructura de árbol
        items_list = QTreeWidget()
        items_list.setHeaderHidden(True)  # Ocultar cabecera
        items_list.setStyleSheet("""
            QTreeWidget {
                background-color: #2d2d2d;
                border: 1px solid #444;
                border-radius: 4px;
                color: #e0e0e0;
                font-size: 10px;
            }
            QTreeWidget::item {
                padding: 5px;
                border-bottom: 1px solid #444;
            }
            QTreeWidget::item:selected {
                background-color: #4a90e2;
                color: white;
            }
            QTreeWidget::item:hover {
                background-color: #3a3a3a;
            }
            QTreeWidget::branch {
                background-color: #2d2d2d;
            }
        """)
        
        # Agregar opción "Ninguno" si está habilitada
        none_option_key = f"none_option_{column_id}"
        if none_option_key in column_data and column_data[none_option_key]:
            none_text = self.get_translation(column_data, "none", "Ninguno")
            none_item = QTreeWidgetItem([none_text])
            
            # Si es una columna de partes, extraer el tipo de vestuario original
            if column_id.startswith("partes_"):
                vestuario_type = column_id.replace("partes_", "")
                none_item.setData(0, Qt.ItemDataRole.UserRole, {"id": "none", "type": vestuario_type, "is_none": True})
            else:
                none_item.setData(0, Qt.ItemDataRole.UserRole, {"id": "none", "type": column_id, "is_none": True})
            
            items_list.addTopLevelItem(none_item)
        
        # Agregar items de la columna
        items_key = f"items_{column_id}"
        if items_key in column_data:
            print(f"Agregando {len(column_data[items_key])} items a la columna {column_id}")
            
            # Verificar si esta columna debe mostrar subcategorías con elementos anidados
            if "show_nested_items" in column_data and column_data["show_nested_items"]:
                self.add_nested_items_to_column(items_list, column_data, column_id)
            else:
                # Comportamiento original para columnas normales
                for item in column_data[items_key]:
                    item_id_key = f"item_id_{column_id}"
                    if item_id_key in item:
                        item_id = item[item_id_key]
                        item_text = self.get_item_translation(column_data, item_id, item_id.replace('_', ' '))
                        list_item = QTreeWidgetItem([item_text])
                        list_item.setData(0, Qt.ItemDataRole.UserRole, item)
                        items_list.addTopLevelItem(list_item)
            
            # Verificar si necesitamos agrupar por subcategoría
            subcategory_key = f"subcategory_{column_id}"
            items_by_subcategory = {}
            
            # Agrupar items por subcategoría si existe el campo
            for item in column_data[items_key]:
                # Buscar la clave del ID del item
                item_id = None
                for key in item.keys():
                    if key.startswith("item_id_"):
                        item_id = item[key]
                        break
                
                if item_id:
                    # Verificar si tiene subcategoría
                    subcategory = item.get(subcategory_key, "default")
                    
                    # Agrupar por subcategoría
                    if subcategory not in items_by_subcategory:
                        items_by_subcategory[subcategory] = []
                    
                    items_by_subcategory[subcategory].append({
                        "id": item_id,
                        "data": item,
                        "type": column_id
                    })
            
            # Si hay subcategorías, mostrar agrupados
            if len(items_by_subcategory) > 1:
                # Ordenar subcategorías para mostrar primero torso, luego headwear, luego extremities
                subcategory_order = ["torso", "headwear", "extremities", "default"]
                
                for subcategory in subcategory_order:
                    if subcategory in items_by_subcategory:
                        # Crear un elemento padre para la subcategoría
                        subcategory_label = self.get_subcategory_translation(column_data, subcategory)
                        category_item = QTreeWidgetItem([subcategory_label])
                        category_item.setFlags(Qt.ItemFlag.ItemIsEnabled)  # No seleccionable pero visible
                        category_item.setBackground(0, Qt.GlobalColor.darkGray)
                        category_item.setForeground(0, Qt.GlobalColor.white)
                        items_list.addTopLevelItem(category_item)
                        
                        # Agregar los items de esta subcategoría como hijos
                        for item_data in items_by_subcategory[subcategory]:
                            item_text = item_data["id"].replace('_', ' ').title()
                            print(f"Agregando item {item_data['id']} a la columna {column_id} (subcategoría {subcategory})")
                            child_item = QTreeWidgetItem([item_text])
                            child_item.setData(0, Qt.ItemDataRole.UserRole, item_data)
                            category_item.addChild(child_item)
                        
                        # Expandir la categoría por defecto
                        category_item.setExpanded(True)
            else:
                # Si no hay subcategorías o solo hay una, mostrar normal
                for item in column_data[items_key]:
                    # Buscar la clave del ID del item
                    item_id = None
                    for key in item.keys():
                        if key.startswith("item_id_"):
                            item_id = item[key]
                            break
                    
                    if item_id:
                        # Usar el ID encontrado para el texto del item
                        item_text = item_id.replace('_', ' ').title()
                        print(f"Agregando item {item_id} a la columna {column_id}")
                        tree_item = QTreeWidgetItem([item_text])
                        tree_item.setData(0, Qt.ItemDataRole.UserRole, {"id": item_id, "data": item, "type": column_id})
                        items_list.addTopLevelItem(tree_item)
                else:
                    print(f"No se encontró ID para el item {item} en la columna {column_id}")
        
        # Conectar señal de selección
        items_list.itemClicked.connect(lambda item: self.on_tree_item_clicked(item, column_id))
        
        column_layout.addWidget(items_list)
        
        # Agregar columna al layout
        self.columns_layout.addWidget(column_widget)
        self.column_widgets.append(column_widget)
        self.columns.append({"id": column_id, "data": column_data, "list_widget": items_list})
    
    def on_tree_item_clicked(self, item, column_id):
        """Maneja el clic en un item de un árbol"""
        # Verificar si el item es un encabezado de categoría (no tiene datos de usuario)
        item_data = item.data(0, Qt.ItemDataRole.UserRole)
        if not item_data:
            print("Item sin datos de usuario (probablemente un encabezado)")
            return
        
        # Verificar si el item tiene hijos (es un padre con subcategorías)
        if item.childCount() > 0:
            # Si es un elemento padre, expandir/colapsar en lugar de seleccionar
            if item.isExpanded():
                item.setExpanded(False)
            else:
                item.setExpanded(True)
            return
        
        # Procesar el item normalmente si es un elemento hijo seleccionable
        self.on_item_clicked(item, column_id)
    
    def on_item_clicked(self, item, column_id):
        """Maneja el clic en un item de una columna"""
        # Para QTreeWidget, los datos están en la columna 0
        if isinstance(item, QTreeWidgetItem):
            item_data = item.data(0, Qt.ItemDataRole.UserRole)
        else:
            item_data = item.data(Qt.ItemDataRole.UserRole)
            
        if not item_data:
            print("Error: No hay datos en el item")
            return
            
        # Imprimir información detallada para depuración
        print(f"on_item_clicked: Item={item_data.get('id', 'unknown')}, Column={column_id}, Data={item_data}")
        
        # Obtener el tipo de vestuario (superior o inferior)
        item_type = item_data.get("type", "")
        
        print(f"Item clickeado: {item_data['id']} de tipo {item_type} en columna {column_id}")
        print(f"Datos completos del item: {item_data}")
        
        # Actualizar el índice de la columna actual y emitir señal
        current_index = next((i for i, col in enumerate(self.columns) if col["id"] == column_id), -1)
        if current_index >= 0:
            self.current_column = current_index
            self.column_changed.emit(current_index)
        
        # Emitir señal de item seleccionado
        self.item_selected.emit(item_data["id"], item_data)
        
        # Si es "Ninguno", generar columna con todas las partes del vestuario
        if item_data["id"] == "none" and item_data.get("is_none", False):
            print(f"Generando partes para {item_type} (Ninguno seleccionado)")
            # Eliminar columnas posteriores a la actual antes de generar nuevas
            if current_index >= 0:
                self.remove_columns_after(current_index)
            result = self.generate_parts_column(item_type)
            print(f"Resultado de generate_parts_column: {result}")
        # Si es una subcategoría específica (torso_interior, torso_exterior, etc.)
        elif column_id == "torso_subcategories" or column_id == "head_subcategories":
            print(f"Subcategoría seleccionada: {item_data['id']}")
            # No hacemos nada aquí porque los elementos ya están cargados como hijos en el TreeWidget
        # Si es una parte del vestuario (subcategoría)
        elif column_id.startswith("partes_"):
            print(f"Generando items para parte {item_data['id']} de tipo {item_type}")
            # Eliminar columnas posteriores a la actual antes de generar nuevas
            if current_index >= 0:
                self.remove_columns_after(current_index)
            self.generate_items_for_part(item_data["id"], item_type)
        # Si es un elemento de vestuario (como blazer, polo_shirt, etc.) o un accesorio (como badge, tie, etc.)
        elif column_id in ["vestuario_superior", "vestuario_inferior"] or column_id.endswith("_accessory") or "torso_" in column_id or "head_" in column_id:
            # Eliminar columnas posteriores a la actual antes de generar nuevas
            if current_index >= 0:
                self.remove_columns_after(current_index)
                print(f"Eliminando columnas después de {column_id} en índice {current_index}")
                
            # Buscar el ítem seleccionado en los datos originales para obtener su subcategoría y next_parts
            if self.current_data and 'flow_vestuary' in self.current_data and column_id in self.current_data['flow_vestuary']:
                vestuario_data = self.current_data['flow_vestuary'][column_id]
                items_key = f"items_{column_id}"
                
                if items_key in vestuario_data:
                    # Buscar el ítem seleccionado en la lista de ítems
                    item_id = item_data["id"]
                    found_item = None
                    
                    for item_obj in vestuario_data[items_key]:
                        item_id_key = f"item_id_{column_id}"
                        if item_id_key in item_obj and item_obj[item_id_key] == item_id:
                            found_item = item_obj
                            break
                    
                    if found_item:
                        # Obtener la subcategoría del ítem
                        subcategory_key = f"subcategory_{column_id}"
                        if subcategory_key in found_item:
                            subcategory = found_item[subcategory_key]
                            print(f"Elemento encontrado: {item_id} con subcategoría: {subcategory}")
                            
                            # Verificar si hay next_parts para esta subcategoría
                            next_parts_key = f"next_parts_{subcategory}"
                            if next_parts_key in found_item:
                                print(f"Encontrado next_parts para {subcategory}: {next_parts_key}")
                                next_parts_data = found_item[next_parts_key]
                                
                                # Manejo especial para accesorios como badge
                                if item_id == "badge":
                                    print(f"Detectado badge en columna {column_id}")
                                    # Eliminar columnas duplicadas si existen
                                    for i, col in enumerate(self.columns):
                                        if col["id"].startswith("torso_") and col["id"] != column_id:
                                            print(f"Eliminando columna duplicada: {col['id']}")
                                            self.remove_columns_after(i-1)
                                            break
                                
                                # Crear datos para la columna de elementos
                                items_column_id = subcategory
                                
                                # Preparar los datos para la columna
                                column_data = {
                                    "type": subcategory,
                                    f"items_{subcategory}": next_parts_data[f"items_{subcategory}"],
                                    f"none_option_{subcategory}": next_parts_data.get(f"none_option_{subcategory}", True),
                                    f"translations_{subcategory}": {
                                        "es": {
                                            "label": self.get_subcategory_translation(vestuario_data, subcategory),
                                            "items": {},
                                            "none": "Ninguno"
                                        }
                                    }
                                }
                                
                                # Imprimir datos para depuración
                                print(f"Datos de la columna para {subcategory}: {column_data}")
                                
                                # Verificar si ya existe una columna con este ID
                                existing_column_index = next((i for i, col in enumerate(self.columns) if col["id"] == subcategory), -1)
                                if existing_column_index >= 0:
                                    print(f"Actualizando columna existente para {subcategory}")
                                    # Actualizar la columna existente
                                    self.update_column(subcategory, column_data)
                                else:
                                    # Agregar una nueva columna
                                    print(f"Generando nueva columna para {subcategory}")
                                    self.add_column(subcategory, column_data)
                                return
                            else:
                                print(f"No se encontró next_parts para la subcategoría {subcategory}")
                                # Si no hay next_parts, generar columna de partes
                                self.generate_parts_column(column_id)
                        else:
                            print(f"No se encontró subcategoría para {item_id}")
                            self.generate_parts_column(column_id)
                    else:
                        print(f"No se encontró el ítem {item_id} en los datos originales")
                        self.generate_parts_column(column_id)
                else:
                    print(f"No se encontraron ítems para {column_id}")
                    self.generate_parts_column(column_id)
            else:
                print(f"No hay datos disponibles para {column_id}")
                self.generate_parts_column(column_id)
        # Si no es "Ninguno", generar siguiente columna si corresponde
        elif "data" in item_data:
            print(f"Generando siguiente columna para {item_data['id']} de tipo {item_type}")
            self.generate_next_column(item_data["data"], item_type)
        else:
            print(f"No se pudo determinar qué hacer con el item {item_data['id']} de tipo {item_type}")
    
    def update_column(self, column_id, column_data):
        """Actualiza una columna existente con nuevos datos"""
        # Buscar la columna existente
        column_index = next((i for i, col in enumerate(self.columns) if col["id"] == column_id), -1)
        if column_index < 0:
            print(f"Error: No se encontró la columna {column_id} para actualizar")
            return False
        
        # Obtener el widget de la lista
        tree_widget = self.columns[column_index]["list_widget"]
        
        # Limpiar la lista actual
        tree_widget.clear()
        
        # Actualizar los datos de la columna
        self.columns[column_index]["data"] = column_data
        
        # Agregar opción "Ninguno" si está habilitada
        none_option_key = f"none_option_{column_id}"
        if none_option_key in column_data and column_data[none_option_key]:
            none_text = self.get_translation(column_data, "none", "Ninguno")
            none_item = QTreeWidgetItem([none_text])
            
            # Si es una columna de partes, extraer el tipo de vestuario original
            if column_id.startswith("partes_"):
                vestuario_type = column_id.replace("partes_", "")
                none_item.setData(0, Qt.ItemDataRole.UserRole, {"id": "none", "type": vestuario_type, "is_none": True})
            else:
                none_item.setData(0, Qt.ItemDataRole.UserRole, {"id": "none", "type": column_id, "is_none": True})
            
            tree_widget.addTopLevelItem(none_item)
        
        # Agregar items de la columna
        items_key = f"items_{column_id}"
        if items_key in column_data:
            print(f"Actualizando {len(column_data[items_key])} items en la columna {column_id}")
            
            # Verificar si necesitamos agrupar por subcategoría
            subcategory_key = f"subcategory_{column_id}"
            items_by_subcategory = {}
            
            # Agrupar items por subcategoría si existe el campo
            for item in column_data[items_key]:
                # Buscar la clave del ID del item
                item_id = None
                for key in item.keys():
                    if key.startswith("item_id_"):
                        item_id = item[key]
                        break
                
                if item_id:
                    # Verificar si tiene subcategoría
                    subcategory = item.get(subcategory_key, "default")
                    
                    # Agrupar por subcategoría
                    if subcategory not in items_by_subcategory:
                        items_by_subcategory[subcategory] = []
                    
                    items_by_subcategory[subcategory].append({
                        "id": item_id,
                        "data": item,
                        "type": column_id
                    })
            
            # Si hay subcategorías, mostrar agrupados
            if len(items_by_subcategory) > 1:
                # Ordenar subcategorías para mostrar primero torso, luego headwear, luego extremities
                subcategory_order = ["torso", "headwear", "extremities", "default"]
                
                for subcategory in subcategory_order:
                    if subcategory in items_by_subcategory:
                        # Crear un elemento padre para la subcategoría
                        subcategory_label = self.get_subcategory_translation(column_data, subcategory)
                        category_item = QTreeWidgetItem([subcategory_label])
                        category_item.setFlags(Qt.ItemFlag.ItemIsEnabled)  # No seleccionable pero visible
                        category_item.setBackground(0, Qt.GlobalColor.darkGray)
                        category_item.setForeground(0, Qt.GlobalColor.white)
                        tree_widget.addTopLevelItem(category_item)
                        
                        # Agregar los items de esta subcategoría como hijos
                        for item_data in items_by_subcategory[subcategory]:
                            item_text = item_data["id"].replace('_', ' ').title()
                            print(f"Actualizando item {item_data['id']} en la columna {column_id} (subcategoría {subcategory})")
                            child_item = QTreeWidgetItem([item_text])
                            child_item.setData(0, Qt.ItemDataRole.UserRole, item_data)
                            category_item.addChild(child_item)
                        
                        # Expandir la categoría por defecto
                        category_item.setExpanded(True)
            else:
                # Si no hay subcategorías o solo hay una, mostrar normal
                for item in column_data[items_key]:
                    # Buscar la clave del ID del item
                    item_id = None
                    for key in item.keys():
                        if key.startswith("item_id_"):
                            item_id = item[key]
                            break
                    
                    if item_id:
                        # Usar el ID encontrado para el texto del item
                        item_text = item_id.replace('_', ' ').title()
                        print(f"Actualizando item {item_id} en la columna {column_id}")
                        tree_item = QTreeWidgetItem([item_text])
                        tree_item.setData(0, Qt.ItemDataRole.UserRole, {"id": item_id, "data": item, "type": column_id})
                        tree_widget.addTopLevelItem(tree_item)
        
        return True
    
    def generate_parts_column(self, vestuario_type):
        """Genera una columna con todas las partes del vestuario cuando se selecciona 'Ninguno'"""
        if not self.current_data or 'flow_vestuary' not in self.current_data:
            print("Error: No hay datos de vestuario disponibles")
            return False
        
        # Obtener datos del tipo de vestuario seleccionado
        if vestuario_type in self.current_data['flow_vestuary']:
            vestuario_data = self.current_data['flow_vestuary'][vestuario_type]
            print(f"Datos de vestuario obtenidos para: {vestuario_type}")
            
            # Crear una columna para las partes del vestuario
            parts_column_id = f"partes_{vestuario_type}"
            parts_data = {}
            
            # Recopilar todas las subcategorías disponibles
            subcategories = set()
            items_key = f"items_{vestuario_type}"
            print(f"Buscando subcategorías en {items_key}")
            
            if items_key in vestuario_data:
                for item in vestuario_data[items_key]:
                    subcategory_key = f"subcategory_{vestuario_type}"
                    print(f"Revisando item: {item}")
                    if subcategory_key in item:
                        subcategory = item[subcategory_key]
                        subcategories.add(subcategory)
                        print(f"Encontrada subcategoría: {subcategory} para {vestuario_type}")
            
            print(f"Subcategorías encontradas para {vestuario_type}: {subcategories}")
            
            if not subcategories:
                print(f"No se encontraron subcategorías para {vestuario_type}")
                return False
            
            if items_key not in vestuario_data:
                print(f"No se encontró la clave {items_key} en los datos de vestuario")
                return False
            
            # Crear datos para la columna de partes
            parts_data[f"items_{parts_column_id}"] = []
            for subcategory in subcategories:
                parts_data[f"items_{parts_column_id}"].append({
                    "id": subcategory,  # Cambiado de "item_id_parts" a "id" para consistencia
                    "subcategory_parts": subcategory,  # Usar la subcategoría real
                    "type": vestuario_type  # Guardar el tipo de vestuario para referencia
                })
                print(f"Agregada parte: {subcategory} para {vestuario_type}")
            
            # Agregar traducciones
            parts_data[f"translations_{parts_column_id}"] = {
                "es": {
                    "label": f"Partes de {self.get_column_title(vestuario_type, vestuario_data)}",
                    "items": {},
                    "none": "Ninguno"
                }
            }
            
            # Agregar traducciones para cada subcategoría
            translations_key = f"translations_{vestuario_type}"
            if translations_key in vestuario_data and "es" in vestuario_data[translations_key]:
                translations = vestuario_data[translations_key]["es"]
                if "subcategories" in translations:
                    for subcategory, translation in translations["subcategories"].items():
                        parts_data[f"translations_{parts_column_id}"]["es"]["items"][subcategory] = translation
                        print(f"Agregada traducción para {subcategory}: {translation}")
            
            # Agregar opción "Ninguno"
            parts_data[f"none_option_{parts_column_id}"] = True
            
            # Agregar título a la columna
            parts_data["title"] = f"Partes de {self.get_column_title(vestuario_type, vestuario_data)}"
            
            # Imprimir datos para depuración
            print(f"Datos de la columna de partes: {parts_data}")
            
            # Verificar si ya existe una columna con este ID
            existing_column_index = next((i for i, col in enumerate(self.columns) if col["id"] == parts_column_id), -1)
            if existing_column_index >= 0:
                print(f"Actualizando columna existente para {parts_column_id}")
                # Actualizar la columna existente
                self.update_column(parts_column_id, parts_data)
            else:
                # Agregar una nueva columna
                print(f"Generando nueva columna para {parts_column_id}")
                self.add_column(parts_column_id, parts_data)
            return True
        else:
            print(f"No se encontró el tipo de vestuario {vestuario_type} en los datos")
        
        return False
        
    def generate_items_for_part(self, part_id, vestuario_type):
        """Genera una columna con los elementos específicos de una parte del vestuario"""
        if not self.current_data or 'flow_vestuary' not in self.current_data:
            print("No hay datos de vestuario disponibles")
            return False
            
        # Eliminar columnas posteriores a la actual
        current_index = next((i for i, col in enumerate(self.columns) if col["id"].startswith("partes_")), -1)
        if current_index >= 0:
            self.remove_columns_after(current_index)
            
        print(f"Buscando elementos para parte {part_id} de tipo {vestuario_type}")
            
        # Obtener datos del tipo de vestuario seleccionado
        if vestuario_type in self.current_data['flow_vestuary']:
            vestuario_data = self.current_data['flow_vestuary'][vestuario_type]
            items_key = f"items_{vestuario_type}"
            
            # Primero buscar si hay next_parts directamente en vestuario_data
            next_parts_key = f"next_parts_{part_id}"
            if next_parts_key in vestuario_data:
                print(f"Encontrado next_parts directamente en vestuario_data: {next_parts_key}")
                next_parts_data = vestuario_data[next_parts_key]
                
                # Crear datos para la columna de elementos
                items_column_id = f"items_{part_id}"
                items_data = {}
                
                # Copiar los datos de next_parts
                for key, value in next_parts_data.items():
                    items_data[key.replace(part_id, items_column_id)] = value
                
                # Agregar título a la columna
                items_data["title"] = self.get_subcategory_translation(vestuario_data, part_id)
                
                # Agregar opción "Ninguno"
                items_data[f"none_option_{items_column_id}"] = True
                
                # Imprimir datos para depuración
                print(f"Datos de la columna de elementos para {part_id}: {items_data}")
                
                # Verificar si ya existe una columna con este ID
                existing_column_index = next((i for i, col in enumerate(self.columns) if col["id"] == items_column_id), -1)
                if existing_column_index >= 0:
                    print(f"Actualizando columna existente para {items_column_id}")
                    # Actualizar la columna existente
                    self.update_column(items_column_id, items_data)
                else:
                    # Agregar una nueva columna
                    print(f"Generando nueva columna para {items_column_id}")
                    self.add_column(items_column_id, items_data)
                return True
            
            # Buscar en todos los elementos del vestuario
            print(f"Buscando elementos con clave {next_parts_key} en items")
            
            for item in vestuario_data.get(items_key, []):
                if next_parts_key in item:
                    print(f"Encontrado elemento con partes: {item}")
                    next_parts_data = item[next_parts_key]
                    
                    # Crear datos para la columna de elementos
                    items_column_id = f"items_{part_id}"
                    items_data = {}
                    
                    # Copiar los datos de next_parts
                    for key, value in next_parts_data.items():
                        items_data[key.replace(part_id, items_column_id)] = value
                    
                    # Agregar título a la columna
                    items_data["title"] = self.get_subcategory_translation(vestuario_data, part_id)
                    
                    # Agregar opción "Ninguno"
                    items_data[f"none_option_{items_column_id}"] = True
                    
                    # Imprimir datos para depuración
                    print(f"Datos de la columna de elementos para {part_id}: {items_data}")
                    
                    # Verificar si ya existe una columna con este ID
                    existing_column_index = next((i for i, col in enumerate(self.columns) if col["id"] == items_column_id), -1)
                    if existing_column_index >= 0:
                        print(f"Actualizando columna existente para {items_column_id}")
                        # Actualizar la columna existente
                        self.update_column(items_column_id, items_data)
                    else:
                        # Agregar una nueva columna
                        print(f"Generando nueva columna para {items_column_id}")
                        self.add_column(items_column_id, items_data)
                    return True
                    
            # Si no encontramos next_parts, buscar elementos por subcategoría
            items_for_part = []
            subcategory_key = f"subcategory_{vestuario_type}"
            
            print(f"Buscando elementos con {subcategory_key}={part_id}")
            
            if items_key in vestuario_data:
                for item in vestuario_data[items_key]:
                    if subcategory_key in item and item[subcategory_key] == part_id:
                        items_for_part.append(item)
                        print(f"Encontrado elemento: {item}")
            
                if items_for_part:
                    # Crear datos para la columna de elementos
                    items_column_id = f"items_{part_id}"
                    items_data = {}
                    
                    # Agregar los elementos a la columna
                    items_data[f"items_{items_column_id}"] = []
                    for item in items_for_part:
                        item_id_key = f"item_id_{vestuario_type}"
                        if item_id_key in item:
                            items_data[f"items_{items_column_id}"].append({
                                f"item_id_{items_column_id}": item[item_id_key],
                                "data": item,
                                "type": vestuario_type
                            })
                    
                    # Agregar título a la columna
                    items_data["title"] = self.get_subcategory_translation(vestuario_data, part_id)
                    
                    # Agregar opción "Ninguno"
                    items_data[f"none_option_{items_column_id}"] = True
                    
                    # Agregar traducciones
                    items_data[f"translations_{items_column_id}"] = {
                        "es": {
                            "label": self.get_subcategory_translation(vestuario_data, part_id),
                            "items": {},
                            "none": "Ninguno"
                        }
                    }
                    
                    # Agregar traducciones para cada elemento
                    translations_key = f"translations_{vestuario_type}"
                    if translations_key in vestuario_data and "es" in vestuario_data[translations_key]:
                        translations = vestuario_data[translations_key]["es"]
                        if "items" in translations:
                            for item in items_for_part:
                                item_id_key = f"item_id_{vestuario_type}"
                                if item_id_key in item and item[item_id_key] in translations["items"]:
                                    item_id = item[item_id_key]
                                    items_data[f"translations_{items_column_id}"]["es"]["items"][item_id] = translations["items"][item_id]
                    
                    # Imprimir datos para depuración
                    print(f"Datos de la columna de elementos para {part_id}: {items_data}")
                    
                    # Agregar la columna
                    print(f"Generando columna de elementos para {part_id}")
                    self.add_column(items_column_id, items_data)
                    return True
                else:
                    print(f"No se encontraron elementos para la parte {part_id}")
            else:
                print(f"No se encontró la clave {items_key} en los datos de vestuario")
        else:
            print(f"No se encontró el tipo de vestuario {vestuario_type} en los datos")
        
        return False
    
    def generate_next_column(self, item_data, parent_column_id):
        """Genera la siguiente columna basada en la selección actual"""
        print(f"Generando siguiente columna con datos: {item_data} y parent_column_id: {parent_column_id}")
        
        # Verificar si ya estamos en una subcategoría específica (torso_interior, torso_accesorios, etc.)
        # En ese caso, no generamos nuevamente la columna de subcategorías
        if parent_column_id.startswith("torso_") or parent_column_id.startswith("head_"):
            print(f"Ya estamos en una subcategoría específica: {parent_column_id}, no generamos columna de subcategorías")
            # Verificar si hay columnas duplicadas y eliminarlas
            existing_columns = [col["id"] for col in self.columns]
            for i, col_id in enumerate(existing_columns):
                if col_id.startswith("torso_") and col_id != parent_column_id:
                    print(f"Eliminando columna duplicada: {col_id}")
                    self.remove_columns_after(i-1)
                    break
            return False
        
        # Caso especial para torso y head
        if parent_column_id in ['torso', 'head']:
            # Eliminar columnas posteriores para evitar duplicación
            current_index = next((i for i, col in enumerate(self.columns) if col["id"] == parent_column_id), -1)
            if current_index >= 0:
                self.remove_columns_after(current_index)
                
            # Generar una columna con subcategorías específicas
            if parent_column_id == 'torso':
                # Para torso, mostrar subcategorías como: prendas interiores, prendas exteriores, accesorios
                self.generate_subcategories_column(parent_column_id, [
                    {"id": "torso_interior", "name": "Prendas Interiores"},
                    {"id": "torso_exterior", "name": "Prendas Exteriores"},
                    {"id": "torso_accesorios", "name": "Accesorios"}
                ])
                return True
            elif parent_column_id == 'head':
                # Para head, mostrar subcategorías como: cabello, accesorios, rostro
                self.generate_subcategories_column(parent_column_id, [
                    {"id": "head_cabello", "name": "Cabello"},
                    {"id": "head_accesorios", "name": "Accesorios"},
                    {"id": "head_rostro", "name": "Rostro"}
                ])
                return True
        
        # Comportamiento original para otras categorías
        subcategory_key = f"subcategory_{parent_column_id}"
        if subcategory_key in item_data:
            subcategory = item_data[subcategory_key]
            next_parts_key = f"next_parts_{subcategory}"
            
            if next_parts_key in item_data:
                print(f"Generando columna para {subcategory} con datos: {next_parts_key}")
                
                # Obtener los datos de next_parts y asegurarse de que la información de subcategoría se pase
                next_parts_data = item_data[next_parts_key]
                
                # Asegurarse de que los items tengan la información de subcategoría
                items_key = f"items_{subcategory}"
                if items_key in next_parts_data:
                    for item in next_parts_data[items_key]:
                        # Agregar la subcategoría original si no existe
                        if f"subcategory_{subcategory}" not in item:
                            item[f"subcategory_{subcategory}"] = subcategory
                        # Asegurar que la información de tipo se pase correctamente
                        if "type" not in item:
                            item["type"] = parent_column_id
                        # Asegurar que la subcategoría del elemento padre se pase a los hijos
                        if subcategory_key not in item and subcategory_key in item_data:
                            item[subcategory_key] = item_data[subcategory_key]
                        # Pasar información adicional de subcategoría si existe en el elemento padre
                        for key in item_data.keys():
                            if key.startswith("subcategory_") and key != subcategory_key and key not in item:
                                item[key] = item_data[key]
                
                # Verificar si ya existe una columna con este ID
                existing_column_index = next((i for i, col in enumerate(self.columns) if col["id"] == subcategory), -1)
                if existing_column_index >= 0:
                    print(f"Actualizando columna existente para {subcategory}")
                    # Actualizar la columna existente
                    self.update_column(subcategory, next_parts_data)
                else:
                    # Agregar una nueva columna
                    print(f"Generando nueva columna para {subcategory}")
                    self.add_column(subcategory, next_parts_data)
                return True
        
        return False
    
    def generate_subcategories_column(self, parent_column_id, subcategories):
        """Genera una columna con subcategorías específicas"""
        print(f"Generando columna de subcategorías para {parent_column_id}")
        
        # Crear datos para la columna
        column_id = f"{parent_column_id}_subcategories"
        column_data = {
            "title": f"Subcategorías de {parent_column_id}",
            f"items_{column_id}": [],
            f"none_option_{column_id}": True,
            f"translations_{column_id}": {
                "es": {
                    "label": f"Subcategorías de {parent_column_id}",
                    "items": {},
                    "none": "Ninguno"
                }
            },
            # Agregar un campo para indicar que esta columna debe mostrar subcategorías con elementos anidados
            "show_nested_items": True,
            "subcategories_data": subcategories,  # Guardar las subcategorías para uso posterior
            "parent_category": parent_column_id  # Guardar la categoría padre
        }
        
        # Agregar subcategorías como items
        for subcategory in subcategories:
            item_data = {
                f"item_id_{column_id}": subcategory["id"],
                "type": column_id,
                "subcategory": parent_column_id,
                "id": subcategory["id"],  # Agregar ID para compatibilidad
                "has_children": True  # Indicar que este item tiene elementos hijos
            }
            column_data[f"items_{column_id}"].append(item_data)
            column_data[f"translations_{column_id}"]["es"]["items"][subcategory["id"]] = subcategory["name"]
        
        # Verificar si ya existe una columna con este ID
        existing_column_index = next((i for i, col in enumerate(self.columns) if col["id"] == column_id), -1)
        if existing_column_index >= 0:
            print(f"Actualizando columna existente para {column_id}")
            # Actualizar la columna existente
            self.update_column(column_id, column_data)
        else:
            # Agregar una nueva columna
            print(f"Generando nueva columna para {column_id}")
            self.add_column(column_id, column_data)
        
        return True
        
    def generate_items_for_subcategory(self, parent_category, subcategory_id):
        """Método auxiliar para obtener los elementos de una subcategoría"""
        print(f"Obteniendo elementos para subcategoría {subcategory_id} de {parent_category}")
        
        # Obtener los elementos para esta subcategoría
        return self.get_items_for_subcategory(parent_category, subcategory_id)
        
    def add_nested_items_to_column(self, tree_widget, column_data, column_id):
        """Agrega elementos anidados a las subcategorías en un TreeWidget"""
        print(f"Agregando elementos anidados a la columna {column_id}")
        
        # Obtener la categoría padre y las subcategorías
        parent_category = column_data.get("parent_category", "")
        subcategories = column_data.get("subcategories_data", [])
        
        # Agregar cada subcategoría como un elemento de nivel superior
        items_key = f"items_{column_id}"
        for item in column_data[items_key]:
            item_id = item.get("id", "")
            item_text = self.get_item_translation(column_data, item_id, item_id.replace('_', ' '))
            
            # Crear el elemento de nivel superior (subcategoría)
            subcategory_item = QTreeWidgetItem([item_text])
            subcategory_item.setData(0, Qt.ItemDataRole.UserRole, item)
            tree_widget.addTopLevelItem(subcategory_item)
            
            # Cargar los elementos hijos para esta subcategoría
            self.load_subcategory_items(subcategory_item, parent_category, item_id)
            
            # Expandir la subcategoría por defecto
            subcategory_item.setExpanded(True)
    
    def load_subcategory_items(self, parent_item, parent_category, subcategory_id):
        """Carga los elementos para una subcategoría específica"""
        print(f"Cargando elementos para subcategoría {subcategory_id} de {parent_category}")
        
        # Obtener los elementos para esta subcategoría
        items = self.get_items_for_subcategory(parent_category, subcategory_id)
        
        # Agregar cada elemento como hijo de la subcategoría
        for item in items:
            item_id = item.get("id", "")
            item_text = item.get("name", item_id.replace('_', ' '))
            
            # Crear el elemento hijo
            child_item = QTreeWidgetItem([item_text])
            child_item.setData(0, Qt.ItemDataRole.UserRole, item)
            parent_item.addChild(child_item)
    
    def get_items_for_subcategory(self, parent_category, subcategory_id):
        """Obtiene los elementos para una subcategoría específica"""
        print(f"Obteniendo elementos para subcategoría {subcategory_id} de {parent_category}")
        
        items = []
        
        # Buscar elementos en los datos del vestuario según la subcategoría
        if self.current_data and 'flow_vestuary' in self.current_data:
            # Determinar el tipo de vestuario (superior o inferior) basado en la subcategoría
            vestuario_type = "vestuario_superior" if subcategory_id.startswith("torso_") or subcategory_id.startswith("head_") else "vestuario_inferior"
            
            if vestuario_type in self.current_data['flow_vestuary']:
                vestuario_data = self.current_data['flow_vestuary'][vestuario_type]
                items_key = f"items_{vestuario_type}"
                
                if items_key in vestuario_data:
                    # Determinar el tipo de subcategoría para filtrar elementos
                    subcategory_type = ""
                    item_id_prefix = ""
                    
                    # Mapeo de subcategorías a tipos y prefijos según la estructura del JSON
                    if subcategory_id == "torso_interior":
                        subcategory_type = "torso"
                        item_id_prefix = "torso_interior"
                    elif subcategory_id == "torso_exterior":
                        subcategory_type = "torso"
                        item_id_prefix = "vestuario_superior"
                    elif subcategory_id == "torso_accesorios":
                        subcategory_type = "torso"
                        item_id_prefix = "torso_accessory"
                    elif subcategory_id == "head_cabello":
                        subcategory_type = "headwear"
                        item_id_prefix = "headwear"
                    elif subcategory_id == "head_accesorios":
                        subcategory_type = "headwear"
                        item_id_prefix = "headwear_accessory"
                    elif subcategory_id == "head_rostro":
                        subcategory_type = "headwear"
                        item_id_prefix = "headwear_accessory"
                    
                    print(f"Buscando elementos para {subcategory_id} con subcategory_type={subcategory_type} y item_id_prefix={item_id_prefix}")
                    
                    # Recorrer todos los elementos del vestuario
                    for item_obj in vestuario_data[items_key]:
                        # Verificar si el elemento tiene next_parts
                        next_parts_key = f"next_parts_{subcategory_type}"
                        if next_parts_key in item_obj:
                            next_parts_data = item_obj[next_parts_key]
                            items_key_inner = f"items_{subcategory_type}"
                            
                            if items_key_inner in next_parts_data:
                                # Filtrar elementos según el tipo de subcategoría
                                for inner_item in next_parts_data[items_key_inner]:
                                    # Verificar si el elemento pertenece a la subcategoría deseada
                                    for key in inner_item.keys():
                                        if key.startswith(f"item_id_{item_id_prefix}"):
                                            item_id = inner_item[key]
                                            print(f"Encontrado item para {subcategory_id}: {item_id} con prefijo {item_id_prefix} en {key}")
                                            
                                            # Verificar si este elemento ya existe en la lista para evitar duplicados
                                            duplicate = False
                                            for existing_item in items:
                                                if existing_item.get("id") == item_id:
                                                    duplicate = True
                                                    print(f"Elemento duplicado detectado: {item_id}")
                                                    break
                                            
                                            if duplicate:
                                                continue
                                            
                                            # Crear datos del elemento
                                            item_data = {
                                                "id": item_id,
                                                "type": subcategory_id,
                                                "subcategory": subcategory_id,
                                                "original_data": inner_item  # Guardar datos originales
                                            }
                                            
                                            # Buscar traducción del elemento
                                            translations_key = f"translations_{vestuario_type}"
                                            if translations_key in vestuario_data and "es" in vestuario_data[translations_key]:
                                                es_translations = vestuario_data[translations_key]["es"]
                                                if "items" in es_translations and item_id in es_translations["items"]:
                                                    item_data["name"] = es_translations["items"][item_id]
                                                else:
                                                    item_data["name"] = item_id.replace('_', ' ')
                                            else:
                                                item_data["name"] = item_id.replace('_', ' ')
                                            
                                            # Agregar el elemento a la lista
                                            items.append(item_data)
        
        # Si no se encontraron elementos, registrar en consola pero no agregar ejemplos estáticos
        if not items:
            print(f"No se encontraron elementos para la subcategoría {subcategory_id} en el JSON. Verifica la estructura del archivo JSON.")
        
        return items
        
        # Verificar si ya existe una columna con este ID
        existing_column_index = next((i for i, col in enumerate(self.columns) if col["id"] == column_id), -1)
        if existing_column_index >= 0:
            print(f"Actualizando columna existente para {column_id}")
            # Actualizar la columna existente
            self.update_column(column_id, column_data)
        else:
            # Agregar una nueva columna
            print(f"Generando nueva columna para {column_id}")
            self.add_column(column_id, column_data)
        
        return True
        
    def get_subcategory_translation_by_id(self, subcategory_id):
        """Obtiene la traducción para una subcategoría específica"""
        translations = {

        }
        
        return translations.get(subcategory_id, subcategory_id)
        
    def remove_columns_after(self, index):
        """Elimina todas las columnas después del índice especificado"""
        if index < 0 or index >= len(self.columns):
            return
        
        print(f"Eliminando columnas después del índice {index}. Total columnas: {len(self.columns)}")
        
        # Eliminar columnas del layout y de las listas
        for i in range(len(self.columns) - 1, index, -1):
            if i < len(self.column_widgets):
                widget = self.column_widgets[i]
                self.columns_layout.removeWidget(widget)
                widget.setParent(None)  # Desconectar del padre
                widget.deleteLater()
                self.column_widgets.pop(i)
                print(f"Columna {i} eliminada")
            
            if i < len(self.columns):
                self.columns.pop(i)
        
        # Forzar actualización del layout
        self.columns_layout.update()
        self.columns_container.adjustSize()
    
    def clear_columns(self):
        """Limpia todas las columnas existentes"""
        for widget in self.column_widgets:
            self.columns_layout.removeWidget(widget)
            widget.deleteLater()
        
        self.column_widgets = []
        self.columns = []
    
    def get_column_title(self, column_id, column_data):
        """Obtiene el título traducido de una columna"""
        return self.get_translation(column_data, "label", column_id.replace('_', ' ').title())
    
    def get_item_translation(self, column_data, item_id, default_text):
        """Obtiene la traducción de un item"""
        translations_key = f"translations_{column_data.get('type', '')}"
        if translations_key in column_data and "es" in column_data[translations_key]:
            translations = column_data[translations_key]["es"]
            if "items" in translations and item_id in translations["items"]:
                return translations["items"][item_id]
        return default_text
    
    def get_translation(self, data, key, default_text):
        """Obtiene una traducción genérica"""
        data_type = data.get('type', '')
        translations_key = f"translations_{data_type}"
        
        if translations_key in data and "es" in data[translations_key]:
            translations = data[translations_key]["es"]
            if key in translations:
                return translations[key]
        return default_text
        
    def get_subcategory_translation(self, vestuario_data, subcategory_id):
        """Obtiene la traducción de una subcategoría"""
        translations_key = None
        for key in vestuario_data.keys():
            if key.startswith("translations_"):
                translations_key = key
                break
                
        if translations_key and "es" in vestuario_data[translations_key]:
            translations = vestuario_data[translations_key]["es"]
            if "subcategories" in translations and subcategory_id in translations["subcategories"]:
                return translations["subcategories"][subcategory_id]
        
        # Si no se encuentra traducción, devolver el ID formateado
        return subcategory_id.replace('_', ' ').title()
        
    def get_subcategory_translation(self, vestuario_data, subcategory_id):
        """Obtiene la traducción de una subcategoría"""
        translations_key = None
        for key in vestuario_data.keys():
            if key.startswith("translations_"):
                translations_key = key
                break
                
        if translations_key and "es" in vestuario_data[translations_key]:
            translations = vestuario_data[translations_key]["es"]
            if "subcategories" in translations and subcategory_id in translations["subcategories"]:
                return translations["subcategories"][subcategory_id]
        
        # Si no se encuentra traducción, devolver el ID formateado
        return subcategory_id.replace('_', ' ').title()