# Visbox 0.3.2 — Fassungsblatt (20.10.2026)

**Codestand:** Fassung 0.3.2 auf `main` (schnelle KI-Vorschau am Heim-PC, Abbruch nach der Geräteprobe richtig);
Vorgänger 0.3.1 = Tag `v0.3.1` (ohne Heim-PC bleibt die Mac-App bedienbar)

**Grundlage:** Demolauf 16.10.2026 (Video-Analyse L4-17); Entscheide 104–104b; Blatt 29 der Entwurfsfläche; Geräteprobe
des Abholers durch die HomeStation am 20.10.2026; Protokoll 74 §148

Visbox zählt selbst (Entscheid 66): Bibliothek `aiimaging`, iPad-App und Mac-App tragen dieselbe Nummer
(`tests/test_versionsnummer.py`). Dieses Blatt ist der Text der Freigabe auf GitHub; die Mac-App zeigt daraus die
Zeilen des Abschnitts «Was neu ist».

## Warum 0.3.2

Im Demolauf kostete jede KI-Variante rund 9 Minuten. Die Ursache war das Forschungsmodell qwen-image-2.1 (40 Schritte,
Lizenz offen), nicht die Vorgabe. Der Heim-PC rechnet jetzt auf Wunsch eine **Vorschau**: schnell, mit dem frei
lizenzierten Vorgabemodell, und geprüft wie jedes Bild. Dazu sind die fünf Fehler behoben, die die HomeStation beim
Abbrechen am Gerät gefunden hat.

## Was neu ist (mit Entscheid und Stand)

| Fähigkeit | Entscheid | Stand |
|---|---|---|
| Heim-PC: Güte «Vorschau» — immer z-image-turbo, 8 Schritte, ein Zufallswert, kleineres KI-Bild (lange Seite 1024), danach auf die Grösse der Grundlage gebracht; geprüft wie jedes Bild, Urteil beginnt mit «VORSCHAU» | 104, 104a | gebaut, mit Probe; Zeit am Gerät ungemessen (Auftrag 290) |
| Heim-PC: Güte «Voll» oder ohne Angabe rechnet wie bisher | 104 | unverändert, mit Probe |
| Heim-PC: Die Grundlage bleibt bei der Vorschau unverändert und ist danach für «Voll» wiederverwendbar | Nr. 85 | gebaut, mit Probe |
| Heim-PC: Ein Teilbild nach Abbruch trägt die Kamera seines Bilds (bisher den Namen der nächsten Kamera) | Geräteprobe 20.10. | behoben, mit Probe |
| Heim-PC: Der Abbruchsatz nennt den nächsten Schritt («… vor dem Bildmodell»); der Fortschritt endet mit «abgebrochen» | Geräteprobe 20.10. | behoben, mit Probe |
| Heim-PC: Die Freigabe nennt das Gerät nur, wenn es sich meldet; sonst neutral | Geräteprobe 20.10. | behoben, mit Probe |
| Heim-PC: Der Laufzettel wird unter Sperre geschrieben; ein Abbruch kann nicht mehr überschrieben werden | Geräteprobe 20.10. | behoben, mit Probe |

## Stand am Gerät

* **Heim-PC:** nach `git pull` Abholer und Dienst neu starten; Auftrag 290 misst Vorschau gegen Voll und wiederholt
  die Abbruchproben.
* **Mac und iPad:** unverändert gegenüber 0.3.1. Der Schalter «Güte» am Render-Knoten kommt mit der nächsten
  Knotenansicht.

## Bekannte Grenzen (schlechte Nachrichten bleiben drin)

* **Die Zeit der Vorschau ist ungemessen.** Das Ziel ist höchstens 2 Minuten je Variante; ob es erreicht wird, zeigt
  Auftrag 290.
* **Die Vorschau zeigt nicht das gewählte Modell**, wenn «Voll» ein anderes rechnet (z. B. qwen-image-2.1): Sie ist
  ein schneller Blick auf Licht und Komposition, nicht auf den Stil des anderen Modells.
* **Mit angehängter Skizze gilt die Güte noch nicht**; der Skizzen-Weg rechnet wie bisher.
* **Ohne mitbestellte Grundlage** rechnet auch die Vorschau Blender in voller Grösse.
* Die Sperre beim Schreiben wirkt nur unter Linux und macOS; unter Windows bleibt nur die Wache, die ein gesetztes
  «abgebrochen» behält.

## Prüfung

Volle Suite ohne GPU, grün (Zahl in `README.md`). iPad/Mac: Prüfstrecke `.github/workflows/ipad.yml`; der Job
`freigabe` legt die Freigabe erst auf `main` an.
