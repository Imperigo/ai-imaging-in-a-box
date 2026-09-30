"""``bedarf.grund`` ist nie leer — weder im Blender-Bericht noch neben dem Geräteweg.

Der Anlass (HomeStation, ``auf-20260924-173``, Zusatz A4)
---------------------------------------------------------
Die Ansage zu Stufe 3 versprach den Satz «im Blender-/Render-Bericht unter bedarf.grund».
Die Antwort vom Gerät: *«LEER — in blender-report.json steht je Kamera "grund": ""; den
Grund nennt nur das Abholer-Protokoll.»*

Nachgelesen, was dort wirklich stand:

* **Der Blender-Bericht hatte gar keinen** ``bedarf``. Die leeren ``grund``-Felder darin
  gehören zu Sonne und Sichtlinie und heissen «nichts zu melden». Blender rechnet auf der
  CPU (gemessen, ``tests/test_cpu_ist_gemessen.py``) und entscheidet nichts über
  Grafikspeicher — gesagt hat der Bericht das nirgends.
* **Neben dem Geräteweg** (``render._geraeteweg``) stand bei einem gemeldeten Weg
  ``"grund": ""`` — eine Zeile über ``bedarf.grund``, in dem die ganze Rechnung stand.
  Ein leeres Feld neben einem gefüllten sagt dem Leser nicht «siehe nebenan», sondern
  «nichts».

Beides ist jetzt ein Satz: im Blender-Bericht, warum es nichts zu entscheiden gab; am
Geräteweg, mit welcher Rechnung der Weg gewählt wurde — oder dass der Lader es nicht sagt.

Regel 2: Der Runner wird als Datei mit einer Attrappe von ``bpy`` geladen, nie importiert.
"""
from __future__ import annotations

from pathlib import Path

from aiimaging import render
from conftest import MINI_PNG

from test_runde7_kamera import AUGE, _bericht, _runner


# ── Blender-Bericht ───────────────────────────────────────────────────────────────────

def test_der_blender_bericht_traegt_bedarf_mit_einem_satz(monkeypatch, tmp_path):
    """**Der Kern des Befunds.** Wer den Blender-Bericht öffnet und ``bedarf.grund``
    sucht, findet einen Satz — und der sagt, dass es nichts zu entscheiden gab."""
    bericht = _bericht(monkeypatch, tmp_path, *AUGE)

    bedarf = bericht["bedarf"]
    assert isinstance(bedarf["grund"], str) and bedarf["grund"].strip()
    assert "CPU" in bedarf["grund"]
    assert "nichts zu entscheiden" in bedarf["grund"]
    # Und er sagt, wo die Entscheidung steht, die es wirklich gab.
    assert "geraeteweg.bedarf.grund" in bedarf["grund"]


def test_die_zahlen_im_blender_bedarf_sind_unbestimmt_nicht_null(monkeypatch):
    """Dieselbe Form wie ``render._bedarfsbericht``: ``None`` heisst nicht bestimmt. Eine
    ``0`` bei ``spielraum_byte`` hiesse «auf den Byte genau gepasst» — eine erfundene
    Messung, und ``abholer._ist_knapp`` läse sie als knapp."""
    from aiimaging import abholer

    bedarf = _runner(monkeypatch)._bedarf_befund()

    for feld in ("summe_byte", "groesster_byte", "zuschlag", "verlangt_byte",
                 "frei_byte", "spielraum_byte"):
        assert feld in bedarf and bedarf[feld] is None, feld
    assert abholer._ist_knapp(bedarf) is False


def test_der_blender_bedarf_hat_dieselben_felder_wie_der_des_bildmodells(monkeypatch):
    """Ein Leser, der beide Berichte liest, soll nicht zwei Formen kennen müssen."""
    blender = _runner(monkeypatch)._bedarf_befund()
    bild = render._bedarfsbericht(quelle="x", summe=None, groesster=None, zuschlag=None,
                                  frei=None, grund="y")
    assert set(bild) <= set(blender)


# ── Geräteweg ─────────────────────────────────────────────────────────────────────────

def _auftrag(tmp_path):
    tiefe = tmp_path / "t.png"
    tiefe.write_bytes(MINI_PNG)
    return render.RenderAuftrag(depth_png=str(tiefe), prompt="a house",
                                ausgabe_png=str(tmp_path / "b.png"))


def _modell(**felder):
    def modell(parameter):
        Path(parameter["ausgabe_png"]).write_bytes(MINI_PNG)
        return parameter["ausgabe_png"]

    for name, wert in felder.items():
        setattr(modell, name, wert)
    return modell


def test_ein_gemeldeter_weg_nennt_seine_rechnung_im_grund(tmp_path):
    """Der Satz aus ``bedarf.grund`` steht auch unter ``geraeteweg.grund`` — dort, wo
    die HomeStation nachsah und ``""`` fand."""
    bedarf = render._bedarfsbericht(quelle=render.QUELLE_MESSUNG, summe=100 * 2**20,
                                    groesster=50 * 2**20, zuschlag=1.1, frei=80 * 2**20)
    assert bedarf["grund"], "Voraussetzung: Der Kern füllt bedarf.grund."

    erg = render.rendere(_auftrag(tmp_path),
                         modell=_modell(geraet="cuda+schichtauslagerung", bedarf=bedarf))

    weg = erg["geraeteweg"]
    assert weg["gemeldet"] is True
    assert weg["bedarf"]["grund"] == bedarf["grund"]
    assert bedarf["grund"] in weg["grund"]
    assert "cuda+schichtauslagerung" in weg["grund"]


def test_ein_weg_ohne_rechnung_sagt_dass_er_sie_nicht_nennt(tmp_path):
    """Ein fremder Lader meldet den Weg, aber nicht, wie er gewählt wurde. Dann steht
    genau das da — UNBEKANNT, und nicht ein leeres Feld, das nach «nichts» aussieht."""
    erg = render.rendere(_auftrag(tmp_path), modell=_modell(geraet="cuda"))

    weg = erg["geraeteweg"]
    assert weg["gemeldet"] is True and weg["bedarf"] is None
    assert weg["grund"].strip()
    assert "UNBEKANNT" in weg["grund"]


def test_die_cpu_ohne_karte_sagt_dass_es_nichts_zu_entscheiden_gab():
    """Der Fall «nichts zu entscheiden» auf der Bildseite: keine Karte sichtbar. Der
    Grund steht im Kern und kommt über den Geräteweg an."""
    class Pipeline:
        def to(self, _):
            pass

    class Torch:
        class cuda:
            @staticmethod
            def is_available():
                return False

    weg, _entflechtung, bedarf = render._lege_auf_geraet(Pipeline(), None, Torch)
    assert weg == "cpu"
    assert "nichts zu entscheiden" in bedarf["grund"]
    grund = render._geraeteweg_grund(weg, bedarf)
    assert "nichts zu entscheiden" in grund
