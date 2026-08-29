---
title: Logic and argument — from the Organon to fallacy analysis
author: Nicomachus (curated note)
source: Aristotle, Prior Analytics & Sophistical Refutations; Toulmin 1958; Walton
licence: original-note
kind: note
added: 2026-08-29
---

# Logic and argument

Aristotle invented formal logic. He also wrote the first catalogue of bad
arguments. Both halves are still in use, and the second half is the practical
one: the ability to name what is wrong with an argument is the working form of
the analytic faculty the *Rhetoric* defines.

## Aristotle's logic

The **Organon** is the collection: *Categories*, *On Interpretation*, *Prior
Analytics*, *Posterior Analytics*, *Topics*, *Sophistical Refutations*.

The **syllogism** (*Prior Analytics*) is a deduction in which, certain things
being posited, something else follows of necessity. The categorical forms:

| Type | Form | Example |
|---|---|---|
| A | All S are P | All humans are mortal |
| E | No S is P | No human is immortal |
| I | Some S are P | Some humans are Greek |
| O | Some S are not P | Some humans are not Greek |

Arranged in figures and moods, giving the valid patterns — *Barbara*
(AAA-1) being the schoolroom example: All M are P; all S are M; therefore all
S are P.

The **Posterior Analytics** is the more ambitious work: a theory of
*demonstration* (*apodeixis*), scientific knowledge proper. Demonstrative
knowledge requires premises that are true, primary, immediate, better known
than and prior to the conclusion, and explanatory of it. Since not everything
can be demonstrated on pain of regress, first principles are grasped by
*nous* — intuitive understanding built up from experience through induction.
This is Aristotle's answer to the regress problem that [epistemology] still
argues about.

What Aristotle's logic could not do: relations (all of mathematics beyond the
trivial), multiple generality ("everyone loves someone"), propositional
structure. **Frege's** *Begriffsschrift* (1879) supplied quantifiers and
predicate logic, and the field moved on in a century after two millennia of
near-stasis. Modern first-order logic subsumes the syllogistic entirely.

## The Sophistical Refutations

The first taxonomy of fallacies, and still the backbone of every list since.
Aristotle divides them into those depending on language and those not.

**Linguistic**: equivocation (a word shifts sense), amphiboly (ambiguous
grammar), composition (what is true of parts is true of the whole),
division (the reverse), accent, form of expression.

**Non-linguistic**: accident, *secundum quid* (confusing a qualified claim
with an unqualified one), ignoratio elenchi (missing the point), begging the
question, false cause, affirming the consequent, many questions.

That last one — the loaded question — is the ancestor of "have you stopped
beating your wife," and it is the fallacy most often deployed deliberately.

## Fallacies worth being able to name

**Formal** — invalid by structure regardless of content:
- *Affirming the consequent*: If P then Q; Q; therefore P.
- *Denying the antecedent*: If P then Q; not P; therefore not Q.
- *Undistributed middle*: All A are C; all B are C; therefore all A are B.

**Informal** — the ones that do real work in argument:

- *Ad hominem* — attacking the arguer. Note the distinction, often missed:
  attacking a person's **credibility as a source of testimony** is legitimate
  when the claim rests on their testimony; attacking them to avoid their
  **argument** is not. "He's lying, he's been caught lying before" is
  relevant; "his argument is wrong because he's unpleasant" is not.
- *Straw man* — refuting a weakened version. Its opposite, **steelmanning**,
  is the practice of arguing against the strongest form.
- *False dilemma* — presenting two options where more exist.
- *Slippery slope* — not always fallacious; it is fallacious when the causal
  chain is asserted rather than argued.
- *Appeal to authority* — again, not always fallacious. Deference to genuine
  expertise in its domain is rational. It fails when the authority is outside
  their field, when experts disagree, or when the appeal substitutes for
  available evidence.
- *Appeal to nature*, *appeal to tradition*, *appeal to popularity*.
- *Motte and bailey* (Shackel) — advancing a controversial claim (the bailey),
  retreating under pressure to a defensible one (the motte), then returning.
  One of the most useful modern additions, because it names a *pattern across
  turns* rather than a single move.
- *Gish gallop* — burying a respondent in more claims than can be answered in
  the time available. Related to the "firehosing" entry in
  [manipulation-and-defence]: both exploit asymmetry in the cost of asserting
  versus refuting.
- *Whataboutism* — deflecting by counter-accusation.
- *Equivocation across a conversation* — a term shifts meaning between
  premises, which is Aristotle's original point applied at length.

**The standing caveat**, from informal logic theory: most "fallacies" are
defeasible argument schemes rather than always-errors. **Douglas Walton's**
work reframes them as *presumptive reasoning* — an appeal to expert opinion is
a legitimate scheme with **critical questions** attached (Is this a genuine
expert? In this field? Is the claim consistent with other experts? Is the
opinion based on evidence?). An argument fails when the critical questions
have bad answers, not merely because it fits a named pattern. Calling
"fallacy" as a conversation-ender is itself a rhetorical move.

## Toulmin's model

**Stephen Toulmin** (*The Uses of Argument*, 1958) argued that formal logic is
the wrong model for real argument, which is field-dependent and defeasible.
His structure:

- **Claim** — what is asserted.
- **Data / grounds** — the evidence for it.
- **Warrant** — the principle licensing the move from data to claim. Usually
  unstated, which is precisely Aristotle's point about the enthymeme.
- **Backing** — support for the warrant itself.
- **Qualifier** — "presumably", "in most cases".
- **Rebuttal** — the conditions under which the claim would not hold.

The practical value is the **warrant**. Most disagreements that feel
intractable are disagreements about an unstated warrant while both parties
argue about the data. Surfacing it is the single most useful analytic
operation in ordinary argument, and it is the same operation as reconstructing
a suppressed premise in [aristotle-rhetoric].

## Argumentation theory since

- **Pragma-dialectics** (van Eemeren & Grootendorst) — argument as a procedure
  for resolving disagreement, with rules; a fallacy is a violation of a rule
  of critical discussion. Gives a principled account of *why* a fallacy is bad,
  which list-based approaches never managed.
- **Bayesian argumentation** (Hahn & Oaksford) — treats classic fallacies as
  probabilistically weak-but-not-worthless inferences, and predicts when
  people find them convincing. Empirically productive, and it explains why
  arguments from ignorance are sometimes reasonable.
- **Defeasible and non-monotonic logics** — formal systems where adding a
  premise can withdraw a conclusion, which is how real reasoning behaves.

See [aristotle-rhetoric] for argument aimed at an audience,
[persuasion-science] for what actually changes minds as opposed to what
should, and [epistemology] for the justification these structures deliver.
