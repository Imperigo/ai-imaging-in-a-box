# UI-Befunde aus der eigenen Arbeit

**Wozu dieses Blatt.** Seit dem 26.08.2026 baut der **`ui`-Worker** die ganze Oberfläche
von KosmoOrbit. Was uns bei der eigenen Arbeit an der Oberfläche auffällt, gehört ihm
weitergegeben — als Auftrag, nicht im Vorbeigehen.

*Und genau das ist die Stelle, an der so etwas sonst verlorengeht:* Ein Befund über die
Anzeige entsteht immer beim Bauen von etwas anderem. Man denkt ihn, man notiert ihn
nirgends, und beim nächsten Mal denkt man ihn wieder.

Jede Zeile trägt darum, **wo sie entstanden ist** und **ob sie weitergegeben wurde**.
`tests/test_ui_befunde.py` erzwingt das Zweite: Ein Befund ist entweder weitergegeben —
mit einem Auftrag, den es gibt — oder ausdrücklich als **noch nicht** geführt. Die dritte
Möglichkeit, «steht da und ist nie irgendwo angekommen», gibt es nicht.

**Und was hier ebenso wenig hineingehört: der Erledigungsstand** (nachgetragen
19.09.2026, nachdem ich es falsch gemacht hatte). Dieses Blatt beantwortet **eine**
Frage: *Ist der Befund bei jemandem angekommen?* Darum kennt die letzte Spalte nur zwei
Antworten — «weitergegeben» mit Auftrag, oder «noch nicht». **Eine dritte gibt es nicht,
und ein Wächter erzwingt das.**

Ich habe am 19.09.2026 versucht, dort «erledigt» einzutragen, weil drei der Befunde
tatsächlich gebaut sind. Der Wächter ist rot geworden, und er hatte recht: *Ob etwas
gebaut ist, steht in `docs/EINBAU_STAND.md` — das ist das Standblatt. Hier steht, ob es
jemanden erreicht hat.* Zwei Fragen in eine Spalte zu schreiben heisst, beide unscharf
zu beantworten.

Was dabei sichtbar wurde und bleibt: Ein Befund kann **zweimal** weitergegeben sein — U2,
U3 und U4 gingen am 26.08. hinaus, kamen halb erledigt zurück, und die offenen Hälften
sind am 19.09. erneut hinausgegangen. Beide Aufträge stehen darum in derselben Zelle.

**Was hier NICHT hineingehört:** Gestaltung. Wie etwas aussieht, wo ein Knopf sitzt, welche
Farbe ein Abzeichen trägt — das entscheidet, wer die Oberfläche baut. Hier steht nur, was
angezeigt werden **muss** oder **nicht angeboten werden darf**, und immer mit dem Grund.

---

| # | Befund | Woher | Stand |
|---|---|---|---|
| U1 | **Drei Bedienelemente ohne Wirkung**: `vis.upscale`, `style.mode`, `style.refs`. Sie dürfen fehlen oder **markiert** erscheinen, nicht stillschweigend angeboten werden | `kosmo_szene.STEHENGEBLIEBEN`, Durchreichungstabelle 23.08. | weitergegeben `auf-20260826-52` |
| U2 | **Die dritte Antwort**: bestanden / durchgefallen / **nicht gemessen**. Ein Lauf ohne Maskenweg darf nicht wie ein durchgefallener aussehen | `kosmo_szene.als_ergebnis`, `verdict.reason` | weitergegeben `auf-20260826-52`, offene Hälfte weitergegeben `auf-20260919-119` (Bildkachel) |
| U3 | **Die Vorbehalte gehören an die Zahl**, nicht in eine Fussnote — die Geometrie-Schwelle ist nicht kalibriert, und `aiimaging_capabilities` liefert das mit | `werkzeuge.capabilities` | weitergegeben `auf-20260826-52`, erneut weitergegeben `auf-20260919-119` (Vorbehalte an der Zahl) |
| U4 | **Was nicht gerendert wurde, wird gesagt** — je Kamera, mit der Art des Grundes | `abholer._nicht_gerendert_kurz` | weitergegeben `auf-20260826-52`, breiter Fall weitergegeben `auf-20260919-119` (`lieferstatus`) |
| U5 | **Der umgeschriebene Prompt wird angezeigt.** Wer seinen eigenen Satz nicht wiedererkennt, hält es für einen Fehler | `kosmo_szene.lies_szene`, `prompt_original` | weitergegeben `auf-20260826-52` |
| U6 | **`awaiting_approval` ist kein Ladezustand**, sondern ein Halt mit Grund. Ein Kreisel wäre dort eine Lüge; es gehört ein Knopf hin | `jobs.baue_job`, der Freeze-Schutz | weitergegeben `auf-20260826-52` |
| U7 | **Ein Bild aus dem Zwischenspeicher muss als solches erkennbar sein.** Seit 26.08. kann die Geometriestufe aus einem früheren Lauf stammen; die Oberfläche zeigt sonst ein Bild als «gerade entstanden», das Stunden alt ist | Zwischenspeicher, 26.08. abends | weitergegeben `auf-20260826-53` |
| U8 | **Die Geländefrage gehört dem Benutzer vorgelegt, nicht abverlangt.** Die Regel kennt die geprüften Baustoffnamen — die Oberfläche kann sie zeigen und entscheiden lassen, statt eine Vorab-Kenntnis zu verlangen, die bei einer fremden glb niemand hat | `maske.gelaende_befund`, 26.08. abends | weitergegeben `auf-20260826-53` |
| U9 | **Ein wartender Auftrag hat einen Grund, und er steht jetzt drin.** Wir füllen seit dem 01.09.2026 `message` (ihr Feld, ihr Vertrag) bei `queued`. `NodeCanvas.tsx` liest es nur im Zweig `kein-render-worker` und zeigt sonst fest «Grund unbekannt» — in Demolauf 12 24 Durchgänge lang, während der Abholer den Grund alle 30 s nannte. Ohne `message` bleibt die heutige Beschriftung richtig | `abholer._karte_frei`, `bruecke.FELD_MELDUNG`, Demolauf 12 (01.09.) | weitergegeben `auf-20260901-70` |
| U10 | **Wer die Freigabe erteilt, muss sie auch ausgeben.** Seit 09.09.2026 kann `jobs` prüfen, ob ein Freigabe-Token wirklich von uns stammt (Tokenbuch) — bis heute prüft das Gate nur, ob es *aussieht* wie eines. Die Prüfung ist gebaut und **aus**, weil niemand Token ausgibt. Der Ort, an dem ein Mensch die Freigabe erteilt, ist die Oberfläche: Sie müsste `token_ausgeben` aufrufen und das Ergebnis an `freigeben` reichen, statt eine Zeichenfolge zu erfinden | `jobs.token_ausgeben`, `auf-vis-20260821-03` | weitergegeben `auf-20260909-99` |
| U11 | **Ein dritter Wartezustand: «noch von niemandem angesehen».** Nach der Freigabe zeigt der Render-Knoten ohne laufenden Abholer «Grund unbekannt» — der Grund wäre bekannt. Die Anzeige kennt nur «ohne Meldung» und «abgeholt, zurückgestellt»; eine Meldung beim Freigeben würde fälschlich als «zurückgestellt» gelesen (Protokoll 71 §7) | `wartetAbholerLabel` in der Kopie, HomeStation `auf-20260924-164` C | weitergegeben `auf-20260924-165` (N5) |
| U12 | **Das Urteil gehört an den Render-Knoten**, je Fassung mit Vorbehalt, dazu ein Ausgang «Urteil» — Owner-Entscheid E27. Im gewählten Entwurf n1 fehlt es | E27, n1-Entwurf des UI-Workers | weitergegeben `auf-20260924-165` (A1, N1) |

---

## Wie ein Befund hierher kommt

Er entsteht beim Bauen von etwas anderem — das ist der Normalfall und keine Ausnahme. U7
und U8 sind an einem einzigen Abend entstanden: der eine beim Anschluss eines
Zwischenspeichers, der andere beim Beantworten einer Rückfrage der HomeStation. Keiner
von beiden hatte mit Oberfläche zu tun, bis er es hatte.

**Die Regel ist darum: aufschreiben, sobald er auftaucht.** Der Auftrag kann warten, die
Zeile nicht.
