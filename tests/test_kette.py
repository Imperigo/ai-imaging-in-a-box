"""Die Bildkette als Graph — und der Nachweis, dass der Zwischenspeicher wirklich greift.

Drei Sorten Tests, bewusst getrennt
-----------------------------------
1. **Bau.** Was ``baue_kette`` an einer unvollständigen Beschreibung meldet, und welche
   Gestalt der Graph hat. Reine Rechnung, kein Lauf.
2. **Lauf mit Attrappen.** Die ganze Kette mit gezählten Ersatz-Ausführern: ohne Blender,
   ohne ``.venv-ifc``, ohne GPU. Hier liegt der eigentliche Beweis.
3. **Echter Lauf** (``@pytest.mark.skipif``). IFC→glb und Multipass wirklich über die
   Prozessgrenze, die QA wirklich gerechnet — nur das Bildmodell bleibt Attrappe, denn
   es gibt keine GPU.

Warum gezählt wird und nicht gemessen
-------------------------------------
„Der Cache greift" liesse sich auch über die Laufzeit behaupten: zweiter Lauf schneller
als der erste. Das ist kein Beweis, sondern eine Beobachtung mit Rauschen — ein warmer
Dateisystem-Cache erklärt dasselbe. Der Beweis ist die **Zahl der Ausführeraufrufe**:
Wird die Funktion für die Geometriestufe nach einer Prompt-Änderung noch ein zweites Mal
gerufen, ist der Zwischenspeicher wertlos, egal wie schnell der Lauf war. Deshalb zählt
``Werkbank`` jeden Aufruf, und die Zusicherungen lauten auf ``== 1``, nicht auf ``< t``.

Regel 3: Alle Testdaten entstehen hier. Die IFC des echten Laufs kommt aus
``tools/make_test_ifc.py`` — synthetisch, im Repo erzeugbar, ohne Bürodaten.
"""
from __future__ import annotations

import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

import pytest

from aiimaging import kette, seams, torwaechter
from aiimaging.graph import ArtefaktCache, Graph, GraphError, Knoten, ZyklusError
from aiimaging.kette import (
    ART_GEOMETRIE,
    ART_MULTIPASS,
    ART_QA,
    ART_RENDER,
    KNOTEN_GEOMETRIE,
    KNOTEN_MULTIPASS,
    KNOTEN_QA,
    KNOTEN_RENDER,
    KettenError,
    baue_kette,
    fuehre_aus,
)
from conftest import REPO

#: Eine bbox in plausiblen Gebäudemassen — der Torwächter lässt sie durch.
BBOX_HAUS = [[0.0, 0.0, 0.0], [8.0, 5.0, 3.0]]


# ======================================================================================
# Werkbank: Attrappen, die zählen und winzige echte Dateien schreiben
# ======================================================================================

class Werkbank:
    """Ersatz-Ausführer für alle vier Knotenarten, mit Aufrufzähler.

    Die Attrappen schreiben **echte** Dateien, wenn auch winzige. Das ist keine
    Spielerei: ``fuehre_aus`` verwirft einen Cache-Eintrag, dessen versprochene Dateien
    nicht mehr existieren. Eine Attrappe, die nur Pfade behauptet, ergäbe darum bei jedem
    Lauf einen Fehltreffer — und der Test bewiese das Gegenteil dessen, was er soll.
    """

    def __init__(self) -> None:
        self.aufrufe: Counter = Counter()
        self.eingaben: dict[str, list[dict]] = {}
        self.arbeitsverzeichnisse: dict[str, Path] = {}

    def tabelle(self) -> dict:
        return {
            ART_GEOMETRIE: self.geometrie,
            ART_MULTIPASS: self.multipass,
            ART_RENDER: self.render,
            ART_QA: self.qa,
        }

    def _vermerke(self, art: str, eingaben: list[dict], out_dir: Path) -> None:
        self.aufrufe[art] += 1
        self.eingaben[art] = eingaben
        self.arbeitsverzeichnisse[art] = out_dir
        assert out_dir.is_dir(), "Das Arbeitsverzeichnis existiert, bevor gerufen wird"

    def geometrie(self, *, knoten, eingaben, out_dir):
        self._vermerke(ART_GEOMETRIE, eingaben, out_dir)
        glb = out_dir / "modell.glb"
        quelle = knoten.params.get("ifc_path") or knoten.params.get("glb_path")
        glb.write_text(f"glb aus {Path(quelle).name}", encoding="utf-8")
        return {"glb_path": str(glb), "up_axis": "Y", "bbox": BBOX_HAUS}

    def multipass(self, *, knoten, eingaben, out_dir):
        self._vermerke(ART_MULTIPASS, eingaben, out_dir)
        tiefe = out_dir / "tiefe_norm.png"
        beauty = out_dir / "beauty.png"
        tiefe.write_text("tiefe", encoding="utf-8")
        beauty.write_text("beauty", encoding="utf-8")
        return {
            "status": "ok",
            "depth_png": str(tiefe),
            "beauty_png": str(beauty),
            "aufloesung": knoten.params["aufloesung"],
            "samples": knoten.params["samples"],
        }

    def render(self, *, knoten, eingaben, out_dir):
        self._vermerke(ART_RENDER, eingaben, out_dir)
        bild = out_dir / "bild.png"
        bild.write_text(f"bild zu {knoten.params['prompt']}", encoding="utf-8")
        return {"status": "ok", "bild_png": str(bild), "seed": knoten.params["seed"]}

    def qa(self, *, knoten, eingaben, out_dir):
        self._vermerke(ART_QA, eingaben, out_dir)
        return {"status": "ok", "bestanden": True, "score": 0.91,
                "schwelle": knoten.params["schwelle"]}


def schreibe_ifc(pfad: Path, inhalt: str = "SYNTHETISCHE-GEOMETRIE-A") -> Path:
    """Eine Platzhalter-IFC. Für die Attrappen zählt nur ihr **Inhalt** — er geht in den Hash."""
    pfad.parent.mkdir(parents=True, exist_ok=True)
    pfad.write_text(inhalt, encoding="utf-8")
    return pfad


def lauf(graph: Graph, werkbank: Werkbank, cache, tmp_path: Path) -> dict:
    """Einen Graphen mit der Werkbank abarbeiten — immer in derselben Ausgabewurzel."""
    return fuehre_aus(graph, cache=cache, ausfuehrer=werkbank.tabelle(),
                      out_dir=tmp_path / "out")


# ======================================================================================
# 1 · Bau
# ======================================================================================

def test_standardkette_hat_vier_knoten_in_erwarteter_reihenfolge():
    g = baue_kette(ifc_path="/tmp/haus.ifc", prompt="Morgenlicht")
    assert len(g) == 4
    assert g.topologische_reihenfolge() == [
        KNOTEN_GEOMETRIE, KNOTEN_MULTIPASS, KNOTEN_RENDER, KNOTEN_QA]


def test_qa_haengt_an_beiden_stufen_und_die_reihenfolge_ist_bedeutung():
    """Slot 0 ist das Soll (Multipass), Slot 1 das Ist (Render) — nicht umgekehrt.

    Das ist der Grund, warum die Kette ein Graph und keine Liste ist: Die QA hat zwei
    Vorgänger, und welcher davon das Soll liefert, steht in der Position.
    """
    g = baue_kette(ifc_path="/tmp/haus.ifc", prompt="x")
    assert g.vorgaenger(KNOTEN_QA) == [KNOTEN_MULTIPASS, KNOTEN_RENDER]


def test_ohne_qa_bleiben_drei_knoten():
    g = baue_kette(ifc_path="/tmp/haus.ifc", prompt="x", qa=False)
    assert sorted(g.knoten) == [KNOTEN_GEOMETRIE, KNOTEN_MULTIPASS, KNOTEN_RENDER]


def test_graph_uebersteht_den_rundlauf_ueber_dict():
    """Eine Kette muss aufschreibbar und wieder lesbar sein — sonst ist sie kein Datum."""
    g = baue_kette(glb_path="/tmp/m.glb", up_axis="Z", bbox=BBOX_HAUS, prompt="x")
    assert Graph.from_dict(json.loads(json.dumps(g.to_dict()))) == g


def test_weder_ifc_noch_glb_wird_gemeldet():
    with pytest.raises(KettenError, match="Genau einer"):
        baue_kette(prompt="x")


def test_beides_zugleich_wird_gemeldet():
    with pytest.raises(KettenError, match="Genau einer"):
        baue_kette(ifc_path="/tmp/a.ifc", glb_path="/tmp/a.glb", up_axis="Y", prompt="x")


def test_glb_ohne_up_achse_wird_gemeldet():
    """Der Phase-0-Befund: KosmoDraw liefert Z-up, KosmoVis Y-up. Kein Default."""
    with pytest.raises(KettenError, match="up_axis"):
        baue_kette(glb_path="/tmp/m.glb", prompt="x")


def test_up_achse_zusammen_mit_ifc_ist_widerspruechlich():
    with pytest.raises(KettenError, match="widersprüchlich"):
        baue_kette(ifc_path="/tmp/a.ifc", up_axis="Z", prompt="x")


def test_up_achse_wird_normalisiert():
    """KosmoVis schreibt einen ganzen Satz — daraus muss ein 'Y' werden."""
    g = baue_kette(glb_path="/tmp/m.glb", up_axis="Y-up (glTF-Konvention)", prompt="x")
    assert g.knoten[KNOTEN_GEOMETRIE].params["up_axis"] == "Y"


@pytest.mark.parametrize("prompt", [None, "", "   "])
def test_ohne_prompt_gibt_es_keine_kette(prompt):
    with pytest.raises(KettenError, match="prompt"):
        baue_kette(ifc_path="/tmp/a.ifc", prompt=prompt)


def test_bbox_als_tupel_wird_zu_listen():
    """Tupel überstehen die JSON-Runde eines Knotens nicht — die Umschrift passiert hier."""
    g = baue_kette(glb_path="/tmp/m.glb", up_axis="Y", prompt="x",
                   bbox=((0, 0, 0), (8, 5, 3)))
    assert g.knoten[KNOTEN_GEOMETRIE].params["bbox"] == [[0.0, 0.0, 0.0], [8.0, 5.0, 3.0]]


@pytest.mark.parametrize("bbox", ["8x5x3", [[0, 0, 0]], [[0, 0], [8, 5]], [[0, 0, 0], [8, 5, "x"]]])
def test_unbrauchbare_bbox_wird_gemeldet(bbox):
    with pytest.raises(KettenError, match="bbox"):
        baue_kette(glb_path="/tmp/m.glb", up_axis="Y", prompt="x", bbox=bbox)


def test_prompt_und_stellschrauben_landen_im_render_knoten():
    g = baue_kette(ifc_path="/tmp/a.ifc", prompt="Beton, Morgenlicht", seed=7,
                   controlnet_staerke=0.55)
    p = g.knoten[KNOTEN_RENDER].params
    assert (p["prompt"], p["seed"], p["controlnet_staerke"]) == ("Beton, Morgenlicht", 7, 0.55)


# ======================================================================================
# 2 · Lauf: der Zwischenspeicher, an Aufrufen gezählt
# ======================================================================================

def test_erster_lauf_rechnet_alles_und_nichts_kommt_aus_dem_cache(tmp_path):
    ifc = schreibe_ifc(tmp_path / "haus.ifc")
    werkbank, cache = Werkbank(), ArtefaktCache(tmp_path / "cache")

    ergebnis = lauf(baue_kette(ifc_path=str(ifc), prompt="Morgenlicht"),
                    werkbank, cache, tmp_path)

    assert ergebnis["status"] == "ok"
    assert ergebnis["gerechnet"] == 4 and ergebnis["cache_treffer"] == 0
    assert werkbank.aufrufe == Counter(
        {ART_GEOMETRIE: 1, ART_MULTIPASS: 1, ART_RENDER: 1, ART_QA: 1})
    for eintrag in ergebnis["knoten"].values():
        assert eintrag["status"] == "ok"
        assert eintrag["aus_cache"] is False
        assert eintrag["hash"] and eintrag["dauer_s"] >= 0.0


def test_ausgaben_fliessen_in_eingangsreihenfolge_zum_nachfolger(tmp_path):
    """Nicht verschmolzen wie in KosmoOrbits `mergeInputs`, sondern nach Position.

    Das ist der Unterschied zwischen äusserem und innerem Graphen: Aussen entstehen
    Kanten über Feldnamen-Gleichheit, hier über Knoten-IDs und Positionen.
    """
    ifc = schreibe_ifc(tmp_path / "haus.ifc")
    werkbank, cache = Werkbank(), ArtefaktCache(tmp_path / "cache")
    lauf(baue_kette(ifc_path=str(ifc), prompt="x"), werkbank, cache, tmp_path)

    soll, ist = werkbank.eingaben[ART_QA]
    assert "depth_png" in soll, "Slot 0 der QA ist der Multipass (Soll)"
    assert "bild_png" in ist, "Slot 1 der QA ist der Render (Ist)"
    assert werkbank.eingaben[ART_MULTIPASS][0]["glb_path"].endswith("modell.glb")


def test_zweiter_gleicher_lauf_ruft_keinen_einzigen_ausfuehrer(tmp_path):
    ifc = schreibe_ifc(tmp_path / "haus.ifc")
    werkbank, cache = Werkbank(), ArtefaktCache(tmp_path / "cache")
    g = baue_kette(ifc_path=str(ifc), prompt="Morgenlicht")

    lauf(g, werkbank, cache, tmp_path)
    vorher = Counter(werkbank.aufrufe)
    zweiter = lauf(g, werkbank, cache, tmp_path)

    assert werkbank.aufrufe == vorher, "Ein vollständiger Treffer ruft gar nichts"
    assert zweiter["cache_treffer"] == 4 and zweiter["gerechnet"] == 0
    assert all(e["aus_cache"] for e in zweiter["knoten"].values())


def test_nur_der_prompt_geaendert_haelt_geometrie_und_multipass_im_cache(tmp_path):
    """**Der entscheidende Nachweis.**

    Prompt ändern heisst: Der Render-Knoten bekommt andere Parameter, also einen anderen
    Hash — und die QA dahinter ebenfalls, weil der Vorgänger-Hash in ihren eigenen
    einfliesst. Geometrie und Multipass ändern sich nicht und dürfen darum nicht wieder
    anlaufen. Gezählt wird, nicht gemessen: Ihre Ausführer stehen nach dem zweiten Lauf
    weiterhin bei genau einem Aufruf.
    """
    ifc = schreibe_ifc(tmp_path / "haus.ifc")
    werkbank, cache = Werkbank(), ArtefaktCache(tmp_path / "cache")

    lauf(baue_kette(ifc_path=str(ifc), prompt="Morgenlicht"), werkbank, cache, tmp_path)
    zweiter = lauf(baue_kette(ifc_path=str(ifc), prompt="Abendstimmung, warmes Licht"),
                   werkbank, cache, tmp_path)

    assert werkbank.aufrufe[ART_GEOMETRIE] == 1, "teure Geometriestufe lief erneut"
    assert werkbank.aufrufe[ART_MULTIPASS] == 1, "teurer Blender-Multipass lief erneut"
    assert werkbank.aufrufe[ART_RENDER] == 2
    assert werkbank.aufrufe[ART_QA] == 2

    assert zweiter["knoten"][KNOTEN_GEOMETRIE]["aus_cache"] is True
    assert zweiter["knoten"][KNOTEN_MULTIPASS]["aus_cache"] is True
    assert zweiter["knoten"][KNOTEN_RENDER]["aus_cache"] is False
    assert zweiter["knoten"][KNOTEN_QA]["aus_cache"] is False
    assert zweiter["cache_treffer"] == 2 and zweiter["gerechnet"] == 2


def test_geaenderte_geometrie_laesst_alles_dahinter_neu_rechnen(tmp_path):
    """Die Gegenprobe. Gleicher Pfad, anderer **Inhalt** — und die ganze Kette rechnet neu.

    Ohne diese Richtung wäre der Cache kein Cache, sondern ein Fehler: Er lieferte das
    Bild von gestern zur Geometrie von heute.
    """
    ifc = schreibe_ifc(tmp_path / "haus.ifc", "GEOMETRIE-A")
    werkbank, cache = Werkbank(), ArtefaktCache(tmp_path / "cache")
    g = baue_kette(ifc_path=str(ifc), prompt="Morgenlicht")
    lauf(g, werkbank, cache, tmp_path)

    schreibe_ifc(ifc, "GEOMETRIE-B — ein Stockwerk mehr")
    zweiter = lauf(g, werkbank, cache, tmp_path)

    assert werkbank.aufrufe == Counter(
        {ART_GEOMETRIE: 2, ART_MULTIPASS: 2, ART_RENDER: 2, ART_QA: 2})
    assert zweiter["cache_treffer"] == 0
    assert not any(e["aus_cache"] for e in zweiter["knoten"].values())


def test_umbenannte_aber_inhaltsgleiche_eingabe_trifft_weiterhin_den_cache(tmp_path):
    """Der Hash geht über den **Inhalt**, nicht über Pfad oder Zeitstempel.

    Eine kopierte oder verschobene IFC ist dieselbe Geometrie. Über mtime zu gehen wäre
    bequemer und in einer Kette aus Subprozessen fast immer falsch.
    """
    a = schreibe_ifc(tmp_path / "haus.ifc", "GEOMETRIE-A")
    werkbank, cache = Werkbank(), ArtefaktCache(tmp_path / "cache")
    lauf(baue_kette(ifc_path=str(a), prompt="x"), werkbank, cache, tmp_path)

    b = schreibe_ifc(tmp_path / "kopie" / "anders-benannt.ifc", "GEOMETRIE-A")
    zweiter = lauf(baue_kette(ifc_path=str(b), prompt="x"), werkbank, cache, tmp_path)

    assert werkbank.aufrufe[ART_GEOMETRIE] == 1
    assert zweiter["cache_treffer"] == 4


def test_geaenderter_multipass_parameter_haelt_nur_die_geometrie_im_cache(tmp_path):
    """Die Invalidierung wirkt genau eine Stufe tief — dort, wo sich etwas geändert hat."""
    ifc = schreibe_ifc(tmp_path / "haus.ifc")
    werkbank, cache = Werkbank(), ArtefaktCache(tmp_path / "cache")
    lauf(baue_kette(ifc_path=str(ifc), prompt="x", samples=16), werkbank, cache, tmp_path)
    zweiter = lauf(baue_kette(ifc_path=str(ifc), prompt="x", samples=64),
                   werkbank, cache, tmp_path)

    assert werkbank.aufrufe == Counter(
        {ART_GEOMETRIE: 1, ART_MULTIPASS: 2, ART_RENDER: 2, ART_QA: 2})
    assert zweiter["knoten"][KNOTEN_GEOMETRIE]["aus_cache"] is True
    assert zweiter["knoten"][KNOTEN_MULTIPASS]["aus_cache"] is False


def test_ohne_cache_rechnet_jeder_lauf_alles(tmp_path):
    ifc = schreibe_ifc(tmp_path / "haus.ifc")
    werkbank = Werkbank()
    g = baue_kette(ifc_path=str(ifc), prompt="x")

    lauf(g, werkbank, None, tmp_path)
    zweiter = lauf(g, werkbank, None, tmp_path)

    assert werkbank.aufrufe[ART_GEOMETRIE] == 2
    assert zweiter["cache_treffer"] == 0
    assert not any(e["aus_cache"] for e in zweiter["knoten"].values())


def test_cache_treffer_traegt_die_dauer_der_urspruenglichen_rechnung(tmp_path):
    """Ohne `dauer_s_original` sähe man nur, dass es schnell ging — nicht, was gespart wurde."""
    ifc = schreibe_ifc(tmp_path / "haus.ifc")
    werkbank, cache = Werkbank(), ArtefaktCache(tmp_path / "cache")
    g = baue_kette(ifc_path=str(ifc), prompt="x")
    erster = lauf(g, werkbank, cache, tmp_path)
    zweiter = lauf(g, werkbank, cache, tmp_path)

    original = erster["knoten"][KNOTEN_MULTIPASS]["dauer_s"]
    aus_cache = zweiter["knoten"][KNOTEN_MULTIPASS]
    assert aus_cache["dauer_s_original"] == original
    assert aus_cache["dauer_s"] >= 0.0


def test_geloeschte_ausgabedatei_verwirft_den_cache_eintrag(tmp_path):
    """Ein Eintrag, dessen Dateien es nicht mehr gibt, ist eine Zusage ins Leere."""
    ifc = schreibe_ifc(tmp_path / "haus.ifc")
    werkbank, cache = Werkbank(), ArtefaktCache(tmp_path / "cache")
    g = baue_kette(ifc_path=str(ifc), prompt="x")
    erster = lauf(g, werkbank, cache, tmp_path)

    Path(erster["knoten"][KNOTEN_MULTIPASS]["ausgaben"]["depth_png"]).unlink()
    zweiter = lauf(g, werkbank, cache, tmp_path)

    assert werkbank.aufrufe[ART_GEOMETRIE] == 1, "die Geometrie ist unberührt"
    assert werkbank.aufrufe[ART_MULTIPASS] == 2, "die fehlende Tiefenkarte wird neu gerechnet"
    assert zweiter["knoten"][KNOTEN_MULTIPASS]["aus_cache"] is False


def test_arbeitsverzeichnis_haengt_am_hash_und_nicht_am_knotennamen(tmp_path):
    """Zwei Stände derselben Stufe dürfen sich nicht gegenseitig überschreiben.

    Der Cache speichert Pfade, nicht Bilder. Schrieben beide Läufe in denselben Ordner,
    zeigte der ältere Eintrag danach auf den neueren Inhalt — ein Cache, der falsche
    Treffer liefert, ist schlimmer als keiner.
    """
    ifc = schreibe_ifc(tmp_path / "haus.ifc")
    werkbank, cache = Werkbank(), ArtefaktCache(tmp_path / "cache")
    a = lauf(baue_kette(ifc_path=str(ifc), prompt="A"), werkbank, cache, tmp_path)
    b = lauf(baue_kette(ifc_path=str(ifc), prompt="B"), werkbank, cache, tmp_path)

    assert a["knoten"][KNOTEN_RENDER]["arbeits_dir"] != b["knoten"][KNOTEN_RENDER]["arbeits_dir"]
    assert a["knoten"][KNOTEN_GEOMETRIE]["arbeits_dir"] == b["knoten"][KNOTEN_GEOMETRIE]["arbeits_dir"]
    assert Path(a["knoten"][KNOTEN_RENDER]["ausgaben"]["bild_png"]).read_text() == "bild zu A"
    assert Path(b["knoten"][KNOTEN_RENDER]["ausgaben"]["bild_png"]).read_text() == "bild zu B"


# ======================================================================================
# 3 · Fehler, Überspringen, und was nicht gespeichert wird
# ======================================================================================

def test_gescheiterter_knoten_laesst_die_nachfolger_aus(tmp_path):
    """Skip-on-Error: Mit halben Eingaben weiterzurechnen erzeugt schlimmstenfalls ein
    plausibel aussehendes Bild auf falscher Grundlage."""
    ifc = schreibe_ifc(tmp_path / "haus.ifc")
    werkbank = Werkbank()
    tabelle = werkbank.tabelle()

    def kaputt(*, knoten, eingaben, out_dir):
        werkbank.aufrufe[ART_MULTIPASS] += 1
        raise seams.SeamError("Blender endete mit Code 1")

    tabelle[ART_MULTIPASS] = kaputt
    ergebnis = fuehre_aus(baue_kette(ifc_path=str(ifc), prompt="x"),
                          cache=ArtefaktCache(tmp_path / "cache"),
                          ausfuehrer=tabelle, out_dir=tmp_path / "out")

    assert ergebnis["status"] == "fehler"
    assert ergebnis["gescheitert"] == [KNOTEN_MULTIPASS]
    assert ergebnis["uebersprungen"] == [KNOTEN_QA, KNOTEN_RENDER]
    assert ergebnis["knoten"][KNOTEN_MULTIPASS]["status"] == "fehler"
    assert "SeamError" in ergebnis["knoten"][KNOTEN_MULTIPASS]["error"]
    assert ergebnis["knoten"][KNOTEN_RENDER]["status"] == "uebersprungen"
    assert "multipass" in ergebnis["knoten"][KNOTEN_QA]["grund"]
    assert werkbank.aufrufe[ART_RENDER] == 0, "der Render wurde gar nicht erst versucht"
    assert werkbank.aufrufe[ART_QA] == 0


def test_ablehnung_bleibt_ablehnung_und_wird_nicht_zu_fehler(tmp_path):
    """`abgelehnt` und `fehler` sind verschiedene Lager — sonst sucht man die Ursache falsch."""
    ifc = schreibe_ifc(tmp_path / "haus.ifc")
    werkbank = Werkbank()
    tabelle = werkbank.tabelle()
    tabelle[ART_GEOMETRIE] = lambda *, knoten, eingaben, out_dir: {
        "status": "abgelehnt", "error": "Torwächter: Massstab unplausibel"}

    ergebnis = fuehre_aus(baue_kette(ifc_path=str(ifc), prompt="x"),
                          cache=ArtefaktCache(tmp_path / "cache"),
                          ausfuehrer=tabelle, out_dir=tmp_path / "out")

    assert ergebnis["knoten"][KNOTEN_GEOMETRIE]["status"] == "abgelehnt"
    assert len(ergebnis["uebersprungen"]) == 3
    assert werkbank.aufrufe.total() == 0


def test_fehlschlaege_landen_nicht_im_cache(tmp_path):
    """Ein Fehlschlag sagt meist etwas über die Umgebung, nicht über die Rechnung.

    Würde er gespeichert, meldete der nächste Lauf ein längst behobenes Problem aus dem
    Gedächtnis — der Cache wäre ein Gedächtnis für Pannen.
    """
    ifc = schreibe_ifc(tmp_path / "haus.ifc")
    cache = ArtefaktCache(tmp_path / "cache")
    aufrufe = Counter()

    def wackelig(*, knoten, eingaben, out_dir):
        aufrufe[ART_GEOMETRIE] += 1
        if aufrufe[ART_GEOMETRIE] == 1:
            return {"status": "fehler", "error": ".venv-ifc nicht gefunden"}
        return {"glb_path": str(out_dir / "m.glb"), "up_axis": "Y"}

    werkbank = Werkbank()
    tabelle = {**werkbank.tabelle(), ART_GEOMETRIE: wackelig}
    g = baue_kette(ifc_path=str(ifc), prompt="x")

    erster = fuehre_aus(g, cache=cache, ausfuehrer=tabelle, out_dir=tmp_path / "out")
    assert erster["status"] == "fehler"
    (tmp_path / "out").mkdir(exist_ok=True)

    zweiter = fuehre_aus(g, cache=cache, ausfuehrer=tabelle, out_dir=tmp_path / "out")
    assert aufrufe[ART_GEOMETRIE] == 2, "der Fehlschlag wurde nicht als Treffer geliefert"
    assert zweiter["knoten"][KNOTEN_GEOMETRIE]["aus_cache"] is False


def test_fehlende_eingabedatei_scheitert_am_hash_und_nicht_am_lauf(tmp_path):
    """Ohne Datei kein Inhalts-Hash — und ohne Hash kein Lauf, der etwas beweisen könnte.

    Bewusst kein Abbruch des ganzen Laufs: Der Knoten scheitert, der Rest wird
    übersprungen, und das Protokoll nennt den Grund.
    """
    werkbank = Werkbank()
    ergebnis = fuehre_aus(baue_kette(ifc_path=str(tmp_path / "gibt-es-nicht.ifc"), prompt="x"),
                          cache=ArtefaktCache(tmp_path / "cache"),
                          ausfuehrer=werkbank.tabelle(), out_dir=tmp_path / "out")

    assert ergebnis["knoten"][KNOTEN_GEOMETRIE]["status"] == "fehler"
    assert "Hash nicht bildbar" in ergebnis["knoten"][KNOTEN_GEOMETRIE]["error"]
    assert werkbank.aufrufe.total() == 0
    assert len(ergebnis["uebersprungen"]) == 3


def test_ausfuehrer_der_kein_woerterbuch_liefert_ist_ein_fehler(tmp_path):
    ifc = schreibe_ifc(tmp_path / "haus.ifc")
    tabelle = {**Werkbank().tabelle(),
               ART_GEOMETRIE: lambda *, knoten, eingaben, out_dir: "/tmp/modell.glb"}
    ergebnis = fuehre_aus(baue_kette(ifc_path=str(ifc), prompt="x"), cache=None,
                          ausfuehrer=tabelle, out_dir=tmp_path / "out")

    assert ergebnis["knoten"][KNOTEN_GEOMETRIE]["status"] == "fehler"
    assert "dict" in ergebnis["knoten"][KNOTEN_GEOMETRIE]["error"]


def test_nicht_speicherbares_ergebnis_meldet_sich_ohne_den_knoten_zu_stuerzen(tmp_path):
    """Der Knoten hat gerechnet und ist gelungen — nur ablegen lässt er sich nicht.

    Stillschweigend übergangen würde es heissen: Der Cache greift nie, und niemand weiss
    warum.
    """
    ifc = schreibe_ifc(tmp_path / "haus.ifc")
    tabelle = {**Werkbank().tabelle(),
               ART_GEOMETRIE: lambda *, knoten, eingaben, out_dir: {
                   "glb_path": str(out_dir / "m.glb"), "unspeicherbar": {1, 2}}}
    ergebnis = fuehre_aus(baue_kette(ifc_path=str(ifc), prompt="x"),
                          cache=ArtefaktCache(tmp_path / "cache"),
                          ausfuehrer=tabelle, out_dir=tmp_path / "out")

    knoten = ergebnis["knoten"][KNOTEN_GEOMETRIE]
    assert knoten["status"] == "ok"
    assert knoten["cache_fehler"] and "JSON" in knoten["cache_fehler"]


def test_knotenart_ohne_ausfuehrer_wird_vor_dem_ersten_knoten_gemeldet(tmp_path):
    """Fail-fast: Eine halb gelaufene Kette hinterlässt Dateien, die zu nichts gehören."""
    ifc = schreibe_ifc(tmp_path / "haus.ifc")
    werkbank = Werkbank()
    tabelle = werkbank.tabelle()
    del tabelle[ART_QA]

    with pytest.raises(KettenError, match="qa"):
        fuehre_aus(baue_kette(ifc_path=str(ifc), prompt="x"), cache=None,
                   ausfuehrer=tabelle, out_dir=tmp_path / "out")
    assert werkbank.aufrufe.total() == 0


def test_ausfuehrer_tabelle_ersetzt_und_ergaenzt_nicht(tmp_path):
    """Eine stille Ergänzung hiesse: Ein Test, der eine Attrappe vergisst, startet Blender."""
    ifc = schreibe_ifc(tmp_path / "haus.ifc")
    nur_geometrie = {ART_GEOMETRIE: Werkbank().geometrie}
    with pytest.raises(KettenError, match="multipass"):
        fuehre_aus(baue_kette(ifc_path=str(ifc), prompt="x"), cache=None,
                   ausfuehrer=nur_geometrie, out_dir=tmp_path / "out")


def test_kein_graph_wird_gemeldet():
    with pytest.raises(KettenError, match="Graph"):
        fuehre_aus({"schema": "aiimaging.graph/v1", "knoten": []})


def test_kreis_hat_keine_reihenfolge(tmp_path):
    """Der Kreis fällt weiterhin dort an, wo er hingehört — in der Sortierung."""
    kreis = Graph([
        Knoten(id="a", art=ART_RENDER, eingaenge=("b",)),
        Knoten(id="b", art=ART_RENDER, eingaenge=("a",)),
    ])
    with pytest.raises(ZyklusError):
        fuehre_aus(kreis, cache=None, ausfuehrer={ART_RENDER: lambda **kw: {}},
                   out_dir=tmp_path / "out")


# ======================================================================================
# 4 · Die eingebauten Ausführer, soweit ohne Blender und ohne GPU prüfbar
# ======================================================================================

def test_ausfuehrer_deckt_alle_arten_der_standardkette_ab():
    g = baue_kette(ifc_path="/tmp/a.ifc", prompt="x")
    assert {k.art for k in g.knoten.values()} <= set(kette.AUSFUEHRER)


def test_geometriestufe_reicht_glb_durch_und_laesst_den_torwaechter_urteilen(tmp_path):
    knoten = baue_kette(glb_path="/tmp/m.glb", up_axis="Z", bbox=BBOX_HAUS,
                        prompt="x").knoten[KNOTEN_GEOMETRIE]
    ausgaben = kette.AUSFUEHRER[ART_GEOMETRIE](knoten=knoten, eingaben=[], out_dir=tmp_path)

    assert ausgaben["status"] == "ok"
    assert (ausgaben["glb_path"], ausgaben["up_axis"]) == ("/tmp/m.glb", "Z")
    assert ausgaben["torwaechter"]["entscheidung"] == torwaechter.ENTSCHEIDUNG_ANNEHMEN


def test_geometriestufe_lehnt_millimeter_als_meter_ab(tmp_path):
    """Der Befund aus dem Vorläufer: Konversion meldet 'ok', das Modell ist 30 km gross.

    Die Ablehnung fällt hier — vor Blender, vor der GPU.
    """
    knoten = baue_kette(glb_path="/tmp/m.glb", up_axis="Z", prompt="x",
                        bbox=[[0, 0, 0], [8000, 5000, 3000]]).knoten[KNOTEN_GEOMETRIE]
    ausgaben = kette.AUSFUEHRER[ART_GEOMETRIE](knoten=knoten, eingaben=[], out_dir=tmp_path)

    assert ausgaben["status"] == "abgelehnt"
    assert ausgaben["torwaechter"]["entscheidung"] == torwaechter.ENTSCHEIDUNG_ABLEHNEN_MASSSTAB
    assert "1000" in ausgaben["error"]


def test_geometriestufe_ohne_bbox_wird_nicht_durchgewunken(tmp_path):
    """Ungeprüft wird nicht gerendert — dieselbe Linie wie `werkzeuge.enqueue_render`."""
    knoten = baue_kette(glb_path="/tmp/m.glb", up_axis="Y", prompt="x").knoten[KNOTEN_GEOMETRIE]
    ausgaben = kette.AUSFUEHRER[ART_GEOMETRIE](knoten=knoten, eingaben=[], out_dir=tmp_path)
    assert ausgaben["status"] == "abgelehnt"


def test_multipassstufe_ohne_glb_meldet_das_fehlende_feld(tmp_path):
    knoten = baue_kette(ifc_path="/tmp/a.ifc", prompt="x").knoten[KNOTEN_MULTIPASS]
    ausgaben = kette.AUSFUEHRER[ART_MULTIPASS](knoten=knoten, eingaben=[{"up_axis": "Y"}],
                                               out_dir=tmp_path)
    assert ausgaben["status"] == "fehler" and "glb_path" in ausgaben["error"]


def test_renderstufe_ohne_tiefenkarte_meldet_das_fehlende_feld(tmp_path):
    """Ohne Tiefenkarte gäbe es keine Konditionierung — das Modell erfände die Kubatur."""
    knoten = baue_kette(ifc_path="/tmp/a.ifc", prompt="x").knoten[KNOTEN_RENDER]
    ausgaben = kette.AUSFUEHRER[ART_RENDER](knoten=knoten, eingaben=[{"beauty_png": "b.png"}],
                                            out_dir=tmp_path)
    assert ausgaben["status"] == "fehler" and "depth_png" in ausgaben["error"]


def test_qastufe_erfindet_keine_ist_werte(tmp_path):
    """Die monokulare Tiefenschätzung fehlt noch (PLAN.md, Phase 4). Das wird gesagt."""
    knoten = baue_kette(ifc_path="/tmp/a.ifc", prompt="x").knoten[KNOTEN_QA]
    ausgaben = kette.AUSFUEHRER[ART_QA](
        knoten=knoten, eingaben=[{"depth_png": "t.png"}, {"bild_png": "b.png"}],
        out_dir=tmp_path)
    assert ausgaben["status"] == "fehler"
    assert "Tiefenschätzung" in ausgaben["error"] and "Phase 4" in ausgaben["error"]


def test_qastufe_braucht_beide_eingaenge(tmp_path):
    knoten = baue_kette(ifc_path="/tmp/a.ifc", prompt="x").knoten[KNOTEN_QA]
    ausgaben = kette.AUSFUEHRER[ART_QA](knoten=knoten, eingaben=[{"depth_png": "t.png"}],
                                        out_dir=tmp_path)
    assert ausgaben["status"] == "fehler" and "zwei Eingänge" in ausgaben["error"]


def test_nicht_bestandenes_gate_ist_ein_ergebnis_und_kein_fehlschlag(tmp_path, monkeypatch):
    """Der interessanteste Fall des Projekts — die erkannte Halluzination — muss als
    Messwert lesbar bleiben und darf nicht hinter einem Skip verschwinden.

    Soll und Ist zeigen denselben Verlauf, aber an verschieden gelegenen Stellen: Die
    Rangkorrelation ist über den gemeinsamen Bereich perfekt, die Silhouetten überdecken
    sich nur zu einem Fünftel. Genau der Fall, den nur die Silhouette fängt.
    """
    from aiimaging import bildlesen

    hintergrund = 1e10
    soll = [1.0 + i / 1000 if i < 600 else hintergrund for i in range(1000)]
    ist = [1.0 + i / 1000 if i >= 400 else hintergrund for i in range(1000)]
    monkeypatch.setattr(bildlesen, "tiefen_aus_report", lambda report, **kw: (soll, 10, 10))

    knoten = Knoten(id=KNOTEN_QA, art=ART_QA, params={"schwelle": 0.65, "hintergrund": None},
                    eingaenge=(KNOTEN_MULTIPASS, KNOTEN_RENDER))
    ausgaben = kette.AUSFUEHRER[ART_QA](
        knoten=knoten, eingaben=[{"depth_exr": "t.exr"}, {"ist_tiefen": ist}], out_dir=tmp_path)

    assert ausgaben["status"] == "ok", "gerechnet ist gerechnet"
    assert ausgaben["bestanden"] is False
    assert ausgaben["score"] is not None and ausgaben["score"] < 0.65
    assert ausgaben["geom_iou"] == pytest.approx(0.2)


# ======================================================================================
# 5 · Der echte Lauf — über beide Prozessgrenzen, nur das Bildmodell bleibt Attrappe
# ======================================================================================

def blender_fehlt() -> bool:
    try:
        return not Path(seams.finde_blender()).exists()
    except seams.SeamError:
        return True


def ifc_venv_fehlt() -> bool:
    try:
        return not Path(seams.finde_ifc_python()).exists()
    except seams.SeamError:
        return True


ohne_prozessgrenzen = pytest.mark.skipif(
    blender_fehlt() or ifc_venv_fehlt(),
    reason="Blender oder .venv-ifc fehlt — der Lauf über die Prozessgrenzen entfällt",
)

#: Klein und wenige Samples: Dieser Test prüft die Verkettung, nicht die Bildqualität.
AUFLOESUNG, SAMPLES = 96, 4


@ohne_prozessgrenzen
def test_echter_lauf_ueber_beide_prozessgrenzen_und_dann_aus_dem_cache(tmp_path):
    """IFC→glb und Multipass wirklich, QA wirklich, Bildmodell als Attrappe.

    Der zweite Teil ist der eigentliche Punkt: Nach einer blossen Prompt-Änderung darf
    **kein** Subprozess mehr starten. Gezählt wird an den echten Ausführern.

    Das Bildmodell bleibt eine Attrappe, weil es keine GPU gibt. Sie reicht die
    Soll-Tiefe als Ist-Tiefe zurück — der hypothetische, perfekt geometrietreue Render.
    Damit rechnet die QA an **echten** Blender-Zahlen und muss nahe 1.0 landen; ein
    Verdrehen der Achsen oder ein vertauschter Slot fiele hier sofort auf.
    """
    from aiimaging import bildlesen

    ifc = tmp_path / "haus.ifc"
    subprocess.run([sys.executable, str(REPO / "tools" / "make_test_ifc.py"), str(ifc)],
                   check=True, capture_output=True)

    aufrufe: Counter = Counter()

    def zaehlend(art):
        echt = kette.AUSFUEHRER[art]

        def huelle(*, knoten, eingaben, out_dir):
            aufrufe[art] += 1
            return echt(knoten=knoten, eingaben=eingaben, out_dir=out_dir)
        return huelle

    def render_attrappe(*, knoten, eingaben, out_dir):
        aufrufe[ART_RENDER] += 1
        bild = out_dir / "bild.png"
        bild.write_text(f"Attrappe: {knoten.params['prompt']}", encoding="utf-8")
        tiefen, _, _ = bildlesen.tiefen_aus_report(eingaben[0])
        return {"status": "ok", "bild_png": str(bild), "ist_tiefen": tiefen}

    tabelle = {
        ART_GEOMETRIE: zaehlend(ART_GEOMETRIE),
        ART_MULTIPASS: zaehlend(ART_MULTIPASS),
        ART_RENDER: render_attrappe,
        ART_QA: zaehlend(ART_QA),
    }
    cache = ArtefaktCache(tmp_path / "cache")

    def starte(prompt):
        return fuehre_aus(
            baue_kette(ifc_path=str(ifc), prompt=prompt, aufloesung=AUFLOESUNG,
                       samples=SAMPLES, material_id=False),
            cache=cache, ausfuehrer=tabelle, out_dir=tmp_path / "out")

    erster = starte("Sichtbeton, Morgenlicht")

    assert erster["status"] == "ok", erster["error"]
    geometrie = erster["knoten"][KNOTEN_GEOMETRIE]["ausgaben"]
    assert Path(geometrie["glb_path"]).is_file()
    assert geometrie["up_axis"] == "Y"
    multipass = erster["knoten"][KNOTEN_MULTIPASS]["ausgaben"]
    assert Path(multipass["depth_exr"]).is_file() and Path(multipass["depth_png"]).is_file()
    qa = erster["knoten"][KNOTEN_QA]["ausgaben"]
    assert qa["bestanden"] is True and qa["score"] > 0.99, qa.get("begruendung")
    assert aufrufe == Counter({ART_GEOMETRIE: 1, ART_MULTIPASS: 1, ART_RENDER: 1, ART_QA: 1})

    zweiter = starte("Abendstimmung, warmes Licht")

    assert aufrufe[ART_GEOMETRIE] == 1, "die IFC-Konversion lief ein zweites Mal"
    assert aufrufe[ART_MULTIPASS] == 1, "Blender lief ein zweites Mal"
    assert aufrufe[ART_RENDER] == 2
    assert zweiter["cache_treffer"] == 2
    assert zweiter["knoten"][KNOTEN_MULTIPASS]["ausgaben"]["depth_exr"] == multipass["depth_exr"]

    dritter = starte("Sichtbeton, Morgenlicht")
    assert dritter["cache_treffer"] == 4, "der erste Prompt liegt vollständig im Speicher"
    assert aufrufe.total() == 6
