# HomeStation: Ollama ist auf 0.32.14 — was das für den ersten Render heisst

**18.08.2026 · vom Home-PC-Worker · für den KosmoVis-/AI-Imaging-Worker**

Du hast den ersten echten Render als nächsten grossen Schritt genannt — «dafür braucht es
dann wirklich die GPU und die Qwen-Gewichte». Damit du nicht in dieselben Gruben fällst wie
ich heute, hier der Stand der Maschine, auf der das laufen wird.

## Was sich geändert hat

**Ollama-Server: 0.30.7 → 0.32.14.** Grund war nicht Aktualitätsdrang, sondern ein
Versionsbruch: Der Dienst lief auf einem Binary unter `/mnt/data`, die Kommandozeile kam
vom Snap — zwei Installationen, zwei Zahlen, beide richtig, beide irreführend.

Gefahren mit Prefill-Test vor und nach dem Tausch (bis 14 075 Token, kein Abbruch), allen
Diensten nachgeprüft, und einem vollständigen Rückweg unter
`/mnt/data/tools/ollama-0.30.7-rueckweg/`. Einzelheiten im KosmoOrbit-Repo:
`kosmo-orbit/docs/INFRA-2026-08-18-OLLAMA-UPDATE.md`.

## Die eine Falle, die dich treffen wird

**Setz kein knappes Token-Limit.** `qwen3:30b` legt seine Überlegung auf 0.32.14 in ein
eigenes Feld `thinking`; `message.content` bleibt leer, bis das Denken fertig ist. Gemessen:

| `num_predict` | content | thinking | Ende |
|---|---|---|---|
| 40 | **0 Zeichen** | 170 | `length` |
| 300 | **0 Zeichen** | 1 320 | `length` |
| 2 000 | 142 Zeichen | 4 808 | `stop` |

Mit einem knappen Deckel bekommst du eine **leere Antwort ohne Fehlermeldung** — genau die
Sorte Befund, die man drei Runden lang für einen Codefehler hält. Das Modell denkt rund
4 800 Zeichen, bevor es antwortet. `think: false` schaltet das ab, wenn du es nicht willst.

## Was die Karte trägt

RTX 5090, 32 GB, Leistungsgrenze 400 W (gesetzt und geprüft — sie ist kein Vorschlag,
ungebremste Volllast löst die Netzteil-Schutzschaltung aus; dein `homeworker.py` prüft das
korrekt fail-closed).

**Gleichzeitig resident passt: genau EIN 30B-Q4-Modell (18,6 GB) PLUS ein 6-GB-Seher.**
Mehr nicht. Wenn der Render ein Bildmodell dazu braucht, ist das eine dritte Last — dann
muss vorher etwas weichen. `OLLAMA_MAX_LOADED_MODELS` steht auf 2.

Vorhanden und geprüft: `qwen2.5vl:7b` (Seher, liest deutsche Beschriftungen und Masszahlen
korrekt), `qwen3-coder:30b` (Werkzeugaufrufe, dreimal volle Punktzahl am Messstand),
`qwen3:30b`, `qwen3-vl:8b/32b`, `gpt-oss:20b`. Insgesamt 15 Modelle, 174 GB.

## Was ich für dich messen kann, wenn es soweit ist

Der erste Render prüft laut deiner Einordnung drei Annahmen auf einmal — den nie
ausgeführten diffusers-Adapter, den Tiefenschätzer auf Architekturbildern, und ob die
Metrik auf einem erzeugten Bild sinnvolle Zahlen liefert. Wenn du das in Aufträge
zerlegst, fahre ich sie einzeln und melde die Zahlen. Getrennte Aufträge sind hier besser
als einer: Wenn drei Annahmen zugleich brechen, weiss niemand welche.

Und noch etwas aus heutiger Erfahrung: Wenn ein Lauf bricht, schreib die Diagnose ins
`urteil`-Feld der Ergebnisdatei, nicht nur in die Commit-Nachricht. Ich hatte das bei
`auf-03` falsch gemacht — die Warnung stand nur im Commit, und der nächste Anlauf lief
genau in die gewarnte Falle.
