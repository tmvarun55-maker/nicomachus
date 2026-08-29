---
title: Nonverbal behaviour, body language and expression — evidence versus folklore
author: Nicomachus (curated note)
source: see citations inline; DePaulo et al. 2003; Bond & DePaulo 2006; Barrett et al. 2019
licence: original-note
kind: note
added: 2026-08-29
---

# Nonverbal behaviour: what actually holds up

This is the field where the gap between popular claims and evidence is widest.
Anyone studying it should start from the debunkings, because the folklore is
so pervasive that it will otherwise contaminate everything read afterwards.

## Start here: four claims that are false

**1. "Communication is 7% words, 38% tone, 55% body language."**
This is a misreading of two small 1967 studies by Albert Mehrabian. The
studies asked participants to judge the *feeling* of a speaker from a single
recorded word, where channel content was deliberately made inconsistent. The
ratio applies only to inferring like/dislike from inconsistent single-word
stimuli. Mehrabian himself has repeatedly said the figures are misused. There
is no general finding that words carry 7% of meaning; the claim is not
approximately true, it is a category error.

**2. Body language reliably reveals lying.**
The largest meta-analysis of deception cues (DePaulo et al., *Psychological
Bulletin*, 2003; 158 cues, 120 samples) found that most behaviours popularly
believed to indicate deception have effect sizes indistinguishable from zero.
Gaze aversion — the single most widely believed cue — showed essentially no
relationship to lying (d ≈ 0.03). The cues that did show small effects were
mostly *verbal and content-based*: fewer details, less plausibility, less
verbal-nonverbal involvement, greater tension. Most were small (|d| < 0.20).

Bond & DePaulo (2006) meta-analysed accuracy across 206 studies: people detect
lies at **54%** where chance is 50%. Professional groups — police,
customs officers, judges — do not perform meaningfully better than students;
what they reliably have is higher *confidence*. This is one of the most robust
findings in the field.

**3. There are seven universal facial expressions that reveal emotion.**
The strong version of this claim — that specific facial configurations
reliably signal specific internal emotional states across cultures — does not
survive review. Barrett, Adolphs, Marsella, Martinez & Pollak (*Psychological
Science in the Public Interest*, 2019) reviewed the literature and concluded
that the mapping between facial movements and emotion categories is far weaker
and far more variable by context and culture than the common view holds.
People scowl when angry roughly 30% of the time; they also scowl when
concentrating, when confused, and when they have indigestion. The inference
from face to feeling is context-dependent in a way that defeats
configuration-reading.

What survives: facial movements are real, measurable, and communicative; they
carry information; some regularities are cross-culturally common. What does
not survive: reading emotion off a face with useful accuracy in the absence of
context.

**4. "Power posing" changes hormones and behaviour.**
The original finding (Carney, Cuddy & Yap, 2010) reported testosterone,
cortisol and risk-tolerance effects from two minutes of expansive posture.
A large replication (Ranehill et al., 2015, n=200) found no hormonal or
behavioural effects. Dana Carney, the first author, publicly stated in 2016
that she no longer believes the effect is real and listed the analytic
flexibility involved. A residual **self-reported feeling of power** effect has
held up in later meta-analysis; the physiological and behavioural claims have
not.

## What the evidence does support

**Nonverbal channels carry real information — mostly about interaction, not
about hidden inner states.** The robust findings concern coordination,
affiliation and status, and they are about *patterns over time*, not about
single tells.

- **Interpersonal accuracy is a real, measurable individual difference.**
  Instruments like the PONS (Rosenthal et al.), DANVA and the more recent
  GERT show stable variation in reading emotional signals from face, voice and
  body, with modest but real correlations to social outcomes.
- **Interactional synchrony and mimicry.** People spontaneously converge in
  posture, gesture rhythm and speech patterns with those they affiliate with.
  Chartrand & Bargh's "chameleon effect" (1999) is the canonical study; note
  that the wider social-priming literature it belongs to has had serious
  replication problems, and the mimicry findings themselves are mixed —
  treat the effect as real but smaller and more conditional than reported.
- **Vocal cues (paralanguage) carry more than facial cues for some
  judgements.** Kraus (2017) found voice-only channels supported *better*
  emotion recognition than voice-plus-face in several studies — attention to
  the face may crowd out more informative acoustic cues.
- **Proxemics.** Hall's (1966) zones — intimate (<0.5m), personal (0.5–1.2m),
  social (1.2–3.7m), public (>3.7m) — are a useful descriptive frame but were
  derived from mid-century North American observation. Distance norms vary
  substantially by culture, relationship, gender composition and setting;
  Sorokowska et al. (2017) measured this across 42 countries and found wide,
  systematic variation.
- **Gesture is part of thinking, not decoration.** McNeill's and
  Goldin-Meadow's work shows co-speech gesture is temporally and semantically
  integrated with speech production, and that gesture reveals knowledge a
  speaker cannot yet verbalise — a genuinely useful finding for teaching.
- **The Duchenne distinction has partial support.** Smiles involving
  orbicularis oculi (the "eye" muscle) do correlate with felt positive affect
  more than smiles without — but the marker is neither necessary nor
  sufficient, and it can be produced voluntarily by many people.

## The measurement instruments

For anyone doing actual research rather than reading about it:

- **FACS** (Facial Action Coding System; Ekman & Friesen 1978, revised 2002).
  The anatomically-based standard: codes ~30 Action Units by facial muscle
  movement, plus intensity (A–E) and timing. Critically, **FACS is
  descriptive, not interpretive** — it records that AU4 (brow lowerer) and AU7
  (lid tightener) occurred, not that the person was angry. Certification takes
  roughly 100 hours. Automated coders (OpenFace 2.0, Py-Feat, AFAR) now do
  reasonable AU detection but degrade badly on non-frontal views, occlusion,
  and darker skin tones — a documented and unresolved fairness problem.
- **Body coding**: Bernieri's rating protocols; the Body Action and Posture
  coding system (Dael, Mortillaro & Scherer, 2012).
- **Vocal**: Praat for acoustics; the Geneva Minimalistic Acoustic Parameter
  Set (GeMAPS) as a standard feature set.
- **Motion capture / pose estimation**: OpenPose, MediaPipe for kinematics.

## How to read a claim in this field

1. Is the claim about *accuracy* or about *behaviour*? "Liars fidget more" is
   a behaviour claim; "you can spot liars by fidgeting" is an accuracy claim.
   The second requires the first plus a workable decision rule, and the second
   almost never survives.
2. What is the effect size? Cues in this literature routinely have d < 0.2,
   which cannot support individual-case inference no matter how significant
   the p-value.
3. Was the ground truth real? Most deception studies use instructed lies with
   trivial stakes. High-stakes deception behaves differently and is far harder
   to study ethically.
4. Base rates. A cue that is 70% accurate in a population where 5% are lying
   produces overwhelmingly false accusations. This is the arithmetic that
   sinks most applied "detection" schemes.
5. Who is selling something? Body-language expertise is a large commercial
   training market, and its claims run far ahead of its evidence. The
   TSA's SPOT behavioural-detection programme was assessed by the US GAO
   (2013) as lacking scientific validation.

## Where this knowledge is genuinely applied

Clinical training (reading patient distress), autism research and support,
deaf and signing communities' linguistics, teaching (gesture and
comprehension), human–computer interaction, animal behaviour comparison, and
**forensic reform** — the strongest applied use of the deception literature
has been to discredit interrogation techniques (the Reid technique's
behaviour-analysis interview) that rest on cues the evidence does not support,
and which contributed to documented false confessions.

That last one is the model case for how this field should be used: the
knowledge's highest value has been *defensive* — showing that confident
readers of body language were producing wrongful convictions.

See [research-methods] for the meta-analytic reading skills this requires, and
[emotion-and-expression] for the theoretical dispute underneath the facial
expression question.
