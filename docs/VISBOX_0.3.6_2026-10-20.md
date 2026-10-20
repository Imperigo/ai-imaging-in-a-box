# Visbox 0.3.6 — Fassungsblatt (20.10.2026)

**Codestand:** Fassung 0.3.6 auf `main` (Himmel nur als Licht, Belichtung je Stimmung, Befunde aus Auftrag 292);
Vorgänger 0.3.5 = Tag `v0.3.5`

**Grundlage:** Ergebnis der HomeStation `auf-20261020-292` (23 Probebilder); Tausch der Himmelsbilder durch die
HomeStation; Protokoll 74 §154

Visbox zählt selbst (Entscheid 66): Bibliothek `aiimaging`, iPad-App und Mac-App tragen dieselbe Nummer
(`tests/test_versionsnummer.py`). Dieses Blatt ist der Text der Freigabe auf GitHub; die Mac-App zeigt daraus die
Zeilen des Abschnitts «Was neu ist».

## Warum 0.3.6

Die ersten Probebilder mit Himmelsbild zeigten das Haus vor einem Fotohintergrund (bei «Abend» ein Wald mit Felsen)
und bei «Mittag» rein weiss überstrahlt. Jetzt gibt der Himmel nur Licht, und die Belichtung passt sich der Stimmung an.

## Was neu ist (mit Entscheid und Stand)

| Fähigkeit | Entscheid | Stand |
|---|---|---|
| Heim-PC: Das Himmelsbild gibt nur Licht und Spiegelungen; hinter dem Haus steht ein ruhiger Verlauf in den Farben dieses Himmels | 110 | gebaut, mit Probe; am Gerät unbestätigt (Auftrag 293) |
| Heim-PC: Tonwerte, die nicht ausbrennen, und Belichtung je Stimmung; Abend warm, Winter kühl | 110 | gebaut, mit Probe; Werte gesetzt, nicht gemessen |
| Heim-PC: Das Ergebnis misst, wie viel vom Haus voll weiss ist, und warnt ab 1 % | — | gebaut, mit Probe |
| Heim-PC: Neue Himmelsbilder — reine Himmel, echter Sonnenuntergang, Dämmerung, Studio für «Weiss» | 110 | am Heim-PC abgelegt, als Vorgabe eingetragen |
| Heim-PC: Das Gelände bekommt nie ein Material | 111 | behoben, mit Probe |
| Heim-PC: Die bestellte Bildgrösse wird genau gerechnet (960 × 600 statt 960 × 592) | auf-292 | behoben, mit Probe |
| Heim-PC: Die Standpunkte für die Kamera-Vorschau rechnen mit dem Seitenverhältnis des Auftrags | auf-292 | behoben, mit Probe |
| Heim-PC: Die Vorschau steuert immer mit voller Stärke (folgt der Gebäudeform besser, gemessen) | 104, auf-292 | gebaut, mit Probe |
| Heim-PC: Eine Variante, die nicht zur Grundlage passt, wird schon beim Anlegen abgewiesen (409) | Integrator | gebaut, mit Probe |
| Heim-PC: Eine unbekannte Material-Kennung liefert ein Ergebnis mit Satz | 113 (2) | behoben, mit Probe |

## Stand am Gerät

* **Heim-PC:** nach `git pull` Dienst und Abholer neu starten; Auftrag 293 rechnet alle acht Stimmungen nochmals.
* **Mac und iPad:** unverändert gegenüber 0.3.5.

## Bekannte Grenzen (schlechte Nachrichten bleiben drin)

* **Ob das Haus jetzt in jeder Stimmung lesbar ist, zeigt erst Auftrag 293.** Die Belichtung je Stimmung ist gesetzt,
  nicht gemessen.
* **Bestehende Grundlagen mit gerundeter Höhe** (z. B. 1600 × 992) passen nicht mehr und werden neu gerechnet.
* In der Vorschau können unleserliche Schriftzeilen erscheinen; ein Gegenmittel ist noch nicht belegt.
* Die Maserung der Holzlattung läuft noch quer zu den Latten.

## Prüfung

Volle Suite ohne GPU, grün (Zahl in `README.md`). iPad/Mac: Prüfstrecke `.github/workflows/ipad.yml`; der Job
`freigabe` legt die Freigabe erst auf `main` an.
