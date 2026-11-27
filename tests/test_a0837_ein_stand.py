"""A0837 «Kein doppelter Mappenstand» — zwei Speicherungen, nie dieselbe Standnummer.

Befund V5 des externen Audits (24.11.2026), dort die Zeile «simultaneous project»: Zwei
Schreiber, die beide auf Stand 2 sitzen und fast gleichzeitig speichern, sahen beide auf
der Platte Stand 2, beide schrieben Stand 3, und die Änderung des ersten war weg, ohne dass
es irgendwo auffiel. :class:`projekt.ProjektKollision` gab es schon; sie kam nur zu spät,
weil zwischen dem Blick auf die Platte und dem Ersetzen keine Sperre lag.

Hier halten die beiden Schreiber nach dem Blick an einer Schranke an, damit genau dieses
Fenster offen steht. Mit der Sperre kommt der zweite gar nicht erst bis zum Blick, solange
der erste schreibt: Die Schranke läuft dann ab, der erste schreibt, und der zweite sieht
danach Stand 3.

**Ohne GPU, ohne Blender, ohne Netz.** Die Mappe entsteht aus ein paar Bytes.
"""
from __future__ import annotations

import json
import threading

import pytest

from aiimaging import projekt

#: Wie lange ein Schreiber an der Schranke auf den anderen wartet. Ohne Sperre kommen
#: beide in Millisekunden an; mit Sperre kommt der zweite nie, und die Schranke bricht.
SCHRANKE_S = 1.5


@pytest.fixture
def ifc(tmp_path):
    """Eine kleine, gültige IFC (Regel 3: synthetisch)."""
    pfad = tmp_path / "modelle" / "haus.ifc"
    pfad.parent.mkdir(parents=True, exist_ok=True)
    pfad.write_text(
        "ISO-10303-21;\nHEADER;\nFILE_DESCRIPTION((''),'');\n"
        "FILE_NAME('haus.ifc','2026-11-26T00:00:00',(''),(''),'','Testfixture','');\n"
        "FILE_SCHEMA(('IFC4'));\nENDSEC;\nDATA;\n"
        "#1=IFCSIUNIT(*,.LENGTHUNIT.,$,.METRE.);\nENDSEC;\nEND-ISO-10303-21;\n",
        encoding="utf-8")
    return pfad


def _mappe_auf_stand_2(tmp_path, ifc):
    wurzel = tmp_path / "mappe"
    p = projekt.neu(wurzel, ifc)
    projekt.speichere(p, wurzel)
    assert p["stand_nr"] == 2
    return wurzel


def _stand_der_platte(wurzel) -> dict:
    return json.loads((wurzel / projekt.PROJEKTDATEI).read_text(encoding="utf-8"))


# ------------------------------------------------------------------ Satz 1 · Schranke

def test_zwei_schreiber_an_der_schranke_ergeben_einen_stand_und_eine_kollision(
        tmp_path, ifc, monkeypatch):
    """Genau einer bekommt Stand 3, der andere eine Kollision, und nichts geht still verloren.

    *Heute beide 3* (Kopf f8c0a776): Beide blicken auf Stand 2, beide schreiben 3, der
    Letzte gewinnt.
    """
    wurzel = _mappe_auf_stand_2(tmp_path, ifc)
    schranke = threading.Barrier(2)
    echter_blick = projekt._stand_auf_der_platte

    def blick_mit_schranke(ziel):
        stand = echter_blick(ziel)
        try:
            schranke.wait(timeout=SCHRANKE_S)
        except threading.BrokenBarrierError:
            pass                     # der andere kam nicht: die Sperre hielt ihn auf
        return stand

    monkeypatch.setattr(projekt, "_stand_auf_der_platte", blick_mit_schranke)

    ergebnis: dict[str, object] = {}

    def schreiber(name: str):
        p = projekt.oeffne(wurzel)["projekt"]
        assert p["stand_nr"] == 2
        p["einstellungen"]["von"] = name
        try:
            projekt.speichere(p, wurzel)
            ergebnis[name] = p["stand_nr"]
        except projekt.ProjektKollision as fehler:
            ergebnis[name] = fehler

    faeden = [threading.Thread(target=schreiber, args=(n,)) for n in ("erster", "zweiter")]
    for f in faeden:
        f.start()
    for f in faeden:
        f.join(timeout=30)
    assert not any(f.is_alive() for f in faeden), "ein Schreiber hängt"

    gespeichert = [n for n, w in ergebnis.items() if w == 3]
    abgelehnt = [n for n, w in ergebnis.items() if isinstance(w, projekt.ProjektKollision)]
    assert len(gespeichert) == 1 and len(abgelehnt) == 1, (
        f"genau einer Stand 3, einer ProjektKollision — war {ergebnis!r}")

    platte = _stand_der_platte(wurzel)
    assert platte["stand_nr"] == 3
    assert platte["einstellungen"]["von"] == gespeichert[0], (
        "auf der Platte steht die Änderung dessen, der Stand 3 bekam")


# -------------------------------------------------------- Satz 2 · Fehler beim Ersetzen

def test_ein_schreibfehler_beim_ersetzen_laesst_den_stand_des_aufrufers_stehen(
        tmp_path, ifc, monkeypatch):
    """Scheitert das Ersetzen, trägt der Aufrufer weiter Stand 2 — und der zweite Versuch 3.

    *Heute* zog die Nummer schon vor dem Schreiben mit: Nach dem Fehler trug der Aufrufer
    Stand 3, die Platte 2, und der zweite Versuch schrieb Stand 4.
    """
    wurzel = _mappe_auf_stand_2(tmp_path, ifc)
    p = projekt.oeffne(wurzel)["projekt"]
    p["einstellungen"]["aenderung"] = "nach dem Fehler noch da"

    echtes_ersetzen = projekt.os.replace
    versuche = {"n": 0}

    def ersetzen_scheitert_einmal(quelle, ziel):
        versuche["n"] += 1
        if versuche["n"] == 1:
            raise OSError("simulierter Schreibfehler beim Ersetzen")
        return echtes_ersetzen(quelle, ziel)

    monkeypatch.setattr(projekt.os, "replace", ersetzen_scheitert_einmal)

    with pytest.raises(OSError, match="simulierter Schreibfehler"):
        projekt.speichere(p, wurzel)
    assert p["stand_nr"] == 2, "nach dem Fehler bleibt der alte Stand im Aufrufer"
    assert _stand_der_platte(wurzel)["stand_nr"] == 2
    assert [d.name for d in wurzel.iterdir()] == [projekt.PROJEKTDATEI], (
        "keine halbe Datei bleibt liegen")

    projekt.speichere(p, wurzel)
    assert p["stand_nr"] == 3
    platte = _stand_der_platte(wurzel)
    assert platte["stand_nr"] == 3
    assert platte["einstellungen"]["aenderung"] == "nach dem Fehler noch da"


# ------------------------------------------------------------------ Satz 3 · bleibt

def test_eine_neue_mappe_speichert_wie_bisher(tmp_path, ifc):
    wurzel = tmp_path / "neu"
    p = projekt.neu(wurzel, ifc)
    assert p["stand_nr"] == 1
    projekt.speichere(p, wurzel)
    assert p["stand_nr"] == 2
    assert _stand_der_platte(wurzel)["stand_nr"] == 2
    assert [d.name for d in wurzel.iterdir()] == [projekt.PROJEKTDATEI], (
        "die Sperre legt nichts in die Mappe")


def test_eine_alte_mappe_ohne_standnummer_behaelt_ihren_anfangsstand(tmp_path, ifc):
    wurzel = tmp_path / "alt"
    p = projekt.neu(wurzel, ifc)
    del p["stand_nr"]
    (wurzel / projekt.PROJEKTDATEI).write_text(
        json.dumps(p, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    alt = projekt.oeffne(wurzel)["projekt"]
    assert "stand_nr" not in alt
    projekt.speichere(alt, wurzel)
    assert alt["stand_nr"] == 1
    assert _stand_der_platte(wurzel)["stand_nr"] == 1
