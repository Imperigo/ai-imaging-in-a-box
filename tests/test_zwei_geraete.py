"""Zwei Geräte an derselben Mappe — und keines verliert seine Arbeit lautlos.

**Der Fall, um den es geht:** Ein iPad und die HomeStation führen dieselbe Mappe. Beide
öffnen sie, beide arbeiten daran, beide schreiben zurück. Bis zum 22.09.2026 gewann dabei
schlicht der Letzte, und der andere verlor alles — ohne Meldung, ohne Spur, ohne dass es
irgendwo auffiel.

Das ist dieselbe Bauform wie die zwei gleichzeitigen Läufe, die am 21.09.2026 einer den
anderen überschrieben haben, nur eine Ebene höher: dort zwei Rechnungen, hier zwei
Geräte.

> *Wer die Arbeit des anderen überschreibt, tut es nie absichtlich — er erfährt nur nie,
> dass es einen anderen gab.*

Neu trägt jede Mappe eine **Standnummer**. Wer speichert, muss von dem Stand kommen, der
auf der Platte liegt; sonst wird abgelehnt statt überschrieben.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from aiimaging import projekt


@pytest.fixture
def modell(tmp_path) -> Path:
    """Eine synthetische Modelldatei — Regel 3, und der Inhalt spielt keine Rolle."""
    pfad = tmp_path / "testkoerper.glb"
    pfad.write_bytes(b"glTF" + b"\x00" * 64)
    return pfad


@pytest.fixture
def mappe(tmp_path, modell) -> Path:
    wurzel = tmp_path / "mappe"
    p = projekt.neu(wurzel, modell, name="Testkoerper")
    projekt.speichere(p, wurzel)
    return wurzel


# --------------------------------------------------------------------------------------
# 1 · Die Nummer selbst
# --------------------------------------------------------------------------------------

def test_eine_neue_mappe_faengt_bei_eins_an(tmp_path, modell):
    p = projekt.neu(tmp_path / "m", modell)

    assert p["stand_nr"] == 1


def test_jedes_speichern_zaehlt_hoch(mappe):
    erst = projekt.oeffne(mappe)["projekt"]
    assert erst["stand_nr"] == 2, "das Anlegen selbst war Stand 1, das Schreiben Stand 2"

    projekt.speichere(erst, mappe)
    zweit = projekt.oeffne(mappe)["projekt"]

    assert zweit["stand_nr"] == 3


def test_der_aufrufer_traegt_die_neue_nummer_danach_selbst(mappe):
    """Sonst fällt er beim zweiten Speichern über seinen eigenen ersten Stand.

    *Eine Nummer, die nur in der Datei hochzählt und nicht im Arbeitsspeicher, macht aus
    dem zweiten Speichern desselben Aufrufers eine Kollision mit sich selbst.*
    """
    p = projekt.oeffne(mappe)["projekt"]
    projekt.speichere(p, mappe)
    projekt.speichere(p, mappe)   # darf nicht werfen

    assert projekt.oeffne(mappe)["projekt"]["stand_nr"] == 4


# --------------------------------------------------------------------------------------
# 2 · Der eigentliche Riegel
# --------------------------------------------------------------------------------------

def test_das_zweite_geraet_ueberschreibt_nicht(mappe):
    """**Der Wächter für den gemeldeten Fall** — zwei Geräte, eine Mappe."""
    ipad = projekt.oeffne(mappe)["projekt"]
    homestation = projekt.oeffne(mappe)["projekt"]

    homestation["einstellungen"] = {"prompt": "von der HomeStation"}
    projekt.speichere(homestation, mappe)

    ipad["einstellungen"] = {"prompt": "vom iPad"}
    with pytest.raises(projekt.ProjektKollision) as fehler:
        projekt.speichere(ipad, mappe)

    assert "Stand" in str(fehler.value)


def test_die_arbeit_des_ersten_steht_danach_noch_da(mappe):
    """Die Gegenprobe, und sie ist der ganze Zweck: nichts ist weg."""
    ipad = projekt.oeffne(mappe)["projekt"]
    homestation = projekt.oeffne(mappe)["projekt"]

    homestation["einstellungen"] = {"prompt": "von der HomeStation"}
    projekt.speichere(homestation, mappe)

    ipad["einstellungen"] = {"prompt": "vom iPad"}
    with pytest.raises(projekt.ProjektKollision):
        projekt.speichere(ipad, mappe)

    danach = projekt.oeffne(mappe)["projekt"]
    assert danach["einstellungen"]["prompt"] == "von der HomeStation"


def test_neu_oeffnen_loest_die_kollision(mappe):
    """Der Weg hinaus, und er ist der Grund für eine eigene Fehlerart.

    Die Kollision ist abfangbar: neu öffnen, die eigene Änderung darauf wiederholen,
    speichern. Ein Satz in einer Fehlermeldung liesse sich nur lesen.
    """
    ipad = projekt.oeffne(mappe)["projekt"]
    homestation = projekt.oeffne(mappe)["projekt"]
    homestation["einstellungen"] = {"prompt": "von der HomeStation"}
    projekt.speichere(homestation, mappe)

    try:
        projekt.speichere(ipad, mappe)
    except projekt.ProjektKollision:
        frisch = projekt.oeffne(mappe)["projekt"]
        frisch["einstellungen"]["prompt"] = "vom iPad, auf dem neuen Stand"
        projekt.speichere(frisch, mappe)

    assert (projekt.oeffne(mappe)["projekt"]["einstellungen"]["prompt"]
            == "vom iPad, auf dem neuen Stand")


def test_eine_kollision_ist_ein_projektfehler(mappe):
    """Wer heute ``ProjektError`` abfängt, fängt sie mit — kein stiller Durchschlupf."""
    assert issubclass(projekt.ProjektKollision, projekt.ProjektError)


# --------------------------------------------------------------------------------------
# 3 · Die dritte Antwort: nicht feststellbar heisst nicht «kollidiert»
# --------------------------------------------------------------------------------------

def test_eine_mappe_ohne_standnummer_klemmt_nicht(mappe):
    """Mappen von vor dieser Neuerung müssen weiter speichern können.

    *Eine Sperre, die alte Mappen unbrauchbar macht, ist keine Sicherung, sondern ein
    Datenverlust mit gutem Gewissen.*
    """
    import json
    datei = mappe / projekt.PROJEKTDATEI
    alt = json.loads(datei.read_text(encoding="utf-8"))
    alt.pop("stand_nr", None)
    datei.write_text(json.dumps(alt), encoding="utf-8")

    p = projekt.oeffne(mappe)["projekt"]
    projekt.speichere(p, mappe)   # darf nicht werfen

    assert projekt.oeffne(mappe)["projekt"]["stand_nr"] >= 1


def test_eine_unlesbare_datei_blockiert_das_speichern_nicht(mappe):
    """Unlesbar heisst nicht «neuerer Stand» — sonst wäre eine kaputte Datei eine Sperre."""
    (mappe / projekt.PROJEKTDATEI).write_text("kein json", encoding="utf-8")
    p = projekt.neu(mappe.parent / "zweit", mappe.parent / "zweit" / "x.glb")
    p_kopie = dict(p)

    projekt.speichere(p_kopie, mappe)   # darf nicht werfen

    assert projekt.oeffne(mappe)["projekt"]["stand_nr"] >= 1


# --------------------------------------------------------------------------------------
# 4 · Die Fläche: wiederholen darf, was hinzufügt — was ersetzt, muss fragen
# --------------------------------------------------------------------------------------
#
# Die beiden Stellen, an denen die Browseroberfläche speichert, kommen jetzt in den Fall
# einer Kollision — und sie müssen ihn VERSCHIEDEN behandeln. Ohne Wächter wären das zwei
# neue Zweige, die niemand je durchläuft, bis es zählt.

import base64 as _b64
import json as _json
import struct as _struct
import sys as _sys
from pathlib import Path as _Path

FLAECHE = _Path(__file__).resolve().parents[1] / "oberflaeche"


@pytest.fixture
def flaechenmodul():
    _sys.path.insert(0, str(FLAECHE))
    try:
        import server as modul
        return modul
    finally:
        _sys.path.remove(str(FLAECHE))


@pytest.fixture
def glb_mappe(tmp_path):
    """Eine Mappe mit durchgereichter glb — dieselbe Bauart wie in `test_oberflaeche`."""
    js = _json.dumps({"asset": {"version": "2.0", "generator": "T"}}).encode()
    js += b" " * (-len(js) % 4)
    block = _struct.pack("<II", len(js), 0x4E4F534A) + js
    modell = tmp_path / "haus.glb"
    modell.write_bytes(_struct.pack("<4sII", b"glTF", 2, 12 + len(block)) + block)

    wurzel = tmp_path / "p"
    p = projekt.neu(wurzel, modell,
                    einstellungen={"prompt": "Abendlicht", "up_axis": "Y"})
    p["import"] = {"status": "ok", "weg": "durchgereicht", "glb": str(modell),
                   "format": "glTF", "treue": None, "hochachse": None,
                   "hochachse_steht_fest": False, "hinweise": []}
    projekt.speichere(p, wurzel)
    return wurzel


def _flaeche(modul, wurzel):
    """Eine Fläche ohne Netz — dieselbe Attrappe wie in `test_oberflaeche`."""
    class Antwort:
        def __init__(self): self.daten = None
        def __call__(self, nutzlast, code=200): self.daten = (nutzlast, code)

    f = modul.Flaeche.__new__(modul.Flaeche)
    f.ordner = wurzel
    antwort = Antwort()
    f._sende = antwort
    f._fehler = lambda satz, code=400: antwort({"fehler": satz}, code)
    return f, antwort


def _drueben_schreibt(wurzel, prompt, schreiben):
    """Das andere Gerät legt einen neuen Stand ab, während die Fläche noch arbeitet.

    ``schreiben`` ist die **echte** Schreibfunktion: Der Test ersetzt sie gleich im Modul,
    und das andere Gerät darf nicht durch dieselbe Ersetzung laufen — sonst ruft es sich
    selbst.
    """
    anderes = projekt.oeffne(wurzel)["projekt"]
    anderes["einstellungen"]["prompt"] = prompt
    schreiben(anderes, wurzel)


def test_eine_skizze_geht_bei_einer_kollision_nicht_verloren(flaechenmodul, glb_mappe,
                                                             monkeypatch):
    """**Wiederholen darf, was hinzufügt.**

    Die Datei liegt beim Auftreten der Kollision schon auf der Platte. Wer nur meldete
    «geht nicht», liesse eine Zeichnung zurück, die es gibt und die in keiner Mappe steht.
    *Eine Zeichnung, die niemand mehr findet, ist verloren, auch wenn ihre Datei noch da
    ist.*
    """
    f, antwort = _flaeche(flaechenmodul, glb_mappe)
    png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32

    echtes_speichern = projekt.speichere
    zustand = {"erstes_mal": True}

    def dazwischen(p, wurzel):
        # Genau EINMAL schreibt das andere Geraet dazwischen — danach laeuft alles normal.
        if zustand["erstes_mal"]:
            zustand["erstes_mal"] = False
            _drueben_schreibt(_Path(wurzel), "von der HomeStation", echtes_speichern)
        return echtes_speichern(p, wurzel)

    monkeypatch.setattr(flaechenmodul.projekt, "speichere", dazwischen)
    f._skizze({"ordner": str(glb_mappe),
               "png_base64": _b64.b64encode(png).decode()})

    nutzlast, _ = antwort.daten
    assert "fehler" not in nutzlast, nutzlast
    danach = projekt.oeffne(glb_mappe)["projekt"]
    assert len(danach["skizzen"]) == 1, "die Zeichnung steht in der Mappe"
    assert danach["einstellungen"]["prompt"] == "von der HomeStation", (
        "und die Arbeit des anderen steht auch noch da")


def test_eine_einstellung_wird_bei_einer_kollision_nicht_wiederholt(flaechenmodul,
                                                                    glb_mappe, monkeypatch):
    """**Was ersetzt, muss fragen.**

    Eine Einstellung auf dem neuen Stand zu wiederholen hiesse, die Einstellung des
    anderen wegzuwerfen — genau das, wovor diese Sperre schützt. Also: melden.
    """
    f, antwort = _flaeche(flaechenmodul, glb_mappe)

    echtes_speichern = projekt.speichere
    zustand = {"erstes_mal": True}

    def dazwischen(p, wurzel):
        if zustand["erstes_mal"]:
            zustand["erstes_mal"] = False
            _drueben_schreibt(_Path(wurzel), "von der HomeStation", echtes_speichern)
        return echtes_speichern(p, wurzel)

    monkeypatch.setattr(flaechenmodul.projekt, "speichere", dazwischen)
    f._einstellungen({"ordner": str(glb_mappe),
                      "einstellungen": {"prompt": "vom iPad"}})

    nutzlast, code = antwort.daten
    assert "fehler" in nutzlast, nutzlast
    assert "neu laden" in nutzlast["fehler"]
    assert code == 400
    assert projekt.oeffne(glb_mappe)["projekt"]["einstellungen"]["prompt"] == (
        "von der HomeStation"), "die Einstellung des anderen bleibt stehen"
