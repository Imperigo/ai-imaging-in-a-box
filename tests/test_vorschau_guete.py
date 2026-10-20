"""Die schnelle KI-Vorschau — Owner-Entscheide 104–104b (20.10.2026).

Am Render-Knoten steht der Schalter «Güte: Vorschau | Voll», Vorgabe Vorschau. Im Vertrag
heisst er ``vis.guete`` (``'vorschau' | 'voll'``, fehlt = ``'voll'``), abgewiesen zusammen
mit ``vis.skip``; im Ergebnis steht oben ``guete``.

Der Anlass: Der Demolauf vom 20.10.2026 brauchte rund neun Minuten je Variante — er
rechnete das Forschungsmodell ``qwen-image-2.1`` mit 40 Schritten. Ziel ist höchstens zwei
Minuten (L4-17). Was die Vorschau anders macht, und was hier bewacht ist:

* immer :data:`aiimaging.backbone.VORSCHAU_BACKBONE`, auch wenn ``vis.backbone`` ein
  anderes nennt — und das Ergebnis sagt, welches gerechnet hat;
* genau EIN Startwert (``vis.seed``, sonst der der Grundlage, sonst 0);
* die Schritte aus dem Registereintrag (``vorschau_schritte``, 8 bei z-image-turbo);
* verkleinerte Steuerbilder für den KI-Schritt, die Grundlage bleibt unverändert;
* die Prüfung läuft (104a), und ``verdict.reason`` beginnt mit «VORSCHAU».

Bei ``'voll'`` oder ohne Feld bleibt alles, wie es war — auch die 20 Schritte von
z-image-turbo (das ist Auftrag 288).

Regel 3: alle Modelle, Bilder und Kameras synthetisch. Blender und Bildmodell sind
Attrappen wie in ``tests/test_grundlage_varianten.py``.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from aiimaging import abholer, backbone, bildlesen, bildschreiben, bruecke, eigene_quelle
from aiimaging import jobs, kosmo_szene

from test_grundlage_varianten import _ordner, _szene, _vertrag
from test_kettenlauf_26august import _kette, _lauf
from test_fortschritt_lauf import _eigener_auftrag

#: Die Grösse der Grundlage in diesen Proben — dasselbe Seitenverhältnis wie die Vorgabe
#: der Gegenseite (1600 x 1000), aber klein genug für die stdlib.
GRUNDLAGE_B, GRUNDLAGE_H = 200, 125
#: Die lange Seite der Vorschau in diesen Proben (im Betrieb 1024).
LANGE_SEITE = 128


def _attrappen(tmp_path):
    """Blender schreibt Tiefe und Schönbild in Grundlagengrösse; das Bildmodell schreibt
    ein Bild in der Grösse der Tiefenkarte, die es bekam — wie die echte Pipeline."""
    protokoll, attrappen = _kette(tmp_path)
    protokoll["qa"] = []

    def multipass(glb, aus, **kw):
        protokoll["multipass"].append(kw)
        aus = Path(aus)
        aus.mkdir(parents=True, exist_ok=True)
        tiefe = aus / "tiefe_norm.png"
        bildschreiben.schreibe_graustufen_png(
            tiefe, [((x + y) % 50) / 50 for y in range(GRUNDLAGE_H)
                    for x in range(GRUNDLAGE_B)], GRUNDLAGE_B, GRUNDLAGE_H)
        schoen = aus / "beauty_.png"
        bildschreiben.schreibe_farb_png(
            schoen, [(x % 256, y % 256, 90) for y in range(GRUNDLAGE_H)
                     for x in range(GRUNDLAGE_B)], GRUNDLAGE_B, GRUNDLAGE_H)
        from test_kettenlauf_26august import BBOX_BAUWERK, BBOX_SZENE, _kamerablock
        return {"depth_png": str(tiefe), "beauty_png": str(schoen),
                "kamera": _kamerablock(kw.get("kamera")),
                "bbox": BBOX_SZENE, "bbox_bauwerk": BBOX_BAUWERK,
                "sonne": {"weg": "vorgabe", "konvention": "von_sueden"}}

    def rendere(a, **kw):
        protokoll["render"].append(a)
        b, h = bildschreiben.png_masse(a.depth_png)
        Path(a.ausgabe_png).parent.mkdir(parents=True, exist_ok=True)
        bildschreiben.schreibe_farb_png(a.ausgabe_png, [(120, 130, 140)] * (b * h), b, h)
        return {"status": "ok", "bild_png": a.ausgabe_png, "hinweise": (),
                "backbone": a.backbone,
                "lizenz": {"lizenz": backbone.hole(a.backbone).lizenz},
                "parameter": {"fuehrung_angewandt": False},
                "geraeteweg": {"geraet": "cuda", "ladeweg": None, "gemeldet": True,
                               "grund": ""}}

    echt_qa = attrappen["_qa"]

    def qa(png, *a, **k):
        protokoll["qa"].append(bildschreiben.png_masse(png))
        return echt_qa(png, *a, **k)

    return protokoll, dict(attrappen, _multipass=multipass, _rendere=rendere, _qa=qa)


def _rechne(tmp_path, attrappen, name, **vis):
    ordner = _ordner(tmp_path, name, vis=vis)
    antwort = _lauf(tmp_path, ordner, attrappen, vorschau_lange_seite=LANGE_SEITE)
    return ordner, antwort


# ======================================================================================
# Die Vorschau rechnet anders
# ======================================================================================

def test_die_vorschau_rechnet_schnell_und_wird_geprueft(tmp_path):
    protokoll, attrappen = _attrappen(tmp_path)
    ordner, antwort = _rechne(tmp_path, attrappen, "vorschau", guete="vorschau")

    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort["grund"]
    auftraege = protokoll["render"]
    assert len(auftraege) == 3, "drei Kameras, je genau EIN KI-Lauf"
    assert {a.seed for a in auftraege} == {0}
    assert {a.schritte for a in auftraege} == {8}
    assert {a.backbone for a in auftraege} == {backbone.VORSCHAU_BACKBONE}
    # Die Steuerbilder sind verkleinert, mit Seitenverhältnis und auf das Raster.
    for a in auftraege:
        assert abholer.VORSCHAU_ORDNER in Path(a.depth_png).parts
        assert bildschreiben.png_masse(a.depth_png) == (128, 80)
        assert bildschreiben.png_masse(a.beauty_png) == (128, 80)
    # Geprueft wurde, und zwar auf der Groesse der Grundlage (104a).
    assert protokoll["qa"] == [(GRUNDLAGE_B, GRUNDLAGE_H)] * 3
    vertrag = _vertrag(ordner)
    assert vertrag["guete"] == "vorschau"
    assert vertrag["engine_used"] == backbone.VORSCHAU_BACKBONE
    assert vertrag["qa"]["verdict"]["reason"].startswith(kosmo_szene.VORSCHAU_ANFANG)
    assert "8 Schritte" in vertrag["qa"]["verdict"]["reason"]
    for name in vertrag["images"]:
        assert bildschreiben.png_masse(ordner / name) == (GRUNDLAGE_B, GRUNDLAGE_H)
    assert {e["seed"] for e in vertrag["qa_je_kamera"]} == {0}


def test_die_vorschau_uebergeht_ein_bestelltes_bildmodell_und_sagt_es(tmp_path):
    protokoll, attrappen = _attrappen(tmp_path)
    ordner, antwort = _rechne(tmp_path, attrappen, "qwen", guete="vorschau",
                              backbone="qwen-image-2.1")

    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort["grund"]
    assert {a.backbone for a in protokoll["render"]} == {backbone.VORSCHAU_BACKBONE}
    assert {a.schritte for a in protokoll["render"]} == {8}, "nicht die 40 von qwen"
    vertrag = _vertrag(ordner)
    assert vertrag["engine_used"] == backbone.VORSCHAU_BACKBONE
    assert "engine_license_open" not in vertrag
    vermerk = abholer.lies_befund(ordner)["kameras"][0][kosmo_szene.URTEIL_GUETE]
    assert vermerk["backbone_bestellt"] == "qwen-image-2.1"
    assert vermerk["backbone"] == backbone.VORSCHAU_BACKBONE
    assert any("Voll" in h for h in vermerk["hinweise"])


def test_ein_bestellter_seed_gilt_auch_in_der_vorschau(tmp_path):
    protokoll, attrappen = _attrappen(tmp_path)
    _rechne(tmp_path, attrappen, "fest", guete="vorschau", seed=42)
    assert {a.seed for a in protokoll["render"]} == {42}


# ======================================================================================
# Die Grundlage bleibt — und ihr Startwert gilt
# ======================================================================================

def _dateien_der_grundlage(tmp_path, kennung):
    satz_pfad = tmp_path / "aus" / abholer.GRUNDLAGEN_ORDNER / f"{kennung}.json"
    satz = json.loads(satz_pfad.read_text(encoding="utf-8"))
    dateien = {}
    for eintrag in satz["kameras"]:
        for feld in ("depth_png", "beauty_png"):
            pfad = Path(eintrag["bericht"][feld])
            dateien[str(pfad)] = pfad.read_bytes()
    return satz_pfad.read_bytes(), dateien


def test_die_vorschau_nimmt_die_grundlage_und_laesst_sie_unveraendert(tmp_path):
    protokoll, attrappen = _attrappen(tmp_path)
    erster, antwort = _rechne(tmp_path, attrappen, "grund", skip=True)
    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort["grund"]
    kennung = _vertrag(erster)["grundlage"]["id"]
    vorher = _dateien_der_grundlage(tmp_path, kennung)
    blender = len(protokoll["multipass"])

    vorschau, antwort = _rechne(tmp_path, attrappen, "vorschau", guete="vorschau",
                                grundlage=kennung)

    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort["grund"]
    assert len(protokoll["multipass"]) == blender, "kein neuer Blender-Lauf"
    assert _vertrag(vorschau)["grundlage"] == {"id": kennung, "wiederverwendet": True}
    assert _dateien_der_grundlage(tmp_path, kennung) == vorher, "Grundlage unverändert"
    assert all(p not in vorher[1] for p in (a.depth_png for a in protokoll["render"])), \
        "die Vorschau rechnet auf Kopien, nicht auf der Grundlage"

    # Und die volle Güte rechnet danach auf DERSELBEN Grundlage, mit ihren Originalen.
    n = len(protokoll["render"])
    voll, antwort = _rechne(tmp_path, attrappen, "voll", guete="voll", grundlage=kennung)
    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort["grund"]
    assert {a.depth_png for a in protokoll["render"][n:]} <= set(vorher[1])
    assert _vertrag(voll)["guete"] == "voll"


def test_die_vorschau_nimmt_den_startwert_der_grundlage(tmp_path):
    protokoll, attrappen = _attrappen(tmp_path)
    erster, _ = _rechne(tmp_path, attrappen, "erster", seed=5)
    kennung = _vertrag(erster)["grundlage"]["id"]
    satz = json.loads((tmp_path / "aus" / abholer.GRUNDLAGEN_ORDNER
                       / f"{kennung}.json").read_text(encoding="utf-8"))
    assert set(satz["seeds"].values()) == {5}
    n = len(protokoll["render"])

    _rechne(tmp_path, attrappen, "vorschau", guete="vorschau", grundlage=kennung)

    assert {a.seed for a in protokoll["render"][n:]} == {5}


def test_eine_alte_grundlage_ohne_startwert_ergibt_null():
    assert abholer.seeds_der_kamera({"guete": "vorschau"}, {"kameras": []}, "s",
                                    abholer.VORGABE_SEEDS) == (0,)


# ======================================================================================
# Volle Güte und fehlendes Feld: wie bisher
# ======================================================================================

@pytest.mark.parametrize("vis", [{}, {"guete": "voll"}])
def test_voll_und_ohne_feld_rechnen_wie_bisher(tmp_path, vis):
    protokoll, attrappen = _attrappen(tmp_path)
    ordner, antwort = _rechne(tmp_path, attrappen, "voll", **vis)

    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort["grund"]
    assert {a.backbone for a in protokoll["render"]} == {backbone.VORGABE_BACKBONE}
    assert {a.schritte for a in protokoll["render"]} == {backbone.SCHRITTE_STANDARD}
    for a in protokoll["render"]:
        assert abholer.VORSCHAU_ORDNER not in Path(a.depth_png).parts
        assert bildschreiben.png_masse(a.depth_png) == (GRUNDLAGE_B, GRUNDLAGE_H)
    vertrag = _vertrag(ordner)
    assert not vertrag["qa"]["verdict"]["reason"].startswith(kosmo_szene.VORSCHAU_ANFANG)
    if vis:
        assert vertrag["guete"] == "voll"
    else:
        assert "guete" not in vertrag, "rückwärtsverträglich: ohne Bestellung kein Feld"
    befund = abholer.lies_befund(ordner)
    assert all(k.get(kosmo_szene.URTEIL_GUETE) is None for k in befund["kameras"])


def test_voll_behaelt_die_auswahl_aus_drei_und_die_20_schritte():
    assert abholer.seeds_der_kamera({"guete": "voll"}, None, "s",
                                    abholer.VORGABE_SEEDS) == abholer.VORGABE_SEEDS
    assert abholer.seeds_der_kamera({}, None, "s", abholer.VORGABE_SEEDS) == (0, 1, 2)
    # Auftrag 288 misst, ob die volle Güte auf 8 Schritte geht — bis dahin 20.
    assert abholer.schritte_des_laufs({"backbone": "z-image-turbo"}) == 20
    assert abholer.schritte_des_laufs({"guete": "voll"}) == 20
    assert abholer.schritte_des_laufs({"backbone": "qwen-image-2.1"}) == 40
    assert abholer.schritte_des_laufs({"guete": "vorschau",
                                       "backbone": "qwen-image-2.1"}) == 8


# ======================================================================================
# Die Lesung im Vertrag
# ======================================================================================

@pytest.mark.parametrize("wert", ["vorschau", "voll"])
def test_guete_wird_gelesen(wert):
    szene = kosmo_szene.lies_szene(_szene(guete=wert), streng=False)
    assert szene["guete"] == wert
    assert not szene["maengel"]


def test_ohne_guete_ist_sie_none_und_null_ebenso():
    assert kosmo_szene.lies_szene(_szene(), streng=False)["guete"] is None
    szene = kosmo_szene.lies_szene(_szene(guete=None), streng=False)
    assert szene["guete"] is None and not szene["maengel"]


@pytest.mark.parametrize("wert", ["Vorschau", "fast", 1, True])
def test_eine_unbekannte_guete_ist_ein_mangel(wert):
    szene = kosmo_szene.lies_szene(_szene(guete=wert), streng=False)
    assert any("'vis.guete'" in m for m in szene["maengel"]), szene["maengel"]
    assert szene["guete"] is None


@pytest.mark.parametrize("wert", ["vorschau", "voll"])
def test_guete_und_skip_zugleich_werden_abgewiesen(wert):
    szene = kosmo_szene.lies_szene(_szene(guete=wert, skip=True), streng=False)
    assert any(m.startswith("'vis.guete'") and "zugleich" in m for m in szene["maengel"])


def test_guete_und_skip_halten_den_lauf_an(tmp_path):
    protokoll, attrappen = _attrappen(tmp_path)
    ordner = _ordner(tmp_path, "beides", skip=True, vis={"guete": "vorschau"})

    antwort = _lauf(tmp_path, ordner, attrappen)

    assert antwort["tat"] != abholer.TAT_VERARBEITET
    assert "vis.guete" in antwort["grund"]
    assert protokoll["multipass"] == [] and protokoll["render"] == []


def test_guete_ist_kein_unbekanntes_feld():
    assert "guete" in kosmo_szene.BEKANNTE_FELDER["vis"]
    assert "guete" in kosmo_szene.DURCHGEREICHT


# ======================================================================================
# Beide Ablagen gleich
# ======================================================================================

def _verarbeite_mit_guete(guete):
    def verarbeite(auftrag):
        bild = Path(auftrag["verzeichnis"]) / "bild.png"
        bildschreiben.schreibe_farb_png(bild, [(1, 2, 3)], 1, 1)
        return {"bilder": [str(bild)], "geometrie_urteil": None, "stil_urteil": None,
                "kameras": [], "zeiten": {"gesamt": 0.1}, "uebersprungen": False,
                "guete": guete}
    return verarbeite


def test_die_eigene_ablage_traegt_die_guete(tmp_path, monkeypatch):
    ablage, job_id = _eigener_auftrag(tmp_path, monkeypatch)
    bericht = abholer.durchgang(ablage, quelle=eigene_quelle,
                                darf_rechnen=lambda: (True, "frei"),
                                verarbeite=_verarbeite_mit_guete("vorschau"))
    assert bericht["verarbeitet"] == 1, bericht["ergebnisse"]
    vertrag = json.loads((ablage / job_id / eigene_quelle.DATEI_ERGEBNIS)
                         .read_text(encoding="utf-8"))
    assert vertrag["guete"] == "vorschau"
    assert vertrag["qa"]["verdict"]["reason"].startswith(kosmo_szene.VORSCHAU_ANFANG)
    assert jobs.lies_job(job_id, ablage / job_id)["status"] == jobs.STATUS_DONE


def test_die_bruecke_traegt_die_guete(tmp_path):
    ordner = _ordner(tmp_path, "bruecke", vis={"guete": "voll"})
    antwort = abholer.hole_einen(ordner, fremde_freigabe_gilt=True,
                                 verarbeite=_verarbeite_mit_guete("voll"))
    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort["grund"]
    assert _vertrag(ordner)["guete"] == "voll"


def test_ohne_guete_schreibt_keine_ablage_das_feld(tmp_path):
    ordner = _ordner(tmp_path, "ohne")
    abholer.hole_einen(ordner, fremde_freigabe_gilt=True,
                       verarbeite=_verarbeite_mit_guete(None))
    assert "guete" not in _vertrag(ordner)


# ======================================================================================
# Der Fortschritt bleibt sinnvoll (R37)
# ======================================================================================

def test_der_fortschritt_der_vorschau_steigt_bis_eins(tmp_path):
    protokoll, attrappen = _attrappen(tmp_path)
    gemeldet = []
    ordner = _ordner(tmp_path, "fort", vis={"guete": "vorschau"})

    _lauf(tmp_path, ordner, attrappen, vorschau_lange_seite=LANGE_SEITE,
          _melde=lambda o, p, dateien=None: gemeldet.append(dict(p)))

    pct = [p["pct"] for p in gemeldet]
    assert pct == sorted(pct) and pct[-1] == 1.0
    assert {p["phase"] for p in gemeldet} >= {"blender", "bildmodell", "pruefung"}
    assert {p["kamera_n"] for p in gemeldet} == {3}


# ======================================================================================
# Die Bausteine
# ======================================================================================

@pytest.mark.parametrize("vorlage, erwartet", [
    ((1600, 1000), (1024, 640)),
    ((1000, 1600), (640, 1024)),
    ((1920, 1080), (1024, 576)),
    ((2048, 2048), (1024, 1024)),
    ((800, 500), (800, 500)),
    ((1024, 640), (1024, 640)),
])
def test_die_groesse_der_vorschau(vorlage, erwartet):
    b, h = backbone.vorschau_groesse(*vorlage)
    assert (b, h) == erwartet
    if (b, h) != vorlage:
        assert b % backbone.PIXEL_RASTER == 0 and h % backbone.PIXEL_RASTER == 0


def test_die_schritte_stehen_am_registereintrag():
    assert backbone.hole(backbone.VORSCHAU_BACKBONE).vorschau_schritte == 8
    assert backbone.vorschau_schritte_fuer("z-image-turbo") == 8
    assert backbone.schritte_fuer("z-image-turbo") == backbone.SCHRITTE_STANDARD == 20
    # Ohne belegten Vorschauwert: die volle Zahl, keine erfundene.
    assert backbone.vorschau_schritte_fuer("qwen-image-2.1") == 40


@pytest.mark.parametrize("ohne_pillow", [False, True])
def test_skaliere_png_haelt_art_und_bittiefe(tmp_path, ohne_pillow):
    grau, farbe = tmp_path / "g.png", tmp_path / "f.png"
    bildschreiben.schreibe_graustufen_png(grau, [x / 39 for _ in range(25) for x in range(40)],
                                          40, 25)
    bildschreiben.schreibe_farb_png(farbe, [(x * 6, 0, 200) for _ in range(25)
                                            for x in range(40)], 40, 25)

    befund = bildschreiben.skaliere_png(grau, tmp_path / "g2.png", 16, 10,
                                        _ohne_pillow=ohne_pillow)
    assert befund["art"] == "grau"
    werte, b, h = bildlesen.lies_png_graustufen(tmp_path / "g2.png")
    assert (b, h) == (16, 10) and werte[0] < 0.1 < 0.9 < werte[15]
    bildschreiben.skaliere_png(farbe, tmp_path / "f2.png", 80, 50, _ohne_pillow=ohne_pillow)
    farben, b, h = bildlesen.lies_png_farben(tmp_path / "f2.png")
    assert (b, h) == (80, 50) and farben[0][2] == 200
