"""Das Paarurteil urteilt nicht mehr — Owner-Entscheid 30.09.2026 («a sofort»).

Befund der HomeStation (``auf-20260929-175``): Für ρ über der Maske gibt es an erzeugten
Bildern weder frontal noch diagonal ein fehlerfreies Fenster; die Schwelle 0,80 trägt
nirgends. Seit dem 29.09. trug ρ das Paarurteil allein. Jetzt: ρ wird gemessen und
gezeigt, ``bestanden`` bleibt ``None``, und kein Satz spricht von «durchgefallen».
"""
from __future__ import annotations

import pytest

from aiimaging import geometrie_qa


def _paar(rho):
    return geometrie_qa.paarurteil({"gerichtet": rho}, {"gerichtet": 0.01},
                                   anteil_ergebnis={"anteil": 0.2})


def test_die_vorgabe_urteilt_nicht():
    assert geometrie_qa.PAARURTEIL_URTEILT is False


@pytest.mark.parametrize("rho", [0.95, 0.80, 0.10, -0.60])
def test_kein_bestanden_und_kein_durchgefallen(rho):
    """Auch über der Schwelle kein «bestanden» — das wäre dieselbe Behauptung."""
    aus = _paar(rho)
    assert aus["gemessen"] is True and aus["bestanden"] is None and aus["traeger"] is None
    assert aus["urteilt"] is False and aus["rho"] == rho
    assert aus["begruendung"].startswith("NICHT GEEICHT, NUR AUSKUNFT")
    assert "auf-20260929-175" in aus["begruendung"]


def test_ohne_rho_nicht_gemessen():
    aus = geometrie_qa.paarurteil(None, None)
    assert aus["gemessen"] is False and aus["bestanden"] is None
    assert aus["begruendung"].startswith("NICHT GEMESSEN")


def test_die_alte_form_bleibt_ausdruecklich_erreichbar():
    aus = geometrie_qa.paarurteil({"gerichtet": 0.5}, {"gerichtet": 0.01},
                                  anteil_ergebnis={"anteil": 0.2}, urteilt=True)
    assert aus["bestanden"] is False and aus["traeger"] == "rho"


def test_der_grund_im_vertrag_sagt_ungeprueft():
    from aiimaging import kosmo_szene
    urteil = {"status": "ok", "score": None, "bestanden": False, "geom_iou": 0.0,
              "spearman": None, "schwelle": 0.65, "n_gemeinsam": 0,
              "paarurteil": _paar(-0.05)}
    grund = kosmo_szene.als_ergebnis("vis-1790000000-abcdef", [],
                                     geometrie_urteil=urteil)["qa"]["verdict"]["reason"]
    assert "URTEILT NICHT" in grund and "ungeprueft" in grund
    assert "DURCHGEFALLEN" not in grund
