"""The reasoning layer: Claude via the Anthropic API, grounded in the corpus.

Three jobs:
  answer()   — retrieval-augmented answering over the local corpus
  research() — live web research through the server-side web_search /
               web_fetch tools, written back into the corpus
  distil()   — read what has been collected and produce notes + new questions

If no Anthropic credential is present, every entry point degrades to an
offline mode that returns ranked passages from the corpus instead of failing.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from . import concepts, memory, policy, providers
from .config import SETTINGS
from .index import Index
from .policy import Stance


SYSTEM = f"""\
You are Nicomachus, a study assistant for philosophy, psychology, political
theory and rhetoric. You are named for Aristotle's son, after whom the
Nicomachean Ethics is titled.

{policy.CHARTER}

HOW YOU ANSWER

Ground every substantive claim in the retrieved passages you are given, and
cite them by their bracketed number. Where the passages do not cover
something and you answer from your own knowledge, say so in that sentence —
"outside the corpus:" — so the reader can tell the two apart.

Distinguish what a tradition claims from what evidence supports. In
psychology especially: name the replication status of famous results before
you describe them. The Stanford prison experiment, ego depletion, power
posing, the Mehrabian 7-38-55 figures, most micro-expression lie detection —
these are known-weak, and saying so is not a digression, it is the answer.

Write in continuous prose. Use headings only when the answer genuinely has
parts. Do not pad, do not moralise, do not restate the question.

When a question asks how to apply a technique to a specific person, give the
mechanism and the countermeasure, and say plainly that you are not writing
the approach. One sentence on that — no lecture.
"""

RESEARCH_SYSTEM = f"""\
You are Nicomachus in research mode. You are gathering material on a topic in
philosophy, psychology, political theory or rhetoric.

{policy.CHARTER}

Search the web, fetch the strongest primary and scholarly sources you find,
and return a dense, well-organised research note. Prefer: peer-reviewed work,
meta-analyses and replication reports, university and encyclopedia sources
(SEP, IEP), primary texts in the public domain. Distrust: popular-psychology
sites, content marketing, unsourced listicles, anything selling a course.

Structure the note as:
  1. What the concept is, precisely.
  2. Where it comes from — the actual originating work, with the citation.
  3. What the evidence says now, including failures to replicate.
  4. The strongest objection to it.
  5. Open questions worth study.

End with a SOURCES section listing each URL you actually used.
"""


@dataclass
class Answer:
    text: str
    citations: list[dict] = field(default_factory=list)
    stance: Stance = Stance.SCHOLARLY
    offline: bool = False
    usage: dict[str, Any] = field(default_factory=dict)
    provider: str = ""
    model: str = ""


def available() -> bool:
    return providers.select() is not None


def current() -> providers.Provider | None:
    return providers.select()


# --- retrieval-augmented answering --------------------------------------

def _context(hits: list[tuple[float, dict]]) -> str:
    parts = []
    for i, (score, ch) in enumerate(hits, 1):
        head = ch["title"]
        if ch.get("author"):
            head += f" — {ch['author']}"
        if ch.get("source"):
            head += f" ({ch['source']})"
        parts.append(f"[{i}] {head}\n{ch['text']}")
    return "\n\n---\n\n".join(parts)


def answer(question: str, ix: Index | None = None, k: int | None = None,
           auto_research: bool | None = None) -> Answer:
    verdict = policy.assess(question)
    ix = ix if ix is not None else Index.load()
    k = k or SETTINGS.top_k
    hits = ix.search(question, k)

    # Second hop: pull a few passages from concepts the question touches but
    # does not name. This is what lets an answer about akrasia bring in ego
    # depletion, or one about gaslighting bring in testimony and epistemic
    # injustice — the cross-tradition connections are the point of the corpus.
    near = concepts.neighbours(question, 4)
    if near:
        have = {c["path"] + c["text"][:60] for _, c in hits}
        for term in near:
            for score, chunk in ix.search(term, 2, per_doc=1, expand=True):
                key = chunk["path"] + chunk["text"][:60]
                if key not in have:
                    have.add(key)
                    chunk = dict(chunk, _via=term)
                    hits.append((score * 0.55, chunk))  # discounted: indirect
        hits.sort(key=lambda kv: kv[0], reverse=True)
        hits = hits[:k + 4]

    # If the corpus plainly cannot answer this, go and read the web first
    # rather than answering thinly from whatever scraps ranked highest.
    # This is the assistant deciding to go online, not the user asking it to.
    if auto_research is None:
        auto_research = SETTINGS.auto_research
    weak = not hits or max(s for s, _ in hits) < SETTINGS.research_threshold
    if (auto_research and weak and verdict.stance is not Stance.OPERATIONAL
            and available()):
        memory.log("auto-research",
                   f"corpus too thin for {question!r} — going online")
        try:
            research(question)
            ix = Index.load()
            hits = ix.search(question, k or SETTINGS.top_k)
        except Exception as e:
            memory.log("auto-research-failed", str(e))
    cites = [
        {"n": i, "title": ch["title"], "author": ch.get("author", ""),
         "source": ch.get("source", ""), "score": round(s, 2)}
        for i, (s, ch) in enumerate(hits, 1)
    ]

    if verdict.stance is Stance.OPERATIONAL:
        topic = _topic_of(question)
        return Answer(
            text=policy.REDIRECT_TEMPLATE.format(topic=topic),
            citations=cites,
            stance=verdict.stance,
        )

    provider = providers.select()
    if provider is None:
        return Answer(text=_offline(question, hits), citations=cites,
                      stance=verdict.stance, offline=True)

    guidance = ""
    if verdict.stance is Stance.DEFENSIVE:
        guidance = ("\n\nThis is a defensive question — how to recognise or "
                    "resist. Give it the fullest answer you have.")
    elif verdict.stance is Stance.CLINICAL:
        guidance = ("\n\nThis question carries signs of personal distress. "
                    "Answer the substance, then say — briefly, without "
                    "condescension — that a person is what helps here, and "
                    "that local support services exist.")

    prompt = (
        f"Retrieved passages from the corpus:\n\n{_context(hits) or '(corpus is empty)'}"
        f"\n\n---\n\nQuestion: {question}{guidance}"
    )

    reply = provider.complete(SYSTEM, prompt, max_tokens=SETTINGS.max_tokens)
    return Answer(
        text=reply.text,
        citations=cites,
        stance=verdict.stance,
        usage=reply.usage,
        provider=reply.provider,
        model=reply.model,
    )


def _offline(question: str, hits: list[tuple[float, dict]]) -> str:
    if not hits:
        return (
            "No model credential is set and the corpus has nothing on this.\n\n"
            "Set ANTHROPIC_API_KEY or GEMINI_API_KEY for reasoned answers, and "
            "run `nicomachus learn \"<topic>\"` to build the corpus."
        )
    out = [
        f"(offline mode — ranked passages, no synthesis)\n",
        f"Question: {question}\n",
    ]
    for i, (score, ch) in enumerate(hits, 1):
        src = f" — {ch['source']}" if ch.get("source") else ""
        out.append(f"[{i}] {ch['title']}{src}  (score {score:.1f})\n{ch['text']}\n")
    return "\n".join(out)


# Named areas the redirect can point at, so it says something specific rather
# than echoing three words back from the question.
_AREAS: list[tuple[str, str]] = [
    (r"gaslight|deny.*memory|make (?:him|her|them) doubt", "gaslighting"),
    (r"guilt|obligat|owe me|reciproc", "reciprocity and induced obligation"),
    (r"scarcit|urgen|deadline|limited|running out", "scarcity and urgency effects"),
    (r"authorit|expert|credential", "authority cues in compliance"),
    (r"social proof|everyone else|other people are", "social proof and norms"),
    (r"attach|jealous|insecur|abandon", "attachment and emotional dependence"),
    (r"body language|posture|micro.?expression|eye contact", "nonverbal signalling"),
    (r"negotiat|deal|price|salary|discount", "negotiation tactics"),
    (r"interrogat|confess|question(?:ing)? technique", "interrogation research"),
    (r"lie|deceiv|deception|honest", "deception and its detection"),
    (r"persuad|convince|influence|sell", "persuasion research"),
    (r"manipulat|coerc|control|pressure", "the manipulation literature"),
]


def _topic_of(question: str) -> str:
    import re
    q = question.lower()
    for pattern, label in _AREAS:
        if re.search(pattern, q):
            return label
    return "the influence literature"


# --- live research through the model's own web tools --------------------

def research(topic: str, max_searches: int = 8) -> Answer:
    """Let the model search and fetch the live web, then keep what it wrote."""
    verdict = policy.assess(topic)
    if verdict.stance is Stance.OPERATIONAL:
        return Answer(text=policy.REDIRECT_TEMPLATE.format(topic=_topic_of(topic)),
                      stance=verdict.stance)

    provider = providers.select()
    if provider is None:
        return Answer(
            text=("Live research needs a model credential.\n"
                  "Set ANTHROPIC_API_KEY or GEMINI_API_KEY.\n"
                  "The direct open-source harvesters still work offline:\n"
                  f'  nicomachus learn "{topic}"'),
            offline=True,
        )

    reply = provider.research(
        RESEARCH_SYSTEM,
        f"Research this thoroughly and write the note: {topic}",
        max_tokens=SETTINGS.research_max_tokens,
    )
    sources = reply.sources

    from . import harvest
    path = harvest._store(
        "research", topic, reply.text,
        title=f"Research note: {topic}",
        author=f"Nicomachus (live research via {reply.provider})",
        source="; ".join(sources[:10]),
        licence="derived-synthesis",
        kind="note",
    )
    memory.log("research", f"live research note on {topic!r}", str(path))
    for u in sources:
        memory.mark_seen(u, topic, str(path), "cited")

    return Answer(
        text=reply.text,
        citations=[{"n": i, "title": u, "source": u} for i, u in enumerate(sources, 1)],
        usage=reply.usage,
        provider=reply.provider,
        model=reply.model,
    )


# --- self-directed study ------------------------------------------------

DISTIL_SYSTEM = f"""\
You are Nicomachus reviewing what you have just read.

{policy.CHARTER}

Return strict JSON, no prose around it:
{{
  "notes": [
    {{"topic": "...", "claim": "one sentence, specific, falsifiable where possible",
      "confidence": "established | contested | tentative"}}
  ],
  "questions": [
    "a question this reading opened that the corpus cannot yet answer"
  ],
  "gaps": ["a topic the corpus is visibly missing"]
}}

Notes must be claims worth keeping — not summaries of what a page said.
Questions must be answerable by further reading, and must be ones you cannot
already answer. Six of each at most.
"""


REFLECT_SYSTEM = f"""\
You are Nicomachus, looking back over what you have read and asking what it
adds up to.

{policy.CHARTER}

You are given your recent notes and your open questions. Think about them
together, then return strict JSON, no prose around it:

{{
  "standing": "2-4 sentences: what you now take to be true across this
               material, stated plainly, including where the evidence is
               weaker than the field's confidence suggests",
  "protective": [
    "Something a person could act on to avoid being misled or pressured —
     grounded in what you actually read, not general advice. Name the
     mechanism and the tell."
  ],
  "revise": ["A note you now doubt, and why"],
  "next": ["The question most worth reading about next, and why it matters"]
}}

Rules. `protective` is the point of the exercise: this corpus exists so that
people can recognise influence being worked on them, and each item should be
usable by someone who has read no psychology. Three to six items. Do not
invent findings — if the notes do not support a protective claim, return
fewer. `revise` is where you disagree with your earlier self; an empty list
is suspicious after real reading.
"""


def reflect() -> dict:
    """Read back its own notes and questions, and work out what they amount to.

    This is the step that makes the corpus into a position rather than a pile.
    It runs on the quality tier — it is the one genuinely reflective task here.
    """
    provider = providers.select()
    if provider is None:
        return {"standing": "", "protective": [], "revise": [], "next": [],
                "offline": True}

    notes = memory.recent_notes(60)
    questions = memory.open_questions(25)
    if not notes:
        return {"standing": "Nothing read yet — run a study cycle first.",
                "protective": [], "revise": [], "next": [], "offline": False}

    body = "MY NOTES\n" + "\n".join(
        f"- [{n['confidence']}] ({n['topic']}) {n['claim']}" for n in notes
    ) + "\n\nMY OPEN QUESTIONS\n" + "\n".join(
        f"- {q['question']}" for q in questions
    )

    reply = provider.complete(REFLECT_SYSTEM, body, max_tokens=8000)
    text = reply.text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
    try:
        out = json.loads(text)
    except json.JSONDecodeError:
        memory.log("reflect-error", "unparseable JSON", text[:500])
        return {"standing": "", "protective": [], "revise": [], "next": [],
                "offline": False}

    for q in out.get("next", []):
        memory.ask(q, topic="reflection")
    memory.log("reflect",
               f"{len(out.get('protective', []))} protective points, "
               f"{len(out.get('revise', []))} revisions",
               out.get("standing", "")[:400])
    out["offline"] = False
    return out


def distil(sample: str, topic: str = "") -> dict:
    """Turn freshly read material into durable notes and new open questions.

    This runs on the provider's fast tier. It is a structured extraction over
    text already gathered, not a reasoning task, and a study cycle makes one
    call per topic — so the flagship model buys nothing here and costs both
    money and wall-clock.
    """
    provider = providers.select()
    if provider is None:
        return {"notes": [], "questions": [], "gaps": []}

    reply = provider.fast(
        DISTIL_SYSTEM,
        f"Topic under study: {topic}\n\nMaterial:\n\n{sample[:120000]}",
        max_tokens=8000,
        json_mode=True,
    )
    text = reply.text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        memory.log("distil-error", "model did not return parseable JSON", text[:500])
        return {"notes": [], "questions": [], "gaps": []}
