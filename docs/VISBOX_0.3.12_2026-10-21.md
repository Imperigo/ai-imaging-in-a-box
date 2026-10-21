# Visbox 0.3.12 — Fassungsblatt (21.10.2026)

**Codestand:** Fassung 0.3.12 auf `main` (Messschalter für das Licht ins KI-Bild); Vorgänger 0.3.11 = Tag `v0.3.11`

**Grundlage:** Entscheid 117; Plan `docs/PLAN_LICHT_INS_KI_BILD_2026-10-21.md`; Messauftrag `auf-20261021-298`;
Protokoll 74 §168; Einbau-Stand C96

Visbox zählt selbst (Entscheid 66): Bibliothek `aiimaging`, iPad-App und Mac-App tragen dieselbe Nummer
(`tests/test_versionsnummer.py`). Dieses Blatt ist der Text der Freigabe auf GitHub; die Mac-App zeigt daraus die
Zeilen des Abschnitts «Was neu ist».

## Warum 0.3.12

Das KI-Modell liest heute nur die Tiefe der Szene; das Licht der Stimmung kommt im KI-Bild nicht an. Der Owner hat
entschieden, zuerst zu messen und dann am Bild zu wählen (Entscheid 117). Dafür braucht der Heim-PC zwei Messschalter.

## Was neu ist (mit Entscheid und Stand)

| Fähigkeit | Entscheid | Stand |
|---|---|---|
| Messschalter «Farbabgleich»: das KI-Bild übernimmt die Farben des gerenderten Grundbilds, ohne dass sich an der Form etwas verschiebt (ab Werk aus) | 117 | gebaut, mit Probe; Messung 298 offen |
| Messschalter «Bildeingang» mit Stärke: das gerenderte Grundbild wird Ausgangspunkt des KI-Bilds, die Tiefe bleibt die Führung (ab Werk aus) | 117 | vorbereitet; am Heim-PC noch nie gerechnet, Messung 298 offen |

## Stand am Gerät

* **Mac:** Update-Knopf; an der Oberfläche ändert sich nichts.
* **Heim-PC:** `git pull`; ohne die Schalter rechnet alles wie in 0.3.11. Kein neues Modell, kein Download.

## Bekannte Grenzen (schlechte Nachrichten bleiben drin)

* Der Bildeingang ist hier nur bis zur Übergabe an das Modell geprüft; ob er rechnet, zeigt erst die Messung.
* Die Zahl «über den Umriss gebaut» misst breite Häuserzeilen zu klein; die Eichung folgt.
* Kugel, Gespräch und Einstellungs-Insel aus 0.3.9 sind am Gerät weiter unbestätigt.

## Prüfung

Volle Suite ohne GPU, grün (Zahl in `README.md`). iPad/Mac: Prüfstrecke `.github/workflows/ipad.yml`; der Job
`freigabe` legt die Freigabe erst auf `main` an.
