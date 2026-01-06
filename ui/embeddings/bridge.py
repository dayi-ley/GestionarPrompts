from pathlib import Path
import json
import time
import os
import logging
import subprocess
import shlex
from urllib.request import urlopen
from urllib.error import URLError
import os
logger = logging.getLogger(__name__)

def _bridge_path():
    base = Path(__file__).resolve().parents[1]
    root = base.parent
    bdir = root / "bridge"
    bdir.mkdir(parents=True, exist_ok=True)
    return bdir / "app_prompts_updates.json"

def receiver_ready():
    base = Path(__file__).resolve().parents[1]
    root = base.parent
    flag = root / "bridge" / "app_prompts_ready.flag"
    if os.environ.get("APP_PROMPTS_READY", "").lower() in ("1", "true", "yes"):
        return True
    url = os.environ.get("APP_PROMPTS_HEALTH_URL", "")
    if url:
        try:
            with urlopen(url, timeout=1.5) as r:
                code = getattr(r, "status", 200)
                if int(code) == 200:
                    return True
        except URLError:
            pass
        except Exception:
            pass
    pname = os.environ.get("APP_PROMPTS_PROCESS_NAME", "")
    if pname:
        try:
            proc = subprocess.run(["tasklist"], capture_output=True, text=True, timeout=2)
            out = proc.stdout.lower()
            if pname.lower() in out:
                return True
        except Exception:
            pass
    return flag.exists()

def send_update(category, items, operation="append"):
    try:
        fp = _bridge_path()
        payload = {
            "source_app": "promptEmbeddings",
            "schema_version": 1,
            "timestamp": int(time.time()),
            "operation": operation,
            "category": category,
            "items": list(dict.fromkeys(items or []))
        }
        current = []
        if fp.exists():
            try:
                data = json.loads(fp.read_text(encoding="utf-8"))
                if isinstance(data, list):
                    current = data
                elif isinstance(data, dict) and "updates" in data and isinstance(data["updates"], list):
                    current = data["updates"]
            except Exception:
                current = []
        current.append(payload)
        tmp = fp.with_suffix(".tmp")
        tmp.write_text(json.dumps(current, ensure_ascii=False), encoding="utf-8")
        if fp.exists():
            try:
                os.replace(tmp, fp)
            except Exception:
                tmp.replace(fp)
        else:
            tmp.replace(fp)
        logger.info(f"bridge write ok category={category} items={len(items or [])}")
        return True
    except Exception as e:
        logger.error(str(e))
        return False
