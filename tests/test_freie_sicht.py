"""«Freie Sicht aufs Haus» (A0306): Heranziehen und Rahmen in einem Ablauf.

**Die Lage vorher.** ``kameras.ziehe_bis_frei`` rechnete seit Wochen die Schritte, mit
denen eine Kamera an einem Nachbarbau vorbei näher ans Haus rückt, und hatte keinen
Aufrufer (``docs/PLAN.md``: «Verdeckung wird auf dem Produktpfad nicht behandelt»). Die
Gegenrichtung, ``schiebe_bis_im_bild``, lief. Wer die zwei hintereinander schaltet, lässt
sie gegeneinander ziehen.

**Die Zielfunktion** (Auftrag A0306, Runde 2 nach dem Gegenlesen): Auf mindestens 40
erfundenen Szenen sind 100 % der lösbaren Fälle nach einem **unabhängigen, dichten Mass**
frei und richtig gerahmt ODER ehrlich als «teilverdeckt, x %» gemeldet; keine einzige
Kamera heisst «frei» bei mehr als 1 % Verdeckung; Fälle ohne Verdeckung bleiben unverändert.

Der Satz steht in ``tests/sichtszenen.py``, das Mass in ``tests/sichtmass.py``. Das Mass
benutzt nichts von der Lösung; die erste Probe unten hält das am Quelltext fest.
"""
from __future__ import annotations

import ast
import math
import random
import re
from pathlib import Path

import pytest

import sichtmass
import sichtszenen as sz
from aiimaging import kameras, kosmo_szene, sichtstrahl

HIER = Path(__file__).resolve().parent
RUNNER = HIER.parent / "src" / "aiimaging" / "runners" / "blender_depth_stage.py"
HAUS = [[0.0, 0.0, 0.0], [14.0, 10.0, 9.0]]


@pytest.fixture(scope="module")
def heute():
    """Der Stand vor A0306: ``kamerasatz`` ohne Sichtprüfung."""
    return sz.messe(None)


@pytest.fixture(scope="module")
def neu():
    """Der eine Ablauf: ``kamerasatz`` mit Sichtprüfung."""
    return sz.messe(sz.mit_sichtpruefung)


# --------------------------------------------------------------------------------------
# Das Prüfmass ist unabhängig von der Lösung
# --------------------------------------------------------------------------------------

def test_das_pruefmass_benutzt_nichts_von_der_loesung():
    """**Am Quelltext geprüft, nicht behauptet** (G-A0306, M2). ``sichtmass.py`` importiert
    nichts aus dem Paket und nennt die Kamera-Bibliothek nirgends im Code. Es liest von
    einer Kamera nur, wo sie steht und wie sie schaut, nie, was sie über sich urteilt."""
    quelle = (HIER / "sichtmass.py").read_text(encoding="utf-8")
    baum = ast.parse(quelle)
    importiert = set()
    for knoten in ast.walk(baum):
        if isinstance(knoten, ast.Import):
            importiert |= {name.name.split(".")[0] for name in knoten.names}
        elif isinstance(knoten, ast.ImportFrom):
            importiert.add((knoten.module or "").split(".")[0])
    assert importiert == {"__future__", "math", "numpy"}, importiert
    namen = {k.id for k in ast.walk(baum) if isinstance(k, ast.Name)} \
        | {k.attr for k in ast.walk(baum) if isinstance(k, ast.Attribute)}
    assert not namen & {"kameras", "sichtstrahl", "aiimaging", "sichtszenen"}
    gelesen = {k.slice.value for k in ast.walk(baum)
               if isinstance(k, ast.Subscript) and isinstance(k.slice, ast.Constant)
               and isinstance(k.slice.value, str)}
    verboten = {"fuellgrad", "fuellgrad_breite", "fuellgrad_hoehe", "sicht", "vollstaendig",
                "warnungen", "flaechenanteil", "abstand_m", "begruendung"}
    assert not gelesen & verboten, gelesen & verboten


def test_der_messlauf_reicht_dem_pruefmass_nur_die_stellung():
    """Die Buchhaltung in ``sichtszenen.beurteile`` gibt dem Mass eine Kamera nur als
    Stellung weiter (fünf Felder). Das Selbsturteil der Lösung liest sie an einer Stelle:
    um es mit dem Mass zu VERGLEICHEN."""
    assert set(sz._nur_stellung(sz.heutige_kamera(sz.faelle()[0]))) == {
        "auge", "blick_auf", "brennweite_mm", "shift_mm", "seitenverhaeltnis"}


def test_die_zahlen_des_massstabs_sind_auf_beiden_seiten_dieselben():
    """Das Mass schreibt Sensor, Bildrand, Riegel und Grenzen als eigene Zahlen. Hier steht,
    dass es dieselben sind wie in der Bibliothek: Ändert eine Seite sie, wird es rot."""
    assert sichtmass.SENSORBREITE_MM == kameras.SENSOR_BREITE_MM
    assert sichtmass.BILDRAND == kameras.BILDRAND
    assert sichtmass.RIEGEL == kameras.BILDBREITE_ABBRUCH
    assert sichtmass.KUERZESTE_BRENNWEITE_MM == kameras.ZIEH_BRENNWEITE_MIN_MM
    assert sichtmass.MINDESTABSTAND_M == kameras.MIN_ZIEH_ABSTAND_M
    assert sichtmass.PUFFER_UM_DAS_HAUS_M == kameras.HUELLBOX_PUFFER_M
    assert sichtmass.FREI_HOECHSTENS == kameras.SICHT_GERINGFUEGIG == 0.01
    assert kameras.ZIEH_BRENNWEITE_MIN_MM == min(kosmo_szene.KAMERAS_AUTO_BRENNWEITEN)


def test_das_pruefmass_misst_bis_an_kante_und_fuss():
    """61 mal 31 Punkte je Fläche, die äussersten einen Millimeter von Kante und Fuss."""
    (punkte, flaeche, tastzeilen), = sichtmass.flaechen(HAUS, (7.0, -30.0, 1.7))
    assert len(punkte) == 61 * 31 and flaeche == 14.0 * 9.0
    assert len(tastzeilen) == 701 * 5
    assert punkte[:, 0].min() == pytest.approx(0.001) and punkte[:, 0].max() == pytest.approx(13.999)
    assert punkte[:, 2].min() == pytest.approx(0.001) and punkte[:, 2].max() == pytest.approx(8.999)
    assert len(sichtmass.flaechen(HAUS, (40.0, -30.0, 1.7))) == 2
    assert len(sichtmass.flaechen(HAUS, (40.0, -30.0, 30.0))) == 3      # mit Dach


def test_drei_strahlentests_ein_urteil():
    """Der Schnitt des Prüfmasses (Wandebenen, alle Punkte auf einmal), der Strahlentest
    der Bibliothek (gedrehtes Achsensystem) und blosses Abtasten der Strecke: An 2000
    Zufallsstrecken sagen die ersten zwei dasselbe, und das Abtasten widerspricht nie (es
    kann einen Streifschuss übersehen, aber keinen erfinden)."""
    import numpy as np
    r = random.Random(4306)
    treffer = 0
    for _ in range(80):
        bauten = [sichtstrahl.quader((r.uniform(-15, 15), r.uniform(-15, 15)), r.uniform(0.5, 9),
                                     r.uniform(0.5, 9), r.uniform(2, 20), fuss_z=r.uniform(-1, 3),
                                     drehung_grad=r.choice((0.0, 0.0, 20.0, 45.0, 90.0, 133.0)))
                  for _ in range(5)]
        auge = (r.uniform(-30, 30), r.uniform(-30, 30), r.uniform(0.5, 12))
        ziele = np.array([[r.uniform(-30, 30), r.uniform(-30, 30), r.uniform(0, 15)]
                          for _ in range(5)])
        for bau in bauten:
            mass = sichtmass.getroffen(auge, ziele, bau)
            for ziel, sagt_mass in zip(ziele, mass):
                bibliothek = sichtstrahl.strecke_trifft(auge, tuple(ziel), bau) is not None
                assert bool(sagt_mass) == bibliothek, (auge, tuple(ziel), bau)
                treffer += bibliothek
                n = max(2, int(math.dist(auge, ziel) / 0.05))
                abgetastet = any(sichtstrahl.punkt_im_koerper(
                    tuple(auge[i] + (ziel[i] - auge[i]) * j / n for i in range(3)), bau)
                    for j in range(n + 1))
                assert bibliothek or not abgetastet
    assert 60 < treffer < 1900


def test_die_vorauswahl_des_pruefmasses_verwirft_keinen_treffer():
    """Das Mass überspringt Bauten, die im Grundriss nicht im Weg stehen können. Über den
    Satz: Was übersprungen wird, hätte keinen einzigen Punkt verdeckt."""
    uebersprungen = 0
    for fall in sz.faelle()[::3]:
        haus, nachbarn = fall["szene"]["haus"], fall["szene"]["nachbarn"]
        auge = sz.heutige_kamera(fall)["auge"]
        for punkte, _flaeche, _zeilen in sichtmass.flaechen(haus, auge):
            for bau in nachbarn:
                if sichtmass._kann_nicht_treffen(auge, punkte, bau):
                    uebersprungen += 1
                    assert not sichtmass.getroffen(auge, punkte, bau).any()
    assert uebersprungen > 100


def test_der_fuellgrad_des_pruefmasses_ist_der_des_kamerasatzes():
    """Der Füllgrad ist im Mass neu ausgeschrieben. Dass er dieselbe Grösse ist wie in der
    Rahmungsregel, zeigt der Vergleich mit dem unveränderten Kamerasatz der Basis (ohne
    Sichtprüfung): über Bauformen, Richtungen, Brennweiten und beide Modi."""
    r = random.Random(5306)
    for _ in range(150):
        haus = [[0.0, 0.0, 3.0], [r.uniform(6, 40), r.uniform(6, 40), 3.0 + r.uniform(4, 30)]]
        vorgabe = {"brennweite_mm": r.choice((24.0, 35.0, 50.0)),
                   "modus": r.choice(kameras.MODI),
                   "seitenverhaeltnis": r.choice((16 / 9, 1.0, 0.8))}
        for kamera in kameras.kamerasatz(haus, **vorgabe)["kameras"]:
            ziel = sichtmass.angehobenes_ziel(kamera)
            eigen = sichtmass.fuellgrad(kamera["abstand_m"], kamera["azimut_grad"],
                                        ziel[2] - 3.0, kamera["brennweite_mm"],
                                        kamera["seitenverhaeltnis"], haus)
            assert eigen == pytest.approx(kamera["fuellgrad"], rel=1e-9)


def test_der_eckentest_des_pruefmasses_urteilt_wie_der_der_bibliothek():
    """Eigene Projektion gegen ``ecken_im_bild``, an 3000 Zufallsstellungen mit Shift."""
    r = random.Random(6306)
    passt = 0
    for _ in range(3000):
        haus = [[0.0, 0.0, 0.0], [r.uniform(6, 30), r.uniform(6, 30), r.uniform(4, 25)]]
        auge = (r.uniform(-60, 90), r.uniform(-90, -8), r.uniform(1.5, 12))
        blick = (haus[1][0] / 2, haus[1][1] / 2, auge[2] if r.random() < 0.7 else r.uniform(2, 10))
        f, shift, sv = r.uniform(20, 60), r.uniform(-2, 9), r.choice((16 / 9, 1.0, 0.8))
        bibliothek = kameras.ecken_im_bild(auge, blick, haus, brennweite_mm=f, shift_mm=shift,
                                           seitenverhaeltnis=sv)
        if abs(bibliothek["max_ueberstehen"] - 1.0) < 1e-6:
            continue                                  # genau auf der Kante: Rundung
        assert sichtmass.ecken_im_bild(auge, blick, f, shift, sv, haus) == bibliothek["passt"]
        passt += bibliothek["passt"]
    assert 300 < passt < 2700


# --------------------------------------------------------------------------------------
# Fertig-Satz 1: der Satz, sein Erzeuger, der heutige Wert
# --------------------------------------------------------------------------------------

def test_der_satz_hat_mindestens_vierzig_szenen_aus_acht_richtungen():
    szenen = sz.szenen()
    assert len(szenen) >= 40
    assert len(sz.RICHTUNGEN) == 8 and set(sz.RICHTUNGEN) <= set(kameras.RICHTUNGSFOLGE)
    assert len(sz.faelle()) == sum(len(s["richtungen"]) for s in szenen) == 461
    for szene in szenen:
        assert 1 <= len(szene["nachbarn"]) <= 5, szene["name"]
    hoehen = sorted(n["z"][1] - n["z"][0] for s in szenen for n in s["nachbarn"])
    assert hoehen[0] < 4.0 and hoehen[-1] > 30.0
    assert any(n["drehung_grad"] for s in szenen for n in s["nachbarn"])


def test_mast_turm_ecke_und_die_faelle_des_gegenlesens_stehen_im_satz():
    arten = {s["art"] for s in sz.szenen()}
    assert {"mast", "turm", "ecke", "gegenlesen"} <= arten
    namen = [s["name"] for s in sz.szenen() if s["art"] == "gegenlesen"]
    assert namen == ["E01", "E02", "E03", "E04", "E05"]
    e01 = next(s for s in sz.szenen() if s["name"] == "E01")
    assert e01["haus"] == [[0.0, 0.0, 0.0], [12.0, 10.0, 9.0]]
    assert e01["nachbarn"][0]["mitte"] == (0.9, -10.91) and e01["nachbarn"][0]["halb"] == (1.5, 1.5)
    schmal = [n for s in sz.szenen() for n in s["nachbarn"] if 2 * n["halb"][0] <= 0.8]
    assert len(schmal) >= 8


def test_der_erzeuger_liefert_jedes_mal_denselben_satz():
    assert sz.szenen() == sz.szenen()


def test_kein_nachbarbau_steht_im_haus():
    """Sonst wäre «verdeckt» keine Frage der Sicht, sondern ein Fehler des Erzeugers."""
    for szene in sz.szenen():
        (x0, y0, z0), (x1, y1, z1) = szene["haus"]
        ecken = [(x, y, z) for x in (x0, x1) for y in (y0, y1) for z in (z0 + 0.1, z1)]
        mitte = ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)
        for nachbar in szene["nachbarn"]:
            assert not any(sichtstrahl.punkt_im_koerper(p, nachbar)
                           for p in ecken + [mitte]), szene["name"]


def test_alle_drei_klassen_sind_im_satz(heute):
    assert heute["zahl"] == {"frei": 332, "loesbar": 76, "unloesbar": 53}, heute["zahl"]


def test_heute_ist_kein_einziger_verdeckter_fall_frei(heute):
    """**Der gemessene Ausgangswert: 0 von 76.** Die Regel wurde nicht aufgerufen. Und alle
    129 verdeckten Kameras werden ohne ein Wort geliefert: 129 Verstösse."""
    assert heute["erreicht"]["loesbar"] == 0 and heute["anteil_loesbar"] == 0.0
    assert heute["frei_gestellt"] == 0 and heute["ehrlich_gemeldet"] == 0
    assert len(heute["verstoesse"]) == 129
    # Wo nichts verdeckt, hält die heutige Kamera die Rahmungsregel: Der Satz misst die
    # Verdeckung, nicht eine schon vorher kaputte Rahmung.
    assert heute["erreicht"]["frei"] == heute["zahl"]["frei"]


def test_die_alte_schaltung_zieht_gegeneinander(heute):
    """Erst ``ziehe_bis_frei``, dann ``schiebe_bis_im_bild``, mit fester Brennweite:
    **gemessen** stellt das 28 von 76 frei, und in einem Teil der Fälle schiebt der
    Eckentest die eben frei gestellte Kamera wieder hinter den Nachbarbau."""
    geloest = zurueck_ins_verdeckte = 0
    for fall, urteil in heute["einzeln"]:
        if urteil["klasse"] != "loesbar":
            continue
        alt = sz.nacheinander(fall)
        nachher = sz.beurteile(fall, alt["kamera"])
        geloest += nachher["frei"] and nachher["gerahmt"]
        zurueck_ins_verdeckte += (alt["gezogen_frei"] and alt["zurueckgeschoben"]
                                  and not nachher["frei"])
    assert geloest == 28, geloest
    assert zurueck_ins_verdeckte >= 10, zurueck_ins_verdeckte


# --------------------------------------------------------------------------------------
# Fertig-Satz 3: der Zielwert der Runde 2
# --------------------------------------------------------------------------------------

def test_ZIEL_alle_loesbaren_faelle_sind_frei_gestellt_oder_ehrlich_gemeldet(neu):
    verfehlt = [(f["szene"]["name"], f["kuerzel"], u["anteil"], u["gerahmt"])
                for f, u in neu["einzeln"] if u["klasse"] == "loesbar" and not u["erreicht"]]
    assert not verfehlt, verfehlt
    assert neu["anteil_loesbar"] == 1.0
    # Und «ehrlich gemeldet» ist nicht der bequeme Ausweg: 75 der 76 sind wirklich frei.
    assert neu["frei_gestellt"] == 75 and neu["ehrlich_gemeldet"] == 1


def test_ZIEL_keine_kamera_heisst_frei_bei_mehr_als_einem_prozent(neu):
    """Über ALLE 461 Fälle, nicht nur die lösbaren: Was «frei» sagt, ist nach dem dichten
    Mass zu höchstens 1 % verdeckt."""
    assert neu["verstoesse"] == []
    for fall, urteil in neu["einzeln"]:
        sicht = urteil["kamera"]["sicht"]
        if sicht["frei"] is True:
            assert urteil["anteil"] <= sichtmass.FREI_HOECHSTENS, fall["szene"]["name"]
            assert sicht["urteil"] == "frei" and sicht["verdeckt_anteil"] == 0.0


def test_jede_bewegte_kamera_ist_frei_und_gerahmt_nach_dem_dichten_mass(neu):
    bewegte = [(f, u) for f, u in neu["einzeln"] if u["kamera"]["sicht"]["bewegt"]]
    assert len(bewegte) == 75
    for fall, urteil in bewegte:
        assert urteil["frei"] and urteil["gerahmt"], (fall["szene"]["name"], fall["kuerzel"])


def test_was_nicht_frei_ist_traegt_teilverdeckt_mit_zahl(neu):
    """Unlösbare und nicht frei gestellte Fälle: ``sicht.frei`` ist falsch, das Urteil
    heisst «teilverdeckt» oder «verdeckt», der Vermerk beginnt damit und nennt die Zahl,
    und die Zahl stimmt mit dem dichten Mass überein (auf drei Prozentpunkte)."""
    gemeldete = [(f, u) for f, u in neu["einzeln"] if u["kamera"]["sicht"]["frei"] is False]
    assert len(gemeldete) == 54
    for fall, urteil in gemeldete:
        kamera = urteil["kamera"]
        sicht = kamera["sicht"]
        wo = (fall["szene"]["name"], fall["kuerzel"])
        assert sicht["urteil"] in ("teilverdeckt", "verdeckt") and not sicht["bewegt"], wo
        assert re.match(r"(teil)?verdeckt, \d+,\d %", sicht["vermerk"]), sicht["vermerk"][:40]
        assert kameras.prozent(sicht["verdeckt_anteil"]) in sicht["vermerk"], wo
        assert sicht["vermerk"] in kamera["warnungen"], wo
        assert abs(sicht["verdeckt_anteil"] - urteil["anteil"]) < 0.03, wo
        assert kamera["auge"] == urteil["basis"]["auge"], wo
        assert kamera["brennweite_mm"] == urteil["basis"]["brennweite_mm"], wo
    fall = gemeldete[0][0]
    satz = kameras.kamerasatz(fall["szene"]["haus"], kuerzel=[fall["kuerzel"]],
                              sicht_frei=sichtstrahl.pruefer(fall["szene"]["nachbarn"]))
    assert satz["verdeckt"] == [fall["kuerzel"]] and satz["sichtfehler"] == []
    assert any(re.match(rf"{fall['kuerzel']}: (teil)?verdeckt, ", w) for w in satz["warnungen"])


def test_die_faelle_des_gegenlesens(neu):
    """E01: war «frei gemeldet, 9,8 % verdeckt», ist jetzt herangezogen und ganz frei.
    E02 bis E05: waren «frei» gemeldet und teilverdeckt; jetzt bleibt die Kamera stehen
    und sagt, wie viel verdeckt ist."""
    e = {f["szene"]["name"]: u for f, u in neu["einzeln"] if f["szene"]["art"] == "gegenlesen"}
    assert e["E01"]["anteil_basis"] == pytest.approx(0.098, abs=0.002)
    assert e["E01"]["kamera"]["sicht"]["bewegt"] and e["E01"]["anteil"] == 0.0
    assert e["E01"]["gerahmt"] and e["E01"]["kamera"]["brennweite_mm"] > 25.0
    for name in ("E02", "E03", "E04", "E05"):
        sicht = e[name]["kamera"]["sicht"]
        assert sicht["urteil"] == "teilverdeckt" and not sicht["bewegt"], name
        assert sicht["vermerk"].startswith("teilverdeckt, "), name
        assert e[name]["anteil"] > 0.05 and not e[name]["verstoss"], name


# --------------------------------------------------------------------------------------
# Fertig-Satz 2: ein Ablauf, und ohne Verdeckung derselbe Kamerasatz
# --------------------------------------------------------------------------------------

def test_ohne_verdeckung_bleibt_die_kamera_zahl_fuer_zahl_dieselbe(neu):
    freie = [(f, u) for f, u in neu["einzeln"] if u["klasse"] == "frei"]
    assert len(freie) == 332
    for fall, urteil in freie:
        kamera = dict(urteil["kamera"])
        sicht = kamera.pop("sicht")
        assert kamera == urteil["basis"], (fall["szene"]["name"], fall["kuerzel"])
        assert sicht["frei"] is True and sicht["bewegt"] is False
        assert sicht["abbruch"] == "sicht_frei" and sicht["vermerk"] == ""


def _zufallssatz(r: random.Random):
    """Ein zufälliger Aufruf von ``kamerasatz``: Box, Brennweite, Modus, Format, Augenhöhe,
    dazu in je einem Zehntel fester Abstand oder Ausschnitt einer langen Halle."""
    lang = r.random() < 0.1
    dx, dy, dz = ((r.uniform(60, 140), r.uniform(8, 14), r.uniform(3, 6)) if lang
                  else (r.uniform(4, 60), r.uniform(4, 60), r.uniform(2.5, 45)))
    x, y, z = r.uniform(-80, 80), r.uniform(-80, 80), r.choice((0.0, 0.0, -3.0, 412.5))
    vorgabe = {"brennweite_mm": r.choice((24.0, 35.0, 50.0, 85.0)),
               "modus": r.choice(kameras.MODI),
               "seitenverhaeltnis": r.choice((16 / 9, 1.0, 0.8, 4 / 3)),
               "augenhoehe_m": r.choice((1.6, 1.7, 1.7, 5.0, 25.0)),
               "kuerzel": r.sample(kameras.RICHTUNGSFOLGE, r.randint(1, 2))}
    if lang:
        vorgabe["ausschnitt"] = True
    elif r.random() < 0.1:
        vorgabe["abstand_fest_m"] = r.uniform(8, 90)
    if r.random() < 0.3:
        vorgabe["gelaende_z"] = z + r.uniform(0.0, 2.0)
    return [[x, y, z], [x + dx, y + dy, z + dz]], vorgabe


def test_M1_der_ganze_kamerasatz_ist_ohne_verdeckung_feld_fuer_feld_die_basis():
    """**Der Fehler der ersten Fassung** (G-A0306, M1): Eine Variable überschrieb die
    Geländehöhe, und der Kamerasatz gab ``gelaende_z`` als Text aus, sobald eine
    Sichtprüfung mitlief und eine Kamera festen Abstand, einen Ausschnitt oder einen
    gescheiterten Eckentest hatte. Die alte Probe verglich nur die Kameras.

    Jetzt über den GANZEN Satz, an 2000 Zufallsaufrufen mit einer Sichtprüfung, die nichts
    verdeckt: jedes Feld gleich der Basis; dazu kommen genau ``verdeckt``, ``sichtfehler``
    und je Kamera ``sicht``."""
    r = random.Random(4711)
    arten = {"fest": 0, "ausschnitt": 0, "unvollstaendig": 0}
    im_grundriss = 0
    for _ in range(2000):
        bbox, vorgabe = _zufallssatz(r)
        basis = kameras.kamerasatz(bbox, **vorgabe)
        mit = kameras.kamerasatz(bbox, sicht_frei=lambda auge, punkt: True, **vorgabe)
        assert mit.pop("verdeckt") == [] and mit.pop("sichtfehler") == []
        for kamera in mit["kameras"]:
            sicht = kamera.pop("sicht")
            assert not sicht["bewegt"]
            if kameras.sichtpunkte(bbox, kamera["auge"]):
                assert sicht["frei"] is True and sicht["urteil"] == "frei"
            else:
                # Ein bestellter Abstand kann die Kamera in den Grundriss stellen: Dann
                # ist ihr keine Fläche zugewandt, und es gibt nichts zu prüfen.
                im_grundriss += 1
                assert sicht["frei"] is None and sicht["abbruch"] == "nicht_pruefbar"
        assert mit == basis, (bbox, vorgabe)
        assert isinstance(mit["gelaende_z"], float) and math.isfinite(mit["gelaende_z"])
        arten["fest"] += basis["abstand_fest_m"] is not None
        arten["ausschnitt"] += any(k["ausschnitt"] for k in basis["kameras"])
        arten["unvollstaendig"] += bool(basis["unvollstaendig"])
    # Die drei Wege, auf denen der Fehler lag, sind in der Stichprobe wirklich drin.
    assert arten["fest"] > 100 and arten["ausschnitt"] > 100 and arten["unvollstaendig"] > 20, arten
    assert im_grundriss < 150, im_grundriss


@pytest.mark.parametrize("vorgabe", [{"abstand_fest_m": 30.0}, {"ausschnitt": True}, {}],
                         ids=["fest", "ausschnitt", "frei-gerechnet"])
def test_M1_gelaende_z_bleibt_eine_zahl_auch_wenn_verdeckt_ist(vorgabe):
    """Die drei Aufrufe aus der Gegenlese-Meldung, diesmal MIT einer Wand davor."""
    haus = [[0.0, 0.0, 0.0], [120.0, 10.0, 6.0]] if vorgabe.get("ausschnitt") else \
        [[0.0, 0.0, 0.0], [12.0, 10.0, 9.0]]
    basis = kameras.kamerasatz(haus, kuerzel=["s"], **vorgabe)
    wand = sichtstrahl.quader(((haus[1][0]) / 2.0, basis["kameras"][0]["auge"][1] / 2.0),
                              400.0, 0.5, 30.0)
    mit = kameras.kamerasatz(haus, kuerzel=["s"], sicht_frei=sichtstrahl.pruefer([wand]),
                             **vorgabe)
    assert mit["gelaende_z"] == basis["gelaende_z"] == 0.0
    assert mit["verdeckt"] == ["s"]
    for schluessel in basis:
        if schluessel not in ("kameras", "warnungen"):
            assert mit[schluessel] == basis[schluessel], schluessel


def test_ohne_sichtpruefung_ist_der_satz_schluessel_fuer_schluessel_der_alte():
    satz = kameras.kamerasatz(HAUS)
    assert "verdeckt" not in satz and "sichtfehler" not in satz
    assert all("sicht" not in k for k in satz["kameras"])


def test_die_herangezogene_kamera_bleibt_auf_ihrem_weg(neu):
    """Näher, weiteres Objektiv, sonst nichts: gleiche Augenhöhe, gleiche Blickrichtung,
    gleiches Blickziel, Brennweite zwischen 24 mm und der bestellten."""
    for fall, urteil in neu["einzeln"]:
        kamera, basis = urteil["kamera"], urteil["basis"]
        if not kamera["sicht"]["bewegt"]:
            continue
        wo = (fall["szene"]["name"], fall["kuerzel"])
        assert kamera["sicht"]["abbruch"] == "herangezogen", wo
        assert kamera["auge"][2] == basis["auge"][2], wo
        assert kamera["blick_auf"][:2] == basis["blick_auf"][:2], wo
        assert kameras.MIN_ZIEH_ABSTAND_M <= kamera["abstand_m"] < basis["abstand_m"], wo
        assert kameras.ZIEH_BRENNWEITE_MIN_MM <= kamera["brennweite_mm"] <= basis["brennweite_mm"], wo
        vorher = [basis["auge"][i] - basis["blick_auf"][i] for i in range(2)]
        nachher = [kamera["auge"][i] - kamera["blick_auf"][i] for i in range(2)]
        kreuz = vorher[0] * nachher[1] - vorher[1] * nachher[0]
        assert abs(kreuz) < 1e-6 * basis["abstand_m"] ** 2, wo
        assert kamera["vollstaendig"] and kamera["fuellgrad"] >= kameras.BILDBREITE_ABBRUCH, wo
        assert kamera["begruendung"].startswith("HERANGEZOGEN"), wo
        assert kamera["sicht"]["vorher"]["verdeckt_anteil"] > kameras.SICHT_GERINGFUEGIG, wo


def test_die_feinsuche_findet_was_die_groben_schritte_ueberspringen(neu):
    fein = [u for _f, u in neu["einzeln"]
            if u["kamera"]["sicht"]["bewegt"] and u["kamera"]["sicht"]["feinsuche"]]
    assert fein, "Kein Fall im Satz braucht die Feinsuche; der Satz prüft sie nicht mehr."
    assert all(u["frei"] and u["gerahmt"] for u in fein)


def test_so_wenig_heran_wie_noetig():
    """Der grobe Schritt landet oft weiter vorn als nötig. Nach ihm wird der fernste freie
    Standpunkt gesucht: Die Kamera steht knapp vor dem Hindernis, nicht einen ganzen
    12-%-Schritt weiter, und das Haus füllt das Bild wie vorher."""
    basis = kameras.kamerasatz(HAUS, kuerzel=["s"])["kameras"][0]
    schuppen = sichtstrahl.quader((basis["auge"][0], basis["auge"][1] + 5.0), 6.0, 4.0, 8.0)
    kamera = kameras.kamerasatz(HAUS, kuerzel=["s"],
                                sicht_frei=sichtstrahl.pruefer([schuppen]))["kameras"][0]
    naeher = kamera["auge"][1] - basis["auge"][1]
    assert 7.0 < naeher < 7.0 + 3 * kameras.ZIEH_FEINSCHRITT_M + 0.02, naeher
    assert kamera["fuellgrad"] == pytest.approx(basis["fuellgrad"], abs=1e-6)
    assert sichtmass.verdeckter_anteil(kamera["auge"], HAUS, [schuppen]) == 0.0


# --------------------------------------------------------------------------------------
# M3: bei jedem Fehler zurück auf die unbewegte Kamera
# --------------------------------------------------------------------------------------

class _Kaputt(RuntimeError):
    pass


def _wirft(nach: int):
    zaehler = {"n": 0}

    def _pruefe(auge, punkt):
        zaehler["n"] += 1
        if zaehler["n"] > nach:
            raise _Kaputt("Strahlenschuss ausgefallen")
        return {"frei": False, "objekt": "wand"}

    return _pruefe


@pytest.mark.parametrize("nach", [0, 1, 500, 1500, 3000])
def test_M3_ein_fehler_der_sichtpruefung_bricht_nichts_ab(nach):
    """**Erzwungener Fehler.** Die Sichtprüfung wirft sofort, nach dem ersten Strahl,
    mitten in der Messung am Standort oder erst mitten im Heranziehen. In jedem Fall kommt
    der Kamerasatz der Basis zurück, Feld für Feld, und sagt, dass nicht geprüft wurde."""
    basis = kameras.kamerasatz(HAUS, kuerzel=["s", "nNE"])
    mit = kameras.kamerasatz(HAUS, kuerzel=["s", "nNE"], sicht_frei=_wirft(nach))
    assert len(mit["sichtfehler"]) >= 1 and mit["verdeckt"] in ([], ["s"])
    fehler = 0
    for kamera, alt in zip(mit["kameras"], basis["kameras"]):
        sicht = kamera["sicht"]
        assert not sicht["bewegt"]
        assert kamera["auge"] == alt["auge"] and kamera["brennweite_mm"] == alt["brennweite_mm"]
        if sicht["abbruch"] != "fehler":
            continue
        fehler += 1
        assert sicht["frei"] is None and sicht["urteil"] == "nicht_pruefbar"
        assert sicht["vermerk"].startswith("Sicht NICHT GEPRÜFT")
        assert "_Kaputt: Strahlenschuss ausgefallen" in sicht["vermerk"]
        assert kamera["warnungen"] == alt["warnungen"] + (sicht["vermerk"],)
        ohne = {k: v for k, v in kamera.items() if k not in ("sicht", "warnungen")}
        assert ohne == {k: v for k, v in alt.items() if k != "warnungen"}
    assert fehler >= 1 and len(mit["sichtfehler"]) == fehler
    for schluessel in basis:
        if schluessel not in ("kameras", "warnungen"):
            assert mit[schluessel] == basis[schluessel], schluessel


def test_M3_auch_ein_fehler_in_der_eigenen_rechnung_faellt_zurueck(monkeypatch):
    """Nicht nur die Prüfung von aussen: Steigt ``freie_sicht_mit_rahmung`` selbst aus,
    bleibt die Kamera die der Basis."""
    def _kaputt(*_a, **_k):
        raise ZeroDivisionError("Rechenfehler im Heranziehen")

    monkeypatch.setattr(kameras, "freie_sicht_mit_rahmung", _kaputt)
    basis = kameras.kamerasatz(HAUS, kuerzel=["s"])
    mit = kameras.kamerasatz(HAUS, kuerzel=["s"], sicht_frei=sichtstrahl.pruefer([]))
    assert "ZeroDivisionError" in mit["sichtfehler"][0]
    assert mit["kameras"][0]["auge"] == basis["kameras"][0]["auge"]
    assert mit["gelaende_z"] == basis["gelaende_z"]


def test_M3_eine_unbrauchbare_eingabe_bleibt_ein_fehler_des_aufrufers():
    """Der Rückfall gilt der Sichtprüfung, nicht dem Aufruf: Eine unlesbare Hüllbox wird
    abgewiesen wie immer."""
    with pytest.raises(ValueError):
        kameras.kamerasatz([[0, 0, 0], [1, 1, float("nan")]], sicht_frei=lambda a, p: True)


# --------------------------------------------------------------------------------------
# M5: die Warnung zur Brennweite
# --------------------------------------------------------------------------------------

def test_M5_mehr_als_15_prozent_kuerzer_steht_in_den_warnungen(neu):
    """Rückt die Kamera so weit heran, dass die Brennweite mehr als 15 % unter der
    bestellten liegt, trägt die Kamera eine Warnung mit beiden Zahlen. Darüber nicht."""
    mit = ohne = 0
    for fall, urteil in neu["einzeln"]:
        kamera, basis = urteil["kamera"], urteil["basis"]
        gewarnt = [w for w in kamera["warnungen"] if w.startswith("Brennweite ")]
        if kamera["brennweite_mm"] < basis["brennweite_mm"] * 0.85:
            mit += 1
            assert len(gewarnt) == 1, (fall["szene"]["name"], fall["kuerzel"])
            assert gewarnt[0].startswith(
                f"Brennweite {kamera['brennweite_mm']:.1f} statt bestellt 35 mm")
        else:
            ohne += kamera["sicht"]["bewegt"]
            assert not gewarnt
    assert mit >= 20 and ohne >= 5, (mit, ohne)


@pytest.mark.parametrize("anteil", [0.80, 0.84, 0.849, 0.851, 0.86, 0.90])
def test_M5_die_schwelle_von_beiden_seiten(anteil, monkeypatch):
    """Die Brennweite der herangezogenen Kamera knapp unter und knapp über 85 % der
    bestellten: Die Warnung kippt genau dort."""
    echt = kameras.freie_sicht_mit_rahmung

    def _mit_fester_brennweite(*a, **k):
        antwort = echt(*a, **k)
        return dict(antwort, brennweite_mm=35.0 * anteil) if antwort["bewegt"] else antwort

    monkeypatch.setattr(kameras, "freie_sicht_mit_rahmung", _mit_fester_brennweite)
    basis = kameras.kamerasatz(HAUS, kuerzel=["s"])["kameras"][0]
    schuppen = sichtstrahl.quader((basis["auge"][0], basis["auge"][1] + 5.0), 6.0, 4.0, 8.0)
    kamera = kameras.kamerasatz(HAUS, kuerzel=["s"],
                                sicht_frei=sichtstrahl.pruefer([schuppen]))["kameras"][0]
    assert kamera["sicht"]["bewegt"]
    assert any(w.startswith("Brennweite ") for w in kamera["warnungen"]) == (anteil < 0.85)


# --------------------------------------------------------------------------------------
# Einzelfälle zum Nachrechnen
# --------------------------------------------------------------------------------------

def test_fester_abstand_wird_gemeldet_aber_nie_bewegt():
    mauer = sichtstrahl.quader((7.0, 30.0), 60.0, 4.0, 12.0, name="riegel")
    ohne = kameras.kamerasatz(HAUS, kuerzel=["n"], abstand_fest_m=45.0)["kameras"][0]
    mit = kameras.kamerasatz(HAUS, kuerzel=["n"], abstand_fest_m=45.0,
                             sicht_frei=sichtstrahl.pruefer([mauer]))
    kamera = mit["kameras"][0]
    assert kamera["auge"] == ohne["auge"] and kamera["brennweite_mm"] == ohne["brennweite_mm"]
    assert kamera["sicht"]["frei"] is False and kamera["sicht"]["bewegt"] is False
    assert kamera["sicht"]["abbruch"] == "nicht_nachgefuehrt"
    assert kamera["sicht"]["vermerk"].startswith("verdeckt, 100,0 %")
    assert "Abstand ist bestellt" in kamera["sicht"]["vermerk"]
    assert kamera["sicht"]["vorher"]["verdeckt_durch"] == "riegel"
    assert mit["verdeckt"] == ["n"]


def test_bestellt_mit_24_mm_gibt_es_kein_weiteres_objektiv():
    basis = kameras.kamerasatz(HAUS, kuerzel=["s"], brennweite_mm=24.0)["kameras"][0]
    weit_vorn = sichtstrahl.quader((basis["auge"][0], basis["auge"][1] + 10.0), 8.0, 4.0, 8.0)
    kamera = kameras.kamerasatz(HAUS, kuerzel=["s"], brennweite_mm=24.0,
                                sicht_frei=sichtstrahl.pruefer([weit_vorn]))["kameras"][0]
    assert kamera["brennweite_mm"] == 24.0
    assert kamera["sicht"]["frei"] is False
    assert kamera["sicht"]["abbruch"] == "kein_freier_standpunkt"


@pytest.mark.parametrize("vorgabe", [{"modus": kameras.MODUS_GEKIPPT},
                                     {"brennweite_mm": 50.0, "seitenverhaeltnis": 1.0}],
                         ids=["gekippt", "50mm-quadratisch"])
def test_die_regel_haelt_auch_mit_anderer_kamera(vorgabe):
    """Der Satz ist mit der Vorgabe-Kamera gebaut (Shift, 35 mm, 16:9). Eine Stichprobe
    mit gekippter Kamera und mit 50 mm im Quadrat: dieselben Zusagen."""
    bewegt = 0
    for fall in sz.faelle()[::6]:
        urteil = sz.beurteile(fall, sz.mit_sichtpruefung(fall, vorgabe), vorgabe=vorgabe)
        wo = (fall["szene"]["name"], fall["kuerzel"])
        assert not urteil["verstoss"], wo
        if urteil["kamera"]["sicht"]["bewegt"]:
            bewegt += 1
            assert urteil["frei"] and urteil["gerahmt"], wo
        else:
            assert urteil["kamera"]["auge"] == urteil["basis"]["auge"], wo
        if urteil["klasse"] == "loesbar":
            assert urteil["erreicht"], wo
    assert bewegt >= 4, "Die Stichprobe enthält kaum noch bewegte Fälle."


# --------------------------------------------------------------------------------------
# Die Sichtprüfung ist austauschbar
# --------------------------------------------------------------------------------------

def test_die_sichtpruefung_darf_wahrheitswert_oder_runnerantwort_liefern():
    basis = kameras.kamerasatz(HAUS, kuerzel=["s"])["kameras"][0]
    schuppen = [sichtstrahl.quader((basis["auge"][0], basis["auge"][1] + 5.0), 6.0, 4.0, 8.0)]
    als_antwort = kameras.kamerasatz(HAUS, kuerzel=["s"],
                                     sicht_frei=sichtstrahl.pruefer(schuppen))["kameras"][0]
    als_bool = kameras.kamerasatz(
        HAUS, kuerzel=["s"],
        sicht_frei=lambda a, p: sichtstrahl.sicht_frei(a, p, schuppen)["frei"])["kameras"][0]
    assert als_bool["auge"] == als_antwort["auge"]
    assert als_bool["brennweite_mm"] == als_antwort["brennweite_mm"]


def test_nicht_gemessen_ist_nicht_frei_und_nicht_verdeckt():
    kamera = kameras.kamerasatz(HAUS, kuerzel=["s"],
                                sicht_frei=lambda a, p: {"frei": None})["kameras"][0]
    assert kamera["sicht"]["frei"] is None and kamera["sicht"]["urteil"] == "nicht_pruefbar"
    assert kamera["sicht"]["abbruch"] == "nicht_pruefbar" and not kamera["sicht"]["bewegt"]
    assert "NICHT GEPRÜFT" in kamera["sicht"]["vermerk"]


def test_sichtpunkte_liegen_dicht_bis_an_kante_und_fuss():
    """Alle 25 cm eine Spalte, alle 50 cm eine Zeile, die äussersten einen Millimeter von
    Kante und Fuss; dazu drei Mastzeilen mit einem Punkt alle 5 cm. Das ist die Antwort auf
    M2: Das alte Raster (5 mal 3, ohne Ränder) liess einen Streifen an der Hauskante und
    einen Mast zwischen zwei Punkten durch."""
    frontal = kameras.sichtpunkte(HAUS, (7.0, -30.0, 1.7))
    assert all(p[1] == 0.0 for p in frontal)
    assert len(frontal) == 57 * 19 + 3 * 281
    xs, zs = sorted({p[0] for p in frontal}), sorted({p[2] for p in frontal})
    assert xs[0] == pytest.approx(0.001) and xs[-1] == pytest.approx(13.999)
    assert zs[0] == pytest.approx(0.001) and zs[-1] == pytest.approx(8.999)
    assert max(b - a for a, b in zip(zs, zs[1:])) <= kameras.SICHTRASTER_ZEILE_M
    for anteil in kameras.SICHTRASTER_MASTZEILEN:
        zeile = sorted(p[0] for p in frontal if p[2] == 9.0 * anteil)
        assert len(zeile) >= 281
        assert max(b - a for a, b in zip(zeile, zeile[1:])) <= kameras.SICHTRASTER_MAST_M
    raster = sorted({p[0] for p in frontal if p[2] == zs[0]})
    assert len(raster) == 57
    assert max(b - a for a, b in zip(raster, raster[1:])) <= kameras.SICHTRASTER_SPALTE_M
    ueber_eck = kameras.sichtpunkte(HAUS, (40.0, -30.0, 1.7))
    assert all(p[0] == 14.0 or p[1] == 0.0 for p in ueber_eck)
    assert len(ueber_eck) == len(frontal) + 41 * 19 + 3 * 201
    assert any(p[2] == 9.0 for p in kameras.sichtpunkte(HAUS, (40.0, -30.0, 30.0)))
    assert kameras.sichtpunkte(HAUS, (7.0, 5.0, 4.0)) == []
    # Auch ein kleiner Bau bekommt das Mindestraster, ein riesiger nicht unendlich viele.
    assert len(kameras.sichtpunkte([[0, 0, 0], [2, 2, 2]], (1.0, -9.0, 1.7))) >= 21 * 11
    assert len(kameras.sichtpunkte([[0, 0, 0], [400, 9, 300]], (1.0, -9.0, 1.7))) \
        <= 161 * 81 + 3 * kameras.SICHTRASTER_MAST_HOECHSTENS


def test_die_reihenfolge_der_sichtpunkte_aendert_kein_urteil():
    """Grob vor fein ist nur schneller. Jeder Punkt kommt genau einmal vor."""
    punkte = kameras.sichtpunkte(HAUS, (40.0, -30.0, 1.7))
    assert len(set(punkte)) == len(punkte)
    assert kameras.sichtpunkte(HAUS, (41.0, -35.0, 1.7)) == punkte


def test_fuellgrad_waechst_gleichmaessig_und_der_eckentest_kippt_nur_einmal():
    """Zwei Eigenschaften, auf die das Heranziehen baut, an Zufallsstellungen nachgemessen:
    Der Füllgrad ist der Brennweite verhältnisgleich, und der Eckentest geht mit kürzerer
    Brennweite nie verloren."""
    r = random.Random(306)
    for _ in range(200):
        haus = [[0.0, 0.0, 0.0], [r.uniform(8, 24), r.uniform(8, 18), r.uniform(6, 18)]]
        basis = kameras.kamerasatz(haus, kuerzel=[r.choice(sz.RICHTUNGEN)])["kameras"][0]
        ziel = sichtmass.angehobenes_ziel(basis)
        anteil = r.uniform(0.45, 1.0)
        ort = tuple(ziel[i] + (basis["auge"][i] - ziel[i]) * anteil for i in range(2)) \
            + (basis["auge"][2],)
        lagen = [kameras.rahmung_am_standpunkt(ort, ziel, haus, brennweite_mm=f,
                                               azimut_grad=basis["azimut_grad"])
                 for f in (24.0, 28.0, 32.0, 35.0)]
        for lage, f in zip(lagen, (24.0, 28.0, 32.0, 35.0)):
            assert math.isclose(lage["fuellgrad"] / f, lagen[0]["fuellgrad"] / 24.0, rel_tol=1e-9)
        passt = [lage["ecken_passt"] for lage in lagen]
        assert passt == sorted(passt, reverse=True), passt


# --------------------------------------------------------------------------------------
# Die Aufrufstelle im Runner (läuft nur in Blender; geprüft wird die Quelle)
# --------------------------------------------------------------------------------------

def _runner_ohne_kommentare() -> str:
    return "\n".join(z.split("#")[0] for z in RUNNER.read_text(encoding="utf-8").splitlines())


def test_der_runner_reicht_den_strahlenschuss_nur_mit_schalter_herein():
    """Ohne ``AIIMAGING_FREIE_SICHT=1`` ändert sich an keinem Lauf etwas: Die Regel ist an
    erfundenen Szenen gemessen, am echten Bestand noch nicht."""
    quelle = _runner_ohne_kommentare()
    treffer = re.findall(r'\*\*\(\{"sicht_frei": _sicht_frei\}\s+'
                         r'if os\.environ\.get\("AIIMAGING_FREIE_SICHT"\) == "1" else \{\}\)',
                         quelle)
    assert len(treffer) == 1
    assert quelle.count("sicht_frei=") == 0, "Die Sichtprüfung darf nur über den Schalter kommen."


def test_der_runner_stellt_die_brennweite_der_herangezogenen_kamera():
    quelle = _runner_ohne_kommentare()
    assert re.search(r'if \(k\.get\("sicht"\) or \{\}\)\.get\("bewegt"\):\s+'
                     r'brennweite = k\["brennweite_mm"\]', quelle)
    assert '"sicht": k.get("sicht"),' in quelle


def test_der_runner_rechnet_nach_dem_kamerasatz_nur_mit_zahlen():
    """Die Zeile, an der die erste Fassung am Gerät abgebrochen wäre (M1): Der Runner zieht
    ``satz["gelaende_z"]`` von einer Höhe ab. Hier wird genau diese Rechnung mit dem
    Kamerasatz gemacht, den er mit Schalter bekäme, auf allen drei alten Fehlerwegen."""
    quelle = _runner_ohne_kommentare()
    assert 'satz["mitte"][2] + satz["masse_m"][2] / 2.0 - satz["gelaende_z"]' in quelle
    for haus, vorgabe in (([[0, 0, 0], [12, 10, 9]], {"abstand_fest_m": 30.0}),
                          ([[0, 0, 0], [120, 10, 6]], {"ausschnitt": True}),
                          ([[0, 0, 0], [12, 10, 9]], {})):
        satz = kameras.kamerasatz(haus, kuerzel=["s"], sicht_frei=sichtstrahl.pruefer([]),
                                  **vorgabe)
        assert round(satz["mitte"][2] + satz["masse_m"][2] / 2.0 - satz["gelaende_z"], 4) > 0.0


def test_die_antwort_des_runners_und_des_strahlentests_haben_dieselben_felder():
    quelle = RUNNER.read_text(encoding="utf-8")
    anfang = quelle.index("def _sicht_frei(")
    rumpf = quelle[anfang:quelle.index("\ndef ", anfang + 10)]
    antwort = sichtstrahl.sicht_frei((0, 0, 0), (10, 0, 0), [])
    for feld in antwort:
        assert f'"{feld}"' in rumpf, feld
