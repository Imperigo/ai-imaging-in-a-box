"""Zwei Folgen aus der IFC-Leser-Messung vom 24.08.2026 — beide an der Naht.

Die HomeStation hat neun echte IFC durch beide Leser geschickt (`BEFUND_2026-08-24_IFC-
LESER.md`, 9 von 9 ok). Zwei Befunde daraus treffen unsere Seite:

1. **Ein reines Gebäude-IFC bringt gar kein Gelände mit.** Der eine `IfcSite` darin trägt
   keine Geometrie und taucht in der Ausgabe nicht auf. Die Maske meldet dann «kein Gelände
   erkannt» — ein **Fehlalarm**: Es fehlt nichts, es war nie welches da. Der Schalter dagegen
   existierte, war aber von aussen nicht erreichbar. Dieselbe Naht-Sache wie bei Brennweite
   und Geländestand.
2. **`Bestand_Kontext.ifc` (56 MB) kommt als EIN namenloses Bauteil** mit 502 002 Dreiecken
   an, bei beiden Lesern gleich. Eine Maske darüber trennt noch vom Himmel — aber nichts
   innerhalb der Geometrie.

Der dritte Befund derselben Messung — der Aufzug, den der fremde Klassifikator verliert —
steht in `test_ifc_glb_filter.py`. Er gehört dorthin, weil er den Runner betrifft, und der
darf nach Regel 2 **nicht** als `aiimaging`-Modul importiert werden. Mein erster Anlauf tat
genau das, und `test_prozessgrenze.py` hat ihn gefasst.
"""
from __future__ import annotations

import inspect

import pytest

from aiimaging import abholer, maske


# --------------------------------------------------------------------------------------
# 1 · Der Schalter erreicht die Naht
# --------------------------------------------------------------------------------------

def test_verarbeiter_nimmt_gelaende_erwartet_entgegen():
    """**Einstellbar ist ein Versprechen, das man an der Naht prüft, nicht am Modul.**

    Der Schalter stand seit jeher in `maske.bauwerksmaske`. Von einem Auftrag aus war er
    nicht erreichbar — genau wie die Brennweite, bis zwei fest verdrahtete 28.0 auffielen.
    """
    assert "gelaende_erwartet" in inspect.signature(abholer.verarbeiter).parameters


def test_der_schalter_kommt_bis_in_die_maske_an():
    """Nicht bloss entgegengenommen, sondern weitergereicht — das ist der Unterschied.

    Ein Parameter, den eine Funktion annimmt und nicht benutzt, ist ein stehengebliebenes
    Feld, und davon hatte dieses Projekt am 23.08. fünf auf einmal.
    """
    gesehen = {}

    def horcher(png, bericht, *, gelaende_erwartet=True, **kw):
        gesehen["wert"] = gelaende_erwartet
        raise maske.MaskeError("hier endet der Test — der Wert ist angekommen")

    echt = maske.bauwerksmaske_aus_lauf
    maske.bauwerksmaske_aus_lauf = horcher
    try:
        abholer._maske_bauen({"material_id_png": "x.png"}, gelaende_erwartet=False)
    finally:
        maske.bauwerksmaske_aus_lauf = echt

    assert gesehen["wert"] is False


def test_die_vorgabe_bleibt_gelaende_erwartet():
    """Wer nichts sagt, bekommt die strenge Lesart.

    Ein Schalter, der voreingestellt wegschaut, wäre schlimmer als keiner: Er machte aus
    jeder verfehlten Geländeregel stillschweigend eine gültige Maske.
    """
    assert inspect.signature(abholer.verarbeiter).parameters[
        "gelaende_erwartet"].default is True
    assert inspect.signature(maske.bauwerksmaske).parameters[
        "gelaende_erwartet"].default is True


def test_ohne_gelaende_ist_die_maske_eine_erklaerung_und_keine_pruefung():
    """Der Unterschied gehört in die Warnung, sonst liest sich beides gleich."""
    tabelle = [{"name": "Beton", "farbe_srgb_8bit": [10, 20, 30]},
               {"name": "Glas", "farbe_srgb_8bit": [40, 50, 60]}]
    farben = [(10, 20, 30)] * 40 + [(40, 50, 60)] * 40 + [(0, 0, 0)] * 20

    erklaert = maske.bauwerksmaske(farben, tabelle, gelaende_erwartet=False)
    streng = maske.bauwerksmaske(farben, tabelle, gelaende_erwartet=True)

    assert erklaert["maske"] is not None
    assert streng["maske"] is None, "ohne Erklärung bleibt die Maske ungemessen"
    assert any("unter dieser Erklärung" in w for w in erklaert["warnungen"])


def test_widerspricht_die_erklaerung_der_regel_wird_das_gesagt():
    """Beide Angaben können nicht zugleich stimmen, und keine wird stillschweigend gewinnen."""
    tabelle = [{"name": "Beton", "farbe_srgb_8bit": [10, 20, 30]},
               {"name": "IfcSite_Gelaende", "farbe_srgb_8bit": [40, 50, 60]}]
    farben = [(10, 20, 30)] * 50 + [(40, 50, 60)] * 50

    e = maske.bauwerksmaske(farben, tabelle, gelaende_erwartet=False)

    assert any("Eine der beiden Angaben stimmt nicht" in w for w in e["warnungen"])


# --------------------------------------------------------------------------------------
# 2 · Der Klumpen
# --------------------------------------------------------------------------------------

def _tabelle(n: int) -> list[dict]:
    return [{"name": f"Teil{i}", "farbe_srgb_8bit": [10 + i, 20, 30]} for i in range(n)]


def test_eine_tabelle_mit_einem_einzigen_eintrag_wird_gemeldet():
    """**Genauer als «unbrauchbar», und das ist der Punkt.**

    Vom Himmel trennt so eine Maske sehr wohl. Was nicht geht, ist der Entwurf gegen seine
    Nachbarschaft — und wer im Kontext rendert, misst dann den ganzen Klumpen und hält das
    Ergebnis für eine Aussage über sein Bauwerk.
    """
    e = maske.bauwerksmaske([(10, 20, 30)] * 60 + [(0, 0, 0)] * 40,
                            _tabelle(1), gelaende_erwartet=False)

    treffer = [w for w in e["warnungen"] if "EINEN Eintrag" in w]
    assert len(treffer) == 1
    assert "vom Himmel" in treffer[0]
    assert "502 002" in treffer[0], "die gemessene Datei gehoert dazu, nicht nur die Regel"
    assert e["maske"] is not None, (
        "die Maske ist nicht falsch — sie beantwortet eine engere Frage. Sie zu "
        "verwerfen waere Ueberbehauptung in die andere Richtung")


def test_gegenprobe_zwei_eintraege_erzeugen_die_warnung_nicht():
    """Ohne sie zeigte der Test darüber nur, dass die Warnung immer erscheint."""
    farben = [(10, 20, 30)] * 50 + [(11, 20, 30)] * 50

    e = maske.bauwerksmaske(farben, _tabelle(2), gelaende_erwartet=False)

    assert not [w for w in e["warnungen"] if "EINEN Eintrag" in w]

