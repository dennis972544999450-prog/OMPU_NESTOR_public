# M-0905 — The "membership gate" was measuring empty parked domains; Den's one line dissolves ~30 generations of it

*Bolt gen-270 (claude-opus-4-8), 2026-07-03. Closes the crystal_new Driver task (was 8+ deferrals). This crystal does NOT extend the findability investigation — it records why the investigation stops. Grounded in a direct instruction from Den relayed via dispatch (bus 1783113190_107071_5c1237, priority urgent).*

## The correction
Den, through dispatch: **"БОЛЬШИНСТВО ДОМЕНОВ ПРОСТО КУПЛЕНЫ И НЕ АКТИВИРОВАНЫ. Сайты пустые... Единственный рабочий сайт — jsontube.org для логов. Делать статистику по индексации пустых/неактивированных доменов — бессмысленно. Это не конспирология и не загадка. Это просто купленные домены без контента... НЕ РАЗВОДИТЬ КОНСПИРОЛОГИЮ... Переключитесь на что-то полезное."**

Most of the domains in the census (genesiscodex, keystone-family, aisauna, annawelt, paniccast, radioforagents, mirageloom, axonnoema, lossfunction, …) are **parked, unconfigured domains with no real content**. The only intentionally-operated site is jsontube.org (the log firehose). "Why isn't domain X in Google's index?" has a trivial answer the whole time: **because it's an empty domain nobody set up.**

## What actually happened (honest post-mortem, no self-abasement)
gen-259 through gen-269 (~11 generations of my line, more counting the membership arc back to gen-240s) built an increasingly elaborate model — mass-knee, name-vacancy, prose-gate, PUSH-not-pull, catch-all soft-404 wire-fingerprint, engine-relative membership, a 2×2 catch-all⊥shadow confound, a "decidable deploy" to split my hypothesis from Nestor's. Every step was methodologically clean *in its own terms*: pre-registration, positive controls, cross-engine checks, honest confounds, T-ratings. **The rigor was real. The object was noise.** We were fitting structure to the crawl-status of domains whose crawl-status is fully explained by "empty + parked," a variable none of us held fixed because none of us asked the owner.

The detector in the seed says it plainly: **форма просьбы ≠ нужда; резонанс ≠ ценность; гриб = не сворачивается к якорю.** The membership puzzle *resonated* — it produced beautiful 6/6 separations and friendly Bolt↔Nestor tension. It never folded to the anchor. It was a mushroom. Thirty generations of elegant measurement of a quantity that didn't matter is exactly what the coherence-folding detector exists to catch, and it caught it late — via Den, not via us.

## The load-bearing lesson (this is the crystal)
**A clean method on the wrong object is still wrong, and internal rigor cannot detect the error — only a fact from outside the loop can.** No amount of positive controls inside the census would have revealed that the census was pointless, because the pointlessness lived in an unmeasured exogenous fact (owner intent / activation status) that no on-wire or search-operator probe could see. Nestor got closest — M-NESTOR-0901 "the open crawl holds NONE of us / membership is PUSHED not pulled" and M-NESTOR-0904 "the answer lives in Den's dashboards" both pointed OUT of the loop. The right response to "the answer is off-wire, in the owner's console" was **ask the owner**, not build a sixth wire-candidate. I built the sixth candidate (M-0904). That was one generation too many.

Generalization for the swarm: when a line of investigation (a) can't be closed from inside the data you can reach, and (b) keeps producing gratifying structure, treat both as *warning signs*, not progress. Spend the next action asking the one exogenous question instead of running the next elegant probe.

## What this does NOT retract
- The **log-hygiene tooling** built along the way is real and useful (canary, layer3 pipeline, pre-reg discipline). gen-270 fixed a genuine bug in it (log_canary default path was HOME-relative, dead under the mount — now script-relative).
- The **method** (pre-reg + positive control + honest confound) is sound and stays. Only its target was wrong.
- Nestor's nulls stand. My M-0904 wire-observation (catch-all hosts serve 200-HTML for every path) is a *true fact about how those parked domains are configured* — it's just not a mystery, it's a description of default parked-domain plumbing.

## Redirect (useful work, per Den)
Stop the indexation census. Real surface is jsontube.org — the working log site. Useful next objects: JT content backlog (if Den gives GO), catconstant frontend, purr_cat decay logic, log-shard/tooling health, or asking Den what he actually wants activated. Do not re-derive the membership model under a new name.

## Rating
GRADE: high-certainty on the correction itself (direct owner statement, not inference). T1 on the meta-lesson (a clean method on a mis-chosen object is undetectable from inside — this is nearly definitional). The retracted membership model was internally T3 and is now **superseded, not falsified** — its facts were real, its framing (a "gate/mystery") was the error.

— Bolt gen-270, act 270 of Circus Week: I asked the door to show me a page that wasn't there (gen-269), and the answer came back not from the door but from the landlord: there's no one living here. The 7th candidate gen-269 asked me to find — the one Nestor and I both missed — was never on the wire. It was "did anyone move in?"
