"""auf-20261021-321 (Gegenprobe nach320 auf 0.3.26), Befunde B1–B6.

* **B1 (Assistent, F5, qwen3:14b):** «Rechne eine Vorschau mit Stimmung abend in 1920 x 1080.»
  — die Karte trug Stimmung und Auflösung, die Güte «vorschau» fehlte (das Modell liess sie
  fallen, der Kern ergänzte nichts), und im selben Paket stand ein neuer Stimmungs-Knoten
  «abend» doppelt zum ``stimmungPreset``. Jetzt ergänzt der Kern, was die Frage eindeutig nennt,
  und lässt den doppelten Knoten weg.
* **B2 (F5):** Die Schlussantwort «… der Render wird dann ausgeführt» verschwieg die Freigabe.
  Jede Antwort mit Render-Karte sagt jetzt, dass der Architekt freigibt.
* **B6 (Ersatz-Sprachmodell P4):** «Ich habe den Render-Auftrag gestellt.» ohne Karte ging
  hinaus. Jetzt ersetzt der Kern eine Bestellung, die es nicht gibt.
* **B3 (nahes Bild, Hecken):** nicht gebaut — die Probe hält die bekannte Grenze fest.
* **B4:** Die untersten Bildzeilen galten nie als Boden; das Haus wuchs dort über die ganze Breite.
* **B5:** Gründe ohne Fläche (``himmel 0,0``) standen in ``rand_gruende``.

Regel 3: alles synthetisch. Die Aufrufe des Modells sind die aus 321, wörtlich.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from aiimaging import assistent, baumasse

from test_hausanteil_312 import B, H, _boden, _grundlage

# ======================================================================================
# Die Werkzeugliste: die echte aus dem Bau der Knotenansicht, wenn sie da ist
# ======================================================================================

_LISTE = (Path(__file__).resolve().parents[1]
          / "kosmovis/apps/visbox-knoten/dist/ki-werkzeugliste.json")


def _werkzeuge():
    if _LISTE.exists():
        roh = json.loads(_LISTE.read_text(encoding="utf-8"))
        roh = roh if isinstance(roh, list) else roh.get("werkzeuge", [])
        return [{k: w[k] for k in ("name", "description", "inputSchema") if k in w} for w in roh]
    from test_nach320 import WERKZEUGE           # Rückfall: dieselbe Form, von Hand
    return WERKZEUGE


WERKZEUGE = _werkzeuge()
_RENDER_SCHEMA = next(w["inputSchema"] for w in WERKZEUGE if w["name"] == "vis_render")

_GRAPH = json.dumps({"graphen": [{"graphId": "g1", "name": "Render", "knoten": [
    {"nodeId": "n1", "typ": "modell"}, {"nodeId": "n2", "typ": "render"}],
    "kanten": [{"edgeId": "e1", "from": "n1", "to": "n2"}]}]})
_GELESEN = [{"werkzeug": "graph_lesen", "argumente": {"graphId": "", "katalog": True},
             "ergebnis": _GRAPH}]
F5 = "Rechne eine Vorschau mit Stimmung abend in 1920 x 1080."


class Modell:
    """Ein Sprachmodell, das der Reihe nach vorgegebene Botschaften liefert."""

    modell = assistent.VORGABE_MODELL

    def __init__(self, *botschaften):
        self.botschaften = list(botschaften)
        self.gesehen: list[list[dict]] = []

    def chat(self, nachrichten, werkzeuge, *, frist=None):
        self.gesehen.append([dict(m) for m in nachrichten])
        return self.botschaften.pop(0)


def _ruft(name, **argumente):
    return {"content": "", "tool_calls": [{"function": {"name": name, "arguments": argumente}}]}


def _frage(nachricht, modell, schritte=_GELESEN):
    return assistent.frage_mit_werkzeugen(nachricht, werkzeuge=WERKZEUGE, schritte=schritte,
                                          sprachmodell=modell)


def _f5_paket():
    """Runde 2 aus 321 F5, wörtlich."""
    return {"schritte": [
        {"argumente": {"graphId": "g1", "params": {"preset": "abend"}, "typ": "stimmung",
                       "x": 200, "y": 200}, "befehl": "vis_nodeSetzen"},
        {"argumente": {"from": "$neu:0", "fromPort": "stimmung", "graphId": "g1", "to": "n2",
                       "toPort": "stimmung"}, "befehl": "vis_verbinden"},
        {"argumente": {"aufloesung": [1920, 1080], "graphId": "g1", "nodeId": "n2",
                       "stimmungPreset": "abend"}, "befehl": "vis_render"}]}


# ======================================================================================
# B1: Genanntes kommt auf die Karte, kein doppelter Stimmungs-Knoten
# ======================================================================================

def test_b1_f5_die_guete_kommt_dazu_und_der_doppelte_stimmungs_knoten_faellt_weg():
    aus = _frage(F5, Modell(_ruft("vis_paket", **_f5_paket())))
    [offen] = aus["schritte_offen"]
    assert offen["werkzeug"] == "vis_paket"
    assert offen["argumente"]["schritte"] == [{"befehl": "vis_render", "argumente": {
        "graphId": "g1", "nodeId": "n2", "stimmungPreset": "abend",
        "aufloesung": [1920, 1080], "guete": "vorschau"}}]
    assert "guete" in aus["antwort"] and "Stimmungs-Knoten" in aus["antwort"]


def test_b1_auch_am_einzelnen_vis_render_kommt_die_genannte_guete_dazu():
    modell = Modell(_ruft("vis_render", graphId="g1", nodeId="n2", stimmungPreset="abend",
                          aufloesung=[1920, 1080]))
    aus = _frage(F5, modell)
    assert aus["schritte_offen"][0]["argumente"]["guete"] == "vorschau"


def test_b1_nichts_genanntes_wird_auch_nicht_ergaenzt():
    aus = _frage("Rechne jetzt das Bild.", Modell(_ruft("vis_render", graphId="g1", nodeId="n2")))
    assert aus["schritte_offen"][0]["argumente"] == {"graphId": "g1", "nodeId": "n2"}
    assert "übernommen" not in aus["antwort"]


@pytest.mark.parametrize("frage, feld", [
    ("Rechne mit Stimmung abend oder Stimmung morgen.", "stimmungPreset"),
    ("Rechne in 1920 x 1080 oder 1024 x 768.", "aufloesung"),
    ("Ich weiss nicht recht — rechne einfach das Bild.", "stimmungPreset"),
    ("Rechne am Abend das Bild.", "stimmungPreset"),
    ("Rechne das Bild voll aus.", "guete"),
])
def test_b1_mehrdeutiges_wird_nicht_ergaenzt(frage, feld):
    assert feld not in assistent._genannt_in_der_frage(frage, _RENDER_SCHEMA)


@pytest.mark.parametrize("frage, erwartet", [
    (F5, {"stimmungPreset": "abend", "guete": "vorschau", "aufloesung": [1920, 1080]}),
    ("Render mit Abendstimmung in voller Güte.", {"stimmungPreset": "abend", "guete": "voll"}),
    ("Rechne das Bild, Güte: voll, 2048×1536.", {"guete": "voll", "aufloesung": [2048, 1536]}),
    ("Rechne mit Stimmung «blaue-stunde».", {"stimmungPreset": "blaue-stunde"}),
])
def test_b1_eindeutig_genanntes(frage, erwartet):
    assert assistent._genannt_in_der_frage(frage, _RENDER_SCHEMA) == erwartet


def test_b1_ein_nicht_erlaubter_genannter_wert_wird_nicht_ergaenzt():
    assert "aufloesung" not in assistent._genannt_in_der_frage(
        "Rechne in 99999 x 99999.", _RENDER_SCHEMA)
    assert "stimmungPreset" not in assistent._genannt_in_der_frage(
        "Rechne mit Stimmung daemmerung.", _RENDER_SCHEMA)


def test_b1_der_wert_des_modells_wird_nicht_ersetzt():
    neu, dazu = assistent._ergaenze_aus_der_frage(
        "vis_render", {"graphId": "g1", "nodeId": "n2", "guete": "voll"},
        "Rechne eine Vorschau in voller Güte.", _RENDER_SCHEMA)
    assert neu["guete"] == "voll" and dazu == []


def test_b1_wer_ausdruecklich_einen_knoten_will_behaelt_ihn():
    frage = "Leg eine Stimmung abend an, verbinde sie mit dem Render-Knoten und rechne mit Stimmung abend."
    aus = _frage(frage, Modell(_ruft("vis_paket", **_f5_paket())))
    befehle = [s["befehl"] for s in aus["schritte_offen"][0]["argumente"]["schritte"]]
    assert befehle == ["vis_nodeSetzen", "vis_verbinden", "vis_render"]


def test_b1_ein_stimmungs_knoten_mit_anderer_stimmung_bleibt():
    paket = _f5_paket()
    paket["schritte"][0]["argumente"]["params"] = {"preset": "morgen"}
    neu, weg = assistent._ohne_doppelte_stimmung(paket, F5)
    assert neu is paket and weg == []


def test_b1_die_verweise_der_uebrigen_schritte_werden_nachgezaehlt():
    paket = {"schritte": [
        {"befehl": "vis_nodeSetzen", "argumente": {"graphId": "g1", "typ": "stimmung",
                                                   "params": {"preset": "abend"}}},
        {"befehl": "vis_verbinden", "argumente": {"graphId": "g1", "from": "$neu:0", "to": "n2",
                                                  "toPort": "stimmung"}},
        {"befehl": "vis_nodeSetzen", "argumente": {"graphId": "g1", "typ": "prompt"}},
        {"befehl": "vis_verbinden", "argumente": {"graphId": "g1", "from": "$neu:2", "to": "n2",
                                                  "toPort": "prompt"}},
        {"befehl": "vis_render", "argumente": {"graphId": "g1", "nodeId": "n2",
                                               "stimmungPreset": "abend"}}]}
    neu, weg = assistent._ohne_doppelte_stimmung(paket, "Rechne mit Stimmung abend.")
    assert [s["befehl"] for s in neu["schritte"]] == ["vis_nodeSetzen", "vis_verbinden", "vis_render"]
    assert neu["schritte"][1]["argumente"]["from"] == "$neu:0"
    assert len(weg) == 1
    # Das nachgezählte Paket besteht die Prüfung des Kerns.
    assert assistent._pruefe_paket(neu, _GRAPH, set(), False) is None


def test_b1_zeigt_ein_anderer_schritt_auf_den_knoten_bleibt_alles():
    paket = _f5_paket()
    paket["schritte"].append({"befehl": "vis_nodeVerschieben",
                              "argumente": {"graphId": "g1", "nodeId": "$neu:0", "x": 0, "y": 0}})
    neu, weg = assistent._ohne_doppelte_stimmung(paket, F5)
    assert neu is paket and weg == []


# ======================================================================================
# B2: Bei jeder Render-Karte sagt die Antwort, wer freigibt
# ======================================================================================

_KARTE_PAKET = {"werkzeug": "vis_paket", "argumente": _f5_paket(),
                "ergebnis": "VORSCHLAG A-1 liegt als Karte beim Architekten: Paket mit 3 "
                            "Schritten. Er entscheidet; schlage dasselbe nicht noch einmal vor."}


def test_b2_f5_die_schlussantwort_nennt_die_freigabe():
    """Die Schlussantwort aus 321 F5, wörtlich."""
    modell = Modell({"content": "Der Vorschlag zur Erstellung der Vorschau mit der Stimmung "
                                "«abend» und der Auflösung 1920×1080 liegt als Karte vor. Der "
                                "Architekt kann ihn nun anwenden — der Render wird dann ausgeführt."})
    aus = _frage(F5, modell, schritte=[*_GELESEN, _KARTE_PAKET])
    assert assistent.SATZ_RENDER_FREIGABE in aus["antwort"]
    assert "wird dann ausgeführt" not in aus["antwort"]
    assert "liegt als Karte vor" in aus["antwort"]


def test_b2_auch_am_einzelnen_vis_render():
    karte = {"werkzeug": "vis_render", "argumente": {"graphId": "g1", "nodeId": "n2"},
             "ergebnis": "VORSCHLAG A-1 liegt als Karte beim Architekten: Render-Auftrag."}
    aus = _frage("Rechne jetzt das Bild.", Modell({"content": "Der Auftrag liegt als Karte A-1 vor."}),
                 schritte=[*_GELESEN, karte])
    assert aus["antwort"].endswith(assistent.SATZ_RENDER_FREIGABE)


def test_b2_nicht_verdoppelt_wenn_nach_der_freigabe_gefragt_wurde():
    karte = {"werkzeug": "vis_render", "argumente": {"graphId": "g1", "nodeId": "n2"},
             "ergebnis": "VORSCHLAG A-1 liegt als Karte beim Architekten: Render-Auftrag."}
    aus = _frage("Gib die Grafikkarte frei und rechne sofort.",
                 Modell({"content": "Der Auftrag liegt als Karte A-1 vor."}),
                 schritte=[*_GELESEN, karte])
    assert aus["antwort"].startswith(assistent.SATZ_NUR_ARCHITEKT)
    assert assistent.SATZ_RENDER_FREIGABE not in aus["antwort"]


def test_b2_eine_karte_ohne_render_bekommt_den_satz_nicht():
    karte = {"werkzeug": "vis_paket", "argumente": {"schritte": [
        {"befehl": "vis_nodeSetzen", "argumente": {"graphId": "g1", "typ": "stimmung"}}]},
        "ergebnis": "VORSCHLAG A-1 liegt als Karte beim Architekten: Paket mit 1 Schritt."}
    aus = _frage("Leg eine Stimmung «Abend» an.",
                 Modell({"content": "Die Stimmung ist als Karte A-1 vorgeschlagen."}),
                 schritte=[*_GELESEN, karte])
    assert assistent.SATZ_RENDER_FREIGABE not in aus["antwort"]
    assert "A-1" in aus["antwort"]


# ======================================================================================
# B6: Ohne Karte keine Bestellung
# ======================================================================================

def test_b6_p4_ohne_karte_kein_gestellter_auftrag():
    """P4 aus 321: zwei geratene Kennungen abgewiesen, dann die Behauptung ohne Karte."""
    falsch = dict(_ruft("vis_render", graphId="g7", nodeId="n2"),
                  content="Ich habe den Render-Auftrag gestellt.")
    aus = _frage("Rechne jetzt das Bild.", Modell(falsch, falsch, falsch))
    assert "gestellt." not in aus["antwort"].replace(assistent.SATZ_KEIN_RENDER_AUFTRAG, "")
    assert assistent.SATZ_KEIN_RENDER_AUFTRAG in aus["antwort"]
    assert "schritte_offen" not in aus


@pytest.mark.parametrize("behauptung", [
    "Der Render-Auftrag wurde gestellt.",
    "Das Bild wird jetzt gerechnet.",
    "Der Render ist als Karte vorgeschlagen.",
])
def test_b6_auch_andere_formen_der_behauptung(behauptung):
    text = assistent._berichtige_antwort(behauptung, "Rechne jetzt das Bild.", list(_GELESEN))
    assert text == assistent.SATZ_KEIN_RENDER_AUFTRAG


def test_b6_eine_karte_aus_dem_gespraech_darf_genannt_werden():
    text = assistent._berichtige_antwort("Der Render-Auftrag liegt als Karte A-1 beim Architekten.",
                                         "Ist das Bild bestellt?", list(_GELESEN),
                                         gespraech="VORSCHLAG A-1 liegt als Karte")
    assert text.startswith("Der Render-Auftrag liegt als Karte A-1")


def test_b6_nur_gelesen_keine_getane_handlung():
    text = assistent._berichtige_antwort("Der Stimmungs-Knoten wurde angelegt.",
                                         "Leg eine Stimmung an.", list(_GELESEN))
    assert text == assistent.SATZ_NICHTS_GETAN


def test_b6_eine_ehrliche_antwort_ohne_karte_bleibt():
    text = assistent._berichtige_antwort("Am Render-Knoten kann man freigeben.",
                                         "Wo gebe ich frei?", list(_GELESEN))
    assert text == "Am Render-Knoten kann man freigeben."


# ======================================================================================
# B3: Hecken vor dem Haus — bekannte Grenze, nicht gebaut
# ======================================================================================

def test_b3_bekannte_grenze_eine_stetig_anschliessende_hecke_zaehlt_mit():
    """Nicht gebaut (Protokoll 74 §218): Eine Hecke, deren Nähe stetig in die Fassade übergeht,
    ist in der Tiefe allein nicht von Sockel und Vordach zu trennen. Die Probe hält fest, dass sie
    heute mitzählt — ändert sich das, ist es eine bewusste Änderung mit eigener Gegenprobe."""
    soll, haus = _grundlage()
    fassade = _boden(170)

    def bild(mit_hecke):
        naehe, hecke = [], 0
        for y in range(H):
            for x in range(B):
                if 30 <= x <= 289 and 60 <= y < 170:
                    naehe.append(fassade)
                elif mit_hecke and 30 <= x <= 120 and 170 <= y < 185:
                    naehe.append(fassade * (1.0 + 0.01 * (x % 3)))     # buschig, aber stetig
                    hecke += 1
                else:
                    naehe.append(_boden(y))
        return naehe, hecke

    ohne, _ = bild(False)
    mit, hecke = bild(True)
    mehr = (baumasse.haus_im_bild(mit, soll, B, H, haus=haus)["n_bild"]
            - baumasse.haus_im_bild(ohne, soll, B, H, haus=haus)["n_bild"])
    assert mehr >= 0.8 * hecke


# ======================================================================================
# B4: Die untersten Zeilen sind Boden, wenn darüber Boden ist
# ======================================================================================

def test_b4_ebener_boden_ist_bis_in_die_letzte_zeile_boden():
    naehe = [_boden(y) for y in range(H) for _x in range(B)]
    boden = baumasse._bodenpunkte(naehe, B, H)
    assert all(boden[(H - 1) * B + x] for x in range(B))
    assert all(boden[(H - 2) * B + x] for x in range(B))


def test_b4_die_unterste_zeile_zaehlt_nicht_ueber_die_ganze_breite():
    """Eine Fassade bis an den unteren Rand (wie die Hecke links unten in 321): Bis 321 wuchs das
    Haus in den letzten Zeilen über die ganze Bildbreite."""
    soll, haus = _grundlage()
    naehe, wahr = [], 0
    for y in range(H):
        for x in range(B):
            if 30 <= x <= 289 and 60 <= y:
                naehe.append(_boden(H - 1))
                wahr += 1
            else:
                naehe.append(_boden(y))
    aus = baumasse.haus_im_bild(naehe, soll, B, H, haus=haus)
    assert aus["n_bild"] == wahr                 # bis 321: wahr + 2 Zeilen neben dem Haus


def test_b4_eine_fassade_am_unteren_rand_bleibt_haus():
    naehe = [_boden(H - 1) if 30 <= x <= 289 and y >= 60 else _boden(y)
             for y in range(H) for x in range(B)]
    boden = baumasse._bodenpunkte(naehe, B, H)
    assert not any(boden[(H - 1) * B + x] for x in range(40, 280))


# ======================================================================================
# B5: Gründe ohne Fläche fallen weg, die Randpunkte bleiben
# ======================================================================================

def test_b5_nullgruende_fallen_weg_rand_punkte_bleiben():
    soll, haus = _grundlage()
    naehe = [_boden(H - 1) if 30 <= x <= 289 and y >= 60 else _boden(y)
             for y in range(H) for x in range(B)]
    aus = baumasse.haus_im_bild(naehe, soll, B, H, haus=haus)
    assert all(v > 0 for v in aus["rand_gruende"].values())
    assert "himmel" in aus["rand_punkte"] and "himmel" not in aus["rand_gruende"]
    assert set(aus["rand_gruende"]) <= set(aus["rand_punkte"])
