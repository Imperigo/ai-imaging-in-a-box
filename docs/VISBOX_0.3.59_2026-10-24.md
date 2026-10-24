# Visbox 0.3.59 — Fassungsblatt (24.10.2026)

**Codestand:** Fassung 0.3.59 auf `main` (Umfeld über die Brücke, übersetzte Skizzen-Bemerkung, Gebiet im Raster);
Vorgänger 0.3.58 = Tag `v0.3.58`

**Grundlage:** Ergebnisse 352, 355 (ROT), 356; Protokoll 74 §287–§289 (Nachträge); Einbau-Stand C204–C206; Auftrag 358.
Abgeglichen gegen alle Änderungen seit `v0.3.58` (`git log v0.3.58..` ohne Zusammenführungen).

Visbox zählt selbst (Entscheid 66): Bibliothek `aiimaging`, iPad-App und Mac-App tragen dieselbe Nummer
(`tests/test_versionsnummer.py`). Dieses Blatt ist der Text der Freigabe auf GitHub; die Mac-App zeigt daraus die
Zeilen des Abschnitts «Was neu ist».

## Warum 0.3.59

Messung 355 zeigte: Über die Brücke wurde das Umfeld nie gestellt — kein Auftrag vom Mac bekam Bäume oder Autos.
Messung 352 zeigte: Eine deutsche Bemerkung an der Skizze ging wörtlich ans Bildmodell und erschien als Schrift auf der
Fassade.

## Was neu ist (mit Entscheid und Stand)

| Fähigkeit | Entscheid | Stand |
|---|---|---|
| Der Knoten «Umfeld» stellt Bäume, Büsche, Wiese, Strasse und Autos jetzt auch bei Bestellungen vom Mac | 147, 148 | gebaut, mit Probe; Messung 358 offen |
| Die Bemerkung an einer Skizze geht übersetzt ans Bildmodell, wie ein Prompt | 96a | gebaut, mit Probe |
| Am Raster der Draufsicht lässt sich auch ein Gebiet wählen («B2:C3») | — | gebaut, mit Probe |

## Stand am Gerät

* **Mac:** Update-Knopf. Prüfen: Knoten «Umfeld» setzen, Bäume und Autos anhaken, rendern — sie stehen im Bild.
* **Heim-PC:** `git pull`, Dienst und Abholer neu starten; dann Auftrag 358.

## Bekannte Grenzen (schlechte Nachrichten bleiben drin)

* Am Wettbewerbsmodell zerlegt die KI den Hauptbau in Blöcke; bei 0,7 löst er sich auf. Die Prüfung merkt es nicht
  (Deckung bei kleinem Hausanteil). Die Stärke je Modell folgt mit der nächsten Fassung.
* Die Übersetzung kennt nicht jedes Wort; Unbekanntes bleibt deutsch.

## Prüfung

Volle Suite ohne GPU, grün (Zahl in `README.md`). iPad/Mac: Prüfstrecke `.github/workflows/ipad.yml`; der Job
`freigabe` legt die Freigabe erst auf `main` an.
