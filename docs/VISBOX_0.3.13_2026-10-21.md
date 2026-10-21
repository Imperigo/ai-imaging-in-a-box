# Visbox 0.3.13 — Fassungsblatt (21.10.2026)

**Codestand:** Fassung 0.3.13 auf `main` (Zahl «über den Umriss» geeicht, Bildeingang mit Speicherschutz); Vorgänger 0.3.12 = Tag `v0.3.12`

**Grundlage:** Entscheid 117; Befunde aus `auf-20261021-297` und `auf-20261021-298`; Plan
`docs/PLAN_LICHT_INS_KI_BILD_2026-10-21.md`; Protokoll 74 §169–§170; Einbau-Stand C97–C98

Visbox zählt selbst (Entscheid 66): Bibliothek `aiimaging`, iPad-App und Mac-App tragen dieselbe Nummer
(`tests/test_versionsnummer.py`). Dieses Blatt ist der Text der Freigabe auf GitHub; die Mac-App zeigt daraus die
Zeilen des Abschnitts «Was neu ist».

## Warum 0.3.13

Die Messung 297 zeigte, dass die Zahl «über den Umriss gebaut» eine Häuserzeile knapp hinter dem Haus übersah. Die
Messung 298 zeigte, dass der Bildeingang mehr Grafikspeicher braucht als angenommen und dass am Ergebnis nicht zu sehen
war, ob er gerechnet hat.

## Was neu ist (mit Entscheid und Stand)

| Fähigkeit | Entscheid | Stand |
|---|---|---|
| Die Zahl «über den Umriss gebaut» zählt alles, was nicht Himmel ist — geeicht an Nachzählungen; ein Gipsmodell vor einer Wand zählt wie bisher | — (297) | gebaut, mit Probe; Messung 299 offen |
| Der Bildeingang lädt nur, wenn die Grafikkarte den gemessenen Bedarf trägt und kein fremdes Modell darauf liegt; sonst klare Abweisung | 117 | gebaut, mit Probe; Messung 300 offen |
| Am Ergebnis steht, ob Bildeingang oder Farbabgleich gerechnet haben, mit Stärke und Schritten | 117 | gebaut, mit Probe |

## Stand am Gerät

* **Mac:** Update-Knopf; an der Oberfläche ändert sich nichts.
* **Heim-PC:** `git pull`; die Zahl «über den Umriss» wird bei Aussenbildern grösser (etwa 2 statt 0,3–1), die Warnung
  steht bei denselben Bildern. Ohne Messschalter rechnet das Bild gleich.

## Bekannte Grenzen (schlechte Nachrichten bleiben drin)

* Mit Bildeingang bis Stärke 0,7 ist das KI-Bild praktisch das gerenderte Gipsmodell mit Licht; Material und
  Beschreibung kommen nicht an. Höhere Stärken misst 300.
* Bilder, in denen statt des Hauses eine Häuserzeile steht, bekommen noch keinen Warnsatz; dafür fehlt das Augenurteil
  (299).
* Kugel, Gespräch und Einstellungs-Insel aus 0.3.9 sind am Gerät weiter unbestätigt.

## Prüfung

Volle Suite ohne GPU, grün (Zahl in `README.md`). iPad/Mac: Prüfstrecke `.github/workflows/ipad.yml`; der Job
`freigabe` legt die Freigabe erst auf `main` an.
