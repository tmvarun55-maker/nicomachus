"""Command line for Nicomachus."""

from __future__ import annotations

import argparse
import sys
import textwrap

from . import brain, corpus, harvest, memory, policy, providers, study
from .config import CORPUS_DIR, DATA_DIR, SETTINGS, TOPICS_DIR
from .index import Index, rebuild

# Windows consoles default to cp1252 and choke on the corpus (Greek, quotes,
# em-dashes). Force UTF-8 and never let an encoding error swallow an answer.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

BANNER = r"""
  +-+ NICOMACHUS
  +-+ philosophy · psychology · political theory · rhetoric
      a study instrument, not an instrument of persuasion
"""


def _wrap(text: str, width: int = 88) -> str:
    """Reflow prose paragraphs; leave lists, tables and indented blocks alone."""
    out: list[str] = []
    para: list[str] = []

    def flush() -> None:
        if para:
            out.append(textwrap.fill(" ".join(para), width))
            para.clear()

    for line in text.split("\n"):
        stripped = line.strip()
        structural = (
            not stripped
            or line[:1] in " \t"
            or stripped[0] in "·-*|>#["
            or stripped[:2].rstrip(".").isdigit()
        )
        if structural:
            flush()
            out.append(line)
        else:
            para.append(stripped)
    flush()
    return "\n".join(out)


# --- commands -----------------------------------------------------------

def cmd_ask(args) -> int:
    ix = Index.load()
    if not len(ix):
        print("The index is empty. Run `nicomachus index` first.\n")
    a = brain.answer(args.question, ix)
    print()
    print(_wrap(a.text))
    if a.citations and not a.offline:
        print("\nSources")
        for c in a.citations:
            src = f"  {c['source']}" if c["source"] else ""
            author = f" — {c['author']}" if c["author"] else ""
            print(f"  [{c['n']}] {c['title']}{author}{src}")
    if a.usage:
        print(f"\n  {a.provider}/{a.model} · "
              f"{a.usage.get('input', 0)} in / {a.usage.get('output', 0)} out tokens")
    return 0


def cmd_research(args) -> int:
    print(f"Researching: {args.topic}\n  (live web search through the model)\n")
    a = brain.research(args.topic)
    print(_wrap(a.text))
    if a.citations:
        print("\nFetched")
        for c in a.citations[:25]:
            print(f"  · {c['source']}")
    return 0


def cmd_learn(args) -> int:
    print(f"Harvesting open sources for: {args.topic}\n")
    got = harvest.gather(args.topic, sources=args.sources, per_source=args.per_source)
    for h in got:
        print(f"  + {h.title[:70]:<70} {h.chars:>8,} chars")
    print(f"\n{len(got)} new document(s). Reindexing...")
    ix = rebuild(verbose=False)
    print(f"Index: {len(ix)} chunks from {corpus.stats()['documents']} documents.")
    return 0


def cmd_study(args) -> int:
    print("Running study cycle...\n")
    rep = study.cycle(targets=args.topics or None, per_source=args.per_source)
    print()
    print(rep.render())
    return 0


def cmd_index(args) -> int:
    print("Rebuilding index...")
    ix = rebuild(verbose=args.verbose)
    s = corpus.stats()
    print(f"\n{len(ix)} chunks from {s['documents']} documents "
          f"({s['characters']:,} characters).")
    print(f"  {s['topics']} curated topic notes")
    print(f"  {s['harvested']} harvested documents")
    return 0


def cmd_status(args) -> int:
    print(BANNER)
    s = corpus.stats()
    ix = Index.load()
    qs = memory.question_stats()
    print(f"  corpus       {s['documents']} documents, {s['characters']:,} chars")
    print(f"               {s['topics']} curated · {s['harvested']} harvested")
    print(f"  index        {len(ix)} chunks")
    print(f"  sources seen {memory.seen_count()}")
    print(f"  notes        {memory.note_count()}")
    print(f"  questions    {qs.get('open', 0)} open · "
          f"{qs.get('studying', 0)} studying · {qs.get('answered', 0)} answered")
    p = brain.current()
    if p is None:
        print("  provider     none — offline mode "
              "(set ANTHROPIC_API_KEY or GEMINI_API_KEY)")
    else:
        quality, fast = _models_for(p.name)
        print(f"  provider     {p.name} · {quality} (fast: {fast})")
    print(f"  data         {DATA_DIR}")
    print()
    recent = memory.journal(6)
    if recent:
        print("  recent")
        for r in recent:
            print(f"    {r['at'][:16]}  {r['kind']:<16} {r['summary'][:60]}")
    return 0


def cmd_reflect(args) -> int:
    print("Reflecting on what it has read...\n")
    r = brain.reflect()
    if r.get("offline"):
        print("Needs an API key — set ANTHROPIC_API_KEY or GEMINI_API_KEY.")
        return 1
    if r.get("standing"):
        print("Standing view")
        print(_wrap("  " + r["standing"], 86), "\n")
    if r.get("protective"):
        print("Worth knowing, to not be worked on")
        for p in r["protective"]:
            print(_wrap("  · " + p, 86))
        print()
    if r.get("revise"):
        print("Revising")
        for v in r["revise"]:
            print(_wrap("  · " + v, 86))
        print()
    if r.get("next"):
        print("Reading next")
        for n in r["next"]:
            print(_wrap("  · " + n, 86))
    return 0


def cmd_autonomous(args) -> int:
    print(f"Studying on its own for {args.rounds} round(s)...\n")
    study.autonomous(rounds=args.rounds, per_source=args.per_source)
    return 0


def cmd_serve(args) -> int:
    from .web import serve
    print(BANNER)
    serve(host=args.host, port=args.port,
          open_browser=not args.no_open and not args.host, verbose=args.verbose)
    return 0


def _models_for(name: str) -> tuple[str, str]:
    for n, _avail, quality, fast in providers.roster():
        if n == name:
            return quality, fast
    return "?", "?"


def cmd_providers(args) -> int:
    if args.use:
        SETTINGS.provider = args.use
        SETTINGS.save()
        print(f"Provider preference set to {args.use!r}.\n")

    print(f"  preference: {SETTINGS.provider}\n")
    for name, avail, quality, fast in providers.roster():
        mark = "✓" if avail else "·"
        state = "credential found" if avail else "no credential"
        print(f"  {mark} {name:<10} {state}")
        print(f"      quality  {quality}")
        print(f"      fast     {fast}")
    active = brain.current()
    print(f"\n  active: {active.name if active else 'none (offline mode)'}")
    if not any(a for _, a, _, _ in providers.roster()):
        print("\n  Set one of:")
        print('    setx ANTHROPIC_API_KEY "sk-ant-..."')
        print('    setx GEMINI_API_KEY "..."')
    return 0


def cmd_questions(args) -> int:
    qs = memory.open_questions(args.limit)
    if not qs:
        print("No open questions. Run `nicomachus seed` or `nicomachus study`.")
        return 0
    print("Open questions Nicomachus has set itself:\n")
    for q in qs:
        print(f"  [{q['id']:>4}] {q['question']}")
        if q["topic"]:
            print(f"         from: {q['topic']}")
    return 0


def cmd_notes(args) -> int:
    rows = memory.notes_for(args.topic, args.limit) if args.topic \
        else memory.recent_notes(args.limit)
    if not rows:
        print("No notes yet. Run `nicomachus study`.")
        return 0
    for r in rows:
        print(f"\n  · [{r['confidence']}] {r['topic']}")
        print(_wrap("    " + r["claim"], 86))
        if r["provenance"]:
            print(f"    ← {r['provenance'][:100]}")
    return 0


def cmd_seed(args) -> int:
    n = study.seed_questions()
    print(f"Seeded {n} opening questions from the curriculum.")
    print("Run `nicomachus study` to start working through them.")
    return 0


def cmd_charter(args) -> int:
    print(policy.CHARTER)
    return 0


def cmd_check(args) -> int:
    v = policy.assess(args.question)
    print(f"  stance : {v.stance.value}")
    print(f"  reason : {v.reason}")
    if v.note:
        print(f"  note   : {v.note}")
    return 0


def cmd_chat(args) -> int:
    print(BANNER)
    print("  Ask anything. Ctrl-C or 'exit' to leave.\n")
    ix = Index.load()
    while True:
        try:
            q = input("  » ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n  Farewell.")
            return 0
        if q.lower() in {"exit", "quit", ":q"}:
            return 0
        if not q:
            continue
        a = brain.answer(q, ix)
        print()
        print(_wrap(a.text))
        print()


# --- parser -------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="nicomachus",
        description="A study assistant for philosophy, psychology, "
                    "political theory and rhetoric.",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("ask", help="ask a question against the corpus")
    a.add_argument("question")
    a.set_defaults(fn=cmd_ask)

    r = sub.add_parser("research", help="live web research on a topic (needs API)")
    r.add_argument("topic")
    r.set_defaults(fn=cmd_research)

    l = sub.add_parser("learn", help="harvest open sources on a topic")
    l.add_argument("topic")
    l.add_argument("--sources", nargs="*",
                   choices=list(harvest.SEARCHERS), default=None)
    l.add_argument("--per-source", type=int, default=3)
    l.set_defaults(fn=cmd_learn)

    s = sub.add_parser("study", help="run a self-directed study cycle")
    s.add_argument("topics", nargs="*")
    s.add_argument("--per-source", type=int, default=3)
    s.set_defaults(fn=cmd_study)

    i = sub.add_parser("index", help="rebuild the search index")
    i.add_argument("-v", "--verbose", action="store_true")
    i.set_defaults(fn=cmd_index)

    st = sub.add_parser("status", help="what it knows and has been doing")
    st.set_defaults(fn=cmd_status)

    q = sub.add_parser("questions", help="its own open questions")
    q.add_argument("--limit", type=int, default=20)
    q.set_defaults(fn=cmd_questions)

    n = sub.add_parser("notes", help="claims it has written down")
    n.add_argument("topic", nargs="?", default="")
    n.add_argument("--limit", type=int, default=20)
    n.set_defaults(fn=cmd_notes)

    sd = sub.add_parser("seed", help="prime the question queue")
    sd.set_defaults(fn=cmd_seed)

    c = sub.add_parser("charter", help="print the study charter")
    c.set_defaults(fn=cmd_charter)

    ck = sub.add_parser("check", help="show how the charter reads a question")
    ck.add_argument("question")
    ck.set_defaults(fn=cmd_check)

    ch = sub.add_parser("chat", help="interactive session")
    ch.set_defaults(fn=cmd_chat)

    rf = sub.add_parser("reflect", help="think over what it has read")
    rf.set_defaults(fn=cmd_reflect)

    au = sub.add_parser("autonomous", help="study unattended, then reflect")
    au.add_argument("--rounds", type=int, default=3)
    au.add_argument("--per-source", type=int, default=3)
    au.set_defaults(fn=cmd_autonomous)

    sv = sub.add_parser("serve", help="open the web interface")
    sv.add_argument("--port", type=int, default=None,
                    help="default 8422, or $PORT")
    sv.add_argument("--host", default=None,
                    help="default 127.0.0.1; 0.0.0.0 needs NICOMACHUS_TOKEN")
    sv.add_argument("--no-open", action="store_true",
                    help="don't launch a browser")
    sv.add_argument("-v", "--verbose", action="store_true",
                    help="log every request")
    sv.set_defaults(fn=cmd_serve)

    pr = sub.add_parser("providers", help="show or choose the model provider")
    pr.add_argument("--use", choices=["auto", "anthropic", "gemini"],
                    help="set the provider preference and save it")
    pr.set_defaults(fn=cmd_providers)

    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.fn(args)
    except KeyboardInterrupt:
        print("\ninterrupted")
        return 130


if __name__ == "__main__":
    sys.exit(main())
