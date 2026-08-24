"""Rang statt Betrag — das dritte Bein, und warum es (noch) über nichts entscheidet.

**Woher es kommt.** Die HomeStation hat am 23.08.2026 nachgerechnet, warum unser
Umrissmass in einer Stadtszene ausfällt: Der Schätzer **ordnet richtig** (Bauwerk 1,7124,
Nachbar 1,6112) und staucht nur den *Betrag* auf 3 % der Kartenspanne. Ein monokularer
Schätzer liefert relative Tiefe — unser Mass fragte nach dem Betrag.

**Was diese Datei prüft, ist nicht «R2 ist gut».** Sie prüft drei Dinge:

1. dass das Mass tut, was es behauptet (Rang, nicht Betrag),
2. dass es seinen eigenen **Nullwert** mitbringt — 50 %, aus der Konstruktion,
3. dass es **nichts entscheidet**, solange die vorgeschlagene Schwelle unter diesem
   Nullwert liegt.

Punkt 3 ist der Anlass für den Entscheid vom 23.08.: 0,45 liegt unter 0,50. Weisses
Rauschen besteht diese Schwelle in 138 von 200 Startwerten — gemessen, unten.

Alle Karten sind synthetisch und hier erzeugt (Regel 3): kein EXR, keine GPU, kein Netz.
"""
from __future__ import annotations

import math
import random
import statistics
from pathlib import Path

import pytest

from aiimaging import geometrie_qa as g
from aiimaging import tiefenschaetzer as ts
from aiimaging.geometrie_qa import (
    POLARITAET_DISPARITAET,
    POLARITAET_TIEFE,
    R2_MIN_ABSCHNITTE,
    R2_SCHWELLE,
    R2_ZUFALLSNIVEAU,
    QaError,
)

BREITE = HOEHE = 120
VON, BIS = 30, 89


def _maske() -> list[bool]:
    return [(VON <= x <= BIS and VON <= y <= BIS)
            for y in range(HOEHE) for x in range(BREITE)]


def _stufe(innen: float, aussen: float) -> list[float]:
    return [(innen if m else aussen) for m in _maske()]


def _rauschen(seed: int) -> list[float]:
    z = random.Random(seed)
    return [z.random() for _ in range(BREITE * HOEHE)]


def _anteil(karte, **kw) -> float:
    return g.anteil_naeher_am_rand(karte, _maske(), breite=BREITE,
                                   polaritaet=POLARITAET_DISPARITAET, **kw)["anteil"]


# --------------------------------------------------------------------------------------
# 1 · Es misst den Rang und nicht den Betrag — das ist der ganze Zweck
# --------------------------------------------------------------------------------------

def test_ein_winziger_sprung_zaehlt_genauso_wie_ein_riesiger():
    """**Die Eigenschaft, für die es das Mass gibt.**

    Das Betragsmass fällt in der Stadtszene von +0,4227 auf +0,0016 — nicht weil das Bild
    schlechter wäre, sondern weil der Schätzer zwei Betonkörper in 34 und 49 m nur um 3 %
    der Kartenspanne auseinanderlegt. Ein Rangmass darf das nicht merken.
    """
    riesig = _anteil(_stufe(9.0, 1.0))
    winzig = _anteil(_stufe(1.0003, 1.0))

    assert riesig == winzig == pytest.approx(1.0)


def test_die_polaritaet_dreht_das_urteil_um():
    """Ohne Richtung heisst «grösser» nichts.

    Bei Disparität liegt das Bauwerk oben, bei metrischer Tiefe unten. Dieselbe Karte
    ergibt darum zwei entgegengesetzte Antworten — und beide sind richtig.
    """
    karte = _stufe(9.0, 1.0)
    maske = _maske()

    als_disparitaet = g.anteil_naeher_am_rand(karte, maske, breite=BREITE,
                                              polaritaet=POLARITAET_DISPARITAET)
    als_tiefe = g.anteil_naeher_am_rand(karte, maske, breite=BREITE,
                                        polaritaet=POLARITAET_TIEFE)

    assert als_disparitaet["anteil"] == pytest.approx(1.0)
    assert als_tiefe["anteil"] == pytest.approx(0.0)


def test_ohne_polaritaet_steht_keine_zahl_da():
    e = g.anteil_naeher_am_rand(_stufe(9.0, 1.0), _maske(), breite=BREITE)

    assert e["anteil"] is None
    assert any("NICHT GEMESSEN" in w for w in e["warnungen"])


def test_eine_karte_ohne_jede_struktur_ist_ueberall_unentschieden():
    """Grau: Innen- und Aussenmedian sind gleich. Kein Abschnitt liegt näher — 0 %.

    Dass die Abschnitte dabei als **unentschieden** gezählt werden und nicht als
    «ferner», ist der Unterschied zwischen einer Auskunft und einem Vorwurf.
    """
    e = g.anteil_naeher_am_rand([5.0] * (BREITE * HOEHE), _maske(), breite=BREITE,
                                polaritaet=POLARITAET_DISPARITAET)

    assert e["anteil"] == pytest.approx(0.0)
    assert e["n_unentschieden"] == e["n_abschnitte"] > 0


# --------------------------------------------------------------------------------------
# 2 · Der eigene Nullwert — und die Schwelle, die darunter liegt
# --------------------------------------------------------------------------------------

def test_weisses_rauschen_liegt_im_mittel_beim_muenzwurf():
    """**Der Befund, der den Entscheid vom 23.08.2026 trägt.**

    Hat die Karte gar keinen Bezug zur Maske, sind Innen- und Aussenmedian zwei
    unabhängige Ziehungen aus derselben Verteilung. Welcher grösser ausfällt, ist ein
    Münzwurf. Das folgt aus der Konstruktion — hier wird es trotzdem gemessen, weil
    «folgt aus der Konstruktion» in diesem Projekt schon einmal falsch war.
    """
    werte = [_anteil(_rauschen(seed)) for seed in range(60)]

    assert statistics.median(werte) == pytest.approx(R2_ZUFALLSNIVEAU, abs=0.06)


def test_die_vorgeschlagene_schwelle_liegt_UNTER_dem_zufallsniveau():
    """0,45 gegen 0,50 — und darum entscheidet dieses Mass heute über nichts.

    Der eine gemessene Rauschanker von 33,7 % ist **eine Ziehung**. Aus einer Ziehung eine
    Schwelle abzulesen ist derselbe Fehler wie eine Spanne aus einer Stichprobe für die
    Wahrheit zu nehmen — und den hat dieses Projekt am selben Tag schon einmal gemacht
    (die Kameraneigung).
    """
    assert R2_SCHWELLE < R2_ZUFALLSNIVEAU

    werte = [_anteil(_rauschen(seed)) for seed in range(60)]
    besteht = sum(1 for w in werte if w >= R2_SCHWELLE)

    assert besteht > len(werte) // 3, (
        "weisses Rauschen besteht die vorgeschlagene Schwelle in einem grossen Teil der "
        "Startwerte — eine Schwelle unter dem Zufallsniveau ist kein Tor")


def test_ein_wert_unter_dem_zufallsniveau_wird_auch_so_gemeldet():
    e = g.anteil_naeher_am_rand([5.0] * (BREITE * HOEHE), _maske(), breite=BREITE,
                                polaritaet=POLARITAET_DISPARITAET)

    assert e["ueber_zufall"] is False
    assert e["zufallsniveau"] == R2_ZUFALLSNIVEAU


def test_ueber_dem_zufallsniveau_wird_NICHT_als_ueber_zufall_gemeldet():
    """**Nicht messbar ist nicht dasselbe wie gut — auch hier nicht.**

    Über dem Münzwurf zu liegen genügt nicht; es käme darauf an, um wieviel. Diese Zahl
    fehlt, weil die Fenster benachbarter Abschnitte überlappen und die Abschnitte darum
    nicht unabhängig sind. `True` zu melden wäre eine Behauptung über einen Abstand, den
    niemand kennt.
    """
    e = g.anteil_naeher_am_rand(_stufe(9.0, 1.0), _maske(), breite=BREITE,
                                polaritaet=POLARITAET_DISPARITAET)

    assert e["anteil"] == pytest.approx(1.0)
    assert e["ueber_zufall"] is None
    assert any("überlappen" in w for w in e["warnungen"])


def test_die_ueberlappung_macht_die_streuung_messbar_groesser():
    """Der Beleg für den Vorbehalt im Satz darüber — gemessen, nicht behauptet.

    Bei `jeder_nte=3` überlappen die Fenster (Radius 6) stark; die tatsächliche Streuung
    des Rauschens liegt deutlich über der binomialen. Wer die binomiale Schranke benutzte,
    hielte Zufall für Signal.
    """
    werte, n = [], None
    for seed in range(60):
        e = g.anteil_naeher_am_rand(_rauschen(seed), _maske(), breite=BREITE,
                                    polaritaet=POLARITAET_DISPARITAET)
        werte.append(e["anteil"])
        n = e["n_abschnitte"]

    binomial = math.sqrt(0.25 / n)
    gemessen = statistics.pstdev(werte)

    assert gemessen > 1.4 * binomial, (
        f"gemessen {gemessen:.4f} gegen binomial erwartet {binomial:.4f} — wäre der "
        f"Faktor nahe 1, wären die Abschnitte unabhängig und die Schranke benutzbar")


# --------------------------------------------------------------------------------------
# 3 · Der Irrweg, den sie dokumentiert haben — damit ihn niemand zweimal geht
# --------------------------------------------------------------------------------------

def _irrweg_maximum_gegen_einzelpunkt(karte, maske, *, breite, jeder_nte=3, radius=6):
    """Die **verworfene** erste Fassung: Maximum innen gegen einen einzelnen Aussenpunkt.

    Steht hier nachgebaut, weil ein dokumentierter Irrweg nur dann etwas nützt, wenn er
    prüfbar ist. Sie ist ausdrücklich **nicht** die Fassung im Produkt.
    """
    hoehe = len(karte) // breite
    innen, _ = g._randpunkte(list(maske), breite, hoehe)
    treffer = gewertet = 0
    for i in innen[::jeder_nte]:
        x0, y0 = i % breite, i // breite
        drin, draussen = [], []
        for y in range(max(0, y0 - radius), min(hoehe, y0 + radius + 1)):
            for x in range(max(0, x0 - radius), min(breite, x0 + radius + 1)):
                k = y * breite + x
                (drin if maske[k] else draussen).append(karte[k])
        if not drin or not draussen:
            continue
        gewertet += 1
        if max(drin) > draussen[0]:          # Maximum gegen EINEN Punkt
            treffer += 1
    return treffer / gewertet if gewertet else None


def test_der_irrweg_laesst_weisses_rauschen_hoch_steigen():
    """**Gleiches gegen Gleiches, und das ist keine Feinheit.**

    Ihr erster Anlauf verglich das Maximum über das Innenfenster gegen einen einzelnen
    Aussenpunkt — strukturell nach oben verzerrt: Weisses Rauschen erreichte 71,3 %, mehr
    als jedes perfekte Bild. Median gegen Median behebt es.
    """
    maske = _maske()
    rauschen = _rauschen(11)

    verzerrt = _irrweg_maximum_gegen_einzelpunkt(rauschen, maske, breite=BREITE)
    sauber = _anteil(rauschen)

    assert verzerrt > 0.9, "der Irrweg hebt reines Rauschen weit über den Münzwurf"
    assert sauber < 0.75, "die gebaute Fassung tut das nicht"
    assert verzerrt > sauber


# --------------------------------------------------------------------------------------
# 4 · Nicht gemessen ist nicht null
# --------------------------------------------------------------------------------------

def test_ein_zu_kurzer_umriss_ergibt_keine_zahl():
    """Ein Anteil aus fünf Abschnitten hat fünf mögliche Werte."""
    klein = [(58 <= x <= 61 and 58 <= y <= 61)
             for y in range(HOEHE) for x in range(BREITE)]

    e = g.anteil_naeher_am_rand(_stufe(9.0, 1.0), klein, breite=BREITE,
                                polaritaet=POLARITAET_DISPARITAET)

    assert e["n_abschnitte"] < R2_MIN_ABSCHNITTE
    assert e["anteil"] is None
    assert any("NICHT GEMESSEN" in w for w in e["warnungen"])


def test_gegenprobe_derselbe_umriss_gross_genug_ergibt_eine_zahl():
    """Ohne sie zeigte der Test darüber nur, dass nie eine Zahl entsteht."""
    assert _anteil(_stufe(9.0, 1.0)) == pytest.approx(1.0)


@pytest.mark.parametrize("kw", [{"fensterradius": 0}, {"jeder_nte": 0},
                                {"fensterradius": -3}, {"jeder_nte": True}])
def test_unsinnige_stellraeder_werden_abgewiesen(kw):
    with pytest.raises(QaError):
        g.anteil_naeher_am_rand(_stufe(9.0, 1.0), _maske(), breite=BREITE,
                                polaritaet=POLARITAET_DISPARITAET, **kw)


def test_zwei_karten_verschiedener_groesse_ergeben_keine_zahl():
    with pytest.raises(QaError, match="unterschiedlich lang"):
        g.anteil_naeher_am_rand(_stufe(9.0, 1.0)[:-1], _maske(), breite=BREITE,
                                polaritaet=POLARITAET_DISPARITAET)


# --------------------------------------------------------------------------------------
# 5 · Und warum es trotzdem NICHT am Produktpfad hängt
# --------------------------------------------------------------------------------------
#
# Am 23.08.2026 habe ich R2 als drittes Bein angeschlossen — mit dem Argument, der
# Anschluss sei streng additiv: Kein Bild besteht durch R2, das ohne R2 durchgefallen
# waere. Am 24.08. hat die HomeStation es an ERZEUGTEN Bildern gemessen, und es ist wieder
# heraus. Diese Tests halten den Grund fest, damit ihn niemand noch einmal wegargumentiert.

def test_das_rangmass_haengt_NICHT_mehr_am_maskenweg():
    """**Die Bitte war ausdrücklich: nicht anzeigen, auch nicht als Beifahrer.**

    Sieben von zehn erzeugten Bildern lagen über dem perfekten Blender-Bild derselben
    Szene, sechs davon mit `|rho| < 0.32`. Eine Zahl, die bei schlechteren Bildern höher
    ausfällt, ist schlimmer als keine — und «sie entscheidet ja nichts» genügt nicht,
    solange ein Mensch sie liest.
    """
    quelle = (Path(ts.__file__)).read_text(encoding="utf-8")

    assert "anteil_naeher_am_rand" not in quelle, (
        "R2 haengt wieder am Maskenweg. Wer das will, misst zuerst an ERZEUGTEN Bildern "
        "und prueft die Y-Verschiebung (auf-vis-20260824-09)")


def test_das_paarurteil_kennt_das_rangmass_nicht():
    u = g.paarurteil({"gerichtet": 0.95}, {"gerichtet": 0.30},
                     anteil_ergebnis={"anteil": 0.90})

    assert "anwesenheit" not in u


def test_der_grund_steht_in_der_funktion_und_nicht_nur_im_protokoll():
    """Ein zurückgezogenes Mass, dessen Grund nur im Sitzungsprotokoll steht, wird wieder
    angeschlossen. Der Beleg gehört dorthin, wo jemand hinsieht, der es anschliessen will.
    """
    doc = g.anteil_naeher_am_rand.__doc__

    assert "NICHT AM PRODUKTPFAD" in doc
    assert "0,8405" in doc, "die Y-Verschiebung ist der entscheidende Beleg"


def test_die_zurueckgezogene_schwelle_traegt_ihre_ruecknahme_bei_sich():
    """Die Zahl bleibt stehen, damit Messungen und Protokolle sich auf sie beziehen können.

    Aber sie muss ihre Rücknahme mittragen, sonst liest sie jemand als Vorschlag. Ihr
    Urheber hat sie selbst zurückgezogen — mit einem Grund, der schwerer wiegt als der
    Anker: Eine Schwelle unter dem Zufallsniveau ist grundsätzlich unhaltbar.
    """
    quelle = Path(g.__file__).read_text(encoding="utf-8")
    ende = quelle.index("R2_SCHWELLE = 0.45")
    beginn = quelle.rindex("#: **ZURÜCKGEZOGEN", 0, ende)
    block = quelle[beginn:ende]

    assert "24.08.2026" in block
    assert "0,4942" in block and "0,1440" in block, (
        "beide Rauschanker gehoeren dazu — sie massen Verschiedenes, und beide hatten recht")
