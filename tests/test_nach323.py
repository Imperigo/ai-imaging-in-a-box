"""Folgen aus auf-20261022-323 (Protokoll 74 §220): Genitiv, jede Karte genannt, «nicht» klein.

* B1 — «der Bestätigung der Architektin» wurde «… dem Architekten»; richtig ist der Genitiv.
* B2 — 323 F5 lief in Einzelaufrufen; neben der Render-Karte ging eine zweite Karte «Knoten
  einstellen» hinaus, die kein Satz nannte. Ab zwei Karten nennt der Kern die ungenannten.
* B3 — «Dazu fand ich kein passendes Werkzeug — Nicht …» mit grossem N nach dem Gedankenstrich.
"""

from __future__ import annotations

import pytest

from aiimaging import assistent

from test_nach321 import Modell, _ruft
from test_nach322 import F3, F5, _GELESEN, _RENDER_KARTE, _frage


@pytest.mark.parametrize("vorher, nachher", [
    ("Er wartet auf der Bestätigung der Architektin.", "Er wartet auf der Bestätigung des Architekten."),
    ("Die Freigabe der Architektin fehlt.", "Die Freigabe des Architekten fehlt."),
    ("Sprich mit der Architektin.", "Sprich mit dem Architekten."),
    ("Das geht zur Architektin.", "Das geht zum Architekten."),
    ("Der Architektin bleibt die Freigabe.", "Dem Architekten bleibt die Freigabe."),
    ("Das liegt bei der Architektin.", "Das liegt beim Architekten."),
    ("Die Architektin entscheidet.", "Der Architekt entscheidet."),
])
def test_b1_genitiv_und_dativ(vorher, nachher):
    assert assistent.fuer_den_architekten(vorher) == nachher


_PARAM_KARTE = {"werkzeug": "vis_nodeParametrieren",
                "argumente": {"graphId": "g1", "nodeId": "n2", "parameter": {"aufloesung": [1920, 1080]}},
                "ergebnis": "VORSCHLAG A-2 liegt als Karte beim Architekten. Er entscheidet."}


def test_b2_die_zweite_karte_wird_genannt():
    text = assistent._berichtige_antwort("Die Vorschau ist vorbereitet.", F5,
                                         [*_GELESEN, _RENDER_KARTE, _PARAM_KARTE])
    assert "A-2 (Knoten einstellen)" in text
    assert "A-1" in text
    assert "vis_" not in text
    assert text.endswith(assistent.SATZ_RENDER_FREIGABE)


def test_b2_eine_genannte_karte_wird_nicht_wiederholt():
    text = assistent._berichtige_antwort("Karte A-1 rendert, Karte A-2 stellt die Grösse ein.", F5,
                                         [*_GELESEN, _RENDER_KARTE, _PARAM_KARTE])
    assert "Als Karte vorgeschlagen" not in text


def test_b2_eine_einzelne_karte_bleibt_wie_bisher():
    text = assistent._berichtige_antwort("Die Vorschau ist vorbereitet.", F5,
                                         [*_GELESEN, _RENDER_KARTE])
    assert "Als Karte vorgeschlagen" not in text


def test_b3_nicht_klein_nach_dem_gedankenstrich():
    falsch = _ruft("vis_render", graphId="g1", nodeId="n9")
    aus = _frage(F3, Modell(falsch, falsch, falsch))
    assert "kein passendes Werkzeug — nicht vorgeschlagen: «Rendern»." in aus["antwort"]
    assert "— Nicht" not in aus["antwort"]


# ======================================================================================
# Folgen aus auf-20261022-324 (Protokoll 74 §221)
# ======================================================================================

@pytest.mark.parametrize("vorher, nachher", [
    ("Warte auf die Bestätigung der Nutzerin.", "Warte auf die Bestätigung des Architekten."),
    ("Die Nutzerin entscheidet.", "Der Architekt entscheidet."),
    ("Der Nutzer gibt frei.", "Der Architekt gibt frei."),
    ("Das zeige ich dem Benutzer.", "Das zeige ich dem Architekten."),
    ("Die Nutzer der App.", "Die Nutzer der App."),
])
def test_324_b1_nutzerin_heisst_architekt(vorher, nachher):
    assert assistent.fuer_den_architekten(vorher) == nachher


def test_324_b2_klammern_in_einer_form_und_mehrzahl():
    param = dict(_PARAM_KARTE, ergebnis="VORSCHLAG A-2 liegt als Karte beim Architekten: "
                                        "vis_nodeParametrieren an n2.")
    text = assistent._berichtige_antwort("Die Vorschau ist vorbereitet.", F5,
                                         [*_GELESEN, _RENDER_KARTE, param])
    assert "Als Karten vorgeschlagen:" in text
    assert "A-2 (Knoten einstellen an n2)" in text
    assert "(«" not in text
    assert "führt sie aus." in text
