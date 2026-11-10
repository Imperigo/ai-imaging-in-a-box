"""Gelände an der **Form** erkennen — wenn der Name es nicht trägt.

Warum es dieses Modul gibt
--------------------------
Die Geländeregel dieses Projekts liest **Namen** (:func:`aiimaging.maske.ist_gelaende`).
Auf echtem Bestand versagt sie messbar: Am 4771-Knoten-Modell schrumpft die Bauwerksbox um
**2,32 %** statt um die erwarteten Zehnerprozente. Der Kommentar an
:data:`aiimaging.maske.WOERTER_AUSDRUECKLICH_NICHT` zieht daraus schon den richtigen
Schluss, und er ist der Ausgangspunkt dieses Moduls:

    *«Damit ist der Befund nicht, welches Wort noch fehlt, sondern dass es keines gibt.»*

Belegt ist das hart. ``decke`` wäre nötig — an einem Geländemodell heissen 111 von 112
Knoten so — und ist zugleich unmöglich: In einer Gebäudedatei desselben Projekts tragen
418 von 2742 Knoten dieselbe Vokabel für Geschossdecken. **Ein Wort, das beides trennen
müsste, gibt es nicht.**

Das «von aussen» war als Feld im Szenenvertrag gedacht (``auf-20260901-67``) und liegt
dort seit dem 01.09.2026 unbeantwortet. Dieses Modul ist das zweite «von aussen» — das,
für das niemand gefragt werden muss: **die Gestalt des Körpers selbst.**

Was es ausdrücklich NICHT ist
-----------------------------
**Keine zweite Regel, sondern eine Zweitmeinung.** Der Unterschied ist der ganze Bau:

* Eine zweite Regel **widerspricht** der ersten. Dann sind zwei Regeln im Spiel, und eine
  davon ist falsch — genau davor warnt der Docstring von
  :func:`aiimaging.glbbox.bauwerksbox` beim Parameter ``regel``.
* Eine Zweitmeinung **spricht nur, wenn die erste schweigt.** Sie überstimmt nichts.

Darum wird sie in :func:`aiimaging.glbbox.bauwerksbox` erst befragt, wenn die Namensregel
fast nichts gefunden hat — an derselben Schwelle, die dort ohnehin schon warnt.

Und sie kennt die dritte Antwort
--------------------------------
:data:`NICHT_ENTSCHEIDBAR` ist hier **der häufige Fall und keine Zierde**: Eine flache,
grosse Platte auf halber Höhe kann ein Geländesockel sein oder eine Tiefgaragendecke, und
die Form entscheidet das nicht. Wo sie nichts entscheidet, sagt sie das — *nicht messbar
ist weder Gelände noch Bauwerk.*

Die Richtung des Fehlers ist entschieden
----------------------------------------
Gelände **in** der Maske ist teurer als Gelände daneben: Auf einer Bodenszene erreichte
weisses Rauschen dort den Score 0,72. Ein zu kleines Bauwerk misst weniger; ein zu grosses
misst das Falsche. Die Schwellen unten sind darum **streng** gewählt — im Zweifel Bauwerk.

Warum drei Merkmale und keine Verdeckungsrechnung
-------------------------------------------------
Gerechnet wird auf den Hüllboxen, die :func:`aiimaging.glbbox.knotenboxen` **ohnehin
schon** liefert — kein neuer Leser, keine Dreiecke, kein Blender. Dieselbe Auskunft, mit
der die HomeStation am 06.09.2026 die Höhenachse an einer echten Datei bestimmt hat.
"""
from __future__ import annotations

import math
from collections.abc import Sequence

#: Die drei Urteile. Keine Wahrheitswerte — siehe Modulkopf.
GELAENDE = "gelaende"
BAUWERK = "bauwerk"
NICHT_ENTSCHEIDBAR = "nicht entscheidbar"

#: **Grundrissanteil**, ab dem ein Körper überhaupt als Gelände in Frage kommt.
#:
#: Gemessen an der echten Bestandsdatei (`auf-20260826-51`, 06.09.2026): Die zwanzig
#: ``IfcCovering_Sub-Division:…``-Knoten bilden zusammen den grössten verbliebenen
#: «Bauwerks»-Knoten mit **47 % der Szenenspannweite** — typisch für eine Geländeplatte,
#: untypisch für ein Bauteil.
#:
#: **Die Begründung war eine Einheitenverwechslung, gemessen am 08.09.2026**
#: (`auf-20260907-82`): Diese 47 % sind ein Anteil an einer **Länge** (der
#: Szenenspannweite); ``grundrissanteil`` ist ein Anteil an einer **Fläche**
#: (Grundfläche ÷ Grundfläche, siehe :func:`merkmale`). Am selben Knoten gemessen:
#: Längenanteil **0,4715**, Flächenanteil **0,2215**, Quadrat des Längenanteils 0,2224.
#: Die 0,25 liegen damit **über** dem Knoten, den sie fangen sollten — er verfehlt sie um
#: 0,0285, und der Trichter fällt an genau dieser ersten Schwelle zu.
#:
#: **Die Zahl bleibt trotzdem stehen, und das ist eine Entscheidung.** Eine Schwelle, die
#: an diesem Knoten nachgezogen wird, ist an *dieser einen Datei* geeicht — genau die
#: Kalibrierung am eigenen Ergebnis, gegen die dieses Projekt seit dem 18.08. antritt.
#: Korrigiert ist die Begründung, nicht der Wert: *Eine falsche Herleitung ist schlimmer
#: als keine, weil sie geprüft aussieht.*
#:
#: **Und ein Nachziehen träfe ohnehin nicht den Kern** (dieselbe Messung): Die Hüllbox
#: über alle zwanzig Sub-Division-Knoten **zusammen** hat Grundrissanteil 0,918,
#: Flachheit 0,037, Tieflage 0,258 — darauf urteilt die Form ``gelaende``. Die drei
#: Merkmale sind also richtig gewählt; sie treffen die Platte, **sobald sie eine Platte
#: ist**. Der Bestand liefert sie als Familie aus zwanzig Stücken, und
#: :func:`gelaende_knoten` urteilt je Knoten. *Kein Schwellenproblem, ein
#: Korngrössenproblem.*
#:
#: *Warum nicht höher:* Ein Gelände muss das Bauwerk nicht umschliessen; ein Vorplatz
#: reicht. *Warum nicht tiefer:* Eine grosse Bodenplatte des Bauwerks liegt darunter,
#: und die soll drinbleiben. Die Zahl kommt aus `tools/studie_gelaendeform.py`.
GRUNDRISSANTEIL_MIN = 0.25

#: **Flachheit** — Höhe geteilt durch die kleinere Grundriss-Kante. Darüber ist es kein
#: Gelände mehr, sondern etwas, das aufragt.
#:
#: Ein Geländekörper ist eine Platte: gross in der Fläche, dünn in der Höhe. Ein
#: Baukörper mit demselben Grundriss ist es nicht.
FLACHHEIT_MAX = 0.15

#: **Tieflage** — wo die Oberkante im Höhenbereich der Szene sitzt, als Anteil.
#:
#: Gelände liegt unten. ``0.0`` ist der tiefste Punkt der Szene, ``1.0`` der höchste.
#: Eine Platte, deren Oberkante im oberen Drittel sitzt, ist ein Dach oder eine Decke.
TIEFLAGE_MAX = 0.35

#: Ab hier ist die Sache **nicht entscheidbar** statt Bauwerk: Der Körper erfüllt den
#: Grundrissanteil und die Flachheit, sitzt aber zu hoch.
#:
#: *Warum das nicht einfach «Bauwerk» heisst:* Eine grosse flache Platte auf halber Höhe
#: ist genau der Fall, den die Form nicht trennt — Geländesockel oder Tiefgaragendecke.
#: Ihn stillschweigend dem Bauwerk zuzuschlagen wäre eine Entscheidung, die niemand
#: gemessen hat.
TIEFLAGE_UNKLAR_MAX = 0.60


# ----------------------------------------------------------------------------------------
# RUNDE 2 (A0289, 10.11.2026): DER BEWEIS AN DER OBERSEITE
# ----------------------------------------------------------------------------------------
#
# Das Gegenlesen von A0289 hat belegt, dass die drei Merkmale oben ein Bauwerk entfernen:
# die Tiefgarage unter einem Haus ab drei Geschossen, das Sockelgeschoss unter einem Turm,
# die flache Halle neben ihrem Kamin, die Bodenplatte mit Ueberstand. Die Ursache ist keine
# Schwelle, sondern die Auskunft selbst: **Eine Huellbox sagt nicht, ob ihre Oberseite eine
# Geschossdecke oder ein Hang ist.** Ein Sockelgeschoss 40 x 30 x 4 m und ein Hangkoerper
# 40 x 30 x 4 m haben dieselbe Box.
#
# Darum gilt, wo die Oberseite gefragt wird (`gelaende_knoten(..., oberseiten=...)`,
# so ruft es `glbbox.bauwerksbox`): Die drei Merkmale machen einen Koerper nur noch zum
# **Kandidaten**. Gelaende wird er erst mit einem **Beweis an seinen Dreiecken**: Die
# Oberseite ist ueberwiegend geneigt UND uneben, sie liegt in einer Lage, nicht auf einem
# Sockel, und unter ihr ist nichts gebaut. Fehlt einer dieser Belege, heisst das
# Urteil «nicht entscheidbar», und der Koerper bleibt in der Huelle.
#
# **Schutz des Hauses geht vor Abtrennen.** Was gebaut ist, ist waagrecht und lotrecht:
# Decken, Platten, Sockel, Hallen. Eine ebene, waagrechte Flaeche kann Gelaende ODER Bauteil
# sein; die Form entscheidet sie nicht mehr.

#: Ab dieser **Neigung** (Hoehe je Laenge) zaehlt ein Dreieck der Oberseite als geneigt.
#:
#: Vier Prozent liegen ueber dem Gefaelle, das eine gebaute Flaeche zum Entwaessern traegt
#: ([Wahrscheinlich]: Flachdach, Bodenplatte und Garagenboden bis etwa 3 %). Was flacher
#: ist, kann eine Platte im Gefaelle sein und beweist kein Gelaende. Steilere gebaute
#: Flaechen (Rampe, Parkdeck, Pultdach) sind einzelne Ebenen; die faengt
#: :data:`RICHTUNGEN_MIN`.
NEIGUNG_MIN = 0.04

#: Bis zu dieser Neigung (45 Grad) gehoert ein Dreieck zur **Oberseite**; steiler ist es Wand,
#: Boeschungskante oder Rand und beweist nichts.
NEIGUNG_MAX = 1.0

#: Die Oberseite muss mindestens diesen Anteil des Grundrisses der Huellbox **decken**.
#: Ein Zaun, ein Mauerring oder die Aussenwaende einer Tiefgarage als ein Koerper haben eine
#: grosse Box und fast keine Oberseite.
DECKUNG_MIN = 0.5

#: Mindestens dieser Anteil der Oberseite (im Grundriss gemessen) muss **geneigt** sein.
GENEIGT_ANTEIL_MIN = 0.5

#: **Flachheit mit Beweis.** Wo die Oberseite gefragt wird, darf ein Kandidat hoeher sein
#: als :data:`FLACHHEIT_MAX`: Ein Hang mit 30 % Steigung ueber sein ganzes Grundstueck hat
#: Flachheit 0,3 und ist doch Gelaende. Die Box allein konnte das nicht von einem Geschoss
#: trennen; der Beweis an der Oberseite, «Gelaende traegt» und die Fussprobe koennen es.
FLACHHEIT_BEWIESEN_MAX = 0.40

#: **Lage mit Beweis.** Am Hang liegt die Oberkante des Gelaendes oft ueber der halben Hoehe
#: der Szene (20 % Steigung ueber 60 m, ein Haus mit vier Geschossen in der Mitte: 62 %).
#: Liegt sie hoeher als dieser Anteil und gelaenge der Beweis sonst, heisst das Urteil
#: «nicht entscheidbar» (``zu_hoch``): Was die Szene fast ueberragt, kann ein steiler Hang
#: sein oder ein frei geformtes Bauwerk mit einem kleinen Aufbau, und das waere das Haus.
LAGE_BEWIESEN_MAX = 0.70

#: So viele verschiedene **Richtungen** muss die geneigte Oberseite mindestens zeigen.
#:
#: Eine einzige schraege Ebene ist eine Rampe, ein Pultdach oder ein Hang; zwei sind ein
#: Satteldach, vier ein Walmdach. Gewachsener Boden ist uneben und zeigt viele. Gezaehlt
#: werden Felder von :data:`RICHTUNG_RASTER` im Gefaelle (je Achse), nicht Dreiecke.
RICHTUNGEN_MIN = 6

#: Die Feldweite, in der Richtungen gezaehlt werden: 1 % Gefaelle je Achse.
RICHTUNG_RASTER = 0.01

#: So hoch darf eine steile Flaeche **im Inneren** des Koerpers hoechstens aufragen (Meter).
#:
#: Ein Netz, das Gelaende UND Haus in einem Stueck traegt, hat eine Oberseite wie Gelaende;
#: wer es abtrennt, entfernt das Haus mit. Verraten wird es von seinen Waenden: steile
#: Dreiecke, die nicht am Rand der Huellbox liegen und hoeher sind als eine Bruestung. Der
#: Rand eines Gelaendekoerpers mit ebenem Boden liegt dagegen AM Rand und zaehlt nicht. Eine
#: Stuetzmauer von mehr als 2 m sieht aus wie eine Hauswand: dann wird nicht geraten.
WANDHOEHE_MAX = 2.0

#: So hoch darf die tiefste Stelle der Oberseite ueber der Unterkante des Koerpers liegen.
#:
#: Ein Haus aus einem Stueck mit Satteldach hat eine geneigte Oberseite, aber sie beginnt an
#: der Traufe, ein Geschoss ueber dem Boden. 1,5 m liegen unter jeder Raumhoehe. Ein
#: Gelaendekoerper mit dickerem Sockel bleibt damit «nicht entscheidbar».
SOCKEL_MAX = 1.5

#: Die Oberseite darf hoechstens so viel mal den Grundriss der Huellbox decken.
#:
#: Gelaende ist ein Hoehenfeld: ueber jedem Punkt des Grundrisses liegt es einmal. Ein Haus
#: aus einem Stueck mit Innenleben zeigt Boden UND Dach nach oben und deckt seinen Grundriss
#: zweimal oder oefter. (Ein Mass an den Waenden taugt dafuer nicht: Ein Gelaendekoerper mit
#: ebenem Boden hat am oberen Ende eines Hangs so viel Rand wie eine Halle Wand.)
LAGEN_MAX = 1.25

#: **Gelaende traegt.** Was die Szene ueberragt (alle Koerper, die hoeher reichen als das
#: bewiesene Gelaende), muss zu mindestens diesem Anteil seines Grundrisses AUF dem Gelaende
#: stehen, und mit mindestens :data:`TRAEGT_FLAECHE_MIN` Quadratmetern.
#:
#: Der Anlass ist eine unabhaengige Gegenprobe (10.11.2026): Eine flache Kuppel, ein Zelt,
#: eine Tonnenhalle, ein Freiform-Vordach haben eine geneigte, unebene Oberseite wie Gelaende.
#: Stand ein Turm DANEBEN, galten sie als Gelaende, und die Huelle war nur noch der Turm.
#: Gelaende liegt aber unter dem, was hoch ist; eine Schale neben einem Turm traegt ihn nicht.
TRAEGT_ANTEIL_MIN = 0.5

#: So viel Grundriss (Quadratmeter) muss das Ueberragende auf dem Gelaende mindestens haben:
#: ein Raum, kein Mast. Ein Zelt mit einem Mast, der durch die Spitze ragt, traegt kein Haus.
TRAEGT_FLAECHE_MIN = 4.0

#: **Die Fussprobe.** Was auf Gelaende steht, setzt auf seiner Oberseite auf: Die Unterkante
#: eines Hauses liegt hoechstens so viel (Meter) unter der Oberseite an seinem Standort
#: (ein Kellergeschoss, dazu das Gefaelle unter dem Haus). Ein Turm, der durch eine Kuppel
#: stoesst, oder ein Kamin durch ein Tonnendach beginnt am Boden, mehrere Meter unter der
#: Flaeche: Er steht nicht darauf, er steht darin. Solche Koerper gelten nicht als getragen.
FUSS_MAX = 3.5

#: Die Oberseite wird fuer die Fussprobe in so viele Felder je Richtung geteilt; je Feld
#: zaehlt die hoechste Ecke der Dreiecke, die es beruehren.
RASTER_FELDER = 16

#: Reichen andere Koerper **tiefer** als der Kandidat, und spannt ihre Huelle im Grundriss
#: mehr als diesen Anteil von ihm auf, ist er unterbaut: ein Dach ueber Waenden oder Stuetzen,
#: eine Decke ueber einem Geschoss. Ein Keller unter einem Haus bleibt darunter.
UNTERBAUT_MAX = 0.25

#: Um so viel (Meter) muss ein anderer Koerper tiefer reichen, damit er als «darunter» zaehlt.
UNTERBAUT_TOLERANZ = 0.1

#: Warum ein Kandidat «nicht entscheidbar» blieb. Kurzwoerter, damit Heim-PC und Mac denselben
#: Grund nennen und eine Probe ihn vergleichen kann.
GRUND_NICHT_LESBAR = "nicht_lesbar"
GRUND_DECKUNG = "deckung"
GRUND_EBEN = "eben"
GRUND_EINE_EBENE = "eine_ebene"
GRUND_LAGEN = "lagen"
GRUND_WAND = "wand"
GRUND_SOCKEL = "sockel"
GRUND_UNTERBAUT = "unterbaut"
GRUND_TRAEGT_NICHT = "traegt_nicht"
GRUND_ZU_HOCH = "zu_hoch"


class GelaendeformError(ValueError):
    """Die Boxen taugen nicht für eine Formaussage."""


def _spannen(lo, hi) -> tuple[float, float, float]:
    return (float(hi[0]) - float(lo[0]),
            float(hi[1]) - float(lo[1]),
            float(hi[2]) - float(lo[2]))


def _szenenbezug(alle, hoch: int):
    """Unterkante, Oberkante und Spannen der Szene — einmal je Szene, nicht je Knoten.

    Bis zum 21.10.2026 rechnete :func:`merkmale` sie für JEDEN Knoten neu. Bei 19 600
    ausgerollten Backsteinen (auf-20261021-316) waren das rund 4·10⁸ Vergleiche für eine
    Zahl, die für alle Knoten dieselbe ist. Die Ergebnisse bleiben Wort für Wort gleich.
    """
    lo_s = [min(float(k[1][i]) for k in alle) for i in range(3)]
    hi_s = [max(float(k[2][i]) for k in alle) for i in range(3)]
    return lo_s, hi_s


def merkmale(knoten, alle, *, hoch: int = 1, _bezug=None) -> dict:
    """Die drei namensfreien Merkmale **eines** Knotens, relativ zur Szene.

    Args:
        knoten: ``(name, lo, hi)`` wie aus :func:`aiimaging.glbbox.knotenboxen`.
        alle: alle Knoten derselben Szene — der Bezug, ohne den keine der drei Zahlen
            etwas bedeutet.
        hoch: Index der Höhenachse in den Koordinaten. Vorgabe ``1`` (glTF: Y oben),
            passend zu den Knotenboxen, die ``knotenboxen`` **vor** der Umrechnung nach
            Weltkoordinaten liefert.

    Returns:
        ``{grundrissanteil, flachheit, tieflage}`` — alle drei einheitenlos.

        * ``grundrissanteil`` — Grundfläche des Knotens ÷ Grundfläche der Szene
        * ``flachheit`` — Höhe ÷ kleinere Grundriss-Kante
        * ``tieflage`` — Oberkante im Höhenbereich der Szene, ``0`` unten, ``1`` oben

    Raises:
        GelaendeformError: Die Szene hat keine Ausdehnung. **Kein Rückfall auf einen
            Vorgabewert:** Eine Fläche von null macht jeden Anteil unendlich oder
            beliebig, und beides sähe wie eine Messung aus.
    """
    if not alle:
        raise GelaendeformError("Keine Knoten — über eine leere Szene sagt keine Form etwas.")

    achsen = [i for i in range(3) if i != hoch]
    lo_s, hi_s = _bezug if _bezug is not None else _szenenbezug(alle, hoch)
    szene = _spannen(lo_s, hi_s)

    grund_szene = szene[achsen[0]] * szene[achsen[1]]
    hoehe_szene = szene[hoch]
    if grund_szene <= 0 or hoehe_szene <= 0:
        raise GelaendeformError(
            f"Die Szene hat keine Ausdehnung (Grundflaeche {grund_szene}, Hoehe "
            f"{hoehe_szene}). Jeder Anteil daran waere unendlich oder beliebig — und "
            f"beides saehe wie eine Messung aus.")

    _name, lo, hi = knoten
    eigen = _spannen(lo, hi)
    kanten = sorted((eigen[achsen[0]], eigen[achsen[1]]))
    grund = eigen[achsen[0]] * eigen[achsen[1]]

    return {
        "grundrissanteil": grund / grund_szene,
        # DURCH DIE KLEINERE KANTE, nicht durch die groessere: Ein langer schmaler Steg
        # waere sonst «flach», obwohl er aufragt. Eine Kante von null macht die Flachheit
        # unendlich — das ist richtig so, denn ein Koerper ohne Grundriss ist keine Platte.
        "flachheit": (eigen[hoch] / kanten[0]) if kanten[0] > 0 else float("inf"),
        "tieflage": (float(hi[hoch]) - lo_s[hoch]) / hoehe_szene,
    }


def urteil(knoten, alle, *, hoch: int = 1, _bezug=None) -> dict:
    """Ist dieser Körper Gelände, Bauwerk — oder nicht entscheidbar?

    Returns:
        ``{name, urteil, grund, merkmale}``. ``urteil`` ist :data:`GELAENDE`,
        :data:`BAUWERK` oder :data:`NICHT_ENTSCHEIDBAR`; ``grund`` sagt in einem Satz,
        **welches Merkmal** entschieden hat.

    *Der Grund ist nicht Zierrat.* Eine Formaussage ohne Begründung ist von aussen nicht
    nachprüfbar, und der nächste, der sie liest, kann nur glauben oder verwerfen.
    """
    m = merkmale(knoten, alle, hoch=hoch, _bezug=_bezug)
    name = str(knoten[0])

    if m["grundrissanteil"] < GRUNDRISSANTEIL_MIN:
        return {"name": name, "urteil": BAUWERK, "merkmale": m,
                "grund": (f"Grundrissanteil {m['grundrissanteil']:.1%} < "
                          f"{GRUNDRISSANTEIL_MIN:.0%} — zu klein fuer Gelaende.")}

    if m["flachheit"] > FLACHHEIT_MAX:
        return {"name": name, "urteil": BAUWERK, "merkmale": m,
                "grund": (f"Flachheit {m['flachheit']:.2f} > {FLACHHEIT_MAX} — der "
                          f"Koerper ragt auf, er liegt nicht.")}

    if m["tieflage"] <= TIEFLAGE_MAX:
        return {"name": name, "urteil": GELAENDE, "merkmale": m,
                "grund": (f"Grundrissanteil {m['grundrissanteil']:.1%}, Flachheit "
                          f"{m['flachheit']:.2f}, Oberkante bei {m['tieflage']:.0%} der "
                          f"Szenenhoehe — gross, flach und unten.")}

    if m["tieflage"] <= TIEFLAGE_UNKLAR_MAX:
        return {"name": name, "urteil": NICHT_ENTSCHEIDBAR, "merkmale": m,
                "grund": (f"Gross ({m['grundrissanteil']:.1%}) und flach "
                          f"({m['flachheit']:.2f}), aber die Oberkante sitzt bei "
                          f"{m['tieflage']:.0%} der Szenenhoehe. Das trennt die Form "
                          f"nicht: Gelaendesockel und Tiefgaragendecke sehen so gleich "
                          f"aus. NICHT geraten.")}

    return {"name": name, "urteil": BAUWERK, "merkmale": m,
            "grund": (f"Flach und gross, aber die Oberkante sitzt bei "
                      f"{m['tieflage']:.0%} der Szenenhoehe — das ist ein Dach oder eine "
                      f"Decke, kein Gelaende.")}


def oberseite(dreiecke, *, hoch: int = 1, gespiegelt: bool = False) -> dict:
    """Die Oberseite eines Koerpers aus seinen Dreiecken, in Weltkoordinaten.

    Args:
        dreiecke: Liste von ``(a, b, c)``, jede Ecke drei Zahlen. Umlaufsinn wie in glTF:
            gegen den Uhrzeiger von aussen gesehen. Die Liste wird zweimal durchlaufen.
        hoch: Index der Hoehenachse.
        gespiegelt: Die Knotenmatrix spiegelt (Determinante negativ); dann dreht sich der
            Umlaufsinn.

    Returns:
        ``{oben, geneigt, steil, wand, tief, richtungen, dreiecke}``:

        * ``oben``: Grundrissflaeche der Dreiecke, die nach oben zeigen und hoechstens
          :data:`NEIGUNG_MAX` geneigt sind
        * ``geneigt``: der Teil davon mit mindestens :data:`NEIGUNG_MIN`
        * ``steil``: wahre Flaeche aller steileren Dreiecke (Waende, gleich welcher Seite);
          nur Auskunft, keine Schwelle haengt daran
        * ``wand``: die groesste Hoehe eines steilen Dreiecks, das NICHT am Rand der
          Huellbox des Koerpers liegt (0 ohne solche)
        * ``tief``: die tiefste Ecke der Oberseite (``None`` ohne Oberseite)
        * ``richtungen``: wie viele verschiedene Gefaellerichtungen der geneigte Teil zeigt

    Die Rechenschritte stehen in genau dieser Reihenfolge auch in ``Gelaendeform.swift``;
    an den Schwellen sagen beide Seiten nur dann dasselbe, wenn sie gleich rechnen.
    """
    a1, a2 = [i for i in range(3) if i != hoch]
    # Die Normale (b - a) x (c - a), zyklisch: Komponente `hoch` aus den beiden anderen Achsen.
    # Fuer hoch = 1 sind (a1, a2) = (0, 2); die zyklische Folge ist (2, 0), darum das Vorzeichen.
    zyklisch = -1.0 if (a1, a2) == (0, 2) else 1.0
    if gespiegelt:
        zyklisch = -zyklisch
    min2 = NEIGUNG_MIN * NEIGUNG_MIN
    max2 = NEIGUNG_MAX * NEIGUNG_MAX
    # Erster Durchgang: der Rand des Koerpers im Grundriss, aus seinen eigenen Ecken.
    lo1 = lo2 = math.inf
    hi1 = hi2 = -math.inf
    for dreieck in dreiecke:
        for e in dreieck:
            lo1, hi1 = min(lo1, e[a1]), max(hi1, e[a1])
            lo2, hi2 = min(lo2, e[a2]), max(hi2, e[a2])
    oben = geneigt = steil = wand = 0.0
    tief = None
    anzahl = 0
    richtungen = set()
    raster = [None] * (RASTER_FELDER * RASTER_FELDER)
    breite1, breite2 = hi1 - lo1, hi2 - lo2

    def feld(wert, lo, breite):
        if not breite > 0.0:
            return 0
        return min(RASTER_FELDER - 1, max(0, int(math.floor((wert - lo) / breite * RASTER_FELDER))))
    for a, b, c in dreiecke:
        anzahl += 1
        u1, uh, u2 = b[a1] - a[a1], b[hoch] - a[hoch], b[a2] - a[a2]
        v1, vh, v2 = c[a1] - a[a1], c[hoch] - a[hoch], c[a2] - a[a2]
        n1 = uh * v2 - u2 * vh
        n2 = u1 * vh - uh * v1
        nh = (u1 * v2 - u2 * v1) * zyklisch
        waag2 = n1 * n1 + n2 * n2
        hoch2 = nh * nh
        if waag2 > max2 * hoch2:
            steil += 0.5 * math.sqrt(waag2 + hoch2)
            am_rand = ((a[a1] == lo1 and b[a1] == lo1 and c[a1] == lo1)
                       or (a[a1] == hi1 and b[a1] == hi1 and c[a1] == hi1)
                       or (a[a2] == lo2 and b[a2] == lo2 and c[a2] == lo2)
                       or (a[a2] == hi2 and b[a2] == hi2 and c[a2] == hi2))
            if not am_rand:
                spanne = max(a[hoch], b[hoch], c[hoch]) - min(a[hoch], b[hoch], c[hoch])
                if spanne > wand:
                    wand = spanne
        elif nh > 0.0:
            grund = 0.5 * nh
            oben += grund
            if waag2 >= min2 * hoch2:
                geneigt += grund
                richtungen.add((math.floor(n1 / nh / RICHTUNG_RASTER + 0.5),
                                math.floor(n2 / nh / RICHTUNG_RASTER + 0.5)))
            t = min(a[hoch], b[hoch], c[hoch])
            if tief is None or t < tief:
                tief = t
            hoechste = max(a[hoch], b[hoch], c[hoch])
            i0, i1 = feld(min(a[a1], b[a1], c[a1]), lo1, breite1), feld(max(a[a1], b[a1], c[a1]), lo1, breite1)
            j0, j1 = feld(min(a[a2], b[a2], c[a2]), lo2, breite2), feld(max(a[a2], b[a2], c[a2]), lo2, breite2)
            for j in range(j0, j1 + 1):
                for i in range(i0, i1 + 1):
                    k = j * RASTER_FELDER + i
                    if raster[k] is None or hoechste > raster[k]:
                        raster[k] = hoechste
    return {"oben": oben, "geneigt": geneigt, "steil": steil, "wand": wand, "tief": tief,
            "richtungen": len(richtungen), "dreiecke": anzahl,
            "raster": {"lo": (lo1, lo2), "hi": (hi1, hi2), "hoehen": raster}}


def oberkante_bei(flaeche, x0, x1, z0, z1):
    """Die hoechste Stelle der Oberseite ueber dem Rechteck ``x0..x1`` x ``z0..z1`` im Grundriss,
    aus dem Raster von :func:`oberseite`; ``None``, wenn dort keine Oberseite liegt."""
    raster = (flaeche or {}).get("raster")
    if not raster:
        return None
    (lo1, lo2), (hi1, hi2) = raster["lo"], raster["hi"]
    if x1 < lo1 or x0 > hi1 or z1 < lo2 or z0 > hi2:
        return None

    def feld(wert, lo, breite):
        if not breite > 0.0:
            return 0
        return min(RASTER_FELDER - 1, max(0, int(math.floor((wert - lo) / breite * RASTER_FELDER))))

    hoechste = None
    for j in range(feld(z0, lo2, hi2 - lo2), feld(z1, lo2, hi2 - lo2) + 1):
        for i in range(feld(x0, lo1, hi1 - lo1), feld(x1, lo1, hi1 - lo1) + 1):
            h = raster["hoehen"][j * RASTER_FELDER + i]
            if h is not None and (hoechste is None or h > hoechste):
                hoechste = h
    return hoechste


def unterbauung(stelle: int, alle, *, hoch: int = 1) -> float:
    """Wie viel vom Grundriss des Koerpers ``alle[stelle]`` ist von Tieferem unterspannt?

    Gezaehlt werden Koerper, die um mehr als :data:`UNTERBAUT_TOLERANZ` **tiefer reichen**
    und den Kandidaten im Grundriss schneiden. Gemessen wird die **Huelle** ihrer
    Schnittflaechen, nicht deren Summe: Vier Stuetzen an den Ecken eines Vordachs decken
    fast nichts und unterspannen doch das ganze Dach.
    """
    a1, a2 = [i for i in range(3) if i != hoch]
    _n, lo, hi = alle[stelle]
    grund = (float(hi[a1]) - float(lo[a1])) * (float(hi[a2]) - float(lo[a2]))
    if grund <= 0:
        return 0.0
    grenze = float(lo[hoch]) - UNTERBAUT_TOLERANZ
    s_lo = [math.inf, math.inf]
    s_hi = [-math.inf, -math.inf]
    for j, (_m, l, h) in enumerate(alle):
        if j == stelle or not float(l[hoch]) < grenze:
            continue
        x0, x1 = max(float(l[a1]), float(lo[a1])), min(float(h[a1]), float(hi[a1]))
        z0, z1 = max(float(l[a2]), float(lo[a2])), min(float(h[a2]), float(hi[a2]))
        if not (x1 > x0 and z1 > z0):
            continue
        s_lo = [min(s_lo[0], x0), min(s_lo[1], z0)]
        s_hi = [max(s_hi[0], x1), max(s_hi[1], z1)]
    if s_lo[0] == math.inf:
        return 0.0
    return ((s_hi[0] - s_lo[0]) * (s_hi[1] - s_lo[1])) / grund


def traegt(gelaende_stellen, alle, *, hoch: int = 1, nur_flaeche: bool = False,
           flaechen=None) -> bool:
    """Steht das, was die Szene ueberragt, auf dem bewiesenen Gelaende?

    Gemessen wird gegen die gemeinsame Huellbox aller Gelaende-Koerper im Grundriss: die
    Grundrissflaeche der ueberragenden Koerper insgesamt und der Teil davon, der in dieser
    Huelle liegt. Siehe :data:`TRAEGT_ANTEIL_MIN` und :data:`TRAEGT_FLAECHE_MIN`.

    ``nur_flaeche``: nur die Mindestflaeche pruefen. So wird jeder Gelaende-Koerper einzeln
    gefragt, ob ueberhaupt etwas Hohes auf IHM steht; der Anteil gilt fuer alle zusammen.

    ``flaechen``: ``{stelle: oberseite(...)}`` der Gelaende-Koerper. Ist es gegeben, zaehlt ein
    ueberragender Koerper nur, wenn er die **Fussprobe** besteht (:data:`FUSS_MAX`): Seine
    Unterkante liegt bei mindestens einem Gelaende-Koerper nicht tiefer als erlaubt unter der
    Oberseite an seinem Standort. Liegt dort keine Oberseite, steht er nicht darauf.
    """
    a1, a2 = [i for i in range(3) if i != hoch]
    weg = set(gelaende_stellen)
    if not weg:
        return False
    lo1 = min(float(alle[i][1][a1]) for i in gelaende_stellen)
    lo2 = min(float(alle[i][1][a2]) for i in gelaende_stellen)
    hi1 = max(float(alle[i][2][a1]) for i in gelaende_stellen)
    hi2 = max(float(alle[i][2][a2]) for i in gelaende_stellen)
    oben = max(float(alle[i][2][hoch]) for i in gelaende_stellen)
    gesamt = innen = 0.0
    for j, (_n, l, h) in enumerate(alle):
        if j in weg or not float(h[hoch]) > oben:
            continue
        gesamt += (float(h[a1]) - float(l[a1])) * (float(h[a2]) - float(l[a2]))
        x0, x1 = max(float(l[a1]), lo1), min(float(h[a1]), hi1)
        z0, z1 = max(float(l[a2]), lo2), min(float(h[a2]), hi2)
        if not (x1 > x0 and z1 > z0):
            continue
        if flaechen is not None:
            aufgesetzt = False
            for i in gelaende_stellen:
                kante = oberkante_bei(flaechen.get(i), float(l[a1]), float(h[a1]),
                                      float(l[a2]), float(h[a2]))
                if kante is not None and not kante - float(l[hoch]) > FUSS_MAX:
                    aufgesetzt = True
                    break
            if not aufgesetzt:
                continue
        innen += (x1 - x0) * (z1 - z0)
    if nur_flaeche:
        return innen >= TRAEGT_FLAECHE_MIN
    return innen >= TRAEGT_FLAECHE_MIN and innen >= TRAEGT_ANTEIL_MIN * gesamt


def beweis(stelle: int, alle, flaeche, *, hoch: int = 1) -> dict:
    """Ist der Kandidat ``alle[stelle]`` an seiner Oberseite **nachweislich** Gelaende?

    Args:
        flaeche: Das Ergebnis von :func:`oberseite` fuer diesen Koerper, oder ``None``,
            wenn seine Dreiecke nicht lesbar sind.

    Returns:
        ``{urteil, kurz, grund}``. ``urteil`` ist :data:`GELAENDE` oder
        :data:`NICHT_ENTSCHEIDBAR`, nie :data:`BAUWERK`: Der Beweis kann nur gelingen oder
        fehlen. ``kurz`` ist eines der ``GRUND_``-Kurzwoerter (leer bei Gelaende).

    Die Reihenfolge der Fragen ist fest (und in Swift dieselbe): lesbar, Deckung, Lagen,
    geneigt, uneben, Wand, Sockel, unterbaut.
    """
    def unklar(kurz, satz):
        return {"urteil": NICHT_ENTSCHEIDBAR, "kurz": kurz, "grund": satz}

    if flaeche is None:
        return unklar(GRUND_NICHT_LESBAR,
                      "Gross, flach und unten, aber die Dreiecke des Koerpers sind nicht "
                      "lesbar. Ohne Blick auf die Oberseite kann das ein Sockelgeschoss "
                      "sein. NICHT geraten.")
    a1, a2 = [i for i in range(3) if i != hoch]
    _n, lo, hi = alle[stelle]
    grund = (float(hi[a1]) - float(lo[a1])) * (float(hi[a2]) - float(lo[a2]))
    oben = flaeche["oben"]
    if not oben >= DECKUNG_MIN * grund or not oben > 0.0:
        return unklar(GRUND_DECKUNG,
                      f"Die Oberseite deckt {oben:.1f} von {grund:.1f} m2 Grundriss, weniger "
                      f"als {DECKUNG_MIN:.0%}: ein Ring oder Geruest, keine Flaeche.")
    if oben > LAGEN_MAX * grund:
        return unklar(GRUND_LAGEN,
                      f"Die Oberseite deckt den Grundriss {oben / grund:.2f} mal, mehr als "
                      f"{LAGEN_MAX}: mehrere Lagen uebereinander (Boden und Dach), kein "
                      f"Hoehenfeld.")
    if not flaeche["geneigt"] >= GENEIGT_ANTEIL_MIN * oben:
        return unklar(GRUND_EBEN,
                      f"Die Oberseite ist eben und waagrecht ({flaeche['geneigt'] / oben:.0%} "
                      f"geneigt). Das kann Gelaende oder ein Bauteil sein (Bodenplatte, "
                      f"Decke, Sockel). NICHT geraten.")
    if flaeche["richtungen"] < RICHTUNGEN_MIN:
        return unklar(GRUND_EINE_EBENE,
                      f"Die Oberseite ist geneigt, zeigt aber nur {flaeche['richtungen']} "
                      f"Richtungen (verlangt {RICHTUNGEN_MIN}): eine oder wenige Ebenen. Das "
                      f"kann ein Hang sein, aber auch eine Rampe oder ein Dach. NICHT geraten.")
    if flaeche["wand"] > WANDHOEHE_MAX:
        return unklar(GRUND_WAND,
                      f"Im Inneren des Koerpers ragt eine steile Flaeche {flaeche['wand']:.1f} m "
                      f"auf, mehr als {WANDHOEHE_MAX} m: Das Netz kann Gelaende UND Haus in "
                      f"einem Stueck tragen, oder eine hohe Stuetzmauer. NICHT geraten.")
    if flaeche["tief"] is None or flaeche["tief"] - float(lo[hoch]) > SOCKEL_MAX:
        return unklar(GRUND_SOCKEL,
                      f"Die Oberseite beginnt mehr als {SOCKEL_MAX} m ueber der Unterkante "
                      f"des Koerpers: das kann ein Haus mit geneigtem Dach sein.")
    anteil = unterbauung(stelle, alle, hoch=hoch)
    if anteil > UNTERBAUT_MAX:
        return unklar(GRUND_UNTERBAUT,
                      f"Tiefer reichende Koerper unterspannen {anteil:.0%} des Grundrisses, "
                      f"mehr als {UNTERBAUT_MAX:.0%}: das kann ein Dach oder eine Decke sein.")
    return {"urteil": GELAENDE, "kurz": "",
            "grund": (f"Gross, flach und unten, und die Oberseite ist zu "
                      f"{flaeche['geneigt'] / oben:.0%} geneigt und uneben, in einer Lage, "
                      f"ohne Sockel, nicht unterbaut.")}


#: Ab wie vielen Knoten eine Namensfamilie als **eine** Platte beurteilt wird.
#:
#: Der Anlass ist ein gemessener Befund der HomeStation (`auf-20260907-82`, 08.09.2026):
#: An der 4771-Knoten-Bestandsdatei erreicht **genau einer** von 4771 Knoten den
#: :data:`GRUNDRISSANTEIL_MIN`. Die zwanzig ``IfcCovering_Sub-Division:…``-Knoten — das
#: eigentliche Gelände — scheitern alle daran, der grösste mit 0,2215.
#:
#: **Die Hüllbox über alle zwanzig ZUSAMMEN urteilt dagegen `gelaende`**: Grundrissanteil
#: 0,918, Flachheit 0,037, Tieflage 0,258. *Die drei Merkmale sind also richtig gewählt;
#: sie treffen die Platte, sobald sie eine Platte ist.* Der Bestand liefert sie als
#: Familie aus zwanzig Stücken, und diese Funktion urteilte bis zum 09.09.2026 je Knoten.
#:
#: **Kein Schwellenproblem, ein Korngrössenproblem** — und darum wird hier auch keine
#: Schwelle nachgezogen. Eine an dieser Datei nachgezogene Schwelle wäre an ihr geeicht.
#:
#: Drei ist die kleinste Zahl, die eine *Familie* von einem Paar unterscheidet.
FAMILIE_MINDEST = 3

#: Zeichen, an denen ein Knotenname in Segmente zerfällt.
#:
#: Die Namen kommen aus dem glTF und tragen die Gestalt ``<IfcKlasse>_<Name>_<GUID>``
#: bzw. ``<IfcKlasse>_<Typ>:<Ausprägung>:<Nummer>``. Die ersten **zwei** Segmente
#: benennen die Bauteilfamilie, alles danach die einzelne Ausprägung.
FAMILIE_TRENNER = "_:"


def familienschluessel(name) -> str:
    """Der Familienname eines Knotens — die ersten zwei Segmente seines Namens.

    ``IfcCovering_Sub-Division:Kies:184321`` → ``IfcCovering_Sub-Division``
    ``IfcSlab_Bodenplatte_2eYuY4S81HqRN8GZ4SZVcP`` → ``IfcSlab_Bodenplatte``

    *Warum zwei und nicht eines:* Ein Segment wäre die IFC-Klasse allein, und damit
    fielen alle Decken eines Hauses in eine Familie. Warum nicht drei: Die dritte Stelle
    ist bereits die einzelne Ausprägung, und dann ist jeder Knoten seine eigene Familie.
    """
    roh = str(name)
    stuecke, feld = [], []
    for zeichen in roh:
        if zeichen in FAMILIE_TRENNER:
            stuecke.append("".join(feld))
            feld = []
            if len(stuecke) >= 2:
                break
        else:
            feld.append(zeichen)
    if len(stuecke) < 2:
        stuecke.append("".join(feld))
    return "_".join(s for s in stuecke if s)


def familien(alle, *, mindest: int = FAMILIE_MINDEST) -> dict:
    """Namensfamilien mit mindestens ``mindest`` Knoten.

    Returns:
        ``{familienname: (knotenname, …)}``, nur Familien ab ``mindest`` Mitgliedern.
        Einzelstücke und Paare kommen nicht vor — sie sind keine zerlegte Platte,
        sondern ein Bauteil.
    """
    gefunden: dict[str, list] = {}
    for k in alle:
        gefunden.setdefault(familienschluessel(k[0]), []).append(str(k[0]))
    return {stamm: tuple(namen) for stamm, namen in gefunden.items()
            if len(namen) >= mindest}


def _familienbox(alle, namen):
    """Die Hüllbox über eine Familie — als Knoten, damit :func:`urteil` sie beurteilen kann."""
    teile = [k for k in alle if str(k[0]) in namen]
    lo = [min(float(k[1][i]) for k in teile) for i in range(3)]
    hi = [max(float(k[2][i]) for k in teile) for i in range(3)]
    return ("familie", lo, hi)


def gelaende_knoten(alle, *, hoch: int = 1, als_familie: bool = False,
                    oberseiten=None) -> dict:
    """Alle Knoten einer Szene beurteilen.

    Returns:
        ``{gelaende, unklar, bauwerk, urteile}`` — die ersten drei als Namenslisten,
        ``urteile`` mit dem vollen Satz je Knoten.

    **``unklar`` wird getrennt geführt und nicht zu einem der beiden geschlagen.** Wer
    die Zahl liest, soll sehen, wie viel die Form *nicht* entschieden hat — sonst sieht
    eine Regel, die bei der Hälfte passt, aus wie eine, die alles trifft.

    ``oberseiten`` (Runde 2 von A0289): eine Funktion ``stelle -> oberseite(...)`` oder
    ``None`` je Koerper. Ist sie gegeben, machen die drei Merkmale einen Koerper nur zum
    Kandidaten (Grundriss ab :data:`GRUNDRISSANTEIL_MIN`, Flachheit bis
    :data:`FLACHHEIT_BEWIESEN_MAX`, Lage bis :data:`LAGE_BEWIESEN_MAX`); Gelaende wird er
    allein mit dem :func:`beweis` an seiner Oberseite, sonst «nicht entscheidbar» (``kurz``
    nennt den Grund). Gefragt wird die Funktion nur fuer Kandidaten. Ohne sie gilt das
    Urteil der drei Merkmale wie bisher.

    ``gelaende_stellen`` und ``unklar_stellen`` nennen die Koerper nach ihrer **Stelle** in
    ``alle``: Namen sind nicht eindeutig, und wer nach ihnen trennt, nimmt ein gleichnamiges
    Geschoss mit hinaus (A0289, Befund 1).
    """
    bezug = _szenenbezug(alle, hoch) if alle else None
    urteile = [urteil(k, alle, hoch=hoch, _bezug=bezug) for k in alle]
    for u in urteile:
        if u["urteil"] == NICHT_ENTSCHEIDBAR:
            u["kurz"] = GRUND_ZU_HOCH
    if oberseiten is not None:
        flaechen = {}
        for stelle, u in enumerate(urteile):
            m = u["merkmale"]
            # KANDIDAT: gross genug, nicht aufragend, nicht das Hoechste. Die Schwellen fuer
            # Flachheit und Lage sind hier weiter als oben, weil der Beweis folgt.
            if (m["grundrissanteil"] < GRUNDRISSANTEIL_MIN
                    or m["flachheit"] > FLACHHEIT_BEWIESEN_MAX):
                if u["urteil"] != BAUWERK:
                    urteile[stelle] = dict(
                        u, urteil=BAUWERK, kurz="",
                        grund="Kein Kandidat fuer den Beweis an der Oberseite.")
                continue
            flaeche = oberseiten(stelle)
            flaechen[stelle] = flaeche
            b = beweis(stelle, alle, flaeche, hoch=hoch)
            if m["tieflage"] > LAGE_BEWIESEN_MAX:
                # ZU HOCH: Nur wenn der Beweis sonst gelaenge, steht der Koerper als «nicht
                # entscheidbar» im Befund; ein gewoehnliches Dach bleibt still Bauwerk.
                if b["urteil"] == GELAENDE:
                    urteile[stelle] = dict(
                        u, urteil=NICHT_ENTSCHEIDBAR, kurz=GRUND_ZU_HOCH,
                        grund=(f"Die Oberseite sieht aus wie Gelaende, aber ihre Oberkante "
                               f"sitzt bei {m['tieflage']:.0%} der Szenenhoehe, ueber "
                               f"{LAGE_BEWIESEN_MAX:.0%}: ein steiler Hang oder ein frei "
                               f"geformtes Bauwerk. NICHT geraten."))
                else:
                    urteile[stelle] = dict(
                        u, urteil=BAUWERK, kurz="",
                        grund="Hoch in der Szene und an der Oberseite kein Gelaende.")
                continue
            urteile[stelle] = dict(u, urteil=b["urteil"], kurz=b["kurz"], grund=b["grund"])
        # GELAENDE TRAEGT: Steht das, was die Szene ueberragt, nicht auf dem bewiesenen
        # Gelaende, ist es eine Schale, ein Zelt, eine Halle NEBEN dem Hohen. Dann bleibt alles.
        # Zuerst JEDER fuer sich: Ein Koerper, auf dem selbst nichts Hohes steht, wird nicht
        # mitgenommen, nur weil ein anderer das Haus traegt (ein Zelt neben dem Haus am Hang).
        # Dann alle zusammen gegen ihre gemeinsame Huelle.
        bewiesen = [i for i, u in enumerate(urteile) if u["urteil"] == GELAENDE]
        allein = [i for i in bewiesen
                  if not traegt([i], alle, hoch=hoch, nur_flaeche=True, flaechen=flaechen)]
        zusammen = [i for i in bewiesen if i not in allein]
        if zusammen and not traegt(zusammen, alle, hoch=hoch, flaechen=flaechen):
            allein = bewiesen
        if allein:
            for i in allein:
                urteile[i] = dict(
                    urteile[i], urteil=NICHT_ENTSCHEIDBAR, kurz=GRUND_TRAEGT_NICHT,
                    grund=("Die Oberseite sieht aus wie Gelaende, aber was die Szene "
                           "ueberragt, steht nicht darauf: Das kann eine Schale, ein Zelt "
                           "oder eine Halle neben einem Turm sein. NICHT geraten."))

    # DIE FAMILIENPRUEFUNG, und sie ist VORGABE AUS.
    #
    # Sie aendert, was als Gelaende gilt — und daran haengt die Bauwerksmaske, an der
    # jede Messung dieses Projekts haengt. Eine stillschweigend geaenderte Maske waere
    # genau die Sorte Aenderung, die eine Messreihe unbrauchbar macht, ohne dass es
    # auffaellt. Wer sie einschaltet, weiss also, dass er sie einschaltet.
    if als_familie:
        nach_name = {u["name"]: u for u in urteile}
        for stamm, namen in familien(alle).items():
            if any(nach_name[n]["urteil"] == GELAENDE for n in namen if n in nach_name):
                continue
            u_familie = urteil(_familienbox(alle, set(namen)), alle, hoch=hoch,
                               _bezug=bezug)
            if u_familie["urteil"] != GELAENDE:
                continue
            for n in namen:
                if n not in nach_name:
                    continue
                nach_name[n] = dict(
                    nach_name[n],
                    urteil=GELAENDE,
                    familie=stamm,
                    grund=(f"Einzeln nicht entschieden ({nach_name[n]['grund']}) — aber "
                           f"die Huellbox ueber die {len(namen)} Knoten der Familie "
                           f"{stamm!r} urteilt Gelaende: {u_familie['grund']}"))
        urteile = [nach_name[u["name"]] for u in urteile]

    return {
        "gelaende": tuple(u["name"] for u in urteile if u["urteil"] == GELAENDE),
        "unklar": tuple(u["name"] for u in urteile if u["urteil"] == NICHT_ENTSCHEIDBAR),
        "bauwerk": tuple(u["name"] for u in urteile if u["urteil"] == BAUWERK),
        "urteile": tuple(urteile),
        "gelaende_stellen": tuple(i for i, u in enumerate(urteile)
                                  if u["urteil"] == GELAENDE),
        "unklar_stellen": tuple(i for i, u in enumerate(urteile)
                                if u["urteil"] == NICHT_ENTSCHEIDBAR),
    }


def ist_gelaende_nach_form(alle, *, hoch: int = 1):
    """Eine Regel in der Gestalt von :func:`aiimaging.maske.ist_gelaende` — ``name → bool``.

    Damit lässt sie sich dort einsetzen, wo heute die Namensregel steht, **ohne dass der
    Aufrufer etwas über Formen wissen muss**.

    ``nicht entscheidbar`` ergibt hier ``False``, also **Bauwerk** — und das ist die
    strengere Auslegung, nicht die bequeme: Gelände in der Maske ist teurer als Gelände
    daneben. Wer die dritte Antwort *sehen* will, nimmt :func:`gelaende_knoten`; diese
    Hülle kann sie nicht ausdrücken, und darum steht es hier.
    """
    befund = gelaende_knoten(alle, hoch=hoch)
    namen = set(befund["gelaende"])
    return lambda name: str(name) in namen


__all__ = [
    "BAUWERK", "GELAENDE", "NICHT_ENTSCHEIDBAR", "FLACHHEIT_MAX",
    "GRUNDRISSANTEIL_MIN", "TIEFLAGE_MAX", "TIEFLAGE_UNKLAR_MAX", "GelaendeformError",
    "FAMILIE_MINDEST", "FAMILIE_TRENNER", "familien", "familienschluessel",
    "gelaende_knoten", "ist_gelaende_nach_form", "merkmale", "urteil",
    "RICHTUNGEN_MIN", "RICHTUNG_RASTER", "FLACHHEIT_BEWIESEN_MAX", "LAGE_BEWIESEN_MAX", "GRUND_EINE_EBENE",
    "NEIGUNG_MIN", "NEIGUNG_MAX", "DECKUNG_MIN", "GENEIGT_ANTEIL_MIN", "SOCKEL_MAX",
    "TRAEGT_ANTEIL_MIN", "TRAEGT_FLAECHE_MIN", "FUSS_MAX", "RASTER_FELDER", "oberkante_bei", "GRUND_TRAEGT_NICHT", "traegt",
    "LAGEN_MAX", "WANDHOEHE_MAX", "GRUND_WAND", "UNTERBAUT_MAX", "UNTERBAUT_TOLERANZ", "GRUND_NICHT_LESBAR",
    "GRUND_DECKUNG", "GRUND_EBEN", "GRUND_LAGEN", "GRUND_SOCKEL", "GRUND_UNTERBAUT",
    "GRUND_ZU_HOCH", "beweis", "oberseite", "unterbauung",
]
