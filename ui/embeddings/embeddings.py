import sys
import os
from pathlib import Path
import json
import hashlib
import numpy as np
import logging

logger = logging.getLogger(__name__)
FALLBACK_CATEGORY = "No localizado"

class EmbeddingsEngine:
    def __init__(self):
        self.model = None

    def _ensure(self):
        if self.model is None:
            try:
                from sentence_transformers import SentenceTransformer
                try:
                    from sentence_transformers.util import set_progress_bar_enabled
                    set_progress_bar_enabled(False)
                except Exception:
                    pass
            except ModuleNotFoundError as e:
                raise RuntimeError(
                    "Faltan dependencias: instala 'sentence-transformers' y 'torch', o coloca el modelo local en 'model/'."
                ) from e
            base = Path(__file__).resolve().parent
            model_root = base / "model"
            local_sub = model_root / "bge-large-en"
            if local_sub.exists():
                load_path = str(local_sub)
            elif model_root.exists():
                load_path = str(model_root)
            else:
                load_path = "BAAI/bge-large-en"
            self.model = SentenceTransformer(load_path, device="cpu")

    def embed(self, texts):
        self._ensure()
        logger.info(f"embedding {len(texts)} items")
        return self.model.encode(texts, normalize_embeddings=True, convert_to_numpy=True, device="cpu", show_progress_bar=False)

    def _load_config(self, force=False):
        if not force and hasattr(self, "_config_loaded") and self._config_loaded:
            return
        cfg_path = Path(__file__).resolve().parent / "config" / "categories.json"
        self._categories = {}
        self._cat_thresholds = {}
        self._cat_keywords = {}
        self._whitelist = set()
        self._global_threshold = 0.35
        logger.info(f"cargando config {cfg_path}")
        if cfg_path.exists():
            data = json.loads(cfg_path.read_text(encoding="utf-8"))
            g = data.get("global", {})
            self._global_threshold = float(g.get("threshold", 0.35))
            wl = g.get("whitelist", [])
            self._whitelist = set(s.lower() for s in wl if isinstance(s, str))
            cats = data.get("categories", {})
            for name, info in cats.items():
                anchors = info.get("anchors", [])
                self._categories[name] = anchors
                self._cat_keywords[name] = info.get("keywords", [])
                if "threshold" in info:
                    self._cat_thresholds[name] = float(info["threshold"])
            logger.info(f"categorías cargadas: {len(self._categories)}")
        else:
            self._categories = {FALLBACK_CATEGORY: [FALLBACK_CATEGORY]}
            self._cat_keywords[FALLBACK_CATEGORY] = []
            self._whitelist = set()
            logger.info("config no encontrada, usando fallback")
        self._config_loaded = True

    def _category_proto_vecs(self):
        self._load_config()
        if hasattr(self, "_cat_proto") and self._cat_proto is not None:
            return self._cat_proto, list(self._categories.keys())
        names = list(self._categories.keys())
        logger.info(f"construyendo/cargando prototipos de {len(names)} categorías")
        cache_dir = Path(__file__).resolve().parent / "cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        proto_path = cache_dir / "prototypes.npy"
        meta_path = cache_dir / "prototypes.meta.json"
        cfg_path = Path(__file__).resolve().parent / "config" / "categories.json"
        cfg_hash = hashlib.sha1(cfg_path.read_bytes()).hexdigest() if cfg_path.exists() else ""
        if proto_path.exists() and meta_path.exists():
            try:
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
                if meta.get("hash") == cfg_hash and meta.get("names") == names:
                    self._cat_proto = np.load(proto_path)
                    logger.info("prototipos cargados desde cache")
                    return self._cat_proto, names
            except Exception:
                logger.info("cache inválido, se recalculará")
        proto_vecs = []
        for name in names:
            anchors = self._categories.get(name) or [name.replace("_", " ")]
            vecs = self.model.encode(anchors, normalize_embeddings=True, convert_to_numpy=True, device="cpu", show_progress_bar=False)
            v = vecs.mean(axis=0)
            n = np.linalg.norm(v) + 1e-12
            proto_vecs.append(v / n)
        self._cat_proto = np.stack(proto_vecs)
        meta_path.write_text(json.dumps({"hash": cfg_hash, "names": names}, ensure_ascii=False), encoding="utf-8")
        np.save(proto_path, self._cat_proto)
        logger.info("prototipos listos y cacheados")
        return self._cat_proto, names

    def _lexical_boost(self, item_lower, names):
        boosts = np.zeros(len(names), dtype=np.float32)
        for i, name in enumerate(names):
            kws = self._cat_keywords.get(name, [])
            hit = 0
            for kw in kws:
                if kw and kw.lower() in item_lower:
                    hit += 1
            if hit:
                boosts[i] = min(0.15, 0.05 * hit)
        return boosts

    def get_whitelist(self):
        self._load_config()
        return getattr(self, "_whitelist", set())

    def categorize(self, items, threshold=None):
        logger.info(f"categorizar {len(items)} ítems")
        vecs = self.embed(items)
        cats, names = self._category_proto_vecs()
        result = {}
        for idx, v in enumerate(vecs):
            sims = np.dot(cats, v)
            boosts = self._lexical_boost(items[idx].lower(), names)
            sims = sims + boosts
            best_i = int(np.argmax(sims))
            best_cat = names[best_i]
            best_score = float(sims[best_i])
            thr = self._cat_thresholds.get(best_cat, self._global_threshold) if threshold is None else threshold
            if best_score >= thr:
                result.setdefault(best_cat, []).append(items[idx])
            else:
                result.setdefault(FALLBACK_CATEGORY, []).append(items[idx])
        logger.info("categorías asignadas: " + ", ".join(f"{k}={len(v)}" for k,v in result.items()))
        return result

    def cluster_texts(self, texts, threshold=0.7):
        vecs = self.embed(texts)
        n = len(texts)
        used = [False] * n
        clusters = []
        for i in range(n):
            if used[i]:
                continue
            cluster = [i]
            used[i] = True
            for j in range(i + 1, n):
                if used[j]:
                    continue
                sim = float(np.dot(vecs[i], vecs[j]))
                if sim >= threshold:
                    used[j] = True
                    cluster.append(j)
            clusters.append(cluster)
        return clusters
