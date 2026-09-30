"""Das Homeworker-Ergebnis sagt, welcher Modus gerechnet wurde und wie treu der Umriss ist.

Der Anlass (PLAN, Sitzung 73: «homeworker-Ergebnis mit ``modus_gerechnet`` und
Umrisstreue»)
--------------------------------------------------------------------------------------
``tools/homeworker.py`` ist der Weg, auf dem die HomeStation ihre **eigenen** Messreihen
fährt. Zwei Auskünfte kamen dort nicht an, obwohl sie im Kern längst gerechnet werden:

* ``modus_gerechnet`` — ``render.rendere`` führt es seit dem 21.09.2026. Abgeschrieben
  wurden nur Status, Seed, Parameter und Hinweise; ein Lauf, der ``image_edit`` bestellt
  und ``txt2img`` gerechnet hat, sah im Ergebnis aus wie einer, der bekam, was er
  bestellte.
* die Formprüfung (Umrisstreue, ``formkandidaten.formpruefung``) — der Abholer führt sie je
  Seed und am Sieger, dieser Weg gar nicht.

Und derselbe Befund wie bei ``bedarf.grund`` (``auf-20260924-173``, Zusatz A4): Der
Geräteweg des Bildmodells samt seinem Grund fehlte in diesem Ergebnis ganz.

Geprüft wird über die Nähte des Skripts, ohne GPU und ohne Gewichte. Alle Bilder sind
synthetisch und hier erzeugt (Regel 3).
"""
from __future__ import annotations

import time
from pathlib import Path

from aiimaging import bildschreiben, formkandidaten, render

import test_homeworker as th
from test_homeworker import (BLOCK_SPALTEN, BLOCK_ZEILEN, BREITE, GLB_BERICHT, HOEHE,
                             Renderattrappe, Tiefenattrappe, _felder_mit, hw, satz,
                             treue_ist_karte)

#: Dieselben Fixtures wie in ``test_homeworker`` — ein synthetischer Blender-Bericht mit
#: echtem 16-Bit-Tiefen-PNG und Material-ID-Pass. Übernommen, nicht nachgebaut: Eine
#: zweite Attrappe liefe still auseinander.
aus = th.aus
bericht = th.bericht


def _bild_mit_bau(ziel: Path, breite: int = BREITE, hoehe: int = HOEHE) -> Path:
    """Ein heller Block vor dunklem Grund — derselbe Umriss wie die Soll-Karte."""
    farben = [(20, 20, 20)] * (breite * hoehe)
    for zeile in BLOCK_ZEILEN:
        for spalte in BLOCK_SPALTEN:
            if zeile < hoehe and spalte < breite:
                farben[zeile * breite + spalte] = (230, 230, 230)
    return bildschreiben.schreibe_farb_png(ziel, farben, breite, hoehe)


class Meldendes:
    """Ein Bildmodell, das wie der echte Adapter meldet, was bestellt und was gerechnet war.

    Bestellt ist ``image_edit`` (der Beauty-Pass geht als Anker mit), gerechnet wird
    ``txt2img`` — genau der Fall, für den die Felder gebaut sind.
    """

    def __init__(self, *, gerechnet=render.MODUS_TXT2IMG, groesse=(BREITE, HOEHE),
                 geraet="cuda+schichtauslagerung", bedarf=None):
        self.gerechnet = gerechnet
        self.groesse = groesse
        self.geraet = geraet
        self.bedarf = bedarf

    def __call__(self, parameter: dict):
        _bild_mit_bau(Path(parameter["ausgabe_png"]), *self.groesse)
        return {"bild_png": parameter["ausgabe_png"],
                "modus_bestellt": parameter["modus"],
                "modus_gerechnet": self.gerechnet}


def _lauf(bericht, aus, modell, **params):
    return hw._render_und_qa(
        satz(), bericht, GLB_BERICHT, aus, {"prompt": "Wohnhaus", **params},
        time.monotonic(), _render_modell=modell,
        _tiefen_modell=Tiefenattrappe(treue_ist_karte(bericht)))


# ── modus_gerechnet ───────────────────────────────────────────────────────────────────

def test_das_ergebnis_nennt_den_gerechneten_modus_und_die_abweichung(bericht, aus):
    """**Der Kern.** Bestellt ``image_edit``, gerechnet ``txt2img`` — das muss im
    Ergebnis stehen, und zwar als vergleichbares Feld, nicht nur als Hinweis."""
    ergebnis = _lauf(bericht, aus, Meldendes())

    lauf = ergebnis["messwerte"]["render"]
    assert lauf["modus_bestellt"] == render.MODUS_IMAGE_EDIT
    assert lauf["modus_gerechnet"] == render.MODUS_TXT2IMG
    assert lauf["modus_abweichung"] is True
    assert ergebnis["urteil"]["modus_gerechnet"] == render.MODUS_TXT2IMG


def test_ein_modell_ohne_meldung_steht_als_nicht_gemeldet_da(bericht, aus):
    """Die dritte Antwort: Eine Naht, die nichts meldet, ist nicht «wie bestellt».
    ``None`` heisst nicht gemessen — und darf nicht zu ``False`` werden."""
    ergebnis = _lauf(bericht, aus, Renderattrappe())

    lauf = ergebnis["messwerte"]["render"]
    assert lauf["modus_bestellt"] == render.MODUS_IMAGE_EDIT
    assert lauf["modus_gerechnet"] is None
    assert lauf["modus_abweichung"] is None
    assert ergebnis["urteil"]["modus_gerechnet"] is None


def test_auch_ein_gescheiterter_render_nennt_den_bestellten_modus(bericht, aus):
    """Gerade ein Fehlschlag muss sagen, was bestellt war — sonst ist er nicht zu deuten."""
    def kaputt(parameter):
        raise RuntimeError("CUDA out of memory")

    ergebnis = _lauf(bericht, aus, kaputt)

    assert ergebnis["status"] == "fehler"
    assert ergebnis["messwerte"]["render"]["modus_bestellt"] == render.MODUS_IMAGE_EDIT
    assert ergebnis["messwerte"]["render"]["modus_gerechnet"] is None


# ── Umrisstreue ───────────────────────────────────────────────────────────────────────

def test_die_umrisstreue_steht_als_auskunft_im_ergebnis(bericht, aus):
    """Soll-Karte und Bild liegen vor → die Formprüfung wird gerechnet, mit derselben
    Funktion wie beim Abholer, und sie urteilt nicht."""
    ergebnis = _lauf(bericht, aus, Meldendes())

    form = ergebnis["messwerte"]["formpruefung"]
    assert form["status"] == "ok", form
    assert form["mass"] == formkandidaten.FORMPRUEFUNG_MASS
    assert isinstance(form["wert"], float)
    assert form["urteilt"] is False and form["schwelle"] is None
    assert form["grundlage"] == formkandidaten.FORMPRUEFUNG_GRUNDLAGE
    assert ergebnis["urteil"]["umrisstreue"] == form["wert"]


def test_die_umrisstreue_ist_dieselbe_zahl_wie_im_kern(bericht, aus):
    """Keine zweite Rechnung: Die Zahl im Ergebnis ist die von ``formkandidaten``."""
    from aiimaging import bildlesen

    ergebnis = _lauf(bericht, aus, Meldendes())

    soll, breite, hoehe = bildlesen.tiefen_aus_report(bericht)
    luminanz, _, _ = bildlesen.lies_png_luminanz(aus / "render.png")
    kern = formkandidaten.formpruefung(luminanz, soll, breite, hoehe)
    assert ergebnis["messwerte"]["formpruefung"]["wert"] == kern["wert"]


def test_die_umrisstreue_beeinflusst_den_status_nicht(bericht, aus):
    """Auskunft, kein Urteil (auf-20260930-196: die Schwelle trägt nicht). Ein nicht
    messbarer Umriss macht aus einem gemessenen Auftrag keinen Fehler."""
    ergebnis = _lauf(bericht, aus, Renderattrappe())   # schreibt kein lesbares PNG

    form = ergebnis["messwerte"]["formpruefung"]
    assert ergebnis["status"] == "ok"
    assert form["wert"] is None
    assert form["status"] == "bild_nicht_lesbar"
    assert form["grund"], "Ein None ohne Satz liesse den Leser raten."
    assert ergebnis["urteil"]["umrisstreue"] is None


def test_verschiedene_raster_ergeben_keine_zahl_sondern_einen_grund(bericht, aus):
    """Ein Umriss auf zwei verschiedenen Rastern wäre eine erfundene Zahl."""
    form = hw._formpruefung(_bild_mit_bau(aus / "gross.png", 32, 32),
                            [1.0] * (BREITE * HOEHE), BREITE, HOEHE)
    assert form["wert"] is None
    assert form["status"] == "groesse_passt_nicht"
    assert "32x32" in form["grund"]


def test_ohne_soll_karte_keine_zahl_sondern_ein_grund(aus):
    form = hw._formpruefung(_bild_mit_bau(aus / "b.png"), None, BREITE, HOEHE)
    assert form["wert"] is None and form["status"] == "keine_soll_karte"


# ── Geräteweg samt Grund ──────────────────────────────────────────────────────────────

def test_der_geraeteweg_und_sein_grund_stehen_im_ergebnis(bericht, aus):
    """``auf-20260924-173``, Zusatz A4: Den Grund der Stufenwahl nannte nur das
    Abholer-Protokoll. Auf diesem Weg fehlte der Geräteweg ganz."""
    satz_ = "Entschieden an gemessene Spitze (Registry): 100 MiB x 1.1 = 110 MiB verlangt."
    ergebnis = _lauf(bericht, aus, Meldendes(bedarf={"grund": satz_}))

    weg = ergebnis["messwerte"]["render"]["geraeteweg"]
    assert weg["geraet"] == "cuda+schichtauslagerung"
    assert weg["bedarf"]["grund"] == satz_
    assert satz_ in weg["grund"]


# ── Regel 3 ───────────────────────────────────────────────────────────────────────────

def test_die_neuen_felder_tragen_kein_arbeitsverzeichnis(bericht, aus):
    """Dieselbe Wache wie in ``test_homeworker`` — über die neuen Felder mit."""
    ergebnis = _lauf(bericht, aus, Meldendes(bedarf={"grund": "Probe"}))
    assert _felder_mit(ergebnis["messwerte"], str(aus)) == []
    assert _felder_mit(ergebnis["urteil"], str(aus), "urteil") == []

    kaputt = _lauf(bericht, aus, Renderattrappe())
    assert _felder_mit(kaputt["messwerte"], str(aus)) == []
