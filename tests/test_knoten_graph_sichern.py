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


# ------------------------------------------------------------------ §231: die Mappe bleibt fest
#
# Mac-Befund 0.3.33 (22.10.2026): Der Heim-PC hat EINE «zuletzt geöffnete» Mappe für alle Geräte.
# Öffnete ein anderes Gerät (die Gegenprobe 330 am Heim-PC) eine Mappe, zeigte die Knotenansicht am
# Mac nach dem Neuladen deren Graph — und eine schon offene Ansicht hätte ihren Graph beim nächsten
# Sichern in die FREMDE Mappe geschrieben. Seither sagt GET, welche Mappe gelesen wurde, und die
# Seite sichert mit `?mappe=` genau dorthin.

def _zweite_mappe(start):
    from aiimaging import arbeitsgang
    quelle = start.parent.parent / "vorlagen" / "Startbau.glb"
    zweite = start.parent / "Fremd"
    arbeitsgang.lege_an(zweite, quelle)
    return zweite


def test_get_nennt_die_gelesene_mappe(server, start):  # noqa: F811
    s = _Server(server, start)
    code, sicht = s.get(server.WEG_KNOTEN_GRAPH)
    assert code == 200 and sicht["mappe"] == start.name


def test_sichern_trifft_die_gelesene_mappe_nicht_die_zuletzt_geoeffnete(server, start):  # noqa: F811
    s = _Server(server, start)
    code, sicht = s.get(server.WEG_KNOTEN_GRAPH)
    gelesen = sicht["mappe"]
    # Ein anderes Gerät öffnet eine andere Mappe — für alle Geräte die «zuletzt geöffnete».
    fremd = _zweite_mappe(start)
    s.klasse.zuletzt_geoeffnet = str(fremd)
    rumpf = json.dumps({"graphen": GRAPH}).encode()
    code, antwort = s._frage("POST", f"{server.WEG_KNOTEN_GRAPH}?mappe={gelesen}", rumpf,
                             {"Content-Type": "application/json"})
    assert code == 200 and antwort == {"gesichert": 1}
    assert (start / knotenweg.GRAPH_DATEI).is_file()
    assert not (fremd / knotenweg.GRAPH_DATEI).exists(), "der Graph landete in der fremden Mappe"


def test_sichern_nur_beim_namen_nie_mit_pfad(server, start, tmp_path):  # noqa: F811
    s = _Server(server, start)
    ziel = tmp_path / "irgendwo"
    ziel.mkdir()
    rumpf = json.dumps({"graphen": GRAPH}).encode()
    code, _ = s._frage("POST", f"{server.WEG_KNOTEN_GRAPH}?ordner={ziel}", rumpf,
                       {"Content-Type": "application/json"})
    assert not (ziel / knotenweg.GRAPH_DATEI).exists()
    code, _ = s._frage("POST", f"{server.WEG_KNOTEN_GRAPH}?mappe=gibt-es-nicht", rumpf,
                       {"Content-Type": "application/json"})
    assert code == 404
