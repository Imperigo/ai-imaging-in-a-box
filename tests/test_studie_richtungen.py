"""Die Auswertung der Richtungsstudie — ohne Blender.

Geprüft wird, was das Werkzeug **rechnet**: die Einteilung in frontal und diagonal und die
Zählung der guten Fälle unter der Schwelle. Der Renderteil braucht Blender und steht unter
`docs/RICHTUNGEN_2026-08-28.md`.

*Der Anlass für diese Datei ist ein eigener Fehler:* Die Messung lief am 28.08.2026
zuerst aus einem Skript unter `build/` — also ausserhalb des Repos. Ihre Zahlen standen
danach in zwei Aufträgen, die andere ausführen sollen, **und niemand hätte sie nachbauen
können.** Das Skript ist deshalb ein Werkzeug geworden.
"""

import importlib.util
from pathlib import Path

import pytest

from aiimaging import geometrie_qa


def _studie():
    pfad = Path(__file__).resolve().parents[1] / "tools" / "studie_richtungen.py"
    spec = importlib.util.spec_from_file_location("werkzeug_studie_richtungen", pfad)
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul


def _zeile(kamera, gruppe, gut_werte, schlecht_werte):
    werte = {f"g{i}": (True, v) for i, v in enumerate(gut_werte)}
    werte.update({f"b{i}": (False, v) for i, v in enumerate(schlecht_werte)})
    return {"kamera": kamera, "gruppe": gruppe, "werte": werte}


# ======================================================================================
# Die Einteilung
# ======================================================================================

def test_genau_die_vier_himmelsrichtungen_gelten_als_frontal():
    """**Vier und nicht mehr.** Wächst die Liste still, verschiebt sich jede Zahl der
    Auswertung, ohne dass es auffällt."""
    st = _studie()
    assert set(st.FRONTAL) == {"n", "e", "s", "w"}
    assert not set(st.FRONTAL) & set(st.DIAGONAL)
    for k in st.FRONTAL:
        assert st.gruppe(k) == "frontal"
    for k in st.DIAGONAL:
        assert st.gruppe(k) == "diagonal"


def test_die_richtungen_gibt_es_wirklich():
    """Ein Tippfehler ergäbe eine Richtung, die `kamerasatz` abweist — erst im Render."""
    from aiimaging import kameras
    st = _studie()
    for k in st.FRONTAL + st.DIAGONAL:
        assert k in kameras.RICHTUNGSFOLGE, k


def test_aus_jedem_quadranten_eine_diagonale():
    """Vier diagonale aus vier Ecken — sonst verglichen wir eine Bauwerksseite mit sich."""
    st = _studie()
    assert len(st.DIAGONAL) == len(st.FRONTAL) == 4
    assert len({k[0] for k in st.DIAGONAL}) == 4, "vier verschiedene Hauptrichtungen"


# ======================================================================================
# Die Auswertung
# ======================================================================================

def test_gute_faelle_unter_der_schwelle_werden_je_gruppe_gezaehlt():
    st = _studie()
    zeilen = [_zeile("n", "frontal", [0.70, 0.95], [0.1]),
              _zeile("sSE", "diagonal", [0.93, 0.99], [0.1])]
    satz = st.auswertung(zeilen, 0.80)
    assert satz["frontal"]["gute_unter_schwelle"] == 1
    assert satz["frontal"]["gute_gesamt"] == 2
    assert satz["diagonal"]["gute_unter_schwelle"] == 0


def test_die_luecke_ist_der_abstand_zwischen_den_gruppen_je_richtung():
    st = _studie()
    zeilen = [_zeile("n", "frontal", [0.90, 0.95], [0.30, 0.10])]
    satz = st.auswertung(zeilen, 0.80)
    assert satz["frontal"]["kleinste_luecke"] == pytest.approx(0.60)
    assert satz["frontal"]["groesste_luecke"] == pytest.approx(0.60)


def test_eine_ueberlappung_gibt_eine_negative_luecke():
    """Nicht auf null abgeschnitten: «knapp getrennt» und «überlappt» sind zwei Aussagen."""
    st = _studie()
    satz = st.auswertung([_zeile("n", "frontal", [0.40], [0.60])], 0.80)
    assert satz["frontal"]["kleinste_luecke"] == pytest.approx(-0.20)


def test_eine_richtung_ohne_messbare_faelle_bringt_die_rechnung_nicht_zu_fall():
    """`None` heisst nicht messbar — und darf weder als 0 noch als Fehler durchgehen."""
    st = _studie()
    satz = st.auswertung([_zeile("n", "frontal", [None], [None])], 0.80)
    assert satz["frontal"]["gute_gesamt"] == 0
    assert satz["frontal"]["kleinste_luecke"] is None


def test_eine_leere_gruppe_meldet_None_statt_einer_zahl():
    st = _studie()
    satz = st.auswertung([_zeile("n", "frontal", [0.9], [0.1])], 0.80)
    assert satz["diagonal"]["gute_gesamt"] == 0
    assert satz["diagonal"]["kleinste_luecke"] is None


def test_die_schwelle_ist_ein_argument_und_keine_konstante():
    """Sonst hinge die Auswertung an einer Zahl, die gerade kalibriert wird."""
    st = _studie()
    zeilen = [_zeile("n", "frontal", [0.70, 0.85], [0.1])]
    assert st.auswertung(zeilen, 0.80)["frontal"]["gute_unter_schwelle"] == 1
    assert st.auswertung(zeilen, 0.90)["frontal"]["gute_unter_schwelle"] == 2
    assert st.auswertung(zeilen, 0.60)["frontal"]["gute_unter_schwelle"] == 0


def test_die_vorgabeschwelle_ist_die_des_paarurteils():
    """Der Befund gilt gegen **die** Schwelle, gegen die im Betrieb geprüft wird."""
    st = _studie()
    zeilen = [_zeile("n", "frontal", [geometrie_qa.PAAR_RHO_SCHWELLE - 0.01], [0.1])]
    satz = st.auswertung(zeilen, geometrie_qa.PAAR_RHO_SCHWELLE)
    assert satz["frontal"]["gute_unter_schwelle"] == 1
