import os
import json
import re
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QFrame, QPushButton, QToolButton, QSizePolicy, QMenu, QWidgetAction)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap, QIcon

# Constantes
DEFAULT_CARD_COLOR = "#252525"
ICON_EDIT = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "assets", "icons", "edit.png")
ICON_SAVE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "assets", "icons", "save.png")

class TagButton(QPushButton):
    def __init__(self, tag, parent_card):
        super().__init__(tag)
        self.tag = tag
        self.parent_card = parent_card
        self.setStyleSheet("""
            QPushButton {
                background-color: #404040;
                border: 1px solid #6366f1;
                border-radius: 12px;
                padding: 4px 8px;
                color: #e0e0e0;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #6366f1;
                color: #fff;
            }
        """)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.parent_card.modify_tag_importance(self.tag, increase=True)
        elif event.button() == Qt.MouseButton.RightButton:
            self.parent_card.modify_tag_importance(self.tag, increase=False)

class CategoryCard(QFrame):
    request_rename = pyqtSignal(str, str)  # (old_name, new_name)
    value_changed = pyqtSignal()  # Nueva señal para cuando cambie el valor

    def __init__(self, name, icon=None, tags=None, prompt_generator=None, bg_color=DEFAULT_CARD_COLOR):
        super().__init__()
        self.prompt_generator = prompt_generator
        self.category_name = name
        self.bg_color = bg_color
        self.icon = icon
        self.is_editing = False
        self.unsaved_changes = False
        self.tags = tags or []
        self.setup_ui(name, tags)
        self.setup_styles()
        self.setup_debounce()

    def setup_ui(self, name, tags):
        """Configura la interfaz de la tarjeta"""
        # Hacer la tarjeta responsiva
        self.setMinimumSize(300, 100)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(4)
        
        # --- Layout horizontal para título y botón de editar ---
        title_layout = QHBoxLayout()
        title_layout.setSpacing(8)
        
        # Título de la categoría
        self.title_label = QLabel(name)
        self.title_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.title_label.setStyleSheet("color: #e0e0e0;")
        self.title_label.setWordWrap(True)
        title_layout.addWidget(self.title_label, 1)
        
        # Campo de edición (oculto por defecto)
        self.title_edit = QLineEdit(name)
        self.title_edit.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.title_edit.hide()
        self.title_edit.returnPressed.connect(self.save_category_name)
        self.title_edit.textChanged.connect(self.on_title_edited)
        title_layout.addWidget(self.title_edit, 1)
    
        # Botón de editar/guardar - SIN ICONO INICIAL
        self.edit_btn = QToolButton()
        self.edit_btn.setText("✏️")  # Usar emoji como fallback
        self.edit_btn.setToolTip("Editar nombre de la categoría")
        self.edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.edit_btn.setFixedSize(22, 22)
        self.edit_btn.clicked.connect(self.toggle_edit_mode)
        title_layout.addWidget(self.edit_btn)
    
        layout.addLayout(title_layout)
        
        # Input para el valor
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Añadir valor...")
        self.input_field.textChanged.connect(self.on_input_change)
        layout.addWidget(self.input_field)
        
        # Guardar los tags para poder actualizarlos después
        self.tags = tags or []
        self.tag_click_counts = {}
        
        # Crear la interfaz de tags
        self.update_tags_ui()

    def update_tags_ui(self, tags=None):
        """Actualiza la interfaz de los tags en la tarjeta"""
        # Limpiar el layout de tags existente
        layout = self.layout()
        
        # Buscar el layout de tags (último layout en la tarjeta)
        # Pero asegurarse de no eliminar el layout del título
        for i in reversed(range(layout.count())):
            item = layout.itemAt(i)
            # Solo eliminar el layout de tags, no el del título ni el input
            if isinstance(item, QHBoxLayout) and i > 1:  # El título está en la posición 0, el input en 1
                tags_layout = item
                # Limpiar este layout
                while tags_layout.count():
                    widget_item = tags_layout.takeAt(0)
                    if widget_item.widget():
                        widget_item.widget().setParent(None)
                # Eliminar el layout vacío
                layout.removeItem(tags_layout)
                break
        
        # Crear nuevo layout para los tags
        tags_layout = QHBoxLayout()
        tags_layout.setContentsMargins(0, 0, 0, 0)
        tags_layout.setSpacing(6)
        
        # Si se proporcionan nuevos tags, actualizar la lista interna
        if tags is not None:
            self.tags = tags
            
        # Recrear los controles de tags: botón "All tags" con menú y botón de tuerquita
        self.tag_click_counts = {}
        if self.tags:
            # Inicializar contadores de importancia para todos los tags
            for tag in self.tags:
                self.tag_click_counts[tag] = 0

            # Botón "All tags" con menú interactivo
            all_tags_btn = QToolButton()
            all_tags_btn.setText("All tags")
            all_tags_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            all_tags_btn.setToolTip(", ".join(self.tags) if self.tags else "Sin tags")
            all_tags_btn.setStyleSheet(
                """
                QToolButton {
                    background-color: #6366f1;
                    color: #fff;
                    border-radius: 10px;
                    padding: 2px 10px;
                    font-size: 10px;
                }
                QToolButton:hover {
                    background-color: #4f46e5;
                }
                """
            )

            menu = QMenu(all_tags_btn)
            menu.setStyleSheet(
                """
                QMenu {
                    background-color: #2b2b2b;
                    border: 1px solid #404040;
                    padding: 4px;
                }
                /* Estilo por defecto para items estándar del menú */
                QMenu::item {
                    padding: 6px 10px;
                    color: #e0e0e0;
                    background-color: transparent;
                }
                QMenu::item:selected {
                    background-color: transparent; /* Evitar gris por defecto */
                }
                """
            )

            # Item de menú personalizado para permitir clic izquierdo/derecho
            class TagMenuItem(QWidget):
                def __init__(self, tag_text, parent_card):
                    super().__init__()
                    self.tag_text = tag_text
                    self.parent_card = parent_card
                    row = QHBoxLayout(self)
                    row.setContentsMargins(8, 4, 8, 4)
                    row.setSpacing(8)
                    label = QLabel(tag_text)
                    label.setStyleSheet("color: #e0e0e0; font-size: 11px;")
                    row.addWidget(label)
                    row.addStretch()
                    # Estilos visuales (base, hover, pressed)
                    self._style_base = (
                        "QWidget { background-color: transparent; } "
                        "QLabel { color: #e0e0e0; font-size: 11px; }"
                    )
                    # Verde jade para hover y click
                    self._style_hover = (
                        "QWidget { background-color: #00A36C; border-radius: 6px; } "
                        "QLabel { color: #ffffff; font-size: 11px; }"
                    )
                    self._style_pressed = (
                        "QWidget { background-color: #008a57; border-radius: 6px; } "
                        "QLabel { color: #ffffff; font-size: 11px; }"
                    )
                    self.setStyleSheet(self._style_base)

                def mousePressEvent(self, event):
                    if event.button() == Qt.MouseButton.LeftButton:
                        # Feedback visual de click
                        self.setStyleSheet(self._style_pressed)
                        self.parent_card.modify_tag_importance(self.tag_text, increase=True)
                        from PyQt6.QtCore import QTimer
                        QTimer.singleShot(120, lambda: self.setStyleSheet(self._style_hover))
                    elif event.button() == Qt.MouseButton.RightButton:
                        self.setStyleSheet(self._style_pressed)
                        self.parent_card.modify_tag_importance(self.tag_text, increase=False)
                        from PyQt6.QtCore import QTimer
                        QTimer.singleShot(120, lambda: self.setStyleSheet(self._style_hover))
                    event.accept()

                def enterEvent(self, event):
                    self.setStyleSheet(self._style_hover)
                    super().enterEvent(event)

                def leaveEvent(self, event):
                    self.setStyleSheet(self._style_base)
                    super().leaveEvent(event)

            for tag in self.tags:
                widget = TagMenuItem(tag, self)
                action = QWidgetAction(menu)
                action.setDefaultWidget(widget)
                menu.addAction(action)

            all_tags_btn.setMenu(menu)
            all_tags_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
            tags_layout.addWidget(all_tags_btn)

            # Botón con icono de tuerquita para abrir el diálogo de tags
            gear_btn = QToolButton()
            gear_btn.setText("⚙️")
            gear_btn.setToolTip("Editar lista de tags")
            gear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            gear_btn.setFixedHeight(22)
            # Estilos jade (base y activo) para feedback visual
            self._gear_style_base = (
                "QToolButton {"
                " background-color: #404040;"
                " color: #fff;"
                " border-radius: 10px;"
                " padding: 0px 8px;"
                " font-size: 12px;"
                "}"
                " QToolButton:hover {"
                " background-color: #00A36C;"
                " color: #ffffff;"
                "}"
            )
            self._gear_style_active = (
                "QToolButton {"
                " background-color: #008a57;"
                " color: #ffffff;"
                " border-radius: 10px;"
                " padding: 0px 8px;"
                " font-size: 12px;"
                "}"
                " QToolButton:hover {"
                " background-color: #008a57;"
                " color: #ffffff;"
                "}"
            )
            gear_btn.setStyleSheet(self._gear_style_base)
            self.gear_btn = gear_btn
            gear_btn.clicked.connect(self.show_tags_dialog)
            tags_layout.addWidget(gear_btn)
    
        tags_layout.addStretch()
        layout.addLayout(tags_layout)

    def show_tags_dialog(self):
        from ..tags_dialog import TagsDialog

        TAGS_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "tags.json")
        key = self.category_name.lower().replace(" ", "_")
        with open(TAGS_PATH, "r", encoding="utf-8") as f:
            tags_data = json.load(f)
            tags = tags_data.get(key, [])
        dlg = TagsDialog(self.category_name, tags, self)
        # Activar resaltado jade mientras el diálogo esté abierto
        if hasattr(self, "gear_btn") and hasattr(self, "_gear_style_active"):
            self.gear_btn.setStyleSheet(self._gear_style_active)
        if dlg.exec():
            # Si el diálogo se cerró con aceptar, actualizar los tags en la UI con los modificados
            updated_tags = getattr(dlg, "tags", tags)
            self.update_tags_ui(updated_tags)
        # Restablecer estilo base al cerrar el diálogo (aceptar o cancelar)
        if hasattr(self, "gear_btn") and hasattr(self, "_gear_style_base"):
            self.gear_btn.setStyleSheet(self._gear_style_base)

    def setup_styles(self):
        """Configura los estilos de la tarjeta"""
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {self.bg_color};
                border: 1px solid #404040;
                border-radius: 8px;
            }}
            QLineEdit {{
                background-color: #1a1a1a;
                border: 1px solid #404040;
                border-radius: 6px;
                color: #e0e0e0;
                padding: 6px;
                font-size: 11px;
            }}
            QLineEdit:focus {{
                border: 1px solid #6366f1;
            }}
            QLabel {{
                color: #e0e0e0;
            }}
        """)

    def setup_debounce(self):
        """Configura el debounce para el input"""
        self.debounce_timer = QTimer()
        self.debounce_timer.setSingleShot(True)
        self.debounce_timer.timeout.connect(self.update_prompt)

    def on_input_change(self):
        """Maneja cambios en el input con debounce"""
        self.debounce_timer.start(500)  # 500ms debounce

    def update_prompt(self):
        """Actualiza el prompt basado en el valor del input"""
        if not self.prompt_generator:
            return
        
        value = self.input_field.text()
        if self.prompt_generator:
            validated_value = self.prompt_generator.validate_input(value)
            # En el método donde se llama a update_category, agregar el mapeo:
            # Convertir nombre de categoría al formato snake_case
            snake_case_name = self.category_name.lower().replace(" ", "_")
            self.prompt_generator.update_category(snake_case_name, validated_value)
            self.value_changed.emit()  # Emitir señal cuando cambie el valor

    def toggle_edit_mode(self):
        """Alterna entre modo edición y modo vista"""
        if not self.is_editing:
            # Entrar en modo edición
            self.is_editing = True
            self.title_label.hide()
            self.title_edit.show()
            self.title_edit.setFocus()
            self.title_edit.selectAll()
            
            # Usar solo emoji/texto - NO crear QIcon
            self.edit_btn.setText("💾")
            self.edit_btn.setToolTip("Guardar cambios")
        else:
            # Salir del modo edición sin guardar
            self.cancel_edit_mode()

    def cancel_edit_mode(self):
        """Cancela el modo edición"""
        self.is_editing = False
        self.unsaved_changes = False
        self.title_edit.hide()
        self.title_label.show()
        self.title_edit.setText(self.category_name)  # Restaurar texto original
        self.title_edit.setStyleSheet("")  # Limpiar estilos de error
        
        # Usar solo emoji/texto - NO crear QIcon
        self.edit_btn.setText("✏️")
        self.edit_btn.setToolTip("Editar nombre de la categoría")
        self.title_edit.setStyleSheet("")

    def save_category_name(self):
        """Guarda el nuevo nombre de la categoría"""
        new_name = self.title_edit.text().strip()
        if new_name and new_name != self.category_name:
            old_name = self.category_name
            self.category_name = new_name
            self.title_label.setText(new_name)
            self.request_rename.emit(old_name, new_name)
        
        self.cancel_edit_mode()

    def on_title_edited(self):
        # Si el usuario edita pero no guarda, subraya en rojo
        if self.title_edit.text().strip() != self.category_name:
            self.unsaved_changes = True
            self.title_edit.setStyleSheet("border-bottom: 2px solid red;")
        else:
            self.unsaved_changes = False
            self.title_edit.setStyleSheet("")

    def modify_tag_importance(self, tag, increase=True):
        count = self.tag_click_counts.get(tag, 0)
        if increase:
            count += 1
        else:
            count -= 1
        count = max(0, count)
        self.tag_click_counts[tag] = count
    
        # Quita versiones anteriores del tag en el input_field
        current = self.input_field.text()
        pattern = re.compile(rf"\(*\s*{re.escape(tag)}\s*\)*,")
        current = pattern.sub("", current).strip()
    
        # Si la importancia es 0, no agregues el tag
        if count > 0:
            # CAMBIO: Primer click sin paréntesis, segundo click en adelante con paréntesis
            if count == 1:
                tag_text = f"{tag},"  # Sin paréntesis en el primer click
            else:
                parentheses_count = count - 1  # Restar 1 para que el segundo click tenga 1 paréntesis
                tag_text = f"{'(' * parentheses_count}{tag}{')' * parentheses_count},"
            
            if current:
                new_text = f"{current} {tag_text}"
            else:
                new_text = tag_text
            self.input_field.setText(new_text.strip())
        else:
            self.input_field.setText(current)

    def get_selected_tags(self):
        """Retorna los tags seleccionados con su importancia"""
        return [tag for tag, count in self.tag_click_counts.items() if count > 0]

    def clear_value(self):
        """Limpia el valor del input y resetea la importancia de los tags."""
        # Vaciar el campo de entrada
        self.input_field.setText("")
        # Resetear contadores de importancia de tags
        self.tag_click_counts = {tag: 0 for tag in self.tags}