"""Full-text index over the corpus, on SQLite FTS5.

This replaced a JSON-file BM25 index that had to be parsed in full on every
command — 2.7 MB and ~250 ms at 1,177 chunks, growing linearly with the
corpus and unbounded. FTS5 queries straight off disk: opening the index is
free regardless of size, and `bm25()` is the same ranking function, in C.

The public surface is unchanged: `Index.load()`, `.search(q, k)`, `len(ix)`.
"""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path

from . import concepts, corpus
from .config import INDEX_PATH, LEGACY_INDEX_PATH

TOKEN = re.compile(r"[a-z0-9][a-z0-9'\-]*")

STOP = frozenset("""
a about above after again against all am an and any are aren't as at be because
been before being below between both but by can cannot could couldn't did didn't
do does doesn't doing don't down during each few for from further had hadn't has
hasn't have haven't having he her here hers herself him himself his how i if in
into is isn't it its itself let's me more most mustn't my myself no nor not of off
on once only or other ought our ours ourselves out over own same shan't she should
shouldn't so some such than that the their theirs them themselves then there these
they this those through to too under until up very was wasn't we were weren't what
when where which while who whom why with won't would wouldn't you your yours
yourself yourselves
""".split())

SCHEMA = """
CREATE VIRTUAL TABLE IF NOT EXISTS chunks USING fts5(
    text,
    title,
    author,
    source  UNINDEXED,
    kind    UNINDEXED,
    path    UNINDEXED,
    doc_id  UNINDEXED,
    tokenize = 'porter unicode61'
);
"""

# Hand-written topic notes and primary texts are denser than scraped pages.
PRIOR = {"note": 1.15, "primary": 1.12, "secondary": 1.0, "reference": 0.98}


def tokenize(text: str) -> list[str]:
    return [t for t in TOKEN.findall(text.lower())
            if t not in STOP and len(t) > 2]


def _match_query(query: str) -> str:
    """Turn free text into an FTS5 MATCH expression (quoted OR-terms)."""
    terms = tokenize(query)
    if not terms:
        return ""
    seen, uniq = set(), []
    for t in terms:
        if t not in seen:
            seen.add(t)
            uniq.append(t)
    return " OR ".join(f'"{t}"' for t in uniq[:40])


class Index:
    def __init__(self, path: Path = INDEX_PATH) -> None:
        self.path = path
        self._conn: sqlite3.Connection | None = None

    # --- connection -----------------------------------------------------

    @property
    def conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(self.path)
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.executescript(SCHEMA)
        return self._conn

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    @classmethod
    def load(cls, path: Path = INDEX_PATH) -> "Index":
        """Open the index. Cheap — nothing is read until a query runs."""
        return cls(path)

    # --- build ----------------------------------------------------------

    @classmethod
    def build(cls, path: Path = INDEX_PATH, verbose: bool = False) -> "Index":
        ix = cls(path)
        c = ix.conn
        c.execute("DELETE FROM chunks")
        rows = []
        for doc in corpus.walk():
            for ch in corpus.chunk(doc):
                rows.append((ch.text, ch.title, ch.author, ch.source,
                             ch.kind, ch.path, ch.doc_id))
            if verbose:
                print(f"  indexed {doc.title}")
            if len(rows) >= 2000:
                c.executemany("INSERT INTO chunks VALUES (?,?,?,?,?,?,?)", rows)
                rows.clear()
        if rows:
            c.executemany("INSERT INTO chunks VALUES (?,?,?,?,?,?,?)", rows)
        c.execute("INSERT INTO chunks(chunks) VALUES('optimize')")
        c.commit()

        # The JSON index this replaced is dead weight once FTS5 is populated.
        if LEGACY_INDEX_PATH.exists():
            LEGACY_INDEX_PATH.unlink()
        return ix

    def save(self) -> None:
        """Kept for API compatibility — FTS5 writes are already committed."""
        if self._conn is not None:
            self._conn.commit()

    # --- query ----------------------------------------------------------

    def search(self, query: str, k: int = 8, per_doc: int = 2,
               expand: bool = True, hop: bool = False) -> list[tuple[float, dict]]:
        """Top-k passages, capped at `per_doc` chunks from any one document.

        Without the cap a single long book — the corpus has a 650k-character
        Gutenberg text — takes every slot, and the answer is grounded in one
        source when several were available. Overflow is kept and used to
        backfill if the cap leaves the result short.
        """
        # A student who knows "weakness of will" should reach passages filed
        # under "akrasia". Alias terms are folded into the same MATCH so BM25
        # still ranks them, rather than being appended as a separate result set.
        terms = query
        if expand:
            extra = concepts.expand(query)
            if extra:
                terms = query + " " + " ".join(extra)
        if hop:
            near = concepts.neighbours(query)
            if near:
                terms += " " + " ".join(near)

        match = _match_query(terms)
        if not match:
            return []
        try:
            rows = self.conn.execute(
                """
                SELECT text, title, author, source, kind, path, doc_id,
                       bm25(chunks, 1.0, 2.0, 0.5) AS rank
                FROM chunks
                WHERE chunks MATCH ?
                ORDER BY rank
                LIMIT ?
                """,
                (match, max(k * 8, 64)),
            ).fetchall()
        except sqlite3.OperationalError:
            return []

        scored: list[tuple[float, dict]] = []
        for r in rows:
            d = dict(r)
            rank = d.pop("rank")
            # bm25() is negative, better matches more negative. Flip it, then
            # apply the source-quality prior.
            score = -rank * PRIOR.get(d.get("kind", ""), 1.0)
            scored.append((score, d))
        scored.sort(key=lambda kv: kv[0], reverse=True)

        picked: list[tuple[float, dict]] = []
        overflow: list[tuple[float, dict]] = []
        seen: dict[str, int] = {}
        for score, d in scored:
            doc = d.get("doc_id", "")
            if seen.get(doc, 0) < per_doc:
                seen[doc] = seen.get(doc, 0) + 1
                picked.append((score, d))
            else:
                overflow.append((score, d))
            if len(picked) == k:
                return picked
        return (picked + overflow)[:k]

    def __len__(self) -> int:
        try:
            return self.conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
        except sqlite3.OperationalError:
            return 0


def rebuild(verbose: bool = True) -> Index:
    return Index.build(verbose=verbose)
