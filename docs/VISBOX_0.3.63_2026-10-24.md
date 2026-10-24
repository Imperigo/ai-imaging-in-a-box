# Visbox 0.3.63 — Fassungsblatt (24.10.2026)

**Codestand:** Fassung 0.3.63 auf `main` (Umfeld beim Hauptbau, Widerspruch beim Annehmen, Satz zur Stärke);
Vorgänger 0.3.62 = Tag `v0.3.62`

**Grundlage:** Ergebnisse 357, 360; Owner-Entscheid 150; Protokoll 74 §288 und §290 (Nachträge); Einbau-Stand C205,
C207; Auftrag 361. Abgeglichen gegen alle Änderungen seit `v0.3.62` (`git log v0.3.62..` ohne Zusammenführungen).

Visbox zählt selbst (Entscheid 66): Bibliothek `aiimaging`, iPad-App und Mac-App tragen dieselbe Nummer
(`tests/test_versionsnummer.py`). Dieses Blatt ist der Text der Freigabe auf GitHub; die Mac-App zeigt daraus die
Zeilen des Abschnitts «Was neu ist».

## Warum 0.3.63

Messung 360: Auf dem Wettbewerbsmodell standen 25 Bäume zufällig über die Anlage verstreut, nur ein oder zwei beim
Hauptbau. Der Owner entschied: vor allem beim Bau, den die Kamera zeigt. Messung 357 fand drei Kleinigkeiten, und im Knoten «Umfeld» waren Zeilen samt «CC0» abgeschnitten.

## Was neu ist (mit Entscheid und Stand)

| Fähigkeit | Entscheid | Stand |
|---|---|---|
| Bei grossen Anlagen stehen Bäume und Autos zuerst im Umkreis des Hauptbaus im Bild; der Rest bleibt ruhig, ein Satz sagt wie viele beim Hauptbau stehen | 150 | gebaut, mit Probe; Messung 361 offen |
| Ein freies Bild mit einer Stärke (Widerspruch) wird schon beim Annehmen abgewiesen, nicht erst nach der Freigabe | 149 | gebaut, mit Probe; Messung 361 offen |
| Jedes Bild mit Bildeingang nennt seine Stärke und woher sie kommt | 149 | gebaut, mit Probe |
| Im Knoten «Umfeld» zeigt jede Zeile Quelle und «CC0» ganz; der Lizenzsatz liegt nicht mehr über dem Ladesatz | 147 | gebaut, mit Probe; am Mac offen |

## Stand am Gerät

* **Mac:** Update-Knopf.
* **Heim-PC:** `git pull`, Dienst und Abholer neu starten; dann Auftrag 361.

## Bekannte Grenzen (schlechte Nachrichten bleiben drin)

* Auch erste Bilder tragen jetzt den Satz zur Stärke (mehr Hinweise als bisher).
* Das Wettbewerbsmodell enthält nur Grundriss-Platten; die KI bleibt daran schwach.
* Der Knoten «Umfeld» ist dafür höher (364 statt 248 px); passen die Zeilen auf eine Linie, bleibt unter der Liste Platz frei.

## Prüfung

Volle Suite ohne GPU, grün (Zahl in `README.md`). iPad/Mac: Prüfstrecke `.github/workflows/ipad.yml`; der Job
`freigabe` legt die Freigabe erst auf `main` an.
