# Visbox 0.3.21 — Fassungsblatt (21.10.2026)

**Codestand:** Fassung 0.3.21 auf `main` (fertige Bilder exportieren im Original); Vorgänger 0.3.20 = Tag `v0.3.20`

**Grundlage:** Blatt 46 der Entwurfsfläche; Video-Befunde L4-16, L3-A4/A5; Protokoll 74 §201–§202; Einbau-Stand C121.
Abgeglichen gegen alle Änderungen seit `v0.3.20` (`git log v0.3.20..` ohne Zusammenführungen).

Visbox zählt selbst (Entscheid 66): Bibliothek `aiimaging`, iPad-App und Mac-App tragen dieselbe Nummer
(`tests/test_versionsnummer.py`). Dieses Blatt ist der Text der Freigabe auf GitHub; die Mac-App zeigt daraus die
Zeilen des Abschnitts «Was neu ist».

## Warum 0.3.21

Im Demolauf lagen die fertigen Bilder nur auf dem Heim-PC; ein Bildschirmausschnitt war das einzige, was weiterging.
Diese Fassung gibt jedes fertige Bild in Originalauflösung heraus.

## Was neu ist (mit Entscheid und Stand)

| Fähigkeit | Entscheid | Stand |
|---|---|---|
| «Exportieren» in der grossen Ansicht und beim Bildpaar sichert das fertige Bild in Originalauflösung über den Sichern-Dialog des Mac; bei Teil- und Zwischenbildern gesperrt, mit Grund | — (Befund L4-16) | gebaut, mit Probe; am Gerät unbestätigt |
| Die Knotenansicht ist auf dem neuesten Stand der Vorlage (Insel und Legende rücken über Claudes Karten; in Visbox ohne sichtbare Änderung) | 115 | gebaut, mit Probe |

## Stand am Gerät

* **Mac:** Update-Knopf. Dann: ein fertiges Bild gross öffnen, «Exportieren», Ort wählen — die Datei hat die volle
  Auflösung des Laufs.
* **Heim-PC:** `git pull`; am Rechnen ändert sich nichts.

## Bekannte Grenzen (schlechte Nachrichten bleiben drin)

* Visbox hat kein Blatt; «Aufs Blatt» gibt es nur in der Vorlage. Dort wartet es auf zwei Bausteine der Gegenseite.
* Das allererste Bild eines Laufs (ohne Grundbild und Verlauf) öffnet noch nicht gross; die Frage dazu liegt beim
  Owner.
* Export am Gerät unbestätigt.

## Prüfung

Volle Suite ohne GPU, grün (Zahl in `README.md`). iPad/Mac: Prüfstrecke `.github/workflows/ipad.yml`; der Job
`freigabe` legt die Freigabe erst auf `main` an.
