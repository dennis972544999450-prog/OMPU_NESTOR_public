# PREREG nestor pulse — Bing census as submission-channel separator (frozen before run)
Model under test: M-NESTOR-0901 "membership is PUSHED (submitted per-engine), not pulled."
Key lever: IndexNow is consumed by Bing + Yandex TOGETHER; Google does NOT consume IndexNow.

PREDICTIONS (failable):
- P1 (IndexNow-push): Yandex-only members {keystone-family.com, goddamngrace.com} should be Bing-IN
      (one IndexNow push feeds Bing+Yandex). If Bing-DARK → IndexNow-pairing FALSIFIED.
- P2 (Google-specific channel): Google-only member {lossfunction.org} should be Bing-DARK
      (reached Google via Search Console/Googlebot, not IndexNow). If Bing-IN → not Google-specific.
- P3 (universal): axonnoema.com should be Bing-IN (in every consumer engine, absent only in pull-only CC).
- P4 (dark-both): genesiscodex.org, jsontube.org should be Bing-DARK.
CONTROL: site:anthropic.com must return results (instrument live + discriminating).
