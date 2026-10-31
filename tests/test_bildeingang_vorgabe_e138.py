"""Entscheid 138 (Owner über die Zentrale, 22.10.2026): **Die KI-Variante geht vom Grundbild aus,
mit Stärke 0,5 als Vorgabe.**

Anlass: Messung auf-20261022-337 — ohne Bildeingang fielen die Fenster weg (Kanten im Haus
0,207), mit 0,5 hielt der Giebel (0,334, ein erfundenes Fenster an der Traufe, KI 13,5 s statt
16,3 s). Auflagen: Bildeingang 0,5 als Vorgabe für Varianten; **nie** an einem Modell mit offener
Lizenz oder Forschungslizenz; das Grundbild bleibt neben dem KI-Bild stehen (unverändert, W-4).
Ersetzt für Varianten Entscheid 117a. Eine eigene Stärke oder ``false`` bleibt bestellbar.

Ohne GPU: ``lies_szene`` und ein Lauf mit Attrappen, deren Bildmodell den Bildeingang meldet wie
die Pipeline am Heim-PC (``bild_und_tiefe`` mit der Stärke). Regel 3: alles synthetisch.
"""
from __future__ import annotations

import json
import types

import pytest

from aiimaging import abholer, backbone, bruecke, kosmo_szene, render

from test_kettenlauf_26august import _auftragsordner, _kette, _lauf
from test_varianten_vorgabe_e126 import _szene, himmel  # noqa: F401 — Fixture


def _lies(**vis):
    return kosmo_szene.lies_szene(_szene(**vis), streng=False)


# ================================================================ die Vorgabe in der Szene

def test_ohne_angabe_gilt_bildeingang_05(himmel):  # noqa: F811
    s = _lies()
    assert s["maengel"] == ()
    assert s["bildeingang"] == 0.5
    assert s["messschalter"]["bildeingang"] == {"herkunft": "vorgabe"}
    # Ohne Grundlage (erstes Bild) bleibt 0,5; Varianten rechnen seit Entscheid 149 mit 0,7.
    assert kosmo_szene.BILDEINGANG_VORGABE == 0.5
    assert kosmo_szene.VARIANTEN_VORGABE["bildeingang"] == kosmo_szene.BILDEINGANG_VORGABE_VARIANTE == 0.7


def test_null_ist_wie_fehlend(himmel):  # noqa: F811
    assert _lies(bildeingang=None)["bildeingang"] == 0.5


def test_eigene_staerke_gewinnt(himmel):  # noqa: F811
    s = _lies(bildeingang=0.65)
    assert s["bildeingang"] == 0.65 and s["maengel"] == ()
    assert s["messschalter"]["bildeingang"] == {"herkunft": "bestellt"}


def test_abschalten_mit_false(himmel):  # noqa: F811
    # Masstreue (A0051, Gegenlesen Runde 2): Abschalten war das freie Bild unter anderem Namen.
    s = _lies(bildeingang=False)
    assert s["bildeingang"] is None
    assert s["maengel"] == (kosmo_szene.masstreue_satz_bildeingang_aus(),)
    assert s["maengel_endgueltig"] == (kosmo_szene.masstreue_satz_bildeingang_aus(),)
    assert s["messschalter"]["bildeingang"] == {"herkunft": "bestellt"}


def test_true_ist_keine_staerke(himmel):  # noqa: F811
    s = _lies(bildeingang=True)
    assert s["bildeingang"] is None
    assert any("'vis.bildeingang' ist True" in m for m in s["maengel"])


def test_lizenz_offen_rechnet_ohne_bildeingang_mit_satz(himmel):  # noqa: F811
    assert backbone.hole("qwen-image-2.1").lizenz_offen
    s = _lies(backbone="qwen-image-2.1")
    # A0051b («Immer vom Render», Owner-Entscheid 31.10.2026): ohne Bildeingang kein Lauf — die Bestellung endet
    # mit dem Satz der Masstreue; der Grund der entfallenen Vorgabe bleibt im Befund.
    assert s["bildeingang"] is None
    assert any(m.startswith(kosmo_szene.SATZ_MASSTREUE) for m in s["maengel_endgueltig"])
    ms = s["messschalter"]["bildeingang"]
    assert ms["herkunft"] == "vorgabe_entfaellt"
    assert ms["grund"].startswith(kosmo_szene.SATZ_BILDEINGANG_LIZENZ)
    assert "offener Lizenz" in ms["grund"]
    assert any(w.startswith(kosmo_szene.SATZ_BILDEINGANG_LIZENZ) for w in s["warnungen"])
    # ... und der Satz steht im Ergebnis (qa.verdict.hinweise), nicht nur im Befund.
    angewandt = abholer.angewandt_der_szene(s)
    assert kosmo_szene.ergebnis_saetze_der_szene(angewandt)[0].startswith(
        kosmo_szene.SATZ_BILDEINGANG_LIZENZ)


def test_forschungslizenz_rechnet_ohne_bildeingang(monkeypatch):
    echt = backbone.hole("z-image-turbo")
    attrappe = types.SimpleNamespace(**{f: getattr(echt, f) for f in (
        "name", "bildeingang_weg")}, lizenz_offen=None, nur_forschung="Forschungs-Ausnahme")
    monkeypatch.setattr(backbone, "hole", lambda name: attrappe)
    grund = kosmo_szene.bildeingang_vorgabe_entfaellt(guete="voll", backbone="z-image-turbo")
    assert grund.startswith(kosmo_szene.SATZ_BILDEINGANG_LIZENZ) and "Forschungslizenz" in grund


@pytest.mark.parametrize("vis, wort, masstreue", [
    # A0051b («Immer vom Render», Owner-Entscheid 31.10.2026): an einem Modell ohne Weg endet
    # die Bestellung an der Masstreue; die Vorschau startet seither vom Grundbild (Vorgabe, kein
    # Entfallen mehr — geprueft in test_masstreue_a0051).
    ({"backbone": "flux2-klein"}, "kein Weg vorbereitet", True),
    ({"skip": True}, "Nur Grundlage", False),
])
def test_wo_die_vorgabe_entfaellt(himmel, vis, wort, masstreue):  # noqa: F811
    s = _lies(**vis)
    assert s["bildeingang"] is None
    assert any(m.startswith(kosmo_szene.SATZ_MASSTREUE) for m in s["maengel"]) is masstreue
    ms = s["messschalter"]["bildeingang"]
    assert ms["herkunft"] == "vorgabe_entfaellt" and wort in ms["grund"]
    assert not any(w.startswith(kosmo_szene.SATZ_BILDEINGANG_LIZENZ) for w in s["warnungen"])


def test_stoff_variante_und_bildeingang_zusammen(tmp_path, monkeypatch):
    """C174 + 138/149: neue Grundlage mit dem Wunschstoff — eine Variante, Bildeingang 0,7."""
    from test_material_der_variante_337 import HOLZ, PROMPT_337_S, _alle_himmel, _lies as lies337
    from test_knoten_material import _texturen
    _alle_himmel(tmp_path, monkeypatch)
    _texturen(tmp_path, monkeypatch)
    s = lies337(PROMPT_337_S, HOLZ, grundlage="gl-0123456789abcdef", seed=7)
    assert s["material_der_variante"]["ersetzung"] == "materialwahl"
    assert s["grundlage"] is None, "die Grundlage wird neu gerechnet"
    assert s["materialien"]["fassade"]["id"] == "sichtbeton-schalungsglatt"
    assert s["bildeingang"] == 0.7 and s["messschalter"]["bildeingang"]["herkunft"] == "vorgabe"
    angewandt = abholer.angewandt_der_szene(s)
    assert angewandt["variante"]["satz"].startswith(kosmo_szene.SATZ_MATERIAL_DER_VARIANTE)


# ================================================================ im Lauf (Attrappen)

def _mit_bildeingang_meldung(attrappen):
    """Das Bildmodell meldet wie am Heim-PC: mit Stärke ``bild_und_tiefe``, sonst ``txt2img``."""
    alt = attrappen["_rendere"]

    def rendere(a, **kw):
        erg = alt(a, **kw)
        mit = a.bildeingang_staerke is not None
        modus = render.MODUS_BILD_UND_TIEFE if mit else render.MODUS_TXT2IMG
        return dict(erg, backbone=a.backbone,
                    modus_bestellt=modus if mit else render.MODUS_IMAGE_EDIT,
                    modus_gerechnet=modus, modus_abweichung=not mit,
                    parameter={"bildeingang_staerke": a.bildeingang_staerke, "denoise": 0.6,
                               "bildeingang_weg": "eigener_start" if mit else None,
                               "controlnet_staerke": 1.0})

    return dict(attrappen, _rendere=rendere)


def _lauf_mit(tmp_path, **vis):
    ordner = _auftragsordner(tmp_path / "a")
    pfad = ordner / bruecke.DATEI_SZENE
    szene = json.loads(pfad.read_text(encoding="utf-8"))
    szene["vis"].update(vis)
    pfad.write_text(json.dumps(szene), encoding="utf-8")
    protokoll, attrappen = _kette(tmp_path / "k")
    antwort = _lauf(tmp_path / "l", ordner, _mit_bildeingang_meldung(attrappen))
    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort["grund"]
    return antwort, protokoll


def test_variante_ohne_angabe_rechnet_img2img_05(tmp_path):
    antwort, protokoll = _lauf_mit(tmp_path)
    assert protokoll["render"] and all(a.bildeingang_staerke == 0.5 for a in protokoll["render"])
    angewandt = antwort["ergebnis"]["angewandt"]
    assert angewandt["ki"]["modus"] == "img2img" and angewandt["ki"]["denoise"] == 0.5
    assert angewandt["ki"]["rueckfall"] is False and not angewandt["ki"].get("warnungen")
    assert angewandt["bildeingang"]["staerke"] == 0.5
    assert angewandt["messschalter"]["bildeingang"] == {"wert": 0.5, "herkunft": "vorgabe"}
    # Seit Ergebnis 357 traegt auch die Vorgabe ihren Satz — mit ihrer Herkunft (hier das erste
    # Bild ohne Grundlage, 0,5 nach Entscheid 138), nicht «Bestellt.».
    hinweise = antwort["ergebnis"]["qa"]["verdict"].get("hinweise", [])
    assert any(h.startswith(kosmo_szene.SATZ_BILDEINGANG)
               and h.endswith("Vorgabe fuer das erste Bild (herkunft vorgabe, Entscheid 138).")
               for h in hinweise), hinweise


def test_abgeschaltet_rechnet_wie_vorher_mit_rueckfall_warnung(tmp_path):
    # Masstreue (A0051, Gegenlesen Runde 2): abgeschaltet wird nicht mehr gerechnet.
    with pytest.raises(AssertionError, match="MASSTREUE"):
        _lauf_mit(tmp_path, bildeingang=False)


def test_eigene_staerke_im_lauf(tmp_path):
    antwort, protokoll = _lauf_mit(tmp_path, bildeingang=0.65)
    assert all(a.bildeingang_staerke == 0.65 for a in protokoll["render"])
    assert antwort["ergebnis"]["angewandt"]["ki"]["denoise"] == 0.65
    hinweise = antwort["ergebnis"]["qa"]["verdict"].get("hinweise", [])
    assert any(h.startswith(kosmo_szene.SATZ_BILDEINGANG) and h.endswith("Bestellt.")
               for h in hinweise)


def test_lizenz_offen_im_lauf_ohne_bildeingang(tmp_path):
    # A0051b («Immer vom Render», Owner-Entscheid 31.10.2026): ohne Bildeingang wird nicht gerechnet.
    with pytest.raises(AssertionError, match="MASSTREUE"):
        _lauf_mit(tmp_path, backbone="qwen-image-2.1")


# ================================================================ die Karte reicht nicht

def test_vorgabe_wird_zurueckgezogen_statt_abgewiesen():
    # A0051b («Immer vom Render», Owner-Entscheid 31.10.2026): der Rueckfall ohne Grundbild ist entfernt; die
    # Vorgabe wird wie ein bestellter Bildeingang abgewiesen (test_volle_karte_vorgabe_rechnet_ohne).
    szene = {"bildeingang": 0.5, "messschalter": {"bildeingang": {"herkunft": "vorgabe"}}}
    assert abholer._bildeingang_aus_vorgabe(szene)
    assert not hasattr(abholer, "bildeingang_vorgabe_zurueckziehen")
    assert not abholer._bildeingang_aus_vorgabe(
        {"bildeingang": 0.5, "messschalter": {"bildeingang": {"herkunft": "bestellt"}}})


def _voll_belegt():
    return {"frei_mib": 2000, "eigen_mib": 0, "fremde_modelle": []}


def test_volle_karte_vorgabe_rechnet_ohne(tmp_path):
    ordner = _auftragsordner(tmp_path / "a")
    protokoll, attrappen = _kette(tmp_path / "k")
    antwort = abholer.hole_einen(ordner, fremde_freigabe_gilt=True,
                                 verarbeite=_verarbeite(tmp_path, attrappen),
                                 bildeingang_karte=_voll_belegt)
    # A0051b («Immer vom Render», Owner-Entscheid 31.10.2026): kein Rueckfall ohne Grundbild — abgewiesen mit Satz.
    assert antwort["tat"] != abholer.TAT_VERARBEITET
    assert not protokoll["render"]
    assert kosmo_szene.SATZ_MASSTREUE in antwort["grund"]


def test_volle_karte_bestellt_wird_abgewiesen(tmp_path):
    ordner = _auftragsordner(tmp_path / "a")
    pfad = ordner / bruecke.DATEI_SZENE
    szene = json.loads(pfad.read_text(encoding="utf-8"))
    szene["vis"]["bildeingang"] = 0.5
    pfad.write_text(json.dumps(szene), encoding="utf-8")
    protokoll, attrappen = _kette(tmp_path / "k")
    antwort = abholer.hole_einen(ordner, fremde_freigabe_gilt=True,
                                 verarbeite=_verarbeite(tmp_path, attrappen),
                                 bildeingang_karte=_voll_belegt)
    assert antwort["tat"] != abholer.TAT_VERARBEITET
    assert not protokoll["render"]


def _verarbeite(tmp_path, attrappen):
    return abholer.verarbeiter(out_wurzel=tmp_path / "aus", nullprobe=False, **attrappen)


# ================================================================ Befund 339: Saetze im Ergebnis

def test_form_weicht_ab_steht_als_satz_im_ergebnis():
    """339 KS: Kanten 0,142, ein anderes Haus — hiess «deckungsgleich». Jetzt ein Satz."""
    hinweise: list = []
    kosmo_szene._deckung_eintragen(None, [{"kamera": "sSE", "deckung": 0.1422},
                                          {"kamera": "nNW", "deckung": 0.4808}], hinweise)
    assert len(hinweise) == 1 and hinweise[0].startswith(kosmo_szene.SATZ_FORM_WEICHT_AB)
    assert "'sSE'" in hinweise[0] and "0.25" in hinweise[0]


def test_der_satz_der_stoff_variante_kommt_ins_ergebnis():
    angewandt = {"variante": {"material_wunsch": {"id": "x"},
                              "satz": "MATERIAL DER VARIANTE: Sichtbeton statt Holz."}}
    assert kosmo_szene.ergebnis_saetze_der_szene(angewandt) == [
        "MATERIAL DER VARIANTE: Sichtbeton statt Holz."]
    assert kosmo_szene.ergebnis_saetze_der_szene(None) == []
