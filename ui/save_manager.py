from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QMessageBox, QComboBox, QLineEdit, 
    QFormLayout, QFrame, QCompleter
)
from PyQt6.QtCore import Qt, QStringListModel
from PyQt6.QtGui import QFont
import os
import json
from .new_character_dialog import NewCharacterDialog

class SaveOptionsDialog(QDialog):
    """Diálogo para seleccionar el tipo de guardado"""
    
    def __init__(self, parent=None, category_grid=None):
        super().__init__(parent)
        self.category_grid = category_grid
        self.setWindowTitle("Guardar Configuración")
        self.setModal(True)
        self.setFixedSize(450, 170)
        self.selected_option = None
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(30, 30, 30, 20)
        
        # Título
        title_label = QLabel("Guardar configuración actual")
        title_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("color: #FFFFFF; margin-bottom: 5px;")
        layout.addWidget(title_label)
        
        # Descripción
        desc_label = QLabel("¿Deseas crear un nuevo personaje o guardar como\nvariación de un personaje existente?")
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setFont(QFont("Segoe UI", 11))
        desc_label.setStyleSheet("color: #FFFFFF; line-height: 1.5; margin-bottom: 10px;")
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        layout.addSpacing(10)
        
        # Botones
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(15)
        
        # Botón Nuevo Personaje
        self.new_character_btn = QPushButton("Nuevo Personaje")
        self.new_character_btn.setFixedSize(150, 40)
        self.new_character_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        self.new_character_btn.clicked.connect(self.select_new_character)
        buttons_layout.addWidget(self.new_character_btn)
        
        # Botón Variación
        self.variation_btn = QPushButton("Variación de un personaje")
        self.variation_btn.setFixedSize(150, 40)
        self.variation_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #1565C0;
            }
        """)
        self.variation_btn.clicked.connect(self.select_variation)
        buttons_layout.addWidget(self.variation_btn)
        
        layout.addLayout(buttons_layout)
        layout.addStretch()
    
    def select_new_character(self):
        """Abre la ventana para crear nuevo personaje"""
        dialog = NewCharacterDialog(self, self.category_grid)
        
        # Conectar la señal del diálogo a la señal del category_grid
        dialog.character_saved.connect(self.category_grid.character_saved.emit)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            character_name = dialog.get_character_name()
            if character_name:
                QMessageBox.information(self, "Éxito", f"Personaje '{character_name}' creado exitosamente.")
                self.selected_option = "new_character"
                self.character_name = character_name
                self.accept()
    
    def select_variation(self):
        """Muestra el diálogo para crear variación de personaje"""
        # Obtener referencia al sidebar desde el parent
        sidebar = None
        if hasattr(self.parent, 'sidebar'):
            sidebar = self.parent.sidebar
        dialog = VariationDialog(self, sidebar, self.category_grid)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            variation_data = dialog.get_variation_data()
            if variation_data:
                self.selected_option = "variation"
                self.character_name = variation_data['character']
                self.variation_name = variation_data['variation_name']
                self.accept()
    
    def get_selected_option(self):
        """Retorna la opción seleccionada"""
        return self.selected_option

class VariationDialog(QDialog):
    """Diálogo para crear una nueva variación de personaje"""
    
    def __init__(self, parent=None, sidebar=None, category_grid=None):
        super().__init__(parent)
        self.sidebar = sidebar
        self.category_grid = category_grid 
        self.setWindowTitle("Crear Variación de Personaje")
        self.setModal(True)
        self.setFixedSize(500, 300)
        self.selected_character = None
        self.variation_name = None
        self.setup_ui()
        self.load_available_characters()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)
        character_layout = QVBoxLayout()
        character_label = QLabel("Seleccionar el personaje para esta variacion:")
        character_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        character_label.setStyleSheet("color: #FFFFFF;")
        character_layout.addWidget(character_label)
        self.character_combo = QComboBox()
        self.character_combo.setEditable(True)
        self.character_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.character_combo.setFixedHeight(35)
        self.completer = QCompleter()
        self.completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.character_combo.setCompleter(self.completer)
        self.character_combo.setStyleSheet("""
            QComboBox {
                background-color: #3a3a3a;
                border: 2px solid #555;
                border-radius: 6px;
                padding: 5px 10px;
                color: #ffffff;
                font-size: 12px;
            }
            QComboBox:focus {
                border-color: #4a90e2;
            }
            QComboBox::drop-down {
                border: none;
                width: 25px;
                background-color: #4a4a4a;
                border-top-right-radius: 6px;
                border-bottom-right-radius: 6px;
            }
            QComboBox::drop-down:hover {
                background-color: #5a5a5a;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 6px solid transparent;
                border-right: 6px solid transparent;
                border-top: 8px solid #ffffff;
                margin: 0px;
            }
            QComboBox::down-arrow:hover {
                border-top-color: #4a90e2;
            }
            QComboBox QAbstractItemView {
                background-color: #3a3a3a;
                border: 1px solid #555;
                selection-background-color: #4a90e2;
                color: #ffffff;
            }
        """)
        self.character_combo.currentTextChanged.connect(self.on_character_text_changed)
        self.character_combo.activated.connect(self.on_character_selected)
        character_layout.addWidget(self.character_combo)
        layout.addLayout(character_layout)
        variation_layout = QVBoxLayout()
        variation_label = QLabel("Nombre de variación:")
        variation_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        variation_label.setStyleSheet("color: #FFFFFF;")
        variation_layout.addWidget(variation_label)
        self.variation_input = QLineEdit()
        self.variation_input.setFixedHeight(35)
        self.variation_input.setStyleSheet("""
            QLineEdit {
                background-color: #3a3a3a;
                border: 2px solid #555;
                border-radius: 6px;
                padding: 5px 10px;
                color: #ffffff;
                font-size: 12px;
            }
            QLineEdit:focus {
                border-color: #4a90e2;
            }
        """)
        variation_layout.addWidget(self.variation_input)
        layout.addLayout(variation_layout)
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)
        self.create_btn = QPushButton("Crear Variación")
        self.create_btn.setFixedSize(130, 35)
        self.create_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #1565C0;
            }
            QPushButton:disabled {
                background-color: #666;
                color: #aaa;
            }
        """)
        self.create_btn.clicked.connect(self.create_variation)
        self.create_btn.setEnabled(False)
        
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.create_btn)
        
        layout.addLayout(buttons_layout)
    
    def detect_current_character(self):
        """Intenta detectar y preseleccionar el personaje actual"""
        try:
            pass
        except Exception as e:
            print(f"Error detectando personaje actual: {e}")
    
    def load_available_characters(self):
        """Carga los personajes disponibles en el ComboBox"""
        try:
            characters_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "characters")
            
            if not os.path.exists(characters_dir):
                return
            
            characters = []
            
            for item in os.listdir(characters_dir):
                item_path = os.path.join(characters_dir, item)
                if os.path.isdir(item_path):
                    # Buscar archivo JSON con el mismo nombre que la carpeta
                    json_filename = f"{item}.json"
                    character_file = os.path.join(item_path, json_filename)
                    if os.path.exists(character_file):
                        try:
                            with open(character_file, 'r', encoding='utf-8') as f:
                                character_data = json.load(f)
                                if "metadata" in character_data and "character_name" in character_data["metadata"]:
                                    character_name = character_data["metadata"]["character_name"]
                                    characters.append(character_name)
                        except Exception as e:
                            print(f"Error cargando personaje {item}: {e}")
            
            characters.sort()
            
            # Limpiar y agregar personajes
            self.character_combo.clear()
            for character in characters:
                self.character_combo.addItem(character)
            
            # Configurar el completer con la lista de personajes
            from PyQt6.QtCore import QStringListModel
            model = QStringListModel(characters)
            self.completer.setModel(model)
            
            # Establecer placeholder text en lugar de un item
            self.character_combo.setCurrentText("")
            self.character_combo.lineEdit().setPlaceholderText("🔍 Buscar personaje...")
            
            self.detect_current_character()
            
        except Exception as e:
            print(f"Error cargando personajes: {e}")
    
    def on_character_text_changed(self, text):
        """Maneja cambios en el texto del selector"""
        # Solo procesar si el texto no está vacío
        if text and text.strip():
            index = self.character_combo.findText(text, Qt.MatchFlag.MatchExactly)
            if index >= 0:
                self.handle_character_selection(text)
        else:
            self.selected_character = None
            self.variation_input.clear()
            self.create_btn.setEnabled(False)
    
    def on_character_selected(self, index):
        """Maneja la selección de personaje por índice (desde activated signal)"""
        character_name = self.character_combo.itemText(index)
        self.handle_character_selection(character_name)
    
    def handle_character_selection(self, character_name):
        """Maneja la selección de personaje y genera nombre de variación"""
        if character_name and character_name.strip():
            self.selected_character = character_name
            self.generate_variation_name(character_name)
            self.create_btn.setEnabled(True)
            self.character_combo.setCurrentText(character_name)
        else:
            self.selected_character = None
            self.variation_input.clear()
            self.create_btn.setEnabled(False)
    
    def generate_variation_name(self, character_name):
        """Genera automáticamente el nombre de la variación"""
        try:
            variations_manager = None
            if self.sidebar and hasattr(self.sidebar, 'variations_manager'):
                variations_manager = self.sidebar.variations_manager
            
            if not variations_manager:
                from logic.variations_manager import VariationsManager
                variations_manager = VariationsManager()
            
            character_data = variations_manager.get_character_variations(character_name)
            existing_variations = character_data.get("variations", {})
            
            base_name = f"{character_name}_var"
            counter = 1
            
            while f"{base_name}{counter}" in existing_variations:
                counter += 1
            
            variation_name = f"{base_name}{counter}"
            self.variation_input.setText(variation_name)
            
        except Exception as e:
            self.variation_input.setText(f"{character_name}_var1")
            print(f"Error generando nombre de variación: {e}")
    
    def create_variation(self):
        """Crea la variación y cierra el diálogo"""
        character = self.selected_character
        variation = self.variation_input.text().strip()
        
        if not character or not variation:
            QMessageBox.warning(self, "Error", "Selecciona un personaje y especifica un nombre de variación.")
            return
        
        if not variation.replace('_', '').replace('-', '').isalnum():
            QMessageBox.warning(self, "Error", "El nombre de variación solo puede contener letras, números, guiones y guiones bajos.")
            return
        
        try:
            # Capturar los valores actuales de las categorías
            current_values = {}
            if self.category_grid:
                current_values = self.category_grid.get_current_values()
                print(f"Valores capturados: {len(current_values)} categorías")
            
            # Acceder al variations_manager desde el sidebar
            variations_manager = None
            if self.sidebar and hasattr(self.sidebar, 'variations_manager'):
                variations_manager = self.sidebar.variations_manager
            
            if not variations_manager:
                # Importar y crear una instancia si no está disponible
                from logic.variations_manager import VariationsManager
                variations_manager = VariationsManager()
            
            # Verificar si la variación ya existe
            existing_variations = variations_manager.get_character_variations(character)
            if variation in existing_variations.get("variations", {}):
                reply = QMessageBox.question(
                    self, "Variación existente",
                    f"Ya existe una variación llamada '{variation}' para {character}.\n¿Deseas sobrescribirla?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.No:
                    return
            
            # Guardar la variación
            success = variations_manager.save_variation(
                character_name=character,
                variation_name=variation,
                categories=current_values,
                description=f"Variación {variation} para {character}",
                tags=[],
                notes="Creada desde la aplicación"
            )
            
            if success:
                # Emitir señal de variación guardada si está disponible
                if self.sidebar and hasattr(self.sidebar, 'variations_panel'):
                    print("🔄 Emitiendo señal variation_saved...")
                    self.sidebar.variations_panel.variation_saved.emit(character, variation)
                    print("🔄 Forzando actualización directa...")
                    self.sidebar.variations_panel.load_variations()
                    print("✅ Actualización directa completada")
                    print(f"✅ Señal emitida para {character} - {variation}")
                
                QMessageBox.information(
                    self, "Éxito", 
                    f"Variación '{variation}' creada exitosamente para {character}\n"
                    f"Categorías guardadas: {len(current_values)}"
                )
                
                
                self.selected_character = character
                self.variation_name = variation
                self.accept()
                
            else:
                QMessageBox.warning(
                    self, "Error", 
                    "No se pudo guardar la variación. Revisa los logs para más detalles."
                )
                
        except Exception as e:
            QMessageBox.critical(
                self, "Error", 
                f"Error al crear la variación: {str(e)}"
            )
            print(f"Error detallado: {e}")
    
    def get_variation_data(self):
        """Retorna los datos de la variación creada"""
        return {
            'character': self.selected_character,
            'variation_name': self.variation_name
        }

class SaveManager:
    """Clase para manejar todas las funcionalidades de guardado"""
    
    def __init__(self, parent=None, category_grid=None):
        self.parent = parent
        self.category_grid = category_grid
    
    def show_save_options(self):
        """Muestra la ventana de opciones de guardado"""
        dialog = SaveOptionsDialog(self.parent, self.category_grid)
        dialog.exec()

    
    def on_changes_updated(self):
        """Maneja cuando se actualizan los cambios detectados"""
        print("Cambios actualizados en VariationDialog")
        changes_data = self.changes_widget.get_changes_data()
        if changes_data:
            print(f"Se detectaron cambios en {len(changes_data)} categorías")