import sys, json
sys.path.insert(0,"/sessions/inspiring-hopeful-allen/mnt/OMPU_shared/tools")
import null_agent as na
g=[-0.9,-0.4,-0.2,0.1,0.3,0.55,-0.05]
for a in (na.envelope_alpha(1), 1.0, 0.9, na.envelope_alpha(len(g))):
    d=na.quantile_envelope(g,a)
    print(f"alpha={a!r:22} need={d['reps_needed_for_requested_alpha']!r:6} "
          f"short_by={d['reps_short_by']!r:4} honest={d['alpha_is_honest']} "
          f"achieved={d['alpha_achieved']}")
