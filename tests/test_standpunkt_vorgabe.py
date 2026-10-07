"""Ohne bestellten Standpunkt rechnet «Anwenden» frontal von Süden — wie der Abholer.

**Der Befund** (HomeStation, ``auf-20261007-261``, 07.10.2026): Die Vorführmappe führt keine
Kamera. Auf dem Weg über die Mappe (:func:`aiimaging.arbeitsgang.rechne`) fiel das bis in
den Runner durch, und der stellte seinen Rückfall — diagonal von vorn-oben, nicht
komponiert. Das Haus füllte 16,7 % des Bildes, jede Prüfung fiel durch (0,02–0,19).
Dieselbe Mappe mit ``kamera="s"`` bestand mit 0,91. Der Abholer rechnet ohne mitgesandte
Kamera seit dem 23.08.2026 komponierte Richtungen, die erste davon ``s``.

Diese Proben halten fest: ohne Angabe ``s`` und ein Satz dazu im Ergebnis; jede bestellte
Angabe bleibt unberührt; die Vorgabe ist dieselbe wie die erste Richtung des Abholers.
"""
from __future__ import annotations

import json
import struct

import pytest

from aiimaging import abholer, arbeitsgang
from aiimaging.kette import ART_MULTIPASS
from test_arbeitsgang import Werkbank


class MerkendeWerkbank(Werkbank):
    """Die Werkbank aus ``test_arbeitsgang``, die sich die Multipass-Knoten merkt."""

    def __init__(self, **kw) -> None:
        super().__init__(**kw)
        self.multipass_params: list[dict] = []

    def tabelle(self) -> dict:
        return {**super().tabelle(), ART_MULTIPASS: self._multipass}

    def _multipass(self, *, knoten, eingaben, out_dir):
        self.multipass_params.append(dict(knoten.params))
        return self.multipass(knoten=knoten, eingaben=eingaben, out_dir=out_dir)


@pytest.fixture
def glb(tmp_path):
    js = json.dumps({"asset": {"version": "2.0", "generator": "Testfixture"}}).encode()
    js += b" " * (-len(js) % 4)
    block = struct.pack("<II", len(js), 0x4E4F534A) + js
    pfad = tmp_path / "quelle" / "haus.glb"
    pfad.parent.mkdir(parents=True, exist_ok=True)
    pfad.write_bytes(struct.pack("<4sII", b"glTF", 2, 12 + len(block)) + block)
    return pfad


def _mappe(tmp_path, glb, **einstellungen):
    wurzel = tmp_path / "projekt"
    arbeitsgang.lege_an(wurzel, glb, name="Probehaus",
                        einstellungen={"prompt": "Abendlicht", "up_axis": "Y",
                                       **einstellungen})
    return wurzel


def test_die_vorgabe_ist_die_erste_richtung_des_abholers():
    # Zwei Wege derselben Software sollen ohne Angabe dasselbe Haus gleich zeigen.
    assert arbeitsgang.STANDPUNKT_VORGABE == abholer.AUTO_RICHTUNGEN[0] == "s"


def test_jede_art_standpunkt_zaehlt_als_bestellt():
    assert set(arbeitsgang.STANDPUNKT_ANGABEN) == {"kamera", "auge", "blick_auf",
                                                   "innenraum"}


def test_ohne_standpunkt_wird_frontal_von_sueden_gerechnet(tmp_path, glb):
    bank = MerkendeWerkbank()
    ergebnis = arbeitsgang.rechne(_mappe(tmp_path, glb), ausfuehrer=bank.tabelle(),
                                  cache=None)
    assert [p.get("kamera") for p in bank.multipass_params] == ["s"]
    vorgabe = ergebnis["standpunkt_vorgabe"]
    assert vorgabe["kamera"] == "s"
    assert "Kein Standpunkt bestellt" in vorgabe["satz"]
    assert "Süden" in vorgabe["satz"]


def test_ohne_angabe_ist_der_knoten_derselbe_wie_mit_kamera_s(tmp_path, glb):
    # Die Vorgabe steht im Knoten und damit im Hash: Ein altes Bild ohne Kamera gilt
    # nicht als Treffer, und «nichts bestellt» rechnet genau dasselbe wie «s bestellt».
    ohne, mit = MerkendeWerkbank(), MerkendeWerkbank()
    arbeitsgang.rechne(_mappe(tmp_path / "a", glb), ausfuehrer=ohne.tabelle(), cache=None)
    arbeitsgang.rechne(_mappe(tmp_path / "b", glb, kamera="s"), ausfuehrer=mit.tabelle(),
                       cache=None)
    assert ohne.multipass_params == mit.multipass_params


def test_alle_varianten_einer_reihe_tragen_die_vorgabe(tmp_path, glb):
    bank = MerkendeWerkbank()
    ergebnis = arbeitsgang.rechne(_mappe(tmp_path, glb), ausfuehrer=bank.tabelle(),
                                  cache=None, varianten=3)
    assert [p.get("kamera") for p in bank.multipass_params] == ["s", "s", "s"]
    assert ergebnis["standpunkt_vorgabe"]["kamera"] == "s"


def test_eine_kamera_der_mappe_bleibt(tmp_path, glb):
    bank = MerkendeWerkbank()
    ergebnis = arbeitsgang.rechne(_mappe(tmp_path, glb, kamera="nNW"),
                                  ausfuehrer=bank.tabelle(), cache=None)
    assert [p.get("kamera") for p in bank.multipass_params] == ["nNW"]
    assert ergebnis["standpunkt_vorgabe"] is None


def test_eine_kamera_im_aufruf_bleibt(tmp_path, glb):
    bank = MerkendeWerkbank()
    ergebnis = arbeitsgang.rechne(_mappe(tmp_path, glb), ausfuehrer=bank.tabelle(),
                                  cache=None, kamera="sSE")
    assert [p.get("kamera") for p in bank.multipass_params] == ["sSE"]
    assert ergebnis["standpunkt_vorgabe"] is None


def test_ein_standpunkt_von_hand_bekommt_keine_kamera_dazu(tmp_path, glb):
    # Sonst wiese die Kette den Lauf als «Standpunkt zweimal bestellt» ab.
    bank = MerkendeWerkbank()
    ergebnis = arbeitsgang.rechne(_mappe(tmp_path, glb), ausfuehrer=bank.tabelle(),
                                  cache=None, auge=[4.0, -20.0, 1.6],
                                  blick_auf=[4.0, 2.5, 1.6])
    assert ergebnis["lauf"]["status"] == "ok"
    assert bank.multipass_params[0].get("kamera") is None
    assert bank.multipass_params[0]["auge"] == [4.0, -20.0, 1.6]
    assert ergebnis["standpunkt_vorgabe"] is None


def test_ein_entwurf_ohne_standpunkt_bekommt_die_vorgabe_auch(tmp_path, glb):
    bank = MerkendeWerkbank()
    ergebnis = arbeitsgang.rechne(_mappe(tmp_path, glb), ausfuehrer=bank.tabelle(),
                                  cache=None, entwurf=True)
    assert bank.multipass_params[0]["kamera"] == "s"
    assert ergebnis["standpunkt_vorgabe"]["kamera"] == "s"
