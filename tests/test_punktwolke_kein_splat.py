"""Eine gewöhnliche Punktwolke als Splat-Kontext bricht den Auftrag nicht ab (Geräteprobe R59).

**Befund (Geräteprobe R59, Heim-PC):** Eine Punktwolke (.ply, ohne 3DGS-Felder) war im Projekt
geladen, ging als Splat-Kontext in die Render-Bestellung mit, und die Blender-Stufe brach den
ganzen Auftrag ab: «… ist kein 3DGS-Splat: Es fehlen f_dc_*, opacity, scale_*». Erst nach
«Aus dem Projekt entfernen» lief der Render.

**Jetzt:** Sie wird weggelassen — mit einem Satz in den Warnungen und in
``qa.verdict.hinweise`` —, und der Render läuft ohne sie weiter. Gelesen wird nur der PLY-Kopf.
Alle Dateien hier sind synthetisch (Regel 3).
"""

from __future__ import annotations

import importlib.util
import re
from pathlib import Path

import pytest
from conftest import MINI_PNG

from aiimaging import abholer, kette, kontext_netz, kosmo_szene, seams
from aiimaging.graph import Knoten

WURZEL = Path(__file__).resolve().parents[1]


def _werkzeug(name: str):
    spez = importlib.util.spec_from_file_location(f"{name}_pw", WURZEL / "tools" / f"{name}.py")
    modul = importlib.util.module_from_spec(spez)
    spez.loader.exec_module(modul)
    return modul


def _punktwolke(pfad: Path, n: int = 5) -> Path:
    """Eine kleine Punktwolke, wie sie ein Laserscanner oder eine Fotogrammetrie liefert:
    Lage und Farbe je Punkt — keine Deckkraft, keine Skala, keine SH-Farbe."""
    pfad.parent.mkdir(parents=True, exist_ok=True)
    zeilen = ["ply", "format ascii 1.0", "comment synthetisch", f"element vertex {n}",
              "property float x", "property float y", "property float z",
              "property uchar red", "property uchar green", "property uchar blue",
              "end_header"]
    zeilen += [f"{i * 0.5} {i * 0.25} 0.0 200 180 160" for i in range(n)]
    pfad.write_text("\n".join(zeilen) + "\n", encoding="ascii")
    return pfad


def _splat(pfad: Path) -> Path:
    _werkzeug("make_test_splat").erzeuge_splat(pfad, punkte=200)
    return pfad


def _context(ply: Path) -> dict:
    return {"kind": "splat", "ply": str(ply), "transform": [1, 0, 0, 0, 0, 1, 0, 0,
                                                            0, 0, 1, 0, 0, 0, 0, 1],
            "fit": "behelf", "crs_note": "Lokales System des Modells."}


# ======================================================================================
# 1 · Der Kopf sagt, was die Datei ist
# ======================================================================================

def test_kopf_erkennt_punktwolke_splat_und_netz(tmp_path):
    wolke = _punktwolke(tmp_path / "wolke.ply")
    assert kontext_netz.fehlende_splat_felder(wolke) == list(kontext_netz.SPLAT_FELDER)
    assert kontext_netz.fehlende_splat_felder(_splat(tmp_path / "splat.ply")) == []
    netz = tmp_path / "netz.ply"
    kontext_netz.schreibe_netz_ply(netz, [(0, 0, 0), (1, 0, 0), (0, 1, 0)],
                                   [(255, 0, 0)] * 3, [(0, 1, 2)])
    assert kontext_netz.fehlende_splat_felder(netz) is None
    # Nicht sicher lesbar → keine Aussage; dann bleibt alles wie bisher.
    kaputt = tmp_path / "kaputt.ply"
    kaputt.write_bytes(b"ply")
    assert kontext_netz.fehlende_splat_felder(kaputt) is None


def test_die_felder_sind_die_der_blender_stufe():
    """Eine mildere Regel hier liesse eine Datei durch, an der Blender dann doch abbricht."""
    quelle = seams.BLENDER_RUNNER.read_text(encoding="utf-8")
    treffer = re.search(r"^KONTEXT_SPALTEN = \(([^)]*)\)", quelle, re.M)
    assert treffer, "KONTEXT_SPALTEN nicht gefunden"
    spalten = tuple(re.findall(r'"([^"]+)"', treffer.group(1)))
    assert spalten == kontext_netz.SPLAT_FELDER


def test_der_satz_nennt_datei_und_felder_ohne_pfad(tmp_path):
    satz = kontext_netz.satz_punktwolke_weggelassen("wolke.ply", list(kontext_netz.SPLAT_FELDER))
    assert satz.startswith("PUNKTWOLKE OHNE SPLAT-FELDER — als Kontext weggelassen: 'wolke.ply'")
    assert "f_dc_*, opacity, scale_*" in satz


# ======================================================================================
# 2 · Der Produktweg: lies_szene nimmt sie heraus
# ======================================================================================

GRUND = {"geometry": {"path": "model.glb", "format": "glb"}, "cameras": "auto",
         "style": {"prompt": "house"}, "render": {}, "vis": {}}


def test_lies_szene_laesst_die_punktwolke_weg_und_sagt_es(tmp_path):
    wolke = _punktwolke(tmp_path / "home" / "nutzer" / "bestand.ply")
    szene = kosmo_szene.lies_szene(dict(GRUND, context=_context(wolke)))
    assert szene["kontext"] is None
    assert not szene["maengel"], szene["maengel"]
    weg = szene["kontext_weggelassen"]
    assert weg["datei"] == "bestand.ply" and "opacity" in weg["fehlende_felder"]
    assert any(w.startswith(kontext_netz.SATZ_PUNKTWOLKE_WEGGELASSEN)
               for w in szene["warnungen"])
    assert "nutzer" not in weg["satz"]


def test_auch_eine_falsche_lage_haelt_eine_weggelassene_wolke_nicht_an(tmp_path):
    wolke = _punktwolke(tmp_path / "bestand.ply")
    szene = kosmo_szene.lies_szene(dict(GRUND, context=dict(_context(wolke),
                                                            transform=[1, 2, 3])))
    assert szene["kontext"] is None and not szene["maengel"]


def test_ein_echter_splat_bleibt_wie_er_war(tmp_path):
    splat = _splat(tmp_path / "umgebung.ply")
    szene = kosmo_szene.lies_szene(dict(GRUND, context=_context(splat)))
    assert szene["kontext"]["datei"] == "umgebung.ply"
    assert szene["kontext_weggelassen"] is None
    assert not any(w.startswith(kontext_netz.SATZ_PUNKTWOLKE_WEGGELASSEN)
                   for w in szene["warnungen"])


# ======================================================================================
# 3 · Der Abholer: der Render läuft ohne sie weiter (gegen alt rot)
# ======================================================================================

def _verarbeite(tmp_path, kontext):
    gesehen = {"multipass": [], "vorbereitet": []}

    def multipass(glb, aus, **kw):
        gesehen["multipass"].append(kw)
        ply = kw.get("kontext_ply")
        fehlend = kontext_netz.fehlende_splat_felder(ply) if ply else None
        if fehlend:
            # Was die Blender-Stufe an dieser Stelle tut (blender_depth_stage, R59).
            raise RuntimeError(f"{Path(ply).name!r} ist kein 3DGS-Splat: Es fehlen {fehlend}.")
        tiefe = Path(aus) / "tiefe_norm.png"
        tiefe.parent.mkdir(parents=True, exist_ok=True)
        tiefe.write_bytes(MINI_PNG)
        (Path(aus) / "beauty.png").write_bytes(MINI_PNG)
        return {"depth_png": str(tiefe), "beauty_png": str(Path(aus) / "beauty.png"),
                "kamera": {"weg": "vorgegeben"}}

    def rendere(auftrag, **kw):
        bild = Path(tmp_path) / "b.png"
        bild.write_bytes(MINI_PNG)
        return {"status": "ok", "bild_png": str(bild), "hinweise": ()}

    def vorbereiten(ply, **kw):
        gesehen["vorbereitet"].append(ply)
        return {"ply": str(ply), "weg": "kugeln", "netz": None, "grund": None,
                "hinweis": kontext_netz.SATZ_KUGELN_NICHT_EINGERICHTET}

    verarbeite = abholer.verarbeiter(
        out_wurzel=tmp_path / "aus", nullprobe=False, _multipass=multipass, _rendere=rendere,
        _kontext_vorbereiten=vorbereiten,
        _qa=lambda *a, **k: {"score": 0.9, "bestanden": True},
        _soll=lambda *a, **k: ([[0.0]], 1, 1))
    glb = tmp_path / "m.glb"
    glb.write_bytes(_werkzeug("make_test_glb").baue_glb(
        [("Halle", (-5.0, 0.0, -5.0), (5.0, 3.0, 5.0))]))
    ergebnis = verarbeite({"modell": glb, "job_id": "vis-1-aaaaaa", "verzeichnis": tmp_path,
                           "szene": {"kameras": [{"kuerzel": "s", "richtung": "s"}],
                                     "aufloesung": 64, "hoehe": 64, "samples": 1,
                                     "prompt": "a house", "kontext": kontext}})
    return ergebnis, gesehen


def test_abholer_rechnet_ohne_punktwolke_weiter_und_sagt_es(tmp_path):
    wolke = _punktwolke(tmp_path / "home" / "nutzer" / "bestand.ply")
    kontext = kosmo_szene.kontext_aus_szene(_context(wolke))
    ergebnis, gesehen = _verarbeite(tmp_path, kontext)
    assert ergebnis["bilder"], ergebnis.get("grund")
    assert all("kontext_ply" not in kw for kw in gesehen["multipass"])
    assert gesehen["vorbereitet"] == [], "die Wolke geht nicht in die Splat-Brücke"
    weg = ergebnis["angewandt"]["kontext_weggelassen"]
    assert weg["datei"] == "bestand.ply"
    vertrag = kosmo_szene.als_ergebnis("vis-1-aaaaaa", [], geometrie_urteil={"score": 0.9,
                                                                              "bestanden": True},
                                       angewandt=ergebnis["angewandt"])
    hinweise = vertrag["qa"]["verdict"].get("hinweise") or []
    assert any(h.startswith(kontext_netz.SATZ_PUNKTWOLKE_WEGGELASSEN) for h in hinweise)
    assert "nutzer" not in str(vertrag)


def test_abholer_mit_echtem_splat_unveraendert(tmp_path):
    splat = _splat(tmp_path / "umgebung.ply")
    kontext = kosmo_szene.kontext_aus_szene(_context(splat))
    ergebnis, gesehen = _verarbeite(tmp_path, kontext)
    assert gesehen["vorbereitet"] == [str(splat)]
    assert all(kw.get("kontext_ply") == str(splat) for kw in gesehen["multipass"])
    assert "kontext_weggelassen" not in (ergebnis["angewandt"] or {})


# ======================================================================================
# 4 · Der Kettenknoten (Knotenansicht von Hand)
# ======================================================================================

def test_kettenknoten_laesst_die_punktwolke_weg(tmp_path, monkeypatch):
    gesehen = {}

    def attrappe(glb, out, **kw):
        gesehen.update(kw)
        return {"status": "ok", "error": "Attrappe"}

    monkeypatch.setattr(seams, "glb_zu_multipass", attrappe)
    monkeypatch.setattr(seams, "kontext_vorbereiten",
                        lambda *a, **k: pytest.fail("Wolke ging in die Brücke"))
    wolke = _punktwolke(tmp_path / "bestand.ply")
    knoten = Knoten(id="multipass", art=kette.ART_MULTIPASS,
                    params={"aufloesung": 32, "samples": 1, "beauty": True,
                            "material_id": True, "kontext_ply": str(wolke),
                            "kontext_matrix": [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]})
    bericht = kette._fuehre_multipass(knoten=knoten,
                                      eingaben=[{"glb_path": "m.glb", "up_axis": "Y"}],
                                      out_dir=tmp_path)
    assert "kontext_ply" not in gesehen and "kontext_matrix" not in gesehen
    weg = bericht["kontext_weg"]
    assert weg["weg"] == "weggelassen"
    assert weg["hinweis"].startswith(kontext_netz.SATZ_PUNKTWOLKE_WEGGELASSEN)
