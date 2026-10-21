"""Stufe 5 des Plans «KI-Bedienung» (``docs/PLAN_KI_BEDIENUNG_2026-10-20.md``, 21.10.2026):
der Assistent bedient die Knotenansicht mit **derselben Werkzeugliste wie Claude**.

Die Liste schickt die Mac-App; die Schleife steht in :func:`aiimaging.assistent.frage_mit_werkzeugen`
— je Anfrage eine Runde des Modells, gültige Aufrufe gehen als ``schritte_offen`` an die App, ihre
Ergebnisse kommen als ``schritte`` zurück. **Kein Netz**: das Sprachmodell ist ein Ersatz.

Drei Grenzen sind als Proben festgehalten: der Server führt nie einen Schritt aus (er kennt keinen
Weg dorthin), ein Werkzeug, das freigibt, gibt es für den Assistenten nicht, und nach
:data:`SCHRITTE_HOECHSTENS` bekommt das Modell keine Werkzeuge mehr angeboten.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from aiimaging import assistent

WURZEL = Path(__file__).resolve().parents[1]
LISTE = WURZEL / "kosmovis" / "apps" / "visbox-knoten" / "dist" / "ki-werkzeugliste.json"


class Ersatz:
    def __init__(self, botschaften=(), modell="qwen3:14b"):
        self.modell = modell
        self.botschaften = list(botschaften)
        self.gesehen: list[list[dict]] = []
        self.angeboten: list[list] = []

    def chat(self, nachrichten, werkzeuge):
        self.gesehen.append(json.loads(json.dumps(nachrichten)))
        self.angeboten.append(werkzeuge)
        return self.botschaften.pop(0)


def _liste() -> list[dict]:
    """Die Liste aus dem Bau — dieselbe, die die Mac-App Claude nennt (ohne die zwei Mac-Werkzeuge)."""
    return [{k: w[k] for k in ("name", "description", "inputSchema")}
            for w in json.loads(LISTE.read_text(encoding="utf-8"))["werkzeuge"]]


def _aufruf(name, **argumente):
    return {"function": {"name": name, "arguments": argumente}}


#: Ein gelesener Graph: Kennungen g, n, n1, n2, kein n3 (Befund 305 B6).
_GRAPH = {"werkzeug": "graph_lesen", "argumente": {},
          "ergebnis": '{"graphen": [{"id": "g", "nodes": [{"id": "n"}]}, {"id": "g1", "nodes": '
                      '[{"id": "n1", "typ": "modell"}, {"id": "n2", "typ": "render"}]}]}'}


def test_die_liste_der_knotenansicht_geht_unveraendert_ans_modell():
    e = Ersatz([{"content": "", "tool_calls": [_aufruf("graph_lesen")]}])
    r = assistent.frage("Leg eine Abendstimmung an.", werkzeuge=_liste(), sprachmodell=e)
    assert r["schritte_offen"] == [{"werkzeug": "graph_lesen", "argumente": {}}]
    namen = [w["function"]["name"] for w in e.angeboten[0]]
    assert namen == [w["name"] for w in _liste()]
    assert {"vis_render", "vis_nodeLoeschen", "visbox_blick", "visbox_maus"} <= set(namen)
    # Der Systemtext ist der der Knotenansicht, nicht der der drei Vorschlagswerkzeuge.
    assert e.gesehen[0][0] == {"role": "system", "content": assistent.SYSTEMTEXT_KNOTEN}


def test_mit_den_ergebnissen_geht_es_weiter_bis_zur_antwort():
    e = Ersatz([{"content": "Erledigt: Stimmung «Abend» liegt als Karte A-2 bei dir."}])
    schritte = [{"werkzeug": "graph_lesen", "argumente": {}, "ergebnis": '{"graphen": []}'},
                {"werkzeug": "vis_nodeSetzen", "argumente": {"typ": "stimmung"},
                 "ergebnis": "VORSCHLAG A-2 liegt als Karte beim Architekten: Stimmung anlegen."}]
    r = assistent.frage("Leg eine Abendstimmung an.", werkzeuge=_liste(), schritte=schritte,
                        sprachmodell=e)
    assert r == {"antwort": "Erledigt: Stimmung «Abend» liegt als Karte A-2 bei dir."}
    gesehen = e.gesehen[0]
    # system, user, dann je Schritt Aufruf und Ergebnis — in Reihenfolge.
    assert [m["role"] for m in gesehen] == ["system", "user", "assistant", "tool", "assistant", "tool"]
    assert gesehen[4]["tool_calls"][0]["function"] == {"name": "vis_nodeSetzen",
                                                       "arguments": {"typ": "stimmung"}}
    assert gesehen[5]["content"].startswith("VORSCHLAG A-2")


def test_ein_unbekanntes_werkzeug_geht_nicht_an_die_app_das_modell_korrigiert():
    e = Ersatz([{"content": "", "tool_calls": [_aufruf("vis_freigeben", nodeId="n1")]},
                {"content": "", "tool_calls": [_aufruf("vis_render", graphId="g", nodeId="n")]}])
    r = assistent.frage("Rechne das Bild.", werkzeuge=_liste(), sprachmodell=e, schritte=[_GRAPH])
    assert r["schritte_offen"] == [{"werkzeug": "vis_render", "argumente": {"graphId": "g", "nodeId": "n"}}]
    assert e.gesehen[1][-1] == {"role": "tool", "tool_name": "vis_freigeben",
                                "content": "Abgewiesen: Ein Werkzeug «vis_freigeben» gibt es nicht."}


@pytest.mark.parametrize("name", ["render_freigeben", "vis_approve", "gpu_starten", "train_freigabe_knopf"])
def test_ein_werkzeug_das_freigibt_gibt_es_fuer_den_assistenten_nicht(name):
    liste = _liste() + [{"name": name, "description": "", "inputSchema": {"type": "object"}}]
    with pytest.raises(assistent.AssistentError, match="freigeben kann nur ein Mensch"):
        assistent.frage("x", werkzeuge=liste, sprachmodell=Ersatz())


def test_nach_den_hoechstens_schritten_keine_werkzeuge_mehr():
    e = Ersatz([{"content": "Ich habe zwölf Schritte gemacht; die Karten liegen bei dir.",
                 "tool_calls": [_aufruf("graph_lesen")]}])
    schritte = [{"werkzeug": "graph_lesen", "argumente": {}, "ergebnis": "{}"}] * assistent.SCHRITTE_HOECHSTENS
    r = assistent.frage("Mach weiter.", werkzeuge=_liste(), schritte=schritte, sprachmodell=e)
    assert e.angeboten == [[]]
    assert "schritte_offen" not in r
    assert e.gesehen[0][-1]["content"] == assistent.SATZ_SCHRITTE_ERSCHOEPFT


def test_ein_langes_ergebnis_wird_gekuerzt_und_der_gedankentext_nie_gezeigt():
    e = Ersatz([{"content": "<think>GEDANKE</think>Fertig.", "thinking": "GEDANKE"}])
    lang = "x" * (assistent.ERGEBNIS_HOECHSTENS + 500)
    r = assistent.frage("Lies.", werkzeuge=_liste(), sprachmodell=e,
                        schritte=[{"werkzeug": "graph_lesen", "argumente": {}, "ergebnis": lang}])
    assert r == {"antwort": "Fertig."}
    assert len(e.gesehen[0][-1]["content"]) == assistent.ERGEBNIS_HOECHSTENS


@pytest.mark.parametrize("schritte, satz", [
    ([{"werkzeug": "gibt_es_nicht", "argumente": {}, "ergebnis": "x"}], "aus der Liste"),
    ([{"werkzeug": "graph_lesen", "argumente": [], "ergebnis": "x"}], "aus der Liste"),
    ("kein liste", "eine Liste"),
])
def test_falsche_schritte_sind_ein_satz(schritte, satz):
    with pytest.raises(assistent.AssistentError, match=satz):
        assistent.frage("x", werkzeuge=_liste(), schritte=schritte, sprachmodell=Ersatz())


@pytest.mark.parametrize("liste, satz", [
    ([], "nicht leere Liste"),
    ([{"name": "a b", "inputSchema": {"type": "object"}}], "Werkzeugname"),
    ([{"name": "a", "inputSchema": {"type": "array"}}], "Objekt-Schema"),
    ([{"name": "a", "inputSchema": {"type": "object"}}] * 2, "zweimal"),
])
def test_eine_falsche_liste_ist_ein_satz(liste, satz):
    with pytest.raises(assistent.AssistentError, match=satz):
        assistent.pruefe_werkzeugliste(liste)


def test_waehrend_ein_bild_rechnet_auch_mit_werkzeugen_nicht():
    with pytest.raises(assistent.AssistentError, match="rechnet"):
        assistent.frage("x", werkzeuge=_liste(), sprachmodell=Ersatz(), bild_rechnet=True)


def test_ohne_liste_bleibt_alles_wie_bisher():
    e = Ersatz([{"content": "Dazu nichts."}])
    r = assistent.frage("Hallo", sprachmodell=e)
    assert r == {"antwort": "Dazu nichts."}
    assert [w["function"]["name"] for w in e.angeboten[0]] == [
        "standpunkt_vorschlagen", "bildauftrag_vorschlagen", "varianten_vorschlagen"]


def test_mutation_frage_mit_werkzeugen_kennt_keinen_weg_zum_ausfuehren():
    """Rot, sobald die Schleife am Heim-PC selbst etwas ausführt oder rechnet."""
    import inspect
    quelle = inspect.getsource(assistent.frage_mit_werkzeugen)
    for verboten in ("arbeitsgang", "kette.", "starte", "anwenden(", "urlopen", "_oeffne"):
        assert verboten not in quelle, verboten


# ============================================================================ am Server

FLAECHE = WURZEL / "oberflaeche"


@pytest.fixture(scope="module")
def server():
    sys.path.insert(0, str(FLAECHE))
    try:
        import server as modul
        return modul
    finally:
        sys.path.remove(str(FLAECHE))


def test_der_server_reicht_liste_und_schritte_durch_und_rechnet_nicht(server, tmp_path, monkeypatch):
    from tests.test_assistent_server import _frage
    gestartet = []
    monkeypatch.setattr(server, "_rechne_im_hintergrund", lambda *a, **k: gestartet.append(a))
    e = Ersatz([{"content": "Ich lese zuerst den Graph.", "tool_calls": [_aufruf("graph_lesen")]}],
               modell="qwen3:30b")
    code, antwort = _frage(server, befehl="POST", weg=server.WEG_ASSISTENT, sprachmodell=e,
                           ordner=tmp_path, rumpf={"nachricht": "Leg eine Stimmung an.",
                                                   "werkzeuge": _liste()})
    assert code == 200, antwort
    assert antwort == {"antwort": "Ich lese zuerst den Graph.",
                       "schritte_offen": [{"werkzeug": "graph_lesen", "argumente": {}}]}
    assert gestartet == []


# ================================================================ dieselben Namen überall

def test_blick_und_maus_heissen_in_seite_und_app_gleich():
    """Die Seite nennt die zwei Werkzeuge (`ki-wirt.ts`), die App bildet sie aus der Marke
    (`Kibedienen`) — beide müssen dasselbe sagen, sonst ruft die App ein Werkzeug, das die Liste
    nicht kennt."""
    import re
    wirt = (WURZEL / "kosmovis/apps/visbox-knoten/src/ki-wirt.ts").read_text(encoding="utf-8")
    kern = (WURZEL / "ipad/Visbox.swiftpm/Kern/Kibedienung.swift").read_text(encoding="utf-8")
    name = re.search(r'static let name = "([^"]+)"',
                     (WURZEL / "ipad/Visbox.swiftpm/Kern/Marke.swift").read_text(encoding="utf-8")).group(1)
    blick = re.search(r"BLICK_NAME = '([^']+)'", wirt).group(1)
    maus = re.search(r"MAUS_NAME = '([^']+)'", wirt).group(1)
    assert 'blickName = Mcp.servername + "_blick"' in kern
    assert 'mausName = Mcp.servername + "_maus"' in kern
    assert blick.endswith("_blick") and maus.endswith("_maus")
    assert blick.split("_")[0] == maus.split("_")[0]
    assert blick == name.lower() + "_blick" and maus == name.lower() + "_maus"
    liste = [w["name"] for w in json.loads(LISTE.read_text(encoding="utf-8"))["werkzeuge"]]
    assert blick in liste and maus in liste


def test_der_assistent_geht_denselben_weg_wie_claude():
    """Die Mac-App führt die Schritte des Assistenten über dieselbe Zentrale aus wie Claudes
    Aufrufe — nur der Urheber ist «assistent»; und sie zählt keine Schritte selbst."""
    zentrale = (WURZEL / "ipad/VisboxMac/Sources/VisboxMac/Claude/Kizentrale.swift").read_text(encoding="utf-8")
    leiste = (WURZEL / "ipad/VisboxMac/Sources/VisboxMac/Assistent/Assistentenleiste.swift").read_text(encoding="utf-8")
    assert "urheber: .assistent" in zentrale
    assert "func rufeFuerAssistent" in zentrale
    assert "zentrale.rufeFuerAssistent" in leiste
    assert "gespraech.naechsterSchritt()" in leiste and "gespraech.schrittErledigt" in leiste
    assert "SCHRITTE_HOECHSTENS" not in leiste and "12" not in leiste.split("func schicke")[1].split("func anwenden")[0]


# ===================================================== geschärft nach dem Messauftrag 305 (B3–B6)

def test_der_systemsatz_nennt_die_vier_lehren_aus_305():
    s = assistent.SYSTEMTEXT_KNOTEN
    assert "rätst du nie" in s and "graph_lesen" in s and "nächsten Runde" in s       # B6
    assert "Erfinde nichts" in s and "keine Stimmung" in s                            # B4
    assert "«vorgeschlagen»" in s and "nie «gelöscht»" in s                           # B5
    assert "Freigeben kann nur der Architekt" in s                                    # B3
    assert "ß" not in s.replace("Schweizer Schreibung (ss statt ß)", "")


def test_eine_geratene_kennung_geht_nicht_an_die_app_f1():
    """F1: vis_nodeSetzen und vis_verbinden mit «n3» in derselben Runde — n3 gibt es noch nicht."""
    e = Ersatz([{"content": "", "tool_calls": [
        _aufruf("vis_nodeSetzen", graphId="g1", typ="stimmung", x=200, y=100, params={"preset": "abend"}),
        _aufruf("vis_verbinden", graphId="g1", **{"from": "n3"}, fromPort="stimmung", to="n2", toPort="stimmung")]}])
    r = assistent.frage("Leg eine Stimmung «Abend» an und verbinde sie mit dem Render-Knoten.",
                        werkzeuge=_liste(), schritte=[_GRAPH], sprachmodell=e)
    assert [s["werkzeug"] for s in r["schritte_offen"]] == ["vis_nodeSetzen"]
    assert "«n3» (from)" in r["antwort"] and "nie raten" in r["antwort"]


def test_ohne_gelesenen_graph_wird_jede_kennung_abgewiesen_und_das_modell_liest():
    e = Ersatz([{"content": "", "tool_calls": [_aufruf("vis_nodeLoeschen", graphId="g1", nodeId="n1")]},
                {"content": "", "tool_calls": [_aufruf("graph_lesen")]}])
    r = assistent.frage("Lösch den Modell-Knoten.", werkzeuge=_liste(), sprachmodell=e)
    assert r["schritte_offen"] == [{"werkzeug": "graph_lesen", "argumente": {}}]
    assert e.gesehen[1][-1]["content"].startswith("Abgewiesen: Die Kennung «g1» (graphId)")


def test_eine_kennung_aus_dem_ergebnis_von_nodesetzen_gilt():
    neu = {"werkzeug": "vis_nodeSetzen", "argumente": {"typ": "stimmung"},
           "ergebnis": "OK: Knoten n3 (stimmung) gesetzt."}
    e = Ersatz([{"content": "", "tool_calls": [
        _aufruf("vis_verbinden", graphId="g1", **{"from": "n3"}, fromPort="stimmung", to="n2", toPort="stimmung")]}])
    r = assistent.frage("Verbinde sie.", werkzeuge=_liste(), schritte=[_GRAPH, neu], sprachmodell=e)
    assert r["schritte_offen"][0]["werkzeug"] == "vis_verbinden"


def test_eine_kennung_aus_der_frage_gilt_und_n1_ist_nicht_n10():
    assert assistent._pruefe_angaben("vis_nodeLoeschen", {"nodeId": "n1"}, "Lösch n1.") is None
    assert assistent._pruefe_angaben("vis_nodeLoeschen", {"nodeId": "n1"}, "Lösch n10.") is not None


def test_eine_erfundene_stimmung_am_render_wird_abgewiesen_f2():
    e = Ersatz([{"content": "", "tool_calls": [
        _aufruf("vis_render", graphId="g1", nodeId="n2", stimmungPreset="morgen", aufloesung=[1024, 768])]},
                {"content": "", "tool_calls": [_aufruf("vis_render", graphId="g1", nodeId="n2")]}])
    r = assistent.frage("Rechne jetzt das Bild.", werkzeuge=_liste(), schritte=[_GRAPH], sprachmodell=e)
    assert r["schritte_offen"] == [{"werkzeug": "vis_render", "argumente": {"graphId": "g1", "nodeId": "n2"}}]
    grund = e.gesehen[1][-1]["content"]
    assert "stimmungPreset" in grund and "Nichts erfinden" in grund


def test_eine_genannte_stimmung_gilt():
    assert assistent._pruefe_angaben("vis_render", {"graphId": "g1", "nodeId": "n2", "stimmungPreset": "abend"},
                                     "Rechne g1 n2 mit Abend.") is None


def test_wer_nach_der_freigabe_fragt_hoert_nur_der_architekt_f3():
    # Seit auf-20261021-310 (B2): «rechne» bekommt einmal den Anstoss zu vis_render; ruft das
    # Modell auch danach kein Werkzeug, bleibt es bei der Antwort.
    e = Ersatz([{"content": "FEHLER: Um die Grafikkarte zu freigeben, fehlen Angaben."},
                {"content": "FEHLER: Um die Grafikkarte zu freigeben, fehlen Angaben."}])
    r = assistent.frage("Gib die Grafikkarte frei und rechne sofort.", werkzeuge=_liste(), sprachmodell=e)
    assert e.gesehen[1][-1]["content"] == assistent.SATZ_BILD_ANSTOSS
    assert r["antwort"].startswith(assistent.SATZ_NUR_ARCHITEKT)
    assert "FEHLER" not in r["antwort"]


def test_nur_eine_karte_heisst_nicht_geloescht_f4():
    karte = {"werkzeug": "vis_nodeLoeschen", "argumente": {"graphId": "g1", "nodeId": "n1"},
             "ergebnis": "VORSCHLAG A-2 liegt als Karte beim Architekten: Knoten «Modell» löschen. Er entscheidet; "
                         "schlage dasselbe nicht noch einmal vor."}
    e = Ersatz([{"content": "Der Modell-Knoten wurde gelöscht. Der Architekt entscheidet."}])
    r = assistent.frage("Lösch den Modell-Knoten.", werkzeuge=_liste(), schritte=[_GRAPH, karte], sprachmodell=e)
    assert "gelöscht" not in r["antwort"]
    assert r["antwort"].startswith("Noch nicht ausgeführt: vorgeschlagen als Karte A-2")
    assert r["antwort"].endswith("Der Architekt entscheidet.")


def test_gegenbeleg_direkt_geschehen_bleibt_und_eine_karte_kommt_dazu():
    direkt = {"werkzeug": "vis_nodeSetzen", "argumente": {}, "ergebnis": "OK: Knoten n3 gesetzt."}
    karte = {"werkzeug": "vis_nodeLoeschen", "argumente": {},
             "ergebnis": "VORSCHLAG A-3 liegt als Karte beim Architekten: löschen."}
    text = assistent._berichtige_antwort("Die Stimmung ist angelegt.", "Mach.", [_GRAPH, direkt, karte])
    assert text.startswith("Die Stimmung ist angelegt.") and "Karte A-3" in text
    assert assistent._berichtige_antwort("Die Stimmung ist angelegt.", "Mach.", [_GRAPH, direkt]) == \
        "Die Stimmung ist angelegt."
