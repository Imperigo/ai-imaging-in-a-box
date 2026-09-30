"""Die Schrittzahl nach der Modellkarte — Befund `auf-20260930-208` (Sitzung 73 §27).

qwen-image-2.1 rechnete mit 20 Schritten; die Karte bei den Gewichten nennt 40 in allen drei
Beispielen. Führung und Negativprompt nennt sie nicht — dort bleibt es ohne Regler.
"""
from __future__ import annotations

import time
from pathlib import Path

import pytest

from aiimaging import backbone, render

import test_homeworker as th
from test_homeworker import GLB_BERICHT, Tiefenattrappe, hw, satz, treue_ist_karte


def test_qwen_21_hat_die_40_schritte_der_karte_und_keinen_regler():
    e = backbone.hole("qwen-image-2.1")
    assert e.schritte_vorgabe == 40 and "Z. 67, 90, 105" in e.schritte_beleg
    assert e.fuehrung_regler is None, "die Karte nennt keine Führung — nicht raten"
    assert backbone.schritte_fuer("qwen-image-2.1") == 40


@pytest.mark.parametrize("name", [None, "", "gibt-es-nicht", "z-image-turbo"])
def test_ohne_beleg_bleibt_es_bei_20(name):
    assert backbone.schritte_fuer(name) == backbone.SCHRITTE_STANDARD == 20


def test_nur_belegte_eintraege_tragen_eine_schrittzahl():
    for name, e in backbone.BACKBONES.items():
        if e.schritte_vorgabe is not None:
            assert e.schritte_beleg, f"{name}: Schrittzahl ohne Beleg"


from test_homeworker_modus_und_umriss import _bild_mit_bau  # noqa: E402

#: Dieselben Fixtures wie in ``test_homeworker`` — übernommen, nicht nachgebaut.
aus = th.aus
bericht = th.bericht


class _Merkt:
    def __init__(self):
        self.schritte = None

    def __call__(self, parameter):
        self.schritte = parameter["schritte"]
        _bild_mit_bau(Path(parameter["ausgabe_png"]))
        return {"bild_png": parameter["ausgabe_png"]}


@pytest.mark.parametrize("params, erwartet", [
    ({"backbone": "qwen-image-2.1"}, 40),
    ({"backbone": "qwen-image-2.1", "schritte": 12}, 12),   # die Bestellung gewinnt
    ({}, 20),                                               # Vorgabemodell, ohne Beleg
])
def test_der_homeworker_nimmt_die_karte_wo_die_bestellung_schweigt(bericht, aus, params,
                                                                   erwartet):
    merkt = _Merkt()
    hw._render_und_qa(satz(), bericht, GLB_BERICHT, aus, {"prompt": "Wohnhaus", **params},
                      time.monotonic(), _render_modell=merkt,
                      _tiefen_modell=Tiefenattrappe(treue_ist_karte(bericht)))
    assert merkt.schritte == erwartet


def test_der_abholer_fragt_das_register():
    """Der Abholer baut den Auftrag in einer inneren Funktion; geprüft wird die Stelle."""
    quelle = Path(render.__file__).with_name("abholer.py").read_text(encoding="utf-8")
    assert "schritte=render.backbone.schritte_fuer(" in quelle
