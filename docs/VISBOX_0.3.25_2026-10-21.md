# Visbox 0.3.25 — Fassungsblatt (21.10.2026)

**Codestand:** Fassung 0.3.25 auf `main` (Grenze «deckungsgleich» aus Messung, Assistent ohne nachgesprochenen
Beispielsatz, kleine Anzeigefehler, Rang-Regel); Vorgänger 0.3.24 = Tag `v0.3.24`

**Grundlage:** Ergebnisse 317, 318, 319; Protokoll 74 §215; Einbau-Stand C129. Abgeglichen gegen alle Änderungen seit
`v0.3.24` (`git log v0.3.24..` ohne Zusammenführungen).

Visbox zählt selbst (Entscheid 66): Bibliothek `aiimaging`, iPad-App und Mac-App tragen dieselbe Nummer
(`tests/test_versionsnummer.py`). Dieses Blatt ist der Text der Freigabe auf GitHub; die Mac-App zeigt daraus die
Zeilen des Abschnitts «Was neu ist».

## Warum 0.3.25

Mit M2 halten Varianten die Form — die Prüfung meldete aber trotzdem «Form weicht ab», weil ihre Grenze geschätzt
war. Jetzt ist sie gemessen. Dazu sprach der Assistent einen Beispielsatz aus seiner Anleitung nach.

## Was neu ist (mit Entscheid und Stand)

| Fähigkeit | Entscheid | Stand |
|---|---|---|
| «deckungsgleich» ab Kanten-Übereinstimmung 0,10 statt 0,30 — gesetzt aus vier gemessenen Läufen (ohne M2 0,03, mit M2 0,20 und mehr) | — (317) | gebaut, mit Probe |
| Der Assistent spricht keinen Beispielsatz mehr nach; Sätze über Karten, die es im Gespräch nicht gibt, werden verworfen; Neu-und-verbinden geht über ein Paket | — (319) | gebaut, mit Probe; Messung 320 offen |
| «Umriss halten: aus» erscheint als «aus» (nicht leer); die Herkunft des Geländes nennt Name und Rolle | — (318/319) | gebaut, mit Probe |
| Der Hausanteil am KI-Bild sagt, wo seine Zählung aufhörte (für den einen Fall, der noch abweicht) | — (317) | gebaut, mit Probe; Messung 320 offen |
| Verständlicher Satz im Protokoll des Heim-PCs zur «geschenkten» Umriss-Treue | — (318) | gebaut |
| Ergebnisse der HomeStation dürfen Lücken in der Reihenfolge hinterlassen; die Prüfung für Ergebnis-Commits steht im Auftrags-Blatt | — | gebaut, mit Probe |

## Stand am Gerät

* **Heim-PC:** `git pull`, Dienst und Abholer neu starten; dann Auftrag 320.
* **Mac:** Update-Knopf; die Marke «deckungsgleich» erscheint jetzt bei M2-Varianten.

## Bekannte Grenzen (schlechte Nachrichten bleiben drin)

* Beim nahen Haus liegt die Schätzung des Hausanteils noch deutlich unter der Handzählung (0,31 gegen 0,46); 320 misst
  die Ursache.
* Die Assistent-Korrekturen sind noch nicht am Heim-PC bestätigt.

## Prüfung

Volle Suite ohne GPU, grün (Zahl in `README.md`). iPad/Mac: Prüfstrecke `.github/workflows/ipad.yml`; der Job
`freigabe` legt die Freigabe erst auf `main` an.
