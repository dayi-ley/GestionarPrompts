from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QScrollArea, QWidget, QHBoxLayout,
    QPushButton, QLineEdit, QMessageBox, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QDrag, QPixmap, QPainter, QColor
import os
import json

TAGS_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "tags.json")

class DraggableTagWidget(QFrame):
    """Widget de tag que se puede arrastrar para reordenar"""
    def __init__(self, tag, parent=None):
        super().__init__(parent)
        self.tag = tag
        self.parent_dialog = parent
        self.setAcceptDrops(True)
        # Estilos (base y durante arrastre) con verde jade
        self._style_base = (
            "QFrame {"
            " background-color: #404040;"
            " border-radius: 8px;"
            " padding: 4px;"
            "}"
            " QFrame:hover {"
            " background-color: #505050;"
            " border: 1px solid #6366f1;"
            "}"
        )
        self._style_drag = (
            "QFrame {"
            " background-color: #00A36C;"  # verde jade
            " border: 1px solid #12b886;"
            " border-radius: 8px;"
            " padding: 4px;"
            "}"
            " QFrame:hover {"
            " background-color: #00A36C;"
            " border: 1px solid #12b886;"
            "}"
        )
        self.setStyleSheet(self._style_base)
        # Compactar altura y evitar expansión vertical
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setFixedHeight(38)
        
        # Layout horizontal para el contenido del tag
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 1, 8, 1)
        layout.setSpacing(8)
        
        # Campo de texto para editar el tag
        self.tag_edit = QLineEdit(tag)
        self.tag_edit.setStyleSheet("background:#404040; color:#fff; border-radius:8px; padding:4px 10px;")
        self.tag_edit.setMinimumWidth(150)
        self.tag_edit.editingFinished.connect(self.on_edit_finished)
        layout.addWidget(self.tag_edit)
        
        # Botón para eliminar el tag
        del_btn = QPushButton("Eliminar")
        del_btn.setFixedWidth(60)
        del_btn.setStyleSheet("background-color: #fecaca; color: #991b1b; border-radius: 8px;")
        del_btn.clicked.connect(self.on_delete_clicked)
        layout.addWidget(del_btn)
        
        # Indicador de arrastrar
        drag_indicator = QLabel("≡")
        drag_indicator.setStyleSheet("color: #fff; font-size: 16px; font-weight: bold;")
        drag_indicator.setToolTip("Arrastra para reordenar")
        layout.addWidget(drag_indicator)
        
        layout.addStretch()
    
    def on_edit_finished(self):
        """Cuando se termina de editar el tag"""
        new_text = self.tag_edit.text().strip()
        if new_text and new_text != self.tag:
            self.parent_dialog.edit_tag(self.tag, new_text)
            self.tag = new_text
    
    def on_delete_clicked(self):
        """Cuando se hace clic en eliminar"""
        self.parent_dialog.confirm_delete_tag(self.tag)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start_position = event.position().toPoint()
            # Feedback inmediato al seleccionar para arrastrar
            self.setStyleSheet(self._style_drag)

    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            return
        
        # Verificar si se ha movido lo suficiente para iniciar el arrastre
        if (event.position().toPoint() - self.drag_start_position).manhattanLength() < 10:
            return
        
        # Crear un drag
        drag = QDrag(self)
        
        # Crear una imagen del widget para mostrar durante el arrastre
        pixmap = QPixmap(self.size())
        pixmap.fill(QColor(0, 0, 0, 0))
        painter = QPainter(pixmap)
        self.render(painter)
        painter.end()
        
        drag.setPixmap(pixmap)
        drag.setHotSpot(event.position().toPoint())
        
        # Crear un objeto QMimeData y establecer el texto
        from PyQt6.QtCore import QMimeData
        mime_data = QMimeData()
        mime_data.setText(self.tag)
        drag.setMimeData(mime_data)
        
        # Ejecutar el drag (mantener resaltado mientras se arrastra)
        drag.exec(Qt.DropAction.MoveAction)
        # Restaurar estilo base al finalizar el arrastre
        self.setStyleSheet(self._style_base)

    def mouseReleaseEvent(self, event):
        # Si se suelta sin iniciar arrastre, restaurar estilo
        self.setStyleSheet(self._style_base)
        super().mouseReleaseEvent(event)
    
    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()
    
    def dropEvent(self, event):
        source_tag = event.mimeData().text()
        target_tag = self.tag
        
        if source_tag != target_tag:
            self.parent_dialog.move_tag_to(source_tag, target_tag)
            event.acceptProposedAction()

class TagsDialog(QDialog):
    def __init__(self, category_name, tags, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Tags de {category_name}")
        self.setMinimumWidth(400)
        self.setMinimumHeight(350)
        self.category_name = category_name
        self.tags = list(tags)
        self.parent_grid = parent.parent() if parent else None  # Para recargar el grid
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        title = QLabel(f"<b>{self.category_name}</b>")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Instrucciones para el usuario
        instructions = QLabel("Arrastra los tags para reordenarlos")
        instructions.setStyleSheet("color: #a0a0a0; font-style: italic;")
        instructions.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(instructions)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setSpacing(6)
        # Alinear arriba para evitar que los tags se estiren verticalmente
        from PyQt6.QtCore import Qt as _Qt
        self.scroll_layout.setAlignment(_Qt.AlignmentFlag.AlignTop)
        self.scroll.setWidget(self.scroll_content)
        layout.addWidget(self.scroll)

        add_row = QHBoxLayout()
        self.new_tag_edit = QLineEdit()
        self.new_tag_edit.setPlaceholderText("Nuevo tag...")
        add_btn = QPushButton("+")
        add_btn.setStyleSheet("background-color: #bbf7d0; color: #065f46; border-radius: 8px; padding: 4px 12px;")
        add_btn.clicked.connect(self.add_tag)
        add_row.addWidget(self.new_tag_edit)
        add_row.addWidget(add_btn)
        layout.addLayout(add_row)

        # Botón Guardar centrado (sin Cancelar, ya existe la X del diálogo)
        btn_row = QHBoxLayout()
        save_btn = QPushButton("Guardar cambios")
        save_btn.setStyleSheet(
            "QPushButton {"
            " background-color: #1e3a8a;"  # azul oscuro
            " color: white;"
            " border-radius: 8px;"
            " padding: 6px 18px;"
            "}"
            " QPushButton:hover {"
            " background-color: #1d4ed8;"  # azul más claro al hover
            " color: white;"
            "}"
            " QPushButton:pressed {"
            " background-color: #1e40af;"
            " color: white;"
            "}"
        )
        save_btn.clicked.connect(self.save_and_close)
        btn_row.addStretch(1)
        btn_row.addWidget(save_btn)
        btn_row.addStretch(1)
        layout.addLayout(btn_row)

        self.refresh_tags()

    def refresh_tags(self):
        # Limpiar el layout de tags
        for i in reversed(range(self.scroll_layout.count())):
            item = self.scroll_layout.itemAt(i)
            if item:
                widget = item.widget()
                if widget:
                    widget.setParent(None)
                else:
                    while item.count():
                        subitem = item.takeAt(0)
                        if subitem.widget():
                            subitem.widget().setParent(None)
                    self.scroll_layout.removeItem(item)

        # Crear widgets de tag arrastrables
        for tag in self.tags:
            tag_widget = DraggableTagWidget(tag, self)
            self.scroll_layout.addWidget(tag_widget)

    def edit_tag(self, old_tag, new_tag):
        """Edita un tag existente"""
        if new_tag and new_tag not in self.tags:
            idx = self.tags.index(old_tag)
            self.tags[idx] = new_tag
            self.refresh_tags()
        else:
            QMessageBox.warning(self, "Error", "El tag está vacío o ya existe.")

    def confirm_delete_tag(self, tag):
        """Confirma la eliminación de un tag"""
        msg = QMessageBox(self)
        msg.setWindowTitle("Eliminar tag")
        msg.setText(f"¿Seguro que deseas eliminar el tag:\n\n'{tag}'?")
        msg.setIcon(QMessageBox.Icon.Warning)
        yes_btn = msg.addButton("Sí", QMessageBox.ButtonRole.YesRole)
        no_btn = msg.addButton("No", QMessageBox.ButtonRole.NoRole)
        # Más espacio entre botones
        msg.setStyleSheet("""
            QPushButton {
                min-width: 80px;
                padding: 8px 24px;
                margin-left: 16px;
                margin-right: 16px;
                font-size: 13px;
            }
        """)
        msg.exec()
        if msg.clickedButton() == yes_btn:
            self.delete_tag(tag)

    def delete_tag(self, tag):
        """Elimina un tag"""
        if tag in self.tags:
            self.tags.remove(tag)
            self.refresh_tags()

    def move_tag_to(self, source_tag, target_tag):
        """Mueve un tag a la posición de otro tag"""
        if source_tag in self.tags and target_tag in self.tags:
            source_idx = self.tags.index(source_tag)
            target_idx = self.tags.index(target_tag)
            
            # Remover el tag de origen
            tag = self.tags.pop(source_idx)
            
            # Insertar en la posición de destino
            self.tags.insert(target_idx, tag)
            
            # Actualizar la interfaz
            self.refresh_tags()

    def add_tag(self):
        """Añade un nuevo tag"""
        new_tag = self.new_tag_edit.text().strip()
        if new_tag and new_tag not in self.tags:
            self.tags.append(new_tag)
            self.new_tag_edit.clear()
            self.refresh_tags()
        else:
            QMessageBox.warning(self, "Error", "El tag está vacío o ya existe.")

    def save_and_close(self):
        # Guarda los tags en tags.json
        with open(TAGS_PATH, "r+", encoding="utf-8") as f:
            tags_data = json.load(f)
            key = self.category_name.lower().replace(" ", "_")
            tags_data[key] = self.tags
            f.seek(0)
            json.dump(tags_data, f, ensure_ascii=False, indent=2)
            f.truncate()
            
        # Actualiza la tarjeta que abrió este diálogo
        parent_card = self.parent()
        if parent_card and hasattr(parent_card, "update_tags_ui"):
            parent_card.update_tags_ui(self.tags)
            
        # NO recargamos todo el grid, ya que la actualización de la tarjeta individual es suficiente
        # if self.parent_grid and hasattr(self.parent_grid, "reload_categories"):
        #     self.parent_grid.reload_categories()
        self.accept()