"""Die Geometrieprüfung läuft **vor** dem Bildlauf — Owner-Einwand vom 25.08.2026.

**Der Anlass ist ein Satz des Owners**, nachdem er das erste Bild aus einem vollständigen
Kettenlauf gesehen hatte (`auftraege/von-homestation/auf-vis-20260825-15.md`, Posten 1):

  *«Das sollte natuerlich gar nicht so weit kommen — die Modelle muessen pruefen, ob die
  Geometrie richtig ist und richtig darstellt, BEVOR AI Imaging startet.»*

Die Kette prüfte bis dahin **danach**. Ein Auftrag, bei dem das Bauwerk 17,5 % der
Bildbreite füllte, lief bis in die Diffusion — und das Bildmodell erfand eine
Fassadendetail-Aufnahme, weil ihm die Vorlage fehlte.

**Und die Lösung war gebaut und ungenutzt.** ``kameras.rahmungsverhaeltnis`` und
``bbox_bauwerk`` hatten ausser Tests keinen einzigen Aufrufer. Die sechste tote Kante
dieser Woche — und die einzige, die von aussen wie eine gelöste Aufgabe aussah.

**Zur Bauart dieser Datei.** Die entscheidenden Prüfungen kommen paarweise: Ein Test, der
zeigt, dass NICHT gerendert wird, ist ohne seine Gegenprobe wertlos — eine Erkennung, die
immer greift, ist keine. Dasselbe gilt für die drei Wege, auf denen **nicht** abgebrochen
wird (vorgegebene Kamera, fehlende Bauwerksbox, ausreichende Rahmung): Ohne sie wäre der
Umbau eine stille Abschaltung der Kette.
"""
import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from aiimaging import abholer, kameras


# ======================================================================================
# Die Zahl und ihre Herkunft
# ======================================================================================

def test_die_abbruchschwelle_ist_die_gemessene_stuetzstelle():
    """0,65 ist keine gerundete Meinung, sondern die kleinste gemessene Bildbreite, bei
    der überhaupt etwas bestand (0.637)."""
    assert kameras.BILDBREITE_ABBRUCH == 0.65


def test_die_beiden_bildbreiten_zahlen_sind_verschiedene_zahlen():
    """Knie und Abbruch beantworten verschiedene Fragen. Fielen sie zusammen, wäre eine
    von beiden überflüssig — und der Widerspruch zwischen den zwei Messungen wäre still
    verschwunden."""
    assert kameras.BILDBREITE_KNIE < kameras.BILDBREITE_ABBRUCH


def test_die_herkunft_der_zahl_steht_im_quelltext_und_nennt_den_nicht_monotonen_punkt():
    """Der Kern der Messung ist, dass 30 % **schlechter** ausgeht als 17,5 %. Wer das
    nicht mitliest, interpoliert zwischen den Stützstellen und erfindet dabei eine Rampe,
    die es nicht gibt."""
    quelle = Path(kameras.__file__).read_text(encoding="utf-8")
    block = quelle.split("BILDBREITE_ABBRUCH = ")[0]
    block = block[block.rindex("#: Bildbreite, **unter der nicht mehr gerendert wird**"):]

    assert "auf-vis-20260825-15" in block, "die Quelle der Messung"
    assert "0.0002" in block and "0.932" in block, "die Stuetzstellen"
    assert "nicht monoton" in block, "der Grund, nicht zu interpolieren"


# ======================================================================================
# Die Rechnung
# ======================================================================================

def test_zu_weite_rahmung_meldet_abbruch():
    """Der gemessene Fall: ein Quader auf einer grossen Platte."""
    lage = kameras.rahmungsverhaeltnis([[0, 0, 0], [40, 40, 10]], [[0, 0, 0], [8, 5, 7]])

    assert lage["abbruch"] is True
    assert lage["traegt"] is False
    assert "NICHT RENDERN" in lage["abbruch_grund"]


def test_ausreichende_rahmung_meldet_keinen_abbruch():
    """Die Gegenprobe. Ohne sie prüfte die Datei nur, dass ein Wert immer True ist."""
    lage = kameras.rahmungsverhaeltnis([[0, 0, 0], [8, 5, 10]], [[0, 0, 0], [8, 5, 7]])

    assert lage["abbruch"] is False
    assert lage["traegt"] is True
    assert lage["abbruch_grund"] == ""


def test_fehlende_bauwerksbox_bricht_nichts_ab():
    """NICHT FESTSTELLBAR ist weder bestanden noch durchgefallen — und ganz sicher kein
    Grund, jede Aufnahme von vor dem 25.08.2026 abzubrechen."""
    lage = kameras.rahmungsverhaeltnis([[0, 0, 0], [40, 40, 10]], None)

    assert lage["abbruch"] is None
    assert lage["traegt"] is None


def test_das_uneinige_band_wird_benannt_und_nicht_geglaettet():
    """Zwischen Knie (0,5991) und Abbruch (0,65) sagt die eine Messung «besteht» und die
    andere «0.001». Der Code entscheidet sich für die vorsichtige Zahl — und **sagt es**,
    statt den Widerspruch in einer Zwischenzahl verschwinden zu lassen."""
    # 8/9 der Szenenbreite bei Deckungsgrad 0.70 → 0.622, genau im Band.
    lage = kameras.rahmungsverhaeltnis([[0, 0, 0], [9, 9, 10]], [[0, 0, 0], [8, 5, 7]])

    assert kameras.BILDBREITE_KNIE <= lage["wirksame_bildbreite"] < kameras.BILDBREITE_ABBRUCH
    assert lage["traegt"] is True and lage["abbruch"] is True
    assert "uneinig" in lage["abbruch_grund"]


# ======================================================================================
# Die Naht — und hier entscheidet sich, ob der Umbau etwas bewirkt
# ======================================================================================

def _lauf(tmp_path, *, bbox, bbox_bauwerk, weg="abgeleitet"):
    """Ein Auftrag durch `verarbeiter` mit Attrappen. Gibt (ergebnis, renderzaehler)."""
    zaehler = {"render": 0}
    bild = tmp_path / "b.png"

    def multipass(glb, aus, **kw):
        tiefe = Path(aus) / "tiefe_norm.png"
        tiefe.write_bytes(b"\x89PNG\r\n\x1a\n")
        return {"depth_png": str(tiefe), "kamera": {"weg": weg},
                "bbox": bbox, "bbox_bauwerk": bbox_bauwerk}

    def rendere(auftrag, **kw):
        zaehler["render"] += 1
        bild.write_bytes(b"\x89PNG\r\n\x1a\n")
        return {"status": "ok", "bild_png": str(bild), "hinweise": ()}

    verarbeite = abholer.verarbeiter(
        out_wurzel=tmp_path, nullprobe=False,
        _multipass=multipass, _rendere=rendere,
        _qa=lambda *a, **k: {"score": 0.9, "bestanden": True},
        _soll=lambda *a, **k: ([[0.0]], 1, 1))

    ergebnis = verarbeite({"modell": tmp_path / "m.glb", "job_id": "vis-1-aaaaaa",
                           "verzeichnis": tmp_path,
                           "szene": {"kameras": [{"kuerzel": "sSE", "richtung": "sSE"}],
                                     "aufloesung": 64, "hoehe": 64,
                                     "samples": 1, "prompt": "a house"}})
    return ergebnis, zaehler["render"]


def test_bei_zu_weiter_rahmung_wird_gar_nicht_erst_gerendert(tmp_path):
    """Der Kern des Owner-Einwands. Kein Render, kein Bild, und das Urteil sagt warum."""
    ergebnis, n_render = _lauf(tmp_path, bbox=[[0, 0, 0], [40, 40, 10]],
                               bbox_bauwerk=[[0, 0, 0], [8, 5, 7]])

    assert n_render == 0, "die Diffusion darf hier gar nicht anlaufen"
    assert ergebnis["bilder"] == []
    urteil = ergebnis["kameras"][0]
    assert urteil["rahmung"]["abbruch"] is True
    assert urteil["score"] is None and urteil["gemessen"] is False


def test_bei_ausreichender_rahmung_laeuft_der_render(tmp_path):
    """Die Gegenprobe, und ohne sie ist die Datei wertlos: Eine Erkennung, die immer
    greift, hätte die Kette stillgelegt und alle Tests darüber grün gelassen."""
    # Ein Gelaendestreifen ringsum, aber ein schmaler: 8 von 8,5 m Szenenbreite sind
    # Bauwerk, bei Deckungsgrad 0,70 also 65,9 % der Bildbreite.
    ergebnis, n_render = _lauf(tmp_path, bbox=[[0, 0, 0], [8.5, 5.5, 10]],
                               bbox_bauwerk=[[0, 0, 0], [8, 5, 7]])

    assert n_render == 1
    assert len(ergebnis["bilder"]) == 1
    assert ergebnis["kameras"][0]["rahmung"]["abbruch"] is False


def test_ohne_bauwerksbox_laeuft_der_render_wie_bisher(tmp_path):
    """Jede Aufnahme vor dem 25.08.2026 hat keine. Sie alle abzubrechen wäre ein
    Rückschritt, getarnt als Sorgfalt."""
    ergebnis, n_render = _lauf(tmp_path, bbox=[[0, 0, 0], [40, 40, 10]],
                               bbox_bauwerk=None)

    assert n_render == 1
    assert ergebnis["kameras"][0]["rahmung"]["abbruch"] is None


def test_eine_vorgegebene_kamera_wird_nicht_nach_dem_deckungsgrad_abgebrochen(tmp_path):
    """Die Rechnung geht von :data:`kameras.DECKUNGSGRAD` aus, und der beschreibt nur den
    abgeleiteten Weg. Wer Standort und Blickziel als Zahlen hereingibt, hat selbst
    gerahmt — ihn mit einer Zahl abzubrechen, die auf ihn nicht zutrifft, wäre schlimmer
    als gar keine Pruefung."""
    ergebnis, n_render = _lauf(tmp_path, bbox=[[0, 0, 0], [40, 40, 10]],
                               bbox_bauwerk=[[0, 0, 0], [8, 5, 7]], weg="vorgegeben")

    assert n_render == 1
    lage = ergebnis["kameras"][0]["rahmung"]
    assert lage["abbruch"] is None
    assert "vorgegeben" in lage["abbruch_grund"]
    assert lage["wirksame_bildbreite"] is not None, (
        "die Zahl steht trotzdem da — als Auskunft, nicht als Urteil")


def test_ein_uebersprungener_lauf_zaehlt_nicht_als_gemessen(tmp_path):
    """Sonst wäre der Abbruch eine stille Verbesserung: Wer nicht antritt, kann nicht
    durchfallen — und das Minimum über die Kameras stiege."""
    ergebnis, _ = _lauf(tmp_path, bbox=[[0, 0, 0], [40, 40, 10]],
                        bbox_bauwerk=[[0, 0, 0], [8, 5, 7]])

    spanne = ergebnis["geometrie_urteil"]["kameraspanne"]
    assert spanne["n"] == 1 and spanne["n_gemessen"] == 0
    assert "UNGEPRUEFT" in spanne["hinweis"]
    assert ergebnis["geometrie_urteil"]["score"] is None


def test_der_kurzbefund_nennt_den_nicht_gelaufenen_render():
    """Ein Abbruch, den niemand sieht, ist von einem verschwundenen Bild nicht zu
    unterscheiden."""
    zeilen = abholer.befund_kurz({"kameras": [
        {"kamera": "sSE", "rahmung": {"abbruch": True}}]})

    treffer = [z for z in zeilen if "NICHT GERENDERT" in z]
    assert len(treffer) == 1
    assert "sSE" in treffer[0] and "65" in treffer[0]


def test_ohne_abbruch_steht_die_zeile_nicht_da():
    """Eine Zeile, die immer dasteht, liest sich nach dem dritten Mal wie eine leere."""
    zeilen = abholer.befund_kurz({"kameras": [
        {"kamera": "sSE", "rahmung": {"abbruch": False}}]})

    assert not [z for z in zeilen if "NICHT GERENDERT" in z]


# ======================================================================================
# Die zweite Hüllbox im Blender-Bericht
# ======================================================================================

RUNNER = (Path(__file__).resolve().parents[1]
          / "src" / "aiimaging" / "runners" / "blender_depth_stage.py")


class _Vektor(list):
    """Gerade so viel `mathutils.Vector`, wie `_bbox_bauwerk` anfasst: Indizierung."""


class _Einheit:
    """Eine Weltmatrix, die nichts tut. Die Prüfung gilt der Auswahl, nicht der Algebra."""

    def __matmul__(self, vektor):
        return vektor


def _runner_mit_objekten(monkeypatch, objekte):
    """Den Blender-Runner als Datei laden — mit gefälschtem `bpy`.

    **Nicht** als `aiimaging.runners.blender_depth_stage` importiert: Das wäre der Anfang
    genau des Weges, den `tests/test_prozessgrenze.py` verbietet (Regel 2). Der Ladeweg
    über den Dateipfad hält die Prozessgrenze ein, und die Attrappen stehen nur in
    ``sys.modules`` dieses Tests.
    """
    mathutils = SimpleNamespace(Vector=_Vektor)
    bpy = SimpleNamespace(data=SimpleNamespace(objects=objekte))
    monkeypatch.setitem(sys.modules, "bpy", bpy)
    monkeypatch.setitem(sys.modules, "mathutils", mathutils)

    spez = importlib.util.spec_from_file_location("blender_pruefling", RUNNER)
    modul = importlib.util.module_from_spec(spez)
    spez.loader.exec_module(modul)
    return modul


def _mesh(name, lo, hi):
    ecken = [(x, y, z) for x in (lo[0], hi[0]) for y in (lo[1], hi[1])
             for z in (lo[2], hi[2])]
    return SimpleNamespace(name=name, type="MESH", bound_box=ecken,
                           matrix_world=_Einheit())


def test_die_bauwerksbox_laesst_das_gelaende_weg(monkeypatch):
    """Der ganze Zweck: die Box dessen, was gezeigt werden soll — nicht die von allem,
    was dasteht."""
    modul = _runner_mit_objekten(monkeypatch, [
        _mesh("Gelaende_Hang", (-20, -20, -0.2), (20, 20, 0.0)),
        _mesh("Wand_Nord", (0, 0, 0), (8, 5, 7)),
    ])

    lo, hi, note = modul._bbox_bauwerk()

    assert lo == [0, 0, 0] and hi == [8, 5, 7]
    assert note == ""


def test_ohne_gebaute_substanz_gibt_es_keine_bauwerksbox_und_keinen_rueckfall(monkeypatch):
    """**Der wichtigste Test dieser Gruppe.** Die Szenenbox stillschweigend als
    Bauwerksbox auszugeben deckte den Bruch genau dort zu, wo er gemessen werden soll —
    und der Bericht sähe dann gesund aus."""
    modul = _runner_mit_objekten(monkeypatch, [
        _mesh("Gelaende_Hang", (-20, -20, -0.2), (20, 20, 0.0)),
    ])

    lo, hi, note = modul._bbox_bauwerk()

    assert lo is None and hi is None
    assert "NICHT auf die Szenenbox" in note


def test_ein_unerreichbares_maske_modul_ist_kein_fehlendes_gelaende(monkeypatch):
    """Die dritte Antwort an der Prozessgrenze: Wenn die Regel nicht angewendet werden
    KONNTE, heisst das nicht, dass sie nicht griff."""
    modul = _runner_mit_objekten(monkeypatch, [_mesh("Wand", (0, 0, 0), (8, 5, 7))])
    monkeypatch.setattr(modul, "_maske_modul", lambda: None)

    lo, hi, note = modul._bbox_bauwerk()

    assert lo is None and hi is None
    assert "nicht erreichbar" in note


def test_der_bericht_traegt_die_zweite_huellbox(monkeypatch):
    """Ohne dieses Feld im Bericht bliebe die ganze Prüfung diesseits der Prozessgrenze
    blind — und `rahmungsverhaeltnis` wieder eine tote Kante."""
    quelle = RUNNER.read_text(encoding="utf-8")
    kopf = quelle.split("report = {", 1)[1].split("\n    }", 1)[0]

    assert '"bbox_bauwerk"' in kopf
    assert '"bbox_bauwerk_note"' in kopf


def test_die_gelaenderegel_wird_nicht_zweimal_hingeschrieben(monkeypatch):
    """Eine zweite Wortliste an der Aussenkante liefe bei der nächsten Schärfung still
    auseinander — genau der Fehler, gegen den `_vorgabe` gebaut ist."""
    from aiimaging import maske

    quelle = RUNNER.read_text(encoding="utf-8")
    for wort in maske.GELAENDE_WOERTER:
        assert f'"{wort}"' not in quelle, (
            f"{wort!r} steht im Runner — die Regel gehoert in aiimaging.maske")
