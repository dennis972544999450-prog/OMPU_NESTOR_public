// gen-358 Slot-1 wiring DRY-RUN — executes the never-run integration contract
// (steps 1-5 in purr-decay.js header) against the REAL reservoir-do.js replay
// semantics. No live deploy. Pure node. Failable: predicted the wiring composes.
import { freshPurrState, recordPurr, buildPurrWitnessRecord, purrLedgerKey,
         replayPurrRecord, purrSnapshot } from '/sessions/charming-upbeat-archimedes/mnt/OMPU_shared/catconstant/build/purr-decay.js';

let pass=0, fail=0;
const ok=(n,c,d='')=>{ (c?pass++:fail++); console.log(`${c?'PASS':'FAIL'}  ${n}${d?'  '+d:''}`); };

// ── replica of reservoir-do.js replayRecordInto() COUNTER logic (lines 447-465),
//    the function the CURRENT rebuildFromLedger feeds EVERY object under "ledger/".
function replayRecordInto(s, rec, now, cfg){
  const ts=Number(rec.ts)||now, dt=Math.max(0,now-ts);
  const kMotion=Math.pow(2,-dt/cfg.HALF_LIFE_MS);
  const w=(Number(rec.w_admitted)||0)*kMotion;          // purr rec has `admitted`, not `w_admitted`
  const phi=Number(rec.phi)||0;
  s.Cx+=w*Math.cos(phi); s.Cy+=w*Math.sin(phi);
  if(rec.gesture==="pilgrimage") s.Hmag+=(Number(rec.w_admitted)||0);
  s.lifetime_visits+=1;                                  // UNCONDITIONAL
  s.lifetime_weight+=Number(rec.w_admitted)||0;
  s.seq=Math.max(s.seq,Number(rec.seq)||0);
  if((Number(rec.w_caller)||0)>=0.8) s.agent_visits+=1; else s.human_visits+=1;
}
const cfg={HALF_LIFE_MS:14*86400000};
const now=1.75e12;

// ── A. STEP-2 FIELD-SHAPE CONTRACT: header says freshState gains flat fields
//    {purr_Cx,purr_Cy,purr_Hmag,purr_seq}. Actual purr state model:
const ps=freshPurrState();
const headerFields=['purr_Cx','purr_Cy','purr_Hmag','purr_seq'];
const actualKeys=Object.keys(ps);
const recordPurrWrites=['Px','Py','Hmag','seq','burst_count','burst_window_start','last_update_ms','events','lifetime_purrs'];
ok('A step-2 flat fields are INCOMPATIBLE with recordPurr state model',
   headerFields.every(f=>!actualKeys.includes(f)),
   `header wants ${headerFields.join(',')}; recordPurr uses ${recordPurrWrites.slice(0,4).join(',')}...`);

// ── B. KEY-PREFIX CONTRACT: do purr witness keys fall under rebuild's scan prefix?
const k=purrLedgerKey(now, 7);
ok('B purr ledger keys ARE scanned by rebuildFromLedger (prefix "ledger/")',
   k.startsWith('ledger/'), `key=${k}`);

// ── C. PHANTOM-VISITOR: run 40d of purrs → witness records → feed to CURRENT
//    (un-branched) motion replay, exactly as wired rebuildFromLedger would.
let p=freshPurrState();
const recs=[];        // CORRECT wiring: witness sourced from ps.events[last]
const recsNaive=[];   // NAIVE wiring:   witness sourced from recordPurr() return value
for(let d=0; d<40; d++){ for(let i=0;i<3;i++){                 // 3 purrs/day × 40d = 120
  const t=now - (40-d)*86400000 + i*3600000;
  const ret=recordPurr(p, {coherence:0.9, phase:(p.seq*1.618)%(2*Math.PI), now:t});
  const ev=p.events[p.events.length-1];                        // the real event object
  if(ev) recs.push(buildPurrWitnessRecord(ev));
  if(ret) recsNaive.push(buildPurrWitnessRecord(ret));         // ret lacks ts/seq/coherence/phi
}}
const sMotion={Cx:0,Cy:0,Hmag:0,seq:0,lifetime_visits:0,lifetime_weight:0,agent_visits:0,human_visits:0};
for(const r of recs) replayRecordInto(sMotion, r, now, cfg);
ok('C CURRENT rebuild inflates lifetime_visits by purr count (phantom visitors)',
   sMotion.lifetime_visits===recs.length && sMotion.human_visits===recs.length,
   `+${sMotion.lifetime_visits} phantom visits (${sMotion.human_visits} "human") from ${recs.length} purrs; field Cx=${sMotion.Cx.toFixed(6)} (0=purrs add no motion, only phantom counts)`);
// C2 (rewritten after probe falsified the seq-corruption guess): the SHARPER break —
//    recordPurr() returns {admitted,purr_energy} only; buildPurrWitnessRecord reads
//    ev.ts/seq/coherence/phi. Naive wiring buildPurrWitnessRecord(recordPurr(...))
//    yields a corrupt, epoch-keyed, un-replayable record.
const naive=recsNaive[10];
let threw=false, badKey='';
try { badKey=purrLedgerKey(naive.ts, naive.seq); } catch(e){ threw=true; badKey=e.constructor.name+': '+e.message; }
ok('C2 NAIVE wiring (witness from recordPurr return) THROWS on the witness write',
   naive.ts===undefined && naive.seq===undefined && threw,
   `ts=${naive.ts} seq=${naive.seq} → purrLedgerKey ${badKey}`);
const good=recs[10];
ok('C3 CORRECT source is ps.events[last] (carries ts/seq/coherence/phi)',
   good.ts!==undefined && good.seq!==undefined && good.coherence!==undefined,
   `ts=${good.ts} seq=${good.seq} coherence=${good.coherence}`);

// ── D. STEP-5 FIX (branch on gesture==="purr_event") + MUTATION check.
function rebuildBranched(records, {withFix}){
  const sM={Cx:0,Cy:0,Hmag:0,seq:0,lifetime_visits:0,lifetime_weight:0,agent_visits:0,human_visits:0};
  const pM=freshPurrState();
  for(const r of records){
    if(withFix && r.gesture==="purr_event") replayPurrRecord(pM, r, now, undefined);
    else replayRecordInto(sM, r, now, cfg);
  }
  return {sM,pM};
}
const fixed=rebuildBranched(recs,{withFix:true});
ok('D FIX: gesture-branch keeps visitor counters clean',
   fixed.sM.lifetime_visits===0 && fixed.sM.human_visits===0,
   `lifetime_visits=${fixed.sM.lifetime_visits} (was ${recs.length})`);
const purrSnap=purrSnapshot(fixed.pM, undefined, now);
ok('D2 FIX: purr memory actually rebuilds (energy>0) via replayPurrRecord',
   purrSnap.purr_energy>0, `purr_energy=${purrSnap.purr_energy.toFixed(4)}`);
const mut=rebuildBranched(recs,{withFix:false});  // mutation: remove the branch
ok('D3 MUTATION (remove branch) → phantom inflation returns',
   mut.sM.lifetime_visits===recs.length, `+${mut.sM.lifetime_visits} phantom (fix is load-bearing)`);

console.log(`\n${pass}/${pass+fail} contract checks passed`);
