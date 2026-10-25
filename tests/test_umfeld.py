"""Knoten «Umfeld» (24.10.2026): Katalog, Lizenzwächter, Schalter, Zwischenspeicher, Plan, Naht.

Alles ohne Netz und ohne Blender: Die Antworten der Quellen sind **synthetisch** nachgebaut
(Aufbau wie die Antwort von ``api.polyhaven.com/files/<id>`` am 24.10.2026, Inhalt erfunden),
die Zip-Pakete werden hier gebaut. Kein Modell, keine Textur einer Quelle liegt im Repo.
"""
from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import math
import zipfile
from pathlib import Path

import pytest

from aiimaging import abholer, kosmo_szene, maske, seams, umfeld

WURZEL = Path(__file__).resolve().parents[1]


def _make_glb():
    spez = importlib.util.spec_from_file_location("make_test_glb_umfeld",
                                                  WURZEL / "tools" / "make_test_glb.py")
    m = importlib.util.module_from_spec(spez)
    spez.loader.exec_module(m)
    return m


def _testszene(tmp_path, *, mit_gelaende=True, strasse=False):
    koerper = [("Haus", (0.0, 0.0, -8.0), (10.0, 6.0, 0.0))]
    if mit_gelaende:
        koerper.insert(0, ("Gelaende", (-30.0, -0.2, -30.0), (30.0, 0.0, 30.0)))
    if strasse:
        koerper.append(("Strasse Sued", (-30.0, 0.0, 22.0), (30.0, 0.05, 28.0)))
    pfad = tmp_path / "szene.glb"
    pfad.write_bytes(_make_glb().baue_glb(koerper))
    return pfad


# ============================================================ Katalog und Lizenz

def test_jedes_asset_und_jede_quelle_ist_cc0():
    for q in umfeld.QUELLEN.values():
        assert q["lizenz"] == umfeld.LIZENZ_CC0
        assert q["adresse"].startswith("https://")
    for e in umfeld.ASSETS:
        umfeld.pruefe_lizenz(e)
        assert e["seite"].startswith("https://")
        assert e["kategorie"] in umfeld.KATEGORIEN
    for name, p in umfeld.PAKETE.items():
        assert p["url"].startswith("https://"), name
        assert len(p["sha256"]) == 64 and int(p["sha256"], 16) >= 0
    # Jede Kategorie hat mindestens eine Vorgabe.
    for kat in umfeld.KATEGORIEN:
        assert umfeld.vorgaben_der_kategorie(kat), kat


@pytest.mark.parametrize("lizenz", ["CC-BY-4.0", "CC-BY-NC-4.0", "GPL-3.0", "", None])
def test_nicht_cc0_wird_abgewiesen(lizenz):
    eintrag = dict(umfeld.asset("shrub_02"), lizenz=lizenz)
    with pytest.raises(umfeld.LizenzFehler):
        umfeld.pruefe_lizenz(eintrag)


def test_fremde_quelle_wird_abgewiesen():
    with pytest.raises(umfeld.LizenzFehler):
        umfeld.pruefe_lizenz(dict(umfeld.asset("shrub_02"), quelle="sketchfab"))


def test_lizenzwaechter_steht_vor_jedem_laden(tmp_path, monkeypatch):
    """Ein Asset, das nicht CC0 ist, kommt nicht bis zum Netz — auch mit Schalter."""
    gerufen = []
    falsch = tuple(dict(e, lizenz="CC-BY-4.0") if e["id"] == "shrub_02" else e
                   for e in umfeld.ASSETS)
    monkeypatch.setattr(umfeld, "ASSETS", falsch)
    with pytest.raises(umfeld.LizenzFehler):
        umfeld.hole_asset("shrub_02", wurzel=tmp_path, oeffner=gerufen.append,
                          umgebung={umfeld.SCHALTER_ENV: "1"})
    assert gerufen == []
    with pytest.raises(umfeld.LizenzFehler):
        umfeld.plane(gelaende=umfeld.Gelaende([((-20, -20, 0), (20, 20, 0))]),
                     bauwerk_boxen=[((0, 0), (5, 5))], haupt_box=((0, 0), (5, 5)),
                     kategorien=["buesche"], assets_wahl={"buesche": ["shrub_02"]})


def test_material_namen_sind_umfeld_und_nie_gelaende():
    for kat in umfeld.KATEGORIEN:
        for e in umfeld.assets_der_kategorie(kat):
            name = umfeld.material_name(kat, e["id"], 3)
            assert maske.ist_umfeld(name), name
            assert not maske.ist_gelaende(name), name


# ============================================================ Schalter und Zwischenspeicher

def test_schalter_vorgabe_an_seit_entscheid_147():
    assert umfeld.freigeschaltet({})
    assert umfeld.freigeschaltet({umfeld.SCHALTER_ENV: "1"})
    for aus in ("0", "aus", "false"):
        assert not umfeld.freigeschaltet({umfeld.SCHALTER_ENV: aus})


def test_entscheid_147_modelle_nur_aus_drei_quellen():
    assert umfeld.QUELLEN_MODELLE == ("polyhaven", "kenney", "quaternius")
    # Ein Modell von ambientCG (dort nur Texturen zugelassen) oder Sketchfab wird abgewiesen.
    for quelle in ("ambientcg", "sketchfab"):
        with pytest.raises(umfeld.LizenzFehler):
            umfeld.pruefe_lizenz(dict(umfeld.asset("shrub_02"), quelle=quelle))
    # Eine Textur von Kenney ebenso; ambientCG-Textur geht (Entscheid 107).
    with pytest.raises(umfeld.LizenzFehler):
        umfeld.pruefe_lizenz(dict(umfeld.asset("Grass004"), quelle="kenney", paket=None))
    umfeld.pruefe_lizenz(umfeld.asset("Grass004"))
    assert {e["quelle"] for e in umfeld.ASSETS if e["art"] == "modell"} <= set(umfeld.QUELLEN_MODELLE)


def test_ausgeschaltet_wird_nichts_geladen(tmp_path):
    gerufen = []
    with pytest.raises(umfeld.GesperrtFehler) as fehler:
        umfeld.hole_asset("shrub_02", wurzel=tmp_path, oeffner=gerufen.append,
                          umgebung={umfeld.SCHALTER_ENV: "0"})
    assert gerufen == []
    assert umfeld.SCHALTER_ENV in str(fehler.value)


def _polyhaven_fixture(asset_id: str, dateien: dict) -> tuple[dict, dict]:
    """Eine synthetische Antwort von ``/files/<id>`` (Aufbau wie am 24.10.2026) und die Bytes."""
    haupt = b'{"asset": {"version": "2.0"}}'
    netz = {}
    include = {}
    for rel, inhalt in dateien.items():
        url = f"https://dl.example.invalid/{asset_id}/{rel}"
        include[rel] = {"url": url, "md5": hashlib.md5(inhalt).hexdigest(), "size": len(inhalt)}  # noqa: S324
        netz[url] = inhalt
    haupt_url = f"https://dl.example.invalid/{asset_id}/{asset_id}_1k.gltf"
    netz[haupt_url] = haupt
    api = {"gltf": {"1k": {"gltf": {"url": haupt_url, "md5": hashlib.md5(haupt).hexdigest(),  # noqa: S324
                                    "size": len(haupt), "include": include}}}}
    netz[f"https://api.polyhaven.com/files/{asset_id}"] = json.dumps(api).encode()
    return api, netz


def test_laden_mit_pruefsumme_und_dann_ohne_netz(tmp_path):
    _, netz = _polyhaven_fixture("shrub_02", {"shrub_02.bin": b"\x00" * 64,
                                             "textures/shrub_02_diff_1k.jpg": b"jpg"})
    geholt = umfeld.hole_asset("shrub_02", wurzel=tmp_path, oeffner=netz.__getitem__,
                               umgebung={umfeld.SCHALTER_ENV: "1"})
    assert geholt["aus_speicher"] is False and geholt["geladen_bytes"] > 0
    assert geholt["lizenz"] == umfeld.LIZENZ_CC0 and geholt["quelle_name"] == "Poly Haven"
    assert (Path(geholt["ordner"]) / "textures" / "shrub_02_diff_1k.jpg").read_bytes() == b"jpg"

    def kein_netz(url):
        raise OSError("offline")
    # Ohne Netz und sogar ausgeschaltet: was im Speicher liegt, geht.
    wieder = umfeld.hole_asset("shrub_02", wurzel=tmp_path, oeffner=kein_netz,
                               umgebung={umfeld.SCHALTER_ENV: "0"})
    assert wieder["aus_speicher"] is True and wieder["geladen_bytes"] == 0


def test_falsche_pruefsumme_wird_abgewiesen(tmp_path):
    _, netz = _polyhaven_fixture("shrub_02", {"shrub_02.bin": b"\x00" * 64})
    url = next(u for u in netz if u.endswith(".bin"))
    netz[url] = b"anders"
    with pytest.raises(umfeld.NetzFehler):
        umfeld.hole_asset("shrub_02", wurzel=tmp_path, oeffner=netz.__getitem__,
                          umgebung={umfeld.SCHALTER_ENV: "1"})
    assert umfeld.im_speicher("shrub_02", wurzel=tmp_path) is None


def test_fremder_pfad_in_der_antwort_wird_abgewiesen(tmp_path):
    _, netz = _polyhaven_fixture("shrub_02", {"../../ausserhalb.bin": b"x"})
    with pytest.raises(umfeld.NetzFehler):
        umfeld.hole_asset("shrub_02", wurzel=tmp_path, oeffner=netz.__getitem__,
                          umgebung={umfeld.SCHALTER_ENV: "1"})
    assert not (tmp_path.parent / "ausserhalb.bin").exists()


def test_kein_netz_ist_ein_satz_kein_absturz(tmp_path):
    def kein_netz(url):
        raise OSError("Netz weg")
    with pytest.raises(umfeld.NetzFehler) as fehler:
        umfeld.hole_asset("shrub_02", wurzel=tmp_path, oeffner=kein_netz,
                          umgebung={umfeld.SCHALTER_ENV: "1"})
    assert "nicht geladen" in str(fehler.value)


def _kenney_zip() -> bytes:
    puffer = io.BytesIO()
    with zipfile.ZipFile(puffer, "w") as z:
        z.writestr("License.txt", "License: (Creative Commons Zero, CC0)")
        z.writestr("Models/GLB format/sedan.glb", b"glTF-synthetisch")
        z.writestr("Models/GLB format/Textures/colormap.png", b"png")
        z.writestr("Models/OBJ format/sedan.obj", b"o")
    return puffer.getvalue()


def test_paket_mit_sha256_und_nur_die_noetigen_dateien(tmp_path, monkeypatch):
    daten = _kenney_zip()
    paket = dict(umfeld.PAKETE["kenney-car-kit"], sha256=hashlib.sha256(daten).hexdigest())
    monkeypatch.setitem(umfeld.PAKETE, "kenney-car-kit", paket)
    geholt = umfeld.hole_asset("kenney-sedan", wurzel=tmp_path,
                               oeffner={paket["url"]: daten}.__getitem__,
                               umgebung={umfeld.SCHALTER_ENV: "1"})
    ordner = Path(geholt["ordner"])
    assert geholt["haupt"] == "sedan.glb" and (ordner / "sedan.glb").is_file()
    assert (ordner / "Textures" / "colormap.png").is_file()
    assert (ordner / "License.txt").is_file()
    assert not any(p.suffix == ".obj" for p in tmp_path.rglob("*"))


def test_paket_mit_anderer_pruefsumme_wird_abgewiesen(tmp_path):
    paket = umfeld.PAKETE["kenney-car-kit"]
    with pytest.raises(umfeld.NetzFehler) as fehler:
        umfeld.hole_asset("kenney-sedan", wurzel=tmp_path,
                          oeffner={paket["url"]: _kenney_zip()}.__getitem__,
                          umgebung={umfeld.SCHALTER_ENV: "1"})
    assert "Prüfsumme" in str(fehler.value)


def test_hole_plan_sammelt_fehler_als_saetze(tmp_path):
    plan = {"platzierungen": [{"asset": "shrub_02"}, {"asset": "tree_small_02"}],
            "strasse": None, "wiese": None}
    _, netz = _polyhaven_fixture("shrub_02", {"shrub_02.bin": b"\x01" * 8})
    geholt = umfeld.hole_plan(plan, wurzel=tmp_path, oeffner=netz.__getitem__,
                              umgebung={umfeld.SCHALTER_ENV: "1"})
    assert set(geholt["assets"]) == {"shrub_02"}
    assert "tree_small_02" in geholt["fehlend"]
    assert any("CC0" in s for s in geholt["saetze"])


# ============================================================ der Plan

HAUS = ((0.0, 0.0), (10.0, 8.0))
KAMERAS = [{"kuerzel": "s", "auge": [5.0, -40.0, 1.7]}, {"kuerzel": "e", "auge": [45.0, 4.0, 1.7]}]


def _flach(seite=30.0):
    return umfeld.Gelaende([((-seite, -seite, -0.2), (seite, seite, 0.0))])


def _plan(**kw):
    werte = dict(gelaende=_flach(), bauwerk_boxen=[HAUS], haupt_box=HAUS, kameras=KAMERAS,
                 kategorien=list(umfeld.KATEGORIEN), dichte="viel", seed=4)
    werte.update(kw)
    return umfeld.plane(**werte)


def test_nichts_im_haus_und_abstand_gehalten():
    plan = _plan()
    assert plan["platzierungen"]
    for p in plan["platzierungen"]:
        abstand = umfeld._abstand_box(p["x"], p["y"], HAUS)
        assert abstand >= umfeld.ABSTAND_HAUS_M + min(p["radius_m"], 1.2) - 1e-6, p


def test_sichtkegel_bleiben_frei():
    plan = _plan()
    for p in plan["platzierungen"]:
        r = p["radius_m"] if p["kategorie"] != "autos" else min(p["radius_m"], 1.2)
        for k in KAMERAS:
            poly = umfeld.sichtkegel(k["auge"], HAUS)
            if _vor_dem_haus(p, k, HAUS):
                continue
            assert umfeld._abstand_polygon(p["x"], p["y"], poly) >= r + umfeld.SICHT_RAND_M - 1e-6, p


def _vor_dem_haus(p, k, haus) -> bool:
    """Mac-Befund 25.10.2026: Ein Auto darf im Blick einer Kamera stehen, wenn es dort nur den Sockel deckt — dann
    nennt es die Kamera in ``vor_dem_haus``, und die Regel hält nachgemessen. Bäume und Büsche nie."""
    if p["kategorie"] != "autos" or k.get("kuerzel") not in (p.get("vor_dem_haus") or ()):
        return False
    r = min(p["radius_m"], 1.2) if not p.get("parkiert") else p["radius_m"]
    assert umfeld._auto_nur_sockel(k["auge"], p["x"], p["y"], r, haus, 0.0), (k, p)
    return True


def test_derselbe_startwert_derselbe_plan_ein_anderer_ein_anderer():
    assert _plan(seed=11) == _plan(seed=11)
    assert _plan(seed=11)["platzierungen"] != _plan(seed=12)["platzierungen"]


def test_auf_der_hoehe_des_gelaendes():
    # Ein Hang: z = 0,1·x, aus zwei Dreiecken.
    def z(x, y):
        return 0.1 * x
    ecken = [(-30, -30), (30, -30), (30, 30), (-30, 30)]
    p3 = [(x, y, z(x, y)) for x, y in ecken]
    hang = umfeld.Gelaende([((-30, -30, -3), (30, 30, 3))],
                           dreiecke=[(p3[0], p3[1], p3[2]), (p3[0], p3[2], p3[3])])
    plan = _plan(gelaende=hang, kategorien=["baeume", "buesche"])
    assert plan["platzierungen"]
    for p in plan["platzierungen"]:
        assert math.isclose(p["z"], z(p["x"], p["y"]), abs_tol=1e-3), p


def test_ohne_gelaende_nichts_und_ein_satz():
    plan = _plan(gelaende=umfeld.Gelaende([]))
    assert plan["platzierungen"] == [] and plan["strasse"] is None
    assert any("kein Gelände" in s for s in plan["saetze"])


def test_strasse_auf_der_seite_der_ersten_kamera_und_autos_darauf():
    plan = _plan(kategorien=["strasse", "autos"], dichte="viel")
    s = plan["strasse"]
    assert s["seite"] == "s" and s["achse"] == "x"
    (x0, y0), (x1, y1) = s["box"]
    assert y1 <= HAUS[0][1] - umfeld.ABSTAND_HAUS_M
    autos = [p for p in plan["platzierungen"] if p["kategorie"] == "autos"]
    assert autos
    for a in autos:
        assert y0 <= a["y"] <= y1 and x0 <= a["x"] <= x1
        assert a["drehung_grad"] in (90.0, 270.0)
    # Die Kamera im Osten zuerst: die Strasse liegt im Osten.
    ost = _plan(kategorien=["strasse"], kameras=list(reversed(KAMERAS)))
    assert ost["strasse"]["seite"] == "e" and ost["strasse"]["achse"] == "y"


def test_eine_strasse_im_modell_wird_genommen():
    plan = _plan(kategorien=["strasse", "autos"], strassen_boxen=[((-30, 20), (30, 26))])
    assert plan["strasse"]["aus_modell"] is True
    assert "asset" not in plan["strasse"]


def test_anzahl_schlaegt_die_dichte():
    plan = _plan(kategorien=["baeume", "autos", "strasse"], anzahl={"baeume": 3, "autos": 1})
    assert plan["zaehlung"]["baeume"] == 3 and plan["zaehlung"]["autos"] == 1


def test_zu_wenig_platz_wird_gesagt():
    plan = _plan(gelaende=_flach(9.0), kategorien=["baeume"], anzahl={"baeume": 12})
    assert plan["zaehlung"]["baeume"] < 12
    assert any("fanden Platz" in s for s in plan["saetze"])


def test_grosses_situationsmodell_bleibt_beim_haus_und_gedeckelt():
    """Anlass: das erste echte Situationsmodell am Heim-PC misst rund 577 × 500 × 26 m (flach, 111 Platten,
    drei Geländeknoten). Geplant wird nur im Umkreis um das Haus, die Zahl je Kategorie ist gedeckelt, und der
    Sichtkegel gilt auch für eine Kamera aus der Vogelschau."""
    gelaende = umfeld.Gelaende([((-288.0, -250.0, -0.5), (289.0, 250.0, 0.0)),
                                ((-288.0, -250.0, -0.5), (0.0, 0.0, 0.0)),
                                ((0.0, 0.0, -0.5), (289.0, 250.0, 0.0))])
    haus = ((-10.0, -8.0), (12.0, 7.0))
    nachbarn = [((40.0, 30.0), (70.0, 55.0)), ((-90.0, -60.0), (-60.0, -40.0))]
    kameras = [{"kuerzel": "s", "auge": [1.0, -60.0, 1.7]},
               {"kuerzel": "vogel", "auge": [60.0, -60.0, 120.0]}]
    plan = umfeld.plane(gelaende=gelaende, bauwerk_boxen=[haus, *nachbarn], haupt_box=haus, kameras=kameras,
                        kategorien=list(umfeld.KATEGORIEN), dichte="viel", seed=3)
    z = plan["zaehlung"]
    assert z["baeume"] <= umfeld.HOECHSTENS["baeume"] and z["buesche"] <= umfeld.HOECHSTENS["buesche"]
    assert z["autos"] <= umfeld.DICHTE_AUTOS["viel"]
    rand = plan["umkreis_m"]
    assert umfeld.UMKREIS_MIN_M <= rand <= umfeld.UMKREIS_MAX_M
    for p in plan["platzierungen"]:
        assert haus[0][0] - rand <= p["x"] <= haus[1][0] + rand, p
        assert haus[0][1] - rand <= p["y"] <= haus[1][1] + rand, p
        r = p["radius_m"] if p["kategorie"] != "autos" else min(p["radius_m"], 1.2)
        for k in kameras:
            poly = umfeld.sichtkegel(k["auge"], haus)
            if _vor_dem_haus(p, k, haus):
                continue
            assert umfeld._abstand_polygon(p["x"], p["y"], poly) >= r + umfeld.SICHT_RAND_M - 1e-6, (k, p)
        for b in nachbarn:
            assert umfeld._abstand_box(p["x"], p["y"], b) >= umfeld.ABSTAND_HAUS_M + min(p["radius_m"], 1.2) - 1e-6
    # Die Strasse liegt am Rand des Umkreises, nicht 250 m weg am Rand des Grundstücks.
    (sx0, sy0), (sx1, sy1) = plan["strasse"]["box"]
    assert sy0 >= haus[0][1] - rand - 1e-6 and sx1 - sx0 <= (haus[1][0] - haus[0][0]) + 2 * rand + 1e-6


def test_plan_aus_einer_glb(tmp_path):
    pfad = _testszene(tmp_path)
    plan = umfeld.plane_fuer_glb(pfad, wunsch={"kategorien": ["baeume", "strasse", "autos"],
                                               "dichte": "mittel", "seed": 2})
    assert plan["gelaende_namen"] == ["Gelaende"] and plan["hoehe_aus"] == "dreiecke"
    assert plan["zaehlung"]["baeume"] > 0 and plan["strasse"] is not None
    # Haus (glb) liegt in der Welt bei x 0..10, y 0..8.
    for p in plan["platzierungen"]:
        assert umfeld._abstand_box(p["x"], p["y"], HAUS) >= umfeld.ABSTAND_HAUS_M


def test_strasse_der_glb_wird_erkannt(tmp_path):
    pfad = _testszene(tmp_path, strasse=True)
    gelesen = umfeld.lies_glb_umfeld(pfad)
    assert gelesen["strassen_namen"] == ["Strasse Sued"]
    plan = umfeld.plane_fuer_glb(pfad, wunsch={"kategorien": ["autos"], "dichte": "wenig",
                                               "seed": 0})
    assert plan["strasse"]["aus_modell"] is True


def test_glb_ohne_gelaende(tmp_path):
    plan = umfeld.plane_fuer_glb(_testszene(tmp_path, mit_gelaende=False),
                                 wunsch={"kategorien": ["baeume"], "dichte": "wenig", "seed": 0})
    assert plan["platzierungen"] == []


# ============================================================ die Bestellung

def _szene(vis_extra=None, **oben):
    s = {"schema": kosmo_szene.SCHEMA_SZENE, "geometry": {"path": "m.glb", "format": "glb"},
         "render": {"resolution": [64, 64], "samples": 1}, "style": {"prompt": "a house"},
         "vis": {"backbone": "z-image-turbo", **(vis_extra or {})}}
    s.update(oben)
    return s


def test_lies_wunsch():
    w, m = umfeld.lies_wunsch({"kategorien": ["autos", "baeume"], "dichte": "wenig", "seed": 3})
    assert m == [] and w == {"kategorien": ["baeume", "autos"], "dichte": "wenig", "seed": 3}
    for falsch in ({"kategorien": []}, {"kategorien": ["palmen"]},
                   {"kategorien": ["baeume"], "dichte": "dicht"},
                   {"kategorien": ["baeume"], "seed": -1},
                   {"kategorien": ["baeume"], "farbe": "gruen"},
                   {"kategorien": ["baeume"], "anzahl": {"baeume": 99}}, "baeume"):
        w, m = umfeld.lies_wunsch(falsch)
        assert w is None and m, falsch


def test_vis_umfeld_ist_ein_bekanntes_feld():
    gelesen = kosmo_szene.lies_szene(_szene({"umfeld": {"kategorien": ["baeume"]}}))
    assert not any("Unbekannte Felder" in s for s in gelesen["maengel"])
    assert gelesen["umfeld"] == {"kategorien": ["baeume"], "dichte": "mittel", "seed": 0}
    assert "umfeld" in kosmo_szene.DURCHGEREICHT
    falsch = kosmo_szene.lies_szene(_szene({"umfeld": {"kategorien": ["palmen"]}}))
    assert any("palmen" in s for s in falsch["maengel"]) and falsch["umfeld"] is None
    ohne = kosmo_szene.lies_szene(_szene())
    assert ohne["umfeld"] is None


def test_mit_skizze_wirkt_das_umfeld_nicht():
    gelesen = kosmo_szene.lies_szene(_szene({"umfeld": {"kategorien": ["baeume"]}},
                                            skizze={"quelle": "mappe", "name": "s.png"}))
    assert gelesen["umfeld"] is None
    assert any("Umfeld" in s for s in gelesen["warnungen"])


def test_ausgestattete_und_leere_grundlage_sind_zwei():
    assert "umfeld" in abholer.GRUNDLAGE_MUSS_PASSEN
    alt = {"umfeld": {"kategorien": ["baeume"], "dichte": "mittel", "seed": 0}}
    assert abholer.grundlage_weicht_ab(alt, {"umfeld": None}) == ["umfeld"]
    assert abholer.grundlage_weicht_ab(alt, dict(alt)) == []


def test_kommando_traegt_das_umfeld(tmp_path):
    datei = tmp_path / "umfeld.json"
    datei.write_text("{}")
    cmd = seams.baue_kommando_multipass(tmp_path / "m.glb", tmp_path, up_axis="Y",
                                        umfeld_json=datei)
    assert cmd[cmd.index("--umfeld") + 1] == str(datei)
    ohne = seams.baue_kommando_multipass(tmp_path / "m.glb", tmp_path, up_axis="Y")
    assert "--umfeld" not in ohne


# ============================================================ der Abholer

def _speicher_fuellen(wurzel: Path, kennungen):
    for k in kennungen:
        e = umfeld.asset(k)
        basis = wurzel / e["quelle"] / k
        basis.mkdir(parents=True)
        if e["art"] == "modell":
            (basis / "a.glb").write_bytes(b"x")
            herkunft = {"id": k, "dateien": ["a.glb"], "haupt": "a.glb"}
        else:
            (basis / "c.jpg").write_bytes(b"x")
            herkunft = {"id": k, "dateien": ["c.jpg"], "karten": {"Color": "c.jpg"}}
        herkunft.update(lizenz=e["lizenz"], quelle=e["quelle"], seite=e["seite"],
                        kategorie=e["kategorie"])
        (basis / umfeld.HERKUNFT_DATEI).write_text(json.dumps(herkunft))


def test_abholer_ausgeschaltet_rechnet_ohne_und_sagt_es(tmp_path):
    szene = {"umfeld": {"kategorien": ["baeume"], "dichte": "wenig", "seed": 0}}
    aus = abholer.umfeld_vorbereiten(tmp_path / "job", szene, _testszene(tmp_path),
                                     umgebung={umfeld.ORDNER_ENV: str(tmp_path / "speicher"),
                                               umfeld.SCHALTER_ENV: "0"})
    assert aus["datei"] is None
    assert any(umfeld.SCHALTER_ENV in s for s in aus["bericht"]["saetze"])


def test_abholer_mit_speicher_legt_den_plan_ab_ohne_pfade_im_bericht(tmp_path):
    speicher = tmp_path / "speicher"
    _speicher_fuellen(speicher, ["tree_small_02", "island_tree_02", "Grass004"])
    szene = {"umfeld": {"kategorien": ["baeume", "wiese"], "dichte": "wenig", "seed": 1}}
    aus = abholer.umfeld_vorbereiten(tmp_path / "job", szene, _testszene(tmp_path),
                                     umgebung={umfeld.ORDNER_ENV: str(speicher)})
    satz = json.loads(Path(aus["datei"]).read_text())
    assert satz["schema"] == umfeld.DATEI_SCHEMA and satz["plan"]["platzierungen"]
    assert satz["plan"]["wiese"]["asset"] == "Grass004"
    for p in satz["plan"]["platzierungen"]:
        assert Path(satz["assets"][p["asset"]]["datei"]).is_file()
    bericht = json.dumps(aus["bericht"])
    assert str(speicher) not in bericht and str(tmp_path) not in bericht
    assert all(a["lizenz"] == "CC0-1.0" for a in aus["bericht"]["assets"])
    # Und im Ergebnis unter `angewandt.umfeld`, mit dem, was Blender je Kamera stellte.
    angewandt = abholer.angewandt_der_szene(
        dict(szene, umfeld_angewandt=aus["bericht"]),
        umfeld_je_kamera={"s": {"gestellt": {"baeume": 2}}})
    assert angewandt["umfeld"]["gestellt_je_kamera"]["s"]["gestellt"] == {"baeume": 2}


# ============================================================ Blender nur als Prozess

def test_kern_ohne_bpy_und_der_runner_stellt_das_umfeld():
    kern = (WURZEL / "src" / "aiimaging" / "umfeld.py").read_text(encoding="utf-8")
    assert "import bpy" not in kern and "bl_info" not in kern
    runner = (WURZEL / "src" / "aiimaging" / "runners" / "blender_depth_stage.py").read_text(
        encoding="utf-8")
    assert '"--umfeld"' in runner and "def _umfeld_laden" in runner
    # Die Namen kommen aus dem Kern, nicht aus dem Runner.
    assert "umfeld.material_name" in runner
    # Die Materialwahl und das graue Gelaende lassen das Umfeld aus.
    assert runner.count("not _ist_umfeld_objekt(") >= 3


# ============================================================ Claude: das MCP-Werkzeug

def test_mcp_werkzeug_plant_ohne_zu_laden(tmp_path, monkeypatch):
    from aiimaging.mcp_schemas import WERKZEUG_UMFELD, WERKZEUGE
    from aiimaging.mcp_server import rufe_werkzeug
    werkzeug = WERKZEUGE[WERKZEUG_UMFELD]
    assert werkzeug["readonly"] is True
    assert werkzeug["inputSchema"]["required"] == ["glb_path", "kategorien"]
    assert set(werkzeug["inputSchema"]["properties"]["kategorien"]["items"]["enum"]) \
        == set(umfeld.KATEGORIEN)
    monkeypatch.setenv(umfeld.SCHALTER_ENV, "0")
    monkeypatch.setenv(umfeld.ORDNER_ENV, str(tmp_path / "speicher"))
    aus = rufe_werkzeug(WERKZEUG_UMFELD, {"glb_path": str(_testszene(tmp_path)),
                                          "kategorien": ["baeume", "autos", "strasse"],
                                          "dichte": "wenig", "seed": 5})
    assert aus["error"] is None and aus["zaehlung"]["baeume"] > 0
    assert aus["assets"] and all(a["lizenz"] == "CC0-1.0" for a in aus["assets"])
    assert not any(a["im_speicher"] for a in aus["assets"])
    assert any(umfeld.SCHALTER_ENV in s for s in aus["saetze"])
    assert not (tmp_path / "speicher").exists()          # nichts geladen
    falsch = rufe_werkzeug(WERKZEUG_UMFELD, {"glb_path": "x.glb", "kategorien": ["palmen"]})
    assert falsch["error"]


@pytest.mark.parametrize("hochachse", ["Y_UP", "Y", None])
def test_abholer_plant_auch_mit_der_hochachse_der_bruecke(tmp_path, hochachse):
    """Ergebnis 355 ROT: Die Brücke gibt ohne eigene Angabe «Y_UP» weiter (ANGENOMMENE_HOCHACHSE);
    ``umfeld.plane_fuer_glb`` kennt nur «Y» — jeder Auftrag vom Mac blieb ohne Umfeld
    («Umfeld nicht geplant: GlbError: up_axis='Y_UP' …»). Wie die Rahmung vom 08.10.2026 über
    ``_glb_hochachse``."""
    speicher = tmp_path / "speicher"
    _speicher_fuellen(speicher, ["tree_small_02", "island_tree_02", "Grass004"])
    szene = {"umfeld": {"kategorien": ["baeume", "wiese"], "dichte": "wenig", "seed": 1}}
    aus = abholer.umfeld_vorbereiten(tmp_path / "job", szene, _testszene(tmp_path),
                                     hochachse=hochachse,
                                     umgebung={umfeld.ORDNER_ENV: str(speicher)})
    assert not any("nicht geplant" in s for s in (aus["bericht"] or {}).get("saetze", []))
    assert aus["datei"] is not None
