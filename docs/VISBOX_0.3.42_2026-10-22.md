# Visbox 0.3.42 — Fassungsblatt (22.10.2026)

**Codestand:** Fassung 0.3.42 auf `main` (Folgen aus Ergebnis 336); Vorgänger 0.3.41 = Tag `v0.3.41`

**Grundlage:** Ergebnis 336; Protokoll 74 §252–§253; Einbau-Stand C171 (erledigt), C172, C173; Entscheide 117a, 126.
Abgeglichen gegen alle Änderungen seit `v0.3.41` (`git log v0.3.41..` ohne Zusammenführungen).

Visbox zählt selbst (Entscheid 66): Bibliothek `aiimaging`, iPad-App und Mac-App tragen dieselbe Nummer
(`tests/test_versionsnummer.py`). Dieses Blatt ist der Text der Freigabe auf GitHub; die Mac-App zeigt daraus die
Zeilen des Abschnitts «Was neu ist».

## Warum 0.3.42

Messung 336 zeigte abends eine Stufe zwischen der sonnigen Geländeplatte und dem Boden dahinter, und sie zeigte, dass
die KI-Variante im Haus frei malt, statt vom gerechneten Grundbild auszugehen.

## Was neu ist (mit Entscheid und Stand)

| Fähigkeit | Entscheid | Stand |
|---|---|---|
| Abends wird der Boden zum Horizont hin so hell wie die Platte — die Stufe an der Plattenkante wird kleiner; mittags unverändert | 126 | gebaut, mit Probe; Messung 338 offen |
| Das Ergebnis sagt, wie das KI-Bild entstanden ist (vom Grundbild aus oder frei gemalt, wie viel neu gemalt), mit Warnung bei frei gemaltem Haus | 117a | gebaut, mit Probe; Messung 337 offen |

## Stand am Gerät

* **Mac:** Update-Knopf.
* **Heim-PC:** `git pull`, Dienst und Abholer neu starten; dann Aufträge 337 und 338. Bestellungen mit sichtbarem Himmel
  rechnen einmal ein neues Grundbild.

## Bekannte Grenzen (schlechte Nachrichten bleiben drin)

* Das KI-Bild malt im Haus weiterhin frei (Fensterteilung, Material); nur die Tiefe bindet die Form. Ob es vom Grundbild
  ausgehen soll, entscheidet der Owner nach Messung 337.
* Abends wird der Abstand Haus/Hintergrund etwas kleiner (gerechnet 23–25, Schwelle 20).
* Glas spiegelt im kleinen Bild noch kaum sichtbar.

## Prüfung

Volle Suite ohne GPU, grün (Zahl in `README.md`). iPad/Mac: Prüfstrecke `.github/workflows/ipad.yml`; der Job
`freigabe` legt die Freigabe erst auf `main` an.
