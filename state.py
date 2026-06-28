# -*- coding: utf-8 -*-
import json, time
from pathlib import Path
from typing import Any, Dict

class BotState:
    def __init__(self, path: str, defaults: Dict[str, Any]):
        self.path = Path(path)
        self.defaults = defaults
        self.data: Dict[str, Any] = {}
        self.load()

    def load(self) -> None:
        if self.path.exists():
            try:
                loaded = json.loads(self.path.read_text(encoding="utf-8"))
            except Exception:
                loaded = {}
        else:
            loaded = {}
        self.data = dict(self.defaults)
        self.data.update(loaded)
        self.data.setdefault("active_incidents", [])
        self.data.setdefault("last_posts", [])
        self.data.setdefault("created_at", int(time.time()))
        self.save()

    def save(self) -> None:
        self.path.write_text(json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8")

    def append_post(self, text: str) -> None:
        posts = self.data.setdefault("last_posts", [])
        posts.append({"ts": int(time.time()), "text": text})
        self.data["last_posts"] = posts[-20:]
        self.save()

    def clear_active(self) -> None:
        self.data["active_incidents"] = []
        self.save()
