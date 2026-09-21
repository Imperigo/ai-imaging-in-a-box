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

## Seit dem 21.09.2026 zeigt sie die Bilder selbst

Vorher nannte sie **Dateinamen und Urteile** — ein Werkzeug für Bilder, das keine Bilder
zeigt.

**Das Abzeichen sitzt auf dem Bild, nicht daneben.** Ein Bild wird angesehen, eine Liste
daneben wird gelesen — und beim Weiterreichen (ein Bildschirmfoto, ein Ausschnitt) bleibt
nur das Bild übrig.

    Ein Vorbehalt, der beim ersten Weiterreichen abfällt, ist kein Vorbehalt.

Die drei Zustände bekommen **drei verschiedene Rahmen**, und der ungemessene ist
zusätzlich gestrichelt: Farbe allein unterscheidet nicht für den, der sie nicht sieht.

**Und wo die Datei fehlt, steht die Lücke da.** Das ist ein Zustand, den es vor der
Bildanzeige gar nicht gab: Die Mappe nennt ein Bild, und die Datei ist weg. *Ein Name ohne
Datei sieht in einer Liste genauso aus wie einer mit.* Gelöscht wird hier trotzdem nichts —
das Projekt nennt den Namen weiter, und die Fläche sagt, dass er ins Leere zeigt.

### Was das an Verantwortung dazubringt

Von dem Augenblick an, in dem diese Fläche **Dateien ausliefert**, entscheidet sie
darüber, was von der Platte dieses Rechners in einen Browser geht.

Sie hört nur auf `127.0.0.1` — die Sperre in `bildpfad` steht trotzdem da:

    Eine zweite Sperre, die nur dann nötig wird, wenn die erste fällt, ist genau die
    Sperre, die man baut, solange nichts passiert ist.

Ausgeliefert wird nur, was **im Projektordner** liegt, und geprüft wird am **aufgelösten**
Pfad statt am Namen: Ein Verweis im Ordner heisst harmlos und kann anderswohin zeigen.
*Ein Name sagt, wie etwas heisst, nicht wo es liegt.*

**Eine dieser Prüfungen trägt nichts zur Sicherheit bei, und das steht dran.** Eine
Mutationsprobe hat gezeigt, dass die Namenssperre nichts fängt, was die Auflösung nicht
auch fängt. Sie bleibt für die **Meldung** stehen — wer `/etc/passwd` eingibt, soll nicht
über Verweise belehrt werden. *Ein Wächter, der nichts fängt, was der nächste nicht auch
fängt, ist kein zweiter Wächter.*

## Seit dem 21.09.2026 kann man hineinzeichnen

Die Zeichenfläche ist die Eingabe des **Entwurfsmodus** (E23) und die Lieferform dafür ist
ein **iPad mit Stift** (E24). Sie ist darum für einen Stift gebaut und nicht für eine
Maus, die auch geht.

**Zeigerereignisse und nichts daneben.** `PointerEvent` ist der einzige Weg, der `pressure`
und `pointerType` liefert und für Maus, Finger und Stift derselbe ist. Maus- und
Berührungsereignisse daneben wären derselbe Code dreimal, und der dritte veraltet zuerst.

**`touch-action: none` ist keine Kosmetik.** Ohne das schiebt ein Tablet beim Zeichnen die
Seite, statt einen Strich zu machen.

**Die Leinwand hat die Punktzahl des Bildes, nicht die des Bildschirms.** Eine Skizze in
Bildschirmpunkten passt später nicht auf das Bild, auf das sie gezeichnet wurde — und
genau darauf soll sie angewandt werden.

**Der Radierer nimmt weg, statt weiss zu malen.** Die Leinwand liegt durchsichtig über dem
Bild; weisse Farbe würde es verdecken statt die eigene Linie zu entfernen.

**Und die Fläche misst genau eine Sache selbst — das Gerät.** Unter der Zeichenfläche
steht, welche Eingabeart gemeldet wurde und ob Druck dabei war. *Eine Zeichenfläche, die
das nicht sagt, lässt den Benutzer raten, warum der Strich überall gleich dick ist.*

Eine **Druckkurve wird ausdrücklich nicht erfunden**: Was ein echter Stift auf einem
echten Gerät meldet, hat hier niemand gemessen, und eine ausgedachte Kennlinie sähe nach
Handwerk aus.

### Was beim Ablegen gilt

* **Das Format wird am Inhalt erkannt**, nicht am Namen — dieselbe Regel wie am Einlass
  für die Modelldateien.
* **Der Grössenriegel greift vor dem Schreiben.** *Ein Riegel, der erst beim Schreiben
  greift, hat schon geschrieben.*
* **Der Dateiname kommt aus dem Zeitpunkt, nie aus dem Wunsch.** Der Wunsch kommt aus
  einem Browser; ihn als Dateinamen zu nehmen hiesse, jemand anderem zu erlauben zu
  bestimmen, wo geschrieben wird. Er geht in die Bemerkung statt verloren.
* **Jede abgelegte Skizze trägt den Satz, dass sie nicht gerechnet wurde.** *Eine
  Bestellung, die angenommen und nicht ausgeliefert wird, ist schlimmer als eine
  abgelehnte: Die Ablehnung sieht man.*

### Sie darf ins Heimnetz — mit Kennwort (E25, 21.09.2026)

    python3 oberflaeche/server.py --ordner <projektordner> --im-heimnetz --kennwort-erzeugen

**Fail-closed, und das ist die eigentliche Eigenschaft.** Eine andere Adresse als
`127.0.0.1` ohne Kennwort ergibt **keinen Server**, sondern einen Satz.

    Eine Sperre, die man vergessen kann, ist im entscheidenden Augenblick vergessen.

Auf `127.0.0.1` bleibt es ohne Kennwort: Dort kommt ohnehin nur diese Maschine heran, und
wer eine Hürde ohne Gegenüber täglich nimmt, schaltet sie irgendwann ab.

Verglichen wird in gleichbleibender Zeit, **Name und Kennwort, beide immer** — ein `and`
käme bei falschem Namen früher zurück, und die Dauer wäre wieder eine Auskunft. Das
Kennwort kommt aus `secrets`: *Ein Zufall, der sich fortrechnen lässt, ist keiner.*

**Und was sie nicht leistet, steht hier, damit es niemand für geleistet hält:** Sie läuft
über gewöhnliches HTTP. Kennwort und Bilder gehen **unverschlüsselt** durch das Netz. Sie
hält Geräte fern, die zufällig im selben Netz sind — nicht jemanden, der dort mithört.

Kein TLS, weil ein selbst ausgestelltes Zertifikat auf dem iPad eine Warnung erzeugt, die
man wegklickt — *und eine Sicherheitswarnung, die man täglich wegklickt, erzieht zum
Wegklicken.*

## Der Grundriss — den Standpunkt anklicken statt eintippen

`auge` und `blick_auf` waren über diese Fläche erreichbar: als **drei getippte Zahlen**.

    Was nur über das Eintippen von Koordinaten erreichbar ist, wird nicht benutzt.

Der Grundriss kommt aus `aiimaging.glbbox.bauwerksbox` — **ohne Blender**, in
Sekundenbruchteilen, in Weltkoordinaten mit Z oben. Erster Klick Standpunkt, zweiter Klick
Blickziel; geschrieben wird über **denselben** Weg wie jede andere Einstellung.

**Gezeichnet wird das Bauwerk, nicht die Szene.** Die Szenenbox enthält das Gelände — ein
Grundriss, in dem das Haus ein Fleck in einer Wiese ist, lädt zu einem Standpunkt ein, der
daran vorbeisieht. Lässt sich die Bauwerksbox nicht bestimmen, gibt es **keinen**
Grundriss und einen Grund: *Die naheliegendste Ersatzantwort ist die, die niemand als
Ersatz erkennt.*

Das Blickziel liegt auf **halber Gebäudehöhe**. Wer auf den Boden zielt, bekommt ein Bild,
in dem das Haus nach hinten kippt.
