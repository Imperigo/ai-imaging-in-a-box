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

``None`` heisst immer: kein Grundriss, die Box gilt, und ein Stoss an diesem Teil ist nicht beweisbar (die
vorsichtige Seite). Reine Rechnung, ohne Paket, ohne Datei (Visbox-Regel 4).

**Annahme (benannt):** Das Netz kragt nicht über sich selbst aus. Eine Auskragung über einer tieferen Dachfläche
zählt deren Fläche doppelt; die Fläche des Grundrisses ist dann zu gross, seine Form bleibt richtig.
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
    if len(huelle) >= 3:
        fh = _flaeche(huelle)
        if flaeche >= fh * (1 - HUELLE_TOLERANZ) and _gedeckt(huelle, seite):
            return [huelle]
    stuecke = _zusammenlegen(seite)
    if len(stuecke) > STUECKE_HOECHSTENS:
        return None
    return stuecke

