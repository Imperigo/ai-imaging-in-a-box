# Visbox 0.3.16 — Fassungsblatt (21.10.2026)

**Codestand:** Fassung 0.3.16 auf `main` (neue Knoten, Grundbild neben dem KI-Bild); Vorgänger 0.3.15 = Tag `v0.3.15`

**Grundlage:** Entscheide 107, 109–113, 117a; Plan `docs/PLAN_KNOTEN_NEU_2026-10-20.md` (Schritte K, C, D, E), Plan
`docs/PLAN_LICHT_INS_KI_BILD_2026-10-21.md` (W-4); Blätter 31–33, 35 und 39 der Entwurfsfläche; Protokoll 74 §176–§177;
Einbau-Stand C104–C105

Visbox zählt selbst (Entscheid 66): Bibliothek `aiimaging`, iPad-App und Mac-App tragen dieselbe Nummer
(`tests/test_versionsnummer.py`). Dieses Blatt ist der Text der Freigabe auf GitHub; die Mac-App zeigt daraus die
Zeilen des Abschnitts «Was neu ist».

## Warum 0.3.16

Stimmungen mit Himmelsbild, automatische Kameras und Materialien rechnete der Heim-PC seit 0.3.5 — in der
Knotenansicht gab es aber keine Knoten, um sie zu bestellen. Und das Licht der Stimmung kommt im KI-Bild nicht an;
darum steht das gerenderte Grundbild jetzt daneben (Entscheid 117a).

## Was neu ist (mit Entscheid und Stand)

| Fähigkeit | Entscheid | Stand |
|---|---|---|
| Knoten «Stimmung»: acht Stimmungen mit Himmelsbild, Himmel drehen, wirkt als Licht, Satz oder beides | 109–111 | gebaut, mit Probe; am Gerät unbestätigt; Vorschaubilder noch gezeichnet |
| Knoten «Kamera»: Auto mit Richtungen, Augenhöhe, Brennweite, Abstand und Perspektive, Standpunkte im 3D-Fenster; Manuell friert ein | 109 | gebaut, mit Probe; am Gerät unbestätigt |
| Knoten «Material», «Farbpalette» und «Oberfläche» (vorher «Material-Bausteine»): Stoff je Bauteil, Vorschau als Kugel, Würfel oder Fläche, Tönung | 107, 112, 113 | gebaut, mit Probe; am Gerät unbestätigt; Vorschaubilder noch gezeichnet |
| Grundbild neben dem KI-Bild: am Render-Knoten «+ Grundbild», ein Klick zeigt beide gross nebeneinander mit Umschalter | 117a | gebaut, mit Probe; am Gerät unbestätigt |

## Stand am Gerät

* **Mac:** Update-Knopf. Dann: neuer Graph, Stimmung «Abend» wählen, Kamera auf «Auto», eine Variante erzeugen; am
  Render-Knoten auf das Bild klicken und Grundbild und KI-Bild vergleichen.
* **Heim-PC:** `git pull`; am Kern ändert sich nichts, aber die Knotenansicht bestellt jetzt Stimmung, Auto-Kamera,
  Material und das Grundbild mit.

## Bekannte Grenzen (schlechte Nachrichten bleiben drin)

* Die Vorschaubilder der Stimmungen und Materialien sind noch gezeichnete Farbverläufe; die echten Bilder rechnet die
  HomeStation.
* Bei mehreren gewählten Stimmungen rechnet der Render-Knoten nur die erste.
* Die Kamera lässt sich im 3D-Fenster noch nicht ziehen, nur über Werte einstellen.
* Am Render-Knoten selbst stehen die Bilder nicht nebeneinander (zu schmal); der Vergleich steht in der grossen Ansicht.

## Prüfung

Volle Suite ohne GPU, grün (Zahl in `README.md`). iPad/Mac: Prüfstrecke `.github/workflows/ipad.yml`; der Job
`freigabe` legt die Freigabe erst auf `main` an.
