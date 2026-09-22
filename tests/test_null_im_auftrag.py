"""Ein ausdrückliches ``null`` im Auftrag darf nichts umwerfen.

**Der Befund** (22.09.2026, Suche über sechs Fehlerarten): ``dict.get(schluessel, ersatz)``
greift **nur bei fehlendem Schlüssel**. Steht das Feld da und trägt ``null``, gewinnt die
``None`` gegen den Ersatz — und gleich darauf wirft ``int(None)`` oder ``float(None)``.

Das ist keine erdachte Lage. Wer die Vorgabe des Vertrags gelten lassen will, schreibt in
JSON genau ``"samples": null``. Und die Folge ist nicht ein Mangel an **diesem** Auftrag,
sondern der Abbruch des **ganzen** Durchgangs: Der ``TypeError`` fällt durch
``except quelle.QUELLEN_FEHLER`` hindurch — das ist nur ``BrueckenError`` — bis hinauf in
``abholer.durchgang``. Und weil der kaputte Auftrag auf ``queued`` stehenbleibt, stolpert
jeder folgende Lauf wieder über ihn.

    *Ein Auftrag, den wir nicht lesen können, ist ein Mangel an diesem Auftrag — und nicht
    das Ende des Durchgangs.*

Derselbe Griff hat in zwei Tagen an **vier** Stellen zugeschlagen
(`homeworker._darf_starten`, `kette._fuehre_geometrie`, `kosmo_szene.lies_szene` zweimal).
Dreimal ist kein Ausrutscher, viermal ist eine Gewohnheit.

**Die Wächter hier prüfen die Wirkung**, und sie prüfen sie **für jedes Feld des
Vertragsblocks**, nicht für die zwei, die aufgefallen sind: *Ein Wächter, der die beiden
bekannten Fälle abdeckt, fängt den dritten nicht.*
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

from aiimaging import kosmo_szene

WERKZEUGE = Path(__file__).resolve().parents[1] / "tools"


def _szene(**render):
    """Eine gerade noch gültige fremde Bestellung, mit ``render`` nach Wunsch."""
    return {
        "schema": kosmo_szene.SCHEMA_SZENE,
        "geometry": {"path": "/tmp/nicht-vorhanden/modell.glb"},
        "render": render,
    }


# --------------------------------------------------------------------------------------
# 1 · Der Vertragsblock — jedes Feld, nicht nur die aufgefallenen
# --------------------------------------------------------------------------------------

@pytest.mark.parametrize("block, feld", [
    ("render", "samples"),
    ("render", "faithful"),
    ("render", "resolution"),
    ("style", "mode"),
    ("style", "refs"),
    ("vis", "skip"),
    ("vis", "upscale"),
    ("vis", "backbone"),
])
def test_ein_null_in_irgendeinem_feld_wirft_nicht(block, feld):
    """**Der eigentliche Riegel.** Jedes Feld einzeln auf ``null`` — nichts darf werfen."""
    roh = _szene()
    roh.setdefault(block, {})[feld] = None

    szene = kosmo_szene.lies_szene(roh)

    assert isinstance(szene, dict), f"{block}.{feld} = null hat den Vertrag umgeworfen"


def test_null_bei_samples_ergibt_die_vorgabe_und_nicht_none():
    ohne = kosmo_szene.lies_szene(_szene())
    mit_null = kosmo_szene.lies_szene(_szene(samples=None))

    assert mit_null["samples"] == ohne["samples"], (
        "ein ausdrueckliches null muss dasselbe heissen wie «nicht gesagt»")
    assert isinstance(mit_null["samples"], int)


def test_null_bei_faithful_ergibt_die_vorgabe_und_nicht_none():
    ohne = kosmo_szene.lies_szene(_szene())
    mit_null = kosmo_szene.lies_szene(_szene(faithful=None))

    assert mit_null["controlnet_staerke"] == ohne["controlnet_staerke"]
    assert isinstance(mit_null["controlnet_staerke"], float)


def test_ein_null_beim_stil_meldet_nicht_faelschlich_ein_stehengebliebenes_feld():
    """Sonst bekommt der Betreiber für einen Auftrag **ohne** Stilwunsch die Meldung,
    die Stil-QA sei bestellt und nicht geliefert worden."""
    roh = _szene()
    roh["style"] = {"mode": None}
    szene = kosmo_szene.lies_szene(roh)

    assert szene["stil_modus"] == "none"
    stehen = [e["feld"] for e in kosmo_szene.stehengebliebene_felder(szene)]
    assert "stil_modus" not in stehen


def test_ein_gesetzter_wert_gewinnt_weiterhin():
    """Die Gegenprobe: Der Helfer darf nicht alles auf die Vorgabe ziehen."""
    szene = kosmo_szene.lies_szene(_szene(samples=7, faithful=0.25))

    assert szene["samples"] == 7
    assert szene["controlnet_staerke"] == pytest.approx(0.25)


def test_der_helfer_unterscheidet_fehlt_von_null():
    assert kosmo_szene.wert_oder({}, "x", 5) == 5
    assert kosmo_szene.wert_oder({"x": None}, "x", 5) == 5
    assert kosmo_szene.wert_oder({"x": 0}, "x", 5) == 0, (
        "eine gesetzte Null ist ein Wert und keine fehlende Angabe")
    assert kosmo_szene.wert_oder({"x": False}, "x", True) is False


# --------------------------------------------------------------------------------------
# 2 · Der Torwächter der HomeStation — dieselbe Falle, andere Datei
# --------------------------------------------------------------------------------------

@pytest.fixture
def hw():
    pfad = WERKZEUGE / "homeworker.py"
    spez = importlib.util.spec_from_file_location("homeworker_null", pfad)
    modul = importlib.util.module_from_spec(spez)
    sys.modules[spez.name] = modul
    spez.loader.exec_module(modul)
    return modul


#: Ein GPU-Zustand, der die Tür wirklich passiert.
#:
#: **Hier stand zuerst ein Wörterbuch ohne ``verfuegbar``.** Damit kehrte
#: ``darf_starten`` gleich in der ersten Zeile um («GPU-Zustand unbekannt») und erreichte
#: die Schwellenprüfung nie — die Wächter darunter waren grün und prüften nichts. Eine
#: Mutationsprobe am 22.09.2026 hat es aufgedeckt: Der Rückbau auf
#: ``.get(schluessel, ersatz)`` liess alle Tests stehen.
#:
#:     *Ein Wächter an einer Stelle, an der der Fall nicht vorkommt, ist kein Wächter —
#:     er ist eine Beruhigung.*
ZUSTAND = {"verfuegbar": True, "name": "Testkarte", "leistung_w": 5.0,
           "speicher_belegt_gb": 0.1, "speicher_gesamt_gb": 32.0,
           "leistungsgrenze_w": 400.0}


def test_der_zustand_dieser_pruefung_kommt_ueberhaupt_bis_zur_schwelle(hw):
    """**Die Vorprüfung des Prüfstandes selbst.**

    Ohne sie prüfen alle Wächter darunter nichts — das war bis zum 22.09.2026 so.
    """
    darf, grund = hw.darf_starten(dict(ZUSTAND), {})

    assert darf is True, grund
    assert "unbekannt" not in grund


@pytest.mark.parametrize("feld", [
    "leistungsgrenze_w", "nur_bei_leerlauf",
    "leerlauf_schwelle_w", "leerlauf_schwelle_mem_gb",
])
def test_ein_null_in_den_auflagen_wirft_den_torwaechter_nicht_um(hw, feld):
    """Er stürzte ab, **bevor** er etwas prüfen konnte — und ein Torwächter, der beim
    Prüfen abstürzt, hat nicht geprüft."""
    darf, grund = hw.darf_starten(dict(ZUSTAND), {feld: None})

    assert isinstance(darf, bool)
    assert isinstance(grund, str) and grund


def test_null_heisst_die_strenge_vorgabe_und_nicht_keine_grenze(hw):
    """**Die Richtung zählt.** ``null`` darf nie «keine Grenze» heissen."""
    mit_null = hw.darf_starten(dict(ZUSTAND), {"leerlauf_schwelle_w": None})
    ohne = hw.darf_starten(dict(ZUSTAND), {})

    assert mit_null == ohne

    # Und die Vorgabe greift wirklich: eine GPU knapp ueber der Vorgabeschwelle faellt
    # durch, obwohl im Auftrag `null` steht.
    laut = dict(ZUSTAND, leistung_w=hw.auf.GPU_LEERLAUF_W + 1.0)
    darf, _ = hw.darf_starten(laut, {"leerlauf_schwelle_w": None})
    assert darf is False


def test_ein_null_schaltet_das_leerlauf_tor_nicht_ab(hw):
    """**Der gefährlichste der vier Fälle — und er wirft nicht, er schweigt.**

    Mit ``auflagen.get("nur_bei_leerlauf", True)`` und dem Wert ``null`` ergibt ``not
    None`` ein ``True``: Das Leerlauf-Tor gilt als **im Auftrag abgeschaltet**. Kein
    Absturz, keine Meldung — die Karte darf laufen, obwohl ein fremdes Modell darauf
    liegt.

        *Eine Sperre, die ein ``null`` aufhebt, ist keine Sperre. Und sie fällt nicht auf,
        weil nichts kaputtgeht.*

    Eine Mutationsprobe am 22.09.2026 hat gezeigt, dass die übrigen Wächter das nicht
    fangen: Sie prüfen, dass nichts **wirft**.
    """
    belegt = dict(ZUSTAND, leistung_w=hw.auf.GPU_LEERLAUF_W + 50.0,
                  speicher_belegt_gb=hw.auf.GPU_LEERLAUF_MEM_GB + 4.0)

    darf, grund = hw.darf_starten(belegt, {"nur_bei_leerlauf": None})

    assert darf is False, (
        "ein null hat das Leerlauf-Tor abgeschaltet — es muss die STRENGE Lesart "
        "bedeuten, nicht die milde")
    assert "abgeschaltet" not in grund


def test_ein_ausdrueckliches_false_schaltet_es_weiterhin_ab(hw):
    """Die Gegenprobe: Wer es wirklich abschalten will, kann das — mit ``false``."""
    belegt = dict(ZUSTAND, leistung_w=hw.auf.GPU_LEERLAUF_W + 50.0)

    darf, grund = hw.darf_starten(belegt, {"nur_bei_leerlauf": False})

    assert darf is True
    assert "abgeschaltet" in grund


def test_der_helfer_der_homestation_unterscheidet_fehlt_von_null(hw):
    assert hw._auflage({}, "x", 5) == 5
    assert hw._auflage({"x": None}, "x", 5) == 5
    assert hw._auflage({"x": 0}, "x", 5) == 0
