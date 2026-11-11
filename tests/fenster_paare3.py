"""Eichsatz Teil (a) zu A0291: die Szene des zweiten Gegenlesens, nachgebaut nach ihren Massen.

Das Gegenlesen der Runde 2 (Meldung ``gegenlesen-an-steuerung-A0291``, 10.11.2026, 15:16 UTC) baute
eine eigene Szene, die der Bau nicht kannte, und fand dort Fehlalarme (M5 Spiegelung eines
Nachbarhauses, M6 Sprossenfenster mit Versatz, dazu Baum, Vorhang und Schatten im Band) und stille
Fehlurteile (M7 grau zwischen hellen Scheiben, M8 nur der untere Teil übermalt). Sein Erzeuger liegt
nicht im Repo; dieser hier baut die Szene aus den Massen der Meldung nach.

**Die Szene** (300 x 210): Dach y 0 bis 23, Wand y 24 bis 184 und x 8 bis 291, Boden ab y 185,
sonst Himmel. Drei Geschosse (Fenster-Oberkante y 40, 90, 140), Glas 16 breit und 22 hoch, sieben
Fenster je Geschoss ab x 24 im Abstand 38. ``einzel``: Rahmen zwei Bildpunkte (Grundbild 80, 80,
82). ``band``: ein Glasstück je Geschoss, im KI-Bild Sprossen zwei Bildpunkte (60, 60, 62).
``sprossen``: im Modell ein Kreuz von zwei Bildpunkten als Rahmen im Glas (vier Scheiben je Fenster).

**Die Klassen** wie in ``fenster_paare2``: ``einzeln``, ``benachbart``, ``alle``, ``gegenfall`` und
``grenze``. Neu ist ``teil`` (nur der untere Teil eines Fensters übermalt): Dort gilt als richtig,
was das Fenster «uebermalt» oder «nicht messbar» nennt; still «gehalten» ist falsch.

Der Erzeuger braucht numpy (nur in den Proben, nicht im Kern) und ist fest gesät.
"""
from __future__ import annotations

import numpy as np

import fenster_paare2 as _fp2

BREITE, HOEHE = 300, 210
AUSSEN, WAND, GLAS, RAHMEN, DACH, BODEN, BAUM = range(7)
KENNFARBE = _fp2.KENNFARBE
TABELLE = _fp2.TABELLE
GLAS_SONST = (150, 172, 188)
#: Name, Wandfarbe, Glasfarbe im Grundbild (aus der Meldung des Gegenlesens).
WAENDE = (
    ("hellgrau", (205, 205, 200), GLAS_SONST),
    ("sandstein", (214, 190, 150), GLAS_SONST),
    ("anthrazit", (62, 62, 64), GLAS_SONST),
    ("dunkelgruen", (52, 72, 58), GLAS_SONST),
    ("rotholz", (120, 62, 44), GLAS_SONST),
    ("blech", (38, 40, 44), (140, 160, 180)),
    ("ocker", (196, 150, 70), GLAS_SONST),
    ("blaugrau", (110, 126, 140), (160, 180, 196)),
)
GESCHOSSE = (40, 90, 140)
GLAS_B, GLAS_H, ANZAHL, ABSTAND, X_ERST = 16, 22, 7, 38, 24
STILE = ("dunkel", "himmel", "wie-grund", "spiegelung")


def name_von(f: dict) -> str:
    teile = [f["gruppe"], WAENDE[f["wand"]][0], f["anordnung"]]
    if f.get("sprossen"):
        teile.append("sprossen")
    if f.get("art"):
        teile.append(f["art"] + "-" + "+".join(str(n) for n in f.get("uebermalt", ())))
    for schluessel in ("stile", "teil", "aenderung", "baum", "vorhang", "schatten", "zufall"):
        if f.get(schluessel) not in (None, "reihum"):
            teile.append(f"{schluessel}={f[schluessel]}")
    return "/".join(str(t) for t in teile)


def _geometrie(f: dict) -> dict:
    band = f["anordnung"] == "band"
    bild = np.full((HOEHE, BREITE), AUSSEN, dtype=np.int8)
    bild[0:24, 8:292] = DACH
    bild[24:185, 8:292] = WAND
    bild[185:, :] = BODEN
    nummer = np.full((HOEHE, BREITE), -1, dtype=np.int16)
    fenster = []
    for oben in GESCHOSSE:
        for n in range(ANZAHL):
            x0 = X_ERST + n * ABSTAND
            x1 = x0 + (ABSTAND - 1 if band else GLAS_B - 1)
            x1 = min(x1, 289)
            if not band:
                bild[oben - 2:oben + GLAS_H + 2, x0 - 2:x1 + 3] = RAHMEN
            bild[oben:oben + GLAS_H, x0:x1 + 1] = GLAS
            if f.get("sprossen") and not band:
                xm, ym = x0 + GLAS_B // 2 - 1, oben + GLAS_H // 2 - 1
                bild[oben:oben + GLAS_H, xm:xm + 2] = RAHMEN
                bild[ym:ym + 2, x0:x1 + 1] = RAHMEN
            rand = 0 if band else 2
            nummer[oben - rand:oben + GLAS_H + rand, x0 - rand:x1 + 1 + rand] = len(fenster)
            fenster.append((x0, x1, oben, oben + GLAS_H - 1))
    kennung = bild.copy()
    baum = None
    if f.get("baum"):
        # Ein Kreis vom Radius 16 um die linke Kante von Fenster 8 (zweites Geschoss).
        x0, _, y0, y1 = fenster[8]
        yy, xx = np.mgrid[0:HOEHE, 0:BREITE]
        baum = (xx - x0) ** 2 + (yy - (y0 + y1) / 2.0) ** 2 <= 16 ** 2
        if f["baum"] == "modell":
            kennung[baum] = BAUM
    return {"bild": bild, "kennung": kennung, "nummer": nummer, "fenster": fenster, "band": band,
            "baum": baum}


def _scheibe(stil: str, glas_grund, x0, x1, y0, y1, xx, yy, rng):
    """Das Glas im KI-Bild für ein Fenster (ganzes Bild gross; nur der Ausschnitt zählt)."""
    form = xx.shape + (3,)
    anteil = ((yy - y0) / max(1, y1 - y0))[..., None]
    if stil == "dunkel":
        v = rng.uniform(35, 75)
        streifen = ((xx + 1.7 * yy) % 19) < 3
        return np.where(streifen[..., None], np.array((140.0, 160.0, 180.0)), np.array((v, v + 9, v + 20)))
    if stil == "himmel":
        return np.array((170.0, 194.0, 220.0)) * (1 - anteil) + np.array((140.0, 164.0, 192.0)) * anteil
    if stil == "hell":
        return np.broadcast_to(np.array((236.0, 242.0, 252.0)), form).copy()
    if stil == "wie-grund":
        return np.broadcast_to(np.array(glas_grund) * rng.uniform(0.92, 1.04), form).copy()
    if stil == "spiegelung":
        # Obere 45 % Himmel, darunter ein Nachbarhaus mit jeder fünften Spalte heller.
        haus = np.array((70.0, 66.0, 64.0)) + np.where(xx % 5 == 0, 25.0, 0.0)[..., None]
        return np.where((anteil < 0.45), np.array((178.0, 198.0, 220.0)), haus)
    if stil == "spiegelung-haus":
        # M5: die ganze Scheibe zeigt ein beiges Haus gegenüber.
        return np.array((120.0, 110.0, 100.0)) + np.where(xx % 5 == 0, 25.0, 0.0)[..., None]
    if stil == "spiegelung-blau":
        return np.array((64.0, 70.0, 82.0)) + np.where(xx % 5 == 0, 25.0, 0.0)[..., None]
    if stil == "sprossen-mix":
        # M5 mit Sprossen: obere Scheiben Himmel, untere ein Haus gegenüber.
        haus = np.array((95.0, 92.0, 90.0)) + np.where(xx % 5 == 0, 25.0, 0.0)[..., None]
        return np.where((anteil < 0.5), np.array((170.0, 194.0, 220.0)), haus)
    raise ValueError(stil)


def paar(f: dict) -> dict:
    name = name_von(f)
    rng = _fp2._wuerfel(name)                                          # noqa: SLF001
    g = _geometrie(f)
    _, wand, glas_grund = WAENDE[f["wand"]]
    bild, nummer, fenster = g["bild"], g["nummer"], g["fenster"]
    form = (HOEHE, BREITE)
    yy, xx = np.mgrid[0:HOEHE, 0:BREITE]
    fest = {DACH: (88, 84, 80), BODEN: (120, 116, 108), AUSSEN: (190, 205, 225), RAHMEN: (80, 80, 82),
            WAND: wand, GLAS: glas_grund}
    grund = np.zeros(form + (3,))
    for stoff, farbe in fest.items():
        grund[bild == stoff] = farbe
    grund += _fp2._korn(_fp2._wuerfel(name_von(dict(f, art=None, uebermalt=(), aenderung=None, teil=None))  # noqa: SLF001
                                      + "/grund"), form, 1.5)
    if f.get("baum") == "modell":
        grund[g["baum"]] = (55, 85, 45)
    wand_ki = np.array(wand) * 0.85 + 0.15 * (sum(wand) / 3.0)
    ki = np.zeros(form + (3,))
    for stoff, farbe in {DACH: (84, 82, 80), BODEN: (118, 114, 108), AUSSEN: (186, 202, 224),
                         RAHMEN: (66, 66, 68)}.items():
        ki[bild == stoff] = farbe
    wandbild = wand_ki + _fp2._korn(rng, form, 4.0)                    # noqa: SLF001
    ki[bild == WAND] = wandbild[bild == WAND]
    stile = f.get("stile", "reihum")
    glasbild = np.zeros(form + (3,))
    for n, (x0, x1, y0, y1) in enumerate(fenster):
        hier = (nummer == n) & (bild == GLAS)
        stil = STILE[(7 * n + 3) % 4] if stile == "reihum" else stile
        glasbild[hier] = _scheibe(stil, glas_grund, x0, x1, y0, y1, xx, yy, rng)[hier]
    glasbild += _fp2._korn(rng, form, float(f.get("korn_glas", 6.0)))  # noqa: SLF001
    if g["band"]:
        for x0, x1, y0, y1 in fenster:
            glasbild[y0:y1 + 1, x0:x0 + 2] = (60, 60, 62)              # die Sprosse
    ki[bild == GLAS] = glasbild[bild == GLAS]
    art = f.get("art")
    for n in f.get("uebermalt", ()):
        x0, x1, y0, y1 = fenster[n]
        hier = (nummer == n) & (bild == GLAS) if g["band"] else (nummer == n) & ((bild == GLAS) | (bild == RAHMEN))
        if f.get("sprossen") and not g["band"]:
            hier = (nummer == n) & (yy >= y0) & (yy <= y1) & (xx >= x0) & (xx <= x1)
        if f.get("teil") == "unten":
            hier = hier & (yy >= y1 - round(0.55 * GLAS_H) + 1)
        if art == "grau":
            farbe = (rng.uniform(150, 185) + np.where(xx % 4 == 0, -5.0, 0.0))[..., None] * np.ones(3) \
                + _fp2._korn(rng, form, 5.0)                           # noqa: SLF001
        elif art == "fassade":
            farbe = wand_ki + _fp2._korn(rng, form, 4.0)               # noqa: SLF001
        elif art == "warm":
            ton = np.array((rng.uniform(210, 240), rng.uniform(160, 190), rng.uniform(70, 105)))
            farbe = ton * np.where(xx % 8 == 0, 0.55, 1.0)[..., None] + _fp2._korn(rng, form, 8.0)  # noqa: SLF001
        elif art == "dunkelgrau":
            farbe = rng.uniform(85, 105) * np.ones(form + (3,)) + _fp2._korn(rng, form, 5.0)  # noqa: SLF001
        else:
            raise ValueError(art)
        ki[hier] = farbe[hier]
    if f.get("vorhang") is not None:
        # Ein Vorhang über die linke Hälfte eines Fensters, mit Falten.
        x0, x1, y0, y1 = fenster[f["vorhang"]]
        stoff = np.array((230.0, 226.0, 214.0)) * np.where(xx % 4 < 2, 1.0, 0.92)[..., None]
        hier = (bild == GLAS) & (xx >= x0) & (xx < x0 + (x1 - x0 + 1) // 2) & (yy >= y0) & (yy <= y1)
        ki[hier] = (0.55 * ki + 0.45 * stoff)[hier]
    if f.get("schatten") is not None:
        # Ein Schatten über drei Fenster samt Wand.
        x0 = fenster[f["schatten"]][0] - 6
        x1 = fenster[min(len(fenster) - 1, f["schatten"] + 2)][1] + 6
        y0, y1 = fenster[f["schatten"]][2] - 6, fenster[f["schatten"]][3] + 6
        ki[y0:y1, x0:x1] *= 0.45
    if f.get("stimmung"):
        ki = ki * np.array(f["stimmung"])
    if f.get("baum"):
        ki[g["baum"]] = (np.array((48.0, 80.0, 40.0)) + _fp2._korn(rng, form, 12.0))[g["baum"]]  # noqa: SLF001
    ki = _fp2._veraendert(ki, f.get("aenderung_schritte"), rng)       # noqa: SLF001

    def liste(feld):
        return list(map(tuple, np.clip(np.rint(feld), 0, 255).astype(int).reshape(-1, 3).tolist()))
    kennfarben = np.array([KENNFARBE[s] for s in range(7)])
    ziele = [{"x0": fenster[n][0], "y0": fenster[n][2], "x1": fenster[n][1], "y1": fenster[n][3]}
             for n in f.get("uebermalt", ())]
    return {"name": name, "fall": f, "klasse": f["klasse"], "ziele": ziele, "breite": BREITE,
            "hoehe": HOEHE, "ki": liste(ki), "grund": liste(grund),
            "kennung": list(map(tuple, kennfarben[g["kennung"]].reshape(-1, 3).tolist())), "tabelle": TABELLE}


def _versatz(dx: int, dy: int) -> dict:
    return {"aenderung_schritte": (("versatz", dx, dy),), "aenderung": f"versatz{dx},{dy}"}


def faelle() -> list:
    """Die Fälle der Szene: M5 bis M8 und die Gegenfälle, die beim Gegenlesen Fehlalarme gaben."""
    aus = []

    def dazu(gruppe, klasse, wand, anordnung, **mehr):
        aus.append(dict(gruppe=gruppe, klasse=klasse, wand=wand, anordnung=anordnung, **mehr))

    for w in range(len(WAENDE)):
        # M5 · Spiegelung eines Nachbarhauses, nichts übermalt
        dazu("m5", "gegenfall", w, "einzel", stile="spiegelung-haus")
        dazu("m5", "gegenfall", w, "einzel", stile="spiegelung-blau")
        dazu("m5", "gegenfall", w, "einzel", sprossen=True, stile="sprossen-mix")
        dazu("m5", "gegenfall", w, "band", stile="spiegelung-haus")
        # M6 · Sprossenfenster, ohne und mit Versatz, nichts übermalt
        dazu("m6", "gegenfall", w, "einzel", sprossen=True)
        for dx, dy in ((-4, 1), (-4, -1), (3, 2), (2, 0)):
            dazu("m6", "gegenfall", w, "einzel", sprossen=True, **_versatz(dx, dy))
        # M6 · übermalt in einem Sprossenfenster: nie still, höchstens «nicht messbar»
        dazu("m6", "einzeln", w, "einzel", sprossen=True, art="warm", uebermalt=(9,))
        # M7 · grau übermalt zwischen hellen Scheiben, und der Gegenfall dazu
        dazu("m7", "gegenfall", w, "einzel", stile="hell")
        dazu("m7", "gegenfall", w, "band", stile="hell")
        for anordnung in ("einzel", "band"):
            dazu("m7", "einzeln", w, anordnung, stile="hell", art="grau", uebermalt=((3 * w + 2) % 21,))
            dazu("m7", "einzeln", w, anordnung, stile="hell", art="grau", uebermalt=((3 * w + 9) % 21,),
                 **_versatz(-2, 0))
        # M8 · nur der untere Teil eines Fensters übermalt
        for anordnung in ("einzel", "band"):
            for k, art in enumerate(("grau", "warm")):
                dazu("m8", "teil", w, anordnung, art=art, teil="unten", uebermalt=((5 * w + 7 * k + 1) % 21,))
        # Weitere Fehlalarme des Gegenlesens: Baum nur im KI-Bild, Vorhang, Schatten (Gegenfälle)
        for anordnung in ("einzel", "band"):
            dazu("gx", "gegenfall", w, anordnung, baum="ki")
            dazu("gx", "gegenfall", w, anordnung, vorhang=(w + 2) % 21)
            dazu("gx", "gegenfall", w, anordnung, schatten=7 + w % 4)
        # Die Erkennung bleibt: ein Fenster je Art, ohne und mit Versatz
        for k, art in enumerate(("grau", "fassade", "warm")):
            for anordnung in ("einzel", "band"):
                dazu("ok", "einzeln", w, anordnung, art=art, uebermalt=((w + 5 * k) % 21,))
            dazu("ok", "einzeln", w, ("einzel", "band")[(w + k) % 2], art=art, uebermalt=((w + 3 * k + 4) % 21,),
                 **_versatz(4, 0))
            dazu("ok", "benachbart", w, ("einzel", "band")[(w + k + 1) % 2], art=art,
                 uebermalt=tuple(range(7 * (k % 3) + 2, 7 * (k % 3) + 4)))
    # Zufallssatz nach den Massen des Gegenlesens
    for i in range(ZUFALL_PAARE):
        aus.append(zufall(i))
    # Die Einzelfälle der Proben (tests/test_fenster_vorsichtig_a0291.py), im selben Durchlauf
    namen = {name_von(f) for f in aus}
    aus.extend(f for f in proben() if name_von(f) not in namen)
    return aus


def probe(**f) -> dict:
    """Ein Einzelfall der Proben (Gruppe ``pr``)."""
    return dict({"gruppe": "pr", "klasse": "gegenfall", "anordnung": "einzel"}, **f)


def proben() -> list:
    """Die Einzelfälle, die die Proben zu M5 bis M8 einzeln ansehen."""
    aus = []
    for w in (2, 3, 5):
        aus.append(probe(wand=w, stile="spiegelung-haus"))
        aus += [probe(wand=w, sprossen=True, **(_versatz(*v) if v else {}))
                for v in (None, (-4, 1), (-4, -1), (3, 2), (2, 0))]
    aus += [probe(wand=w, anordnung="band", stile="spiegelung-haus") for w in (2, 5)]
    aus += [probe(wand=w, sprossen=True, stile="sprossen-mix") for w in (2, 3, 4, 6)]
    aus.append(probe(wand=2, sprossen=True, art="warm", uebermalt=(9,), klasse="einzeln"))
    for w in (0, 6):
        aus.append(probe(wand=w, stile="hell"))
        aus += [probe(wand=w, anordnung=a, stile="hell", art="grau", uebermalt=(9,), klasse="einzeln")
                for a in ("einzel", "band")]
    aus += [probe(wand=w, anordnung=a, art=art, teil="unten", uebermalt=(8,), klasse="teil")
            for w in (0, 2, 6) for a in ("einzel", "band") for art in ("grau", "warm")]
    aus.append(probe(wand=0))
    return aus


#: So viele Paare hat der Zufallssatz (Gruppe ``z``).
ZUFALL_PAARE = 400


def zufall(i: int) -> dict:
    """Ein Fall des Zufallssatzes nach den Massen des Gegenlesens (eigene Saaten, ``RandomState(910000 + i)``).

    Wand und Anordnung zufällig; Glasstil reihum, dunkel, Himmel, wie Grundbild oder hell; ein
    Fünftel der Einzelfenster mit Sprossen; immer ein Versatz (waagrecht -4 bis 4, senkrecht -3 bis
    3); Farbstich, Helligkeit, Unschärfe und Rauschen je mit einer Wahrscheinlichkeit; in der Hälfte
    ein bis drei benachbarte Fenster eines Geschosses übermalt (grau, warm oder Fassade).
    """
    r = np.random.RandomState(910000 + i)
    wand = int(r.randint(len(WAENDE)))
    anordnung = ("einzel", "band")[r.randint(2)]
    stile = ("reihum", "dunkel", "himmel", "wie-grund", "hell")[r.randint(5)]
    schritte = [("versatz", int(r.randint(-4, 5)), int(r.randint(-3, 4)))]
    if r.rand() < 0.5:
        schritte.append(("stich", float(r.uniform(0.92, 1.08)), float(r.uniform(0.92, 1.08)),
                         float(r.uniform(0.92, 1.08))))
    if r.rand() < 0.5:
        schritte.append(("hell", float(r.uniform(0.85, 1.15))))
    if r.rand() < 0.4:
        schritte.append(("unscharf", 1))
    schritte.append(("rausch", float(r.uniform(0.0, 8.0))))
    f = {"gruppe": "z", "wand": wand, "anordnung": anordnung, "stile": stile, "zufall": i,
         "sprossen": anordnung == "einzel" and r.rand() < 0.2, "aenderung_schritte": tuple(schritte),
         "korn_glas": float(r.uniform(2.0, 8.0)), "klasse": "gegenfall"}
    if r.rand() < 0.3:
        f["stimmung"] = ((1.0, 1.0, 1.0), (0.7, 0.72, 0.76), (1.04, 0.93, 0.80), (0.8, 0.84, 0.9))[r.randint(4)]
    if r.rand() < 0.5:
        anzahl = int(r.randint(1, 4))
        geschoss = int(r.randint(3))
        erstes = int(r.randint(ANZAHL - anzahl + 1))
        f.update(art=("grau", "warm", "fassade")[r.randint(3)],
                 uebermalt=tuple(geschoss * ANZAHL + erstes + k for k in range(anzahl)),
                 klasse="einzeln" if anzahl == 1 else "benachbart")
    return f


def werte(p: dict, bauteile) -> dict:
    """Wie ``fenster_paare2.werte``; dazu die Klasse ``teil``: still «gehalten» ist dort falsch."""
    if p["klasse"] == "teil":
        aus = _fp2.werte(dict(p, klasse="einzeln"), bauteile)
        aus["still"] = not aus["erkannt"] and not aus["nicht_messbar"]
        return aus
    aus = _fp2.werte(p, bauteile)
    if p["klasse"] in ("einzeln", "benachbart"):
        aus["still"] = not aus["erkannt"] and not aus["nicht_messbar"]
    return aus


def pruefe(f: dict) -> dict:
    from aiimaging import varianten  # noqa: PLC0415
    p = paar(f)
    befund = varianten.fenster_gehalten(
        p["ki"], p["grund"], p["kennung"], varianten.glasfarben(TABELLE),
        ausser=varianten.nicht_fassade_farben(TABELLE), breite=p["breite"])
    return {"name": p["name"], "gruppe": f["gruppe"], "klasse": p["klasse"], "fall": f, "ziele": p["ziele"],
            "gehalten": befund.get("gehalten"), "band_nicht_gehalten": befund.get("band_nicht_gehalten"),
            "bauteile": befund.get("bauteile"), "hinweis": befund.get("bauteil_hinweis"),
            "wert": werte(p, befund.get("bauteile"))}


def miss(auswahl=None, prozesse: int | None = None) -> dict:
    import os  # noqa: PLC0415
    liste = [f for f in faelle() if auswahl is None or f["gruppe"] in auswahl]
    prozesse = prozesse or min(8, os.cpu_count() or 1)
    if prozesse > 1:
        import multiprocessing  # noqa: PLC0415
        with multiprocessing.get_context("fork" if hasattr(os, "fork") else "spawn").Pool(prozesse) as becken:
            ergebnisse = becken.map(pruefe, liste, chunksize=4)
    else:
        ergebnisse = [pruefe(f) for f in liste]
    aus = {"paare": len(ergebnisse), "fehlalarme": 0, "falsch": [], "still": [], "gruppen": {},
           "ergebnisse": {e["name"]: e for e in ergebnisse}}
    for e in ergebnisse:
        w = e["wert"]
        z = aus["gruppen"].setdefault(e["gruppe"], {"paare": 0, "fehlalarme": 0, "uebermalt": 0, "erkannt": 0,
                                                    "nicht_messbar": 0, "still": 0})
        z["paare"] += 1
        z["fehlalarme"] += w["fehlalarme"]
        aus["fehlalarme"] += w["fehlalarme"]
        if w["fehlalarme"]:
            aus["falsch"].append(e["name"])
        if w["erkannt"] is not None:
            z["uebermalt"] += 1
            z["erkannt"] += bool(w["erkannt"])
            z["nicht_messbar"] += bool(w["nicht_messbar"])
            if w.get("still"):
                z["still"] += 1
                aus["still"].append(e["name"])
    return aus


if __name__ == "__main__":      # python tests/fenster_paare3.py [gruppe ...]
    import sys
    sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[1] / "src"))
    m = miss({a for a in sys.argv[1:] if not a.startswith("--")} or None)
    print(f"Szene des Gegenlesens: {m['paare']} Paare, Fehlalarme {m['fehlalarme']}")
    for gruppe, z in sorted(m["gruppen"].items()):
        print(f"  Gruppe {gruppe}: {z['paare']} Paare, Fehlalarme {z['fehlalarme']}, uebermalt {z['uebermalt']}: "
              f"erkannt {z['erkannt']}, nicht messbar {z['nicht_messbar']}, still {z['still']}")
    for name in m["falsch"]:
        print("  FEHLALARM", name, [(b["art"], b["ort"]["x0"], b["ort"]["y0"]) for b in
                                    m["ergebnisse"][name]["bauteile"] if b["urteil"] == "uebermalt"][:4])
    for name in m["still"]:
        print("  STILL", name)
