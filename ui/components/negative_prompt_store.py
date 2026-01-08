import json
import os
from typing import Dict, List, Any
from datetime import datetime

class NegativePromptStore:
    """Gestor de configuración y persistencia."""
    
    def __init__(self):
        self.config_dir = "data"
        self.config_file = os.path.join(self.config_dir, "settings.json")
        self.characters_file = os.path.join(self.config_dir, "characters.json")
        self.scenes_file = os.path.join(self.config_dir, "scenes.json")
        self.history_file = os.path.join(self.config_dir, "prompt_history.json")
        
        os.makedirs(self.config_dir, exist_ok=True)
        
        self.default_settings = {
            "theme": "dark",
            "window_size": "1400x900",
            "sidebar_width": 280,
            "auto_save": True,
            "max_history": 100,
            "default_negative_prompt": "blurry, low quality, distorted, deformed, ugly, bad anatomy",
            "saved_negative_prompts": []
        }
        
        self.settings = self.load_settings()
    
    def load_settings(self) -> Dict[str, Any]:
        """Carga configuraciones."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                self.save_settings(self.default_settings)
                return self.default_settings
        except Exception as e:
            print(f"Error cargando configuraciones: {e}")
            return self.default_settings
    
    def save_settings(self, settings: Dict[str, Any]):
        """Guarda configuraciones."""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error guardando configuraciones: {e}")
    
    def get_setting(self, key: str, default=None):
        """Obtiene configuración."""
        return self.settings.get(key, default)
    
    def set_setting(self, key: str, value: Any):
        """Establece configuración."""
        self.settings[key] = value
        self.save_settings(self.settings)
    
    def load_characters(self) -> List[Dict[str, Any]]:
        """Carga personajes."""
        try:
            if os.path.exists(self.characters_file):
                with open(self.characters_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return []
        except Exception as e:
            print(f"Error cargando personajes: {e}")
            return []
    
    def save_characters(self, characters: List[Dict[str, Any]]):
        """Guarda personajes."""
        try:
            with open(self.characters_file, 'w', encoding='utf-8') as f:
                json.dump(characters, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error guardando personajes: {e}")
    
    def load_scenes(self) -> List[Dict[str, Any]]:
        """Carga escenas."""
        try:
            if os.path.exists(self.scenes_file):
                with open(self.scenes_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return []
        except Exception as e:
            print(f"Error cargando escenas: {e}")
            return []
    
    def save_scenes(self, scenes: List[Dict[str, Any]]):
        """Guarda escenas."""
        try:
            with open(self.scenes_file, 'w', encoding='utf-8') as f:
                json.dump(scenes, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error guardando escenas: {e}")
    
    def load_prompt_history(self) -> List[Dict[str, Any]]:
        """Carga historial."""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
                    max_history = self.get_setting("max_history", 100)
                    return history[-max_history:] if len(history) > max_history else history
            return []
        except Exception as e:
            print(f"Error cargando historial: {e}")
            return []
    
    def save_prompt_history(self, history: List[Dict[str, Any]]):
        """Guarda historial."""
        try:
            max_history = self.get_setting("max_history", 100)
            if len(history) > max_history:
                history = history[-max_history:]
            
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error guardando historial: {e}")
    
    def add_prompt_to_history(self, prompt: str, negative_prompt: str = ""):
        """Añade prompt al historial."""
        history = self.load_prompt_history()
        
        new_entry = {
            "timestamp": datetime.now().isoformat(),
            "prompt": prompt,
            "negative_prompt": negative_prompt
        }
        
        history.append(new_entry)
        self.save_prompt_history(history)
    
    def export_prompt(self, prompt: str, negative_prompt: str = "", format: str = "json") -> str:
        """Exporta prompt."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if format.lower() == "json":
            data = {
                "prompt": prompt,
                "negative_prompt": negative_prompt,
                "timestamp": datetime.now().isoformat(),
                "version": "1.0"
            }
            filename = f"prompt_export_{timestamp}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        
        elif format.lower() == "txt":
            filename = f"prompt_export_{timestamp}.txt"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"Prompt: {prompt}\n")
                f.write(f"Negative Prompt: {negative_prompt}\n")
                f.write(f"Exported: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        else:
            raise ValueError(f"Formato no soportado: {format}")
        
        return filename 
    
    def get_saved_negative_prompts(self) -> List[str]:
        """Obtiene negative prompts guardados."""
        return self.settings.get("saved_negative_prompts", [])

    def add_saved_negative_prompt(self, text: str) -> int:
        """Agrega negative prompt."""
        prompts = self.get_saved_negative_prompts()
        prompts.append(text)
        self.set_setting("saved_negative_prompts", prompts)
        return len(prompts)

    def update_saved_negative_prompt(self, index: int, new_text: str):
        """Actualiza negative prompt."""
        prompts = self.get_saved_negative_prompts()
        if 1 <= index <= len(prompts):
            prompts[index - 1] = new_text
            self.set_setting("saved_negative_prompts", prompts)

    def delete_saved_negative_prompt(self, index: int):
        """Elimina negative prompt."""
        prompts = self.get_saved_negative_prompts()
        if 1 <= index <= len(prompts):
            del prompts[index - 1]
            self.set_setting("saved_negative_prompts", prompts)
