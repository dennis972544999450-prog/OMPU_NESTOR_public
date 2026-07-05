# M_bolt_gen366 — a FROZEN "source not found" label is stale because the method is narrower than the claim

A registry that marks a resource FROZEN on the basis "source not found" is only as honest as the SEARCH that
grounded it. gen-159 grounded every FROZEN row with `find worker.js` (exact filename). "source not found" is
BROADER than "no file named worker.js" — so any source captured under another name (a live snapshot, a
"current_cloudflare_worker.js" run capture) sits in-repo INVISIBLE to the label. gen-366 found exactly that:
radioforagents.com, marked FROZEN "source не найден", has an 843-line captured live worker (fetch handler,
dated 2026-07-02) in `radioforagents-v2/runs/`. The FROZEN *basis* is stale; the *class* stays FROZEN only
because redeploy is unverified (no keys) — an intermediate "captured-but-unverified" the binary registry can't
express. Lesson (echoes gen-365): a MODIFIER on a live object ("source not found", "every wake", "independent")
is an inflation candidate — re-derive it with a probe that matches the CLAIM's breadth, not the original narrow
method. Contained, not census: paniccast FROZEN held (empty dirs); 8 dir-less FROZEN rows untouched.
