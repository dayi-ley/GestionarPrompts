from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QFrame, QLineEdit, 
    QCompleter, QPushButton, QHBoxLayout, QGridLayout, QScrollArea, QSizePolicy,
    QFileDialog, QMessageBox  # Solo agregar estas dos
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QEvent
from PyQt6.QtGui import QPixmap, QCursor
from PIL import Image  # Agregar esta línea
import json
import os

class VisualTooltip(QWidget):
    """Tooltip que muestra opciones en cuadrícula con imágenes"""
    
    option_selected = pyqtSignal(str, str)  # option_id, label
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("""
            QWidget {
                background-color: rgba(45, 45, 45, 250);
                border: 2px solid #666;
                border-radius: 8px;
            }
        """)
        self.image_tooltip = None  # Para el tooltip de imagen
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)
        
        # Título del tooltip
        self.title_label = QLabel("Opciones disponibles:")
        self.title_label.setStyleSheet("""
            QLabel {
                color: #e0e0e0;
                font-size: 11px;
                font-weight: bold;
                margin-bottom: 4px;
            }
        """)
        layout.addWidget(self.title_label)
        
        # Área de scroll para las opciones
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMaximumHeight(300)
        scroll_area.setMaximumWidth(400)
        # Evitar scroll horizontal para limitar el ancho visual
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background-color: #555;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background-color: #777;
                border-radius: 4px;
            }
        """)
        
        # Widget contenedor para las opciones
        self.options_widget = QWidget()
        self.options_layout = QGridLayout(self.options_widget)
        self.options_layout.setSpacing(3)
        
        scroll_area.setWidget(self.options_widget)
        layout.addWidget(scroll_area)
        
    def show_options(self, options_list, options_data):
        """Muestra las opciones en el tooltip"""
        # Limpiar opciones anteriores
        for i in reversed(range(self.options_layout.count())):
            child = self.options_layout.itemAt(i)
            if child.widget():
                child.widget().deleteLater()
        
        row = 0
        col = 0
        max_cols = 3
        
        for option_id in options_list:
            option_data = options_data.get(option_id, {})
            # Mostrar el prompt en inglés en lugar de la etiqueta en español
            display_text = option_data.get("prompt", option_id)
            spanish_label = option_data.get("label", {}).get("es", option_id)
            image_path = option_data.get("image", "")
            # Convertir ruta relativa a absoluta
            if image_path:
                image_path = os.path.join("data", "sugeprompt", image_path)
            
            # Crear frame para cada opción (clickeable)
            option_frame = QFrame()
            option_frame.setFixedSize(80, 30)
            # Agregar tooltip con la traducción en español
            option_frame.setToolTip(spanish_label)
            option_frame.setStyleSheet("""
                QFrame {
                    background-color: #555;
                    border: 1px solid #777;
                    border-radius: 4px;
                    margin: 2px;
                }
                QFrame:hover {
                    border-color: #28a745;
                    background-color: #606060;
                    cursor: pointer;
                }
            """)
            
            # Hacer el frame clickeable - CORREGIDO
            option_frame.mousePressEvent = lambda event, oid=option_id, lbl=display_text, img=image_path, sp_lbl=spanish_label: self.handle_mouse_press(event, oid, lbl, img, sp_lbl)
            
            # Frame que se adapta al contenido (sin tamaño fijo)
            option_frame.setStyleSheet("""
                QFrame {
                    background-color: #444;
                    border: 1px solid #666;
                    border-radius: 3px;
                    padding: 2px;
                }
                QFrame:hover {
                    background-color: #555;
                    border-color: #888;
                }
            """)
            
            # Layout horizontal para que sea más compacto
            frame_layout = QHBoxLayout(option_frame)
            frame_layout.setContentsMargins(3, 2, 3, 2)  # Márgenes mínimos
            frame_layout.setSpacing(0)  # Sin espaciado
            
            # TODO: Implementar carga lazy de imágenes de referencia
            # Las imágenes se cargarán solo cuando se haga clic derecho
            # Esto mejorará el rendimiento con muchas opciones
            
            # Etiqueta de texto que se adapta al contenido
            text_label = QLabel(display_text)
            text_label.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
            text_label.setStyleSheet("""
                QLabel {
                    color: #333;
                    background-color: #f0f0f0;
                    border: 1px solid #ccc;
                    border-radius: 3px;
                    padding: 4px 8px;
                    font-size: 9px;
                }
                QLabel:hover {
                    background-color: #e0e0e0;
                }
            """)
            text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            text_label.setWordWrap(False)  # Sin wrap para mantener compacto
            text_label.setToolTip(f"{spanish_label}")  # Tooltip de la traduccion de cada opcion
            text_label.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)  # Se ajusta al contenido
            text_label.setStyleSheet("""
                QLabel {
                    color: #e0e0e0;
                    font-size: 9px;
                    font-weight: bold;
                    background-color: transparent;
                    border: none;
                    padding: 1px 3px;
                }
            """)
            # Limitar el ancho visual de cada opción y elidir el texto
            max_label_width = 100
            text_label.setFixedWidth(max_label_width)
            metrics = text_label.fontMetrics()
            elided = metrics.elidedText(display_text, Qt.TextElideMode.ElideRight, max_label_width - 8)
            text_label.setText(elided)
            frame_layout.addWidget(text_label)
            
            # Hacer que el frame se ajuste al contenido
            option_frame.adjustSize()
            
            # Añadir al grid
            self.options_layout.addWidget(option_frame, row, col)
            
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
        
        # Ajustar tamaño del tooltip
        self.adjustSize()
    
    def handle_mouse_press(self, event, option_id, label, image_path, spanish_label):
        """Maneja los clics del mouse en las opciones"""
        if event.button() == Qt.MouseButton.LeftButton:
            # Clic izquierdo: seleccionar opción
            self.on_option_clicked(option_id, label)
        elif event.button() == Qt.MouseButton.RightButton:
            # Clic derecho: mostrar imagen de referencia
            self.show_image_tooltip(event.globalPosition().toPoint(), image_path, spanish_label, option_id)
    
    def show_image_tooltip(self, position, image_path, label, option_id=None):
        """Muestra el tooltip de imagen de referencia"""
        if not self.image_tooltip:
            self.image_tooltip = ImageTooltip(self)
        
        # Obtener category del parent (ConfigSection)
        category = getattr(self.parent(), 'current_category', None) if self.parent() else None
        self.image_tooltip.show_image(image_path, label, option_id, category)
        
        # Posicionar el tooltip de imagen cerca del cursor
        self.image_tooltip.move(position.x() + 10, position.y() - 75)
        self.image_tooltip.show()
        
        # Auto-ocultar después de 3 segundos
        QTimer.singleShot(3000, self.image_tooltip.hide)
    
    def on_option_clicked(self, option_id, label):
        """Maneja el click en una opción"""
        self.option_selected.emit(option_id, label)
        self.hide()

class ImageTooltip(QWidget):
    """Tooltip secundario que muestra la imagen de referencia"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.ToolTip | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("""
            QWidget {
                background-color: rgba(30, 30, 30, 240);
                border: 2px solid #666;
                border-radius: 8px;
                padding: 8px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        #Lineas agregadas
        self.option_id = None
        self.category = None  # SOLO agregar esta línea
        
        self.image_label = QLabel()
        self.image_label.setFixedSize(200, 150)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setCursor(Qt.CursorShape.PointingHandCursor)  # Cursor de mano
        self.image_label.setStyleSheet("""
            QLabel {
                background-color: #444;
                border: 1px solid #666;
                border-radius: 4px;
            }
        """)
        self.image_label.mousePressEvent = self.load_new_image  # Evento click
        layout.addWidget(self.image_label)
        
        self.text_label = QLabel()
        self.text_label.setStyleSheet("""
            QLabel {
                color: #e0e0e0;
                font-size: 11px;
                font-weight: bold;
                text-align: center;
                margin-top: 4px;
            }
        """)
        layout.addWidget(self.text_label)
    
    def show_image(self, image_path, label, option_id=None, category=None):
        """Muestra la imagen y etiqueta"""
        self.option_id = option_id
        self.category = category
        self.text_label.setText(f"{label}\n(Click para cambiar imagen)")
        
        if image_path and os.path.exists(image_path):
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(
                    200, 150, 
                    Qt.AspectRatioMode.KeepAspectRatio, 
                    Qt.TransformationMode.SmoothTransformation
                )
                self.image_label.setPixmap(scaled_pixmap)
            else:
                self.image_label.setText("📷\nImagen no encontrada\n(Click para cargar)")
                self.image_label.setStyleSheet(self.image_label.styleSheet() + "font-size: 14px;")
        else:
            self.image_label.setText("📷\nSin imagen\n(Click para cargar)")
            self.image_label.setStyleSheet(self.image_label.styleSheet() + "font-size: 14px;")
    
    def load_new_image(self, event):
        """Abre diálogo para seleccionar nueva imagen"""
        if not self.option_id or not self.category:
            QMessageBox.warning(self, "Error", "No se puede cargar imagen: datos insuficientes")
            return
            
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar imagen de referencia",
            "", "Imágenes (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        
        if file_path:
            try:
                # Crear directorio si no existe
                ref_dir = os.path.join("data", "sugeprompt", "references", self.category)
                os.makedirs(ref_dir, exist_ok=True)
                
                # Guardar imagen optimizada
                new_path = self.save_optimized_image(file_path, ref_dir, self.option_id)
                
                # Actualizar JSON
                self.update_json_reference(new_path)
                
                # Recargar imagen en el tooltip
                pixmap = QPixmap(new_path)
                scaled_pixmap = pixmap.scaled(
                    200, 150, 
                    Qt.AspectRatioMode.KeepAspectRatio, 
                    Qt.TransformationMode.SmoothTransformation
                )
                self.image_label.setPixmap(scaled_pixmap)
                
                QMessageBox.information(self, "Éxito", "Imagen cargada y optimizada correctamente")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error al cargar imagen: {str(e)}")
    
    def save_optimized_image(self, source_path, target_dir, option_id):
        """Optimiza y guarda la imagen"""
        target_path = os.path.join(target_dir, f"{option_id}.jpg")
        
        # Abrir y optimizar con PIL
        with Image.open(source_path) as img:
            # Convertir a RGB si es necesario
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')
            
            # Redimensionar manteniendo aspecto
            img.thumbnail((400, 300), Image.Resampling.LANCZOS)
            
            # Guardar con compresión
            img.save(target_path, 'JPEG', quality=85, optimize=True)
        
        return target_path
    
    def update_json_reference(self, image_path):
        """Actualiza la referencia de imagen en el JSON"""
        try:
            json_path = os.path.join("data", "sugeprompt", "categories", f"{self.category}.json")
            
            if os.path.exists(json_path):
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Buscar y actualizar la opción
                for option in data.get('options', []):
                    if option.get('id') == self.option_id:
                        # Usar ruta relativa con extensión .jpg (que es como se guarda realmente)
                        rel_path = os.path.relpath(image_path, "data/sugeprompt")
                        # Cambiar la extensión a .jpg ya que save_optimized_image siempre guarda como JPG
                        rel_path = os.path.splitext(rel_path)[0] + '.jpg'
                        option['image'] = rel_path.replace("\\", "/")
                        break
                
                # Guardar cambios
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                    
        except Exception as e:
            print(f"Error actualizando JSON: {e}")

class OptionsTooltip(QWidget):
    """Tooltip principal que muestra opciones en cuadrícula"""
    
    option_selected = pyqtSignal(str, str)  # option_id, label
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("""
            QWidget {
                background-color: rgba(45, 45, 45, 250);
                border: 2px solid #666;
                border-radius: 8px;
            }
        """)
        self.image_tooltip = None
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)
        
        # Título del tooltip
        self.title_label = QLabel("Selecciona una opción:")
        self.title_label.setStyleSheet("""
            QLabel {
                color: #e0e0e0;
                font-size: 11px;
                font-weight: bold;
                margin-bottom: 4px;
            }
        """)
        layout.addWidget(self.title_label)
        
        # Área de scroll para las opciones
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMaximumHeight(300)
        scroll_area.setMaximumWidth(400)
        # Evitar scroll horizontal para limitar el ancho visual
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background-color: #555;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background-color: #777;
                border-radius: 4px;
            }
        """)
        
        # Widget contenedor para las opciones
        self.options_widget = QWidget()
        self.options_layout = QGridLayout(self.options_widget)
        self.options_layout.setSpacing(4)
        
        scroll_area.setWidget(self.options_widget)
        layout.addWidget(scroll_area)
        
    def show_options(self, options_data, options_list):
        """Muestra las opciones en cuadrícula"""
        # Limpiar opciones anteriores
        while self.options_layout.count():
            child = self.options_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        row = 0
        col = 0
        max_cols = 4  # Más columnas para mostrar más opciones
        
        for option_id in options_list:
            option_data = options_data.get(option_id, {})
            label = option_data.get("label", {}).get("es", option_id)
            image_path = option_data.get("image", "")
            # Convertir ruta relativa a absoluta
            if image_path:
                image_path = os.path.join("data", "sugeprompt", image_path)
            
            # Crear botón para cada opción
            option_btn = QPushButton(label)
            option_btn.setFixedSize(90, 30)
            option_btn.setStyleSheet("""
                QPushButton {
                    background-color: #555;
                    border: 1px solid #777;
                    border-radius: 4px;
                    color: #e0e0e0;
                    font-size: 9px;
                    font-weight: bold;
                    text-align: center;
                    padding: 4px;
                }
                QPushButton:hover {
                    border-color: #28a745;
                    background-color: #606060;
                }
                QPushButton:pressed {
                    background-color: #28a745;
                }
            """)
            # Elidir texto para que el botón no se expanda y mantener ancho
            metrics = option_btn.fontMetrics()
            elided_label = metrics.elidedText(label, Qt.TextElideMode.ElideRight, 80)
            option_btn.setText(elided_label)
            
            # Conectar click izquierdo para selección
            option_btn.clicked.connect(lambda checked, oid=option_id, lbl=label: self.on_option_clicked(oid, lbl))
            
            # Instalar filtro de eventos para clic derecho
            option_btn.installEventFilter(self)
            option_btn.option_id = option_id
            option_btn.option_label = label
            option_btn.image_path = image_path
            
            # Añadir al grid
            self.options_layout.addWidget(option_btn, row, col)
            
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
        
        # Ajustar tamaño del tooltip
        self.adjustSize()
    
    def eventFilter(self, obj, event):
        """Filtro de eventos para manejar clic derecho"""
        if event.type() == QEvent.Type.MouseButtonPress:
            if event.button() == Qt.MouseButton.RightButton:
                if hasattr(obj, 'option_id'):
                    self.show_image_tooltip(obj, obj.image_path, obj.option_label)
                    return True
        return super().eventFilter(obj, event)
    
    def show_image_tooltip(self, widget, image_path, label):
        """Muestra el tooltip de imagen"""
        if not self.image_tooltip:
            self.image_tooltip = ImageTooltip(self)
        
        # Obtener option_id y category del widget
        option_id = getattr(widget, 'option_id', None)
        category = getattr(self.parent(), 'current_category', None) if self.parent() else None
        self.image_tooltip.show_image(image_path, label, option_id, category)
        
        # Posicionar el tooltip de imagen
        widget_pos = widget.mapToGlobal(widget.rect().topRight())
        self.image_tooltip.move(widget_pos.x() + 10, widget_pos.y())
        self.image_tooltip.show()
        
        # Auto-ocultar después de 3 segundos
        QTimer.singleShot(3000, self.image_tooltip.hide)
    
    def on_option_selected(self, option_id, display_text):
        """Maneja la selección de una opción"""
        print(f"DEBUG ConfigSection: on_option_selected llamado con option_id={option_id}")
        
        # Insertar el prompt en inglés en el input
        option_data = self.options_data.get(option_id, {})
        print(f"DEBUG ConfigSection: option_data encontrada: {bool(option_data)}")
        print(f"DEBUG ConfigSection: option_data keys: {list(option_data.keys()) if option_data else 'None'}")
        
        prompt = option_data.get("prompt", option_id)
        self.value_input.setText(prompt)
        
        # Emitir señal con los datos de la opción seleccionada
        print(f"DEBUG ConfigSection: Emitiendo señal option_selected con option_id={option_id}")
        self.option_selected.emit(option_id, option_data)
    
    def setup_autocomplete(self, options):
        """Configura el autocompletado para el input"""
        option_prompts = []
        for option in options:
            option_data = self.options_data.get(option, {})
            # Usar el prompt en inglés para el autocompletado
            prompt = option_data.get("prompt", option)
            option_prompts.append(prompt)
        
        completer = QCompleter(option_prompts)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.value_input.setCompleter(completer)
    
    def clear_config(self):
        """Limpia el área de configuración"""
        while self.config_layout.count():
            child = self.config_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

class ConfigSection(QWidget):
    """Sección de configuración que muestra opciones según la categoría seleccionada"""
    
    option_selected = pyqtSignal(str, dict)  # option_id, option_data
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_category = None
        self.categories_data = {}
        self.options_data = {}
        self.options_tooltip = None
        self.load_data()
        self.setup_ui()
    
    def load_data(self):
        """Carga los datos de categorías y opciones desde los archivos JSON"""
        try:
            # Cargar categorías principales
            categories_path = os.path.join("data", "sugeprompt", "prompt_categories.json")
            with open(categories_path, 'r', encoding='utf-8') as f:
                self.categories_data = json.load(f)
            
            # Inicializar diccionario de opciones
            self.options_data = {}
            
            # Cargar opciones desde archivos individuales de categorías
            categories_dir = os.path.join("data", "sugeprompt", "categories")
            if os.path.exists(categories_dir):
                # Buscar archivos JSON en el directorio raíz
                for filename in os.listdir(categories_dir):
                    if filename.endswith('.json'):
                        category_file_path = os.path.join(categories_dir, filename)
                        try:
                            with open(category_file_path, 'r', encoding='utf-8') as f:
                                category_data = json.load(f)
                                # Agregar las opciones de esta categoría al diccionario global
                                if 'options' in category_data:
                                    self.options_data.update(category_data['options'])
                                # También agregar el archivo completo con su ID
                                if 'id' in category_data:
                                    self.options_data[category_data['id']] = category_data
                        except Exception as e:
                            print(f"Error cargando archivo de categoría {filename}: {e}")
                
                # Buscar archivos JSON en subcarpetas
                for item in os.listdir(categories_dir):
                    item_path = os.path.join(categories_dir, item)
                    if os.path.isdir(item_path):
                        for filename in os.listdir(item_path):
                            if filename.endswith('.json'):
                                category_file_path = os.path.join(item_path, filename)
                                try:
                                    with open(category_file_path, 'r', encoding='utf-8') as f:
                                        category_data = json.load(f)
                                        # Agregar las opciones de esta categoría al diccionario global
                                        if 'options' in category_data:
                                            self.options_data.update(category_data['options'])
                                        # También agregar el archivo completo con su ID
                                        if 'id' in category_data:
                                            self.options_data[category_data['id']] = category_data
                                except Exception as e:
                                    print(f"Error cargando archivo de categoría {filename}: {e}")
            
            # Fallback: cargar desde prompt_options.json si existe
            options_path = os.path.join("data", "sugeprompt", "prompt_options.json")
            if os.path.exists(options_path):
                try:
                    with open(options_path, 'r', encoding='utf-8') as f:
                        fallback_options = json.load(f)
                        # Agregar opciones que no estén ya cargadas
                        for key, value in fallback_options.items():
                            if key not in self.options_data:
                                self.options_data[key] = value
                except Exception as e:
                    print(f"Error cargando opciones de fallback: {e}")
                    
        except Exception as e:
            print(f"Error cargando datos principales: {e}")
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(8)
        
        # Título pequeño
        title = QLabel("Configuración")
        title.setStyleSheet("""
            QLabel {
                font-size: 12px;
                font-weight: bold;
                color: #e0e0e0;
                margin-bottom: 5px;
            }
        """)
        layout.addWidget(title)
        
        # Área de configuración
        self.config_area = QFrame()
        self.config_area.setStyleSheet("""
            QFrame {
                background-color: #272727;
                border: 1px solid #555;
                border-radius: 6px;
                padding: 10px;
            }
        """)
        
        self.config_layout = QVBoxLayout(self.config_area)
        self.show_default_message()
        
        layout.addWidget(self.config_area)
        
    
    def show_default_message(self):
        """Muestra mensaje por defecto cuando no hay categoría seleccionada"""
        self.clear_config()
        
        default_label = QLabel("Selecciona una categoría para configurar")
        default_label.setStyleSheet("""
            QLabel {
                color: #a0a0a0;
                font-style: italic;
                text-align: center;
                padding: 20px;
            }
        """)
        default_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.config_layout.addWidget(default_label)
    
    def update_category_config(self, category):
        """Actualiza la configuración según la categoría seleccionada"""
        self.current_category = category
        self.clear_config()
        
        # Obtener datos de la categoría
        category_info = self.categories_data.get("categorias", {}).get(category, {})
        if not category_info:
            return
        
        # Crear cuadrito de configuración
        config_box = QFrame()
        config_box.setStyleSheet("""
            QFrame {
                background-color: #1d2636;
                border: 1px solid #666;
                border-radius: 4px;
                padding: 8px;
                max-width: 250px;
            }
        """)
        
        box_layout = QVBoxLayout(config_box)
        box_layout.setContentsMargins(8, 8, 4, 8)
        box_layout.setSpacing(6)
        
        # Título de la categoría
        category_label = category_info.get("label", {}).get("es", category)
        category_title = QLabel(category_label)
        category_title.setStyleSheet("""
            QLabel {
                font-size: 11px;
                font-weight: bold;
                color: #e0e0e0;
                margin-bottom: 1px;
            }
        """)
        box_layout.addWidget(category_title)
        
        # Input con botón de opciones
        input_container = QHBoxLayout()
        input_container.setSpacing(4)
        
        self.value_input = QLineEdit()
        self.value_input.setPlaceholderText(f"Escribe o selecciona {category_label.lower()}...")
        self.value_input.setStyleSheet("""
            QLineEdit {
                background-color: #555;
                border: 1px solid #777;
                border-radius: 3px;
                padding: 4px 6px;
                color: #e0e0e0;
                font-size: 10px;
            }
            QLineEdit:focus {
                border-color: #28a745;
            }
        """)
        
        # Configurar autocompletado
        self.current_options = category_info.get("opciones", [])
        self.setup_autocomplete(self.current_options)
        
        # Botón de opciones
        self.options_btn = QPushButton("⚙")
        self.options_btn.setFixedSize(24, 24)
        self.options_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                border: none;
                border-radius: 3px;
                color: white;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #34ce57;
            }
            QPushButton:pressed {
                background-color: #28a745;
            }
        """)
        
        # Conectar click del botón
        self.options_btn.clicked.connect(self.show_options_tooltip)
        
        input_container.addWidget(self.value_input)
        input_container.addWidget(self.options_btn)
        
        box_layout.addLayout(input_container)
        
        self.config_layout.addWidget(config_box)
    
    def show_options_tooltip(self):
        """Muestra el tooltip de opciones"""
        if not hasattr(self, 'current_options') or not self.current_options:
            return
            
        if not self.options_tooltip:
            self.options_tooltip = VisualTooltip(self)
            self.options_tooltip.option_selected.connect(self.on_option_selected)
        
        # Actualizar contenido del tooltip
        self.options_tooltip.show_options(self.current_options, self.options_data)
        
        # Posicionar el tooltip cerca del botón
        button_pos = self.options_btn.mapToGlobal(self.options_btn.rect().bottomLeft())
        self.options_tooltip.move(button_pos.x() - 50, button_pos.y() + 5)
        self.options_tooltip.show()

    def on_option_selected(self, option_id, display_text):
        """Maneja la selección de una opción"""
        print(f"DEBUG ConfigSection: on_option_selected llamado con option_id={option_id}")
        
        # Insertar el prompt en inglés en el input
        option_data = self.options_data.get(option_id, {})
        print(f"DEBUG ConfigSection: option_data encontrada: {bool(option_data)}")
        print(f"DEBUG ConfigSection: option_data keys: {list(option_data.keys()) if option_data else 'None'}")
        
        prompt = option_data.get("prompt", option_id)
        self.value_input.setText(prompt)
        
        # Emitir señal con los datos de la opción seleccionada
        print(f"DEBUG ConfigSection: Emitiendo señal option_selected con option_id={option_id}")
        self.option_selected.emit(option_id, option_data)
    
    def setup_autocomplete(self, options):
        """Configura el autocompletado para el input"""
        option_prompts = []
        for option in options:
            option_data = self.options_data.get(option, {})
            # Usar el prompt en inglés para el autocompletado
            prompt = option_data.get("prompt", option)
            option_prompts.append(prompt)
        
        completer = QCompleter(option_prompts)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.value_input.setCompleter(completer)
    
    def clear_config(self):
        """Limpia el área de configuración"""
        while self.config_layout.count():
            child = self.config_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
