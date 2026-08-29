"""The study cycle — how Nicomachus gets better without being told to.

One cycle:
  1. choose what to study (its own open questions first, then curriculum gaps)
  2. harvest from the open sources
  3. read what came back and distil it into notes + new questions
  4. reindex
  5. write the cycle to the journal

Run it once by hand, or on a schedule. Each cycle leaves the corpus larger and
the open-question list different, which is the whole mechanism: the questions
it generates determine what it reads next.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from . import brain, corpus, harvest, memory
from .config import SETTINGS
from .index import rebuild

# The starting curriculum — used when the question queue runs dry.
CURRICULUM = [
    # Aristotle, first
    "Aristotle Nicomachean Ethics virtue doctrine of the mean",
    "Aristotle phronesis practical wisdom",
    "Aristotle Rhetoric ethos pathos logos enthymeme",
    "Aristotle Politics constitutions polity citizenship",
    "Aristotle Poetics catharsis mimesis tragedy",
    "Aristotle De Anima soul perception",
    "Aristotle four causes hylomorphism substance",
    "Aristotle Prior Analytics syllogism logic",
    "Aristotle eudaimonia flourishing highest good",
    "Aristotle akrasia weakness of will",
    # philosophy beyond Aristotle
    "virtue ethics contemporary revival Anscombe MacIntyre",
    "deontology Kant categorical imperative",
    "utilitarianism Bentham Mill consequentialism",
    "Stoicism Epictetus Marcus Aurelius ethics",
    "epistemology justified true belief Gettier problem",
    "philosophy of mind consciousness qualia",
    "moral psychology sentimentalism rationalism",
    "philosophy of emotion cognitive theories",
    # political theory
    "social contract Hobbes Locke Rousseau",
    "Machiavelli The Prince political realism",
    "John Rawls theory of justice original position",
    "Hannah Arendt totalitarianism banality of evil",
    "Foucault power knowledge discipline",
    "deliberative democracy Habermas public sphere",
    "political polarization affective polarization research",
    "propaganda theory Ellul Bernays",
    # psychology
    "cognitive biases heuristics Kahneman Tversky",
    "dual process theory System 1 System 2 critique",
    "Big Five personality HEXACO structure evidence",
    "self determination theory motivation autonomy competence",
    "attachment theory Bowlby Ainsworth adult attachment",
    "cognitive dissonance Festinger replication",
    "conformity Asch obedience Milgram reappraisal",
    "replication crisis psychology p-hacking preregistration",
    "memory reconsolidation false memory Loftus",
    "emotion theory basic emotions constructed emotion Barrett",
    "facial action coding system FACS validity",
    "nonverbal behavior deception detection meta-analysis",
    "Mehrabian 7-38-55 myth misinterpretation",
    "moral foundations theory Haidt critique",
    "developmental psychology Piaget Vygotsky",
    "social identity theory Tajfel intergroup",
    # influence, studied as a science
    "elaboration likelihood model persuasion Petty Cacioppo",
    "Cialdini principles of influence replication evidence",
    "inoculation theory misinformation prebunking",
    "framing effects prospect theory",
    "negotiation integrative distributive BATNA Fisher Ury",
    "coercive control Evan Stark recognition",
    "dark patterns manipulative design taxonomy",
    "media literacy interventions effectiveness",
    # epistemology, logic, mind, science
    "Gettier problem justified true belief analysis",
    "epistemic injustice Fricker testimonial hermeneutical",
    "testimony epistemology trust reductionism",
    "informal logic fallacies argumentation schemes Walton",
    "Toulmin model warrant argument structure",
    "hard problem of consciousness Chalmers zombie argument",
    "functionalism multiple realisability philosophy of mind",
    "extended mind Clark Chalmers embodied cognition",
    "personal identity Parfit psychological continuity",
    "Popper falsification demarcation criterion",
    "Kuhn paradigm incommensurability scientific revolution",
    "Lakatos research programmes progressive degenerating",
    "Duhem Quine underdetermination holism",
    "severity Mayo error statistics philosophy",
    "scientific realism no miracles pessimistic meta-induction",
    "values in science inductive risk Douglas",
    # social psychology, decision
    "implicit association test predictive validity critique",
    "prejudice reduction interventions field experiments Paluck",
    "pluralistic ignorance norm misperception",
    "implementation intentions Gollwitzer meta-analysis",
    "stereotype threat replication effect size",
    "prospect theory loss aversion magnitude debate",
    "ultimatum game cross-cultural Henrich",
    "iterated prisoner dilemma tit for tat noise",
    "Schelling commitment strategy bargaining",
    "signalling theory costly signals credibility",
    "Arrow impossibility theorem social choice",
    "Condorcet jury theorem epistemic democracy",
    "ecological rationality Gigerenzer fast frugal heuristics",
    "confabulation Nisbett Wilson telling more than we know",
    "split brain interpreter Gazzaniga",
    "motivated reasoning identity protective cognition Kahan",
    "illusion of explanatory depth debiasing",
]


@dataclass
class CycleReport:
    targets: list[str] = field(default_factory=list)
    harvested: int = 0
    notes: int = 0
    new_questions: int = 0
    indexed: int = 0
    errors: list[str] = field(default_factory=list)

    def render(self) -> str:
        lines = ["Study cycle complete.", ""]
        lines.append(f"  studied      {len(self.targets)} topic(s)")
        for t in self.targets:
            lines.append(f"               · {t}")
        lines.append(f"  harvested    {self.harvested} new document(s)")
        lines.append(f"  notes kept   {self.notes}")
        lines.append(f"  questions    {self.new_questions} new")
        lines.append(f"  index        {self.indexed} chunks")
        if self.errors:
            lines.append("  errors:")
            lines.extend(f"               ! {e}" for e in self.errors)
        return "\n".join(lines)


def choose_targets(n: int) -> list[str]:
    """Its own open questions come first; curriculum fills the rest.

    Chosen questions move to 'studying' so the next cycle advances instead of
    re-reading the same three.
    """
    targets: list[str] = []
    for q in memory.open_questions(n):
        targets.append(q["question"])
        memory.mark_studying(q["id"])

    if len(targets) < n:
        done = {r["summary"] for r in memory.journal(500) if r["kind"] == "studied"}
        fresh = [c for c in CURRICULUM if c not in done] or CURRICULUM
        targets += random.sample(fresh, min(n - len(targets), len(fresh)))
    return targets[:n]


def cycle(targets: list[str] | None = None, *, per_source: int = 3,
          verbose: bool = True) -> CycleReport:
    rep = CycleReport()
    rep.targets = targets or choose_targets(max(1, SETTINGS.questions_per_cycle // 2))

    for target in rep.targets:
        if verbose:
            print(f"  studying: {target}")
        try:
            got = harvest.gather(target, per_source=per_source)
        except Exception as e:
            rep.errors.append(f"harvest {target!r}: {e}")
            continue
        rep.harvested += len(got)
        memory.log("studied", target, f"{len(got)} documents")

        if not got:
            continue

        # Read a sample of what came back and turn it into durable notes.
        sample = "\n\n".join(
            corpus.parse(h.path).body[:12000] for h in got[:6]
        )
        try:
            result = brain.distil(sample, topic=target)
        except Exception as e:
            rep.errors.append(f"distil {target!r}: {e}")
            continue

        for note in result.get("notes", []):
            if note.get("claim"):
                memory.add_note(
                    note.get("topic", target),
                    note["claim"],
                    note.get("confidence", "tentative"),
                    provenance="; ".join(h.url for h in got[:4]),
                )
                rep.notes += 1
        for q in result.get("questions", []) + result.get("gaps", []):
            if memory.ask(q, topic=target):
                rep.new_questions += 1

    ix = rebuild(verbose=False)
    rep.indexed = len(ix)
    memory.log(
        "cycle",
        f"{len(rep.targets)} topics, +{rep.harvested} docs, "
        f"+{rep.notes} notes, +{rep.new_questions} questions",
        "\n".join(rep.targets),
    )
    return rep


def autonomous(rounds: int = 3, per_source: int = 3,
               verbose: bool = True) -> list[CycleReport]:
    """Study on its own for a while, then think about what it found.

    Each round it picks its own targets, reads, and distils; the questions
    that come out steer the next round. Reflection runs at the end, which is
    what turns the accumulated notes into a position and a set of protective
    points. This is the mode to put on a schedule.
    """
    reports = []
    for i in range(max(1, rounds)):
        if verbose:
            print(f"  round {i + 1}/{rounds}")
        reports.append(cycle(per_source=per_source, verbose=verbose))

    result = brain.reflect()
    if result.get("standing"):
        memory.add_note("standing view", result["standing"], "tentative",
                        provenance="reflection")
    for point in result.get("protective", []):
        memory.add_note("protective", point, "tentative",
                        provenance="reflection")
    if verbose and result.get("standing"):
        print(f"\n  {result['standing']}")
    return reports


def seed_questions() -> int:
    """Prime the question queue from the curriculum so cycle 1 has direction."""
    n = 0
    for topic in CURRICULUM[:12]:
        if memory.ask(f"What does the current evidence say about: {topic}?", topic):
            n += 1
    return n
