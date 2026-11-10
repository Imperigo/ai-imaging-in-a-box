"""«Freie Sicht aufs Haus» (A0306): die Schwellen der Lösung, von beiden Seiten besetzt.

**Warum es diese Datei gibt.** Ein Satz, an dem die Lösung 100 % erreicht, belegt wenig,
wenn ihre Schwellen in einer leeren Lücke des Satzes liegen (Lehre aus dem ersten
Gegenlesen im Spezialauftrag, 10.11.2026). ``tests/test_freie_sicht.py`` misst die
Zielfunktion; hier steht, was daneben gehört:

* **Reihen in kleinen Schritten quer über jede Schwelle** der Lösung: ab wann ein Streifen
  an der Hauskante zählt (0 %, 1 %), wie schmal ein Mast sein darf, der Spielraum des
  Standpunkts (5 und 10 cm), die kürzeste Brennweite (24 mm), die Höhe, ab der ein Bau
  den Fuss verdeckt, die Grenzen des Heranziehens bei kleinen Bauten.
* **Mehrere tausend Zufallsfälle gegen die Basis:** Jede Abweichung von der heutigen Kamera
  ist eine belegte Verbesserung (vorher verdeckt, nachher frei und gerahmt). Kein Fall
  wird schlechter, und keine Kamera sagt «frei», die es nach dem dichten Mass nicht ist.
* **Nicht entscheidbar** bleibt nicht entscheidbar: Wo die Sichtprüfung nicht jeden Punkt
  messen kann, wird weder «frei» noch «verdeckt» geraten und die Kamera nicht bewegt.
* **Gemeine Fälle**, gebaut, bevor es das Gegenlesen tut.

Geurteilt wird überall mit dem Prüfmass aus ``tests/sichtmass.py``, das nichts von der
Lösung benutzt.
"""
from __future__ import annotations

import math
import re

import pytest

import sichtmass
import sichtszenen as sz
from aiimaging import kameras, sichtstrahl

HAUS = [[0.0, 0.0, 0.0], [14.0, 10.0, 9.0]]


def _pruefe(haus, nachbarn, kuerzel="s", **vorgabe) -> dict:
    """Ein Fall durch Lösung und Prüfmass, mit allen Zusagen. Gibt das Urteil zurück."""
    fall = {"szene": {"name": "reihe", "haus": haus, "nachbarn": nachbarn}, "kuerzel": kuerzel}
    satz = kameras.kamerasatz(haus, kuerzel=[kuerzel],
                              sicht_frei=sichtstrahl.pruefer(nachbarn), **vorgabe)
    kamera = satz["kameras"][0]
    urteil = sz.beurteile(fall, kamera, vorgabe=vorgabe)
    basis, sicht = urteil["basis"], kamera["sicht"]
    ohne_sicht = {k: v for k, v in kamera.items() if k != "sicht"}
    # 1. Nie «frei» sagen und es nicht sein.
    assert not urteil["verstoss"], (urteil["anteil"], sicht)
    # 2. Eine bewegte Kamera ist frei und gerahmt (dichtes Mass), in den Grenzen des Wegs.
    if sicht["bewegt"]:
        assert sicht["frei"] is True and urteil["frei"] and urteil["gerahmt"], sicht
        assert urteil["anteil_basis"] > 0.0
        assert kamera["brennweite_mm"] >= min(kameras.ZIEH_BRENNWEITE_MIN_MM,
                                              basis["brennweite_mm"]) - 1e-9
        assert kamera["brennweite_mm"] <= basis["brennweite_mm"] + 1e-9
        assert kamera["abstand_m"] >= kameras.MIN_ZIEH_ABSTAND_M
    else:
        # 3. Eine unbewegte Kamera ist die der Basis. Nie halb herangezogen.
        assert ohne_sicht["auge"] == basis["auge"]
        assert ohne_sicht["brennweite_mm"] == basis["brennweite_mm"]
    # 4. Ohne jede Verdeckung: Zahl für Zahl dieselbe Kamera, und sie heisst frei.
    if urteil["anteil_basis"] == 0.0:
        assert ohne_sicht == basis and sicht["frei"] is True and sicht["urteil"] == "frei"
    # 5. Was nicht frei ist, sagt es mit Zahl und steht im Satz unter `verdeckt`.
    if sicht["frei"] is False:
        assert re.match(r"(teil)?verdeckt, \d+,\d %", sicht["vermerk"]), sicht["vermerk"][:50]
        assert satz["verdeckt"] == [kuerzel] and sicht["vermerk"] in kamera["warnungen"]
    # 6. Lösbar nach dem dichten Mass heisst: frei gestellt oder ehrlich gemeldet.
    if urteil["klasse"] == "loesbar":
        assert urteil["erreicht"]
    return urteil


# --------------------------------------------------------------------------------------
# Schwelle 1: der Streifen an der Hauskante (0 % und 1 %)
# --------------------------------------------------------------------------------------

def test_reihe_ueber_den_streifen_an_der_hauskante():
    """Ein niedriger Bau (3 m) vor der Kamera wandert von der Seite ins Blickfeld, 2 cm je
    Schritt. Erst verdeckt er nichts, dann das untere Stück eines Streifens an der Kante,
    der mit jedem Schritt breiter wird. Drei Bereiche, alle besetzt:

    * nichts verdeckt: dieselbe Kamera, «frei»;
    * bis 1 % (geringfügig): Die Kamera bleibt stehen, heisst aber nicht «frei», sondern
      «teilverdeckt, 0,x %»;
    * darüber: herangezogen oder ehrlich gemeldet.

    Das ist der Fall E01 des Gegenlesens, in kleinen Schritten. (Ein Bau über die ganze
    Höhe springt beim ersten Rasterpunkt gleich über 1 %: Die äusserste Spalte wiegt in
    beiden Rastern rund 1,7 % der Fassade. Darum hier ein niedriger.)"""
    basis = kameras.kamerasatz(HAUS, kuerzel=["s"])["kameras"][0]
    y = basis["auge"][1] + 16.0
    kante = next(x / 100.0 for x in range(-600, 700)
                 if sichtmass.verdeckter_anteil(
                     basis["auge"], HAUS, [sichtstrahl.quader((x / 100.0, y), 3.0, 3.0, 3.0)]) > 0.0)
    bereich = {"nichts": 0, "geringfuegig": 0, "mehr": 0}
    for schritt in range(-8, 40):
        turm = sichtstrahl.quader((kante + schritt * 0.02, y), 3.0, 3.0, 3.0, name="turm")
        urteil = _pruefe(HAUS, [turm])
        sicht = urteil["kamera"]["sicht"]
        eigen = sicht["vorher"]["verdeckt_anteil"]          # was die Lösung am Standort mass
        if eigen == 0.0:
            bereich["nichts"] += 1
            assert sicht["abbruch"] == "sicht_frei"
        elif eigen <= kameras.SICHT_GERINGFUEGIG:
            bereich["geringfuegig"] += 1
            assert sicht["abbruch"] == "geringfuegig" and not sicht["bewegt"]
            assert sicht["frei"] is False and sicht["urteil"] == "teilverdeckt"
            assert sicht["vermerk"].startswith("teilverdeckt, 0,") or \
                sicht["vermerk"].startswith("teilverdeckt, 1,0 %")
        else:
            bereich["mehr"] += 1
            assert sicht["abbruch"] in ("herangezogen", "kein_freier_standpunkt")
        # Lösung und dichtes Mass sehen dieselbe Kante: nie «nichts» bei über 1 %.
        assert abs(eigen - urteil["anteil_basis"]) < 0.02
    assert bereich["nichts"] >= 5 and bereich["geringfuegig"] >= 3 and bereich["mehr"] >= 15, bereich


# --------------------------------------------------------------------------------------
# Schwelle 2: wie schmal ein Mast sein darf
# --------------------------------------------------------------------------------------

@pytest.mark.parametrize("breite", [0.06, 0.08, 0.10, 0.15, 0.20, 0.24, 0.26, 0.30, 0.40, 0.60, 1.0])
@pytest.mark.parametrize("vor_der_fassade", [0.5, 5.0, 12.0, 22.0])
def test_reihe_ueber_die_mastbreite(breite, vor_der_fassade):
    """Ein Mast von 40 m Höhe, 6 cm bis 1 m breit, einen halben Meter vor der Fassade bis
    dicht vor der Kamera, vor fünf Stellen der Fassade (auch zwischen zwei Rasterspalten).
    Das Raster der Lösung hat 25 cm Spaltenabstand; ohne die Mastzeilen (5 cm) fiele alles
    unter 25 cm durch. Zugesagt ab 6 cm: Der Mast wird bemerkt, und die Kamera sagt nie
    «frei», wenn er nach dem dichten Mass mehr als 1 % verdeckt. Das sind die Fälle E04
    und E05 des Gegenlesens, als Reihe."""
    basis = kameras.kamerasatz(HAUS, kuerzel=["s"])["kameras"][0]
    auge = basis["auge"]
    for vor_x in (1.37, 5.02, 7.11, 9.93, 12.61):
        # Auf der Sichtlinie vom Auge zum Fassadenpunkt (vor_x, 0), `vor_der_fassade` davor.
        anteil = vor_der_fassade / -auge[1]
        ort = (vor_x + (auge[0] - vor_x) * anteil, -vor_der_fassade)
        mast = sichtstrahl.quader(ort, breite, breite, 40.0, name="mast")
        urteil = _pruefe(HAUS, [mast])
        sicht = urteil["kamera"]["sicht"]
        assert sicht["vorher"]["verdeckte_punkte"] >= 1, ("Der Mast blieb unbemerkt.", vor_x)
        assert sicht["frei"] is not True or urteil["anteil"] == 0.0


def test_die_mastzeilen_tragen_das_ergebnis_wirklich(monkeypatch):
    """Gegenprobe: Ohne die Mastzeilen übersieht das Raster einen 10 cm breiten Mast
    zwischen zwei Spalten, und die Kamera hiesse «frei». Die Reihe oben ist also nicht aus
    Versehen grün."""
    basis = kameras.kamerasatz(HAUS, kuerzel=["s"])["kameras"][0]
    mast = sichtstrahl.quader((7.12, -0.5), 0.10, 0.10, 40.0)
    mit = kameras.sichtbefund(basis["auge"], HAUS, sichtstrahl.pruefer([mast]))
    assert mit["frei"] is False and 0.0 < mit["anteil"] < 0.02
    monkeypatch.setattr(kameras, "SICHTRASTER_MASTZEILEN", ())
    kameras._sichtpunkte_der_flaechen.cache_clear()
    try:
        ohne = kameras.sichtbefund(basis["auge"], HAUS, sichtstrahl.pruefer([mast]))
        assert ohne["frei"] is True
    finally:
        monkeypatch.undo()
        kameras._sichtpunkte_der_flaechen.cache_clear()


# --------------------------------------------------------------------------------------
# Schwelle 3: der Spielraum des Standpunkts (unter 5 cm nie, ab 10 cm immer)
# --------------------------------------------------------------------------------------

def _rahmungsgrenze(haus, basis) -> float:
    """Der kleinste Abstand, an dem die Rahmung noch hält, auf 1 mm. Mit dem Prüfmass
    gerechnet: von der heutigen Kamera aus so lange näher, wie es mit der kürzesten
    zulässigen Brennweite noch geht."""
    ziel = sichtmass.angehobenes_ziel(basis)
    d0 = math.hypot(basis["auge"][0] - ziel[0], basis["auge"][1] - ziel[1])
    ux, uy = (basis["auge"][0] - ziel[0]) / d0, (basis["auge"][1] - ziel[1]) / d0
    letzter = d0
    d = d0
    while d > sichtmass.MINDESTABSTAND_M:
        ort = (ziel[0] + ux * d, ziel[1] + uy * d, basis["auge"][2])
        f = max(sichtmass.KUERZESTE_BRENNWEITE_MM,
                basis["brennweite_mm"] * sichtmass.RIEGEL * (1 + 1e-9)
                / sichtmass.fuellgrad(d, basis["azimut_grad"], ziel[2] - haus[0][2],
                                      basis["brennweite_mm"], basis["seitenverhaeltnis"], haus))
        kamera = {"auge": ort, "blick_auf": (ziel[0], ziel[1], ort[2]), "brennweite_mm": f,
                  "shift_mm": f * (ziel[2] - ort[2]) / d,
                  "seitenverhaeltnis": basis["seitenverhaeltnis"]}
        if f > basis["brennweite_mm"] or not sichtmass.rahmung_haelt(
                kamera, haus, azimut_grad=basis["azimut_grad"],
                zielhoehe_ueber_fuss=ziel[2] - haus[0][2]):
            return letzter
        letzter = d
        d -= 0.001
    return letzter


def test_reihe_ueber_den_spielraum_in_zentimeterschritten():
    """Ein breiter Riegel quer vor der Kamera, in Schritten von 1 cm verschoben. Hinter ihm
    ist alles verdeckt, vor ihm nichts; das freie Wegstück reicht von seiner Vorderkante
    bis zur Rahmungsgrenze und wächst je Schritt um einen Zentimeter, von «gibt es nicht»
    bis 25 cm. Zugesagt: unter 5 cm nie herangezogen, ab 10 cm immer, dazwischen beides
    erlaubt. In jedem Schritt gelten die Zusagen von oben."""
    basis = kameras.kamerasatz(HAUS, kuerzel=["s"])["kameras"][0]
    d_min = _rahmungsgrenze(HAUS, basis)
    uy = (basis["auge"][1] - basis["blick_auf"][1]) / basis["abstand_m"]
    geloest = {"unter_5": 0, "zwischen": 0, "ab_10": 0}
    gezaehlt = dict(geloest)
    for schritt in range(-10, 26):
        stueck = schritt / 100.0 + 0.005                    # nie genau auf der Schwelle
        kante_y = basis["blick_auf"][1] + uy * (d_min + stueck)
        riegel = sichtstrahl.quader((7.0, kante_y - 1.0), 60.0, 2.0, 14.0, name="riegel")
        urteil = _pruefe(HAUS, [riegel])
        gruppe = ("unter_5" if stueck < 0.05 else "ab_10" if stueck >= 0.10 else "zwischen")
        gezaehlt[gruppe] += 1
        geloest[gruppe] += urteil["kamera"]["sicht"]["bewegt"]
    assert geloest["unter_5"] == 0, geloest
    assert geloest["ab_10"] == gezaehlt["ab_10"] == 16, (geloest, gezaehlt)
    assert gezaehlt["unter_5"] == 15 and gezaehlt["zwischen"] == 5


def test_wo_die_rahmung_einmal_nicht_mehr_haelt_haelt_sie_naeher_am_haus_nie_wieder():
    """Die Feinsuche hört auf, sobald an einem Standpunkt auch das weiteste Objektiv die
    Rahmung nicht mehr hält. Das ist nur richtig, wenn es näher am Haus nicht wieder geht.
    Nachgemessen an 120 Zufallshäusern, je vom Standort bis 6 m in 25-cm-Schritten: Die
    Standpunkte mit haltender Rahmung bilden ein einziges Stück, das am Standort beginnt."""
    import random
    r = random.Random(7306)
    for _ in range(120):
        haus = [[0.0, 0.0, 0.0], [r.uniform(5, 40), r.uniform(5, 30), r.uniform(3, 30)]]
        vorgabe = {"modus": r.choice(kameras.MODI), "brennweite_mm": r.choice((28.0, 35.0, 50.0)),
                   "seitenverhaeltnis": r.choice((16 / 9, 1.0, 0.8))}
        basis = kameras.kamerasatz(haus, kuerzel=[r.choice(sz.RICHTUNGEN)], **vorgabe)["kameras"][0]
        if not basis["vollstaendig"] or basis["fuellgrad"] < kameras.BILDBREITE_ABBRUCH:
            continue
        ziel = sichtmass.angehobenes_ziel(basis)
        d0 = math.hypot(basis["auge"][0] - ziel[0], basis["auge"][1] - ziel[1])
        ux, uy = (basis["auge"][0] - ziel[0]) / d0, (basis["auge"][1] - ziel[1]) / d0
        kw = {"azimut_grad": basis["azimut_grad"], "modus": basis["modus"],
              "seitenverhaeltnis": basis["seitenverhaeltnis"]}
        haelt = []
        d = d0 - 0.01
        while d >= kameras.MIN_ZIEH_ABSTAND_M:
            ort = (ziel[0] + ux * d, ziel[1] + uy * d, basis["auge"][2])
            bei_f0 = kameras.rahmung_am_standpunkt(ort, ziel, haus,
                                                   brennweite_mm=basis["brennweite_mm"], **kw)
            f = max(kameras.ZIEH_BRENNWEITE_MIN_MM, basis["brennweite_mm"]
                    * kameras.BILDBREITE_ABBRUCH / bei_f0["fuellgrad"] * (1 + 1e-9))
            haelt.append(f <= basis["brennweite_mm"] and kameras.rahmung_am_standpunkt(
                ort, ziel, haus, brennweite_mm=f, **kw)["haelt"])
            d -= 0.25
        assert haelt == sorted(haelt, reverse=True), (haus, vorgabe, basis["kuerzel"])


# --------------------------------------------------------------------------------------
# Schwelle 4: die kürzeste Brennweite
# --------------------------------------------------------------------------------------

@pytest.mark.parametrize("brennweite", [24.0 + i * 0.25 for i in range(13)] + [28.0, 31.5, 35.0, 50.0])
def test_reihe_ueber_die_bestellte_brennweite(brennweite):
    """Von 24 mm aufwärts in Viertelmillimetern: Mit 24 mm bestellt gibt es kein weiteres
    Objektiv, knapp darüber ein wenig. Je Brennweite drei Riegel in verschiedener Lage
    zwischen Kamera und Haus; nie fällt die Brennweite unter 24 mm."""
    basis = kameras.kamerasatz(HAUS, kuerzel=["s"], brennweite_mm=brennweite)["kameras"][0]
    bewegt = 0
    for anteil in (0.97, 0.9, 0.8):
        y = basis["blick_auf"][1] + (basis["auge"][1] - basis["blick_auf"][1]) * anteil
        riegel = sichtstrahl.quader((7.0, y), 60.0, 1.0, 14.0)
        urteil = _pruefe(HAUS, [riegel], brennweite_mm=brennweite)
        assert urteil["klasse"] != "frei"
        bewegt += urteil["kamera"]["sicht"]["bewegt"]
    if brennweite >= 28.0:
        assert bewegt >= 1, "Mit Luft bis 24 mm muss der Riegel dicht vor der Kamera lösbar sein."


def test_unter_24_mm_bestellt_wird_nie_verlaengert_und_nie_weiter_verkuerzt():
    basis = kameras.kamerasatz(HAUS, kuerzel=["s"], brennweite_mm=20.0)["kameras"][0]
    for versatz in (1.5, 3.0, 6.0):
        schuppen = sichtstrahl.quader((basis["auge"][0], basis["auge"][1] + versatz), 30.0, 1.0, 12.0)
        urteil = _pruefe(HAUS, [schuppen], brennweite_mm=20.0)
        assert urteil["kamera"]["brennweite_mm"] == 20.0


# --------------------------------------------------------------------------------------
# Schwelle 5: die Höhe, ab der ein Bau den Fuss des Hauses verdeckt
# --------------------------------------------------------------------------------------

def test_reihe_ueber_die_hoehe_des_nachbarbaus_in_fuenf_zentimeter_schritten():
    """Ein Bau vor der Kamera wächst von 0,3 m auf 4,3 m. Solange die Kamera über ihn
    hinweg den Fuss des Hauses sieht, verdeckt er nichts; darüber zuerst den Fuss. Die
    Schwelle liegt knapp unter Augenhöhe, und beide Seiten sind besetzt. Das alte Raster
    begann erst bei 15 % der Haushöhe und sah die ersten Zentimeter nicht."""
    basis = kameras.kamerasatz(HAUS, kuerzel=["s"])["kameras"][0]
    frei = []
    for i in range(81):
        hoehe = 0.3 + i * 0.05
        bau = sichtstrahl.quader((basis["auge"][0], basis["auge"][1] + 4.0), 20.0, 3.0, hoehe)
        urteil = _pruefe(HAUS, [bau])
        frei.append(urteil["anteil_basis"] == 0.0)
        assert (urteil["kamera"]["sicht"]["vorher"]["verdeckte_punkte"] == 0) == frei[-1], hoehe
    assert frei[0] and not frei[-1]
    wechsel = sum(1 for a, b in zip(frei, frei[1:]) if a != b)
    assert wechsel == 1, "Zwischen «verdeckt nichts» und «verdeckt» liegt genau eine Höhe."
    schwelle = 0.3 + frei.index(False) * 0.05
    assert 1.2 < schwelle < 1.7, schwelle


# --------------------------------------------------------------------------------------
# Schwelle 6: kleine Bauten und die Grenzen des Heranziehens
# --------------------------------------------------------------------------------------

@pytest.mark.parametrize("kante", [2.0 + i * 0.5 for i in range(17)])
def test_reihe_ueber_die_hausgroesse(kante):
    """Vom Kiosk (2 m) bis zum Haus (10 m): Bei kleinen Bauten setzt der Mindestabstand den
    Standort, der Riegel 65 % und die Untergrenze von 6 m zum Blickziel kommen ins Spiel.
    Die Zusagen gelten auch dort, aus zwei Richtungen und mit zwei Lagen des Hindernisses."""
    haus = [[0.0, 0.0, 0.0], [kante, kante * 0.8, max(2.5, kante * 0.7)]]
    for kuerzel in ("s", "eES"):
        basis = kameras.kamerasatz(haus, kuerzel=[kuerzel])["kameras"][0]
        for anteil in (0.95, 0.75):
            ort = [basis["blick_auf"][i] + (basis["auge"][i] - basis["blick_auf"][i]) * anteil
                   for i in range(2)]
            schuppen = sichtstrahl.quader(ort, 3.0, 0.6, 6.0, drehung_grad=basis["azimut_grad"])
            kamera = _pruefe(haus, [schuppen], kuerzel)["kamera"]
            p = kameras.HUELLBOX_PUFFER_M
            assert not (haus[0][0] - p <= kamera["auge"][0] <= haus[1][0] + p
                        and haus[0][1] - p <= kamera["auge"][1] <= haus[1][1] + p)


# --------------------------------------------------------------------------------------
# Mehrere tausend Zufallsfälle gegen die Basis: nie schlechter, nie falsch «frei»
# --------------------------------------------------------------------------------------

@pytest.mark.parametrize("saat", [101, 102, 103, 104])
def test_zufallsfaelle_gegen_die_basis_keiner_wird_schlechter(saat, monkeypatch):
    """Vier weitere Sätze aus anderer Saat, je 461 Fälle (1844 zusammen), mit Masten,
    Türmen und Eckbauten. Verglichen wird mit der heutigen Kamera und gemessen mit dem
    dichten Mass: Entweder ist die neue Kamera Zahl für Zahl die alte (verdeckt sie, trägt
    sie zusätzlich die Warnung), oder die alte war verdeckt und die neue ist frei und
    regelgerecht gerahmt. Und nie sagt eine «frei», die es nicht ist. (Ohne die Suche des
    Prüfmasses nach Lösbarkeit; die läuft im Hauptsatz.)"""
    monkeypatch.setattr(sz, "SAAT", saat)
    bewegt = gemeldet = 0
    for fall in sz.faelle():
        haus, nachbarn = fall["szene"]["haus"], fall["szene"]["nachbarn"]
        basis = sz.heutige_kamera(fall)
        kamera = sz.mit_sichtpruefung(fall)
        sicht = kamera.pop("sicht")
        wo = (saat, fall["szene"]["name"], fall["kuerzel"])
        anteil_basis = sichtmass.verdeckter_anteil(basis["auge"], haus, nachbarn)
        assert sicht["frei"] is not None, wo
        if sicht["bewegt"]:
            bewegt += 1
            assert anteil_basis > 0.0, wo
            assert sichtmass.verdeckter_anteil(kamera["auge"], haus, nachbarn) \
                <= sichtmass.FREI_HOECHSTENS, wo
            assert sichtmass.rahmung_haelt(
                sz._nur_stellung(kamera), haus, azimut_grad=basis["azimut_grad"],
                zielhoehe_ueber_fuss=sichtmass.angehobenes_ziel(basis)[2] - haus[0][2]), wo
            kamera["warnungen"] = ()          # die Brennweiten-Warnung ist gewollt neu
        elif sicht["frei"] is False:
            gemeldet += 1
            assert kamera.pop("warnungen") == basis["warnungen"] + (sicht["vermerk"],), wo
            assert {k: v for k, v in basis.items() if k != "warnungen"} == kamera, wo
        else:
            assert anteil_basis <= sichtmass.FREI_HOECHSTENS, wo     # sagt frei: ist es
            assert kamera == basis, wo
    assert bewegt >= 30 and gemeldet >= 30, (bewegt, gemeldet)


# --------------------------------------------------------------------------------------
# Nicht entscheidbar: nicht raten, wie die Basis handeln
# --------------------------------------------------------------------------------------

def _teils_ungemessen(nachbarn, jeder: int):
    """Eine Sichtprüfung, die jeden ``jeder``-ten Strahl nicht messen kann."""
    zaehler = {"n": 0}

    def _pruefe_teils(auge, punkt):
        zaehler["n"] += 1
        if zaehler["n"] % jeder == 0:
            return {"frei": None, "grund": "NICHT GEMESSEN"}
        return sichtstrahl.sicht_frei(auge, punkt, nachbarn)

    return _pruefe_teils


@pytest.mark.parametrize("jeder", [1, 2, 3, 7, 15, 1000])
def test_teils_ungemessen_und_nichts_verdeckt_ist_nicht_entscheidbar(jeder):
    """Kein Punkt verdeckt, aber nicht jeder gemessen (und sei es einer von tausend): Das
    ist nicht «frei». Die Kamera bleibt die der Basis, das Ergebnis sagt «nicht prüfbar»."""
    basis = kameras.kamerasatz(HAUS, kuerzel=["s"])["kameras"][0]
    satz = kameras.kamerasatz(HAUS, kuerzel=["s"], sicht_frei=_teils_ungemessen([], jeder))
    kamera = satz["kameras"][0]
    sicht = kamera.pop("sicht")
    assert kamera == basis
    assert sicht["frei"] is None and sicht["abbruch"] == "nicht_pruefbar"
    assert sicht["urteil"] == "nicht_pruefbar" and "NICHT GEPRÜFT" in sicht["vermerk"]
    assert satz["verdeckt"] == []


@pytest.mark.parametrize("jeder", [2, 3, 7])
def test_auf_einen_standpunkt_mit_ungemessener_sicht_wird_nicht_gezogen(jeder):
    """Am Standort sicher verdeckt (ein gemessener Punkt genügt dafür), aber unterwegs ist
    nie jeder Punkt messbar: Die Kamera wird nicht auf Verdacht herangezogen."""
    basis = kameras.kamerasatz(HAUS, kuerzel=["s"])["kameras"][0]
    schuppen = [sichtstrahl.quader((basis["auge"][0], basis["auge"][1] + 5.0), 30.0, 2.0, 14.0)]
    kamera = kameras.kamerasatz(HAUS, kuerzel=["s"],
                                sicht_frei=_teils_ungemessen(schuppen, jeder))["kameras"][0]
    assert kamera["sicht"]["frei"] is False and not kamera["sicht"]["bewegt"]
    assert kamera["auge"] == basis["auge"]
    # Mit einer Prüfung, die alles misst, ist derselbe Fall lösbar: Der Unterschied ist
    # allein das Nichtwissen.
    assert kameras.kamerasatz(HAUS, kuerzel=["s"], sicht_frei=sichtstrahl.pruefer(schuppen)
                              )["kameras"][0]["sicht"]["bewegt"]


# --------------------------------------------------------------------------------------
# Gemeine Fälle
# --------------------------------------------------------------------------------------

def _basis(kuerzel="s", haus=HAUS):
    return kameras.kamerasatz(haus, kuerzel=[kuerzel])["kameras"][0]


def test_gemein_die_kamera_steht_im_nachbarbau():
    """Der gerechnete Standort liegt IN einem Bau. Das ist verdeckt (wer im Bau steht,
    sieht nichts), und frei wird die Kamera erst ausserhalb."""
    b = _basis()
    um_die_kamera = sichtstrahl.quader((b["auge"][0], b["auge"][1]), 6.0, 6.0, 10.0, name="um")
    urteil = _pruefe(HAUS, [um_die_kamera])
    assert urteil["klasse"] == "loesbar" and urteil["kamera"]["sicht"]["bewegt"]
    assert not sichtstrahl.punkt_im_koerper(urteil["kamera"]["auge"], um_die_kamera)


def test_gemein_der_nachbarbau_klebt_an_der_fassade():
    """Wand an Wand: Kein Standpunkt der Welt macht diese Fassade frei."""
    anbau = sichtstrahl.quader((7.0, -3.0), 14.0, 6.0, 9.0)
    urteil = _pruefe(HAUS, [anbau])
    assert urteil["klasse"] == "unloesbar"
    assert urteil["kamera"]["sicht"]["vermerk"].startswith("verdeckt, 100,0 %")
    assert _pruefe(HAUS, [anbau], "n")["klasse"] == "frei"


def test_gemein_ein_halb_angebauter_nachbar_ist_teilverdeckt_mit_der_richtigen_zahl():
    """Ein Anbau vor der halben Fassade, halb so hoch: ein Viertel verdeckt, von überall."""
    anbau = sichtstrahl.quader((3.5, -2.0), 7.0, 4.0, 4.5)
    urteil = _pruefe(HAUS, [anbau])
    sicht = urteil["kamera"]["sicht"]
    assert urteil["klasse"] == "unloesbar" and sicht["urteil"] == "teilverdeckt"
    assert sicht["verdeckt_anteil"] == pytest.approx(urteil["anteil"], abs=0.03)
    assert 0.2 < urteil["anteil"] < 0.4


def test_gemein_bauten_hinter_haus_und_hinter_kamera_stoeren_nicht():
    b = _basis()
    hinter_haus = sichtstrahl.quader((7.0, 30.0), 40.0, 10.0, 30.0)
    hinter_kamera = sichtstrahl.quader((b["auge"][0], b["auge"][1] - 6.0), 40.0, 10.0, 30.0)
    neben = sichtstrahl.quader((60.0, -10.0), 10.0, 10.0, 30.0)
    assert _pruefe(HAUS, [hinter_haus, hinter_kamera, neben])["klasse"] == "frei"


def test_gemein_ein_schwebender_bau_verdeckt_nur_oben():
    """Eine Brücke über dem Weg, Unterkante über Augenhöhe: Die Kamera schaut darunter
    durch zum Fuss, aber der obere Teil der Fassade ist verdeckt. Das zählt als verdeckt."""
    b = _basis()
    bruecke = sichtstrahl.quader((7.0, b["auge"][1] + 8.0), 40.0, 3.0, 20.0, fuss_z=3.0)
    urteil = _pruefe(HAUS, [bruecke])
    assert urteil["klasse"] != "frei" and urteil["basis"]["auge"][2] < 3.0


def test_gemein_eine_gasse_zwischen_zwei_bauten():
    """Zwei Bauten lassen eine Gasse, durch die die Kamera schaut. Zu eng: verdeckt. Breit
    genug: frei. Die Breite wächst in 25-cm-Schritten über die Schwelle."""
    b = _basis()
    y = b["auge"][1] + 10.0
    frei = []
    for i in range(40):
        halbe = 0.5 + i * 0.25
        links = sichtstrahl.quader((b["auge"][0] - halbe - 5.0, y), 10.0, 4.0, 14.0)
        rechts = sichtstrahl.quader((b["auge"][0] + halbe + 5.0, y), 10.0, 4.0, 14.0)
        frei.append(_pruefe(HAUS, [links, rechts])["anteil_basis"] == 0.0)
    assert not frei[0] and frei[-1]
    assert 5 <= frei.count(True) <= 35
    assert frei == sorted(frei), "Einmal breit genug, immer breit genug."


def test_gemein_hochformat_gekippt_gelaende_und_landeskoordinaten():
    """Andere Kamera, anderes Format, gesetzter Geländestand, Haus weit weg vom Ursprung
    und auf 412 m Höhe: dieselben Zusagen."""
    haus = [[2600000.0, 1200000.0, 412.5], [2600016.0, 1200011.0, 424.0]]
    for vorgabe in ({"seitenverhaeltnis": 0.8}, {"modus": kameras.MODUS_GEKIPPT},
                    {"gelaende_z": 413.0}, {"deckungsgrad": 0.8}):
        for kuerzel in ("s", "wWN", "e"):
            b = kameras.kamerasatz(haus, kuerzel=[kuerzel], **vorgabe)["kameras"][0]
            ort = [b["blick_auf"][i] + (b["auge"][i] - b["blick_auf"][i]) * 0.93 for i in range(2)]
            schuppen = sichtstrahl.quader(ort, 5.0, 1.0, 9.0, fuss_z=412.5,
                                          drehung_grad=37.0, name="schuppen")
            _pruefe(haus, [schuppen], kuerzel, **vorgabe)


def test_gemein_das_auge_ueber_dem_dach_sieht_auch_das_dach():
    """Augenhöhe 30 m über einem 9 m hohen Haus: Das Dach gehört zur Sicht. Ein Bau, der
    nur das Dach verdeckt, zählt."""
    haus = HAUS
    kamera = kameras.kamerasatz(haus, kuerzel=["s"], augenhoehe_m=30.0, modus=kameras.MODUS_GEKIPPT)
    auge = kamera["kameras"][0]["auge"]
    assert any(p[2] == 9.0 for p in kameras.sichtpunkte(haus, auge))
    # Eine Platte knapp über dem Dach, zur Kamera hin versetzt: verdeckt Dachpunkte.
    platte = sichtstrahl.quader((7.0, -1.0), 14.0, 10.0, 0.5, fuss_z=12.0)
    befund = kameras.sichtbefund(auge, haus, sichtstrahl.pruefer([platte]))
    assert befund["frei"] is False
    assert sichtmass.verdeckter_anteil(auge, haus, [platte]) > 0.01


def test_gemein_ausschnitt_kamera_wird_gemeldet_nie_bewegt():
    """Eine lange, flache Halle als Ausschnitt (Entscheid 75): gewollt nah. Steht etwas
    davor, steht es im Ergebnis; bewegt wird die Kamera nicht."""
    halle = [[0.0, 0.0, 0.0], [66.0, 12.0, 3.45]]
    ohne = kameras.kamerasatz(halle, kuerzel=["s"], ausschnitt=True)["kameras"][0]
    assert ohne["ausschnitt"]
    wand = sichtstrahl.quader((33.0, ohne["auge"][1] / 2.0), 80.0, 0.5, 6.0)
    kamera = kameras.kamerasatz(halle, kuerzel=["s"], ausschnitt=True,
                                sicht_frei=sichtstrahl.pruefer([wand]))["kameras"][0]
    sicht = kamera.pop("sicht")
    assert sicht["frei"] is False and not sicht["bewegt"]
    assert sicht["abbruch"] == "nicht_nachgefuehrt" and "Ausschnitt" in sicht["vermerk"]
    assert kamera["auge"] == ohne["auge"] and kamera["brennweite_mm"] == ohne["brennweite_mm"]


def test_gemein_die_sichtpruefung_wird_nur_mit_auge_und_punkt_gefragt():
    """Die Prüfung der Szene bekommt genau zwei Dreiergruppen, nie etwas anderes: Das ist
    die Form, die der Strahlenschuss des Runners annimmt. Und jeder Sichtpunkt wird genau
    einmal gefragt, wenn nichts verdeckt."""
    gefragt = []

    def _merke(auge, punkt):
        gefragt.append((auge, punkt))
        return True

    satz = kameras.kamerasatz(HAUS, kuerzel=["s", "nNE"], sicht_frei=_merke)
    erwartet = sum(len(kameras.sichtpunkte(HAUS, k["auge"])) for k in satz["kameras"])
    assert len(gefragt) == erwartet
    assert all(len(a) == 3 and len(p) == 3 for a, p in gefragt)
