"""Die Geländeplatte wächst mit der Höhe — und das muss jemand erfahren.

**Der Befund** (HomeStation, `auf-20260921-128`, 22.09.2026): Der Widerspruch zwischen
`0,93` beim Quader und `0,36` beim Hochbau lag **nicht am Messweg**. Beide Szenen wurden
buchstabengleich gleich gemessen. Er lag daran, dass der Hochbau im Bild nur rund ein
Viertel so viel Fläche einnimmt (0,1524 gegen 0,5822).

**Die Ursache hinter der Ursache:** Die Geländeplatte ist ein Vielfaches der **grössten**
Spanne des Bauwerks — und beim Hochbau ist das die **Höhe**. 15,25 m hoch ergibt 38,12 m
Platte bei einem Grundriss von 12 × 9,5 m. Ein kleiner Turm auf einem grossen Feld.

Der Vorbehalt stand seit dem 09.09.2026 im Docstring der Konstanten. Er hat niemanden
gewarnt.

    *Ein Vorbehalt im Docstring ist kein Wächter. Er wird gelesen, wenn man ihn schon
    kennt.*

Die Wächter hier prüfen dreierlei: dass die Zahl an **einer** Stelle gerechnet wird, dass
die erzeugte Datei wirklich diese Zahl trägt, und dass die Warnung **genau dann** kommt,
wenn die Höhe treibt.
"""
from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

WERKZEUG = Path(__file__).resolve().parents[1] / "tools" / "make_test_ifc.py"


@pytest.fixture
def mk():
    spez = importlib.util.spec_from_file_location("make_test_ifc_gelaende", WERKZEUG)
    modul = importlib.util.module_from_spec(spez)
    sys.modules[spez.name] = modul
    spez.loader.exec_module(modul)
    return modul


# --------------------------------------------------------------------------------------
# 1 · Was die Platte treibt
# --------------------------------------------------------------------------------------

def test_beim_quader_treibt_der_grundriss(mk):
    mass = mk.gelaendekante(hochbau=False)

    assert mass["treiber"] == mk.TREIBER_GRUNDRISS
    assert mass["kante"] == pytest.approx(20.0), (
        "20 m — der Wert, auf den jede bestehende Messreihe des Quaders gebaut ist")
    assert mass["anteil_grundriss"] == pytest.approx(1.0)


def test_beim_hochbau_treibt_die_hoehe(mk):
    """**Der gemeldete Fall.**"""
    mass = mk.gelaendekante(hochbau=True)

    assert mass["treiber"] == mk.TREIBER_HOEHE
    assert mass["spanne_z"] > max(mass["spanne_x"], mass["spanne_y"])
    assert mass["kante"] == pytest.approx(38.125, abs=0.01), (
        "38,12 m Platte bei 12 m Grundriss — die Zahl aus auf-20260921-128")
    assert mass["anteil_grundriss"] < 0.8, (
        "der Grundriss erklaert weniger als vier Fuenftel der Plattenbreite")


def test_die_grenze_liegt_bei_groesser_und_nicht_bei_groesser_gleich(mk, monkeypatch):
    """**Dieser Test stand zuerst hier und prüfte nichts.**

    Er behauptete, die Grenze sei ``>`` und nicht ``>=``, und verglich dann zwei
    Konstanten miteinander. Eine Mutationsprobe (22.09.2026) hat ihn überführt: ``>=``
    eingesetzt, und er blieb grün — weil in keiner der beiden Szenen Höhe und Grundriss
    gleich gross sind.

        *Ein Wächter an einer Stelle, an der der Fall nicht vorkommt, ist kein Wächter —
        er ist eine Beruhigung.*

    Jetzt wird der Fall hergestellt: ein Körper, dessen Höhe **genau** dem Grundriss
    entspricht. Dann muss der Grundriss treiben, sonst warnte das Werkzeug bei jedem
    Würfel — und *eine Warnung, die auch im harmlosen Fall kommt, wird abgeschaltet.*
    """
    grundriss = max(mk.LAENGE_X, mk.BREITE_Y)

    monkeypatch.setattr(mk, "HOEHE_Z", grundriss - mk.PLATTENDICKE)
    gleich = mk.gelaendekante(hochbau=False)
    assert gleich["spanne_z"] == pytest.approx(grundriss), "der Fall muss wirklich eintreten"
    assert gleich["treiber"] == mk.TREIBER_GRUNDRISS

    monkeypatch.setattr(mk, "HOEHE_Z", grundriss - mk.PLATTENDICKE + 0.01)
    knapp_darueber = mk.gelaendekante(hochbau=False)
    assert knapp_darueber["treiber"] == mk.TREIBER_HOEHE, (
        "einen Zentimeter darueber muss sie kippen, sonst prueft der Test die Grenze "
        "wieder nicht")


def test_das_vielfache_geht_linear_ein(mk):
    einfach = mk.gelaendekante(hochbau=True, vielfaches=1.0)["kante"]
    sechsfach = mk.gelaendekante(hochbau=True, vielfaches=6.0)["kante"]

    assert sechsfach == pytest.approx(6.0 * einfach)


# --------------------------------------------------------------------------------------
# 2 · Die Zahl wird an EINER Stelle gerechnet — und die Datei trägt sie
# --------------------------------------------------------------------------------------

def test_die_erzeugte_datei_traegt_die_kante_aus_dieser_funktion(mk, tmp_path,
                                                                 monkeypatch):
    """**Der Wächter gegen die zweite Rechnung.**

    Hier stand dieselbe Arithmetik ein zweites Mal im Erzeuger. *Eine Zahl an zwei Stellen
    ist an einer davon bereits falsch, sobald jemand eine davon anfasst.*

    Geprüft wird die **Wirkung**: Eine erfundene Kantenlänge muss in der geschriebenen
    Datei auftauchen. Täte der Erzeuger seine eigene Rechnung, stünde dort etwas anderes.
    """
    erkennbar = 137.5
    # DIE ECHTE FUNKTION VORHER FESTHALTEN. Wer sie erst im Ersatz nachschlaegt, ruft den
    # Ersatz — der Test rief sich selbst.
    echte = mk.gelaendekante

    def gefaelscht(*, hochbau, vielfaches=None):
        return {**echte(hochbau=hochbau), "kante": erkennbar}

    monkeypatch.setattr(mk, "gelaendekante", gefaelscht)
    ziel = mk.erzeuge_ifc(tmp_path / "bau.ifc", mit_gelaende=True, hochbau=True)

    assert "137.5" in ziel.read_text(encoding="utf-8"), (
        "der Erzeuger rechnet die Plattenbreite selbst statt sie zu erfragen")


def test_ohne_gelaende_gibt_es_keine_platte(mk, tmp_path):
    ohne = mk.erzeuge_ifc(tmp_path / "ohne.ifc", mit_gelaende=False, hochbau=True)
    mit = mk.erzeuge_ifc(tmp_path / "mit.ifc", mit_gelaende=True, hochbau=True)

    # Geprüft wird am `.BASESLAB.` und nicht am Wort «Gelaende»: Das steht auch ohne
    # Platte in der Datei, als Name des IFCSITE. *Ein Wächter, der ein Wort sucht,
    # bewacht das Wort.*
    assert ".BASESLAB." not in ohne.read_text(encoding="utf-8")
    assert ".BASESLAB." in mit.read_text(encoding="utf-8")


# --------------------------------------------------------------------------------------
# 3 · Die Warnung, und dass sie genau dann kommt
# --------------------------------------------------------------------------------------

def _lauf(tmp_path, *schalter):
    return subprocess.run(
        [sys.executable, str(WERKZEUG), str(tmp_path / "bau.ifc"), *schalter],
        capture_output=True, text=True, timeout=120)


def test_der_hochbau_mit_gelaende_warnt(tmp_path):
    ergebnis = _lauf(tmp_path, "--gelaende", "--hochbau")

    assert ergebnis.returncode == 0
    assert "HOEHE" in ergebnis.stderr
    assert "NICHT VERGLEICHBAR" in ergebnis.stderr
    assert "38.12" in ergebnis.stderr, "die Warnung nennt die Zahl, nicht nur den Umstand"


def test_der_quader_warnt_nicht(tmp_path):
    """*Eine Warnung, die immer kommt, ist keine Warnung.*"""
    ergebnis = _lauf(tmp_path, "--gelaende")

    assert ergebnis.returncode == 0
    assert "ACHTUNG" not in ergebnis.stderr


def test_ohne_gelaende_warnt_auch_der_hochbau_nicht(tmp_path):
    """Ohne Platte gibt es nichts, was die Höhe aufblasen könnte."""
    ergebnis = _lauf(tmp_path, "--hochbau")

    assert "ACHTUNG" not in ergebnis.stderr


def test_die_warnung_nennt_den_ausweg(tmp_path):
    """Ein Befund ohne nächsten Schritt lässt den Leser stehen."""
    ergebnis = _lauf(tmp_path, "--gelaende", "--hochbau")

    assert "--gelaende-vielfaches=" in ergebnis.stderr
    assert "6.0" in ergebnis.stderr, "die gemessene Zahl, mit der sich angleichen lässt"


def test_ein_angeglichenes_vielfaches_warnt_weiterhin(tmp_path):
    """**Und das ist Absicht.**

    Auch bei ``--gelaende-vielfaches=6.0`` treibt die Höhe die Platte — sie ist nur
    grösser. Die Warnung beschreibt den Umstand, nicht die Unvergleichbarkeit einer
    bestimmten Zahl. *Wer sie nach dem Angleichen verschwinden liesse, behauptete
    Vergleichbarkeit, die niemand gemessen hat.*
    """
    ergebnis = _lauf(tmp_path, "--gelaende", "--hochbau", "--gelaende-vielfaches=6.0")

    assert "ACHTUNG" in ergebnis.stderr
    assert "91.50" in ergebnis.stderr
