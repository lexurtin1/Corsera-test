import json
from pathlib import Path
from typing import Any, Dict, Optional


class SessionStore:
    """Very small JSON-backed store for uploaded orders."""

    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text("{}", encoding="utf-8")

    def _read(self) -> Dict[str, Dict[str, Any]]:
        if not self.path.exists():
            return {}
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}

    def _write(self, data: Dict[str, Dict[str, Any]]) -> None:
        self.path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def get(self, order_id: str) -> Optional[Dict[str, Any]]:
        return self._read().get(order_id)

    def set(self, order_id: str, record: Dict[str, Any]) -> None:
        data = self._read()
        data[order_id] = record
        self._write(data)

    def update(self, order_id: str, updates: Dict[str, Any]) -> None:
        data = self._read()
        record = data.get(order_id, {})
        record.update(updates)
        data[order_id] = record
        self._write(data)
