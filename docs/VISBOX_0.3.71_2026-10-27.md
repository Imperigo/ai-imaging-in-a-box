# Visbox 0.3.71 — Fassungsblatt (27.10.2026)

**Codestand:** Fassung 0.3.71 auf `main` (Innenraum mit Raumleuchte, Skizze über KosmoOrbit mit Hochachse); Vorgänger 0.3.70
= Tag `v0.3.70`

**Grundlage:** Generalprobe 373 (S9, S11); Protokoll 74 §299, §300; Einbau-Stand C211, C214; Aufträge 374, 375. Abgeglichen
gegen alle Änderungen seit `v0.3.70` (`git log v0.3.70..` ohne Zusammenführungen).

Visbox zählt selbst (Entscheid 66): Bibliothek `aiimaging`, iPad-App und Mac-App tragen dieselbe Nummer
(`tests/test_versionsnummer.py`). Dieses Blatt ist der Text der Freigabe auf GitHub; die Mac-App zeigt daraus die
Zeilen des Abschnitts «Was neu ist».

## Warum 0.3.71

Generalprobe 373: Das Innenbild einer IFC mit Räumen war schwarz — die Kamera stand richtig, aber in einem geschlossenen
Raum ohne Tageslicht (Fenster und Türen der Datei sind volle Körper ohne Glas), und Blender beleuchtete nur von aussen.
«Bild aus Skizze» brach auf dem Weg über KosmoOrbit ab, weil die Hochachse in der Mappe des Auftrags fehlte.

## Was neu ist (mit Entscheid und Stand)

| Fähigkeit | Entscheid | Stand |
|---|---|---|
| Steht eine Kamera in einem Raum, bekommt er eine unsichtbare Raumleuchte unter der Decke; die Helligkeit wird gemessen und nachgestellt | — | gebaut, mit Probe; Messung 374 offen |
| Jede Kamera meldet ihre mittlere Helligkeit; Satz «INNENBILD ZU DUNKEL» bzw. «INNENKAMERA IN EINEM BAUTEIL» | — | gebaut, mit Probe |
| «Bild aus Skizze» über KosmoOrbit nimmt die Hochachse aus Mappe, Umwandlung oder Auftrag, sonst Y oben | 96 | gebaut, mit Probe; Messung 375 offen |
| «Hochachse setzen» geht auch in einer Mappe ohne Prompt in den Einstellungen | — | gebaut, mit Probe |

## Stand am Gerät

* **Mac:** Update-Knopf (die Änderungen dieser Fassung laufen am Heim-PC; der Mac-Weg der Skizze war nicht betroffen).
* **Heim-PC:** `git pull`, Dienst und Abholer neu starten; dann Aufträge 374 und 375.

## Bekannte Grenzen (schlechte Nachrichten bleiben drin)

* Die Raumleuchte ist ohne Blender gebaut; Messung 374 belegt sie erst.
* Ein eigener Innenstandpunkt lässt sich in der Knotenansicht noch nicht setzen.
* Nach einem abgebrochenen Lauf kann das letzte Bild eines Render-Knotens verschwinden — Fix folgt mit 0.3.72.
* Fenster ohne Glas in der Datei bleiben Holzfelder; das liegt am Export.

## Prüfung

Volle Suite ohne GPU, grün (Zahl in `README.md`). iPad/Mac: Prüfstrecke `.github/workflows/ipad.yml`; der Job
`freigabe` legt die Freigabe erst auf `main` an.
