"""Zu wenig Grafikspeicher: warten mit Grund, nicht laden und sterben (B161/B1, 24.09.2026).

KosmoOrbit fragte im Auftrag B161: *«ein Weg, der bei zu wenig Grafikspeicher ablehnt mit
Grund, statt abzustuerzen»*. Nachgemessen am 24.09.2026: Einen solchen Weg gab es nicht.
Die Stufenwahl in ``render._lege_auf_geraet`` wählte den sparsamsten Weg auch bei 500 MiB
freiem Speicher, und ein Speicherfehler mitten im Lauf endete als ``status: error`` mit
dem Text nur in ``error`` — das Feld, das die Anzeige drüben liest (``message``), blieb leer.

Geprüft wird hier ohne Grafikkarte: der Riegel vor dem Laden, der Satz nach einem
Speicherfehler, und dass nichts anderes sich ändert.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

from aiimaging import abholer, bruecke, render

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_abholer import _auftrag, _erfolg, _nie_aufgerufen  # noqa: E402

WURZEL = Path(__file__).resolve().parents[1]


def _zettel(ordner):
    return json.loads((ordner / bruecke.DATEI_LAUFZETTEL).read_text(encoding="utf-8"))


def _abholen():
    spec = importlib.util.spec_from_file_location("abholen_probe", WURZEL / "tools" / "abholen.py")
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul


# ---------------------------------------------------------------------------------------
# Der Riegel vor dem Laden
# ---------------------------------------------------------------------------------------

def test_zu_wenig_speicher_laesst_den_auftrag_mit_grund_warten(tmp_path):
    ordner = _auftrag(tmp_path)
    antwort = abholer.hole_einen(ordner, verarbeite=_nie_aufgerufen,
                                 fremde_freigabe_gilt=True,
                                 speicher_frei=lambda: 500)
    assert antwort["tat"] != abholer.TAT_VERARBEITET
    zettel = _zettel(ordner)
    assert zettel["status"] == bruecke.STATUS_QUEUED, "E79: bleibt in der Warteschlange"
    meldung = zettel[bruecke.FELD_MELDUNG]
    assert "500 MiB" in meldung and str(abholer.MINDEST_FREI_MIB) in meldung
    assert "Warteschlange" in meldung


def test_genug_speicher_rechnet_wie_bisher(tmp_path):
    """Die Gegenprobe — sonst wäre ein Riegel, der immer sperrt, ebenfalls grün."""
    ordner = _auftrag(tmp_path)
    antwort = abholer.hole_einen(ordner, verarbeite=_erfolg(), fremde_freigabe_gilt=True,
                                 speicher_frei=lambda: abholer.MINDEST_FREI_MIB)
    assert antwort["tat"] == abholer.TAT_VERARBEITET
    assert _zettel(ordner)["status"] == bruecke.STATUS_DONE


@pytest.mark.parametrize("auskunft", [None, lambda: None, lambda: 1 / 0, lambda: True,
                                      lambda: "viel"])
def test_unbekannter_speicher_sperrt_nichts(tmp_path, auskunft):
    """Neu und darum zurückhaltend: Was bis heute lief, läuft weiter, wenn niemand es weiss."""
    ordner = _auftrag(tmp_path)
    antwort = abholer.hole_einen(ordner, verarbeite=_erfolg(), fremde_freigabe_gilt=True,
                                 speicher_frei=auskunft)
    assert antwort["tat"] == abholer.TAT_VERARBEITET


def test_der_durchgang_reicht_die_auskunft_weiter(tmp_path):
    _auftrag(tmp_path)
    bericht = abholer.durchgang(tmp_path, verarbeite=_nie_aufgerufen,
                                fremde_freigabe_gilt=True, speicher_frei=lambda: 10)
    assert bericht["verarbeitet"] == 0


# ---------------------------------------------------------------------------------------
# Ein Speicherfehler mitten im Lauf
# ---------------------------------------------------------------------------------------

OOM = ("Kamera 's', seed 0: Render fehler — OutOfMemoryError: CUDA out of memory. "
       "Tried to allocate 72.00 MiB.")


def test_ein_speicherfehler_im_lauf_steht_auch_in_message(tmp_path):
    ordner = _auftrag(tmp_path)

    def kracht(auftrag):
        raise abholer.AbholerError(OOM)

    antwort = abholer.hole_einen(ordner, verarbeite=kracht, fremde_freigabe_gilt=True)
    assert antwort["tat"] == abholer.TAT_FEHLER
    zettel = _zettel(ordner)
    assert zettel["status"] == bruecke.STATUS_ERROR
    assert "Grafikspeicher reichte" in zettel[bruecke.FELD_MELDUNG]
    assert "72.00 MiB" in zettel[bruecke.FELD_MELDUNG], "der Wortlaut reist mit"


def test_ein_anderer_fehler_bekommt_diesen_satz_nicht(tmp_path):
    ordner = _auftrag(tmp_path)

    def kracht(auftrag):
        raise RuntimeError("Blender endete mit Code 1")

    abholer.hole_einen(ordner, verarbeite=kracht, fremde_freigabe_gilt=True)
    assert "Grafikspeicher" not in (_zettel(ordner).get(bruecke.FELD_MELDUNG) or "")


@pytest.mark.parametrize("text,erwartet", [
    ("OutOfMemoryError: CUDA out of memory.", True),
    ("RuntimeError: CUDA out of memory. Tried to allocate", True),
    ("RuntimeError: Expected all tensors to be on the same device", False),
    ("Blender endete mit Code 1", False),
])
def test_speichermangel_wird_am_wortlaut_erkannt(text, erwartet):
    assert abholer.ist_speichermangel(RuntimeError(text)) is erwartet


def test_rendere_stellt_den_satz_vor_die_ausnahme(tmp_path):
    """Die Ausnahme bleibt wörtlich; davor steht, was sie heisst."""
    class OutOfMemoryError(RuntimeError):
        pass

    class Modell:
        geraet = "cuda+schichtauslagerung"

        def __call__(self, parameter):
            raise OutOfMemoryError("CUDA out of memory. Tried to allocate 72.00 MiB.")

    tiefe = tmp_path / "tiefe.png"
    from conftest import MINI_PNG
    tiefe.write_bytes(MINI_PNG)
    erg = render.rendere(render.RenderAuftrag(depth_png=str(tiefe), prompt="ein Haus",
                                              ausgabe_png=str(tmp_path / "aus.png")),
                         modell=Modell())
    if erg["status"] == render.STATUS_ABGELEHNT:
        pytest.skip(f"Auftrag vorher abgelehnt: {erg.get('maengel')}")
    assert erg["status"] == render.STATUS_FEHLER
    assert erg["error"].startswith("Grafikspeicher reichte nicht (Weg cuda+schichtauslagerung)")
    assert "OutOfMemoryError: CUDA out of memory" in erg["error"]


# ---------------------------------------------------------------------------------------
# Der Betriebsweg: EinmalGeladen
# ---------------------------------------------------------------------------------------

def test_nach_einem_speicherfehler_wird_das_modell_nicht_behalten():
    abholen = _abholen()
    geladen = []

    class Modell:
        bedarf = {"grund": "49152 MiB x 1.25 verlangt"}

        def __init__(self):
            self.mal = 0

        def __call__(self, parameter):
            raise RuntimeError("CUDA out of memory")

    def lader(name, wurzel):
        geladen.append(name)
        return Modell()

    einmal = abholen.EinmalGeladen(lader, "backbone")
    assert not einmal.haelt_gewichte
    with pytest.raises(RuntimeError):
        einmal({"backbone": "x"})
    assert einmal.bedarf == {"grund": "49152 MiB x 1.25 verlangt"}, "bedarf reist jetzt mit"
    assert not einmal.haelt_gewichte, "nach dem Speicherfehler verworfen"
    with pytest.raises(RuntimeError):
        einmal({"backbone": "x"})
    assert geladen == ["x", "x"]


def test_ein_anderer_fehler_behaelt_das_modell():
    """Gegenprobe: Neu laden kostet 40 GB Arbeitsspeicher — nur, wenn es etwas bringt."""
    abholen = _abholen()
    geladen = []

    def lader(name, wurzel):
        geladen.append(name)

        def modell(parameter):
            raise ValueError("kaputter Parameter")
        return modell

    einmal = abholen.EinmalGeladen(lader, "backbone")
    for _ in range(2):
        with pytest.raises(ValueError):
            einmal({"backbone": "x"})
    assert geladen == ["x"]
    assert einmal.haelt_gewichte
