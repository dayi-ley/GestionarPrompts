from PyQt6.QtWidgets import QFrame, QVBoxLayout, QPushButton, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

class AddCategoryCard(QFrame):
    def __init__(self, on_click_callback):
        super().__init__()
        self.on_click_callback = on_click_callback
        self.setup_ui()
        self.setup_styles()

    def setup_ui(self):
        self.setMinimumSize(300, 100)
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)
        
        add_icon = QLabel("+")
        add_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        add_icon.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        layout.addWidget(add_icon)
        
        label = QLabel("Añadir categoría")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setFont(QFont("Segoe UI", 12))
        layout.addWidget(label)
        
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.on_click_callback()
        super().mousePressEvent(event)

    def setup_styles(self):
        self.setStyleSheet("""
            QFrame {
                background-color: #6366f1;
                border: 1px solid #4f46e5;
                border-radius: 8px;
            }
            QFrame:hover {
                background-color: #4f46e5;
                border-color: #3730a3;
            }
            QLabel {
                color: #ffffff;
                background-color: transparent;
                border: none;
            }
        """)
