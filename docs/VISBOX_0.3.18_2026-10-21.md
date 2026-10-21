# Visbox 0.3.18 — Fassungsblatt (21.10.2026)

**Codestand:** Fassung 0.3.18 auf `main` (Gestaltung der Knotenansicht repariert, Karten bleiben, iPad nur über den Mac, breiterer Render-Knoten, Stimmungssatz); Vorgänger 0.3.17 = Tag `v0.3.17`

**Grundlage:** Entscheide 118a, 119; Befunde aus 302, 303, 305, 306, 307 und dem ersten Claude-Demolauf am Mac;
Protokoll 74 §181–§187; Einbau-Stand C108–C112. Abgeglichen gegen alle Änderungen seit `v0.3.17`
(`git log v0.3.17..` ohne Zusammenführungen).

Visbox zählt selbst (Entscheid 66): Bibliothek `aiimaging`, iPad-App und Mac-App tragen dieselbe Nummer
(`tests/test_versionsnummer.py`). Dieses Blatt ist der Text der Freigabe auf GitHub; die Mac-App zeigt daraus die
Zeilen des Abschnitts «Was neu ist».

## Warum 0.3.18

Auf dem Mac lagen Inselleiste, Sonne-Insel, Claude-Marke, Karten und Gesprächsfeld ohne Gestaltung am Rand — eine
fehlende Klammer in einer Gestaltungsdatei hatte fast die Hälfte der Regeln unwirksam gemacht. Claudes Karten waren
darum unsichtbar und gingen beim Wechsel der Ansicht verloren.

## Was neu ist (mit Entscheid und Stand)

| Fähigkeit | Entscheid | Stand |
|---|---|---|
| Die Knotenansicht ist wieder gestaltet: Inseln am Rand, Claude-Marke, Karten, Gesprächsfeld | 115 | gebaut, mit Probe; am Gerät unbestätigt |
| Offene Claude-Karten bleiben beim Wechsel der Ansicht erhalten, ohne Frist; verworfen wird nur mit Ablehnen oder beim Beenden (App zu, «Claude über MCP» aus), immer mit Satz an Claude; bei Leitungsverlust bleiben sie mit Vermerk stehen | — (Demolauf, Regel wie KosmoOrbit) | gebaut, mit Probe; am Gerät unbestätigt |
| Der Assistent rät keine Knoten-Kennungen mehr, erfindet nichts und nennt Karten «vorgeschlagen»; der Kern prüft das nach | — (305) | gebaut, mit Probe; Messung 310 offen |
| Claude kennt alle acht Stimmungen mit ihren Namen | — (Demolauf) | gebaut, mit Probe |
| Der Render-Knoten ist breiter; Grundbild und KI-Bild stehen schon am Knoten nebeneinander | 119 | gebaut, mit Probe; am Gerät unbestätigt |
| Das iPad verbindet sich nur noch über den Mac; ein direkt verbundenes iPad bekommt einen klaren Satz; der Mac vermittelt auch ohne Heim-PC | 118a | gebaut, mit Probe; Messung 308 offen |
| Bei bestellter Stimmung gilt immer der englische Stimmungssatz des Heim-PC, einmal; halbe Übersetzungen fallen weg | — (306) | gebaut, mit Probe; Messung 309 offen |
| Stimmung «weiss» mit hellem Studio-Himmelsbild | — (306) | gebaut, mit Probe |
| «Grundlage rendern» rechnet einen schon gerechneten Stand nicht neu; die eingefrorene Kamera behält ihre senkrechte Ausrichtung; echte Vorschaubilder für Himmel und Materialien | — (306) | gebaut, mit Probe |
| «Material vorne» höchstens dreimal; die Sätze zu «Umriss halten» sprechen über das gelieferte Bild | — (303) | gebaut, mit Probe; Messung 309 offen |
| Ein veralteter Ladestand meldet sich als veraltet | — (307) | gebaut, mit Probe |

## Stand am Gerät

* **Mac:** Update-Knopf. Dann: Knotenansicht öffnen — unten links und am Rand muss alles gestaltet sein wie in KosmoVis.
  Claude etwas vorschlagen lassen: die Karte erscheint unten links; zur Visbox-Seite und zurück — sie steht noch da.
* **iPad:** vorher mit dem Mac koppeln (Mac: Menü «iPad» › «iPad koppeln»); ein direkt verbundenes iPad zeigt nur noch
  den Satz.
* **Heim-PC:** `git pull` (Ansagen lagen vorab): die Tür nimmt das iPad nur noch über den Mac, mit Stimmung ändert sich
  der Prompt, «weiss» wird neu gerechnet, der Assistent hat einen geschärften Systemsatz.

## Bekannte Grenzen (schlechte Nachrichten bleiben drin)

* Einzelne Bedienteile in den neuen Knoten (Kamera, Stimmung) sehen im Bau noch anders aus als erwartet; der Vergleich
  mit KosmoVis läuft.
* Der Vermerk «Leitung unterbrochen» steht erst in der Leiste der Mac-App, noch nicht an der Claude-Marke.
* Am Knoten wird «Grundbild mit Licht» in 96 px voraussichtlich gekürzt.
* Ein iPad mit einer App älter als 0.2.12 wird nicht als iPad erkannt.

## Prüfung

Volle Suite ohne GPU, grün (Zahl in `README.md`). iPad/Mac: Prüfstrecke `.github/workflows/ipad.yml`; der Job
`freigabe` legt die Freigabe erst auf `main` an.
