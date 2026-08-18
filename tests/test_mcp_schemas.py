"""Prüft, ob KosmoOrbit unsere Werkzeuge sehen und verdrahten könnte.

Das ist das Abnahmekriterium der Phase 2. Weil KosmoOrbits Prüfung in TypeScript steckt
und nur im Cockpit läuft, ist sie in `mcp_schemas.pruefe_verdrahtbarkeit` nachgebaut. Die
Gegenseite dieser Tests sind jedoch die **echten** Ausgabeschemas von KosmoDraw, wörtlich
übernommen aus `kosmodraw_mcp_server.py:274-300` (gelesen 2026-08-14, Commit `8481ea8`).

Damit ist die Verdrahtbarkeit belegt und nicht behauptet — soweit das ohne laufendes
Cockpit möglich ist. Was diese Tests NICHT können: bestätigen, dass Kosmo den Server
tatsächlich registriert. Das braucht die laufende Umgebung.
"""
from __future__ import annotations

import json

import pytest

from aiimaging.mcp_schemas import (
    GEOMETRIE_FELDER,
    WERKZEUG_ENQUEUE,
    WERKZEUG_PRUEFE,
    WERKZEUG_QUERY,
    WERKZEUGE,
    pruefe_verdrahtbarkeit,
    pruefe_vertrag,
    schema_felder,
    voller_name,
    werkzeug,
)
from aiimaging.mcp_server import rufe_werkzeug

# ── Die echten Nachbarn, wörtlich aus KosmoDraws _OUT-Block ──────────────────────────

KOSMODRAW_EXPORT_IFC = {
    "name": "kosmodraw_export_ifc",
    "outputSchema": {"type": "object", "properties": {
        "ifc_path": {"type": ["string", "null"]},
        "n_entities": {"type": "object"},
        "status": {"type": "string"},
        "error": {"type": ["string", "null"]}}},
}

KOSMODRAW_EXPORT_GLB = {
    "name": "kosmodraw_export_glb",
    "outputSchema": {"type": "object", "properties": {
        "glb_path": {"type": ["string", "null"]},
        "n_vertices": {"type": ["integer", "null"]},
        "n_triangles": {"type": ["integer", "null"]},
        "bbox": {"type": ["array", "null"]},
        "up_axis": {"type": ["string", "null"]},
        "layers": {"type": "array", "items": {"type": "object"}},
        "status": {"type": "string"}}},
}

KOSMODRAW_BIM_LAYERS = {
    "name": "kosmodraw_bim_layers",
    "outputSchema": {"type": "object", "properties": {
        "layers": {"type": "array", "items": {"type": "object"}},
        "n_layers": {"type": ["integer", "null"]},
        "bbox": {"type": ["array", "null"]},
        "element_counts": {"type": "object"},
        "geometry_ref": {"type": ["string", "null"]},
        "source_ifc": {"type": ["string", "null"]},
        "bbox_note": {"type": ["string", "null"]}}},
}


# ── Der Vertrag als solcher ──────────────────────────────────────────────────────────

@pytest.mark.parametrize("name", sorted(WERKZEUGE))
def test_jeder_vertrag_erfuellt_die_oekosystem_anforderungen(name):
    """Ohne inputSchema UND outputSchema meldet pipelineReadiness unsere Kanten als tot."""
    assert pruefe_vertrag(WERKZEUGE[name]) == []


@pytest.mark.parametrize("name", sorted(WERKZEUGE))
def test_kein_geschlossenes_eingabeschema(name):
    """mergeInputs reicht ALLE Vorgängerfelder durch — ein geschlossenes Schema scheiterte daran."""
    assert WERKZEUGE[name]["inputSchema"].get("additionalProperties") is not False


@pytest.mark.parametrize("name", sorted(WERKZEUGE))
def test_vertrag_ist_json_faehig(name):
    """Die Verträge gehen über die Leitung — sie müssen serialisierbar sein."""
    assert json.loads(json.dumps(WERKZEUGE[name]))["name"] == name


def test_werkzeugname_traegt_den_lane_namen_doppelt():
    """Ökosystem-Konvention: mcp__<server>__<lane>_<funktion>, belegt an mcp__kosmodraw__kosmodraw_*."""
    assert voller_name(WERKZEUG_ENQUEUE) == "mcp__aiimaging__aiimaging_enqueue_render"


def test_unbekanntes_werkzeug_wird_gemeldet():
    """Ein Tippfehler im Namen soll auffallen, nicht None zurückgeben."""
    with pytest.raises(KeyError, match="Unbekanntes Werkzeug"):
        werkzeug("aiimaging_gibt_es_nicht")


# ── Verdrahtbarkeit gegen die echten Nachbarn ────────────────────────────────────────

@pytest.mark.parametrize("erzeuger", [
    KOSMODRAW_EXPORT_IFC, KOSMODRAW_EXPORT_GLB, KOSMODRAW_BIM_LAYERS,
], ids=lambda e: e["name"])
def test_enqueue_ist_an_jeden_echten_erzeuger_verdrahtbar(erzeuger):
    """Der Kern der Phase: von allen drei KosmoDraw-Ausgängen muss eine tragende Kante entstehen.

    Beide Wege sind gültig — eigener IFC-Pfad (Regel 4) und Einfügen hinter export_glb.
    Genau deshalb steht in `required` nichts: KosmoOrbits Prüfung kennt kein
    Entweder-oder, und ein Pflichtfeld würde jeweils den anderen Weg brechen.
    """
    assert pruefe_verdrahtbarkeit(erzeuger, WERKZEUGE[WERKZEUG_ENQUEUE]) == []


@pytest.mark.parametrize("erzeuger,erwartet", [
    (KOSMODRAW_EXPORT_IFC, "ifc_path"),
    (KOSMODRAW_EXPORT_GLB, "glb_path"),
    (KOSMODRAW_BIM_LAYERS, "bbox"),
], ids=["export_ifc", "export_glb", "bim_layers"])
def test_die_tragende_kante_hat_einen_konkreten_namen(erzeuger, erwartet):
    """Nicht nur 'irgendeine' Überschneidung: das erwartete Feld muss es wirklich sein."""
    gemeinsam = (set(schema_felder(erzeuger["outputSchema"]))
                 & set(schema_felder(WERKZEUGE[WERKZEUG_ENQUEUE]["inputSchema"])))
    assert erwartet in gemeinsam


def test_pruefe_werkzeug_ist_ebenfalls_verdrahtbar():
    """Die Vorprüfung soll vor den Render gehängt werden können, ohne tote Kante."""
    assert pruefe_verdrahtbarkeit(KOSMODRAW_EXPORT_GLB, WERKZEUGE[WERKZEUG_PRUEFE]) == []


def test_query_braucht_die_job_id_und_meldet_sie_als_pflicht():
    """Gegenprobe, dass die Prüfung nicht blind gutmütig ist: query hat ein echtes Pflichtfeld."""
    befunde = pruefe_verdrahtbarkeit(KOSMODRAW_EXPORT_IFC, WERKZEUGE[WERKZEUG_QUERY])
    assert any(b["art"] == "missing-required" and "job_id" in b["detail"] for b in befunde)


def test_query_ist_hinter_enqueue_verdrahtbar():
    """Die natürliche Kette enqueue → query muss ohne Handarbeit tragen."""
    assert pruefe_verdrahtbarkeit(WERKZEUGE[WERKZEUG_ENQUEUE], WERKZEUGE[WERKZEUG_QUERY]) == []


def test_gesetztes_arg_ersetzt_den_fehlenden_vorgaenger():
    """Wie im Cockpit: ein von Hand gesetztes Feld zählt als verfügbar.

    Die tote Kante bleibt dabei zu Recht bestehen — `export_ifc` liefert nichts, was
    `query_render` entgegennimmt. Das ist keine Schwäche der Prüfung, sondern ihr Zweck:
    Sie sagt, dass man diese Kante gar nicht erst ziehen sollte. Das Pflichtfeld
    verschwindet, die Warnung nicht.
    """
    befunde = pruefe_verdrahtbarkeit(
        KOSMODRAW_EXPORT_IFC, WERKZEUGE[WERKZEUG_QUERY], gesetzte_args={"job_id"})

    assert not [b for b in befunde if b["art"] == "missing-required"]
    assert [b["art"] for b in befunde] == ["dead-edge"]


# ── Die Prüfung selbst muss scharf sein ──────────────────────────────────────────────

def test_prueffunktion_erkennt_eine_wirklich_tote_kante():
    """Mutationsprobe: ohne diesen Test wüsste niemand, ob die Prüfung überhaupt anschlägt."""
    fremd = {"name": "fremd", "outputSchema": {"type": "object",
                                               "properties": {"voellig_anderes": {"type": "string"}}}}
    verbraucher = {"name": "v", "inputSchema": {"type": "object",
                                                "properties": {"nichts_gemeinsames": {"type": "string"}}},
                   "outputSchema": {"type": "object", "properties": {"x": {}}}}
    befunde = pruefe_verdrahtbarkeit(fremd, verbraucher)
    assert [b["art"] for b in befunde] == ["dead-edge"]


def test_prueffunktion_meldet_fehlendes_outputschema_als_mangel():
    """Gegenprobe zur Vertragsprüfung — sonst wäre sie leer und nichtssagend."""
    maengel = pruefe_vertrag({"name": "x", "description": "y",
                              "inputSchema": {"type": "object", "properties": {}}})
    assert any("outputSchema" in m for m in maengel)


def test_prueffunktion_meldet_geschlossenes_schema():
    """additionalProperties:false ist der Fehler, den man am leichtesten versehentlich macht."""
    maengel = pruefe_vertrag({
        "name": "x", "description": "y",
        "inputSchema": {"type": "object", "properties": {"a": {}}, "additionalProperties": False},
        "outputSchema": {"type": "object", "properties": {"b": {}}}})
    assert any("additionalProperties" in m for m in maengel)


def test_geometriefelder_stimmen_mit_dem_phase_0_befund_ueberein():
    """Die belegten Feldnamen sind bindend — eine Umbenennung hier bricht die Kette still."""
    ein = set(schema_felder(WERKZEUGE[WERKZEUG_ENQUEUE]["inputSchema"]))
    assert set(GEOMETRIE_FELDER) <= ein


def test_enqueue_gibt_geometry_ref_zurueck():
    """`geometry_ref` ist der Ökosystem-Begriff für 'hier liegt die Geometrie'."""
    assert "geometry_ref" in schema_felder(WERKZEUGE[WERKZEUG_ENQUEUE]["outputSchema"])


def test_enqueue_kann_niemals_running_melden():
    """Dieses Werkzeug legt nur ab. Rührte es die GPU an, wäre der Freeze-Schutz hinfällig."""
    beschreibung = WERKZEUGE[WERKZEUG_ENQUEUE]["outputSchema"]["properties"]["status"]["description"]
    assert "nie 'running'" in beschreibung


# ==========================================================================================
# Halten die Werkzeuge ihre eigene Zusage — auch auf den Fehlerwegen?
#
# Befund vom 18.08.2026 (`docs/HOMESTATION-2026-08-18-MCP-REGISTRIERUNG.md`): Odysseus wies
# `aiimaging_query_render` auf einen unbekannten Auftrag ab mit
# `Output validation error: None is not of type 'string'`. Die Antwort war richtig, die
# ZUSAGE war falsch — `status` war als nicht-nullbar deklariert, obwohl ein Auftrag, den es
# nicht gibt, keinen Zustand hat.
#
# Aufgefallen ist das erst bei der Registrierung an einem fremden Cockpit. Diese Tests
# holen die Prüfung hierher, damit die nächste solche Lücke vor dem Cockpit anschlägt: Der
# GLÜCKLICHE Weg wurde geprüft, der Fehlerweg nicht — und Schemaverletzungen leben genau
# dort.
# ==========================================================================================

def _passt_zum_typ(wert, typ) -> bool:
    """Ob ein Wert einem JSON-Schema-``type`` genügt. Nur die hier benutzte Teilmenge.

    Bewusst selbst gebaut statt über ``jsonschema``: Das Paket ist keine Abhängigkeit
    dieses Projekts, und die Zusagen hier sind flach. Ein Test, der eine neue
    Abhängigkeit mitbringt, wird beim ersten frischen Environment übersprungen — und
    dann prüft er nichts mehr.
    """
    erlaubt = typ if isinstance(typ, list) else [typ]
    for t in erlaubt:
        if t == "null" and wert is None:
            return True
        if t == "string" and isinstance(wert, str):
            return True
        if t == "array" and isinstance(wert, list):
            return True
        if t == "object" and isinstance(wert, dict):
            return True
        if t == "boolean" and isinstance(wert, bool):
            return True
        if t == "number" and isinstance(wert, (int, float)) and not isinstance(wert, bool):
            return True
        if t == "integer" and isinstance(wert, int) and not isinstance(wert, bool):
            return True
    return False


def pruefe_gegen_schema(ergebnis: dict, schema: dict) -> list[str]:
    """Alle Verletzungen als Liste — nicht die erste, sondern alle.

    Wer eine Antwort repariert, will wissen, wie viele Felder betroffen sind, nicht nur
    das alphabetisch erste.
    """
    verstoesse = []
    eigenschaften = schema.get("properties", {})
    for name, teilschema in eigenschaften.items():
        if name not in ergebnis:
            continue
        if "type" in teilschema and not _passt_zum_typ(ergebnis[name], teilschema["type"]):
            verstoesse.append(
                f"{name}: {ergebnis[name]!r} passt nicht zu type={teilschema['type']!r}"
            )
    for pflicht in schema.get("required", []):
        if pflicht not in ergebnis:
            verstoesse.append(f"{pflicht}: Pflichtfeld fehlt in der Antwort")
    return verstoesse


def test_query_auf_unbekannten_auftrag_haelt_sein_schema():
    """Der Fall, an dem Odysseus die Antwort abgewiesen hat.

    Ein unbekannter Auftrag ist kein Sonderfall, sondern der häufigste Fehlerweg
    überhaupt — ein Tippfehler in der `job_id` genügt.
    """
    ergebnis = rufe_werkzeug(WERKZEUG_QUERY, {"job_id": "gibt-es-nicht"})
    verstoesse = pruefe_gegen_schema(ergebnis, WERKZEUGE[WERKZEUG_QUERY]["outputSchema"])
    assert verstoesse == [], verstoesse
    assert ergebnis["status"] is None
    assert ergebnis["error"]


def test_status_darf_nullbar_sein_aber_nicht_erfunden():
    """Der Flicken, der nicht gemacht wurde — und warum.

    Ein Ersatzwert wie ``"unbekannt"`` hätte das Schema erfüllt und wäre falsch gewesen:
    ``status`` trägt die Zustände des Auftrags-Automaten, und ``kosmo_naht`` liest genau
    dieses Feld, um zu entscheiden, ob ein Auftrag freigegeben ist. Ein erfundener
    Zustand stünde in einer Vokabelliste, in der kein Auftrag je sein kann.
    """
    from aiimaging import jobs
    ergebnis = rufe_werkzeug(WERKZEUG_QUERY, {"job_id": "gibt-es-nicht"})
    zustaende = {jobs.STATUS_AWAITING, jobs.STATUS_QUEUED, jobs.STATUS_RUNNING,
                 jobs.STATUS_DONE, jobs.STATUS_ERROR, jobs.STATUS_CANCELLED}
    assert ergebnis["status"] not in zustaende
    assert ergebnis["status"] is None


@pytest.mark.parametrize("name", sorted(WERKZEUGE))
def test_jedes_werkzeug_haelt_sein_schema_auch_bei_leeren_argumenten(name):
    """Der Fehlerweg, den niemand aufruft — und in dem Schemaverletzungen leben.

    Keine Argumente ist die härteste Eingabe: Jedes Pflichtfeld fehlt. Was das Werkzeug
    dann antwortet, muss trotzdem der Zusage genügen, die in der Knotenliste steht — denn
    das Cockpit prüft sie und weist die Antwort sonst ab.
    """
    ergebnis = rufe_werkzeug(name, {})
    verstoesse = pruefe_gegen_schema(ergebnis, WERKZEUGE[name]["outputSchema"])
    assert verstoesse == [], verstoesse


@pytest.mark.parametrize("name", sorted(WERKZEUGE))
def test_jedes_werkzeug_haelt_sein_schema_bei_unsinnigen_argumenten(name):
    """Argumente vom falschen Typ kommen aus einem fremden Cockpit jederzeit an."""
    for argumente in ({"job_id": 42}, {"job_id": None}, {"unbekannt": "x"}):
        ergebnis = rufe_werkzeug(name, argumente)
        verstoesse = pruefe_gegen_schema(ergebnis, WERKZEUGE[name]["outputSchema"])
        assert verstoesse == [], (argumente, verstoesse)


def test_unbekanntes_werkzeug_wird_gemeldet_und_stuerzt_nicht():
    ergebnis = rufe_werkzeug("aiimaging_gibt_es_nicht", {})
    assert "error" in ergebnis
    assert "Unbekanntes Werkzeug" in ergebnis["error"]
