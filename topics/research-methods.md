---
title: Reading the evidence — methods, the replication crisis, and how to judge a claim
author: Nicomachus (curated note)
source: Open Science Collaboration 2015; Ioannidis 2005; Simmons et al. 2011
licence: original-note
kind: note
added: 2026-08-29
---

# How to judge a psychological claim

This note comes before the content notes in importance. Most of what a
student will encounter about human behaviour is overstated, and the skill of
discounting it correctly is more valuable than any individual finding.

## What happened

**Ioannidis (2005), "Why Most Published Research Findings Are False."** A
formal argument that in fields with small studies, small effects, many tested
relationships, flexible designs and strong incentives, the majority of
published positive claims will be false — driven by the base rate of true
hypotheses tested, not by fraud.

**Simmons, Nelson & Simonsohn (2011), "False-Positive Psychology."** Showed by
simulation and demonstration that ordinary, undeclared analytic flexibility —
choosing when to stop collecting data, which covariates to include, which of
several measures to report, which conditions to combine — raises the
false-positive rate from 5% to over 60%. They coined *p-hacking* and
*researcher degrees of freedom*, and demonstrated the point by "proving" that
listening to a song made people younger.

**The Reproducibility Project (Open Science Collaboration, *Science*, 2015).**
100 replications of studies from three top psychology journals. 97% of the
originals reported significant results; 36% of the replications did.
Mean effect size fell by roughly half. Social psychology fared worse than
cognitive psychology.

**Many Labs and multi-lab replications** since have confirmed the pattern for
specific effects: ego depletion (null), facial feedback (null in the
pre-registered multi-lab test, though later work with different methods is
mixed), power posing (physiological claims null), most social priming (null).
Some effects survived robustly — anchoring, for instance.

## The reforms that followed, and which to look for

- **Pre-registration** — hypotheses, design and analysis plan filed before
  data collection (OSF, AsPredicted). Converts an exploratory finding into a
  confirmatory test. A pre-registered null is worth more than an
  unregistered significant result.
- **Registered Reports** — peer review of the *protocol*, with in-principle
  acceptance before results exist. This is the strongest single reform,
  because it removes the incentive to find something. Registered Reports
  produce null results roughly 60% of the time, against under 10% in the
  conventional literature — a stark measure of how much publication bias was
  operating.
- **Open data and materials.**
- **Larger samples / power analysis.** Classic social psychology studies were
  routinely powered around 20–40%. To detect a typical social-psychology
  effect (d ≈ 0.4) at 80% power needs about 100 per cell, not 20.
- **Effect sizes and confidence intervals reported, not just p-values.**

## A working checklist

1. **Effect size, not significance.** Cohen's rough conventions: d = 0.2
   small, 0.5 medium, 0.8 large; r = .1/.3/.5. Ask what the effect means in
   the units of the world — "1.9% less energy used", not "p < .001".
2. **Sample size and power.** Under ~50 per condition on a between-subjects
   social psychology design, treat as a pilot.
3. **Pre-registered?** If not, the reported p-value is not the real one.
4. **Replicated by an independent lab?** Same-lab replication is much weaker
   evidence than independent replication.
5. **Sample composition.** Henrich, Heine & Norenzayan (2010) showed the
   literature is dominated by WEIRD samples — Western, Educated,
   Industrialised, Rich, Democratic — which are outliers on many measures
   including visual illusion susceptibility, fairness in economic games, and
   moral reasoning. A finding from US undergraduates is a finding about US
   undergraduates until shown otherwise.
6. **Lab or field?** Effects routinely shrink or vanish when moved to the
   field with real stakes.
7. **Self-report or behaviour?** The gap between attitude measures and
   behaviour is one of the field's oldest problems.
8. **Who funded it, and is there a book?** Not disqualifying, but a reason to
   check the primary source rather than the summary.
9. **Publication bias in the meta-analysis.** Look for funnel plots, trim-and-
   fill, p-curve or PET-PEESE. A meta-analysis without bias correction can
   confidently average a literature of false positives — this is what happened
   with the original ego-depletion meta-analysis.

## Statistical points that repeatedly matter

- **A p-value is not the probability the hypothesis is true.** It is the
  probability of data at least this extreme if the null were true. The
  inversion is the most common error in popular science writing.
- **Non-significant does not mean no effect** — especially in an underpowered
  study. Absence of evidence, evidence of absence: only equivalence tests or
  Bayes factors distinguish them.
- **The difference between significant and non-significant is not itself
  significant** (Gelman & Stern, 2006). Comparing two studies by whether each
  crossed threshold is invalid.
- **Regression to the mean** explains a great deal of apparent intervention
  success when selection was on an extreme score.
- **Base rates** defeat most applied screening and detection schemes.
- **Garden of forking paths** (Gelman & Loken) — p-hacking need not be
  conscious; the analysis choices a researcher *would have made* under other
  data are enough.

## Free tools worth knowing

- **OSF** (osf.io) — pre-registration, data, materials.
- **Semantic Scholar, OpenAlex, Crossref, CORE, DOAJ, Unpaywall** — open
  bibliographic and full-text access.
- **PubMed / PMC** — biomedical and much of psychology.
- **Cochrane Library** — the standard for clinical evidence synthesis.
- **Retraction Watch database** — check before citing.
- **Stanford Encyclopedia of Philosophy** — free, peer-reviewed, and the
  single best philosophy reference in existence.
- **Curate Science / Replication Index** — replication status of specific
  findings.

## The honest summary for a student

Psychology is not broken; it is one of the few fields that audited itself in
public. But the audit's findings mean that any confident, dramatic,
counter-intuitive claim about human behaviour published before roughly 2015
and not since replicated should be held loosely — including several in the
textbooks. Approach it the way Aristotle approached his predecessors: take the
phenomena seriously, and the explanations provisionally.
