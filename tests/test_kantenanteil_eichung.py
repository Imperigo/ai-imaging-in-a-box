"""Der Umrissanteil an den drei Nullankern — und warum er zwei davon nicht messen KANN.

**Der Anlass ist eine fremde Eichung, die meinen eigenen Vorschlag erledigt hat.**
`docs/EICHUNG_2026-08-23.md` (HomeStation) prüfte dieselbe Idee in zwei Fassungen und zog
sie zurück: In der relativen Fassung erreichen grau und ein Verlauf **100 %**. Bei einem
strukturlosen Bild ist der Gradient überall gleich, und „über dem 95. Perzentil von lauter
Gleichständen" ist für jeden Punkt wahr — das Mass belohnt dann Strukturlosigkeit, also
genau die Krankheit von ``geom_iou``, gegen die es antreten sollte.

**Meine Fassung hatte denselben Defekt, nur halb verdeckt.** Nachgemessen:

    grau      100 % gegen Nullwert 100 %   → fiel richtig durch
    Verlauf   100 % gegen Nullwert  93.9 % → galt als „über Zufall"

Rechnerisch stimmt das zweite und bedeutet nichts: Wo 94 % aller Bildpunkte als „stärkste
5 %" gelten, sagt ein Anteil von 100 % an der Grenze nichts über den Umriss. Die Antwort
ist nicht ein strengerer Vergleich, sondern die richtige **Kategorie** — nicht messbar.
"""
import random

import pytest

from aiimaging import geometrie_qa

BREITE = HOEHE = 64
#: Ein Quader in der Bildmitte. Dieselbe Maske für alle Fälle.
MASKE = [bool(18 <= i % BREITE < 46 and 20 <= i // BREITE < 52)
         for i in range(BREITE * HOEHE)]


def _karte(fn):
    return [fn(i % BREITE, i // BREITE) for i in range(BREITE * HOEHE)]


PERFEKT = _karte(lambda x, y: 0.9 if MASKE[y * BREITE + x] else 0.1)
GRAU = _karte(lambda x, y: 0.5)
VERLAUF = _karte(lambda x, y: x / BREITE)
RAUSCHEN = _karte(lambda x, y: random.Random(7 * y + x).random())


def _anteil(karte):
    return geometrie_qa.anteil_grenze_mit_kante(karte, MASKE, breite=BREITE)


# ======================================================================================
# Die drei Nullanker
# ======================================================================================

def test_grau_ist_nicht_messbar_und_nicht_etwa_perfekt():
    befund = _anteil(GRAU)
    assert befund["messbar"] is False
    assert befund["anteil"] is None, (
        "ein strukturloses Bild bekommt KEINE Zahl — es hätte sonst 100 %"
    )
    assert befund["ueber_zufall"] is None
    assert "Nicht messbar" in befund["grund"]


def test_ein_verlauf_ist_nicht_messbar():
    """Der Fall, der vorher durchging.

    Der Verlauf meldete 100 % gegen einen Nullwert von 93,9 % — und galt damit als „über
    Zufall". Die Zahl stimmte, und sie bedeutete nichts.
    """
    befund = _anteil(VERLAUF)
    assert befund["messbar"] is False
    assert befund["anteil"] is None
    assert befund["zufall"] > 0.5, (
        "der tatsächliche Nullwert liegt weit über den verlangten 5 % — genau daran "
        "erkennt man, dass die Schranke nicht trennt"
    )


def test_weisses_rauschen_ist_messbar_und_faellt_durch():
    """Wichtige Unterscheidung: Rauschen ist **messbar** und schlecht, nicht unmessbar.

    Es hat überall echte Gradientenunterschiede — die Schranke trennt also sauber (der
    Nullwert liegt bei 5,0 %). Der Anteil an der Grenze ist dann klein, und die Schwelle
    fängt ihn. Wer Rauschen als „nicht messbar" abtäte, verlöre genau die Aussage.
    """
    befund = _anteil(RAUSCHEN)
    assert befund["messbar"] is True
    assert befund["zufall"] == pytest.approx(0.05, abs=0.02)
    assert befund["anteil"] < geometrie_qa.PAAR_KANTENANTEIL_SCHWELLE


def test_das_perfekte_bild_ist_messbar_und_besteht():
    befund = _anteil(PERFEKT)
    assert befund["messbar"] is True
    assert befund["zufall"] == pytest.approx(0.05, abs=0.02)
    assert befund["anteil"] > geometrie_qa.PAAR_KANTENANTEIL_SCHWELLE


# ======================================================================================
# Was daraus für das Paarurteil folgt
# ======================================================================================

def test_ein_unmessbarer_anteil_faellt_auf_die_kante_zurueck():
    """`anteil = None` heisst „kein zweites Bein aus dem Anteil" — und der Test sagt es.

    Vorher lieferte der Verlauf eine 1.0, `paarurteil` verglich sie mit der Schwelle
    0.20, und ein reiner Verlauf bestand das zweite Bein. Eine Zahl mit Fussnote wird
    ohne die Fussnote weitergereicht.
    """
    anteil = _anteil(VERLAUF)
    kante = geometrie_qa.kante_an_maskengrenze(VERLAUF, MASKE, breite=BREITE,
                                               polaritaet=1)
    urteil = geometrie_qa.paarurteil({"gerichtet": 0.85}, kante,
                                     anteil_ergebnis=anteil)
    assert urteil["zweites_bein"] == "kante"
    assert urteil["anteil"] is None
    assert urteil["bestanden"] is False


def test_beim_perfekten_bild_traegt_der_anteil_das_zweite_bein():
    """Gegenprobe — sonst prüfte der Test oben nur, dass immer die Kante gewinnt."""
    anteil = _anteil(PERFEKT)
    kante = geometrie_qa.kante_an_maskengrenze(PERFEKT, MASKE, breite=BREITE,
                                               polaritaet=1)
    urteil = geometrie_qa.paarurteil({"gerichtet": 0.85}, kante,
                                     anteil_ergebnis=anteil)
    assert urteil["zweites_bein"] == "anteil"
    assert urteil["anteil"] == pytest.approx(1.0)


def test_die_grenze_zwischen_messbar_und_nicht_traegt_ihre_herkunft():
    """`MAX_ZUFALL_FAKTOR` steht als benannte Konstante da — nicht als 2 im Ausdruck.

    Und ihre Herkunft steht daneben: Sie kommt aus einer fremden Eichung, die meinen
    eigenen Vorschlag widerlegt hat. Eine Zahl ohne Herkunft ist in einem Jahr eine
    Zahl, die jemand geraten haben könnte.
    """
    from pathlib import Path as _P

    assert geometrie_qa.MAX_ZUFALL_FAKTOR == 2.0

    quelle = _P(geometrie_qa.__file__).read_text(encoding="utf-8")
    kopf = quelle.split("MAX_ZUFALL_FAKTOR")[0]
    letzter_block = kopf[kopf.rindex("KANTENANTEIL_STAERKSTE"):]
    assert "EICHUNG_2026-08-23" in letzter_block, (
        "die Herkunft der Konstante gehört an die Konstante"
    )
    assert "2 * staerkste" not in quelle, "die 2 darf nicht mehr im Ausdruck stehen"
