# Visbox 0.3.44 — Fassungsblatt (22.10.2026)

**Codestand:** Fassung 0.3.44 auf `main` (Entscheid 138 und Folgen aus der Mac-Prüfliste und Ergebnis 339); Vorgänger 0.3.43 = Tag `v0.3.43`

**Grundlage:** Ergebnisse 337, 339; Mac-Prüfliste Teil 2; Protokoll 74 §255–§256; Einbau-Stand C174 (erledigt), C175,
C176; Entscheid 138. Abgeglichen gegen alle Änderungen seit `v0.3.43` (`git log v0.3.43..` ohne Zusammenführungen).

Visbox zählt selbst (Entscheid 66): Bibliothek `aiimaging`, iPad-App und Mac-App tragen dieselbe Nummer
(`tests/test_versionsnummer.py`). Dieses Blatt ist der Text der Freigabe auf GitHub; die Mac-App zeigt daraus die
Zeilen des Abschnitts «Was neu ist».

## Warum 0.3.44

Ohne Grundbild malte die KI die Fenster frei oder sogar ein anderes Haus (Messungen 337, 339); der Owner hat
entschieden, dass die Variante vom Grundbild ausgeht. Am Mac zeigte der Render-Knoten nach dem Öffnen der Mappe sein
letztes Bild nicht mehr.

## Was neu ist (mit Entscheid und Stand)

| Fähigkeit | Entscheid | Stand |
|---|---|---|
| Die KI-Variante geht vom Grundbild aus (Stärke 0,5): Form, Fenster und Stoff bleiben — nie für Modelle mit offener Lizenz | 138 | gebaut, mit Probe; Messung 340 offen |
| Das Ergebnis sagt «Form weicht vom Grundbild ab», wenn die KI ein anderes Haus malt (strengere Prüfung) | 138 | gebaut, mit Probe |
| Der Render-Knoten merkt sich sein letztes Bild und zeigt es nach dem Öffnen der Mappe wieder | — | gebaut, mit Probe; am Mac offen |

## Stand am Gerät

* **Mac:** Update-Knopf. Prüfen: einen Lauf machen, Mappe schliessen und wieder öffnen — das Bild steht am Knoten.
* **Heim-PC:** `git pull`, Dienst und Abholer neu starten; dann Auftrag 340. Jede KI-Variante rechnet jetzt vom
  Grundbild aus (img2img 0,5).

## Bekannte Grenzen (schlechte Nachrichten bleiben drin)

* Bilder aus Läufen vor dieser Fassung kommen am Knoten nicht zurück; sie liegen weiter in der Mappe.
* Die Vorschau geht noch nicht vom Grundbild aus und kann darum anders aussehen als die volle Variante.
* Die Anzeige «deckungsgleich» in der Knotenansicht folgt der strengeren Prüfung erst mit der nächsten Fassung.
* Zwei Stoff-Varianten mit demselben Stoff rechnen das Grundbild doppelt (je 6–10 s).

## Prüfung

Volle Suite ohne GPU, grün (Zahl in `README.md`). iPad/Mac: Prüfstrecke `.github/workflows/ipad.yml`; der Job
`freigabe` legt die Freigabe erst auf `main` an.
