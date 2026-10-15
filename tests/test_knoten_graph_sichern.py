"""Der Graph der Knotenansicht übersteht das Neuladen (15.10.2026, auf-20261015-286).

In Visbox lebt das Dokument der Knotenansicht nur in der Seite; nach dem Neuladen war der Graph
weg. Der Heim-PC sichert ihn jetzt je Mappe (``knotengraph.json``) und gibt ihn beim Öffnen zurück.
"""
from __future__ import annotations

import json

import pytest

from aiimaging import knotenweg

from test_modell_laden import _Server, server, start  # noqa: F401 — Probe-Wirt und Fixtures

GRAPH = [{"id": "visgraph_1", "kind": "visgraph", "name": "Bilder",
          "nodes": [{"id": "n1", "typ": "render", "x": 0, "y": 0, "params": {}}], "edges": []}]


def test_sichern_und_lesen(tmp_path):
    assert knotenweg.lies_graph(tmp_path) == {"graphen": [], "satz": None}
    assert knotenweg.schreibe_graph(tmp_path, GRAPH) == {"gesichert": 1}
    assert knotenweg.lies_graph(tmp_path)["graphen"] == GRAPH


@pytest.mark.parametrize("falsch", [{"kind": "visgraph"}, [{"kind": "storey", "id": "s"}],
                                    [{"kind": "visgraph", "id": "g", "nodes": "x", "edges": []}]])
def test_nur_render_graphen(tmp_path, falsch):
    with pytest.raises(knotenweg.KnotenwegError):
        knotenweg.schreibe_graph(tmp_path, falsch)


def test_eine_kaputte_datei_heisst_neu_anfangen(tmp_path):
    (tmp_path / knotenweg.GRAPH_DATEI).write_text("{kaputt", encoding="utf-8")
    erg = knotenweg.lies_graph(tmp_path)
    assert erg["graphen"] == [] and "nicht lesen" in erg["satz"]


def test_der_weg_am_server(server, start):  # noqa: F811
    s = _Server(server, start)
    code, sicht = s.get(server.WEG_KNOTEN_GRAPH)
    assert code == 200 and sicht["graphen"] == []
    rumpf = json.dumps({"graphen": GRAPH}).encode()
    code, antwort = s._frage("POST", server.WEG_KNOTEN_GRAPH, rumpf,
                             {"Content-Type": "application/json"})
    assert code == 200 and antwort == {"gesichert": 1}
    code, sicht = s.get(server.WEG_KNOTEN_GRAPH)
    assert sicht["graphen"] == GRAPH
    assert (start / knotenweg.GRAPH_DATEI).is_file()
    code, antwort = s._frage("POST", server.WEG_KNOTEN_GRAPH, b'{"graphen": [{"kind": "x"}]}',
                             {"Content-Type": "application/json"})
    assert code == 400
