"""Der Nachweis, dass die Stilstudie misst — und dass sie nicht mehr behauptet als sie misst.

Die Geometriestudie musste zwei Zahlen berichtigen, weil ihre **Messinstrumente** schief
waren und nicht ihre Metrik (Kapitel 4a von ``docs/SCHWELLENSTUDIE_2026-08-18.md``). Diese
Datei ist die Antwort darauf: Sie prüft zuerst die Instrumente und erst danach die
Ergebnisse.

Drei Gruppen, in dieser Reihenfolge:

1. **Die Generatoren sagen die Wahrheit über sich selbst.** Isotrope Vektoren müssen eine
   Ähnlichkeitsstreuung von ``1/√d`` erzeugen, Kegelvektoren mit Anteil ``a`` eine
   mittlere Ähnlichkeit von ``a²``. Beides ist geschlossen bekannt. Trifft es nicht zu,
   ist keine Zeile der Studie deutbar — dieselbe Rolle wie
   ``test_szene_ist_praktisch_bindungsfrei`` in der Geometriestudie.

2. **Die Längeninvarianz.** Sie ist die einzige Prüfung hier, die die Metrik *widerlegen*
   kann, und sie hält — bis auf einen Zahlbereich, in dem sie **still** bricht. Der Bruch
   steht in ``test_jenseits_von_1e153_faelscht_die_metrik_still``, weil er die Gestalt hat,
   gegen die ``StilError`` überhaupt angetreten ist: eine bedeutungslose Zahl, die ein
   Gate passiert.

3. **Was die Studie NICHT belegt**, in ausführbarer Form. Mehrere Tests halten
   ausdrücklich fest, dass eine Zahl *keine* Aussage über echte Bilder ist — etwa
   ``test_der_boden_haengt_am_einbetter_und_der_ist_hier_nicht_gemessen``. Ein Test, der
   eine Grenze festschreibt, ist die einzige Form von Bescheidenheit, die ein Refactoring
   überlebt.

Alle Vektoren sind synthetisch und hier erzeugt (Regel 3). Kein Modell, keine GPU, kein
Netz, kein ``numpy``. Zufall trägt feste Startwerte.

Die Dimensionen sind hier klein gehalten, wo die Aussage nicht an der Dimension hängt:
Ein Lauf über 768 Dimensionen zieht Millionen von Zufallszahlen in reinem Python. Wo die
Dimension die Aussage trägt, steht sie ausdrücklich im Test.
"""
from __future__ import annotations

import ast
import json
import math
import random
import statistics
import sys

import pytest

from aiimaging import einbetter
from aiimaging.stil_qa import (
    AGG_MAX,
    AGG_MITTEL,
    SCHWELLE_STIL,
    StilError,
    boden_fuer,
    kosinus,
    schwelle_aus_boden,
    stil_score,
)
from aiimaging.stilstudie import (
    KEGELANTEILE,
    REGISTRY_DIMENSIONEN,
    VORGABE_DIMENSION,
    StilstudieError,
    aggregationsvergleich,
    baue_referenzsatz,
    grenzfaelle,
    invarianzgrenze,
    kegelreihe,
    kohaerenz,
    laengeninvarianz,
    maxreihe,
    mittel_bei_teiltreffer,
    nullverteilung,
    nullverteilung_je_dimension,
    studienlauf,
    winkel_grad,
    zufallstreffer_schranke,
)
from conftest import PAKET, nachgeladene_module

#: Arbeitsmass der Stichprobentests. 256 Dimensionen sind gross genug, dass die
#: Konzentration greift, und klein genug für eine schnelle Testsuite.
DIM = 256

#: Proben je Messpunkt in dieser Datei. Die Streuung einer Streuungsschätzung liegt bei
#: ``1/√(2n)``, bei 400 also rund 3,5 %.
PROBEN = 400


def zufallsvektoren(seed: int, dimension: int, anzahl: int) -> list[list[float]]:
    """Unabhängige isotrope Vektoren — für Tests, die den Generator des Moduls umgehen."""
    wuerfel = random.Random(seed)
    return [[wuerfel.gauss(0.0, 1.0) for _ in range(dimension)] for _ in range(anzahl)]


# --------------------------------------------------------------------------------------
# 0 · Die Instrumente — ohne sie ist keine Zeile darunter deutbar
# --------------------------------------------------------------------------------------

@pytest.mark.parametrize("dimension", [64, 128, 256])
def test_der_isotrope_generator_trifft_seine_eigene_vorhersage(dimension):
    """Die Streuung des Bodens muss ``1/√d`` sein. Das ist geschlossen bekannt.

    Der wichtigste Test dieser Datei. Weicht die Messung ab, zieht der Generator nicht
    über die Dimension, die er angibt — und jede Bodenzahl der Studie wäre ein Artefakt.
    """
    ergebnis = nullverteilung(dimension, n_proben=PROBEN, seed=1)
    kontrolle = ergebnis["kontrolle"]
    assert kontrolle["pruefbar"] is True
    assert kontrolle["groesse"] == "streuung"
    assert kontrolle["erwartet"] == pytest.approx(1.0 / math.sqrt(dimension))
    assert kontrolle["erfuellt"] is True, (
        f"gemessen {kontrolle['gemessen']}, erwartet {kontrolle['erwartet']}")


def test_der_boden_liegt_bei_null_und_nicht_irgendwo():
    """Zwei zusammenhanglose Vektoren sind im Mittel rechtwinklig — nicht ähnlich.

    Das ist der Nullpunkt, gegen den jede Schwelle gelesen wird.
    """
    kennzahlen = nullverteilung(DIM, n_proben=PROBEN, seed=2)["kennzahlen"]
    assert kennzahlen["mittel"] == pytest.approx(0.0, abs=0.01)


@pytest.mark.parametrize("anteil", [0.2, 0.4, 0.6])
def test_der_kegelgenerator_trifft_seine_eigene_vorhersage(anteil):
    """Ein Kegel mit Anteil ``a`` hebt den Boden auf ``a²``.

    Die Herleitung ist eine Zeile: Für unabhängige Ziehungen ``u, v`` von der
    Einheitskugel ist ``E[⟨u, v⟩] = |E[u]|²``, und der Mittelvektor dieses Kegels ist
    ``a`` mal seine Achse.

    Trifft das nicht zu, baut der Generator einen anderen Kegel als sein Parameter
    behauptet — genau der Fehler des zu kleinen Zusatzkörpers in der Geometriestudie:
    Die Rechnung wäre richtig und die Achse falsch beschriftet.
    """
    ergebnis = nullverteilung(DIM, kegelanteil=anteil, n_proben=PROBEN, seed=3)
    kontrolle = ergebnis["kontrolle"]
    assert kontrolle["groesse"] == "mittel"
    assert kontrolle["erwartet"] == pytest.approx(anteil * anteil)
    assert kontrolle["erfuellt"] is True
    assert ergebnis["kennzahlen"]["mittel"] == pytest.approx(anteil * anteil, abs=0.02)


def test_bei_mehreren_referenzen_gibt_es_keine_vorhersage_und_das_steht_da():
    """Kein Urteil aus Mangel an Vorhersage — dieselbe Haltung wie in der Geometriestudie.

    Für ``max`` über mehrere Referenzen ist kein geschlossener Erwartungswert bekannt. Die
    Zeile beschreibt dann, sie prüft nicht, und sie sagt das von sich selbst.
    """
    kontrolle = nullverteilung(DIM, n_referenzen=4, n_proben=60, seed=4)["kontrolle"]
    assert kontrolle["pruefbar"] is False
    assert "keine geschlossene" in kontrolle["grund"]


def test_wuerfel_statt_kugel_waere_hier_kein_messbarer_fehler():
    """Eine Annahme des ersten Entwurfs, nachgemessen statt geglaubt.

    Der Entwurf begründete die normalverteilten Komponenten damit, gleichverteilte
    (``uniform(-1, 1)``) würden den Boden sichtbar zu hoch treiben. **Das ist falsch.**
    Der Würfel erzeugt zwar keine gleichmässige Richtung, aber die *paarweise
    Kosinus-Ähnlichkeit* unterscheidet sich in diesen Dimensionen nicht messbar.

    Der Test hält die Widerlegung fest, damit die Begründung im Modul-Docstring nicht
    wieder zur bequemen Geschichte wird: Die Wahl ist richtig wegen Exaktheit, nicht weil
    sie einen Fehler abwendet.
    """
    wuerfel = random.Random(9)
    aus_kugel = [kosinus([wuerfel.gauss(0.0, 1.0) for _ in range(DIM)],
                         [wuerfel.gauss(0.0, 1.0) for _ in range(DIM)])
                 for _ in range(PROBEN)]
    aus_wuerfel = [kosinus([wuerfel.uniform(-1.0, 1.0) for _ in range(DIM)],
                           [wuerfel.uniform(-1.0, 1.0) for _ in range(DIM)])
                   for _ in range(PROBEN)]
    kugel_streuung = statistics.stdev(aus_kugel)
    wuerfel_streuung = statistics.stdev(aus_wuerfel)
    assert wuerfel_streuung == pytest.approx(kugel_streuung, rel=0.15)
    assert wuerfel_streuung == pytest.approx(1.0 / math.sqrt(DIM), rel=0.15)


def test_der_boden_ist_niemals_negativ_egal_welche_verteilung():
    """``E[⟨u, v⟩] = |E[u]|² ≥ 0`` — der Satz, der die Studie mit der Wirklichkeit verbindet.

    Für unabhängige Ziehungen aus **irgendeiner** Verteilung auf der Einheitskugel ist die
    mittlere paarweise Ähnlichkeit das Quadrat der Länge des Mittelvektors, also nie
    negativ. Der isotrope Boden bei 0,00 ist damit der **kleinstmögliche** Boden: Jeder
    echte Einbetter liegt darüber, nur um wieviel, ist hier nicht messbar.
    """
    for anteil in (0.0, 0.3, 0.6):
        mittel = nullverteilung(DIM, kegelanteil=anteil, n_proben=200,
                                seed=5)["kennzahlen"]["mittel"]
        assert mittel >= -0.02, f"Boden bei Kegelanteil {anteil} negativ: {mittel}"


# --------------------------------------------------------------------------------------
# 1 · Die Nullverteilung — wo eine Schwelle von 0,30 überhaupt liegt
# --------------------------------------------------------------------------------------

def test_die_dimensionen_kommen_aus_der_registry_nicht_aus_der_luft():
    """Kommt ein Einbetter dazu, wandert seine Dimension von selbst in die Studie."""
    assert REGISTRY_DIMENSIONEN == tuple(
        sorted({e.dimension for e in einbetter.EINBETTER.values()}))
    assert VORGABE_DIMENSION == einbetter.hole(einbetter.VORGABE_EINBETTER).dimension
    assert VORGABE_DIMENSION == 768, "SigLIP 2 ist die Vorgabe — 768 Dimensionen"


def test_dinov3_dimension_ist_enthalten_obwohl_es_ausgeschlossen_ist():
    """1024 gehört in die Studie: Auf diesem Boden ist die überlieferte 0,30 entstanden.

    Regel 1 schliesst DINOv3 als Abhängigkeit aus. Als **Herkunft der Zahl** bleibt es
    relevant — wer 0,30 deuten will, muss wissen, wo sie gemessen wurde.
    """
    dinov3 = einbetter.hole("dinov3")
    assert dinov3.zulaessig is False
    assert dinov3.dimension in REGISTRY_DIMENSIONEN


def test_je_hoeher_die_dimension_desto_enger_der_boden():
    """Die Konzentration ist die ganze Aussage: In hohen Dimensionen ist alles fast rechtwinklig."""
    streuungen = [nullverteilung(d, n_proben=PROBEN, seed=6)["kennzahlen"]["streuung"]
                  for d in (64, 256, 1024)]
    assert streuungen[0] > streuungen[1] > streuungen[2]


def test_die_schwelle_liegt_viele_streuungen_ueber_dem_boden():
    """Bei 768 Dimensionen sind es rund acht. Das ist die Zahl, um die es geht.

    Sie sagt: Ein *zusammenhangloses* Bildpaar erreicht 0,30 praktisch nie — **wenn** der
    Einbetter isotrop streut. Was 0,30 über Stil sagt, steht damit noch nicht fest.
    """
    ergebnis = nullverteilung(768, n_proben=PROBEN, seed=7)
    assert ergebnis["abstand_in_streuungen"] > 6.0
    assert ergebnis["anteil_ueber_schwelle"] == 0.0


def test_keine_einzige_zufallsprobe_erreicht_die_schwelle():
    """Über alle Registry-Dimensionen: kein Treffer. Die Stichprobe ist die Aussage.

    Was hier **nicht** steht, ist eine Wahrscheinlichkeit. „0 von 400" heisst „kleiner als
    etwa 1/400", nicht „null".
    """
    lauf = nullverteilung_je_dimension(n_proben=PROBEN, seed=8)
    assert lauf["alle_kontrollen_erfuellt"] is True
    for zeile in lauf["zeilen"]:
        assert zeile["anteil_ueber_schwelle"] == 0.0
        assert zeile["kennzahlen"]["groesster"] < SCHWELLE_STIL


def test_die_schranke_ist_eine_schranke_und_wird_nicht_verletzt():
    """``exp(-d·t²/2)`` muss den gemessenen Anteil überdecken — bei kleinen d prüfbar.

    Bei 768 Dimensionen ist die Schranke rund 10⁻¹⁵ und mit keiner Stichprobe dieser Welt
    zu prüfen. Bei acht bis 64 Dimensionen ist der Anteil noch messbar, und dort muss die
    Schranke halten. Tut sie es dort nicht, taugt sie oben erst recht nichts.
    """
    for dimension in (8, 16, 32, 64):
        for schwelle in (0.3, 0.5):
            gemessen = nullverteilung(dimension, n_proben=800, seed=10,
                                      schwelle=schwelle)["anteil_ueber_schwelle"]
            schranke = zufallstreffer_schranke(dimension, schwelle)
            assert gemessen <= schranke, (dimension, schwelle, gemessen, schranke)


def test_die_schranke_ist_lose_und_darf_nicht_als_wahrscheinlichkeit_gelesen_werden():
    """Sie liegt um ein Mehrfaches über dem gemessenen Anteil. Das ist Absicht, keine Güte."""
    gemessen = nullverteilung(32, n_proben=800, seed=11, schwelle=0.3)["anteil_ueber_schwelle"]
    schranke = zufallstreffer_schranke(32, 0.3)
    assert schranke > 2 * gemessen


def test_die_schranke_bei_nicht_positiver_schwelle_ist_die_triviale_eins():
    """Unter 0 liegt die halbe Kugel — eine Schranke kleiner als 1 wäre dort falsch."""
    assert zufallstreffer_schranke(768, 0.0) == 1.0
    assert zufallstreffer_schranke(768, -0.5) == 1.0


#: Die alte Schwelle. Sie steht hier weiter, weil mehrere Tests dieser Datei die Aussage
#: festhalten, WARUM sie falsch war — und dafür brauchen sie die Zahl.
ALTE_SCHWELLE = 0.30


def test_die_warnung_dieser_studie_ist_eingetreten_und_wurde_uebertroffen():
    """**Die wichtigste Grenze dieser Studie — und ihre Bestätigung am Gerät.**

    Die Kegelreihe sagte vorher: Besetzt ein Einbetter einen Kegel mit Anteil 0,6, liegt
    der Boden bei 0,36 — **über** der damaligen Schwelle 0,30. Dann besteht jedes
    beliebige Bildpaar, auch ein völlig zusammenhangloses. Die Studie konnte das nur als
    Möglichkeit benennen; wo SigLIP 2 liegt, war hier nicht messbar.

    **Gemessen am 18.08.2026** (`auf-20260818-11`, 4950 Paare aus 100 Bildern): Der Boden
    liegt bei **0,526** — also noch über der ungünstigsten Vorausrechnung dieser Studie.
    Die Folge war genau die vorhergesagte: 4950 von 4950 Paaren bestanden.

    *Eine synthetische Studie kann eine Zahl nicht widerlegen, aber sie kann sagen, woran
    sie hängt — und wo man messen muss. Genau das hat sie getan, und die Messung fiel
    schlechter aus als ihr pessimistischster Fall.*
    """
    # Gegen die ALTE Schwelle gerechnet — das ist die Warnung, die damals ausgesprochen
    # wurde, und sie soll nachvollziehbar bleiben.
    damals = kegelreihe(dimension=DIM, kegelanteile=KEGELANTEILE, n_proben=200, seed=12,
                        schwelle=ALTE_SCHWELLE)
    boeden = {z["kegelanteil"]: z["kennzahlen"]["mittel"] for z in damals["zeilen"]}
    assert boeden[0.0] < boeden[0.3] < boeden[0.6]
    assert boeden[0.6] > ALTE_SCHWELLE          # die Warnung dieser Studie
    assert damals["kippanteil"] == 0.6
    zeile = next(z for z in damals["zeilen"] if z["kegelanteil"] == 0.6)
    assert zeile["anteil_ueber_schwelle"] > 0.8

    gemessen = boden_fuer("siglip2-base", "pooler_output")
    assert gemessen["mittel"] > boeden[0.6], "Die Wirklichkeit war schlimmer als der Kegel 0,6."
    assert gemessen["mittel"] > ALTE_SCHWELLE

    # Und gegen die NEUE Schwelle kippt keine einzige Zeile mehr: Selbst ein Kegel von 0,6
    # hebt den Boden nicht bis dorthin. Das ist der Abstand, den ein Gate braucht.
    heute = kegelreihe(dimension=DIM, kegelanteile=KEGELANTEILE, n_proben=200, seed=12)
    assert heute["kippanteil"] is None
    assert SCHWELLE_STIL > max(boeden.values())


def test_der_ueberlieferte_fehlbereich_passt_zu_einem_kegel_von_etwa_0_3():
    """Ein Zusammentreffen, das die überlieferten Zahlen anders lesen lässt.

    ``stil_qa`` überliefert aus DINOv3-Läufen: verfehlte Bilder lagen bei **0,06–0,13**.
    Ein Kegel mit Anteil 0,3 erzeugt genau dort seinen Boden — bei einem Mittel um 0,09.

    Das **belegt nicht**, dass DINOv3 einen solchen Kegel hat; dafür bräuchte es das
    Modell. Es zeigt, dass der überlieferte „Fehlbereich" ebensogut der Boden des
    Einbetters sein kann wie eine Messung von Stilunähnlichkeit. Und wenn er das ist, ist
    er beim Wechsel auf SigLIP 2 **nicht übertragbar**.
    """
    zeile = nullverteilung(768, kegelanteil=0.3, n_proben=300, seed=13)
    kennzahlen = zeile["kennzahlen"]
    assert 0.06 <= kennzahlen["mittel"] <= 0.13
    assert kennzahlen["q05"] > 0.0, "ein Kegelboden liegt ganz im Positiven"


def test_max_ueber_viele_referenzen_hebt_den_boden():
    """Jede weitere Referenz ist ein weiterer Versuch, zufällig hoch auszufallen.

    Wer sein Referenzset vergrössert, verschiebt die Bedeutung der Schwelle, ohne die
    Schwelle anzufassen. Auf isotropem Grund bleibt der Boden auch bei 32 Referenzen weit
    unter 0,30 — das ist die Entwarnung, und sie gilt nur unter Isotropie.
    """
    reihe = maxreihe(dimension=DIM, referenzzahlen=(1, 4, 16), n_proben=120, seed=14)
    mittel = [z["kennzahlen"]["mittel"] for z in reihe["zeilen"]]
    assert mittel[0] < mittel[1] < mittel[2]
    assert all(z["anteil_ueber_schwelle"] == 0.0 for z in reihe["zeilen"])


# --------------------------------------------------------------------------------------
# 2 · Die Kontrolle, die widerlegen kann
# --------------------------------------------------------------------------------------

def test_laengeninvarianz_haelt_ueber_zwoelf_zehnerpotenzen():
    """Die Zusage, auf der das Stil-Gate ruht: Länge trägt keine Bedeutung.

    Das Gegenstück zu ``MONOTON`` in der Geometriestudie — die einzige Messung hier, die
    die Metrik hätte umwerfen können.
    """
    ergebnis = laengeninvarianz(dimension=DIM, n_paare=10, seed=15)
    assert ergebnis["bestanden"] is True
    assert ergebnis["groesste_abweichung"] < 1e-12
    assert ergebnis["n_vergleiche"] == 10 * 7 * 7


def test_beide_vektoren_werden_verschieden_gestreckt():
    """Zwei gleich gestreckte Vektoren wären der leichtere Fall — und der falsche Test."""
    ergebnis = laengeninvarianz(dimension=32, faktoren=(1e-4, 1.0, 1e4), n_paare=5, seed=16)
    assert ergebnis["bestanden"] is True
    assert ergebnis["n_vergleiche"] == 5 * 9


@pytest.mark.parametrize("faktoren", [(0.0, 1.0), (-2.0, 1.0), ()])
def test_unbrauchbare_faktoren_sind_ein_fehler(faktoren):
    """0 löscht die Richtung, ein negativer Faktor dreht sie um — beides ist nicht „Länge"."""
    with pytest.raises(StilstudieError):
        laengeninvarianz(dimension=8, faktoren=faktoren, n_paare=2)


def test_die_metrik_faelscht_auch_jenseits_von_1e153_nicht_mehr_still():
    """**Der schwerwiegendste Befund dieser Studie — behoben am 18.08.2026.**

    ``kosinus`` bildete ``sum(x*x)``. Ab Komponenten der Grössenordnung 10¹⁵⁴ lief diese
    Summe über, `inf/inf` ergab `nan`, und die abschliessende Klammerung zog daraus
    **1.0** — den höchstmöglichen Score. Zwei rechtwinklige Vektoren bekamen so einen
    vollen Treffer: **ein bestandenes Gate aus einem Überlauf, ohne Fehlermeldung.** Aus
    einem echten 0,8 wurde ebenfalls 1,0.

    Genau diese Gestalt hat der Fehler, gegen den ``StilError`` angetreten ist: nicht ein
    Abbruch, sondern eine bedeutungslose Zahl, die ein Gate passiert. Im Betrieb kam er
    nicht vor — SigLIP-Komponenten liegen bei ungefähr 1 —, aber ein Gate, das bei Unsinn
    „bestanden" sagt, ist schlimmer als eines, das abstürzt.

    Behoben durch Normierung auf die grösste Komponente **vor** dem Quadrieren. Das ist
    mathematisch folgenlos, weil der Kosinus längeninvariant ist — das ist seine
    definierende Eigenschaft — und macht die Rechnung für jede endliche Eingabe
    überlauffrei.
    """
    grenze = invarianzgrenze(dimension=64, seed=17, von=-200, bis=200)

    assert grenze["stille_faelschungen"] == [], (
        f"stille Fälschung zurück: {grenze['stille_faelschungen'][:3]}")
    assert grenze["sicher_bis"] >= 200, "der ganze geprüfte Bereich muss sicher sein"
    assert grenze["sicher_von"] <= -200


def test_auch_der_unterlauf_ist_weg_und_mit_ihm_die_falsche_diagnose():
    """Dieselbe Normierung behebt den Gegenfall.

    Bei sehr kleinen Komponenten wurde die Norm zu 0, und ``kosinus`` meldete „Nullvektor
    — das Bild wurde nicht gelesen". Der Vektor war in Ordnung; nur die Rechnung war es
    nicht. Ein lauter Abbruch mit falscher Begründung ist besser als ein stiller Treffer,
    aber er schickt die Fehlersuche in die falsche Richtung.

    Der Nullvektor bleibt ein Abbruch — er ist echt.
    """
    grenze = invarianzgrenze(dimension=64, seed=18, von=-200, bis=0)
    assert grenze["laute_abbrueche"] == [], (
        f"Unterlauf bricht weiterhin ab: {grenze['laute_abbrueche'][:3]}")

    # Gegenprobe: der ECHTE Nullvektor meldet weiterhin, und mit derselben Begründung.
    with pytest.raises(StilError, match="Bild wurde nicht gelesen"):
        kosinus([0.0, 0.0, 0.0], [1.0, 2.0, 3.0])


def test_der_alltagsbereich_eines_einbetters_ist_unberuehrt():
    """Damit der Befund nicht grösser gemacht wird als er ist.

    Einbettungskomponenten liegen in der Grössenordnung 1. Über sechs Zehnerpotenzen in
    beide Richtungen ändert sich nichts an der vierzehnten Stelle.
    """
    a, b = zufallsvektoren(19, 128, 2)
    soll = kosinus(a, b)
    for faktor in (1e-6, 1e-3, 1.0, 1e3, 1e6):
        assert kosinus([x * faktor for x in a], b) == pytest.approx(soll, abs=1e-14)


# --------------------------------------------------------------------------------------
# 3 · Wertebereich und Winkel — die Anschauung, die in die Irre führt
# --------------------------------------------------------------------------------------

def test_die_vier_ecken_des_wertebereichs():
    """Gleich, fast gleich, rechtwinklig, entgegengesetzt — an gebauten Vektoren."""
    ecken = grenzfaelle(DIM, seed=20)
    assert ecken["gleich"] == pytest.approx(1.0)
    assert ecken["fast_gleich"] == pytest.approx(1.0, abs=1e-3)
    assert ecken["fast_gleich"] < 1.0
    assert ecken["rechtwinklig"] == pytest.approx(0.0, abs=1e-12)
    assert ecken["entgegengesetzt"] == pytest.approx(-1.0)
    assert ecken["doppelte_laenge"] == pytest.approx(1.0)


def test_die_schwelle_als_winkel():
    """Anschaulicher als der Kosinus: Wie weit dürfen zwei Bilder auseinanderstehen?

    Die alte Schwelle 0,30 entsprach **72,5°** — fast ein rechter Winkel, also nahezu
    „beliebig verschieden". Die abgeleitete Schwelle 0,666 entspricht **48,2°**. Der
    Unterschied ist kein Feinschliff: Von „fast rechtwinklig darf es sein" zu „etwa ein
    halber rechter Winkel".
    """
    assert winkel_grad(SCHWELLE_STIL) == pytest.approx(48.24, abs=0.01)
    assert winkel_grad(ALTE_SCHWELLE) == pytest.approx(72.54, abs=0.01)
    assert winkel_grad(1.0) == pytest.approx(0.0)
    assert winkel_grad(0.0) == pytest.approx(90.0)
    assert winkel_grad(-1.0) == pytest.approx(180.0)


def test_derselbe_kosinus_bedeutet_in_zwei_und_in_768_dimensionen_gegenteiliges():
    """**Der Befund über die Instrumente dieses Projekts selbst.**

    ``tests/test_stil_qa.py`` baut jeden Prüfvektor in **zwei** Dimensionen
    (``vektor_mit_kosinus``). Als Prüfung der Arithmetik ist das richtig und bleibt es.
    Als Anschauung für die Schwelle ist es irreführend:

    * In zwei Dimensionen erreicht ein guter Teil aller zufälligen Vektorpaare die
      Schwelle — sie ist dort ein weiter Kegel und trennt wenig.
    * In 768 Dimensionen erreicht es **keines** von hunderten — dieselbe Zahl ist dort
      eine sehr scharfe Grenze.

    Eine Kosinus-Schwelle hat also keine von der Dimension unabhängige Bedeutung, und wer
    ein Gefühl für sie aus zweidimensionalen Testvektoren zieht, zieht das falsche.

    *Der Befund gilt unverändert für die neue Schwelle — nur die Anteile verschieben sich.
    Und er ist die zweite Hälfte der Erklärung dafür, wie 0,30 so lange bestehen konnte:
    In den zweidimensionalen Prüfvektoren sah die Zahl streng aus.*
    """
    zweid = nullverteilung(2, n_proben=1000, seed=21)
    hochd = nullverteilung(768, n_proben=300, seed=21)
    # Anteil in der Ebene: der Winkel ist gleichverteilt, also acos(schwelle)/180°.
    assert zweid["anteil_ueber_schwelle"] == pytest.approx(
        winkel_grad(SCHWELLE_STIL) / 180.0, abs=0.05)
    assert zweid["anteil_ueber_schwelle"] > 0.2
    assert hochd["anteil_ueber_schwelle"] == 0.0


# --------------------------------------------------------------------------------------
# 4 · Referenzsatz und Aggregation
# --------------------------------------------------------------------------------------

def test_kohaerenz_erkennt_einen_heterogenen_referenzsatz():
    """Der Kennwert, den ein Büro **ohne jedes Modell** an seinem eigenen Satz messen kann.

    Er beantwortet die Frage, die ``stil_qa`` aufwirft, ohne sie zu beantworten: Ist
    dieses Referenzset homogen genug, dass ``max`` und ``mittel`` dasselbe messen?
    """
    aufbau = baue_referenzsatz(dimension=DIM, n_auspraegungen=4, je_auspraegung=2, seed=22)
    heterogen = aufbau["kohaerenz"]
    assert heterogen["n"] == 8
    assert heterogen["n_paare"] == 28
    assert heterogen["homogen"] is False
    assert heterogen["spreizung"] > 0.5

    homogen = baue_referenzsatz(dimension=DIM, n_auspraegungen=1, je_auspraegung=6,
                                naehe=0.95, seed=22)["kohaerenz"]
    assert homogen["homogen"] is True
    assert homogen["mittlere_aehnlichkeit"] > heterogen["mittlere_aehnlichkeit"]


def test_kohaerenz_einer_einzelnen_referenz_ist_ein_fehler():
    """Bei einer Referenz sind max und mittel ohnehin dasselbe — eine Kohärenz gibt es nicht."""
    with pytest.raises(StilstudieError, match="mindestens zwei"):
        kohaerenz([[1.0, 0.0]])


def test_eine_einzige_untypische_referenz_oeffnet_das_gate():
    """``stil_qa`` nennt diese Schwäche im Fliesstext. Hier steht die Zahl dazu.

    Dasselbe Bild, derselbe Massstab, ein Referenzbild mehr im Satz: Der Score springt von
    „durchgefallen" auf „bestanden". Der Referenzsatz ist damit selbst ein Prüfgegenstand.
    """
    vergleich = aggregationsvergleich(dimension=DIM, seed=23)
    befund = vergleich["befunde"]["eine_referenz_oeffnet_das_gate"]
    assert befund["kippt"] is True
    assert befund["vorher"] < SCHWELLE_STIL
    assert befund["nachher"] > 0.7


def test_mittel_laesst_das_stiltreue_bild_durchfallen():
    """0,30 mit ``mittel`` ist nicht dieselbe Schwelle, nur strenger — es ist eine andere.

    Ein Bild, das eine Ausprägung des Hausstils genau trifft, besteht mit ``max`` (0,73)
    und fällt mit ``mittel`` durch (0,12). Nicht weil es schlecht wäre, sondern weil der
    Satz heterogen ist.
    """
    vergleich = aggregationsvergleich(dimension=DIM, seed=24)
    befund = vergleich["befunde"]["mittel_bestraft_das_stiltreue_bild"]
    assert befund["faellt_durch"] is True
    assert befund["max"] > SCHWELLE_STIL
    assert befund["mittel"] < SCHWELLE_STIL


def test_ein_zusammenhangloses_bild_faellt_unter_beiden_aggregationen_durch():
    """Die Gegenprobe. Ohne sie wäre der Befund oben nur „mittel ist streng"."""
    vergleich = aggregationsvergleich(dimension=DIM, seed=25)
    fremd = [z for z in vergleich["zeilen"] if z["bild"] == "ohne_zusammenhang"]
    assert fremd, "das Prüfbild ohne Zusammenhang fehlt"
    for zeile in fremd:
        assert zeile["bestanden_max"] is False
        assert zeile["bestanden_mittel"] is False


def test_die_verduennung_ist_exakt_und_braucht_keinen_zufall():
    """Die schärfste Aussage der Aggregationsfrage ist eine Zeile Arithmetik.

    Trifft ein Bild genau eine Referenz perfekt und steht zu allen übrigen rechtwinklig,
    ist der ``mittel``-Score ``1/n``. **Ab vier Referenzen liegt er unter 0,30** — ein
    perfekter Treffer fällt durch, weil der Satz gewachsen ist.
    """
    assert mittel_bei_teiltreffer(1, 1) == pytest.approx(1.0)
    assert mittel_bei_teiltreffer(3, 1) == pytest.approx(1 / 3)
    assert mittel_bei_teiltreffer(4, 1) == pytest.approx(0.25)
    assert mittel_bei_teiltreffer(4, 1) < SCHWELLE_STIL
    assert mittel_bei_teiltreffer(8, 2, 0.9) == pytest.approx(0.225)


def test_die_verduennung_stimmt_mit_der_gemessenen_aggregation_ueberein():
    """Die Arithmetik gegen die gebauten Vektoren gehalten — Formel und Messung, nicht eines von beiden."""
    einheit = [1.0] + [0.0] * 7
    orthogonale = [[1.0 if i == k else 0.0 for i in range(8)] for k in range(1, 8)]
    satz = [einheit, *orthogonale]
    gemessen = stil_score(einheit, satz, aggregation=AGG_MITTEL)["score"]
    assert gemessen == pytest.approx(mittel_bei_teiltreffer(8, 1))
    assert stil_score(einheit, satz, aggregation=AGG_MAX)["score"] == pytest.approx(1.0)


@pytest.mark.parametrize("n_referenzen,n_treffer", [(0, 0), (3, 4), (3, -1)])
def test_unmoegliche_teiltreffer_sind_ein_fehler(n_referenzen, n_treffer):
    with pytest.raises(StilstudieError):
        mittel_bei_teiltreffer(n_referenzen, n_treffer)


# --------------------------------------------------------------------------------------
# 5 · Wiederholbarkeit und Fehlereingaben
# --------------------------------------------------------------------------------------

def test_derselbe_startwert_liefert_dieselben_zahlen():
    """Eine Studie, die sich nicht wiederholen lässt, ist keine."""
    eins = nullverteilung(64, n_proben=50, seed=42)["kennzahlen"]
    zwei = nullverteilung(64, n_proben=50, seed=42)["kennzahlen"]
    assert eins == zwei


def test_ein_anderer_startwert_liefert_andere_zahlen():
    """Gegenprobe: Sonst wäre die Wiederholbarkeit nur ein eingefrorener Wert."""
    eins = nullverteilung(64, n_proben=50, seed=42)["kennzahlen"]["mittel"]
    zwei = nullverteilung(64, n_proben=50, seed=43)["kennzahlen"]["mittel"]
    assert eins != zwei


def test_der_referenzsatz_ist_wiederholbar():
    assert (baue_referenzsatz(dimension=32, seed=44)["satz"]
            == baue_referenzsatz(dimension=32, seed=44)["satz"])


@pytest.mark.parametrize("kwargs", [
    {"dimension": 1},
    {"dimension": 0},
    {"dimension": 16, "n_referenzen": 0},
    {"dimension": 16, "kegelanteil": -0.1},
    {"dimension": 16, "kegelanteil": 1.5},
    {"dimension": 16, "kegelanteil": 1.0},
    {"dimension": 16, "aggregation": "median"},
    {"dimension": 16, "n_proben": 1},
])
def test_unbrauchbare_angaben_brechen_ab_statt_zu_raten(kwargs):
    """Kein stiller Rückfall auf eine Vorgabe. Der Aufrufer meinte etwas anderes."""
    kwargs.setdefault("n_proben", 10)
    with pytest.raises(StilstudieError):
        nullverteilung(**kwargs)


def test_kegelanteil_eins_ist_keine_verteilung_mehr():
    """Alle Vektoren zeigen exakt gleich — dann gibt es nur noch eine Konstante."""
    with pytest.raises(StilstudieError, match="Konstante"):
        nullverteilung(16, kegelanteil=1.0, n_proben=10)


@pytest.mark.parametrize("wert", [1.5, -1.5])
def test_winkel_ausserhalb_des_wertebereichs_ist_ein_fehler(wert):
    with pytest.raises(StilstudieError):
        winkel_grad(wert)


def test_unbrauchbarer_referenzsatz_ist_ein_fehler():
    with pytest.raises(StilstudieError):
        baue_referenzsatz(dimension=16, n_auspraegungen=0)
    with pytest.raises(StilstudieError):
        baue_referenzsatz(dimension=16, naehe=1.0)


# --------------------------------------------------------------------------------------
# 6 · Der Studienlauf
# --------------------------------------------------------------------------------------

def test_studienlauf_traegt_alle_teile_und_seine_eigenen_grenzen():
    """Ein Ergebnis, das ohne seine Einschränkungen zitierbar wäre, wäre gefährlich.

    Darum reist ``was_nicht_gemessen_wurde`` mit den Zahlen mit — die Geometriestudie
    musste dieselbe Lehre nachträglich ziehen.
    """
    lauf = studienlauf(dimension=64, dimensionen=(32, 64), n_proben=60, seed=45)
    assert set(lauf) >= {"boden", "kegel", "max_reihe", "invarianz", "grenzfaelle",
                         "aggregation", "kontrollen_bestanden", "was_nicht_gemessen_wurde"}
    assert lauf["kontrollen_bestanden"] is True
    assert lauf["einbetter_vorgabe"] == einbetter.VORGABE_EINBETTER
    assert "menschliches Urteil" in lauf["was_nicht_gemessen_wurde"]


def test_das_ergebnis_ist_regel_3_tauglich():
    """Nur Zahlen und Text — kein Bild, kein Pfad, nichts aus einem echten Projekt.

    Dieselbe Prüfung wie bei der Geometriestudie: Das Ergebnis muss unverändert über das
    Repo reisen dürfen.
    """
    lauf = studienlauf(dimension=32, dimensionen=(32,), n_proben=40, seed=46)
    text = json.dumps(lauf, ensure_ascii=False)
    assert len(text) > 500


def test_der_studienlauf_zieht_keine_echten_bilder_heran():
    """Gegenprobe zur Redlichkeit: Nirgends steht ein Dateipfad oder ein Bildname.

    Die Studie misst Eigenschaften der Metrik. Käme hier je ein Pfad vor, hätte jemand
    angefangen, echte Daten hineinzuziehen — und das wäre Regel 3 und zugleich das Ende
    der Aussage, dass hier nichts über echte Bilder behauptet wird.
    """
    text = json.dumps(studienlauf(dimension=32, dimensionen=(32,), n_proben=40, seed=47))
    for verdaechtig in (".png", ".jpg", ".exr", "/home", "referenz_a"):
        assert verdaechtig not in text


# --------------------------------------------------------------------------------------
# 7 · Was die Studie NICHT zeigt — als ausführbare Festlegung
# --------------------------------------------------------------------------------------

def test_die_studie_kennt_kein_einziges_bild():
    """Sie kann darum nicht sagen, ob 0,30 richtige von falschen Bildern trennt.

    Der Quelltext enthält weder einen Bildpfad noch einen Aufruf eines Einbetters. Was
    hier gemessen wird, sind Eigenschaften der Metrik — Tauglichkeit ist etwas anderes,
    und sie braucht echte Bilder und ein menschliches Urteil.
    """
    quelle = (PAKET / "stilstudie.py").read_text(encoding="utf-8")
    baum = ast.parse(quelle)
    aufgerufene = {knoten.func.id for knoten in ast.walk(baum)
                   if isinstance(knoten, ast.Call) and isinstance(knoten.func, ast.Name)}
    assert "stil_gate_aus_bildern" not in aufgerufene
    assert "open" not in aufgerufene


def test_diese_studie_hat_die_schwelle_nicht_veraendert_die_messung_hat_es():
    """Wer die Zahl verschoben hat — und wer nicht.

    Diese Studie liess 0,30 bewusst stehen: Aus synthetischen Vektoren lässt sich keine
    Bildschwelle ableiten, und eine neue geratene Zahl wäre keine Verbesserung gewesen.
    Was sie geliefert hat, ist die **Begründung daneben** und die Anweisung, wo zu messen
    ist.

    Verschoben hat die Zahl erst die Messung am Gerät (`auf-20260818-11`). Genau so soll
    die Reihenfolge sein: erst wissen, woran eine Zahl hängt, dann messen, dann setzen —
    und nicht raten, weil die alte Zahl unbefriedigend aussah.
    """
    assert SCHWELLE_STIL != ALTE_SCHWELLE
    boden = boden_fuer("siglip2-base", "pooler_output")
    assert SCHWELLE_STIL == pytest.approx(schwelle_aus_boden(boden), abs=1e-3)


def test_der_konstanten_kommentar_nennt_die_offene_frage():
    """Wer die Zahl liest, muss am selben Ort erfahren, worauf sie sich stützt — und worauf nicht.

    Jetzt zusätzlich: dass die eine Hälfte gemessen und die andere gesetzt ist. Der Boden
    sagt, wo Unähnlichkeit **aufhört** — nicht, wo Ähnlichkeit **anfängt**.
    """
    quelle = (PAKET / "stil_qa.py").read_text(encoding="utf-8")
    kopf = quelle.split("SCHWELLE_STIL = ")[0]
    for stichwort in ("Boden", "SigLIP", "Kegel", "stilstudie", "auf-20260818-11"):
        assert stichwort in kopf, f"{stichwort!r} fehlt im Kommentar zur Schwelle"


# --------------------------------------------------------------------------------------
# 8 · Hygiene
# --------------------------------------------------------------------------------------

def test_modul_importiert_nur_stdlib():
    """Regel 4: Die Studie muss überall laufen — ohne GPU, ohne Gewichte, ohne numpy.

    Hier ist der Griff nach ``numpy`` besonders verführerisch: Zehntausende Skalarprodukte
    in reinem Python sind langsam, und ein ``import numpy`` wäre eine Zeile. Damit wäre
    die Studie nur noch dort nachrechenbar, wo numpy liegt.
    """
    quelle = (PAKET / "stilstudie.py").read_text(encoding="utf-8")
    module: set[str] = set()
    for knoten in ast.walk(ast.parse(quelle)):
        if isinstance(knoten, ast.Import):
            module.update(a.name.split(".")[0] for a in knoten.names)
        elif isinstance(knoten, ast.ImportFrom) and knoten.level == 0 and knoten.module:
            module.add(knoten.module.split(".")[0])
    fremd = sorted(m for m in module if m not in sys.stdlib_module_names and m != "aiimaging")
    assert not fremd, f"stilstudie.py importiert {fremd}"


def test_kein_schweres_paket_wird_nachgeladen():
    """Der Quelltext-Scan darüber sieht nur diese eine Datei — hier zählt die ganze Kette.

    ``stilstudie.py`` importiert ``stil_qa`` und ``einbetter``; ein ``import numpy`` dort
    machte die Studie ebenso unrechenbar, ohne dass der Scan oben anschlüge.

    Gemessen in einem **frischen Interpreter** (:func:`conftest.nachgeladene_module`) und
    nicht am ``sys.modules`` des Testlaufs: Das zeigt die Vorgeschichte des Laufs, nicht
    die Folgen dieses Imports. Wo der GPU-Stack installiert ist, hat ihn eine frühere
    Testdatei längst geladen — die Prüfung wäre rot, ohne dass an der Studie etwas falsch
    wäre; wo er fehlt, könnte sie nie rot werden. Ein Test, der nur in einer Umgebung
    gilt, misst die Umgebung und nicht den Code.

    ``statistics`` steht als Zeuge mit in der Liste: Die Studie importiert es, ein nackter
    Interpreter hat es nicht. Bleibt der Zeuge aus, schaut die Sonde ins Leere, und ihr
    Schweigen zu ``torch`` wäre keine Aussage.
    """
    geladen = nachgeladene_module(
        "aiimaging.stilstudie", ("torch", "numpy", "transformers", "statistics"))
    assert "statistics" in geladen, "Die Sonde sieht nicht einmal den Zeugen — sie misst nichts"

    schwer = [m for m in geladen if m != "statistics"]
    assert not schwer, f"{schwer} wurde durch die Stilstudie geladen"


def test_die_aggregationen_der_studie_sind_die_des_gates():
    """Die Studie darf nicht gegen eine eigene Vokabel messen — sonst misst sie etwas anderes."""
    vergleich = aggregationsvergleich(dimension=32, seed=48)
    for zeile in vergleich["zeilen"]:
        bild = zeile["bild"]
        assert bild in ("im_stil", "am_ausreisser", "ohne_zusammenhang")
    assert AGG_MAX == "max" and AGG_MITTEL == "mittel"
