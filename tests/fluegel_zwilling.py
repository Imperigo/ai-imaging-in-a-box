"""Der Zwilling: der Gegenbeweis zu einem Stoss, unabhängig von ``aiimaging.umfeld`` gerechnet (A0301, Runde 2).

**Wozu:** ``umfeld.grundriss_cluster`` bekommt von jedem Bauteil nur den achsparallelen Hüllquader. Zwei
Boxen, die ineinander stecken, können zwei Flügel eines Hauses sein oder die Hüllquader zweier schräg
stehender, getrennter Nachbarn. Ob die zweite Lesart möglich ist, lässt sich ausrechnen: Gibt es zu den zwei
Boxen zwei gedrehte Rechtecke (jedes füllt seine Box aus und ist mindestens ``dicke_min`` dick), die sich
nicht oder nur knapp durchdringen, dann ist dieses Paar ein **Zwilling**, und der Stoss ist aus den Boxen
allein nicht entscheidbar. Gibt es keines, ist der Stoss bewiesen.

Diese Datei rechnet das ein zweites Mal und anders als das Produkt (Winkelraster statt Dickenraster, Schnitt
über Vielecke statt Trennachsen), damit die Proben die Regel nicht mit sich selbst vergleichen. Sie liefert
den Zwilling als zwei Vielecke: ein nachprüfbarer Beleg, kein Urteil.
"""
from __future__ import annotations

import math


def _rechteck(box, winkel: float, dicke_min: float):
    """Das um ``winkel`` (Bogenmass, zwischen -90 und 90 Grad) gedrehte Rechteck mit Hüllquader ``box`` als
    Vieleck gegen den Uhrzeigersinn, oder ``None``, wenn es keines gibt, das mindestens ``dicke_min`` dick ist."""
    (x0, y0), (x1, y1) = box
    breite, tiefe = x1 - x0, y1 - y0
    c, s = abs(math.cos(winkel)), abs(math.sin(winkel))
    det = c * c - s * s
    if abs(det) < 1e-9:
        return None
    w, h = (breite * c - tiefe * s) / det, (tiefe * c - breite * s) / det
    if w < dicke_min - 1e-9 or h < dicke_min - 1e-9:
        return None
    mx, my = (x0 + x1) / 2, (y0 + y1) / 2
    cw, sw = math.cos(winkel), math.sin(winkel)
    return [(mx + a * w / 2 * cw - b * h / 2 * sw, my + a * w / 2 * sw + b * h / 2 * cw)
            for a, b in ((-1, -1), (1, -1), (1, 1), (-1, 1))]


def lesarten(box, dicke_min: float, raster_grad: float = 1.0) -> list:
    """Die Box selbst und die gedrehten Rechtecke im Winkelraster, dazu je Drehsinn und Ast das dünnste noch
    zulässige (der Winkel, bei dem eine Seite genau ``dicke_min`` misst, per Halbierung gesucht)."""
    aus = [_rechteck(box, 0.0, 0.0)]
    schritte = int(round(90 / raster_grad))
    for k in range(1, schritte):
        for sinn in (1, -1):
            r = _rechteck(box, sinn * math.radians(k * raster_grad), dicke_min)
            if r:
                aus.append(r)
    (x0, y0), (x1, y1) = box
    if abs((x1 - x0) - (y1 - y0)) < 0.01:                  # Quadrat: bei genau 45 Grad passt jede Aufteilung
        seite, mx, my = ((x1 - x0) + (y1 - y0)) / 2, (x0 + x1) / 2, (y0 + y1) / 2
        dicke = dicke_min
        while dicke <= seite * math.sqrt(2.0) / 2:
            laenge = seite * math.sqrt(2.0) - dicke
            for sinn in (1, -1):
                c, s = math.sqrt(0.5), sinn * math.sqrt(0.5)
                aus.append([(mx + a * laenge / 2 * c - b * dicke / 2 * s, my + a * laenge / 2 * s + b * dicke / 2 * c)
                            for a, b in ((-1, -1), (1, -1), (1, 1), (-1, 1))])
            dicke += 0.25
    for start, ende in ((0.0, math.pi / 4), (math.pi / 2, math.pi / 4)):
        if _rechteck(box, start if start else math.pi / 2 - 1e-9, dicke_min) is None:
            continue
        lo, hi = start, ende
        for _ in range(60):
            mitte = (lo + hi) / 2
            if _rechteck(box, mitte, dicke_min):
                lo = mitte
            else:
                hi = mitte
        for sinn in (1, -1):
            r = _rechteck(box, sinn * lo, dicke_min)
            if r and abs(lo - start) > 1e-9:
                aus.append(r)
    return aus


def _schnitt(a, b) -> list:
    """Schnitt zweier konvexer Vielecke (gegen den Uhrzeigersinn), eigene Fassung."""
    aus = list(a)
    for k in range(len(b)):
        (px, py), (qx, qy) = b[k - 1], b[k]
        ein, aus = aus, []
        for m in range(len(ein)):
            u, v = ein[m - 1], ein[m]
            su = (qx - px) * (u[1] - py) - (qy - py) * (u[0] - px)
            sv = (qx - px) * (v[1] - py) - (qy - py) * (v[0] - px)
            if (su >= 0) != (sv >= 0):
                t = su / (su - sv)
                aus.append((u[0] + t * (v[0] - u[0]), u[1] + t * (v[1] - u[1])))
            if sv >= 0:
                aus.append(v)
        if not aus:
            return []
    return aus


def breite_des_schnitts(a, b) -> float:
    """Die Mindestbreite des Schnitts zweier konvexer Vielecke (0, wenn sie sich nicht schneiden)."""
    s = _schnitt(a, b)
    if len(s) < 3:
        return 0.0
    kleinste = float("inf")
    for k in range(len(s)):
        (px, py), (qx, qy) = s[k - 1], s[k]
        laenge = math.hypot(qx - px, qy - py)
        if laenge > 1e-9:
            kleinste = min(kleinste, max(abs((qx - px) * (r[1] - py) - (qy - py) * (r[0] - px)) for r in s) / laenge)
    return kleinste if kleinste < float("inf") else 0.0


def zwilling(box_a, box_b, *, dicke_min: float = 3.0, tiefe_min: float = 0.5, raster_grad: float = 1.0):
    """Zwei gedrehte Rechtecke mit den Hüllquadern ``box_a`` und ``box_b``, die sich weniger als ``tiefe_min``
    durchdringen: der Beleg, dass der Stoss nicht bewiesen ist. ``None``, wenn es im Raster keines gibt."""
    la, lb = lesarten(box_a, dicke_min, raster_grad), lesarten(box_b, dicke_min, raster_grad)
    for p in la:
        for q in lb:
            if breite_des_schnitts(p, q) < tiefe_min:
                return p, q
    return None


def haeuser_bewiesen(boxen, haus, *, dicke_min: float = 3.0, tiefe_min: float = 0.5, raster_grad: float = 2.0):
    """Hängt jedes Haus eines Falls über Stösse zusammen, zu denen es keinen Zwilling gibt?

    Returns:
        ``(ja, zwillinge)``: ``zwillinge`` sind die gefundenen Gegenbeweise ``(box_a, box_b, vieleck_a,
        vieleck_b)`` der Paare, die sich überlappen, aber nicht bewiesen sind.
    """
    ja, zwillinge = True, []
    for nummer in sorted({h for h in haus if h is not None}):
        grundrisse = sorted({(tuple(round(v * 2) / 2 for v in (b[0][0], b[0][1])),
                              tuple(round(v * 2) / 2 for v in (b[1][0], b[1][1])))
                             for b, h in zip(boxen, haus) if h == nummer})
        erreicht, rand = {grundrisse[0]}, [grundrisse[0]]
        geprueft: dict = {}
        while rand:
            a = rand.pop()
            for b in grundrisse:
                if b in erreicht:
                    continue
                if min(a[1][0], b[1][0]) - max(a[0][0], b[0][0]) <= 0.01 or min(a[1][1], b[1][1]) - max(a[0][1], b[0][1]) <= 0.01:
                    continue
                if (a, b) not in geprueft:
                    geprueft[(a, b)] = geprueft[(b, a)] = zwilling(a, b, dicke_min=dicke_min, tiefe_min=tiefe_min,
                                                                    raster_grad=raster_grad)
                if geprueft[(a, b)] is None:
                    erreicht.add(b)
                    rand.append(b)
        if len(erreicht) < len(grundrisse):
            ja = False
            zwillinge += [(a, b) + z for (a, b), z in geprueft.items() if z is not None and a < b]
    return ja, zwillinge
