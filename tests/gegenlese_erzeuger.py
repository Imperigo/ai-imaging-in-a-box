"""Zweiter Erzeuger synthetischer Bildpaare (Grundbild, KI-Bild, Bauwerksmaske).

Nachgebaut nach den Massen des Gegenlesens A0300 vom 10.11.2026; unabhaengig von
anlagen_erzeuger.py; synthetisch, keine echten Projektdaten. Reine Standardbibliothek,
alles haengt allein am Startwert (und den Parametern), also deterministisch.
"""

import math
import random

BREITE, HOEHE = 320, 200
N = BREITE * HOEHE
GRUEN5 = [(58, 104, 52), (96, 146, 78), (134, 172, 104), (40, 78, 44), (112, 158, 92)]
FENSTER = (78, 78, 82)
LUFT = 4


def _kl(v):
    v = int(round(v))
    return 0 if v < 0 else 255 if v > 255 else v


def _rausch(rng, n, basis, amp):
    """n Farben um `basis`, je Kanal gleichverteilt +-amp."""
    d = rng.randbytes(3 * n)
    m = 2 * amp + 1
    t = [[_kl(basis[c] - amp + (b % m)) for b in range(256)] for c in range(3)]
    return list(zip(map(t[0].__getitem__, d[0::3]),
                    map(t[1].__getitem__, d[1::3]),
                    map(t[2].__getitem__, d[2::3])))


def _fuell(img, x0, y0, x1, y1, wert):
    x0, y0 = max(x0, 0), max(y0, 0)
    x1, y1 = min(x1, BREITE), min(y1, HOEHE)
    if x1 <= x0 or y1 <= y0:
        return
    z = [wert] * (x1 - x0)
    for y in range(y0, y1):
        img[y * BREITE + x0:y * BREITE + x1] = z


def _ring(img, box, hof, wert):
    x0, y0, x1, y1 = box
    hx0, hy0, hx1, hy1 = hof
    _fuell(img, x0, y0, x1, hy0, wert)
    _fuell(img, x0, hy1, x1, y1, wert)
    _fuell(img, x0, hy0, hx0, hy1, wert)
    _fuell(img, hx1, hy0, x1, hy1, wert)


def _schneidet(x0, y0, x1, y1, k):
    return x0 < k[2] and x1 > k[0] and y0 < k[3] and y1 > k[1]


def _frei(box, andere):
    for o in andere:
        if not (box[2] + LUFT <= o[0] or o[2] + LUFT <= box[0]
                or box[3] + LUFT <= o[1] or o[3] + LUFT <= box[1]):
            return False
    return True


def _anordnung(rng, ha, gross, beruehrt):
    if gross:
        return ((4, 4, 222, 196), (90, 80, 136, 120),
                [(230, 4, 316, 65), (230, 69, 316, 130), (230, 134, 316, 196)])
    flaeche = ha * N
    kast = 0.55 * flaeche / 0.75          # Hof = 1/4 des Kastens, Ring = 3/4
    w = int(round(math.sqrt(kast * 1.4)))
    h = int(round(w / 1.4))
    w = max(16, min(w, 296 if beruehrt else 312))
    h = max(12, min(h, 192))
    hw, hh = w // 2, h // 2
    if beruehrt:
        x0 = rng.randint(4, 310 - w)
    elif rng.random() < 0.5:
        x0 = rng.choice((4, 316 - w))
    else:
        x0 = rng.randint(4, 316 - w)
    y0 = rng.randint(4, 196 - h)
    haupt = (x0, y0, x0 + w, y0 + h)
    hx0, hy0 = x0 + (w - hw) // 2, y0 + (h - hh) // 2
    hof = (hx0, hy0, hx0 + hw, hy0 + hh)
    rest = 0.45 * flaeche
    n = rng.randint(2, 4)
    gew = [rng.uniform(0.5, 1.5) for _ in range(n)]
    s = sum(gew)
    neben = []
    for i in range(n):
        a = rest * gew[i] / s
        nw = math.sqrt(a * rng.uniform(0.6, 1.7))
        nh = a / nw
        massstab = 1.0
        for versuch in range(600):
            if versuch % 30 == 29:
                massstab *= 0.92
            cw = min(312, max(6, int(nw * massstab)))
            ch = min(192, max(6, int(nh * massstab)))
            if i == 0 and beruehrt:
                cw = min(cw, 316 - haupt[2])
                ch = min(ch, h)
                if cw < 6:
                    break
                y = rng.randint(haupt[1], haupt[3] - ch)
                neben.append((haupt[2], y, haupt[2] + cw, y + ch))
                break
            x = rng.randint(4, 316 - cw)
            y = rng.randint(4, 196 - ch)
            box = (x, y, x + cw, y + ch)
            if _frei(box, [haupt] + neben):
                neben.append(box)
                break
    return haupt, hof, neben


def _fenstergitter(box, hof, w, h, px, py):
    x0, y0, x1, y1 = box
    res = []
    y = y0 + 3
    while y + h <= y1 - 3:
        x = x0 + 3
        while x + w <= x1 - 3:
            if hof is None or not _schneidet(x - 3, y - 3, x + w + 3, y + h + 3, hof):
                res.append((x, y, w, h))
            x += px
        y += py
    return res


def _kreise(img, kr, box, anzahl, rmin, rmax, zentren=None, region=None):
    x0, y0, x1, y1 = box
    for _ in range(anzahl):
        r = kr.randint(rmin, rmax)
        col = kr.choice(GRUEN5)
        if zentren is None:
            cx, cy = kr.randint(x0, x1 - 1), kr.randint(y0, y1 - 1)
        else:
            cx, cy = divmod(kr.choice(zentren), BREITE)[::-1]
        for dy in range(-r, r + 1):
            y = cy + dy
            if y < y0 or y >= y1:
                continue
            half = int(math.sqrt(r * r - dy * dy))
            xa, xb = max(x0, cx - half), min(x1, cx + half + 1)
            if xb <= xa:
                continue
            if region is None:
                img[y * BREITE + xa:y * BREITE + xb] = [col] * (xb - xa)
            else:
                for x in range(xa, xb):
                    if region[y * BREITE + x]:
                        img[y * BREITE + x] = col


# ---------------------------------------------------------------- Stoerungen

def _tabelle(f):
    return [_kl(v * f) for v in range(256)]


def _hell(img, f):
    t = _tabelle(f)
    return [(t[r], t[g], t[b]) for r, g, b in img]


def _stich(img, f):
    ta, tb, tc = _tabelle(f[0]), _tabelle(f[1]), _tabelle(f[2])
    return [(ta[r], tb[g], tc[b]) for r, g, b in img]


def _korn(img, sr, sigma):
    ga = sr.gauss
    return [(_kl(r + ga(0, sigma)), _kl(g + ga(0, sigma)), _kl(b + ga(0, sigma)))
            for r, g, b in img]


def _blur(img):
    W = BREITE
    out = []
    for c in range(3):
        ch = [p[c] for p in img]
        h = []
        for y in range(HOEHE):
            row = ch[y * W:(y + 1) * W]
            l = [row[0]] + row[:-1]
            r = row[1:] + [row[-1]]
            h.extend([a + b + d for a, b, d in zip(l, row, r)])
        v = []
        for y in range(HOEHE):
            up = h[max(y - 1, 0) * W:max(y - 1, 0) * W + W]
            cur = h[y * W:(y + 1) * W]
            dn = h[min(y + 1, HOEHE - 1) * W:min(y + 1, HOEHE - 1) * W + W]
            v.extend([(a + b + d + 4) // 9 for a, b, d in zip(up, cur, dn)])
        out.append(v)
    return list(zip(*out))


def _versatz(img, dx, dy):
    xs = [min(BREITE - 1, max(0, x - dx)) for x in range(BREITE)]
    neu = []
    for y in range(HOEHE):
        sy = min(HOEHE - 1, max(0, y - dy))
        row = img[sy * BREITE:(sy + 1) * BREITE]
        neu.extend([row[i] for i in xs])
    return neu


def _skala(img, f):
    xs = [min(BREITE - 1, max(0, int(math.floor((x + 0.5 - BREITE / 2) / f + BREITE / 2))))
          for x in range(BREITE)]
    ys = [min(HOEHE - 1, max(0, int(math.floor((y + 0.5 - HOEHE / 2) / f + HOEHE / 2))))
          for y in range(HOEHE)]
    neu = []
    for sy in ys:
        row = img[sy * BREITE:(sy + 1) * BREITE]
        neu.extend([row[i] for i in xs])
    return neu


def _stoere(img, sr, liste):
    for name, wert in liste:
        if name == "hell":
            img = _hell(img, wert)
        elif name == "stich":
            img = _stich(img, wert)
        elif name == "blur":
            for _ in range(int(wert)):
                img = _blur(img)
        elif name == "korn":
            img = _korn(img, sr, wert)
        elif name == "versatz":
            img = _versatz(img, int(wert[0]), int(wert[1]))
        elif name == "skala":
            img = _skala(img, wert)
        else:
            raise ValueError(f"unbekannte Stoerung: {name}")
    return img


# --------------------------------------------------------------------- paar

def paar(startwert: int, zustand: str = "intakt", *, teil: float = 0.0, stoerungen=(),
         pflaster=None, hausanteil=None, fensterfarbe_ki=None, glatt_im_grundbild=False,
         beruehrt=False, gross=False, nebenbau_verschoben=False) -> dict:
    zustaende = ("intakt", "flecken", "platte", "glatt", "baeume", "wiese", "teil")
    if zustand not in zustaende:
        raise ValueError(f"unbekannter Zustand: {zustand}")
    rng = random.Random(f"grund-{startwert}")
    ha_vorgabe = rng.uniform(0.15, 0.55)
    ha = ha_vorgabe if hausanteil is None else hausanteil
    haupt, hof, neben = _anordnung(rng, ha, gross, beruehrt)

    maske = bytearray(N)
    _ring(maske, haupt, hof, 1)
    for b in neben:
        _fuell(maske, *b, 1)

    bg = _rausch(rng, N, (118, 126, 108), 5)
    if pflaster:
        kontrast, zelle = pflaster
        prng = random.Random(f"pflaster-{startwert}")
        nzx, nzy = -(-BREITE // zelle), -(-HOEHE // zelle)
        off = [[prng.randint(-kontrast, kontrast) for _ in range(nzx)] for _ in range(nzy)]
        for y in range(HOEHE):
            orow = off[y // zelle]
            for x in range(BREITE):
                i = y * BREITE + x
                o = orow[x // zelle]
                if o and not maske[i]:
                    r, g, b = bg[i]
                    bg[i] = (_kl(r + o), _kl(g + o), _kl(b + o))

    # Bauten: (Kasten, Hof oder None, Fassadenfarbe, Fenster, Rasterweite x)
    bauten = []
    for k, box in enumerate([haupt] + neben):
        gr = rng.randint(200, 220)
        fw, fh = rng.randint(2, 4), rng.randint(2, 4)
        px, py = fw + rng.randint(3, 5), fh + rng.randint(3, 5)
        h_ = hof if k == 0 else None
        bauten.append((box, h_, (gr, gr, gr), _fenstergitter(box, h_, fw, fh, px, py), px))

    grund = list(bg)
    for k, (box, h_, col, wins, px) in enumerate(bauten):
        if h_ is not None:
            _ring(grund, box, h_, col)
        else:
            _fuell(grund, *box, col)
        if k == 0 and glatt_im_grundbild:
            continue
        for (x, y, w, h) in wins:
            _fuell(grund, x, y, x + w, y + h, FENSTER)

    # ------------------------------------------------------------- KI-Bild
    kr = random.Random(f"ki-{startwert}-{zustand}-{teil}")
    ton = kr.uniform(0.92, 1.06)
    fg = kr.randint(64, 80) if fensterfarbe_ki is None else int(fensterfarbe_ki)
    fcol = (_kl(fg),) * 3
    ki = list(grund)
    ox_neben = 0
    if nebenbau_verschoben and neben:
        b0 = neben[0]
        for y in range(max(b0[1], 0), min(b0[3], HOEHE)):
            ki[y * BREITE + b0[0]:y * BREITE + b0[2]] = bg[y * BREITE + b0[0]:y * BREITE + b0[2]]
        ox_neben = (b0[2] - b0[0]) // 2

    def male_bau(k, mit_fenster=True):
        box, h_, col, wins, px = bauten[k]
        ox = ox_neben if (k == 1 and nebenbau_verschoben) else 0
        x0, y0, x1, y1 = box
        if h_ is not None:
            _ring(ki, box, h_, col)
        else:
            _fuell(ki, x0 + ox, y0, x1 + ox, y1, col)
        for (x, y, w, h) in wins:
            weg = kr.random() < 0.12
            dx = kr.choice((-1, 0, 1))
            neu = kr.random() < 0.06
            if mit_fenster:
                if not weg:
                    _fuell(ki, x + dx + ox, y, x + dx + ox + w, y + h, fcol)
                if neu:
                    nx = x + px // 2
                    if (nx + w <= x1 and
                            (h_ is None or not _schneidet(nx, y, nx + w, y + h, h_))):
                        _fuell(ki, nx + ox, y, nx + ox + w, y + h, fcol)

    bx0, by0, bx1, by1 = haupt
    bw, bh = bx1 - bx0, by1 - by0
    mpunkte = bw * bh - (hof[2] - hof[0]) * (hof[3] - hof[1])
    gedeckt = 0.0
    if zustand == "intakt":
        male_bau(0)
    elif zustand == "glatt":
        male_bau(0, mit_fenster=False)
        gedeckt = 1.0
    elif zustand == "platte":
        _fuell(ki, bx0, by0, bx1, by1, (178, 180, 174))
        gedeckt = 1.0
    elif zustand == "wiese":
        farben = _rausch(kr, bw * bh, (70, 110, 60), 8)
        for j in range(bh):
            ki[(by0 + j) * BREITE + bx0:(by0 + j) * BREITE + bx1] = farben[j * bw:(j + 1) * bw]
        gedeckt = 1.0
    elif zustand == "flecken":
        _fuell(ki, bx0, by0, bx1, by1, (60, 96, 50))
        _kreise(ki, kr, haupt, bw * bh // 25, 4, 10)
        gedeckt = 1.0
    elif zustand == "baeume":
        _fuell(ki, bx0, by0, bx1, by1, (60, 96, 50))
        _kreise(ki, kr, haupt, bw * bh // 6, 2, 4)
        gedeckt = 1.0
    else:  # teil
        male_bau(0)
        while True:
            sx, sy = kr.randint(bx0, bx1 - 1), kr.randint(by0, by1 - 1)
            if not (hof[0] <= sx < hof[2] and hof[1] <= sy < hof[3]):
                break
        ziel = max(0.0, min(1.0, teil)) * mpunkte
        ds = [(bx0 + i % bw - sx) ** 2 + (by0 + i // bw - sy) ** 2 for i in range(bw * bh)]
        region = bytearray(N)
        zentren = []
        zaehl = 0
        for i in sorted(range(bw * bh), key=ds.__getitem__):
            if zaehl >= ziel:
                break
            x, y = bx0 + i % bw, by0 + i // bw
            idx = y * BREITE + x
            region[idx] = 1
            zentren.append(idx)
            ki[idx] = (60, 96, 50)
            if not (hof[0] <= x < hof[2] and hof[1] <= y < hof[3]):
                zaehl += 1
        if zentren:
            _kreise(ki, kr, haupt, len(zentren) // 25, 4, 10, zentren=zentren, region=region)
        gedeckt = zaehl / mpunkte if mpunkte else 0.0

    for k in range(1, len(bauten)):
        male_bau(k)

    t = _tabelle(ton)
    ki = [(t[r], t[g], t[b]) for r, g, b in ki]
    if stoerungen:
        sr = random.Random(f"stoerung-{startwert}-{zustand}-{teil}")
        ki = _stoere(ki, sr, list(stoerungen))

    mliste = list(map(bool, maske))
    return {
        "name": f"{zustand}-{startwert}", "zustand": zustand, "startwert": startwert,
        "breite": BREITE, "hoehe": HOEHE, "grund": grund, "ki": ki, "maske": mliste,
        "haupt": haupt, "hof": hof, "neben": list(neben),
        "hausanteil": sum(maske) / N, "gedeckt": gedeckt,
    }
