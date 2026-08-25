"""Eine Szene ohne Bauwerk darf keinen gesund aussehenden Kamerasatz ergeben.

**Der Anlass ist ein Demolauf, der nicht bei uns lag** (HomeStation, 24.08.2026, dritter
Lauf): Der Modell-Knoten meldete den ganzen Lauf «Szene: 0 Bauteile (GLB)», weil das aktive
Projekt den Stationswechsel nicht überlebte. Die Ursache liegt in der Oberfläche und ist als
`auf-40` weitergereicht.

**Was danach kommt, ist unsere Sache.** Aus einer leeren Szene entsteht eine Hüllbox ohne
Ausdehnung, und `kamerasatz` rechnet darauf weiter.

Der **leere** Fall warnte schon vorher — über den Füllgrad von 0,0 %. Der gefährlichere ist
der andere: Eine Hüllbox **ohne Höhe** — Gelände ohne Bauwerk, oder ein Bauwerk, dessen
Umwandlung stillschweigend nichts lieferte — ergab bis zum 24.08.2026 einen Kamerasatz, der
**völlig gesund aussieht**: Füllgrad 0,549, **keine einzige Warnung**. Die Kamera steht dann
sauber gerahmt vor einer Platte.

Das ist derselbe Fehlertyp wie überall diese Woche, nur eine Ebene früher: Es *sieht* nach
einer Messung aus.
"""
from __future__ import annotations

import pytest

from aiimaging import kameras
from aiimaging.kameras import LEERE_KANTE_M

NORMAL = [[0.0, 0.0, 0.0], [16.0, 10.0, 15.0]]
OHNE_HOEHE = [[0.0, 0.0, 0.0], [10.0, 10.0, 0.0]]
LEER = [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0]]


# --------------------------------------------------------------------------------------
# 1 · Die Prüfung selbst
# --------------------------------------------------------------------------------------

def test_eine_huellbox_ohne_hoehe_taugt_nicht():
    """**Der Fall, für den es die Prüfung gibt.**

    Er ist gefährlicher als die leere Szene, gerade weil er unauffällig ist.
    """
    e = kameras.huellbox_taugt(OHNE_HOEHE)

    assert e["taugt"] is False
    assert e["leere_achsen"] == ("Z",)
    assert "Gelände ohne Bauwerk" in e["grund"]
    assert "gesund aus" in e["grund"], (
        "der Grund muss sagen, WARUM man es sonst nicht merkt")


def test_eine_leere_szene_wird_als_solche_benannt():
    """Und nicht als «keine Höhe» — die Diagnose ist eine andere und der Handgriff auch."""
    e = kameras.huellbox_taugt(LEER)

    assert e["taugt"] is False
    assert e["leere_achsen"] == ("X", "Y", "Z")
    assert "Szene ist leer" in e["grund"]


def test_eine_gewoehnliche_huellbox_taugt():
    """Gegenprobe — ohne sie hiesse alles darüber nur, dass nie etwas taugt."""
    e = kameras.huellbox_taugt(NORMAL)

    assert e["taugt"] is True
    assert e["leere_achsen"] == ()
    assert e["grund"] == ""


def test_die_grenze_ist_absolut_und_nicht_anteilig():
    """**Eine anteilige Grenze liesse die lange flache Platte durchgehen.**

    200 m lang, 10 cm hoch: relativ zur grössten Kante ist das ein Tausendstel und fiele
    unter jede anteilige Schranke — es ist trotzdem kein Bauwerk.
    """
    platte = [[0.0, 0.0, 0.0], [200.0, 200.0, 0.05]]

    assert kameras.huellbox_taugt(platte)["taugt"] is False
    assert LEERE_KANTE_M == 0.10


def test_knapp_darueber_taugt_noch():
    """Die Schwelle trennt und lehnt nicht alles Flache ab."""
    knapp = [[0.0, 0.0, 0.0], [10.0, 10.0, LEERE_KANTE_M * 1.5]]

    assert kameras.huellbox_taugt(knapp)["taugt"] is True


@pytest.mark.parametrize("kaputt", [None, [[0, 0, 0]], [[0, 0], [1, 1]], "acht"])
def test_eine_unlesbare_huellbox_wird_abgewiesen(kaputt):
    with pytest.raises(ValueError, match="zwei Punkte"):
        kameras.huellbox_taugt(kaputt)


# --------------------------------------------------------------------------------------
# 2 · Und der Kamerasatz sagt es, statt gesund auszusehen
# --------------------------------------------------------------------------------------

def test_der_kamerasatz_meldet_die_untaugliche_huellbox_ganz_vorn():
    """**Ganz vorn, weil danach alle weiteren Zahlen Auskunft über eine leere Szene sind.**"""
    satz = kameras.kamerasatz(OHNE_HOEHE, kuerzel=["s"])

    assert satz["huellbox_taugt"] is False
    assert satz["leere_achsen"] == ("Z",)
    assert satz["warnungen"], "eine Warnung muss es geben"
    assert "keine HÖHE" in satz["warnungen"][0], (
        "und sie gehoert an die erste Stelle, nicht ans Ende einer Liste")


def test_der_zustand_bis_zum_24_08_2026_kehrt_nicht_zurueck():
    """Die Szene ohne Höhe sah vorher **makellos** aus. Genau das ist der Befund.

    Der Kamerasatz rechnet weiterhin — das ist richtig, denn ein Kamerastandpunkt um eine
    Platte ist wohldefiniert. Er darf nur nicht so tun, als wäre nichts.
    """
    satz = kameras.kamerasatz(OHNE_HOEHE, kuerzel=["s"])
    kamera = satz["kameras"][0]

    assert kamera["fuellgrad"] > 0.5, (
        "der Fuellgrad sieht weiterhin gesund aus — er ist nicht das Warnsignal, und "
        "genau darum braucht es das andere")
    assert satz["huellbox_taugt"] is False


def test_gegenprobe_eine_gewoehnliche_szene_bleibt_ohne_warnung():
    """Sonst wäre die Warnung die nächste Dauerwarnung."""
    satz = kameras.kamerasatz(NORMAL, kuerzel=["s"])

    assert satz["huellbox_taugt"] is True
    assert satz["leere_achsen"] == ()
    assert not [w for w in satz["warnungen"] if "Ausdehnung" in w or "HÖHE" in w]
