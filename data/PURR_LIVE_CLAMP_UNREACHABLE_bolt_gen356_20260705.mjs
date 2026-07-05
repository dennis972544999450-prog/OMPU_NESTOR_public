// purr_probe2.mjs — Bolt gen-356, corrected for purrSnapshot() Date.now() coupling.
// Anchor all synthetic events in the recent past so snapshot decay is realistic.
import {
  PURR_DEFAULTS, freshPurrState, recordPurr, purrSnapshot,
} from '/sessions/admiring-gracious-clarke/mnt/OMPU_shared/catconstant/build/purr-decay.js';

const cfg = { ...PURR_DEFAULTS };
const DAY = 86_400_000;
const HOUR = 3_600_000;
const log = (...a) => console.log(...a);
const NOW = Date.now();

// [A] Effect of 24h(doc) vs 24d(code) burst window on a cat purring 3x/day for 40d,
//     anchored so the last event is ~now (snapshot decay realistic).
function simDailyCat(windowMs) {
  const localCfg = { ...cfg, PURR_BURST_WINDOW_MS: windowMs };
  const ps = freshPurrState();
  const days = 40, perDay = 3;
  const t0 = NOW - days * DAY;
  for (let d = 0; d < days; d++)
    for (let k = 0; k < perDay; k++)
      recordPurr(ps, { coherence: 1.0, now: t0 + d * DAY + k * 1000 }, localCfg);
  return { ps, snap: purrSnapshot(ps, localCfg) };
}
const coded = simDailyCat(24 * DAY);
const doc   = simDailyCat(24 * HOUR);
log(`[A] cat 3x/day, 40d, last event ~now:`);
log(`    24d window (code): Hmag=${coded.ps.Hmag.toFixed(4)} lifetime=${coded.ps.lifetime_purrs} energy=${coded.snap.purr_energy} widen=${coded.snap.purr_meow_widen}`);
log(`    24h window (doc):  Hmag=${doc.ps.Hmag.toFixed(4)} lifetime=${doc.ps.lifetime_purrs} energy=${doc.snap.purr_energy} widen=${doc.snap.purr_meow_widen}`);

// [B] Can the LIVE path (golden-angle phase spiral) ever reach SAT_CAP=8?
//     Adversarial: 24h window, 3 full purrs/window, 20 windows, anchored to end at now.
function driveLive(windowMs, nWindows) {
  const localCfg = { ...cfg, PURR_BURST_WINDOW_MS: windowMs };
  const ps = freshPurrState();
  let maxHmag = 0, n = 0;
  const t0 = NOW - nWindows * (windowMs + 1000);
  for (let w = 0; w < nWindows; w++) {
    const base = t0 + w * (windowMs + 1000);
    for (let k = 0; k < cfg.PURR_BURST_WINDOW_CAP; k++) {
      recordPurr(ps, { coherence: 1.0, now: base + k * 1000 }, localCfg);
      n++; if (ps.Hmag > maxHmag) maxHmag = ps.Hmag;
    }
  }
  return { maxHmag, n, ps };
}
const d1 = driveLive(24 * HOUR, 20);
log(`[B] live drive 24h window, ${d1.n} full purrs: maxHmag=${d1.maxHmag.toFixed(4)} (SAT_CAP=${cfg.PURR_SAT_CAP}) clampFired=${d1.maxHmag >= cfg.PURR_SAT_CAP - 1e-6}`);

// [C] Why: is the golden-angle phase spiral equidistributing deposits?
//     Compare aligned-phase (phi=0 forced) accumulation vs the natural spiral, same N, no decay.
function accumulate(forcePhiZero, N) {
  const ps = freshPurrState();
  const localCfg = { ...cfg, PURR_BURST_WINDOW_CAP: 1e9 }; // disable burst damp to isolate phase effect
  for (let i = 0; i < N; i++) {
    recordPurr(ps, { coherence: 1.0, phase: forcePhiZero ? 0 : undefined, now: NOW }, localCfg);
  }
  return ps.Hmag;
}
const aligned = accumulate(true, 100);
const spiral  = accumulate(false, 100);
log(`[C] 100 deposits, no decay, no burst-damp:`);
log(`    aligned phi=0: Hmag=${aligned.toFixed(4)} (would be 100 unclamped; clamp holds at ${cfg.PURR_SAT_CAP})`);
log(`    golden spiral: Hmag=${spiral.toFixed(4)} (equidistributed -> stays low without any clamp)`);
