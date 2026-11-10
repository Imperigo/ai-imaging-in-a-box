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


def bodentiefe(zeile: int, horizont: int) -> float:
    return K / (zeile - horizont + 0.5)


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
    for y in range(szene.horizont, HOEHE):
        d = bodentiefe(y, szene.horizont)
        for x in range(BREITE):
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
    for y in range(szene.horizont, HOEHE):
        d = bodentiefe(y, szene.horizont)
        for x in range(BREITE):
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
                anteil_im_umriss=_anteil_im_umriss(maske, koerper)))
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
