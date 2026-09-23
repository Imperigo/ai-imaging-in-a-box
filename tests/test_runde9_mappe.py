"""Runde 9 — zwei Befunde der HomeStation zur Mappe (``auf-20260922-139``, 23.09.2026).

**M1 · Ein Modell im Heimatordner, die Mappe ausserhalb.** ``projekt.pfad_fuer_die_mappe``
schrieb den Modellpfad relativ zur Mappe und verliess sich darauf, dass ein relativer Pfad
keinen Benutzernamen enthält. Liegt die Mappe auf dem Datenlaufwerk und das Modell im
Heimatordner, führt der relative Weg durch ``/home/<name>/`` — die Säuberung nach Regel 3
machte daraus ``<nutzer>``, und ``arbeitsgang.rechne`` brach ab: «An diesem Pfad liegt
keine Datei mehr», obwohl sie da war.

**Warum die Proben es nie sahen:** Jede lief unter ``tmp_path``, und dort liegt kein
Heimatordner im Weg. Die Wächter hier **lenken das Heimatverzeichnis um** (``HOME`` auf
einen Ordner unter ``tmp_path``, der wie ein Benutzername heisst) und fahren den
Produktweg: ``arbeitsgang.lege_an`` und ``arbeitsgang.rechne``, mit Attrappen statt
Blender und Gewichten, die Mappe danach **von der Platte** gelesen.

**M2 · Wie ein Bild entstand, je Bild.** Die HomeStation meldete ``modus_bestellt`` und
``modus_gerechnet`` «weder am Bildeintrag noch in dessen herkunft». Nachgeprüft: Sie
stehen dort — eine Ebene tiefer, unter ``bilder[].herkunft.messung`` (seit dem
22.09.2026). Der Wächter hier fährt den Weg der HomeStation nach (``lege_an`` mit Prompt
und Startwert, dann ``rechne``) und liest die geschriebene Datei, damit die Stelle
festgehalten ist und nicht wieder gesucht werden muss.
"""
from __future__ import annotations

import json
import struct
from pathlib import Path

import pytest

from aiimaging import arbeitsgang, projekt
from aiimaging.kette import ART_GEOMETRIE, ART_MULTIPASS, ART_QA, ART_RENDER

#: Ein Name, der aussieht wie ein Benutzername. Er darf in keiner Mappe stehen.
NAME = "vreni-beispiel"


# ------------------------------------------------------------------- die Attrappen

class Werkbank:
    """Ersatz-Ausführer für die vier Knotenarten — schreibt echte Dateien.

    ``glb_gesehen`` hält fest, welchen glb-Pfad der Geometrieknoten bekam: Er muss auf
    die Datei zeigen, die es gibt, nicht auf einen gesäuberten Namen.
    """

    def __init__(self, *, rendermeldung: dict | None = None) -> None:
        self.rendermeldung = dict(rendermeldung or {})
        self.glb_gesehen: list[str] = []

    def tabelle(self) -> dict:
        return {ART_GEOMETRIE: self.geometrie, ART_MULTIPASS: self.multipass,
                ART_RENDER: self.render, ART_QA: self.qa}

    def geometrie(self, *, knoten, eingaben, out_dir):
        self.glb_gesehen.append(str(knoten.params.get("glb_path")))
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
        bild = Path(out_dir) / "bild.png"
        bild.write_text("bild", encoding="utf-8")
        return {"status": "ok", "bild_png": str(bild), "seed": knoten.params["seed"],
                **self.rendermeldung}

    def qa(self, *, knoten, eingaben, out_dir):
        return {"status": "ok", "bestanden": True, "score": 0.91,
                "schwelle": knoten.params["schwelle"]}


def _schreibe_glb(pfad: Path) -> Path:
    """Ein gültiges glb — Weg «durchgereicht», also ohne jeden Subprozess."""
    js = json.dumps({"asset": {"version": "2.0", "generator": "Testfixture"}}).encode()
    js += b" " * (-len(js) % 4)
    block = struct.pack("<II", len(js), 0x4E4F534A) + js
    pfad.parent.mkdir(parents=True, exist_ok=True)
    pfad.write_bytes(struct.pack("<4sII", b"glTF", 2, 12 + len(block)) + block)
    return pfad


@pytest.fixture
def heim(tmp_path, monkeypatch):
    """Ein umgelenktes Heimatverzeichnis unter ``/…/home/<name>`` — wie auf der
    HomeStation, damit die Säuberung nach Regel 3 wirklich greift."""
    ordner = tmp_path / "home" / NAME
    ordner.mkdir(parents=True)
    monkeypatch.setenv("HOME", str(ordner))
    monkeypatch.setenv("USERPROFILE", str(ordner))
    assert Path.home() == ordner, "Die Umlenkung greift nicht — der Wächter wäre leer."
    return ordner


def _lege_an_und_rechne(wurzel: Path, modell: Path, werk: Werkbank) -> dict:
    """Der Weg der HomeStation in V4: anlegen mit Prompt und Startwert, dann rechnen."""
    arbeitsgang.lege_an(wurzel, modell, name="Probe",
                        einstellungen={"prompt": "Abendlicht", "seed": 7, "up_axis": "Y"})
    return arbeitsgang.rechne(wurzel, ausfuehrer=werk.tabelle())


def _text_der_mappe(wurzel: Path) -> str:
    return (wurzel / projekt.PROJEKTDATEI).read_text(encoding="utf-8")


# ------------------------------------------------ M1 · Modell im Heim, Mappe ausserhalb

def test_modell_im_heimatordner_mappe_ausserhalb_rechnet_durch(tmp_path, heim):
    """Der gemeldete Fall, über den Produktweg: Er muss rechnen, nicht abbrechen."""
    modell = _schreibe_glb(heim / "modelle" / "haus.glb")
    wurzel = tmp_path / "datenlaufwerk" / "projekt"
    werk = Werkbank()

    ergebnis = _lege_an_und_rechne(wurzel, modell, werk)

    assert ergebnis["modell_stand"] == projekt.MODELL_UNVERAENDERT
    assert ergebnis["vermerkt"] == 1
    # DER GEOMETRIEKNOTEN BEKAM DIE ECHTE DATEI — die durchgereichte glb liegt im Heim,
    # also geht auch `import.glb` durch denselben Leser.
    assert werk.glb_gesehen and Path(werk.glb_gesehen[0]).resolve() == modell.resolve()
    assert projekt.oeffne(wurzel)["modell_stand"] == projekt.MODELL_UNVERAENDERT


def test_die_mappe_nennt_dabei_keinen_namen(tmp_path, heim):
    """Regel 3 bleibt erfüllt — und zwar ohne Säuberung, nicht durch sie."""
    modell = _schreibe_glb(heim / "modelle" / "haus.glb")
    wurzel = tmp_path / "datenlaufwerk" / "projekt"
    _lege_an_und_rechne(wurzel, modell, Werkbank())

    text = _text_der_mappe(wurzel)
    assert NAME not in text
    assert "<nutzer>" not in text
    gespeichert = json.loads(text)
    assert gespeichert["modell"]["pfad"] == "~/modelle/haus.glb"
    assert gespeichert["regel3_ersetzt"] == 0


def test_heimatordner_ausserhalb_von_home_verraet_den_namen_nicht(tmp_path, monkeypatch):
    """Die stille Schwester des Befunds: Heisst das Heimatverzeichnis nicht ``/home/…``,
    greift die Säuberung gar nicht — der relative Weg trüge den Namen dann **offen** in
    die Mappe. Heimrelativ trägt er ihn nicht."""
    ordner = tmp_path / "konten" / "anna-muster"
    ordner.mkdir(parents=True)
    monkeypatch.setenv("HOME", str(ordner))
    modell = _schreibe_glb(ordner / "haus.glb")
    wurzel = tmp_path / "datenlaufwerk" / "projekt"

    ergebnis = _lege_an_und_rechne(wurzel, modell, Werkbank())

    assert ergebnis["vermerkt"] == 1
    assert "anna-muster" not in _text_der_mappe(wurzel)


def test_gegenprobe_mappe_und_modell_im_heim_bleiben_relativ(heim):
    """Beide im Heimatordner: relativ zur Mappe, wie bisher — umziehbar, ohne Namen."""
    modell = _schreibe_glb(heim / "modelle" / "haus.glb")
    wurzel = heim / "mappen" / "projekt"

    ergebnis = _lege_an_und_rechne(wurzel, modell, Werkbank())

    assert ergebnis["vermerkt"] == 1
    gespeichert = json.loads(_text_der_mappe(wurzel))
    assert gespeichert["modell"]["pfad"] == str(Path("..") / ".." / "modelle" / "haus.glb")
    assert NAME not in _text_der_mappe(wurzel)


def test_gegenprobe_mappe_und_modell_ausserhalb_bleiben_relativ(tmp_path, heim):
    """Beide ausserhalb des Heimatordners: relativ, der Weg berührt ihn nicht."""
    modell = _schreibe_glb(tmp_path / "datenlaufwerk" / "modelle" / "haus.glb")
    wurzel = tmp_path / "datenlaufwerk" / "projekt"

    ergebnis = _lege_an_und_rechne(wurzel, modell, Werkbank())

    assert ergebnis["vermerkt"] == 1
    gespeichert = json.loads(_text_der_mappe(wurzel))
    assert gespeichert["modell"]["pfad"] == str(Path("..") / "modelle" / "haus.glb")


def test_was_in_der_mappe_liegt_bleibt_relativ_auch_wenn_das_heim_darin_liegt(
        tmp_path, monkeypatch):
    """Die Bilder liegen in der Mappe, und die Fläche kennt sie nur am relativen Namen.
    Liegt das Heimatverzeichnis ausnahmsweise **in** der Mappe, darf aus einem Bild kein
    ``~/…`` werden — es wäre für die Fläche kein Bild mehr."""
    wurzel = tmp_path / "mappe"
    monkeypatch.setenv("HOME", str(wurzel / "laeufe"))
    modell = _schreibe_glb(tmp_path / "quelle" / "haus.glb")

    ergebnis = _lege_an_und_rechne(wurzel, modell, Werkbank())

    assert ergebnis["vermerkt"] == 1
    namen = [b["bild"] for b in json.loads(_text_der_mappe(wurzel))["bilder"]]
    assert namen and all(n.startswith("laeufe") for n in namen), namen


def test_ein_dateiname_mit_tilde_bleibt_in_der_mappe(tmp_path, heim):
    """Nur ``~`` und ``~/…`` meinen das Heimatverzeichnis. ``~entwurf.png`` ist ein
    Dateiname in der Mappe — ``expanduser`` läse ihn als Heim eines Benutzers."""
    assert projekt.loese_pfad("~entwurf.png", tmp_path) == tmp_path / "~entwurf.png"
    assert projekt.loese_pfad("~/modelle/haus.glb", tmp_path) == heim / "modelle" / "haus.glb"


# ------------------------------------------------- M2 · wie ein Bild entstand, je Bild

MODUSFELDER = ("modus_bestellt", "modus_gerechnet", "modus_abweichung")


def test_der_modus_steht_an_jedem_bild_unter_herkunft_messung(tmp_path):
    """Der Weg der HomeStation (V4), die Datei danach als Text gelesen: Am Bild steht,
    was bestellt und was gerechnet wurde — dieselben Werte wie im Lauf."""
    modell = _schreibe_glb(tmp_path / "quelle" / "haus.glb")
    wurzel = tmp_path / "projekt"
    werk = Werkbank(rendermeldung={"modus_bestellt": "image_edit",
                                   "modus_gerechnet": "txt2img",
                                   "modus_abweichung": True})

    _lege_an_und_rechne(wurzel, modell, werk)

    gespeichert = json.loads(_text_der_mappe(wurzel))
    lauf = gespeichert["laeufe"][-1]
    assert gespeichert["bilder"]
    for bild in gespeichert["bilder"]:
        herkunft = bild["herkunft"]
        messung = herkunft["messung"]
        assert messung["modus_bestellt"] == "image_edit"
        assert messung["modus_gerechnet"] == "txt2img"
        assert messung["modus_abweichung"] is True
        im_lauf = lauf["messungen"][herkunft["knoten"]]
        assert {f: messung[f] for f in MODUSFELDER} == {f: im_lauf[f] for f in MODUSFELDER}


def test_ein_ungemessener_modus_steht_am_bild_als_null_nicht_als_false(tmp_path):
    """Die dritte Antwort: Meldet die Bildstufe nichts, stehen die Felder **da** und
    sind ``null`` — nicht weggelassen, nicht ``false``."""
    modell = _schreibe_glb(tmp_path / "quelle" / "haus.glb")
    wurzel = tmp_path / "projekt"

    _lege_an_und_rechne(wurzel, modell, Werkbank())

    for bild in json.loads(_text_der_mappe(wurzel))["bilder"]:
        messung = bild["herkunft"]["messung"]
        for feld in MODUSFELDER:
            assert feld in messung, feld
            assert messung[feld] is None, (feld, messung[feld])
