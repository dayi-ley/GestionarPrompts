import os
import json
import re
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
    QLineEdit, QScrollArea, QPushButton, QToolButton, QInputDialog, QMessageBox,
    QDialog, QLabel, QTextEdit
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from .components import CategoryCard, AddCategoryCard
from .utils.category_utils import (
    load_categories_and_tags, 
    normalize_category,
    update_categories_json,
    update_tags_json,
    rename_category_in_files,
    DEFAULT_CARD_COLOR,
    save_categories_order,
    load_category_colors,
    rename_category_color_key
)
from .save_manager import SaveManager

class CategoryGridFrame(QWidget):
    prompt_updated = pyqtSignal(str)
    category_value_changed = pyqtSignal(str, str, str)  # (category_name, old_value, new_value)
    character_saved = pyqtSignal(str)  # Nueva señal: (character_name)
    
    def __init__(self, prompt_generator, main_window=None):
        super().__init__()
        self.prompt_generator = prompt_generator
        self.main_window = main_window  # ← AGREGAR REFERENCIA AL MAIN_WINDOW
        self.cards = []
        self.previous_values = {}
        self.previous_values_snapshot = {}
        
        # Inicializar SaveManager con referencia a self
        self.save_manager = SaveManager(self, self)
        
        self.setup_ui()
        self.create_cards()

    def setup_ui(self):
        """Configura la interfaz del grid"""
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(16, 0, 16, 16)
        self.main_layout.setSpacing(0)
        
        # --- Layout horizontal para buscador y botones ---
        search_layout = QHBoxLayout()
        search_layout.setSpacing(8)
        
        # Botón/ícono para limpiar todas las categorías (a la izquierda del filtro)
        self.clear_btn = QToolButton()
        self.clear_btn.setText("🧹")
        self.clear_btn.setToolTip("Limpiar todas las categorías")
        self.clear_btn.setFixedSize(28, 28)
        self.clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clear_btn.setStyleSheet(
            """
            QToolButton {
                background-color: #404040;
                color: #ffffff;
                border-radius: 6px;
                padding: 2px;
            }
            QToolButton:hover {
                background-color: #6366f1;
            }
            """
        )
        self.clear_btn.clicked.connect(self.clear_all_values)
        search_layout.addWidget(self.clear_btn)
        # Separación extra para evitar clics accidentales entre limpieza y buscador
        search_layout.addSpacing(10)
        
        # Botón Reordenar al lado izquierdo del buscador
        self.reorder_btn = QToolButton()
        self.reorder_btn.setText("↕️")
        self.reorder_btn.setToolTip("Activar modo reordenar categorías")
        self.reorder_btn.setCheckable(True)
        self.reorder_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.reorder_btn.setFixedHeight(28)
        self.reorder_btn.setStyleSheet(
            """
            QToolButton { background-color:#404040; color:#fff; border-radius:6px; padding:2px 8px; }
            QToolButton:hover { background-color:#6366f1; }
            QToolButton:checked { background-color:#00A36C; }
            """
        )
        self.reorder_btn.toggled.connect(self.toggle_reorder_mode)
        search_layout.addWidget(self.reorder_btn)
        search_layout.addSpacing(10)
        
        # Buscador
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Buscar categoría...")
        # Hacer el buscador más ancho pero controlado
        self.search_box.setMinimumWidth(360)
        self.search_box.setMaximumWidth(600)
        self.search_box.textChanged.connect(self.filter_cards)
        search_layout.addWidget(self.search_box)
        # Empujar los botones a la derecha
        search_layout.addStretch(1)
        
        # Botón para importar datos
        self.import_data_btn = QPushButton("Importar Datos")
        from PyQt6.QtWidgets import QSizePolicy
        self.import_data_btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.import_data_btn.clicked.connect(self.import_data_dialog)
        # Reducir padding para que sea más angosto
        self.import_data_btn.setStyleSheet("QPushButton { padding: 4px 12px; }")
        search_layout.addWidget(self.import_data_btn)
        
        # Nuevo botón para guardar
        self.save_btn = QPushButton("Guardar")
        self.save_btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.save_btn.clicked.connect(self.show_save_options)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #446879;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 4px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #acc8d7;
            }
            QPushButton:pressed {
                background-color: #E65100;
            }
        """)
        search_layout.addWidget(self.save_btn)
        
        self.main_layout.addLayout(search_layout)

        # Scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Widget contenedor para el grid
        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setSpacing(8)
        
        # Hacer el grid responsivo
        self.grid_layout.setColumnStretch(0, 1)
        self.grid_layout.setColumnStretch(1, 1)
        self.grid_layout.setColumnStretch(2, 1)
        
        self.scroll_area.setWidget(self.grid_widget)
        self.main_layout.addWidget(self.scroll_area)
        
    def setup_styles(self):
        """Configura los estilos del grid"""
        self.setStyleSheet("""
            QLineEdit {
                background-color: #1a1a1a;
                border: 1px solid #404040;
                border-radius: 6px;
                color: #e0e0e0;
                padding: 8px;
                font-size: 12px;
                margin-bottom: 8px;
            }
            QLineEdit:focus {
                border: 1px solid #6366f1;
            }
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QPushButton {
                background-color: #6366f1;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 12px;
                margin-top: 8px;
            }
            QPushButton:hover {
                background-color: #4f46e5;
            }
        """)
    def get_category_group_color(self, category_name):
        """Determina el color del grupo por palabras clave en el nombre."""
        name = category_name.lower()
        rules = [
            (['loras estilos artistico', 'loras detalles mejoras', 'loras modelos especificos', 'loras personaje', 'loras '], '#4c0027'),
            (['personaje'], '#d09305'),
            (['cabello forma', 'cabello color', 'cabello accesorios', 'cabello '], '#4e635a'),
            (['vestuario', 'ropa interior', 'lenceria', 'lencería', 'prendas superiores', 'prendas inferiores'], '#553c9a'),
            (['pose actitud global', 'pose brazos', 'pose piernas', 'pose ', 'orientacion personaje', 'orientación personaje'], '#38a169'),
            (['expresion facial', 'expresión facial'], '#38a169'),
            (['rasgo fisico', 'rasgo_fisico'], '#dd6b20'),
            (['objetos'], '#319795'),
        ]
        for keywords, color in rules:
            for kw in keywords:
                if name.startswith(kw) or kw in name:
                    return color
        return "#252525"

    def create_cards(self):
        """Crea las tarjetas de categorías"""
        categories = load_categories_and_tags()
        colors_map = load_category_colors()
        
        row, col = 0, 0
        # Reiniciar referencia de tarjetas antes de poblar
        self.cards = []
        for category in categories:
            # Preferir color manual persistido sobre color grupal
            snake = category["name"].lower().replace(" ", "_")
            manual_color = colors_map.get(snake)
            group_color = manual_color or self.get_category_group_color(category["name"]) 
            
            card = CategoryCard(
                category["name"], 
                category["icon"], 
                category["tags"], 
                self.prompt_generator,
                bg_color=group_color  # ¡Agregar el color grupal!
            )
            card.request_rename.connect(self.handle_category_rename)
            card.value_changed.connect(self.update_prompt)
            # Conectar señales de reordenar hacia el grid
            if hasattr(card, 'request_move_up'):
                card.request_move_up.connect(lambda name=category["name"]: self.move_card(name, -1))
            if hasattr(card, 'request_move_down'):
                card.request_move_down.connect(lambda name=category["name"]: self.move_card(name, 1))
            
            self.cards.append(card)
            self.grid_layout.addWidget(card, row, col)
            
            col += 1
            if col >= 3:
                col = 0
                row += 1
        
        # Tarjeta para añadir nueva categoría
        self.add_card = AddCategoryCard(self.add_custom_category)
        self.grid_layout.addWidget(self.add_card, row, col)

    def filter_cards(self, text):
        """Filtra las tarjetas según el texto de búsqueda"""
        text = text.lower()
        for card in self.cards:
            if hasattr(card, 'category_name'):
                visible = text in card.category_name.lower()
                card.setVisible(visible)
    
    def clear_all_values(self):
        """Limpia los valores de todas las tarjetas de categorías."""
        for card in self.cards:
            # Respetar bloqueo de tarjeta
            if hasattr(card, 'is_locked') and card.is_locked:
                continue
            if hasattr(card, 'clear_value'):
                card.clear_value()
        # Actualizar prompt y señales tras limpiar
        self.update_prompt()

    def toggle_reorder_mode(self, enabled: bool):
        """Activa o desactiva el modo reordenar mostrando controles en cada tarjeta."""
        for card in self.cards:
            if hasattr(card, 'set_reorder_mode'):
                card.set_reorder_mode(enabled)

    def move_card(self, category_display_name: str, delta: int):
        """Mueve una tarjeta arriba/abajo y reconstruye el grid. También guarda el nuevo orden."""
        # Buscar índice actual de la tarjeta
        idx = None
        for i, card in enumerate(self.cards):
            if getattr(card, 'category_name', '') == category_display_name:
                idx = i
                break
        if idx is None:
            return
        new_idx = max(0, min(len(self.cards) - 1, idx + delta))
        if new_idx == idx:
            return
        # Reordenar lista interna
        card = self.cards.pop(idx)
        self.cards.insert(new_idx, card)
        # Re-flujo visual del grid
        self.reflow_cards()
        # Persistir nuevo orden en categories.json
        try:
            snake_order = [c.category_name.lower().replace(" ", "_") for c in self.cards]
            save_categories_order(snake_order)
        except Exception:
            pass

    def reflow_cards(self):
        """Reconstruye la cuadrícula según el orden actual de self.cards."""
        # Vaciar el layout sin destruir los widgets
        try:
            while self.grid_layout.count():
                item = self.grid_layout.takeAt(0)
                w = item.widget()
                if w is not None:
                    w.setParent(self.grid_widget)
        except Exception:
            pass
        # Reagregar según orden
        row, col = 0, 0
        for card in self.cards:
            self.grid_layout.addWidget(card, row, col)
            col += 1
            if col >= 3:
                col = 0
                row += 1
        # Agregar la tarjeta de añadir al final
        if hasattr(self, 'add_card') and self.add_card is not None:
            self.grid_layout.addWidget(self.add_card, row, col)

    def update_prompt(self):
        """Actualiza el prompt cuando cambian los valores de las tarjetas"""
        # Crear mapeo inverso: formato capitalizado -> formato snake_case
        with open("c:\\Users\\LENOVO\\Desktop\\AppPrompts\\data\\categories.json", "r", encoding="utf-8") as f:
            original_categories = json.load(f)["categorias"]
        
        category_reverse_mapping = {}
        for orig_cat in original_categories:
            formatted_cat = orig_cat.replace("_", " ").capitalize()
            category_reverse_mapping[formatted_cat] = orig_cat
        
        # Detectar qué categoría cambió y notificar al sidebar
        current_values = self.get_current_values()
        
        for category_name, current_value in current_values.items():
            previous_value = self.previous_values.get(category_name, "")
            if previous_value != current_value:
                # Emitir señal de cambio específico
                self.category_value_changed.emit(category_name, previous_value, current_value)
                
                # Actualizar el prompt_generator con el nombre correcto
                snake_case_name = category_reverse_mapping.get(category_name, category_name.lower().replace(" ", "_"))
                if self.prompt_generator:
                    self.prompt_generator.update_category(snake_case_name, current_value)
        
        # Actualizar valores anteriores
        self.previous_values = current_values.copy()
        
        # Usar el prompt_generator en lugar de generar el prompt manualmente
        prompt = self.prompt_generator.generate_prompt()
        self.prompt_updated.emit(prompt)
    
    def get_current_values(self):
        """Obtiene los valores actuales de todas las categorías"""
        current_values = {}
        for card in self.cards:
            if hasattr(card, 'category_name') and hasattr(card, 'input_field'):
                current_values[card.category_name] = card.input_field.text()
        return current_values
    
    def set_previous_values_snapshot(self, values):
        """Establece el snapshot de valores previos"""

        self.previous_values_snapshot = values

    def handle_category_rename(self, old_name, new_name):
        """Maneja el renombrado de categorías"""
        try:
            rename_category_in_files(old_name, new_name)
            # Migrar color si existe en el almacenamiento
            try:
                rename_category_color_key(old_name, new_name)
            except Exception:
                pass
            QMessageBox.information(self, "Éxito", f"Categoría renombrada de '{old_name}' a '{new_name}'")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error al renombrar categoría: {str(e)}")

    def add_custom_category(self):
        """Añade una nueva categoría personalizada"""
        name, ok = QInputDialog.getText(self, "Nueva Categoría", "Nombre de la categoría:")
        if ok and name.strip():
            try:
                normalized_name = normalize_category(name.strip())
                update_categories_json(normalized_name)
                update_tags_json(normalized_name, [])
                
                # Recrear las tarjetas
                self.clear_grid()
                self.create_cards()
                
                QMessageBox.information(self, "Éxito", f"Categoría '{name}' añadida correctamente")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Error al añadir categoría: {str(e)}")

    def clear_grid(self):
        """Limpia el grid de tarjetas"""
        for card in self.cards:
            card.setParent(None)
        self.cards.clear()
        
        # Limpiar el grid layout
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)

    def show_save_options(self):
        """Muestra las opciones de guardado"""
        # Verificar que hay datos para guardar
        current_values = self.get_current_values()
        
        # Contar cuántas categorías tienen datos
        categories_with_data = 0
        for category_name, value in current_values.items():
            if value and value.strip():  # Si el valor no está vacío
                categories_with_data += 1
        
        # Si no hay datos en ninguna categoría, mostrar mensaje de advertencia
        if categories_with_data == 0:
            QMessageBox.warning(
                self, 
                "Sin datos para guardar", 
                "No se puede guardar porque no hay datos en ninguna categoría.\n\n"
                "Por favor, ingresa algunos valores en las categorías antes de guardar."
            )
            return
        
        # Si hay al menos una categoría con datos, proceder con el guardado
        self.save_manager.show_save_options()

    
    
    def save_as_new_character(self, variation_data):
        """Guarda los valores actuales como un nuevo personaje"""
        # Solicitar nombre del personaje
        name, ok = QInputDialog.getText(
            self, 
            "Nuevo Personaje", 
            "Ingresa el nombre del personaje:"
        )
        
        if not ok or not name.strip():
            return
        
        name = name.strip()
        
        # Verificar si ya existe
        characters_dir = "data/characters"
        if not os.path.exists(characters_dir):
            os.makedirs(characters_dir)
        
        character_file = os.path.join(characters_dir, f"{name}.json")
        if os.path.exists(character_file):
            reply = QMessageBox.question(
                self,
                "Personaje existente",
                f"El personaje '{name}' ya existe. ¿Deseas sobrescribirlo?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return
        
        try:
            # Guardar archivo del personaje
            with open(character_file, "w", encoding="utf-8") as f:
                json.dump(variation_data, f, ensure_ascii=False, indent=2)
            
            # Emitir señal para actualizar el dropdown de personajes
            self.character_saved.emit(name)
            
            QMessageBox.information(
                self, 
                "Éxito", 
                f"Personaje '{name}' guardado exitosamente."
            )
            
        except Exception as e:
            QMessageBox.critical(
                self, 
                "Error", 
                f"Error al guardar el personaje: {str(e)}"
            )
    
    def import_data_dialog(self):
        """Muestra el diálogo para importar datos"""
        dialog = ImportDataDialog(self)
        if dialog.exec():
            imported_data = dialog.get_imported_data()
            if imported_data:
                self.load_imported_data(imported_data)
    
    def load_imported_data(self, data):
        """Carga los datos importados en las tarjetas"""
        if not data:
            return
            
        loaded_count = 0
        for card in self.cards:
            if hasattr(card, 'category_name') and hasattr(card, 'input_field'):
                # Respetar bloqueo de tarjeta
                if hasattr(card, 'is_locked') and card.is_locked:
                    continue
                    
                category_name = card.category_name.lower().replace(' ', '_')
                if category_name in data:
                    card.input_field.setText(data[category_name])
                    loaded_count += 1
        
        self.update_prompt()
        
        if loaded_count > 0:
            QMessageBox.information(
                self, 
                "Datos importados", 
                f"Se han cargado {loaded_count} categorías."
            )

    def apply_character_defaults(self, character_data):
        """Aplica los valores por defecto de un personaje a las tarjetas"""
        if not character_data:
            return
            
        loaded_count = 0
        for card in self.cards:
            if hasattr(card, 'category_name') and hasattr(card, 'input_field'):
                # Respetar bloqueo de tarjeta
                if hasattr(card, 'is_locked') and card.is_locked:
                    continue

                # Normalizar el nombre de la categoría para buscar en los datos
                category_name = card.category_name.lower().replace(' ', '_')
                
                if category_name in character_data:
                    card.input_field.setText(character_data[category_name])
                    loaded_count += 1
        
        # Actualizar el prompt después de cargar los datos
        self.update_prompt()
        
        # Opcional: mostrar mensaje de confirmación
        if loaded_count > 0:
            QMessageBox.information(
                self, 
                "Personaje cargado", 
                f"Se han cargado {loaded_count} categorías del personaje."
            )

    def apply_variation(self, variation_data):
        """Aplica los valores de una variación a las tarjetas de categoría"""
        if not variation_data:
            return
        
        # Los datos de variación tienen la estructura: {'categories': {...}, 'name': '...', etc.}
        categories_data = variation_data.get('categories', {})
        
        if not categories_data:
            return
        
        loaded_count = 0
        for card in self.cards:
            if hasattr(card, 'category_name') and hasattr(card, 'input_field'):
                # Respetar bloqueo de tarjeta
                if hasattr(card, 'is_locked') and card.is_locked:
                    continue

                # Buscar el valor de la categoría en los datos de la variación
                category_name = card.category_name
                
                if category_name in categories_data:
                    # Aplicar el valor a la tarjeta
                    card.input_field.setText(categories_data[category_name])
                    loaded_count += 1
        
        # Actualizar el prompt después de cargar los datos
        self.update_prompt()
        
        # Mostrar mensaje de confirmación
        if loaded_count > 0:
            variation_name = variation_data.get('name', 'Variación')
            QMessageBox.information(
                self, 
                "Variación cargada", 
                f"Se han cargado {loaded_count} categorías de la variación '{variation_name}'."
            )

    def apply_preset(self, preset_data):
        """Aplica un preset a las categorías, limpiando solo las categorías seleccionadas"""
        if not preset_data:
            return
        
        # Verificar si preset_data ya contiene las categorías directamente
        # o si tiene la estructura anidada
        if 'categories' in preset_data:
            # preset_data tiene estructura anidada
            preset_categories = preset_data.get('categories', {})
            preset_name = preset_data.get('name', preset_data.get('preset_display_name', '.'))
        else:
            # Las categorías están directamente en preset_data
            preset_categories = preset_data
            # Usar el nombre pasado desde presets_panel o el del preset_data
            preset_name = preset_data.get('preset_display_name', preset_data.get('name', 'Preset'))
        
        print(f"DEBUG: preset_categories = {preset_categories}")  # DEBUG
        
        if not preset_categories:
            QMessageBox.information(self, "Preset vacío", "El preset no contiene categorías.")
            return
        
        print(f"DEBUG: Número de cards disponibles: {len(self.cards)}")  # DEBUG
        
        applied_count = 0
        
        # Aplicar valores del preset a las categorías correspondientes
        for i, card in enumerate(self.cards):
            if hasattr(card, 'category_name') and hasattr(card, 'input_field'):
                # Respetar bloqueo de tarjeta
                if hasattr(card, 'is_locked') and card.is_locked:
                    continue
                    
                card_name = card.category_name
                print(f"DEBUG: Card {i} - nombre: '{card_name}'")  # DEBUG
                
                # Buscar coincidencia exacta primero
                if card_name in preset_categories:
                    preset_value = preset_categories[card_name]
                    print(f"DEBUG: Coincidencia exacta encontrada para '{card_name}' -> '{preset_value}'")  # DEBUG
                    card.input_field.setText(preset_value)
                    applied_count += 1
                else:
                    # Buscar coincidencia normalizada (sin espacios, minúsculas)
                    card_normalized = card_name.lower().replace(" ", "_")
                    print(f"DEBUG: Buscando coincidencia normalizada para '{card_name}' -> '{card_normalized}'")  # DEBUG
                    
                    found_match = False
                    for preset_key, preset_value in preset_categories.items():
                        preset_normalized = preset_key.lower().replace(" ", "_")
                        print(f"DEBUG: Comparando '{card_normalized}' con '{preset_normalized}'")  # DEBUG
                        
                        if card_normalized == preset_normalized:
                            print(f"DEBUG: Coincidencia normalizada encontrada: '{card_name}' -> '{preset_value}'")  # DEBUG
                            card.input_field.setText(preset_value)
                            applied_count += 1
                            found_match = True
                            break
                    
                    if not found_match:
                        print(f"DEBUG: No se encontró coincidencia para '{card_name}'")  # DEBUG
            else:
                print(f"DEBUG: Card {i} no tiene category_name o input_field")  # DEBUG
        
        print(f"DEBUG: Total aplicado: {applied_count} de {len(preset_categories)}")  # DEBUG
        
        # Actualizar el prompt después de aplicar los valores
        self.update_prompt()
        
        # Mostrar mensaje de confirmación
        if applied_count > 0:
            QMessageBox.information(
                self, 
                "Preset aplicado", 
                f"Se ha aplicado el preset '{preset_name}' correctamente.\n\n"
                f"Categorías actualizadas: {applied_count} de {len(preset_categories)}"
            )
        else:
            QMessageBox.warning(
                self, 
                "Sin coincidencias", 
                f"No se encontraron categorías coincidentes para el preset '{preset_name}'.\n\n"
                f"Verifica que las categorías del preset existan en la aplicación."
            )

    def set_category_value(self, category_name, value):
        """
        Establece el valor de una categoría específica.
        Retorna True si tuvo éxito, False si la categoría no existe o está bloqueada.
        """
        category_normalized = category_name.lower().replace(" ", "_")
        
        for card in self.cards:
            if hasattr(card, 'category_name') and hasattr(card, 'input_field'):
                card_cat_normalized = card.category_name.lower().replace(" ", "_")
                
                if card_cat_normalized == category_normalized:
                    # Verificar si está bloqueada
                    if hasattr(card, 'is_locked') and card.is_locked:
                        return False
                    
                    card.input_field.setText(value)
                    self.update_prompt()
                    return True
        
        return False

class ImportDataDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Importar Datos")
        self.setModal(True)
        self.setFixedSize(600, 400)
        self.imported_data = None
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Instrucciones
        instructions = QLabel("Pega aquí los datos del personaje (formato: categoría: valor):")
        layout.addWidget(instructions)
        
        # Área de texto para pegar datos
        self.text_area = QTextEdit()
        self.text_area.setPlaceholderText('Ejemplo:\n\nangulo: ((low angle)),\ncalidad_tecnica: masterpiece, best quality,\n ...\n')
        layout.addWidget(self.text_area)
        
        # Botones
        button_layout = QHBoxLayout()
        
        validate_btn = QPushButton("Validar y Cargar")
        validate_btn.clicked.connect(self.validate_and_load)
        button_layout.addWidget(validate_btn)
        
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
    
    def validate_and_load(self):
        """Valida y procesa los datos ingresados"""
        text = self.text_area.toPlainText().strip()
        
        # 1. Validar que hay contenido
        if not text:
            QMessageBox.warning(self, "Sin datos", "No hay datos para validar o cargar.\n\nPor favor ingresa algunos datos en el área de texto.")
            return
        
        try:
            # 2. Procesar el texto línea por línea
            lines = text.split('\n')
            mapped_data = {}
            categories_with_values = []
            categories_empty = []
            
            # Obtener todas las categorías disponibles del sistema
            from .utils.category_utils import load_categories_and_tags
            all_categories = load_categories_and_tags()
            system_categories = [cat["name"].lower().replace(" ", "_") for cat in all_categories]
            
            for line in lines:
                line = line.strip()
                if ':' in line:
                    parts = line.split(':', 1)
                    if len(parts) == 2:
                        category = parts[0].strip().lower().replace(" ", "_")
                        value = parts[1].strip()
                        
                        # 3. Validar y agregar coma al final si no la tiene
                        if value and not value.endswith(','):
                            value = value + ','
                        
                        mapped_data[category] = value
                        
                        # Clasificar categorías con y sin valores
                        if value and value.strip() and value.strip() != ',':
                            categories_with_values.append(category)
                        else:
                            categories_empty.append(category)
            
            
            if not mapped_data:
                QMessageBox.warning(self, "Error", "No se encontraron datos válidos en el formato esperado.\n\nFormato: categoria: valor")
                return
            
            # 5. Mostrar información sobre categorías vacías
            if categories_empty:
                empty_list = "\n• ".join(categories_empty)
                message = f"Se detectaron {len(categories_empty)} categorías sin valores:\n\n• {empty_list}\n\n"
                message += f"Categorías con datos: {len(categories_with_values)}\n"
                message += "¿Deseas continuar con la carga?"
                
                reply = QMessageBox.question(
                    self, 
                    "Categorías vacías detectadas", 
                    message,
                    QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
                    QMessageBox.StandardButton.Ok
                )
                
                if reply == QMessageBox.StandardButton.Cancel:
                    return
            
            # 6. Si todo está bien, proceder con la carga
            self.imported_data = mapped_data
            
            success_message = f"Datos validados correctamente.\n\n"
            success_message += f"• Categorías con valores: {len(categories_with_values)}\n"
            success_message += f"• Categorías vacías: {len(categories_empty)}\n"
            success_message += f"• Total de categorías: {len(mapped_data)}"
            
            QMessageBox.information(self, "Validación exitosa", success_message)
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error inesperado durante la validación: {str(e)}")
    
    def get_imported_data(self):
        """Retorna los datos importados"""
        return self.imported_data


