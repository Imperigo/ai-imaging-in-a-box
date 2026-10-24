# Visbox 0.3.58 — Fassungsblatt (24.10.2026)

**Codestand:** Fassung 0.3.58 auf `main` (Knoten «Umfeld», grosse Modelle und Vogelschau); Vorgänger 0.3.57 = Tag
`v0.3.57`

**Grundlage:** Owner-Auftrag 24.10. (Umfeld aus freien 3D-Modellen; eigenes Modell statt Demohaus); Ergebnisse 351, 353,
354; Protokoll 74 §288–§289; Einbau-Stand C205, C206; Entscheide 147, 148; Aufträge 355, 356. Abgeglichen gegen alle
Änderungen seit `v0.3.57` (`git log v0.3.57..` ohne Zusammenführungen).

Visbox zählt selbst (Entscheid 66): Bibliothek `aiimaging`, iPad-App und Mac-App tragen dieselbe Nummer
(`tests/test_versionsnummer.py`). Dieses Blatt ist der Text der Freigabe auf GitHub; die Mac-App zeigt daraus die
Zeilen des Abschnitts «Was neu ist».

## Warum 0.3.58

Der Owner will die Szene des Grundmodells mit Bäumen, Büschen, Wiese, Strasse und Autos auffrischen, und für die Demo
ein grosses Situationsmodell statt des Demohauses zeigen. Dieses Modell (rund 577 × 500 m) war aus Augenhöhe nur ein
Strich am Horizont, und die Blender-Kamera hatte keine eigene Sichtweite.

## Was neu ist (mit Entscheid und Stand)

| Fähigkeit | Entscheid | Stand |
|---|---|---|
| Knoten «Umfeld» zwischen Modell und Render: Bäume, Büsche, Wiese, Strasse und Autos aus freien CC0-Modellen (Poly Haven, Kenney), am Heim-PC geladen, nie im Haus und nie in der Sicht auf das Haus; auch über Claude | 147, 148 | gebaut, mit Probe; Messung 355 offen |
| Umfeld-Stücke zählen als Umgebung, nicht als Gebäude (Maske, Deckung, Umriss halten) | 148 | gebaut, mit Probe |
| Die Blender-Kamera sieht so weit, wie die Szene reicht (vorher konnte sie grosse Modelle abschneiden) | — | gebaut, mit Probe; Messung 356 offen |
| Grosse, flache Modelle bekommen Auto-Kameras als Vogelschau (40° von oben) statt Augenhöhe | — | gebaut, mit Probe; Messung 356 offen |
| Werkzeug für Draufsicht mit Raster und Vogelschau-Kameras | — | gebaut, mit Probe |

## Stand am Gerät

* **Mac:** Update-Knopf; danach die Claude-Sitzung neu starten (neue Werkzeuge). Prüfen: in der Knotenansicht den Knoten
  «Umfeld» zwischen Modell und Render setzen, Bäume und Autos anhaken, rendern.
* **Heim-PC:** `git pull`, Dienst und Abholer neu starten; dann Aufträge 356 (dringend), 355, 352.

## Bekannte Grenzen (schlechte Nachrichten bleiben drin)

* In Blender ist das Stellen der Umfeld-Stücke noch nicht gemessen (355).
* Ein Modell nur aus Platten (ohne Wände und Dächer) liest sich auch in der Vogelschau als gestapelte Platten.
* Füllen die Gebäude weniger als 20 % des Bildes, heisst die Prüfung des KI-Bilds «nicht beurteilbar».
* Grosse Modelle: Die Tiefenkarte hat in der Vogelschau nur wenige Graustufen je Gebäude.
* Die KI verändert das Grundbild bei Stärke 0,5 kaum — Owner-Frage zur Stärke liegt vor.

## Prüfung

Volle Suite ohne GPU, grün (Zahl in `README.md`). iPad/Mac: Prüfstrecke `.github/workflows/ipad.yml`; der Job
`freigabe` legt die Freigabe erst auf `main` an.
