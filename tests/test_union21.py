"""Union-2.1 als eigener Eintrag — Befunde aus `auf-20260930-199` (Sitzung 73 §22).

1. Der Ladeweg suchte die Basis im Ordner «z-image-turbo-union21» und wies den Lauf ab —
   auch auf dem Abholer-Weg. Seither sagt ``gewichte_ordner``, wo sie liegt.
2. Die gemessene Spitze passt auf der 32-GB-Karte nicht mit Zuschlag: Der Ladeweg lagert aus.
"""
from __future__ import annotations

from aiimaging import backbone, render

NAME = "z-image-turbo-union21"


def test_die_basis_liegt_im_ordner_von_z_image_turbo():
    assert render.wurzel_fuer(NAME) == render.standard_modell_wurzel("z-image-turbo")
    assert render.wurzel_fuer(NAME) == render.wurzel_fuer("z-image-turbo")


def test_ein_unbekannter_name_bleibt_sein_eigener_ordner():
    assert render.wurzel_fuer("gibt-es-nicht") == render.standard_modell_wurzel("gibt-es-nicht")


def test_die_uebrigen_eintraege_behalten_ihren_namen_als_ordner():
    for name, e in backbone.BACKBONES.items():
        if name != NAME:
            assert e.gewichte_ordner is None, name
            assert render.wurzel_fuer(name) == render.standard_modell_wurzel(name)


def test_der_parameterbericht_nennt_die_richtige_wurzel(tmp_path):
    tiefe = tmp_path / "tiefe.png"
    tiefe.write_bytes(b"x")
    a = render.RenderAuftrag(backbone=NAME, depth_png=str(tiefe), prompt="a house",
                             ausgabe_png=str(tmp_path / "aus.png"))
    p = render._baue_parameter(a, backbone.hole(NAME))
    assert p["modell_wurzel"] == str(render.wurzel_fuer("z-image-turbo"))


def test_die_gemessene_spitze_laesst_auf_32_gb_auslagern():
    """31,1 GiB gemessen (auf-199, 1024 px) × Messzuschlag > was eine 32-GB-Karte frei hat."""
    e = backbone.hole(NAME)
    assert e.vram_gemessen is True and e.vram_gb == 31.1
    summe, _ = render._erwarteter_bedarf(e)
    frei = 30_938 * 2**20                                   # frei vor dem Lauf, auf-199 C3
    assert frei < summe * render.MESSUNG_ZUSCHLAG


def test_nie_vorgabe():
    assert NAME not in {backbone.VORGABE_BACKBONE, backbone.VORSCHAU_BACKBONE,
                        backbone.RUECKFALL_BACKBONE}


def test_die_vorpruefung_sucht_im_selben_ordner_wie_der_ladeweg(tmp_path, monkeypatch):
    """auf-201: `rendere` prüft VOR dem Laden mit `modellwurzel_lage` — die suchte den Namen
    als Ordner und wies ab, obwohl der Ladeweg die Basis gefunden hätte."""
    monkeypatch.setenv(render.UMGEBUNG_MODELLE, str(tmp_path))
    (tmp_path / "z-image-turbo").mkdir()
    lage = render.modellwurzel_lage(NAME)
    assert lage["existiert"] is True
    assert lage["wurzel"] == str(tmp_path / "z-image-turbo") == str(render.wurzel_fuer(NAME))


def test_rendere_weist_union21_nicht_mehr_wegen_des_ordners_ab(tmp_path, monkeypatch):
    """Der Weg, den die HomeStation fuhr: ohne modell, ohne _lader, ohne modell_wurzel."""
    monkeypatch.setenv(render.UMGEBUNG_MODELLE, str(tmp_path))
    (tmp_path / "z-image-turbo").mkdir()
    tiefe = tmp_path / "tiefe.png"
    tiefe.write_bytes(b"x")
    a = render.RenderAuftrag(backbone=NAME, depth_png=str(tiefe), prompt="a house",
                             ausgabe_png=str(tmp_path / "aus.png"))
    erg = render.rendere(a)
    assert "kein Ordner" not in (erg.get("error") or ""), erg.get("error")
