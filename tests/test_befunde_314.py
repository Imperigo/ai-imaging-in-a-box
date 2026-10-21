"""Befunde aus ``auf-20261021-314`` (local) im Heim-PC-Kern behoben — B2, B4, B6, Teil 8.

B3 (Assistent F4/F1) steht in ``tests/test_assistent_werkzeuge.py``, B1 (Speichersatz) in
``tests/test_befunde_303.py``. Kein Netz, keine GPU, kein Blender.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from aiimaging import abholer, geraetebuch, kameras, kosmo_szene

WURZEL = Path(__file__).resolve().parents[1]


# ============================================================ B4 · das Gerätebuch, genau der Fall aus 314

#: 314 Teil 7 wörtlich: Eintrag ipad mit NUR weg und zuletzt_um (kein gekoppelt_um).
FALL_314 = {"geraete": {"ipad": {"weg": "mac", "zuletzt_um": 1792583625.9921439}}}


def _werkzeug():
    spez = importlib.util.spec_from_file_location(
        "bereinigen_314", WURZEL / "tools" / "geraetebuch_bereinigen.py")
    modul = importlib.util.module_from_spec(spez)
    spez.loader.exec_module(modul)
    return modul


def test_b4_mit_ja_bleibt_der_eintrag_gekoppelt(tmp_path, capsys):
    datei = tmp_path / "geraete.json"
    datei.write_text(json.dumps(FALL_314), encoding="utf-8")
    vorher = geraetebuch.antwort(geraetebuch.lies(datei), jetzt=1792600000.0)["ipad"]
    assert vorher["gekoppelt"] is True and vorher["weg"] == "mac"          # Fehlstand aus 308
    assert _werkzeug().main([str(datei), "--zuletzt-um", "1792583625", "--ja"]) == 0
    ausgabe = json.loads(capsys.readouterr().out)
    assert ausgabe["geschrieben"] is True and ausgabe["nachher"] == {"gekoppelt": True}
    # Was /api/geraete danach zeigt — erwartet laut 314: gekoppelt true, gesehen null, weg null.
    nachher = geraetebuch.antwort(geraetebuch.lies(datei), jetzt=1792600000.0)["ipad"]
    assert nachher == {"gekoppelt": True, "gekoppelt_vor_s": None, "zuletzt_gesehen_s": None,
                       "weg": None}
    # Der Eintrag ist nicht weg, und ein zweites Mal ändert nichts mehr.
    assert "ipad" in json.loads(datei.read_text(encoding="utf-8"))["geraete"]
    assert _werkzeug().main([str(datei), "--zuletzt-um", "1792583625", "--ja"]) == 1


def test_b4_ein_echtes_ipad_danach_schreibt_wieder_zeit_und_weg():
    buch = json.loads(json.dumps(FALL_314))
    geraetebuch.bereinige_fehleintrag(buch, "ipad", zuletzt_um=1792583625.0)
    geraetebuch.vermerke_anfrage(buch, "ipad", weg="direkt", jetzt=1792600100.0)
    a = geraetebuch.antwort(buch, jetzt=1792600110.0)["ipad"]
    assert a["gekoppelt"] is True and a["zuletzt_gesehen_s"] == 10 and a["weg"] == "direkt"
    geraetebuch.vermerke_kopplung(buch, "ipad", jetzt=1792600200.0)
    assert "gekoppelt" not in buch["geraete"]["ipad"]                  # jetzt mit Zeit


def test_b4_ein_leerer_probename_faellt_weg_wie_bisher():
    buch = {"geraete": {"ipad-probe": {"weg": "mac", "zuletzt_um": 1792590000.0}}}
    befund = geraetebuch.bereinige_fehleintrag(buch, "ipad-probe", zuletzt_um=1792590000.0)
    assert befund["bereinigt"] is True and befund["nachher"] is None
    assert "ipad-probe" not in buch["geraete"]


# ============================================================ B2 · deutsche Kamerakürzel

def _szene(richtungen):
    return {"geometry": {"path": "/x/model.glb", "format": "glb"}, "cameras": "auto",
            "cameras_auto": {"richtungen": richtungen}, "render": {},
            "style": {"prompt": "a house"}, "vis": {}}


def test_b2_nno_heisst_nne_und_das_ergebnis_sagt_es():
    s = kosmo_szene.lies_szene(_szene(["sSE", "nNW", "nNO", "sSW"]))
    assert s["maengel"] == ()
    assert s["kameras_auto"]["richtungen"] == ["sSE", "nNW", "nNE", "sSW"]
    assert s["kameras_umgedeutet"] == {"nNO": "nNE"}
    assert any("'nNO' (deutsch) als 'nNE'" in w for w in s["warnungen"])
    assert "umgedeutet" not in s["kameras_auto"]           # Schluessel der Grundlage gleich
    assert abholer.angewandt_der_szene(s)["cameras_auto"]["umgedeutet"] == {"nNO": "nNE"}
    englisch = kosmo_szene.lies_szene(_szene(["sSE", "nNW", "nNE", "sSW"]))
    assert englisch["kameras_auto"] == s["kameras_auto"]


@pytest.mark.parametrize("de, en", sorted(kameras.GLEICHWORTE_DEUTSCH.items()))
def test_b2_jedes_gleichwort_ist_eindeutig(de, en):
    assert en in kameras.RICHTUNGEN and de not in kameras.RICHTUNGEN
    assert "O" not in "".join(kameras.RICHTUNGEN) and "o" not in "".join(kameras.RICHTUNGEN)
    assert de.replace("O", "E").replace("o", "e") == en


def test_b2_ein_unbekanntes_kuerzel_endet_sofort_mit_satz():
    s = kosmo_szene.lies_szene(_szene(["sSE", "nXY"]))
    assert any("cameras_auto.richtungen" in m for m in s["maengel_endgueltig"])
    satz = next(m for m in s["maengel_endgueltig"] if "cameras_auto.richtungen" in m)
    assert "'nXY'" in satz and "nNO" in satz                       # nennt auch die deutschen
    # doppelt nach dem Umdeuten ist ebenso endgueltig
    assert kosmo_szene.lies_szene(_szene(["nNE", "nNO"]))["maengel_endgueltig"]


# ============================================================ B6 · beide Sätze, wo beide gelten

def _je_kamera(werte):
    return [{"kamera": k, "geometrie_urteil": {"kamera": k, "ausserhalb_umriss": {"anteil_haus": w}}}
            for k, w in werte]


def test_b6_der_umriss_satz_steht_je_kamera_ueber_der_schwelle():
    """314 K, 4 Kameras: sSE hoch, nNW 2,13, nNE 2,25, sSW 3,33 — alle über 0,25."""
    werte = [("sSE", 4.1), ("nNW", 2.13), ("nNE", 2.25), ("sSW", 3.33), ("s", 0.1)]
    qa, hinweise = {}, []
    kosmo_szene._ausserhalb_eintragen(qa, None, _je_kamera(werte), hinweise)
    assert qa[kosmo_szene.FELD_AUSSERHALB] == 4.1                       # Lauf: der groesste
    saetze = [h for h in hinweise if h.startswith(kosmo_szene.SATZ_AUSSERHALB)]
    assert [s.split("Kamera ")[1].split(" ")[0] for s in saetze] == \
        ["'sSE'", "'nNW'", "'nNE'", "'sSW'"]


# ============================================================ Teil 8 · OptiX, kein Verhaltenswechsel

def test_optix_cpu_bleibt_und_die_begruendung_nennt_314():
    quelle = (WURZEL / "src" / "aiimaging" / "runners" / "blender_depth_stage.py").read_text(
        encoding="utf-8")
    assert 'szene.cycles.device = "CPU"' in quelle
    assert "auf-20261021-314" in quelle and "7,4 s" in quelle and "3,9 GB" in quelle
