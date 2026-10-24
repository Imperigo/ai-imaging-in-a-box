# Visbox 0.3.57 — Fassungsblatt (24.10.2026)

**Codestand:** Fassung 0.3.57 auf `main` (Befund F4 «Bild aus Skizze», Legende über der Leinwand, Werkzeug zum
Neutralisieren einer IFC); Vorgänger 0.3.56 = Tag `v0.3.56`

**Grundlage:** Demolauf 0.3.54/0.3.55 (F4 ROT, Legende hinter Knoten); Owner-Auftrag 24.10. (eigenes Modell statt
Demohaus); Protokoll 74 §284–§287; Einbau-Stand C202–C204; Aufträge 352, 353, 354. Abgeglichen gegen alle Änderungen
seit `v0.3.56` (`git log v0.3.56..` ohne Zusammenführungen).

Visbox zählt selbst (Entscheid 66): Bibliothek `aiimaging`, iPad-App und Mac-App tragen dieselbe Nummer
(`tests/test_versionsnummer.py`). Dieses Blatt ist der Text der Freigabe auf GitHub; die Mac-App zeigt daraus die
Zeilen des Abschnitts «Was neu ist».

## Warum 0.3.57

«Bild aus Skizze» brach dreimal mit «prompt fehlt oder ist leer (None)» ab, wenn an der iPad-Skizze nur der gewünschte
Name stand. Die Legende verschwand beim Zoomen hinter dem Beiblatt des Render-Knotens.

## Was neu ist (mit Entscheid und Stand)

| Fähigkeit | Entscheid | Stand |
|---|---|---|
| «Bild aus Skizze» rechnet, wenn an der Skizze nur der gewünschte Name steht — der Prompt gilt als Anweisung; der Name bleibt Titel | 96c | gebaut, mit Probe; Messung 352 offen |
| Ohne Anweisung und ohne Prompt wird schon beim Bestellen mit einem Satz abgelehnt, statt später abzubrechen | — | gebaut, mit Probe |
| Vor «Freigeben» steht am Knoten, welche Anweisung gilt; der Bildwerkzeug-Wähler nennt das bestellte Werkzeug | — | gebaut, mit Probe; am Mac offen |
| Legende und Kuratier-Fläche liegen immer über Knoten und Beiblatt, bei jeder Zoomstufe | 115 | gebaut, mit Probe; am Mac offen |
| Werkzeug, das eine IFC neutralisiert: Beschriftungen, Namen, Adressen, Lage, Schilder entfernt, Restprüfung | — | gebaut, mit Probe; Auftrag 354 offen |

## Stand am Gerät

* **Mac:** Update-Knopf. Prüfen: Skizze «Variante A» vom iPad, Text am Prompt-Knoten, «Bild aus Skizze» → ein Bild;
  Beiblatt unter die Legende schieben und zoomen → Legende bleibt oben.
* **Heim-PC:** `git pull`, Dienst und Abholer neu starten; dann Aufträge 352, 353, 354.

## Bekannte Grenzen (schlechte Nachrichten bleiben drin)

* Rendern über die Maus bleibt in «Voll» eine Karte.
* Ein offenes Beiblatt liegt jetzt unter der Legende (gewollt).
* Neutralisieren entfernt Texte, nicht die Form: Ein echter Ort bleibt an seiner Gestalt erkennbar.
* Das KI-Bild weicht bei Stärke 0,5 mit «Umriss halten» kaum vom Grundbild ab — Messung 353 läuft, danach Owner-Entscheid.

## Prüfung

Volle Suite ohne GPU, grün (Zahl in `README.md`). iPad/Mac: Prüfstrecke `.github/workflows/ipad.yml`; der Job
`freigabe` legt die Freigabe erst auf `main` an.
