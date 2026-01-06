from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
    QPushButton, QLineEdit, QLabel, QMessageBox, QInputDialog,
    QDialog, QComboBox, QCheckBox, QScrollArea, QTextEdit, QFileDialog, QGridLayout,
    QToolTip, QFrame, QMenu, QSpacerItem, QSizePolicy  # Mantener QToolTip y QFrame y agregar QMenu
)
from PyQt6.QtCore import Qt, pyqtSignal, QBuffer, QPoint, QEvent, QSize  # Remover QTimer
from PyQt6.QtGui import QFont, QPixmap, QCursor, QAction, QIcon
from ui.edit_preset_dialog import EditPresetDialog
from logic.presets_manager import PresetsManager
from datetime import datetime  # ← AGREGAR ESTE IMPORT
from PIL import Image  # Agregar para redimensionar imágenes
import os
import base64
import io

class PresetsPanel(QWidget):
    preset_loaded = pyqtSignal(dict)  # Emite cuando se carga un preset
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_widget = parent
        self.presets_manager = PresetsManager()
        self._image_thumb_cache = {}

        self.setup_ui()
        self.load_presets()
    
    def setup_ui(self):
        """Configura la interfaz del panel de presets"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # Título
        title = QLabel("Presets")
        title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Buscador
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("🔍 Buscar presets...")
        self.search_box.textChanged.connect(self.filter_presets)
        layout.addWidget(self.search_box)
        
        # Árbol de presets (organizado por carpetas)
        self.presets_tree = QTreeWidget()
        self.presets_tree.setHeaderHidden(True)
        # Asegurar tamaño de icono visible
        self.presets_tree.setIconSize(QSize(24, 24))
        self.presets_tree.setStyleSheet(
            "QToolTip { background-color: #ffffff; color: #000000; border: 1px solid #000000; padding: 4px; font-weight: 600; }\n"
            "QTreeWidget::item:selected { background-color: #ffeb3b; color: #000000; }"
            "QTreeWidget::item { height: 28px; }" # Dar altura suficiente a los items
        )
        self._tooltip_label = None
        self._tooltip_item = None
        self._preview_label = None
        self._preview_item = None
        self.presets_tree.viewport().installEventFilter(self)
        if self.parent_widget:
            try:
                self.parent_widget.installEventFilter(self)
            except Exception:
                pass
        # Configurar clic derecho para menú contextual con opciones
        self.presets_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.presets_tree.customContextMenuRequested.connect(self.show_context_menu)
        # Conectar doble clic para cargar preset
        self.presets_tree.itemDoubleClicked.connect(self.load_selected_preset)
        # Conectar clic simple para alternar expansión de carpetas
        self.presets_tree.itemClicked.connect(self.toggle_folder_on_click)
        layout.addWidget(self.presets_tree)
        
        # Botones
        buttons_layout = QHBoxLayout()
        
        # Botón Nueva Carpeta - estilizado y más pequeño
        new_folder_btn = QPushButton("📁Crear Set")
        new_folder_btn.clicked.connect(self.create_new_folder)
        new_folder_btn.setStyleSheet("""
            QPushButton {
                background-color: #2d2d2d;
                border: 1px solid #404040;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 11px;
                font-weight: 500;
                color: #e0e0e0;
            }
            QPushButton:hover {
                background-color: #3d3d3d;
                border-color: #505050;
            }
            QPushButton:pressed {
                background-color: #1d1d1d;
            }
        """)
        buttons_layout.addWidget(new_folder_btn)
        
        # Botón Guardar Preset - estilizado y más pequeño
        save_btn = QPushButton("💾 Capturar un Preset")
        save_btn.clicked.connect(self.save_current_as_preset)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #2d4a2d;
                border: 1px solid #404040;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 11px;
                font-weight: 500;
                color: #e0e0e0;
            }
            QPushButton:hover {
                background-color: #3d5a3d;
                border-color: #505050;
            }
            QPushButton:pressed {
                background-color: #1d3a1d;
            }
        """)
        buttons_layout.addWidget(save_btn)
        
        # QUITAR EL BOTÓN "+" - ya no se incluye
        
        layout.addLayout(buttons_layout)
    
    def load_presets(self):
        """Carga los presets en el árbol"""
        self.presets_tree.clear()
        
        # Obtener todas las carpetas disponibles (predefinidas + personalizadas)
        all_folders = self.presets_manager.get_all_preset_folders()
        
        for folder_id, folder_info in all_folders.items():
            # Crear nodo padre
            category_item = QTreeWidgetItem(self.presets_tree)
            category_item.setText(0, folder_info['display_name'])
            category_item.setData(0, Qt.ItemDataRole.UserRole, {
                'type': 'category',
                'category_id': folder_id,
                'is_custom': folder_info.get('is_custom', False)
            })
            # Tooltip con opciones disponibles
            category_item.setToolTip(0, "Opciones: Renombrar carpeta • Eliminar carpeta")
            
            # Cargar presets de esta categoría
            presets = self.presets_manager.get_presets_by_category(folder_id)
            # Preparar lista con timestamp para ordenar por fecha (más reciente primero)
            sortable = []
            for preset_id, preset_data in presets.items():
                created_str = preset_data.get('created_at')
                ts = 0
                if created_str:
                    try:
                        dt = datetime.fromisoformat(created_str.replace('Z', '+00:00'))
                        ts = int(dt.timestamp())
                    except Exception:
                        ts = 0
                if ts == 0:
                    # Respaldo: usar mtime del archivo JSON del preset
                    json_path = os.path.join(self.presets_manager.presets_dir, folder_id, f"{preset_id}.json")
                    if os.path.exists(json_path):
                        try:
                            ts = int(os.path.getmtime(json_path))
                        except Exception:
                            ts = 0
                sortable.append((preset_id, preset_data, ts))
            # Ordenar: primero por timestamp desc, luego por nombre para desempate estable
            sortable.sort(key=lambda x: (x[2], (x[1].get('name', x[0]) or "").lower()), reverse=True)
            # Pintar en orden
            for preset_id, preset_data, _ts in sortable:
                preset_item = QTreeWidgetItem(category_item)
                preset_name = preset_data.get('name', preset_id)
                preset_item.setText(0, preset_name)
                
                # Asignar icono si hay imagen(es)
                image_paths = []
                images_list = preset_data.get('images', [])
                
                # Si es una lista de nombres de archivo (nuevo formato)
                if isinstance(images_list, list) and images_list:
                    # Construir ruta a la carpeta de imágenes del preset
                    # La estructura es: data/presets/<categoria>/<preset_name>_images/<imagen>
                    # Pero el nombre de la carpeta de imágenes puede ser diferente al ID si se sanitizó diferente
                    # Sin embargo, PresetsManager.save_preset usa el mismo método de sanitización.
                    # Asumimos que la carpeta está en el mismo directorio que el JSON
                    
                    # Intentamos deducir la ruta
                    # El json_path lo construimos antes para el timestamp:
                    # json_path = os.path.join(self.presets_manager.presets_dir, folder_id, f"{preset_id}.json")
                    
                    # La carpeta de imágenes suele ser: <preset_id>_images
                    # Pero cuidado, preset_id es el nombre del archivo sin extensión.
                    images_folder_name = f"{preset_id}_images"
                    images_dir = os.path.join(self.presets_manager.presets_dir, folder_id, images_folder_name)
                    
                    if os.path.isdir(images_dir):
                        for img_name in images_list:
                            full_path = os.path.join(images_dir, img_name)
                            if os.path.exists(full_path):
                                image_paths.append(full_path)
                
                # Si tenemos imágenes, usar la primera como icono
                if image_paths:
                    try:
                        pixmap = QPixmap(image_paths[0])
                        if not pixmap.isNull():
                            pixmap = pixmap.scaled(24, 24, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                            icon = QIcon(pixmap)
                            preset_item.setIcon(0, icon)
                    except Exception as e:
                        print(f"Error cargando icono desde archivo para preset {preset_id}: {e}")
                
                # Soporte legacy para base64 'image' field (si existiera)
                elif preset_data.get('image'):
                     try:
                        image_data = preset_data.get('image')
                        img_bytes = base64.b64decode(image_data.split(',')[1] if ',' in image_data else image_data)
                        pixmap = QPixmap()
                        pixmap.loadFromData(img_bytes)
                        pixmap = pixmap.scaled(24, 24, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                        icon = QIcon(pixmap)
                        preset_item.setIcon(0, icon)
                        # Convertir a lista ficticia para el preview
                        image_paths = [image_data] # Marcador de que es data raw
                     except Exception:
                        pass

                preset_item.setData(0, Qt.ItemDataRole.UserRole, {
                    'type': 'preset',
                    'category_id': folder_id,
                    'preset_id': preset_id,
                    'preset_data': preset_data,
                    'image_paths': image_paths  # Guardar rutas para el preview
                })
        
        # Colapsar todos los nodos por defecto
        self.presets_tree.collapseAll()

    def toggle_folder_on_click(self, item, column):
        """Alterna expansión al hacer clic en una carpeta (item raíz)."""
        if item is None:
            return
        item_data = item.data(0, Qt.ItemDataRole.UserRole) or {}
        if item_data.get('type') == 'category' and item.parent() is None:
            item.setExpanded(not item.isExpanded())
        elif item_data.get('type') == 'preset':
            # Detectar si el clic fue en el icono
            # QTreeWidget no tiene un evento "clickedIcon", así que usamos una heurística
            # Si el clic es en la columna 0, podría ser texto o icono.
            # Sin embargo, si queremos ser muy precisos, necesitamos coordenadas.
            # Pero una aproximación es usar mouseReleaseEvent o comprobar si hay imágenes
            # y si el usuario hizo clic en la zona izquierda.
            
            # Como el usuario pidió "al presionar un click en el icono de la imagen aparesca la vista previa"
            # y "al presionar en otro lado de la opcion del present es para seleccionar",
            # la forma más robusta es detectar la posición del ratón relativa al item.
            # Pero `itemClicked` no da posición exacta del mouse.
            
            # Vamos a usar una lógica basada en el evento del mouse que ya tenemos filtrado en eventFilter? No.
            # Usaremos el cursor actual.
            
            tree = self.presets_tree
            pos = tree.viewport().mapFromGlobal(QCursor.pos())
            rect = tree.visualItemRect(item)
            
            # Asumimos que el icono está a la izquierda.
            # El indentado depende del nivel. Preset es hijo de categoría, nivel 1.
            indent = tree.indentation()
            # Margen izquierdo aproximado: indent (por la flecha de root) + indent (nivel 1)
            # En realidad el icono empieza después de la indentación.
            # Un icono de 24px.
            
            # Vamos a simplificar: Si hay icono, asumimos que los primeros 40-50 pixeles del item son la "zona activa" del icono.
            # Ajustaremos este valor según sea necesario.
            icon_width = 32 # 24px icono + padding
            
            # Calculamos la X relativa al inicio del item visual
            # visualItemRect devuelve el rectangulo de toda la fila en la columna 0.
            # Pero ojo, en un árbol indentado, rect.x() ya tiene el desplazamiento.
            
            relative_x = pos.x() - rect.x()
            
            # Si el clic está dentro del ancho del icono (aprox)
            if 0 <= relative_x <= icon_width:
                 image_paths = item_data.get('image_paths')
                 if image_paths:
                     self.show_preview_dialog(item.text(0), image_paths)
                     # Importante: podríamos querer detener la propagación para que no seleccione/cargue
                     # Pero load_selected_preset es con doble clic.
                     # Y la selección simple está bien que ocurra.
            

    def show_preview_dialog(self, title, image_paths):
        """Muestra un diálogo modal tipo Popup con la galería de imágenes en Grid 2x2"""
        if not image_paths:
            return
            
        dialog = QDialog(self)
        # Configurar como Popup para que no tenga bordes ni botones y se cierre al hacer click fuera
        dialog.setWindowFlags(Qt.WindowType.Popup)
        dialog.setModal(True)
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Contenedor para el grid
        content_widget = QWidget()
        grid_layout = QGridLayout(content_widget)
        grid_layout.setSpacing(0)
        grid_layout.setContentsMargins(0, 0, 0, 0)
        
        # Tamaño fijo para las imágenes (150px)
        MAX_IMG_SIZE = 150
        
        # Contadores para calcular el tamaño final
        max_row = 0
        max_col = 0
        has_images = False
        
        for i, img_source in enumerate(image_paths):
            label = QLabel()
            pixmap = QPixmap()
            
            # Verificar si es ruta de archivo o data base64
            if isinstance(img_source, str) and os.path.exists(img_source):
                pixmap.load(img_source)
            elif isinstance(img_source, str): # Asumir base64 legacy
                 try:
                    img_bytes = base64.b64decode(img_source.split(',')[1] if ',' in img_source else img_source)
                    pixmap.loadFromData(img_bytes)
                 except:
                    pass
            
            if not pixmap.isNull():
                has_images = True
                # Escalar manteniendo relación de aspecto
                # Usamos KeepAspectRatio para que encaje en 100x100 sin deformarse
                pixmap = pixmap.scaled(MAX_IMG_SIZE, MAX_IMG_SIZE, 
                                     Qt.AspectRatioMode.KeepAspectRatio, 
                                     Qt.TransformationMode.SmoothTransformation)
                
                label.setPixmap(pixmap)
                label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                # Estilo sin bordes ni padding
                label.setStyleSheet("border: none; background-color: #222; margin: 0px; padding: 0px;")
                label.setFixedSize(MAX_IMG_SIZE, MAX_IMG_SIZE)
                
                # Calcular posición en grid (row, col)
                row = i // 2
                col = i % 2
                grid_layout.addWidget(label, row, col)
                
                max_row = max(max_row, row)
                max_col = max(max_col, col)
        
        if not has_images:
            return

        layout.addWidget(content_widget)
        
        # Ajustar tamaño del diálogo al contenido exacto
        # max_row y max_col son índices, así que sumamos 1 para la cuenta
        total_width = (max_col + 1) * MAX_IMG_SIZE
        total_height = (max_row + 1) * MAX_IMG_SIZE
        dialog.setFixedSize(total_width, total_height)
        
        # Mover el diálogo cerca del cursor
        dialog.move(QCursor.pos())
        
        dialog.exec()

    def show_persistent_tooltip(self, item, text):
        """Muestra un tooltip persistente sobre el item clickeado."""
        self.hide_persistent_tooltip()
        label = QLabel(text, self.presets_tree.viewport())
        label.setStyleSheet("background-color: #ffffff; color: #000000; border: 1px solid #000000; padding: 6px; font-weight: 600;")
        label.setWordWrap(True)
        label.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        label.adjustSize()

        rect = self.presets_tree.visualItemRect(item)
        pos = rect.topLeft()
        y = pos.y() - label.height() - 4
        if y < 0:
            y = rect.bottom() + 4
        viewport = self.presets_tree.viewport()
        max_x = viewport.width() - label.width() - 4
        x = max(0, min(pos.x(), max_x))
        label.move(x, y)
        label.raise_()
        label.show()

        self._tooltip_label = label
        self._tooltip_item = item

    def hide_persistent_tooltip(self):
        """Oculta y destruye el tooltip persistente si existe."""
        if getattr(self, '_tooltip_label', None):
            self._tooltip_label.hide()
            self._tooltip_label.deleteLater()
            self._tooltip_label = None
            self._tooltip_item = None

    def show_preview_overlay(self, item, html):
        if getattr(self, '_preview_label', None):
            self._preview_label.hide()
            self._preview_label.deleteLater()
            self._preview_label = None
            self._preview_item = None
        parent_for_overlay = self.parent_widget if self.parent_widget else self.presets_tree.viewport()
        label = QLabel(parent_for_overlay)
        label.setTextFormat(Qt.TextFormat.RichText)
        label.setText(html)
        label.setStyleSheet("background-color: #2d2d2d; border: 2px solid #00ff00; border-radius: 8px;")
        label.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        try:
            label.setFixedWidth(350)
        except Exception:
            pass
        label.adjustSize()

        rect = self.presets_tree.visualItemRect(item)
        global_anchor = self.presets_tree.viewport().mapToGlobal(rect.topRight())
        if parent_for_overlay is self.parent_widget:
            local_anchor = self.parent_widget.mapFromGlobal(global_anchor)
        else:
            local_anchor = self.presets_tree.viewport().mapFromGlobal(global_anchor)

        x = local_anchor.x() + 20
        y = local_anchor.y() - 10

        max_x = parent_for_overlay.width() - label.width() - 6
        max_y = parent_for_overlay.height() - label.height() - 6
        x = max(0, min(x, max_x))
        y = max(0, min(y, max_y))

        label.move(x, y)
        label.raise_()
        label.show()

        self._preview_label = label
        self._preview_item = item

    def hide_preview_overlay(self):
        if getattr(self, '_preview_label', None):
            self._preview_label.hide()
            self._preview_label.deleteLater()
            self._preview_label = None
            self._preview_item = None

    def eventFilter(self, obj, event):
        """Oculta el tooltip al hacer clic fuera o en otro item."""
        if event.type() == QEvent.Type.MouseButtonPress:
            if obj == self.presets_tree.viewport():
                item = self.presets_tree.itemAt(event.pos())
                if self._tooltip_label and (item is None or item != self._tooltip_item):
                    self.hide_persistent_tooltip()
                # Ya no necesitamos ocultar preview overlay porque ahora es un diálogo modal
            elif obj == self.parent_widget:
                pass
        return super().eventFilter(obj, event)
    
    def load_selected_preset(self, item, column):
        """Carga el preset seleccionado al hacer doble clic con confirmación"""
        # Verificar que es un preset (no una carpeta)
        if item.parent() is None:
            return  # Es una carpeta, no un preset
            
        preset_name = item.text(0)
        folder_name = item.parent().text(0).replace('📂 ', '')
        
        # Mostrar diálogo de confirmación
        reply = QMessageBox.question(
            self, 
            "Cargar Preset", 
            f"¿Deseas cargar el preset '{preset_name}'?\n\n"
            f"Esto limpiará los valores actuales de las categorías\n"
            f"incluidas en este preset y los reemplazará con\n"
            f"los valores guardados.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Cargar el preset
            preset_data = self.presets_manager.load_preset(
                folder_name.lower().replace(' ', '_'), 
                preset_name
            )
            
            if preset_data:
                # Agregar el nombre del preset a los datos antes de emitir la señal
                preset_data['preset_display_name'] = preset_name
                # Emitir señal con los datos del preset
                self.preset_loaded.emit(preset_data)

            else:
                QMessageBox.warning(
                    self, 
                    "Error", 
                    f"No se pudo cargar el preset '{preset_name}'."
                )
    
    def save_current_as_preset(self):
        """Guarda los valores actuales como un nuevo preset con selección manual de categorías"""
        # Buscar el MainWindow navegando por la jerarquía de widgets
        main_window = None
        parent = self.parent_widget
        
        # Navegar hacia arriba hasta encontrar el MainWindow
        while parent:
            if hasattr(parent, 'category_grid'):
                main_window = parent
                break
            parent = parent.parent() if hasattr(parent, 'parent') else None
        
        if not main_window or not hasattr(main_window, 'category_grid'):
            QMessageBox.warning(self, "Error", "No se puede acceder a los valores de categorías.")
            return
        
        # Obtener todos los valores actuales (incluye vacíos)
        all_values = main_window.category_grid.get_current_values()
        
        # Crear diálogo personalizado más compacto
        dialog = QDialog(self)
        dialog.setWindowTitle("Guardar Preset")
        dialog.setModal(True)
        dialog.resize(700, 650)  # Reducir ancho de 900 a 700
        
        # Layout principal horizontal
        main_layout = QHBoxLayout(dialog)
        
        # ===== COLUMNA IZQUIERDA: CATEGORÍAS (75% del ancho) =====
        left_section = QVBoxLayout()
        
        # Título de categorías (mostrar todas, incluidas vacías)
        categories_title = QLabel(f"Seleccionar Categorías ({len(all_values)} disponibles):")
        categories_title.setStyleSheet("font-weight: bold; font-size: 14px; margin-bottom: 5px;")
        left_section.addWidget(categories_title)
        
        # Botones de selección rápida compactos
        # Botones de selección rápida con colores
        quick_select_layout = QHBoxLayout()
        toggle_all_btn = QPushButton("")
        toggle_all_btn.setFixedSize(20, 20)
        toggle_all_btn.setStyleSheet("QPushButton { background-color: transparent; border: 2px solid white; border-radius: 10px; } QPushButton:hover { background-color: rgba(255,255,255,0.1); }")
        
        select_vestuario_btn = QPushButton("👗 Vestuario")
        select_vestuario_btn.setMaximumHeight(25)
        select_vestuario_btn.setStyleSheet("background-color: #553c9a; color: white; font-weight: bold;")
        
        select_poses_btn = QPushButton("🤸 Poses")
        select_poses_btn.setMaximumHeight(25)
        select_poses_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        
        select_expresiones_btn = QPushButton("Expresiones")
        select_expresiones_btn.setMaximumHeight(25)
        select_expresiones_btn.setStyleSheet("background-color: #FF9800; color: white; font-weight: bold;")
        select_rasgo_btn = QPushButton("RasgoFisico")
        select_rasgo_btn.setMaximumHeight(25)
        select_rasgo_btn.setStyleSheet("background-color: #9E9E9E; color: white; font-weight: bold;")
        select_fondos_btn = QPushButton("Fondos")
        select_fondos_btn.setMaximumHeight(25)
        select_fondos_btn.setStyleSheet("background-color: #607D8B; color: white; font-weight: bold;")
        select_otros_btn = QPushButton("Otros")
        select_otros_btn.setMaximumHeight(25)
        select_otros_btn.setStyleSheet("background-color: #757575; color: white; font-weight: bold;")
        
        quick_select_layout.addWidget(toggle_all_btn)
        quick_select_layout.addWidget(select_vestuario_btn)
        quick_select_layout.addWidget(select_poses_btn)
        quick_select_layout.addWidget(select_expresiones_btn)
        quick_select_layout.addWidget(select_rasgo_btn)
        quick_select_layout.addWidget(select_fondos_btn)
        quick_select_layout.addWidget(select_otros_btn)
        quick_select_layout.addStretch()
        left_section.addLayout(quick_select_layout)
        
        # Área de scroll para categorías (OCUPA TODA LA ALTURA)
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setSpacing(2)  # Menos espacio entre elementos
        
        # Variable para almacenar imagen comprimida
        compressed_image_data = None
        
        # Crear checkboxes para cada categoría (incluye vacías) con LETRA MÁS GRANDE Y COLORES
        checkboxes = {}
        for category, value in all_values.items():
            checkbox = QCheckBox(f"{category}: {value[:45]}{'...' if len(value) > 45 else ''}")
            checkbox.setChecked(False)
            
            # LETRA MÁS GRANDE (12px) y colores por tipo de categoría
            category_lower = category.lower()
            if any(word in category_lower for word in ['vestuario', 'ropa', 'outfit', 'clothing']):
                # Vestuario - Azul
                checkbox.setStyleSheet("font-size: 12px; padding: 3px; color: #af69cd; font-weight: bold;")
            elif any(word in category_lower for word in ['direccion','orientacion','mirada','angulo','pose', 'postura', 'position']):
                # Poses - Verde
                checkbox.setStyleSheet("font-size: 12px; padding: 3px; color: #4CAF50; font-weight: bold;")
            elif any(word in category_lower for word in ['expresion', 'expression', 'cara', 'face']):
                # Expresiones - Naranja
                checkbox.setStyleSheet("font-size: 12px; padding: 3px; color: #FF9800; font-weight: bold;")
            elif any(word in category_lower for word in [ 'angle', 'vista', 'view']):
                # Ángulos - Púrpura
                checkbox.setStyleSheet("font-size: 12px; padding: 3px; color: #9C27B0; font-weight: bold;")
            elif any(word in category_lower for word in ['iluminacion', 'lighting', 'luz', 'light']):
                # Iluminación - Amarillo oscuro
                checkbox.setStyleSheet("font-size: 12px; padding: 3px; color: #F57C00; font-weight: bold;")
            elif any(word in category_lower for word in ['cabello', 'hair', 'pelo']):
                # Cabello - Marrón
                checkbox.setStyleSheet("font-size: 12px; padding: 3px; color: #795548; font-weight: bold;")
            elif any(word in category_lower for word in ['ojos', 'eyes', 'mirada']):
                # Ojos - Cian
                checkbox.setStyleSheet("font-size: 12px; padding: 3px; color: #00BCD4; font-weight: bold;")
            elif any(word in category_lower for word in ['fondo', 'background', 'escenario']):
                # Fondo - Gris oscuro
                checkbox.setStyleSheet("font-size: 12px; padding: 3px; color: #607D8B; font-weight: bold;")
            elif any(word in category_lower for word in ['accesorio', 'accessory', 'complemento']):
                # Accesorios - Rosa
                checkbox.setStyleSheet("font-size: 12px; padding: 3px; color: #E91E63; font-weight: bold;")
            else:
                # Otras categorías - Negro
                checkbox.setStyleSheet("font-size: 12px; padding: 3px; color: #333333; font-weight: bold;")
            
            checkboxes[category] = checkbox
            scroll_layout.addWidget(checkbox)
        
        # ESTAS LÍNEAS DEBEN ESTAR FUERA DEL BUCLE:
        scroll_widget.setLayout(scroll_layout)
        scroll_area.setWidget(scroll_widget)
        left_section.addWidget(scroll_area)
        
        # ===== FUNCIONES PARA BOTONES DE SELECCIÓN RÁPIDA =====
        def select_all():
            """Selecciona todos los checkboxes"""
            for checkbox in checkboxes.values():
                checkbox.setChecked(True)
        
        def deselect_all():
            """Deselecciona todos los checkboxes"""
            for checkbox in checkboxes.values():
                checkbox.setChecked(False)
        
        def select_vestuario():
            """Selecciona solo categorías de vestuario"""
            for category, checkbox in checkboxes.items():
                category_lower = category.lower()
                if any(word in category_lower for word in ['vestuario', 'ropa', 'outfit', 'clothing']):
                    checkbox.setChecked(True)
                else:
                    checkbox.setChecked(False)
            select_folder_for_keywords(['vestuario','ropa','outfit','clothing'])
        
        def select_poses():
            """Selecciona solo categorías de poses"""
            for category, checkbox in checkboxes.items():
                category_lower = category.lower()
                if any(word in category_lower for word in ['direccion','orientacion','mirada','angulo','pose', 'postura', 'position']):
                    checkbox.setChecked(True)
                else:
                    checkbox.setChecked(False)
            select_folder_for_keywords(['poses','pose','postura','orientacion','angulo'])
        
        def select_expresiones():
            """Selecciona solo categorías de expresiones"""
            for category, checkbox in checkboxes.items():
                category_lower = category.lower()
                if any(word in category_lower for word in ['expresion', 'expression', 'cara', 'face']):
                    checkbox.setChecked(True)
                else:
                    checkbox.setChecked(False)
            select_folder_for_keywords(['expresion','expresiones','expression','face'])
        def select_rasgos():
            for category, checkbox in checkboxes.items():
                cl = category.lower()
                is_pose = ('pose' in cl) or ('postura' in cl)
                include = False
                if cl.startswith('rasgo fisico') or ('tipo de cuerpo' in cl):
                    include = True
                if ('cabello forma' in cl) or ('cabello color' in cl) or ('ojos' in cl) or ('nsfw' in cl):
                    include = True
                if ('personaje' in cl) or ('loras personaje' in cl):
                    include = True
                excluded_specifics = ('expresion facial ojos' in cl) or ('direccion mirada personaje' in cl) or ('orientacion personaje' in cl)
                checkbox.setChecked(include and not is_pose and not excluded_specifics)
            select_folder_for_keywords(['rasgo','fisico','cuerpo','tipo de cuerpo','personaje'])
        def select_fondos():
            for category, checkbox in checkboxes.items():
                cl = category.lower()
                if any(word in cl for word in ['fondo', 'background', 'escenario', 'ambiente', 'paisaje']):
                    checkbox.setChecked(True)
                else:
                    checkbox.setChecked(False)
            select_folder_for_keywords(['fondo','fondos','escenario','background','ambiente','paisaje'])
        def select_otros():
            vest = ['vestuario', 'ropa', 'outfit', 'clothing']
            poses = ['direccion','orientacion','mirada','angulo','pose', 'postura', 'position']
            expr = ['expresion', 'expression', 'cara', 'face']
            rasg = ['rasgo', 'fisico', 'cuerpo', 'piernas', 'busto', 'cintura', 'brazo', 'piel']
            fondo = ['fondo', 'background', 'escenario', 'ambiente', 'paisaje']
            groups = vest + poses + expr + rasg + fondo
            for category, checkbox in checkboxes.items():
                cl = category.lower()
                if any(word in cl for word in groups):
                    checkbox.setChecked(False)
                else:
                    checkbox.setChecked(True)
            select_folder_for_keywords(['otros'])
        
        all_toggle_state = False
        def toggle_all():
            nonlocal all_toggle_state
            if not all_toggle_state:
                select_all()
                toggle_all_btn.setStyleSheet("QPushButton { background-color: #4CAF50; border: 2px solid white; border-radius: 10px; } QPushButton:hover { background-color: #43A047; }")
                all_toggle_state = True
            else:
                deselect_all()
                toggle_all_btn.setStyleSheet("QPushButton { background-color: transparent; border: 2px solid white; border-radius: 10px; } QPushButton:hover { background-color: rgba(255,255,255,0.1); }")
                all_toggle_state = False
        toggle_all_btn.clicked.connect(toggle_all)
        
        # ===== CONECTAR BOTONES A SUS FUNCIONES =====
        select_vestuario_btn.clicked.connect(select_vestuario)
        select_poses_btn.clicked.connect(select_poses)
        select_expresiones_btn.clicked.connect(select_expresiones)
        select_rasgo_btn.clicked.connect(select_rasgos)
        select_fondos_btn.clicked.connect(select_fondos)
        select_otros_btn.clicked.connect(select_otros)
        
        # ===== COLUMNA DERECHA: CONTROLES (30% del ancho) =====
        right_section = QVBoxLayout()
        right_section.setSpacing(15)
        
        # Carpeta
        right_section.addWidget(QLabel("Carpeta:"))
        type_combo = QComboBox()
        type_combo.setMaximumWidth(200)  # Limitar ancho del combo
        # Obtener todas las carpetas disponibles
        all_folders = self.presets_manager.get_all_preset_folders()
        for folder_id, folder_info in all_folders.items():
            type_combo.addItem(folder_info['display_name'], folder_id)
        right_section.addWidget(type_combo)
        def select_folder_for_keywords(keywords):
            kw = [k.lower() for k in keywords]
            count = type_combo.count()
            for i in range(count):
                text = (type_combo.itemText(i) or "").lower()
                data = (type_combo.itemData(i) or "").lower()
                comp = text + " " + data
                if any(k in comp for k in kw):
                    type_combo.setCurrentIndex(i)
                    break
        
        # Nombre del preset
        right_section.addWidget(QLabel("Nombre del Preset:"))
        name_input = QLineEdit()
        name_input.setMaximumWidth(200)  # Limitar ancho del input
        right_section.addWidget(name_input)
        
        
        # Separador
        separator = QLabel()
        separator.setStyleSheet("border-bottom: 1px solid #ccc; margin: 2px 0;")  # Reducir margen
        right_section.addWidget(separator)
        
        # Sección de imágenes de referencia (hasta 4)
        right_section.addWidget(QLabel("Imágenes de Referencia:"))
        
        # Container para las 4 imágenes en grid 2x2 más compacto
        images_container = QWidget()
        images_container.setMaximumWidth(210)  # Limitar ancho del contenedor de imágenes
        images_grid = QGridLayout(images_container)
        images_grid.setHorizontalSpacing(0)
        images_grid.setVerticalSpacing(0)
        images_grid.setContentsMargins(0, 0, 0, 0)  # Sin márgenes
        
        # Crear 4 espacios para imágenes
        self.image_previews = []
        for i in range(4):
            image_preview = QLabel(f"Imagen {i+1}\nNo seleccionada")
            image_preview.setFixedSize(100, 140)
            image_preview.setStyleSheet("border: 1px solid #ccc; background-color: #383b40; font-size: 10px;")  # Border más sutil
            image_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            # Posicionar en grid 2x2
            row = i // 2
            col = i % 2
            images_grid.addWidget(image_preview, row, col)
            self.image_previews.append(image_preview)
        
        right_section.addWidget(images_container)
        
        # Botones para manejo de imágenes
        images_buttons_layout = QHBoxLayout()
        
        select_images_btn = QPushButton("Agregar Imágenes ")
        select_images_btn.setMaximumHeight(25)
        images_buttons_layout.addWidget(select_images_btn)
        
        clear_images_btn = QPushButton("🗑️")
        clear_images_btn.setMaximumHeight(25)
        images_buttons_layout.addWidget(clear_images_btn)
        
        # AGREGAR ESTA LÍNEA QUE FALTA:
        right_section.addLayout(images_buttons_layout)
        
        # Inicializar lista de imágenes seleccionadas
        if not hasattr(self, 'selected_images'):
            self.selected_images = []
        
        # Funciones para manejo de imágenes
        def select_image():
            """Selecciona múltiples imágenes y las agrega a la lista"""
            remaining_slots = 4 - len(self.selected_images)
            if remaining_slots <= 0:
                QMessageBox.information(dialog, "Límite alcanzado", "Ya has seleccionado el máximo de 4 imágenes.")
                return
            
            file_paths, _ = QFileDialog.getOpenFileNames(  # Cambiar a getOpenFileNames para múltiple selección
                dialog,
                f"Seleccionar imágenes de referencia (máximo {remaining_slots})",
                "",
                "Archivos de imagen (*.png *.jpg *.jpeg *.bmp *.gif)"
            )
            
            if file_paths:
                # Limitar a los espacios disponibles
                files_to_process = file_paths[:remaining_slots]
                
                for file_path in files_to_process:
                    try:
                        # Cargar y redimensionar la imagen
                        pil_image = Image.open(file_path)
                        pil_image.thumbnail((160,160), Image.Resampling.LANCZOS)  # Cambiar a 100x100
                        
                        # Convertir a QPixmap
                        buffer = QBuffer()
                        buffer.open(QBuffer.OpenModeFlag.WriteOnly)
                        pil_image.save(buffer, format='PNG')
                        pixmap = QPixmap()
                        pixmap.loadFromData(buffer.data())
                        
                        # Agregar a la lista
                        self.selected_images.append(file_path)
                        
                        # Actualizar la vista previa
                        index = len(self.selected_images) - 1
                        if index < len(self.image_previews):
                            self.image_previews[index].setPixmap(pixmap)
                            self.image_previews[index].setText("")
                            self.image_previews[index].setStyleSheet("border: 2px solid white; background-color: #879999; border-radius: 4px;")
                        
                    except Exception as e:
                        QMessageBox.warning(dialog, "Error", f"No se pudo cargar la imagen {os.path.basename(file_path)}: {str(e)}")
                        continue
                
                # Mostrar mensaje informativo
                loaded_count = len(files_to_process)
                if loaded_count > 0:
                    QMessageBox.information(dialog, "Imágenes cargadas", f"Se cargaron {loaded_count} imagen(es) correctamente.")
        
        def clear_all_images():
            """Limpia todas las imágenes seleccionadas"""
            self.selected_images.clear()
            for i, preview in enumerate(self.image_previews):
                preview.clear()
                preview.setText(f"Imagen {i+1}\nNo seleccionada")
                preview.setStyleSheet("border: 2px solid gray; background-color: #f0f0f0; border-radius: 4px; font-size: 10px;")  # Aumentar font-size
        
        # Conectar botones
        select_images_btn.clicked.connect(select_image)
        clear_images_btn.clicked.connect(clear_all_images)
        
        # Espaciador para empujar botones hacia abajo
        right_section.addStretch()
        
        # Botón de acción
        buttons_layout = QHBoxLayout()
        save_btn = QPushButton("💾 Guardar Preset")
        save_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        buttons_layout.addStretch()
        buttons_layout.addWidget(save_btn)
        right_section.addLayout(buttons_layout)
        
        # Agregar las dos columnas al layout principal
        main_layout.addLayout(left_section, 7)  # 70% del ancho
        main_layout.addLayout(right_section, 3)  # 30% del ancho
        
        # Función para guardar el preset
        def save_preset():
            """Guarda el preset con las categorías y configuraciones seleccionadas"""
            preset_name = name_input.text().strip()
            if not preset_name:
                QMessageBox.warning(dialog, "Error", "Por favor ingresa un nombre para el preset.")
                return
            
            # Obtener la carpeta seleccionada
            selected_folder = type_combo.currentData()
            if not selected_folder:
                QMessageBox.warning(dialog, "Error", "Por favor selecciona una carpeta.")
                return

            # Obtener las categorías seleccionadas (guardar aunque estén vacías)
            selected_categories = {}
            for category, checkbox in checkboxes.items():
                if checkbox.isChecked():
                    if category in all_values:
                        selected_categories[category] = all_values[category]

            if not selected_categories:
                QMessageBox.warning(dialog, "Error", "Por favor selecciona al menos una categoría.")
                return

            try:
                # Crear el preset
                preset_data = {
                    'name': preset_name,
                    'categories': selected_categories,
                    'images': getattr(self, 'selected_images', []),
                    'created_at': datetime.now().isoformat()
                }
                
                # Guardar usando el presets_manager
                success = self.presets_manager.save_preset(selected_folder, preset_name, preset_data)
                
                if success:
                    QMessageBox.information(dialog, "Éxito", f"Preset '{preset_name}' guardado correctamente.")
                    # Recargar la lista de presets
                    self.load_presets()
                    dialog.accept()
                else:
                    QMessageBox.warning(dialog, "Error", "No se pudo guardar el preset.")
                    
            except Exception as e:
                QMessageBox.critical(dialog, "Error", f"Error al guardar el preset: {str(e)}")
        
        # Conectar botón
        save_btn.clicked.connect(save_preset)
        
        dialog.exec()

    def show_context_menu(self, position):
        """Muestra menú contextual con opciones al hacer clic derecho"""
        item = self.presets_tree.itemAt(position)
        if not item:
            return

        item_data = item.data(0, Qt.ItemDataRole.UserRole) or {}
        item_type = item_data.get('type')

        context_menu = QMenu(self)

        if item_type == 'preset' and item.parent() is not None:
            preset_name = item.text(0)
            category_id = item_data.get('category_id')
            # image_paths = item_data.get('image_paths', []) # Ya no se usa en el menú
            
            # La acción de ver imágenes ahora se hace con clic en el icono,
            # así que la quitamos del menú contextual para simplificar.

            delete_action = QAction("🗑️ Eliminar Preset", self)
            def do_delete():
                dlg = QDialog(self)
                dlg.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
                dlg.setModal(True)
                dlg.resize(280, 130)
                v = QVBoxLayout(dlg)
                m1 = QLabel(f"¿Eliminar el preset '{preset_name}'?")
                m2 = QLabel("Esta acción no se puede deshacer.")
                m1.setStyleSheet("color: white; font-size: 14px; font-weight: bold;")
                m2.setStyleSheet("color: #ffdddd; font-size: 12px;")
                dlg.setStyleSheet("background-color: #7f1d1d; border: 2px solid #ef4444; border-radius: 8px;")
                v.addWidget(m1)
                v.addWidget(m2)
                h = QHBoxLayout()
                cancel_btn = QPushButton("Cancelar")
                confirm_btn = QPushButton("Eliminar")
                cancel_btn.setStyleSheet("background-color: #555; color: white; padding: 6px 12px; border-radius: 4px;")
                confirm_btn.setStyleSheet("background-color: #dc2626; color: white; font-weight: bold; padding: 6px 12px; border-radius: 4px;")
                h.addStretch()
                h.addWidget(cancel_btn)
                h.addWidget(confirm_btn)
                v.addLayout(h)
                def on_confirm():
                    ok = self.presets_manager.delete_preset(category_id, preset_name)
                    if ok:
                        self.load_presets()
                        dlg.accept()
                    else:
                        QMessageBox.warning(self, "Error", "No se pudo eliminar el preset.")
                cancel_btn.clicked.connect(dlg.reject)
                confirm_btn.clicked.connect(on_confirm)
                dlg.exec()
            delete_action.triggered.connect(do_delete)
            context_menu.addAction(delete_action)
            edit_action = QAction("✏️ Editar Preset", self)
            edit_action.triggered.connect(lambda: self.open_edit_preset_dialog(item))
            context_menu.addAction(edit_action)

            # Ya no necesitamos la acción de Vista Previa en el menú contextual
            # preview_action = QAction("👁️ Vista Previa", self)
            # preview_action.triggered.connect(lambda: self.show_preset_preview(position))
            # context_menu.addAction(preview_action)

        elif item_type == 'category' and item.parent() is None:
            # Menú para carpetas
            folder_id = item_data.get('category_id')

            rename_action = QAction("✏️ Renombrar Carpeta", self)
            def do_rename():
                new_name, ok = QInputDialog.getText(self, "Renombrar Carpeta", "Nuevo nombre:")
                if not ok:
                    return
                success, new_folder_id = self.presets_manager.rename_folder(folder_id, new_name)
                if not success:
                    QMessageBox.warning(self, "Error", "No se pudo renombrar la carpeta. Verifica que el nombre no exista y sea válido.")
                    return
                # Recargar árbol
                self.load_presets()
            rename_action.triggered.connect(do_rename)
            context_menu.addAction(rename_action)

            delete_action = QAction("🗑️ Eliminar Carpeta", self)
            def do_delete():
                confirm = QMessageBox.question(self, "Eliminar Carpeta",
                                              f"¿Eliminar la carpeta '{item.text(0)}' y todos sus presets?",
                                              QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                              QMessageBox.StandardButton.No)
                if confirm != QMessageBox.StandardButton.Yes:
                    return
                if not self.presets_manager.delete_folder(folder_id):
                    QMessageBox.warning(self, "Error", "No se pudo eliminar la carpeta.")
                    return
                self.load_presets()
            delete_action.triggered.connect(do_delete)
            context_menu.addAction(delete_action)

        else:
            return

        global_pos = self.presets_tree.mapToGlobal(position)
        context_menu.exec(global_pos)

    def open_edit_preset_dialog(self, item):
        """Abre el diálogo de edición para el preset seleccionado"""
        if not item or item.parent() is None:
            return

        item_data = item.data(0, Qt.ItemDataRole.UserRole)
        if not item_data or item_data.get('type') != 'preset':
            return

        category_id = item_data.get('category_id')
        preset_data = item_data.get('preset_data', {})
        preset_name = preset_data.get('name', 'Sin nombre')

        # Cargar datos completos (incluye rutas absolutas de imágenes)
        full_preset_data = self.presets_manager.load_preset(category_id, preset_name) or {}
        categories = full_preset_data.get('categories', preset_data.get('categories', {}))
        images = full_preset_data.get('images', [])

        dialog = EditPresetDialog(self)
        dialog.setWindowTitle(f"Editar Preset - {preset_name}")
        dialog.set_preset_data(preset_name, category_id, categories, images)
        def on_accept():
            updated_categories = dialog.get_updated_categories()
            updated_images = dialog.get_selected_images()
            updated_name = getattr(dialog, 'get_preset_name', lambda: preset_name)()

            new_preset_data = {
                'name': updated_name,
                'categories': updated_categories,
                'images': updated_images,
                'created_at': datetime.now().isoformat()
            }

            if updated_name != preset_name:
                success_new = self.presets_manager.save_preset(category_id, updated_name, new_preset_data)
                if success_new:
                    if hasattr(self.presets_manager, 'delete_preset'):
                        try:
                            self.presets_manager.delete_preset(category_id, preset_name)
                        except Exception as e:
                            print(f"Advertencia: No se pudo eliminar el preset anterior: {e}")
                    QMessageBox.information(self, "Éxito", f"Preset renombrado a '{updated_name}' y actualizado correctamente.")
                    self.load_presets()
                else:
                    QMessageBox.warning(self, "Error", "No se pudo guardar el preset con el nuevo nombre.")
            else:
                success = self.presets_manager.save_preset(category_id, preset_name, new_preset_data)
                if success:
                    QMessageBox.information(self, "Éxito", f"Preset '{preset_name}' actualizado correctamente.")
                    self.load_presets()
                else:
                    QMessageBox.warning(self, "Error", "No se pudo actualizar el preset.")

        dialog.accepted.connect(on_accept)
        dialog.show()

    def show_preset_preview(self, position):
        """Muestra vista previa de imágenes del preset al hacer clic derecho"""
        print(f"DEBUG: show_preset_preview llamado en posición {position}")

        item = self.presets_tree.itemAt(position)
        if not item or item.parent() is None:
            print("DEBUG: No es un preset válido")
            return
            
        # Obtener datos del preset
        item_data = item.data(0, Qt.ItemDataRole.UserRole)
        if not item_data or item_data.get('type') != 'preset':
            print("DEBUG: Item no tiene datos de preset")
            return
            
        preset_data = item_data.get('preset_data', {})
        preset_name = preset_data.get('name', 'Sin nombre')
        categories_count = len(preset_data.get('categories', {}))
        
        print(f"DEBUG: Preset name: {preset_name}, categories: {categories_count}")
        
        # Cargar las rutas completas de las imágenes
        category_id = item_data.get('category_id')
        
        # Usar el presets_manager para cargar las imágenes correctamente
        full_preset_data = self.presets_manager.load_preset(category_id, preset_name)
        images = full_preset_data.get('images', []) if full_preset_data else []
        
        print(f"DEBUG: Imágenes encontradas: {len(images)}")
        
        header_html = f"""<div style='background-color: #2d2d2d; padding: 16px; border-radius: 10px; max-width: 450px; min-width: 380px; border: 3px solid #00ff00; box-shadow: 0 4px 8px rgba(0,0,0,0.5);'>
            <h3 style='color: #00ff00; margin: 0 0 12px 0; font-size: 16px; font-weight: bold; text-align: center;'>{preset_name}</h3>
            <p style='color: #ffffff; margin: 0 0 12px 0; font-size: 13px; text-align: center;'>📁 {categories_count} categorías</p>"""
        loading_html = "<p style='color: #bbb; font-size: 13px; text-align: center;'>Cargando imágenes…</p></div>"
        self.show_preview_overlay(item, header_html + loading_html)
        
        final_html = header_html
        if images:
            print(f"DEBUG: Procesando {len(images)} imágenes")
            images_html = "<div style='display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; margin-top: 12px;'>"
            for i, image_path in enumerate(images[:4]):
                print(f"DEBUG: Procesando imagen {i+1}: {image_path}")
                if os.path.exists(image_path):
                    try:
                        image_data = self._get_base64_thumb(image_path, size=120)
                        if image_data:
                            images_html += f"<img src='data:image/png;base64,{image_data}' style='border-radius: 6px; border: 2px solid #00ff00;'>"
                            print(f"DEBUG: Imagen {i+1} procesada correctamente")
                        else:
                            print(f"DEBUG: Error: imagen sin datos {image_path}")
                    except Exception as e:
                        print(f"DEBUG: Error cargando imagen {image_path}: {e}")
                else:
                    print(f"DEBUG: Imagen no existe: {image_path}")
            images_html += "</div>"
            final_html += images_html + "</div>"
        else:
            final_html += "<p style='color: #ffff00; margin: 0; font-size: 14px; font-style: italic; text-align: center;'>⚠️ Sin imágenes disponibles</p></div>"

        if getattr(self, '_preview_label', None):
            self._preview_label.setText(final_html)
            try:
                self._preview_label.adjustSize()
            except Exception:
                pass

    def _get_base64_thumb(self, image_path: str, size: int = 120):
        cached = self._image_thumb_cache.get((image_path, size))
        if cached:
            return cached
        pixmap = QPixmap(image_path)
        if pixmap.isNull():
            return None
        scaled = pixmap.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.FastTransformation)
        buffer = QBuffer()
        buffer.open(QBuffer.OpenModeFlag.WriteOnly)
        scaled.save(buffer, "PNG")
        data = buffer.data().toBase64().data().decode()
        self._image_thumb_cache[(image_path, size)] = data
        return data


    def filter_presets(self, text):
        """Filtra los presets basado en el texto de búsqueda"""
        search_text = text.lower().strip()
        
        # Iterar por todos los elementos del árbol
        root = self.presets_tree.invisibleRootItem()
        for i in range(root.childCount()):
            folder_item = root.child(i)
            folder_visible = False
            
            # Verificar si el nombre de la carpeta coincide
            if search_text in folder_item.text(0).lower():
                folder_visible = True
            
            # Verificar presets dentro de la carpeta
            for j in range(folder_item.childCount()):
                preset_item = folder_item.child(j)
                preset_name = preset_item.text(0).lower()
                
                if search_text == "" or search_text in preset_name:
                    preset_item.setHidden(False)
                    folder_visible = True
                else:
                    preset_item.setHidden(True)
            
            # Mostrar/ocultar carpeta basado en si tiene presets visibles
            folder_item.setHidden(not folder_visible)
            
            # Expandir carpeta si hay coincidencias y texto de búsqueda
            if folder_visible and search_text:
                folder_item.setExpanded(True)
            elif not search_text:
                folder_item.setExpanded(False)

    def show_all_items(self):
        """Muestra todos los elementos del árbol"""
        root = self.presets_tree.invisibleRootItem()
        for i in range(root.childCount()):
            folder_item = root.child(i)
            folder_item.setHidden(False)
            folder_item.setExpanded(False)
            
            for j in range(folder_item.childCount()):
                preset_item = folder_item.child(j)
                preset_item.setHidden(False)

    def create_new_folder(self):
        """Crea una nueva carpeta para organizar presets"""
        folder_name, ok = QInputDialog.getText(
            self, "Nueva Carpeta", "Nombre de la carpeta:"
        )
        
        if ok and folder_name.strip():
            try:
                success = self.presets_manager.create_custom_folder(folder_name.strip())
                if success:
                    self.load_presets()  # Recargar para mostrar la nueva carpeta
                    QMessageBox.information(
                        self, "Éxito", f"Carpeta '{folder_name}' creada exitosamente."
                    )
                else:
                    QMessageBox.warning(
                        self, "Error", f"No se pudo crear la carpeta. Puede que ya exista una carpeta con ese nombre."
                    )
            except Exception as e:
                QMessageBox.warning(
                    self, "Error", f"No se pudo crear la carpeta: {str(e)}"
                )

