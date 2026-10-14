"""Die Mac-App zeigt zuerst die Knoten (Owner-Entscheid 85, 14.10.2026; Blatt 19).

Anlass: Owner-Frage *«die Macversion ist vollständig KosmoVis-Werkzeug, nichts auf Website —
warum auf Website?»*. Bis dahin öffnete die Mac-App nach «Schon anfangen» die Visbox-Seite;
der Knotenbaum lag hinter deren Knopf. Entschieden am Blatt:

* **A** — Schalter «Knoten | Visbox-Seite» oben in der Kopfleiste;
* **B** — die Knoten zeigen die zuletzt auf der Seite geöffnete Mappe, sonst die vom Start;
* **C** — beim Öffnen immer zuerst die Knoten.

Swift lässt sich hier nicht übersetzen (das tut die Prüfstrecke am Mac); bewacht wird darum
die Abschrift (``Flaechenwahl.swift`` gegen ``WEG_KNOTEN`` des Servers) und die Verdrahtung
in der Mac-App, und **B** am echten Server-Code.
"""
from __future__ import annotations

import base64
import importlib.util
import io
import json
import re
import sys
from pathlib import Path

import pytest

from aiimaging import arbeitsgang

WURZEL = Path(__file__).resolve().parents[1]
FLAECHE = WURZEL / "oberflaeche"
WAHL = WURZEL / "ipad" / "Visbox.swiftpm" / "Kern" / "Flaechenwahl.swift"
ARBEIT = WURZEL / "ipad" / "VisboxMac" / "Sources" / "VisboxMac" / "Start" / "Arbeitsansicht.swift"


@pytest.fixture
def server():
    sys.path.insert(0, str(FLAECHE))
    try:
        import server as modul
        return modul
    finally:
        sys.path.remove(str(FLAECHE))


def _glb(tmp_path, name):
    spec = importlib.util.spec_from_file_location("mk_glb_mac", WURZEL / "tools" / "make_test_glb.py")
    mk = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mk)
    ziel = tmp_path / name
    ziel.write_bytes(mk.baue_glb([("Haus", (0, 0, 0), (8, 3, 5))]))
    return ziel


def _mappe(tmp_path, name):
    mappe = tmp_path / name
    mappe.mkdir()
    arbeitsgang.lege_an(mappe, _glb(tmp_path, name + ".glb"), name=name)
    return mappe


class _Server:
    """Viele Anfragen an **einen** Server (eine Klasse), wie im Betrieb — ohne Netz."""

    def __init__(self, modul, ordner):
        self.klasse = type("FlaecheMitOrdner", (modul.Flaeche,),
                           {"kennwort": "geheim", "ordner": ordner, "kopplung_offen": None,
                            "ablage": None, "zuletzt_geoeffnet": None})

    def frage(self, weg):
        selbst = self.klasse.__new__(self.klasse)
        selbst.command, selbst.path = "GET", weg
        kopf = "Basic " + base64.b64encode(b"visbox:geheim").decode()
        selbst.headers = {"Authorization": kopf, "Content-Length": "0"}
        selbst.rfile, selbst.wfile = io.BytesIO(b""), io.BytesIO()
        codes = []
        selbst.send_response = lambda code, *a, **k: codes.append(code)
        selbst.send_header = lambda *a: None
        selbst.end_headers = lambda: None
        selbst.do_GET()
        roh = selbst.wfile.getvalue()
        return codes[0], (json.loads(roh) if roh[:1] == b"{" else roh)


def test_b_die_knoten_zeigen_die_zuletzt_geoeffnete_mappe(server, tmp_path):
    start, andere = _mappe(tmp_path, "Startbau"), _mappe(tmp_path, "Anderbau")
    s = _Server(server, start)
    code, mappe = s.frage("/knoten/mappe")
    assert code == 200 and mappe["name"] == "Startbau"           # vorher: die vom Start
    code, _ = s.frage("/api/projekt?ordner=" + str(andere))
    assert code == 200
    code, mappe = s.frage("/knoten/mappe")
    assert code == 200 and mappe["name"] == "Anderbau"           # jetzt: die zuletzt geöffnete
    code, glb = s.frage("/knoten/modell.glb")
    assert code == 200 and glb[:4] == b"glTF"
    # Eine Mappe, die sich nicht öffnen liess, verschiebt nichts.
    code, _ = s.frage("/api/projekt?ordner=" + str(tmp_path / "gibt-es-nicht"))
    assert code == 404
    assert s.frage("/knoten/mappe")[1]["name"] == "Anderbau"
    # Ausdrücklich genannt gilt weiter vor allem.
    assert s.frage("/knoten/mappe?ordner=" + str(start))[1]["name"] == "Startbau"


def test_b_die_erinnerung_gehoert_dem_server_nicht_der_grundklasse(server, tmp_path):
    a = _Server(server, _mappe(tmp_path, "Erstbau"))
    a.frage("/api/projekt?ordner=" + str(_mappe(tmp_path, "Zweitbau")))
    assert server.Flaeche.zuletzt_geoeffnet is None
    gebaut = server.baue_server(ordner=_mappe(tmp_path, "Drittbau"), anschluss=0)
    try:
        assert gebaut.RequestHandlerClass.zuletzt_geoeffnet is None
    finally:
        gebaut.server_close()


def test_der_pfad_der_knoten_in_der_app_ist_der_des_servers(server):
    text = WAHL.read_text(encoding="utf-8")
    pfad = re.search(r'case \.knoten: return "([^"]+)"\s*\n\s*case \.seite: return Wege\.seite\.pfad',
                     text)
    assert pfad, "Flaechenwahl.pfad hat seine Form geändert"
    # MIT SCHRAEGSTRICH: ohne ihn antwortet der Server mit einer Weiterleitung.
    assert pfad.group(1) == server.WEG_KNOTEN + "/"


def test_c_zuerst_die_knoten_und_a_der_schalter_oben():
    wahl = WAHL.read_text(encoding="utf-8")
    assert re.search(r"static let beimOeffnen: Flaechenwahl = \.knoten", wahl)
    assert re.search(r"case knoten\s*\n\s*case seite", wahl)      # Reihenfolge im Schalter
    arbeit = ARBEIT.read_text(encoding="utf-8")
    assert "@State private var wahl: Flaechenwahl = Flaechenwahl.beimOeffnen" in arbeit
    assert ".pickerStyle(.segmented)" in arbeit
    assert "wahl.adresse(basis: basis)" in arbeit
    # Nichts gemerkt (C): kein AppStorage/UserDefaults für die Wahl.
    assert "AppStorage" not in arbeit and "UserDefaults" not in arbeit
