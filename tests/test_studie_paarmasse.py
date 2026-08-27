"""Die Fallkonstruktion der Obergrenzen-Studie — ohne Blender.

Geprüft wird, was das Skript **rechnet**, nicht was Blender liefert: Die Fälle entstehen
aus einer Soll-Karte und einer Maske, und genau dort sitzen die Annahmen, die der Befund
trägt. Der Renderteil braucht Blender und steht deshalb nicht unter Test — er steht unter
der Auswertung in `docs/PAARSCHWELLEN_OBERGRENZE_2026-08-27.md`.
"""

import importlib.util
from pathlib import Path

import pytest

from aiimaging import geometrie_qa


def _studie():
    pfad = Path(__file__).resolve().parents[1] / "tools" / "studie_paarmasse.py"
    spec = importlib.util.spec_from_file_location("werkzeug_studie_paarmasse", pfad)
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul


HG = 1.0e10


def _szene(mit_boden: bool, breite=16, hoehe=16):
    """Ein Klotz in der Mitte. Mit Boden: der Hintergrund trägt endliche Werte.

    **16 × 16 und nicht kleiner**, weil `rho_ueber_maske` unter 32 Maskenpunkten mit
    Begründung schweigt — «ein rho daraus wäre Rauschen mit Dezimalpunkt». Eine 8 × 8-Szene
    hätte hier lauter `None` geliefert, und die Tests hätten die Wächter gemessen statt
    der Fallkonstruktion.
    """
    soll, maske = [], []
    for y in range(hoehe):
        for x in range(breite):
            innen = 4 <= x < 12 and 4 <= y < 12
            maske.append(innen)
            if innen:
                soll.append(10.0 + 0.1 * (x + y))
            else:
                soll.append(30.0 + 0.5 * y if mit_boden else HG)
    return soll, maske, breite, hoehe


# ======================================================================================
# Befund 3 — der Fall, um den es geht, ist ohne Boden NICHT MESSBAR
# ======================================================================================

def test_ohne_boden_bleibt_die_maske_nach_dem_entfernen_konstant():
    """**Der Kern von Befund 3.**

    Ohne Gelände gibt es nichts, womit sich die Lücke füllen liesse — in der Maske steht
    dann nur noch die Hintergrundmarke. Eine Konstante hat keine Rangfolge, und ρ ist
    `None`: *nicht messbar*, nicht null.
    """
    st = _studie()
    soll, maske, b, h = _szene(mit_boden=False)
    ist = st._boden_statt_bauwerk(soll, maske, b, h)
    innen = {ist[i] for i in range(len(ist)) if maske[i]}
    assert innen == {HG}, "ohne Boden bleibt die Hintergrundmarke stehen"

    rho = geometrie_qa.rho_ueber_maske(soll, ist, maske,
                                       polaritaet=geometrie_qa.POLARITAET_TIEFE)
    assert rho["gerichtet"] is None, "nicht messbar — und ausdruecklich nicht 0"


def test_mit_boden_wird_derselbe_fall_messbar_und_faellt_durch():
    """Die Gegenprobe: Wo Boden liegt, greift der Maskenweg — und urteilt klar."""
    st = _studie()
    soll, maske, b, h = _szene(mit_boden=True)
    ist = st._boden_statt_bauwerk(soll, maske, b, h)
    innen = {round(ist[i], 6) for i in range(len(ist)) if maske[i]}
    assert len(innen) > 1, "mit Boden entsteht wieder eine Rangfolge"

    rho = geometrie_qa.rho_ueber_maske(soll, ist, maske,
                                       polaritaet=geometrie_qa.POLARITAET_TIEFE)
    assert rho["gerichtet"] is not None
    assert rho["gerichtet"] < geometrie_qa.PAAR_RHO_SCHWELLE, "der Fall muss durchfallen"


# ======================================================================================
# Befund 2 — der Fall, an dem der Kantenanteil scheitert
# ======================================================================================

def test_innen_vertauscht_behaelt_den_umriss_und_dreht_die_tiefen_um():
    """Perfekte Umrisstreue bei vollständig falschen Tiefen — die Umkehrung der
    Warnung, die im Quelltext von `anteil_grenze_mit_kante` schon steht."""
    import random
    st = _studie()
    soll, maske, b, h = _szene(mit_boden=True)
    fall = dict((art, (gut, ist)) for art, gut, ist
                in st.faelle(soll, maske, b, h, random.Random(1)))
    gut, ist = fall["innen_vertauscht"]
    assert gut is False

    # Der Hintergrund ist unberuehrt — der Umriss steht also noch.
    assert all(ist[i] == soll[i] for i in range(len(soll)) if not maske[i])
    rho = geometrie_qa.rho_ueber_maske(soll, ist, maske,
                                       polaritaet=geometrie_qa.POLARITAET_TIEFE)
    assert rho["gerichtet"] == pytest.approx(-1.0), "vollstaendig verkehrt herum"

    # UND DAS IST BEFUND 2 IM KLEINEN: Der Kantenanteil unterscheidet diesen Fall
    # **gar nicht** vom treuen — der Umriss ist derselbe, also ist die Zahl dieselbe.
    # (In der echten Studie stehen dort 1.0000 gegen 1.0000; hier reicht die kleine
    # Szene nicht für den vollen Umriss, die Gleichheit trägt trotzdem.)
    treu = dict((a, i) for a, _, i in st.faelle(soll, maske, b, h,
                                                random.Random(1)))["treu"]
    assert (geometrie_qa.anteil_grenze_mit_kante(ist, maske, breite=b)["anteil"]
            == pytest.approx(
                geometrie_qa.anteil_grenze_mit_kante(treu, maske, breite=b)["anteil"])), (
        "der Kantenanteil sieht keinen Unterschied zum treuen Fall — genau das ist "
        "der Grund, warum er nicht als Tor taugt")


# ======================================================================================
# Befund 1 — die guten Fälle müssen gut bleiben
# ======================================================================================

def test_die_streng_monotone_umrechnung_laesst_rho_bei_eins():
    """Das Mass ist rangbasiert. Fällt das, ist nicht die Schwelle falsch, sondern
    die Metrik."""
    st = _studie()
    soll, maske, b, h = _szene(mit_boden=True)
    import random
    fall = dict((art, ist) for art, _, ist in st.faelle(soll, maske, b, h,
                                                        random.Random(1)))
    rho = geometrie_qa.rho_ueber_maske(soll, fall["skala"], maske,
                                       polaritaet=geometrie_qa.POLARITAET_TIEFE)
    assert rho["gerichtet"] == pytest.approx(1.0)


def test_die_nullprobe_der_treue_fall_ist_die_soll_karte():
    st = _studie()
    soll, maske, b, h = _szene(mit_boden=True)
    import random
    fall = dict((art, ist) for art, _, ist in st.faelle(soll, maske, b, h,
                                                        random.Random(1)))
    assert fall["treu"] == list(soll)


def test_die_etiketten_sind_fuenf_gute_und_sechs_schlechte():
    """Verschiebt sich das Verhältnis, verschiebt sich jede Zahl der Auswertung."""
    st = _studie()
    soll, maske, b, h = _szene(mit_boden=True)
    import random
    etiketten = [gut for _, gut, _ in st.faelle(soll, maske, b, h, random.Random(1))]
    assert etiketten.count(True) == 5
    assert etiketten.count(False) == 6


def test_jeder_fall_hat_die_laenge_der_soll_karte():
    """Eine Karte anderer Länge wuerde in `rho_ueber_maske` sofort scheitern — hier
    faellt es frueher auf und mit klarerer Ursache."""
    st = _studie()
    soll, maske, b, h = _szene(mit_boden=True)
    import random
    for art, _, ist in st.faelle(soll, maske, b, h, random.Random(1)):
        assert len(ist) == len(soll), art
