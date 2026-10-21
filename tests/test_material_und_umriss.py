"""Strang Treue (21.10.2026): Messschalter «Umriss halten» und «Material vorne».

Planblatt ``docs/PLAN_MATERIAL_UND_UMRISS_2026-10-21.md``. Beide Schalter sind Vorgabe aus;
ohne sie rechnet der Heim-PC Wort für Wort wie vorher. Geprüft wird hier, was ohne Grafikkarte
prüfbar ist: die Maske, die Mischung, die Rechnung je Schritt (mit numpy statt torch), das
Lesen der Szene, der Parametersatz, der Vermerk im Lauf und der Messauftrag.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

from aiimaging import (abholer, auftrag, bildlesen, bildschreiben, kosmo_szene, materialwahl,
                       prompts, render, umrisshalt)

WURZEL = Path(__file__).resolve().parents[1]


# ============================================================== die Maske und die Mischung

def _rechteck(b, h, x0, x1, y0, y1):
    return [x0 <= x < x1 and y0 <= y < y1 for y in range(h) for x in range(b)]


def test_abstand_ist_null_auf_dem_haus_und_waechst_daneben():
    b, h = 9, 5
    maske = _rechteck(b, h, 4, 5, 2, 3)          # ein einzelner Punkt in der Mitte
    d = umrisshalt.abstand_px(maske, b, h)
    assert d[2 * b + 4] == 0.0
    assert d[2 * b + 5] == 1.0 and d[2 * b + 3] == 1.0
    assert d[1 * b + 5] == pytest.approx(math.sqrt(2))
    assert d[2 * b + 8] == 4.0
    assert umrisshalt.abstand_px([False] * (b * h), b, h)[0] == math.inf


def test_freigabe_haus_rand_und_weicher_uebergang():
    b, h = 20, 1
    maske = _rechteck(b, h, 0, 5, 0, 1)
    f = umrisshalt.freigabe(maske, b, h, rand=2, weich=4)
    assert f[:7] == [1.0] * 7                     # Haus (0-4) und Rand bis Abstand 2
    assert f[7] == pytest.approx(0.75) and f[9] == pytest.approx(0.25)
    assert f[10:] == [0.0] * 10
    hart = umrisshalt.freigabe(maske, b, h, rand=2, weich=0)
    assert hart[6] == 1.0 and hart[7] == 0.0


def test_rand_und_weich_folgen_der_langen_seite():
    assert umrisshalt.RAND_ANTEIL == 0.02          # dieselbe Zahl wie baumasse
    assert umrisshalt.rand_px(960, 600) == 19
    assert umrisshalt.weich_px(960, 600) == 10
    assert umrisshalt.rand_px(50, 40) == umrisshalt.RAND_MIN_PX


def test_maske_mit_falscher_laenge_wird_abgewiesen():
    with pytest.raises(umrisshalt.UmrissHaltenError):
        umrisshalt.freigabe([True] * 5, 3, 2, rand=1)


B, H = 40, 24
KI_FARBE, GRUND_FARBE = (200, 50, 50), (40, 90, 160)


def _bilder(tmp_path):
    ki = bildschreiben.schreibe_farb_png(tmp_path / "ki.png", [KI_FARBE] * (B * H), B, H)
    grund = bildschreiben.schreibe_farb_png(tmp_path / "grund.png", [GRUND_FARBE] * (B * H), B, H)
    return ki, grund, _rechteck(B, H, 15, 25, 8, 20)


def test_nachher_das_haus_bleibt_ki_aussen_das_grundbild(tmp_path):
    ki, grund, maske = _bilder(tmp_path)
    ziel = tmp_path / "aus.png"
    vermerk = umrisshalt.halte_datei(ki, grund, maske, B, H, ziel, rand=2, weich=2)
    farben, b, h = bildlesen.lies_png_farben(ziel)
    assert (b, h) == (B, H)
    assert farben[10 * B + 20] == KI_FARBE                      # im Haus
    assert farben[10 * B + 13] == KI_FARBE                      # im Rand (Abstand 2)
    assert farben[0] == GRUND_FARBE                             # weit weg
    zwischen = farben[10 * B + 12]                              # Abstand 3: halb
    assert zwischen not in (KI_FARBE, GRUND_FARBE)
    assert vermerk["angewandt"] is True and vermerk["art"] == umrisshalt.ART_NACHHER
    assert vermerk["methode"] == umrisshalt.METHODE_NACHHER
    assert vermerk["punkte_geaendert"] > 0
    assert 0 < vermerk["anteil_haus"] < vermerk["anteil_ki"] < 1
    assert vermerk["anteil_ki"] + vermerk["anteil_grund"] == pytest.approx(1.0, abs=1e-3)


def test_nachher_darf_das_ki_bild_selbst_ueberschreiben(tmp_path):
    ki, grund, maske = _bilder(tmp_path)
    umrisshalt.halte_datei(ki, grund, maske, B, H, ki, rand=0, weich=0)
    farben, _b, _h = bildlesen.lies_png_farben(ki)
    assert farben[0] == GRUND_FARBE and farben[10 * B + 20] == KI_FARBE


@pytest.mark.parametrize("fall", ["groesse", "leer"])
def test_nachher_weist_unpassendes_ab(tmp_path, fall):
    ki, grund, maske = _bilder(tmp_path)
    if fall == "groesse":
        klein = bildschreiben.schreibe_farb_png(tmp_path / "k.png", [GRUND_FARBE] * 4, 2, 2)
        with pytest.raises(umrisshalt.UmrissHaltenError, match="Groessen"):
            umrisshalt.halte_datei(ki, klein, maske, B, H, tmp_path / "z.png")
    else:
        with pytest.raises(umrisshalt.UmrissHaltenError, match="leer"):
            umrisshalt.halte_datei(ki, grund, [False] * (B * H), B, H, tmp_path / "z.png")


def test_freigabe_png_ist_weiss_auf_haus_und_rand(tmp_path):
    _ki, _grund, maske = _bilder(tmp_path)
    ziel = tmp_path / "unter" / "f.png"
    vermerk = umrisshalt.schreibe_freigabe_png(ziel, maske, B, H, rand=1)
    grau, b, h = bildlesen.lies_png_graustufen(ziel)
    assert (b, h) == (B, H)
    assert grau[10 * B + 20] == pytest.approx(1.0) and grau[10 * B + 14] == pytest.approx(1.0)
    assert grau[0] == 0.0 and grau[10 * B + 13] == 0.0
    assert vermerk["art"] == umrisshalt.ART_IM_LAUF and vermerk["rand_px"] == 1
    assert 0 < vermerk["anteil_frei"] < 1


# ============================================================== die Rechnung je Schritt

def test_halte_latenten_innen_frei_aussen_verrauschtes_grundbild():
    np = pytest.importorskip("numpy")
    lat = np.full((1, 2, 2, 2), 5.0)
    hg = np.full_like(lat, 1.0)
    rauschen = np.full_like(lat, -1.0)
    frei = np.array([[[[1.0, 0.0], [0.0, 1.0]]]])
    for sigma, aussen in ((1.0, -1.0), (0.0, 1.0), (0.25, 0.25 * -1.0 + 0.75 * 1.0)):
        neu = umrisshalt.halte_latenten(lat, hg, rauschen, frei, sigma)
        assert neu[0, 0, 0, 0] == 5.0 and neu[0, 1, 1, 1] == 5.0      # frei: unberuehrt
        assert neu[0, 0, 0, 1] == pytest.approx(aussen)
        assert neu[0, 1, 1, 0] == pytest.approx(aussen)


def test_der_rueckruf_zaehlt_zuerst_und_haelt_dann_mit_der_naechsten_stufe():
    np = pytest.importorskip("numpy")

    class Feld(np.ndarray):
        def to(self, *_a, **_k):
            return self

    class Plan:
        sigmas = [1.0, 0.5, 0.0]

    class Pipe:
        scheduler = Plan()

    gezaehlt = []

    def innen(pipe, schritt, zeit, kwargs):
        gezaehlt.append(schritt)
        return kwargs

    umriss = {"hintergrund": np.full((1, 1, 1, 2), 2.0), "rauschen": np.zeros((1, 1, 1, 2)),
              "frei": np.array([[[[1.0, 0.0]]]]), "schritte": 0}
    rueckruf = render._umriss_halten_rueckruf(innen, umriss)
    lat = np.full((1, 1, 1, 2), 9.0).view(Feld)
    aus = rueckruf(Pipe(), 0, None, {"latents": lat})
    assert gezaehlt == [0]
    assert aus["latents"][0, 0, 0, 0] == 9.0
    assert aus["latents"][0, 0, 0, 1] == pytest.approx(0.5 * 0 + 0.5 * 2.0)   # sigma[1]
    aus = rueckruf(Pipe(), 1, None, {"latents": lat})
    assert aus["latents"][0, 0, 0, 1] == pytest.approx(2.0)                     # sigma 0
    assert umriss["schritte"] == 2


def test_der_satz_sagt_ob_es_ankam():
    umriss = {"anteil_frei": 0.31, "zellen": (80, 128)}
    assert "NICHT angekommen" in render._umriss_halten_satz(umriss, False)
    satz = render._umriss_halten_satz(umriss, True)
    assert satz.startswith(umrisshalt.SATZ) and "31 %" in satz and "128 x 80" in satz


# ============================================================== der Parametersatz

def _auftrag(tmp_path, **kw):
    tiefe = bildschreiben.schreibe_graustufen_png(tmp_path / "t.png", [0.5] * 16, 4, 4)
    return render.RenderAuftrag(depth_png=str(tiefe), prompt="a house", backbone="z-image-turbo",
                                ausgabe_png=str(tmp_path / "b.png"), **kw)


def test_ohne_schalter_ist_der_parametersatz_wort_fuer_wort(tmp_path):
    from aiimaging import backbone
    a = _auftrag(tmp_path)
    satz = render._baue_parameter(a, backbone.hole("z-image-turbo"))
    assert "umriss_halten_png" not in satz and "umriss_halten_schritte" not in satz


def test_mit_schalter_steht_die_maske_im_parametersatz_und_wird_geprueft(tmp_path):
    from aiimaging import backbone
    maske = bildschreiben.schreibe_graustufen_png(tmp_path / "m.png", [1.0] * 16, 4, 4)
    schoen = bildschreiben.schreibe_farb_png(tmp_path / "s.png", [(1, 2, 3)] * 16, 4, 4)
    a = _auftrag(tmp_path, umriss_halten_png=str(maske), beauty_png=str(schoen))
    assert render._baue_parameter(a, backbone.hole("z-image-turbo"))["umriss_halten_png"] == \
        str(maske)
    assert not [m for m in render.pruefe_auftrag(a) if "umriss_halten" in m]
    ohne_bild = _auftrag(tmp_path, umriss_halten_png=str(maske))
    assert any("ohne beauty_png" in m for m in render.pruefe_auftrag(ohne_bild))
    fehlt = _auftrag(tmp_path, umriss_halten_png=str(tmp_path / "gibt-es-nicht.png"),
                     beauty_png=str(schoen))
    assert any("umriss_halten_png liegt nicht vor" in m for m in render.pruefe_auftrag(fehlt))


def test_rendere_traegt_die_gehaltenen_schritte_nur_mit_schalter(tmp_path):
    maske = bildschreiben.schreibe_graustufen_png(tmp_path / "m.png", [1.0] * 16, 4, 4)
    schoen = bildschreiben.schreibe_farb_png(tmp_path / "s.png", [(1, 2, 3)] * 16, 4, 4)

    def modell(parameter):
        bildschreiben.schreibe_farb_png(parameter["ausgabe_png"], [(9, 9, 9)] * 16, 4, 4)
        return {"bild_png": parameter["ausgabe_png"], "umriss_halten_schritte": 20}

    mit = render.rendere(_auftrag(tmp_path, umriss_halten_png=str(maske),
                                  beauty_png=str(schoen)), modell=modell)
    assert mit["status"] == "ok", mit
    assert mit["parameter"]["umriss_halten_schritte"] == 20
    ohne = render.rendere(_auftrag(tmp_path), modell=modell)
    assert "umriss_halten_schritte" not in ohne["parameter"]


# ============================================================== die Szene

def _szene(prompt="a house", render_block=None, **vis):
    return {"geometry": {"path": "model.glb", "format": "glb"}, "cameras": "auto",
            "render": dict({"samples": 8}, **(render_block or {})),
            "style": {"prompt": prompt}, "vis": vis}


def test_ausdruecklich_aus_bleiben_prompt_und_szene_wie_sie_waren():
    # Seit Entscheid 126 heisst «ohne Schalter» die Vorgabe M2; «aus» ist ausdruecklich false.
    szene = kosmo_szene.lies_szene(_szene("exposed concrete house", umriss_halten=False,
                                          material_vorne=False), streng=False)
    assert szene["prompt"] == "exposed concrete house" and not szene["maengel"]
    assert szene["umriss_halten"] is None
    assert not [z for z in szene["prompt_zusaetze"] if z["art"] == "material_vorne"]
    assert szene["messschalter"]["umriss_halten"] == {"herkunft": "bestellt"}


@pytest.mark.parametrize("vis", [{}, {"umriss_halten": None, "material_vorne": None}])
def test_ohne_schalter_gilt_die_vorgabe_m2(vis):
    szene = kosmo_szene.lies_szene(_szene("exposed concrete house", **vis), streng=False)
    assert not szene["maengel"]
    assert szene["umriss_halten"] == "im_lauf"
    assert szene["prompt"].startswith("monolithic exposed concrete building")
    assert szene["messschalter"]["umriss_halten"] == {"herkunft": "vorgabe"}
    assert szene["messschalter"]["material_vorne"] == {"herkunft": "vorgabe"}


@pytest.mark.parametrize("art", umrisshalt.ARTEN)
def test_umriss_halten_wird_gelesen(art):
    szene = kosmo_szene.lies_szene(_szene(umriss_halten=art), streng=False)
    assert szene["umriss_halten"] == art and not szene["maengel"]


@pytest.mark.parametrize("vis, wort, endgueltig", [
    ({"umriss_halten": "immer"}, "erwartet war", False),
    ({"umriss_halten": True}, "erwartet war", False),
    ({"umriss_halten": "nachher", "skip": True}, "zugleich", True),
    ({"umriss_halten": "im_lauf", "guete": "vorschau"}, "zugleich", True),
    ({"material_vorne": "ja"}, "erwartet war", False),
    ({"material_vorne": True, "skip": True}, "zugleich", True),
])
def test_falsche_schalter_sind_maengel(vis, wort, endgueltig):
    szene = kosmo_szene.lies_szene(_szene(**vis), streng=False)
    assert any(wort in m for m in szene["maengel"])
    assert any(wort in m for m in szene["maengel_endgueltig"]) is endgueltig


def test_material_vorne_stellt_den_stoff_aus_dem_prompt_an_den_anfang():
    prompt = "contemporary residential building, exposed concrete, architectural photography"
    szene = kosmo_szene.lies_szene(_szene(prompt, material_vorne=True), streng=False)
    assert not szene["maengel"]
    # Der Prompt nennt den Stoff schon einmal — vorne stehen darum zwei Nennungen, im ganzen
    # Prompt drei (seit auf-20261021-303, B3; bis 0.3.16 vier).
    assert szene["prompt"].startswith("monolithic exposed concrete building, made entirely of "
                                      "exposed concrete, contemporary residential building")
    assert kosmo_szene.stoff_nennungen(szene["prompt"], "exposed concrete") == 3
    assert szene["prompt"].endswith(prompt)
    zusatz = [z for z in szene["prompt_zusaetze"] if z["art"] == "material_vorne"]
    assert len(zusatz) == 1 and zusatz[0]["vorne"] is True
    assert zusatz[0]["stoffe"] == ["exposed concrete"]


def test_material_vorne_nimmt_den_bestellten_stoff_des_material_knotens(monkeypatch):
    satz, stoffe = kosmo_szene.material_vorne_satz(
        "a house, timber", [materialwahl.BIBLIOTHEK["sichtbeton-schalungsglatt"]["prompt_en"]])
    assert stoffe == ("smooth fair-faced concrete",)
    assert satz.startswith("monolithic smooth fair-faced concrete building")


def test_material_vorne_ohne_stoff_aendert_nichts():
    assert kosmo_szene.material_vorne_satz("a house at dusk") == (None, ())
    szene = kosmo_szene.lies_szene(_szene("a house at dusk", material_vorne=True), streng=False)
    assert szene["prompt"] == "a house at dusk" and not szene["maengel"]


def test_material_vorne_nennt_kein_bauteil_und_den_ersten_stoff_zuerst():
    satz, stoffe = kosmo_szene.material_vorne_satz("red brick and concrete villa")
    assert stoffe == ("red brick", "concrete")
    assert not prompts.bauteilwaechter(satz)["gefunden"]
    # «exposed concrete» zaehlt nicht zusaetzlich als «concrete»
    assert kosmo_szene.material_vorne_satz("an exposed concrete house")[1] == \
        ("exposed concrete",)


# ============================================================== im Lauf (Attrappen)

def _lauf(tmp_path, monkeypatch=None, **vis):
    """Der Lauf der E117-Probe (Attrappen fuer Blender und Bildmodell). Mit ``monkeypatch``
    dazu eine Bauwerksmaske und Soll-Karten in der Groesse der Bilder — die Attrappen der
    Kette schreiben keinen Material-ID-Pass und messen 1 x 1."""
    from test_kettenlauf_26august import _auftragsordner, _kette, _lauf as kettenlauf
    from test_licht_ins_ki_bild_e117 import B as LB, CYCLES_ABEND, H as LH, KI
    if monkeypatch is None:
        from test_licht_ins_ki_bild_e117 import _lauf_mit
        return _lauf_mit(tmp_path, **vis)
    maske = _rechteck(LB, LH, 20, 44, 10, 34)
    monkeypatch.setattr(abholer, "_maske_bauen",
                        lambda *a, **k: {"maske": list(maske), "gemessen": True, "grund": ""})
    ordner = _auftragsordner(tmp_path / "a")
    from aiimaging import bruecke
    pfad = ordner / bruecke.DATEI_SZENE
    szene = json.loads(pfad.read_text(encoding="utf-8"))
    szene["vis"].update(vis)
    pfad.write_text(json.dumps(szene), encoding="utf-8")
    protokoll, attrappen = _kette(tmp_path / "k")
    multipass_alt, rendere_alt = attrappen["_multipass"], attrappen["_rendere"]
    zaehler = iter(range(1, 100))

    def multipass(glb, aus, **kw):
        bericht = multipass_alt(glb, aus, **kw)
        schoen = bildschreiben.schreibe_farb_png(Path(aus) / "beauty_.png", CYCLES_ABEND, LB, LH)
        return dict(bericht, beauty_png=str(schoen))

    def rendere(a, **kw):
        erg = rendere_alt(a, **kw)
        bildschreiben.schreibe_farb_png(a.ausgabe_png, KI, LB, LH)
        return erg

    def soll(*_a, **_k):
        n = next(zaehler)       # je Kamera eine andere Karte, sonst gelten sie als Zwillinge
        return [float(n) if m else math.inf for m in maske], LB, LH

    attrappen = dict(attrappen, _multipass=multipass, _rendere=rendere, _soll=soll)
    antwort = kettenlauf(tmp_path / "l", ordner, attrappen)
    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort["grund"]
    return ordner, antwort, protokoll


def test_lauf_mit_schalter_aus_traegt_keinen_vermerk(tmp_path):
    ordner, _antwort, protokoll = _lauf(tmp_path, umriss_halten=False)
    kameras = abholer.lies_befund(ordner)["kameras"]
    assert kameras and all(abholer.URTEIL_UMRISS_HALTEN not in k for k in kameras)
    assert all(a.umriss_halten_png is None for a in protokoll["render"])


def _gerechnete(ordner):
    kameras = [k for k in abholer.lies_befund(ordner)["kameras"] if not k.get("doppelt_von")]
    assert kameras
    return kameras


def test_lauf_ohne_maske_sagt_warum_und_liefert_das_bild(tmp_path):
    for art in umrisshalt.ARTEN:
        ordner, antwort, protokoll = _lauf(tmp_path / art, umriss_halten=art)
        for k in _gerechnete(ordner):
            vermerk = k[abholer.URTEIL_UMRISS_HALTEN]
            assert vermerk["angewandt"] is False and "Bauwerksmaske" in vermerk["grund"]
        assert all(a.umriss_halten_png is None for a in protokoll["render"])
        assert any("NICHT angewandt" in h and h.startswith(umrisshalt.SATZ)
                   for h in antwort["ergebnis"]["qa"]["verdict"].get("hinweise", []))


def test_lauf_nachher_haelt_und_misst_ein_zweites_mal(tmp_path, monkeypatch):
    from test_licht_ins_ki_bild_e117 import CYCLES_ABEND, KI
    ordner, antwort, protokoll = _lauf(tmp_path, monkeypatch, umriss_halten="nachher")
    assert all(a.umriss_halten_png is None for a in protokoll["render"])
    for k in _gerechnete(ordner):
        vermerk = k[abholer.URTEIL_UMRISS_HALTEN]
        assert vermerk["angewandt"] is True, vermerk
        assert vermerk["art"] == umrisshalt.ART_NACHHER and vermerk["punkte_geaendert"] > 0
        assert "geom_iou_nachher" in vermerk and "ausserhalb_nachher" in vermerk
        roh = next(q for q in (tmp_path / "l").rglob("*.png")
                   if q.as_posix().endswith(f"/{k['kamera']}/{vermerk['ohne_umriss_halten_png']}"))
        geliefert = ordner / Path(k["bild_png"]).name
        farben_roh, _b, _h = bildlesen.lies_png_farben(roh)
        farben, _b, _h = bildlesen.lies_png_farben(geliefert)
        assert farben_roh == list(map(tuple, KI))
        assert farben[0] == tuple(CYCLES_ABEND[0]), "aussen das Cycles-Bild"
        assert farben[22 * 64 + 32] == tuple(KI[22 * 64 + 32]), "im Haus das KI-Bild"
    saetze = [h for h in antwort["ergebnis"]["qa"]["verdict"].get("hinweise", [])
              if h.startswith(umrisshalt.SATZ)]
    assert saetze and all("'nachher'" in s for s in saetze)


def test_lauf_im_lauf_gibt_die_freigabe_ans_bildmodell(tmp_path, monkeypatch):
    ordner, _antwort, protokoll = _lauf(tmp_path, monkeypatch, umriss_halten="im_lauf")
    mit_maske = [a for a in protokoll["render"] if a.umriss_halten_png]
    assert mit_maske
    for a in mit_maske:
        assert Path(a.umriss_halten_png).is_file() and a.beauty_png
        assert Path(a.umriss_halten_png).parent.name == umrisshalt.ORDNER_MASKE
    for k in _gerechnete(ordner):
        vermerk = k[abholer.URTEIL_UMRISS_HALTEN]
        assert vermerk["art"] == umrisshalt.ART_IM_LAUF and vermerk["rand_px"] >= 3
        # Die Attrappe meldet keine gehaltenen Schritte — das heisst UNBEKANNT, nicht ja.
        assert vermerk["angewandt"] is None and "UNBEKANNT" in vermerk["grund"]


def test_vermerk_im_lauf_aus_dem_ergebnis():
    erg = {"parameter": {"umriss_halten_schritte": 20},
           "hinweise": (f"{umrisshalt.SATZ}: Hintergrund …", "anderes")}
    v = abholer.umriss_halten_vermerk_im_lauf(erg, {"rand_px": 19})
    assert v["angewandt"] is True and v["schritte"] == 20 and v["rand_px"] == 19
    assert v["hinweise"] == [f"{umrisshalt.SATZ}: Hintergrund …"]
    leer = abholer.umriss_halten_vermerk_im_lauf({"parameter": {}}, {})
    assert leer["angewandt"] is None and "UNBEKANNT" in leer["grund"]


def test_kamera_nachher_ohne_maske_kostet_das_bild_nicht(tmp_path):
    ki, grund, _m = _bilder(tmp_path)
    v = abholer.umriss_halten_der_kamera(ki, grund, None, B, H, tmp_path)
    assert v["angewandt"] is False and "Bauwerksmaske" in v["grund"]


def test_kamera_nachher_traegt_vorher_und_nachher(tmp_path):
    ki, grund, maske = _bilder(tmp_path)
    vorher = {"geom_iou": 0.5, "ausserhalb_umriss": {"anteil_haus": 2.1}}
    v = abholer.umriss_halten_der_kamera(
        ki, grund, maske, B, H, tmp_path, urteil_vorher=vorher,
        messen=lambda png: {"geom_iou": 0.6, "ausserhalb_umriss": {"anteil_haus": 0.1}})
    assert v["angewandt"] is True
    assert (v["geom_iou_vorher"], v["geom_iou_nachher"]) == (0.5, 0.6)
    assert (v["ausserhalb_vorher"], v["ausserhalb_nachher"]) == (2.1, 0.1)
    assert (tmp_path / umrisshalt.ORDNER_OHNE / "ki.png").is_file()


def test_satz_im_ergebnis_je_art():
    hinweise = []
    kosmo_szene._messschalter_eintragen(None, [
        {"kamera": "sSE", "geometrie_urteil": {
            "umriss_halten": {"angewandt": True, "art": "nachher", "rand_px": 19,
                              "geom_iou_nachher": 0.6, "ausserhalb_nachher": 0.1}}},
        {"kamera": "nNW", "geometrie_urteil": {
            "umriss_halten": {"angewandt": False, "art": "im_lauf", "grund": "kaputt"}}}],
        hinweise)
    assert hinweise[0].startswith(umrisshalt.SATZ) and "'nachher'" in hinweise[0]
    assert "ausserhalb des Hauses" in hinweise[0] and "0.1" in hinweise[0]
    assert "NICHT angewandt — kaputt" in hinweise[1]


# ============================================================== Papier

def test_das_planblatt_traegt_seine_waechterzeilen_und_die_optionen():
    text = (WURZEL / "docs" / "PLAN_MATERIAL_UND_UMRISS_2026-10-21.md").read_text(
        encoding="utf-8")
    zeilen = text.splitlines()
    assert any(z.startswith("**Codestand:** `") for z in zeilen)
    assert any(z.startswith("**Grundlage:** ") for z in zeilen)
    assert "## Zu entscheiden" in text
    for stichwort in ("control_guidance_start", "Canny", "Inpaint", "Apache-2.0", "VRAM",
                      "vis.umriss_halten", "vis.material_vorne"):
        assert stichwort in text, stichwort


def _messauftrag():
    treffer = []
    for pfad in sorted((WURZEL / "auftraege" / "offen").glob("auf-2026102*-*.json")):
        daten = json.loads(pfad.read_text(encoding="utf-8"))
        # Der Messauftrag DIESES Strangs (303); der Nachfolger 307 traegt «Strang Kern».
        if ("vis.umriss_halten" in json.dumps(daten.get("params", {}))
                and "Strang Treue" in daten.get("beschreibung", "")):
            treffer.append(daten)
    assert len(treffer) == 1, [t.get("auftrag_id") for t in treffer]
    return treffer[0]


def test_der_messauftrag_ist_gueltig_und_vollstaendig():
    daten = _messauftrag()
    assert auftrag.pruefe_auftrag(daten) == []
    assert daten["worker"] == "local" and daten["art"] == "qa"
    text = daten["anweisung"]
    for stichwort in ("Kontrolle", "geom_iou", "ausserhalb_umriss_anteil", "Sichtbeton?",
                      "Tafel", "EINBAU", "NICHT", "WAS AM HEIM-PC JETZT ANDERS RECHNET",
                      "vis.umriss_halten", "vis.material_vorne", "bildpunktgleich"):
        assert stichwort in text, stichwort
    assert "FLUX.1-dev" in text and "SDXL" in text
