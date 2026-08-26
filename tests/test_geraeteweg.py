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
from conftest import MINI_PNG


def _auftrag(tmp_path):
    tiefe = tmp_path / "t.png"
    tiefe.write_bytes(MINI_PNG)
    return render.RenderAuftrag(depth_png=str(tiefe), prompt="a house",
                                ausgabe_png=str(tmp_path / "b.png"))


def _modell(tmp_path, **felder):
    """Eine Modellattrappe, die ein Bild schreibt — und die Angaben führt, die zählen."""
    def modell(parameter):
        Path(parameter["ausgabe_png"]).write_bytes(MINI_PNG)
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
        tiefe.write_bytes(MINI_PNG)
        return {"depth_png": str(tiefe), "kamera": {"weg": "vorgegeben"}}

    def rendere(auftrag, **kw):
        bild.write_bytes(MINI_PNG)
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


# ======================================================================================
# Die ControlNet-Verflechtung — Posten 3 derselben Liste
# ======================================================================================
#
# Gemessen (HomeStation, auf-vis-20260825-14): ZImageControlNetPipeline teilt 67
# Parameter zwischen ControlNet und Transformer, darunter den ERSTEN. `accelerate` prueft
# beim Auslagern nur den ersten — also gilt der Transformer als erledigt, und 454 von 521
# seiner Parameter bleiben auf der CPU. Der erste Diffusionsschritt stirbt dann an einem
# Geraetekonflikt.
#
# Geprueft wird hier OHNE torch: Die Frage ist, welche Untermodule Parameterobjekte
# gemeinsam haben, und das ist Identitaet und keine Algebra. Eine Reparatur, die sich nur
# auf einer 5090 pruefen laesst, wird nie geprueft.

class _Param:
    """Ein Parameter ist hier nur ein Ding mit Identität. Mehr fragt der Code nicht ab."""


class _Modul:
    """Gerade so viel `torch.nn.Module`, wie `_entflechte_controlnet` anfasst."""

    def __init__(self, eigene=0, **kinder):
        self._eigene = [_Param() for _ in range(eigene)]
        for name, kind in kinder.items():
            setattr(self, name, kind)
        self._namen = list(kinder)

    def named_children(self):
        return [(name, getattr(self, name)) for name in self._namen]

    def parameters(self):
        for p in self._eigene:
            yield p
        for _, kind in self.named_children():
            yield from kind.parameters()


class _Pipeline:
    def __init__(self, controlnet=None, transformer=None):
        if controlnet is not None:
            self.controlnet = controlnet
        if transformer is not None:
            self.transformer = transformer


def test_geteilte_untermodule_bekommen_eigene_kopien():
    """**Der Fall, der die Kette getoetet hat.** Nach der Entflechtung darf kein einziger
    Parameter mehr beiden gehören — sonst zieht `accelerate` weiterhin falsche Schlüsse."""
    geteilt = _Modul(eigene=3)
    controlnet = _Modul(eigen=_Modul(eigene=2), gemeinsam=geteilt)
    transformer = _Modul(kopf=_Modul(eigene=4), gemeinsam=geteilt)

    bericht = render._entflechte_controlnet(_Pipeline(controlnet, transformer))

    assert bericht["noetig"] is True
    assert bericht["vorher"] == 3
    assert bericht["nachher"] == 0
    assert bericht["kopiert"] == ("gemeinsam",)
    assert render._geteilte_parameter(controlnet, transformer) == set()


def test_nur_die_betroffenen_kinder_werden_kopiert():
    """Das ganze ControlNet zu kopieren hätte dieselbe Wirkung zum vielfachen Preis — und
    der Preis ist hier genau das knappe Gut."""
    geteilt = _Modul(eigene=1)
    unberuehrt = _Modul(eigene=5)
    controlnet = _Modul(eigen=unberuehrt, gemeinsam=geteilt)
    transformer = _Modul(gemeinsam=geteilt)

    render._entflechte_controlnet(_Pipeline(controlnet, transformer))

    assert controlnet.eigen is unberuehrt, "ein unbeteiligtes Kind bleibt dasselbe Objekt"
    assert controlnet.gemeinsam is not geteilt


def test_ohne_verflechtung_wird_nichts_kopiert():
    """Die Gegenprobe. Eine Reparatur, die immer greift, kostet bei jedem gesunden Lauf
    1,35 GiB — auf einer Karte, auf der zwei Zehntel Gigabyte entschieden haben."""
    controlnet = _Modul(eigene=2)
    transformer = _Modul(eigene=2)

    bericht = render._entflechte_controlnet(_Pipeline(controlnet, transformer))

    assert bericht["noetig"] is False
    assert bericht["kopiert"] == ()
    assert bericht["vorher"] == 0


def test_eine_pipeline_ohne_controlnet_ist_kein_befund():
    bericht = render._entflechte_controlnet(_Pipeline(transformer=_Modul(eigene=1)))

    assert bericht["noetig"] is False
    assert "kein ControlNet" in bericht["grund"]


def test_eine_gescheiterte_entflechtung_haelt_den_lauf_nicht_auf():
    """Ohne die Reparatur stirbt der Lauf auf dem Auslagerungsweg ohnehin. Ein Fehlschlag
    HIER darf ihn nicht zusätzlich um die Meldung bringen, an der die Ursache erkennbar
    ist — darum wird gemeldet und nicht geworfen."""
    class _Unkopierbar(_Modul):
        def __deepcopy__(self, memo):
            raise RuntimeError("dieses Modul laesst sich nicht kopieren")

    geteilt = _Unkopierbar(eigene=1)
    controlnet = _Modul(gemeinsam=geteilt)
    transformer = _Modul(gemeinsam=geteilt)

    bericht = render._entflechte_controlnet(_Pipeline(controlnet, transformer))

    assert bericht["noetig"] is True, "die Verflechtung war da und ist es geblieben"
    assert bericht["nachher"] is None, "UNBEKANNT — nicht 'null geteilte Parameter'"
    assert "gescheitert" in bericht["grund"]
    assert "RuntimeError" in bericht["grund"], "die fremde Meldung gehoert dazu"


def test_auf_dem_auslagerungsweg_wird_sehr_wohl_entflochten():
    """Die Gegenprobe zum Test ganz unten: Eine Entflechtung, die **nie** greift, wäre
    ebenso wertlos wie eine, die immer greift."""
    geteilt = _Modul(eigene=1)

    class _Pipe:
        def __init__(self):
            self.controlnet = _Modul(gemeinsam=geteilt)
            self.transformer = _Modul(gemeinsam=geteilt)

        def to(self, wohin):
            raise AssertionError("hier wird ausgelagert und nicht umgezogen")

        def enable_model_cpu_offload(self):
            pass

    class _Torch:
        class cuda:
            @staticmethod
            def is_available():
                return True

            @staticmethod
            def mem_get_info():
                # Genug fuer die groesste Komponente, zu wenig fuer die Summe.
                return (2 * 2**30, 32 * 2**30)

    pipe = _Pipe()
    weg, entflechtung = render._lege_auf_geraet(
        pipe, "/gibt/es/nicht", _Torch, erwartet=(30 * 2**30, 1 * 2**30))

    assert weg == "cuda+auslagerung"
    assert entflechtung["noetig"] is True and entflechtung["nachher"] == 0


def test_der_bericht_nennt_die_gemessene_ursache():
    """Die Zahl 67 und die 454 von 521 sind das, was diesen Eingriff rechtfertigt. Ohne
    sie stünde hier eine Reparatur ohne Anlass — und niemand könnte sie später prüfen."""
    quelle = Path(render.__file__).read_text(encoding="utf-8")
    kopf = quelle.split("def _entflechte_controlnet", 1)[1].split("\ndef ", 1)[0]

    assert "auf-vis-20260825-14" in kopf
    assert "67" in kopf and "454" in kopf
    assert "kein Rückfall" in kopf or "kein Rueckfall" in kopf


def test_auf_dem_vollen_weg_wird_gar_nicht_entflochten():
    """**Die wichtigste Prüfung dieser Gruppe.** Die Kopien kosten 1,35 GiB. Auf einer
    Karte, auf der 29,25 GiB verlangt und 28,89 frei waren, wäre das genau der Zuschlag,
    der einen gesunden Lauf erst in den Auslagerungsweg drängt — die Reparatur richtete
    dann den Schaden an, gegen den sie gebaut ist."""
    gerufen = []

    class _Torch:
        class cuda:
            @staticmethod
            def is_available():
                return True

            @staticmethod
            def mem_get_info():
                return (100 * 2**30, 128 * 2**30)      # reichlich frei

    class _Pipe:
        def to(self, wohin):
            gerufen.append(("to", wohin))

        def enable_model_cpu_offload(self):
            gerufen.append(("auslagern", None))

        @property
        def controlnet(self):
            raise AssertionError("auf dem vollen Weg darf niemand danach fragen")

    weg, entflechtung = render._lege_auf_geraet(
        _Pipe(), "/gibt/es/nicht", _Torch, erwartet=(2 * 2**30, 1 * 2**30))

    assert weg == "cuda"
    assert entflechtung is None
    assert gerufen == [("to", "cuda")]


def test_der_kurzbefund_meldet_eine_nicht_durchgegriffene_entflechtung():
    """Der Satz gehört VOR den Lauf, der daran stirbt. Bis zum 26.08.2026 hiess dieser
    Fall «Expected all tensors to be on the same device» und kostete drei Stunden."""
    zeilen = abholer.befund_kurz({"kameras": [
        {"kamera": "sSE", "geraeteweg": {"geraet": "cuda+auslagerung", "gemeldet": True,
                                         "entflechtung": {"noetig": True, "nachher": 12}}}]})

    treffer = [z for z in zeilen if "NICHT durchgegriffen" in z]
    assert len(treffer) == 1 and "sSE" in treffer[0]


def test_eine_gelungene_entflechtung_erzeugt_keine_zeile():
    """Die Gegenprobe: Sie ist der Normalfall auf dem Auslagerungsweg, und eine Warnung
    für den Normalfall ist keine."""
    zeilen = abholer.befund_kurz({"kameras": [
        {"kamera": "sSE", "geraeteweg": {"geraet": "cuda+auslagerung", "gemeldet": True,
                                         "entflechtung": {"noetig": True, "nachher": 0}}}]})

    assert not [z for z in zeilen if "NICHT durchgegriffen" in z]


def test_ein_lauf_ohne_auslagerung_erzeugt_ebenfalls_keine_zeile():
    """`entflechtung: None` heisst «war nicht nötig» — daraus eine Warnung zu machen
    meldete jeden gesunden Lauf."""
    zeilen = abholer.befund_kurz({"kameras": [
        {"kamera": "sSE", "geraeteweg": {"geraet": "cuda", "gemeldet": True,
                                         "entflechtung": None}}]})

    assert not [z for z in zeilen if "NICHT durchgegriffen" in z]
