"""Paths and runtime settings for Nicomachus."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

TOPICS_DIR = ROOT / "topics"      # curated seed knowledge (hand-written)
CORPUS_DIR = ROOT / "corpus"      # harvested open-licence texts
DATA_DIR = ROOT / "data"          # index, memory db, state
DOCS_DIR = ROOT / "docs"
LOG_DIR = DATA_DIR / "logs"

INDEX_PATH = DATA_DIR / "index.sqlite3"
LEGACY_INDEX_PATH = DATA_DIR / "index.json"
MEMORY_DB = DATA_DIR / "memory.sqlite3"
STATE_PATH = DATA_DIR / "state.json"
SETTINGS_PATH = DATA_DIR / "settings.json"

for _d in (TOPICS_DIR, CORPUS_DIR, DATA_DIR, DOCS_DIR, LOG_DIR):
    _d.mkdir(parents=True, exist_ok=True)


@dataclass
class Settings:
    """User-tunable settings, persisted to data/settings.json."""

    # Which provider powers synthesis: "auto" | "anthropic" | "gemini".
    # "auto" takes whichever has a credential, Anthropic first.
    provider: str = "auto"

    anthropic_model: str = "claude-opus-5"
    anthropic_fast_model: str = "claude-haiku-4-5"
    effort: str = "high"

    # gemini-3.7-flash is the current flagship Flash model; the lite variant is
    # the fastest and cheapest tier and is what distillation runs on.
    gemini_model: str = "gemini-3.7-flash"
    gemini_fast_model: str = "gemini-3.5-flash-lite"
    gemini_thinking: str = "low"      # low | high — low is markedly faster

    max_tokens: int = 16000
    research_max_tokens: int = 32000

    # Retrieval
    top_k: int = 8
    chunk_chars: int = 1400
    chunk_overlap: int = 200

    # Harvesting.
    # Wikimedia and NCBI both require a User-Agent that identifies the client
    # and gives a way to reach its operator. Put your own contact in
    # `contact` (data/settings.json) before running large harvests — several
    # APIs will rate-limit or block an anonymous agent, and it is the
    # courtesy their terms of use ask for.
    contact: str = ""
    user_agent_base: str = "Nicomachus/0.1 (open-source study assistant)"
    # Rate limiting is per-host, not global, so different sources are fetched
    # concurrently while each host still sees a polite serial stream.
    request_delay_seconds: float = 1.0
    max_bytes_per_doc: int = 8_000_000
    corpus_budget_gb: float = 20.0
    harvest_workers: int = 5

    # Self-study
    questions_per_cycle: int = 6
    harvest_per_cycle: int = 12

    # When retrieval comes back this weak, go and read the web unprompted
    # rather than answering thinly from whatever ranked highest.
    auto_research: bool = True
    research_threshold: float = 9.0

    allowed_domains: list[str] = field(default_factory=lambda: [
        "en.wikipedia.org",
        "en.wikisource.org",
        "www.gutenberg.org",
        "gutendex.com",
        "export.arxiv.org",
        "api.openalex.org",
        "eutils.ncbi.nlm.nih.gov",
        "www.ncbi.nlm.nih.gov",
        "archive.org",
        "doaj.org",
        "api.crossref.org",
        "psycnet-open.apa.org",
        "philpapers.org",
    ])

    @property
    def user_agent(self) -> str:
        if self.contact:
            return f"{self.user_agent_base} contact: {self.contact}"
        return self.user_agent_base

    def save(self) -> None:
        SETTINGS_PATH.write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")

    @classmethod
    def load(cls) -> "Settings":
        if SETTINGS_PATH.exists():
            try:
                raw = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
                known = {k: v for k, v in raw.items() if k in cls.__dataclass_fields__}
                return cls(**known)
            except Exception:
                pass
        s = cls()
        s.save()
        return s


SETTINGS = Settings.load()


def has_api_credentials() -> bool:
    """True if an Anthropic credential looks available in the environment."""
    if os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN"):
        return True
    # `ant auth login` writes a profile the SDK picks up with no env var set.
    prof = Path.home() / ".config" / "anthropic"
    return prof.exists() and any(prof.iterdir())
