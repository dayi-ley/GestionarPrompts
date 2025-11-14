from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTextEdit, QFrame, QSizePolicy, QFileDialog, QListWidget, QMenu, QInputDialog, QDialog, QMessageBox)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QKeySequence, QShortcut, QIcon, QTextOption
import pyperclip
import json
import os
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

        # Editor de texto con ajuste a la ventana
        self.text_edit = QTextEdit(self)
        self.text_edit.setPlainText(initial_text)
        self.text_edit.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        # En PyQt6 las enumeraciones están anidadas en WrapMode
        self.text_edit.setWordWrapMode(QTextOption.WrapMode.WrapAtWordBoundaryOrAnywhere)
        self.text_edit.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.text_edit.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.text_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.text_edit.setFont(QFont("Courier New", 10))
        layout.addWidget(self.text_edit)

        # Barra de acciones: solo Guardar (sin Cancelar)
        actions = QHBoxLayout()
        actions.addStretch()
        save_btn = QPushButton("Guardar", self)
        save_btn.setFixedHeight(28)
        save_btn.clicked.connect(self.accept)
        actions.addWidget(save_btn)
        layout.addLayout(actions)

        # Estilo del diálogo
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
        
        # Inicializar popup de configuración
        self.config_popup = None
        
        self.setup_ui()
        self.setup_styles()
        self.setup_shortcuts()

    def setup_ui(self):
        """Configura la interfaz de la sección de prompt"""
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)  # Reducido de 16 a 12
        layout.setSpacing(8)  # Reducido de 10 a 8
        
        # Título - tamaño reducido
        title_label = QLabel("Prompt generado")
        title_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))  # Reducido de 14 a 12
        layout.addWidget(title_label)
        
        # Textarea para el prompt - altura y fuente reducidas
        self.prompt_text = QTextEdit()
        self.prompt_text.setFixedHeight(80)  # Reducido de 120 a 80
        self.prompt_text.setFont(QFont("Courier New", 10))  # Reducido de 11 a 10
        self.prompt_text.setPlaceholderText("Aquí aparecerá el prompt generado...")
        self.prompt_text.setReadOnly(False)  # Permitir edición manual
        layout.addWidget(self.prompt_text)
        
        # Botones de acción
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(8)  # Reducido de 10 a 8
        
        self.copy_btn = QPushButton("Copiar")
        self.copy_btn.setFixedSize(100, 32)
        self.copy_btn.clicked.connect(self.copy_prompt)
        buttons_layout.addWidget(self.copy_btn)
        
        self.export_btn = QPushButton("Exportar")
        self.export_btn.setFixedSize(100, 32)
        self.export_btn.clicked.connect(self.export_prompt)
        buttons_layout.addWidget(self.export_btn)
        
        # Espacio flexible para empujar el botón de configuración a la derecha
        buttons_layout.addStretch()
        
        # Botón de configuración (solo ícono)
        self.config_btn = QPushButton()
        self.config_btn.setFixedSize(32, 32)  # Botón cuadrado más pequeño
        self.config_btn.setToolTip("Configuración")
        self.config_btn.clicked.connect(self.open_config)
        
        # Configurar ícono de tuerca (usando texto Unicode como fallback)
        try:
            # Intentar cargar ícono desde archivo si existe
            icon_path = "assets/icons/config.png"
            if os.path.exists(icon_path):
                self.config_btn.setIcon(QIcon(icon_path))
            else:
                # Usar símbolo Unicode de tuerca como fallback
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
            # Fallback final: texto simple
            self.config_btn.setText("⚙")
        
        buttons_layout.addWidget(self.config_btn)
        
        layout.addLayout(buttons_layout)
        
        # Sección de negative prompt
        self.setup_negative_prompt(layout)

    def setup_negative_prompt(self, layout):
        """Configura la sección de negative prompt colapsable"""
        # Frame para negative prompt
        self.negative_frame = QFrame()
        negative_layout = QVBoxLayout(self.negative_frame)
        negative_layout.setContentsMargins(0, 0, 0, 0)
        negative_layout.setSpacing(4)  # Reducido de 6 a 4
        
        # Barra de cabecera: botones guardados (izquierda) + toggle + guardar (derecha)
        header_bar = QHBoxLayout()
        header_bar.setContentsMargins(6, 4, 6, 0)
        header_bar.setSpacing(6)

        # Botón para expandir/contraer
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
        # Colocar el título primero, sin stretch, para que los botones queden justo a su derecha
        header_bar.addWidget(self.negative_toggle)

        # Contenedor de botones guardados: se coloca a la derecha del título
        self.saved_neg_container = QWidget()
        self.saved_neg_layout = QHBoxLayout(self.saved_neg_container)
        self.saved_neg_layout.setContentsMargins(0, 0, 0, 0)
        self.saved_neg_layout.setSpacing(4)
        header_bar.addWidget(self.saved_neg_container)

        # Luego un stretch para empujar el botón de guardar a la esquina derecha
        header_bar.addStretch()

        # Botón de guardar Negative Prompt (esquina superior derecha)
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
        
        # Textarea para negative prompt - altura reducida
        self.negative_text = QTextEdit()
        self.negative_text.setFixedHeight(60)  # Reducido de 80 a 60
        self.negative_text.setFont(QFont("Courier New", 9))  # Reducido de 10 a 9
        default_negative = self.neg_store.get_setting("default_negative_prompt", 
                                                   "blurry, low quality, distorted, deformed, ugly, bad anatomy")
        self.negative_text.setPlainText(default_negative)
        negative_layout.addWidget(self.negative_text)
        
        # Inicialmente oculto
        self.negative_text.hide()
        self.negative_expanded = False
        
        # Cargar y renderizar botones guardados
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
        # Ctrl+C para copiar
        copy_shortcut = QShortcut(QKeySequence("Ctrl+C"), self)
        copy_shortcut.activated.connect(self.copy_prompt)
        
        
        # Ctrl+E para exportar
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


    def export_prompt(self):
        """Exporta el prompt en formato TXT con diálogo de guardado"""
        prompt_content = self.prompt_text.toPlainText()
        negative_content = self.negative_text.toPlainText()
        
        if prompt_content and prompt_content != "Aquí aparecerá el prompt generado...":
            try:
                # Obtener el personaje seleccionado desde el main window
                main_window = self.window()  # Obtiene la ventana principal
                current_character = None
                
                # Intentar obtener el personaje actual desde el sidebar
                if hasattr(main_window, 'sidebar'):
                    if hasattr(main_window.sidebar, 'character_list') and main_window.sidebar.character_list.currentItem():
                        current_character = main_window.sidebar.character_list.currentItem().data(Qt.ItemDataRole.UserRole)
                
                # Generar nombre de archivo por defecto
                if current_character:
                    # Usar el nombre del personaje
                    safe_character_name = current_character.replace(' ', '_').replace('/', '_').replace('\\', '_')
                    default_filename = f"{safe_character_name}_prompt.txt"
                else:
                    # Fallback al timestamp si no hay personaje seleccionado
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    default_filename = f"prompt_export_{timestamp}.txt"
                
                # Mostrar diálogo de guardado
                filename, _ = QFileDialog.getSaveFileName(
                    self,
                    "Exportar Prompt",
                    default_filename,
                    "Archivos de texto (*.txt);;Todos los archivos (*.*)"
                )
                
                if filename:  # Si el usuario no canceló
                    # Asegurar que tenga extensión .txt
                    if not filename.lower().endswith('.txt'):
                        filename += '.txt'
                    
                    # Escribir el archivo
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
        
        # Restaurar después de 2 segundos
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

    # -----------------------------
    # Gestión de Negative Prompts guardados
    # -----------------------------
    def refresh_saved_negative_buttons(self):
        """Reconstruye los botones numerados según los negative prompts guardados."""
        # Limpiar layout existente
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
            # Sin tooltip al pasar el mouse
            btn.setToolTip("")
            # Clic izquierdo: cargar prompt
            btn.clicked.connect(lambda checked=False, idx=i: self.on_saved_button_clicked(idx))
            # Right-click: menú contextual para editar/eliminar
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
        """Muestra un menú contextual para editar o eliminar el prompt guardado."""
        menu = QMenu(self)
        edit_action = menu.addAction("Editar")
        delete_action = menu.addAction("Eliminar")
        action = menu.exec(button.mapToGlobal(button.rect().bottomLeft()))
        if action == edit_action:
            self.edit_saved_negative_prompt(index)
        elif action == delete_action:
            self.delete_saved_negative_prompt(index)

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
        # Solo botón de confirmación, cancelar con la "X" de la ventana
        confirm.setStandardButtons(QMessageBox.StandardButton.Yes)
        # Localizar el texto del botón
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
            # Si ya está abierto, cerrarlo
            self.config_popup.hide()
            return
        
        # Crear el popup si no existe
        if not self.config_popup:
            self.create_config_popup()
        
        # Posicionar el popup al lado del botón
        self.position_config_popup()
        
        # Mostrar el popup
        self.config_popup.show()
        self.config_popup.raise_()
    
    def create_config_popup(self):
        """Crea la ventana popup de configuración"""
        self.config_popup = QFrame(self)
        self.config_popup.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.config_popup.setFixedSize(200, 150)
        
        # Layout del popup
        popup_layout = QVBoxLayout(self.config_popup)
        popup_layout.setContentsMargins(8, 8, 8, 8)
        popup_layout.setSpacing(4)
        
        # Título del popup
        title_label = QLabel("Configuración")
        title_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        popup_layout.addWidget(title_label)
        
        # Lista de opciones con scroll
        self.config_list = QListWidget()
        self.config_list.setMaximumHeight(100)
        
        # Agregar opciones
        options = ["CopyCategories", "Opción 2 (por implementar)", "Opción 3 (por implementar)", "Opción 4 (por implementar)", "Opción 5 (por implementar)"]
        for option in options:
            self.config_list.addItem(option)
        
        # Conectar señal de selección
        self.config_list.itemClicked.connect(self.on_config_option_selected)
        
        popup_layout.addWidget(self.config_list)
        
        # Estilo del popup
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
        
        # Obtener la posición del botón de configuración
        button_pos = self.config_btn.mapToGlobal(self.config_btn.rect().topRight())
        
        # Ajustar posición para que aparezca al lado derecho del botón
        popup_x = button_pos.x() - self.config_popup.width() + 10
        popup_y = button_pos.y()
        
        # Asegurar que el popup no se salga de la pantalla
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

    def on_config_option_selected(self, item):
        """Maneja la selección de una opción de configuración"""
        option_text = item.text()
        print(f"Opción seleccionada: {option_text}")
        
        # Cerrar el popup después de seleccionar
        self.config_popup.hide()
        
        # Implementar acciones específicas para cada opción
        if option_text == "CopyCategories":
            self.copy_categories()
        elif "por implementar" in option_text:
            self.show_feedback(self.config_btn, "Pendiente", error=False)
            print(f"Funcionalidad pendiente: {option_text}")
        else:
            # Mostrar feedback genérico para otras opciones
            self.show_feedback(self.config_btn, "✓", error=False)

        # Aquí se implementará la lógica específica para cada opción
        # TODO: Implementar acciones específicas para cada opción
    def mousePressEvent(self, event):
        """Cierra el popup si se hace clic fuera de él"""
        if self.config_popup and self.config_popup.isVisible():
            if not self.config_popup.geometry().contains(event.globalPosition().toPoint()):
                self.config_popup.hide()
        super().mousePressEvent(event)
