# Visbox 0.3.47 — Fassungsblatt (23.10.2026)

**Codestand:** Fassung 0.3.47 auf `main` (Folgen aus Ergebnis 343); Vorgänger 0.3.46 = Tag `v0.3.46`

**Grundlage:** Ergebnis 343; Protokoll 74 §262; Einbau-Stand C180 (erledigt), C181, C182. Abgeglichen gegen alle
Änderungen seit `v0.3.46` (`git log v0.3.46..` ohne Zusammenführungen).

Visbox zählt selbst (Entscheid 66): Bibliothek `aiimaging`, iPad-App und Mac-App tragen dieselbe Nummer
(`tests/test_versionsnummer.py`). Dieses Blatt ist der Text der Freigabe auf GitHub; die Mac-App zeigt daraus die
Zeilen des Abschnitts «Was neu ist».

## Warum 0.3.47

In Messung 343 waren die Urteile zur Augenhöhe vertauscht (die richtig stehende Eingangskamera hiess «zu hoch», die zu
tiefe Ansicht «augenhoch»), das Gelände wurde nur am Namen erkannt, und «Haus kaum sichtbar» kam in allen Läufen.

## Was neu ist (mit Entscheid und Stand)

| Fähigkeit | Entscheid | Stand |
|---|---|---|
| Die Augenhöhe wird am richtigen Bezug beurteilt: Gelände am Standpunkt, sonst OK EG der Bestellung, sonst Gelände in der Nähe | — | gebaut, mit Probe; Messung 344 offen |
| Das Gelände wird an seiner Kennzeichnung in der Datei erkannt (Rolle «ground»), erst danach am Namen | — | gebaut, mit Probe |
| Zusätzlich zum Mittelwert wird der Kontrast am Umriss des Hauses gemessen und genannt | — | gebaut, mit Probe; Messung 344 offen |

## Stand am Gerät

* **Mac:** Update-Knopf.
* **Heim-PC:** `git pull`, Dienst und Abholer neu starten; dann Auftrag 344. Kein Bild ändert sich, keine Kamera steht
  anders.

## Bekannte Grenzen (schlechte Nachrichten bleiben drin)

* Ob das Haus mittags wirklich zu wenig absticht, ist offen — Messung 344 vergleicht Mittelwert, Umriss und Blick.
* Die Szene liefert keine EG-Kote; «OK EG» nimmt heute Weltnull an.
* Die automatischen Kameras des Heim-PC stehen weiter rund 1,3 m über dem Gelände (Owner-Frage nach der Demo).

## Prüfung

Volle Suite ohne GPU, grün (Zahl in `README.md`). iPad/Mac: Prüfstrecke `.github/workflows/ipad.yml`; der Job
`freigabe` legt die Freigabe erst auf `main` an.
