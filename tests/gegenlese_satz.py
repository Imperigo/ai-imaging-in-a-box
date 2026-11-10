"""Die Paare des Gegenlesens A0300 (10.11.2026), nachgebaut mit ``gegenlese_erzeuger``.

Jeder Fall: ``(gruppe, erwartung, startwert, zustand, regler)``. ``erwartung`` ist

* ``"still"``: ein intaktes Bild (auch versetzt, skaliert, getönt, unscharf, körnig); die
  Prüfung je Baukörper darf es nicht strenger beurteilen als die Deckung von heute;
* ``"auffallen"``: ein Bau ist aufgelöst oder ersetzt; das Bild darf nicht «deckungsgleich»
  heissen, ausser die Prüfung sagt «nicht gemessen» mit Grund;
* ``"offen"``: ein Übergang oder eine Frage der Definition; gezählt, nicht geurteilt.
"""
from __future__ import annotations

KOMBI = (("hell", 1.08), ("stich", (1.05, 1.0, 0.93)), ("korn", 4), ("blur", 1))
FARBE = {"hell+": (("hell", 1.10),), "hell-": (("hell", 0.90),),
         "stich": (("stich", (1.06, 1.0, 0.92)),), "blur": (("blur", 1),),
         "korn": (("korn", 6),), "weich": (("blur", 1), ("korn", 3)), "kombi": KOMBI,
         "ohne": ()}
LAGE = {"versatz1": (("versatz", (1, 0)),), "skala1.01": (("skala", 1.01),),
        "versatz2": (("versatz", (2, 0)),), "versatz3x2": (("versatz", (3, 2)),),
        "versatz3": (("versatz", (3, 0)),), "versatz4": (("versatz", (4, 0)),),
        "versatz4x4": (("versatz", (4, 4)),), "skala1.02": (("skala", 1.02),),
        "skala0.98": (("skala", 0.98),), "skala0.97": (("skala", 0.97),),
        "skala1.03": (("skala", 1.03),), "kombi+versatz2": KOMBI + (("versatz", (2, 0)),)}


def faelle() -> list[tuple]:
    aus = []
    for name, st in FARBE.items():
        for s in (1, 2, 3):
            aus.append(("a-farbe-" + name, "still", s, "intakt", {"stoerungen": st}))
    for name, st in LAGE.items():
        frisch = tuple(range(101, 111))
        starts = frisch if name in ("versatz1", "skala1.01") else (1, 2, 3) + frisch
        for s in starts:
            aus.append(("a-lage-" + name, "still", s, "intakt", {"stoerungen": st}))
    for s in (1, 2, 3):
        aus.append(("a-versatz5", "offen", s, "intakt", {"stoerungen": (("versatz", (5, 0)),)}))
    for zustand in ("flecken", "platte"):
        for s in (11, 12):
            for name in ("hell+", "stich", "blur", "korn", "kombi"):
                aus.append(("b-" + zustand, "auffallen", s, zustand,
                            {"stoerungen": FARBE[name]}))
            for name in ("versatz3x2", "skala1.02", "kombi+versatz2"):
                aus.append(("b-" + zustand, "auffallen", s, zustand,
                            {"stoerungen": LAGE[name]}))
    for s in (21, 22, 23):
        aus.append(("c-glatt", "auffallen", s, "glatt", {}))
    for s in (21, 22):
        aus.append(("c-glatt", "auffallen", s, "glatt", {"stoerungen": KOMBI}))
    for s in (101, 102, 103):
        aus.append(("c-im-grundbild-glatt", "auffallen", s, "flecken",
                    {"glatt_im_grundbild": True}))
    for s in (31, 32, 33, 34):
        aus.append(("d-wiese", "auffallen", s, "wiese", {}))
    for s in (31, 32, 33, 34) + tuple(range(101, 111)):
        aus.append(("d-baeume", "auffallen", s, "baeume", {}))
    for s in (41, 42, 43):
        aus.append(("f-nebenbau-verschoben", "auffallen", s, "intakt",
                    {"nebenbau_verschoben": True}))
    for s in (51, 52, 53) + tuple(range(101, 107)):
        aus.append(("g-beruehrt-flecken", "auffallen", s, "flecken", {"beruehrt": True}))
    for s in (51, 52):
        aus.append(("g-beruehrt-intakt", "still", s, "intakt", {"beruehrt": True}))
    for s in (61, 62):
        aus.append(("h-klein-intakt", "still", s, "intakt", {"hausanteil": 0.05}))
        aus.append(("h-klein-flecken", "auffallen", s, "flecken", {"hausanteil": 0.05}))
    for s in (101, 102):
        aus.append(("h-gross-intakt", "still", s, "intakt", {"gross": True}))
        aus.append(("h-gross-kombi", "still", s, "intakt", {"gross": True, "stoerungen": KOMBI}))
        aus.append(("h-gross-flecken", "auffallen", s, "flecken", {"gross": True}))
    for s in (71, 72):
        for t in (0.35, 0.40, 0.45, 0.50, 0.55, 0.60):
            aus.append(("i-teil-uebergang", "offen", s, "teil", {"teil": t}))
    for t in (0.6, 0.7, 0.8):
        for s in range(101, 111):
            aus.append(("i-teil-ab-60", "auffallen", s, "teil", {"teil": t}))
    for s in (81, 82, 101, 102):
        for pflaster in ((30, 3), (60, 3)):
            aus.append(("5-pflaster", "still", s, "intakt", {"pflaster": pflaster}))
    for s in (101, 102):
        aus.append(("5-weiche-fenster", "still", s, "intakt", {"fensterfarbe_ki": 140}))
        aus.append(("5-weiche-fenster-pflaster", "still", s, "intakt",
                    {"fensterfarbe_ki": 140, "pflaster": (60, 1)}))
    return aus


def miss(fall: tuple) -> dict:
    """Ein Fall: Urteil der Deckung von heute und neues Urteil (mit Baukörpern)."""
    import gegenlese_erzeuger as gl
    from aiimaging import farbabgleich, formtreue, varianten
    gruppe, erwartung, startwert, zustand, regler = fall
    p = gl.paar(startwert, zustand, **regler)
    ka, kb = farbabgleich.kantenkarten(p["ki"], p["grund"], p["breite"], p["hoehe"])
    alt = varianten.deckung(True, farbabgleich.kanten_iou_aus_karten(ka, kb, bereich=p["maske"]))
    befund = formtreue.formtreue_aus_karten(ka, kb, p["maske"], p["breite"], p["hoehe"])
    neu = formtreue.deckung_mit_baukoerpern(alt, befund)
    return {"gruppe": gruppe, "erwartung": erwartung, "startwert": startwert,
            "zustand": zustand, "regler": regler, "alt": alt["urteil"], "neu": neu["urteil"],
            "kanten_iou_haus": alt["kanten_iou"], "anlage": befund["anlage"],
            "beanstandet": befund["aufgeloest"] + befund["verfleckt"],
            "hinweise": befund["hinweise"], "kantenquote": befund["kantenquote"],
            "baukoerper": [(k["nr"], k["urteil"], (k.get("innen") or {}).get("erhalten"),
                            (k.get("innen") or {}).get("anteil"),
                            (k.get("innen") or {}).get("versatz")) for k in befund["baukoerper"]
                           if k["n"] >= 300]}


def einordnen(e: dict) -> str:
    """``gut``, ``fehlalarm``, ``erkannt``, ``nicht_gemessen``, ``durchgelassen`` oder ``offen``."""
    from aiimaging import varianten
    ab, gleich = varianten.FORM_WEICHT_AB, varianten.DECKUNGSGLEICH
    if e["erwartung"] == "still":
        return "fehlalarm" if (e["alt"] == gleich and e["neu"] == ab) else "gut"
    if e["erwartung"] == "auffallen":
        if e["neu"] == ab:
            return "erkannt"
        from aiimaging import formtreue
        gesagt = any(h.startswith(formtreue.SATZ_NICHT_GEMESSEN) for h in e["hinweise"])
        return "nicht_gemessen" if gesagt else "durchgelassen"
    return "offen"


#: Die bekannten Grenzen am ganzen Satz (313 Paare, gemessen 10.11.2026): vier Fehlalarme, alle
#: mit Unschärfe auf sehr feinem Fensterraster bei erreichter Kantenquote, und ein
#: durchgelassener Fall (ein Nebenbau um seine halbe Breite verschoben: Sein Fensterraster
#: deckt sich nach vier Bildpunkten wieder mit sich selbst, die Suche nach dem Versatz folgt ihm).
BEKANNTE_FEHLALARME = (("a-farbe-blur", 2), ("a-farbe-weich", 2), ("a-farbe-kombi", 2),
                       ("a-lage-kombi+versatz2", 106))
BEKANNT_DURCHGELASSEN = (("f-nebenbau-verschoben", 43),)


def kernsatz() -> list[tuple]:
    """Jeder fünfte Fall des Satzes, dazu alle bekannten Grenzfälle: 67 Paare für die Proben."""
    alle = faelle()
    kern = [f for i, f in enumerate(alle) if i % 5 == 0]
    grenzen = set(BEKANNTE_FEHLALARME) | set(BEKANNT_DURCHGELASSEN)
    kern += [f for f in alle if (f[0], f[2]) in grenzen and f not in kern]
    return kern


if __name__ == "__main__":
    import sys
    from collections import Counter
    from multiprocessing import Pool
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
    with Pool() as becken:
        ergebnisse = becken.map(miss, faelle(), chunksize=4)
    print(len(ergebnisse), dict(Counter(einordnen(e) for e in ergebnisse)))
    for e in ergebnisse:
        if einordnen(e) in ("fehlalarm", "durchgelassen"):
            print(einordnen(e), e["gruppe"], e["startwert"])

