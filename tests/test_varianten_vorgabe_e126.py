"""Entscheid 126 (Owner, Klickfrage A, 21.10.2026): **M2 mit Himmel ist die Vorgabe für Varianten.**

Fehlt ``vis.material_vorne``, ``vis.umriss_halten`` oder ``vis.himmel_sichtbar`` in der Bestellung
(oder steht ``null``), gilt am Heim-PC ``true`` / ``"im_lauf"`` / ``true``. Ein ausdrücklich
gesetzter Schalter gewinnt, auch «aus» (``false``). Wo ein Schalter fachlich nicht passt, entfällt
die Vorgabe mit Grund und **ohne** Mangel. Der Himmel gehört zur Grundlage: Eine Variante auf einer
Grundlage ohne Himmel wird nicht still ungültig — sie behält den Himmel der Grundlage, mit Satz,
oder wird laut abgewiesen, wenn der Schalter ausdrücklich anders bestellt war.

Kein Netz, keine GPU: nur ``lies_szene``, die Grundlage auf der Platte und ``als_ergebnis``.
"""
from __future__ import annotations

import json

import pytest

from aiimaging import abholer, kosmo_szene, stimmung


@pytest.fixture
def himmel(tmp_path, monkeypatch):
    ordner = tmp_path / "himmel"
    ordner.mkdir()
    for preset, eintrag in stimmung.STIMMUNGEN.items():
        for a in ("2k", "4k"):
            (ordner / stimmung.dateiname(preset, eintrag["hdri"], a)).write_bytes(b"#?RADIANCE\n")
    monkeypatch.setenv(stimmung.HIMMEL_ORDNER_ENV, str(ordner))
    return ordner


def _szene(preset="abend", prompt="exposed concrete house", **vis):
    render = {"environment": {"preset": preset}} if preset else {}
    return {"geometry": {"path": "/x/model.glb", "format": "glb"}, "cameras": "auto",
            "render": render, "style": {"prompt": prompt}, "vis": vis}


def _herkunft(s):
    return {k: v["herkunft"] for k, v in s["messschalter"].items()}


# ================================================================ die Vorgabe und wer gewinnt

def test_ohne_schalter_gilt_m2_mit_himmel(himmel):
    s = kosmo_szene.lies_szene(_szene())
    assert s["maengel"] == ()
    assert s["umriss_halten"] == "im_lauf" and s["himmel_sichtbar"] is True
    assert s["prompt"].startswith("monolithic exposed concrete building")
    assert _herkunft(s) == {"material_vorne": "vorgabe", "umriss_halten": "vorgabe",
                            "himmel_sichtbar": "vorgabe"}
    assert kosmo_szene.VARIANTEN_VORGABE == {"material_vorne": True, "umriss_halten": "im_lauf",
                                             "himmel_sichtbar": True}


def test_null_ist_wie_fehlend(himmel):
    s = kosmo_szene.lies_szene(_szene(material_vorne=None, umriss_halten=None,
                                      himmel_sichtbar=None))
    assert set(_herkunft(s).values()) == {"vorgabe"}


@pytest.mark.parametrize("name, aus, feld, wert_aus", [
    ("material_vorne", False, "prompt", "exposed concrete house"),
    ("umriss_halten", False, "umriss_halten", None),
    ("himmel_sichtbar", False, "himmel_sichtbar", False),
])
def test_ausdruecklich_aus_gewinnt(himmel, name, aus, feld, wert_aus):
    s = kosmo_szene.lies_szene(_szene(**{name: aus}))
    assert s["maengel"] == ()
    assert s[feld] == wert_aus if feld != "prompt" else not s[feld].startswith("monolithic")
    assert s["messschalter"][name] == {"herkunft": "bestellt"}
    # die beiden anderen bleiben Vorgabe
    assert [v for k, v in _herkunft(s).items() if k != name] == ["vorgabe", "vorgabe"]


def test_ausdruecklich_nachher_gewinnt_gegen_im_lauf(himmel):
    s = kosmo_szene.lies_szene(_szene(umriss_halten="nachher"))
    assert s["umriss_halten"] == "nachher"
    assert s["messschalter"]["umriss_halten"] == {"herkunft": "bestellt"}


# ================================================================ wo die Vorgabe entfällt (ohne Mangel)

def test_nur_grundlage_traegt_den_himmel_aber_kein_ki_schalter(himmel):
    s = kosmo_szene.lies_szene(_szene(skip=True))
    assert s["maengel"] == () and s["maengel_endgueltig"] == ()
    assert s["himmel_sichtbar"] is True                     # die Grundlage bekommt den Himmel
    assert s["umriss_halten"] is None
    assert not [z for z in s["prompt_zusaetze"] if z["art"] == "material_vorne"]
    assert _herkunft(s) == {"material_vorne": "vorgabe_entfaellt",
                            "umriss_halten": "vorgabe_entfaellt", "himmel_sichtbar": "vorgabe"}


def test_die_vorschau_haelt_den_umriss_nicht(himmel):
    s = kosmo_szene.lies_szene(_szene(guete="vorschau"))
    assert s["maengel"] == () and s["umriss_halten"] is None
    assert "Vorschau" in s["messschalter"]["umriss_halten"]["grund"]
    assert s["messschalter"]["material_vorne"] == {"herkunft": "vorgabe"}


def test_an_einem_ungemessenen_bildmodell_entfaellt_umriss_halten(himmel):
    s = kosmo_szene.lies_szene(_szene(backbone="qwen"))
    assert s["umriss_halten"] is None
    assert "nicht gemessen" in s["messschalter"]["umriss_halten"]["grund"]
    bestellt = kosmo_szene.lies_szene(_szene(backbone="qwen", umriss_halten="im_lauf"))
    assert bestellt["umriss_halten"] == "im_lauf"           # bestellt bleibt bestellt


def test_ohne_stimmung_kein_himmel_und_kein_mangel():
    s = kosmo_szene.lies_szene(_szene(preset=None))
    assert s["maengel"] == () and s["himmel_sichtbar"] is False
    assert "keine Stimmung" in s["messschalter"]["himmel_sichtbar"]["grund"]
    # ausdruecklich bestellt bleibt es ein endgueltiger Mangel (wie vor 126)
    r = kosmo_szene.lies_szene(_szene(preset=None, himmel_sichtbar=True))
    assert any("ohne 'render.environment'" in m for m in r["maengel_endgueltig"])


def test_das_gipsmodell_bleibt_vor_dem_verlauf(himmel):
    s = kosmo_szene.lies_szene(_szene(preset=stimmung.PRESET_WEISS))
    assert s["himmel_sichtbar"] is False
    assert "Gipsmodell" in s["messschalter"]["himmel_sichtbar"]["grund"]


def test_ohne_stoff_im_prompt_kein_leerer_zusatz(himmel):
    s = kosmo_szene.lies_szene(_szene(prompt="a quiet house"))
    assert not [z for z in s["prompt_zusaetze"] if z["art"] == "material_vorne"]
    assert s["messschalter"]["material_vorne"]["herkunft"] == "vorgabe_entfaellt"


# ================================================================ der Himmel steht in der Grundlage

def test_die_vorgabe_geht_in_die_lichtdaten(himmel):
    s = kosmo_szene.lies_szene(_szene())
    licht = json.loads(abholer.umgebung_einstellungen(s)["umgebung_licht"])
    assert licht["himmel_sichtbar"] is True


def test_die_grundlage_merkt_sich_den_himmel(tmp_path):
    pfad = abholer.lege_grundlage_ab(tmp_path, "gl-0123456789abcdef", job_id="j",
                                     szene={"himmel_sichtbar": True}, berichte={})
    assert json.loads(pfad.read_text(encoding="utf-8"))["himmel_sichtbar"] is True
    pfad = abholer.lege_grundlage_ab(tmp_path, "gl-0123456789abcdef", job_id="j",
                                     szene={}, berichte={})
    assert json.loads(pfad.read_text(encoding="utf-8"))["himmel_sichtbar"] is False


def _mit(herkunft, wert=True):
    return {"himmel_sichtbar": wert, "messschalter": {"himmel_sichtbar": {"herkunft": herkunft}}}


def test_variante_auf_alter_grundlage_ohne_himmel_behaelt_ihn_mit_satz():
    alt = {"id": "gl-0123456789abcdef"}                      # vor 126: ohne Feld
    szene, satz = abholer.himmel_der_grundlage(_mit("vorgabe"), alt)
    assert szene["himmel_sichtbar"] is False
    assert szene["messschalter"]["himmel_sichtbar"]["herkunft"] == "grundlage"
    assert satz.startswith("HIMMEL WIE IN DER GRUNDLAGE") and "neu rendern" in satz


def test_variante_mit_ausdruecklichem_himmel_auf_grundlage_ohne_wird_laut_abgewiesen():
    with pytest.raises(abholer.AbholerError, match="ohne sichtbaren Himmel"):
        abholer.himmel_der_grundlage(_mit("bestellt"), {"id": "gl-0123456789abcdef"})
    with pytest.raises(abholer.AbholerError, match="mit sichtbaren Himmel"):
        abholer.himmel_der_grundlage(_mit("bestellt", False),
                                     {"id": "gl-0123456789abcdef", "himmel_sichtbar": True})


def test_passt_der_himmel_bleibt_alles_wie_es_ist():
    szene = _mit("vorgabe")
    assert abholer.himmel_der_grundlage(szene, {"himmel_sichtbar": True}) == (szene, None)


# ================================================================ was gerechnet wurde, steht im Ergebnis

def test_angewandt_traegt_wert_und_herkunft(himmel):
    s = kosmo_szene.lies_szene(_szene(umriss_halten=False))
    ms = abholer.angewandt_der_szene(s)["messschalter"]
    assert ms["material_vorne"] == {"wert": True, "herkunft": "vorgabe"}
    assert ms["umriss_halten"] == {"wert": None, "herkunft": "bestellt"}
    assert ms["himmel_sichtbar"] == {"wert": True, "herkunft": "vorgabe"}


def test_der_himmelsatz_der_grundlage_steht_in_den_hinweisen():
    satz = "HIMMEL WIE IN DER GRUNDLAGE: x"
    angewandt = {"messschalter": {"himmel_sichtbar": {"wert": False, "herkunft": "grundlage",
                                                       "grund": satz}}}
    erg = kosmo_szene.als_ergebnis("j", [], angewandt=angewandt)
    assert satz in erg["hinweise"]


def test_ein_nicht_angewandter_vorgabe_umriss_bekommt_keinen_vorbehalt():
    vorgabe = {"kamera": "sSE", kosmo_szene.URTEIL_UMRISS_HALTEN: {
        "angewandt": False, "art": "im_lauf", "grund": "keine Bauwerksmaske", "vorgabe": True}}
    bestellt = {"kamera": "sSE", kosmo_szene.URTEIL_UMRISS_HALTEN: {
        "angewandt": False, "art": "im_lauf", "grund": "keine Bauwerksmaske"}}
    h1, h2 = [], []
    kosmo_szene._messschalter_eintragen(None, [vorgabe], h1)
    kosmo_szene._messschalter_eintragen(None, [bestellt], h2)
    assert not h1 and any("NICHT angewandt" in h for h in h2)


def test_ein_angewandter_vorgabe_umriss_sagt_vorgabe():
    u = {"kamera": "sSE", kosmo_szene.URTEIL_UMRISS_HALTEN: {
        "angewandt": True, "art": "im_lauf", "rand_px": 19, "vorgabe": True}}
    h = []
    kosmo_szene._messschalter_eintragen(None, [u], h)
    assert any("Vorgabe fuer Varianten (Entscheid 126)" in s for s in h)
    assert not any("Nie Vorgabe" in s for s in h)
