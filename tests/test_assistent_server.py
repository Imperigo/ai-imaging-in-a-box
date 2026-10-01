"""Die Wege des Assistenten am Server (Plan v0.1.7, Strom D2): ``POST /api/assistent``,
``POST /api/assistent/anwenden`` und ``GET /api/heim`` — und die zwei neuen Schalter.

Die Anfragen laufen durch ``do_GET``/``do_POST`` und damit durch die Tür, wie in
``tests/test_ipad_geruest.py``. Das Sprachmodell ist ein Ersatz ohne Netz; der Lauf im
Hintergrund wird an ``_rechne_im_hintergrund`` abgefangen — es wird nichts gerechnet,
aber festgehalten, **ob** und **womit** gestartet worden wäre.
"""
from __future__ import annotations

import base64
import io
import json
import sys
from pathlib import Path

import pytest

from aiimaging import assistent, heimstand

FLAECHE = Path(__file__).resolve().parents[1] / "oberflaeche"


@pytest.fixture(scope="module")
def server():
    sys.path.insert(0, str(FLAECHE))
    try:
        import server as modul
        return modul
    finally:
        sys.path.remove(str(FLAECHE))


class Ersatz:
    def __init__(self, botschaften=(), *, aus=False):
        self.modell = "qwen3:30b"
        self.botschaften = list(botschaften)
        self.aus = aus
        self.protokoll: list[str] = []

    def chat(self, nachrichten, werkzeuge):
        self.protokoll.append("chat")
        return self.botschaften.pop(0)

    def vorhandene(self):
        if self.aus:
            raise assistent.NichtErreichbar("aus")
        return ["qwen3:30b"]

    def geladene(self):
        return []

    def entlade(self):
        self.protokoll.append("entlade")
        return {"entladen": True, "satz": "entladen"}


def _blatt14():
    return [{"content": "", "thinking": "GEDANKE", "tool_calls": [
        {"function": {"name": "standpunkt_vorschlagen",
                      "arguments": {"kamera": "sSE", "augenhoehe": 1.6}}},
        {"function": {"name": "bildauftrag_vorschlagen",
                      "arguments": {"prompt": "evening light, street view, residential "
                                              "building"}}},
        {"function": {"name": "varianten_vorschlagen",
                      "arguments": {"anzahl": 3, "startwert": 0}}}]},
        {"content": "Vorschlag: von Süd-Ost, Abendlicht, drei Varianten."}]


def _frage(modul, *, befehl, weg, rumpf=None, sprachmodell=None, ordner=None,
           angemeldet=True):
    roh = json.dumps(rumpf if rumpf is not None else {}).encode()
    klasse = type("FlaechePruefling", (modul.Flaeche,),
                  {"kennwort": "geheim", "ordner": ordner, "kopplung_offen": None,
                   "sprachmodell": sprachmodell})
    selbst = klasse.__new__(klasse)
    selbst.command, selbst.path = befehl, weg
    kopf = ("Basic " + base64.b64encode(f"{modul.BENUTZER}:geheim".encode()).decode()
            if angemeldet else None)
    selbst.headers = {"Authorization": kopf, "Content-Length": str(len(roh))}
    selbst.rfile, selbst.wfile = io.BytesIO(roh), io.BytesIO()
    codes = []
    selbst.send_response = lambda code, *a, **k: codes.append(code)
    selbst.send_header = lambda *a: None
    selbst.end_headers = lambda: None
    (selbst.do_GET if befehl == "GET" else selbst.do_POST)()
    return codes[0], json.loads(selbst.wfile.getvalue() or b"null")


@pytest.fixture
def lauf(server, monkeypatch):
    """Fängt den Lauf im Hintergrund ab und räumt den Laufstand danach auf."""
    gestartet = []

    def statt_zu_rechnen(ordner, trotz_aenderung, einstellungen, **kw):
        gestartet.append({"ordner": ordner, "einstellungen": einstellungen, **kw})
    monkeypatch.setattr(server, "_rechne_im_hintergrund", statt_zu_rechnen)
    yield gestartet
    server.LAUFSTAND.beende()


# ========================================================================== POST /api/assistent

def test_der_assistent_antwortet_mit_vorschlag_und_rechnet_nicht(server, lauf, tmp_path):
    """**Mutationsprobe am Server:** rot, sobald ``/api/assistent`` einen Lauf startet."""
    e = Ersatz(_blatt14())
    code, antwort = _frage(server, befehl="POST", weg=server.WEG_ASSISTENT, sprachmodell=e,
                           ordner=tmp_path, rumpf={"nachricht": "Zeig das Haus …"})
    assert code == 200, antwort
    assert set(antwort) == {"antwort", "vorschlag"}
    assert antwort["vorschlag"]["varianten"] == 3
    assert "GEDANKE" not in json.dumps(antwort, ensure_ascii=False)
    assert lauf == [] and server.LAUFSTAND.sicht()["laeuft"] is False
    assert "entlade" not in e.protokoll


def test_ohne_nachricht_ist_es_ein_satz(server):
    code, antwort = _frage(server, befehl="POST", weg=server.WEG_ASSISTENT,
                           sprachmodell=Ersatz())
    assert code == 400 and "Nachricht" in antwort["fehler"]


def test_waehrend_ein_bild_rechnet_schweigt_der_assistent(server, lauf):
    server.LAUFSTAND.beginne("x")
    e = Ersatz([{"content": "nie"}])
    code, antwort = _frage(server, befehl="POST", weg=server.WEG_ASSISTENT, sprachmodell=e,
                           rumpf={"nachricht": "Hallo"})
    assert code == 400 and "Grafikkarte" in antwort["fehler"]
    assert e.protokoll == []


def test_ollama_aus_ist_503_mit_satz(server, monkeypatch):
    class Aus(Ersatz):
        def chat(self, *_a):
            raise assistent.NichtErreichbar("Ollama antwortet nicht.")
    code, antwort = _frage(server, befehl="POST", weg=server.WEG_ASSISTENT,
                           sprachmodell=Aus(), rumpf={"nachricht": "Hallo"})
    assert code == 503 and antwort == {"fehler": "Ollama antwortet nicht."}


def test_ohne_anmeldung_kein_assistent(server):
    e = Ersatz([{"content": "nie"}])
    code, _ = _frage(server, befehl="POST", weg=server.WEG_ASSISTENT, sprachmodell=e,
                     rumpf={"nachricht": "Hallo"}, angemeldet=False)
    assert code == 401 and e.protokoll == []


# ================================================================ POST /api/assistent/anwenden

def _vorschlag(server, tmp_path):
    _, antwort = _frage(server, befehl="POST", weg=server.WEG_ASSISTENT,
                        sprachmodell=Ersatz(_blatt14()), rumpf={"nachricht": "x"})
    return antwort["vorschlag"]


def test_anwenden_entlaedt_und_startet_wie_rechne(server, lauf, tmp_path):
    v = _vorschlag(server, tmp_path)
    e = Ersatz()
    reihenfolge = e.protokoll
    echt = server._rechne_im_hintergrund

    def merkt(*a, **kw):
        reihenfolge.append("lauf")
        echt(*a, **kw)
    server._rechne_im_hintergrund = merkt
    try:
        code, antwort = _frage(server, befehl="POST", weg=server.WEG_ASSISTENT_ANWENDEN,
                               sprachmodell=e, ordner=tmp_path, rumpf={"vorschlag": v})
        for faden in __import__("threading").enumerate():
            if faden.name != "MainThread" and faden.daemon:
                faden.join(timeout=2)
    finally:
        server._rechne_im_hintergrund = echt
    assert code == 200, antwort
    # DIESELBE ANTWORT WIE POST /api/rechne
    assert set(antwort) == {"gestartet", "schritte_gesamt", "entwurf", "varianten"}
    assert antwort["gestartet"] is True and antwort["varianten"] == 3
    assert reihenfolge == ["entlade", "lauf"], "erst entladen, dann rechnen"
    assert lauf[0]["varianten"] == 3
    assert lauf[0]["einstellungen"]["kamera"] == "sSE"
    assert lauf[0]["einstellungen"]["auge"] is None


def test_anwenden_hat_die_fehler_von_rechne(server, lauf, tmp_path):
    v = _vorschlag(server, tmp_path)
    server.LAUFSTAND.beginne(tmp_path)
    code, antwort = _frage(server, befehl="POST", weg=server.WEG_ASSISTENT_ANWENDEN,
                           sprachmodell=Ersatz(), ordner=tmp_path, rumpf={"vorschlag": v})
    assert code == 400 and antwort["fehler"].startswith("Es läuft schon einer.")
    server.LAUFSTAND.beende()
    code, antwort = _frage(server, befehl="POST", weg=server.WEG_ASSISTENT_ANWENDEN,
                           sprachmodell=Ersatz(), rumpf={"vorschlag": v})
    assert code == 400 and antwort["fehler"] == "Kein Projektordner angegeben."
    assert lauf == []


def test_der_ordner_der_anfrage_gilt(server, lauf, tmp_path):
    v = _vorschlag(server, tmp_path)
    code, _ = _frage(server, befehl="POST", weg=server.WEG_ASSISTENT_ANWENDEN,
                     sprachmodell=Ersatz(), rumpf={"vorschlag": v, "ordner": str(tmp_path)})
    assert code == 200 and Path(lauf[0]["ordner"]) == tmp_path


def test_ein_gefaelschter_vorschlag_entlaedt_nicht_und_startet_nicht(server, lauf, tmp_path):
    e = Ersatz()
    code, antwort = _frage(server, befehl="POST", weg=server.WEG_ASSISTENT_ANWENDEN,
                           sprachmodell=e, ordner=tmp_path,
                           rumpf={"vorschlag": {"einstellungen": {"qa": False},
                                                "varianten": 3}})
    assert code == 400 and "qa" in antwort["fehler"]
    assert e.protokoll == [] and lauf == []


# ================================================================================ GET /api/heim

def test_heim_hat_den_festen_vertrag(server, monkeypatch):
    monkeypatch.setattr(heimstand, "grafikkarte",
                        lambda: {"frei_gb": None, "satz": "nicht gemessen"})
    code, h = _frage(server, befehl="GET", weg=server.WEG_HEIM,
                     sprachmodell=Ersatz(aus=True))
    assert code == 200
    assert set(h) == {"blender", "grafikkarte", "assistent", "satz"}
    assert set(h["blender"]) == {"da", "satz"}
    assert set(h["grafikkarte"]) == {"frei_gb", "satz"}
    assert h["assistent"] == {"stand": "aus", "modell": "qwen3:30b",
                              "satz": h["assistent"]["satz"]}


def test_heim_sagt_laedt_waehrend_ein_bild_rechnet(server, lauf, monkeypatch):
    monkeypatch.setattr(heimstand, "grafikkarte", lambda: {"frei_gb": 3.0, "satz": "x"})
    server.LAUFSTAND.beginne("x")
    _, h = _frage(server, befehl="GET", weg=server.WEG_HEIM, sprachmodell=Ersatz())
    assert h["assistent"]["stand"] == "laedt"


def test_heim_nimmt_ohne_schalter_die_adresse_aus_der_umgebung(server, monkeypatch):
    """Ohne ``--assistent-adresse`` liest der Kern ``AIIMAGING_OLLAMA`` — je Anfrage."""
    gesehen = []

    def leitung(anfrage, frist):
        gesehen.append(anfrage.full_url)
        return b'{"models": [{"name": "qwen3:30b"}]}'
    monkeypatch.setattr(assistent, "_oeffne", leitung)
    monkeypatch.setattr(heimstand, "grafikkarte", lambda: {"frei_gb": None, "satz": "x"})
    monkeypatch.setenv(assistent.UMGEBUNG_ADRESSE, "http://127.0.0.1:23456")
    monkeypatch.delenv(assistent.UMGEBUNG_MODELL, raising=False)
    _, h = _frage(server, befehl="GET", weg=server.WEG_HEIM)
    assert gesehen and all(u.startswith("http://127.0.0.1:23456/api/") for u in gesehen)
    assert h["assistent"]["stand"] == "bereit"
    assert "23456" not in json.dumps(h)


# =============================================================== die zwei Schalter am Start

@pytest.fixture
def gebaut(server, monkeypatch):
    echt = server.baue_server
    liste = []

    def bau(**kw):
        srv = echt(**kw)

        def sofort_beendet():
            raise KeyboardInterrupt
        srv.serve_forever = sofort_beendet
        liste.append(srv)
        return srv
    monkeypatch.setattr(server, "baue_server", bau)
    return liste


def test_schalter_sprachmodell_und_adresse_landen_am_server(server, gebaut, capsys):
    assert server.main(["--anschluss", "0", "--sprachmodell", "qwen3:14b",
                        "--assistent-adresse", "http://127.0.0.1:11999"]) == 0
    modell = gebaut[0].RequestHandlerClass.sprachmodell
    assert (modell.modell, modell.adresse) == ("qwen3:14b", "http://127.0.0.1:11999")
    gebaut[0].server_close()


def test_ohne_schalter_bleibt_der_server_bei_der_umgebung(server, gebaut):
    assert server.main(["--anschluss", "0"]) == 0
    assert gebaut[0].RequestHandlerClass.sprachmodell is None
    gebaut[0].server_close()


@pytest.mark.parametrize("schalter,stichwort", [
    (["--sprachmodell", "llama3.1:8b"], "Llama"),
    (["--sprachmodell", "gemma3:27b"], "Gemma"),
    (["--assistent-adresse", "file:///etc/passwd"], "http://"),
])
def test_ein_unzulaessiger_schalter_haelt_den_start_auf(server, gebaut, capsys, schalter,
                                                        stichwort):
    assert server.main(["--anschluss", "0", *schalter]) == 2
    assert stichwort in capsys.readouterr().out
    assert gebaut == [], "es wurde nichts gebaut"
