# Visbox 0.3.26 — Fassungsblatt (21.10.2026)

**Codestand:** Fassung 0.3.26 auf `main` (Assistent rendert wieder auf Bildwunsch, Freigabesatz sicher, Hausanteil beim
nahen Haus, Paketweg in den Werkzeugbeschreibungen); Vorgänger 0.3.25 = Tag `v0.3.25`

**Grundlage:** Ergebnis 320; Protokoll 74 §216–§217; Einbau-Stand C130–C131. Abgeglichen gegen alle Änderungen seit
`v0.3.25` (`git log v0.3.25..` ohne Zusammenführungen).

Visbox zählt selbst (Entscheid 66): Bibliothek `aiimaging`, iPad-App und Mac-App tragen dieselbe Nummer
(`tests/test_versionsnummer.py`). Dieses Blatt ist der Text der Freigabe auf GitHub; die Mac-App zeigt daraus die
Zeilen des Abschnitts «Was neu ist».

## Warum 0.3.26

Messung 320 zeigte einen Rückschritt: Auf einen Bildwunsch füllte der Assistent Einstellungen aus, die es nicht gibt,
und kam nach drei Runden ohne Render-Karte zurück. Für die Demo muss genau das gehen.

## Was neu ist (mit Entscheid und Stand)

| Fähigkeit | Entscheid | Stand |
|---|---|---|
| Auf einen Bildwunsch entsteht wieder eine Render-Karte: erfundene Einstellungen werden weggelassen (mit Satz), statt den Aufruf abzuweisen; genannte Werte werden gegen die erlaubten geprüft | — (320) | gebaut, mit Probe; Messung 321 offen |
| «Freigeben kann nur der Architekt …» steht am Anfang jeder Antwort auf eine Frage nach der Freigabe | — (320) | gebaut, mit Probe |
| Claude und Assistent lesen an «Knoten setzen» und «Verbinden»: neu und gleich verbinden geht über ein Paket | — (319) | gebaut, mit Probe |
| Hausanteil am KI-Bild: Rahmt die KI näher, schneidet die Bodenlinie der Grundlage das Haus nicht mehr ab; die Gründe, wo die Zählung aufhörte, stehen als Flächenanteile | — (320) | gebaut, mit Probe; Messung 321 offen |
| «Nur Grundlage» legt den Maskenbefund ab | — (320) | gebaut, mit Probe |
| «Sichtbackstein» wird im Prompt übersetzt | — | gebaut, mit Probe |

## Stand am Gerät

* **Heim-PC:** `git pull`, Dienst und Abholer neu starten; dann Auftrag 321.
* **Mac:** Update-Knopf (die neue Werkzeugliste gilt erst mit der neuen App).

## Bekannte Grenzen (schlechte Nachrichten bleiben drin)

* Beim nahen Haus zählt die Schätzung jetzt eher zu viel (Hecken und Boden, erwartet ≈ 0,56 gegen 0,46 von Hand);
  321 zeigt, ob es eine eigene Grenze braucht.
* Ob das Sprachmodell den Paketweg wirklich wählt, ist noch nicht gemessen (321).

## Prüfung

Volle Suite ohne GPU, grün (Zahl in `README.md`). iPad/Mac: Prüfstrecke `.github/workflows/ipad.yml`; der Job
`freigabe` legt die Freigabe erst auf `main` an.
