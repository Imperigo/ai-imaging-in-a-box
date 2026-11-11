"""Der echte Grundriss eines Bauteils, aus seinen Dreiecken gelesen (A0301, Runde 3).

**Wozu:** :func:`aiimaging.umfeld.grundriss_cluster` fasst Bauteile zu Bauten zusammen. Von einem Teil kennt sie
sonst nur den achsparallelen Hüllquader. Der sagt nicht, ob das Teil seine Box ausfüllt: Ein Haus, das als EIN Netz
kommt und ein U oder L ist, hat einen leeren Hof in seiner Box, und ein Nachbar im Hof sieht dann aus wie ein
angebauter Flügel. Den Unterschied sieht nur der Grundriss, und den trägt das Netz selbst: Wirft man seine
Dreiecke senkrecht auf den Boden, decken sie genau die Fläche, die das Teil überbaut.

**Wie:** :func:`aus_dreiecken` nimmt die Dreiecke eines Teils in Weltkoordinaten (Z oben) und gibt eine Liste
konvexer Stücke zurück, die sich nicht überlappen (so verlangt es ``grundriss_cluster``):

1. Senkrechte Dreiecke (Wände) werfen keine Fläche und fallen weg. Von den übrigen zählt nur die eine Seite: die
   nach oben schauenden (bei einem geschlossenen Netz decken sie den Grundriss genau einmal, die nach unten
   schauenden ein zweites Mal). Welche Seite oben ist, sagt der Umlaufsinn; ist das Netz innen und aussen
   gemischt gewickelt (beide Seiten verschieden gross, keine leer), ist der Grundriss nicht sicher lesbar:
   ``None``.
2. Füllen die Dreiecke ihre konvexe Hülle (Fläche bis auf ein Promille, dazu ein Punktraster als Gegenprobe),
   ist der Grundriss diese Hülle: ein Stück. Das ist der häufige Fall, auch für ein gedrehtes Rechteck mit
   tausend Dreiecken.
3. Sonst (U, L, T, Z) werden die Dreiecke zu möglichst wenigen konvexen Stücken zusammengelegt; mehr als
   :data:`STUECKE_HOECHSTENS` Stücke oder mehr als :data:`DREIECKE_HOECHSTENS` Dreiecke: ``None``.

**Überlappende Dachdreiecke (A0322).** Schritt 2 und 3 setzen voraus, dass jeder Punkt des Bodens von höchstens
einem nach oben schauenden Dreieck gedeckt ist. Das gilt nicht, wenn ein Netz mehrere Körper trägt, die
übereinander liegen: Geschosse als eigene Körper, Flügel, die sich in den Ecken überlappen, eine Auskragung über
einem tieferen Dach. Die Flächensumme ist dann zu gross, und das Zusammenlegen würde Hof und Winkel zulegen. Darum
prüft :func:`aus_dreiecken` zuerst, wie oft jeder Punkt gedeckt ist (:func:`_streifen`):

* Gemeinsame Innenkanten zweier Dachdreiecke heben sich auf (sie laufen in beiden Richtungen); übrig bleiben die
  Randkanten der Dachflächen, auch bei tausend Dreiecken meist nur der Umriss.
* Zwischen je zwei senkrechten Linien durch alle Ecken und Kantenschnitte (ein **Streifen**) kreuzen sich diese
  Kanten nicht. Von unten nach oben gezählt, sagt jede Kante, ob man eine Dachfläche betritt (+1) oder verlässt
  (-1): Die Summe ist die **Deckungszahl**, wie viele Dächer über dem Punkt liegen.
* Deckungszahl höchstens 1 überall: keine Überlappung, Schritt 2 und 3 wie bisher. Sonst ist der Grundriss die
  Fläche mit Deckungszahl ab 1, die Vereinigung, genau gerechnet: Füllt sie ihre Hülle, ein Stück; sonst ihre
  Trapeze je Streifen (konvex, ohne Überlappung), zu möglichst wenigen Stücken zusammengelegt.
* Mehr als :data:`KANTEN_HOECHSTENS` Randkanten oder mehr Rechenschritte als :data:`ARBEIT_HOECHSTENS`: die
  Deckung ist nicht in vernünftiger Zeit sicher zu prüfen, ``None``. Nie wird eine Fläche geraten.

``None`` heisst immer: kein Grundriss, die Box gilt, und ein Stoss an diesem Teil ist nicht beweisbar (die
vorsichtige Seite). Reine Rechnung, ohne Paket, ohne Datei (Visbox-Regel 4).

**Bis A0322 galt die Annahme**, das Netz krage nicht über sich selbst aus (die Fläche sei dann nur zu gross, die
Form richtig). Das war falsch: Die Form war auch falsch (Hof und Winkel zugelegt). Siehe oben.
"""
from __future__ import annotations

#: So viele Dreiecke liest :func:`aus_dreiecken` je Teil höchstens; darüber kein Grundriss (die Box gilt).
DREIECKE_HOECHSTENS = 20_000
#: So viele konvexe Stücke darf ein nicht konvexer Grundriss haben; darüber kein Grundriss (die Box gilt).
STUECKE_HOECHSTENS = 64
#: Dreiecke mit weniger Grundfläche (m²) sind senkrecht oder entartet und werfen keine Fläche.
FLAECHE_MIN_M2 = 1e-6
#: So genau müssen die Dreiecke ihre Hülle füllen, damit sie als ein Stück gilt (Anteil der Fläche).
HUELLE_TOLERANZ = 1e-3
#: So viele Prüfpunkte je Richtung legt die Gegenprobe über die Hülle.
RASTER = 15
#: So viele Randkanten der Dachflächen prüft :func:`_streifen` höchstens auf Überlappung; darüber kein Grundriss.
KANTEN_HOECHSTENS = 1_000
#: So viele Kantenschnitte und Kanten je Streifen zusammen rechnet :func:`_streifen` höchstens; darüber kein Grundriss
#: (die Rechenzeit bliebe sonst bei sehr wirren Netzen unbegrenzt).
ARBEIT_HOECHSTENS = 400_000
#: Ab diesem Anteil der Vereinigung gilt eine doppelt gedeckte Fläche als Überlappung (darunter Rundung an Kanten).
UEBERLAPPUNG_ANTEIL = 1e-6
#: Ecken, die näher als diese Länge (m) beieinander liegen, gelten beim Aufheben der Innenkanten als eine.
RUNDUNG_M = 1e-7


def _umlauf(p) -> float:
    """Doppelte vorzeichenbehaftete Fläche eines Vielecks (positiv gegen den Uhrzeigersinn)."""
    return sum(p[k - 1][0] * p[k][1] - p[k][0] * p[k - 1][1] for k in range(len(p)))


def _flaeche(p) -> float:
    return abs(_umlauf(p)) / 2.0


def konvexe_huelle(punkte) -> list:
    """Die konvexe Hülle (Andrew), gegen den Uhrzeigersinn, ohne Punkte auf den Kanten."""
    pts = sorted(set((float(x), float(y)) for x, y in punkte))
    if len(pts) <= 2:
        return pts

    def kreuz(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    unten: list = []
    for p in pts:
        while len(unten) >= 2 and kreuz(unten[-2], unten[-1], p) <= 1e-12:
            unten.pop()
        unten.append(p)
    oben: list = []
    for p in reversed(pts):
        while len(oben) >= 2 and kreuz(oben[-2], oben[-1], p) <= 1e-12:
            oben.pop()
        oben.append(p)
    return unten[:-1] + oben[:-1]


def _im_dreieck(x, y, d) -> bool:
    (ax, ay), (bx, by), (cx, cy) = d
    s1 = (bx - ax) * (y - ay) - (by - ay) * (x - ax)
    s2 = (cx - bx) * (y - by) - (cy - by) * (x - bx)
    s3 = (ax - cx) * (y - cy) - (ay - cy) * (x - cx)
    eps = 1e-9
    return (s1 >= -eps and s2 >= -eps and s3 >= -eps) or (s1 <= eps and s2 <= eps and s3 <= eps)


def _im_konvexen(x, y, p) -> bool:
    """Liegt der Punkt im konvexen Vieleck ``p`` (gegen den Uhrzeigersinn)?"""
    for k in range(len(p)):
        (ax, ay), (bx, by) = p[k - 1], p[k]
        if (bx - ax) * (y - ay) - (by - ay) * (x - ax) < -1e-9:
            return False
    return True


def _gedeckt(huelle, dreiecke) -> bool:
    """Gegenprobe: liegt jeder Punkt eines Rasters über der Hülle (etwas eingerückt) in einem Dreieck?"""
    xs, ys = [p[0] for p in huelle], [p[1] for p in huelle]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
    for a in range(RASTER):
        for b in range(RASTER):
            x = x0 + (x1 - x0) * (a + 0.5) / RASTER
            y = y0 + (y1 - y0) * (b + 0.5) / RASTER
            x, y = mx + (x - mx) * 0.999, my + (y - my) * 0.999
            if not _im_konvexen(x, y, huelle):
                continue
            if not any(_im_dreieck(x, y, d) for d in dreiecke):
                return False
    return True


def _zusammenlegen(dreiecke) -> list:
    """Dreiecke, die sich nicht überlappen, zu möglichst wenigen konvexen Stücken: Zwei Stücke werden eins, wenn
    ihre gemeinsame Hülle nicht grösser ist als beide zusammen (dann ist die Vereinigung selbst konvex)."""
    stuecke = [(konvexe_huelle(d), _flaeche(d)) for d in sorted(dreiecke, key=_flaeche, reverse=True)]
    geaendert = True
    while geaendert and len(stuecke) > 1:
        geaendert = False
        k = 0
        while k < len(stuecke):
            p, fp = stuecke[k]
            m = k + 1
            while m < len(stuecke):
                q, fq = stuecke[m]
                if _beruehren(p, q):
                    h = konvexe_huelle(p + q)
                    fh = _flaeche(h)
                    if fh <= (fp + fq) * (1 + 1e-9) + 1e-9:
                        p, fp = h, fp + fq
                        stuecke[k] = (p, fp)
                        del stuecke[m]
                        geaendert = True
                        continue
                m += 1
            k += 1
    return [p for p, _ in stuecke]


def _beruehren(p, q) -> bool:
    """Haben zwei konvexe Stücke einen gemeinsamen Punkt (Hüllquader berühren sich, schneller Vortest)?"""
    return not (max(a[0] for a in p) < min(b[0] for b in q) - 1e-6 or max(b[0] for b in q) < min(a[0] for a in p) - 1e-6
                or max(a[1] for a in p) < min(b[1] for b in q) - 1e-6 or max(b[1] for b in q) < min(a[1] for a in p) - 1e-6)


def _randkanten(dreiecke) -> dict | None:
    """Die Randkanten der Dachflächen ``seite`` (gegen den Uhrzeigersinn): ``{(a, b): gewicht}`` mit ``a`` links von
    ``b``; ``gewicht`` zählt, wie oft die Kante von links nach rechts läuft (Unterkante einer Fläche, positiv) weniger
    die Male von rechts nach links (Oberkante). Innenkanten heben sich auf, senkrechte Kanten fallen weg (sie kreuzt
    keine senkrechte Linie). ``None`` bei mehr als :data:`KANTEN_HOECHSTENS` Kanten."""
    kanten: dict = {}
    q = 1.0 / RUNDUNG_M
    for d in dreiecke:
        e = [(round(x * q) / q, round(y * q) / q) for x, y in d]
        for k in range(3):
            a, b = e[k], e[(k + 1) % 3]
            if a[0] == b[0]:
                continue
            if a < b:
                kanten[(a, b)] = kanten.get((a, b), 0) + 1
            else:
                kanten[(b, a)] = kanten.get((b, a), 0) - 1
    kanten = {k: g for k, g in kanten.items() if g}
    if len(kanten) > KANTEN_HOECHSTENS:
        return None
    return kanten


def _streifen(kanten) -> tuple | None:
    """Die Deckung der Dachflächen, Streifen für Streifen (Modulkopf).

    Returns:
        ``(vereinigung_m2, doppelt_m2, trapeze)``: die Fläche mit Deckungszahl ab 1, die Fläche mit Deckungszahl ab 2,
        und die Vereinigung als Trapeze ``[[(x, y), …], …]`` (konvex, gegen den Uhrzeigersinn, ohne Überlappung).
        ``None``, wenn die Rechnung mehr als :data:`ARBEIT_HOECHSTENS` Schritte bräuchte.
    """
    arbeit = 0
    liste = sorted(((a[0], a[1], b[0], b[1], g) for (a, b), g in kanten.items()))
    xs = {x for k in liste for x in (k[0], k[2])}
    for i, (ax0, ay0, ax1, ay1, _) in enumerate(liste):          # Kantenschnitte: dort beginnt ein neuer Streifen
        ma = (ay1 - ay0) / (ax1 - ax0)
        for bx0, by0, bx1, by1, _ in liste[i + 1:]:
            if bx0 >= ax1:
                break
            lo, hi = bx0, min(ax1, bx1)
            if hi <= lo:
                continue
            mb = (by1 - by0) / (bx1 - bx0)
            f0 = (ay0 + (lo - ax0) * ma) - (by0 + (lo - bx0) * mb)
            f1 = (ay0 + (hi - ax0) * ma) - (by0 + (hi - bx0) * mb)
            if (f0 > 1e-9 and f1 < -1e-9) or (f0 < -1e-9 and f1 > 1e-9):
                xs.add(lo + (hi - lo) * f0 / (f0 - f1))
                arbeit += 1
                if arbeit > ARBEIT_HOECHSTENS:
                    return None
    xs = sorted(xs)
    vereinigung = doppelt = 0.0
    trapeze: list = []
    aktiv: list = []
    naechste = 0
    for xa, xb in zip(xs, xs[1:]):
        breite = xb - xa
        if breite <= 1e-9:
            continue
        while naechste < len(liste) and liste[naechste][0] <= xa + 1e-12:
            aktiv.append(liste[naechste])
            naechste += 1
        aktiv = [k for k in aktiv if k[2] > xa + 1e-12]
        arbeit += len(aktiv)
        if arbeit > ARBEIT_HOECHSTENS:
            return None
        reihe = []
        for x0, y0, x1, y1, g in aktiv:
            if x1 < xb - 1e-12:                                   # endet im Streifen: nur durch Rundung möglich
                continue
            m = (y1 - y0) / (x1 - x0)
            ya, yb = y0 + (xa - x0) * m, y0 + (xb - x0) * m
            reihe.append(((ya + yb) / 2.0, ya, yb, g))
        reihe.sort()
        w = 0
        unten = None
        for k, (ym, ya, yb, g) in enumerate(reihe):
            w += g
            hoehe = reihe[k + 1][0] - ym if k + 1 < len(reihe) else 0.0
            if hoehe <= 1e-12:
                continue
            if w >= 1:
                vereinigung += hoehe * breite
                if w >= 2:
                    doppelt += hoehe * breite
                if unten is None:
                    unten = (ya, yb)
            elif unten is not None:
                trapeze.append(_trapez(xa, xb, unten, (ya, yb)))
                unten = None
        if unten is not None and reihe:
            trapeze.append(_trapez(xa, xb, unten, reihe[-1][1:3]))
    return vereinigung, doppelt, [t for t in trapeze if len(t) >= 3]


def _trapez(xa, xb, unten, oben) -> list:
    """Das Trapez zwischen zwei Kanten im Streifen ``xa``..``xb``, gegen den Uhrzeigersinn, ohne doppelte Ecken."""
    ecken = [(xa, unten[0]), (xb, unten[1]), (xb, oben[1]), (xa, oben[0])]
    aus = []
    for p in ecken:
        if not aus or abs(p[0] - aus[-1][0]) > 1e-12 or abs(p[1] - aus[-1][1]) > 1e-12:
            aus.append(p)
    if len(aus) > 1 and abs(aus[0][0] - aus[-1][0]) <= 1e-12 and abs(aus[0][1] - aus[-1][1]) <= 1e-12:
        aus.pop()
    return aus


def aus_dreiecken(dreiecke) -> list | None:
    """Der Grundriss eines Teils aus seinen Dreiecken ``[((x, y, z), (x, y, z), (x, y, z)), …]`` (Welt, Z oben).

    Returns:
        Eine Liste konvexer Stücke ``[[(x, y), …], …]`` (gegen den Uhrzeigersinn, ohne Überlappung), oder
        ``None``, wenn der Grundriss nicht sicher lesbar ist (keine Fläche, gemischt gewickelt, zu viele
        Dreiecke oder Stücke). Siehe Modulkopf.
    """
    dreiecke = list(dreiecke or ())
    if not dreiecke or len(dreiecke) > DREIECKE_HOECHSTENS:
        return None
    auf, ab, punkte = [], [], []
    flaeche_auf = flaeche_ab = 0.0
    for d in dreiecke:
        p = [(float(e[0]), float(e[1])) for e in d]
        punkte.extend(p)
        u = _umlauf(p) / 2.0
        if u > FLAECHE_MIN_M2:
            auf.append(p)
            flaeche_auf += u
        elif u < -FLAECHE_MIN_M2:
            ab.append(p[::-1])
            flaeche_ab -= u
    if not auf and not ab:
        return None
    if auf and ab and abs(flaeche_auf - flaeche_ab) > 1e-3 * max(flaeche_auf, flaeche_ab):
        return None                                        # gemischt gewickelt: nicht sicher lesbar
    seite, flaeche = (auf, flaeche_auf) if flaeche_auf >= flaeche_ab else (ab, flaeche_ab)
    huelle = konvexe_huelle(punkte)
    kanten = _randkanten(seite)
    if kanten is None:
        return None                                        # Deckung nicht sicher prüfbar: nicht raten
    deckung = _streifen(kanten)
    if deckung is None:
        return None
    vereinigung, doppelt, trapeze = deckung
    if doppelt > UEBERLAPPUNG_ANTEIL * vereinigung + FLAECHE_MIN_M2:
        return _vereinigung(huelle, vereinigung, trapeze)   # Dächer übereinander (A0322)
    if len(huelle) >= 3:
        fh = _flaeche(huelle)
        if flaeche >= fh * (1 - HUELLE_TOLERANZ) and _gedeckt(huelle, seite):
            return [huelle]
    stuecke = _zusammenlegen(seite)
    if len(stuecke) > STUECKE_HOECHSTENS:
        return None
    return stuecke


def _vereinigung(huelle, vereinigung, trapeze) -> list | None:
    """Der Grundriss aus überlappenden Dachflächen: die Hülle, wenn die Vereinigung sie füllt, sonst die Trapeze der
    Vereinigung, zu möglichst wenigen konvexen Stücken zusammengelegt; ``None`` bei zu vielen Stücken oder wenn die
    Trapeze die gerechnete Fläche nicht ergeben."""
    if vereinigung <= FLAECHE_MIN_M2:
        return None
    if len(huelle) >= 3 and vereinigung >= _flaeche(huelle) * (1 - HUELLE_TOLERANZ):
        return [huelle]
    if abs(sum(_flaeche(t) for t in trapeze) - vereinigung) > 1e-6 * vereinigung + FLAECHE_MIN_M2:
        return None
    stuecke = _zusammenlegen(trapeze)
    if len(stuecke) > STUECKE_HOECHSTENS:
        return None
    return stuecke

