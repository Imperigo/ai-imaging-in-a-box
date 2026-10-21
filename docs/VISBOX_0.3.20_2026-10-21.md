# Visbox 0.3.20 — Fassungsblatt (21.10.2026)

**Codestand:** Fassung 0.3.20 auf `main` (Befunde aus dem Demolauf: Hausanteil, gesicherter Blick, grosse Ansicht,
Vergleich, Deckung, Lizenz-Satz; Heim-PC-Befunde 309–311); Vorgänger 0.3.19 = Tag `v0.3.19`

**Grundlage:** Blätter 39 und 41–45 der Entwurfsfläche; Entscheid 120; Befunde 309, 310, 311 und 289; Protokoll 74
§193–§199; Einbau-Stand C116–C120. Abgeglichen gegen alle Änderungen seit `v0.3.19` (`git log v0.3.19..` ohne
Zusammenführungen).

Visbox zählt selbst (Entscheid 66): Bibliothek `aiimaging`, iPad-App und Mac-App tragen dieselbe Nummer
(`tests/test_versionsnummer.py`). Dieses Blatt ist der Text der Freigabe auf GitHub; die Mac-App zeigt daraus die
Zeilen des Abschnitts «Was neu ist».

## Warum 0.3.20

Im Demolauf widersprachen Zahl und Bild sich sichtbar, der gute gesicherte Blick kam nicht in den Kamera-Knoten, das
fertige Bild war kaum zu sehen, und zwei Varianten sahen wie zwei Häuser aus. Diese Fassung behebt das, und sie
bringt die Fehler aus den letzten Heim-PC-Messungen in Ordnung.

## Was neu ist (mit Entscheid und Stand)

| Fähigkeit | Entscheid | Stand |
|---|---|---|
| Die Prüfung zeigt zwei Hausanteile: am Grundbild (gezählt) und am KI-Bild (geschätzt, ≈); rahmt die KI anders, steht «Ausschnitt anders» dabei, und «Geometrie 0.0» wird in Worten erklärt | — (Befund L4-2) | gebaut, mit Probe; Nachzählung 312 offen |
| Im Kamera-Knoten lässt sich ein gesicherter Blick direkt wählen, ohne 3D-Ansicht; gemerkt an seiner Kennung, ein umbenannter Blick bleibt gültig; die Standpunkte der Mappe stehen in derselben Liste | — (Befund L4-4) | gebaut, mit Probe; am Gerät unbestätigt |
| Die grosse Ansicht zeigt das Bild auf mindestens 70 % der Fläche, die Prüfwerte sind eingeklappt, das Urteil steht im Kopf; auf Wunsch öffnet sie bei «fertig» von selbst | — (Befund L4-14) | gebaut, mit Probe; am Gerät unbestätigt |
| Läufe derselben Grundlage lassen sich nebeneinander vergleichen; der Verlauf trennt nach Grundlage; Kuratieren kennt jeden Lauf | — (Befund L4-15) | gebaut, mit Probe |
| Varianten werden auf Deckung geprüft: gleiche Grundlage und Umrisse im Bild über einer Schwelle heisst «deckungsgleich», sonst «Form weicht ab» mit Warnung | — (Befund L4-1) | gebaut, mit Probe; Schwelle gesetzt, nicht gemessen |
| Blendet ein Entwurf den ganzen Bestand aus, sagt «Bestellen» das; der Heim-PC legt je Kamera eine Maske der Umgebung ab | — (Befund L4-5) | gebaut, mit Probe; Messung 313 offen |
| Bilder mit Qwen-Image-2.1 tragen den Satz «Lizenz offen — nicht für Wettbewerb oder Veröffentlichung» | 120 | gebaut, mit Probe |
| Kamera-, Stimmungs- und Varianten-Knoten stehen sauber in ihren Kästchen; «Himmel drehen» heisst kurz «Drehen»; Schriften und Pfeile mit genügend Kontrast | 115 | gebaut, mit Probe |
| Heim-PC: Gebäudewort im Prompt, wenn sonst nur die Stimmung bestellt ist; weniger Speicherbedarf beim Bildeingang; «ausserhalb des Umrisses» zählt den festgehaltenen Hintergrund nicht mehr mit; Schalter «Himmel sichtbar» (ab Werk aus) | — (309) | gebaut, mit Probe; Messung 314 offen |
| Assistent: nimmt keine Kartenkennung als Knoten an und ruft beim Bildwunsch wieder sein Werkzeug | — (310) | gebaut, mit Probe; Messung 314 offen |
| Ergebnisse tragen, wie das Bildmodell tatsächlich gerechnet hat (`angewandt.modus`) | — (Vertrag) | gebaut, mit Probe |
| Werkzeug, um einen falschen Eintrag im Gerätebuch gezielt zu entfernen | — (311) | gebaut, mit Probe |

## Stand am Gerät

* **Mac:** Update-Knopf. Dann: im Kamera-Knoten den Reiter «Blick» öffnen; ein Bild rechnen und gross ansehen; zwei
  Varianten nebeneinander stellen.
* **Heim-PC:** `git pull`. Danach rechnet er neu wie angesagt (Gebäudewort, Speicher, Umriss-Zählung, neue Felder
  `haus_anteil_*`, `deckung`, `kontext_maske`, `angewandt.modus`). Danach die Aufträge 312, 313 und 314.

## Bekannte Grenzen (schlechte Nachrichten bleiben drin)

* Die Grenzen für «Ausschnitt anders» und «deckungsgleich» sind gesetzt, nicht gemessen; 312 misst sie nach.
* «Bild aufs Blatt» in voller Auflösung ist noch nicht dabei; es wartet auf zwei Bausteine der Gegenseite.
* Die Geometrie-Treue ist noch kein Pflicht-Eingang des Bildmodells; zwei Varianten können darum weiter in der Form
  abweichen — die Fassung sagt es jetzt nur.
* Der Bestand zählt am Heim-PC noch als Bauwerk; ob er herausgenommen wird, entscheidet 313.
* Gesicherter Blick, grosse Ansicht und Vergleich sind am Gerät unbestätigt.

## Prüfung

Volle Suite ohne GPU, grün (Zahl in `README.md`). iPad/Mac: Prüfstrecke `.github/workflows/ipad.yml`; der Job
`freigabe` legt die Freigabe erst auf `main` an.
