"""auf-20261021-320 (Gegenprobe nach317 auf 0.3.25), Befunde B1–B6 und das Glossar.

* **B1–B3 (Assistent, qwen3:14b):** F2 «Rechne jetzt das Bild.» und F3 «Gib die Grafikkarte
  frei und rechne sofort.» endeten ohne Render-Karte. Das Modell rief ``vis_render`` mit
  erfundenen Angaben (backbone, guete, stimmungPreset, aufloesung) — die Beschreibung des
  Werkzeugs zählt sie samt erlaubten Werten auf, ein 14-B-Modell füllt sie aus. Der Kern wies
  je Runde EINE ab (die erste in der Feldreihenfolge), das Modell strich je Runde eine; nach
  drei inneren Runden kam «Dazu fand ich kein passendes Werkzeug — …». Jetzt lässt der Kern
  erfundene und ungültige freie Angaben weg und stellt den Auftrag mit den gültigen (B1);
  ``aufloesung`` wird gegen das Schema geprüft (B2); und jeder Ausgang einer Frage nach der
  Freigabe trägt «Freigeben kann nur der Architekt» (B3).
* **B4 (nahes Bild):** Die Trennhilfe des Messbodens der GRUNDLAGE schnitt im näher
  gerahmten KI-Bild Sockel, Vordach und Eingang ab (0,308 gegen 0,456 von Hand).
* **B5:** ``rand_gruende`` zählte Randpunkte statt verlorener Fläche.
* **B6:** Ein Lauf «nur Grundlage» trug keinen ``maskenbefund``.

Regel 3: alles synthetisch.
"""
from __future__ import annotations

import json

import pytest

from aiimaging import assistent, baumasse, sprache

from test_hausanteil_312 import B, H, _boden, _grundlage, _ki_bild

# ======================================================================================
# B1–B3: der Assistent stellt den Render-Auftrag ohne erfundene Angaben
# ======================================================================================

_GRAPH = json.dumps({"graphen": [{"graphId": "g1", "name": "Render", "knoten": [
    {"nodeId": "n1", "typ": "modell"}, {"nodeId": "n2", "typ": "render"}],
    "kanten": [{"edgeId": "e1", "from": "n1", "to": "n2"}]}]})

_RENDER_SCHEMA = {"type": "object", "properties": {
    "graphId": {"type": "string"}, "nodeId": {"type": "string"},
    "kameraWahl": {"default": "auto", "type": "string", "enum": ["auto", "saved"]},
    "stimmungPreset": {"type": "string", "enum": ["morgen", "mittag", "abend", "blaue-stunde"]},
    "backbone": {"type": "string", "enum": ["z-image-turbo", "qwen", "flux2-klein"]},
    "grundlage": {"type": "string"},
    "seed": {"type": "integer", "minimum": 0, "maximum": 2147483647},
    "guete": {"type": "string", "enum": ["vorschau", "voll"]},
    "aufloesung": {"type": "array", "minItems": 2, "maxItems": 2,
                   "items": {"type": "integer", "exclusiveMinimum": 0}}},
    "required": ["graphId", "nodeId"]}

WERKZEUGE = [
    {"name": "graph_lesen", "description": "Liest den Graph.",
     "inputSchema": {"type": "object", "properties": {"graphId": {"type": "string"}}}},
    {"name": "vis_render", "description": "Stellt einen Render-AUFTRAG.",
     "inputSchema": _RENDER_SCHEMA},
    {"name": "vis_paket", "description": "Mehrere Schritte.",
     "inputSchema": {"type": "object", "properties": {"schritte": {"type": "array"}}}},
]
_GELESEN = [{"werkzeug": "graph_lesen", "argumente": {"graphId": ""}, "ergebnis": _GRAPH}]


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


def test_b1_f2_erfundene_angaben_fallen_weg_und_die_karte_entsteht_in_einer_runde():
    """Genau der Aufruf aus 320 F2: eine Runde, eine Render-Karte, nur graphId und nodeId."""
    modell = Modell(_ruft("vis_render", graphId="g1", nodeId="n2", aufloesung=[1024, 768],
                          backbone="qwen", guete="voll"))
    aus = _frage("Rechne jetzt das Bild.", modell)
    assert aus["schritte_offen"] == [{"werkzeug": "vis_render",
                                      "argumente": {"graphId": "g1", "nodeId": "n2"}}]
    assert len(modell.gesehen) == 1, "keine Runde für Abweisungen verbraucht"
    assert "Dazu fand ich kein passendes Werkzeug" not in aus["antwort"]
    for feld in ("backbone", "guete", "aufloesung"):
        assert feld in aus["antwort"], "der Mensch sieht, was weggelassen wurde"


def test_b1_f3_auch_stimmung_und_kamerawahl_fallen_weg():
    modell = Modell(_ruft("vis_render", kameraWahl="auto", stimmungPreset="morgen",
                          graphId="g1", nodeId="n2", aufloesung=[1920, 1080],
                          backbone="z-image-turbo", guete="voll"))
    aus = _frage("Gib die Grafikkarte frei und rechne sofort.", modell)
    assert aus["schritte_offen"][0]["argumente"] == {"graphId": "g1", "nodeId": "n2"}


def test_b1_genannte_angaben_bleiben():
    modell = Modell(_ruft("vis_render", graphId="g1", nodeId="n2", stimmungPreset="abend",
                          guete="vorschau", aufloesung=[1920, 1080]))
    aus = _frage("Rechne eine Vorschau mit Stimmung abend in 1920 x 1080.", modell)
    assert aus["schritte_offen"][0]["argumente"] == {
        "graphId": "g1", "nodeId": "n2", "stimmungPreset": "abend", "guete": "vorschau",
        "aufloesung": [1920, 1080]}
    assert "Weggelassen" not in aus["antwort"]


def test_b1_eine_geratene_kennung_wird_weiter_abgewiesen():
    """Weglassen gilt nur für freie Angaben — eine Kennung bleibt ein Grund zum Abweisen."""
    modell = Modell(_ruft("vis_render", graphId="g1", nodeId="n7", backbone="qwen"),
                    _ruft("vis_render", graphId="g1", nodeId="n2", backbone="qwen"))
    aus = _frage("Rechne jetzt das Bild.", modell)
    assert aus["schritte_offen"][0]["argumente"] == {"graphId": "g1", "nodeId": "n2"}
    abweisung = [m for m in modell.gesehen[1] if m.get("role") == "tool"][-1]["content"]
    assert "n7" in abweisung


def test_b1_auch_im_paket_fallen_erfundene_angaben_am_render_schritt_weg():
    modell = Modell(_ruft("vis_paket", schritte=[
        {"befehl": "vis_render", "argumente": {"graphId": "g1", "nodeId": "n2",
                                               "backbone": "qwen", "guete": "voll"}}]))
    aus = _frage("Rechne jetzt das Bild.", modell)
    schritt = aus["schritte_offen"][0]["argumente"]["schritte"][0]
    assert schritt["argumente"] == {"graphId": "g1", "nodeId": "n2"}


def test_b1_die_beschreibung_von_vis_render_sagt_lass_weg():
    liste = assistent.pruefe_werkzeugliste(WERKZEUGE)
    text = next(w["function"]["description"] for w in liste
                if w["function"]["name"] == "vis_render")
    assert text.startswith("Stellt einen Render-AUFTRAG.")
    assert "weg" in text and "graphId und nodeId" in text


@pytest.mark.parametrize("wert, gilt", [
    ([1920, 1080], True), ([1024, 768], True), ([1920], False), ([1920, 1080, 3], False),
    ([0, 1080], False), ([-5, 1080], False), (["1920", 1080], False), ([True, 1080], False),
    ([1920.5, 1080], False), ([1 << 17, 1080], False), ("1920x1080", False),
])
def test_b2_aufloesung_wird_gegen_die_erlaubten_werte_geprueft(wert, gilt):
    assert (assistent._passt_zum_schema(wert, _RENDER_SCHEMA["properties"]["aufloesung"],
                                        feld="aufloesung") is None) is gilt


def test_b2_eine_genannte_aber_ungueltige_aufloesung_faellt_weg():
    modell = Modell(_ruft("vis_render", graphId="g1", nodeId="n2", aufloesung=[0, 1080]))
    aus = _frage("Rechne das Bild in 0 x 1080.", modell)
    assert aus["schritte_offen"][0]["argumente"] == {"graphId": "g1", "nodeId": "n2"}
    assert "aufloesung" in aus["antwort"]


def test_b2_ein_ungueltiger_backbone_faellt_weg_auch_wenn_er_genannt_wurde():
    modell = Modell(_ruft("vis_render", graphId="g1", nodeId="n2", backbone="flux-dev"))
    aus = _frage("Rechne das Bild mit flux-dev.", modell)
    assert aus["schritte_offen"][0]["argumente"] == {"graphId": "g1", "nodeId": "n2"}


def test_b3_freigabesatz_auch_wenn_die_antwort_den_render_knoten_nennt():
    """Bis 320 fehlte der Satz, sobald die Antwort «Render-Knoten» enthielt."""
    karte = {"werkzeug": "vis_render", "argumente": {"graphId": "g1", "nodeId": "n2"},
             "ergebnis": "VORSCHLAG A-1 liegt als Karte beim Architekten: Render-Auftrag. "
                         "Er entscheidet."}
    modell = Modell({"content": "Der Render-Auftrag liegt als Karte A-1 am Render-Knoten."})
    aus = _frage("Gib die Grafikkarte frei und rechne sofort.", modell,
                 schritte=[*_GELESEN, karte])
    assert aus["antwort"].startswith(assistent.SATZ_NUR_ARCHITEKT)
    assert aus["antwort"].count("Freigeben kann nur der Architekt") == 1


def test_b3_freigabesatz_auch_wenn_kein_werkzeug_passte():
    """Der Ausgang «kein passendes Werkzeug» trug den Satz nicht (320 F3)."""
    falsch = _ruft("vis_render", graphId="g1", nodeId="n9")
    modell = Modell(falsch, falsch, falsch)
    aus = _frage("Gib die Grafikkarte frei und rechne sofort.", modell)
    assert aus["antwort"].startswith(assistent.SATZ_NUR_ARCHITEKT)
    assert "kein passendes Werkzeug" in aus["antwort"]


def test_b3_der_kurze_satz_des_modells_wird_nicht_verdoppelt():
    modell = Modell({"content": "Freigeben kann nur der Architekt. Ich kann nichts freigeben."})
    aus = _frage("Gib die GPU frei.", modell)
    assert aus["antwort"].count("Freigeben kann nur der Architekt") == 1


# ======================================================================================
# B4 und B5: die Trennhilfe im näher gerahmten KI-Bild, verlorene Fläche je Grund
# ======================================================================================

def _trennhilfe(soll):
    """Wie der Messboden der Grundlage: Hintergrund unter dem Fuss (Zeile 140) der Grundlage."""
    return [y >= 141 and not soll[y * B + x] for y in range(H) for x in range(B)]


def _naeher_gerahmt():
    """Wie K-normal in 320: Das KI-Bild rahmt näher — Fassade Zeilen 60–169, Fuss 170, also
    30 Zeilen unter dem Fuss der Grundlage; darunter ebener Boden."""
    naehe, wahr = [], 0
    for y in range(H):
        for x in range(B):
            if 30 <= x <= 289 and 60 <= y < 170:
                naehe.append(_boden(170))
                wahr += 1
            else:
                naehe.append(_boden(y))
    return naehe, wahr


def test_b4_die_trennhilfe_schneidet_das_naeher_gerahmte_haus_nicht_mehr_ab():
    soll, haus = _grundlage()
    naehe, wahr = _naeher_gerahmt()
    aus = baumasse.haus_im_bild(naehe, soll, B, H, haus=haus, trennhilfe=_trennhilfe(soll))
    assert aus["n_bild"] == pytest.approx(wahr, rel=0.05)
    th = aus["trennhilfe"]
    assert th["angewandt"] is False and "rahmt anders" in th["grund"]
    # Mit der Trennhilfe wäre es abgeschnitten gewesen — wie 0,308 gegen 0,456 in 320.
    assert th["anteil_mit"] < 0.8 * wahr / (B * H)
    assert "trennhilfe" not in aus["rand_gruende"]


def test_b4_bei_gleichem_ausschnitt_bleibt_die_trennhilfe():
    soll, haus = _grundlage()
    naehe, wahr = _ki_bild(breit=False)
    aus = baumasse.haus_im_bild(naehe, soll, B, H, haus=haus, trennhilfe=_trennhilfe(soll))
    assert aus["trennhilfe"]["angewandt"] is True
    assert aus["n_bild"] == pytest.approx(wahr, rel=0.10)


def test_b4_das_breite_haus_mit_hecke_behaelt_die_trennhilfe():
    """Anders gerahmt, aber unter der Kante liegt Hecke und Boden, kein Haus: Sie bleibt."""
    soll, haus = _grundlage()
    naehe, wahr = _ki_bild(breit=True)
    aus = baumasse.haus_im_bild(naehe, soll, B, H, haus=haus, trennhilfe=_trennhilfe(soll))
    assert aus["trennhilfe"]["angewandt"] is True
    assert aus["n_bild"] == pytest.approx(wahr, rel=0.10)


def test_b4_ohne_trennhilfe_kein_vermerk():
    soll, haus = _grundlage()
    naehe, _ = _ki_bild(breit=False)
    assert "trennhilfe" not in baumasse.haus_im_bild(naehe, soll, B, H, haus=haus)


def test_b5_rand_gruende_nach_flaeche_die_gerade_schnittlinie_fuehrt():
    """Wie 320: Die Trennhilfe schneidet mit einer geraden Linie (wenige Randpunkte) mehr
    Fläche ab als der gezackte Rand. Hier rahmt das KI-Bild NICHT anders (die Maske der
    Grundlage ist fast so gross), die Trennhilfe bleibt — und führt nach Fläche."""
    naehe, wahr = _naeher_gerahmt()
    haus = [30 <= x <= 289 and 60 <= y <= 140 for y in range(H) for x in range(B)]
    trennhilfe = [y >= 141 for y in range(H) for x in range(B)]
    aus = baumasse.haus_im_bild(naehe, haus, B, H, haus=haus, trennhilfe=trennhilfe)
    assert aus["trennhilfe"]["angewandt"] is True
    flaeche, punkte = aus["rand_gruende"], aus["rand_punkte"]
    assert aus["rand_einheit"] == "anteil_am_bild_hinter_der_grenze"
    assert set(flaeche) == set(punkte)
    assert all(isinstance(v, float) and 0.0 <= v <= 1.0 for v in flaeche.values())
    assert list(flaeche.values()) == sorted(flaeche.values(), reverse=True), "Fläche führt"
    assert next(iter(flaeche)) == "trennhilfe"
    # Die Fläche hinter der Linie ist der abgeschnittene Sockel (Zeilen 141–169).
    assert flaeche["trennhilfe"] == pytest.approx((wahr - aus["n_bild"]) / (B * H), rel=0.10)
    # Nach Punkten wöge der lange Rand ebenso viel — darum führt die Fläche.
    assert punkte["trennhilfe"] < 2 * B


# ======================================================================================
# Glossar
# ======================================================================================

def test_sichtbackstein_wird_uebersetzt():
    aus = sprache.glossar_uebersetzung("Wohnhaus aus Sichtbackstein")
    assert aus["unbekannt"] == ()
    assert "brick" in aus["text"] and "sichtbackstein" not in aus["text"].lower()


# ======================================================================================
# B6: ein Lauf «nur Grundlage» trägt den Maskenbefund
# ======================================================================================

def test_b6_nur_grundlage_legt_den_maskenbefund_ab(tmp_path, monkeypatch):
    from aiimaging import abholer
    from test_grundlage_varianten import _grundlage_rechnen, _mit_schoenbild
    from test_kettenlauf_26august import _kette

    gebaut = []

    def maske_bauen(bericht, **kw):
        gebaut.append(kw)
        return {"maske": None, "gemessen": True, "gelaende_quelle": "name+rolle",
                "grund": "synthetisch"}

    abgelegt = []
    monkeypatch.setattr(abholer, "_maske_bauen", maske_bauen)
    monkeypatch.setattr(abholer, "_urteil_ablegen", lambda ordner, urteil: abgelegt.append(urteil))
    protokoll, attrappen = _kette(tmp_path)
    _grundlage_rechnen(tmp_path, protokoll, _mit_schoenbild(attrappen))
    assert protokoll["render"] == [], "kein Bildmodell"
    grundlage = [u for u in abgelegt if u.get("nur_grundlage")]
    assert grundlage and len(gebaut) == len(grundlage), "je Kamera eine Maske, auch ohne Stimmung"
    for urteil in grundlage:
        assert urteil["maskenbefund"]["gelaende_quelle"] == "name+rolle"


def test_b2_die_kantengrenze_des_assistenten_ist_die_des_kerns():
    from aiimaging import kosmo_szene
    assert assistent.KANTE_HOECHSTENS == kosmo_szene.KANTE_HOECHSTENS
