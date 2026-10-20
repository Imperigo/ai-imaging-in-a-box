# Visbox 0.3.5 — Fassungsblatt (20.10.2026)

**Codestand:** Fassung 0.3.5 auf `main` (Heim-PC rechnet Himmelsbilder, Kamera-Einstellungen und Materialien);
Vorgänger 0.3.4 = Tag `v0.3.4`

**Grundlage:** Entscheide 107, 109–113 (Blätter 31–33); Bauplan `docs/PLAN_KNOTEN_NEU_2026-10-20.md` (Schritte H1–H3);
Himmelsbilder und Texturen der HomeStation (CC0, am Heim-PC); Protokoll 74 §153

Visbox zählt selbst (Entscheid 66): Bibliothek `aiimaging`, iPad-App und Mac-App tragen dieselbe Nummer
(`tests/test_versionsnummer.py`). Dieses Blatt ist der Text der Freigabe auf GitHub; die Mac-App zeigt daraus die
Zeilen des Abschnitts «Was neu ist».

## Warum 0.3.5

Die neuen Knoten (Stimmung mit Himmelsbild, Kamera mit Einstellungen, Oberfläche und Material) brauchen zuerst einen
Heim-PC, der sie rechnet. Das ist dieser Schritt. Die Knoten selbst kommen in den nächsten Fassungen.

## Was neu ist (mit Entscheid und Stand)

| Fähigkeit | Entscheid | Stand |
|---|---|---|
| Heim-PC: Stimmung mit Himmelsbild als Licht in Blender (acht Stimmungen, Drehung, Stärke); ohne bestellte Sonne keine zusätzliche Sonnenlampe | 110 | gebaut, mit Probe; am Gerät unbestätigt (Auftrag 292) |
| Heim-PC: «Weiss (Studio)» macht alle Flächen weiss wie ein Gipsmodell | 113 (6) | gebaut, mit Probe; am Gerät unbestätigt |
| Heim-PC: Auto-Kamera mit Richtungen, Augenhöhe, Brennweite, «Haus füllt» (Vorgabe 70 %) und «Senkrechte gerade» je Auftrag | 109, 113 (5) | gebaut, mit Probe; am Gerät unbestätigt |
| Heim-PC: Materialien je Bauteil-Art (Fassade, Dach, Fenster, Boden, Übrige; Türen = Übrige) aus elf Texturen, mit Relief, Tönung und Fugen bei der Lattung | 111, 113 (7) | gebaut, mit Probe; am Gerät unbestätigt |
| Heim-PC: Fehlt ein Himmelsbild oder eine Textur, wird der Auftrag mit Satz und Namen abgewiesen | 113 (2) | gebaut, mit Probe |
| Heim-PC: Das Ergebnis nennt, was angewandt wurde und welche Vorgaben der Heim-PC selbst gesetzt hat | — | gebaut, mit Probe |
| Heim-PC: Der Satz beim Entladen des Assistenten-Modells kommt jetzt bis zum Mac | auf-291 | behoben, mit Probe |

## Stand am Gerät

* **Heim-PC:** nach `git pull` Dienst und Abholer neu starten; Auftrag 292 rechnet je Stimmung ein Bild, das Gipsmodell,
  die Kamera und zwei Materialien.
* **Mac und iPad:** unverändert gegenüber 0.3.4 — die Knoten zum Bedienen kommen danach.

## Bekannte Grenzen (schlechte Nachrichten bleiben drin)

* **Noch nicht bedienbar:** In der Knotenansicht gibt es die neuen Einstellungen erst mit den nächsten Fassungen.
* **Am Gerät nicht geprüft**, auch nicht, wie die Himmelsbilder und Texturen im Bild wirken.
* Nicht quadratische Texturen werden nur in einer Achse korrigiert; Böden können leicht verzerrt sein.
* Dächer aus IFC-Modellen werden ohne Angabe des Dachtyps nicht als Dach erkannt.
* Eine Grundlage passt nur noch zur gleichen Stimmung, zu denselben Materialien und Kamera-Einstellungen.

## Prüfung

Volle Suite ohne GPU, grün (Zahl in `README.md`). iPad/Mac: Prüfstrecke `.github/workflows/ipad.yml`; der Job
`freigabe` legt die Freigabe erst auf `main` an.
