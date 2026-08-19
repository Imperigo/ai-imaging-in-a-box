"""Der Nachweis, dass die Geometrie-QA das trennt, wozu sie gebaut ist.

Der Anlass steht in ``geometrie_qa.py``: Ein reines Stil-Gate meldete ``bestanden``
(0.42) auf eine **halluzinierte** Kubatur. Ein Test, der nur zeigt, dass identische
Karten 1.0 ergeben, hätte diesen Fall ebenfalls durchgelassen. Darum sind die zwei
wichtigsten Tests dieser Datei:

* ``test_halluzination_faellt_durch_obwohl_die_tiefenordnung_stimmt`` — die erfundene
  Kubatur hat im Überlappungsbereich eine **perfekte** Rangkorrelation (1.000) und fällt
  trotzdem durch, weil die Silhouetten sich kaum decken (geom_iou 0.040 → Score 0.199).
* ``test_arithmetisches_mittel_haette_die_halluzination_durchgelassen`` — derselbe Fall
  mit dem naheliegenden Mittelwert gerechnet: 0.520, also fast bestanden. Das ist der
  Beleg für das geometrische Mittel; ohne ihn wäre es Geschmack.

Daneben der Fall, der das rangbasierte Verfahren rechtfertigt:
``test_treue_kubatur_mit_anderem_massstab_und_offset`` — ``ist = 3*soll + 7 + Rauschen``
erreicht 0.999. Ein Absolutvergleich in Metern läge hier bei einem katastrophalen Fehler,
obwohl die Geometrie stimmt.

Alle Tiefenkarten sind synthetisch und hier erzeugt (Regel 3): kein EXR, kein Blender,
keine GPU, kein Netz. Zufall ist mit festem Startwert gezogen, damit jeder Lauf dieselben
Zahlen liefert.
"""
from __future__ import annotations

import ast
import math
import random
import sys
from pathlib import Path

import pytest

from aiimaging import geometrie_qa
from aiimaging.geometrie_qa import (
    DIAGNOSE_IOU_NIEDRIG,
    DIAGNOSE_RHO_HOCH,
    HINTERGRUND_SCHWELLE_M,
    METHODE,
    MIN_GEMEINSAME_PUNKTE,
    SCHWELLE_GEOMETRIE,
    QaError,
    geometrie_gate,
    geometrie_score,
    iou,
    silhouette,
    spearman,
)
from conftest import PAKET

# --------------------------------------------------------------------------------------
# Synthetische Tiefenkarten
# --------------------------------------------------------------------------------------

#: Bildraster. Klein genug für schnelle Tests, gross genug, dass eine Silhouette aus
#: hunderten Punkten besteht und MIN_GEMEINSAME_PUNKTE nicht zufällig unterschritten wird.
BREITE, HOEHE = 64, 48

#: Hintergrundmarke, wie sie ein Renderer für „Strahl hat nichts getroffen“ schreibt.
HINTERGRUND = 1.0e10


def tiefenkarte(x0: int, x1: int, y0: int, y1: int, *,
                grund: float = 20.0, dx: float = 0.05, dy: float = 0.08) -> list[float]:
    """Ein quaderförmiger Baukörper vor leerem Hintergrund, zeilenweise ausgelesen.

    Innerhalb des Rechtecks wächst die Tiefe leicht nach rechts und nach unten — eine
    schräg zur Bildebene stehende Fassade. Das ist der einfachste Fall, der überhaupt
    eine *Reihenfolge* trägt: Eine Fläche mit konstanter Tiefe hätte keine, und die
    Rangkorrelation wäre auf ihr zu Recht nicht definiert.
    """
    return [
        (grund + dx * (x - x0) + dy * (y - y0)) if (x0 <= x < x1 and y0 <= y < y1)
        else HINTERGRUND
        for y in range(HOEHE)
        for x in range(BREITE)
    ]


def abgebildet(karte, funktion) -> list[float]:
    """Wendet ``funktion`` auf die Geometriepunkte an; der Hintergrund bleibt Hintergrund.

    So entstehen die „Ist“-Karten: dieselbe Geometrie, aber in der Skala eines fremden
    Verfahrens. Der Hintergrund darf dabei nicht mitgerechnet werden — sonst wäre er
    keiner mehr, und die Silhouette wanderte.
    """
    return [funktion(w) if w < HINTERGRUND_SCHWELLE_M else HINTERGRUND for w in karte]


def verrauscht(karte, *, faktor: float, offset: float, streuung: float, seed: int):
    """``ist = faktor * soll + offset + Rauschen`` — eine treue, aber fremd skalierte Karte."""
    zufall = random.Random(seed)
    return abgebildet(
        karte, lambda w: faktor * w + offset + zufall.uniform(-streuung, streuung)
    )


#: Der Entwurf: ein Baukörper links der Bildmitte, 24 × 24 Punkte = 576 Geometriepunkte.
SOLL = tiefenkarte(8, 32, 12, 36)

#: Derselbe Bau, in fremder Skala und mit Messrauschen zurückgerechnet. Der Regelfall
#: eines geglückten Renders.
IST_TREU = verrauscht(SOLL, faktor=3.0, offset=7.0, streuung=0.5, seed=20260818)

#: Erfundene Kubatur: ein in sich völlig stimmiges Gebäude — nur woanders, etwas näher
#: und mit leicht anderer Neigung. Die Silhouetten überlappen sich in zwei Spalten.
IST_HALLUZINIERT = tiefenkarte(30, 54, 14, 38, grund=16.0, dx=0.06, dy=0.07)


# --------------------------------------------------------------------------------------
# spearman — gegen Handrechnungen
# --------------------------------------------------------------------------------------

def test_spearman_gleichlaeufig_ist_eins():
    assert spearman([1.0, 2.0, 3.0, 4.0], [10.0, 20.0, 30.0, 40.0]) == 1.0


def test_spearman_perfekt_gegenlaeufig_ist_minus_eins():
    """Handrechnung: umgekehrte Reihenfolge → −1. Das Vorzeichen bleibt hier erhalten."""
    assert spearman([1.0, 2.0, 3.0], [3.0, 2.0, 1.0]) == -1.0


def test_spearman_handbeispiel_null_komma_sechs():
    """Handrechnung ohne Bindungen: d = (−1, 1, −1, 1), Σd² = 4, ρ = 1 − 6·4/(4·15) = 0.6."""
    assert spearman([1.0, 2.0, 3.0, 4.0], [2.0, 1.0, 4.0, 3.0]) == pytest.approx(0.6)


def test_spearman_mit_bindung_nimmt_den_mittleren_rang():
    """Handrechnung mit Bindung: a-Ränge (1.5, 1.5, 3), b-Ränge (1, 2, 3) → ρ = √3/2.

    Mit der Kurzformel ``1 − 6Σd²/(n(n²−1))`` käme hier 0.75 heraus — ein anderer Wert.
    Der Test hält fest, dass die bindungskorrekte Fassung gerechnet wird.
    """
    assert spearman([1.0, 1.0, 2.0], [1.0, 2.0, 3.0]) == pytest.approx(math.sqrt(3) / 2)


def test_spearman_ist_unempfindlich_gegen_massstab_und_offset():
    """Der Kern des Verfahrens: eine affine Umrechnung ändert die Reihenfolge nicht.

    Genau deshalb ist die Metrik rangbasiert — die zurückgerechnete Tiefe kennt weder
    die Meter noch den Nullpunkt der echten Geometrie.
    """
    a = [3.0, 1.0, 4.0, 1.5, 9.0, 2.6]
    b = [1000.0 * w + 7.0 for w in a]
    assert spearman(a, b) == 1.0


def test_spearman_ist_unempfindlich_gegen_jede_monotone_umrechnung():
    """Auch nichtlinear, solange streng steigend: eine Wurzel ändert keinen Rang."""
    a = [3.0, 1.0, 4.0, 1.5, 9.0, 2.6]
    assert spearman(a, [math.sqrt(w) for w in a]) == 1.0


def test_spearman_ist_symmetrisch():
    a = [3.0, 1.0, 4.0, 1.5, 9.0]
    b = [2.0, 8.0, 1.0, 8.0, 3.0]
    assert spearman(a, b) == spearman(b, a)


def test_spearman_bleibt_im_wertebereich():
    zufall = random.Random(7)
    a = [zufall.uniform(-100, 100) for _ in range(200)]
    b = [zufall.uniform(-100, 100) for _ in range(200)]
    assert -1.0 <= spearman(a, b) <= 1.0


def test_spearman_ungleiche_laenge_ist_ein_fehler():
    with pytest.raises(QaError, match="unterschiedlich lang"):
        spearman([1.0, 2.0, 3.0], [1.0, 2.0])


def test_spearman_braucht_mindestens_zwei_punkte():
    with pytest.raises(QaError, match="mindestens 2 Punkte"):
        spearman([1.0], [2.0])


def test_spearman_weist_konstante_folgen_zurueck():
    """Ohne Streuung gibt es keine Reihenfolge — jeder Rückgabewert wäre erfunden."""
    with pytest.raises(QaError, match="konstant"):
        spearman([5.0, 5.0, 5.0], [1.0, 2.0, 3.0])


@pytest.mark.parametrize("kaputt", [float("nan"), float("inf"), float("-inf")])
def test_spearman_weist_nicht_endliche_werte_zurueck(kaputt):
    """NaN und inf sind Hintergrundmarken, keine Tiefen. Sie gehören vorher aussortiert."""
    with pytest.raises(QaError):
        spearman([1.0, 2.0, kaputt], [1.0, 2.0, 3.0])


def test_spearman_weist_text_und_wahrheitswerte_zurueck():
    with pytest.raises(QaError):
        spearman(["1.0", "2.0"], [1.0, 2.0])
    with pytest.raises(QaError):
        spearman([True, False], [1.0, 2.0])


def test_spearman_weist_generatoren_zurueck():
    """Ein Generator wäre nach dem ersten Durchlauf leer — stiller Datenverlust."""
    with pytest.raises(QaError, match="Generator"):
        spearman((w for w in [1.0, 2.0, 3.0]), [1.0, 2.0, 3.0])


# --------------------------------------------------------------------------------------
# silhouette
# --------------------------------------------------------------------------------------

def test_silhouette_trennt_geometrie_vom_hintergrund():
    assert silhouette([12.5, HINTERGRUND, 30.0, HINTERGRUND]) == [True, False, True, False]


@pytest.mark.parametrize("marke", [float("inf"), float("nan"), float("-inf")])
def test_silhouette_wertet_nicht_endliche_werte_als_hintergrund(marke):
    """Ein Strahl, der nichts trifft, liefert je nach Renderer inf oder NaN."""
    assert silhouette([10.0, marke]) == [True, False]


def test_silhouette_nimmt_eine_eigene_marke_entgegen():
    assert silhouette([10.0, 500.0, 999.0], hintergrund=500.0) == [True, False, False]


def test_silhouette_zaehlt_die_marke_selbst_zum_hintergrund():
    """Renderer schreiben die Marke exakt; ``>=`` wäre hier die falsche Grenze."""
    assert silhouette([1.0e10], hintergrund=1.0e10) == [False]


def test_silhouette_haelt_grosse_bauwerksmasse_noch_fuer_geometrie():
    """Ein Kameraabstand von 900 m ist plausibel; die Vorgabemarke liegt bei 1e6 m."""
    assert silhouette([900.0, 999_999.0, HINTERGRUND]) == [True, True, False]


def test_silhouette_haelt_negative_werte_fuer_geometrie():
    """Manche Verfahren zählen Tiefe mit umgekehrtem Vorzeichen. Ein Nullpunkt wird nicht
    angenommen — eine falsche Annahme schnitte halbe Baukörper stumm heraus."""
    assert silhouette([-5.0, 0.0, 5.0]) == [True, True, True]


def test_silhouette_weist_unbrauchbare_marken_zurueck():
    with pytest.raises(QaError):
        silhouette([1.0], hintergrund=0.0)
    with pytest.raises(QaError):
        silhouette([1.0], hintergrund=float("nan"))
    with pytest.raises(QaError):
        silhouette([1.0], hintergrund="viel")


def test_silhouette_der_synthetischen_karte_hat_die_erwartete_groesse():
    """Vorbedingung aller weiteren Tests: 24 × 24 Punkte tragen Geometrie."""
    assert sum(silhouette(SOLL)) == 576


# --------------------------------------------------------------------------------------
# iou
# --------------------------------------------------------------------------------------

def test_iou_identisch_ist_eins():
    assert iou([True, True, False], [True, True, False]) == 1.0


def test_iou_disjunkt_ist_null():
    assert iou([True, False], [False, True]) == 0.0


def test_iou_haelfte():
    """Zwei Punkte gemeinsam, vier in der Vereinigung → 0.5."""
    assert iou([True, True, True, False], [False, True, True, True]) == 0.5


def test_iou_ist_symmetrisch():
    a = [True, False, True, True]
    b = [True, True, False, False]
    assert iou(a, b) == iou(b, a)


def test_iou_zweier_leerer_silhouetten_ist_ein_fehler():
    """0/0. Zwei leere Bilder sind nicht 'perfekt gleich', sondern ungeprüft."""
    with pytest.raises(QaError, match="nicht definiert"):
        iou([False, False], [False, False])


def test_iou_weist_zahlen_zurueck():
    """Fängt den wahrscheinlichsten Fehlgriff: Tiefenkarten statt Silhouetten übergeben."""
    with pytest.raises(QaError, match="Wahrheitswert"):
        iou([1.0, 0.0], [True, False])


def test_iou_ungleiche_laenge_ist_ein_fehler():
    with pytest.raises(QaError, match="unterschiedlich lang"):
        iou([True, False], [True])


# --------------------------------------------------------------------------------------
# geometrie_score — die vier Fälle, um die es geht
# --------------------------------------------------------------------------------------

def test_identische_tiefenkarten_ergeben_eins():
    ergebnis = geometrie_score(SOLL, list(SOLL))
    assert ergebnis["score"] == pytest.approx(1.0)
    assert ergebnis["spearman"] == pytest.approx(1.0)
    assert ergebnis["geom_iou"] == 1.0
    # Genau eine Warnung, und sie ist lehrreich: Diese Testkarte trägt nur auf 18.8 %
    # der Punkte Geometrie und liegt damit selbst in dem Bereich, in dem die Schwelle
    # unerreichbar wäre. Für Soll-gegen-Soll ist das gleichgültig; für ein erzeugtes
    # Bild wäre es der ganze Unterschied.
    assert [w for w in ergebnis["warnungen"] if "Geringer Geometrieanteil" in w]
    # Seit dem 21.08. kommt eine zweite dazu, und zwar bei JEDEM ungerichteten Score:
    # ohne gemessene Polarität ist er nicht monoton im geometrischen Fehler. Das gilt
    # auch hier — nur fällt es an Soll-gegen-Soll nicht auf, weil es keinen Fehler gibt.
    assert [w for w in ergebnis["warnungen"] if "NICHT MONOTON" in w]
    assert len(ergebnis["warnungen"]) == 2, ergebnis["warnungen"]


def test_mit_gemessener_polaritaet_faellt_der_monotonie_vorbehalt_weg():
    ergebnis = geometrie_score(SOLL, list(SOLL),
                               polaritaet=geometrie_qa.POLARITAET_TIEFE)

    assert ergebnis["score"] == pytest.approx(1.0)
    assert ergebnis["polaritaet"] == 1
    assert "gerichtet" in ergebnis["methode"]
    assert not [w for w in ergebnis["warnungen"] if "NICHT MONOTON" in w]


def test_treue_kubatur_mit_anderem_massstab_und_offset():
    """Der Fall, der das rangbasierte Verfahren rechtfertigt.

    ``ist = 3 · soll + 7 + Rauschen``: In Metern gerechnet wäre der Fehler gewaltig
    (aus 20 m werden 67 m), die Geometrie stimmt aber vollständig. Gemessen: 0.995.
    """
    ergebnis = geometrie_score(SOLL, IST_TREU)
    assert ergebnis["score"] > 0.8
    assert ergebnis["score"] == pytest.approx(0.9946, abs=0.002)
    assert ergebnis["geom_iou"] == 1.0
    assert ergebnis["n_gemeinsam"] == 576


@pytest.mark.parametrize("streuung, mindestens", [(0.15, 0.99), (0.5, 0.98), (1.0, 0.95), (2.0, 0.9)])
def test_treue_kubatur_bleibt_auch_bei_stärkerem_rauschen_treu(streuung, mindestens):
    """Die Rangkorrelation bricht unter Rauschen langsam ein, nicht schlagartig.

    Bei ±2.0 übersteigt das Rauschen den Tiefenschritt zwischen Nachbarpunkten (0.05)
    um das Vierzigfache — der Score sinkt trotzdem nur auf 0.93. Ränge sind robust,
    weil ein einzelner Ausreisser nur um wenige Plätze verschiebt.
    """
    ist = verrauscht(SOLL, faktor=3.0, offset=7.0, streuung=streuung, seed=20260818)
    assert geometrie_score(SOLL, ist)["score"] > mindestens


def test_treue_kubatur_mit_leichtem_versatz_bleibt_ueber_der_schwelle():
    """Realistischer als der Idealfall: Die zurückgerechnete Silhouette sitzt einen Punkt
    daneben. Der Score fällt von 0.99 auf 0.90 — spürbar, aber weit über der Schwelle.
    Das ist die empirisch beobachtete Bandbreite treuer Renders (0.81–0.93)."""
    versetzt = verrauscht(tiefenkarte(9, 33, 13, 37), faktor=3.0, offset=7.0,
                          streuung=1.0, seed=4711)
    ergebnis = geometrie_score(SOLL, versetzt)
    assert ergebnis["geom_iou"] == pytest.approx(0.849, abs=0.01)
    assert ergebnis["score"] == pytest.approx(0.902, abs=0.01)
    assert ergebnis["score"] > SCHWELLE_GEOMETRIE


def test_halluzination_faellt_durch_obwohl_die_tiefenordnung_stimmt():
    """**Der Daseinsgrund der Metrik.**

    Die erfundene Kubatur ist in sich vollkommen stimmig: Im Überlappungsbereich ist die
    Rangkorrelation exakt 1.000 — ein reines Tiefen-Mass hätte hier Bestnoten vergeben.
    Sie steht nur an der falschen Stelle, und das sieht ``geom_iou``: 0.040. Der Score
    fällt auf 0.199.
    """
    ergebnis = geometrie_score(SOLL, IST_HALLUZINIERT)

    # Erst der Nachweis, dass der Fall wirklich der schwierige ist ...
    assert abs(ergebnis["spearman"]) > 0.9, "Testfall entwertet: Tiefenordnung stimmt nicht"
    assert ergebnis["n_gemeinsam"] >= MIN_GEMEINSAME_PUNKTE, "Testfall entwertet: nicht messbar"
    # ... und dann, dass die Silhouette ihn trotzdem fängt.
    assert ergebnis["geom_iou"] < 0.1
    assert ergebnis["score"] < 0.3
    assert ergebnis["score"] == pytest.approx(0.199, abs=0.01)


def test_arithmetisches_mittel_haette_die_halluzination_durchgelassen():
    """Warum das geometrische Mittel — als Rechnung, nicht als Behauptung.

    Derselbe halluzinierte Fall: ``(|ρ| + IoU)/2 = 0.520``, also mehr als das Doppelte
    des tatsächlichen Scores und nahe an der Schwelle. Ein Mittelwert lässt einen
    perfekten Anteil den ausgefallenen ausgleichen; genau das darf hier nicht passieren.
    """
    ergebnis = geometrie_score(SOLL, IST_HALLUZINIERT)
    arithmetisch = (abs(ergebnis["spearman"]) + ergebnis["geom_iou"]) / 2.0
    assert arithmetisch > 0.5
    assert ergebnis["score"] < arithmetisch / 2.0


def test_das_muster_wird_benannt_und_nicht_gedeutet():
    """Der Befund steht im Klartext — mit **beiden** Ursachen, nicht mit einer.

    Bis zum 18.08.2026 nannte diese Warnung genau eine Ursache: eine erfundene Kubatur.
    Die Deutung war zu sicher. `auf-20260818-10` hat dasselbe Muster an einem Bild
    gemessen, das die Geometrie **exakt zeigt** — |spearman| 0.990 bei geom_iou 0.261 —,
    und die Ursache lag in der Silhouettenauswahl, nicht im Bild.

    *Eine Warnung, die eine von zwei möglichen Ursachen als die einzige ausgibt, schickt
    jemanden an die falsche Stelle. Das kostet mehr als gar keine Warnung.*
    """
    ergebnis = geometrie_score(SOLL, IST_HALLUZINIERT)
    text = " ".join(ergebnis["warnungen"])
    assert "Innen stimmig, aussen daneben" in text
    assert "erfundene Kubatur" in text            # Ursache (a)
    assert "Silhouettenauswahl" in text           # Ursache (b)
    assert "trennen" in text                      # und die Metrik kann es nicht
    assert abs(ergebnis["spearman"]) >= DIAGNOSE_RHO_HOCH
    assert ergebnis["geom_iou"] <= DIAGNOSE_IOU_NIEDRIG


def test_die_warnung_sagt_woran_die_beiden_ursachen_zu_unterscheiden_sind():
    """Ein Verdacht kostet jedes Mal einen Menschen, der nachsieht — eine Diagnose sagt ihm, wo.

    Wenn die Metrik zwei Ursachen nicht trennen kann, muss sie wenigstens sagen, woran es
    ein Mensch kann: am Ort der überzähligen Punkte im Bild.
    """
    text = " ".join(geometrie_score(SOLL, IST_HALLUZINIERT)["warnungen"])
    assert "Bildecke" in text
    assert "34 %" in text                          # die gemessene Zahl, nicht eine runde


def test_invertierte_tiefe_wird_aufgefangen():
    """Disparität (nah = grosser Wert) ist eine Konvention, kein Geometriefehler.

    ``ist = 1/soll`` kehrt jeden Rang um: ρ = −1. Gewertet wird der Betrag, der Score
    bleibt 1.0 — das Vorzeichen erscheint aber als Warnung, weil es auch eine echte
    Vorne-Hinten-Vertauschung bedeuten könnte.
    """
    invertiert = abgebildet(SOLL, lambda w: 1.0 / w)
    ergebnis = geometrie_score(SOLL, invertiert)
    assert ergebnis["spearman"] == pytest.approx(-1.0)
    assert ergebnis["score"] == pytest.approx(1.0)
    assert any("negativ" in w for w in ergebnis["warnungen"])


def test_score_ist_symmetrisch_in_soll_und_ist():
    """Beide Anteile sind symmetrisch; die Reihenfolge der Argumente darf nichts ändern."""
    hin = geometrie_score(SOLL, IST_TREU)
    zurueck = geometrie_score(IST_TREU, SOLL)
    assert hin["score"] == pytest.approx(zurueck["score"])
    assert hin["geom_iou"] == zurueck["geom_iou"]


def test_score_veraendert_die_eingaben_nicht():
    soll = list(SOLL)
    ist = list(IST_TREU)
    geometrie_score(soll, ist)
    assert soll == list(SOLL) and ist == list(IST_TREU)


def test_score_traegt_den_rechenweg_mit():
    """Wer eine Zahl später in der Arbeit wiederfindet, soll ihr die Herkunft ansehen."""
    assert geometrie_score(SOLL, IST_TREU)["methode"] == METHODE


# --------------------------------------------------------------------------------------
# geometrie_score — nicht messbare Fälle. Kein stilles 0 und kein stilles 1.
# --------------------------------------------------------------------------------------

def test_ohne_gemeinsame_silhouette_gibt_es_keinen_score():
    """Die Halluzination im Extremfall: kein einziger gemeinsamer Punkt.

    ``None`` statt 0.0 — nicht aus Zimperlichkeit, sondern weil 0.0 eine Messung
    behauptete, die nicht stattfand. Das Gate lässt den Fall trotzdem nicht durch.
    """
    woanders = tiefenkarte(36, 60, 14, 38, grund=16.0)
    ergebnis = geometrie_score(SOLL, woanders)
    assert ergebnis["score"] is None
    assert ergebnis["n_gemeinsam"] == 0
    assert ergebnis["geom_iou"] == 0.0
    assert any("Keine gemeinsame Silhouette" in w for w in ergebnis["warnungen"])
    assert geometrie_gate(SOLL, woanders)["bestanden"] is False


def test_zu_kleine_gemeinsame_silhouette_gibt_keinen_score():
    """22 gemeinsame Punkte liegen unter der Mindestzahl — der Score bliebe Rauschen."""
    knapp_daneben = tiefenkarte(31, 55, 14, 38, grund=16.0)
    ergebnis = geometrie_score(SOLL, knapp_daneben)
    assert 0 < ergebnis["n_gemeinsam"] < MIN_GEMEINSAME_PUNKTE
    assert ergebnis["score"] is None
    assert any("zu klein" in w for w in ergebnis["warnungen"])
    assert geometrie_gate(SOLL, knapp_daneben)["bestanden"] is False


def test_leere_sollkarte_wird_benannt_statt_bewertet():
    """Eine leere Szene ist kein bestandener und kein durchgefallener Render."""
    leer = [HINTERGRUND] * len(SOLL)
    ergebnis = geometrie_score(leer, IST_TREU)
    assert ergebnis["n_soll"] == 0
    assert ergebnis["score"] is None
    assert any("Soll-Tiefenkarte trägt keine Geometrie" in w for w in ergebnis["warnungen"])


def test_zwei_leere_karten_ergeben_kein_urteil():
    """0/0 in der Überdeckung: weder 0.0 noch 1.0 wäre eine Feststellung."""
    leer = [HINTERGRUND] * 100
    ergebnis = geometrie_score(leer, [float("nan")] * 100)
    assert ergebnis["score"] is None
    assert ergebnis["geom_iou"] is None
    assert any("nicht definiert" in w for w in ergebnis["warnungen"])


def test_konstante_tiefe_in_der_ueberlappung_ergibt_keinen_score():
    """Eine Fläche exakt parallel zur Bildebene trägt keine Reihenfolge.

    Der Score bleibt ``None`` statt 0.0: Nicht die Geometrie ist falsch, sondern die
    Frage hier unbeantwortbar.
    """
    flach = [(25.0 if w < HINTERGRUND_SCHWELLE_M else HINTERGRUND) for w in SOLL]
    ergebnis = geometrie_score(flach, list(flach))
    assert ergebnis["geom_iou"] == 1.0
    assert ergebnis["score"] is None
    assert ergebnis["spearman"] is None
    assert any("nicht berechenbar" in w for w in ergebnis["warnungen"])


def test_nan_punkte_gelten_als_hintergrund_und_stuerzen_nicht_ab():
    """Ausfälle der Tiefenschätzung schrumpfen die Silhouette — sie brechen nichts."""
    # Die ersten 200 Punkte INNERHALB der Silhouette ausfallen lassen — der leere
    # Bildrand davor wäre kein Test, er ist ohnehin Hintergrund.
    innen = [k for k, w in enumerate(SOLL) if w < HINTERGRUND_SCHWELLE_M][:200]
    loechrig = [float("nan") if k in set(innen) else w for k, w in enumerate(IST_TREU)]
    ergebnis = geometrie_score(SOLL, loechrig)
    assert ergebnis["score"] is not None
    assert ergebnis["n_ist"] < ergebnis["n_soll"]


def test_ungleich_lange_karten_sind_ein_fehler():
    """Kein Abschneiden: Wer kürzt, verschiebt die Zuordnung aller Punkte danach."""
    with pytest.raises(QaError, match="unterschiedlich lang"):
        geometrie_score(SOLL, IST_TREU[:-1])


def test_leere_karten_sind_ein_fehler():
    with pytest.raises(QaError, match="leer"):
        geometrie_score([], [])


# --------------------------------------------------------------------------------------
# geometrie_gate — das Urteil
# --------------------------------------------------------------------------------------

def test_gate_laesst_den_treuen_render_durch():
    urteil = geometrie_gate(SOLL, IST_TREU)
    assert urteil["bestanden"] is True
    assert urteil["schwelle"] == SCHWELLE_GEOMETRIE
    assert "≥" in urteil["begruendung"]


def test_gate_haelt_die_halluzination_auf():
    urteil = geometrie_gate(SOLL, IST_HALLUZINIERT)
    assert urteil["bestanden"] is False
    assert urteil["score"] < SCHWELLE_GEOMETRIE
    assert "Innen stimmig, aussen daneben" in " ".join(urteil["warnungen"])


def test_die_schwelle_trennt_beide_faelle():
    """Der eigentliche Zweck der Zahl 0.65 — beide Seiten geprüft, nicht nur eine.

    Zwischen 0.199 (halluziniert) und 0.995 (treu) liegt eine breite Lücke; die Schwelle
    darin ist plausibel, aber an wenigen Fällen kalibriert (siehe Modul-Docstring und
    ``docs/PLAN.md``, Phase 4).
    """
    treu = geometrie_score(SOLL, IST_TREU)["score"]
    halluziniert = geometrie_score(SOLL, IST_HALLUZINIERT)["score"]
    assert halluziniert < SCHWELLE_GEOMETRIE < treu
    assert geometrie_gate(SOLL, IST_TREU)["bestanden"] is True
    assert geometrie_gate(SOLL, IST_HALLUZINIERT)["bestanden"] is False


def test_gate_nimmt_eine_eigene_schwelle():
    """Damit die Schwellenstudie in Phase 4 die Grenze verschieben kann, ohne den
    Rechenweg anzufassen."""
    assert geometrie_gate(SOLL, IST_HALLUZINIERT, schwelle=0.1)["bestanden"] is True
    assert geometrie_gate(SOLL, IST_TREU, schwelle=0.999)["bestanden"] is False


def test_gate_reicht_die_hintergrundmarke_durch():
    """``**kw`` ist kein Zierrat: Renderer schreiben verschiedene Marken."""
    # 12 Wiederholungen à 3 Geometriepunkte = 36 > MIN_GEMEINSAME_PUNKTE. Mit 10
    # Wiederholungen bliebe der Score None — die Mindestzahl greift auch hier.
    soll = [10.0, 20.0, 30.0, 500.0] * 12
    ist = [1.0, 2.0, 3.0, 500.0] * 12
    urteil = geometrie_gate(soll, ist, hintergrund=500.0)
    assert urteil["n_soll"] == 36 and urteil["n_ist"] == 36
    assert urteil["bestanden"] is True


def test_gate_wertet_nicht_messbar_als_nicht_bestanden():
    """Ein Freispruch aus Mangel an Messung wäre die teuerste Sorte Fehler — niemand
    sucht danach. Der Torwächter hält es genauso: ungeprüft wird nicht durchgelassen."""
    leer = [HINTERGRUND] * len(SOLL)
    urteil = geometrie_gate(SOLL, leer)
    assert urteil["score"] is None
    assert urteil["bestanden"] is False
    assert "Nicht messbar" in urteil["begruendung"]


def test_gate_traegt_alle_felder_des_scores_weiter():
    urteil = geometrie_gate(SOLL, IST_TREU)
    assert set(urteil) == {
        "bestanden", "schwelle", "begruendung",
        "score", "spearman", "geom_iou",
        "n_gemeinsam", "n_soll", "n_ist", "anteil_soll", "methode", "polaritaet",
            "warnungen",
    }


@pytest.mark.parametrize("schwelle", [-0.1, 1.5, float("nan"), "hoch", True])
def test_gate_weist_unbrauchbare_schwellen_zurueck(schwelle):
    with pytest.raises(QaError):
        geometrie_gate(SOLL, IST_TREU, schwelle=schwelle)


def test_gate_reicht_eingabefehler_durch():
    """Ein Aufruffehler bleibt ein Fehler und wird nicht zu 'nicht bestanden' geglättet."""
    with pytest.raises(QaError):
        geometrie_gate(SOLL, IST_TREU[:-1])


# --------------------------------------------------------------------------------------
# Die bekannten Grenzen — als Test festgehalten, damit sie nicht in Vergessenheit geraten
# --------------------------------------------------------------------------------------

def test_massstabsblindheit_ist_bekannt_und_gewollt():
    """Grenze 2 des Modul-Docstrings, hier belegt statt behauptet.

    Eine entlang der Sichtachse gestauchte Kubatur (``ist = log(soll)``) behält die
    Tiefen*reihenfolge* und erreicht darum fast 1.0 — obwohl die Proportionen in
    Blickrichtung nicht stimmen. Wer diese Fehlerklasse fangen will, braucht eine zweite
    Grösse; die Rangkorrelation kann es prinzipiell nicht.
    """
    gestaucht = abgebildet(SOLL, math.log)
    assert geometrie_score(SOLL, gestaucht)["score"] > 0.99


def test_metrik_kennt_keine_nachbarschaft():
    """Grenze 4: Die Punkte sind eine Menge, kein Bild.

    Dieselbe Silhouette und dieselbe Tiefenordnung, aber räumlich durcheinander — die
    Metrik sieht keinen Unterschied, weil sie punktweise vergleicht und Kanten,
    Zusammenhang und Glattheit nicht kennt.
    """
    zufall = random.Random(99)
    punkte = [k for k, w in enumerate(SOLL) if w < HINTERGRUND_SCHWELLE_M]
    werte = [SOLL[k] for k in punkte]
    zufall.shuffle(werte)
    gemischt = list(SOLL)
    for k, wert in zip(punkte, werte):
        gemischt[k] = wert
    # Gegen sich selbst gemessen ist die gewürfelte Karte perfekt — obwohl sie kein
    # Gebäude mehr zeigt, sondern Rauschen in Gebäudeform.
    assert geometrie_score(gemischt, list(gemischt))["score"] == pytest.approx(1.0)


# --------------------------------------------------------------------------------------
# Hygiene: reine stdlib
# --------------------------------------------------------------------------------------

def test_modul_importiert_nur_stdlib():
    """Regel 4 in ihrer praktischen Form: Die Metrik muss überall laufen.

    Ein ``import numpy`` hier bände den wissenschaftlichen Kern an eine Umgebung mit
    schweren Binärpaketen — deren Lizenzen zudem ungeprüft sind (``docs/PLAN.md``,
    Wissensschulden). Der Test ist billig und fängt genau den bequemen Moment ab.
    """
    quelle = (PAKET / "geometrie_qa.py").read_text(encoding="utf-8")
    module: set[str] = set()
    for knoten in ast.walk(ast.parse(quelle)):
        if isinstance(knoten, ast.Import):
            module.update(a.name.split(".")[0] for a in knoten.names)
        elif isinstance(knoten, ast.ImportFrom) and knoten.level == 0 and knoten.module:
            module.add(knoten.module.split(".")[0])
    fremd = sorted(m for m in module if m not in sys.stdlib_module_names and m != "aiimaging")
    assert not fremd, f"geometrie_qa.py importiert {fremd} — die Metrik ist reine Mathematik"


# ======================================================================================
# Randlose Silhouette — die Zahl, die gut aussieht und leer ist
# ======================================================================================

def test_eine_silhouette_ueber_das_ganze_bild_wird_gemeldet():
    """`auf-20260819-15`, Szene mit Bodenebene bis zum Horizont: geom_iou exakt 1.0000,
    weil n_soll gleich der Bildpunktzahl war. Es gab keinen Hintergrund mehr.

    Eine Silhouette, die das ganze Bild ist, überdeckt jede andere, die das ganze Bild
    ist. Der Wert 1.0 misst dort nichts.
    """
    soll = [1.0, 2.0, 3.0, 4.0]
    ist = [1.0, 2.0, 3.0, 4.0]
    urteil = geometrie_score(soll, ist)
    assert urteil["geom_iou"] == 1.0
    assert urteil["n_soll"] == urteil["n_ist"] == 4
    warnung = [w for w in urteil["warnungen"] if "Randlose Silhouette" in w]
    assert warnung, urteil["warnungen"]
    assert "KEIN Beleg" in warnung[0]
    assert "auf-20260819-15" in warnung[0], "die Messung gehört in die Meldung"


def test_mit_hintergrund_entsteht_die_warnung_nicht():
    soll = [1.0, 2.0, float("inf"), float("inf")]
    ist = [1.0, 2.0, float("inf"), float("inf")]
    urteil = geometrie_score(soll, ist)
    assert urteil["geom_iou"] == 1.0
    assert not [w for w in urteil["warnungen"] if "Randlose Silhouette" in w], (
        "hier ist 1.0 echt verdient — die Hälfte des Bildes ist Hintergrund")


def test_auch_eine_einseitig_randlose_karte_wird_gemeldet():
    """Wenn nur die Ist-Karte randlos ist, ist der Vergleich ebenso wenig aussagekräftig
    — und der Text nennt, welche der beiden es war."""
    soll = [1.0, 2.0, float("inf"), float("inf")]
    ist = [1.0, 2.0, 3.0, 4.0]
    urteil = geometrie_score(soll, ist)
    warnung = [w for w in urteil["warnungen"] if "Randlose Silhouette" in w]
    assert warnung and "Ist (" in warnung[0] and "Soll (" not in warnung[0]


# ======================================================================================
# Erreichbarkeit — die Frage, die drei Aufträge früher hätte gestellt werden müssen
# ======================================================================================

def test_die_schwelle_war_auf_der_szene_ohne_boden_unerreichbar():
    """**Der Befund, der seit dem 18.08.2026 in den Zahlen stand.**

    Alle Renderläufe dieses Projekts liefen auf dem Testbau *ohne Boden*. Dort deckelt
    ``geom_iou`` bei 0.256 (`wie_soll`) bzw. 0.406 (`ohne_randberuehrung`) — gemessen an
    einem *gerenderten* Bild, also am bestmöglichen Fall. Bei einer Rangkorrelation von
    0.998 ergibt das höchstens 0.505 bzw. 0.636.

    Die Schwelle liegt bei 0.65. **Sie war dort arithmetisch unerreichbar**, und ein
    durchgefallenes Bild belegte nichts über seine Geometrietreue.
    """
    for strategie in ("wie_soll", "ohne_randberuehrung"):
        urteil = geometrie_qa.erreichbarkeit_fuer("ohne_boden", strategie)
        assert urteil["erreichbar"] is False, strategie
        assert urteil["hoechster_score"] < geometrie_qa.SCHWELLE_GEOMETRIE
        assert "UNERREICHBAR" in urteil["begruendung"]
        assert "belegt hier NICHTS" in urteil["begruendung"]


def test_mit_boden_ist_die_schwelle_erreichbar():
    """Und zwar deutlich — der Deckel liegt bei 0.98 statt bei 0.64."""
    for szene in ("platte_endlich", "ebene_bis_rand", "ebene_mit_horizont"):
        urteil = geometrie_qa.erreichbarkeit_fuer(szene, "wie_soll")
        assert urteil["erreichbar"] is True, szene
        assert urteil["hoechster_score"] > 0.95


def test_die_formel_ist_die_umkehrung_des_scores():
    """Kein neues Verfahren, nur die Umstellung von score = sqrt(|rho| * iou)."""
    import math
    for schwelle in (0.5, 0.65, 0.9):
        for rho in (1.0, 0.9, 0.7):
            iou = geometrie_qa.noetiges_iou(schwelle, rho)
            assert math.sqrt(rho * iou) == pytest.approx(schwelle)


def test_bei_perfekter_ordnung_verlangt_die_schwelle_das_quadrat():
    assert geometrie_qa.noetiges_iou(0.65, 1.0) == pytest.approx(0.4225)


def test_eine_schlechtere_ordnung_verlangt_mehr_ueberdeckung():
    """Die beiden Grössen ersetzen einander nicht — das geometrische Mittel lässt keine
    von beiden die andere ausgleichen."""
    assert (geometrie_qa.noetiges_iou(0.65, 0.85)
            > geometrie_qa.noetiges_iou(0.65, 1.0))


def test_eine_ungemessene_kombination_bekommt_keine_schaetzung():
    """Ein geratener Deckel wäre genau die Sorte Zahl, gegen die dieses Modul antritt."""
    assert geometrie_qa.erreichbarkeit_fuer("gibtsnicht", "wie_soll") is None
    assert geometrie_qa.erreichbarkeit_fuer("ohne_boden", "quantil") is None


def test_die_luecke_wird_beziffert_und_nicht_nur_behauptet():
    urteil = geometrie_qa.erreichbarkeit_fuer("ohne_boden", "ohne_randberuehrung")
    assert urteil["luecke"] == pytest.approx(
        urteil["noetiges_iou"] - geometrie_qa.IOU_DECKEL[("ohne_boden",
                                                          "ohne_randberuehrung")])
    assert urteil["luecke"] > 0


def test_erreichbar_heisst_nicht_erreicht():
    """Die Prüfung sagt, ob die Frage sinnvoll ist — nicht, wie sie ausgeht."""
    urteil = geometrie_qa.erreichbarkeit_fuer("platte_endlich", "wie_soll")
    assert "sagt das NICHT" in urteil["begruendung"]


@pytest.mark.parametrize("schwelle, rho", [(-0.1, 1.0), (1.1, 1.0), (0.65, 0.0)])
def test_unbrauchbare_eingaben_werden_abgewiesen(schwelle, rho):
    with pytest.raises(QaError):
        geometrie_qa.noetiges_iou(schwelle, rho)


def test_ein_deckel_ausserhalb_von_null_bis_eins_wird_abgewiesen():
    with pytest.raises(QaError, match="iou_deckel"):
        geometrie_qa.erreichbarkeit(iou_deckel=1.5)


# ======================================================================================
# Der Geometrieanteil — aus der Karte abgelesen statt aus der Szene geraten
# ======================================================================================

def test_der_geometrieanteil_steht_im_ergebnis():
    """Er ist der beste Vorhersager des Deckels, den wir haben — und er kostet nichts."""
    hg = float("inf")
    soll = [1.0, 2.0, hg, hg, hg, hg, hg, hg, hg, hg]
    ergebnis = geometrie_score(soll, soll)
    assert ergebnis["anteil_soll"] == pytest.approx(0.2)


def test_ein_geringer_anteil_wird_gewarnt_mit_der_messung_dabei():
    """`auf-20260819-15`: Bei 17 % Geometrieanteil deckelt geom_iou bei 0.256, ab 60 %
    bei 0.967. Der Anteil ist ablesbar, die Szene nicht."""
    hg = float("inf")
    soll = [1.0] + [hg] * 19            # 5 %
    warnung = [w for w in geometrie_score(soll, soll)["warnungen"]
               if "Geringer Geometrieanteil" in w]
    assert warnung
    assert "UNERREICHBAR" in warnung[0]
    assert "auf-20260819-15" in warnung[0]
    assert "ungemessen" in warnung[0], "die Lücke zwischen 20 % und 60 % gehört dazu"


def test_ein_hoher_anteil_wird_nicht_gewarnt():
    hg = float("inf")
    soll = [1.0] * 15 + [hg] * 5        # 75 %
    assert not [w for w in geometrie_score(soll, soll)["warnungen"]
                if "Geringer Geometrieanteil" in w]


def test_die_marken_sind_die_gemessenen_und_keine_gerundeten():
    """Vier Punkte sind keine Kurve — es stehen die untere und die obere Marke da,
    nicht eine Formel dazwischen."""
    assert geometrie_qa.ANTEIL_GEMESSEN_NIEDRIG == 0.20
    assert geometrie_qa.ANTEIL_GEMESSEN_HOCH == 0.60


def test_eine_leere_sollkarte_warnt_nicht_zweimal_ueber_dasselbe():
    """Ohne Geometrie gibt es schon eine eigene, deutlichere Warnung."""
    hg = float("inf")
    warnungen = geometrie_score([hg] * 10, [1.0] * 10)["warnungen"]
    assert [w for w in warnungen if "trägt keine Geometrie" in w]
    assert not [w for w in warnungen if "Geringer Geometrieanteil" in w]


# ======================================================================================
# Nullanker — weisses Rauschen besteht das Gate
# ======================================================================================

def test_weisses_rauschen_besteht_das_gate():
    """**Der schwerste Befund dieses Moduls** (`auf-20260820-21`, 20.08.2026).

    Auf der Szene ``platte_endlich`` erreicht weisses Rauschen **0.7217** — mehr als die
    Schwelle 0.65 und mehr als jeder der fünf echten Läufe derselben Messung.

    Der Grund liegt nicht am Rauschen: Ein monokularer Schätzer legt in *jedes* Bild eine
    zum Horizont laufende Bodenebene (`auf-20260818-10`). Eine Szene mit 60 % Boden **ist**
    im Wesentlichen so eine Rampe — die Rangkorrelation misst dann zwei Bodenrampen
    gegeneinander und nicht das Bauwerk.
    """
    anker = geometrie_qa.anker_fuer("platte_endlich")
    assert anker[geometrie_qa.ANKER_RAUSCHEN] > geometrie_qa.SCHWELLE_GEOMETRIE


def test_der_eine_lauf_ueber_dem_gate_lag_unter_dem_rauschen():
    """0.6568 bestand die Schwelle — und liegt trotzdem 24,8 % unter dem Rauschanker.

    Ein Wert, den Rauschen übertrifft, belegt keine Geometrietreue. Auch dann nicht, wenn
    er die Schwelle überschreitet.
    """
    urteil = geometrie_qa.einordnung(0.6568,
                                     geometrie_qa.anker_fuer("platte_endlich"))
    assert urteil["ueber_gate"] is True
    assert urteil["ueber_rauschen"] is False
    assert urteil["anteil_der_spanne"] < 0
    assert "belegt keine Geometrietreue" in urteil["begruendung"]


def test_die_perfekte_geometrie_geht_die_ganze_spanne():
    urteil = geometrie_qa.einordnung(0.9839,
                                     geometrie_qa.anker_fuer("platte_endlich"))
    assert urteil["ueber_rauschen"] is True
    assert urteil["anteil_der_spanne"] == pytest.approx(1.0)


def test_ohne_anker_gibt_es_keine_einordnung_sondern_deren_fehlen():
    """Eine geschätzte Einordnung wäre schlimmer als keine — sie sähe aus wie ein Urteil."""
    urteil = geometrie_qa.einordnung(0.9, None)
    assert urteil["ueber_rauschen"] is None
    assert urteil["anteil_der_spanne"] is None
    assert "KEINE Nullprobe" in urteil["begruendung"]
    assert urteil["ueber_gate"] is True, "die Schwelle allein lässt sich weiter prüfen"


def test_die_meldung_ohne_anker_nennt_die_groessenordnung():
    """Damit niemand 'kein Anker' für 'wahrscheinlich egal' hält."""
    urteil = geometrie_qa.einordnung(0.7, None)
    assert "0.72" in urteil["begruendung"]
    assert "mehr als das Gate" in urteil["begruendung"]


def test_kein_score_heisst_nichts_einzuordnen():
    urteil = geometrie_qa.einordnung(None, geometrie_qa.anker_fuer("platte_endlich"))
    assert urteil["ueber_rauschen"] is None
    assert "nichts einzuordnen" in urteil["begruendung"]


def test_eine_ungemessene_szene_bekommt_keinen_fremden_anker():
    assert geometrie_qa.anker_fuer("ohne_boden") is None
    assert geometrie_qa.anker_fuer("platte_endlich") is not None


def test_die_anker_sind_geordnet_wie_die_bilder():
    """Perfekt > Rauschen > Grau > strukturloser Verlauf. Wäre die Ordnung anders,
    hätte die Nullprobe selbst einen Fehler."""
    a = geometrie_qa.NULLANKER["platte_endlich"]
    assert a["beauty"] > a["rauschen"] > a["grau"] > a["verlauf"]


# ======================================================================================
# Der Zusammenhang ist NICHT monoton — und eine feste Schwelle kann es nicht geben
# ======================================================================================

def test_die_mitte_hat_die_niedrigste_decke_von_dreien():
    """`auf-20260820-22`: „Zwischen den beiden Fehlerbereichen liegt der gute Bereich"
    war zu einfach gedacht.

    Bei 29,1 % Geometrieanteil erreicht das perfekte Bild nur 0.415 — weniger als bei
    17 % (0.504) und weit weniger als bei 59,8 % (0.984).
    """
    mitte = geometrie_qa.erreichbarkeit_fuer("platte_11m", "wie_soll")
    viel = geometrie_qa.erreichbarkeit_fuer("platte_endlich", "wie_soll")
    wenig = geometrie_qa.erreichbarkeit_fuer("ohne_boden", "wie_soll")
    assert mitte["hoechster_score"] < wenig["hoechster_score"] < viel["hoechster_score"]


def test_die_mitte_trennt_trotzdem_am_besten():
    """Niedrigste Decke und beste Trennung zugleich — beides gehört in denselben Satz."""
    def verhaeltnis(szene):
        a = geometrie_qa.NULLANKER[szene]
        return a["beauty"] / a[geometrie_qa.ANKER_RAUSCHEN]

    assert verhaeltnis("platte_11m") > verhaeltnis("platte_endlich")


def test_bei_29_prozent_besteht_rauschen_das_gate_nicht_mehr():
    """Die gute Nachricht der Messung — und die halbe."""
    anker = geometrie_qa.anker_fuer("platte_11m")
    assert anker[geometrie_qa.ANKER_RAUSCHEN] < geometrie_qa.SCHWELLE_GEOMETRIE
    # Aber das perfekte Bild besteht es auch nicht.
    assert anker["beauty"] < geometrie_qa.SCHWELLE_GEOMETRIE


def test_der_alte_szenenunabhaengigkeits_test_war_tautologisch():
    """**Ein grüner Test, der eine Unwahrheit dokumentierte** — und der Grund dafür.

    Bis zum 21.08. stand hier ein Test namens
    `test_der_anteil_der_spanne_ist_die_szenenunabhaengige_groesse`. Er setzte in beide
    Szenen den Mittelwert zwischen Rauschanker und perfekt ein und stellte fest, dass
    beide Male 0.5 herauskommt. Das war grün, und es bewies **nichts**: Der Anteil ist
    als lineare Abbildung von [rauschen, beauty] auf [0, 1] definiert, also trifft ihre
    Mitte per Konstruktion 0.5. In beiden Szenen. In jeder Szene. Auch in einer, in der
    die Normierung völlig falsch wäre.

    Geprüft wurde die Umkehrfunktion der eigenen Definition, nicht die Behauptung im
    Namen. Genau die Fehlerart, gegen die die Vakuumprobe antritt — nur dass sie hier
    nicht greift, weil die Zusicherung ja etwas prüft, bloss nicht das Behauptete.
    """
    for szene in ("platte_11m", "platte_endlich"):
        anker = geometrie_qa.anker_fuer(szene)
        mitte = anker[geometrie_qa.ANKER_RAUSCHEN] + 0.5 * (
            anker["beauty"] - anker[geometrie_qa.ANKER_RAUSCHEN])
        # Immer noch 0.5 — und immer noch ohne jede Aussage über Szenenunabhängigkeit.
        assert geometrie_qa.einordnung(mitte, anker)["anteil_der_spanne"] == pytest.approx(0.5)


def test_die_szenenunabhaengigkeit_ist_gemessen_und_widerlegt():
    """Die echte Prüfung: DERSELBE geometrische Fehler in beiden Szenen.

    Nicht derselbe *Anteil* — der kommt per Definition gleich heraus —, sondern
    dieselbe Verschiebung von 1 m. Die Messwerte stammen aus `auf-20260820-23`
    (`docs/EMPFINDLICHKEIT_2026-08-20.md`) und sind hier fest eingetragen, weil sie
    eine Messung sind.

    Wäre der Anteil szenenunabhängig, müssten beide Zahlen nahe beieinanderliegen. Sie
    liegen um Faktor 2,3 auseinander.
    """
    a11 = geometrie_qa.anker_fuer("platte_11m")
    a60 = geometrie_qa.anker_fuer("platte_endlich")

    anteil_11 = geometrie_qa.einordnung(0.3184, a11)["anteil_der_spanne"]
    anteil_60 = geometrie_qa.einordnung(0.9617, a60)["anteil_der_spanne"]

    assert anteil_11 == pytest.approx(0.40, abs=0.02)
    assert anteil_60 == pytest.approx(0.92, abs=0.02)
    assert anteil_60 / anteil_11 > 2.0, "derselbe Fehler, mehr als doppelter Anteil"


def test_die_einordnung_erklaert_den_anteil_fuer_ungueltig():
    """Die Widerlegung muss den Aufrufer erreichen, nicht nur den Docstring."""
    urteil = geometrie_qa.einordnung(0.35, geometrie_qa.anker_fuer("platte_11m"))

    assert urteil["anteil_der_spanne"] is not None, "gerechnet wird sie weiter"
    assert urteil["anteil_gilt"] is False, "gedeutet wird sie nicht mehr"
    assert "widerlegt" in urteil["begruendung"]


def test_ueber_rauschen_ueberlebt_die_widerlegung():
    """Was von der Einordnung bleibt — und warum ausgerechnet das.

    `ueber_rauschen` ist ein **Vergleich innerhalb einer Szene**, kein Abstand: Erreicht
    dieses Bild mehr als eines ganz ohne Geometrie, auf derselben Soll-Karte? Diese
    Aussage braucht keine Monotonie und keine Szenenunabhängigkeit; sie braucht nur
    einen gemessenen Anker. Darum trägt sie weiter, während der Anteil fällt.
    """
    a60 = geometrie_qa.anker_fuer("platte_endlich")
    rauschen = a60[geometrie_qa.ANKER_RAUSCHEN]

    assert geometrie_qa.einordnung(rauschen + 0.01, a60)["ueber_rauschen"] is True
    assert geometrie_qa.einordnung(rauschen - 0.01, a60)["ueber_rauschen"] is False


def test_ein_anker_ohne_grau_und_verlauf_ist_trotzdem_brauchbar():
    """Bei 29 % sind beide gar nicht messbar (n_gemeinsam 0) — sie fehlen darum im
    Anker, statt als Null zu erscheinen."""
    anker = geometrie_qa.anker_fuer("platte_11m")
    assert "grau" not in anker and "verlauf" not in anker
    assert geometrie_qa.einordnung(0.35, anker)["anteil_der_spanne"] is not None


# ======================================================================================
# Polarität — der Ausweg aus dem Nicht-Monotonie-Befund vom 20.08.2026
# ======================================================================================
#
# `auf-20260820-23` hat gemessen: Mit `abs(spearman)` gab 2 m Versatz den Score 0.1191
# und 4 m Versatz 0.2301. Mehr Fehler, besserer Score. Der Grund ist geometrisch: `abs()`
# faltet die Skala in der Mitte, der schlechteste Wert liegt bei ρ = 0 statt an einem
# Ende. Diese Tests prüfen die Richtungsentscheidung, nicht die Messung.

def test_die_gemessene_nicht_monotonie_verschwindet_mit_der_polaritaet():
    """Die beiden Zahlen aus `auf-20260820-23`, nachgerechnet.

    Sie sind hier fest eingetragen, weil sie eine MESSUNG sind und keine Erfindung des
    Tests: ρ und `geom_iou` stehen so in `docs/EMPFINDLICHKEIT_2026-08-20.md`.
    """
    zwei_m = (-0.073, 0.1946)      # Versatz 2 m, Szene A
    vier_m = (+0.337, 0.1571)      # Versatz 4 m, Szene A — mehr Fehler

    ungerichtet = [math.sqrt(abs(r) * i) for r, i in (zwei_m, vier_m)]
    gerichtet = [math.sqrt(max(0.0, -1 * r) * i) for r, i in (zwei_m, vier_m)]

    assert ungerichtet[1] > ungerichtet[0], "so war der Befund: mehr Fehler, besserer Score"
    assert gerichtet[1] < gerichtet[0], "gerichtet dreht sich das um"
    assert gerichtet[1] == 0.0, "vollständig verkehrt herum ist 0 und nicht 0.23"


def test_eine_falsch_herum_gedrehte_karte_faellt_auf_null_statt_auf_perfekt():
    """Die eigentliche Lücke: Bisher bestand eine INVERTIERTE Tiefenkarte das Gate.

    Mit `abs()` erreicht sie 1.0 — dasselbe wie eine perfekte. Das ist kein
    Genauigkeitsproblem, sondern ein Loch im Tor: Vorne und hinten vertauscht ist der
    grösstmögliche Geometriefehler und sah bisher aus wie der kleinste.
    """
    invertiert = abgebildet(SOLL, lambda w: 1.0 / w)

    ohne = geometrie_score(SOLL, invertiert)
    mit = geometrie_score(SOLL, invertiert, polaritaet=geometrie_qa.POLARITAET_TIEFE)

    assert ohne["score"] == pytest.approx(1.0)
    assert mit["score"] == 0.0
    assert [w for w in mit["warnungen"] if "falsche Richtung" in w]


def test_bei_disparitaet_ist_das_negative_vorzeichen_der_erwartete_fall():
    """Derselbe Schätzer, richtig deklariert: aus der Warnung wird eine Feststellung."""
    invertiert = abgebildet(SOLL, lambda w: 1.0 / w)
    ergebnis = geometrie_score(SOLL, invertiert,
                               polaritaet=geometrie_qa.POLARITAET_DISPARITAET)

    assert ergebnis["score"] == pytest.approx(1.0)
    assert [w for w in ergebnis["warnungen"] if "ERWARTETE" in w]
    assert not [w for w in ergebnis["warnungen"] if "falsche Richtung" in w]


@pytest.mark.parametrize("pol", [0, 2, -2, 0.5, "tiefe"])
def test_eine_erfundene_polaritaet_wird_abgewiesen(pol):
    """Ein anderer Wert würde den Score SKALIEREN statt ihn zu richten.

    `0` ist der heimtückischste davon: Er machte jeden Score zu 0 und sähe aus wie ein
    Befund. `1.0` und `True` sind dagegen zugelassen, weil sie in Python `+1` SIND und
    sich rechnerisch nicht davon unterscheiden — eine Strenge ohne Fehlerfall dahinter
    wäre Lärm.
    """
    with pytest.raises(geometrie_qa.QaError, match="polaritaet"):
        geometrie_score(SOLL, list(SOLL), polaritaet=pol)


def test_die_polaritaet_von_depth_anything_ist_gemessen_und_nicht_angenommen():
    """Sie steht in einer Tabelle, weil sie zum PAAR aus Schätzer und Soll-Konvention gehört.

    Eine Polarität aus der Modellkarte des Schätzers wäre nur die halbe Auskunft — sie
    hinge davon ab, wie unsere eigene Soll-Karte herum liegt.
    """
    assert geometrie_qa.GEMESSENE_POLARITAET["depth-anything-v2-small"] == -1


def test_ein_einzelner_lauf_bestimmt_keine_polaritaet():
    """Sonst bestimmte man die Polarität aus genau dem Fehler, den man fangen will."""
    antwort = geometrie_qa.polaritaet_aus_messungen([-0.98])

    assert antwort["polaritaet"] is None
    assert antwort["gemessen"] is False


def test_uneinige_laeufe_bestimmen_keine_polaritaet():
    """Eine Polarität, die von Lauf zu Lauf kippt, ist keine Eigenschaft des Schätzers."""
    antwort = geometrie_qa.polaritaet_aus_messungen([-0.98, -0.96, +0.94, -0.97])

    assert antwort["polaritaet"] is None
    assert antwort["einig"] is False
    assert "nicht einig" in antwort["begruendung"]


def test_ein_rho_nahe_null_zaehlt_nicht_als_richtungszeuge():
    """Ein ρ ohne Richtung einer Seite zuzuschlagen wäre geraten und nicht gemessen."""
    antwort = geometrie_qa.polaritaet_aus_messungen([-0.98, -0.96, 0.02, -0.03])

    assert antwort["n"] == 4
    assert antwort["n_gewertet"] == 2
    assert antwort["polaritaet"] is None


def test_die_sechs_treuesten_laeufe_ergeben_disparitaet():
    """Die Messung, aus der `GEMESSENE_POLARITAET` stammt — hier nachvollzogen.

    Sechs Läufe mit kleinem geometrischem Fehler, aus zwei verschiedenen Szenen
    (`auf-20260820-23`). Zwei Szenen, damit die Antwort nicht an einer hängt.
    """
    antwort = geometrie_qa.polaritaet_aus_messungen(
        [-0.962, -0.895, -0.782, -0.998, -0.992, -0.985])

    assert antwort["polaritaet"] == geometrie_qa.POLARITAET_DISPARITAET
    assert antwort["gemessen"] is True
    assert antwort["n_gewertet"] == 6


# ======================================================================================
# Der Maskenweg — ρ nur über die übergebene Teilmenge der Bildpunkte
# ======================================================================================
#
# Anlass ist `auf-20260821-24` (21.08.2026, `docs/MASKE_2026-08-21.md`): Über das ganze
# Bild gerechnet misst die Metrik in einer bodenlastigen Szene im Wesentlichen zwei
# Bodenrampen gegeneinander — weisses Rauschen erreichte dort den Score 0.7217, den
# Rauschanker jener Szene aus `auf-20260820-21/22`. ρ nur über
# die Bauwerkspunkte ist dagegen in beiden gemessenen Szenen streng monoton, und die
# beiden Szenenkurven liegen mit höchstens 0.005 aufeinander.
#
# Diese Tests prüfen den Rechenweg und die Fallunterscheidungen. Sie prüfen NICHT, ob ρ
# über der Maske Halluzination fängt — das ist als `auf-20260821-25` unterwegs und
# ungemessen. Ein Test kann diese Frage auch gar nicht beantworten: Sie hängt daran, was
# ein echter Schätzer auf einem echten Bild tut, und nicht daran, was hier von Hand in
# eine Ist-Karte geschrieben wird.


def bodenlastige_szene() -> tuple[list[float], list[float], list[bool]]:
    """Soll-Karte mit Bodenrampe und Bauwerk, dazu eine Ist-Karte aus reiner Rampe.

    So gebaut, dass der gemessene Mechanismus **im Kleinen nachvollziehbar** wird:

    * Der **Boden** wird nach unten hin näher — eine Rampe, die nur von ``y`` abhängt.
      Genau so eine Rampe legt ein monokularer Schätzer in eine strukturlose Fläche
      (`auf-20260818-10`), und genau darum korrelieren die beiden.
    * Das **Bauwerk** ist eine Fassade, deren Tiefe nur von ``x`` abhängt. Ihre
      Tiefenstaffelung steht damit senkrecht auf der Bodenrampe — sie hat mit ihr nichts
      zu tun, und das ist der Punkt.
    * Die **Ist-Karte** ist die reine Bodenrampe über das ganze Bild, in fremder Skala:
      das Bild, in dem der Schätzer nur Boden gesehen hat.

    Die dritte Rückgabe ist die Maske: ``True`` genau auf den Bauwerkspunkten.
    """
    def boden(y: int) -> float:
        return 40.0 - 0.5 * y

    soll: list[float] = []
    maske: list[bool] = []
    for y in range(HOEHE):
        for x in range(BREITE):
            bauwerk = 8 <= x < 32 and 12 <= y < 36
            soll.append(22.0 + 0.05 * x if bauwerk else boden(y))
            maske.append(bauwerk)
    ist = [3.0 * boden(y) + 7.0 for y in range(HOEHE) for _ in range(BREITE)]
    return soll, ist, maske


def maske_mit_punkten(anzahl: int) -> list[bool]:
    """Eine Maske aus den ersten ``anzahl`` Geometriepunkten von ``SOLL``."""
    sil = silhouette(SOLL)
    maske = [False] * len(sil)
    gewaehlt = 0
    for k, an in enumerate(sil):
        if an and gewaehlt < anzahl:
            maske[k] = True
            gewaehlt += 1
    assert sum(maske) == anzahl, "die Vorbedingung des Tests muss selbst stimmen"
    return maske


#: Maske über den ganzen Baukörper von ``SOLL`` — 576 Punkte, weit über der Mindestzahl.
MASKE_BAUWERK = silhouette(SOLL)


# --------------------------------------------------------------------------------------
# Der Mechanismus, um den es geht
# --------------------------------------------------------------------------------------

def test_ueber_dem_ganzen_bild_misst_die_bodenrampe_sich_selbst():
    """Der Befund vom 21.08.2026, im Kleinen nachgebaut — und was die Maske daran ändert.

    Die Ist-Karte zeigt hier **kein Bauwerk**, sondern nur die Bodenrampe. Über das ganze
    Bild gerechnet sieht das trotzdem nach einem fast perfekten Render aus: Die Silhouette
    ist randlos (``geom_iou`` 1.0, weil beide Karten überall Werte tragen), und die
    Rangkorrelation ist hoch, weil der Boden den grössten Teil des Bildes stellt und sich
    selbst begegnet.

    Über der Maske bleibt davon nichts: Dort steht die Tiefenstaffelung der Fassade
    (nur ``x``) senkrecht auf der Bodenrampe (nur ``y``), und ρ ist exakt 0.

    **Was dieser Test NICHT zeigt.** Er ist kein Beleg, dass ρ über der Maske
    Halluzination fängt. Die Ist-Karte ist hier von Hand gesetzt; auf einem echten Bild
    entscheidet, was ein echter Schätzer an diesen Punkten liefert. Das ist als
    `auf-20260821-25` unterwegs und ungemessen.
    """
    soll, ist, maske = bodenlastige_szene()

    ganzes_bild = geometrie_score(soll, ist, polaritaet=geometrie_qa.POLARITAET_TIEFE)
    ueber_maske = geometrie_qa.rho_ueber_maske(
        soll, ist, maske, polaritaet=geometrie_qa.POLARITAET_TIEFE)

    assert ganzes_bild["score"] > 0.95, "so sieht der Boden aus, der sich selbst misst"
    assert ganzes_bild["geom_iou"] == 1.0
    assert ueber_maske["rho"] == pytest.approx(0.0, abs=1e-9)
    assert ueber_maske["gerichtet"] == pytest.approx(0.0, abs=1e-9)
    assert ueber_maske["n_maske"] == 576
    assert ueber_maske["anteil_maske"] == pytest.approx(576 / (BREITE * HOEHE))


def test_die_gemessenen_maskenkurven_sind_streng_monoton_und_fallen_zusammen():
    """Die Messung aus `auf-20260821-24`, nachvollzogen — beide Behauptungen einzeln.

    Die Zahlen stehen so in ``docs/MASKE_2026-08-21.md`` und sind hier fest eingetragen,
    weil sie eine **Messung** sind und keine Erfindung des Tests: ρ mit Vorzeichen über
    den 44 604 Maskenpunkten, je Versatz, für zwei Szenen mit 29 % und 59.8 %
    Geometrieanteil.

    Geprüft wird, was die Messung behauptet:

    1. **streng monoton** — jeder Meter Versatz kostet, keiner bringt. Das war über dem
       ganzen Bild nicht so (dort: 2 m → 0.1191, 4 m → 0.2301, mehr Fehler und besserer
       Score), und der Kontrast steht am Ende dieses Tests.
    2. **die beiden Szenenkurven fallen zusammen** — höchstens 0.005 Abstand, ohne jede
       Normierung. Genau das sollte ``anteil_der_spanne`` leisten und leistet es nicht.
    3. **der Rauschboden ist keine Null** — auch das schlechteste Glied der Reihe liegt
       noch deutlich vor weissem Rauschen.
    """
    versaetze = (0.0, 0.25, 0.5, 1.0, 2.0, 4.0)
    szene_29 = (-0.9908, -0.9627, -0.9239, -0.8449, -0.7814, -0.7386)
    szene_598 = (-0.9874, -0.9594, -0.9211, -0.8437, -0.7843, -0.7435)
    pol = geometrie_qa.POLARITAET_DISPARITAET

    assert len(szene_29) == len(szene_598) == len(versaetze) == 6

    for name, reihe in (("29 %", szene_29), ("59.8 %", szene_598)):
        gerichtet = [pol * r for r in reihe]
        for k in range(1, len(gerichtet)):
            assert gerichtet[k] < gerichtet[k - 1], (
                f"Szene {name}: {versaetze[k]} m Versatz ist nicht schlechter als "
                f"{versaetze[k - 1]} m — dann wäre die Reihe nicht monoton")

    for k in range(len(versaetze)):
        assert abs(szene_29[k] - szene_598[k]) <= 0.005, (
            f"bei {versaetze[k]} m liegen die beiden Szenenkurven weiter auseinander "
            f"als die gemessenen 0.005")

    boden = pol * geometrie_qa.RAUSCHBODEN_UEBER_MASKE
    for k in range(len(versaetze)):
        assert pol * szene_29[k] > boden, f"{versaetze[k]} m fällt unter den Rauschboden"
        assert pol * szene_598[k] > boden, f"{versaetze[k]} m fällt unter den Rauschboden"

    # Der Kontrast: dieselbe Reihe über dem GANZEN Bild, Szene A, aus
    # `docs/EMPFINDLICHKEIT_2026-08-20.md`. 4 m ist dort besser als 2 m.
    assert 0.2301 > 0.1191, "so war der Befund, den die Maske aufgehoben hat"


def test_der_rauschboden_ueber_der_maske_ist_gemessen_und_keine_null():
    """−0.5207 ist eine Messung und liegt weit weg von 0 — und weit weg von perfekt.

    Wer ρ über der Maske gegen 0 hält, hält es gegen die falsche Zahl: Ein Bild ohne jede
    Geometrie erreicht dort −0.52, weil der Schätzer auch in Rauschen eine Rampe sieht.

    Verglichen wird trotzdem **nicht** selbsttätig: Der Boden gehört zum Paar aus Schätzer
    und Szenenart, und welches Paar vorliegt, weiss der Aufrufer. Ein Ergebnisfeld
    ``ueber_rauschboden`` gäbe es nur um den Preis, diesen Boden für jeden Schätzer zu
    behaupten.
    """
    boden = geometrie_qa.RAUSCHBODEN_UEBER_MASKE
    assert boden == pytest.approx(-0.5207)
    assert -0.9874 < boden < 0.0, "zwischen perfekt und keinem Zusammenhang, nicht bei 0"

    ergebnis = geometrie_qa.rho_ueber_maske(
        SOLL, IST_TREU, MASKE_BAUWERK, polaritaet=geometrie_qa.POLARITAET_TIEFE)
    assert "ueber_rauschboden" not in ergebnis


# --------------------------------------------------------------------------------------
# Die drei Fälle, die nicht dasselbe sind: Maske fehlt / leer / zu klein
# --------------------------------------------------------------------------------------

def test_eine_fehlende_maske_ist_ein_aufruffehler_und_keine_leere_messung():
    """``None`` als „alle Punkte“ zu deuten ergäbe wieder die Rechnung über den Boden."""
    with pytest.raises(QaError, match="AUFRUFEFEHLER"):
        geometrie_qa.rho_ueber_maske(SOLL, IST_TREU, None)


def test_eine_leere_maske_ist_nicht_gemessen_und_weder_null_noch_eins():
    """``None`` heisst in diesem Projekt *kein Wert* — niemals *in Ordnung*.

    Eine leere Maske ist kein Aufrufefehler: Sie kann aus einem Material-ID-Pass kommen,
    in dem das Bauwerk nicht vorkam. Das ist ein Befund über die Maske und kein Urteil
    über das Bild.
    """
    leer = [False] * len(SOLL)
    ergebnis = geometrie_qa.rho_ueber_maske(SOLL, IST_TREU, leer,
                                            polaritaet=geometrie_qa.POLARITAET_TIEFE)

    assert ergebnis["rho"] is None
    assert ergebnis["gerichtet"] is None
    assert ergebnis["n_maske"] == 0
    assert any("NICHT GEMESSEN" in w for w in ergebnis["warnungen"]), ergebnis["warnungen"]


def test_eine_zu_kleine_maske_ist_ein_befund_und_kein_wert():
    """Unter der Mindestzahl wäre ρ Rauschen mit Dezimalpunkt — und ab ihr gibt es einen.

    Die zweite Hälfte gehört dazu: Ohne sie wäre der Test auch dann grün, wenn die
    Funktion **nie** ein ρ lieferte.
    """
    knapp_zu_wenig = geometrie_qa.MIN_MASKENPUNKTE - 1
    zu_klein = geometrie_qa.rho_ueber_maske(SOLL, IST_TREU,
                                            maske_mit_punkten(knapp_zu_wenig))
    gerade_genug = geometrie_qa.rho_ueber_maske(
        SOLL, IST_TREU, maske_mit_punkten(geometrie_qa.MIN_MASKENPUNKTE))

    assert zu_klein["rho"] is None
    assert zu_klein["n_maske"] == knapp_zu_wenig
    assert any("zu klein" in w for w in zu_klein["warnungen"]), zu_klein["warnungen"]
    assert gerade_genug["rho"] is not None, "ein Punkt mehr, und es ist messbar"


def test_die_mindestzahl_ist_dieselbe_wie_fuer_die_gemeinsame_silhouette():
    """Zwei Zahlen für dasselbe Argument liefen mit der Zeit auseinander."""
    assert geometrie_qa.MIN_MASKENPUNKTE == MIN_GEMEINSAME_PUNKTE


# --------------------------------------------------------------------------------------
# Eingaben — streng, wie im ganzen Modul
# --------------------------------------------------------------------------------------

def test_eine_maske_anderer_laenge_wird_nicht_stillschweigend_abgeschnitten():
    """Abschneiden verschöbe die Zuordnung aller Punkte danach."""
    with pytest.raises(QaError, match="unterschiedlich lang"):
        geometrie_qa.rho_ueber_maske(SOLL, IST_TREU, MASKE_BAUWERK[:-1])


def test_die_maske_muss_wahrheitswerte_tragen():
    """0 und 1 als Maske zu deuten wäre die Sorte Reparatur, gegen die das Modul steht."""
    zahlen = [1 if an else 0 for an in MASKE_BAUWERK]
    with pytest.raises(QaError, match="Wahrheitswert"):
        geometrie_qa.rho_ueber_maske(SOLL, IST_TREU, zahlen)


def test_ungleich_lange_karten_sind_auch_im_maskenweg_ein_fehler():
    with pytest.raises(QaError, match="unterschiedlich lang"):
        geometrie_qa.rho_ueber_maske(SOLL, IST_TREU[:-1], MASKE_BAUWERK)


@pytest.mark.parametrize("pol", [0, 2, -2, 0.5, "tiefe"])
def test_eine_erfundene_polaritaet_wird_auch_im_maskenweg_abgewiesen(pol):
    with pytest.raises(QaError, match="polaritaet"):
        geometrie_qa.rho_ueber_maske(SOLL, IST_TREU, MASKE_BAUWERK, polaritaet=pol)


def test_der_maskenweg_veraendert_die_eingaben_nicht():
    soll, ist, maske = list(SOLL), list(IST_TREU), list(MASKE_BAUWERK)
    geometrie_qa.rho_ueber_maske(soll, ist, maske)
    assert soll == list(SOLL) and ist == list(IST_TREU) and maske == list(MASKE_BAUWERK)


def test_nicht_endliche_werte_an_maskenpunkten_werden_mit_dem_bildindex_gemeldet():
    """Der Index muss auf das BILD zeigen und nicht auf die Position in der Auswahl.

    ``spearman`` kennt nur die Auswahl; seine Meldung zeigte auf einen Punkt, den es im
    Bild nicht gibt. Eine Fehlermeldung an der falschen Stelle kostet mehr als keine.
    """
    stelle = MASKE_BAUWERK.index(True)
    kaputt = list(IST_TREU)
    kaputt[stelle] = float("nan")

    ergebnis = geometrie_qa.rho_ueber_maske(SOLL, kaputt, MASKE_BAUWERK)

    assert ergebnis["rho"] is None
    assert ergebnis["n_maske"] == 576, "die Maske bleibt, wie sie übergeben wurde"
    treffer = [w for w in ergebnis["warnungen"] if "NaN oder inf" in w]
    assert treffer, ergebnis["warnungen"]
    assert f"Bildindex {stelle}" in treffer[0]
    assert stelle > 100, "sonst wäre der Bildindex zufällig gleich der Auswahlposition"


def test_konstante_tiefe_in_der_maske_ergibt_keinen_wert():
    """Eine Fläche parallel zur Bildebene trägt keine Reihenfolge — ρ bleibt None."""
    flach = [(25.0 if an else w) for w, an in zip(SOLL, MASKE_BAUWERK)]
    ergebnis = geometrie_qa.rho_ueber_maske(flach, IST_TREU, MASKE_BAUWERK)

    assert ergebnis["rho"] is None
    assert any("nicht berechenbar" in w for w in ergebnis["warnungen"]), ergebnis["warnungen"]


# --------------------------------------------------------------------------------------
# Die Punkte werden DIREKT gewählt — nicht über eine Hintergrundschwelle
# --------------------------------------------------------------------------------------

def test_die_maske_waehlt_die_punkte_direkt_und_nicht_ueber_eine_hintergrundschwelle():
    """Der Grund steht in `auf-20260821-24`: Über die übliche Kette bricht es zusammen.

    Dort erreichte das **perfekte** Bild zwei gemeinsame Punkte, weil die
    Hintergrundstrategie die nächstgelegenen Punkte irgendwo im Bild wählt — und die
    liegen auf dem Boden. Der Maskenweg fragt die Silhouetten darum gar nicht erst.

    Geprüft an der halluzinierten Kubatur: Ihre Silhouette überlappt die Soll-Silhouette
    nur in wenigen Spalten. Der Weg über das ganze Bild wertet nur diese Überlappung, der
    Maskenweg alle übergebenen Punkte.
    """
    ganzes_bild = geometrie_score(SOLL, IST_HALLUZINIERT)
    ueber_maske = geometrie_qa.rho_ueber_maske(SOLL, IST_HALLUZINIERT, MASKE_BAUWERK)

    assert ganzes_bild["n_gemeinsam"] < 100, "die Silhouetten überlappen kaum"
    assert ueber_maske["n_maske"] == 576, "die Maske bleibt vollständig — sie entscheidet"
    assert ueber_maske["rho"] is not None


def test_eine_maske_ueber_das_ganze_bild_wird_gemeldet():
    """Eine Maske, die alles auswählt, wählt nichts aus — und misst wieder den Boden."""
    soll, ist, _ = bodenlastige_szene()
    ergebnis = geometrie_qa.rho_ueber_maske(soll, ist, [True] * len(soll))

    assert ergebnis["n_maske"] == ergebnis["n_bild"]
    assert ergebnis["anteil_maske"] == 1.0
    treffer = [w for w in ergebnis["warnungen"] if "Randlose Maske" in w]
    assert treffer, ergebnis["warnungen"]
    assert "0.72" in treffer[0], "die Messung gehört in die Meldung"


# --------------------------------------------------------------------------------------
# Richtung — das vorzeichenbehaftete ρ, sobald die Polarität gemessen ist
# --------------------------------------------------------------------------------------

def test_ohne_gemessene_polaritaet_gibt_es_keinen_gerichteten_wert():
    """Und das Ergebnis sagt selbst, dass es ohne Richtung nicht monoton wäre.

    Der Satz gehört in die Warnung und nicht nur in den Docstring: Wer den Rückgabewert
    liest, liest den Docstring nicht.
    """
    ergebnis = geometrie_qa.rho_ueber_maske(SOLL, IST_TREU, MASKE_BAUWERK)

    assert ergebnis["rho"] is not None, "gemessen wird trotzdem"
    assert ergebnis["gerichtet"] is None
    assert ergebnis["polaritaet"] is None
    treffer = [w for w in ergebnis["warnungen"] if "NICHT MONOTON" in w]
    assert treffer, ergebnis["warnungen"]
    assert "auf-20260820-23" in treffer[0], "die Messung gehört in die Meldung"


def test_mit_gemessener_polaritaet_wird_das_vorzeichenbehaftete_rho_gewertet():
    """Ein Disparitäts-Schätzer richtig deklariert: aus −1 wird der beste Wert."""
    invertiert = abgebildet(SOLL, lambda w: 1.0 / w)
    ergebnis = geometrie_qa.rho_ueber_maske(
        SOLL, invertiert, MASKE_BAUWERK, polaritaet=geometrie_qa.POLARITAET_DISPARITAET)

    assert ergebnis["rho"] == pytest.approx(-1.0)
    assert ergebnis["gerichtet"] == pytest.approx(1.0)
    assert [w for w in ergebnis["warnungen"] if "ERWARTETE" in w]
    assert not [w for w in ergebnis["warnungen"] if "falsche Richtung" in w]


def test_verkehrt_herum_ist_etwas_anderes_als_kein_zusammenhang():
    """Darum wird ``gerichtet`` NICHT bei 0 abgeschnitten.

    Der Score schneidet ab, weil unter „vollständig verkehrt" nichts Schlechteres in eine
    Wurzel geht. Hier entsteht kein Score — und dann ist der Unterschied zwischen
    ``−1`` (vorne und hinten vertauscht) und ``0`` (gar kein Zusammenhang) ein Befund,
    den wegzuschneiden Auskunft vernichtete.
    """
    invertiert = abgebildet(SOLL, lambda w: 1.0 / w)
    verkehrt = geometrie_qa.rho_ueber_maske(
        SOLL, invertiert, MASKE_BAUWERK, polaritaet=geometrie_qa.POLARITAET_TIEFE)

    soll, ist, maske = bodenlastige_szene()
    ohne_zusammenhang = geometrie_qa.rho_ueber_maske(
        soll, ist, maske, polaritaet=geometrie_qa.POLARITAET_TIEFE)

    assert verkehrt["gerichtet"] == pytest.approx(-1.0)
    assert ohne_zusammenhang["gerichtet"] == pytest.approx(0.0, abs=1e-9)
    assert verkehrt["gerichtet"] < ohne_zusammenhang["gerichtet"]
    assert [w for w in verkehrt["warnungen"] if "falsche Richtung" in w]


# --------------------------------------------------------------------------------------
# Additiv: der bestehende Score bleibt, wie er ist
# --------------------------------------------------------------------------------------

def test_der_maskenweg_liefert_weder_score_noch_geom_iou():
    """Beides mit Grund, und die Gründe sind verschieden.

    ``geom_iou`` **über der Maske** ist bedeutungslos: Innerhalb der Maske trägt die
    Soll-Karte überall Geometrie, die Überdeckung ist dort konstruktionsbedingt 1
    (`auf-20260821-24`, gemessen).

    Ein **Score** aus ρ allein nähme die Antwort auf `auf-20260821-25` vorweg: ``geom_iou``
    war der Halluzinationsfänger, und ob ρ über der Maske dieselbe Arbeit tut, ist
    ungemessen. Wäre die Antwort nein, hätte dieses Modul die Erpressbarkeit wieder
    eingebaut, gegen die ``geom_iou`` gebaut wurde.
    """
    ergebnis = geometrie_qa.rho_ueber_maske(SOLL, IST_TREU, MASKE_BAUWERK)

    assert "geom_iou" not in ergebnis
    assert "score" not in ergebnis
    assert set(ergebnis) == {"rho", "gerichtet", "n_maske", "n_bild", "anteil_maske",
                             "methode", "polaritaet", "warnungen"}


def test_das_ergebnis_traegt_den_eigenen_rechenweg_mit():
    """Drei Rechenwege im selben Modul liefern drei verschiedene Zahlen zum selben Bild."""
    ergebnis = geometrie_qa.rho_ueber_maske(SOLL, IST_TREU, MASKE_BAUWERK)

    assert ergebnis["methode"] == geometrie_qa.METHODE_MASKE
    assert ergebnis["methode"] != METHODE
    assert ergebnis["methode"] != geometrie_qa.METHODE_GERICHTET
    assert "kein Score" in ergebnis["methode"]


def test_der_maskenweg_laesst_den_bestehenden_score_unangetastet():
    """Alle bisher gemessenen Zahlen des Projekts sind mit ``sqrt(|ρ| * geom_iou)``
    entstanden und müssen reproduzierbar bleiben. Ein zweiter Weg ist kein Ersatz.
    """
    assert geometrie_score(SOLL, IST_TREU)["score"] == pytest.approx(0.99459, abs=1e-5)
    assert METHODE.startswith("sqrt(abs(spearman) * geom_iou)")
    assert geometrie_qa.METHODE_GERICHTET.startswith(
        "sqrt(max(0, polaritaet * spearman) * geom_iou)")
