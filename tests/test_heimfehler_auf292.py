"""Die Befunde aus ``auf-20261020-292`` (HomeStation, 20.10.2026): Stimmung, Kamera, Material.

Der Owner hat die Bilder angesehen: bei «abend» das Himmelsbild als Fotohintergrund, das Haus
schwebt davor; bei «mittag» das Haus eine rein weisse Fläche; die Geländeplatte mit Stampflehm.
Je Punkt eine Probe — mit Attrappen, der Runner per Quelltext- und Argumentprobe (Regel 2:
kein ``bpy`` im Produkt-venv). Testdaten synthetisch (Regel 3).
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import pytest

from aiimaging import (abholer, arbeitsgang, backbone, belichtung, bruecke, kameras,
                       knotenweg, kosmo_szene, materialwahl, maske, seams, stimmung)

from test_kettenlauf_26august import _auftragsordner, _kette, _lauf
from test_knotenweg import _glb

RUNNER = (Path(__file__).resolve().parents[1] / "src" / "aiimaging" / "runners"
          / "blender_depth_stage.py")


def _runner(monkeypatch):
    bpy = mock.MagicMock()
    monkeypatch.setitem(sys.modules, "bpy", bpy)
    spez = importlib.util.spec_from_file_location("blender_pruefling_auf292", RUNNER)
    modul = importlib.util.module_from_spec(spez)
    spez.loader.exec_module(modul)
    return modul, bpy


def _szene_aendern(ordner, **render):
    pfad = ordner / bruecke.DATEI_SZENE
    szene = json.loads(pfad.read_text(encoding="utf-8"))
    szene["render"].update(render)
    pfad.write_text(json.dumps(szene), encoding="utf-8")


# ====================================================================== die neuen Himmelsbilder

#: Die Tabelle der HomeStation vom 20.10.2026 abends (Tausch; die alten Dateien bleiben).
NEUE_HIMMEL = {"morgen": "kloppenheim_06_puresky", "mittag": "kloofendal_43d_clear_puresky",
               "abend": "belfast_sunset_puresky", "blaue-stunde": "qwantani_dusk_2_puresky",
               "bedeckt": "overcast_soil_puresky", "nebel": "kloofendal_misty_morning_puresky",
               "winter": "snow_field", "weiss": "studio_small_08"}


def test_die_vorgaben_sind_die_getauschten_himmelsbilder():
    assert {p: e["hdri"] for p, e in stimmung.STIMMUNGEN.items()} == NEUE_HIMMEL
    assert stimmung.STIMMUNGEN["abend"]["hdri_vorher"] == "fish_eagle_hill"
    assert stimmung.HERKUNFT["lizenz"] == "CC0-1.0"
    for e in stimmung.STIMMUNGEN.values():
        assert stimmung.HDRI_MUSTER.match(e["hdri"])
        assert e["hdri_vorher"] is None or stimmung.HDRI_MUSTER.match(e["hdri_vorher"])


# ====================================================================== 1 · ruhiger Hintergrund

def _himmel(breite, hoehe, oben, unten, sonne=None):
    """Ein equirektanguläres Bild in Blenders Reihenfolge (Zeile 0 unten), RGBA."""
    px = []
    for z in range(hoehe):
        hoch = (z + 0.5) / hoehe * 180.0 - 90.0
        farbe = oben if hoch > 0 else unten
        for x in range(breite):
            f = sonne if (sonne and hoch > 50 and x == 3) else farbe
            px.extend([*f, 1.0])
    return px


def test_die_farben_des_hintergrunds_kommen_aus_dem_himmel_ohne_sonne():
    """Median: Die Sonnenscheibe (50'000) färbt den Grund nicht weiss."""
    px = _himmel(16, 32, (0.3, 0.5, 0.9), (0.2, 0.15, 0.1), sonne=(5e4, 5e4, 5e4))
    farben = stimmung.hintergrund_aus_himmel(px, 16, 32)
    assert farben["zenit"] == [0.3, 0.5, 0.9]
    assert farben["horizont"] == [0.3, 0.5, 0.9], "Band ueber dem Horizont, nicht der Boden"
    with pytest.raises(ValueError):
        stimmung.hintergrund_aus_himmel([0.0] * 10, 16, 32)


def test_kamerastrahlen_sehen_den_verlauf_nicht_das_himmelsbild(monkeypatch):
    modul, bpy = _runner(monkeypatch)
    befund = modul._welt_setzen((0.5, 0.5, 0.5), 1.0, hdr="/x/abend__y_4k.hdr",
                                toenung=(1.1, 0.98, 0.8))
    baum = bpy.data.worlds.new.return_value.node_tree
    arten = [c.args[0] for c in baum.nodes.new.call_args_list]
    assert {"ShaderNodeLightPath", "ShaderNodeMixShader", "ShaderNodeBackground",
            "ShaderNodeVectorMath"} <= set(arten)
    gezogen = [(c.args[0], c.args[1]) for c in baum.links.new.call_args_list]
    licht_weg = bpy.data.worlds.new.return_value.node_tree.nodes.new.return_value
    assert any(a is licht_weg.outputs.__getitem__.return_value for a, _ in gezogen)
    assert befund["hintergrund"]["kamerastrahl"] == "ruhig"
    # Die Attrappe hat keine Bildpunkte: Rueckfall auf das ruhige Grau — NIE das Foto.
    assert befund["hintergrund"]["weg"] == "rueckfall"
    assert befund["toenung"] == [1.1, 0.98, 0.8]


def test_der_runner_waehlt_is_camera_ray_und_nicht_den_transparenten_film():
    quelle = RUNNER.read_text(encoding="utf-8")
    assert '"Is Camera Ray"' in quelle
    assert "film_transparent = True" not in quelle, "der KI-Schritt bekaeme einen Alphakanal"
    # Der ID-Pass baut seine Welt neu (schwarz) — die Bauwerksmaske leidet nicht.
    assert "_welt_setzen((0.0, 0.0, 0.0), 0.0)" in quelle


# ====================================================================== 2 · Belichtung, Tonwerte

def test_tonwerte_agx_mit_himmelsbild_und_zurueck_fuer_den_id_pass(monkeypatch):
    modul, _bpy = _runner(monkeypatch)
    szene = SimpleNamespace(view_settings=SimpleNamespace(view_transform="Standard",
                                                          look="None", exposure=0.0))
    befund = modul._tonwerte_setzen(szene, -1.0)
    assert befund == {"tonwerte": "AgX", "belichtung_ev": -1.0, "grund": ""}
    assert (szene.view_settings.view_transform, szene.view_settings.exposure) == ("AgX", -1.0)
    modul._tonwerte_zurueck(szene)
    assert (szene.view_settings.view_transform, szene.view_settings.exposure) == \
        ("Standard", 0.0)


def test_kennt_blender_kein_agx_gilt_filmic(monkeypatch):
    modul, _bpy = _runner(monkeypatch)

    class Ansicht:
        look = "None"
        exposure = 0.0
        _vt = "Standard"

        @property
        def view_transform(self):
            return self._vt

        @view_transform.setter
        def view_transform(self, wert):
            if wert == "AgX":
                raise TypeError("enum 'AgX' not found")
            self._vt = wert

    szene = SimpleNamespace(view_settings=Ansicht())
    assert modul._tonwerte_setzen(szene, 0.5)["tonwerte"] == "Filmic"


def test_der_id_pass_rechnet_wieder_mit_standard():
    quelle = RUNNER.read_text(encoding="utf-8")
    schwarz = quelle.index("_welt_setzen((0.0, 0.0, 0.0), 0.0)")
    assert quelle.index("_tonwerte_zurueck(szene)", schwarz) < \
        quelle.index('szene.render.filepath = str(out_dir / "material_id")')
    # Ohne Himmelsbild bleibt «Standard» (die Zeile in `_renderparameter_setzen`).
    assert 'szene.view_settings.view_transform = "Standard"' in quelle


def test_der_runner_kennt_belichtung_und_toenung(monkeypatch):
    modul, _ = _runner(monkeypatch)
    monkeypatch.setattr(sys, "argv", ["blender", "--", "--glb", "a.glb", "--out", "aus",
                                      "--umgebung-hdr", "h.hdr", "--umgebung-belichtung=-1.5",
                                      "--umgebung-toenung=1.1,0.9,0.8"])
    a = modul._argumente()
    assert (a.umgebung_belichtung, a.umgebung_toenung) == (-1.5, "1.1,0.9,0.8")


def test_seams_reicht_belichtung_und_toenung_an_blender():
    cmd = seams.baue_kommando_multipass("m.glb", "aus", up_axis="Y", umgebung_hdr="h.hdr",
                                        umgebung_belichtung=-1.0,
                                        umgebung_toenung=(1.1, 0.9, 0.8))
    assert "--umgebung-belichtung=-1.0" in cmd
    assert "--umgebung-toenung=1.100000,0.900000,0.800000" in cmd
    ohne = seams.baue_kommando_multipass("m.glb", "aus", up_axis="Y")
    assert not any("belichtung" in t or "toenung" in t for t in ohne)


def test_belichtung_je_stimmung_als_daten():
    for preset, e in stimmung.STIMMUNGEN.items():
        assert isinstance(e["belichtung_ev"], float), preset
        assert -3.0 <= e["belichtung_ev"] <= 3.0
    # Mittag und Morgen dunkler als Abend (Befund B1: dort brannte das Haus aus).
    assert stimmung.STIMMUNGEN["mittag"]["belichtung_ev"] < \
        stimmung.STIMMUNGEN["abend"]["belichtung_ev"]
    assert stimmung.STIMMUNGEN["morgen"]["belichtung_ev"] < 0
    assert stimmung.licht_der_stimmung("mittag")["tonwerte"] == ["AgX", "Filmic"]


def test_ueberstrahlt_misst_nur_am_haus():
    farben = [(255, 255, 255)] * 3 + [(200, 200, 200)] * 5 + [(255, 255, 255)] * 2
    haus = [True] * 8 + [False] * 2
    befund = belichtung.ueberstrahlt_anteil(farben, maske=haus)
    assert befund["anteil"] == pytest.approx(3 / 8)
    assert befund["anteil_bild"] == pytest.approx(0.5)
    assert befund["bezug"] == "bauwerk" and befund["unter_ziel"] is False
    # Ein fast weisser Punkt (254) traegt noch Zeichnung — er zaehlt nicht.
    assert belichtung.ueberstrahlt_anteil([(255, 255, 254)])["anteil"] == 0.0
    assert belichtung.ueberstrahlt_anteil(farben, maske=[False] * 10)["anteil"] is None
    with pytest.raises(belichtung.BelichtungsError):
        belichtung.ueberstrahlt_anteil(farben, maske=[True])


def test_ueberstrahlt_aus_png_nie_eine_ausnahme(tmp_path):
    pytest.importorskip("PIL")
    from PIL import Image
    bild = tmp_path / "beauty.png"
    Image.new("RGBA", (4, 2), (255, 255, 255, 255)).save(bild)
    assert belichtung.ueberstrahlt_aus_png(bild)["anteil"] == 1.0
    assert belichtung.ueberstrahlt_aus_png(tmp_path / "fehlt.png")["anteil"] is None
    assert belichtung.ueberstrahlt_aus_png(None)["grund"]


def test_ueberstrahlt_steht_im_ergebnis_je_kamera_und_hoechster():
    je = [{"kamera": "s", "geometrie_urteil": {"kamera": "s", "score": 0.8, "bestanden": True,
                                              "ueberstrahlt": {"anteil": 0.002}}},
          {"kamera": "sSE", "geometrie_urteil": {"kamera": "sSE", "score": 0.7,
                                                "bestanden": True,
                                                "ueberstrahlt": {"anteil": 0.12}}}]
    e = kosmo_szene.als_ergebnis("vis-1-abcdef", ["a.png", "b.png"],
                                 geometrie_urteil=je[1]["geometrie_urteil"], je_kamera=je)
    assert e["qa"]["ueberstrahlt_anteil"] == 0.12
    assert [k.get("ueberstrahlt_anteil") for k in e["qa_je_kamera"]] == [0.002, 0.12]
    assert any("UEBERSTRAHLT" in h and "'sSE'" in h for h in e["hinweise"])
    # Ohne Messung fehlt das Feld — kein null (ihr `.optional()`).
    ohne = kosmo_szene.als_ergebnis("vis-1-abcdef", ["a.png"],
                                    geometrie_urteil={"score": 0.8, "bestanden": True})
    assert "ueberstrahlt_anteil" not in ohne["qa"]


# ====================================================================== 3 · Farbtemperatur

def test_toenung_haelt_die_helligkeit_und_faerbt():
    warm = stimmung.toenung_fuer(4000)
    hell = 0.2126 * warm[0] + 0.7152 * warm[1] + 0.0722 * warm[2]
    assert hell == pytest.approx(1.0, abs=1e-5)
    assert warm[0] > warm[2], "warm heisst mehr Rot als Blau"
    kalt = stimmung.toenung_fuer(9000)
    assert kalt[2] > kalt[0]
    assert stimmung.toenung_fuer(stimmung.NEUTRAL_KELVIN) == pytest.approx((1.0, 1.0, 1.0))
    assert stimmung.toenung_fuer(None) is None


def test_abend_ist_warm_getoent_und_staerke_je_stimmung():
    licht = stimmung.licht_der_stimmung("abend")
    assert licht["kelvin"] is not None and licht["toenung_linear"][0] > \
        licht["toenung_linear"][2]
    assert stimmung.vorgabe_staerke("abend") == stimmung.STIMMUNGEN["abend"]["staerke"]
    s = kosmo_szene.lies_szene({"geometry": {"path": "/x/m.glb", "format": "glb"},
                                "render": {"environment": {"preset": "abend"}},
                                "vis": {"grundlage": "gl-0123456789abcdef"}})
    assert s["umgebung"]["intensitaet"] == stimmung.vorgabe_staerke("abend")


# ====================================================================== 4 · Gelände ohne Material

def test_die_gelaendeplatte_ist_gelaende_und_nicht_boden():
    """Genau der Fall aus 292: ``IfcSlab_Gelaende_292p`` — das Praefix sagt «boden», die
    Bauwerksmaske sagt Gelände. Die Geländeregel gewinnt."""
    name = "IfcSlab_Gelaende_292p"
    assert maske.ist_gelaende(name)
    assert materialwahl.art_von(name, ist_gelaende=maske.ist_gelaende(name)) == "gelaende"
    # Auch gegen ein kind des Modells.
    assert materialwahl.art_von("Platte", kind="slab", ist_gelaende=True) == "gelaende"
    # Eine Decke bleibt Boden.
    assert materialwahl.art_von("IfcSlab_Decke_0abc",
                                ist_gelaende=maske.ist_gelaende("IfcSlab_Decke_0abc")) == "boden"


def test_der_runner_laesst_die_platte_ohne_material(monkeypatch, tmp_path):
    modul, bpy = _runner(monkeypatch)

    def objekt(name):
        o = mock.MagicMock()
        o.name, o.type, o.parent = name, "MESH", None
        o.material_slots = []
        o.get.return_value = None
        return o

    platte, wand = objekt("IfcSlab_Gelaende_292p"), objekt("IfcWall_Hauptbau_292a")
    bpy.data.objects = [platte, wand]
    wahl = tmp_path / "wahl.json"
    wahl.write_text(json.dumps({"arten": {"boden": {"id": "stampflehm"},
                                          "fassade": {"id": "backstein"}}}), encoding="utf-8")
    monkeypatch.setattr(modul, "_material_aus_wahl", lambda *a: mock.MagicMock())
    befund = modul._materialien_setzen(SimpleNamespace(materialien=str(wahl)))
    assert befund["objekte_je_art"]["gelaende"] == 1
    assert befund["objekte_je_art"]["boden"] == 0
    assert befund["nicht_getroffen"] == ["boden"]


# ====================================================================== 5 · Standpunkte

def _hoher_bau(tmp_path) -> Path:
    """Ein hoher Bau wie der Testbau aus 292 (Hauptbau 15 m): Die Höhe bestimmt den Abstand,
    und damit wirkt das Seitenverhältnis."""
    werkzeug = Path(__file__).resolve().parents[1] / "tools" / "make_test_glb.py"
    spez = importlib.util.spec_from_file_location("mk_glb_auf292", werkzeug)
    mk = importlib.util.module_from_spec(spez)
    spez.loader.exec_module(mk)
    ziel = tmp_path / "hoch.glb"
    ziel.write_bytes(mk.baue_glb([("Hauptbau", (-6.0, 0.0, -4.5), (6.0, 15.0, 4.5))]))
    return ziel


def test_die_standpunkte_rechnen_mit_dem_seitenverhaeltnis_des_auftrags(tmp_path):
    mappe = tmp_path / "mappe"
    mappe.mkdir()
    arbeitsgang.lege_an(mappe, _hoher_bau(tmp_path), name="Testbau")
    frage = {"richtungen": ["s"], "brennweite": ["50"], "perspektive": ["senkrecht"]}
    b600 = knotenweg.standpunkte_abfrage(mappe, dict(frage, aufloesung=["960x600"]))
    b592 = knotenweg.standpunkte_abfrage(mappe, dict(frage, aufloesung=["960x592"]))
    ohne = knotenweg.standpunkte_abfrage(mappe, frage)
    getrennt = knotenweg.standpunkte_abfrage(mappe, dict(frage, breite=["960"],
                                                         hoehe=["592"]))
    assert b600["seitenverhaeltnis"] == pytest.approx(1.6)
    assert b592["seitenverhaeltnis"] == pytest.approx(960 / 592, abs=1e-6)
    assert b600["standpunkte"][0]["auge"] == ohne["standpunkte"][0]["auge"]
    assert b592["standpunkte"][0]["auge"] == getrennt["standpunkte"][0]["auge"]
    assert b592["standpunkte"][0]["auge"] != b600["standpunkte"][0]["auge"]
    # Dieselbe Rechnung wie der Heim-PC: kamerasatz mit dem Seitenverhaeltnis des Laufs.
    glb = knotenweg.glb_der_mappe(mappe)
    direkt = knotenweg.heim_standpunkte(glb, "Y", kameras_auto=b592["kameras_auto"],
                                        seitenverhaeltnis=960 / 592)
    assert direkt["standpunkte"][0]["auge"] == b592["standpunkte"][0]["auge"]


@pytest.mark.parametrize("frage", [
    {"aufloesung": ["960"]}, {"aufloesung": ["axb"]}, {"seitenverhaeltnis": ["0"]},
    {"breite": ["960"]}, {"aufloesung": ["960x600"], "seitenverhaeltnis": ["1.6"]},
    {"seitenverhaeltnis": ["nan"]},
])
def test_eine_falsche_bildgroesse_ist_400(tmp_path, frage):
    mappe = tmp_path / "mappe"
    mappe.mkdir()
    arbeitsgang.lege_an(mappe, _glb(tmp_path), name="Testbau")
    with pytest.raises(knotenweg.KnotenwegError) as fehler:
        knotenweg.standpunkte_abfrage(mappe, frage)
    assert fehler.value.code == 400


# ====================================================================== 6 · bestellte Grösse

def test_blender_rechnet_die_bestellte_groesse(tmp_path):
    ordner = _auftragsordner(tmp_path)
    _szene_aendern(ordner, resolution=[960, 600])
    protokoll, attrappen = _kette(tmp_path)
    antwort = _lauf(tmp_path, ordner, attrappen)
    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort["grund"]
    kw = protokoll["multipass"][0]
    assert (kw["aufloesung"], kw["hoehe"]) == (960, 600)
    assert any("960x592" in w and "zurück" in w for w in antwort["warnungen"])


def test_nur_der_ki_schritt_rastert_und_kommt_zurueck(tmp_path):
    pytest.importorskip("PIL")
    from aiimaging import bildschreiben
    tiefe = tmp_path / "tiefe.png"
    bildschreiben.schreibe_graustufen_png(tiefe, [0.5] * (96 * 60), 96, 60, bittiefe=16)
    steuer = abholer.ki_steuerbilder(tiefe, None, tmp_path / "_ki", vorschau=False)
    assert steuer["verkleinert"] is True
    assert steuer["ki_groesse"] == [96, 48] and steuer["grundlage_groesse"] == [96, 60]
    assert bildschreiben.png_masse(steuer["tiefe_png"]) == (96, 48)
    # Liegt sie schon auf dem Raster, bleibt alles, wie es ist.
    passt = tmp_path / "passt.png"
    bildschreiben.schreibe_graustufen_png(passt, [0.5] * (96 * 64), 96, 64, bittiefe=16)
    assert abholer.ki_steuerbilder(passt, None, tmp_path / "_k2",
                                   vorschau=False)["verkleinert"] is False
    assert backbone.ki_raster_groesse(960, 600) == (960, 592)


# ====================================================================== 7 · Vorschau

def test_die_vorschau_steuert_mit_dem_registerwert():
    assert backbone.hole("z-image-turbo").vorschau_steuerstaerke == 1.0
    assert "auf-20261020-292" in backbone.hole("z-image-turbo").vorschau_steuerstaerke_beleg
    assert abholer.steuerstaerke_des_laufs({"guete": "vorschau",
                                            "controlnet_staerke": 0.8}) == 1.0
    assert abholer.steuerstaerke_des_laufs({"guete": "voll", "controlnet_staerke": 0.8}) == 0.8
    assert abholer.steuerstaerke_des_laufs({"controlnet_staerke": 0.6}) == 0.6
    # Kein verstreuter Wert: im Abholer steht keine 1.0 fuer die Vorschau.
    quelle = (Path(abholer.__file__)).read_text(encoding="utf-8")
    assert "controlnet_staerke=steuerstaerke_des_laufs(szene)" in quelle


def test_der_vorschau_vermerk_nennt_die_uebergangene_staerke():
    vermerk = abholer._guete_vermerk({"guete": "vorschau", "controlnet_staerke": 0.8},
                                     "z-image-turbo", 8, None, None)
    assert vermerk["steuerstaerke"] == 1.0 and vermerk["steuerstaerke_bestellt"] == 0.8
    assert any("faithful 0.8" in h for h in vermerk["hinweise"])


def test_z_image_turbo_nimmt_keinen_negativprompt():
    """Befund statt Zusatz: Führung 0.0 heisst, diffusers schaltet die klassifikatorfreie
    Führung ab — ein Negativprompt wirkt dann nicht. Ein positiver «no text» ist nicht belegt
    (ein Wort im Prompt kann das Gegenteil bestellen); er wird in 293 gemessen, nicht gesetzt."""
    assert backbone.hole("z-image-turbo").fuehrung == 0.0
    from aiimaging import prompts
    assert "lettering" not in json.dumps(getattr(prompts, "__dict__", {}), default=str)


# ====================================================================== 8 · Geometriemass leer

def test_ohne_gemeinsame_silhouette_ist_geom_iou_leer_mit_grund():
    urteil = {"score": None, "bestanden": None, "geom_iou": 0.0, "n_gemeinsam": 0,
              "spearman": None, "gesamtwert_anwendbar": False, "anteil_soll": 0.12}
    e = kosmo_szene.als_ergebnis("vis-1-abcdef", ["a.png"], geometrie_urteil=urteil)
    assert e["qa"]["geometry"]["geom_iou"] is None
    assert "nicht gemessen" in e["qa"]["geometry"]["geom_iou_grund"]
    # Ein gemessener Wert bleibt, auch unter 20 % Hausanteil.
    gemessen = dict(urteil, score=0.4, geom_iou=0.3, n_gemeinsam=900, spearman=0.6)
    e = kosmo_szene.als_ergebnis("vis-1-abcdef", ["a.png"], geometrie_urteil=gemessen)
    assert e["qa"]["geometry"]["geom_iou"] == 0.3
    assert "geom_iou_grund" not in e["qa"]["geometry"]


# ====================================================================== 9 · Abweisung mit Ergebnis

def _texturen(ordner, kennung, asset, karten):
    from PIL import Image
    ordner.mkdir(parents=True, exist_ok=True)
    for k in karten:
        Image.new("RGB", (4, 2), (120, 110, 100)).save(
            ordner / f"{kennung}__{asset}_2K-JPG_{k}.jpg", "JPEG")


@pytest.mark.parametrize("fall", ["unbekannte_id", "textur_fehlt"])
def test_eine_fehlende_textur_oder_id_ergibt_ein_ergebnis_mit_grund(tmp_path, monkeypatch,
                                                                     fall):
    pytest.importorskip("PIL")
    bibliothek = tmp_path / "bibliothek"
    # NUR EINE KOPIE in tmp_path: Klinker ohne Displacement-Karte (wie umbenannt).
    _texturen(bibliothek, "klinker", "Bricks054", ("Color", "Roughness"))
    monkeypatch.setenv(materialwahl.MATERIAL_ORDNER_ENV, str(bibliothek))
    ordner = _auftragsordner(tmp_path / "a")
    kennung = "klinker-gibt-es-nicht" if fall == "unbekannte_id" else "klinker"
    _szene_aendern(ordner, materialien={"dach": {"id": kennung}})
    protokoll, attrappen = _kette(tmp_path)

    antwort = _lauf(tmp_path, ordner, attrappen)

    assert antwort["tat"] == abholer.TAT_FEHLER
    assert protokoll["multipass"] == [], "kein Blender"
    ergebnis = json.loads((ordner / bruecke.DATEI_ERGEBNIS).read_text(encoding="utf-8"))
    assert ergebnis["lieferstatus"] == kosmo_szene.LIEFERSTATUS_FEHLGESCHLAGEN
    assert ergebnis["images"] == []
    if fall == "unbekannte_id":
        assert ergebnis["lieferstatus_grund"].startswith(
            "Material 'klinker-gibt-es-nicht' (dach) ist nicht in der Bibliothek")
    else:
        assert ergebnis["lieferstatus_grund"] == \
            "Textur 'klinker' (2K, Displacement) fehlt am Rechner."
    assert str(tmp_path) not in json.dumps(ergebnis), "kein Pfad (Regel 3)"


# ====================================================================== 10 · 409 beim Anlegen

def _grundlage_auftrag(ablage: Path, kennung: str, render: dict) -> Path:
    erster = knotenweg.lege_an(ablage, {"geometry": {"format": "glb"}, "render": render,
                                        "vis": {}},
                               b"glTF-erstes-modell", "m.glb", kennung="vis-1792500000-aaaaaa")
    (ablage / erster["job_id"] / bruecke.DATEI_ERGEBNIS).write_text(
        json.dumps({"grundlage": {"id": kennung, "wiederverwendet": False}}), encoding="utf-8")
    return ablage / erster["job_id"]


def test_eine_variante_mit_anderer_stimmung_wird_beim_anlegen_abgewiesen(tmp_path):
    kennung = "gl-0123456789abcdef"
    _grundlage_auftrag(tmp_path, kennung, {"environment": {"preset": "mittag"}})
    with pytest.raises(knotenweg.KnotenwegError) as fehler:
        knotenweg.lege_an(tmp_path, {"render": {"environment": {"preset": "abend"}},
                                     "vis": {"grundlage": kennung}}, None,
                          kennung="vis-1792500100-bbbbbb")
    assert fehler.value.code == 409
    assert "Stimmung" in str(fehler.value) and "Grundlage rendern" in str(fehler.value)
    assert not (tmp_path / "vis-1792500100-bbbbbb").exists(), "kein Ordner angelegt"
    # Dieselbe Stimmung geht durch.
    zettel = knotenweg.lege_an(tmp_path, {"render": {"environment": {"preset": "mittag"}},
                                          "vis": {"grundlage": kennung}}, None,
                               kennung="vis-1792500200-cccccc")
    assert zettel["status"] == bruecke.STATUS_AWAITING


def test_andere_materialien_oder_kamera_sind_auch_409(tmp_path):
    kennung = "gl-00112233445566aa"
    _grundlage_auftrag(tmp_path, kennung, {"materialien": {"fassade": {"id": "backstein"}}})
    with pytest.raises(knotenweg.KnotenwegError) as fehler:
        knotenweg.lege_an(tmp_path, {"render": {"materialien": {"fassade": {"id": "klinker"}}},
                                     "vis": {"grundlage": kennung}}, b"glTF", "m.glb",
                          kennung="vis-1792500300-dddddd")
    assert fehler.value.code == 409 and "Materialien" in str(fehler.value)
    with pytest.raises(knotenweg.KnotenwegError) as fehler:
        knotenweg.lege_an(tmp_path, {"render": {"materialien": {"fassade": {"id": "backstein"}}},
                                     "cameras_auto": {"richtungen": ["n"]},
                                     "vis": {"grundlage": kennung}}, b"glTF", "m.glb",
                          kennung="vis-1792500400-eeeeee")
    assert fehler.value.code == 409 and "Kamera" in str(fehler.value)


def test_ohne_bekannte_grundlage_sagt_die_pruefung_nichts(tmp_path):
    assert knotenweg.grundlage_passt_nicht(
        tmp_path, {"vis": {"grundlage": "gl-ffffffffffffffff"}}) is None
    assert knotenweg.grundlage_passt_nicht(tmp_path, {"vis": {}}) is None


def test_ohne_gemeinsame_silhouette_kein_null_in_geometry_gates():
    """Integrator 20.10.2026: ``geometry_gates.geom_iou`` ist im fremden Vertrag nur optional,
    nicht nullbar — ein ``null`` dort verwirft in KosmoOrbit v0.1.8 das GANZE Ergebnis.
    Hinaus (``nur_vertragsfelder``) darf darum in ``geometry_gates`` nirgends ``null`` stehen;
    ``qa.geometry.geom_iou`` ist dort nullbar und darf leer sein."""
    urteil = {"score": None, "bestanden": None, "geom_iou": 0.0, "n_gemeinsam": 0,
              "spearman": None, "gesamtwert_anwendbar": False, "anteil_soll": 0.12}
    tore = {"bestanden": None,
            "tor_folgt": {"gemessen": True, "wert": 0.41, "schwelle": 0.3, "bestanden": True},
            "tor_dieses": {"gemessen": False, "wert": None, "schwelle": 0.5, "bestanden": None},
            "gegenprobe": None, "warnungen": []}
    e = kosmo_szene.als_ergebnis("vis-1-abcdef", ["a.png"], geometrie_urteil=urteil,
                                 zwei_tore_urteil=tore)
    aus = kosmo_szene.nur_vertragsfelder(e)
    tore_aus = aus[kosmo_szene.FELD_ZWEI_TORE]
    assert "geom_iou" not in tore_aus
    assert all(v is not None for v in tore_aus.values())
    assert isinstance(tore_aus["passed"], bool) and isinstance(tore_aus["released"], bool)
    assert aus["qa"]["geometry"]["geom_iou"] is None
