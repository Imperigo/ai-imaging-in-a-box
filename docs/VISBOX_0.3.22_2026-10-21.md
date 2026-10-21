# Visbox 0.3.22 — Fassungsblatt (21.10.2026)

**Codestand:** Fassung 0.3.22 auf `main` (Variante ohne Modelldatei wird gerechnet); Vorgänger 0.3.21 = Tag `v0.3.21`

**Grundlage:** Befund aus der Test-App (Auftrag vis-1792595849-002a06 «liegengelassen — render-scene ohne
'geometry.path'»); Protokoll 74 §204; Einbau-Stand C122. Abgeglichen gegen alle Änderungen seit `v0.3.21`
(`git log v0.3.21..` ohne Zusammenführungen).

Visbox zählt selbst (Entscheid 66): Bibliothek `aiimaging`, iPad-App und Mac-App tragen dieselbe Nummer
(`tests/test_versionsnummer.py`). Dieses Blatt ist der Text der Freigabe auf GitHub; die Mac-App zeigt daraus die
Zeilen des Abschnitts «Was neu ist».

## Warum 0.3.22

«Variante erzeugen» nach «Grundlage rendern» wurde am Heim-PC nie gerechnet: Die Bestellung nennt — wie vereinbart —
die Grundlage statt einer Modelldatei, der Heim-PC verlangte aber immer die Datei. Vor der Demo am 29.10. ist das der
wichtigste Weg.

## Was neu ist (mit Entscheid und Stand)

| Fähigkeit | Entscheid | Stand |
|---|---|---|
| Eine Variante mit gültiger Grundlage und ohne Modelldatei wird gerechnet: das Modell kommt vom Grundlage-Auftrag, sonst rechnet der Heim-PC aus der abgelegten Grundlage allein (mit Warnung); eine unbekannte Grundlage endet mit klarem Satz, ohne Blender und ohne Bildmodell | — (Befund Test-App) | gebaut, mit Probe; Messauftrag 315 offen |
| Neu abgelegte Grundlagen tragen Bestand und Modellstand mit (ältere bleiben gültig) | — | gebaut, mit Probe |

## Stand am Gerät

* **Heim-PC:** `git pull`, Dienst und Abholer neu starten. Dann Auftrag 315: «Grundlage rendern» → «Variante
  erzeugen» einmal echt.
* **Mac:** Update-Knopf; sichtbar ändert sich nichts.

## Bekannte Grenzen (schlechte Nachrichten bleiben drin)

* Rechnet der Heim-PC aus der Grundlage allein (ohne Modell), bleiben Rahmungsbox und Modellstand ungeprüft — die
  Warnung steht am Auftrag.
* Der echte Lauf in der Test-App steht noch aus (315).

## Prüfung

Volle Suite ohne GPU, grün (Zahl in `README.md`). iPad/Mac: Prüfstrecke `.github/workflows/ipad.yml`; der Job
`freigabe` legt die Freigabe erst auf `main` an.
