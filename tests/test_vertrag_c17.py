"""Vertrag C17 (21.10.2026, vom Integrator angenommen): drei Unterfelder von ``angewandt``.

* A1 ``angewandt.modus {bestellt, gerechnet, abweichung, kameras}`` — wie das KI-Bild entstand,
  an JEDEM Lauf mit KI-Schritt (bis dahin nur beim Messschalter ``vis.bildeingang`` und als Satz).
* A2 ``angewandt.umriss_halten`` und A3 ``angewandt.cameras_senkrecht`` schrieb der Heim-PC schon;
  hier nur die Form, die der Vertrag liest (A2: ``art`` 'nachher'/'im_lauf' oder None, je Kamera
  ``angewandt`` immer).

Testdaten synthetisch (Regel 3), Blender und Bildmodell als Attrappen (Regel 2).
"""
from __future__ import annotations

import json

from aiimaging import abholer, bruecke, kosmo_szene, render

from test_kettenlauf_26august import _auftragsordner, _kette, _lauf


def _erg(bestellt, gerechnet, abweichung="aus"):
    erg = {"modus_bestellt": bestellt, "modus_gerechnet": gerechnet}
    if abweichung != "aus":
        erg["modus_abweichung"] = abweichung
    return erg


# ====================================================================== A1 · je Kamera

def test_der_vermerk_nennt_bestellt_gerechnet_und_abweichung():
    assert abholer.modus_vermerk(_erg("image_edit", "image_edit", False)) == {
        "bestellt": "image_edit", "gerechnet": "image_edit", "abweichung": False}
    assert abholer.modus_vermerk(_erg("image_edit", "txt2img", True)) == {
        "bestellt": "image_edit", "gerechnet": "txt2img", "abweichung": True}


def test_nicht_gemeldet_ist_nicht_gleich():
    v = abholer.modus_vermerk(_erg("bild_und_tiefe", None, None))
    assert v == {"bestellt": "bild_und_tiefe", "gerechnet": None, "abweichung": None}


def test_fehlt_die_abweichung_wird_sie_aus_beiden_werten_gelesen():
    assert abholer.modus_vermerk(_erg("txt2img", "tiefe_als_bild"))["abweichung"] is True
    assert abholer.modus_vermerk(_erg("txt2img", None))["abweichung"] is None


def test_ohne_bestellten_modus_kein_vermerk():
    assert abholer.modus_vermerk({}) is None
    assert abholer.modus_vermerk(None) is None
    assert abholer.modus_vermerk({"modus_gerechnet": "txt2img"}) is None


def test_die_form_des_bildmodells_passt_zum_vermerk():
    """Was ``render._ergebnis`` schreibt, liest der Vermerk — dieselben drei Woerter."""
    erg = render._ergebnis("ok", {"seed": 0, "backbone": "x", "modus": "image_edit"},
                           modus_bestellt="image_edit", modus_gerechnet="txt2img")
    assert abholer.modus_vermerk(erg) == {"bestellt": "image_edit", "gerechnet": "txt2img",
                                          "abweichung": True}


# ====================================================================== A1 · am Auftrag

def _u(kamera, bestellt, gerechnet):
    return {"kamera": kamera, abholer.URTEIL_MODUS: abholer.modus_vermerk(
        _erg(bestellt, gerechnet))}


def test_alle_gleich_oben_der_gemeinsame_wert():
    m = abholer.modus_des_auftrags([_u("sSE", "image_edit", "image_edit"),
                                    _u("nNW", "image_edit", "image_edit")])
    assert m == {"bestellt": "image_edit", "gerechnet": "image_edit", "abweichung": False,
                 "kameras": {"sSE": {"gerechnet": "image_edit", "abweichung": False},
                             "nNW": {"gerechnet": "image_edit", "abweichung": False}}}


def test_verschieden_oben_gerechnet_null_und_abweichung_true():
    m = abholer.modus_des_auftrags([_u("sSE", "image_edit", "txt2img"),
                                    _u("nNW", "image_edit", "image_edit")])
    assert m["bestellt"] == "image_edit"
    assert m["gerechnet"] is None and m["abweichung"] is True
    assert m["kameras"]["sSE"] == {"gerechnet": "txt2img", "abweichung": True}


def test_eine_kamera_ohne_meldung_macht_oben_unbekannt_nicht_gleich():
    m = abholer.modus_des_auftrags([_u("sSE", "image_edit", None),
                                    _u("nNW", "image_edit", "image_edit")])
    assert m["abweichung"] is None and m["gerechnet"] is None


def test_ohne_vermerk_fehlt_das_feld():
    assert abholer.modus_des_auftrags([{"kamera": "sSE"}]) is None
    assert "modus" not in abholer.angewandt_mit_messschaltern({"x": 1}, [{"kamera": "sSE"}])


def test_angewandt_traegt_den_modus_additiv():
    mit = abholer.angewandt_mit_messschaltern({"environment": {"preset": "abend"}},
                                              [_u("sSE", "txt2img", "txt2img")])
    assert mit["environment"] == {"preset": "abend"}
    assert mit["modus"]["gerechnet"] == "txt2img" and mit["modus"]["abweichung"] is False


def test_der_modus_kommt_durch_die_vertragsfassung():
    angewandt = abholer.angewandt_mit_messschaltern(None, [_u("sSE", "image_edit", "txt2img")])
    aus = kosmo_szene.nur_vertragsfelder(kosmo_szene.als_ergebnis(
        "vis-1-abcdef", [], geometrie_urteil={"kamera": "sSE"}, angewandt=angewandt))
    assert aus["angewandt"]["modus"]["kameras"]["sSE"]["abweichung"] is True


# ====================================================================== A1 · die Kette

def _mit_modus(attrappen, abweichend_bei=1):
    alt = attrappen["_rendere"]
    zaehler = {"n": 0}

    def rendere(a, **kw):
        erg = alt(a, **kw)
        zaehler["n"] += 1
        gerechnet = "txt2img" if zaehler["n"] == abweichend_bei else "tiefe_als_bild"
        return dict(erg, modus_bestellt="tiefe_als_bild", modus_gerechnet=gerechnet,
                    modus_abweichung=gerechnet != "tiefe_als_bild")

    return dict(attrappen, _rendere=rendere)


def test_die_kette_schreibt_den_modus_ins_ergebnis(tmp_path):
    ordner = _auftragsordner(tmp_path / "a")
    _protokoll, attrappen = _kette(tmp_path)
    antwort = _lauf(tmp_path, ordner, _mit_modus(attrappen))
    # A0051c (Mangel 3 der Gegenlese R3, «Immer vom Render»): Der Auftrag traegt den Bildeingang
    # (Vorgabe); meldet das Bildmodell etwas anderes als 'bild_und_tiefe', kam das Grundbild nicht
    # an — dann wird kein Bild geliefert. Die Zusammenfassung mit Abweichung je Kamera bleibt an
    # der reinen Funktion geprueft (test_der_modus_kommt_durch_die_vertragsfassung).
    assert antwort["tat"] != abholer.TAT_VERARBEITET
    assert kosmo_szene.SATZ_MASSTREUE in str(antwort["grund"])


def test_die_kette_schreibt_den_modus_vom_grundbild_ins_ergebnis(tmp_path):
    """A1 am Lauf, dessen Grundbild an jeder Kamera ankam (A0051c)."""
    ordner = _auftragsordner(tmp_path / "a")
    _protokoll, attrappen = _kette(tmp_path)
    alt = attrappen["_rendere"]

    def rendere(a, **kw):
        return dict(alt(a, **kw), modus_bestellt="bild_und_tiefe",
                    modus_gerechnet="bild_und_tiefe", modus_abweichung=False)

    antwort = _lauf(tmp_path, ordner, dict(attrappen, _rendere=rendere))
    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort["grund"]
    ergebnis = json.loads((ordner / bruecke.DATEI_ERGEBNIS).read_text(encoding="utf-8"))
    m = ergebnis["angewandt"]["modus"]
    assert m["bestellt"] == "bild_und_tiefe"
    assert m["gerechnet"] == "bild_und_tiefe" and m["abweichung"] is False
    assert set(m["kameras"]) <= {k["kamera"] for k in ergebnis["qa_je_kamera"]}


def test_ohne_meldung_des_bildmodells_bleibt_das_ergebnis_wie_es_war(tmp_path):
    ordner = _auftragsordner(tmp_path / "a")
    _protokoll, attrappen = _kette(tmp_path)
    antwort = _lauf(tmp_path, ordner, attrappen)
    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort["grund"]
    ergebnis = json.loads((ordner / bruecke.DATEI_ERGEBNIS).read_text(encoding="utf-8"))
    assert "modus" not in (ergebnis.get("angewandt") or {})


# ====================================================================== A2 · die gelesene Form

def test_umriss_halten_art_oben_und_angewandt_je_kamera():
    an = abholer.umriss_halten_vermerk_im_lauf(
        {"parameter": {"umriss_halten_schritte": 20}, "hinweise": ()}, {"rand_px": 19})
    aus = abholer.umriss_halten_vermerk_im_lauf(
        {"parameter": {"umriss_halten_schritte": 0}, "hinweise": ()}, {"rand_px": 19})
    uh = abholer.angewandt_mit_messschaltern(None, [
        {"kamera": "sSE", abholer.URTEIL_UMRISS_HALTEN: an},
        {"kamera": "nNW", abholer.URTEIL_UMRISS_HALTEN: aus}])["umriss_halten"]
    assert uh["art"] in ("nachher", "im_lauf", None)
    assert uh["kameras"]["sSE"]["angewandt"] is True
    assert uh["kameras"]["nNW"]["angewandt"] is False and uh["kameras"]["nNW"]["grund"]
    assert all(isinstance(v["angewandt"], bool) for v in uh["kameras"].values())
