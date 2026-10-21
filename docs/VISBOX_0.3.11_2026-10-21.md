# Visbox 0.3.11 — Fassungsblatt (21.10.2026)

**Codestand:** Fassung 0.3.11 auf `main` (Warnsatz auch im Bild voller Häuser, Messschalter «leerer Hintergrund»); Vorgänger 0.3.10 = Tag `v0.3.10`

**Grundlage:** Befunde aus Auftrag `auf-20261021-296`; Plan `docs/PLAN_LICHT_INS_KI_BILD_2026-10-21.md`; Protokoll 74
§167; Einbau-Stand C95

Visbox zählt selbst (Entscheid 66): Bibliothek `aiimaging`, iPad-App und Mac-App tragen dieselbe Nummer
(`tests/test_versionsnummer.py`). Dieses Blatt ist der Text der Freigabe auf GitHub; die Mac-App zeigt daraus die
Zeilen des Abschnitts «Was neu ist».

## Warum 0.3.11

Die Messung 296 zeigte ein KI-Bild, das fast das ganze Bild als Haus malte und trotzdem ohne Warnung blieb, weil das
Modell zufällig zu einem Fünftel überdeckt war.

## Was neu ist (mit Entscheid und Stand)

| Fähigkeit | Entscheid | Stand |
|---|---|---|
| Der Satz «Haus im KI-Bild nicht wiederzuerkennen» kommt auch, wenn die KI viel mehr Gebäude malt als modelliert, und nennt seinen Auslöser | — (296) | gebaut, mit Probe; Schwellen gesetzt, nicht gemessen |
| Die Prüfung sagt bei jedem gemessenen Bild ausdrücklich, ob der Umriss gilt | — (296) | gebaut, mit Probe |
| Messschalter «leerer Hintergrund» (ab Werk aus), damit die Messung prüfen kann, ob er das Haus im Umriss hält | — (296) | gebaut, mit Probe; Messung 297 offen |

## Stand am Gerät

* **Mac:** Update-Knopf; an der Oberfläche ändert sich nichts.
* **Heim-PC:** `git pull`; ohne den neuen Schalter bleibt jedes Bild wie in 0.3.10, nur der Warnsatz kommt öfter.

## Bekannte Grenzen (schlechte Nachrichten bleiben drin)

* **Das Licht der Stimmung kommt im KI-Bild nicht an:** Das KI-Modell liest nur die Tiefe der Szene, nicht das
  gerenderte Grundbild (gemessen). Die Stimmung wirkt dort nur über den Text. Wie es weitergeht, entscheidet der Owner
  (Plan-Blatt Licht ins KI-Bild).
* Die KI baut weiter über den Umriss hinaus und malt Sichtbeton nur teilweise.
* Kugel, Gespräch und Einstellungs-Insel aus 0.3.9 sind am Gerät weiter unbestätigt.

## Prüfung

Volle Suite ohne GPU, grün (Zahl in `README.md`). iPad/Mac: Prüfstrecke `.github/workflows/ipad.yml`; der Job
`freigabe` legt die Freigabe erst auf `main` an.
