from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QLineEdit, QMessageBox, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap, QImage, QKeySequence, QShortcut
import os
import json
import re
from datetime import datetime
from PIL import Image
from io import BytesIO
from ui.ui_elements import PasteImageWidget

class NewCharacterDialog(QDialog):
    """Diálogo para crear un nuevo personaje"""
    
    character_saved = pyqtSignal(str)
    
    def __init__(self, parent=None, category_grid=None):
        super().__init__(parent)
        self.setWindowTitle("Nuevo Personaje")
        self.setModal(True)
        self.setFixedSize(500, 220)
        self.character_name = None
        self.category_grid = category_grid 
        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
            }
        """)
        self.setup_ui()
    
    def setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(25, 25, 25, 25)
        image_layout = QVBoxLayout()
        self.image_widget = PasteImageWidget()
        self.image_widget.image_pasted.connect(self.check_validity)
        image_layout.addWidget(self.image_widget)
        image_layout.addStretch()
        main_layout.addLayout(image_layout)
        form_layout = QVBoxLayout()
        form_layout.setSpacing(15)
        title_label = QLabel("Crear Nuevo Personaje")
        title_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title_label.setStyleSheet("color: white;")
        form_layout.addWidget(title_label)
        instruction_label = QLabel("Ingresa un nombre:")
        instruction_label.setFont(QFont("Segoe UI", 11))
        instruction_label.setStyleSheet("color: #ccc;")
        form_layout.addWidget(instruction_label)
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Nombre del personaje")
        self.name_input.setFont(QFont("Segoe UI", 11))
        self.name_input.setStyleSheet("""
            QLineEdit {
                padding: 5px;
                border: 2px solid #555;
                border-radius: 6px;
                font-size: 11px;
                background-color: #404040;
                color: white;
            }
            QLineEdit:focus {
                border-color: #4CAF50;
                outline: none;
            }
            QLineEdit::placeholder {
                color: #aaa;
            }
        """)
        self.name_input.textChanged.connect(self.check_validity)
        self.name_input.returnPressed.connect(self.save_character)
        form_layout.addWidget(self.name_input)
        form_layout.addStretch()
        buttons_layout = QHBoxLayout()
        self.save_btn = QPushButton("Guardar Personaje")
        self.save_btn.setFixedSize(140, 35)
        self.save_btn.setEnabled(False)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 11px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
            QPushButton:disabled {
                background-color: #444;
                color: #888;
                border: 1px solid #555;
            }
        """)
        self.save_btn.clicked.connect(self.save_character)
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.save_btn)
        form_layout.addLayout(buttons_layout)
        main_layout.addLayout(form_layout)
        self.name_input.setFocus()

    def check_validity(self):
        """Habilita el botón guardar solo si hay nombre e imagen"""
        name = self.name_input.text().strip()
        has_image = self.image_widget.get_image() is not None
        
        self.save_btn.setEnabled(bool(name and has_image))

    def save_character(self):
        """Valida y guarda el nuevo personaje"""
        if not self.save_btn.isEnabled():
            return
        name = self.name_input.text().strip()

        if not name:
            QMessageBox.warning(self, "Error", "Por favor ingresa un nombre para el personaje.")
            self.name_input.setFocus()
            return
        
        if not re.match(r'^[a-zA-Z0-9\s_-]+$', name):
            QMessageBox.warning(self, "Error", "El nombre solo puede contener letras, números, espacios, guiones y guiones bajos.")
            self.name_input.setFocus()
            return
        
        if self.character_exists(name):
            QMessageBox.warning(self, "Error", f"Ya existe un personaje con el nombre '{name}'.\nPor favor elige otro nombre.")
            self.name_input.setFocus()
            return
        

        try:
            image = self.image_widget.get_image()
            self.save_character_data(name, image)
            self.character_name = name
            self.character_saved.emit(name)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al guardar el personaje: {str(e)}")
    
    def save_character_data(self, name, image=None):
        """Guarda los datos del personaje en el archivo JSON e imagen"""
        # Crear directorio de personajes si no existe
        characters_dir = os.path.join("data", "characters")
        os.makedirs(characters_dir, exist_ok=True)
        
        # Normalizar nombre para el archivo
        normalized_name = name.lower().replace(" ", "_")
        character_folder = os.path.join(characters_dir, normalized_name)
        
        # Crear carpeta del personaje
        os.makedirs(character_folder, exist_ok=True)

        if image:
            image_path = os.path.join(character_folder, "image.png")
            image.save(image_path, "PNG")
        
 
        if self.category_grid:
            current_values = self.category_grid.get_current_values()
            category_data = {}
            for display_name, value in current_values.items():
                snake_case_name = display_name.lower().replace(" ", "_")
                category_data[snake_case_name] = value
        else:
            category_data = {}
        character_data = {
            "metadata": {
                "character_name": name,
                "display_name": name,
                "created_date": datetime.now().isoformat(),
                "last_modified": datetime.now().isoformat(),
                "version": "1.0",
                "type": "character",
                "description": f"Personaje {name} creado desde la aplicación"
            },
            "categories": category_data
        }
        
        json_file_path = os.path.join(character_folder, f"{normalized_name}.json")
        
        with open(json_file_path, 'w', encoding='utf-8') as f:
            json.dump(character_data, f, ensure_ascii=False, indent=2)
        
        print(f"Personaje guardado en: {json_file_path}")
    
    def character_exists(self, name):
        """Verifica si ya existe un personaje con ese nombre"""
        characters_dir = os.path.join("data", "characters")
        if not os.path.exists(characters_dir):
            return False
        normalized_name = name.lower().replace(" ", "_")
        character_folder = os.path.join(characters_dir, normalized_name)
        
        return os.path.exists(character_folder)
    
    def get_character_name(self):
        """Retorna el nombre del personaje ingresado"""
        return self.character_name