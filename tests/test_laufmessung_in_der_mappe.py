"""Was der Lauf gemessen hat, muss **in der Mappe** wiederzufinden sein.

**Der Befund (22.09.2026):** :func:`aiimaging.arbeitsgang.rechne` schrieb vom Lauf nur
sechs Zusammenfassungsfelder in die Projektdatei — Status, Gerechnetes, Treffer,
Gescheitertes, Dauer, Fehler. Alles, was die Renderstufe über *diesen* Lauf gemessen
hatte, blieb im Knotenergebnis liegen und wurde dort nie wieder gelesen:
``modus_bestellt``, ``modus_gerechnet``, ``modus_abweichung``, ``hinweise``,
``schritte_gerechnet``, ``geraeteweg``.

Nachgestellt: Ein Render-Knoten meldete ``modus_bestellt='image_edit'``,
``modus_gerechnet='txt2img'``, ``modus_abweichung=True`` und den Satz «BESTELLT WAR …» —
in der geschriebenen Projektdatei kam keines dieser Wörter vor.

**Und es wiegt schwer.** ``modus_abweichung`` wurde am 21.09.2026 eigens verdrahtet,
weil es zuvor eine Funktion vor dem Leser weggeworfen wurde
(``tests/test_modus_kommt_an.py``). Eine Ebene später wurde es wieder weggeworfen — die
dritte Fundstelle derselben Fehlerart in einer Woche.

    *Eine Auskunft, die eine Ebene früher wegfällt, als der Leser sie braucht, gibt es
    für den Leser nicht — und es ist gleichgültig, welche Ebene es war.*

**Wie hier geprüft wird.** Jeder Wächter fährt den **Produktweg** (``rechne``), schreibt
die Mappe und liest sie danach **von der Platte zurück**. Kein Blick auf das
zurückgegebene Wörterbuch im Arbeitsspeicher und kein Textvergleich am Quelltext: Was
nicht durch Schreiben und Öffnen kommt, gibt es für den Leser der Mappe nicht.

**Ohne GPU, ohne Blender, ohne Gewichte** — alle Knoten sind Attrappen.
"""
from __future__ import annotations

import json
import struct
from pathlib import Path

import pytest

from aiimaging import arbeitsgang, kette, projekt
from aiimaging.kette import ART_GEOMETRIE, ART_MULTIPASS, ART_QA, ART_RENDER

#: Der Satz, den der Adapter schreibt, wenn das Ausgangsbild nicht angekommen ist.
ABWEICHUNG = (
    "BESTELLT WAR 'image_edit', GERECHNET WURDE 'txt2img': Das Ausgangsbild ist bei "
    "dieser Pipeline nicht angekommen.")


# ------------------------------------------------------------------- die Attrappen

class Werkbank:
    """Ersatz-Ausführer für die vier Knotenarten.

    Die Attrappen schreiben **echte** Dateien — eine, die nur Pfade behauptet, ergäbe
    einen Fehltreffer im Zwischenspeicher und der Wächter bewiese etwas anderes als
    gedacht.

    ``rendermeldung`` ist das, was die Renderstufe über ihren eigenen Lauf meldet. Leer
    heisst: **eine schweigende Naht**, und das ist der zweite geprüfte Fall.
    """

    def __init__(self, *, rendermeldung: dict | None = None,
                 render_faellt: bool = False) -> None:
        self.rendermeldung = dict(rendermeldung or {})
        self.render_faellt = render_faellt

    def tabelle(self) -> dict:
        return {ART_GEOMETRIE: self.geometrie, ART_MULTIPASS: self.multipass,
                ART_RENDER: self.render, ART_QA: self.qa}

    def geometrie(self, *, knoten, eingaben, out_dir):
        glb = Path(out_dir) / "modell.glb"
        glb.write_text("glb", encoding="utf-8")
        return {"glb_path": str(glb), "up_axis": "Y",
                "bbox": [[0, 0, 0], [8.0, 5.0, 3.25]]}

    def multipass(self, *, knoten, eingaben, out_dir):
        tiefe, beauty = Path(out_dir) / "tiefe_norm.png", Path(out_dir) / "beauty.png"
        tiefe.write_text("tiefe", encoding="utf-8")
        beauty.write_text("beauty", encoding="utf-8")
        return {"status": "ok", "depth_png": str(tiefe), "beauty_png": str(beauty),
                "aufloesung": knoten.params["aufloesung"],
                "samples": knoten.params["samples"]}

    def render(self, *, knoten, eingaben, out_dir):
        if self.render_faellt:
            return {"status": "fehler", "error": "Die Karte ist voll.",
                    **self.rendermeldung}
        bild = Path(out_dir) / "bild.png"
        bild.write_text("bild", encoding="utf-8")
        return {"status": "ok", "bild_png": str(bild), "seed": knoten.params["seed"],
                **self.rendermeldung}

    def qa(self, *, knoten, eingaben, out_dir):
        return {"status": "ok", "bestanden": True, "score": 0.91,
                "schwelle": knoten.params["schwelle"]}


@pytest.fixture
def glb(tmp_path):
    """Ein gültiges glb — Weg «durchgereicht», also ohne jeden Subprozess."""
    js = json.dumps({"asset": {"version": "2.0", "generator": "Testfixture"}}).encode()
    js += b" " * (-len(js) % 4)
    block = struct.pack("<II", len(js), 0x4E4F534A) + js
    pfad = tmp_path / "quelle" / "haus.glb"
    pfad.parent.mkdir(parents=True, exist_ok=True)
    pfad.write_bytes(struct.pack("<4sII", b"glTF", 2, 12 + len(block)) + block)
    return pfad


@pytest.fixture
def mappe(tmp_path, glb):
    wurzel = tmp_path / "projekt"
    arbeitsgang.lege_an(wurzel, glb, name="Wohnhaus Nord",
                        einstellungen={"prompt": "Abendlicht", "seed": 7, "up_axis": "Y"})
    return wurzel


def _von_der_platte(wurzel) -> dict:
    """Die Mappe **neu geöffnet**, nicht das Wörterbuch aus dem Arbeitsspeicher.

    Der Unterschied ist der ganze Befund: Das zurückgegebene Wörterbuch hätte den Wert
    auch dann, wenn er beim Schreiben verlorenginge.
    """
    return projekt.oeffne(wurzel)["projekt"]


def _letzter_lauf(wurzel) -> dict:
    return _von_der_platte(wurzel)["laeufe"][-1]


# --------------------------------------------------------- 1 · die Abweichung kommt an

def test_eine_abweichung_ist_nach_dem_speichern_in_der_mappe_zu_finden(mappe):
    """Der Wächter für den gemeldeten Befund.

    Der Knoten meldet, dass etwas anderes gerechnet wurde als bestellt. Nach dem
    Speichern muss das in der wieder geöffneten Mappe stehen — sonst ist der Lauf
    entwertet, und niemand sieht es.
    """
    werk = Werkbank(rendermeldung={"modus_bestellt": "image_edit",
                                   "modus_gerechnet": "txt2img",
                                   "modus_abweichung": True,
                                   "hinweise": [ABWEICHUNG]})

    arbeitsgang.rechne(mappe, ausfuehrer=werk.tabelle())

    lauf = _letzter_lauf(mappe)
    assert lauf["modus_abweichungen"], (
        "der Lauf hat eine Abweichung gemeldet, und in der Mappe steht keine")
    eintrag = lauf["modus_abweichungen"][0]
    assert eintrag["bestellt"] == "image_edit"
    assert eintrag["gerechnet"] == "txt2img"
    assert ABWEICHUNG in eintrag["hinweise"], (
        "der Satz, der den Lauf entwertet, gehoert mit zur Abweichung")


def test_die_abweichung_haengt_auch_am_einzelnen_bild(mappe):
    """Wer ein Bild ansieht, sieht nicht den Lauf.

    Ein entwertetes Bild darf nicht aussehen wie jedes andere, nur weil der Leser eine
    Ebene höher nicht nachgesehen hat.
    """
    werk = Werkbank(rendermeldung={"modus_bestellt": "image_edit",
                                   "modus_gerechnet": "txt2img",
                                   "modus_abweichung": True,
                                   "hinweise": [ABWEICHUNG]})

    arbeitsgang.rechne(mappe, ausfuehrer=werk.tabelle())

    bild = _von_der_platte(mappe)["bilder"][0]
    messung = bild["herkunft"]["messung"]
    assert messung["modus_abweichung"] is True
    assert messung["modus_bestellt"] == "image_edit"
    assert messung["modus_gerechnet"] == "txt2img"


def test_das_wort_der_abweichung_steht_im_text_der_projektdatei(mappe):
    """Grob, aber genau der nachgestellte Befund: keines dieser Wörter kam vor.

    Geprüft wird die **geschriebene Datei**, nicht der Quelltext — die Wirkung also, und
    nicht die Stellung einer Zeile.
    """
    werk = Werkbank(rendermeldung={"modus_bestellt": "image_edit",
                                   "modus_gerechnet": "txt2img",
                                   "modus_abweichung": True,
                                   "hinweise": [ABWEICHUNG]})

    ergebnis = arbeitsgang.rechne(mappe, ausfuehrer=werk.tabelle())

    text = Path(ergebnis["pfad"]).read_text(encoding="utf-8")
    assert "image_edit" in text
    assert "txt2img" in text
    assert "BESTELLT WAR" in text


# ------------------------------------------------- 2 · die dritte Antwort bleibt stehen

def test_eine_schweigende_naht_wird_nicht_zu_keiner_abweichung(mappe):
    """``None`` heisst **nicht gemessen** — und nicht «war gleich».

    Ohne die zweite Liste hiesse eine leere Abweichungsliste zweierlei: «niemand hat
    abweichend gerechnet» und «niemand hat hingesehen». Die beiden dürfen in einer Mappe
    nicht gleich aussehen.
    """
    arbeitsgang.rechne(mappe, ausfuehrer=Werkbank().tabelle())

    lauf = _letzter_lauf(mappe)
    assert lauf["modus_abweichungen"] == []
    assert kette.KNOTEN_RENDER in lauf["modus_ungemessen"], (
        "die schweigende Stufe muss als ungemessen dastehen, sonst liest sich die leere "
        "Abweichungsliste wie ein Freispruch")
    assert lauf["messungen"][kette.KNOTEN_RENDER]["modus_abweichung"] is None
    assert lauf["messungen"][kette.KNOTEN_RENDER]["hinweise"] is None, (
        "keine Meldung ist etwas anderes als eine Meldung ohne Hinweise")


def test_gemessen_und_gleich_ist_nicht_ungemessen(mappe):
    """Der Gegenfall: Die Naht hat geantwortet, und es passte.

    ``False`` ist ein Messwert. Er darf nicht in derselben Liste landen wie das
    Schweigen.
    """
    werk = Werkbank(rendermeldung={"modus_bestellt": "txt2img",
                                   "modus_gerechnet": "txt2img",
                                   "modus_abweichung": False,
                                   "hinweise": []})

    arbeitsgang.rechne(mappe, ausfuehrer=werk.tabelle())

    lauf = _letzter_lauf(mappe)
    assert lauf["modus_abweichungen"] == []
    assert lauf["modus_ungemessen"] == [], (
        "gemessen und gleich ist nicht dasselbe wie nicht gemessen")
    assert lauf["messungen"][kette.KNOTEN_RENDER]["modus_abweichung"] is False
    assert lauf["messungen"][kette.KNOTEN_RENDER]["hinweise"] == [], (
        "gemessen und nichts zu sagen bleibt eine leere Liste und wird nicht None")


# --------------------------------------------------- 3 · die übrigen vier Messungen

def test_schrittzahl_und_geraeteweg_erreichen_die_mappe(mappe):
    """``schritte_gerechnet`` und ``geraeteweg`` sind gemessen und landeten nirgends.

    Der Gerätweg kostete am 25.08.2026 drei Stunden Suche, weil er gemessen wurde und
    nirgends stand. Dass er eine Ebene später wieder wegfiel, ist derselbe Verlust.
    """
    werk = Werkbank(rendermeldung={
        "schritte_gerechnet": 12,
        "geraeteweg": {"geraet": "cuda", "ladeweg": "ganz", "entflechtung": None,
                       "bedarf": None, "gemeldet": True, "grund": ""}})

    arbeitsgang.rechne(mappe, ausfuehrer=werk.tabelle())

    messung = _letzter_lauf(mappe)["messungen"][kette.KNOTEN_RENDER]
    assert messung["schritte_gerechnet"] == 12
    assert messung["geraeteweg"]["geraet"] == "cuda"
    assert messung["geraeteweg"]["gemeldet"] is True


def test_eine_ungemessene_schrittzahl_bleibt_none_und_wird_nicht_null(mappe):
    """Aus «unbekannt» darf keine Null werden — sie sähe aus wie ein Messwert."""
    arbeitsgang.rechne(mappe, ausfuehrer=Werkbank().tabelle())

    messung = _letzter_lauf(mappe)["messungen"][kette.KNOTEN_RENDER]
    assert messung["schritte_gerechnet"] is None
    assert messung["geraeteweg"] is None


def test_jedes_messfeld_steht_in_der_mappe(mappe):
    """Kein Feld fällt still weg — auch keines, das gerade nichts zu sagen hat.

    Ein fehlendes Feld zwingt jeden Leser zu einer Fallunterscheidung, die nichts
    bedeutet, und verdeckt genau den Fall, wegen dem dieser Wächter steht.
    """
    arbeitsgang.rechne(mappe, ausfuehrer=Werkbank().tabelle())

    messung = _letzter_lauf(mappe)["messungen"][kette.KNOTEN_RENDER]
    assert set(messung) == set(arbeitsgang.MESSFELDER)


# ------------------------------------------- 4 · die bisherigen Leser brechen nicht

def test_die_bisherigen_lauffelder_stehen_unveraendert_da(mappe):
    """Der Zusatz kommt **dazu**, er ersetzt nichts.

    ``oberflaeche/server.py`` und die beiden bestehenden Testsammlungen lesen diese
    Felder. Ein Umbau hätte sie still leergelaufen.
    """
    arbeitsgang.rechne(mappe, ausfuehrer=Werkbank().tabelle())

    lauf = _letzter_lauf(mappe)
    for feld in ("status", "gerechnet", "cache_treffer", "gescheitert", "dauer_s",
                 "error", "modell_stand", "bilder_vermerkt"):
        assert feld in lauf, f"{feld} wurde bisher gelesen und fehlt jetzt"
    assert lauf["bilder_vermerkt"] == 1


def test_das_bild_behaelt_urteil_und_herkunft(mappe):
    """Die Messung hängt **neben** der Herkunft, nicht an ihrer Stelle."""
    arbeitsgang.rechne(mappe, ausfuehrer=Werkbank().tabelle())

    bild = _von_der_platte(mappe)["bilder"][0]
    assert bild["geometrie_bestanden"] is True
    assert bild["geometrie_gemessen"] is True
    assert bild["herkunft"]["seed"] == 7
    assert bild["herkunft"]["urteil_von"] == kette.KNOTEN_QA
    assert "messung" in bild["herkunft"]


def test_ein_gescheiterter_knoten_steht_trotzdem_in_den_messungen(mappe):
    """Auch die Stufe **ohne Bild** wird gemessen und eingetragen.

    Sie hat womöglich trotzdem gemeldet, auf welchem Weg sie lief — und ein fehlender
    Eintrag wäre von einem Knoten, den es nie gab, nicht zu unterscheiden. Gerade der
    Fehlschlag ist der Fall, in dem später jemand nachsieht.
    """
    werk = Werkbank(render_faellt=True, rendermeldung={
        "geraeteweg": {"geraet": "cpu", "ladeweg": "ausgelagert", "entflechtung": None,
                       "bedarf": None, "gemeldet": True, "grund": ""}})

    ergebnis = arbeitsgang.rechne(mappe, ausfuehrer=werk.tabelle())

    assert ergebnis["vermerkt"] == 0, "ohne Bild kein Bildeintrag"
    lauf = _letzter_lauf(mappe)
    assert kette.KNOTEN_RENDER in lauf["messungen"], (
        "ein Knoten ohne Bild faellt sonst aus der Mappe, samt seiner Messung")
    assert lauf["messungen"][kette.KNOTEN_RENDER]["geraeteweg"]["geraet"] == "cpu"
