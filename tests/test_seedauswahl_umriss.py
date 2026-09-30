"""Die Startwert-Auswahl nach der Umrisstreue — Owner-Entscheid «1», Regel erfüllt in auf-190.

Bestätigungsreihe (36 Bilder, Bauwerksrahmung, Auge blind): Die Umrisstreue setzte in 5 von 5
Fällen ein richtig stehendes Bild auf Platz 1, ρ in 3. Vorbehalt: mit «unklar» als richtig
gleichauf. Mit ``SEEDAUSWAHL_NACH = "rho"`` gilt die alte Auswahl.
"""
from __future__ import annotations

import pytest

from aiimaging import abholer, bildschreiben

B, H = 64, 48
HG = 1.0e10


def _soll():
    return [10.0 if (20 <= x < 44 and 12 <= y < 36) else HG
            for y in range(H) for x in range(B)]


def _grau(pfad):
    bildschreiben.schreibe_farb_png(pfad, [(128, 128, 128)] * (B * H), B, H)


def _passend(pfad):
    bildschreiben.schreibe_farb_png(
        pfad, [(220, 220, 220) if (20 <= x < 44 and 12 <= y < 36) else (40, 40, 40)
               for y in range(H) for x in range(B)], B, H)


def _lauf(tmp_path, *, soll):
    """Seed 0: graues Bild, aber hohes rho. Seed 1: passender Umriss, niedriges rho."""
    rho = {0: 0.95, 1: 0.10}

    def rendere_seed(seed, ziel):
        (_grau if seed == 0 else _passend)(ziel)
        return {"status": "ok", "bild_png": ziel}

    def messe(png):
        seed = 0 if png.endswith("seed0.png") else 1
        return {"rho_maske": {"gerichtet": rho[seed]}, "paarurteil": None}

    return abholer._bester_seed([0, 1], tmp_path, "sSE", rendere_seed, messe,
                                maske_da=True, soll=soll, breite=B, hoehe=H)


def test_die_umrisstreue_waehlt_das_bild_mit_dem_passenden_umriss(tmp_path):
    _, _, auswahl = _lauf(tmp_path, soll=_soll())
    assert abholer.SEEDAUSWAHL_NACH == "umriss"
    assert auswahl["gewaehlt"] == 1 and auswahl["nach"] == "umriss"
    assert "UMRISSTREUE" in auswahl["grund"] and auswahl["vorsprung"] is None
    assert all("abhebung" in k and "gerichtet" in k for k in auswahl["kandidaten"])


def test_ohne_soll_gilt_die_alte_auswahl_nach_rho(tmp_path):
    _, _, auswahl = _lauf(tmp_path, soll=None)
    assert auswahl["gewaehlt"] == 0 and auswahl["nach"] == "rho"


def test_der_schalter_stellt_rho_wieder_her(tmp_path, monkeypatch):
    monkeypatch.setattr(abholer, "SEEDAUSWAHL_NACH", "rho")
    _, _, auswahl = _lauf(tmp_path, soll=_soll())
    assert auswahl["gewaehlt"] == 0
