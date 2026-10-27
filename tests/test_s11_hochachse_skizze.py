"""«Bild aus Skizze» ohne Hochachse in der Mappe — Generalprobe 373, S11 (27.10.2026).

Befund (Ergebnis ``auf-20261027-373``, S11/B9): Über die Brücke bestellt, in einer Mappe, die aus
einer durchgereichten glb angelegt war, brachen Z-Image und Qwen nach rund 10 s ab — «Welche Achse
oben ist, steht für dieses Modell nicht fest». Das Grundbild DESSELBEN Modells war vorher gerechnet
worden: Der Abholer nimmt für eine glb der Brücke die Hochachse des Auftrags, sonst die Annahme
Y-up (``ANGENOMMENE_HOCHACHSE``). Nur der Skizzenlauf rechnet in der Mappe — und die wusste nichts.
Wer die Hochachse in der Mappe setzen wollte, wurde mit «prompt fehlt» abgewiesen: Die Prüfung der
Einstellungen baut die Kette, und die verlangt den Prompt zuerst. Den trägt eine Mappe der
Knotenansicht aber am Prompt-Knoten, nicht in den Einstellungen.

Geprüft wird hier, ohne GPU, über den Produktweg Annehmen → Freigeben → Abholen:

1. Weg KosmoOrbit (Mappe am Heim-PC, ``X-Mappe-Heim``): Die Skizze rechnet mit der Hochachse des
   Auftrags (sonst Y-up, wie das Grundbild), und das Ergebnis nennt sie samt Quelle.
2. Eine Mappe mit eigener Hochachse behält sie.
3. ``/api/einstellungen``: Die Hochachse lässt sich in einer Mappe ohne Prompt setzen; ein
   ausdrücklich leerer Prompt bleibt abgewiesen.
4. Weg Mac (``X-Mappe-Am-Mac``, ``skizze_png``/``unterlage_png``), eine glb ohne Hochachse: rechnet,
   die Mappe im Auftrag trägt «Y» (normalisiert, nicht «Y_UP»), das Ergebnis nennt sie.

Regel 3: alles synthetisch.
"""
from __future__ import annotations

import http.client
import json

import pytest

from aiimaging import abholer, knotenweg, projekt

from test_heimfehler_20261020 import _formular
from test_mappenpaket import flaeche  # noqa: F401 (Fixture)
from test_skizze_fuehrt import ROT, _Modell, _ergebnis, _rgba_png, _szene, _tabelle
from test_skizze_reist_mit import SKIZZE, UEBER, _png, _unterlage


def _post(anschluss, weg, rumpf, koepfe):
    leitung = http.client.HTTPConnection("127.0.0.1", anschluss, timeout=10)
    leitung.request("POST", weg, body=rumpf, headers=koepfe)
    antwort = leitung.getresponse()
    return antwort.status, json.loads(antwort.read() or b"{}")


def _abholen(ordner, modell):
    return abholer.hole_einen(
        ordner, verarbeite=abholer.verarbeiter(_skizzen_ausfuehrer=_tabelle(modell)),
        darf_rechnen=lambda: (True, "frei"))


def _gueltige_skizze(mappe):
    """Die Skizze der Probemappe als lesbares PNG (die aus ``test_mappenpaket`` prueft nur Bytes)."""
    _rgba_png(mappe / "skizze-a.png", 4, 4, {(1, 1): (*ROT, 255)})


def _glb_bytes(tmp):
    return (tmp / "Hof.glb").read_bytes()


def _bestelle_ueber_die_bruecke(anschluss, tmp, szene, koepfe, **felder):
    rumpf, typ = _formular({"scene": (None, json.dumps(szene).encode()),
                            "model": ("m.glb", _glb_bytes(tmp)), **felder})
    status, zettel = _post(anschluss, "/bruecke/jobs", rumpf, {"Content-Type": typ, **koepfe})
    assert status == 200, zettel
    knotenweg.freigeben(tmp / "ablage", zettel["job_id"], zettel["approval_token"])
    return tmp / "ablage" / zettel["job_id"]


# ============================================================ 1 · Weg KosmoOrbit (Mappe am Heim-PC)

@pytest.mark.parametrize("backbone", ["z-image-turbo", "qwen-image-2.1"])
def test_skizze_in_einer_mappe_ohne_hochachse_rechnet_mit_der_des_auftrags(flaeche,  # noqa: F811
                                                                         backbone):
    """Die Mappe der Generalprobe: angelegt aus einer glb, ohne Prompt, ohne Hochachse."""
    _, anschluss, tmp = flaeche
    mappe = tmp / "mappen" / "Hof"
    _gueltige_skizze(mappe)
    p = projekt.oeffne(mappe)["projekt"]
    assert not (p.get("einstellungen") or {}).get("up_axis")
    assert not (p.get("import") or {}).get("hochachse_steht_fest")
    ordner = _bestelle_ueber_die_bruecke(
        anschluss, tmp, _szene(name="skizze-a.png", backbone=backbone), {"X-Mappe-Heim": "Hof"})
    assert knotenweg.mappe_des_auftrags(ordner) is not None
    modell = _Modell()
    antwort = _abholen(ordner, modell)
    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort["grund"]
    ergebnis = _ergebnis(ordner)
    assert len(ergebnis["images"]) == 1
    assert ergebnis["engine_used"] == backbone
    # E128: Qwen bleibt markiert bis ins Ergebnis, Z-Image nicht.
    assert ergebnis.get("engine_license_open", False) is (backbone == "qwen-image-2.1")
    # Die Anweisung aus dem Prompt der Bestellung, übersetzt (F4: keine Anweisung, keine Bemerkung).
    assert modell.auftraege[-1]["prompt"] == "residential building in the evening light"
    assert abholer.lies_befund(ordner)["skizze"]["anweisung_aus"] == "prompt"
    befund = abholer.lies_befund(ordner)
    assert befund["hochachse"] == {"wert": "Y", "quelle": "annahme"}
    assert befund["skizze"]["hochachse"] == {"wert": "Y", "quelle": "annahme"}
    # Die Mappe selbst bleibt, wie sie war — die Annahme gilt für diesen Lauf, sie wird nicht
    # still zur Einstellung.
    assert not (projekt.oeffne(mappe)["projekt"].get("einstellungen") or {}).get("up_axis")


def test_eine_mappe_mit_eigener_hochachse_behaelt_sie(flaeche):  # noqa: F811
    _, anschluss, tmp = flaeche
    mappe = tmp / "mappen" / "Hof"
    _gueltige_skizze(mappe)
    p = projekt.oeffne(mappe)["projekt"]
    p["einstellungen"] = {**(p.get("einstellungen") or {}), "up_axis": "Z"}
    projekt.speichere(p, mappe)
    ordner = _bestelle_ueber_die_bruecke(anschluss, tmp, _szene(name="skizze-a.png"),
                                         {"X-Mappe-Heim": "Hof"})
    antwort = _abholen(ordner, _Modell())
    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort["grund"]
    assert abholer.lies_befund(ordner)["hochachse"] == {"wert": "Z", "quelle": "mappe"}


# ============================================================ 2 · Hochachse setzen ohne Prompt

def test_die_hochachse_laesst_sich_in_einer_mappe_ohne_prompt_setzen(flaeche):  # noqa: F811
    _, anschluss, tmp = flaeche
    mappe = tmp / "mappen" / "Hof"
    status, antwort = _post(anschluss, "/api/einstellungen",
                            json.dumps({"ordner": str(mappe),
                                        "einstellungen": {"up_axis": "Y"}}).encode(),
                            {"Content-Type": "application/json"})
    assert status == 200, antwort
    einstellungen = projekt.oeffne(mappe)["projekt"]["einstellungen"]
    assert einstellungen.get("up_axis") == "Y"
    # Kein Prompt hineingeschmuggelt: Der Platzhalter der Prüfung wird nicht gespeichert.
    assert not einstellungen.get("prompt")


@pytest.mark.parametrize("einstellungen,satz", [
    ({"prompt": ""}, "prompt fehlt"),
    ({"up_axis": "Zeichnung"}, "up_axis"),
])
def test_was_nicht_baut_bleibt_abgewiesen(flaeche, einstellungen, satz):  # noqa: F811
    _, anschluss, tmp = flaeche
    mappe = tmp / "mappen" / "Hof"
    status, antwort = _post(anschluss, "/api/einstellungen",
                            json.dumps({"ordner": str(mappe),
                                        "einstellungen": einstellungen}).encode(),
                            {"Content-Type": "application/json"})
    assert status == 400 and satz in antwort["fehler"], antwort
    assert "up_axis" not in (projekt.oeffne(mappe)["projekt"].get("einstellungen") or {})


# ============================================================ 3 · Weg Mac (Mappe am Mac)

def test_mac_weg_mit_glb_ohne_hochachse_rechnet_und_nennt_sie(flaeche):  # noqa: F811
    """Genau wie die Mac-App 0.3.70 bestellt: Formular mit Skizze, Unterlage und Angaben, Kopf
    ``X-Mappe-Am-Mac``, eine glb ohne Hochachse."""
    _, anschluss, tmp = flaeche
    ordner = _bestelle_ueber_die_bruecke(
        anschluss, tmp, _szene(name=SKIZZE), {"X-Mappe-Am-Mac": "haus-am-hang"},
        **{knotenweg.FELD_SKIZZE_PNG: ("skizze.png", _png(tmp, "s.png", {(1, 1): (*ROT, 255)})),
           knotenweg.FELD_UNTERLAGE_PNG: ("unterlage.png", _unterlage(tmp)),
           knotenweg.FELD_SKIZZE_INFO: (None, json.dumps({"ueber": UEBER,
                                                          "bemerkung": "ein Vordach"}).encode())})
    antwort = _abholen(ordner, _Modell())
    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort["grund"]
    gebaut = projekt.oeffne(ordner / knotenweg.ORDNER_SKIZZENMAPPE)["projekt"]
    # NORMALISIERT (Fehlerklasse 08.10./355): «Y», nicht die Schreibweise der Annahme «Y_UP».
    assert gebaut["einstellungen"]["up_axis"] == "Y"
    befund = abholer.lies_befund(ordner)
    assert befund["hochachse"] == {"wert": "Y", "quelle": "annahme"}
    assert "vom Bild unter der Skizze (sSW)" in befund["skizze"]["standpunkt"]
