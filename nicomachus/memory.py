"""Long-term memory: what Nicomachus has read, asked, and concluded.

Four tables:
  seen      — every source URL ingested, so nothing is fetched twice
  notes     — durable claims it has written down, with provenance
  questions — its own open questions, the engine of self-directed study
  journal   — a running log of study cycles, for the human to audit
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterator

from .config import MEMORY_DB

SCHEMA = """
CREATE TABLE IF NOT EXISTS seen (
    url        TEXT PRIMARY KEY,
    title      TEXT,
    path       TEXT,
    licence    TEXT,
    fetched_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS notes (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    topic      TEXT NOT NULL,
    claim      TEXT NOT NULL,
    confidence TEXT NOT NULL DEFAULT 'tentative',
    provenance TEXT,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS notes_topic ON notes(topic);

CREATE TABLE IF NOT EXISTS questions (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    question   TEXT NOT NULL UNIQUE,
    topic      TEXT,
    status     TEXT NOT NULL DEFAULT 'open',   -- open | studying | answered | parked
    answer     TEXT,
    asked_at   TEXT NOT NULL,
    closed_at  TEXT
);

CREATE TABLE IF NOT EXISTS journal (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    kind       TEXT NOT NULL,
    summary    TEXT NOT NULL,
    detail     TEXT,
    at         TEXT NOT NULL
);
"""


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


_initialised = False


@contextmanager
def db() -> Iterator[sqlite3.Connection]:
    """A connection per call, safe to use from harvest worker threads.

    WAL lets readers and one writer proceed together; the busy timeout makes
    concurrent writers queue instead of raising "database is locked".
    """
    global _initialised
    conn = sqlite3.connect(MEMORY_DB, timeout=30.0)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=30000")
        if not _initialised:
            conn.executescript(SCHEMA)
            _initialised = True
        yield conn
        conn.commit()
    finally:
        conn.close()


# --- seen ---------------------------------------------------------------

def mark_seen(url: str, title: str, path: str, licence: str = "") -> None:
    with db() as c:
        c.execute(
            "INSERT OR REPLACE INTO seen (url, title, path, licence, fetched_at) "
            "VALUES (?,?,?,?,?)",
            (url, title, path, licence, now()),
        )


def already_seen(url: str) -> bool:
    with db() as c:
        return c.execute("SELECT 1 FROM seen WHERE url=?", (url,)).fetchone() is not None


def forget(url: str) -> None:
    """Drop a URL from `seen` so it can be fetched again under a better query."""
    with db() as c:
        c.execute("DELETE FROM seen WHERE url=?", (url,))


def seen_count() -> int:
    with db() as c:
        return c.execute("SELECT COUNT(*) FROM seen").fetchone()[0]


# --- notes --------------------------------------------------------------

def add_note(topic: str, claim: str, confidence: str = "tentative",
             provenance: str = "") -> int:
    with db() as c:
        cur = c.execute(
            "INSERT INTO notes (topic, claim, confidence, provenance, created_at) "
            "VALUES (?,?,?,?,?)",
            (topic, claim.strip(), confidence, provenance, now()),
        )
        return cur.lastrowid


def notes_for(topic: str, limit: int = 20) -> list[sqlite3.Row]:
    with db() as c:
        return c.execute(
            "SELECT * FROM notes WHERE topic LIKE ? ORDER BY id DESC LIMIT ?",
            (f"%{topic}%", limit),
        ).fetchall()


def note_count() -> int:
    with db() as c:
        return c.execute("SELECT COUNT(*) FROM notes").fetchone()[0]


def recent_notes(limit: int = 20) -> list[sqlite3.Row]:
    with db() as c:
        return c.execute(
            "SELECT * FROM notes ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()


# --- questions ----------------------------------------------------------

def ask(question: str, topic: str = "") -> bool:
    """Record an open question. Returns False if already known."""
    q = question.strip()
    if not q:
        return False
    with db() as c:
        try:
            c.execute(
                "INSERT INTO questions (question, topic, asked_at) VALUES (?,?,?)",
                (q, topic, now()),
            )
            return True
        except sqlite3.IntegrityError:
            return False


def open_questions(limit: int = 10) -> list[sqlite3.Row]:
    with db() as c:
        return c.execute(
            "SELECT * FROM questions WHERE status='open' ORDER BY id LIMIT ?", (limit,)
        ).fetchall()


def mark_studying(qid: int) -> None:
    """A cycle has read for this question; don't hand it back as the next pick."""
    with db() as c:
        c.execute("UPDATE questions SET status='studying' WHERE id=? AND status='open'",
                  (qid,))


def answer_question(qid: int, answer: str) -> None:
    with db() as c:
        c.execute(
            "UPDATE questions SET status='answered', answer=?, closed_at=? WHERE id=?",
            (answer, now(), qid),
        )


def question_stats() -> dict[str, int]:
    with db() as c:
        rows = c.execute(
            "SELECT status, COUNT(*) n FROM questions GROUP BY status"
        ).fetchall()
    return {r["status"]: r["n"] for r in rows}


# --- journal ------------------------------------------------------------

def log(kind: str, summary: str, detail: str = "") -> None:
    with db() as c:
        c.execute(
            "INSERT INTO journal (kind, summary, detail, at) VALUES (?,?,?,?)",
            (kind, summary, detail, now()),
        )


def journal(limit: int = 20) -> list[sqlite3.Row]:
    with db() as c:
        return c.execute(
            "SELECT * FROM journal ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
