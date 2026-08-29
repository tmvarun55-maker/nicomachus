"""A local web interface for Nicomachus.

Standard library only — `http.server` with a thread pool, a small JSON API and
a single-page front end. Nothing to install, nothing to build, no framework.

Long operations (asking, studying, harvesting, live research) run as jobs: the
POST returns an id immediately and the page polls it, so a sixty-second model
call never blocks the interface or trips a request timeout.

Binds to 127.0.0.1 by default. The corpus, the notes and the model credential
are all on this machine; nothing here is meant to face a network.
"""

from __future__ import annotations

import json
import mimetypes
import threading
import traceback
import uuid
import webbrowser
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from . import brain, corpus, harvest, memory, policy, providers, study
from .config import CORPUS_DIR, SETTINGS, TOPICS_DIR
from .index import Index, rebuild

STATIC = Path(__file__).parent / "static"

_pool = ThreadPoolExecutor(max_workers=4)
_jobs: dict[str, dict] = {}
_jobs_lock = threading.Lock()

# One shared index handle would be simpler, but SQLite connections belong to
# the thread that made them, so each worker opens its own.
_local = threading.local()


def _index() -> Index:
    if getattr(_local, "index", None) is None:
        _local.index = Index.load()
    return _local.index


# --- jobs ---------------------------------------------------------------

def start_job(kind: str, fn, *args, **kwargs) -> str:
    job_id = uuid.uuid4().hex[:12]
    with _jobs_lock:
        _jobs[job_id] = {"id": job_id, "kind": kind, "state": "running",
                         "result": None, "error": None}

    def run():
        try:
            result = fn(*args, **kwargs)
            with _jobs_lock:
                _jobs[job_id].update(state="done", result=result)
        except Exception as e:
            with _jobs_lock:
                _jobs[job_id].update(state="error", error=str(e))
            memory.log("web-error", f"{kind} failed: {e}", traceback.format_exc())

    _pool.submit(run)
    return job_id


def job_state(job_id: str) -> dict | None:
    with _jobs_lock:
        job = _jobs.get(job_id)
        return dict(job) if job else None


# --- job bodies ---------------------------------------------------------

def _do_ask(question: str) -> dict:
    a = brain.answer(question, _index())
    return {
        "text": a.text,
        "citations": a.citations,
        "stance": a.stance.value,
        "offline": a.offline,
        "provider": a.provider,
        "model": a.model,
        "usage": a.usage,
    }


def _do_research(topic: str) -> dict:
    a = brain.research(topic)
    return {"text": a.text, "citations": a.citations, "offline": a.offline,
            "provider": a.provider, "model": a.model}


def _do_learn(topic: str, sources: list[str] | None, per_source: int) -> dict:
    got = harvest.gather(topic, sources=sources, per_source=per_source)
    ix = rebuild(verbose=False)
    _local.index = None
    return {
        "harvested": [{"title": h.title, "url": h.url, "chars": h.chars} for h in got],
        "chunks": len(ix),
        "documents": corpus.stats()["documents"],
    }


def _do_reflect() -> dict:
    return brain.reflect()


def _do_autonomous(rounds: int, per_source: int) -> dict:
    reports = study.autonomous(rounds=rounds, per_source=per_source,
                               verbose=False)
    return {
        "rounds": len(reports),
        "harvested": sum(r.harvested for r in reports),
        "notes": sum(r.notes for r in reports),
        "questions": sum(r.new_questions for r in reports),
        "reflection": brain.reflect(),
    }


def _do_study(topics: list[str], per_source: int) -> dict:
    rep = study.cycle(targets=topics or None, per_source=per_source, verbose=False)
    _local.index = None
    return {
        "targets": rep.targets,
        "harvested": rep.harvested,
        "notes": rep.notes,
        "questions": rep.new_questions,
        "indexed": rep.indexed,
        "errors": rep.errors,
    }


# --- read-only API ------------------------------------------------------

def api_status() -> dict:
    s = corpus.stats()
    p = brain.current()
    return {
        "corpus": s,
        "chunks": len(_index()),
        "seen": memory.seen_count(),
        "notes": memory.note_count(),
        "questions": memory.question_stats(),
        "provider": p.name if p else None,
        "providers": [
            {"name": n, "available": a, "model": q, "fast": f}
            for n, a, q, f in providers.roster()
        ],
        "preference": SETTINGS.provider,
        "journal": [dict(r) for r in memory.journal(12)],
    }


def api_questions() -> dict:
    return {"questions": [dict(r) for r in memory.open_questions(50)]}


def api_notes(topic: str = "") -> dict:
    rows = memory.notes_for(topic, 100) if topic else memory.recent_notes(100)
    return {"notes": [dict(r) for r in rows]}


def api_search(q: str, k: int = 10) -> dict:
    hits = _index().search(q, k)
    return {"hits": [
        {"score": round(s, 2), "title": c["title"], "author": c.get("author", ""),
         "source": c.get("source", ""), "kind": c.get("kind", ""),
         "path": c.get("path", ""), "text": c["text"]}
        for s, c in hits
    ]}


def api_library() -> dict:
    docs = []
    for d in corpus.walk():
        docs.append({
            "title": d.title,
            "author": d.author,
            "source": d.source,
            "kind": d.kind,
            "licence": d.meta.get("licence", ""),
            "chars": len(d.body),
            "path": str(d.path),
            "curated": TOPICS_DIR in d.path.parents,
        })
    docs.sort(key=lambda x: (not x["curated"], x["title"].lower()))
    return {"documents": docs}


def api_document(path: str) -> dict:
    p = Path(path).resolve()
    # Only ever serve files from inside the corpus. Without this check the
    # `path` parameter is an arbitrary file read.
    roots = [TOPICS_DIR.resolve(), CORPUS_DIR.resolve()]
    if not any(r == p or r in p.parents for r in roots):
        raise PermissionError("outside the corpus")
    doc = corpus.parse(p)
    return {"title": doc.title, "author": doc.author, "source": doc.source,
            "kind": doc.kind, "licence": doc.meta.get("licence", ""),
            "body": doc.body}


def api_check(question: str) -> dict:
    v = policy.assess(question)
    return {"stance": v.stance.value, "reason": v.reason, "note": v.note}


# --- HTTP ---------------------------------------------------------------

class Handler(BaseHTTPRequestHandler):
    server_version = "Nicomachus"

    def log_message(self, fmt, *args):  # quiet by default
        if self.server.verbose:  # type: ignore[attr-defined]
            super().log_message(fmt, *args)

    # -- helpers --
    def _send(self, code: int, body: bytes, ctype: str):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionAbortedError):
            pass

    def _json(self, data, code: int = 200):
        self._send(code, json.dumps(data).encode("utf-8"),
                   "application/json; charset=utf-8")

    def _body(self) -> dict:
        n = int(self.headers.get("Content-Length") or 0)
        if not n:
            return {}
        try:
            return json.loads(self.rfile.read(n).decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return {}

    def _static(self, name: str):
        path = (STATIC / name).resolve()
        if STATIC.resolve() not in path.parents or not path.is_file():
            return self._send(404, b"not found", "text/plain")
        ctype = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        if ctype.startswith("text/") or ctype == "application/javascript":
            ctype += "; charset=utf-8"
        self._send(200, path.read_bytes(), ctype)

    # -- routes --
    def do_GET(self):
        u = urlparse(self.path)
        q = parse_qs(u.query)
        route = u.path

        try:
            if route in ("/", "/index.html"):
                return self._static("index.html")
            if route.startswith("/static/"):
                return self._static(route[len("/static/"):])

            if route == "/api/status":
                return self._json(api_status())
            if route == "/api/questions":
                return self._json(api_questions())
            if route == "/api/notes":
                return self._json(api_notes(q.get("topic", [""])[0]))
            if route == "/api/search":
                return self._json(api_search(q.get("q", [""])[0],
                                             int(q.get("k", ["10"])[0])))
            if route == "/api/library":
                return self._json(api_library())
            if route == "/api/document":
                return self._json(api_document(unquote(q.get("path", [""])[0])))
            if route == "/api/charter":
                return self._json({"charter": policy.CHARTER})
            if route.startswith("/api/job/"):
                job = job_state(route.rsplit("/", 1)[-1])
                return self._json(job or {"error": "unknown job"},
                                  200 if job else 404)
            return self._send(404, b"not found", "text/plain")

        except PermissionError as e:
            return self._json({"error": str(e)}, 403)
        except Exception as e:
            memory.log("web-error", f"GET {route}: {e}", traceback.format_exc())
            return self._json({"error": str(e)}, 500)

    def do_POST(self):
        route = urlparse(self.path).path
        body = self._body()
        try:
            if route == "/api/ask":
                question = (body.get("question") or "").strip()
                if not question:
                    return self._json({"error": "empty question"}, 400)
                return self._json({"job": start_job("ask", _do_ask, question)})

            if route == "/api/research":
                topic = (body.get("topic") or "").strip()
                if not topic:
                    return self._json({"error": "empty topic"}, 400)
                return self._json({"job": start_job("research", _do_research, topic)})

            if route == "/api/learn":
                topic = (body.get("topic") or "").strip()
                if not topic:
                    return self._json({"error": "empty topic"}, 400)
                return self._json({"job": start_job(
                    "learn", _do_learn, topic,
                    body.get("sources") or None,
                    int(body.get("per_source") or 3))})

            if route == "/api/study":
                return self._json({"job": start_job(
                    "study", _do_study,
                    body.get("topics") or [],
                    int(body.get("per_source") or 3))})

            if route == "/api/reflect":
                return self._json({"job": start_job("reflect", _do_reflect)})

            if route == "/api/autonomous":
                return self._json({"job": start_job(
                    "autonomous", _do_autonomous,
                    int(body.get("rounds") or 2),
                    int(body.get("per_source") or 3))})

            if route == "/api/check":
                return self._json(api_check(body.get("question", "")))

            if route == "/api/provider":
                name = body.get("provider", "auto")
                if name not in ("auto", "anthropic", "gemini"):
                    return self._json({"error": "unknown provider"}, 400)
                SETTINGS.provider = name
                SETTINGS.save()
                return self._json({"ok": True, "preference": name})

            return self._send(404, b"not found", "text/plain")

        except Exception as e:
            memory.log("web-error", f"POST {route}: {e}", traceback.format_exc())
            return self._json({"error": str(e)}, 500)


def serve(host: str = "127.0.0.1", port: int = 8422, open_browser: bool = True,
          verbose: bool = False) -> None:
    httpd = ThreadingHTTPServer((host, port), Handler)
    httpd.verbose = verbose  # type: ignore[attr-defined]
    url = f"http://{host}:{port}/"

    print(f"  Nicomachus is at {url}")
    p = brain.current()
    print(f"  provider: {p.name if p else 'none — offline mode'}")
    print("  Ctrl-C to stop.\n")

    if open_browser:
        threading.Timer(0.5, lambda: webbrowser.open(url)).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n  stopped.")
    finally:
        httpd.server_close()
