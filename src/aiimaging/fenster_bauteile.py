"""Die Fensterprüfung je Bauteil (A0291, «Masstreue je Bauteil») — reine Bibliothek, kein Paket.

**Anlass.** ``varianten.fenster_gehalten`` urteilt über das ganze Bild und seit v5 je Fensterband
(ein Geschoss). Übermalt die KI EIN Fenster in einem Band von fünf, bleibt der Median des Bands
Glas und der Gesamtanteil bei vier Fünfteln: Beide Zahlen halten, und niemand sagt, welches
Fenster fehlt. Gemessen am synthetischen Eichsatz (``tests/fenster_paare.py``, 105 Paare): Die
Band-Prüfung merkt 3 von 45 einzeln übermalten Fenstern, ohne Ort.

**Was hier geprüft wird.** Jedes zusammenhängende Glasstück des Material-ID-Passes ist ein
Bauteil. Ein Fensterband ist im ID-Pass aber EIN Glasstück ohne Sprossen (so im Testhaus der
Eichdaten von A0158); breite Glasstücke werden darum in quadratische **Felder** geteilt, die sich
überlappen, und jedes Feld wird wie ein Bauteil geprüft. Nebeneinanderliegende übermalte Felder
werden zu EINEM Fund zusammengezogen.

Je Bauteil oder Feld wird das Glas mit der **Wand gleich daneben** verglichen (ein Ring aus
Fassade, wie in v5) — und zwar nachdem das KI-Bild an genau dieser Wand ins Licht des Grundbilds
gebracht ist. Darum stört weder eine Stimmung noch ein Schatten, der über Fenster und Wand
zugleich fällt. Drei Regeln, jede für eine Art der Übermalung:

1. **Wie die Wand daneben** — der Abstand Glas zu Wand ist im KI-Bild unter einem Viertel des
   Abstands im Grundbild (dieselbe Schwelle wie je Band, ``FENSTER_BAND_KONTRAST_ANTEIL``), und
   mindestens drei Viertel der Bildpunkte liegen näher an der Wand als der halbe Abstand im
   Grundbild. Der zweite Teil hält den Ort genau: Ein Feld, das nur zur Hälfte übermalt ist,
   zählt nicht mit.
2. **Warm** — mindestens drei Viertel der Bildpunkte sind klar rötlicher als die Wand daneben
   und nicht dunkel, obwohl das Glas im Grundbild bläulicher war als die Wand.
3. **Ohne den Glaston der Nachbarfenster** — mindestens drei Viertel der Bildpunkte sind klar
   weniger bläulich als die Geschwister (andere Bauteile mit gleichem Glas im Grundbild) und
   nicht dunkel. Das fängt ein grau übermaltes Fenster in einer farbigen Wand: Es hebt sich von
   der Wand ab und ist doch kein Glas mehr. Gemessen wird am Verhältnis Blau zu Rot, weil eine
   Stimmung dieses bei allen Scheiben gleich verschiebt, und an der Streuung der Geschwister,
   weil Scheiben eines Bilds verschieden spiegeln.

Im Band zählt ein Fund erst, wenn er auch auf doppelter Feldbreite trägt: Ein Vorhang deckt ein
Feld, ein Fenster ist breiter.

**Teil (a), die vorsichtige Ausgabe** (zweites Gegenlesen, Mängel M5 bis M8; :func:`_vorsichtig`).
Wo ein Vorwurf nicht sicher ist, heisst das Bauteil «nicht messbar» mit Grund, nie «uebermalt»,
und ein verändertes Fenster bleibt nicht still «gehalten»: Scheiben eines Sprossenfensters werfen
nichts vor (:func:`sprossen_scheiben`); haben die meisten Scheiben keinen Glaston mehr (Spiegelung),
fehlt der Massstab für «warm» und «ohne Glaston»; ist ein Feld oben anders als unten, ist es kein
gleichmässiger Anstrich; ist es in der Farbe der Wand, aber viel unruhiger, steht etwas davor; ist
nur eine Hälfte übermalt oder sind die Nachbarscheiben selbst fast farblos, heisst es «nicht
messbar». Ein «uebermalt» wird dort nur zurückgenommen, nie gesetzt.

**Nachbau (a)** (drittes Gegenlesen, Fälle G1 und G2). Spiegelt nur EINE Scheibe, ist ihr Fund «warm» oder «ohne
Glaston» «nicht messbar», wenn sie gleichmässig farblos bis warm ist und ihr Rahmen erhalten ist (eine Spiegelung
bleibt im Glas, ein Anstrich nimmt den Rahmen mit; :func:`_spiegelt_einzeln`). Eine Scheibe von höchstens 2 x 4
Bildpunkten Breite, an der die Wand ohne Rahmen anliegt, trägt keinen Vorwurf «wie die Wand» (:func:`schmale_stuecke`).

**Was es nicht ist.** Ein Hinweis, kein Urteil: ``fenster_gehalten`` hängt den Befund an, ändert
aber ``gehalten`` nicht. Die Schwellen sind am synthetischen Eichsatz gesetzt und an den echten
Ausschnitten von A0158 gegengeprüft; am echten KI-Bild sind sie noch nicht geeicht.

**Bekannte Grenzen.** Ein heller, undurchsichtiger Vorhang, der mehr als ein Feld deckt, sieht aus
wie eine Übermalung. Sind die Geschwister selbst fast neutral, fällt ein graues Fenster nicht auf.
Sind alle Fenster einer farbigen Wand grau übermalt, gibt es keine Geschwister zum Vergleich. Ein
übermaltes Fenster im Band, das schmaler ist als 1,2 Feldbreiten, wird nicht gemeldet. Der Ort
eines Funds im Band stimmt auf etwa ein halbes Feld. Spiegelt im Band nur ein Feld ein Haus, bleibt der Vorwurf: Ohne
eigenen Rahmen trennt nichts die Spiegelung vom Anstrich.
"""
from __future__ import annotations

import math

from . import varianten as _v

#: Ein Glasstück, das mindestens so viel breiter als hoch ist, wird in Felder geteilt. Gesetzt:
#: zwei — ein gewöhnliches Fenster bleibt ein Bauteil, ein Band wird geteilt.
FELD_AB_SEITENVERHAELTNIS = 2.0
#: Ein Feld ist so breit, wie das Glasstück hoch ist, mindestens aber so viele Bildpunkte.
FELD_MIN_BREITE = 6
#: Felder überlappen: Der Schritt ist ein Viertel der Feldbreite. So liegt ein übermaltes Fenster,
#: das mindestens so breit ist wie ein Feld, in einem Feld zu mindestens drei Vierteln.
FELD_SCHRITT_ANTEIL = 0.25
#: Der Ring aus Wand um ein Bauteil reicht mindestens so weit wie in v5 (``FENSTER_RING``) und
#: sonst diesen Anteil der Höhe des Bauteils weit. Gesetzt: gut ein Drittel — bei einem Fünftel
#: lag der Ring im vierfachen Massstab noch zur Hälfte im Rahmen (13 Fehlalarme).
RING_ANTEIL_HOEHE = 0.35
#: Weicht die Farbart der Wand neben einem Feld (Grundbild zu KI-Bild) um mehr als diesen Betrag
#: von der mittleren Verschiebung aller Felder ab, gilt die Wand dort als verdeckt oder umgefärbt.
#: Gesetzt: 0,25 — ein Baum vor weisser Wand liegt bei 0,6, die echte Vorschau unter 0,1.
WAND_VERAENDERT = 0.25
#: Der Sockel der Farbart (auf jeden Kanal gezählt), damit fast Schwarzes keine Farbe vortäuscht.
FARBART_SOCKEL = 32.0
#: Hebt sich das Glas im Grundbild von der Wand um weniger als dieses Vielfache der
#: Mindesttrennung ab, darf der nächste Stoff (der Ring von v5) als Massstab dienen, wenn er
#: klarer trennt. Gesetzt: anderthalb.
WAND_SCHWACH = 1.5
#: Ein Feld mit weniger als diesem Anteil der Bildpunkte eines vollen Felds wird weggelassen.
FELD_MIN_ANTEIL = 0.6
#: Regel 1: Unter diesem Anteil des Abstands im Grundbild ist das Glas «wie die Wand daneben».
#: Zwischen diesem Wert und der Schwelle von v5 (ein Viertel) hebt es sich kaum ab, ist aber nicht
#: eindeutig übermalt: «nicht messbar». Gesetzt: ein Achtel. Dunkles spiegelndes Glas in dunkler
#: Holzschalung liegt bei 0,20 bis 0,22 (Mangel M1 des Gegenlesens), die echte Übermalung bei 0,05.
KONTRAST_KLAR = 0.125
#: So viele Bildpunkte Rand eines Bauteils bleiben höchstens aussen vor (Versatz des KI-Bilds),
#: und höchstens dieser Bruchteil seiner kürzeren Seite.
KERN_RAND_MAX = 4
KERN_RAND_TEIL = 5
#: Anteile werden an Mitteln über so viele aufeinanderfolgende Bildpunkte gezählt, nicht an
#: einzelnen: Rauschen im KI-Bild liesse sonst jeden Anteil unter die Schwelle fallen.
BLOCK = 8
#: Weniger Glaspunkte, und das Bauteil ist «nicht messbar».
BAUTEIL_MIN_PUNKTE = 24
#: So viele Bildpunkte eines Bauteils müssen für Regel 2 und 3 betroffen sein. Gesetzt: drei
#: Viertel — ein Vorhang über die halbe Scheibe reicht nicht.
BAUTEIL_ANTEIL = 0.75
#: Im Band zählt ein Fund erst, wenn auf doppelter Feldbreite so viele Bildpunkte betroffen sind.
#: Gesetzt: sechs Zehntel — ein Fenster von 1,2 Feldbreiten reicht, ein Vorhang von einer nicht.
BESTAETIGUNG_ANTEIL = 0.6
#: Regel 2 zählt nur, wenn mindestens dieser Anteil der Bildpunkte nicht dunkel ist.
HELL_MIN_ANTEIL = 0.4
#: Unter diesem Anteil der Helligkeit der Wand gilt ein Bildpunkt als dunkel (Spiegelung, Öffnung)
#: und zählt für Regel 2 nicht als warm.
BAUTEIL_DUNKEL = 0.6
#: Regel 3: So bläulich (Blau zu Rot als Logarithmus) muss das Glas im Grundbild mindestens sein,
#: damit ein verlorener Glaston auffallen kann. Gesetzt: 0,06 — das Glas der Eichdaten hat 0,18.
REIHE_TON_MIN = 0.06
#: Regel 3: Liegt der Glaston eines Felds um mindestens diesen Anteil des Glastons im Grundbild
#: unter dem unteren Fünftel der Geschwister, ist es «uebermalt». Gesetzt: 0,8 — ein graues Feld
#: hat keinen Glaston mehr, sein Rückstand ist der ganze Glaston der mattesten Scheibe. Mit 0,7
#: (an der Mitte gemessen) gab es in 5 von 13 Saaten Fehlalarme bei gemischten Scheiben.
REIHE_TON_KLAR = 0.8
#: Regel 3: Ab diesem Anteil ist der Rückstand auffällig, aber nicht eindeutig: «nicht messbar».
#: Scheiben eines Bilds spiegeln verschieden; eine matte Scheibe neben blauen ist kein Fund.
REIHE_TON_ANTEIL = 0.4
#: Regel 3: Ein auffällig mattes Feld gilt doch als übermalt, wenn es zudem höchstens um diesen
#: Anteil des Vorsprungs im Grundbild bläulicher ist als die Wand daneben. Gesetzt: 0,15.
WANDTON_ANTEIL = 0.15
#: Regel 3: Weicht ein Feld auf der Grün-Achse um mehr als diesen Betrag von seinen Geschwistern
#: ab, ist es nicht grau übermalt, sondern von etwas Farbigem verdeckt. Gesetzt: 0,2.
FARBE_FREMD = 0.2
#: Regel 3: Geschwister, deren Glaston höchstens diesen Anteil des Glastons im Grundbild über dem
#: des Felds liegt, zählen nicht als Massstab: Sie sind womöglich selbst übermalt (zwei graue
#: Fenster nebeneinander deckten sich sonst gegenseitig, Mangel M2 des Gegenlesens).
REIHE_GLEICH = 0.25
#: Regel 3 braucht mindestens so viele Geschwister.
REIHE_GESCHWISTER_MIN = 2
#: Höchstens so viele Bildpunkte je Bauteil gehen in die Rechnung (gleichmässig ausgedünnt).
BAUTEIL_STICHPROBE = 3000
#: Teil (a), vorsichtige Ausgabe: Zwei Glasstücke, die nur ein schmaler Steg trennt (höchstens
#: dieser Anteil ihrer kürzesten Seite), sind Scheiben EINES Fensters mit Sprossen. Gesetzt: die
#: Hälfte — die Sprosse ist ein Bruchteil der Scheibe, der Abstand zweier Fenster ist es nie (in
#: allen Eichsätzen mindestens das Anderthalbfache des Abstands, den diese Schwelle zulässt).
SPROSSE_ANTEIL = 0.5
#: Teil (a): Ein Feld, das «wie die Wand» aussieht, aber so viel unruhiger ist als die Wand
#: daneben (Streuung der Helligkeit), ist nicht übermalt, sondern von etwas davor verdeckt (ein
#: Baum, den nur die KI gemalt hat). Gesetzt: das Doppelte — eine Übermalung mit der Wand trägt
#: deren Körnung, eine Krone ist gröber.
TEXTUR_FREMD = 2.0
#: Teil (a): Behält von den Glasbauteilen, an denen sich der Glaston messen lässt, weniger als
#: dieser Anteil im KI-Bild seinen Glaston, gibt es keinen Massstab: Ein Fenster «warm» oder «ohne
#: den Glaston der Nachbarfenster» könnte ebenso eine Spiegelung sein wie alle anderen auch.
GESCHWISTER_GLASTON_MIN = 0.5
#: Nachbau (a), Regel 2: Ein Glasstück, das höchstens zweimal so breit ist wie der waagrechte
#: Versatz, den die Eichsätze dem KI-Bild zumuten (vier Bildpunkte, so breit wie der breiteste Rand,
#: den :func:`_rand` auslässt) und an dem die Wand ohne Rahmen anliegt, trägt keinen Vorwurf «wie die
#: Wand daneben»: Bei diesem Versatz liegt die halbe Scheibe auf der Wand oder dem Steg daneben (Fall
#: G2 des dritten Gegenlesens; :func:`schmale_stuecke`).
SCHMAL_VERSATZ = 4
#: Nachbau (a), Regel 1: Ein Rahmen gilt als erhalten (nicht mit übermalt), wenn mindestens ein
#: Viertel seiner Bildpunkte im KI-Bild aussieht wie der Rahmen im Grundbild. Ein Viertel, weil ein
#: Versatz von bis zu :data:`SCHMAL_VERSATZ` Bildpunkten höchstens zwei Seiten des Rahmens ganz und
#: die beiden anderen zum Teil auf Glas oder Wand schiebt; ein Anstrich samt Rahmen lässt von ihm
#: nichts übrig.
RAHMEN_ERHALTEN_ANTEIL = 0.25

GRUND_SPROSSEN = ("Scheibe eines Sprossenfensters — die Sprosse ist zu schmal, um die Wand daneben "
                  "oder einen Versatz des KI-Bilds sicher abzugrenzen: nicht beurteilt, nie ein Vorwurf.")
GRUND_SPIEGELUNG = ("Die Geschwister haben selbst keinen Glaston mehr (die meisten Scheiben spiegeln "
                    "etwas Farbloses oder Warmes, etwa ein Haus gegenueber) — Spiegelung oder alles "
                    "uebermalt, ohne Massstab nicht entscheidbar.")
GRUND_SPIEGELUNG_TEIL = ("Oben ein anderer Glaston als unten (Himmel ueber etwas Farblosem, wie eine "
                         "Spiegelung) — kein gleichmaessiger Anstrich, nicht entscheidbar.")
GRUND_SPIEGELUNG_EINZELN = ("Ohne Glaston, aber gleichmaessig farblos bis warm und der Rahmen unveraendert, "
                            "waehrend die Nachbarfenster ihren Glaston haben — eine Spiegelung (etwa ein Haus "
                            "gegenueber) bleibt im Glas, ein Anstrich nimmt meist den Rahmen mit: nicht "
                            "entscheidbar.")
GRUND_SCHMAL = ("Zu schmal, um «wie die Wand daneben» sicher zu sagen: Bei einem Versatz des KI-Bilds um "
                "{versatz} Bildpunkte laege die halbe Scheibe auf der Wand daneben.")
GRUND_BLIND = ("Weniger Glaston als die Nachbarfenster, die aber selbst fast farblos sind (heller "
               "Himmel im Glas) — grau uebermalt oder nur anders gespiegelt, nicht entscheidbar.")
GRUND_TEXTUR = ("In der Farbe der Wand, aber viel unruhiger als sie — etwas steht davor (ein Baum "
                "oder Gegenstand), nicht uebermalt.")
GRUND_TEIL = ("Nur der {teil} Teil sieht nicht mehr aus wie Glas ({art}) — halb uebermalt, Rollladen "
              "oder Vorhang, nicht entscheidbar.")

GEHALTEN, UEBERMALT, NICHT_MESSBAR = "gehalten", "uebermalt", "nicht messbar"
ART_WAND, ART_WARM, ART_REIHE = "wie die Wand daneben", "warm uebermalt", "ohne den Glaston der Nachbarfenster"
SATZ_BAUTEIL_UEBERMALT = "FENSTER EINZELN UEBERMALT"
METHODE_BAUTEILE = (
    "Je zusammenhaengendem Glasstueck des Material-ID-Passes (breite Stuecke in ueberlappende "
    "quadratische Felder geteilt): Glas gegen die Wand gleich daneben, nachdem das KI-Bild an "
    "dieser Wand ins Licht des Grundbilds gebracht ist. Uebermalt, wenn der Abstand zur Wand unter "
    "einem Viertel des Abstands im Grundbild liegt, wenn drei Viertel der Bildpunkte klar "
    "roetlicher als die Wand und nicht dunkel sind, oder wenn drei Viertel klar weniger blaeulich "
    "sind als die anderen Fenster des Bilds (Blau zu Rot, gemessen an deren Streuung). Im Band "
    "muss ein Fund auf doppelter Feldbreite tragen. Vorsichtig: Sprossen-Scheiben, Spiegelung ohne "
    "Glaston, eine Scheibe ohne Glaston mit erhaltenem Rahmen, eine schmale Scheibe an der Wand, oben "
    "anders als unten, unruhiger als die Wand, nur halb veraendert und Geschwister ohne Glaston heissen "
    "nicht messbar statt uebermalt. Hinweis, kein Urteil (A0291)")


def _ton(p) -> float:
    """Der Glaston eines Bildpunkts: Blau zu Rot als Logarithmus (0 ist neutral, darüber bläulich)."""
    return math.log((float(p[2]) + 1.0) / (float(p[0]) + 1.0))


def _gruen(p) -> float:
    """Wie grünlich ein Bildpunkt ist: Grün gegen das Mittel aus Rot und Blau, als Logarithmus.

    Die zweite Achse der Farbart neben dem Glaston. Glas, Grau und Putz liegen nahe null; Laub
    liegt bei 0,6. Eine Stimmung verschiebt auch sie bei allen Scheiben gleich.
    """
    return math.log((float(p[1]) + 1.0) ** 2 / ((float(p[0]) + 1.0) * (float(p[2]) + 1.0))) / 2.0


def _helligkeit(p) -> float:
    return (float(p[0]) + float(p[1]) + float(p[2])) / 3.0


def _bits_zu_x(bits: int) -> list:
    aus = []
    while bits:
        tief = bits & -bits
        aus.append(tief.bit_length() - 1)
        bits ^= tief
    return aus


def glasstuecke(glas_zeilen: dict) -> list:
    """Die zusammenhängenden Glasstücke (vier Nachbarn) als ``{zeile: bits}`` je Stück."""
    eltern: list = []

    def wurzel(a: int) -> int:
        while eltern[a] != a:
            eltern[a] = eltern[eltern[a]]
            a = eltern[a]
        return a

    laeufe = []                                   # (zeile, bits des Laufs)
    davor: list = []                              # Läufe der Zeile darüber: (nummer, bits)
    letzte = None
    for y in sorted(glas_zeilen):
        if letzte is None or y != letzte + 1:
            davor = []
        jetzt = []
        bits = glas_zeilen[y]
        while bits:
            tief = bits & -bits
            lauf = bits & ~(bits + tief)          # die zusammenhängenden Einsen ab dem tiefsten Bit
            bits ^= lauf
            nummer = len(laeufe)
            laeufe.append((y, lauf))
            eltern.append(nummer)
            for andere, andere_bits in davor:
                if andere_bits & lauf:
                    eltern[wurzel(andere)] = wurzel(nummer)
            jetzt.append((nummer, lauf))
        davor, letzte = jetzt, y
    stuecke: dict = {}
    for nummer, (y, lauf) in enumerate(laeufe):
        zeilen = stuecke.setdefault(wurzel(nummer), {})
        zeilen[y] = zeilen.get(y, 0) | lauf
    return sorted(stuecke.values(), key=lambda z: (min(z), min((b & -b).bit_length() for b in z.values())))


def _kern(zeilen: dict, rand: int = 1) -> dict:
    """Das Stück ohne seinen Rand: Dort verfehlt ein versetztes KI-Bild das Glas nicht."""
    aus = zeilen
    for _ in range(rand):
        innen = {}
        for y, b in aus.items():
            rest = b & (b << 1) & (b >> 1) & aus.get(y - 1, 0) & aus.get(y + 1, 0)
            if rest:
                innen[y] = rest
        aus = innen
    return aus


def _rand(zeilen: dict) -> int:
    """Wie breit der Rand ist, der aussen vor bleibt: bis vier Bildpunkte, ein Fünftel der kürzeren Seite."""
    ort = _ort(zeilen)
    weite = ort["x1"] - ort["x0"] + 1
    hoehe = sum(bin(b).count("1") for b in zeilen.values()) / weite
    return max(1, min(KERN_RAND_MAX, int(min(weite, hoehe)) // KERN_RAND_TEIL))


def _bloecke(punkte: list) -> list:
    """Mittel über je :data:`BLOCK` aufeinanderfolgende Bildpunkte (der Rest bildet den letzten Block)."""
    aus = []
    for i in range(0, len(punkte), BLOCK):
        teil = punkte[i:i + BLOCK]
        if len(teil) * 2 >= BLOCK or not aus:
            aus.append(tuple(sum(p[k] for p in teil) / len(teil) for k in range(3)))
    return aus


def _ausschnitt(zeilen: dict, x0: int, x1: int) -> dict:
    maske = ((1 << (x1 - x0 + 1)) - 1) << x0
    return {y: b & maske for y, b in zeilen.items() if b & maske}


def _punkte(zeilen: dict, breite: int) -> list:
    return [y * breite + x for y, b in sorted(zeilen.items()) for x in _bits_zu_x(b)]


def _ort(zeilen: dict) -> dict:
    alle = 0
    for b in zeilen.values():
        alle |= b
    return {"x0": (alle & -alle).bit_length() - 1, "y0": min(zeilen),
            "x1": alle.bit_length() - 1, "y1": max(zeilen)}


def _felder(zeilen: dict) -> list:
    """Ein breites Glasstück in überlappende Felder teilen; sonst das Stück selbst.

    Returns: ``[(x0, x1, zeilen des Felds)]`` — bei einem ungeteilten Stück genau ein Eintrag.
    """
    ort = _ort(zeilen)
    weite = ort["x1"] - ort["x0"] + 1
    n = sum(bin(b).count("1") for b in zeilen.values())
    hoehe = n / weite                              # die mittlere Höhe einer Spalte
    feld = max(FELD_MIN_BREITE, round(hoehe))
    if weite < FELD_AB_SEITENVERHAELTNIS * hoehe or weite < 2 * feld:
        return [(ort["x0"], ort["x1"], zeilen)]
    schritt = max(1, round(feld * FELD_SCHRITT_ANTEIL))
    anfaenge = list(range(ort["x0"], ort["x1"] - feld + 2, schritt))
    if anfaenge[-1] != ort["x1"] - feld + 1:
        anfaenge.append(ort["x1"] - feld + 1)
    teile = [(a, a + feld - 1, _ausschnitt(zeilen, a, a + feld - 1)) for a in anfaenge]
    # Ein schräg angeschnittenes Feld am Ende des Bands besteht fast nur aus Rand: weglassen.
    voll = sorted(sum(bin(b).count("1") for b in t[2].values()) for t in teile)[len(teile) // 2]
    return [t for t in teile if sum(bin(b).count("1") for b in t[2].values()) >= FELD_MIN_ANTEIL * voll]


def _lage_in_worten(ort: dict, breite: int, hoehe: int) -> str:
    mx, my = (ort["x0"] + ort["x1"]) / 2.0 / max(1, breite), (ort["y0"] + ort["y1"]) / 2.0 / max(1, hoehe)
    senkrecht = "oben" if my < 1 / 3 else ("unten" if my > 2 / 3 else "Mitte")
    waagrecht = "links" if mx < 1 / 3 else ("rechts" if mx > 2 / 3 else "Mitte")
    return "Bildmitte" if senkrecht == waagrecht == "Mitte" else f"{senkrecht} {waagrecht}".replace(
        "Mitte ", "mittig ").replace(" Mitte", " mittig")


def _haeufigster_stoff(kennung, aussen: dict, innen: dict, fassade_zeilen: dict, breite: int) -> list:
    """Die Fassadenpunkte des häufigsten Stoffs zwischen zwei gewachsenen Flächen.

    Nur der häufigste: Ein Rahmen, ein Stück Dach oder ein Sturz neben dem Fenster ist nicht die
    Wand, mit der das Glas verglichen werden soll.
    """
    stoffe: dict = {}
    for y, b in aussen.items():
        frei = b & ~innen.get(y, 0) & fassade_zeilen.get(y, 0)
        for x in _bits_zu_x(frei):
            i = y * breite + x
            stoffe.setdefault(tuple(kennung[i][:3]), []).append(i)
    return max(stoffe.values(), key=len) if stoffe else []


def _streuung(werte: list) -> float:
    """Die mittlere Abweichung vom Median (robust gegen einzelne Ausreisser)."""
    if not werte:
        return 0.0
    werte = sorted(werte)
    mitte = werte[len(werte) // 2]
    abw = sorted(abs(w - mitte) for w in werte)
    return abw[len(abw) // 2]


def _art_der_punkte(roh: list, ausgleich, wand_k, wand_roh, abstand_grund: float, vorsprung_grund: float,
                    ton_grund: float, hell_wand: float):
    """Regel 1 und 2 an einem Teil eines Bauteils: die Art der Übermalung oder ``None``."""
    if len(roh) < 2:
        return None
    punkte = [tuple(p[k] * ausgleich[k] for k in range(3)) for p in roh]
    median = _v._median_je_kanal                                       # noqa: SLF001
    kontrast = _v._abstand(median(punkte), wand_k) / abstand_grund     # noqa: SLF001
    blau_wand = _v._blau(wand_k)                                       # noqa: SLF001
    helle = [p for p in punkte if _helligkeit(p) >= BAUTEIL_DUNKEL * hell_wand]
    warm = (sum(1 for p in helle if _v._blau(p) - blau_wand <= -_v.FENSTER_FARBTON_TRENNUNG_MIN)  # noqa: SLF001
            / len(helle)) if len(helle) >= HELL_MIN_ANTEIL * len(punkte) else 0.0
    naehe = _v.FENSTER_ABHEBUNG_ANTEIL * abstand_grund
    wie_wand = sum(1 for p in punkte if _v._abstand(p, wand_k) <= naehe) / len(punkte)   # noqa: SLF001
    ton_ki = _ton(median(roh)) - _ton(wand_roh)
    glasig = ton_grund >= REIHE_TON_MIN and ton_ki >= _v.FENSTER_FARBTON_ANTEIL * ton_grund
    if vorsprung_grund >= _v.FENSTER_FARBTON_TRENNUNG_MIN and warm >= BAUTEIL_ANTEIL:
        return ART_WARM
    if kontrast < KONTRAST_KLAR and wie_wand >= BAUTEIL_ANTEIL and not glasig:
        return ART_WAND
    return None


def _miss(ki, grund, kennung, zeilen: dict, kern: dict, fassade_zeilen: dict, breite: int,
          wand=None) -> dict:
    """Ein Bauteil oder Feld gegen die Wand daneben: Kennzahlen und, wo es reicht, Regel 1 und 2.

    ``wand`` gibt die Bildpunkte der Wand vor (für die Bestätigung auf doppelter Breite: derselbe
    Massstab wie beim Feld, das bestätigt werden soll); sonst wird sie im Ring gesucht.
    """
    voll = (1 << breite) - 1
    alle_i = _punkte(zeilen, breite)
    aus = {"n_glas": len(alle_i), "urteil": NICHT_MESSBAR, "art": None, "kontrast": None,
           "abstand_grund": None}
    if len(alle_i) < BAUTEIL_MIN_PUNKTE:
        return dict(aus, grund=f"Zu klein ({len(alle_i)} Bildpunkte, unter {BAUTEIL_MIN_PUNKTE}).")
    # NUR DER KERN ZÄHLT: Das KI-Bild sitzt oft einen Bildpunkt daneben, und am Rand eines
    # Fensters stünde dann Wand. Bleibt ohne Rand zu wenig übrig, wird nicht gemessen.
    glas_i = _punkte(kern, breite)
    if len(glas_i) < BAUTEIL_MIN_PUNKTE:
        return dict(aus, grund=f"Zu schmal (ohne Rand {len(glas_i)} Bildpunkte, unter "
                               f"{BAUTEIL_MIN_PUNKTE}).")
    glas_i = glas_i[::max(1, len(glas_i) // BAUTEIL_STICHPROBE)]
    # SPALTE FÜR SPALTE: Die Anteile werden an Mitteln über benachbarte Bildpunkte gezählt
    # (:func:`_bloecke`). Die Grenze zwischen einem übermalten Fenster und dem Glas daneben läuft
    # senkrecht; ein Block, der in einer Spalte bleibt, liegt nie halb auf beiden.
    glas_i.sort(key=lambda i: (i % breite, i // breite))
    median = _v._median_je_kanal                                       # noqa: SLF001
    glas_g = median([grund[i] for i in glas_i])
    # DIE WAND DANEBEN: der häufigste Stoff in einem Ring um das Bauteil. Der Ring reicht so weit
    # wie in v5 (sieben Bildpunkte) und bei grossen Bauteilen gut ein Drittel ihrer Höhe weit —
    # bei 1600 Bildpunkten Bildbreite ist ein Rahmen breiter als sieben Bildpunkte, und der Ring
    # läge sonst ganz im Rahmen (im achtfachen Massstab gemessen: jedes Fenster ein Fehlalarm).
    if wand is not None:
        ring_i = wand
        wand_g = median([grund[i] for i in ring_i])
        abstand_grund = _v._abstand(glas_g, wand_g)                    # noqa: SLF001
    else:
        innen = _v._zeilen_wachsen(zeilen, _v.FENSTER_RING[0], voll)      # noqa: SLF001
        nah = _v._zeilen_wachsen(zeilen, _v.FENSTER_RING[1], voll)        # noqa: SLF001
        weite = round(RING_ANTEIL_HOEHE * len(zeilen))
        fern = _v._zeilen_wachsen(zeilen, weite, voll) if weite > _v.FENSTER_RING[1] else nah  # noqa: SLF001
        ring_i = _haeufigster_stoff(kennung, fern, innen, fassade_zeilen, breite)
        if len(ring_i) < _v.FENSTER_RING_MIN:
            return dict(aus, grund=f"Zu wenig Wand daneben ({len(ring_i)} Bildpunkte).")
        ring_i = ring_i[::max(1, len(ring_i) // BAUTEIL_STICHPROBE)]
        wand_g = median([grund[i] for i in ring_i])
        abstand_grund = _v._abstand(glas_g, wand_g)                        # noqa: SLF001
        if fern is not nah and abstand_grund < WAND_SCHWACH * _v.FENSTER_TRENNUNG_MIN:
            # HEBT SICH DAS GLAS VON DIESER WAND KAUM AB (helles Glas neben heller Wand, so im
            # Obergeschoss des Testhauses), dient der nächste Stoff als Massstab, wenn er klarer trennt.
            naechster_i = _haeufigster_stoff(kennung, nah, innen, fassade_zeilen, breite)
            naechster_i = naechster_i[::max(1, len(naechster_i) // BAUTEIL_STICHPROBE)]
            if len(naechster_i) >= _v.FENSTER_RING_MIN:
                naechster_g = median([grund[i] for i in naechster_i])
                if _v._abstand(glas_g, naechster_g) > abstand_grund:       # noqa: SLF001
                    ring_i, wand_g = naechster_i, naechster_g
                    abstand_grund = _v._abstand(glas_g, wand_g)            # noqa: SLF001
    aus["abstand_grund"] = round(abstand_grund, 1)
    if abstand_grund < _v.FENSTER_TRENNUNG_MIN:
        return dict(aus, grund=f"Im Grundbild sieht das Glas aus wie die Wand daneben (Abstand "
                               f"{abstand_grund:.1f} unter {_v.FENSTER_TRENNUNG_MIN:.0f}).")
    wand_roh = median([ki[i] for i in ring_i])
    unten, oben = _v.FENSTER_AUSGLEICH_GRENZE
    ausgleich = tuple(min(oben, max(unten, (wand_g[k] + 1.0) / (wand_roh[k] + 1.0))) for k in range(3))
    wand_k = tuple(wand_roh[k] * ausgleich[k] for k in range(3))
    roh = _bloecke([ki[i] for i in glas_i])
    punkte = [tuple(p[k] * ausgleich[k] for k in range(3)) for p in roh]
    glas_k = median(punkte)
    kontrast = _v._abstand(glas_k, wand_k) / abstand_grund             # noqa: SLF001
    blau_wand = _v._blau(wand_k)                                       # noqa: SLF001
    vorsprung_grund = _v._blau(glas_g) - _v._blau(wand_g)              # noqa: SLF001
    hell_wand = _helligkeit(wand_k)
    # WARM: an den Bildpunkten gezählt, die nicht dunkel sind — Fugen einer Holzverkleidung sind
    # dunkel und zählen weder dafür noch dagegen (Mangel M3 des Gegenlesens).
    helle = [p for p in punkte if _helligkeit(p) >= BAUTEIL_DUNKEL * hell_wand]
    warm = (sum(1 for p in helle if _v._blau(p) - blau_wand <= -_v.FENSTER_FARBTON_TRENNUNG_MIN)  # noqa: SLF001
            / len(helle)) if len(helle) >= HELL_MIN_ANTEIL * len(punkte) else 0.0
    naehe = _v.FENSTER_ABHEBUNG_ANTEIL * abstand_grund
    wie_wand = sum(1 for p in punkte if _v._abstand(p, wand_k) <= naehe) / len(punkte)   # noqa: SLF001
    # DER GLASTON GEGEN DIE WAND, am rohen Bild: Eine Stimmung verschiebt ihn bei Glas und Wand gleich.
    ton_grund = _ton(glas_g) - _ton(wand_g)
    ton_ki = _ton(median(roh)) - _ton(wand_roh)
    glasig = ton_grund >= REIHE_TON_MIN and ton_ki >= _v.FENSTER_FARBTON_ANTEIL * ton_grund
    aus.update(urteil=GEHALTEN, kontrast=round(kontrast, 3), warm_anteil=round(warm, 3),
               wand_anteil=round(wie_wand, 3),
               _glas_g=glas_g, _roh=roh, _wand_roh=wand_roh, _wand_g=wand_g, _ton=_ton(median(roh)),
               _ring=ring_i, _glasig=glasig, _ton_grund=ton_grund,
               _ton_wand=(round(ton_ki, 3), round(ton_grund, 3)))
    # TEIL (a), DIE HÄLFTEN: Ist nur der obere oder untere Teil verändert, bleibt das Ganze Glas
    # (Mangel M8 des Gegenlesens). Jede Hälfte wird darum mit denselben Regeln 1 und 2 gemessen;
    # ihre Bildpunkte stehen für Regel 3 bereit.
    zeilen_kern = sorted({i // breite for i in glas_i})
    if len(zeilen_kern) >= 4:
        mitte_y = zeilen_kern[len(zeilen_kern) // 2]
        haelften = {}
        for teil, drin in (("obere", lambda y: y < mitte_y), ("untere", lambda y: y >= mitte_y)):
            roh_h = _bloecke([ki[i] for i in glas_i if drin(i // breite)])
            haelften[teil] = {"roh": roh_h, "art": _art_der_punkte(
                roh_h, ausgleich, wand_k, wand_roh, abstand_grund, vorsprung_grund, ton_grund, hell_wand)}
        aus["_haelften"] = haelften
    if vorsprung_grund >= _v.FENSTER_FARBTON_TRENNUNG_MIN and warm >= BAUTEIL_ANTEIL:
        aus.update(urteil=UEBERMALT, art=ART_WARM)
    elif kontrast < KONTRAST_KLAR and wie_wand >= BAUTEIL_ANTEIL and not glasig:
        aus.update(urteil=UEBERMALT, art=ART_WAND)
        # TEIL (a): In der Farbe der Wand, aber unruhiger als sie, ist es etwas davor, kein Anstrich.
        unruhe_glas = _streuung([_helligkeit(ki[i]) for i in glas_i])
        unruhe_wand = _streuung([_helligkeit(ki[i]) for i in ring_i])
        aus["_unruhe"] = (round(unruhe_glas, 2), round(unruhe_wand, 2))
        if unruhe_glas > TEXTUR_FREMD * max(1.0, unruhe_wand):
            aus.update(urteil=NICHT_MESSBAR, art=None, unklar=True, verdeckt=True, grund=GRUND_TEXTUR)
    elif kontrast < _v.FENSTER_BAND_KONTRAST_ANTEIL:
        # NICHT RATEN: Das Glas hebt sich von der Wand kaum ab, ist aber nicht eindeutig übermalt
        # (dunkles spiegelndes Glas in dunkler Schalung, Mangel M1 des Gegenlesens).
        aus.update(urteil=NICHT_MESSBAR, unklar=True,
                   grund=(f"Das Glas hebt sich im KI-Bild kaum von der Wand daneben ab (Kontrast "
                          f"{kontrast:.2f} unter {_v.FENSTER_BAND_KONTRAST_ANTEIL:.2f}), "
                          + ("hat aber noch den Farbton von Glas" if glasig else
                             f"ist aber nicht eindeutig uebermalt (dafuer unter {KONTRAST_KLAR:.3f})")
                          + " — dunkles Glas vor dunkler Wand oder uebermalt, nicht entscheidbar."))
    return aus


def _farbart(p) -> tuple:
    """Die Farbart ohne die Helligkeit: Rot zu Grün und Blau zu Grün, als Logarithmen.

    Mit einem Sockel (:data:`FARBART_SOCKEL`): Bei fast schwarzen Bildpunkten ist das Verhältnis
    zweier Kanäle reines Rauschen (am echten Testhaus liegt neben dem Obergeschoss eine
    Schattenfuge mit Werten um 3 von 255, und ohne Sockel galt sie als «umgefärbt»).
    """
    gruen = float(p[1]) + FARBART_SOCKEL
    return (math.log((float(p[0]) + FARBART_SOCKEL) / gruen), math.log((float(p[2]) + FARBART_SOCKEL) / gruen))


def _wand_verdeckt(felder: list) -> None:
    """Felder, deren Wand daneben im KI-Bild selbst nicht mehr wie die Wand aussieht: «nicht messbar».

    Ein Baum, den nur die KI gemalt hat, deckt Glas und Wand zugleich; das Glas ist dann nicht
    übermalt, sondern verdeckt, und die Wand daneben kein Massstab. Zu erkennen an der Farbart der
    Wand: Eine Stimmung, ein Farbstich oder ein Schatten verschieben sie bei allen Wänden des Bilds
    gleich (oder gar nicht), ein Baum nur an seiner Stelle. Verglichen wird darum die Verschiebung
    der Farbart vom Grundbild zum KI-Bild mit der mittleren Verschiebung aller Felder.
    """
    messbare = [f for f in felder if "_wand_roh" in f]
    if len(messbare) < 3:
        return
    for f in messbare:
        ki, grund = _farbart(f["_wand_roh"]), _farbart(f["_wand_g"])
        f["_schub"] = (ki[0] - grund[0], ki[1] - grund[1])
    mitte = tuple(sorted(f["_schub"][k] for f in messbare)[len(messbare) // 2] for k in range(2))
    for f in messbare:
        weg = ((f["_schub"][0] - mitte[0]) ** 2 + (f["_schub"][1] - mitte[1]) ** 2) ** 0.5
        if weg > WAND_VERAENDERT:
            f.update(urteil=NICHT_MESSBAR, art=None, unklar=True, verdeckt=True,
                     grund="Die Wand daneben sieht im KI-Bild anders aus als im Grundbild (verdeckt, "
                           "etwa von einem Baum, oder umgefaerbt) — kein Massstab fuer das Glas.")


def _aus_der_reihe(felder: list) -> None:
    """Regel 3 über alle gehaltenen Felder: den Glaston verloren, den die Geschwister noch haben.

    Der Glaston ist das Verhältnis Blau zu Rot (als Logarithmus). Eine Stimmung verschiebt es bei
    allen Scheiben eines Bilds um denselben Betrag; der UNTERSCHIED zu den Geschwistern bleibt.
    Darum wird hier am rohen KI-Bild gemessen, ohne Ausgleich an der Wand.

    Massstab sind nur Geschwister, die klar MEHR Glaston haben als das Feld selbst: Zwei graue
    Fenster nebeneinander deckten sich sonst gegenseitig. Und es gibt drei Antworten: Ein Feld
    ohne jeden Glaston ist übermalt; eines mit auffällig weniger ist «nicht messbar» (grau
    übermalt oder nur matter gespiegelt, an den Farben nicht zu entscheiden); sonst gehalten.
    """
    abstand = _v._abstand                                              # noqa: SLF001
    kandidaten = [f for f in felder if f["urteil"] == GEHALTEN]
    funde, unklare, fremde = [], [], []
    for f in kandidaten:
        ton_grund = _ton(f["_glas_g"])
        if ton_grund < REIHE_TON_MIN:
            continue                               # das Glas hat im Grundbild selbst keinen Glaston
        alle = [g for g in kandidaten if g is not f
                and not (g["_stueck"] == f["_stueck"] and g["_x0"] <= f["_x1"] and f["_x0"] <= g["_x1"])
                and abstand(g["_glas_g"], f["_glas_g"]) < _v.FENSTER_TRENNUNG_MIN]
        geschwister = [g for g in alle if g["_ton"] > f["_ton"] + REIHE_GLEICH * ton_grund]
        if len(geschwister) < max(REIHE_GESCHWISTER_MIN, (len(alle) + 1) // 2):
            continue
        # KLAR UNTER DER REIHE, GEMESSEN AN IHREM UNTEREN RAND: Scheiben eines Bilds spiegeln
        # verschieden (dunkel, Himmel, wie im Grundbild), und ihr Glaston streut entsprechend.
        # Massstab ist darum nicht die Mitte der Geschwister, sondern ihr unteres Fünftel: Wie weit
        # liegt das Feld unter der mattesten Scheibe, die noch Glas ist? (Das unterste Fünftel
        # selbst bleibt aussen vor: Dort stehen Felder, die halb auf einem übermalten Fenster liegen.)
        toene = sorted(g["_ton"] for g in geschwister)
        unten = toene[(len(toene) - 1) // 5]
        mitte = toene[len(toene) // 2]
        klar = unten - REIHE_TON_KLAR * ton_grund
        auffaellig = unten - REIHE_TON_ANTEIL * ton_grund
        hell = BAUTEIL_DUNKEL * _helligkeit(f["_wand_roh"])
        helle = [_ton(p) for p in f["_roh"] if _helligkeit(p) >= hell]
        if len(helle) < BAUTEIL_ANTEIL * len(f["_roh"]):
            continue                               # dunkel: Spiegelung oder Öffnung, kein Anstrich
        # EINE FREMDE FARBE IST KEIN ANSTRICH: Grau hat keine Farbe, Laub schon. Liegt das Feld auf
        # der Grün-Achse weit weg von seinen Geschwistern, steht etwas davor (ein Baum, den nur die
        # KI gemalt hat) — verdeckt, nicht übermalt, also «nicht messbar».
        gruen = sorted(_gruen(_v._median_je_kanal(g["_roh"])) for g in geschwister)   # noqa: SLF001
        if abs(_gruen(_v._median_je_kanal(f["_roh"])) - gruen[len(gruen) // 2]) > FARBE_FREMD:   # noqa: SLF001
            if sum(1 for t in helle if t <= auffaellig) >= BAUTEIL_ANTEIL * len(f["_roh"]):
                f["_grenze_matt"] = auffaellig
                fremde.append(f)
            continue
        entfaerbt = sum(1 for t in helle if t <= klar) / len(f["_roh"])
        matt = sum(1 for t in helle if t <= auffaellig) / len(f["_roh"])
        f["reihe_anteil"], f["_grenze"], f["_grenze_matt"] = round(entfaerbt, 3), klar, auffaellig
        f["_reihe"] = (round(mitte, 3), round(unten, 3), round(matt, 3), len(geschwister), len(alle))
        if entfaerbt < BAUTEIL_ANTEIL:
            # TEIL (a): eine Hälfte ohne jeden Glaston, das Ganze noch nicht (Mangel M8).
            for teil, h in (f.get("_haelften") or {}).items():
                if h["roh"] and sum(1 for p in h["roh"] if _helligkeit(p) >= hell and _ton(p) <= klar) \
                        >= BAUTEIL_ANTEIL * len(h["roh"]):
                    f["_teil_kandidat"] = (teil, ART_REIHE)
                    break
        if entfaerbt >= BAUTEIL_ANTEIL:
            funde.append(f)
        elif matt >= BAUTEIL_ANTEIL:
            # ZWEI SCHWACHE BELEGE ZUSAMMEN: auffällig weniger Glaston als jede Nachbarscheibe UND
            # nicht bläulicher als die Wand daneben, obwohl das Glas es im Grundbild klar war. Das
            # ist ein graues Fenster in grauer Wand, nur heller oder dunkler als sie (am Beton des
            # Eichsatzes sonst immer «nicht messbar»). Eine matte Scheibe in farbiger Wand bleibt
            # bläulicher als die Wand und damit unklar.
            ton_wand = _ton(f["_wand_roh"])
            ton_grund_wand = ton_grund - _ton(f["_wand_g"])
            wie_wand = sum(1 for p in f["_roh"] if _helligkeit(p) >= hell
                           and _ton(p) - ton_wand <= WANDTON_ANTEIL * ton_grund_wand) / len(f["_roh"])
            if ton_grund_wand >= REIHE_TON_MIN and wie_wand >= BAUTEIL_ANTEIL:
                f["_grenze"] = auffaellig
                funde.append(f)
            else:
                unklare.append(f)
    for f in funde:                                # erst am Ende: Ein Fund ändert die Geschwister nicht
        f.update(urteil=UEBERMALT, art=ART_REIHE)
    for f in fremde:
        f.update(urteil=NICHT_MESSBAR, unklar=True,
                 grund="Weder Glas noch Wand noch Grau, sondern eine andere Farbe — vermutlich verdeckt "
                       "(ein Baum oder Gegenstand davor), nicht uebermalt.")
    for f in unklare:
        f.update(urteil=NICHT_MESSBAR, unklar=True,
                 grund="Deutlich weniger Glaston als die Nachbarfenster, aber nicht eindeutig ohne — "
                       "grau uebermalt oder nur matter gespiegelt, nicht entscheidbar.")


def sprossen_scheiben(stuecke: list, kennung=None, breite: int = 0, wand=None) -> set:
    """Die Glasstücke, die Scheiben eines Fensters mit Sprossen sind (Nummern in ``stuecke``).

    Zwei Stücke gehören zu EINEM Fenster, wenn sie sich auf einer Achse zur Hälfte überdecken und
    auf der anderen nur ein Steg sie trennt, der höchstens :data:`SPROSSE_ANTEIL` ihrer kürzesten
    Seite breit ist UND im ID-Pass keine Wand enthält (``wand``: die Kennfarbe der Wand). Zwei
    Fenster nebeneinander trennt ein Stück Wand; Scheiben eines Fensters trennt der Rahmen.
    """
    orte = [_ort(z) for z in stuecke]

    def wand_im_steg(x0, x1, y0, y1) -> bool:
        if kennung is None or wand is None or not breite:
            return False
        n = sum(1 for y in range(y0, y1 + 1) for x in range(x0, x1 + 1)
                if tuple(kennung[y * breite + x][:3]) == wand)
        return n * 10 >= max(1, (x1 - x0 + 1) * (y1 - y0 + 1))
    aus = set()
    for a in range(len(orte)):
        for b in range(a + 1, len(orte)):
            p, q = orte[a], orte[b]
            kurz = min(p["x1"] - p["x0"], p["y1"] - p["y0"], q["x1"] - q["x0"], q["y1"] - q["y0"]) + 1
            for lo, hi, quer_lo, quer_hi in (("x0", "x1", "y0", "y1"), ("y0", "y1", "x0", "x1")):
                ueber = min(p[quer_hi], q[quer_hi]) - max(p[quer_lo], q[quer_lo]) + 1
                schmaler = min(p[quer_hi] - p[quer_lo], q[quer_hi] - q[quer_lo]) + 1
                steg = max(q[lo] - p[hi], p[lo] - q[hi]) - 1
                if not (ueber >= 0.5 * schmaler and 0 <= steg <= SPROSSE_ANTEIL * kurz):
                    continue
                von, bis = min(p[hi], q[hi]) + 1, max(p[lo], q[lo]) - 1
                quer = (max(p[quer_lo], q[quer_lo]), min(p[quer_hi], q[quer_hi]))
                steg_ort = (von, bis) + quer if lo == "x0" else quer + (von, bis)
                if not wand_im_steg(steg_ort[0], steg_ort[1], steg_ort[2], steg_ort[3]):
                    aus.update((a, b))
    return aus


def _oben_anders(f: dict) -> bool:
    """Hat die obere Hälfte einen anderen Glaston als die untere (Spiegelung: Himmel über einem Haus)?

    Ein Anstrich ist oben wie unten; eine Spiegelung zeigt oben den Himmel und unten, was gegenüber
    steht. Unterscheiden sich die Glastöne der Hälften um mehr als :data:`REIHE_TON_ANTEIL` des
    Glastons im Grundbild — dieselbe Schwelle, ab der Regel 3 einen Rückstand auffällig nennt —,
    ist das Feld kein gleichmässiger Anstrich.
    """
    haelften = f.get("_haelften") or {}
    toene = []
    for teil in ("obere", "untere"):
        roh = (haelften.get(teil) or {}).get("roh") or []
        if not roh:
            return False
        werte = sorted(_ton(p) for p in roh)
        toene.append(werte[len(werte) // 2])
    return abs(toene[0] - toene[1]) > REIHE_TON_ANTEIL * max(REIHE_TON_MIN, _ton(f["_glas_g"]))


def rahmen_je_stueck(ki, grund, kennung, stuecke: list, fassade_zeilen: dict, breite: int, wand) -> dict:
    """Der Rahmen um jedes Glasstück: ``{nr: (Farben im KI-Bild, Median im Grundbild)}``.

    Rahmen heisst der häufigste Stoff des ID-Passes, der das Glas unmittelbar umgibt (bis
    ``FENSTER_RING[0]`` Bildpunkte weit), sofern er nicht die Wand ist. Ein Glasstück im Band oder
    ohne eigenen Rahmen fehlt im Ergebnis.
    """
    voll = (1 << breite) - 1
    median = _v._median_je_kanal                                       # noqa: SLF001
    aus = {}
    for nr, zeilen in enumerate(stuecke):
        um = _v._zeilen_wachsen(zeilen, _v.FENSTER_RING[0], voll)          # noqa: SLF001
        ring = _haeufigster_stoff(kennung, um, zeilen, fassade_zeilen, breite)
        if len(ring) < _v.FENSTER_RING_MIN or tuple(kennung[ring[0]][:3]) == wand:
            continue
        ring = ring[::max(1, len(ring) // BAUTEIL_STICHPROBE)]
        aus[nr] = ([ki[i] for i in ring], median([grund[i] for i in ring]))
    return aus


def schmale_stuecke(stuecke: list, kennung, breite: int, wand) -> set:
    """Nachbau (a), Regel 2: die Glasstücke, die keinen Vorwurf «wie die Wand daneben» tragen (Fall G2).

    Ein Stück gehört dazu, wenn es höchstens ``2 x SCHMAL_VERSATZ`` Bildpunkte breit ist UND die Wand
    im ID-Pass in mindestens der Hälfte seiner Zeilen links oder rechts unmittelbar ans Glas grenzt
    (kein Rahmen dazwischen, etwa ein breiter Steg aus Wand). Dann schiebt ein waagrechter Versatz
    des KI-Bilds die Wand selbst in die halbe Scheibe. Liegt ein Rahmen dazwischen, schiebt er
    zuerst den Rahmen hinein, und das Glas sieht nicht aus wie die Wand.
    """
    if wand is None or not breite:
        return set()
    aus = set()
    for nr, zeilen in enumerate(stuecke):
        ort = _ort(zeilen)
        if ort["x1"] - ort["x0"] + 1 > 2 * SCHMAL_VERSATZ:
            continue
        an_wand = 0
        for y, b in zeilen.items():
            links, rechts = (b & -b).bit_length() - 2, b.bit_length()
            an_wand += any(0 <= x < breite and tuple(kennung[y * breite + x][:3]) == wand for x in (links, rechts))
        if 2 * an_wand >= len(zeilen):
            aus.add(nr)
    return aus


def _spiegelt_einzeln(f: dict, rahmen: dict) -> bool:
    """Nachbau (a), Regel 1: Kann das Fenster eine Spiegelung in EINER Scheibe sein (Fall G1)?

    Ja, wenn zweierlei zutrifft:

    * Die Scheibe ist **gleichmässig farblos bis warm**: Beide Hälften sind nach dem Ausgleich an
      der Wand nicht bläulicher als :data:`REIHE_TON_MIN`, die Grenze für «hat keinen Glaston».
    * Der **Rahmen ist erhalten**: Er sieht im KI-Bild aus wie im Grundbild (Median, Abstand unter
      ``FENSTER_TRENNUNG_MIN``), oder mindestens :data:`RAHMEN_ERHALTEN_ANTEIL` seiner Bildpunkte
      tun es. Eine Spiegelung bleibt im Glas; wer ein Fenster übermalt, nimmt den Rahmen mit. Das
      Zweite trägt auch bei einem Versatz des KI-Bilds, bei dem ein Teil des Rahmens auf Glas oder
      Wand fällt.

    Ein Feld im Band und ein Glasstück ohne eigenen Rahmen lassen sich so nicht entscheiden (der
    Rahmen eines Bands gehört allen seinen Fenstern): Dort bleibt das Urteil, wie es ist (benannte
    Grenze; «nicht messbar» kostete am Band fast jeden Fund).
    """
    if f["_geteilt"] or f["_stueck"] not in rahmen:
        return False                                   # ein Feld im Band: der Rahmen gehört dem ganzen Band
    unten, oben = _v.FENSTER_AUSGLEICH_GRENZE
    ausgleich = [min(oben, max(unten, (f["_wand_g"][k] + 1.0) / (f["_wand_roh"][k] + 1.0))) for k in range(3)]

    def aus(p):
        return tuple(p[k] * ausgleich[k] for k in range(3))
    median, abstand = _v._median_je_kanal, _v._abstand                # noqa: SLF001
    teile = [h.get("roh") for h in (f.get("_haelften") or {}).values()] or [f["_roh"]]
    for roh in teile:
        if not roh or _ton(aus(median(roh))) >= REIHE_TON_MIN:
            return False                               # bläulich: dort ist noch Glas, kein Spiegelbild
    ki_r, grund_r = rahmen[f["_stueck"]]
    if abstand(aus(median(ki_r)), grund_r) < _v.FENSTER_TRENNUNG_MIN:
        return True
    wie_rahmen = sum(1 for p in ki_r if abstand(aus(p), grund_r) < _v.FENSTER_TRENNUNG_MIN)
    return wie_rahmen >= RAHMEN_ERHALTEN_ANTEIL * len(ki_r)


def _vorsichtig(felder: list, sprossen: set, rahmen: dict | None = None, schmal: set = frozenset()) -> None:
    """Teil (a): wo ein Vorwurf nicht sicher ist, «nicht messbar» mit Grund statt «uebermalt».

    Vier Fälle aus dem zweiten Gegenlesen (M5 bis M8), je ein Grund:

    * **Sprossen-Scheiben** (M6): Jede Scheibe ist klein, und ihre «Wand daneben» ist die Sprosse;
      ein Versatz des KI-Bilds schiebt die Sprosse in die Scheibe. Kein Vorwurf an einer Scheibe.
    * **Spiegelung ohne Glaston** (M5): Haben die meisten messbaren Scheiben im KI-Bild keinen
      Glaston mehr, fehlt der Massstab — ein Haus gegenüber im Glas sieht aus wie «warm» oder
      «ohne Glaston». Regel 2 und 3 werfen dann nichts vor; Regel 1 (wie die Wand) bleibt.
    * **Geschwister ohne Glaston** (M7): Sind die Nachbarscheiben selbst fast farblos (heller
      Himmel), kann Regel 3 ein graues Fenster nicht von ihnen trennen; ein Fenster, das deutlich
      anders aussieht und nicht bläulicher ist, heisst dann «nicht messbar» statt still «gehalten».
    * **Nur ein Teil verändert** (M8): Ist die obere oder untere Hälfte übermalt, das Ganze aber
      nicht, heisst das Fenster «nicht messbar» statt still «gehalten».

    Dazu zwei Fälle aus dem dritten Gegenlesen (Nachbau, G1 und G2):

    * **Spiegelung in einer Scheibe** (G1): ein Fund «warm» oder «ohne Glaston» an einer Scheibe,
      die gleichmässig farblos bis warm ist und deren Rahmen erhalten ist (:func:`_spiegelt_einzeln`),
      auch wenn die Nachbarn ihren Glaston haben.
    * **Schmale Scheibe an der Wand** (G2): kein Vorwurf «wie die Wand» an einem Glasstück aus
      ``schmal`` (:func:`schmale_stuecke`).

    Ein Urteil «uebermalt» wird hier nur zurückgenommen, nie gesetzt.
    """
    abstand, median = _v._abstand, _v._median_je_kanal                 # noqa: SLF001
    gemessen = [f for f in felder if "_roh" in f]
    # Geschwister ohne Glaston: wie viele der messbaren Scheiben haben ihren Glaston behalten?
    mit_ton = [f for f in gemessen if f["_ton_grund"] >= REIHE_TON_MIN and not f.get("verdeckt")]
    ohne_massstab = len(mit_ton) >= 3 and sum(1 for f in mit_ton if f["_glasig"]) \
        < GESCHWISTER_GLASTON_MIN * len(mit_ton)
    gehalten = [f for f in gemessen if f["urteil"] == GEHALTEN and not f.get("unklar")]
    blinde = []
    for f in gehalten:
        ton_grund = _ton(f["_glas_g"])
        if ton_grund < REIHE_TON_MIN or f["_stueck"] in sprossen:
            continue
        alle = [g for g in gehalten if g is not f
                and not (g["_stueck"] == f["_stueck"] and g["_x0"] <= f["_x1"] and f["_x0"] <= g["_x1"])
                and abstand(g["_glas_g"], f["_glas_g"]) < _v.FENSTER_TRENNUNG_MIN]
        if len(alle) < REIHE_GESCHWISTER_MIN:
            continue
        toene = sorted(g["_ton"] for g in alle)
        unten = toene[(len(toene) - 1) // 5]
        # Am rohen Bild wie Regel 3: Liegt schon der untere Rand der Reihe so tief, dass ein farbloses
        # Fenster darunter nicht einmal auffiele, sind die Geschwister selbst ohne Glaston.
        if unten >= REIHE_TON_ANTEIL * ton_grund or f["_ton"] > unten:
            continue                                   # Regel 3 sieht hier; oder bläulicher als die Reihe
        hell = BAUTEIL_DUNKEL * _helligkeit(f["_wand_roh"])
        if sum(1 for p in f["_roh"] if _helligkeit(p) >= hell) < BAUTEIL_ANTEIL * len(f["_roh"]):
            continue                                   # dunkel: Spiegelung oder Öffnung
        reihe = median([median(g["_roh"]) for g in alle])
        if abstand(median(f["_roh"]), reihe) < _v.FENSTER_TRENNUNG_MIN:
            continue                                   # sieht aus wie die Nachbarscheiben
        blinde.append((f, (f["_ton"] + unten) / 2.0))
    for f, grenze in blinde:
        f.update(urteil=NICHT_MESSBAR, unklar=True, blind=True, _grenze_matt=grenze, grund=GRUND_BLIND)
    for f in gemessen:
        if f["urteil"] == UEBERMALT and f["_stueck"] in sprossen:
            f.update(urteil=NICHT_MESSBAR, _war=f["art"], art=None, unklar=True, sprossen=True,
                     grund=GRUND_SPROSSEN)
        elif f["urteil"] == UEBERMALT and ohne_massstab and f["art"] in (ART_WARM, ART_REIHE):
            f.update(urteil=NICHT_MESSBAR, _war=f["art"], art=None, unklar=True, spiegelung=True,
                     grund=GRUND_SPIEGELUNG)
        elif f["urteil"] == UEBERMALT and f["art"] in (ART_WARM, ART_REIHE) and _oben_anders(f):
            f.update(urteil=NICHT_MESSBAR, _war=f["art"], art=None, unklar=True, spiegelung=True,
                     grund=GRUND_SPIEGELUNG_TEIL)
        elif f["urteil"] == UEBERMALT and f["art"] in (ART_WARM, ART_REIHE) and rahmen is not None \
                and _spiegelt_einzeln(f, rahmen):
            f.update(urteil=NICHT_MESSBAR, _war=f["art"], art=None, unklar=True, spiegelung=True,
                     grund=GRUND_SPIEGELUNG_EINZELN)
        elif f["urteil"] == UEBERMALT and f["art"] == ART_WAND and f["_stueck"] in schmal:
            f.update(urteil=NICHT_MESSBAR, _war=f["art"], art=None, unklar=True, schmal_versatz=True,
                     grund=GRUND_SCHMAL.format(versatz=SCHMAL_VERSATZ))
        elif f["urteil"] == GEHALTEN and not f.get("unklar"):
            teil = f.get("_teil_kandidat") or next(((t, h["art"]) for t, h in (f.get("_haelften") or {}).items()
                                           if h["art"]), None)
            if teil and (f["_stueck"] in sprossen or (ohne_massstab and teil[1] != ART_WAND)):
                continue                               # dort wäre auch das Ganze kein Vorwurf
            if teil:
                f.update(urteil=NICHT_MESSBAR, unklar=True, _teil=teil,
                         grund=GRUND_TEIL.format(teil=teil[0], art=teil[1]))


def _bestaetigt(gruppe: list, ki, grund, kennung, zeilen: dict, kern: dict, fassade_zeilen: dict,
                breite: int) -> bool:
    """Trägt ein Fund im Band auch auf doppelter Feldbreite?

    Ein Feld ist so breit, wie das Band hoch ist; ein Vorhang kann es ganz decken. Ein Fenster ist
    breiter. Darum zählt ein Fund im Band erst, wenn auch auf doppelter Breite um seine Mitte
    mindestens :data:`BESTAETIGUNG_ANTEIL` der Bildpunkte betroffen sind. Für «nicht messbar»
    gilt dasselbe: Ein schmaler Streifen ist kein Befund.
    """
    feld = gruppe[0]["_x1"] - gruppe[0]["_x0"] + 1
    ort = _ort(zeilen)
    mitte = (min(f["_x0"] for f in gruppe) + max(f["_x1"] for f in gruppe) + 1) // 2
    x0 = max(ort["x0"], min(mitte - feld, ort["x1"] - 2 * feld + 1))
    x1 = min(ort["x1"], x0 + 2 * feld - 1)
    doppelt = _miss(ki, grund, kennung, _ausschnitt(zeilen, x0, x1), _ausschnitt(kern, x0, x1),
                    fassade_zeilen, breite, wand=gruppe[len(gruppe) // 2]["_ring"])
    if "wand_anteil" not in doppelt:
        return False
    hell = BAUTEIL_DUNKEL * _helligkeit(doppelt["_wand_roh"])
    roh = doppelt["_roh"]
    for f in gruppe:
        if f.get("verdeckt"):
            return True
        if f.get("_teil"):                         # Teil (a): nur eine Hälfte verändert
            teil, art = f["_teil"]
            h = (doppelt.get("_haelften") or {}).get(teil)
            if h and art == ART_REIHE:
                # Für «nicht messbar» reicht auf doppelter Breite der auffällige Rückstand.
                grenze = f.get("_grenze_matt", f.get("_grenze"))
                if grenze is not None and h["roh"] and sum(
                        1 for p in h["roh"] if _ton(p) <= grenze and _helligkeit(p) >= hell) \
                        >= BESTAETIGUNG_ANTEIL * len(h["roh"]):
                    return True
            elif h and h["art"] == art:
                return True
            continue
        war = f.get("_war")                        # Teil (a): zurückgenommener Fund, wie gemessen
        if war == ART_WAND and doppelt["wand_anteil"] >= BESTAETIGUNG_ANTEIL:
            return True
        if war == ART_WARM and doppelt["warm_anteil"] >= BESTAETIGUNG_ANTEIL:
            return True
        if war == ART_REIHE and sum(1 for p in roh if _ton(p) <= f["_grenze"] and _helligkeit(p) >= hell) \
                >= BESTAETIGUNG_ANTEIL * len(roh):
            return True
        if war:
            # Zurückgenommen, weil nur eine Hälfte so aussah (Spiegelung oder halb übermalt): Dann
            # trägt es auf doppelter Breite in dieser Hälfte.
            for h in (doppelt.get("_haelften") or {}).values():
                if h["art"] == war and war != ART_REIHE:
                    return True
                if war == ART_REIHE and h["roh"] and sum(
                        1 for p in h["roh"] if _ton(p) <= f["_grenze"] and _helligkeit(p) >= hell) \
                        >= BESTAETIGUNG_ANTEIL * len(h["roh"]):
                    return True
            continue
        if f.get("unklar"):
            if "_grenze_matt" not in f:            # kaum von der Wand zu trennen
                if doppelt["wand_anteil"] >= BESTAETIGUNG_ANTEIL:
                    return True
            elif sum(1 for p in roh if _ton(p) <= f["_grenze_matt"] and _helligkeit(p) >= hell) \
                    >= BESTAETIGUNG_ANTEIL * len(roh):
                return True
        elif f["art"] == ART_WAND and doppelt["wand_anteil"] >= BESTAETIGUNG_ANTEIL:
            return True
        elif f["art"] == ART_WARM and doppelt["warm_anteil"] >= BESTAETIGUNG_ANTEIL:
            return True
        elif f["art"] == ART_REIHE and sum(
                1 for p in roh if _ton(p) <= f["_grenze"] and _helligkeit(p) >= hell) \
                >= BESTAETIGUNG_ANTEIL * len(roh):
            return True
    return False


def _gruppen(felder: list) -> list:
    """Nebeneinanderliegende Felder zu Gruppen zusammenziehen (von links nach rechts)."""
    gruppen: list = []
    for f in sorted(felder, key=lambda f: f["_x0"]):
        if gruppen and f["_x0"] <= gruppen[-1][-1]["_x1"] + 1:
            gruppen[-1].append(f)
        else:
            gruppen.append([f])
    return gruppen


def _gruppen_je_grund(felder: list) -> list:
    """Wie :func:`_gruppen`, aber nur Felder derselben Art von Befund zusammen (Teil (a)).

    Ein Feld, das halb übermalt ist, und ein Feld daneben, das sich kaum von der Wand abhebt, sind
    zwei Befunde; zusammengezogen würde die Bestätigung auf doppelter Breite am falschen Ort messen.
    Die Befunde vor Teil (a) bilden zusammen eine Art, wie bisher.
    """
    def art(f):
        return "teil" if f.get("_teil") else ("zurueck" if f.get("_war") else ("blind" if f.get("blind") else ""))
    arten: list = []
    for f in felder:
        if art(f) not in arten:
            arten.append(art(f))
    return [g for a in arten for g in _gruppen([f for f in felder if art(f) == a])]


def _flaeche(gruppe: list) -> dict:
    flaeche: dict = {}
    for f in gruppe:
        for y, b in f["_zeilen"].items():
            flaeche[y] = flaeche.get(y, 0) | b
    return flaeche


def pruefe_indizes(ki, grund, kennung, glas_i, fassade_i, breite: int) -> dict:
    """Wie :func:`pruefe_bauteile`, aber mit den schon gesuchten Glas- und Fassadenpunkten."""
    hoehe = len(kennung) // breite if breite else 0
    fassade_zeilen = _v._zeilen_bits(fassade_i, breite)                # noqa: SLF001
    felder = []
    stuecke = glasstuecke(_v._zeilen_bits(glas_i, breite))             # noqa: SLF001
    kerne = []
    for nr, zeilen in enumerate(stuecke):
        kern = _kern(zeilen, _rand(zeilen))
        kerne.append(kern)
        teile = _felder(zeilen)
        for x0, x1, feld_zeilen in teile:
            if not feld_zeilen:
                continue
            feld = _miss(ki, grund, kennung, feld_zeilen, _ausschnitt(kern, x0, x1) if len(teile) > 1
                         else kern, fassade_zeilen, breite)
            feld.update(_stueck=nr, _x0=x0, _x1=x1, _zeilen=feld_zeilen, _geteilt=len(teile) > 1)
            felder.append(feld)
    _wand_verdeckt(felder)
    _aus_der_reihe(felder)
    stoffe: dict = {}
    for i in fassade_i[::max(1, len(fassade_i) // BAUTEIL_STICHPROBE)]:
        k = tuple(kennung[i][:3])
        stoffe[k] = stoffe.get(k, 0) + 1
    wand = max(stoffe, key=stoffe.get) if stoffe else None
    sprossen = sprossen_scheiben(stuecke, kennung, breite, wand)
    rahmen = rahmen_je_stueck(ki, grund, kennung, stuecke, fassade_zeilen, breite, wand)
    schmal = schmale_stuecke(stuecke, kennung, breite, wand)
    _vorsichtig(felder, sprossen, rahmen, schmal)
    bauteile = []
    for nr, zeilen in enumerate(stuecke):
        eigene = [f for f in felder if f["_stueck"] == nr]
        geteilt = bool(eigene) and eigene[0]["_geteilt"]
        n_glas = sum(bin(b).count("1") for b in zeilen.values())
        if not geteilt:
            # EIN UNGETEILTES STÜCK IST SEIN EIGENES URTEIL.
            f = eigene[0] if eigene else {"urteil": NICHT_MESSBAR, "grund": "Nicht messbar."}
            bauteile.append({"urteil": f["urteil"], "art": f.get("art"), "ort": _ort(zeilen),
                             "n_glas": n_glas, "kontrast": f.get("kontrast"), "feld": False,
                             "glasstueck": nr, **({"grund": f["grund"]} if f.get("grund") else {}),
                             **({"sprossen": True} if nr in sprossen else {})})
            continue
        # IM BAND: nebeneinanderliegende übermalte Felder sind EIN Fund, nebeneinanderliegende
        # unklare EIN «nicht messbar» — beides erst, wenn es auf doppelter Feldbreite trägt.
        funde = _gruppen([f for f in eigene if f["urteil"] == UEBERMALT])
        unklare = _gruppen_je_grund([f for f in eigene if f.get("unklar")])
        for gruppe in funde + unklare:
            if not _bestaetigt(gruppe, ki, grund, kennung, zeilen, kerne[nr], fassade_zeilen, breite):
                for f in gruppe:                   # zu schmal für ein Fenster: kein Befund
                    f.update(urteil=GEHALTEN, art=None, schmal=True, unklar=False)
        funde = [g for g in funde if g[0]["urteil"] == UEBERMALT]
        # Ein unklares Feld, das an einen Fund stösst, ist dessen Rand (halb Fenster, halb Glas)
        # und kein eigener Befund.
        raender = [(min(f["_x0"] for f in g), max(f["_x1"] for f in g)) for g in funde]
        for gruppe in unklare:
            for f in gruppe:
                if any(f["_x0"] <= x1 + 1 and x0 <= f["_x1"] + 1 for x0, x1 in raender):
                    f.update(urteil=GEHALTEN, unklar=False, rand=True)
        unklare = _gruppen_je_grund([f for g in unklare for f in g if f.get("unklar")])
        for gruppe in funde:
            schlimmstes = min(gruppe, key=lambda f: f["kontrast"])
            flaeche = _flaeche(gruppe)
            bauteile.append({"urteil": UEBERMALT, "art": schlimmstes["art"], "ort": _ort(flaeche),
                             "n_glas": sum(bin(b).count("1") for b in flaeche.values()),
                             "kontrast": schlimmstes["kontrast"], "feld": True, "glasstueck": nr})
        for gruppe in unklare:
            flaeche = _flaeche(gruppe)
            bauteile.append({"urteil": NICHT_MESSBAR, "art": None, "ort": _ort(flaeche),
                             "n_glas": sum(bin(b).count("1") for b in flaeche.values()),
                             "kontrast": min(f["kontrast"] for f in gruppe), "feld": True,
                             "glasstueck": nr, "grund": gruppe[0]["grund"]})
        heil = sorted(f["kontrast"] for f in eigene if f["urteil"] == GEHALTEN)
        if not heil and (funde or unklare):
            continue                               # das ganze Band ist Fund oder unklar: steht schon da
        rest = {"urteil": GEHALTEN if heil else NICHT_MESSBAR, "art": None, "ort": _ort(zeilen),
                "n_glas": n_glas, "kontrast": heil[len(heil) // 2] if heil else None, "feld": False,
                "glasstueck": nr, "felder": len(eigene),
                "felder_uebermalt": sum(len(g) for g in funde),
                "felder_nicht_messbar": sum(len(g) for g in unklare)}
        if not heil:
            rest["grund"] = next((f.get("grund") for f in eigene if f.get("grund")), "Nicht messbar.")
        bauteile.append(rest)
    bauteile.sort(key=lambda b: (b["ort"]["y0"], b["ort"]["x0"], b["urteil"] != UEBERMALT))
    for nr, b in enumerate(bauteile):
        b["nr"] = nr
        b["lage"] = _lage_in_worten(b["ort"], breite, hoehe)
    uebermalt = [b["nr"] for b in bauteile if b["urteil"] == UEBERMALT]
    return {"bauteile": bauteile, "uebermalt": uebermalt, "hinweis": _hinweis(bauteile),
            "methode": METHODE_BAUTEILE}


def _hinweis(bauteile: list) -> str | None:
    """Der Satz für den Bericht der Kamera — ``None``, wenn kein Bauteil übermalt ist."""
    funde = [b for b in bauteile if b["urteil"] == UEBERMALT]
    if not funde:
        return None
    gemessen = sum(1 for b in bauteile if b["urteil"] != NICHT_MESSBAR)
    orte = "; ".join(
        f"Bauteil {b['nr']} ({b['lage']}, Bildpunkte x {b['ort']['x0']} bis {b['ort']['x1']}, "
        f"y {b['ort']['y0']} bis {b['ort']['y1']}: {b['art']})" for b in funde[:6])
    mehr = f" und {len(funde) - 6} weitere" if len(funde) > 6 else ""
    return (f"{SATZ_BAUTEIL_UEBERMALT} (Hinweis, kein Urteil): {len(funde)} von {gemessen} gemessenen "
            f"Glasbauteilen sehen im KI-Bild nicht mehr aus wie Glas — {orte}{mehr}. Am Bild pruefen.")


def pruefe_bauteile(ki, grund, kennung, glas: set, *, breite: int, maske=None, ausser=()) -> dict:
    """Je Glasbauteil des ID-Passes: «gehalten», «uebermalt» oder «nicht messbar», mit Ort.

    Args:
        ki, grund, kennung: Farben je Bildpunkt (gleich lang) — KI-Bild, Grundbild und
            Material-ID-Pass.
        glas: die Kennfarben des Glases (``varianten.glasfarben``).
        breite: Bildbreite in Bildpunkten; ohne sie gibt es keinen Ort.
        maske: die Bauwerksmaske; ohne sie zählt jeder Punkt, der im ID-Pass nicht schwarz ist.
        ausser: Kennfarben, die nicht zur Fassade zählen (Umfeld, Gelände).

    Returns:
        ``{bauteile, uebermalt, hinweis, methode}`` — ``bauteile`` ist eine Liste von
        ``{nr, urteil, art, ort: {x0, y0, x1, y1}, lage, n_glas, kontrast, feld, glasstueck,
        grund?}``, von oben links nach unten rechts. ``feld`` sagt, ob der Fund ein Teil eines
        breiten Glasstücks ist (ein Fenster im Band). ``uebermalt`` nennt die Nummern,
        ``hinweis`` ist der Satz für den Bericht oder ``None``.
    """
    n = len(kennung)
    if not breite or breite <= 0 or n % breite:
        raise ValueError(f"Die Breite {breite!r} passt nicht zu {n} Bildpunkten.")
    if len(ki) != n or len(grund) != n or (maske is not None and len(maske) != n):
        raise ValueError(f"Ungleiche Laengen: KI {len(ki)}, Grundbild {len(grund)}, ID-Pass {n}, "
                         f"Maske {None if maske is None else len(maske)}.")
    ausser = {tuple(int(k) for k in f[:3]) for f in ausser or ()}
    glas_i, fassade_i = [], []
    for i, k in enumerate(kennung):
        k = tuple(k[:3])
        if not (maske[i] if maske is not None else k != (0, 0, 0)):
            continue
        if k in glas:
            glas_i.append(i)
        elif k not in ausser:
            fassade_i.append(i)
    return pruefe_indizes(ki, grund, kennung, glas_i, fassade_i, breite)
