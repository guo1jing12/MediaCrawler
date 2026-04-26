import json
import os
import threading
from typing import Any, Dict, Optional

import config
from tools import utils


class CrawlCheckpoint:
    def __init__(self, platform: Optional[str] = None, crawler_type: Optional[str] = None, account: Optional[str] = None):
        self.enabled = bool(config.ENABLE_RESUME_CRAWL)
        self.platform = platform or config.PLATFORM
        self.crawler_type = crawler_type or config.CRAWLER_TYPE
        self.account = account or config.ACCOUNT_NAME or "default"
        self._lock = threading.Lock()
        self.path = self._build_path()
        self._state: Dict[str, Any] = {"completed": {}}
        if self.enabled:
            self._load()

    def _build_path(self) -> str:
        if config.RESUME_CHECKPOINT_FILE:
            return config.RESUME_CHECKPOINT_FILE
        filename = f"{self.platform}_{self.crawler_type}_{self.account}.json"
        return os.path.join(config.RESUME_CHECKPOINT_DIR, filename)

    def _load(self) -> None:
        if not os.path.exists(self.path):
            return
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            if isinstance(loaded, dict):
                self._state.update(loaded)
                self._state.setdefault("completed", {})
        except Exception as e:
            utils.logger.warning(f"[CrawlCheckpoint] Failed to load checkpoint {self.path}: {e}")

    def _save(self) -> None:
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        tmp_path = f"{self.path}.tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(self._state, f, ensure_ascii=False, indent=2, sort_keys=True)
        os.replace(tmp_path, self.path)

    @staticmethod
    def search_page_key(keyword: str, page: int) -> str:
        return f"search:{keyword}:page:{page}"

    @staticmethod
    def item_key(item_type: str, item_id: str) -> str:
        return f"{item_type}:{item_id}"

    def is_completed(self, key: str) -> bool:
        if not self.enabled:
            return False
        return bool(self._state.get("completed", {}).get(key))

    def mark_completed(self, key: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        if not self.enabled:
            return
        with self._lock:
            self._state.setdefault("completed", {})[key] = metadata or True
            self._save()

    def reset(self) -> None:
        if os.path.exists(self.path):
            os.remove(self.path)
        self._state = {"completed": {}}
