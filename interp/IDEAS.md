D1: D1 is a detective that's intentionally not smart. It's meant to be a loop. Here's the loop it follows: Make a suspect list. Run correlation on the recordings, for free. Sort neurons by "moves with MN9." Top of the list = first suspects. Cost so far: 0 experiments.
Test the top suspect. Silence it. Drive sugar. Read MN9. Cost: 1 experiment.
Record the verdict. MN9 dropped a lot → mark "required." MN9 rose → mark "brake." No change → mark "innocent."
Update the list. Simple rule, for example: if the suspect was innocent, also push its close co-movers down the list, since they likely ride the same signal. If required, pull its strongest partners up.
Go to step 2. Repeat until the budget is gone.
Output: the marked list. Every mark is backed by a real lesion

It's very logical in the sense that the correlation with MN9 gives it a starting order. Then we're marking the suspects and we're getting a verdict
D2: D2 is the one that looks into emergence. The chooser is an LLM agent with access to run_exp.

It reads the results so far.
It forms an idea: "these three look like a chain; if I cut the middle, both readouts should drop."
It designs the next experiment itself. It can do things D1's recipe never will: test pairs, vary the input rate, chase a hunch, abandon a dead end.
It explains its choices in words as it goes.

This is meant to test the emergence versus the logical proceeding and see if it can do the same work I did on its own

## How D gets scored (different sport than A/B/C)
A/B/C only watch, so they're graded on their ranked lists. D acts, so
with enough budget it trivially rederives the whole answer key — that's
literally how I built it. So D's score is EFFICIENCY: fraction of the
true circuit correctly marked, as a curve over budget (10 / 50 / 200
experiments). D1 and D2 get identical budgets and identical moves; the
only difference is who chooses the next experiment.

## Why D1 exists
D1 is the yardstick. If the 50-line loop marks the circuit in 30
experiments, D2 must beat 30 or the LLM added nothing over a shopping
list. Never run D2 without D1's floor established first.

## The brake, inverted
The trap that blinds every watching method is transparent to an acting
one: silence a brake and MN9 jumps UP (I measured 2.41x). Any D that
reaches a brake in its list gets the verdict for free — intervention
sees suppression directly. Prediction P6 (sealed in PREDICTIONS.md):
D-class methods find the brakes AND their sign; observational methods
don't.

## D2's cheating problem
The fly papers are in training data. D2 "discovering" G2N_1 could be
recall, not science. Fix: degree-preserving rewired variant connectomes,
simulated fresh — same statistics, no paper describes them, answer key
computed by me via exhaustive lesions and kept private. Variant brains
are REQUIRED for any D2 claim; on the real connectome D2 is only a demo.
Second control: run D2 once on the real brain and once on a variant —
if it's much better on the real one, that gap measures the recall.

## Cost & guardrails
D1: electricity only, seeded, resumable — same rules as any sim.
D2: API tokens + my review; runs with a hard experiment budget and
logs every call. D2 competes with effort-atlas for my supervision
attention, which is the real cost.

## Trigger conditions (so this doesn't scope-creep)
Build D1 only after the A/B/C weekend ships REPORT.md.
Build D2 only after D1 works AND the October decision says the
benchmark grows. If A/B/C results are boring, D1 alone may still be
worth one evening — the brake-inversion result stands on its own.:?
