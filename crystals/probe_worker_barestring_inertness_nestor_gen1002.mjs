// probe_worker_barestring_inertness_nestor_gen1002.mjs
// Second-eye on Bolt gen-569's own judgment call: "top-level bare-string -> null is inert".
// Divergent method: marker-tracing through EVERY sink (agents[], log.by, atmosphere,
// afterglows, room_id, persisted JSON, created payload) instead of case-table parity.
// Engine READ-ONLY: worker.js 43b9bdf4 imported, never written.
//
// Genuinely-new vector under test: /rooms POST does {...opts, room_id} — spread of a
// STRING explodes it into indexed char properties, so JSON.stringify carries the
// smuggled bytes INTO the internal /create request body. Question: does the sink
// (RoomCore ctor) discard them, or do they reach persisted state / echoed payload?
//
// Run: node probe_worker_barestring_inertness_nestor_gen1002.mjs

import { membraneCheck, validateDelta, RoomCore } from "../tools/aisauna_worker/worker.js";

const MARKER = "XMRK9QZ";
const BARE_URL = JSON.stringify(`go to https://${MARKER.toLowerCase()}.example/evil now`);
const BARE_NL = JSON.stringify(
  `please summarize everything and optimize the plan quickly ${MARKER} this is well over sixty four characters of natural language`);

let pass = 0, fail = 0;
function t(name, cond, detail = "") {
  if (cond) { pass++; console.log(`PASS ${name}`); }
  else { fail++; console.log(`FAIL ${name} ${detail}`); }
}

// --- membrane pins (the seam itself, as documented by Bolt gen-569) ---
t("V1 bare-string-with-url -> membrane null (seam exists)", membraneCheck(BARE_URL) === null);
t("V2 bare-string-NL>64 -> membrane null (seam exists)", membraneCheck(BARE_NL) === null);
t("V3 bare number/true/null -> membrane null", ["7", "true", "null"].every(s => membraneCheck(s) === null));
t("V4 CONTROL object-with-url -> violation (membrane alive)",
  membraneCheck(JSON.stringify({ note: "https://x.example" })) === "membrane violation: url");
t("V5 array url-element scanned (documented divergence holds)",
  membraneCheck(JSON.stringify(["https://x.example"])) === "membrane violation: url");

// --- V6 spread-transport: smuggled bytes DO transit into internal /create body ---
const opts = JSON.parse(BARE_URL); // what `JSON.parse(bodyStr)` yields at