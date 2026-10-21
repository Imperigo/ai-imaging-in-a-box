"""Die Befunde aus ``auf-20261021-296`` (HomeStation, 21.10.2026): drei Punkte nach der Nachmessung.

Erfüllt war: abend hebt sich ab (Kontrast 41/39), der Satz «NICHT WIEDERZUERKENNEN» trifft abend
voll (0,005), ``drehung_je_kamera`` stimmt, ohne Stimmung bildpunktgleich, und 0,25 trennt das
Gipsmodell (0,0) vom Strassenbild (2,15). Offen blieben:

* **N1** — das Strassenbild (``faithful`` 0,3, Strassenprompt) entging dem Satz: ``geom_iou`` 0,197,
  aber das Bild ist fast ganz «Haus» (``n_ist`` 165'964 gegen ``n_soll`` 67'541, 2,46).
* **N6** (im Auftrag «N5») — ``seedauswahl.umriss_gilt`` stand nur, wenn falsch.
* **N3** — bei mittag hielt auch ``faithful`` 1,0 das Haus nicht im Umriss; nur der Gipsprompt mit
  «empty background, no other buildings» blieb drin. Vorbereitet als Schalter, Vorgabe aus.

Reine Funktionen und der Lauf mit Attrappen (Regel 2). Testdaten synthetisch (Regel 3); die Zahlen
sind die aus 296.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from aiimaging import abholer, auftrag, bruecke, kosmo_szene, umriss

WURZEL = Path(__file__).resolve().parents[1]

#: Die Bilder aus 296: (geom_iou, n_ist, ausserhalb_umriss_anteil, Haus selbst erkannt).
N_SOLL = 67541
BILDER_296 = {
    "abend_voll": (0.004992736647864836, 86044, 2.0855, False),
    "abend_vorschau": (0.3842293631679444, 76722, 1.9185, True),       # teilweise erkannt
    "weiss_f10": (0.8699735535057731, 77410, 0.0, True),
    "mittag_f10": (0.4910794347731981, 77128, 1.0077, True),           # erkannt, daneben gebaut
    "strasse_f03": (0.19726506419459372, 165964, 2.1481, False),
}


# ====================================================================== N1 · das Strassenbild

def test_die_schwellen_sind_benannt_und_gesetzt():
    assert umriss.WIEDERERKENNUNG_GEOM_IOU == 0.1
    assert umriss.WIEDERERKENNUNG_FLAECHE_VERHAELTNIS == 2.0
    assert umriss.WIEDERERKENNUNG_AUSSERHALB_ANTEIL == 1.5
    assert umriss.WIEDERERKENNUNG_GEOM_IOU_BEI_AUSSERHALB == 0.3
    quelle = (WURZEL / "src" / "aiimaging" / "umriss.py").read_text(encoding="utf-8")
    assert quelle.count("**Beide gesetzt, nicht gemessen:**") == 1
    assert "auf-20261021-296, N1" in quelle


@pytest.mark.parametrize("name", sorted(BILDER_296))
def test_die_regel_trifft_jedes_bild_aus_296_wie_gesehen(name):
    iou, n_ist, aussen, erkannt = BILDER_296[name]
    befund = umriss.wiedererkennung(iou, n_ist=n_ist, n_soll=N_SOLL, ausserhalb_anteil=aussen)
    assert befund["gilt"] is erkannt, name
    assert umriss.umriss_gilt(iou, n_ist=n_ist, n_soll=N_SOLL,
                              ausserhalb_anteil=aussen) is erkannt
    assert (befund["grund"] is None) is erkannt


def test_das_strassenbild_nennt_beide_ausloeser():
    iou, n_ist, aussen, _ = BILDER_296["strasse_f03"]
    befund = umriss.wiedererkennung(iou, n_ist=n_ist, n_soll=N_SOLL, ausserhalb_anteil=aussen)
    assert befund["ausloeser"] == [umriss.AUSLOESER_FLAECHE, umriss.AUSLOESER_AUSSERHALB]
    assert "Verhaeltnis 2.46" in befund["grund"] and "2.15 der Hausflaeche" in befund["grund"]
    # Jeder Auslöser für sich genügt.
    assert umriss.wiedererkennung(0.45, n_ist=2.01 * N_SOLL, n_soll=N_SOLL)["gilt"] is False
    assert umriss.wiedererkennung(0.29, ausserhalb_anteil=1.51)["gilt"] is False
    # An den Grenzen: genau 2,0 und genau 1,5 lösen nicht aus, 0,3 auch nicht.
    assert umriss.wiedererkennung(0.45, n_ist=2 * N_SOLL, n_soll=N_SOLL)["gilt"] is True
    assert umriss.wiedererkennung(0.29, ausserhalb_anteil=1.5)["gilt"] is True
    assert umriss.wiedererkennung(0.3, ausserhalb_anteil=4.0)["gilt"] is True


def test_ohne_zaehlung_gilt_die_regel_wie_bis_295():
    assert umriss.umriss_gilt(0.005) is False and umriss.umriss_gilt(0.197) is True
    assert umriss.wiedererkennung(None) is None
    assert umriss.wiedererkennung(0.5, n_ist=10, n_soll=0)["gilt"] is True     # kein Teiler
    assert umriss.wiedererkennung(0.5, n_ist=True, n_soll=1)["gilt"] is True   # kein bool
    assert umriss.wiedererkennung(0.2, ausserhalb_anteil=float("nan"))["gilt"] is True


def _urteil(name, kamera="sSE"):
    iou, n_ist, aussen, _ = BILDER_296[name]
    return {"kamera": kamera, "score": 0.0, "bestanden": False, "geom_iou": iou,
            "spearman": 0.5, "n_gemeinsam": 38473, "n_soll": N_SOLL, "n_ist": n_ist,
            "ausserhalb_umriss": {"anteil_haus": aussen, "n_haus": 58589}}


def _saetze(ergebnis):
    return [h for h in ergebnis["qa"]["verdict"].get("hinweise") or ()
            if h.startswith(kosmo_szene.SATZ_NICHT_WIEDERZUERKENNEN)]


def test_der_satz_steht_beim_strassenbild_und_der_vertrag_bleibt():
    je = [{"kamera": "sSE", "geometrie_urteil": _urteil("strasse_f03")}]
    e = kosmo_szene.als_ergebnis("vis-1-abcdef", ["a.png"],
                                 geometrie_urteil=je[0]["geometrie_urteil"], je_kamera=je)
    saetze = _saetze(e)
    assert len(saetze) == 1 and "'sSE'" in saetze[0]
    assert "165964 Punkte gegen 67541" in saetze[0] and "Verhaeltnis 2.46" in saetze[0]
    assert "ueber den Umriss" in saetze[0] and "gesetzt, nicht gemessen" in saetze[0]
    assert "Umriss-IoU" in saetze[0] and saetze[0] in e["hinweise"]
    gut = [{"kamera": "sSE", "geometrie_urteil": _urteil("mittag_f10")}]
    g = kosmo_szene.als_ergebnis("vis-1-abcdef", ["a.png"],
                                 geometrie_urteil=gut[0]["geometrie_urteil"], je_kamera=gut)
    assert _saetze(g) == []
    assert set(e["qa"]["geometry"]) == set(g["qa"]["geometry"])
    assert set(e.get("geometry_gates") or {}) == set(g.get("geometry_gates") or {})
    assert [set(k) for k in e["qa_je_kamera"]] == [set(k) for k in g["qa_je_kamera"]]


def test_abend_voll_behaelt_seinen_satz_aus_295():
    """Der Satz aus 295 bleibt wörtlich, die Baumasse kommt als zweiter Teil dazu."""
    je = [{"kamera": "sSE", "geometrie_urteil": dict(_urteil("abend_voll"), n_gemeinsam=763)}]
    satz = _saetze(kosmo_szene.als_ergebnis("vis-1-abcdef", ["a.png"],
                                            geometrie_urteil=je[0]["geometrie_urteil"],
                                            je_kamera=je))[0]
    assert ("decken sich Modell und Bild kaum (geom_iou 0.005, Schwelle 0.1) (763 von 67541 "
            "Punkten des Modells gemeinsam)") in satz
    assert "; und baut das Bild weit ueber den Umriss hinaus (2.09" in satz


# ====================================================================== N6 · umriss_gilt immer

def _lauf_mit(tmp_path, qa):
    from test_kettenlauf_26august import _auftragsordner, _kette, _lauf
    ordner = _auftragsordner(tmp_path / "a")
    _protokoll, attrappen = _kette(tmp_path)
    attrappen["_qa"] = lambda *a, **k: dict(qa)
    antwort = _lauf(tmp_path, ordner, attrappen)
    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort["grund"]
    kameras = [k for k in abholer.lies_befund(ordner)["kameras"] if not k.get("doppelt_von")]
    assert kameras
    return antwort, kameras


def test_umriss_gilt_steht_auch_wenn_wahr(tmp_path):
    antwort, kameras = _lauf_mit(tmp_path, {"score": 0.4, "bestanden": False, "geom_iou": 0.45,
                                            "n_gemeinsam": 300, "n_soll": 600, "n_ist": 650})
    assert not _saetze(antwort["ergebnis"])
    for k in kameras:
        assert k["seedauswahl"]["umriss_gilt"] is True
        assert "umriss_grund" not in k["seedauswahl"]


def test_im_lauf_faengt_die_flaeche_das_strassenbild(tmp_path):
    antwort, kameras = _lauf_mit(tmp_path, {
        "score": 0.0, "bestanden": False, "geom_iou": 0.197, "n_gemeinsam": 38473,
        "n_soll": N_SOLL, "n_ist": 165964, "ausserhalb_umriss": {"anteil_haus": 2.1481}})
    assert _saetze(antwort["ergebnis"])
    for k in kameras:
        assert k["seedauswahl"]["umriss_gilt"] is False
        assert "Verhaeltnis 2.46" in k["seedauswahl"]["umriss_grund"]


def test_ohne_messung_kein_umriss_gilt(tmp_path):
    _antwort, kameras = _lauf_mit(tmp_path, {"score": None, "bestanden": False, "geom_iou": 0.0,
                                             "n_gemeinsam": 0, "n_soll": 600, "n_ist": 0})
    for k in kameras:
        assert "umriss_gilt" not in k["seedauswahl"]


# ====================================================================== N3 · der Zusatz, Vorgabe aus

def _szene(prompt="a house", **vis):
    return {"geometry": {"path": "model.glb", "format": "glb"}, "cameras": "auto",
            "render": {"samples": 8}, "style": {"prompt": prompt}, "vis": vis}


def test_ohne_schalter_bleibt_der_prompt_wie_er_war():
    for vis in ({}, {"leerer_hintergrund": False}, {"leerer_hintergrund": None}):
        szene = kosmo_szene.lies_szene(_szene(**vis), streng=False)
        assert szene["prompt"] == "a house" and not szene["maengel"]
        assert not [z for z in szene["prompt_zusaetze"] if z["art"] == "leerer_hintergrund"]


def test_mit_schalter_kommt_der_zusatz_einmal():
    szene = kosmo_szene.lies_szene(_szene(leerer_hintergrund=True), streng=False)
    assert szene["prompt"] == "a house, empty background, no other buildings"
    assert not szene["maengel"]
    zusatz = [z for z in szene["prompt_zusaetze"] if z["art"] == "leerer_hintergrund"]
    assert zusatz == [{"art": "leerer_hintergrund", "satz": kosmo_szene.ZUSATZ_LEERER_HINTERGRUND,
                       "schon_im_prompt": False}]
    schon = kosmo_szene.lies_szene(
        _szene("a house, Empty background, no other buildings", leerer_hintergrund=True),
        streng=False)
    assert schon["prompt"] == "a house, Empty background, no other buildings"
    assert [z["schon_im_prompt"] for z in schon["prompt_zusaetze"]] == [True]


@pytest.mark.parametrize("vis, wort, endgueltig", [
    ({"leerer_hintergrund": "true"}, "erwartet war true", False),
    ({"leerer_hintergrund": True, "skip": True}, "zugleich", True),
])
def test_falscher_schalter_ist_ein_mangel(vis, wort, endgueltig):
    szene = kosmo_szene.lies_szene(_szene(**vis), streng=False)
    assert any(wort in m for m in szene["maengel"])
    assert any(wort in m for m in szene["maengel_endgueltig"]) is endgueltig


def test_der_zusatz_erreicht_das_bildmodell(tmp_path):
    from test_kettenlauf_26august import _auftragsordner, _kette, _lauf
    prompts = {}
    for an in (False, True):
        ordner = _auftragsordner(tmp_path / f"a{an}")
        pfad = ordner / bruecke.DATEI_SZENE
        szene = json.loads(pfad.read_text(encoding="utf-8"))
        if an:
            szene["vis"]["leerer_hintergrund"] = True
        pfad.write_text(json.dumps(szene), encoding="utf-8")
        protokoll, attrappen = _kette(tmp_path / f"k{an}")
        antwort = _lauf(tmp_path / f"l{an}", ordner, attrappen)
        assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort["grund"]
        prompts[an] = {a.prompt for a in protokoll["render"]}
    assert prompts[False] == {"overcast sky, no people"}
    assert prompts[True] == {"overcast sky, no people, empty background, no other buildings"}


# ====================================================================== der Messauftrag 297

def test_der_messauftrag_297_ist_gueltig_und_fragt_alle_punkte():
    pfad = WURZEL / "auftraege" / "offen" / "auf-20261021-297.json"
    daten = json.loads(pfad.read_text(encoding="utf-8"))
    assert auftrag.pruefe_auftrag(daten) == []
    assert daten["worker"] == "local" and daten["art"] == "qa" and daten["rang"] == 84
    assert daten["params"]["folgt_auf"] == "auf-20261021-296"
    text = daten["anweisung"]
    for stichwort in ("NICHT WIEDERZUERKENNEN", "umriss_gilt", "leerer_hintergrund",
                      "empty background, no other buildings", "faithful", "bildpunktgleich",
                      "ausserhalb_umriss_anteil", "WAS AM HEIM-PC JETZT ANDERS RECHNET"):
        assert stichwort in text, stichwort


def test_das_planblatt_licht_traegt_seine_waechterzeilen():
    text = (WURZEL / "docs" / "PLAN_LICHT_INS_KI_BILD_2026-10-21.md").read_text(encoding="utf-8")
    zeilen = text.splitlines()
    assert any(z.startswith("**Codestand:** `") for z in zeilen)
    assert any(z.startswith("**Grundlage:** ") for z in zeilen)
    assert "## Zu entscheiden" in text and "FLUX" in text
