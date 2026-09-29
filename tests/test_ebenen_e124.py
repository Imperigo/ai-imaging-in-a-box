"""Die Ebenen (Render-Pässe), Schritt 1 nach E124 — 29.09.2026.

KosmoOrbit hat am 29.09.2026 entschieden, die Pässe in zwei Schritten zu nehmen: erst Vertrag
und Rückweg gegen ein echtes Beispiel-JSON, die Anzeige erst nach einem echten Lauf. Ihre drei
Bedingungen aus der Antwort auf auf-171 (K4) sind hier je eine Probe:

a. ``bedeutung`` ist strukturiert, nicht Freitext (Tiefe in Metern, Material-ID mit Tabelle
   und Nullfarbe).
b. ``ebenen`` ist optional und ohne Vorgabe: ohne Bestellung fehlt das Feld.
c. «bestellt, aber fehlt» heisst an der Kamera ``lieferstatus: fehlgeschlagen`` mit Grund.

Dazu die Form, die ihr ``get_artifact`` verlangt: ein flacher Name ohne ``/``.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

from aiimaging import abholer, bruecke, kosmo_szene  # noqa: E402
from test_abholer import _auftrag, _kette  # noqa: E402

JOB = "vis-1787123048-098c6e"


def _szene(passes=None, **render):
    szene = {"schema": kosmo_szene.SCHEMA_SZENE,
             "geometry": {"path": "model.glb", "format": "glb"},
             "cameras": [
                 {"name": "Eingang", "position": [0, -20, 1.3], "target": [0, 0, 1.3],
                  "fov": 60, "up_axis": "z"},
                 {"name": "Uebersicht", "position": [0, -60, 38], "target": [0, 0, 5],
                  "fov": 50, "up_axis": "z"},
             ],
             "render": {"resolution": [512, 512], "samples": 64, "faithful": 0.8, **render},
             "style": {"prompt": "ein Haus", "mode": "none"}}
    if passes is not None:
        szene["render"]["passes"] = passes
    return szene


# ======================================================================================
# 1 · Die Bestellung
# ======================================================================================

@pytest.mark.parametrize("passes, erwartet", [
    (None, ()),
    ([], ()),
    (["tiefe"], ("tiefe",)),
    (["material-id", "tiefe", "tiefe"], ("material-id", "tiefe")),
    ("alle", kosmo_szene.EBENEN_ARTEN),
])
def test_render_passes_wird_gelesen(passes, erwartet):
    gelesen = kosmo_szene.lies_szene(_szene(passes))
    assert not gelesen["maengel"], gelesen["maengel"]
    assert gelesen["ebenen"] == erwartet


@pytest.mark.parametrize("passes", [["normalen"], "tiefe", [1], {"tiefe": True}])
def test_eine_unbekannte_ebene_wird_nicht_geraten(passes):
    gelesen = kosmo_szene.lies_szene(_szene(passes))
    assert any("render.passes" in m for m in gelesen["maengel"])
    assert gelesen["ebenen"] == ()


# ======================================================================================
# 2 · Die ganze Kette mit Attrappen: was im Auftragsordner ankommt
# ======================================================================================

def _lauf(tmp_path, passes):
    ordner = _auftrag(tmp_path, JOB, szene=_szene(passes))
    _, attrappen = _kette(scores=(0.8, 0.8))
    antwort = abholer.hole_einen(ordner, fremde_freigabe_gilt=True,
                                 verarbeite=abholer.verarbeiter(
                                     out_wurzel=tmp_path / "aus", nullprobe=False,
                                     **attrappen))
    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort
    return ordner, json.loads((ordner / bruecke.DATEI_ERGEBNIS).read_text(encoding="utf-8"))


def test_ohne_bestellung_fehlt_das_feld(tmp_path):
    """Bedingung b: kein Feld heisst «nichts gesagt», ein leeres hiesse «keine Ebenen»."""
    _, ergebnis = _lauf(tmp_path, None)
    assert "ebenen" not in ergebnis


def test_alle_ebenen_kommen_flach_und_strukturiert_an(tmp_path):
    ordner, ergebnis = _lauf(tmp_path, "alle")
    ebenen = ergebnis["ebenen"]
    kameras = {e["kamera"] for e in ebenen}
    assert len(kameras) == 2
    assert len(ebenen) == 2 * len(kosmo_szene.EBENEN_ARTEN)
    for e in ebenen:
        assert set(e) == {"kamera", "art", "datei", "bedeutung"}, e   # kein `quelle` (Regel 3)
        assert "/" not in e["datei"] and e["datei"] == f"{e['kamera']}__{e['art']}.png"
        assert (ordner / e["datei"]).is_file(), e["datei"]
        assert isinstance(e["bedeutung"], dict)                       # Bedingung a
    tiefe = next(e for e in ebenen if e["art"] == "tiefe")["bedeutung"]
    assert tiefe["einheit"] == "m" and tiefe["nah"] == "hell"
    mid = next(e for e in ebenen if e["art"] == "material-id")["bedeutung"]
    assert mid["nullfarbe_srgb_8bit"] == [0, 0, 0]
    assert [t["name"] for t in mid["tabelle"]] == ["Wand", "Boden_Platte"]
    # Alles Bestellte ist da: an der Lieferung aendert sich nichts.
    assert all(s["lieferstatus"] == "geliefert" for s in ergebnis["qa_je_kamera"])


def test_kein_pfad_dieser_maschine_im_ergebnis(tmp_path):
    ordner, _ = _lauf(tmp_path, "alle")
    text = (ordner / bruecke.DATEI_ERGEBNIS).read_text(encoding="utf-8")
    assert str(tmp_path) not in text


# ======================================================================================
# 3 · Bestellt, aber fehlt → die Kamera ist «fehlgeschlagen» (Bedingung c)
# ======================================================================================

def _kamera(name):
    return {"kamera": name, "lieferstatus": "geliefert", "lieferstatus_grund": "",
            "bilder_soll": 1, "bilder_ist": 1}


def test_eine_fehlende_ebene_macht_die_kamera_fehlgeschlagen():
    ebenen = [{"kamera": "K1", "art": "tiefe", "datei": "K1__tiefe.png",
               "bedeutung": {"einheit": "m"}},
              {"kamera": "K2", "art": "tiefe", "datei": None, "bedeutung": None,
               "grund": "Der Multipass hat kein depth_png geschrieben."}]
    ergebnis = kosmo_szene.als_ergebnis(JOB, ["K1.png", "K2.png"],
                                        je_kamera=[_kamera("K1"), _kamera("K2")],
                                        ebenen=ebenen)
    je = {s["kamera"]: s for s in ergebnis["qa_je_kamera"]}
    assert je["K1"]["lieferstatus"] == "geliefert"
    assert je["K2"]["lieferstatus"] == "fehlgeschlagen"
    assert "BESTELLTE EBENE FEHLT: tiefe" in je["K2"]["lieferstatus_grund"]
    assert ergebnis["lieferstatus"] == "fehlgeschlagen"
    # Die fehlende Ebene bleibt in der Liste, mit ihrem Grund — keine stille Luecke.
    fehlt = next(e for e in ergebnis["ebenen"] if e["kamera"] == "K2")
    assert fehlt["datei"] is None and fehlt["grund"]
    # Die gelieferte traegt kein `grund`-Feld.
    assert "grund" not in next(e for e in ergebnis["ebenen"] if e["kamera"] == "K1")


def test_der_abholer_nennt_eine_fehlende_datei_mit_grund(tmp_path):
    bericht = {"depth_png": None, "depth_png_fehler": "Kompositor kaputt",
               "beauty_png": str(tmp_path / "gibt-es-nicht.png")}
    ebenen = abholer.ebenen_dieser_kamera(bericht, "K1", ("tiefe", "schoenbild"))
    assert [e["datei"] for e in ebenen] == [None, None]
    assert "Kompositor kaputt" in ebenen[0]["grund"]


def test_die_zustellung_streicht_den_pfad_und_kopiert(tmp_path):
    quelle = tmp_path / "ablage" / "tiefe.png"
    quelle.parent.mkdir()
    quelle.write_bytes(b"png")
    ordner = tmp_path / "auftrag"
    ordner.mkdir()
    aus = bruecke.ebenen_bereitstellen(ordner, [
        {"kamera": "K1", "art": "tiefe", "datei": "K1__tiefe.png", "bedeutung": {},
         "quelle": str(quelle)},
        {"kamera": "K2", "art": "tiefe", "datei": "K2__tiefe.png", "bedeutung": {},
         "quelle": str(tmp_path / "weg.png")}])
    assert (ordner / "K1__tiefe.png").read_bytes() == b"png"
    assert all("quelle" not in e for e in aus)
    assert aus[1]["datei"] is None and aus[1]["grund"]
    assert bruecke.ebenen_bereitstellen(ordner, None) is None


# ======================================================================================
# 4 · `geometry_gates` und `qa.geometry` in IHREN Woertern (Antwort auf auf-142)
# ======================================================================================
#
# Ihre zwei Bedingungen: `passed` ist Boolean, nie null (V3); `status` kennt genau
# `measured | not_measured | not_applicable` (V2). Drinnen bleibt unsere dreiwertige Form —
# geprueft wird hier nur die Aussengrenze `nur_vertragsfelder`.

IHRE_WOERTER = {"measured", "not_measured", "not_applicable"}


@pytest.mark.parametrize("status, passed, erwartet", [
    (kosmo_szene.STATUS_OK, True, ("measured", True)),
    (kosmo_szene.STATUS_OK, False, ("measured", False)),
    (kosmo_szene.STATUS_OK, None, ("not_applicable", False)),     # gemessen, trennt nicht
    (kosmo_szene.STATUS_FEHLT, None, ("not_measured", False)),
    (kosmo_szene.STATUS_FEHLT, False, ("not_measured", False)),   # andere Kamera faellt
    (kosmo_szene.STATUS_DEGENERIERT, None, ("not_measured", False)),
])
def test_tore_in_ihren_worten(status, passed, erwartet):
    block = {"status": status, "passed": passed, "released": False, "separates": None,
             "rho_mask": None, "rho_mask_status": status, "geom_iou_status": status,
             "counter_check_status": kosmo_szene.STATUS_FEHLT, "fail_reasons": ["x"]}
    aus = kosmo_szene.tore_in_ihren_worten(block)
    assert (aus["status"], aus["passed"]) == erwartet
    assert all(aus[f] in IHRE_WOERTER for f in kosmo_szene.TOR_STATUSFELDER)
    assert None not in aus.values(), "kein null — weglassen ist bei ihnen richtig"
    assert aus["fail_reasons"] == ["x"]
    assert block["passed"] is passed, "die innere Form bleibt unberuehrt"


def test_die_geschriebene_datei_kennt_nur_ihre_woerter(tmp_path):
    _, ergebnis = _lauf(tmp_path, None)
    for geo in [ergebnis["qa"].get("geometry")] + [
            s.get("geometry") for s in ergebnis.get("qa_je_kamera") or ()]:
        if geo is not None:
            assert geo["status"] in IHRE_WOERTER
            assert isinstance(geo["passed"], bool)
    tore = ergebnis.get(kosmo_szene.FELD_ZWEI_TORE)
    if tore is not None:
        assert tore["status"] in IHRE_WOERTER and isinstance(tore["passed"], bool)
