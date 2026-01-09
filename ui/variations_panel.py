from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
    QPushButton, QLabel, QDialog, QLineEdit, QTextEdit, QComboBox,
    QSpinBox, QCheckBox, QDialogButtonBox, QMessageBox, QInputDialog,
    QSplitter, QGroupBox, QFormLayout, QListWidget, QScrollArea, QFrame,
    QStyle
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QIcon
from logic.variations_manager import VariationsManager
from datetime import datetime
import os

class VariationsPanel(QWidget):
    variation_loaded = pyqtSignal(dict) 
    variation_saved = pyqtSignal(str, str)  
    character_changed = pyqtSignal(str) 
    
    def __init__(self, variations_manager, prompt_generator):
        super().__init__()
        self.variations_manager = variations_manager
        self.prompt_generator = prompt_generator
        self.current_character = None
        self.setup_ui()
        self.setup_styles()
        self.load_variations()

    def setup_ui(self):
        """Configura la interfaz del panel de variaciones"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        header_layout = QHBoxLayout()
        title_label = QLabel("Variaciones")
        title_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        self.refresh_button = QPushButton("🔄")
        self.refresh_button.setToolTip("Actualizar lista de variaciones")
        self.refresh_button.clicked.connect(self.refresh_variations)
        self.refresh_button.setMaximumWidth(30)
        self.refresh_button.setMaximumHeight(30)
        self.refresh_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                font-size: 16px;
                padding: 4px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.2);
            }
        """)
        header_layout.addWidget(self.refresh_button)
        self.delete_button = QPushButton("🗑️")
        self.delete_button.setToolTip("Eliminar variaciones")
        self.delete_button.clicked.connect(self.show_delete_dialog)
        self.delete_button.setMaximumWidth(30)
        self.delete_button.setMaximumHeight(30)
        self.delete_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                font-size: 16px;
                padding: 4px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: rgba(255, 100, 100, 0.2);
            }
            QPushButton:pressed {
                background-color: rgba(255, 100, 100, 0.3);
            }
        """)
        header_layout.addWidget(self.delete_button)
        layout.addLayout(header_layout)
        self.variations_tree = QTreeWidget()
        self.variations_tree.setHeaderLabels(["Personaje/Variación"])
        self.variations_tree.setRootIsDecorated(True)
        self.variations_tree.setAlternatingRowColors(True)
        self.variations_tree.itemDoubleClicked.connect(self.load_variation_on_double_click)
        self.variations_tree.itemClicked.connect(self.toggle_character_on_click)
        layout.addWidget(self.variations_tree)
        
    def setup_styles(self):
        """Configura los estilos del panel"""
        self.setStyleSheet("""
            QTreeWidget {
                background-color: #2b2b2b;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 4px;
            }
            QTreeWidget::item {
                padding: 4px;
                border-bottom: 1px solid #444444;
            }
            QTreeWidget::item:selected {
                background-color: #6366f1;
            }
            QTreeWidget::item:hover {
                background-color: #404040;
            }
            QPushButton {
                background-color: #6366f1;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5855eb;
            }
            QPushButton:pressed {
                background-color: #4f46e5;
            }
        """)

    def load_variations(self, character_name=None):
        self.variations_tree.clear()
        try:
            characters = self.variations_manager.get_all_characters_with_variations()
            if character_name:
                characters = [character_name] if character_name in characters else []
            assets_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'icons')
            character_icon_path = os.path.join(assets_dir, 'folder.png')
            variation_icon_path = os.path.join(assets_dir, 'file.png')
            character_icon = QIcon(character_icon_path) if os.path.exists(character_icon_path) else self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
            variation_icon = QIcon(variation_icon_path) if os.path.exists(variation_icon_path) else self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowRight)

            enriched = []
            for character in characters:
                data = self.variations_manager.get_character_variations(character)
                variations = data.get("variations", {})
                if not variations:
                    continue
                var_list = []
                for variation_name, variation_data in variations.items():
                    created_str = variation_data.get("created_date")
                    ts = 0
                    if created_str:
                        try:
                            dt = datetime.fromisoformat(created_str.replace('Z', '+00:00'))
                            ts = int(dt.timestamp())
                        except Exception:
                            ts = 0
                    if ts == 0:
                        vf = self.variations_manager.get_character_variations_file(character)
                        ts = int(os.path.getmtime(vf)) if os.path.exists(vf) else 0
                    var_list.append((variation_name, variation_data, ts))
                var_list.sort(key=lambda x: (x[2], x[0].lower()), reverse=True)
                latest_ts = var_list[0][2] if var_list else 0
                enriched.append({"character": character, "variations": var_list, "latest_ts": latest_ts})

            enriched.sort(key=lambda x: (x["latest_ts"], x["character"].lower()), reverse=True)

            for entry in enriched:
                character_item = QTreeWidgetItem(self.variations_tree)
                character_item.setText(0, entry["character"])
                character_item.setText(1, f"{len(entry['variations'])} variaciones")
                character_item.setExpanded(False)
                character_item.setIcon(0, character_icon)
                for variation_name, variation_data, _ts in entry["variations"]:
                    variation_item = QTreeWidgetItem(character_item)
                    variation_item.setText(0, variation_name)
                    variation_item.setIcon(0, variation_icon)
                    variation_item.setData(0, Qt.ItemDataRole.UserRole, {
                        'character': entry["character"],
                        'variation_name': variation_name,
                        'data': variation_data
                    })
        except Exception as e:
            print(f"Error cargando variaciones: {e}")

    def toggle_character_on_click(self, item, column):
        """Expande/colapsa con un clic si el item es un personaje (raíz)."""
        try:
            if item and item.parent() is None:
                item.setExpanded(not item.isExpanded())
        except Exception as e:
            print(f"Error al alternar expansión: {e}")

    def get_variation_description(self, variation_data):
        """Genera una descripción breve de la variación"""
        if not variation_data or 'categories' not in variation_data:
            return "Sin descripción"
        
        categories = variation_data['categories']
        active_categories = [name for name, data in categories.items() 
                           if data.get('enabled', False)]
        
        if not active_categories:
            return "Sin categorías activas"
        
        if len(active_categories) <= 3:
            return ", ".join(active_categories)
        else:
            return f"{', '.join(active_categories[:3])}... (+{len(active_categories)-3})"

    def load_variation(self):
        """Carga la variación seleccionada"""
        current_item = self.variations_tree.currentItem()
        if not current_item:
            QMessageBox.information(self, "Información", "Selecciona una variación para cargar")
            return
        
        # Verificar que sea una variación 
        variation_data = current_item.data(0, Qt.ItemDataRole.UserRole)
        if not variation_data:
            QMessageBox.information(self, "Información", "Selecciona una variación específica")
            return
        
        # Emitir señal para cargar la variación
        self.variation_loaded.emit(variation_data['data'])
        self.character_changed.emit(variation_data['character'])
        
        QMessageBox.information(
            self, "Éxito", 
            f"Variación '{variation_data['variation_name']}' cargada"
        )

    def load_variation_on_double_click(self, item, column):
        """Carga variación al hacer doble clic"""
        variation_data = item.data(0, Qt.ItemDataRole.UserRole)
        if variation_data:
            self.variation_loaded.emit(variation_data['data'])
            self.character_changed.emit(variation_data['character'])

    def delete_variation(self):
        """Elimina la variación seleccionada"""
        current_item = self.variations_tree.currentItem()
        if not current_item:
            QMessageBox.information(self, "Información", "Selecciona una variación para eliminar")
            return
        
        variation_data = current_item.data(0, Qt.ItemDataRole.UserRole)
        if not variation_data:
            QMessageBox.information(self, "Información", "Selecciona una variación específica")
            return
        
        character = variation_data['character']
        variation_name = variation_data['variation_name']
        
        reply = QMessageBox.question(
            self, "Confirmar eliminación",
            f"¿Estás seguro de que quieres eliminar la variación '{variation_name}' de {character}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            success = self.variations_manager.delete_variation(character, variation_name)
            if success:
                self.load_variations()
                QMessageBox.information(
                    self, "Éxito", 
                    f"Variación '{variation_name}' eliminada"
                )
            else:
                QMessageBox.warning(
                    self, "Error", 
                    "No se pudo eliminar la variación"
                )

    def copy_variation(self):
        """Copia una variación a otro personaje"""
        current_item = self.variations_tree.currentItem()
        if not current_item:
            QMessageBox.information(self, "Información", "Selecciona una variación para copiar")
            return
        
        variation_data = current_item.data(0, Qt.ItemDataRole.UserRole)
        if not variation_data:
            QMessageBox.information(self, "Información", "Selecciona una variación específica")
            return
        
        source_character = variation_data['character']
        source_variation = variation_data['variation_name']
        
        dialog = CopyVariationDialog(self, source_character, source_variation)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            target_character = dialog.target_character
            new_name = dialog.new_variation_name
            
            if target_character and new_name:
                new_variation_data = variation_data['data'].copy()
                new_variation_data['modified_at'] = datetime.now().isoformat()
                
                success = self.variations_manager.save_variation(
                    target_character, new_name, new_variation_data
                )
                
                if success:
                    self.load_variations()
                    QMessageBox.information(
                        self, "Éxito", 
                        f"Variación copiada como '{new_name}' para {target_character}"
                    )
                else:
                    QMessageBox.warning(
                        self, "Error", 
                        "No se pudo copiar la variación"
                    )

    def refresh_variations(self):
        """Actualiza manualmente la lista de variaciones"""
        print("🔄 Actualizando lista de variaciones...")
        self.load_variations()
        print("✅ Lista de variaciones actualizada")

    def show_delete_dialog(self):
        """Muestra diálogo simple para eliminar la variación seleccionada"""
        current_item = self.variations_tree.currentItem()
        if not current_item:
            QMessageBox.information(self, "Información", "Selecciona una variación para eliminar")
            return
        
        # Verificar si es una variación
        variation_data = current_item.data(0, Qt.ItemDataRole.UserRole)
        if not variation_data:
            QMessageBox.information(self, "Información", "Selecciona una variación para eliminar")
            return
        
        character_name = current_item.parent().text(0)
        variation_name = variation_data['variation_name']
        reply = QMessageBox.question(
            self, "Confirmar Eliminación",
            f"¿Estás seguro de que deseas eliminar la variación '{variation_name}' del personaje '{character_name}'?\n\nEsta acción no se puede deshacer.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            success = self.variations_manager.delete_variation(character_name, variation_name)
            if success:
                QMessageBox.information(self, "Éxito", "Variación eliminada correctamente")
                self.load_variations()
            else:
                QMessageBox.warning(self, "Error", "No se pudo eliminar la variación")

    def refresh_variations(self):
        """Actualiza manualmente la lista de variaciones"""
        print("🔄 Actualizando lista de variaciones...")
        self.load_variations()
        print("✅ Lista de variaciones actualizada")

class SaveVariationDialog(QDialog):
    """Diálogo para guardar una nueva variación"""
    
    def __init__(self, character_name=None, current_values=None, parent=None, changes=None):
        super().__init__(parent)
        self._character_name = character_name or ""
        self.current_values = current_values or {}
        self.changes = changes or {}
        self.parent_widget = parent
        self.setWindowTitle("Guardar Variación")
        self.setModal(True)
        self.resize(500, 350)
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        self.character_input = QLineEdit()
        if character_name:
            self.character_input.setText(character_name)
            self.character_input.setReadOnly(True)
        form_layout.addRow("Personaje:", self.character_input)
        self.variation_input = QLineEdit()
        default_variation_name = self._generate_default_variation_name()
        self.variation_input.setText(default_variation_name)
        form_layout.addRow("Nombre de variación:", self.variation_input)
        layout.addLayout(form_layout)
        changes_group = QGroupBox("Valores añadidos en esta variación:")
        changes_layout = QVBoxLayout(changes_group)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMaximumHeight(150)
        changes_widget = QWidget()
        changes_widget_layout = QVBoxLayout(changes_widget)
        self._create_changes_view(changes_widget_layout)
        scroll_area.setWidget(changes_widget)
        changes_layout.addWidget(scroll_area)
        layout.addWidget(changes_group)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def _create_changes_view(self, layout):
        """Crea la vista de cambios mostrando solo valores específicos añadidos"""
        changes_found = False
        for category_name, change_info in self.changes.items():
            
            if change_info['added']:

                changes_found = True
                category_layout = QHBoxLayout()
                category_label = QLabel(f"{category_name}:")
                category_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
                category_label.setMinimumWidth(100)
                category_layout.addWidget(category_label)
                values_layout = QHBoxLayout()
                values_layout.setSpacing(5)
                for added_value in change_info['added']:
                    value_label = QLabel(f"{added_value}")
                    value_label.setStyleSheet("""
                        QLabel {
                            background-color: #E8F5E8;
                            color: #2E7D32;
                            border: 1px solid #4CAF50;
                            border-radius: 12px;
                            padding: 4px 8px;
                            margin: 2px;
                            font-family: 'Consolas', 'Monaco', monospace;
                            font-size: 11px;
                            font-weight: bold;
                        }
                    """)
                    values_layout.addWidget(value_label)
                
                values_layout.addStretch()
                category_layout.addLayout(values_layout)
                category_widget = QWidget()
                category_widget.setLayout(category_layout)
                layout.addWidget(category_widget)
        
        if not changes_found:
            no_changes_label = QLabel("No se añadieron valores nuevos en esta variación.")
            no_changes_label.setStyleSheet("color: #757575; font-style: italic; padding: 20px;")
            no_changes_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(no_changes_label)
    
    def _get_currently_loaded_variation(self):
        """Obtiene los valores de la variación actualmente cargada"""
        if hasattr(self.parent_widget, 'currently_loaded_variation_values'):
            return self.parent_widget.currently_loaded_variation_values
        return self._get_base_config()
    
    def _get_specific_added_values(self, loaded_value, current_value):
        """Obtiene solo los valores específicos que se añadieron"""
        loaded_items = set(item.strip() for item in loaded_value.split(',') if item.strip())
        current_items = set(item.strip() for item in current_value.split(',') if item.strip())
        added_items = current_items - loaded_items
        
        return sorted(list(added_items))
    
    def _get_base_config(self):
        """Obtiene la configuración base del personaje"""
        variations_manager = None
        if hasattr(self.parent_widget, 'variations_manager'):
            variations_manager = self.parent_widget.variations_manager
        elif hasattr(self.parent_widget, 'parent') and hasattr(self.parent_widget.parent(), 'variations_manager'):
            variations_manager = self.parent_widget.parent().variations_manager
        
        if variations_manager and self._character_name:
            return variations_manager.get_character_base_config(self._character_name)
        return {}
    
    def _generate_default_variation_name(self):
        """Genera un nombre por defecto para la variación"""
        if not self._character_name:
            return "va1"
        
        variations_manager = None
        if hasattr(self.parent_widget, 'variations_manager'):
            variations_manager = self.parent_widget.variations_manager
        elif hasattr(self.parent_widget, 'parent') and hasattr(self.parent_widget.parent(), 'variations_manager'):
            variations_manager = self.parent_widget.parent().variations_manager
        
        if variations_manager:
            character_data = variations_manager.get_character_variations(self._character_name)
            variations = character_data.get("variations", {})
            
            existing_numbers = []
            base_name = f"{self._character_name}_va"
            
            for var_name in variations.keys():
                if var_name.startswith(base_name):
                    try:
                        num_str = var_name[len(base_name):]
                        existing_numbers.append(int(num_str))
                    except ValueError:
                        continue
            
            next_num = 1
            while next_num in existing_numbers:
                next_num += 1
            
            return f"{base_name}{next_num}"
        
        return f"{self._character_name}_va1"
    
    def get_variation_data(self):
        """Retorna los datos de la variación"""
        return {
            'name': self.variation_name,
            'categories': self.current_values
        }
    
    @property
    def character_name(self):
        return self.character_input.text().strip()
    
    @property
    def variation_name(self):
        return self.variation_input.text().strip()
    
    @property
    def description(self):
        return self.description_input.toPlainText().strip()

class CopyVariationDialog(QDialog):
    """Diálogo para copiar una variación a otro personaje"""
    
    def __init__(self, parent=None, source_character="", source_variation=""):
        super().__init__(parent)
        self.setWindowTitle("Copiar Variación")
        self.setModal(True)
        self.resize(350, 200)
        layout = QVBoxLayout(self)
        info_label = QLabel(f"Copiando: {source_character} > {source_variation}")
        info_label.setStyleSheet("font-weight: bold; color: #6366f1;")
        layout.addWidget(info_label)
        form_layout = QFormLayout()
        self.target_input = QLineEdit()
        form_layout.addRow("Personaje destino:", self.target_input)
        self.new_name_input = QLineEdit()
        self.new_name_input.setText(f"{source_variation}_copy")
        form_layout.addRow("Nuevo nombre:", self.new_name_input)
        layout.addLayout(form_layout)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    @property
    def target_character(self):
        return self.target_input.text().strip()
    
    @property
    def new_variation_name(self):
        return self.new_name_input.text().strip()
