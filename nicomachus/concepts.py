"""A concept map for the fields, and what it is for.

BM25 matches words. These fields say the same thing in many words — akrasia is
weakness of will is incontinence is self-control failure — and a student who
knows one of those names should get the passages written under the others.

Two structures:

  ALIASES   terms that name the same concept. Used to expand a query before
            it reaches the index, so vocabulary never gates recall.

  RELATED   concepts that illuminate each other across traditions. Used for a
            second retrieval hop, so an answer about akrasia can reach ego
            depletion and self-regulation without the user knowing to ask.

The map is hand-built rather than learned. It is small, it is auditable, and
it encodes the connections that actually matter in these fields — which is
the thing a keyword index cannot know and an embedding would only approximate.
"""

from __future__ import annotations

import re

# --- same concept, different names --------------------------------------

ALIASES: dict[str, list[str]] = {
    # Aristotle
    "akrasia": ["weakness of will", "incontinence", "self-control failure"],
    "phronesis": ["practical wisdom", "prudence", "practical reason"],
    "eudaimonia": ["flourishing", "happiness", "living well", "the good life"],
    "arete": ["virtue", "excellence"],
    "hexis": ["disposition", "stable state", "character trait"],
    "ergon": ["function argument", "characteristic activity"],
    "enkrateia": ["continence", "self-mastery", "self-control"],
    "sophrosyne": ["temperance", "moderation"],
    "megalopsychia": ["magnanimity", "greatness of soul"],
    "philia": ["friendship", "affection", "social bond"],
    "theoria": ["contemplation", "contemplative life"],
    "telos": ["end", "purpose", "final cause", "teleology"],
    "hylomorphism": ["matter and form", "form and matter"],
    "enthymeme": ["rhetorical syllogism", "suppressed premise"],
    "topoi": ["commonplaces", "lines of argument", "topics"],
    "ethos": ["speaker credibility", "character of the speaker"],
    "pathos": ["emotional appeal", "audience emotion"],
    "logos": ["argument", "reasoning", "rational appeal"],
    "catharsis": ["purgation", "purification"],
    "mimesis": ["imitation", "representation"],
    "polis": ["city state", "political community"],
    "politeia": ["polity", "constitution", "mixed constitution"],

    # philosophy
    "deontology": ["kantian ethics", "duty ethics", "categorical imperative"],
    "consequentialism": ["utilitarianism", "outcome ethics"],
    "virtue ethics": ["character ethics", "aretaic ethics"],
    "epistemology": ["theory of knowledge", "justification", "knowing"],
    "gettier": ["justified true belief", "jtb problem"],
    "qualia": ["phenomenal consciousness", "what it is like", "subjective experience"],
    "hard problem": ["explanatory gap", "consciousness problem"],
    "physicalism": ["materialism", "mind brain identity"],
    "falsification": ["popper", "falsifiability", "demarcation"],
    "paradigm": ["kuhn", "normal science", "scientific revolution"],
    "underdetermination": ["duhem quine", "theory choice"],
    "social contract": ["contractarianism", "state of nature", "consent theory"],
    "general will": ["rousseau", "popular sovereignty"],
    "veil of ignorance": ["original position", "rawls", "justice as fairness"],
    "harm principle": ["mill", "liberty principle"],
    "banality of evil": ["arendt", "thoughtlessness"],
    "governmentality": ["foucault", "biopower", "disciplinary power"],

    # psychology
    "heuristics": ["mental shortcuts", "rules of thumb", "cognitive biases"],
    "anchoring": ["anchor effect", "first offer effect"],
    "availability": ["availability heuristic", "ease of retrieval"],
    "framing": ["prospect theory", "loss aversion", "gain loss framing"],
    "dual process": ["system 1", "system 2", "fast and slow thinking"],
    "cognitive dissonance": ["festinger", "dissonance reduction"],
    "self determination theory": ["sdt", "autonomy competence relatedness",
                                  "intrinsic motivation"],
    "big five": ["five factor model", "ffm", "ocean personality"],
    "hexaco": ["honesty humility", "six factor personality"],
    "attachment": ["bowlby", "ainsworth", "strange situation",
                   "secure avoidant anxious"],
    "ego depletion": ["willpower depletion", "self control resource"],
    "reconstructive memory": ["false memory", "misinformation effect", "loftus"],
    "testing effect": ["retrieval practice", "spacing effect",
                       "distributed practice"],
    "social identity": ["tajfel", "ingroup outgroup", "minimal group"],
    "fundamental attribution error": ["correspondence bias",
                                      "dispositional attribution"],
    "bystander effect": ["diffusion of responsibility"],
    "conformity": ["asch", "normative influence", "social pressure"],
    "obedience": ["milgram", "authority compliance", "engaged followership"],
    "replication crisis": ["reproducibility", "p hacking",
                           "researcher degrees of freedom", "preregistration"],
    "weird samples": ["western educated industrialised rich democratic",
                      "sample generalisability"],

    # emotion and expression
    "appraisal theory": ["lazarus", "scherer", "cognitive appraisal",
                         "component process model"],
    "basic emotions": ["ekman", "universal expressions", "discrete emotions"],
    "constructed emotion": ["barrett", "psychological construction",
                            "core affect"],
    "facs": ["facial action coding", "action units", "au coding"],
    "reappraisal": ["cognitive reappraisal", "emotion regulation", "gross model"],
    "suppression": ["expressive suppression", "emotion inhibition"],
    "affect labelling": ["naming emotions", "putting feelings into words"],
    "alexithymia": ["emotional granularity", "emotion vocabulary"],
    "proxemics": ["personal space", "interpersonal distance", "hall zones"],
    "paralanguage": ["vocal cues", "prosody", "tone of voice"],
    "duchenne": ["genuine smile", "orbicularis oculi"],
    "mehrabian": ["7 38 55", "7-38-55", "communication percentages"],

    # influence
    "elaboration likelihood": ["elm", "central route", "peripheral route",
                               "petty cacioppo"],
    "heuristic systematic": ["hsm", "chaiken"],
    "inoculation": ["prebunking", "resistance to persuasion",
                    "attitudinal inoculation"],
    "social proof": ["descriptive norms", "what others do", "normative feedback"],
    "reciprocity": ["obligation", "returning favours", "indebtedness"],
    "scarcity": ["limited availability", "urgency", "fomo"],
    "foot in the door": ["incremental commitment", "escalating requests"],
    "door in the face": ["rejection then retreat"],
    # Aliases here include how people actually phrase the question when it is
    # happening to them, not only the technical name. Someone asking "am I
    # being made to doubt my memory" has never heard the word gaslighting.
    "gaslighting": ["reality denial", "epistemic abuse", "memory undermining",
                    "denying my reality", "doubt my memory", "doubt my own",
                    "making me feel crazy", "questioning my sanity",
                    "denies things happened", "rewriting what happened"],
    "coercive control": ["stark", "intimate partner control",
                         "controlling behaviour"],
    "dark patterns": ["deceptive design", "manipulative interface", "sludge"],
    "love bombing": ["overwhelming affection", "idealisation phase"],
    "intermittent reinforcement": ["variable ratio", "unpredictable reward",
                                   "trauma bond"],
    "darvo": ["deny attack reverse victim offender"],
    "motivational interviewing": ["change talk", "miller rollnick",
                                  "self persuasion"],
    "deep canvassing": ["perspective taking conversation", "broockman kalla"],
    "lateral reading": ["source checking", "fact checker method", "wineburg"],

    # negotiation
    "batna": ["best alternative", "walk away option", "outside option"],
    "zopa": ["zone of possible agreement", "bargaining range"],
    "integrative": ["value creation", "win win", "joint gains"],
    "distributive": ["value claiming", "zero sum bargaining"],
    "fixed pie": ["fixed pie bias", "zero sum assumption"],
    "meso": ["multiple equivalent simultaneous offers"],
    "reactive devaluation": ["adversary discount"],
}

# --- concepts that illuminate each other --------------------------------

RELATED: dict[str, list[str]] = {
    "akrasia": ["ego depletion", "enkrateia", "self determination theory",
                "dual process", "phronesis"],
    "phronesis": ["akrasia", "virtue ethics", "practical wisdom",
                  "expertise", "situationism"],
    "eudaimonia": ["self determination theory", "wellbeing", "virtue ethics"],
    "ethos": ["source credibility", "elaboration likelihood", "authority"],
    "pathos": ["appraisal theory", "fear appeals", "emotion regulation"],
    "logos": ["enthymeme", "logical fallacies", "argument"],
    "enthymeme": ["topoi", "logical fallacies", "framing"],
    "virtue ethics": ["deontology", "consequentialism", "situationism",
                      "big five", "moral psychology"],
    "situationism": ["fundamental attribution error", "obedience",
                     "virtue ethics", "big five"],
    "obedience": ["conformity", "social identity", "authority",
                  "replication crisis"],
    "conformity": ["social proof", "social identity", "obedience"],
    "social proof": ["conformity", "descriptive norms", "dark patterns"],
    "gaslighting": ["coercive control", "darvo", "epistemology",
                    "reconstructive memory"],
    "coercive control": ["gaslighting", "intermittent reinforcement",
                         "attachment", "love bombing"],
    "manipulation": ["gaslighting", "dark patterns", "coercive control",
                     "inoculation", "harm principle", "autonomy"],
    "inoculation": ["manipulation", "forewarning", "lateral reading",
                    "media literacy"],
    "dark patterns": ["framing", "defaults", "manipulation", "social proof"],
    "framing": ["anchoring", "prospect theory", "dark patterns", "negotiation"],
    "anchoring": ["framing", "batna", "negotiation", "heuristics"],
    "batna": ["zopa", "anchoring", "integrative", "power"],
    "basic emotions": ["constructed emotion", "facs", "appraisal theory"],
    "constructed emotion": ["basic emotions", "alexithymia", "appraisal theory"],
    "facs": ["basic emotions", "deception detection", "constructed emotion"],
    "deception detection": ["facs", "nonverbal", "base rates",
                            "replication crisis", "interrogation"],
    "replication crisis": ["ego depletion", "obedience", "weird samples",
                           "falsification", "publication bias"],
    "falsification": ["replication crisis", "paradigm", "underdetermination"],
    "epistemology": ["gettier", "testimony", "gaslighting", "falsification"],
    "attachment": ["coercive control", "developmental psychology",
                   "intermittent reinforcement"],
    "self determination theory": ["motivational interviewing", "manipulation",
                                  "eudaimonia", "autonomy"],
    "motivational interviewing": ["self determination theory",
                                  "cognitive dissonance", "deep canvassing"],
    "autonomy": ["manipulation", "harm principle", "self determination theory",
                 "veil of ignorance"],
    "social contract": ["veil of ignorance", "general will", "harm principle"],
    "harm principle": ["manipulation", "autonomy", "dark patterns"],
}

# Digits are part of concept names here — "7-38-55", "system 1", "big five".
# Stripping them made the Mehrabian ratio unfindable by its own name.
_WORD = re.compile(r"[a-z0-9][a-z0-9\-]*")

# Reverse index: any alias phrase -> its canonical concept.
_LOOKUP: dict[str, str] = {}
for _canon, _alts in ALIASES.items():
    _LOOKUP[_canon] = _canon
    for _a in _alts:
        _LOOKUP[_a] = _canon


def canonical(phrase: str) -> str | None:
    return _LOOKUP.get(phrase.strip().lower())


def concepts_in(text: str) -> list[str]:
    """Which known concepts does this text mention?"""
    low = " " + " ".join(_WORD.findall(text.lower())) + " "
    found = []
    for phrase, canon in _LOOKUP.items():
        if f" {phrase} " in low and canon not in found:
            found.append(canon)
    return found


def expand(query: str, limit: int = 12) -> list[str]:
    """Extra search terms for a query — the other names for what it asked about.

    Returns only the added terms, so the caller decides how to weight them.
    """
    extra: list[str] = []
    for canon in concepts_in(query):
        for term in [canon] + ALIASES.get(canon, []):
            if term.lower() not in query.lower() and term not in extra:
                extra.append(term)
    return extra[:limit]


def neighbours(query: str, limit: int = 6) -> list[str]:
    """Concepts worth a second retrieval hop for this query."""
    out: list[str] = []
    for canon in concepts_in(query):
        for rel in RELATED.get(canon, []):
            if rel not in out and rel.lower() not in query.lower():
                out.append(rel)
    return out[:limit]


def map_size() -> dict[str, int]:
    return {
        "concepts": len(ALIASES),
        "aliases": sum(len(v) for v in ALIASES.values()),
        "relations": sum(len(v) for v in RELATED.values()),
    }
