"""Der gewählte Geräteweg wird protokolliert — der billigste Posten mit dem grössten Hebel.

**Der Anlass sind drei verlorene Stunden** (HomeStation, `auf-vis-20260825-15`, Posten 4):

  *«`lade_modell` setzt `modell.geraet` und `modell.ladeweg` — kein Aufrufer schreibt sie
  irgendwohin. Darum sah der Unterschied zwischen dem gelungenen Lauf vom 20.08. und dem
  Fehlschlag vom 25.08. wie ein Rueckfall aus, obwohl sich am Code nichts geaendert
  hatte. Eine Zeile Protokoll haette drei Stunden Untersuchung gespart.»*

Entschieden hatte in Wahrheit der **freie** Kartenspeicher: `_lege_auf_geraet` verlangt
29,25 GiB, am Abend waren 28,89 bis 29,07 frei. Zwei bis vier Zehntel Gigabyte.

Eine Zahl, die gemessen wird und nirgends landet, ist für jede spätere Untersuchung nicht
vorhanden — dieselbe Krankheit wie eine tote Kante, nur an der Ausgabe statt am Aufruf.
"""
from pathlib import Path
from types import SimpleNamespace

import pytest

from aiimaging import abholer, render


def _auftrag(tmp_path):
    tiefe = tmp_path / "t.png"
    tiefe.write_bytes(b"\x89PNG\r\n\x1a\n")
    return render.RenderAuftrag(depth_png=str(tiefe), prompt="a house",
                                ausgabe_png=str(tmp_path / "b.png"))


def _modell(tmp_path, **felder):
    """Eine Modellattrappe, die ein Bild schreibt — und die Angaben führt, die zählen."""
    def modell(parameter):
        Path(parameter["ausgabe_png"]).write_bytes(b"\x89PNG\r\n\x1a\n")
        return parameter["ausgabe_png"]

    for name, wert in felder.items():
        setattr(modell, name, wert)
    return modell


def test_der_geraeteweg_steht_im_ergebnis(tmp_path):
    """Der ganze Posten in einem Test: Was gemessen wurde, muss auch irgendwo landen."""
    erg = render.rendere(_auftrag(tmp_path),
                         modell=_modell(tmp_path, geraet="cuda+schichtauslagerung",
                                        ladeweg="basis+controlnet"))

    assert erg["status"] == "ok"
    assert erg["geraeteweg"]["geraet"] == "cuda+schichtauslagerung"
    assert erg["geraeteweg"]["ladeweg"] == "basis+controlnet"
    assert erg["geraeteweg"]["gemeldet"] is True


def test_ein_modell_ohne_angabe_meldet_unbekannt_und_nicht_cpu(tmp_path):
    """Die dritte Antwort, wieder. Ein Modell ohne Geräteangabe als «CPU» zu
    protokollieren wäre eine erfundene Messung — und sie sähe wie eine echte aus."""
    erg = render.rendere(_auftrag(tmp_path), modell=_modell(tmp_path))

    assert erg["geraeteweg"]["geraet"] is None
    assert erg["geraeteweg"]["gemeldet"] is False
    assert "UNBEKANNT" in erg["geraeteweg"]["grund"]


def test_auch_eine_ablehnung_traegt_das_feld(tmp_path):
    """Ein Ergebnissatz mit wechselnden Schlüsseln zwingt jeden Auswerter zu verzweigen —
    dieselbe Begründung wie bei den Parametern in `_ergebnis`."""
    erg = render.rendere(render.RenderAuftrag(depth_png="", prompt=""))

    assert erg["status"] == render.STATUS_ABGELEHNT
    assert erg["geraeteweg"]["gemeldet"] is False
    assert "nichts geladen" in erg["geraeteweg"]["grund"]


def test_ein_fehlschlag_sagt_auf_welchem_weg_er_passierte(tmp_path):
    """**Der Fall, der den Anlass gab.** Ein Fehlschlag ohne Geräteangabe ist von einem
    Rückfall im Code nicht zu unterscheiden."""
    def kaputt(parameter):
        raise RuntimeError("CUDA out of memory")

    kaputt.geraet = "cuda+auslagerung"
    erg = render.rendere(_auftrag(tmp_path), modell=kaputt)

    assert erg["status"] == render.STATUS_FEHLER
    assert erg["geraeteweg"]["geraet"] == "cuda+auslagerung"


# ======================================================================================
# Die Naht — bis in den Befund, sonst wäre es wieder nur eine gesetzte Eigenschaft
# ======================================================================================

def _lauf(tmp_path, geraet):
    zaehler = {}
    bild = tmp_path / "b.png"

    def multipass(glb, aus, **kw):
        tiefe = Path(aus) / "tiefe_norm.png"
        tiefe.write_bytes(b"\x89PNG\r\n\x1a\n")
        return {"depth_png": str(tiefe), "kamera": {"weg": "vorgegeben"}}

    def rendere(auftrag, **kw):
        bild.write_bytes(b"\x89PNG\r\n\x1a\n")
        return {"status": "ok", "bild_png": str(bild), "hinweise": (),
                "geraeteweg": {"geraet": geraet, "ladeweg": None, "gemeldet": True,
                               "grund": ""}}

    verarbeite = abholer.verarbeiter(
        out_wurzel=tmp_path, nullprobe=False,
        _multipass=multipass, _rendere=rendere,
        _qa=lambda *a, **k: {"score": 0.9, "bestanden": True},
        _soll=lambda *a, **k: ([[0.0]], 1, 1))

    ergebnis = verarbeite({"modell": tmp_path / "m.glb", "job_id": "vis-1-aaaaaa",
                           "verzeichnis": tmp_path,
                           "szene": {"kameras": [{"kuerzel": "sSE", "richtung": "sSE"}],
                                     "aufloesung": 64, "hoehe": 64, "samples": 1,
                                     "prompt": "a house"}})
    zaehler["ergebnis"] = ergebnis
    return ergebnis


def test_der_geraeteweg_erreicht_das_kameraurteil(tmp_path):
    ergebnis = _lauf(tmp_path, "cuda+schichtauslagerung")

    assert ergebnis["kameras"][0]["geraeteweg"]["geraet"] == "cuda+schichtauslagerung"


def test_der_kurzbefund_nennt_den_langsamen_weg():
    """Er erklärt Laufzeit, nicht Qualität — und genau diese Verwechslung hat drei
    Stunden gekostet."""
    zeilen = abholer.befund_kurz({"kameras": [
        {"kamera": "sSE", "geraeteweg": {"geraet": "cuda+auslagerung", "gemeldet": True}}]})

    treffer = [z for z in zeilen if "nicht ganz auf der Karte" in z]
    assert len(treffer) == 1
    assert "cuda+auslagerung" in treffer[0]


def test_der_schnelle_weg_erzeugt_keine_zeile():
    """Die Gegenprobe. Eine Zeile bei jedem gesunden Lauf wird nach dem dritten Mal nicht
    mehr gelesen — dann fehlt sie genau dann, wenn sie zählt."""
    zeilen = abholer.befund_kurz({"kameras": [
        {"kamera": "sSE", "geraeteweg": {"geraet": "cuda", "gemeldet": True}}]})

    assert not [z for z in zeilen if "nicht ganz auf der Karte" in z]


def test_ein_ungemeldeter_weg_erzeugt_ebenfalls_keine_zeile():
    """UNBEKANNT ist kein Befund über die Karte. Wer daraus eine Warnung machte, meldete
    jede Attrappe als langsamen Lauf."""
    zeilen = abholer.befund_kurz({"kameras": [
        {"kamera": "sSE", "geraeteweg": {"geraet": None, "gemeldet": False}}]})

    assert not [z for z in zeilen if "nicht ganz auf der Karte" in z]


@pytest.mark.parametrize("weg", ["cuda", "cuda+auslagerung", "cuda+schichtauslagerung",
                                 "cpu"])
def test_alle_vier_wege_aus_lege_auf_geraet_sind_zulaessige_werte(weg):
    """Die Liste im Kurzbefund darf nicht an einer eigenen Aufzählung hängen — sie hängt
    an dem, was `_lege_auf_geraet` wirklich zurückgibt."""
    quelle = Path(render.__file__).read_text(encoding="utf-8")
    kopf = quelle.split("def _lege_auf_geraet", 1)[1].split("\ndef ", 1)[0]

    assert f'return "{weg}"' in kopf
