from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QScrollArea, QWidget, QHBoxLayout,
    QPushButton, QLineEdit, QMessageBox, QFrame, QSizePolicy, QFileDialog,
    QApplication, QToolButton
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QDrag, QPixmap, QPainter, QColor, QKeySequence, QImage, QShortcut
import os
import json
import shutil
import re

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

        # Botón para cargar/actualizar imagen del tag
        img_btn = QPushButton("🖼️")
        img_btn.setFixedWidth(34)
        img_btn.setToolTip("Asignar imagen de referencia al tag")
        img_btn.setStyleSheet("background-color: #bbf7d0; color: #065f46; border-radius: 8px;")
        img_btn.clicked.connect(self.on_image_clicked)
        layout.addWidget(img_btn)
        
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

    def on_image_clicked(self):
        """Abre el diálogo avanzado para asignar/gestionar imagen del tag"""
        self.parent_dialog.open_tag_image_dialog(self.tag)
    
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
        # Rutas para imágenes de tags
        self.project_root = os.path.dirname(os.path.dirname(__file__))
        self.tag_images_dir = os.path.join(self.project_root, "data", "tag_images")
        # Nombre representativo del índice de imágenes por tag
        self.tag_images_index = os.path.join(self.tag_images_dir, "tag_images_index.json")
        # Compatibilidad con nombre legado
        self._tag_images_index_legacy = os.path.join(self.tag_images_dir, "index.json")
        self._tag_index_cache = None
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

    # -------------------- Diálogo para imagen por tag --------------------
    def open_tag_image_dialog(self, tag):
        dlg = TagImageDialog(self, self.category_name, tag)
        dlg.exec()

    # Utilidades de imágenes para tags
    def _category_key(self):
        return self.category_name.lower().replace(" ", "_")

    def _normalize_tag(self, tag):
        return re.sub(r"[^a-z0-9_\-]", "", tag.lower().replace(" ", "_"))

    def _load_index(self):
        if self._tag_index_cache is not None:
            return self._tag_index_cache
        try:
            if os.path.isfile(self.tag_images_index):
                with open(self.tag_images_index, "r", encoding="utf-8") as f:
                    self._tag_index_cache = json.load(f)
            elif os.path.isfile(self._tag_images_index_legacy):
                # Migración: cargar archivo legado y persistir con el nuevo nombre
                with open(self._tag_images_index_legacy, "r", encoding="utf-8") as f:
                    self._tag_index_cache = json.load(f)
                try:
                    self._save_index(self._tag_index_cache)
                except Exception:
                    pass
            else:
                self._tag_index_cache = {}
        except Exception:
            self._tag_index_cache = {}
        return self._tag_index_cache

    def _save_index(self, idx):
        os.makedirs(self.tag_images_dir, exist_ok=True)
        with open(self.tag_images_index, "w", encoding="utf-8") as f:
            json.dump(idx, f, ensure_ascii=False, indent=2)
        self._tag_index_cache = idx

    def choose_tag_image(self, tag):
        """Abre diálogo de archivo y asigna imagen al tag"""
        # Mantener para compatibilidad, ahora abre el diálogo avanzado
        self.open_tag_image_dialog(tag)

    def edit_tag(self, old_tag, new_tag):
        """Edita un tag existente"""
        if new_tag and new_tag not in self.tags:
            idx_pos = self.tags.index(old_tag)
            self.tags[idx_pos] = new_tag

            # Preservar imagen asociada al tag si existe
            try:
                idx = self._load_index()
                category_key = self._category_key()
                old_norm = self._normalize_tag(old_tag)
                new_norm = self._normalize_tag(new_tag)

                # Si el normalizado no cambia, no hacer nada
                if old_norm != new_norm:
                    old_key = f"{category_key}/{old_norm}"
                    new_key = f"{category_key}/{new_norm}"
                    rel = idx.get(old_key)
                    # Solo migrar si había una imagen asociada al antiguo y el nuevo aún no existe
                    if rel and new_key not in idx:
                        try:
                            # Renombrar archivo para mantener consistencia de nombre
                            abs_old = os.path.join(self.project_root, "data", rel)
                            ext = os.path.splitext(rel)[1].lower()
                            new_rel = os.path.join("tag_images", category_key, f"{new_norm}{ext}")
                            abs_new = os.path.join(self.project_root, "data", new_rel)
                            os.makedirs(os.path.dirname(abs_new), exist_ok=True)
                            if os.path.isfile(abs_old):
                                # Si el destino existe (raro), sobreescribir moviendo
                                if os.path.isfile(abs_new):
                                    try:
                                        os.remove(abs_new)
                                    except Exception:
                                        pass
                                shutil.move(abs_old, abs_new)
                                idx[new_key] = new_rel.replace("\\", "/")
                            else:
                                # Si falta archivo, al menos mantener la referencia antigua
                                idx[new_key] = rel.replace("\\", "/")
                            # Eliminar clave antigua para evitar duplicados
                            try:
                                del idx[old_key]
                            except Exception:
                                pass
                            self._save_index(idx)
                            # Invalidar caché en la tarjeta de categoría para refrescar tooltips
                            try:
                                parent_card = self.parent()
                                if parent_card and hasattr(parent_card, "invalidate_tag_image_cache"):
                                    parent_card.invalidate_tag_image_cache()
                            except Exception:
                                pass
                        except Exception:
                            # Fallback silencioso: no romper edición por error en migración de imagen
                            pass

            except Exception:
                # No bloquear edición por errores de índice
                pass

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


class TagImageDialog(QDialog):
    """Diálogo para asignar/pegar/quitar imagen de un tag"""
    def __init__(self, parent_dialog: TagsDialog, category_name: str, tag: str):
        super().__init__(parent_dialog)
        self.setWindowTitle(f"Imagen para '{tag}'")
        self.setMinimumWidth(420)
        self.parent_dialog = parent_dialog
        self.category_name = category_name
        self.tag = tag
        self._current_pixmap: QPixmap | None = None
        self._current_ext: str | None = None  # .png/.jpg elegido al guardar
        self._existing_rel: str | None = None
        # Reglas de compresión por defecto
        self.MAX_DIM = 512  # tamaño máximo por lado
        self.TARGET_MAX_SIZE_KB = 300  # tamaño objetivo máximo en KB

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        self.preview = QLabel("Sin imagen")
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview.setStyleSheet("color:#a0a0a0; border:1px dashed #404040; border-radius:8px; padding:8px;")
        self.preview.setMinimumHeight(180)
        # Importante: NO deformar la imagen. No usar setScaledContents.
        # Permitimos que el contenedor se adapte al contenido.
        layout.addWidget(self.preview)

        hint = QLabel("Puedes seleccionar archivo o pegar con Ctrl+V")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint.setStyleSheet("color:#a0a0a0; font-style:italic;")
        layout.addWidget(hint)

        btns = QHBoxLayout()
        select_btn = QToolButton()
        select_btn.setText("📁")
        select_btn.setToolTip("Seleccionar archivo…")
        select_btn.setFixedSize(28, 28)
        select_btn.clicked.connect(self.select_file)
        self.remove_btn = QToolButton()
        self.remove_btn.setText("🗑️")
        self.remove_btn.setToolTip("Quitar imagen")
        self.remove_btn.setFixedSize(28, 28)
        self.remove_btn.setStyleSheet("background-color:#fecaca; color:#991b1b; border-radius:8px;")
        self.remove_btn.clicked.connect(self.remove_image)
        self.remove_btn.setEnabled(False)
        btns.addWidget(select_btn)
        btns.addStretch(1)
        btns.addWidget(self.remove_btn)
        layout.addLayout(btns)

        action_row = QHBoxLayout()
        save_btn = QPushButton("Guardar")
        save_btn.setStyleSheet("background-color:#1e3a8a; color:white; border-radius:8px; padding:6px 18px;")
        save_btn.clicked.connect(self.save_image)
        action_row.addStretch(1)
        action_row.addWidget(save_btn)
        layout.addLayout(action_row)

        # Atajo Ctrl+V
        self._paste_shortcut = QShortcut(QKeySequence("Ctrl+V"), self)
        self._paste_shortcut.activated.connect(self.paste_from_clipboard)

        # Cargar existente si hubiera
        self.load_existing()

    def _category_key(self):
        return self.parent_dialog._category_key()

    def _normalize_tag(self, tag):
        return self.parent_dialog._normalize_tag(tag)

    def load_existing(self):
        idx = self.parent_dialog._load_index()
        key = f"{self._category_key()}/{self._normalize_tag(self.tag)}"
        rel = idx.get(key)
        if rel:
            abs_path = os.path.join(self.parent_dialog.project_root, "data", rel)
            if os.path.isfile(abs_path):
                pix = QPixmap(abs_path)
                if not pix.isNull():
                    self._existing_rel = rel
                    self._current_pixmap = pix
                    self._current_ext = os.path.splitext(rel)[1].lower()
                    self._update_preview()
                    self.remove_btn.setEnabled(True)

    def _update_preview(self):
        if self._current_pixmap is None:
            self.preview.setText("Sin imagen")
            self.preview.setPixmap(QPixmap())
        else:
            # Mantener tamaño original si cabe; si no, reducir manteniendo aspecto.
            pix = self._current_pixmap
            avail_w = max(240, self.preview.width())
            avail_h = max(180, self.preview.height())
            if pix.width() > avail_w or pix.height() > avail_h:
                scaled = pix.scaled(avail_w, avail_h, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            else:
                scaled = pix
            self.preview.setText("")
            self.preview.setPixmap(scaled)
            # Adaptar el contenedor al contenido para evitar estirar horizontalmente
            self.preview.adjustSize()

    def resizeEvent(self, event):
        # Recalcular solo reducción si el diálogo cambia de tamaño
        super().resizeEvent(event)
        if self._current_pixmap:
            self._update_preview()

    def select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar imagen de referencia",
            "",
            "Imágenes (*.png *.jpg *.jpeg)"
        )
        if not file_path:
            return
        ext = os.path.splitext(file_path)[1].lower()
        if ext not in [".png", ".jpg", ".jpeg"]:
            QMessageBox.warning(self, "Formato no soportado", "Usa PNG o JPG/JPEG.")
            return
        pix = QPixmap(file_path)
        if pix.isNull():
            QMessageBox.warning(self, "Error", "No se pudo cargar la imagen seleccionada.")
            return
        self._current_pixmap = pix
        self._current_ext = ext
        self._update_preview()

    def paste_from_clipboard(self):
        cb = QApplication.clipboard()
        img: QImage = cb.image()
        pix = None
        if img and not img.isNull():
            pix = QPixmap.fromImage(img)
        else:
            # Fallback por si el portapapeles expone pixmap directamente
            pix = cb.pixmap()
        if not pix or pix.isNull():
            QMessageBox.warning(self, "Portapapeles vacío", "No hay imagen en el portapapeles.")
            return
        self._current_pixmap = pix
        # Por defecto guardamos como PNG si viene del portapapeles
        self._current_ext = ".png"
        self._update_preview()

    def save_image(self):
        if not self._current_pixmap:
            QMessageBox.warning(self, "Sin imagen", "Selecciona o pega una imagen antes de guardar.")
            return
        try:
            idx = self.parent_dialog._load_index()
            category_key = self._category_key()
            normalized_tag = self._normalize_tag(self.tag)
            os.makedirs(os.path.join(self.parent_dialog.tag_images_dir, category_key), exist_ok=True)

            # Preparar imagen: escalar y decidir formato según alpha
            img, fmt, chosen_ext = self._prepare_image_for_save(self._current_pixmap)
            dest_rel = os.path.join("tag_images", category_key, f"{normalized_tag}{chosen_ext}")
            dest_abs = os.path.join(self.parent_dialog.project_root, "data", dest_rel)

            # Guardar con calidad/compression y ajustar si excede el tamaño objetivo
            if fmt == "JPEG":
                for q in [80, 70, 60, 50]:
                    if not img.save(dest_abs, fmt, q):
                        continue
                    if os.path.isfile(dest_abs) and (os.path.getsize(dest_abs) / 1024.0) <= self.TARGET_MAX_SIZE_KB:
                        break
                # Si aún supera, dejar último guardado (50) como fallback
            elif fmt == "PNG":
                # Para PNG, el parámetro "quality" es el nivel de compresión (0-9)
                img.save(dest_abs, fmt, 9)
            else:
                # Fallback genérico
                img.save(dest_abs)

            key = f"{category_key}/{normalized_tag}"
            idx[key] = dest_rel.replace("\\", "/")
            self.parent_dialog._save_index(idx)
            # Invalidar caché de imágenes en la tarjeta de categoría para ver el preview sin reiniciar
            try:
                parent_card = self.parent_dialog.parent()
                if parent_card and hasattr(parent_card, "invalidate_tag_image_cache"):
                    parent_card.invalidate_tag_image_cache()
            except Exception:
                pass
            QMessageBox.information(self, "Imagen guardada", f"Se guardó y optimizó la imagen para el tag '{self.tag}'.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo guardar la imagen:\n{e}")

    def remove_image(self):
        try:
            # Confirmación antes de quitar
            msg = QMessageBox(self)
            msg.setWindowTitle("Quitar imagen")
            msg.setText("¿Seguro que deseas quitar la imagen del tag?")
            msg.setIcon(QMessageBox.Icon.Warning)
            yes_btn = msg.addButton("Sí", QMessageBox.ButtonRole.YesRole)
            no_btn = msg.addButton("No", QMessageBox.ButtonRole.NoRole)
            msg.exec()
            if msg.clickedButton() != yes_btn:
                return
            idx = self.parent_dialog._load_index()
            key = f"{self._category_key()}/{self._normalize_tag(self.tag)}"
            rel = idx.get(key)
            if rel:
                abs_path = os.path.join(self.parent_dialog.project_root, "data", rel)
                if os.path.isfile(abs_path):
                    try:
                        os.remove(abs_path)
                    except Exception:
                        pass
                idx.pop(key, None)
                self.parent_dialog._save_index(idx)
            self._current_pixmap = None
            self._current_ext = None
            self._existing_rel = None
            self._update_preview()
            self.remove_btn.setEnabled(False)
            # Invalidar caché de imágenes en la tarjeta de categoría
            try:
                parent_card = self.parent_dialog.parent()
                if parent_card and hasattr(parent_card, "invalidate_tag_image_cache"):
                    parent_card.invalidate_tag_image_cache()
            except Exception:
                pass
            QMessageBox.information(self, "Imagen quitada", "Se quitó la imagen del tag.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo quitar la imagen:\n{e}")

    def _prepare_image_for_save(self, pixmap: QPixmap):
        """Escala y decide formato/extension según alpha y tamaño."""
        img = pixmap.toImage()
        # Escalar si excede MAX_DIM
        w, h = img.width(), img.height()
        if max(w, h) > self.MAX_DIM:
            img = img.scaled(self.MAX_DIM, self.MAX_DIM, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        # Elegir formato por alpha
        has_alpha = img.hasAlphaChannel()
        if has_alpha:
            return img, "PNG", ".png"
        # Si no tiene alpha, usar JPEG para mejor compresión
        return img, "JPEG", ".jpg"