"""Erzeuger des synthetischen Eichsatzes «Masstreue je Bauteil» (A0291).

Jedes Paar besteht aus einem Grundbild, dem Material-ID-Pass und einem «KI-Bild», alle drei
gerechnet, nichts davon aus einem echten Auftrag (Regel 3). Der Erzeuger ist fest gesät: derselbe
Aufruf liefert dieselben Bildpunkte.

**Was er nachstellt, und woher die Zahlen kommen.** Die Farben des Glases im Grundbild (159, 179,
191), die Streuung des gehaltenen KI-Glases und das Aussehen der beiden echten Übermalungen (graue
Lattung, warmes Holz mit dunklen Fugen) sind an den Eichdaten von A0092 und A0158 abgelesen
(``tests/fixtures/glas-v4``, ``glas-v5``). Dort ist auch belegt, dass ein Fensterband im ID-Pass
EIN zusammenhängendes Glasstück ohne Sprossen ist; darum gibt es hier zwei Anordnungen:

* ``einzel``: getrennte Fenster mit Rahmen, jedes ein eigenes Glasbauteil im ID-Pass.
* ``band``: ein durchgehendes Glasband je Geschoss; die einzelnen Fenster zeigt nur das KI-Bild.

**Die Fälle.** Je Szene (fünf Fassaden mal drei Blickrichtungen) drei Paare mit genau EINEM
übermalten Fenster (grau, Fassadenfarbe, warm) und vier Gegenfälle ohne Übermalung (dunkel
spiegelndes Glas, Schatten quer über die Fassade, Vorhang, gemischte Scheiben). Der Blick von oben
ist kein eigener Fall, sondern eine der drei Blickrichtungen, in der alle sieben Fälle vorkommen.

**Der Vorhang** liegt hinter der Scheibe: Je steiler der Blick, desto mehr spiegelt das Glas und
desto weniger scheint er durch (Gewicht 0,55 auf Augenhöhe, 0,35 erhöht, 0,15 von oben). Er deckt
höchstens 45 % eines Fensters.
"""
from __future__ import annotations

import functools
import math
import random

BREITE, HOEHE = 200, 124
KORN_TAFEL = 4093

AUSSEN, WAND, GLAS, RAHMEN, DACH, BODEN = range(6)
KENNFARBE = {AUSSEN: (0, 0, 0), WAND: (200, 10, 10), GLAS: (10, 200, 30),
             RAHMEN: (10, 30, 200), DACH: (120, 120, 10), BODEN: (90, 60, 20)}
TABELLE = [
    {"name": "Fassade", "farbe_srgb_8bit": list(KENNFARBE[WAND])},
    {"name": "Fensterglas", "farbe_srgb_8bit": list(KENNFARBE[GLAS])},
    {"name": "Fensterrahmen", "farbe_srgb_8bit": list(KENNFARBE[RAHMEN])},
    {"name": "Dach", "farbe_srgb_8bit": list(KENNFARBE[DACH])},
    {"name": "Gelaende Vorplatz", "farbe_srgb_8bit": list(KENNFARBE[BODEN])},
]

#: Name, Wandfarbe, Muster der Wand, Glasfarbe im Grundbild.
FASSADEN = (
    ("putz-weiss", (232, 228, 220), "glatt", (159, 179, 191)),
    ("putz-beige", (200, 178, 148), "glatt", (159, 179, 191)),
    ("beton-grau", (150, 150, 148), "glatt", (110, 132, 156)),
    ("klinker-rot", (150, 88, 70), "lagen", (159, 179, 191)),
    ("holz-dunkel", (96, 74, 56), "latten", (159, 179, 191)),
)
#: Name, Fensterhöhe, Geschosshöhe, Scherung, Dachhöhe, Geschosse, Gewicht des Vorhangs.
BLICKE = (
    ("augenhoehe", 22, 34, 0.0, 6, 3, 0.55),
    ("erhoeht", 14, 24, 0.12, 22, 3, 0.35),
    ("von-oben", 7, 15, 0.30, 50, 4, 0.15),
)
STIMMUNGEN = (
    ("neutral", (1.0, 1.0, 1.0)),
    ("morgen", (0.62, 0.64, 0.68)),
    ("abend", (1.04, 0.92, 0.78)),
    ("winter", (0.78, 0.82, 0.88)),
)
UEBERMALUNGEN = ("grau", "fassade", "warm")
GEGENFAELLE = ("dunkel", "schatten", "vorhang", "gemischt")


def _szene(f_nr: int, b_nr: int) -> dict:
    """Die Geometrie einer Szene: je Bildpunkt Stoff und Fensternummer, dazu die Fenster."""
    _, hf, pitch, scherung, dach_h, geschosse, _ = BLICKE[b_nr]
    anordnung = "band" if (f_nr + b_nr) % 2 == 0 else "einzel"
    rand = 8 + math.ceil(scherung * HOEHE / 2)
    f0 = 2 + dach_h
    f1 = f0 + geschosse * pitch + 4
    fenster = []                                   # (x0, x1, y0, y1) ungeschert, Enden inklusive
    for g in range(geschosse):
        y0 = f0 + 2 + g * pitch + (pitch - hf) // 2
        if anordnung == "einzel":
            anzahl = (BREITE - 2 * rand) // 36
            frei = (BREITE - 2 * rand) - anzahl * 22
            for n in range(anzahl):
                x0 = rand + round(frei * (n + 1) / (anzahl + 1)) + n * 22
                fenster.append((x0, x0 + 21, y0, y0 + hf - 1))
        else:
            links, rechts = rand + 10, BREITE - rand - 11
            anzahl = max(3, round((rechts - links + 1) / 32))
            for n in range(anzahl):
                x0 = links + round((rechts - links + 1) * n / anzahl)
                x1 = links + round((rechts - links + 1) * (n + 1) / anzahl) - 1
                fenster.append((x0, x1, y0, y0 + hf - 1))
    return {"anordnung": anordnung, "rand": rand, "f0": f0, "f1": f1, "scherung": scherung,
            "dach": (2, f0), "fenster": fenster}


@functools.lru_cache(maxsize=None)
def _stoffe(f_nr: int, b_nr: int, dx: int = 0, dy: int = 0) -> tuple:
    """Je Bildpunkt ``(Stoff, Fensternummer oder -1, x ungeschert, y)``, um ``dx, dy`` verschoben."""
    szene = _szene(f_nr, b_nr)
    aus = []
    rand, f0, f1 = szene["rand"], szene["f0"], szene["f1"]
    einzel = szene["anordnung"] == "einzel"
    for y_bild in range(HOEHE):
        y = y_bild - dy
        versatz = round(szene["scherung"] * (y - HOEHE / 2))
        for x_bild in range(BREITE):
            x = x_bild - dx - versatz
            stoff, nr = AUSSEN, -1
            if rand <= x < BREITE - rand:
                if szene["dach"][0] <= y < szene["dach"][1]:
                    stoff = DACH
                elif f0 <= y < f1:
                    stoff = WAND
                    for n, (x0, x1, y0, y1) in enumerate(szene["fenster"]):
                        if x0 <= x <= x1 and y0 <= y <= y1:
                            stoff, nr = GLAS, n
                            break
                        if einzel and x0 - 1 <= x <= x1 + 1 and y0 - 1 <= y <= y1 + 1:
                            stoff, nr = RAHMEN, n
                            break
                elif f1 <= y < HOEHE:
                    stoff = BODEN
            aus.append((stoff, nr, x, y))
    return tuple(aus)


def _korn(rng, farbe, sigma: float) -> tuple:
    """Die Farbe mit Korn: ein gemeinsamer Teil (Helligkeit) und ein kleinerer je Kanal (Farbe).

    Das Korn kommt aus einer festen Tafel je Paar (reihum gelesen) statt je Bildpunkt gewürfelt;
    das hält den Erzeuger schnell genug für die Probensammlung.
    """
    z, tafel, fein = rng.zeiger, rng.tafel, 0.4 * sigma
    rng.zeiger = (z + 4) % KORN_TAFEL
    gemeinsam = tafel[z] * sigma
    r = farbe[0] + gemeinsam + tafel[z + 1] * fein
    g = farbe[1] + gemeinsam + tafel[z + 2] * fein
    b = farbe[2] + gemeinsam + tafel[z + 3] * fein
    return (0 if r < 0 else 255 if r > 255 else round(r), 0 if g < 0 else 255 if g > 255 else round(g),
            0 if b < 0 else 255 if b > 255 else round(b))


def _punkt(farbe, plus: float = 0.0) -> tuple:
    return tuple(max(0, min(255, round(k + plus))) for k in farbe)


def _mal(farbe, faktor) -> tuple:
    if isinstance(faktor, (int, float)):
        return tuple(k * faktor for k in farbe)
    return tuple(k * f for k, f in zip(farbe, faktor))


def _wandmuster(muster: str, x: int, y: int) -> float:
    if muster == "lagen":
        return -9.0 if y % 4 == 0 else 0.0
    if muster == "latten":
        return (-7.0, 0.0, 5.0, 0.0, -3.0)[x % 5]
    return 0.0


@functools.lru_cache(maxsize=None)
def _grundbild(f_nr: int, b_nr: int, saat: str) -> tuple:
    """Das Grundbild einer Szene — für alle sieben Paare der Szene dasselbe, wie beim echten Render."""
    rng = _wuerfel(f"{saat}/{FASSADEN[f_nr][0]}/{BLICKE[b_nr][0]}/grundbild")
    szene = _szene(f_nr, b_nr)
    _, wand, muster, glas = FASSADEN[f_nr]
    f0, f1 = szene["f0"], szene["f1"]
    zeile: dict = {}
    aus = []
    for stoff, _, x, y in _stoffe(f_nr, b_nr):
        if stoff == WAND:
            if y not in zeile:
                zeile[y] = _mal(wand, 1.0 - 0.06 * (y - f0) / (f1 - f0))
            m = _wandmuster(muster, x, y)
            aus.append(_korn(rng, tuple(k + m for k in zeile[y]) if m else zeile[y], 1.5))
        elif stoff == GLAS:
            aus.append(_korn(rng, glas, 1.0))
        elif stoff == RAHMEN:
            aus.append(_korn(rng, (70, 70, 72), 1.0))
        elif stoff == DACH:
            aus.append(_korn(rng, (88, 84, 80), 2.0))
        elif stoff == BODEN:
            aus.append(_korn(rng, (120, 116, 108), 2.0))
        else:
            aus.append((190, 205, 225))
    return tuple(aus)


def _wuerfel(name: str):
    rng = random.Random(name)
    rng.tafel, rng.zeiger = [rng.gauss(0.0, 1.0) for _ in range(KORN_TAFEL + 4)], 0
    return rng


def _wand_ki(wand, muster, stimmung, x, y, f0, f1, rng) -> tuple:
    """Die Wand, wie die KI sie malt: Stimmung, etwas entsättigt, eigenes Korn."""
    farbe = rng.wand_zeile.get(y)
    if farbe is None:
        farbe = _mal(_mal(wand, 1.0 - 0.05 * (y - f0) / (f1 - f0)), stimmung)
        grau = sum(farbe) / 3.0
        farbe = rng.wand_zeile[y] = tuple(0.85 * k + 0.15 * grau for k in farbe)
    m = 1.2 * _wandmuster(muster, x, y)
    return _korn(rng, tuple(k + m for k in farbe) if m else farbe, 5.0)


def _glas_ki(stil: str, glas_grund, stimmung, fx: float, fy: float, x: int, y: int, wuerfel: dict,
             rng, vorhang_gewicht: float) -> tuple:
    """Eine Scheibe, wie die KI sie malt. ``fx, fy`` sind die Lage in der Scheibe (0..1)."""
    if stil == "wie-grund":
        return _korn(rng, _mal(_mal(glas_grund, stimmung), wuerfel["hell"]), 10.0)
    if stil == "himmel":
        oben, unten = (175, 198, 222), (150, 172, 198)
        farbe = tuple(o + (u - o) * fy for o, u in zip(oben, unten))
        return _korn(rng, _mal(_mal(farbe, stimmung), wuerfel["hell"]), 6.0)
    v = wuerfel["dunkel"]
    farbe = (v, v + 7, v + 16)
    if (x + 1.3 * y + wuerfel["phase"]) % 23 < 4.5:           # der helle Streifen einer Spiegelung
        farbe = (150, 168, 186)
    farbe = _mal(farbe, stimmung)
    if stil == "vorhang":
        seite, anteil = wuerfel["vorhang"]
        if (fx < anteil) if seite == 0 else (fx > 1.0 - anteil):
            stoff = _mal((205, 200, 188), stimmung)
            falte = 6.0 if x % 4 == 0 else 0.0
            farbe = tuple(vorhang_gewicht * (s - falte) + (1.0 - vorhang_gewicht) * k
                          for s, k in zip(stoff, farbe))
    return _korn(rng, farbe, 7.0)


def _uebermalt(art: str, wand, muster, stimmung, x, y, f0, f1, wuerfel: dict, rng) -> tuple:
    if art == "fassade":
        return _wand_ki(wand, muster, stimmung, x, y, f0, f1, rng)
    if art == "grau":
        g = wuerfel["grau"] + (-4.0 if x % 3 == 0 else 0.0)      # Lattung wie im echten Fall
        return _korn(rng, _mal((g, g, g), stimmung), 5.0)
    farbe = wuerfel["warm"]
    if (x * 7 + wuerfel["phase"]) % 19 == 0:                     # dunkle Fuge wie im echten Fall
        farbe = _mal(farbe, 0.45)
    return _korn(rng, _mal(farbe, stimmung), 8.0)


def _paar(f_nr: int, b_nr: int, fall: str, lfd: int, saat: str = "A0291") -> dict:
    name = f"{FASSADEN[f_nr][0]}/{BLICKE[b_nr][0]}/{fall}"
    rng = _wuerfel(f"{saat}/{name}")
    rng.wand_zeile = {}
    szene = _szene(f_nr, b_nr)
    _, wand, muster, glas_grund = FASSADEN[f_nr]
    stoffe = _stoffe(f_nr, b_nr)
    kennung = [KENNFARBE[s[0]] for s in stoffe]
    grund = list(_grundbild(f_nr, b_nr, saat))
    stimmung = STIMMUNGEN[(f_nr + 2 * b_nr + lfd) % len(STIMMUNGEN)]
    anzahl = len(szene["fenster"])
    uebermalt = fall in UEBERMALUNGEN
    ziel_nr = (3 * f_nr + 5 * b_nr + 2 * lfd + 1) % anzahl if uebermalt else -1
    # Der Stil der Scheiben: in den Übermalungs-Paaren reihum, in den Gegenfällen nach dem Fall.
    reihum = ("dunkel", "himmel", "wie-grund")
    # Dunkles, spiegelndes Glas, von Auge noch als Fenster zu sehen: vor einer hellen Wand fast
    # schwarz, vor einer dunklen Wand so hell wie in den echten Stimmungsbildern (Median um 135).
    dunkel = (40, 70) if sum(wand) / 3.0 >= 120 else (115, 140)
    stile, wuerfel = [], []
    for n in range(anzahl):
        if uebermalt:
            stil = reihum[(f_nr + b_nr + lfd) % 3]
        elif fall == "gemischt":
            stil = reihum[rng.randrange(3)]
        elif fall == "schatten":
            stil = ("wie-grund", "dunkel")[(f_nr + b_nr) % 2]
        elif fall == "vorhang":
            stil = "vorhang" if n % 2 == 0 else "dunkel"
        else:
            stil = "dunkel"
        stile.append(stil)
        wuerfel.append({"hell": rng.uniform(0.94, 1.03), "dunkel": rng.uniform(*dunkel),
                        "phase": rng.uniform(0, 23),
                        "vorhang": (rng.randrange(2), rng.uniform(0.30, 0.45)),
                        "grau": rng.uniform(150, 185),
                        "warm": (rng.uniform(215, 240), rng.uniform(165, 190), rng.uniform(70, 100))})
    dx, dy = rng.choice((-1, 0, 1)), rng.choice((-1, 0, 1))
    # Der Schatten: eine schräge Kante quer über die Fassade, darunter 0,55.
    kante = (rng.uniform(0.35, 0.65) * BREITE, rng.choice((-0.6, 0.6)))
    f0, f1 = szene["f0"], szene["f1"]
    einzel = szene["anordnung"] == "einzel"
    ki = []
    aussen = _punkt(_mal((186, 202, 224), stimmung[1]))
    for i, (stoff, nr, x, y) in enumerate(_stoffe(f_nr, b_nr, dx, dy)):
        if stoff == WAND:
            farbe = _wand_ki(wand, muster, stimmung[1], x, y, f0, f1, rng)
        elif stoff in (GLAS, RAHMEN) and nr == ziel_nr:
            farbe = _uebermalt(fall, wand, muster, stimmung[1], x, y, f0, f1, wuerfel[nr], rng)
        elif stoff == GLAS:
            x0, x1, y0, y1 = szene["fenster"][nr]
            if not einzel and x == x0 and stile[nr] != "wie-grund" and nr > 0:
                farbe = _korn(rng, _mal((62, 62, 64), stimmung[1]), 3.0)  # Sprosse
            else:
                farbe = _glas_ki(stile[nr], glas_grund, stimmung[1], (x - x0) / max(1, x1 - x0),
                                 (y - y0) / max(1, y1 - y0), x, y, wuerfel[nr], rng,
                                 BLICKE[b_nr][6])
        elif stoff == RAHMEN:
            farbe = _korn(rng, _mal((66, 66, 68), stimmung[1]), 3.0)
        elif stoff == DACH:
            farbe = _korn(rng, _mal((84, 82, 80), stimmung[1]), 5.0)
        elif stoff == BODEN:
            farbe = _korn(rng, _mal((118, 114, 108), stimmung[1]), 6.0)
        else:
            farbe = aussen
        if fall == "schatten" and stoff != AUSSEN:
            bx, by = i % BREITE, i // BREITE
            if bx + kante[1] * by > kante[0]:
                farbe = _punkt(_mal(farbe, 0.55))
        ki.append(farbe)
    ziel = None
    if uebermalt:
        xs = [i % BREITE for i, s in enumerate(stoffe) if s[0] == GLAS and s[1] == ziel_nr]
        ys = [i // BREITE for i, s in enumerate(stoffe) if s[0] == GLAS and s[1] == ziel_nr]
        ziel = {"x0": min(xs), "y0": min(ys), "x1": max(xs), "y1": max(ys)}
    return {"name": name, "fassade": FASSADEN[f_nr][0], "blick": BLICKE[b_nr][0], "fall": fall,
            "anordnung": szene["anordnung"], "stimmung": stimmung[0], "uebermalt": uebermalt,
            "ziel": ziel, "breite": BREITE, "hoehe": HOEHE, "ki": ki, "grund": grund,
            "kennung": kennung, "tabelle": TABELLE}


def eichsatz(saat: str = "A0291") -> list:
    """Alle 105 Paare: je Szene drei mit einem übermalten Fenster und vier Gegenfälle.

    ``saat`` würfelt Korn, Versatz, Helligkeiten, Vorhänge und Schattenkante neu; welches Fenster
    übermalt wird und welche Stimmung gilt, bleibt. Der Eichsatz ist die Vorgabe ``"A0291"``.
    """
    paare = []
    for f_nr in range(len(FASSADEN)):
        for b_nr in range(len(BLICKE)):
            for lfd, fall in enumerate(UEBERMALUNGEN + GEGENFAELLE):
                paare.append(_paar(f_nr, b_nr, fall, lfd, saat))
    return paare


def _im_ziel(ort: dict, ziel: dict, luft: int = 2) -> float:
    """Welcher Anteil der Fläche von ``ort`` im Ziel liegt (mit ``luft`` Bildpunkten Rand)."""
    bx = min(ort["x1"], ziel["x1"] + luft) - max(ort["x0"], ziel["x0"] - luft) + 1
    by = min(ort["y1"], ziel["y1"] + luft) - max(ort["y0"], ziel["y0"] - luft) + 1
    if bx <= 0 or by <= 0:
        return 0.0
    return bx * by / ((ort["x1"] - ort["x0"] + 1) * (ort["y1"] - ort["y0"] + 1))


def werte(paar: dict, bauteile) -> dict:
    """Ein Paar gegen den Befund je Bauteil: erkannt (am richtigen Ort) und Fehlalarme.

    Ein Fund zählt als richtig, wenn mindestens die Hälfte seiner Fläche im übermalten Fenster
    liegt; jeder andere Fund ist ein Fehlalarm, auch in einem Paar mit Übermalung.
    """
    funde = [b for b in bauteile or () if b.get("urteil") == "uebermalt"]
    if not paar["uebermalt"]:
        return {"erkannt": None, "fehlalarme": len(funde)}
    richtig = [b for b in funde if _im_ziel(b["ort"], paar["ziel"]) >= 0.5]
    return {"erkannt": bool(richtig), "fehlalarme": len(funde) - len(richtig)}


def miss(saat: str = "A0291") -> dict:
    """Der Prüfweg von A0291: der Eichsatz durch ``varianten.fenster_gehalten``, ausgezählt.

    Returns:
        ``{paare, uebermalt, gegenfaelle, erkannt, rate, fehlalarme, verfehlt, falsch, je_art,
        je_blick, band_merkt, band_fehlalarme}`` — ``erkannt`` und ``fehlalarme`` zählen die
        Prüfung je Bauteil (mit Ort), ``band_*`` das Urteil ``gehalten`` der Prüfung je Band
        allein (ohne Ort), also den Stand vor A0291.
    """
    from aiimaging import varianten  # noqa: PLC0415
    glas, ausser = varianten.glasfarben(TABELLE), varianten.nicht_fassade_farben(TABELLE)
    aus = {"paare": 0, "uebermalt": 0, "gegenfaelle": 0, "erkannt": 0, "fehlalarme": 0,
           "verfehlt": [], "falsch": [], "je_art": {}, "je_blick": {}, "band_merkt": 0,
           "band_fehlalarme": 0, "befunde": {}}
    for paar in eichsatz(saat):
        befund = varianten.fenster_gehalten(paar["ki"], paar["grund"], paar["kennung"], glas,
                                            ausser=ausser, breite=paar["breite"])
        wert = werte(paar, befund.get("bauteile"))
        aus["paare"] += 1
        aus["fehlalarme"] += wert["fehlalarme"]
        aus["befunde"][paar["name"]] = {"paar": {k: v for k, v in paar.items()
                                                 if k not in ("ki", "grund", "kennung")},
                                        "befund": befund, "wert": wert}
        if wert["fehlalarme"]:
            aus["falsch"].append(paar["name"])
        if paar["uebermalt"]:
            aus["uebermalt"] += 1
            aus["erkannt"] += bool(wert["erkannt"])
            aus["band_merkt"] += befund["gehalten"] is False
            for schluessel, wo in ((paar["fall"], aus["je_art"]), (paar["blick"], aus["je_blick"])):
                eintrag = wo.setdefault(schluessel, [0, 0])
                eintrag[0] += bool(wert["erkannt"])
                eintrag[1] += 1
            if not wert["erkannt"]:
                aus["verfehlt"].append(paar["name"])
        else:
            aus["gegenfaelle"] += 1
            aus["band_fehlalarme"] += befund["gehalten"] is False
    aus["rate"] = aus["erkannt"] / aus["uebermalt"]
    return aus


def schreibe_png(pfad, punkte, breite: int, hoehe: int) -> None:
    """Ein 8-Bit-RGB-PNG ohne fremdes Paket (für die Probe über die Bilddateien)."""
    import struct  # noqa: PLC0415
    import zlib  # noqa: PLC0415

    def block(art: bytes, daten: bytes) -> bytes:
        return (struct.pack(">I", len(daten)) + art + daten
                + struct.pack(">I", zlib.crc32(art + daten) & 0xFFFFFFFF))
    roh = bytearray()
    for y in range(hoehe):
        roh.append(0)
        for p in punkte[y * breite:(y + 1) * breite]:
            roh.extend(p)
    with open(pfad, "wb") as datei:
        datei.write(b"\x89PNG\r\n\x1a\n" + block(b"IHDR", struct.pack(">IIBBBBB", breite, hoehe, 8, 2, 0, 0, 0))
                    + block(b"IDAT", zlib.compress(bytes(roh), 6)) + block(b"IEND", b""))


if __name__ == "__main__":      # python tests/fenster_paare.py [saat ...] — die Zahlen der Meldung
    import sys
    sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[1] / "src"))
    for _saat in sys.argv[1:] or ["A0291"]:
        _m = miss(_saat)
        print(f"{_saat}: je Bauteil erkannt {_m['erkannt']}/{_m['uebermalt']} ({_m['rate']:.1%}), "
              f"Fehlalarme {_m['fehlalarme']} in {_m['paare']} Paaren ({_m['gegenfaelle']} Gegenfaelle); "
              f"je Band allein: merkt {_m['band_merkt']}/{_m['uebermalt']} ohne Ort, "
              f"Fehlalarme {_m['band_fehlalarme']}/{_m['gegenfaelle']}")
        print(f"  je Art {_m['je_art']}, je Blick {_m['je_blick']}")
        print(f"  verfehlt {_m['verfehlt']}, falsch {_m['falsch']}")
