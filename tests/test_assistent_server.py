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
import threading
import time
import urllib.error
import urllib.request
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


# =========================================== H1 · eine Frage hält den Server nicht mehr fest

class _Langsam(Ersatz):
    """Ein Sprachmodell, das denkt — und meldet, wann es angefangen hat."""

    def __init__(self, sekunden=2.0):
        super().__init__([{"content": "fertig"}] * 4)
        self.sekunden = sekunden
        self.denkt = threading.Event()

    def chat(self, nachrichten, werkzeuge):
        self.denkt.set()
        time.sleep(self.sekunden)
        return super().chat(nachrichten, werkzeuge)


@pytest.fixture
def laufender_server(server, lauf, tmp_path):
    """Der echte Server über ``baue_server``, auf einem freien Anschluss, ohne Kennwort."""
    gebaute = []

    def baue(sprachmodell):
        srv = server.baue_server(anschluss=0, ordner=tmp_path, sprachmodell=sprachmodell)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        gebaute.append(srv)
        return f"http://127.0.0.1:{srv.server_address[1]}"
    yield baue
    for srv in gebaute:
        srv.shutdown()
        srv.server_close()


def _hole(adresse, weg, rumpf=None, frist=10.0):
    """``(code, antwort, sekunden)`` — GET ohne Rumpf, sonst POST mit JSON."""
    daten = None if rumpf is None else json.dumps(rumpf).encode()
    anfrage = urllib.request.Request(adresse + weg, data=daten,
                                     method="GET" if rumpf is None else "POST")
    beginn = time.monotonic()
    try:
        with urllib.request.urlopen(anfrage, timeout=frist) as a:
            code, roh = a.status, a.read()
    except urllib.error.HTTPError as fehler:
        code, roh = fehler.code, fehler.read()
    return code, json.loads(roh or b"null"), time.monotonic() - beginn


def _frage_im_hintergrund(adresse, weg, modell, ergebnis):
    faden = threading.Thread(
        target=lambda: ergebnis.append(_hole(adresse, weg, {"nachricht": "Hallo"})),
        daemon=True)
    faden.start()
    assert modell.denkt.wait(5), "die Frage kam nie beim Sprachmodell an"
    return faden


def test_waehrend_einer_frage_antwortet_der_fortschritt_sofort(server, laufender_server):
    """**Rot vor dem 01.10.2026:** ``HTTPServer`` nahm eine Anfrage nach der anderen; der
    Fortschritt wartete, bis das Sprachmodell fertig war."""
    modell = _Langsam(2.0)
    adresse = laufender_server(modell)
    erste = []
    faden = _frage_im_hintergrund(adresse, server.WEG_ASSISTENT, modell, erste)
    code, stand, dauer = _hole(adresse, server.WEG_FORTSCHRITT)
    assert code == 200 and stand["laeuft"] is False
    assert dauer < 1.0, f"der Fortschritt wartete {dauer:.1f} s auf die Frage"
    faden.join(10)
    assert erste and erste[0][0] == 200 and erste[0][1]["antwort"] == "fertig"


def test_eine_zweite_gleichzeitige_frage_wird_mit_satz_abgewiesen(server, laufender_server):
    modell = _Langsam(2.0)
    adresse = laufender_server(modell)
    erste = []
    faden = _frage_im_hintergrund(adresse, server.WEG_ASSISTENT, modell, erste)
    code, antwort, dauer = _hole(adresse, server.WEG_ASSISTENT, {"nachricht": "Noch eine"})
    assert code == 400 and antwort == {"fehler": server.SATZ_FRAGE_LAEUFT}
    assert dauer < 1.0, "abgewiesen, nicht gewartet"
    faden.join(10)
    assert erste[0][0] == 200
    # DANACH GEHT DIE NAECHSTE wieder — die Sperre ist zurueckgegeben.
    modell.sekunden = 0.0
    assert _hole(adresse, server.WEG_ASSISTENT, {"nachricht": "Jetzt"})[0] == 200


def test_waehrend_einer_frage_wird_nicht_gerechnet(server, laufender_server, lauf):
    """Bildmodell und Sprachmodell passen nicht zugleich auf die Karte — ``/api/rechne``
    und «Anwenden» weisen ab, statt das Bildmodell neben das Sprachmodell zu laden."""
    modell = _Langsam(2.0)
    adresse = laufender_server(modell)
    erste = []
    faden = _frage_im_hintergrund(adresse, server.WEG_ASSISTENT, modell, erste)
    code, antwort, _ = _hole(adresse, server.WEG_RECHNE, {})
    assert code == 400 and antwort == {"fehler": server.SATZ_RECHNEN_WAEHREND_FRAGE}
    code, antwort, _ = _hole(adresse, server.WEG_ASSISTENT_ANWENDEN,
                             {"vorschlag": {"einstellungen": {"kamera": "n"},
                                            "varianten": None}})
    assert code == 400 and antwort == {"fehler": server.SATZ_RECHNEN_WAEHREND_FRAGE}
    assert "entlade" not in modell.protokoll, "eine laufende Frage wird nicht entladen"
    faden.join(10)
    assert lauf == [] and server.LAUFSTAND.sicht()["laeuft"] is False


def test_zwei_gleichzeitige_rechenauftraege_starten_hoechstens_einen_lauf(server, lauf,
                                                                          monkeypatch,
                                                                          tmp_path):
    """**Rot vor dem 01.10.2026:** «läuft schon einer?» und «beginnen» waren zwei Griffe;
    zwischen ihnen lag das Lesen der Mappe. Zwei Anfragen zugleich starteten beide."""
    echt = server._schritte_gesamt

    def langsam(*a, **kw):
        time.sleep(0.3)
        return echt(*a, **kw)
    monkeypatch.setattr(server, "_schritte_gesamt", langsam)
    codes = []
    faeden = [threading.Thread(target=lambda: codes.append(_frage(
        server, befehl="POST", weg=server.WEG_RECHNE, ordner=tmp_path)[0]))
        for _ in range(2)]
    for f in faeden:
        f.start()
    for f in faeden:
        f.join(5)
    assert sorted(codes) == [200, 400], codes
    assert len(lauf) == 1


# ================================================================ M3 · die Mappe am Server

def _mappe(tmp_path, einstellungen):
    from aiimaging import projekt
    modell = tmp_path / "probe.glb"
    modell.write_bytes(b"glTF")
    projekt.speichere(projekt.neu(tmp_path, modell, einstellungen=einstellungen), tmp_path)
    return tmp_path


class _Merkt(Ersatz):
    def __init__(self, botschaften=()):
        super().__init__(botschaften)
        self.gesehen = []

    def chat(self, nachrichten, werkzeuge):
        self.gesehen.append(json.loads(json.dumps(nachrichten)))
        return super().chat(nachrichten, werkzeuge)


def test_der_assistent_prueft_gegen_die_mappe_und_sagt_dem_modell_was_sie_traegt(
        server, lauf, tmp_path):
    ordner = _mappe(tmp_path, {"kamera": "sSE", "prompt": "Haus am Hang"})
    e = _Merkt([{"content": "", "tool_calls": [
        {"function": {"name": "standpunkt_vorschlagen", "arguments": {"augenhoehe": 1.6}}}]},
        {"content": "Gut."}])
    code, antwort = _frage(server, befehl="POST", weg=server.WEG_ASSISTENT, sprachmodell=e,
                           ordner=ordner, rumpf={"nachricht": "Augenhöhe 1,6 m"})
    assert code == 200, antwort
    assert antwort["vorschlag"]["einstellungen"] == {"augenhoehe": 1.6}
    system = e.gesehen[0][0]["content"]
    assert "«Haus am Hang»" in system and "kamera «sSE»" in system
    assert str(tmp_path) not in system and "probe.glb" not in system
    # «ANWENDEN» PRUEFT EBENSO gegen die Mappe — und startet.
    code, antwort = _frage(server, befehl="POST", weg=server.WEG_ASSISTENT_ANWENDEN,
                           sprachmodell=Ersatz(), ordner=ordner,
                           rumpf={"vorschlag": antwort["vorschlag"]})
    assert code == 200, antwort
    assert lauf and lauf[0]["einstellungen"] == {"augenhoehe": 1.6}


def test_anwenden_weist_einen_standpunkt_ab_der_sich_mit_der_mappe_widerspricht(
        server, lauf, tmp_path):
    ordner = _mappe(tmp_path, {"innenraum": {"raum": "r1"}})
    e = Ersatz()
    code, antwort = _frage(server, befehl="POST", weg=server.WEG_ASSISTENT_ANWENDEN,
                           sprachmodell=e, ordner=ordner,
                           rumpf={"vorschlag": {"einstellungen": {"brennweite": 24},
                                                "varianten": None}})
    assert code == 400 and "zweimal" in antwort["fehler"]
    assert e.protokoll == [] and lauf == []


# ================================================ Auftrag 218 · Grafikkarte und Schrittzahl

def test_anwenden_und_rechne_nennen_dieselbe_schrittzahl(server, lauf, tmp_path):
    """``auf-20261001-218``: «Anwenden» meldete ``schritte_gesamt: null``. Ohne Angabe gilt
    die Vorgabe der Kette — und beide Wege nennen sie."""
    import inspect
    from aiimaging import kette
    ordner = _mappe(tmp_path, {"prompt": "Haus am Hang"})
    vorgabe = inspect.signature(kette.baue_kette).parameters["schritte"].default
    code, a = _frage(server, befehl="POST", weg=server.WEG_ASSISTENT_ANWENDEN,
                     sprachmodell=Ersatz(), ordner=ordner,
                     rumpf={"vorschlag": {"einstellungen": {"kamera": "n"},
                                          "varianten": None}})
    assert code == 200 and a["schritte_gesamt"] == vorgabe
    server.LAUFSTAND.beende()
    code, r = _frage(server, befehl="POST", weg=server.WEG_RECHNE, ordner=ordner)
    assert code == 200 and r["schritte_gesamt"] == vorgabe


def test_vor_der_frage_wird_die_grafikkarte_freigegeben(server, monkeypatch):
    from aiimaging import render
    gesehen = []

    def haelt_fest():
        gesehen.append("frei")
        return {"belegt_mib": 25_900, "haelt_bildmodell": True, "satz": "x"}
    monkeypatch.setattr(render, "gib_grafikspeicher_frei", haelt_fest)
    e = Ersatz([{"content": "nie"}])
    code, antwort = _frage(server, befehl="POST", weg=server.WEG_ASSISTENT, sprachmodell=e,
                           rumpf={"nachricht": "Hallo"})
    assert gesehen == ["frei"]
    assert code == 400 and antwort["fehler"] == assistent.SATZ_BILDMODELL_GELADEN
    assert e.protokoll == []


def test_heim_sagt_nicht_bereit_solange_das_bildmodell_liegt(server, monkeypatch):
    from aiimaging import render
    monkeypatch.setattr(heimstand, "grafikkarte", lambda: {"frei_gb": 6.1, "satz": "x"})
    monkeypatch.setattr(render, "grafikspeicher_des_prozesses",
                        lambda: {"belegt_mib": 25_900, "haelt_bildmodell": True, "satz": "x"})
    _, h = _frage(server, befehl="GET", weg=server.WEG_HEIM, sprachmodell=Ersatz())
    assert h["assistent"]["stand"] == "laedt"
    assert h["assistent"]["satz"] == assistent.SATZ_BILDMODELL_GELADEN


def test_nach_dem_lauf_wird_die_grafikkarte_vor_dem_fertig_freigegeben(server, monkeypatch,
                                                                       tmp_path):
    from aiimaging import arbeitsgang, render
    reihenfolge = []

    def frei():
        reihenfolge.append(("frei", server.LAUFSTAND.sicht()["laeuft"]))
        return {}
    monkeypatch.setattr(render, "gib_grafikspeicher_frei", frei)

    def scheitert(*_a, **_k):
        raise arbeitsgang.ArbeitsgangError("kaputt")
    monkeypatch.setattr(arbeitsgang, "rechne", scheitert)
    server.LAUFSTAND.beginne(tmp_path)
    server._rechne_im_hintergrund(tmp_path, False, {})
    assert reihenfolge == [("frei", True)], "freigegeben, solange der Lauf noch läuft"
    assert server.LAUFSTAND.sicht()["fehler"] == "kaputt"


# ======================================== POST /api/kopplung (Owner-Entscheid 63, 01.10.2026)

def _koppel_klasse(server, kennwort="geheim"):
    return type("FlaecheKopplung", (server.Flaeche,),
                {"kennwort": kennwort, "ordner": None, "kopplung_offen": None,
                 "sprachmodell": None})


def _an(server, klasse, *, befehl, weg, rumpf=None, angemeldet=True):
    """Wie ``_frage``, aber auf **einer** Klasse für mehrere Anfragen — die Kopplung liegt
    auf der Klasse und soll von Anfrage zu Anfrage dieselbe sein."""
    roh = json.dumps(rumpf if rumpf is not None else {}).encode()
    selbst = klasse.__new__(klasse)
    selbst.command, selbst.path = befehl, weg
    kopf = ("Basic " + base64.b64encode(f"{server.BENUTZER}:geheim".encode()).decode()
            if angemeldet else None)
    selbst.headers = {"Authorization": kopf, "Content-Length": str(len(roh))}
    selbst.rfile, selbst.wfile = io.BytesIO(roh), io.BytesIO()
    codes = []
    selbst.send_response = lambda code, *a, **k: codes.append(code)
    selbst.send_header = lambda *a: None
    selbst.end_headers = lambda: None
    (selbst.do_GET if befehl == "GET" else selbst.do_POST)()
    return codes[0], json.loads(selbst.wfile.getvalue() or b"null")


def test_kopplung_ohne_anmeldung_ist_401(server):
    klasse = _koppel_klasse(server)
    code, _ = _an(server, klasse, befehl="POST", weg=server.WEG_KOPPLUNG, angemeldet=False)
    assert code == 401 and klasse.kopplung_offen is None


def test_kopplung_gibt_eine_zahl_und_das_verbinden_damit_das_kennwort(server, capsys):
    klasse = _koppel_klasse(server)
    code, a = _an(server, klasse, befehl="POST", weg=server.WEG_KOPPLUNG)
    assert code == 200 and set(a) == {"zahl", "gilt_noch_s", "satz"}
    assert len(a["zahl"]) == 6 and a["zahl"].isdigit() and a["gilt_noch_s"] == 600
    # DIE ZAHL NIE INS FENSTER: Im Dienstbetrieb ist es das Systemprotokoll.
    assert a["zahl"] not in capsys.readouterr().out
    # EINE FALSCHE ZAHL zaehlt einen Versuch, mit dem gleichbleibenden Satz.
    falsch = "000000" if a["zahl"] != "000000" else "111111"
    code, v = _an(server, klasse, befehl="POST", weg=server.WEG_VERBINDEN,
                  rumpf={"pin": falsch}, angemeldet=False)
    assert code == 403 and v["verbunden"] is False
    # DIE ZAHL KAM VOM MAC (Entscheid 63, Befund 221 B3): Die Ablehnung schickt dorthin.
    from aiimaging import kopplung as _k
    assert v["satz"] == _k.SATZ_FUER_DAS_GERAET_VOM_MAC
    assert klasse.kopplung_offen.versuche_uebrig == 4
    code, v = _an(server, klasse, befehl="POST", weg=server.WEG_VERBINDEN,
                  rumpf={"pin": a["zahl"]}, angemeldet=False)
    assert code == 200 and v["verbunden"] is True
    assert (v["benutzer"], v["kennwort"]) == (server.BENUTZER, "geheim")
    assert a["zahl"] not in capsys.readouterr().out


def test_eine_neue_zahl_ersetzt_die_alte(server):
    from aiimaging import kopplung
    klasse = _koppel_klasse(server)
    _an(server, klasse, befehl="POST", weg=server.WEG_KOPPLUNG)
    alt = klasse.kopplung_offen
    _an(server, klasse, befehl="POST", weg=server.WEG_KOPPLUNG)
    assert klasse.kopplung_offen is not alt
    assert kopplung.stand(alt) != kopplung.STAND_OFFEN, "die alte Zahl gilt nicht mehr"
    assert kopplung.stand(klasse.kopplung_offen) == kopplung.STAND_OFFEN


def test_ohne_kennwort_am_server_gibt_es_keine_zahl(server):
    klasse = _koppel_klasse(server, kennwort=None)
    code, a = _an(server, klasse, befehl="POST", weg=server.WEG_KOPPLUNG, angemeldet=False)
    assert code == 400 and "ohne Kennwort" in a["fehler"] and "zahl" not in a
    assert klasse.kopplung_offen is None
