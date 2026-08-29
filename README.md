# Nicomachus

A study assistant for philosophy, psychology, political theory and rhetoric.
Named for Aristotle's son.

It holds a curated knowledge base, harvests open scholarly sources, reasons
over them with Claude, generates its own open questions, and reads to answer
them on a schedule. It runs on your machine and owns its own corpus.

```bash
nicomachus.bat
```

That opens the web interface at `http://127.0.0.1:8422` — ask, browse the
library, read its notes and open questions, and run study cycles from the
page. Everything also works from the command line.

---

## What it is

| | |
|---|---|
| **Knowledge base** | 16 hand-written reference notes: Aristotle (ethics, rhetoric, politics), epistemology, logic and fallacies, philosophy of mind, philosophy of science, psychology, social psychology, emotion, nonverbal behaviour, persuasion, manipulation, negotiation, decision and game theory, research methods — each with replication status attached |
| **Corpus** | Public-domain primary texts, Wikipedia, OpenAlex, arXiv, PubMed — harvested, licence-tagged, deduplicated |
| **Retrieval** | SQLite FTS5 + BM25, source-diversity capped, with a 95-concept alias map so "weakness of will" reaches passages filed under "akrasia", and a second hop through related concepts so answers connect traditions |
| **Reasoning** | Claude Opus 5 **or** Google Gemini — whichever you have a key for |
| **Live research** | Web-grounded search through the model (Anthropic `web_search`/`web_fetch`, or Gemini Google Search grounding), written back into the corpus |
| **Memory** | SQLite: what it has read, what it concluded, what it still wants to know |
| **Self-direction** | Each cycle it distils notes and generates new questions; those questions decide what it reads next |
| **Its own judgement** | When retrieval comes back too thin to answer honestly, it goes and reads the web unprompted, then answers |
| **Reflection** | Reads back its own notes and works out what they amount to — a standing view, points a person could actually use to avoid being worked on, and notes it now doubts |
| **Interface** | A local web app — stdlib `http.server`, no framework, no build step |

## Install

```bash
pip install -r requirements.txt
```

Set a credential for reasoning — either provider, or both (harvesting and
search work without one):

```bash
setx ANTHROPIC_API_KEY "sk-ant-..."
```

```bash
setx GEMINI_API_KEY "..."
```

With both set it uses Anthropic; `nicomachus providers --use gemini` switches
and remembers. `nicomachus providers` shows what's active.

| | quality tier | fast tier (distillation) |
|---|---|---|
| anthropic | `claude-opus-5` | `claude-haiku-4-5` |
| gemini | `gemini-3.7-flash` | `gemini-3.5-flash-lite` |

Edit `data/settings.json` to change any of these.

Then open a new shell, and:

```bash
python -m nicomachus index
python -m nicomachus seed
python -m nicomachus study
```

Put your own contact address in `data/settings.json` under `contact` before
running large harvests — Wikimedia and NCBI both ask for a reachable
User-Agent, and an anonymous one gets rate-limited.

## Commands

```
ask "<question>"        answer from the corpus, with citations
chat                    interactive session
research "<topic>"      live web research through the model, saved as a note
learn "<topic>"         harvest open sources on a topic
study [topics...]       a full self-directed cycle: read, distil, question, reindex
index                   rebuild the search index
status                  what it knows and what it has been doing
questions               the open questions it has set itself
notes [topic]           claims it has written down, with provenance
serve                   open the web interface (default when run bare)
reflect                 think over what it has read: standing view,
                        protective points, what it now doubts, what's next
autonomous [--rounds N] study unattended, then reflect
charter                 the study charter it operates under
check "<question>"      show how the charter reads a question
providers [--use X]     show or switch model provider (auto|anthropic|gemini)
```

`learn --sources` takes any of `wikipedia openalex arxiv pubmed gutenberg`.

## Keeping it running

**Windows** — a daily cycle via Task Scheduler:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\install_task.ps1
```

**Free hosted** — push to GitHub and `.github/workflows/study.yml` runs a
cycle nightly on GitHub's runners at no cost, committing what it learned back
to the repo. That is the honest version of "its own server": someone else's
machine, free, on a cron, with the corpus as the persistent state.

## The charter

Nicomachus holds the literature on persuasion, propaganda, coercive control
and nonverbal signalling, because those are things students and researchers
study. It is built so that the knowledge is fully available and the operation
is not.

- It explains **mechanism, evidence, history and critique** for everything in
  its corpus. Nothing in the subject matter is withheld.
- It does not compose an approach aimed at a named person — no script, no
  sequence of moves, no tailored message. Asked for one, it returns the
  mechanism and the countermeasure instead.
- It treats the **defensive use as the first-class use**. "How would I notice
  this being done to me" gets the fullest answer it has.
- It states replication status before it states a finding.

`python -m nicomachus check "<question>"` shows you where any question lands.

This is not a filter bolted on the front. It reflects something real in the
material: the compliance techniques have small effects and a poor replication
record, while the recognition and resistance findings are robust and
generalise. Manipulation works by a gap between what is happening and what the
target perceives — so understanding it closes the gap. The knowledge is
genuinely better suited to defence than to offence, which is the argument for
teaching it openly rather than restricting it.

## Speed

Measured on this corpus (37 documents, 1.1M characters, 1,177 chunks):

| | before | after |
|---|---|---|
| any command (cold start) | 3.00 s | **0.35 s** |
| index rebuild | 2.62 s | **0.62 s** |
| harvest, 4 sources | 39.8 s | **7.9 s** |

Where it went:

- **Cold start** was `available()` calling `import anthropic` just to check the
  package existed — 3.2 s of import for a yes/no answer. Now `find_spec`
  locates it without executing it, and the SDK is imported on first real use.
  This was the whole 3 seconds, on every command.
- **Retrieval** moved from a 2.7 MB JSON index parsed in full on every command
  to SQLite FTS5, which queries off disk. Cost no longer grows with the corpus.
- **Harvesting** runs sources concurrently, and each host is rate-limited to
  its own documented figure rather than a blanket 1 s — OpenAlex allows 10/s,
  NCBI 3/s, while arXiv asks for 3 s and now actually gets it. Requests to a
  single host stay serial, which is what Wikimedia's etiquette asks for.
- **Distillation** runs on the fast tier. It is structured extraction over
  text already gathered, not reasoning, so the flagship model bought nothing.

## Layout

```
nicomachus/
  config.py    paths, settings, per-provider models
  policy.py    the charter, and the classifier that applies it
  corpus.py    document format, front matter, chunking
  index.py     SQLite FTS5 index
  harvest.py   the open-source fetchers (allowlisted, per-host rate limits)
  memory.py    SQLite: seen / notes / questions / journal
  providers.py Anthropic and Gemini behind one interface
  brain.py     answering, live research, distillation
  study.py     the study cycle and the seed curriculum
  cli.py       commands
topics/        hand-written reference notes (the seed knowledge)
corpus/        harvested documents, by source
data/          index, memory, settings, logs
```

## Sources it draws on

All open, all with a documented public API, all used within their terms:
Wikipedia (CC BY-SA), Project Gutenberg via Gutendex (public domain),
OpenAlex (CC0), arXiv, PubMed/NCBI E-utilities. Requests are serialised,
rate-limited to one per second, capped per document, and checked against
robots.txt except on documented API endpoints, which are governed by their
own terms of use instead.

It does not crawl the open web, bypass paywalls, or copy in-copyright books.

## Honest limits

- **It does not contain "all information on the internet."** No system does.
  What it has is a good curated core plus a growing, licence-clean corpus and
  live retrieval for the rest. That is the version of the goal that exists.
- **It does not improve its own weights.** What genuinely improves is its
  corpus, its notes, and its question queue — and those change what it can
  answer. The learning is real; it lives in the knowledge base, not the model.
- **It has no data centre.** It runs on your machine, or free on a GitHub
  runner. Both are real; neither is a data centre.
- **The reasoning quality is Claude's.** Nicomachus supplies the grounding,
  the citations, the charter and the memory.
