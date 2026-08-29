"""Model providers: Anthropic and Google Gemini, behind one interface.

Each provider exposes three calls:

    complete()  — grounded answering, the quality tier
    fast()      — the cheap/quick tier, for distillation and classification
    research()  — answering with live web grounding, returning source URLs

Selection order: whatever `settings.provider` names, else whichever has a
credential, else offline. Both credentials present means you get the one you
configured, defaulting to Anthropic.
"""

from __future__ import annotations

import importlib.util
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path

from .config import SETTINGS


def _installed(module: str) -> bool:
    """Is the package importable, without paying to import it?

    `import anthropic` costs ~3s and `google.genai` ~0.6s. Every command asks
    which providers are available, so importing them to find out made the CLI
    feel broken. find_spec locates the module without executing it; the real
    import happens lazily on the first call that needs the client.
    """
    try:
        return importlib.util.find_spec(module) is not None
    except (ImportError, ValueError):
        return False


@dataclass
class Reply:
    text: str
    provider: str = ""
    model: str = ""
    sources: list[str] = field(default_factory=list)
    usage: dict[str, int] = field(default_factory=dict)


class Provider(ABC):
    name: str = ""

    @abstractmethod
    def available(self) -> bool: ...

    @abstractmethod
    def complete(self, system: str, prompt: str, *, max_tokens: int,
                 json_mode: bool = False) -> Reply: ...

    @abstractmethod
    def fast(self, system: str, prompt: str, *, max_tokens: int,
             json_mode: bool = False) -> Reply: ...

    @abstractmethod
    def research(self, system: str, prompt: str, *, max_tokens: int) -> Reply: ...


# --- Anthropic ----------------------------------------------------------

class AnthropicProvider(Provider):
    name = "anthropic"

    def __init__(self) -> None:
        self._client = None

    def available(self) -> bool:
        if not _installed("anthropic"):
            return False
        if os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN"):
            return True
        prof = Path.home() / ".config" / "anthropic"
        return prof.exists() and any(prof.iterdir())

    @property
    def client(self):
        if self._client is None:
            import anthropic
            self._client = anthropic.Anthropic()
        return self._client

    def _call(self, system: str, prompt: str, *, model: str, max_tokens: int,
              effort: str, tools: list | None = None) -> Reply:
        kwargs = {
            "model": model,
            "max_tokens": max_tokens,
            "system": [{"type": "text", "text": system,
                        "cache_control": {"type": "ephemeral"}}],
            "thinking": {"type": "adaptive"},
            "output_config": {"effort": effort},
            "messages": [{"role": "user", "content": prompt}],
        }
        if tools:
            kwargs["tools"] = tools

        with self.client.messages.stream(**kwargs) as stream:
            msg = stream.get_final_message()

        return Reply(
            text="".join(b.text for b in msg.content if b.type == "text"),
            provider=self.name,
            model=model,
            sources=_anthropic_sources(msg),
            usage={"input": msg.usage.input_tokens,
                   "output": msg.usage.output_tokens},
        )

    def complete(self, system, prompt, *, max_tokens, json_mode=False) -> Reply:
        return self._call(system, prompt, model=SETTINGS.anthropic_model,
                          max_tokens=max_tokens, effort=SETTINGS.effort)

    def fast(self, system, prompt, *, max_tokens, json_mode=False) -> Reply:
        return self._call(system, prompt, model=SETTINGS.anthropic_fast_model,
                          max_tokens=max_tokens, effort="low")

    def research(self, system, prompt, *, max_tokens) -> Reply:
        tools = [
            {"type": "web_search_20260209", "name": "web_search", "max_uses": 8},
            {"type": "web_fetch_20260209", "name": "web_fetch", "max_uses": 8,
             "citations": {"enabled": True}, "max_content_tokens": 60000},
        ]
        return self._call(system, prompt, model=SETTINGS.anthropic_model,
                          max_tokens=max_tokens, effort=SETTINGS.effort,
                          tools=tools)


def _anthropic_sources(msg) -> list[str]:
    urls: list[str] = []

    def add(u):
        if u and u not in urls:
            urls.append(u)

    for block in msg.content:
        t = getattr(block, "type", "")
        if t == "web_search_tool_result":
            content = getattr(block, "content", None)
            if isinstance(content, list):
                for r in content:
                    add(getattr(r, "url", None))
        elif t == "web_fetch_tool_result":
            add(getattr(getattr(block, "content", None), "url", None))
        elif t == "text":
            for c in (getattr(block, "citations", None) or []):
                add(getattr(c, "url", None))
    return urls


# --- Google Gemini ------------------------------------------------------

class GeminiProvider(Provider):
    name = "gemini"

    def __init__(self) -> None:
        self._client = None

    def available(self) -> bool:
        if not _installed("google.genai"):
            return False
        return bool(os.environ.get("GEMINI_API_KEY")
                    or os.environ.get("GOOGLE_API_KEY"))

    @property
    def client(self):
        if self._client is None:
            from google import genai
            key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
            self._client = genai.Client(api_key=key)
        return self._client

    def _call(self, system: str, prompt: str, *, model: str, max_tokens: int,
              thinking_level: str | None, search: bool = False,
              json_mode: bool = False) -> Reply:
        from google.genai import types

        def build(with_thinking: bool):
            cfg: dict = {
                "system_instruction": system,
                "max_output_tokens": max_tokens,
            }
            if search:
                cfg["tools"] = [types.Tool(google_search=types.GoogleSearch())]
            elif json_mode:
                # Search grounding and forced JSON are mutually exclusive.
                cfg["response_mime_type"] = "application/json"
            if with_thinking and thinking_level:
                cfg["thinking_config"] = types.ThinkingConfig(
                    thinking_level=thinking_level
                )
            return types.GenerateContentConfig(**cfg)

        try:
            resp = self.client.models.generate_content(
                model=model, contents=prompt, config=build(True)
            )
        except Exception as e:
            # Not every model accepts an explicit thinking level; the request is
            # still perfectly valid without one, so retry rather than fail.
            if thinking_level and "thinking" in str(e).lower():
                resp = self.client.models.generate_content(
                    model=model, contents=prompt, config=build(False)
                )
            else:
                raise

        usage = {}
        if getattr(resp, "usage_metadata", None):
            usage = {
                "input": resp.usage_metadata.prompt_token_count or 0,
                "output": resp.usage_metadata.candidates_token_count or 0,
            }

        return Reply(
            text=resp.text or "",
            provider=self.name,
            model=model,
            sources=_gemini_sources(resp),
            usage=usage,
        )

    def complete(self, system, prompt, *, max_tokens, json_mode=False) -> Reply:
        return self._call(system, prompt, model=SETTINGS.gemini_model,
                          max_tokens=max_tokens,
                          thinking_level=SETTINGS.gemini_thinking,
                          json_mode=json_mode)

    def fast(self, system, prompt, *, max_tokens, json_mode=False) -> Reply:
        return self._call(system, prompt, model=SETTINGS.gemini_fast_model,
                          max_tokens=max_tokens, thinking_level="low",
                          json_mode=json_mode)

    def research(self, system, prompt, *, max_tokens) -> Reply:
        return self._call(system, prompt, model=SETTINGS.gemini_model,
                          max_tokens=max_tokens,
                          thinking_level=SETTINGS.gemini_thinking, search=True)


def _gemini_sources(resp) -> list[str]:
    urls: list[str] = []
    for cand in (getattr(resp, "candidates", None) or []):
        meta = getattr(cand, "grounding_metadata", None)
        for chunk in (getattr(meta, "grounding_chunks", None) or []):
            uri = getattr(getattr(chunk, "web", None), "uri", None)
            if uri and uri not in urls:
                urls.append(uri)
    return urls


# --- selection ----------------------------------------------------------

_REGISTRY: dict[str, type[Provider]] = {
    "anthropic": AnthropicProvider,
    "gemini": GeminiProvider,
}

_cache: dict[str, Provider] = {}


def get(name: str) -> Provider:
    if name not in _cache:
        cls = _REGISTRY.get(name)
        if cls is None:
            raise ValueError(f"unknown provider {name!r}; "
                             f"choose from {', '.join(_REGISTRY)}")
        _cache[name] = cls()
    return _cache[name]


def select(preference: str | None = None) -> Provider | None:
    """The provider to use, or None if nothing has a credential."""
    want = preference or SETTINGS.provider
    if want and want != "auto":
        p = get(want)
        return p if p.available() else None
    for name in ("anthropic", "gemini"):
        p = get(name)
        if p.available():
            return p
    return None


def roster() -> list[tuple[str, bool, str, str]]:
    """(name, available, quality model, fast model) for every provider."""
    return [
        ("anthropic", get("anthropic").available(),
         SETTINGS.anthropic_model, SETTINGS.anthropic_fast_model),
        ("gemini", get("gemini").available(),
         SETTINGS.gemini_model, SETTINGS.gemini_fast_model),
    ]
