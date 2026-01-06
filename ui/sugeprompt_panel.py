from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QStackedWidget, QApplication
from PyQt6.QtCore import Qt, QTimer
import logging

class SugePromptPanel(QWidget):
    """
    Panel contenedor para 'Capturar Prompt'.
    Carga diferida del módulo de embeddings para optimizar el arranque.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.embeddings_widget = None
        self.setup_ui()
        
    def setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # Stack para alternar entre botón de inicio y la app cargada
        self.stack = QStackedWidget()
        self.layout.addWidget(self.stack)
        
        # Pagina 1: Botón de arranque
        self.start_page = QWidget()
        start_layout = QVBoxLayout(self.start_page)
        start_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.btn_capture = QPushButton("Capturar Prompt")
        self.btn_capture.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_capture.setFixedSize(200, 60)
        self.btn_capture.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
                color: white;
                font-size: 16px;
                font-weight: bold;
                border-radius: 30px;
                border: 2px solid #27ae60;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
            QPushButton:pressed {
                background-color: #219150;
                padding-top: 2px;
                padding-left: 2px;
            }
        """)
        self.btn_capture.clicked.connect(self.load_embeddings_app)
        
        start_layout.addWidget(self.btn_capture)
        
        # Añadir página de inicio al stack
        self.stack.addWidget(self.start_page)
        
    def load_embeddings_app(self):
        """Carga el módulo pesado solo cuando se solicita"""
        if self.embeddings_widget is not None:
            self.stack.setCurrentWidget(self.embeddings_widget)
            return
            
        # UI Feedback inmediato
        self.btn_capture.setText("Cargando motor IA...")
        self.btn_capture.setEnabled(False)
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        
        # Inactivar la ventana principal para evitar clicks
        if self.window():
            self.window().setEnabled(False)

        # Dar tiempo al event loop para pintar los cambios (100ms)
        QTimer.singleShot(100, self._perform_load)

    def _perform_load(self):
        try:
            # Importación diferida
            from ui.embeddings.main_widget import EmbeddingsMainWidget
            
            self.embeddings_widget = EmbeddingsMainWidget(self)
            self.stack.addWidget(self.embeddings_widget)
            self.stack.setCurrentWidget(self.embeddings_widget)
            
        except Exception as e:
            logging.error(f"Error cargando embeddings: {e}")
            self.btn_capture.setText("Error al cargar")
            self.btn_capture.setEnabled(True) # Re-enable if failed
            
            error_label = QLabel(f"Error: {str(e)}")
            error_label.setStyleSheet("color: red;")
            self.start_page.layout().addWidget(error_label)
        finally:
            # Restaurar estado UI
            QApplication.restoreOverrideCursor()
            if self.window():
                self.window().setEnabled(True)
