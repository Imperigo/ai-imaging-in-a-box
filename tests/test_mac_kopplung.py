"""Der Mac koppelt sich mit einer Zahl (Owner-Entscheid 83, 13.10.2026).

Geprüft wird an der Wirkung, über ganze Anfragen an ``Flaeche``:

* ``GET /api/hallo`` — ohne Anmeldung, ohne Geheimnis, ohne Rechnernamen;
* ``POST /api/kopplung/anfordern`` — ohne Anmeldung, die Zahl **nie** im Rumpf, die Anzeige
  wird aufgerufen, gedrosselt (eine neue Zahl je 30 s);
* die angeforderte Zahl: fünf Minuten, einmal, drei Versuche — und was ``verbinden`` dann
  über den künftigen Zugang sagt;
* der verschlüsselte Zuhörer im Heimnetz (``--heimnetz``): nur TLS, und der Fingerabdruck
  in der Antwort ist der des Zertifikats, das der Mac im Handschlag sieht;
* ``openssl``, ``notify-send`` und ``avahi-publish-service`` über eine Starter-Attrappe —
  keine Probe lässt am Heim-PC etwas aufpoppen oder kündigt etwas im WLAN an.
"""
from __future__ import annotations

import base64
import hashlib
import http.client
import io
import json
import shutil
import socket
import ssl
import sys
import threading
from pathlib import Path

import pytest

WURZEL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WURZEL / "src"))

from aiimaging import heimnetz, kopplung  # noqa: E402

FLAECHE = WURZEL / "oberflaeche"


@pytest.fixture(scope="module")
def server():
    sys.path.insert(0, str(FLAECHE))
    try:
        import server as modul
        return modul
    finally:
        sys.path.remove(str(FLAECHE))


class _Anzeige:
    """Die Attrappe für ``zeige_zahl`` — merkt sich, was gezeigt worden wäre."""

    def __init__(self):
        self.gezeigt = []

    def __call__(self, offen):
        self.gezeigt.append(offen.pin)


def _klasse(modul, *, kennwort="geheim", anzeige=None):
    return type("FlaecheMac", (modul.Flaeche,),
                {"kennwort": kennwort, "ordner": None, "kopplung_offen": None,
                 "kopplung_vom_mac": False, "kopplung_angefordert": False,
                 "kopplung_angefordert_um": None,
                 "zeige_zahl": staticmethod(anzeige or _Anzeige())})


def _frage(klasse, modul, *, befehl, weg, rumpf=b"{}", angemeldet=False, koepfe=None):
    selbst = klasse.__new__(klasse)
    selbst.command = befehl
    selbst.path = weg
    kopf = {"Content-Length": str(len(rumpf))}
    if angemeldet:
        kopf["Authorization"] = "Basic " + base64.b64encode(
            f"{modul.BENUTZER}:{klasse.kennwort}".encode()).decode()
    kopf.update(koepfe or {})
    selbst.headers = kopf
    selbst.rfile = io.BytesIO(rumpf)
    selbst.wfile = io.BytesIO()
    codes = []
    selbst.send_response = lambda code, *a, **k: codes.append(code)
    selbst.send_header = lambda *a: None
    selbst.end_headers = lambda: None
    (selbst.do_GET if befehl == "GET" else selbst.do_POST)()
    text = selbst.wfile.getvalue().decode("utf-8")
    return codes[0], (json.loads(text) if text else {}), text


def _anfordern(klasse, modul):
    return _frage(klasse, modul, befehl="POST", weg=modul.WEG_KOPPLUNG_ANFORDERN)


def _verbinden(klasse, modul, pin):
    return _frage(klasse, modul, befehl="POST", weg=modul.WEG_VERBINDEN,
                  rumpf=json.dumps({"pin": pin}).encode())


# ================================================================== 1 · hallo

def test_hallo_antwortet_ohne_anmeldung_und_ohne_geheimnis(server):
    klasse = _klasse(server, kennwort="ein-langes-kennwort")
    code, antwort, text = _frage(klasse, server, befehl="GET", weg=server.WEG_HALLO)
    assert code == 200
    assert antwort == {server.NAME.lower(): True, "fassung": server.aiimaging.__version__,
                       "name": f"{server.NAME} Heim-PC"}
    assert "ein-langes-kennwort" not in text
    assert socket.gethostname() not in text


def test_hallo_auch_hinter_einer_weiterleitung_ohne_kennwort(server):
    """Der Mac soll auch einen Heim-PC erkennen, der (noch) ohne Kennwort läuft — alles
    andere bleibt dort zu (403)."""
    klasse = _klasse(server, kennwort=None)
    koepfe = {"X-Forwarded-For": "100.64.0.9"}
    assert _frage(klasse, server, befehl="GET", weg=server.WEG_HALLO, koepfe=koepfe)[0] == 200
    assert _frage(klasse, server, befehl="GET", weg=server.WEG_PROJEKT,
                  koepfe=koepfe)[0] == 403


def test_hallo_nur_als_get(server):
    klasse = _klasse(server)
    assert _frage(klasse, server, befehl="POST", weg=server.WEG_HALLO)[0] == 401


# ================================================================== 2 · anfordern

def test_anfordern_zeigt_die_zahl_am_heim_pc_und_nie_im_rumpf(server):
    anzeige = _Anzeige()
    klasse = _klasse(server, anzeige=anzeige)
    code, antwort, text = _anfordern(klasse, server)
    assert code == 200, text
    assert antwort["angezeigt"] is True and antwort["neu"] is True
    assert len(anzeige.gezeigt) == 1
    pin = anzeige.gezeigt[0]
    assert pin not in text, "die Zahl darf nie in der Antwort stehen"
    assert "zahl" not in antwort and "pin" not in antwort
    assert antwort["gilt_bis"] in antwort["satz"]
    assert antwort["versuche"] == kopplung.VERSUCHE_ANGEFORDERT == 3
    offen = klasse.kopplung_offen
    assert offen.pin == pin and offen.versuche_uebrig == 3


def test_anfordern_ohne_kennwort_am_server_gibt_keine_zahl(server):
    anzeige = _Anzeige()
    klasse = _klasse(server, kennwort=None, anzeige=anzeige)
    code, antwort, _ = _anfordern(klasse, server)
    assert code == 400 and "Kennwort" in antwort["fehler"]
    assert anzeige.gezeigt == [] and klasse.kopplung_offen is None


def test_anfordern_nur_als_post_und_mit_kleinem_rumpf(server):
    klasse = _klasse(server)
    assert _frage(klasse, server, befehl="GET", weg=server.WEG_KOPPLUNG_ANFORDERN)[0] == 401
    gross = b"{" + b" " * (server.VERBINDEN_HOECHSTENS + 10) + b"}"
    assert _frage(klasse, server, befehl="POST", weg=server.WEG_KOPPLUNG_ANFORDERN,
                  rumpf=gross)[0] == 413


def test_die_drossel_laesst_hoechstens_eine_neue_zahl_je_30_s(server, monkeypatch):
    uhr = [1000.0]
    monkeypatch.setattr(kopplung.time, "monotonic", lambda: uhr[0])
    anzeige = _Anzeige()
    klasse = _klasse(server, anzeige=anzeige)
    assert _anfordern(klasse, server)[0] == 200
    erste = klasse.kopplung_offen

    # 10 s spaeter: dieselbe Zahl bleibt, nichts Neues am Bildschirm.
    uhr[0] += 10
    code, antwort, _ = _anfordern(klasse, server)
    assert code == 200 and antwort["neu"] is False
    assert "20 s" in antwort["satz"]
    assert len(anzeige.gezeigt) == 1 and klasse.kopplung_offen is erste

    # Nach 30 s: eine neue Zahl, die alte ist tot.
    uhr[0] += 21
    code, antwort, _ = _anfordern(klasse, server)
    assert code == 200 and antwort["neu"] is True
    assert len(anzeige.gezeigt) == 2
    assert kopplung.stand(erste) == kopplung.STAND_VERBRAUCHT
    assert klasse.kopplung_offen is not erste


def test_gedrosselt_und_ohne_geltende_zahl_kommt_429(server, monkeypatch):
    uhr = [500.0]
    monkeypatch.setattr(kopplung.time, "monotonic", lambda: uhr[0])
    klasse = _klasse(server)
    _anfordern(klasse, server)
    for _ in range(3):
        _verbinden(klasse, server, "xxxxxx")
    uhr[0] += 5
    code, antwort, _ = _anfordern(klasse, server)
    assert code == 429 and antwort["angezeigt"] is False and antwort["warten_s"] == 25


def test_die_drossel_rechnet_auf_der_stetigen_uhr():
    assert kopplung.naechste_anforderung_in(None) == 0.0
    assert kopplung.naechste_anforderung_in(100.0, jetzt=110.0) == 20.0
    assert kopplung.naechste_anforderung_in(100.0, jetzt=131.0) == 0.0
    assert kopplung.DROSSEL_ANGEFORDERT_S == 30.0


# ============================================== 3 · fünf Minuten, einmal, drei Versuche

def test_die_angeforderte_zahl_gilt_fuenf_minuten(server, monkeypatch):
    uhr = [2000.0]
    monkeypatch.setattr(kopplung.time, "monotonic", lambda: uhr[0])
    anzeige = _Anzeige()
    klasse = _klasse(server, anzeige=anzeige)
    _anfordern(klasse, server)
    assert kopplung.FRIST_ANGEFORDERT_S == 300.0
    uhr[0] += 300
    code, antwort, _ = _verbinden(klasse, server, anzeige.gezeigt[0])
    assert code == 403 and antwort["verbunden"] is False
    assert antwort["satz"] == kopplung.SATZ_FUER_DEN_MAC_ANGEFORDERT


def test_die_angeforderte_zahl_gilt_einmal_und_sagt_den_zugang(server):
    anzeige = _Anzeige()
    klasse = _klasse(server, kennwort="langes-kennwort", anzeige=anzeige)
    _anfordern(klasse, server)
    pin = anzeige.gezeigt[0]
    code, antwort, _ = _verbinden(klasse, server, pin)
    assert code == 200 and antwort["verbunden"] is True
    assert antwort["kennwort"] == "langes-kennwort" and antwort["benutzer"] == server.BENUTZER
    # OHNE ZUHOERER IM HEIMNETZ: dieselbe Adresse, unter der gefragt wurde.
    assert antwort["zugang"] == {"weg": "wie_gefragt", "adresse": None,
                                 "zertifikat_sha256": None}
    code, antwort, _ = _verbinden(klasse, server, pin)
    assert code == 403 and antwort["verbunden"] is False


def test_nach_drei_fehlversuchen_ist_die_zahl_geschlossen(server, capsys):
    anzeige = _Anzeige()
    klasse = _klasse(server, anzeige=anzeige)
    _anfordern(klasse, server)
    pin = anzeige.gezeigt[0]
    falsch = "000000" if pin != "000000" else "111111"
    for _ in range(3):
        assert _verbinden(klasse, server, falsch)[0] == 403
    assert kopplung.stand(klasse.kopplung_offen) == kopplung.STAND_AUFGEBRAUCHT
    assert "geschlossen" in capsys.readouterr().out
    code, antwort, _ = _verbinden(klasse, server, pin)
    assert code == 403 and "kennwort" not in antwort


def test_die_zahl_fuers_ipad_behaelt_ihre_regeln(server):
    """``POST /api/kopplung`` (angemeldet, Entscheid 63) bleibt bei zehn Minuten und fünf
    Versuchen — und gibt die Zahl weiter in der Antwort, weil der angemeldete Mac sie zeigt."""
    klasse = _klasse(server)
    code, antwort, _ = _frage(klasse, server, befehl="POST", weg=server.WEG_KOPPLUNG,
                              angemeldet=True)
    assert code == 200 and len(antwort["zahl"]) == 6
    assert klasse.kopplung_offen.versuche_uebrig == kopplung.VERSUCHE == 5
    assert klasse.kopplung_angefordert is False


# ============================================================ 4 · die Anzeige

class _Starter:
    def __init__(self, rueckgabe=0):
        self.befehle = []
        self.rueckgabe = rueckgabe

    def __call__(self, befehl, **kw):
        self.befehle.append(list(befehl))

        class _E:
            returncode = self.rueckgabe
            stdout = stderr = ""
        return _E()


def test_die_zahl_erscheint_im_fenster_und_als_mitteilung(server, capsys):
    offen = kopplung.eroeffne(_pin="123456", frist_s=300, versuche=3)
    starter = _Starter()
    grund = server.zeige_zahl_mit_mitteilung(offen, starter=starter,
                                             wo=lambda n: f"/usr/bin/{n}")
    assert grund is None
    assert "123 456" in capsys.readouterr().out
    (befehl,) = starter.befehle
    assert befehl[0] == "/usr/bin/notify-send"
    assert "123 456" in befehl[-1] and offen.gilt_bis in befehl[-1]


def test_ohne_notify_send_nur_fenster_mit_grund(server, capsys):
    offen = kopplung.eroeffne(_pin="654321", frist_s=300, versuche=3)
    starter = _Starter()
    grund = server.zeige_zahl_mit_mitteilung(offen, starter=starter, wo=lambda n: None)
    assert grund and "notify-send fehlt" in grund
    aus = capsys.readouterr().out
    assert "654 321" in aus and "notify-send fehlt" in aus
    assert starter.befehle == []


def test_scheitert_notify_send_steht_der_grund_da():
    grund = heimnetz.mitteile("T", "x", starter=_Starter(rueckgabe=1),
                              wo=lambda n: "/usr/bin/notify-send")
    assert grund and "scheiterte" in grund


def test_eine_probe_mit_baue_server_zeigt_keine_mitteilung(server):
    s = server.baue_server(anschluss=0, kennwort="k")
    try:
        assert s.RequestHandlerClass.zeige_zahl is None
    finally:
        s.server_close()
    s = server.baue_server(anschluss=0, kennwort="k", mitteilung=True)
    try:
        assert s.RequestHandlerClass.zeige_zahl is server.zeige_zahl_mit_mitteilung
    finally:
        s.server_close()


# ============================================================ 5 · Zertifikat

def test_das_zertifikat_entsteht_mit_openssl_als_prozess(tmp_path):
    erzeugt = []

    def starter(befehl, **kw):
        erzeugt.append(befehl)
        Path(befehl[befehl.index("-keyout") + 1]).write_text("schluessel")
        Path(befehl[befehl.index("-out") + 1]).write_text("zertifikat")

        class _E:
            returncode = 0
        return _E()

    pem, schluessel, neu = heimnetz.zertifikat(tmp_path / "dienst", "Visbox", starter=starter,
                                               wo=lambda n: "/usr/bin/openssl")
    assert neu and pem.exists() and schluessel.exists()
    (befehl,) = erzeugt
    assert befehl[:3] == ["/usr/bin/openssl", "req", "-x509"]
    assert "-nodes" in befehl and "/CN=Visbox Heim-PC" in befehl
    assert oct(schluessel.stat().st_mode & 0o777) == "0o600"
    # Beim zweiten Mal wird nichts erzeugt.
    assert heimnetz.zertifikat(tmp_path / "dienst", "Visbox", starter=starter,
                               wo=lambda n: "/usr/bin/openssl")[2] is False
    assert len(erzeugt) == 1


def test_ohne_openssl_kein_zertifikat_und_kein_klartext(tmp_path):
    with pytest.raises(heimnetz.HeimnetzError, match="openssl"):
        heimnetz.zertifikat(tmp_path, "Visbox", wo=lambda n: None)


def test_ein_halbes_zertifikat_wird_nicht_still_ersetzt(tmp_path):
    (tmp_path / heimnetz.ZERTIFIKAT_DATEI).write_text("x")
    with pytest.raises(heimnetz.HeimnetzError, match="Beide löschen"):
        heimnetz.zertifikat(tmp_path, "Visbox", wo=lambda n: "/usr/bin/openssl")


def test_das_zeichen_sind_sechzehn_stellen_in_vierergruppen():
    assert heimnetz.zeichen("AB:12:cd:34:ef:56:78:90:11:22") == "ab12 cd34 ef56 7890"


# ============================================================ 6 · Ankündigung

class _Prozess:
    def __init__(self, rueckgabe=None):
        self.rueckgabe = rueckgabe
        self.beendet = False

    def poll(self):
        return self.rueckgabe

    def terminate(self):
        self.beendet = True

    def wait(self, timeout=None):
        return 0


def test_die_ankuendigung_laeuft_ueber_avahi_als_prozess():
    befehle, prozess = [], _Prozess()

    def starter(befehl, **kw):
        befehle.append(befehl)
        return prozess

    ankuendigung, satz = heimnetz.kuendige_an(
        name="Visbox", dienst="_visbox._tcp", anschluss=8732, texte=("fassung=1", "tls=1"),
        starter=starter, wo=lambda n: "/usr/bin/avahi-publish-service", warte=lambda s: None)
    assert ankuendigung is not None and "angekündigt" in satz
    assert befehle == [["/usr/bin/avahi-publish-service", "-s", "Visbox Heim-PC",
                        "_visbox._tcp", "8732", "fassung=1", "tls=1"]]
    ankuendigung.beende()
    assert prozess.beendet


def test_ohne_avahi_nur_tailscale_mit_grund():
    ankuendigung, satz = heimnetz.kuendige_an(name="Visbox", dienst="_visbox._tcp",
                                              anschluss=1, wo=lambda n: None)
    assert ankuendigung is None and "nur über Tailscale" in satz


def test_gibt_avahi_gleich_auf_steht_der_grund_da():
    ankuendigung, satz = heimnetz.kuendige_an(
        name="Visbox", dienst="_visbox._tcp", anschluss=1,
        starter=lambda b, **k: _Prozess(rueckgabe=1),
        wo=lambda n: "/usr/bin/avahi-publish-service", warte=lambda s: None)
    assert ankuendigung is None and "aufgegeben" in satz


# ============================================================ 7 · nur TLS im Heimnetz

def test_ohne_kennwort_oder_zertifikat_kein_zuhoerer(server):
    ohne = server.baue_server(anschluss=0)
    try:
        with pytest.raises(server.FlaechenError, match="Kennwort"):
            server.baue_heimnetz_server(ohne, adresse="127.0.0.1", anschluss=0,
                                        zertifikat="x", schluessel="y")
    finally:
        ohne.server_close()
    mit = server.baue_server(anschluss=0, kennwort="k")
    try:
        with pytest.raises(server.FlaechenError, match="Klartext"):
            server.baue_heimnetz_server(mit, adresse="127.0.0.1", anschluss=0,
                                        zertifikat=None, schluessel=None)
        with pytest.raises(server.FlaechenError, match="Adresse"):
            server.baue_heimnetz_server(mit, adresse="0.0.0.0", anschluss=0,
                                        zertifikat="x", schluessel="y")
    finally:
        mit.server_close()


def test_heimnetz_verlangt_die_kennwortdatei(server, capsys):
    assert server.main(["--heimnetz", "--kennwort-erzeugen", "--anschluss", "0"]) == 2
    assert "--kennwort-datei" in capsys.readouterr().out


@pytest.mark.skipif(shutil.which("openssl") is None, reason="openssl fehlt hier")
def test_der_zuhoerer_spricht_nur_tls_und_nennt_den_fingerabdruck(server, tmp_path):
    pem, schluessel, _ = heimnetz.zertifikat(tmp_path, "Visbox")
    haupt = server.baue_server(anschluss=0, kennwort="kennwort-im-wlan")
    anzeige = _Anzeige()
    haupt.RequestHandlerClass.zeige_zahl = staticmethod(anzeige)
    heim = server.baue_heimnetz_server(haupt, adresse="127.0.0.1", anschluss=0,
                                       zertifikat=pem, schluessel=schluessel)
    faden = threading.Thread(target=heim.serve_forever, daemon=True)
    faden.start()
    anschluss = heim.server_address[1]
    try:
        # KLARTEXT: keine Antwort, nicht einmal ein Satz.
        with socket.create_connection(("127.0.0.1", anschluss), timeout=5) as roh:
            roh.sendall(b"GET /api/hallo HTTP/1.1\r\nHost: x\r\n\r\n")
            try:
                antwort = roh.recv(4096)
            except (ConnectionResetError, socket.timeout):
                antwort = b""
        assert b"HTTP/" not in antwort and b"visbox" not in antwort

        # TLS (ungeprueft, wie der Mac beim ersten Mal — er heftet danach an).
        kontext = ssl.create_default_context()
        kontext.check_hostname = False
        kontext.verify_mode = ssl.CERT_NONE

        def frage(methode, weg, rumpf=None):
            v = http.client.HTTPSConnection("127.0.0.1", anschluss, context=kontext, timeout=5)
            v.request(methode, weg, body=rumpf,
                      headers={"Content-Type": "application/json"} if rumpf else {})
            gesehen = v.sock.getpeercert(binary_form=True)
            a = v.getresponse()
            daten = json.loads(a.read() or b"{}")
            v.close()
            return a.status, daten, gesehen

        status, daten, gesehen = frage("GET", server.WEG_HALLO)
        assert status == 200 and daten["visbox"] is True
        assert frage("POST", server.WEG_KOPPLUNG_ANFORDERN, b"{}")[0] == 200
        status, daten, gesehen = frage("POST", server.WEG_VERBINDEN,
                                       json.dumps({"pin": anzeige.gezeigt[0]}).encode())
        assert status == 200 and daten["kennwort"] == "kennwort-im-wlan"
        zugang = daten["zugang"]
        assert zugang["weg"] == "heimnetz"
        assert zugang["adresse"] == f"https://127.0.0.1:{anschluss}"
        assert zugang["zertifikat_sha256"] == hashlib.sha256(gesehen).hexdigest()
        assert zugang["zertifikat_sha256"] == heimnetz.fingerabdruck(pem)
    finally:
        heim.shutdown()
        heim.server_close()
        haupt.server_close()


@pytest.mark.skipif(shutil.which("openssl") is None, reason="openssl fehlt hier")
def test_der_zuhoerer_nimmt_kein_tls_unter_1_2(tmp_path):
    pem, schluessel, _ = heimnetz.zertifikat(tmp_path, "Visbox")
    kontext = heimnetz.tls_kontext(pem, schluessel)
    assert kontext.minimum_version >= ssl.TLSVersion.TLSv1_2
