"""A0062 · FLUX 3 Image Klein als Forschungsmodell — die drei Proben (a), (b), (c).

Owner 31.10.2026: «wir nehmens mal auf und testen». Ein **Test als Forschungsmodell** nach der
Präzisierung Forschungsmodelle (CLAUDE.md, Regel 1, Owner-Entscheid 29.09.2026, vier Auflagen),
**keine** Produktfreigabe. Dazu der Grundsatz «Immer vom Render» (Masstreue, 31.10.2026).

Die Proben gelten nicht nur für FLUX 3, sondern für **jeden** Registereintrag mit
``nur_forschung`` — ein zweites Forschungsmodell soll dieselben Sperren erben, ohne dass jemand
daran denken muss. Damit sie nicht leer durchlaufen, verlangt die erste Probe, dass es
mindestens einen solchen Eintrag gibt (heute ``flux3-image-klein``).

(a) Ohne ``AIIMAGING_FORSCHUNGSMODELLE=1`` wird das Modell nicht geladen.
(b) Über den Bestellweg der Brücke (KosmoVis/KosmoOrbit) ist es nicht wählbar — auch dann
    nicht, wenn der Schalter am Rechner der Brücke gesetzt wäre.
(c) Ein Lauf ohne Beauty-Render (Cycles-Bild derselben Kamera) wird abgewiesen.

Kein Test lädt Gewichte oder braucht eine GPU.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from aiimaging import backbone, knotenweg, kosmo_szene, render

WURZEL = Path(__file__).resolve().parents[1]
FLUX3 = "flux3-image-klein"
SCHALTER = backbone.FORSCHUNG_SCHALTER


def _forschungsmodelle() -> list[str]:
    return sorted(n for n, e in backbone.BACKBONES.items() if e.nur_forschung)


@pytest.fixture
def ohne_schalter(monkeypatch):
    monkeypatch.delenv(SCHALTER, raising=False)


@pytest.fixture
def mit_schalter(monkeypatch):
    monkeypatch.setenv(SCHALTER, "1")


# --------------------------------------------------------------------------------------
# Der Eintrag selbst
# --------------------------------------------------------------------------------------

def test_flux3_steht_als_forschungsmodell_im_register():
    """Eingetragen, nicht verkaufbar, mit Begründung — und damit nicht leer für die Proben."""
    assert FLUX3 in _forschungsmodelle()
    e = backbone.hole(FLUX3)
    assert e.modell_id == "black-forest-labs/flux-3-image-klein"
    assert e.kommerziell_nutzbar is False
    assert e.lizenz_offen is None
    assert "A0062" in e.nur_forschung and "31.10.2026" in e.nur_forschung
    assert backbone.pruefe_lizenz(FLUX3)["zulaessig"] is False  # «nicht im Produkt»


@pytest.mark.parametrize("name", _forschungsmodelle() or ["(keines)"])
def test_ein_forschungsmodell_ist_nie_vorgabe_vorschau_rueckfall_oder_kommerziell(name):
    assert name in backbone.BACKBONES, "kein Eintrag mit nur_forschung im Register"
    assert name not in (backbone.VORGABE_BACKBONE, backbone.VORSCHAU_BACKBONE,
                        backbone.RUECKFALL_BACKBONE)
    assert name not in [b.name for b in backbone.waehle(kommerziell=True)]
    assert backbone.waehle(kommerziell=True)[0].name == backbone.VORGABE_BACKBONE


def test_die_notice_fuehrt_flux3_als_nicht_ausgeliefert():
    text = (WURZEL / "NOTICE").read_text(encoding="utf-8")
    kopf = text.index("Forschungsmodelle - NICHT ausgeliefert")
    assert text.find("black-forest-labs/flux-3-image-klein", kopf) > kopf
    assert "FLUX Kommunity License" in text[kopf:]


# --------------------------------------------------------------------------------------
# (a) Ohne Schalter nicht geladen
# --------------------------------------------------------------------------------------

@pytest.mark.parametrize("name", _forschungsmodelle() or ["(keines)"])
def test_a_ohne_schalter_keine_ladefreigabe(name):
    for umgebung in ({}, {SCHALTER: "0"}, {SCHALTER: "true"}, {SCHALTER: ""}):
        urteil = backbone.ladefreigabe(name, umgebung=umgebung)
        assert urteil["darf"] is False, umgebung
        assert SCHALTER in urteil["begruendung"]
    urteil = backbone.ladefreigabe(name, umgebung={SCHALTER: "1"})
    assert urteil["darf"] is True and urteil["forschung"] is True


@pytest.mark.parametrize("name", _forschungsmodelle() or ["(keines)"])
def test_a_der_lader_weist_ohne_schalter_ab_bevor_er_die_platte_ansieht(
        name, ohne_schalter, tmp_path):
    # Ein leerer Ordner als Modellwurzel: Fehlte die Sperre, kaeme die Meldung «es fehlen
    # Dateien». Sie muss aber die Lizenz nennen — vor jedem Blick auf die Gewichte.
    with pytest.raises(render.RenderError) as fehler:
        render.lade_modell(name, modell_wurzel=tmp_path)
    assert "wird nicht geladen" in str(fehler.value)
    assert SCHALTER in str(fehler.value)


def test_a_ohne_schalter_lehnt_die_auftragspruefung_ab(ohne_schalter, tmp_path):
    tiefe, beauty = _bilder(tmp_path)
    a = render.RenderAuftrag(depth_png=tiefe, beauty_png=beauty, prompt="ein Haus",
                             backbone=FLUX3)
    assert any("Regel 1" in m and SCHALTER in m for m in render.pruefe_auftrag(a))


# --------------------------------------------------------------------------------------
# (b) Über die Brücke (KosmoVis/KosmoOrbit) nicht wählbar
# --------------------------------------------------------------------------------------

@pytest.mark.parametrize("name", _forschungsmodelle() or ["(keines)"])
def test_b_kein_forschungsmodell_hat_ein_kuerzel_im_fremden_vertrag(name):
    assert name not in kosmo_szene.BACKBONE_VON_FREMD.values()
    assert name not in kosmo_szene.BACKBONE_VON_FREMD
    assert kosmo_szene.backbone_nach_fremd(name)["ausdrueckbar"] is False


@pytest.mark.parametrize("name", _forschungsmodelle() or ["(keines)"])
def test_b_eine_bestellung_ueber_die_bruecke_wird_abgewiesen(name, mit_schalter):
    """Auch mit gesetztem Schalter — die Brücke ist nie der Heimrechner eines Messlaufs."""
    gelesen = kosmo_szene.lies_szene(_szene(name))
    assert gelesen["maengel"], "Bestellung eines Forschungsmodells ueber die Bruecke angenommen"
    assert any("keine Entsprechung" in m for m in gelesen["maengel"])


@pytest.mark.parametrize("name", _forschungsmodelle() or ["(keines)"])
def test_b_die_zweite_sperre_haelt_auch_mit_eingetragenem_kuerzel(name, mit_schalter,
                                                                   monkeypatch):
    """Trüge jemand ein Kürzel nach, hält `ladefreigabe(umgebung={})` trotzdem dicht."""
    monkeypatch.setitem(kosmo_szene.BACKBONE_VON_FREMD, name, name)
    urteil = kosmo_szene.backbone_von_fremd(name)
    assert urteil["bekannt"] is True and urteil["zulaessig"] is False
    gelesen = kosmo_szene.lies_szene(_szene(name))
    assert any("Regel 1" in m for m in gelesen["maengel"])
    assert name not in knotenweg.voll_bildmodelle()
    assert name not in knotenweg.voll_skizzen_bildmodelle()


def test_b_die_oberflaechen_nennen_flux3_nicht():
    """Die Knotenansicht und ihre Kopie bieten das Modell nicht an (kein Kürzel, kein Name)."""
    treffer = []
    for ordner in ("kosmovis", "oberflaeche", "ipad", "integrations"):
        for pfad in (WURZEL / ordner).rglob("*"):
            if not pfad.is_file() or "node_modules" in pfad.parts:
                continue
            if pfad.suffix not in {".ts", ".tsx", ".js", ".json", ".swift", ".py", ".html"}:
                continue
            text = pfad.read_text(encoding="utf-8", errors="ignore").lower()
            if "flux3" in text or "flux-3" in text:
                treffer.append(str(pfad.relative_to(WURZEL)))
    assert not treffer, treffer


# --------------------------------------------------------------------------------------
# (c) Ohne Beauty-Render abgewiesen («Immer vom Render»)
# --------------------------------------------------------------------------------------

@pytest.mark.parametrize("name", _forschungsmodelle() or ["(keines)"])
def test_c_ohne_beauty_render_abgewiesen(name, mit_schalter, tmp_path):
    tiefe, _ = _bilder(tmp_path)
    a = render.RenderAuftrag(depth_png=tiefe, prompt="ein Haus", backbone=name)
    maengel = render.pruefe_auftrag(a)
    assert any(render.SATZ_FORSCHUNG_NUR_VOM_RENDER in m for m in maengel), maengel


@pytest.mark.parametrize("name", _forschungsmodelle() or ["(keines)"])
def test_c_mit_beauty_render_bleibt_die_pruefung_frei(name, mit_schalter, tmp_path):
    tiefe, beauty = _bilder(tmp_path)
    a = render.RenderAuftrag(depth_png=tiefe, beauty_png=beauty, prompt="ein Haus",
                             backbone=name)
    assert render.pruefe_auftrag(a) == []


@pytest.mark.parametrize("name", _forschungsmodelle() or ["(keines)"])
def test_c_rendere_rechnet_ohne_beauty_render_nicht(name, mit_schalter, tmp_path):
    tiefe, _ = _bilder(tmp_path)
    geladen = []
    a = render.RenderAuftrag(depth_png=tiefe, prompt="ein Haus", backbone=name)
    ergebnis = render.rendere(a, _lader=lambda *x, **k: geladen.append(x))
    assert ergebnis["status"] == render.STATUS_ABGELEHNT
    assert geladen == []
    assert ergebnis["parameter"].get("nur_forschung") is True


def test_c_das_vorgabemodell_bleibt_unberuehrt(tmp_path):
    """Die Sperre gilt dem Forschungsmodell, nicht jedem Lauf ohne Cycles-Bild."""
    tiefe, _ = _bilder(tmp_path)
    a = render.RenderAuftrag(depth_png=tiefe, prompt="ein Haus")
    assert not any(render.SATZ_FORSCHUNG_NUR_VOM_RENDER in m
                   for m in render.pruefe_auftrag(a))


# --------------------------------------------------------------------------------------

def _bilder(ordner: Path) -> tuple[str, str]:
    tiefe, beauty = ordner / "tiefe.png", ordner / "beauty.png"
    tiefe.write_bytes(b"\x89PNG\r\n\x1a\n")
    beauty.write_bytes(b"\x89PNG\r\n\x1a\n")
    return str(tiefe), str(beauty)


def _szene(kuerzel: str) -> dict:
    return {
        "schema": kosmo_szene.SCHEMA_SZENE,
        "geometry": {"path": "/synthetisch/modell.glb", "format": "glb"},
        "out": "/synthetisch/aus",
        "render": {"resolution": [1600, 1000], "samples": 128, "faithful": 0.8},
        "style": {"mode": "none", "refs": [], "prompt": ""},
        "vis": {"skip": False, "backbone": kuerzel, "upscale": False},
    }
