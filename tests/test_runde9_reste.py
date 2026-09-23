"""Runde 9 — die Reste der Durchsicht der Runde 8, nachgestellt am 23.09.2026.

Befunde (jeder zuerst selbst nachgefahren, Python 3.11)
-------------------------------------------------------
R1. ``kamera_zu_spec`` und ``spec_zu_kamera`` meldeten einen Punkt mit falscher Länge mit
    ``repr`` der ganzen Liste. ``auge [10**5000, 0, 0, 0]`` warf darum aus dem Satz
    selbst einen nackten ``ValueError`` statt ``SzenenError``. Dasselbe bei einer
    riesigen Zahl in einem Block (``[[10**5000], 0, 0]``) — dort warf ``_zeige``, und
    mit ihm jeder Satz aus ``lies_zahl``.
R2. Alle drei Kamerafunktionen nahmen ``True`` und ``'5'`` als Koordinaten an:
    ``kamera_zu_spec(auge=[True, '5', 0])`` ergab ``position [1.0, 5.0, 0.0]``. Vorher
    nachgelesen: KosmoOrbit schickt Koordinaten nirgends als Text (keine ``ANTWORT-*``,
    kein abgelegter Auftrag, kein Dokument; einziger Treffer unser eigener Gegentest).
    Entscheid: nur echte Zahlen, mit ``lies_zahl`` je Koordinate — dieselbe Regel.
R3. ``kosmo_naht.als_kosmo_auftrag`` liess ``aufloesung: None`` weg, schickte aber
    ``samples``, ``bbox`` usw. als ``null`` in ``params``. Dieselbe Unbekannte, zwei
    Behandlungen. Seither fällt jedes ``None`` in ``params`` weg.
R4. ``werkzeuge.enqueue_render`` überging ``faithful`` STILL: Der Auftrag wurde mit 0.8
    gerechnet, was immer bestellt war. Seither mit ``REGEL_TREUE`` gelesen und über
    eigene Ablage → ``als_render_scene`` → ``lies_szene`` → ``verarbeiter`` bis zur
    ``controlnet_staerke`` getragen. ``faithful_slider`` (KosmoOrbits eigener Regler,
    «structural faithfulness (denoise)») wird mit Satz ABGEWIESEN: Er meint die
    Entrauschung, die diese Lane nicht aus der Bestellung setzt, und seine Richtung
    gegenüber der ControlNet-Stärke ist offen.

R5 (der Docstring von ``lies_zahl``) ist Text und hat keinen Wächter.

Bewacht über den Weg, den das Produkt geht: Brücke → ``durchgang`` für die Kameras der
Bestellung, ``enqueue_render`` → eigene Ablage → Naht → ``verarbeiter`` mit Attrappen
für die Treue. ``kamera_zu_spec`` und ``kamera_nach_blender`` sind öffentlich und werden
darum auch direkt gerufen.

Regel 3: Szenen, Aufträge und Punkte sind synthetisch.
"""
from __future__ import annotations

import pytest

from aiimaging import (abholer, bruecke, eigene_quelle, jobs, kosmo_naht, kosmo_szene,
                       werkzeuge)
from aiimaging.kosmo_szene import SzenenError

import test_abholer
from test_abholer import _auftrag
from test_runde7b_einlass import _durchgang_bruecke, _laufzettel, _szene

#: Eine ganze Zahl mit 5001 Stellen: `repr` wirft darauf ab Python 3.11 `ValueError`.
UEBER_4300 = 10**5000

GUTE_KAMERA = {"kuerzel": "k", "auge": [40.0, -30.0, 1.7], "blick_auf": [10.0, 8.0, 4.5],
               "brennweite_mm": 35.0}
GUTE_SPEC = {"name": "k1", "position": [40.0, -30.0, 1.7], "target": [10.0, 8.0, 4.5],
             "fov": 50.0, "up_axis": "z"}


@pytest.fixture()
def ablage(tmp_path, monkeypatch):
    """Eine eigene Ablage — **nie** die des Benutzers."""
    ziel = tmp_path / "aiimaging-jobs"
    monkeypatch.setenv(werkzeuge.UMGEBUNG_JOBS, str(ziel))
    return ziel


# ======================================================================================
# R1 · Der Satz über einen falschen Punkt wird nicht selbst zum Fehler
# ======================================================================================

VIER_MIT_RIESIG = [UEBER_4300, 0, 0, 0]
RIESIG_IM_BLOCK = [[UEBER_4300], 0, 0]


@pytest.mark.parametrize("punkt", [VIER_MIT_RIESIG, RIESIG_IM_BLOCK],
                         ids=["vier_eintraege", "riesig_im_block"])
@pytest.mark.parametrize("aufruf", [
    lambda p: kosmo_szene.kamera_zu_spec(dict(GUTE_KAMERA, auge=p)),
    lambda p: kosmo_szene.kamera_zu_spec(dict(GUTE_KAMERA, blick_auf=p)),
    lambda p: kosmo_szene.spec_zu_kamera(dict(GUTE_SPEC, position=p)),
    lambda p: kosmo_szene.spec_zu_kamera(dict(GUTE_SPEC, target=p)),
    lambda p: kosmo_szene.kamera_nach_blender(p, "y"),
], ids=["kamera_zu_spec_auge", "kamera_zu_spec_blick", "spec_zu_kamera_position",
        "spec_zu_kamera_target", "kamera_nach_blender"])
def test_ein_falscher_punkt_mit_riesiger_zahl_ist_ein_szenenfehler(aufruf, punkt):
    """**Der Wächter von R1.** Bis zur Runde 9 warf hier ``ValueError`` (Grenze der
    Umwandlung in Text) — aus dem Satz, der den Fehler erklären sollte."""
    with pytest.raises(SzenenError, match="über 4300 Stellen|rund 5001 Stellen"):
        aufruf(punkt)


def test_ein_falscher_punkt_der_bestellung_haelt_nur_seinen_auftrag_auf(tmp_path):
    """R1 über den Produktweg: Brücke → ``durchgang``.

    **Eine Zahl mit über 4300 Stellen erreicht diesen Weg nicht** (nachgefahren am
    23.09.2026): ``json.loads`` weist sie selbst mit ``ValueError`` ab, bevor
    ``lies_szene`` sie sieht. Der Wurf aus dem Satz war also nur über die öffentlichen
    Funktionen erreichbar (oben). Auf diesem Weg zeigt sich derselbe Satzbau an einer Zahl
    mit 401 Stellen: Bis zur Runde 9 stand sie mit allen Ziffern im Grund, seither als
    Stellenzahl — und der nächste Auftrag wird gerechnet."""
    kamera = dict(GUTE_SPEC, position=[10**400, 0, 0, 0])
    kaputt = _auftrag(tmp_path, "vis-1700000000-aaaaaa",
                      szene=dict(_szene(), cameras=[kamera]))
    gut = _auftrag(tmp_path, "vis-1700000001-bbbbbb")

    bericht, gesehen = _durchgang_bruecke(tmp_path)

    assert gesehen == [gut.name]
    grund = bericht["ergebnisse"][0]["grund"]
    assert ("CameraSpec 'position' ist kein Punkt aus drei Zahlen: [eine ganze Zahl mit "
            "rund 401 Stellen, 0, 0, 0]") in grund, grund
    assert "0" * 400 not in grund
    assert "kein Punkt aus drei Zahlen" in _laufzettel(kaputt)[bruecke.FELD_MELDUNG]


def test_eine_riesige_zahl_im_block_ist_auch_fuer_render_ein_satz():
    """Derselbe Fehler in ``lies_zahl``: Der Satz über ``samples: [10**5000]`` warf."""
    zahl, satz = kosmo_szene.lies_zahl([UEBER_4300], "render.samples",
                                       **kosmo_szene.REGEL_SAMPLES)
    assert zahl is None
    assert "ein list mit einer ganzen Zahl von über 4300 Stellen darin" in satz


# ======================================================================================
# R2 · Eine Koordinate ist eine echte Zahl — kein Wahrheitswert, kein Text
# ======================================================================================

UNECHT = [
    ([True, 0.0, 0.0], "'{f}[0]' ist True", "ein Wahrheitswert ist keine Zahl"),
    ([0.0, "5", 0.0], "'{f}[1]' ist '5'", "str ist keine Zahl"),
    ([0.0, 0.0, None], "'{f}[2]' ist None", "NoneType ist keine Zahl"),
]


@pytest.mark.parametrize("punkt, feldsatz, grund", UNECHT,
                         ids=["wahrheitswert", "text", "null"])
@pytest.mark.parametrize("aufruf, feld", [
    (lambda p: kosmo_szene.kamera_zu_spec(dict(GUTE_KAMERA, auge=p)), "auge"),
    (lambda p: kosmo_szene.kamera_zu_spec(dict(GUTE_KAMERA, blick_auf=p)), "blick_auf"),
    (lambda p: kosmo_szene.spec_zu_kamera(dict(GUTE_SPEC, position=p)), "position"),
    (lambda p: kosmo_szene.spec_zu_kamera(dict(GUTE_SPEC, target=p)), "target"),
    (lambda p: kosmo_szene.kamera_nach_blender(p, "z"), "punkt"),
], ids=["kamera_zu_spec_auge", "kamera_zu_spec_blick", "spec_zu_kamera_position",
        "spec_zu_kamera_target", "kamera_nach_blender"])
def test_eine_unechte_koordinate_wird_abgewiesen(aufruf, feld, punkt, feldsatz, grund):
    """**Der Wächter von R2.** Bis zur Runde 9 wurde ``True`` still 1.0 und ``'5'`` still
    5.0. Der Satz ist der von ``lies_zahl`` — dieselbe Regel wie für ``render.*``."""
    with pytest.raises(SzenenError, match="keine Zahlen") as fehler:
        aufruf(punkt)
    assert feldsatz.format(f=feld) in str(fehler.value), str(fehler.value)
    assert grund in str(fehler.value)


@pytest.mark.parametrize("punkt", [[True, -30.0, 1.7], ["40", -30.0, 1.7]],
                         ids=["wahrheitswert", "text"])
def test_eine_unechte_koordinate_der_bestellung_haelt_nur_ihren_auftrag_auf(
        tmp_path, punkt):
    """R2 über den Produktweg: Die Kamera kam bis zur Runde 9 als ``(1.0, -30.0, 1.7)``
    beim Runner an."""
    kaputt = _auftrag(tmp_path, "vis-1700000000-aaaaaa",
                      szene=dict(_szene(), cameras=[dict(GUTE_SPEC, position=punkt)]))
    gut = _auftrag(tmp_path, "vis-1700000001-bbbbbb")

    bericht, gesehen = _durchgang_bruecke(tmp_path)

    assert gesehen == [gut.name]
    satz = f"'position[0]' ist {punkt[0]!r}"
    assert satz in bericht["ergebnisse"][0]["grund"], bericht["ergebnisse"][0]["grund"]
    assert satz in _laufzettel(kaputt)[bruecke.FELD_MELDUNG]


def test_gegenprobe_ganze_und_gleitkommazahlen_bleiben_koordinaten():
    """Die Regel nimmt nichts weg, was ging: ``40`` und ``40.0`` sind dieselbe Koordinate."""
    spec = kosmo_szene.kamera_zu_spec(dict(GUTE_KAMERA, auge=[40, -30, 2]))
    assert spec["position"] == [40.0, -30.0, 2.0]
    assert all(type(v) is float for v in spec["position"])
    kamera = kosmo_szene.spec_zu_kamera(dict(GUTE_SPEC, position=(1, 2, 3)))
    assert kamera["auge"] == (1.0, 2.0, 3.0)


@pytest.mark.parametrize("punkt", [[1, 2], [1, 2, 3, 4], "1,2,3", None],
                         ids=["zwei", "vier", "text", "null"])
def test_kamera_nach_blender_verlangt_drei_eintraege(punkt):
    """Ihr Docstring sagt «drei Zahlen»; bis zur Runde 9 kam ``[1, 2]`` bei ``z`` still als
    Paar zurück."""
    with pytest.raises(SzenenError, match="kein Punkt aus drei Zahlen"):
        kosmo_szene.kamera_nach_blender(punkt, "z")


def test_kamera_zu_spec_sagt_szenenerror_auch_ohne_woerterbuch():
    with pytest.raises(SzenenError, match="kein Wörterbuch"):
        kosmo_szene.kamera_zu_spec(["auge", "blick_auf"])


# ======================================================================================
# R3 · None heisst nicht bestellt — für jedes Feld der Bestellung
# ======================================================================================

def _argumente(tmp_path, **zusatz) -> dict:
    glb = tmp_path / "modell.glb"
    glb.write_bytes(test_abholer._minimale_glb())
    argumente = {"glb_path": str(glb), "up_axis": "Y", "bbox": [[0, 0, 0], [20, 15, 10]],
                 "out_dir": str(tmp_path / "out"),
                 "approval_token": jobs.TOKEN_PRAEFIX + "TEST"}
    argumente.update(zusatz)
    return argumente


def _abgelegt(ablage, antwort) -> dict:
    assert antwort["status"] == jobs.STATUS_QUEUED, antwort
    return jobs.lies_job(antwort["job_id"], ablage / antwort["job_id"])


def test_kein_null_in_ihren_params(tmp_path, ablage):
    """**Der Wächter von R3**, über den Produktweg: ``enqueue_render`` ohne Zahlen legt
    ``None`` ab, und die Naht schickt davon NICHTS hinüber — wie bei der Auflösung."""
    satz = _abgelegt(ablage, werkzeuge.enqueue_render(_argumente(tmp_path)))
    nichts = {k for k, v in satz["params"].items() if v is None}
    assert {"aufloesung", "samples", "faithful"} <= nichts, "Vorbedingung"

    fremd = kosmo_naht.als_kosmo_auftrag(satz)

    assert not [k for k, v in fremd["params"].items() if v is None], fremd["params"]
    assert not nichts & set(fremd["params"])
    assert fremd["params"]["glb_path"] == satz["params"]["glb_path"]


def test_gegenprobe_bestellte_zahlen_gehen_weiter_hinueber(tmp_path, ablage):
    satz = _abgelegt(ablage, werkzeuge.enqueue_render(
        _argumente(tmp_path, samples=64, faithful=0.25, aufloesung=512)))

    fremd = kosmo_naht.als_kosmo_auftrag(satz)

    assert fremd["params"]["samples"] == 64
    assert fremd["params"]["faithful"] == 0.25
    assert fremd["params"]["resolution"] == "512x512"
    # Ausserhalb von `params` bleibt das leere Feld eine Aussage über unseren Satz.
    assert "progress" in fremd and fremd["progress"] is None


# ======================================================================================
# R4 · faithful am MCP-Einlass wirkt — bis zur ControlNet-Stärke
# ======================================================================================

def _render_auftraege(tmp_path, ablage) -> list:
    """Die eigene Ablage durch ``durchgang`` mit dem echten ``verarbeiter`` und Attrappen
    für Multipass und Render; zurück kommen die ``RenderAuftrag``-Objekte."""
    protokoll, attrappen = test_abholer._kette()
    bericht = abholer.durchgang(
        ablage, quelle=eigene_quelle, darf_rechnen=lambda: (True, "frei"),
        verarbeite=abholer.verarbeiter(out_wurzel=tmp_path / "aus", **attrappen))
    assert bericht["verarbeitet"] == 1, bericht["ergebnisse"]
    assert protokoll["render"], "Vorbedingung: es wurde gerendert"
    return protokoll["render"]


@pytest.mark.parametrize("wert, erwartet", [(0.3, 0.3), (0, 0.0), (1, 1.0)],
                         ids=["drei_zehntel", "null_ganz", "eins_ganz"])
def test_faithful_am_einlass_kommt_als_controlnet_staerke_an(
        tmp_path, ablage, wert, erwartet):
    """**Der Wächter von R4.** Bis zur Runde 9 rechnete jeder dieser Aufträge mit 0.8."""
    satz = _abgelegt(ablage, werkzeuge.enqueue_render(_argumente(tmp_path, faithful=wert)))
    assert satz["params"]["faithful"] == erwartet
    assert type(satz["params"]["faithful"]) is float, "abgelegt wird die gelesene Zahl"

    for auftrag in _render_auftraege(tmp_path, ablage):
        assert auftrag.controlnet_staerke == erwartet


def test_gegenprobe_ohne_faithful_gilt_die_vorgabe_des_vertrags(tmp_path, ablage):
    werkzeuge.enqueue_render(_argumente(tmp_path))
    for auftrag in _render_auftraege(tmp_path, ablage):
        assert auftrag.controlnet_staerke == 0.8


@pytest.mark.parametrize("wert", [5.0, -0.1, True, "hoch", float("nan")],
                         ids=["fuenf", "minus", "wahrheitswert", "text", "nan"])
def test_ein_unbrauchbares_faithful_am_einlass_legt_nichts_ab(tmp_path, ablage, wert):
    """Dieselbe Regel wie in ``lies_szene`` (``REGEL_TREUE``): abgewiesen, bevor etwas
    abgelegt wird — nicht erst beim Abholer."""
    antwort = werkzeuge.enqueue_render(_argumente(tmp_path, faithful=wert))

    assert antwort["status"] is None and antwort["job_id"] is None
    assert f"'faithful' ist {wert!r}, erwartet war eine endliche Zahl ab 0 bis 1" \
        in antwort["error"], antwort["error"]
    assert not ablage.exists() or not any(ablage.iterdir()), "es wurde nichts abgelegt"


@pytest.mark.parametrize("zusatz", [{"faithful_slider": 0.5},
                                    {"faithful_slider": 0.5, "faithful": 0.5}],
                         ids=["allein", "neben_faithful"])
def test_faithful_slider_wird_mit_satz_abgewiesen(tmp_path, ablage, zusatz):
    """Nicht still übergangen und nicht geraten: Der Regler meint drüben die
    Entrauschung, und ihre Richtung gegenüber der ControlNet-Stärke ist offen."""
    antwort = werkzeuge.enqueue_render(_argumente(tmp_path, **zusatz))

    assert antwort["status"] is None and antwort["job_id"] is None
    assert "'faithful_slider' ist 0.5 und wirkt hier nicht" in antwort["error"]
    assert "denoise" in antwort["error"]
    assert not ablage.exists() or not any(ablage.iterdir()), "es wurde nichts abgelegt"


def test_gegenprobe_faithful_slider_null_ist_nicht_bestellt(tmp_path, ablage):
    """``null`` heisst auch hier: nicht bestellt — der Auftrag entsteht."""
    satz = _abgelegt(ablage, werkzeuge.enqueue_render(
        _argumente(tmp_path, faithful_slider=None)))
    assert "faithful_slider" not in satz["params"]
