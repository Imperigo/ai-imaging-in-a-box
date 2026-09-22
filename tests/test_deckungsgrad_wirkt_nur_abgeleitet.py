"""Der Deckungsgrad wird nur dort gemeldet, wo er gewirkt hat — und nur dort bestellt.

**Befund 22.09.2026** (Anlass ``auf-20260922-137``: zwei Deckungsgrade, dieselbe
Tiefenkarte). Mit einer Attrappe von ``bpy`` am ``main`` des Runners nachgefahren:

(a) Der Runner liest ``--deckungsgrad`` nur auf dem Kameraweg ``abgeleitet`` (Kamera aus
    dem Richtungskürzel gerechnet). Auf ``vorgegeben`` (``--auge``/``--blick-auf``) und
    ``rueckfall`` (gar keine Kamera) ist er wirkungslos — der Bericht schrieb ihn trotzdem
    hinein, und wer ihn las, bekam eine Rahmung gemeldet, die nie gestellt wurde.
(b) ``kamera`` und ``auge`` zugleich: Unterwegs fiel das Kürzel still weg (``seams``
    reicht nur ``--auge`` weiter). Dieselbe Vorrangregel, die bei ``innenraum`` + ``auge``
    abgewiesen wird.

Die Wächter hier prüfen die **Wirkung**: am Runner den geschriebenen Bericht auf allen
drei Wegen, an der Kette, ob der echte Multipass-Ausführer die Naht zum Runner überhaupt
erreicht.

Der Runner wird **als Datei** geladen, nicht als ``aiimaging.runners…`` importiert — das
wäre der Weg, den ``tests/test_prozessgrenze.py`` verbietet (Regel 2). Die Attrappen
stehen nur in ``sys.modules`` dieses Tests.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import pytest

from aiimaging import abholer, kette, seams
from aiimaging.kette import ART_MULTIPASS, KNOTEN_MULTIPASS

RUNNER = (Path(__file__).resolve().parents[1]
          / "src" / "aiimaging" / "runners" / "blender_depth_stage.py")

#: Die Hüllbox der Attrappenszene, in Metern. Gross genug, dass die Kamerarechnung den
#: Deckungsgrad einhält und nicht der Mindestabstand übernimmt.
SZENE = ([0.0, 0.0, 0.0], [20.0, 16.0, 9.0])
BBOX = [list(SZENE[0]), list(SZENE[1])]

AUGE = ["--auge=40,-30,1.7", "--blick-auf=10,8,4.5"]


# ======================================================================================
# Die Attrappe — gerade so viel Blender, wie `main` bis zum Bericht anfasst
# ======================================================================================

class _Vektor(list):
    """So viel ``mathutils.Vector``, wie ``_kamera_setzen`` rechnet."""

    def __add__(self, anderer):
        return _Vektor(a + b for a, b in zip(self, anderer))

    def __sub__(self, anderer):
        return _Vektor(a - b for a, b in zip(self, anderer))

    def __mul__(self, zahl):
        return _Vektor(a * zahl for a in self)

    def to_track_quat(self, *_):
        return (1.0, 0.0, 0.0, 0.0)


class _Objekte(list):
    def new(self, name, daten):
        return SimpleNamespace(name=name, data=daten, type="CAMERA")


def _runner(monkeypatch, *, ohne_bibliothek: bool = False):
    """Den Runner mit gefälschtem ``bpy`` laden. Gerendert wird nichts — der Bericht
    entsteht trotzdem, und um ihn geht es."""
    bpy = mock.MagicMock()
    bpy.app.version_string = "attrappe"
    bpy.data.objects = _Objekte()
    bpy.data.materials = []
    bpy.data.cameras.new = lambda name: SimpleNamespace(
        lens=50.0, shift_y=0.0, sensor_fit="AUTO", sensor_width=36.0)
    monkeypatch.setitem(sys.modules, "bpy", bpy)
    monkeypatch.setitem(sys.modules, "mathutils", SimpleNamespace(Vector=_Vektor))

    spez = importlib.util.spec_from_file_location("blender_pruefling_deckung", RUNNER)
    modul = importlib.util.module_from_spec(spez)
    spez.loader.exec_module(modul)

    # Was Blender-Geometrie, Licht und Kompositor braucht, fällt weg. Die Kamera
    # (`_kamera_setzen`) und der Bericht laufen ECHT.
    monkeypatch.setattr(modul, "_bbox_aller_meshes", lambda: (list(SZENE[0]), list(SZENE[1])))
    monkeypatch.setattr(modul, "_bbox_bauwerk", lambda: (
        list(SZENE[0]), list(SZENE[1]), "", None,
        {"entschieden_durch": "keine", "gelaende_namen": []}))
    monkeypatch.setattr(modul, "_sonne_setzen", lambda *a, **k: (None, {"attrappe": True}))
    monkeypatch.setattr(modul, "_compositor_auf_tiefe", lambda out: "attrappe")
    monkeypatch.setattr(modul, "_welt_setzen", lambda *a, **k: None)
    if ohne_bibliothek:
        monkeypatch.setattr(modul, "_kameras_modul", lambda: None)
    return modul


def _bericht(monkeypatch, tmp_path, *schalter, ohne_bibliothek=False) -> dict:
    """``main`` fahren wie Blender es täte und den geschriebenen Bericht lesen."""
    modul = _runner(monkeypatch, ohne_bibliothek=ohne_bibliothek)
    aus = tmp_path / f"lauf_{sum(1 for _ in tmp_path.iterdir())}"
    monkeypatch.setattr(sys, "argv", ["blender", "--background", "--python", "x.py", "--",
                                      "--glb", "m.glb", "--out", str(aus),
                                      "--ohne-material-id", *schalter])
    modul.main()
    return json.loads((aus / "blender-report.json").read_text(encoding="utf-8"))


# ======================================================================================
# (a) Am Runner — auf allen drei Wegen
# ======================================================================================

def test_abgeleitet_meldet_den_deckungsgrad_mit_dem_gerechnet_wurde(monkeypatch, tmp_path):
    """Der einzige Weg, auf dem er gelesen wird — und dort wirkt er auch: Zwei Werte
    ergeben zwei Standorte. Ohne diese Gegenprobe prüfte der Test nur eine Zahl."""
    eng = _bericht(monkeypatch, tmp_path, "--kamera", "sSE", "--deckungsgrad=0.55")
    weit = _bericht(monkeypatch, tmp_path, "--kamera", "sSE", "--deckungsgrad=0.70")

    assert eng["kamera"]["weg"] == "abgeleitet"
    assert eng["deckungsgrad"] == pytest.approx(0.55)
    assert weit["deckungsgrad"] == pytest.approx(0.70)
    assert eng["deckungsgrad_wirkungslos"] is None
    assert eng["kamera"]["auge"] != weit["kamera"]["auge"], (
        "Auf dem abgeleiteten Weg muss der Deckungsgrad den Standort verschieben.")


@pytest.mark.parametrize("weg, schalter", [
    ("vorgegeben", AUGE),
    ("rueckfall", []),
])
def test_ohne_abgeleitete_kamera_steht_kein_deckungsgrad_im_bericht(
        monkeypatch, tmp_path, weg, schalter):
    """**Der Kern des Befunds.** Zwei Bestellungen, dieselbe Kamera — und bis zum
    22.09.2026 zwei verschiedene Zahlen im Bericht."""
    eng = _bericht(monkeypatch, tmp_path, *schalter, "--deckungsgrad=0.55")
    weit = _bericht(monkeypatch, tmp_path, *schalter, "--deckungsgrad=0.70")

    assert eng["kamera"]["weg"] == weg
    assert eng["kamera"]["auge"] == weit["kamera"]["auge"], (
        "Voraussetzung des Befunds: Auf diesem Weg wirkt der Deckungsgrad nicht.")
    assert eng["deckungsgrad"] is None and weit["deckungsgrad"] is None, (
        f"Auf dem Weg {weg!r} hat der Deckungsgrad nichts gerahmt. `None` heisst NICHT "
        f"GERAHMT — eine Zahl hier behauptet eine Rahmung, die nie gestellt wurde.")
    grund = eng["deckungsgrad_wirkungslos"]
    assert isinstance(grund, str) and weg in grund and "0.55" in grund, (
        "Der Grund muss den Weg und die übergangene Bestellung nennen.")


def test_ohne_bestellung_sagt_der_grund_dass_keiner_bestellt_war(monkeypatch, tmp_path):
    """Nicht bestellt und übergangen sind verschiedene Aussagen."""
    bericht = _bericht(monkeypatch, tmp_path, *AUGE)
    assert bericht["deckungsgrad"] is None
    assert "Bestellt war keiner" in bericht["deckungsgrad_wirkungslos"]


def test_rueckfall_ohne_bibliothek_schreibt_trotzdem_einen_bericht(monkeypatch, tmp_path):
    """Bis zum 22.09.2026 rechnete der Bericht ``_kameras_modul().DECKUNGSGRAD`` — ohne
    erreichbare Bibliothek ist das ``None.DECKUNGSGRAD``, und ``main`` stürzte ab, statt
    den Rückfall zu melden, den ``_kameras_modul`` genau dafür vorsieht."""
    bericht = _bericht(monkeypatch, tmp_path, "--kamera", "sSE", ohne_bibliothek=True)
    assert bericht["kamera"]["weg"] == "rueckfall"
    assert bericht["deckungsgrad"] is None
    assert bericht["deckungsgrad_wirkungslos"]


def test_der_abholer_nimmt_den_bericht_des_vorgegebenen_wegs_nicht_als_bestellung(
        monkeypatch, tmp_path):
    """Der Leser am anderen Ende: Aus dem Bericht des vorgegebenen Wegs darf kein
    Deckungsgrad «aus dem Bericht» werden, und abgebrochen wird dort nicht."""
    bericht = _bericht(monkeypatch, tmp_path, *AUGE, "--deckungsgrad=0.55")
    lage = abholer._rahmung_vor_dem_render(bericht)
    assert lage["deckungsgrad_quelle"] != "bericht"
    assert lage["deckungsgrad"] != pytest.approx(0.55)
    assert lage["abbruch"] is None


# ======================================================================================
# (b) An der Kette — über baue_kette und den echten Multipass-Ausführer
# ======================================================================================

@pytest.fixture
def naht(monkeypatch):
    """Die Naht zum Runner abgefangen: Was hier ankommt, wäre an Blender gegangen."""
    aufrufe: list[dict] = []

    def glb_zu_multipass(glb_path, out_dir, **kw):
        aufrufe.append(kw)
        tiefe = Path(out_dir) / "tiefe_norm.png"
        tiefe.write_text("t", encoding="utf-8")
        return {"status": "ok", "depth_png": str(tiefe)}

    monkeypatch.setattr(seams, "glb_zu_multipass", glb_zu_multipass)
    return aufrufe


def _multipass(tmp_path, **bestellung) -> dict:
    graph = kette.baue_kette(glb_path=str(tmp_path / "m.glb"), up_axis="Z",
                             prompt="Haus", bbox=BBOX, **bestellung)
    return kette.AUSFUEHRER[ART_MULTIPASS](
        knoten=graph.knoten[KNOTEN_MULTIPASS],
        eingaben=[{"glb_path": str(tmp_path / "m.glb"), "up_axis": "Z"}],
        out_dir=tmp_path)


def test_kamera_und_auge_zugleich_werden_abgewiesen(tmp_path, naht):
    aus = _multipass(tmp_path, kamera="sSE", auge=[40.0, -30.0, 1.7],
                     blick_auf=[10.0, 8.0, 4.5])
    assert aus["status"] == kette.STATUS_FEHLER
    assert "zweimal bestellt" in aus["error"] and "kamera" in aus["error"]
    assert naht == [], "Abgewiesen heisst: Blender wird gar nicht erst gerufen."


def test_kamera_und_innenraum_zugleich_werden_abgewiesen(tmp_path, naht):
    """``innenraum`` rechnet ein Auge aus — danach fiele das Kürzel genauso still weg."""
    aus = _multipass(tmp_path, kamera="sSE", innenraum={"raum": "R1"})
    assert aus["status"] == kette.STATUS_FEHLER
    assert "zweimal bestellt" in aus["error"] and "innenraum" in aus["error"]
    assert naht == []


@pytest.mark.parametrize("ohne_kamera", [
    {},                                                        # Rückfall
    {"auge": [40.0, -30.0, 1.7], "blick_auf": [10.0, 8.0, 4.5]},  # vorgegeben
])
def test_deckungsgrad_ohne_kamera_wird_abgewiesen(tmp_path, naht, ohne_kamera):
    aus = _multipass(tmp_path, deckungsgrad=0.55, **ohne_kamera)
    assert aus["status"] == kette.STATUS_FEHLER
    assert "Rahmung bestellt, aber kein Kameraweg" in aus["error"]
    assert naht == []


def test_die_gegenproben_laufen_durch(tmp_path, naht):
    """Ohne sie zeigten die Abweisungen oben nur, dass irgendetwas abweist."""
    mit_kamera = _multipass(tmp_path, kamera="sSE", deckungsgrad=0.55)
    von_hand = _multipass(tmp_path, auge=[40.0, -30.0, 1.7], blick_auf=[10.0, 8.0, 4.5])
    assert mit_kamera["status"] == kette.STATUS_OK
    assert von_hand["status"] == kette.STATUS_OK
    assert naht[0]["deckungsgrad"] == 0.55 and naht[0]["kamera"] == "sSE"
    assert naht[1]["auge"] == [40.0, -30.0, 1.7] and "kamera" not in naht[1]
