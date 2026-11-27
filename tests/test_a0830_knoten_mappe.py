"""A0830 «Knoten bleiben in ihrer Mappe» — der Vertrag zwischen Wirt und Heim-PC (Audit 24.11.2026, V1).

Die Visbox-Seite öffnet die Knotenansicht mit ``?ordner=<A>``. Bis 0.3.77 fragte der Wirt den Graphen
ohne Angabe ab; der Heim-PC antwortete mit der zuletzt geöffneten Mappe (B), und das nächste Sichern
ging mit der Kennung von B dorthin (Audit-Probe ``visbox-speicherprobe.py``, Zeile «explicit A map»:
``Mappe-Alpha graph Beta Graph-Beta``). Seit A0830 fragt der Wirt ``./mappe`` und ``./graph`` mit
derselben Angabe (``kosmovis/apps/visbox-knoten/src/graph-sichern.ts``, ``leseWeg``). Diese Probe hält
fest, dass der Heim-PC auf genau diese Frage beide Male A nennt, und dass das Sichern mit der
gemerkten Kennung in A schreibt und B bytegleich lässt.

Ohne Netz, ohne Browser: der Server wird gebaut und nicht gestartet. Nur synthetische Mappen.
"""
from __future__ import annotations

import hashlib
import io
import json
import sys
import urllib.parse
from pathlib import Path

import pytest

WURZEL = Path(__file__).resolve().parents[1]
FLAECHE = WURZEL / "oberflaeche"
WERKZEUGE = WURZEL / "tools"


@pytest.fixture(scope="module")
def server():
    sys.path.insert(0, str(FLAECHE))
    try:
        import server as modul
        return modul
    finally:
        sys.path.remove(str(FLAECHE))


@pytest.fixture(scope="module")
def make_test_glb():
    sys.path.insert(0, str(WERKZEUGE))
    try:
        import make_test_glb as modul
        return modul
    finally:
        sys.path.remove(str(WERKZEUGE))


def _sha256(pfad: Path) -> str:
    return hashlib.sha256(pfad.read_bytes()).hexdigest()


def _frage(abfrage: str) -> dict:
    return urllib.parse.parse_qs(abfrage)


@pytest.fixture
def zwei_mappen(tmp_path, monkeypatch, make_test_glb):
    """Alpha und Beta nebeneinander, beide mit eigenem Graph; zuletzt geöffnet ist Beta."""
    from aiimaging import arbeitsgang, knotenweg, mappenpaket

    # Gesucht wird nur neben den beiden Mappen, nie im Rückfall-Ordner des Rechners.
    monkeypatch.setattr(mappenpaket, "_rueckfall", lambda: None)
    haus = tmp_path / "haus.glb"
    haus.write_bytes(make_test_glb.baue_glb(make_test_glb.situationsszene()))
    alpha, beta = tmp_path / "Alpha", tmp_path / "Beta"
    arbeitsgang.lege_an(alpha, haus, name="Alpha", einstellungen={"up_axis": "Y", "prompt": "Abendlicht"})
    arbeitsgang.lege_an(beta, haus, name="Beta", einstellungen={"up_axis": "Y", "prompt": "Winter"})
    leer = {"kind": "visgraph", "nodes": [], "edges": []}
    knotenweg.schreibe_graph(alpha, [{**leer, "id": "Graph-Alpha"}])
    knotenweg.schreibe_graph(beta, [{**leer, "id": "Graph-Beta"}])
    return alpha, beta


def _handler(server, zuletzt: Path):
    klasse = type("Probe", (server.Flaeche,), {"zuletzt_geoeffnet": str(zuletzt)})
    handler = object.__new__(klasse)
    handler.ordner = None
    handler.antworten = []
    handler._sende = lambda daten, *rest: handler.antworten.append(daten)
    handler._fehler = lambda satz, code=400, *rest: handler.antworten.append({"fehler": satz, "code": code})
    return handler


def _frage_des_wirts(alpha: Path) -> str:
    """Genau die Frage, die der Wirt nach A0830 an ``./mappe`` und ``./graph`` hängt (``encodeURIComponent``)."""
    return "ordner=" + urllib.parse.quote(str(alpha), safe="")


def test_mappe_und_graph_mit_der_frage_des_wirts_nennen_beide_alpha(server, zwei_mappen):
    alpha, beta = zwei_mappen
    handler = _handler(server, zuletzt=beta)
    frage = _frage(_frage_des_wirts(alpha))
    handler._knotenweg_lesen(server.WEG_KNOTEN_MAPPE, frage)
    handler._knotenweg_lesen(server.WEG_KNOTEN_GRAPH, frage)
    mappe, graph = handler.antworten
    assert mappe.get("name") == "Alpha", mappe
    assert graph.get("mappe") == "Alpha"
    assert [g["id"] for g in graph["graphen"]] == ["Graph-Alpha"]


def test_sichern_mit_der_gemerkten_kennung_schreibt_in_alpha_und_beta_bleibt_bytegleich(server, zwei_mappen):
    from aiimaging import knotenweg

    alpha, beta = zwei_mappen
    # Jede Datei von Beta, also auch ihre Graphdatei: sha256 vorher und nachher.
    beta_dateien = {p: _sha256(p) for p in sorted(beta.rglob("*")) if p.is_file()}
    handler = _handler(server, zuletzt=beta)
    handler._knotenweg_lesen(server.WEG_KNOTEN_GRAPH, _frage(_frage_des_wirts(alpha)))
    gelesen = handler.antworten[-1]
    # So baut der Wirt den Weg zum Sichern (`sicherWeg`): Kennung und Stand aus der Antwort.
    abfrage = urllib.parse.urlencode({k: v for k, v in (("mappe", gelesen.get("mappe")),
                                                        ("stand", gelesen.get("stand"))) if v})
    assert "mappe=Alpha" in abfrage
    rumpf = json.dumps({"graphen": [{"id": "Graph-Alpha-neu", "kind": "visgraph", "nodes": [], "edges": []}]}).encode()
    handler.path = f"{server.WEG_KNOTEN_GRAPH}?{abfrage}"
    handler.rfile = io.BytesIO(rumpf)
    handler._knotenweg_handeln(server.WEG_KNOTEN_GRAPH, len(rumpf))
    assert "fehler" not in handler.antworten[-1], handler.antworten[-1]
    assert [g["id"] for g in knotenweg.lies_graph(alpha)["graphen"]] == ["Graph-Alpha-neu"]
    assert [g["id"] for g in knotenweg.lies_graph(beta)["graphen"]] == ["Graph-Beta"]
    assert {p: _sha256(p) for p in sorted(beta.rglob("*")) if p.is_file()} == beta_dateien


def test_bleibt_ohne_angabe_die_zuletzt_geoeffnete(server, zwei_mappen):
    """Entscheid 85 B: ohne Angabe die zuletzt geöffnete Mappe; der Grund, warum der Wirt fragen muss."""
    _, beta = zwei_mappen
    handler = _handler(server, zuletzt=beta)
    handler._knotenweg_lesen(server.WEG_KNOTEN_GRAPH, {})
    assert handler.antworten[-1].get("mappe") == "Beta"
