import os
import json

# Constantes de rutas
CATEGORIES_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "categories.json")
TAGS_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "tags.json")
ICON_EDIT = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "assets", "icons", "edit.png")
ICON_SAVE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "assets", "icons", "save.png")
CATEGORY_COLORS_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "category_colors.json")

# Constantes de estilo
DEFAULT_CARD_COLOR = "#252525"

def load_categories_and_tags():
    """Carga las categorías y sus tags asociados desde los archivos JSON"""
    with open(CATEGORIES_PATH, "r", encoding="utf-8") as f:
        categories = json.load(f)["categorias"]
    with open(TAGS_PATH, "r", encoding="utf-8") as f:
        tags = json.load(f)
    # Relaciona cada categoría con sus tags (o lista vacía si no hay)
    categories_real = [
        {"name": cat.replace("_", " ").capitalize(), "icon": None, "tags": tags.get(cat, [])}
        for cat in categories
    ]
    return categories_real

def _ensure_colors_file():
    """Create a colors file if none exists; prefer separate file for clarity."""
    try:
        if not os.path.isfile(CATEGORY_COLORS_PATH):
            # Initialize empty mapping
            with open(CATEGORY_COLORS_PATH, "w", encoding="utf-8") as f:
                json.dump({}, f, ensure_ascii=False, indent=2)
    except Exception:
        # Silently ignore; fallback to categories.json if needed
        pass

def load_category_colors():
    """Load persisted category colors.
    Priority:
    1) data/category_colors.json as a mapping {snake_case: "#rrggbb"}
    2) data/categories.json under key "colors" if present
    Returns a dict.
    """
    # Try dedicated colors file first
    try:
        if os.path.isfile(CATEGORY_COLORS_PATH):
            with open(CATEGORY_COLORS_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
    except Exception:
        pass
    # Fallback to categories.json colors key
    try:
        if os.path.isfile(CATEGORIES_PATH):
            with open(CATEGORIES_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                colors = data.get("colors")
                if isinstance(colors, dict):
                    return colors
    except Exception:
        pass
    return {}

def save_category_color(category_snake_case: str, color_hex: str):
    """Persist a color for a category. Store in category_colors.json.
    If categories.json has an embedded "colors" dict but separate file is missing,
    migrate/save to the separate file to keep data tidy.
    """
    # Normalize hex (e.g., from QColor.name())
    if isinstance(color_hex, str) and not color_hex.startswith("#"):
        color_hex = f"#{color_hex}"
    try:
        _ensure_colors_file()
        # Load current
        current = {}
        if os.path.isfile(CATEGORY_COLORS_PATH):
            with open(CATEGORY_COLORS_PATH, "r", encoding="utf-8") as f:
                try:
                    current = json.load(f) or {}
                except Exception:
                    current = {}
        # Update and save
        current[category_snake_case] = color_hex
        with open(CATEGORY_COLORS_PATH, "w", encoding="utf-8") as f:
            json.dump(current, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        # As a fallback, try to write into categories.json under colors
        try:
            with open(CATEGORIES_PATH, "r+", encoding="utf-8") as f:
                data = json.load(f)
                colors = data.get("colors", {})
                colors[category_snake_case] = color_hex
                data["colors"] = colors
                f.seek(0)
                json.dump(data, f, ensure_ascii=False, indent=2)
                f.truncate()
            return True
        except Exception:
            return False

def rename_category_color_key(old_name_capitalized: str, new_name_capitalized: str):
    """If a color mapping exists, move it from old to new snake_case key."""
    old_key = old_name_capitalized.lower().replace(" ", "_")
    new_key = new_name_capitalized.lower().replace(" ", "_")
    # Try dedicated colors file
    try:
        if os.path.isfile(CATEGORY_COLORS_PATH):
            with open(CATEGORY_COLORS_PATH, "r+", encoding="utf-8") as f:
                data = json.load(f) or {}
                if old_key in data:
                    data[new_key] = data.pop(old_key)
                    f.seek(0)
                    json.dump(data, f, ensure_ascii=False, indent=2)
                    f.truncate()
                    return True
    except Exception:
        pass
    # Fallback: categories.json embedded colors
    try:
        with open(CATEGORIES_PATH, "r+", encoding="utf-8") as f:
            data = json.load(f)
            colors = data.get("colors", {})
            if old_key in colors:
                colors[new_key] = colors.pop(old_key)
                data["colors"] = colors
                f.seek(0)
                json.dump(data, f, ensure_ascii=False, indent=2)
                f.truncate()
                return True
    except Exception:
        pass
    return False

def normalize_category(name):
    """Normaliza el nombre de una categoría para búsquedas"""
    return name.lower().replace(" ", "").replace("(", "").replace(")", "").replace("_", "")

def update_categories_json(name):
    """Actualiza el archivo categories.json con una nueva categoría"""
    with open(CATEGORIES_PATH, "r+", encoding="utf-8") as f:
        data = json.load(f)
        if name not in data["categorias"]:
            data["categorias"].append(name)
            f.seek(0)
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.truncate()
            return True
    return False

def update_tags_json(name, tags):
    """Actualiza el archivo tags.json con los tags de una categoría"""
    with open(TAGS_PATH, "r+", encoding="utf-8") as f:
        tags_data = json.load(f)
        tags_data[name] = tags
        f.seek(0)
        json.dump(tags_data, f, ensure_ascii=False, indent=2)
        f.truncate()

def rename_category_in_files(old_name, new_name):
    """Renombra una categoría en todos los archivos JSON"""
    # Actualizar categories.json
    with open(CATEGORIES_PATH, "r+", encoding="utf-8") as f:
        data = json.load(f)
        if old_name in data["categorias"]:
            index = data["categorias"].index(old_name)
            data["categorias"][index] = new_name
            f.seek(0)
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.truncate()
    
    # Actualizar tags.json
    old_key = old_name.lower().replace(" ", "_")
    new_key = new_name.lower().replace(" ", "_")
    
    with open(TAGS_PATH, "r+", encoding="utf-8") as f:
        tags_data = json.load(f)
        if old_key in tags_data:
            tags_data[new_key] = tags_data.pop(old_key)
            f.seek(0)
            json.dump(tags_data, f, ensure_ascii=False, indent=2)
            f.truncate()

def save_categories_order(new_order):
    """Guarda el nuevo orden de categorías en categories.json.
    new_order debe ser una lista de claves snake_case (p.ej. 'vestuario_superior').
    """
    if not isinstance(new_order, list):
        return False
    try:
        with open(CATEGORIES_PATH, "r+", encoding="utf-8") as f:
            data = json.load(f)
            data["categorias"] = new_order
            f.seek(0)
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.truncate()
        return True
    except Exception:
        return False