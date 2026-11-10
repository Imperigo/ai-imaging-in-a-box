"""Erzeuger und Messlauf für «Freie Sicht aufs Haus» (A0306). Keine Probe, ein Werkzeug.

**Der Satz.** 62 erfundene Szenen: ein Haus als Quader, dazu Nachbarbauten in wechselndem
Abstand, wechselnder Höhe und Drehung, Masten, Türme und Bauten, die nur eine Hausecke
verdecken; am Ende die fünf Fälle E01 bis E05 des Gegenlesens, Mass für Mass. Jede Szene
wird aus acht Richtungen betrachtet (E01 bis E05 aus der einen, für die sie gebaut sind).
Alles entsteht aus einer festen Zufallssaat in diesem Modul; es gibt keine Datei daneben
und kein echtes Projekt dahinter (Regel 3).

**Gemessen wird mit** ``tests/sichtmass.py``, und das benutzt nichts von der Lösung: eigene
dichte Punkte bis an die Kanten, eigener Schnitt, eigene Rahmungsrechnung, eigene Suche.
Dieses Modul hier ist der Erzeuger und die Buchhaltung: Es baut die Fälle, holt die heutige
Kamera (``kamerasatz`` ohne Sichtprüfung, das ist der Fall und nicht die Lösung) und zählt.

**Die Klassen eines Falls** (nach dem dichten Mass):

* ``frei``: Am gerechneten Standort ist höchstens 1 % der zugewandten Fläche verdeckt.
* ``loesbar``: mehr als 1 % verdeckt, und die eigene Suche findet auf dem Weg der Kamera
  einen Standpunkt mit höchstens 1 % und haltender Rahmung.
* ``unloesbar``: mehr als 1 % verdeckt, und die Suche findet nichts.

**Was als erreicht zählt** (Zielfunktion Runde 2): Die fertige Kamera ist nach dem dichten
Mass frei und regelgerecht gerahmt, ODER sie sagt ehrlich, dass sie es nicht ist
(``sicht.frei`` ist nicht wahr, und der Vermerk nennt «teilverdeckt, x %» oder «verdeckt»).
Der Verstoss, den es nie geben darf: eine Kamera, die «frei» sagt und nach dem dichten
Mass zu mehr als 1 % verdeckt ist.
"""
from __future__ import annotations

import math
import random

import sichtmass
from aiimaging import kameras, sichtstrahl

#: Die feste Saat. Wer sie ändert, ändert den Satz, und jede Zahl in der Meldung zu A0306.
SAAT = 20261110

#: Acht Richtungen: die vier Frontalen und je eine Über-Eck-Ansicht pro Seite.
RICHTUNGEN = ("n", "e", "s", "w", "nNE", "eES", "sSW", "wWN")

#: Wie viele Szenen je Art. Die Art lenkt nur das Würfeln; was ein Fall IST (frei, lösbar,
#: unlösbar), entscheidet allein das Prüfmass.
ARTEN = (("fern", 14), ("niedrig", 5), ("seitlich", 8), ("ecke", 8), ("mast", 6),
         ("turm", 4), ("nah", 5), ("ring", 3), ("abseits", 4))


# --------------------------------------------------------------------------------------
# Der Erzeuger
# --------------------------------------------------------------------------------------

def _haus(r: random.Random):
    breite, tiefe, hoehe = r.uniform(9, 24), r.uniform(8, 18), r.uniform(6, 18)
    x, y = r.uniform(-30, 30), r.uniform(-30, 30)
    fuss = r.choice((0.0, 0.0, 412.5))
    return [[x, y, fuss], [x + breite, y + tiefe, fuss + hoehe]]


def _nachbar(r: random.Random, haus, art: str, satz: dict, nr: int, winkel=None):
    """Ein Nachbarbau, der das Haus nicht berührt.

    Die meisten Arten stellen ihn **auf den Weg einer der acht Kameras**: ``anteil`` ist
    seine Lage zwischen Blickziel (0) und Kamera (1), ``quer`` der seitliche Versatz in
    Metern. So entstehen Verdeckungen mit Absicht und nicht nur, wenn der Zufall einen Bau
    gerade in eine Sichtlinie würfelt. ``ecke`` schiebt ihn so weit zur Seite, dass er nur
    einen Streifen an der Hauskante verdeckt; ``mast`` und ``turm`` sind schmal und hoch.
    """
    (x0, y0, fuss), (x1, y1, _oben) = haus
    mx, my = (x0 + x1) / 2.0, (y0 + y1) / 2.0
    weite = sum(k["abstand_m"] for k in satz["kameras"]) / len(satz["kameras"])
    for _ in range(400):
        breite, tiefe = r.uniform(5, 14), r.uniform(5, 14)
        hoehe = r.uniform(5, 20)
        drehung = r.choice((0.0, 0.0, 15.0, 30.0, 45.0, 70.0))
        if art in ("fern", "niedrig", "seitlich", "ecke", "mast", "turm"):
            kamera = r.choice(satz["kameras"])
            if art == "fern":
                anteil, quer = r.uniform(0.8, 1.02), r.uniform(-4.0, 4.0)
                breite, tiefe = r.uniform(4, 9), r.uniform(4, 9)
            elif art == "niedrig":
                anteil, quer = r.uniform(0.78, 1.0), r.uniform(-5.0, 5.0)
                hoehe = r.uniform(2.0, 4.0)
            elif art == "seitlich":
                anteil = r.uniform(0.55, 0.92)
                quer = r.choice((-1.0, 1.0)) * r.uniform(3.0, 12.0)
                breite, tiefe = r.uniform(3, 7), r.uniform(3, 7)
            elif art == "ecke":
                # Halb so weit wie die Kamera, seitlich knapp neben der halben Hausbreite:
                # Er verdeckt einen Streifen an der Kante oder gerade nichts mehr.
                anteil = r.uniform(0.3, 0.85)
                halbe = math.hypot(x1 - x0, y1 - y0) / 4.0
                quer = r.choice((-1.0, 1.0)) * (halbe * anteil + r.uniform(0.0, 3.5))
                breite, tiefe, hoehe = 3.0, 3.0, r.uniform(8, 16)
            elif art == "mast":
                anteil, quer = r.uniform(0.2, 0.9), r.uniform(-3.0, 3.0)
                breite = tiefe = r.choice((0.4, 0.6, 0.8))
                hoehe, drehung = r.uniform(15, 40), 0.0
            else:                                           # turm
                anteil, quer = r.uniform(0.5, 0.98), r.uniform(-2.5, 2.5)
                breite = tiefe = r.uniform(1.5, 3.0)
                hoehe = r.uniform(20, 45)
            ex, ey = kamera["auge"][0] - mx, kamera["auge"][1] - my
            laenge = math.hypot(ex, ey)
            cx = mx + ex * anteil + (ey / laenge) * quer
            cy = my + ey * anteil - (ex / laenge) * quer
        else:
            w = r.uniform(0.0, 360.0) if winkel is None else winkel + r.uniform(-12.0, 12.0)
            if art == "nah":
                abstand = (max(x1 - x0, y1 - y0) / 2.0 + r.uniform(1.0, 6.0)
                           + max(breite, tiefe) / 2.0)
                drehung = 0.0
            elif art == "ring":
                breite, tiefe = r.uniform(12, 20), r.uniform(12, 20)
                hoehe = r.uniform(12, 22)
                abstand = (max(x1 - x0, y1 - y0) / 2.0 + r.uniform(4.0, 9.0)
                           + max(breite, tiefe) / 2.0)
            else:                                           # abseits
                abstand = r.uniform(1.4, 2.2) * weite
            cx = mx + math.sin(math.radians(w)) * abstand
            cy = my + math.cos(math.radians(w)) * abstand
        radius = math.hypot(breite, tiefe) / 2.0
        # Abstand des Mittelpunkts vom Hausrechteck, grob und auf der sicheren Seite.
        dx = max(x0 - cx, 0.0, cx - x1)
        dy = max(y0 - cy, 0.0, cy - y1)
        if math.hypot(dx, dy) > radius + 0.5:
            return sichtstrahl.quader((cx, cy), breite, tiefe, hoehe, fuss_z=fuss,
                                      drehung_grad=drehung, name=f"nachbar-{nr}")
    raise RuntimeError("Kein Platz für den Nachbarbau gefunden; der Erzeuger ist verstellt.")


#: Das Haus der Fälle E01 bis E05 aus dem Gegenlesen (G-A0306), von Süden gesehen.
E_HAUS = [[0.0, 0.0, 0.0], [12.0, 10.0, 9.0]]


def gegenlese_szenen() -> list[dict]:
    """E01 bis E05, mit den Massen aus der Gegenlese-Meldung vom 10.11.2026.

    E01 und E02: ein Bau 3 x 3 x 14 m, der einen Streifen an der Hauskante verdeckt (9,8 %
    nach dem Mass des Gegenlesens). E03: derselbe Bau, näher an der Blickachse. E04 und
    E05: ein Mast 0,6 x 0,6 x 40 m neben der Achse. E01 und E02 mit den Koordinaten der
    Meldung; E03 bis E05 aus «Anteil der Achse, seitlich» gerechnet.
    """
    # Die heutige Kamera von Süden steht bei (4.8, -27.16, 1.7) und schaut auf (6, 5):
    # «Anteil 0.5 der Achse» ist der Punkt (5.4, -11.08), «seitlich» geht nach Westen.
    faelle = (
        ("E01", sichtstrahl.quader((0.9, -10.91), 3.0, 3.0, 14.0, name="eckbau")),
        ("E02", sichtstrahl.quader((1.9, -10.95), 3.0, 3.0, 14.0, name="eckbau")),
        ("E03", sichtstrahl.quader((2.9, -10.97), 3.0, 3.0, 14.0, name="eckbau")),
        ("E04", sichtstrahl.quader((4.8, -11.08), 0.6, 0.6, 40.0, name="mast")),
        ("E05", sichtstrahl.quader((4.44, -4.648), 0.6, 0.6, 40.0, name="mast")),
    )
    return [{"name": name, "art": "gegenlesen", "haus": E_HAUS, "nachbarn": [bau],
             "richtungen": ("s",)} for name, bau in faelle]


def szenen() -> list[dict]:
    """Die 62 Szenen, jedes Mal dieselben. Je Szene ``name``, ``art``, ``haus``, ``nachbarn``."""
    r = random.Random(SAAT)
    aus = []
    for art, anzahl in ARTEN:
        for i in range(anzahl):
            haus = _haus(r)
            satz = kameras.kamerasatz(haus, kuerzel=list(RICHTUNGEN))
            if art == "ring":
                # Rundum zugebaut: je ein hoher Bau in vier bis fünf Himmelsrichtungen.
                start = r.uniform(0.0, 90.0)
                n = r.choice((4, 5))
                nachbarn = [_nachbar(r, haus, art, satz, j, winkel=start + j * 360.0 / n)
                            for j in range(n)]
            elif art in ("ecke", "mast", "turm"):
                # Ein bis drei solche, dazu manchmal ein gewöhnlicher Nachbarbau.
                nachbarn = [_nachbar(r, haus, art, satz, j) for j in range(r.randint(1, 3))]
                if r.random() < 0.4:
                    nachbarn.append(_nachbar(r, haus, "fern", satz, len(nachbarn)))
            else:
                nachbarn = [_nachbar(r, haus, art, satz, j) for j in range(r.randint(1, 5))]
            aus.append({"name": f"{art}-{i + 1:02d}", "art": art, "haus": haus,
                        "nachbarn": nachbarn, "richtungen": RICHTUNGEN})
    return aus + gegenlese_szenen()


def faelle() -> list[dict]:
    """Jede Szene aus jeder ihrer Richtungen: ``{szene, kuerzel}``."""
    return [{"szene": s, "kuerzel": k} for s in szenen() for k in s["richtungen"]]


# --------------------------------------------------------------------------------------
# Der Messlauf: der Fall, das Urteil des Prüfmasses, die Zählung
# --------------------------------------------------------------------------------------

def heutige_kamera(fall: dict, vorgabe: dict | None = None) -> dict:
    """Die Kamera ohne Sichtprüfung: der Fall, wie er heute gerechnet wird."""
    return kameras.kamerasatz(fall["szene"]["haus"], kuerzel=[fall["kuerzel"]],
                              **(vorgabe or {}))["kameras"][0]


_KLASSEN: dict = {}


def _nur_stellung(kamera: dict) -> dict:
    """Was das Prüfmass von einer Kamera sehen darf: wo sie steht und wie sie schaut.
    Nichts, was die Lösung über sich selbst urteilt."""
    return {schluessel: kamera[schluessel] for schluessel in
            ("auge", "blick_auf", "brennweite_mm", "shift_mm", "seitenverhaeltnis")}


def beurteile(fall: dict, kamera: dict | None = None, *, vorgabe: dict | None = None) -> dict:
    """Ein Fall, beurteilt mit dem dichten Mass.

    ``kamera`` ist die fertige Kamera der Lösung; ohne sie wird die heutige beurteilt.
    ``vorgabe`` sind weitere Angaben für den Kamerasatz (Brennweite, Modus, Format); sie
    müssen dieselben sein, mit denen ``kamera`` gerechnet wurde.

    Returns:
        ``{klasse, basis, kamera, anteil_basis, anteil, frei, gerahmt, sagt_frei,
        ehrlich, erreicht, verstoss, fund}``.

        * ``anteil``: verdeckter Anteil an der fertigen Kamera nach dem dichten Mass.
        * ``sagt_frei``: was die Lösung über sich sagt (``sicht.frei`` ist wahr). Ohne
          Sichtprüfung sagt eine Kamera nichts und gilt als «sagt frei»: Sie wird ohne
          Vermerk geliefert.
        * ``erreicht``: frei und gerahmt nach dem dichten Mass, ODER ehrlich gemeldet.
        * ``verstoss``: sagt frei und ist zu mehr als 1 % verdeckt.
        * ``fund``: der Standpunkt, den die eigene Suche gefunden hat (oder ``None``).
    """
    haus, nachbarn = fall["szene"]["haus"], fall["szene"]["nachbarn"]
    # Die Klasse eines Falls hängt nicht von der Lösung ab. Sie wird einmal gerechnet und
    # gemerkt, damit «heute» und «neu» denselben Fall nicht zweimal durchsuchen.
    marke = (repr(haus), repr(nachbarn), fall["kuerzel"], repr(sorted((vorgabe or {}).items())))
    if marke not in _KLASSEN:
        basis = heutige_kamera(fall, vorgabe)
        anteil_basis = sichtmass.verdeckter_anteil(basis["auge"], haus, nachbarn)
        fund = None
        if anteil_basis is not None and anteil_basis <= sichtmass.FREI_HOECHSTENS:
            klasse = "frei"
        else:
            fund = sichtmass.suche_standpunkt(haus, nachbarn, basis)
            klasse = "loesbar" if fund else "unloesbar"
        _KLASSEN[marke] = (basis, anteil_basis, fund, klasse)
    basis, anteil_basis, fund, klasse = _KLASSEN[marke]
    basis = dict(basis)
    zielhoehe = sichtmass.angehobenes_ziel(basis)[2] - min(haus[0][2], haus[1][2])
    fertig = basis if kamera is None else kamera
    anteil = sichtmass.verdeckter_anteil(fertig["auge"], haus, nachbarn)
    frei = anteil is not None and anteil <= sichtmass.FREI_HOECHSTENS
    gerahmt = sichtmass.rahmung_haelt(_nur_stellung(fertig), haus,
                                      azimut_grad=basis["azimut_grad"],
                                      zielhoehe_ueber_fuss=zielhoehe)
    sicht = fertig.get("sicht")
    sagt_frei = True if sicht is None else sicht["frei"] is True
    ehrlich = (sicht is not None and sicht["frei"] is False
               and ("teilverdeckt, " in sicht["vermerk"] or "verdeckt, " in sicht["vermerk"])
               and "%" in sicht["vermerk"])
    return {"klasse": klasse, "basis": basis, "kamera": fertig, "anteil_basis": anteil_basis,
            "anteil": anteil, "frei": frei, "gerahmt": gerahmt, "sagt_frei": sagt_frei,
            "ehrlich": ehrlich, "erreicht": (frei and gerahmt and sagt_frei) or ehrlich,
            "verstoss": sagt_frei and not frei, "fund": fund}


def nacheinander(fall: dict) -> dict:
    """Die zwei alten Regeln hintereinander: erst heranziehen, dann zurückschieben.

    Das ist die Schaltung, vor der der Kommentar an ``ziehe_bis_frei`` warnt, mit fester
    Brennweite. Sie ist hier nachgebaut, um das Gegeneinander zu MESSEN statt zu behaupten.
    Die Sichtprüfung dabei ist die des dichten Masses.
    """
    haus, nachbarn = fall["szene"]["haus"], fall["szene"]["nachbarn"]
    basis = heutige_kamera(fall)
    gezogen = kameras.ziehe_bis_frei(
        basis["auge"], basis["blick_auf"], haus,
        lambda auge, _ziel: sichtmass.ist_frei(auge, haus, nachbarn))
    geschoben = kameras.schiebe_bis_im_bild(
        gezogen["auge"], basis["blick_auf"], haus, shift_mm=basis["shift_mm"],
        brennweite_mm=basis["brennweite_mm"], seitenverhaeltnis=basis["seitenverhaeltnis"])
    return {"kamera": dict(_nur_stellung(basis), auge=geschoben["auge"]),
            "gezogen_frei": gezogen["frei"],
            "zurueckgeschoben": geschoben["durchlaeufe"] > 0}


def mit_sichtpruefung(fall: dict, vorgabe: dict | None = None) -> dict:
    """Die Lösung: ``kamerasatz`` mit dem reinen Strahlentest als Sichtprüfung."""
    szene = fall["szene"]
    return kameras.kamerasatz(szene["haus"], kuerzel=[fall["kuerzel"]],
                              sicht_frei=sichtstrahl.pruefer(szene["nachbarn"]),
                              **(vorgabe or {}))["kameras"][0]


def messe(loesung=None) -> dict:
    """Die Zielfunktion über den ganzen Satz.

    ``loesung`` ist ``(fall) → fertige Kamera`` oder ``None`` für den heutigen Stand.

    Returns:
        ``zahl`` je Klasse; ``frei_gestellt`` (lösbare Fälle, deren fertige Kamera nach dem
        dichten Mass frei und gerahmt ist und das auch sagt); ``ehrlich_gemeldet``
        (lösbare Fälle, die nicht frei gestellt, aber mit Zahl gemeldet sind);
        ``erreicht`` je Klasse; ``verstoesse`` (sagt frei, ist es nicht) über ALLE Fälle;
        ``anteil_loesbar`` = erreicht / lösbar.
    """
    zahl = {"frei": 0, "loesbar": 0, "unloesbar": 0}
    erreicht = dict(zahl)
    frei_gestellt = ehrlich_gemeldet = 0
    verstoesse, einzeln = [], []
    for fall in faelle():
        urteil = beurteile(fall, None if loesung is None else loesung(fall))
        zahl[urteil["klasse"]] += 1
        erreicht[urteil["klasse"]] += urteil["erreicht"]
        if urteil["klasse"] == "loesbar":
            gestellt = urteil["frei"] and urteil["gerahmt"] and urteil["sagt_frei"]
            frei_gestellt += gestellt
            ehrlich_gemeldet += (not gestellt) and urteil["ehrlich"]
        if urteil["verstoss"]:
            verstoesse.append((fall["szene"]["name"], fall["kuerzel"], urteil["anteil"]))
        einzeln.append((fall, urteil))
    return {"faelle": len(einzeln), "szenen": len(szenen()), "zahl": zahl,
            "erreicht": erreicht, "frei_gestellt": frei_gestellt,
            "ehrlich_gemeldet": ehrlich_gemeldet, "verstoesse": verstoesse,
            "anteil_loesbar": (erreicht["loesbar"] / zahl["loesbar"]) if zahl["loesbar"] else None,
            "einzeln": einzeln}


if __name__ == "__main__":                                  # pragma: no cover
    # `python tests/sichtszenen.py` druckt die Messung, wie sie in der Meldung steht.
    for titel, weg in (("heute (ohne Sichtprüfung)", None),
                       ("nacheinander (alt, feste Brennweite)",
                        lambda fall: nacheinander(fall)["kamera"]),
                       ("ein Ablauf (A0306)", mit_sichtpruefung)):
        m = messe(weg)
        print(f"{titel}: {m['szenen']} Szenen, {m['faelle']} Fälle, Klassen {m['zahl']}; "
              f"lösbare: frei gestellt {m['frei_gestellt']}, ehrlich gemeldet "
              f"{m['ehrlich_gemeldet']}, erreicht {m['erreicht']['loesbar']} von "
              f"{m['zahl']['loesbar']} ({m['anteil_loesbar']:.1%}); "
              f"Verstösse (sagt frei, ist über 1 % verdeckt): {len(m['verstoesse'])}")
