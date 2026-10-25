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
    """Erst wenn der Umkreis voll ist, geht es zu den anderen Bauten — und der Satz sagt, wie viele.

    Angepasst nach Ergebnis 363 (mit Grund): Der Überlauf geht nur noch zu den nächsten Bauten und höchstens ein
    Drittel des Ziels; der Rest wird mit Satz nicht gestellt, damit die Anlage ruhig bleibt."""
    monkeypatch.setattr(umfeld, "UMKREIS_HAUPTBAU_MIN_M", 1.0)
    monkeypatch.setattr(umfeld, "UMKREIS_HAUPTBAU_ANTEIL", 0.0)      # 1 m: näher als der Abstand zum Bau
    pfad, kam = _situation(tmp_path), _vogel_auf([[-70.0, -40.0, 0.0], [60.0, 60.0, 25.0]])
    plan = umfeld.plane_fuer_glb(pfad, wunsch={"kategorien": ["baeume"], "dichte": "mittel", "seed": 0},
                                 kameras=[kam])
    baeume = plan["platzierungen"]
    assert baeume and not any(p["beim_hauptbau"] for p in baeume)
    ziel = plan["ziel"]["baeume"]
    assert len(baeume) <= int(ziel * umfeld.UEBERLAUF_ANTEIL)
    v = plan["hauptbau"]["verteilung"]["baeume"]
    assert v == {"ziel": ziel, "im_umkreis": 0, "auf_gelaende": 0, "auf_bodenplatten": 0,
                 "nebenan": len(baeume),
                 "weggelassen": ziel - len(baeume)}
    satz = [s for s in plan["saetze"] if s.startswith("Beim Hauptbau")][0]
    assert f"0 von {ziel} Bäumen" in satz
    assert f"{len(baeume)} weitere bei " in satz and "weil beim Hauptbau kein Platz mehr war" in satz
    assert f"{ziel - len(baeume)} nicht gestellt, damit der Rest der Anlage ruhig bleibt" in satz
    assert "Im Umkreis fand sich kein Platz — am häufigsten im Weg: der Hauptbau selbst" in satz


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
        assert any("weitere bei " in s or "nicht gestellt" in s for s in plan["saetze"]), plan["saetze"]


def test_e150_ohne_blickziel_bleibt_es_der_groesste_bau():
    bauten = [{"box": ((0.0, 0.0), (100.0, 100.0)), "flaeche_m2": 10000.0},
              {"box": ((200.0, 0.0), (210.0, 10.0)), "flaeche_m2": 100.0}]
    assert umfeld._hauptbau_am_ziel(bauten, [{"auge": [0, 0, 50]}]) == (bauten[0], "groesster")
    assert umfeld._hauptbau_am_ziel(bauten, [{"blick_auf": [205.0, 5.0, 0.0]}]) == (bauten[1], "blickziel")
    # Ziel daneben: der nächste Grundriss gewinnt, nicht der grösste.
    assert umfeld._hauptbau_am_ziel(bauten, [{"blick_auf": [190.0, 5.0, 0.0]}])[0] is bauten[1]


# ============================================================ Ergebnis 363: der Umkreis liegt auf Platten

def _w(name, x0, y0, x1, y1, h0=0.0, h1=2.0):
    """Eine Box in Weltkoordinaten (Z oben) als glTF-Knoten (Y oben, welt = (x, −z, y))."""
    return (name, (x0, h0, -y1), (x1, h1, -y0))


def _hofbau_eng(tmp_path, band=30.0):
    """Wie das Wettbewerbsmodell in Ergebnis 363, frei erfunden: ein kleiner Bau mit Innenhof (EINE 2-m-Platte,
    41 × 41 m Box — der Hof liegt in der Box, wie bei der echten Grundrissplatte), rundum dicht an dicht 2-m-Platten
    von ``band`` m Breite (Beläge oder Nachbargrundrisse — das Modell sagt nicht, welche), dahinter drei
    Nachbarbauten und ein ferner Bau; alles auf zwei grossen 2-m-Bodenplatten. Gegen 0.3.65: 0 Stücke beim
    Hauptbau, jeder Versuch im Umkreis scheitert an «haus»."""
    a, b = 20.5, 20.5 + band
    k = [_w("IfcSlab_Gelaende_A", -300, -250, 300, 250, -1.0, 0.0),
         _w("IfcSlab_Platte_West", -280, -230, 0, 230), _w("IfcSlab_Platte_Ost", 0, -230, 280, 230),
         _w("IfcSlab_Hofbau", -a, -a, a, a),
         _w("IfcSlab_Belag_N", -b, a, b, b), _w("IfcSlab_Belag_S", -b, -b, b, -a),
         _w("IfcSlab_Belag_W", -b, -a, -a, a), _w("IfcSlab_Belag_O", a, -a, b, a),
         _w("IfcSlab_Nachbar_O", b + 4, -20, b + 34, 10), _w("IfcSlab_Nachbar_W", -b - 30, -10, -b - 4, 15),
         _w("IfcSlab_Nachbar_N", -15, b + 4, 25, b + 24), _w("IfcSlab_Fern", 150, 150, 180, 175)]
    pfad = tmp_path / f"hofbau_eng_{band:g}.glb"
    pfad.write_bytes(_make_glb().baue_glb(k))
    return pfad, _vogel_auf([[-110.0, -110.0, 0.0], [110.0, 110.0, 10.0]])


HOF = ((-20.5, -20.5), (20.5, 20.5))


def _flache_platten(band):
    """Alle 2-m-Teile von :func:`_hofbau_eng` ausser dem Hofbau und den Bodenplatten: vier Beläge, drei Nachbarn."""
    a, b = 20.5, 20.5 + band
    return [((-b, a), (b, b)), ((-b, -b), (b, -a)), ((-b, -a), (-a, a)), ((a, -a), (b, a)),
            ((b + 4, -20), (b + 34, 10)), ((-b - 30, -10), (-b - 4, 15)), ((-15, b + 4), (25, b + 24))]


@pytest.mark.parametrize("seed", [0, 1, 2])
def test_152_im_plattenguertel_steht_nichts_auf_den_flachen_platten(tmp_path, seed):
    """Ergebnis 363 ROT (0 von 25 beim Bau mit Innenhof, der ganze Umkreis lag auf 2-m-Platten) — 0.3.66 stellte
    darauf in einer zweiten Runde. ENTSCHEID 152 (Owner, 25.10.2026): Die Platten sind gemischt, Beläge und
    Grundrisse, und niemand weiss welche — also steht auf ihnen NIE etwas. Im 30-m-Gürtel findet sich im 25-m-Umkreis
    darum kein Platz: weniger gestellt, höchstens ein Drittel bei den nächsten Bauten, der Rest mit Satz weggelassen.
    Was steht, steht auf dem Gelände oder einer grossen Bodenplatte — nie auf einer flachen Platte, nie am Hauptbau."""
    pfad, kam = _hofbau_eng(tmp_path)
    wunsch = {"kategorien": ["baeume", "autos"], "dichte": "mittel", "seed": seed}
    plan = umfeld.plane_fuer_glb(pfad, wunsch=wunsch, kameras=[kam])
    hb = plan["hauptbau"]
    assert hb["gewaehlt"] == "blickziel" and hb["box"] == [list(HOF[0]), list(HOF[1])]
    assert hb["umkreis_m"] == umfeld.UMKREIS_HAUPTBAU_MIN_M == 25.0
    assert hb["flache_teile_im_umkreis"] > 0
    stuecke = plan["platzierungen"]
    ziel = umfeld.HOECHSTENS["baeume"] + umfeld.DICHTE_AUTOS["mittel"]
    assert len(stuecke) <= ziel // 3 + 1 < ziel, len(stuecke)          # weniger gestellt
    for p in stuecke:
        assert p["beim_hauptbau"] == _beim_hauptbau(plan, p)
        assert umfeld._abstand_box(p["x"], p["y"], HOF) >= umfeld.ABSTAND_HAUS_M + p["radius_m"] - 1e-6, p
        assert not any(umfeld._abstand_box(p["x"], p["y"], q) == 0.0 for q in _flache_platten(30.0)), p
        assert p["standflaeche"] in ("gelaende", "bodenplatte"), p
    v = hb["verteilung"]
    weg = v["baeume"]["weggelassen"] + v["autos"]["weggelassen"]
    assert weg > 0 and v["baeume"]["im_umkreis"] == v["autos"]["im_umkreis"] == 0
    assert "auf_flachen_platten" not in v["baeume"]
    sperren = hb["sperren"]
    assert sperren and len(sperren) <= umfeld.SPERREN_HOECHSTENS
    assert {s["art"] for s in sperren} <= {"hauptbau", "bau", "belag"}
    assert any(s["flach"] for s in sperren)
    assert all(set(s) == {"cluster", "art", "flach", "flaeche_m2", "hoehe_m", "abstand_m", "versuche"}
               for s in sperren)
    satz = [s for s in plan["saetze"] if s.startswith("Beim Hauptbau")][0]
    assert f"{weg} nicht gestellt, damit der Rest der Anlage ruhig bleibt" in satz, satz
    assert "auf den flachen Platten bis 3 m im Umkreis steht nichts" in satz, satz
    _alle_autos_ganz(plan, [kam])
    # Wiederholbar mit dem Startwert.
    assert umfeld.plane_fuer_glb(pfad, wunsch=wunsch, kameras=[kam])["platzierungen"] == stuecke


def test_363_freier_boden_im_umkreis_wird_genommen(tmp_path):
    """Liegt im Umkreis freier Boden (schmaler Gürtel), stehen alle Stücke dort — auf der Bodenplatte, nie auf
    den flachen Platten."""
    pfad, kam = _hofbau_eng(tmp_path, band=12.0)
    plan = umfeld.plane_fuer_glb(pfad, wunsch={"kategorien": ["baeume"], "dichte": "mittel", "seed": 0},
                                 kameras=[kam])
    v = plan["hauptbau"]["verteilung"]["baeume"]
    assert v["im_umkreis"] == v["ziel"] == 25 and v["weggelassen"] == 0
    flach = [((-32.5, -32.5), (32.5, 32.5))]                        # Hofbau und Belag zusammen
    for p in plan["platzierungen"]:
        assert umfeld._abstand_box(p["x"], p["y"], flach[0]) >= umfeld.ABSTAND_HAUS_M + p["radius_m"] - 1e-6, p
    assert not any("auf flachen Platten" in s or "steht nichts" in s for s in plan["saetze"])


def test_363_ueberlauf_nur_zu_den_naechsten_bauten_und_hoechstens_ein_drittel(tmp_path, monkeypatch):
    """Ergebnis 363: Was beim Hauptbau keinen Platz fand, streute wieder über die ganze Ansicht. Jetzt geht es nur
    zu den nächsten Bauten neben dem Hauptbau, höchstens ein Drittel des Ziels; der Rest wird mit Satz nicht
    gestellt. Zwei Autos: ein Drittel ist 0 — beide fallen weg, und das steht da."""
    monkeypatch.setattr(umfeld, "UMKREIS_HAUPTBAU_MIN_M", 1.0)
    monkeypatch.setattr(umfeld, "UMKREIS_HAUPTBAU_ANTEIL", 0.0)
    pfad, kam = _hofbau_eng(tmp_path)
    plan = umfeld.plane_fuer_glb(pfad, wunsch={"kategorien": ["baeume", "autos"], "dichte": "mittel", "seed": 0},
                                 kameras=[kam])
    hb = plan["hauptbau"]
    assert len(hb["nachbarn"]) == umfeld.UEBERLAUF_NACHBARN
    baeume = [p for p in plan["platzierungen"] if p["kategorie"] == "baeume"]
    assert 0 < len(baeume) <= 25 // 3
    assert not [p for p in plan["platzierungen"] if p["kategorie"] == "autos"]
    for p in baeume:
        assert min(umfeld._abstand_box(p["x"], p["y"], umfeld._box2(n["box"])) for n in hb["nachbarn"]) \
            <= umfeld.NAEHE_HAUS_PARK_M + 1e-6, p
        # Nicht beim fernen Bau.
        assert umfeld._abstand_box(p["x"], p["y"], ((150.0, 150.0), (180.0, 175.0))) > 60.0
    assert hb["verteilung"]["autos"] == {"ziel": 2, "im_umkreis": 0, "auf_gelaende": 0, "auf_bodenplatten": 0,
                                         "nebenan": 0, "weggelassen": 2}
    weg = 25 - len(baeume) + 2
    satz = [s for s in plan["saetze"] if s.startswith("Beim Hauptbau")][0]
    assert f"{len(baeume)} weitere bei den 3 nächsten Bauten daneben" in satz
    assert f"{weg} nicht gestellt, damit der Rest der Anlage ruhig bleibt" in satz
    assert "Im Umkreis fand sich kein Platz — am häufigsten im Weg:" in satz


# ============================================================ Ergebnis 364: ein Wortschatz für «worauf»

@pytest.mark.parametrize("seed,band", [(0, 20.0), (1, 20.0), (0, 30.0), (0, 12.0)])
def test_364_standflaeche_ein_feld_fuer_satz_verteilung_und_runner(tmp_path, seed, band):
    """Ergebnis 364: Satz und ``verteilung`` nannten 17 Stücke «auf flachen Platten» (Autos 0), das Feld
    ``auf_platte`` stand aber bei 26 von 27 (auch bei beiden Autos) — es zählte die grossen Bodenplatten mit, die
    Verteilung nur die zweite Runde. Jetzt trägt jedes Stück ``standflaeche`` (gelaende/bodenplatte; flache Platten
    gibt es nach Entscheid 152 nicht mehr), ``auf_platte`` ist genau dann wahr, wenn es «bodenplatte» ist, und Satz
    und Verteilung zählen aus dem Feld."""
    pfad, kam = _hofbau_eng(tmp_path, band=band)
    plan = umfeld.plane_fuer_glb(pfad, wunsch={"kategorien": ["baeume", "autos"], "dichte": "mittel",
                                               "seed": seed}, kameras=[kam])
    stuecke = plan["platzierungen"]
    assert stuecke and umfeld.STANDFLAECHEN == ("gelaende", "bodenplatte")
    for p in stuecke:
        assert p["standflaeche"] in umfeld.STANDFLAECHEN, p
        assert bool(p.get("auf_platte")) == (p["standflaeche"] == "bodenplatte"), p
        if p["standflaeche"] == "bodenplatte":
            assert math.isclose(p["z"], 2.0, abs_tol=1e-6), p
        assert not any(umfeld._abstand_box(p["x"], p["y"], q) == 0.0 for q in _flache_platten(band)), p
    vt = plan["hauptbau"]["verteilung"]
    for kat, v in vt.items():
        umkreis = [p for p in stuecke if p["kategorie"] == kat and p["beim_hauptbau"]]
        assert v["im_umkreis"] == len(umkreis) == v["auf_gelaende"] + v["auf_bodenplatten"]
        assert v["auf_bodenplatten"] == sum(1 for p in umkreis if p["standflaeche"] == "bodenplatte")
        assert "auf_flachen_platten" not in v
    satz = [s for s in plan["saetze"] if s.startswith("Beim Hauptbau")][0]
    assert "Bodenplatten" not in satz and "davon auf flachen Platten" not in satz
    # Nachprobe 0.3.67: «worauf» in eigenem Satz, gezählt über ALLE Stücke aus dem Feld (vorher 10 gegen 13).
    boden = sum(1 for p in stuecke if p["standflaeche"] == "bodenplatte")
    worauf = [s for s in plan["saetze"] if s.startswith("Worauf:")]
    if boden:
        assert worauf == [f"Worauf: {boden} von {len(stuecke)} Stücken stehen auf den grossen Bodenplatten des "
                          f"Modells (sie zählen wie Gelände), {len(stuecke) - boden} auf dem Gelände; auf den "
                          f"flachen Platten steht keines (Entscheid 152)."], plan["saetze"]
    else:
        assert worauf == []


def test_364_ohne_situationsmodell_kein_feld_standflaeche():
    plan = _haus_plan()
    assert plan["platzierungen"] and not any("standflaeche" in p or "auf_platte" in p for p in plan["platzierungen"])


def test_364_runner_zaehlt_standflaeche_und_nimmt_z_weiter_aus_auf_platte():
    runner = (WURZEL / "src" / "aiimaging" / "runners" / "blender_depth_stage.py").read_text(encoding="utf-8")
    assert 'if p.get("auf_platte"):' in runner
    assert 'sf = befund.setdefault("standflaeche", {})' in runner


# ============================================================ Mac-Befund 25.10.2026: vier Kameras rundum, 0 Autos

def _rundum_plan(richtungen, rand=8.0, seed=1, boxen3=(((0.0, 0.0, 0.0), (12.0, 9.0, 7.0)),),
                 kategorien=("autos", "baeume")):
    from aiimaging import kameras as _k
    lo = tuple(min(b[0][i] for b in boxen3) for i in range(3))
    hi = tuple(max(b[1][i] for b in boxen3) for i in range(3))
    haus = ((lo[0], lo[1]), (hi[0], hi[1]))
    satz = _k.kamerasatz((lo, hi), kuerzel=list(richtungen), brennweite_mm=_k.BRENNWEITE_MM, seitenverhaeltnis=1.5)
    kam = [{"kuerzel": k["kuerzel"], "auge": k["auge"], "blick_auf": k.get("blick_auf"),
            "brennweite_mm": _k.BRENNWEITE_MM, "seitenverhaeltnis": 1.5, "shift_mm": k.get("shift_mm")}
           for k in satz["kameras"]]
    plan = umfeld.plane(gelaende=umfeld.Gelaende([((lo[0] - rand, lo[1] - rand, -0.2),
                                                   (hi[0] + rand, hi[1] + rand, 0.0))]),
                        bauwerk_boxen=list(boxen3), haupt_box=haus, kameras=kam, kategorien=list(kategorien),
                        dichte="mittel", seed=seed, seitenverhaeltnis=1.5)
    return plan, kam, haus


@pytest.mark.parametrize("seed", [1, 2, 3])
@pytest.mark.parametrize("richtungen", [("sSE", "eEN", "nNW", "wWS"), ("sSE", "sSW", "nNE", "nNW")])
def test_mac_vier_kameras_rundum_mindestens_ein_auto(richtungen, seed):
    """Mac-Befund 25.10.2026 (Mappe am Hang, Umfeld mit Autos, vier Kameras rundum): 0 Autos, «der freie Platz liegt
    im Blick der Kamera auf das Haus», und Parkieren ging auch nicht. Ein Auto darf jetzt vor dem Haus stehen, wenn
    es dort nur den Sockel deckt (hausnahe Hälfte des Blicks); es steht ganz in mindestens einem Bild, in keinem
    angeschnitten, und nennt die Kameras. Bäume halten den Blick weiter ganz frei."""
    # Nachprobe 0.3.67: seit der Messung im Bild bei 10 m Grundstücksrand (bei 8 m je nach Startwert keines, mit Satz).
    plan, kam, haus = _rundum_plan(richtungen, rand=10.0, seed=seed)
    autos = [p for p in plan["platzierungen"] if p["kategorie"] == "autos"]
    assert len(autos) >= 1, plan["saetze"]
    rahmen = [r for r in (umfeld.kamera_rahmen(k, seitenverhaeltnis=1.5) for k in kam) if r]
    for a in autos:
        assert umfeld.lage_im_bild(rahmen, umfeld._auto_ecken(a["x"], a["y"], a["z"], a["drehung_grad"],
                                                              a["laenge_m"]), verdeckt_durch=haus) == "ganz", a
        for k in kam:
            poly = umfeld.sichtkegel(k["auge"], haus)
            r = a["radius_m"] if a.get("parkiert") else min(a["radius_m"], 1.2)
            if umfeld._abstand_polygon(a["x"], a["y"], poly) < r + umfeld.SICHT_RAND_M:
                assert k["kuerzel"] in a.get("vor_dem_haus", ()), (k["kuerzel"], a)
                assert umfeld._auto_nur_sockel(k["auge"], a["x"], a["y"], r, haus, 0.0)
                # Nachprobe 0.3.67: im Bild gemessen, mit den echten Ecken des Autos.
                rah = umfeld.kamera_rahmen(k, seitenverhaeltnis=1.5)
                d = umfeld.auto_deckt_im_bild(rah, umfeld._auto_ecken(a["x"], a["y"], a["z"], a["drehung_grad"],
                                                                      a["laenge_m"]),
                                              [((0.0, 0.0, 0.0), (12.0, 9.0, 7.0))])
                assert d["ok"], (k["kuerzel"], d)
    for b in (p for p in plan["platzierungen"] if p["kategorie"] == "baeume"):
        assert "vor_dem_haus" not in b
        for k in kam:
            assert umfeld._abstand_polygon(b["x"], b["y"], umfeld.sichtkegel(k["auge"], haus)) \
                >= b["radius_m"] + umfeld.SICHT_RAND_M - 1e-6
    if any(a.get("vor_dem_haus") for a in autos):
        assert any("vor dem Haus im Bild der Kamera" in s and "höchstens den Sockel" in s for s in plan["saetze"])


def test_mac_auto_nur_sockel_nah_an_der_kamera_nie():
    """Gross vor der Kamera (vordere Hälfte des Blicks) ist kein Sockel — dort bleibt der Blick frei."""
    auge, haus = (6.0, -40.0, 1.7), ((0.0, 0.0), (12.0, 9.0))
    assert umfeld._auto_nur_sockel(auge, 6.0, -8.0, 2.2, haus, 0.0)          # nahe am Haus
    assert not umfeld._auto_nur_sockel(auge, 6.0, -30.0, 2.2, haus, 0.0)     # nahe an der Kamera
    # Ein tiefes Auge (unter dem Autodach) sieht ein nahes Auto höher an der Fassade.
    assert not umfeld._auto_nur_sockel((6.0, -40.0, 0.3), 6.0, -19.0, 2.2, haus, 0.0)


def test_mac_werkzeug_plant_mit_den_bestellten_richtungen(tmp_path, monkeypatch):
    """Das MCP-Werkzeug plant mit den Standpunkten des Auftrags (``richtungen``), nicht mit der Vorgabe."""
    from aiimaging import werkzeuge
    gesehen = {}

    def plane_fuer_glb(pfad, **kw):
        gesehen.update(kw)
        return {"platzierungen": [], "strasse": None, "wiese": None, "zaehlung": {}, "saetze": []}
    monkeypatch.setattr(umfeld, "plane_fuer_glb", plane_fuer_glb)
    glb = tmp_path / "h.glb"
    glb.write_bytes(b"x")
    werkzeuge.plan_surroundings({"glb_path": str(glb), "kategorien": ["autos"],
                                 "richtungen": ["sSE", "eEN", "nNW", "wWS"]})
    assert gesehen["richtungen"] == ("sSE", "eEN", "nNW", "wWS")
    from aiimaging import mcp_schemas
    assert "richtungen" in mcp_schemas.werkzeug(mcp_schemas.WERKZEUG_UMFELD)["inputSchema"]["properties"]


# ============================================================ Mac-Befund 25.10.2026: die eigenen Bäume des Modells

def test_mac_modellbaeume_ausblenden_nur_mit_baeumen_im_umfeld():
    """Stellt das Umfeld Bäume, blendet Blender die eigenen Bäume des Modells aus (Vorgabe an, Empfehlung); ohne
    Bäume im Umfeld bleibt das Flag aus."""
    assert umfeld.MODELLBAEUME_AUSBLENDEN is True
    assert _haus_plan(kategorien=["baeume", "autos"])["modellbaeume_ausblenden"] is True
    assert _haus_plan(kategorien=["autos", "strasse", "wiese"])["modellbaeume_ausblenden"] is False
    assert "Bäume des Modells ausgeblendet" in umfeld.satz_modellbaeume(3)
    assert umfeld.satz_modellbaeume(1).startswith("1 Baum des Modells ausgeblendet")


@pytest.mark.parametrize("name,erwartet", [
    ("Baum_Laub", True), ("Baum_Stamm.003", True), ("Hecke_Nord", True), ("IfcGeographicElement_Kegel_2", True),
    ("IfcCivilElement_Nachbar_1", False), ("IfcGeographicElement_Gelaendeflaeche_1", False),
    ("Wand_Aussen", False), ("Stammhaus", False), ("Laubengang", False)])
def test_mac_ist_vegetation(name, erwartet):
    from aiimaging import maske
    assert maske.ist_vegetation(name) is erwartet


def test_mac_runner_blendet_modellbaeume_aus_nur_wenn_baeume_stehen():
    runner = (WURZEL / "src" / "aiimaging" / "runners" / "blender_depth_stage.py").read_text(encoding="utf-8")
    teil = runner[runner.index("DIE EIGENEN BÄUME DES MODELLS"):]
    teil = teil[:teil.index('befund["modellbaeume_ausgeblendet"] = n') + 40]
    assert 'plan.get("modellbaeume_ausblenden") and befund["gestellt"].get("baeume")' in teil
    assert "maske.ist_modellbaum(_namen_fuer_maske(o))" in teil and "o.hide_render = True" in teil
    namen = runner[runner.index("def _namen_fuer_maske(obj)"):runner.index("def _ist_umfeld_objekt(obj)")]
    assert "material_slots" in namen and "URSPRUNG_MARKE" in namen and "obj.data" in namen
    assert "not _ist_umfeld_objekt(o)" in teil                    # die CC0-Bäume bleiben
    abholer_text = (WURZEL / "src" / "aiimaging" / "abholer.py").read_text(encoding="utf-8")
    assert '"modellbaeume_ausgeblendet")}' in abholer_text and "_umfeld.satz_modellbaeume(aus_n)" in abholer_text


# ============================================================ Nachprobe 0.3.67: Autos vor dem Haus, im Bild gemessen

ANBAU = (((0.0, 0.0, 0.0), (12.0, 9.0, 7.0)), ((12.0, 0.0, 0.0), (18.0, 6.0, 3.0)))


@pytest.mark.parametrize("seed", range(6))
def test_0367_kein_auto_verdeckt_das_erdgeschoss_des_anbaus(seed):
    """Nachprobe 0.3.67 am Demohaus, Kamera sSE: zwei Autos «vor dem Haus» deckten das Erdgeschoss des Anbaus und den
    Fuss der Giebelseite — die Prüfung kannte nur die Höhe des Autos. Jetzt im Bild jeder Kamera gemessen: Ein Auto
    vor dem Haus deckt von keinem Bauteil mehr als ``AUTO_BILDANTEIL_HOECHSTENS`` seiner Bildfläche (auch nicht vom
    niedrigen Anbau, 6 × 6 × 3 m) und reicht im Bild nicht über dessen 2,2-m-Linie."""
    plan, kam, _ = _rundum_plan(("sSE",), rand=10.0, seed=seed, boxen3=ANBAU, kategorien=("autos",))
    rah = umfeld.kamera_rahmen(kam[0], seitenverhaeltnis=1.5)
    anbau_rechteck = umfeld._bildrechteck(rah, [(x, y, z) for x in (12.0, 18.0) for y in (0.0, 6.0)
                                                for z in (0.0, 3.0)])
    for a in (p for p in plan["platzierungen"] if p["kategorie"] == "autos"):
        ecken = umfeld._auto_ecken(a["x"], a["y"], a["z"], a["drehung_grad"], a["laenge_m"])
        d = umfeld.auto_deckt_im_bild(rah, ecken, ANBAU)
        if a.get("vor_dem_haus"):
            assert d["ok"] and d["anteil_bauteil_max"] <= umfeld.AUTO_BILDANTEIL_HOECHSTENS, (a, d)
        auto = umfeld._bildrechteck(rah, ecken)
        if auto is not None and anbau_rechteck is not None and a.get("vor_dem_haus"):
            f = (anbau_rechteck[2] - anbau_rechteck[0]) * (anbau_rechteck[3] - anbau_rechteck[1])
            assert umfeld._ueberlappung(auto, anbau_rechteck) / f <= umfeld.AUTO_BILDANTEIL_HOECHSTENS, a


def test_0367_ein_auto_dicht_vor_dem_anbau_gilt_nicht_als_sockel():
    """Gegenprobe: ein Auto dicht vor dem Anbau, mitten in seinem Bild — die Höhenregel allein liesse es zu (es
    steht in der hausnahen Hälfte, Dach unter 2,2 m), im Bild deckt es einen grossen Teil des Erdgeschosses."""
    _, kam, haus = _rundum_plan(("sSE",), rand=10.0, boxen3=ANBAU, kategorien=("autos",))
    k = kam[0]
    rah = umfeld.kamera_rahmen(k, seitenverhaeltnis=1.5)
    # Auf der Linie Auge → Mitte der Anbau-Front, 3 m davor.
    mx, my = 15.0, 0.0
    dx, dy = k["auge"][0] - mx, k["auge"][1] - my
    n = (dx * dx + dy * dy) ** 0.5
    x, y = mx + 3.0 * dx / n, my + 3.0 * dy / n
    assert umfeld._auto_nur_sockel(k["auge"], x, y, 2.2, haus, 0.0)               # die alte Regel: ja
    d = umfeld.auto_deckt_im_bild(rah, umfeld._auto_ecken(x, y, 0.0, 90.0, 4.4), ANBAU)
    assert not d["ok"] and d["anteil_bauteil_max"] > 0.15, d                      # im Bild: nein


def test_0367_satz_nennt_die_bildregel():
    plan, _, _ = _rundum_plan(("sSE", "eEN", "nNW", "wWS"))
    satz = [s for s in plan["saetze"] if "vor dem Haus im Bild" in s]
    if satz:
        assert "unter der 2.2-m-Linie" in satz[0] and "6%" in satz[0], satz



# ============================================================ Nachprobe 0.3.67: die Kegelbäume des Demohauses

def _glb_mit_stoffen(tmp_path, koerper_stoff):
    """Eine glb wie das Demohaus mit Bäumen: Knoten mit neutralen Namen, der Baum steckt im MATERIAL (``Baum_Laub``,
    ``Baum_Stamm`` — so erkannte die Maske sie in C190, über die Material-Kennungstabelle). Inhalt erfunden."""
    zus = importlib.util.spec_from_file_location("glb_zus_0367", WURZEL / "tools" / "glb_zusammenfuehren.py")
    modul = importlib.util.module_from_spec(zus)
    zus.loader.exec_module(modul)
    stoffe = sorted({st for _, _, _, st in koerper_stoff})
    roh = _make_glb().baue_glb([(n, lo, hi) for n, lo, hi, _ in koerper_stoff], materialien=stoffe)
    js, binaer = modul.lies_glb(roh)
    index = {m["name"]: i for i, m in enumerate(js["materials"])}
    for knoten, (_, _, _, st) in zip(js["nodes"], koerper_stoff):
        for pr in js["meshes"][knoten["mesh"]]["primitives"]:
            pr["material"] = index[st]
    pfad = tmp_path / "demohaus_artig.glb"
    pfad.write_bytes(modul.schreibe_glb(js, binaer))
    return pfad


def test_0367_kegelbaeume_am_material_erkannt(tmp_path):
    from aiimaging import maske
    pfad = _glb_mit_stoffen(tmp_path, [
        ("Gelaende", (-30.0, -0.2, -30.0), (30.0, 0.0, 30.0), "Gelaende"),
        ("Wand AW Beton 36 · EG", (0.0, 0.0, -8.0), (10.0, 6.0, 0.0), "Beton"),
        ("Kegel 1", (14.0, 0.0, -4.0), (16.0, 6.0, -2.0), "Baum_Laub"),
        ("Kegel 1 Fuss", (14.8, 0.0, -3.2), (15.2, 1.0, -2.8), "Baum_Stamm"),
        ("Objekt 7", (-8.0, 0.0, -4.0), (-6.0, 5.0, -2.0), "Baum_Laub"),
    ])
    assert umfeld.modellbaeume_im_glb(pfad) == 3
    # Am Objektnamen allein (der alte Weg) war es keiner — der Befund aus 0.3.67.
    assert not any(maske.ist_vegetation(n) for n in ("Kegel 1", "Kegel 1 Fuss", "Objekt 7"))
    assert maske.ist_modellbaum(["Kegel 1", "Mesh.003", "Baum_Laub"])
    assert not maske.ist_modellbaum(["Wand AW Beton 36 · EG", "Beton"])
    assert not maske.ist_modellbaum(["Nachbar", "IfcCivilElement_Nachbar_1"])
    plan = umfeld.plane_fuer_glb(pfad, wunsch={"kategorien": ["baeume"], "dichte": "mittel", "seed": 0})
    assert plan["modellbaeume_im_modell"] == 3 and plan["modellbaeume_ausblenden"] is True
