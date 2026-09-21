# Die Oberfläche von Visbox

**Sie liegt ausserhalb von `src/aiimaging/`, und das ist keine Ordnungsfrage.**

Regel 4 sagt: *Der Kern ist eine Bibliothek, ohne Oberfläche aufrufbar. Die Oberfläche ist
eine dünne Schicht über der Bibliothek, nie deren Voraussetzung.*
`tests/test_regel4_bibliothek.py` setzt das durch — es verbietet jeden Oberflächen-Import
in `src/aiimaging/`. Diese Fläche steht darum daneben, nicht darin.

    Was nur über einen Klick erreichbar ist, existiert nicht.

## Die vier Auflagen, unter denen sie steht

**1 · Sie darf nichts können, was die Bibliothek nicht kann.**
Jeder Knopf ruft genau eine Funktion aus `aiimaging`. Fände sich hier eine Rechnung, eine
Schwelle oder ein Urteil, wäre sie keine dünne Schicht mehr — und dieselbe Fähigkeit stünde
an zwei Stellen, von denen eine ohne Oberfläche nicht erreichbar ist.
`tests/test_oberflaeche.py` prüft es.

**2 · Keine fremden Bausteine, aus dem Netz schon gar nicht.**
Kein Fenster-Werkzeugkasten (PyQt und PySide sind copyleft — Regel 1), kein Web-Rahmenwerk,
keine Schriftart und kein Skript von einem fremden Server. Es läuft mit dem, was in Python
selbst steckt, und einer Seite, die neben dieser Datei liegt.
*Eine Software, die zum Start das Netz braucht, ist kein Ein-Klick-Download.*

**3 · Sie hört nur auf dem eigenen Rechner.**
Hier liegen die Gebäudemodelle von jemandem. Eine Fläche, die von aussen erreichbar ist,
gibt sie weiter — auch wenn niemand das wollte.

**4 · Sie zeigt die dritte Antwort, und zwar sichtbar.**
Das ist die Auflage, um die es eigentlich geht. Aus dem Entwurf vom 26.08.2026:

> *«Ein Produkt zeigt Bilder, keine Messwerte.» Trägt die Oberfläche die Messung nicht,
> ist sie im Produkt unsichtbar; trägt sie sie als grünes Abzeichen, ist sie schlimmer als
> unsichtbar.*

**Ein ungeprüftes Bild darf nie aussehen wie ein bestandenes** — und auch nicht wie gar
nichts. Es bekommt ein eigenes Zeichen und einen eigenen Satz. Der UI-Worker hat am
03.09.2026 genau das an seiner eigenen Fläche gemeldet: Die Bildkachel zeigte bei fehlender
Prüfung **kein** Abzeichen, und kein Abzeichen sieht aus wie kein Problem.

## Warum die Bedienfelder nicht hier aufgezählt sind

Sie kommen aus `aiimaging.kette.baue_kette` — Namen, Vorgaben und die Zuordnung zum
Knoten. Eine Liste an dieser Stelle wäre in dem Augenblick veraltet, in dem die Bibliothek
etwas dazubekommt.

*Genau so ist am 21.09.2026 die Lücke entstanden, in der elf Bestellungen über einen der
beiden Wege nicht erreichbar waren.* Eine Oberfläche mit handgeschriebener Feldliste macht
denselben Fehler ein drittes Mal — und diesmal sähe ihn niemand, weil nichts kaputtgeht,
sondern nur fehlt.

**Wo ein Feld wirkt, wird ausprobiert**, nicht nachgeschlagen: Die Fläche baut die Kette
einmal je Feld mit einem Probewert und sieht, welcher Knoten danach anders aussieht.
Verglichen werden **Werte**, nicht Namen — sonst bliebe jedes Feld unsichtbar, das im
Knoten anders heisst (`qa_schwelle` steht dort als `schwelle`).

Und wo die Probe nichts sieht, steht das da. **«Kein Knoten» heisst dreierlei**, und die
drei sahen zuerst gleich aus:

| | |
|---|---|
| **formt den Bau** | Das Feld bestimmt, *welche* Knoten es gibt — `qa` schaltet die Prüfung ab |
| **unbekannt** (mit `?`) | Die Probe hat nichts gesehen. *Weder ja noch nein* |
| sonst | Genau ein Knoten sieht damit anders aus |

## Geprüft wird nicht hier

Was eingegeben wird, legt die Fläche der Bibliothek vor. Baut `baue_kette` damit eine
Kette, ist es brauchbar; wirft sie, kommt **ihr** Satz zurück und **es wird nichts
gespeichert**.

*Eine Oberfläche, die eigene Regeln über zulässige Werte kennt, hat dieselbe Regel
zweimal — und die zweite veraltet, ohne dass jemand es merkt.*

## Starten

    python3 oberflaeche/server.py --ordner <projektordner>

Dann im Browser `http://127.0.0.1:8731`. Ohne `--ordner` startet sie leer und fragt danach.

## Was sie heute kann, und was nicht

| | |
|---|---|
| **kann** | Ein Projekt anzeigen: Modell, Zustand des Modells, den Knotenbaum der Rechnung, jedes Bild mit seinem Urteil und dessen Vorbehalt |
| **kann** | Ein Projekt anlegen (Modell hereinholen) |
| **kann** | Einen Lauf starten — und den Fehlschlag als Satz zeigen, wenn Werkzeuge fehlen |
| **kann** | Den Knotenbaum **bedienen**: Knoten anklicken, Einstellungen ändern, übernehmen. Die Felder kommen aus der Bibliothek, nicht aus einer Liste hier |
| **kann nicht** | Knoten hinzufügen, entfernen oder umhängen. Die Form der Kette steht fest |
| **kann nicht** | Bilder nebeneinanderlegen, Varianten vergleichen |

*Die zweite Spalte ist kein Mangelbericht, sondern der Stand.* Was hier fehlt, fehlt
sichtbar statt halb gebaut dazustehen.
