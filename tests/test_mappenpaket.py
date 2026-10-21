"""«An den Mac holen» — das Mappenpaket des Heim-PC («Visbox eigenständig», Schritt 3, 21.10.2026).

Seit Owner-Entscheid 103 liegt die Mappe am Mac. Eine bestehende Mappe am Heim-PC holt die
Mac-App einmal herüber: Liste (``/knoten/mappen``), Paket (``/knoten/mappe-paket``), Dateien
(``/knoten/mappe-datei``). Und ein Auftrag aus einer Mappe am Mac nennt deren Namen im
Laufzettel, nicht den der Mappe, die am Heim-PC zuletzt offen war.

Regel 3: alles synthetisch, keine Projektdaten; die Antworten tragen keine Pfade.
"""
from __future__ import annotations

import http.client
import json
import threading
from pathlib import Path

import pytest

from aiimaging import arbeitsgang, knotenweg, mappenpaket, projekt

from test_heimfehler_20261020 import _formular
from test_knotenweg import _glb

WURZEL = Path(__file__).resolve().parents[1]
PNG = (b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00"
       b"\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc\xf8\xff\xff?\x00\x05\xfe\x02\xfe\xa7\x35\x81\x84"
       b"\x00\x00\x00\x00IEND\xaeB`\x82")


def _mappe(wurzel: Path, name: str, *, skizze: str | None = "skizze-a.png",
           bild: str | None = "bild-1.png") -> Path:
    quelle = wurzel / f"{name}.glb"
    quelle.write_bytes(_glb(wurzel, f"{name}-q.glb").read_bytes())
    mappe = wurzel / "mappen" / name
    arbeitsgang.lege_an(mappe, quelle, name=f"Probe {name}")
    # Die glb liegt fuer das Paket IN der Mappe (wie nach «Datei laden …»).
    p = projekt.oeffne(mappe)["projekt"]
    (mappe / "modell.glb").write_bytes(quelle.read_bytes())
    p.setdefault("import", {})["glb"] = "modell.glb"
    if skizze:
        (mappe / skizze).write_bytes(PNG)
        projekt.vermerke_skizze(p, skizze=skizze, stand=projekt.SKIZZE_OFFEN)
    if bild:
        (mappe / bild).write_bytes(PNG)
        projekt.vermerke_bild(p, bild=bild, schicht="ai-imaging-layer")
    projekt.speichere(p, mappe)
    return mappe


# ======================================================================== die Bibliothek

def test_die_liste_nennt_namen_keine_pfade(tmp_path):
    a = _mappe(tmp_path, "Hof")
    _mappe(tmp_path, "Turm", skizze=None)
    liste = mappenpaket.mappen_am_heim(a, None, rueckfall=tmp_path / "leer")
    namen = [m["mappe"] for m in liste["mappen"]]
    assert namen == ["Hof", "Turm"]
    hof = liste["mappen"][0]
    assert hof["modell"] is True and hof["skizzen"] == 1 and hof["bilder"] == 1
    assert str(tmp_path) not in json.dumps(liste)


def test_finde_nur_flache_namen(tmp_path):
    a = _mappe(tmp_path, "Hof")
    assert mappenpaket.finde("Hof", a, rueckfall=tmp_path / "leer") == a
    for schlecht in ("../Hof", ".Hof", "", "a/b", "x" * 61):
        with pytest.raises(mappenpaket.MappenpaketError):
            mappenpaket.finde(schlecht, a, rueckfall=tmp_path / "leer")
    with pytest.raises(mappenpaket.MappenpaketError) as fehler:
        mappenpaket.finde("Gibtsnicht", a, rueckfall=tmp_path / "leer")
    assert fehler.value.code == 404


def test_das_paket_nennt_modell_skizze_bild_und_den_graph(tmp_path):
    a = _mappe(tmp_path, "Hof")
    knotenweg.schreibe_graph(a, [{"kind": "visgraph", "id": "g1", "nodes": [], "edges": []}])
    paket = mappenpaket.paket(a)
    assert paket["format"] == mappenpaket.FORMAT
    assert [d["weg"] for d in paket["dateien"]] == ["modell.glb", "skizze-a.png", "bild-1.png"]
    assert [d["art"] for d in paket["dateien"]] == ["modell", "skizze", "bild"]
    assert paket["knoten"]["glb"] is True and paket["knoten"]["huellbox_m"]
    assert paket["graph"]["graphen"][0]["id"] == "g1"
    assert str(tmp_path) not in json.dumps(paket["knoten"])


def test_eine_datei_nur_aus_dem_paket(tmp_path):
    a = _mappe(tmp_path, "Hof")
    assert mappenpaket.datei(a, "skizze-a.png").read_bytes() == PNG
    assert mappenpaket.datei(a, "modell.glb").is_file()
    (a / "fremd.png").write_bytes(PNG)
    for weg in ("fremd.png", "projekt.json", "../Hof.glb", ""):
        with pytest.raises(mappenpaket.MappenpaketError):
            mappenpaket.datei(a, weg)


def test_eine_datei_ausserhalb_der_mappe_geht_nicht_ins_paket(tmp_path):
    a = _mappe(tmp_path, "Hof", bild=None)
    draussen = tmp_path / "draussen.png"
    draussen.write_bytes(PNG)
    p = projekt.oeffne(a)["projekt"]
    projekt.vermerke_bild(p, bild=str(draussen), schicht="ai-imaging-layer")
    projekt.speichere(p, a)
    assert "draussen.png" not in json.dumps(mappenpaket.paket(a)["dateien"])


# ======================================================================== der Server

@pytest.fixture
def flaeche(tmp_path, monkeypatch):
    import sys
    sys.path.insert(0, str(WURZEL / "oberflaeche"))
    import server
    start = _mappe(tmp_path, "Hof")
    monkeypatch.setattr(server.Flaeche, "ablage", tmp_path / "ablage")
    monkeypatch.setattr(server.Flaeche, "kennwort", None)
    monkeypatch.setattr(server.Flaeche, "ordner", start)
    monkeypatch.setattr(server.Flaeche, "zuletzt_geoeffnet", None)
    monkeypatch.setenv("AIIMAGING_MAPPEN_ORDNER", str(tmp_path / "rueckfall"))
    (tmp_path / "ablage").mkdir()
    dienst = server.ThreadingHTTPServer(("127.0.0.1", 0), server.Flaeche)
    threading.Thread(target=dienst.serve_forever, daemon=True).start()
    yield server, dienst.server_address[1], tmp_path
    dienst.shutdown()
    dienst.server_close()


def _hole(anschluss, weg, koepfe=None):
    leitung = http.client.HTTPConnection("127.0.0.1", anschluss, timeout=10)
    leitung.request("GET", weg, headers=koepfe or {})
    antwort = leitung.getresponse()
    return antwort.status, antwort.read()


def test_der_server_nennt_liste_paket_und_datei(flaeche):
    server, anschluss, tmp = flaeche
    status, roh = _hole(anschluss, "/knoten/mappen")
    assert status == 200 and [m["mappe"] for m in json.loads(roh)["mappen"]] == ["Hof"]
    status, roh = _hole(anschluss, "/knoten/mappe-paket?mappe=Hof")
    assert status == 200 and json.loads(roh)["mappe"] == "Hof"
    status, roh = _hole(anschluss, "/knoten/mappe-datei?mappe=Hof&weg=skizze-a.png")
    assert status == 200 and roh == PNG
    status, roh = _hole(anschluss, "/knoten/mappe-datei?mappe=Hof&weg=projekt.json")
    assert status == 404 and "gehört nicht zum Paket" in json.loads(roh)["fehler"]
    status, _ = _hole(anschluss, "/knoten/mappe-paket?mappe=..%2FHof")
    assert status == 400


def test_die_wege_lesen_draussen(flaeche):
    server = flaeche[0]
    for weg in (server.WEG_KNOTEN_MAPPEN, server.WEG_KNOTEN_MAPPE_PAKET, server.WEG_KNOTEN_MAPPE_DATEI):
        assert server.ausserhalb_der_reihe("GET", weg)


def test_standpunkte_auch_beim_namen_der_mappe(flaeche):
    _, anschluss, _ = flaeche
    status, roh = _hole(anschluss, "/knoten/mappe?mappe=Hof")
    assert status == 200 and json.loads(roh)["mappe"] == "Hof"


def _auftrag(anschluss, koepfe):
    rumpf, typ = _formular({"scene": (None, b'{"geometry": {"format": "glb"}}'),
                            "model": ("m.glb", b"glTF" + b"\0" * 64)})
    leitung = http.client.HTTPConnection("127.0.0.1", anschluss, timeout=10)
    leitung.request("POST", "/bruecke/jobs", body=rumpf, headers={"Content-Type": typ, **koepfe})
    antwort = leitung.getresponse()
    return antwort.status, json.loads(antwort.read())


def test_ein_auftrag_aus_der_mappe_am_mac_traegt_ihren_namen(flaeche):
    _, anschluss, _ = flaeche
    status, zettel = _auftrag(anschluss, {"X-Mappe-Am-Mac": "Mein%20Hof"})
    assert status == 200 and zettel["mappe"] == "Mein Hof"


def test_ohne_kopf_wie_bisher_die_mappe_des_heim_pc(flaeche):
    _, anschluss, _ = flaeche
    status, zettel = _auftrag(anschluss, {})
    assert status == 200 and zettel["mappe"] == "Hof"


def test_ein_schlechter_kopf_gilt_als_nicht_gesagt(flaeche):
    _, anschluss, _ = flaeche
    status, zettel = _auftrag(anschluss, {"X-Mappe-Am-Mac": "..%2Fetc"})
    assert status == 200 and zettel["mappe"] == "Hof"
