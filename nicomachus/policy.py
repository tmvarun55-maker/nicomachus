"""The study-use charter.

Nicomachus holds the literature on influence, persuasion, coercion and
nonverbal behaviour because researchers and students need it. The same
literature can be turned into an operational script aimed at a named person.
The charter draws that line and keeps it drawn.

The rule in one sentence: Nicomachus explains mechanisms, evidence and
countermeasures for anyone; it does not write the operation.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum


class Stance(str, Enum):
    SCHOLARLY = "scholarly"        # explain / analyse / cite — answer in full
    DEFENSIVE = "defensive"        # detect / resist / protect — answer in full, gladly
    OPERATIONAL = "operational"    # build me the play against a person — reframe
    CLINICAL = "clinical"          # someone may be in distress — answer, plus signpost


@dataclass
class Verdict:
    stance: Stance
    reason: str
    note: str = ""

    @property
    def redirect(self) -> bool:
        return self.stance is Stance.OPERATIONAL


# --- signals -------------------------------------------------------------

# "do this to a specific person" — the operational shape
_TARGETED = re.compile(
    r"\b(?:"
    r"how (?:do|can|should) i (?:get|make|convince|persuade|manipulate|pressure|"
    r"trick|guilt|force|coerce|break|wear (?:him|her|them) down)"
    r"|write (?:me )?(?:a )?(?:script|message|text|email|dm)\b[^.?!]{0,60}\b"
    r"(?:so (?:he|she|they)|to (?:get|make)|that will make)"
    r"|what (?:do|should) i say to (?:get|make|convince)"
    r"|steps? to (?:manipulate|control|dominate|break down|gaslight)"
    r"|exploit (?:his|her|their|my) (?:weakness|insecurit|trauma|fear|grief|"
    r"loneliness|attachment)"
    r"|use (?:this|that|it) (?:on|against) (?:him|her|them|my)"
    r")",
    re.I,
)

_HARM_FRAME = re.compile(
    r"\b(?:gaslight(?:ing)?|love.?bomb(?:ing)?|negging|coercive control|"
    r"dark triad play|isolate (?:him|her|them)|grooming|brainwash|"
    r"break (?:his|her|their) will|trauma bond)\b",
    re.I,
)

# marks of an academic frame — these pull *back* toward scholarly
_SCHOLARLY = re.compile(
    r"\b(?:explain|what is|what are|define|history of|origin|literature|"
    r"evidence|meta.?analys|replicat|effect size|critique|criticism|compare|"
    r"contrast|theory|theories|framework|taxonomy|cite|citation|source|study|"
    r"studies|research|experiment|paper|according to|aristotle|kant|hume|"
    r"summar|overview|syllabus|lecture|essay|thesis|dissertation|exam|"
    r"coursework|for my (?:class|course|paper|research))\b",
    re.I,
)

_DEFENSIVE = re.compile(
    r"\b(?:recogni[sz]e|detect|spot|identify|resist|protect|defend|guard|"
    r"inoculat|debunk|counter|red flag|warning sign|am i being|was i being|"
    r"is (?:this|that) manipulation|how do i tell if|safeguard|prebunk)\b",
    re.I,
)

_DISTRESS = re.compile(
    r"\b(?:i (?:want to|might|"
    r"feel like) (?:die|end it|kill myself|hurt myself)|suicid|self.?harm|"
    r"abus(?:ive|ing) (?:relationship|partner|parent)|he hits me|she hits me|"
    r"afraid of (?:him|her|them)|threaten(?:s|ed) me)\b",
    re.I,
)

_VULNERABLE = re.compile(
    r"\b(?:my (?:child|kid|son|daughter|student|patient|employee|report)|"
    r"a (?:child|minor|teenager|patient|elderly)|under.?age|grandmother|"
    r"grandfather|dementia|vulnerable)\b",
    re.I,
)


def assess(question: str) -> Verdict:
    """Classify a question against the charter. Cheap, local, no model call."""
    q = question.strip()

    if _DISTRESS.search(q):
        return Verdict(
            Stance.CLINICAL,
            "the question carries signs of personal distress",
            "Answer the substance, then say plainly that a person — not a "
            "reading list — is what helps here.",
        )

    if _DEFENSIVE.search(q) and not _TARGETED.search(q):
        return Verdict(Stance.DEFENSIVE, "asks how to recognise or resist influence")

    targeted = bool(_TARGETED.search(q))
    harmful = bool(_HARM_FRAME.search(q))
    scholarly = bool(_SCHOLARLY.search(q))

    if targeted and not scholarly:
        return Verdict(
            Stance.OPERATIONAL,
            "asks for a tactic aimed at a particular person rather than for "
            "an account of how the tactic works",
        )

    if harmful and targeted:
        return Verdict(
            Stance.OPERATIONAL,
            "asks how to apply a coercive technique to someone",
        )

    if _VULNERABLE.search(q) and targeted:
        return Verdict(
            Stance.OPERATIONAL,
            "asks about influencing someone in a dependent or protected position",
        )

    return Verdict(Stance.SCHOLARLY, "reads as a question about the subject matter")


REDIRECT_TEMPLATE = """\
I'll give you the mechanism, not the move.

The literature you're reaching for is {topic}. What I can lay out — and will,
in full — is how it is theorised to work, what the evidence actually supports
(often much less than the popular version claims), how it's measured, who
criticised it and why, and how the same body of work is used to teach people
to notice it being done to them.

What I won't do is compose the approach for a specific person. Not because the
knowledge is forbidden — you're holding it — but because a script aimed at a
named human being is the one form of this material that stops being study.

Ask it the other way and I'll go as deep as you like:
  · how does {topic} work, and what's the strongest critique of it?
  · what does the replication record look like?
  · how would a person recognise it being used on them?
"""


CHARTER = """\
NICOMACHUS — STUDY CHARTER

1. This assistant exists for students, teachers and researchers of
   philosophy, psychology, political theory and rhetoric.

2. It teaches the mechanism, the evidence, the history and the critique of
   every technique in its corpus — including persuasion, propaganda,
   negotiation, interrogation, coercive control and nonverbal signalling.
   Nothing in the subject matter is off-limits to study.

3. It does not compose an operation against a named person. It will not write
   the message, the script, the sequence of moves, or the tailored approach.
   Asked for one, it returns the mechanism and the countermeasure instead.

4. It treats the defensive use as the first-class use. "How would I notice
   this being done to me" always gets the fullest answer available.

5. It states uncertainty. Where a famous finding failed to replicate, it says
   so before it says anything else. An overstated claim is a worse failure
   than a missing one.

6. It cites. Every substantive claim is traceable to a source in the corpus
   or is marked as the assistant's own synthesis.
"""
