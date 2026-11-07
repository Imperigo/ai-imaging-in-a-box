# Visbox 0.3.75 — Fassungsblatt (04.11.2026)

**Codestand:** Arbeitszweig `fab/visbox/int-0375`, noch nicht auf `main`; Vorgänger 0.3.74 = Tag `v0.3.74`

**Grundlage:** Masstreue-Entscheide 30.10. und 31.10.2026 («Immer vom Render»); gegengelesen grün: A0064 Runde 2, A0092, A0150, A0158, A0155, A0203. Der Schritt auf `main` wartet auf das Okay des Owners.

Visbox zählt selbst (Entscheid 66): Bibliothek `aiimaging`, iPad-App und Mac-App tragen dieselbe Nummer
(`tests/test_versionsnummer.py`). Dieses Blatt ist der Text der Freigabe auf GitHub; die Mac-App zeigt daraus die
Zeilen des Abschnitts «Was neu ist».

## Warum 0.3.75

Winter und Morgen waren als Stimmung kaum zu erkennen, und die Fenster-Prüfung meldete realistisch dunkles,
spiegelndes KI-Glas als «nicht gehalten». Beides stört die tägliche Arbeit, keines ändert die Bildkette im Grundsatz.

## Was neu ist (mit Entscheid und Stand)

- **Winter- und Morgen-Stimmung sichtbar:** Winter zeigt Schnee und winterliche Vegetation, Morgen tiefes Licht. Beide starten weiter vom eigenen Render. Geometrie am Testhaus: Morgen 0,975, Winter 0,976, Morgen im erhöhten Blick 0,986 (A0064).
- **Fenster-Prüfung ohne Fehlalarm:** Dunkles, spiegelndes Glas gilt als gehalten. Im Eichsatz fallen die Fehlalarme von 4 auf 0, der richtige Alarm bleibt (A0092).

- **Bild aus Skizze rechnet wieder vom frischen Grundbild:** Der Lauf bricht nicht mehr ab, es entsteht ein Bild; am Heim-PC gemessen mit Geometrie 0,82 und 0,81 bei der Skizzen-Stärke 0,55. Ein Auftrag mit frischer Grundlage ohne Höhenachse scheitert sofort, statt liegen zu bleiben (A0150).

- **Fenster-Prüfung je Fensterband:** Ein grau übermaltes Fensterband, etwa das Obergeschoss, schlägt jetzt an, auch wenn ein anderes Geschoss die Gesamtzahl hält. Der Eichsatz bleibt bei 12 von 12 (A0158).
- **Puls an der Pille «N offen»:** Liegt ein Vorschlag offen, pulsiert die Pille ruhig an der Claude-Marke. Bei reduzierter Bewegung steht dort nur ein stiller Ring (A0155).
- **Abholer meldet eine fehlende Ablage gedrosselt:** Die Zeile «fehlt» erscheint höchstens einmal je Stunde und sofort wieder, wenn sich ändert, welche Ablage fehlt; vorher füllte sie das Journal mit rund 5400 Zeilen am Tag (A0203).

## Stand am Gerät

Am Heim-PC gemessen, am Testhaus aus der Richtung Süd-Südost. Auf dem Mac nicht geprüft.

## Bekannte Grenzen (schlechte Nachrichten bleiben drin)

- Die langen Morgenschatten sind auf Augenhöhe kaum zu lesen, klar sichtbar sind sie im erhöhten Blick.
- Ein warm übermaltes Erdgeschoss fällt nicht über das Band auf, nur über die Gesamtzahl. Blick von stark oben und einzelne übermalte Fenster innerhalb eines Bands sind nicht geprüft.
- Der Abstand ist knapp: Morgenglas behält im Median 0,38 des Farbtons, graue Lattung 0,27, die Grenze liegt bei 0,3.
- Der Eichsatz stammt aus zwei Bauten und einer Kamerarichtung, die Band-Prüfung ist mit bestehenden Bildern nachgerechnet. Warme Spiegelung im Glas und Innenansichten mit Schnee sind nicht geprüft.
- Mit Z-Image entstehen aus Strichen der Skizze keine Bauteile: Ein gezeichneter Anbau erscheint nur als Linie auf der Fassade (E154). Dafür ist Qwen ausdrücklich zu wählen.
- A0063b (Mac) ist zurückgestellt.
- Die Drossel des Abholers ist im laufenden Dienst nicht gemessen, nur in Proben. Fehlen alle Ablagen, bleibt die Abbruchzeile «Ablageort fehlt» ungedrosselt: das ist ein Totalausfall und soll sichtbar sein. Ist die Brücken-Ablage nicht schreibbar, drosselt nichts.

## Prüfung

`python -m pytest -q` voll mit A0203: 13683 grün, 266 übersprungen, 2 rot (zusammen 13951). Die zwei sind dieselben wie auf diesem Zweig vor A0203 (dort 13669 grün, 266 übersprungen, 2 rot) und hängen an der Umgebung des Heim-PC: `test_betriebseinheiten` (visbox-flaeche.service weicht ab), `test_knoten_kurztasten::test_welche_taste_was_tut`. Der Lauf fuhr im Arbeitsbaum ohne `.venv-ifc`, Blender, Chromium und Swift-Kette, darum mehr übersprungen als die 212 der Runde davor; `test_swift_test_im_kern` und `test_visbox_icon`, zuvor auf diesem Gerät rot, sind dabei übersprungen, also nicht grün belegt. CI «Proben» läuft auf dem Arbeitszweig, «iPad» nur bei geänderten iPad-Dateien. Knoten-vitest 201 grün.
