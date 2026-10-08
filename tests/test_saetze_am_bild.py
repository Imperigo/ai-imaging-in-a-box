"""Zwei Sätze am Bild — gezeichnet auf Blatt 16 der Entwurfsfläche («Sätze am Bild», Teil B).

**Entscheid 73:** Rechnet ein Lauf ohne bestellten Standpunkt, steht unter dem Bild «Kein
Standpunkt bestellt — von Süden gerechnet.» Bis zum 08.10.2026 stand der Satz nur im
Rückgabewert von :func:`aiimaging.arbeitsgang.rechne` und im Laufstand des Dienstes — nach
einem Neuladen der Seite war er weg. Seither steht er **am Bildeintrag in der Mappe**
(``herkunft.standpunkt_vorgabe``), und die Sicht reicht die Zeile je Bild weiter
(``standpunkt_vorgabe``). War ein Standpunkt bestellt, steht dort ``None`` — und die Zeile
bleibt weg.

**Entscheid 70 (Anzeige):** Füllt das Haus weniger als 20 % des Bildes, ist das Urteil
«nicht beurteilbar» (``tiefenschaetzer.qa_gegen_soll``). Bis zum 08.10.2026 zeigten Fläche
und iPad dafür «NICHT GEMESSEN» — gemessen war aber. Seither ein eigenes Zeichen,
``nicht-beurteilbar``: Ton und Strich wie «nicht gemessen», getrennt durch das Wort. Der
Weg dahin: Prüfknoten (``gesamtwert_anwendbar``) → ``herkunft.messung`` am Bild → Sicht.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from aiimaging import arbeitsgang, projekt
from test_arbeitsgang import Werkbank

WURZEL = Path(__file__).resolve().parents[1]
FLAECHE = WURZEL / "oberflaeche"
SEITE = FLAECHE / "seite.html"

ZEILE = "Kein Standpunkt bestellt — von Süden gerechnet."


@pytest.fixture(scope="module")
def server():
    sys.path.insert(0, str(FLAECHE))
    try:
        import server as modul
        return modul
    finally:
        sys.path.remove(str(FLAECHE))


@pytest.fixture
def glb(tmp_path):
    import struct
    js = json.dumps({"asset": {"version": "2.0", "generator": "Testfixture"}}).encode()
    js += b" " * (-len(js) % 4)
    block = struct.pack("<II", len(js), 0x4E4F534A) + js
    pfad = tmp_path / "quelle" / "haus.glb"
    pfad.parent.mkdir(parents=True, exist_ok=True)
    pfad.write_bytes(struct.pack("<4sII", b"glTF", 2, 12 + len(block)) + block)
    return pfad


def _mappe(tmp_path, glb, **einstellungen):
    wurzel = tmp_path / "projekt"
    arbeitsgang.lege_an(wurzel, glb, name="Probehaus",
                        einstellungen={"prompt": "Abendlicht", "up_axis": "Y",
                                       **einstellungen})
    return wurzel


def _bilder(wurzel):
    return projekt.oeffne(wurzel)["projekt"]["bilder"]


class UnterZwanzig(Werkbank):
    """Eine Prüfung, wie ``qa_gegen_soll`` sie unter 20 % Gebäudeanteil liefert."""

    def qa(self, *, knoten, eingaben, out_dir):
        return {"status": "ok", "bestanden": None, "score": 0.97,
                "schwelle": knoten.params["schwelle"], "anteil_soll": 0.179,
                "gesamtwert_anwendbar": False,
                "begruendung": ("Nicht beurteilbar — das Haus füllt nur 17.9% des Bildes, "
                                "weniger als 20%; der Gesamtwert ist hier nicht anwendbar.")}


# ============================================= 1 · der Standpunkt-Satz steht in der Mappe

def test_ohne_standpunkt_traegt_jedes_bild_den_satz(tmp_path, glb):
    wurzel = _mappe(tmp_path, glb)
    arbeitsgang.rechne(wurzel, ausfuehrer=Werkbank().tabelle(), cache=None, varianten=2)
    bilder = _bilder(wurzel)
    assert len(bilder) == 2
    for b in bilder:
        vorgabe = b["herkunft"]["standpunkt_vorgabe"]
        assert vorgabe["kamera"] == "s"
        assert vorgabe["zeile"] == ZEILE
        assert vorgabe["satz"].startswith("Kein Standpunkt bestellt")


def test_mit_bestelltem_standpunkt_steht_none_am_bild(tmp_path, glb):
    wurzel = _mappe(tmp_path, glb, kamera="nNW")
    arbeitsgang.rechne(wurzel, ausfuehrer=Werkbank().tabelle(), cache=None)
    (b,) = _bilder(wurzel)
    assert "standpunkt_vorgabe" in b["herkunft"], "das Feld steht da — als None"
    assert b["herkunft"]["standpunkt_vorgabe"] is None


def test_die_zeile_im_rueckgabewert_ist_dieselbe_wie_am_bild(tmp_path, glb):
    wurzel = _mappe(tmp_path, glb)
    ergebnis = arbeitsgang.rechne(wurzel, ausfuehrer=Werkbank().tabelle(), cache=None)
    assert ergebnis["standpunkt_vorgabe"] == _bilder(wurzel)[0]["herkunft"]["standpunkt_vorgabe"]


def test_die_vorgabe_am_bild_ist_eine_eigene_kopie(tmp_path, glb):
    # `projekt.vermerke_bild` kopiert die Herkunft nur flach (Befund 22.09.2026).
    wurzel = _mappe(tmp_path, glb)
    ergebnis = arbeitsgang.rechne(wurzel, ausfuehrer=Werkbank().tabelle(), cache=None,
                                  varianten=2)
    a, b = (x["herkunft"]["standpunkt_vorgabe"] for x in ergebnis["projekt"]["bilder"])
    assert a is not b and a is not ergebnis["standpunkt_vorgabe"]


# ============================================ 2 · die Sicht reicht die Zeile je Bild weiter

def test_die_sicht_reicht_die_zeile_weiter(server):
    d = server._bild_fuer_die_flaeche({
        "bild": "a.png", "geometrie_bestanden": True,
        "herkunft": {"standpunkt_vorgabe": {"kamera": "s", "satz": "lang", "zeile": ZEILE}}})
    assert d["standpunkt_vorgabe"] == ZEILE


@pytest.mark.parametrize("herkunft", [
    {},                                              # aelterer Eintrag ohne Feld
    {"standpunkt_vorgabe": None},                    # Standpunkt bestellt
    {"standpunkt_vorgabe": {"kamera": "s"}},         # ohne Zeile: kein geratener Satz
    {"standpunkt_vorgabe": {"zeile": "  "}},
    {"standpunkt_vorgabe": "Kein Standpunkt"},       # keine Form, die wir schrieben
])
def test_ohne_vorgabe_keine_zeile(server, herkunft):
    d = server._bild_fuer_die_flaeche({"bild": "a.png", "herkunft": herkunft})
    assert d["standpunkt_vorgabe"] is None


def test_von_der_mappe_bis_zur_sicht(server, tmp_path, glb):
    wurzel = _mappe(tmp_path, glb)
    arbeitsgang.rechne(wurzel, ausfuehrer=Werkbank().tabelle(), cache=None)
    assert [b["standpunkt_vorgabe"] for b in server.sicht(wurzel)["bilder"]] == [ZEILE]


# ===================================================== 3 · das Zeichen «nicht beurteilbar»

def test_unter_zwanzig_prozent_ist_nicht_beurteilbar(server):
    grund = "Nicht beurteilbar — das Haus füllt nur 17.9% des Bildes."
    d = server._bild_fuer_die_flaeche({
        "bild": "a.png", "geometrie_bestanden": None,
        "herkunft": {"grund": grund, "messung": {"gesamtwert_anwendbar": False,
                                                 "score": 0.97, "schwelle": 0.65}}})
    assert d["zeichen"] == "nicht-beurteilbar"
    assert d["satz"] == grund
    assert d["score"] is None and d["schwelle"] is None, "ohne Urteil keine Zahl"


@pytest.mark.parametrize("messung", [
    None, {}, {"gesamtwert_anwendbar": None}, {"gesamtwert_anwendbar": True},
    {"gesamtwert_anwendbar": 0},                     # keine Zahl als Wahrheitswert
])
def test_sonst_ohne_urteil_bleibt_es_nicht_gemessen(server, messung):
    herkunft = {"grund": "NICHT GEMESSEN."}
    if messung is not None:
        herkunft["messung"] = messung
    d = server._bild_fuer_die_flaeche({"bild": "a.png", "geometrie_bestanden": None,
                                       "herkunft": herkunft})
    assert d["zeichen"] == "nicht-gemessen"


def test_ein_urteil_bleibt_ein_urteil(server):
    # Kann aus der Bibliothek nicht kommen (unter 20 % ist `bestanden` None); falls doch,
    # wird das Urteil nicht still umgedeutet.
    for urteil, zeichen in ((True, "bestanden"), (False, "durchgefallen")):
        d = server._bild_fuer_die_flaeche({
            "bild": "a.png", "geometrie_bestanden": urteil,
            "herkunft": {"messung": {"gesamtwert_anwendbar": False}}})
        assert d["zeichen"] == zeichen


def test_ein_entwurf_bleibt_nicht_gemessen(server):
    d = server._bild_fuer_die_flaeche({
        "bild": "a.png", "geometrie_bestanden": None, "entwurf": True,
        "herkunft": {"messung": {"gesamtwert_anwendbar": False}}})
    assert d["zeichen"] == "nicht-gemessen"


def test_der_pruefknoten_kommt_bis_zum_zeichen(server, tmp_path, glb):
    wurzel = _mappe(tmp_path, glb, kamera="s")
    arbeitsgang.rechne(wurzel, ausfuehrer=UnterZwanzig().tabelle(), cache=None)
    (b,) = _bilder(wurzel)
    assert b["geometrie_bestanden"] is None
    assert b["herkunft"]["messung"]["gesamtwert_anwendbar"] is False
    (s,) = server.sicht(wurzel)["bilder"]
    assert s["zeichen"] == "nicht-beurteilbar"
    assert s["satz"].startswith("Nicht beurteilbar")
    assert "NICHT GEMESSEN" not in s["satz"], "zwei Antworten am selben Bild"


def test_ohne_pruefung_steht_das_feld_als_none(tmp_path, glb):
    wurzel = _mappe(tmp_path, glb)
    arbeitsgang.rechne(wurzel, ausfuehrer=Werkbank().tabelle(), cache=None, entwurf=True)
    (b,) = _bilder(wurzel)
    assert b["herkunft"]["messung"]["gesamtwert_anwendbar"] is None


def test_eine_pruefung_ohne_das_feld_gibt_none(tmp_path, glb):
    # Die Werkbank meldet das Feld nicht — wie ein Prüfknoten vor dem 08.10.2026.
    wurzel = _mappe(tmp_path, glb)
    arbeitsgang.rechne(wurzel, ausfuehrer=Werkbank().tabelle(), cache=None)
    (b,) = _bilder(wurzel)
    assert b["herkunft"]["messung"]["gesamtwert_anwendbar"] is None
    assert b["geometrie_bestanden"] is True, "die Prüfung lief und urteilte"


# ================================================================= 4 · die Seite selbst

def test_die_seite_kennt_das_wort():
    seite = SEITE.read_text(encoding="utf-8")
    assert '"nicht-beurteilbar": "nicht beurteilbar"' in seite, "Wortliste am Kopf der Karte"
    assert '"nicht-beurteilbar": "NICHT BEURTEILBAR"' in seite, "Wortliste der Auflage"


def test_die_seite_zeichnet_es_wie_nicht_gemessen():
    seite = SEITE.read_text(encoding="utf-8")
    for regel in (".nicht-beurteilbar", ".rahmen.nicht-beurteilbar",
                  ".rahmen.nicht-beurteilbar .auflage"):
        assert regel in seite, regel
    strich = seite.split(".rahmen.nicht-beurteilbar", 1)[1].split("}", 1)[0]
    assert "dashed" in strich and "var(--ungemessen)" in strich


def test_die_seite_zeigt_die_zeile_unter_dem_bild():
    seite = SEITE.read_text(encoding="utf-8")
    baustein = seite.split("function zeigeBilder", 1)[1].split("\nfunction ", 1)[0]
    bild = baustein.index("karte.append(nebeneinander(")
    zeile = baustein.index("standpunktZeile(b)")
    assert bild < zeile < baustein.index("if (b.basis)"), "direkt unter dem Bild"
    assert 'id="standpunkt"' in seite, "«Standpunkt setzen» braucht ein Ziel"
    assert 'href = "#standpunkt"' in seite
    assert "Standpunkt setzen" in seite
    # Das «S» im Kreis ist die Vorgabe der Bibliothek, nicht eine eigene Annahme der Seite.
    assert f'feld("span", "richtung", "{arbeitsgang.STANDPUNKT_VORGABE.upper()}")' in seite
