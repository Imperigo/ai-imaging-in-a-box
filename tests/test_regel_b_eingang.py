"""Regel B an unserem Eingang — KosmoOrbit E123, gebaut am 30.09.2026.

«Wer Daten empfängt, nimmt ``null`` an und meldet einen benannten Mangel («nicht bekannt»)
statt abzuweisen.» An der Kante von KosmoDraw zu uns sind wir der Empfänger; die vier
Geometriefelder kommen dort nullbar an (`auf-20260910-101`).

Drei Dinge werden hier festgehalten:
1. Das Eingangsschema erlaubt ``null`` für alle vier Felder.
2. Ein ``null`` erscheint mit Namen im Ausgabefeld ``nicht_bekannt`` — auch im Fehlerfall.
3. «Nicht gesagt» (Schlüssel fehlt) ist etwas anderes als «nicht bekannt» (``null``).
"""
from __future__ import annotations

import pytest

from aiimaging import contracts, mcp_schemas, werkzeuge


@pytest.mark.parametrize("werkzeug", [mcp_schemas.WERKZEUG_ENQUEUE,
                                      mcp_schemas.WERKZEUG_PRUEFE])
def test_das_eingangsschema_erlaubt_null_fuer_jedes_geometriefeld(werkzeug):
    eigenschaften = mcp_schemas.werkzeug(werkzeug)["inputSchema"]["properties"]
    for feld in contracts.LANE_FIELDS:
        typ = eigenschaften[feld]["type"]
        assert isinstance(typ, list) and "null" in typ and len(typ) == 2, (feld, typ)
        assert "nicht bekannt" in eigenschaften[feld]["description"]


@pytest.mark.parametrize("werkzeug", [mcp_schemas.WERKZEUG_ENQUEUE,
                                      mcp_schemas.WERKZEUG_PRUEFE])
def test_das_ausgabeschema_fuehrt_den_mangel(werkzeug):
    aus = mcp_schemas.werkzeug(werkzeug)["outputSchema"]["properties"]
    assert aus["nicht_bekannt"]["type"] == "array"


def test_fehlend_und_null_sind_zwei_aussagen():
    assert werkzeuge.nicht_bekannt({}) == []
    assert werkzeuge.nicht_bekannt({"glb_path": "a.glb", "bbox": None}) == ["bbox"]
    assert werkzeuge.nicht_bekannt({f: None for f in contracts.LANE_FIELDS}) == list(
        contracts.LANE_FIELDS)
    assert werkzeuge.nicht_bekannt(None) == []


def test_alles_null_ergibt_einen_benannten_mangel_statt_eines_schemafehlers():
    """Der Fehlerfall des Vorgängers: Er lieferte nichts. Kein Auftrag — aber die Ursache
    steht mit Namen da, nicht bloss «keine Geometriequelle»."""
    aus = werkzeuge.enqueue_render({f: None for f in contracts.LANE_FIELDS})
    assert aus["job_id"] is None and aus["error"]
    assert "nicht bekannt" in aus["error"]
    for feld in contracts.LANE_FIELDS:
        assert feld in aus["error"]
    assert aus["nicht_bekannt"] == list(contracts.LANE_FIELDS)


def test_die_pruefung_meldet_den_mangel_ebenfalls():
    aus = werkzeuge.check_geometry({"ifc_path": None, "glb_path": None, "bbox": None})
    assert aus["nicht_bekannt"] == ["ifc_path", "glb_path", "bbox"]
    assert "nicht bekannt" in aus["begruendung"]


def test_eine_bbox_null_neben_echter_geometrie_haelt_nichts_auf():
    """Nur die fehlende Box ist unbekannt; geprüft wird trotzdem, was da ist."""
    aus = werkzeuge.check_geometry({"bbox": [[0, 0, 0], [8, 5, 3]], "up_axis": None})
    assert aus["nicht_bekannt"] == ["up_axis"]
    assert aus["bbox"] == [[0, 0, 0], [8, 5, 3]]


def test_ohne_null_ist_die_liste_leer_und_nie_abwesend():
    aus = werkzeuge.check_geometry({"bbox": [[0, 0, 0], [8, 5, 3]]})
    assert aus["nicht_bekannt"] == []
    assert werkzeuge.enqueue_render({})["nicht_bekannt"] == []
