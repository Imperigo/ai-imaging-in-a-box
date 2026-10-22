# Visbox 0.3.45 — Fassungsblatt (22.10.2026)

**Codestand:** Fassung 0.3.45 auf `main` (Folgen aus Ergebnis 340); Vorgänger 0.3.44 = Tag `v0.3.44`

**Grundlage:** Ergebnis 340; Protokoll 74 §257–§258; Einbau-Stand C176 (erledigt), C177, C178; Entscheide 126, 138.
Abgeglichen gegen alle Änderungen seit `v0.3.44` (`git log v0.3.44..` ohne Zusammenführungen).

Visbox zählt selbst (Entscheid 66): Bibliothek `aiimaging`, iPad-App und Mac-App tragen dieselbe Nummer
(`tests/test_versionsnummer.py`). Dieses Blatt ist der Text der Freigabe auf GitHub; die Mac-App zeigt daraus die
Zeilen des Abschnitts «Was neu ist».

## Warum 0.3.45

In Messung 340 wurde eine Variante «Licht abend» auf einem Mittag-Grundbild abgewiesen — genau so, wie der Mac sie
bestellt. Und die Knotenansicht nannte ein ganz anderes Haus noch «deckungsgleich».

## Was neu ist (mit Entscheid und Stand)

| Fähigkeit | Entscheid | Stand |
|---|---|---|
| Eine Variante mit anderer Stimmung als ihr Grundbild (Licht oder Stimmungswort im Prompt) rechnet ein eigenes Grundbild, statt abgewiesen zu werden | 126, 138 | gebaut, mit Probe; Messung 342 offen |
| Die Knotenansicht zeigt «Form weicht ab» nach derselben, strengeren Prüfung wie das Ergebnis | 138 | gebaut, mit Probe |

## Stand am Gerät

* **Mac:** Update-Knopf. Prüfen: auf einem Mittag-Bild die Stimmung «Abend» wählen und eine Variante bestellen — es
  entsteht ein Bild.
* **Heim-PC:** `git pull`, Dienst und Abholer neu starten; dann Auftrag 342.

## Bekannte Grenzen (schlechte Nachrichten bleiben drin)

* Eine Variante mit anderer Stimmung dauert länger, weil das Grundbild neu gerechnet wird.
* Mit Stärke 0,5 bleibt eine Variante gleicher Stimmung sehr nah am Grundbild.
* Stoff-Varianten mit gleichem Stoff rechnen ihr Grundbild doppelt.
* Die automatische Kamera «Eingang» kann zu tief stehen — Fix folgt.

## Prüfung

Volle Suite ohne GPU, grün (Zahl in `README.md`). iPad/Mac: Prüfstrecke `.github/workflows/ipad.yml`; der Job
`freigabe` legt die Freigabe erst auf `main` an.
