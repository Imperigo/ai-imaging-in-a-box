"""Erzeuger und Prüfmass für «Freie Sicht aufs Haus» (A0306). Keine Probe, ein Werkzeug.

**Der Satz.** 48 erfundene Szenen: ein Haus als Quader, dazu ein bis fünf Nachbarbauten in
wechselndem Abstand, wechselnder Höhe und Drehung. Jede Szene wird aus acht Richtungen
betrachtet, das ergibt 384 Fälle. Alles entsteht aus einer festen Zufallssaat in diesem
Modul; es gibt keine Datei daneben und kein echtes Projekt dahinter (Regel 3).

**Das Prüfmass ist mit Absicht nicht die Lösung.** Wer die Lösung mit ihrem eigenen Code
prüft, prüft nichts. Darum steht hier:

* ein **eigener Strahlentest** (:func:`strahl_trifft`, über die vier Wandebenen im
  Weltsystem statt über das gedrehte Achsensystem von ``aiimaging.sichtstrahl``),
* eine **eigene Projektion** der acht Hausecken (:func:`ecken_im_rahmen`),
* und eine **eigene Suche** nach einem zulässigen Standpunkt
  (:func:`freies_wegstueck`): in Schritten von 1 cm statt 5 cm, und mit der *kürzesten*
  zulässigen Brennweite geprüft, wo die Lösung die *längste* sucht.

Was das Prüfmass von der Bibliothek übernimmt, ist allein der Massstab, den der Auftrag
nennt: der Eckentest (``kameras.ecken_im_bild``), der Füllgrad, wie ``kamerasatz`` ihn
misst, und der Riegel ``BILDBREITE_ABBRUCH``.

**Was «lösbar» heisst.** Es gibt einen Standpunkt auf dem Weg vom gerechneten Standort zum
Blickziel (gleiche Augenhöhe, gleiche Richtung), nicht näher als die Grenzen von
``ziehe_bis_frei``, an dem eine Brennweite zwischen ``ZIEH_BRENNWEITE_MIN_MM`` und der
bestellten das Haus regelgerecht rahmt UND kein Nachbarbau einen Sichtpunkt verdeckt, und
dieses Wegstück ist mindestens zehn Zentimeter lang (:data:`LOESBAR_AB_M`).
"""
from __future__ import annotations

import math
import random

from aiimaging import kameras, sichtstrahl

#: Die feste Saat. Wer sie ändert, ändert den Satz, und jede Zahl in der Meldung zu A0306.
SAAT = 20261110

#: Acht Richtungen: die vier Frontalen und je eine Über-Eck-Ansicht pro Seite.
RICHTUNGEN = ("n", "e", "s", "w", "nNE", "eES", "sSW", "wWN")

#: Wie viele Szenen je Art. Die Art lenkt nur das Würfeln; was ein Fall IST (frei, lösbar,
#: unlösbar), entscheidet allein :func:`beurteile`.
ARTEN = (("fern", 16), ("niedrig", 6), ("seitlich", 10), ("nah", 6), ("ring", 4),
         ("abseits", 6))

#: Schrittweite der Suche im Prüfmass, in Metern. Fünfmal feiner als die Feinsuche der Lösung.
PRUEFSCHRITT_M = 0.01

#: Ab welcher Länge des freien, regelgerechten Wegstücks ein Fall **lösbar** heisst, und
#: unter welcher **unlösbar**. Dazwischen liegt der Grenzfall: Dort ist ein Standpunkt nur
#: mit weniger als zehn Zentimetern Spielraum zu haben, und beide Antworten sind vertretbar.
#: Die Lösung sagt genau diese zwei Grenzen zu (``kameras.ZIEH_FEINSCHRITT_M``); eine Probe
#: hält die Zahlen beisammen. Das Prüfmass misst mit einem Schritt Zugabe, weil ein Raster
#: von 1 cm ein Wegstück nur auf 1 cm genau kennt.
LOESBAR_AB_M = 0.11
UNLOESBAR_UNTER_M = 0.04


# --------------------------------------------------------------------------------------
# Der Erzeuger
# --------------------------------------------------------------------------------------

def _haus(r: random.Random):
    breite, tiefe, hoehe = r.uniform(9, 24), r.uniform(8, 18), r.uniform(6, 18)
    x, y = r.uniform(-30, 30), r.uniform(-30, 30)
    fuss = r.choice((0.0, 0.0, 412.5))
    return [[x, y, fuss], [x + breite, y + tiefe, fuss + hoehe]]


def _nachbar(r: random.Random, haus, art: str, satz: dict, nr: int, winkel=None):
    """Ein Nachbarbau, der das Haus nicht berührt.

    Die Arten ``fern``, ``niedrig`` und ``seitlich`` stellen ihn **auf den Weg einer der
    acht Kameras**: ``anteil`` ist seine Lage zwischen Blickziel (0) und Kamera (1),
    ``quer`` der seitliche Versatz in Metern. So entstehen Verdeckungen mit Absicht und
    nicht nur, wenn der Zufall einen Bau gerade in eine Sichtlinie würfelt.
    """
    (x0, y0, fuss), (x1, y1, _oben) = haus
    mx, my = (x0 + x1) / 2.0, (y0 + y1) / 2.0
    weite = sum(k["abstand_m"] for k in satz["kameras"]) / len(satz["kameras"])
    for _ in range(400):
        breite, tiefe = r.uniform(5, 14), r.uniform(5, 14)
        hoehe = r.uniform(5, 20)
        drehung = r.choice((0.0, 0.0, 15.0, 30.0, 45.0, 70.0))
        if art in ("fern", "niedrig", "seitlich"):
            kamera = r.choice(satz["kameras"])
            if art == "fern":
                anteil, quer = r.uniform(0.8, 1.02), r.uniform(-4.0, 4.0)
                breite, tiefe = r.uniform(4, 9), r.uniform(4, 9)
            elif art == "niedrig":
                anteil, quer = r.uniform(0.78, 1.0), r.uniform(-5.0, 5.0)
                hoehe = r.uniform(2.0, 4.0)
            else:
                anteil = r.uniform(0.55, 0.92)
                quer = r.choice((-1.0, 1.0)) * r.uniform(3.0, 12.0)
                breite, tiefe = r.uniform(3, 7), r.uniform(3, 7)
            ex, ey = kamera["auge"][0] - mx, kamera["auge"][1] - my
            laenge = math.hypot(ex, ey)
            cx = mx + ex * anteil + (ey / laenge) * quer
            cy = my + ey * anteil - (ex / laenge) * quer
        else:
            w = r.uniform(0.0, 360.0) if winkel is None else winkel + r.uniform(-12.0, 12.0)
            if art == "nah":
                abstand = (max(x1 - x0, y1 - y0) / 2.0 + r.uniform(1.0, 6.0)
                           + max(breite, tiefe) / 2.0)
                drehung = 0.0
            elif art == "ring":
                breite, tiefe = r.uniform(12, 20), r.uniform(12, 20)
                hoehe = r.uniform(12, 22)
                abstand = (max(x1 - x0, y1 - y0) / 2.0 + r.uniform(4.0, 9.0)
                           + max(breite, tiefe) / 2.0)
            else:                                           # abseits
                abstand = r.uniform(1.4, 2.2) * weite
            cx = mx + math.sin(math.radians(w)) * abstand
            cy = my + math.cos(math.radians(w)) * abstand
        radius = math.hypot(breite, tiefe) / 2.0
        # Abstand des Mittelpunkts vom Hausrechteck, grob und auf der sicheren Seite.
        dx = max(x0 - cx, 0.0, cx - x1)
        dy = max(y0 - cy, 0.0, cy - y1)
        if math.hypot(dx, dy) > radius + 0.5:
            return sichtstrahl.quader((cx, cy), breite, tiefe, hoehe, fuss_z=fuss,
                                      drehung_grad=drehung, name=f"nachbar-{nr}")
    raise RuntimeError("Kein Platz für den Nachbarbau gefunden; der Erzeuger ist verstellt.")


def szenen() -> list[dict]:
    """Die 48 Szenen, jedes Mal dieselben. Je Szene ``name``, ``art``, ``haus``, ``nachbarn``."""
    r = random.Random(SAAT)
    aus = []
    for art, anzahl in ARTEN:
        for i in range(anzahl):
            haus = _haus(r)
            satz = kameras.kamerasatz(haus, kuerzel=list(RICHTUNGEN))
            if art == "ring":
                # Rundum zugebaut: je ein hoher Bau in vier bis fünf Himmelsrichtungen.
                start = r.uniform(0.0, 90.0)
                n = r.choice((4, 5))
                nachbarn = [_nachbar(r, haus, art, satz, j, winkel=start + j * 360.0 / n)
                            for j in range(n)]
            else:
                nachbarn = [_nachbar(r, haus, art, satz, j) for j in range(r.randint(1, 5))]
            aus.append({"name": f"{art}-{i + 1:02d}", "art": art, "haus": haus,
                        "nachbarn": nachbarn})
    return aus


def faelle() -> list[dict]:
    """Jede Szene aus jeder der acht Richtungen: ``{szene, kuerzel}``."""
    return [{"szene": s, "kuerzel": k} for s in szenen() for k in RICHTUNGEN]


# --------------------------------------------------------------------------------------
# Das Prüfmass: eigener Strahlentest, eigene Projektion, eigene Suche
# --------------------------------------------------------------------------------------

def strahl_trifft(von, nach, koerper: dict) -> bool:
    """Berührt die Strecke den Quader? Gerechnet an den vier Wandebenen im Weltsystem.

    Mit Absicht ein anderer Weg als ``sichtstrahl.strecke_trifft``: Dort wird die Strecke in
    das Achsensystem des Quaders gedreht, hier bleiben die Punkte, wo sie sind, und die
    Wände werden als Halbebenen mit gedrehten Normalen angesetzt.
    """
    w = math.radians(koerper["drehung_grad"])
    achsen = ((math.cos(w), math.sin(w)), (-math.sin(w), math.cos(w)))
    t_ein, t_aus = 0.0, 1.0
    halbebenen = []
    for (nx, ny), halb in zip(achsen, koerper["halb"]):
        mitte = nx * koerper["mitte"][0] + ny * koerper["mitte"][1]
        halbebenen.append((nx * von[0] + ny * von[1] - mitte,
                           nx * (nach[0] - von[0]) + ny * (nach[1] - von[1]), halb))
    z_mitte = (koerper["z"][0] + koerper["z"][1]) / 2.0
    halbebenen.append((von[2] - z_mitte, nach[2] - von[2],
                       (koerper["z"][1] - koerper["z"][0]) / 2.0))
    for lage, gang, halb in halbebenen:
        # Bedingung: -halb <= lage + t * gang <= halb
        if gang == 0.0:
            if abs(lage) > halb:
                return False
            continue
        a, b = (-halb - lage) / gang, (halb - lage) / gang
        t_ein, t_aus = max(t_ein, min(a, b)), min(t_aus, max(a, b))
        if t_ein > t_aus:
            return False
    return True


def sicht_ist_frei(auge, haus, nachbarn) -> bool:
    """Verdeckt kein Nachbarbau einen Sichtpunkt des Hauses? Mit dem eigenen Strahlentest."""
    punkte = kameras.sichtpunkte(haus, auge)
    if not punkte:
        return False
    return not any(strahl_trifft(auge, p, n) for p in punkte for n in nachbarn)


def ecken_im_rahmen(kamera: dict, haus) -> bool:
    """Liegen alle acht Hausecken im Bild dieser Kamera? Eigene Projektion, ohne Bildrand.

    Die Gegenprobe zu ``kameras.ecken_im_bild``: dieselbe Frage, aber aus Auge, Blickziel,
    Brennweite und Shift der fertigen Kamera selbst gerechnet. Ohne den Sicherheitsrand,
    darum etwas milder; ein Fehler in den Feldern der Kamera fällt trotzdem auf.
    """
    auge, blick = kamera["auge"], kamera["blick_auf"]
    v = [blick[i] - auge[i] for i in range(3)]
    laenge = math.sqrt(sum(c * c for c in v))
    v = [c / laenge for c in v]
    rechts = (v[1], -v[0], 0.0)
    norm = math.hypot(rechts[0], rechts[1])
    rechts = (rechts[0] / norm, rechts[1] / norm, 0.0)
    hoch = (rechts[1] * v[2] - rechts[2] * v[1], rechts[2] * v[0] - rechts[0] * v[2],
            rechts[0] * v[1] - rechts[1] * v[0])
    f = kamera["brennweite_mm"]
    halb_b = kameras.SENSOR_BREITE_MM / 2.0
    halb_h = halb_b / kamera["seitenverhaeltnis"]
    for x in (haus[0][0], haus[1][0]):
        for y in (haus[0][1], haus[1][1]):
            for z in (haus[0][2], haus[1][2]):
                d = (x - auge[0], y - auge[1], z - auge[2])
                tiefe = sum(d[i] * v[i] for i in range(3))
                if tiefe <= 0.0:
                    return False
                auf_sensor_x = f * sum(d[i] * rechts[i] for i in range(3)) / tiefe
                auf_sensor_y = f * sum(d[i] * hoch[i] for i in range(3)) / tiefe
                # Der Shift verschiebt den Rahmen nach oben: Mitte bei +shift_mm.
                if abs(auf_sensor_x) > halb_b or abs(auf_sensor_y - kamera["shift_mm"]) > halb_h:
                    return False
    return True


def rahmung_haelt(kamera: dict, haus) -> bool:
    """Hält die fertige Kamera die Rahmungsregel? Eckentest, Füllgrad, Gegenprobe."""
    ecken = kameras.ecken_im_bild(kamera["auge"], kamera["blick_auf"], haus,
                                  brennweite_mm=kamera["brennweite_mm"],
                                  seitenverhaeltnis=kamera["seitenverhaeltnis"],
                                  shift_mm=kamera["shift_mm"])
    return (ecken["passt"] and ecken_im_rahmen(kamera, haus)
            and kamera["fuellgrad"] >= kameras.BILDBREITE_ABBRUCH)


def _ziel(haus, kamera):
    """Das angehobene Blickziel, wie ``kamerasatz`` es setzt (aus Shift zurückgerechnet)."""
    blick = kamera["blick_auf"]
    abstand = math.hypot(blick[0] - kamera["auge"][0], blick[1] - kamera["auge"][1])
    return (blick[0], blick[1],
            blick[2] + kamera["shift_mm"] / kamera["brennweite_mm"] * abstand)


def freies_wegstueck(haus, nachbarn, basis: dict, *, schritt_m: float = PRUEFSCHRITT_M,
                     genug_m: float = LOESBAR_AB_M) -> float:
    """Das längste zusammenhängende Wegstück mit freier Sicht und haltender Rahmung, in Metern.

    Die Suche des Prüfmasses, nicht die der Lösung: in Schritten von 1 cm, und an jedem
    Standpunkt mit der **kürzesten** Brennweite geprüft, die den Riegel noch hält. Geht der
    Eckentest mit ihr nicht auf, geht er mit keiner längeren auf (mehr Brennweite heisst
    engerer Rahmen). Bricht ab, sobald ``genug_m`` erreicht ist.
    """
    auge0 = basis["auge"]
    f0 = basis["brennweite_mm"]
    ziel = _ziel(haus, basis)
    d0 = math.hypot(auge0[0] - ziel[0], auge0[1] - ziel[1])
    ux, uy = (auge0[0] - ziel[0]) / d0, (auge0[1] - ziel[1]) / d0
    puffer = kameras.HUELLBOX_PUFFER_M
    kw = {"azimut_grad": basis["azimut_grad"], "modus": basis["modus"],
          "seitenverhaeltnis": basis["seitenverhaeltnis"]}
    laengstes = 0.0
    anfang = None
    n = 1
    while True:
        d = d0 - n * schritt_m
        n += 1
        ort = (ziel[0] + ux * d, ziel[1] + uy * d, auge0[2])
        if d < kameras.MIN_ZIEH_ABSTAND_M or (
                haus[0][0] - puffer <= ort[0] <= haus[1][0] + puffer
                and haus[0][1] - puffer <= ort[1] <= haus[1][1] + puffer):
            return laengstes
        gut = sicht_ist_frei(ort, haus, nachbarn)
        if gut:
            bei_f0 = kameras.rahmung_am_standpunkt(ort, ziel, haus, brennweite_mm=f0, **kw)
            # Füllgrad wächst gleichmässig mit der Brennweite: die kürzeste, die 65 % hält.
            f_kurz = max(kameras.ZIEH_BRENNWEITE_MIN_MM,
                         f0 * kameras.BILDBREITE_ABBRUCH / bei_f0["fuellgrad"] * (1.0 + 1e-9))
            gut = f_kurz <= f0 and kameras.rahmung_am_standpunkt(
                ort, ziel, haus, brennweite_mm=f_kurz, **kw)["haelt"]
        if not gut:
            anfang = None
            continue
        anfang = d if anfang is None else anfang
        laengstes = max(laengstes, anfang - d)
        if laengstes >= genug_m:
            return laengstes


def beurteile(fall: dict, kamera: dict | None = None, *, vorgabe: dict | None = None) -> dict:
    """Ein Fall, beurteilt: was er ist, und ob die fertige Kamera das Ziel erreicht.

    ``kamera`` ist die fertige Kamera der Lösung; ohne sie wird die heutige beurteilt
    (``kamerasatz`` ohne Sichtprüfung). ``vorgabe`` sind weitere Angaben für den Kamerasatz
    der Basis (Brennweite, Modus, Seitenverhältnis); sie müssen dieselben sein, mit denen
    ``kamera`` gerechnet wurde.

    Returns:
        ``{klasse, basis, kamera, frei, gerahmt, erreicht}``. ``klasse`` ist ``frei`` (am
        gerechneten Standort verdeckt nichts), ``loesbar`` (verdeckt, aber es gibt einen
        Standpunkt mit Spielraum), ``unloesbar`` oder ``grenzfall`` (ein Standpunkt nur
        auf der Messerschneide, siehe :data:`LOESBAR_AB_M`).
    """
    haus, nachbarn = fall["szene"]["haus"], fall["szene"]["nachbarn"]
    basis = kameras.kamerasatz(haus, kuerzel=[fall["kuerzel"]], **(vorgabe or {}))["kameras"][0]
    if sicht_ist_frei(basis["auge"], haus, nachbarn):
        klasse = "frei"
    else:
        stueck = freies_wegstueck(haus, nachbarn, basis)
        klasse = ("loesbar" if stueck >= LOESBAR_AB_M else
                  "unloesbar" if stueck < UNLOESBAR_UNTER_M else "grenzfall")
    fertig = basis if kamera is None else kamera
    frei = sicht_ist_frei(fertig["auge"], haus, nachbarn)
    gerahmt = rahmung_haelt(fertig, haus)
    return {"klasse": klasse, "basis": basis, "kamera": fertig, "frei": frei,
            "gerahmt": gerahmt, "erreicht": frei and gerahmt,
            "wegstueck_m": None if klasse == "frei" else stueck}


def nacheinander(fall: dict) -> dict:
    """Die zwei alten Regeln hintereinander: erst heranziehen, dann zurückschieben.

    Das ist die Schaltung, vor der der Kommentar an ``ziehe_bis_frei`` warnt, mit fester
    Brennweite. Sie ist hier nachgebaut, um das Gegeneinander zu MESSEN statt zu behaupten.
    """
    haus, nachbarn = fall["szene"]["haus"], fall["szene"]["nachbarn"]
    basis = kameras.kamerasatz(haus, kuerzel=[fall["kuerzel"]])["kameras"][0]
    gezogen = kameras.ziehe_bis_frei(
        basis["auge"], basis["blick_auf"], haus,
        lambda auge, _ziel: sicht_ist_frei(auge, haus, nachbarn))
    geschoben = kameras.schiebe_bis_im_bild(
        gezogen["auge"], basis["blick_auf"], haus, shift_mm=basis["shift_mm"],
        brennweite_mm=basis["brennweite_mm"], seitenverhaeltnis=basis["seitenverhaeltnis"])
    kamera = dict(basis, auge=geschoben["auge"])
    lage = kameras.rahmung_am_standpunkt(
        kamera["auge"], _ziel(haus, basis), haus, azimut_grad=basis["azimut_grad"],
        brennweite_mm=basis["brennweite_mm"], seitenverhaeltnis=basis["seitenverhaeltnis"],
        modus=basis["modus"])
    kamera["fuellgrad"] = lage["fuellgrad"]
    return {"kamera": kamera, "gezogen_frei": gezogen["frei"],
            "zurueckgeschoben": geschoben["durchlaeufe"] > 0}


def messe(loesung=None) -> dict:
    """Die Zielfunktion über den ganzen Satz.

    ``loesung`` ist ``(fall) → fertige Kamera`` oder ``None`` für den heutigen Stand.

    Returns:
        Zählung je Klasse und ``anteil_loesbar`` (verdeckt und lösbar: wie viele davon
        frei und regelgerecht gerahmt sind), dazu ``anteil_mit_freien`` (dieselbe Zahl
        einschliesslich der Fälle, in denen von Anfang an nichts verdeckt).
    """
    zahl = {"frei": 0, "loesbar": 0, "unloesbar": 0, "grenzfall": 0}
    erreicht = {"frei": 0, "loesbar": 0, "unloesbar": 0, "grenzfall": 0}
    einzeln = []
    for fall in faelle():
        urteil = beurteile(fall, None if loesung is None else loesung(fall))
        zahl[urteil["klasse"]] += 1
        erreicht[urteil["klasse"]] += urteil["erreicht"]
        einzeln.append((fall, urteil))
    mit_freien = zahl["frei"] + zahl["loesbar"]
    return {"faelle": len(einzeln), "szenen": len(szenen()), "zahl": zahl,
            "erreicht": erreicht,
            "anteil_loesbar": (erreicht["loesbar"] / zahl["loesbar"]) if zahl["loesbar"] else None,
            "anteil_mit_freien": ((erreicht["frei"] + erreicht["loesbar"]) / mit_freien
                                  if mit_freien else None),
            "einzeln": einzeln}


if __name__ == "__main__":                                  # pragma: no cover
    # `python tests/sichtszenen.py` druckt die Messung, wie sie in der Meldung steht.
    def _mit_sicht(fall):
        s = fall["szene"]
        return kameras.kamerasatz(s["haus"], kuerzel=[fall["kuerzel"]],
                                  sicht_frei=sichtstrahl.pruefer(s["nachbarn"]))["kameras"][0]

    for titel, weg in (("heute (ohne Sichtprüfung)", None),
                       ("nacheinander (alt, feste Brennweite)",
                        lambda fall: nacheinander(fall)["kamera"]),
                       ("ein Ablauf (A0306)", _mit_sicht)):
        m = messe(weg)
        print(f"{titel}: {m['szenen']} Szenen, {m['faelle']} Fälle, Klassen {m['zahl']}, "
              f"erreicht {m['erreicht']}, lösbare frei und gerahmt: "
              f"{m['anteil_loesbar']:.1%} (mit von Anfang an freien: "
              f"{m['anteil_mit_freien']:.1%})")
