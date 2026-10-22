# Visbox 0.3.35 — Fassungsblatt (22.10.2026)

**Codestand:** Fassung 0.3.35 auf `main` (Folgen aus dem Mac-Test und dem Mac-Demolauf); Vorgänger 0.3.34 = Tag `v0.3.34`

**Grundlage:** Mac-Test 0.3.33, Schlussbericht des Mac-Demolaufs (F1–F18), Ergebnisse 330 und 331; Protokoll 74
§231–§241; Einbau-Stand C140–C157; Entscheide 128–134. Abgeglichen gegen alle Änderungen seit `v0.3.34`
(`git log v0.3.34..` ohne Zusammenführungen).

Visbox zählt selbst (Entscheid 66): Bibliothek `aiimaging`, iPad-App und Mac-App tragen dieselbe Nummer
(`tests/test_versionsnummer.py`). Dieses Blatt ist der Text der Freigabe auf GitHub; die Mac-App zeigt daraus die
Zeilen des Abschnitts «Was neu ist».

## Warum 0.3.35

Der Owner hat Visbox am Mac von vorn bis hinten durchgespielt. Sieben von acht Schritten gingen; dabei fielen eine
Lücke in der Spielregel (Claude konnte die eigene Karte anwenden), mehrere stille Sackgassen und eine Reihe von
Anzeigen auf, die einen falschen Stand zeigten.

## Was neu ist (mit Entscheid und Stand)

| Fähigkeit | Entscheid | Stand |
|---|---|---|
| Claude kann seine eigenen Vorschläge nicht mehr anwenden — Anwenden und Freigeben bleiben beim Architekten | 106b/c | gebaut, mit Probe |
| Vorschläge nur noch an der Karte unten links, mit Werten statt Feldnamen («Stimmung: Morgenlicht → Abendstimmung») | 131 | gebaut, mit Probe |
| Eine Stimmung, die Claude wählt, gilt wirklich für Knoten, Bildbeschreibung und Bestellung | — | gebaut, mit Probe |
| Der Mac bleibt bei seiner eigenen Mappe; zwei Geräte überschreiben sich nicht mehr still | 129 | gebaut, mit Probe |
| «Freigeben» scheitert nie mehr still; «Grundlage rendern» ist neben einem wartenden Auftrag frei | — | gebaut, mit Probe |
| «Bild aus Skizze erzeugen» am Render-Knoten, wenn eine Skizze anhängt | — | gebaut, mit Probe |
| Beim Herauszoomen schrumpft die Schrift mit dem Knoten | 130 (R1.2) | gebaut, mit Probe |
| Ehrliche Zeitschätzung am Varianten-Knoten; Wartemeldung erst nach 30 s | — | gebaut, mit Probe |
| Das iPad erkennt den Mac an einer festen Kennung; «Neu koppeln» ohne Trennen; iPad-Zeile am Mac nur grün bei frischem Kontakt | — | gebaut, mit Probe |
| Mit gewählter Fenster-Textur bleibt das Glas durchsichtig | — | gebaut, mit Probe |
| Feste Unterschrift der Mac-App möglich, sobald der Owner sie eingerichtet hat (`docs/MAC_UNTERSCHRIFT_EINRICHTEN.md`) | 128 | gebaut; Einrichtung beim Owner |

## Stand am Gerät

* **Mac:** Update-Knopf; danach Claude Desktop ganz beenden (⌘Q) und neu öffnen.
* **iPad:** am 26. oder 27.10. neu aufspielen (Ablauf des freien Kontos).
* **Heim-PC:** `git pull`, Dienst und Abholer neu starten.

## Bekannte Grenzen (schlechte Nachrichten bleiben drin)

* Eine iPad-Skizze in einer Mappe **am Mac** wird nicht gerechnet (der Heim-PC hat die Skizze nicht) — jetzt mit klarem
  Satz. Für «Stift zu Bild» eine Mappe am Heim-PC nehmen.
* Aus einer IFC-Datei gewandelte Modelle verlieren Dach, Material und Glas — in Arbeit.
* Ohne Gelände im Modell schwebt das Haus; das Demohaus bekommt eine Bodenplatte.
* Die schnelle Vorschau sieht das Grundbild nicht und malt nach Beschreibung (Umriss gehalten).

## Prüfung

Volle Suite ohne GPU, grün (Zahl in `README.md`). iPad/Mac: Prüfstrecke `.github/workflows/ipad.yml`; der Job
`freigabe` legt die Freigabe erst auf `main` an.
