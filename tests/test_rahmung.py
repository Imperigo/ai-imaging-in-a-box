"""Die Kamera rahmt die Szene, gemessen wird das Bauwerk — das ist der Bruch.

**Der Befund kommt von der HomeStation** (24.08.2026, `auf-13`/`auf-35`) und widerlegt eine
Behauptung, die dieses Projekt eine Woche lang mitgeführt hat: `SCHWELLE_GEOMETRIE = 0.65`
sei arithmetisch unerreichbar.

**Sie ist es nicht. Sie ist es bei der Rahmung, die `cameras: auto` erzeugt** — und das ist
etwas ganz anderes, weil es sich beheben lässt, ohne eine Schwelle zu senken.

Ein Quader 15,36 × 10,36 × 6,0 m auf einer Platte mit zehnfacher Grundfläche, ein Startwert,
eine Ansicht, vier Abstände:

    anteil_maske 0.0193 → geom_iou 0.000183   (auto, 90,6 m)
    anteil_maske 0.0565 → geom_iou 0.0        (55,0 m)
    anteil_maske 0.1565 → geom_iou 0.00144    (35,1 m)
    anteil_maske 0.3051 → geom_iou 0.9323     (26,6 m) — Score 0.9599, BESTANDEN

Der Sprung zwischen den letzten beiden ist **Faktor 647**: keine Rampe, sondern eine
Schwelle in einer Grösse, die niemand als Schwelle angelegt hat.

Die Ursache liegt eine Ebene tiefer: `kameras.py` rechnet aus der Hüllbox der **ganzen
Szene**. Steht das Bauwerk auf einer zehnfach grossen Platte, rahmt die Kamera Platte plus
Bauwerk — und die Maske deckt nur das Bauwerk.
"""
from __future__ import annotations

import pytest

from aiimaging import abholer, geometrie_qa as g
from aiimaging.geometrie_qa import (
    ANTEIL_MASKE_GEMESSEN_REICHT,
    ANTEIL_MASKE_GEMESSEN_ZU_KLEIN,
    RAHMUNG_GEMESSEN,
)


# --------------------------------------------------------------------------------------
# 1 · Die Frage ist vor dem Renderlauf beantwortbar
# --------------------------------------------------------------------------------------

def test_die_rahmung_von_auto_kann_gemessen_nicht_bestehen():
    """**Der Kern.** Ein Lauf, der nicht bestehen *kann*, ist verlorene Rechenzeit — und
    ein irreführendes Urteil obendrein.
    """
    e = g.torchance(0.0193)

    assert e["lage"] == "zu_klein"
    assert "kein Urteil über das Bild" in e["begruendung"]
    assert "keine gesenkte Schwelle" in e["begruendung"], (
        "die Abhilfe gehoert in dieselbe Zeile, sonst senkt jemand die Schwelle")


def test_bei_siebzig_prozent_bildbreite_reicht_es():
    """Gegenprobe — ohne sie hiesse der Test darüber nur, dass nie etwas besteht."""
    e = g.torchance(0.3051)

    assert e["lage"] == "reicht"
    assert "über das Bild sagt das nichts" in e["begruendung"], (
        "'die Rahmung steht nicht im Weg' ist nicht dasselbe wie 'das Bild ist gut'")


def test_dazwischen_wird_NICHT_interpoliert():
    """**Faktor 647 zwischen zwei Punkten — eine Gerade hindurch wäre eine Erfindung.**

    Dieselbe Zurückhaltung wie bei `minimum_abschlag` jenseits seiner Tabelle: Wo nichts
    gemessen ist, steht `None` und nicht eine gerechnete Zahl.
    """
    e = g.torchance(0.22)

    assert e["lage"] is None
    assert "NICHT BEANTWORTET" in e["begruendung"]
    assert "Erfindung" in e["begruendung"]


def test_ohne_maskenanteil_ist_die_frage_nicht_beantwortet_und_nicht_verneint():
    e = g.torchance(None)

    assert e["lage"] is None
    assert "nicht verneint" in e["begruendung"]


def test_die_tabelle_ist_eine_stichprobe_und_sagt_das():
    """Eine Szene, ein Startwert, eine Ansicht — vier Punkte.

    Die Zahlen stehen als Messung da und nicht als Kurve. Wer daraus ein Gesetz macht,
    wiederholt den Fehler, den dieses Projekt diese Woche dreimal korrigiert hat.
    """
    assert len(RAHMUNG_GEMESSEN) == 4
    anteile = [a for a, _ in RAHMUNG_GEMESSEN]
    assert anteile == sorted(anteile), "die Tabelle ist nach Maskenanteil geordnet"
    assert ANTEIL_MASKE_GEMESSEN_ZU_KLEIN in anteile
    assert ANTEIL_MASKE_GEMESSEN_REICHT in anteile, (
        "beide Grenzen sind GEMESSENE Punkte und keine gewaehlten Werte dazwischen")


def test_der_sprung_ist_wirklich_ein_sprung_und_keine_rampe():
    """Der Beleg für die Zurückhaltung darüber — aus den Zahlen selbst."""
    nach_anteil = dict(RAHMUNG_GEMESSEN)
    klein = nach_anteil[ANTEIL_MASKE_GEMESSEN_ZU_KLEIN]
    gross = nach_anteil[ANTEIL_MASKE_GEMESSEN_REICHT]

    assert gross / klein > 500, "Faktor 647 — das ist keine Rampe"


def test_die_schwelle_ist_damit_NICHT_unerreichbar():
    """**Die Behauptung, die eine Woche lang mitgeführt wurde, ist widerlegt.**

    Bei 0.3051 entstand ein Score von 0.9599 — weit über `SCHWELLE_GEOMETRIE`.
    """
    _, bestes_iou = RAHMUNG_GEMESSEN[-1]

    assert bestes_iou > g.SCHWELLE_GEOMETRIE, (
        "wenn schon das gemessene geom_iou unter der Schwelle laege, waere die "
        "Unerreichbarkeit nicht widerlegt")


# --------------------------------------------------------------------------------------
# 2 · Und es erreicht den Menschen am Terminal — weit oben
# --------------------------------------------------------------------------------------

def test_der_kurzbefund_meldet_die_zu_weite_rahmung():
    """Diese Zeile steht bewusst weit oben.

    Konnte der Lauf nicht bestehen, sind alle folgenden Zahlen Auskunft über die Rahmung
    und nicht über das Bild.
    """
    befund = {"kameras": [{"kamera": "s", "torchance": g.torchance(0.0193)},
                          {"kamera": "sSE", "torchance": g.torchance(0.31)}]}

    zeilen = abholer.befund_kurz(befund)
    treffer = [z for z in zeilen if "RAHMUNG ZU WEIT" in z]

    assert len(treffer) == 1
    assert "s" in treffer[0] and "sSE" not in treffer[0]
    assert zeilen[0] == treffer[0], "sie gehoert nach oben, nicht ans Ende"


def test_gegenprobe_eine_gute_rahmung_erzeugt_keine_zeile():
    befund = {"kameras": [{"kamera": "s", "torchance": g.torchance(0.31)}]}

    assert abholer.befund_kurz(befund) == ()


def test_eine_unbeantwortete_rahmung_erzeugt_ebenfalls_keine_zeile():
    """Zwischen den Messpunkten wird nichts behauptet — auch keine Warnung.

    Eine Warnung bei jedem Zwischenwert wäre die nächste Dauerwarnung.
    """
    befund = {"kameras": [{"kamera": "s", "torchance": g.torchance(0.22)}]}

    assert not [z for z in abholer.befund_kurz(befund) if "RAHMUNG" in z]
