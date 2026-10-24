"""Situationsmodell, Vogelschau und Sichtweite — die Kette für eine Anlage von 500 m.

**Anlass (Ergebnis auf-20261024-354, 24.10.2026):** Das Wettbewerbsmodell des Owners ist eine
Anlage von rund 577 x 500 x 26 m aus Platten, ohne Wände und Dächer. Die Auto-Kamera sSE stand
auf Augenhöhe über der Unterkante und sah sie als Strich am Horizont; die Blender-Kamera hatte
keine eigene Sichtweite. Die ganze Kette war an einem Haus von 15 m eingestellt.

Geprüft wird hier, ohne Blender: die Regel «Situationsmodell», die Vogelschau (alle Ecken im
Bild, Ziel in der Mitte der Bauteile), die Sichtweite (verlängert, nie gekürzt), das Raster
über der Draufsicht, und dass die Auto-Kameras des Abholers und die Kegel der Knotenansicht
dieselbe Vogelschau stellen — mit dem Urteil «Aufsicht», ohne Augenhöhe-Warnung.

Regel 3: alles synthetisch (``tools/make_test_glb.py --situation``).
"""
from __future__ import annotations

import itertools
import math
import sys
from pathlib import Path

import pytest

from aiimaging import abholer, kameras, knotenweg
from aiimaging import kosmo_szene as _kosmo_szene
from conftest import MINI_PNG

WURZEL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WURZEL / "tools"))
import make_test_glb  # noqa: E402

#: Wie das echte Modell aus Ergebnis 354 (gerundet), Z oben.
ANLAGE = [[-288.6, -250.1, 0.0], [288.6, 250.1, 26.2]]
#: Das Demohaus.
HAUS = [[0.0, 0.0, -0.4], [12.0, 9.0, 15.0]]


# ====================================================================== die Regel

@pytest.mark.parametrize("box, ja", [
    (ANLAGE, True),
    (HAUS, False),
    ([[0, 0, 0], [120, 30, 12]], False),        # lange, flache Halle: Entscheid 75, nicht hier
    ([[0, 0, 0], [90, 80, 60]], False),         # hoch: ein Haus
    ([[0, 0, 0], [90, 70, 12]], True),          # flache Anlage von 90 m
])
def test_die_regel_situationsmodell(box, ja):
    befund = kameras.ist_situationsmodell(box)
    assert befund["ja"] is ja
    assert ("SITUATIONSMODELL" in befund["grund"]) is ja


def test_eine_unlesbare_box_ist_nicht_beurteilt_und_nicht_nein():
    assert kameras.ist_situationsmodell(None)["ja"] is None


# ====================================================================== die Vogelschau

def _bild(auge, ziel, punkt, brennweite, verhaeltnis):
    """Punkt → (x, y) als Anteil des halben Bildwinkels — dieselbe Lochkamera wie Blender."""
    vor = kameras._normiert(kameras._minus(ziel, auge))
    rechts = kameras._normiert(kameras._kreuz(vor, (0.0, 0.0, 1.0)))
    oben = kameras._kreuz(rechts, vor)
    p = kameras._minus(punkt, auge)
    tiefe = kameras._punkt(p, vor)
    hfov, vfov = kameras.bildwinkel(brennweite, seitenverhaeltnis=verhaeltnis)
    return (kameras._punkt(p, rechts) / tiefe / math.tan(hfov / 2),
            kameras._punkt(p, oben) / tiefe / math.tan(vfov / 2))


@pytest.mark.parametrize("hoehe", [30.0, 40.0, 45.0])
@pytest.mark.parametrize("kuerzel", ["s", "sSE", "nNW"])
def test_alle_ecken_im_bild_mit_rand_und_die_box_fuellt_es(hoehe, kuerzel):
    k = kameras.vogelschau(ANLAGE, kuerzel=kuerzel, hoehe_grad=hoehe, seitenverhaeltnis=1.6)
    groesste = 0.0
    for ecke in itertools.product(*zip(*ANLAGE)):
        x, y = _bild(k["auge"], k["blick_auf"], ecke, k["brennweite_mm"], 1.6)
        assert abs(x) <= kameras.BILDRAND + 1e-6 and abs(y) <= kameras.BILDRAND + 1e-6
        groesste = max(groesste, abs(x), abs(y))
    # Der Abstand ist der KLEINSTE, bei dem alles passt: eine Ecke liegt am Rand.
    assert groesste == pytest.approx(kameras.BILDRAND, abs=1e-3)
    # Ziel ist die Mitte der Box, der Hoehenwinkel wie bestellt.
    assert k["blick_auf"] == pytest.approx([0.0, 0.0, 13.1], abs=1e-3)
    d = kameras._minus(k["auge"], k["blick_auf"])
    assert math.degrees(math.asin(d[2] / kameras._laenge(d))) == pytest.approx(hoehe)
    assert k["kuerzel"] == f"vogelschau-{kuerzel}"
    assert kameras.ist_vogelschau(k["kuerzel"])


def test_die_draufsicht_hat_norden_oben():
    k = kameras.vogelschau(ANLAGE, kuerzel="s", hoehe_grad=kameras.DRAUFSICHT_GRAD,
                           seitenverhaeltnis=1.6)
    assert k["draufsicht"] and k["kuerzel"] == "draufsicht-s"
    _, y_nord = _bild(k["auge"], k["blick_auf"], (0.0, 250.0, 0.0), 35.0, 1.6)
    _, y_sued = _bild(k["auge"], k["blick_auf"], (0.0, -250.0, 0.0), 35.0, 1.6)
    assert y_nord > 0 > y_sued


@pytest.mark.parametrize("hoehe", [90.0, 0.0, float("nan"), True])
def test_senkrecht_und_waagrecht_werden_abgewiesen(hoehe):
    with pytest.raises(ValueError):
        kameras.vogelschau(ANLAGE, hoehe_grad=hoehe)


def test_unbekannte_richtung_wird_abgewiesen():
    with pytest.raises(ValueError):
        kameras.vogelschau(ANLAGE, kuerzel="oben")


# ====================================================================== die Sichtweite

def test_die_sichtweite_reicht_ueber_die_weiteste_ecke():
    k = kameras.vogelschau(ANLAGE, kuerzel="sSE", hoehe_grad=45, seitenverhaeltnis=1.6)
    befund = kameras.sichtweite(ANLAGE, k["auge"], clip_end_vorher_m=100.0)
    assert befund["clip_end_m"] > befund["weiteste_m"] > 1000.0
    assert befund["verlaengert"] and befund["haette_abgeschnitten"]
    assert "VERLAENGERT" in befund["grund"]


def test_die_sichtweite_kuerzt_nie__ein_haus_rendert_wie_bisher():
    befund = kameras.sichtweite(HAUS, (30.0, -30.0, 1.7), clip_end_vorher_m=1000.0)
    assert befund["clip_end_m"] == 1000.0
    assert not befund["verlaengert"] and not befund["haette_abgeschnitten"]


def test_die_sichtweite_ohne_standpunkt_ist_nicht_geprueft():
    befund = kameras.sichtweite(HAUS, None, clip_end_vorher_m=100.0)
    assert befund["clip_end_m"] == 100.0 and "NICHT GEPRUEFT" in befund["grund"]


def test_der_runner_setzt_die_sichtweite_nach_kontext_und_umfeld():
    """Statisch (kein Blender hier): Der Runner ruft `_sichtweite_setzen` NACH dem Laden von
    Kontext und Umfeld, und die Funktion stellt `clip_end` aus `kameras.sichtweite`."""
    text = (WURZEL / "src/aiimaging/runners/blender_depth_stage.py").read_text(encoding="utf-8")
    haupt = text[text.index("def main() -> int:"):]
    aufruf = haupt.index('kamera_herkunft["sichtweite"] = _sichtweite_setzen(kamera_herkunft)')
    assert haupt.index("_umfeld_laden(a,") < aufruf
    assert haupt.index("_kontext_laden(a)") < aufruf
    assert aufruf < haupt.index("_renderparameter_setzen(a)")
    funktion = text[text.index("def _sichtweite_setzen"):text.index("def _gelaende_am_standpunkt")]
    assert "kameras.sichtweite(" in funktion and "kam.data.clip_end =" in funktion


# ====================================================================== das Raster

def test_die_zellen_des_rasters_liegen_wie_im_plan():
    k = kameras.vogelschau(ANLAGE, kuerzel="s", hoehe_grad=kameras.DRAUFSICHT_GRAD,
                           seitenverhaeltnis=1.6)
    zelle = {z: kameras.rasterzelle_bereich(z, k["auge"], k["blick_auf"], boden_z=0.0,
                                            hoehe_m=26.2, seitenverhaeltnis=1.6)
             for z in ("A1", "D1", "A4", "D4", "B2", "C3")}
    # A1 oben links = Nordwesten, D4 unten rechts = Suedosten.
    assert zelle["A1"][1][0] <= 1.0 and zelle["A1"][0][1] >= -1.0
    assert zelle["D4"][0][0] >= -1.0 and zelle["D4"][1][1] <= 1.0
    assert zelle["D1"][0][0] > zelle["A1"][0][0]
    assert zelle["A4"][0][1] < zelle["A1"][0][1]
    # Die vier Spalten zusammen ueberdecken die Anlage.
    assert zelle["A1"][0][0] < ANLAGE[0][0] and zelle["D1"][1][0] > ANLAGE[1][0]
    # Eine Zelle ist eine Box, auf die eine Vogelschau gestellt werden kann.
    v = kameras.vogelschau(zelle["B2"], kuerzel="sSE", hoehe_grad=40)
    assert v["abstand_m"] < kameras.vogelschau(ANLAGE, kuerzel="sSE", hoehe_grad=40)["abstand_m"]


def test_ein_gebiet_aus_vier_zellen_umfasst_sie_alle():
    """Ergebnis 356: Der Owner wählte den Kreuzpunkt B2/B3/C2/C3, nicht eine Zelle."""
    k = kameras.vogelschau(ANLAGE, kuerzel="s", hoehe_grad=kameras.DRAUFSICHT_GRAD,
                           seitenverhaeltnis=1.6)
    def bereich(z):
        return kameras.rasterzelle_bereich(z, k["auge"], k["blick_auf"], boden_z=0.0,
                                           hoehe_m=26.2, seitenverhaeltnis=1.6)
    gebiet = bereich("B2:C3")
    assert bereich("c3:b2") == gebiet
    for z in ("B2", "B3", "C2", "C3"):
        b = bereich(z)
        for i in (0, 1):
            assert gebiet[0][i] <= b[0][i] + 1e-6 and gebiet[1][i] >= b[1][i] - 1e-6
    # Ein Gebiet aus einer Zelle ist die Zelle selbst.
    assert bereich("B2:B2") == bereich("B2")
    # Die Vogelschau auf das Gebiet steht weiter weg als auf eine Zelle, näher als auf alles.
    v = lambda box: kameras.vogelschau(box, kuerzel="sSE", hoehe_grad=40)["abstand_m"]
    assert v(bereich("B2")) < v(gebiet) < v(ANLAGE)


@pytest.mark.parametrize("zelle", ["E1", "A5", "A0", "", "B", "B2:C3:D4", "B2:E1"])
def test_eine_unbekannte_zelle_wird_abgewiesen(zelle):
    k = kameras.vogelschau(ANLAGE, kuerzel="s", hoehe_grad=kameras.DRAUFSICHT_GRAD)
    with pytest.raises(ValueError):
        kameras.rasterzelle_bereich(zelle, k["auge"], k["blick_auf"], boden_z=0.0, hoehe_m=1.0)


# ====================================================================== Abholer und Kegel

@pytest.fixture
def anlage(tmp_path):
    pfad = tmp_path / "anlage.glb"
    assert make_test_glb.main([str(pfad), "--situation"]) == 0
    return pfad


@pytest.fixture
def haus(tmp_path):
    pfad = tmp_path / "haus.glb"
    assert make_test_glb.main([str(pfad)]) == 0
    return pfad


def test_die_synthetische_anlage_ist_ein_situationsmodell_aus_platten(anlage):
    from aiimaging import glbbox
    rahmung = glbbox.rahmungsbox(anlage, up_axis="Y")
    assert rahmung["box"] is not None, "die Gelaendeplatten fallen aus der Bauwerksbox"
    assert kameras.ist_situationsmodell(rahmung["box"])["ja"] is True
    namen = [k[0] for k in make_test_glb.situationsszene()]
    assert all(n.startswith("IfcSlab_") for n in namen)
    assert sum("Gelaende" in n for n in namen) == 3


def test_die_auto_kameras_einer_anlage_sind_vogelschauen(anlage):
    vogel = abholer.vogelschau_der_auto_kameras(anlage, "Y", abholer.AUTO_RICHTUNGEN,
                                                seitenverhaeltnis=1.6)
    assert vogel is not None and vogel["situation"]["ja"]
    assert [a["kuerzel"] for a in vogel["aufgaben"]] == [
        f"vogelschau-{r}" for r in abholer.AUTO_RICHTUNGEN]
    for a in vogel["aufgaben"]:
        assert "richtung" not in a, "Standort gegeben — kein Kuerzel, sonst doppelt bestellt"
        assert a["auge"][2] > 200.0
        assert a["vogelschau"]["hoehe_grad"] == kameras.VOGELSCHAU_GRAD


def test_ein_haus_bleibt_in_augenhoehe(haus):
    assert abholer.vogelschau_der_auto_kameras(haus, "Y", abholer.AUTO_RICHTUNGEN) is None
    vorschau = knotenweg.heim_standpunkte(haus, "Y")
    assert [s["kuerzel"] for s in vorschau["standpunkte"]] == list(abholer.AUTO_RICHTUNGEN)


def test_die_kegel_der_knotenansicht_zeigen_dieselbe_vogelschau(anlage):
    vorschau = knotenweg.heim_standpunkte(anlage, "Y", seitenverhaeltnis=1.6)
    vogel = abholer.vogelschau_der_auto_kameras(anlage, "Y", abholer.AUTO_RICHTUNGEN,
                                                seitenverhaeltnis=1.6)
    assert [s["kuerzel"] for s in vorschau["standpunkte"]] == [
        a["kuerzel"] for a in vogel["aufgaben"]]
    for s, a in zip(vorschau["standpunkte"], vogel["aufgaben"]):
        assert s["auge"] == pytest.approx(a["auge"], abs=1e-2)
        assert s["name"].startswith("Vogelschau")


def test_der_abholer_stellt_die_vogelschau_und_urteilt_aufsicht(anlage, tmp_path):
    """An der Naht: Die Auto-Kameras gehen als Standort an den Runner, und der Bericht, den der
    Runner daraus schreibt, ergibt «Aufsicht» — ohne Satz zur Kamerahoehe."""
    from aiimaging import glbbox
    szene_box = glbbox.bauwerksbox(anlage, up_axis="Y")["bbox_szene"]
    gestellt = []

    def multipass(glb, aus, **kw):
        gestellt.append(kw)
        tiefe = Path(aus) / "tiefe_norm.png"
        tiefe.write_bytes(MINI_PNG)
        felder = kameras.berichtsfelder_aus_stellung(kw["auge"], kw["blick_auf"], szene_box)
        return {"depth_png": str(tiefe),
                "kamera": dict(felder, weg="vorgegeben", auge=list(kw["auge"]),
                               blick_auf=list(kw["blick_auf"]))}

    bild = tmp_path / "b.png"

    def rendere(auftrag, **kw):
        bild.write_bytes(MINI_PNG)
        return {"status": "ok", "bild_png": str(bild), "hinweise": ()}

    zaehler = iter(range(1, 99))
    verarbeite = abholer.verarbeiter(
        out_wurzel=tmp_path / "aus", nullprobe=False, _multipass=multipass, _rendere=rendere,
        _qa=lambda *a, **k: {"score": 0.8, "bestanden": True},
        _soll=lambda *a, **k: ([[float(next(zaehler))]], 1, 1))
    ergebnis = verarbeite({"modell": anlage, "job_id": "vis-1-aaaaaa", "verzeichnis": tmp_path,
                           "szene": {"kameras": "auto", "aufloesung": 160, "hoehe": 100,
                                     "samples": 1, "prompt": "a site"}})
    assert [kw.get("kamera") for kw in gestellt] == [None] * 3
    assert all(kw["auge"][2] > 200.0 for kw in gestellt)
    for urteil in ergebnis["kameras"]:
        assert kameras.ist_vogelschau(urteil["kamera"])
        assert urteil["komposition"]["aufsicht"] is not None
        assert "AUFSICHT" in urteil["komposition"]["grund"]
        assert not urteil.get(_kosmo_szene.URTEIL_KAMERAHOEHE)
        assert "SITUATIONSMODELL" in urteil[_kosmo_szene.URTEIL_VOGELSCHAU]["satz"]


def test_abschaltbar(anlage, tmp_path):
    gestellt = []

    def multipass(glb, aus, **kw):
        gestellt.append(kw)
        tiefe = Path(aus) / "tiefe_norm.png"
        tiefe.write_bytes(MINI_PNG)
        return {"depth_png": str(tiefe), "kamera": {"weg": "abgeleitet"}}

    zaehler = iter(range(1, 99))
    verarbeite = abholer.verarbeiter(
        out_wurzel=tmp_path / "aus", nullprobe=False, vogelschau_auto=False,
        _multipass=multipass,
        _rendere=lambda auftrag, **kw: {"status": "ok", "bild_png": str(_bild_datei(tmp_path)),
                                        "hinweise": ()},
        _qa=lambda *a, **k: {"score": 0.8, "bestanden": True},
        _soll=lambda *a, **k: ([[float(next(zaehler))]], 1, 1))
    verarbeite({"modell": anlage, "job_id": "vis-1-bbbbbb", "verzeichnis": tmp_path,
                "szene": {"kameras": "auto", "aufloesung": 64, "hoehe": 64, "samples": 1,
                          "prompt": "a site"}})
    assert [kw.get("kamera") for kw in gestellt] == list(abholer.AUTO_RICHTUNGEN)


def _bild_datei(ordner):
    pfad = Path(ordner) / "b.png"
    pfad.write_bytes(MINI_PNG)
    return pfad


def test_der_satz_der_vogelschau_geht_in_die_hinweise():
    vermerk = {"satz": "SITUATIONSMODELL (…). VOGELSCHAU aus sSE."}
    saetze = _kosmo_szene._aufsicht_saetze(None, [{"kamera": "vogelschau-sSE",
                                                   _kosmo_szene.URTEIL_VOGELSCHAU: vermerk}])
    assert vermerk["satz"] in saetze


# ====================================================================== das Werkzeug (Auftrag 356)

def test_das_werkzeug_gibt_kameras_fuer_die_bruecke(anlage):
    import vogelschau as werkzeug
    aus = werkzeug.kameras_fuer(anlage, hoehen=(45, 30), draufsicht=True, zelle="B2",
                                seitenverhaeltnis=1.6)
    namen = [c["name"] for c in aus["cameras"]]
    assert namen == ["draufsicht-s", "vogelschau-sSE-45", "vogelschau-sSE-30", "zelle-B2-sSE"]
    for spec in aus["cameras"]:
        # Was die Bruecke annimmt: `spec_zu_kamera` liest es zurueck, Z oben.
        zurueck = _kosmo_szene.spec_zu_kamera(spec)
        assert zurueck["auge"] == pytest.approx(spec["position"])
        assert spec["perspektive"] == "frei"
    assert aus["situation"]["ja"] is True


def test_das_werkzeug_zeichnet_das_raster(tmp_path):
    pytest.importorskip("PIL")
    from PIL import Image

    import vogelschau as werkzeug
    Image.new("RGB", (160, 100), (200, 200, 200)).save(tmp_path / "plan.png")
    werkzeug.raster_zeichnen(tmp_path / "plan.png", tmp_path / "raster.png")
    bild = Image.open(tmp_path / "raster.png").convert("RGB")
    assert bild.size == (160, 100)
    assert bild.getpixel((40, 60)) == (255, 40, 40), "Spaltenlinie zwischen A und B"


def test_das_werkzeug_von_der_befehlszeile(anlage, capsys):
    """Alle Schalter einmal gedrueckt (Schalterprobe): Ausgabe ist JSON mit den Kameras."""
    import json

    import vogelschau as werkzeug
    assert werkzeug.main(["kameras", str(anlage), "--hoehe", "40", "--richtung", "s",
                          "--draufsicht", "--zelle", "C3", "--aufloesung", "960x600",
                          "--brennweite", "35", "--achse", "Y"]) == 0
    aus = json.loads(capsys.readouterr().out)
    assert [c["name"] for c in aus["cameras"]] == ["draufsicht-s", "vogelschau-s-40",
                                                   "zelle-C3-s"]
    assert werkzeug.main(["kameras", str(anlage), "--zelle", "Z9"]) == 2
