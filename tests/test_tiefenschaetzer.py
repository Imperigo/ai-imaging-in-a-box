"""Die Ist-Seite der Geometrie-QA — Registry, Naht, Hintergrundmarke, Bogen zur Metrik.

Was diese Datei belegen kann und was nicht
------------------------------------------
Es gibt hier weder GPU noch Gewichte. Geprüft wird deshalb alles, was **entscheidbar**
ist: die Lizenztabelle, der Ausschluss der drei CC-BY-NC-Grössen, die Hintergrund-
markierung, die Formprüfungen der Naht und der ganze Bogen ``Bild → Schätzung → Urteil``
mit einer Attrappe. **Nicht** belegt ist, wie ein echter Schätzer sich auf einem
Architekturrender verhält — dazu kann dieser Rechner nichts sagen, und diese Datei
behauptet es auch nirgends.

Zwei Tests hier sind Gegenproben, und sie sind der Grund, warum die anderen etwas wert
sind: Ein Ausschlusstest ist vakuös, wenn das Ausgeschlossene gar nicht in der Registry
steht; ein „``torch`` steht nicht auf Modulebene" ist vakuös, wenn ``torch`` nirgends
importiert wird.
"""
from __future__ import annotations

import ast
import math
from pathlib import Path

import pytest

from aiimaging import auftrag, geometrie_qa
from aiimaging import tiefenschaetzer as ts
from aiimaging.lizenzquelle import QUELLE_SEKUNDAER, QUELLE_UNGEPRUEFT, ist_belegt
from conftest import nachgeladene_module

#: Die drei Grössen, die unter Regel 1 ausscheiden. Als Konstante, damit ein späterer
#: Umbau der Registry nicht stillschweigend eine davon fallen lässt.
NC_GROESSEN = (
    "depth-anything-v2-base",
    "depth-anything-v2-large",
    "depth-anything-v2-giant",
)


# --------------------------------------------------------------------------------------
# Testdaten — synthetisch, im Repo erzeugt (Regel 3)
# --------------------------------------------------------------------------------------

def soll_karte(n_geometrie: int = 64, n_himmel: int = 64) -> list[float]:
    """Eine Soll-Tiefenkarte, wie Blender sie liefert: Meter, Himmel als ``inf``.

    Die Geometriepunkte laufen streng monoton von 10 m nach 20 m — damit hat die Karte
    eine eindeutige Tiefenordnung, gegen die eine Schätzung geprüft werden kann. 64
    Geometriepunkte liegen bewusst über ``MIN_GEMEINSAME_PUNKTE`` (32), sonst gäbe die
    Metrik gar keinen Score aus.
    """
    schritt = 10.0 / n_geometrie
    return [10.0 + i * schritt for i in range(n_geometrie)] + [math.inf] * n_himmel


def disparitaets_karte(soll: list[float], himmel: float = 0.001) -> list[float]:
    """Eine **treue, aber invertierte** Schätzung: Disparität statt Meter.

    ``1/tiefe`` ist die Rangumkehr der Tiefe — genau das, was Depth-Anything liefert
    (nah = grosser Wert). Der Himmel bekommt einen kleinen endlichen Wert, denn genau das
    ist der Punkt: Ein Schätzer schreibt dort **kein** ``inf``.
    """
    return [himmel if math.isinf(t) else 1.0 / t for t in soll]


def attrappe(werte, *, breite=None, hoehe=None, mitschrift: list | None = None):
    """Ein Modell im Sinne des Moduls: Wörterbuch hinein, Zahlenfolge heraus.

    Drei Zeilen — genau das ist die Zusage der Naht. Wäre der Vertrag breiter, liesse
    sich der Bogen hier nicht prüfen.
    """
    def modell(parameter: dict):
        if mitschrift is not None:
            mitschrift.append(parameter)
        if breite is None and hoehe is None:
            return list(werte)
        return {"tiefen": list(werte), "breite": breite, "hoehe": hoehe}

    return modell


@pytest.fixture()
def bild(tmp_path) -> Path:
    """Ein Bild, das existiert. Der Inhalt ist gleichgültig — es liest ihn hier niemand."""
    pfad = tmp_path / "render_1.png"
    pfad.write_bytes(b"\x89PNG\r\n\x1a\n")
    return pfad


# --------------------------------------------------------------------------------------
# 1 · Die Registry — Regel 1 in ausführbarer Form
# --------------------------------------------------------------------------------------

@pytest.mark.parametrize("name", NC_GROESSEN)
def test_gegenprobe_die_nc_groessen_stehen_ueberhaupt_in_der_registry(name):
    """Ohne diesen Test wären alle Ausschlusstests vakuös — sie schlössen nichts aus."""
    assert name in ts.TIEFENSCHAETZER


@pytest.mark.parametrize("name", NC_GROESSEN)
def test_die_nc_groessen_sind_nicht_zulaessig(name):
    """CC-BY-NC-4.0 ist NonCommercial und damit keine der vier permissiven Lizenzen."""
    eintrag = ts.TIEFENSCHAETZER[name]
    assert eintrag.lizenz == "CC-BY-NC-4.0"
    assert eintrag.zulaessig is False


@pytest.mark.parametrize("name", NC_GROESSEN)
def test_waehle_gibt_die_nc_groessen_niemals_zurueck(name):
    """Regel 1 im ausführbaren Pfad, nicht nur in der Doku."""
    assert name not in [x.name for x in ts.waehle()]


@pytest.mark.parametrize("name", NC_GROESSEN)
def test_waehle_ohne_filter_zeigt_sie_doch(name):
    """Der Ausschluss soll auffindbar bleiben — sonst wird er in einem Jahr neu diskutiert."""
    assert name in [x.name for x in ts.waehle(nur_zulaessige=False)]


def test_waehle_liefert_genau_die_kleine_variante():
    """Vier Grössen in der Registry, genau eine brauchbar."""
    assert [x.name for x in ts.waehle()] == ["depth-anything-v2-small"]


@pytest.mark.parametrize("name", NC_GROESSEN)
def test_fordere_zulaessigen_lehnt_die_nc_groessen_mit_begruendung_ab(name):
    """Nicht bloss „geht nicht" — der Grund muss in der Meldung stehen."""
    with pytest.raises(ts.TiefenschaetzerError) as fehler:
        ts.fordere_zulaessigen(name)
    meldung = str(fehler.value)
    assert "Regel 1" in meldung
    assert "NonCommercial" in meldung


def test_die_begruendung_nennt_die_geerbte_annahme_aus_kosmovis():
    """Der Grund, warum wir ViT-L nicht übernehmen, gehört an den Datensatz — nicht in ein Protokoll."""
    grund = ts.TIEFENSCHAETZER["depth-anything-v2-large"].begruendung
    assert "KosmoVis" in grund
    assert "ViT-L" in grund


def test_die_begruendung_nennt_dass_die_lizenz_an_der_groesse_haengt():
    """Das ist der überraschende Teil des Befunds — er darf nicht verloren gehen."""
    for name in NC_GROESSEN:
        assert "MODELLGROESSE" in ts.TIEFENSCHAETZER[name].begruendung


def test_vorgabe_ist_zulaessig_und_apache():
    """Die Vorgabe muss ohne Lizenzvorbehalt nutzbar sein, sonst ist das Repo nicht nachvollziehbar."""
    v = ts.hole(ts.VORGABE_TIEFENSCHAETZER)
    assert v.zulaessig and v.lizenz == "Apache-2.0"
    assert ts.VORGABE_TIEFENSCHAETZER == "depth-anything-v2-small"


@pytest.mark.parametrize("name", [n for n, x in ts.TIEFENSCHAETZER.items() if x.zulaessig])
def test_jeder_zulaessige_traegt_eine_erlaubte_lizenz(name):
    """Zulässig und Lizenz dürfen nicht auseinanderlaufen."""
    assert ts.TIEFENSCHAETZER[name].lizenz in ts.ZUGELASSENE_LIZENZEN


def test_die_kleine_variante_ist_wirklich_die_kleinste():
    """Sonst wäre die Vorgabe aus einem anderen Grund gewählt als dem, der im Text steht."""
    klein = ts.hole("depth-anything-v2-small")
    assert all(klein.parameter_m < x.parameter_m
               for x in ts.TIEFENSCHAETZER.values() if x.name != klein.name)


def test_lizenzquelle_ist_bei_allen_vermerkt_und_geprueft():
    """Ein Ausschluss muss belegt sein — 'sekundär gehört' genügt für Regel 1 nicht.

    Gefragt wird seit dem 18.08.2026 über ``ist_belegt`` statt über eine Textprobe auf
    „geprueft": dieselbe Vokabel, die die Registry selbst benutzt, und dieselbe wie in
    ``backbone`` und ``einbetter``. Eine Textprobe beantwortet dieselbe Frage nur
    zufällig mit — und trifft daneben, sobald irgendwo sonst „geprueft" im Satz steht
    (Prüfbericht Abschnitt 5).
    """
    for x in ts.TIEFENSCHAETZER.values():
        assert ist_belegt(x.lizenz_quelle), f"{x.name}: {x.lizenz_quelle!r}"


def _probe(name, lizenz_quelle):
    """Ein synthetischer Eintrag, der nur die Herkunft der Lizenzangabe variiert."""
    return ts.Tiefenschaetzer(name=name, modell_id=f"org/{name}", lizenz="Apache-2.0",
                              zulaessig=True, begruendung="synthetisch", parameter_m=1.0,
                              lizenz_quelle=lizenz_quelle)


@pytest.mark.parametrize("quelle", [QUELLE_UNGEPRUEFT, QUELLE_SEKUNDAER])
def test_eine_unbelegte_angabe_wird_als_solche_gemeldet(monkeypatch, quelle):
    """Der Prüfstand gehört in die Antwort — als Feld, nicht als Textprobe des Aufrufers.

    Synthetisch statt an einem Namen aus dem Bestand: Ein Test über eine Namensliste hält
    einen Schuldenstand fest und wird beim nächsten Beleg zum Hindernis. Genau das ist in
    ``test_backbone.py`` passiert.
    """
    monkeypatch.setitem(ts.TIEFENSCHAETZER, "probe", _probe("probe", quelle))

    urteil = ts.pruefe_lizenz("probe")
    assert urteil["lizenz_belegt"] is False
    assert urteil["lizenz_hinweis"].startswith("Lizenzangabe")


def test_ein_belegter_vermerk_mit_url_gilt_als_beleg(monkeypatch):
    """Die Gegenprobe — ohne sie wäre die Zusicherung oben vakuös.

    Der Giant-Eintrag zeigt, warum die freie Form nötig ist: Sein Beleg ist keine
    Modellkarte, sondern der LICENSE-Abschnitt eines README. Ein Schlagwort „modellkarte"
    wäre dort schlicht falsch.
    """
    monkeypatch.setitem(ts.TIEFENSCHAETZER, "probe",
                        _probe("probe", "geprueft 2026-08-18 (https://example.invalid/mk)"))

    urteil = ts.pruefe_lizenz("probe")
    assert urteil["lizenz_belegt"] is True
    assert urteil["lizenz_hinweis"] is None


@pytest.mark.parametrize("name", NC_GROESSEN)
def test_die_belegfrage_ist_von_der_zulaessigkeit_getrennt(name):
    """Ein Ausschluss ist kein Prüfstand: Die NC-Grössen sind belegt UND unzulässig."""
    urteil = ts.pruefe_lizenz(name)
    assert urteil["zulaessig"] is False
    assert urteil["lizenz_belegt"] is True


def test_pruefe_lizenz_gibt_die_lage_als_daten():
    lage = ts.pruefe_lizenz("depth-anything-v2-large")
    assert lage["zulaessig"] is False
    assert lage["lizenz"] == "CC-BY-NC-4.0"
    assert lage["parameter_m"] == pytest.approx(335.3)


def test_unbekannter_schaetzer_wird_gemeldet():
    with pytest.raises(ts.TiefenschaetzerError, match="Unbekannter Tiefenschaetzer"):
        ts.hole("gibt-es-nicht")


def test_registry_ist_unveraenderlich():
    """``frozen=True``: Ein ``zulaessig = True`` irgendwo im Programm hebelte Regel 1 lautlos aus."""
    with pytest.raises(AttributeError):
        ts.TIEFENSCHAETZER["depth-anything-v2-large"].zulaessig = True


# --------------------------------------------------------------------------------------
# 2 · Die Hintergrundmarke — die eigentliche Entscheidung des Moduls
# --------------------------------------------------------------------------------------

def test_keine_strategie_markiert_nichts_und_sagt_es():
    """Ehrlich, aber strukturell zu streng — und genau das steht in der Unsicherheit."""
    befund = ts.markiere_hintergrund(
        [0.1, 0.2, 0.3, 0.4], polaritaet=ts.POLARITAET_DISPARITAET, strategie=ts.HG_KEINE,
    )
    assert befund["n_hintergrund"] == 0
    assert all(math.isfinite(w) for w in befund["tiefen"])
    assert befund["unsicherheit"], "Auch 'nichts markieren' ist eine Entscheidung mit Folgen"


def test_disparitaet_markiert_die_kleinsten_werte():
    """Bei Disparität ist nah = gross; der Himmel liegt also bei den KLEINSTEN Werten."""
    befund = ts.markiere_hintergrund(
        [0.9, 0.01, 0.8, 0.02], polaritaet=ts.POLARITAET_DISPARITAET,
        strategie=ts.HG_QUANTIL, anteil=0.5,
    )
    assert befund["tiefen"][0] == 0.9 and befund["tiefen"][2] == 0.8
    assert math.isinf(befund["tiefen"][1]) and math.isinf(befund["tiefen"][3])


def test_tiefe_markiert_die_groessten_werte():
    """Bei metrischer Tiefe genau andersherum — die Polarität entscheidet die Seite."""
    befund = ts.markiere_hintergrund(
        [1.0, 900.0, 2.0, 800.0], polaritaet=ts.POLARITAET_TIEFE,
        strategie=ts.HG_QUANTIL, anteil=0.5,
    )
    assert befund["tiefen"][0] == 1.0 and befund["tiefen"][2] == 2.0
    assert math.isinf(befund["tiefen"][1]) and math.isinf(befund["tiefen"][3])


def test_unbekannte_polaritaet_wird_nicht_geraten():
    """Ein Rateschluss schnitte mit halber Wahrscheinlichkeit das Gebäude heraus — lautlos."""
    with pytest.raises(ts.TiefenschaetzerError, match="Polaritaet"):
        ts.markiere_hintergrund(
            [0.1, 0.2], polaritaet=ts.POLARITAET_UNBEKANNT, strategie=ts.HG_QUANTIL,
        )


def test_ohne_markierung_ist_die_unbekannte_polaritaet_kein_hindernis():
    """Wer nichts markiert, muss die Seite auch nicht kennen."""
    befund = ts.markiere_hintergrund(
        [0.1, 0.2], polaritaet=ts.POLARITAET_UNBEKANNT, strategie=ts.HG_KEINE,
    )
    assert befund["n_hintergrund"] == 0


def test_wie_soll_behaelt_genau_so_viele_punkte_wie_das_soll():
    """Die Anzahl wird der einzigen Quelle entnommen, die sie kennt — nicht geraten."""
    befund = ts.markiere_hintergrund(
        [0.5, 0.4, 0.3, 0.2, 0.1], polaritaet=ts.POLARITAET_DISPARITAET,
        strategie=ts.HG_WIE_SOLL, n_geometrie=2,
    )
    assert befund["n_hintergrund"] == 3
    assert [math.isfinite(w) for w in befund["tiefen"]] == [True, True, False, False, False]


def test_wie_soll_meldet_den_preis_der_wahl():
    """Die Grösse der Silhouette ist damit nicht mehr messbar — das wird gesagt, nicht versteckt."""
    befund = ts.markiere_hintergrund(
        [0.5, 0.4, 0.3], polaritaet=ts.POLARITAET_DISPARITAET,
        strategie=ts.HG_WIE_SOLL, n_geometrie=1,
    )
    text = " ".join(befund["unsicherheit"])
    assert "LAGE" in text and "GROESSE" in text


def test_wie_soll_ohne_zahl_bricht_ab():
    with pytest.raises(ts.TiefenschaetzerError, match="n_geometrie"):
        ts.markiere_hintergrund(
            [0.1, 0.2], polaritaet=ts.POLARITAET_DISPARITAET, strategie=ts.HG_WIE_SOLL,
        )


def test_markierung_laesst_die_eingabe_unveraendert():
    """Sonst liesse sich dieselbe Rohkarte nicht mit zwei Strategien vergleichen."""
    roh = [0.1, 0.9, 0.2]
    ts.markiere_hintergrund(roh, polaritaet=ts.POLARITAET_DISPARITAET,
                            strategie=ts.HG_QUANTIL, anteil=0.5)
    assert roh == [0.1, 0.9, 0.2]


def test_nicht_endliche_schaetzwerte_gelten_als_hintergrund_und_werden_gemeldet():
    befund = ts.markiere_hintergrund(
        [0.5, math.nan, 0.3], polaritaet=ts.POLARITAET_DISPARITAET, strategie=ts.HG_KEINE,
    )
    assert befund["n_hintergrund"] == 1
    assert any("nicht endlich" in w for w in befund["warnungen"])


def test_bindung_an_der_schnittkante_wird_gemeldet():
    """Wo gleiche Werte auf der Kante liegen, entscheidet die Bildreihenfolge — nicht die Schätzung."""
    befund = ts.markiere_hintergrund(
        [0.5, 0.5, 0.5, 0.5], polaritaet=ts.POLARITAET_DISPARITAET,
        strategie=ts.HG_QUANTIL, anteil=0.5,
    )
    assert any("Schnittkante" in w for w in befund["warnungen"])


def test_unbekannte_strategie_wird_nicht_auf_die_vorgabe_zurueckgesetzt():
    with pytest.raises(ts.TiefenschaetzerError, match="Hintergrundstrategie"):
        ts.markiere_hintergrund([0.1], polaritaet=ts.POLARITAET_DISPARITAET,
                                strategie="irgendwas")


@pytest.mark.parametrize("wert", [0.0, 1.0, 1.5, -0.2, "0.4", True])
def test_unbrauchbarer_anteil_wird_abgewiesen(wert):
    with pytest.raises(ts.TiefenschaetzerError, match="anteil"):
        ts.markiere_hintergrund([0.1, 0.2], polaritaet=ts.POLARITAET_DISPARITAET,
                                strategie=ts.HG_QUANTIL, anteil=wert)


def test_leere_karte_wird_abgewiesen():
    with pytest.raises(ts.TiefenschaetzerError, match="Leere Tiefenkarte"):
        ts.markiere_hintergrund([], polaritaet=ts.POLARITAET_DISPARITAET)


def test_text_statt_zahlen_wird_nicht_umgedeutet():
    """``"0.5"`` stillschweigend zu deuten wäre die Reparatur, gegen die das Projekt antritt."""
    with pytest.raises(ts.TiefenschaetzerError, match="Zahl erwartet"):
        ts.markiere_hintergrund([0.1, "0.5"], polaritaet=ts.POLARITAET_DISPARITAET)


def test_generator_wird_abgewiesen():
    """Ein Generator wäre nach dem ersten Durchlauf leer — die halbe Prüfung liefe still ins Nichts."""
    with pytest.raises(ts.TiefenschaetzerError, match="Sequenz"):
        ts.markiere_hintergrund((x for x in [0.1, 0.2]),
                                polaritaet=ts.POLARITAET_DISPARITAET)


# --------------------------------------------------------------------------------------
# 3 · Schätzen mit Attrappe — der ganze Pfad ohne ein einziges Gewicht
# --------------------------------------------------------------------------------------

def test_vollstaendiger_durchlauf_mit_attrappe(bild):
    """Ohne GPU, ohne ``torch``, ohne Gewichte — genau dafür ist die Naht injizierbar."""
    werte = [0.1 * i for i in range(1, 17)]
    ergebnis = ts.schaetze_tiefe(bild, modell=attrappe(werte, breite=4, hoehe=4))

    assert ergebnis["status"] == ts.STATUS_OK
    assert ergebnis["tiefen"] == werte
    assert (ergebnis["breite"], ergebnis["hoehe"], ergebnis["n_punkte"]) == (4, 4, 16)
    assert ergebnis["schaetzer"] == ts.VORGABE_TIEFENSCHAETZER
    assert ergebnis["lizenz"] == "Apache-2.0"
    assert ergebnis["polaritaet"] == ts.POLARITAET_DISPARITAET
    assert ergebnis["error"] is None


def test_die_naht_bekommt_bild_und_schaetzer_uebergeben(bild):
    """Was nicht im Parametersatz steht, kann das Modell nicht benutzt haben."""
    mitschrift: list = []
    ts.schaetze_tiefe(bild, modell=attrappe([1.0, 2.0], mitschrift=mitschrift))

    assert len(mitschrift) == 1
    assert mitschrift[0]["bild_png"] == str(bild)
    assert mitschrift[0]["modell_id"].endswith("Small-hf")


def test_eine_blosse_zahlenfolge_genuegt_der_naht(bild):
    """Der schmale Vertrag: eine Liste reicht, ein Wörterbuch ist die Kür."""
    ergebnis = ts.schaetze_tiefe(bild, modell=lambda p: [3.0, 1.0, 2.0])
    assert ergebnis["status"] == ts.STATUS_OK and ergebnis["tiefen"] == [3.0, 1.0, 2.0]


def test_fehlendes_bild_wird_abgelehnt_ohne_zu_laden(tmp_path):
    """Vor dem Laden geprüft: Sonst wanderten erst Gewichte auf die GPU, um dann an einem
    Dateinamen zu scheitern."""
    def darf_nicht_laufen(*_args, **_kw):        # pragma: no cover
        raise AssertionError("Es wurde geladen, obwohl das Bild fehlt")

    ergebnis = ts.schaetze_tiefe(tmp_path / "gibt-es-nicht.png",
                                 _lader=darf_nicht_laufen)

    assert ergebnis["status"] == ts.STATUS_ABGELEHNT
    assert ergebnis["tiefen"] is None
    assert "gibt-es-nicht.png" in ergebnis["error"]


def test_ein_verzeichnis_ist_kein_bild(tmp_path):
    ergebnis = ts.schaetze_tiefe(tmp_path, modell=attrappe([1.0, 2.0]))
    assert ergebnis["status"] == ts.STATUS_ABGELEHNT


def test_eine_werfende_naht_wird_zu_status_fehler(bild):
    """Ein Stapelabbruch kostete die ganze Serie; ein protokollierter Fehler kostet ein Bild."""
    def kaputt(_parameter):
        raise RuntimeError("CUDA out of memory")

    ergebnis = ts.schaetze_tiefe(bild, modell=kaputt)
    assert ergebnis["status"] == ts.STATUS_FEHLER
    assert "CUDA out of memory" in ergebnis["error"]
    assert ergebnis["schaetzer"] == ts.VORGABE_TIEFENSCHAETZER, \
        "Auch ein Fehlschlag trägt, womit er fehlschlug"


def test_leere_antwort_der_naht_ist_ein_fehler(bild):
    ergebnis = ts.schaetze_tiefe(bild, modell=lambda p: [])
    assert ergebnis["status"] == ts.STATUS_FEHLER and "leere Tiefenkarte" in ergebnis["error"]


def test_widerspruechliche_bildgroesse_ist_ein_fehler(bild):
    """Ohne verlässliche Grösse ist Indexgleichheit mit dem Soll nicht mehr zu behaupten."""
    ergebnis = ts.schaetze_tiefe(bild, modell=attrappe([1.0, 2.0, 3.0], breite=2, hoehe=2))
    assert ergebnis["status"] == ts.STATUS_FEHLER
    assert "Indexgleichheit" in ergebnis["error"]


def test_woerterbuch_ohne_tiefen_ist_ein_fehler(bild):
    ergebnis = ts.schaetze_tiefe(bild, modell=lambda p: {"depth": [1.0]})
    assert ergebnis["status"] == ts.STATUS_FEHLER and "tiefen" in ergebnis["error"]


@pytest.mark.parametrize("name", NC_GROESSEN)
def test_schaetze_tiefe_lehnt_die_nc_groessen_ab_bevor_irgendetwas_geschieht(bild, name):
    """Regel 1 entscheidet vor der Technik — auch wenn eine Attrappe bereitliegt."""
    with pytest.raises(ts.TiefenschaetzerError, match="Regel 1"):
        ts.schaetze_tiefe(bild, schaetzer=name, modell=attrappe([1.0, 2.0]))


def test_wie_soll_ist_ohne_soll_nicht_zu_haben(bild):
    """Die Strategie braucht die Soll-Silhouette — hier gibt es keine, also bricht sie ab."""
    with pytest.raises(ts.TiefenschaetzerError, match="qa_gegen_soll"):
        ts.schaetze_tiefe(bild, modell=attrappe([1.0, 2.0]),
                          hintergrund_strategie=ts.HG_WIE_SOLL)


def test_quantil_markiert_beim_schaetzen_mit(bild):
    ergebnis = ts.schaetze_tiefe(
        bild, modell=attrappe([0.9, 0.8, 0.02, 0.01]),
        hintergrund_strategie=ts.HG_QUANTIL, hintergrund_anteil=0.5,
    )
    assert ergebnis["n_hintergrund"] == 2
    assert ergebnis["anteil_hintergrund"] == pytest.approx(0.5)
    assert ergebnis["unsicherheit"], "Eine Annahme über die Himmelsfläche wird deklariert"


# --------------------------------------------------------------------------------------
# 4 · Der Bogen zum Schluss — die Metrik endlich angewandt
# --------------------------------------------------------------------------------------

def test_treuer_render_besteht_das_geometrie_gate(bild):
    """Der Bogen: Bild → Schätzung → Hintergrundmarke → Urteil, in einem Aufruf."""
    soll = soll_karte()
    ist = disparitaets_karte(soll)

    urteil = ts.qa_gegen_soll(bild, soll, modell=attrappe(ist))

    assert urteil["status"] == ts.STATUS_OK
    assert urteil["bestanden"] is True
    assert urteil["score"] == pytest.approx(1.0)
    assert urteil["geom_iou"] == pytest.approx(1.0)


def test_invertierte_schaetzung_gilt_trotzdem_als_treu(bild):
    """**Der Sinn der Vorzeichen-Invarianz.**

    Die Schätzung ist eine Disparität: nah = grosser Wert, also gegenüber den Metern des
    Solls exakt umgekehrt sortiert. Die Rangkorrelation ist deshalb −1. Gewertet wird ihr
    **Betrag** — sonst fiele jede korrekte Depth-Anything-Schätzung durch, und zwar aus
    einem reinen Konventionsgrund.
    """
    soll = soll_karte()
    urteil = ts.qa_gegen_soll(bild, soll, modell=attrappe(disparitaets_karte(soll)))

    assert urteil["spearman"] == pytest.approx(-1.0)
    assert urteil["score"] == pytest.approx(1.0)
    assert urteil["bestanden"] is True
    assert any("negativ" in w for w in urteil["warnungen"]), \
        "Das Vorzeichen bleibt sichtbar — es könnte auch ein echter Geometriebefund sein"


def test_gegenprobe_dieselbe_karte_nicht_invertiert_besteht_ebenso(bild):
    """Ohne diese Gegenprobe wäre nicht gezeigt, dass der Betrag beide Richtungen gleich wertet."""
    soll = soll_karte()
    nicht_invertiert = [0.001 if math.isinf(t) else 100.0 - t for t in soll]
    # 100 - t ist gleichsinnig zur Disparität (nah = gross), also dieselbe Polarität.
    urteil = ts.qa_gegen_soll(bild, soll, modell=attrappe(nicht_invertiert))

    assert urteil["score"] == pytest.approx(1.0)
    assert urteil["spearman"] == pytest.approx(-1.0)


def test_halluzinierte_kubatur_faellt_durch(bild):
    """Der belegte Anlass des ganzen Gates: ein in sich stimmiger Bau an der falschen Stelle.

    Die Schätzung sieht Geometrie genau dort, wo das Soll Himmel hat, und Himmel dort, wo
    das Soll baut. Die Tiefenordnung im Überlappungsbereich kann dabei beliebig gut sein —
    das geometrische Mittel lässt sie den fehlenden Umriss nicht ausgleichen.
    """
    soll = soll_karte(n_geometrie=64, n_himmel=64)
    # Erst Himmel (kleine Disparität), dann Bau — also genau seitenverkehrt zum Soll.
    ist = [0.001] * 64 + [0.05 + 0.001 * i for i in range(64)]

    urteil = ts.qa_gegen_soll(bild, soll, modell=attrappe(ist))

    assert urteil["geom_iou"] == pytest.approx(0.0)
    assert urteil["bestanden"] is False


def test_ungleich_lange_karten_werden_abgelehnt_statt_beschnitten(bild):
    """Abschneiden verschöbe stillschweigend die Zuordnung aller Punkte danach."""
    urteil = ts.qa_gegen_soll(bild, soll_karte(), modell=attrappe([0.1, 0.2, 0.3]))

    assert urteil["status"] == ts.STATUS_ABGELEHNT
    assert urteil["bestanden"] is False
    assert urteil["score"] is None
    assert "Indexgleichheit" in urteil["error"]


def test_fehlendes_bild_faellt_im_bogen_durch(tmp_path):
    """Fail-closed: Was nicht gemessen wurde, wird nicht durchgelassen."""
    urteil = ts.qa_gegen_soll(tmp_path / "weg.png", soll_karte(),
                              modell=attrappe([1.0]))
    assert urteil["status"] == ts.STATUS_ABGELEHNT
    assert urteil["bestanden"] is False and urteil["score"] is None


def test_werfende_naht_faellt_im_bogen_durch(bild):
    def kaputt(_parameter):
        raise RuntimeError("Gewichte beschädigt")

    urteil = ts.qa_gegen_soll(bild, soll_karte(), modell=kaputt)
    assert urteil["status"] == ts.STATUS_FEHLER
    assert urteil["bestanden"] is False
    assert "Gewichte beschädigt" in urteil["error"]


@pytest.mark.parametrize("name", NC_GROESSEN)
def test_der_bogen_lehnt_die_nc_groessen_ab(bild, name):
    with pytest.raises(ts.TiefenschaetzerError, match="Regel 1"):
        ts.qa_gegen_soll(bild, soll_karte(), schaetzer=name, modell=attrappe([1.0]))


def test_die_vorgabe_ist_wie_soll_mit_und_ohne_bildmasse(bild):
    """**Zurückgenommen am 20.08.2026.**

    Vom 18. bis zum 20.08. war ``ohne_randberuehrung`` die Vorgabe, sobald die Bildmasse
    bekannt waren. `auf-20260819-15` hat sie an drei Szenen **mit Boden** gemessen: Sie
    wählt dort **null Punkte** — sobald ein Boden da ist, berührt jede Fläche den Rand.

    Ein echtes Gebäude steht auf dem Boden. Die Vorgabe ist darum zurück auf ``wie_soll``,
    und sie hängt nicht mehr davon ab, ob die Bildmasse bekannt sind.
    """
    soll = soll_karte()
    ohne = ts.qa_gegen_soll(bild, soll, modell=attrappe(disparitaets_karte(soll)))
    mit = ts.qa_gegen_soll(bild, soll,
                           modell=attrappe(disparitaets_karte(soll), breite=16, hoehe=8))

    assert ohne["hintergrund_strategie"] == ts.HG_WIE_SOLL
    assert mit["hintergrund_strategie"] == ts.HG_WIE_SOLL
    assert ohne["n_ist"] == ohne["n_soll"] == 64
    assert not [w for w in ohne["warnungen"] if "Bildmasse unbekannt" in w], (
        "die Warnung gehörte zu einem Rückfall, den es nicht mehr gibt")


def test_ohne_randberuehrung_bleibt_waehlbar(bild):
    """Sie löst genau einen Fall: eine freigestellte Szene ohne Grund. Wer sie wählt,
    soll sie bekommen — sonst wäre die Vergleichsmessung nicht wiederholbar."""
    soll = soll_karte()
    urteil = ts.qa_gegen_soll(
        bild, soll, hintergrund_strategie=ts.HG_OHNE_RANDBERUEHRUNG,
        modell=attrappe(disparitaets_karte(soll), breite=16, hoehe=8))
    assert urteil["hintergrund_strategie"] == ts.HG_OHNE_RANDBERUEHRUNG


def test_die_wahl_des_aufrufers_wird_nicht_ueberstimmt(bild):
    """Auch nicht zu seinem Besten.

    Wer ausdrücklich ``wie_soll`` verlangt, bekommt ``wie_soll`` — sonst wäre eine
    Vergleichsmessung zwischen beiden Regeln gar nicht möglich, und genau so eine hat den
    Befund überhaupt erst gebracht.
    """
    soll = soll_karte()
    urteil = ts.qa_gegen_soll(bild, soll,
                              modell=attrappe(disparitaets_karte(soll), breite=16, hoehe=8),
                              hintergrund_strategie=ts.HG_WIE_SOLL)
    assert urteil["hintergrund_strategie"] == ts.HG_WIE_SOLL


def test_loese_strategie_gibt_jede_andere_wahl_unveraendert_zurueck():
    for strategie in ts.HG_STRATEGIEN:
        gewaehlt, warnungen = ts.loese_strategie(strategie, breite=8, hoehe=8)
        assert gewaehlt == strategie
        assert warnungen == ()


def test_ohne_soll_ist_die_neue_regel_ebenso_unmoeglich_wie_die_alte(bild):
    """Sie braucht dieselbe Zahl aus derselben Quelle — das muss der Fehler auch sagen."""
    for strategie in (ts.HG_WIE_SOLL, ts.HG_OHNE_RANDBERUEHRUNG, ts.HG_VORGABE):
        with pytest.raises(ts.TiefenschaetzerError, match="SOLL-Karte"):
            ts.schaetze_tiefe(bild, modell=attrappe([0.5] * 4),
                              hintergrund_strategie=strategie)


def test_ohne_markierung_faellt_derselbe_treue_render_durch(bild):
    """Die Zahl hinter der Entscheidung — und der Grund, warum HG_KEINE nicht die Vorgabe ist.

    Dieselbe treue Schätzung, nur ohne Hintergrundmarke: Der Schätzer liefert für den
    Himmel endliche Werte, die Ist-Silhouette trägt damit das ganze Bild, und ``geom_iou``
    ist nach oben durch den Bildanteil der Soll-Geometrie begrenzt — hier deckt der Bau
    30 % des Bildes, also ist der Score durch ``sqrt(0.30) ≈ 0.55`` gedeckelt und liegt
    unter der Schwelle 0.65. Das Urteil fällt aus einem Grund, der nichts mit dem Bild zu
    tun hat, und wäre bei jedem noch so treuen Render dasselbe.
    """
    soll = soll_karte(n_geometrie=48, n_himmel=112)          # Bau deckt 30 % des Bildes
    urteil = ts.qa_gegen_soll(bild, soll, modell=attrappe(disparitaets_karte(soll)),
                              hintergrund_strategie=ts.HG_KEINE)

    assert urteil["geom_iou_obergrenze"] == pytest.approx(0.3)
    assert urteil["geom_iou"] == pytest.approx(0.3)
    assert urteil["score"] == pytest.approx(math.sqrt(0.3))
    assert urteil["score"] < geometrie_qa.SCHWELLE_GEOMETRIE
    assert urteil["bestanden"] is False
    assert any("KEIN Hintergrund" in u for u in urteil["unsicherheit"])


def test_jedes_urteil_traegt_seine_unsicherheit(bild):
    """Die Vereinbarung wird gemeldet, nicht versteckt — bei jeder Strategie."""
    soll = soll_karte()
    urteil = ts.qa_gegen_soll(bild, soll, modell=attrappe(disparitaets_karte(soll)))

    text = " ".join(urteil["unsicherheit"])
    assert "Soll-Silhouette" in text
    assert "Schaetzung, keine Messung" in text


def test_das_ergebnis_traegt_lizenz_und_modell(bild):
    """Wer eine Zahl in der Arbeit wiederfindet, soll ihr ansehen, womit sie entstand."""
    soll = soll_karte()
    urteil = ts.qa_gegen_soll(bild, soll, modell=attrappe(disparitaets_karte(soll)))

    assert urteil["lizenz"] == "Apache-2.0"
    assert urteil["modell_id"] == "depth-anything/Depth-Anything-V2-Small-hf"
    assert urteil["methode"] == geometrie_qa.METHODE
    assert urteil["methode_ist"] == ts.METHODE_IST


def test_die_schwelle_bleibt_verschiebbar(bild):
    """Phase 4 soll die Grenze verschieben können, ohne den Rechenweg anzufassen."""
    soll = soll_karte()
    ist = disparitaets_karte(soll)
    streng = ts.qa_gegen_soll(bild, soll, modell=attrappe(ist),
                              hintergrund_strategie=ts.HG_KEINE, schwelle=0.9)
    mild = ts.qa_gegen_soll(bild, soll, modell=attrappe(ist),
                            hintergrund_strategie=ts.HG_KEINE, schwelle=0.5)
    assert streng["bestanden"] is False and mild["bestanden"] is True


def test_leeres_soll_wird_abgewiesen(bild):
    with pytest.raises(ts.TiefenschaetzerError, match="soll_tiefen ist leer"):
        ts.qa_gegen_soll(bild, [], modell=attrappe([1.0]))


# --------------------------------------------------------------------------------------
# 5 · Die Ergebnisform — sie muss über das Repo reisen dürfen (Regel 3)
# --------------------------------------------------------------------------------------

def test_das_urteil_traegt_keine_bilddaten(bild):
    """``auftrag.baue_ergebnis`` wehrt eingebettete Daten ab — das Urteil muss durchkommen."""
    soll = soll_karte()
    urteil = ts.qa_gegen_soll(bild, soll, modell=attrappe(disparitaets_karte(soll)))

    satz = auftrag.baue_ergebnis(auftrag_id="auf-20260818-01", status="ok",
                                 messwerte=urteil)
    assert satz["messwerte"]["score"] == pytest.approx(1.0)


def test_das_urteil_enthaelt_die_tiefenkarte_nicht(bild):
    """Eine Karte mit 128 Zahlen im Ergebnissatz wäre kein Messwert, sondern ein Bild in Zahlen."""
    soll = soll_karte()
    urteil = ts.qa_gegen_soll(bild, soll, modell=attrappe(disparitaets_karte(soll)))

    assert "tiefen" not in urteil
    lange_listen = [k for k, v in urteil.items()
                    if isinstance(v, (list, tuple)) and len(v) > 32]
    assert not lange_listen, f"{lange_listen} sieht nach Bilddaten aus"


def test_die_schaetzung_selbst_traegt_die_karte_sehr_wohl(bild):
    """Gegenprobe: Der Arbeitsschritt liefert die Karte — nur der Rückweg tut es nicht."""
    ergebnis = ts.schaetze_tiefe(bild, modell=attrappe([1.0, 2.0, 3.0]))
    assert ergebnis["tiefen"] == [1.0, 2.0, 3.0]


# --------------------------------------------------------------------------------------
# 6 · Das Laden — Lizenz zuerst, GPU-Stack zuletzt
# --------------------------------------------------------------------------------------

@pytest.mark.parametrize("name", NC_GROESSEN)
def test_lade_modell_scheitert_an_regel_1_und_nicht_an_fehlenden_gewichten(name, tmp_path):
    """Die Reihenfolge ist bindend: Ein ausgeschlossenes Modell scheitert an der Lizenz,
    auch wenn jemand die Gewichte längst heruntergeladen hat."""
    with pytest.raises(ts.TiefenschaetzerError, match="Regel 1"):
        ts.lade_modell(name, tmp_path)


def test_lade_modell_scheitert_erst_am_fehlenden_gpu_stack(tmp_path, ohne_gpu_stack):
    """Ist die Lizenz in Ordnung, bleibt hier genau ein Hindernis — und es wird erklärt.

    Das Fehlen des Stacks stellt ``ohne_gpu_stack`` (``conftest.py``) her, statt es
    vorauszusetzen. Vorher übersprang sich der Test selbst, sobald ``torch`` in
    ``sys.modules`` lag — also genau auf der Maschine, auf der ``lade_modell`` wirklich
    gerufen wird. Ein Test, der sich dort wegduckt, wo es ernst wird, belegt nichts.
    """
    with pytest.raises(ts.TiefenschaetzerError, match="torch/transformers"):
        ts.lade_modell(ts.VORGABE_TIEFENSCHAETZER, tmp_path)


def test_lade_modell_meldet_unbekannten_namen():
    with pytest.raises(ts.TiefenschaetzerError, match="Unbekannter Tiefenschaetzer"):
        ts.lade_modell("gibt-es-nicht")


def test_standard_modell_wurzel_ist_eine_konvention():
    """Sie schaut nicht nach, ob dort etwas liegt — sie sagt nur, wo es läge."""
    assert ts.standard_modell_wurzel("depth-anything-v2-small").name == "depth-anything-v2-small"


def test_der_lader_wird_nur_ohne_modell_gerufen(bild):
    """``modell=`` heisst: Es wird nichts geladen. Sonst wäre die Test-Naht wertlos."""
    def darf_nicht_laufen(*_args, **_kw):            # pragma: no cover
        raise AssertionError("Geladen, obwohl ein Modell übergeben wurde")

    ergebnis = ts.schaetze_tiefe(bild, modell=attrappe([1.0]), _lader=darf_nicht_laufen)
    assert ergebnis["status"] == ts.STATUS_OK


def test_der_lader_wird_ohne_modell_sehr_wohl_gerufen(bild):
    """Gegenprobe zum Test darüber."""
    gerufen: list = []

    def lader(name, wurzel):
        gerufen.append((name, wurzel))
        return attrappe([1.0, 2.0])

    ergebnis = ts.schaetze_tiefe(bild, _lader=lader)
    assert gerufen == [(ts.VORGABE_TIEFENSCHAETZER, None)]
    assert ergebnis["status"] == ts.STATUS_OK


# --------------------------------------------------------------------------------------
# 7 · Die Grenze zum GPU-Stack
# --------------------------------------------------------------------------------------

def _importe(quelle: str, nur_modulebene: bool) -> set[str]:
    """Top-level-Modulnamen der Importe einer Quelldatei.

    Über ``ast`` und nicht über Textsuche — derselbe Grund wie in ``test_render.py`` und
    ``test_prozessgrenze.py``: Der Modul-Docstring **spricht** über ``import torch``, und
    eine Textsuche wäre dadurch immer rot, also wertlos.
    """
    baum = ast.parse(quelle)
    knoten = baum.body if nur_modulebene else list(ast.walk(baum))
    gefunden: set[str] = set()
    for k in knoten:
        if isinstance(k, ast.Import):
            gefunden.update(a.name.split(".")[0] for a in k.names)
        elif isinstance(k, ast.ImportFrom) and k.level == 0 and k.module:
            gefunden.add(k.module.split(".")[0])
    return gefunden


def test_scanner_selbstprobe():
    """Ein Scanner, der nichts findet, bewacht nichts."""
    quelle = "import json\ndef f():\n    import torch\n    from transformers import pipeline\n"
    assert _importe(quelle, nur_modulebene=True) == {"json"}
    assert {"torch", "transformers"} <= _importe(quelle, nur_modulebene=False)


def test_torch_und_transformers_stehen_nicht_auf_modulebene():
    """Sonst liesse sich das Modul auf keinem Rechner ohne GPU-Stack importieren."""
    quelle = Path(ts.__file__).read_text(encoding="utf-8")
    assert not {"torch", "transformers"} & _importe(quelle, nur_modulebene=True)


def test_gegenprobe_torch_und_transformers_werden_sehr_wohl_importiert():
    """Sonst wäre der Test darüber erfüllt, weil das Modul gar nie ein Modell lädt."""
    quelle = Path(ts.__file__).read_text(encoding="utf-8")
    assert {"torch", "transformers"} <= _importe(quelle, nur_modulebene=False)


def test_import_des_moduls_zieht_keinen_gpu_stack_nach():
    """``import aiimaging.tiefenschaetzer`` darf ``torch``/``transformers`` nicht nachziehen.

    Gemessen in einem **frischen Interpreter** (:func:`conftest.nachgeladene_module`) und
    nicht am ``sys.modules`` dieses Testlaufs: Dort steht, was der bisherige Lauf geladen
    hat, nicht was dieser Import lädt. Wo der GPU-Stack installiert ist, hat ihn ein
    früherer Test längst gezogen — die Prüfung wäre rot, ohne dass am Modul etwas falsch
    wäre; wo er fehlt, könnte sie nie rot werden. Ein Test, der nur in einer Umgebung
    gilt, misst die Umgebung und nicht den Code.
    """
    geladen = nachgeladene_module("aiimaging.tiefenschaetzer", ("torch", "transformers"))
    assert not geladen, f"{geladen} liegt nach dem Import in sys.modules"


def test_gegenprobe_die_sonde_sieht_ein_wirklich_geladenes_modul():
    """Wie ``test_scanner_selbstprobe``, nur für die Sonde: Wer nie etwas findet, bewacht nichts.

    ``tiefenschaetzer.py`` importiert ``pathlib`` auf Modulebene, ein nackter Interpreter
    hat es nicht. Meldet die Sonde es nach diesem Import — und nach ``import sys`` eben
    nicht —, dann misst sie die Folgen des Imports, und ihr Schweigen zum GPU-Stack oben
    ist eine Aussage.
    """
    assert nachgeladene_module("aiimaging.tiefenschaetzer", ("pathlib",)) == ["pathlib"]
    assert nachgeladene_module("sys", ("pathlib",)) == []


def test_kein_bpy_und_kein_ifcopenshell():
    """Regel 2 — hier noch einmal am Modul selbst, nicht nur im paketweiten Scan."""
    quelle = Path(ts.__file__).read_text(encoding="utf-8")
    assert not {"bpy", "ifcopenshell"} & _importe(quelle, nur_modulebene=False)


# ==========================================================================================
# HG_OHNE_RANDBERUEHRUNG — die Regel, die gemessen und nicht geraten wurde
#
# `auf-20260818-12` hat sechs Auswahlregeln an Blenders eigenem Beauty-Pass gegeneinander
# gemessen — an einem Bild, das die Geometrie exakt zeigt. Ergebnis: `wie_soll` traf nur
# 40.7 % der Punkte auf dem Bauwerk, `ohne_randberuehrung` 99.2 %; geom_iou 0.256 → 0.406.
#
# Der lehrreiche Teil ist der Verlierer: `groesste_flaeche` — der naheliegendste Filter —
# erreicht 0.0 %. Die grösste zusammenhängende Fläche der „nächsten n" IST der
# Hintergrundkeil. Eingebaut statt gemessen wäre alles schlechter geworden.
# ==========================================================================================

def _testkarte(breite=8, hoehe=8):
    """Ein Bauwerk in der Mitte, ein Halluzinationskeil in der Ecke oben rechts.

    Nachgebaut, was der Schätzer wirklich tut: In den leeren, gleichmässigen Grund legt er
    eine Bodenebene, die zur Bildecke hin auf die Kamera zuläuft. Sie erscheint dadurch
    „nah" — und verdrängt in einer Auswahl nach Nähe echte Bauwerkspunkte.
    """
    karte = [0.1] * (breite * hoehe)
    for y in range(3, 6):
        for x in range(3, 6):
            karte[y * breite + x] = 0.9          # Bauwerk, freistehend, nah
    for y in range(0, 2):
        for x in range(6, 8):
            karte[y * breite + x] = 0.85         # Keil, am Bildrand
    return karte, breite, hoehe


def _auf_dem_bauwerk(tiefen, breite):
    import math as _math
    geo = [i for i, w in enumerate(tiefen) if _math.isfinite(w)]
    treffer = sum(1 for i in geo if 3 <= i // breite <= 5 and 3 <= i % breite <= 5)
    return len(geo), treffer


def test_die_alte_regel_waehlt_den_hintergrundkeil_mit():
    """Der Befund, der den Deckel erklärt — hier im Kleinen nachgestellt."""
    karte, b, h = _testkarte()
    r = ts.markiere_hintergrund(karte, polaritaet=ts.POLARITAET_DISPARITAET,
                             strategie=ts.HG_WIE_SOLL, n_geometrie=13, breite=b, hoehe=h)
    n_geo, treffer = _auf_dem_bauwerk(r["tiefen"], b)
    assert treffer < n_geo, "der Keil müsste mitgewählt sein"


def test_ohne_randberuehrung_behaelt_nur_das_bauwerk():
    karte, b, h = _testkarte()
    r = ts.markiere_hintergrund(karte, polaritaet=ts.POLARITAET_DISPARITAET,
                             strategie=ts.HG_OHNE_RANDBERUEHRUNG, n_geometrie=13,
                             breite=b, hoehe=h)
    n_geo, treffer = _auf_dem_bauwerk(r["tiefen"], b)
    assert treffer == n_geo == 9
    assert r["n_randflaechen_verworfen"] == 1


def test_die_regel_braucht_die_bildmasse_und_raet_sie_nicht():
    """Ohne Bildmasse ist nicht entscheidbar, welcher Punkt am Rand liegt.

    Sie zu raten — etwa aus einer Quadratwurzel — ginge bei nicht-quadratischen Bildern
    schief, und zwar lautlos: Die Zeilen wären falsch umgebrochen, und „Rand" bezeichnete
    beliebige Punkte in der Bildmitte.
    """
    karte, b, h = _testkarte()
    with pytest.raises(ts.TiefenschaetzerError, match="breite"):
        ts.markiere_hintergrund(karte, polaritaet=ts.POLARITAET_DISPARITAET,
                             strategie=ts.HG_OHNE_RANDBERUEHRUNG, n_geometrie=13)


def test_unpassende_bildmasse_werden_abgewiesen():
    karte, b, h = _testkarte()
    with pytest.raises(ts.TiefenschaetzerError, match="passt nicht"):
        ts.markiere_hintergrund(karte, polaritaet=ts.POLARITAET_DISPARITAET,
                             strategie=ts.HG_OHNE_RANDBERUEHRUNG, n_geometrie=13,
                             breite=5, hoehe=5)


def test_ein_angeschnittenes_bauwerk_wird_ganz_verworfen_und_das_ist_sichtbar():
    """Die Annahme der Regel, als Test — sie darf nicht still danebengehen.

    Die Regel setzt voraus, dass das Bauwerk den Bildrand nicht berührt. Bei einem
    angeschnittenen Bau — Innenraum, Detailaufnahme, zu nahe Kamera — trifft das nicht zu,
    und dann verwirft sie das Bauwerk selbst. **Das ist hinnehmbar, weil es sichtbar ist:**
    Es bleibt kein einziger Geometriepunkt, `geometrie_qa` meldet „keine gemeinsame
    Silhouette" und gibt `score: None` statt einer Zahl. Ein verweigertes Urteil ist besser
    als ein erfundenes.
    """
    b = h = 8
    karte = [0.1] * (b * h)
    for y in range(0, 4):                        # Bauwerk läuft in den linken Bildrand
        for x in range(0, 4):
            karte[y * b + x] = 0.9
    r = ts.markiere_hintergrund(karte, polaritaet=ts.POLARITAET_DISPARITAET,
                             strategie=ts.HG_OHNE_RANDBERUEHRUNG, n_geometrie=16,
                             breite=b, hoehe=h)
    assert r["n_hintergrund"] == b * h
    assert any("gesamte Ist-Karte" in w for w in r["warnungen"])


def test_die_unsicherheit_nennt_die_annahme_und_die_gemessene_zahl():
    """Wer die Regel benutzt, muss am selben Ort lesen, worauf sie beruht und was sie unterstellt."""
    karte, b, h = _testkarte()
    r = ts.markiere_hintergrund(karte, polaritaet=ts.POLARITAET_DISPARITAET,
                             strategie=ts.HG_OHNE_RANDBERUEHRUNG, n_geometrie=13,
                             breite=b, hoehe=h)
    text = " ".join(r["unsicherheit"])
    assert "99.2" in text and "40.7" in text          # gemessen, nicht behauptet
    assert "auf-20260818-12" in text                  # und woher
    assert "angeschnittenen Bau" in text              # die Annahme, benannt


def test_vierer_nachbarschaft_trennt_was_sich_nur_ueber_eine_ecke_beruehrt():
    """Mit Achter-Nachbarschaft wäre die Regel an einer einzigen Pixelecke zerbrechlich.

    Ein diagonaler Kontakt zwischen Bauwerk und Bodenkeil genügte, und beide würden
    gemeinsam verworfen — aus einer guten Auswahl würde eine leere.
    """
    b = h = 6
    karte = [0.1] * (b * h)
    karte[2 * b + 2] = 0.9                       # freistehend, Bildmitte
    karte[1 * b + 1] = 0.9                       # nur über die Ecke verbunden …
    karte[0 * b + 0] = 0.9                       # … und am Rand
    r = ts.markiere_hintergrund(karte, polaritaet=ts.POLARITAET_DISPARITAET,
                             strategie=ts.HG_OHNE_RANDBERUEHRUNG, n_geometrie=3,
                             breite=b, hoehe=h)
    import math as _math
    geo = [i for i, w in enumerate(r["tiefen"]) if _math.isfinite(w)]
    # Alle drei berühren sich nur über Ecken, sind also drei getrennte Flächen. Verworfen
    # wird genau die am Rand; die beiden inneren überleben — auch die, die über die Ecke
    # an der verworfenen hängt. Mit Achter-Nachbarschaft wären alle drei EINE Fläche
    # gewesen, sie hätte den Rand berührt, und es bliebe nichts.
    assert 0 not in geo, "die Fläche am Bildrand müsste verworfen sein"
    assert set(geo) == {1 * b + 1, 2 * b + 2}, geo


def test_die_neue_strategie_steht_in_der_liste():
    assert ts.HG_OHNE_RANDBERUEHRUNG in ts.HG_STRATEGIEN


# ======================================================================================
# Der Maskenweg durch `qa_gegen_soll` — die Verdrahtung, nicht die Masse
# ======================================================================================
#
# Was die beiden Masse tun, steht in `test_geometrie_qa.py`. Hier wird geprüft, dass sie
# überhaupt gerufen werden und die richtige Karte bekommen. Ein Modul, das nie läuft, ist
# von einem fehlenden Modul nicht zu unterscheiden — das ist die Lehre, wegen der
# `tools/abholen.py` existiert.

_MASKE_B = 32
_MASKE_VON, _MASKE_BIS = 8, 23


def _zweidimensionale_szene():
    """Ein Bauwerk als Quadrat vor Himmel, gross genug für eine Maskengrenze.

    Die eindimensionalen Karten weiter oben taugen hier nicht: Eine Grenze braucht
    Nachbarschaft, und die entsteht erst mit einer Breite.
    """
    maske = [(_MASKE_VON <= x <= _MASKE_BIS and _MASKE_VON <= y <= _MASKE_BIS)
             for y in range(_MASKE_B) for x in range(_MASKE_B)]
    # Soll: Meter, von 10 nach 20 über das Bauwerk, Himmel unendlich.
    soll = []
    n = 0
    for m in maske:
        if m:
            soll.append(10.0 + 10.0 * n / sum(maske))
            n += 1
        else:
            soll.append(float("inf"))
    # Ist: Disparität — nah = gross. Himmel bekommt einen kleinen Wert, kein inf.
    ist = [(1.0 / s if s != float("inf") else 0.001) for s in soll]
    return soll, ist, maske


def _urteil_mit(maske, bild):
    soll, ist, _ = _zweidimensionale_szene()
    return ts.qa_gegen_soll(bild, soll, modell=attrappe(ist),
                            breite=_MASKE_B, hoehe=_MASKE_B, maske=maske)


def test_ohne_maske_bleibt_der_maskenweg_ungemessen(bild):
    """`None` heisst hier nicht gemessen — nicht in Ordnung.

    Der Score über das ganze Bild beantwortet weder Existenz noch Richtigkeit: Ein leeres
    Grundstück erreicht dort 0.9530 und besteht das Tor (auf-20260821-26).
    """
    urteil = _urteil_mit(None, bild)

    assert urteil["rho_maske"] is None
    assert urteil["kante"] is None
    assert urteil["paarurteil"] is None


def test_mit_maske_entstehen_beide_masse_und_ein_paarurteil(bild):
    _soll, _ist, maske = _zweidimensionale_szene()

    urteil = _urteil_mit(maske, bild)

    assert urteil["rho_maske"]["n_maske"] == sum(maske)
    assert urteil["kante"]["n_innen"] >= geometrie_qa.MIN_RANDPUNKTE
    assert urteil["paarurteil"]["schwellen"]["rho"] == geometrie_qa.PAAR_RHO_SCHWELLE


def test_die_kante_bekommt_die_ROHE_karte_und_nicht_die_markierte(bild):
    """**Die Entscheidung, die man übersehen kann.**

    Die Hintergrundmarkierung setzt alles ausserhalb der Geometrie auf eine Marke.
    Innerhalb der Maske wäre das gleichgültig — aber die Kante liest ausdrücklich auch
    AUSSERHALB, und dort verdürbe die Marke den Median. Sie misst den Sprung zwischen
    Fassade und dem, was dahinter liegt; dafür braucht sie, was der Schätzer dort
    wirklich gesehen hat.
    """
    _soll, ist, maske = _zweidimensionale_szene()

    urteil = _urteil_mit(maske, bild)

    assert urteil["kante"]["spanne"] == pytest.approx(max(ist) - min(ist)), (
        "Die Spanne stammt nicht aus der rohen Schätzkarte — dann steckt die "
        "Hintergrundmarke darin, und das Mass misst die Marke statt die Kante"
    )
    assert urteil["kante"]["gerichtet"] > 0, "das Bauwerk ist näher als der Himmel"


def test_die_gemessene_polaritaet_schlaegt_die_deklarierte(bild):
    """Zwei Quellen für dieselbe Tatsache, und sie behaupten nicht dasselbe.

    Die Zeichenkette am Schätzer beschreibt den SCHÄTZER. Das Vorzeichen in
    `GEMESSENE_POLARITAET` beschreibt das PAAR aus Schätzer und unserer Soll-Karte und ist
    an 24 Läufen gemessen. Wo beides vorliegt, gilt das Gemessene.
    """
    _soll, _ist, maske = _zweidimensionale_szene()

    urteil = _urteil_mit(maske, bild)

    assert urteil["rho_maske"]["polaritaet"] == geometrie_qa.POLARITAET_DISPARITAET
    assert (geometrie_qa.GEMESSENE_POLARITAET["depth-anything-v2-small"]
            == ts.POLARITAETSZEICHEN["disparitaet"]), (
        "hier stimmen sie überein — dass sie es tun, ist ein Befund und keine Regel")


def test_der_kantenanteil_kommt_mit_und_traegt_das_paarurteil(bild):
    """Das zweite Bein muss auch wirklich ankommen — sonst fällt der Paartest still auf
    die Median-Kante zurück, die kippt statt zu trennen."""
    _soll, _ist, maske = _zweidimensionale_szene()

    urteil = _urteil_mit(maske, bild)

    assert urteil["kantenanteil"] is not None
    assert urteil["paarurteil"]["zweites_bein"] == "anteil", (
        "der Paartest nimmt den Anteil und nicht die Median-Kante")
