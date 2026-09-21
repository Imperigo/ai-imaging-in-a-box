"""Ein glb-Eingang ohne mitgelieferte Ausdehnung sperrte den ganzen Weg.

**Am 21.09.2026 von der HomeStation auf zwei unabhängigen Wegen gemeldet** —
`auf-20260921-127` am Graphenweg (`baue_kette` → `fuehre_aus`) und `auf-20260921-136` am
Produktweg (Tür → Mappe → Arbeitsgang). Beide brachen am **ersten** Knoten mit demselben
Satz ab:

    Torwächter: Konversion meldet status='ok', trägt aber keine brauchbare bbox (None).

Der Torwächter hatte recht — er bekam wirklich keine. Nur lag das nicht am Modell: Beim
glb-Eingang gab es überhaupt keine Stelle, an der die Ausdehnung herkam. Der Produktweg
wandelt die IFC beim Import und reicht der Kette danach nur noch den glb-Pfad; die
Ausdehnung aus dem Wandlungsbericht bleibt unterwegs liegen.

*Eine Angabe, die das Programm aus der Datei selbst ausrechnen kann, darf es nicht vom
Aufrufer verlangen.*

Die Wächter hier prüfen darum nicht, dass eine Zeile dasteht, sondern **dass der Knoten
durchkommt** — und im Gegenfall, dass er mit der ehrlichen Begründung stehen bleibt statt
eine Ausdehnung zu erfinden.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

from aiimaging import glbbox, kette, torwaechter

WERKZEUG = Path(__file__).resolve().parents[1] / "tools" / "make_test_glb.py"

#: Bauwerk 12 × 9 × 15 m auf einer Geländeplatte 40 × 30 m, in glTF-Koordinaten.
SZENE = (
    ("IfcSlab_Gelaende_0aBcDeFgHiJkLmNoPqRsTu", (-14.0, -0.5, -12.0), (26.0, 0.0, 18.0)),
    ("IfcWall_Aussenwand_1aBcDeFgHiJkLmNoPqRsT", (0.0, 0.0, 0.0), (12.0, 15.0, 9.0)),
)


def _erzeuger():
    spez = importlib.util.spec_from_file_location("make_test_glb_fuer_bbox", WERKZEUG)
    modul = importlib.util.module_from_spec(spez)
    sys.modules[spez.name] = modul
    spez.loader.exec_module(modul)
    return modul


@pytest.fixture
def szene_glb(tmp_path):
    pfad = tmp_path / "szene.glb"
    pfad.write_bytes(_erzeuger().baue_glb(SZENE))
    return pfad


def _geometrieknoten(graph):
    for knoten in graph.knoten.values() if hasattr(graph, "knoten") else graph:
        if getattr(knoten, "art", None) == kette.ART_GEOMETRIE:
            return knoten
    raise AssertionError("kein Geometrieknoten im Graphen")


def _baue(glb_path, **zusatz):
    return kette.baue_kette(
        glb_path=str(glb_path), up_axis="Y", prompt="ein Haus am Hang", **zusatz,
    )


# --------------------------------------------------------------------------------------
# 1 · Der Befund selbst: der Knoten kommt durch, ohne dass jemand die bbox mitgibt
# --------------------------------------------------------------------------------------

def test_ein_glb_eingang_ohne_bbox_kommt_durch(tmp_path, szene_glb):
    """Der Wächter für den gemeldeten Abbruch — und er prüft die **Wirkung**.

    Nicht «steht die Zeile da», sondern: Der Knoten, der am 21.09. jeden Lauf gestoppt
    hat, läuft durch und trägt danach eine Ausdehnung.
    """
    graph = _baue(szene_glb)
    knoten = _geometrieknoten(graph)

    aus = kette._fuehre_geometrie(knoten=knoten, eingaben=[], out_dir=tmp_path)

    assert aus["status"] == kette.STATUS_OK, aus.get("error")
    assert aus["bbox"] is not None, (
        "ohne Ausdehnung lehnt der Torwaechter ab — genau der gemeldete Abbruch")
    assert aus["torwaechter"]["entscheidung"] == torwaechter.ENTSCHEIDUNG_ANNEHMEN


def test_die_bbox_ist_die_szenenbox_und_nicht_die_bauwerksbox(tmp_path, szene_glb):
    """**Der Unterschied, den man leicht verwechselt — und der hier zählt.**

    Der Torwächter prüft den Massstab der *Konversion*: Dafür gilt, was in der Datei
    steht, nicht was davon Bauwerk ist. Die Bauwerksbox ist der Weg für die **Kamera**.
    Wer hier die kleinere Box einsetzte, prüfte den Massstab eines Ausschnitts.
    """
    graph = _baue(szene_glb)
    aus = kette._fuehre_geometrie(
        knoten=_geometrieknoten(graph), eingaben=[], out_dir=tmp_path)
    erwartet = glbbox.bauwerksbox(szene_glb, up_axis="Y")

    assert aus["bbox"] == erwartet["bbox_szene"]
    assert aus["bbox"] != erwartet["bbox_bauwerk"], (
        "Szenen- und Bauwerksbox sind in dieser Szene verschieden — sonst prueft der "
        "Test nichts")


def test_eine_ausdrueckliche_bbox_gewinnt_gegen_die_datei(tmp_path, szene_glb):
    """Wer die Ausdehnung kennt, hat sie meist aus einer Quelle, die mehr weiss."""
    eigene = [[0.0, 0.0, 0.0], [8.0, 5.0, 3.25]]
    graph = _baue(szene_glb, bbox=eigene)

    aus = kette._fuehre_geometrie(
        knoten=_geometrieknoten(graph), eingaben=[], out_dir=tmp_path)

    assert aus["bbox"] == eigene
    assert aus["bbox"] != glbbox.bauwerksbox(szene_glb, up_axis="Y")["bbox_szene"]


# --------------------------------------------------------------------------------------
# 2 · Die dritte Antwort bleibt: unlesbar heisst nicht geraten
# --------------------------------------------------------------------------------------

def test_eine_unlesbare_glb_wird_abgelehnt_statt_geraten(tmp_path):
    """**Die Gegenprobe zur Reparatur.**

    Eine erfundene Ausdehnung liesse die Massstabsprüfung stillschweigend bestehen — und
    damit wäre der Torwächter ein Abzeichen ohne Prüfung. Nicht lesbar heisst darum:
    abgelehnt, mit seiner eigenen Begründung.
    """
    kaputt = tmp_path / "kaputt.glb"
    kaputt.write_bytes(b"das ist keine glb")
    graph = _baue(kaputt)

    aus = kette._fuehre_geometrie(
        knoten=_geometrieknoten(graph), eingaben=[], out_dir=tmp_path)

    assert aus["status"] == kette.STATUS_ABGELEHNT
    assert aus["bbox"] is None
    assert "bbox" in aus["error"]


# --------------------------------------------------------------------------------------
# 3 · Die zweite Falle im selben Knoten: `.get(schluessel, ersatz)` bei gesetztem None
# --------------------------------------------------------------------------------------

def test_ein_report_mit_bbox_none_faellt_auf_die_angabe_zurueck(tmp_path, monkeypatch):
    """``dict.get(k, ersatz)`` liefert den Ersatz **nur bei fehlendem Schlüssel**.

    Trägt der Wandlungsbericht den Schlüssel ``bbox`` mit dem Wert ``None``, gewinnt die
    ``None`` gegen die Angabe des Aufrufers — derselbe Griff, der am selben Tag schon
    `homeworker._darf_starten` zu Fall gebracht hat. Hier kostet er den ganzen Lauf.
    """
    eigene = [[0.0, 0.0, 0.0], [8.0, 5.0, 3.25]]
    ifc = tmp_path / "haus.ifc"
    ifc.write_text("ISO-10303-21;", encoding="utf-8")

    def falscher_bericht(quelle, ziel, **_):
        return {"status": "ok", "glb_path": ziel, "up_axis": "Y", "bbox": None}

    monkeypatch.setattr(kette.seams, "ifc_zu_glb", falscher_bericht)
    monkeypatch.setattr(kette, "_raeume_lesen", lambda *_a, **_k: None)

    graph = kette.baue_kette(ifc_path=str(ifc), prompt="ein Haus", bbox=eigene)
    aus = kette._fuehre_geometrie(
        knoten=_geometrieknoten(graph), eingaben=[], out_dir=tmp_path)

    assert aus["bbox"] == eigene, (
        "ein gesetztes None im Bericht darf die Angabe des Aufrufers nicht schlagen")
    assert aus["status"] == kette.STATUS_OK
