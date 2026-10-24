"""Knoten «Umfeld», Ergebnis auf-20261024-358: Auto ohne Farbe und angeschnitten, Situationsmodell ohne Bäume.

Drei Befunde, drei Proben — alles ohne Netz und ohne Blender, die Kenney-artige glb wird hier gebaut
(Aufbau wie ``sedan.glb`` aus dem Car Kit: fünf Wurzeln, Farbe als Datei daneben; Inhalt erfunden):

1. Das Auto: Die Datei ist EIN Stück aus fünf Wurzeln (``ein_stueck``), und jeder Verweis der glb auf
   eine Datei daneben wird geprüft — fehlt sie, holt der Speicher sie aus dem geprüften Paket nach
   oder sagt es in einem Satz.
2. Der Bildrahmen: Ein Auto steht ganz im Bild einer Kamera und in keiner angeschnitten — oder gar nicht.
3. Das Situationsmodell: geplant um die einzelnen Bauten im Bild der Kamera, nicht um die Box aller
   Platten; und jede Kategorie mit 0 trägt ihren Grund.
"""
from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import math
import struct
import zipfile
from pathlib import Path

import pytest

from aiimaging import abholer, kameras, umfeld

WURZEL = Path(__file__).resolve().parents[1]


def _make_glb():
    spez = importlib.util.spec_from_file_location("make_test_glb_rahmen",
                                                  WURZEL / "tools" / "make_test_glb.py")
    m = importlib.util.module_from_spec(spez)
    spez.loader.exec_module(m)
    return m


# ============================================================ 1. das Auto: ein Stück, mit Farbe

def _kenney_artige_glb(textur_uri="Textures/colormap.png") -> bytes:
    """Fünf Wurzeln (Karosserie, vier Räder) und eine Farbe als Datei daneben — wie Kenney."""
    js = {"asset": {"version": "2.0"}, "scene": 0,
          "scenes": [{"nodes": [0, 1, 2, 3, 4], "name": "sedan"}],
          "nodes": [{"name": "wheel-front-right", "translation": [-0.3, 0.3, 0.66]},
                    {"name": "body", "translation": [0.0, 0.15, 0.0]},
                    {"name": "wheel-back-left", "translation": [0.3, 0.3, -0.66]},
                    {"name": "wheel-back-right", "translation": [-0.3, 0.3, -0.66]},
                    {"name": "wheel-front-left", "translation": [0.3, 0.3, 0.66]}],
          "images": [{"uri": textur_uri, "name": "colormap"}],
          "textures": [{"source": 0}],
          "materials": [{"name": "colormap",
                         "pbrMetallicRoughness": {"baseColorTexture": {"index": 0}}}],
          "buffers": [{"byteLength": 4}]}
    roh = json.dumps(js).encode("utf-8")
    roh += b" " * ((4 - len(roh) % 4) % 4)
    binaer = b"\x00" * 4
    gesamt = 12 + 8 + len(roh) + 8 + len(binaer)
    return (struct.pack("<III", 0x46546C67, 2, gesamt) + struct.pack("<II", len(roh), 0x4E4F534A)
            + roh + struct.pack("<II", len(binaer), 0x004E4942) + binaer)


def _kit_zip(*, mit_textur=True) -> bytes:
    puffer = io.BytesIO()
    with zipfile.ZipFile(puffer, "w") as z:
        z.writestr("License.txt", "License: (Creative Commons Zero, CC0)")
        z.writestr("Models/GLB format/sedan.glb", _kenney_artige_glb())
        if mit_textur:
            z.writestr("Models/GLB format/Textures/colormap.png", b"\x89PNG-synthetisch")
    return puffer.getvalue()


def _paket(monkeypatch, daten):
    paket = dict(umfeld.PAKETE["kenney-car-kit"], sha256=hashlib.sha256(daten).hexdigest())
    monkeypatch.setitem(umfeld.PAKETE, "kenney-car-kit", paket)
    return paket


def test_kenney_autos_sind_ein_stueck_und_der_runner_liest_es():
    autos = [e for e in umfeld.ASSETS if e["quelle"] == "kenney"]
    assert autos and all(e.get("ein_stueck") is True for e in autos)
    # Poly Haven legt Varianten nebeneinander — dort bleibt jede Wurzel eine Variante.
    assert not any(e.get("ein_stueck") for e in umfeld.ASSETS if e["quelle"] == "polyhaven")
    runner = (WURZEL / "src" / "aiimaging" / "runners" / "blender_depth_stage.py").read_text(
        encoding="utf-8")
    assert 'ein_stueck=bool(info.get("ein_stueck"))' in runner
    assert "def _vorlage_laden(pfad: str, *, ein_stueck: bool = False)" in runner


def test_glb_verweise_werden_gelesen():
    assert umfeld.glb_bezuege(_kenney_artige_glb()) == ["Textures/colormap.png"]
    assert umfeld.glb_bezuege(_kenney_artige_glb("Textures/farbe%20karte.png")) == [
        "Textures/farbe karte.png"]
    assert umfeld.glb_bezuege(b"kein glb") == []
    eingebettet = _kenney_artige_glb("data:image/png;base64,AAAA")
    assert umfeld.glb_bezuege(eingebettet) == []


def test_textur_kommt_mit_und_fuer_blender_traegt_ein_stueck(tmp_path, monkeypatch):
    daten = _kit_zip()
    paket = _paket(monkeypatch, daten)
    geholt = umfeld.hole_asset("kenney-sedan", wurzel=tmp_path,
                               oeffner={paket["url"]: daten}.__getitem__,
                               umgebung={umfeld.SCHALTER_ENV: "1"})
    ordner = Path(geholt["ordner"])
    assert (ordner / "Textures" / "colormap.png").is_file()
    assert geholt["bezuege_fehlend"] == []
    assert umfeld.fehlende_bezuege(ordner / "sedan.glb") == []
    plan = {"platzierungen": [{"asset": "kenney-sedan", "kategorie": "autos"}], "strasse": None,
            "wiese": None}
    satz = umfeld.fuer_blender(plan, {"assets": {"kenney-sedan": geholt}})
    assert satz["assets"]["kenney-sedan"]["ein_stueck"] is True


def test_fehlende_textur_wird_ohne_netz_aus_dem_paket_nachgeholt(tmp_path, monkeypatch):
    daten = _kit_zip()
    paket = _paket(monkeypatch, daten)
    umfeld.hole_asset("kenney-sedan", wurzel=tmp_path, oeffner={paket["url"]: daten}.__getitem__,
                      umgebung={umfeld.SCHALTER_ENV: "1"})
    textur = tmp_path / "kenney" / "kenney-sedan" / "Textures" / "colormap.png"
    textur.unlink()                                      # ein älterer Speicherstand ohne Farbe
    assert umfeld.im_speicher("kenney-sedan", wurzel=tmp_path)["bezuege_fehlend"] == [
        "Textures/colormap.png"]

    def kein_netz(url):
        raise AssertionError(f"kein Netz erwartet: {url}")
    wieder = umfeld.hole_asset("kenney-sedan", wurzel=tmp_path, oeffner=kein_netz,
                               umgebung={umfeld.SCHALTER_ENV: "0"})
    assert textur.is_file() and wieder["bezuege_fehlend"] == [] and wieder["geladen_bytes"] == 0


def test_fehlt_die_textur_auch_im_paket_steht_es_als_satz(tmp_path, monkeypatch):
    daten = _kit_zip(mit_textur=False)
    paket = _paket(monkeypatch, daten)
    plan = {"platzierungen": [{"asset": "kenney-sedan"}], "strasse": None, "wiese": None}
    geholt = umfeld.hole_plan(plan, wurzel=tmp_path, oeffner={paket["url"]: daten}.__getitem__,
                              umgebung={umfeld.SCHALTER_ENV: "1"})
    assert "kenney-sedan" in geholt["assets"]            # das Auto bleibt — nur ohne Farbe
    satz = [s for s in geholt["saetze"] if "colormap.png" in s]
    assert satz and "ohne seine Farbe" in satz[0]


# ============================================================ 2. der Bildrahmen

KAMERA_S = {"kuerzel": "s", "auge": [5.0, -30.0, 1.7], "blick_auf": [5.0, 4.0, 1.7],
            "brennweite_mm": 35.0, "seitenverhaeltnis": 16 / 9}


def test_im_rahmen_ganz_angeschnitten_aussen():
    r = umfeld.kamera_rahmen(KAMERA_S)
    assert umfeld.im_rahmen(r, (5.0, 0.0, 1.7))
    assert not umfeld.im_rahmen(r, (5.0, -40.0, 1.7))   # hinter der Kamera
    mitte = umfeld._auto_ecken(5.0, 0.0, 0.0, 90.0, 4.6)
    assert umfeld.lage_im_bild([r], mitte) == "ganz"
    # Am linken Rand: halbe Bildbreite bei 30 m Tiefe = 30 · 18/35 ≈ 15,4 m.
    rand = umfeld._auto_ecken(5.0 - 15.4, 0.0, 0.0, 90.0, 4.6)
    assert umfeld.lage_im_bild([r], rand) == "angeschnitten"
    weit = umfeld._auto_ecken(60.0, 0.0, 0.0, 90.0, 4.6)
    assert umfeld.lage_im_bild([r], weit) == "aussen"
    # Hinter dem Haus: ganz im Bild, aber verdeckt.
    hinten = umfeld._auto_ecken(5.0, 20.0, 0.0, 90.0, 4.6)
    assert umfeld.lage_im_bild([r], hinten, verdeckt_durch=((0.0, 0.0), (10.0, 8.0))) == "verdeckt"
    # Shift nach oben: der untere Rand rückt herauf.
    hoch = umfeld.kamera_rahmen(dict(KAMERA_S, shift_y=0.2))
    assert umfeld.im_rahmen(r, (5.0, 0.0, -2.0)) and not umfeld.im_rahmen(hoch, (5.0, 0.0, -2.0))
    # Ohne Blickziel gibt es keinen Rahmen (dann prüft der Plan nur den Sichtkegel).
    assert umfeld.kamera_rahmen({"kuerzel": "x", "auge": [0, 0, 1.7]}) is None


def _alle_autos_ganz(plan, kams, haus=None):
    rahmen = [umfeld.kamera_rahmen(k) for k in kams]
    autos = [p for p in plan["platzierungen"] if p["kategorie"] == "autos"]
    for a in autos:
        ecken = umfeld._auto_ecken(a["x"], a["y"], a["z"], a["drehung_grad"], a["laenge_m"])
        assert umfeld.lage_im_bild(rahmen, ecken, verdeckt_durch=haus) == "ganz", a
    return autos


@pytest.mark.parametrize("seed", [0, 1, 2, 3])
def test_autos_stehen_ganz_im_bild_oder_gar_nicht(seed):
    haus = ((0.0, 0.0), (10.0, 8.0))
    gelaende = umfeld.Gelaende([((-30.0, -30.0, -0.2), (30.0, 30.0, 0.0))])
    plan = umfeld.plane(gelaende=gelaende, bauwerk_boxen=[haus], haupt_box=haus, kameras=[KAMERA_S],
                        kategorien=["strasse", "autos"], dichte="viel", seed=seed)
    autos = _alle_autos_ganz(plan, [KAMERA_S], haus)
    if len(autos) < plan["ziel"]["autos"]:
        assert any("Auto" in s and ("Nur" in s or "Keine" in s) for s in plan["saetze"]), plan["saetze"]


def test_auf_der_glb_mit_der_bestellten_kamera_ganz_im_bild(tmp_path):
    """Wie das Demohaus mit Grundbild sSE: die Auto-Kamera aus dem Plan, Autos ganz im Bild."""
    pfad = tmp_path / "haus.glb"
    pfad.write_bytes(_make_glb().baue_glb([("Gelaende", (-30.0, -0.2, -30.0), (30.0, 0.0, 30.0)),
                                           ("Haus", (0.0, 0.0, -8.0), (10.0, 6.0, 0.0))]))
    for seed in range(3):
        plan = umfeld.plane_fuer_glb(pfad, wunsch={"kategorien": ["strasse", "autos"],
                                                   "dichte": "mittel", "seed": seed},
                                     richtungen=("sSE",))
        haupt = umfeld.lies_glb_umfeld(pfad)["haupt_box"]
        satz = kameras.kamerasatz(haupt, kuerzel=["sSE"], brennweite_mm=35.0,
                                  seitenverhaeltnis=umfeld.SEITENVERHAELTNIS_VORGABE)["kameras"][0]
        kam = {"auge": satz["auge"], "blick_auf": satz["blick_auf"], "brennweite_mm": 35.0,
               "shift_mm": satz.get("shift_mm"), "seitenverhaeltnis": umfeld.SEITENVERHAELTNIS_VORGABE}
        autos = _alle_autos_ganz(plan, [kam], umfeld._box2(haupt))
        assert autos, plan["saetze"]                     # die Demo bekommt ein Auto
        for a in autos:
            assert umfeld._abstand_box(a["x"], a["y"], umfeld._box2(haupt)) >= umfeld.ABSTAND_HAUS_M


# ============================================================ 3. das Situationsmodell

def test_grundriss_cluster():
    """Ergebnis 359: Berühren genügt nicht — nur Geschosse übereinander (echte Überlappung) sind ein Bau;
    ein Haufen über 20 000 m² ist Boden, und eine Kette darf die Bauten darin nicht verschlucken."""
    platten = [((0.0, 0.0, 3.5 * g), (20.0, 10.0, 3.5 * g + 0.3)) for g in range(4)]
    nachbar = [((20.0, 0.0, 0.0), (30.0, 10.0, 6.0))]       # berührt nur: eigener Bau
    fern = [((80.0, 80.0, 0.0), (90.0, 90.0, 9.0))]
    belag = [((-40.0, -40.0, 0.0), (-20.0, -20.0, 0.1))]
    c = umfeld.grundriss_cluster(platten + nachbar + fern + belag)
    assert len(c) == 4
    assert c[0]["box"] == ((0.0, 0.0), (20.0, 10.0)) and c[0]["bau"] and c[0]["teile"] == [0, 1, 2, 3]
    assert [x["art"] for x in c if x["box"] == ((-40.0, -40.0), (-20.0, -20.0))] == ["belag"]
    # Eine grosse Platte mit Grundrissen darauf: die Platte ist Boden, die Grundrisse bleiben Bauten.
    platte = [((-200.0, -200.0, 0.0), (200.0, 200.0, 2.0))]
    auf = [((0.0, 0.0, 0.0), (30.0, 20.0, 2.0)), ((50.0, 50.0, 0.0), (70.0, 60.0, 2.0))]
    c = umfeld.grundriss_cluster(platte + auf)
    assert sorted(x["art"] for x in c) == ["bau", "bau", "boden"]


def _wettbewerbsartig(tmp_path):
    """Wie das Wettbewerbsmodell in 359, frei erfunden: zwei grosse 2-m-Platten, die sich berühren und fast die
    ganze Anlage decken, darauf 2-m-Grundrisse der Bauten (zwei davon aneinander)."""
    k = [("IfcSlab_Gelaende_A", (-300.0, -1.0, -250.0), (300.0, 0.0, 250.0)),
         ("IfcSlab_Platte_West", (-280.0, 0.0, -230.0), (0.0, 2.0, 230.0)),
         ("IfcSlab_Platte_Ost", (0.0, 0.0, -230.0), (280.0, 2.0, 230.0))]
    for n, (x, z, b, t) in enumerate(((-40.0, -20.0, 60.0, 40.0), (20.0, -20.0, 20.0, 40.0),
                                      (-150.0, 120.0, 30.0, 20.0), (150.0, -150.0, 40.0, 25.0),
                                      (120.0, 140.0, 25.0, 25.0))):
        k.append((f"IfcSlab_Grundriss_{n}", (x - b / 2, 0.0, z - t / 2), (x + b / 2, 2.0, z + t / 2)))
    pfad = tmp_path / "wettbewerbsartig.glb"
    pfad.write_bytes(_make_glb().baue_glb(k))
    return pfad


@pytest.mark.parametrize("anzahl", [None, {"baeume": 3, "autos": 2}])
def test_wettbewerbsartig_baeume_bei_den_bauten_im_bild(tmp_path, anzahl):
    """Ergebnis 359 ROT: «Keine Bäume: 0 bestellt.» bei Dichte mittel — die Platten verschmolzen zu einem Bau
    von fast der ganzen Anlage, und frei sichtbar blieben 0 m². Gegen den alten Stand: 0 Bäume, 0 Autos."""
    pfad = _wettbewerbsartig(tmp_path)
    kam = _vogel_auf([[-90.0, -40.0, 0.0], [60.0, 60.0, 10.0]])
    wunsch = {"kategorien": ["baeume", "autos"], "dichte": "mittel", "seed": 0}
    if anzahl:
        wunsch["anzahl"] = anzahl
    plan = umfeld.plane_fuer_glb(pfad, wunsch=wunsch, kameras=[kam])
    assert plan["situation"] and plan["bauten"]["boden"] == 2 and plan["bauten"]["im_bild"] >= 1
    assert plan["bauten"]["groesster_bau_m2"] < umfeld.BAU_MAX_FLAECHE_M2
    assert plan["freie_flaeche_m2"] > 0
    z = plan["zaehlung"]
    if anzahl:
        assert z == {"baeume": 3, "autos": 2}, plan["saetze"]
    else:
        assert 0 < z["baeume"] <= umfeld.HOECHSTENS["baeume"] and z["autos"] == umfeld.DICHTE_AUTOS["mittel"]
    assert not any("0 bestellt" in s for s in plan["saetze"])
    bauten = [c for c in umfeld.grundriss_cluster(umfeld.lies_glb_umfeld(pfad)["bauwerk_boxen"]) if c["bau"]]
    for p in plan["platzierungen"]:
        naechster = min(umfeld._abstand_box(p["x"], p["y"], c["box"]) for c in bauten)
        assert umfeld.ABSTAND_HAUS_M <= naechster <= umfeld.NAEHE_BAU_M + p["radius_m"], p
        # Auf der Platte, nicht im Gelände darunter.
        assert p.get("auf_platte") is True and math.isclose(p["z"], 2.0, abs_tol=1e-6), p
    _alle_autos_ganz(plan, [kam])


def test_freie_flaeche_null_ist_nicht_null_bestellt():
    """Ist das Ziel 0, weil im Bild kein freies Gelände bleibt, heisst der Satz so — nicht «0 bestellt»."""
    haus = ((0.0, 0.0), (10.0, 8.0))
    plan = umfeld.plane(gelaende=umfeld.Gelaende([((0.5, 0.5, -0.2), (9.5, 7.5, 0.0))]), bauwerk_boxen=[haus],
                        haupt_box=haus, kameras=[], kategorien=["baeume"], dichte="mittel", seed=0)
    assert plan["ziel"]["baeume"] == 0
    assert "Keine Bäume: Um das Haus bleibt kein freies Gelände." in plan["saetze"]
    assert not any("0 bestellt" in s for s in plan["saetze"])


def test_rueckfall_parkieren_steht_im_plan_und_im_satz(tmp_path):
    """Ergebnis 359 (a): Der Rückfall lief, fand aber keinen Platz — und sagte es nicht. Jetzt trägt jedes Auto
    ``parkiert``, der Plan ``parkieren``, und ein Satz sagt, warum es auch neben dem Haus nicht ging."""
    pfad = tmp_path / "eng.glb"
    # Ein Haus, das die Geländeplatte fast füllt — wie das Demohaus mit 8 m Gelände rundum.
    pfad.write_bytes(_make_glb().baue_glb([("Gelaende", (-8.0, -0.2, -18.0), (23.0, 0.0, 8.0)),
                                           ("Haus", (-0.5, 0.0, -10.5), (15.3, 8.6, 1.5))]))
    plan = umfeld.plane_fuer_glb(pfad, wunsch={"kategorien": ["autos"], "dichte": "viel", "seed": 7},
                                 richtungen=("sSE",), seitenverhaeltnis=1.6)
    assert all(isinstance(p.get("parkiert"), bool) for p in plan["platzierungen"])
    if plan["zaehlung"]["autos"] < plan["ziel"]["autos"]:
        assert plan["parkieren"]["versucht"] >= 1 and isinstance(plan["parkieren"]["gruende"], dict)
        geparkt = plan["parkieren"]["gestellt"]
        assert geparkt == sum(1 for p in plan["platzierungen"] if p["parkiert"])
        if geparkt < plan["parkieren"]["versucht"]:
            assert any(s.startswith("Neben dem Haus parkieren ging") for s in plan["saetze"]), plan["saetze"]
    # Und wo Platz ist, parkiert er wirklich (das Haus in der Mitte eines grossen Geländes).
    gross = tmp_path / "gross.glb"
    gross.write_bytes(_make_glb().baue_glb([("Gelaende", (-30.0, -0.2, -30.0), (30.0, 0.0, 30.0)),
                                            ("Haus", (0.0, 0.0, -8.0), (10.0, 6.0, 0.0))]))
    plan = umfeld.plane_fuer_glb(gross, wunsch={"kategorien": ["autos"], "dichte": "mittel", "seed": 0},
                                 richtungen=("sSE",))
    assert plan["parkieren"]["gestellt"] >= 1
    assert any("neben dem Haus parkiert" in s for s in plan["saetze"])


def test_runner_stellt_auf_die_platte():
    runner = (WURZEL / "src" / "aiimaging" / "runners" / "blender_depth_stage.py").read_text(encoding="utf-8")
    assert 'if p.get("auf_platte"):' in runner


def _situation(tmp_path):
    pfad = tmp_path / "situation.glb"
    pfad.write_bytes(_make_glb().baue_glb(_make_glb().situationsszene()))
    return pfad


def _vogel_auf(box, kuerzel="sSE"):
    v = kameras.vogelschau(box, kuerzel=kuerzel)
    return {"kuerzel": f"zelle-{kuerzel}", "auge": v["auge"], "blick_auf": v["blick_auf"],
            "brennweite_mm": v["brennweite_mm"], "seitenverhaeltnis": v["seitenverhaeltnis"]}


def test_situationsmodell_plant_um_die_bauten_im_bild(tmp_path):
    """Ergebnis 358: Wettbewerbsmodell, Gebiet B2:C3 aus der Vogelschau, Bäume und Autos mittel →
    0 Bäume, ohne Grund. Jetzt: Bäume nahe bei den Bauten im Bild, im Bild, nicht im Bau."""
    pfad = _situation(tmp_path)
    gelesen = umfeld.lies_glb_umfeld(pfad)
    assert kameras.ist_situationsmodell(gelesen["haupt_box"])["ja"]
    # Ein Gebiet um den grossen Bau in der Mitte (wie B2:C3 auf der Draufsicht).
    kam = _vogel_auf([[-70.0, -40.0, 0.0], [60.0, 60.0, 25.0]])
    plan = umfeld.plane_fuer_glb(pfad, wunsch={"kategorien": ["baeume", "autos"], "dichte": "mittel",
                                               "seed": 0}, kameras=[kam])
    assert plan["situation"] is True
    assert plan["zaehlung"]["baeume"] > 0, plan["saetze"]
    assert plan["zaehlung"]["baeume"] <= umfeld.HOECHSTENS["baeume"]
    # Der Hauptbau ist der grosse Bau in der Mitte, nicht die Box aller Platten.
    (hx0, hy0), (hx1, hy1) = plan["hauptbau"]["box"]
    assert (hx1 - hx0) * (hy1 - hy0) < 0.05 * 440 * 395
    bauten = [c for c in umfeld.grundriss_cluster(gelesen["bauwerk_boxen"]) if c["bau"]]
    rahmen = umfeld.kamera_rahmen(kam)
    boden = gelesen["gelaende"].ausdehnung()[1][2]
    sicht = umfeld._bodenflaeche(rahmen, boden)
    for p in plan["platzierungen"]:
        naechster = min(umfeld._abstand_box(p["x"], p["y"], c["box"]) for c in bauten)
        assert umfeld.ABSTAND_HAUS_M <= naechster <= umfeld.NAEHE_BAU_M + p["radius_m"], p
        assert umfeld._in_polygon(p["x"], p["y"], sicht), p
    _alle_autos_ganz(plan, [kam])
    assert any("Situationsmodell" in s for s in plan["saetze"])


def test_situationsmodell_ohne_bau_im_bild_sagt_warum(tmp_path):
    pfad = _situation(tmp_path)
    # Ein Gebiet ganz ohne Bau (Südwestecke der Anlage, zwischen den Bauten).
    kam = _vogel_auf([[-120.0, -240.0, 0.0], [-60.0, -200.0, 5.0]])
    plan = umfeld.plane_fuer_glb(pfad, wunsch={"kategorien": ["baeume", "autos"], "dichte": "mittel",
                                               "seed": 0}, kameras=[kam])
    assert plan["bauten"]["im_bild"] == 0
    assert plan["zaehlung"] == {"baeume": 0, "autos": 0}
    for label in ("Bäume", "Autos"):
        assert any(s.startswith(f"Keine {label}: Im Bild der Kamera steht kein Bau")
                   for s in plan["saetze"]), plan["saetze"]


# ============================================================ jede 0 hat ihren Grund

def _haus_plan(**kw):
    haus = ((0.0, 0.0), (10.0, 8.0))
    werte = dict(gelaende=umfeld.Gelaende([((-30.0, -30.0, -0.2), (30.0, 30.0, 0.0))]),
                 bauwerk_boxen=[haus], haupt_box=haus,
                 kameras=[{"kuerzel": "s", "auge": [5.0, -40.0, 1.7]}],
                 kategorien=["baeume", "buesche", "autos", "strasse"], dichte="mittel", seed=1)
    werte.update(kw)
    return umfeld.plane(**werte)


def test_jede_kategorie_mit_null_traegt_einen_satz():
    # Kein freies Gelände: die Platte ist kaum grösser als das Haus.
    eng = _haus_plan(gelaende=umfeld.Gelaende([((-1.0, -1.0, -0.2), (11.0, 9.0, 0.0))]),
                     kategorien=["baeume", "buesche"])
    for kat, label in (("baeume", "Bäume"), ("buesche", "Büsche")):
        assert eng["zaehlung"][kat] == 0
        assert any(s.startswith(f"Keine {label}:") for s in eng["saetze"]), eng["saetze"]
    # Ausdrücklich 0 bestellt.
    null = _haus_plan(anzahl={"baeume": 0})
    assert null["zaehlung"]["baeume"] == 0 and "Keine Bäume: 0 bestellt." in null["saetze"]
    # Keine Strasse, also keine Autos.
    ohne = _haus_plan(gelaende=umfeld.Gelaende([((-3.0, -3.0, -0.2), (13.0, 11.0, 0.0))]),
                      kategorien=["autos"])
    assert ohne["zaehlung"]["autos"] == 0
    assert any(s.startswith("Keine Autos:") for s in ohne["saetze"]), ohne["saetze"]


def test_bericht_traegt_den_grund_ins_ergebnis():
    plan = _haus_plan(gelaende=umfeld.Gelaende([((-1.0, -1.0, -0.2), (11.0, 9.0, 0.0))]),
                      kategorien=["baeume"])
    bericht = umfeld.bericht_fuer_ergebnis({"kategorien": ["baeume"]}, plan, None,
                                           freigeschaltet_jetzt=True)
    assert any(s.startswith("Keine Bäume:") for s in bericht["saetze"])


# ============================================================ die Naht: der Abholer gibt den Rahmen mit

def test_abholer_gibt_blickziel_brennweite_und_seitenverhaeltnis(tmp_path, monkeypatch):
    gesehen = {}

    def plane_fuer_glb(modell, **kw):
        gesehen.update(kw)
        return {"platzierungen": [], "strasse": None, "wiese": None, "zaehlung": {}, "saetze": []}
    monkeypatch.setattr(umfeld, "plane_fuer_glb", plane_fuer_glb)
    szene = {"umfeld": {"kategorien": ["autos"], "dichte": "wenig", "seed": 0},
             "aufloesung": 960, "hoehe": 600}
    aufgaben = [{"kuerzel": "zelle-B2C3-sSE", "auge": [1.0, -50.0, 40.0], "blick_auf": [0.0, 0.0, 0.0],
                 "brennweite_mm": 35.0, "shift_y": 0.05}]
    abholer.umfeld_vorbereiten(tmp_path / "job", szene, tmp_path / "x.glb", aufgaben=aufgaben,
                               umgebung={umfeld.ORDNER_ENV: str(tmp_path / "speicher")})
    kam = gesehen["kameras"][0]
    assert kam["blick_auf"] == [0.0, 0.0, 0.0] and kam["brennweite_mm"] == 35.0
    assert kam["shift_y"] == 0.05 and math.isclose(kam["seitenverhaeltnis"], 1.6)
    assert gesehen["brennweite_mm"] == 35.0 and math.isclose(gesehen["seitenverhaeltnis"], 1.6)


# ============================================================ Entscheid 150: das Grün beim Hauptbau

def _beim_hauptbau(plan, p):
    hb = plan["hauptbau"]
    return umfeld._abstand_box(p["x"], p["y"], hb["box"]) <= hb["umkreis_m"] + 1e-6


@pytest.mark.parametrize("seed", [0, 1, 2])
@pytest.mark.parametrize("szene", ["situation", "wettbewerbsartig"])
def test_e150_baeume_und_autos_stehen_beim_hauptbau(tmp_path, seed, szene):
    """Entscheid 150 (Owner über die Zentrale, 24.10.2026, nach dem Bild 360 b1): Auf dem Wettbewerbsmodell
    streuten 25 Bäume über die ganze Ansicht, nur 1–2 standen beim Hauptbau. Jetzt zuerst im Umkreis um den
    Bau, den die Kamera zeigt; der Rest der Anlage bleibt ruhig. Gegen den alten Stand: ein kleiner Teil."""
    if szene == "situation":
        pfad, kam = _situation(tmp_path), _vogel_auf([[-70.0, -40.0, 0.0], [60.0, 60.0, 25.0]])
    else:
        pfad, kam = _wettbewerbsartig(tmp_path), _vogel_auf([[-90.0, -40.0, 0.0], [60.0, 60.0, 10.0]])
    plan = umfeld.plane_fuer_glb(pfad, wunsch={"kategorien": ["baeume", "autos"], "dichte": "mittel",
                                               "seed": seed}, kameras=[kam])
    hb = plan["hauptbau"]
    seite = max(hb["box"][1][0] - hb["box"][0][0], hb["box"][1][1] - hb["box"][0][1])
    assert umfeld.UMKREIS_HAUPTBAU_MIN_M <= hb["umkreis_m"] <= umfeld.NAEHE_BAU_M
    assert hb["umkreis_m"] == round(umfeld.umkreis_hauptbau(hb["box"]), 1)
    assert hb["umkreis_m"] >= min(umfeld.NAEHE_BAU_M, 0.25 * seite) - 0.05
    baeume = [p for p in plan["platzierungen"] if p["kategorie"] == "baeume"]
    autos = [p for p in plan["platzierungen"] if p["kategorie"] == "autos"]
    assert len(baeume) == umfeld.HOECHSTENS["baeume"] and len(autos) == umfeld.DICHTE_AUTOS["mittel"]
    nah = [p for p in baeume if _beim_hauptbau(plan, p)]
    assert len(nah) >= 0.8 * len(baeume), (len(nah), len(baeume))
    assert all(_beim_hauptbau(plan, p) for p in autos)
    assert all(p["beim_hauptbau"] == _beim_hauptbau(plan, p) for p in baeume + autos)
    # Die alten Regeln bleiben: nicht im Bau, bis 30 m an einem Bau, Autos ganz im Bild.
    bauten = [c for c in umfeld.grundriss_cluster(umfeld.lies_glb_umfeld(pfad)["bauwerk_boxen"]) if c["bau"]]
    for p in plan["platzierungen"]:
        naechster = min(umfeld._abstand_box(p["x"], p["y"], c["box"]) for c in bauten)
        assert umfeld.ABSTAND_HAUS_M <= naechster <= umfeld.NAEHE_BAU_M + p["radius_m"], p
    _alle_autos_ganz(plan, [kam])
    satz = [s for s in plan["saetze"] if s.startswith("Beim Hauptbau")]
    assert satz and f"{len(nah)} von {len(baeume)} Bäumen" in satz[0], plan["saetze"]
    # Wiederholbar mit dem Startwert.
    noch = umfeld.plane_fuer_glb(pfad, wunsch={"kategorien": ["baeume", "autos"], "dichte": "mittel",
                                               "seed": seed}, kameras=[kam])
    assert noch["platzierungen"] == plan["platzierungen"]


def test_e150_ist_beim_hauptbau_kein_platz_kommt_der_rest_zu_den_anderen_bauten(tmp_path, monkeypatch):
    """Erst wenn der Umkreis voll ist, geht es zu den anderen Bauten — und der Satz sagt, wie viele."""
    monkeypatch.setattr(umfeld, "UMKREIS_HAUPTBAU_MIN_M", 1.0)
    monkeypatch.setattr(umfeld, "UMKREIS_HAUPTBAU_ANTEIL", 0.0)      # 1 m: näher als der Abstand zum Bau
    pfad, kam = _situation(tmp_path), _vogel_auf([[-70.0, -40.0, 0.0], [60.0, 60.0, 25.0]])
    plan = umfeld.plane_fuer_glb(pfad, wunsch={"kategorien": ["baeume"], "dichte": "mittel", "seed": 0},
                                 kameras=[kam])
    baeume = plan["platzierungen"]
    assert baeume and not any(p["beim_hauptbau"] for p in baeume)
    satz = [s for s in plan["saetze"] if s.startswith("Beim Hauptbau")][0]
    assert f"0 von {len(baeume)} Bäumen" in satz
    assert f"{len(baeume)} weitere bei anderen Bauten im Bild, weil beim Hauptbau kein Platz mehr war" in satz


def test_e150_ohne_situationsmodell_aendert_sich_nichts():
    plan = _haus_plan()
    assert not any("beim_hauptbau" in p for p in plan["platzierungen"])
    assert not any(s.startswith("Beim Hauptbau") for s in plan["saetze"])


def test_e150_hauptbau_ist_der_bau_am_blickziel_nicht_der_groesste(tmp_path):
    """Ergebnis 361: Der grösste Bau im Bild war nicht der Bau mit Innenhof, auf den die Zellen-Kamera zielte —
    alle 25 Bäume standen am falschen Bau. Entscheid 150 heisst «um den Bau, den die Kamera zeigt»: der Bau am
    Blickziel (enthält es oder liegt ihm am nächsten); nur ohne Blickziel der grösste."""
    pfad = _wettbewerbsartig(tmp_path)
    bauten = [c for c in umfeld.grundriss_cluster(umfeld.lies_glb_umfeld(pfad)["bauwerk_boxen"]) if c["bau"]]
    groesster, kleiner = bauten[0], min(bauten[1:], key=lambda c: abs(c["box"][0][0]) + abs(c["box"][0][1]))
    assert kleiner["flaeche_m2"] < groesster["flaeche_m2"]
    lo = [min(groesster["box"][0][k], kleiner["box"][0][k]) - 10.0 for k in (0, 1)]
    hi = [max(groesster["box"][1][k], kleiner["box"][1][k]) + 10.0 for k in (0, 1)]
    kam = _vogel_auf([[lo[0], lo[1], 0.0], [hi[0], hi[1], 10.0]])
    wunsch = {"kategorien": ["baeume"], "dichte": "mittel", "seed": 0}
    vorher = umfeld.plane_fuer_glb(pfad, wunsch=wunsch, kameras=[dict(kam, blick_auf=None)])
    assert vorher["bauten"]["im_bild"] >= 2 and vorher["hauptbau"]["gewaehlt"] == "groesster"
    assert vorher["hauptbau"]["box"] == [list(groesster["box"][0]), list(groesster["box"][1])]
    mitte = [(kleiner["box"][0][0] + kleiner["box"][1][0]) / 2,
             (kleiner["box"][0][1] + kleiner["box"][1][1]) / 2, 1.0]
    plan = umfeld.plane_fuer_glb(pfad, wunsch=wunsch, kameras=[dict(kam, blick_auf=mitte)])
    assert plan["hauptbau"]["gewaehlt"] == "blickziel"
    assert plan["hauptbau"]["box"] == [list(kleiner["box"][0]), list(kleiner["box"][1])], plan["hauptbau"]
    assert any("um den Bau am Blickziel" in s for s in plan["saetze"]), plan["saetze"]
    # Ergebnis 362: Der Plan nannte den Bau am Blickziel, gestellt wurde beim grössten — und Feld und Satz
    # behaupteten «25 von 25 beim Hauptbau». Jetzt gemessen: wer beim_hauptbau trägt, steht dort.
    baeume = [p for p in plan["platzierungen"] if p["kategorie"] == "baeume"]
    for p in baeume:
        assert p["beim_hauptbau"] == _beim_hauptbau(plan, p), p
    nah = [p for p in baeume if _beim_hauptbau(plan, p)]
    assert nah, "beim Bau am Blickziel steht kein Baum"
    # Was beim kleinen Bau keinen Platz fand, geht mit Satz zu den anderen Bauten (E150).
    if len(nah) < len(baeume):
        assert any("weitere bei anderen Bauten" in s for s in plan["saetze"]), plan["saetze"]


def test_e150_ohne_blickziel_bleibt_es_der_groesste_bau():
    bauten = [{"box": ((0.0, 0.0), (100.0, 100.0)), "flaeche_m2": 10000.0},
              {"box": ((200.0, 0.0), (210.0, 10.0)), "flaeche_m2": 100.0}]
    assert umfeld._hauptbau_am_ziel(bauten, [{"auge": [0, 0, 50]}]) == (bauten[0], "groesster")
    assert umfeld._hauptbau_am_ziel(bauten, [{"blick_auf": [205.0, 5.0, 0.0]}]) == (bauten[1], "blickziel")
    # Ziel daneben: der nächste Grundriss gewinnt, nicht der grösste.
    assert umfeld._hauptbau_am_ziel(bauten, [{"blick_auf": [190.0, 5.0, 0.0]}])[0] is bauten[1]
