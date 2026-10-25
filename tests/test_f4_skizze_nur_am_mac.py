"""Befund F4 (Mac-Demolauf 0.3.54, 24.10.2026): «Bild aus Skizze» aus einer Mappe am Mac.

Am Mac war die Mappe «haus-am-hang» offen; der Knoten «Skizze vom iPad» zeigte die Skizze
``ipad/skizze-…png`` (die Mac-App liest sie aus der Mappe am Mac, ``skizzen_lesen`` ebenso).
Bestellt kam vom Heim-PC: «steht nicht (mehr) in der Mappe … — verworfen oder nie abgelegt».
Falsch: Die Skizze war weder verworfen noch nie abgelegt — sie lag am Mac, und der Zwilling der
Mappe am Heim-PC hatte sie nie bekommen (die Mac-App schickt sie beim Bestellen noch nicht mit).

Seither sagt der Heim-PC bei einer Bestellung aus einer Mappe am Mac (``X-Mappe-Am-Mac``), dass
die Skizze nur am Mac liegt, und was bis zum Mitschicken zu tun ist. Ohne Mappe am Mac bleibt der
alte Satz — dort stimmt er.

Regel 3: synthetische Mappen (Muster ``test_mappenpaket``), keine Projektdaten.
"""
from __future__ import annotations

import http.client
import json
from pathlib import Path

import pytest

from aiimaging import knotenweg

from test_heimfehler_20261020 import _formular
from test_mappenpaket import _mappe, flaeche  # noqa: F401 (Fixture)

WURZEL = Path(__file__).resolve().parents[1]
SKIZZE_AM_MAC = "ipad/skizze-20261023-191207-616.png"
ALT = "verworfen oder nie abgelegt"


def _szene(name: str) -> bytes:
    # Mit Prompt: Eine Skizze ohne Anweisung und ohne Prompt weist der Heim-PC seit dem
    # 24.10.2026 schon beim Annehmen ab (Befund F4, ``test_skizze_anweisung_f4``).
    return json.dumps({"geometry": {"format": "glb"}, "style": {"prompt": "Abendlicht"},
                       "skizze": {"quelle": "mappe", "name": name}}).encode()


def _bestellen(anschluss, name, koepfe):
    rumpf, typ = _formular({"scene": (None, _szene(name)),
                            "model": ("m.glb", b"glTF" + b"\0" * 64)})
    leitung = http.client.HTTPConnection("127.0.0.1", anschluss, timeout=10)
    leitung.request("POST", "/bruecke/jobs", body=rumpf, headers={"Content-Type": typ, **koepfe})
    antwort = leitung.getresponse()
    return antwort.status, json.loads(antwort.read())


def _auftraege(tmp) -> list:
    return [d for d in (tmp / "ablage").iterdir() if d.is_dir()]


def test_skizze_nur_am_mac_sagt_es_statt_verworfen(flaeche):
    """Der Demolauf: Mappe am Mac mit Zwilling «Hof», die Skizze liegt nur am Mac."""
    _, anschluss, tmp = flaeche
    status, antwort = _bestellen(anschluss, SKIZZE_AM_MAC,
                                 {"X-Mappe-Am-Mac": "haus-am-hang", "X-Mappe-Heim": "Hof"})
    satz = antwort["fehler"]
    assert status == 400
    assert "liegt nur am Mac (Mappe «haus-am-hang»)" in satz
    assert "der Heim-PC hat sie nicht bekommen" in satz
    assert "Ohne Mappe am Mac" in satz and "am iPad neu senden" in satz
    assert ALT not in satz and "steht nicht (mehr)" not in satz
    # Kein Pfad im Satz (Regel 3), und nichts angelegt.
    assert str(tmp) not in satz
    assert _auftraege(tmp) == []


def test_mappe_am_mac_ohne_zwilling_sagt_dasselbe_statt_mappe_oeffnen(flaeche):
    _, anschluss, tmp = flaeche
    status, antwort = _bestellen(anschluss, SKIZZE_AM_MAC, {"X-Mappe-Am-Mac": "haus-am-hang"})
    assert status == 400
    assert "liegt nur am Mac" in antwort["fehler"]
    assert "Visbox-Seite öffnen" not in antwort["fehler"]
    assert _auftraege(tmp) == []


def test_liegt_die_skizze_auch_im_zwilling_wird_sie_angenommen(flaeche):
    _, anschluss, _ = flaeche
    status, zettel = _bestellen(anschluss, "skizze-a.png",
                                {"X-Mappe-Am-Mac": "haus-am-hang", "X-Mappe-Heim": "Hof"})
    assert status == 200 and zettel["mappe"] == "haus-am-hang"


def test_ohne_mappe_am_mac_bleibt_der_alte_satz(flaeche):
    """Die Mappe am Heim-PC: Dort heisst «fehlt» wirklich verworfen oder nie abgelegt."""
    _, anschluss, _ = flaeche
    status, antwort = _bestellen(anschluss, "skizze-weg.png", {})
    assert status == 400 and ALT in antwort["fehler"]
    assert "nur am Mac" not in antwort["fehler"]


def test_die_bibliothek_ohne_server(tmp_path):
    """Regel 4: derselbe Satz aus ``knotenweg.lege_an``, ohne Oberfläche."""
    zwilling = _mappe(tmp_path, "Hof")
    szene = json.loads(_szene(SKIZZE_AM_MAC))
    with pytest.raises(knotenweg.KnotenwegError) as fehler:
        knotenweg.lege_an(tmp_path / "ablage", szene, b"glTF" + b"\0" * 64, "m.glb",
                          mappe="haus-am-hang", mappe_pfad=zwilling, am_mac="haus-am-hang")
    assert str(fehler.value) == knotenweg.SATZ_SKIZZE_NUR_AM_MAC.format(
        name=SKIZZE_AM_MAC, mappe="haus-am-hang")
    with pytest.raises(knotenweg.KnotenwegError) as fehler:
        knotenweg.lege_an(tmp_path / "ablage", szene, b"glTF" + b"\0" * 64, "m.glb",
                          mappe="Hof", mappe_pfad=zwilling)
    assert ALT in str(fehler.value)


def test_der_server_reicht_die_mappe_am_mac_an_den_kern():
    """Quelltext-Wächter: ``_auftrag_annehmen`` nennt ``am_mac`` beim Anlegen."""
    quelle = (WURZEL / "oberflaeche" / "server.py").read_text(encoding="utf-8")
    assert "mappe_pfad=aus_mappe or None, am_mac=am_mac, ohne_klick=ohne_klick," in quelle
