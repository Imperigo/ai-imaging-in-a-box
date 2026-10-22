# Visbox 0.3.33 — Fassungsblatt (22.10.2026)

**Codestand:** Fassung 0.3.33 auf `main` (Grafikkarte vor jedem Bild frei); Vorgänger 0.3.32 = Tag `v0.3.32`

**Grundlage:** Entscheid 127; Protokoll 74 §228; Einbau-Stand C139. Abgeglichen gegen alle Änderungen seit `v0.3.32`
(`git log v0.3.32..` ohne Zusammenführungen).

Visbox zählt selbst (Entscheid 66): Bibliothek `aiimaging`, iPad-App und Mac-App tragen dieselbe Nummer
(`tests/test_versionsnummer.py`). Dieses Blatt ist der Text der Freigabe auf GitHub; die Mac-App zeigt daraus die
Zeilen des Abschnitts «Was neu ist».

## Warum 0.3.33

In der Generalprobe lag ein anderes Sprachmodell auf derselben Grafikkarte. Bildmodell und Sprachmodell passten nicht
zusammen; danach antwortete der Assistent fast drei Minuten lang vom Prozessor aus. Entscheid 127: Visbox hat Vorrang.

## Was neu ist (mit Entscheid und Stand)

| Fähigkeit | Entscheid | Stand |
|---|---|---|
| Vor jedem Bild gibt Visbox jedes geladene Sprachmodell von der Grafikkarte frei, auch fremde; das fremde Programm lädt seins bei Bedarf neu | 127 | gebaut, mit Probe; Messung 329 offen |
| Im Ergebnis steht, was freigegeben wurde | 127 | gebaut, mit Probe |

## Stand am Gerät

* **Heim-PC:** erst Auftrag 328 fertig rechnen, dann `git pull`, Dienst und Abholer neu starten; dann Auftrag 329.
* **Mac:** Update-Knopf.

## Bekannte Grenzen (schlechte Nachrichten bleiben drin)

* Fragt man den Assistenten, solange das Bildmodell nach dem Bild noch auf der Karte liegt, kann er weiter langsam sein;
  329 misst, wie lange das dauert.
* Ein wartender Bildauftrag nimmt einem anderen Programm sein Sprachmodell alle 30 s erneut weg — gewollt für die Demo.

## Prüfung

Volle Suite ohne GPU, grün (Zahl in `README.md`). iPad/Mac: Prüfstrecke `.github/workflows/ipad.yml`; der Job
`freigabe` legt die Freigabe erst auf `main` an.
