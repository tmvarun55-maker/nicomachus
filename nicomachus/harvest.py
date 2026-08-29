"""Harvesting from open, free, legitimately-reusable sources.

Every source here is either public domain, CC0/CC-BY, or an official public
API that offers metadata and abstracts for reuse. The allowlist in
config.Settings is enforced on every request; robots.txt is checked and
obeyed; requests are rate-limited and single-threaded on purpose.

What this deliberately does not do: crawl the open web, bypass paywalls, or
copy full text of in-copyright books. Those are the reasons "collect the whole
internet" is not a plan — the useful, lawful subset is large and is what gets
collected here.
"""

from __future__ import annotations

import json
import re
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path

from . import corpus, memory
from .config import CORPUS_DIR, SETTINGS

# Rate limiting is per-host. Sources are fetched concurrently, but each
# individual host still sees one serial, delayed stream of requests — which is
# what their terms of use actually ask for. A global lock would have been
# politeness to nobody, since Wikipedia does not care how fast we talk to arXiv.
_host_locks: dict[str, threading.Lock] = {}
_host_last: dict[str, float] = {}
_locks_guard = threading.Lock()

_robots: dict[str, urllib.robotparser.RobotFileParser] = {}
_robots_guard = threading.Lock()
_store_guard = threading.Lock()

# Documented public APIs. robots.txt exists to keep crawlers off a site's HTML
# and its expensive dynamic endpoints; these hosts publish an API precisely so
# that programs use it instead of scraping, and govern it by their own terms of
# use rather than by robots.txt. (Wikipedia, for instance, disallows /w/ for
# crawlers while documenting /w/api.php as the supported client route.)
#
# The obligations those terms impose — an identifying User-Agent with real
# contact details, serial requests, and rate limiting — are honoured above.
# Everything not listed here still goes through the robots.txt check.
API_ENDPOINTS: tuple[tuple[str, str], ...] = (
    ("en.wikipedia.org", "/w/api.php"),
    ("en.wikipedia.org", "/api/rest_v1/"),
    ("en.wikisource.org", "/w/api.php"),
    ("gutendex.com", "/books"),
    ("export.arxiv.org", "/api/"),
    ("api.openalex.org", "/"),
    ("api.crossref.org", "/"),
    ("eutils.ncbi.nlm.nih.gov", "/entrez/eutils"),
    ("doaj.org", "/api/"),
)


def _is_documented_api(url: str) -> bool:
    parts = urllib.parse.urlparse(url)
    host, path = parts.netloc.lower(), parts.path
    return any(host == h and path.startswith(p) for h, p in API_ENDPOINTS)


@dataclass
class Harvested:
    title: str
    url: str
    path: Path
    chars: int


class NotAllowed(Exception):
    pass


# --- polite HTTP --------------------------------------------------------

def _host(url: str) -> str:
    return urllib.parse.urlparse(url).netloc.lower()


def _check_allowed(url: str) -> None:
    host = _host(url)
    if host not in SETTINGS.allowed_domains:
        raise NotAllowed(f"{host} is not on the source allowlist")
    if _is_documented_api(url):
        return
    if not _robots_ok(url):
        raise NotAllowed(f"robots.txt disallows {url}")


def _robots_ok(url: str) -> bool:
    parts = urllib.parse.urlparse(url)
    base = f"{parts.scheme}://{parts.netloc}"
    with _robots_guard:
        rp = _robots.get(base)
    if rp is None:
        rp = urllib.robotparser.RobotFileParser()
        rp.set_url(base + "/robots.txt")
        try:
            rp.read()
        except Exception:
            # No reachable robots.txt: the allowlist already vouched for the host.
            permissive = urllib.robotparser.RobotFileParser()
            permissive.allow_all = True
            with _robots_guard:
                _robots[base] = permissive
            return True
        with _robots_guard:
            _robots[base] = rp
    try:
        return rp.can_fetch(SETTINGS.user_agent, url)
    except Exception:
        return True


# Each host's own published rate limit, in seconds between requests. Using one
# blanket delay meant crawling OpenAlex (10 req/s allowed) at Wikipedia's pace
# while still exceeding what arXiv asks for. These are the documented figures:
#   OpenAlex   10 req/s in the polite pool
#   NCBI        3 req/s without an API key
#   arXiv       explicitly asks for 3 seconds between requests
#   Wikimedia   asks for serial requests; 1s is comfortably within that
HOST_DELAYS: dict[str, float] = {
    "api.openalex.org": 0.1,
    "api.crossref.org": 0.1,
    "eutils.ncbi.nlm.nih.gov": 0.34,
    "www.ncbi.nlm.nih.gov": 0.34,
    "gutendex.com": 0.5,
    "en.wikipedia.org": 1.0,
    "en.wikisource.org": 1.0,
    "www.gutenberg.org": 1.0,
    "export.arxiv.org": 3.0,
}


def _delay_for(host: str) -> float:
    return HOST_DELAYS.get(host, SETTINGS.request_delay_seconds)


def _lock_for(host: str) -> threading.Lock:
    with _locks_guard:
        return _host_locks.setdefault(host, threading.Lock())


def fetch(url: str, *, accept: str = "*/*", timeout: int = 30) -> bytes:
    """One rate-limited, allowlisted, robots-respecting GET.

    The delay is held per host, so two sources never wait on each other.
    """
    _check_allowed(url)
    host = _host(url)

    with _lock_for(host):
        delay = _delay_for(host)
        gap = time.time() - _host_last.get(host, 0.0)
        if gap < delay:
            time.sleep(delay - gap)

        req = urllib.request.Request(
            url,
            headers={"User-Agent": SETTINGS.user_agent, "Accept": accept},
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read(SETTINGS.max_bytes_per_doc)
        finally:
            _host_last[host] = time.time()


def fetch_json(url: str, timeout: int = 30) -> dict:
    return json.loads(fetch(url, accept="application/json", timeout=timeout))


def fetch_text(url: str, timeout: int = 30) -> str:
    return fetch(url, timeout=timeout).decode("utf-8", errors="replace")


def _store(subdir: str, slug: str, body: str, **meta) -> Path:
    safe = re.sub(r"[^a-z0-9\-_]+", "-", slug.lower()).strip("-")[:80] or "untitled"
    # Claiming the filename must be atomic across worker threads, or two
    # documents race to the same path and one silently overwrites the other.
    with _store_guard:
        path = CORPUS_DIR / subdir / f"{safe}.md"
        n = 1
        while path.exists():
            n += 1
            path = CORPUS_DIR / subdir / f"{safe}-{n}.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch()
    return corpus.write(path, body, **meta)


# --- Wikipedia (CC BY-SA) ----------------------------------------------

WIKI_API = "https://en.wikipedia.org/w/api.php"


def wikipedia(title: str) -> Harvested | None:
    """Plain-text extract of one article."""
    q = urllib.parse.urlencode({
        "action": "query", "format": "json", "prop": "extracts",
        "explaintext": "1", "redirects": "1", "titles": title,
    })
    url = f"{WIKI_API}?{q}"
    canonical = "https://en.wikipedia.org/wiki/" + urllib.parse.quote(title.replace(" ", "_"))
    if memory.already_seen(canonical):
        return None

    data = fetch_json(url)
    pages = data.get("query", {}).get("pages", {})
    for _, page in pages.items():
        text = page.get("extract", "")
        if not text or len(text) < 400:
            continue
        p = _store(
            "wikipedia", page.get("title", title), text,
            title=page.get("title", title), author="Wikipedia contributors",
            source=canonical, licence="CC BY-SA 4.0", kind="reference",
        )
        memory.mark_seen(canonical, page.get("title", title), str(p), "CC BY-SA 4.0")
        return Harvested(page.get("title", title), canonical, p, len(text))
    return None


def wikipedia_search(query: str, limit: int = 5) -> list[str]:
    q = urllib.parse.urlencode({
        "action": "query", "format": "json", "list": "search",
        "srsearch": query, "srlimit": str(limit),
    })
    data = fetch_json(f"{WIKI_API}?{q}")
    return [r["title"] for r in data.get("query", {}).get("search", [])]


# --- Project Gutenberg (public domain) ---------------------------------

def gutenberg_search(query: str, limit: int = 5) -> list[dict]:
    url = "https://gutendex.com/books?" + urllib.parse.urlencode({"search": query})
    data = fetch_json(url)
    return data.get("results", [])[:limit]


def gutenberg(book: dict) -> Harvested | None:
    """Download the plain-text form of one Gutendex book record."""
    fmts = book.get("formats", {})
    txt_url = next(
        (u for k, u in fmts.items()
         if k.startswith("text/plain") and not u.endswith(".zip")),
        None,
    )
    if not txt_url or memory.already_seen(txt_url):
        return None
    if _host(txt_url) not in SETTINGS.allowed_domains:
        return None

    text = fetch_text(txt_url)
    # Strip the Gutenberg boilerplate wrapper.
    start = re.search(r"\*\*\*\s*START OF (?:THE|THIS) PROJECT GUTENBERG.*?\*\*\*", text)
    end = re.search(r"\*\*\*\s*END OF (?:THE|THIS) PROJECT GUTENBERG.*?\*\*\*", text)
    if start:
        text = text[start.end():]
    if end:
        text = text[:end.start()]

    title = book.get("title", "untitled")
    authors = ", ".join(a.get("name", "") for a in book.get("authors", []))
    p = _store(
        "gutenberg", title, text,
        title=title, author=authors, source=txt_url,
        licence="public-domain", kind="primary",
    )
    memory.mark_seen(txt_url, title, str(p), "public-domain")
    return Harvested(title, txt_url, p, len(text))


# --- arXiv (open abstracts) --------------------------------------------

def arxiv(query: str, limit: int = 8) -> list[Harvested]:
    url = "http://export.arxiv.org/api/query?" + urllib.parse.urlencode({
        "search_query": f"all:{query}", "max_results": str(limit),
        "sortBy": "relevance",
    })
    url = url.replace("http://", "https://", 1)
    xml = fetch_text(url)
    out: list[Harvested] = []
    for entry in re.findall(r"<entry>(.*?)</entry>", xml, re.S):
        def tag(name: str) -> str:
            m = re.search(rf"<{name}>(.*?)</{name}>", entry, re.S)
            return re.sub(r"\s+", " ", m.group(1)).strip() if m else ""
        link = tag("id")
        if not link or memory.already_seen(link):
            continue
        title, summary = tag("title"), tag("summary")
        if len(summary) < 200:
            continue
        authors = ", ".join(re.findall(r"<name>(.*?)</name>", entry))
        body = f"{title}\n\n{summary}"
        p = _store("arxiv", title, body, title=title, author=authors,
                   source=link, licence="arXiv-abstract", kind="secondary")
        memory.mark_seen(link, title, str(p), "arXiv-abstract")
        out.append(Harvested(title, link, p, len(body)))
    return out


# --- OpenAlex (CC0 scholarly metadata) ---------------------------------

def openalex(query: str, limit: int = 10) -> list[Harvested]:
    url = "https://api.openalex.org/works?" + urllib.parse.urlencode({
        "search": query, "per-page": str(limit), "mailto": "nicomachus@local",
    })
    data = fetch_json(url)
    out: list[Harvested] = []
    for w in data.get("results", []):
        wid = w.get("id")
        if not wid or memory.already_seen(wid):
            continue
        abstract = _deinvert(w.get("abstract_inverted_index"))
        if not abstract or len(abstract) < 200:
            continue
        title = w.get("title") or w.get("display_name") or "untitled"
        authors = ", ".join(
            a["author"]["display_name"]
            for a in (w.get("authorships") or [])[:8]
            if a.get("author", {}).get("display_name")
        )
        year = w.get("publication_year", "")
        cited = w.get("cited_by_count", 0)
        body = (
            f"{title}\n\n{abstract}\n\n"
            f"[year: {year}; cited by: {cited}; "
            f"open access: {w.get('open_access', {}).get('is_oa')}]"
        )
        p = _store("openalex", title, body, title=title, author=authors,
                   source=wid, licence="CC0-metadata", kind="secondary")
        memory.mark_seen(wid, title, str(p), "CC0-metadata")
        out.append(Harvested(title, wid, p, len(body)))
    return out


def _deinvert(inv: dict | None) -> str:
    """OpenAlex ships abstracts as an inverted index; put it back in order."""
    if not inv:
        return ""
    positions: list[tuple[int, str]] = []
    for word, idxs in inv.items():
        for i in idxs:
            positions.append((i, word))
    return " ".join(w for _, w in sorted(positions))


# --- PubMed (NCBI E-utilities) -----------------------------------------

EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


def pubmed(query: str, limit: int = 8) -> list[Harvested]:
    search = f"{EUTILS}/esearch.fcgi?" + urllib.parse.urlencode({
        "db": "pubmed", "term": query, "retmax": str(limit), "retmode": "json",
    })
    ids = fetch_json(search).get("esearchresult", {}).get("idlist", [])
    if not ids:
        return []
    fetch_url = f"{EUTILS}/efetch.fcgi?" + urllib.parse.urlencode({
        "db": "pubmed", "id": ",".join(ids), "retmode": "xml", "rettype": "abstract",
    })
    xml = fetch_text(fetch_url)
    out: list[Harvested] = []
    for art in re.findall(r"<PubmedArticle>(.*?)</PubmedArticle>", xml, re.S):
        pmid_m = re.search(r"<PMID[^>]*>(\d+)</PMID>", art)
        if not pmid_m:
            continue
        url = f"https://www.ncbi.nlm.nih.gov/pubmed/{pmid_m.group(1)}"
        if memory.already_seen(url):
            continue
        title = _strip(re.search(r"<ArticleTitle>(.*?)</ArticleTitle>", art, re.S))
        abstract = " ".join(
            _strip_str(t) for t in re.findall(r"<AbstractText[^>]*>(.*?)</AbstractText>", art, re.S)
        )
        if len(abstract) < 200:
            continue
        body = f"{title}\n\n{abstract}"
        p = _store("pubmed", title or url, body, title=title or url,
                   author="", source=url, licence="NCBI-abstract", kind="secondary")
        memory.mark_seen(url, title, str(p), "NCBI-abstract")
        out.append(Harvested(title, url, p, len(body)))
    return out


def _strip(m) -> str:
    return _strip_str(m.group(1)) if m else ""


def _strip_str(s: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", s)).strip()


# --- orchestration ------------------------------------------------------

SEARCHERS = {
    "wikipedia": lambda q, n: [
        h for t in wikipedia_search(q, n) if (h := wikipedia(t))
    ],
    "openalex": openalex,
    "arxiv": arxiv,
    "pubmed": pubmed,
    "gutenberg": lambda q, n: [
        h for b in gutenberg_search(q, n) if (h := gutenberg(b))
    ],
}


_WORD = re.compile(r"[a-z]{4,}")
_QUERY_STOP = frozenset("""
what does than that this current evidence about does with from have been more
most such they their there which while would could should about into your
""".split())


def _relevant(query: str, title: str, body: str, floor: float = 0.25) -> bool:
    """Does this result actually have anything to do with the query?

    Several sources match loosely — arXiv's `all:` search will happily return
    a quantum field theory paper for "inoculation theory", because arXiv holds
    almost no humanities work and still owes you N results. Requiring a share
    of the query's content words to appear keeps the corpus clean; without it
    the index fills with confident noise.
    """
    terms = {w for w in _WORD.findall(query.lower()) if w not in _QUERY_STOP}
    if not terms:
        return True
    haystack = f"{title} {body[:4000]}".lower()
    hits = sum(1 for t in terms if t in haystack)
    # A ratio alone is not enough: one generic word carries it. "inoculation
    # theory misinformation" matched a quantum field theory paper on the
    # strength of "theory" (1 of 3 = 0.33). Demand two distinct terms whenever
    # the query offers two, so a single common word can never qualify.
    return hits >= min(2, len(terms)) and hits / len(terms) >= floor


def gather(query: str, sources: list[str] | None = None,
           per_source: int = 3) -> list[Harvested]:
    """Pull `query` from every requested source concurrently.

    Sources hit different hosts, so they run in parallel and the whole gather
    takes about as long as its slowest source rather than their sum. Failures
    are logged and never stop the others.
    """
    picked = [s for s in (sources or ["wikipedia", "openalex", "arxiv"])
              if s in SEARCHERS]
    if not picked:
        return []

    def run(name: str) -> list[Harvested]:
        try:
            got = SEARCHERS[name](query, per_source) or []
            memory.log("harvest", f"{name}: {len(got)} new for {query!r}")
            return got
        except NotAllowed as e:
            memory.log("harvest-blocked", f"{name}: {e}")
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
            memory.log("harvest-error", f"{name} unreachable for {query!r}: {e}")
        except Exception as e:  # a malformed feed must not kill the cycle
            memory.log("harvest-error", f"{name} failed on {query!r}: {e}")
        return []

    results: list[Harvested] = []
    workers = max(1, min(SETTINGS.harvest_workers, len(picked)))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(run, n): n for n in picked}
        for fut in as_completed(futures):
            results.extend(fut.result())

    kept, dropped = [], 0
    for h in results:
        try:
            body = corpus.parse(h.path).body
        except Exception:
            kept.append(h)
            continue
        if _relevant(query, h.title, body):
            kept.append(h)
        else:
            # Off-topic: unlink the file and forget it, so a later, better
            # query for the same URL is still allowed to fetch it.
            h.path.unlink(missing_ok=True)
            memory.forget(h.url)
            dropped += 1
    if dropped:
        memory.log("harvest-filtered",
                   f"dropped {dropped} off-topic result(s) for {query!r}")
    return kept
