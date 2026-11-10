"""Das Prüfmass für «Freie Sicht aufs Haus» (A0306, Runde 2). Keine Probe, ein Messgerät.

**Dieses Modul benutzt nichts von der Lösung.** Kein Import aus dem Paket, keine Funktion
der Kamera-Bibliothek, kein Wert, den die Lösung über sich selbst meldet (Füllgrad,
Sichturteil, verdeckter Anteil). Eine Probe prüft das am Quelltext
(``test_freie_sicht.py``). Der Anlass ist der Befund des Gegenlesens (G-A0306, M2): Das
erste Prüfmass teilte mit der Lösung die 15 Sichtpunkte, die Rahmungsrechnung und den
gemeldeten Füllgrad. Was das gemeinsame Raster nicht sah, galt in Lösung und Prüfmass als
frei, und die 100 % massen die Blindheit des Rasters.

Was hier steht, ist darum alles selbst gerechnet:

* **Verdeckung**: ein eigenes, festes Raster von 61 mal 31 Punkten je zugewandter Fläche,
  bis an die Kanten und an den Fuss (1 mm eingerückt), das Dach dazu, wenn das Auge darüber
  steht. Der Schnitt Strecke gegen Quader läuft an den Wandebenen im Weltsystem
  (Cyrus-Beck), für alle Punkte auf einmal. Das Ergebnis ist ein **Anteil der zugewandten
  Fläche in Quadratmetern**, nicht ein Ja oder Nein.
* **Rahmung**: eigene Projektion der acht Hausecken mit Shift und Bildrand, und der
  Füllgrad nach seiner Definition neu ausgeschrieben (Silhouette der vier Grundrissecken
  in der Bildbreite, Höhe an der nahen Fassade, die grössere Zahl gilt).
* **Lösbarkeit**: eine eigene Suche auf dem Weg der Kamera, in Schritten von 10 cm, die
  Brennweite von der bestellten abwärts in halben Millimetern.

Die Zahlen des Massstabs (Sensor, Bildrand, Riegel, kürzeste Brennweite, Grenzen des
Wegs) stehen hier als eigene Zahlen. Dass sie mit denen der Bibliothek übereinstimmen,
hält eine Probe fest; so fällt auf, wenn eine Seite sie ändert.

Ein Nachbarbau ist ein Verzeichnis ``{"mitte": (x, y), "halb": (hx, hy), "z": (unten,
oben), "drehung_grad": w}``: blosse Daten, wie der Erzeuger sie liefert.
"""
from __future__ import annotations

import math

import numpy as np

SENSORBREITE_MM = 36.0
BILDRAND = 0.92
RIEGEL = 0.65
KUERZESTE_BRENNWEITE_MM = 24.0
MINDESTABSTAND_M = 6.0
PUFFER_UM_DAS_HAUS_M = 3.0

#: Bis zu diesem verdeckten Anteil der zugewandten Fläche heisst eine Kamera «frei»
#: (Auftrag A0306, Runde 2).
FREI_HOECHSTENS = 0.01

RASTER = (61, 31)
EINGERUECKT_M = 0.001

#: Tastzeilen für Schmales: Sieht das Raster auf einer Fassade nichts, wird sie auf fünf
#: Höhen in Schritten von 2 cm abgetastet. Ein Mast von 20 cm Breite fällt zwischen zwei
#: Spalten des Rasters (23 cm bei 14 m Fassade) und verdeckt doch 1,4 % der Fläche.
TASTHOEHEN = (1 / 6, 2 / 6, 3 / 6, 4 / 6, 5 / 6)
TASTSCHRITT_M = 0.02
SUCHSCHRITT_M = 0.10
BRENNWEITENSCHRITT_MM = 0.5


# --------------------------------------------------------------------------------------
# Verdeckung
# --------------------------------------------------------------------------------------

def _grenzen(haus):
    lo = [min(haus[0][i], haus[1][i]) for i in range(3)]
    hi = [max(haus[0][i], haus[1][i]) for i in range(3)]
    return lo, hi


def flaechen(haus, auge) -> list[tuple[np.ndarray, float, np.ndarray | None]]:
    """Die dem Auge zugewandten Flächen der Hüllbox: je ``(Punkte N×3, Fläche in m²,
    Tastzeilen M×3)``. Das Dach hat keine Tastzeilen (``None``)."""
    lo, hi = _grenzen(haus)
    n_u, n_v = RASTER

    def _lagen(von, bis, n):
        rand = min(EINGERUECKT_M, (bis - von) / 4.0)
        return np.linspace(von + rand, bis - rand, n)

    aus = []
    zs = _lagen(lo[2], hi[2], n_v)
    for achse in (0, 1):
        andere = 1 - achse
        fest = (lo[achse] if auge[achse] < lo[achse] else
                hi[achse] if auge[achse] > hi[achse] else None)
        if fest is None:
            continue
        us = _lagen(lo[andere], hi[andere], n_u)
        uu, zz = np.meshgrid(us, zs, indexing="ij")
        punkte = np.empty((uu.size, 3))
        punkte[:, achse] = fest
        punkte[:, andere] = uu.ravel()
        punkte[:, 2] = zz.ravel()
        ts = _lagen(lo[andere], hi[andere],
                    int(math.ceil((hi[andere] - lo[andere]) / TASTSCHRITT_M)) + 1)
        tt, hh = np.meshgrid(ts, [lo[2] + (hi[2] - lo[2]) * q for q in TASTHOEHEN],
                             indexing="ij")
        zeilen = np.empty((tt.size, 3))
        zeilen[:, achse] = fest
        zeilen[:, andere] = tt.ravel()
        zeilen[:, 2] = hh.ravel()
        aus.append((punkte, (hi[andere] - lo[andere]) * (hi[2] - lo[2]), zeilen))
    if auge[2] > hi[2]:
        xx, yy = np.meshgrid(_lagen(lo[0], hi[0], n_u), _lagen(lo[1], hi[1], n_u), indexing="ij")
        punkte = np.column_stack([xx.ravel(), yy.ravel(), np.full(xx.size, hi[2])])
        aus.append((punkte, (hi[0] - lo[0]) * (hi[1] - lo[1]), None))
    return aus


def getroffen(auge, punkte: np.ndarray, koerper: dict) -> np.ndarray:
    """Für jede Strecke Auge → Punkt: Berührt sie den Quader? (Cyrus-Beck, Weltsystem.)"""
    a = np.asarray(auge, dtype=float)
    gang = punkte - a
    w = math.radians(koerper["drehung_grad"])
    t_ein = np.zeros(len(punkte))
    t_aus = np.ones(len(punkte))
    ok = np.ones(len(punkte), dtype=bool)
    ebenen = [((math.cos(w), math.sin(w), 0.0), koerper["halb"][0],
               math.cos(w) * koerper["mitte"][0] + math.sin(w) * koerper["mitte"][1]),
              ((-math.sin(w), math.cos(w), 0.0), koerper["halb"][1],
               -math.sin(w) * koerper["mitte"][0] + math.cos(w) * koerper["mitte"][1]),
              ((0.0, 0.0, 1.0), (koerper["z"][1] - koerper["z"][0]) / 2.0,
               (koerper["z"][1] + koerper["z"][0]) / 2.0)]
    for normale, halb, mitte in ebenen:
        n = np.asarray(normale)
        lage = float(a @ n) - mitte                 # Auge, gemessen von der Mittelebene
        schritt = gang @ n
        steht = schritt == 0.0
        ok &= ~(steht & (abs(lage) > halb))
        with np.errstate(divide="ignore", invalid="ignore"):
            t1 = (-halb - lage) / schritt
            t2 = (halb - lage) / schritt
        kleiner, groesser = np.minimum(t1, t2), np.maximum(t1, t2)
        t_ein = np.where(steht, t_ein, np.maximum(t_ein, kleiner))
        t_aus = np.where(steht, t_aus, np.minimum(t_aus, groesser))
    return ok & (t_ein <= t_aus)


def _kann_nicht_treffen(auge, punkte: np.ndarray, koerper: dict) -> bool:
    """Grobe Vorauswahl im Grundriss, auf der sicheren Seite: Liegt der Umkreis des Baus
    ganz hinter dem Auge, ganz hinter der Fläche oder ganz neben dem Fächer der
    Sichtlinien, kann keine Strecke ihn berühren. Im Zweifel ``False`` (dann wird gerechnet).
    """
    radius = math.hypot(koerper["halb"][0], koerper["halb"][1])
    ex, ey = float(auge[0]), float(auge[1])
    mx, my = float(punkte[:, 0].mean()), float(punkte[:, 1].mean())
    lx, ly = mx - ex, my - ey
    laenge = math.hypot(lx, ly)
    if laenge <= 1e-9:
        return False
    lx, ly = lx / laenge, ly / laenge
    cx, cy = koerper["mitte"][0] - ex, koerper["mitte"][1] - ey
    entlang = cx * lx + cy * ly
    quer = abs(-cx * ly + cy * lx)
    px, py = punkte[:, 0] - ex, punkte[:, 1] - ey
    weit = float((px * lx + py * ly).max())
    breit = float(np.abs(-px * ly + py * lx).max())
    return entlang + radius < 0.0 or entlang - radius > weit or quer - radius > breit


def verdeckter_anteil(auge, haus, nachbarn) -> float | None:
    """Welcher Anteil der zugewandten Fläche des Hauses hinter Nachbarbauten liegt (0 bis 1).

    ``None``, wenn dem Auge keine Fläche zugewandt ist.
    """
    gesamt = verdeckt = 0.0
    for punkte, flaeche, tastzeilen in flaechen(haus, auge):
        im_weg = [k for k in nachbarn if not _kann_nicht_treffen(auge, punkte, k)]
        zu = np.zeros(len(punkte), dtype=bool)
        for koerper in im_weg:
            zu |= getroffen(auge, punkte, koerper)
        anteil = float(zu.mean())
        if anteil == 0.0 and tastzeilen is not None and im_weg:
            # Das Raster sieht nichts: Steht etwas Schmales zwischen seinen Spalten?
            schmal = np.zeros(len(tastzeilen), dtype=bool)
            for koerper in im_weg:
                schmal |= getroffen(auge, tastzeilen, koerper)
            anteil = float(schmal.mean())
        gesamt += flaeche
        verdeckt += flaeche * anteil
    return (verdeckt / gesamt) if gesamt > 0.0 else None


def sicher_mehr_verdeckt_als(auge, haus, nachbarn, grenze: float) -> bool:
    """Schnelle, sichere Vorprüfung für die Suche: Zählt schon jede vierte Spalte des
    Rasters so viele verdeckte Punkte, dass der Anteil über ``grenze`` liegen MUSS, ist die
    volle Messung überflüssig. ``False`` heisst nur «nicht sicher», nie «frei»."""
    gesamt = sicher = 0.0
    for punkte, flaeche, _zeilen in flaechen(haus, auge):
        teil = punkte.reshape(RASTER[0], -1, 3)[::4].reshape(-1, 3)
        zu = np.zeros(len(teil), dtype=bool)
        for koerper in nachbarn:
            if not _kann_nicht_treffen(auge, punkte, koerper):
                zu |= getroffen(auge, teil, koerper)
        gesamt += flaeche
        sicher += flaeche * float(zu.sum()) / len(punkte)      # Untergrenze des Anteils
    return gesamt > 0.0 and sicher / gesamt > grenze


def ist_frei(auge, haus, nachbarn) -> bool:
    anteil = verdeckter_anteil(auge, haus, nachbarn)
    return anteil is not None and anteil <= FREI_HOECHSTENS


# --------------------------------------------------------------------------------------
# Rahmung
# --------------------------------------------------------------------------------------

def ecken_im_bild(auge, blick_auf, brennweite_mm, shift_mm, seitenverhaeltnis, haus,
                  rand: float = BILDRAND) -> bool:
    """Liegen alle acht Hausecken im Bild, mit Sicherheitsrand? Eigene Projektion.

    Die Kamera schaut von ``auge`` nach ``blick_auf``, Welt-Z ist oben. Der Shift
    verschiebt den Rahmen auf dem Sensor nach oben: Die Bildmitte liegt bei ``+shift_mm``.
    Der Rand gilt um die Achse (nicht um die verschobene Mitte), wie es der Eckentest der
    Bibliothek beschreibt: nach oben reicht der Rahmen ``rand · halbe Höhe + Shift``, nach
    unten ``rand · halbe Höhe − Shift``.
    """
    v = [blick_auf[i] - auge[i] for i in range(3)]
    laenge = math.sqrt(sum(c * c for c in v))
    v = [c / laenge for c in v]
    # rechts = v × z, hoch = rechts × v
    norm = math.hypot(v[1], v[0])
    rechts = (v[1] / norm, -v[0] / norm, 0.0)
    hoch = (rechts[1] * v[2], -rechts[0] * v[2], rechts[0] * v[1] - rechts[1] * v[0])
    halb_b = SENSORBREITE_MM / 2.0 * rand
    halb_h = SENSORBREITE_MM / seitenverhaeltnis / 2.0 * rand
    for x in (haus[0][0], haus[1][0]):
        for y in (haus[0][1], haus[1][1]):
            for z in (haus[0][2], haus[1][2]):
                d = (x - auge[0], y - auge[1], z - auge[2])
                tiefe = d[0] * v[0] + d[1] * v[1] + d[2] * v[2]
                if tiefe < 0.5:
                    return False
                sx = brennweite_mm * (d[0] * rechts[0] + d[1] * rechts[1]) / tiefe
                sy = brennweite_mm * (d[0] * hoch[0] + d[1] * hoch[1] + d[2] * hoch[2]) / tiefe
                if abs(sx) > halb_b or sy > halb_h + shift_mm or -sy > halb_h - shift_mm:
                    return False
    return True


def fuellgrad(abstand_m, azimut_grad, zielhoehe_ueber_fuss, brennweite_mm,
              seitenverhaeltnis, haus) -> float:
    """Welchen Anteil des Bildes das Haus füllt: die grössere Zahl aus Breite und Höhe.

    Neu ausgeschrieben nach der Definition der Rahmungsregel, nicht aus der Bibliothek
    gerufen. ``abstand_m`` ist der waagrechte Abstand der Kamera zur Mitte des Hauses,
    ``azimut_grad`` die Himmelsrichtung, in der die Kamera steht (im Uhrzeigersinn ab
    Nord).

    * **Breite:** Die vier Grundrissecken werden je an ihrer eigenen Tiefe auf die
      Bildebene geworfen; die Spanne zwischen der linkesten und der rechtesten, geteilt
      durch die Bildbreite.
    * **Höhe:** an der zugewandten Fassade (halbe Bautiefe näher als die Mitte); von der
      Zielhöhe aus der grössere der zwei Wege zu Traufe und Fuss, verdoppelt, geteilt
      durch die Bildhöhe dort.
    """
    lo, hi = _grenzen(haus)
    dx, dy, dz = hi[0] - lo[0], hi[1] - lo[1], hi[2] - lo[2]
    a = math.radians(azimut_grad)
    spuren = []
    for sx in (-1.0, 1.0):
        for sy in (-1.0, 1.0):
            quer = sx * dx / 2.0 * math.cos(a) - sy * dy / 2.0 * math.sin(a)
            laengs = sx * dx / 2.0 * math.sin(a) + sy * dy / 2.0 * math.cos(a)
            if abstand_m - laengs <= 1e-9:
                return 0.0
            spuren.append(quer / (abstand_m - laengs))
    bildbreite = SENSORBREITE_MM / brennweite_mm                 # in Brennweiten
    breite = (max(spuren) - min(spuren)) / bildbreite
    bautiefe = abs(dx * math.sin(a)) + abs(dy * math.cos(a))
    nah = max(abstand_m - bautiefe / 2.0, 1e-6)
    halbe = max(max(0.0, dz - zielhoehe_ueber_fuss), max(0.0, zielhoehe_ueber_fuss))
    bildhoehe = SENSORBREITE_MM / seitenverhaeltnis / brennweite_mm * nah
    hoehe = 2.0 * halbe / bildhoehe
    return max(breite, hoehe)


def angehobenes_ziel(kamera: dict) -> tuple[float, float, float]:
    """Das Blickziel, bevor der Shift es auf Augenhöhe zurückholte.

    Im Shift-Modus schaut die Kamera waagrecht, und der Höhenunterschied steckt im Shift:
    ``Höhe = Shift / Brennweite · Abstand``. Im gekippten Modus ist der Shift null und das
    Blickziel schon das angehobene.
    """
    auge, blick = kamera["auge"], kamera["blick_auf"]
    abstand = math.hypot(blick[0] - auge[0], blick[1] - auge[1])
    return (blick[0], blick[1], blick[2] + kamera["shift_mm"] / kamera["brennweite_mm"] * abstand)


def rahmung_haelt(kamera: dict, haus, *, azimut_grad: float, zielhoehe_ueber_fuss: float) -> bool:
    """Hält diese Kamera die Rahmungsregel? Nur aus Auge, Blickziel, Brennweite, Shift und
    Seitenverhältnis gerechnet. ``azimut_grad`` und die Zielhöhe kommen vom Fall (aus der
    heutigen Kamera), nicht von der Lösung."""
    auge, blick = kamera["auge"], kamera["blick_auf"]
    abstand = math.hypot(blick[0] - auge[0], blick[1] - auge[1])
    return (fuellgrad(abstand, azimut_grad, zielhoehe_ueber_fuss, kamera["brennweite_mm"],
                      kamera["seitenverhaeltnis"], haus) >= RIEGEL
            and ecken_im_bild(auge, blick, kamera["brennweite_mm"], kamera["shift_mm"],
                              kamera["seitenverhaeltnis"], haus))


# --------------------------------------------------------------------------------------
# Lösbarkeit: die eigene Suche
# --------------------------------------------------------------------------------------

def suche_standpunkt(haus, nachbarn, heutige: dict, *, hoechstens: float = FREI_HOECHSTENS,
                     schritt_m: float = SUCHSCHRITT_M) -> dict | None:
    """Gibt es auf dem Weg der Kamera einen Standpunkt, frei und regelgerecht gerahmt?

    ``heutige`` ist die Kamera ohne Sichtprüfung (der Fall, nicht die Lösung). Gesucht wird
    von ihr aus zum Haus hin, gleiche Augenhöhe, gleiche Richtung, nicht näher als 6 m am
    Blickziel und nicht im 3-m-Saum um das Haus; die Brennweite von der bestellten abwärts
    bis 24 mm. Zurück kommt der erste Fund (am weitesten vom Haus) oder ``None``.
    """
    lo, hi = _grenzen(haus)
    auge0 = heutige["auge"]
    ziel = angehobenes_ziel(heutige)
    gekippt = heutige["modus"] == "gekippt"
    d0 = math.hypot(auge0[0] - ziel[0], auge0[1] - ziel[1])
    ux, uy = (auge0[0] - ziel[0]) / d0, (auge0[1] - ziel[1]) / d0
    f0 = heutige["brennweite_mm"]
    brennweiten = [f0 - i * BRENNWEITENSCHRITT_MM
                   for i in range(int(max(0.0, f0 - KUERZESTE_BRENNWEITE_MM)
                                      / BRENNWEITENSCHRITT_MM) + 1)]
    if f0 > KUERZESTE_BRENNWEITE_MM and brennweiten[-1] > KUERZESTE_BRENNWEITE_MM:
        brennweiten.append(KUERZESTE_BRENNWEITE_MM)
    p = PUFFER_UM_DAS_HAUS_M
    n = 0
    while True:
        d = d0 - n * schritt_m
        n += 1
        ort = (ziel[0] + ux * d, ziel[1] + uy * d, auge0[2])
        if d < MINDESTABSTAND_M or (lo[0] - p <= ort[0] <= hi[0] + p
                                    and lo[1] - p <= ort[1] <= hi[1] + p):
            return None
        if sicher_mehr_verdeckt_als(ort, haus, nachbarn, hoechstens):
            continue
        anteil = verdeckter_anteil(ort, haus, nachbarn)
        if anteil is None or anteil > hoechstens:
            continue
        for f in brennweiten:
            if gekippt:
                blick, shift = ziel, 0.0
            else:
                blick, shift = (ziel[0], ziel[1], ort[2]), f * (ziel[2] - ort[2]) / d
            kamera = {"auge": ort, "blick_auf": blick, "brennweite_mm": f, "shift_mm": shift,
                      "seitenverhaeltnis": heutige["seitenverhaeltnis"]}
            if rahmung_haelt(kamera, haus, azimut_grad=heutige["azimut_grad"],
                             zielhoehe_ueber_fuss=ziel[2] - lo[2]):
                return dict(kamera, abstand_m=d, verdeckt_anteil=anteil)
