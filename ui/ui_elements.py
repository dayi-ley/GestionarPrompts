# UI Elements para PyQt6
# Este archivo contiene widgets personalizados para PyQt6

from PyQt6.QtWidgets import QLabel, QPushButton, QFrame, QLineEdit, QComboBox, QTextEdit, QApplication
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPalette, QColor, QKeySequence, QPixmap, QImage

class CustomLabel(QLabel):
    """Label personalizado con estilos consistentes"""
    def __init__(self, text="", parent=None, **kwargs):
        super().__init__(text, parent)
        self.setup_styles()
        
    def setup_styles(self):
        self.setStyleSheet("""
            QLabel {
                color: #e0e0e0;
                font-family: 'Segoe UI';
            }
        """)

class CustomButton(QPushButton):
    """Botón personalizado con estilos consistentes"""
    def __init__(self, text="", parent=None, **kwargs):
        super().__init__(text, parent)
        self.setup_styles()
        
    def setup_styles(self):
        self.setStyleSheet("""
            QPushButton {
                background-color: #6366f1;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 11px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #4f46e5;
            }
            QPushButton:pressed {
                background-color: #3730a3;
            }
        """)

class CustomFrame(QFrame):
    """Frame personalizado con estilos consistentes"""
    def __init__(self, parent=None, **kwargs):
        super().__init__(parent)
        self.setup_styles()
        
    def setup_styles(self):
        self.setStyleSheet("""
            QFrame {
                background-color: #252525;
                border: 1px solid #404040;
                border-radius: 8px;
            }
        """)

class PasteImageWidget(QLabel):
    """Widget para pegar y mostrar imágenes (Ctrl+V)"""
    
    image_pasted = pyqtSignal(bool)  # Señal: True si hay imagen, False si no
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFixedSize(120, 120)  # Tamaño cuadrado fijo
        self.setStyleSheet("""
            QLabel {
                background-color: #333;
                border: 2px dashed #555;
                border-radius: 8px;
                color: #888;
                font-size: 11px;
            }
            QLabel:hover {
                border-color: #666;
                background-color: #3a3a3a;
            }
        """)
        self.setText("Pegar imagen\n(Ctrl+V)")
        self.current_image = None  # Almacena la QImage actual
        
        # Habilitar foco para capturar teclado
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def keyPressEvent(self, event):
        """Captura Ctrl+V para pegar imagen"""
        if event.matches(QKeySequence.StandardKey.Paste):
            self.paste_image()
        else:
            super().keyPressEvent(event)
            
    def mousePressEvent(self, event):
        """Al hacer clic, intentamos pegar también si es botón izquierdo"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.setFocus()
            # Opcional: intentar pegar al hacer clic
            # self.paste_image()
        super().mousePressEvent(event)

    def paste_image(self):
        """Intenta pegar una imagen desde el portapapeles"""
        clipboard = QApplication.clipboard()
        mime_data = clipboard.mimeData()

        if mime_data.hasImage():
            image = clipboard.image()
            if not image.isNull():
                self.set_image(image)
        else:
            # Feedback visual de error (opcional)
            print("No hay imagen en el portapapeles")

    def set_image(self, image):
        """Establece la imagen en el widget"""
        self.current_image = image
        
        # Escalar imagen para mostrar
        pixmap = QPixmap.fromImage(image)
        scaled_pixmap = pixmap.scaled(
            self.size(), 
            Qt.AspectRatioMode.KeepAspectRatio, 
            Qt.TransformationMode.SmoothTransformation
        )
        
        self.setPixmap(scaled_pixmap)
        self.setStyleSheet("""
            QLabel {
                background-color: #222;
                border: 2px solid #4CAF50;
                border-radius: 8px;
            }
        """)
        self.image_pasted.emit(True)

    def get_image(self):
        """Retorna la imagen actual"""
        return self.current_image
