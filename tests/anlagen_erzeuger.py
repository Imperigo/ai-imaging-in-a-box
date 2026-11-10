"""Der Erzeuger des synthetischen Anlagen-Satzes (A0300 «Formtreue je Baukörper»).

**Wozu.** Die Formprüfung (``varianten.deckung``) zählt die Kanten des KI-Bilds gegen das
Grundbild über die GANZE Hausfläche. In einer Anlage mit mehreren Bauten kann die KI darum den
Hauptbau auflösen, und das Bild heisst trotzdem «deckungsgleich»: Die Nebenbauten halten ihre
Kanten und heben die Zahl über die Schwelle (belegt am Wettbewerbsmodell, 24.10.2026:
Kanten-Deckung 0,256 gegen 0,25, Hauptbau in grüne Flecken aufgelöst). Dieser Erzeuger baut
solche Bildpaare, damit der Fehler ohne Grafikkarte und ohne echte Projektdaten messbar ist.

**Was er baut.** Eine Anlage von oben: ein Hauptbau mit Hof (ein Ring) und zwei bis vier
Nebenbauten auf einem Grund mit Wegen. Jeder Bau trägt eine Zeichnung aus kleinen dunklen
Öffnungen im Raster (wie Oberlichter oder Fenster). Je Fall drei Dinge gleicher Grösse:

* das **Grundbild** (helle Bauten mit Öffnungen, wie ein Gipsmodell),
* das **KI-Bild** in einer von vier Arten (unten),
* die **Bauwerksmaske** (wahr auf den Bauten, der Hof gehört nicht dazu).

**Die Arten des KI-Bilds.**

* ``intakt``: alle Bauten halten ihre Form. Die KI tönt um, lässt einzelne Öffnungen weg (nie
  zwei nebeneinander) und malt einzelne dazu (wie am Gerät: «Form ja» lag bei Kanten-Deckung
  0,27 bis 0,75, nie bei 1).
* ``flecken``: der Hauptbau samt Hof ist in grüne Flecken aufgelöst, die Nebenbauten halten.
* ``platte``: der Hauptbau samt Hof ist eine glatte Platte, die Nebenbauten halten.
* ``verfleckt``: wenige grosse Flecken decken den grösseren Teil des Hauptbaus (mindestens 60
  bis 85 % seiner Fläche), der Rest hält.

Alles hängt allein am Startwert (``random.Random``), reine stdlib, keine Datei wird gelesen.
Die Zahlen hier sind **gesetzt, nicht am Gerät geeicht**: Sie stellen den belegten Fehler nach,
sie ersetzen keine Messung am echten Bild.

**Drei Kunstfehler, die der Satz vermeidet (alle am 10.11.2026 gemessen, mit der ersten
Fassung: lange Fugen statt Öffnungen).**

1. *Zusammenhängender Verlust ist kein «intakt».* Bei unabhängigem Weglassen fehlten an einem
   Hauptbau drei Fugen nebeneinander, fast die halbe Länge war glatt (Startwert 20). Das ist
   die Art «Platte» im Kleinen. Darum fehlen nie zwei Öffnungen nebeneinander.
2. *Die Kantenquote.* Die Kantenfindung (``umriss.bildkanten``) lässt höchstens die stärksten
   15 % der Bildpunkte als Kante gelten. Bei 60 % Hausanteil und dichter Zeichnung waren
   15,2 % des Grundbilds Kante; im KI-Bild fielen dann Kanten heraus, die gemalt waren, und
   ein gehaltener Bau hiess «verfleckt» (Startwert 48). Darum richtet sich der Abstand der
   Öffnungen nach dem Hausanteil (:func:`raster_min`), und die Wege sind nur schwach abgesetzt.
3. *Zwei, drei Linien sind keine Zeichnung.* Mit weiten Fugen trug ein Bau noch drei bis sechs
   Linien; eine fehlende Linie verschob seine Zahl um ein Drittel. Darum kleine Öffnungen:
   Ein Bau trägt Dutzende, und jede zählt für sich.
"""
from __future__ import annotations

import random

#: Bildgrösse des Satzes. Klein, damit die Kantenfindung in reinem Python schnell bleibt.
BREITE, HOEHE = 256, 160

ART_INTAKT = "intakt"
ART_FLECKEN = "flecken"
ART_PLATTE = "platte"
ART_VERFLECKT = "verfleckt"
ARTEN_AUFGELOEST = (ART_FLECKEN, ART_PLATTE, ART_VERFLECKT)

#: Die Grenzen des Auftrags: Hausanteil 15 bis 60 % der Bildfläche, zwei bis vier Nebenbauten.
HAUSANTEIL_MIN, HAUSANTEIL_MAX = 0.15, 0.60

#: Wie stark ein Bau im KI-Bild von seinem Grundbild abweicht, ohne dass seine Form verloren
#: ist: Anteil der Öffnungen, die fehlen, und Anteil, der dazukommt (je Bau zufällig aus der
#: Spanne, beide bezogen auf die Zahl der Öffnungen des Baus). Gesetzt so, dass ein gehaltener
#: Bau klar über der Schwelle der Deckung (0,25) liegt: Ein Bau AUF der Schwelle ist schon nach
#: dem alten Massstab ein Grenzfall und kein Beleg für «Form gehalten».
KI_WEG = (0.03, 0.25)
KI_DAZU = (0.0, 0.20)

#: «Verfleckt» im Satz: Die Flecken decken mindestens diesen Teil des Baus (je Fall zufällig aus
#: der Spanne). Gemessen an der Reihe über den Fleckanteil (10.11.2026): bis 30 % gedeckt
#: schlägt die Prüfung nie an, ab 60 % immer, dazwischen teils. Der Satz nimmt darum nur, was
#: eindeutig verfleckt ist; der Übergang steht als Reihe in den Proben.
VERFLECKT_SPANNE = (0.60, 0.85)

#: Eine Öffnung: so breit und so hoch in Bildpunkten.
OEFFNUNG = (3, 4)
#: So viele Kantenpunkte gibt eine Öffnung der Kantenfindung (gezählt, gerundet).
KANTEN_JE_OEFFNUNG = 30
#: Der Anteil der Bildfläche, den die Kanten der Öffnungen zusammen höchstens füllen sollen,
#: damit mit Umrissen und Zugaben der KI die Quote von 15 % nicht greift.
KANTEN_ANTEIL_MAX = 0.075

_HELL, _FUGE = (206, 204, 198), (128, 126, 122)
_GRUND, _WEG = (120, 132, 110), (127, 138, 117)
_GRUEN = ((58, 104, 52), (96, 146, 78), (134, 172, 104), (40, 78, 44), (112, 158, 92))
_PLATTE = (176, 178, 172)


def _anordnung(rng: random.Random, ziel_anteil: float, n_neben: int) -> dict:
    """Hauptbau links (mit Hof) und die Nebenbauten rechts untereinander, alle getrennt."""
    rand = 4
    haupt_teil = rng.uniform(0.40, 0.62)            # Anteil des Hauptbaus an der Hausfläche
    flaeche = ziel_anteil * BREITE * HOEHE
    # Der Ring: aussen w x h, Hof innen. Ringstärke 24 % der kürzeren Seite.
    zone_b = int(BREITE * rng.uniform(0.52, 0.60))
    seiten = rng.uniform(1.15, 1.6)
    # Ringfläche = w*h - (w-2t)*(h-2t) mit t = 0.24*h  ->  rund 0.73*w*h bei w = seiten*h
    h = (haupt_teil * flaeche / (seiten * (1 - (1 - 0.48 / seiten) * 0.52))) ** 0.5
    w = seiten * h
    w = min(int(w), zone_b - 2 * rand)
    h = min(int(h), HOEHE - 2 * rand)
    t = max(5, int(0.24 * min(w, h)))
    x0 = rand + rng.randint(0, max(0, zone_b - 2 * rand - w))
    y0 = rand + rng.randint(0, max(0, HOEHE - 2 * rand - h))
    haupt = (x0, y0, x0 + w, y0 + h)
    hof = (x0 + t, y0 + t, x0 + w - t, y0 + h - t)
    ring = w * h - (w - 2 * t) * (h - 2 * t)
    # Die Nebenbauten: je eine Zelle in der rechten Zone, darin ein Rechteck.
    rest = max(0.0, flaeche - ring)
    zx0, zx1 = zone_b + rand, BREITE - rand
    zelle_h = (HOEHE - 2 * rand) / n_neben
    neben = []
    for i in range(n_neben):
        ziel = rest / n_neben * rng.uniform(0.8, 1.2)
        max_b, max_h = zx1 - zx0, int(zelle_h) - 4
        b = min(max_b, max(12, int((ziel * rng.uniform(1.2, 2.2)) ** 0.5)))
        hh = min(max_h, max(8, int(ziel / b)))
        b = min(max_b, max(12, int(ziel / hh)))
        nx = zx0 + rng.randint(0, max_b - b)
        ny = rand + int(i * zelle_h) + 2 + rng.randint(0, max(0, max_h - hh))
        neben.append((nx, ny, nx + b, ny + hh))
    eng = raster_min(ziel_anteil)
    return {"haupt": haupt, "hof": hof, "neben": neben, "spiegeln": rng.random() < 0.5,
            "raster_haupt": eng + rng.randint(0, 3),
            "raster_neben": [eng + rng.randint(0, 3) for _ in neben]}


def raster_min(hausanteil: float) -> int:
    """Der kleinste Abstand der Öffnungen, bei dem die Kantenquote nicht greift."""
    return max(8, int(-(-(KANTEN_JE_OEFFNUNG * hausanteil / KANTEN_ANTEIL_MAX) ** 0.5 // 1)))


def _in(k, x, y) -> bool:
    return k[0] <= x < k[2] and k[1] <= y < k[3]


def _oeffnungen(kasten, raster: int, hof=None) -> list[tuple[int, int]]:
    """Die Lagen der Öffnungen eines Baus (linke obere Ecke), im Raster, 2 Punkte vom Rand."""
    ob, oh = OEFFNUNG
    lagen = []
    for y in range(kasten[1] + 3, kasten[3] - oh - 2, raster):
        for x in range(kasten[0] + 3, kasten[2] - ob - 2, raster):
            if hof is not None and not (x + ob + 2 <= hof[0] or x - 2 >= hof[2]
                                        or y + oh + 2 <= hof[1] or y - 2 >= hof[3]):
                continue
            lagen.append((x, y))
    return lagen


def _male_bau(bild, kasten, oeffnungen, *, hell=_HELL, dunkel=_FUGE, ausser=None) -> None:
    for y in range(kasten[1], kasten[3]):
        for x in range(kasten[0], kasten[2]):
            if ausser is None or not _in(ausser, x, y):
                bild[y * BREITE + x] = hell
    for (ox, oy) in oeffnungen:
        for y in range(oy, oy + OEFFNUNG[1]):
            for x in range(ox, ox + OEFFNUNG[0]):
                bild[y * BREITE + x] = dunkel


def _grundflaeche(rng: random.Random) -> list:
    bild = [_GRUND] * (BREITE * HOEHE)
    for _ in range(3):                                  # Wege quer durch die Anlage
        y = rng.randint(6, HOEHE - 8)
        for x in range(BREITE):
            for d in (0, 1):
                bild[(y + d) * BREITE + x] = _WEG
    return bild


def _toene(farbe, faktoren, rng: random.Random, rauschen: int):
    return tuple(max(0, min(255, int(c * f) + rng.randint(-rauschen, rauschen)))
                 for c, f in zip(farbe, faktoren))


def _ki_oeffnungen(rng: random.Random, oeffnungen: list, kasten, raster: int, hof,
                   weg: float, dazu: float, *, verstreut: bool = True) -> list:
    """Die Öffnungen, wie die KI sie malt: einzelne fehlen, einzelne kommen dazwischen dazu.

    Nie fehlen zwei nebeneinander (Kunstfehler 1 im Kopf dieser Datei); mit ``verstreut``
    falsch fällt jede Öffnung für sich, für die Reihen bis «alles fehlt». Dazu kommen
    ``dazu`` mal so viele, wie der Bau hat, auf den Lücken des Rasters (bis zum Dreifachen:
    zuerst schräg versetzt, dann waagrecht, dann senkrecht).
    """
    bleiben, vorige = [], None
    for (x, y) in oeffnungen:
        neben_fehlt = verstreut and vorige is not None and vorige[1] == y and vorige[2]
        fehlt = (not neben_fehlt) and rng.random() < weg
        if not fehlt:
            bleiben.append((x, y))
        vorige = (x, y, fehlt)
    halb = raster // 2
    ob, oh = OEFFNUNG

    def frei(dx, dy):
        return [(x + dx, y + dy) for (x, y) in oeffnungen
                if x + dx + ob + 2 <= kasten[2] and y + dy + oh + 2 <= kasten[3]
                and (hof is None or x + dx + ob + 2 <= hof[0] or x + dx - 2 >= hof[2]
                     or y + dy + oh + 2 <= hof[1] or y + dy - 2 >= hof[3])]
    luecken = frei(halb, halb)
    n_neu = int(round(dazu * len(oeffnungen)))
    if n_neu <= len(luecken):
        return bleiben + rng.sample(luecken, n_neu)
    mehr = frei(halb, 0) + frei(0, halb)
    return bleiben + luecken + rng.sample(mehr, min(len(mehr), n_neu - len(luecken)))


def _flecken(rng: random.Random, kasten, anzahl: int) -> list:
    return [(rng.uniform(kasten[0], kasten[2]), rng.uniform(kasten[1], kasten[3]),
             rng.choice(_GRUEN), rng.random()) for _ in range(anzahl)]


def _naechster(flecken, x, y):
    return min(flecken, key=lambda f: (f[0] - x) ** 2 + (f[1] - y) ** 2)


def fall(startwert: int, art: str = ART_INTAKT, *, einzelhaus: bool = False,
         fleck_anteil: float | None = None, weg: float | None = None,
         dazu: float | None = None, glatt: tuple = (), ki_malt_auf_glatt: float = 0.0,
         fleck_auf: int = 0) -> dict:
    """Ein Bildpaar des Satzes.

    Args:
        startwert: bestimmt Anordnung, Zeichnung und Abweichungen der KI vollständig.
        art: ``intakt``, ``flecken``, ``platte`` oder ``verfleckt``.
        einzelhaus: nur ein Bau (ein Rechteck ohne Hof) — für die Gegenprobe, dass sich am
            Einzelhaus nichts ändert. ``art`` wirkt dann auf dieses eine Haus.
        fleck_anteil: nur ``verfleckt``: der Teil des Baus, den die Flecken mindestens decken
            (0..1), statt der Spanne 0,55 bis 0,80. Für Reihen quer über die Schwelle.
        weg, dazu: der Anteil der Öffnungen, der in JEDEM Bau fehlt bzw. dazukommt (``dazu``
            bis 3,0), statt der Spannen :data:`KI_WEG` und :data:`KI_DAZU`. Mit ``weg`` fällt
            jede Öffnung für sich, auch zwei nebeneinander.
        glatt: Nummern der Bauten ohne Zeichnung im Grundbild (0 = Hauptbau, 1.. = Nebenbauten).
        ki_malt_auf_glatt: so viele Öffnungen malt die KI auf einen glatten Bau, als Anteil
            dessen, was sein Raster trüge (0 = keine). Der gemeine Fall «Zeichnung dazugemalt».
        fleck_auf: welcher Bau aufgelöst wird (0 = Hauptbau, 1.. = Nebenbau; dort ohne Hof).

    Returns:
        ``{name, art, startwert, breite, hoehe, grund, ki, maske, haupt, hof, neben,
        hausanteil, fleck_bau, fleck_gedeckt}``; ``fleck_gedeckt`` ist der Teil des
        aufgelösten Baus, den Platte oder Flecken wirklich decken (0 bei ``intakt``);
        ``bauten`` sagt je Bau, was wirklich geschah (``oeffnungen`` im Grundbild, davon
        ``erhalten`` im KI-Bild, ``dazu`` gemalte), die Wahrheit für Vergleiche; ``grund`` und ``ki`` sind Listen von ``(r, g, b)``, ``maske`` eine Liste
        von Wahrheitswerten, ``haupt``/``hof``/``neben`` Kästen ``(x0, y0, x1, y1)``.
    """
    if art not in (ART_INTAKT, *ARTEN_AUFGELOEST):
        raise ValueError(f"Art {art!r} gibt es nicht.")
    rng = random.Random(f"anlage-{startwert}-{'einzel' if einzelhaus else 'anlage'}")
    if einzelhaus:
        w, h = rng.randint(90, 160), rng.randint(60, 110)
        x0, y0 = rng.randint(6, BREITE - w - 6), rng.randint(6, HOEHE - h - 6)
        lage = {"haupt": (x0, y0, x0 + w, y0 + h), "hof": None, "neben": [],
                "spiegeln": False, "raster_neben": [],
                "raster_haupt": raster_min(w * h / (BREITE * HOEHE)) + rng.randint(0, 3)}
    else:
        lage = _anordnung(rng, rng.uniform(HAUSANTEIL_MIN + 0.02, HAUSANTEIL_MAX - 0.03),
                          rng.randint(2, 4))
    haupt, hof, neben = lage["haupt"], lage["hof"], lage["neben"]
    boden = _grundflaeche(rng)
    grund = list(boden)
    raster_o_haupt = _oeffnungen(haupt, lage["raster_haupt"], hof)
    raster_o_neben = [_oeffnungen(k, r) for k, r in zip(neben, lage["raster_neben"])]
    o_haupt = [] if 0 in glatt else raster_o_haupt
    o_neben = [[] if i + 1 in glatt else o for i, o in enumerate(raster_o_neben)]
    _male_bau(grund, haupt, o_haupt, ausser=hof)
    for k, o in zip(neben, o_neben):
        _male_bau(grund, k, o)
    maske = [False] * (BREITE * HOEHE)
    for k in (haupt, *neben):
        for y in range(k[1], k[3]):
            for x in range(k[0], k[2]):
                maske[y * BREITE + x] = not (hof is not None and k is haupt and _in(hof, x, y))

    # ---- das KI-Bild: eigener Zufallsstrang, damit `art` die Anordnung nicht verschiebt
    krng = random.Random(f"ki-{startwert}-{art}-{einzelhaus}")
    faktoren = tuple(krng.uniform(0.86, 1.08) for _ in range(3))
    hell = _toene(_HELL, faktoren, krng, 0)
    fuge = _toene(_FUGE, faktoren, krng, 0)
    ki = [_toene(c, (0.9, 1.05, 0.85), krng, 0) for c in boden]      # der Grund wird grüner
    def ki_zeichnung(nr, o, raster_o, k, r, hof_k):
        w = krng.uniform(*KI_WEG) if weg is None else weg
        d = krng.uniform(*KI_DAZU) if dazu is None else dazu
        if nr in glatt:                      # im Grundbild glatt: die KI malt (vielleicht) dazu
            return krng.sample(raster_o, int(round(ki_malt_auf_glatt * len(raster_o))))
        return _ki_oeffnungen(krng, o, k, r, hof_k, w, d, verstreut=weg is None)

    ki_o = {}                                # je Bau: die Öffnungen, die die KI malt
    for i, (k, o, r) in enumerate(zip(neben, o_neben, lage["raster_neben"])):
        ki_o[i + 1] = ki_zeichnung(i + 1, o, raster_o_neben[i], k, r, None)
        _male_bau(ki, k, ki_o[i + 1], hell=hell, dunkel=fuge)
    ki_o[0] = ki_zeichnung(0, o_haupt, raster_o_haupt, haupt, lage["raster_haupt"], hof)
    _male_bau(ki, haupt, ki_o[0], hell=hell, dunkel=fuge, ausser=hof)
    uebermalt = set()                        # Bildpunkte, die Platte oder Flecken decken
    ziel_bau = haupt if fleck_auf == 0 or not neben else neben[min(fleck_auf, len(neben)) - 1]
    fleck_gedeckt = 0.0                     # der Teil des Baus, den Platte oder Flecken decken
    if art == ART_PLATTE:
        platte = _toene(_PLATTE, faktoren, krng, 0)
        for y in range(ziel_bau[1], ziel_bau[3]):
            for x in range(ziel_bau[0], ziel_bau[2]):
                ki[y * BREITE + x] = platte
                uebermalt.add((x, y))
        fleck_gedeckt = 1.0
    elif art in (ART_FLECKEN, ART_VERFLECKT):
        flaeche = (ziel_bau[2] - ziel_bau[0]) * (ziel_bau[3] - ziel_bau[1])
        # Aufgelöst: viele kleine Flecken über den ganzen Bau. Verfleckt: wenige grosse, von
        # denen so viele grün werden, bis der gewählte Teil des Baus gedeckt ist.
        flecken = _flecken(krng, ziel_bau, max(6, flaeche // (390 if art == ART_FLECKEN else 890)))
        zu = {}
        for y in range(ziel_bau[1], ziel_bau[3]):
            for x in range(ziel_bau[0], ziel_bau[2]):
                zu[(x, y)] = flecken.index(_naechster(flecken, x, y))
        if art == ART_FLECKEN:
            gruen = set(range(len(flecken)))
        else:
            ziel = (krng.uniform(*VERFLECKT_SPANNE) if fleck_anteil is None else fleck_anteil) * sum(
                1 for (x, y) in zu if maske[y * BREITE + x])
            je = [0] * len(flecken)
            for (x, y), i in zu.items():
                je[i] += maske[y * BREITE + x]
            gruen, gedeckt = set(), 0
            for i in sorted(range(len(flecken)), key=lambda i: flecken[i][3]):
                if gedeckt >= ziel:
                    break
                gruen.add(i)
                gedeckt += je[i]
        im_bau = [(x, y) for (x, y) in zu if maske[y * BREITE + x]]
        fleck_gedeckt = sum(1 for xy in im_bau if zu[xy] in gruen) / max(1, len(im_bau))
        for (x, y), i in zu.items():
            if i in gruen:
                ki[y * BREITE + x] = flecken[i][2]
                uebermalt.add((x, y))
    ki = [tuple(max(0, min(255, c + krng.randint(-2, 2))) for c in p) for p in ki]
    # Was je Bau WIRKLICH geschah: Öffnungen des Grundbilds, davon im KI-Bild noch da (gemalt
    # und nicht übermalt), und dazugemalte. Die Wahrheit für den Vergleich, je Bau.
    bauten = []
    for nr, (k, o) in enumerate([(haupt, o_haupt)] + list(zip(neben, o_neben))):
        da = [xy for xy in ki_o[nr] if xy not in uebermalt]
        bauten.append({"nr": nr, "kasten": k, "oeffnungen": len(o),
                       "erhalten": len(set(o) & set(da)), "dazu": len(set(da) - set(o))})

    if lage["spiegeln"]:
        def gespiegelt(liste):
            return [liste[y * BREITE + (BREITE - 1 - x)] for y in range(HOEHE) for x in range(BREITE)]
        grund, ki, maske = gespiegelt(grund), gespiegelt(ki), gespiegelt(maske)

        def kasten_g(k):
            return None if k is None else (BREITE - k[2], k[1], BREITE - k[0], k[3])
        haupt, hof, neben = kasten_g(haupt), kasten_g(hof), [kasten_g(k) for k in neben]
        for bau in bauten:
            bau["kasten"] = kasten_g(bau["kasten"])
    return {"name": f"{'einzel' if einzelhaus else 'anlage'}-{startwert:03d}-{art}",
            "art": art, "startwert": startwert, "breite": BREITE, "hoehe": HOEHE,
            "grund": grund, "ki": ki, "maske": maske, "haupt": haupt, "hof": hof,
            "neben": neben, "hausanteil": sum(maske) / len(maske),
            "fleck_bau": ziel_bau if not lage["spiegeln"] else kasten_g(ziel_bau),
            "fleck_gedeckt": round(fleck_gedeckt, 4), "bauten": bauten}


#: Die Startwerte des Satzes: je Startwert eine Anordnung, jede in allen vier Arten.
STARTWERTE = tuple(range(1, 9))
#: Verfleckte Hauptbauten, die im Ganzen nicht als verloren gelten (gemessen über 100
#: Startwerte: sechs solche, 16, 45, 46, 54, 70, 74). Erst die örtliche Prüfung findet sie.
STARTWERTE_NUR_OERTLICH = (16, 45, 46)
#: Die Startwerte der Einzelhäuser für die Gegenprobe.
STARTWERTE_EINZELHAUS = tuple(range(1, 7))


def anlagen_satz() -> list[dict]:
    """Der ganze Satz: 24 intakte Anlagen und 24 aufgelöste (je 8 Flecken, Platte, verfleckt).

    Die 24 intakten sind 8 Anordnungen mit je drei verschiedenen KI-Fassungen (drei
    Startwerte der KI je Anordnung über die Startwerte 1..24 hinweg wäre gleichwertig; hier
    sind es 24 eigene Anordnungen, damit kein intaktes Bild doppelt zählt).
    """
    intakt = [fall(s, ART_INTAKT) for s in range(1, 25)]
    aufgeloest = [fall(s, art) for art in ARTEN_AUFGELOEST for s in STARTWERTE]
    return intakt + aufgeloest


def einzelhaus_satz() -> list[dict]:
    """Einzelhäuser, intakt und in den drei aufgelösten Arten — für «Urteil unverändert»."""
    return [fall(s, art, einzelhaus=True) for art in (ART_INTAKT, *ARTEN_AUFGELOEST)
            for s in STARTWERTE_EINZELHAUS]
