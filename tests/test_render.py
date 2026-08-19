"""Die Bildmodell-Stufe ohne Bildmodell — was hier belegt wird, und was nicht.

Diese Datei läuft ohne GPU, ohne ``torch`` und ohne Gewichte — und sie prüft deshalb
genau das, was auch ohne all das eine Aussage hat: die **Verdrahtung**. Sie muss dabei
dasselbe sagen, wo der GPU-Stack installiert ist (HomeStation) wie dort, wo er fehlt
(Entwicklungscontainer); kein Test hier darf sein Urteil aus der Umgebung beziehen.

* Der Lauf selbst — Prüfung, Backbone-Auflösung, Aufruf der Naht, Aufbau des
  Ergebnisses — wird mit einer :class:`Attrappe` vollständig durchgespielt. Dieselbe
  Test-Naht wie ``_starte`` in ``seams.py`` und ``einbetter`` in ``stil_qa.py``.
* Regel 1 wird als **ausführbarer** Pfad geprüft: FLUX.1-dev wird abgelehnt. Jede
  solche Ablehnungsprobe hat hier eine Gegenprobe, die zeigt, dass das Modell wirklich
  in der Registry steht — sonst prüfte der Test nur, dass ein Tippfehler abgelehnt wird,
  und wäre vakuös.
* Die Prozessgrenze zum GPU-Stack: ``torch`` und ``diffusers`` dürfen nach
  ``import aiimaging.render`` nicht in ``sys.modules`` liegen — gemessen in einem
  frischen Interpreter (``nachgeladene_module`` in ``conftest.py``), weil das
  ``sys.modules`` des Testlaufs die Vorgeschichte des Laufs zeigt und nicht die Folgen
  dieses einen Imports.

Was diese Datei ausdrücklich **nicht** belegt: dass ein echter Render funktioniert, dass
die ControlNet-Verdrahtung in ``_pipeline_adapter`` trägt, dass ein Bild der Geometrie
folgt, oder dass die VRAM-Schätzungen stimmen. Das kann nur die HomeStation.

Alle Bilddateien sind synthetische Platzhalter (Regel 3).
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

from conftest import nachgeladene_module

from aiimaging import auftrag as auftrag_modul
from aiimaging import backbone, render
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
    ist_controlnet_naht,
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


def test_eine_unbekannte_konditionierungsart_wird_abgelehnt(tmp_path):
    """**Berichtigt am 18.08.2026 durch den ersten echten Render (`auf-20260818-09`).**

    Bis dahin wies diese Prüfung alles ab, was nicht ``depth_controlnet`` war — mit der
    Begründung, für ``integriertes_edit`` fehle eine Adapterschicht. Der Lauf hat das
    widerlegt: Der Adapter trägt es, indem er die Tiefenkarte als ``image`` übergibt.

    Was er **nicht** kann, ist ein Regler dafür — und das meldet er je Lauf als Hinweis,
    statt es in einer Pauschalablehnung zu verstecken. Abgewiesen wird darum nur noch
    eine Art, die die Registry gar nicht kennt.
    """
    a = auftrag(tmp_path, backbone="flux2-klein-4b")
    assert "Konditionierungsart" not in " ".join(pruefe_auftrag(a)), (
        "integriertes_edit ist keine Ablehnung mehr"
    )



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


def test_lade_modell_traegt_integriertes_edit(tmp_path, monkeypatch):
    """Die Gegenprobe auf der Ladeseite: kein Abbruch mehr an der Konditionierungsart.

    Gescheitert wird jetzt erst an den Gewichten — also an etwas, das wirklich fehlt.
    """
    monkeypatch.setenv("AIIMAGING_MODELLE", str(tmp_path))
    with pytest.raises(RenderError) as fehler:
        render.lade_modell("flux2-klein-4b")
    assert "Konditionierung" not in str(fehler.value)
    assert "Gewichte" in str(fehler.value)



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


def test_lade_modell_scheitert_erst_am_fehlenden_torch(tmp_path, ohne_gpu_stack):
    """Sind Lizenz, Naht und Gewichte in Ordnung, bleibt genau ein Hindernis: der GPU-Stack.

    Der Test belegt damit die **Reihenfolge** der Prüfungen — und zugleich, dass ohne
    ``torch`` sauber und erklärend abgebrochen wird, statt mit einem ``ImportError`` aus
    der Tiefe.

    Das Fehlen des Stacks wird **hergestellt** (``ohne_gpu_stack`` in ``conftest.py``) und
    nicht vorausgesetzt. Früher stand hier ein ``skip``, falls ``torch`` in
    ``sys.modules`` lag: Damit prüfte der Test dort, wo der Stack installiert ist, gar
    nichts mehr — und wo er fehlt, war er ohne Zutun wahr. Der Riegel macht die Aussage in
    beiden Umgebungen zu einer Aussage über ``lade_modell``.
    """
    wurzel = tmp_path / "qwen"
    wurzel.mkdir()
    for eintrag in backbone.hole(backbone.VORGABE_BACKBONE).dateien:
        (wurzel / eintrag).mkdir()

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
    """``import aiimaging.render`` muss auf einem Rechner ohne GPU-Stack durchlaufen.

    Gemessen wird in einem **frischen Interpreter** (:func:`conftest.nachgeladene_module`),
    nicht am ``sys.modules`` dieses Testlaufs. Der Grund ist ein Messfehler, der lange
    unsichtbar war: Wo der GPU-Stack installiert ist, hat ihn irgendein früherer Test
    längst geladen — die Prüfung schlug dort fehl, obwohl an ``render.py`` nichts falsch
    war; und wo er gar nicht installiert ist, konnte sie nie fehlschlagen. Ein Test, der
    nur in einer Umgebung gilt, misst die Umgebung und nicht den Code.

    Im eigenen Prozess bringt genau dieser eine Import mit, was danach in ``sys.modules``
    steht. Damit hält der Test auch dort, wo die Zusage etwas wert ist: auf der
    HomeStation, wo ``torch`` und ``diffusers`` greifbar wären.
    """
    geladen = nachgeladene_module("aiimaging.render", ("torch", "diffusers"))
    assert not geladen, f"{geladen} liegt nach dem Import in sys.modules"


def test_gegenprobe_die_sonde_sieht_ein_wirklich_geladenes_modul():
    """Eine Sonde, die nie etwas meldet, bewacht nichts — dieselbe Sorge wie beim Scanner.

    ``render.py`` importiert ``pathlib`` auf Modulebene; in einem nackten Interpreter
    liegt es nicht. Meldet die Sonde es nach dem Import, misst sie tatsächlich die Folgen
    des Imports — und ihr Schweigen zu ``torch``/``diffusers`` oben ist eine Aussage und
    kein Nichts.
    """
    assert nachgeladene_module("aiimaging.render", ("pathlib",)) == ["pathlib"]
    assert nachgeladene_module("sys", ("pathlib",)) == []


def test_kein_comfyui_im_modul():
    """ComfyUI ist GPL-3.0 und als Kern ausgeschlossen (Regel 1) — auch nicht als Import."""
    quelle = Path(render.__file__).read_text(encoding="utf-8")
    assert "comfy" not in {m.lower() for m in _importe(quelle, nur_modulebene=False)}


# ==========================================================================================
# Die Führung (guidance_scale) — der Regler, den niemand gesetzt hat
#
# Befund vom 18.08.2026 (`docs/BACKBONE_CONTROLNET_2026-08-18.md`, Kap. 5): `_baue_parameter`
# kannte kein `guidance_scale`, also griff die Vorgabe von diffusers. Für ein destilliertes
# Turbo-Modell ist die falsch — und beim richtigen Wert 0.0 wird der negative Prompt still
# ignoriert. Dieselbe Fehlerklasse wie `auf-20260818-09`, nur an einem anderen Argument.
# ==========================================================================================

def test_fuehrung_steht_im_parametersatz(tiefe, ziel):
    """Was nicht im Parametersatz steht, kann das Modell nicht benutzt haben."""
    ergebnis = rendere(auftrag(tiefe, ausgabe_png=ziel), modell=Attrappe())
    assert "fuehrung" in ergebnis["parameter"]


def test_die_fuehrung_des_backbones_greift_ohne_eigene_angabe(tiefe, ziel):
    """`z-image-turbo` ist destilliert und läuft ohne Führung — 0.0 ist der richtige Wert."""
    ergebnis = rendere(auftrag(tiefe, ausgabe_png=ziel, backbone="z-image-turbo"),
                       modell=Attrappe())
    assert ergebnis["parameter"]["fuehrung"] == 0.0


def test_der_auftrag_schlaegt_die_registry(tiefe, ziel):
    ergebnis = rendere(auftrag(tiefe, ausgabe_png=ziel, backbone="z-image-turbo",
                               fuehrung=3.5), modell=Attrappe())
    assert ergebnis["parameter"]["fuehrung"] == 3.5


def test_unbestimmte_fuehrung_wird_gemeldet_statt_ersetzt(tiefe, ziel):
    """Ein eingesetzter Ersatzwert wäre eine Erfindung — der Hinweis ist die Wahrheit.

    ``None`` heisst: Es greift die Vorgabe von diffusers. Das ist eine fremde
    Entscheidung, und der Ergebnissatz sagt das, statt sie als eigene auszugeben.
    """
    ergebnis = rendere(auftrag(tiefe, ausgabe_png=ziel, backbone="qwen-image-2512"),
                       modell=Attrappe())
    assert ergebnis["parameter"]["fuehrung"] is None
    assert any("keine Führung" in h for h in ergebnis["hinweise"])


def test_negativer_prompt_unter_fuehrung_eins_wird_als_wirkungslos_gemeldet(tiefe, ziel):
    """Der stille Fall: Der negative Prompt steht im Protokoll, im Bild wirkt er nicht.

    Unterhalb von 1.0 schaltet diffusers die klassifikatorfreie Führung ab. Ohne diesen
    Hinweis stünde ein negativer Prompt in der Wiederholvorschrift, hätte aber nie ein
    Bild beeinflusst — und eine Vergleichsreihe darüber ergäbe dreimal dasselbe Bild.
    """
    ergebnis = rendere(auftrag(tiefe, ausgabe_png=ziel, backbone="z-image-turbo",
                               negativ_prompt="unscharf, verzerrt"), modell=Attrappe())
    treffer = [h for h in ergebnis["hinweise"] if "WIRKUNGSLOS" in h]
    assert treffer, ergebnis["hinweise"]
    assert "unscharf, verzerrt" in treffer[0]


def test_ohne_negativen_prompt_kein_hinweis(tiefe, ziel):
    """Ein Hinweis, der immer kommt, wird überlesen."""
    ergebnis = rendere(auftrag(tiefe, ausgabe_png=ziel, backbone="z-image-turbo"),
                       modell=Attrappe())
    assert not any("WIRKUNGSLOS" in h for h in ergebnis["hinweise"])


# ==========================================================================================
# Die SDXL-Falle — eine tragende Naht nicht als kaputt melden
# ==========================================================================================

class _PipelineOhneControlNet:
    """Eine Bildbearbeitungs-Pipeline: nimmt ein `image`, hat aber kein ControlNet."""
    controlnet = None


class _SdxlControlNet:
    """SDXL nennt das Steuerbild `image` und kennt `control_image` gar nicht."""
    controlnet = object()


def test_sdxl_naht_wird_als_controlnet_erkannt_obwohl_control_image_fehlt():
    """Der spiegelbildliche Fehler zu `auf-20260818-09` — hier verhindert.

    Dort wurde eine fehlende Naht für vorhanden gehalten. Hier würde eine tragende für
    kaputt erklärt, bloss weil sie ihren Eingang anders nennt.
    """
    assert ist_controlnet_naht(_SdxlControlNet(), {"image": "…"}) is True


def test_controlnet_staerke_im_argumentsatz_genuegt_als_beleg():
    """Wer eine ControlNet-Stärke zu regeln hat, hat ein ControlNet."""
    assert ist_controlnet_naht(_PipelineOhneControlNet(),
                               {"controlnet_conditioning_scale": 0.8}) is True


def test_eine_pipeline_ohne_beides_ist_keine_controlnet_naht():
    assert ist_controlnet_naht(_PipelineOhneControlNet(), {"image": "…"}) is False


def test_der_name_der_pipeline_entscheidet_nicht():
    """Modellname und Fassungsnummer haben sich in diesem Projekt zweimal geirrt."""
    class HeisstNachControlNetIstAberKeines:
        __name__ = "SuperControlNetPipelineXL"
        controlnet = None
    assert ist_controlnet_naht(HeisstNachControlNetIstAberKeines(), {"image": "…"}) is False


# ==========================================================================================
# Die Tiefenpolarität — der teuerste ungeprüfte Punkt der Kette
#
# `auf-20260818-13` hat gemessen, was keine Modellkarte sagt: Das ControlNet von Z-Image
# erwartet nah = DUNKEL, unsere `tiefe_norm.png` schreibt nah = hell. Mit unserer Karte
# liegt |spearman| bei 0.38–0.52, mit umgedrehter bei 0.79–0.85 — bei jeder Stärke rund
# das Doppelte.
#
# Eine verkehrte Polarität erklärt einen schlechten Score VOLLSTÄNDIG. Und sie sieht aus
# wie ein Problem des Bildmodells, während sie eines der Übergabe ist.
# ==========================================================================================

def test_die_polaritaet_steht_im_parametersatz(tiefe, ziel):
    """Was nicht im Parametersatz steht, kann ein späterer Leser nicht nachvollziehen.

    Die Datei auf der Platte bleibt unverändert — das Modell sieht womöglich ihr Negativ.
    Ohne diesen Eintrag wäre nicht erkennbar, welche Karte gewirkt hat.
    """
    ergebnis = rendere(auftrag(tiefe, ausgabe_png=ziel), modell=Attrappe())
    assert "tiefe_invertiert" in ergebnis["parameter"]
    assert "tiefen_polaritaet_modell" in ergebnis["parameter"]


def test_bei_z_image_wird_gedreht_und_es_steht_dabei(tiefe, ziel):
    ergebnis = rendere(auftrag(tiefe, ausgabe_png=ziel, backbone="z-image-turbo"),
                       modell=Attrappe())
    assert ergebnis["parameter"]["tiefe_invertiert"] is True
    assert ergebnis["parameter"]["tiefen_polaritaet_modell"] == backbone.POL_NAH_DUNKEL
    assert any("UMGEDREHT" in h for h in ergebnis["hinweise"])


def test_bei_ungemessener_polaritaet_wird_nicht_gedreht_aber_gewarnt(tiefe, ziel):
    """Raten hiesse, mit halber Wahrscheinlichkeit die Geometrie zu spiegeln — lautlos.

    Schweigen wäre aber schlimmer als nicht drehen: Ein schlechter Score hat hier
    womöglich eine harmlose Erklärung, und ohne den Hinweis sucht jemand tagelang am
    Bildmodell.
    """
    ergebnis = rendere(auftrag(tiefe, ausgabe_png=ziel, backbone="qwen-image-2512"),
                       modell=Attrappe())
    assert ergebnis["parameter"]["tiefe_invertiert"] is False
    assert any("nicht gemessen" in h and "NICHT gedreht" in h
               for h in ergebnis["hinweise"])


def test_die_warnung_nennt_die_groesse_des_unterschieds(tiefe, ziel):
    """Ein Hinweis ohne Zahl wird als Formalie gelesen.

    „Kann daran liegen" ist ein Achselzucken; „hebt |spearman| von 0.38 auf 0.85" ist ein
    Grund, sofort nachzusehen.
    """
    ergebnis = rendere(auftrag(tiefe, ausgabe_png=ziel, backbone="qwen-image-2512"),
                       modell=Attrappe())
    text = " ".join(ergebnis["hinweise"])
    assert "0.79" in text or "0.85" in text


def test_unsere_eigene_konvention_ist_benannt():
    """Ohne einen benannten Bezugspunkt ist „umgedreht" keine Aussage."""
    assert backbone.UNSERE_POLARITAET == backbone.POL_NAH_HELL
    assert backbone.POL_NAH_HELL in backbone.TIEFENPOLARITAETEN


def test_jede_polaritaet_in_der_registry_ist_eine_bekannte():
    for name, eintrag in backbone.BACKBONES.items():
        assert eintrag.tiefen_polaritaet in backbone.TIEFENPOLARITAETEN, name


# ======================================================================================
# Der Schrittzähler — der einzige BELEGTE Fortschritt, den dieses Projekt hat
# ======================================================================================

class Pipelineattrappe:
    """Eine diffusers-Pipeline, die ihren `callback_on_step_end` wirklich ruft."""

    def __init__(self, *, kennt_rueckruf: bool = True, schritte: int = 4):
        self._kennt = kennt_rueckruf
        self._schritte = schritte
        self.gesehen = {}

    def __call__(self, **kw):
        self.gesehen = kw
        rueckruf = kw.get("callback_on_step_end")
        if rueckruf is not None:
            for i in range(self._schritte):
                zurueck = rueckruf(self, i, 0.0, {"latents": "x"})
                assert isinstance(zurueck, dict), (
                    "diffusers bricht ab, wenn der Rückruf kein Wörterbuch liefert")
        return type("Aus", (), {"images": [_Bildattrappe()]})()


class _Bildattrappe:
    height = 64
    width = 64

    def save(self, ziel):
        Path(ziel).write_bytes(b"\x89PNG")


def _schreibe_graustufen_png(pfad):
    """Ein winziges, gültiges 8-Bit-Graustufen-PNG — Pillow liest es, wir brauchen es nur
    als Datei, die es gibt."""
    import struct
    import zlib

    breite = hoehe = 2
    roh = b"".join(b"\x00" + bytes([128, 200]) for _ in range(hoehe))

    def block(art, nutz):
        return (struct.pack(">I", len(nutz)) + art + nutz
                + struct.pack(">I", zlib.crc32(art + nutz) & 0xFFFFFFFF))

    Path(pfad).write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + block(b"IHDR", struct.pack(">IIBBBBB", breite, hoehe, 8, 0, 0, 0, 0))
        + block(b"IDAT", zlib.compress(roh))
        + block(b"IEND", b""))
    return pfad


@pytest.fixture
def pillow_attrappe(monkeypatch):
    """Ein winziges `PIL`-Ersatzmodul.

    ``_pipeline_adapter`` galt in diesem Modul bisher als **ungeprüft** — es lädt Pillow,
    und im Entwicklungscontainer gibt es weder Pillow noch torch. Geprüft werden soll hier
    aber nicht Pillow, sondern **unsere Verdrahtung**: ob der Schrittzähler ankommt und
    ob eine Pipeline, die ihn nicht kennt, gemeldet wird.

    Die Attrappe ist darum bewusst dumm und heisst so. Sie ersetzt kein Pillow — sie
    macht nur den Weg dorthin begehbar.
    """
    import sys as _sys
    import types

    class _Bild:
        height = width = 64

        def convert(self, _modus):
            return self

        def save(self, ziel):
            Path(ziel).write_bytes(b"\x89PNG")

    pil = types.ModuleType("PIL")
    bildmodul = types.ModuleType("PIL.Image")
    bildmodul.open = lambda _pfad: _Bild()
    ops = types.ModuleType("PIL.ImageOps")
    ops.invert = lambda bild: bild
    pil.Image = bildmodul
    pil.ImageOps = ops
    monkeypatch.setitem(_sys.modules, "PIL", pil)
    monkeypatch.setitem(_sys.modules, "PIL.Image", bildmodul)
    monkeypatch.setitem(_sys.modules, "PIL.ImageOps", ops)
    return pil


class _Torchattrappe:
    """Nur so viel torch, wie der Adapter wirklich anfasst.

    Die Liste ist kurz und soll es bleiben: Was hier fehlt, fällt beim Lauf sofort auf —
    und jede Zeile mehr wäre eine Zeile, die vorgibt, torch zu sein."""

    class _Cuda:
        @staticmethod
        def is_available():
            return False

    cuda = _Cuda()

    class Generator:
        def __init__(self, device=None):
            self.device = device

        def manual_seed(self, seed):
            self.seed = seed
            return self


def _adapter(pipeline, zaehler=None):
    eintrag = backbone.hole(render.VORGABE_BACKBONE)
    return render._pipeline_adapter(pipeline, eintrag, _Torchattrappe(),
                                    schrittzaehler=zaehler)


def test_der_zaehler_wird_je_schritt_gerufen(tmp_path, monkeypatch, pillow_attrappe):
    gezaehlt = []
    pipeline = Pipelineattrappe(schritte=5)
    monkeypatch.setattr(render, "_vertraegliche_argumente",
                        lambda p, a: (dict(a), []))
    tiefe = tmp_path / "t.png"
    _schreibe_graustufen_png(tiefe)
    modell = _adapter(pipeline, gezaehlt.append)
    modell({"depth_png": str(tiefe), "tiefe_invertiert": False, "seed": 1,
            "prompt": "x", "negativ_prompt": "", "controlnet_staerke": 0.8,
            "schritte": 5, "fuehrung": 1.0, "modus": render.MODUS_TXT2IMG,
            "denoise": 0.6, "beauty_png": None, "ausgabe_png": str(tmp_path / "b.png")})
    assert gezaehlt == [1, 2, 3, 4, 5], "ab eins gezählt, nicht ab null"


def test_der_rueckruf_wird_auch_ohne_eigenen_zaehler_gesetzt(tmp_path, monkeypatch,
                                                             pillow_attrappe):
    """Absicht, und eine Änderung gegenüber der ersten Fassung.

    Der Adapter zählt die Schritte **immer** selbst — nur so lässt sich melden, dass eine
    Pipeline weniger gerechnet hat als bestellt. Ein eigener `schrittzaehler` hängt sich
    daran, statt ihn zu ersetzen.
    """
    pipeline = Pipelineattrappe(schritte=5)
    monkeypatch.setattr(render, "_vertraegliche_argumente", lambda p, a: (dict(a), []))
    tiefe = _schreibe_graustufen_png(tmp_path / "t.png")
    ergebnis = _adapter(pipeline, None)({
        "depth_png": str(tiefe), "tiefe_invertiert": False, "seed": 1, "prompt": "x",
        "negativ_prompt": "", "controlnet_staerke": 0.8, "schritte": 5,
        "fuehrung": 1.0, "modus": render.MODUS_TXT2IMG, "denoise": 0.6,
        "beauty_png": None, "ausgabe_png": str(tmp_path / "b.png")})
    assert "callback_on_step_end" in pipeline.gesehen
    assert ergebnis["schritte_gerechnet"] == 5


def test_eine_pipeline_ohne_rueckruf_wird_GEMELDET(tmp_path, monkeypatch, pillow_attrappe):
    """Ein Rückruf, der nie gerufen wird, sähe von aussen genauso aus wie ein hängender
    Lauf. Genau die Fehlerart, gegen die dieses Modul seit `auf-09` gebaut ist."""
    pipeline = Pipelineattrappe()
    monkeypatch.setattr(
        render, "_vertraegliche_argumente",
        lambda p, a: ({k: v for k, v in a.items() if k != "callback_on_step_end"},
                      ["callback_on_step_end"]))
    tiefe = tmp_path / "t.png"
    _schreibe_graustufen_png(tiefe)
    ergebnis = _adapter(pipeline, lambda s: None)({
        "depth_png": str(tiefe), "tiefe_invertiert": False, "seed": 1, "prompt": "x",
        "negativ_prompt": "", "controlnet_staerke": 0.8, "schritte": 5,
        "fuehrung": 1.0, "modus": render.MODUS_TXT2IMG, "denoise": 0.6,
        "beauty_png": None, "ausgabe_png": str(tmp_path / "b.png")})
    hinweise = " ".join(ergebnis["hinweise"])
    assert "callback_on_step_end" in hinweise
    assert "NICHT verdrahtet" in hinweise
    assert "Lebenszeichen" in hinweise, "der Unterschied gehört in die Meldung"


def test_ein_werfender_zaehler_nimmt_den_render_nicht_mit(tmp_path, monkeypatch, pillow_attrappe):
    """Ein Fortschrittszähler, der einen laufenden Render abbricht, kostet mehr, als er
    je einbringt — und der Abbruch käme als Fehler des Renderers daher."""
    pipeline = Pipelineattrappe(schritte=3)
    monkeypatch.setattr(render, "_vertraegliche_argumente", lambda p, a: (dict(a), []))
    tiefe = tmp_path / "t.png"
    _schreibe_graustufen_png(tiefe)

    def kaputt(_schritt):
        raise RuntimeError("der Zähler ist hin")

    ergebnis = _adapter(pipeline, kaputt)({
        "depth_png": str(tiefe), "tiefe_invertiert": False, "seed": 1, "prompt": "x",
        "negativ_prompt": "", "controlnet_staerke": 0.8, "schritte": 3,
        "fuehrung": 1.0, "modus": render.MODUS_TXT2IMG, "denoise": 0.6,
        "beauty_png": None, "ausgabe_png": str(tmp_path / "b.png")})
    assert ergebnis["bild_png"], "das Bild muss trotzdem entstehen"


def test_der_rueckruf_liefert_das_woerterbuch_zurueck():
    """diffusers bricht mitten im Sampling ab, wenn er None bekommt."""
    rueckruf = render._als_diffusers_rueckruf(lambda s: None)
    kwargs = {"latents": "etwas"}
    assert rueckruf(None, 0, 0.0, kwargs) is kwargs


def test_die_zahl_der_wirklich_gerechneten_schritte_steht_im_ergebnis(tmp_path,
                                                                      monkeypatch,
                                                                      pillow_attrappe):
    """Im Bildbearbeitungsmodus rechnen viele Pipelines nur `schritte × denoise`.

    Der Parametersatz nennt die **bestellte** Zahl. Wer zwei Läufe über die Schrittzahl
    vergleicht, verglich bis heute in Wahrheit etwas anderes.
    """
    pipeline = Pipelineattrappe(schritte=12)          # 20 bestellt, 12 gerechnet
    monkeypatch.setattr(render, "_vertraegliche_argumente", lambda p, a: (dict(a), []))
    tiefe = _schreibe_graustufen_png(tmp_path / "t.png")
    ergebnis = _adapter(pipeline)({
        "depth_png": str(tiefe), "tiefe_invertiert": False, "seed": 1, "prompt": "x",
        "negativ_prompt": "", "controlnet_staerke": 0.8, "schritte": 20,
        "fuehrung": 1.0, "modus": render.MODUS_TXT2IMG, "denoise": 0.6,
        "beauty_png": None, "ausgabe_png": str(tmp_path / "b.png")})
    assert ergebnis["schritte_gerechnet"] == 12
    hinweise = " ".join(ergebnis["hinweise"])
    assert "12 Diffusionsschritte, bestellt waren 20" in hinweise
    assert "20 x 0.6 = 12" in hinweise, "die Rechnung gehört in die Meldung"


def test_gleiche_schrittzahl_erzeugt_keinen_hinweis(tmp_path, monkeypatch,
                                                    pillow_attrappe):
    pipeline = Pipelineattrappe(schritte=20)
    monkeypatch.setattr(render, "_vertraegliche_argumente", lambda p, a: (dict(a), []))
    tiefe = _schreibe_graustufen_png(tmp_path / "t.png")
    ergebnis = _adapter(pipeline)({
        "depth_png": str(tiefe), "tiefe_invertiert": False, "seed": 1, "prompt": "x",
        "negativ_prompt": "", "controlnet_staerke": 0.8, "schritte": 20,
        "fuehrung": 1.0, "modus": render.MODUS_TXT2IMG, "denoise": 1.0,
        "beauty_png": None, "ausgabe_png": str(tmp_path / "b.png")})
    assert ergebnis["schritte_gerechnet"] == 20
    assert not [h for h in ergebnis["hinweise"] if "bestellt waren" in h]


def test_ohne_rueckruf_ist_die_zahl_ungemessen_und_nicht_null(tmp_path, monkeypatch,
                                                              pillow_attrappe):
    """None heisst ungemessen. Null hiesse: es lief kein einziger Schritt."""
    pipeline = Pipelineattrappe()
    monkeypatch.setattr(
        render, "_vertraegliche_argumente",
        lambda p, a: ({k: v for k, v in a.items() if k != "callback_on_step_end"},
                      ["callback_on_step_end"]))
    tiefe = _schreibe_graustufen_png(tmp_path / "t.png")
    ergebnis = _adapter(pipeline)({
        "depth_png": str(tiefe), "tiefe_invertiert": False, "seed": 1, "prompt": "x",
        "negativ_prompt": "", "controlnet_staerke": 0.8, "schritte": 20,
        "fuehrung": 1.0, "modus": render.MODUS_TXT2IMG, "denoise": 0.6,
        "beauty_png": None, "ausgabe_png": str(tmp_path / "b.png")})
    assert ergebnis["schritte_gerechnet"] is None
    assert ergebnis["hinweise"], "die Nichtverdrahtung selbst muss gemeldet sein"
    assert not [h for h in ergebnis["hinweise"] if "bestellt waren" in h], (
        "ohne Messung darf keine Abweichung behauptet werden")


def test_rendere_reicht_die_zahl_bis_ins_ergebnis(tmp_path):
    tiefe = _schreibe_graustufen_png(tmp_path / "t.png")
    ziel = tmp_path / "bild.png"

    def modell(parameter):
        Path(parameter["ausgabe_png"]).write_bytes(b"\x89PNG")
        return {"bild_png": parameter["ausgabe_png"], "schritte_gerechnet": 7}

    ergebnis = render.rendere(
        render.RenderAuftrag(depth_png=str(tiefe), prompt="x", ausgabe_png=str(ziel)),
        modell=modell)
    assert ergebnis["status"] == "ok"
    assert ergebnis["schritte_gerechnet"] == 7


def test_ein_modell_das_nur_einen_pfad_liefert_meldet_ungemessen(tmp_path):
    tiefe = _schreibe_graustufen_png(tmp_path / "t.png")
    ziel = tmp_path / "bild.png"

    def modell(parameter):
        Path(parameter["ausgabe_png"]).write_bytes(b"\x89PNG")
        return parameter["ausgabe_png"]

    ergebnis = render.rendere(
        render.RenderAuftrag(depth_png=str(tiefe), prompt="x", ausgabe_png=str(ziel)),
        modell=modell)
    assert ergebnis["schritte_gerechnet"] is None


# ---------------------------------------------------------------------------------------
# Der ControlNet-Ladeweg — Demolauf 2, 19.08.2026
# ---------------------------------------------------------------------------------------
#
# `lade_modell` rief bis dahin schlicht `DiffusionPipeline.from_pretrained` und bekam fuer
# `z-image-turbo` eine blanke `ZImagePipeline` — reines Text-zu-Bild, ohne Steuereingang.
# Der Adapter reichte die Tiefenkarte als `image` durch, und auch das kennt sie nicht.
# Geprueft wird hier, was OHNE GPU pruefbar ist: dass der Weg ueberhaupt genommen wird und
# dass er bei fehlenden Gewichten sprechend abbricht statt spaeter.

def test_vorgabe_backbone_nennt_seinen_controlnet_ordner():
    """Ohne Ordner ist die Repo-Kennung kein Pfad — und der Ladeweg raet nicht."""
    from aiimaging.backbone import BACKBONES, VORGABE_BACKBONE
    e = BACKBONES[VORGABE_BACKBONE]
    assert e.controlnet_id, "der Vorgabe-Backbone konditioniert ueber ein ControlNet"
    assert e.controlnet_ordner, "…und muss sagen, wo dessen Gewichte liegen"


def test_ohne_controlnet_ordner_bricht_es_sprechend_ab(tmp_path):
    from dataclasses import replace
    from aiimaging import render
    from aiimaging.backbone import BACKBONES, VORGABE_BACKBONE
    e = replace(BACKBONES[VORGABE_BACKBONE], controlnet_ordner=None)
    with pytest.raises(render.RenderError) as fehler:
        render._lade_mit_controlnet(e, tmp_path / "basis", torch=None)
    assert "controlnet_ordner" in str(fehler.value)
    assert "kein Pfad" in str(fehler.value)


def test_fehlende_controlnet_gewichte_brechen_vor_dem_laden_ab(tmp_path):
    """Der Ordner ist da, die Datei nicht — das soll JETZT auffallen, nicht nach 20 GB."""
    from aiimaging import render
    from aiimaging.backbone import BACKBONES, VORGABE_BACKBONE
    (tmp_path / "cn").mkdir()
    e = BACKBONES[VORGABE_BACKBONE]
    e = type(e)(**{**e.__dict__, "controlnet_ordner": "cn"})
    with pytest.raises(render.RenderError) as fehler:
        render._lade_mit_controlnet(e, tmp_path / "basis", torch=None)
    text = str(fehler.value)
    assert "safetensors" in text
    assert "erfundene Kubatur" in text        # der Grund, nicht nur der Umstand
