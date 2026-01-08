import re
from typing import Dict, List, Set

class PromptGenerator:
    """Generador de prompts dinámico."""
    
    def __init__(self):
        self.category_order = [
            "angulo",
            "calidad_tecnica", 
            "estilo_artistico",
            "composicion",
            "atmosfera_vibe",
            "loras_estilos_artistico",
            "loras_detalles_mejoras",
            "loras_modelos_especificos",
            "loras_personaje",
            "fondo",
            "personaje",
            "cabello_forma",
            "cabello_color",
            "cabello_accesorios",
            "rostro_accesorios",
            "ojos",
            "expresion_facial_ojos",
            "expresion_facial_mejillas",
            "expresion_facial_boca",
            "postura_cabeza",
            "direccion_mirada_personaje",
            "vestuario_general",
            "vestuario_superior",
            "vestuario_inferior",
            "vestuario_accesorios",
            "ropa_interior_superior",
            "ropa_interior_inferior",
            "ropa_interior_accesorios",
            "tipo_de_cuerpo",
            "rasgo_fisico_cuerpo",
            "rasgo_fisico_piernas",
            "pose_actitud_global",
            "pose_brazos",
            "pose_piernas",
            "orientacion_personaje",
            "actitud_emocion",
            "nsfw",
            "objetos_interaccion",
            "objetos_escenario",
            "mirada_espectador"
        ]
        
        self.active_categories: Dict[str, str] = {}
        self.duplicate_terms: Set[str] = set()
        
    def update_category(self, category_name: str, value: str):
        """Actualiza categoría."""
        if value and value.strip():
            self.active_categories[category_name] = value.strip()
        else:
            self.active_categories.pop(category_name, None)
    
    def clear_category(self, category_name: str):
        """Limpia categoría."""
        self.active_categories.pop(category_name, None)
    
    def clear_all(self):
        """Limpia todo."""
        self.active_categories.clear()
    
    def validate_input(self, text: str) -> str:
        """Valida input."""
        if not text:
            return ""
        
        cleaned = re.sub(r'\s+', ' ', text.strip())
        cleaned = re.sub(r'[^a-zA-Z0-9\s,.()\[\]<>:_-]', '', cleaned)
        
        return cleaned
    
    def remove_duplicates(self, prompt_parts: List[str]) -> List[str]:
        """Elimina duplicados."""
        seen = set()
        unique_parts = []
        
        for part in prompt_parts:
            normalized = part.lower().strip()
            if normalized and normalized not in seen:
                seen.add(normalized)
                unique_parts.append(part)
        
        return unique_parts
    
    def generate_prompt(self) -> str:
        """Genera prompt final."""
        if not self.active_categories:
            return ""
        
        prompt_parts = []
        
        for category in self.category_order:
            if category in self.active_categories:
                value = self.active_categories[category]
                if value:
                    cleaned_value = value.rstrip(', ').strip()
                    if cleaned_value:
                        prompt_parts.append(cleaned_value)
        
        for category, value in self.active_categories.items():
            if category not in self.category_order and value:
                cleaned_value = value.rstrip(', ').strip()
                if cleaned_value:
                    prompt_parts.append(cleaned_value)
        
        unique_parts = self.remove_duplicates(prompt_parts)
        
        final_prompt = ", ".join(unique_parts)
        final_prompt = re.sub(r'\s+', ' ', final_prompt)
        
        return final_prompt.strip()
    
    def get_category_value(self, category_name: str) -> str:
        """Obtiene valor de categoría."""
        return self.active_categories.get(category_name, "")
    
    def get_active_categories(self) -> Dict[str, str]:
        """Obtiene categorías activas."""
        return self.active_categories.copy()
    
    def get_prompt_statistics(self) -> Dict[str, int]:
        """Obtiene estadísticas."""
        prompt = self.generate_prompt()
        if not prompt:
            return {"total_terms": 0, "total_characters": 0}
        
        terms = [term.strip() for term in prompt.split(",")]
        return {
            "total_terms": len(terms),
            "total_characters": len(prompt)
        }
