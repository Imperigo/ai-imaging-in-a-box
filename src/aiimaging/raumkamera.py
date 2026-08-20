"""RAUMKAMERA — wo eine Kamera IM Raum steht.

Warum dieses Modul entsteht
---------------------------
Bis zum 22.08.2026 konnte dieses Projekt Gebäude nur von **aussen**. :mod:`aiimaging.kameras`
rechnet ausschliesslich Standpunkte um eine Hüllbox herum, und seine Konstante
``WANDABSTAND_M = 10.0`` macht eine Innenaufnahme nicht etwa schlecht, sondern
**rechnerisch unmöglich**: In einem 4 m breiten Zimmer gibt es keinen zulässigen
Standpunkt. Wer bis dahin „Innenbild" sagte, bekam eine Kamera zehn Meter ausserhalb der
Wand.

Seit demselben Tag lassen sich Räume aus IFC lesen (:mod:`aiimaging.runners.ifc_raeume_runner`).
Dieses Modul ist der Schritt danach: aus einem Raum Standpunkte rechnen.

Ein Befund von aussen, der die frontale Ansicht trifft
------------------------------------------------------
`auf-20260822-29` hat nebenbei etwas gemessen, das hier zählt und beim Bauen dieses
Moduls noch nicht bekannt war:

> **Für ρ über der Bauwerksmaske muss die Blickrichtung MEHR ALS EINE Fläche zeigen —
> sonst misst man den Schätzer statt der Geometrie.**

Gemessen an einer Aussenaufnahme: Frontal vor der Langseite lieferte dieselbe Szene
−0.8305, +0.6509 und +0.8159 — **mit Vorzeichenwechsel**. Der Grund ist geometrisch: Von
vorn zeigt ein Bauwerk *eine* flache Wand, fast parallel zur Bildebene. Innerhalb der
Maske gibt es dann keine Tiefenstaffelung, die sich ordnen liesse, und der Tiefenschätzer
trägt seine eigene Annahme ein.

**Was das für :func:`frontaler_standpunkt` heisst.** Eine frontale Innenaufnahme zeigt
genau das: eine Wand, senkrecht zur Blickachse. Die Vermutung liegt nahe, dass unsere
Geometrie-QA sie nicht sinnvoll bewerten kann — **aber sie ist ungemessen.** Innen ist die
Lage nicht dieselbe wie aussen: Boden, Decke und die anschneidenden Seitenwände liegen
schräg im Bild und tragen Tiefe, auch wenn die Stirnwand es nicht tut.

Die frontale Ansicht wird darum **weiter gerechnet und weiter geliefert**. Sie
wegzulassen, weil ein Aussenbefund sie verdächtig macht, wäre ein Schluss von einer
Messung auf einen Fall, den sie nicht enthält. Der Verdacht steht als eigener Punkt in
``docs/PLAN.md``, und die Messung dazu ist billig: dieselbe Szene, beide Blickarten, ρ und
Kante vergleichen.

Was hier NICHT drin ist
-----------------------
Der **Verdeckungstest**. Ob zwischen Kamera und Blickziel ein Möbel, eine Stütze oder
eine Brüstung steht, weiss nur die Szene, und die lebt jenseits der Prozessgrenze. Was
hier gerechnet wird, ist die Lage im **Raumumriss** — dass die Kamera nicht in einer Wand
steht und dass der Raum überhaupt Platz für sie hat. Das ist notwendig und nicht
hinreichend, und es steht so in jedem Befund.

Die drei Entscheidungen, die hier fallen
-----------------------------------------
**1 · Die Kamera steht auf halber Raumhöhe, und das ist keine Faustregel.** Bei
waagrechter Kamera bekommen Boden und Decke **exakt gleich viel Bildfläche**, wenn die
Kamera auf halber Raumhöhe steht — unabhängig von Brennweite und Abstand. Nachgerechnet
am 21.08. über 24/35/50 mm und 3/5/8 m: Differenz jedes Mal 0,000000. Die
Ratgeber-Faustregel *„auf halber Höhe zwischen Boden und Decke"* bekommt damit eine
präzise geometrische Bedeutung. Bei 2,55 m Raumhöhe sind das 1,275 m; die 1,70 m aus
``kameras.AUGENHOEHE_M`` erzeugen dort **28 Prozentpunkte Ungleichgewicht** und liegen
ausserdem ausserhalb dessen, was die Innenraumfotografie überhaupt nennt (0,91–1,52 m).

**2 · Die Kamera bleibt waagrecht.** Parallele Vertikalen entstehen dadurch, dass die
Bildebene lotrecht steht — HABS/NPS schreibt die Perspektivkorrektur *bei der Aufnahme*
zwingend vor, und es ist die einzige institutionell verbindliche Regel des Fachs. Das
Blickziel liegt darum **auf Kamerahöhe**, nicht darüber. (``kameras.py`` tut das bis heute
anders und erzeugt 9,46° Neigung; die Umstellung dort ist ein eigener Schritt.)

**3 · Es werden BEIDE Blickarten gerechnet, und gewählt wird anderswo.** Ob eine frontale
Einpunktaufnahme oder ein Blick über Eck richtig ist, hängt laut allen gesichteten Quellen
daran, ob die Stirnwand ein **Motiv** trägt — einen Kamin, eine Küchenzeile, eine
Fensterfront. **Das steht in keiner IFC-Datei.** Ein Programm, das hier entscheidet, tut
so, als wüsste es etwas, das es nicht wissen kann. Also rechnet es beides und reicht
beides weiter (Owner-Entscheid 22.08.2026).

Woher die Zahlen kommen
-----------------------
Aus ``docs/recherche/KOMPOSITION_INNEN.md`` und der Synthese in
``docs/KAMERAREGELN_2026-08-21.md``. Jede Zahl trägt unten, ob sie **belegt**, **hergeleitet**
oder **gesetzt** ist. Wo die Recherche nichts fand, steht das ausdrücklich — und dann ist
die Zahl eine Setzung dieses Projekts und keine Fachaussage.

Abhängigkeiten: reine stdlib. Kein ``bpy``, kein ``ifcopenshell``, ohne Oberfläche
aufrufbar (Regeln 2 und 4).
"""
from __future__ import annotations

import math
from typing import Sequence

#: Wie weit die Kamera mindestens von jeder Wand wegbleibt, in Metern.
#:
#: **Gesetzt, nicht belegt.** Der PBRS-Datensatz (arXiv 1612.07429) schliesst Standpunkte
#: innerhalb von **10 cm** eines Hindernisses aus — das ist aber die Schranke dafür, nicht
#: *in* der Wand zu stehen, und keine fotografische Angabe. Ein Stativ braucht mehr, und
#: eine Kamera 10 cm vor einer Wand sieht von ihr nichts als Unschärfe.
#:
#: 30 cm sind die Setzung dieses Projekts: genug für ein Stativbein, wenig genug, dass
#: auch ein kleines Zimmer noch einen Standpunkt hat. Wer sie ändert, ändert damit auch,
#: welche Räume überhaupt als aufnehmbar gelten — darum steht sie als Parameter.
WANDABSTAND_INNEN_M = 0.30

#: Kleinster Raum, der überhaupt einen Standpunkt bekommt — als kleinste Ausdehnung.
#:
#: Unterhalb davon bleibt nach zweimal :data:`WANDABSTAND_INNEN_M` nichts übrig. Der
#: Befund heisst dann ausdrücklich *kein Standpunkt* und nicht *irgendein Standpunkt*:
#: Die Fotografie kennt für enge Räume eine Eskalationskaskade — Ecke, Türöffnung,
#: Nachbarraum, weitwinkliger, und zuletzt **aufgeben und einen Teilausschnitt zeigen**.
#: Der letzte Schritt ist der, den ein Programm auslässt und ein Fotograf
#: selbstverständlich geht.
MIN_RAUMMASS_M = 2 * WANDABSTAND_INNEN_M + 0.4

#: Blickarten. Beide werden gerechnet; welche gefahren wird, entscheidet der Auftrag.
ART_FRONTAL = "frontal"
ART_UEBER_ECK = "ueber_eck"

#: Wie die Zielwand für die frontale Aufnahme gewählt wird.
#:
#: **Nach Länge — eine Setzung, und eine schwache.** Die Praxis wählt die Wand mit dem
#: Motiv; ein Motiv steht in keiner IFC-Datei. Die längste Wand ist die einzige Wahl, die
#: sich aus der reinen Geometrie begründen lässt, und sie ist oft, aber nicht immer, die
#: richtige. Der Befund sagt das bei jedem Standpunkt dazu, statt es zu verschweigen.
ZIELWAND_REGEL = "laengste_wand"


#: Arbeitsbrennweite im Innenraum, Kleinbild. **Belegt**: Die Recherche findet
#: durchgehend 24–35 mm, mit 24 mm als weitem Ende, das noch als normal gilt
#: (`docs/recherche/KOMPOSITION_INNEN.md`).
BRENNWEITE_INNEN_MM = 24.0

#: Wo Weitwinkel in Unglaubwürdigkeit kippt. **Belegt und bindend**: Airbnb schreibt
#: seinen Fotografen wörtlich vor, *„never capture wider than 16mm"* — eine
#: Plattformvorgabe, keine Meinung.
#:
#: Für dieses Projekt zählt das doppelt: Wir prüfen Bilder auf ihre **Geometrietreue**.
#: Ein Objektiv, das den Raum grösser macht, als er ist, erzeugt genau den Fehler, den die
#: QA finden soll — nur diesmal von uns selbst eingebaut.
BRENNWEITE_GRENZE_MM = 16.0

#: Sensorbreite, Kleinbild. Dieselbe Bezugsgrösse wie in :mod:`aiimaging.kameras`.
SENSOR_BREITE_MM = 36.0


class RaumkameraError(ValueError):
    """Der Raum taugt nicht zum Rechnen. Erbt von ``ValueError`` wie alle Fehler hier."""


# --------------------------------------------------------------------------------------
# Geometrie in der Waagerechten
# --------------------------------------------------------------------------------------

def _als_polygon(grundriss) -> list[tuple[float, float]]:
    """Den Grundriss prüfen und als Liste von Punkten zurückgeben."""
    if not grundriss:
        raise RaumkameraError(
            "Kein Grundriss. Ohne Umriss gibt es keinen Innenraum, in dem etwas stehen "
            "könnte — und ein leerer Umriss ist nicht dasselbe wie ein leerer Raum."
        )
    punkte = []
    for i, p in enumerate(grundriss):
        if len(p) != 2:
            raise RaumkameraError(
                f"Grundrisspunkt {i} hat {len(p)} Werte statt zwei. Dieser Umriss liegt "
                f"in der Waagerechten; die Höhe steht getrennt daneben, weil sie einen "
                f"eigenen Bezugspunkt hat."
            )
        punkte.append((float(p[0]), float(p[1])))
    if len(punkte) < 3:
        raise RaumkameraError(
            f"Ein Umriss braucht mindestens drei Ecken, dieser hat {len(punkte)}."
        )
    return punkte


def flaeche(polygon: Sequence[Sequence[float]]) -> float:
    """Die **vorzeichenbehaftete** Fläche. Positiv heisst gegen den Uhrzeigersinn.

    Das Vorzeichen ist hier kein Nebenprodukt, sondern die Auskunft, die gebraucht wird:
    Bei welcher Umlaufrichtung liegt das Innere links der Kante? Der Raumleser meldet den
    Umlaufsinn, **begradigt ihn aber nicht** — das ist die Entscheidung dessen, der den
    Ring benutzt, und hier fällt sie.
    """
    p = _als_polygon(polygon)
    s = 0.0
    for i in range(len(p)):
        x1, y1 = p[i]
        x2, y2 = p[(i + 1) % len(p)]
        s += x1 * y2 - x2 * y1
    return s / 2.0


def _gegen_uhrzeigersinn(polygon: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """Den Umriss auf gegen den Uhrzeigersinn drehen.

    Danach liegt das Innere **links** jeder gerichteten Kante, und die innere Normale ist
    ``(-dy, dx)``. Ohne diese Vereinheitlichung zeigte dieselbe Rechnung je nach Datei
    nach innen oder nach aussen — und eine Kamera stünde in der Wand statt davor.
    """
    return polygon if flaeche(polygon) > 0 else list(reversed(polygon))


def _kanten(polygon: list[tuple[float, float]]):
    """Je Kante: ``(anfang, ende, laenge, innere_normale)``."""
    n = len(polygon)
    for i in range(n):
        a, b = polygon[i], polygon[(i + 1) % n]
        dx, dy = b[0] - a[0], b[1] - a[1]
        laenge = math.hypot(dx, dy)
        if laenge <= 0.0:
            continue          # Doppelte Ecke — keine Kante, kein Fehler.
        yield a, b, laenge, (-dy / laenge, dx / laenge)


def ist_innen(punkt: Sequence[float], polygon: Sequence[Sequence[float]]) -> bool:
    """Liegt der Punkt im Umriss? Strahlensatz nach rechts, ungerade Zahl von Kreuzungen.

    Nötig, weil Räume **nicht konvex** sein müssen: Der L-förmige Testraum hat eine
    einspringende Ecke, und in ihrer Nähe liegen Punkte ausserhalb, die einer
    Mittelpunkts-Rechnung als innen erschienen.
    """
    p = _als_polygon(polygon)
    x, y = float(punkt[0]), float(punkt[1])
    drin = False
    for i in range(len(p)):
        x1, y1 = p[i]
        x2, y2 = p[(i + 1) % len(p)]
        if (y1 > y) != (y2 > y):
            schnitt_x = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
            if x < schnitt_x:
                drin = not drin
    return drin


def abstand_zum_rand(punkt: Sequence[float], polygon: Sequence[Sequence[float]]) -> float:
    """Kürzester Abstand zu irgendeiner Wand, in Metern. Immer positiv.

    Sagt **nicht**, ob der Punkt innen liegt — dafür ist :func:`ist_innen` da. Beides zu
    vermischen wäre bequem und falsch: Ein Punkt zwei Meter ausserhalb der Wand hat
    denselben Abstand wie einer zwei Meter innerhalb.
    """
    p = _als_polygon(polygon)
    x, y = float(punkt[0]), float(punkt[1])
    kleinster = float("inf")
    for a, b, laenge, _n in _kanten(p):
        dx, dy = b[0] - a[0], b[1] - a[1]
        t = ((x - a[0]) * dx + (y - a[1]) * dy) / (laenge * laenge)
        t = max(0.0, min(1.0, t))
        kleinster = min(kleinster, math.hypot(x - (a[0] + t * dx), y - (a[1] + t * dy)))
    return kleinster


# --------------------------------------------------------------------------------------
# Passt der Raum ins Bild? — der Unterschied zwischen „steht legal" und „sieht etwas"
# --------------------------------------------------------------------------------------

def _sichtbare_breite(abstand_m: float, brennweite_mm: float,
                      seitenverhaeltnis: float) -> float:
    """Wie breit der Ausschnitt in ``abstand_m`` Entfernung ist, in Metern."""
    hfov = 2.0 * math.atan(SENSOR_BREITE_MM / (2.0 * brennweite_mm))
    return 2.0 * abstand_m * math.tan(hfov / 2.0)


def noetige_brennweite(abstand_m: float, breite_m: float,
                       seitenverhaeltnis: float = 1.6) -> float:
    """Welche Brennweite es bräuchte, damit ``breite_m`` in ``abstand_m`` ins Bild passt.

    Reine Umstellung von :func:`_sichtbare_breite` nach der Brennweite. Der Nutzen liegt
    nicht in der Zahl, sondern im Vergleich mit :data:`BRENNWEITE_GRENZE_MM`: Sie sagt,
    **ob ein Standpunkt überhaupt fotografierbar ist** oder nur rechnerisch existiert.
    """
    if abstand_m <= 0 or breite_m <= 0:
        raise RaumkameraError(
            f"Abstand und Breite müssen positiv sein, waren {abstand_m} und {breite_m}.")
    return SENSOR_BREITE_MM * abstand_m / breite_m


def _sichtfeld(abstand_m: float, ziel_breite_m: float | None, *,
               brennweite_mm: float, seitenverhaeltnis: float) -> dict:
    """Ob das Ziel bei dieser Brennweite ins Bild passt — und was es sonst bräuchte.

    **Warum das dazugehört und nicht Kür ist.** Ein Standpunkt, der geometrisch zulässig
    ist, aber seine Zielwand nicht fasst, ist halb nützlich — und stillschweigend
    ausgeliefert wäre er irreführend. Gemessen am L-förmigen Testraum: Der frontale
    Standpunkt steht 4,10 m vor einer 7,40 m breiten Wand und sieht bei 24 mm davon
    **6,15 m**. Nötig wären 20 mm.

    Die Fotografie kennt für diesen Fall eine Kaskade — weiter zurück, weitwinkliger, und
    zuletzt **aufgeben und einen Teilausschnitt zeigen**. Weiter zurück geht hier nicht
    (die Wand im Rücken ist die Schranke). Bleibt die Brennweite, und die hat eine
    belegte Grenze.
    """
    sichtbar = _sichtbare_breite(abstand_m, brennweite_mm, seitenverhaeltnis)
    antwort = {"brennweite_mm": brennweite_mm, "sichtbare_breite_m": round(sichtbar, 4),
               "ziel_breite_m": ziel_breite_m, "passt": None,
               "noetige_brennweite_mm": None, "hinweis": ""}
    if ziel_breite_m is None:
        antwort["hinweis"] = (
            "Kein bestimmtes Ziel, dessen Breite zu fassen wäre — bei einem Blick über "
            "Eck gibt es keine Wand, die ganz ins Bild soll. 'passt' bleibt darum "
            "NICHT GEMESSEN und nicht 'ja'.")
        return antwort

    antwort["passt"] = sichtbar >= ziel_breite_m
    if antwort["passt"]:
        return antwort

    noetig = noetige_brennweite(abstand_m, ziel_breite_m, seitenverhaeltnis)
    antwort["noetige_brennweite_mm"] = round(noetig, 2)
    if noetig >= BRENNWEITE_GRENZE_MM:
        antwort["hinweis"] = (
            f"Bei {brennweite_mm:.0f} mm sind nur {sichtbar:.2f} m von {ziel_breite_m:.2f} m "
            f"im Bild. Nötig wären {noetig:.1f} mm — noch über der Grenze von "
            f"{BRENNWEITE_GRENZE_MM:.0f} mm, also machbar, aber weiter als die übliche "
            f"Arbeitsbrennweite.")
    else:
        antwort["hinweis"] = (
            f"Bei {brennweite_mm:.0f} mm sind nur {sichtbar:.2f} m von {ziel_breite_m:.2f} m "
            f"im Bild, und nötig wären {noetig:.1f} mm — UNTER der belegten Grenze von "
            f"{BRENNWEITE_GRENZE_MM:.0f} mm. Ab dort macht das Objektiv den Raum grösser, "
            f"als er ist. Für ein Projekt, das Bilder auf Geometrietreue prüft, wäre das "
            f"der Fehler, den es finden soll — selbst eingebaut. Die Fotografie zeigt hier "
            f"einen Teilausschnitt.")
    return antwort


def _lauf_nach_innen(start: tuple[float, float], richtung: tuple[float, float],
                     polygon: list[tuple[float, float]], *, abstand: float,
                     schritt: float = 0.01) -> tuple[float, float] | None:
    """Von ``start`` in ``richtung`` abschreiten und den gültigen Bereich zurückgeben.

    Returns:
        ``(t_min, t_max)`` — der erste und der letzte Schritt, an dem der Punkt **innen**
        liegt **und** mindestens ``abstand`` von jeder Wand entfernt ist. ``None``, wenn
        es keinen solchen Schritt gibt.

    **Warum abgeschritten und nicht gerechnet.** Für einen konvexen Raum liesse sich der
    gültige Bereich geschlossen bestimmen. Räume sind aber **nicht konvex** — der
    L-förmige Testraum hat eine einspringende Ecke, und dort zerfällt der gültige Bereich
    entlang eines Strahls in mehrere Stücke. Eine Intervall-Rechnung nähme das erste Stück
    für das ganze und stellte die Kamera hinter eine Wand.

    Die Schrittweite ist die Auflösung dieser Antwort und keine Näherung an eine exakte:
    Ein Zentimeter ist feiner, als jede Kamerastellung je gemeint ist.
    """
    laengste = math.hypot(
        max(p[0] for p in polygon) - min(p[0] for p in polygon),
        max(p[1] for p in polygon) - min(p[1] for p in polygon),
    )
    t_min = t_max = None
    t = 0.0
    while t <= laengste:
        punkt = (start[0] + richtung[0] * t, start[1] + richtung[1] * t)
        if ist_innen(punkt, polygon) and abstand_zum_rand(punkt, polygon) >= abstand:
            if t_min is None:
                t_min = t
            t_max = t
        t += schritt
    return None if t_min is None else (t_min, t_max)


def _kamerahoehe(raum: dict) -> tuple[float | None, str]:
    """Die Kamerahöhe in Weltkoordinaten — oder eine benannte Lücke.

    **Halbe Raumhöhe**, weil dann Boden und Decke exakt gleich viel Bildfläche bekommen,
    unabhängig von Brennweite und Abstand (nachgerechnet 21.08.2026). Gemessen ab
    ``z_unten_m``, dem Bezugspunkt, den der Raumleser mitliefert.

    Fehlt die Höhe, gibt es **keine** Ersatzhöhe. ``kameras.AUGENHOEHE_M`` (1,70 m)
    einzusetzen wäre bequem und falsch: In einem 2,55-m-Raum erzeugt sie 28 Prozentpunkte
    Ungleichgewicht zwischen Boden und Decke und liegt ausserhalb dessen, was die
    Innenraumfotografie überhaupt nennt.
    """
    hoehe = raum.get("hoehe_m")
    z_unten = raum.get("z_unten_m")
    if hoehe is None or z_unten is None:
        return None, (
            "Keine Kamerahöhe: Die Raumhöhe oder ihr Bezugspunkt fehlt "
            f"(hoehe_m={hoehe!r}, z_unten_m={z_unten!r}). Eine Ersatzhöhe wäre geraten — "
            f"und die Augenhöhe der Aussenaufnahme (1,70 m) ist in einem gewöhnlichen "
            f"Wohnraum nachweislich falsch.")
    if hoehe <= 0:
        return None, f"Die Raumhöhe ist {hoehe} m — daraus lässt sich nichts rechnen."
    return float(z_unten) + float(hoehe) / 2.0, ""


def frontaler_standpunkt(raum: dict, *,
                         wandabstand_m: float = WANDABSTAND_INNEN_M,
                         brennweite_mm: float = BRENNWEITE_INNEN_MM,
                         seitenverhaeltnis: float = 1.6) -> dict:
    """Frontal auf eine Wand, Kamera waagrecht, Fluchtpunkt mittig.

    Die einzige **belegte** Positionskonvention des Innenraums ist der mittige
    Fluchtpunkt bei der frontalen Aufnahme — und die Bedingung dafür ist im Renderer
    trivial: Kamera auf der Mittelachse, senkrecht zur Wand, ohne Neigung und ohne Rollen.
    Was einen Fotografen im wirklichen Raum zehn bis fünfzehn Minuten kostet, ist hier ein
    Zahlenwert.

    **Welche Wand, ist eine Setzung** (:data:`ZIELWAND_REGEL`) und steht im Befund.
    """
    roh = _als_polygon(raum.get("grundriss_m"))
    polygon = _gegen_uhrzeigersinn(roh)
    z, hoehen_grund = _kamerahoehe(raum)
    antwort = {"art": ART_FRONTAL, "auge": None, "blick_auf": None,
               "zielwand": None, "abstand_m": None, "sichtfeld": None,
               "befund": "", "hinweise": []}
    if z is None:
        antwort["befund"] = hoehen_grund
        return antwort

    kanten = sorted(_kanten(polygon), key=lambda k: k[2], reverse=True)
    for a, b, laenge, normale in kanten:
        mitte = ((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0)
        lauf = _lauf_nach_innen(mitte, normale, polygon, abstand=wandabstand_m)
        if lauf is None:
            continue
        _t_min, t_max = lauf
        antwort.update(
            auge=(mitte[0] + normale[0] * t_max, mitte[1] + normale[1] * t_max, z),
            # Blickziel auf KAMERAHÖHE — die Bildebene bleibt lotrecht, die Vertikalen
            # parallel. Ein Ziel darüber wäre der Fehler aus `kameras.py`.
            blick_auf=(mitte[0], mitte[1], z),
            zielwand={"von": list(a), "bis": list(b), "laenge_m": round(laenge, 4)},
            abstand_m=round(t_max, 4),
            sichtfeld=_sichtfeld(t_max, laenge, brennweite_mm=brennweite_mm,
                                 seitenverhaeltnis=seitenverhaeltnis))
        antwort["hinweise"].append(
            f"Zielwand nach Regel {ZIELWAND_REGEL!r} gewählt ({laenge:.2f} m, die "
            f"längste). Die Praxis wählt die Wand mit dem MOTIV — ein Motiv steht in "
            f"keiner IFC-Datei. Diese Wahl ist eine Setzung dieses Projekts.")
        return antwort

    antwort["befund"] = (
        f"Keine Wand hat einen Standpunkt mit {wandabstand_m:.2f} m Abstand. Der Raum ist "
        f"zu eng. Die Fotografie geht hier weiter — Türöffnung, Nachbarraum, weitwinkliger, "
        f"und zuletzt einen Teilausschnitt zeigen. Dieses Modul kann das nicht und sagt es, "
        f"statt einen Standpunkt zu erfinden.")
    return antwort


def eck_standpunkt(raum: dict, *, wandabstand_m: float = WANDABSTAND_INNEN_M,
                   brennweite_mm: float = BRENNWEITE_INNEN_MM,
                   seitenverhaeltnis: float = 1.6) -> dict:
    """Über Eck aus einer Raumecke — Zweipunktperspektive.

    Genommen wird die **vorspringende** Ecke, von der aus der längste Blick durch den Raum
    geht. Einspringende Ecken werden übergangen: Dort zeigt die Winkelhalbierende nach
    aussen, und eine Kamera dort sähe weniger statt mehr.
    """
    roh = _als_polygon(raum.get("grundriss_m"))
    polygon = _gegen_uhrzeigersinn(roh)
    z, hoehen_grund = _kamerahoehe(raum)
    antwort = {"art": ART_UEBER_ECK, "auge": None, "blick_auf": None,
               "ecke": None, "sichtweite_m": None, "sichtfeld": None,
               "befund": "", "hinweise": []}
    if z is None:
        antwort["befund"] = hoehen_grund
        return antwort

    n = len(polygon)
    bester = None
    for i in range(n):
        vor, hier, nach = polygon[i - 1], polygon[i], polygon[(i + 1) % n]
        ein = (hier[0] - vor[0], hier[1] - vor[1])
        aus = (nach[0] - hier[0], nach[1] - hier[1])
        # KEIN Wächter gegen einspringende Ecken — sie schliessen sich selbst aus.
        #
        # Hier stand zuerst eine Abfrage auf das Kreuzprodukt. Die Mutationsprobe hat sie
        # überlebt, und die Nachprüfung zeigt warum: An einer einspringenden Ecke ist der
        # Innenwinkel grösser als 180°, die Summe unten halbiert darum den ÄUSSEREN Winkel
        # und zeigt nach aussen. `_lauf_nach_innen` findet von dort keinen einzigen
        # gültigen Punkt und liefert `None`. Am L-förmigen Testraum nachgemessen: fünf
        # vorspringende Ecken mit Lauf, die einspringende ohne.
        #
        # Ein Wächter, der nie greift, ist eine tote Kante — auch dann, wenn er richtig
        # gedacht ist. Die Tatsache steht jetzt als Test statt als Code.
        r1 = math.hypot(*ein) or 1.0
        r2 = math.hypot(*aus) or 1.0
        # Ins Innere zeigt die Summe aus „zurück zur vorigen Ecke" und „vor zur nächsten".
        bx = (-ein[0] / r1) + (aus[0] / r2)
        by = (-ein[1] / r1) + (aus[1] / r2)
        laenge = math.hypot(bx, by)
        if laenge <= 1e-9:
            continue          # gestreckte Ecke — keine Ecke
        richtung = (bx / laenge, by / laenge)
        lauf = _lauf_nach_innen(hier, richtung, polygon, abstand=wandabstand_m)
        if lauf is None:
            continue
        t_min, t_max = lauf
        if bester is None or (t_max - t_min) > bester[0]:
            bester = (t_max - t_min, hier, richtung, t_min, t_max)

    if bester is None:
        antwort["befund"] = (
            f"Keine vorspringende Ecke bietet einen Standpunkt mit {wandabstand_m:.2f} m "
            f"Abstand. Der Raum ist zu eng für eine Über-Eck-Aufnahme.")
        return antwort

    sicht, ecke, richtung, t_min, t_max = bester
    antwort.update(
        # So weit in die Ecke wie erlaubt: Von dort sieht man am meisten vom Raum.
        auge=(ecke[0] + richtung[0] * t_min, ecke[1] + richtung[1] * t_min, z),
        blick_auf=(ecke[0] + richtung[0] * t_max, ecke[1] + richtung[1] * t_max, z),
        ecke=list(ecke), sichtweite_m=round(sicht, 4),
        # Über Eck gibt es keine Wand, die ganz ins Bild soll — `passt` bleibt darum
        # ausdrücklich NICHT GEMESSEN statt stillschweigend „ja".
        sichtfeld=_sichtfeld(t_max - t_min, None, brennweite_mm=brennweite_mm,
                             seitenverhaeltnis=seitenverhaeltnis))
    antwort["hinweise"].append(
        "Blick diagonal durch den Raum, Kamera waagrecht. Welche Ecke die richtige ist, "
        "hängt in der Praxis am Motiv — hier gewählt wurde die mit der längsten Sicht.")
    return antwort


def standpunkte(raum: dict, *, wandabstand_m: float = WANDABSTAND_INNEN_M,
                brennweite_mm: float = BRENNWEITE_INNEN_MM,
                seitenverhaeltnis: float = 1.6) -> dict:
    """**Beide** Blickarten für einen Raum — gewählt wird anderswo.

    Owner-Entscheid vom 22.08.2026. Der Grund steht im Modulkopf: Ob frontal oder über
    Eck richtig ist, hängt daran, ob die Stirnwand ein Motiv trägt, und das steht in
    keiner IFC-Datei. Ein Programm, das hier entscheidet, tut so, als wüsste es etwas, das
    es nicht wissen kann.

    Returns:
        ``{raum, standpunkte, n_brauchbar, befund}``. ``standpunkte`` enthält **immer**
        beide Einträge — auch die unbrauchbaren, mit ihrem Befund. Einen wegzulassen
        hiesse, den Unterschied zwischen *ging nicht* und *wurde nicht versucht* zu
        verwischen.
    """
    args = {"wandabstand_m": wandabstand_m, "brennweite_mm": brennweite_mm,
            "seitenverhaeltnis": seitenverhaeltnis}
    beide = [frontaler_standpunkt(raum, **args), eck_standpunkt(raum, **args)]
    brauchbar = [s for s in beide if s["auge"] is not None]
    return {
        "raum": raum.get("name") or raum.get("global_id"),
        "standpunkte": beide,
        "n_brauchbar": len(brauchbar),
        "befund": "" if brauchbar else (
            "Kein einziger Standpunkt. " + (beide[0]["befund"] or beide[1]["befund"])),
    }




# --------------------------------------------------------------------------------------
# Auswahl — welcher Raum, welche Blickart
# --------------------------------------------------------------------------------------
#
# **Wie viele Räume eines Gebäudes gerendert werden, ist eine Betriebsfrage.** Dieses
# Projekt hat sie für die Aussenansicht schon einmal beantwortet: ``abholer.AUTO_RICHTUNGEN``
# kennt **eine** Richtung, nicht zwölf, mit der Begründung, dass zwölf Standpunkte zwölf
# Renderläufe sind und das eine Entscheidung des Betriebs ist.
#
# Innen ist die Vorgabe darum **keine**: Standpunkte werden gerechnet (das kostet nichts)
# und berichtet, gerendert wird nur, was ausdrücklich verlangt ist. Ein Auftrag, der nicht
# nach Innenansichten gefragt hat, soll nicht stillschweigend ein Dutzend Renderläufe
# auslösen.


def waehle(raeume_ausgabe: dict | None, *, raum: str | None = None,
           art: str = ART_FRONTAL) -> dict:
    """Einen bestimmten Standpunkt aus der Raumliste holen.

    Args:
        raeume_ausgabe: die Ausgabe von ``kette._raeume_lesen``, oder ``None``.
        raum: Name oder ``global_id``. ``None`` heisst **der erste Raum mit einem
            brauchbaren Standpunkt** — nicht „irgendeiner": Ein Raum ohne Standpunkt zu
            wählen und dann zu scheitern, wäre eine Auswahl, die keine ist.
        art: :data:`ART_FRONTAL` oder :data:`ART_UEBER_ECK`.

    Returns:
        ``{gefunden, standpunkt, raum, grund}``. ``gefunden`` ist ``False`` mit einem
        Grund, wenn es den Raum nicht gibt, die Blickart dort nicht geht, oder gar keine
        Räume vorliegen.

    **Es wird nicht ausgewichen.** Wer frontal verlangt und frontal nicht bekommt,
    bekommt einen Befund und nicht die Über-Eck-Ansicht. Ein stiller Ersatz wäre ein
    anderes Bild als das bestellte — und niemand sähe es dem Ergebnis an.
    """
    if art not in (ART_FRONTAL, ART_UEBER_ECK):
        raise RaumkameraError(
            f"art ist {art!r}; erlaubt sind {ART_FRONTAL!r} und {ART_UEBER_ECK!r}.")
    leer = {"gefunden": False, "standpunkt": None, "raum": None, "grund": ""}
    if not raeume_ausgabe or not raeume_ausgabe.get("raeume"):
        return dict(leer, grund=(
            "Keine Räume. Entweder wurde über eine glb eingestiegen — dann gibt es keinen "
            "Raumbegriff — oder der Raumleser hat nichts gefunden. Beides ist NICHT "
            "GEMESSEN und nicht 'dieses Gebäude hat keine Räume'."))

    eintraege = raeume_ausgabe["raeume"]
    if raum is not None:
        eintraege = [e for e in eintraege
                     if raum in (e["raum"].get("name"), e["raum"].get("global_id"))]
        if not eintraege:
            vorhanden = [e["raum"].get("name") for e in raeume_ausgabe["raeume"]]
            return dict(leer, grund=(
                f"Kein Raum namens {raum!r}. Vorhanden: {vorhanden}. Es wird NICHT auf "
                f"einen anderen ausgewichen — ein stiller Ersatz wäre ein anderes Bild "
                f"als das bestellte."))

    for eintrag in eintraege:
        for s in eintrag["kamera"]["standpunkte"]:
            if s["art"] == art and s["auge"] is not None:
                return {"gefunden": True, "standpunkt": s,
                        "raum": eintrag["raum"].get("name"), "grund": ""}

    namen = [e["raum"].get("name") for e in eintraege]
    gruende = [s["befund"] for e in eintraege for s in e["kamera"]["standpunkte"]
               if s["art"] == art and s["befund"]]
    return dict(leer, grund=(
        f"Blickart {art!r} ist in {namen} nicht möglich. "
        + (gruende[0] if gruende else "Ohne näheren Grund.")))
