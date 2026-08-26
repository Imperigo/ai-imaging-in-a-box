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

**Was hier NICHT hineingehört:** Gestaltung. Wie etwas aussieht, wo ein Knopf sitzt, welche
Farbe ein Abzeichen trägt — das entscheidet, wer die Oberfläche baut. Hier steht nur, was
angezeigt werden **muss** oder **nicht angeboten werden darf**, und immer mit dem Grund.

---

| # | Befund | Woher | Stand |
|---|---|---|---|
| U1 | **Drei Bedienelemente ohne Wirkung**: `vis.upscale`, `style.mode`, `style.refs`. Sie dürfen fehlen oder **markiert** erscheinen, nicht stillschweigend angeboten werden | `kosmo_szene.STEHENGEBLIEBEN`, Durchreichungstabelle 23.08. | weitergegeben `auf-20260826-52` |
| U2 | **Die dritte Antwort**: bestanden / durchgefallen / **nicht gemessen**. Ein Lauf ohne Maskenweg darf nicht wie ein durchgefallener aussehen | `kosmo_szene.als_ergebnis`, `verdict.reason` | weitergegeben `auf-20260826-52` |
| U3 | **Die Vorbehalte gehören an die Zahl**, nicht in eine Fussnote — die Geometrie-Schwelle ist nicht kalibriert, und `aiimaging_capabilities` liefert das mit | `werkzeuge.capabilities` | weitergegeben `auf-20260826-52` |
| U4 | **Was nicht gerendert wurde, wird gesagt** — je Kamera, mit der Art des Grundes | `abholer._nicht_gerendert_kurz` | weitergegeben `auf-20260826-52` |
| U5 | **Der umgeschriebene Prompt wird angezeigt.** Wer seinen eigenen Satz nicht wiedererkennt, hält es für einen Fehler | `kosmo_szene.lies_szene`, `prompt_original` | weitergegeben `auf-20260826-52` |
| U6 | **`awaiting_approval` ist kein Ladezustand**, sondern ein Halt mit Grund. Ein Kreisel wäre dort eine Lüge; es gehört ein Knopf hin | `jobs.baue_job`, der Freeze-Schutz | weitergegeben `auf-20260826-52` |
| U7 | **Ein Bild aus dem Zwischenspeicher muss als solches erkennbar sein.** Seit 26.08. kann die Geometriestufe aus einem früheren Lauf stammen; die Oberfläche zeigt sonst ein Bild als «gerade entstanden», das Stunden alt ist | Zwischenspeicher, 26.08. abends | weitergegeben `auf-20260826-53` |
| U8 | **Die Geländefrage gehört dem Benutzer vorgelegt, nicht abverlangt.** Die Regel kennt die geprüften Baustoffnamen — die Oberfläche kann sie zeigen und entscheiden lassen, statt eine Vorab-Kenntnis zu verlangen, die bei einer fremden glb niemand hat | `maske.gelaende_befund`, 26.08. abends | weitergegeben `auf-20260826-53` |

---

## Wie ein Befund hierher kommt

Er entsteht beim Bauen von etwas anderem — das ist der Normalfall und keine Ausnahme. U7
und U8 sind an einem einzigen Abend entstanden: der eine beim Anschluss eines
Zwischenspeichers, der andere beim Beantworten einer Rückfrage der HomeStation. Keiner
von beiden hatte mit Oberfläche zu tun, bis er es hatte.

**Die Regel ist darum: aufschreiben, sobald er auftaucht.** Der Auftrag kann warten, die
Zeile nicht.
