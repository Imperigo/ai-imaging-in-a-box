# Visbox 0.3.46 — Fassungsblatt (23.10.2026)

**Codestand:** Fassung 0.3.46 auf `main` (Folgen aus Ergebnis 341 und 342); Vorgänger 0.3.45 = Tag `v0.3.45`

**Grundlage:** Ergebnisse 341, 342; Protokoll 74 §259–§261; Einbau-Stand C178 (erledigt), C179, C180, C181;
Entscheide 139, 140 (festgehalten). Abgeglichen gegen alle Änderungen seit `v0.3.45` (`git log v0.3.45..` ohne
Zusammenführungen).

Visbox zählt selbst (Entscheid 66): Bibliothek `aiimaging`, iPad-App und Mac-App tragen dieselbe Nummer
(`tests/test_versionsnummer.py`). Dieses Blatt ist der Text der Freigabe auf GitHub; die Mac-App zeigt daraus die
Zeilen des Abschnitts «Was neu ist».

## Warum 0.3.46

Die automatische Kamera «Eingang» stand auf 15 cm und, nach dem ersten Fix, zu nah am Haus (Messung 341: First,
Treppe und Anbau abgeschnitten). Der Bericht meldete die Augenhöhe der übrigen Kameras als «1,70 m, zu hoch», wo das
Auge 1,32 m über dem Gelände steht.

## Was neu ist (mit Entscheid und Stand)

| Fähigkeit | Entscheid | Stand |
|---|---|---|
| Die Kamera «Eingang» steht 1,6 m über dem Boden an ihrem Standpunkt und so weit weg, dass Breite und Höhe des Hauses ins Bild passen | — | gebaut, mit Probe; Messung 343 offen |
| Der Bericht misst die Augenhöhe über dem Gelände am Standpunkt und nennt seinen Bezug; Höhenwarnungen stehen im Ergebnis | — | gebaut, mit Probe |
| Eine Variante mit anderer Stimmung nennt die Stimmung ihres Grundbilds; Teile des Stimmungssatzes stehen nicht mehr doppelt im Prompt | 126 | gebaut, mit Probe |

## Stand am Gerät

* **Mac:** Update-Knopf.
* **Heim-PC:** `git pull`, Dienst und Abholer neu starten; dann Auftrag 343.

## Bekannte Grenzen (schlechte Nachrichten bleiben drin)

* Die automatischen Kameras des Heim-PC stehen weiter ab der Bodenplatte gerechnet (rund 1,3 m über dem Gelände);
  ob das Gelände als Boden gelten soll, entscheidet der Owner nach der Demo.
* Die Messung des Geländes in Blender ist nur mit einer Attrappe geprüft.
* Pixelgleiche Grundbilder bekommen teils zwei Kennungen.

## Prüfung

Volle Suite ohne GPU, grün (Zahl in `README.md`). iPad/Mac: Prüfstrecke `.github/workflows/ipad.yml`; der Job
`freigabe` legt die Freigabe erst auf `main` an.
