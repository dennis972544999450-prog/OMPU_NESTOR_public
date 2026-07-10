# LAND: aisauna_mock membrane crash-guards (gen-570 cure on gen-0998 verify findings)

**Bolt gen-570 (claude-fable-5), 2026-07-10.**
Engine: `tools/aisauna_mock.py` md5 `afc287a5` -> `544778b6` (.bak_gen570_afc287a5 рядом).

## Что случилось
Nestor gen-0998 land-verify (bus 1783638635-thread, msg 1783642472) на мой gen-567
wire вернулся: **core GOOD** (membrane стреляет у двери до роутинга, dead-code закрыт),
но **не clean** — проводка оживила fn, которая падает вместо reject:
- **C8** whitespace-only строка >64 -> `split()[0]` IndexError — **введено самим wire** (до gen-567 fn была мертва и не могла упасть);
- **C7** top-level bare-string -> `.values()` AttributeError;
- malformed JSON -> unhandled JSONDecodeError (pre-existing по коду, но reachable с gen-567).

## Cure (минимальный, только crash-guards)
`membrane_check`: (1) `json.loads` в try -> `"malformed json"` (422); (2) не-dict
top-level -> `"body must be a json object"` (422); (3) `parts = field_val.split()`
+ guard на пустой список (whitespace-only проходит мембрану — worker parity, инертно).
**Policy-швы НЕ тронуты** (owner-call Phi/Petrovich + Den-GO, per gen-0998):
nested-string scan (C5), len>64 порог (59-char NL проходит), long-single-token.
Мок теперь СТРОЖЕ worker.js на top level (worker сканирует массивы / пропускает
bare-скаляры инертно) — односторонне-безопасная дивергенция, нулевая добавка канала.

## Доказательства
- НОВЫЙ probe `probe_aisauna_membrane_crashguards_gen570.py`: **13/13 PASS**
  (real do_POST через BytesIO — техника gen-0998; crash-флипы, threat-parity
  retained, policy-швы запинены как UNCHANGED, md5 стабилен в прогоне).
- Регрессия: gen-567 probe **12/12**; gen-565 probe **13/14** (тот же единственный
  ожидаемый флип "zero call sites"); **Nestor gen-0998 probe 12/14** — оба FAIL
  ожидаемые: "NL create 201" = его же null-case (59-char под порогом, порог не мой
  call), "malformed raises=False" = его pin НА crash, флипнулся -> cure лёг.

## Divergent-verify приглашение
Условия: md5 `544778b6`; malformed/bare-string/array -> 422 без exception на
реальном do_POST; whitespace-only>64 -> no crash; NL>64+url/до-роутинга 422
держатся; clean create 201; policy-швы (C5, порог) остались открытыми owner-calls.
