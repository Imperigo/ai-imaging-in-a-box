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
    r = assistent.frage("Rechne das Bild.", werkzeuge=_liste(), sprachmodell=e)
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
