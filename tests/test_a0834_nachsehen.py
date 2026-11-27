"""A0834 «Nachsehen verschiebt nichts» — die Warteschlange fragt einen schmalen Weg.

Die offene Visbox-Seite sieht alle zehn Sekunden nach, ob vom iPad eine Skizze kam
(``nachsehen()`` in ``oberflaeche/seite.html``). Bis zum 27.11.2026 fragte sie dafür
``/api/projekt`` — und das rechnete jedes Mal die ganze Projektsicht (Knotenbaum,
Grundriss, Abdruck des Modells) und setzte ``zuletzt_geoeffnet``: Ein Fenster, das nur
nachsah, stellte die Mappe eines anderen Fensters oder der Mac-App um (Entscheide 85 B und
90 gelten nur für das Öffnen).

Die Proben nehmen den Weg, den die Seite **wirklich** fragt — aus ihrem Quelltext gelesen,
nicht hier abgeschrieben. Sonst prüften sie einen Weg, den niemand ruft.

Die Zählung ist die Zeile «projection calls» der Audit-Probe ``visbox-speicherprobe.py``
(externes Audit 24.11.2026, Befund V1 und V7), umgestellt auf den Weg des Nachsehens.
"""
from __future__ import annotations

import base64
import json
import re
import statistics
import sys
import time
import urllib.parse
from pathlib import Path

import pytest

from aiimaging import arbeitsgang, projekt

WURZEL = Path(__file__).resolve().parents[1]
FLAECHE = WURZEL / "oberflaeche"
WERKZEUGE = WURZEL / "tools"
SEITE = FLAECHE / "seite.html"

#: Die Funktionen, die eine Projektsicht teuer machen — die Zeile «projection calls».
TEUER = ("baue_kette", "grundriss", "fingerabdruck")


@pytest.fixture
def modul():
    sys.path[:0] = [str(FLAECHE), str(WERKZEUGE)]
    try:
        import server
        import make_test_glb
        return server, make_test_glb
    finally:
        for weg in (str(FLAECHE), str(WERKZEUGE)):
            sys.path.remove(weg)


@pytest.fixture
def zwei_mappen(tmp_path, modul):
    """Zwei Mappen A und B über demselben synthetischen Situationsmodell (Regel 3)."""
    _, make_test_glb = modul
    haus = tmp_path / "situation.glb"
    haus.write_bytes(make_test_glb.baue_glb(make_test_glb.situationsszene()))
    a, b = tmp_path / "A", tmp_path / "B"
    arbeitsgang.lege_an(a, haus, name="A",
                        einstellungen={"up_axis": "Y", "prompt": "Abendlicht", "seed": 7})
    arbeitsgang.lege_an(b, haus, name="B",
                        einstellungen={"up_axis": "Y", "prompt": "Winter"})
    return haus, a, b


def _weg_des_nachsehens() -> str:
    """Der Weg, den ``nachsehen()`` in der Seite fragt — aus dem Quelltext."""
    text = SEITE.read_text(encoding="utf-8")
    anfang = text.index("async function nachsehen()")
    ende = text.index("\n}\n", anfang)
    treffer = re.search(r'fetch\(\s*"(/api/[a-z\-]+)\?ordner="', text[anfang:ende])
    assert treffer, "nachsehen() fragt einen Weg mit ?ordner="
    return treffer.group(1)


def _flaeche(server, *, start, zuletzt):
    """Eine Fläche ohne Netz, mit eigener Klasse — ``zuletzt_geoeffnet`` gehört der Klasse,
    und die echte ``Flaeche`` soll diese Probe nicht verstellen."""
    klasse = type("Probefläche", (server.Flaeche,),
                  {"zuletzt_geoeffnet": None if zuletzt is None else str(zuletzt)})
    f = klasse.__new__(klasse)
    f.ordner = str(start)
    antworten = []
    f._sende = lambda nutzlast, code=200: antworten.append((nutzlast, code))
    f._fehler = lambda satz, code=400: antworten.append(({"fehler": satz}, code))
    return klasse, f, antworten


def _frage(f, antworten, weg, ordner):
    f.path = weg + "?ordner=" + urllib.parse.quote(str(ordner))
    f._lies()
    return antworten[-1]


def _gezaehlt(handeln) -> dict:
    zahl = dict.fromkeys(TEUER, 0)

    def zaehle(rahmen, ereignis, _arg):
        if ereignis == "call" and rahmen.f_code.co_name in zahl:
            zahl[rahmen.f_code.co_name] += 1

    sys.setprofile(zaehle)
    try:
        handeln()
    finally:
        sys.setprofile(None)
    return zahl


def _reiche_skizze_ein(f, antworten, ordner):
    png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32
    f._skizze({"ordner": str(ordner), "png_base64": base64.b64encode(png).decode()})
    nutzlast, code = antworten[-1]
    assert code == 200 and "fehler" not in nutzlast, nutzlast
    return nutzlast


# ---------------------------------------------------------------------------- Satz 1

def test_die_synthetische_mappe_ist_die_des_audits(modul, zwei_mappen):
    """Dieselbe Lage wie die Audit-Probe: GLB 18 088 Byte, 45 Bedienfelder."""
    server, _ = modul
    haus, a, _ = zwei_mappen
    assert haus.stat().st_size == 18088
    assert len(server.sicht(a)["bedienfelder"]) == 45


def test_nachsehen_baut_keine_kette_keinen_grundriss_keinen_abdruck(modul, zwei_mappen):
    """Satz 1: eine Abfrage des Nachsehens ruft ``baue_kette``, ``grundriss`` und
    ``fingerabdruck`` je 0-mal (über ``/api/projekt`` waren es 46, 1, 1)."""
    server, _ = modul
    _, a, b = zwei_mappen
    _, f, antworten = _flaeche(server, start=a, zuletzt=b)
    weg = _weg_des_nachsehens()
    zahl = _gezaehlt(lambda: _frage(f, antworten, weg, a))
    nutzlast, code = antworten[-1]
    assert code == 200 and "fehler" not in nutzlast, nutzlast
    assert zahl == dict.fromkeys(TEUER, 0), f"Nachsehen über {weg} rechnet: {zahl}"


def test_oeffnen_rechnet_weiter_die_ganze_sicht(modul, zwei_mappen):
    """Gegenprobe: Die Zählung sieht die teuren Funktionen, wo sie laufen — sonst bewiese
    die Null oben nichts."""
    server, _ = modul
    _, a, b = zwei_mappen
    _, f, antworten = _flaeche(server, start=a, zuletzt=b)
    zahl = _gezaehlt(lambda: _frage(f, antworten, server.WEG_PROJEKT, a))
    assert zahl["baue_kette"] > 0 and zahl["grundriss"] == 1 and zahl["fingerabdruck"] == 1


# ---------------------------------------------------------------------------- Satz 2

def test_nachsehen_fuer_a_laesst_die_zuletzt_geoeffnete_auf_b(modul, zwei_mappen):
    """Satz 2: ``zuletzt_geoeffnet`` steht auf B; Nachsehen für A lässt es auf B; eine danach
    in A eingereichte Skizze steht in der nächsten Antwort des Nachsehens."""
    server, _ = modul
    _, a, b = zwei_mappen
    klasse, f, antworten = _flaeche(server, start=a, zuletzt=b)
    weg = _weg_des_nachsehens()

    vorher, _ = _frage(f, antworten, weg, a)
    assert klasse.zuletzt_geoeffnet == str(b), "Nachsehen hat die Mappe umgestellt"
    assert vorher.get("skizzen") == []

    abgelegt = _reiche_skizze_ein(f, antworten, a)
    danach, code = _frage(f, antworten, weg, a)
    assert code == 200
    assert klasse.zuletzt_geoeffnet == str(b)
    namen = [s.get("skizze") for s in danach.get("skizzen") or []]
    assert len(namen) == 1 and namen[0], danach
    assert abgelegt.get("skizze") in (None, namen[0])


def test_nachsehen_nennt_die_gefragte_mappe(modul, zwei_mappen):
    """Die Antwort sagt, welche Mappe sie meint — die Seite vergleicht ``ordner``, um «neu»
    zu markieren, und baut daraus die Bildwege."""
    server, _ = modul
    _, a, b = zwei_mappen
    _, f, antworten = _flaeche(server, start=a, zuletzt=b)
    nutzlast, _ = _frage(f, antworten, _weg_des_nachsehens(), a)
    assert nutzlast["ordner"] == str(a)


def test_nachsehen_in_einer_fremden_ablage_meldet_einen_fehler(modul, tmp_path, zwei_mappen):
    """Kein Projekt am Ort: ein Satz mit 404 wie beim Öffnen, keine leere Schlange."""
    server, _ = modul
    _, a, b = zwei_mappen
    klasse, f, antworten = _flaeche(server, start=a, zuletzt=b)
    leer = tmp_path / "leer"
    leer.mkdir()
    nutzlast, code = _frage(f, antworten, _weg_des_nachsehens(), leer)
    assert code == 404 and nutzlast.get("fehler")
    assert klasse.zuletzt_geoeffnet == str(b)


# ---------------------------------------------------------------------------- Satz 3

def test_oeffnen_setzt_die_zuletzt_geoeffnete_wie_bisher(modul, zwei_mappen):
    """Satz 3, Entscheid 85 B: Öffnen über ``/api/projekt`` merkt sich die Mappe."""
    server, _ = modul
    _, a, b = zwei_mappen
    klasse, f, antworten = _flaeche(server, start=a, zuletzt=b)
    _frage(f, antworten, server.WEG_PROJEKT, a)
    assert klasse.zuletzt_geoeffnet == str(a)


def test_der_stand_der_schlange_ist_derselbe_wie_beim_oeffnen(modul, zwei_mappen):
    """Satz 3: Die Seite zeichnet die Schlange nur neu, wenn ``skizzenStand`` sich ändert.
    Lieferte das Nachsehen die Skizzen anders als das Öffnen, zeichnete sie bei jedem
    Nachsehen neu."""
    server, _ = modul
    _, a, b = zwei_mappen
    _, f, antworten = _flaeche(server, start=a, zuletzt=b)
    _reiche_skizze_ein(f, antworten, a)
    _reiche_skizze_ein(f, antworten, a)
    # Die erste als gerechnet, mit einem Bild, bei dem die Skizze nicht ankam — so liest
    # zeigeWarteschlange die Bilder überhaupt.
    p = projekt.oeffne(a)["projekt"]
    erste = p["skizzen"][0]
    erste["stand"], erste["ergebnis"] = "gerechnet", "bild-a.png"
    p.setdefault("bilder", []).extend([
        {"bild": "bild-a.png", "schicht": "bild",
         "herkunft": {"skizze": erste["skizze"],
                      "messung": {"hinweise": [server.SKIZZE_NICHT_ANGEKOMMEN + " Probe."]}}},
        {"bild": "anderes.png", "schicht": "bild", "herkunft": {}}])
    projekt.speichere(p, a)
    geoeffnet, _ = _frage(f, antworten, server.WEG_PROJEKT, a)
    nachgesehen, _ = _frage(f, antworten, _weg_des_nachsehens(), a)
    assert nachgesehen["skizzen"] == geoeffnet["skizzen"]
    # Was zeigeWarteschlange an den Bildern liest, ist gleich: je Ergebnis einer Skizze
    # dieselben drei Felder wie beim Öffnen.
    felder = ("bild", "skizze_nicht_angekommen", "skizze_hinweis")
    nach_name = {b.get("bild"): b for b in geoeffnet.get("bilder") or []}
    assert [b["bild"] for b in nachgesehen["bilder"]] == ["bild-a.png"]
    assert nachgesehen["bilder"][0]["skizze_nicht_angekommen"] is True
    for b in nachgesehen["bilder"]:
        assert {k: b.get(k) for k in felder} == {
            k: nach_name[b["bild"]].get(k) for k in felder}


def test_nachsehen_zeichnet_nur_die_schlange_und_nur_bei_neuem_stand():
    """Satz 3, in der Seite: ``nachsehen()`` fragt den schmalen Weg, vergleicht den Stand
    und ruft nur ``zeigeWarteschlange`` — nie die Projektsicht oder die Zeichenfläche."""
    text = SEITE.read_text(encoding="utf-8")
    anfang = text.index("async function nachsehen()")
    rumpf = text[anfang:text.index("\n}\n", anfang)]
    assert "/api/projekt" not in rumpf
    assert "skizzenStand(d) !== schlangenStand" in rumpf
    aufrufe = set(re.findall(r"\b([a-zA-Z]+)\(", rumpf)) - {
        "nachsehen", "fetch", "encodeURIComponent", "json", "trim", "skizzenStand", "$"}
    assert aufrufe == {"zeigeWarteschlange"}, aufrufe


# ---------------------------------------------------------------------------- Satz 4

def test_messung_antwortgroesse_und_median(modul, zwei_mappen, capsys):
    """Satz 4: Antwortgrösse und Median von 20 warmen Abfragen, vorher (``/api/projekt``)
    und nachher (Weg des Nachsehens). Gedruckt für die Meldung; geprüft wird nur, dass der
    schmale Weg kleiner ist."""
    server, _ = modul
    _, a, b = zwei_mappen
    _, f, antworten = _flaeche(server, start=a, zuletzt=b)
    werte = {}
    for name, weg in (("vorher", server.WEG_PROJEKT), ("nachher", _weg_des_nachsehens())):
        nutzlast, _ = _frage(f, antworten, weg, a)
        zeiten = []
        for _ in range(20):
            t = time.perf_counter()
            _frage(f, antworten, weg, a)
            zeiten.append(time.perf_counter() - t)
        werte[name] = (len(json.dumps(nutzlast, ensure_ascii=False).encode()),
                       statistics.median(zeiten) * 1000)
    with capsys.disabled():
        for name, (groesse, ms) in werte.items():
            print(f"\nA0834 {name}: {groesse} Byte, Median {ms:.2f} ms")
    assert werte["nachher"][0] < werte["vorher"][0]
