"""Eichsatz Teil (a) zu A0291, Nachbau: die Szene des dritten Gegenlesens, nach ihren Massen.

Das Gegenlesen von Teil (a) (Meldung ``gegenlesen-an-steuerung-A0291-3``, 11.11.2026) baute eine
eigene Szene und fand dort zwei Fälle mit falschem Vorwurf:

* **G1**: EIN Fenster (oder zwei, drei von zwölf) spiegelt ein Haus gegenüber, alle anderen haben
  ihren Glaston. Die Regel «Spiegelung ohne Glaston» griff nur, wenn die Mehrheit spiegelt.
  Behoben über den Rahmen (``fenster_bauteile._spiegelt_einzeln``); im Band, wo das Glasstück
  keinen eigenen Rahmen hat, bleibt der Fall eine benannte Grenze (Klasse ``grenze``).
* **G2**: Ein breiter Steg (6 Bildpunkte, im ID-Pass Wand) teilt jedes Fenster in zwei Scheiben
  von 8 Bildpunkten Breite; mit waagrechtem Versatz 4 hiess eine Scheibe «wie die Wand daneben».

Sein Erzeuger liegt nicht im Repo; dieser baut die Szene aus den Massen der Meldung nach.

**Die Szene** (360 x 250): Dach y 0 bis 19, Wand y 20 bis 219 und x 6 bis 353, Boden ab y 220,
sonst Himmel. Zwei Geschosse (Glas-Oberkante y 50 und 130), Glas 22 breit und 30 hoch, sechs
Fenster je Geschoss ab x 30 im Abstand 52, Rahmen 3 Bildpunkte (Grundbild 78, 78, 80; im KI-Bild
das 0,92-Fache). ``band``: ein Glasstück je Geschoss. Glas im Grundbild 145, 168, 190, Korn 2.
Im KI-Bild die Wand 0,88 x Farbe + 0,12 x Mittel mit Korn 3,5; die Scheiben reihum blau (oben
168, 190, 216 bis unten 132, 158, 190), dunkel (52, 60, 76, oben 18 heller) und wie im Grundbild
(0,96-fach), Korn Glas 5. ``spieg_haus``: die ganze Scheibe 132, 118, 104, jede sechste Spalte 22
heller. ``spieg_oben``: die oberen 40 % Himmel (176, 197, 222), darunter ``spieg_haus``.
Übermalt samt Rahmen: grau (155 bis 182), Fassade (die Wand des KI-Bilds) oder warm (215 bis 238,
165 bis 188, 80 bis 105). Ein Versatz verschiebt das ganze KI-Bild.

Der Erzeuger braucht numpy (nur in den Proben, nicht im Kern) und ist fest gesät.
"""
from __future__ import annotations

import numpy as np

import fenster_paare2 as _fp2

BREITE, HOEHE = 360, 250
AUSSEN, WAND, GLAS, RAHMEN, DACH, BODEN = range(6)
KENNFARBE = _fp2.KENNFARBE
TABELLE = _fp2.TABELLE
GLAS_GRUND = (145, 168, 190)
#: Name und Wandfarbe (aus der Meldung des Gegenlesens).
WAENDE = (
    ("beige", (215, 205, 185)),
    ("anthrazit", (58, 60, 62)),
    ("klinker", (150, 70, 55)),
    ("dunkelgruen", (50, 70, 55)),
    ("weiss", (232, 230, 224)),
    ("dunkelholz", (70, 52, 40)),
)
BEIGE, ANTHRAZIT, KLINKER, DUNKELGRUEN, WEISS, DUNKELHOLZ = range(6)
DUNKLE = (ANTHRAZIT, DUNKELGRUEN, DUNKELHOLZ)
GESCHOSSE = (50, 130)
GLAS_B, GLAS_H, ANZAHL, ABSTAND, X_ERST, RAHMEN_B = 22, 30, 6, 52, 30, 3
STILE = ("blau", "dunkel", "wie-grund")


def name_von(f: dict) -> str:
    teile = [f["gruppe"], WAENDE[f["wand"]][0], f["anordnung"]]
    if f.get("steg"):
        teile.append(f"steg{f['steg']}-{f.get('steg_stoff', 'wand')}")
    if f.get("spiegelt"):
        teile.append(f.get("spiegel_stil", "spieg_haus") + "-" + "+".join(str(n) for n in f["spiegelt"]))
    if f.get("art"):
        teile.append(f["art"] + "-" + "+".join(str(n) for n in f.get("uebermalt", ())))
    if f.get("versatz"):
        teile.append("versatz{},{}".format(*f["versatz"]))
    return "/".join(str(t) for t in teile)


def _geometrie(f: dict) -> dict:
    band = f["anordnung"] == "band"
    bild = np.full((HOEHE, BREITE), AUSSEN, dtype=np.int8)
    bild[0:20, 6:354] = DACH
    bild[20:220, 6:354] = WAND
    bild[220:, :] = BODEN
    nummer = np.full((HOEHE, BREITE), -1, dtype=np.int16)
    fenster = []
    for oben in GESCHOSSE:
        for n in range(ANZAHL):
            x0 = X_ERST + n * ABSTAND
            x1 = x0 + (ABSTAND - 1 if band else GLAS_B - 1)
            r = 0 if band else RAHMEN_B
            if not band:
                bild[oben - r:oben + GLAS_H + r, x0 - r:x1 + 1 + r] = RAHMEN
            bild[oben:oben + GLAS_H, x0:x1 + 1] = GLAS
            if f.get("steg") and not band:
                # Ein senkrechter Steg in der Mitte: aus Wand (G2) oder aus Rahmen.
                s = f["steg"]
                xs = x0 + (GLAS_B - s) // 2
                bild[oben:oben + GLAS_H, xs:xs + s] = WAND if f.get("steg_stoff", "wand") == "wand" else RAHMEN
            nummer[oben - r:oben + GLAS_H + r, x0 - r:x1 + 1 + r] = len(fenster)
            fenster.append((x0, x1, oben, oben + GLAS_H - 1))
    return {"bild": bild, "nummer": nummer, "fenster": fenster, "band": band}


def _scheibe(stil: str, x0, x1, y0, y1, xx, yy, rng):
    form = xx.shape + (3,)
    anteil = ((yy - y0) / max(1, y1 - y0))[..., None]
    if stil == "blau":
        return np.array((168.0, 190.0, 216.0)) * (1 - anteil) + np.array((132.0, 158.0, 190.0)) * anteil
    if stil == "dunkel":
        return np.array((52.0, 60.0, 76.0)) + 18.0 * (1 - anteil)
    if stil == "wie-grund":
        return np.broadcast_to(np.array(GLAS_GRUND) * 0.96, form).copy()
    if stil == "spieg_haus":
        return np.array((132.0, 118.0, 104.0)) + np.where(xx % 6 == 0, 22.0, 0.0)[..., None]
    if stil == "spieg_oben":
        haus = np.array((132.0, 118.0, 104.0)) + np.where(xx % 6 == 0, 22.0, 0.0)[..., None]
        return np.where(anteil < 0.4, np.array((176.0, 197.0, 222.0)), haus)
    raise ValueError(stil)


def paar(f: dict) -> dict:
    name = name_von(f)
    rng = _fp2._wuerfel(name)                                          # noqa: SLF001
    g = _geometrie(f)
    _, wand = WAENDE[f["wand"]]
    bild, nummer, fenster = g["bild"], g["nummer"], g["fenster"]
    form = (HOEHE, BREITE)
    yy, xx = np.mgrid[0:HOEHE, 0:BREITE]
    rahmen = (78, 78, 80)
    fest = {DACH: (88, 84, 80), BODEN: (120, 116, 108), AUSSEN: (190, 205, 225), RAHMEN: rahmen,
            WAND: wand, GLAS: GLAS_GRUND}
    grund = np.zeros(form + (3,))
    for stoff, farbe in fest.items():
        grund[bild == stoff] = farbe
    grund += _fp2._korn(_fp2._wuerfel(name + "/grund"), form, 2.0)    # noqa: SLF001
    wand_ki = np.array(wand) * 0.88 + 0.12 * (sum(wand) / 3.0)
    ki = np.zeros(form + (3,))
    for stoff, farbe in {DACH: (84, 82, 80), BODEN: (118, 114, 108), AUSSEN: (186, 202, 224),
                         RAHMEN: tuple(0.92 * c for c in rahmen)}.items():
        ki[bild == stoff] = farbe
    wandbild = wand_ki + _fp2._korn(rng, form, 3.5)                    # noqa: SLF001
    ki[bild == WAND] = wandbild[bild == WAND]
    glasbild = np.zeros(form + (3,))
    spiegelt = set(f.get("spiegelt", ()))
    for n, (x0, x1, y0, y1) in enumerate(fenster):
        hier = (nummer == n) & (bild == GLAS)
        stil = f.get("spiegel_stil", "spieg_haus") if n in spiegelt else STILE[n % 3]
        glasbild[hier] = _scheibe(stil, x0, x1, y0, y1, xx, yy, rng)[hier]
    glasbild += _fp2._korn(rng, form, 5.0)                             # noqa: SLF001
    ki[bild == GLAS] = glasbild[bild == GLAS]
    art = f.get("art")
    for n in f.get("uebermalt", ()):
        hier = (nummer == n) & (bild == GLAS) if g["band"] else (nummer == n) & ((bild == GLAS) | (bild == RAHMEN))
        if art == "grau":
            farbe = rng.uniform(155, 182) * np.ones(form + (3,)) + _fp2._korn(rng, form, 4.0)  # noqa: SLF001
        elif art == "fassade":
            farbe = wand_ki + _fp2._korn(rng, form, 3.5)               # noqa: SLF001
        elif art == "warm":
            ton = np.array((rng.uniform(215, 238), rng.uniform(165, 188), rng.uniform(80, 105)))
            farbe = ton + _fp2._korn(rng, form, 4.0)                   # noqa: SLF001
        else:
            raise ValueError(art)
        ki[hier] = farbe[hier]
    if f.get("versatz"):
        ki = _fp2._versetzt(ki, *f["versatz"])                         # noqa: SLF001

    def liste(feld):
        return list(map(tuple, np.clip(np.rint(feld), 0, 255).astype(int).reshape(-1, 3).tolist()))
    kennfarben = np.array([KENNFARBE[s] for s in range(6)])
    ziele = [{"x0": fenster[n][0], "y0": fenster[n][2], "x1": fenster[n][1], "y1": fenster[n][3]}
             for n in f.get("uebermalt", ())]
    return {"name": name, "fall": f, "klasse": f["klasse"], "ziele": ziele, "breite": BREITE,
            "hoehe": HOEHE, "ki": liste(ki), "grund": liste(grund),
            "kennung": list(map(tuple, kennfarben[bild].reshape(-1, 3).tolist())), "tabelle": TABELLE}


def fall(**f) -> dict:
    return dict({"gruppe": "g", "klasse": "gegenfall", "anordnung": "einzel"}, **f)


def faelle() -> list:
    """G1, G2 und die Gegenproben dazu (die Erkennung daneben bleibt)."""
    aus = []
    for w in range(len(WAENDE)):
        # G1 · Spiegelung eines Hauses in einem bis drei von zwölf Fenstern, nichts übermalt
        for spiegelt in ((1,), (1, 3), (4, 7, 10)):
            aus.append(fall(gruppe="g1", wand=w, spiegelt=spiegelt))
        aus.append(fall(gruppe="g1", wand=w, spiegelt=(1,), versatz=(2, 1)))
        # Im Band ohne eigenen Rahmen: benannte Grenze (zählt nicht als Fehlalarm, wird aber gezählt)
        aus.append(fall(gruppe="g1", klasse="grenze", wand=w, spiegelt=(1,), anordnung="band"))
        aus.append(fall(gruppe="g1", wand=w, spiegelt=(1,), spiegel_stil="spieg_oben"))
        # G2 · breiter Steg aus Wand, Scheiben 8 breit, Versatz waagrecht 4 (und die Nachbarn davon)
        for v in ((-4, 0), (4, 0), (-3, 0), (0, 4), (0, 0)):
            aus.append(fall(gruppe="g2", wand=w, steg=6, versatz=v))
        aus.append(fall(gruppe="g2", wand=w, steg=4, steg_stoff="rahmen", versatz=(-4, 0)))
        # Die Erkennung bleibt: ehrlich übermalt neben Fenstern mit Glaston, auch neben einer Spiegelung
        for k, art in enumerate(("grau", "fassade", "warm")):
            ziel = (2 + 5 * k + w) % 12
            aus.append(fall(gruppe="ok", klasse="einzeln", wand=w, art=art, uebermalt=(ziel,)))
            aus.append(fall(gruppe="ok", klasse="einzeln", wand=w, art=art, uebermalt=(ziel,),
                            spiegelt=((ziel + 1) % 12,)))
            aus.append(fall(gruppe="ok", klasse="einzeln", wand=w, art=art, uebermalt=(ziel,), anordnung="band"))
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
            "wert": _fp2.werte(p, befund.get("bauteile"))}


def miss(auswahl=None, prozesse: int | None = None) -> dict:
    import os  # noqa: PLC0415
    liste = [f for f in faelle() if auswahl is None or f["gruppe"] in auswahl]
    prozesse = prozesse or min(8, os.cpu_count() or 1)
    if prozesse > 1:
        import multiprocessing  # noqa: PLC0415
        with multiprocessing.get_context("fork" if hasattr(os, "fork") else "spawn").Pool(prozesse) as becken:
            ergebnisse = becken.map(pruefe, liste, chunksize=2)
    else:
        ergebnisse = [pruefe(f) for f in liste]
    aus = {"paare": len(ergebnisse), "fehlalarme": 0, "falsch": [], "gruppen": {}, "grenze": [],
           "ergebnisse": {e["name"]: e for e in ergebnisse}}
    for e in ergebnisse:
        w = e["wert"]
        if e["klasse"] == "grenze":
            if w["fehlalarme"]:
                aus["grenze"].append(e["name"])
            continue
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
            z["still"] += not w["erkannt"] and not w["nicht_messbar"]
    return aus


if __name__ == "__main__":      # python tests/fenster_paare4.py [gruppe ...]
    import sys
    sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[1] / "src"))
    m = miss({a for a in sys.argv[1:]} or None)
    print(f"Szene des dritten Gegenlesens: {m['paare']} Paare, Fehlalarme {m['fehlalarme']}")
    for gruppe, z in sorted(m["gruppen"].items()):
        print(f"  Gruppe {gruppe}: {z['paare']} Paare, Fehlalarme {z['fehlalarme']}, uebermalt {z['uebermalt']}: "
              f"erkannt {z['erkannt']}, nicht messbar {z['nicht_messbar']}, still {z['still']}")
    for name in m["grenze"]:
        print("  GRENZE (Band ohne Rahmen, Vorwurf)", name)
    for name in m["falsch"]:
        print("  FEHLALARM", name, [(b["art"], b["ort"]["x0"], b["ort"]["x1"], b["ort"]["y0"]) for b in
                                    m["ergebnisse"][name]["bauteile"] if b["urteil"] == "uebermalt"][:4])
