from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QComboBox, QFrame, QSizePolicy, QTabWidget,
                             QListWidget, QListWidgetItem, QLineEdit, QMenu, QDialog, QTextEdit, QMessageBox)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QPalette, QColor, QIcon, QPixmap, QAction
import shutil
import os
import json
from datetime import datetime
from ui.variations_panel import VariationsPanel
from ui.ui_elements import PasteImageWidget
from ui.presets_panel import PresetsPanel
from ui.capture_prompt_panel import CapturePromptPanel
from logic.variations_manager import VariationsManager
from ui.utils.style_loader import load_stylesheet

class SidebarFrame(QFrame):
    character_defaults_selected = pyqtSignal(dict)
    variation_applied = pyqtSignal(dict)
    
    def __init__(self, prompt_generator, main_window=None):
        super().__init__()
        self.prompt_generator = prompt_generator
        self.main_window = main_window
        self.is_collapsed = False
        self.expanded_width = 280
        self.collapsed_width = 60
        
        self.variations_manager = VariationsManager()
        
        # Sistema de tracking de cambios
        self.original_values_snapshot = {}
        self.changes_tracker = {}
        
        self.setup_ui()
        self.setup_styles()
        self.setup_data()
        self.connect_variation_signals()

    def setup_ui(self):
        """Configura la interfaz del sidebar"""
        self.setFixedWidth(self.expanded_width)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        header_layout = QHBoxLayout()
        
        self.header_label = QLabel("Prompt Organizer")
        self.header_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        header_layout.addWidget(self.header_label)
        
        self.toggle_button = QPushButton("◀")
        self.toggle_button.setFixedSize(30, 25)
        self.toggle_button.clicked.connect(self.toggle_sidebar)
        header_layout.addWidget(self.toggle_button)
        
        layout.addLayout(header_layout)
        
        self.subtitle_label = QLabel("Gestion de Prompts")
        self.subtitle_label.setFont(QFont("Segoe UI", 10))
        self.subtitle_label.setStyleSheet("color: #a0a0a0;")
        layout.addWidget(self.subtitle_label)
        
        self.content_widget = QWidget()
        content_layout = QVBoxLayout(self.content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(8)
        
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.TabPosition.North)
        self.tab_widget.setUsesScrollButtons(False)
        self.tab_widget.setElideMode(Qt.TextElideMode.ElideRight)
        
        self.character_tab = QWidget()
        self.setup_character_tab()
        self.tab_widget.addTab(self.character_tab, "Personajes")
        
        self.variations_panel = VariationsPanel(self.variations_manager, self.prompt_generator)
        self.tab_widget.addTab(self.variations_panel, "Variaciones")
        
        self.presets_panel = PresetsPanel(self.main_window)
        self.tab_widget.addTab(self.presets_panel, "Presets")
        
        from ui.capture_prompt_panel import CapturePromptPanel
        self.capture_prompt_panel = CapturePromptPanel(self.main_window)
        self.tab_widget.addTab(self.capture_prompt_panel, "PromptCapture")
        
        self.tab_widget.setTabToolTip(0, "Gestión de Personajes")
        self.tab_widget.setTabToolTip(1, "Gestión de Variaciones")
        self.tab_widget.setTabToolTip(2, "Gestión de Presets")
        self.tab_widget.setTabToolTip(3, "PromptCapture")
        
        content_layout.addWidget(self.tab_widget)
        layout.addWidget(self.content_widget)

    def setup_character_tab(self):
        """Configura la pestaña de personajes"""
        layout = QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)
        
        self.search_filter = QLineEdit()
        self.search_filter.setPlaceholderText("🔍 Buscar personaje...")
        self.search_filter.textChanged.connect(self.filter_characters)
        layout.addWidget(self.search_filter)
        
        self.character_list = QListWidget()
        self.character_list.setIconSize(QSize(40, 40))
        self.character_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.character_list.customContextMenuRequested.connect(self.show_context_menu)
        self.character_list.itemClicked.connect(self.on_character_selected)
        self.character_list.itemDoubleClicked.connect(self.on_character_double_clicked)
        layout.addWidget(self.character_list)
        
        self.character_tab.setLayout(layout)
        
        self.all_characters = []
        
        self.character_dropdown = QComboBox()
        self.character_dropdown.currentTextChanged.connect(self.on_character_change)
        
        self.character_dropdown.view().doubleClicked.connect(self.load_selected_character)
    
        
    def connect_variation_signals(self):
        """Conecta las señales del panel de variaciones"""
        self.variations_panel.variation_loaded.connect(self.on_variation_loaded)
        self.variations_panel.variation_saved.connect(self.on_variation_saved)

    def on_variation_loaded(self, variation_data):
        """Maneja cuando se carga una variación"""
        self.original_values_snapshot = variation_data.get('values', {}).copy()
        self.changes_tracker = {}
        
        self.variation_applied.emit(variation_data)
        
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
            del self.changes_tracker[category_name]

    def on_variation_saved(self, character_name, variation_name):
        """Maneja cuando se guarda una variación"""
        print(f"📨 SEÑAL RECIBIDA: variation_saved para {character_name} - {variation_name}")
        
        self.refresh_characters()
        
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
            self.content_widget.hide()
            self.subtitle_label.hide()
            self.toggle_button.setText("▶")
            self.setFixedWidth(60)
        else:
            self.content_widget.show()
            self.subtitle_label.show()
            self.toggle_button.setText("◀")
            self.setMaximumWidth(16777215)
            self.setMinimumWidth(250)
            self.setFixedWidth(250)

    def setup_styles(self):
        """Configura los estilos del sidebar"""
        style = load_stylesheet("sidebar.qss")
        if style:
            self.setStyleSheet(style)

    def setup_data(self):
        """Configura los datos de personajes desde archivos"""
        characters_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "characters")
        
        if not os.path.exists(characters_dir):
            os.makedirs(characters_dir)
        
        self.character_list.clear()
        self.all_characters = []
        
        for item in os.listdir(characters_dir):
            item_path = os.path.join(characters_dir, item)
            
            # Verificar si es una carpeta (nueva estructura)
            if os.path.isdir(item_path):
                json_filename = f"{item}.json"
                json_path = os.path.join(item_path, json_filename)
                
                image_path = os.path.join(item_path, "image.png")
                has_image = os.path.exists(image_path)
                
                if os.path.exists(json_path):
                    try:
                        with open(json_path, "r", encoding="utf-8") as f:
                            character_data = json.load(f)
                        
                        if "metadata" in character_data and "character_name" in character_data["metadata"]:
                            character_name = character_data["metadata"]["character_name"]
                            
                            if "created_date" in character_data["metadata"]:
                                created_date_str = character_data["metadata"]["created_date"]
                                try:
                                    created_date = datetime.fromisoformat(created_date_str.replace('Z', '+00:00'))
                                    formatted_date = created_date.strftime("%d/%m/%Y")
                                    display_text = f"{character_name} - {formatted_date}"
                                    created_ts = int(created_date.timestamp())
                                except ValueError:
                                    display_text = f"{character_name} - Fecha inválida"
                                    try:
                                        created_ts = int(os.path.getmtime(json_path))
                                    except Exception:
                                        created_ts = 0
                            else:
                                display_text = f"{character_name} - Sin fecha"
                                try:
                                    created_ts = int(os.path.getmtime(json_path))
                                except Exception:
                                    created_ts = 0
                        else:
                            # Fallback al nombre de la carpeta
                            character_name = item.replace('_', ' ').title()
                            display_text = f"{character_name} - Sin metadatos"
                            try:
                                created_ts = int(os.path.getmtime(json_path))
                            except Exception:
                                created_ts = 0
                        
                        self.all_characters.append({
                            'name': character_name,
                            'display_text': display_text,
                            'created_ts': created_ts,
                            'image_path': image_path if has_image else None
                        })
                        
                    except (json.JSONDecodeError, FileNotFoundError) as e:
                        character_name = item.replace('_', ' ').title()
                        display_text = f"{character_name} - Error al cargar"
                        try:
                            created_ts = int(os.path.getmtime(json_path))
                        except Exception:
                            created_ts = 0
                        self.all_characters.append({
                            'name': character_name,
                            'display_text': display_text,
                            'created_ts': created_ts
                        })
            
            # También manejar archivos JSON directos (estructura antigua)
            elif item.endswith('.json'):
                json_path = os.path.join(characters_dir, item)
                try:
                    with open(json_path, "r", encoding="utf-8") as f:
                        character_data = json.load(f)
                    
                    character_name = item[:-5].replace('_', ' ').title()
                    display_text = f"{character_name} - Formato antiguo"
                    try:
                        created_ts = int(os.path.getmtime(json_path))
                    except Exception:
                        created_ts = 0
                    
                    self.all_characters.append({
                        'name': character_name,
                        'display_text': display_text,
                        'created_ts': created_ts
                    })
                    
                except (json.JSONDecodeError, FileNotFoundError):
                    pass
        
        # Ordenar por fecha (más reciente primero), luego por nombre
        self.all_characters.sort(key=lambda x: (x.get('created_ts', 0), x['name'].lower()), reverse=True)
        
        self.filter_characters("")

    def on_character_change(self, character_name):
        """Maneja el cambio de personaje seleccionado"""
        if character_name and character_name != "Seleccionar personaje...":
            characters_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "characters")
            
            character_folder = os.path.join(characters_dir, character_name.lower().replace(' ', '_'))
            json_path = os.path.join(character_folder, f"{character_name.lower().replace(' ', '_')}.json")
            
            if not os.path.exists(json_path):
                json_path = os.path.join(characters_dir, f"{character_name.lower().replace(' ', '_')}.json")
            
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    character_data = json.load(f)
                
                if "metadata" in character_data and "categories" in character_data:
                    self.character_defaults_selected.emit(character_data["categories"])
                else:
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
        
        if current_selection:
            for i in range(self.character_list.count()):
                item = self.character_list.item(i)
                if item.data(Qt.ItemDataRole.UserRole) == current_selection:
                    self.character_list.setCurrentItem(item)
                    break
    
    def add_character_to_dropdown(self, character_name=None):
        """Añade un personaje a la lista o refresca la lista completa"""
        self.refresh_characters()
        
        if character_name:
            for i in range(self.character_list.count()):
                item = self.character_list.item(i)
                if item.data(Qt.ItemDataRole.UserRole) == character_name:
                    self.character_list.setCurrentItem(item)
                    break

    def filter_characters(self, text):
        """Filtra los personajes según el texto de búsqueda"""
        self.character_list.clear()
        
        for character_data in self.all_characters:
            character_name = character_data['name']
            display_text = character_data['display_text']
            image_path = character_data.get('image_path')
            
            # Filtrar por nombre (case insensitive)
            if text.lower() in character_name.lower():
                item = QListWidgetItem(display_text)
                item.setData(Qt.ItemDataRole.UserRole, character_name)
                
                # Asignar icono si existe imagen
                if image_path and os.path.exists(image_path):
                    # Intentar carga directa y escalado
                    pixmap = QPixmap(image_path)
                    if not pixmap.isNull():
                        scaled_pixmap = pixmap.scaled(40, 40, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
                        icon = QIcon(scaled_pixmap)
                        item.setIcon(icon)
                        html_image_path = image_path.replace("\\", "/")
                        tooltip_html = f"<img src='{html_image_path}' height='150'>"
                        item.setToolTip(tooltip_html)
                
                self.character_list.addItem(item)
    
    def on_character_selected(self, item):
        """Maneja la selección de un personaje en la lista"""
        pass
    
    def on_character_double_clicked(self, item):
        """Maneja el doble clic para cargar un personaje"""
        character_name = item.data(Qt.ItemDataRole.UserRole)
        if character_name:
            self.on_character_change(character_name)

    def show_context_menu(self, position):
        """Muestra el menú contextual para los personajes"""
        item = self.character_list.itemAt(position)
        if not item:
            return
            
        character_name = item.data(Qt.ItemDataRole.UserRole)
        
        menu = QMenu()
        menu.setStyleSheet("""
            QMenu {
                background-color: #2b2b2b;
                color: #e0e0e0;
                border: 1px solid #404040;
            }
            QMenu::item {
                padding: 5px 20px;
            }
            QMenu::item:selected {
                background-color: #404040;
            }
        """)
        
        change_img_action = QAction("Cambiar Imagen", self)
        change_img_action.triggered.connect(lambda: self.change_character_image(character_name))
        menu.addAction(change_img_action)
        
        view_values_action = QAction("Ver Valores", self)
        view_values_action.triggered.connect(lambda: self.view_character_values(character_name))
        menu.addAction(view_values_action)
        
        menu.exec(self.character_list.mapToGlobal(position))

    def change_character_image(self, character_name):
        """Abre un diálogo para cambiar la imagen del personaje"""
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Cambiar imagen de {character_name}")
        dialog.setFixedSize(300, 250)
        dialog.setStyleSheet("background-color: #2b2b2b; color: white;")
        
        layout = QVBoxLayout(dialog)
        
        label = QLabel("Pega una nueva imagen (Ctrl+V):")
        layout.addWidget(label)
        
        paste_widget = PasteImageWidget()
        layout.addWidget(paste_widget, alignment=Qt.AlignmentFlag.AlignCenter)
        
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Guardar")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
            }
            QPushButton:hover { background-color: #45a049; }
        """)
        save_btn.clicked.connect(dialog.accept)
        btn_layout.addStretch()
        btn_layout.addWidget(save_btn)
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            image = paste_widget.get_image()
            if image:
                # Rutas base
                characters_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "characters")
                normalized_name = character_name.lower().replace(" ", "_")
                character_folder = os.path.join(characters_dir, normalized_name)
                old_json_path = os.path.join(characters_dir, f"{normalized_name}.json")
            
                if not os.path.exists(character_folder):
                    os.makedirs(character_folder, exist_ok=True)
                
                if os.path.exists(old_json_path):
                    new_json_path = os.path.join(character_folder, f"{normalized_name}.json")
                    try:
                        shutil.move(old_json_path, new_json_path)
                        print(f"Migrado {old_json_path} a {new_json_path}")
                    except Exception as e:
                        QMessageBox.warning(self, "Advertencia", f"Error al migrar archivo de datos: {str(e)}")
                
                # Guardar imagen
                image_path = os.path.join(character_folder, "image.png")
                try:
                    image.save(image_path, "PNG")
                    # Refrescar lista
                    self.refresh_characters()
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"No se pudo guardar la imagen: {str(e)}")
            else:
                QMessageBox.warning(self, "Advertencia", "No se ha pegado ninguna imagen.")

    def view_character_values(self, character_name):
        """Muestra los valores JSON del personaje"""
        # Buscar el archivo
        characters_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "characters")
        character_folder = os.path.join(characters_dir, character_name.lower().replace(' ', '_'))
        json_path = os.path.join(character_folder, f"{character_name.lower().replace(' ', '_')}.json")
        
        if not os.path.exists(json_path):
            # Intentar ruta antigua
            json_path = os.path.join(characters_dir, f"{character_name.lower().replace(' ', '_')}.json")
            
        if os.path.exists(json_path):
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                dialog = QDialog(self)
                dialog.setWindowTitle(f"Valores de {character_name}")
                dialog.resize(500, 400)
                dialog.setStyleSheet("background-color: #2b2b2b; color: white;")
                layout = QVBoxLayout(dialog)
                text_edit = QTextEdit()
                text_edit.setReadOnly(True)
                text_edit.setPlainText(json.dumps(data, indent=4, ensure_ascii=False))
                text_edit.setStyleSheet("""
                    QTextEdit {
                        background-color: #1a1a1a;
                        border: 1px solid #404040;
                        font-family: Consolas, monospace;
                        font-size: 12px;
                        color: #dcdcdc;
                    }
                """)
                layout.addWidget(text_edit)
                
                close_btn = QPushButton("Cerrar")
                close_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #555;
                        color: white;
                        border: none;
                        border-radius: 4px;
                        padding: 6px 12px;
                    }
                    QPushButton:hover { background-color: #666; }
                """)
                close_btn.clicked.connect(dialog.accept)
                layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignRight)
                
                dialog.exec()
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo leer el archivo: {str(e)}")
        else:
            QMessageBox.warning(self, "Error", "No se encontró el archivo de datos del personaje.")
            
