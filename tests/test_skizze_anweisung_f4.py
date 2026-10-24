"""Befund F4 (Demolauf 24.10.2026, Mac 0.3.54 / Heim-PC 0.3.55): «Bild aus Skizze» ohne Anweisung.

«Bild aus Skizze» scheiterte dreimal mit «prompt fehlt oder ist leer (None)». Am Code bestätigt:

1. Das iPad legt die Skizze mit der Bemerkung «gewünschter Name: Variante A» ab (aus der Kopfzeile
   «SKIZZE · VARIANTE A»; ein Feld für eine Anweisung gibt es am iPad nicht).
2. Die Knotenansicht hielt das für eine Bemerkung und schickte den Prompt des Render-Knotens nicht
   als Anweisung mit (Rückfall 96c griff nur bei leerer Bemerkung).
3. Am Heim-PC baute der Skizzenlauf erst den Graphen der Mappe — und deren Einstellungen trugen
   keinen Prompt (er steht am Prompt-Knoten). ``kette.baue_kette`` wies mit genau dem Satz des
   Demolaufs ab. Wäre er durchgekommen, hätte das Bildmodell «gewünschter Name: Variante A» als
   Anweisung bekommen.

Seither: Der gewünschte Name ist keine Anweisung (``projekt.bemerkung_ohne_name``); ohne Bemerkung
gilt der Prompt der Bestellung, auch am Heim-PC (``abholer.anweisung_der_skizze``); der Grundgraph
bekommt den Prompt der Bestellung, wenn die Mappe keinen hat; fehlt alles, weist ``knotenweg.lege_an``
schon beim Annehmen mit Satz ab (400), nicht nach dem Lauf.

Regel 3: synthetische Mappe aus ein paar Bytes (Fixture aus ``test_skizze_fuehrt``).
"""
from __future__ import annotations

from pathlib import Path

import pytest

from aiimaging import abholer, arbeitsgang, knotenweg, projekt

from test_skizze_fuehrt import (KENNUNG, _abholen, _bestellen_und_freigeben, _ergebnis, _glb,
                                _Modell, _szene, mappe)  # noqa: F401 (Fixture)

NUR_NAME = "gewünschter Name: Variante A"
PROMPT = "a wooden facade at dusk"


def _setze(wurzel, *, bemerkung, prompt_der_mappe=True) -> None:
    p = projekt.oeffne(wurzel)["projekt"]
    if not prompt_der_mappe:
        p["einstellungen"].pop("prompt", None)
    eintrag = [e for e in p["skizzen"] if e["skizze"] == "skizze-a.png"][-1]
    eintrag["bemerkung"] = bemerkung
    projekt.speichere(p, wurzel)


def _szene_mit(prompt: str, **skizze) -> dict:
    s = _szene(name="skizze-a.png", **skizze)
    s["style"]["prompt"] = prompt
    return s


# ======================================================================================
# Die Bibliothek: der Name ist keine Anweisung
# ======================================================================================

@pytest.mark.parametrize("bemerkung, ohne, name", [
    (NUR_NAME, "", "Variante A"),
    ("ein Vordach · gewünschter Name: Variante B", "ein Vordach", "Variante B"),
    ("ein Vordach", "ein Vordach", ""),
    ("   ", "", ""),
    (None, "", ""),
])
def test_bemerkung_ohne_name_und_der_name(bemerkung, ohne, name):
    assert projekt.bemerkung_ohne_name(bemerkung) == ohne
    assert projekt.gewuenschter_name(bemerkung) == name


def test_die_liste_des_knotens_meldet_keine_bemerkung_und_den_namen_als_titel(mappe):
    _setze(mappe, bemerkung=NUR_NAME)
    (s,) = knotenweg.skizzen_der_mappe(projekt.oeffne(mappe)["projekt"])
    assert s["bemerkung"] is None
    assert s["titel"] == "Variante A"


def test_auf_der_seite_wird_der_name_nicht_zur_anweisung(mappe):
    _setze(mappe, bemerkung=NUR_NAME)
    with pytest.raises(arbeitsgang.ArbeitsgangError, match="nur der gewünschte Name «Variante A»"):
        arbeitsgang.rechne_skizze(mappe, "skizze-a.png")


# ======================================================================================
# Der Demolauf über den Produktweg Annehmen → Freigeben → Abholen
# ======================================================================================

def test_der_demolauf_mappe_ohne_prompt_bemerkung_nur_name_prompt_der_bestellung(tmp_path, mappe):
    """Genau der Fall vom 24.10.2026 — vorher «prompt fehlt oder ist leer (None)»."""
    _setze(mappe, bemerkung=NUR_NAME, prompt_der_mappe=False)
    ordner = _bestellen_und_freigeben(tmp_path / "ablage", mappe, _szene_mit(PROMPT))
    modell = _Modell()
    antwort = _abholen(ordner, modell)
    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort["grund"]
    # Die Anweisung ist der Prompt der Bestellung, nicht der Name.
    assert modell.auftraege[-1]["prompt"] == PROMPT
    befund = abholer.lies_befund(ordner)
    assert befund["skizze"]["anweisung_aus"] == "prompt"
    assert befund["skizze"]["gewuenschter_name"] == "Variante A"
    assert any("Anweisung aus dem Prompt am Render-Knoten" in h
               for h in _ergebnis(ordner)["qa"]["verdict"]["hinweise"])


def test_mappe_mit_prompt_bemerkung_nur_name_der_name_geht_nicht_ans_modell(tmp_path, mappe):
    _setze(mappe, bemerkung=NUR_NAME)
    ordner = _bestellen_und_freigeben(tmp_path / "ablage", mappe, _szene_mit(PROMPT))
    modell = _Modell()
    assert _abholen(ordner, modell)["tat"] == abholer.TAT_VERARBEITET
    assert modell.auftraege[-1]["prompt"] == PROMPT
    assert "gewünschter Name" not in modell.auftraege[-1]["prompt"]


def test_echte_bemerkung_mit_namen_gilt_ohne_den_namen(tmp_path, mappe):
    _setze(mappe, bemerkung="ein Vordach · gewünschter Name: Variante B")
    ordner = _bestellen_und_freigeben(tmp_path / "ablage", mappe, _szene_mit(PROMPT))
    modell = _Modell()
    assert _abholen(ordner, modell)["tat"] == abholer.TAT_VERARBEITET
    # Ergebnis 352 S3: die Bemerkung geht übersetzt ans Bildmodell, wie ein Prompt.
    assert modell.auftraege[-1]["prompt"] == "a canopy"
    assert abholer.lies_befund(ordner)["skizze"]["anweisung_aus"] == "bemerkung"


def test_die_anweisung_der_bestellung_geht_vor(tmp_path, mappe):
    _setze(mappe, bemerkung=NUR_NAME, prompt_der_mappe=False)
    ordner = _bestellen_und_freigeben(tmp_path / "ablage", mappe,
                                      _szene_mit(PROMPT, anweisung="a wooden balcony"))
    modell = _Modell()
    assert _abholen(ordner, modell)["tat"] == abholer.TAT_VERARBEITET
    assert modell.auftraege[-1]["prompt"] == "a wooden balcony"


# ======================================================================================
# Ohne alles: schon beim Annehmen abgewiesen, mit Satz
# ======================================================================================

def test_ohne_anweisung_und_ohne_prompt_weist_schon_das_annehmen_ab(tmp_path, mappe):
    _setze(mappe, bemerkung=NUR_NAME)
    ablage = tmp_path / "ablage"
    with pytest.raises(knotenweg.KnotenwegError) as fehler:
        knotenweg.lege_an(ablage, _szene_mit(""), _glb(mappe), "model.glb", kennung=KENNUNG,
                          mappe=Path(mappe).name, mappe_pfad=mappe)
    assert fehler.value.code == 400
    assert str(fehler.value) == knotenweg.SATZ_SKIZZE_OHNE_ANWEISUNG
    assert "Prompt-Knoten" in str(fehler.value)
    assert "None" not in str(fehler.value)
    assert not (ablage / KENNUNG).exists()


def test_der_satz_ist_auf_beiden_seiten_derselbe():
    assert abholer.SATZ_SKIZZE_OHNE_ANWEISUNG == knotenweg.SATZ_SKIZZE_OHNE_ANWEISUNG
    with pytest.raises(abholer.AbholerError, match="am Render-Knoten steht kein Prompt"):
        abholer.anweisung_der_skizze({"name": "a.png"}, {"bemerkung": NUR_NAME}, "  ")


def test_ein_von_hand_gelegter_auftrag_ohne_alles_sagt_es_beim_abholen(tmp_path, mappe):
    """Zweite Sicherung: ein Auftrag, der am Annehmen vorbei in die Ablage kam."""
    _setze(mappe, bemerkung="ein Vordach")
    ordner = _bestellen_und_freigeben(tmp_path / "ablage", mappe, _szene_mit(""))
    _setze(mappe, bemerkung=NUR_NAME)
    antwort = _abholen(ordner, _Modell())
    assert antwort["tat"] != abholer.TAT_VERARBEITET
    assert abholer.SATZ_SKIZZE_OHNE_ANWEISUNG in antwort["grund"]
    assert "prompt fehlt oder ist leer" not in antwort["grund"]


def test_eine_deutsche_bemerkung_geht_uebersetzt_ans_bildmodell():
    """Ergebnis 352 S3: «Fassade heller» ging wörtlich ans Bildmodell — grafische Fassade mit Schrift."""
    text, aus = abholer.anweisung_der_skizze(
        {}, {"bemerkung": "Fassade heller · gewünschter Name: Variante A"}, None)
    assert aus == "bemerkung"
    assert "Fassade" not in text and "facade" in text and "Variante" not in text
