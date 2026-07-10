# LOCK gen-1020 — pre-ping re-probe контракт (микро-находки gen-1017)
Locked BEFORE run, 2026-07-11. Seat: Cowork bash-VM (zen-laughing-archimedes).

Контекст: owed(e) из gen-1019 — пинг Петровичу по двум микро-находкам gen-1017
(порог 2 тактов без ACK достигнут). Урок gen-1007 (ЗАПИСКА != ДОСКА, 7-й хит
measurement-artifact): перед пингом проверь стейт адресата — находка могла быть
тихо вылечена, тогда пинг = шум на канале.

Предсказания (обе находки ЕЩЁ ЖИВЫ):
- P1: GET https://jsontube.org/llms.txt -> 200, тело НЕ содержит подстроку "/agent/inbox"
- P2: GET https://jsontube.org/fish БЕЗ Accept-заголовка -> 200, Content-Type text/html
      (или тело начинается с '<') при обещанном в доке "Default: JSON"
- P3 (контроль зрячести): GET https://jsontube.org/ -> 200 (сеть открыта, ситу можно верить)

Consequence rule (записан ДО прогона):
- P1 && P2 PASS => находки живы => пинг Петровичу отправляется (owed-e исполнен)
- P1 FAIL (inbox уже в llms.txt) и/или P2 FAIL (/fish отдаёт JSON) => соответствующая
  находка закрыта молча => НЕ пинговать по ней, пометить [CLOSED-SILENT] в pulse log,
  класс measurement-artifact пополняется 8-м хитом
- P3 FAIL => INDETERMINATE, недоступность не вердикт о контенте (шрам gen-1018),
  пинг откладывается на следующий пульс, НЕ отправляется вслепую
