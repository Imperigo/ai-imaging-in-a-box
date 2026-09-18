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
import contextlib
import dataclasses
import sys
from pathlib import Path

import pytest

from aiimaging import backbone as backbone_modul
from aiimaging.backbone import (
    BACKBONES,
    GROESSENGEBUNDENE_FAMILIEN,
    groessen_riegel,
    FRUEHERER_VORGABE_BACKBONE,
    KOND_DEPTH_CONTROLNET,
    KOND_INTEGRIERTES_EDIT,
    KONDITIONIERUNGEN,
    QUELLE_MODELLKARTE,
    QUELLE_SEKUNDAER,
    POL_NAH_DUNKEL,
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

def test_die_vorgabe_traegt_endlich_eine_echte_controlnet_naht():
    """Die Geschichte dieses Tests ist die Geschichte des Projekts.

    Er hiess zuerst „…_und_depth_naht" und prüfte, dass die Vorgabe ein Depth-ControlNet
    ist. `auf-20260818-09` hat das widerlegt: `QwenImageEditPlusPipeline` kennt weder
    `control_image` noch `controlnet_conditioning_scale`. Daraufhin hiess er
    „…_ist_qwen_edit_und_apache" und hielt ausdrücklich fest, dass die Vorgabe **keine**
    Naht hat — damit die alte Annahme nicht über einen anderen Test zurückkommt.

    Seit `auf-20260818-13` stimmt der ursprüngliche Anspruch wieder, nur mit einem
    anderen Modell: Z-Image + Fun-ControlNet-Union nimmt beide Argumente wirklich an, und
    die Tiefenordnung bleibt mit |spearman| 0.853 erhalten statt bei 0.005 zu
    verschwinden.
    """
    e = hole(VORGABE_BACKBONE)
    assert e.name == "z-image-turbo"
    assert e.lizenz == "Apache-2.0" and e.kommerziell_nutzbar is True
    assert e.konditionierung == KOND_DEPTH_CONTROLNET
    assert pruefe_lizenz(e.name)["lizenz_quelle"] == QUELLE_MODELLKARTE


def test_die_vorgabe_ist_beidseitig_permissiv():
    """Beide Hälften der Naht — sonst wäre der Wechsel eine Regel-1-Verschlechterung."""
    urteil = pruefe_lizenz(VORGABE_BACKBONE)
    assert urteil["zulaessig"] is True
    assert urteil["controlnet"]["zulaessig"] is True
    assert urteil["controlnet"]["lizenz"] == "Apache-2.0"


def test_die_vorgabe_weiss_welche_tiefenkonvention_sie_erwartet():
    """Der teuerste ungeprüfte Punkt der Kette — jetzt gemessen und deklariert.

    Keine Modellkarte sagt die Konvention. Eine verkehrte Polarität erklärt einen
    schlechten Score vollständig und sieht dabei wie ein Problem des Bildmodells aus.
    """
    assert hole(VORGABE_BACKBONE).tiefen_polaritaet == POL_NAH_DUNKEL


def test_der_frueherer_vorgabewert_bleibt_nachschlagbar():
    """Damit ein alter Lauf im Protokoll deutbar bleibt.

    Ohne diesen Eintrag hielte jemand ein Ergebnis von gestern für einen Messfehler,
    statt für ein Ergebnis eines anderen Modells.
    """
    assert FRUEHERER_VORGABE_BACKBONE in BACKBONES
    assert FRUEHERER_VORGABE_BACKBONE != VORGABE_BACKBONE
    # Und der Grund des Wechsels bleibt am Eintrag ablesbar, nicht nur im Kommentar:
    assert hole(FRUEHERER_VORGABE_BACKBONE).konditionierung == KOND_INTEGRIERTES_EDIT, (
        "am Gerät gemessen: kein ControlNet, sondern instruktionsgeführte Bildbearbeitung"
    )



def test_die_vorgabe_steht_in_der_auswahl_vorn():
    """``waehle()[0]`` ist die empfohlene Wahl — Registry-Reihenfolge ist bedeutungstragend."""
    assert waehle()[0].name == VORGABE_BACKBONE


def test_vorschau_und_vorgabe_sind_dasselbe_modell_geworden():
    """Ein Befund, der die Erwartung umdreht — und darum hier festgehalten wird.

    Der Vorschaupfad war als **Kompromiss** gedacht: klein und schnell, dafür weniger
    treu. Gemessen ist es umgekehrt gekommen. Z-Image ist rund hundertfach schneller als
    der bisherige Vorgabewert (1.4 s gegen 150 s je Bild) **und** hält die Geometrie
    deutlich besser (|spearman| 0.853 gegen 0.005).

    Es gibt hier also nichts abzuwägen. Dass die beiden Namen bestehen bleiben, ist
    Absicht: Sie stehen für zwei verschiedene Fragen, und ein späterer Kandidat kann sie
    wieder trennen.
    """
    assert VORSCHAU_BACKBONE == VORGABE_BACKBONE
    b = hole(VORSCHAU_BACKBONE)
    assert b.parameter_b == 6.0
    assert b.lizenz == "Apache-2.0"
    assert b.konditionierung == KOND_DEPTH_CONTROLNET


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
    """Die Grenze schneidet die grossen Modelle weg — und lässt die kleinen stehen.

    **Berichtigt am 19.08.2026 durch eine Messung.** Hier stand: *«16 GB sollte für den
    6B-Vorschaupfad reichen»*, und der Test verlangte, dass
    :data:`VORSCHAU_BACKBONE` in der 16-GB-Auswahl auftaucht. Das war eine Folgerung aus
    der Parameterzahl (6 B → 14,4 GB geschätzt) — und sie ist falsch.

    Am Gerät gemessen (`auf-20260818-13`, bestätigt in `auf-20260820-21` und `-22`)
    belegen Basis **und ControlNet** in bfloat16 **23,4 GiB**. Das ControlNet ist nicht
    optional: ohne es gibt es keine Konditionierung, und dann rendert die Kette an der
    Geometrie vorbei. Die ehrliche Zahl ist darum die gemeinsame.

    **Was daraus folgt und hier festgehalten gehört:** Der Vorschaupfad passt **nicht**
    auf eine 16-GB-Karte. Er passt auf die RTX 5090 (31,4 GiB nutzbar, Spitze 23 391 MiB
    gemessen). Wer ihn auf kleinerer Hardware braucht, braucht Auslagerung oder
    Quantisierung — nicht eine kleinere Schätzung.
    """
    klein = waehle(max_vram_gb=16.0)
    assert klein, "unter 16 GB sollte mindestens ein Eintrag bleiben"
    assert VORSCHAU_BACKBONE not in {b.name for b in klein}, (
        "z-image-turbo braucht mit ControlNet 23,4 GiB — gemessen, nicht geschätzt"
    )
    assert all(b.vram_gb <= 16.0 for b in klein)
    # Bis zum 18.08.2026 stand hier die Gegenprobe „die 20B-Vorgabe passt nicht in 16 GB".
    # Sie ist mit dem Wechsel gegenstandslos geworden — die Vorgabe IST jetzt das kleine
    # Modell. Die Gegenprobe bleibt, aber an einem Eintrag, der wirklich zu gross ist:
    # sonst wäre der Test vakuös und schnitte gar nichts mehr weg.
    gross = {b.name for b in BACKBONES.values() if b.vram_gb > 16.0}
    assert gross, "kein einziger Eintrag über 16 GB — dann prüft diese Grenze nichts"
    assert not (gross & {b.name for b in klein})


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

    # ``re`` kam am 18.09.2026 dazu: Der Grössenriegel liest die Grössenangabe aus Name
    # und Kennung (``_groessen_behauptungen``). Stdlib, keine Fremdabhängigkeit — die
    # Tabelle bleibt überall lesbar, worum es diesem Test geht.
    assert _importierte_wurzelmodule(modul) <= {
        "__future__", "dataclasses", "pathlib", "re", "aiimaging",
    }


def test_die_lizenzvokabel_zieht_selbst_nichts_nach():
    """Sonst wäre die Erlaubnis oben ein Schlupfloch: ein stdlib-Modul mit Hintertür."""
    import aiimaging.lizenzquelle as modul

    assert _importierte_wurzelmodule(modul) <= {"__future__"}


# ==========================================================================================
# Die zweite Hälfte der Naht — ein Depth-ControlNet ist immer ZWEI Modelle
#
# Befund vom 18.08.2026 (`docs/BACKBONE_CONTROLNET_2026-08-18.md`): Die Registry kannte
# eine Lizenz, die Naht braucht zwei. Damit war bei jedem ControlNet-Eintrag systematisch
# die halbe Naht geprüft — und die andere Hälfte galt als geprüft, weil niemand sie
# vermisste.
# ==========================================================================================

def test_controlnet_eintraege_werden_beidseitig_beurteilt():
    """Jeder Depth-ControlNet-Eintrag muss zur ControlNet-Seite etwas zu sagen haben."""
    for name, eintrag in BACKBONES.items():
        urteil = pruefe_lizenz(name)
        cn = urteil["controlnet"]
        assert cn["noetig"] is (eintrag.konditionierung == KOND_DEPTH_CONTROLNET), name


def test_unbenanntes_controlnet_ist_nicht_dasselbe_wie_ein_erlaubtes():
    """``None`` heisst „nicht beurteilbar", nicht „in Ordnung".

    Genau diese Gleichsetzung war der Fehler: Wo nichts stand, galt nichts als Problem.
    """
    for name, eintrag in BACKBONES.items():
        cn = pruefe_lizenz(name)["controlnet"]
        if cn["noetig"] and not cn["benannt"]:
            assert cn["zulaessig"] is None, name
            assert any("UNVOLLSTÄNDIG" in a for a in cn["auflagen"]), name


def test_der_empfohlene_kandidat_ist_beidseitig_permissiv():
    """`z-image-turbo` — der einzige Kandidat, bei dem beide Hälften Apache-2.0 sind."""
    urteil = pruefe_lizenz("z-image-turbo")
    cn = urteil["controlnet"]
    assert urteil["zulaessig"] is True
    assert cn["benannt"] is True
    assert cn["lizenz"] == "Apache-2.0"
    assert cn["zulaessig"] is True
    assert cn["lizenz_belegt"] is True


def test_flux_ist_beidseitig_zu_und_sagt_es_auch():
    """Der Fall, der das Loch in Regel 1 sichtbar macht.

    Bei FLUX sind die verbreiteten Depth-ControlNets **selbst** nicht-kommerziell. Ein
    permissives FLUX-Basismodell hätte hier „zulässig" ergeben, und die fertige Kette
    wäre trotzdem unverkäuflich gewesen.
    """
    urteil = pruefe_lizenz("flux1-dev")
    assert urteil["zulaessig"] is False
    assert urteil["controlnet"]["zulaessig"] is False
    assert "BEIDSEITIG" in urteil["begruendung"]


def test_der_aeltere_ausschlussgrund_wird_nicht_verdeckt():
    """Zwei Gründe sind zwei Gründe — der zweite darf den ersten nicht überschreiben.

    ``flux1-dev`` ist schon wegen des Basismodells ausgeschlossen. Verdeckte die
    ControlNet-Begründung diese, ginge der Satz über die abgeleiteten LoRAs verloren —
    und genau der schlägt beim Stil-Training zu.
    """
    begruendung = pruefe_lizenz("flux1-dev")["begruendung"]
    assert "LoRA" in begruendung
    assert "HINZU KOMMT" in begruendung


def test_sd35_nennt_die_beiden_nachgetragenen_auflagen():
    """Zwei Auflagen der Community License, die bis zum 18.08.2026 nirgends standen.

    Beide sind für dieses Projekt unmittelbar einschlägig — die zweite verbietet genau
    das, was ein LoRA auf selbst erzeugten Bildern täte.
    """
    auflagen = " ".join(pruefe_lizenz("sd35-large")["auflagen"])
    assert "Powered by Stability AI" in auflagen
    assert "Basismodelle" in auflagen


def test_ein_controlnet_an_einem_edit_modell_ist_ein_widerspruch():
    """Ein integriertes Edit-Modell braucht kein zweites Repo — steht dort eines, stimmt was nicht."""
    import dataclasses
    edit = dataclasses.replace(BACKBONES["qwen-image-edit-2511"],
                               controlnet_id="irgendwer/irgendwas")
    from aiimaging.backbone import _pruefe_controlnet
    cn = _pruefe_controlnet(edit)
    assert any("Widerspruch" in a for a in cn["auflagen"])


def test_die_vram_zahl_ist_die_groessere_der_beiden_messungen():
    """Zwei Messungen an derselben Karte, 9,7 % auseinander — und die Richtung zählt.

    `auf-20260818-13` mass **23,4 GiB** (bfloat16, ControlNet über den Ordnerweg),
    `auf-20260909-92` am 08.09.2026 **25,1 GiB** (diffusers 0.39.0, ControlNet über
    `from_single_file`, 512 × 512). Beide sind richtig; sie gelten für verschiedene
    Bedingungen.

    Im Register steht die **grössere**, weil dieses Feld eine einzige Frage beantwortet:
    *Passt es auf die Karte?* Eine zu kleine Zahl lässt `waehle(max_vram_gb=24)` das
    Modell durchgehen, und der Lauf stirbt am Speicher. Eine zu grosse verweigert nur
    einen Lauf, der vielleicht ginge. **Von den beiden Irrtümern ist der zweite der
    billigere** — und dieser Test hält fest, dass die Wahl bewusst so fiel.
    """
    z = hole("z-image-turbo")
    assert z.vram_gb == pytest.approx(25.1), (
        "die kleinere der beiden Messungen wäre die gefährlichere Zahl"
    )
    assert z.name not in {b.name for b in waehle(max_vram_gb=24.0)}, (
        "mit 25,1 GiB darf eine 24-GB-Schranke dieses Modell nicht mehr durchlassen"
    )
    assert z.name in {b.name for b in waehle(max_vram_gb=26.0)}, (
        "und eine Schranke oberhalb der Messung muss es weiterhin zulassen"
    )


# --------------------------------------------------------------------------------------
# 6 · Die Lizenz hängt an der GRÖSSE, nicht am Namen
#
# Zwei Funde der Kartierung vom 18.09.2026, und beide schlagen erst beim LADEN zu — also
# auf der Maschine der Nutzerin und nicht bei uns, wo die Registry blosse Daten ist:
#
#   1  `flux2-klein-4b` trug die Kennung "black-forest-labs/FLUX.2-klein". Die gibt es
#      nicht (401); die Gewichte liegen unter ".../FLUX.2-klein-4B".
#   2  Der Lizenzriegel las den Namen. Bei FLUX.2-klein entscheidet aber die Grösse:
#      4B ist Apache-2.0, 9B ist Non-Commercial. Ein Namensvergleich hält die eine für
#      die andere — und das ist ein Loch in Regel 1, also in der Grundlage der ganzen
#      Open-Source-Auslieferung.
# --------------------------------------------------------------------------------------

@contextlib.contextmanager
def _vorruebergehend(eintrag):
    """Legt einen erfundenen Eintrag direkt in die Registry und räumt ihn wieder weg.

    **Absichtlich an ``_eintrag`` vorbei.** Der Riegel soll auch dann halten, wenn ein
    Eintrag nicht durch die Eingangsprüfung gekommen ist — sonst wäre er genau einmal
    wirksam, nämlich beim Import, und jede spätere Änderung an ``BACKBONES`` liefe an
    ihm vorbei. Dass ``_eintrag`` denselben Fall schon früher abfängt, prüft ein eigener
    Test weiter unten; hier geht es um den Weg daran vorbei.
    """
    BACKBONES[eintrag.name] = eintrag
    try:
        yield eintrag
    finally:
        BACKBONES.pop(eintrag.name, None)


def _klein(name, *, parameter_b, lizenz, kommerziell, modell_id=None):
    """Ein erfundener FLUX.2-klein-Eintrag — die Bausteine der Proben hier unten."""
    return Backbone(
        name=name,
        modell_id=modell_id or f"black-forest-labs/FLUX.2-klein-{parameter_b:g}B",
        parameter_b=parameter_b,
        lizenz=lizenz,
        kommerziell_nutzbar=kommerziell,
        konditionierung=KOND_INTEGRIERTES_EDIT,
        vram_gb=parameter_b * 2.4,
        dateien=("model_index.json",),
        lizenz_quelle=QUELLE_MODELLKARTE,
    )


def test_die_kennung_der_4b_fassung_zeigt_auf_ein_repo_das_es_gibt():
    """Fund 1: Die eingetragene Kennung existierte nicht — und das fiel erst beim Laden auf.

    "black-forest-labs/FLUX.2-klein" liefert 401, weil ein nicht existierendes Repo von
    einem gesperrten nicht zu unterscheiden ist. Die Fehlermeldung zeigt damit in die
    falsche Richtung: Sie liest sich wie ein Zugangsproblem und ist ein Tippfehler.

    Hier bleibt es still — die Registry lädt nichts. Genau deshalb braucht dieser
    Buchstabe eine Probe.
    """
    b = hole("flux2-klein-4b")
    assert b.modell_id == "black-forest-labs/FLUX.2-klein-4B"
    assert b.modell_id.endswith("-4B"), "die Grösse gehört in die Kennung"
    for eintrag in BACKBONES.values():
        assert eintrag.modell_id != "black-forest-labs/FLUX.2-klein", (
            "die Kennung ohne Grössenangabe existiert auf Hugging Face nicht"
        )


def test_die_9b_fassung_wird_abgewiesen_obwohl_ihr_name_dem_zugelassenen_gleicht():
    """Fund 2, der Kern: ein ehrlich deklarierter 9B-Eintrag darf nicht in die Auswahl.

    Der Name ähnelt dem zugelassenen bis auf zwei Zeichen. Genau darauf hat der alte
    Riegel geschaut.
    """
    neun = _klein("flux2-klein-9b", parameter_b=9.0,
                  lizenz="FLUX.2 [klein] Non-Commercial License", kommerziell=False)
    with _vorruebergehend(neun):
        urteil = pruefe_lizenz("flux2-klein-9b")
        assert urteil["zulaessig"] is False
        assert "flux2-klein-9b" not in {b.name for b in waehle(kommerziell=True)}


def test_der_riegel_haengt_an_der_groesse_und_nicht_am_lizenzfeld():
    """Der schwerere Fall — und der wahrscheinlichere.

    Ein neuer Eintrag entsteht durch Abschreiben des benachbarten. Wer ``flux2-klein-9b``
    aus ``flux2-klein-4b`` kopiert, erbt dabei ``lizenz="Apache-2.0"`` und
    ``kommerziell_nutzbar=True``. Der Datensatz behauptet dann etwas Falsches — und eine
    Prüfung, die allein den Datensatz liest, bestätigt es.

    Der Riegel muss hier gegen die eigenen Felder des Eintrags entscheiden. Tut er das
    nicht, ist er eine Beschriftung und kein Riegel.
    """
    getarnt = _klein("flux2-klein-9b", parameter_b=9.0,
                     lizenz="Apache-2.0", kommerziell=True)

    riegel = groessen_riegel(getarnt)
    assert riegel["zulaessig"] is False
    assert riegel["grund"] == "bekannt_nicht_kommerziell"
    assert "Non-Commercial" in riegel["erwartete_lizenz"]

    with _vorruebergehend(getarnt):
        urteil = pruefe_lizenz("flux2-klein-9b")
        assert urteil["zulaessig"] is False, (
            "ein permissives Lizenzfeld darf die Grösse nicht überstimmen"
        )
        assert "GRÖSSE" in urteil["begruendung"]
        assert "flux2-klein-9b" not in {b.name for b in waehle(kommerziell=True)}, (
            "und die Auswahl darf es ebenso wenig durchlassen wie die Prüfung"
        )


def test_ein_ausschlussgrund_darf_vom_widerspruch_nicht_geloescht_werden():
    """BEFUND 18.09.2026: Das Urteil war richtig — und der Satz daneben sagte das Gegenteil.

    Der Widerspruchszweig in :func:`pruefe_lizenz` ersetzte die Begruendung
    BEDINGUNGSLOS, begruendet mit «Der Ausgang bleibt `zulaessig=True` — die Groesse ist
    ja freigegeben». Diese Praemisse ist falsch: Die Lizenzpruefung laeuft zuerst, und
    `zulaessig` kann dort laengst `False` geworden sein.

    Nachgestellt mit einem 4B-Eintrag (Groesse freigegeben), dessen Lizenzfeld auf
    nicht-kommerziell steht::

        zulaessig     False                                  richtig
        begruendung   «Die Groesse ist unter Regel 1 freigegeben, aber …»
        verschwunden  «erlaubt keine kommerzielle Nutzung»,
                      «Unter Regel 1 AUSGESCHLOSSEN», der Satz ueber LoRAs

    Wer nur die Begruendung liest — und das tut jede Fehlermeldung, die sie durchreicht —
    las einen Etikettenstreit, wo ein Lizenzausschluss stand. **Ein Fehlschlag, der wie
    ein Erfolg aussieht, wird nicht gefunden, er wird geglaubt.**
    """
    boes = _klein("probe-4b-nc", parameter_b=4.0,
                  lizenz="FLUX.2 [klein] Non-Commercial License", kommerziell=False)

    with _vorruebergehend(boes):
        urteil = pruefe_lizenz("probe-4b-nc")

    assert urteil["zulaessig"] is False
    for stueck in ("AUSGESCHLOSSEN", "kommerzielle Nutzung", "LoRA"):
        assert stueck in urteil["begruendung"], (
            f"der Ausschlussgrund ist aus der Begruendung verschwunden: {stueck!r} fehlt"
        )
    assert "WIDERSPRUCH" in urteil["begruendung"], \
        "und der zweite Grund muss daneben stehen — zwei Gruende sind zwei Gruende"


def test_bestehende_auflagen_ueberleben_den_widerspruch():
    """Derselbe Fund eine Ebene tiefer, und hier bleibt das Urteil sogar `True`.

    Traegt die alte Begruendung ihre Auflagen bereits mit, ist sie nicht widerlegt,
    sondern unvollstaendig — Ersetzen waere Loeschen. Nachgestellt an einem 4B-Eintrag
    auf 'Stability AI Community License': Umsatzschwelle, Nennungspflicht und
    Trainingsverbot fielen aus der Begruendung heraus und standen danach nur noch in
    `auflagen`.

    Die Unterscheidung ist darum nicht `zulaessig`, sondern ob der alte Satz
    Bedingungslosigkeit behauptet hat.
    """
    stability = _klein("probe-4b-stab", parameter_b=4.0,
                       lizenz="Stability AI Community License", kommerziell=True)

    with _vorruebergehend(stability):
        urteil = pruefe_lizenz("probe-4b-stab")

    assert urteil["zulaessig"] is True, "die Groesse ist freigegeben, strittig ist der Name"
    for stueck in ("Mio USD", "Powered by Stability AI", "trainieren"):
        assert stueck in urteil["begruendung"], (
            f"eine bestehende Auflage ist aus der Begruendung verschwunden: {stueck!r}"
        )
    assert "WIDERSPRUCH" in urteil["begruendung"]


def test_ohne_bestehende_auflagen_wird_die_begruendung_ersetzt_und_nicht_ergaenzt():
    """Die Gegenprobe zu den beiden oben — sonst waere «immer ergaenzen» auch gruen.

    Behauptet der alte Satz Bedingungslosigkeit, ist er durch den Widerspruch widerlegt.
    Eine widerlegte Behauptung mit einem «aber» stehen zu lassen, heisst sie stehen zu
    lassen. Genau dieser Satz darf danach NICHT mehr dastehen.
    """
    sauber = _klein("probe-4b-apache", parameter_b=4.0,
                    lizenz="MIT", kommerziell=True)

    with _vorruebergehend(sauber):
        urteil = pruefe_lizenz("probe-4b-apache")

    assert "OHNE WEITERE AUFLAGE" not in urteil["begruendung"], (
        "der widerlegte Satz steht noch da — dann bestreitet wieder ein Satz den anderen"
    )
    assert "HINZU KOMMT" not in urteil["begruendung"], \
        "hier war nichts zu ergaenzen, sondern etwas zu ersetzen"


def test_die_4b_fassung_geht_weiter_durch():
    """Die Gegenprobe. Ein Riegel, der alles sperrt, bewacht nichts.

    Ohne diesen Test wäre der obige auch dann grün, wenn der Riegel die ganze Familie
    ausschlösse — und dann hätte er die eine Fassung mitgenommen, auf der die
    Laptop-Tauglichkeit dieser Arbeit beruht.
    """
    vier = hole("flux2-klein-4b")
    riegel = groessen_riegel(vier)
    assert riegel["zulaessig"] is True
    assert riegel["grund"] == "freigegebene_groesse"
    assert riegel["erwartete_lizenz"] == "Apache-2.0"
    assert riegel["auflagen"] == (), "Tabelle und Eintrag sagen dasselbe"

    assert pruefe_lizenz("flux2-klein-4b")["zulaessig"] is True
    assert "flux2-klein-4b" in {b.name for b in waehle(kommerziell=True)}


@pytest.mark.parametrize("name, modell_id", [
    # Der Name verrät die Familie, die Kennung ist harmlos …
    ("flux2-klein-9b", "irgendwer/ein-ganz-anderes-repo"),
    # … und umgekehrt. Fund 1 dieser Sitzung war eine falsche Kennung bei richtigem
    # Namen; der umgekehrte Fall ist genauso möglich, und ein Riegel, der nur eine der
    # beiden Spuren liest, ist durch Ändern der anderen zu umgehen.
    ("kleines-modell", "black-forest-labs/FLUX.2-klein-9B"),
])
def test_die_familie_wird_an_beiden_spuren_erkannt(name, modell_id):
    """Umbenennen darf den Riegel nicht aushebeln — weder der Name noch die Kennung."""
    getarnt = _klein(name, parameter_b=9.0, lizenz="Apache-2.0", kommerziell=True,
                     modell_id=modell_id)
    assert groessen_riegel(getarnt)["zulaessig"] is False


def test_eine_unbekannte_groesse_faellt_zu_und_sagt_dass_sie_ungeprueft_ist():
    """FAIL-CLOSED — und die dritte Antwort bleibt trotzdem lesbar.

    Erscheint morgen eine 6B-Fassung, weiss niemand ihre Lizenz. Sie wird abgewiesen,
    nicht durchgewunken. Aber ``grund`` hält den Unterschied fest: ``9B`` ist
    nachgesehen und ausgeschlossen, ``6B`` ist schlicht nicht nachgesehen. Beide Male
    schliesst dasselbe Tor — die Gründe sind verschieden, und wer nachträgt, muss
    wissen, welcher vorliegt.
    """
    sechs = _klein("flux2-klein-6b", parameter_b=6.0,
                   lizenz="Apache-2.0", kommerziell=True)
    riegel = groessen_riegel(sechs)
    assert riegel["zulaessig"] is False
    assert riegel["grund"] == "nicht_freigegebene_groesse"
    assert riegel["erwartete_lizenz"] is None, "nicht gemessen heisst nicht gemessen"
    assert any("NICHT geprüft" in a for a in riegel["auflagen"])

    neun = _klein("flux2-klein-9b", parameter_b=9.0,
                  lizenz="Apache-2.0", kommerziell=True)
    assert groessen_riegel(neun)["grund"] != riegel["grund"], (
        "durchgefallen und nicht gemessen dürfen nicht dasselbe Wort tragen"
    )


@pytest.mark.parametrize("name", ["z-image-turbo", "sdxl-juggernaut", "flux1-dev"])
def test_der_riegel_schweigt_zu_familien_die_er_nicht_kennt(name):
    """``None`` heisst „andere Frage" — nicht „in Ordnung" und nicht „durchgefallen".

    Der Riegel beantwortet genau eine Frage: hängt die Lizenz dieser Familie an der
    Grösse? Für die meisten Einträge lautet die Antwort „gilt hier nicht". Gäbe er dort
    ``True`` zurück, sähe ein ungeprüfter Eintrag wie ein freigegebener aus — und
    ``flux1-dev`` bliebe trotzdem ausgeschlossen, nur eben aus einem anderen Grund.
    """
    riegel = groessen_riegel(hole(name))
    assert riegel["zulaessig"] is None
    assert riegel["greift"] is False
    assert riegel["grund"] == "keine_groessengebundene_familie"

    # Und die Lizenzprüfung urteilt davon unberührt weiter.
    assert pruefe_lizenz(name)["zulaessig"] is (name != "flux1-dev")


def test_ein_widerspruechlicher_eintrag_kommt_gar_nicht_erst_in_die_registry():
    """Der früheste der drei Standorte: beim Import, also bei uns statt bei der Nutzerin.

    ``_eintrag`` weist den Widerspruch ab — nicht den Ausschluss. Ein ehrlich als
    nicht-kommerziell deklarierter Eintrag darf in der Registry stehen, genau wie
    ``flux1-dev``: Ein ausgeschlossenes Modell, das gar nicht erst auftaucht, kann auch
    nicht als ausgeschlossen gemeldet werden.
    """
    getarnt = _klein("flux2-klein-9b-getarnt", parameter_b=9.0,
                     lizenz="Apache-2.0", kommerziell=True)
    with pytest.raises(BackboneError, match="GRÖSSE"):
        backbone_modul._eintrag(getarnt)
    assert "flux2-klein-9b-getarnt" not in BACKBONES

    ehrlich = _klein("flux2-klein-9b-ehrlich", parameter_b=9.0,
                     lizenz="FLUX.2 [klein] Non-Commercial License", kommerziell=False)
    try:
        backbone_modul._eintrag(ehrlich)
        assert "flux2-klein-9b-ehrlich" in BACKBONES
        assert pruefe_lizenz("flux2-klein-9b-ehrlich")["zulaessig"] is False
    finally:
        BACKBONES.pop("flux2-klein-9b-ehrlich", None)


def test_die_tabelle_ist_die_quelle_und_nicht_das_lizenzfeld():
    """Auch auf der freigegebenen Grösse gewinnt die Tabelle — und sagt es laut.

    Trägt jemand für 4B eine andere Lizenz ein als die geprüfte, ist einer von beiden
    veraltet. Weil die Tabelle die Quelle ist, ist es der Eintrag; der Widerspruch wird
    gemeldet statt still übernommen.
    """
    schief = _klein("flux2-klein-4b-schief", parameter_b=4.0,
                    lizenz="MIT", kommerziell=True)
    riegel = groessen_riegel(schief)
    assert riegel["zulaessig"] is True
    assert any("WIDERSPRUCH" in a for a in riegel["auflagen"])
    with pytest.raises(BackboneError, match="WIDERSPRUCH"):
        backbone_modul._eintrag(schief)


def test_die_groessengebundene_tabelle_ist_nicht_leer():
    """Ohne Eintrag in der Tabelle wäre jeder Test dieses Abschnitts vakuös.

    Ein Riegel, der nichts kennt, lässt alles durch und bleibt dabei grün.
    """
    assert "FLUX.2-klein" in GROESSENGEBUNDENE_FAMILIEN
    familie = GROESSENGEBUNDENE_FAMILIEN["FLUX.2-klein"]
    assert 4.0 in familie["freie_groessen_b"]
    assert 9.0 in familie["gesperrte_groessen_b"]
    assert "Non-Commercial" in familie["gesperrte_groessen_b"][9.0]


# --------------------------------------------------------------------------------------
# 7 · Gegenprüfung 18.09.2026 — der Riegel traute einem Feld, das genauso kopiert wird
#
# Der Riegel aus Abschnitt 6 nimmt dem Feld ``lizenz`` das Vertrauen und gibt es dem Feld
# ``parameter_b``. Beide stehen in derselben Zeile derselben Registry und werden von Hand
# gepflegt. Gemessen: Ein Eintrag, dessen Name UND Kennung „-9B" sagen, dessen
# ``parameter_b`` aber 4.0 führt, kam durch alle drei Standorte — Riegel, Prüfung,
# Auswahl — und liess sich ausserdem eintragen.
#
# Und es ist der wahrscheinlichere Kopierfehler: Der Name MUSS geändert werden, sonst
# entsteht kein zweiter Eintrag (der Schlüssel kollidiert). Die Zahl darunter muss nicht.
# --------------------------------------------------------------------------------------

def test_der_riegel_glaubt_auch_dem_feld_parameter_b_nicht_allein():
    """Name und Kennung sagen 9B, ``parameter_b`` sagt 4.0 — das darf nicht durchgehen.

    Welche der beiden Angaben stimmt, ist von der Registry aus nicht entscheidbar. Ein
    fail-closed Riegel entscheidet sich dann nicht für die freundlichere Lesart.
    """
    verrutscht = _klein("flux2-klein-9b", parameter_b=4.0,
                        lizenz="Apache-2.0", kommerziell=True,
                        modell_id="black-forest-labs/FLUX.2-klein-9B")

    riegel = groessen_riegel(verrutscht)
    assert riegel["zulaessig"] is False, (
        "die Bezeichner nennen 9B — parameter_b=4.0 allein darf das nicht aufwiegen"
    )
    assert riegel["grund"] == "groessenangabe_widerspruechlich"
    assert riegel["erwartete_lizenz"] is None, "welche Grösse gilt, ist nicht gemessen"
    assert any("WIDERSPRUCH IN DER GRÖSSE" in a for a in riegel["auflagen"])

    with _vorruebergehend(verrutscht):
        assert pruefe_lizenz("flux2-klein-9b")["zulaessig"] is False
        assert "flux2-klein-9b" not in {b.name for b in waehle(kommerziell=True)}

    with pytest.raises(BackboneError, match="WIDERSPRUCH IN DER GRÖSSE"):
        backbone_modul._eintrag(verrutscht)
    assert "flux2-klein-9b" not in BACKBONES


@pytest.mark.parametrize("name, modell_id, parameter_b", [
    # Nur der NAME widerspricht — die Kennung schweigt zur Grösse.
    ("flux2-klein-9b", "black-forest-labs/FLUX.2-klein", 4.0),
    # Nur die KENNUNG widerspricht — der Name schweigt zur Grösse. Ohne diesen Fall
    # bliebe die Probe grün, wenn die Gegenprüfung die Kennung gar nicht läse
    # (nachgefahren als Mutationsprobe, 18.09.2026: sie war es).
    ("flux2-klein", "black-forest-labs/FLUX.2-klein-9B", 4.0),
])
def test_der_widerspruch_wird_auf_beiden_spuren_gesehen(name, modell_id, parameter_b):
    """Eine Spur genügt. Wer nur eine der beiden liest, übersieht die Hälfte der Fälle.

    Dieselbe Begründung wie bei der Familienerkennung: Name und Kennung sind zwei von
    Hand gepflegte Angaben, und Fund 1 derselben Kartierung war eine falsche Kennung bei
    richtigem Namen.
    """
    verrutscht = _klein(name, parameter_b=parameter_b, lizenz="Apache-2.0",
                        kommerziell=True, modell_id=modell_id)
    riegel = groessen_riegel(verrutscht)
    assert riegel["zulaessig"] is False
    assert riegel["grund"] == "groessenangabe_widerspruechlich"


def test_der_widerspruch_gilt_in_beide_richtungen():
    """Auch der umgekehrte Verrutscher — Bezeichner 4B, ``parameter_b`` 9.0 — fällt.

    Hier wäre das Urteil zufällig ohnehin „nein", aber aus dem falschen Grund. Der
    Unterschied zählt: ``bekannt_nicht_kommerziell`` hiesse, jemand habe die 9B-Lizenz
    nachgesehen. Nachgesehen hat niemand — der Eintrag widerspricht sich.
    """
    verrutscht = _klein("flux2-klein-4b-kopie", parameter_b=9.0,
                        lizenz="Apache-2.0", kommerziell=True,
                        modell_id="black-forest-labs/FLUX.2-klein-4B")
    riegel = groessen_riegel(verrutscht)
    assert riegel["zulaessig"] is False
    assert riegel["grund"] == "groessenangabe_widerspruechlich"


def test_bezeichner_ohne_groessenangabe_sind_keine_bestaetigung():
    """Leere Menge heisst nicht gemessen — und darf weder freisprechen noch verurteilen.

    Sagen die Bezeichner nichts über die Grösse, bleibt ``parameter_b`` die einzige
    Angabe. Dann urteilt der Riegel wie zuvor, nicht strenger und nicht milder.
    """
    assert backbone_modul._groessen_behauptungen(("flux2-klein", "irgendwer/flux2-klein")) == set()

    stumm = _klein("flux2-klein", parameter_b=4.0, lizenz="Apache-2.0", kommerziell=True,
                   modell_id="black-forest-labs/FLUX.2-klein")
    assert groessen_riegel(stumm)["grund"] == "freigegebene_groesse"

    stumm_neun = _klein("flux2-klein", parameter_b=9.0, lizenz="Apache-2.0",
                        kommerziell=True, modell_id="black-forest-labs/FLUX.2-klein")
    assert groessen_riegel(stumm_neun)["grund"] == "bekannt_nicht_kommerziell"


def test_das_urteil_sagt_ob_die_bezeichner_die_groesse_decken():
    """BEFUND 18.09.2026: «nicht gemessen» und «doppelt belegt» ergaben DASSELBE Urteil.

    Zwei 4B-Eintraege — einer mit der Groesse in Name und Kennung, einer mit
    schweigenden Bezeichnern — lieferten byteweise identische dicts. Wer den zweiten las,
    konnte nicht erkennen, dass allein `parameter_b` geurteilt hatte: genau das Feld, dem
    dieser Riegel nicht allein glauben soll.

    Der Ausgang bleibt gleich, und das ist richtig — ein Eintrag ohne Groesse im Namen
    ist nicht unzulaessig. Unterscheidbar muss er trotzdem sein.
    """
    belegt = _klein("flux2-klein-4b-x", parameter_b=4.0, lizenz="Apache-2.0",
                    kommerziell=True, modell_id="black-forest-labs/FLUX.2-klein-4B")
    stumm = _klein("flux2-klein-neu", parameter_b=4.0, lizenz="Apache-2.0",
                   kommerziell=True, modell_id="black-forest-labs/FLUX.2-klein")

    a, b = groessen_riegel(belegt), groessen_riegel(stumm)

    assert a != b, "zwei verschiedene Lagen duerfen nicht dasselbe Urteil ergeben"
    assert a["zulaessig"] is b["zulaessig"] is True, "am Ausgang aendert sich nichts"

    assert a["bestaetigt_durch"] == ("name", "modell_id")
    assert b["bestaetigt_durch"] == (), "gefragt, und kein Bezeichner deckt die Groesse"
    assert any("NUR EINE SPUR" in auf for auf in b["auflagen"]), \
        "der Vorbehalt gehoert dorthin, wo gelesen wird"
    assert not any("NUR EINE SPUR" in auf for auf in a["auflagen"])


def test_ohne_groessengebundene_familie_wurde_gar_nicht_erst_gefragt():
    """Die dritte Antwort, angewandt auf das neue Feld: `None` ist nicht `()`.

    `()` heisst «gefragt, und kein Bezeichner deckt die Groesse». `None` heisst «nicht
    gefragt» — der Riegel greift hier gar nicht. Die beiden zu verschmelzen hiesse, einen
    Vorbehalt zu melden, wo es nichts vorzubehalten gibt.
    """
    fremd = _klein("etwas-anderes", parameter_b=4.0, lizenz="Apache-2.0",
                   kommerziell=True, modell_id="jemand/etwas-anderes")
    urteil = groessen_riegel(fremd)

    assert urteil["greift"] is False
    assert urteil["zulaessig"] is None
    assert urteil["bestaetigt_durch"] is None, "nicht gefragt ist nicht dasselbe wie leer"


def test_die_groessenangabe_wird_gelesen_und_nicht_erraten():
    """Was als Grössenangabe zählt — und was ausdrücklich nicht.

    ``flux2`` trägt eine Ziffer und ist keine Grösse; ``labs`` trägt ein ``b`` und ist
    keine. Ein zu gieriges Muster machte den Riegel unbrauchbar, weil dann jeder echte
    Eintrag sich selbst widerspräche.
    """
    lies = backbone_modul._groessen_behauptungen
    assert lies(("flux2-klein-9b",)) == {9.0}
    assert lies(("black-forest-labs/flux.2-klein-4b",)) == {4.0}
    assert lies(("flux2-klein-4b", "black-forest-labs/flux.2-klein-4b")) == {4.0}
    assert lies(("black-forest-labs/flux.2-klein",)) == set(), "labs ist keine Grösse"
    assert lies(("sdxl-juggernaut",)) == set()


def test_der_echte_eintrag_widerspricht_sich_nicht():
    """Die Gegenprobe zur ganzen Gegenprüfung: Der Riegel darf 4B nicht mitreissen.

    Ein Widerspruchsriegel, der den einzigen echten Eintrag der Familie abweist, hätte
    die Fassung genommen, auf der die Laptop-Tauglichkeit dieser Arbeit beruht.
    """
    vier = hole("flux2-klein-4b")
    assert backbone_modul._groessen_behauptungen(
        (vier.name.lower(), vier.modell_id.lower())) == {4.0}
    assert groessen_riegel(vier)["zulaessig"] is True
    assert pruefe_lizenz("flux2-klein-4b")["zulaessig"] is True
    assert "flux2-klein-4b" in {b.name for b in waehle(kommerziell=True)}


def test_am_rand_der_toleranz_wird_geschlossen_und_nicht_geoeffnet():
    """Bei genau 4.5 ist „das ist die 4B-Fassung" eine Behauptung, keine Ablesung.

    GEMESSEN: Der vorherige Stand verglich die Freiliste mit ``<=`` und gab bei 4.5
    ``freigegebene_groesse`` zurück. Ein fail-closed Riegel öffnet am Rand nicht.
    """
    rand = _klein("flux2-klein-rand", parameter_b=4.0 + backbone_modul.GROESSEN_TOLERANZ_B,
                  lizenz="Apache-2.0", kommerziell=True,
                  modell_id="black-forest-labs/FLUX.2-klein")
    riegel = groessen_riegel(rand)
    assert riegel["zulaessig"] is False
    assert riegel["grund"] == "nicht_freigegebene_groesse"

    # Knapp innerhalb bleibt frei — sonst wäre der Riegel bloss strenger geworden.
    drin = _klein("flux2-klein-drin", parameter_b=4.03,
                  lizenz="Apache-2.0", kommerziell=True,
                  modell_id="black-forest-labs/FLUX.2-klein")
    assert groessen_riegel(drin)["zulaessig"] is True


def test_die_begruendung_verschweigt_den_widerspruch_nicht():
    """Ein Satz darf den anderen nicht bestreiten.

    GEMESSEN: Bei einem 4B-Eintrag mit abweichendem Lizenzfeld stand der WIDERSPRUCH in
    ``auflagen``, während ``begruendung`` wörtlich „ohne weitere Auflage mit Regel 1
    vereinbar" sagte. Wer nur die Begründung liest — und das tut jede Fehlermeldung, die
    sie durchreicht —, erfuhr davon nichts.
    """
    schief = _klein("flux2-klein-4b-schief-lizenz", parameter_b=4.0,
                    lizenz="MIT", kommerziell=True,
                    modell_id="black-forest-labs/FLUX.2-klein-4B")
    with _vorruebergehend(schief):
        urteil = pruefe_lizenz("flux2-klein-4b-schief-lizenz")
        assert urteil["zulaessig"] is True, "4B bleibt zulässig — die Grösse stimmt ja"
        assert any("WIDERSPRUCH" in a for a in urteil["auflagen"])
        assert "WIDERSPRUCH" in urteil["begruendung"], (
            "die Begründung muss den Widerspruch mittragen, nicht nur die Auflagen"
        )
        assert "ohne weitere Auflage" not in urteil["begruendung"]


def test_die_modell_id_treibt_keinen_ladevorgang():
    """Die Zusage des Kommentars an der 4B-Kennung, nachgeprüft statt geglaubt.

    Der Kommentar dort sagt, wo die falsche Kennung aufschlägt und wo nicht: Kein Pfad
    dieser Software lädt über ``modell_id``; das Verzeichnis kommt aus ``name``. Diese
    Probe hält das fest, damit der Kommentar nicht stillschweigend unwahr wird — träte
    einmal ein Ladeweg über die Kennung hinzu, wäre die Kennung plötzlich laufgefährlich
    und nicht mehr bloss eine Angabe für Menschen.

    **BERICHTIGT 18.09.2026 — der Wächter fiel nicht, wo er fallen sollte.** Er suchte
    ``modell_id`` nur in den ARGUMENTEN eines Aufrufs. Gemessen an zwei Mutationen::

        return str(b.modell_id)              → Probe faellt   (gut)
        kennung = b.modell_id; str(kennung)  → Probe bleibt gruen

    Die zweite Form ist die, in der ein echter Ladeweg geschrieben wuerde. *Ein Waechter,
    der nicht faellt, bewacht nichts.*

    Gesucht wird darum jeder Zugriff auf das Feld — **ausser als Wert in einem
    Woerterbuch.** Das ist der Laufzettel (`render.py:1517`), und dort wird die Kennung
    aufgeschrieben, nicht befolgt. Ein Waechter, der auch sie meldet, faellt beim ersten
    Lauf und wird dann aufgeweicht statt geschaerft.
    """
    quelle = (Path(__file__).resolve().parents[1] / "src" / "aiimaging" / "render.py"
              ).read_text(encoding="utf-8")
    baum = ast.parse(quelle)
    # Erlaubt ist GENAU EINE Verwendung: als Wert in einem Wörterbuch. Das ist der
    # Laufzettel — dort wird die Kennung aufgeschrieben, nicht befolgt. Jede andere
    # Stelle (Zuweisung, Aufrufargument, Pfadrechnung, f-String) ist ein Fund.
    aufgeschrieben = {id(wert) for knoten in ast.walk(baum)
                      if isinstance(knoten, ast.Dict) for wert in knoten.values}
    treffer = [knoten.lineno for knoten in ast.walk(baum)
               if isinstance(knoten, ast.Attribute) and knoten.attr == "modell_id"
               and id(knoten) not in aufgeschrieben]
    assert not treffer, (
        f"render.py verwendet `modell_id` ausserhalb des Laufzettels (Zeile(n) "
        f"{treffer}) — der Kommentar an der 4B-Kennung behauptet, es gebe keinen "
        f"Ladeweg über die Kennung. Einer von beiden muss nachgezogen werden."
    )
