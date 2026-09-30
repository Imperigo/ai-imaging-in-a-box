"""Kandidaten für die Formprüfung — die Nullproben zuerst (Sitzung 73 §17).

Jeder Kandidat muss vor der Messung an der HomeStation zwei Dinge können: einer grauen Fläche
nichts geben und Rauschen nicht belohnen. Die «Ordnung an Tiefensprüngen» gab einer grauen
Fläche die Bestnote (auf-172); die Umrisstreue belohnte kantenreiche Fälschungen (auf-186) —
darum hier zusätzlich eine **Textur**, die viele Kanten hat, aber in alle Richtungen.
"""
from __future__ import annotations

import math
import random

from aiimaging import formkandidaten as fk

B, H = 64, 48
HG = 1.0e10


def _im_bau(x, y):
    return 20 <= x < 44 and 12 <= y < 36


def _soll():
    # Zwei Wände verschiedener Tiefe, damit es eine innere Stufe gibt.
    return [(10.0 if x < 32 else 11.0) if _im_bau(x, y) else HG
            for y in range(H) for x in range(B)]


def _flaechen():
    return [(1 if x < 32 else 2) if _im_bau(x, y) else 0
            for y in range(H) for x in range(B)]


def _passend():
    return [(0.8 if x < 32 else 0.6) if _im_bau(x, y) else 0.2
            for y in range(H) for x in range(B)]


def _textur():
    """Viele Kanten in allen Richtungen, ohne Bezug zum Bau — die «Holzfassade»."""
    rnd = random.Random(3)
    return [0.5 + 0.4 * math.sin(0.9 * x + 1.7 * y + rnd.random()) for y in range(H)
            for x in range(B)]


def test_das_passende_bild_hebt_sich_in_allen_kandidaten_ab():
    aus = fk.alle(_passend(), _soll(), B, H, flaechen=_flaechen())
    assert aus["urteilt"] is False
    assert aus["richtung_abhebung"] > 1.4
    assert aus["flaechentrennung"] > 0.9
    assert aus["silhouette_abhebung"] > 3


def test_die_graue_flaeche_bekommt_ueberall_null():
    aus = fk.alle([0.5] * (B * H), _soll(), B, H, flaechen=_flaechen())
    assert aus["richtung"] == 0.0 and aus["flaechentrennung"] == 0.0
    assert aus["umriss_abhebung"] == 0.0 and aus["silhouette_abhebung"] == 0.0


def test_rauschen_ist_zufall():
    rnd = random.Random(7)
    aus = fk.alle([rnd.random() for _ in range(B * H)], _soll(), B, H, flaechen=_flaechen())
    assert 0.75 < aus["richtung_abhebung"] < 1.25, aus
    assert aus["flaechentrennung"] < 0.05, aus


def test_eine_textur_ohne_bezug_wird_nicht_belohnt():
    aus = fk.alle(_textur(), _soll(), B, H, flaechen=_flaechen())
    passend = fk.alle(_passend(), _soll(), B, H, flaechen=_flaechen())
    assert aus["flaechentrennung"] < 0.1
    assert aus["richtung_abhebung"] < passend["richtung_abhebung"]


def test_flaechen_aus_farben_schwarz_ist_null():
    assert fk.flaechen_aus_farben([(0, 0, 0), (10, 20, 30), (10, 20, 30), (1, 2, 3)]) \
        == [0, 1, 1, 2]


# ======================================================================================
# Der Weg über den Blender-Bericht und die Auswertung
# ======================================================================================

def test_aus_dem_bericht_mit_flaechen(monkeypatch):
    from aiimaging import bildlesen
    farben = [((200, 0, 0) if f == 1 else (0, 200, 0) if f == 2 else (0, 0, 0))
              for f in _flaechen()]
    monkeypatch.setattr(bildlesen, "tiefen_aus_report", lambda r: (_soll(), B, H))
    monkeypatch.setattr(bildlesen, "lies_png_luminanz", lambda p: (_passend(), B, H))
    monkeypatch.setattr(bildlesen, "lies_png_farben", lambda p: (farben, B, H))
    aus = fk.alle_aus_bericht("bild.png", {"material_id_png": "mid.png"})
    assert aus["status"] == "ok" and aus["flaechentrennung"] > 0.9


def test_eine_andere_bildgroesse_ist_ein_befund(monkeypatch):
    from aiimaging import bildlesen
    monkeypatch.setattr(bildlesen, "tiefen_aus_report", lambda r: (_soll(), B, H))
    monkeypatch.setattr(bildlesen, "lies_png_luminanz", lambda p: ([0.5] * 4, 2, 2))
    aus = fk.alle_aus_bericht("bild.png", {})
    assert aus["status"] == "groesse_passt_nicht" and aus["urteilt"] is False


def _auswertung():
    import importlib.util
    from pathlib import Path
    pfad = Path(__file__).resolve().parents[1] / "tools" / "formpruefung_auswertung.py"
    spec = importlib.util.spec_from_file_location("formpruefung_auswertung", pfad)
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul


def test_die_auswertung_trennt_fall_und_bild(tmp_path):
    """Eine Zahl, die nur den Fall kennt (Blick), hat über alles eine hohe AUC, im Fall 0,5."""
    import json
    aw = _auswertung()
    bilder = []
    for blick, gut in (("s", 0.2), ("sSE", 0.8)):
        for sw, etikett in enumerate(["steht", "steht nicht", "steht", "unklar"]):
            if blick == "s" and etikett == "steht":
                etikett = "steht nicht" if sw == 0 else "steht"
            bilder.append({"koerper": "hochbau", "blick": blick, "startwert": sw,
                           "blind_id": f"B{blick}{sw}",
                           "rahmung": "bauwerk", "augenetikett": etikett,
                           "nur_fall": gut, "folgt_auge": 1.0 if etikett == "steht" else 0.0})
    datei = tmp_path / "e.json"
    datei.write_text(json.dumps({"auftrag_id": "auf-x", "bilder": bilder, "kreuzpaare": [
        {"bild": "BsSE0", "eigen": True, "folgt_auge": 0.9},
        {"bild": "BsSE0", "eigen": False, "folgt_auge": 0.1},
        # ein Bild ohne Form zählt nicht mit, auch wenn die fremde Soll-Karte gewinnt
        {"bild": "BsSE1", "eigen": True, "folgt_auge": 0.1},
        {"bild": "BsSE1", "eigen": False, "folgt_auge": 0.9}]}))
    erg = aw.auswerten(aw.zeilen_aus([datei]), kreuzpaare=aw.kreuzpaare_aus([datei]))
    assert erg["masse"]["folgt_auge"]["auc"] == 1.0
    assert erg["masse"]["folgt_auge"]["auc_im_fall"] == 1.0
    assert erg["masse"]["folgt_auge"]["kreuz"] == 1.0
    assert erg["masse"]["nur_fall"]["auc_im_fall"] == 0.5
    assert erg["augen"]["hochbau"] == {"steht": 3, "steht_nicht": 3, "unklar": 2}


def test_ein_unbekanntes_augenwort_ist_ein_fehler():
    import pytest
    with pytest.raises(ValueError):
        _auswertung().auge("vielleicht")


def _werkzeug(name):
    import importlib.util
    from pathlib import Path
    pfad = Path(__file__).resolve().parents[1] / "tools" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, pfad)
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul


def test_das_messwerkzeug_schreibt_eigen_und_fremd_ohne_pfade(tmp_path, monkeypatch, capsys):
    import json
    werkzeug = _werkzeug("formkandidaten_messen")
    for ordner in ("hochbau-s", "hochbau-sSE"):
        (tmp_path / ordner).mkdir()
        (tmp_path / ordner / "blender-report.json").write_text("{}")
    monkeypatch.setattr(fk, "alle_aus_bericht", lambda bild, bericht: {"status": "ok",
                                                                        "richtung": 0.9})
    assert werkzeug.main(["--bild", "b.png",
                          "--bericht", str(tmp_path / "hochbau-s" / "blender-report.json"),
                          "--fremd", str(tmp_path / "hochbau-sSE" / "blender-report.json"),
                          "--bild-id", "190-B14"]) == 0
    zeilen = [json.loads(z) for z in capsys.readouterr().out.splitlines()]
    assert [(z["bild"], z["eigen"], z["soll_von"]) for z in zeilen] == [
        ("190-B14", True, "hochbau-s"), ("190-B14", False, "hochbau-sSE")]
    assert str(tmp_path) not in json.dumps(zeilen), "Regel 3: kein Pfad in der Ausgabe"


def test_die_auswertung_filtert_nach_rahmung(tmp_path, capsys):
    import json
    datei = tmp_path / "e.json"
    datei.write_text(json.dumps({"auftrag_id": "auf-x", "bilder": [
        {"koerper": "hochbau", "blick": "s", "rahmung": r, "augenetikett": e, "z": v}
        for r, e, v in (("bauwerk", "steht", 1.0), ("bauwerk", "steht nicht", 0.0),
                        ("szene", "steht nicht", 0.5))]}))
    aw = _werkzeug("formpruefung_auswertung")
    assert aw.main(["--rahmung", "bauwerk", "--json", str(datei)]) == 0
    erg = json.loads(capsys.readouterr().out)
    assert erg["n_bilder"] == 2 and erg["masse"]["z"]["auc"] == 1.0


def test_kreuzprobe_je_art_und_ihre_decke():
    """194: Gegen Nachbarblicke verlor jede Zahl — ob die Probe taugt, sagt erst das Schönbild."""
    aw = _werkzeug("formpruefung_auswertung")
    paare = [{"bild": "B1", "eigen": True, "z": 0.6},
             {"bild": "B1", "eigen": False, "z": 0.7},                      # alt: Nachbarblick
             {"bild": "B1", "eigen": False, "fremd_art": "anderer_koerper", "z": 0.1}]
    assert aw.kreuz(paare, "z", art="nachbarblick") == 0.0
    assert aw.kreuz(paare, "z", art="anderer_koerper") == 1.0
    assert aw.kreuz(paare, "z") == 0.0
    anker = [dict(p, probe="schoenbild") for p in paare] + [
        {"bild": "G", "eigen": True, "probe": "grau", "z": 0.0},
        {"bild": "G", "eigen": False, "probe": "grau", "z": 0.0}]
    assert aw.decke(anker, "z", art="anderer_koerper") == 1.0
    assert aw.decke(anker, "z", art="nachbarblick") == 0.0


def test_doppelte_bilder_werden_erkannt_und_das_juengste_bleibt():
    """194 wiederholte Startwerte aus 190 — dasselbe Bild zählte zweimal."""
    aw = _werkzeug("formpruefung_auswertung")
    zeilen = [
        {"serie": "auf-190", "blind_id": "190-B1", "koerper": "h", "blick": "s", "auge": True,
         "z": 0.585, "y": 1.0},
        {"serie": "auf-194", "blind_id": "194-B7", "koerper": "h", "blick": "s", "auge": True,
         "z": 0.58472, "y": 1.0},
        {"serie": "auf-194", "blind_id": "194-B8", "koerper": "h", "blick": "s", "auge": False,
         "z": 0.1, "y": 1.0}]
    assert aw.doppelte(zeilen) == [["190-B1", "194-B7"]]
    assert [z["blind_id"] for z in aw.ohne_doppelte(zeilen)] == ["194-B7", "194-B8"]


def test_das_messwerkzeug_trennt_nachbarblick_und_anderen_koerper(tmp_path, monkeypatch,
                                                                    capsys):
    import json
    werkzeug = _werkzeug("formkandidaten_messen")
    for ordner in ("eigen", "nachbar", "koerper"):
        (tmp_path / ordner).mkdir()
        (tmp_path / ordner / "blender-report.json").write_text("{}")
    monkeypatch.setattr(fk, "alle_aus_bericht", lambda bild, bericht: {"status": "ok"})
    werkzeug.main(["--bild", "b.png", "--bericht", str(tmp_path / "eigen/blender-report.json"),
                   "--fremd", str(tmp_path / "nachbar/blender-report.json"),
                   "--fremd-koerper", str(tmp_path / "koerper/blender-report.json")])
    zeilen = [json.loads(z) for z in capsys.readouterr().out.splitlines()]
    assert [z.get("fremd_art") for z in zeilen] == [None, "nachbarblick", "anderer_koerper"]


def test_die_auswertung_ohne_doppelte_ueber_die_kommandozeile(tmp_path, capsys):
    import json
    datei = tmp_path / "e.json"
    datei.write_text(json.dumps({"auftrag_id": "auf-x", "bilder": [
        {"koerper": "h", "blick": "s", "blind_id": b, "augenetikett": e, "z": v}
        for b, e, v in (("A", "steht", 1.0), ("B", "steht", 1.0), ("C", "steht nicht", 0.0))]}))
    aw = _werkzeug("formpruefung_auswertung")
    aw.main(["--json", "--ohne-doppelte", str(datei)])
    assert json.loads(capsys.readouterr().out)["n_bilder"] == 2
