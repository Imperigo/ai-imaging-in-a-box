# Visbox 0.3.32 — Fassungsblatt (22.10.2026)

**Codestand:** Fassung 0.3.32 auf `main` (Folgen aus der Generalprobe: Vorschau hält den Umriss, Knotenansicht zeigt den
richtigen Stand); Vorgänger 0.3.31 = Tag `v0.3.31`

**Grundlage:** Ergebnis 327 (Generalprobe); Protokoll 74 §225–§227; Einbau-Stand C137, C138. Abgeglichen gegen alle
Änderungen seit `v0.3.31` (`git log v0.3.31..` ohne Zusammenführungen).

Visbox zählt selbst (Entscheid 66): Bibliothek `aiimaging`, iPad-App und Mac-App tragen dieselbe Nummer
(`tests/test_versionsnummer.py`). Dieses Blatt ist der Text der Freigabe auf GitHub; die Mac-App zeigt daraus die
Zeilen des Abschnitts «Was neu ist».

## Warum 0.3.32

Die Generalprobe lief die ganze Demo-Kette ohne Abbruch, fand aber eine Vorschau, die über den Umriss des Hauses hinaus
malte, und zwei Stellen, an denen die Knotenansicht einen falschen Stand zeigte.

## Was neu ist (mit Entscheid und Stand)

| Fähigkeit | Entscheid | Stand |
|---|---|---|
| Die schnelle Vorschau hält den Umriss des Hauses wie die vollen Varianten | 126 | gebaut, mit Probe; Messung 328 offen |
| Ehrlicher Hinweis, wenn das Bildmodell das Grundbild nur ausserhalb des Hauses übernimmt | 125 | gebaut, mit Probe |
| Hintergrund je Kamera und Zusätze im Bildwunsch stehen im Ergebnis | — | gebaut, mit Probe |
| Nach «Datei laden …» erscheint der Graph der neuen Mappe sofort | 91 | gebaut, mit Probe |
| Der Varianten-Knoten nennt die Richtungen der Kamera und kündigt so viele Bilder an | — | gebaut, mit Probe |

## Stand am Gerät

* **Heim-PC:** `git pull`, Dienst und Abholer neu starten; dann Auftrag 328.
* **Mac:** Update-Knopf.

## Bekannte Grenzen (schlechte Nachrichten bleiben drin)

* Ein Wolkenschleier kann bei einer Kamera auf der Fassade liegen; Messung nach der Demo.
* Eine Stimmung wird zusätzlich angekreuzt, nicht ersetzt — beim Wechsel die alte abwählen.
* Die Zeile «Himmel» am Render-Knoten hat keine Wirkung; der Himmel kommt aus der Stimmung.
* Ob ein weiteres Sprachmodell auf derselben Grafikkarte Platz lässt, ist offen.

## Prüfung

Volle Suite ohne GPU, grün (Zahl in `README.md`). iPad/Mac: Prüfstrecke `.github/workflows/ipad.yml`; der Job
`freigabe` legt die Freigabe erst auf `main` an.
