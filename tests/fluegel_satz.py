"""Der synthetische Satz «Flügel bleiben ein Haus» (A0301) und sein Erzeuger.

**Wozu:** ``umfeld.grundriss_cluster`` fasst Bauteile zu Bauten zusammen. Steht eine Anlage auf einer
grossen Geländeplatte, hing bis zu diesem Auftrag alles über diese Platte zusammen, der Haufen wuchs
über die Flächengrenze und wurde nach *gleichem Grundriss* zerlegt: ein Haus aus Flügeln (verschiedene
Grundrisse) zerfiel in seine Flügel. Dieser Satz misst das, und er misst die Gegenrichtung: zwei
getrennte Häuser dürfen nicht verschmelzen.

**Regel 3:** frei erfunden, keine Projektdaten. Alles entsteht aus den Zahlen in dieser Datei
(:func:`faelle`), ohne Zufall, ohne Datei, ohne Netz.

**Was ein Fall ist:** eine Liste Boxen ``((x0, y0, z0), (x1, y1, z1))`` (Welt, Z oben, Meter) und je
Box, zu welchem Haus sie gehört (``haus``: 0, 1, … oder ``None`` für Gelände, Hof und Belag, die zu
keinem Haus gehören). **Richtig gruppiert** heisst: Die Gruppen, die Hausteile enthalten, sind genau
die Häuser; kein Geländeteil steckt in einer Hausgruppe; jede Hausgruppe gilt als Bau.
**Falsche Verschmelzung** heisst: Eine Gruppe enthält Teile von zwei Häusern.

**Runde 2 (nach dem ersten Gegenlesen):** Der Satz enthält drei Herkünfte (Feld ``herkunft``):
``runde1`` (die 66 Fälle des ersten Baus), ``gegenlesen`` (die 44 Fälle, an denen das Gegenlesen die
erste Lösung widerlegt hat, hier nach seiner Meldung nachgebaut) und ``reihe`` (Reihen, die jede
Schwelle der Regel von beiden Seiten dicht besetzen: Deckung, Sockelhöhe, Plattendicke, Überstand,
Abstand, Bodengrösse).

**Mehrdeutig** (Feld ``mehrdeutig``): Wo dieselben Körper zwei Wahrheiten haben können (zwei Häuser
auf einer gemeinsamen Platte gegen zwei Teile eines Hauses auf seiner Bodenplatte; ein Haus auf einem
Vorplatz gegen ein Haus mit Bodenplatte), kann keine Regel aus der Geometrie allein richtig liegen.
Solche Fälle stehen als Paare im Satz (gleiche Boxen, zwei Lesarten in ``haus``). Verlangt ist dort
nicht «richtig», sondern: Die Funktion setzt den Vermerk ``mehrdeutig`` und gruppiert nicht schlechter
als die Basis (:mod:`fluegel_basis`). Entscheidbare Fälle müssen richtig sein und tragen keinen Vermerk.

Die Messung selbst steht in :func:`miss`; die Probe dazu in ``tests/test_fluegel_gruppierung.py``.
"""
from __future__ import annotations

import math

#: Die Bauweisen eines Flügels: ein Körper, eine 2-m-Grundrissplatte (wie in einem Situationsmodell aus
#: Platten) oder Geschossdecken übereinander (gleicher Grundriss, 3,5 m Abstand).
BAUWEISEN = ("koerper", "platten", "decken")

#: Rechtecke ``(x0, y0, x1, y1)`` der Flügel je Form. Die Flügel überlappen sich an den Gelenken um die
#: volle Flügeltiefe (so entstehen sie, wenn man Baukörper ineinander schiebt).
FORMEN = {
    "L": ((0, 0, 32, 12), (0, 0, 12, 28)),
    "U": ((0, 0, 44, 12), (0, 0, 12, 30), (32, 0, 44, 30)),
    "H": ((0, 0, 12, 40), (32, 0, 44, 40), (6, 14, 38, 26)),
    "Kamm": ((0, 0, 62, 12), (0, 4, 10, 34), (17, 4, 27, 34), (35, 4, 45, 34), (52, 4, 62, 34)),
}

#: Zweite Massreihe (kurze Schenkel, die zu mehr als der Hälfte im Nachbarflügel stecken; schmale Flügel).
FORMEN_KURZ = {
    "L": ((0, 0, 40, 14), (0, 0, 14, 22)),
    "U": ((0, 0, 60, 12), (0, 0, 12, 20), (48, 0, 60, 20)),
    "H": ((0, 0, 10, 30), (24, 0, 34, 30), (8, 11, 26, 19)),
    "Kamm": ((0, 0, 50, 10), (2, 0, 12, 18), (38, 0, 48, 18)),
}


def _fluegel(rechteck, bauweise: str, versatz=(0.0, 0.0)) -> list:
    """Die Boxen eines Flügels in der Bauweise."""
    x0, y0, x1, y1 = (float(v) for v in rechteck)
    x0, x1 = x0 + versatz[0], x1 + versatz[0]
    y0, y1 = y0 + versatz[1], y1 + versatz[1]
    if bauweise == "koerper":
        return [((x0, y0, 0.0), (x1, y1, 10.5))]
    if bauweise == "platten":
        return [((x0, y0, 0.0), (x1, y1, 2.0))]
    if bauweise == "decken":
        return [((x0, y0, 3.5 * g), (x1, y1, 3.5 * g + 0.3)) for g in range(4)]
    raise ValueError(bauweise)


def _haus(rechtecke, bauweise, versatz=(0.0, 0.0)) -> list:
    return [b for r in rechtecke for b in _fluegel(r, bauweise, versatz)]


def _gelaendeplatte(dick=2.0) -> list:
    """Eine Platte, auf der die Anlage steht: 400 × 400 m, also weit über der Flächengrenze für einen Bau."""
    return [((-150.0, -150.0, 0.0), (250.0, 250.0, dick))]


def _fall(name, gruppe, teile, gegenfall=False, *, mehrdeutig=False, herkunft="reihe") -> dict:
    """``teile``: Liste ``(haus, [boxen])``. Flacht sie zu ``boxen`` und ``haus`` (je Box) ab."""
    boxen, haus = [], []
    for nummer, liste in teile:
        for b in liste:
            boxen.append(b)
            haus.append(nummer)
    return {"name": name, "gruppe": gruppe, "boxen": boxen, "haus": haus, "gegenfall": gegenfall,
            "mehrdeutig": mehrdeutig, "herkunft": herkunft}


#: Fälle der ersten Runde, die dieselben Körper haben wie ein Fall mit der anderen Wahrheit (Teile auf einer
#: Bodenplatte gegen Häuser auf einem Belag; ein Bau auf einer Platte, die selbst als Bau gelten kann).
MEHRDEUTIG_RUNDE1 = ("bodenplatte-", "zwei-haeuser-hofbelag-", "haus-nebenbau-hofbelag-", "L-und-nachbar-plattenkette")

#: Der Blockrand: vier Flügel um einen Hof (12 bis 38 m, 12 bis 28 m).
BLOCKRAND = ((0, 0, 50, 12), (0, 0, 12, 40), (38, 0, 50, 40), (0, 28, 50, 40))


def _huelle(rechteck, grad: float):
    """Der achsparallele Hüllquader eines um den Ursprung gedrehten Rechtecks: So bekommt die Gruppierung
    einen gedrehten Flügel zu sehen."""
    x0, y0, x1, y1 = rechteck
    w = math.radians(grad)
    c, s = math.cos(w), math.sin(w)
    p = [(x * c - y * s, x * s + y * c) for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1))]
    return (round(min(a for a, _ in p), 3), round(min(b for _, b in p), 3),
            round(max(a for a, _ in p), 3), round(max(b for _, b in p), 3))


def _platte_um(breite: float, tiefe: float, belegt_m2: float, deckung: float, dick: float) -> list:
    """Eine Platte mit gleichem Rand rundum um ein Feld ``breite`` × ``tiefe`` (bei 0,0), so gross, dass
    ``belegt_m2`` genau den Anteil ``deckung`` von ihr ausmacht."""
    ziel = belegt_m2 / deckung
    rand = (-(breite + tiefe) + math.sqrt((breite + tiefe) ** 2 - 4 * (breite * tiefe - ziel))) / 4
    assert rand >= 0, (breite, tiefe, deckung)
    return [((-rand, -rand, 0.0), (breite + rand, tiefe + rand, dick))]


def _koerper(x0, y0, x1, y1, z0, z1) -> list:
    return [((float(x0), float(y0), float(z0)), (float(x1), float(y1), float(z1)))]


def _lagen(name, gruppe, teile, **kw) -> list:
    """Derselbe Fall frei und auf der Geländeplatte."""
    return [_fall(f"{name}-frei", gruppe, teile, **kw),
            _fall(f"{name}-gelaende", gruppe, [(None, _gelaendeplatte())] + teile, **kw)]


def _faelle_gegenlesen() -> list:
    """Die 44 Fälle des ersten Gegenlesens (Meldung G-A0301 vom 10.11.2026), nach ihrem Text nachgebaut.
    In Klammern steht je, was das Gegenlesen gemessen hat (Basis / erste Lösung)."""
    g = dict(herkunft="gegenlesen")
    aus = []
    # Blockrand in drei Bauweisen: auf der Geländeplatte (falsch / richtig) und frei (richtig / richtig).
    for bauweise in BAUWEISEN:
        aus += _lagen(f"blockrand-{bauweise}", "fluegel", [(0, _haus(BLOCKRAND, bauweise))], **g)
    # Blockrand mit Innenhofbelag, der die Flügel nur berührt (richtig / richtig).
    aus.append(_fall("blockrand-innenhofbelag-frei", "fluegel",
                     [(0, _haus(BLOCKRAND, "koerper")), (None, _koerper(12, 12, 38, 28, 0, 0.1))], **g))
    # L, U und Kamm um 30 und 45 Grad gedreht, je Flügel sein Hüllquader: auf der Geländeplatte in Platten und
    # Körpern (falsch / richtig), frei in Platten (richtig / richtig).
    for form in ("L", "U", "Kamm"):
        for grad in (30, 45):
            huellen = [_huelle(r, grad) for r in FORMEN[form]]
            for bauweise in ("platten", "koerper"):
                aus.append(_fall(f"{form}-gedreht{grad}-{bauweise}-gelaende", "fluegel",
                                 [(None, _gelaendeplatte()), (0, _haus(huellen, bauweise))], **g))
            aus.append(_fall(f"{form}-gedreht{grad}-platten-frei", "fluegel", [(0, _haus(huellen, "platten"))], **g))
    # Zwei Häuser 2 m auseinander auf einer gemeinsamen 0,3-m-Platte, Deckung 0,48 / 0,52 / 0,71; dieselben
    # Körper als EIN Haus aus zwei Teilen auf seiner Bodenplatte (Deckung 0,48 und 0,40).
    def paar(deckung, abstand=2.0, dick=0.3):
        platte = _platte_um(24 + abstand, 10, 240.0, deckung, dick)
        return platte, _koerper(0, 0, 12, 10, dick, 9) + _koerper(12 + abstand, 0, 24 + abstand, 10, dick, 9)
    m = dict(mehrdeutig=True, herkunft="gegenlesen")
    for deckung in (0.48, 0.52, 0.71):
        platte, (h0, h1) = paar(deckung)
        aus += _lagen(f"zwei-haeuser-platte-deckung{deckung:g}", "paar", [(None, platte), (0, [h0]), (1, [h1])],
                      gegenfall=True, **m)
    for deckung in (0.48, 0.40):
        platte, haeuser = paar(deckung)
        aus.append(_fall(f"ein-haus-bodenplatte-deckung{deckung:g}-frei", "paar", [(0, platte + haeuser)], **m))
    # Sockel 60 × 40 m, 2 m hoch, mit zwei Türmen 15 × 15 m (frei: richtig / falsch; Gelände: falsch / falsch).
    sockel = _koerper(0, 0, 60, 40, 0, 2) + _koerper(8, 12, 23, 27, 2, 30) + _koerper(37, 12, 52, 27, 2, 30)
    aus += _lagen("sockel-zwei-tuerme", "paar", [(0, sockel)], **m)
    # Plattenmodell: Erdgeschossplatte 40 × 30 m mit zwei Obergeschossplatten darauf (richtig / falsch).
    eg = _koerper(0, 0, 40, 30, 0, 3) + _koerper(4, 10, 16, 20, 3, 6) + _koerper(24, 10, 36, 20, 3, 6)
    aus.append(_fall("eg-platte-zwei-og-platten-frei", "paar", [(0, eg)], **m))
    # Haus und Garage auf grossem Vorplatz (falsch / richtig) und auf knappem Vorplatz (falsch / falsch).
    haus_garage = [(0, _koerper(0, 0, 12, 9, 0.1, 9)), (1, _koerper(14, 2, 17.5, 7, 0.1, 2.9))]
    aus.append(_fall("haus-garage-vorplatz-gross-frei", "paar",
                     [(None, _koerper(-8, -8, 26, 17, 0, 0.1))] + haus_garage, gegenfall=True, **m))
    aus.append(_fall("haus-garage-vorplatz-knapp-frei", "paar",
                     [(None, _koerper(-0.5, -0.5, 18, 9.5, 0, 0.1))] + haus_garage, gegenfall=True, **m))
    # Fünf Reihenhäuser 6 × 10 m, Wand an Wand: ohne Decke (richtig / richtig) und auf gemeinsamer
    # 0,5-m-Tiefgaragendecke (frei: falsch / falsch; Gelände: richtig / falsch).
    reihe = [(k, _koerper(6 * k, 0, 6 * k + 6, 10, 0.5, 9)) for k in range(5)]
    aus.append(_fall("reihenhaeuser-ohne-decke-frei", "gegenfall", reihe, gegenfall=True, **g))
    aus += _lagen("reihenhaeuser-tiefgaragendecke", "paar", [(None, _koerper(-2, -2, 32, 12, 0, 0.5))] + reihe,
                  gegenfall=True, **m)
    # Hofbelag 44 × 30 m, zwei Häuser 12 × 10 m, 18 m auseinander, eines ragt 6 m über den Rand
    # (frei: falsch / falsch; Gelände: richtig / falsch).
    ragt = [(None, _koerper(0, 0, 44, 30, 0, 0.1)), (0, _koerper(8, 10, 20, 20, 0, 9)),
            (1, _koerper(38, 10, 50, 20, 0, 9))]
    aus += _lagen("haus-ragt-ueber-hofbelag", "paar", ragt, gegenfall=True, **m)
    # Drei Häuser auf einem Hofbelag, Deckung 0,64 (falsch / falsch).
    drei = [(k, _koerper(14 * k, 0, 14 * k + 12, 10, 0.3, 9)) for k in range(3)]
    aus.append(_fall("drei-haeuser-hofbelag-deckung0.64-frei", "paar",
                     [(None, _platte_um(40, 10, 360.0, 0.64, 0.3))] + drei, gegenfall=True, **m))
    assert len(aus) == 44, len(aus)
    return aus


#: Die Stufen der Reihen. Jede Schwelle der Regel liegt zwischen zwei eng benachbarten Stufen.
REIHE_DECKUNG = tuple(round(0.15 + 0.05 * k, 2) for k in range(17))                 # 0,15 bis 0,95
REIHE_SOCKELHOEHE = (0.2, 0.5, 0.9, 0.99, 1.0, 1.01, 1.5, 2.0, 2.9, 3.0, 3.01, 3.5, 4.5, 6.0)
REIHE_ANTEIL = (0.5, 0.6, 0.7, 0.8, 0.85, 0.89, 0.9, 0.91, 0.95, 1.0)              # um TRAEGER_ANTEIL
REIHE_ABSTAND = (-3.0, -1.0, -0.5, -0.1, -0.02, -0.011, -0.009, -0.005, 0.0, 0.01, 0.1, 0.5, 1.0, 2.0)
REIHE_UEBERRAGT = (-1.0, -0.5, 0.0, 0.5, 0.9, 0.99, 1.0, 1.01, 1.5, 4.0, 10.0)             # um bau_min_hoehe_m
REIHE_BODEN = (100.0, 140.0, 141.0, 141.4, 141.5, 142.0, 150.0, 400.0)             # Seite; 141,42² = 20 000


def _faelle_reihen() -> list:
    """Reihen quer über jede Schwelle der Regel, in kleinen Schritten von beiden Seiten."""
    aus = []
    m = dict(mehrdeutig=True)
    # ---- Deckung: zwei Körper 12 × 10 m, 1 m auseinander, auf einer 0,3-m-Platte. Dieselben Boxen in zwei
    # Lesarten (zwei Häuser auf einem Belag / ein Haus auf seiner Bodenplatte), frei und auf Geländeplatte.
    # Die Regel hat hier KEINE Schwelle: Jede Stufe ist mehrdeutig und wird wie an der Basis gruppiert.
    for deckung in REIHE_DECKUNG:
        platte = _platte_um(25, 10, 240.0, deckung, 0.3)
        h0, h1 = _koerper(0, 0, 12, 10, 0.3, 9), _koerper(13, 0, 25, 10, 0.3, 9)
        aus += _lagen(f"deckung{deckung:.2f}-zwei-haeuser", "paar", [(None, platte), (0, h0), (1, h1)],
                      gegenfall=True, **m)
        aus += _lagen(f"deckung{deckung:.2f}-ein-haus", "paar", [(0, platte + h0 + h1)], **m)
    # ---- Sockelhöhe: Sockel 40 × 20 m mit zwei Türmen 10 × 10 m, die ganz auf ihm stehen. Auch hier keine
    # Schwelle: ob Sockel mit Türmen oder Platte mit Häusern, sagt die Höhe nicht.
    for hoehe in REIHE_SOCKELHOEHE:
        sockel = _koerper(0, 0, 40, 20, 0, hoehe)
        t0, t1 = _koerper(4, 5, 14, 15, hoehe, hoehe + 20), _koerper(26, 5, 36, 15, hoehe, hoehe + 20)
        aus += _lagen(f"sockel{hoehe:g}m-ein-haus", "paar", [(0, sockel + t0 + t1)], **m)
        aus += _lagen(f"sockel{hoehe:g}m-zwei-haeuser", "paar", [(None, sockel), (0, t0), (1, t1)],
                      gegenfall=True, **m)
    # ---- Überstand (TRAEGER_ANTEIL): eine 2-m-Platte 40 × 20 m und ein 2-m-Flügel 20 × 10 m, von dem der
    # Anteil ``a`` in der Platte liegt. Unter 0,9 durchdringt er sie (ein Bau, entscheidbar); ab 0,9 steht
    # er auf ihr (mehrdeutig: Aufbau eines Hauses oder Haus auf einer Platte).
    for anteil in REIHE_ANTEIL:
        x0 = 40.0 - 20.0 * anteil
        teile = [(0, _koerper(0, 0, 40, 20, 0, 2) + _koerper(x0, 5, x0 + 20, 15, 0, 2))]
        aus += _lagen(f"ueberstand-anteil{anteil:.2f}-platten", "fluegel" if anteil < 0.9 else "paar", teile,
                      mehrdeutig=anteil >= 0.9)
    # ---- Körper über einer grösseren flachen Platte: ein Haus 12 × 10 × 9 m ragt 0 bis 9 m über den Rand einer
    # 2-m-Platte 44 × 30 m. Es wird getragen, wie weit es auch ragt (mehrdeutig, Lesart: Haus auf Platte).
    for ragt in (0.0, 1.0, 3.0, 6.0, 9.0):
        teile = [(None, _koerper(0, 0, 44, 30, 0, 2)), (0, _koerper(32 + ragt, 10, 44 + ragt, 20, 0, 9))]
        aus += _lagen(f"koerper-ragt{ragt:g}m-ueber-2m-platte", "paar", teile, **m)
    # ---- Plattenhöhe unter einem Körper, der zur Hälfte hinausragt (FLACH_MAX_M): bis 3 m trägt die Platte
    # (mehrdeutig); darüber ist sie selbst ein Baukörper, den das Haus durchdringt (ein Bau).
    for hoehe in REIHE_SOCKELHOEHE:
        boxen = _koerper(0, 0, 44, 30, 0, hoehe) + _koerper(38, 10, 50, 20, 0, 12)
        if hoehe > 3.0:
            aus.append(_fall(f"koerper-halb-ueber-platte{hoehe:g}m-gelaende", "fluegel",
                             [(None, _gelaendeplatte()), (0, boxen)]))
        else:
            aus.append(_fall(f"koerper-halb-ueber-platte{hoehe:g}m-gelaende", "paar",
                             [(None, _gelaendeplatte()), (None, boxen[:1]), (0, boxen[1:])], **m))
    # ---- Plattendicke unter einem 2-m-Flügel, der zur Hälfte hinausragt (bau_min_hoehe_m, zweimal): unter 1 m
    # ist die Platte ein Belag und bindet nicht; bis genau 1 m überragt der Flügel sie um eine Bauhöhe und wird
    # getragen (beides mehrdeutig). Darüber durchdringen sich zwei etwa gleich hohe Baukörper (ein Bau).
    for dick in REIHE_SOCKELHOEHE:
        boxen = _koerper(0, 0, 44, 30, 0, dick) + _koerper(38, 10, 50, 20, 0, 2)
        if dick > 1.0:
            aus.append(_fall(f"fluegel-halb-ueber-platte{dick:g}m-gelaende", "fluegel",
                             [(None, _gelaendeplatte()), (0, boxen)]))
        else:
            aus.append(_fall(f"fluegel-halb-ueber-platte{dick:g}m-gelaende", "paar",
                             [(None, _gelaendeplatte()), (None, boxen[:1]), (0, boxen[1:])], **m))
    # ---- Überragen (bau_min_hoehe_m über einer flachen Platte): eine 2-m-Platte 44 × 30 m und ein Teil 12 × 10 m,
    # das zur Hälfte hinausragt und sie um ``mehr`` überragt. Unter einer Bauhöhe (1 m) Unterschied sind es zwei
    # Platten, die sich durchdringen (ein Bau); ab 1 m steht ein Haus über dem Rand einer Platte (mehrdeutig).
    for mehr in REIHE_UEBERRAGT:
        boxen = _koerper(0, 0, 44, 30, 0, 2) + _koerper(38, 10, 50, 20, 0, 2 + mehr)
        if mehr < 1.0:
            aus.append(_fall(f"ueberragt{mehr:g}m-2m-platte-gelaende", "fluegel", [(None, _gelaendeplatte()), (0, boxen)]))
        else:
            aus.append(_fall(f"ueberragt{mehr:g}m-2m-platte-gelaende", "paar",
                             [(None, _gelaendeplatte()), (None, boxen[:1]), (0, boxen[1:])], **m))
    # ---- Verbindungsgang nach Höhe: ab 1 m bindet er (ein Bau); darunter ist er ein Belag zwischen zwei
    # Körpern (mehrdeutig: Passerelle eines Hauses oder Weg zwischen zwei Häusern).
    for hoehe in (0.3, 0.9, 0.99, 1.0, 1.01, 2.0, 3.0, 3.5):
        boxen = _koerper(0, 0, 14, 12, 0, 10.5) + _koerper(13, 4.5, 23, 7.5, 0, hoehe) + _koerper(22, 0, 36, 12, 0, 10.5)
        aus.append(_fall(f"gang{hoehe:g}m-gelaende", "gang" if hoehe >= 1.0 else "paar",
                         [(None, _gelaendeplatte()), (0, boxen)], mehrdeutig=hoehe < 1.0))
    # ---- Abstand (CLUSTER_LUECKE_M): zwei Körper 12 × 10 m. Überlappen sie sich um mehr als 1 cm, sind sie ein
    # Bau (Ergebnis 359); berühren sie sich nur oder liegen auseinander, sind es zwei.
    for abstand in REIHE_ABSTAND:
        a, b = _koerper(0, 0, 12, 10, 0, 9), _koerper(12 + abstand, 2, 24 + abstand, 12, 0, 9)
        if abstand < -0.01:
            aus += _lagen(f"abstand{abstand:g}m-ein-bau", "fluegel", [(0, a + b)])
        else:
            aus += _lagen(f"abstand{abstand:g}m-zwei-haeuser", "gegenfall", [(0, a), (1, b)], gegenfall=True)
    # ---- Bodengrösse (BAU_MAX_FLAECHE_M2): ein L aus 2-m-Platten und ein Nachbarhaus auf einer quadratischen
    # 2-m-Platte. Über 20 000 m² ist sie Boden (entscheidbar: L ein Bau, Nachbar für sich); darunter kann sie
    # selbst ein Bau sein (mehrdeutig, wie an der Basis alles ein Cluster).
    for seite in REIHE_BODEN:
        platte = [((-20.0, -20.0, 0.0), (seite - 20.0, seite - 20.0, 2.0))]
        teile = [(None, platte), (0, _haus(FORMEN["L"], "platten")), (1, _fluegel((40, 0, 52, 10), "platten"))]
        aus.append(_fall(f"platte-seite{seite:g}m-L-und-nachbar", "gemischt" if seite ** 2 > 20_000 else "paar",
                         teile, gegenfall=True, mehrdeutig=seite ** 2 <= 20_000))
    # ---- Gemischt auf einer 2-m-Platte: ein Flügel steht ganz darauf, einer ragt zur Hälfte hinaus.
    teile = [(0, _koerper(0, 0, 44, 30, 0, 2) + _koerper(6, 10, 18, 20, 0, 2) + _koerper(38, 10, 50, 20, 0, 2))]
    aus += _lagen("einer-steht-einer-ragt-2m-platte", "paar", teile, **m)
    # ---- Gedrehte Formen frei auch als Körper, Reihenhäuser ohne Decke auch auf der Geländeplatte.
    for form in ("L", "U", "Kamm"):
        for grad in (30, 45):
            aus.append(_fall(f"{form}-gedreht{grad}-koerper-frei", "fluegel",
                             [(0, _haus([_huelle(r, grad) for r in FORMEN[form]], "koerper"))]))
    aus.append(_fall("reihenhaeuser-ohne-decke-gelaende", "gegenfall",
                     [(None, _gelaendeplatte())] + [(k, _koerper(6 * k, 0, 6 * k + 6, 10, 0.5, 9)) for k in range(5)],
                     gegenfall=True))
    return aus


def faelle() -> list[dict]:
    """Alle Fälle des Satzes, in fester Reihenfolge.

    Returns:
        ``[{name, gruppe, boxen, haus, gegenfall, mehrdeutig, herkunft}, …]``. ``gruppe`` ist ``"fluegel"``,
        ``"bodenplatte"``, ``"gang"``, ``"gemischt"``, ``"gegenfall"`` oder ``"paar"`` (eine von zwei
        Lesarten derselben Körper); ``gegenfall`` ist wahr, wenn der Fall mindestens zwei Häuser enthält,
        die getrennt bleiben müssen; ``mehrdeutig``, wenn die Geometrie allein nicht entscheidet.
    """
    aus = []
    # ---- 1. Flügelbauten: vier Formen, drei Bauweisen, frei und auf der Geländeplatte.
    for form, rechtecke in FORMEN.items():
        for bauweise in BAUWEISEN:
            aus.append(_fall(f"{form}-{bauweise}-frei", "fluegel", [(0, _haus(rechtecke, bauweise))]))
            aus.append(_fall(f"{form}-{bauweise}-gelaende", "fluegel",
                             [(None, _gelaendeplatte()), (0, _haus(rechtecke, bauweise))]))
    for form, rechtecke in FORMEN_KURZ.items():
        aus.append(_fall(f"{form}-kurz-platten-gelaende", "fluegel",
                         [(None, _gelaendeplatte()), (0, _haus(rechtecke, "platten", (20.0, -30.0)))]))
    # Der Bau liegt über der Naht zweier Geländeplatten (sie berühren sich, oder sie überlappen knapp).
    for naht, ueber in (("beruehrt", 0.0), ("ueberlappt", 0.5)):
        platten = [((-300.0, -200.0, 0.0), (20.0 + ueber, 200.0, 2.0)), ((20.0, -200.0, 0.0), (300.0, 200.0, 2.0))]
        aus.append(_fall(f"L-platten-naht-{naht}", "fluegel",
                         [(None, platten), (0, _haus(FORMEN["L"], "platten"))]))
    # ---- 2. Teile, die nur über eine Bodenplatte zusammenhängen (die Platte gehört zum Haus).
    sockel2 = [((0.0, 0.0, 0.0), (34.0, 14.0, 0.4))]
    zwei = [((1.0, 1.0, 0.4), (15.0, 13.0, 9.0)), ((19.0, 1.0, 0.4), (33.0, 13.0, 12.0))]
    sockel3 = [((0.0, 0.0, 0.0), (50.0, 16.0, 0.3))]
    drei = [((1.0, 1.0, 0.3), (15.0, 15.0, 7.0)), ((18.0, 2.0, 0.3), (32.0, 14.0, 10.0)),
            ((35.0, 1.0, 0.3), (49.0, 15.0, 7.0))]
    sockel_p = [((0.0, 0.0, 0.0), (30.0, 12.0, 0.3))]
    zwei_p = [((0.5, 0.5, 0.0), (13.0, 11.5, 2.0)), ((17.0, 0.5, 0.0), (29.5, 11.5, 2.0))]
    for name, sockel, teile in (("zwei-koerper", sockel2, zwei), ("drei-koerper", sockel3, drei),
                                ("zwei-platten", sockel_p, zwei_p)):
        aus.append(_fall(f"bodenplatte-{name}-frei", "bodenplatte", [(0, sockel + teile)]))
        aus.append(_fall(f"bodenplatte-{name}-gelaende", "bodenplatte",
                         [(None, _gelaendeplatte()), (0, sockel + teile)]))
    # ---- 3. Teile, die nur über einen Verbindungsgang zusammenhängen (er steckt je 1 m in beiden).
    for bauweise in ("koerper", "platten"):
        a = _fluegel((0, 0, 14, 12), bauweise)
        b = _fluegel((22, 0, 36, 12), bauweise)
        gang = [((13.0, 4.5, 0.0), (23.0, 7.5, 3.0 if bauweise == "koerper" else 2.0))]
        aus.append(_fall(f"gang-{bauweise}-frei", "gang", [(0, a + gang + b)]))
        aus.append(_fall(f"gang-{bauweise}-gelaende", "gang", [(None, _gelaendeplatte()), (0, a + gang + b)]))
    # ---- 4. Gemischt: ein Flügelbau und ein getrenntes Haus daneben. Beides muss stimmen.
    for bauweise in BAUWEISEN:
        aus.append(_fall(f"L-und-nachbar-{bauweise}-gelaende", "gemischt",
                         [(None, _gelaendeplatte()), (0, _haus(FORMEN["L"], bauweise)),
                          (1, _fluegel((35, 0, 47, 10), bauweise))], gegenfall=True))
    # Ein Haus steht im Winkel des L, 3 m von beiden Schenkeln: die Hüllen überlappen, die Grundrisse nicht.
    for lage in ("frei", "gelaende"):
        teile = [(0, _haus(FORMEN["L"], "koerper")), (1, _fluegel((15, 15, 27, 27), "koerper"))]
        aus.append(_fall(f"L-und-haus-im-winkel-{lage}", "gemischt",
                         ([(None, _gelaendeplatte())] if lage == "gelaende" else []) + teile, gegenfall=True))
    # Zwei Geländeplatten unter der Flächengrenze, die knapp überlappen (eine Kette): je ein Bau darauf.
    kette = [((-100.0, -60.0, 0.0), (20.0, 60.0, 2.0)), ((19.5, -60.0, 0.0), (139.5, 60.0, 2.0))]
    aus.append(_fall("L-und-nachbar-plattenkette", "gemischt",
                     [(None, kette), (0, _haus(FORMEN["L"], "platten", (-60.0, -20.0))),
                      (1, _fluegel((60, 0, 80, 12), "platten"))], gegenfall=True))
    # ---- 5. Gegenfälle: zwei getrennte Häuser mit kleinem Abstand; Haus neben Nebenbau.
    for bauweise in BAUWEISEN:
        for abstand in (0.0, 0.5, 2.0):            # 0: sie berühren sich nur (Ergebnis 359: zwei Bauten)
            h0 = _fluegel((0, 0, 12, 10), bauweise)
            h1 = _fluegel((12 + abstand, 0, 24 + abstand, 10), bauweise)
            if bauweise == "koerper":
                aus.append(_fall(f"zwei-haeuser-{abstand:g}m-koerper-frei", "gegenfall", [(0, h0), (1, h1)], True))
            aus.append(_fall(f"zwei-haeuser-{abstand:g}m-{bauweise}-gelaende", "gegenfall",
                             [(None, _gelaendeplatte()), (0, h0), (1, h1)], True))
    for abstand in (0.0, 1.0):
        haus = _fluegel((0, 0, 12, 9), "koerper")
        nebenbau = [((12.0 + abstand, 2.0, 0.0), (15.5 + abstand, 7.0, 2.8))]
        aus.append(_fall(f"haus-nebenbau-{abstand:g}m-frei", "gegenfall", [(0, haus), (1, nebenbau)], True))
        aus.append(_fall(f"haus-nebenbau-{abstand:g}m-gelaende", "gegenfall",
                         [(None, _gelaendeplatte()), (0, haus), (1, nebenbau)], True))
    # Zwei Häuser (und Haus mit Nebenbau) auf einem gemeinsamen Hofbelag, der viel grösser ist als sie:
    # der Belag ist kein Sockel, die Häuser bleiben zwei.
    hof = [((-8.0, -8.0, 0.0), (36.0, 22.0, 0.1))]
    paar = [(0, _fluegel((0, 0, 12, 10), "koerper")), (1, _fluegel((15, 0, 27, 10), "koerper"))]
    mit_nebenbau = [(0, _fluegel((0, 0, 12, 9), "koerper")), (1, [((14.0, 2.0, 0.0), (17.5, 7.0, 2.8))])]
    for name, teile in (("zwei-haeuser", paar), ("haus-nebenbau", mit_nebenbau)):
        aus.append(_fall(f"{name}-hofbelag-frei", "gegenfall", [(None, hof)] + teile, True))
        aus.append(_fall(f"{name}-hofbelag-gelaende", "gegenfall",
                         [(None, _gelaendeplatte(0.05)), (None, hof)] + teile, True))
    for f in aus:
        f["herkunft"] = "runde1"
        f["mehrdeutig"] = f["name"].startswith(MEHRDEUTIG_RUNDE1)
    aus += _faelle_gegenlesen() + _faelle_reihen()
    namen = [f["name"] for f in aus]
    assert len(set(namen)) == len(namen), "doppelte Fallnamen"
    return aus


def beurteile(fall: dict, cluster: list[dict]) -> dict:
    """Ein Fall gegen das Ergebnis von ``grundriss_cluster``.

    Returns:
        ``{richtig, verschmelzungen, zerlegt, grund}``. ``verschmelzungen`` zählt die Gruppen mit
        Teilen aus zwei Häusern, ``zerlegt`` die Häuser, deren Teile in mehr als einer Gruppe liegen.
    """
    haus = fall["haus"]
    soll = {}
    for i, h in enumerate(haus):
        if h is not None:
            soll.setdefault(h, set()).add(i)
    verschmelzungen, gruende = 0, []
    gruppen_je_haus: dict = {h: 0 for h in soll}
    alle = sorted(i for c in cluster for i in c["teile"])
    if alle != list(range(len(haus))):
        gruende.append("nicht jedes Teil liegt in genau einer Gruppe")
    for c in cluster:
        haeuser = {haus[i] for i in c["teile"]} - {None}
        if not haeuser:
            continue
        if len(haeuser) > 1:
            verschmelzungen += 1
            gruende.append(f"Gruppe {c['teile']} enthält die Häuser {sorted(haeuser)}")
        for h in haeuser:
            gruppen_je_haus[h] += 1
        if any(haus[i] is None for i in c["teile"]):
            gruende.append(f"Gruppe {c['teile']} enthält Gelände oder Belag")
        if not c["bau"]:
            gruende.append(f"Gruppe {c['teile']} gilt nicht als Bau ({c['art']})")
    zerlegt = sum(1 for n in gruppen_je_haus.values() if n > 1)
    if zerlegt:
        gruende.append(f"{zerlegt} Haus/Häuser in mehrere Gruppen zerlegt: {gruppen_je_haus}")
    return {"richtig": not gruende, "verschmelzungen": verschmelzungen, "zerlegt": zerlegt,
            "grund": "; ".join(gruende)}


def zufallsszene(rnd, *, flache_platten: bool, gelaendeplatte: bool) -> list:
    """Eine Zufallsszene ohne Wahrheit (nur Geometrie): 2 bis 14 Boxen auf 120 × 120 m, als Körper oder (mit
    ``flache_platten``) gemischt mit Belägen und 2-m-Platten; wahlweise auf einer Geländeplatte."""
    hoehen = (0.1, 0.3, 0.9, 1.0, 2.0, 3.0, 3.5, 6.0, 12.0) if flache_platten else (3.5, 6.0, 12.0)
    boxen = []
    for _ in range(rnd.randint(2, 14)):
        breite, tiefe = rnd.choice((4, 8, 12, 20, 40)), rnd.choice((4, 8, 12, 20, 40))
        x, y = rnd.randint(0, 160) / 2, rnd.randint(0, 160) / 2
        z0 = rnd.choice((0.0, 0.0, 0.3, 3.5))
        boxen.append(((x, y, z0), (x + breite, y + tiefe, z0 + rnd.choice(hoehen))))
    if gelaendeplatte:
        boxen.append(((-200.0, -200.0, 0.0), (300.0, 300.0, rnd.choice((0.05, 2.0)))))
    return boxen


def zufallsfall(rnd, *, gelaendeplatte: bool) -> dict:
    """Eine Zufallsszene MIT Wahrheit: 1 bis 4 Anlagen, jede in ihrem Feld (140 m Raster, sie berühren sich
    nie). Eine Anlage ist ein Flügelbau (auch gedreht, als Hüllquader), ein Haus mit Belag darunter, zwei
    Nachbarn mit kleinem Abstand, oder zwei Körper auf gemeinsamer Platte in einer der beiden Lesarten."""
    teile, naechstes = [], 0
    for feld in range(rnd.randint(1, 4)):
        ox, oy = 140.0 * (feld % 2), 140.0 * (feld // 2)

        def versetzt(boxen):
            x0, y0 = min(b[0][0] for b in boxen), min(b[0][1] for b in boxen)
            return [((b[0][0] - x0 + ox, b[0][1] - y0 + oy, b[0][2]), (b[1][0] - x0 + ox, b[1][1] - y0 + oy, b[1][2]))
                    for b in boxen]
        art = rnd.choice(("fluegel", "fluegel", "fluegel", "belag", "nachbarn", "platte", "sockel"))
        if art in ("fluegel", "belag"):
            rechtecke = rnd.choice(list(FORMEN.values()) + list(FORMEN_KURZ.values()) + [BLOCKRAND, ((0, 0, 14, 10),)])
            grad = rnd.choice((0, 0, 0, 15, 30, 45, 60))
            haus = _haus([_huelle(r, grad) for r in rechtecke] if grad else rechtecke, rnd.choice(BAUWEISEN))
            if art == "belag":
                rand = rnd.choice((-4.0, 0.5, 3.0, 10.0))
                x0, y0 = min(b[0][0] for b in haus), min(b[0][1] for b in haus)
                x1, y1 = max(b[1][0] for b in haus), max(b[1][1] for b in haus)
                alle = versetzt([((x0 - rand, y0 - rand, 0.0), (x1 + rand, y1 + rand, rnd.choice((0.1, 0.5, 0.9))))] + haus)
                teile += [(None, alle[:1]), (naechstes, alle[1:])]
            else:
                teile.append((naechstes, versetzt(haus)))
            naechstes += 1
        elif art == "nachbarn":
            abstand = rnd.choice((0.0, 0.5, 2.0))
            bauweise = rnd.choice(BAUWEISEN)
            alle = versetzt(_fluegel((0, 0, 12, 10), bauweise) + _fluegel((12 + abstand, 0, 24 + abstand, 10), bauweise))
            teile += [(naechstes, alle[:len(alle) // 2]), (naechstes + 1, alle[len(alle) // 2:])]
            naechstes += 2
        else:
            dick = rnd.choice((0.1, 0.5, 0.99, 1.0, 2.0, 3.0, 4.5)) if art == "platte" else rnd.choice((2.0, 3.0, 4.5))
            abstand = rnd.choice((1.0, 2.0, 8.0))
            ragt = rnd.choice((0.0, 0.0, 0.5, 6.0))
            hoch = rnd.choice((2.0, 9.0))
            ein_haus = rnd.random() < 0.5 or dick > 3.0       # über 3 m ist die Platte ein Geschoss, kein Belag
            if not ein_haus and dick > 1.0:                   # ein Belag ist niedriger als das Haus darauf: Eine
                hoch = 9.0                                    # Platte, so hoch wie die Platte über ihr, ist ein Flügel
            deckung = min(rnd.choice((0.2, 0.45, 0.55, 0.8)), 0.95 * 240.0 / ((24 + abstand) * 10))
            platte = _platte_um(24 + abstand, 10, 240.0, deckung, dick)
            alle = versetzt(platte + _koerper(0, 0, 12, 10, dick, dick + hoch)
                            + _koerper(12 + abstand, ragt, 24 + abstand, 10 + ragt, dick, dick + hoch))
            if ein_haus:                                      # Lesart: ein Haus auf seiner Bodenplatte
                teile.append((naechstes, alle))
                naechstes += 1
            else:                                             # Lesart: zwei Häuser auf einem Belag
                teile += [(None, alle[:1]), (naechstes, alle[1:2]), (naechstes + 1, alle[2:])]
                naechstes += 2
    if gelaendeplatte:
        teile.append((None, [((-150.0, -150.0, 0.0), (450.0, 450.0, rnd.choice((0.05, 2.0))))]))
    return _fall("zufall", "zufall", teile, gegenfall=naechstes > 1)


def gruppen_von(cluster: list[dict]) -> set:
    """Die Gruppierung als Menge von Teilemengen (zum Vergleich zweier Fassungen)."""
    return {frozenset(c["teile"]) for c in cluster}


def gemeldet(cluster: list[dict]) -> bool:
    """Trägt irgendeine Gruppe den Vermerk ``mehrdeutig``?"""
    return any(c.get("mehrdeutig") for c in cluster)


def schlechter(urteil: dict, basis: dict) -> bool:
    """Ist ein Urteil schlechter als das der Basis? (Rückschritt: vorher richtig und jetzt nicht, oder mehr
    falsche Verschmelzungen, oder mehr zerlegte Häuser.)"""
    return ((basis["richtig"] and not urteil["richtig"]) or urteil["verschmelzungen"] > basis["verschmelzungen"]
            or urteil["zerlegt"] > basis["zerlegt"])


def miss(gruppierung, basis=None) -> dict:
    """Die Zielfunktion von A0301 (Runde 2).

    Args:
        gruppierung: die Funktion, die gemessen wird (``umfeld.grundriss_cluster``).
        basis: die Fassung, gegen die Rückschritte gezählt werden (``fluegel_basis.basis_cluster``);
            ohne sie bleibt ``rueckschritte`` leer.

    Returns:
        ``faelle``; ``entscheidbar`` und davon ``richtig`` (``anteil``); ``gegenfaelle`` (entscheidbar,
        mindestens zwei Häuser) und darin ``verschmelzungen_gegenfaelle``; ``verschmelzungen`` (alle
        entscheidbaren Fälle); ``mehrdeutig`` und davon ``gemeldet``; ``falsch_gemeldet`` (entscheidbare
        Fälle mit Vermerk); ``rueckschritte`` und ``falsch`` als ``[(name, grund), …]``; ``richtig_alle``
        (auch die mehrdeutigen, zum Vergleich mit der Basis).
    """
    alle = faelle()
    aus = {"faelle": len(alle), "entscheidbar": 0, "richtig": 0, "gegenfaelle": 0, "verschmelzungen_gegenfaelle": 0,
           "verschmelzungen": 0, "mehrdeutig": 0, "gemeldet": 0, "falsch_gemeldet": [], "rueckschritte": [],
           "falsch": [], "richtig_alle": 0}
    for fall in alle:
        cluster = gruppierung(fall["boxen"])
        urteil = beurteile(fall, cluster)
        aus["richtig_alle"] += urteil["richtig"]
        if basis is not None:
            vorher = beurteile(fall, basis(fall["boxen"]))
            if schlechter(urteil, vorher):
                aus["rueckschritte"].append((fall["name"], urteil["grund"]))
        if fall["mehrdeutig"]:
            aus["mehrdeutig"] += 1
            aus["gemeldet"] += gemeldet(cluster)
            continue
        aus["entscheidbar"] += 1
        aus["verschmelzungen"] += urteil["verschmelzungen"]
        if fall["gegenfall"]:
            aus["gegenfaelle"] += 1
            aus["verschmelzungen_gegenfaelle"] += urteil["verschmelzungen"]
        if gemeldet(cluster):
            aus["falsch_gemeldet"].append(fall["name"])
        if urteil["richtig"]:
            aus["richtig"] += 1
        else:
            aus["falsch"].append((fall["name"], urteil["grund"]))
    aus["anteil"] = aus["richtig"] / aus["entscheidbar"]
    return aus


def bericht(m: dict) -> str:
    return (f"{m['richtig']} von {m['entscheidbar']} entscheidbaren Fällen richtig ({100 * m['anteil']:.1f} %), "
            f"{m['verschmelzungen_gegenfaelle']} falsche Verschmelzungen in {m['gegenfaelle']} entscheidbaren "
            f"Gegenfällen, {m['gemeldet']} von {m['mehrdeutig']} mehrdeutigen Fällen gemeldet, "
            f"{len(m['falsch_gemeldet'])} entscheidbare mit Vermerk, {len(m['rueckschritte'])} Rückschritte "
            f"gegen die Basis; alle {m['faelle']} Fälle: {m['richtig_alle']} richtig")


if __name__ == "__main__":                                    # pragma: no cover: Messung von Hand
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
    from aiimaging import umfeld
    from fluegel_basis import basis_cluster
    for name, funktion in (("Basis", basis_cluster), ("Kopf ", umfeld.grundriss_cluster)):
        m = miss(funktion, basis_cluster)
        print(f"{name}: {bericht(m)}")
        if funktion is not basis_cluster:
            for wort in ("falsch", "rueckschritte"):
                for fall, grund in m[wort]:
                    print(f"  {wort.upper()} {fall}: {grund}")
            for fall in m["falsch_gemeldet"]:
                print(f"  ENTSCHEIDBAR MIT VERMERK {fall}")
