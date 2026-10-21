"""«Datei laden …» aus der Mappe am Mac stellt die Mappe am Heim-PC nicht um.

Befund ``auf-20261021-304`` B1 (21.10.2026): ``POST /knoten/modell-laden`` machte die neue Mappe
**immer** zur zuletzt geöffneten (Entscheid 85 B). Kam das Laden aus der Mac-App mit offener
Mappe am Mac, zeigten danach ``/knoten/mappe``, die Knotenansicht, die Visbox-Seite und das iPad
im Übergang für **alle** Geräte die neue Mappe; der Helfer stellte sie nach rund drei Minuten von
Hand zurück.

Seither:

* Mit ``X-Mappe-Am-Mac`` entsteht am Heim-PC **höchstens ein Zwilling** — neu angelegt, mit dem
  Namen aus dem Dateinamen — und die zuletzt geöffnete Mappe bleibt, wie sie war. Der Stand sagt
  ``zuletzt_geoeffnet: false`` und nennt die Mappe am Mac (``am_mac``).
* Eine neue Fassung (90b) bekommt aus dem Mac **nur** der Zwilling, den der Mac mit
  ``X-Mappe-Heim`` nennt — nie die Start-Mappe oder die zuletzt geöffnete, auch wenn sie dieselbe
  Datei trägt. Dann kommt die Datei in den nächsten freien Namen.
* **Gegenprobe:** ohne Kopf (oder mit einem, der nicht taugt) alles wie bisher.

Regel 3: alles synthetisch (``tools/make_test_glb.py``).
"""
from __future__ import annotations

from aiimaging import modellladen, projekt

from test_modell_laden import ZWEI_TEILE, _glb, _Server, server, start  # noqa: F401 — Fixtures

MAC = {"X-Mappe-Am-Mac": "Mein%20Hof"}


def _lade(s, dateiname, inhalt, kopf=None):
    """Wie ``_Server.lade``, aber mit Köpfen — und bis zum Ende."""
    grenze = "----visbox-probe"
    rumpf = (f"--{grenze}\r\nContent-Disposition: form-data; name=\"datei\"; "
             f"filename=\"{dateiname}\"\r\nContent-Type: application/octet-stream\r\n\r\n"
             ).encode() + inhalt + f"\r\n--{grenze}--\r\n".encode()
    code, antwort = s._frage("POST", "/knoten/modell-laden", rumpf,
                             {"Content-Type": f"multipart/form-data; boundary={grenze}",
                              **(kopf or {})})
    assert code == 202, antwort
    s.warte()
    return s.get("/knoten/modell-laden")[1]["laden"]


# ======================================================================== die Bibliothek

def test_ersetzbar_leer_heisst_nie_in_eine_vorhandene_mappe(start):
    """Dieselbe Datei wie die Start-Mappe: ohne Erlaubnis kein 90b, sondern ``-2``."""
    ziel, ersetzen = modellladen.ziel_fuer(start.parent, "Startbau.glb")
    assert ziel == start and ersetzen is True                       # wie bisher
    ziel, ersetzen = modellladen.ziel_fuer(start.parent, "Startbau.glb", ersetzbar=set())
    assert ziel == start.parent / "Startbau-2" and ersetzen is False
    ziel, ersetzen = modellladen.ziel_fuer(start.parent, "Startbau.glb", ersetzbar={start})
    assert ziel == start and ersetzen is True


# ======================================================================== der Server

def test_aus_der_mappe_am_mac_bleibt_die_mappe_am_heim_pc(server, start):
    s = _Server(server, start)
    vorher = s.get("/knoten/mappe")[1]
    laden = _lade(s, "Neubau.glb", _glb(), MAC)
    assert laden["stand"] == "geladen", laden
    # DER ZWILLING ist da, mit Namen, und der Mac kann ihn holen.
    assert laden["mappe"] == "Neubau" and laden["bauteile"] == 3
    assert laden["am_mac"] == "Mein Hof" and laden["zuletzt_geoeffnet"] is False
    assert (start.parent / "Neubau" / "projekt.json").is_file()
    code, paket = s.get("/knoten/mappe-paket?mappe=Neubau")
    assert code == 200 and paket["dateien"][0]["weg"] == "modell.glb"
    # UND DIE MAPPE ALLER ANDEREN GERAETE BLEIBT.
    assert s.klasse.zuletzt_geoeffnet is None
    assert s.get("/knoten/mappe")[1] == vorher
    code, seite = s.get("/api/projekt")
    assert code == 200 and seite["ordner"] == str(start)


def test_eine_vorher_geoeffnete_mappe_bleibt_die_zuletzt_geoeffnete(server, start):
    s = _Server(server, start)
    _lade(s, "Altbau.glb", _glb())                                 # ohne Kopf: wie bisher
    assert s.klasse.zuletzt_geoeffnet == str(start.parent / "Altbau")
    laden = _lade(s, "Neubau.glb", _glb(), MAC)
    assert laden["stand"] == "geladen" and laden["mappe"] == "Neubau"
    assert s.klasse.zuletzt_geoeffnet == str(start.parent / "Altbau")
    assert s.get("/knoten/mappe")[1]["mappe"] == "Altbau"
    # Und auch als Zwilling genannt bekommt die zuletzt geoeffnete keine Fassung vom Mac.
    laden = _lade(s, "Altbau.glb", _glb(ZWEI_TEILE), {**MAC, "X-Mappe-Heim": "Altbau"})
    assert laden["mappe"] == "Altbau-2" and laden["ersetzt"] is False
    assert s.get("/knoten/mappe")[1]["fassung"] == 1


def test_dieselbe_datei_wie_die_heim_mappe_wird_ein_zwilling_keine_fassung(server, start):
    s = _Server(server, start)
    laden = _lade(s, "Startbau.glb", _glb(ZWEI_TEILE), MAC)
    assert laden["stand"] == "geladen" and laden["ersetzt"] is False
    assert laden["mappe"] == "Startbau-2" and laden["fassung"] == 1
    # Die Start-Mappe hat keine neue Fassung bekommen.
    assert projekt.modellfassung(projekt.oeffne(start)["projekt"]) == 1
    assert s.get("/knoten/mappe")[1]["bauteile"] == 3


def test_der_genannte_zwilling_bekommt_die_neue_fassung(server, start):
    s = _Server(server, start)
    erste = _lade(s, "Wohnhaus.glb", _glb(), MAC)
    assert erste["mappe"] == "Wohnhaus" and erste["fassung"] == 1
    zweite = _lade(s, "Wohnhaus.glb", _glb(ZWEI_TEILE), {**MAC, "X-Mappe-Heim": "Wohnhaus"})
    assert zweite["mappe"] == "Wohnhaus" and zweite["ersetzt"] is True
    assert zweite["fassung"] == 2 and zweite["bauteile"] == 2
    assert s.klasse.zuletzt_geoeffnet is None
    # Ohne den Zwilling zu nennen: kein Hineinschreiben, eine neue Mappe daneben.
    dritte = _lade(s, "Wohnhaus.glb", _glb(), MAC)
    assert dritte["mappe"] == "Wohnhaus-2" and dritte["ersetzt"] is False


def test_der_zwilling_darf_nie_die_offene_mappe_sein(server, start):
    """Nennt der Mac die Start-Mappe als Zwilling, bekommt sie trotzdem keine Fassung."""
    s = _Server(server, start)
    laden = _lade(s, "Startbau.glb", _glb(ZWEI_TEILE), {**MAC, "X-Mappe-Heim": "Startbau"})
    assert laden["mappe"] == "Startbau-2" and laden["ersetzt"] is False
    assert projekt.modellfassung(projekt.oeffne(start)["projekt"]) == 1


# ======================================================================== die Gegenprobe

def test_gegenprobe_ohne_kopf_wie_bisher(server, start):
    s = _Server(server, start)
    laden = _lade(s, "Neubau.glb", _glb())
    assert laden["stand"] == "geladen" and laden["zuletzt_geoeffnet"] is True
    assert "am_mac" not in laden
    assert s.klasse.zuletzt_geoeffnet == str(start.parent / "Neubau")
    assert s.get("/knoten/mappe")[1]["mappe"] == "Neubau"
    # Und dieselbe Datei wie die Start-Mappe ist ohne Kopf weiter eine neue Fassung (90b).
    laden = _lade(s, "Startbau.glb", _glb(ZWEI_TEILE))
    assert laden["mappe"] == "Startbau" and laden["ersetzt"] is True


def test_gegenprobe_ein_schlechter_kopf_gilt_als_nicht_gesagt(server, start):
    s = _Server(server, start)
    laden = _lade(s, "Neubau.glb", _glb(), {"X-Mappe-Am-Mac": "..%2Fetc"})
    assert laden["zuletzt_geoeffnet"] is True
    assert s.klasse.zuletzt_geoeffnet == str(start.parent / "Neubau")


# ======================================================================== die Mac-App

def test_die_mac_app_schickt_die_koepfe_beim_laden():
    """Mit Mappe am Mac geht «Datei laden …» mit ``ladekoepfe`` hinüber (Kern und Wirt)."""
    from test_modell_laden import WURZEL
    kern = (WURZEL / "ipad" / "Visbox.swiftpm" / "Kern" / "Macmappe.swift").read_text(encoding="utf-8")
    quelle = (WURZEL / "ipad" / "VisboxMac" / "Sources" / "VisboxMac" / "Start"
              / "Knotenquelle.swift").read_text(encoding="utf-8")
    assert 'case ("POST", wegModellLaden): return .modellLaden' in kern
    assert 'public static let wegModellLaden = "/knoten/modell-laden"' in kern
    assert "case .modellLaden:" in quelle
    assert "zusatz: Mappenkern.ladekoepfe(mappe)" in quelle
