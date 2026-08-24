"""Der Rauschboden ist keine Konstante des Rauschens, sondern der Maskenlage.

**Der Befund kommt von der HomeStation** (`auf-vis-20260824-10`, 24.08.2026) und trifft
eine Zahl, die seit dem 21.08. als Konstante im Code steht.

`depth-anything-v2-small` hat ein **festes Ortsfeld**: Was es auf einem leeren Bild
ausgibt, ist zu **95,75 %** eine Funktion des Ortes — zirkelfrei gemessen, das Feld aus 15
Rauschbildern gewonnen und an 15 anderen geprüft. Dieselbe Rauschkarte mit derselben, nur
verschobenen Maske:

    96 px hoch    ρ −0,6249
    Mitte         ρ +0,5207   ← genau der Betrag unserer Konstanten
    96 px runter  ρ +0,6387
    96 px rechts  ρ +0,6513

Ausschlag 1,28 **mit Vorzeichenwechsel**. Zwei Kontrollen schliessen aus, dass es am Mass
liegt: Karte und Maske gemeinsam verschoben ändert nichts, und das mittlere Feld allein
sagt den Boden an allen 13 Lagen vorher (Korrelation 0,9993).

**Der Boden wurde bei uns immer schon je Lauf gemessen** — `_nullprobe` läuft je Kamera.
Er wurde nur nie **gelesen**. Das ist die fünfte tote Kante dieser Woche, und die teuerste:
Sie sass unter dem Tor.
"""
from __future__ import annotations

import pytest

from aiimaging import abholer, geometrie_qa as g
from aiimaging.geometrie_qa import PAAR_RHO_SCHWELLE


def _anker(**rhos) -> dict:
    return {art: {"rho": wert, "kante": None} for art, wert in rhos.items()}


# --------------------------------------------------------------------------------------
# 1 · Gegen den gemessenen Boden, nicht gegen die Konstante
# --------------------------------------------------------------------------------------

def test_der_abstand_wird_gegen_den_HOECHSTEN_nullanker_gemessen():
    """Ein echtes Bild muss den **besten** Nullanker schlagen, nicht den bequemsten.

    Sonst schlägt man den Boden, indem man sich den Anker aussucht — dieselbe Fehlerart
    wie ein Mittelwert über Urteile, der ein durchgefallenes Bild hinter zwei bestandenen
    verschwinden lässt.
    """
    e = g.rho_gegen_gemessenen_boden(0.91, _anker(rauschen=-0.52, grau=0.10, verlauf=-0.30))

    assert e["boden"] == pytest.approx(0.10)
    assert e["boden_art"] == "grau"
    assert e["abstand"] == pytest.approx(0.81)


def test_liegt_der_boden_ueber_der_schwelle_traegt_das_tor_nicht_mehr():
    """**Der Befund, für den es diese Funktion gibt.**

    Über verschiedene Maskenlagen schwankt der Abstand der Schwelle 0,80 zum Boden
    zwischen 0,15 und 1,42. Wird er negativ, lässt das Tor an dieser Lage Rauschen durch —
    und das ist ein Befund über die **Kameralage**, nicht über das Bild.
    """
    e = g.rho_gegen_gemessenen_boden(0.91, _anker(rauschen=0.85))

    assert e["schwelle_traegt"] is False
    assert any("Rauschen durch" in w for w in e["warnungen"])
    assert any("keine andere Schwelle" in w for w in e["warnungen"]), (
        "die Abhilfe gehoert dazu — sonst senkt jemand die Schwelle, und das waere "
        "genau die falsche Richtung")


def test_gegenprobe_ein_tiefer_boden_traegt():
    """Ohne sie zeigte der Test darüber nur, dass die Prüfung immer anschlägt."""
    e = g.rho_gegen_gemessenen_boden(0.91, _anker(rauschen=-0.52))

    assert e["schwelle_traegt"] is True
    assert e["warnungen"] == []


def test_ohne_nullprobe_steht_rho_gegen_nichts():
    """**Und die Konstante hilft dort ausdrücklich nicht.**

    Wer bei fehlender Nullprobe auf `RAUSCHBODEN_UEBER_MASKE` ausweicht, vergleicht mit
    der Zahl einer anderen Maskenlage — bei einem Ausschlag von 1,28 mit Vorzeichenwechsel
    ist das schlimmer als kein Vergleich.
    """
    e = g.rho_gegen_gemessenen_boden(0.91, None)

    assert e["boden"] is None
    assert e["abstand"] is None
    assert any("gegen NICHTS" in w for w in e["warnungen"])


def test_ohne_rho_ist_der_abstand_nicht_gemessen_und_nicht_null():
    e = g.rho_gegen_gemessenen_boden(None, _anker(rauschen=-0.52))

    assert e["boden"] == pytest.approx(-0.52), "der Boden steht trotzdem da"
    assert e["abstand"] is None
    assert any("NICHT GEMESSEN" in w for w in e["warnungen"])


def test_anker_ohne_rho_werden_uebergangen_und_nicht_als_null_gelesen():
    e = g.rho_gegen_gemessenen_boden(0.91, {"rauschen": {"rho": None, "kante": 0.2},
                                            "grau": {"rho": -0.4}})

    assert e["boden_art"] == "grau"


def test_die_konstante_traegt_ihre_eigene_widerlegung():
    """Wer `-0.5207` liest, muss im selben Blick sehen, dass sie für **eine Lage** gilt.

    Eine Konstante, deren Widerlegung nur im Sitzungsprotokoll steht, wird weiterbenutzt.
    """
    from pathlib import Path
    quelle = Path(g.__file__).read_text(encoding="utf-8")
    ende = quelle.index("RAUSCHBODEN_UEBER_MASKE = -0.5207")
    block = quelle[ende - 2600:ende]

    assert "Ortsfeld" in block
    assert "95,75" in block
    assert "Vorzeichenwechsel" in block


# --------------------------------------------------------------------------------------
# 2 · Und es erreicht den Menschen am Terminal
# --------------------------------------------------------------------------------------

def test_der_kurzbefund_nennt_die_kamera_deren_schwelle_nichts_mehr_trennt():
    befund = {"kameras": [
        {"kamera": "s", "bodenabstand": {"schwelle_traegt": False, "boden": 0.85}},
        {"kamera": "sSE", "bodenabstand": {"schwelle_traegt": True, "boden": -0.52}},
    ]}

    treffer = [z for z in abholer.befund_kurz(befund) if "SCHWELLE TRAEGT HIER NICHT" in z]

    assert len(treffer) == 1
    assert "s" in treffer[0] and "sSE" not in treffer[0]


def test_der_kurzbefund_nennt_auch_die_fehlende_nullprobe():
    """Zwei verschiedene Befunde, zwei verschiedene Zeilen.

    Eine Schwelle, die hier nichts mehr trennt, ist etwas anderes als gar kein Vergleich.
    """
    befund = {"kameras": [
        {"kamera": "nNW", "bodenabstand": {"schwelle_traegt": None, "boden": None}}]}

    zeilen = abholer.befund_kurz(befund)

    assert [z for z in zeilen if "Kein gemessener Rauschboden" in z]
    assert not [z for z in zeilen if "SCHWELLE TRAEGT HIER NICHT" in z]


def test_gegenprobe_ein_tragender_boden_erzeugt_keine_zeile():
    befund = {"kameras": [
        {"kamera": "s", "bodenabstand": {"schwelle_traegt": True, "boden": -0.52}}]}

    assert abholer.befund_kurz(befund) == ()


def test_die_schwelle_ist_dieselbe_wie_im_paartest():
    """Eine Zahl, die an zwei Stellen steht, ist an einer davon bereits falsch."""
    e = g.rho_gegen_gemessenen_boden(0.9, _anker(rauschen=-0.5))

    assert e["schwelle"] == PAAR_RHO_SCHWELLE
