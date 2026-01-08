import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QSplitter
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QPalette, QColor, QFont
from ui.sidebar import SidebarFrame
from ui.category_grid import CategoryGridFrame
from ui.prompt_section import PromptSectionFrame
from logic.prompt_generator import PromptGenerator

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Inicializar el generador de prompts
        self.prompt_generator = PromptGenerator()
        
        # Configurar la ventana
        self.setWindowTitle("Prompt Organizer")
        
        # Crear la interfaz de usuario
        self.setup_ui()
        
        # Conectar señales
        self.connect_signals()
        
        # Configurar tema y tamaño
        self.set_dark_theme()
        self.setup_responsive_size()
        self.center_window()
    
    def setup_ui(self):
        """Configura la interfaz de usuario"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(8)
        
        self.sidebar = SidebarFrame(self.prompt_generator, self) 
        main_layout.addWidget(self.sidebar)
        # Contenedor principal para categorías y prompt
        main_container = QWidget()
        main_layout.addWidget(main_container, 1) 
        
        # Layout vertical para el contenedor principal
        container_layout = QVBoxLayout(main_container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(8)
        
        # Sección de categorías
        self.category_grid = CategoryGridFrame(self.prompt_generator, self)
        container_layout.addWidget(self.category_grid, 1) 
        
        # Sección de prompt
        self.prompt_section = PromptSectionFrame(self.prompt_generator)
        container_layout.addWidget(self.prompt_section, 0)

    def setup_responsive_size(self):
        """Configura el tamaño de la ventana de manera responsiva"""
        
        screen = self.screen()
        screen_geometry = screen.geometry()

        optimal_width = int(screen_geometry.width() * 0.8)
        optimal_height = int(screen_geometry.height() * 0.80)
        
        min_width = 1300
        min_height = 600

        window_width = max(min_width, optimal_width)
        window_height = max(min_height, optimal_height)

        self.setMinimumSize(min_width, min_height)
        self.resize(window_width, window_height)

    def center_window(self):
        """Posiciona la ventana en una posición fija"""

        x = 40 
        y = 40   
        
        self.move(x, y)

    def set_dark_theme(self):
        """Configura el tema oscuro"""
        palette = QPalette()

        dark_bg = QColor("#1a1a1a")
        dark_secondary = QColor("#252525")
        dark_border = QColor("#404040")
        accent = QColor("#6366f1")
        text_primary = QColor("#e0e0e0")
        text_secondary = QColor("#a0a0a0")

        palette.setColor(QPalette.ColorRole.Window, dark_bg)
        palette.setColor(QPalette.ColorRole.WindowText, text_primary)
        palette.setColor(QPalette.ColorRole.Base, dark_secondary)
        palette.setColor(QPalette.ColorRole.AlternateBase, dark_border)
        palette.setColor(QPalette.ColorRole.ToolTipBase, dark_secondary)
        palette.setColor(QPalette.ColorRole.ToolTipText, text_primary)
        palette.setColor(QPalette.ColorRole.Text, text_primary)
        palette.setColor(QPalette.ColorRole.Button, dark_secondary)
        palette.setColor(QPalette.ColorRole.ButtonText, text_primary)
        palette.setColor(QPalette.ColorRole.BrightText, accent)
        palette.setColor(QPalette.ColorRole.Link, accent)
        palette.setColor(QPalette.ColorRole.Highlight, accent)
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
        
        self.setPalette(palette)

        font = QFont("Segoe UI", 9)
        self.setFont(font)

    def connect_signals(self):
        """Conecta las señales entre componentes"""
        self.category_grid.prompt_updated.connect(self.prompt_section.update_prompt)

        self.sidebar.character_defaults_selected.connect(self.category_grid.apply_character_defaults)
        self.sidebar.variation_applied.connect(self.apply_variation)
 
        self.category_grid.category_value_changed.connect(self.sidebar.track_category_change)

        self.category_grid.character_saved.connect(self.sidebar.add_character_to_dropdown)

        self.sidebar.presets_panel.preset_loaded.connect(self.apply_preset)

    def apply_preset(self, preset_data):
        """Aplica un preset a las categorías"""
        if 'categories' in preset_data:
            self.category_grid.apply_preset(preset_data['categories'])
    
    def apply_variation(self, variation_data):
        """Aplica una variación a las tarjetas de categoría"""
        self.category_grid.apply_variation(variation_data)
    
    def run(self):
        """Muestra la ventana"""
        self.show()
