"""Die zwei Ausnahmen zu Regel 1 für nicht verkaufbare Gewichte.

**Forschungs-Ausnahme** (Owner-Entscheid 29.09.2026, ``Backbone.nur_forschung``): lädt nur mit
dem Schalter ``AIIMAGING_FORSCHUNGSMODELLE=1``, nie über KosmoOrbit, jeder Lauf markiert. Heute
trägt sie kein Registereintrag mehr — geprüft wird sie an einer Kopie, damit der Mechanismus
nicht still verrottet, bis ihn das nächste Forschungsmodell braucht.

**Einbau mit offener Lizenz** (Owner-Entscheid E128, 30.09.2026, ``Backbone.lizenz_offen``):
Qwen-Image-2.1 ist regulär bestellbar, auch über KosmoOrbit, ohne Schalter — aber nie Vorgabe,
``pruefe_lizenz`` sagt weiter «nicht im Produkt», und jedes Ergebnis trägt
``engine_license_open: true``, damit drüben eine Veröffentlichung gesperrt bleibt, bis die
Lizenz gelöst ist.
"""
from __future__ import annotations

import dataclasses

import pytest

from aiimaging import abholer, backbone, kosmo_szene

QWEN = "qwen-image-2.1"
AN = {backbone.FORSCHUNG_SCHALTER: "1"}


# ======================================================================================
# 1 · Einbau mit offener Lizenz (E128)
# ======================================================================================

@pytest.mark.parametrize("umgebung", [{}, AN])
def test_qwen_laedt_ohne_schalter_und_traegt_die_marke(umgebung):
    aus = backbone.ladefreigabe(QWEN, umgebung=umgebung)
    assert aus["darf"] is True and aus["lizenz_offen"] is True and aus["forschung"] is False
    assert aus["begruendung"].startswith("LIZENZ OFFEN")


def test_das_produkturteil_bleibt_nein():
    assert backbone.pruefe_lizenz(QWEN)["zulaessig"] is False
    assert backbone.hole(QWEN).kommerziell_nutzbar is False


def test_nie_vorgabe_und_nie_im_kommerziellen_angebot():
    assert QWEN not in {backbone.VORGABE_BACKBONE, backbone.VORSCHAU_BACKBONE,
                        backbone.RUECKFALL_BACKBONE}
    assert QWEN not in {b.name for b in backbone.waehle(kommerziell=True)}


def test_kosmoorbit_kann_es_bestellen():
    urteil = kosmo_szene.backbone_von_fremd(QWEN)
    assert urteil["name"] == QWEN and urteil["zulaessig"] is True


@pytest.mark.parametrize("name", ["flux1-dev", "flux2-dev"])
def test_die_uebrigen_ausgeschlossenen_bleiben_draussen(name):
    assert backbone.ladefreigabe(name, umgebung=AN)["darf"] is False


def test_verkaufbare_modelle_tragen_keine_marke():
    aus = backbone.ladefreigabe(backbone.VORGABE_BACKBONE, umgebung={})
    assert aus["darf"] is True and aus["lizenz_offen"] is False


def test_die_marke_reist_bis_ins_ergebnis():
    """Vom Renderergebnis über den Abholer in die Vertragsfelder — nur wenn wahr."""
    lauf = {"backbone": QWEN, "lizenz": {"lizenz": "Qwen Research License Agreement"},
            "parameter": {"lizenz_offen": True}}
    engine = abholer._engine_aus(lauf)
    felder = kosmo_szene.engine_felder(engine)
    assert felder == {"engine_used": QWEN, "engine_license": "Qwen Research License Agreement",
                      "engine_license_open": True}
    frei = kosmo_szene.engine_felder(abholer._engine_aus(
        {"backbone": "z-image-turbo", "lizenz": {"lizenz": "Apache-2.0"}, "parameter": {}}))
    assert "engine_license_open" not in frei, "kein false — das hiesse «geprüft und frei»"


def test_der_renderweg_nimmt_qwen_an_und_markiert_den_lauf(monkeypatch, tmp_path):
    from aiimaging import render
    monkeypatch.delenv(backbone.FORSCHUNG_SCHALTER, raising=False)
    tiefe = tmp_path / "tiefe.png"
    tiefe.write_bytes(b"x")
    a = render.RenderAuftrag(backbone=QWEN, depth_png=str(tiefe), prompt="a house",
                             ausgabe_png=str(tmp_path / "aus.png"))
    assert not any("Regel 1" in m for m in render.pruefe_auftrag(a))


@pytest.mark.parametrize("aenderung", [
    {"kommerziell_nutzbar": True, "lizenz": "Apache-2.0"},     # verkaufbar braucht keine
    {"lizenz_offen": "   "},                                   # Freigabe ohne Satz
    {"nur_forschung": "Forschung"},                            # nicht beides zugleich
])
def test_eine_leere_oder_widerspruechliche_freigabe_kommt_nicht_ins_register(
        monkeypatch, aenderung):
    monkeypatch.setattr(backbone, "BACKBONES", dict(backbone.BACKBONES))
    kopie = dataclasses.replace(backbone.BACKBONES[QWEN], name="probe-kopie", **aenderung)
    with pytest.raises(backbone.BackboneError):
        backbone._eintrag(kopie)


# ======================================================================================
# 2 · Die Forschungs-Ausnahme bleibt als Mechanismus — an einer Kopie geprüft
# ======================================================================================

@pytest.fixture
def forschung(monkeypatch):
    monkeypatch.setattr(backbone, "BACKBONES", dict(backbone.BACKBONES))
    backbone._eintrag(dataclasses.replace(
        backbone.BACKBONES[QWEN], name="probe-forschung", lizenz_offen=None,
        nur_forschung="Probe: nur fuer die Forschung."))
    return "probe-forschung"


def test_ohne_schalter_wird_ein_forschungsmodell_nicht_geladen(forschung):
    aus = backbone.ladefreigabe(forschung, umgebung={})
    assert aus["darf"] is False and backbone.FORSCHUNG_SCHALTER in aus["begruendung"]


@pytest.mark.parametrize("wert", ["0", "true", "ja", ""])
def test_nur_die_eins_schaltet(forschung, wert):
    assert backbone.ladefreigabe(
        forschung, umgebung={backbone.FORSCHUNG_SCHALTER: wert})["darf"] is False


def test_mit_schalter_geladen_und_als_forschung_markiert(forschung):
    aus = backbone.ladefreigabe(forschung, umgebung=AN)
    assert aus["darf"] is True and aus["forschung"] is True and aus["lizenz_offen"] is False
    assert aus["begruendung"].startswith("NUR FORSCHUNG")


def test_eine_leere_forschungsausnahme_kommt_nicht_ins_register(monkeypatch):
    monkeypatch.setattr(backbone, "BACKBONES", dict(backbone.BACKBONES))
    kopie = dataclasses.replace(backbone.BACKBONES[QWEN], name="probe-kopie",
                                lizenz_offen=None, nur_forschung="   ")
    with pytest.raises(backbone.BackboneError, match="nur_forschung"):
        backbone._eintrag(kopie)
