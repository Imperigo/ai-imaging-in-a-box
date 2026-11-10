"""Erzeuger für den Messsatz «Bauwerk fehlt» (A0299) — synthetisch, ohne Zufall von aussen.

Was er liefert
--------------
:func:`satz` baut Bildpaare aus Soll-Tiefenkarte (Meter, Himmel als Marke) und einer
**nachgestellten Schätzkarte** eines Bildes. Je Szene gibt es gute Bilder (perfekt und leicht
abweichend) und Fehl-Fälle (Bauwerk ganz weg, halb weg, durch ein anderes Volumen ersetzt).
Die Szenen decken einen Bodenanteil von 20 bis 80 % und einen Hausanteil von 10 bis 60 % ab.

Nichts hier stammt aus einem echten Projekt (Regel 3): Die Szene ist ein Quader auf einer
Ebene, die Kamera ein Lochbild mit Horizontzeile.

Was die nachgestellte Schätzkarte kann und was nicht
---------------------------------------------------
Sie bildet die Eigenschaften nach, die an echten Schätzkarten **gemessen** sind und an denen
frühere Anwesenheitsmasse gescheitert sind (``geometrie_qa``, Befunde 21.08. bis 24.09.2026):

* Nähe statt Tiefe (Disparität), mit beliebigem Massstab und einer Krümmung (``gamma``),
* ein **Ortsfeld**: unten näher als oben, zur Mitte anders als am Rand, auch auf leerer Fläche,
* weiche Kanten und Rauschen,
* der Boden wird im Bild überall gefüllt, auch wo das Bauwerk fehlt.

Sie ist **kein** Schätzer. Ob ein Mass, das hier trennt, auch an erzeugten Bildern trennt, ist
eine Messung am Gerät und wird nirgends behauptet.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field

#: Bildgrösse des Satzes. Klein genug für reines Python, gross genug für Flanken und Ränder.
BREITE = 96
HOEHE = 64

#: Hintergrundmarke der Soll-Karte (Himmel), wie sie ein Renderer schreibt.
MARKE = 1.0e10

#: Tiefe des Himmels im nachgestellten Bild (Meter). Endlich: Ein Schätzer schreibt keine Marke.
HIMMEL_M = 1.0e4

#: Kamerakonstante: Bodentiefe = K / (Zeile − Horizont + 0,5).
K = 60.0

#: Zielwerte (Bodenanteil, Hausanteil) der zwölf Szenen.
ZIELE = ((0.20, 0.10), (0.20, 0.35), (0.20, 0.60), (0.35, 0.20), (0.35, 0.50),
         (0.50, 0.10), (0.50, 0.35), (0.65, 0.10), (0.65, 0.20), (0.65, 0.30),
         (0.80, 0.10), (0.80, 0.15))

GUT = ("perfekt", "versatz", "kleiner", "weich", "feldstark")
FEHL = ("ganz_weg", "halb_links_weg", "halb_oben_weg", "ersetzt_daneben", "ersetzt_turm",
        "ersetzt_flachbau")


@dataclass(frozen=True)
class Koerper:
    """Ein Quader im Bild: Spalten ``[x0, x1)``, Zeilen ``[yt, yf)``, Tiefe am linken Rand."""
    x0: int
    x1: int
    yt: int
    yf: int
    tiefe: float
    schraege: float = 0.0     # Tiefenzuwachs über die Breite, als Anteil der Tiefe

    def tiefe_bei(self, x: int) -> float:
        breite = max(1, self.x1 - self.x0)
        return self.tiefe * (1.0 + self.schraege * (x - self.x0) / breite)


@dataclass(frozen=True)
class Szene:
    horizont: int
    haus: Koerper
    bodenanteil: float
    hausanteil: float
    gefaelle: float = 0.0     # Quergefälle des Geländes (Hang), 0 = eben


@dataclass
class Paar:
    name: str
    art: str                  # Eintrag aus GUT oder FEHL
    fehlt: bool               # True = «Bauwerk fehlt»-Fall, muss durchfallen
    breite: int
    soll: list[float]
    maske: list[bool]
    roh: list[float]          # nachgestellte Schätzkarte, ohne Marke
    polaritaet: int           # −1 Disparität (nah = gross), +1 Tiefe (nah = klein)
    bodenanteil: float
    hausanteil: float
    anteil_im_umriss: float = field(default=1.0)   # wie viel des Umrisses das Bild füllt
    klasse: str = ""          # gut | fehl | uebergang | abgegrenzt (Runde 2)


def bodentiefe(zeile: int, horizont: int) -> float:
    return K / (zeile - horizont + 0.5)


def _boden(szene: "Szene", x: int, y: int) -> float | None:
    """Bodentiefe an einem Bildpunkt, ``None`` für Himmel. Mit Quergefälle wandert der Horizont."""
    nenner = y - szene.horizont + 0.5 + szene.gefaelle * (x - BREITE / 2)
    return K / nenner if nenner >= 0.5 else None


def _szene_fuer(ziel_boden: float, ziel_haus: float) -> Szene:
    """Die Szene, deren Anteile den Zielwerten am nächsten kommen (erschöpfende Suche)."""
    n = BREITE * HOEHE
    bestes = None
    for horizont in range(2, HOEHE - 6):
        for yf in range(horizont + 4, HOEHE - 2):          # Fuss unter dem Horizont
            for yt in range(2, yf - 5):
                hoehe = yf - yt
                bw = round(ziel_haus * n / hoehe)
                if bw < 8 or bw > BREITE - 24:
                    continue
                haus = bw * hoehe
                unter = yf - max(yt, horizont)
                boden = BREITE * (HOEHE - horizont) - bw * unter
                fehler = abs(boden / n - ziel_boden) + abs(haus / n - ziel_haus)
                # Bei gleichem Fehler die Szene mit mehr Bauwerk über dem Horizont.
                rang = (round(fehler, 4), yt)
                if bestes is None or rang < bestes[0]:
                    bestes = (rang, horizont, yt, yf, bw, boden / n, haus / n)
    _, horizont, yt, yf, bw, boden, haus = bestes
    x0 = (BREITE - bw) // 2 - 3                             # leicht aus der Mitte
    tiefe = bodentiefe(yf - 1, horizont)
    return Szene(horizont, Koerper(x0, x0 + bw, yt, yf, tiefe), boden, haus)


def szenen() -> list[Szene]:
    liste = []
    for nr, (boden, haus) in enumerate(ZIELE):
        s = _szene_fuer(boden, haus)
        if nr % 3 == 1:                                     # jede dritte übereck
            s = Szene(s.horizont, Koerper(s.haus.x0, s.haus.x1, s.haus.yt, s.haus.yf,
                                          s.haus.tiefe, 0.15), s.bodenanteil, s.hausanteil)
        liste.append(s)
    return liste


def soll_karte(szene: Szene) -> tuple[list[float], list[bool]]:
    """Soll-Tiefe in Metern (Boden und Bauwerk, Himmel als Marke) und die Bauwerksmaske."""
    soll = [MARKE] * (BREITE * HOEHE)
    maske = [False] * (BREITE * HOEHE)
    for y in range(HOEHE):
        for x in range(BREITE):
            d = _boden(szene, x, y)
            if d is not None:
                soll[y * BREITE + x] = d
    h = szene.haus
    for y in range(h.yt, h.yf):
        for x in range(h.x0, h.x1):
            soll[y * BREITE + x] = h.tiefe_bei(x)
            maske[y * BREITE + x] = True
    return soll, maske


def bild_tiefe(szene: Szene, koerper: list[Koerper]) -> list[float]:
    """Was das Bild zeigt: Boden bis zum Horizont, Himmel darüber, davor die Körper."""
    t = [HIMMEL_M] * (BREITE * HOEHE)
    for y in range(HOEHE):
        for x in range(BREITE):
            d = _boden(szene, x, y)
            if d is not None:
                t[y * BREITE + x] = d
    for k in koerper:
        for y in range(max(0, k.yt), min(HOEHE, k.yf)):
            for x in range(max(0, k.x0), min(BREITE, k.x1)):
                i = y * BREITE + x
                t[i] = min(t[i], k.tiefe_bei(x))
    return t


def _weichzeichnen(werte: list[float], durchgaenge: int) -> list[float]:
    for _ in range(durchgaenge):
        neu = list(werte)
        for y in range(HOEHE):
            for x in range(BREITE):
                summe = 0.0
                anzahl = 0
                for dy in (-1, 0, 1):
                    yy = y + dy
                    if not 0 <= yy < HOEHE:
                        continue
                    for dx in (-1, 0, 1):
                        xx = x + dx
                        if 0 <= xx < BREITE:
                            summe += werte[yy * BREITE + xx]
                            anzahl += 1
                neu[y * BREITE + x] = summe / anzahl
        werte = neu
    return werte


def schaetzkarte(tiefe: list[float], *, polaritaet: int, startwert: int, feld: float = 0.15,
                 gamma: float = 0.8, weich: int = 1, rauschen: float = 0.004) -> list[float]:
    """Die nachgestellte Schätzkarte eines Bildes mit der Tiefe ``tiefe`` (siehe Modultext)."""
    naehe = [1.0 / d for d in tiefe]
    groesste = max(naehe)
    karte = []
    for i, wert in enumerate(naehe):
        x, y = i % BREITE, i // BREITE
        u = 2.0 * x / (BREITE - 1) - 1.0
        ortsfeld = 0.6 * (y / (HOEHE - 1)) + 0.4 * (1.0 - u * u)
        karte.append((1.0 - feld) * (wert / groesste) ** gamma + feld * ortsfeld)
    karte = _weichzeichnen(karte, weich)
    zufall = random.Random(startwert)
    karte = [wert + zufall.gauss(0.0, rauschen) for wert in karte]
    if polaritaet > 0:                       # als Tiefe ausgegeben: nah = klein
        karte = [3.0 - 2.0 * wert for wert in karte]
    return karte


def _koerper_fuer(art: str, szene: Szene) -> list[Koerper]:
    h = szene.haus
    bw, bh = h.x1 - h.x0, h.yf - h.yt
    if art in ("perfekt", "weich", "feldstark"):
        return [h]
    if art == "versatz":                     # zwei Punkte nach rechts, einer nach oben
        return [Koerper(h.x0 + 2, h.x1 + 2, h.yt - 1, h.yf - 1, h.tiefe, h.schraege)]
    if art == "kleiner":                     # ringsum einen Punkt kleiner
        return [Koerper(h.x0 + 1, h.x1 - 1, h.yt + 1, h.yf, h.tiefe, h.schraege)]
    if art == "ganz_weg":
        return []
    if art == "halb_links_weg":
        return [Koerper(h.x0 + bw // 2, h.x1, h.yt, h.yf, h.tiefe, h.schraege)]
    if art == "halb_oben_weg":
        return [Koerper(h.x0, h.x1, h.yt + bh // 2, h.yf, h.tiefe, h.schraege)]
    if art == "ersetzt_daneben":             # gleich gross, ganz neben dem Umriss
        platz_rechts = BREITE - h.x1
        if platz_rechts >= h.x0:
            x0 = h.x1 + 1
            return [Koerper(x0, min(BREITE, x0 + bw), h.yt, h.yf, h.tiefe)]
        return [Koerper(max(0, h.x0 - 1 - bw), h.x0 - 1, h.yt, h.yf, h.tiefe)]
    if art == "ersetzt_turm":                # schmal und höher, mitten im Umriss
        tb = max(3, round(0.35 * bw))
        x0 = h.x0 + (bw - tb) // 2
        return [Koerper(x0, x0 + tb, max(0, h.yt - bh // 3), h.yf, h.tiefe)]
    if art == "ersetzt_flachbau":            # breiter und nur 40 % so hoch
        mehr = max(2, round(0.15 * bw))
        return [Koerper(max(0, h.x0 - mehr), min(BREITE, h.x1 + mehr),
                        h.yf - max(2, round(0.4 * bh)), h.yf, h.tiefe)]
    raise ValueError(f"Unbekannte Art {art!r}.")


def _anteil_im_umriss(maske: list[bool], koerper: list[Koerper]) -> float:
    n = sum(maske)
    drin = 0
    for i, m in enumerate(maske):
        if not m:
            continue
        x, y = i % BREITE, i // BREITE
        if any(k.x0 <= x < k.x1 and k.yt <= y < k.yf for k in koerper):
            drin += 1
    return drin / n


def satz() -> list[Paar]:
    """Alle Paare: zwölf Szenen, je fünf gute Bilder und sechs Fehl-Fälle (132 Paare)."""
    paare: list[Paar] = []
    for nr, szene in enumerate(szenen()):
        soll, maske = soll_karte(szene)
        polaritaet = -1 if nr % 2 == 0 else +1
        for art in GUT + FEHL:
            koerper = _koerper_fuer(art, szene)
            einstellung = {"feld": 0.15, "gamma": 0.8, "weich": 1, "rauschen": 0.004}
            if art == "weich":
                einstellung.update(weich=3, rauschen=0.008)
            if art == "feldstark":
                einstellung.update(feld=0.35, gamma=1.3)
            roh = schaetzkarte(bild_tiefe(szene, koerper), polaritaet=polaritaet,
                               startwert=1000 * nr + (GUT + FEHL).index(art), **einstellung)
            paare.append(Paar(
                name=f"s{nr:02d}-{art}", art=art, fehlt=art in FEHL, breite=BREITE,
                soll=soll, maske=maske, roh=roh, polaritaet=polaritaet,
                bodenanteil=szene.bodenanteil, hausanteil=szene.hausanteil,
                anteil_im_umriss=_anteil_im_umriss(maske, koerper),
                klasse="fehl" if art in FEHL else "gut"))
    return paare


# --------------------------------------------------------------------------------------
# Zufallsfälle und Reihen quer über die Schwelle (Anleitung Spezialauftrag, Abschnitt 2)
# --------------------------------------------------------------------------------------

def teilbau(haus: Koerper, anteil: float, seite: str) -> list[Koerper]:
    """Das Haus, von dem nur der Anteil ``anteil`` steht: von links, rechts oder oben beschnitten."""
    bw, bh = haus.x1 - haus.x0, haus.yf - haus.yt
    if anteil <= 0.0:
        return []
    if seite == "links":
        return [Koerper(haus.x1 - max(1, round(anteil * bw)), haus.x1, haus.yt, haus.yf,
                        haus.tiefe, haus.schraege)]
    if seite == "rechts":
        return [Koerper(haus.x0, haus.x0 + max(1, round(anteil * bw)), haus.yt, haus.yf,
                        haus.tiefe, haus.schraege)]
    return [Koerper(haus.x0, haus.x1, haus.yf - max(1, round(anteil * bh)), haus.yf,
                    haus.tiefe, haus.schraege)]


def zufallsfall(startwert: int) -> dict:
    """Ein zufälliger Fall mit bekannter Wahrheit: Szene, Bildinhalt, Schätzkarte, Sonderlage.

    Returns:
        ``{soll, maske, roh, polaritaet, im_umriss, lage, art}``. ``im_umriss`` ist der
        Anteil des Umrisses, den das Bild mit einem Körper füllt (die Wahrheit); ``lage``
        ist ``frei``, ``wand`` (gleich weit entfernter Körper hinter dem Umriss, auch im
        Soll), ``ohne_gelaende`` (Soll trägt nur das Haus) oder ``rand`` (Haus am Bildrand
        angeschnitten).
    """
    z = random.Random(startwert)
    horizont = z.randint(4, 44)
    yf = z.randint(horizont + 5, HOEHE - 3)
    yt = z.randint(2, max(2, yf - 12))
    bw = z.randint(10, 64)
    lage = z.choices(("frei", "wand", "ohne_gelaende", "rand"), (0.7, 0.1, 0.1, 0.1))[0]
    x0 = 0 if lage == "rand" else z.randint(8, BREITE - bw - 8)
    haus = Koerper(x0, x0 + bw, yt, yf, bodentiefe(yf - 1, horizont),
                   z.choice((0.0, 0.0, 0.1, 0.2)))
    szene = Szene(horizont, haus, 0.0, 0.0)
    soll, maske = soll_karte(szene)
    art = z.choice(("da", "da", "versatz", "teil", "teil", "teil", "weg", "ersetzt"))
    if art == "da":
        koerper = [haus]
    elif art == "versatz":
        dx, dy = z.randint(-2, 2), z.randint(-1, 1)
        koerper = [Koerper(haus.x0 + dx, haus.x1 + dx, haus.yt + dy, haus.yf + dy,
                           haus.tiefe, haus.schraege)]
    elif art == "teil":
        koerper = teilbau(haus, z.random(), z.choice(("links", "rechts", "oben")))
    elif art == "weg":
        koerper = []
    else:
        kb, kh = z.randint(6, 50), z.randint(6, 45)
        kx = z.randint(0, BREITE - kb)
        kf = z.randint(horizont + 3, HOEHE - 1)
        koerper = [Koerper(kx, kx + kb, max(0, kf - kh), kf, bodentiefe(kf - 1, horizont))]
    hinten: list[Koerper] = []
    if lage == "wand":
        hinten = [Koerper(0, BREITE, yt, yf, haus.tiefe)]
        for y in range(yt, yf):
            for x in range(BREITE):
                if not maske[y * BREITE + x]:
                    soll[y * BREITE + x] = min(soll[y * BREITE + x], haus.tiefe)
    if lage == "ohne_gelaende":
        soll = [wert if m else MARKE for wert, m in zip(soll, maske)]
    polaritaet = z.choice((-1, +1))
    roh = schaetzkarte(bild_tiefe(szene, hinten + koerper), polaritaet=polaritaet,
                       startwert=startwert, feld=z.uniform(0.0, 0.35),
                       gamma=z.uniform(0.5, 2.0), weich=z.randint(0, 3),
                       rauschen=z.uniform(0.001, 0.02))
    return {"soll": soll, "maske": maske, "roh": roh, "polaritaet": polaritaet,
            "im_umriss": _anteil_im_umriss(maske, koerper), "lage": lage, "art": art}


# --------------------------------------------------------------------------------------
# Satz der Runde 2: die Fälle des Gegenlesens und dichte Reihen (Auftrag, 10.11.2026 11:40)
# --------------------------------------------------------------------------------------

def baeume(haus: Koerper, *, dichte: float, faktor: float, startwert: int,
           unten_ab: int | None = None) -> list[Koerper]:
    """Baumkronen im Umriss: je 4 bis 9 Spalten breit, Oberkante unregelmässig, Tiefe ±8 %."""
    z = random.Random(startwert)
    bh = haus.yf - haus.yt
    kronen = []
    x = haus.x0
    while x < haus.x1:
        breite = z.randint(4, 9)
        oben = haus.yt + z.randint(-3, bh // 2)
        tiefe = haus.tiefe * faktor * (1.0 + z.uniform(-0.08, 0.08))
        if z.random() < dichte:
            kronen.append(Koerper(x, min(haus.x1, x + breite),
                                  oben if unten_ab is None else max(oben, unten_ab),
                                  haus.yf, tiefe))
        x += breite
    return kronen


def satteldach(haus: Koerper) -> list[Koerper]:
    """Dasselbe Haus mit Giebel: In den oberen 30 % läuft die Breite zur Mitte zusammen."""
    bw, bh = haus.x1 - haus.x0, haus.yf - haus.yt
    giebel = max(2, round(0.3 * bh))
    teile = [Koerper(haus.x0, haus.x1, haus.yt + giebel, haus.yf, haus.tiefe, haus.schraege)]
    for k in range(giebel):
        halb = round(0.5 * bw * (k + 1) / giebel)
        mitte = haus.x0 + bw // 2
        teile.append(Koerper(mitte - halb, mitte + halb, haus.yt + k, haus.yt + k + 1,
                             haus.tiefe))
    return teile


def _paar(name: str, klasse: str, szene: Szene, tiefe: list[float], polaritaet: int,
          im_umriss: float, **einstellung) -> Paar:
    soll, maske = soll_karte(szene)
    werte = {"feld": 0.15, "gamma": 0.8, "weich": 1, "rauschen": 0.004}
    werte.update(einstellung)
    startwert = sum(ord(c) * (k + 1) for k, c in enumerate(name)) % 9973
    roh = schaetzkarte(tiefe, polaritaet=polaritaet, startwert=startwert, **werte)
    return Paar(name=name, art=name.split("-", 1)[1], fehlt=klasse == "fehl", breite=BREITE,
                soll=soll, maske=maske, roh=roh, polaritaet=polaritaet,
                bodenanteil=szene.bodenanteil, hausanteil=szene.hausanteil,
                anteil_im_umriss=im_umriss, klasse=klasse)


#: Ab welchem Tiefenfaktor ein anderes Volumen im gleichen Umriss als Fehl-Fall gilt. Darunter
#: ist es ein Übergang ohne Soll-Urteil; die gemessene Grenze steht im Ergebnisblatt.
M2_FEHL_AB = 1.3


def satz_runde2() -> list[Paar]:
    """Der Satz der Runde 2: die 132 Paare der Runde 1 und rund 200 weitere.

    Dazu kommen die Fälle des Gegenlesens (anderes Volumen im gleichen Umriss, Satteldach,
    Bäume, Bodentextur, Bau dahinter, Glas, verschobene Maske, kleines Haus, Bildrand, Hang),
    Reihen in Schritten von 5 % des Umrisses quer über die Schwelle, das Ortsfeld von 0,3
    bis 0,8 mit starkem Rauschen und Tiefenfaktoren von 1,1 bis 3.
    """
    paare = satz()
    alle = szenen()
    hang = Szene(15, Koerper(38, 60, 22, 50, bodentiefe(49, 15)), 0.0, 0.0, gefaelle=0.12)
    klein = _szene_fuer(0.5, 0.05)
    for kurz, szene in (("g06", alle[6]), ("g03", alle[3])):
        h = szene.haus
        bw, bh = h.x1 - h.x0, h.yf - h.yt
        ohne = bild_tiefe(szene, [])
        voll = bild_tiefe(szene, [h])
        for pol in (-1, +1):
            p = "m" if pol < 0 else "p"

            def neu(art, klasse, tiefe, im_umriss, szene_=szene, **kw):
                paare.append(_paar(f"{kurz}{p}-{art}", klasse, szene_, tiefe, pol, im_umriss,
                                   **kw))

            # Gegenlesen F1a und die Reihe der Tiefenfaktoren (M2)
            for faktor in (1.1, 1.2, 1.3, 1.5, 2.0, 3.0):
                tiefer = Koerper(h.x0, h.x1, h.yt, h.yf, h.tiefe * faktor)
                neu(f"gleicher_umriss_{faktor:.1f}x_tiefer",
                    "fehl" if faktor >= M2_FEHL_AB else "uebergang",
                    bild_tiefe(szene, [tiefer]), 1.0)
            neu("satteldach", "gut", bild_tiefe(szene, satteldach(h)), 0.85)
            # M1: Bäume an Stelle des Hauses. Dicht in Haustiefe: abgegrenzt (Formfrage).
            neu("baeume_dicht", "abgegrenzt",
                bild_tiefe(szene, baeume(h, dichte=1.0, faktor=1.0, startwert=3)), 0.0)
            neu("baeume_licht", "fehl",
                bild_tiefe(szene, baeume(h, dichte=0.6, faktor=1.0, startwert=4)), 0.0)
            neu("haus_halb_hinter_baeumen", "gut",
                bild_tiefe(szene, [h] + baeume(h, dichte=1.0, faktor=0.7, startwert=5,
                                               unten_ab=h.yt + bh // 2)), 1.0)
            # F10: Haus fehlt, Boden im Umriss mit Textur ±30 %
            z = random.Random(10 + pol)
            textur = [d * (1.0 + z.uniform(-0.3, 0.3))
                      if h.x0 <= i % BREITE < h.x1 and h.yt <= i // BREITE < h.yf
                      and d < HIMMEL_M else d for i, d in enumerate(ohne)]
            neu("boden_mit_textur", "fehl", textur, 0.0)
            # F11: Haus fehlt, grosser Bau 2,5-mal tiefer dahinter
            dahinter = Koerper(max(0, h.x0 - 8), min(BREITE, h.x1 + 8), max(0, h.yt - 2),
                               szene.horizont + 1, h.tiefe * 2.5)
            neu("bau_dahinter", "fehl", bild_tiefe(szene, [dahinter]), 0.0)
            # G7 / F7: starkes Rauschen, weich
            neu("perfekt_rauschen", "gut", voll, 1.0, rauschen=0.02, weich=4)
            neu("ganz_weg_rauschen", "fehl", ohne, 0.0, rauschen=0.02, weich=4)
            # G6: Glasbau, der Schätzer sieht zu 75 % hindurch
            glas = [1.0 / (0.25 / v + 0.75 / o) for v, o in zip(voll, ohne)]
            neu("glasbau", "gut", glas, 1.0)
            # L: Haus nur 60 / 70 / 80 % der Breite, und die dichte Reihe quer über die Schwelle
            for seite in ("links", "oben"):
                for schritt in range(6, 20):
                    anteil = schritt / 20
                    klasse = "fehl" if anteil <= 0.55 else ("gut" if anteil >= 0.85
                                                            else "uebergang")
                    neu(f"teil_{seite}_{anteil:.2f}", klasse,
                        bild_tiefe(szene, teilbau(h, anteil, seite)), anteil)
            # Ortsfeld von 0,3 bis 0,8, mit Rauschen wie bei einem echten Schätzer
            for feld in (0.3, 0.45, 0.55, 0.6, 0.7, 0.8):
                neu(f"feld_{feld:.2f}_perfekt", "gut", voll, 1.0, feld=feld, gamma=1.3,
                    rauschen=0.01, weich=2)
                neu(f"feld_{feld:.2f}_ganz_weg", "fehl", ohne, 0.0, feld=feld, gamma=1.3,
                    rauschen=0.01, weich=2)
                neu(f"feld_{feld:.2f}_halb_weg", "fehl",
                    bild_tiefe(szene, teilbau(h, 0.5, "links")), 0.5, feld=feld, gamma=1.3,
                    rauschen=0.01, weich=2)
            # G8 / F8: Maske 3 rechts, 2 hoch, 0,9-fach gegenüber dem Bild
            mb, mh = round(0.9 * bw), round(0.9 * bh)
            versetzt = Szene(szene.horizont,
                             Koerper(h.x0 + 3, h.x0 + 3 + mb, h.yf - 2 - mh, h.yf - 2,
                                     h.tiefe), szene.bodenanteil, szene.hausanteil)
            neu("maske_versetzt_perfekt", "gut", voll, 1.0, szene_=versetzt)
            neu("maske_versetzt_ganz_weg", "fehl", ohne, 0.0, szene_=versetzt)
            # G5 / F5: Haus am linken Bildrand angeschnitten
            rand_haus = Koerper(0, bw // 2 + 4, h.yt, h.yf, h.tiefe)
            rand = Szene(szene.horizont, rand_haus, szene.bodenanteil, szene.hausanteil)
            neu("bildrand_perfekt", "gut", bild_tiefe(rand, [rand_haus]), 1.0, szene_=rand)
            neu("bildrand_ganz_weg", "fehl", bild_tiefe(rand, []), 0.0, szene_=rand)
    for pol in (-1, +1):
        p = "m" if pol < 0 else "p"
        for kurz, szene in (("hang", hang), ("klein", klein)):
            paare.append(_paar(f"{kurz}{p}-perfekt", "gut", szene,
                               bild_tiefe(szene, [szene.haus]), pol, 1.0))
            paare.append(_paar(f"{kurz}{p}-ganz_weg", "fehl", szene,
                               bild_tiefe(szene, []), pol, 0.0))
    return paare


def zufallsfall2(startwert: int) -> dict:
    """Zufallsfall der Runde 2: wie :func:`zufallsfall`, dazu Hang, Glas, Verdeckung, Giebel,
    tieferes Volumen, Bäume, Textur, Bau dahinter, Ortsfeld bis 0,8 und Rauschen bis 0,03.

    Returns:
        ``{soll, maske, roh, polaritaet, klasse, art, lage, im_umriss}`` mit ``klasse`` aus
        ``gut``, ``fehl``, ``uebergang``, ``abgegrenzt``.
    """
    z = random.Random(1_000_003 + startwert)
    horizont = z.randint(4, 44)
    yf = z.randint(horizont + 5, HOEHE - 3)
    yt = z.randint(2, max(2, yf - 12))
    bw = z.randint(10, 64)
    lage = z.choices(("frei", "wand", "ohne_gelaende", "rand"), (0.76, 0.08, 0.08, 0.08))[0]
    x0 = 0 if lage == "rand" else z.randint(8, BREITE - bw - 8)
    gefaelle = z.choice((0.0, 0.0, 0.0, 0.06, -0.06, 0.12)) if lage == "frei" else 0.0
    haus = Koerper(x0, x0 + bw, yt, yf, bodentiefe(yf - 1, horizont),
                   z.choice((0.0, 0.0, 0.1, 0.2)))
    szene = Szene(horizont, haus, 0.0, 0.0, gefaelle=gefaelle)
    soll, maske = soll_karte(szene)
    bh = yf - yt
    art = z.choice(("da", "da", "versatz", "teil", "teil", "weg", "weg", "ersetzt", "glas",
                    "verdeckt", "giebel", "tiefer", "baeume", "textur", "dahinter"))
    klasse, im_umriss = "gut", 1.0
    hinten: list[Koerper] = []
    if lage == "wand":
        hinten = [Koerper(0, BREITE, yt, yf, haus.tiefe)]
        for y in range(yt, yf):
            for x in range(BREITE):
                if not maske[y * BREITE + x]:
                    soll[y * BREITE + x] = min(soll[y * BREITE + x], haus.tiefe)
    if lage == "ohne_gelaende":
        soll = [wert if m else MARKE for wert, m in zip(soll, maske)]
    ohne = bild_tiefe(szene, hinten)
    voll = bild_tiefe(szene, hinten + [haus])
    if art == "da":
        tiefe = voll
    elif art == "versatz":
        dx, dy = z.randint(-2, 2), z.randint(-1, 1)
        koerper = [Koerper(haus.x0 + dx, haus.x1 + dx, haus.yt + dy, haus.yf + dy,
                           haus.tiefe, haus.schraege)]
        tiefe, im_umriss = bild_tiefe(szene, hinten + koerper), _anteil_im_umriss(maske, koerper)
        klasse = "gut" if im_umriss >= 0.85 else "uebergang"
    elif art == "teil":
        koerper = teilbau(haus, z.random(), z.choice(("links", "rechts", "oben")))
        tiefe, im_umriss = bild_tiefe(szene, hinten + koerper), _anteil_im_umriss(maske, koerper)
        klasse = "gut" if im_umriss >= 0.85 else ("fehl" if im_umriss <= 0.55 else "uebergang")
    elif art == "weg":
        tiefe, im_umriss, klasse = ohne, 0.0, "fehl"
    elif art == "ersetzt":
        kb, kh = z.randint(6, 50), z.randint(6, 45)
        kx = z.randint(0, BREITE - kb)
        kf = z.randint(horizont + 3, HOEHE - 1)
        koerper = [Koerper(kx, kx + kb, max(0, kf - kh), kf, bodentiefe(kf - 1, horizont))]
        tiefe, im_umriss = bild_tiefe(szene, hinten + koerper), _anteil_im_umriss(maske, koerper)
        klasse = "fehl" if im_umriss <= 0.55 else "uebergang"
    elif art == "glas":
        durch = z.uniform(0.3, 0.9)
        tiefe = [1.0 / ((1.0 - durch) / v + durch / o) for v, o in zip(voll, ohne)]
    elif art == "verdeckt":
        davor = baeume(haus, dichte=z.uniform(0.5, 1.0), faktor=z.uniform(0.5, 0.8),
                       startwert=startwert, unten_ab=haus.yt + bh // 2)
        tiefe = bild_tiefe(szene, hinten + [haus] + davor)
    elif art == "giebel":
        tiefe, im_umriss = bild_tiefe(szene, hinten + satteldach(haus)), 0.85
    elif art == "tiefer":
        faktor = z.uniform(1.05, 3.0)
        tiefe = bild_tiefe(szene, hinten + [Koerper(haus.x0, haus.x1, haus.yt, haus.yf,
                                                    haus.tiefe * faktor)])
        klasse = "fehl" if faktor >= M2_FEHL_AB else "uebergang"
    elif art == "baeume":
        tiefe = bild_tiefe(szene, hinten + baeume(haus, dichte=z.uniform(0.5, 1.0),
                                                  faktor=z.uniform(0.9, 1.1),
                                                  startwert=startwert))
        klasse, im_umriss = "abgegrenzt", 0.0
    elif art == "textur":
        tiefe = [d * (1.0 + z.uniform(-0.3, 0.3)) if m and d < HIMMEL_M else d
                 for d, m in zip(ohne, maske)]
        klasse, im_umriss = "fehl", 0.0
    else:
        dahinter = Koerper(max(0, haus.x0 - 8), min(BREITE, haus.x1 + 8), max(0, yt - 2),
                           horizont + 1, haus.tiefe * z.uniform(2.0, 4.0))
        tiefe, klasse, im_umriss = bild_tiefe(szene, hinten + [dahinter]), "fehl", 0.0
    polaritaet = z.choice((-1, +1))
    roh = schaetzkarte(tiefe, polaritaet=polaritaet, startwert=startwert,
                       feld=z.uniform(0.0, 0.8), gamma=z.uniform(0.5, 2.0),
                       weich=z.randint(0, 4), rauschen=z.uniform(0.001, 0.03))
    return {"soll": soll, "maske": maske, "roh": roh, "polaritaet": polaritaet,
            "klasse": klasse, "art": art, "lage": lage, "im_umriss": im_umriss}
