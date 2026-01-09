from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTextEdit, QFrame, QSizePolicy, QFileDialog, QListWidget, QMenu, QInputDialog, QDialog, QMessageBox)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QKeySequence, QShortcut, QIcon, QTextOption
import pyperclip
import json
import os
import re
from datetime import datetime
from ui.components.negative_prompt_store import NegativePromptStore

class NegativePromptEditDialog(QDialog):
    def __init__(self, parent=None, initial_text=""):
        super().__init__(parent)
        self.setWindowTitle("Editar Negative Prompt")
        self.setModal(True)
        self.setMinimumSize(420, 300)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        self.text_edit = QTextEdit(self)
        self.text_edit.setPlainText(initial_text)
        self.text_edit.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self.text_edit.setWordWrapMode(QTextOption.WrapMode.WrapAtWordBoundaryOrAnywhere)
        self.text_edit.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.text_edit.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.text_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.text_edit.setFont(QFont("Courier New", 10))
        layout.addWidget(self.text_edit)
        actions = QHBoxLayout()
        actions.addStretch()
        save_btn = QPushButton("Guardar", self)
        save_btn.setFixedHeight(28)
        save_btn.clicked.connect(self.accept)
        actions.addWidget(save_btn)
        layout.addLayout(actions)
        self.setStyleSheet("""
            QDialog {
                background-color: #2d2d2d;
            }
            QTextEdit {
                background-color: #1a1a1a;
                border: 1px solid #404040;
                border-radius: 6px;
                color: #e0e0e0;
                padding: 8px;
            }
            QPushButton {
                background-color: #6366f1;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 11px;
                padding: 4px 12px;
            }
            QPushButton:hover {
                background-color: #4f46e5;
            }
            QPushButton:pressed {
                background-color: #3730a3;
            }
        """)

class PromptSectionFrame(QFrame):
    def __init__(self, prompt_generator):
        super().__init__()
        self.prompt_generator = prompt_generator
        self.neg_store = NegativePromptStore()
        self.config_popup = None
        
        self.setup_ui()
        self.setup_styles()
        self.setup_shortcuts()

    def setup_ui(self):
        """Configura la interfaz de la sección de prompt"""
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)
        self.positive_frame = QFrame()
        positive_layout = QVBoxLayout(self.positive_frame)
        positive_layout.setContentsMargins(0, 0, 0, 0)
        positive_layout.setSpacing(4)
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 6, 0)
        header_layout.setSpacing(8)
        self.positive_toggle = QPushButton("Prompt generado ▼")
        self.positive_toggle.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: #e0e0e0;
                font-weight: bold;
                font-size: 12px;
                text-align: left;
                padding: 6px;
            }
            QPushButton:hover {
                background-color: #252525;
                border-radius: 6px;
            }
        """)
        self.positive_toggle.clicked.connect(self.toggle_positive)
        header_layout.addWidget(self.positive_toggle)
        header_layout.addStretch()
        self.positive_buttons_container = QWidget()
        buttons_layout = QHBoxLayout(self.positive_buttons_container)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        buttons_layout.setSpacing(8)
        self.copy_btn = QPushButton("Copiar")
        self.copy_btn.setFixedSize(100, 28)
        self.copy_btn.clicked.connect(self.copy_prompt)
        self.copy_btn.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.copy_btn.customContextMenuRequested.connect(self.show_copy_menu)
        self.copy_btn.setToolTip("Click para copiar todo\nClick derecho para más opciones")
        buttons_layout.addWidget(self.copy_btn)
        self.export_btn = QPushButton("Exportar")
        self.export_btn.setFixedSize(100, 28)
        self.export_btn.clicked.connect(self.export_prompt)
        buttons_layout.addWidget(self.export_btn)
        self.config_btn = QPushButton()
        self.config_btn.setFixedSize(28, 28)
        self.config_btn.setToolTip("Configuración")
        self.config_btn.clicked.connect(self.open_config)
        try:
            icon_path = "assets/icons/config.png"
            if os.path.exists(icon_path):
                self.config_btn.setIcon(QIcon(icon_path))
            else:
                self.config_btn.setText("⚙")
                self.config_btn.setStyleSheet("""
                    QPushButton {
                        font-size: 16px;
                        font-weight: bold;
                        border: 1px solid #555;
                        border-radius: 6px;
                        background-color: #3a3a3a;
                        color: #ffffff;
                    }
                    QPushButton:hover {
                        background-color: #4a4a4a;
                        border-color: #666;
                    }
                    QPushButton:pressed {
                        background-color: #2a2a2a;
                    }
                """)
        except Exception:
            self.config_btn.setText("⚙")
        buttons_layout.addWidget(self.config_btn)
        header_layout.addWidget(self.positive_buttons_container)
        positive_layout.addLayout(header_layout)
        self.prompt_text = QTextEdit()
        self.prompt_text.setFixedHeight(80)
        self.prompt_text.setFont(QFont("Courier New", 10))
        self.prompt_text.setPlaceholderText("Aquí aparecerá el prompt generado...")
        self.prompt_text.setReadOnly(False)
        positive_layout.addWidget(self.prompt_text)
        self.positive_expanded = True
        layout.addWidget(self.positive_frame)
        self.setup_negative_prompt(layout)

    def toggle_positive(self):
        """Alterna la visibilidad del prompt positivo"""
        self.positive_expanded = not self.positive_expanded
        self.prompt_text.setVisible(self.positive_expanded)
        arrow = "▼" if self.positive_expanded else "▶"
        self.positive_toggle.setText(f"Prompt generado {arrow}")

    def setup_negative_prompt(self, layout):
        """Configura la sección de negative prompt colapsable"""
        # Frame para negative prompt
        self.negative_frame = QFrame()
        negative_layout = QVBoxLayout(self.negative_frame)
        negative_layout.setContentsMargins(0, 0, 0, 0)
        negative_layout.setSpacing(4)  # Reducido de 6 a 4
        header_bar = QHBoxLayout()
        header_bar.setContentsMargins(6, 4, 6, 0)
        header_bar.setSpacing(6)
        self.negative_toggle = QPushButton("Negative Prompt ►")
        self.negative_toggle.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: #e0e0e0;
                font-weight: bold;
                font-size: 11px;  /* Reducido de 12px a 11px */
                text-align: left;
                padding: 6px;  /* Reducido de 8px a 6px */
            }
            QPushButton:hover {
                background-color: #252525;
                border-radius: 6px;
            }
        """)
        self.negative_toggle.clicked.connect(self.toggle_negative)
        header_bar.addWidget(self.negative_toggle)
        self.saved_neg_container = QWidget()
        self.saved_neg_layout = QHBoxLayout(self.saved_neg_container)
        self.saved_neg_layout.setContentsMargins(0, 0, 0, 0)
        self.saved_neg_layout.setSpacing(4)
        header_bar.addWidget(self.saved_neg_container)
        header_bar.addStretch()
        self.negative_save_btn = QPushButton()
        self.negative_save_btn.setToolTip("Guardar Negative Prompt")
        self.negative_save_btn.setFixedSize(24, 24)
        try:
            icon_path = os.path.join("assets", "icons", "save.png")
            if os.path.exists(icon_path):
                self.negative_save_btn.setIcon(QIcon(icon_path))
            else:
                self.negative_save_btn.setText("💾")
        except Exception:
            self.negative_save_btn.setText("💾")
        self.negative_save_btn.clicked.connect(self.save_current_negative_prompt)
        header_bar.addWidget(self.negative_save_btn)
        negative_layout.addLayout(header_bar)
        self.negative_text = QTextEdit()
        self.negative_text.setFixedHeight(60)
        self.negative_text.setFont(QFont("Courier New", 9))
        default_negative = self.neg_store.get_setting("default_negative_prompt", 
                                                   "blurry, low quality, distorted, deformed, ugly, bad anatomy")
        self.negative_text.setPlainText(default_negative)
        negative_layout.addWidget(self.negative_text)
        self.negative_text.hide()
        self.negative_expanded = False
        self.refresh_saved_negative_buttons()

        layout.addWidget(self.negative_frame)

    def setup_styles(self):
        """Configura los estilos de la sección"""
        self.setStyleSheet("""
            QFrame {
                background-color: #252525;
                border: 1px solid #404040;
                border-radius: 8px;
            }
            QTextEdit {
                background-color: #1a1a1a;
                border: 1px solid #404040;
                border-radius: 6px;
                color: #e0e0e0;
                padding: 8px;
            }
            QTextEdit:focus {
                border: 1px solid #6366f1;
            }
            QPushButton {
                background-color: #6366f1;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #4f46e5;
            }
            QPushButton:pressed {
                background-color: #3730a3;
            }
            QLabel {
                color: #e0e0e0;
            }
        """)

    def setup_shortcuts(self):
        """Configura los atajos de teclado"""
        copy_shortcut = QShortcut(QKeySequence("Ctrl+C"), self)
        copy_shortcut.activated.connect(self.copy_prompt)
        export_shortcut = QShortcut(QKeySequence("Ctrl+E"), self)
        export_shortcut.activated.connect(self.export_prompt)

    def toggle_negative(self):
        """Alterna la visibilidad del negative prompt"""
        if self.negative_expanded:
            self.negative_text.hide()
            self.negative_toggle.setText("Negative Prompt ►")
            self.negative_expanded = False
        else:
            self.negative_text.show()
            self.negative_toggle.setText("Negative Prompt ▼")
            self.negative_expanded = True

    def copy_prompt(self):
        """Copia el prompt al portapapeles"""
        prompt_content = self.prompt_text.toPlainText()
        if prompt_content and prompt_content != "Aquí aparecerá el prompt generado...":
            pyperclip.copy(prompt_content)
            self.show_feedback(self.copy_btn, "¡Copiado!")

    def show_copy_menu(self, pos):
        """Muestra el menú contextual con opciones de copiado"""
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #2d2d2d;
                color: #e0e0e0;
                border: 1px solid #555;
            }
            QMenu::item {
                padding: 6px 20px;
            }
            QMenu::item:selected {
                background-color: #3d3d3d;
            }
        """)

        action_no_lora = menu.addAction("Copiar Sin Loras")
        menu.addSeparator()
        action_traits = menu.addAction("Copiar Rasgos")
        action_outfit = menu.addAction("Copiar Vestuario")

        action = menu.exec(self.copy_btn.mapToGlobal(pos))

        if action == action_no_lora:
            self.copy_prompt_no_lora()
        elif action == action_traits:
            self.copy_traits()
        elif action == action_outfit:
            self.copy_outfit()

    def copy_prompt_no_lora(self):
        """Copia el prompt al portapapeles excluyendo los Loras"""
        prompt_content = self.prompt_text.toPlainText()
        if prompt_content and prompt_content != "Aquí aparecerá el prompt generado...":
            text_no_lora = re.sub(r'<lora:[^>]+>', '', prompt_content)
            
            # Dividir por comas y limpiar espacios
            parts = [p.strip() for p in text_no_lora.split(',')]
            
            # Filtrar partes vacías
            clean_parts = [p for p in parts if p]
            
            # Unir con coma y espacio
            clean_text = ', '.join(clean_parts)
            
            pyperclip.copy(clean_text)
            self.show_feedback(self.copy_btn, "¡Copiado S/Lora!")

    def copy_traits(self):
        """Copia solo las categorías de rasgos físicos"""
        traits_categories = [
            "personaje", "cabello forma", "cabello color", "cabello accesorios",
            "rostro accesorios", "ojos", "expresion facial ojos", 
            "expresion facial mejillas", "expresion facial boca", "tipo de cuerpo",
            "rasgo fisico cuerpo", "rasgo fisico piernas", "actitud emocion", "nsfw"
        ]
        self._copy_specific_categories(traits_categories, "¡Rasgos Copiados!")

    def copy_outfit(self):
        """Copia solo las categorías de vestuario"""
        # Palabras clave para identificar vestuario
        outfit_keywords = [
            "vestuario", "ropa", "lenceria", "lencería", 
            "prendas", "calzado", "medias", "zapatos", "botas"
        ]

        target_categories = []
        main_window = self.window()
        if hasattr(main_window, 'category_grid'):
            all_values = main_window.category_grid.get_current_values()
            for cat_name in all_values.keys():
                lower_name = cat_name.lower()
                if any(kw in lower_name for kw in outfit_keywords):
                    target_categories.append(lower_name)
        
        self._copy_specific_categories(target_categories, "¡Vestuario Copiado!", exact_match=False)

    def _copy_specific_categories(self, target_categories, feedback_text, exact_match=True):
        """Helper para copiar categorías específicas"""
        main_window = self.window()
        if not hasattr(main_window, 'category_grid'):
            return

        current_values = main_window.category_grid.get_current_values()
        collected_values = []
        targets_normalized = [t.lower() for t in target_categories]

        for cat_name, value in current_values.items():
            if not value.strip():
                continue
            cleaned_value = value.strip().strip(',')
            if not cleaned_value:
                continue
                
            cat_lower = cat_name.lower()
            
            should_include = False
            if exact_match:
                if cat_lower in targets_normalized:
                    should_include = True
            else:
                if cat_lower in targets_normalized:
                    should_include = True

            if should_include:
                collected_values.append(cleaned_value)

        if collected_values:
            final_text = ", ".join(collected_values)
            parts = [p.strip() for p in final_text.split(',')]
            clean_parts = [p for p in parts if p]
            final_clean_text = ', '.join(clean_parts)
            
            pyperclip.copy(final_clean_text)
            self.show_feedback(self.copy_btn, feedback_text)
        else:
            self.show_feedback(self.copy_btn, "Sin datos", error=True)



    def export_prompt(self):
        """Exporta el prompt en formato TXT con diálogo de guardado"""
        prompt_content = self.prompt_text.toPlainText()
        negative_content = self.negative_text.toPlainText()
        
        if prompt_content and prompt_content != "Aquí aparecerá el prompt generado...":
            try:
                main_window = self.window()
                current_character = None
                if hasattr(main_window, 'sidebar'):
                    if hasattr(main_window.sidebar, 'character_list') and main_window.sidebar.character_list.currentItem():
                        current_character = main_window.sidebar.character_list.currentItem().data(Qt.ItemDataRole.UserRole)

                if current_character:
                    
                    safe_character_name = current_character.replace(' ', '_').replace('/', '_').replace('\\', '_')
                    default_filename = f"{safe_character_name}_prompt.txt"
                else:
                    
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    default_filename = f"prompt_export_{timestamp}.txt"

                filename, _ = QFileDialog.getSaveFileName(
                    self,
                    "Exportar Prompt",
                    default_filename,
                    "Archivos de texto (*.txt);;Todos los archivos (*.*)"
                )
                
                if filename: 
                    
                    if not filename.lower().endswith('.txt'):
                        filename += '.txt'

                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(f"Prompt: {prompt_content}\n\n")
                        if negative_content:
                            f.write(f"Negative Prompt: {negative_content}\n\n")
                        f.write(f"Exportado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    
                    self.show_feedback(self.export_btn, "¡Exportado!")
                    print(f"Prompt exportado a: {filename}")
                
            except Exception as e:
                print(f"Error al exportar: {e}")
                self.show_feedback(self.export_btn, "Error", error=True)

    def show_feedback(self, button, text, error=False):
        """Muestra feedback visual en un botón"""
        original_text = button.text()
        original_style = button.styleSheet()
        
        if error:
            button.setStyleSheet("""
                QPushButton {
                    background-color: #ef4444;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    font-weight: bold;
                    font-size: 11px;
                }
            """)
        else:
            button.setStyleSheet("""
                QPushButton {
                    background-color: #10b981;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    font-weight: bold;
                    font-size: 11px;
                }
            """)
        
        button.setText(text)
        QTimer.singleShot(2000, lambda: self.restore_button(button, original_text, original_style))

    def restore_button(self, button, text, style):
        """Restaura el estado original de un botón"""
        button.setText(text)
        button.setStyleSheet(style)

    def update_prompt(self, prompt_text):
        """Actualiza el prompt generado"""
        if prompt_text:
            self.prompt_text.setPlainText(prompt_text)
        else:
            self.prompt_text.setPlainText("Aquí aparecerá el prompt generado...")

    def get_negative_prompt(self):
        """Obtiene el contenido del negative prompt"""
        return self.negative_text.toPlainText()
    def refresh_saved_negative_buttons(self):
        """Reconstruye los botones numerados según los negative prompts guardados."""
        while self.saved_neg_layout.count():
            item = self.saved_neg_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        prompts = self.neg_store.get_saved_negative_prompts()
        for i, text in enumerate(prompts, start=1):
            btn = QPushButton(f"({i})")
            btn.setFixedHeight(22)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #3a3a3a;
                    color: #e0e0e0;
                    border: 1px solid #555;
                    border-radius: 6px;
                    font-size: 10px;
                    padding: 2px 6px;
                }
                QPushButton:hover {
                    background-color: #4a4a4a;
                }
                QPushButton:pressed {
                    background-color: #2a2a2a;
                }
            """)
            btn.setToolTip("")
            btn.clicked.connect(lambda checked=False, idx=i: self.on_saved_button_clicked(idx))
            btn.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            btn.customContextMenuRequested.connect(lambda pos, idx=i, button=btn: self.show_saved_menu(idx, button))
            self.saved_neg_layout.addWidget(btn)

    def save_current_negative_prompt(self):
        """Guarda el contenido actual del textarea como nuevo negative prompt."""
        text = self.get_negative_prompt().strip()
        if not text:
            return
        self.neg_store.add_saved_negative_prompt(text)
        self.refresh_saved_negative_buttons()

    def on_saved_button_clicked(self, index: int):
        """Carga el negative prompt guardado en el índice en el textarea."""
        prompts = self.neg_store.get_saved_negative_prompts()
        if 1 <= index <= len(prompts):
            self.negative_text.setPlainText(prompts[index - 1])
            # Mostrar si estaba oculto
            if not self.negative_expanded:
                self.toggle_negative()

    def show_saved_menu(self, index: int, button: QPushButton):
        """Muestra un menú contextual para editar, copiar o eliminar el prompt guardado."""
        menu = QMenu(self)
        copy_action = menu.addAction("Copiar")
        edit_action = menu.addAction("Editar")
        delete_action = menu.addAction("Eliminar")
        menu.setStyleSheet("""
            QMenu {
                background-color: #2d2d2d;
                color: #e0e0e0;
                border: 1px solid #555;
            }
            QMenu::item {
                padding: 4px 20px;
            }
            QMenu::item:selected {
                background-color: #3d3d3d;
            }
        """)
        
        action = menu.exec(button.mapToGlobal(button.rect().bottomLeft()))
        
        if action == copy_action:
            self.copy_saved_negative_prompt(index, button)
        elif action == edit_action:
            self.edit_saved_negative_prompt(index)
        elif action == delete_action:
            self.delete_saved_negative_prompt(index)

    def copy_saved_negative_prompt(self, index: int, button: QPushButton):
        """Copia el negative prompt guardado al portapapeles."""
        prompts = self.neg_store.get_saved_negative_prompts()
        if 1 <= index <= len(prompts):
            text = prompts[index - 1]
            pyperclip.copy(text)
            original_text = button.text()
            original_style = button.styleSheet()
            
            button.setText("¡Copiado!")
            button.setStyleSheet("""
                QPushButton {
                    background-color: #10b981;
                    color: white;
                    border: 1px solid #10b981;
                    border-radius: 6px;
                    font-size: 10px;
                    padding: 2px 6px;
                }
            """)
            
            QTimer.singleShot(1000, lambda: self.restore_button(button, original_text, original_style))

    def edit_saved_negative_prompt(self, index: int):
        prompts = self.neg_store.get_saved_negative_prompts()
        if 1 <= index <= len(prompts):
            current = prompts[index - 1]
            dlg = NegativePromptEditDialog(self, current)
            if dlg.exec():
                new_text = dlg.text_edit.toPlainText().strip()
                if new_text:
                    self.neg_store.update_saved_negative_prompt(index, new_text)
                    self.refresh_saved_negative_buttons()

    def delete_saved_negative_prompt(self, index: int):
        prompts = self.neg_store.get_saved_negative_prompts()
        if not (1 <= index <= len(prompts)):
            return

        confirm = QMessageBox(self)
        confirm.setWindowTitle("Confirmar eliminación")
        confirm.setText("¿Eliminar este Negative Prompt guardado?")
        confirm.setInformativeText("Esta acción no se puede deshacer.")
        confirm.setIcon(QMessageBox.Icon.Warning)
        confirm.setStandardButtons(QMessageBox.StandardButton.Yes)

        try:
            confirm.setButtonText(QMessageBox.StandardButton.Yes, "Sí")
        except Exception:
            pass
        confirm.setDefaultButton(QMessageBox.StandardButton.Yes)

        result = confirm.exec()
        if result == QMessageBox.StandardButton.Yes:
            self.neg_store.delete_saved_negative_prompt(index)
            self.refresh_saved_negative_buttons()

    def open_config(self):
        """Abre el popup de configuración al lado del botón"""
        if self.config_popup and self.config_popup.isVisible():
            self.config_popup.hide()
            return
        if not self.config_popup:
            self.create_config_popup()
        self.position_config_popup()
        self.config_popup.show()
        self.config_popup.raise_()
    
    def create_config_popup(self):
        """Crea la ventana popup de configuración"""
        self.config_popup = QFrame(self)
        self.config_popup.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.config_popup.setFixedSize(200, 150)
        popup_layout = QVBoxLayout(self.config_popup)
        popup_layout.setContentsMargins(8, 8, 8, 8)
        popup_layout.setSpacing(4)
        title_label = QLabel("Configuración")
        title_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        popup_layout.addWidget(title_label)
        self.config_list = QListWidget()
        self.config_list.setMaximumHeight(100)
        options = [
            "Copiar Categorías",
            "Copiar Vestuario",
            "Copiar Poses",
            "Copiar Expresiones",
            "Copiar Todo con Valores"
        ]
        for option in options:
            self.config_list.addItem(option)
        self.config_list.itemClicked.connect(self.on_config_option_selected)
        popup_layout.addWidget(self.config_list)
        self.config_popup.setStyleSheet("""
            QFrame {
                background-color: #2d2d2d;
                border: 1px solid #555;
                border-radius: 8px;
            }
            QLabel {
                color: #ffffff;
                padding: 4px;
            }
            QListWidget {
                background-color: #3a3a3a;
                border: 1px solid #555;
                border-radius: 4px;
                color: #ffffff;
                selection-background-color: #4a90e2;
            }
            QListWidget::item {
                padding: 6px;
                border-bottom: 1px solid #444;
            }
            QListWidget::item:hover {
                background-color: #4a4a4a;
            }
            QListWidget::item:selected {
                background-color: #4a90e2;
            }
        """)
    
    def position_config_popup(self):
        """Posiciona el popup al lado del botón de configuración"""
        if not self.config_popup:
            return
        button_pos = self.config_btn.mapToGlobal(self.config_btn.rect().topRight())
        popup_x = button_pos.x() - self.config_popup.width() + 10
        popup_y = button_pos.y()
        screen_geometry = self.screen().geometry()
        if popup_x + self.config_popup.width() > screen_geometry.right():
            popup_x = button_pos.x() - self.config_popup.width() - 10
        
        if popup_y + self.config_popup.height() > screen_geometry.bottom():
            popup_y = button_pos.y() - self.config_popup.height()
        
        self.config_popup.move(popup_x, popup_y)
    
    def load_categories_from_json(self):
        """Carga las categorías desde el archivo JSON"""
        try:
            categories_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'categories.json')
            with open(categories_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('categorias', [])
        except Exception as e:
            print(f"Error al cargar categorías: {e}")
            return []

    def format_categories_for_copy(self, categories):
        """Formatea las categorías para copiar con dos puntos"""
        formatted_categories = []
        for category in categories:
            formatted_categories.append(f"{category}:")
        return "\n".join(formatted_categories)

    def copy_categories(self):
        """Copia todas las categorías al portapapeles"""
        try:
            categories = self.load_categories_from_json()
            if categories:
                formatted_text = self.format_categories_for_copy(categories)
                pyperclip.copy(formatted_text)
                self.show_feedback(self.config_btn, "¡Copiado!", error=False)
                print("Categorías copiadas al portapapeles")
            else:
                self.show_feedback(self.config_btn, "Error", error=True)
                print("No se pudieron cargar las categorías")
        except Exception as e:
            print(f"Error al copiar categorías: {e}")
            self.show_feedback(self.config_btn, "Error", error=True)

    def copy_outfit_categories(self):
        """Copia solo las categorías de vestuario"""
        try:
            # Lista EXACTA de categorías para vestuario según usuario
            outfit_targets = [
                "cabello accesorios",
                "rostro accesorios",
                "vestuario_general",
                "vestuario_superior",
                "vestuario_inferior",
                "vestuario_accesorios",
                "vestuariospies",
                "ropa_interior_superior",
                "ropa_interior_inferior",
                "ropa_interior_accesorios"
            ]
            
            outfit_targets_norm = [t.lower().replace(" ", "_").strip() for t in outfit_targets]
            
            all_categories = self.load_categories_from_json()
            outfit_categories = []
            
            for cat in all_categories:
                # Normalizar categoría del JSON
                cat_clean = cat.lower().replace(" ", "_").strip()
                if cat_clean in outfit_targets_norm:
                    outfit_categories.append(cat)
            
            if outfit_categories:
                formatted_text = self.format_categories_for_copy(outfit_categories)
                pyperclip.copy(formatted_text)
                self.show_feedback(self.config_btn, "¡Copiado!", error=False)
            else:
                self.show_feedback(self.config_btn, "Sin datos", error=True)
                
        except Exception as e:
            print(f"Error al copiar categorías de vestuario: {e}")
            self.show_feedback(self.config_btn, "Error", error=True)

    def copy_pose_categories(self):
        """Copia solo las categorías de poses"""
        try:
            # Lista EXACTA de categorías para poses según usuario
            pose_targets = [
                "angulo",
                "postura_cabeza",
                "direccion mirada personaje",
                "vestuariospies",
                "pose_actitud_global",
                "pose_brazos",
                "pose_piernas",
                "orientación personaje",
                "mirada espectador"
            ]
            pose_targets_norm = [t.lower().replace(" ", "_").strip() for t in pose_targets]
            all_categories = self.load_categories_from_json()
            pose_categories = []
            for cat in all_categories:
                cat_clean = cat.lower().replace(" ", "_").strip()
                if cat_clean in pose_targets_norm:
                    pose_categories.append(cat)
            
            if pose_categories:
                formatted_text = self.format_categories_for_copy(pose_categories)
                pyperclip.copy(formatted_text)
                self.show_feedback(self.config_btn, "¡Copiado!", error=False)
            else:
                self.show_feedback(self.config_btn, "Sin datos", error=True)

        except Exception as e:
            print(f"Error al copiar categorías de poses: {e}")
            self.show_feedback(self.config_btn, "Error", error=True)

    def copy_expression_categories(self):
        """Copia solo las categorías de expresiones"""
        try:
            # Lista EXACTA de categorías para expresiones según usuario
            expression_targets = [
                "expresion_facial_ojos",
                "expresion_facial_mejillas",
                "expresion_facial_boca",
                "actitud emoción"
            ]
            
            # Normalizar para comparación
            expression_targets_norm = [t.lower().replace(" ", "_").strip() for t in expression_targets]
            all_categories = self.load_categories_from_json()
            expression_categories = []
            for cat in all_categories:
                cat_clean = cat.lower().replace(" ", "_").strip()
                if cat_clean in expression_targets_norm:
                    expression_categories.append(cat)
            
            if expression_categories:
                formatted_text = self.format_categories_for_copy(expression_categories)
                pyperclip.copy(formatted_text)
                self.show_feedback(self.config_btn, "¡Copiado!", error=False)
            else:
                self.show_feedback(self.config_btn, "Sin datos", error=True)

        except Exception as e:
            print(f"Error al copiar categorías de expresiones: {e}")
            self.show_feedback(self.config_btn, "Error", error=True)

    def copy_all_categories_with_values(self):
        """Copia todas las categorías con sus valores actuales"""
        try:
            main_window = self.window()
            if not hasattr(main_window, 'category_grid'):
                self.show_feedback(self.config_btn, "Error", error=True)
                return

            current_values = main_window.category_grid.get_current_values()
            formatted_lines = []
            for category, value in sorted(current_values.items()):
                clean_value = value.strip().strip(',')
                formatted_lines.append(f"{category}: {clean_value}")

            if formatted_lines:
                final_text = "\n".join(formatted_lines)
                pyperclip.copy(final_text)
                self.show_feedback(self.config_btn, "¡Copiado!", error=False)
            else:
                self.show_feedback(self.config_btn, "Vacío", error=True)

        except Exception as e:
            print(f"Error al copiar todo con valores: {e}")
            self.show_feedback(self.config_btn, "Error", error=True)

    def on_config_option_selected(self, item):
        """Maneja la selección de una opción de configuración"""
        option_text = item.text()
        print(f"Opción seleccionada: {option_text}")
        self.config_popup.hide()
        if option_text == "Copiar Categorías":
            self.copy_categories()
        elif option_text == "Copiar Vestuario":
            self.copy_outfit_categories()
        elif option_text == "Copiar Poses":
            self.copy_pose_categories()
        elif option_text == "Copiar Expresiones":
            self.copy_expression_categories()
        elif option_text == "Copiar Todo con Valores":
            self.copy_all_categories_with_values()
        else:
            self.show_feedback(self.config_btn, "✓", error=False)
    def mousePressEvent(self, event):
        """Cierra el popup si se hace clic fuera de él"""
        if self.config_popup and self.config_popup.isVisible():
            if not self.config_popup.geometry().contains(event.globalPosition().toPoint()):
                self.config_popup.hide()
        super().mousePressEvent(event)
