"""Documents: on-disk format, chunking, and the corpus walker.

Every document is a UTF-8 text file with a small YAML-ish front matter block:

    ---
    title: Nicomachean Ethics, Book II
    author: Aristotle
    source: https://www.gutenberg.org/ebooks/8438
    licence: public-domain
    kind: primary | secondary | note | reference
    added: 2026-08-29
    ---
    <body>

Front matter is deliberately hand-editable — the corpus should stay readable
without this program.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Iterable, Iterator

from .config import CORPUS_DIR, SETTINGS, TOPICS_DIR

FRONT = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.S)
_WS = re.compile(r"[ \t]+")
_NL = re.compile(r"\n{3,}")


@dataclass
class Document:
    path: Path
    meta: dict[str, str]
    body: str

    @property
    def doc_id(self) -> str:
        return hashlib.sha1(str(self.path).encode("utf-8")).hexdigest()[:16]

    @property
    def title(self) -> str:
        return self.meta.get("title") or self.path.stem.replace("_", " ")

    @property
    def author(self) -> str:
        return self.meta.get("author", "")

    @property
    def source(self) -> str:
        return self.meta.get("source", "")

    @property
    def kind(self) -> str:
        return self.meta.get("kind", "reference")

    def citation(self) -> str:
        bits = [self.title]
        if self.author:
            bits.append(self.author)
        if self.source:
            bits.append(self.source)
        return " — ".join(bits)


@dataclass
class Chunk:
    doc_id: str
    ordinal: int
    text: str
    title: str
    author: str
    source: str
    kind: str
    path: str

    @property
    def chunk_id(self) -> str:
        return f"{self.doc_id}:{self.ordinal}"


def parse(path: Path) -> Document:
    raw = path.read_text(encoding="utf-8", errors="replace")
    meta: dict[str, str] = {}
    m = FRONT.match(raw)
    body = raw
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, _, v = line.partition(":")
                meta[k.strip().lower()] = v.strip()
        body = raw[m.end():]
    return Document(path=path, meta=meta, body=body)


def write(
    path: Path,
    body: str,
    *,
    title: str,
    author: str = "",
    source: str = "",
    licence: str = "unknown",
    kind: str = "reference",
) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    front = (
        "---\n"
        f"title: {title}\n"
        f"author: {author}\n"
        f"source: {source}\n"
        f"licence: {licence}\n"
        f"kind: {kind}\n"
        f"added: {date.today().isoformat()}\n"
        "---\n"
    )
    path.write_text(front + normalise(body), encoding="utf-8")
    return path


def normalise(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = _WS.sub(" ", text)
    return _NL.sub("\n\n", text).strip() + "\n"


def walk(dirs: Iterable[Path] | None = None) -> Iterator[Document]:
    for d in dirs or (TOPICS_DIR, CORPUS_DIR):
        if not d.exists():
            continue
        for p in sorted(d.rglob("*.md")) + sorted(d.rglob("*.txt")):
            try:
                yield parse(p)
            except Exception:
                continue


def chunk(doc: Document, size: int | None = None, overlap: int | None = None) -> list[Chunk]:
    size = size or SETTINGS.chunk_chars
    overlap = overlap or SETTINGS.chunk_overlap
    text = doc.body.strip()
    if not text:
        return []

    # Prefer paragraph boundaries, fall back to hard slicing for walls of text.
    paras = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: list[str] = []
    buf = ""
    for p in paras:
        if len(p) > size:
            if buf:
                chunks.append(buf)
                buf = ""
            for i in range(0, len(p), size - overlap):
                chunks.append(p[i:i + size])
            continue
        if len(buf) + len(p) + 2 > size:
            chunks.append(buf)
            buf = buf[-overlap:] + "\n\n" + p if overlap else p
        else:
            buf = f"{buf}\n\n{p}" if buf else p
    if buf.strip():
        chunks.append(buf)

    return [
        Chunk(
            doc_id=doc.doc_id,
            ordinal=i,
            text=c.strip(),
            title=doc.title,
            author=doc.author,
            source=doc.source,
            kind=doc.kind,
            path=str(doc.path),
        )
        for i, c in enumerate(chunks)
        if c.strip()
    ]


def stats() -> dict[str, int]:
    docs = list(walk())
    return {
        "documents": len(docs),
        "characters": sum(len(d.body) for d in docs),
        "topics": sum(1 for d in docs if TOPICS_DIR in d.path.parents),
        "harvested": sum(1 for d in docs if CORPUS_DIR in d.path.parents),
    }
