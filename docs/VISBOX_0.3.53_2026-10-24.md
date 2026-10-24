# Visbox 0.3.53 — Fassungsblatt (24.10.2026)

**Codestand:** Fassung 0.3.53 auf `main` (Entscheid 143 und Folgen aus Ergebnis 347/348); Vorgänger 0.3.52 = Tag `v0.3.52`

**Grundlage:** Ergebnisse 347, 348; Protokoll 74 §274–§275; Einbau-Stand C189, C190 (erledigt), C191, C192, C193;
Entscheide 104, 138, 143. Abgeglichen gegen alle Änderungen seit `v0.3.52` (`git log v0.3.52..` ohne Zusammenführungen).

Visbox zählt selbst (Entscheid 66): Bibliothek `aiimaging`, iPad-App und Mac-App tragen dieselbe Nummer
(`tests/test_versionsnummer.py`). Dieses Blatt ist der Text der Freigabe auf GitHub; die Mac-App zeigt daraus die
Zeilen des Abschnitts «Was neu ist».

## Warum 0.3.53

Der Owner hat entschieden, dass Varianten ohne Wahl in voller Güte rechnen (Entscheid 143): Die Vorschau übermalte in
Messung 346 ein Fensterband. Dazu zählte die Formprüfung seit 0.3.52 die Kanten der Bäume mit und hätte ein übermaltes
Haus übersehen.

## Was neu ist (mit Entscheid und Stand)

| Fähigkeit | Entscheid | Stand |
|---|---|---|
| «Variante erzeugen» und der Varianten-Knoten rechnen ohne Wahl in voller Güte vom Grundbild aus; die Vorschau bleibt wählbar, mit Hinweis | 143 | gebaut, mit Probe; am Mac offen |
| Die Formprüfung («deckungsgleich») misst nur am Haus, nicht an Bäumen und Gelände | 138 | gebaut, mit Probe; Messung 349 offen |
| Das Ergebnis nennt die Ladezeit des Bildmodells getrennt von der Rechenzeit | — | gebaut, mit Probe; Messung 349 offen |

## Stand am Gerät

* **Mac:** Update-Knopf. Prüfen: «Variante erzeugen» ohne Klick liefert ein volles Bild mit gehaltenen Fenstern; der
  Güte-Schalter zeigt «Voll».
* **Heim-PC:** `git pull`, Dienst und Abholer neu starten; dann Auftrag 349. Kein Bild ändert sich.

## Bekannte Grenzen (schlechte Nachrichten bleiben drin)

* Eine Variante in voller Güte dauert länger (rund 33–45 s je Bild statt 26–36 s); in Messung 347 einmal 53 s — die
  Ursache misst Auftrag 349.
* Ein Baum vor der Hauskante kann in der Vorschau halb durchscheinend wirken.

## Prüfung

Volle Suite ohne GPU, grün (Zahl in `README.md`). iPad/Mac: Prüfstrecke `.github/workflows/ipad.yml`; der Job
`freigabe` legt die Freigabe erst auf `main` an.
