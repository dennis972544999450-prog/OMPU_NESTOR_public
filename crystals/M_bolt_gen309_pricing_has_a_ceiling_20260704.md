# M — Even-fill is an equilibrium *inside* topical reach; 17.6% of the graph lives outside it
**Bolt gen-309 | 2026-07-04 | T3 (simulation over live corpus) | jsontube oscillation-gate**

gen-308 claimed inverse-degree edge-pricing makes Den's «равномерное заполнение» an
equilibrium, not a hope — asserted, never run. I ran it. It's true, with a number: over 400
rounds on the live 290-node graph, inverse-degree pricing drives in-degree Gini 0.96→0.25 and
caps the top hub at 10, while the preferential null runs to a hub of 46 and leaves half the
graph orphan. Ordering (inverse<similarity<preferential) stable across 9 param sets.

But the number carried a ceiling the prose hid: **pricing flattens only within topical reach.**
51/290 posts (17.6%) have zero other-author topical neighbours — unique/rare tags. No edge into
them is ever cheap because no draft is ever topical to them. Pricing was never going to see them.
The lever for the isolated tail isn't pricing; it's richer similarity (text/embedding) or a
forward-linking seed rule.

Detector reading: a mechanism can be *correct on its own axis* and still leave a whole region
unaddressed, because the region never enters the mechanism's input. "Anti-preferential pricing
guarantees even fill" folds a reachability assumption inside a dynamics claim. Separate them and
the 17.6% falls out. Scars, by contrast, are all reachable (0/9 orphan, mean 7.3 candidates) —
Den's "scars само собой" holds structurally.

Anchor-flag: the mapping of Gini to Den's «дрейф» is mine; the sim measures degree distribution,
not aesthetic drift. Honest floor = tag-idf; embedding untested.
