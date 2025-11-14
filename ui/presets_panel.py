from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
    QPushButton, QLineEdit, QLabel, QMessageBox, QInputDialog,
    QDialog, QComboBox, QCheckBox, QScrollArea, QTextEdit, QFileDialog, QGridLayout,
    QToolTip, QFrame, QMenu  # Mantener QToolTip y QFrame y agregar QMenu
)
from PyQt6.QtCore import Qt, pyqtSignal, QBuffer, QPoint  # Remover QTimer
from PyQt6.QtGui import QFont, QPixmap, QCursor, QAction
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
            for preset_id, preset_data in presets.items():
                preset_item = QTreeWidgetItem(category_item)
                preset_item.setText(0, preset_data.get('name', preset_id))
                preset_item.setData(0, Qt.ItemDataRole.UserRole, {
                    'type': 'preset',
                    'category_id': folder_id,
                    'preset_id': preset_id,
                    'preset_data': preset_data
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
        
        select_all_btn = QPushButton("✅ Todo")
        select_all_btn.setMaximumHeight(25)
        select_all_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        
        deselect_all_btn = QPushButton("❌ Nada")
        deselect_all_btn.setMaximumHeight(25)
        deselect_all_btn.setStyleSheet("background-color: #f44336; color: white; font-weight: bold;")
        
        select_vestuario_btn = QPushButton("👗 Vestuario")
        select_vestuario_btn.setMaximumHeight(25)
        select_vestuario_btn.setStyleSheet("background-color: #553c9a; color: white; font-weight: bold;")
        
        select_poses_btn = QPushButton("🤸 Poses")
        select_poses_btn.setMaximumHeight(25)
        select_poses_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        
        select_expresiones_btn = QPushButton("😊 Expresiones")
        select_expresiones_btn.setMaximumHeight(25)
        select_expresiones_btn.setStyleSheet("background-color: #FF9800; color: white; font-weight: bold;")
        
        quick_select_layout.addWidget(select_all_btn)
        quick_select_layout.addWidget(deselect_all_btn)
        quick_select_layout.addWidget(select_vestuario_btn)
        quick_select_layout.addWidget(select_poses_btn)
        quick_select_layout.addWidget(select_expresiones_btn)
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
            checkbox.setChecked(True)
            
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
        
        def select_poses():
            """Selecciona solo categorías de poses"""
            for category, checkbox in checkboxes.items():
                category_lower = category.lower()
                if any(word in category_lower for word in ['direccion','orientacion','mirada','angulo','pose', 'postura', 'position']):
                    checkbox.setChecked(True)
                else:
                    checkbox.setChecked(False)
        
        def select_expresiones():
            """Selecciona solo categorías de expresiones"""
            for category, checkbox in checkboxes.items():
                category_lower = category.lower()
                if any(word in category_lower for word in ['expresion', 'expression', 'cara', 'face']):
                    checkbox.setChecked(True)
                else:
                    checkbox.setChecked(False)
        
        # ===== CONECTAR BOTONES A SUS FUNCIONES =====
        select_all_btn.clicked.connect(select_all)
        deselect_all_btn.clicked.connect(deselect_all)
        select_vestuario_btn.clicked.connect(select_vestuario)
        select_poses_btn.clicked.connect(select_poses)
        select_expresiones_btn.clicked.connect(select_expresiones)
        
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
        
        # Botones de acción
        buttons_layout = QHBoxLayout()
        cancel_btn = QPushButton("Cancelar")
        save_btn = QPushButton("💾 Guardar Preset")
        save_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        buttons_layout.addWidget(cancel_btn)
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
        
        # Conectar botones
        cancel_btn.clicked.connect(dialog.reject)
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
            # Menú para presets
            edit_action = QAction("✏️ Editar Preset", self)
            edit_action.triggered.connect(lambda: self.open_edit_preset_dialog(item))
            context_menu.addAction(edit_action)

            preview_action = QAction("👁️ Vista Previa", self)
            preview_action.triggered.connect(lambda: self.show_preset_preview(position))
            context_menu.addAction(preview_action)

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
        if dialog.exec():
            # Guardar cambios (posible renombre si el nombre cambia)
            updated_categories = dialog.get_updated_categories()
            updated_images = dialog.get_selected_images()
            updated_name = getattr(dialog, 'get_preset_name', lambda: preset_name)()

            new_preset_data = {
                'name': updated_name,
                'categories': updated_categories,
                'images': updated_images,
                'created_at': datetime.now().isoformat()
            }

            # Si el nombre cambió, guardar con el nuevo nombre y eliminar el antiguo
            if updated_name != preset_name:
                success_new = self.presets_manager.save_preset(category_id, updated_name, new_preset_data)
                if success_new:
                    # Eliminar el preset anterior para simular "renombrar"
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
                # Nombre no cambió: comportamiento original de actualización
                success = self.presets_manager.save_preset(category_id, preset_name, new_preset_data)
                if success:
                    QMessageBox.information(self, "Éxito", f"Preset '{preset_name}' actualizado correctamente.")
                    self.load_presets()
                else:
                    QMessageBox.warning(self, "Error", "No se pudo actualizar el preset.")

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
        
        # Crear contenido del tooltip
        tooltip_html = f"""<div style='background-color: #2d2d2d; padding: 20px; border-radius: 10px; max-width: 600px; min-width: 400px; border: 3px solid #00ff00; box-shadow: 0 4px 8px rgba(0,0,0,0.5);'>
            <h3 style='color: #00ff00; margin: 0 0 15px 0; font-size: 18px; font-weight: bold; text-align: center;'>{preset_name}</h3>
            <p style='color: #ffffff; margin: 0 0 15px 0; font-size: 14px; text-align: center;'>📁 {categories_count} categorías</p>"""
        
        if images:
            print(f"DEBUG: Procesando {len(images)} imágenes")
            # Cargar y mostrar hasta 4 imágenes en miniatura
            images_html = "<div style='display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; margin-top: 15px;'>"
            for i, image_path in enumerate(images[:4]):
                print(f"DEBUG: Procesando imagen {i+1}: {image_path}")
                if os.path.exists(image_path):
                    try:
                        # Cargar y redimensionar imagen
                        pixmap = QPixmap(image_path)
                        if not pixmap.isNull():
                            # Redimensionar a 150x150 manteniendo aspecto
                            scaled_pixmap = pixmap.scaled(150, 150, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                            
                            # Convertir a base64 para HTML
                            buffer = QBuffer()
                            buffer.open(QBuffer.OpenModeFlag.WriteOnly)
                            scaled_pixmap.save(buffer, "PNG")
                            image_data = buffer.data().toBase64().data().decode()
                            
                            images_html += f"<img src='data:image/png;base64,{image_data}' style='width: 150px; height: 150px; border-radius: 8px; object-fit: cover; border: 2px solid #00ff00; box-shadow: 0 2px 4px rgba(0,255,0,0.3);'>"
                            print(f"DEBUG: Imagen {i+1} procesada correctamente")
                        else:
                            print(f"DEBUG: Error: pixmap nulo para {image_path}")
                    except Exception as e:
                        print(f"DEBUG: Error cargando imagen {image_path}: {e}")
                else:
                    print(f"DEBUG: Imagen no existe: {image_path}")
                    
            images_html += "</div>"
            tooltip_html += images_html
        else:
            tooltip_html += "<p style='color: #ffff00; margin: 0; font-size: 14px; font-style: italic; text-align: center;'>⚠️ Sin imágenes disponibles</p>"
            
        tooltip_html += "</div>"
        
        # Mostrar tooltip en la posición del click derecho
        global_pos = self.presets_tree.mapToGlobal(position)
        global_pos.setX(global_pos.x() + 15)
        global_pos.setY(global_pos.y() - 15)
        
        print(f"DEBUG: Posición global del tooltip: {global_pos}")
        print(f"DEBUG: Contenido HTML del tooltip: {tooltip_html[:200]}...")
        
        # Mostrar tooltip que permanecerá visible por 15 segundos
        QToolTip.showText(global_pos, tooltip_html, self.presets_tree, self.presets_tree.rect(), 15000)
        print("DEBUG: QToolTip.showText ejecutado")


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

