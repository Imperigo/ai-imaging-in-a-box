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
    weg, entflechtung, bedarf = render._lege_auf_geraet(
        pipe, "/gibt/es/nicht", _Torch, erwartet=(30 * 2**30, 1 * 2**30),
        erwartet_gemessen=True)

    assert weg == "cuda+auslagerung"
    assert entflechtung["noetig"] is True and entflechtung["nachher"] == 0
    # Und der Bericht sagt, GEGEN WELCHE ZAHL entschieden wurde — nicht bloss, dass
    # ausgelagert wurde. Ein negativer Spielraum ist genau das: es reichte nicht.
    assert bedarf["quelle"] == render.QUELLE_MESSUNG
    assert bedarf["zuschlag"] == render.MESSUNG_ZUSCHLAG
    assert bedarf["spielraum_byte"] < 0


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

    weg, entflechtung, bedarf = render._lege_auf_geraet(
        _Pipe(), "/gibt/es/nicht", _Torch, erwartet=(2 * 2**30, 1 * 2**30))

    assert weg == "cuda"
    assert entflechtung is None
    assert gerufen == [("to", "cuda")]
    assert bedarf["spielraum_byte"] > 0


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


# ───────────────────────────────────────────── Der Zuschlag haengt an der Herkunft
#
# Anlass: `auf-20260919-123`, HomeStation, 21.09.2026. Der Vorgabe-Backbone lief dort
# UEBERHAUPT NICHT mehr — frei 30 717 MiB, wirklich gebraucht 25 671 MiB, verlangt
# 32 128 MiB. Er passte mit ueber 5 GiB Luft und wurde trotzdem ausgelagert, und der
# Auslagerungsweg starb am Geraetekonflikt.
#
# Der Fehler war nicht die Zahl, sondern der Zuschlag darauf: `GERAETE_ZUSCHLAG` fuehrt
# von der GEWICHTSGROESSE zum Laufzeitbedarf — er bezahlt die Aktivierungen. `vram_gb`
# ist aber schon eine Spitze IM BETRIEB. Beides zu multiplizieren zaehlt dieselbe Sache
# zweimal.

#: Was auf der Werkstattmaschine frei war, als der Lauf starb (`auf-20260919-123`).
FREI_HOMESTATION = 30717 * 2**20

#: Was derselbe Lauf wirklich brauchte, gemessen im Viersekundenraster (`auf-20260909-92`).
SPITZE_GEMESSEN = 25671 * 2**20


def _torch_mit(frei):
    class _Torch:
        class cuda:
            @staticmethod
            def is_available():
                return True

            @staticmethod
            def mem_get_info():
                return (frei, 32 * 2**30)
    return _Torch


class _VollwegPipe:
    """Eine Pipeline, die **nur** den vollen Weg duldet — jeder andere fliegt auf."""

    def __init__(self):
        self.gerufen = []

    def to(self, wohin):
        self.gerufen.append(wohin)

    def enable_model_cpu_offload(self):
        raise AssertionError("hier darf nicht ausgelagert werden")

    def enable_sequential_cpu_offload(self):
        raise AssertionError("hier darf erst recht nicht schichtweise ausgelagert werden")

    @property
    def controlnet(self):
        raise AssertionError("auf dem vollen Weg wird nicht entflochten")


def test_der_vorgabe_backbone_passt_auf_die_werkstattkarte():
    """**Die Probe, um die es geht.** Nicht eine erfundene Lage, sondern die gemessene:
    der Vorgabe-Backbone, die Zahl aus der Registry, und der freie Speicher, bei dem der
    Lauf am 21.09.2026 starb.

    Sie ruft `_erwarteter_bedarf` und rechnet nicht selbst nach — *eine Probe, die die
    geprüfte Rechnung nachbaut, prüft ihre eigene Kopie.*
    """
    from aiimaging import backbone

    eintrag = backbone.hole(render.VORGABE_BACKBONE)
    erwartet = render._erwarteter_bedarf(eintrag)
    assert erwartet is not None, "ohne gemessene Zahl prüft diese Probe nichts"

    pipe = _VollwegPipe()
    weg, entflechtung, bedarf = render._lege_auf_geraet(
        pipe, "/gibt/es/nicht", _torch_mit(FREI_HOMESTATION), erwartet=erwartet,
        erwartet_gemessen=render._bedarf_ist_gemessen(eintrag))

    assert weg == "cuda", (
        f"Der Vorgabe-Backbone muss auf {FREI_HOMESTATION / 2**20:.0f} MiB freiem "
        f"Speicher voll auf die Karte. Gemessen gebraucht hat er "
        f"{SPITZE_GEMESSEN / 2**20:.0f} MiB.")
    assert entflechtung is None
    assert pipe.gerufen == ["cuda"]
    assert bedarf["verlangt_byte"] < FREI_HOMESTATION
    assert bedarf["spielraum_byte"] > 0


def test_der_alte_zuschlag_haette_genau_diesen_lauf_ausgelagert():
    """Die Gegenprobe zur vorigen — **ohne sie wäre jene wertlos.**

    Sie zeigt, dass der Unterschied wirklich am Zuschlag hängt und nicht daran, dass die
    Zahlen ohnehin bequem passen: Mit ``GERAETE_ZUSCHLAG`` statt ``MESSUNG_ZUSCHLAG``
    reicht derselbe freie Speicher für denselben Backbone **nicht**.
    """
    from aiimaging import backbone

    summe, _groesster = render._erwarteter_bedarf(backbone.hole(render.VORGABE_BACKBONE))

    assert summe * render.GERAETE_ZUSCHLAG > FREI_HOMESTATION, (
        "Mit dem alten Zuschlag wäre ausgelagert worden — das ist der Befund.")
    assert summe * render.MESSUNG_ZUSCHLAG <= FREI_HOMESTATION, (
        "Mit dem neuen Zuschlag bleibt er auf der Karte — das ist die Reparatur.")


def test_die_wirklich_gemessene_spitze_passt_mit_luft():
    """Und der Beleg, dass die Reparatur nicht bloss eine engere Wette ist: Was der Lauf
    **gemessen** brauchte, liegt deutlich unter dem, was frei war. Der volle Weg ist hier
    nicht knapp erlaubt, sondern richtig."""
    assert SPITZE_GEMESSEN < FREI_HOMESTATION
    assert FREI_HOMESTATION - SPITZE_GEMESSEN > 4 * 2**30


def test_die_plattengroesse_behaelt_den_grossen_zuschlag(tmp_path):
    """Der Fall, den die Reparatur **nicht** anfassen darf.

    Eine Datei auf der Platte ist keine Speichergrösse: ``z-image-turbo`` liegt mit einem
    fp32-Transformer da und wiegt in bfloat16 die Hälfte. Wer ohne Registryzahl
    entscheidet, weiss das nicht — und braucht den ganzen Aufschlag.
    """
    (tmp_path / "teil.bin").write_bytes(b"\0" * 1024)

    pipe = _VollwegPipe()
    weg, _entflechtung, bedarf = render._lege_auf_geraet(
        pipe, tmp_path, _torch_mit(10 * 2**20), erwartet=None)

    assert weg == "cuda"
    assert bedarf["quelle"] == render.QUELLE_PLATTE
    assert bedarf["zuschlag"] == render.GERAETE_ZUSCHLAG
    assert bedarf["summe_byte"] == 1024


def test_die_beiden_zuschlaege_sind_verschieden_und_der_gemessene_ist_kleiner():
    """Ein Wächter gegen die Zusammenlegung, die der Befund gerade widerlegt hat.

    Würden beide wieder derselbe Wert, wären alle Proben darüber grün — sie prüfen Wege,
    nicht Konstanten. *Ein Zweig ohne Fall ist kein bewachter Zweig.*
    """
    assert render.MESSUNG_ZUSCHLAG < render.GERAETE_ZUSCHLAG
    assert render.MESSUNG_ZUSCHLAG > 1.0, (
        "Ganz ohne Zuschlag wäre die Schwankung derselben Messung nicht gedeckt — "
        "22,89 / 23,4 / 25,1 GiB sind 9,7 Prozent.")


def test_ohne_jede_messbare_zahl_wird_nicht_ausgelagert(tmp_path):
    """UNBEKANNT ist kein Grund zum Auslagern. Der volle Weg scheitert wenigstens sofort
    und sichtbar; der Auslagerungsweg ist langsamer **und** hat den Gerätekonflikt."""
    pipe = _VollwegPipe()
    weg, _entflechtung, bedarf = render._lege_auf_geraet(
        pipe, tmp_path / "gibt-es-nicht", _torch_mit(1), erwartet=None)

    assert weg == "cuda"
    assert bedarf["quelle"] == render.QUELLE_KEINE
    assert bedarf["verlangt_byte"] is None, "eine Zahl, die es nicht gibt, steht nicht da"


def test_der_bedarf_landet_im_ergebnis(tmp_path):
    """Die Rechnung muss aus dem Ergebnis lesbar sein — sonst ist sie von aussen nicht von
    einer Eigenschaft der Maschine zu unterscheiden. Genau daran hat sich der Befund drei
    Wochen lang aufgehalten."""
    modell = _modell(tmp_path, geraet="cuda", ladeweg="basis+controlnet",
                     bedarf={"quelle": render.QUELLE_MESSUNG, "spielraum_byte": 5 * 2**30,
                             "grund": "Entschieden an gemessener Spitze"})

    ergebnis = render.rendere(_auftrag(tmp_path), modell=modell)

    assert ergebnis["geraeteweg"]["bedarf"]["spielraum_byte"] == 5 * 2**30


def test_ein_knapp_gewaehlter_vollweg_wird_gemeldet():
    """Die Gegenrichtung, die es bis zum 21.09.2026 gar nicht gab: Ein Lauf, der mit
    200 MiB Luft auf die Karte kam, ist nicht gesund — er hatte Glück, und beim nächsten
    Bild in grösserer Auflösung hat er es nicht mehr."""
    zeilen = abholer.befund_kurz({"kameras": [
        {"kamera": "sSE", "geraeteweg": {"geraet": "cuda", "gemeldet": True,
                                         "entflechtung": None,
                                         "bedarf": {"spielraum_byte": 200 * 2**20}}}]})

    assert [z for z in zeilen if "KNAPP" in z], zeilen


def test_ein_bequemer_vollweg_wird_nicht_gemeldet():
    """Die Gegenprobe. Eine Warnung, die bei jedem gesunden Lauf erscheint, wird nach dem
    dritten Mal nicht mehr gelesen."""
    zeilen = abholer.befund_kurz({"kameras": [
        {"kamera": "sSE", "geraeteweg": {"geraet": "cuda", "gemeldet": True,
                                         "entflechtung": None,
                                         "bedarf": {"spielraum_byte": 5 * 2**30}}}]})

    assert not [z for z in zeilen if "KNAPP" in z]


def test_ohne_bedarfsangabe_wird_nichts_behauptet():
    """Ältere Befunde führen kein `bedarf` — und ein fehlendes Feld ist **kein** knapper
    Lauf. *Die dritte Antwort, angewandt auf eine Warnung.*"""
    for bedarf in (None, {}, {"spielraum_byte": None}):
        zeilen = abholer.befund_kurz({"kameras": [
            {"kamera": "sSE", "geraeteweg": {"geraet": "cuda", "gemeldet": True,
                                             "entflechtung": None, "bedarf": bedarf}}]})

        assert not [z for z in zeilen if "KNAPP" in z], bedarf


def test_der_auslagerungsweg_nennt_die_zahl_gegen_die_entschieden_wurde():
    """Bis zum 21.09.2026 sagte der Kurzbefund, der freie Kartenspeicher habe entschieden.
    Er sagte nicht, **gegen welche Zahl** — und genau das war die fehlende Auskunft."""
    zeilen = abholer.befund_kurz({"kameras": [
        {"kamera": "sSE", "geraeteweg": {
            "geraet": "cuda+auslagerung", "gemeldet": True,
            "entflechtung": {"noetig": True, "nachher": 0},
            "bedarf": {"grund": "Entschieden an gemessene Spitze (Registry): "
                                "25702 MiB x 1.1 = 28272 MiB verlangt, 20000 MiB frei."}}}]})

    treffer = [z for z in zeilen if "28272 MiB verlangt" in z]
    assert treffer, zeilen


# ──────────────────────── Die Herkunft der Registry-Zahl — Messung oder Schaetzung
#
# BERICHTIGUNG AM TAG DES EINBAUS (21.09.2026). Der erste Wurf von `MESSUNG_ZUSCHLAG`
# hat ihn auf JEDES `vram_gb` der Registry angewandt. Dort stehen aber fuenf von sieben
# Eintraegen als Schaetzung aus der Parameterzahl — und die ganze Begruendung des kleinen
# Zuschlags («die Aktivierungen sind schon drin») traegt fuer eine Schaetzung nicht.
#
#     Ein Zuschlag, der mit einer Messung begruendet ist, darf nicht auf eine Schaetzung
#     angewandt werden — sonst ist die Begruendung eine Erzaehlung ueber die eigenen Daten.

def test_die_registry_trennt_gemessene_von_geschaetzten_zahlen():
    """**Beide Sorten muessen wirklich vorkommen**, sonst prueft alles darunter nichts.

    Gaebe es nur gemessene Eintraege, waere der Zweig fuer Schaetzungen ein Zweig ohne
    Fall; gaebe es nur geschaetzte, der andere. *Ein Zweig ohne Fall ist kein bewachter
    Zweig.*
    """
    from aiimaging import backbone

    gemessen = [n for n in backbone.BACKBONES if backbone.hole(n).vram_gemessen]
    geschaetzt = [n for n in backbone.BACKBONES if not backbone.hole(n).vram_gemessen]

    assert gemessen, "kein einziger gemessener Eintrag"
    assert geschaetzt, "kein einziger geschaetzter Eintrag"


def test_eine_geschaetzte_zahl_bekommt_den_grossen_zuschlag():
    """Der Fall, der vor der Berichtigung falsch lief."""
    pipe = _VollwegPipe()
    _weg, _e, bedarf = render._lege_auf_geraet(
        pipe, "/gibt/es/nicht", _torch_mit(100 * 2**30),
        erwartet=(8 * 2**30, 4 * 2**30), erwartet_gemessen=False)

    assert bedarf["quelle"] == render.QUELLE_SCHAETZUNG
    assert bedarf["zuschlag"] == render.GERAETE_ZUSCHLAG


def test_eine_unbekannte_herkunft_wird_wie_eine_schaetzung_behandelt():
    """**Die Richtung des Irrtums, und sie ist eine Entscheidung.**

    Wer die Angabe vergisst, bekommt den vorsichtigeren Weg. Umgekehrt voreingestellt
    bekaeme er den kuehnen genau dann, wenn er nicht hingesehen hat.
    """
    pipe = _VollwegPipe()
    _weg, _e, bedarf = render._lege_auf_geraet(
        pipe, "/gibt/es/nicht", _torch_mit(100 * 2**30),
        erwartet=(8 * 2**30, 4 * 2**30))          # erwartet_gemessen fehlt absichtlich

    assert bedarf["zuschlag"] == render.GERAETE_ZUSCHLAG


def test_ein_fremdes_objekt_ohne_das_feld_gilt_als_geschaetzt():
    """Eine Attrappe, ein aelterer Eintrag, ein fremder Lader — keines von ihnen fuehrt
    `vram_gemessen`. *Eine Zahl, von der niemand weiss, woher sie kommt, ist keine
    Messung.*"""
    from types import SimpleNamespace

    assert render._bedarf_ist_gemessen(SimpleNamespace(vram_gb=20.0)) is False


def test_nur_ein_echtes_ja_zaehlt_als_messung():
    """`1` ist in Python gleich `True`. Ein `vram_gemessen=1` in einem Eintrag saehe aus
    wie eine Messung und waere keine — derselbe Fall wie beim Urteil in der Projektmappe,
    wo genau das schon einmal durchgerutscht ist."""
    from types import SimpleNamespace

    assert render._bedarf_ist_gemessen(SimpleNamespace(vram_gemessen=True)) is True
    for falsch in (1, "ja", [1]):
        assert render._bedarf_ist_gemessen(SimpleNamespace(vram_gemessen=falsch)) is False


def test_der_vorgabe_backbone_traegt_eine_gemessene_zahl():
    """Sonst waere die Probe weiter oben — «er passt auf die Werkstattkarte» — gruen aus
    dem falschen Grund: Mit dem grossen Zuschlag passt er naemlich NICHT."""
    from aiimaging import backbone

    assert backbone.hole(render.VORGABE_BACKBONE).vram_gemessen is True
