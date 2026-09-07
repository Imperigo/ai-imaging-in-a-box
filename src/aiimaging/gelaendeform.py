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


class GelaendeformError(ValueError):
    """Die Boxen taugen nicht für eine Formaussage."""


def _spannen(lo, hi) -> tuple[float, float, float]:
    return (float(hi[0]) - float(lo[0]),
            float(hi[1]) - float(lo[1]),
            float(hi[2]) - float(lo[2]))


def merkmale(knoten, alle, *, hoch: int = 1) -> dict:
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
    lo_s = [min(float(k[1][i]) for k in alle) for i in range(3)]
    hi_s = [max(float(k[2][i]) for k in alle) for i in range(3)]
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


def urteil(knoten, alle, *, hoch: int = 1) -> dict:
    """Ist dieser Körper Gelände, Bauwerk — oder nicht entscheidbar?

    Returns:
        ``{name, urteil, grund, merkmale}``. ``urteil`` ist :data:`GELAENDE`,
        :data:`BAUWERK` oder :data:`NICHT_ENTSCHEIDBAR`; ``grund`` sagt in einem Satz,
        **welches Merkmal** entschieden hat.

    *Der Grund ist nicht Zierrat.* Eine Formaussage ohne Begründung ist von aussen nicht
    nachprüfbar, und der nächste, der sie liest, kann nur glauben oder verwerfen.
    """
    m = merkmale(knoten, alle, hoch=hoch)
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


def gelaende_knoten(alle, *, hoch: int = 1) -> dict:
    """Alle Knoten einer Szene beurteilen.

    Returns:
        ``{gelaende, unklar, bauwerk, urteile}`` — die ersten drei als Namenslisten,
        ``urteile`` mit dem vollen Satz je Knoten.

    **``unklar`` wird getrennt geführt und nicht zu einem der beiden geschlagen.** Wer
    die Zahl liest, soll sehen, wie viel die Form *nicht* entschieden hat — sonst sieht
    eine Regel, die bei der Hälfte passt, aus wie eine, die alles trifft.
    """
    urteile = [urteil(k, alle, hoch=hoch) for k in alle]
    return {
        "gelaende": tuple(u["name"] for u in urteile if u["urteil"] == GELAENDE),
        "unklar": tuple(u["name"] for u in urteile if u["urteil"] == NICHT_ENTSCHEIDBAR),
        "bauwerk": tuple(u["name"] for u in urteile if u["urteil"] == BAUWERK),
        "urteile": tuple(urteile),
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
    "gelaende_knoten", "ist_gelaende_nach_form", "merkmale", "urteil",
]
