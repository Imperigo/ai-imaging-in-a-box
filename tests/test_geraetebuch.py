"""Das Gerätebuch des Heim-PC (Owner-Befund vom 20.10.2026, Visbox 0.2.11).

Das iPad war direkt mit dem Heim-PC gekoppelt, der Mac zeigte die Zeile «iPad» trotzdem als
«wartet» und bot neue Zahlen an — er konnte es nicht wissen. Seither vermerkt der Heim-PC, ob
ein iPad gekoppelt ist und wann es sich zuletzt meldete (``aiimaging.geraetebuch``), und gibt
es angemeldet über ``GET /api/geraete`` heraus.

Geprüft wird an der Wirkung, über ganze Anfragen an ``Flaeche``:

* die angenommene Zahl wird vermerkt — fürs iPad, nie für einen Mac, der sich selbst koppelt;
* angemeldete Anfragen mit ``X-Geraet: ipad`` über den Mac werden vermerkt, mit dem Weg;
* ein iPad, das **direkt** spricht, bekommt seit Entscheid 118a 410 mit Satz, und nichts wird
  vermerkt (Mac-App, Seite und Werkzeuge ohne Gerätekopf bleiben unberührt);
* das Buch übersteht einen Neustart (eine neue Klasse liest die Datei);
* angemeldet lesbar, unangemeldet abgewiesen, und **kein Geheimnis** darin (Datei 0600).
"""
from __future__ import annotations

import base64
import io
import json
import os
import stat
import sys
from pathlib import Path

import pytest

WURZEL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WURZEL / "src"))

from aiimaging import geraetebuch  # noqa: E402

FLAECHE = WURZEL / "oberflaeche"


@pytest.fixture(scope="module")
def server():
    sys.path.insert(0, str(FLAECHE))
    try:
        import server as modul
        return modul
    finally:
        sys.path.remove(str(FLAECHE))


KENNWORT = "ein-langes-kennwort-fuer-die-probe"


def _klasse(modul, datei=None):
    return type("FlaecheBuch", (modul.Flaeche,),
                {"kennwort": KENNWORT, "ordner": None, "kopplung_offen": None,
                 "kopplung_vom_mac": False, "kopplung_angefordert": False,
                 "kopplung_angefordert_um": None, "geraetebuch_datei": datei,
                 "zeige_zahl": staticmethod(lambda offen: None)})


def _frage(klasse, modul, *, befehl, weg, rumpf=b"{}", angemeldet=True, koepfe=None):
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


def _koppeln_wie_der_mac(klasse, modul, *, koepfe=None):
    """«iPad koppeln» am Mac (``POST /api/kopplung``), dann das iPad an ``/api/verbinden``."""
    code, antwort, _ = _frage(klasse, modul, befehl="POST", weg=modul.WEG_KOPPLUNG)
    assert code == 200, antwort
    return _frage(klasse, modul, befehl="POST", weg=modul.WEG_VERBINDEN, angemeldet=False,
                  rumpf=json.dumps({"pin": antwort["zahl"]}).encode(), koepfe=koepfe)


def _buch(klasse, modul, **kw):
    return _frage(klasse, modul, befehl="GET", weg=modul.WEG_GERAETE, **kw)


# ================================================================ 1 · die Kopplung

def test_ohne_kopplung_ist_kein_ipad_gekoppelt(server):
    code, antwort, _ = _buch(_klasse(server), server)
    assert code == 200
    assert antwort == {"ipad": {"gekoppelt": False, "gekoppelt_vor_s": None,
                                "zuletzt_gesehen_s": None, "weg": None}}


def test_eine_angenommene_zahl_fuers_ipad_wird_vermerkt_und_geschrieben(server, tmp_path):
    datei = tmp_path / "dienst" / geraetebuch.DATEINAME
    klasse = _klasse(server, datei)
    code, antwort, _ = _koppeln_wie_der_mac(klasse, server)
    assert code == 200 and antwort["verbunden"] is True
    code, buch, _ = _buch(klasse, server)
    assert buch["ipad"]["gekoppelt"] is True
    assert buch["ipad"]["weg"] == "direkt"
    assert buch["ipad"]["gekoppelt_vor_s"] == 0
    assert datei.exists(), "die Kopplung geht gleich auf die Platte"
    assert stat.S_IMODE(os.stat(datei).st_mode) == 0o600, "nur für den eigenen Benutzer"


def test_ein_ipad_vor_0_2_12_ohne_kopf_zaehlt_wenn_der_mac_die_zahl_holte(server):
    """Ein älteres iPad sagt seine Art nicht — die Zahl aus «iPad koppeln» galt ihm."""
    klasse = _klasse(server)
    assert _koppeln_wie_der_mac(klasse, server)[0] == 200
    assert _buch(klasse, server)[1]["ipad"]["gekoppelt"] is True


def test_ein_mac_der_sich_selbst_koppelt_ist_kein_ipad(server):
    """Die Zahl aus ``POST /api/kopplung/anfordern`` ist die des Mac (Entscheid 83)."""
    gezeigt = []
    klasse = _klasse(server)
    klasse.zeige_zahl = staticmethod(lambda offen: gezeigt.append(offen.pin))
    assert _frage(klasse, server, befehl="POST", weg=server.WEG_KOPPLUNG_ANFORDERN,
                  angemeldet=False)[0] == 200
    code, antwort, _ = _frage(klasse, server, befehl="POST", weg=server.WEG_VERBINDEN,
                              angemeldet=False, rumpf=json.dumps({"pin": gezeigt[0]}).encode(),
                              koepfe={"X-Geraet": "mac"})
    assert code == 200 and antwort["verbunden"] is True
    assert _buch(klasse, server)[1]["ipad"]["gekoppelt"] is False


def test_eine_abgelehnte_zahl_vermerkt_nichts(server):
    klasse = _klasse(server)
    _frage(klasse, server, befehl="POST", weg=server.WEG_KOPPLUNG)
    falsch = "000000" if klasse.kopplung_offen.pin != "000000" else "111111"
    code, _, _ = _frage(klasse, server, befehl="POST", weg=server.WEG_VERBINDEN,
                        angemeldet=False, rumpf=json.dumps({"pin": falsch}).encode())
    assert code == 403
    assert _buch(klasse, server)[1]["ipad"]["gekoppelt"] is False


# ================================================================ 2 · die Meldungen

def test_eine_angemeldete_anfrage_vom_ipad_wird_vermerkt_mit_dem_weg(server):
    klasse = _klasse(server)
    # UEBER DIE VERMITTLUNG DES MAC — der einzige Weg seit Entscheid 118a:
    assert _frage(klasse, server, befehl="GET", weg=server.WEG_FORTSCHRITT,
                  koepfe={"x-geraet": "ipad", "X-Geraet-Weg": "mac"})[0] == 200
    buch = _buch(klasse, server)[1]["ipad"]
    assert buch["gekoppelt"] is True, "wer das Kennwort hat, ist gekoppelt"
    assert buch["zuletzt_gesehen_s"] == 0 and buch["weg"] == "mac"
    assert buch["gekoppelt_vor_s"] is None, "wann, weiss das Buch dann nicht"


# ================================================= 2a · der direkte Weg endet (118a)

def test_ein_direkt_sprechendes_ipad_bekommt_410_mit_satz(server):
    klasse = _klasse(server)
    for koepfe in ({"X-Geraet": "ipad"}, {"X-Geraet": " iPad ", "X-Geraet-Weg": "direkt"},
                   {"x-geraet": "ipad", "X-Geraet-Weg": ""}):
        code, antwort, _ = _frage(klasse, server, befehl="GET", weg=server.WEG_FORTSCHRITT,
                                  koepfe=koepfe)
        assert code == 410, koepfe
        assert antwort == {"fehler": geraetebuch.SATZ_DIREKT_BEENDET}
        assert "über den Mac" in antwort["fehler"] and "«iPad koppeln»" in antwort["fehler"]
    assert _buch(klasse, server)[1]["ipad"]["gekoppelt"] is False, "abgewiesen heisst: nicht da"


def test_auch_unangemeldet_und_beim_koppeln_kommt_der_satz(server):
    """Vor Tür und Kopplung: Ein altes iPad, das direkt am Heim-PC koppeln will, erfährt den
    neuen Weg, statt an einer Zahl zu scheitern — und die Zahl bleibt für den Mac offen."""
    klasse = _klasse(server)
    assert _frage(klasse, server, befehl="GET", weg=server.WEG_FORTSCHRITT,
                  angemeldet=False, koepfe={"X-Geraet": "ipad"})[0] == 410
    code, antwort, _ = _koppeln_wie_der_mac(klasse, server, koepfe={"X-Geraet": "ipad"})
    assert code == 410 and antwort["fehler"] == geraetebuch.SATZ_DIREKT_BEENDET
    assert "kennwort" not in antwort and "benutzer" not in antwort
    assert server.kopplung.stand(klasse.kopplung_offen) == server.kopplung.STAND_OFFEN
    assert _buch(klasse, server)[1]["ipad"]["gekoppelt"] is False


def test_andere_geraete_bleiben_unberuehrt(server):
    """Mac-App (``mac``), Seite, KosmoOrbit und Werkzeuge (ohne Kopf) und das iPad über den Mac."""
    klasse = _klasse(server)
    for koepfe in ({}, {"X-Geraet": "mac"}, {"X-Geraet-Weg": "mac"},
                   {"X-Geraet": "ipad", "X-Geraet-Weg": "mac"},
                   {"X-Geraet": "ipad", "X-Geraet-Weg": " MAC "}):
        assert _frage(klasse, server, befehl="GET", weg=server.WEG_FORTSCHRITT,
                      koepfe=koepfe)[0] == 200, koepfe
    # DAS HALLO bleibt fuer jeden offen (es traegt kein Geheimnis):
    assert _frage(klasse, server, befehl="GET", weg=server.WEG_HALLO, angemeldet=False,
                  koepfe={"X-Geraet": "ipad"})[0] == 200


def test_die_regel_in_der_bibliothek():
    assert geraetebuch.direkt_vom_ipad("ipad", None) is True
    assert geraetebuch.direkt_vom_ipad("IPAD", "direkt") is True
    assert geraetebuch.direkt_vom_ipad("ipad", "mac") is False
    assert geraetebuch.direkt_vom_ipad(None, None) is False
    assert geraetebuch.direkt_vom_ipad("mac", None) is False
    assert geraetebuch.direkt_vom_ipad("ipad-pro", None) is False


def test_der_mac_und_fremde_arten_werden_nicht_vermerkt(server):
    klasse = _klasse(server)
    for art in ("mac", "telefon", "", "IPAD-Pro von Jemand"):
        _frage(klasse, server, befehl="GET", weg=server.WEG_FORTSCHRITT,
               koepfe={"X-Geraet": art})
    assert _buch(klasse, server)[1]["ipad"]["gekoppelt"] is False


def test_eine_unangemeldete_anfrage_mit_ipad_kopf_vermerkt_nichts(server):
    klasse = _klasse(server)
    code, _, _ = _frage(klasse, server, befehl="GET", weg=server.WEG_FORTSCHRITT,
                        angemeldet=False, koepfe={"X-Geraet": "ipad", "X-Geraet-Weg": "mac"})
    assert code == 401
    assert _buch(klasse, server)[1]["ipad"]["gekoppelt"] is False


def test_meldungen_werden_hoechstens_einmal_je_minute_geschrieben():
    buch = {"geraete": {}}
    assert geraetebuch.vermerke_anfrage(buch, "ipad", weg="direkt", jetzt=1000) is True
    geraetebuch.gemerkt(buch, "ipad", jetzt=1000)
    assert geraetebuch.vermerke_anfrage(buch, "ipad", weg="direkt", jetzt=1010) is False
    assert buch["geraete"]["ipad"]["zuletzt_um"] == 1010, "im Speicher immer der neueste"
    assert geraetebuch.vermerke_anfrage(buch, "ipad", weg="mac", jetzt=1011) is True, \
        "ein anderer Weg geht gleich hinaus"
    geraetebuch.gemerkt(buch, "ipad", jetzt=1011)
    assert geraetebuch.vermerke_anfrage(buch, "ipad", weg="mac", jetzt=1071) is True


# ================================================================ 3 · der Neustart

def test_das_buch_uebersteht_einen_neustart(server, tmp_path):
    datei = tmp_path / geraetebuch.DATEINAME
    erste = _klasse(server, datei)
    assert _koppeln_wie_der_mac(erste, server)[0] == 200
    # DER NEUSTART: eine neue Klasse (wie `baue_server` sie je Server baut), dieselbe Datei.
    zweite = _klasse(server, datei)
    buch = _buch(zweite, server)[1]["ipad"]
    assert buch["gekoppelt"] is True and buch["weg"] == "direkt"
    assert buch["gekoppelt_vor_s"] is not None


def test_baue_server_reicht_die_datei_durch(server, tmp_path):
    datei = tmp_path / geraetebuch.DATEINAME
    s = server.baue_server(kennwort=KENNWORT, anschluss=0, geraetebuch_datei=datei)
    try:
        assert s.RequestHandlerClass.geraetebuch_datei == datei
    finally:
        s.server_close()
    s = server.baue_server(kennwort=KENNWORT, anschluss=0)
    try:
        assert s.RequestHandlerClass.geraetebuch_datei is None, "ohne Datei nur im Speicher"
    finally:
        s.server_close()


def test_ein_kaputtes_buch_haelt_nichts_auf(server, tmp_path):
    datei = tmp_path / geraetebuch.DATEINAME
    datei.write_text("{nicht json", encoding="utf-8")
    klasse = _klasse(server, datei)
    assert _buch(klasse, server)[1]["ipad"]["gekoppelt"] is False
    assert _frage(klasse, server, befehl="GET", weg=server.WEG_FORTSCHRITT,
                  koepfe={"X-Geraet": "ipad", "X-Geraet-Weg": "mac"})[0] == 200
    assert json.loads(datei.read_text(encoding="utf-8"))["geraete"]["ipad"]["weg"] == "mac"
    # FREMDES WIRD WEGGELASSEN, NICHT GERATEN:
    datei.write_text(json.dumps({"geraete": {"ipad": {"zuletzt_um": "gestern", "weg": "funk"},
                                             "mac": {"zuletzt_um": 5}}}), encoding="utf-8")
    assert geraetebuch.lies(datei) == {"geraete": {}}


# ================================================================ 4 · Tür und Geheimnis

def test_das_buch_nur_angemeldet(server):
    klasse = _klasse(server)
    code, antwort, text = _buch(klasse, server, angemeldet=False)
    assert code == 401
    assert "ipad" not in antwort


def test_kein_geheimnis_im_buch(server, tmp_path):
    datei = tmp_path / geraetebuch.DATEINAME
    klasse = _klasse(server, datei)
    _frage(klasse, server, befehl="POST", weg=server.WEG_KOPPLUNG)
    pin = klasse.kopplung_offen.pin
    _frage(klasse, server, befehl="POST", weg=server.WEG_VERBINDEN, angemeldet=False,
           rumpf=json.dumps({"pin": pin}).encode())
    _, _, text = _buch(klasse, server)
    inhalt = datei.read_text(encoding="utf-8")
    for geheim in (KENNWORT, pin, server.BENUTZER):
        assert geheim not in text and geheim not in inhalt, geheim
    assert set(json.loads(inhalt)) == {"geraete"}
    assert set(json.loads(inhalt)["geraete"]["ipad"]) == {"gekoppelt_um", "zuletzt_um", "weg"}


def test_der_weg_steht_in_der_tafel_und_in_der_app(server):
    assert server.WEGTAFEL_LESEN[server.WEG_GERAETE] == "_geraete"
    wege = (WURZEL / "ipad" / "Visbox.swiftpm" / "Kern" / "Wege.swift").read_text(encoding="utf-8")
    assert 'Weg(pfad: "/api/geraete", methode: .get)' in wege
