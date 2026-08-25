"""Vier Funktionen, die niemand ruft — gezählt statt einzeln gestolpert.

Diese Woche sind **fünf** tote Kanten einzeln aufgefallen: `komposition.py`, `befund.json`,
der Bauteilwächter, der Maskenanker und die Kompositionsprüfung auf dem Produktivweg. Jede
war ein Zufallsfund.

Am 25.08.2026 habe ich stattdessen **gezählt**: 256 öffentliche Funktionen, davon 67 vom
Produktpfad nicht gerufen. Die meisten davon sind zu Recht ungerufen — Einstiegspunkte für
Werkzeuge, MCP-Werkzeuge über eine Registry, Studienläufe. **Eine rohe Zahl ist hier keine
Prüfung**, und ein Test darauf wäre 67 Fehlalarme.

**Vier sind es wirklich: null Produktrufe UND null Testrufe.** Sie sind verschiedener
Natur, und darum steht hier für jede etwas anderes.
"""
from __future__ import annotations

import json

import pytest

from aiimaging import auftrag, contracts, gate


# --------------------------------------------------------------------------------------
# 1 · `als_kosmovis_verdikt` — die bitterste
# --------------------------------------------------------------------------------------
#
# Ihr eigener Docstring sagt, wogegen sie gebaut wurde: «Das ist der Phase-0-Befund in
# seiner teuersten Auspraegung: eine tote Kante, die niemand meldet.» Sie ist selbst eine.
#
# Ob sie WEG gehoert oder ANGESCHLOSSEN, entscheidet eine Auskunft, die wir nicht haben:
# Liest noch jemand diese Feldnamen? Das steht als Frage im Auftrag an den Cloud-Worker.
# Bis dahin ist sie wenigstens geprueft — ungetestet ist schlimmer als ungerufen.

GEO_OK = {"score": 0.9, "schwelle": 0.65, "bestanden": True, "status": "ok"}
STIL_OK = {"score": 0.8, "schwelle": 0.666, "bestanden": True, "status": "ok"}


def test_die_uebersetzung_traegt_genau_die_neun_fremden_feldnamen():
    """Der Zweck der Funktion ist die **Namensgleichheit** — sie ist die ganze Zusage.

    KosmoOrbit verdrahtet über Feldnamen, ohne Fehlermeldung. Ein fehlender Name ist dort
    kein Fehler, sondern Stille.
    """
    v = gate.als_kosmovis_verdikt(gate.gesamturteil(GEO_OK, STIL_OK))

    assert set(v) == {"released", "passed", "style_status", "geometry_status",
                      "fail_reasons", "style_score", "geometry_fidelity",
                      "style_threshold", "geometry_threshold"}


def test_released_ist_fail_closed_und_nie_None():
    """Nur wenn beide Gates `ok` sind **und** beide bestehen."""
    beide = gate.als_kosmovis_verdikt(gate.gesamturteil(GEO_OK, STIL_OK))
    geo_faellt = gate.als_kosmovis_verdikt(
        gate.gesamturteil(dict(GEO_OK, bestanden=False), STIL_OK))
    ohne_stil = gate.als_kosmovis_verdikt(gate.gesamturteil(GEO_OK, {}))

    assert beide["released"] is True
    assert geo_faellt["released"] is False
    assert ohne_stil["released"] is False, "fehlt ein Gate, wird NICHT freigegeben"


def test_passed_bleibt_dreiwertig_wo_released_es_nicht_darf():
    """Der Unterschied ist der ganze Grund für zwei Felder.

    `released` ist eine **Handlung** — freigeben oder nicht, dazwischen gibt es nichts.
    `passed` ist eine **Auskunft** und darf «weiss nicht» sagen.
    """
    ohne_stil = gate.als_kosmovis_verdikt(gate.gesamturteil(GEO_OK, {}))

    assert ohne_stil["passed"] is None
    assert ohne_stil["released"] is False


def test_die_form_ist_eine_ANDERE_als_die_von_als_ergebnis():
    """**Und das ist die eigentliche offene Frage.**

    `kosmo_szene.als_ergebnis` liefert `render-result/v2` — verschachtelt, mit
    `qa.verdict`. Diese hier liefert neun flache Felder. Beide beschreiben dasselbe
    Doppel-Gate. Ob der Empfänger der flachen Namen noch existiert, wissen wir nicht;
    solange nicht, ist die Funktion weder anzuschliessen noch zu löschen.
    """
    from aiimaging import kosmo_szene

    flach = gate.als_kosmovis_verdikt(gate.gesamturteil(GEO_OK, STIL_OK))
    verschachtelt = kosmo_szene.als_ergebnis(
        "vis-1-abcdef", ["a.png"],
        geometrie_urteil={"score": 0.9, "bestanden": True, "nullanker": {"x": 1}})

    assert "geometry_fidelity" in flach
    assert "geometry_fidelity" not in verschachtelt["qa"]
    assert "geometry_fidelity" in verschachtelt["qa"]["geometry"], (
        "dieselbe Zahl, ein Stockwerk tiefer — genau daran haengt die Frage")


# --------------------------------------------------------------------------------------
# 2 · `load_render_scene` — ausgeführt, exportiert, ungetestet
# --------------------------------------------------------------------------------------

def test_eine_szene_wird_aus_einer_datei_gelesen_und_geprueft(tmp_path):
    """Sie steht in `aiimaging.__init__` und ist damit **öffentliche Zusage**.

    Eine exportierte Funktion ohne Test ist schlimmer als eine ungerufene: Wer sie von
    aussen benutzt, verlässt sich auf etwas, das niemand nachgesehen hat.
    """
    pfad = tmp_path / "szene.json"
    pfad.write_text(json.dumps({"geometry": {"glb_path": "/x/y.glb", "up_axis": "Y"},
                                "out_dir": "/x/out"}), encoding="utf-8")

    szene = contracts.load_render_scene(pfad)

    assert szene["geometry"]["glb_path"] == "/x/y.glb"
    assert szene["geometry"]["up_axis"] == "Y", (
        "die Hochachse wird geprueft und nicht geraten — das ist der Phase-0-Befund")


def test_eine_szene_ohne_geometriequelle_wird_abgewiesen(tmp_path):
    """Die Prüfung gehört zur Zusage — sonst wäre es nur ein `json.load` mit Umweg."""
    pfad = tmp_path / "leer.json"
    pfad.write_text(json.dumps({"geometry": {}}), encoding="utf-8")

    with pytest.raises(contracts.ContractError, match="ifc_path oder glb_path"):
        contracts.load_render_scene(pfad)


def test_eine_kaputte_datei_wird_abgewiesen_und_nicht_halb_gelesen(tmp_path):
    pfad = tmp_path / "kaputt.json"
    pfad.write_text("{ das ist kein json", encoding="utf-8")

    with pytest.raises(json.JSONDecodeError):
        contracts.load_render_scene(pfad)


# --------------------------------------------------------------------------------------
# 3 · `neue_auftrag_id` — es gab sie, und ich habe eine Woche von Hand gezählt
# --------------------------------------------------------------------------------------

def test_die_kennung_entsteht_aus_datum_und_laufnummer():
    """**Ein Befund über die eigene Arbeitsweise.**

    Diese Funktion steht seit Phase 0 da. Ich habe die Kennungen der letzten Woche
    trotzdem von Hand geschrieben — und genau dabei ist eine Kollision entstanden:
    `auf-20260823-38` (unsere) und `auf-20260824-38` (ihre) tragen dieselbe Nummer an
    verschiedenen Tagen. Von Hand gezählt heisst: irgendwann doppelt.
    """
    assert auftrag.neue_auftrag_id("20260825", 41) == "auf-20260825-41"
    assert auftrag.neue_auftrag_id("20260825", 7) == "auf-20260825-07", (
        "zweistellig — sonst sortiert 10 vor 7"
    )


def test_die_erzeugte_kennung_besteht_die_eigene_pruefung():
    """Sonst wäre sie eine Falle: erzeugt, aber nicht schreibbar."""
    kennung = auftrag.neue_auftrag_id("20260825", 41)
    satz = auftrag.baue_auftrag(auftrag_id=kennung, art="qa", synthetisch=True,
                                beschreibung="Probe, ob die erzeugte Kennung traegt.")

    assert satz["auftrag_id"] == kennung
