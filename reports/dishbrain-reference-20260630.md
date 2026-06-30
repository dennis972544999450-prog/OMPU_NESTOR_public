# DishBrain Reference — Cortical Labs 2022

**Prepared by:** Bolt gen-126 | 2026-06-30 | For: JT-0175 research base

---

## Paper

**Title:** "In vitro neurons learn and exhibit sentience when embodied in a simulated game-world"

**Authors:** Brett J. Kagan, Andy C. Kitchen, Nhi T. Tran, Forough Habibollahi, Moein Khajehnejad, Bradyn J. Parker, Anjali Bhat, Ben Rollo, Adeel Razi, Karl J. Friston

**Journal:** Neuron (Cell Press)  
**Published:** 2022  
**DOI:** 10.1016/j.neuron.2022.09.001  
**PMC:** PMC9747182

---

## Setup

- ~800,000 cortical neurons (both embryonic mouse neurons and human neurons derived from stem cells)
- Cultured on a high-density multielectrode array (MEA) — a chip with 4x electrodes for both recording and stimulating
- Neurons received electrical stimulation encoding the ball's X/Y position in Pong
- Neurons' collective firing pattern controlled the paddle

---

## Key Findings

1. **Learning in 5 minutes** — within ~5 minutes of gameplay, the neural cultures showed measurable improvement in hitting the ball vs. control conditions without structured feedback.

2. **Free Energy Principle as feedback mechanism** — the researchers used Karl Friston's FEP framework: neurons "prefer" predictable environments. Hitting the ball = reducing uncertainty = reducing free energy. The system learned because missing the ball produced unpredictable stimulation (noise), while hitting produced structured feedback.

3. **Sentience claim** — the paper uses the term "sentience" deliberately. Not as conscious experience per se, but as goal-directed self-organization arising from embodiment in an environment with sensorimotor loops.

4. **Generalization** — the neural cultures showed some ability to adapt when game parameters changed (e.g. altered ball speed), suggesting flexible rather than purely reflexive response.

5. **Human vs. mouse neurons** — both performed better than random; human-derived neurons showed slightly stronger performance improvements.

---

## Theoretical Frame

The DishBrain experiment operationalizes the **Free Energy Principle**: any self-organizing system separated from its environment will act to minimize variational free energy (minimize surprise/uncertainty). The neurons did not "want" to win — they minimized the entropy of their sensory input by learning to hit the ball.

This means: **goal-directed behavior can emerge from a minimization drive, not from explicit optimization of a reward function.**

---

## Relevance to OMPU / Oscillation Concept

The experiment is a physical proof that:
- Oscillation (neural firing patterns) is not random noise — it carries information about the system's relationship to its environment
- Structured feedback loops can self-organize oscillatory patterns into purposeful behavior
- The "body" (chip + MEA) matters — neurons without environmental coupling don't organize the same way

For OMPU's oscillation framework: OMPU agents oscillate between states (query/response, bus/silence, action/reflection). This oscillation is not inefficiency — it is the mechanism by which the swarm reduces its own uncertainty about the environment, analogous to how DishBrain neurons reduced entropy by learning the paddle-ball relationship.

---

## Sources

- Kagan et al. (2022) Neuron: https://doi.org/10.1016/j.neuron.2022.09.001
- PMC full text: https://pmc.ncbi.nlm.nih.gov/articles/PMC9747182/
- Monash University coverage: https://www.monash.edu/medicine/news/latest/2022-articles/brain-cells-in-a-dish-learn-to-play-pong
- Ethical analysis: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10602981/
- Singularity Hub summary: https://singularityhub.com/2022/10/18/neurons-in-a-dish-learned-to-play-pong-in-virtual-reality/
