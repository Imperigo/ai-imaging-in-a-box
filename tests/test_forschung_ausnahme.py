"""Die Forschungs-Ausnahme zu Regel 1 — Owner-Entscheid 29.09.2026.

«Wir sind noch lange nicht im Verkauf»: Qwen-Image-2.1 (Qwen Research License, nur
Forschung) darf für die Vertiefungsarbeit rechnen — aber nur unter vier Auflagen, und
jede ist hier eine Probe:

1. nur mit gesetztem Schalter (``AIIMAGING_FORSCHUNGSMODELLE=1``),
2. nie als Vorgabe und nie über ``waehle(kommerziell=True)``,
3. nie über den Bestellweg von KosmoOrbit,
4. ``pruefe_lizenz`` sagt weiter «nicht im Produkt», und jeder Lauf trägt die Marke.
"""
from __future__ import annotations

import dataclasses

import pytest

from aiimaging import backbone, kosmo_szene

NAME = "qwen-image-2.1"
AN = {backbone.FORSCHUNG_SCHALTER: "1"}


def test_ohne_schalter_wird_nicht_geladen():
    aus = backbone.ladefreigabe(NAME, umgebung={})
    assert aus["darf"] is False and aus["forschung"] is False
    assert backbone.FORSCHUNG_SCHALTER in aus["begruendung"]


@pytest.mark.parametrize("wert", ["0", "true", "ja", ""])
def test_nur_die_eins_schaltet(wert):
    assert backbone.ladefreigabe(NAME, umgebung={backbone.FORSCHUNG_SCHALTER: wert})[
        "darf"] is False


def test_mit_schalter_wird_geladen_und_markiert():
    aus = backbone.ladefreigabe(NAME, umgebung=AN)
    assert aus["darf"] is True and aus["forschung"] is True
    assert aus["begruendung"].startswith("NUR FORSCHUNG")


def test_das_produkturteil_bleibt_nein():
    urteil = backbone.pruefe_lizenz(NAME)
    assert urteil["zulaessig"] is False
    assert backbone.hole(NAME).kommerziell_nutzbar is False


@pytest.mark.parametrize("name", ["flux1-dev", "flux2-dev"])
def test_der_schalter_oeffnet_keine_anderen_ausgeschlossenen(name):
    """Die Ausnahme gilt je Eintrag, nicht für alles Nicht-Kommerzielle."""
    assert backbone.ladefreigabe(name, umgebung=AN)["darf"] is False


def test_verkaufbare_modelle_brauchen_keinen_schalter():
    aus = backbone.ladefreigabe(backbone.VORGABE_BACKBONE, umgebung={})
    assert aus["darf"] is True and aus["forschung"] is False


def test_nie_vorgabe_und_nie_im_kommerziellen_angebot():
    assert NAME not in {backbone.VORGABE_BACKBONE, backbone.VORSCHAU_BACKBONE,
                        backbone.RUECKFALL_BACKBONE}
    assert NAME not in {b.name for b in backbone.waehle(kommerziell=True)}


def test_nie_ueber_den_bestellweg_von_kosmoorbit():
    assert NAME not in kosmo_szene.BACKBONE_VON_FREMD.values()


@pytest.mark.parametrize("aenderung", [
    {"kommerziell_nutzbar": True, "lizenz": "Apache-2.0"},   # verkaufbar braucht keine
    {"nur_forschung": "   "},                                # Ausnahme ohne Satz
])
def test_eine_leere_oder_unnoetige_ausnahme_kommt_nicht_ins_register(monkeypatch, aenderung):
    monkeypatch.setattr(backbone, "BACKBONES", dict(backbone.BACKBONES))
    kopie = dataclasses.replace(backbone.BACKBONES[NAME], name="probe-kopie", **aenderung)
    with pytest.raises(backbone.BackboneError, match="nur_forschung"):
        backbone._eintrag(kopie)


def test_der_renderweg_lehnt_ohne_schalter_ab(monkeypatch, tmp_path):
    from aiimaging import render
    monkeypatch.delenv(backbone.FORSCHUNG_SCHALTER, raising=False)
    tiefe = tmp_path / "tiefe.png"
    tiefe.write_bytes(b"x")
    a = render.RenderAuftrag(backbone=NAME, depth_png=str(tiefe), prompt="a house",
                             ausgabe_png=str(tmp_path / "aus.png"))
    maengel = render.pruefe_auftrag(a)
    assert any("Regel 1" in m and backbone.FORSCHUNG_SCHALTER in m for m in maengel), maengel

    monkeypatch.setenv(backbone.FORSCHUNG_SCHALTER, "1")
    assert not any("Regel 1" in m for m in render.pruefe_auftrag(a))
