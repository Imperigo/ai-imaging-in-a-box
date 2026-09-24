"""Zwei Ansichten, die dasselbe zeigen — und ein Renderlauf für nichts.

**Der Befund** (HomeStation, `auf-vis-20260824-12`, 24.08.2026): Bei einem Quader sind
`sSE` und `nNW` **byte-identisch**. Ein Quader hat zweizählige Drehsymmetrie, und die
beiden Über-Eck-Ansichten der HABS/NPS-Regel fallen dann zusammen. 24,5 s Diffusion für
ein Bild, das schon dalag — gerade bei den einfachen Demofällen.

**Warum an der Soll-Karte und nicht an der Hüllbox.** Die Hüllbox hat *immer*
zweizählige Symmetrie. Aus ihr allein liesse sich das nicht entscheiden, ohne bei jedem
realen Bauwerk falschen Alarm zu schlagen — ein Haus mit Eingang auf einer Seite steckt in
derselben Box wie eines ohne. Die Soll-Tiefenkarte entscheidet es zuverlässig, und sie
liegt **vor** dem teuren Bildrender vor.

**Und die Doppelung darf das Urteil nicht verbessern.** Ein Minimum fällt mit der Zahl der
Ziehungen; eine Wiederholung ist keine Ziehung. Sie mitzuzählen wäre eine stille
Verschärfung — genau der Fehler vom 23.08.2026, als drei Ansichten das Gate ungefragt
strenger machten.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from aiimaging import abholer
from conftest import MINI_PNG


# ======================================================================================
# Die Kennzahl
# ======================================================================================

def test_zwei_gleiche_karten_sind_dieselbe_ansicht():
    assert abholer._gleiche_ansicht([0.0, 1.0, 2.0, 3.0], [0.0, 1.0, 2.0, 3.0])


def test_zwei_verschiedene_karten_sind_verschiedene_ansichten():
    """Die Gegenprobe. Ein Vergleich, der alles gleich nennt, spart jeden zweiten Render
    und liefert das falsche Bild."""
    assert not abholer._gleiche_ansicht([0.0, 1.0, 2.0, 3.0], [0.0, 1.0, 2.0, 3.5])


def test_eine_andere_maske_ist_eine_andere_ansicht():
    inf = float("inf")
    assert not abholer._gleiche_ansicht([1.0, inf], [1.0, 1.0])


def test_rechenrauschen_gilt_als_gleich_ein_zentimeter_nicht():
    """Gemessen 9,5·10⁻⁶ m zwischen sSE und nNW des Testbaus (24.09.2026) — gleich.
    Ein Zentimeter ist eine andere Geometrie."""
    assert abholer._gleiche_ansicht([10.0, 11.0], [10.0000095, 11.0])
    assert not abholer._gleiche_ansicht([10.0, 11.0], [10.01, 11.0])


def test_die_flache_karte_ist_die_form_des_betriebs():
    """**Der Fehler, der die Erkennung im Betrieb abgeschaltet hatte** (auf-169).

    ``tiefen_aus_report`` liefert eine FLACHE Liste. Die alte Kennung erwartete Zeilen,
    stolperte an der ersten Zahl und gab still «nicht vergleichbar» zurück — die Proben
    fütterten Zeilen und blieben grün.
    """
    assert abholer._flache_karte([1.0, 2.0]) == [1.0, 2.0]
    assert abholer._flache_karte([[1.0], [2.0]]) == [1.0, 2.0]
    assert abholer._flache_karte(["x"]) is None


@pytest.mark.parametrize("kaputt", [None, "karte", [["a"]], [[None]]])
def test_eine_unlesbare_karte_hat_keinen_zwilling(kaputt):
    """Nicht vergleichbar führt nie zu einer Doppelung — im Zweifel wird gerendert, denn
    ein fehlendes Bild ist teurer als ein doppeltes."""
    vorbild = [{"soll": [0.0] * 4, "breite": 2, "hoehe": 2, "kamera": "k0", "urteil": {}}]
    assert abholer._finde_zwilling(vorbild, kaputt, 2, 2) is None


def test_ohne_bildmasse_gibt_es_keinen_zwilling():
    vorbild = [{"soll": [0.0], "breite": 1, "hoehe": 1, "kamera": "k0", "urteil": {}}]
    assert abholer._finde_zwilling(vorbild, [0.0], None, 1) is None
    assert abholer._finde_zwilling(vorbild, [0.0], 1, 0) is None
    assert abholer._finde_zwilling(vorbild, [0.0], 1, 1) is vorbild[0]


# ======================================================================================
# Die Naht — hier entscheidet sich, ob überhaupt Rechenzeit gespart wird
# ======================================================================================

def _lauf(tmp_path, karten):
    """Ein Lauf mit je einer Soll-Karte pro Kamera. Gibt (ergebnis, Zahl der Render).

    Die Karten sind seit dem 24.09.2026 FLACH, wie ``tiefen_aus_report`` sie liefert. Bis
    dahin fütterte diese Attrappe Zeilen — die einzige Form, in der die alte Kennung
    funktionierte, und nicht die des Betriebs (auf-169).
    """
    folge = iter(karten)
    zaehler = {"render": 0}

    def multipass(glb, aus, **kw):
        tiefe = Path(aus) / "tiefe_norm.png"
        tiefe.write_bytes(MINI_PNG)
        return {"depth_png": str(tiefe), "kamera": {"weg": "vorgegeben"}}

    def rendere(auftrag, **kw):
        zaehler["render"] += 1
        bild = Path(tmp_path) / f"bild_{zaehler['render']}.png"
        bild.write_bytes(MINI_PNG)
        return {"status": "ok", "bild_png": str(bild), "hinweise": ()}

    verarbeite = abholer.verarbeiter(
        out_wurzel=tmp_path, nullprobe=False,
        _multipass=multipass, _rendere=rendere,
        _qa=lambda *a, **k: {"score": 0.9, "bestanden": True},
        _soll=lambda *a, **k: (next(folge), 2, 1))

    kameras = [{"kuerzel": f"k{i}", "richtung": "sSE"} for i in range(len(karten))]
    ergebnis = verarbeite({"modell": Path(tmp_path) / "m.glb", "job_id": "vis-1-aaaaaa",
                           "verzeichnis": tmp_path,
                           "szene": {"kameras": kameras, "aufloesung": 64, "hoehe": 64,
                                     "samples": 1, "prompt": "a house"}})
    return ergebnis, zaehler["render"]


def test_zwei_gleiche_ansichten_werden_einmal_gerendert(tmp_path):
    """**Der gemessene Fall.** 24,5 s gespart, und das Bild ist dasselbe."""
    ergebnis, n_render = _lauf(tmp_path, [[1.0, 2.0], [1.0, 2.0]])

    assert n_render == 1
    assert ergebnis["kameras"][1]["doppelt_von"] == "k0"
    assert ergebnis["kameras"][0]["doppelt_von"] is None
    assert ergebnis["kameras"][1]["bild_png"] == ergebnis["kameras"][0]["bild_png"]


def test_zwei_ungleiche_ansichten_werden_beide_gerendert(tmp_path):
    """**Die Gegenprobe, und sie ist die wichtigere.** Eine Erkennung, die immer greift,
    liefert für jede Ansicht dasselbe Bild und sieht dabei sparsam aus."""
    ergebnis, n_render = _lauf(tmp_path, [[1.0, 2.0], [3.0, 4.0]])

    assert n_render == 2
    assert [k["doppelt_von"] for k in ergebnis["kameras"]] == [None, None]


def test_die_doppelung_zaehlt_nicht_als_zweite_ziehung(tmp_path):
    """**Sonst wäre das Ganze eine stille Verschärfung.** Das Minimum fällt mit der Zahl
    der Ziehungen — bei drei Ansichten rechnerisch um 0,845 Streuungen. Eine Wiederholung
    ist keine Ziehung."""
    ergebnis, _ = _lauf(tmp_path, [[1.0, 2.0], [1.0, 2.0], [5.0, 6.0]])

    spanne = ergebnis["geometrie_urteil"]["kameraspanne"]
    assert spanne["n"] == 3, "alle drei Ansichten waren bestellt"
    assert spanne["n_gemessen"] == 2, "aber nur zwei sind unabhaengig"
    assert spanne["n_doppelt"] == 1
    assert "IDENTISCH" in spanne["hinweis"]


def test_ohne_doppelung_steht_der_satz_nicht_im_hinweis(tmp_path):
    """Ein Satz, der bei jedem Lauf dasteht, ist nach dem dritten Mal keiner."""
    ergebnis, _ = _lauf(tmp_path, [[1.0, 2.0], [3.0, 4.0]])

    spanne = ergebnis["geometrie_urteil"]["kameraspanne"]
    assert spanne["n_doppelt"] == 0
    assert "IDENTISCH" not in spanne["hinweis"]


def test_der_kurzbefund_nennt_die_uebernommene_ansicht():
    """Ein wiederverwendetes Bild, das niemand als solches erkennt, ist von einem
    zweiten Renderlauf nicht zu unterscheiden — und dann steht in der Auswertung eine
    Übereinstimmung, die keine ist."""
    zeilen = abholer.befund_kurz({"kameras": [
        {"kamera": "sSE", "doppelt_von": None},
        {"kamera": "nNW", "doppelt_von": "sSE"}]})

    treffer = [z for z in zeilen if "identisch" in z]
    assert len(treffer) == 1
    assert "nNW ist mit sSE identisch" in treffer[0]


def test_ohne_doppelung_steht_die_zeile_nicht_da():
    zeilen = abholer.befund_kurz({"kameras": [{"kamera": "sSE", "doppelt_von": None}]})

    assert not [z for z in zeilen if "identisch" in z]


# ======================================================================================
# Mit echtem Blender — die Form und das Rauschen des Betriebs (auf-169, 24.09.2026)
# ======================================================================================

def _kette_fehlt() -> bool:
    import shutil
    from aiimaging import seams
    if not shutil.which("blender") and not Path("/opt/blender/blender").exists():
        return True
    try:
        return not Path(seams.finde_ifc_python()).exists()
    except Exception:                                  # noqa: BLE001
        return True


@pytest.mark.skipif(_kette_fehlt(), reason="Blender oder .venv-ifc fehlt")
def test_am_echten_testbau_sind_sse_und_nnw_zwillinge_und_s_nicht(tmp_path):
    """Die HomeStation lieferte sSE und nNW byte-gleich und hatte beide gerechnet (468 s
    für nichts). Hier dieselbe Frage an echten Blender-Karten — mit der Gegenprobe ``s``."""
    import subprocess
    import sys
    from aiimaging import bildlesen, seams
    wurzel = Path(__file__).resolve().parents[1]
    subprocess.run([sys.executable, "tools/make_test_ifc.py", str(tmp_path / "bau.ifc")],
                   check=True, capture_output=True, cwd=wurzel)
    assert seams.ifc_zu_glb(tmp_path / "bau.ifc", tmp_path / "m.glb")["status"] == "ok"
    karten = {}
    for k in ("s", "sSE", "nNW"):
        bericht = seams.glb_zu_multipass(tmp_path / "m.glb", tmp_path / k, up_axis="Y",
                                         kamera=k, aufloesung=96, hoehe=64, samples=1,
                                         material_id=False, beauty=False, timeout=600)
        assert bericht["status"] == "ok", bericht.get("error")
        karten[k] = bildlesen.tiefen_aus_report(bericht)
    gesehen = []
    for k in ("s", "sSE"):
        soll, b, h = karten[k]
        gesehen.append({"soll": abholer._flache_karte(soll), "breite": b, "hoehe": h,
                        "kamera": k, "urteil": {}})
    soll, b, h = karten["nNW"]
    zwilling = abholer._finde_zwilling(gesehen, soll, b, h)
    assert zwilling is not None and zwilling["kamera"] == "sSE"
    soll_s, b, h = karten["s"]
    assert abholer._finde_zwilling(gesehen[1:], soll_s, b, h) is None
