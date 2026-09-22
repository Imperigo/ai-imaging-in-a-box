"""Kommt das Ausgangsbild an? — die Auskunft steht am Registereintrag.

Befund 22.09.2026
-----------------
``kette.bildeingang_lage('z-image-turbo')`` meldete ``traegt: None`` mit «NICHT GEMESSEN —
braucht einen Lauf an echten Gewichten». Gemessen war es aber: ``auf-20260919-123``
(sieben Läufe mit und ohne Ausgangsbild, eine einzige sha256) und bestätigt über den
Produktweg in ``auf-20260922-137`` V5 (``modus_abweichung`` True). Für den
VORGABE-Backbone stand damit die dritte Antwort, wo längst eine erste feststand.

Der Grund war ein Bauort: Die Funktion fragte den Namen ``qwen-image-edit-2511`` ab und
kannte sonst nichts. Seither steht die Auskunft als ``bildeingang_traegt`` mit
``bildeingang_beleg`` am Eintrag in ``backbone.py``, und ``bildeingang_lage`` liest sie.

Was hier geprüft wird, und über welchen Weg
-------------------------------------------
1. Der Vorgabe-Backbone trägt NICHT, mit Beleg.
2. Ein Eintrag ohne Messung bleibt ``None`` — die dritte Antwort wird nicht zu ``False``.
3. Das Register nimmt kein Urteil ohne Beleg an.
4. Die Auskunft kommt vom Eintrag, nicht vom Namen.
5. **Der Produktweg:** Ein Graph mit Nachrender, durch ``fuehre_aus`` gerechnet, trägt das
   gemessene Urteil in den Ausgaben des Nachrender-Knotens — dort, wo es gelesen wird.

Ohne GPU, ohne Gewichte, ohne Blender. Regel 3: Alle Bilder entstehen hier aus ein paar
Bytes; kein echtes Projektbild.
"""
from __future__ import annotations

import dataclasses
import struct
import zlib
from pathlib import Path

import pytest

from aiimaging import backbone, kette, render
from aiimaging.graph import ArtefaktCache
from aiimaging.kette import (
    ART_BILDQUELLE,
    ART_GEOMETRIE,
    ART_MULTIPASS,
    ART_NACHRENDER,
    ART_QA,
    ART_RENDER,
    baue_kette,
    fuehre_aus,
    haenge_nachrender_an,
)

BELEG_Z_IMAGE = "auf-20260919-123"
BESTAETIGUNG_Z_IMAGE = "auf-20260922-137"


# ======================================================================================
# Werkzeug
# ======================================================================================

def _png(pfad, werte=(0, 64, 128, 255)) -> Path:
    """Ein gültiges 2x2-Graustufen-PNG — echt, weil ``bildlesen.pruefe_png`` es liest."""
    roh = b"".join(b"\x00" + bytes(werte[z * 2:(z + 1) * 2]) for z in range(2))

    def block(art, nutz):
        return (struct.pack(">I", len(nutz)) + art + nutz
                + struct.pack(">I", zlib.crc32(art + nutz) & 0xFFFFFFFF))

    pfad = Path(pfad)
    pfad.parent.mkdir(parents=True, exist_ok=True)
    pfad.write_bytes(b"\x89PNG\r\n\x1a\n"
                     + block(b"IHDR", struct.pack(">IIBBBBB", 2, 2, 8, 0, 0, 0, 0))
                     + block(b"IDAT", zlib.compress(roh))
                     + block(b"IEND", b""))
    return pfad


class _Modell:
    """Ein Bildmodell, das nichts rechnet — die Frage hier ist die Auskunft, nicht das Bild."""

    def __call__(self, parameter: dict) -> dict:
        ziel = parameter["ausgabe_png"]
        _png(ziel, werte=(10, 20, 30, 40))
        return {"bild_png": ziel, "hinweise": [], "schritte_gerechnet": None}


@pytest.fixture
def eigenes_register(monkeypatch):
    """Eine Kopie des Registers, damit Probeeinträge nicht in andere Tests durchsickern."""
    kopie = dict(backbone.BACKBONES)
    monkeypatch.setattr(backbone, "BACKBONES", kopie)
    return kopie


# ======================================================================================
# 1 · Der Vorgabe-Backbone: gemessen, trägt nicht
# ======================================================================================

def test_der_vorgabe_backbone_traegt_das_ausgangsbild_gemessen_nicht():
    """Die erste Antwort, wo bis 22.09.2026 die dritte stand.

    Geprüft über ``render.VORGABE_BACKBONE`` und nicht nur über den Namen: Das ist der
    Backbone, auf dem ein Nachrender ohne ausdrückliche Wahl rechnet.
    """
    assert render.VORGABE_BACKBONE == "z-image-turbo"
    lage = kette.bildeingang_lage(render.VORGABE_BACKBONE)

    assert lage["traegt"] is False, (
        "gemessen in auf-20260919-123: sieben Läufe mit und ohne Ausgangsbild, eine "
        "sha256 — das Ausgangsbild kommt nicht an")
    assert BELEG_Z_IMAGE in lage["beleg"], "ein Urteil ohne Auftragskennung ist keines"
    assert BESTAETIGUNG_Z_IMAGE in lage["beleg"]
    assert "NICHT GEMESSEN" not in lage["beleg"]
    assert "Nicht gemessen" not in lage["grund"]


def test_qwen_edit_bleibt_beim_gemessenen_verlust():
    """Der Umzug an den Eintrag darf die ältere Messung nicht verlieren."""
    lage = kette.bildeingang_lage("qwen-image-edit-2511")
    assert lage["traegt"] is False
    assert "auf-20260818-09" in lage["beleg"]


# ======================================================================================
# 2 · Ohne Messung: die dritte Antwort, und sie bleibt es
# ======================================================================================

def test_ein_eintrag_ohne_messung_bleibt_nicht_gemessen():
    """``None`` heisst NICHT GEMESSEN — weder «trägt» noch «trägt nicht».

    Geprüft an JEDEM ungemessenen Eintrag des Registers, nicht an einem ausgesuchten.
    """
    ungemessen = [e.name for e in backbone.BACKBONES.values()
                  if e.bildeingang_traegt is None]
    assert "flux2-klein-4b" in ungemessen, (
        "für flux2-klein-4b ist der Bildeingang nicht gemessen; stünde er hier nicht, "
        "hätte jemand ein Urteil ohne Lauf eingetragen")
    for name in ungemessen:
        lage = kette.bildeingang_lage(name)
        assert lage["traegt"] is None, (
            f"{name}: aus 'nicht gemessen' ist {lage['traegt']!r} geworden")
        assert "NICHT GEMESSEN" in lage["beleg"], name


# ======================================================================================
# 3 · Das Register nimmt kein Urteil ohne Beleg an
# ======================================================================================

def test_ein_urteil_ohne_beleg_kommt_nicht_ins_register(eigenes_register):
    vorlage = backbone.hole("flux2-klein-4b")

    ohne_beleg = dataclasses.replace(vorlage, name="probe-ohne-beleg",
                                     bildeingang_traegt=False, bildeingang_beleg=None)
    with pytest.raises(backbone.BackboneError, match="Auftragskennung"):
        backbone._eintrag(ohne_beleg)

    beleg_ohne_urteil = dataclasses.replace(vorlage, name="probe-beleg-ohne-urteil",
                                            bildeingang_traegt=None,
                                            bildeingang_beleg="auf-probe")
    with pytest.raises(backbone.BackboneError, match="Auftragskennung"):
        backbone._eintrag(beleg_ohne_urteil)

    assert "probe-ohne-beleg" not in eigenes_register
    assert "probe-beleg-ohne-urteil" not in eigenes_register


# ======================================================================================
# 4 · Die Auskunft kommt vom Eintrag, nicht vom Namen
# ======================================================================================

def test_die_auskunft_kommt_vom_eintrag_nicht_vom_namen(eigenes_register):
    """Ein neuer Eintrag mit Messung wird gelesen, ohne dass ``kette.py`` ihn kennt.

    Synthetisch: Weder der Name noch die Kennung stehen für eine echte Messung.
    """
    vorlage = backbone.hole("flux2-klein-4b")
    backbone._eintrag(dataclasses.replace(
        vorlage, name="probe-traegt", bildeingang_traegt=True,
        bildeingang_beleg="auf-20260922-999", bildeingang_grund="Probeeintrag"))

    lage = kette.bildeingang_lage("probe-traegt")
    assert lage["traegt"] is True
    assert lage["beleg"] == "auf-20260922-999"
    assert lage["grund"] == "Probeeintrag"


# ======================================================================================
# 5 · Der Produktweg: der Nachrender im Graphen meldet das gemessene Urteil
# ======================================================================================

def _tabelle(modell) -> dict:
    """Attrappen für die teuren Stufen; Bildquelle und Nachrender sind ECHT."""
    def geometrie(*, knoten, eingaben, out_dir):
        glb = out_dir / "modell.glb"
        glb.write_text("glb", encoding="utf-8")
        return {"status": "ok", "glb_path": str(glb), "up_axis": "Y",
                "bbox": [[0.0, 0.0, 0.0], [8.0, 5.0, 3.0]]}

    def multipass(*, knoten, eingaben, out_dir):
        return {"status": "ok", "depth_png": str(_png(out_dir / "tiefe_norm.png"))}

    def rendern(*, knoten, eingaben, out_dir):
        return {"status": "ok", "bild_png": str(_png(out_dir / "bild.png", (9, 9, 9, 9)))}

    def qa(*, knoten, eingaben, out_dir):
        return {"status": "ok", "bestanden": True, "score": 0.9}

    return {ART_GEOMETRIE: geometrie, ART_MULTIPASS: multipass, ART_RENDER: rendern,
            ART_QA: qa, ART_BILDQUELLE: kette.AUSFUEHRER[ART_BILDQUELLE],
            ART_NACHRENDER: kette.nachrender_ausfuehrer(modell=modell)}


def test_der_nachrender_im_graphen_meldet_das_gemessene_urteil(tmp_path):
    """Der Weg, den das Produkt geht: Kette bauen, Nachrender anhängen, ``fuehre_aus``.

    Kein Backbone ausdrücklich gewählt — der Nachrender übernimmt den des Renders, und
    das ist der Vorgabe-Backbone. Seine Ausgaben tragen ``bildeingang_lage``; genau dort
    muss das gemessene «trägt nicht» stehen und nicht «nicht gemessen».
    """
    zeichnung = _png(tmp_path / "zeichnung.png", werte=(1, 1, 1, 1))
    (tmp_path / "m.glb").write_text("glb", encoding="utf-8")
    graph = haenge_nachrender_an(
        baue_kette(glb_path=str(tmp_path / "m.glb"), up_axis="Y", prompt="ein Haus",
                   qa=False),
        prompt="ein Balkon dazu", eingangsbild=str(zeichnung))

    lauf = fuehre_aus(graph, cache=ArtefaktCache(tmp_path / "cache"),
                      ausfuehrer=_tabelle(_Modell()), out_dir=tmp_path / "out")
    assert lauf["status"] == "ok", lauf["error"]

    nachrender = [kid for kid, k in graph.knoten.items() if k.art == ART_NACHRENDER]
    assert len(nachrender) == 1
    assert graph.knoten[nachrender[0]].params["backbone"] == render.VORGABE_BACKBONE

    ausgaben = lauf["knoten"][nachrender[0]]["ausgaben"]
    lage = ausgaben["bildeingang_lage"]
    assert lage["traegt"] is False, (
        "der Nachrender auf dem Vorgabe-Backbone meldete nicht das gemessene Urteil")
    assert BELEG_Z_IMAGE in lage["beleg"]


def test_ein_beleg_ohne_auftragskennung_wird_abgewiesen(eigenes_register):
    """Die Regel im Register prüft, was ihr Kommentar sagt: eine **Auftragskennung**.

    Bis zur Durchsicht vom 22.09.2026 prüfte sie nur, ob der Beleg leer ist — ein Beleg
    «irgendwas» ging durch, und das Urteil stand ohne Messung da.
    """
    with pytest.raises(backbone.BackboneError):
        backbone._eintrag(dataclasses.replace(
            backbone.BACKBONES["flux2-klein-4b"], name="probe-ohne-kennung",
            bildeingang_traegt=False, bildeingang_beleg="am Geraet gesehen",
            bildeingang_grund="Probeeintrag"))


def test_der_nachrender_sagt_zuvorderst_dass_die_skizze_nicht_ankam(tmp_path):
    """Owner-Entscheid 22.09.2026: auf dem Vorgabemodell weiter rechnen — mit Hinweis.

    Derselbe Weg wie oben (Kette, Nachrender, ``fuehre_aus``). Der Satz muss als ERSTER
    Hinweis stehen und den Beleg nennen; sonst sieht ein reiner Text-zu-Bild-Lauf aus wie
    eine Bearbeitung der Skizze. Gerechnet wird trotzdem: Status ok, ein Bild liegt da.
    """
    zeichnung = _png(tmp_path / "zeichnung.png", werte=(1, 1, 1, 1))
    (tmp_path / "m.glb").write_text("glb", encoding="utf-8")
    graph = haenge_nachrender_an(
        baue_kette(glb_path=str(tmp_path / "m.glb"), up_axis="Y", prompt="ein Haus",
                   qa=False),
        prompt="ein Balkon dazu", eingangsbild=str(zeichnung))

    lauf = fuehre_aus(graph, cache=ArtefaktCache(tmp_path / "cache"),
                      ausfuehrer=_tabelle(_Modell()), out_dir=tmp_path / "out")
    assert lauf["status"] == "ok", lauf["error"]

    nachrender = [kid for kid, k in graph.knoten.items() if k.art == ART_NACHRENDER][0]
    ausgaben = lauf["knoten"][nachrender]["ausgaben"]
    assert ausgaben.get("bild_png"), "weiter rechnen heisst: ein Bild entsteht"
    hinweise = list(ausgaben["hinweise"])
    assert hinweise and hinweise[0].startswith("SKIZZE NICHT ANGEKOMMEN"), hinweise
    assert BELEG_Z_IMAGE in hinweise[0]


def test_ein_ungemessener_bildeingang_behauptet_nicht_dass_die_skizze_fehlt(tmp_path):
    """Gegenprobe: ``traegt is None`` heisst ungemessen — nicht «kommt nicht an»."""
    zeichnung = _png(tmp_path / "zeichnung.png", werte=(1, 1, 1, 1))
    (tmp_path / "m.glb").write_text("glb", encoding="utf-8")
    graph = haenge_nachrender_an(
        baue_kette(glb_path=str(tmp_path / "m.glb"), up_axis="Y", prompt="ein Haus",
                   qa=False, backbone="flux2-klein-4b"),
        prompt="ein Balkon dazu", eingangsbild=str(zeichnung), backbone="flux2-klein-4b")

    lauf = fuehre_aus(graph, cache=ArtefaktCache(tmp_path / "cache"),
                      ausfuehrer=_tabelle(_Modell()), out_dir=tmp_path / "out")
    assert lauf["status"] == "ok", lauf["error"]
    nachrender = [kid for kid, k in graph.knoten.items() if k.art == ART_NACHRENDER][0]
    ausgaben = lauf["knoten"][nachrender].get("ausgaben") or {}
    assert ausgaben.get("bildeingang_lage", {}).get("traegt") is None, (
        "die Gegenprobe braucht einen UNGEMESSENEN Bildeingang")
    assert not any(str(h).startswith("SKIZZE NICHT ANGEKOMMEN")
                   for h in (ausgaben.get("hinweise") or ())), ausgaben.get("hinweise")
