"""Regel 1 in ausführbarer Form — plus die Fallen der Modellandschaft.

``backbone.py`` ist eine Tabelle. Eine Tabelle kann man falsch abschreiben, und die
folgenschwerste Art, sie falsch abzuschreiben, betrifft die Lizenz. Darum steht der
wichtigste Test dieser Datei zuoberst:
``test_waehle_kommerziell_gibt_niemals_ein_non_commercial_modell``. Er hält fest, dass
FLUX.1-dev und FLUX.2-dev bei der vorgabegemässen Auswahl **niemals** erscheinen.

Damit dieser Test nicht vakuös ist, steht die Gegenprobe daneben: Beide Modelle sind
tatsächlich in der Registry und tauchen bei gelockerter Anforderung auf. Ein Filter, der
nur deshalb nichts Verbotenes liefert, weil das Verbotene gar nicht existiert, bewacht
nichts.

Die zweite Falle ist subtiler: **FLUX.2-klein-4B ist Apache-2.0 und trotzdem kein
Kandidat für die Depth-Naht.** Wer nur nach der Lizenz filtert, wählt ein Modell, für das
die Konditionierung dieses Projekts nicht existiert. Auch das ist hier festgehalten.

Kein Netz, keine GPU, keine Gewichte — die Registry ist Daten.
"""
from __future__ import annotations

import ast
import dataclasses
import sys
from pathlib import Path

import pytest

from aiimaging.backbone import (
    BACKBONES,
    KOND_DEPTH_CONTROLNET,
    KOND_INTEGRIERTES_EDIT,
    KONDITIONIERUNGEN,
    QUELLE_MODELLKARTE,
    QUELLE_SEKUNDAER,
    QUELLE_UNGEPRUEFT,
    RUECKFALL_BACKBONE,
    VORGABE_BACKBONE,
    VORSCHAU_BACKBONE,
    Backbone,
    BackboneError,
    hole,
    ist_belegt,
    pruefe_lizenz,
    vorhandene_dateien,
    waehle,
)

#: Die unter Regel 1 ausgeschlossenen Gewichte. Namentlich, nicht als Suchmuster —
#: der Ausschluss soll auch dann auffallen, wenn jemand den Lizenznamen umformuliert.
NON_COMMERCIAL = ("flux1-dev", "flux2-dev")


# --------------------------------------------------------------------------------------
# 0 · Regel 1 — der Test, wegen dem dieses Modul die Lizenz im Datensatz trägt
# --------------------------------------------------------------------------------------

def test_waehle_kommerziell_gibt_niemals_ein_non_commercial_modell():
    """Regel 1: Die vorgabegemässe Auswahl enthält kein FLUX-dev. Nie."""
    namen = {b.name for b in waehle(kommerziell=True)}
    verstoss = namen.intersection(NON_COMMERCIAL)
    assert not verstoss, (
        f"{sorted(verstoss)} ist Non-Commercial und darf in keiner kommerziellen "
        "Auswahl auftauchen — Modellgewichte zählen unter Regel 1 mit."
    )


def test_die_vorgabe_von_waehle_ist_kommerziell():
    """Wer nichts sagt, bekommt nichts Ausgeschlossenes — der Default trägt die Regel."""
    assert {b.name for b in waehle()} == {b.name for b in waehle(kommerziell=True)}


def test_der_regel_1_test_ist_nicht_vakuos():
    """Gegenprobe: Die verbotenen Modelle sind da — der Filter entfernt sie tatsächlich.

    Ohne diesen Test liesse sich der Test darüber grün halten, indem man die Einträge
    schlicht löscht. Dann bewachte er nichts.
    """
    alle = {b.name for b in waehle(kommerziell=False)}
    assert set(NON_COMMERCIAL) <= alle, "Die ausgeschlossenen Modelle fehlen in der Registry"
    assert set(NON_COMMERCIAL) <= set(BACKBONES)


def test_kommerziell_false_lockert_die_anforderung_statt_sie_umzukehren():
    """``kommerziell=False`` heisst „egal", nicht „nur Non-Commercial"."""
    gelockert = {b.name for b in waehle(kommerziell=False)}
    assert gelockert == set(BACKBONES)
    assert VORGABE_BACKBONE in gelockert


@pytest.mark.parametrize("name", sorted(BACKBONES))
def test_flag_und_lizenzname_widersprechen_sich_nie(name):
    """``kommerziell_nutzbar`` und der Lizenzname müssen dasselbe sagen.

    Beide Felder werden von Hand gepflegt. Widersprechen sie sich, ist unklar, welches
    die Auswahl steuert — und das ist genau der Zustand, in dem Regel 1 lautlos kippt.
    """
    backbone = BACKBONES[name]
    non_commercial_im_namen = "non-commercial" in backbone.lizenz.lower()
    assert backbone.kommerziell_nutzbar is not non_commercial_im_namen


@pytest.mark.parametrize("name", NON_COMMERCIAL)
def test_pruefe_lizenz_meldet_den_ausschluss_ausdruecklich(name):
    """Regel 1 verlangt eine ausdrückliche Meldung, kein stillschweigendes Übergehen."""
    urteil = pruefe_lizenz(name)
    assert urteil["zulaessig"] is False
    assert urteil["kommerziell_nutzbar"] is False
    assert "AUSGESCHLOSSEN" in urteil["begruendung"]
    # Der Ausschluss erstreckt sich auf abgeleitete LoRAs — das ist der Teil, der beim
    # Stil-Training zuschlägt und darum in der Begründung stehen muss.
    assert "LoRA" in urteil["begruendung"]


# --------------------------------------------------------------------------------------
# 1 · Die Registry als Datensatz
# --------------------------------------------------------------------------------------

def test_registry_ist_nicht_leer():
    """Vorbedingung: Alle parametrisierten Tests laufen über echte Einträge."""
    assert len(BACKBONES) >= 8


@pytest.mark.parametrize("name", sorted(BACKBONES))
def test_schluessel_und_name_stimmen_ueberein(name):
    """Ein Eintrag unter falschem Schlüssel ist über ``hole`` nicht mehr auffindbar."""
    assert BACKBONES[name].name == name


@pytest.mark.parametrize("name", sorted(BACKBONES))
def test_jeder_eintrag_ist_vollstaendig_und_plausibel(name):
    """Grundzusagen des Datensatzes: Kennung, Grösse, Lizenz, Dateien, Konditionierung."""
    b = BACKBONES[name]
    assert "/" in b.modell_id, "modell_id ist keine Hugging-Face-Repo-Kennung"
    assert b.parameter_b > 0
    assert b.lizenz.strip()
    assert isinstance(b.kommerziell_nutzbar, bool)
    assert b.konditionierung in KONDITIONIERUNGEN
    assert isinstance(b.dateien, tuple) and b.dateien, "ohne Dateiliste ist nichts prüfbar"


@pytest.mark.parametrize("name", sorted(BACKBONES))
def test_vram_schaetzung_fasst_die_gewichte_mindestens(name):
    """Untere Schranke statt Formeltreue: Gewichte in bf16 müssen hineinpassen.

    Bewusst keine Prüfung auf die Schätzformel — sonst müsste eine später *gemessene*
    Zahl den Test brechen. Gemessen wird hier nichts: Es gibt keine GPU.
    """
    b = BACKBONES[name]
    assert b.vram_gb >= b.parameter_b * 2.0


def test_backbone_ist_unveraenderlich():
    """``frozen=True``: Ein Zuweisen an ``kommerziell_nutzbar`` würde Regel 1 aushebeln."""
    with pytest.raises(dataclasses.FrozenInstanceError):
        hole(VORGABE_BACKBONE).kommerziell_nutzbar = True  # type: ignore[misc]


def test_backbone_laesst_sich_ohne_lizenz_quelle_bauen():
    """Das nachgetragene Feld hat einen Vorgabewert — ältere Aufrufe bleiben gültig.

    Und der Vorgabewert ist die zurückhaltendste Annahme: nicht belegt. Geprüft wird der
    **Zustand** (``ist_belegt``) und nicht der Name der Vokabel — ein Vergleich auf einen
    Namen wäre genau der Fehler, an dem sich die Lizenzprüfung vom 18.08.2026 gestossen
    hat.
    """
    b = Backbone("x", "org/x", 1.0, "Apache-2.0", True, KOND_DEPTH_CONTROLNET, 2.4, ("a",))
    assert not ist_belegt(b.lizenz_quelle)


# --------------------------------------------------------------------------------------
# 2 · Die belegten Fakten aus der Lagebeurteilung, Kapitel 4
# --------------------------------------------------------------------------------------

def test_vorgabe_ist_qwen_edit_und_apache(tmp_path=None):
    """Die Vorgabe ist permissiv und belegt — **aber sie ist kein Depth-ControlNet.**

    Bis zum 18.08.2026 hiess dieser Test „…_und_depth_naht" und prüfte genau das. Der
    erste echte Render (`auf-20260818-09`) hat es widerlegt: `QwenImageEditPlusPipeline`
    kennt weder einen `control_image`-Eingang noch `controlnet_conditioning_scale` noch
    `strength`. Die Tiefenkarte geht als `image` hinein und **ersetzt dabei den
    Beauty-Pass**; `controlnet_staerke` und `denoise` sind wirkungslos.

    Der Test hält jetzt fest, was stimmt — und ausdrücklich mit, dass die Vorgabe
    **keine** ControlNet-Naht hat. Sonst käme die alte Annahme über einen anderen Test
    zurück.
    """
    e = hole(VORGABE_BACKBONE)
    assert e.name == "qwen-image-edit-2511"
    assert e.lizenz == "Apache-2.0" and e.kommerziell_nutzbar is True
    assert pruefe_lizenz(e.name)["lizenz_quelle"] == QUELLE_MODELLKARTE
    assert e.konditionierung == KOND_INTEGRIERTES_EDIT, (
        "am Gerät gemessen: kein ControlNet, sondern instruktionsgeführte Bildbearbeitung"
    )



def test_die_vorgabe_steht_in_der_auswahl_vorn():
    """``waehle()[0]`` ist die empfohlene Wahl — Registry-Reihenfolge ist bedeutungstragend."""
    assert waehle()[0].name == VORGABE_BACKBONE


def test_vorschau_pfad_ist_klein_und_apache():
    """Z-Image-Turbo, 6B, Apache-2.0 — der schnelle Pfad für Vorschauen."""
    b = hole(VORSCHAU_BACKBONE)
    assert b.parameter_b == 6.0
    assert b.lizenz == "Apache-2.0"
    assert b.konditionierung == KOND_DEPTH_CONTROLNET
    assert b.vram_gb < hole(VORGABE_BACKBONE).vram_gb


def test_rueckfall_ist_sdxl_mit_eigenem_controlnet():
    """SDXL trägt die Depth-Naht — aber über ein separates ControlNet-Modell."""
    b = hole(RUECKFALL_BACKBONE)
    assert b.konditionierung == KOND_DEPTH_CONTROLNET
    assert any("controlnet" in datei for datei in b.dateien), (
        "SDXL bringt kein natives Depth-ControlNet mit; die Datei gehört in die Liste"
    )


def test_flux2_klein_ist_apache_aber_nicht_die_depth_naht():
    """Die Falle: permissiv lizenziert und trotzdem kein Kandidat für die Naht.

    Wer nur nach der Lizenz filtert, wählt hier ein Modell, für das die
    Depth-ControlNet-Konditionierung dieses Projekts nicht existiert. Die
    Lagebeurteilung nennt das ausdrücklich als etwas, das früh einzuplanen ist.
    """
    b = hole("flux2-klein-4b")
    assert b.lizenz == "Apache-2.0"
    assert b.kommerziell_nutzbar is True
    assert b.konditionierung == KOND_INTEGRIERTES_EDIT
    assert pruefe_lizenz("flux2-klein-4b")["zulaessig"] is True

    depth = {x.name for x in waehle(konditionierung=KOND_DEPTH_CONTROLNET)}
    assert "flux2-klein-4b" not in depth


def test_sd35_meldet_die_umsatzschwelle_als_auflage():
    """Kommerziell nutzbar, aber nicht bedingungslos — die Bedingung gehört benannt."""
    urteil = pruefe_lizenz("sd35-large")
    assert urteil["zulaessig"] is True
    assert any("1 Mio USD" in a for a in urteil["auflagen"])


def test_sdxl_meldet_die_openrail_nutzungsauflagen():
    """OpenRAIL++-M ist keine der vier permissiven Lizenzen aus Regel 1."""
    urteil = pruefe_lizenz(RUECKFALL_BACKBONE)
    assert urteil["zulaessig"] is True
    assert any("OpenRAIL" in a for a in urteil["auflagen"])


# --------------------------------------------------------------------------------------
# 2b · Die Herkunft der Lizenzangabe — Zustand statt Namensliste
#
# Hier stand bis zum 18.08.2026 ``test_ungepruefte_lizenzen_werden_als_solche_gemeldet``,
# parametrisiert über ["sd35-large", "sdxl-juggernaut"]. Der Test hielt damit den
# Wissensstand vom 14.08. fest — eine Schuldenliste, keine Eigenschaft. Als die
# Lizenzprüfung Juggernaut am Original belegte, wurde der Test zum Hindernis: Der Beleg
# konnte nicht eingetragen werden, ohne ihn zu brechen (Prüfbericht Abschnitt 5).
#
# Dazu kam, dass er das Falsche mass. Seine zweite Zusicherung suchte das Wort „geprüft"
# in den Auflagen — und fand es bei Juggernaut in einer Auflage, die mit der Herkunft
# nichts zu tun hat („Modellkarte, geprüft 2026-08-18"). Er wäre also auch dann grün
# geblieben, wenn die Herkunfts-Auflage gefehlt hätte.
#
# Erhalten bleibt, was er sichern sollte: **Eine nicht am Original geprüfte Lizenzangabe
# darf nicht als geprüft durchgehen.** Das ist eine Eigenschaft des Eintrags-Zustands und
# hängt an keinem Namen. Die Gegenprobe steht daneben, sonst wäre die Zusicherung vakuös.
# --------------------------------------------------------------------------------------

def _probe(name, lizenz_quelle):
    """Ein synthetischer Registry-Eintrag, der nur die Herkunft variiert.

    Synthetisch und nicht aus dem Bestand gegriffen: Sonst hinge der Test wieder daran,
    dass ein bestimmtes Modell einen bestimmten Prüfstand hat — also an genau der
    Schuldenliste, die hier abgeräumt wird.
    """
    return Backbone(name, f"org/{name}", 1.0, "Apache-2.0", True,
                    KOND_DEPTH_CONTROLNET, 2.4, ("model_index.json",),
                    lizenz_quelle=lizenz_quelle)


@pytest.mark.parametrize("quelle", [QUELLE_UNGEPRUEFT, QUELLE_SEKUNDAER, "", "irgendwas"])
def test_eine_nicht_belegte_lizenzangabe_geht_nicht_als_geprueft_durch(monkeypatch, quelle):
    """Die eigentliche Zusicherung: kein Beleg, kein „geprüft" — egal welcher Eintrag."""
    monkeypatch.setitem(BACKBONES, "probe-unbelegt", _probe("probe-unbelegt", quelle))

    urteil = pruefe_lizenz("probe-unbelegt")
    assert urteil["lizenz_belegt"] is False
    assert any(a.startswith("Lizenzangabe") for a in urteil["auflagen"]), (
        "Eine unbelegte Lizenzangabe muss als Auflage erscheinen, nicht als Fussnote"
    )
    assert "Lizenzangabe" in urteil["begruendung"]


def test_die_sekundaerquelle_wird_von_gar_nicht_geprueft_unterschieden(monkeypatch):
    """Beides ist kein Beleg — aber „sekundär gehört" ist nicht dasselbe wie „nichts"."""
    monkeypatch.setitem(BACKBONES, "probe-sekundaer",
                        _probe("probe-sekundaer", QUELLE_SEKUNDAER))
    monkeypatch.setitem(BACKBONES, "probe-nichts",
                        _probe("probe-nichts", QUELLE_UNGEPRUEFT))

    sekundaer = " ".join(pruefe_lizenz("probe-sekundaer")["auflagen"])
    nichts = " ".join(pruefe_lizenz("probe-nichts")["auflagen"])
    assert "Sekundärquelle" in sekundaer
    assert "NICHT geprüft" in nichts
    assert sekundaer != nichts


@pytest.mark.parametrize("quelle", [
    QUELLE_MODELLKARTE,
    "geprueft 2026-08-18 (https://example.invalid/modellkarte)",
])
def test_ein_belegter_eintrag_wird_nicht_als_ungeprueft_gemeldet(monkeypatch, quelle):
    """Die Gegenprobe — ohne sie wäre die Zusicherung oben vakuös.

    Und zugleich der Fehler vom 18.08.2026 in ausführbarer Form: Ein Vermerk mit Datum
    und URL ist ein Beleg. Er wurde als „NICHT geprüft" weitergemeldet, weil exakt auf
    das Schlagwort verglichen wurde. Ein Beleg, den die Prüflogik nicht als Beleg
    erkennt, ist kein Beleg.
    """
    monkeypatch.setitem(BACKBONES, "probe-belegt", _probe("probe-belegt", quelle))

    urteil = pruefe_lizenz("probe-belegt")
    assert urteil["lizenz_belegt"] is True
    assert not any(a.startswith("Lizenzangabe") for a in urteil["auflagen"]), (
        f"{quelle!r} ist ein Beleg und darf nicht als ungeprüft gemeldet werden"
    )
    assert "Lizenzangabe" not in urteil["begruendung"]


@pytest.mark.parametrize("name", sorted(BACKBONES))
def test_die_meldung_folgt_dem_zustand_des_eintrags(name):
    """Dieselbe Regel, angewandt auf den echten Bestand — ohne einen Namen zu nennen.

    Der Test hält keinen Prüfstand fest: Wird ein Eintrag belegt, verschwindet die
    Auflage von selbst und der Test bleibt grün. Er bricht nur, wenn Datensatz und
    Meldung auseinanderlaufen.
    """
    urteil = pruefe_lizenz(name)
    belegt = ist_belegt(BACKBONES[name].lizenz_quelle)

    assert urteil["lizenz_belegt"] is belegt
    herkunft = [a for a in urteil["auflagen"] if a.startswith("Lizenzangabe")]
    assert bool(herkunft) is not belegt, (
        f"{name}: lizenz_quelle={BACKBONES[name].lizenz_quelle!r} und die gemeldeten "
        f"Auflagen {urteil['auflagen']} sagen Verschiedenes"
    )


def test_es_gibt_mindestens_zwei_apache_modelle_an_der_depth_naht():
    """Die Lage ist günstig: Der Verzicht auf FLUX-dev lässt echte Wahl übrig."""
    apache = [b for b in waehle(kommerziell=True, konditionierung=KOND_DEPTH_CONTROLNET)
              if b.lizenz == "Apache-2.0"]
    assert len(apache) >= 2


# --------------------------------------------------------------------------------------
# 3 · hole und waehle — Fehler sind laut, nicht leer
# --------------------------------------------------------------------------------------

def test_hole_nennt_die_bekannten_namen():
    """Ein Tippfehler soll nicht zur Suche im Quelltext zwingen."""
    with pytest.raises(BackboneError) as fehler:
        hole("qwen-image-edit")
    assert VORGABE_BACKBONE in str(fehler.value)


@pytest.mark.parametrize("eingabe", [None, "", "   ", 42])
def test_hole_weist_unbrauchbare_namen_ab(eingabe):
    with pytest.raises(BackboneError):
        hole(eingabe)


def test_unbekannte_konditionierung_ist_ein_fehler_keine_leere_liste():
    """Eine leere Liste läse sich wie „kein Modell passt" statt „deine Anfrage war falsch"."""
    with pytest.raises(BackboneError, match="Konditionierung"):
        waehle(konditionierung="depth")


@pytest.mark.parametrize("grenze", [0, -5, "24", True])
def test_unbrauchbare_vram_grenze_ist_ein_fehler(grenze):
    with pytest.raises(BackboneError):
        waehle(max_vram_gb=grenze)


def test_vram_grenze_filtert_und_ist_nicht_vakuos():
    """Die Grenze schneidet die grossen Modelle weg — und lässt die kleinen stehen."""
    klein = waehle(max_vram_gb=16.0)
    assert klein, "16 GB sollte für den 6B-Vorschaupfad reichen"
    assert VORSCHAU_BACKBONE in {b.name for b in klein}
    assert all(b.vram_gb <= 16.0 for b in klein)
    assert VORGABE_BACKBONE not in {b.name for b in klein}, "20B passt nicht in 16 GB"


def test_filter_lassen_sich_kombinieren():
    """Alle drei Kriterien zugleich — und das Ergebnis erfüllt jedes einzelne."""
    treffer = waehle(kommerziell=True, max_vram_gb=50.0,
                     konditionierung=KOND_DEPTH_CONTROLNET)
    assert treffer
    for b in treffer:
        assert b.kommerziell_nutzbar and b.vram_gb <= 50.0
        assert b.konditionierung == KOND_DEPTH_CONTROLNET


def test_leere_auswahl_ist_erlaubt_wenn_die_anfrage_gueltig_war():
    """Gültige Anfrage ohne Treffer: leere Liste, kein Fehler. Der Unterschied zählt."""
    assert waehle(max_vram_gb=0.5) == []


def test_waehle_gibt_die_registry_nicht_zum_veraendern_heraus():
    """Die zurückgegebene Liste ist eine Kopie — Anhängen darf die Registry nicht anfassen."""
    treffer = waehle()
    treffer.append(treffer[0])
    assert len(waehle()) == len(treffer) - 1


def test_pruefe_lizenz_kennt_dieselben_namen_wie_hole():
    with pytest.raises(BackboneError):
        pruefe_lizenz("gibt-es-nicht")


# --------------------------------------------------------------------------------------
# 4 · vorhandene_dateien — schaut nach, lädt nichts
# --------------------------------------------------------------------------------------

def test_vollstaendige_wurzel_wird_erkannt(tmp_path):
    """Alle benötigten Einträge da — Dateien wie Ordner (diffusers legt beides an)."""
    b = hole(VORGABE_BACKBONE)
    for eintrag in b.dateien:
        ziel = tmp_path / eintrag
        if eintrag.endswith(".json"):
            ziel.write_text("{}", encoding="utf-8")
        else:
            ziel.mkdir()

    ergebnis = vorhandene_dateien(VORGABE_BACKBONE, tmp_path)
    assert ergebnis["vollstaendig"] is True
    assert ergebnis["fehlend"] == ()
    assert set(ergebnis["vorhanden"]) == set(b.dateien)
    assert ergebnis["wurzel_existiert"] is True


def test_fehlende_datei_wird_benannt(tmp_path):
    """Was fehlt, wird namentlich gemeldet — nicht bloss als „unvollständig"."""
    (tmp_path / "model_index.json").write_text("{}", encoding="utf-8")

    ergebnis = vorhandene_dateien(VORGABE_BACKBONE, tmp_path)
    assert ergebnis["vollstaendig"] is False
    assert "model_index.json" in ergebnis["vorhanden"]
    assert "transformer" in ergebnis["fehlend"]


def test_fehlende_wurzel_ist_kein_absturz(tmp_path):
    """Der Normalfall vor dem ersten Download: nichts da, und das wird gesagt."""
    ergebnis = vorhandene_dateien(VORGABE_BACKBONE, tmp_path / "gibt-es-nicht")
    assert ergebnis["vollstaendig"] is False
    assert ergebnis["wurzel_existiert"] is False
    assert set(ergebnis["fehlend"]) == set(hole(VORGABE_BACKBONE).dateien)
    assert ergebnis["vorhanden"] == ()


def test_wurzel_darf_ein_string_sein(tmp_path):
    """Aufrufer arbeiten mit ``str`` wie mit ``Path`` — beides muss gehen."""
    assert vorhandene_dateien(VORGABE_BACKBONE, str(tmp_path))["wurzel"] == str(tmp_path)


# --------------------------------------------------------------------------------------
# 5 · Prüfbar ohne GPU — das ist die Eigenschaft, nicht der Behelf
# --------------------------------------------------------------------------------------

def test_registry_laedt_keine_schweren_bibliotheken():
    """``import aiimaging.backbone`` zieht weder ``torch`` noch ``diffusers`` nach.

    Die Registry ist Daten. Zöge sie das Ökosystem nach, wäre sie genau dort nicht mehr
    lesbar, wo man sie am ehesten befragt: auf einem Rechner ohne GPU.
    """
    import aiimaging.backbone  # noqa: F401

    schwer = [m for m in ("torch", "diffusers", "transformers") if m in sys.modules]
    assert not schwer, f"{schwer} wurde durch die Registry geladen"


def _importierte_wurzelmodule(modul) -> set[str]:
    """Die obersten Modulnamen, die eine Quelldatei importiert — aus dem Syntaxbaum.

    Quelltextprobe statt ``sys.modules``: Was ein anderer Test schon geladen hat, soll
    das Ergebnis nicht verfälschen.
    """
    quelle = Path(modul.__file__).read_text(encoding="utf-8")
    module = set()
    for knoten in ast.walk(ast.parse(quelle)):
        if isinstance(knoten, ast.Import):
            module.update(a.name.split(".")[0] for a in knoten.names)
        elif isinstance(knoten, ast.ImportFrom) and knoten.level == 0 and knoten.module:
            module.add(knoten.module.split(".")[0])
    return module


def test_backbone_importiert_nur_stdlib():
    """Quelltextprobe: keine Fremdabhängigkeit, damit die Tabelle überall lesbar bleibt.

    ``aiimaging`` steht seit dem 18.08.2026 in der erlaubten Menge: Die Vokabel für die
    Herkunft einer Lizenzangabe liegt in ``aiimaging.lizenzquelle``, weil sie drei
    Registries gemeinsam gehört. Das ist keine Fremdabhängigkeit — der nächste Test hält
    fest, dass auch jenes Modul nichts nachzieht.
    """
    import aiimaging.backbone as modul

    assert _importierte_wurzelmodule(modul) <= {
        "__future__", "dataclasses", "pathlib", "aiimaging",
    }


def test_die_lizenzvokabel_zieht_selbst_nichts_nach():
    """Sonst wäre die Erlaubnis oben ein Schlupfloch: ein stdlib-Modul mit Hintertür."""
    import aiimaging.lizenzquelle as modul

    assert _importierte_wurzelmodule(modul) <= {"__future__"}
