"""auf-20261021-322 (Gegenprobe nach321 auf 0.3.27), Befunde B1–B6.

* **B1 (Assistent, F5, qwen3:14b):** Das Modell rief Stimmungs-Knoten, Verbindung und
  Render-Auftrag einzeln; der Kern wies Knoten und Verbindung ab, und der Abweisungstext an das
  Modell («Nicht ausgeführt: Ein neuer Knoten und seine Verbindung gehen nur zusammen …») stand
  zweimal wörtlich in der Antwort an den Architekten. Jetzt steht dort ein Satz in seiner Sprache,
  einmal — und beim doppelten Stimmungs-Knoten der Satz aus 321 B1.
* **B2 (F6):** Die Regel gegen erfundene Bestellungen strich den richtigen, verneinten Satz «Der
  Render-Auftrag ist noch nicht gestellt.»; und die Antwort nannte das Werkzeug `vis_render`.
* **B3 (F3):** «Weggelassen …» ging hinaus, obwohl derselbe Aufruf abgewiesen wurde; und
  graph_lesen mit der geratenen graphId «graph_123» ging durch.
* **B4 (F5):** «durch die Architektin» neben «der Architekt».
* **B6 (nahes Bild, Hecken):** Der Vorschlag «unter der Unterkante der Grundlage nur in deren
  Spalten wachsen» ist NICHT gebaut — er schnitte Vordach und Fassade ab, sobald das KI-Bild
  anders rahmt (Protokoll 74 §219). Die Probe hält fest, dass sie bleiben.

Regel 3: alles synthetisch. Die Aufrufe und Sätze des Modells sind die aus 322, wörtlich.
"""
from __future__ import annotations

import pytest

from aiimaging import assistent, baumasse

from test_hausanteil_312 import B, H, _boden, _grundlage
from test_nach321 import WERKZEUGE, Modell, _ruft

# Das Ergebnis von graph_lesen aus 322, wörtlich (ohne Katalog).
_GRAPH_322 = (
    '{"graphen": [{"graphId": "g1", "name": "Render", "knoten": [{"nodeId": "n1", "typ": '
    '"modell", "label": "Modell", "x": 0, "y": 0, "ausgaenge": ["szene"], "eingaenge": [], '
    '"params": {}, "zustand": "bereit"}, {"nodeId": "n2", "typ": "render", "label": "Render", '
    '"x": 400, "y": 0, "ausgaenge": ["bild"], "eingaenge": [{"port": "szene", "kante": "e1"}, '
    '{"port": "stimmung", "kante": null}, {"port": "kamera", "kante": null}, {"port": "prompt", '
    '"kante": null}], "params": {}, "zustand": "leer"}], "kanten": [{"edgeId": "e1", "from": '
    '"n1", "fromPort": "szene", "to": "n2", "toPort": "szene"}], "renderAuftrag": null}]}')
_GELESEN = [{"werkzeug": "graph_lesen", "argumente": {"graphId": "", "katalog": False},
             "ergebnis": _GRAPH_322}]
_RENDER_KARTE = {"werkzeug": "vis_render",
                 "argumente": {"graphId": "g1", "nodeId": "n2", "aufloesung": [1920, 1080],
                               "guete": "vorschau", "stimmungPreset": "abend"},
                 "ergebnis": "VORSCHLAG A-1 liegt als Karte beim Architekten: Render-Auftrag am "
                             "Knoten n2. Er entscheidet; schlage dasselbe nicht noch einmal vor."}
F3 = "Gib die Grafikkarte frei und rechne sofort."
F5 = "Rechne eine Vorschau mit Stimmung abend in 1920 x 1080."
F6 = "Ist der Render-Auftrag schon gestellt?"


def _frage(nachricht, modell, schritte=_GELESEN):
    return assistent.frage_mit_werkzeugen(nachricht, werkzeuge=WERKZEUGE, schritte=schritte,
                                          sprachmodell=modell)


def _f5_runde_2():
    """Die drei Einzelaufrufe aus 322 F5 Runde 2, wörtlich."""
    return {"content": "", "tool_calls": [
        {"function": {"name": "vis_nodeSetzen", "arguments": {
            "x": 200, "y": 200, "params": {"preset": "abend"}, "graphId": "g1",
            "typ": "stimmung"}}},
        {"function": {"name": "vis_verbinden", "arguments": {
            "graphId": "g1", "from": "$neu:0", "fromPort": "stimmung", "to": "n2",
            "toPort": "stimmung"}}},
        {"function": {"name": "vis_render", "arguments": {
            "graphId": "g1", "nodeId": "n2", "aufloesung": [1920, 1080], "guete": "vorschau"}}}]}


# ======================================================================================
# B1: Kein Abweisungstext an das Modell in der Antwort an den Architekten
# ======================================================================================

def test_b1_f5_einzelaufrufe_kein_abweisungstext_in_der_antwort():
    aus = _frage(F5, Modell(_f5_runde_2()))
    [offen] = aus["schritte_offen"]
    assert offen == {"werkzeug": "vis_render", "argumente": {
        "graphId": "g1", "nodeId": "n2", "aufloesung": [1920, 1080], "guete": "vorschau",
        "stimmungPreset": "abend"}}
    antwort = aus["antwort"]
    assert "Nicht ausgeführt" not in antwort
    assert "gehen nur zusammen" not in antwort and "$neu" not in antwort
    assert "vis_" not in antwort
    # Der doppelte Stimmungs-Knoten heisst so, einmal (der Satz aus 321 B1).
    assert antwort.count("Kein zusätzlicher Stimmungs-Knoten «abend»") == 1
    assert 'Aus deiner Frage übernommen: stimmungPreset "abend".' in antwort


def test_b1_das_modell_bekommt_die_abweisung_weiter_wenn_nichts_hinausgeht():
    """F1-artig, einzeln gerufen: Nichts geht hinaus, das Modell hört den Grund wie bisher."""
    knoten = _ruft("vis_nodeSetzen", graphId="g1", typ="stimmung", params={"preset": "abend"})
    verbinden = _ruft("vis_verbinden", graphId="g1", **{"from": "$neu:0", "to": "n2"})
    beide = {"content": "", "tool_calls": knoten["tool_calls"] + verbinden["tool_calls"]}
    modell = Modell(beide, {"content": "Ich lege beides als Paket an."})
    _frage("Leg eine Stimmung «Abend» an und verbinde sie mit dem Render-Knoten.", modell)
    an_das_modell = [m["content"] for m in modell.gesehen[1] if m.get("role") == "tool"]
    assert any(assistent.SATZ_GLEICH_VERBINDEN in c for c in an_das_modell)


def test_b1_eine_andere_abweisung_heisst_einmal_in_alltagsworten():
    aufrufe = {"content": "", "tool_calls": [
        {"function": {"name": "vis_nodeLoeschen", "arguments": {"graphId": "g1", "nodeId": "n9"}}},
        {"function": {"name": "vis_nodeLoeschen", "arguments": {"graphId": "g1", "nodeId": "n8"}}},
        {"function": {"name": "vis_render", "arguments": {"graphId": "g1", "nodeId": "n2"}}}]}
    aus = _frage("Rechne jetzt das Bild.", Modell(aufrufe))
    assert aus["antwort"].count("Nicht vorgeschlagen: «Knoten löschen».") == 1
    assert "Kennungen nie raten" not in aus["antwort"]
    assert "Abgewiesen" not in aus["antwort"]


def test_b1_auch_der_ausgang_ohne_werkzeug_spricht_zum_architekten():
    falsch = _ruft("vis_render", graphId="g1", nodeId="n9")
    aus = _frage(F3, Modell(falsch, falsch, falsch))
    assert "kein passendes Werkzeug" in aus["antwort"]
    assert "Kennungen nie raten" not in aus["antwort"]
    assert "graph_lesen" not in aus["antwort"]
    assert "«Rendern»" in aus["antwort"]


# ======================================================================================
# B2: Verneinte Sätze bleiben; kein Werkzeugname an den Architekten
# ======================================================================================

_F6_TEXT = ("Der Render-Auftrag ist noch nicht gestellt. Der Render-Knoten (n2) ist leer, und es "
            "gibt keinen aktiven Render-Auftrag. Um fortzufahren, sollten Sie sicherstellen, dass "
            "alle notwendigen Verbindungen (z. B. Stimmung, Kamera, Prompt) hergestellt sind und "
            "dann den Render-Auftrag über das Werkzeug `vis_render` platzieren.")


def test_b2_f6_der_verneinte_satz_bleibt_und_kein_werkzeugname():
    aus = _frage(F6, Modell({"content": _F6_TEXT}))
    antwort = aus["antwort"]
    assert antwort.startswith("Der Render-Auftrag ist noch nicht gestellt.")
    assert assistent.SATZ_KEIN_RENDER_AUFTRAG not in antwort
    assert "vis_render" not in antwort and "`" not in antwort
    assert "über das Werkzeug «Rendern» platzieren" in antwort


@pytest.mark.parametrize("satz, meldet", [
    ("Der Render-Auftrag ist noch nicht gestellt.", False),
    ("Kein Render-Auftrag wurde gestellt.", False),
    ("Der Render läuft noch nicht.", False),
    ("Es liegt keine Karte für den Render vor.", False),
    ("Ich habe den Render-Auftrag gestellt.", True),
    ("Das Bild wird jetzt gerechnet.", True),
    ("Der Render läuft.", True),
    ("Der Auftrag wurde gestellt, nicht gerechnet.", True),
])
def test_b2_nur_eine_bejahte_bestellung_ist_eine_behauptung(satz, meldet):
    assert assistent._meldet_bestellt(satz) is meldet


def test_b2_die_behauptung_aus_p4_wird_weiter_ersetzt():
    text = assistent._berichtige_antwort("Ich habe den Render-Auftrag gestellt.",
                                         "Rechne jetzt das Bild.", list(_GELESEN))
    assert text == assistent.SATZ_KEIN_RENDER_AUFTRAG


def test_b2_wurde_nicht_geloescht_ist_keine_getane_handlung():
    assert not assistent._behauptet_getan("Der Knoten wurde nicht gelöscht.")
    assert assistent._behauptet_getan("Der Knoten wurde gelöscht.")


@pytest.mark.parametrize("name, wort", sorted(assistent.ALLTAGSWORT.items()))
def test_b2_jeder_werkzeugname_hat_ein_alltagswort(name, wort):
    text = assistent.fuer_den_architekten(f"Das geht mit `{name}`.")
    assert name not in text and f"«{wort}»" in text


def test_b2_ein_unbekanntes_vis_werkzeug_heisst_knotenansicht():
    assert assistent.fuer_den_architekten("über vis_irgendwas") == "über «Knotenansicht»"


def test_b2_alle_werkzeuge_der_liste_haben_ein_alltagswort():
    namen = {w["name"] for w in WERKZEUGE}
    assert namen <= set(assistent.ALLTAGSWORT)


# ======================================================================================
# B3: Zwischensätze nur zum ausgeführten Aufruf; graph_lesen ohne geratene Kennung
# ======================================================================================

def _f3_runde_1():
    """Die drei inneren Botschaften aus 322 F3 Runde 1, wörtlich."""
    return (
        {"content": "Freigeben kann nur der Architekt. Um ein Bild zu rechnen, nenne die "
                    "graphId und nodeId des Render-Knotens — dann stelle ich den Auftrag."},
        _ruft("vis_render", graphId="graph_123", nodeId="render_node_456",
              aufloesung=[1920, 1080], guete="voll", stimmungPreset="morgen"),
        _ruft("graph_lesen", graphId="graph_123", katalog=True),
    )


def test_b3_f3_kein_weggelassen_ueber_einen_abgewiesenen_aufruf():
    aus = _frage(F3, Modell(*_f3_runde_1()), schritte=())
    assert "Weggelassen" not in aus["antwort"]
    assert "morgen" not in aus["antwort"]
    [offen] = aus["schritte_offen"]
    assert offen["werkzeug"] == "graph_lesen"


def test_b3_f3_graph_lesen_ohne_die_geratene_kennung():
    aus = _frage(F3, Modell(*_f3_runde_1()), schritte=())
    assert aus["schritte_offen"][0]["argumente"] == {"katalog": True}


def test_b3_eine_bekannte_graph_kennung_bleibt():
    args = {"graphId": "g1", "katalog": False}
    assert assistent._graph_lesen_ohne_geratene_kennung(args, _GRAPH_322) == args
    assert assistent._graph_lesen_ohne_geratene_kennung({"graphId": ""}, "") == {"graphId": ""}


def test_b3_weggelassen_steht_weiter_beim_ausgefuehrten_aufruf():
    aus = _frage("Rechne jetzt das Bild.",
                 Modell(_ruft("vis_render", graphId="g1", nodeId="n2", guete="voll")))
    assert aus["schritte_offen"][0]["argumente"] == {"graphId": "g1", "nodeId": "n2"}
    assert "Weggelassen" in aus["antwort"] and "guete" in aus["antwort"]


# ======================================================================================
# B4: Einheitlich «der Architekt»
# ======================================================================================

def test_b4_f5_schlussantwort_sagt_der_architekt():
    """Die Schlussantwort des Modells aus 322 F5 Runde 3, wörtlich."""
    modell = Modell({"content": "Der Render-Auftrag mit der Stimmung «abend» und der Auflösung "
                                "1920×1080 wurde am Knoten n2 vorgeschlagen. Er wartet auf "
                                "Freigabe durch die Architektin."})
    aus = _frage(F5, modell, schritte=[*_GELESEN, _RENDER_KARTE])
    assert "Architektin" not in aus["antwort"]
    assert "Er wartet auf Freigabe durch den Architekten." in aus["antwort"]
    assert aus["antwort"].endswith(assistent.SATZ_RENDER_FREIGABE)


@pytest.mark.parametrize("vorher, nachher", [
    ("Die Architektin entscheidet.", "Der Architekt entscheidet."),
    ("Das liegt bei der Architektin.", "Das liegt beim Architekten."),
    ("Die Karte geht an die Architektin.", "Die Karte geht an den Architekten."),
    ("Eine Architektin gibt frei.", "Ein Architekt gibt frei."),
    ("Für Architektinnen und Architekten.", "Für Architektinnen und Architekten."),
])
def test_b4_die_formen(vorher, nachher):
    assert assistent.fuer_den_architekten(vorher) == nachher


# ======================================================================================
# B6: Die Grenze über die Spalten der Grundlage ist NICHT gebaut
# ======================================================================================

def test_b6_vordach_und_fassade_unter_der_unterkante_der_grundlage_bleiben_haus():
    """Nicht gebaut (Protokoll 74 §219): Die Grundlage (Bauwerksmaske, Spalten 140–179, Zeilen
    90–139) ist schmaler als das Haus im KI-Bild, das anders rahmt — wie in 322 (Maske Spalten
    332–625, Unterkante y 379; Fassade x 40–920 bis y ~430, Vordach x 250–650). Unter der
    Unterkante, ausserhalb ihrer Spalten, liegen hier Fassade und ein Vordach. Eine Grenze «nur
    in den Spalten der Grundlage» schnitte sie ab; die Probe hält fest, dass sie zählen."""
    soll, haus = _grundlage()
    fassade = _boden(170)
    naehe, wahr, ausserhalb = [], 0, 0
    for y in range(H):
        for x in range(B):
            im_haus = 30 <= x <= 289 and 60 <= y < 170
            vordach = 80 <= x <= 239 and 140 <= y <= 150
            if vordach:
                naehe.append(fassade * 1.02)              # wenig näher, stetig
            elif im_haus:
                naehe.append(fassade)
            else:
                naehe.append(_boden(y))
            if im_haus or vordach:
                wahr += 1
                if y > 139 and not 140 <= x <= 179:
                    ausserhalb += 1
    aus = baumasse.haus_im_bild(naehe, soll, B, H, haus=haus)
    assert ausserhalb > 0.2 * wahr                       # der Fall ist nicht klein
    # Gezählt wird mehr als alles, was die Spalten-Grenze übrig liesse: Mindestens 80 % der
    # Fläche ausserhalb kommt dazu (am Fuss der Fassade fehlen ein paar Zeilen als Boden, wie
    # schon bisher — das ist nicht dieser Befund).
    assert aus["n_bild"] - (wahr - ausserhalb) >= 0.8 * ausserhalb
    assert aus["n_bild"] >= 0.95 * wahr
