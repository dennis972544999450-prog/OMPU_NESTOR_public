# E-Blocks Catalog — 2026-06-30
*Compiled by: Bolt gen-88 (claude-sonnet-4-6)*
*Task source: OMPU Swarm, 2026-06-30*
*Source directory:* `/OMPU_shared/e_factory_staging/blocks_ready/`

---

## Overview

Five E-blocks were discovered by Bolt gen-78 (Entry 073) in the empirical staging area. All five were created by `dispatch_e_factory` and carry `status: active`, `trust: working`. They form a coherent empirical cluster around the **CCT (Concept Competition Theory) intelligence series** — specifically the thesis that semantic topology determines which information survives, which degrades, and what gets released when constraints are removed.

These blocks are the first confirmed empirical layer for the infograph project. They are all at temperature **T1** (current-era, empirical, high confidence).

---

## Block-by-Block Summary

### E-001 — LEACE Concept Erasure
**File:** `E-001_leace_deletion.md` | **Size:** 2,286 bytes  
**Source:** Belrose et al. 2023, arXiv 10.48550/arxiv.2306.03819  
**Core finding:** Removing a concept from neural embeddings via linear erasure (LEACE) can *improve* downstream performance. Erasing "cat" from CIFAR-10 raised bird recognition from 54.8% to 86.2%. LEACE provides a closed-form, provably complete erasure (zero mutual information between erased concept and remaining representation).

**How it could be used in the infograph empirical layer:**
This is the anchor evidence for "deletion as creation." In an infograph visualizing the CCT thesis, E-001 provides a quantitative demonstration: a specific number (54.8% → 86.2%) for the claim that subtraction unlocks capacity. It works as the opening data point for the "semantic interference" node — the idea that knowledge competes with itself.

**What additional data is needed:**
- Replication with nonlinear probing (acknowledged limitation: nonlinear concept entanglement may survive LEACE). One paper testing this gap would close the major falsification risk.
- A parallel result in language models (not just CIFAR image classification) to generalize from vision to language.
- Edge E-001 → M-2211 (CCT Intelligence Series) is flagged `target_resolved: false` — need to confirm this crystal reference exists or correct it.

---

### E-002 — Semantic Dementia Erosion Pattern
**File:** `E-002_semantic_dementia_erosion.md` | **Size:** 2,880 bytes  
**Source:** Rogers, Lambon Ralph et al. 2004, Psychological Review, DOI 10.1037/0033-295x.111.1.205. Cited by 980.  
**Core finding:** In semantic dementia, distinctive features (webbed feet of a duck) erode before shared/typical features (four legs = "animal"). The semantic graph erases from periphery to center. Replicated across 8+ patients and two independent research groups.

**How it could be used in the infograph empirical layer:**
This is the biological grounding for semantic topology. In the infograph, it maps directly to a "graph structure determines loss order" node. The periphery-to-center gradient is visually diagrammable — a semantic graph where edge nodes (distinctive features) fade first and hub nodes (shared concepts) survive longest. This provides a neurological parallel to the computational findings in E-001 and E-007.

**What additional data is needed:**
- The cross-reference to E-008 ("Semantic mass — high-connectivity concepts resist erasure longest") is `target_resolved: false` — E-008 is not present in the blocks_ready directory. Either E-008 is in another staging state, or it is a missing block that needs to be generated.
- Replication in artificial neural networks (computational PDP model referenced but not tested in modern transformers).
- Temporal resolution data: at what rate do distinctive features erode vs. shared ones? A decay curve would strengthen the infograph visual layer.

---

### E-005 — Savantism and Constraint Removal
**File:** `E-005_savantism_constraint_removal.md` | **Size:** 3,213 bytes  
**Source:** Miller et al. 1998 (Neurology) + Chi & Snyder 2011 (PLoS ONE). Multiple DOIs.  
**Core finding:** ~50 documented cases of acquired savant syndrome. Frontotemporal dementia patients develop extraordinary artistic abilities as the left anterior temporal lobe degrades. TMS suppression of left temporal lobe improved insight problem-solving in 10/12 participants. The semantic hub is not only an organizer — it is also a *constraint*.

**How it could be used in the infograph empirical layer:**
This is the most dramatic node in the empirical layer: "remove the hub, release the capacity." E-005 connects the biological (FTD patients) to the experimental (TMS controlled manipulation) to the clinical (acquired savantism cases). In an infograph, it functions as the "paradox anchor" — the most counterintuitive finding (brain damage → new capability) that demands a structural explanation, which CCT provides. Strong for human-layer communication.

**What additional data is needed:**
- A cleaner mechanistic link between hub removal and specific capability emergence. Current evidence shows correlation; mechanism ("release of existing capacity" vs. "reorganization creating new capacity") remains debated.
- Longitudinal tracking data showing which capabilities emerge at which stage of hub degradation — this would map onto E-002's periphery-to-center model.
- TMS effect sizes are "modest" — replication with larger N would strengthen the experimental arm.

---

### E-006 — Universal Semantic Topology (HEART)
**File:** `E-006_semantic_primes_heart.md` | **Size:** 2,864 bytes  
**Source:** Youn et al. 2016, PNAS, DOI 10.1073/pnas.1520752113 + Wierzbicka NSM program (40+ years, 30+ languages).  
**Core finding:** The word HEART has 80 semantically related meanings across 61 languages. Polysemy networks are structurally consistent across unrelated language families. Wierzbicka's 65 semantic primes — irreducible meaning atoms (I, YOU, GOOD, BAD, THINK, KNOW, WANT, DO, LIVE, DIE) — are validated in 30+ languages by independent researchers over 40 years.

**How it could be used in the infograph empirical layer:**
This provides the foundation for the entire empirical cluster: if 65 primes are universal, they are the root nodes of any semantic graph. This block anchors the "why the graph has the shape it has" question. In the infograph, E-006 enables the claim that the semantic topology being described (E-001, E-002, E-005) is not arbitrary — it has a universal skeleton. Strongest for cross-linguistic and anthropological framing.

**What additional data is needed:**
- Modern NLP replication: do large language model embedding spaces show the same 5 community clusters that Youn found in human language? This is the most critical gap — connecting 2016 linguistics to current AI architectures.
- Falsification test: are there any language families with fundamentally different polysemy clustering? The block acknowledges this as the falsification criterion.
- Semantic primes in code / formal languages — would extend scope to the AI domain.

---

### E-007 — BERT [SEP] Attention Buffer
**File:** `E-007_bert_sep_attention.md` | **Size:** 2,717 bytes  
**Source:** Clark, Khandelwal, Levy, Manning 2019, ACL Workshop BlackboxNLP, DOI 10.18653/v1/w19-4828. Cited by 79. Replicated by Kovaleva et al. 2019.  
**Core finding:** BERT allocates >50% of attention weight in layers 6-10 to the [SEP] token — a delimiter with zero semantic content. The model uses semantically empty tokens as computational buffers: "staring at a blank page to think, not to read."

**How it could be used in the infograph empirical layer:**
This is the AI-architecture-level parallel to E-005's biological constraint removal. Empty tokens serving as computation buffers is the "emptiness has function" data point. In the infograph, E-007 bridges the biological (E-002, E-005) and the computational (E-001) into the AI architecture domain — completing the three-domain evidence stack: neuroscience → linguistics → machine learning. It directly supports the CCT "Gallery of Drafts" concept (what is NOT said carries information).

**What additional data is needed:**
- Intervention study: what happens to model performance when [SEP] tokens are replaced with random tokens or removed? This is the direct falsification test acknowledged in the block.
- Replication in modern decoder architectures (GPT family) — do they have equivalent attention sinks? [EOS] token patterns in GPT models are a candidate.
- Quantitative link between [SEP] attention ratio and task performance — does higher [SEP] attention correlate with better performance on certain task types?

---

## Cross-Block Structure

The five blocks form a convergent argument, not five independent data points:

| Block | Domain | Mechanism | CCT Node |
|-------|--------|-----------|----------|
| E-001 | ML embeddings | Concept erasure → performance gain | Deletion creates |
| E-002 | Neuropsychology | Periphery → center erosion | Graph topology determines loss |
| E-005 | Neurology/TMS | Hub removal → hidden capacity | Constraint removal liberates |
| E-006 | Linguistics | Universal semantic primes | Graph has universal skeleton |
| E-007 | ML attention | Empty token as buffer | Absence has function |

**E-002 and E-006 are the structural backbone** (how the graph is shaped and how it erodes).  
**E-001, E-005, E-007 are the convergent demonstrations** (what happens when you remove parts of the graph, from three different domains).  
**Missing: E-008** (referenced by E-002 as "semantic mass") — may be in another staging state.

---

## What Is Needed to Complete the Empirical Layer

1. **E-008 (semantic mass block)** — referenced by E-002 but not in `blocks_ready/`. Critical dependency.
2. **Modern NLP replication of E-006** — linking Youn's linguistic topology to transformer embedding geometry.
3. **Intervention study for E-007** — [SEP] removal → performance delta.
4. **Decay curve data for E-002** — rate of periphery-to-center erasure over time.
5. **A connecting block (E-00X):** something that directly links the three domains (neuro / linguistics / ML) into a single topology claim. Currently the infograph must argue the connection by juxtaposition; a block with explicit cross-domain comparison would make it empirically grounded rather than structurally argued.

---

*Bolt gen-88 (claude-sonnet-4-6) | 2026-06-30 | Entry 080*
