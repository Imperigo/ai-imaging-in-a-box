"""Sieben Stile führen einen negativen Prompt, und keiner erreicht je ein Bild.

**Zwei Wirkungslosigkeiten übereinander, und beide sehen wie Sorgfalt aus.**

1. **Kein Weg.** Gesetzt wird der negative Prompt von `prompts.komponiere` — und
   `komponiere` liegt nicht auf dem Weg, den ein Auftrag der Oberfläche nimmt. Der bringt
   seinen Prompt roh mit. Dieselbe Fehlerart wie beim Bauteilwächter (23.08.2026), nur an
   einem anderen Feld.
2. **Und auch mit Weg keine Wirkung.** Unser Vorgabe-Backbone `z-image-turbo` läuft mit
   `fuehrung = 0.0`. Unterhalb von 1.0 ist die klassifikatorfreie Führung abgeschaltet —
   dann gibt es nichts, wovon sich ein negativer Prompt abziehen liesse.

**Diese Datei prüft nicht, dass es behoben ist.** Sie prüft, dass es **gemeldet** wird.
Den Prompt anzuschliessen ergäbe den schlechtesten Zustand von allen: Er stünde im
Protokoll, sähe nach Wirkung aus und änderte kein Bildpunkt. Ob er auf einem Backbone mit
Führung etwas verbessert, ist ungemessen — und eine ungemessene Änderung am Bild ist kein
Anschluss, sondern ein Eingriff.
"""
from __future__ import annotations

import pytest

from aiimaging import abholer, prompts, render
from aiimaging.render import FUEHRUNG_MINDESTENS


# --------------------------------------------------------------------------------------
# 1 · Der Befund selbst — gezählt, nicht vermutet
# --------------------------------------------------------------------------------------

def test_jeder_stil_fuehrt_einen_negativen_prompt():
    """Sieben von sieben. Wäre es einer, wäre es ein Einzelfall; so ist es ein Muster."""
    ohne = [s.slug for s in prompts.STILE.values() if not s.negativ]

    assert not ohne, f"diese Stile führen keinen negativen Prompt: {ohne}"
    assert len(prompts.STILE) >= 5, "die Aussage 'alle' braucht mehr als zwei Stile"


def test_auf_dem_vorgabe_backbone_koennte_er_gar_nicht_wirken():
    """**Der zweite Boden unter dem ersten.**

    Selbst wenn der Weg gebaut wäre, änderte sich kein Bildpunkt. Das ist der Grund, ihn
    NICHT zu bauen, bevor jemand gemessen hat, ob er auf einem Backbone mit Führung etwas
    verbessert.
    """
    e = render.negativ_wirksam(render.VORGABE_BACKBONE)

    assert e["wirksam"] is False
    assert e["fuehrung"] <= FUEHRUNG_MINDESTENS
    assert "WIRKUNGSLOS" in e["grund"]


def test_mit_ausdruecklicher_fuehrung_waere_er_wirksam():
    """Gegenprobe: Das Mass sagt nicht immer nein.

    Ohne sie zeigte der Test darüber nur, dass die Funktion nie `True` liefert.
    """
    e = render.negativ_wirksam(render.VORGABE_BACKBONE, fuehrung=3.5)

    assert e["wirksam"] is True


def test_eine_unbestimmte_fuehrung_heisst_unbekannt_und_nicht_nein():
    """**Nicht gemessen ist nicht dasselbe wie wirkungslos.**

    Ist für ein Backbone keine Führung bestimmt, greift die Vorgabe von `diffusers` — eine
    fremde Entscheidung. Was sie ist, wissen wir hier nicht, und `False` zu melden hiesse,
    etwas Ungemessenes zu behaupten.
    """
    e = render.negativ_wirksam("sdxl-juggernaut")

    assert e["wirksam"] is None
    assert "UNBEKANNT" in e["grund"]


def test_ein_unbekanntes_backbone_ergibt_ebenfalls_unbekannt():
    e = render.negativ_wirksam("gibt-es-nicht")

    assert e["wirksam"] is None
    assert "unbekannt" in e["grund"].lower()


# --------------------------------------------------------------------------------------
# 2 · Die Lage wird gemeldet — nur wenn es etwas zu melden gibt
# --------------------------------------------------------------------------------------

def test_die_lage_nennt_beide_gruende_zugleich():
    lage = abholer.negativ_lage("kosmo_standard", "z-image-turbo")

    assert lage["erreicht_render"] is False
    assert lage["waere_wirksam"] is False
    assert lage["negativ"] == prompts.hole_stil("kosmo_standard").negativ


def test_ohne_stil_gibt_es_nichts_zu_melden():
    """Sonst wäre es die nächste Dauerwarnung — die Lehre vom 23.08.2026 früh."""
    assert abholer.negativ_lage(None, "z-image-turbo") is None
    assert abholer.negativ_lage("", "z-image-turbo") is None


def test_ein_unbekannter_stil_meldet_hier_nichts():
    """Er ist anderswo ein Mangel; hier wäre er eine zweite, schlechtere Fehlermeldung."""
    assert abholer.negativ_lage("gibt-es-nicht", "z-image-turbo") is None


# --------------------------------------------------------------------------------------
# 3 · Und es erreicht den Menschen am Terminal
# --------------------------------------------------------------------------------------

def test_der_kurzbefund_nennt_es():
    befund = {"kameras": [],
              "negativ_lage": abholer.negativ_lage("kosmo_standard", "z-image-turbo")}

    treffer = [z for z in abholer.befund_kurz(befund) if "Negativ-Prompt" in z]

    assert len(treffer) == 1
    assert "kosmo_standard" in treffer[0]
    assert "ohnehin wirkungslos" in treffer[0], (
        "beide Gruende gehoeren in dieselbe Zeile — wer nur den ersten liest, baut den "
        "Weg und wundert sich, dass sich nichts aendert")


def test_gegenprobe_ohne_lage_steht_die_zeile_nicht_da():
    assert not [z for z in abholer.befund_kurz({"kameras": []}) if "Negativ-Prompt" in z]


def test_bei_unbekannter_wirkung_wird_der_zusatz_weggelassen():
    """Die Zeile behauptet nur, was feststeht.

    Ist die Führung unbestimmt, steht dort *nicht* «wäre ohnehin wirkungslos» — das wäre
    dieselbe Überbehauptung, gegen die dieses Modul gebaut ist.
    """
    lage = abholer.negativ_lage("kosmo_standard", "sdxl-juggernaut")
    zeile = [z for z in abholer.befund_kurz({"kameras": [], "negativ_lage": lage})
             if "Negativ-Prompt" in z][0]

    assert lage["waere_wirksam"] is None
    assert "ohnehin wirkungslos" not in zeile
