"""Der synthetische Satz «Flügel bleiben ein Haus» (A0301) und sein Erzeuger.

**Wozu:** ``umfeld.grundriss_cluster`` fasst Bauteile zu Bauten zusammen. Steht eine Anlage auf einer
grossen Geländeplatte, hing bis zu diesem Auftrag alles über diese Platte zusammen, der Haufen wuchs
über die Flächengrenze und wurde nach *gleichem Grundriss* zerlegt: ein Haus aus Flügeln (verschiedene
Grundrisse) zerfiel in seine Flügel. Dieser Satz misst das, und er misst die Gegenrichtung: zwei
getrennte Häuser dürfen nicht verschmelzen.

**Regel 3:** frei erfunden, keine Projektdaten. Alles entsteht aus den Zahlen in dieser Datei
(:func:`faelle`), ohne Zufall, ohne Datei, ohne Netz.

**Was ein Fall ist:** eine Liste Boxen ``((x0, y0, z0), (x1, y1, z1))`` (Welt, Z oben, Meter) und je
Box, zu welchem Haus sie gehört (``haus``: 0, 1, … oder ``None`` für Gelände, Hof und Belag, die zu
keinem Haus gehören). **Richtig gruppiert** heisst: Die Gruppen, die Hausteile enthalten, sind genau
die Häuser; kein Geländeteil steckt in einer Hausgruppe; jede Hausgruppe gilt als Bau.
**Falsche Verschmelzung** heisst: Eine Gruppe enthält Teile von zwei Häusern.

Die Messung selbst steht in :func:`miss`; die Probe dazu in ``tests/test_fluegel_gruppierung.py``.
"""
from __future__ import annotations

#: Die Bauweisen eines Flügels: ein Körper, eine 2-m-Grundrissplatte (wie in einem Situationsmodell aus
#: Platten) oder Geschossdecken übereinander (gleicher Grundriss, 3,5 m Abstand).
BAUWEISEN = ("koerper", "platten", "decken")

#: Rechtecke ``(x0, y0, x1, y1)`` der Flügel je Form. Die Flügel überlappen sich an den Gelenken um die
#: volle Flügeltiefe (so entstehen sie, wenn man Baukörper ineinander schiebt).
FORMEN = {
    "L": ((0, 0, 32, 12), (0, 0, 12, 28)),
    "U": ((0, 0, 44, 12), (0, 0, 12, 30), (32, 0, 44, 30)),
    "H": ((0, 0, 12, 40), (32, 0, 44, 40), (6, 14, 38, 26)),
    "Kamm": ((0, 0, 62, 12), (0, 4, 10, 34), (17, 4, 27, 34), (35, 4, 45, 34), (52, 4, 62, 34)),
}

#: Zweite Massreihe (kurze Schenkel, die zu mehr als der Hälfte im Nachbarflügel stecken; schmale Flügel).
FORMEN_KURZ = {
    "L": ((0, 0, 40, 14), (0, 0, 14, 22)),
    "U": ((0, 0, 60, 12), (0, 0, 12, 20), (48, 0, 60, 20)),
    "H": ((0, 0, 10, 30), (24, 0, 34, 30), (8, 11, 26, 19)),
    "Kamm": ((0, 0, 50, 10), (2, 0, 12, 18), (38, 0, 48, 18)),
}


def _fluegel(rechteck, bauweise: str, versatz=(0.0, 0.0)) -> list:
    """Die Boxen eines Flügels in der Bauweise."""
    x0, y0, x1, y1 = (float(v) for v in rechteck)
    x0, x1 = x0 + versatz[0], x1 + versatz[0]
    y0, y1 = y0 + versatz[1], y1 + versatz[1]
    if bauweise == "koerper":
        return [((x0, y0, 0.0), (x1, y1, 10.5))]
    if bauweise == "platten":
        return [((x0, y0, 0.0), (x1, y1, 2.0))]
    if bauweise == "decken":
        return [((x0, y0, 3.5 * g), (x1, y1, 3.5 * g + 0.3)) for g in range(4)]
    raise ValueError(bauweise)


def _haus(rechtecke, bauweise, versatz=(0.0, 0.0)) -> list:
    return [b for r in rechtecke for b in _fluegel(r, bauweise, versatz)]


def _gelaendeplatte(dick=2.0) -> list:
    """Eine Platte, auf der die Anlage steht: 400 × 400 m, also weit über der Flächengrenze für einen Bau."""
    return [((-150.0, -150.0, 0.0), (250.0, 250.0, dick))]


def _fall(name, gruppe, teile, gegenfall=False) -> dict:
    """``teile``: Liste ``(haus, [boxen])``. Flacht sie zu ``boxen`` und ``haus`` (je Box) ab."""
    boxen, haus = [], []
    for nummer, liste in teile:
        for b in liste:
            boxen.append(b)
            haus.append(nummer)
    return {"name": name, "gruppe": gruppe, "boxen": boxen, "haus": haus, "gegenfall": gegenfall}


def faelle() -> list[dict]:
    """Alle Fälle des Satzes, in fester Reihenfolge.

    Returns:
        ``[{name, gruppe, boxen, haus, gegenfall}, …]``. ``gruppe`` ist ``"fluegel"``, ``"bodenplatte"``,
        ``"gang"``, ``"gemischt"`` oder ``"gegenfall"``; ``gegenfall`` ist wahr, wenn der Fall mindestens
        zwei Häuser enthält, die getrennt bleiben müssen.
    """
    aus = []
    # ---- 1. Flügelbauten: vier Formen, drei Bauweisen, frei und auf der Geländeplatte.
    for form, rechtecke in FORMEN.items():
        for bauweise in BAUWEISEN:
            aus.append(_fall(f"{form}-{bauweise}-frei", "fluegel", [(0, _haus(rechtecke, bauweise))]))
            aus.append(_fall(f"{form}-{bauweise}-gelaende", "fluegel",
                             [(None, _gelaendeplatte()), (0, _haus(rechtecke, bauweise))]))
    for form, rechtecke in FORMEN_KURZ.items():
        aus.append(_fall(f"{form}-kurz-platten-gelaende", "fluegel",
                         [(None, _gelaendeplatte()), (0, _haus(rechtecke, "platten", (20.0, -30.0)))]))
    # Der Bau liegt über der Naht zweier Geländeplatten (sie berühren sich, oder sie überlappen knapp).
    for naht, ueber in (("beruehrt", 0.0), ("ueberlappt", 0.5)):
        platten = [((-300.0, -200.0, 0.0), (20.0 + ueber, 200.0, 2.0)), ((20.0, -200.0, 0.0), (300.0, 200.0, 2.0))]
        aus.append(_fall(f"L-platten-naht-{naht}", "fluegel",
                         [(None, platten), (0, _haus(FORMEN["L"], "platten"))]))
    # ---- 2. Teile, die nur über eine Bodenplatte zusammenhängen (die Platte gehört zum Haus).
    sockel2 = [((0.0, 0.0, 0.0), (34.0, 14.0, 0.4))]
    zwei = [((1.0, 1.0, 0.4), (15.0, 13.0, 9.0)), ((19.0, 1.0, 0.4), (33.0, 13.0, 12.0))]
    sockel3 = [((0.0, 0.0, 0.0), (50.0, 16.0, 0.3))]
    drei = [((1.0, 1.0, 0.3), (15.0, 15.0, 7.0)), ((18.0, 2.0, 0.3), (32.0, 14.0, 10.0)),
            ((35.0, 1.0, 0.3), (49.0, 15.0, 7.0))]
    sockel_p = [((0.0, 0.0, 0.0), (30.0, 12.0, 0.3))]
    zwei_p = [((0.5, 0.5, 0.0), (13.0, 11.5, 2.0)), ((17.0, 0.5, 0.0), (29.5, 11.5, 2.0))]
    for name, sockel, teile in (("zwei-koerper", sockel2, zwei), ("drei-koerper", sockel3, drei),
                                ("zwei-platten", sockel_p, zwei_p)):
        aus.append(_fall(f"bodenplatte-{name}-frei", "bodenplatte", [(0, sockel + teile)]))
        aus.append(_fall(f"bodenplatte-{name}-gelaende", "bodenplatte",
                         [(None, _gelaendeplatte()), (0, sockel + teile)]))
    # ---- 3. Teile, die nur über einen Verbindungsgang zusammenhängen (er steckt je 1 m in beiden).
    for bauweise in ("koerper", "platten"):
        a = _fluegel((0, 0, 14, 12), bauweise)
        b = _fluegel((22, 0, 36, 12), bauweise)
        gang = [((13.0, 4.5, 0.0), (23.0, 7.5, 3.0 if bauweise == "koerper" else 2.0))]
        aus.append(_fall(f"gang-{bauweise}-frei", "gang", [(0, a + gang + b)]))
        aus.append(_fall(f"gang-{bauweise}-gelaende", "gang", [(None, _gelaendeplatte()), (0, a + gang + b)]))
    # ---- 4. Gemischt: ein Flügelbau und ein getrenntes Haus daneben. Beides muss stimmen.
    for bauweise in BAUWEISEN:
        aus.append(_fall(f"L-und-nachbar-{bauweise}-gelaende", "gemischt",
                         [(None, _gelaendeplatte()), (0, _haus(FORMEN["L"], bauweise)),
                          (1, _fluegel((35, 0, 47, 10), bauweise))], gegenfall=True))
    # Ein Haus steht im Winkel des L, 3 m von beiden Schenkeln: die Hüllen überlappen, die Grundrisse nicht.
    for lage in ("frei", "gelaende"):
        teile = [(0, _haus(FORMEN["L"], "koerper")), (1, _fluegel((15, 15, 27, 27), "koerper"))]
        aus.append(_fall(f"L-und-haus-im-winkel-{lage}", "gemischt",
                         ([(None, _gelaendeplatte())] if lage == "gelaende" else []) + teile, gegenfall=True))
    # Zwei Geländeplatten unter der Flächengrenze, die knapp überlappen (eine Kette): je ein Bau darauf.
    kette = [((-100.0, -60.0, 0.0), (20.0, 60.0, 2.0)), ((19.5, -60.0, 0.0), (139.5, 60.0, 2.0))]
    aus.append(_fall("L-und-nachbar-plattenkette", "gemischt",
                     [(None, kette), (0, _haus(FORMEN["L"], "platten", (-60.0, -20.0))),
                      (1, _fluegel((60, 0, 80, 12), "platten"))], gegenfall=True))
    # ---- 5. Gegenfälle: zwei getrennte Häuser mit kleinem Abstand; Haus neben Nebenbau.
    for bauweise in BAUWEISEN:
        for abstand in (0.0, 0.5, 2.0):            # 0: sie berühren sich nur (Ergebnis 359: zwei Bauten)
            h0 = _fluegel((0, 0, 12, 10), bauweise)
            h1 = _fluegel((12 + abstand, 0, 24 + abstand, 10), bauweise)
            if bauweise == "koerper":
                aus.append(_fall(f"zwei-haeuser-{abstand:g}m-koerper-frei", "gegenfall", [(0, h0), (1, h1)], True))
            aus.append(_fall(f"zwei-haeuser-{abstand:g}m-{bauweise}-gelaende", "gegenfall",
                             [(None, _gelaendeplatte()), (0, h0), (1, h1)], True))
    for abstand in (0.0, 1.0):
        haus = _fluegel((0, 0, 12, 9), "koerper")
        nebenbau = [((12.0 + abstand, 2.0, 0.0), (15.5 + abstand, 7.0, 2.8))]
        aus.append(_fall(f"haus-nebenbau-{abstand:g}m-frei", "gegenfall", [(0, haus), (1, nebenbau)], True))
        aus.append(_fall(f"haus-nebenbau-{abstand:g}m-gelaende", "gegenfall",
                         [(None, _gelaendeplatte()), (0, haus), (1, nebenbau)], True))
    # Zwei Häuser (und Haus mit Nebenbau) auf einem gemeinsamen Hofbelag, der viel grösser ist als sie:
    # der Belag ist kein Sockel, die Häuser bleiben zwei.
    hof = [((-8.0, -8.0, 0.0), (36.0, 22.0, 0.1))]
    paar = [(0, _fluegel((0, 0, 12, 10), "koerper")), (1, _fluegel((15, 0, 27, 10), "koerper"))]
    mit_nebenbau = [(0, _fluegel((0, 0, 12, 9), "koerper")), (1, [((14.0, 2.0, 0.0), (17.5, 7.0, 2.8))])]
    for name, teile in (("zwei-haeuser", paar), ("haus-nebenbau", mit_nebenbau)):
        aus.append(_fall(f"{name}-hofbelag-frei", "gegenfall", [(None, hof)] + teile, True))
        aus.append(_fall(f"{name}-hofbelag-gelaende", "gegenfall",
                         [(None, _gelaendeplatte(0.05)), (None, hof)] + teile, True))
    namen = [f["name"] for f in aus]
    assert len(set(namen)) == len(namen), "doppelte Fallnamen"
    return aus


def beurteile(fall: dict, cluster: list[dict]) -> dict:
    """Ein Fall gegen das Ergebnis von ``grundriss_cluster``.

    Returns:
        ``{richtig, verschmelzungen, zerlegt, grund}``. ``verschmelzungen`` zählt die Gruppen mit
        Teilen aus zwei Häusern, ``zerlegt`` die Häuser, deren Teile in mehr als einer Gruppe liegen.
    """
    haus = fall["haus"]
    soll = {}
    for i, h in enumerate(haus):
        if h is not None:
            soll.setdefault(h, set()).add(i)
    verschmelzungen, gruende = 0, []
    gruppen_je_haus: dict = {h: 0 for h in soll}
    alle = sorted(i for c in cluster for i in c["teile"])
    if alle != list(range(len(haus))):
        gruende.append("nicht jedes Teil liegt in genau einer Gruppe")
    for c in cluster:
        haeuser = {haus[i] for i in c["teile"]} - {None}
        if not haeuser:
            continue
        if len(haeuser) > 1:
            verschmelzungen += 1
            gruende.append(f"Gruppe {c['teile']} enthält die Häuser {sorted(haeuser)}")
        for h in haeuser:
            gruppen_je_haus[h] += 1
        if any(haus[i] is None for i in c["teile"]):
            gruende.append(f"Gruppe {c['teile']} enthält Gelände oder Belag")
        if not c["bau"]:
            gruende.append(f"Gruppe {c['teile']} gilt nicht als Bau ({c['art']})")
    zerlegt = sum(1 for n in gruppen_je_haus.values() if n > 1)
    if zerlegt:
        gruende.append(f"{zerlegt} Haus/Häuser in mehrere Gruppen zerlegt: {gruppen_je_haus}")
    return {"richtig": not gruende, "verschmelzungen": verschmelzungen, "zerlegt": zerlegt,
            "grund": "; ".join(gruende)}


def miss(gruppierung) -> dict:
    """Die Zielfunktion von A0301: der Anteil richtig gruppierter Fälle und die falschen Verschmelzungen.

    Args:
        gruppierung: die Funktion, die gemessen wird (``umfeld.grundriss_cluster``).

    Returns:
        ``{faelle, richtig, anteil, gegenfaelle, verschmelzungen_gegenfaelle, verschmelzungen, falsch}``;
        ``falsch`` ist ``[(name, grund), …]``.
    """
    alle = faelle()
    richtig, falsch, v_gegen, v_alle = 0, [], 0, 0
    for fall in alle:
        urteil = beurteile(fall, gruppierung(fall["boxen"]))
        v_alle += urteil["verschmelzungen"]
        if fall["gegenfall"]:
            v_gegen += urteil["verschmelzungen"]
        if urteil["richtig"]:
            richtig += 1
        else:
            falsch.append((fall["name"], urteil["grund"]))
    return {"faelle": len(alle), "richtig": richtig, "anteil": richtig / len(alle),
            "gegenfaelle": sum(1 for f in alle if f["gegenfall"]),
            "verschmelzungen_gegenfaelle": v_gegen, "verschmelzungen": v_alle, "falsch": falsch}


if __name__ == "__main__":                                    # pragma: no cover — Messung von Hand
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
    from aiimaging import umfeld
    m = miss(umfeld.grundriss_cluster)
    print(f"{m['richtig']} von {m['faelle']} richtig ({100 * m['anteil']:.1f} %), "
          f"{m['verschmelzungen_gegenfaelle']} falsche Verschmelzungen in {m['gegenfaelle']} Gegenfällen")
    for name, grund in m["falsch"]:
        print(f"  FALSCH {name}: {grund}")
