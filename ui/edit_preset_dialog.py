from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit,
    QScrollArea, QWidget, QInputDialog, QFileDialog, QFrame, QGridLayout, QSizePolicy, QLineEdit,
    QComboBox, QCheckBox, QMessageBox, QToolButton
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
import os


class EditPresetDialog(QDialog):
    """Diálogo sencillo para editar las categorías y las imágenes de un preset"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setModal(False)
        self.setWindowModality(Qt.WindowModality.NonModal)
        self.resize(700, 600)

        self.preset_name = ""
        self.category_id = ""
        self.category_editors = {}  # {category_name: QTextEdit}
        self.selected_images = []   # lista de rutas absolutas

        self._build_ui()

    def _build_ui(self):
        self.setWindowTitle("Editar Preset")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(6)

        # Estilos generales más compactos
        self.setStyleSheet("""
            QDialog { background-color: #2b2b2b; color: #e0e0e0; }
            QLabel { background: transparent; }
            QPushButton { min-width: 0; padding: 4px 8px; font-size: 10px; }
            QTextEdit { background-color: #2f2f2f; color: #ddd; border: 1px solid #555; border-radius: 4px; font-size: 11px; }
        """)

        # Encabezado
        self.header_label = QLabel("")
        self.header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.header_label)

        # Cuerpo a dos columnas
        body = QHBoxLayout()
        body.setSpacing(8)

        # === Columna Izquierda: Imágenes ===
        left_panel = QVBoxLayout()
        left_panel.setSpacing(6)

        img_controls = QHBoxLayout()
        add_imgs_btn = QPushButton("🖼️ Agregar imágenes")
        add_imgs_btn.setMaximumHeight(24)
        add_imgs_btn.clicked.connect(self._select_images)
        clear_imgs_btn = QPushButton("🧹 Limpiar imágenes")
        clear_imgs_btn.setMaximumHeight(24)
        clear_imgs_btn.clicked.connect(self._clear_images)
        img_controls.addWidget(add_imgs_btn)
        img_controls.addWidget(clear_imgs_btn)
        img_controls.addStretch()
        left_panel.addLayout(img_controls)

        # Lista vertical de previsualizaciones (1x4)
        grid = QGridLayout()
        grid.setSpacing(6)
        self.image_previews = []
        for i in range(4):
            lbl = QLabel(f"Imagen {i+1}\nNo seleccionada")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet("border: 2px solid gray; background-color: #2f2f2f; border-radius: 4px; font-size: 10px; padding: 6px;")
            lbl.setFixedSize(150, 150)
            self.image_previews.append(lbl)
            grid.addWidget(lbl, i, 0)
        # Envolver las previsualizaciones en un área con scroll vertical
        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        left_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        left_scroll.setFrameShape(QFrame.Shape.NoFrame)
        left_scroll_content = QWidget()
        left_scroll_content.setLayout(grid)
        left_scroll.setWidget(left_scroll_content)
        left_panel.addWidget(left_scroll)

        self.images_hint = QLabel("Sin imágenes seleccionadas")
        self.images_hint.setStyleSheet("color: #888; font-size: 10px;")
        left_panel.addWidget(self.images_hint)

        # Limitar el ancho máximo del panel izquierdo para hacerlo más angosto
        left_container = QWidget()
        left_container.setLayout(left_panel)
        left_container.setFixedWidth(280)
        left_container.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        body.addWidget(left_container, 1)

        # === Columna Derecha: Categorías ===
        right_panel = QVBoxLayout()
        right_panel.setSpacing(6)

        # Campo para editar el nombre del preset
        name_row = QHBoxLayout()
        name_row.setSpacing(6)
        name_label = QLabel("Nombre del preset:")
        # Aumentar únicamente el alto del label del nombre
        name_label.setObjectName("presetNameLabel")
        name_label.setFixedHeight(32)
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Ingresa el nombre…")
        self.name_input.setMaximumHeight(32)
        name_row.addWidget(name_label, alignment=Qt.AlignmentFlag.AlignVCenter)
        name_row.addWidget(self.name_input)
        right_panel.addLayout(name_row)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        scroll_content = QWidget()
        self.categories_layout = QVBoxLayout(scroll_content)
        self.categories_layout.setSpacing(4)
        # Evitar que los elementos se distribuyan para ocupar todo el alto:
        # alinearlos arriba del área de scroll
        self.categories_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll.setWidget(scroll_content)
        right_panel.addWidget(scroll)

        # Controles de categorías (debajo del scroll)
        # Botón: añadir categoría desde tarjetas
        add_from_cards_btn = QPushButton("📋 Añadir desde tarjetas")
        add_from_cards_btn.setMaximumHeight(24)
        add_from_cards_btn.setMaximumWidth(180)
        add_from_cards_btn.setStyleSheet(
            """
            QPushButton {
                background-color: rgba(100, 149, 237, 0.25);
                color: #dbe9ff;
                border: 1px solid rgba(100, 149, 237, 0.55);
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(100, 149, 237, 0.35);
                border-color: rgba(100, 149, 237, 0.75);
            }
            QPushButton:pressed {
                background-color: rgba(100, 149, 237, 0.5);
                border-color: rgba(100, 149, 237, 0.9);
            }
            """
        )
        add_from_cards_btn.clicked.connect(self._add_category_from_cards)
        # Colocar el botón en una fila
        buttons_row = QHBoxLayout()
        buttons_row.setSpacing(8)
        buttons_row.addWidget(add_from_cards_btn)
        buttons_row.addStretch()
        right_panel.addLayout(buttons_row)

        # Botones de acción (debajo a la derecha)
        actions = QHBoxLayout()
        actions.addStretch()
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.setMaximumHeight(24)
        save_btn = QPushButton("💾 Guardar")
        save_btn.setMaximumHeight(24)
        save_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; font-size: 10px;")
        cancel_btn.clicked.connect(self.reject)
        save_btn.clicked.connect(self.accept)
        actions.addWidget(cancel_btn)
        actions.addWidget(save_btn)
        right_panel.addLayout(actions)

        body.addLayout(right_panel, 3)
        layout.addLayout(body)

    def set_preset_data(self, preset_name, category_id, categories, images):
        """Inicializa el diálogo con los datos actuales del preset"""
        self.preset_name = preset_name
        self.category_id = category_id
        self.header_label.setText(f"Carpeta: {category_id}")
        # Inicializar el campo de nombre editable
        if hasattr(self, 'name_input') and self.name_input is not None:
            self.name_input.setText(preset_name)

        # Limpiar editores previos
        for i in reversed(range(self.categories_layout.count())):
            item = self.categories_layout.itemAt(i)
            w = item.widget()
            if w:
                w.setParent(None)
        self.category_editors.clear()

        # Crear un editor por categoría
        for cat_name, cat_value in categories.items():
            self._add_category_editor(cat_name, cat_value)

        # Cargar imágenes existentes
        self.selected_images = list(images or [])
        self._update_images_hint()
        self._refresh_image_previews()

    def get_preset_name(self):
        """Devuelve el nombre del preset, usando el campo editable si existe"""
        if hasattr(self, 'name_input') and self.name_input is not None:
            name = self.name_input.text().strip()
            return name or self.preset_name
        return self.preset_name

    def _add_category_editor(self, category_name, initial_text=""):
        color = self._group_color_for_category(category_name)

        frame = QFrame()
        frame.setStyleSheet(f"QFrame {{ background-color: #2c2c2c; border: 1px solid #444; border-left: 4px solid {color}; border-radius: 6px; margin: 2px 0; }}")
        frame.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        v = QVBoxLayout(frame)
        v.setContentsMargins(8, 6, 8, 6)
        v.setSpacing(4)

        row = QHBoxLayout()
        label = QLabel(category_name)
        label.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 11px;")
        row.addWidget(label)
        row.addStretch()
        jump_btn = QToolButton()
        jump_btn.setText("→")
        jump_btn.setFixedSize(20, 20)
        jump_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        jump_btn.setStyleSheet("QToolButton { background-color: #404040; color: #fff; border-radius: 4px; } QToolButton:hover { background-color: #6366f1; }")
        jump_btn.clicked.connect(lambda: self._jump_to_category(category_name, editor.toPlainText().strip()))
        row.addWidget(jump_btn)
        v.addLayout(row)

        editor = QTextEdit()
        editor.setPlainText(initial_text or "")
        editor.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        editor.setFixedHeight(35)
        v.addWidget(editor)

        self.categories_layout.addWidget(frame)
        self.category_editors[category_name] = editor

    def _jump_to_category(self, category_name: str, value: str):
        print(f"DEBUG EditPresetDialog: jump requested -> category='{category_name}', value_len={len(value or '')}")
        parent = self.parent()
        main_window = None
        while parent:
            if hasattr(parent, 'category_grid'):
                main_window = parent
                break
            parent = parent.parent() if hasattr(parent, 'parent') else None
        if main_window and hasattr(main_window, 'category_grid'):
            print("DEBUG EditPresetDialog: main_window found, focusing and setting value")
            try:
                grid = main_window.category_grid
                if hasattr(grid, 'set_category_value'):
                    grid.set_category_value(category_name, value)
                else:
                    print("DEBUG EditPresetDialog: set_category_value not found, using fallback")
                    target = None
                    for card in getattr(grid, 'cards', []):
                        if getattr(card, 'category_name', '') == category_name:
                            target = card
                            break
                    if target and hasattr(target, 'input_field'):
                        if hasattr(target, 'is_locked') and target.is_locked:
                            print(f"DEBUG EditPresetDialog: Card '{category_name}' is locked. Skipping update.")
                            return
                        target.input_field.setText(value or "")
                        try:
                            grid.focus_category(category_name)
                        except Exception:
                            print("DEBUG EditPresetDialog: fallback focus failed")
                    else:
                        print("DEBUG EditPresetDialog: fallback target not found or no input_field")
            except Exception as e:
                print(f"DEBUG EditPresetDialog: error calling set_category_value -> {e}")
        else:
            print("DEBUG EditPresetDialog: main_window with category_grid not found")

    def _add_category_interactive(self):
        name, ok = QInputDialog.getText(self, "Nueva categoría", "Nombre de la categoría:")
        if ok and name.strip():
            cleaned = name.strip()
            if cleaned in self.category_editors:
                return
            self._add_category_editor(cleaned, "")

    def _get_grid_current_values(self):
        """Intenta obtener el grid de categorías para listar nombres y valores actuales.
        Devuelve dict {nombre: valor_str} o {} si no disponible.
        """
        # Navegar por padres hasta encontrar un objeto con atributo category_grid
        parent = self.parent()
        main_window = None
        while parent:
            if hasattr(parent, 'category_grid'):
                main_window = parent
                break
            parent = parent.parent() if hasattr(parent, 'parent') else None

        try:
            if main_window and hasattr(main_window, 'category_grid'):
                grid = main_window.category_grid
                if hasattr(grid, 'get_current_values'):
                    values = grid.get_current_values() or {}
                    # Asegurar que todos sean str
                    return {k: (v if isinstance(v, str) else str(v)) for k, v in values.items()}
        except Exception:
            pass
        return {}

    def _add_category_from_cards(self):
        """Abre un diálogo para elegir una categoría existente del grid y añadirla
        al preset, con opción de incluir sus valores actuales o dejarla vacía.
        Evita duplicados respecto a las ya presentes en el editor.
        """
        source_values = self._get_grid_current_values()
        if not source_values:
            QMessageBox.information(self, "Sin categorías", "No se pudo obtener categorías desde las tarjetas.")
            return

        # Excluir categorías ya presentes
        available_names = [n for n in source_values.keys() if n not in self.category_editors]
        if not available_names:
            QMessageBox.information(self, "Sin categorías", "Todas las categorías del grid ya están añadidas.")
            return

        # Construir diálogo de selección
        dlg = QDialog(self)
        dlg.setWindowTitle("Añadir desde tarjetas")
        dlg.setModal(True)
        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(6)

        label = QLabel("Elige una categoría del grid:")
        layout.addWidget(label)

        # Buscador para filtrar categorías
        search_box = QLineEdit()
        search_box.setPlaceholderText("Buscar categoría…")
        search_box.setMaximumHeight(32)
        layout.addWidget(search_box)

        combo = QComboBox()
        layout.addWidget(combo)

        preview_label = QLabel("Valores actuales (vista previa):")
        preview_label.setStyleSheet("color: #bbb; font-size: 10px;")
        layout.addWidget(preview_label)

        preview = QTextEdit()
        preview.setReadOnly(True)
        preview.setFixedHeight(60)
        layout.addWidget(preview)

        include_checkbox = QCheckBox("Incluir valores actuales")
        include_checkbox.setChecked(True)
        layout.addWidget(include_checkbox)

        # Actualizar preview según selección
        def update_preview():
            name = combo.currentText()
            val = source_values.get(name, "")
            preview.setPlainText(val if name else "")

        # Repoblar combo según filtro
        all_names = available_names[:]
        def repopulate_combo(filter_text: str):
            text = (filter_text or "").lower()
            filtered = [n for n in all_names if text in n.lower()]
            combo.blockSignals(True)
            combo.clear()
            combo.addItems(filtered)
            combo.blockSignals(False)
            update_preview()

        search_box.textChanged.connect(repopulate_combo)
        repopulate_combo("")
        combo.currentIndexChanged.connect(update_preview)

        # Botones
        buttons = QHBoxLayout()
        buttons.addStretch()
        cancel = QPushButton("Cancelar")
        ok = QPushButton("Añadir")
        cancel.setMaximumHeight(24)
        ok.setMaximumHeight(24)
        buttons.addWidget(cancel)
        buttons.addWidget(ok)
        layout.addLayout(buttons)

        cancel.clicked.connect(dlg.reject)
        ok.clicked.connect(dlg.accept)

        if dlg.exec():
            selected_name = combo.currentText().strip()
            if not selected_name:
                return
            initial_text = source_values.get(selected_name, "") if include_checkbox.isChecked() else ""
            # Añadir editor
            self._add_category_editor(selected_name, initial_text)

    def _select_images(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Seleccionar imágenes", "", "Imágenes (*.png *.jpg *.jpeg *.webp *.bmp)"
        )
        if files:
            self.selected_images = files[:4]  # limitar a 4 para consistencia con vista previa
            self._update_images_hint()
            self._refresh_image_previews()

    def _clear_images(self):
        self.selected_images = []
        self._update_images_hint()
        self._refresh_image_previews()

    def _update_images_hint(self):
        if self.selected_images:
            names = [os.path.basename(p) for p in self.selected_images]
            self.images_hint.setText("Imágenes: " + ", ".join(names))
        else:
            self.images_hint.setText("Sin imágenes seleccionadas")

    def get_updated_categories(self):
        """Devuelve todas las categorías presentes con sus textos (incluye vacías)."""
        result = {}
        for cat, editor in self.category_editors.items():
            text = editor.toPlainText().strip()
            result[cat] = text  # incluir también vacías
        return result

    def get_selected_images(self):
        return list(self.selected_images)

    def _refresh_image_previews(self):
        # Actualiza las miniaturas en el grid 2x2
        for i, lbl in enumerate(self.image_previews):
            if i < len(self.selected_images) and os.path.exists(self.selected_images[i]):
                pix = QPixmap(self.selected_images[i])
                if not pix.isNull():
                    scaled = pix.scaled(150, 150, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                    lbl.setPixmap(scaled)
                    lbl.setText("")
                    lbl.setStyleSheet("border: 2px solid #4CAF50; background-color: #1f1f1f; border-radius: 4px;")
                else:
                    lbl.setPixmap(QPixmap())
                    lbl.setText(f"Imagen {i+1}\nNo válida")
                    lbl.setStyleSheet("border: 2px solid #f44336; background-color: #2f2f2f; border-radius: 4px; font-size: 10px; padding: 6px;")
            else:
                lbl.setPixmap(QPixmap())
                lbl.setText(f"Imagen {i+1}\nNo seleccionada")
                lbl.setStyleSheet("border: 2px solid gray; background-color: #2f2f2f; border-radius: 4px; font-size: 10px; padding: 6px;")

    def _group_color_for_category(self, name: str) -> str:
        """Heurística para asignar color por grupo de categoría"""
        n = (name or "").lower()
        if any(w in n for w in ["vestuario", "ropa", "outfit", "clothing", "prendas"]):
            return "#af69cd"  # Vestuario
        if any(w in n for w in ["pose", "postura", "position", "poses"]):
            return "#4CAF50"  # Poses
        if any(w in n for w in ["expresion", "expression", "cara", "face", "expresiones"]):
            return "#FF9800"  # Expresiones
        if any(w in n for w in ["angulo", "angle", "cámara", "camara", "vista", "view"]):
            return "#9C27B0"  # Ángulos
        if any(w in n for w in ["iluminacion", "lighting", "luz", "light"]):
            return "#F57C00"  # Iluminación
        if any(w in n for w in ["cabello", "hair", "pelo"]):
            return "#795548"  # Cabello
        if any(w in n for w in ["ojos", "eyes", "mirada"]):
            return "#00BCD4"  # Ojos
        if any(w in n for w in ["fondo", "background", "escenario"]):
            return "#607D8B"  # Fondo
        if any(w in n for w in ["accesorio", "accessory", "complemento"]):
            return "#E91E63"  # Accesorios
        return "#cccccc"  # Default
