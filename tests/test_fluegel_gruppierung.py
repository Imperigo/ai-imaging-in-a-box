"""A0301 «Flügel bleiben ein Haus»: die Gruppierung der Grundrisse am synthetischen Satz.

Ursache, belegt am 10.11.2026 (und als Nebenbefund schon in Sitzung 74, Ergebnis 363): Steht eine Anlage auf
einer grossen Geländeplatte, hängt jedes Teil über diese Platte mit jedem zusammen. Der Haufen wuchs über
``BAU_MAX_FLAECHE_M2`` und wurde nach *gleichem Grundriss* zerlegt. Geschosse übereinander haben denselben
Grundriss und blieben zusammen; Flügel haben verschiedene Grundrisse und fielen auseinander, ebenso Teile, die
nur über Bodenplatte oder Verbindungsgang zusammenhängen.

Gemessen gegen den Stand vor dem Auftrag (``fab/visbox/int-0376``): 36 von 66 richtig (54,5 %), 2 falsche
Verschmelzungen in 26 Gegenfällen. Ziel: 66 von 66, 0 falsche Verschmelzungen.
"""
from __future__ import annotations

import pytest

from aiimaging import umfeld
from fluegel_satz import beurteile, faelle, miss

FAELLE = faelle()


def test_der_satz_ist_gross_genug_und_deckt_die_verlangten_formen():
    """Der Auftrag verlangt mindestens 30 Fälle: L-, U-, H- und Kammform, Bodenplatte, Verbindungsgang und die
    Gegenfälle (zwei Häuser mit kleinem Abstand, Haus neben Nebenbau)."""
    namen = [f["name"] for f in FAELLE]
    assert len(FAELLE) >= 30
    for form in ("L-", "U-", "H-", "Kamm-"):
        assert sum(n.startswith(form) for n in namen) >= 6, form
    assert sum(f["gruppe"] == "bodenplatte" for f in FAELLE) >= 4
    assert sum(f["gruppe"] == "gang" for f in FAELLE) >= 2
    assert sum(n.startswith("zwei-haeuser") for n in namen) >= 6
    assert sum(n.startswith("haus-nebenbau") for n in namen) >= 4
    assert sum(f["gegenfall"] for f in FAELLE) >= 10


def test_der_satz_ist_wiederholbar_und_ohne_fremde_daten():
    """Regel 3: Der Satz entsteht aus Zahlen im Erzeuger, zweimal erzeugt ist er gleich."""
    assert faelle() == FAELLE
    for f in FAELLE:
        assert len(f["boxen"]) == len(f["haus"]) >= 2
        for lo, hi in f["boxen"]:
            assert all(a < b for a, b in zip(lo, hi)), f["name"]


@pytest.mark.parametrize("fall", FAELLE, ids=[f["name"] for f in FAELLE])
def test_fall_ist_richtig_gruppiert(fall):
    urteil = beurteile(fall, umfeld.grundriss_cluster(fall["boxen"]))
    assert urteil["verschmelzungen"] == 0, urteil["grund"]
    assert urteil["richtig"], urteil["grund"]


def test_zielfunktion_alle_richtig_und_keine_falsche_verschmelzung():
    """Die Zielfunktion des Auftrags in einer Zahl: 100 % richtig, 0 falsche Verschmelzungen."""
    m = miss(umfeld.grundriss_cluster)
    assert m["verschmelzungen_gegenfaelle"] == 0 and m["verschmelzungen"] == 0, m["falsch"]
    assert m["richtig"] == m["faelle"], m["falsch"]


def _haeuser(fall):
    """Die Hausgruppen eines Falls als Menge von Boxen (ohne Gelände und Belag) — vergleichbar zwischen
    «frei» und «auf der Geländeplatte», wo dieselben Boxen andere Nummern tragen."""
    aus = set()
    for c in umfeld.grundriss_cluster(fall["boxen"]):
        teile = [i for i in c["teile"] if fall["haus"][i] is not None]
        if teile:
            aus.add(frozenset(fall["boxen"][i] for i in teile))
    return aus


PAARE = [(f, g) for f in FAELLE for g in FAELLE
         if f["name"].endswith("-frei") and g["name"] == f["name"][:-len("frei")] + "gelaende"]


@pytest.mark.parametrize("frei,gelaende", PAARE, ids=[f["name"][:-len("-frei")] for f, _ in PAARE])
def test_die_gelaendeplatte_aendert_die_haeuser_nicht(frei, gelaende):
    """Der Kern des Befunds als Eigenschaft: Ob eine Geländeplatte unter der Anlage liegt, ändert nicht, welche
    Teile ein Haus sind. Vor dem Auftrag zerfiel jeder Flügelbau, sobald die Platte dazukam."""
    assert _haeuser(frei) == _haeuser(gelaende)
    boden = [c for c in umfeld.grundriss_cluster(gelaende["boxen"]) if c["art"] == "boden"]
    assert len(boden) == 1 and boden[0]["teile"] == [0]


def test_die_reihenfolge_der_teile_aendert_die_gruppen_nicht():
    """Dieselben Boxen rückwärts: dieselben Gruppen (als Mengen von Boxen), dieselbe Art."""
    for fall in FAELLE:
        vor = {(frozenset(fall["boxen"][i] for i in c["teile"]), c["art"])
               for c in umfeld.grundriss_cluster(fall["boxen"])}
        rueck_boxen = fall["boxen"][::-1]
        rueck = {(frozenset(rueck_boxen[i] for i in c["teile"]), c["art"])
                 for c in umfeld.grundriss_cluster(rueck_boxen)}
        assert vor == rueck, fall["name"]


def test_eine_kette_knapp_ueberlappender_platten_bleibt_zerlegt():
    """Was Ergebnis 359 festlegt, bleibt: Platten, die nur als Kette über die Flächengrenze wachsen und nichts
    tragen, werden weiter einzeln beurteilt und nicht zu einem Boden verschmolzen."""
    kette = [((119.5 * k, 0.0, 0.0), (119.5 * k + 120.0, 100.0, 2.0)) for k in range(4)]
    c = umfeld.grundriss_cluster(kette)
    assert sorted(x["teile"] for x in c) == [[0], [1], [2], [3]]
    assert all(x["art"] == "bau" for x in c)


def test_ein_sockel_bindet_ein_hofbelag_nicht():
    """Die Grenze zwischen «Teile auf gemeinsamer Bodenplatte» und «zwei Häuser auf einem Belag»: Eine flache
    Platte, auf der getrennte Teile stehen, bindet sie nur, wenn die Teile sie mindestens zur Hälfte decken."""
    teile = [((1.0, 1.0, 0.3), (11.0, 9.0, 8.0)), ((14.0, 1.0, 0.3), (24.0, 9.0, 8.0))]
    sockel = ((0.0, 0.0, 0.0), (25.0, 10.0, 0.3))                         # 160 von 250 m² gedeckt
    belag = ((-10.0, -10.0, 0.0), (40.0, 22.0, 0.3))                      # 160 von 1600 m² gedeckt
    ein = umfeld.grundriss_cluster([sockel] + teile)
    assert [x["teile"] for x in ein] == [[0, 1, 2]] and ein[0]["bau"]
    zwei = umfeld.grundriss_cluster([belag] + teile)
    assert sorted(x["teile"] for x in zwei) == [[0], [1], [2]]
    assert [x["art"] for x in zwei if x["teile"] == [0]] == ["belag"]
    # Ein hoher Sockelbau (über FLACH_MAX_M) mit zwei Türmen darauf ist ein Bau, wie viel sie auch decken.
    podium = ((-10.0, -10.0, 0.0), (40.0, 22.0, 4.5))
    hoch = umfeld.grundriss_cluster([podium] + [((a[0], a[1], 4.5), (b[0], b[1], 30.0)) for a, b in teile])
    assert [x["teile"] for x in hoch] == [[0, 1, 2]]
