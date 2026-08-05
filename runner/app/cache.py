"""編譯結果快取 — 相同程式碼不重新編譯（互動練習中重跑佔比高）。

key = sha256(編譯旗標 + 原始碼)；value = 快取目錄下的可執行檔。
LRU 上限 settings.cache_max_entries，逐出即刪檔。
單一 asyncio event loop 內使用，無需鎖。
"""

import hashlib
import os
from collections import OrderedDict

from .config import settings


class BinaryCache:
    def __init__(self) -> None:
        self._entries: OrderedDict[str, str] = OrderedDict()
        os.makedirs(settings.cache_dir, exist_ok=True)

    def __len__(self) -> int:
        return len(self._entries)

    @staticmethod
    def key_for(code: str) -> str:
        h = hashlib.sha256()
        h.update(" ".join(settings.cxx_flags).encode())
        h.update(b"\x00")
        h.update(code.encode())
        return h.hexdigest()

    def get(self, key: str) -> str | None:
        """命中回傳可執行檔路徑並更新 LRU 順序。"""
        path = self._entries.get(key)
        if path is None:
            return None
        if not os.path.exists(path):  # 檔案被外部清掉（如 /tmp 清理）
            del self._entries[key]
            return None
        self._entries.move_to_end(key)
        return path

    def put(self, key: str, binary_path: str) -> str:
        """把編譯產物移入快取，回傳快取後路徑；超額逐出最舊項。"""
        dest = os.path.join(settings.cache_dir, key)
        os.replace(binary_path, dest)
        self._entries[key] = dest
        self._entries.move_to_end(key)
        while len(self._entries) > settings.cache_max_entries:
            _, old_path = self._entries.popitem(last=False)
            try:
                os.unlink(old_path)
            except OSError:
                pass
        return dest


binary_cache = BinaryCache()
