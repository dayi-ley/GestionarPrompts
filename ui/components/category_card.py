import os
import json
import re
import math
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QFrame, QPushButton, QToolButton, QSizePolicy, QMenu, QWidgetAction, QApplication, QStyle, QColorDialog, QGridLayout)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPoint
from PyQt6.QtGui import QFont, QPixmap, QIcon, QColor
from ..utils.category_utils import save_category_color

ICON_COLORS = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "assets", "icons", "colors.png")
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
    request_rename = pyqtSignal(str, str)
    value_changed = pyqtSignal()
    request_move_up = pyqtSignal(str)
    request_move_down = pyqtSignal(str)

    def __init__(self, name, icon=None, tags=None, prompt_generator=None, bg_color=DEFAULT_CARD_COLOR):
        super().__init__()
        self.prompt_generator = prompt_generator
        self.category_name = name
        self.bg_color = bg_color
        self.icon = icon
        self.is_editing = False
        self.unsaved_changes = False
        self.is_locked = False
        self.tags = tags or []
        self.setup_ui(name, tags)
        self.setup_styles()
        self.setup_debounce()
        self._tag_image_index = None
        self._tag_pixmap_cache = {}

    def setup_ui(self, name, tags):
        self.setMinimumSize(300, 100)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(4)
        
        title_layout = QHBoxLayout()
        title_layout.setSpacing(8)
        
        self.title_label = QLabel(name)
        self.title_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.title_label.setStyleSheet("color: #e0e0e0;")
        self.title_label.setWordWrap(True)
        title_layout.addWidget(self.title_label, 1)
        
        self.title_edit = QLineEdit(name)
        self.title_edit.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.title_edit.hide()
        self.title_edit.returnPressed.connect(self.save_category_name)
        self.title_edit.textChanged.connect(self.on_title_edited)
        title_layout.addWidget(self.title_edit, 1)
    
        self.edit_btn = QToolButton()
        self.edit_btn.setIcon(QIcon(ICON_EDIT))
        self.edit_btn.setIconSize(self.edit_btn.size())
        self.edit_btn.setToolTip("Editar nombre")
        self.edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.edit_btn.setFixedSize(22, 22)
        self.edit_btn.clicked.connect(self.toggle_edit_mode)
        title_layout.addWidget(self.edit_btn)

        self.move_up_btn = QToolButton()
        try:
            self.move_up_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowUp))
        except Exception:
            self.move_up_btn.setText("⬆️")
        self.move_up_btn.setIconSize(self.move_up_btn.size())
        self.move_up_btn.setToolTip("Mover arriba")
        self.move_up_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.move_up_btn.setFixedSize(22, 22)
        self.move_up_btn.hide()
        self.move_up_btn.clicked.connect(lambda: self.request_move_up.emit(self.category_name))
        title_layout.addWidget(self.move_up_btn)

        self.move_down_btn = QToolButton()
        try:
            self.move_down_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowDown))
        except Exception:
            self.move_down_btn.setText("⬇️")
        self.move_down_btn.setIconSize(self.move_down_btn.size())
        self.move_down_btn.setToolTip("Mover abajo")
        self.move_down_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.move_down_btn.setFixedSize(22, 22)
        self.move_down_btn.hide()
        self.move_down_btn.clicked.connect(lambda: self.request_move_down.emit(self.category_name))
        title_layout.addWidget(self.move_down_btn)
    
        layout.addLayout(title_layout)
        
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Añadir valor...")
        self.input_field.textChanged.connect(self.on_input_change)
        layout.addWidget(self.input_field)
        
        self.tags = tags or []
        self.tag_click_counts = {}
        
        self.update_tags_ui()

    def update_color_button_style(self):
        if hasattr(self, 'color_btn') and self.color_btn is not None:
            bg = self.bg_color if isinstance(self.bg_color, str) else DEFAULT_CARD_COLOR
            self.color_btn.setStyleSheet(
                f"QToolButton {{ background-color: {bg}; border: 1px solid #404040; border-radius: 6px; padding: 0 6px; color: #fff; }}"
            )

    def apply_bg_color(self, color_hex: str):
        self.bg_color = color_hex
        self.setup_styles()
        self.update_color_button_style()

    def choose_color(self):
        current = QColor(self.bg_color) if isinstance(self.bg_color, str) else QColor(DEFAULT_CARD_COLOR)
        color = QColorDialog.getColor(current, self, "Elegir color")
        if color and color.isValid():
            hex_color = color.name()
            self.apply_bg_color(hex_color)
            try:
                save_category_color(self._category_key(), hex_color)
            except Exception:
                pass

    def set_reorder_mode(self, enabled: bool):
        if enabled:
            self.move_up_btn.show()
            self.move_down_btn.show()
        else:
            self.move_up_btn.hide()
            self.move_down_btn.hide()

    def toggle_lock(self):
        self.is_locked = not self.is_locked
        self.update_lock_style()
        
    def update_lock_style(self):
        self.setup_styles()
        
        if hasattr(self, 'lock_btn'):
            if self.is_locked:
                self.lock_btn.setText("🔒")
                self.lock_btn.setToolTip("Bloqueada")
                self.lock_btn.setStyleSheet("""
                    QToolButton {
                        background-color: #d32f2f;
                        color: white;
                        border-radius: 10px;
                        padding: 2px 6px;
                        font-size: 12px;
                    }
                    QToolButton:hover {
                        background-color: #b71c1c;
                    }
                """)
            else:
                self.lock_btn.setText("🔓")
                self.lock_btn.setToolTip("Bloquear")
                self.lock_btn.setStyleSheet("""
                    QToolButton {
                        background-color: #404040;
                        color: #aaaaaa;
                        border-radius: 10px;
                        padding: 2px 6px;
                        font-size: 12px;
                    }
                    QToolButton:hover {
                        background-color: #6366f1;
                        color: white;
                    }
                """)

    def update_tags_ui(self, tags=None):
        layout = self.layout()
        
        for i in reversed(range(layout.count())):
            item = layout.itemAt(i)
            if isinstance(item, QHBoxLayout) and i > 1:
                tags_layout = item
                while tags_layout.count():
                    widget_item = tags_layout.takeAt(0)
                    if widget_item.widget():
                        widget_item.widget().setParent(None)
                layout.removeItem(tags_layout)
                break
        
        tags_layout = QHBoxLayout()
        tags_layout.setContentsMargins(0, 0, 0, 0)
        tags_layout.setSpacing(6)
        
        if tags is not None:
            self.tags = tags
            
        self.tag_click_counts = {}
        if self.tags:
            for tag in self.tags:
                self.tag_click_counts[tag] = 0

            all_tags_btn = QToolButton()
            all_tags_btn.setText("All tags")
            all_tags_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            
            def _build_tags_tooltip(tags, max_items=3, max_chars=80):
                if not tags:
                    return "Sin tags"
                display = ", ".join(tags[:max_items])
                if len(tags) > max_items:
                    display += ", …"
                if len(display) > max_chars:
                    display = display[:max_chars].rstrip(", ") + "…"
                return display
            all_tags_btn.setToolTip(_build_tags_tooltip(self.tags))
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
                QMenu::item {
                    padding: 6px 10px;
                    color: #e0e0e0;
                    background-color: transparent;
                }
                QMenu::item:selected {
                    background-color: transparent;
                }
                """
            )
            menu.setMinimumWidth(200)

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
                    max_width = 130
                    label.setFixedWidth(max_width)
                    metrics = label.fontMetrics()
                    elided = metrics.elidedText(tag_text, Qt.TextElideMode.ElideRight, max_width - 10)
                    label.setText(elided)
                    label.setToolTip(tag_text)
                    row.addWidget(label)
                    row.addStretch()
                    self._style_base = (
                        "QWidget { background-color: transparent; } "
                        "QLabel { color: #e0e0e0; font-size: 11px; }"
                    )
                    self._style_hover = (
                        "QWidget { background-color: #00A36C; border-radius: 6px; } "
                        "QLabel { color: #ffffff; font-size: 11px; }"
                    )
                    self._style_pressed = (
                        "QWidget { background-color: #008a57; border-radius: 6px; } "
                        "QLabel { color: #ffffff; font-size: 11px; }"
                    )
                    self.setStyleSheet(self._style_base)
                    self._preview = None

                def mousePressEvent(self, event):
                    if event.button() == Qt.MouseButton.LeftButton:
                        self.setStyleSheet(self._style_pressed)
                        self.parent_card.modify_tag_importance(self.tag_text, increase=True)
                        from PyQt6.QtCore import QTimer
                        QTimer.singleShot(120, lambda: self.setStyleSheet(self._style_hover))
                    elif event.button() == Qt.MouseButton.RightButton:
                        self.setStyleSheet(self._style_pressed)
                        self.parent_card.modify_tag_importance(self.tag_text, increase=False)
                        from PyQt6.QtCore import QTimer
                        QTimer.singleShot(120, lambda: self.setStyleSheet(self._style_hover))
                    self._hide_preview()
                    event.accept()

                def enterEvent(self, event):
                    self.setStyleSheet(self._style_hover)
                    pix = self.parent_card.get_tag_pixmap(self.tag_text)
                    if pix is not None:
                        self._show_preview(pix)
                    super().enterEvent(event)

                def leaveEvent(self, event):
                    self.setStyleSheet(self._style_base)
                    self._hide_preview()
                    super().leaveEvent(event)

                def _show_preview(self, pixmap):
                    from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
                    if self._preview is None:
                        self._preview = QWidget(None, Qt.WindowType.ToolTip)
                        self._preview.setStyleSheet("background-color:#1a1a1a; border:1px solid #404040; border-radius:6px;")
                        lay = QVBoxLayout(self._preview)
                        lay.setContentsMargins(6, 6, 6, 6)
                        lay.setSpacing(4)
                        img_label = QLabel()
                        img_label.setObjectName("img_label")
                        img_label.setScaledContents(True)
                        lay.addWidget(img_label)
                    img_label = self._preview.findChild(QLabel, "img_label")
                    max_side = 200
                    if pixmap.width() > max_side or pixmap.height() > max_side:
                        scaled = pixmap.scaled(max_side, max_side, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                    else:
                        scaled = pixmap
                    img_label.setPixmap(scaled)
                    img_label.adjustSize()
                    self._preview.adjustSize()
                    pos_right = self.mapToGlobal(self.rect().topRight()) + QPoint(10, 0)
                    screen = self._preview.screen() or (QApplication.primaryScreen() if hasattr(QApplication, 'primaryScreen') else None)
                    avail = screen.availableGeometry() if screen else None
                    w = self._preview.width()
                    h = self._preview.height()
                    final_pos = pos_right
                    if avail and (pos_right.x() + w > avail.right() - 8):
                        pos_left = self.mapToGlobal(self.rect().topLeft()) - QPoint(w + 10, 0)
                        final_pos = pos_left
                        if final_pos.x() < avail.left() + 8:
                            final_pos.setX(avail.left() + 8)
                    if avail:
                        y = final_pos.y()
                        if y + h > avail.bottom() - 8:
                            y = max(avail.top() + 8, avail.bottom() - h - 8)
                        final_pos.setY(y)
                    self._preview.move(final_pos)
                    self._preview.show()

                def _hide_preview(self):
                    if self._preview is not None:
                        self._preview.hide()

            grid_container = QWidget()
            container_layout = QVBoxLayout(grid_container)
            container_layout.setContentsMargins(6, 6, 6, 6)
            container_layout.setSpacing(6)

            grid_layout = QGridLayout()
            grid_layout.setContentsMargins(0, 0, 0, 0)
            grid_layout.setHorizontalSpacing(4)
            grid_layout.setVerticalSpacing(4)
            container_layout.addLayout(grid_layout)

            nav_layout = QHBoxLayout()
            nav_layout.setContentsMargins(0, 0, 0, 0)
            nav_layout.setSpacing(8)
            prev_btn = QToolButton()
            prev_btn.setText("◄")
            prev_btn.setToolTip("Anterior")
            next_btn = QToolButton()
            next_btn.setText("►")
            next_btn.setToolTip("Siguiente")
            page_indicator = QLabel("")
            page_indicator.setStyleSheet("color:#bdbdbd; font-size:10px;")
            nav_layout.addWidget(prev_btn)
            nav_layout.addStretch(1)
            nav_layout.addWidget(page_indicator)
            nav_layout.addStretch(1)
            nav_layout.addWidget(next_btn)
            container_layout.addLayout(nav_layout)

            rows_per_col = 20
            cols_per_page = 2
            items_per_page = rows_per_col * cols_per_page
            total_items = len(self.tags)
            total_pages = max(1, math.ceil(total_items / items_per_page))
            page_index = 0

            def render_page():
                while grid_layout.count():
                    item = grid_layout.takeAt(0)
                    if item and item.widget():
                        item.widget().setParent(None)
                start = page_index * items_per_page
                end = min(total_items, start + items_per_page)
                for i, idx in enumerate(range(start, end)):
                    tag = self.tags[idx]
                    row = i % rows_per_col
                    col = i // rows_per_col
                    widget = TagMenuItem(tag, self)
                    grid_layout.addWidget(widget, row, col)
                page_indicator.setText(f"Página {page_index + 1} / {total_pages}")
                prev_btn.setEnabled(page_index > 0)
                next_btn.setEnabled(page_index < total_pages - 1)

            def go_prev():
                nonlocal page_index
                if page_index > 0:
                    page_index -= 1
                    render_page()

            def go_next():
                nonlocal page_index
                if page_index < total_pages - 1:
                    page_index += 1
                    render_page()

            prev_btn.clicked.connect(go_prev)
            next_btn.clicked.connect(go_next)
            render_page()

            grid_action = QWidgetAction(menu)
            grid_action.setDefaultWidget(grid_container)
            menu.addAction(grid_action)

            all_tags_btn.setMenu(menu)
            all_tags_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)

            gear_btn = QToolButton()
            gear_btn.setText("⚙️")
            gear_btn.setToolTip("Editar tags")
            gear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            gear_btn.setFixedHeight(22)
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
            
            color_btn = QToolButton()
            color_btn.setToolTip("Asignar color")
            color_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            color_btn.setFixedSize(24, 22)
            try:
                color_btn.setIcon(QIcon(ICON_COLORS))
                color_btn.setIconSize(color_btn.size())
            except Exception:
                color_btn.setText("🎨")
            color_btn.clicked.connect(self.choose_color)
            self.color_btn = color_btn
            self.update_color_button_style()
            
            tags_layout.addWidget(gear_btn)
            tags_layout.addWidget(color_btn)
            tags_layout.addStretch()
            
            self.lock_btn = QToolButton()
            self.lock_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self.lock_btn.setFixedSize(28, 22)
            self.lock_btn.clicked.connect(self.toggle_lock)
            self.update_lock_style()
            tags_layout.addWidget(self.lock_btn)

            tags_layout.addWidget(all_tags_btn)

        else:
            gear_btn = QToolButton()
            gear_btn.setText("⚙️")
            gear_btn.setToolTip("Editar tags")
            gear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            gear_btn.setFixedHeight(22)
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
            gear_btn.setStyleSheet(self._gear_style_base)
            self.gear_btn = gear_btn
            gear_btn.clicked.connect(self.show_tags_dialog)
            
            color_btn = QToolButton()
            color_btn.setToolTip("Asignar color")
            color_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            color_btn.setFixedSize(32, 30)
            try:
                color_btn.setIcon(QIcon(ICON_COLORS))
                color_btn.setIconSize(color_btn.size())
            except Exception:
                color_btn.setText("🎨")
            color_btn.clicked.connect(self.choose_color)
            self.color_btn = color_btn
            self.update_color_button_style()
            
            tags_layout.addWidget(gear_btn)
            tags_layout.addWidget(color_btn)
            tags_layout.addStretch()

            all_tags_btn = QToolButton()
            all_tags_btn.setText("All tags")
            all_tags_btn.setToolTip("Sin tags")
            all_tags_btn.setEnabled(False)
            all_tags_btn.setStyleSheet(
                """
                QToolButton {
                    background-color: #4f4f4f;
                    color: #bbbbbb;
                    border-radius: 10px;
                    padding: 2px 10px;
                    font-size: 10px;
                }
                """
            )
            
            self.lock_btn = QToolButton()
            self.lock_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self.lock_btn.setFixedSize(28, 22)
            self.lock_btn.clicked.connect(self.toggle_lock)
            self.update_lock_style()
            tags_layout.addWidget(self.lock_btn)

            tags_layout.addWidget(all_tags_btn)


        layout.addLayout(tags_layout)

    def _project_root(self):
        return os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

    def _load_tag_image_index(self):
        if self._tag_image_index is not None:
            return self._tag_image_index
        index_path = os.path.join(self._project_root(), "data", "tag_images", "tag_images_index.json")
        legacy_path = os.path.join(self._project_root(), "data", "tag_images", "index.json")
        try:
            if os.path.isfile(index_path):
                with open(index_path, "r", encoding="utf-8") as f:
                    self._tag_image_index = json.load(f)
            elif os.path.isfile(legacy_path):
                with open(legacy_path, "r", encoding="utf-8") as f:
                    self._tag_image_index = json.load(f)
            else:
                self._tag_image_index = {}
        except Exception:
            self._tag_image_index = {}
        return self._tag_image_index

    def _category_key(self):
        return self.category_name.lower().replace(" ", "_")

    def _normalize_tag(self, tag):
        return re.sub(r"[^a-z0-9_\-]", "", tag.lower().replace(" ", "_"))

    def get_tag_pixmap(self, tag):
        key = f"{self._category_key()}/{self._normalize_tag(tag)}"
        if key in self._tag_pixmap_cache:
            return self._tag_pixmap_cache[key]
        idx = self._load_tag_image_index()
        rel = idx.get(key)
        if not rel:
            try:
                cat_dir = os.path.join(self._project_root(), "data", "tag_images", self._category_key())
                if os.path.isdir(cat_dir):
                    base = self._normalize_tag(tag)
                    candidates = [f"{base}.png", f"{base}.jpg", f"{base}.jpeg"]
                    for fname in candidates:
                        abs_candidate = os.path.join(cat_dir, fname)
                        if os.path.isfile(abs_candidate):
                            rel = os.path.join("tag_images", self._category_key(), fname).replace("\\", "/")
                            try:
                                idx[key] = rel
                            except Exception:
                                pass
                            break
            except Exception:
                pass
            if not rel:
                return None
        abs_path = os.path.join(self._project_root(), "data", rel)
        if not os.path.isfile(abs_path):
            return None
        try:
            pix = QPixmap(abs_path)
            if pix and not pix.isNull():
                self._tag_pixmap_cache[key] = pix
                return pix
        except Exception:
            return None
        return None

    def invalidate_tag_image_cache(self):
        try:
            self._tag_image_index = None
            if isinstance(self._tag_pixmap_cache, dict):
                self._tag_pixmap_cache.clear()
        except Exception:
            self._tag_image_index = None

    def show_tags_dialog(self):
        from ..tags_dialog import TagsDialog

        TAGS_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "tags.json")
        key = self.category_name.lower().replace(" ", "_")
        with open(TAGS_PATH, "r", encoding="utf-8") as f:
            tags_data = json.load(f)
            tags = tags_data.get(key, [])
        dlg = TagsDialog(self.category_name, tags, self)
        if hasattr(self, "gear_btn") and hasattr(self, "_gear_style_active"):
            self.gear_btn.setStyleSheet(self._gear_style_active)
        if dlg.exec():
            updated_tags = getattr(dlg, "tags", tags)
            self.update_tags_ui(updated_tags)
        if hasattr(self, "gear_btn") and hasattr(self, "_gear_style_base"):
            self.gear_btn.setStyleSheet(self._gear_style_base)

    def setup_styles(self):
        border_color = "#d32f2f" if self.is_locked else "#404040"
        border_width = "2px" if self.is_locked else "1px"
        
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {self.bg_color};
                border: {border_width} solid {border_color};
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
        self.debounce_timer = QTimer()
        self.debounce_timer.setSingleShot(True)
        self.debounce_timer.timeout.connect(self.update_prompt)

    def on_input_change(self):
        self.debounce_timer.start(500)

    def update_prompt(self):
        if not self.prompt_generator:
            return
        
        value = self.input_field.text()
        if self.prompt_generator:
            validated_value = self.prompt_generator.validate_input(value)
            snake_case_name = self.category_name.lower().replace(" ", "_")
            self.prompt_generator.update_category(snake_case_name, validated_value)
            self.value_changed.emit()

    def toggle_edit_mode(self):
        if not self.is_editing:
            self.is_editing = True
            self.title_label.hide()
            self.title_edit.show()
            self.title_edit.setFocus()
            self.title_edit.selectAll()
            
            try:
                self.edit_btn.setIcon(QIcon(ICON_SAVE))
            except Exception:
                self.edit_btn.setText("💾")
            self.edit_btn.setToolTip("Guardar")
        else:
            self.cancel_edit_mode()

    def cancel_edit_mode(self):
        self.is_editing = False
        self.unsaved_changes = False
        self.title_edit.hide()
        self.title_label.show()
        self.title_edit.setText(self.category_name)
        self.title_edit.setStyleSheet("")
        
        try:
            self.edit_btn.setIcon(QIcon(ICON_EDIT))
        except Exception:
            self.edit_btn.setText("✏️")
        self.edit_btn.setToolTip("Editar nombre")
        self.title_edit.setStyleSheet("")

    def save_category_name(self):
        new_name = self.title_edit.text().strip()
        if new_name and new_name != self.category_name:
            old_name = self.category_name
            self.category_name = new_name
            self.title_label.setText(new_name)
            self.request_rename.emit(old_name, new_name)
        
        self.cancel_edit_mode()

    def on_title_edited(self):
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
    
        current = self.input_field.text()
        pattern = re.compile(rf"\(*\s*{re.escape(tag)}\s*\)*,")
        current = pattern.sub("", current).strip()
    
        if count > 0:
            if count == 1:
                tag_text = f"{tag},"
            else:
                parentheses_count = count - 1
                tag_text = f"{'(' * parentheses_count}{tag}{')' * parentheses_count},"
            
            if current:
                new_text = f"{current} {tag_text}"
            else:
                new_text = tag_text
            self.input_field.setText(new_text.strip())
        else:
            self.input_field.setText(current)

    def get_selected_tags(self):
        return [tag for tag, count in self.tag_click_counts.items() if count > 0]

    def clear_value(self):
        if self.is_locked:
            return

        self.input_field.setText("")
        self.tag_click_counts = {tag: 0 for tag in self.tags}
