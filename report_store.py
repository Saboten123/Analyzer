"""Short-lived in-memory storage for result-page PDF downloads."""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from threading import Lock
from uuid import uuid4


@dataclass(frozen=True)
class StoredAnalysis:
    analysis: dict
    expires_at: datetime


class AnalysisStore:
    """Small development-friendly store; replace with Redis/S3 in production."""

    def __init__(self, ttl_minutes: int = 30):
        self.ttl = timedelta(minutes=ttl_minutes)
        self._items: dict[str, StoredAnalysis] = {}
        self._lock = Lock()

    def put(self, analysis: dict) -> str:
        token = uuid4().hex
        now = datetime.now(timezone.utc)
        with self._lock:
            self._items = {key: item for key, item in self._items.items() if item.expires_at > now}
            self._items[token] = StoredAnalysis(analysis, now + self.ttl)
        return token

    def get(self, token: str) -> dict | None:
        with self._lock:
            item = self._items.get(token)
            if item is None or item.expires_at <= datetime.now(timezone.utc):
                self._items.pop(token, None)
                return None
            return item.analysis
