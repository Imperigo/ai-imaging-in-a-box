"""Entscheid 117 (21.10.2026, Variante A: erst messen, dann am Bild entscheiden).

Zwei Messschalter, beide **Vorgabe aus**, keiner im Vertrag:

* ``vis.farbabgleich`` — das KI-Bild bekommt Mittel und Streuung der Farben des Cycles-Bilds
  (:mod:`aiimaging.farbabgleich`). **Kein Bildpunkt wandert**: Die Proben beweisen es an der
  reinen Funktion (vertauschte Bildpunkte geben vertauschte Ergebnisse, gleiche Kantenkarte,
  gleiche Umrisstreue) und im Lauf (die Prüfung misst dasselbe, ``geom_iou`` vor und nach).
* ``vis.bildeingang`` — das Cycles-Bild geht **zusätzlich** zur Tiefe ins Modell, über den
  vorbereiteten, ungemessenen eigenen Start (``Backbone.bildeingang_weg``).

Dazu der Messauftrag auf-20261021-298. Reine Funktionen und der Lauf mit Attrappen (Regel 2);
Testbilder synthetisch (Regel 3).
"""
from __future__ import annotations

import dataclasses
import hashlib
import json
import random
from pathlib import Path

import pytest

from aiimaging import (abholer, auftrag, backbone, bildlesen, bildschreiben, bruecke,
                       farbabgleich, kosmo_szene, render, umriss)

WURZEL = Path(__file__).resolve().parents[1]
B, H = 64, 40


def _bild(ton=(1.0, 1.0, 1.0), *, rauschen=0.0, seed=0):
    """Ein Haus mit Fenstern, Dach, Himmel und Boden — flache Flächen, klare Kanten."""
    zufall = random.Random(seed)
    aus = []
    for y in range(H):
        for x in range(B):
            haus = 16 < x < 46 and 12 < y < 34
            dach = 16 < x < 46 and 8 < y <= 12
            fenster = haus and (x - 19) % 8 < 3 and (y - 15) % 7 < 3
            farbe = (150, 150, 155) if haus else ((120, 60, 50) if dach else (90, 140, 220))
            if fenster:
                farbe = (40, 50, 60)
            if y >= 34:
                farbe = (110, 105, 95)
            aus.append(tuple(min(255, max(0, int(c * ton[i] + zufall.gauss(0, rauschen))))
                             for i, c in enumerate(farbe)))
    return aus


KI = _bild()
CYCLES_ABEND = _bild((1.25, 0.95, 0.7))


def _lum(farben):
    return [(farbabgleich.LR * r + farbabgleich.LG * g + farbabgleich.LB * b) / 255.0
            for r, g, b in farben]


# ====================================================================== die reine Funktion

def test_nur_farbe_naehert_sich():
    neu, vermerk = farbabgleich.gleiche_ab(KI, CYCLES_ABEND)
    assert len(neu) == len(KI)
    assert vermerk["angewandt"] is True and vermerk["bildpunkte_verschoben"] is False
    assert vermerk["abstand_nachher"] < 0.1 * vermerk["abstand_vorher"]
    # Die Farbstimmung kommt an: abends waermer (mehr Rot, weniger Blau als vorher).
    vor, nach = vermerk["kennwerte_ki"], vermerk["kennwerte_nachher"]
    assert nach["cr"]["mittel"] > vor["cr"]["mittel"]
    assert nach["cb"]["mittel"] < vor["cb"]["mittel"]


def test_kein_bildpunkt_wandert_vertauschen_vertauscht_nur():
    """Der Beweis, dass nur die Farbe zählt: Werden die Bildpunkte vorher vertauscht, ist das
    Ergebnis genau das vertauschte Ergebnis — der Wert eines Punkts hängt an keinem Nachbarn."""
    reihenfolge = list(range(len(KI)))
    random.Random(7).shuffle(reihenfolge)
    neu, _ = farbabgleich.gleiche_ab(KI, CYCLES_ABEND)
    neu_vertauscht, _ = farbabgleich.gleiche_ab([KI[i] for i in reihenfolge], CYCLES_ABEND)
    assert neu_vertauscht == [neu[i] for i in reihenfolge]


def test_gleiche_farbe_gibt_gleiche_farbe():
    neu, _ = farbabgleich.gleiche_ab(KI, CYCLES_ABEND)
    abbildung = {}
    for alt, ergebnis in zip(KI, neu):
        assert abbildung.setdefault(alt, ergebnis) == ergebnis


def test_kantenkarte_und_umrisstreue_bleiben_gleich():
    neu, _ = farbabgleich.gleiche_ab(KI, CYCLES_ABEND)
    assert umriss.bildkanten(_lum(KI), B, H) == umriss.bildkanten(_lum(neu), B, H)
    assert farbabgleich.kanten_iou(KI, neu, B, H) == 1.0
    # Eine Soll-Karte wie aus Blender: Haus nah, sonst Hintergrund.
    soll = [10.0 if (16 < x < 46 and 8 < y < 34) else 1e10 for y in range(H) for x in range(B)]
    vorher = umriss.umriss_treue(_lum(KI), soll, B, H)
    nachher = umriss.umriss_treue(_lum(neu), soll, B, H)
    assert vorher == nachher


def test_mit_rauschen_bleiben_die_kanten_fast_gleich_und_es_wird_gezaehlt():
    """Am verrauschten Bild kippen nur Kanten an der Schwelle (Rundung auf 8 Bit) — der
    Vermerk zählt es, statt es zu verschweigen."""
    ki = _bild(rauschen=5.0, seed=1)
    neu, _ = farbabgleich.gleiche_ab(ki, _bild((1.25, 0.95, 0.7), rauschen=5.0, seed=2))
    assert farbabgleich.kanten_iou(ki, neu, B, H) > 0.85


def test_die_streckung_ist_begrenzt_und_es_steht_da():
    flach = [(120, 121, 122)] * (B * H - 1) + [(122, 121, 120)]
    _neu, vermerk = farbabgleich.gleiche_ab(flach, CYCLES_ABEND)
    oben = farbabgleich.STRECKUNG_GRENZEN[1]
    assert vermerk["begrenzt"]
    assert all(v <= oben for v in vermerk["streckung"].values())


def test_leeres_bild_wird_abgewiesen():
    with pytest.raises(farbabgleich.FarbabgleichError):
        farbabgleich.gleiche_ab([], CYCLES_ABEND)


def test_datei_ungleiche_masse_schreibt_nichts(tmp_path):
    ki = bildschreiben.schreibe_farb_png(tmp_path / "ki.png", KI, B, H)
    klein = bildschreiben.schreibe_farb_png(tmp_path / "cy.png", [(1, 2, 3)] * 4, 2, 2)
    vorher = ki.read_bytes()
    vermerk = farbabgleich.gleiche_datei_ab(ki, klein, ki)
    assert vermerk["angewandt"] is False and "ungleiche Masse" in vermerk["grund"]
    assert ki.read_bytes() == vorher
    ohne = farbabgleich.gleiche_datei_ab(ki, tmp_path / "fehlt.png", ki)
    assert ohne["angewandt"] is False and ki.read_bytes() == vorher


# ====================================================================== die Schalter

def _szene(prompt="a house", **vis):
    return {"geometry": {"path": "model.glb", "format": "glb"}, "cameras": "auto",
            "render": {"samples": 8}, "style": {"prompt": prompt}, "vis": vis}


def test_ohne_schalter_ist_alles_aus():
    # Seit Entscheid 138 ist der Bildeingang Vorgabe (0,5) fuer Varianten; aus nur mit `false`.
    for vis in ({}, {"farbabgleich": False, "bildeingang": None}, {"farbabgleich": None}):
        szene = kosmo_szene.lies_szene(_szene(**vis), streng=False)
        assert szene["farbabgleich"] is False and szene["bildeingang"] == 0.5
        assert not szene["maengel"]
    # Masstreue (A0051): `false` ist das aufgehobene freie Bild — ein endgueltiger Mangel.
    szene = kosmo_szene.lies_szene(_szene(bildeingang=False), streng=False)
    assert szene["bildeingang"] is None
    assert szene["maengel_endgueltig"] == (kosmo_szene.masstreue_satz_bildeingang_aus(),)


def test_mit_schaltern():
    szene = kosmo_szene.lies_szene(_szene(farbabgleich=True, bildeingang=0.55), streng=False)
    assert szene["farbabgleich"] is True and szene["bildeingang"] == 0.55
    assert not szene["maengel"]


@pytest.mark.parametrize("vis, wort, endgueltig", [
    ({"farbabgleich": "true"}, "erwartet war true", False),
    ({"farbabgleich": True, "skip": True}, "zugleich", True),
    ({"bildeingang": "0.5"}, "erwartet war eine Staerke", False),
    ({"bildeingang": 0.0}, "erwartet war eine Staerke", False),
    ({"bildeingang": 1.5}, "erwartet war eine Staerke", False),
    ({"bildeingang": True}, "erwartet war eine Staerke", False),
    ({"bildeingang": 0.55, "skip": True}, "zugleich", True),
    ({"bildeingang": 0.55, "guete": "vorschau"}, "Vorschau", True),
    ({"bildeingang": 0.55, "backbone": "qwen"}, "kein Weg vorbereitet", True),
])
def test_falsche_schalter_sind_maengel(vis, wort, endgueltig):
    szene = kosmo_szene.lies_szene(_szene(**vis), streng=False)
    assert any(wort in m for m in szene["maengel"]), szene["maengel"]
    assert any(wort in m for m in szene["maengel_endgueltig"]) is endgueltig


def test_beide_schalter_sind_keine_vertragsfelder():
    assert {"farbabgleich", "bildeingang"} <= set(kosmo_szene.BEKANNTE_FELDER["vis"])
    assert "farbabgleich" in kosmo_szene.DURCHGEREICHT
    assert "bildeingang" in kosmo_szene.DURCHGEREICHT


# ====================================================================== das Register

def test_das_urteil_bildeingang_traegt_bleibt_bis_gemessen():
    eintrag = backbone.hole("z-image-turbo")
    assert eintrag.bildeingang_traegt is False            # gemessen auf-123, unveraendert
    assert eintrag.bildeingang_weg == backbone.BILDEINGANG_EIGENER_START
    assert "auf-20261021-298" in eintrag.bildeingang_weg_beleg
    assert backbone.bildeingang_weg_fuer("qwen-image-edit-2511") is None
    assert render.VORGABE_BACKBONE == "z-image-turbo"


def test_ein_weg_an_der_falschen_familie_kommt_nicht_ins_register():
    falsch = dataclasses.replace(backbone.hole("qwen-image-edit-2511"), name="probe-falsch",
                                 bildeingang_weg=backbone.BILDEINGANG_EIGENER_START,
                                 bildeingang_weg_beleg="probe")
    with pytest.raises(backbone.BackboneError):
        backbone._eintrag(falsch)
    ohne_beleg = dataclasses.replace(backbone.hole("z-image-turbo"), name="probe-ohne",
                                     bildeingang_weg_beleg=None)
    with pytest.raises(backbone.BackboneError):
        backbone._eintrag(ohne_beleg)
    assert "probe-falsch" not in backbone.BACKBONES and "probe-ohne" not in backbone.BACKBONES


# ====================================================================== der Render-Auftrag

def _auftrag(tmp_path, **kw):
    tiefe = tmp_path / "tiefe.png"
    tiefe.write_bytes(bildschreiben.schreibe_graustufen_png(
        tmp_path / "t.png", [0.5] * 4, 2, 2).read_bytes())
    return render.RenderAuftrag(depth_png=str(tiefe), prompt="a house", **kw)


def test_ohne_schalter_ist_der_parametersatz_der_von_vorher(tmp_path):
    eintrag = backbone.hole("z-image-turbo")
    a = _auftrag(tmp_path, beauty_png=str(tmp_path / "t.png"))
    satz = render._baue_parameter(a, eintrag)
    assert satz["modus"] == render.MODUS_IMAGE_EDIT
    assert "bildeingang_staerke" not in satz and "bildeingang_weg" not in satz
    assert not [h for h in render._hinweise(a, satz, backbone.pruefe_lizenz(eintrag.name)) if "bildeingang" in h]


def test_mit_schalter_eigener_modus_und_hinweis(tmp_path):
    eintrag = backbone.hole("z-image-turbo")
    a = _auftrag(tmp_path, beauty_png=str(tmp_path / "t.png"), bildeingang_staerke=0.55)
    assert not [m for m in render.pruefe_auftrag(a) if "bildeingang" in m]
    satz = render._baue_parameter(a, eintrag)
    assert satz["modus"] == render.MODUS_BILD_UND_TIEFE
    assert satz["bildeingang_staerke"] == 0.55
    assert satz["bildeingang_weg"] == backbone.BILDEINGANG_EIGENER_START
    assert any("MESSSCHALTER bildeingang_staerke" in h for h in render._hinweise(a, satz, backbone.pruefe_lizenz(eintrag.name)))


@pytest.mark.parametrize("kw, wort", [
    ({"bildeingang_staerke": 0.55}, "ohne beauty_png"),
    ({"bildeingang_staerke": 0.0, "beauty_png": "B"}, "erwartet eine Zahl"),
    ({"bildeingang_staerke": 0.55, "beauty_png": "B", "backbone": "qwen-image-edit-2511"},
     "kein Weg"),
])
def test_bildeingang_maengel_im_auftrag(tmp_path, kw, wort):
    if kw.get("beauty_png") == "B":
        kw = dict(kw, beauty_png=str(bildschreiben.schreibe_farb_png(
            tmp_path / "b.png", [(1, 2, 3)] * 4, 2, 2)))
    maengel = render.pruefe_auftrag(_auftrag(tmp_path, **kw))
    assert any(wort in m for m in maengel), maengel


def test_die_staerke_erreicht_das_modell(tmp_path):
    gesehen = {}

    def modell(parameter):
        gesehen.update(parameter)
        ziel = parameter["ausgabe_png"]
        Path(ziel).write_bytes(Path(parameter["depth_png"]).read_bytes())
        return {"bild_png": ziel, "hinweise": (), "modus_bestellt": parameter["modus"],
                "modus_gerechnet": parameter["modus"]}

    beauty = bildschreiben.schreibe_farb_png(tmp_path / "b.png", [(1, 2, 3)] * 4, 2, 2)
    a = _auftrag(tmp_path, beauty_png=str(beauty), bildeingang_staerke=0.4,
                 ausgabe_png=str(tmp_path / "aus.png"))
    erg = render.rendere(a, modell=modell)
    assert erg["status"] == "ok", erg
    assert gesehen["modus"] == render.MODUS_BILD_UND_TIEFE
    assert gesehen["bildeingang_staerke"] == 0.4


# ====================================================================== im Lauf (Attrappen)

def _lauf_mit(tmp_path, **vis):
    from test_kettenlauf_26august import _auftragsordner, _kette, _lauf
    ordner = _auftragsordner(tmp_path / "a")
    pfad = ordner / bruecke.DATEI_SZENE
    szene = json.loads(pfad.read_text(encoding="utf-8"))
    szene["vis"].update(vis)
    pfad.write_text(json.dumps(szene), encoding="utf-8")
    protokoll, attrappen = _kette(tmp_path / "k")
    multipass_alt, rendere_alt = attrappen["_multipass"], attrappen["_rendere"]

    def multipass(glb, aus, **kw):
        bericht = multipass_alt(glb, aus, **kw)
        schoen = bildschreiben.schreibe_farb_png(Path(aus) / "beauty_.png", CYCLES_ABEND, B, H)
        return dict(bericht, beauty_png=str(schoen))

    def rendere(a, **kw):
        erg = rendere_alt(a, **kw)
        bildschreiben.schreibe_farb_png(a.ausgabe_png, KI, B, H)
        return erg

    attrappen = dict(attrappen, _multipass=multipass, _rendere=rendere)
    antwort = _lauf(tmp_path / "l", ordner, attrappen)
    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort["grund"]
    return ordner, antwort, protokoll


def _sha(pfad):
    return hashlib.sha256(Path(pfad).read_bytes()).hexdigest()


def _gefunden(wurzel, relativ):
    """Der Befund traegt Pfade ohne Ordner (Regel 3) — die Datei unter der Ausgabe suchen."""
    treffer = [p for p in Path(wurzel).rglob(Path(relativ).name)
               if p.as_posix().endswith(Path(relativ).as_posix())]
    assert len(treffer) == 1, (relativ, treffer)
    return treffer[0]


def test_ohne_schalter_kein_vermerk_und_das_bild_der_attrappe(tmp_path):
    # Masstreue (A0051): «ohne Schalter» heisst mit der Vorgabe des Bildeingangs — aus gibt es nicht mehr.
    ordner, antwort, protokoll = _lauf_mit(tmp_path)
    kameras = abholer.lies_befund(ordner)["kameras"]
    assert kameras and all(abholer.URTEIL_FARBABGLEICH not in k for k in kameras)
    assert all(a.bildeingang_staerke == kosmo_szene.BILDEINGANG_VORGABE for a in protokoll["render"])
    referenz = bildschreiben.schreibe_farb_png(tmp_path / "ref.png", KI, B, H)
    for k in kameras:
        if not k.get("doppelt_von"):
            bild = _gefunden(tmp_path / "l", f"{k['kamera']}/{k['bild_png']}")
            assert _sha(bild) == _sha(referenz)
            assert not (bild.parent / farbabgleich.ORDNER_OHNE).exists()


def test_mit_farbabgleich_das_original_bleibt_und_die_pruefung_misst_dasselbe(tmp_path):
    _o, ohne, _p = _lauf_mit(tmp_path / "ohne")
    ordner, mit, _p = _lauf_mit(tmp_path / "mit", farbabgleich=True)
    referenz = bildschreiben.schreibe_farb_png(tmp_path / "ref.png", KI, B, H)
    kameras = [k for k in abholer.lies_befund(ordner)["kameras"] if not k.get("doppelt_von")]
    assert kameras
    for k in kameras:
        vermerk = k[abholer.URTEIL_FARBABGLEICH]
        assert vermerk["angewandt"] is True, vermerk
        assert vermerk["kanten_iou"] == 1.0
        assert vermerk["geom_iou_gleich"] in (True, None)
        roh = _gefunden(tmp_path / "mit", vermerk["ohne_farbabgleich_png"])
        bild = roh.parent.parent / Path(k["bild_png"]).name
        assert _sha(roh) == _sha(referenz), "das Original liegt unveraendert daneben"
        assert _sha(bild) != _sha(referenz), "geliefert wird das abgeglichene Bild"
        geliefert = ordner / Path(k["bild_png"]).name
        assert _sha(geliefert) == _sha(bild), "in den Auftragsordner geht das abgeglichene"
        farben, b, h = bildlesen.lies_png_farben(bild)
        assert (b, h) == (B, H)
        assert umriss.bildkanten(_lum(farben), B, H) == umriss.bildkanten(_lum(KI), B, H)
    # Die Pruefung misst das KI-Bild wie ohne Schalter: dasselbe Urteil im Vertrag — bis auf
    # den Satz in `verdict.hinweise` und `angewandt.farbabgleich` (auf-20261021-298, B1).
    qa_ohne, qa_mit = json.loads(json.dumps(ohne["ergebnis"]["qa"])), json.loads(
        json.dumps(mit["ergebnis"]["qa"]))
    saetze = qa_mit["verdict"].pop("hinweise", [])
    # Beide Laeufe mit der Vorgabe des Bildeingangs (seit der Masstreue, A0051, gibt es kein «aus»
    # mehr) — verglichen wird wie bisher alles ausser dem Satz des Farbabgleichs.
    assert qa_ohne["verdict"].pop("hinweise", []) == [
        h for h in saetze if not h.startswith(kosmo_szene.SATZ_FARBABGLEICH)]
    assert qa_ohne == qa_mit
    assert any(h.startswith(kosmo_szene.SATZ_FARBABGLEICH) for h in saetze)
    assert "farbabgleich" not in json.dumps(ohne["ergebnis"])
    assert set(mit["ergebnis"]["angewandt"]["farbabgleich"]["kameras"]) == {
        k["kamera"] for k in kameras}


def test_der_bildeingang_erreicht_das_bildmodell(tmp_path):
    _o, _a, protokoll = _lauf_mit(tmp_path, bildeingang=0.7)
    assert protokoll["render"]
    for a in protokoll["render"]:
        assert a.bildeingang_staerke == 0.7 and a.beauty_png


# ====================================================================== der Messauftrag 298

def test_der_messauftrag_298_ist_gueltig_und_vollstaendig():
    pfad = WURZEL / "auftraege" / "offen" / "auf-20261021-298.json"
    daten = json.loads(pfad.read_text(encoding="utf-8"))
    assert auftrag.pruefe_auftrag(daten) == []
    assert daten["worker"] == "local" and daten["art"] == "qa" and daten["rang"] == 85
    assert daten["auflagen"]["leistungsgrenze_w"] == 400
    assert daten["params"]["entscheide"][0] == "117"
    text = daten["anweisung"]
    for stichwort in ("vis.farbabgleich", "vis.bildeingang", "Apache-2.0", "VRAM",
                      "morgen", "abend", "bedeckt", "0.4", "0.55", "0.7", "bildpunktgleich",
                      "geom_iou", "ausserhalb_umriss_anteil", "Kontrast", "960",
                      "WAS AM HEIM-PC JETZT ANDERS RECHNET", "EINBAU", "NICHT:",
                      "FLUX", "SDXL", "Tongyi-MAI/Z-Image-Turbo",
                      "alibaba-pai/Z-Image-Turbo-Fun-Controlnet-Union"):
        assert stichwort in text, stichwort


def test_entscheid_117_steht_in_der_tabelle_und_im_planblatt():
    tabelle = (WURZEL / "docs" / "ENTSCHEIDE_IPAD_2026-09-21.md").read_text(encoding="utf-8")
    assert any(z.startswith("| 117 |") for z in tabelle.splitlines())
    plan = (WURZEL / "docs" / "PLAN_LICHT_INS_KI_BILD_2026-10-21.md").read_text(encoding="utf-8")
    assert "Entscheid 117" in plan
