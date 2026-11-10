"""Eichsatz Runde 2 zu A0291: die Paare des Gegenlesens und Reihen quer über jede Schwelle.

Das unabhängige Gegenlesen (Meldung ``gegenlesen-an-steuerung-A0291``, 10.11.2026) fand an 420
eigenen Paaren vier Mängel, die der erste Eichsatz (``fenster_paare.py``) nicht zeigte: Seine
Schwellen lagen in leeren Lücken. Dieser Erzeuger baut die Szene des Gegenlesens nach (Masse aus
der Meldung) und setzt Reihen in kleinen Schritten quer über jede Schwelle der Prüfung.

**Die Szene** (240 x 160): Dach y 0 bis 19, Wand y 20 bis 139 und x 10 bis 229, Boden ab y 140.
Zwei Geschosse (Fenster-Oberkante y 35 und 85), sechs Fenster 20 x 18 je Geschoss ab x 22 im
Abstand 34. ``einzel``: Rahmen zwei Bildpunkte. ``band``: ein Glasstück je Geschoss im ID-Pass,
im KI-Bild Sprossen alle 34 Bildpunkte; ein «Fenster» ist dort ein Abschnitt von 34.

**Die Gruppen.**

* ``a`` bis ``k``: die Fälle des Gegenlesens (ganzes Bild verändert; ein Fenster übermalt dazu;
  Rollladen; Vordachschatten; heller Himmel im Glas; kleine Fenster; am Bildrand angeschnitten;
  halb hinter einem Baum; zwei und drei benachbarte; alle übermalt; ID-Glas grösser als im Bild).
* ``s1``: dunkles Glas in 25 Helligkeiten vor jeder Wand — die Reihe quer über die Schwelle
  «wie die Wand daneben». Nie übermalt; wo es von der Wand nicht zu trennen ist, «nicht messbar».
* ``s2``: Versatz des KI-Bilds 0 bis 6 Bildpunkte, waagrecht und schräg, je Übermalungsart.
* ``s3``: ein bis vier benachbarte übermalte Fenster.
* ``s4``: Helligkeit, Farbstich, Unschärfe und Rauschen über das ganze Bild, in Stufen.
* ``s5``: eine Übermalung, die in Stufen in Glas übergeht (0 = übermalt, 1 = Glas).

**Die Klassen** eines Paars: ``einzeln`` (genau ein Fenster übermalt), ``benachbart`` (zwei oder
drei nebeneinander), ``viele`` (vier nebeneinander), ``alle``, ``gegenfall`` (nichts übermalt)
und ``grenze`` (Rollladen, halb übermalt: zählt weder als Treffer noch als Fehlalarm).

Der Erzeuger braucht numpy (nur in den Proben, nicht im Kern) und ist fest gesät
(``numpy.random.RandomState``, dessen Zahlenfolge über die Fassungen von numpy hinweg gleich bleibt).
"""
from __future__ import annotations

import hashlib

import numpy as np

BREITE, HOEHE = 240, 160
AUSSEN, WAND, GLAS, RAHMEN, DACH, BODEN, BAUM = range(7)
KENNFARBE = {AUSSEN: (0, 0, 0), WAND: (200, 10, 10), GLAS: (10, 200, 30), RAHMEN: (10, 30, 200),
             DACH: (120, 120, 10), BODEN: (90, 60, 20), BAUM: (20, 120, 120)}
TABELLE = [
    {"name": "Fassade", "farbe_srgb_8bit": list(KENNFARBE[WAND])},
    {"name": "Fensterglas", "farbe_srgb_8bit": list(KENNFARBE[GLAS])},
    {"name": "Fensterrahmen", "farbe_srgb_8bit": list(KENNFARBE[RAHMEN])},
    {"name": "Dach", "farbe_srgb_8bit": list(KENNFARBE[DACH])},
    {"name": "Gelaende Vorplatz", "farbe_srgb_8bit": list(KENNFARBE[BODEN])},
    {"name": "Baum", "farbe_srgb_8bit": list(KENNFARBE[BAUM])},
]
#: Name, Wandfarbe, Glasfarbe im Grundbild.
WAENDE = (
    ("weiss", (232, 228, 220), (159, 179, 191)),
    ("beige", (200, 178, 148), (159, 179, 191)),
    ("beton", (150, 150, 148), (110, 132, 156)),
    ("klinker", (150, 88, 70), (159, 179, 191)),
    ("holz", (96, 74, 56), (159, 179, 191)),
)
STIMMUNGEN = ((1.0, 1.0, 1.0), (0.7, 0.72, 0.76), (1.04, 0.93, 0.80), (0.8, 0.84, 0.9))
ARTEN = ("grau", "fassade", "warm")
ANORDNUNGEN = ("einzel", "band")
#: Fenstergrösse: Breite, Höhe, Anzahl je Geschoss, Abstand.
FENSTER = {"normal": (20, 18, 6, 34), "klein-10x12": (10, 12, 10, 21), "klein-8x10": (8, 10, 12, 18)}
#: Die zehn Veränderungen über das ganze Bild (Gruppen a und b).
AENDERUNGEN = {
    "heller": (("hell", 1.10),), "dunkler": (("hell", 0.90),), "farbstich": (("stich", 1.08, 1.0, 0.9),),
    "unscharf": (("unscharf", 1),), "rauschen": (("rausch", 8.0),), "versatz-3-2": (("versatz", 3, 2),),
    "versatz--4-0": (("versatz", -4, 0),), "skaliert": (("skala", 1.03),), "kontrast": (("kontrast", 1.12),),
    "alles": (("hell", 1.10), ("stich", 1.08, 1.0, 0.9), ("unscharf", 1), ("rausch", 8.0),
              ("versatz", 3, 2), ("skala", 1.03), ("kontrast", 1.12)),
}


def _wuerfel(name: str):
    return np.random.RandomState(int.from_bytes(hashlib.sha256(name.encode("utf-8")).digest()[:4], "big"))


def name_von(f: dict) -> str:
    """Der Name eines Falls: eindeutig, lesbar, und zugleich seine Saat."""
    teile = [f["gruppe"], WAENDE[f["wand"]][0], f["anordnung"]]
    if f.get("fenster", "normal") != "normal":
        teile.append(f["fenster"])
    if f.get("art"):
        teile.append(f["art"] + "-" + "+".join(str(n) for n in f.get("uebermalt", ())))
    for schluessel in ("stile", "aenderung", "schatten", "baum", "mix", "fuge", "sonder"):
        if f.get(schluessel) not in (None, "reihum", 7):
            wert = f[schluessel]
            teile.append(f"{schluessel}={wert}" if not isinstance(wert, str) or schluessel == "stile"
                         else wert)
    return "/".join(str(t) for t in teile)


def _geometrie(f: dict) -> dict:
    """Stoff je Bildpunkt im ID-Pass und im Bild, Fensternummer, und die Fenster als Rechtecke."""
    bw, bh, anzahl, abstand = FENSTER[f.get("fenster", "normal")]
    band = f["anordnung"] == "band"
    am_rand = f.get("sonder") == "bildrand"
    x_wand = 0 if am_rand else 10
    bild = np.zeros((HOEHE, BREITE), dtype=np.int8)
    bild[0:20, x_wand:230] = DACH
    bild[20:140, x_wand:230] = WAND
    bild[140:, :] = BODEN
    nummer = np.full((HOEHE, BREITE), -1, dtype=np.int16)
    fenster = []
    x_erst = -10 if am_rand else 22
    for oben in (35, 85):
        for n in range(anzahl):
            x0 = x_erst + n * abstand
            x1 = x0 + (abstand - 1 if band else bw - 1)
            a, b = max(0, x0), min(BREITE - 1, x1)
            if not band:
                bild[oben - 2:oben + bh + 2, max(0, x0 - 2):min(BREITE, x1 + 3)] = RAHMEN
            bild[oben:oben + bh, a:b + 1] = GLAS
            nummer[oben - 2 * (not band):oben + bh + 2 * (not band),
                   max(0, x0 - 2 * (not band)):min(BREITE, x1 + 1 + 2 * (not band))] = len(fenster)
            fenster.append((a, b, oben, oben + bh - 1, x0))
    kennung = bild.copy()
    if f.get("sonder") == "id-groesser":
        # Das Glas im ID-Pass ist rundum zwei Bildpunkte grösser als das Glas im Bild.
        bild[bild == RAHMEN] = WAND
        glas = bild == GLAS
        gross = glas.copy()
        for dy in range(-2, 3):
            for dx in range(-2, 3):
                gross |= np.roll(np.roll(glas, dy, axis=0), dx, axis=1)
        kennung = bild.copy()
        kennung[gross] = GLAS
    baum = None
    if f.get("baum"):
        x_kante, y_mitte = fenster[2][4], 35 + bh // 2
        yy, xx = np.mgrid[0:HOEHE, 0:BREITE]
        baum = (xx - x_kante) ** 2 + (yy - y_mitte) ** 2 <= 15 ** 2
        if f["baum"] == "modell":
            kennung[baum] = BAUM
    return {"bild": bild, "kennung": kennung, "nummer": nummer, "fenster": fenster, "baum": baum,
            "band": band, "bh": bh}


def _korn(rng, form, sigma: float):
    return rng.normal(0.0, sigma, form + (1,)) + rng.normal(0.0, 0.4 * sigma, form + (3,))


def _unscharf(bild):
    rand = np.pad(bild, ((1, 1), (1, 1), (0, 0)), mode="edge")
    return sum(rand[1 + dy:1 + dy + bild.shape[0], 1 + dx:1 + dx + bild.shape[1]]
               for dy in (-1, 0, 1) for dx in (-1, 0, 1)) / 9.0


def _versetzt(bild, dx: int, dy: int):
    r = max(abs(dx), abs(dy))
    if not r:
        return bild
    rand = np.pad(bild, ((r, r), (r, r), (0, 0)), mode="edge")
    return rand[r - dy:r - dy + bild.shape[0], r - dx:r - dx + bild.shape[1]]


def _skaliert(bild, faktor: float):
    yy, xx = np.mgrid[0:bild.shape[0], 0:bild.shape[1]]
    qy = np.clip(np.rint((yy - bild.shape[0] / 2) / faktor + bild.shape[0] / 2), 0, bild.shape[0] - 1)
    qx = np.clip(np.rint((xx - bild.shape[1] / 2) / faktor + bild.shape[1] / 2), 0, bild.shape[1] - 1)
    return bild[qy.astype(int), qx.astype(int)]


def _veraendert(bild, schritte, rng):
    for schritt in schritte or ():
        art = schritt[0]
        if art == "hell":
            bild = bild * schritt[1]
        elif art == "stich":
            bild = bild * np.array(schritt[1:4])
        elif art == "unscharf":
            for _ in range(schritt[1]):
                bild = _unscharf(bild)
        elif art == "rausch":
            bild = bild + rng.normal(0.0, schritt[1], bild.shape)
        elif art == "versatz":
            bild = _versetzt(bild, schritt[1], schritt[2])
        elif art == "skala":
            bild = _skaliert(bild, schritt[1])
        elif art == "kontrast":
            bild = (bild - 128.0) * schritt[1] + 128.0
    return bild


def paar(f: dict) -> dict:
    """Ein Fall → Grundbild, Material-ID und KI-Bild als Listen von Farben, dazu die Ziele."""
    name = name_von(f)
    rng = _wuerfel(name)
    g = _geometrie(f)
    _, wand, glas_grund = WAENDE[f["wand"]]
    bild, nummer, fenster = g["bild"], g["nummer"], g["fenster"]
    form = (HOEHE, BREITE)
    yy, xx = np.mgrid[0:HOEHE, 0:BREITE]
    fest = {DACH: (88, 84, 80), BODEN: (120, 116, 108), AUSSEN: (190, 205, 225), RAHMEN: (70, 70, 72),
            WAND: wand, GLAS: glas_grund}
    grund = np.zeros(form + (3,))
    for stoff, farbe in fest.items():
        grund[bild == stoff] = farbe
    grund += _korn(_wuerfel(name_von(dict(f, art=None, uebermalt=(), aenderung=None, mix=None)) + "/grund"),
                   form, 1.5)
    if f.get("baum") == "modell":
        grund[g["baum"]] = (55, 85, 45)
    # --- das KI-Bild
    wand_ki = np.array(wand) * 0.85 + 0.15 * (sum(wand) / 3.0)
    ki = np.zeros(form + (3,))
    for stoff, farbe in {DACH: (84, 82, 80), BODEN: (118, 114, 108), AUSSEN: (186, 202, 224),
                         RAHMEN: (66, 66, 68)}.items():
        ki[bild == stoff] = farbe
    wandbild = wand_ki + _korn(rng, form, 4.0)
    ki[bild == WAND] = wandbild[bild == WAND]
    stile = f.get("stile", "reihum")
    reihum = ("dunkel", "himmel", "wie-grund")
    streifen = ((xx + 1.3 * yy) % 23) < 4
    glasbild = np.zeros(form + (3,))
    for n, (x0, x1, y0, y1, _) in enumerate(fenster):
        hier = (nummer == n) & (bild == GLAS)
        if isinstance(stile, (tuple, list)) and stile[0] == "dunkel_v":
            stil, v = "dunkel", float(stile[1])
        else:
            stil = reihum[(n + f["wand"]) % 3] if stile == "reihum" else (
                reihum[rng.randint(3)] if stile == "gemischt-hell" and n % 2 else stile)
            v = rng.uniform(40, 70)
        if stil == "dunkel":
            farbe = np.where(streifen[..., None], np.array((150.0, 168.0, 186.0)), np.array((v, v + 8, v + 18)))
        elif stil in ("hell", "gemischt-hell"):
            anteil = ((yy - y0) / max(1, y1 - y0))[..., None]
            farbe = np.array((228.0, 236.0, 250.0)) * (1 - anteil) + np.array((208.0, 222.0, 242.0)) * anteil
        elif stil == "himmel":
            anteil = ((yy - y0) / max(1, y1 - y0))[..., None]
            farbe = np.array((175.0, 198.0, 222.0)) * (1 - anteil) + np.array((150.0, 172.0, 198.0)) * anteil
        else:
            farbe = np.broadcast_to(np.array(glas_grund) * rng.uniform(0.94, 1.03), form + (3,))
        glasbild[hier] = farbe[hier]
    glasbild += _korn(rng, form, 6.0)
    if g["band"]:
        for n, (x0, x1, y0, y1, roh) in enumerate(fenster):
            if roh >= 0:
                glasbild[y0:y1 + 1, roh:roh + 2] = (62, 62, 64)          # die Sprosse
    ki[bild == GLAS] = glasbild[bild == GLAS]
    # --- die Übermalung, im selben Licht wie das Bild
    art = f.get("art")
    for n in f.get("uebermalt", ()):
        hier = nummer == n
        if g["band"]:
            hier = hier & (bild == GLAS)
        if art == "grau":
            farbe = (rng.uniform(155, 180) + np.where(xx % 3 == 0, -4.0, 0.0))[..., None] * np.ones(3) \
                + _korn(rng, form, 5.0)
        elif art == "fassade":
            farbe = wand_ki + _korn(rng, form, 4.0)
        elif art == "warm":
            ton = np.array((rng.uniform(215, 240), rng.uniform(165, 190), rng.uniform(70, 100)))
            farbe = ton * np.where(xx % int(f.get("fuge", 7)) == 0, 0.5, 1.0)[..., None] + _korn(rng, form, 8.0)
        else:                                                         # der Rollladen
            farbe = np.array((178.0, 174.0, 166.0)) * np.where(yy % 3 == 0, 0.75, 1.0)[..., None] \
                + _korn(rng, form, 4.0)
        if f.get("mix") is not None:
            farbe = f["mix"] * ki + (1.0 - f["mix"]) * farbe
        ki[hier] = farbe[hier]
    ki = ki * np.array(STIMMUNGEN[f.get("stimmung", 0)])
    if f.get("schatten"):
        ki[f["schatten"][0]:f["schatten"][1]] *= 0.5
    if f.get("baum"):
        ki[g["baum"]] = (np.array((50.0, 82.0, 40.0)) + _korn(rng, form, 12.0))[g["baum"]]
    ki = _veraendert(ki, f.get("aenderung_schritte") or AENDERUNGEN.get(f.get("aenderung")), rng)

    def liste(feld):
        return list(map(tuple, np.clip(np.rint(feld), 0, 255).astype(int).reshape(-1, 3).tolist()))
    kennfarben = np.array([KENNFARBE[s] for s in range(7)])
    ziele = []
    for n in f.get("uebermalt", ()):
        x0, x1, y0, y1, _ = fenster[n]
        ziele.append({"x0": x0, "y0": y0, "x1": x1, "y1": y1})
    return {"name": name, "fall": f, "klasse": f["klasse"], "ziele": ziele, "breite": BREITE,
            "hoehe": HOEHE, "ki": liste(ki), "grund": liste(grund),
            "kennung": list(map(tuple, kennfarben[g["kennung"]].reshape(-1, 3).tolist())),
            "tabelle": TABELLE}


def faelle() -> list:
    """Alle Fälle der Runde 2, ohne Bilder (die rechnet :func:`paar`)."""
    aus = []

    def dazu(gruppe, klasse, wand, anordnung, **mehr):
        aus.append(dict(gruppe=gruppe, klasse=klasse, wand=wand, anordnung=anordnung, **mehr))

    zaehler = 0
    for w in range(5):
        for a, anordnung in enumerate(ANORDNUNGEN):
            for k, aenderung in enumerate(AENDERUNGEN):
                zaehler += 1
                # a · nichts übermalt, das ganze Bild verändert
                dazu("a", "gegenfall", w, anordnung, aenderung=aenderung, stimmung=(w + k) % 4)
                # b · ein Fenster übermalt, dieselbe Veränderung
                dazu("b", "einzeln", w, anordnung, aenderung=aenderung, stimmung=(w + k) % 4,
                     art=ARTEN[zaehler % 3], uebermalt=((zaehler * 5) % 12,))
            # c · Rollladen: weder Treffer noch Fehlalarm
            dazu("c", "grenze", w, anordnung, art="rollladen", uebermalt=((w * 3 + a) % 12,))
            # d · Vordachschatten, die zweite Kante mitten durch die oberen Fenster
            for schatten in ((20, 60), (20, 44)):
                dazu("d", "gegenfall", w, anordnung, schatten=schatten)
            # e · heller Himmel im Glas, alle Scheiben oder gemischt
            for stile in ("hell", "gemischt-hell"):
                dazu("e", "gegenfall", w, anordnung, stile=stile)
            # g · am Bildrand angeschnitten
            dazu("g", "gegenfall", w, anordnung, sonder="bildrand")
            dazu("g", "einzeln", w, anordnung, sonder="bildrand", art=ARTEN[(w + a) % 3],
                 uebermalt=(0 if (w + a) % 2 else 3,))
            # h · halb hinter einem Baum, nur im KI-Bild oder auch im Modell
            for baum in ("ki", "modell"):
                dazu("h", "gegenfall", w, anordnung, baum=baum)
            # i · zwei und drei benachbarte, je Art
            for k, art in enumerate(ARTEN):
                erstes = (w + k) % 3 + 1
                dazu("i", "benachbart", w, anordnung, art=art, uebermalt=(erstes, erstes + 1))
                dazu("i", "benachbart", w, anordnung, art=art, uebermalt=(erstes, erstes + 1, erstes + 2))
                # j · alle Fenster übermalt
                dazu("j", "alle", w, anordnung, art=art, uebermalt=tuple(range(12)))
            # k · das Glas im ID-Pass ist zwei Bildpunkte grösser als im Bild
            dazu("k", "gegenfall", w, anordnung, sonder="id-groesser")
            for k, art in enumerate(ARTEN):
                dazu("k", "einzeln", w, anordnung, sonder="id-groesser", art=art, uebermalt=((w + 2 * k) % 12,))
        # f · kleine Fenster
        for groesse in ("klein-10x12", "klein-8x10"):
            dazu("f", "gegenfall", w, "einzel", fenster=groesse)
            dazu("f", "einzeln", w, "einzel", fenster=groesse, art=ARTEN[w % 3], uebermalt=(w + 2,))
        # s1 · dunkles Glas in 25 Helligkeiten: quer über die Schwelle «wie die Wand daneben»
        for v in range(30, 155, 5):
            dazu("s1", "gegenfall", w, ANORDNUNGEN[(v // 5 + w) % 2], stile=("dunkel_v", v))
        # s2 · Versatz 0 bis 6, waagrecht und schräg
        for dx in range(7):
            dazu("s2", "gegenfall", w, ANORDNUNGEN[(dx + w) % 2], aenderung_schritte=(("versatz", dx, 0),),
                 aenderung=f"versatz-{dx}-0")
            for k, art in enumerate(ARTEN):
                dazu("s2", "einzeln" if dx <= 4 else "einzeln-weit", w, ANORDNUNGEN[(dx + w + k) % 2], art=art,
                     uebermalt=((w + dx + 4 * k) % 12,), aenderung_schritte=(("versatz", dx, 0),),
                     aenderung=f"versatz-{dx}-0")
        for dx, dy in ((0, 3), (3, 3), (-4, -2)):
            for k, art in enumerate(ARTEN):
                dazu("s2", "einzeln", w, ANORDNUNGEN[(dx + w + k) % 2], art=art,
                     uebermalt=((w + 3 * k + dy) % 12,), aenderung_schritte=(("versatz", dx, dy),),
                     aenderung=f"versatz-{dx}-{dy}")
        # s3 · ein bis vier benachbarte im Band, zwei und drei grau auch als Einzelfenster
        for anzahl in (1, 2, 3, 4):
            for k, art in enumerate(ARTEN):
                erstes = 6 * ((w + k) % 2) + (w + anzahl) % 2
                dazu("s3", ("einzeln", "benachbart", "benachbart", "viele")[anzahl - 1], w, "band", art=art,
                     uebermalt=tuple(range(erstes, erstes + anzahl)), stimmung=(w + anzahl) % 4)
        for anzahl in (2, 3):
            dazu("s3", "benachbart", w, "einzel", art="grau", uebermalt=tuple(range(1, 1 + anzahl)))
        # s4 · Helligkeit, Farbstich, Unschärfe, Rauschen in Stufen, je mit und ohne Übermalung
        stufen = [("hell", h) for h in (0.7, 0.8, 0.9, 1.1, 1.2, 1.3)] \
            + [("stich", 1.0 + 0.03 * s, 1.0, 1.0 - 0.04 * s) for s in range(1, 6)] \
            + [("unscharf", 1), ("unscharf", 2)] + [("rausch", float(s)) for s in (4, 8, 12, 16)]
        for k, stufe in enumerate(stufen):
            kurz = "-".join(str(t) for t in stufe)
            dazu("s4", "gegenfall", w, ANORDNUNGEN[(k + w) % 2], aenderung_schritte=(stufe,), aenderung=kurz)
            dazu("s4", "einzeln", w, ANORDNUNGEN[(k + w) % 2], aenderung_schritte=(stufe,), aenderung=kurz,
                 art=ARTEN[(k + w) % 3], uebermalt=((3 * k + w) % 12,))
        # s5 · eine Übermalung geht in Stufen in Glas über
        for stufe in range(11):
            mix = stufe / 10.0
            dazu("s5", "einzeln" if mix <= 0.2 else ("gegenfall" if mix >= 0.8 else "grenze"), w,
                 ANORDNUNGEN[(stufe + w) % 2], art="fassade", uebermalt=((stufe + 2 * w) % 12,), mix=mix)
    return aus


def _flaeche(a: dict) -> int:
    return (a["x1"] - a["x0"] + 1) * (a["y1"] - a["y0"] + 1)


def _schnitt(a: dict, b: dict, luft: int = 0) -> int:
    bx = min(a["x1"], b["x1"] + luft) - max(a["x0"], b["x0"] - luft) + 1
    by = min(a["y1"], b["y1"] + luft) - max(a["y0"], b["y0"] - luft) + 1
    return bx * by if bx > 0 and by > 0 else 0


def werte(p: dict, bauteile) -> dict:
    """Ein Paar gegen den Befund je Bauteil.

    Ein Fund ist **richtig**, wenn mindestens die Hälfte seiner Fläche in der Hülle der übermalten
    Fenster liegt (mit zwei Bildpunkten Luft); jeder andere Fund ist ein Fehlalarm. Ein
    übermaltes Fenster ist **gefunden**, wenn richtige Funde mindestens die Hälfte seiner Fläche
    decken, und **nicht messbar**, wenn stattdessen ein Bauteil «nicht messbar» das tut. Ein Paar
    ist erkannt, wenn jedes seiner übermalten Fenster gefunden ist.
    """
    funde = [b for b in bauteile or () if b.get("urteil") == "uebermalt"]
    unklar = [b for b in bauteile or () if b.get("urteil") == "nicht messbar"]
    ziele = p["ziele"]
    if not ziele or p["klasse"] == "gegenfall":
        return {"erkannt": None, "fehlalarme": len(funde), "nicht_messbar": None,
                "unklar": len(unklar)}
    huelle = {"x0": min(z["x0"] for z in ziele), "y0": min(z["y0"] for z in ziele),
              "x1": max(z["x1"] for z in ziele), "y1": max(z["y1"] for z in ziele)}
    richtig = [b for b in funde if _schnitt(b["ort"], huelle, 2) >= 0.5 * _flaeche(b["ort"])]
    gefunden = [sum(_schnitt(z, b["ort"]) for b in richtig) >= 0.5 * _flaeche(z) for z in ziele]
    offen = [sum(_schnitt(z, b["ort"]) for b in unklar) >= 0.5 * _flaeche(z) for z in ziele]
    erkannt = all(gefunden)
    return {"erkannt": erkannt, "fehlalarme": len(funde) - len(richtig),
            "nicht_messbar": (not erkannt) and all(g or o for g, o in zip(gefunden, offen)),
            "gefunden": sum(gefunden), "ziele": len(ziele), "unklar": len(unklar)}


def pruefe(f: dict) -> dict:
    """Ein Fall durch ``varianten.fenster_gehalten`` — das, was ein Arbeiter des Prüfwegs tut."""
    from aiimaging import varianten  # noqa: PLC0415
    p = paar(f)
    befund = varianten.fenster_gehalten(
        p["ki"], p["grund"], p["kennung"], varianten.glasfarben(TABELLE),
        ausser=varianten.nicht_fassade_farben(TABELLE), breite=p["breite"])
    return {"name": p["name"], "gruppe": f["gruppe"], "klasse": p["klasse"], "fall": f, "ziele": p["ziele"],
            "gehalten": befund.get("gehalten"), "anteil": befund.get("anteil"),
            "band_nicht_gehalten": befund.get("band_nicht_gehalten"),
            "bauteile": befund.get("bauteile"), "hinweis": befund.get("bauteil_hinweis"),
            "wert": werte(p, befund.get("bauteile"))}


def miss(auswahl=None, prozesse: int | None = None) -> dict:
    """Der Prüfweg der Runde 2: alle Fälle (oder eine Auswahl von Gruppen), ausgezählt."""
    import os  # noqa: PLC0415
    liste = [f for f in faelle() if auswahl is None or f["gruppe"] in auswahl]
    prozesse = prozesse or min(8, os.cpu_count() or 1)
    if prozesse > 1:
        import multiprocessing  # noqa: PLC0415
        with multiprocessing.get_context("fork" if hasattr(os, "fork") else "spawn").Pool(prozesse) as becken:
            ergebnisse = becken.map(pruefe, liste, chunksize=8)
    else:
        ergebnisse = [pruefe(f) for f in liste]
    return auszaehlen(ergebnisse)


def auszaehlen(ergebnisse: list) -> dict:
    aus = {"paare": len(ergebnisse), "fehlalarme": 0, "falsch": [], "klassen": {}, "gruppen": {},
           "ergebnisse": {e["name"]: e for e in ergebnisse}}
    for e in ergebnisse:
        w = e["wert"]
        zeile = aus["klassen"].setdefault(e["klasse"], {"paare": 0, "erkannt": 0, "nicht_messbar": 0,
                                                        "verfehlt": [], "fehlalarme": 0})
        gruppe = aus["gruppen"].setdefault(e["gruppe"], {"paare": 0, "uebermalt": 0, "erkannt": 0,
                                                         "nicht_messbar": 0, "fehlalarme": 0})
        zeile["paare"] += 1
        gruppe["paare"] += 1
        if e["klasse"] == "grenze":
            continue                                # zählt weder als Treffer noch als Fehlalarm
        if e["klasse"] != "alle":
            zeile["fehlalarme"] += w["fehlalarme"]
            gruppe["fehlalarme"] += w["fehlalarme"]
            aus["fehlalarme"] += w["fehlalarme"]
            if w["fehlalarme"]:
                aus["falsch"].append(e["name"])
        if w["erkannt"] is not None:
            gruppe["uebermalt"] += 1
            zeile["erkannt"] += bool(w["erkannt"])
            gruppe["erkannt"] += bool(w["erkannt"])
            zeile["nicht_messbar"] += bool(w["nicht_messbar"])
            gruppe["nicht_messbar"] += bool(w["nicht_messbar"])
            if not w["erkannt"] and not w["nicht_messbar"]:
                zeile["verfehlt"].append(e["name"])
    for zeile in aus["klassen"].values():
        messbar = zeile["paare"] - zeile["nicht_messbar"]
        zeile["rate"] = zeile["erkannt"] / messbar if messbar else None
        zeile["anteil_nicht_messbar"] = zeile["nicht_messbar"] / zeile["paare"] if zeile["paare"] else None
    return aus


if __name__ == "__main__":      # python tests/fenster_paare2.py [gruppe ...] — die Zahlen der Meldung
    import sys
    sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[1] / "src"))
    m = miss(set(sys.argv[1:]) or None)
    print(f"Runde 2: {m['paare']} Paare, Fehlalarme {m['fehlalarme']}")
    for klasse, z in sorted(m["klassen"].items()):
        if klasse in ("gegenfall", "grenze"):
            print(f"  {klasse}: {z['paare']} Paare, Fehlalarme {z['fehlalarme']}")
        else:
            rate = "-" if z["rate"] is None else f"{z['rate']:.1%}"
            print(f"  {klasse}: erkannt {z['erkannt']} von {z['paare']} ({rate} der messbaren), nicht messbar "
                  f"{z['nicht_messbar']}, Fehlalarme {z['fehlalarme']}")
    for gruppe, z in sorted(m["gruppen"].items()):
        print(f"  Gruppe {gruppe}: {z['paare']} Paare, erkannt {z['erkannt']}/{z['uebermalt']}, nicht messbar "
              f"{z['nicht_messbar']}, Fehlalarme {z['fehlalarme']}")
    for klasse, z in sorted(m["klassen"].items()):
        for name in z["verfehlt"]:
            print("  VERFEHLT", name)
    for name in m["falsch"]:
        print("  FEHLALARM", name)
