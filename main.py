import sys
import os
from pathlib import Path

# Limpiar sys.path de rutas conflictivas externas
sys.path = [p for p in sys.path if "appPrompt" not in p]

def setup_runtime():
    # Configurar entorno para evitar conflictos con librerías numéricas
    os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
    os.environ["OMP_NUM_THREADS"] = "1"
    os.environ["MKL_THREADING_LAYER"] = "SEQ"
    os.environ["OPENBLAS_NUM_THREADS"] = "1"
    os.environ["NUMEXPR_NUM_THREADS"] = "1"

    # Pre-cargar Torch para inicializar DLLs
    try:
        import torch
        
        torch_lib_path = Path(torch.__file__).parent / "lib"
        if torch_lib_path.exists():
            if hasattr(os, 'add_dll_directory'):
                try:
                    os.add_dll_directory(str(torch_lib_path))
                except Exception:
                    pass
            os.environ["PATH"] = str(torch_lib_path) + os.pathsep + os.environ["PATH"]
            
    except Exception:
        # Intentar método alternativo si falla el import directo
        try:
            import importlib.util
            torch_spec = importlib.util.find_spec("torch")
            if torch_spec and torch_spec.origin:
                torch_lib_path = Path(torch_spec.origin).parent / "lib"
                if torch_lib_path.exists():
                    os.environ["PATH"] = str(torch_lib_path) + os.pathsep + os.environ["PATH"]
        except Exception:
            pass

setup_runtime()

from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
