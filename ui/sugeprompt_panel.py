from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, 
    QScrollArea, QFrame, QPushButton, QDialog, QSplitter
)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint
from PyQt6.QtGui import QFont, QMouseEvent
from .sugeprompt.category_section import CategorySection
from .sugeprompt.config_section import ConfigSection
# Eliminamos la importación de NodeFlowSection
# from .sugeprompt.results_section import NodeFlowSection
from .sugeprompt.column_system import ColumnSystem

class MinimizedBubble(QWidget):
    """Burbuja flotante que aparece cuando se minimiza el diálogo"""
    
    restore_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(120, 40)
        
        # Variables para el arrastre
        self.dragging = False
        self.drag_position = QPoint()
        
        self.setup_ui()
        
        # Posicionar en la esquina superior derecha
        screen = self.screen().geometry()
        self.move(screen.width() - 140, 20)
    
    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Botón para restaurar
        restore_btn = QPushButton("📝 Prompts")
        restore_btn.clicked.connect(self.restore_requested.emit)
        restore_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(74, 144, 226, 200);
                color: white;
                border: none;
                border-radius: 15px;
                font-size: 10px;
                font-weight: bold;
                padding: 5px 10px;
            }
            QPushButton:hover {
                background-color: rgba(53, 122, 189, 220);
            }
        """)
        layout.addWidget(restore_btn)
    
    def setup_styles(self):
        """Configura los estilos del diálogo"""
        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
                color: #e0e0e0;
            }
            QLabel {
                background: transparent;
            }
        """)
    
    def mousePressEvent(self, event: QMouseEvent):
        """Inicia el arrastre de la ventana"""
        if event.button() == Qt.MouseButton.LeftButton:
            # Solo permitir arrastre desde la barra de título (primeros 40 píxeles)
            if event.position().y() <= 40:
                self.dragging = True
                self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                event.accept()
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """Mueve la ventana durante el arrastre"""
        if event.buttons() == Qt.MouseButton.LeftButton and self.dragging:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        """Termina el arrastre de la ventana"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = False
            event.accept()

class SugerenciaPromptDialog(QDialog):
    """Diálogo para generar sugerencias de prompts - TODO: Implementar funcionalidad"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle("Sugerencia de Prompt")
        self.setModal(False)  # CAMBIO: De True a False
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)  # CAMBIO: Dialog a Window
        
        # Variables para el arrastre de ventana
        self.dragging = False
        self.drag_position = QPoint()
        
        # Variable para controlar el estado minimizado
        self.is_minimized = False
        self.normal_size = (1300, 680)
        self.minimized_size = (200, 50)  # AGREGAR: tamaño minimizado
        self.bubble = None  # Inicializar bubble como None
        
        # Ventana más grande y responsiva
        self.setMinimumSize(200, 50)  # Permitir tamaño mínimo pequeño
        self.resize(1300, 680)
        self.setup_ui()
        self.setup_styles()
        # ELIMINAR: self.center() - no es necesario para el funcionamiento
    
    def toggle_minimize(self):
        """Alterna entre tamaño normal y minimizado"""
        if self.is_minimized:
            # Restaurar tamaño normal
            self.resize(*self.normal_size)
            self.content_widget.show()
            self.minimize_button.setText("−")
            self.is_minimized = False
            # Mover al centro de la pantalla al restaurar
            screen = self.screen().geometry()
            self.move((screen.width() - self.width()) // 2, (screen.height() - self.height()) // 2)
        else:
            # Minimizar a tamaño pequeño
            self.resize(*self.minimized_size)
            self.content_widget.hide()
            self.minimize_button.setText("□")
            self.is_minimized = True
            
            # Mover a esquina superior derecha
            screen = self.screen().geometry()
            self.move(screen.width() - 220, 20)
    
    def setup_ui(self):
        """Configura la interfaz del diálogo con 3 secciones"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Barra de título personalizada con botones
        title_container = QWidget()
        title_container.setFixedHeight(40)
        title_container.setStyleSheet("""
            QWidget {
                background-color: #333c4d;
                border-bottom: 1px solid #9b59b6;
            }
        """)
        title_container.setCursor(Qt.CursorShape.SizeAllCursor)
        
        title_layout = QHBoxLayout(title_container)
        title_layout.setContentsMargins(15, 0, 10, 0)
        
        # Título de la ventana
        self.title_label = QLabel("Generar Sugerencia de Prompt")
        self.title_label.setStyleSheet("""
            QLabel {
                color: #e0e0e0;
                font-size: 14px;
                font-weight: bold;
                background: transparent;
            }
        """)
        title_layout.addWidget(self.title_label)
        title_layout.addStretch()
        
        # Botón minimizar/restaurar
        self.minimize_button = QPushButton("−")
        self.minimize_button.setFixedSize(30, 30)
        self.minimize_button.clicked.connect(self.toggle_minimize)
        self.minimize_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #e0e0e0;
                border: none;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #404040;
                border-radius: 15px;
            }
            QPushButton:pressed {
                background-color: #505050;
            }
        """)
        title_layout.addWidget(self.minimize_button)
        
        # Botón cerrar
        close_button = QPushButton("×")
        close_button.setFixedSize(30, 30)
        close_button.clicked.connect(self.close)
        close_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #e0e0e0;
                border: none;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e74c3c;
                border-radius: 15px;
            }
            QPushButton:pressed {
                background-color: #c0392b;
            }
        """)
        title_layout.addWidget(close_button)
        
        main_layout.addWidget(title_container)
        
        # Contenedor para las secciones (se puede ocultar)
        self.content_widget = QWidget()
        content_layout = QVBoxLayout(self.content_widget)
        content_layout.setContentsMargins(5, 3, 20, 15)
        content_layout.setSpacing(6)
        
        # SECCIÓN 1: Elección de Categoría
        self.category_section = CategorySection()  # Cambiar a self.category_section
        content_layout.addWidget(self.category_section)
        
        # SECCIÓN 2: Configuración
        self.config_section = ConfigSection()  # Cambiar a self.config_section
        content_layout.addWidget(self.config_section)
        
        # CONECTAR SEÑALES: Cuando se selecciona una categoría, actualizar configuración
        self.category_section.category_selected.connect(self.config_section.update_category_config)
        
        # CONECTAR SEÑALES: Cuando se selecciona una opción, activar área de prompt
        # Cambiar esta línea:
        # self.config_section.option_selected.connect(self.activate_prompt_area)
        # Por esta:
        self.config_section.option_selected.connect(lambda option_id, option_data: self.add_suggestion_to_prompt(option_data.get('prompt', option_id.replace('_', ' '))))
        
        # En el método setup_ui de SugerenciaPromptDialog, después de crear self.prompt_area
        # Alrededor de la línea 240
        
        # Área de Prompt
        self.prompt_area = self.create_prompt_area()
        
        # SECCIÓN 3: Sistema de Columnas
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        
        # Crear y agregar el sistema de columnas primero (lado izquierdo)
        self.column_system = ColumnSystem()
        splitter.addWidget(self.column_system)
        
        # Agregar el área de prompt al splitter (lado derecho)
        splitter.addWidget(self.prompt_area)
        
        # Establecer proporciones iniciales (60% columnas, 40% prompt)
        splitter.setSizes([30, 70])
        
        # Agregar el splitter al layout principal en lugar del prompt_area directamente
        content_layout.addWidget(splitter)
        
        # Conectar la señal de opción seleccionada al sistema de columnas
        self.config_section.option_selected.connect(self.activate_column_system)
        
        main_layout.addWidget(self.content_widget)

        main_layout.addWidget(self.content_widget)  # CAMBIAR: content_widget → self.content_widget
    
    def activate_node_flow(self, option_id, option_data):
        """Activa el flujo de nodos cuando se selecciona una opción"""
        import sys
        print(f"DEBUG SugePromptPanel: activate_node_flow llamado con option_id={option_id}", flush=True)
        print(f"DEBUG SugePromptPanel: option_data type: {type(option_data)}", flush=True)
        
        # Verificar si es school_uniform y cargar datos específicos
        if option_id == 'school_uniform':
            print(f"DEBUG SugePromptPanel: Detectada opción school_uniform, cargando datos específicos", flush=True)
            sys.stdout.flush()
            
            # Cargar datos específicos del archivo JSON
            import os
            import json
            option_file_path = os.path.join('data', 'sugeprompt', 'categories', 'vestuario_general', f"{option_id}.json")
            
            if os.path.exists(option_file_path):
                try:
                    with open(option_file_path, 'r', encoding='utf-8') as file:
                        specific_data = json.load(file)
                        
                    # Combinar datos específicos con los datos generales
                    if isinstance(option_data, dict) and isinstance(specific_data, dict):
                        for key, value in specific_data.items():
                            if key not in option_data:
                                option_data[key] = value
                        
                    # Eliminamos los print con flush=True
                except Exception as e:
                    # Eliminamos los print con flush=True
                    pass
        
        self.node_flow_section.load_option(option_id, option_data)
    
    def activate_column_system(self, option_id, option_data):
        """Activa el sistema de columnas cuando se selecciona una opción"""
        print(f"DEBUG: activate_column_system llamado con option_id={option_id}")
        
        # Verificar si es school_uniform y cargar datos específicos
        if option_id == 'school_uniform':
            # Cargar datos específicos del archivo JSON
            import os
            import json
            option_file_path = os.path.join('data', 'sugeprompt', 'categories', 'vestuario_general', f"{option_id}.json")
            
            if os.path.exists(option_file_path):
                try:
                    with open(option_file_path, 'r', encoding='utf-8') as file:
                        specific_data = json.load(file)
                        
                    # Combinar datos específicos con los datos generales
                    if isinstance(option_data, dict) and isinstance(specific_data, dict):
                        for key, value in specific_data.items():
                            if key not in option_data:
                                option_data[key] = value
                except Exception as e:
                    print(f"Error al cargar datos específicos: {e}")
        
        # Pasar los datos al sistema de columnas
        self.column_system.load_option(option_id, option_data)
        
        # También podemos agregar la sugerencia al prompt
        # Extraer el texto de sugerencia del prompt o usar el option_id como fallback
        suggestion_text = option_data.get('prompt', option_id.replace('_', ' '))
        self.add_suggestion_to_prompt(suggestion_text)
    
    def on_category_selected(self, category_label):
        """Maneja la selección de una categoría"""
        # Limpiar el área de prompt y agregar la categoría
        self.prompt_text_area.clear()
        self.prompt_text_area.setPlainText(category_label)
    
    def on_item_selected(self, item_label):
        """Maneja la selección de un item desde la columna Items"""
        # Agregar el item al prompt existente
        current_text = self.prompt_text_area.toPlainText().strip()
        if current_text:
            new_text = f"{current_text}, {item_label}"
        else:
            new_text = item_label
        self.prompt_text_area.setPlainText(new_text)
        
    def add_suggestion_to_prompt(self, suggestion):
        """Agrega una sugerencia al área de texto del prompt"""
        current_text = self.prompt_text_area.toPlainText().strip()
        
        if current_text:
            # Si ya hay texto, agregar con coma
            new_text = f"{current_text}, {suggestion}"
        else:
            # Si está vacío, agregar directamente
            new_text = suggestion
        
        self.prompt_text_area.setPlainText(new_text)
        # Mover cursor al final
        cursor = self.prompt_text_area.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.prompt_text_area.setTextCursor(cursor)
    
    def create_prompt_area(self):
        """Crea el área de prompt con botones horizontales"""
        prompt_widget = QWidget()
        prompt_layout = QVBoxLayout(prompt_widget)
        prompt_layout.setContentsMargins(10, 5, 10, 5)
        prompt_layout.setSpacing(8)
        
        # Título pequeño
        title = QLabel("Prompt Generado")
        title.setStyleSheet("""
            QLabel {
                font-size: 12px;
                font-weight: bold;
                color: #e0e0e0;
                margin-bottom: 5px;
            }
        """)
        prompt_layout.addWidget(title)
        
        # Área de texto del prompt
        self.prompt_text_area = QTextEdit()
        self.prompt_text_area.setPlaceholderText("El prompt generado aparecerá aquí...")
        self.prompt_text_area.setStyleSheet("""
            QTextEdit {
                background-color: #383838;
                border: 1px solid #555;
                border-radius: 6px;
                padding: 10px;
                color: #e0e0e0;
                font-size: 11px;
                line-height: 1.4;
            }
        """)
        prompt_layout.addWidget(self.prompt_text_area)
        
        # Botones horizontales
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(5)
        
        # Crear botones
        button_configs = [
            ("Copiar", "#4a90e2", "#357abd"),
            ("Guardar", "#27ae60", "#219a52"),
            ("Limpiar", "#e74c3c", "#c0392b"),
            ("Generar", "#9b59b6", "#8e44ad"),
            ("Aplicar Sugerencias", "#3498db", "#2980b9")
        ]
        
        for text, bg_color, hover_color in button_configs:
            button = QPushButton(text)
            button.setFixedHeight(28)
            button.clicked.connect(lambda checked, action=text: self.on_prompt_action(action))
            button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {bg_color};
                    color: white;
                    border: none;
                    border-radius: 4px;
                    font-size: 10px;
                    font-weight: 600;
                    padding: 4px 8px;
                }}
                QPushButton:hover {{
                    background-color: {hover_color};
                }}
                QPushButton:pressed {{
                    background-color: {hover_color};
                    transform: translateY(1px);
                }}
            """)
            buttons_layout.addWidget(button)
        
        prompt_layout.addLayout(buttons_layout)
        
        return prompt_widget
    
    def on_prompt_action(self, action):
        """Maneja las acciones de los botones del área de prompt"""
        if action == "Limpiar":
            self.prompt_text_area.clear()
        elif action == "Copiar":
            text = self.prompt_text_area.toPlainText()
            if text.strip():
                try:
                    import pyperclip
                    pyperclip.copy(text)
                    print("Prompt copiado al portapapeles")
                except ImportError:
                    print("pyperclip no disponible - instalar con: pip install pyperclip")
        elif action == "Guardar":
            print("TODO: Guardar prompt en historial")
        elif action == "Generar":
            # Generar prompt básico
            prompt_parts = ["masterpiece, best quality, ultra detailed", "1girl, portrait", "professional photography, cinematic lighting"]
            generated_prompt = ", ".join(prompt_parts)
            
            current_text = self.prompt_text_area.toPlainText().strip()
            if current_text:
                final_prompt = f"{current_text}, {generated_prompt}"
            else:
                final_prompt = generated_prompt
            
            self.prompt_text_area.setPlainText(final_prompt)
        elif action == "Aplicar Sugerencias":
            # Aplicar sugerencias seleccionadas
            print("Sugerencias aplicadas al prompt")
            # Aquí se podría implementar lógica adicional como guardar el prompt
            # o enviarlo a otro componente de la aplicación
    
    def create_section_frame(self, min_height):
        """Crea un frame de sección con título y altura mínima"""
        frame = QFrame()
        frame.setMinimumHeight(min_height)
        frame.setStyleSheet("""
            QFrame {
                background-color: #333;
                border: 2px solid #555;
                border-radius: 8px;
                margin: 3px;
            }
        """)
        return frame
    
    def setup_styles(self):
        """Configura los estilos del diálogo"""
        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
                color: #e0e0e0;
            }
            QLabel {
                background: transparent;
            }
        """)
    
    def mousePressEvent(self, event: QMouseEvent):
        """Inicia el arrastre de la ventana"""
        if event.button() == Qt.MouseButton.LeftButton:
            # Solo permitir arrastre desde la barra de título (primeros 40 píxeles)
            if event.position().y() <= 40:
                self.dragging = True
                self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                event.accept()
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """Mueve la ventana durante el arrastre"""
        if event.buttons() == Qt.MouseButton.LeftButton and self.dragging:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        """Termina el arrastre de la ventana"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = False
            event.accept()

class SugePromptPanel(QWidget):
    """Panel para sugerencias de prompts - TODO: Implementar funcionalidad"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_widget = parent
        self.current_dialog = None  # Referencia al diálogo actual
        self.setup_ui()
        self.setup_styles()
    
    def open_suggestion_dialog(self):
        """Abre el diálogo de sugerencias"""
        if self.current_dialog and self.current_dialog.isHidden():
            # Si existe un diálogo oculto, lo restauramos
            self.current_dialog.show()
            self.current_dialog.raise_()
            self.current_dialog.activateWindow()
        else:
            # Crear nuevo diálogo
            self.current_dialog = SugerenciaPromptDialog(self)
            self.current_dialog.show()  # CAMBIO: exec() por show()
    
    def setup_ui(self):
        """Configura la interfaz del panel de sugerencias"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # Título
        title = QLabel("Sugerencias de Prompts")
        title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Sección vacía para futuras implementaciones
        empty_section = QFrame()
        empty_section.setStyleSheet("""
            QFrame {
                background-color: #333;
                border: 1px solid #555;
                border-radius: 6px;
                margin: 2px;
                min-height: 80px;
            }
        """)
        
        empty_layout = QVBoxLayout(empty_section)
        empty_layout.setContentsMargins(16, 16, 16, 16)
        
        empty_label = QLabel("📝 Sección por implementar")
        empty_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        empty_label.setStyleSheet("color: #888; text-align: center;")
        empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(empty_label)
        
        empty_desc = QLabel("Esta área contendrá funcionalidades adicionales")
        empty_desc.setFont(QFont("Segoe UI", 9))
        empty_desc.setStyleSheet("color: #666;")
        empty_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(empty_desc)
        
        layout.addWidget(empty_section)
        
        # Botón para generar sugerencia
        self.generate_button = QPushButton("🚀 Generar Sugerencia de Prompt")
        self.generate_button.setFixedHeight(40)
        self.generate_button.clicked.connect(self.open_suggestion_dialog)
        self.generate_button.setStyleSheet("""
            QPushButton {
                background-color: #4a90e2;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 12px;
                font-weight: 600;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #357abd;
            }
            QPushButton:pressed {
                background-color: #2968a3;
            }
        """)
        layout.addWidget(self.generate_button)
        
        # Área de contenido TODO (reducida)
        content_frame = QFrame()
        content_frame.setStyleSheet("""
            QFrame {
                background-color: #333;
                border: 1px solid #555;
                border-radius: 6px;
                margin: 2px;
            }
        """)
        
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(12, 12, 12, 12)
        content_layout.setSpacing(8)
        
        # TODO Label (más pequeño)
        todo_title = QLabel("🚧 Funcionalidades Pendientes")
        todo_title.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        todo_title.setStyleSheet("color: #ffa500;")
        content_layout.addWidget(todo_title)
        
        # Lista compacta de funcionalidades
        todo_description = QLabel(
            "• Recomendaciones contextuales\n"
            "• Plantillas predefinidas"
        )
        todo_description.setFont(QFont("Segoe UI", 9))
        todo_description.setStyleSheet("color: #a0a0a0;")
        todo_description.setWordWrap(True)
        content_layout.addWidget(todo_description)
        
        layout.addWidget(content_frame)
        layout.addStretch()
    
    def open_suggestion_dialog(self):
        """Abre el diálogo de sugerencias"""
        dialog = SugerenciaPromptDialog(self)
        dialog.show()  # CAMBIO: exec() por show()
    
    def setup_styles(self):
        """Configura los estilos del panel"""
        self.setStyleSheet("""
            QWidget {
                background-color: #2b2b2b;
                color: #e0e0e0;
            }
            QLabel {
                background: transparent;
            }
        """)

    # Añadir la importación al inicio del archivo (línea 7)
    from .sugeprompt.column_system import ColumnSystem
    
    def activate_prompt_area(self, option_id, option_data):
        """Activa el área de prompt cuando se selecciona una opción"""
        # Agregar la opción seleccionada al área de prompt
        if isinstance(option_data, dict) and 'prompt' in option_data:
            self.add_suggestion_to_prompt(option_data['prompt'])
        else:
            self.add_suggestion_to_prompt(option_id.replace('_', ' '))

    def activate_column_system(self, option_id, option_data):
        """Activa el sistema de columnas cuando se selecciona una opción"""
        print(f"DEBUG: activate_column_system llamado con option_id={option_id}")
        
        # Verificar si es school_uniform y cargar datos específicos
        if option_id == 'school_uniform':
            # Cargar datos específicos del archivo JSON
            import os
            import json
            option_file_path = os.path.join('data', 'sugeprompt', 'categories', 'vestuario_general', f"{option_id}.json")
            
            if os.path.exists(option_file_path):
                try:
                    with open(option_file_path, 'r', encoding='utf-8') as file:
                        specific_data = json.load(file)
                        
                    # Combinar datos específicos con los datos generales
                    if isinstance(option_data, dict) and isinstance(specific_data, dict):
                        for key, value in specific_data.items():
                            if key not in option_data:
                                option_data[key] = value
                except Exception as e:
                    print(f"Error al cargar datos específicos: {e}")
        
        # Pasar los datos al sistema de columnas
        self.column_system.load_option(option_id, option_data)
        
        # También podemos agregar la sugerencia al prompt
        self.add_suggestion_to_prompt(option_id, option_data)