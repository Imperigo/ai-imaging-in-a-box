"""Befund auf-20261021-312 B3 / 313 B4: bestellt ``image_edit``, gerechnet ``txt2img`` — und
das Ergebnis sagte nichts dazu.

**Die Ursache, aus Code und Register:** Der Produktweg «Variante» gibt das Cycles-Bild der
Grundlage immer als ``beauty_png`` mit; damit ist ``image_edit`` bestellt
(``render._baue_parameter``). Die Vorgabe ``z-image-turbo`` hat keinen Eingang für ein
Ausgangsbild (``bildeingang_traegt=False``, gemessen auf-20260919-123) — die Naht verwirft es,
und es rechnet ein Text-zu-Bild-Lauf, an die Grundlage gebunden nur über die Tiefe. Der Weg,
auf dem das Bild ankommt (``bildeingang_weg='eigener_start'``), läuft nur mit dem Messschalter
``vis.bildeingang``; in 312/313 war keiner gesetzt. Die Speicherschwelle des Bildeingangs
(28116 MiB) spielte darum keine Rolle: Sie gilt nur mit Schalter, und die Spitze der Läufe
(27551 MiB) ist die des Laufs ohne Bildeingang.

Jetzt sagt der Lauf es mit einem Satz in ``qa.verdict.hinweise`` und im Befund je Kamera.
Testdaten synthetisch (Regel 3), Blender und Bildmodell als Attrappen (Regel 2).
"""
from __future__ import annotations

import json

from aiimaging import abholer, backbone, bruecke, kosmo_szene, render

from test_kettenlauf_26august import _auftragsordner, _kette, _lauf

ABWEICHEND = {"bestellt": "image_edit", "gerechnet": "txt2img", "abweichung": True}


# ====================================================================== die Ursache

def test_die_vorgabe_traegt_kein_ausgangsbild_und_der_weg_braucht_den_schalter():
    eintrag = backbone.hole(backbone.VORGABE_BACKBONE)
    assert eintrag.bildeingang_traegt is False
    assert eintrag.bildeingang_weg == backbone.BILDEINGANG_EIGENER_START


def test_mit_cycles_bild_ist_image_edit_bestellt_ohne_schalter_kein_eigener_start():
    eintrag = backbone.hole(backbone.VORGABE_BACKBONE)
    ohne = render._baue_parameter(render.RenderAuftrag(
        depth_png="t.png", prompt="Haus", beauty_png="b.png"), eintrag)
    assert ohne["modus"] == render.MODUS_IMAGE_EDIT
    assert "bildeingang_weg" not in ohne
    mit = render._baue_parameter(render.RenderAuftrag(
        depth_png="t.png", prompt="Haus", beauty_png="b.png", bildeingang_staerke=0.4),
        eintrag)
    assert mit["modus"] == render.MODUS_BILD_UND_TIEFE


# ====================================================================== der Satz

def test_der_satz_nennt_bestellt_gerechnet_und_den_grund_aus_dem_register():
    satz = kosmo_szene.modus_satz("sSE", ABWEICHEND, "z-image-turbo")
    assert satz.startswith(kosmo_szene.SATZ_OHNE_GRUNDLAGENBILD)
    assert "'image_edit'" in satz and "'txt2img'" in satz and "NICHT angekommen" in satz
    assert "nur die Tiefenkarte" in satz
    assert backbone.hole("z-image-turbo").bildeingang_grund in satz
    assert "vis.bildeingang" in satz and "nicht Vorgabe" in satz


def test_ohne_abweichung_oder_ohne_meldung_kein_satz():
    assert kosmo_szene.modus_satz("s", dict(ABWEICHEND, abweichung=False), "z-image-turbo") \
        is None
    assert kosmo_szene.modus_satz("s", dict(ABWEICHEND, abweichung=None)) is None
    assert kosmo_szene.modus_satz("s", None) is None


def test_ein_unbekanntes_modell_bekommt_den_satz_ohne_grund():
    satz = kosmo_szene.modus_satz("s", ABWEICHEND, "gibt-es-nicht")
    assert satz.startswith(kosmo_szene.SATZ_OHNE_GRUNDLAGENBILD) and "Grund:" not in satz


def test_der_satz_steht_in_verdict_hinweise():
    urteil = {"kamera": "sSE", "modus": ABWEICHEND, "engine": {"name": "z-image-turbo"}}
    erg = kosmo_szene.als_ergebnis("vis-1-abcdef", [], geometrie_urteil=urteil)
    hinweise = erg["qa"]["verdict"].get("hinweise") or []
    assert any(h.startswith(kosmo_szene.SATZ_OHNE_GRUNDLAGENBILD) for h in hinweise)
    aus = kosmo_szene.nur_vertragsfelder(erg)
    assert any(h.startswith(kosmo_szene.SATZ_OHNE_GRUNDLAGENBILD)
               for h in aus["qa"]["verdict"]["hinweise"])


def test_ohne_abweichung_bleibt_das_verdict_ohne_satz():
    urteil = {"kamera": "sSE", "modus": dict(ABWEICHEND, gerechnet="image_edit",
                                              abweichung=False)}
    erg = kosmo_szene.als_ergebnis("vis-1-abcdef", [], geometrie_urteil=urteil)
    assert not any(h.startswith(kosmo_szene.SATZ_OHNE_GRUNDLAGENBILD)
                   for h in erg["qa"]["verdict"].get("hinweise") or [])


def test_mit_messschalter_bildeingang_nur_dessen_satz():
    urteil = {"kamera": "sSE", "modus": dict(ABWEICHEND, bestellt="bild_und_tiefe"),
              "bildeingang": {"staerke": 0.4, "modus_bestellt": "bild_und_tiefe",
                              "modus_gerechnet": "txt2img", "modus_abweichung": True}}
    erg = kosmo_szene.als_ergebnis("vis-1-abcdef", [], geometrie_urteil=urteil)
    hinweise = erg["qa"]["verdict"].get("hinweise") or []
    assert any(h.startswith(kosmo_szene.SATZ_BILDEINGANG) for h in hinweise)
    assert not any(h.startswith(kosmo_szene.SATZ_OHNE_GRUNDLAGENBILD) for h in hinweise)


# ====================================================================== die Kette

def _abweichend(attrappen):
    alt = attrappen["_rendere"]

    def rendere(a, **kw):
        erg = alt(a, **kw)
        return dict(erg, backbone="z-image-turbo", modus_bestellt="image_edit",
                    modus_gerechnet="txt2img", modus_abweichung=True)

    return dict(attrappen, _rendere=rendere)


def test_die_kette_schreibt_den_satz_ins_ergebnis_und_angewandt_bleibt_c17(tmp_path):
    ordner = _auftragsordner(tmp_path / "a")
    _protokoll, attrappen = _kette(tmp_path)
    antwort = _lauf(tmp_path, ordner, _abweichend(attrappen))
    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort["grund"]
    ergebnis = json.loads((ordner / bruecke.DATEI_ERGEBNIS).read_text(encoding="utf-8"))
    hinweise = ergebnis["qa"]["verdict"]["hinweise"]
    saetze = [h for h in hinweise if h.startswith(kosmo_szene.SATZ_OHNE_GRUNDLAGENBILD)]
    assert saetze and all("'txt2img'" in s for s in saetze)
    m = ergebnis["angewandt"]["modus"]
    assert set(m) == {"bestellt", "gerechnet", "abweichung", "kameras"}
    assert all(set(v) == {"gerechnet", "abweichung"} for v in m["kameras"].values())
