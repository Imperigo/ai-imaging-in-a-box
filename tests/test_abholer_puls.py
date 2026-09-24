"""«Läuft, leer» ist von «läuft nicht» zu unterscheiden (B161/B8, 24.09.2026).

Nachgemessen vor dem Bau: Ein leerer Durchgang und ein Abholer, der gar nicht lief,
hinterliessen dieselbe Ablage, und ``/health`` kannte den Abholer nicht.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from aiimaging import abholer, bruecke, knotenweg

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_abholer import _auftrag, _erfolg, _nie_aufgerufen  # noqa: E402

UHR = 1_790_000_000.0


def _puls(ablage):
    return json.loads((ablage / abholer.DATEI_PULS).read_text(encoding="utf-8"))


def test_ohne_je_einen_durchgang_heisst_es_nie_gesehen(tmp_path):
    zustand = knotenweg.abholer_zustand(tmp_path, _uhr=lambda: UHR)
    assert zustand["zustand"] == "nie_gesehen"
    assert "andere Ablage" in zustand["grund"]


def test_ein_leerer_durchgang_hinterlaesst_einen_puls(tmp_path):
    bericht = abholer.durchgang(tmp_path, verarbeite=_nie_aufgerufen, _uhr=lambda: UHR)
    assert bericht["puls"] == "geschrieben"
    puls = _puls(tmp_path)
    assert puls["schema"] == abholer.SCHEMA_PULS and puls["gesehen"] == 0
    zustand = knotenweg.abholer_zustand(tmp_path, _uhr=lambda: UHR + 10)
    assert zustand["zustand"] == "laeuft_leer" and zustand["alter_s"] == 10.0


def test_ein_alter_puls_heisst_steht(tmp_path):
    abholer.durchgang(tmp_path, verarbeite=_nie_aufgerufen, _uhr=lambda: UHR)
    zustand = knotenweg.abholer_zustand(
        tmp_path, _uhr=lambda: UHR + knotenweg.PULS_FRIST_S + 1)
    assert zustand["zustand"] == "steht"


def test_liegengelassene_auftraege_heissen_wartet(tmp_path):
    _auftrag(tmp_path, token=None)            # ohne Freigabe: wird liegengelassen
    abholer.durchgang(tmp_path, verarbeite=_nie_aufgerufen, _uhr=lambda: UHR)
    assert _puls(tmp_path)["liegengelassen"] == 1
    assert knotenweg.abholer_zustand(tmp_path, _uhr=lambda: UHR)["zustand"] == "wartet"


def test_ein_laufender_auftrag_heisst_arbeitet(tmp_path):
    abholer.durchgang(tmp_path, verarbeite=_nie_aufgerufen, _uhr=lambda: UHR)
    _auftrag(tmp_path, status=bruecke.STATUS_RUNNING)
    assert knotenweg.abholer_zustand(tmp_path, _uhr=lambda: UHR)["zustand"] == "arbeitet"


def test_ein_fehlender_ablageort_wird_nicht_angelegt(tmp_path):
    """Wer in die falsche Ablage schaut, soll dort keinen beruhigenden Puls hinterlassen."""
    fehlt = tmp_path / "gibt-es-nicht"
    bericht = abholer.durchgang(fehlt, verarbeite=_nie_aufgerufen, _uhr=lambda: UHR)
    assert bericht["puls"].startswith("nicht geschrieben")
    assert not fehlt.exists()


def test_der_puls_ist_kein_auftrag(tmp_path):
    """Die Datei liegt neben den Aufträgen und darf keiner werden."""
    abholer.durchgang(tmp_path, verarbeite=_nie_aufgerufen, _uhr=lambda: UHR)
    assert bruecke.offene_auftraege(tmp_path) == []
    _auftrag(tmp_path)
    bericht = abholer.durchgang(tmp_path, verarbeite=_erfolg(), fremde_freigabe_gilt=True,
                                _uhr=lambda: UHR)
    assert bericht["verarbeitet"] == 1 and _puls(tmp_path)["verarbeitet"] == 1


def test_gesundheit_traegt_den_abholer_neben_den_diensten(tmp_path):
    antwort = knotenweg.gesundheit(tmp_path, _uhr=lambda: UHR)
    assert all(isinstance(v, bool) for v in antwort["services"].values()), \
        "ihr BridgeHealth-Schema kennt in services nur Wahrheitswerte"
    assert antwort["abholer"]["zustand"] in knotenweg.ABHOLER_ZUSTAENDE
