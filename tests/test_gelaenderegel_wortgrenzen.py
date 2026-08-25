"""Die Geländeregel sperrte Szenen mit ausgeschriebenem Namen aus — und schaltete damit
eine Owner-Vorgabe still ab.

**Gemessen** (HomeStation, `auf-vis-20260824-12`, 24.08.2026): `GELAENDE_MUSTER` vergleicht
mit `fnmatch` gegen den **ganzen** Namen, und nur `ifcsite*` trägt einen Platzhalter. Ein
Objekt namens `Gelaende_Hang` fiel damit durch die Regel — die Maske kam als `None` zurück,
und `_bester_seed` rendert dann **einen** Startwert statt drei.

**Auf zwei von drei Auftragsgeometrien griff die Drei-Seed-Vorgabe deshalb gar nicht.** Das
ist ein Owner-Entscheid vom 22.08., der seither still abgeschaltet war — und das Ergebnis
hiess fälschlich «ein Startwert genügt». *Eine Vorgabe, die von einem Namen abhängt, ist
keine Vorgabe.*

**Die Lösung ist nicht `*gelaende*`**, und daran hängt der ganze Test: Ein blosses Präfix
trifft `Geländer_Balkon` — ein Geländer ist kein Gelände. Dieselbe Falle wie beim
Bauteilwächter, wo «Betonung» bei «Beton» anschlug. Verglichen wird darum auf
**Wortgrenzen**.
"""
from __future__ import annotations

import pytest

from aiimaging import maske
from aiimaging.maske import GELAENDE_MUSTER, GELAENDE_WOERTER


# --------------------------------------------------------------------------------------
# 1 · Der gemeldete Fall greift jetzt
# --------------------------------------------------------------------------------------

@pytest.mark.parametrize("name", ["Gelaende_Hang", "Gelaende_vorn", "Terrain-Nord",
                                  "gelände", "Site_01", "terrain"])
def test_ein_ausgeschriebener_gelaendename_gilt_als_gelaende(name):
    assert maske.ist_gelaende(name) is True


@pytest.mark.parametrize("name", ["IfcSite_1a2b3c", "boden_platte"])
def test_die_alten_muster_gelten_unveraendert_weiter(name):
    """Die Ergänzung darf nichts wegnehmen — sonst tauscht man einen Ausfall gegen einen
    anderen."""
    assert maske.ist_gelaende(name) is True


# --------------------------------------------------------------------------------------
# 2 · Und die Falle daneben schnappt NICHT zu
# --------------------------------------------------------------------------------------

@pytest.mark.parametrize("name,warum", [
    ("Geländer_Balkon", "ein Geländer ist kein Gelände — die Falle, an der ein Praefix scheitert"),
    ("Gelaender_Treppe", "dasselbe ohne Umlaut"),
    ("Bodenplatte des 2. OG", "ein Geschossboden ist kein Gelände"),
    ("Beton_C25", "ein Material"),
    ("Terrassentuer", "faengt mit 'terra' an und ist eine Tuer"),
])
def test_was_nur_so_AUSSIEHT_wird_nicht_zu_gelaende(name, warum):
    assert maske.ist_gelaende(name) is False, warum


def test_ein_kompositum_ohne_trenner_wird_NICHT_erfasst():
    """**Eine bewusste Grenze, und sie gehört genannt.**

    `Baugelaende` trägt das Wort, aber ohne Trennzeichen — die Regel erkennt es nicht.
    Das ist der Preis dafür, dass `Geländer` nicht erfasst wird; beides zugleich ginge nur
    mit einer Wortliste der deutschen Sprache. Wer solche Namen vergibt, schreibt sie mit
    Trennzeichen oder trägt das Muster nach.
    """
    assert maske.ist_gelaende("Baugelaende") is False


# --------------------------------------------------------------------------------------
# 3 · Die Regel bleibt befragbar und übersteuerbar
# --------------------------------------------------------------------------------------

def test_eine_eigene_regel_bekommt_keine_stille_zugabe():
    """Wer eine **eigene** Musterliste übergibt, bekommt genau sie.

    Sonst wäre die Ergänzung eine versteckte Nebenwirkung — und ein Aufrufer, der die
    Regel bewusst eng zieht, bekäme sie heimlich weit.
    """
    assert maske.ist_gelaende("Gelaende_Hang", ("nur_dies",)) is False
    assert maske.ist_gelaende("Gelaende_Hang", GELAENDE_MUSTER) is True


def test_die_wortliste_enthaelt_nichts_mehrdeutiges():
    """`boden` gehört **nicht** hinein — sonst wird jeder Geschossboden zu Gelände.

    Die Liste ist kurz, weil jedes Wort darin eine Entscheidung ist. Wer sie erweitert,
    prüfe zuerst, ob das Wort auch als Bauteil vorkommt.
    """
    assert "boden" not in GELAENDE_WOERTER
    assert "platte" not in GELAENDE_WOERTER
    assert len(GELAENDE_WOERTER) <= 6, (
        "eine wachsende Wortliste ist der Anfang des Teilstring-Vergleichs")


# --------------------------------------------------------------------------------------
# 4 · Und die Folge, um die es eigentlich ging
# --------------------------------------------------------------------------------------

def test_mit_gelaendenamen_entsteht_wieder_eine_maske():
    """**Der eigentliche Schaden war nicht die Regel, sondern was daran hing.**

    Ohne erkanntes Gelände liefert `bauwerksmaske` `None` — richtig so. Aber `_bester_seed`
    wählt ohne Maske nicht aus und rendert **einen** Startwert statt drei. Die
    Drei-Seed-Vorgabe fiel damit lautlos aus.
    """
    tabelle = [{"name": "Beton_C25", "farbe_srgb_8bit": [10, 20, 30]},
               {"name": "Gelaende_Hang", "farbe_srgb_8bit": [40, 50, 60]}]
    farben = [(10, 20, 30)] * 50 + [(40, 50, 60)] * 50

    e = maske.bauwerksmaske(farben, tabelle)

    assert e["maske"] is not None, "ohne Maske faellt die Drei-Startwert-Vorgabe aus"
    assert sum(e["maske"]) == 50, "das Gelaende gehoert NICHT ins Bauwerk"


def test_gegenprobe_ohne_gelaendenamen_bleibt_es_bei_None():
    """Die Regel wird weiter statt aufgeweicht — das ist der Unterschied.

    Ein Name, den niemand als Gelände erkennen kann, führt weiterhin zu `None`. Das ist
    ein Befund und kein Fehler.
    """
    tabelle = [{"name": "Beton_C25", "farbe_srgb_8bit": [10, 20, 30]},
               {"name": "Flaeche_A", "farbe_srgb_8bit": [40, 50, 60]}]
    farben = [(10, 20, 30)] * 50 + [(40, 50, 60)] * 50

    assert maske.bauwerksmaske(farben, tabelle)["maske"] is None
