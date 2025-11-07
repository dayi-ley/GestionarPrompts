from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QComboBox, QFrame, QSizePolicy, QTabWidget,
                             QListWidget, QListWidgetItem, QLineEdit)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QPalette, QColor
from ui.variations_panel import VariationsPanel
from ui.presets_panel import PresetsPanel
from ui.sugeprompt_panel import SugePromptPanel  # ← NUEVA IMPORTACIÓN
from logic.variations_manager import VariationsManager
import os
import json
from datetime import datetime

class SidebarFrame(QFrame):
    character_defaults_selected = pyqtSignal(dict)
    variation_applied = pyqtSignal(dict)
    
    def __init__(self, prompt_generator, main_window=None):
        super().__init__()
        self.prompt_generator = prompt_generator
        self.main_window = main_window  # ← Agregar referencia al MainWindow
        self.is_collapsed = False
        self.expanded_width = 280
        self.collapsed_width = 60
        
        # Inicializar el manager de variaciones
        self.variations_manager = VariationsManager()
        
        # Sistema de tracking de cambios
        self.original_values_snapshot = {}
        self.changes_tracker = {}
        
        self.setup_ui()
        self.setup_styles()
        self.setup_data()
        self.connect_variation_signals()

    # En el método setup_ui(), después de la pestaña de Variaciones:
    def setup_ui(self):
        """Configura la interfaz del sidebar"""
        self.setFixedWidth(self.expanded_width)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        
        # Layout principal
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # Header con botón de colapsar
        header_layout = QHBoxLayout()
        
        self.header_label = QLabel("AI Prompt Studio")
        self.header_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        header_layout.addWidget(self.header_label)
        
        self.toggle_button = QPushButton("◀")
        self.toggle_button.setFixedSize(30, 25)
        self.toggle_button.clicked.connect(self.toggle_sidebar)
        header_layout.addWidget(self.toggle_button)
        
        layout.addLayout(header_layout)
        
        # Subtítulo
        self.subtitle_label = QLabel("Generador de Prompts IA")
        self.subtitle_label.setFont(QFont("Segoe UI", 10))
        self.subtitle_label.setStyleSheet("color: #a0a0a0;")
        layout.addWidget(self.subtitle_label)
        
        # Contenedor para el contenido con pestañas
        self.content_widget = QWidget()
        content_layout = QVBoxLayout(self.content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(8)
        
        # Widget de pestañas
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.TabPosition.North)
        self.tab_widget.setUsesScrollButtons(False)  # Desactiva scroll buttons
        self.tab_widget.setElideMode(Qt.TextElideMode.ElideRight)  # Trunca texto si es necesario
        
        # Aplicar estilo para hacer las pestañas más pequeñas
        self.tab_widget.setStyleSheet("""
            QTabWidget::tab-bar {
                alignment: center;
            }
            QTabBar::tab {
                background-color: #28104e;
                border-bottom-color: #C2C7CB;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                min-width: 60px;
                max-width: 80px;
                padding: 4px 8px;
                font-size: 10px;  /* ← Letra más pequeña */
                font-weight: normal;
            }
            QTabBar::tab:selected {
                background-color: #9854cb;
                border-bottom-color: #ffffff;
            }
            QTabBar::tab:hover {
                background-color: #6437a0;
            }
        """)
        
        # Pestaña de Personajes
        self.character_tab = QWidget()
        self.setup_character_tab()
        self.tab_widget.addTab(self.character_tab, "Personajes")
        
        # Pestaña de Variaciones
        self.variations_panel = VariationsPanel(self.variations_manager, self.prompt_generator)
        self.tab_widget.addTab(self.variations_panel, "Variaciones")
        
        # ← NUEVA PESTAÑA DE PRESETS
        # En el método setup_ui(), cambiar la línea 114:
        # Cambiar esta línea:
        self.presets_panel = PresetsPanel(self.main_window)  # ← Pasar MainWindow en lugar de self
        self.tab_widget.addTab(self.presets_panel, "Presets")
        
        # Pestaña de SugePrompt
        from ui.sugeprompt_panel import SugePromptPanel
        self.sugeprompt_panel = SugePromptPanel(self.main_window)
        self.tab_widget.addTab(self.sugeprompt_panel, "SugePrompt")
        
        # Configurar tooltips para las pestañas
        self.tab_widget.setTabToolTip(0, "Gestión de Personajes")
        self.tab_widget.setTabToolTip(1, "Gestión de Variaciones")
        self.tab_widget.setTabToolTip(2, "Gestión de Presets")
        self.tab_widget.setTabToolTip(3, "SugePrompt")
        
        content_layout.addWidget(self.tab_widget)
        layout.addWidget(self.content_widget)

    def setup_character_tab(self):
        """Configura la pestaña de personajes"""
        layout = QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)
        
        # Campo de filtro de búsqueda
        self.search_filter = QLineEdit()
        self.search_filter.setPlaceholderText("🔍 Buscar personaje...")
        self.search_filter.textChanged.connect(self.filter_characters)
        layout.addWidget(self.search_filter)
        
        # Lista de personajes
        self.character_list = QListWidget()
        self.character_list.itemClicked.connect(self.on_character_selected)
        self.character_list.itemDoubleClicked.connect(self.on_character_double_clicked)
        layout.addWidget(self.character_list)
        
        # Asignar el layout al tab
        self.character_tab.setLayout(layout)
        
        # Lista para almacenar todos los personajes (para filtrado)
        self.all_characters = []
        
        # Dropdown de personajes
        self.character_dropdown = QComboBox()
        # Remover los elementos hardcodeados ya que setup_data() los cargará dinámicamente
        self.character_dropdown.currentTextChanged.connect(self.on_character_change)
        
        # Habilitar doble clic para cargar personajes
        self.character_dropdown.view().doubleClicked.connect(self.load_selected_character)
    
        
    def connect_variation_signals(self):
        """Conecta las señales del panel de variaciones"""
        self.variations_panel.variation_loaded.connect(self.on_variation_loaded)
        self.variations_panel.variation_saved.connect(self.on_variation_saved)

    def on_variation_loaded(self, variation_data):
        """Maneja cuando se carga una variación"""
        # Guardar snapshot de los valores originales
        self.original_values_snapshot = variation_data.get('values', {}).copy()
        self.changes_tracker = {}  # Limpiar tracker de cambios
        
        # Emitir señal para que el main_window aplique la variación
        self.variation_applied.emit(variation_data)
        
        # Actualizar la descripción del personaje si es necesario
        character_name = variation_data.get('character', '')
        if character_name:
            current_char = self.character_dropdown.currentText()
            if current_char != character_name:
                index = self.character_dropdown.findText(character_name)
                if index >= 0:
                    self.character_dropdown.setCurrentIndex(index)
    
    def track_category_change(self, category_name, old_value, new_value):
        """Registra un cambio específico en una categoría"""
        if category_name not in self.original_values_snapshot:
            self.original_values_snapshot[category_name] = ""
        
        original = self.original_values_snapshot[category_name]
        
        # Calcular qué se añadió específicamente
        original_items = set(item.strip() for item in original.split(',') if item.strip())
        new_items = set(item.strip() for item in new_value.split(',') if item.strip())
        
        added_items = new_items - original_items
        removed_items = original_items - new_items
        
        if added_items or removed_items:
            self.changes_tracker[category_name] = {
                'added': list(added_items),
                'removed': list(removed_items),
                'original': original,
                'current': new_value
            }
        elif category_name in self.changes_tracker:
            # Si no hay cambios, remover del tracker
            del self.changes_tracker[category_name]

    def on_variation_saved(self, character_name, variation_name):
        """Maneja cuando se guarda una variación"""
        print(f"📨 SEÑAL RECIBIDA: variation_saved para {character_name} - {variation_name}")
        
        # Actualizar la lista de personajes si es necesario
        self.refresh_characters()
        
        # FORZAR actualización inmediata de variaciones
        if hasattr(self, 'variations_panel'):
            print("🔄 Actualizando variations_panel AHORA...")
            self.variations_panel.load_variations()
            print("✅ Actualización completada")
        
        print(f"✅ Proceso completo para '{variation_name}' en {character_name}")

    def get_current_character(self):
        """Obtiene el personaje actualmente seleccionado"""
        current = self.character_dropdown.currentText()
        if current == "Seleccionar personaje...":
            return None
        return current

    def set_current_character(self, character_name):
        """Establece el personaje actual en el dropdown"""
        index = self.character_dropdown.findText(character_name)
        if index >= 0:
            self.character_dropdown.setCurrentIndex(index)
        else:
            # Añadir el personaje si no existe
            self.character_dropdown.addItem(character_name)
            self.character_dropdown.setCurrentText(character_name)

    def toggle_sidebar(self):
        """Colapsa o expande el sidebar"""
        if self.content_widget.isVisible():
            # Colapsar
            self.content_widget.hide()
            self.subtitle_label.hide()
            self.toggle_button.setText("▶")
            self.setFixedWidth(60)
        else:
            # Expandir
            self.content_widget.show()
            self.subtitle_label.show()
            self.toggle_button.setText("◀")
            self.setMaximumWidth(16777215)  # Restaurar ancho máximo
            self.setMinimumWidth(250)  # Ancho mínimo reducido
            self.setFixedWidth(250)  # Ancho fijo más pequeño

    def setup_styles(self):
        """Configura los estilos del sidebar"""
        self.setStyleSheet("""
            QFrame {
                background-color: #2b2b2b;
                border: 1px solid #404040;
                border-radius: 8px;
            }
            QLabel {
                color: #e0e0e0;
                background: transparent;
            }
            QPushButton {
                background-color: #404040;
                border: 1px solid #606060;
                border-radius: 4px;
                color: #e0e0e0;
                padding: 4px 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #505050;
                border-color: #707070;
            }
            QPushButton:pressed {
                background-color: #353535;
            }
            QTabWidget::pane {
                border: 1px solid #404040;
                background-color: #2b2b2b;
                border-radius: 4px;
            }
            QTabWidget::tab-bar {
                alignment: center;
            }
            QTabBar::tab {
                background-color: #404040;
                color: #e0e0e0;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #6366f1;
                color: white;
            }
            QTabBar::tab:hover {
                background-color: #505050;
            }
            QLineEdit {
                background-color: #1a1a1a;
                border: 1px solid #404040;
                border-radius: 6px;
                color: #e0e0e0;
                padding: 8px;
                font-size: 11px;
            }
            QLineEdit:focus {
                border-color: #6366f1;
            }
            QListWidget {
                background-color: #1a1a1a;
                border: 1px solid #404040;
                border-radius: 6px;
                color: #e0e0e0;
                padding: 4px;
                font-size: 11px;
                outline: none;
            }
            QListWidget::item {
                padding: 8px;
                border-radius: 4px;
                margin: 1px;
            }
            QListWidget::item:hover {
                background-color: #404040;
            }
            QListWidget::item:selected {
                background-color: white;
                color: black;
                font-weight: bold;
            }
            QListWidget::item:selected:hover {
                background-color: #f0f0f0;
                color: black;
            }
        """)

    def setup_data(self):
        """Configura los datos de personajes desde archivos"""
        # Cargar personajes desde la carpeta de personajes
        characters_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "characters")
        
        # Asegurarse de que el directorio existe
        if not os.path.exists(characters_dir):
            os.makedirs(characters_dir)
        
        # Limpiar la lista y el array de personajes
        self.character_list.clear()
        self.all_characters = []
        
        # Cargar personajes desde la nueva estructura (carpetas)
        for item in os.listdir(characters_dir):
            item_path = os.path.join(characters_dir, item)
            
            # Verificar si es una carpeta (nueva estructura)
            if os.path.isdir(item_path):
                # Buscar el archivo JSON con el mismo nombre que la carpeta
                json_filename = f"{item}.json"
                json_path = os.path.join(item_path, json_filename)
                
                if os.path.exists(json_path):
                    try:
                        # Leer el archivo JSON para obtener metadatos
                        with open(json_path, "r", encoding="utf-8") as f:
                            character_data = json.load(f)
                        
                        # Obtener el nombre del personaje y fecha de creación
                        if "metadata" in character_data and "character_name" in character_data["metadata"]:
                            character_name = character_data["metadata"]["character_name"]
                            
                            # Obtener y formatear la fecha de creación
                            if "created_date" in character_data["metadata"]:
                                created_date_str = character_data["metadata"]["created_date"]
                                try:
                                    # Parsear la fecha ISO
                                    created_date = datetime.fromisoformat(created_date_str.replace('Z', '+00:00'))
                                    formatted_date = created_date.strftime("%d/%m/%Y")
                                    display_text = f"{character_name} - {formatted_date}"
                                except ValueError:
                                    display_text = f"{character_name} - Fecha inválida"
                            else:
                                display_text = f"{character_name} - Sin fecha"
                        else:
                            # Fallback al nombre de la carpeta
                            character_name = item.replace('_', ' ').title()
                            display_text = f"{character_name} - Sin metadatos"
                        
                        # Agregar al array de personajes
                        self.all_characters.append({
                            'name': character_name,
                            'display_text': display_text
                        })
                        
                    except (json.JSONDecodeError, FileNotFoundError) as e:
                        # En caso de error, usar el nombre de la carpeta
                        character_name = item.replace('_', ' ').title()
                        display_text = f"{character_name} - Error al cargar"
                        self.all_characters.append({
                            'name': character_name,
                            'display_text': display_text
                        })
            
            # También manejar archivos JSON directos (estructura antigua)
            elif item.endswith('.json'):
                json_path = os.path.join(characters_dir, item)
                try:
                    with open(json_path, "r", encoding="utf-8") as f:
                        character_data = json.load(f)
                    
                    character_name = item[:-5].replace('_', ' ').title()
                    display_text = f"{character_name} - Formato antiguo"
                    
                    self.all_characters.append({
                        'name': character_name,
                        'display_text': display_text
                    })
                    
                except (json.JSONDecodeError, FileNotFoundError):
                    pass
        
        # Ordenar personajes alfabéticamente
        self.all_characters.sort(key=lambda x: x['name'])
        
        # Mostrar todos los personajes inicialmente
        self.filter_characters("")

    def on_character_change(self, character_name):
        """Maneja el cambio de personaje seleccionado"""
        if character_name and character_name != "Seleccionar personaje...":
            # Buscar el archivo del personaje
            characters_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "characters")
            
            # Intentar cargar desde la nueva estructura (carpeta)
            character_folder = os.path.join(characters_dir, character_name.lower().replace(' ', '_'))
            json_path = os.path.join(character_folder, f"{character_name.lower().replace(' ', '_')}.json")
            
            # Si no existe, intentar con la estructura antigua
            if not os.path.exists(json_path):
                json_path = os.path.join(characters_dir, f"{character_name.lower().replace(' ', '_')}.json")
            
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    character_data = json.load(f)
                
                # Emitir los datos del personaje
                if "metadata" in character_data and "categories" in character_data:
                    # Nuevo formato con metadatos
                    self.character_defaults_selected.emit(character_data["categories"])
                else:
                    # Formato antiguo sin estructura de metadatos
                    self.character_defaults_selected.emit(character_data)
                    
            except (json.JSONDecodeError, FileNotFoundError) as e:
                print(f"Error al cargar {character_name}: {str(e)}")
        else:
            self.character_desc.setText(f"❌ No se encontraron datos para {character_name}")

    def load_selected_character(self, index):
        """Carga el personaje seleccionado al hacer doble clic"""
        character_name = self.character_dropdown.itemText(index.row())
        if character_name and character_name != "Seleccionar personaje...":
            self.on_character_change(character_name)
    
    def refresh_characters(self):
        """Refresca la lista de personajes desde los archivos"""
        current_selection = None
        if self.character_list.currentItem():
            current_selection = self.character_list.currentItem().data(Qt.ItemDataRole.UserRole)
        
        self.setup_data()
        
        # Intentar mantener la selección actual si existe
        if current_selection:
            for i in range(self.character_list.count()):
                item = self.character_list.item(i)
                if item.data(Qt.ItemDataRole.UserRole) == current_selection:
                    self.character_list.setCurrentItem(item)
                    break
    
    def add_character_to_dropdown(self, character_name=None):
        """Añade un personaje a la lista o refresca la lista completa"""
        self.refresh_characters()
        
        # Si se proporciona un nombre de personaje, solo seleccionarlo visualmente
        # pero NO cargar automáticamente sus datos
        if character_name:
            for i in range(self.character_list.count()):
                item = self.character_list.item(i)
                if item.data(Qt.ItemDataRole.UserRole) == character_name:
                    self.character_list.setCurrentItem(item)
                    # ELIMINAR ESTA LÍNEA: self.on_character_change(character_name)
                    break

    def filter_characters(self, text):
        """Filtra los personajes según el texto de búsqueda"""
        self.character_list.clear()
        
        for character_data in self.all_characters:
            character_name = character_data['name']
            display_text = character_data['display_text']
            
            # Filtrar por nombre (case insensitive)
            if text.lower() in character_name.lower():
                item = QListWidgetItem(display_text)
                item.setData(Qt.ItemDataRole.UserRole, character_name)
                self.character_list.addItem(item)
    
    def on_character_selected(self, item):
        """Maneja la selección de un personaje en la lista"""
        # Solo para selección, sin acción específica
        pass
    
    def on_character_double_clicked(self, item):
        """Maneja el doble clic para cargar un personaje"""
        character_name = item.data(Qt.ItemDataRole.UserRole)
        if character_name:
            self.on_character_change(character_name)
            
