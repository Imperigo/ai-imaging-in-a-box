"""Mac-Befund 0.3.33 (Protokoll 74 §236): Stimmung per Werkzeug — ``preset`` und ``presets``.

In der Knotenansicht gilt seit §236 eine Regel (``stimmungAufruf``): ``presets`` gewinnt vor
``preset``, sonst ersetzt ``preset`` die Wahl. Der Visbox-Kern liest am Stimmungs-Knoten nur an
einer Stelle mit: beim Weglassen eines Stimmungs-Knotens, der doppelt zum ``stimmungPreset`` des
Render-Auftrags stünde (321 B1, 322 B1). Seit die Werkzeugliste ``presets`` nennt, kann das Modell
die Stimmung auch so angeben — die Doppel-Erkennung darf dann nicht blind sein.

Das Ergänzen aus der Frage (``stimmungPreset``) betrifft nur den Render-Auftrag und bleibt, wie es
ist. Regel 3: alles synthetisch.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from aiimaging import assistent


@pytest.mark.parametrize("params, stimmung", [
    ({"preset": "abend"}, "abend"),
    ({"presets": '["abend"]'}, "abend"),
    ({"presets": "abend"}, "abend"),
    ({"presets": '["abend"]', "preset": "morgen"}, "abend"),  # presets gewinnt
    ({"presets": '["abend","nebel"]'}, None),  # mehrere: keine Doppelung
    ({}, None),
    (None, None),
])
def test_die_eine_stimmung_des_knotens(params, stimmung):
    assert assistent._stimmung_des_knotens(params) == stimmung


def _paket(params):
    return {"schritte": [
        {"befehl": "vis_nodeSetzen", "argumente": {"graphId": "g1", "typ": "stimmung", "params": params,
                                                   "x": 200, "y": 200}},
        {"befehl": "vis_verbinden", "argumente": {"from": "$neu:0", "fromPort": "prompt", "graphId": "g1",
                                                  "to": "n2", "toPort": "stimmung"}},
        {"befehl": "vis_render", "argumente": {"graphId": "g1", "nodeId": "n2", "stimmungPreset": "abend"}}]}


def test_doppelter_knoten_mit_presets_faellt_weg():
    neu, weg = assistent._ohne_doppelte_stimmung(_paket({"presets": '["abend"]'}), "Rechne mit Stimmung abend.")
    assert [s["befehl"] for s in neu["schritte"]] == ["vis_render"]
    assert weg == ["kein zusätzlicher Stimmungs-Knoten «abend» — der Render-Auftrag trägt die Stimmung schon"]


def test_widerspruechlicher_aufruf_liest_presets():
    # preset «abend», aber presets «morgen»: der Knoten wählt Morgen — keine Doppelung zu «abend».
    paket = _paket({"presets": '["morgen"]', "preset": "abend"})
    neu, weg = assistent._ohne_doppelte_stimmung(paket, "Rechne mit Stimmung abend.")
    assert neu is paket and weg == []


def test_die_werkzeugliste_im_bau_nennt_die_regel():
    liste = Path(__file__).resolve().parents[1] / "kosmovis/apps/visbox-knoten/dist/ki-werkzeugliste.json"
    roh = json.loads(liste.read_text(encoding="utf-8"))
    d = next(w["description"] for w in roh["werkzeuge"] if w["name"] == "vis_nodeParametrieren")
    assert "preset = EINE Stimmung, ersetzt die ganze Wahl" in d
    assert "gewinnt vor preset" in d
