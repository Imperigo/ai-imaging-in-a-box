"""«Datei laden …» am Modell-Knoten — Owner-Entscheid 90 (14.10.2026, Blatt 21).

Was hier bewacht wird
---------------------
* **Bibliothek** (:mod:`aiimaging.modellladen`, :func:`arbeitsgang.ersetze_modell`,
  :func:`projekt.neue_fassung`): die neue Mappe liegt **neben der Start-Mappe** (90a), ihr
  Name kommt bereinigt aus dem Dateinamen, ein Namenszusammenstoss mit einem fremden Ordner
  gibt ``-2``; **dieselbe Datei noch einmal** ist eine neue Fassung in derselben Mappe, und
  Bilder, Skizzen und Läufe bleiben (90b); eine ArchiCAD-Datei bekommt ihren Satz (90c);
  eine abgelehnte Datei hinterlässt keine Mappe und ersetzt nichts.
* **Server** (``POST``/``GET /knoten/modell-laden``): nur angemeldet, Grösse, Dateiname,
  Laden im Hintergrund, danach ist die Mappe die zuletzt geöffnete — für die Knoten und für
  die Visbox-Seite.
* **Formate:** die Liste unter dem Knopf ist die aus ``importeur.WEGE``.
* **Mac-App:** ohne ``WKUIDelegate`` öffnet ein ``<input type=file>`` in einer
  ``WKWebView`` nichts — der Wächter verlangt ``runOpenPanelWith`` mit ``NSOpenPanel``.

Ohne ``.venv-ifc`` und ohne Blender: Umwandlung und Raumleser der IFC werden an der
Prozessgrenze ersetzt (wie in ``tests/test_innenansicht_mappe.py``). Die Dateien kommen aus
``tools/make_test_glb.py`` und ``tools/make_test_ifc.py`` — synthetisch (Regel 3).
"""
from __future__ import annotations

import base64
import importlib.util
import io
import json
import re
import sys
from pathlib import Path

import pytest

from aiimaging import arbeitsgang, importeur, kette, knotenweg, modellladen, projekt

WURZEL = Path(__file__).resolve().parents[1]
FLAECHE = WURZEL / "oberflaeche"
ARBEIT = WURZEL / "ipad" / "VisboxMac" / "Sources" / "VisboxMac" / "Start" / "Arbeitsansicht.swift"
WIRT = WURZEL / "kosmovis" / "apps" / "visbox-knoten" / "src"
SEITE = FLAECHE / "seite.html"


def _werkzeug(datei: str, name: str):
    spez = importlib.util.spec_from_file_location(name, WURZEL / "tools" / datei)
    modul = importlib.util.module_from_spec(spez)
    sys.modules[spez.name] = modul
    spez.loader.exec_module(modul)
    return modul


MK_GLB = _werkzeug("make_test_glb.py", "make_test_glb_fuer_modell_laden")
MK_IFC = _werkzeug("make_test_ifc.py", "make_test_ifc_fuer_modell_laden")

#: Drei Teile mit Geometrie, in glTF-Koordinaten — synthetisch.
DREI_TEILE = (("Wand_Nord", (0, 0, 0), (8, 3, 0.3)), ("Wand_Sued", (0, 0, 5), (8, 3, 5.3)),
              ("Decke", (0, 3, 0), (8, 3.2, 5.3)))
ZWEI_TEILE = (("Wand", (0, 0, 0), (6, 3, 0.3)), ("Decke", (0, 3, 0), (6, 3.2, 4)))


def _glb(teile=DREI_TEILE) -> bytes:
    return MK_GLB.baue_glb(list(teile))


class IfcAttrappe:
    """Umwandlung und Raumleser der IFC an der Prozessgrenze — was ankam, wird gezählt."""

    def __init__(self, monkeypatch, teile=DREI_TEILE):
        self.glb = _glb(teile)
        self.umgewandelt: list[str] = []
        self.raeume_gelesen: list[str] = []
        monkeypatch.setattr(kette.seams, "ifc_zu_glb", self.umwandlung)
        monkeypatch.setattr(kette.seams, "ifc_raeume", self.raumleser)

    def umwandlung(self, quelle, ziel, **kw):
        self.umgewandelt.append(Path(quelle).name)
        Path(ziel).write_bytes(self.glb)
        return {"status": "ok", "glb_path": str(ziel), "up_axis": "Y", "n_elements": 3}

    def raumleser(self, ifc_path, **kw):
        self.raeume_gelesen.append(Path(ifc_path).name)
        return {"status": "ok", "raeume": []}


@pytest.fixture
def start(tmp_path):
    """Die Start-Mappe des Servers — angelegt aus einer glb, wie im Betrieb."""
    quelle = tmp_path / "vorlagen" / "Startbau.glb"
    quelle.parent.mkdir()
    quelle.write_bytes(_glb())
    mappe = tmp_path / "mappen" / "Startbau"
    arbeitsgang.lege_an(mappe, quelle)
    return mappe


def _ifc_bytes(tmp_path) -> bytes:
    return MK_IFC.erzeuge_ifc(tmp_path / "ifc-vorlage" / "haus.ifc").read_bytes()


# ============================================================== die Bibliothek

def test_mappenname_nur_buchstaben_ziffern_strich_unterstrich():
    assert modellladen.mappenname("Bürohaus Süd (Stand 3).ifc") == "Buerohaus-Sued-Stand-3"
    assert modellladen.mappenname("haus_v2.glb") == "haus_v2"
    assert modellladen.mappenname("Café—Entwurf.obj") == "Cafe-Entwurf"
    assert modellladen.mappenname("###.glb") == "modell"
    assert len(modellladen.mappenname("a" * 300 + ".glb")) <= modellladen.NAME_HOECHSTENS
    for name in ("x.ifc", "Haus 1.glb", "Ümlaut.fbx"):
        assert re.fullmatch(r"[A-Za-z0-9_-]+", modellladen.mappenname(name))


@pytest.mark.parametrize("name", ["", "../haus.ifc", "ordner/haus.ifc", "a\\b.glb", ".glb",
                                  "ohne_endung", "x\n.glb", "a" * 201 + ".glb"])
def test_kein_name_der_kein_dateiname_ist(name):
    with pytest.raises(modellladen.ModellLadenError):
        modellladen.pruefe_dateiname(name)


def test_die_formate_sind_die_des_importeurs():
    formate = modellladen.anzeige_formate()
    assert formate[:2] == ["glb/glTF", "IFC"]
    for name in ("OBJ", "FBX", "STL", "PLY", "USD"):
        assert name in formate
    # Die fassungsabhängigen stehen am Ende, und nichts doppelt.
    assert formate[-2:] == ["Collada", "X3D"] and len(formate) == len(set(formate))
    endungen = modellladen.annehmen().split(",")
    assert set(importeur.WEGE) <= set(endungen)
    assert ".pln" in endungen, "sonst bietet der Wähler eine ArchiCAD-Datei gar nicht an (90c)"


def test_90a_neue_mappe_neben_der_start_mappe(start):
    ergebnis = modellladen.lade(start, "Neubau.glb", _glb())
    assert ergebnis["stand"] == "geladen", ergebnis
    mappe = ergebnis["mappe"]
    assert mappe == start.parent / "Neubau" and not ergebnis["ersetzt"]
    p = projekt.oeffne(mappe)["projekt"]
    assert p["name"] == "Neubau" and p["import"]["status"] == "ok"
    assert p["modell"]["pfad"] == "quelle/f1/Neubau.glb"           # relativ, in der Mappe
    assert (mappe / "quelle" / "f1" / "Neubau.glb").read_bytes() == _glb()
    assert knotenweg.mappe_fuer_knoten(mappe)["bauteile"] == 3
    # Die Start-Mappe ist unberührt.
    assert projekt.oeffne(start)["projekt"]["name"] == "Startbau"


def test_90a_ein_fremder_ordner_gleichen_namens_wird_nie_angefasst(start):
    fremd = start.parent / "Neubau"
    fremd.mkdir()
    (fremd / "notiz.txt").write_text("nicht anfassen", encoding="utf-8")
    andere = modellladen.lade(start, "Neubau.glb", _glb())["mappe"]
    assert andere == start.parent / "Neubau-2"
    assert sorted(p.name for p in fremd.iterdir()) == ["notiz.txt"]
    # Eine andere Datei, deren Name dieselbe Mappe ergäbe, bekommt die nächste Nummer.
    dritte = modellladen.lade(start, "Neubau.gltf.glb", _glb())["mappe"]
    assert dritte.name == "Neubau-gltf"
    vierte = modellladen.lade(start, "Neubau!.glb", _glb())["mappe"]
    assert vierte == start.parent / "Neubau-3"


def test_90b_dieselbe_datei_ist_eine_neue_fassung_und_bilder_bleiben(start):
    erste = modellladen.lade(start, "Wohnhaus.glb", _glb())
    mappe = erste["mappe"]
    p = projekt.oeffne(mappe)["projekt"]
    p["bilder"].append({"bild": "bild_001.png", "schicht": "render", "geometrie_bestanden": None})
    p["skizzen"].append({"skizze": "skizze_001.png"})
    p.setdefault("laeufe", []).append({"lauf": 1})
    projekt.speichere(p, mappe)
    vorher = projekt.oeffne(mappe)["projekt"]

    zweite = modellladen.lade(start, "Wohnhaus.glb", _glb(ZWEI_TEILE))
    assert zweite["stand"] == "geladen" and zweite["ersetzt"] and zweite["fassung"] == 2
    assert zweite["mappe"] == mappe, "gleiche Datei → gleiche Mappe"
    auf = projekt.oeffne(mappe)
    nachher = auf["projekt"]
    assert nachher["bilder"] == vorher["bilder"]
    assert nachher["skizzen"] == vorher["skizzen"]
    assert nachher["laeufe"] == vorher["laeufe"]
    # Der Modellstand wechselt sichtbar: Fassung, Pfad, Fingerabdruck, Verlauf.
    assert nachher["modell"]["fassung"] == 2 and projekt.modellfassung(nachher) == 2
    assert nachher["modell"]["pfad"] == "quelle/f2/Wohnhaus.glb"
    assert nachher["modell"]["abdruck"] != vorher["modell"]["abdruck"]
    (eintrag,) = nachher["modell_fassungen"]
    assert eintrag["fassung"] == 1 and eintrag["pfad"] == "quelle/f1/Wohnhaus.glb"
    assert eintrag["bilder_bis_dahin"] == 1 and eintrag["skizzen_bis_dahin"] == 1
    assert auf["modell_stand"] == projekt.MODELL_UNVERAENDERT     # rechnen geht weiter
    assert knotenweg.mappe_fuer_knoten(mappe)["bauteile"] == 2
    assert knotenweg.mappe_fuer_knoten(mappe)["fassung"] == 2
    # Die Datei der alten Fassung ist weg, ihr Eintrag nicht.
    assert not (mappe / "quelle" / "f1").exists()


def test_90b_ifc_neue_fassung_wandelt_um_und_liest_die_raeume(start, tmp_path, monkeypatch):
    attrappe = IfcAttrappe(monkeypatch)
    ifc = _ifc_bytes(tmp_path)
    schritte = []
    erste = modellladen.lade(start, "Haus.ifc", ifc, melder=schritte.append)
    assert erste["stand"] == "geladen", erste
    assert [s["schritt"] for s in schritte] == ["ablegen", "umwandeln", "raeume"]
    assert "Bauteile und Räume" in schritte[1]["satz"]
    mappe = erste["mappe"]
    assert knotenweg.mappe_fuer_knoten(mappe)["herkunft"] == "IFC"

    attrappe.glb = _glb(ZWEI_TEILE)
    zweite = modellladen.lade(start, "Haus.ifc", ifc)
    assert zweite["ersetzt"] and zweite["fassung"] == 2
    assert attrappe.umgewandelt == ["Haus.ifc", "Haus.ifc"]
    assert attrappe.raeume_gelesen == ["Haus.ifc", "Haus.ifc"]
    nachher = projekt.oeffne(mappe)["projekt"]
    assert nachher["import"]["glb"] == "modell.glb" and nachher["import"]["raeume"] is not None
    assert not (mappe / arbeitsgang.ZWISCHEN_GLB).exists()
    assert knotenweg.mappe_fuer_knoten(mappe)["bauteile"] == 2


def test_90b_eine_abgelehnte_neue_fassung_ersetzt_nichts(start, monkeypatch):
    mappe = modellladen.lade(start, "Haus.glb", _glb())["mappe"]
    vorher = projekt.oeffne(mappe)["projekt"]
    # Eine JPG unter dem Namen der glb: Der Sichtgang weist sie ab.
    zweite = modellladen.lade(start, "Haus.glb", b"\xff\xd8\xff\xe0" + b"\0" * 64)
    assert zweite["stand"] == "fehler" and zweite["satz"]
    nachher = projekt.oeffne(mappe)["projekt"]
    assert nachher["modell"] == vorher["modell"] and nachher["import"] == vorher["import"]
    assert not (mappe / "quelle" / "f2").exists()
    assert (mappe / "quelle" / "f1" / "Haus.glb").is_file()


def test_eine_abgelehnte_datei_hinterlaesst_keine_mappe(start):
    ergebnis = modellladen.lade(start, "Kaputt.glb", b"keine glb")
    assert ergebnis["stand"] == "fehler" and ergebnis["mappe"] is None
    assert "keine glb" in ergebnis["satz"]
    assert not (start.parent / "Kaputt").exists()


def test_eine_abgelehnte_umwandlung_hinterlaesst_keine_mappe(start, monkeypatch):
    def leer(quelle, ziel, **kw):
        # Wie der echte Weg: Der Runner endet mit Code 1, `ifc_zu_glb` wirft.
        raise kette.seams.SeamError("IFC→glb fehlgeschlagen (Code 1): keine Geometrie im IFC.")

    monkeypatch.setattr(kette.seams, "ifc_zu_glb", leer)
    ergebnis = modellladen.lade(start, "Leer.ifc", b"ISO-10303-21;\nEND-ISO-10303-21;\n")
    assert ergebnis["stand"] == "fehler" and ergebnis["mappe"] is None, ergebnis
    assert "keine Geometrie" in ergebnis["satz"]
    assert not (start.parent / "Leer").exists()


def test_gltf_mit_getrennten_dateien_wird_erklaert(start):
    js = {"asset": {"version": "2.0"}, "buffers": [{"uri": "haus.bin", "byteLength": 4}]}
    ergebnis = modellladen.lade(start, "Haus.gltf", json.dumps(js).encode())
    assert ergebnis["stand"] == "fehler" and "haus.bin" in ergebnis["satz"]
    assert ".glb" in ergebnis["satz"]


def test_90c_archicad_bekommt_den_satz_und_keine_mappe(start):
    ergebnis = modellladen.lade(start, "Entwurf.pln", b"ArchiCAD")
    assert ergebnis == {"stand": "fehler", "mappe": None, "ersetzt": False, "herkunft": "PLN",
                        "satz": "ArchiCAD-Dateien sind ein geschlossenes Format. In ArchiCAD: "
                                "Ablage → Sichern unter → IFC, dann die IFC laden."}
    assert not (start.parent / "Entwurf").exists()


def test_unbekanntes_format_nennt_die_formate(start):
    ergebnis = modellladen.lade(start, "plan.dwg", b"x")
    assert ergebnis["stand"] == "fehler" and "IFC" in ergebnis["satz"] and ".dwg" in ergebnis["satz"]


def test_ohne_start_mappe_kommt_die_mappe_in_den_festen_ordner(tmp_path, monkeypatch):
    """90d: Am Heim-PC lief der Dienst ohne --ordner; dann der feste Rueckfall-Ordner."""
    ziel = tmp_path / "zuhause" / "Visbox-Mappen"
    monkeypatch.setenv(modellladen.MAPPEN_ORDNER_ENV, str(ziel))
    ergebnis = modellladen.lade(None, "Neubau.glb", _glb())
    assert ergebnis["stand"] == "geladen", ergebnis
    assert Path(ergebnis["mappe"]).parent == ziel.resolve() or Path(ergebnis["mappe"]).parent == ziel
    monkeypatch.delenv(modellladen.MAPPEN_ORDNER_ENV)
    assert modellladen.mappen_ordner() == Path.home() / "Visbox-Mappen"


def test_zu_gross_ist_die_anfrage_falsch(start, monkeypatch):
    monkeypatch.setattr(modellladen, "GROESSTE_DATEI_BYTE", 10)
    with pytest.raises(modellladen.ModellLadenError, match="zu gross"):
        modellladen.lade(start, "a.glb", _glb())


def test_ersetzen_waehrend_einer_rechnung_wird_abgewiesen(start):
    mappe = modellladen.lade(start, "Haus.glb", _glb())["mappe"]
    sperre = arbeitsgang._nimm_sperre(mappe)
    try:
        ergebnis = modellladen.lade(start, "Haus.glb", _glb(ZWEI_TEILE))
    finally:
        sperre.unlink()
    assert ergebnis["stand"] == "fehler" and "läuft schon eine Rechnung" in ergebnis["satz"]
    assert projekt.modellfassung(projekt.oeffne(mappe)["projekt"]) == 1


def test_lege_an_meldet_seine_schritte_ohne_sich_aufhalten_zu_lassen(tmp_path):
    quelle = tmp_path / "a.glb"
    quelle.write_bytes(_glb())

    def kaputt(_):
        raise RuntimeError("Melder kaputt")

    ergebnis = arbeitsgang.lege_an(tmp_path / "m", quelle, melder=kaputt)
    assert ergebnis["import_bericht"]["status"] == "ok"


# ================================================================== der Server

@pytest.fixture
def server():
    sys.path.insert(0, str(FLAECHE))
    try:
        import server as modul
        return modul
    finally:
        sys.path.remove(str(FLAECHE))


class _Server:
    """Anfragen an **einen** Server (eine Klasse), wie im Betrieb — ohne Netz."""

    def __init__(self, modul, ordner, kennwort="geheim"):
        self.klasse = type("FlaecheMitOrdner", (modul.Flaeche,),
                           {"kennwort": kennwort, "ordner": ordner, "kopplung_offen": None,
                            "ablage": None, "zuletzt_geoeffnet": None,
                            "modell_laden": None, "modell_faden": None})

    def _frage(self, methode, weg, rumpf=b"", kopf=None, angemeldet=True):
        selbst = self.klasse.__new__(self.klasse)
        selbst.command, selbst.path = methode, weg
        koepfe = {"Content-Length": str(len(rumpf)), **(kopf or {})}
        if angemeldet:
            koepfe["Authorization"] = "Basic " + base64.b64encode(b"visbox:geheim").decode()
        selbst.headers = koepfe
        selbst.rfile, selbst.wfile = io.BytesIO(rumpf), io.BytesIO()
        codes = []
        selbst.send_response = lambda code, *a, **k: codes.append(code)
        selbst.send_header = lambda *a: None
        selbst.end_headers = lambda: None
        (selbst.do_POST if methode == "POST" else selbst.do_GET)()
        roh = selbst.wfile.getvalue()
        return codes[0], (json.loads(roh) if roh[:1] == b"{" else roh)

    def get(self, weg, **kw):
        return self._frage("GET", weg, **kw)

    def lade(self, dateiname, inhalt: bytes, **kw):
        grenze = "----visbox-probe"
        rumpf = (f"--{grenze}\r\nContent-Disposition: form-data; name=\"datei\"; "
                 f"filename=\"{dateiname}\"\r\nContent-Type: application/octet-stream\r\n\r\n"
                 ).encode() + inhalt + f"\r\n--{grenze}--\r\n".encode()
        return self._frage("POST", "/knoten/modell-laden", rumpf,
                           {"Content-Type": f"multipart/form-data; boundary={grenze}"}, **kw)

    def warte(self):
        faden = self.klasse.modell_faden
        if faden is not None:
            faden.join(timeout=30)
            assert not faden.is_alive()


def test_server_laedt_eine_datei_und_die_mappe_ist_danach_die_zuletzt_geoeffnete(server, start):
    s = _Server(server, start)
    code, sicht = s.get("/knoten/modell-laden")
    assert code == 200 and sicht["laden"] is None
    assert sicht["formate"] == modellladen.anzeige_formate()
    assert sicht["annehmen"] == modellladen.annehmen()

    code, antwort = s.lade("Neubau.glb", _glb())
    assert code == 202 and antwort["laden"]["stand"] == "laeuft"
    assert antwort["laden"]["datei"] == "Neubau.glb"
    s.warte()
    code, sicht = s.get("/knoten/modell-laden")
    laden = sicht["laden"]
    assert laden["stand"] == "geladen", laden
    assert laden["mappe"] == "Neubau" and laden["bauteile"] == 3 and laden["herkunft"] == "glb"
    assert laden["fassung"] == 1 and laden["ersetzt"] is False
    # KEIN PLATTENPFAD in der Antwort (Regel 3).
    assert str(start.parent) not in json.dumps(sicht)

    assert s.klasse.zuletzt_geoeffnet == str(start.parent / "Neubau")
    code, mappe = s.get("/knoten/mappe")
    assert code == 200 and mappe["mappe"] == "Neubau" and mappe["bauteile"] == 3
    code, glb = s.get("/knoten/modell.glb")
    assert code == 200 and glb[:4] == b"glTF"
    # Die Visbox-Seite ohne Angabe zeigt dieselbe Mappe (Entscheid 90 mit 85 B).
    code, seite = s.get("/api/projekt")
    assert code == 200 and seite["ordner"] == str(start.parent / "Neubau")


def test_server_dieselbe_datei_noch_einmal_neue_fassung(server, start):
    s = _Server(server, start)
    s.lade("Wohnhaus.glb", _glb())
    s.warte()
    s.lade("Wohnhaus.glb", _glb(ZWEI_TEILE))
    s.warte()
    laden = s.get("/knoten/modell-laden")[1]["laden"]
    assert laden["stand"] == "geladen" and laden["ersetzt"] is True and laden["fassung"] == 2
    assert laden["bauteile"] == 2 and "Bilder und Skizzen bleiben" in laden["satz"]
    assert s.get("/knoten/mappe")[1]["fassung"] == 2


def test_server_archicad_satz_kommt_als_zustand(server, start):
    s = _Server(server, start)
    s.lade("Entwurf.pln", b"ArchiCAD")
    s.warte()
    laden = s.get("/knoten/modell-laden")[1]["laden"]
    assert laden["stand"] == "fehler"
    assert laden["satz"].startswith("ArchiCAD-Dateien sind ein geschlossenes Format.")
    assert s.klasse.zuletzt_geoeffnet is None, "ein Fehlschlag verschiebt nichts"


def test_server_nur_angemeldet(server, start):
    s = _Server(server, start)
    code, _ = s.lade("Neubau.glb", _glb(), angemeldet=False)
    assert code == 401
    assert s.get("/knoten/modell-laden", angemeldet=False)[0] == 401
    assert s.klasse.modell_laden is None and not (start.parent / "Neubau").exists()


def test_server_grenzen_name_und_formular(server, start, monkeypatch):
    s = _Server(server, start)
    code, antwort = s.lade("../boese.glb", _glb())
    assert code == 400 and "Dateiname" in antwort["fehler"]
    code, antwort = s._frage("POST", "/knoten/modell-laden", b"{}",
                             {"Content-Type": "application/json"})
    assert code == 400 and "Formular" in antwort["fehler"]
    monkeypatch.setattr(modellladen, "GROESSTE_DATEI_BYTE", 1)
    code, antwort = s._frage("POST", "/knoten/modell-laden", b"x" * (1024 * 1024 + 64),
                             {"Content-Type": "multipart/form-data; boundary=x"})
    assert code == 413 and "zu gross" in antwort["fehler"]
    assert s.klasse.modell_laden is None


def test_server_ohne_start_mappe_und_eine_zur_zeit(server, start):
    # 90d: ohne Start-Mappe wird angenommen (fester Rueckfall-Ordner, eigene Probe oben).

    s = _Server(server, start)
    s.klasse.modell_laden = {"kennung": "x", "stand": "laeuft", "datei": "gross.ifc",
                             "satz": "…", "schritt": "umwandeln", "begonnen": 0.0}
    code, antwort = s.lade("Neubau.glb", _glb())
    assert code == 409 and "gross.ifc" in antwort["fehler"]


def test_der_weg_steht_nicht_in_den_tafeln_der_app(server):
    """Die App ruft den Weg nicht — er gehört zur Knotenansicht, die über die Vorsilbe
    erkannt wird; ``Wege.swift`` (``tests/test_ipad_geruest.py``) muss ihn nicht kennen."""
    assert server.WEG_KNOTEN_MODELL_LADEN.startswith(server.WEG_KNOTEN + "/")
    assert server._ist_knotenweg(server.WEG_KNOTEN_MODELL_LADEN)
    assert server.WEG_KNOTEN_MODELL_LADEN not in server.WEGTAFEL
    assert server.WEG_KNOTEN_MODELL_LADEN not in server.WEGTAFEL_LESEN


# ======================================================== Wirt, Seite, Mac-App

def test_der_wirt_spricht_den_weg_des_servers(server):
    mappe = (WIRT / "mappe.ts").read_text(encoding="utf-8")
    haupt = (WIRT / "main.tsx").read_text(encoding="utf-8")
    weg = "./" + server.WEG_KNOTEN_MODELL_LADEN.removeprefix(server.WEG_KNOTEN + "/")
    assert f"fetch('{weg}', {{ method: 'POST'" in mappe
    assert f"fetch('{weg}')" in mappe and f"fetch('{weg}')" in haupt
    assert "formular.append('datei'" in mappe
    assert "registriereModellLaden(ladeWirt(" in haupt


def test_die_seite_traegt_die_gezeigte_mappe_ein():
    text = SEITE.read_text(encoding="utf-8")
    assert 'if (!ordner && d.ordner) $("ordner").value = d.ordner;' in text


def test_mac_app_oeffnet_den_dateiwaehler_der_seite():
    text = ARBEIT.read_text(encoding="utf-8")
    assert re.search(r"final class Flaechenlotse: NSObject, WKNavigationDelegate, WKUIDelegate", text)
    assert "ansicht.uiDelegate = lotse" in text
    assert re.search(r"func webView\(_ webView: WKWebView, runOpenPanelWith parameters: "
                     r"WKOpenPanelParameters,\s*initiatedByFrame frame: WKFrameInfo,\s*"
                     r"completionHandler: @escaping \(\[URL\]\?\) -> Void\)", text)
    assert "NSOpenPanel()" in text
    assert "completionHandler(antwort == .OK ? tafel.urls : nil)" in text
    # Jede Datei wählbar, auch die ArchiCAD-Datei (90c): keine Typbeschränkung am Wähler.
    assert "allowedContentTypes" not in text and "allowedFileTypes" not in text
