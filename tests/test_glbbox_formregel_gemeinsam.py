"""A0289 «Gelände an der Form», Runde 2: Schutz des Hauses geht vor Abtrennen.

Der Massstab ist ``aiimaging.gelaendeform`` in ihrem Einsatz in ``glbbox.bauwerksbox`` (die
Zweitmeinung: sie spricht nur, wenn die Namensregel schweigt, und kennt «nicht entscheidbar»). Seit
Runde 2 machen die Merkmale der Hüllbox einen Körper nur zum Kandidaten; Gelände wird er erst mit dem
Beweis an seinen Dreiecken (``gelaendeform.beweis``). Der Mac bildet das in
``ipad/Visbox.swiftpm/Kern/Gelaendeform.swift`` ab.

Beide Seiten lesen dieselbe Probendatei (``tests/daten/glbbox_gelaenderegel.json``, Schlüssel
``formfaelle``, erzeugt von ``tools/glbbox_proben.py``). ``erwartet`` ist die Entscheidung des
Heim-PC; diese Datei prüft, dass sie noch stimmt und dass eine Regeländerung ohne neu erzeugte Datei
rot wird. Die Swift-Probe ``GelaendeformTests`` verlangt in JEDEM Fall dasselbe (Gleichstand 100 %).

**Die Zielfunktion der Runde 2:**

* mindestens 80 Gegenfälle (Tiefgarage, Sockel, Halle, Bodenplatte, namenlos und gleichnamig): in
  KEINEM wird ein Bauwerk oder Bauwerksteil als Gelände entfernt, die Hülle umfasst alles Gebaute;
* mindestens 40 Fälle mit echtem Gelände ohne Namen: mindestens 80 % abgetrennt; eine ebene,
  waagrechte Fläche zählt als richtig, wenn sie als «nicht entscheidbar» gemeldet ist;
* jede Schwelle der Regel ist von beiden Seiten dicht besetzt;
* Zufallsvergleich an mindestens 5000 Modellen: ``tests/test_glbbox_formregel_zufall.py``.
"""
from __future__ import annotations

import collections
import importlib.util
import json
import math
import re
from pathlib import Path

import pytest

from aiimaging import gelaendeform, glbbox, maske

WURZEL = Path(__file__).resolve().parents[1]
DATEI = WURZEL / "tests" / "daten" / "glbbox_gelaenderegel.json"
SWIFT_FORM = WURZEL / "ipad" / "Visbox.swiftpm" / "Kern" / "Gelaendeform.swift"
SWIFT_BOX = WURZEL / "ipad" / "Visbox.swiftpm" / "Kern" / "Modelltausch.swift"
SWIFT_PROBE = WURZEL / "ipad" / "VisboxKern" / "Tests" / "VisboxKernTests" / "GelaendeformTests.swift"


def _werkzeug():
    spez = importlib.util.spec_from_file_location("glbbox_proben", WURZEL / "tools" / "glbbox_proben.py")
    modul = importlib.util.module_from_spec(spez)
    spez.loader.exec_module(modul)
    return modul


DATEN = json.loads(DATEI.read_text(encoding="utf-8"))
FORMFAELLE = DATEN["formfaelle"]
NACH_NAME = {f["fall"]: f for f in FORMFAELLE}
IDS = [f["fall"] for f in FORMFAELLE]
GEGEN = [f for f in FORMFAELLE if f["gruppe"] == "gegenfall"]
GELAENDE = [f for f in FORMFAELLE if f["gruppe"] == "gelaende"]


def _pfad(fall, tmp_path):
    p = tmp_path / "probe.glb"
    _werkzeug().schreibe_glb(fall["glb"], p, bool(fall.get("binaerblock")))
    return p


def _bauwerksbox(fall, tmp_path):
    return glbbox.bauwerksbox(_pfad(fall, tmp_path))


def _abgetrennte_stellen(aus):
    if aus["entschieden_durch"] != "form":
        return set()
    return set(aus["form_befund"]["gelaende_stellen"])


def _ganz_abgetrennt(fall):
    """Die Form hat entschieden und genau die Körper abgetrennt, die in Wahrheit Gelände sind."""
    e = fall["erwartet"]
    return (e["entschieden_durch"] == "form"
            and set(e["gelaende_stellen"]) == set(fall["wahrheit"]["gelaende_stellen"]))


# ---------------------------------------------------------------- die Probendatei


def test_die_probendatei_traegt_die_verlangten_familien():
    gruppen = collections.Counter(f["gruppe"] for f in FORMFAELLE)
    assert set(gruppen) == {"gegenfall", "gelaende", "hang", "schwelle", "namen", "gemischt", "beschaedigt"}
    assert gruppen["gegenfall"] >= 250, "Runde 3 verlangt mindestens 250 Gegenfälle"
    assert gruppen["hang"] >= 40
    assert gruppen["gegenfall"] >= 80, "der Auftrag verlangt mindestens 80 Gegenfälle"
    assert gruppen["gelaende"] >= 40, "der Auftrag verlangt mindestens 40 Geländefälle"
    assert len(IDS) == len(set(IDS)), "Fallnamen doppelt"
    familien = collections.Counter(f["familie"] for f in GEGEN)
    # Die Pflichtfamilien der Steuerung, je mit Streuung.
    assert familien["tiefgarage"] == 20, "ein bis zehn Geschosse, ein und zwei Untergeschosse"
    assert familien["sockel"] == 18, "ein bis drei Sockelgeschosse unter Turm und Zeile"
    assert familien["halle"] == 25, "4 bis 12 m, mit Kamin, Silo, Dachaufbau, Satteldach"
    assert familien["bodenplatte"] >= 18, "Überstand 0 bis 4 m"
    assert familien["namen"] >= 9, "namenlos, gleichnamig, leerer Name"
    assert familien["gebogen"] >= 18, "Schale, Zelt, Tonnenhalle, Freiform-Vordach, Erdhaus, Brücke"
    assert familien["durchstossen"] >= 8, "Turm aus der Schale, Kamin durch das Tonnendach, Zelt mit Turm"
    # Runde 3: gewölbt, gewellt, geneigt und gebaut, je mit etwas Höherem darauf.
    for familie, mindestens in (("kuppel", 40), ("stadion", 20), ("wellendach", 30), ("podium", 15), ("skatepark", 10),
                                ("gruendach", 20), ("rampe", 10), ("tribuene", 10), ("erdhaus", 10)):
        assert familien[familie] >= mindestens, familie
    pflicht = sum(familien[f] for f in ("kuppel", "stadion", "wellendach", "podium", "skatepark", "gruendach", "rampe",
                                        "tribuene", "erdhaus"))
    assert pflicht >= 250, f"Runde 3 verlangt in diesen neun Familien zusammen mindestens 250 Gegenfälle, es sind {pflicht}"
    for stichwort in ("hang", "mulde", "terrasse", "uneben", "unter-dem-haus", "neben-dem-haus", "eben"):
        assert any(f["familie"] == stichwort for f in GELAENDE), stichwort


def test_kein_formfall_traegt_einen_gelaendenamen():
    """«Ohne erkennbaren Namen»: nur die Gruppe ``namen`` prüft Namen und Form zusammen."""
    mit_namen = {f["gruppe"] for f in FORMFAELLE
                 if any(maske.ist_gelaende(k.get("name", "")) for k in f["glb"]["nodes"])}
    assert mit_namen == {"namen"}


def test_die_wahrheit_der_gegenfaelle_ist_kein_gelaende():
    assert all(f["wahrheit"]["gelaende_stellen"] == [] for f in GEGEN)
    assert all(f["wahrheit"]["gelaende_stellen"] for f in GELAENDE)


@pytest.mark.parametrize("fall", FORMFAELLE, ids=IDS)
def test_der_heim_pc_entscheidet_wie_in_der_probendatei(fall, tmp_path):
    aus = _bauwerksbox(fall, tmp_path)
    soll = fall["erwartet"]
    assert aus["entschieden_durch"] == soll["entschieden_durch"]
    assert aus["n_gelaende"] == soll["gelaendeKnoten"]
    assert aus["n_knoten"] == soll["bauteile"]
    assert (aus["bbox_bauwerk"] is not None and aus["n_gelaende"] > 0) == soll["abgetrennt"]
    for ist_e, soll_e in zip(aus["bbox_szene"], soll["szenenbox"]):
        assert ist_e == pytest.approx(soll_e, abs=DATEN["toleranz_m"])
    box = aus["bbox_bauwerk"] if aus["bbox_bauwerk"] is not None else aus["bbox_szene"]
    for ist_e, soll_e in zip(box, soll["huellbox"]):
        assert ist_e == pytest.approx(soll_e, abs=DATEN["toleranz_m"])
    assert (aus["form_befund"] is not None) == soll["form_gefragt"]
    befund = aus["form_befund"] or {}
    assert len(befund.get("gelaende_stellen") or ()) == soll["form_gelaende"]
    assert len(befund.get("unklar_stellen") or ()) == soll["form_unklar"]
    assert list(befund.get("gruende") or ()) == soll["form_gruende"]
    if soll["entschieden_durch"] == "form":
        assert sorted(_abgetrennte_stellen(aus)) == soll["gelaende_stellen"]


# ---------------------------------------------------------------- Schutz des Hauses


@pytest.mark.parametrize("fall", FORMFAELLE, ids=IDS)
def test_nie_wird_ein_bauwerk_als_gelaende_entfernt(fall, tmp_path):
    """In KEINEM Fall der Datei, gleich welcher Gruppe: Was abgetrennt wird, ist in Wahrheit Gelände,
    die Hülle ist endlich und nicht leer, und sie umfasst jeden Körper, der gebaut ist."""
    pfad = _pfad(fall, tmp_path)
    aus = glbbox.bauwerksbox(pfad)
    wahr = set(fall["wahrheit"]["gelaende_stellen"])
    if fall["gruppe"] != "namen":
        assert _abgetrennte_stellen(aus) <= wahr, "ein gebauter Körper wurde als Gelände abgetrennt"
    box = aus["bbox_bauwerk"] if aus["bbox_bauwerk"] is not None else aus["bbox_szene"]
    assert all(math.isfinite(v) for e in box for v in e), "die Hülle ist nicht endlich"
    assert box[1][0] > box[0][0] and box[1][1] > box[0][1] and box[1][2] >= box[0][2], "leere Hülle"
    toleranz = DATEN["toleranz_m"]
    for stelle, (_name, lo, hi) in enumerate(glbbox.knotenboxen(glbbox.lies_gltf_json(pfad))["knoten"]):
        if stelle in wahr:
            continue
        wlo, whi = glbbox.nach_welt(lo, hi)
        assert all(box[0][i] - toleranz <= wlo[i] and whi[i] <= box[1][i] + toleranz for i in range(3)), (
            f"der gebaute Körper an Stelle {stelle} liegt ausserhalb der Hülle")


@pytest.mark.parametrize("fall", GEGEN, ids=[f["fall"] for f in GEGEN])
def test_gegenfaelle_behalten_die_ganze_szene(fall, tmp_path):
    """Tiefgarage, Sockel, Halle, Bodenplatte, namenlos: nichts wird abgetrennt, die Hülle ist die Szene."""
    aus = _bauwerksbox(fall, tmp_path)
    assert aus["entschieden_durch"] == "keine"
    assert aus["n_gelaende"] == 0
    assert aus["bbox_bauwerk"] == aus["bbox_szene"]
    assert all(math.isfinite(v) for e in aus["bbox_bauwerk"] for v in e)


def test_die_pflichtfaelle_des_gegenlesens_im_wortlaut(tmp_path):
    """G1, G2, G5, G10 und Befund 1 aus der Meldung des Gegenlesens, mit deren Massen nachgebaut."""
    w = _werkzeug()

    def box(b):
        p = tmp_path / "g.glb"
        w.schreibe_glb(b.kopf(), p)
        return glbbox.bauwerksbox(p)

    # G1: Tiefgarage 60 x 50 m, 3 m tief, Decke 0,4 m, darauf ein Haus 12 x 10 x 14 m.
    b = w._Bau()
    b.quader("Garagenwaende", (-30, -3, -25), (30, 0, 25))
    b.quader("Decke", (-30, 0, -25), (30, 0.4, 25))
    b.quader("Haus", (-6, 0.4, -5), (6, 14.4, 5))
    aus = box(b)
    assert aus["entschieden_durch"] == "keine" and aus["bbox_bauwerk"] == aus["bbox_szene"]
    assert aus["bbox_bauwerk"][1][0] - aus["bbox_bauwerk"][0][0] == pytest.approx(60.0)

    # G2: Sockel 40 x 30 x 4 m, Turm 12 x 10 x 24 m.
    b = w._Bau()
    b.quader("Sockel", (-20, 0, -15), (20, 4, 15))
    b.quader("Turm", (-6, 4, -5), (6, 28, 5))
    aus = box(b)
    assert aus["entschieden_durch"] == "keine"
    assert aus["bbox_bauwerk"][1][0] - aus["bbox_bauwerk"][0][0] == pytest.approx(40.0)

    # G5: flache Halle 60 x 50 x 6 m mit Kamin 2 x 2 x 25 m: vorher blieb nur der Kamin.
    b = w._Bau()
    b.quader("Halle", (-30, 0, -25), (30, 6, 25))
    b.quader("Kamin", (10, 0, 10), (12, 25, 12))
    aus = box(b)
    assert aus["entschieden_durch"] == "keine"
    assert aus["bbox_bauwerk"][1][0] - aus["bbox_bauwerk"][0][0] == pytest.approx(60.0)
    assert aus["form_befund"]["gruende"] == (gelaendeform.GRUND_EBEN,)

    # G10: Bodenplatte mit 3 m Überstand und Vordach.
    b = w._Bau()
    b.quader("Fundamentplatte", (-9, -0.4, -8), (9, 0, 8))
    b.haus(-6, -5, 12, 10, 9)
    aus = box(b)
    assert aus["entschieden_durch"] == "keine"
    assert aus["bbox_bauwerk"][1][0] - aus["bbox_bauwerk"][0][0] == pytest.approx(18.0)

    # Befund 1: zwei Körper ohne Namen (Platte 60 x 50 x 0,5, Haus 12 x 10 x 9): vorher unendlich.
    b = w._Bau()
    b.quader(None, (-30, -0.5, -25), (30, 0, 25))
    b.quader(None, (-6, 0, -5), (6, 9, 5))
    aus = box(b)
    assert all(math.isfinite(v) for e in aus["bbox_bauwerk"] for v in e)
    assert aus["schrumpfung"] == 0.0


def test_befund_1_getrennt_wird_nach_der_stelle_nicht_nach_dem_namen(tmp_path):
    """Hang und Haus tragen denselben Namen (oder keinen): Der Hang geht, das Haus bleibt GANZ."""
    for name in ("gelaende-namenlos-hang-und-haus", "gelaende-gleichnamig-hang-und-haus",
                 "gelaende-leerer-name-hang-und-haus"):
        fall = NACH_NAME[name]
        aus = _bauwerksbox(fall, tmp_path)
        assert aus["entschieden_durch"] == "form", name
        assert aus["n_gelaende"] == 1 and aus["n_bauwerk"] == 3, name
        (x0, y0, z0), (x1, y1, z1) = aus["bbox_bauwerk"]
        assert (x1 - x0, y1 - y0, z1 - z0) == pytest.approx((12.0, 10.0, 9.0)), name
        assert all(math.isfinite(v) for v in (x0, y0, z0, x1, y1, z1)), name


# ---------------------------------------------------------------- die Zielfunktion


def test_zielfunktion_gegenfaelle_hundert_prozent():
    """Laut Probendatei: in keinem der mindestens 80 Gegenfälle ist etwas abgetrennt."""
    assert len(GEGEN) >= 80
    verloren = [f["fall"] for f in GEGEN
                if f["erwartet"]["abgetrennt"] or f["erwartet"]["gelaendeKnoten"]
                or f["erwartet"]["huellbox"] != f["erwartet"]["szenenbox"]]
    assert verloren == []
    for f in FORMFAELLE:
        if f["gruppe"] != "namen":
            assert set(f["erwartet"]["gelaende_stellen"]) <= set(f["wahrheit"]["gelaende_stellen"]), f["fall"]


HANG = [f for f in FORMFAELLE if f["gruppe"] == "hang"]


def test_zielfunktion_runde_3_haus_am_offenen_hang_mindestens_neunzig_prozent():
    """Die Mindestanforderung der Runde 3: Ein Haus auf geneigtem, unebenem Gelände, das als offene
    Fläche vorliegt und das Haus auf allen Seiten überragt, wird in mindestens 90 % abgetrennt."""
    assert len(HANG) >= 40
    ab = [f for f in HANG if _ganz_abgetrennt(f)]
    print(f"A0289-3 Mindestanforderung: Haus am offenen Hang {len(ab)} von {len(HANG)} abgetrennt "
          f"({len(ab) / len(HANG):.0%})")
    assert len(ab) / len(HANG) >= 0.9
    assert sorted(f["fall"] for f in HANG if not _ganz_abgetrennt(f)) == [
        "hang-offen-05-prozent-diagonal-60x50", "hang-offen-05-prozent-x-60x50",
        "hang-offen-25-prozent-diagonal-40x30"]
    for f in ab:
        (x0, y0, _), (x1, y1, _) = f["erwartet"]["huellbox"]
        assert (x1 - x0, y1 - y0) == pytest.approx((12.0, 10.0)), f["fall"]


def test_abtrennrate_je_art_ausgewiesen():
    """Runde 3: Die Abtrennrate echten Geländes ist kein Zielwert mehr; sie wird je Art ausgewiesen.
    Geschlossene Geländekörper, Mulden und hügeliges Gelände ohne Gefälle im Ganzen bleiben in der
    Hülle (nicht entscheidbar), ebene Flächen ohnehin."""
    je_art = collections.defaultdict(lambda: [0, 0])
    for f in GELAENDE + HANG:
        art = f["familie"]
        if f["familie"] in ("hang", "mulde"):
            art += "-koerper" if f["fall"].endswith("koerper") else "-flaeche"
        je_art[art][1] += 1
        je_art[art][0] += _ganz_abgetrennt(f)
    zeile = ", ".join(f"{art} {ab} von {n}" for art, (ab, n) in sorted(je_art.items()))
    print(f"A0289-3 Abtrennrate je Art: {zeile}")
    assert je_art["hang-flaeche"][0] >= 8, "offene Hänge werden abgetrennt"
    assert je_art["hang-koerper"][0] == 0, "geschlossene Geländekörper bleiben in der Hülle"
    assert je_art["mulde-flaeche"][0] == 0 and je_art["eben"][0] == 0
    for f in GELAENDE:
        if f.get("eben"):
            assert set(f["erwartet"]["form_gruende"]) == {gelaendeform.GRUND_EBEN}, f["fall"]


def test_abgetrenntes_gelaende_macht_die_huelle_wirklich_enger():
    for f in GELAENDE:
        if _ganz_abgetrennt(f):
            e = f["erwartet"]
            assert e["huellbox"] != e["szenenbox"], f["fall"]
    hang = NACH_NAME["gelaende-hang-10-prozent-laengs-x-flaeche"]["erwartet"]
    assert hang["entschieden_durch"] == "form"
    (x0, y0, _), (x1, y1, _) = hang["huellbox"]
    assert (x1 - x0, y1 - y0) == pytest.approx((12.0, 10.0))


# ---------------------------------------------------------------- die Schwellen


SCHWELLEN = [
    (gelaendeform, "GRUNDRISSANTEIL_MIN", 0.24), (gelaendeform, "GRUNDRISSANTEIL_MIN", 0.26),
    (gelaendeform, "FLACHHEIT_BEWIESEN_MAX", 0.39), (gelaendeform, "FLACHHEIT_BEWIESEN_MAX", 0.41),
    (gelaendeform, "OFFEN_MAX", 0.042), (gelaendeform, "OFFEN_MAX", 0.058),
    (gelaendeform, "GEFAELLE_GESAMT_MAX", 0.335), (gelaendeform, "GEFAELLE_GESAMT_MAX", 0.365),
    (gelaendeform, "GEFAELLE_UEBERWIEGT_MIN", 0.8), (gelaendeform, "GEFAELLE_UEBERWIEGT_MIN", 1.25),
    (gelaendeform, "AUFRAGEN_MIN", 1.8), (gelaendeform, "AUFRAGEN_MIN", 2.2),
    (gelaendeform, "NEIGUNG_MIN", 0.035), (gelaendeform, "NEIGUNG_MIN", 0.045),
    (gelaendeform, "NEIGUNG_MAX", 0.95), (gelaendeform, "NEIGUNG_MAX", 1.05),
    (gelaendeform, "DECKUNG_MIN", 0.48), (gelaendeform, "DECKUNG_MIN", 0.52),
    (gelaendeform, "LAGEN_MAX", 1.22), (gelaendeform, "LAGEN_MAX", 1.28),
    (gelaendeform, "GENEIGT_ANTEIL_MIN", 0.47), (gelaendeform, "GENEIGT_ANTEIL_MIN", 0.53),
    (gelaendeform, "RICHTUNGEN_MIN", 5), (gelaendeform, "RICHTUNGEN_MIN", 7),
    (gelaendeform, "STREUUNG_QUER_MIN", 0.95), (gelaendeform, "STREUUNG_QUER_MIN", 1.05),
    (gelaendeform, "RICHTUNG_RASTER", 0.007), (gelaendeform, "RICHTUNG_RASTER", 0.015),
    (gelaendeform, "WANDHOEHE_MAX", 1.9), (gelaendeform, "WANDHOEHE_MAX", 2.1),
    (gelaendeform, "TRAEGT_ANTEIL_MIN", 0.47), (gelaendeform, "TRAEGT_ANTEIL_MIN", 0.53),
    (gelaendeform, "TRAEGT_FLAECHE_MIN", 3.6), (gelaendeform, "TRAEGT_FLAECHE_MIN", 4.4),
    (gelaendeform, "FUSS_MAX", 3.3), (gelaendeform, "FUSS_MAX", 3.7),
    # Die Zahl der Rasterfelder ist eine Auflösung, keine Schwelle: bewacht ist nur «zu grob».
    (gelaendeform, "RASTER_FELDER", 4),
    (gelaendeform, "UNTERBAUT_MAX", 0.24), (gelaendeform, "UNTERBAUT_MAX", 0.26),
    (gelaendeform, "UNTERBAUT_TOLERANZ", 0.08), (gelaendeform, "UNTERBAUT_TOLERANZ", 0.13),
    (glbbox, "GERINGE_SCHRUMPFUNG", 0.04), (glbbox, "GERINGE_SCHRUMPFUNG", 0.06),
]


@pytest.mark.parametrize("modul, name, wert", SCHWELLEN, ids=[f"{n}={w}" for _, n, w in SCHWELLEN])
def test_eine_regelaenderung_ohne_neue_datei_wird_rot(modul, name, wert, monkeypatch):
    """Jede Schwelle der Regel ist von beiden Seiten dicht besetzt: Wer sie um einen kleinen Schritt
    verschiebt, ohne die Datei neu zu erzeugen, fällt auf."""
    assert json.loads(json.dumps(_werkzeug().erzeuge())) == DATEN, "vor der Änderung muss die Datei passen"
    monkeypatch.setattr(modul, name, wert)
    assert json.loads(json.dumps(_werkzeug().erzeuge())) != DATEN, (
        f"{name} = {wert} ändert keinen einzigen Fall: die Probendatei bewacht diese Schwelle nicht")


def test_jede_schwelle_der_regel_steht_in_der_liste():
    """Kommt eine Schwelle dazu, muss sie auch bewacht werden."""
    bewacht = {name for _, name, _ in SCHWELLEN}
    quelle = (WURZEL / "src" / "aiimaging" / "gelaendeform.py").read_text(encoding="utf-8")
    zahlen = set(re.findall(r"^([A-Z_]+) = [0-9.]+$", quelle, re.M))
    # Nur im alten Weg ohne Oberseiten wirksam (andere Aufrufer), nicht in `bauwerksbox`:
    alt = {"FLACHHEIT_MAX", "TIEFLAGE_MAX", "TIEFLAGE_UNKLAR_MAX", "FAMILIE_MINDEST"}
    assert zahlen - alt <= bewacht, zahlen - alt - bewacht


def test_ohne_beweis_trennt_die_form_nichts(monkeypatch):
    """Rot vor grün, auf der Python-Seite nachgestellt: Gelingt der Beweis nie, bleibt überall die
    Szenenhülle; so steht ein Mac, dessen Formregel stumm ist."""
    def nie(stelle, alle, flaeche, **_):
        return {"urteil": gelaendeform.NICHT_ENTSCHEIDBAR, "kurz": "stumm", "grund": ""}
    monkeypatch.setattr(gelaendeform, "beweis", nie)
    neu = _werkzeug().erzeuge()["formfaelle"]
    assert not any(f["erwartet"]["entschieden_durch"] == "form" for f in neu)
    anders = [f["fall"] for f, alt in zip(neu, FORMFAELLE)
              if f["erwartet"]["huellbox"] != alt["erwartet"]["huellbox"]]
    assert len(anders) >= 40, len(anders)


# ---------------------------------------------------------------- die Swift-Seite, soweit hier lesbar


def test_der_mac_fuehrt_dieselben_schwellen_wie_der_heim_pc():
    """Die Schwellen in ``Gelaendeform.swift`` sind ein Abbild; sie stehen hier gegen Python fest."""
    text = SWIFT_FORM.read_text(encoding="utf-8")

    def zahl(name):
        m = re.search(r"static let " + name + r"(?::\s*\w+)?\s*=\s*([0-9._]+)", text)
        assert m, name
        return float(m.group(1).replace("_", ""))

    assert zahl("grundrissanteilMin") == gelaendeform.GRUNDRISSANTEIL_MIN
    assert zahl("flachheitBewiesenMax") == gelaendeform.FLACHHEIT_BEWIESEN_MAX
    assert zahl("offenMax") == gelaendeform.OFFEN_MAX
    assert zahl("gefaelleGesamtMax") == gelaendeform.GEFAELLE_GESAMT_MAX
    assert zahl("gefaelleUeberwiegtMin") == gelaendeform.GEFAELLE_UEBERWIEGT_MIN
    assert zahl("aufragenMin") == gelaendeform.AUFRAGEN_MIN
    assert zahl("neigungMin") == gelaendeform.NEIGUNG_MIN
    assert zahl("neigungMax") == gelaendeform.NEIGUNG_MAX
    assert zahl("deckungMin") == gelaendeform.DECKUNG_MIN
    assert zahl("lagenMax") == gelaendeform.LAGEN_MAX
    assert zahl("geneigtAnteilMin") == gelaendeform.GENEIGT_ANTEIL_MIN
    assert zahl("richtungenMin") == gelaendeform.RICHTUNGEN_MIN
    assert zahl("richtungRaster") == gelaendeform.RICHTUNG_RASTER
    assert zahl("streuungQuerMin") == gelaendeform.STREUUNG_QUER_MIN
    assert zahl("wandhoeheMax") == gelaendeform.WANDHOEHE_MAX
    assert zahl("traegtAnteilMin") == gelaendeform.TRAEGT_ANTEIL_MIN
    assert zahl("traegtFlaecheMin") == gelaendeform.TRAEGT_FLAECHE_MIN
    assert zahl("fussMax") == gelaendeform.FUSS_MAX
    assert zahl("rasterFelder") == gelaendeform.RASTER_FELDER
    assert zahl("eckeHoechstens") == glbbox.ECKE_HOECHSTENS
    assert zahl("unterbautMax") == gelaendeform.UNTERBAUT_MAX
    assert zahl("unterbautToleranz") == gelaendeform.UNTERBAUT_TOLERANZ
    assert zahl("geringeSchrumpfung") == glbbox.GERINGE_SCHRUMPFUNG
    assert zahl("dreieckeHoechstens") == glbbox.DREIECKE_HOECHSTENS
    for kurz in (gelaendeform.GRUND_NICHT_LESBAR, gelaendeform.GRUND_DECKUNG, gelaendeform.GRUND_LAGEN,
                 gelaendeform.GRUND_EBEN, gelaendeform.GRUND_EINE_EBENE, gelaendeform.GRUND_EINFACH_GEKRUEMMT,
                 gelaendeform.GRUND_WAND, gelaendeform.GRUND_GESCHLOSSEN, gelaendeform.GRUND_KEIN_HANG,
                 gelaendeform.GRUND_UNTERBAUT, gelaendeform.GRUND_TRAEGT_NICHT):
        assert f'"{kurz}"' in text, kurz


def test_der_mac_fragt_die_form_und_die_swift_probe_liest_die_formfaelle():
    assert "Gelaendeform.zweitmeinung(" in SWIFT_BOX.read_text(encoding="utf-8")
    probe = SWIFT_PROBE.read_text(encoding="utf-8")
    assert '"formfaelle"' in probe and "glbbox_gelaenderegel.json" in probe
    assert "namensgleich" not in SWIFT_FORM.read_text(encoding="utf-8"), (
        "die Ausnahme «namensgleich» ist mit Runde 2 weggefallen")


def test_die_familienpruefung_ist_am_heim_pc_vorgabe_aus():
    """Der Mac bildet sie nicht ab, weil ``bauwerksbox`` sie nicht einschaltet. Ändert sich das,
    muss der Mac nachziehen: dann wird diese Probe rot."""
    import inspect
    assert inspect.signature(gelaendeform.gelaende_knoten).parameters["als_familie"].default is False
    assert "als_familie" not in inspect.getsource(glbbox._zweitmeinung)


def test_beschaedigte_dateien_sind_nicht_lesbar_und_behalten_die_szenenhuelle(tmp_path):
    """Runde 3, M2: verdorbene Angaben zum Lesen der Dreiecke. Nie eine Ausnahme, nie abgetrennt."""
    faelle = [f for f in FORMFAELLE if f["gruppe"] == "beschaedigt"]
    assert len(faelle) >= 15
    for f in faelle:
        aus = _bauwerksbox(f, tmp_path)
        assert aus["entschieden_durch"] == "keine", f["fall"]
        assert aus["bbox_bauwerk"] == aus["bbox_szene"], f["fall"]
        assert aus["form_befund"]["gruende"] == (gelaendeform.GRUND_NICHT_LESBAR,), f["fall"]
