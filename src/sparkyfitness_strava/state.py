"""Durable journal and OAuth storage; one process per state volume."""
import json
import os
from pathlib import Path
import sqlite3


def encode(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


class State:
    def __init__(self, directory):
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        self.lock = (directory / "connector.lock").open("a+b")
        try:
            if os.name == "nt":
                import msvcrt
                self.lock.seek(0)
                self.lock.write(b"0")
                self.lock.flush()
                self.lock.seek(0)
                msvcrt.locking(self.lock.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(self.lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            self.lock.close()
            raise ValueError("Another connector command is using this state volume; stop watch first") from None
        self.db = sqlite3.connect(directory / "state.sqlite3")
        self.db.execute("PRAGMA synchronous=FULL")
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS exports (session TEXT PRIMARY KEY, value TEXT NOT NULL);
        """)
        self.db.commit()
        (directory / "state.sqlite3").chmod(0o600)

    def close(self):
        self.db.close()
        self.lock.close()

    def get(self, key, default=None):
        row = self.db.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return json.loads(row[0]) if row else default

    def set(self, key, value):
        self.db.execute("INSERT OR REPLACE INTO settings VALUES (?,?)", (key, encode(value)))
        self.db.commit()

    def bind(self, key, value):
        old = self.get(key)
        if old is not None and old != value:
            raise ValueError("Account or API endpoint changed; use a separate state volume")
        self.set(key, value)

    def export(self, session):
        row = self.db.execute("SELECT value FROM exports WHERE session=?", (str(session),)).fetchone()
        return json.loads(row[0]) if row else None

    def save(self, session, value):
        self.db.execute("INSERT OR REPLACE INTO exports VALUES (?,?)", (str(session), encode(value)))
        self.db.commit()

    def exports(self):
        return {row[0]: json.loads(row[1]) for row in self.db.execute("SELECT session,value FROM exports ORDER BY session")}
