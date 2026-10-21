# Visbox 0.3.14 — Fassungsblatt (21.10.2026)

**Codestand:** Fassung 0.3.14 auf `main` (Bildeingang rechnet über die Brücke, Warnsatz bei Häuserzeile); Vorgänger 0.3.13 = Tag `v0.3.13`

**Grundlage:** Entscheid 117; Befunde aus `auf-20261021-299` und `auf-20261021-300`; Plan
`docs/PLAN_LICHT_INS_KI_BILD_2026-10-21.md`; Protokoll 74 §171; Einbau-Stand C99

Visbox zählt selbst (Entscheid 66): Bibliothek `aiimaging`, iPad-App und Mac-App tragen dieselbe Nummer
(`tests/test_versionsnummer.py`). Dieses Blatt ist der Text der Freigabe auf GitHub; die Mac-App zeigt daraus die
Zeilen des Abschnitts «Was neu ist».

## Warum 0.3.14

In 0.3.13 wies der Speicherschutz jeden Bildeingang ab, auch bei leerer Grafikkarte, weil die zweite Prüfung den
eigenen Prozess als fremd zählte. Die Messung 299 lieferte das Augenurteil, mit dem sich Häuserzeilen erkennen lassen.

## Was neu ist (mit Entscheid und Stand)

| Fähigkeit | Entscheid | Stand |
|---|---|---|
| Der Bildeingang rechnet über den normalen Weg wieder; beide Speicherprüfungen rechnen gleich | 117 | gebaut, mit Probe; Messung 301 offen |
| Weist das Bildmodell ab, steht der Grund im Ergebnis | 117 | gebaut, mit Probe |
| Der Abweisungssatz nennt jedes Modell einmal und das eigene Assistenzmodell nicht «fremd» | — (300) | gebaut, mit Probe |
| Satz «Haus im KI-Bild nicht wiederzuerkennen» auch, wenn die KI eine Häuserzeile statt des Hauses malt (ab 960 px) | — (299) | gebaut, mit Probe; an 14 Bildern gegen das Augenurteil geprüft |

## Stand am Gerät

* **Mac:** Update-Knopf; an der Oberfläche ändert sich nichts.
* **Heim-PC:** `git pull`; der Warnsatz kommt bei einigen Bildern mehr. Ohne Messschalter bleibt jedes Bild gleich.

## Bekannte Grenzen (schlechte Nachrichten bleiben drin)

* Der Bildeingang bringt das Licht ins KI-Bild, aber bis Stärke 0,9 nur als Gipsmodell mit Licht; bei 0,95 verliert
  das Haus seine Form. Sichtbeton kam in keiner Messung. Empfohlen ist, das gerenderte Grundbild neben das KI-Bild zu
  stellen; die Wahl trifft der Owner am Bild.
* Die Zahl «über den Umriss» kann an gemalten Himmeln kippen.
* Kugel, Gespräch und Einstellungs-Insel aus 0.3.9 sind am Gerät weiter unbestätigt.

## Prüfung

Volle Suite ohne GPU, grün (Zahl in `README.md`). iPad/Mac: Prüfstrecke `.github/workflows/ipad.yml`; der Job
`freigabe` legt die Freigabe erst auf `main` an.
