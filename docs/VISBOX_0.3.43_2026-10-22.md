# Visbox 0.3.43 — Fassungsblatt (22.10.2026)

**Codestand:** Fassung 0.3.43 auf `main` (Folgen aus Ergebnis 337 und 338); Vorgänger 0.3.42 = Tag `v0.3.42`

**Grundlage:** Ergebnisse 337, 338; Protokoll 74 §254; Einbau-Stand C172, C173 (erledigt), C174; Entscheid 126.
Abgeglichen gegen alle Änderungen seit `v0.3.42` (`git log v0.3.42..` ohne Zusammenführungen).

Visbox zählt selbst (Entscheid 66): Bibliothek `aiimaging`, iPad-App und Mac-App tragen dieselbe Nummer
(`tests/test_versionsnummer.py`). Dieses Blatt ist der Text der Freigabe auf GitHub; die Mac-App zeigt daraus die
Zeilen des Abschnitts «Was neu ist».

## Warum 0.3.43

In Messung 337 kam eine Variante «Fassade aus Sichtbeton» in keinem Bild an: Das Holz aus der Datei stand vorne im
Prompt und im Grundbild und überstimmte den Wunsch.

## Was neu ist (mit Entscheid und Stand)

| Fähigkeit | Entscheid | Stand |
|---|---|---|
| Eine Variante, die einen anderen Fassadenstoff nennt (z. B. Sichtbeton), rechnet ihr Grundbild mit diesem Stoff neu und stellt ihn vorne in den Prompt; Dach, Fenster und Gelände bleiben | 126 | gebaut, mit Probe; Messung 339 offen |

## Stand am Gerät

* **Mac:** Update-Knopf.
* **Heim-PC:** `git pull`, Dienst und Abholer neu starten; dann Auftrag 339.

## Bekannte Grenzen (schlechte Nachrichten bleiben drin)

* Eine Stoff-Variante dauert länger, weil das Grundbild neu gerechnet wird.
* Glas und Metall haben kein eigenes Material: Dort ändert sich nur der Prompt.
* Eine frische Bestellung mit Material-Knoten «Holz» und Prompt «Sichtbeton» folgt weiter dem Material-Knoten.
* Die KI-Variante geht weiterhin nicht vom Grundbild aus, bis der Owner entschieden hat (Messung 337: Bildeingang 0,5).

## Prüfung

Volle Suite ohne GPU, grün (Zahl in `README.md`). iPad/Mac: Prüfstrecke `.github/workflows/ipad.yml`; der Job
`freigabe` legt die Freigabe erst auf `main` an.
