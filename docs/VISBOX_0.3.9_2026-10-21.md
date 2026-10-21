# Visbox 0.3.9 — Fassungsblatt (21.10.2026)

**Codestand:** Fassung 0.3.9 auf `main` (Assistent und Einstellungen als Inseln, Licht von der Seite); Vorgänger 0.3.8 = Tag `v0.3.8`

**Grundlage:** Entscheide 115, 116; Plan `docs/PLAN_UI_GLEICHHEIT_2026-10-20.md` (Stufen S3 und S4); Befunde aus Auftrag
`auf-20261020-294`; Protokoll 74 §161–§162; Einbau-Stand C90–C91

Visbox zählt selbst (Entscheid 66): Bibliothek `aiimaging`, iPad-App und Mac-App tragen dieselbe Nummer
(`tests/test_versionsnummer.py`). Dieses Blatt ist der Text der Freigabe auf GitHub; die Mac-App zeigt daraus die
Zeilen des Abschnitts «Was neu ist».

## Warum 0.3.9

Mit 0.3.8 standen die Kopfteile in der Knotenansicht, Assistent und Einrichten aber noch als eigene Mac-Fenster daneben.
Die Messung 294 zeigte zudem, dass die Sonne in allen Stimmungen fast hinter der Kamera stand.

## Was neu ist (mit Entscheid und Stand)

| Fähigkeit | Entscheid | Stand |
|---|---|---|
| Assistenten-Kugel unten rechts mit Gesprächsfeld; der Assistent (am Heim-PC) schlägt vor, Anwenden und Ablehnen an der Karte; ohne Heim-PC steht ein klarer Satz statt der Eingabe | 115, 116 (2) | gebaut, mit Probe; am Gerät unbestätigt |
| Einstellungen als Insel (Zahnrad oder Heim-PC-Chip): Anzeige, Darstellung, Bewegung & Klang, Heim-PC, «Wer rechnet?», «Claude über MCP», Lizenzen, Neuigkeiten; Adresse und Kennwort des Heim-PC bleiben in der Mac-App | 115, 116 (6) | gebaut, mit Probe; am Gerät unbestätigt |
| Die Assistent-Leiste fällt in der Knotenansicht weg und bleibt nur auf der Visbox-Seite | 115, 116 (8) | gebaut, mit Probe |
| Stimmungen: Sonne je Kamera seitlich (Streiflicht, Schatten neben dem Haus), weiche Lampe bei Morgen und Winter, Blaue Stunde dunkler, Abend nicht mehr wie Nacht | — (294) | gebaut, mit Probe; Messung 295 offen |
| Deutsche Bildbeschreibungen mit englischem Zusatz werden übersetzt | — (294) | gebaut, mit Probe |
| Neue Zahl: wieviel das KI-Bild über den Umriss hinaus baut, mit Satz ab einem Viertel der Hausfläche (kein Tor) | — (294) | gebaut, mit Probe; Schwelle gesetzt, nicht gemessen |

## Stand am Gerät

* **Mac:** Update-Knopf (ab 0.3.8 lädt er die neueste Fassung). Danach: Kugel öffnen, eine Frage stellen, eine Karte
  anwenden; Zahnrad öffnen, «Wer rechnet?» und «Claude über MCP» ansehen.
* **Heim-PC:** `git pull`; mit Stimmung dreht sich das Himmelsbild je Kamera, gespeicherte Grundlagen mit Stimmung werden
  neu gerechnet; gemischte Bildbeschreibungen gehen englisch in den KI-Schritt. Ohne Stimmung bleibt das Grundbild gleich.

## Bekannte Grenzen (schlechte Nachrichten bleiben drin)

* **Am Gerät nicht geprüft** — Kugel, Gespräch und Einstellungs-Insel sind nur durch Proben und die Prüfstrecke belegt.
* Die Lichtwinkel und die Schwelle für «über den Umriss» sind gesetzt, nicht gemessen; die Messung 295 steht aus.
* Die Befehlspalette (⌘K) fehlt noch.

## Prüfung

Volle Suite ohne GPU, grün (Zahl in `README.md`). iPad/Mac: Prüfstrecke `.github/workflows/ipad.yml`; der Job
`freigabe` legt die Freigabe erst auf `main` an.
