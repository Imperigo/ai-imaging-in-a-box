"""Fenster-Pruefung v4 (A0092): realistisch dunkles, spiegelndes KI-Glas ist kein Fehlalarm.

Der Eichsatz stammt aus zwei echten Messreihen (Stimmungen vom 31.10. und 02.11., Auftrag
auf-20261023-346), ausgeduennt auf einige hundert Bildpunkte je Lauf. Die Laeufe sind von Auge
beurteilt: In den Stimmungsbildern und in den vollen Laeufen sind die Fenster sichtbar, im
Vorschaubild S2m nicht.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from aiimaging import varianten

EICHSATZ = json.loads((Path(__file__).parent / "fixtures" / "glas-v4" / "eichsatz.json")
                      .read_text(encoding="utf-8"))["laeufe"]
GLAS_ID, FASSADE_ID = (10, 200, 30), (200, 10, 10)


def _miss(lauf):
    glas, fassade = lauf["glas_ki"], lauf["fassade_ki"]
    ki = glas + fassade
    grund = lauf["glas_grund"] + lauf["fassade_grund"]
    kennung = [GLAS_ID] * len(glas) + [FASSADE_ID] * len(fassade)
    return varianten.fenster_gehalten(ki, grund, kennung, {GLAS_ID})


@pytest.mark.parametrize("lauf", EICHSATZ, ids=[z["name"] for z in EICHSATZ])
def test_eichsatz_urteil_wie_von_auge(lauf):
    assert _miss(lauf)["gehalten"] is lauf["soll_gehalten"]


def test_eichsatz_hat_vier_fehlalarme_sieben_gehaltene_und_einen_richtigen_alarm():
    namen = [z["name"] for z in EICHSATZ]
    assert sum(n.startswith("stimmung-") for n in namen) == 4
    assert sum(n.startswith("voll-") for n in namen) == 7
    assert [z["soll_gehalten"] for z in EICHSATZ].count(False) == 1


def test_dunkles_neutrales_glas_gilt_als_gehalten():
    """Spiegelndes Glas ist nicht blaeulich, aber es hebt sich von der Fassade ab."""
    ki = [(60, 60, 60)] * 50 + [(170, 130, 90)] * 50
    grund = [(40, 60, 90)] * 50 + [(170, 130, 90)] * 50
    kennung = [GLAS_ID] * 50 + [FASSADE_ID] * 50
    assert varianten.fenster_gehalten(ki, grund, kennung, {GLAS_ID})["gehalten"] is True


def test_warm_uebermaltes_glas_bleibt_nicht_gehalten():
    """Waermer als die Fassade ist kein Glas, auch wenn es sich deutlich abhebt."""
    ki = [(235, 180, 80)] * 50 + [(120, 118, 116)] * 50
    grund = [(159, 179, 191)] * 50 + [(120, 118, 116)] * 50
    kennung = [GLAS_ID] * 50 + [FASSADE_ID] * 50
    assert varianten.fenster_gehalten(ki, grund, kennung, {GLAS_ID})["gehalten"] is False


def test_wie_die_fassade_uebermaltes_glas_bleibt_nicht_gehalten():
    ki = [(170, 130, 90)] * 100
    grund = [(40, 60, 90)] * 50 + [(170, 130, 90)] * 50
    kennung = [GLAS_ID] * 50 + [FASSADE_ID] * 50
    assert varianten.fenster_gehalten(ki, grund, kennung, {GLAS_ID})["gehalten"] is False
