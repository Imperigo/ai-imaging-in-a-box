"""Die Bildmodell-Stufe ohne Bildmodell — was hier belegt wird, und was nicht.

Auf diesem Rechner gibt es keine GPU, kein ``torch``, keine Gewichte. Diese Datei prüft
deshalb genau das, was auch ohne all das eine Aussage hat: die **Verdrahtung**.

* Der Lauf selbst — Prüfung, Backbone-Auflösung, Aufruf der Naht, Aufbau des
  Ergebnisses — wird mit einer :class:`Attrappe` vollständig durchgespielt. Dieselbe
  Test-Naht wie ``_starte`` in ``seams.py`` und ``einbetter`` in ``stil_qa.py``.
* Regel 1 wird als **ausführbarer** Pfad geprüft: FLUX.1-dev wird abgelehnt. Jede
  solche Ablehnungsprobe hat hier eine Gegenprobe, die zeigt, dass das Modell wirklich
  in der Registry steht — sonst prüfte der Test nur, dass ein Tippfehler abgelehnt wird,
  und wäre vakuös.
* Die Prozessgrenze zum GPU-Stack: ``torch`` und ``diffusers`` dürfen nach
  ``import aiimaging.render`` nicht in ``sys.modules`` liegen.

Was diese Datei ausdrücklich **nicht** belegt: dass ein echter Render funktioniert, dass
die ControlNet-Verdrahtung in ``_pipeline_adapter`` trägt, dass ein Bild der Geometrie
folgt, oder dass die VRAM-Schätzungen stimmen. Das kann nur die HomeStation.

Alle Bilddateien sind synthetische Platzhalter (Regel 3).
"""
from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

import pytest

from conftest import SRC

from aiimaging import auftrag as auftrag_modul
from aiimaging import backbone, render
from aiimaging.render import (
    MAX_SCHRITTE,
    MAX_SEED,
    MODUS_IMAGE_EDIT,
    MODUS_TXT2IMG,
    STATUS_ABGELEHNT,
    STATUS_FEHLER,
    STATUS_OK,
    RenderAuftrag,
    RenderError,
    pruefe_auftrag,
    rendere,
)

#: Ein paar Bytes mit PNG-Signatur. Der Kern liest nie einen Bildinhalt — er fragt nur,
#: ob die Datei da ist. Ein echtes Bild zu erzeugen bräuchte eine Bildbibliothek und
#: würde nichts zusätzlich belegen.
PNG_PLATZHALTER = b"\x89PNG\r\n\x1a\n"

#: Unterscheidet „keine Antwort vorgegeben" von der Antwort ``None``. Ohne dieses
#: Merkzeichen liesse sich der Fall „das Modell gibt None zurück" gar nicht stellen.
_UNGESETZT = object()


class Attrappe:
    """Ein Modell aus drei Zeilen — der Beleg, dass die Naht schmal genug ist.

    Sie merkt sich, womit sie gerufen wurde (``aufrufe``), und schreibt eine Datei an
    den vereinbarten Ort. ``schreibt=False`` erzeugt den Fall „Modell meldet einen Pfad,
    schreibt aber nichts" — der Fehlgriff, gegen den ``rendere`` nachsieht.
    """

    def __init__(self, ziel=None, *, schreibt: bool = True, wirft: Exception | None = None,
                 antwort=_UNGESETZT):
        self.ziel = str(ziel) if ziel is not None else None
        self.schreibt = schreibt
        self.wirft = wirft
        self.antwort = antwort
        self.aufrufe: list[dict] = []

    def __call__(self, parameter: dict):
        self.aufrufe.append(parameter)
        if self.wirft is not None:
            raise self.wirft
        if self.antwort is not _UNGESETZT:
            return self.antwort
        ziel = self.ziel or parameter["ausgabe_png"]
        if self.schreibt:
            Path(ziel).write_bytes(PNG_PLATZHALTER)
        return ziel


@pytest.fixture
def tiefe(tmp_path) -> str:
    """Eine synthetische Tiefenkarte — Existenz genügt, Inhalt spielt keine Rolle."""
    pfad = tmp_path / "tiefe_norm.png"
    pfad.write_bytes(PNG_PLATZHALTER)
    return str(pfad)


@pytest.fixture
def ziel(tmp_path) -> str:
    return str(tmp_path / "render.png")


def auftrag(tiefe: str, **kw) -> RenderAuftrag:
    """Ein gültiger Auftrag; ``kw`` überschreibt einzelne Felder."""
    felder = {"depth_png": tiefe, "prompt": "Wohnhaus, Beton und Holz, Morgenlicht"}
    felder.update(kw)
    return RenderAuftrag(**felder)


# --------------------------------------------------------------------------------------
# 1 · Der vollständige Durchlauf mit Attrappe
# --------------------------------------------------------------------------------------

def test_vollstaendiger_durchlauf_liefert_ok_und_ein_bild(tiefe, ziel):
    """Ohne GPU, ohne torch, ohne Gewichte: der Lauf geht durch und legt eine Datei ab."""
    ergebnis = rendere(auftrag(tiefe, ausgabe_png=ziel), modell=Attrappe())

    assert ergebnis["status"] == STATUS_OK
    assert ergebnis["bild_png"] == ziel
    assert Path(ziel).is_file()
    assert ergebnis["error"] is None
    assert ergebnis["maengel"] == ()


def test_ergebnis_traegt_die_vertragsfelder(tiefe, ziel):
    """Der Ergebnissatz passt zum Auftrags-/Ergebnisvertrag aus ``auftrag.py``."""
    ergebnis = rendere(auftrag(tiefe, ausgabe_png=ziel), modell=Attrappe())

    for feld in ("status", "bild_png", "seed", "backbone", "parameter", "dauer_s",
                 "error"):
        assert feld in ergebnis, f"Pflichtfeld {feld} fehlt im Ergebnis"
    assert isinstance(ergebnis["dauer_s"], float)
    assert ergebnis["dauer_s"] >= 0.0


def test_statuswoerter_passen_zum_homestation_vertrag():
    """Ein Render-Ergebnis muss ohne Übersetzung in ein HomeStation-Ergebnis passen.

    Gegenprobe gegen die Versuchung, hier eigene Statuswörter zu erfinden: ``auftrag.py``
    kennt eine feste Menge, und ``baue_ergebnis`` weist alles andere zurück.
    """
    for status in render.STATUSSE:
        satz = auftrag_modul.baue_ergebnis(auftrag_id="auf-20260818-01", status=status)
        assert satz["status"] == status


def test_attrappe_bekommt_alle_parameter(tiefe, ziel):
    """Die Naht übergibt die Wiederholvorschrift vollständig — nicht nur den Prompt."""
    attrappe = Attrappe()
    rendere(auftrag(tiefe, ausgabe_png=ziel, seed=4711, schritte=12,
                    controlnet_staerke=0.55, negativ_prompt="Menschen"),
            modell=attrappe)

    (gesehen,) = attrappe.aufrufe
    assert gesehen["seed"] == 4711
    assert gesehen["schritte"] == 12
    assert gesehen["controlnet_staerke"] == 0.55
    assert gesehen["negativ_prompt"] == "Menschen"
    assert gesehen["depth_png"] == tiefe
    assert gesehen["ausgabe_png"] == ziel
    assert gesehen["backbone"] == backbone.VORGABE_BACKBONE
    assert gesehen["modell_id"] == backbone.hole(backbone.VORGABE_BACKBONE).modell_id


def test_parameter_enthalten_alles_zur_wiederholung(tiefe, ziel):
    """Fehlte ein Parameter im Protokoll, liesse sich ein Bildunterschied nicht zuordnen."""
    ergebnis = rendere(auftrag(tiefe, ausgabe_png=ziel), modell=Attrappe())

    erwartet = {"backbone", "modell_id", "konditionierung", "modus", "depth_png",
                "beauty_png", "ausgabe_png", "prompt", "negativ_prompt", "seed",
                "schritte", "controlnet_staerke", "denoise", "modell_wurzel"}
    assert erwartet <= set(ergebnis["parameter"])


def test_modell_wird_genau_einmal_gerufen(tiefe, ziel):
    attrappe = Attrappe()
    rendere(auftrag(tiefe, ausgabe_png=ziel), modell=attrappe)
    assert len(attrappe.aufrufe) == 1


def test_wortliste_als_antwort_wird_akzeptiert(tiefe, ziel):
    """Die Naht nimmt auch ein Wörterbuch mit ``bild_png`` — dokumentierter Vertrag."""
    Path(ziel).write_bytes(PNG_PLATZHALTER)
    attrappe = Attrappe(antwort={"bild_png": ziel, "extra": 1})

    ergebnis = rendere(auftrag(tiefe, ausgabe_png=None), modell=attrappe)

    assert ergebnis["status"] == STATUS_OK
    assert ergebnis["bild_png"] == ziel


# --------------------------------------------------------------------------------------
# 2 · Reproduzierbarkeit — Seed und Parameter im Ergebnis
# --------------------------------------------------------------------------------------

def test_gleicher_seed_ergibt_gleiche_parameter(tiefe, ziel):
    """Zwei Läufe mit demselben Auftrag protokollieren dieselbe Wiederholvorschrift."""
    a = auftrag(tiefe, ausgabe_png=ziel, seed=123)

    erst = rendere(a, modell=Attrappe())
    zweit = rendere(a, modell=Attrappe())

    assert erst["parameter"] == zweit["parameter"]
    assert erst["seed"] == zweit["seed"] == 123


def test_anderer_seed_ergibt_andere_parameter(tiefe, ziel):
    """Gegenprobe: Der Vergleich oben ist nicht deshalb gleich, weil er nichts vergleicht."""
    erst = rendere(auftrag(tiefe, ausgabe_png=ziel, seed=1), modell=Attrappe())
    zweit = rendere(auftrag(tiefe, ausgabe_png=ziel, seed=2), modell=Attrappe())

    assert erst["parameter"] != zweit["parameter"]
    assert (erst["seed"], zweit["seed"]) == (1, 2)


def test_seed_steht_auch_bei_ablehnung_im_ergebnis(tiefe):
    """Auch eine Ablehnung trägt die Parameter — sonst steht im Protokoll nur „abgelehnt"."""
    ergebnis = rendere(auftrag(tiefe, seed=99, schritte=0), modell=Attrappe())

    assert ergebnis["status"] == STATUS_ABGELEHNT
    assert ergebnis["seed"] == 99
    assert ergebnis["parameter"]["schritte"] == 0


# --------------------------------------------------------------------------------------
# 3 · Regel 1 im ausführbaren Pfad — mit Gegenproben gegen vakuöse Tests
# --------------------------------------------------------------------------------------

@pytest.mark.parametrize("name", ["flux1-dev", "flux2-dev"])
def test_gegenprobe_nicht_kommerzielle_modelle_stehen_in_der_registry(name):
    """Ohne diese Probe prüften die Ablehnungstests nur, dass ein Tippfehler auffällt.

    Die Registry führt beide FLUX-dev-Einträge bewusst mit (siehe ``backbone.py``) —
    genau damit die Ablehnung an der Lizenz hängt und nicht an einem unbekannten Namen.
    """
    eintrag = backbone.hole(name)
    assert eintrag.kommerziell_nutzbar is False
    assert backbone.pruefe_lizenz(name)["zulaessig"] is False


def test_flux_dev_wird_abgelehnt(tiefe, ziel):
    """Regel 1: Non-Commercial-Gewichte werden nicht gerendert."""
    ergebnis = rendere(auftrag(tiefe, ausgabe_png=ziel, backbone="flux1-dev"),
                       modell=Attrappe())

    assert ergebnis["status"] == STATUS_ABGELEHNT
    assert ergebnis["bild_png"] is None
    assert "Regel 1" in ergebnis["error"]
    assert any("kommerzielle Nutzung" in m for m in ergebnis["maengel"])


def test_flux_dev_wird_abgelehnt_obwohl_die_naht_passte(tiefe):
    """Die Ablehnung ist eine Lizenzentscheidung, keine technische.

    FLUX.1-dev trägt in der Registry ``depth_controlnet`` — technisch würde die Naht
    tragen. Abgelehnt wird es allein wegen Regel 1.
    """
    assert backbone.hole("flux1-dev").konditionierung == render.KOND_DEPTH_CONTROLNET

    maengel = pruefe_auftrag(auftrag(tiefe, backbone="flux1-dev"))
    assert len(maengel) == 1
    assert "Regel 1" in maengel[0]


def test_ablehnung_laedt_kein_modell(tiefe, ziel):
    """Regel 1 entscheidet, **bevor** 20 GB Gewichte bewegt werden."""
    def lader(*_args):
        raise AssertionError("Bei einer Ablehnung darf nichts geladen werden")

    ergebnis = rendere(auftrag(tiefe, ausgabe_png=ziel, backbone="flux1-dev"),
                       _lader=lader)

    assert ergebnis["status"] == STATUS_ABGELEHNT


def test_ablehnung_schreibt_kein_bild(tiefe, ziel):
    """Kein Bild, keine Datei — und die Ablehnung ist an ``bild_png=None`` erkennbar."""
    rendere(auftrag(tiefe, ausgabe_png=ziel, backbone="flux1-dev"), modell=Attrappe())
    assert not Path(ziel).exists()


# --------------------------------------------------------------------------------------
# 4 · Die Konditionierungsart — integriertes_edit hat keine Depth-Naht
# --------------------------------------------------------------------------------------

def test_gegenprobe_flux2_klein_ist_erlaubt_aber_ohne_depth_naht():
    """Die Falle des Registry-Eintrags: permissiv lizenziert, aber ohne ControlNet.

    Ohne diese Gegenprobe könnte die Ablehnung unten auch an der Lizenz hängen — dann
    prüfte der Test etwas anderes, als sein Name behauptet.
    """
    eintrag = backbone.hole("flux2-klein-4b")
    assert eintrag.kommerziell_nutzbar is True
    assert backbone.pruefe_lizenz("flux2-klein-4b")["zulaessig"] is True
    assert eintrag.konditionierung == backbone.KOND_INTEGRIERTES_EDIT


def test_integriertes_edit_wird_abgelehnt(tiefe, ziel):
    """Kein So-tun-als-ob: Fehlt die Naht, wird nicht gerendert."""
    ergebnis = rendere(auftrag(tiefe, ausgabe_png=ziel, backbone="flux2-klein-4b"),
                       modell=Attrappe())

    assert ergebnis["status"] == STATUS_ABGELEHNT
    assert ergebnis["bild_png"] is None
    assert any("Adapterschicht" in m for m in ergebnis["maengel"])


def test_alle_registrierten_depth_backbones_werden_angenommen(tiefe):
    """Die Kehrseite: Was die Registry als tauglich führt, muss auch durchkommen.

    Sonst wäre die Ablehnung oben nur eine besonders strenge Fassung von „nichts geht".
    """
    tauglich = backbone.waehle(kommerziell=True,
                               konditionierung=render.KOND_DEPTH_CONTROLNET)
    assert tauglich, "Vorbedingung: die Registry führt taugliche Backbones"

    for eintrag in tauglich:
        assert pruefe_auftrag(auftrag(tiefe, backbone=eintrag.name)) == []


# --------------------------------------------------------------------------------------
# 5 · Unsinnige Parameter und fehlende Eingaben — laut, nie zurechtgebogen
# --------------------------------------------------------------------------------------

def test_fehlende_tiefenkarte_wird_gemeldet(tmp_path, ziel):
    fehlt = str(tmp_path / "gibt-es-nicht.png")
    ergebnis = rendere(RenderAuftrag(depth_png=fehlt, prompt="Haus", ausgabe_png=ziel),
                       modell=Attrappe())

    assert ergebnis["status"] == STATUS_ABGELEHNT
    assert any("liegt nicht vor" in m for m in ergebnis["maengel"])


def test_tiefenkarte_ist_pflicht_auch_als_leerer_text(ziel):
    maengel = pruefe_auftrag(RenderAuftrag(depth_png="  ", prompt="Haus"))
    assert any("depth_png" in m for m in maengel)


def test_fehlendes_ausgangsbild_wird_gemeldet(tiefe, tmp_path):
    maengel = pruefe_auftrag(auftrag(tiefe, beauty_png=str(tmp_path / "weg.png")))
    assert any("beauty_png" in m for m in maengel)


@pytest.mark.parametrize("schritte", [0, -5])
def test_schrittzahl_muss_positiv_sein(tiefe, schritte):
    maengel = pruefe_auftrag(auftrag(tiefe, schritte=schritte))
    assert any("schritte muss positiv sein" in m for m in maengel)


def test_schrittzahl_hat_eine_obergrenze(tiefe):
    """Schutz vor dem Tippfehler, der die einzige GPU des Projekts stundenlang bindet."""
    maengel = pruefe_auftrag(auftrag(tiefe, schritte=MAX_SCHRITTE + 1))
    assert any(str(MAX_SCHRITTE) in m for m in maengel)
    assert pruefe_auftrag(auftrag(tiefe, schritte=MAX_SCHRITTE)) == []


@pytest.mark.parametrize("feld", ["controlnet_staerke", "denoise"])
@pytest.mark.parametrize("wert", [-0.1, 1.5, float("nan"), float("inf")])
def test_anteile_ausserhalb_von_null_bis_eins(tiefe, feld, wert):
    """Nicht geklemmt, sondern gemeldet: Ein geklemmter Wert stünde falsch im Protokoll."""
    maengel = pruefe_auftrag(auftrag(tiefe, **{feld: wert}))
    assert any(feld in m for m in maengel)


@pytest.mark.parametrize("feld", ["controlnet_staerke", "denoise"])
def test_wahrheitswert_ist_keine_zahl(tiefe, feld):
    """``True`` wäre 1.0 und liefe stillschweigend durch — es ist aber immer ein Irrtum."""
    maengel = pruefe_auftrag(auftrag(tiefe, **{feld: True}))
    assert any("keine Zahl" in m for m in maengel)


@pytest.mark.parametrize("seed", [-1, MAX_SEED + 1, 2.5, True])
def test_unbrauchbare_seeds(tiefe, seed):
    assert any("seed" in m for m in pruefe_auftrag(auftrag(tiefe, seed=seed)))


def test_leerer_prompt_wird_gemeldet(tiefe):
    maengel = pruefe_auftrag(auftrag(tiefe, prompt="   "))
    assert any("Prompt ist leer" in m for m in maengel)


def test_unbekannter_backbone_nennt_die_bekannten(tiefe, ziel):
    ergebnis = rendere(auftrag(tiefe, ausgabe_png=ziel, backbone="qwen-image-edit-2512"),
                       modell=Attrappe())

    assert ergebnis["status"] == STATUS_ABGELEHNT
    assert backbone.VORGABE_BACKBONE in ergebnis["error"]
    # Auch ohne Registry-Eintrag bleibt das Protokoll lesbar.
    assert ergebnis["backbone"] == "qwen-image-edit-2512"
    assert ergebnis["parameter"]["prompt"]


def test_fehlendes_ausgabeverzeichnis_wird_vorher_gemeldet(tiefe, tmp_path):
    """Vor dem Lauf feststellbar — nach dem Lauf ein verlorener Lauf."""
    ziel = str(tmp_path / "gibt-es-nicht" / "render.png")
    maengel = pruefe_auftrag(auftrag(tiefe, ausgabe_png=ziel))
    assert any("Ausgabeverzeichnis" in m for m in maengel)


def test_alle_maengel_auf_einmal(tiefe):
    """Wer einen Auftrag von Hand baut, soll nicht fünfmal hintereinander scheitern."""
    maengel = pruefe_auftrag(RenderAuftrag(depth_png="/weg.png", prompt="",
                                           schritte=0, denoise=2.0))
    assert len(maengel) >= 4


def test_gueltiger_auftrag_hat_keine_maengel(tiefe, ziel):
    assert pruefe_auftrag(auftrag(tiefe, ausgabe_png=ziel)) == []


def test_kein_auftrag_wirft(tiefe):
    """Ohne Auftrag gibt es keine Parameter — und damit kein protokollierbares Ergebnis."""
    with pytest.raises(RenderError, match="RenderAuftrag"):
        rendere({"depth_png": tiefe, "prompt": "Haus"}, modell=Attrappe())

    assert pruefe_auftrag("kein Auftrag") == ["Kein RenderAuftrag, sondern str."]


# --------------------------------------------------------------------------------------
# 6 · Modus, Hinweise, Lizenzangabe im Ergebnis
# --------------------------------------------------------------------------------------

def test_modus_txt2img_ohne_ausgangsbild(tiefe, ziel):
    ergebnis = rendere(auftrag(tiefe, ausgabe_png=ziel), modell=Attrappe())
    assert ergebnis["parameter"]["modus"] == MODUS_TXT2IMG


def test_modus_image_edit_mit_ausgangsbild(tmp_path, tiefe, ziel):
    beauty = tmp_path / "beauty.png"
    beauty.write_bytes(PNG_PLATZHALTER)

    ergebnis = rendere(auftrag(tiefe, ausgabe_png=ziel, beauty_png=str(beauty)),
                       modell=Attrappe())

    assert ergebnis["status"] == STATUS_OK
    assert ergebnis["parameter"]["modus"] == MODUS_IMAGE_EDIT
    assert ergebnis["parameter"]["beauty_png"] == str(beauty)


def test_denoise_ohne_ausgangsbild_wird_benannt_statt_verworfen(tiefe, ziel):
    """Wirkungslos ist erlaubt — stillschweigend wirkungslos nicht."""
    ergebnis = rendere(auftrag(tiefe, ausgabe_png=ziel, denoise=0.7), modell=Attrappe())

    assert ergebnis["status"] == STATUS_OK
    assert any("denoise" in h for h in ergebnis["hinweise"])


def test_kein_denoise_hinweis_im_image_edit(tmp_path, tiefe, ziel):
    """Gegenprobe: Mit Ausgangsbild wirkt denoise und wird nicht kommentiert."""
    beauty = tmp_path / "beauty.png"
    beauty.write_bytes(PNG_PLATZHALTER)

    ergebnis = rendere(auftrag(tiefe, ausgabe_png=ziel, beauty_png=str(beauty),
                               denoise=0.7), modell=Attrappe())

    assert not any("denoise" in h for h in ergebnis["hinweise"])


def test_lizenzauflagen_reisen_im_ergebnis_mit(tiefe, ziel):
    """SDXL ist erlaubt, aber nicht bedingungslos — die Auflage gehört ins Protokoll."""
    ergebnis = rendere(auftrag(tiefe, ausgabe_png=ziel, backbone="sdxl-juggernaut"),
                       modell=Attrappe())

    assert ergebnis["status"] == STATUS_OK
    assert ergebnis["lizenz"]["zulaessig"] is True
    assert ergebnis["lizenz"]["auflagen"]
    assert any("OpenRAIL" in h for h in ergebnis["hinweise"])


def test_fehlender_ausgabeort_wird_als_hinweis_vermerkt(tiefe, tmp_path):
    """Ohne ``ausgabe_png`` entfällt der Schutz gegen ein Bild von gestern — das wird gesagt."""
    frei = tmp_path / "frei.png"
    ergebnis = rendere(auftrag(tiefe), modell=Attrappe(ziel=frei))

    assert ergebnis["status"] == STATUS_OK
    assert any("liegengebliebenes Bild" in h for h in ergebnis["hinweise"])


# --------------------------------------------------------------------------------------
# 7 · Wenn das Modell scheitert — die Lehre aus Sitzung 05
# --------------------------------------------------------------------------------------

def test_altes_bild_wird_vor_dem_lauf_entfernt(tiefe, ziel):
    """Die Existenz einer Datei ist kein Beleg für ihren Inhalt (vgl. ``seams.py``).

    Läge das Bild des Vorlaufs noch da, meldete sich ein gescheiterter Lauf an ihm
    gesund — genau der Fehler, den das Projekt beim Multipass schon einmal bezahlt hat.
    """
    Path(ziel).write_bytes(b"Bild von gestern")

    ergebnis = rendere(auftrag(tiefe, ausgabe_png=ziel), modell=Attrappe(schreibt=False))

    assert ergebnis["status"] == STATUS_FEHLER
    assert not Path(ziel).exists()
    assert "keine Datei" in ergebnis["error"]


def test_modell_das_wirft_wird_zum_fehlerergebnis(tiefe, ziel):
    """Ein Stapelabbruch kostet die ganze Serie; ein Fehlerergebnis kostet einen Auftrag."""
    ergebnis = rendere(auftrag(tiefe, ausgabe_png=ziel),
                       modell=Attrappe(wirft=RuntimeError("CUDA out of memory")))

    assert ergebnis["status"] == STATUS_FEHLER
    assert ergebnis["bild_png"] is None
    assert "CUDA out of memory" in ergebnis["error"]
    assert ergebnis["parameter"]["seed"] == 0        # Protokoll bleibt vollständig


@pytest.mark.parametrize("antwort", [None, 42, "", {"kein_bild": 1}])
def test_modell_ohne_pfad_wird_zum_fehlerergebnis(tiefe, ziel, antwort):
    """Der Vertrag der Naht ist ein Pfad. Alles andere ist ein Fehlschlag, kein Erfolg."""
    ergebnis = rendere(auftrag(tiefe, ausgabe_png=ziel), modell=Attrappe(antwort=antwort))

    assert ergebnis["status"] == STATUS_FEHLER
    assert "Bildpfad" in ergebnis["error"]


def test_scheiternder_lader_wird_zum_fehlerergebnis(tiefe, ziel):
    def lader(_name, _wurzel):
        raise RenderError("torch/diffusers nicht verfügbar")

    ergebnis = rendere(auftrag(tiefe, ausgabe_png=ziel), _lader=lader)

    assert ergebnis["status"] == STATUS_FEHLER
    assert "torch/diffusers" in ergebnis["error"]


# --------------------------------------------------------------------------------------
# 8 · Die Naht selbst — wer wird wann gerufen
# --------------------------------------------------------------------------------------

def test_lader_bekommt_backbone_und_wurzel(tiefe, ziel):
    gesehen = {}

    def lader(name, wurzel):
        gesehen["name"] = name
        gesehen["wurzel"] = wurzel
        return Attrappe()

    rendere(auftrag(tiefe, ausgabe_png=ziel, modell_wurzel="/ai/anderswo"), _lader=lader)

    assert gesehen == {"name": backbone.VORGABE_BACKBONE, "wurzel": "/ai/anderswo"}


def test_uebergebenes_modell_schaltet_den_lader_aus(tiefe, ziel):
    """Mit fertigem Modell wird nichts geladen — sonst wäre kein Testlauf ohne Gewichte möglich."""
    def lader(*_args):
        raise AssertionError("Es wurde ein Modell übergeben")

    ergebnis = rendere(auftrag(tiefe, ausgabe_png=ziel), modell=Attrappe(), _lader=lader)
    assert ergebnis["status"] == STATUS_OK


def test_standard_modellwurzel_folgt_der_umgebungsvariable(monkeypatch):
    monkeypatch.setenv(render.UMGEBUNG_MODELLE, "/woanders/modelle")
    assert render.standard_modell_wurzel("qwen-image-2512") == Path(
        "/woanders/modelle/qwen-image-2512")

    monkeypatch.delenv(render.UMGEBUNG_MODELLE, raising=False)
    assert render.standard_modell_wurzel("qwen-image-2512") == Path(
        f"{render.VORGABE_MODELLWURZEL}/qwen-image-2512")


# --------------------------------------------------------------------------------------
# 9 · lade_modell — die Prüfungen vor dem ersten Import
# --------------------------------------------------------------------------------------

def test_lade_modell_lehnt_nicht_kommerzielle_gewichte_ab(tmp_path):
    """Regel 1 zuerst: Selbst wer die 24 GB schon heruntergeladen hat, lädt sie nicht."""
    with pytest.raises(RenderError, match="Regel 1"):
        render.lade_modell("flux1-dev", tmp_path)


def test_lade_modell_lehnt_integriertes_edit_ab(tmp_path):
    with pytest.raises(RenderError, match="Adapterschicht"):
        render.lade_modell("flux2-klein-4b", tmp_path)


def test_lade_modell_meldet_fehlende_gewichte(tmp_path):
    """Die billige Frage zuerst: Liegen die Dateien überhaupt da?"""
    with pytest.raises(RenderError) as fehler:
        render.lade_modell(backbone.VORGABE_BACKBONE, tmp_path / "leer")

    assert "unvollständig" in str(fehler.value)
    assert "model_index.json" in str(fehler.value)


def test_lade_modell_meldet_unbekannten_backbone(tmp_path):
    """``BackboneError`` wird zu ``RenderError`` — der Aufrufer kennt nur eine Klasse."""
    with pytest.raises(RenderError, match="Unbekannter Backbone"):
        render.lade_modell("gibt-es-nicht", tmp_path)


def test_lade_modell_scheitert_erst_am_fehlenden_torch(tmp_path):
    """Sind Lizenz, Naht und Gewichte in Ordnung, bleibt genau ein Hindernis: der GPU-Stack.

    Hier gibt es keinen. Der Test belegt damit die **Reihenfolge** der Prüfungen — und
    zugleich, dass ohne ``torch`` sauber und erklärend abgebrochen wird, statt mit einem
    ``ImportError`` aus der Tiefe.
    """
    wurzel = tmp_path / "qwen"
    wurzel.mkdir()
    for eintrag in backbone.hole(backbone.VORGABE_BACKBONE).dateien:
        (wurzel / eintrag).mkdir()

    if "torch" in sys.modules:                      # pragma: no cover
        pytest.skip("torch ist installiert — dieser Test prüft den Fall ohne GPU-Stack")

    with pytest.raises(RenderError, match="torch/diffusers"):
        render.lade_modell(backbone.VORGABE_BACKBONE, wurzel)


# --------------------------------------------------------------------------------------
# 10 · Die Grenze zum GPU-Stack
# --------------------------------------------------------------------------------------

def _importe(quelle: str, nur_modulebene: bool) -> set[str]:
    """Top-level-Modulnamen der Importe einer Quelldatei.

    ``nur_modulebene=True`` sieht nur die Importe ganz oben; sonst auch die in Funktionen.
    Über ``ast`` und nicht über Textsuche — derselbe Grund wie in
    ``test_prozessgrenze.py``: Der Modul-Docstring von ``render.py`` **spricht** über
    ``import torch``, und eine Textsuche wäre dadurch immer rot.
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


def test_torch_und_diffusers_stehen_nicht_auf_modulebene():
    quelle = Path(render.__file__).read_text(encoding="utf-8")
    assert not {"torch", "diffusers"} & _importe(quelle, nur_modulebene=True)


def test_gegenprobe_torch_und_diffusers_werden_sehr_wohl_importiert():
    """Sonst wäre der Test oben erfüllt, weil das Modul das Modell gar nie lädt."""
    quelle = Path(render.__file__).read_text(encoding="utf-8")
    assert {"torch", "diffusers"} <= _importe(quelle, nur_modulebene=False)


def test_import_des_moduls_zieht_keinen_gpu_stack_nach():
    """``import aiimaging.render`` muss auf einem Rechner ohne GPU-Stack durchlaufen."""
    import aiimaging.render  # noqa: F401

    geladen = sorted(m for m in ("torch", "diffusers") if m in sys.modules)
    assert not geladen, f"{geladen} liegt nach dem Import in sys.modules"


def test_frischer_interpreter_bleibt_frei_vom_gpu_stack():
    """Gegenprobe in einem sauberen Prozess — unabhängig davon, was pytest sonst lud.

    Der Test ist auf diesem Rechner schwach (es gibt gar kein ``torch``); er wird stark,
    sobald jemand ihn auf der HomeStation laufen lässt, wo beides installiert ist. Genau
    dort soll die Grenze halten.
    """
    programm = (
        "import sys\n"
        "import aiimaging.render\n"
        "print(','.join(m for m in ('torch', 'diffusers') if m in sys.modules))\n"
    )
    ergebnis = subprocess.run(
        [sys.executable, "-c", programm],
        capture_output=True, text=True, timeout=120,
        env={"PATH": "/usr/bin:/bin", "PYTHONPATH": str(SRC), "PYTHONDONTWRITEBYTECODE": "1"},
    )
    assert ergebnis.returncode == 0, ergebnis.stderr
    assert ergebnis.stdout.strip() == "", f"nachgeladen: {ergebnis.stdout.strip()}"


def test_kein_comfyui_im_modul():
    """ComfyUI ist GPL-3.0 und als Kern ausgeschlossen (Regel 1) — auch nicht als Import."""
    quelle = Path(render.__file__).read_text(encoding="utf-8")
    assert "comfy" not in {m.lower() for m in _importe(quelle, nur_modulebene=False)}
