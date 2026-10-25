# Visbox 0.3.67 — Fassungsblatt (25.10.2026)

**Codestand:** Fassung 0.3.67 auf `main` (Mac-Befunde 0.3.66, Umfeld nur auf freiem Boden, Marke «freies Bild»);
Vorgänger 0.3.66 = Tag `v0.3.66`

**Grundlage:** Mac-Prüfzeilen 0.3.66 (Demotester); Ergebnis 364; Owner-Entscheid 152; Protokoll 74 §291–§293; Einbau-Stand
C201, C207–C210; Aufträge 366 (365 zurückgezogen). Abgeglichen gegen alle Änderungen seit `v0.3.66`
(`git log v0.3.66..` ohne Zusammenführungen).

Visbox zählt selbst (Entscheid 66): Bibliothek `aiimaging`, iPad-App und Mac-App tragen dieselbe Nummer
(`tests/test_versionsnummer.py`). Dieses Blatt ist der Text der Freigabe auf GitHub; die Mac-App zeigt daraus die
Zeilen des Abschnitts «Was neu ist».

## Warum 0.3.67

Am Mac rechnete eine Variante über Claude mit 0,5 statt 0,7, der gewählte Standpunkt wurde ignoriert, «Grundbild
rendern» rechnete ohne Änderung neu, «Freies Bild» fehlte in Claudes Werkzeugliste, mit vier Kameras fand kein Auto
Platz, und die Marke «freies Bild» war abgeschnitten. Der Owner entschied, dass das Umfeld nie auf Platten steht.

## Was neu ist (mit Entscheid und Stand)

| Fähigkeit | Entscheid | Stand |
|---|---|---|
| Varianten tragen eine Marke und rechnen auch ohne passende Grundlage mit 0,7 (grosse Anlagen 0,5) | 149 | gebaut, mit Probe; Messung 366 offen |
| Ein gewählter Standpunkt («sSE») gilt — nur diese Kamera wird gerechnet | — | gebaut, mit Probe; Messung 366 offen |
| Ein Variantenlauf merkt sich sein Grundbild; «Grundbild rendern» ohne Änderung nennt es und rechnet nicht neu | 146 | gebaut, mit Probe; Messung 366 offen |
| «Freies Bild» steht mit Erklärung in Claudes Werkzeugliste | 149 | gebaut, mit Probe |
| Umfeld auf grossen Anlagen nur auf freiem Boden (und grossen Bodenplatten), nie auf 2-m-Platten; was fehlt, mit Satz | 152 | gebaut, mit Probe |
| Autos dürfen vor dem Haus stehen, wenn sie nur den Sockel (bis 2,2 m) decken — auch bei vier Kameras rundum | — | gebaut, mit Probe; am Gerät offen |
| Stellt das Umfeld Bäume, werden die Bäume des Modells ausgeblendet | — | gebaut, mit Probe; am Gerät offen |
| Die Marke «freies Bild» ist auf jeder Fläche ganz sichtbar | 149 | gebaut, mit Probe |

## Stand am Gerät

* **Mac:** Update-Knopf, danach die Claude-Sitzung neu verbinden. Prüfen: «Variante Abend nur von Südost» → ein Bild mit
  0,7; danach «Grundbild rendern» → kein neuer Lauf.
* **Heim-PC:** `git pull`, Dienst und Abholer neu starten; dann Auftrag 366.

## Bekannte Grenzen (schlechte Nachrichten bleiben drin)

* Am Wettbewerbsmodell stehen nach Entscheid 152 deutlich weniger Bäume beim Bau mit Innenhof.
* Die Sockel-Regel für Autos ändert auch Bilder mit drei Kameras; am Gerät ungeprüft.
* Modellbäume ohne Pflanzenwort im Namen bleiben stehen.
* `vis_render` kennt noch keine Standpunkt-Wahl.

## Prüfung

Volle Suite ohne GPU, grün (Zahl in `README.md`). iPad/Mac: Prüfstrecke `.github/workflows/ipad.yml`; der Job
`freigabe` legt die Freigabe erst auf `main` an.
