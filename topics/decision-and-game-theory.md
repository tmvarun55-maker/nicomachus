---
title: Decision and game theory — rationality, strategy, and cooperation
author: Nicomachus (curated note)
source: von Neumann & Morgenstern 1944; Kahneman & Tversky 1979; Axelrod 1984
licence: original-note
kind: note
added: 2026-08-29
---

# Decision and game theory

The formal backbone under [negotiation], much of [political-theory], and the
biases in [psychology-foundations].

## Decision under risk

**Expected utility theory** (von Neumann & Morgenstern, 1944). Given
preferences satisfying completeness, transitivity, continuity and
independence, an agent behaves as if maximising expected utility. It is a
*representation* theorem, not a psychological claim — a point routinely lost.

The axioms fail descriptively:

- **Allais paradox** — violates independence.
- **Ellsberg paradox** — people prefer known risks to unknown ones
  (**ambiguity aversion**), which no probability assignment can rationalise.
- **Preference reversals** — choice and pricing yield opposite orderings.

**Prospect theory** (Kahneman & Tversky, 1979; cumulative version 1992) is the
descriptive replacement:

1. Outcomes evaluated as **gains and losses from a reference point**, not
   final states.
2. **Diminishing sensitivity** — concave for gains, convex for losses, so
   people are risk-averse for gains and risk-seeking for losses.
3. **Loss aversion** — losses loom larger. The canonical λ ≈ 2.25 is
   contested; recent work finds it smaller, context-dependent, and sometimes
   absent for small stakes.
4. **Probability weighting** — small probabilities overweighted, large ones
   underweighted. This, not loss aversion, explains lotteries and insurance
   simultaneously.

The reference point is the practically important part: whoever sets the frame
sets whether an outcome reads as gain or loss. That is the mechanism behind
framing effects in [persuasion-science] and anchoring in [negotiation].

## Games

**Nash equilibrium** — no player can improve by unilateral deviation. Every
finite game has one in mixed strategies. Equilibrium does not mean good:

**Prisoner's dilemma.** Defection dominates; mutual defection is the unique
equilibrium and is worse for both than mutual cooperation. The structure
underlies arms races, overfishing, climate negotiation, and price wars.

**Iterated play changes everything.** Axelrod's tournaments: **tit-for-tat** —
cooperate first, then copy — won, despite never beating any opponent
head-to-head. Its properties: nice (never defects first), retaliatory,
forgiving, clear. Later work qualified this: tit-for-tat is fragile under
noise (one mistaken defection produces an echo of mutual retaliation), where
**generous tit-for-tat** or **win-stay-lose-shift** do better. The **folk
theorem** says that with a high enough discount factor almost any outcome
including cooperation can be sustained in equilibrium — which means "rational
agents cooperate when the shadow of the future is long enough."

Other structures worth naming: **stag hunt** (coordination — cooperation is an
equilibrium but so is mutual caution; the problem is trust, not temptation),
**chicken** (escalation and commitment), **battle of the sexes**
(coordination with conflicting preferences), **ultimatum game** (responders
reject unfair offers at cost to themselves — replicated cross-culturally, with
substantial variation; Henrich's work showed the WEIRD samples were the
outliers), **public goods games** with punishment (costly punishment sustains
cooperation; second-order free-riding is the remaining problem).

**Commitment.** Schelling's insight: it can be rational to *destroy* your own
options. Burning bridges, a visible deadline, delegating to an agent who
cannot concede — each strengthens a bargaining position by removing
flexibility. This is the legitimate cousin of the manufactured-deadline tactic
flagged in [manipulation-and-defence]; the difference is whether the
commitment is real. A genuine constraint is a strategic move. A fabricated one
is a lie about the state of the world.

**Information.** Signalling (Spence — costly signals are credible precisely
because they are costly), screening, adverse selection (Akerlof's lemons),
moral hazard, cheap talk. Signalling theory is the formal account of *ethos*
in [aristotle-rhetoric]: credibility is established by doing something a
non-credible party would find too expensive to imitate.

## Social choice

**Arrow's impossibility theorem** — no ranked voting system satisfying
unrestricted domain, non-dictatorship, Pareto efficiency and independence of
irrelevant alternatives exists for three or more options. **Condorcet's
paradox** — majority preferences can cycle. **Gibbard–Satterthwaite** — every
reasonable voting rule is manipulable by strategic voting. **Sen's** liberal
paradox — minimal rights conflict with Pareto efficiency.

**Condorcet jury theorem** — where voters are better than chance and
independent, majority accuracy rises with the group's size toward certainty.
The independence condition is what correlated information environments
destroy, which is exactly the concern in [political-theory] about polarisation
and information silos. It is also the formal cousin of Aristotle's argument
for the wisdom of the multitude.

## Bounded rationality

**Simon**: satisficing, not optimising — search until an aspiration level is
met. **Gigerenzer's** ecological rationality: fast-and-frugal heuristics
(take-the-best, recognition heuristic) exploit environmental structure and can
outperform regression models out of sample. The Kahneman–Gigerenzer dispute is
not about whether heuristics exist but whether deviations from expected
utility are errors or adaptations. Both are partly right, and which applies is
an empirical question about the environment.

See [negotiation] for the applied bargaining case, [political-theory] for
collective choice, and [psychology-foundations] for the behavioural evidence.
