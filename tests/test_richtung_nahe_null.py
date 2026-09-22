"""«Vorne und hinten vertauscht» erst, wenn die Umkehrung deutlich ist.

**Befund vom 22.09.2026 (auf-20260922-137):** Die Meldung «vorne und hinten sind
vertauscht» löste bei ``polaritaet * rho < 0`` aus, ganz ohne Mindestbetrag. Am Gerät
gemessen: ρ = +0,037 über 848 Punkte bei Polarität −1. Die Zufallsstreuung einer
Rangkorrelation ohne Zusammenhang liegt dort bei ``1/sqrt(n-1)`` ≈ 0,034 — der Wert war
von null nicht zu unterscheiden. Das heisst «kein Zusammenhang», nicht «umgekehrt».

Geprüft wird an beiden Stellen, die die Meldung erzeugen: am Tor
(:func:`geometrie_qa.geometrie_gate`, das über ``geometrie_score`` läuft) und am Maskenweg
(:func:`geometrie_qa.rho_ueber_maske`). Die Karten sind synthetisch und hier erzeugt.
"""

from __future__ import annotations

import pytest

from aiimaging import geometrie_qa

#: Am Gerät waren es 848 gemeinsame Punkte; hier 849 — die Grenze liegt dabei bei 0,0686
#: statt 0,0687, am Befund ändert das nichts.
N_GERAET = 849

#: Hintergrund, der in beiden Karten gleich liegt — damit die Silhouette nicht das ganze
#: Bild ist und keine fremde Warnung («randlos») mitläuft.
HINTERGRUND = 1.0e10
N_HINTERGRUND = 151


def ist_karte(n: int, schritt: int, steigung: float) -> list[float]:
    """Eine Ist-Karte mit einstellbarer Ordnung gegen die Soll-Karte ``0, 1, …, n-1``.

    ``steigung * k`` trägt die Soll-Ordnung, ``(k * schritt) % n`` ist ein Sägezahn ohne
    sie. Mit ``steigung = 0`` bleibt nur der Sägezahn: ρ nahe null, je nach ``schritt``
    etwas darüber oder darunter. Alles ganzzahlig und ohne Zufall — der Test sieht bei
    jedem Lauf dieselben Zahlen.
    """
    return [steigung * k + float((k * schritt) % n) for k in range(n)]


def karten(n: int, schritt: int, steigung: float):
    """Soll, Ist und Maske über ``n`` Geometriepunkte plus gemeinsamen Hintergrund."""
    soll = [float(k) + 1.0 for k in range(n)] + [HINTERGRUND] * N_HINTERGRUND
    ist = [w + 1.0 for w in ist_karte(n, schritt, steigung)] + [HINTERGRUND] * N_HINTERGRUND
    maske = [True] * n + [False] * N_HINTERGRUND
    return soll, ist, maske


def _vertauscht(warnungen) -> list[str]:
    return [w for w in warnungen if "vertauscht" in w or "falsche Richtung" in w]


def _kein_zusammenhang(warnungen) -> list[str]:
    return [w for w in warnungen if "Kein messbarer Zusammenhang" in w]


# --------------------------------------------------------------------------------------
# Der Fall vom Gerät: ρ ≈ +0,035 bei Polarität −1 über 849 Punkte
# --------------------------------------------------------------------------------------

@pytest.fixture
def geraetefall():
    soll, ist, maske = karten(N_GERAET, schritt=49, steigung=0.0)
    return soll, ist, maske


def test_das_tor_meldet_bei_rho_nahe_null_nicht_vertauscht(geraetefall):
    """Das Tor sagt «kein messbarer Zusammenhang» statt «vertauscht» — und urteilt gleich.

    Die Meldung ist ein Hinweis, kein Urteil: Der Score schneidet jedes negative
    ``polaritaet * rho`` auf 0 ab, das Bild fällt wie vorher durch. Genau das wird
    mitgeprüft, damit die neue Schwelle kein Urteil still verschiebt.
    """
    soll, ist, _ = geraetefall
    urteil = geometrie_qa.geometrie_gate(
        soll, ist, polaritaet=geometrie_qa.POLARITAET_DISPARITAET)

    assert urteil["n_gemeinsam"] == N_GERAET
    assert 0.03 < urteil["spearman"] < 0.04, "Vorbedingung: der Gerätefall, nachgestellt"
    assert not _vertauscht(urteil["warnungen"]), urteil["warnungen"]
    treffer = _kein_zusammenhang(urteil["warnungen"])
    assert treffer, urteil["warnungen"]
    assert "Richtung ist nicht bestimmbar" in treffer[0]
    # Das Urteil bleibt, wie es war.
    assert urteil["score"] == 0.0
    assert urteil["bestanden"] is False


def test_der_maskenweg_meldet_bei_rho_nahe_null_nicht_vertauscht(geraetefall):
    """Derselbe Fall im Maskenweg: ``gerichtet`` bleibt gemessen, der Hinweis wird ehrlich."""
    soll, ist, maske = geraetefall
    ergebnis = geometrie_qa.rho_ueber_maske(
        soll, ist, maske, polaritaet=geometrie_qa.POLARITAET_DISPARITAET)

    assert ergebnis["n_maske"] == N_GERAET
    assert 0.03 < ergebnis["rho"] < 0.04, "Vorbedingung: der Gerätefall, nachgestellt"
    assert ergebnis["gerichtet"] == pytest.approx(-ergebnis["rho"]), \
        "der gerichtete Wert wird nicht angetastet"
    assert not _vertauscht(ergebnis["warnungen"]), ergebnis["warnungen"]
    treffer = _kein_zusammenhang(ergebnis["warnungen"])
    assert treffer, ergebnis["warnungen"]
    assert "Richtung ist nicht bestimmbar" in treffer[0]


# --------------------------------------------------------------------------------------
# Die Gegenprobe: eine deutliche Umkehrung bleibt «vertauscht»
# --------------------------------------------------------------------------------------

@pytest.fixture
def deutlich_verkehrt():
    """ρ ≈ +0,90 bei Polarität −1: gewertet −0,90, weit jenseits jeder Zufallsstreuung."""
    return karten(N_GERAET, schritt=49, steigung=2.0)


def test_das_tor_meldet_eine_deutliche_umkehrung_weiter_als_vertauscht(deutlich_verkehrt):
    soll, ist, _ = deutlich_verkehrt
    urteil = geometrie_qa.geometrie_gate(
        soll, ist, polaritaet=geometrie_qa.POLARITAET_DISPARITAET)

    assert urteil["spearman"] > 0.85, "Vorbedingung"
    assert _vertauscht(urteil["warnungen"]), urteil["warnungen"]
    assert not _kein_zusammenhang(urteil["warnungen"])
    assert urteil["bestanden"] is False


def test_der_maskenweg_meldet_eine_deutliche_umkehrung_weiter_als_vertauscht(
        deutlich_verkehrt):
    soll, ist, maske = deutlich_verkehrt
    ergebnis = geometrie_qa.rho_ueber_maske(
        soll, ist, maske, polaritaet=geometrie_qa.POLARITAET_DISPARITAET)

    assert ergebnis["rho"] > 0.85, "Vorbedingung"
    assert _vertauscht(ergebnis["warnungen"]), ergebnis["warnungen"]
    assert not _kein_zusammenhang(ergebnis["warnungen"])


# --------------------------------------------------------------------------------------
# Die Grenze hängt an der Punktzahl — eine feste Zahl wäre dieselbe Falle, nur verschoben
# --------------------------------------------------------------------------------------

@pytest.mark.parametrize("weg", ["tor", "maske"])
def test_dasselbe_rho_ist_bei_vielen_punkten_eine_richtung_und_bei_wenigen_nicht(weg):
    """ρ ≈ −0,11 bei Polarität +1: über 849 Punkte deutlich (Grenze −0,069), über 101
    Punkte nicht (Grenze −0,200). Eine feste Schwelle könnte nur einen der beiden Fälle
    richtig nennen."""
    def pruefen(n, schritt):
        soll, ist, maske = karten(n, schritt=schritt, steigung=0.0)
        if weg == "tor":
            e = geometrie_qa.geometrie_gate(soll, ist,
                                            polaritaet=geometrie_qa.POLARITAET_TIEFE)
            rho = e["spearman"]
        else:
            e = geometrie_qa.rho_ueber_maske(soll, ist, maske,
                                             polaritaet=geometrie_qa.POLARITAET_TIEFE)
            rho = e["rho"]
        assert -0.13 < rho < -0.09, f"Vorbedingung bei n={n}: rho={rho}"
        return e["warnungen"]

    viele = pruefen(N_GERAET, schritt=106)
    wenige = pruefen(101, schritt=20)

    assert _vertauscht(viele), viele
    assert not _vertauscht(wenige), wenige
    assert _kein_zusammenhang(wenige), wenige


def test_die_grenze_ist_zwei_zufallsstreuungen():
    """Die Zahl selbst, wie im Befund begründet: 2/sqrt(n-1)."""
    assert geometrie_qa.richtungsgrenze(849) == pytest.approx(2.0 / 848 ** 0.5)
    assert geometrie_qa.richtungsgrenze(849) > 0.037, \
        "der Gerätewert +0,037 muss unter der Grenze liegen"
    assert geometrie_qa.richtungsgrenze(1) == float("inf"), \
        "ohne zwei Punkte gibt es keine Richtung"
