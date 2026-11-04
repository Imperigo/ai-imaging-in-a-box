# Visbox 0.3.75 — Fassungsblatt (04.11.2026)

**Codestand:** Arbeitszweig `fab/visbox/int-0375`, noch nicht auf `main`; Vorgänger 0.3.74 = Tag `v0.3.74`

**Grundlage:** Masstreue-Entscheide 30.10. und 31.10.2026 («Immer vom Render»); gegengelesen grün: A0064 Runde 2, A0092, A0150. Der Schritt auf `main` wartet auf das Okay des Owners.

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

## Stand am Gerät

Am Heim-PC gemessen, am Testhaus aus der Richtung Süd-Südost. Auf dem Mac nicht geprüft.

## Bekannte Grenzen (schlechte Nachrichten bleiben drin)

- Die langen Morgenschatten sind auf Augenhöhe kaum zu lesen, klar sichtbar sind sie im erhöhten Blick.
- Die Fenster-Prüfung sieht ein grau übermaltes Obergeschoss-Band nicht; der richtige Alarm im Eichsatz kommt nur vom Erdgeschoss.
- Der Abstand ist knapp: Morgenglas behält im Median 0,38 des Farbtons, graue Lattung 0,27, die Grenze liegt bei 0,3.
- Der Eichsatz stammt aus zwei Bauten und einer Kamerarichtung. Warme Spiegelung im Glas und Innenansichten mit Schnee sind nicht geprüft.
- Mit Z-Image entstehen aus Strichen der Skizze keine Bauteile: Ein gezeichneter Anbau erscheint nur als Linie auf der Fassade (E154). Dafür ist Qwen ausdrücklich zu wählen.
- A0063b (Mac) ist zurückgestellt.

## Prüfung

`python -m pytest -q` voll: 13711 grün, 212 übersprungen, 4 rot. Die vier sind dieselben wie auf `main` vor dieser Runde und hängen an der Umgebung des Heim-PC: `test_betriebseinheiten` (visbox-flaeche.service weicht ab), `test_ipad_geruest::test_swift_test_im_kern`, `test_knoten_kurztasten::test_welche_taste_was_tut`, `test_visbox_icon`. CI «iPad» und «Proben» laufen auf dem Arbeitszweig.
