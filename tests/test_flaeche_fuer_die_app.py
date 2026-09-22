"""Die Fläche für die App — **über echte Anfragen geprüft** (Einheit D-SERVER, 22.09.2026).

Die Bibliothek kann seit dem 22.09.2026 benennen, abbrechen, Entwürfe, Varianten und
Skizzen rechnen (``tests/test_mappe_fuer_die_app.py``). Hier wird geprüft, dass die
**Leitung** es auch kann: Jede Probe schickt eine ganze Anfrage durch ``do_GET``/``do_POST``
(Muster ``_Anfrage`` aus ``tests/test_oberflaeche.py``), und gerechnet wird über die
**echte** Bibliothek — nur die Knoten selbst sind Attrappen, eingehängt an
``arbeitsgang.rechne``/``rechne_skizze``, weil die Fläche selbst nie eine Attrappe
weiterreicht (``test_die_flaeche_setzt_keine_attrappen_ein``).

1. **Die Koppelseite** (Entscheid 26): ohne Kennwort, nur bei geltender Zahl, und nichts
   sonst.
2. **Skizzen**: eindeutige Namen (Befund: die zweite Skizze einer Sekunde überschrieb die
   erste still) und der Schlüssel gegen Doppelsendung.
3. **Die neuen Wege**: benennen, abbrechen, Skizze rechnen lassen, Entwurf, Varianten.
4. **Das Bild in der Sicht** trägt Zahl, Titel, Entwurf, Gruppe, Hinweise — mit der
   dritten Antwort, wo nichts gemessen ist.
5. **Die Zahl im Prüfzeichen** wird auf der Seite nie auf Gleichstand gerundet (mit
   ``node`` gefahren, wenn es da ist).

Ohne GPU, ohne Blender, ohne Netz. Regel 3: alle Dateien entstehen hier aus ein paar Bytes.
"""
from __future__ import annotations

import base64
import io
import json
import re
import shutil
import struct
import subprocess
import sys
import threading
import time
import zlib
from pathlib import Path

import pytest

from aiimaging import arbeitsgang, kette, kopplung, projekt
from aiimaging.kette import (ART_BILDQUELLE, ART_GEOMETRIE, ART_MULTIPASS, ART_NACHRENDER,
                             ART_QA, ART_RENDER)

WURZEL = Path(__file__).resolve().parents[1]
FLAECHE = WURZEL / "oberflaeche"
SEITE = FLAECHE / "seite.html"


@pytest.fixture(scope="module")
def server():
    sys.path.insert(0, str(FLAECHE))
    try:
        import server as modul
        return modul
    finally:
        sys.path.remove(str(FLAECHE))


@pytest.fixture(autouse=True)
def eigener_laufstand(server, monkeypatch):
    """Jede Probe bekommt ihren eigenen Laufstand und ihr eigenes Eingangsbuch — und am
    Ende wird gewartet, bis ihr Lauf wirklich fertig ist. Ein Faden, der in die nächste
    Probe hineinläuft, machte deren Befund zu einem Zufall."""
    monkeypatch.setattr(server, "LAUFSTAND", server.Laufstand())
    monkeypatch.setattr(server, "EINGANG", server.Eingangsbuch())
    yield
    _warte(server)


def _warte(server, frist_s: float = 20.0) -> dict:
    ende = time.monotonic() + frist_s
    while time.monotonic() < ende:
        sicht = server.LAUFSTAND.sicht()
        if not sicht["laeuft"]:
            return sicht
        time.sleep(0.02)
    raise AssertionError("Der Lauf ist nicht fertig geworden")


# ======================================================================================
# Werkzeug
# ======================================================================================

def _png_bytes(werte=(0, 64, 128, 255)) -> bytes:
    """Ein gültiges 2x2-Graustufen-PNG — echt, weil die Bildquelle es liest."""
    roh = b"".join(b"\x00" + bytes(werte[z * 2:(z + 1) * 2]) for z in range(2))

    def block(art, nutz):
        return (struct.pack(">I", len(nutz)) + art + nutz
                + struct.pack(">I", zlib.crc32(art + nutz) & 0xFFFFFFFF))

    return (b"\x89PNG\r\n\x1a\n"
            + block(b"IHDR", struct.pack(">IIBBBBB", 2, 2, 8, 0, 0, 0, 0))
            + block(b"IDAT", zlib.compress(roh)) + block(b"IEND", b""))


def _png(pfad, werte=(0, 64, 128, 255)) -> Path:
    pfad = Path(pfad)
    pfad.parent.mkdir(parents=True, exist_ok=True)
    pfad.write_bytes(_png_bytes(werte))
    return pfad


class _Anfrage:
    """Eine ganze Anfrage an ``Flaeche`` — ``do_GET``/``do_POST`` laufen wirklich.

    Dieselbe Bauform wie in ``tests/test_oberflaeche.py``; sie steht hier ein weiteres
    Mal, weil Probedateien einander nicht importieren.
    """

    def __init__(self, modul, *, befehl, weg, kennwort="geheim", angemeldet=True,
                 offen=None, rumpf=None, ordner=None):
        if isinstance(rumpf, dict):
            rumpf = json.dumps(rumpf).encode("utf-8")
        rumpf = b"" if rumpf is None else rumpf
        klasse = type("FlaechePruefling", (modul.Flaeche,),
                      {"kennwort": kennwort, "ordner": ordner, "kopplung_offen": offen})
        kopf = None
        if angemeldet and kennwort:
            kopf = "Basic " + base64.b64encode(
                f"{modul.BENUTZER}:{kennwort}".encode()).decode()
        self.selbst = klasse.__new__(klasse)
        self.selbst.command = befehl
        self.selbst.path = weg
        self.selbst.headers = {"Authorization": kopf, "Content-Length": str(len(rumpf))}
        self.selbst.rfile = io.BytesIO(rumpf)
        self.selbst.wfile = io.BytesIO()
        self.codes: list[int] = []
        self.koepfe: list[tuple[str, str]] = []
        self.selbst.send_response = lambda code, *a, **k: self.codes.append(code)
        self.selbst.send_header = lambda name, wert: self.koepfe.append((name, wert))
        self.selbst.end_headers = lambda: None

    def stelle(self) -> "_Anfrage":
        (self.selbst.do_GET if self.selbst.command == "GET" else self.selbst.do_POST)()
        return self

    @property
    def text(self) -> str:
        return self.selbst.wfile.getvalue().decode("utf-8", "replace")

    @property
    def daten(self) -> dict:
        return json.loads(self.text)


def _post(server, weg, rumpf, **kw):
    return _Anfrage(server, befehl="POST", weg=weg, rumpf=rumpf, **kw).stelle()


def _get(server, weg, **kw):
    return _Anfrage(server, befehl="GET", weg=weg, **kw).stelle()


class _Werkbank:
    """Attrappen für die vier Stufen der Standardkette — sie schreiben echte Dateien."""

    def __init__(self, *, geometrie_wartet: threading.Event | None = None):
        self.render_schritte: list[int] = []
        self.render_seeds: list[int] = []
        self.qa_aufrufe = 0
        self.warten = geometrie_wartet
        self.geometrie_begonnen = threading.Event()

    def geometrie(self, *, knoten, eingaben, out_dir):
        self.geometrie_begonnen.set()
        if self.warten is not None:
            assert self.warten.wait(15), "die Probe hat die Geometrie nie freigegeben"
        glb = Path(out_dir) / "modell.glb"
        glb.write_text("glb", encoding="utf-8")
        return {"glb_path": str(glb), "up_axis": "Y", "bbox": [[0, 0, 0], [8.0, 5.0, 3.25]]}

    def multipass(self, *, knoten, eingaben, out_dir):
        return {"status": "ok", "depth_png": str(_png(Path(out_dir) / "tiefe_norm.png")),
                "beauty_png": str(_png(Path(out_dir) / "beauty.png", (5, 5, 5, 5)))}

    def render(self, *, knoten, eingaben, out_dir):
        self.render_schritte.append(knoten.params["schritte"])
        self.render_seeds.append(knoten.params["seed"])
        s = knoten.params["seed"] % 250
        return {"status": "ok", "bild_png": str(_png(Path(out_dir) / "bild.png", (s, s, 1, 2)))}

    def qa(self, *, knoten, eingaben, out_dir):
        self.qa_aufrufe += 1
        return {"status": "ok", "bestanden": True, "score": 0.8123,
                "schwelle": knoten.params["schwelle"], "begruendung": "Attrappe."}

    def tabelle(self) -> dict:
        return {ART_GEOMETRIE: self.geometrie, ART_MULTIPASS: self.multipass,
                ART_RENDER: self.render, ART_QA: self.qa}


class _Modell:
    """Ein Bildmodell, das nichts rechnet — es hält nur fest, welcher Prompt ankam."""

    def __init__(self):
        self.prompts: list[str] = []

    def __call__(self, parameter: dict) -> dict:
        self.prompts.append(parameter["prompt"])
        _png(parameter["ausgabe_png"], (10, 20, 30, 40))
        return {"bild_png": parameter["ausgabe_png"], "hinweise": [],
                "schritte_gerechnet": None}


def _haenge_ein(monkeypatch, werk: _Werkbank, modell: _Modell | None = None) -> None:
    """Die Attrappen an der Bibliothek einhängen — **nicht** an der Fläche.

    Die Fläche ruft ``arbeitsgang.rechne``/``rechne_skizze`` ohne Ausführertafel (echte
    Werkzeuge). Hier bekommt die Bibliothek für die Dauer der Probe eine Tafel mit — alles
    andere (Sperre, Plan, Vermerk, Mappe, Laufstand) läuft echt.
    """
    echt_rechne, echt_skizze = arbeitsgang.rechne, arbeitsgang.rechne_skizze
    tafel = werk.tabelle()

    def verboten(**_):
        raise AssertionError("ein Skizzenlauf rechnet das Bild aus dem Modell nicht")

    skizzentafel = {**tafel, ART_RENDER: verboten,
                    ART_BILDQUELLE: kette.AUSFUEHRER[ART_BILDQUELLE],
                    ART_NACHRENDER: kette.nachrender_ausfuehrer(modell=modell or _Modell()),
                    ART_QA: kette.qa_ausfuehrer()}
    monkeypatch.setattr(arbeitsgang, "rechne",
                        lambda *a, **k: echt_rechne(*a, ausfuehrer=tafel, **k))
    monkeypatch.setattr(arbeitsgang, "rechne_skizze",
                        lambda *a, **k: echt_skizze(*a, ausfuehrer=skizzentafel, **k))


@pytest.fixture
def mappe(tmp_path):
    """Eine Mappe mit durchgereichter glb — ohne jeden Subprozess."""
    js = json.dumps({"asset": {"version": "2.0", "generator": "Testfixture"}}).encode()
    js += b" " * (-len(js) % 4)
    block = struct.pack("<II", len(js), 0x4E4F534A) + js
    glb = tmp_path / "quelle" / "haus.glb"
    glb.parent.mkdir(parents=True, exist_ok=True)
    glb.write_bytes(struct.pack("<4sII", b"glTF", 2, 12 + len(block)) + block)
    wurzel = tmp_path / "projekt"
    arbeitsgang.lege_an(wurzel, glb, name="Probehaus",
                        einstellungen={"prompt": "Abendlicht", "seed": 7, "up_axis": "Y"})
    return wurzel


def _mappe(wurzel) -> dict:
    return projekt.oeffne(wurzel)["projekt"]


def _sicht(server, wurzel) -> dict:
    a = _get(server, "/api/projekt?ordner=" + str(wurzel))
    assert a.codes == [200], a.text
    return a.daten


def _skizze_schicken(server, wurzel, **mehr) -> _Anfrage:
    rumpf = {"ordner": str(wurzel),
             "png_base64": base64.b64encode(mehr.pop("png", _png_bytes())).decode(), **mehr}
    return _post(server, server.WEG_SKIZZE, rumpf)


# ======================================================================================
# 1 · Die Koppelseite (Entscheid 26)
# ======================================================================================

def test_ohne_offene_kopplung_bleibt_die_koppelseite_zu(server):
    """**Die Tür bleibt zu, wenn niemand koppelt.** Unangemeldet 401, und nichts geht mit."""
    a = _get(server, server.WEG_KOPPELN, angemeldet=False, offen=None)
    assert a.codes == [401]
    assert "<html" not in a.text.lower()
    assert a.daten.keys() == {"fehler"}


def test_angemeldet_ohne_offene_kopplung_gibt_es_nichts_zu_koppeln(server):
    """404 mit Satz, keine Seite: Ein Zahlenfeld, in das keine Zahl passt, wäre ein
    Bedienelement ohne Wirkung."""
    a = _get(server, server.WEG_KOPPELN, offen=None)
    assert a.codes == [404]
    assert "kein Verbinden offen" in a.daten["fehler"]


def test_eine_verbrauchte_zahl_oeffnet_die_koppelseite_nicht_mehr(server):
    offen = kopplung.eroeffne(_pin="123456")
    kopplung.schliesse(offen)
    a = _get(server, server.WEG_KOPPELN, angemeldet=False, offen=offen)
    assert a.codes == [401]
    assert "<html" not in a.text.lower()


def test_mit_offener_kopplung_kommt_genau_die_koppelseite(server):
    """Ohne Kennwort, weil die Zahl gilt — und die Seite ist ein Zahlenfeld, das
    ``POST /api/verbinden`` ruft. Nicht mehr: kein Projekt, kein Pfad, kein Nachladen."""
    offen = kopplung.eroeffne(_pin="123456")
    a = _get(server, server.WEG_KOPPELN + "?egal=1", angemeldet=False, offen=offen,
             ordner="/geheimer/projektordner")
    assert a.codes == [200]
    assert ("Content-Type", "text/html; charset=utf-8") in a.koepfe
    assert ("Cache-Control", "no-store") in a.koepfe
    seite = a.text
    assert 'fetch("/api/verbinden"' in seite
    assert 'inputmode="numeric"' in seite
    assert "geheimer" not in seite, "die Seite vor der Tür nennt nichts aus dem Projekt"
    for muster in ("http://", "https://", "src=", "<link"):
        assert muster not in seite, f"die Koppelseite lädt etwas nach: {muster!r}"


@pytest.mark.parametrize("befehl,weg", [
    ("GET", "/"), ("GET", "/index.html"), ("GET", "/api/projekt"), ("GET", "/api/fortschritt"),
    ("GET", "/bild?name=a.png"), ("GET", "/koppeln/"), ("GET", "/koppeln/../"),
    ("GET", "/api/verbinden"), ("POST", "/koppeln"), ("POST", "/api/benennen"),
    ("POST", "/api/abbrechen"), ("POST", "/api/rechne-skizze"), ("POST", "/api/skizze"),
])
def test_mit_offener_kopplung_bleibt_alles_andere_hinter_der_tuer(server, befehl, weg):
    """**Und nichts sonst.** Die Öffnung ist genau ein Pfad mit genau einer Methode."""
    offen = kopplung.eroeffne(_pin="123456")
    a = _Anfrage(server, befehl=befehl, weg=weg, angemeldet=False, offen=offen,
                 rumpf=b"{}").stelle()
    assert a.codes == [401], (befehl, weg, a.codes)


def test_die_koppelseite_fuehrt_wirklich_zum_kennwort(server):
    """Der Weg, den der Browser geht: Seite holen (ohne Kennwort), die Zahl an den Weg
    schicken, den die Seite nennt (ohne Kennwort) — und das Kennwort kommt zurück."""
    offen = kopplung.eroeffne(_pin="654321")
    seite = _get(server, server.WEG_KOPPELN, angemeldet=False, offen=offen,
                 kennwort="das-lange-kennwort").text
    ziel = re.search(r'fetch\("([^"]+)"', seite).group(1)
    a = _post(server, ziel, {"pin": "654321"}, angemeldet=False, offen=offen,
              kennwort="das-lange-kennwort")
    assert a.codes == [200]
    assert a.daten["kennwort"] == "das-lange-kennwort"
    # UND DANACH IST DIE SEITE WEG: Die Zahl ist verbraucht.
    assert _get(server, server.WEG_KOPPELN, angemeldet=False, offen=offen,
                kennwort="das-lange-kennwort").codes == [401]


# ======================================================================================
# 2 · Skizzen: eindeutige Namen und der Schlüssel gegen Doppelsendung
# ======================================================================================

def test_zwei_skizzen_in_derselben_sekunde_ueberschreiben_sich_nicht(server, mappe,
                                                                     monkeypatch):
    """**Der Befund:** Bis zum 22.09.2026 hiess jede Skizze einer Sekunde gleich, und die
    zweite überschrieb die erste still. Die Uhr steht hier still — beide kommen in
    derselben Sekunde an."""
    monkeypatch.setattr(server, "_stempel", lambda: "20260922-120000")
    erste = _skizze_schicken(server, mappe, png=_png_bytes((1, 1, 1, 1)))
    zweite = _skizze_schicken(server, mappe, png=_png_bytes((2, 2, 2, 2)))

    assert erste.codes == [200] and zweite.codes == [200], (erste.text, zweite.text)
    a, b = erste.daten["skizze"], zweite.daten["skizze"]
    assert a != b
    assert (mappe / a).read_bytes() == _png_bytes((1, 1, 1, 1)), "die erste ist unberührt"
    assert (mappe / b).read_bytes() == _png_bytes((2, 2, 2, 2))
    assert [s["skizze"] for s in _mappe(mappe)["skizzen"]] == [a, b]


def test_eine_datei_die_die_mappe_nicht_kennt_wird_auch_nicht_ueberschrieben(
        server, mappe, monkeypatch):
    """Die Mappe ist nicht die einzige Quelle: Eine Datei kann auf der Platte liegen,
    ohne in der Mappe zu stehen. Das Schreiben selbst legt nur **neu** an."""
    monkeypatch.setattr(server, "_stempel", lambda: "20260922-120000")
    fremd = mappe / "skizze-20260922-120000.png"
    fremd.write_bytes(b"liegt schon da")

    a = _skizze_schicken(server, mappe)

    assert a.codes == [200], a.text
    assert a.daten["skizze"] != fremd.name
    assert fremd.read_bytes() == b"liegt schon da"


def test_ein_name_den_die_mappe_noch_nennt_wird_nicht_neu_vergeben(server, mappe,
                                                                     monkeypatch):
    """Die Gegenrichtung: Die Datei ist weg, die Mappe nennt sie weiter. Ein neuer Name,
    der mit ihr zusammenfiele, stünde zweimal in der Mappe — und eine Skizze, die zweimal
    dasteht, rechnet die Bibliothek nicht (die Wahl wäre geraten)."""
    monkeypatch.setattr(server, "_stempel", lambda: "20260922-120000")
    p = _mappe(mappe)
    projekt.vermerke_skizze(p, skizze="skizze-20260922-120000.png", bemerkung="Datei weg")
    projekt.speichere(p, mappe)

    a = _skizze_schicken(server, mappe)

    assert a.codes == [200], a.text
    assert a.daten["skizze"] != "skizze-20260922-120000.png"
    namen = [s["skizze"] for s in _mappe(mappe)["skizzen"]]
    assert len(namen) == len(set(namen)) == 2


def test_derselbe_schluessel_zweimal_gibt_dieselbe_antwort_und_keine_zweite_datei(
        server, mappe):
    """**Das Parkfach der App schickt nach einem Abriss noch einmal.** Drüben liegt die
    Skizze dann schon — und darf nicht ein zweites Mal liegen."""
    schluessel = "8f14e45f-ceea-467a-9575-0a1b2c3d4e5f"
    erste = _skizze_schicken(server, mappe, schluessel=schluessel)
    zweite = _skizze_schicken(server, mappe, schluessel=schluessel)

    assert erste.codes == [200] and zweite.codes == [200]
    assert zweite.daten == erste.daten, "dieselbe Antwort"
    assert erste.daten["schluessel"] == schluessel
    assert len(_mappe(mappe)["skizzen"]) == 1
    assert len(list(mappe.glob("skizze-*.png"))) == 1


def test_ohne_schluessel_bleibt_es_bei_zwei_dateien(server, mappe):
    """Die Gegenprobe: Ohne Schlüssel weiss niemand, dass es dieselbe ist."""
    _skizze_schicken(server, mappe)
    _skizze_schicken(server, mappe)
    assert len(_mappe(mappe)["skizzen"]) == 2


def test_derselbe_schluessel_mit_einer_anderen_zeichnung_wird_abgewiesen(server, mappe):
    """Als Wiederholung behandelt, ginge die zweite Zeichnung still verloren."""
    schluessel = "schluessel-aus-der-probe-1"
    _skizze_schicken(server, mappe, schluessel=schluessel, png=_png_bytes((1, 1, 1, 1)))
    a = _skizze_schicken(server, mappe, schluessel=schluessel, png=_png_bytes((9, 9, 9, 9)))

    assert a.codes == [400]
    assert "ANDEREN Zeichnung" in a.daten["fehler"]
    assert len(_mappe(mappe)["skizzen"]) == 1


@pytest.mark.parametrize("schluessel", ["kurz", "../../etc", "a" * 129, 12345678, ""])
def test_ein_unbrauchbarer_schluessel_wird_abgewiesen_und_nichts_geschrieben(
        server, mappe, schluessel):
    a = _skizze_schicken(server, mappe, schluessel=schluessel)
    assert a.codes == [400], a.text
    assert "Schlüssel" in a.daten["fehler"]
    assert _mappe(mappe).get("skizzen", []) == []
    assert list(mappe.glob("skizze-*.png")) == []


def test_eine_gescheiterte_ablage_merkt_sich_den_schluessel_nicht(server, tmp_path):
    """Scheitert das Ablegen (hier: kein Projekt), darf die Wiederholung es noch einmal
    versuchen — sonst bekäme sie eine Absage, die nicht mehr stimmt."""
    leer = tmp_path / "kein-projekt"
    leer.mkdir()
    a = _skizze_schicken(server, leer, schluessel="schluessel-aus-der-probe-2")
    assert a.codes == [400]
    assert server.EINGANG.nachsehen(leer, "schluessel-aus-der-probe-2") is None


# ======================================================================================
# 3 · Die neuen Wege
# ======================================================================================

def _rechne_und_warte(server, wurzel, **mehr) -> dict:
    a = _post(server, server.WEG_RECHNE, {"ordner": str(wurzel), **mehr})
    assert a.codes == [200], a.text
    return {"antwort": a.daten, "stand": _warte(server)}


def test_umbenennen_ueber_die_leitung(server, mappe, monkeypatch):
    _haenge_ein(monkeypatch, _Werkbank())
    _rechne_und_warte(server, mappe)
    sicht = _sicht(server, mappe)
    (bild,) = sicht["bilder"]
    assert bild["titel"] is None

    a = _post(server, server.WEG_BENENNEN, {"ordner": str(mappe), "bild": bild["bild"],
                                            "titel": "Südansicht", "von_stand": sicht["stand_nr"]})

    assert a.codes == [200], a.text
    assert a.daten["eintrag"]["titel"] == "Südansicht"
    danach = _sicht(server, mappe)
    assert danach["bilder"][0]["titel"] == "Südansicht"
    assert danach["bilder"][0]["bild"] == bild["bild"], "die Datei heisst weiter wie vorher"
    assert danach["stand_nr"] == sicht["stand_nr"] + 1


def test_umbenennen_von_einem_alten_stand_wird_abgewiesen(server, mappe, monkeypatch):
    """*Was ersetzt, muss fragen.* Wer einen alten Stand vor Augen hatte, überschreibt
    nicht den Namen, den inzwischen jemand anderes gegeben hat."""
    _haenge_ein(monkeypatch, _Werkbank())
    _rechne_und_warte(server, mappe)
    alt = _sicht(server, mappe)
    name = alt["bilder"][0]["bild"]
    projekt.benenne(mappe, bild=name, titel="Von drüben")

    a = _post(server, server.WEG_BENENNEN, {"ordner": str(mappe), "bild": name,
                                            "titel": "Von hier", "von_stand": alt["stand_nr"]})

    assert a.codes == [400]
    assert "neu laden" in a.daten["fehler"]
    assert _sicht(server, mappe)["bilder"][0]["titel"] == "Von drüben"


def test_ohne_titelfeld_wird_nichts_geloescht(server, mappe, monkeypatch):
    """Ein fehlendes Feld ist kein «zurücknehmen» — sonst löschte ein vergessenes Feld
    einen Namen."""
    _haenge_ein(monkeypatch, _Werkbank())
    _rechne_und_warte(server, mappe)
    name = _sicht(server, mappe)["bilder"][0]["bild"]
    projekt.benenne(mappe, bild=name, titel="Favorit")
    stand = _mappe(mappe)["stand_nr"]

    a = _post(server, server.WEG_BENENNEN, {"ordner": str(mappe), "bild": name})

    assert a.codes == [400]
    assert _mappe(mappe)["stand_nr"] == stand
    assert _sicht(server, mappe)["bilder"][0]["titel"] == "Favorit"
    # UND MIT null WIRD ER WIRKLICH ZURUECKGENOMMEN.
    assert _post(server, server.WEG_BENENNEN,
                 {"ordner": str(mappe), "bild": name, "titel": None}).codes == [200]
    assert _sicht(server, mappe)["bilder"][0]["titel"] is None


def test_eine_skizze_bekommt_ueber_die_leitung_einen_namen(server, mappe):
    name = _skizze_schicken(server, mappe).daten["skizze"]
    a = _post(server, server.WEG_BENENNEN, {"ordner": str(mappe), "skizze": name,
                                            "titel": "Erste Idee"})
    assert a.codes == [200], a.text
    assert _sicht(server, mappe)["skizzen"][0]["titel"] == "Erste Idee"


def test_abbrechen_ohne_lauf_sagt_dass_nichts_laeuft(server):
    a = _post(server, server.WEG_ABBRECHEN, {})
    assert a.codes == [400]
    assert "kein Lauf" in a.daten["fehler"]


def test_abbrechen_haelt_den_lauf_zwischen_zwei_knoten_an(server, mappe, monkeypatch):
    """**Entscheid 31 über die Leitung.** Der erste Knoten rechnet, während der Abbruch
    verlangt wird; er rechnet zu Ende, danach beginnt keiner mehr. Das Zeichen muss die
    Bibliothek wirklich erreichen — gefragt wird es in ``kette.fuehre_aus``."""
    weiter = threading.Event()
    werk = _Werkbank(geometrie_wartet=weiter)
    _haenge_ein(monkeypatch, werk)

    start = _post(server, server.WEG_RECHNE, {"ordner": str(mappe)})
    assert start.codes == [200], start.text
    assert werk.geometrie_begonnen.wait(10)

    a = _post(server, server.WEG_ABBRECHEN, {})
    assert a.codes == [200], a.text
    assert a.daten["abbruch_verlangt"] is True
    assert server.LAUFSTAND.sicht()["abbruch_verlangt"] is True
    weiter.set()
    stand = _warte(server)

    assert stand["ergebnis"]["abgebrochen"] is True, stand
    assert werk.render_schritte == [], "nach dem Abbruch hat keine Bildstufe mehr begonnen"
    abgebrochen = [k for k in stand["fertige"] if k["status"] == kette.STATUS_ABGEBROCHEN]
    assert [k["knoten"] for k in abgebrochen] == [kette.KNOTEN_MULTIPASS,
                                                  kette.KNOTEN_RENDER, kette.KNOTEN_QA]
    lauf = _mappe(mappe)["laeufe"][-1]
    assert lauf["abgebrochen"] is True


def test_ein_abbruch_nach_dem_letzten_knoten_ist_kein_abbruch(server, mappe, monkeypatch):
    """**Verlangt ist nicht gewirkt.** Der Abbruch kommt, als der letzte Knoten schon
    fertig ist — danach fragt niemand mehr. Das Zeichen steht, aber der Lauf lief
    regulär zu Ende, und genau so muss es im Ergebnis stehen."""

    class _ZuSpaet(server.Laufstand):
        def melde(self, ereignis):
            super().melde(ereignis)
            if (ereignis.get("art") == "knoten_fertig"
                    and ereignis.get("knoten") == kette.KNOTEN_QA):
                assert self.verlange_abbruch() is True

    monkeypatch.setattr(server, "LAUFSTAND", _ZuSpaet())
    werk = _Werkbank()
    _haenge_ein(monkeypatch, werk)
    stand = _rechne_und_warte(server, mappe)["stand"]

    assert stand["abbruch_verlangt"] is True
    assert stand["ergebnis"]["abgebrochen"] is False
    assert werk.qa_aufrufe == 1 and len(_sicht(server, mappe)["bilder"]) == 1


def test_entwurf_mit_drei_startwerten_ueber_die_leitung(server, mappe, monkeypatch):
    """Entscheide 30 und 32 zusammen: drei Bilder, jedes ein Entwurf (blaues Zeichen,
    nicht gemessen, höchstens acht Schritte, keine Prüfung), alle in einer Reihe."""
    werk = _Werkbank()
    _haenge_ein(monkeypatch, werk)

    r = _rechne_und_warte(server, mappe, entwurf=True, varianten=3)

    assert r["antwort"]["schritte_gesamt"] == arbeitsgang.ENTWURF_SCHRITTE
    assert werk.render_schritte == [arbeitsgang.ENTWURF_SCHRITTE] * 3
    assert werk.render_seeds == [7, 8, 9]
    assert werk.qa_aufrufe == 0, "ein Entwurf wird nicht geprüft"
    bilder = _sicht(server, mappe)["bilder"]
    assert len(bilder) == 3
    for b in bilder:
        assert b["entwurf"] is True
        assert b["zeichen"] == "nicht-gemessen", "ein Entwurf ist nie «bestanden»"
        assert b["satz"].startswith(arbeitsgang.ENTWURF_VERMERK)
        assert b["score"] is None and b["schwelle"] is None
    gruppen = [b["variantengruppe"] for b in bilder]
    assert len({g["id"] for g in gruppen}) == 1
    assert [g["nummer"] for g in gruppen] == [1, 2, 3]
    assert {g["art"] for g in gruppen} == {arbeitsgang.VARIANTEN_STARTWERTE}


def test_das_gepruefte_bild_traegt_seine_zahl_in_der_sicht(server, mappe, monkeypatch):
    """Entscheid 16: Farbe, Wort **und Zahl** — aus der Prüfung, bis in die Sicht."""
    _haenge_ein(monkeypatch, _Werkbank())
    _rechne_und_warte(server, mappe, einstellungen={"qa_schwelle": 0.7})
    (b,) = _sicht(server, mappe)["bilder"]
    assert b["zeichen"] == "bestanden"
    assert b["score"] == pytest.approx(0.8123)
    assert b["schwelle"] == pytest.approx(0.7)
    assert b["entwurf"] is False
    assert b["variantengruppe"] is None


def test_zwei_skizzen_als_ebenen_rechnen_lassen(server, mappe, monkeypatch):
    """Der ganze Weg der Warteschlange: ablegen über ``/api/skizze``, rechnen lassen über
    ``/api/rechne-skizze`` als Ebenen-Reihe — und am Bild in der Sicht steht, dass die
    Skizze beim Vorgabemodell **nicht ankam** (Befund ``auf-20260919-123``)."""
    modell = _Modell()
    _haenge_ein(monkeypatch, _Werkbank(), modell)
    a = _skizze_schicken(server, mappe, bemerkung="ein Vordach").daten["skizze"]
    b = _skizze_schicken(server, mappe, bemerkung="ein Erker").daten["skizze"]

    start = _post(server, server.WEG_RECHNE_SKIZZE,
                  {"ordner": str(mappe), "skizze": [a, b], "entwurf": True})
    assert start.codes == [200], start.text
    assert start.daten["skizzen"] == [a, b]
    stand = _warte(server)
    assert stand["fehler"] is None, stand["fehler"]
    assert stand["bestellung"]["art"] == "skizze"

    assert modell.prompts == ["ein Vordach", "ein Erker"]
    sicht = _sicht(server, mappe)
    assert {s["stand"] for s in sicht["skizzen"]} == {projekt.SKIZZE_GERECHNET}
    bilder = sicht["bilder"]
    assert [x["herkunft"]["skizze"] for x in bilder] == [a, b]
    assert {x["variantengruppe"]["art"] for x in bilder} == {arbeitsgang.VARIANTEN_EBENEN}
    for x in bilder:
        assert x["entwurf"] is True
        assert x["skizze_nicht_angekommen"] is True
        assert x["skizze_hinweis"].startswith(
            kette.HINWEIS_SKIZZE_NICHT_ANGEKOMMEN.split(":")[0])
        assert x["skizze_hinweis"] in x["hinweise"]


def test_eine_einzelne_skizze_mit_eigener_anweisung(server, mappe, monkeypatch):
    modell = _Modell()
    _haenge_ein(monkeypatch, _Werkbank(), modell)
    name = _skizze_schicken(server, mappe, bemerkung="Bemerkung").daten["skizze"]

    start = _post(server, server.WEG_RECHNE_SKIZZE,
                  {"ordner": str(mappe), "skizze": name, "anweisung": "ein Vordach"})
    assert start.codes == [200], start.text
    assert _warte(server)["fehler"] is None
    assert modell.prompts == ["ein Vordach"]
    (bild,) = _sicht(server, mappe)["bilder"]
    assert bild["herkunft"]["anweisung"] == "ein Vordach"
    assert bild["variantengruppe"] is None


def test_was_die_bibliothek_an_der_skizze_abweist_steht_im_laufstand(server, mappe,
                                                                      monkeypatch):
    """Geprüft wird unter der Laufsperre, in der Bibliothek — die Fläche reicht den Satz
    durch, statt eine zweite Regel zu führen."""
    _haenge_ein(monkeypatch, _Werkbank())
    start = _post(server, server.WEG_RECHNE_SKIZZE,
                  {"ordner": str(mappe), "skizze": "skizze-gibt-es-nicht.png"})
    assert start.codes == [200]
    stand = _warte(server)
    assert stand["fehler"] and "skizze-gibt-es-nicht.png" in stand["fehler"]
    assert not stand["fehler"].startswith("ArbeitsgangError"), "ohne Typnamen"


@pytest.mark.parametrize("weg,rumpf,satz", [
    ("/api/rechne", {"entwurf": "ja"}, "wahr oder falsch"),
    ("/api/rechne", {"trotz_aenderung": 1}, "wahr oder falsch"),
    ("/api/rechne", {"varianten": 9}, "2 bis"),
    ("/api/rechne", {"varianten": 1}, "2 bis"),
    ("/api/rechne", {"varianten": True}, "ganze Zahl"),
    ("/api/rechne", {"einstellungen": {"ausfuehrer": {}}}, "kennt das Programm nicht"),
    ("/api/rechne", {"einstellungen": {"cache": None}}, "kennt das Programm nicht"),
    ("/api/rechne", {"einstellungen": ["prompt"]}, "Objekt"),
    ("/api/rechne-skizze", {}, "nicht gesagt"),
    ("/api/rechne-skizze", {"skizze": ["a.png"] * 9}, "2 bis"),
    ("/api/rechne-skizze", {"skizze": [1, 2]}, "Dateiname"),
    ("/api/rechne-skizze", {"skizze": "a.png", "varianten": 3}, "Ebenen"),
    ("/api/rechne-skizze", {"skizze": "a.png", "anweisung": 5}, "Text"),
    ("/api/rechne-skizze", {"skizze": "a.png", "entwurf": "ja"}, "wahr oder falsch"),
])
def test_eine_falsch_geformte_bestellung_startet_keinen_lauf(server, mappe, weg, rumpf, satz):
    """**Die Form wird an der Leitung geprüft, der Inhalt in der Bibliothek.** Was die
    Leitung verfälschen kann (``"ja"`` ist für Python wahr), und was von aussen nie in
    die Bibliothek darf (Ausführer, Speicher), wird abgewiesen, bevor ein Faden startet."""
    a = _post(server, weg, {"ordner": str(mappe), **rumpf})
    assert a.codes == [400], a.text
    assert satz in a.daten["fehler"]
    sicht = server.LAUFSTAND.sicht()
    assert sicht["laeuft"] is False and sicht["ergebnis"] is None and sicht["fehler"] is None


def test_waehrend_eines_laufs_startet_keine_skizze(server, mappe, monkeypatch):
    weiter = threading.Event()
    werk = _Werkbank(geometrie_wartet=weiter)
    _haenge_ein(monkeypatch, werk)
    assert _post(server, server.WEG_RECHNE, {"ordner": str(mappe)}).codes == [200]
    assert werk.geometrie_begonnen.wait(10)
    try:
        a = _post(server, server.WEG_RECHNE_SKIZZE, {"ordner": str(mappe), "skizze": "x.png"})
        assert a.codes == [400]
        assert "läuft schon einer" in a.daten["fehler"]
    finally:
        weiter.set()


# ======================================================================================
# 4 · Das Bild in der Sicht — und die dritte Antwort
# ======================================================================================

def test_ein_alter_eintrag_ohne_die_neuen_felder_heisst_nicht_gemessen(server):
    """Ältere Einträge führen Score, Entwurf, Gruppe und Messung nicht. Ihr Fehlen heisst
    **nicht gemessen** — nie 0, nie «kein Entwurf», nie «keine Hinweise»."""
    d = server._bild_fuer_die_flaeche({"bild": "a.png", "schicht": "geometrielayer",
                                       "geometrie_bestanden": None, "herkunft": {}})
    for feld in ("score", "schwelle", "titel", "entwurf", "variantengruppe", "hinweise",
                 "skizze_nicht_angekommen", "skizze_hinweis"):
        assert d[feld] is None, feld


@pytest.mark.parametrize("wert", [True, "0.8", float("nan"), float("inf")])
def test_was_keine_endliche_zahl_ist_wird_keine(server, wert):
    d = server._bild_fuer_die_flaeche({"bild": "a.png", "score": wert, "schwelle": wert,
                                       "herkunft": {}})
    assert d["score"] is None and d["schwelle"] is None


def test_skizze_nicht_angekommen_hat_drei_antworten(server):
    satz = kette.HINWEIS_SKIZZE_NICHT_ANGEKOMMEN.format(backbone="b", beleg="x")

    def bild(herkunft):
        return server._bild_fuer_die_flaeche({"bild": "a.png", "herkunft": herkunft})

    ja = bild({"skizze": "s.png", "messung": {"hinweise": [satz, "anderes"]}})
    nein = bild({"skizze": "s.png", "messung": {"hinweise": ["anderes"]}})
    ungemessen = bild({"skizze": "s.png"})
    keine_skizze = bild({"messung": {"hinweise": [satz]}})

    assert (ja["skizze_nicht_angekommen"], ja["skizze_hinweis"]) == (True, satz)
    assert (nein["skizze_nicht_angekommen"], nein["skizze_hinweis"]) == (False, None)
    assert ungemessen["skizze_nicht_angekommen"] is None
    assert ungemessen["hinweise"] is None
    assert keine_skizze["skizze_nicht_angekommen"] is None
    assert nein["hinweise"] == ["anderes"]


def test_der_laufstand_zeigt_die_laufende_variante(server, tmp_path):
    stand = server.Laufstand()
    stand.beginne(tmp_path, schritte_gesamt=8, bestellung={"art": "modell", "varianten": 3})
    stand.melde({"art": "knoten_beginnt", "knoten": "render", "knotenart": "render",
                 "nummer": 3, "von": 4})
    stand.melde({"art": "schritt", "schritt": 5})
    stand.melde({"art": "variante_beginnt", "nummer": 2, "von": 3, "gruppe": "g"})

    s = stand.sicht()
    assert s["variante"] == {"nummer": 2, "von": 3, "gruppe": "g"}
    assert s["schritt"] is None and s["nummer"] is None, (
        "die neue Variante zählt von vorn — sonst sähe sie aus wie ein Lauf rückwärts")
    assert s["bestellung"]["varianten"] == 3


def test_ein_neuer_lauf_vergisst_den_alten_abbruch(server, tmp_path):
    stand = server.Laufstand()
    stand.beginne(tmp_path)
    assert stand.verlange_abbruch() is True
    stand.beende(ergebnis={"abgebrochen": True})
    assert stand.verlange_abbruch() is False, "nach dem Ende gibt es nichts abzubrechen"
    stand.beginne(tmp_path)
    assert stand.abbruch_verlangt() is False


# ======================================================================================
# 5 · Die Seite: die Zahl im Prüfzeichen wird nie auf Gleichstand gerundet
# ======================================================================================

def _node():
    return shutil.which("node")


@pytest.mark.parametrize("score,schwelle,erwartet", [
    (0.8123, 0.7, ("0.81", "0.70")),
    (0.7999, 0.8, ("0.7999", "0.8000")),       # durchgefallen; zwei Stellen: «0.80 / 0.80»
    (0.80001, 0.8, ("0.80001", "0.80000")),    # bestanden, knapp; erst die fünfte trennt
    (0.7949, 0.795, ("0.79", "0.80")),         # schon zwei Stellen trennen — mehr nicht
    (0.7, 0.7, ("0.70", "0.70")),              # wirklich gleich bleibt gleich
    (0.9, None, ("0.90", None)),
    (None, 0.7, None),                         # nicht gemessen ist keine Zahl
])
def test_die_zahl_im_pruefzeichen_wird_nie_auf_gleichstand_gerundet(score, schwelle,
                                                                     erwartet):
    """Gefahren in ``node`` — die Funktion aus der Seite selbst, nicht eine Abschrift."""
    node = _node()
    if node is None:
        pytest.skip("kein node im PATH — die Funktion der Seite lässt sich hier nicht fahren")
    seite = SEITE.read_text(encoding="utf-8")
    funktion = re.search(r"\nfunction zahlText\(.*?\n}\n", seite, re.S)
    assert funktion, "zahlText steht nicht mehr in der Seite"
    skript = (funktion.group(0) + "\nconst r = zahlText(" + json.dumps(score) + ", "
              + json.dumps(schwelle) + ");\nconsole.log(JSON.stringify(r));\n")
    lauf = subprocess.run([node, "-e", skript], capture_output=True, text=True, timeout=30)
    assert lauf.returncode == 0, lauf.stderr
    r = json.loads(lauf.stdout)
    if erwartet is None:
        assert r is None
    else:
        assert (r["score"], r["schwelle"]) == erwartet


def test_die_seite_ruft_die_neuen_wege(server):
    """Was nur über einen Klick erreichbar ist, existiert nicht — und umgekehrt: Ein Weg,
    den die Seite nicht ruft, ist für den Menschen am Rechner nicht da. Gelesen als Text;
    die Wirkung der Wege selbst prüfen die Proben oben."""
    seite = SEITE.read_text(encoding="utf-8")
    for weg in (server.WEG_BENENNEN, server.WEG_ABBRECHEN, server.WEG_RECHNE_SKIZZE):
        assert f'"{weg}"' in seite, weg
    assert "schluessel: tafel.schluessel" in seite
    assert "Wischregler" in seite and "Nebeneinander" in seite


# ======================================================================================
# 6 · Die Seite selbst, gefahren in node — gegen eine echte Sicht
# ======================================================================================
#
# Kein Browser in dieser Umgebung. Gefahren wird darum das Skript der Seite in node
# gegen eine kleine DOM-Attrappe (unten, _DOM) — mit einer Sicht, die der Server aus
# einer echten Mappe baut. Geprueft wird, was die Seite TUT: was sie anzeigt, welche Wege
# sie mit welchem Rumpf ruft, und dass der Wischregler schneidet. Nicht geprueft: wie es
# aussieht (Abstaende, Farben am Bildschirm) — das zeigt erst ein Browser.

_DOM = r"""// Eine DOM-Attrappe: gerade so viel Element, wie das Skript der Seite anfasst. Was sie
// nicht kennt, wirft — und genau das soll hier auffallen.
const fs = require("fs");
const sicht = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
const skript = fs.readFileSync(process.argv[3], "utf8");
const fehler = [];
class ClassList { constructor(e){this.e=e;} _s(){return new Set((this.e.className||"").split(/\s+/).filter(Boolean));}
  add(...c){const s=this._s();c.forEach(x=>s.add(x));this.e.className=[...s].join(" ");}
  remove(...c){const s=this._s();c.forEach(x=>s.delete(x));this.e.className=[...s].join(" ");}
  toggle(c,f){const s=this._s();const an=f===undefined?!s.has(c):f;an?s.add(c):s.delete(c);this.e.className=[...s].join(" ");return an;}
  contains(c){return this._s().has(c);} }
class El {
  constructor(tag){this.tagName=(tag||"div").toUpperCase();this.children=[];this.className="";this.hidden=false;this.style={};this.dataset={};
    this._text="";this.value="";this.classList=new ClassList(this);this.listeners={};this.width=0;this.height=0;this.naturalWidth=0;this.checked=false;this.disabled=false;}
  get textContent(){return this._text+this.children.map(c=>c.textContent||"").join("");}
  set textContent(t){this._text=String(t);this.children=[];}
  append(...k){for(const x of k){if(x&&x.parentNode)x.remove();const n=(typeof x==="string")?Object.assign(new El("#text"),{_text:x}):x;n.parentNode=this;this.children.push(n);}}
  prepend(...k){this.append(...k);const n=this.children.splice(this.children.length-k.length);this.children.unshift(...n);}
  replaceChildren(...k){this.children=[];this._text="";this.append(...k);}
  insertBefore(n,ref){if(n.parentNode)n.remove();n.parentNode=this;const i=this.children.indexOf(ref);if(i<0)this.children.push(n);else this.children.splice(i,0,n);}
  remove(){if(this.parentNode){const p=this.parentNode;p.children=p.children.filter(c=>c!==this);this.parentNode=null;}}
  replaceWith(n){const p=this.parentNode;if(!p)return;const i=p.children.indexOf(this);p.children[i]=n;n.parentNode=p;this.parentNode=null;}
  addEventListener(t,f){(this.listeners[t]=this.listeners[t]||[]).push(f);}
  klick(){for(const f of (this.listeners.click||[]))f({});}
  querySelector(sel){const cls=sel.replace(".","");const such=(e)=>{for(const c of e.children){if(c.classList&&c.classList.contains(cls))return c;const r=such(c);if(r)return r;}return null;};return such(this);}
  alle(pred,aus=[]){for(const c of this.children){if(pred(c))aus.push(c);c.alle&&c.alle(pred,aus);}return aus;}
  focus(){} setPointerCapture(){} getBoundingClientRect(){return {left:0,top:0,width:1,height:1};}
  getContext(){return new Proxy({}, {get:()=>()=>{} , set:()=>true});}
  toDataURL(){return "data:image/png;base64,AAAA";}
}
const ids = {};
const document = { hidden:false, getElementById:(id)=>ids[id]||(ids[id]=new El("div")), createElement:(t)=>new El(t),
  createTextNode:(t)=>Object.assign(new El("#text"),{_text:t}), querySelectorAll:(sel)=>{
    const cls=sel.replace(/^\./,"").split(" ")[0]; const out=[]; for (const e of Object.values(ids)) e.alle(c=>c.classList&&c.classList.contains(cls), out); return out; } };
let fortschritt = {laeuft:false, fertige:[], ergebnis:null, fehler:null};
const gesendet = [];
async function fetch(url, opt) {
  gesendet.push([url, opt && opt.body]);
  let d = {};
  if (url.startsWith("/api/projekt")) d = sicht;
  else if (url.startsWith("/api/fortschritt")) d = fortschritt;
  else d = {gestartet:true, abbruch_verlangt:true, satz:"ok", benannt:true};
  return {json: async () => d};
}
const crypto = require("crypto").webcrypto;
const ctx = {document, fetch, crypto, setInterval:()=>1, clearInterval:()=>{}, console, isFinite, Number, JSON, Math, Set, Map, Array, String, Uint8Array};
const lauf = new Function(...Object.keys(ctx), skript + `
;return {zeigeLauf, zeigeBilder, zeigeWarteschlange, laden, ids: null};`);
(async () => {
  const api = lauf(...Object.values(ctx));
  await new Promise(r => setTimeout(r, 50));
  // Nach dem Laden: Bilder und Warteschlange
  const bilder = ids["bilder"], schlange = ids["schlange"];
  const text = bilder.textContent;
  const pruefe = (b, satz) => { if (!b) fehler.push(satz); };
  pruefe(text.includes("bestanden · 0.81"), "Zahl im Zeichen fehlt");
  pruefe(text.includes("(Schwelle 0.80)"), "Schwelle in der Auflage fehlt");
  pruefe(text.includes("Entwurf — nicht geprüft"), "Entwurf-Zeichen fehlt");
  pruefe(text.includes("ENTWURF — NICHT GEPRÜFT"), "Entwurf in der Auflage fehlt");
  pruefe(text.includes("SKIZZE NICHT ANGEKOMMEN"), "Skizze-Hinweis fehlt");
  // AUF DEM BILD, nicht nur in der Karte: in der Auflage, die beim Weiterreichen mitgeht.
  const auflagen = bilder.alle(c => c.classList && c.classList.contains("auflage"));
  pruefe(auflagen.some(a => a.textContent.includes("SKIZZE NICHT ANGEKOMMEN")),
         "der Skizze-Hinweis steht nicht auf dem Bild");
  pruefe(auflagen.some(a => a.textContent.startsWith("GEPRÜFT · 0.81 (Schwelle 0.80)")),
         "Zahl und Schwelle stehen nicht auf dem Bild");
  pruefe(text.includes("Variantenreihe (Startwerte)"), "Reihe Startwerte fehlt");
  pruefe(text.includes("Variantenreihe (Ebenen)"), "Reihe Ebenen fehlt");
  pruefe(schlange.textContent.includes("Dritte Idee"), "Titel in der Warteschlange fehlt");
  pruefe(ids["schlangenzahl"].textContent === "1", "Zahl der Warteschlange: " + ids["schlangenzahl"].textContent);
  pruefe(schlange.textContent.includes("gerechnet: skizze-1.png"), "gerechnete Skizze fehlt");
  // Wischregler umschalten
  const knoepfe = bilder.alle(c => c.tagName === "BUTTON" && c.textContent === "Wischregler");
  pruefe(knoepfe.length === 2, "Wischregler-Knoepfe: " + knoepfe.length);
  knoepfe[0].klick();
  const regler = bilder.alle(c => c.classList && c.classList.contains("wischregler"));
  pruefe(regler.length === 1, "kein Regler nach dem Umschalten");
  if (regler[0]) { regler[0].value = "30"; regler[0].listeners.input[0](); }
  const deck = bilder.alle(c => c.classList && c.classList.contains("deck"))[0];
  pruefe(deck && deck.children[0].style.clipPath === "inset(0 0 0 30%)", "Schnitt wirkt nicht");
  // Rechnen lassen in der Warteschlange
  const los = schlange.alle(c => c.tagName === "BUTTON" && c.textContent === "Rechnen lassen");
  los[0].klick();
  await new Promise(r => setTimeout(r, 10));
  const rs = gesendet.find(g => g[0] === "/api/rechne-skizze");
  pruefe(rs && JSON.parse(rs[1]).skizze === "skizze-3.png", "rechne-skizze nicht gesendet: " + JSON.stringify(rs));
  // Umbenennen eines Bildes
  const ben = bilder.alle(c => c.tagName === "BUTTON" && c.textContent === "Benennen")[0];
  ben.klick();
  const zeilen = bilder.alle(c => c.classList && c.classList.contains("benennen"));
  const inp = zeilen[0].children[0]; inp.value = "Neu";
  zeilen[0].children[1].klick();
  await new Promise(r => setTimeout(r, 10));
  const bn = gesendet.find(g => g[0] === "/api/benennen");
  pruefe(bn && JSON.parse(bn[1]).titel === "Neu" && JSON.parse(bn[1]).von_stand === sicht.stand_nr && JSON.parse(bn[1]).bild, "benennen: " + JSON.stringify(bn));
  // Laufstand: laeuft mit Variante, dann angehalten
  api.zeigeLauf({laeuft:true, knotenart:"render", nummer:3, von:4, art_des_zeichens:"belegt", schritt:4, schritte_gesamt:8,
                 fertige:[{knotenart:"geometrie", status:"ok"}], variante:{nummer:2, von:3}, bestellung:{entwurf:true}, abbruch_verlangt:false});
  pruefe(ids["abbrechen"].hidden === false, "Abbrechen-Knopf nicht sichtbar");
  pruefe(ids["laufknoten"].textContent.includes("Variante 2 von 3"), "Variante fehlt");
  ids["abbrechen"].klick();
  await new Promise(r => setTimeout(r, 10));
  pruefe(gesendet.some(g => g[0] === "/api/abbrechen"), "abbrechen nicht gesendet");
  api.zeigeLauf({laeuft:false, fertige:[], abbruch_verlangt:true, ergebnis:{vermerkt:1, abgebrochen:true, varianten_nicht_begonnen:1}, fehler:null});
  pruefe(ids["laufsatz"].textContent.startsWith("Angehalten — 1 Bilder eingetragen, 1 Varianten nicht begonnen"), "Angehalten: " + ids["laufsatz"].textContent);
  pruefe(ids["abbrechen"].hidden === true, "Knopf bleibt nach dem Ende");
  api.zeigeLauf({laeuft:false, fertige:[], abbruch_verlangt:true, ergebnis:{vermerkt:1, abgebrochen:false}, fehler:null});
  pruefe(ids["abbruchsatz"].textContent.includes("schon fertig"), "verlangt ungewirkt");
  console.log(fehler.length ? "FEHLER:\n" + fehler.join("\n") : "alles gut");
})().catch(e => { console.log("AUSNAHME", e.stack); });
"""


@pytest.fixture
def sicht_mit_allem(server, mappe, monkeypatch):
    """Eine Mappe mit einem gepruefen Bild, einer Entwurfsreihe aus drei Startwerten,
    zwei als Ebenen gerechneten Skizzen und einer benannten, noch offenen Skizze."""
    werk = _Werkbank()
    tafel = werk.tabelle()
    arbeitsgang.rechne(mappe, ausfuehrer=tafel, qa_schwelle=0.8)
    arbeitsgang.rechne(mappe, ausfuehrer=tafel, entwurf=True, varianten=3)
    for i in (1, 2, 3):
        _png(mappe / f"skizze-{i}.png")
        p = _mappe(mappe)
        projekt.vermerke_skizze(p, skizze=f"skizze-{i}.png", bemerkung=f"Ebene {i}")
        projekt.speichere(p, mappe)
    skizzentafel = {**tafel, ART_BILDQUELLE: kette.AUSFUEHRER[ART_BILDQUELLE],
                    ART_NACHRENDER: kette.nachrender_ausfuehrer(modell=_Modell()),
                    ART_QA: kette.qa_ausfuehrer()}
    arbeitsgang.rechne_skizze(mappe, ["skizze-1.png", "skizze-2.png"], ausfuehrer=skizzentafel)
    projekt.benenne(mappe, skizze="skizze-3.png", titel="Dritte Idee")
    return server.sicht(mappe)


def test_die_seite_zeigt_und_ruft_was_die_app_braucht(sicht_mit_allem, tmp_path):
    """Zahl im Prüfzeichen, Entwurf, «Skizze nicht angekommen», Variantenreihen,
    Warteschlange mit «Rechnen lassen», Umbenennen, Wischregler, Abbrechen — **an der
    Wirkung des Skripts**, nicht an seinem Text."""
    node = _node()
    if node is None:
        pytest.skip("kein node im PATH — das Skript der Seite lässt sich hier nicht fahren")
    skript = re.search(r"<script>(.*)</script>", SEITE.read_text(encoding="utf-8"), re.S)
    (tmp_path / "seite.js").write_text(skript.group(1), encoding="utf-8")
    (tmp_path / "sicht.json").write_text(json.dumps(sicht_mit_allem), encoding="utf-8")
    (tmp_path / "dom.js").write_text(_DOM, encoding="utf-8")
    lauf = subprocess.run([node, str(tmp_path / "dom.js"), str(tmp_path / "sicht.json"),
                           str(tmp_path / "seite.js")], capture_output=True, text=True,
                          timeout=60)
    assert lauf.returncode == 0, lauf.stderr
    assert lauf.stdout.strip() == "alles gut", lauf.stdout + lauf.stderr
