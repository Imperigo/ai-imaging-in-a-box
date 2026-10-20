# Visbox 0.3.8 — Fassungsblatt (20.10.2026)

**Codestand:** Fassung 0.3.8 auf `main` (Kopfteile, bessere Stimmungen, 3D-Fenster, Aktualisieren); Vorgänger 0.3.7 = Tag `v0.3.7`

**Grundlage:** Entscheide 115, 116, 116a; Plan `docs/PLAN_UI_GLEICHHEIT_2026-10-20.md` (Stufen S1 und S2); Befunde aus
Auftrag `auf-20261020-293`; Protokoll 74 §157–§160; Einbau-Stand C86–C89

Visbox zählt selbst (Entscheid 66): Bibliothek `aiimaging`, iPad-App und Mac-App tragen dieselbe Nummer
(`tests/test_versionsnummer.py`). Dieses Blatt ist der Text der Freigabe auf GitHub; die Mac-App zeigt daraus die
Zeilen des Abschnitts «Was neu ist».

## Warum 0.3.8

Der Owner sah am Mac ein schwarzes 3D-Fenster, Stimmungsbilder ohne Schatten und ohne Kontrast, einen Update-Knopf, der
nicht auf die neueste Fassung sprang, und eine Knotenansicht ohne die Bedienteile, die zum Rendern gehören.
Entscheid 115 verlangt, dass die Ansichten gleich sind.

## Was neu ist (mit Entscheid und Stand)

| Fähigkeit | Entscheid | Stand |
|---|---|---|
| Die Knotenansicht trägt ihre Bedienteile: Einstellungs- und Speichern-Kreis, Rückgängig/Wiederholen und Fassung, Stationen-Palette, Heim-PC-Chip («Wer rechnet?»), Claude-Karten unten links, Tätigkeitszeile oben; die eigenen Mac-Leisten fallen dort weg | 115, 116 | gebaut, mit Probe; am Gerät unbestätigt |
| Dunkles Farbthema, umschaltbar über «Darstellung → Thema wechseln» | 116 (3) | gebaut, mit Probe; am Gerät unbestätigt |
| Speichern sagt «NICHT gesichert» mit dem Satz des Heim-PC, wenn dieser das Speichern abweist (vorher stand immer «gesichert») | — | gebaut, mit Probe |
| Stimmungen mit Sonne und Schatten aus dem Himmelsbild, Haus eine Blendenstufe vom Hintergrund abgehoben, graue Platte, kräftigere Tonwerte, Blaue Stunde dunkler; neue Zahl «Kontrast Haus–Hintergrund» | — (293) | gebaut, mit Probe; Messung 294 offen |
| Vorschau rechnet den KI-Schritt mindestens 1024 px lang; die Geometrieprüfung trennt Boden und Himmel auch neben der Platte | — (293) | gebaut, mit Probe; Messung 294 offen |
| 3D-Fenster im Modell-Knoten: Modell hell statt schwarz, kein Abschneiden beim Heranzoomen, ältere Graphen werden beim Laden entzerrt | — | gebaut, mit Probe; am Gerät unbestätigt |
| Der Update-Knopf fragt vor dem Laden nach und lädt die neueste Fassung; Nachfrage auch nach dem Aufwachen | — | gebaut, mit Probe; am Gerät unbestätigt |

## Stand am Gerät

* **Mac:** Update-Knopf. Danach: IFC-Modell öffnen, im 3D-Fenster drehen und nah heranzoomen; Kopfteile, Thema und
  Heim-PC-Chip ansehen.
* **Heim-PC:** `git pull`. Mit Stimmung rechnet Blender etwas länger (Vorprobe) und gespeicherte Grundlagen mit Stimmung
  werden neu gerechnet; `geom_iou` und Score können sich bei Geländeplatte verschieben. Ohne Stimmung bleibt alles gleich.

## Bekannte Grenzen (schlechte Nachrichten bleiben drin)

* **Am Gerät nicht geprüft** — die Mac-Teile der Kopfteile sind hier nur auf Syntax geprüft.
* Die Lichtwerte der Stimmungen sind gesetzt, nicht gemessen; die Messung 294 steht aus.
* Der neue Update-Knopf wirkt erst ab dieser Fassung: der Schritt von 0.3.7 auf 0.3.8 läuft noch nach der alten Regel.
* Die Assistenten-Kugel mit Gespräch und die Einstellungs-Insel fehlen noch (Stufen S3, S4).

## Prüfung

Volle Suite ohne GPU, grün (Zahl in `README.md`). iPad/Mac: Prüfstrecke `.github/workflows/ipad.yml`; der Job
`freigabe` legt die Freigabe erst auf `main` an.
