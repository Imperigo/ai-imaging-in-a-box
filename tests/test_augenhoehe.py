"""Augenhöhe heisst 1.60–1.70 m — und bis zum 03.09.2026 sagte das keine Zahl.

**Der Anlass.** Bestellt waren drei augenhohe Perspektiven. Der Auto-Kamera-Knoten leitet
seit Lauf 16 unverändert genau **zwei** Standpunkte ab («Eingang» und «Übersicht»); ein
dritter, «Innenraum», entsteht gar nicht. Von den zwei gelieferten stand einer bei
1.60 m, der andere bei 54.79 m über Gelände. Der zweite wurde richtig abgelehnt — 54 m
sind keine Augenhöhe —, und damit blieb **eine** von drei bestellten Perspektiven übrig.

Gemeldet hat das niemand, weil niemand danach fragte: Der Dachriegel
(``abholer._kamera_ueber_dach``) fängt die Kamera, die zu hoch steht, um «Dach und Fuss im
Bild» zu fragen. Ob ein Standpunkt die **Bestellung** erfüllt, ist eine andere Frage, und
sie war in keinem Lauf gestellt.

**Warum die Ursache hier nicht repariert wird.** Sie liegt nicht in diesem Repo. Gemessen
am 03.09.2026 hat sie zwei Schichten, beide in KosmoOrbit: Der Bestellweg filtert
«Innenraum» unbedingt heraus (``istUeberDiesenWegBestellbar``), und noch davor liest der
IFC-Einleser ``IfcSpace`` gar nicht ein — ohne Zonen kann ``hauptnutzraum()`` keinen
Innenraum finden. Beides geht als Auftrag hinüber. Was hierher gehört, ist die Zahl, die
den Fehlbetrag sichtbar macht.

Alle Werte sind synthetisch oder aus den Berichten der Läufe 16/17 abgeschrieben (Zahlen,
keine Daten — Regel 3).
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aiimaging import abholer, kameras  # noqa: E402


def _kamera(auge_z: float, gelaende_z: float = 0.0, name: str | None = None):
    k = {"auge": [10.0, 10.0, auge_z], "gelaende_z": gelaende_z}
    if name:
        k["name"] = name
    return k


def test_das_band_ist_ein_band_und_kein_punkt():
    """Eine Kamera bei 1.62 m ist augenhoch, ohne 1.70 zu sein. Eine Prüfung auf
    Gleichheit mit ``AUGENHOEHE_M`` würde sie verwerfen."""
    assert kameras.AUGENHOEHE_BAND_M == (1.60, kameras.AUGENHOEHE_M)
    for z in (1.60, 1.62, 1.65, 1.70):
        assert kameras.augenhoehe_befund(_kamera(z))["augenhoch"] is True, z


def test_knapp_daneben_ist_daneben():
    """Sonst wäre das Band kein Band, sondern eine Geste."""
    assert kameras.augenhoehe_befund(_kamera(1.59))["augenhoch"] is False
    assert kameras.augenhoehe_befund(_kamera(1.71))["augenhoch"] is False


def test_die_uebersicht_aus_lauf_17_ist_keine_augenhoehe():
    """Die echten Zahlen des Laufs: ``auge[2] = 54.35``, ``gelaende_z = −0.437``.
    Der Abholer meldete daraus 54.787 m; dieselbe Rechnung muss hier herauskommen."""
    befund = kameras.augenhoehe_befund(_kamera(54.35, -0.437))
    assert befund["kamerahoehe_m"] == pytest_approx(54.787)
    assert befund["augenhoch"] is False
    assert "zu hoch" in befund["grund"]


def test_gerechnet_wird_ueber_gelaende_und_nicht_ueber_der_nulllinie():
    """**Der Kellerfall.** Ein Standpunkt im Untergeschoss steht über der Nulllinie bei
    −1.6 m und wäre formal «zu tief» — im Raum steht er auf Augenhöhe."""
    assert kameras.augenhoehe_befund(_kamera(-1.65, -3.30))["augenhoch"] is True
    assert kameras.augenhoehe_befund(_kamera(-1.65, 0.0))["augenhoch"] is False


def test_fehlende_zahlen_sind_NICHT_GEMESSEN_und_nicht_durchgefallen():
    """``False`` wäre ein Urteil über etwas, das niemand angesehen hat."""
    for kaputt in ({}, {"auge": [1, 2]}, {"auge": [1, 2, 3]}, {"gelaende_z": 0.0},
                   {"auge": None, "gelaende_z": 0.0}):
        befund = kameras.augenhoehe_befund(kaputt)
        assert befund["gemessen"] is False
        assert befund["augenhoch"] is None
        assert "NICHT GEMESSEN" in befund["grund"]


# ── Die Zählung, die den Fehlbetrag sichtbar macht ────────────────────────────────────

def test_lauf_17_lieferte_eine_von_drei_bestellten_perspektiven():
    """**Der Fall, um den es geht**, mit den Zahlen der beiden Läufe."""
    gelieferte = [_kamera(1.60, 0.0, "Eingang"), _kamera(54.35, -0.437, "Übersicht")]
    zaehlung = kameras.augenhohe_standpunkte(gelieferte, bestellt=3)

    assert zaehlung["n_gelieferte"] == 2
    assert zaehlung["n_augenhoch"] == 1
    assert zaehlung["fehlbetrag"] == 2
    assert zaehlung["warnungen"], "ein Fehlbetrag ohne Meldung ist kein Befund"
    assert "es fehlen 2" in zaehlung["warnungen"][0]
    assert [b["kamera"] for b in zaehlung["je_kamera"]] == ["Eingang", "Übersicht"]


def test_ein_abgelehnter_standpunkt_zaehlt_nicht_als_gelieferter():
    """Wer nur die Bilder zählt, zählt die Ablehnung als Erfolg mit — genau das ist in
    Lauf 16 und 17 passiert."""
    zaehlung = kameras.augenhohe_standpunkte(
        [_kamera(54.35, -0.437, "Übersicht")], bestellt=3)
    assert zaehlung["n_augenhoch"] == 0
    assert zaehlung["fehlbetrag"] == 3


def test_ohne_bestellung_wird_gezaehlt_und_nicht_geurteilt():
    """Wieviele Perspektiven bestellt sind, gehört zum Auftrag und nicht zur Bibliothek.
    Eine Lücke gegen eine ungenannte Zahl wäre keine."""
    zaehlung = kameras.augenhohe_standpunkte([_kamera(1.65), _kamera(30.0)])
    assert zaehlung["n_augenhoch"] == 1
    assert zaehlung["bestellt"] is None
    assert zaehlung["fehlbetrag"] is None
    assert zaehlung["warnungen"] == []


def test_drei_augenhohe_erfuellen_die_bestellung_und_melden_nichts():
    """Die Gegenprobe: Wäre die Meldung immer da, verdeckte sie die echten Fälle."""
    zaehlung = kameras.augenhohe_standpunkte(
        [_kamera(1.60), _kamera(1.65), _kamera(1.70)], bestellt=3)
    assert zaehlung["fehlbetrag"] == 0
    assert zaehlung["warnungen"] == []


# ── Und die Naht: steht die Zahl auch im Lauf? ────────────────────────────────────────

def test_der_abholer_fuehrt_die_augenhoehe_im_urteil_mit():
    """Eine Bibliotheksfunktion, die im Lauf nicht vorkommt, hat den Lauf nicht gemessen."""
    bericht = {"kamera": _kamera(1.60, 0.0, "Eingang")}
    urteil = abholer._komposition_vor_dem_render(bericht)
    assert urteil["augenhoehe"]["augenhoch"] is True

    bericht = {"kamera": dict(_kamera(54.35, -0.437, "Übersicht"),
                              gebaeudehoehe_m=30.437)}
    urteil = abholer._komposition_vor_dem_render(bericht)
    assert urteil["abbruch"] is True, "der Dachriegel greift weiterhin"
    assert urteil["augenhoehe"]["augenhoch"] is False, (
        "und die Augenhoehe steht daneben — beide Fragen, nicht nur eine")


def pytest_approx(wert, toleranz=1e-3):
    class _Nah:
        def __eq__(self, anderer):
            return abs(anderer - wert) < toleranz

        def __repr__(self):
            return f"~{wert}"
    return _Nah()
