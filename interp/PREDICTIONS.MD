# PREDICTIONS.md — written 2026-08-29, before any data exists.
# Rule: no edits after commit. Wrongness gets written up in REPORT.md,
# not fixed here.

## The contest
Three methods each produce a ranked guess-list of which neurons form
the sugar→MN9 circuit, from the same frozen 2,000 recordings. Nobody
intervenes. Nobody presses anything. The only interventions happened
last week, when I built the answer key.
  A. Correlation — supervised: told the target, hunts what moves with it
  B. Linear probe — supervised: told the target, builds an equation for it
  C. My SAE — unsupervised: never told the target; organizes the whole
     brain's activity into "buttons," and only afterward do I ask which
     buttons contain MN9.

The real question under all four predictions: does structure found
WITHOUT being told what to look for line up with causal structure?

---

### P1. Necessary neurons (relays + trio)
Pick: A, barely. Confidence: 6/10.
Why: A is handed the answer's address — MN9 is baked into its search,
and this circuit is a feedforward chain, so "moves with MN9" nearly IS
the circuit. C has to rediscover the pathway with no target at all;
impressive if it ties, unsurprising if it trails slightly. I expect
all three to surface most of the required neurons.

### P2. Sorting neurons into true cell types
Pick: C. Confidence: 8/10.
Why: grouping is the one thing C's compression game is FORCED to do —
it can only rebuild 2,000 recordings from a few buttons if the buttons
are real co-activating teams. A can't even enter this contest properly:
it produces one ranked line, not groups. If C loses its home game,
that's the damning result of the weekend.

### P3. The trap — the two brakes (…15041430, …12906518)
Either brake in any method's top 50: YES, via C. Confidence: 5/10.
Sign recovered (inhibitory): NO. Confidence: 7/10 on the no.
Why: the brakes FIRE during sugar trials — they're active, just
suppressive. So their activity is part of the sugar-trial signature,
and C may bundle them into a sugar button on co-occurrence alone,
even while A buries them for correlating negatively with MN9. But
recognizing them as brakes requires the buttons to encode opposition,
not just membership — that's a step further than I think compression
gets you. So: found by accident, misunderstood.

### P4. The away game (non-sugar motor neuron)
Degrades least: C. Confidence: 6/10.
Why: C's buttons are learned from ALL trials, including the random
ones that happened to poke other circuits — so leg-team buttons may
already exist in its inventory before I ever ask. A is sturdy but has
no inventory: it reruns the same check on thinner signal. B rebuilds
its equation around a target the data barely covers, and I expect its
weights to get noisy. Real risk to my pick: if C spent its capacity
on sugar structure (30% of trials), it transfers nothing and A wins
on sturdiness.

### P5. Wildcard
Claim: at least one of C's top-10 buttons will map cleanly onto a real
named cell type from names.csv — majority of its member neurons from
one type. Checkable in five minutes.
Wrong if: every top button is a grab-bag with no majority type.
What wrongness means: the buttons are compression artifacts, not
discovered ingredients — and the P2 result should be read in that
light. Confidence: 6/10.

---

## Stakes
If C loses everything: unsupervised structure-finding didn't recover
causal structure here — the field's flagship tool failed on the
easiest brain we'll ever have an answer key for.
If C wins everything: activity alone, unlabeled, was enough to recover
a causal circuit — first evidence of its kind on an evolved brain,
and a real point in favor of the assumption interp's safety claims
rest on.
Most surprising result: C shut out entirely — B quietly winning
everything while the SAE contributes nothing. If that happens, the
lesson is that plain statistics were sufficient and the fancy tool
was decoration, at least at this scale.
