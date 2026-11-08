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

- **Kein «Freies Bild» mehr, auch nicht über Claude:** Am Varianten-Knoten gibt es den Haken nicht mehr, und die Werkzeugliste für Claude bietet ihn nicht mehr an; ein Aufruf, der ein Bild ohne Grundlage verlangt, wird abgewiesen, bevor etwas entsteht. Alte freie Bilder bleiben lesbar und tragen ihre Marke (A0256, Owner-Entscheid Masstreue 30.10.).
- **Mac-Fensterkopf aus Glas, Visbox folgt hell und dunkel des Systems:** Der Kopf mischt mit dem Hintergrund hinter dem Fenster, bei «Transparenz reduzieren» deckend; das Erscheinungsbild ist nicht mehr fest dunkel. Ein grüner Punkt an der Fassungsnummer zeigt eine neuere Fassung, Klick öffnet «Aktualisieren» (A0156, O-20261107-01).
- **Modell laden am Mac zieht die Mappe nach:** Passt eine liegende `modell.glb` nicht zur `mappe.json`, werden Bauteilzahl und Hülle aus der Datei nachgezogen oder deutlich gemeldet; «Szene: Bauteile unbekannt» statt «0»; jeder Abbruch holt das alte Modell zurück, zweimaliges Laden ist gesperrt; eine Bestellung aus einer nachgezogenen Mappe rechnet mit dem Modell vom Mac (A0063b, A0261).
- **Start am Mac ohne stilles Hängen:** Das Fenster steht vor jeder Schlüsselbund-Frage, mit Hinweis; ein Testbau trägt eine eigene Kennung, startet neben der installierten Visbox, liest nur und schreibt nie in geteilte Schlüsselbund-Einträge, und er bietet sich dem iPad nie an; nach «iPad vergessen» arbeitet jeder neue Dienst mit dem frischen Zugang (A0255, A0265).
- **Startseite am Mac bei schmalem Fenster ganz:** Ab 1100 px stehen beide Seiten ganz im Fenster, «Schon anfangen» ist immer erreichbar; die Liste «Noch am Heim-PC» springt beim Laden nicht mehr (A0264).

## Stand am Gerät

Am Heim-PC gemessen, am Testhaus aus der Richtung Süd-Südost. Auf dem Mac nicht geprüft.

## Bekannte Grenzen (schlechte Nachrichten bleiben drin)

- Die langen Morgenschatten sind auf Augenhöhe kaum zu lesen, klar sichtbar sind sie im erhöhten Blick.
- Ein warm übermaltes Erdgeschoss fällt nicht über das Band auf, nur über die Gesamtzahl. Blick von stark oben und einzelne übermalte Fenster innerhalb eines Bands sind nicht geprüft.
- Der Abstand ist knapp: Morgenglas behält im Median 0,38 des Farbtons, graue Lattung 0,27, die Grenze liegt bei 0,3.
- Der Eichsatz stammt aus zwei Bauten und einer Kamerarichtung, die Band-Prüfung ist mit bestehenden Bildern nachgerechnet. Warme Spiegelung im Glas und Innenansichten mit Schnee sind nicht geprüft.
- Mit Z-Image entstehen aus Strichen der Skizze keine Bauteile: Ein gezeichneter Anbau erscheint nur als Linie auf der Fassade (E154). Dafür ist Qwen ausdrücklich zu wählen.
- Die Mac-Aufträge (A0063b, A0156, A0255, A0261, A0264, A0265) sind im Code gegengelesen und in der CI übersetzt, am Mac aber nicht am Gerät geprüft (Owner-Entscheid O-20261108-06: Geräteprobe mit dem Release). «iPad vergessen» ist auf Wunsch des Owners am Gerät ausgelassen. Ob die rechte Startseite bei 1100 px mit 659 px auskommt und ob das Glas hinter dem Fenster mischt, zeigt erst der Mac.
- Die Hüllbox einer am Mac nachgezogenen Mappe ist die Box der ganzen Szene mit Gelände (Geräteprobe: 60 × 50 m statt der Hausbox). Der Vermerk «Gelände nicht abgetrennt» steht in der Mappe; Standpunkte rechnet weiter nur der Heim-PC. Die Trennung folgt mit A0267 in 0.3.76.
- Die Drossel des Abholers ist im laufenden Dienst nicht gemessen, nur in Proben. Fehlen alle Ablagen, bleibt die Abbruchzeile «Ablageort fehlt» ungedrosselt: das ist ein Totalausfall und soll sichtbar sein. Ist die Brücken-Ablage nicht schreibbar, drosselt nichts.

## Prüfung

`python -m pytest -q` voll mit A0203: 13683 grün, 266 übersprungen, 2 rot (zusammen 13951). Die zwei sind dieselben wie auf diesem Zweig vor A0203 (dort 13669 grün, 266 übersprungen, 2 rot) und hängen an der Umgebung des Heim-PC: `test_betriebseinheiten` (visbox-flaeche.service weicht ab), `test_knoten_kurztasten::test_welche_taste_was_tut`. Der Lauf fuhr im Arbeitsbaum ohne `.venv-ifc`, Blender, Chromium und Swift-Kette, darum mehr übersprungen als die 212 der Runde davor; `test_swift_test_im_kern` und `test_visbox_icon`, zuvor auf diesem Gerät rot, sind dabei übersprungen, also nicht grün belegt. CI «Proben» läuft auf dem Arbeitszweig, «iPad» nur bei geänderten iPad-Dateien. Knoten-vitest 201 grün.


Nachtrag 08.11.2026 (Einspielen der Mac-Aufträge und A0256 aus der Cloud, O-20261108-04): `python -m pytest -q tests` 13697 grün, 263 übersprungen, 0 rot nach dem Nachführen der README-Zahl (13961 gesammelt); kosmovis Typecheck 7 Pakete ohne Fehler, Vitest alle Pakete grün (orbit-app 763, Knoten 203). Swift ist in der Cloud nicht vorhanden; Übersetzung und `swift test` belegt die iPad-CI auf dem Kopf.

Nachtrag 08.11.2026, nachmittags (Geräteprobe Teil 1, A0266): Am Mac schob der lange Nachzug-Satz den Knopf «Andere Datei …» aus dem fest hohen Modell-Knoten. Der Knopf steht jetzt vor dem Satz, Sätze sind auf vier Zeilen begrenzt (voller Text im Hinweis), die Mappenzeile ist einzeilig. Nachgestellt in Chromium mit dem eingecheckten Bau: vorher abgeschnitten und nicht anklickbar, nachher im Knoten und anklickbar. pytest 13698 grün, 263 übersprungen; Vitest orbit-app 769, Knoten 203; Mac-Übersetzung in der iPad-CI.

Nachtrag 08.11.2026, Geräteprobe Teil 2 (hell, Heim-PC): A0156, A0261, A0255 mit A0265 und A0264 tragen am Gerät. Behoben vor dem Tag (A0269): das Kopplungsblatt kürzte «Neu suchen» und «Abbrechen», nach «Neu ist:» stand bei einer Freigabe ohne Angaben nichts. Ungeprüft mit: dunkler Modus, «Transparenz reduzieren», Schalter und Koppeln im Testbau. Mit 0.3.76 (A0270): Varianten-Knoten nennt bei einer nachgezogenen Mappe den Weg über «Andere Datei …», deaktivierte Felder der Rechnerwahl lesbarer. pytest 13701 grün, 263 übersprungen.
