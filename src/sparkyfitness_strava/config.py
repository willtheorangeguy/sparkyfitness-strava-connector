from dataclasses import dataclass
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo
import os


def endpoint(value):
    parsed = urlsplit(value)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError("API URLs must be HTTP(S) URLs without credentials, query or fragment")
    return value.rstrip("/")


@dataclass
class Config:
    data_dir: Path
    sparkyfitness_url: str
    sparkyfitness_api_key: str
    client_id: str
    client_secret: str
    strava_url: str = "https://www.strava.com"
    timezone: str = "UTC"
    since: str = ""
    interval: int = 900
    settle: int = 300
    batch: int = 10

    def __post_init__(self):
        self.sparkyfitness_url = endpoint(self.sparkyfitness_url)
        self.strava_url = endpoint(self.strava_url)
        try:
            ZoneInfo(self.timezone)
        except KeyError:
            raise ValueError("WORKOUT_TIMEZONE must name an installed IANA timezone") from None
        if self.since:
            date.fromisoformat(self.since)
        if self.interval < 60 or self.settle < 0 or not 1 <= self.batch <= 100:
            raise ValueError("Interval must be >=60, settle >=0 and batch between 1 and 100")

    @classmethod
    def env(cls):
        e = os.environ
        return cls(Path(e.get("DATA_DIR", "/data")), e.get("SPARKYFITNESS_BASE_URL", "http://host.docker.internal:8102"),
                   e.get("SPARKYFITNESS_API_KEY", ""), e.get("STRAVA_CLIENT_ID", ""), e.get("STRAVA_CLIENT_SECRET", ""),
                   e.get("STRAVA_BASE_URL", "https://www.strava.com"), e.get("WORKOUT_TIMEZONE", "UTC"),
                   e.get("EXPORT_SINCE", ""), int(e.get("SYNC_INTERVAL_SECONDS", "900")),
                   int(e.get("SETTLE_SECONDS", "300")), int(e.get("MAX_UPLOADS_PER_SYNC", "10")))
