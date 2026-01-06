from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, QSplitter, QLabel, QMessageBox, QApplication, QScrollArea, QGroupBox, QPlainTextEdit, QSizePolicy, QGridLayout, QSpacerItem, QToolButton, QToolTip, QStyle
from PyQt6.QtCore import Qt, QThread, QObject, pyqtSignal, QTimer, QPoint
from PyQt6.QtGui import QTextOption
import re
import logging
import time
import traceback
from .embeddings import EmbeddingsEngine
from .bridge import send_update, receiver_ready

class EmbeddingWorker(QObject):
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    def __init__(self, engine, items, threshold):
        super().__init__()
        self.engine = engine
        self.items = items
        self.threshold = threshold
    def run(self):
        try:
            mapping = self.engine.categorize(self.items, threshold=self.threshold)
            self.finished.emit(mapping)
        except Exception as e:
            self.error.emit(str(e))

class TranslateWorker(QObject):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    def __init__(self, text):
        super().__init__()
        self.text = text
    def run(self):
        s = (self.text or "").strip()
        if not s:
            self.error.emit("texto vacío")
            return
        if len(s) > 1200:
            s = s[:1200]
        try:
            import argostranslate.translate as at_translate
        except Exception as e:
            self.error.emit("instala argostranslate y el paquete en→es")
            return
        try:
            langs = at_translate.get_installed_languages()
            src = next((l for l in langs if l.code.startswith("en")), None)
            tgt = next((l for l in langs if l.code.startswith("es")), None)
            if not src or not tgt:
                self.error.emit("paquete de idioma en→es no instalado")
                return
            tr = src.get_translation(tgt)
            out = tr.translate(s)
            self.finished.emit(out)
        except Exception as e:
            self.error.emit(str(e))

class ResultsWindow(QWidget):
    """Ventana flotante para mostrar resultados"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Resultados de Clasificación")
        self.resize(800, 450)
        self.setup_ui()
        self._groups = {
            "Todos": {"names": [], "color": "#444"},
            "Poses": {"names": ["angulo", "postura_cabeza", "direccion_mirada_personaje", "pose_global", "pose_brazos", "pose_piernas", "orientacion_personaje", "objetos_interaccion", "mirada_espectador"], "color": "#38A169"},
            "Vestuario": {"names": ["vestuario_general", "vestuario_superior", "vestuario_inferior", "vestuario_accesorios", "vestuariospies", "ropa_interior_superior", "ropa_interior_inferior", "ropa_interior_accesorios", "cabello_accesorios", "rostro_accesorios"], "color": "#553C9A"},
            "Rasgos Físicos": {"names": ["tipo_de_cuerpo", "rasgo_fisico_cuerpo", "rasgo_fisico_piernas", "cabello_forma", "cabello_color", "ojos"], "color": "#B77B00"},
            "Expresiones": {"names": ["actitud_emocion", "expresion_facial_ojos", "expresion_facial_mejillas", "expresion_facial_boca"], "color": "#FD547E"},
            "Otros": {"names": [
                "calidad_tecnica", "estilo_artistico", "composicion", "atmosfera_vibe", 
                "loras", "fondo", "personaje", "objetos_escenario", "nsfw"
            ], "color": "#444"}
        }
        self._group_filter = None
        self._last_mapping = None

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Barra superior con estado
        self.status_label = QLabel("Categorías")
        layout.addWidget(self.status_label)
        
        # Barra de filtros
        self._filter_bar = QWidget()
        self._filter_bar_layout = QHBoxLayout()
        self._filter_bar_layout.setContentsMargins(6, 6, 6, 6)
        self._filter_bar_layout.setSpacing(6)
        self._filter_bar.setLayout(self._filter_bar_layout)
        layout.addWidget(self._filter_bar)
        
        # Area de scroll para resultados
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.sections = QWidget()
        self.sections_layout = QGridLayout()
        self.sections_layout.setHorizontalSpacing(8)
        self.sections_layout.setVerticalSpacing(10)
        self.sections_layout.setContentsMargins(8, 8, 8, 8)
        self.sections.setLayout(self.sections_layout)
        self.scroll.setWidget(self.sections)
        layout.addWidget(self.scroll)

    def render_categories(self, mapping, engine_ref):
        self.engine_ref = engine_ref # Referencia para callbacks si es necesario
        self._create_filter_buttons()
        self._render_grid(mapping)

    def _create_filter_buttons(self):
        # Limpiar botones anteriores
        while self._filter_bar_layout.count():
            item = self._filter_bar_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        self._group_buttons = {}
        for gname, info in self._groups.items():
            btn = QToolButton()
            btn.setText(gname)
            btn.setAutoRaise(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setCheckable(True)
            btn.setChecked(False)
            btn.setStyleSheet(f"QToolButton{{background:{info['color']};color:white;border-radius:10px;padding:4px 8px;}} QToolButton:checked{{background:{info['color']};opacity:0.95}}")
            btn.clicked.connect(lambda _, n=gname: self._on_group_clicked(n))
            self._filter_bar_layout.addWidget(btn)
            self._group_buttons[gname] = btn
        
        if "Todos" in self._group_buttons:
            self._group_buttons["Todos"].setChecked(True)
            self._group_filter = "Todos"

    def _on_group_clicked(self, name):
        for n, b in self._group_buttons.items():
            b.setChecked(n == name)
        self._group_filter = name
        if self._last_mapping:
            self._render_grid(self._last_mapping)

    def _render_grid(self, mapping):
        self._last_mapping = mapping
        # Limpiar grid
        while self.sections_layout.count():
            item = self.sections_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        cols = 2
        i = 0
        
        def _canon(name):
            n = name.strip().rstrip(":")
            if n == "pose_actitud_global": return "pose_global"
            return n

        # Identificar qué categorías pertenecen a qué grupo visible
        # Si el filtro es "Todos", mostramos todo.
        # Si hay filtro específico, solo mostramos categorías de ese grupo.
        
        target_group = self._group_filter if self._group_filter in self._groups else "Todos"
        
        # Recopilar todas las categorías que deben mostrarse
        cats_to_show = []
        
        # Mapeo de categoría -> Grupo al que pertenece (para asignar color si es "Todos")
        cat_group_map = {}
        
        # Construir mapa basado en la definición actual de grupos
        for gname, info in self._groups.items():
            if gname == "Todos": continue
            for cname in info["names"]:
                c_canon = _canon(cname)
                cat_group_map[c_canon] = gname
        
        for cat, items in mapping.items():
            if not items: continue
            c_canon = _canon(cat)
            
            # Determinar a qué grupo pertenece realmente esta categoría
            actual_group = cat_group_map.get(c_canon, "Otros")

            # Filtrado
            if target_group == "Todos" or target_group == actual_group:
                cats_to_show.append((cat, items, actual_group))

        if not cats_to_show:
            self.status_label.setText("Sin coincidencias")
            return

        self.status_label.setText(f"Categorías mostradas: {len(cats_to_show)}")
        
        for cat, items, group_name in cats_to_show:
            # Obtener color del grupo al que pertenece
            color = self._groups[group_name]["color"] if group_name in self._groups else "#888"
            
            # Generar fondos basados en ese color
            bg = self._get_color_alpha(color, 80)
            bg_text = self._get_color_alpha(color, 48)
            
            box = QGroupBox(f"{cat} (n={len(items)})")
            inner = QHBoxLayout()
            
            text = QPlainTextEdit(", ".join(items))
            text.setReadOnly(True)
            text.setWordWrapMode(QTextOption.WrapMode.WrapAtWordBoundaryOrAnywhere)
            text.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            text.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            text.setFixedHeight(36)
            text.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            text.setStyleSheet(f"QPlainTextEdit{{background:{bg_text};color:#ffffff;border:1px solid {color};border-radius:4px;font-size:10px;padding:4px;}}")
            
            btn_copy = QToolButton()
            btn_copy.setText("⧉")
            btn_copy.setToolTip("Copiar al portapapeles")
            btn_copy.setAutoRaise(True)
            btn_copy.setFixedSize(24, 24)
            btn_copy.setStyleSheet(f"""
                QToolButton {{
                    color: #ddd;
                    border: 1px solid {color};
                    border-radius: 4px;
                    background: rgba(0,0,0,0.2);
                }}
                QToolButton:hover {{
                    background: {color};
                    color: white;
                }}
            """)
            btn_copy.clicked.connect(lambda _, t=text: self._copy_text(t))

            btn_send = QToolButton()
            btn_send.setText("→")
            btn_send.setToolTip("Enviar a tarjeta principal")
            btn_send.setAutoRaise(True)
            btn_send.setFixedSize(24, 24)
            btn_send.setStyleSheet(f"""
                QToolButton {{
                    color: #ddd;
                    border: 1px solid {color};
                    border-radius: 4px;
                    background: rgba(0,0,0,0.2);
                    font-weight: bold;
                }}
                QToolButton:hover {{
                    background: {color};
                    color: white;
                }}
            """)
            btn_send.setProperty("default_style", btn_send.styleSheet())
            # Usamos una referencia débil o pasamos el botón para cambiar su estado
            btn_send.clicked.connect(lambda _, c=cat, i=items, b=btn_send: self._send_category(c, i, b))
            
            inner.setContentsMargins(6, 2, 6, 2)
            inner.setSpacing(4)
            inner.addWidget(text)
            inner.addWidget(btn_copy)
            inner.addWidget(btn_send)
            
            box.setLayout(inner)
            box.setStyleSheet(f"QGroupBox{{margin-top:12px;font-size:12px;color:#ddd;border:1px solid {color};border-radius:6px;background:{bg};}} QGroupBox::title{{subcontrol-origin: margin;left:8px;padding:0 3px;color:#ffffff;}}")
            box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            box.setFixedHeight(72)
            
            r = i // cols
            c = i % cols
            self.sections_layout.addWidget(box, r, c)
            i += 1

        spacer = QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        self.sections_layout.addItem(spacer, (i // cols) + 1, 0, 1, cols)
        self.sections_layout.setRowStretch((i // cols) + 1, 1)

    def _get_color_alpha(self, color_hex, alpha):
        s = color_hex.lstrip('#')
        r, g, b = (int(s[i:i+2], 16) for i in (0, 2, 4)) if len(s) == 6 else (68, 68, 68)
        return f"rgba({r},{g},{b},{alpha})"

    def _copy_text(self, widget):
        widget.selectAll()
        widget.copy()

    def _send_category(self, category, items, btn):
        success = False
        try:
            # Buscar MainWindow en topLevelWidgets
            main_window = None
            for w in QApplication.topLevelWidgets():
                if hasattr(w, 'category_grid') and w.__class__.__name__ == 'MainWindow':
                    main_window = w
                    break
            
            if main_window:
                value = ", ".join(items) if items else ""
                # Asegurar coma final si hay valores
                if value and not value.strip().endswith(','):
                    value += ","

                # set_category_value retorna True si éxito, False si falló (bloqueado/no encontrado)
                success = main_window.category_grid.set_category_value(category, value)
            else:
                # Fallback a bridge si no encontramos la ventana
                success = send_update(category, items)
        except Exception as e:
            logging.error(f"Error enviando categoría: {e}")
            success = False

        if success:
            # Feedback visual de éxito
            btn.setText("✓")
            btn.setStyleSheet(f"""
                QToolButton {{
                    color: #2ecc71;
                    border: 1px solid #2ecc71;
                    border-radius: 4px;
                    background: rgba(46, 204, 113, 0.2);
                    font-weight: bold;
                }}
            """)
            btn.setToolTip("Enviado correctamente")
            # El botón se mantiene en estado de éxito para referencia del usuario
        else:
            # Feedback de error
            btn.setText("✕")
            btn.setStyleSheet(f"""
                QToolButton {{
                    color: #e74c3c;
                    border: 1px solid #e74c3c;
                    border-radius: 4px;
                    background: rgba(231, 76, 60, 0.2);
                    font-weight: bold;
                }}
            """)
            QMessageBox.warning(self, "No se pudo enviar", f"No se pudo actualizar la categoría '{category}'.\n\nPosibles causas:\n- La categoría está bloqueada (candado cerrado).\n- La categoría no existe en el panel principal.")
            QTimer.singleShot(2000, lambda: self._restore_send_btn(btn))
    
    def _restore_send_btn(self, btn):
        try:
            # Verificar si el objeto C++ ha sido eliminado
            if not btn or not hasattr(btn, "setText"):
                return
            btn.setText("→")
            style = btn.property("default_style")
            if style:
                btn.setStyleSheet(style)
            btn.setToolTip("Enviar a tarjeta principal")
        except RuntimeError:
            # Objeto eliminado (C++ deleted), ignorar
            pass
        except Exception:
            pass

class EmbeddingsMainWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.results_window = None
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Panel de entrada (Texto + Botón)
        self.input_text = QTextEdit()
        self.input_text.setPlaceholderText("Ingresa texto, prompt o tags...")
        main_layout.addWidget(self.input_text)
        
        self.process_button = QPushButton("Procesar")
        self.process_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.process_button.setFixedHeight(40)
        self.process_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 rgba(46,204,113,220), stop:1 rgba(39,174,96,180));
                color: white;
                border: 1px solid rgba(46,204,113,230);
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 rgba(76,224,143,230), stop:1 rgba(49,184,106,190));
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 rgba(36,184,93,230), stop:1 rgba(29,154,76,190));
            }
        """)
        main_layout.addWidget(self.process_button)
        
        self.status_label = QLabel("Listo para procesar")
        self.status_label.setStyleSheet("color: #888; font-size: 11px;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.status_label)

        # Inicialización del motor
        self.engine = EmbeddingsEngine()
        self.init_engine()
        
        self.process_button.clicked.connect(self.on_process)
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timer)
        self.elapsed_time = 0

    def update_timer(self):
        self.elapsed_time += 0.1
        self.process_button.setText(f"Procesando... {self.elapsed_time:.1f}s")

    def init_engine(self):
        logging.info("Iniciando carga del motor de embeddings...")
        try:
            self.engine._ensure()
            logging.info("Motor cargado correctamente.")
            self.status_label.setText("Modelo IA cargado correctamente")
            # Warmup
            try:
                logging.info("Realizando warmup...")
                self.engine.embed(["warmup"])
                logging.info("Warmup completado.")
            except Exception as we:
                logging.warning(f"Error en warmup (no crítico): {we}")
        except Exception as e:
            err_msg = str(e)
            tb = traceback.format_exc()
            logging.error(f"Error cargando modelo: {err_msg}\n{tb}")
            
            self.status_label.setText("Error al cargar motor IA")
            self.status_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
            self.process_button.setEnabled(False)
            self.process_button.setText("Error de carga")
            
            # Mostrar error visible al usuario
            QMessageBox.critical(
                self, 
                "Error de Inicialización", 
                f"No se pudo cargar el motor de Inteligencia Artificial.\n\nDetalle: {err_msg}\n\nVerifica que la carpeta 'promptEmbeddings' tenga las librerías necesarias."
            )

    def on_process(self):
        text = self.input_text.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "Aviso", "Ingresa algún texto para procesar.")
            return

        logging.info(f"Iniciando procesamiento de texto. Longitud: {len(text)}")
        self.process_button.setEnabled(False)
        self.process_button.setText("Procesando... 0.0s")
        self.elapsed_time = 0
        self.timer.start(100) # Actualizar cada 100ms
        self.status_label.setText("Analizando semánticamente...")
        
        # Procesamiento en hilo secundario
        items = [x.strip() for x in re.split(r'[,\n]', text) if x.strip()]
        logging.info(f"Items detectados: {len(items)}")
        
        self.worker = EmbeddingWorker(self.engine, items, 0.35)
        self.thread = QThread()
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.on_finished)
        self.worker.error.connect(self.on_error)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    def on_finished(self, mapping):
        self.timer.stop()
        self.process_button.setEnabled(True)
        self.process_button.setText(f"Procesado en {self.elapsed_time:.1f}s")
        self.status_label.setText("Procesamiento completado")
        
        if not self.results_window:
            self.results_window = ResultsWindow()
        
        self.results_window.show()
        self.results_window.raise_()
        self.results_window.activateWindow()
        self.results_window.render_categories(mapping, self.engine)

    def on_error(self, msg):
        logging.error(f"Error durante el procesamiento: {msg}")
        self.timer.stop()
        self.process_button.setEnabled(True)
        self.process_button.setText("Procesar")
        self.status_label.setText("Error en procesamiento")
        QMessageBox.critical(self, "Error de Procesamiento", f"Ocurrió un error al analizar los prompts:\n\n{msg}")
