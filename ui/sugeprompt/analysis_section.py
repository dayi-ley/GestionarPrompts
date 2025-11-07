from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
    QPushButton, QScrollArea, QTreeWidget, QTreeWidgetItem
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor
import os
import json
from logic.suggestion_engine import SuggestionEngine

class AnalysisSection(QWidget):
    # Señales para comunicar selecciones y eventos
    suggestion_applied = pyqtSignal(str, str)  # categoría, selección
    combination_requested = pyqtSignal(dict)  # combinación completa
    prompt_updated = pyqtSignal(str)  # texto del prompt actualizado
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Inicializar motor de sugerencias
        self.suggestion_engine = SuggestionEngine(self)
        
        # Variables para el estado de las columnas
        self.columns = []  # Lista de columnas activas
        self.column_data = {}  # Datos de cada columna
        self.column_states = {}  # Estado de cada columna (selección actual)
        self.category_stack = []  # Pila de categorías visitadas
        self.current_category = None  # Categoría actual
        self.saved_prompts = {}  # Prompts guardados por categoría
        
        # Variables para vestuario
        self.garment_selections = {}  # Selecciones de prendas
        self.current_garment_id = None  # ID de la prenda actual
        
        # Conectar señales del motor de sugerencias
        self.suggestion_engine.suggestions_updated.connect(self.update_suggestions)
        self.suggestion_engine.error_occurred.connect(self.show_error)
        
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(8)
        
        # Título pequeño
        title = QLabel("Vestuario General")
        title.setStyleSheet("""
            QLabel {
                font-size: 12px;
                font-weight: bold;
                color: #e0e0e0;
                margin-bottom: 5px;
            }
        """)
        layout.addWidget(title)
        
        # Solo la sección de sugerencias ocupando todo el espacio
        suggestions_frame = self.create_suggestions_section()
        layout.addWidget(suggestions_frame)
    
    def create_suggestions_section(self):
        """Crea la sección para Vestuario General con columnas dinámicas"""
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: #383838;
                border: 1px solid #555;
                border-radius: 6px;
            }
        """)
        
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)
        
        # Subtítulo con botones de navegación
        header_layout = QHBoxLayout()
        
        # Botón Atrás
        self.back_button = QPushButton("← Atrás")
        self.back_button.setStyleSheet("""
            QPushButton {
                background-color: #2b2b2b;
                color: #e0e0e0;
                border: 1px solid #444;
                border-radius: 3px;
                padding: 3px 8px;
                font-size: 10px;
                max-width: 60px;
            }
            QPushButton:hover {
                background-color: #3a3a3a;
            }
            QPushButton:pressed {
                background-color: #444;
            }
            QPushButton:disabled {
                background-color: #222;
                color: #555;
            }
        """)
        self.back_button.clicked.connect(self.navigate_back)
        self.back_button.setEnabled(False)  # Inicialmente deshabilitado
        header_layout.addWidget(self.back_button)
        
        # Título central
        self.category_title = QLabel("Vestuario General")
        self.category_title.setStyleSheet("""
            QLabel {
                font-size: 11px;
                font-weight: bold;
                color: #e0e0e0;
                margin-bottom: 3px;
            }
        """)
        self.category_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(self.category_title, 1)  # 1 = stretch factor
        
        # Botón Saltar
        self.skip_button = QPushButton("Saltar →")
        self.skip_button.setStyleSheet("""
            QPushButton {
                background-color: #2b2b2b;
                color: #e0e0e0;
                border: 1px solid #444;
                border-radius: 3px;
                padding: 3px 8px;
                font-size: 10px;
                max-width: 60px;
            }
            QPushButton:hover {
                background-color: #3a3a3a;
            }
            QPushButton:pressed {
                background-color: #444;
            }
        """)
        self.skip_button.clicked.connect(self.skip_current_category)
        header_layout.addWidget(self.skip_button)
        
        layout.addLayout(header_layout)
        
        # Área de scroll para las columnas de sugerencias
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background-color: #2b2b2b;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #555;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #666;
            }
        """)
        
        # Contenedor para las columnas dinámicas
        self.columns_container = QWidget()
        self.columns_layout = QHBoxLayout(self.columns_container)
        self.columns_layout.setContentsMargins(0, 0, 0, 0)
        self.columns_layout.setSpacing(8)
        
        self.scroll_area.setWidget(self.columns_container)
        layout.addWidget(self.scroll_area)
        
        # Iniciar con la primera categoría
        self.load_initial_category()
        
        return frame
    
    def create_suggestion_column(self, category_id, options):
        """Crea una columna de sugerencias con árbol de opciones"""
        column_frame = QFrame()
        column_frame.setStyleSheet("""
            QFrame {
                background-color: #2b2b2b;
                border: 1px solid #444;
                border-radius: 4px;
                padding: 4px;
                min-width: 150px;
                max-width: 200px;
            }
        """)
        
        column_layout = QVBoxLayout(column_frame)
        column_layout.setContentsMargins(6, 6, 6, 6)
        column_layout.setSpacing(3)
        
        # Título de la columna (traducido)
        title = self.suggestion_engine.get_translation(category_id)
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 10px;
                font-weight: bold;
                color: #3498db;
                margin-bottom: 2px;
                text-align: center;
            }
        """)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        column_layout.addWidget(title_label)
        
        # Crear árbol de sugerencias
        tree_widget = QTreeWidget()
        tree_widget.setHeaderHidden(True)
        tree_widget.setStyleSheet("""
            QTreeWidget {
                background-color: #2b2b2b;
                border: none;
                color: #e0e0e0;
                font-size: 10px;
            }
            QTreeWidget::item {
                padding: 3px;
                margin: 1px 0px;
            }
            QTreeWidget::item:selected {
                background-color: #3498db;
            }
            QTreeWidget::item:hover {
                background-color: #404040;
            }
        """)
        
        # Añadir opciones al árbol
        for option_id, option_data in options.items():
            # Obtener etiqueta traducida
            option_key = f"{category_id}.{option_id}"
            label = self.suggestion_engine.get_translation(option_key)
            
            # Crear item para la opción
            item = QTreeWidgetItem([label])
            item.setData(0, Qt.ItemDataRole.UserRole, {
                'category_id': category_id,
                'option_id': option_id,
                'data': option_data
            })
            
            # Si es un color, aplicar color de fondo
            if 'hex' in option_data:
                hex_color = option_data['hex']
                bg_color = QColor(hex_color)
                item.setBackground(0, bg_color)
                
                # Determinar si el texto debe ser blanco o negro según el color de fondo
                luminance = (0.299 * bg_color.red() + 0.587 * bg_color.green() + 0.114 * bg_color.blue()) / 255
                if luminance < 0.5:
                    item.setForeground(0, QColor("#FFFFFF"))
                else:
                    item.setForeground(0, QColor("#000000"))
            
            tree_widget.addTopLevelItem(item)
        
        # Conectar señal de doble clic
        tree_widget.itemDoubleClicked.connect(self.on_suggestion_selected)
        
        column_layout.addWidget(tree_widget)
        
        # Guardar referencia al árbol y datos de la columna
        column_data = {
            'frame': column_frame,
            'tree': tree_widget,
            'category_id': category_id,
            'options': options
        }
        
        # Añadir a la lista de columnas
        self.columns.append(column_data)
        
        return column_frame
    
    def load_initial_category(self):
        """Carga la categoría inicial de sugerencias"""
        # Limpiar columnas existentes
        self.clear_columns()
        
        # Usar directamente vestuario_general como categoría inicial
        # Establecer la categoría actual
        self.current_category = "vestuario_general"
        self.category_stack = []  # Inicializar pila vacía
        
        # Actualizar título
        category_label = self.suggestion_engine.get_translation(self.current_category)
        self.category_title.setText(category_label)
        
        # Cargar opciones para esta categoría
        self.load_category_options(self.current_category)
    
    def load_category_options(self, category_id):
        """Carga las opciones para una categoría específica"""
        # Obtener sugerencias para esta categoría
        category_data = self.suggestion_engine.get_suggestions_for_category(category_id)
        
        if category_data and 'options' in category_data:
            # Crear columna para esta categoría
            column = self.create_suggestion_column(category_id, category_data['options'])
            self.columns_layout.addWidget(column)
        else:
            self.show_error(f"No se encontraron opciones para la categoría: {category_id}")
    
    def on_suggestion_selected(self, item, column):
        """Maneja la selección de una sugerencia"""
        # Obtener datos del item
        item_data = item.data(0, Qt.ItemDataRole.UserRole)
        if not item_data:
            return
        
        category_id = item_data['category_id']
        option_id = item_data['option_id']
        option_data = item_data['data']
        
        # Actualizar estado de la columna
        self.column_states[category_id] = option_id
        
        # Actualizar contexto en el motor de sugerencias
        self.suggestion_engine.update_context(category_id, option_id)
        
        # Emitir señal de sugerencia aplicada
        self.suggestion_applied.emit(category_id, option_id)
        
        # Verificar si hay categorías siguientes
        if 'next_categories' in option_data:
            # Guardar categoría actual en la pila
            self.category_stack.append(self.current_category)
            
            # Limpiar columnas después de la actual
            current_index = self.get_column_index(category_id)
            if current_index >= 0:
                self.clear_columns_after(current_index)
            
            # Cargar siguiente categoría
            next_category = option_data['next_categories'][0]  # Tomar la primera
            self.current_category = next_category
            
            # Actualizar título
            category_label = self.suggestion_engine.get_translation(next_category)
            self.category_title.setText(category_label)
            
            # Cargar opciones para la siguiente categoría
            self.load_category_options(next_category)
            
            # Habilitar botón de retroceso
            self.back_button.setEnabled(True)
    
    def navigate_back(self):
        """Navega a la categoría anterior"""
        if self.category_stack:
            # Obtener categoría anterior
            previous_category = self.category_stack.pop()
            
            # Limpiar todas las columnas
            self.clear_columns()
            
            # Actualizar categoría actual
            self.current_category = previous_category
            
            # Actualizar título
            category_label = self.suggestion_engine.get_translation(previous_category)
            self.category_title.setText(category_label)
            
            # Cargar opciones para la categoría anterior
            self.load_category_options(previous_category)
            
            # Deshabilitar botón de retroceso si no hay más categorías en la pila
            if not self.category_stack:
                self.back_button.setEnabled(False)
    
    def skip_current_category(self):
        """Salta la categoría actual y pasa a la siguiente"""
        # Implementar lógica para saltar categoría
        # Por ahora, simplemente avanzamos a la siguiente si hay alguna definida
        if self.current_category == 'vestuario_general':
            self.category_stack.append(self.current_category)
            self.current_category = 'vestuario_superior'
            
            # Limpiar columnas
            self.clear_columns()
            
            # Actualizar título
            category_label = self.suggestion_engine.get_translation(self.current_category)
            self.category_title.setText(category_label)
            
            # Cargar opciones para la nueva categoría
            self.load_category_options(self.current_category)
            
            # Habilitar botón de retroceso
            self.back_button.setEnabled(True)
    
    def clear_columns(self):
        """Elimina todas las columnas de sugerencias"""
        # Eliminar widgets de columnas
        for column_data in self.columns:
            self.columns_layout.removeWidget(column_data['frame'])
            column_data['frame'].deleteLater()
        
        # Limpiar lista de columnas
        self.columns = []
    
    def clear_columns_after(self, index):
        """Elimina todas las columnas después del índice especificado"""
        if index < len(self.columns) - 1:
            # Eliminar columnas después del índice
            for i in range(len(self.columns) - 1, index, -1):
                column_data = self.columns[i]
                self.columns_layout.removeWidget(column_data['frame'])
                column_data['frame'].deleteLater()
                self.columns.pop(i)
    
    def get_column_index(self, category_id):
        """Obtiene el índice de una columna por su ID de categoría"""
        for i, column_data in enumerate(self.columns):
            if column_data['category_id'] == category_id:
                return i
        return -1
    
    def show_error(self, message):
        """Muestra un mensaje de error"""
        print(f"Error: {message}")  # Por ahora solo imprimimos, luego podemos mostrar en UI
    
    def update_suggestions(self, suggestions):
        """Actualiza las sugerencias mostradas"""
        # Esta función se llamará cuando el motor de sugerencias emita la señal suggestions_updated
        pass
    
    def add_suggestion_to_prompt(self, suggestion):
        """Agrega una sugerencia al área de texto del prompt"""
        # Emitir señal para que el panel de prompt actualice su texto
        self.prompt_updated.emit(suggestion)