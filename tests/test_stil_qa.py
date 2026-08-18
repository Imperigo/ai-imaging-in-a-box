"""Die Metrik ohne Modell — und die Naht, an der das Modell später einhängt.

``stil_qa.py`` zerfällt in zwei Teile, und die Teilung ist der Grund, warum diese Datei
auf einem Rechner ohne GPU und ohne Gewichte überhaupt etwas belegen kann:

* Die **Metrik** — Kosinus-Ähnlichkeit und Aggregation — ist Arithmetik über
  Zahlenfolgen. Sie wird hier vollständig geprüft, gegen von Hand nachrechenbare
  Vektoren.
* Das **Einbetten** ist eine injizierbare Funktion. Die Attrappe unten (``attrappe``)
  ersetzt DINOv3 durch ein Wörterbuch. Dieselbe Test-Naht wie ``_starte`` in
  ``seams.py``.

Was diese Datei ausdrücklich **nicht** belegt: dass 0.30 die richtige Schwelle ist. Die
Zahl stammt aus wenigen Fällen des Vorläufers; hier wird nur festgehalten, dass die
belegten Wertebereiche (getroffen ~0.5–0.6, verfehlt ~0.06–0.13) auf den erwarteten
Seiten der Schwelle liegen. Ob die Schwelle an echten Bildern trägt, kann ohne
Einbettungsmodell niemand prüfen — die systematische Schwellenstudie steht in
``docs/PLAN.md``.

Alle Vektoren sind synthetisch (Regel 3).
"""
from __future__ import annotations

import ast
import math
import sys
from pathlib import Path

import pytest

from aiimaging.stil_qa import (
    AGG_MAX,
    AGG_MITTEL,
    SCHWELLE_STIL,
    StilError,
    kosinus,
    stil_gate,
    stil_gate_aus_bildern,
    stil_score,
)

#: Zwei Einheitsvektoren im rechten Winkel — von Hand nachrechenbar.
OST = [1.0, 0.0]
NORD = [0.0, 1.0]

#: 45 Grad zwischen beiden: Kosinus = 1/√2 ≈ 0.7071 zu jedem der beiden.
DIAGONAL = [1.0, 1.0]


def vektor_mit_kosinus(ziel: float) -> list[float]:
    """Ein 2D-Vektor, dessen Kosinus-Ähnlichkeit zu :data:`OST` genau ``ziel`` ist.

    ``[cos φ, sin φ]`` mit ``φ = arccos(ziel)``. Damit lassen sich Testfälle an exakt
    der gewünschten Stelle relativ zur Schwelle setzen, statt Zahlen zu raten.
    """
    winkel = math.acos(ziel)
    return [math.cos(winkel), math.sin(winkel)]


# --------------------------------------------------------------------------------------
# 1 · Kosinus — die Mathematik, von Hand nachrechenbar
# --------------------------------------------------------------------------------------

def test_gleiche_richtung_ist_eins():
    assert kosinus(OST, OST) == pytest.approx(1.0)


def test_rechter_winkel_ist_null():
    assert kosinus(OST, NORD) == pytest.approx(0.0)


def test_entgegengesetzt_ist_minus_eins():
    assert kosinus(OST, [-1.0, 0.0]) == pytest.approx(-1.0)


def test_45_grad_ist_ein_durch_wurzel_zwei():
    assert kosinus(OST, DIAGONAL) == pytest.approx(1 / math.sqrt(2))


def test_laenge_spielt_keine_rolle():
    """Gemessen wird der Winkel. Ein dreifach langer Vektor zeigt in dieselbe Richtung.

    Genau deshalb taugt Kosinus für Embeddings: Deren Länge trägt kaum Bedeutung.
    """
    assert kosinus([1.0, 2.0, 3.0], [3.0, 6.0, 9.0]) == pytest.approx(1.0)


def test_symmetrisch():
    assert kosinus(DIAGONAL, NORD) == pytest.approx(kosinus(NORD, DIAGONAL))


def test_ergebnis_bleibt_im_wertebereich():
    """Geklemmt auf [-1, 1]: Fliesskomma liefert bei identischen Vektoren sonst >1.

    Ein Score von 1.0000000000000002 wäre ein Rätsel ohne Ursache — und in einem
    Protokoll ein Beleg, dem niemand mehr traut.
    """
    lang = [0.1] * 1024
    assert -1.0 <= kosinus(lang, lang) <= 1.0
    assert kosinus(lang, lang) == pytest.approx(1.0)


def test_ganzzahlen_sind_zulaessig():
    """Einbettungen kommen als Listen; ob int oder float darin steht, ist Zufall."""
    assert kosinus([1, 0], [1, 0]) == pytest.approx(1.0)


def test_verschiedene_laengen_sind_ein_fehler():
    """Zwei Längen heissen zwei Modelle — ihre Räume sind nicht vergleichbar."""
    with pytest.raises(StilError, match="verschieden lang"):
        kosinus([1.0, 0.0], [1.0, 0.0, 0.0])


def test_nullvektor_ist_ein_fehler_kein_nullscore():
    """0.0 hiesse „kein Zusammenhang" — richtig ist „keine Aussage möglich".

    Ein Nullvektor aus einem Einbettungsmodell heisst praktisch immer: Das Bild wurde
    nicht gelesen. Als 0.0 durchgereicht sähe das aus wie ein gemessener Misserfolg.
    """
    with pytest.raises(StilError, match="Nullvektor"):
        kosinus([0.0, 0.0], OST)


@pytest.mark.parametrize("kaputt", [
    [float("nan"), 1.0],
    [float("inf"), 1.0],
    [],
    "0.5,0.5",
    None,
    [True, False],
    [1.0, "0.5"],
])
def test_unbrauchbare_vektoren_werden_abgewiesen(kaputt):
    """NaN darf keinen Vergleich erreichen: Jeder Vergleich mit NaN ist falsch."""
    with pytest.raises(StilError):
        kosinus(kaputt, [1.0, 1.0])


# --------------------------------------------------------------------------------------
# 2 · Aggregation — max gegen mittel, und was das misst
# --------------------------------------------------------------------------------------

def test_max_nimmt_die_naechste_referenz():
    """``max`` fragt: Sieht das Bild aus wie *irgendeines* der Belegbilder?"""
    ergebnis = stil_score(OST, [NORD, OST, DIAGONAL], aggregation=AGG_MAX)
    assert ergebnis["score"] == pytest.approx(1.0)
    assert ergebnis["beste_referenz"] == 1
    assert ergebnis["schlechteste_referenz"] == 0


def test_mittel_mittelt_ueber_alle_referenzen():
    """``mittel`` fragt: Wie nah ist das Bild am Schwerpunkt des Sets?"""
    ergebnis = stil_score(OST, [NORD, OST], aggregation=AGG_MITTEL)
    assert ergebnis["score"] == pytest.approx(0.5)


def test_max_ist_die_vorgabe():
    """Die Schwelle 0.30 ist mit ``max`` kalibriert — der Default muss dazu passen."""
    assert stil_score(OST, [NORD, OST])["aggregation"] == AGG_MAX
    assert stil_score(OST, [NORD, OST])["score"] == pytest.approx(1.0)


def test_die_beiden_aggregationen_urteilen_bei_heterogenem_set_verschieden():
    """Der Grund für den Default, an Zahlen: ein Treffer in einem gemischten Set.

    Das Bild trifft eine Referenz genau (Kosinus 1.0) und hat zu den drei übrigen keinen
    Zusammenhang. ``max`` sagt „im Stil", ``mittel`` sagt „durchgefallen" — bei
    identischen Daten. Wer die Aggregation wechselt, ohne die Schwelle neu zu bestimmen,
    misst mit einem Massstab, der für etwas anderes geeicht wurde.
    """
    referenzen = [OST, NORD, [0.0, -1.0], [-1.0, 0.0]]
    mit_max = stil_gate(OST, referenzen, aggregation=AGG_MAX)
    mit_mittel = stil_gate(OST, referenzen, aggregation=AGG_MITTEL)

    assert mit_max["bestanden"] is True
    assert mit_mittel["bestanden"] is False
    assert mit_max["score"] > mit_mittel["score"]


def test_streuung_zeigt_ein_heterogenes_referenzset_an():
    """Grosse Streuung heisst: ``max`` und ``mittel`` sagen sehr Verschiedenes.

    Das Referenzset ist damit selbst ein Prüfgegenstand — ``mittel`` ist das Werkzeug,
    mit dem man es prüft.
    """
    homogen = stil_score(OST, [OST, OST])
    heterogen = stil_score(OST, [OST, [-1.0, 0.0]])
    assert homogen["streuung"] == pytest.approx(0.0)
    assert heterogen["streuung"] == pytest.approx(2.0)


def test_einzelwerte_werden_mitgeliefert():
    """Der aggregierte Wert allein sagt nicht, warum er so ausfällt.

    Die spätere Schwellenstudie braucht genau diese Einzelwerte.
    """
    ergebnis = stil_score(OST, [OST, NORD, DIAGONAL])
    assert ergebnis["n_referenzen"] == 3
    assert len(ergebnis["einzelwerte"]) == 3
    assert ergebnis["einzelwerte"][2] == pytest.approx(1 / math.sqrt(2))


def test_leeres_referenzset_ist_ein_fehler():
    """Ohne Belegbilder gibt es keinen Hausstil — ein Score wäre eine erfundene Messung."""
    with pytest.raises(StilError, match="leer"):
        stil_score(OST, [])


def test_unbekannte_aggregation_ist_ein_fehler():
    """Kein stiller Rückfall auf ``max``: Der Aufrufer meinte etwas anderes."""
    with pytest.raises(StilError, match="Aggregation"):
        stil_score(OST, [OST], aggregation="median")


def test_ein_generator_als_referenzset_ist_zulaessig():
    """Referenzen kommen oft aus einer Schleife über ein Verzeichnis."""
    assert stil_score(OST, (v for v in [NORD, OST]))["score"] == pytest.approx(1.0)


# --------------------------------------------------------------------------------------
# 3 · Das Gate
# --------------------------------------------------------------------------------------

def test_schwelle_ist_030():
    assert SCHWELLE_STIL == 0.30


def test_belegter_trefferbereich_besteht():
    """Getroffene Bilder lagen im Vorläufer bei ~0.5–0.6."""
    for ziel in (0.50, 0.55, 0.60):
        urteil = stil_gate(vektor_mit_kosinus(ziel), [OST])
        assert urteil["bestanden"] is True, ziel
        assert urteil["score"] == pytest.approx(ziel)


def test_belegter_fehlbereich_besteht_nicht():
    """Verfehlte Bilder lagen im Vorläufer bei ~0.06–0.13."""
    for ziel in (0.06, 0.10, 0.13):
        urteil = stil_gate(vektor_mit_kosinus(ziel), [OST])
        assert urteil["bestanden"] is False, ziel


def test_genau_auf_der_schwelle_besteht():
    """``>=``: Eine gesetzte Zahl soll nicht ausgerechnet an ihrem eigenen Rand streng sein.

    Der Testfall wird bewusst nicht über einen Vektor mit „genau 0.30" gebaut — ein
    solcher Vektor ist in Fliesskomma nicht konstruierbar (``cos(arccos(0.3))`` landet
    bei 0.29999999999999993). Geprüft wird die Eigenschaft, um die es geht: Ein Score,
    der die Schwelle exakt trifft, besteht. Dass ein Bild diesen Punkt in der Praxis nie
    genau trifft, ist gerade der Grund, warum die Richtung des Vergleichs festgehalten
    gehört statt ausprobiert zu werden.
    """
    vektor = vektor_mit_kosinus(SCHWELLE_STIL)
    score = stil_score(vektor, [OST])["score"]
    assert score == pytest.approx(SCHWELLE_STIL)

    assert stil_gate(vektor, [OST], schwelle=score)["bestanden"] is True


def test_knapp_darunter_besteht_nicht():
    assert stil_gate(vektor_mit_kosinus(SCHWELLE_STIL - 0.01), [OST])["bestanden"] is False


def test_urteil_traegt_seinen_massstab_mit():
    """Ohne Schwelle und Aggregation ist ein protokolliertes ``False`` später nicht deutbar."""
    urteil = stil_gate(OST, [NORD], schwelle=0.5, aggregation=AGG_MITTEL)
    assert urteil["schwelle"] == 0.5
    assert urteil["aggregation"] == AGG_MITTEL
    assert "0.50" in urteil["begruendung"]


def test_eigene_schwelle_verschiebt_das_urteil():
    """Dieselben Daten, anderer Massstab — und das Urteil kippt. Die Schwelle ist gesetzt."""
    vektor = vektor_mit_kosinus(0.4)
    assert stil_gate(vektor, [OST])["bestanden"] is True
    assert stil_gate(vektor, [OST], schwelle=0.9)["bestanden"] is False


@pytest.mark.parametrize("schwelle", [1.5, -2.0, float("nan"), "0.3", True])
def test_unbrauchbare_schwelle_ist_ein_fehler(schwelle):
    """Eine Schwelle ausserhalb [-1, 1] wäre kein Gate, sondern eine offene Tür."""
    with pytest.raises(StilError):
        stil_gate(OST, [OST], schwelle=schwelle)


def test_begruendung_nennt_die_naechste_referenz_beim_durchfallen():
    """Wer nachbessern soll, will wissen, welchem Belegbild der Render am nächsten kam."""
    urteil = stil_gate(vektor_mit_kosinus(0.1), [[-1.0, 0.0], OST])
    assert urteil["bestanden"] is False
    assert "Nr. 1" in urteil["begruendung"]


def test_bestanden_ist_ein_echter_bool():
    """Das Feld wird vom Doppel-Gate strikt auf ``bool`` geprüft — hier entsteht es."""
    assert isinstance(stil_gate(OST, [OST])["bestanden"], bool)


# --------------------------------------------------------------------------------------
# 4 · Die Naht zum Einbettungsmodell
# --------------------------------------------------------------------------------------

def attrappe(pfad):
    """Einbetter-Attrappe: bildet Pfadnamen auf Vektoren ab, ohne DINOv3 und ohne GPU.

    Das ist die ganze Naht. Im Betrieb steht hier der Aufruf des Einbettungsmodells,
    im Test ein Wörterbuch — die Metrik darunter merkt keinen Unterschied.
    """
    tabelle = {
        "treffer.png": vektor_mit_kosinus(0.55),
        "fehlschlag.png": vektor_mit_kosinus(0.09),
        "referenz_a.png": OST,
        "referenz_b.png": [-1.0, 0.0],
    }
    return tabelle[Path(pfad).name]


def test_gate_aus_bildern_laeuft_mit_attrappe_ohne_gewichte():
    """Der Betriebsfall, geprüft ohne Modell: Pfade hinein, Urteil heraus."""
    urteil = stil_gate_aus_bildern(
        "/synthetisch/treffer.png",
        ["/synthetisch/referenz_a.png", "/synthetisch/referenz_b.png"],
        einbetter=attrappe,
    )
    assert urteil["bestanden"] is True
    assert urteil["score"] == pytest.approx(0.55)
    assert urteil["n_referenzen"] == 2


def test_gate_aus_bildern_faellt_durch_wenn_der_stil_verfehlt_ist():
    urteil = stil_gate_aus_bildern(
        "/synthetisch/fehlschlag.png", ["/synthetisch/referenz_a.png"], einbetter=attrappe,
    )
    assert urteil["bestanden"] is False


def test_urteil_nennt_worueber_es_urteilte():
    """Ein protokolliertes Urteil ohne Bezug auf seine Bilder ist später wertlos."""
    urteil = stil_gate_aus_bildern(
        "/synthetisch/treffer.png", ["/synthetisch/referenz_a.png"], einbetter=attrappe,
    )
    assert urteil["bild_pfad"].endswith("treffer.png")
    assert urteil["referenz_pfade"] == ("/synthetisch/referenz_a.png",)


def test_ohne_einbetter_wird_abgebrochen_statt_geraten():
    """Kein Behelfs-Einbetter. Ein Gate auf erfundenen Zahlen ist schlimmer als keines.

    Dieselbe Haltung wie ``finde_ifc_python`` in ``seams.py``, das lieber abbricht als
    auf das falsche Python zurückzufallen.
    """
    with pytest.raises(StilError) as fehler:
        stil_gate_aus_bildern("/synthetisch/treffer.png", ["/synthetisch/referenz_a.png"])
    meldung = str(fehler.value)
    assert "DINOv3" in meldung and "gated" in meldung
    # Die ungeklärte Lizenz gehört mit in die Meldung — sie ist ein offener Punkt (Regel 1).
    assert "Lizenz" in meldung


def test_leeres_referenzset_bricht_ab_bevor_eingebettet_wird():
    """Kein Einbetten ohne Referenzen — das spart im Betrieb einen teuren Modellaufruf."""
    aufrufe = []

    def zaehlender_einbetter(pfad):
        aufrufe.append(pfad)
        return OST

    with pytest.raises(StilError, match="leer"):
        stil_gate_aus_bildern("/synthetisch/treffer.png", [], einbetter=zaehlender_einbetter)
    assert aufrufe == []


def test_ein_einzelner_pfad_statt_einer_liste_wird_abgefangen():
    """``"a.png"`` zerfiele in seine Zeichen — der Einbetter bekäme "/" als Bild.

    Ein häufiger und stiller Fehlgriff: Der Aufruf liefe durch und der Score wäre Unsinn.
    """
    with pytest.raises(StilError, match="einzelner Pfad"):
        stil_gate_aus_bildern("a.png", "b.png", einbetter=attrappe)


def test_kaputter_einbetter_wird_als_solcher_gemeldet():
    """Liefert das Modell keinen brauchbaren Vektor, bricht es hier ab — nicht später."""
    with pytest.raises(StilError):
        stil_gate_aus_bildern("a.png", ["b.png"], einbetter=lambda _p: None)


# --------------------------------------------------------------------------------------
# 5 · Prüfbar ohne GPU — die Eigenschaft, nicht der Behelf
# --------------------------------------------------------------------------------------

def test_stil_qa_laedt_keine_schweren_bibliotheken():
    """``import aiimaging.stil_qa`` zieht weder ``torch`` noch ``numpy`` nach."""
    import aiimaging.stil_qa  # noqa: F401

    schwer = [m for m in ("torch", "numpy", "transformers") if m in sys.modules]
    assert not schwer, f"{schwer} wurde durch die Stil-QA geladen"


def test_stil_qa_importiert_nur_stdlib():
    """Quelltextprobe: Die Metrik bleibt überall nachrechenbar."""
    import aiimaging.stil_qa as modul

    quelle = Path(modul.__file__).read_text(encoding="utf-8")
    module = set()
    for knoten in ast.walk(ast.parse(quelle)):
        if isinstance(knoten, ast.Import):
            module.update(a.name.split(".")[0] for a in knoten.names)
        elif isinstance(knoten, ast.ImportFrom) and knoten.level == 0 and knoten.module:
            module.add(knoten.module.split(".")[0])
    assert module <= {"__future__", "math"}
