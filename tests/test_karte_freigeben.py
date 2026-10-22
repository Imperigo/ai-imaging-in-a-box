"""Owner-Entscheid 127 (22.10.2026, Option A): **Vor jedem Bildauftrag gibt Visbox alle
geladenen Ollama-Modelle frei — auch fremde — per ``keep_alive: 0``.**

Anlass: Generalprobe 327 (``auftraege/ergebnisse/auf-20261022-327.json``, Hauptbefund 1):
Bildmodell 27,9 GB und das Sprachmodell eines anderen Programms (22 GB) passen nicht zugleich
auf die 32-GB-Karte.

Geprüft ohne GPU und ohne Ollama — Ollama ist nachgestellt (``assistent._oeffne``):
mehrere Modelle, eines fremd; Ollama fehlt; Ollama hängt; ein Modell, das bleibt; und der
Weg durch den Abholer und den Dienst. Kein Bild, keine echten Projektdaten (Regel 3).
"""
from __future__ import annotations

import io
import json
import socket
import sys
import urllib.error
from pathlib import Path

import pytest

from aiimaging import abholer, assistent, bruecke, render
from conftest import GIB_KARTE_FREI_ECHT

WURZEL = Path(__file__).resolve().parents[1]
GIB = 2**30

#: Was Ollama in 327 hielt — das fremde Modell mit 22 GB, dazu das eigene des Assistenten.
FREMD = "kosmo-qwen3.6:35b-a3b"
EIGEN = "qwen3:14b"


class Uhr:
    """Eine Uhr, die nur beim Warten vorrückt — damit Fristen ohne Schlaf geprüft werden."""

    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t

    def warte(self, s):
        self.t += s


class NachgestelltesOllama:
    """``/api/ps``, ``/api/generate`` und ``/api/chat`` wie Ollama — nur im Speicher.

    ``bleibt``: Modelle, die ``keep_alive: 0`` nicht von der Karte nimmt. ``generate_400``:
    Modelle, bei denen ``/api/generate`` mit 400 ablehnt (etwa ein reines Einbettungsmodell).
    """

    def __init__(self, geladen, *, bleibt=(), generate_400=(), doppelt=False):
        self.geladen = list(geladen)
        self.bleibt, self.generate_400, self.doppelt = set(bleibt), set(generate_400), doppelt
        self.anfragen = []

    def __call__(self, anfrage, frist):
        pfad = anfrage.full_url.split("11434", 1)[-1]
        rumpf = json.loads(anfrage.data) if anfrage.data else None
        self.anfragen.append((anfrage.get_method(), pfad, rumpf))
        if pfad == "/api/ps":
            modelle = []
            for name, groesse_gb in self.geladen:
                m = {"name": name, "model": name, "size": int(groesse_gb * GIB),
                     "size_vram": int(groesse_gb * GIB)}
                modelle.append(m)
                if self.doppelt:
                    modelle.append(dict(m, model=name + ":latest" if ":" not in name else name))
            return json.dumps({"models": modelle}).encode()
        if pfad in ("/api/generate", "/api/chat"):
            name = rumpf["model"]
            if pfad == "/api/generate" and name in self.generate_400:
                raise urllib.error.HTTPError(anfrage.full_url, 400, "bad", {}, io.BytesIO(b""))
            if rumpf.get("keep_alive") == 0 and name not in self.bleibt:
                self.geladen = [(n, g) for n, g in self.geladen if n != name]
            return json.dumps({"done": True}).encode()
        raise AssertionError(f"unerwartete Anfrage {pfad}")

    def posts(self):
        return [(p, r) for m, p, r in self.anfragen if m == "POST"]


def _frei(monkeypatch, ollama, **kw):
    monkeypatch.setattr(assistent, "_oeffne", ollama)
    uhr = Uhr()
    return GIB_KARTE_FREI_ECHT(_uhr=uhr, _warte=uhr.warte, **kw)


# =============================================================== die Freigabe selbst

def test_alle_modelle_werden_freigegeben_auch_das_fremde(monkeypatch):
    ollama = NachgestelltesOllama([(FREMD, 22.0), (EIGEN, 16.4)])
    befund = _frei(monkeypatch, ollama)
    assert befund["ollama"] == "freigegeben"
    assert [m["modell"] for m in befund["freigegeben"]] == [FREMD, EIGEN]
    assert {m["modell"]: m["eigen"] for m in befund["freigegeben"]} == {FREMD: False, EIGEN: True}
    assert befund["freigegeben"][0]["vram_mib"] == 22528
    assert befund["danach_leer"] is True and befund["nicht_freigegeben"] == []
    assert befund["dauer_s"] is not None
    # NUR keep_alive 0, NUR an die gemeldeten Modelle — nichts geladen, nichts eingestellt.
    assert ollama.posts() == [("/api/generate", {"model": FREMD, "keep_alive": 0}),
                              ("/api/generate", {"model": EIGEN, "keep_alive": 0})]
    assert FREMD in befund["satz"] and "22,0 GB" in befund["satz"]
    assert "anderes Programm" in befund["satz"] and "Assistent der Visbox" in befund["satz"]


def test_name_und_model_zaehlen_einmal(monkeypatch):
    ollama = NachgestelltesOllama([(FREMD, 22.0)], doppelt=True)
    befund = _frei(monkeypatch, ollama)
    assert len(befund["freigegeben"]) == 1 and len(ollama.posts()) == 1


def test_nichts_geladen_nichts_gefragt(monkeypatch):
    ollama = NachgestelltesOllama([])
    befund = _frei(monkeypatch, ollama)
    assert befund["ollama"] == "leer" and befund["danach_leer"] is True
    assert ollama.posts() == []


def test_ollama_fehlt_kein_fehler(monkeypatch):
    def aus(anfrage, frist):
        raise urllib.error.URLError(ConnectionRefusedError(111, "refused"))
    befund = _frei(monkeypatch, aus)
    assert befund["ollama"] == "aus" and befund["freigegeben"] == []
    assert "nichts freizugeben" in befund["satz"]


@pytest.mark.parametrize("fehler", [socket.timeout("timed out"), TimeoutError()])
def test_ollama_haengt_kein_fehler(monkeypatch, fehler):
    gefragt = []

    def haengt(anfrage, frist):
        gefragt.append(frist)
        raise fehler
    befund = _frei(monkeypatch, haengt)
    assert befund["ollama"] == "haengt" and "trotzdem" in befund["satz"]
    # Nur die eine Abfrage, mit kurzer Frist — ein hängendes Ollama hält den Auftrag nicht auf.
    assert len(gefragt) == 1 and gefragt[0] <= assistent.FRIST_STAND_S


def test_haengt_beim_freigeben_die_uebrigen_werden_nicht_mehr_gefragt(monkeypatch):
    ollama = NachgestelltesOllama([(FREMD, 22.0), (EIGEN, 16.4)])

    def oeffne(anfrage, frist):
        if anfrage.full_url.endswith("/api/generate"):
            ollama.anfragen.append(("POST", "/api/generate", None))
            raise socket.timeout("timed out")
        return ollama(anfrage, frist)
    befund = _frei(monkeypatch, oeffne)
    assert befund["ollama"] == "teilweise" and befund["freigegeben"] == []
    assert [m["modell"] for m in befund["nicht_freigegeben"]] == [FREMD, EIGEN]
    assert len(ollama.posts()) == 1


def test_ein_modell_das_bleibt_wird_nach_der_frist_genannt(monkeypatch):
    ollama = NachgestelltesOllama([(FREMD, 22.0), (EIGEN, 16.4)], bleibt={FREMD})
    befund = _frei(monkeypatch, ollama)
    assert befund["ollama"] == "teilweise" and befund["danach_leer"] is False
    assert befund["noch_geladen"] == [FREMD]
    assert befund["dauer_s"] >= assistent.FRIST_KARTE_LEER_S
    assert f"liegt noch {FREMD}" in befund["satz"]


def test_lehnt_generate_ab_dann_ueber_chat(monkeypatch):
    ollama = NachgestelltesOllama([("nomic-embed-text", 0.3)], generate_400={"nomic-embed-text"})
    befund = _frei(monkeypatch, ollama)
    assert befund["ollama"] == "freigegeben"
    assert ollama.posts()[-1] == ("/api/chat", {"model": "nomic-embed-text", "keep_alive": 0,
                                                "messages": []})


def test_falsche_adresse_kein_fehler(monkeypatch):
    befund = GIB_KARTE_FREI_ECHT(adresse="file:///etc/passwd")
    assert befund["ollama"] == "fehler"


def test_die_proben_geben_keine_echte_karte_frei():
    """Die Vorkehrung in ``conftest.py``: In der Sammlung ist die Freigabe ersetzt."""
    assert assistent.gib_karte_frei is not GIB_KARTE_FREI_ECHT
    assert assistent.gib_karte_frei() is None


# ================================================================= durch den Abholer

def _ordner(tmp_path, **vis):
    from test_kettenlauf_26august import _auftragsordner
    ordner = _auftragsordner(tmp_path / "a")
    if vis:
        pfad = ordner / bruecke.DATEI_SZENE
        szene = json.loads(pfad.read_text(encoding="utf-8"))
        szene["vis"].update(vis)
        pfad.write_text(json.dumps(szene), encoding="utf-8")
    return ordner


def _verarbeiter(tmp_path):
    from test_befunde_298 import _verarbeiter as v
    return v(tmp_path)


def test_der_abholer_gibt_vor_allen_pruefungen_frei_und_vermerkt_es(tmp_path):
    """Der Fall aus 298/327: ein fremdes Modell auf der Karte. Nach der Freigabe sieht die
    Bildeingang-Prüfung eine leere Karte, und der Auftrag rechnet."""
    ordner = _ordner(tmp_path, bildeingang=0.55)
    zettel = ordner / bruecke.DATEI_LAUFZETTEL
    daten = json.loads(zettel.read_text(encoding="utf-8"))
    daten["idle_window_only"] = True
    zettel.write_text(json.dumps(daten), encoding="utf-8")
    geladen = [FREMD]
    folge = []
    befund = {"ollama": "freigegeben", "freigegeben": [{"modell": FREMD, "groesse_mib": 22528,
                                                        "vram_mib": 22528, "eigen": False}],
              "nicht_freigegeben": [], "danach_leer": True, "noch_geladen": [],
              "dauer_s": 0.4, "satz": f"Grafikkarte für das Bild freigegeben: {FREMD}."}

    def freigeben():
        folge.append("freigeben")
        geladen.clear()
        return befund

    def karte():
        folge.append("karte")
        return (not geladen), ("frei" if not geladen else "22000 MiB belegt")

    def bildeingang():
        folge.append("bildeingang")
        return {"frei_mib": 30868, "eigen_mib": 0, "fremde_modelle": list(geladen)}

    _p, verarbeite = _verarbeiter(tmp_path)
    antwort = abholer.hole_einen(ordner, fremde_freigabe_gilt=True, verarbeite=verarbeite,
                                 darf_rechnen=karte, bildeingang_karte=bildeingang,
                                 karte_freigeben=freigeben)
    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort["grund"]
    assert folge == ["freigeben", "karte", "bildeingang"]
    assert antwort["freigegeben"] == befund
    ergebnis = json.loads((ordner / bruecke.DATEI_ERGEBNIS).read_text(encoding="utf-8"))
    assert ergebnis["angewandt"]["freigegeben"]["freigegeben"][0]["modell"] == FREMD
    # Additiv: was vorher in `angewandt` stand, bleibt.
    assert "messschalter" in ergebnis["angewandt"]
    befund_datei = json.loads((ordner / abholer.DATEI_BEFUND).read_text(encoding="utf-8"))
    assert befund_datei["angewandt"]["freigegeben"]["ollama"] == "freigegeben"


def test_scheitert_die_freigabe_rechnet_der_auftrag_trotzdem(tmp_path):
    ordner = _ordner(tmp_path)

    def kaputt():
        raise RuntimeError("Ollama weg")
    _p, verarbeite = _verarbeiter(tmp_path)
    antwort = abholer.hole_einen(ordner, fremde_freigabe_gilt=True, verarbeite=verarbeite,
                                 karte_freigeben=kaputt)
    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort["grund"]
    assert antwort["freigegeben"]["ollama"] == "fehler"
    assert "trotzdem" in antwort["freigegeben"]["satz"]


def test_ohne_freigabe_wie_bisher(tmp_path):
    ordner = _ordner(tmp_path)
    _p, verarbeite = _verarbeiter(tmp_path)
    antwort = abholer.hole_einen(ordner, fremde_freigabe_gilt=True, verarbeite=verarbeite)
    assert antwort["tat"] == abholer.TAT_VERARBEITET and antwort["freigegeben"] is None
    ergebnis = json.loads((ordner / bruecke.DATEI_ERGEBNIS).read_text(encoding="utf-8"))
    assert "freigegeben" not in (ergebnis.get("angewandt") or {})


def test_ein_auftrag_mit_maengeln_gibt_nichts_frei(tmp_path):
    """Freigegeben wird nur für einen Auftrag, der rechnen darf — nicht für einen, der liegen
    bleibt, weil die Bestellung kaputt ist."""
    ordner = _ordner(tmp_path, skip=True, guete="voll")
    gerufen = []
    _p, verarbeite = _verarbeiter(tmp_path)
    antwort = abholer.hole_einen(ordner, fremde_freigabe_gilt=True, verarbeite=verarbeite,
                                 karte_freigeben=lambda: gerufen.append(1))
    assert antwort["tat"] != abholer.TAT_VERARBEITET
    assert gerufen == [] and antwort["freigegeben"] is None


def test_der_betrieb_gibt_frei_und_meldet_es():
    quelle = (WURZEL / "tools" / "abholen.py").read_text(encoding="utf-8")
    assert "karte_freigeben=lambda: assistent.gib_karte_frei()" in quelle
    assert "Grafikkarte (" in quelle


def test_die_bildeingang_absage_sagt_nicht_mehr_nie(tmp_path):
    satz = render.pruefe_bildeingang_karte("z-image-turbo", frei_mib=15000,
                                           fremde_modelle=[FREMD])["satz"]
    assert "Entscheid 127" in satz and "nie" not in satz.replace("Nicht", "")


# =================================================================== durch den Dienst

@pytest.fixture(scope="module")
def server():
    flaeche = WURZEL / "oberflaeche"
    sys.path.insert(0, str(flaeche))
    try:
        import server as modul
        return modul
    finally:
        sys.path.remove(str(flaeche))


def test_der_dienst_gibt_vor_dem_lauf_frei(server, monkeypatch, tmp_path):
    from aiimaging import arbeitsgang
    folge = []
    befund = {"ollama": "leer", "satz": "nichts"}

    def frei():
        folge.append("frei")
        return befund

    def rechne(*_a, **_k):
        folge.append("rechne")
        return {"lauf": {"status": "ok"}, "vermerkt": True, "modell_stand": None}
    monkeypatch.setattr(assistent, "gib_karte_frei", frei)
    monkeypatch.setattr(arbeitsgang, "rechne", rechne)
    monkeypatch.setattr(render, "gib_grafikspeicher_frei", lambda: {})
    server.LAUFSTAND.beginne(tmp_path)
    server._rechne_im_hintergrund(tmp_path, False, {})
    assert folge == ["frei", "rechne"]
    assert server.LAUFSTAND.sicht()["ergebnis"]["freigegeben"] == befund
