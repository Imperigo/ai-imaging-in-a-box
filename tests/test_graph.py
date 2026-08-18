"""Der Graph-Kern unter Aufsicht: Reihenfolge, Hash, Cache.

Warum diese Tests so aussehen, wie sie aussehen
-----------------------------------------------
Der Graph-Kern hat keine sichtbare Wirkung. Ob er richtig rechnet, merkt man erst am
fertigen Bild — und dort ist die Ursache nicht mehr zu erkennen. Die drei Fehler, die
hier lauern, sind allesamt **stille**:

1. Eine Reihenfolge, die sich von Lauf zu Lauf ändert. Zwei Läufe derselben Datei wären
   nicht vergleichbar, und die spätere Geometrie-QA verlöre ihren Bezugspunkt.
2. Ein Hash, der an der Schlüsselreihenfolge eines dict hängt. Der Cache verwürfe sich
   selbst, ohne dass sich etwas geändert hätte — oder, schlimmer, träfe daneben.
3. Ein halb geschriebener Cache-Eintrag, der beim nächsten Lauf als gültig gilt. Ein
   Cache mit falschen Treffern ist schlechter als gar keiner.

Darum prüfen diese Tests nicht nur „läuft durch“, sondern die Zusagen: Stabilität gegen
Eingabereihenfolge, Unabhängigkeit von Namen, Gleichheit über Prozessgrenzen hinweg, und
dass nach einem abgebrochenen Schreibvorgang **nichts** liegen bleibt.

Alles läuft ohne Blender, ohne GPU und ohne Netz — ``graph`` ist reine stdlib.
"""
from __future__ import annotations

import dataclasses
import itertools
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from aiimaging.graph import (
    GRAPH_SCHEMA_ID,
    PFAD_MARKE,
    ZUSAGEN_FELD,
    ArtefaktCache,
    Bedarf,
    Graph,
    GraphError,
    Knoten,
    ZyklusError,
    inhalts_hash,
    pruefe_bedarf,
)
from conftest import SRC


def kette(*paare: tuple[str, tuple[str, ...]]) -> Graph:
    """Kleiner Baukasten: ``("b", ("a",))`` heisst „Knoten b hat Eingang a“."""
    return Graph([Knoten(id=kid, art="test", eingaenge=eing) for kid, eing in paare])


#: Ein Graph, wie ihn die Bildkette später wirklich hat: eine Quelle, zwei parallele
#: Zweige, ein Zusammenfluss. Synthetisch (Regel 3), aber mit echten Knotenarten.
def bildkette() -> Graph:
    return Graph([
        Knoten("geometrie", "ifc_zu_glb", {"ifc": "build/testbau.ifc"}),
        Knoten("tiefe", "tiefenkarte", {"aufloesung": 512}, ("geometrie",)),
        Knoten("beauty", "beauty_pass", {"samples": 16}, ("geometrie",)),
        Knoten("bild", "render", {"prompt": "Wohnhaus"}, ("tiefe", "beauty")),
        Knoten("qa", "geometrie_qa", {}, ("bild", "tiefe")),
    ])


# --------------------------------------------------------------------------------------
# Knoten — unveränderlich, und zwar wirklich
# --------------------------------------------------------------------------------------

def test_knoten_laesst_sich_nicht_nachtraeglich_aendern():
    """``frozen``: Nach dem Hashen darf sich ein Knoten nicht mehr verändern lassen."""
    k = Knoten("a", "render", {"samples": 16})
    with pytest.raises(dataclasses.FrozenInstanceError):
        k.art = "etwas anderes"


def test_params_werden_beim_anlegen_kopiert():
    """``frozen`` schützt nur die Zuweisung — der Inhalt eines dict muss kopiert werden.

    Ohne die Kopie könnte der Aufrufer nach dem Hashen in den Knoten hineingreifen und
    bekäme einen fremden Cache-Eintrag als eigenen.
    """
    aussen = {"samples": 16}
    k = Knoten("a", "render", aussen)

    aussen["samples"] = 9999

    assert k.params == {"samples": 16}


def test_eingaenge_werden_zu_einem_tupel():
    """Eine Liste beim Anlegen ist bequem; gespeichert wird die unveränderliche Form."""
    k = Knoten("b", "render", eingaenge=["a", "x"])
    assert k.eingaenge == ("a", "x")


def test_nicht_json_faehige_params_werden_sofort_gemeldet():
    """Ein ``Path`` in den Parametern fällt beim Anlegen auf, nicht erst beim Hashen."""
    with pytest.raises(GraphError, match="JSON"):
        Knoten("a", "render", {"pfad": Path("build/x.glb")})


def test_params_die_die_json_runde_nicht_ueberstehen_werden_abgelehnt():
    """Ein Tupel würde zur Liste — stillschweigend. Dann hiesse ein Rundlauf „gleich“,
    obwohl sich die Parameter geändert hätten."""
    with pytest.raises(GraphError, match="verlustfrei"):
        Knoten("a", "render", {"groesse": (512, 512)})


def test_nan_in_params_wird_abgelehnt():
    """NaN ist kein JSON und wäre auch nicht mit sich selbst gleich — ein Hash darauf
    wäre wertlos."""
    with pytest.raises(GraphError):
        Knoten("a", "render", {"schwelle": float("nan")})


def test_eingaenge_als_einzelner_string_wird_gemeldet():
    """``eingaenge="a"`` zerfiele lautlos in einzelne Zeichen — der klassische Tippfehler."""
    with pytest.raises(GraphError, match="einzelner String"):
        Knoten("b", "render", eingaenge="abc")


@pytest.mark.parametrize("id_, art", [("", "render"), ("  ", "render"), ("a", ""), (None, "render")])
def test_leere_id_oder_art_wird_gemeldet(id_, art):
    with pytest.raises(GraphError):
        Knoten(id_, art)


def test_knoten_ist_nicht_python_hashbar():
    """Beleg für die Entwurfsentscheidung: Pythons ``hash`` ist hier kein Ersatz.

    Er scheitert an ``params`` (dict) — und wäre selbst dann untauglich, weil er für
    Strings zwischen zwei Prozessen zufällig ist. Der stabile Hash ist ``inhalts_hash``.
    """
    with pytest.raises(TypeError):
        hash(Knoten("a", "render"))


# --------------------------------------------------------------------------------------
# Graph-Aufbau — was ohne Rechnen prüfbar ist, wird beim Anlegen geprüft
# --------------------------------------------------------------------------------------

def test_doppelte_id_wird_gemeldet():
    """IDs sind die einzige Verdrahtung; zwei gleiche Namen wären nicht auflösbar."""
    with pytest.raises(GraphError, match="doppelt"):
        Graph([Knoten("a", "render"), Knoten("a", "tiefenkarte")])


def test_unbekannter_eingang_wird_gemeldet():
    """Ein Tippfehler im Eingang ergäbe sonst einen wurzellosen Knoten, der zuerst
    gerechnet wird — und als vertauschte Reihenfolge auffiele, nicht als Tippfehler."""
    with pytest.raises(GraphError, match="tiefel"):
        Graph([Knoten("tiefe", "tiefenkarte"), Knoten("bild", "render", eingaenge=("tiefel",))])


def test_vorgaenger_darf_spaeter_in_der_liste_stehen():
    """Die Aufzählungsreihenfolge ist Darstellung, nicht Inhalt."""
    graph = Graph([Knoten("b", "render", eingaenge=("a",)), Knoten("a", "ifc_zu_glb")])
    assert graph.topologische_reihenfolge() == ["a", "b"]


def test_nur_knoten_objekte():
    with pytest.raises(GraphError, match="from_dict"):
        Graph([{"id": "a", "art": "render"}])


def test_knoten_zugriff_ist_schreibgeschuetzt():
    """Ein nachträglich eingehängter Knoten umginge sämtliche Prüfungen."""
    graph = kette(("a", ()))
    assert graph.knoten["a"].art == "test"
    assert "a" in graph and len(graph) == 1
    with pytest.raises(TypeError):
        graph.knoten["b"] = Knoten("b", "render")


# --------------------------------------------------------------------------------------
# Topologische Reihenfolge
# --------------------------------------------------------------------------------------

def test_lineare_kette():
    graph = kette(("a", ()), ("b", ("a",)), ("c", ("b",)))
    assert graph.topologische_reihenfolge() == ["a", "b", "c"]


def test_verzweigung():
    """Eine Quelle, zwei Zweige: beide nach der Quelle, untereinander nach ID sortiert."""
    graph = kette(("a", ()), ("z", ("a",)), ("b", ("a",)))
    assert graph.topologische_reihenfolge() == ["a", "b", "z"]


def test_zusammenfluss():
    """Zwei Quellen, ein Ziel: das Ziel kommt zuletzt, egal wie die Quellen heissen."""
    graph = kette(("a", ()), ("b", ()), ("ziel", ("b", "a")))
    assert graph.topologische_reihenfolge() == ["a", "b", "ziel"]


def test_bildkette_in_erwarteter_reihenfolge():
    """Der realistische Fall, ausgeschrieben — so soll die spätere Kette laufen."""
    assert bildkette().topologische_reihenfolge() == [
        "geometrie", "beauty", "tiefe", "bild", "qa",
    ]


def test_reihenfolge_haengt_nicht_an_der_eingabereihenfolge():
    """Der Kern der Reproduzierbarkeit: dieselbe Kette, anders aufgeschrieben, läuft gleich.

    Ohne die sortierte Auswahl unter gleichrangigen Knoten hinge das Ergebnis an der
    Einfügereihenfolge — und zwei Protokolle desselben Laufs wären nicht vergleichbar.
    """
    knoten = [
        Knoten("a", "test"),
        Knoten("b", "test", eingaenge=("a",)),
        Knoten("c", "test", eingaenge=("a",)),
        Knoten("d", "test", eingaenge=("b", "c")),
    ]
    ergebnisse = {tuple(Graph(p).topologische_reihenfolge()) for p in itertools.permutations(knoten)}
    assert ergebnisse == {("a", "b", "c", "d")}


def test_reihenfolge_ist_ueber_wiederholte_aufrufe_gleich():
    graph = bildkette()
    assert graph.topologische_reihenfolge() == graph.topologische_reihenfolge()


def test_jeder_knoten_steht_hinter_seinen_vorgaengern():
    """Die eigentliche Zusage der Sortierung, unabhängig von konkreten Namen geprüft."""
    graph = bildkette()
    reihenfolge = graph.topologische_reihenfolge()
    platz = {kid: i for i, kid in enumerate(reihenfolge)}

    assert sorted(reihenfolge) == sorted(graph.knoten)
    for kid in reihenfolge:
        for vor in graph.vorgaenger(kid):
            assert platz[vor] < platz[kid], f"{vor} muss vor {kid} stehen"


def test_doppelt_genannter_eingang_blockiert_die_sortierung_nicht():
    """Derselbe Vorgänger in zwei Slots ist erlaubt (Vordergrund/Hintergrund) — aber nur
    EINE Kante. Würde er doppelt gezählt, käme der Eingangsgrad nie auf null."""
    graph = Graph([Knoten("a", "test"), Knoten("b", "test", eingaenge=("a", "a"))])
    assert graph.topologische_reihenfolge() == ["a", "b"]
    assert graph.vorgaenger("b") == ["a", "a"]


def test_kreis_wird_gemeldet():
    graph = kette(("a", ("c",)), ("b", ("a",)), ("c", ("b",)))
    with pytest.raises(ZyklusError) as fehler:
        graph.topologische_reihenfolge()
    assert "a" in str(fehler.value) and "c" in str(fehler.value)


def test_selbstkante_ist_ein_kreis():
    """Ein Knoten, der sich selbst als Eingang nennt, wartet für immer auf sich selbst."""
    with pytest.raises(ZyklusError):
        Graph([Knoten("a", "test", eingaenge=("a",))]).topologische_reihenfolge()


def test_kreis_meldet_auch_die_knoten_dahinter():
    """Alles hinter dem Kreis ist ebenfalls unerreichbar — und wird mitgenannt."""
    graph = kette(("a", ("b",)), ("b", ("a",)), ("dahinter", ("b",)), ("frei", ()))
    with pytest.raises(ZyklusError) as fehler:
        graph.topologische_reihenfolge()
    assert "dahinter" in str(fehler.value)
    assert "frei" not in str(fehler.value)


def test_zykluserror_ist_ein_grapherror():
    """Wer alle Graph-Fehler fangen will, soll nicht zwei Klassen nennen müssen."""
    assert issubclass(ZyklusError, GraphError)
    with pytest.raises(GraphError):
        Graph([Knoten("a", "test", eingaenge=("a",))]).topologische_reihenfolge()


def test_leerer_graph_ist_erlaubt():
    """Kein Sonderfall: eine leere Kette hat eine leere Reihenfolge."""
    assert Graph([]).topologische_reihenfolge() == []


# --------------------------------------------------------------------------------------
# vorgaenger / nachfolger_transitiv
# --------------------------------------------------------------------------------------

def test_vorgaenger_behaelt_die_slot_reihenfolge():
    """Die Position ist Bedeutung — nicht sortieren, nicht entdoppeln."""
    graph = bildkette()
    assert graph.vorgaenger("bild") == ["tiefe", "beauty"]
    assert graph.vorgaenger("geometrie") == []


def test_vorgaenger_unbekannter_id_wird_gemeldet():
    with pytest.raises(GraphError, match="Unbekannte Knoten-ID"):
        bildkette().vorgaenger("gibtsnicht")


def test_nachfolger_transitiv_reicht_ueber_mehrere_stufen():
    """Skip-on-Error: Scheitert die Geometrie, ist die ganze Kette dahinter wertlos."""
    assert bildkette().nachfolger_transitiv(["geometrie"]) == {"tiefe", "beauty", "bild", "qa"}


def test_nachfolger_transitiv_enthaelt_den_startknoten_nicht():
    """Der gescheiterte Knoten gilt als gescheitert, nicht als übersprungen. Die beiden
    Zustände zu vermischen, verschleiert im Protokoll die Ursache."""
    assert "tiefe" not in bildkette().nachfolger_transitiv(["tiefe"])


def test_nachfolger_transitiv_mit_mehreren_startknoten():
    assert bildkette().nachfolger_transitiv(["beauty", "tiefe"]) == {"bild", "qa"}


def test_nachfolger_transitiv_eines_blattes_ist_leer():
    assert bildkette().nachfolger_transitiv(["qa"]) == set()


def test_nachfolger_transitiv_ohne_startknoten_ist_leer():
    assert bildkette().nachfolger_transitiv([]) == set()


def test_nachfolger_transitiv_meldet_unbekannte_id():
    with pytest.raises(GraphError, match="Unbekannte Knoten-ID"):
        bildkette().nachfolger_transitiv(["tiefe", "gibtsnicht"])


def test_nachfolger_transitiv_lehnt_einzelnen_string_ab():
    """``nachfolger_transitiv("tiefe")`` zerfiele sonst in einzelne Zeichen."""
    with pytest.raises(GraphError, match="Folge von IDs"):
        bildkette().nachfolger_transitiv("tiefe")


def test_nachfolger_transitiv_bleibt_bei_einem_kreis_stehen():
    """Auch ein kaputter Graph muss untersuchbar bleiben — die Suche darf nicht hängen."""
    graph = kette(("a", ("b",)), ("b", ("a",)), ("c", ("b",)))
    assert graph.nachfolger_transitiv(["a"]) == {"a", "b", "c"}


# --------------------------------------------------------------------------------------
# Serialisierung
# --------------------------------------------------------------------------------------

def test_rundlauf_ergibt_denselben_graphen():
    original = bildkette()
    zurueck = Graph.from_dict(original.to_dict())

    assert zurueck == original
    assert zurueck.to_dict() == original.to_dict()
    assert zurueck.topologische_reihenfolge() == original.topologische_reihenfolge()


def test_rundlauf_ueber_echtes_json():
    """Nicht nur durch das dict, sondern durch Text — so liegt der Graph später auf Platte."""
    original = bildkette()
    zurueck = Graph.from_dict(json.loads(json.dumps(original.to_dict())))
    assert zurueck == original


def test_to_dict_traegt_die_schema_kennung():
    assert bildkette().to_dict()["schema"] == GRAPH_SCHEMA_ID


def test_to_dict_gibt_eine_kopie_der_parameter():
    """Sonst könnte man über das zurückgegebene dict in den ``frozen`` Knoten greifen."""
    graph = bildkette()
    d = graph.to_dict()
    d["knoten"][0]["params"]["ifc"] = "etwas anderes"

    assert graph.knoten["geometrie"].params["ifc"] == "build/testbau.ifc"


def test_from_dict_lehnt_fremdes_format_ab():
    d = bildkette().to_dict()
    d["schema"] = "comfy/workflow-api"
    with pytest.raises(GraphError, match="Unbekanntes Graph-Format"):
        Graph.from_dict(d)


def test_from_dict_lehnt_fehlende_schema_kennung_ab():
    with pytest.raises(GraphError, match="Unbekanntes Graph-Format"):
        Graph.from_dict({"knoten": []})


def test_from_dict_meldet_tippfehler_im_feldnamen():
    """``eingang`` statt ``eingaenge`` ergäbe sonst lautlos einen wurzellosen Knoten."""
    d = {"schema": GRAPH_SCHEMA_ID, "knoten": [
        {"id": "a", "art": "test", "params": {}, "eingaenge": []},
        {"id": "b", "art": "test", "params": {}, "eingang": ["a"]},
    ]}
    with pytest.raises(GraphError, match="unbekannte Felder"):
        Graph.from_dict(d)


def test_from_dict_meldet_fehlende_knotenliste():
    with pytest.raises(GraphError, match="knoten"):
        Graph.from_dict({"schema": GRAPH_SCHEMA_ID})


def test_from_dict_meldet_falschen_typ():
    with pytest.raises(GraphError):
        Graph.from_dict("{}")


def test_from_dict_erbt_die_pruefungen_des_konstruktors():
    d = {"schema": GRAPH_SCHEMA_ID, "knoten": [{"id": "b", "art": "test", "eingaenge": ["a"]}]}
    with pytest.raises(GraphError, match="nicht gibt"):
        Graph.from_dict(d)


# --------------------------------------------------------------------------------------
# Bedarf — was ein Knoten braucht, und die Prüfung ohne Ausführung
# --------------------------------------------------------------------------------------
#
# Diese Prüfung ist das Gegenstück zu KosmoOrbits `pipelineReadiness`. Ihr ganzer Wert
# liegt im Zeitpunkt: Was sie meldet, meldet sie **bevor** Blender startet. Ein Test, der
# dafür etwas ausführen müsste, hätte den Zweck schon verfehlt — hier läuft nichts.


def bedarfstabelle() -> dict:
    """Die Bildkette von oben, als Deklaration. Synthetisch, aber in echter Gestalt."""
    return {
        "ifc_zu_glb": Bedarf(liefert=("glb_path",), dateien=("glb_path",)),
        "tiefenkarte": Bedarf(braucht=(("glb_path",),), liefert=("depth_png",),
                              dateien=("depth_png",)),
        "beauty_pass": Bedarf(braucht=(("glb_path",),), liefert=("beauty_png",)),
        "render": Bedarf(braucht=(("depth_png",), ("beauty_png",)), liefert=("bild_png",)),
        "geometrie_qa": Bedarf(braucht=(("bild_png",), ("depth_png",)), liefert=("bestanden",)),
    }


def test_vollstaendig_verdrahtete_kette_meldet_nichts():
    """Leer heisst verdrahtet — dieselbe Zusage wie ``pruefe_verdrahtbarkeit``."""
    assert pruefe_bedarf(bildkette(), bedarfstabelle()) == []


def test_vertauschte_eingaenge_fallen_ohne_lauf_auf():
    """Slot 0 und Slot 1 vertauscht: Die Kante besteht, sie trägt nur das Falsche.

    Das ist die tote Kante des inneren Graphen. Aussen entsteht sie durch ungleiche
    Feldnamen, hier durch eine Position — der Fehler ist derselbe, und ohne diese Prüfung
    fiele er erst nach dem Rendern auf.
    """
    graph = Graph([
        Knoten("geometrie", "ifc_zu_glb", {}),
        Knoten("tiefe", "tiefenkarte", {}, ("geometrie",)),
        Knoten("beauty", "beauty_pass", {}, ("geometrie",)),
        Knoten("bild", "render", {}, ("beauty", "tiefe")),      # verdreht
    ])
    befunde = pruefe_bedarf(graph, bedarfstabelle())

    assert [b["befund"] for b in befunde] == ["fehlendes-feld", "fehlendes-feld"]
    assert all(b["knoten"] == "bild" and b["schwere"] == "error" for b in befunde)
    assert "depth_png" in befunde[0]["detail"]


def test_fehlender_eingang_wird_gemeldet():
    """Eine QA mit nur einem Vorgänger hätte kein Ist zum Vergleichen."""
    graph = Graph([
        Knoten("geometrie", "ifc_zu_glb", {}),
        Knoten("tiefe", "tiefenkarte", {}, ("geometrie",)),
        Knoten("beauty", "beauty_pass", {}, ("geometrie",)),
        Knoten("bild", "render", {}, ("tiefe", "beauty")),
        Knoten("qa", "geometrie_qa", {}, ("bild",)),
    ])
    befunde = pruefe_bedarf(graph, bedarfstabelle())

    assert [(b["knoten"], b["befund"]) for b in befunde] == [("qa", "fehlender-eingang")]
    assert "Slot 1" in befunde[0]["detail"]


def test_unbekannte_art_wird_gemeldet_statt_fuer_richtig_gehalten():
    """Nicht prüfbar ist nicht dasselbe wie in Ordnung — sonst wäre Schweigen ein Urteil."""
    graph = Graph([Knoten("x", "irgendwas", {})])
    befunde = pruefe_bedarf(graph, bedarfstabelle())

    assert [(b["befund"], b["schwere"]) for b in befunde] == [("unbekannte-art", "warn")]


def test_kante_in_eine_unbekannte_art_wird_nicht_beurteilt():
    """Wer nicht weiss, was der Vorgänger liefert, darf ihm nichts vorwerfen."""
    graph = Graph([
        Knoten("fremd", "irgendwas", {}),
        Knoten("tiefe", "tiefenkarte", {}, ("fremd",)),
    ])
    befunde = pruefe_bedarf(graph, bedarfstabelle())

    assert [b["befund"] for b in befunde] == ["unbekannte-art"]


def test_unbenutzter_eingang_ist_nur_eine_warnung():
    """Eine Kante darf auch bloss eine Reihenfolge erzwingen — das ist kein Fehler."""
    graph = Graph([
        Knoten("geometrie", "ifc_zu_glb", {}),
        Knoten("beauty", "beauty_pass", {}, ("geometrie",)),
        Knoten("tiefe", "tiefenkarte", {}, ("geometrie", "beauty")),
    ])
    befunde = pruefe_bedarf(graph, bedarfstabelle())

    assert [(b["knoten"], b["befund"], b["schwere"]) for b in befunde] == [
        ("tiefe", "unbenutzter-eingang", "warn")]


def test_ein_kreis_verhindert_die_pruefung_nicht():
    """Geprüft wird ohne Rechenreihenfolge — sonst verdeckte der eine Fehler den anderen."""
    graph = Graph([
        Knoten("a", "tiefenkarte", {}, ("b",)),
        Knoten("b", "tiefenkarte", {}, ("a",)),
    ])
    with pytest.raises(ZyklusError):
        graph.topologische_reihenfolge()

    befunde = pruefe_bedarf(graph, bedarfstabelle())
    assert [b["knoten"] for b in befunde] == ["a", "b"]
    assert all(b["befund"] == "fehlendes-feld" for b in befunde)


def test_befunde_sind_nach_knoten_sortiert_und_wiederholbar():
    """Zwei Läufe, dieselbe Ausgabe — sonst wäre ein Protokoll nicht vergleichbar."""
    graph = Graph([
        Knoten("zebra", "tiefenkarte", {}, ("geometrie",)),
        Knoten("geometrie", "ifc_zu_glb", {}),
        Knoten("alpha", "render", {}, ("geometrie", "geometrie")),
    ])
    befunde = pruefe_bedarf(graph, bedarfstabelle())

    assert [b["knoten"] for b in befunde] == ["alpha", "alpha"]
    assert pruefe_bedarf(graph, bedarfstabelle()) == befunde


def test_leere_deklaration_meldet_jeden_knoten_als_ungeprueft():
    assert len(pruefe_bedarf(bildkette(), {})) == len(bildkette())


@pytest.mark.parametrize("bedarf", [
    dict(braucht="glb_path"), dict(liefert="glb_path"), dict(dateien="glb_path"),
])
def test_einzelner_feldname_statt_folge_wird_gemeldet(bedarf):
    """Dieselbe Falle wie bei ``Knoten.eingaenge``: Ein String zerfiele in Zeichen."""
    with pytest.raises(GraphError, match="kein einzelner String"):
        Bedarf(**bedarf)


def test_feldname_muss_text_sein():
    with pytest.raises(GraphError, match="Feldname"):
        Bedarf(liefert=(7,))


def test_braucht_wird_zu_tupeln_normalisiert():
    """Eine Liste von Listen ist dieselbe Aussage — sie soll dieselbe Gestalt annehmen."""
    assert Bedarf(braucht=[["a"], ["b", "c"]]).braucht == (("a",), ("b", "c"))


def test_pruefe_bedarf_nimmt_keinen_dict_statt_graph():
    with pytest.raises(GraphError, match="Graph"):
        pruefe_bedarf(bildkette().to_dict(), bedarfstabelle())


def test_pruefe_bedarf_meldet_eine_falsch_gefuellte_tabelle():
    with pytest.raises(GraphError, match="kein Bedarf-Objekt"):
        pruefe_bedarf(Graph([Knoten("a", "render", {})]), {"render": ("bild_png",)})


def test_falsch_gefuellte_tabelle_faellt_auch_am_vorgaenger_auf():
    """Der Vorgänger heisst 'z' und ist in der Sortierung zuletzt dran — ein
    AttributeError zwei Zeilen weiter wäre eine Fehlermeldung ohne Ursache."""
    graph = Graph([Knoten("z", "beauty_pass", {}), Knoten("a", "render", {}, ("z", "z"))])
    with pytest.raises(GraphError, match="kein Bedarf-Objekt"):
        pruefe_bedarf(graph, {**bedarfstabelle(), "beauty_pass": ("beauty_png",)})


# -- Die Zusage einer Ausgabe ----------------------------------------------------------

def test_leeres_pflichtfeld_ist_ein_mangel(tmp_path):
    """**Der Fehler aus Sitzung 07**, auf seinen Kern eingedampft.

    ``depth_png = None`` bei ``status='ok'``: Die Endungs-Heuristik der Kette sah nur
    Felder mit nicht-leerem Text und liess es durch. Der Eintrag wanderte in den Cache
    und galt für immer als Treffer — die teure Stufe wurde nie wieder gerechnet.
    """
    bedarf = Bedarf(liefert=("depth_png",), dateien=("depth_png",))
    assert bedarf.maengel({"status": "ok", "depth_png": None})
    assert "depth_png" in bedarf.maengel({"status": "ok", "depth_png": None})[0]


def test_fehlende_zugesagte_datei_ist_ein_mangel(tmp_path):
    bedarf = Bedarf(liefert=("bild_png",), dateien=("bild_png",))
    bild = tmp_path / "bild.png"
    bild.write_text("x", encoding="utf-8")

    assert bedarf.maengel({"bild_png": str(bild)}) == []
    bild.unlink()
    assert "Zugesagte Datei fehlt" in bedarf.maengel({"bild_png": str(bild)})[0]


def test_wahlweise_datei_wird_nur_geprueft_wenn_sie_genannt_ist(tmp_path):
    """Der Beauty-Pass lässt sich abschalten — dann ist sein Feld leer und in Ordnung."""
    bedarf = Bedarf(liefert=("depth_png",), dateien=("depth_png", "beauty_png"))
    tiefe = tmp_path / "t.png"
    tiefe.write_text("x", encoding="utf-8")

    assert bedarf.maengel({"depth_png": str(tiefe), "beauty_png": None}) == []
    assert bedarf.maengel({"depth_png": str(tiefe), "beauty_png": "/gibt/es/nicht.png"})


def test_falsch_ist_kein_fehlendes_feld():
    """``bestanden=False`` ist ein Urteil, kein Mangel.

    Würde ein durchgefallenes Gate wie ein leeres Feld behandelt, verwürfe der Cache
    ausgerechnet den interessantesten Fall des Projekts — die erkannte Halluzination.
    """
    assert Bedarf(liefert=("bestanden", "score")).maengel({"bestanden": False, "score": 0}) == []


def test_zugesagte_dateien_sind_die_gesetzten_in_deklarierter_reihenfolge():
    bedarf = Bedarf(dateien=("depth_png", "depth_exr", "beauty_png"))
    ausgaben = {"depth_png": "/a.png", "depth_exr": None, "beauty_png": "/c.png"}
    assert bedarf.zugesagte_dateien(ausgaben) == ["/a.png", "/c.png"]


# --------------------------------------------------------------------------------------
# inhalts_hash
# --------------------------------------------------------------------------------------

def test_gleiche_eingabe_gleicher_hash():
    k = Knoten("bild", "render", {"prompt": "Wohnhaus", "steps": 30})
    assert inhalts_hash(k, ["aaa"]) == inhalts_hash(k, ["aaa"])


def test_hash_ist_ein_sha256_hexwert():
    h = inhalts_hash(Knoten("a", "render"), [])
    assert len(h) == 64 and all(z in "0123456789abcdef" for z in h)


def test_geaenderter_parameter_ergibt_anderen_hash():
    a = Knoten("bild", "render", {"prompt": "Wohnhaus", "steps": 30})
    b = Knoten("bild", "render", {"prompt": "Wohnhaus", "steps": 31})
    assert inhalts_hash(a, []) != inhalts_hash(b, [])


def test_andere_schluesselreihenfolge_ergibt_denselben_hash():
    """Der Grund für ``sort_keys``: Ein von Hand umsortiertes JSON darf den Cache nicht
    verwerfen — inhaltlich hat sich nichts geändert."""
    a = Knoten("bild", "render", {"prompt": "Wohnhaus", "steps": 30, "cfg": 4.5})
    b = Knoten("bild", "render", {"cfg": 4.5, "steps": 30, "prompt": "Wohnhaus"})
    assert inhalts_hash(a, []) == inhalts_hash(b, [])


def test_schluesselreihenfolge_auch_verschachtelt_egal():
    """``sort_keys`` wirkt rekursiv — hier festgehalten, weil die Parameter der späteren
    Knoten geschachtelt sein werden (Kamera, Ausgabe, Modell)."""
    a = Knoten("bild", "render", {"kamera": {"brennweite": 35, "hoehe": 1.6}})
    b = Knoten("bild", "render", {"kamera": {"hoehe": 1.6, "brennweite": 35}})
    assert inhalts_hash(a, []) == inhalts_hash(b, [])


def test_knoten_id_fliesst_nicht_in_den_hash_ein():
    """Der Name ist kein Inhalt: Ein umbenannter Knoten soll nicht neu rechnen, und zwei
    gleich eingestellte Knoten sollen sich einen Cache-Eintrag teilen."""
    a = Knoten("tiefe", "tiefenkarte", {"aufloesung": 512})
    b = Knoten("tiefe_v2", "tiefenkarte", {"aufloesung": 512})
    assert inhalts_hash(a, ["x"]) == inhalts_hash(b, ["x"])


def test_eingangs_namen_fliessen_nicht_ein():
    """Was von den Vorgängern kommt, steckt bereits in deren Hashes."""
    a = Knoten("bild", "render", {}, ("tiefe",))
    b = Knoten("bild", "render", {}, ("anders_benannt",))
    assert inhalts_hash(a, ["x"]) == inhalts_hash(b, ["x"])


def test_geaenderte_art_ergibt_anderen_hash():
    assert inhalts_hash(Knoten("a", "render"), []) != inhalts_hash(Knoten("a", "tiefenkarte"), [])


def test_andere_vorgaenger_ergeben_anderen_hash():
    k = Knoten("bild", "render")
    assert inhalts_hash(k, ["aaa"]) != inhalts_hash(k, ["bbb"])
    assert inhalts_hash(k, ["aaa"]) != inhalts_hash(k, [])


def test_reihenfolge_der_vorgaenger_zaehlt():
    """Slot 0 ist nicht Slot 1 — Vordergrund und Hintergrund sind nicht vertauschbar."""
    k = Knoten("bild", "render")
    assert inhalts_hash(k, ["aaa", "bbb"]) != inhalts_hash(k, ["bbb", "aaa"])


def test_geaenderter_dateiinhalt_ergibt_anderen_hash(tmp_path):
    datei = tmp_path / "geometrie.glb"
    k = Knoten("tiefe", "tiefenkarte")

    datei.write_bytes(b"glTF-Fassung-1")
    vorher = inhalts_hash(k, [], [datei])
    datei.write_bytes(b"glTF-Fassung-2")

    assert inhalts_hash(k, [], [datei]) != vorher


def test_umbenannte_datei_mit_gleichem_inhalt_ergibt_gleichen_hash(tmp_path):
    """Der Kern der Entscheidung „Inhalt statt Pfad und mtime“: In einer Kette aus
    Subprozessen wird ständig kopiert und umbenannt, ohne dass sich etwas ändert."""
    eins = tmp_path / "export.glb"
    zwei = tmp_path / "anderswo" / "umbenannt.glb"
    zwei.parent.mkdir()
    eins.write_bytes(b"identischer Inhalt")
    zwei.write_bytes(b"identischer Inhalt")
    # mtime absichtlich verschieden setzen — sie darf nichts ändern.
    os.utime(zwei, (0, 0))

    k = Knoten("tiefe", "tiefenkarte")
    assert inhalts_hash(k, [], [eins]) == inhalts_hash(k, [], [zwei])


def test_dateien_werden_als_str_und_als_path_gleich_behandelt(tmp_path):
    datei = tmp_path / "x.glb"
    datei.write_bytes(b"abc")
    k = Knoten("a", "render")
    assert inhalts_hash(k, [], [datei]) == inhalts_hash(k, [], [str(datei)])


def test_grosse_datei_wird_vollstaendig_gehasht(tmp_path):
    """Blockweises Lesen darf nichts verlieren: Zwei Dateien, die sich erst weit hinten
    unterscheiden, müssen verschiedene Hashes ergeben."""
    gross = b"A" * (2 * (1 << 20) + 7)
    eins, zwei = tmp_path / "a.exr", tmp_path / "b.exr"
    eins.write_bytes(gross)
    zwei.write_bytes(gross[:-1] + b"B")

    k = Knoten("a", "render")
    assert inhalts_hash(k, [], [eins]) != inhalts_hash(k, [], [zwei])


def test_fehlende_datei_wird_gemeldet(tmp_path):
    """Nicht als leer behandeln — sonst hätte ein fehlendes Artefakt denselben Hash wie
    ein leeres und ergäbe einen falschen Cache-Treffer."""
    with pytest.raises(GraphError, match="fehlt"):
        inhalts_hash(Knoten("a", "render"), [], [tmp_path / "gibtsnicht.glb"])


def test_verzeichnis_statt_datei_wird_gemeldet(tmp_path):
    with pytest.raises(GraphError, match="Verzeichnis"):
        inhalts_hash(Knoten("a", "render"), [], [tmp_path])


def test_einzelner_pfad_statt_folge_wird_gemeldet(tmp_path):
    datei = tmp_path / "x.glb"
    datei.write_bytes(b"abc")
    with pytest.raises(GraphError, match="Folge von Pfaden"):
        inhalts_hash(Knoten("a", "render"), [], datei)


def test_einzelner_vorgaenger_hash_statt_folge_wird_gemeldet():
    with pytest.raises(GraphError, match="Folge von Hashes"):
        inhalts_hash(Knoten("a", "render"), "aaa")


def test_hash_ist_ueber_prozessgrenzen_hinweg_stabil():
    """Die eigentliche Zusage: derselbe Hash in einem anderen Prozess, mit anderem
    ``PYTHONHASHSEED``.

    Pythons eingebauter ``hash`` für Strings ist pro Prozess zufällig. Wäre er
    versehentlich im Spiel — etwa über eine Mengen- oder dict-Reihenfolge —, träfe der
    Cache mal und mal nicht, und niemand fände heraus warum. Dieser Test würde das
    bemerken.
    """
    programm = (
        "from aiimaging.graph import Knoten, inhalts_hash\n"
        "k = Knoten('bild', 'render', {'prompt': 'Wohnhaus', 'kamera': {'b': 2, 'a': 1}})\n"
        "print(inhalts_hash(k, ['aaa', 'bbb']))\n"
    )
    hier = inhalts_hash(
        Knoten("bild", "render", {"prompt": "Wohnhaus", "kamera": {"b": 2, "a": 1}}),
        ["aaa", "bbb"],
    )
    for seed in ("0", "1", "12345"):
        ergebnis = subprocess.run(
            [sys.executable, "-c", programm],
            capture_output=True, text=True, timeout=120,
            env={"PATH": "/usr/bin:/bin", "PYTHONPATH": str(SRC),
                 "PYTHONHASHSEED": seed, "PYTHONDONTWRITEBYTECODE": "1"},
        )
        assert ergebnis.returncode == 0, ergebnis.stderr
        assert ergebnis.stdout.strip() == hier, f"PYTHONHASHSEED={seed} ergab etwas anderes"


# -- param_dateien: die Ausnahmeliste für Pfad-Parameter -------------------------------
#
# Die Kette hat sich diese Umschrift bis Sitzung 07 selbst gebaut (eigener Zweitknoten
# mit ersetzten Pfaden). Hier steht sie jetzt, und diese Tests halten fest, warum sie
# überhaupt gebraucht wird.

def test_verschobener_projektordner_verwirft_den_cache_nicht(tmp_path):
    """Derselbe Inhalt an einem anderen Ort ergibt denselben Schlüssel.

    Ohne die Ausnahmeliste hinge der Hash am Dateinamen: Ein umbenannter Projektordner
    verwürfe den ganzen Zwischenspeicher, obwohl sich an der Geometrie nichts geändert
    hat. Es ist der teuerste Fehltreffer, den ein Cache machen kann, weil er wie ein
    korrekter Cache aussieht — er rechnet einfach immer.
    """
    alt = tmp_path / "projekt-a" / "haus.ifc"
    neu = tmp_path / "projekt-b" / "haus.ifc"
    for pfad in (alt, neu):
        pfad.parent.mkdir(parents=True)
        pfad.write_text("SYNTHETISCHE-GEOMETRIE", encoding="utf-8")

    a = inhalts_hash(Knoten("g", "geometrie", {"ifc_path": str(alt)}), [],
                     param_dateien=("ifc_path",))
    b = inhalts_hash(Knoten("g", "geometrie", {"ifc_path": str(neu)}), [],
                     param_dateien=("ifc_path",))
    assert a == b


def test_gleicher_pfad_anderer_inhalt_ergibt_anderen_hash(tmp_path):
    """Die Gegenprobe: Der Inhalt zählt weiterhin voll mit."""
    ifc = tmp_path / "haus.ifc"
    ifc.write_text("STAND-A", encoding="utf-8")
    knoten = Knoten("g", "geometrie", {"ifc_path": str(ifc)})
    vorher = inhalts_hash(knoten, [], param_dateien=("ifc_path",))

    ifc.write_text("STAND-B — ein Stockwerk mehr", encoding="utf-8")
    assert inhalts_hash(knoten, [], param_dateien=("ifc_path",)) != vorher


def test_der_feldname_bleibt_stehen_und_unterscheidet(tmp_path):
    """Ersetzt, nicht gelöscht.

    ``ifc_path`` heisst „konvertiere", ``glb_path`` heisst „reiche durch". Würde der
    Parameter ganz entfernt, ergäben dieselben Bytes unter beiden Namen denselben Hash —
    und der Cache lieferte zum glb-Durchreichen das Ergebnis einer Konversion.
    """
    datei = tmp_path / "modell"
    datei.write_text("DIESELBEN BYTES", encoding="utf-8")

    als_ifc = inhalts_hash(Knoten("g", "geometrie", {"ifc_path": str(datei)}), [],
                           param_dateien=("ifc_path", "glb_path"))
    als_glb = inhalts_hash(Knoten("g", "geometrie", {"glb_path": str(datei)}), [],
                           param_dateien=("ifc_path", "glb_path"))
    assert als_ifc != als_glb


def test_ausnahmeliste_ist_gleichbedeutend_mit_der_umschrift_von_hand(tmp_path):
    """Der Kern rechnet genau das, was die Kette sich vorher selbst gebaut hat.

    Wichtig für den Umstieg: Ein bestehender Zwischenspeicher bleibt gültig. Wäre der
    Hash auch nur um ein Zeichen anders, wäre er beim ersten Lauf nach dem Umbau
    vollständig verworfen — ohne dass jemand es gemerkt hätte.
    """
    ifc = tmp_path / "haus.ifc"
    ifc.write_text("SYNTHETISCHE-GEOMETRIE", encoding="utf-8")
    params = {"ifc_path": str(ifc), "bbox": None}

    von_hand = inhalts_hash(
        Knoten("g", "geometrie", {**params, "ifc_path": PFAD_MARKE}), ["v"], [str(ifc)])
    aus_dem_kern = inhalts_hash(
        Knoten("g", "geometrie", params), ["v"], param_dateien=("ifc_path", "glb_path"))
    assert von_hand == aus_dem_kern


def test_nicht_gesetzte_pfad_parameter_bleiben_folgenlos(tmp_path):
    """Die Liste nennt beide Eingänge; belegt ist immer nur einer."""
    ifc = tmp_path / "haus.ifc"
    ifc.write_text("x", encoding="utf-8")
    mit_leerem = inhalts_hash(Knoten("g", "geometrie", {"ifc_path": str(ifc)}), [],
                              param_dateien=("ifc_path", "glb_path"))
    ohne = inhalts_hash(Knoten("g", "geometrie", {"ifc_path": str(ifc)}), [],
                        param_dateien=("ifc_path",))
    assert mit_leerem == ohne


def test_fehlende_datei_aus_der_ausnahmeliste_wird_gemeldet(tmp_path):
    """Kein Hash ohne Datei — sonst ergäbe eine fehlende Eingabe denselben Schlüssel
    wie eine leere."""
    with pytest.raises(GraphError, match="fehlt"):
        inhalts_hash(Knoten("g", "geometrie", {"ifc_path": str(tmp_path / "weg.ifc")}), [],
                     param_dateien=("ifc_path",))


def test_pfad_parameter_der_kein_pfad_ist_wird_gemeldet():
    with pytest.raises(GraphError, match="kein Pfad"):
        inhalts_hash(Knoten("g", "geometrie", {"ifc_path": 7}), [],
                     param_dateien=("ifc_path",))


def test_param_dateien_als_einzelner_string_wird_gemeldet(tmp_path):
    with pytest.raises(GraphError, match="kein einzelner String"):
        inhalts_hash(Knoten("g", "geometrie", {}), [], param_dateien="ifc_path")


# --------------------------------------------------------------------------------------
# ArtefaktCache
# --------------------------------------------------------------------------------------

def test_ablegen_und_holen(tmp_path):
    cache = ArtefaktCache(tmp_path / "cache")
    bericht = {"glb_path": "build/e2e.glb", "n_triangles": 60, "up_axis": "Y"}

    pfad = cache.lege_ab("abc123", bericht)

    assert pfad.is_file()
    assert cache.hat("abc123")
    assert cache.hole("abc123") == bericht


def test_fehltreffer_gibt_none(tmp_path):
    """Ein Fehltreffer ist der Normalfall und darum kein Fehler."""
    cache = ArtefaktCache(tmp_path)
    assert cache.hat("nochnie") is False
    assert cache.hole("nochnie") is None


def test_holen_gibt_jedes_mal_ein_frisches_dict(tmp_path):
    """Wer das Ergebnis verändert, darf damit nicht den Cache verändern."""
    cache = ArtefaktCache(tmp_path)
    cache.lege_ab("k", {"n": 1})

    geholt = cache.hole("k")
    geholt["n"] = 999

    assert cache.hole("k") == {"n": 1}


def test_ablegen_ueberschreibt_denselben_schluessel(tmp_path):
    cache = ArtefaktCache(tmp_path)
    cache.lege_ab("k", {"lauf": 1})
    cache.lege_ab("k", {"lauf": 2})

    assert cache.hole("k") == {"lauf": 2}
    assert len(list(tmp_path.glob("*.json"))) == 1


def test_wurzel_wird_angelegt(tmp_path):
    wurzel = tmp_path / "tief" / "drin"
    ArtefaktCache(wurzel)
    assert wurzel.is_dir()


def test_leere_loescht_und_zaehlt(tmp_path):
    cache = ArtefaktCache(tmp_path)
    for schluessel in ("a1", "b2", "c3"):
        cache.lege_ab(schluessel, {"x": schluessel})

    assert cache.leere() == 3
    assert cache.hole("a1") is None
    assert cache.leere() == 0


def test_leere_fasst_fremde_dateien_nicht_an(tmp_path):
    """Der Cache räumt seinen eigenen Ordner auf, nicht den Rechner."""
    cache = ArtefaktCache(tmp_path)
    cache.lege_ab("a1", {"x": 1})
    fremd = tmp_path / "notizen.txt"
    fremd.write_text("nicht anfassen", encoding="utf-8")

    assert cache.leere() == 1
    assert fremd.exists()


@pytest.mark.parametrize("schluessel", [
    "../ausbruch", "unter/verzeichnis", "..", "", "a" * 200, ".versteckt", "mit leerzeichen",
])
def test_unzulaessiger_schluessel_wird_gemeldet(tmp_path, schluessel):
    """Der Schlüssel wird zum Dateinamen — ohne Prüfung schriebe ``../..`` ausserhalb
    der Cache-Wurzel."""
    cache = ArtefaktCache(tmp_path / "cache")
    with pytest.raises(GraphError, match="Schlüssel"):
        cache.lege_ab(schluessel, {"x": 1})


def test_ausbruchsversuch_legt_nichts_ausserhalb_an(tmp_path):
    cache = ArtefaktCache(tmp_path / "cache")
    with pytest.raises(GraphError):
        cache.lege_ab("../ausbruch", {"x": 1})
    assert not (tmp_path / "ausbruch.json").exists()


def test_inhalts_hash_taugt_als_schluessel(tmp_path):
    """Zusammenspiel der beiden Hälften: Der Hash ist genau die Gestalt, die der Cache
    als Dateinamen akzeptiert."""
    cache = ArtefaktCache(tmp_path)
    schluessel = inhalts_hash(Knoten("tiefe", "tiefenkarte", {"aufloesung": 512}), [])

    cache.lege_ab(schluessel, {"exr": "build/depth/tiefe_0001.exr"})

    assert cache.hat(schluessel)


def test_nicht_serialisierbares_ergebnis_hinterlaesst_keinen_rest(tmp_path):
    """Serialisiert wird **vor** dem Anlegen der temporären Datei — sonst bliebe hier
    eine Leiche liegen."""
    cache = ArtefaktCache(tmp_path)
    with pytest.raises(GraphError, match="JSON"):
        cache.lege_ab("k", {"pfad": Path("build/x.glb")})

    assert list(tmp_path.iterdir()) == []


def test_kein_dict_wird_gemeldet(tmp_path):
    cache = ArtefaktCache(tmp_path)
    with pytest.raises(GraphError):
        cache.lege_ab("k", ["kein", "Bericht"])


def test_abgebrochenes_schreiben_hinterlaesst_keinen_halben_eintrag(tmp_path, monkeypatch):
    """Der Grund für ``os.replace``: Ein Abbruch mitten im Schreiben (Strom weg, Ctrl-C,
    OOM beim Rendern) darf keinen Eintrag hinterlassen, der später als gültig gilt.

    Der Abbruch wird hier erzwungen, indem ``os.replace`` fehlschlägt — der Schritt, der
    aus der temporären Datei den gültigen Eintrag macht.
    """
    import aiimaging.graph as graph_modul

    cache = ArtefaktCache(tmp_path)
    cache.lege_ab("bestand", {"lauf": 1})

    def kracht(*_args, **_kwargs):
        raise OSError("Dateisystem voll")

    monkeypatch.setattr(graph_modul.os, "replace", kracht)

    with pytest.raises(OSError):
        cache.lege_ab("neu", {"lauf": 2})

    # Weder ein Eintrag noch eine temporäre Leiche — und der alte Eintrag ist unversehrt.
    assert cache.hole("neu") is None
    assert cache.hole("bestand") == {"lauf": 1}
    assert sorted(p.name for p in tmp_path.iterdir()) == ["bestand.json"]


def test_unlesbarer_eintrag_wird_gemeldet_statt_als_fehltreffer_verkleidet(tmp_path):
    """``lege_ab`` schreibt atomar — kaputtes JSON heisst also, dass etwas Fremdes in den
    Cache geschrieben hat. Das wird gesagt, nicht überdeckt."""
    cache = ArtefaktCache(tmp_path)
    (tmp_path / "kaputt.json").write_text("{ das ist kein JSON", encoding="utf-8")

    assert cache.hat("kaputt")
    with pytest.raises(GraphError, match="unlesbar"):
        cache.hole("kaputt")


# -- Was ein Eintrag zusagt ------------------------------------------------------------

def test_eintrag_ohne_zusage_bleibt_wie_er_uebergeben_wurde(tmp_path):
    """Wer nichts verspricht, bekommt auch kein zusätzliches Feld untergeschoben."""
    cache = ArtefaktCache(tmp_path)
    cache.lege_ab("k", {"n": 1})
    assert cache.hole("k") == {"n": 1}


def test_zugesagte_datei_wird_im_eintrag_vermerkt(tmp_path):
    cache = ArtefaktCache(tmp_path / "cache")
    bild = tmp_path / "bild.png"
    bild.write_text("x", encoding="utf-8")

    cache.lege_ab("k", {"bild_png": str(bild)}, zusagen=[bild])

    assert cache.hole("k")[ZUSAGEN_FELD] == [str(bild)]


def test_eintrag_mit_verschwundener_datei_ist_kein_treffer(tmp_path):
    """Ein Eintrag zeigt auf Dateien ausserhalb des Caches — ein aufgeräumtes ``/tmp``
    genügt, und die Zusage geht ins Leere.

    ``hat`` sagt weiterhin ja: Es ist eine reine Existenzprüfung auf den Eintrag und
    beantwortet eine andere Frage. Wer das Ergebnis braucht, fragt ``hole``.
    """
    cache = ArtefaktCache(tmp_path / "cache")
    bild = tmp_path / "bild.png"
    bild.write_text("x", encoding="utf-8")
    cache.lege_ab("k", {"bild_png": str(bild)}, zusagen=[str(bild)])
    assert cache.hole("k") is not None

    bild.unlink()

    assert cache.hole("k") is None
    assert cache.hat("k") is True


def test_ein_verworfener_eintrag_bleibt_liegen_und_wird_ueberschrieben(tmp_path):
    """Beim Lesen zu löschen wäre bei zwei gleichzeitigen Läufen ein Rennen."""
    cache = ArtefaktCache(tmp_path / "cache")
    bild = tmp_path / "bild.png"
    bild.write_text("x", encoding="utf-8")
    cache.lege_ab("k", {"lauf": 1}, zusagen=[str(bild)])
    bild.unlink()

    assert cache.hole("k") is None
    assert cache.schluessel() == ["k"]

    bild.write_text("wieder da", encoding="utf-8")
    cache.lege_ab("k", {"lauf": 2}, zusagen=[str(bild)])
    assert cache.hole("k")["lauf"] == 2


def test_einzelner_pfad_statt_folge_von_zusagen_wird_gemeldet(tmp_path):
    cache = ArtefaktCache(tmp_path)
    with pytest.raises(GraphError, match="kein einzelner Pfad"):
        cache.lege_ab("k", {"x": 1}, zusagen="/tmp/bild.png")


# -- Selektive Verwerfung --------------------------------------------------------------

def test_verwirf_loescht_genau_einen_eintrag(tmp_path):
    """Bis Sitzung 07 half nur ``rm -rf`` auf dem ganzen Ausgabeordner — und damit fiel
    die teure Geometriestufe mit, um einen Render zu wiederholen."""
    cache = ArtefaktCache(tmp_path)
    for schluessel in ("geometrie", "multipass", "render"):
        cache.lege_ab(schluessel, {"x": schluessel})

    assert cache.verwirf("multipass") is True

    assert cache.schluessel() == ["geometrie", "render"]
    assert cache.hole("multipass") is None
    assert cache.hole("geometrie") == {"x": "geometrie"}


def test_verwirf_meldet_einen_unbekannten_schluessel_als_nichts_getan(tmp_path):
    assert ArtefaktCache(tmp_path).verwirf("nochnie") is False


def test_verwirf_prueft_den_schluessel_wie_jeder_andere_zugriff(tmp_path):
    """Der Schlüssel wird zum Dateinamen — auch beim Löschen."""
    cache = ArtefaktCache(tmp_path / "cache")
    fremd = tmp_path / "wichtig.json"
    fremd.write_text("{}", encoding="utf-8")

    with pytest.raises(GraphError, match="Schlüssel"):
        cache.verwirf("../wichtig")
    assert fremd.exists()


def test_schluessel_sind_sortiert_und_nennen_keine_truemmer(tmp_path):
    cache = ArtefaktCache(tmp_path)
    for schluessel in ("c3", "a1", "b2"):
        cache.lege_ab(schluessel, {"x": 1})
    (tmp_path / ".a1.abc.tmp").write_text("halb", encoding="utf-8")
    (tmp_path / "notizen.txt").write_text("fremd", encoding="utf-8")

    assert cache.schluessel() == ["a1", "b2", "c3"]


def test_schluessel_eines_leeren_caches_ist_leer(tmp_path):
    assert ArtefaktCache(tmp_path / "neu").schluessel() == []


# --------------------------------------------------------------------------------------
# Zusammenspiel: ein Lauf mit Cache und Skip-on-Error, ohne einen einzigen echten Knoten
# --------------------------------------------------------------------------------------

def test_lauf_mit_cache_und_uebersprungenen_knoten(tmp_path):
    """Ein trockener Durchlauf der ganzen Mechanik — Reihenfolge, Hashes, Cache, Skip.

    Ausgeführt wird nichts; die „Arbeit“ ist ein dict. Genau darum ist der Test hier
    richtig: Er prüft die Ablaufsteuerung, nicht die Bildkette.
    """
    graph = bildkette()
    cache = ArtefaktCache(tmp_path)
    hashes: dict[str, str] = {}
    gerechnet: list[str] = []

    def lauf(kaputt: str | None = None) -> list[str]:
        gerechnet.clear()
        uebersprungen = set()
        for kid in graph.topologische_reihenfolge():
            if kid in uebersprungen:
                continue
            knoten = graph.knoten[kid]
            schluessel = inhalts_hash(knoten, [hashes[v] for v in graph.vorgaenger(kid)])
            hashes[kid] = schluessel
            if kid == kaputt:
                uebersprungen |= graph.nachfolger_transitiv([kid])
                continue
            if cache.hole(schluessel) is None:
                gerechnet.append(kid)
                cache.lege_ab(schluessel, {"knoten": kid})
        return list(gerechnet)

    # Erster Lauf: alles neu. Zweiter: nichts mehr zu tun.
    assert lauf() == ["geometrie", "beauty", "tiefe", "bild", "qa"]
    assert lauf() == []

    # Ein geänderter Parameter tief in der Kette muss alles dahinter neu rechnen —
    # über die Vorgänger-Hashes, ohne dass irgendwo eine Invalidierung programmiert wäre.
    graph = Graph([
        k if k.id != "tiefe" else Knoten("tiefe", "tiefenkarte", {"aufloesung": 1024}, ("geometrie",))
        for k in bildkette().knoten.values()
    ])
    assert lauf() == ["tiefe", "bild", "qa"]

    # Scheitert die Tiefenkarte, wird alles dahinter übersprungen — und der unbeteiligte
    # Beauty-Zweig bleibt unberührt (er lag schon im Cache).
    cache.leere()
    assert lauf(kaputt="tiefe") == ["geometrie", "beauty"]
