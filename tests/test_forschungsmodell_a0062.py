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
    """Die Sperre ``SATZ_FORSCHUNG_NUR_VOM_RENDER`` gilt dem Forschungsmodell. Läufe am Vorgabemodell
    ohne Cycles-Bild sperrt die Masstreue («Immer vom Render», A0051 bis A0051c) an Bestellung,
    Knotenweg und Bildstufe — mit ihrem eigenen Satz, nicht mit diesem; ein solcher Lauf ist also
    NICHT in Ordnung, er wird nur nicht hier abgewiesen."""
    tiefe, _ = _bilder(tmp_path)
    a = render.RenderAuftrag(depth_png=tiefe, prompt="ein Haus")
    assert not any(render.SATZ_FORSCHUNG_NUR_VOM_RENDER in m
                   for m in render.pruefe_auftrag(a))


# --------------------------------------------------------------------------------------
# A0062b (Gegenlese rot, Mangel 1): «nur vom Render» heisst ANGEKOMMEN, nicht nur «Datei genannt»
# --------------------------------------------------------------------------------------

def _echte_bilder(ordner: Path) -> tuple[str, str]:
    """Zwei lesbare PNGs (Pillow öffnet sie im Adapter)."""
    from conftest import MINI_PNG  # noqa: PLC0415
    tiefe, beauty = ordner / "tiefe.png", ordner / "beauty.png"
    tiefe.write_bytes(MINI_PNG)
    beauty.write_bytes(MINI_PNG)
    return str(tiefe), str(beauty)


@pytest.fixture
def verwirft_image(monkeypatch):
    """Der ECHTE Adapter über einer Pipeline, die ``image`` nicht kennt (die Lage, die die
    Gegenlese für das modulare FLUX-3-Paket offen sah): Die Naht verwirft das Bild still."""
    import PIL.Image  # noqa: F401, PLC0415 — Pillow steht in den dev-Abhaengigkeiten
    from test_render import Pipelineattrappe, _Torchattrappe  # noqa: PLC0415

    def vertraeglich(pipeline, argumente):
        verworfen = [n for n in ("image", "strength") if n in argumente]
        return {k: v for k, v in argumente.items() if k not in verworfen}, verworfen

    monkeypatch.setattr(render, "_vertraegliche_argumente", vertraeglich)
    pipeline = Pipelineattrappe(schritte=2)

    def bauen(name):
        return render._pipeline_adapter(pipeline, backbone.hole(name), _Torchattrappe())
    bauen.pipeline = pipeline
    return bauen


@pytest.mark.parametrize("name", _forschungsmodelle() or ["(keines)"])
def test_c_verwirft_die_pipeline_das_bild_wird_kein_bild_geliefert(name, mit_schalter,
                                                                    tmp_path, verwirft_image):
    tiefe, beauty = _echte_bilder(tmp_path)
    a = render.RenderAuftrag(depth_png=tiefe, beauty_png=beauty, prompt="ein Haus",
                             backbone=name, schritte=2, denoise=0.7,
                             ausgabe_png=str(tmp_path / "bild.png"))
    ergebnis = render.rendere(a, modell=verwirft_image(name))
    assert "image" not in verwirft_image.pipeline.gesehen, "die Attrappe hat image verworfen"
    assert ergebnis["status"] != render.STATUS_OK
    assert not ergebnis.get("bild_png")
    assert render.SATZ_FORSCHUNG_NUR_VOM_RENDER in ergebnis["error"]
    assert ergebnis["modus_gerechnet"] == render.MODUS_TXT2IMG


@pytest.mark.parametrize("name", _forschungsmodelle() or ["(keines)"])
def test_c_nimmt_die_pipeline_das_bild_wird_geliefert(name, mit_schalter, tmp_path,
                                                       monkeypatch):
    """Gegenprobe: dieselbe Lage, aber die Pipeline nimmt ``image`` — Bild mit image_edit."""
    import PIL.Image  # noqa: F401, PLC0415 — Pillow steht in den dev-Abhaengigkeiten
    from test_render import Pipelineattrappe, _Torchattrappe  # noqa: PLC0415
    monkeypatch.setattr(render, "_vertraegliche_argumente", lambda p, a: (dict(a), []))
    pipeline = Pipelineattrappe(schritte=2)
    tiefe, beauty = _echte_bilder(tmp_path)
    a = render.RenderAuftrag(depth_png=tiefe, beauty_png=beauty, prompt="ein Haus",
                             backbone=name, schritte=2, denoise=0.7,
                             ausgabe_png=str(tmp_path / "bild.png"))
    ergebnis = render.rendere(a, modell=render._pipeline_adapter(
        pipeline, backbone.hole(name), _Torchattrappe()))
    assert ergebnis["status"] == render.STATUS_OK, ergebnis.get("error")
    assert ergebnis["modus_gerechnet"] == render.MODUS_IMAGE_EDIT


@pytest.mark.parametrize("name", _forschungsmodelle() or ["(keines)"])
@pytest.mark.parametrize("denoise", [1.0, 0.9])
def test_c_denoise_ueber_0_8_wird_abgewiesen(name, denoise, mit_schalter, tmp_path):
    tiefe, beauty = _bilder(tmp_path)
    a = render.RenderAuftrag(depth_png=tiefe, beauty_png=beauty, prompt="ein Haus",
                             backbone=name, denoise=denoise)
    assert any(render.SATZ_FORSCHUNG_NUR_VOM_RENDER in m and "denoise" in m
               for m in render.pruefe_auftrag(a))


@pytest.mark.parametrize("name", _forschungsmodelle() or ["(keines)"])
def test_c_denoise_0_8_bleibt_erlaubt(name, mit_schalter, tmp_path):
    tiefe, beauty = _bilder(tmp_path)
    a = render.RenderAuftrag(depth_png=tiefe, beauty_png=beauty, prompt="ein Haus",
                             backbone=name, denoise=0.8)
    assert render.pruefe_auftrag(a) == []


@pytest.mark.parametrize("name", _forschungsmodelle() or ["(keines)"])
def test_c_der_nachrender_rechnet_kein_forschungsmodell(name, mit_schalter, tmp_path):
    """Der Nachrender rechnet auf einem fremden oder früheren KI-Bild, nie auf dem Beauty-Render."""
    from aiimaging import kette  # noqa: PLC0415
    from aiimaging.graph import Knoten  # noqa: PLC0415
    tiefe, beauty = _echte_bilder(tmp_path)
    gerufen = []
    stufe = kette.nachrender_ausfuehrer(modell=lambda p: gerufen.append(p))
    erg = stufe(knoten=Knoten(id="n", art=kette.ART_NACHRENDER, eingaenge=("m", "r"), params={
        "prompt": "p", "negativ_prompt": "", "backbone": name, "seed": 0, "schritte": 4,
        "controlnet_staerke": 0.8, "denoise": 0.5}),
        eingaben=[{"depth_png": tiefe}, {"bild_png": beauty}], out_dir=tmp_path)
    assert erg["status"] != "ok"
    assert render.SATZ_FORSCHUNG_NUR_VOM_RENDER in erg["error"]
    assert gerufen == []


@pytest.mark.parametrize("name", _forschungsmodelle() or ["(keines)"])
def test_b_die_bruecke_weist_ein_forschungsmodell_sofort_ab(name, tmp_path):
    """Hinweis H1 der Gegenlese: nicht liegen bleiben, sondern 400 mit Satz, kein Ordner."""
    szene = _szene(name)
    saetze = kosmo_szene.widersprueche_beim_annehmen(szene)
    assert any(s.startswith("FORSCHUNGSMODELL") for s in saetze), saetze
    assert any(s.startswith("FORSCHUNGSMODELL")
               for s in kosmo_szene.lies_szene(szene, streng=False)["maengel_endgueltig"])
    with pytest.raises(knotenweg.KnotenwegError) as fehler:
        knotenweg.lege_an(tmp_path, szene, b"glTF-bytes", "model.glb",
                          kennung="vis-1790000000-00a062")
    assert fehler.value.code == 400
    assert not (tmp_path / "vis-1790000000-00a062").exists()


def test_der_messauftrag_vergleicht_vom_selben_beauty_render():
    """Mangel 2 der Gegenlese: Vergleich am Vorgabemodell MIT Bildeingang (≤ 0,8), gleicher
    Standpunkt, modus_gerechnet je Lauf; Gegenprobe ergänzt; Codestand auf A0051c."""
    import json  # noqa: PLC0415
    a = json.loads((WURZEL / "auftraege/offen/auf-20261031-377.json").read_text(encoding="utf-8"))
    p = a["params"]
    assert 0 < p["bildeingang_staerke_vorgabemodell"] <= kosmo_szene.BILDEINGANG_SPANNE[1]
    assert 0 < p["denoise_flux3"] <= render.FORSCHUNG_DENOISE_HOECHSTENS
    # A0062c: die Textliste heisst «ablauf» (schritte ist die Zahl), und Schritt 2 steht wieder davor.
    assert "bildeingang_staerke 0.7" in p["ablauf"][4] and "Standpunkt" in p["ablauf"][4]
    assert "modus_gerechnet" in p["ablauf"][4] and "modus_gerechnet" in p["ablauf"][5]
    assert "denoise 1.0" in p["ablauf"][6]
    assert "A0051c" in p["codestand"]
    assert any("modus_gerechnet" in r for r in a["rueckgabe"])


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


# --------------------------------------------------------------------------------------
# A0062c (Gegenlese A0062b rot): Messauftrag ausführbar, denoise-Grenze wirksam
# --------------------------------------------------------------------------------------

def _messauftrag() -> dict:
    import json  # noqa: PLC0415
    return json.loads((WURZEL / "auftraege/offen/auf-20261031-377.json").read_text(encoding="utf-8"))


def test_a0062c_der_messauftrag_hat_seinen_blender_schritt_wieder():
    """Mangel 1: Schritt 2 erzeugt den Beauty-Render, von dem beide Modelle starten."""
    ablauf = _messauftrag()["params"]["ablauf"]
    zwei = [s for s in ablauf if s.startswith("2 ")]
    assert len(zwei) == 1 and "Blender" in zwei[0] and "Beauty-Render" in zwei[0]
    assert "Schritt 2" in _messauftrag()["params"]["standpunkt"]


def test_a0062c_der_messauftrag_hat_eine_fassung_von_schritt_5():
    ablauf = _messauftrag()["params"]["ablauf"]
    fuenf = [s for s in ablauf if s.startswith("5 ")]
    assert len(fuenf) == 1
    assert all(f"({b})" in fuenf[0] for b in "abcd")
    assert any("vier" in r for r in _messauftrag()["rueckgabe"])


def test_a0062c_schritte_ist_eine_ganze_zahl():
    s = _messauftrag()["params"]["schritte"]
    assert isinstance(s, int) and not isinstance(s, bool) and s >= 1


def test_a0062c_der_takt_rechnet_den_messauftrag_nicht_selbst():
    """Der Homeworker fasst art «frage» nicht an — sonst führe er einen eigenen Lauf ohne die
    Schritte (am Vorgabemodell, ohne die Vergleichsreihe)."""
    from aiimaging import auftrag  # noqa: PLC0415
    a = _messauftrag()
    assert a["art"] == auftrag.ART_FRAGE
    assert a["art"] not in auftrag.ARTEN_LAUF
    assert auftrag.pruefe_auftrag(a) == []


@pytest.fixture
def verwirft_strength(monkeypatch):
    """Der ECHTE Adapter über einer Pipeline, die ``image`` nimmt, aber ``strength`` verwirft —
    Bearbeiten mit dem Render nur als Referenz, alle Schritte ab Rauschen (Gegenlese A0062b, 2)."""
    import PIL.Image  # noqa: F401, PLC0415
    from test_render import Pipelineattrappe, _Torchattrappe  # noqa: PLC0415

    def vertraeglich(pipeline, argumente):
        verworfen = [n for n in ("strength",) if n in argumente]
        return {k: v for k, v in argumente.items() if k not in verworfen}, verworfen

    monkeypatch.setattr(render, "_vertraegliche_argumente", vertraeglich)
    pipeline = Pipelineattrappe(schritte=2)

    def bauen(name):
        return render._pipeline_adapter(pipeline, backbone.hole(name), _Torchattrappe())
    bauen.pipeline = pipeline
    return bauen


@pytest.mark.parametrize("name", _forschungsmodelle() or ["(keines)"])
def test_a0062c_ohne_angekommenes_strength_kein_bild(name, mit_schalter, tmp_path,
                                                     verwirft_strength):
    tiefe, beauty = _echte_bilder(tmp_path)
    a = render.RenderAuftrag(depth_png=tiefe, beauty_png=beauty, prompt="ein Haus",
                             backbone=name, schritte=2, denoise=0.7,
                             ausgabe_png=str(tmp_path / "bild.png"))
    ergebnis = render.rendere(a, modell=verwirft_strength(name))
    assert "strength" not in verwirft_strength.pipeline.gesehen
    assert ergebnis["status"] != render.STATUS_OK
    assert not ergebnis.get("bild_png")
    assert render.SATZ_FORSCHUNG_NUR_VOM_RENDER in ergebnis["error"]
    assert "strength" in ergebnis["error"]
    assert ergebnis["parameter"]["strength_genommen"] is False


@pytest.mark.parametrize("name", _forschungsmodelle() or ["(keines)"])
def test_a0062c_gegenprobe_strength_genommen_steht_im_lauf(name, mit_schalter, tmp_path,
                                                          monkeypatch):
    import PIL.Image  # noqa: F401, PLC0415
    from test_render import Pipelineattrappe, _Torchattrappe  # noqa: PLC0415
    monkeypatch.setattr(render, "_vertraegliche_argumente", lambda p, a: (dict(a), []))
    tiefe, beauty = _echte_bilder(tmp_path)
    a = render.RenderAuftrag(depth_png=tiefe, beauty_png=beauty, prompt="ein Haus",
                             backbone=name, schritte=2, denoise=0.7,
                             ausgabe_png=str(tmp_path / "bild.png"))
    ergebnis = render.rendere(a, modell=render._pipeline_adapter(
        Pipelineattrappe(schritte=2), backbone.hole(name), _Torchattrappe()))
    assert ergebnis["status"] == render.STATUS_OK, ergebnis.get("error")
    assert ergebnis["parameter"]["strength_genommen"] is True


# --------------------------------------------------------------------------------------
# A0062d (Gegenlese A0062c rot, Mangel 1): **kwargs heisst UNBELEGT, nicht «alles genommen»
# --------------------------------------------------------------------------------------

class _KwargsPipeline:
    """Wie ``ModularPipeline.__call__(state, output, **kwargs)`` in diffusers 0.42.1: nimmt jedes
    Argument entgegen und verwirft ``image`` und ``strength`` still (dort nur mit Warnung). Ruft
    den Schrittzähler wirklich, damit die gerechneten Schritte belegt sind."""

    def __init__(self, schritte: int = 2):
        self._schritte = schritte
        self.gesehen = {}
        self.benutzt = set()

    def __call__(self, state=None, output=None, **kwargs):
        from test_render import _Bildattrappe  # noqa: PLC0415
        self.gesehen = kwargs
        self.benutzt = {k for k in kwargs if k not in ("image", "strength")}
        rueckruf = kwargs.get("callback_on_step_end")
        if rueckruf is not None:
            for i in range(self._schritte):
                rueckruf(self, i, 0.0, {"latents": "x"})
        return type("Aus", (), {"images": [_Bildattrappe()]})()


class _UnlesbarePipeline(_KwargsPipeline):
    """Eine Pipeline, deren Signatur ``inspect.signature`` nicht lesen kann."""

    def __call__(self, *args, **kwargs):
        return super().__call__(**kwargs)

    __call__.__signature__ = "nicht lesbar"


def _a0062d_auftrag(name, tmp_path) -> render.RenderAuftrag:
    tiefe, beauty = _echte_bilder(tmp_path)
    return render.RenderAuftrag(depth_png=tiefe, beauty_png=beauty, prompt="ein Haus",
                                backbone=name, schritte=2, denoise=0.7,
                                ausgabe_png=str(tmp_path / "bild.png"))


@pytest.mark.parametrize("pipeline_art", [_KwargsPipeline, _UnlesbarePipeline])
@pytest.mark.parametrize("name", _forschungsmodelle() or ["(keines)"])
def test_a0062d_kwargs_pipeline_ohne_strength_liefert_kein_bild(name, pipeline_art, mit_schalter,
                                                                tmp_path):
    """Der ECHTE Adapter und die ECHTE Signaturlesung, kein Ersatz: Bei **kwargs oder unlesbarer
    Signatur ist nicht belegt, dass strength und image ankamen — ein Forschungsmodell liefert dann
    kein Bild, und beide Felder stehen als unbelegt (None) da, nicht als «ja»."""
    import PIL.Image  # noqa: F401, PLC0415
    from test_render import _Torchattrappe  # noqa: PLC0415
    pipeline = pipeline_art(schritte=2)
    ergebnis = render.rendere(_a0062d_auftrag(name, tmp_path), modell=render._pipeline_adapter(
        pipeline, backbone.hole(name), _Torchattrappe()))
    assert "strength" in pipeline.gesehen and "strength" not in pipeline.benutzt
    assert ergebnis["status"] == render.STATUS_FEHLER
    assert not ergebnis.get("bild_png")
    assert render.SATZ_FORSCHUNG_NUR_VOM_RENDER in ergebnis["error"]
    assert ergebnis["parameter"]["strength_genommen"] is None
    assert ergebnis["modus_gerechnet"] is None
    assert any("UNBELEGT" in h for h in ergebnis["hinweise"])


def test_a0062d_gegenprobe_das_vorgabemodell_bleibt_unveraendert(tmp_path):
    """Freigegebene Modelle werden NICHT angefasst, bis der Heim-PC ihre Signaturen gemessen hat:
    Dieselbe **kwargs-Pipeline am Vorgabemodell meldet wie vor A0062d, was bestellt war."""
    import PIL.Image  # noqa: F401, PLC0415
    from test_render import _Torchattrappe  # noqa: PLC0415
    name = backbone.VORGABE_BACKBONE
    assert not backbone.hole(name).nur_forschung
    for pipeline_art in (_KwargsPipeline, _UnlesbarePipeline):
        modell = render._pipeline_adapter(pipeline_art(schritte=2), backbone.hole(name),
                                          _Torchattrappe())
        ergebnis = render.rendere(_a0062d_auftrag(name, tmp_path), modell=modell)
        assert ergebnis["status"] == render.STATUS_OK, ergebnis.get("error")
        assert ergebnis["modus_gerechnet"] == ergebnis["modus_bestellt"] == render.MODUS_IMAGE_EDIT
        assert ergebnis["parameter"]["strength_genommen"] is True
        assert not any("UNBELEGT" in h for h in ergebnis["hinweise"])


# --------------------------------------------------------------------------------------
# A0062d (3) = Hinweis H4: Fehler-Ergebnisse behalten schritte_gerechnet und laden_s
# --------------------------------------------------------------------------------------

@pytest.mark.parametrize("name", _forschungsmodelle() or ["(keines)"])
def test_a0062d_fehler_ergebnis_behaelt_schritte_und_ladezeit(name, mit_schalter, tmp_path):
    """Ein abgewiesener Lauf hat trotzdem gerechnet und geladen — gerade am Messlauf zählt, wie
    viele Schritte und wie viel Ladezeit ein verworfenes Bild gekostet hat."""
    import PIL.Image  # noqa: F401, PLC0415
    from test_render import _Torchattrappe  # noqa: PLC0415
    modell = render._pipeline_adapter(_KwargsPipeline(schritte=2), backbone.hole(name),
                                      _Torchattrappe())
    ergebnis = render.rendere(_a0062d_auftrag(name, tmp_path),
                              _lader=lambda backbone_name, wurzel: modell)
    assert ergebnis["status"] == render.STATUS_FEHLER
    assert ergebnis["schritte_gerechnet"] == 2
    assert isinstance(ergebnis["laden_s"], float) and ergebnis["laden_s"] >= 0.0


def test_a0062d_auch_der_ausnahme_fehler_behaelt_die_ladezeit(tmp_path):
    """Wirft die Pipeline, ist die Ladezeit trotzdem gemessen — sie geht nicht mit verloren."""
    def wirft(parameter):
        raise RuntimeError("Attrappe wirft")

    ergebnis = render.rendere(_a0062d_auftrag(backbone.VORGABE_BACKBONE, tmp_path),
                              _lader=lambda backbone_name, wurzel: wirft)
    assert ergebnis["status"] == render.STATUS_FEHLER
    assert isinstance(ergebnis["laden_s"], float) and ergebnis["laden_s"] >= 0.0


# --------------------------------------------------------------------------------------
# A0062d (2): Messauftrag auf-20261031-377 — Codestand, V1 mit Signatur, Schrittzahl Vorgabemodell
# --------------------------------------------------------------------------------------

def test_a0062d_der_messauftrag_nennt_den_codestand_ab_a0062d():
    """Hinweis H1 der Gegenlese: Der Codestand stand noch auf A0062b."""
    p = _messauftrag()["params"]
    assert "A0062d" in p["codestand"]
    assert "A0062d" in _messauftrag()["anweisung"]


def test_a0062d_v1_gibt_klasse_signatur_und_erwartete_eingaben_zurueck():
    """Liste Heim-PC Punkt 2: Erst die Messung am Gerät sagt, ob die geladene Pipeline image UND
    strength wirklich nimmt — V1 muss es zurückgeben, nicht nur «lädt»."""
    a = _messauftrag()
    v1 = [s for s in a["params"]["ablauf"] if s.startswith("V1 ")]
    assert len(v1) == 1
    for wort in ("Klasse", "__call__", "Signatur", "erwarteten Eingaben", "image", "strength",
                 "SIGNATUR UNBELEGT"):
        assert wort in v1[0], wort
    assert any("Klasse" in r and "Signatur" in r for r in a["rueckgabe"])


def test_a0062d_der_messauftrag_nennt_die_schrittzahl_von_z_image_turbo():
    """Hinweis H2: Die Schrittzahl des Vorgabemodells steht als Zahl da, und Schritt 3 nennt sie
    samt der gerechneten Schritte bei Stärke 0,7."""
    p = _messauftrag()["params"]
    s = p["schritte_vorgabemodell"]
    assert isinstance(s, int) and not isinstance(s, bool) and s >= 1
    gerechnet = render.bildeingang_schritte(s, p["bildeingang_staerke_vorgabemodell"])
    assert f"{s} Schritte" in p["ablauf"][4]
    assert f"{gerechnet} gerechnet" in p["ablauf"][4]
