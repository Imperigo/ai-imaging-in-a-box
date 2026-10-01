"""Die Vorführmappe (``tools/vorfuehrmappe.py``) — **jeder Schalter gedrückt**, und die
Mappe gegen beide Seiten gehalten: gegen die Fläche des Servers, deren Felder sie trägt, und
gegen die App, die sie liest.

Was hier hält:

1. ``--beispiel`` legt eine Mappe aus Platzhaltern an, mit jeder Art von Zeichen, und die
   Mappe im Repo (``ipad/VisboxMac/Beispielmappe/``) ist **genau** ihre Ausgabe — die
   Kern-Probe der App liest also eine Mappe aus dem Werkzeug, keine von Hand geschriebene.
2. Die Felder je Bild sind die der Fläche (``server._bild_fuer_die_flaeche``) und die, die
   ``Mappenbild`` in der App liest — eine Liste, an beiden Seiten bewacht.
3. ``--ordner`` nimmt die Felder aus ``server.sicht``, kopiert nur PNG und streift deren
   Begleitdaten ab, und lässt **keinen Pfad, keinen Rechner- und keinen Benutzernamen**
   durch (Regel 3).
"""
from __future__ import annotations

import importlib.util
import json
import re
import struct
import sys
import zlib
from pathlib import Path

import pytest

WURZEL = Path(__file__).resolve().parents[1]
WERKZEUG = WURZEL / "tools" / "vorfuehrmappe.py"
ABGELEGT = WURZEL / "ipad" / "VisboxMac" / "Beispielmappe"
PRUEFZEICHEN_SWIFT = WURZEL / "ipad" / "Visbox.swiftpm" / "Kern" / "Pruefzeichen.swift"

sys.path.insert(0, str(WURZEL / "src"))
from aiimaging import bildlesen, bildschreiben, projekt  # noqa: E402


@pytest.fixture(scope="module")
def vm():
    spez = importlib.util.spec_from_file_location("vorfuehrmappe_pruefling", WERKZEUG)
    modul = importlib.util.module_from_spec(spez)
    spez.loader.exec_module(modul)
    return modul


@pytest.fixture(scope="module")
def server(vm):
    return vm._server()


def _lies(ordner: Path) -> dict:
    return json.loads((ordner / "vorfuehrmappe.json").read_text(encoding="utf-8"))


def _bloecke(roh: bytes) -> list[bytes]:
    arten, stelle = [], 8
    while stelle < len(roh):
        laenge = struct.unpack(">I", roh[stelle:stelle + 4])[0]
        arten.append(roh[stelle + 4:stelle + 8])
        stelle += 12 + laenge
    return arten


# ============================================================ 1 · --beispiel

def test_beispiel_legt_eine_mappe_mit_jeder_art_von_zeichen_an(vm, tmp_path):
    ziel = tmp_path / "bsp"
    assert vm.main(["--beispiel", str(ziel)]) == 0
    m = _lies(ziel)
    assert m["schema"] == vm.SCHEMA == "visbox.vorfuehrmappe/v1"
    assert m["platzhalter"] is True and m["gerechnet_am"] is None, (
        "Platzhalter sind an keinem Tag gerechnet — ein Datum behauptete eine Messung")
    assert "Platzhalter" in m["satz"]
    arten = {(b["flaeche"]["zeichen"], b["flaeche"]["entwurf"],
              b["flaeche"]["skizze_nicht_angekommen"]) for b in m["bilder"]}
    assert ("bestanden", False, None) in arten
    assert ("durchgefallen", False, None) in arten
    assert ("nicht-gemessen", False, True) in arten, "ungemessen mit Vorbehalt"
    assert ("nicht-gemessen", True, None) in arten, "Entwurf"
    for b in m["bilder"]:
        assert b["gerechnet_am"] is None
        assert set(b["flaeche"]) == set(vm.FELDER_DER_FLAECHE)
        assert b["flaeche"]["bild"] == b["datei"]
        roh = (ziel / b["datei"]).read_bytes()
        assert roh.startswith(vm.PNG_KENNUNG)
        assert set(_bloecke(roh)) <= vm.PNG_BLOECKE
        # GRAU, und nur grau: Ein Platzhalter darf nicht wie ein gerechnetes Bild aussehen.
        farben = bildlesen.lies_png_farben(ziel / b["datei"])[0]
        assert all(r == g == bl for r, g, bl in farben)


def test_beispiel_mit_titel(vm, tmp_path):
    assert vm.main(["--beispiel", str(tmp_path / "b"), "--titel", "Würfel am Hang"]) == 0
    assert _lies(tmp_path / "b")["titel"] == "Würfel am Hang"


def test_die_abgelegte_beispielmappe_ist_die_ausgabe_des_werkzeugs(vm, tmp_path):
    """Die Mappe unter ``ipad/VisboxMac/Beispielmappe/`` liest die Kern-Probe der App
    (``VorfuehrmappeTests``). Sie muss die Ausgabe von ``--beispiel`` sein — sonst prüfte die
    App eine Mappe, die das Werkzeug nicht mehr erzeugt.

    Die Bilder werden **nach Bildpunkten** verglichen, nicht nach Bytes: Eine andere
    zlib-Fassung packt dieselben Punkte anders, und das ist keine andere Mappe."""
    assert vm.main(["--beispiel", str(tmp_path / "neu")]) == 0
    neu, alt = _lies(tmp_path / "neu"), _lies(ABGELEGT)
    assert neu == alt, "Beispielmappe neu erzeugen: python3 tools/vorfuehrmappe.py --beispiel ipad/VisboxMac/Beispielmappe"
    assert sorted(p.name for p in ABGELEGT.iterdir()) == sorted(
        p.name for p in (tmp_path / "neu").iterdir())
    for b in neu["bilder"]:
        assert (bildlesen.lies_png_farben(ABGELEGT / b["datei"])
                == bildlesen.lies_png_farben(tmp_path / "neu" / b["datei"])), b["datei"]


def test_die_abgelegte_beispielmappe_ist_klein():
    """Klein genug für das Repo und das App-Bündel — Platzhalter, keine Bilder."""
    assert sum(p.stat().st_size for p in ABGELEGT.iterdir()) < 64 * 1024


def test_beispiel_nimmt_kein_nach_kein_bild_und_keinen_blick(vm, tmp_path, capsys):
    for zusatz in (["--nach", str(tmp_path / "x")], ["--bild", "a.png"],
                   ["--blick", "a.png=Blick"]):
        assert vm.main(["--beispiel", str(tmp_path / "b"), *zusatz]) == 2, zusatz
        assert "gehören zu --ordner" in capsys.readouterr().err
    assert not (tmp_path / "b").exists()


def test_ohne_quelle_bricht_argparse_ab(vm):
    with pytest.raises(SystemExit):
        vm.main([])
    with pytest.raises(SystemExit):
        vm.main(["--ordner", "a", "--beispiel", "b"])


# ============================================ 2 · die Felder, an beiden Seiten bewacht

def test_die_felder_sind_die_der_flaeche(vm, server):
    """Jedes Feld, das die Fläche je Bild liefert, geht mit oder steht mit Grund in
    ``NICHT_IN_DIE_MAPPE`` — ein neues Feld des Servers fällt hier auf."""
    felder = set(server._bild_fuer_die_flaeche({"bild": "a.png"}))
    assert set(vm.FELDER_DER_FLAECHE) | set(vm.NICHT_IN_DIE_MAPPE) == felder
    assert not set(vm.FELDER_DER_FLAECHE) & set(vm.NICHT_IN_DIE_MAPPE)


def test_die_felder_sind_die_die_die_app_liest(vm):
    """``Mappenbild.init`` in ``Pruefzeichen.swift`` — gelesen als Text, die Gegenseite."""
    text = PRUEFZEICHEN_SWIFT.read_text(encoding="utf-8")
    rumpf = re.search(r"public struct Mappenbild\b.*?public init\(_ o: \[String: JSONWert\]\) \{"
                      r"(.*?)\n    \}", text, re.S)
    assert rumpf, "Mappenbild.init nicht gefunden"
    gelesen = set(re.findall(r'o\["(\w+)"\]', rumpf.group(1)))
    assert gelesen - {"vorhanden"} == set(vm.FELDER_DER_FLAECHE), (
        f"die App liest {sorted(gelesen)}, die Mappe trägt {sorted(vm.FELDER_DER_FLAECHE)}")


def test_das_zeichen_kommt_vom_server_nicht_aus_dem_werkzeug(vm, server, monkeypatch, tmp_path):
    """Ändert die Fläche ihre Ableitung, ändert sich die Mappe mit — keine Abschrift."""
    echt = server._bild_fuer_die_flaeche

    def anders(eintrag, *a, **k):
        aus = echt(eintrag, *a, **k)
        aus["satz"] = "VON DER FLÄCHE"
        return aus

    monkeypatch.setattr(vm, "_server", lambda: server)
    monkeypatch.setattr(server, "_bild_fuer_die_flaeche", anders)
    mappe, _ = vm.beispiel()
    assert {b["flaeche"]["satz"] for b in mappe["bilder"]} == {"VON DER FLÄCHE"}


# ================================================================ 3 · --ordner

def _png_mit_text(ziel: Path, text: str) -> None:
    """Ein graues PNG mit einem tEXt-Block — wie ein Bildprogramm Pfade hineinschreibt."""
    bildschreiben.schreibe_farb_png(ziel, [(100, 100, 100)] * 12, 4, 3)
    roh = ziel.read_bytes()
    nutzlast = b"Quelle\x00" + text.encode("latin-1")
    block = (struct.pack(">I", len(nutzlast)) + b"tEXt" + nutzlast
             + struct.pack(">I", zlib.crc32(b"tEXt" + nutzlast) & 0xFFFFFFFF))
    ziel.write_bytes(roh[:-12] + block + roh[-12:])


@pytest.fixture()
def mappe_ordner(tmp_path):
    """Ein synthetisches Projekt mit drei Bildern (eines ohne Datei) — Regel 3."""
    ordner = tmp_path / "projekt"
    ordner.mkdir()
    modell = tmp_path / "modell.glb"
    modell.write_bytes(b"glTF")
    p = projekt.neu(ordner, modell, name="Testbau")
    (ordner / "bilder").mkdir()
    _png_mit_text(ordner / "bilder" / "lauf-a.png", "/home/jemand/geheim/lauf-a.png")
    _png_mit_text(ordner / "lauf-b.png", "Rechner: irgendwo")
    projekt.vermerke_bild(p, bild="bilder/lauf-a.png", schicht="ai-imaging-layer", urteil=True,
                          score=0.84, schwelle=0.65,
                          herkunft={"grund": "gemessen", "prompt": "a house"})
    projekt.vermerke_bild(p, bild="lauf-b.png", schicht="ai-imaging-layer", urteil=None,
                          herkunft={"grund": "NICHT GEMESSEN: kein Maskenweg.",
                                    "skizze": "skizze-1.png",
                                    "unterlage": {"bild": "bilder/lauf-a.png",
                                                  "gestreckt": False, "grund": ""},
                                    "messung": {"hinweise": []}})
    projekt.vermerke_bild(p, bild="weg.png", schicht="ai-imaging-layer", urteil=False,
                          score=0.4, schwelle=0.65)
    for b in p["bilder"]:
        b["erzeugt"] = "2026-10-28T13:00:00Z"
    p["bilder"][1]["erzeugt"] = "2026-10-27T09:00:00Z"
    projekt.speichere(p, ordner)
    return ordner


def test_ordner_nimmt_die_felder_der_flaeche_und_streift_die_begleitdaten_ab(
        vm, server, mappe_ordner, tmp_path, capsys):
    ziel = tmp_path / "mappe"
    assert vm.main(["--ordner", str(mappe_ordner), "--nach", str(ziel)]) == 0
    assert "übersprungen, die Datei fehlt: weg.png" in capsys.readouterr().err
    m = _lies(ziel)
    assert m["platzhalter"] is False
    assert m["titel"] == "Testbau", "ohne --titel der Name des Projekts"
    assert m["gerechnet_am"] == "2026-10-28"
    assert [b["datei"] for b in m["bilder"]] == ["lauf-a.png", "lauf-b.png"], "nur Dateinamen"
    a, b = m["bilder"]
    assert a["gerechnet_am"] == "2026-10-28" and b["gerechnet_am"] == "2026-10-27"
    assert "28.10.2026" in a["satz"]
    # DIESELBEN FELDER WIE DIE FLAECHE — bis auf den Namen, der zum Dateinamen wird.
    live = {e["bild"]: e for e in server.sicht(mappe_ordner)["bilder"]}
    for eintrag, name in ((a, "bilder/lauf-a.png"), (b, "lauf-b.png")):
        erwartet = {k: live[name][k] for k in vm.FELDER_DER_FLAECHE}
        erwartet["bild"] = eintrag["datei"]
        erwartet["vorher"] = eintrag["flaeche"]["vorher"]
        assert eintrag["flaeche"] == erwartet
    assert a["flaeche"]["zeichen"] == "bestanden" and a["flaeche"]["score"] == 0.84
    assert b["flaeche"]["zeichen"] == "nicht-gemessen"
    # DAS VORHER, ALS DATEINAME DER MAPPE: Die Unterlage geht mit, also zeigt es auf sie.
    assert live["lauf-b.png"]["vorher"] == "bilder/lauf-a.png"
    assert b["flaeche"]["vorher"] == "lauf-a.png"
    text = (ziel / "vorfuehrmappe.json").read_text(encoding="utf-8")
    assert "herkunft" not in text and "a house" not in text and str(mappe_ordner) not in text
    for datei in ("lauf-a.png", "lauf-b.png"):
        roh = (ziel / datei).read_bytes()
        assert b"tEXt" not in _bloecke(roh) and b"geheim" not in roh and b"Rechner" not in roh
        assert bildlesen.lies_png_farben(ziel / datei)[0] == [(100, 100, 100)] * 12


def test_ordner_mit_bild_waehlt_und_ordnet(vm, mappe_ordner, tmp_path):
    ziel = tmp_path / "mappe"
    assert vm.main(["--ordner", str(mappe_ordner), "--nach", str(ziel),
                    "--bild", "lauf-b.png", "bilder/lauf-a.png"]) == 0
    m = _lies(ziel)
    assert [b["datei"] for b in m["bilder"]] == ["lauf-b.png", "lauf-a.png"]


def test_ordner_mit_bild_das_fehlt_bricht_ab(vm, mappe_ordner, tmp_path, capsys):
    ziel = tmp_path / "mappe"
    assert vm.main(["--ordner", str(mappe_ordner), "--nach", str(ziel),
                    "--bild", "gibt-es-nicht.png"]) == 2
    assert "Nicht in der Mappe: gibt-es-nicht.png" in capsys.readouterr().err
    # GENANNT UND OHNE DATEI: kein stilles Überspringen, wenn jemand es ausdrücklich will.
    assert vm.main(["--ordner", str(mappe_ordner), "--nach", str(ziel), "--bild", "weg.png"]) == 2
    assert "gibt es nicht" in capsys.readouterr().err
    assert not ziel.exists()


def test_ordner_mit_blick_und_titel(vm, mappe_ordner, tmp_path, capsys):
    ziel = tmp_path / "mappe"
    assert vm.main(["--ordner", str(mappe_ordner), "--nach", str(ziel), "--titel", "Würfel",
                    "--blick", "bilder/lauf-a.png=Blick Süd-Ost",
                    "--blick", "lauf-b.png=Blick vom Hof"]) == 0
    m = _lies(ziel)
    assert m["titel"] == "Würfel"
    assert [b["blick"] for b in m["bilder"]] == ["Blick Süd-Ost", "Blick vom Hof"]
    assert vm.main(["--ordner", str(mappe_ordner), "--nach", str(tmp_path / "x"),
                    "--blick", "ohne-gleich"]) == 2
    assert "NAME=TEXT" in capsys.readouterr().err
    assert vm.main(["--ordner", str(mappe_ordner), "--nach", str(tmp_path / "x"),
                    "--blick", "weg.png=Blick"]) == 2
    assert "nicht mitgeht" in capsys.readouterr().err


def test_ordner_ohne_nach_bricht_ab(vm, mappe_ordner, capsys):
    assert vm.main(["--ordner", str(mappe_ordner)]) == 2
    assert "--nach" in capsys.readouterr().err


def test_ordner_ohne_projekt_bricht_mit_dem_satz_der_bibliothek_ab(vm, tmp_path, capsys):
    assert vm.main(["--ordner", str(tmp_path), "--nach", str(tmp_path / "m")]) == 2
    assert "kein Projekt" in capsys.readouterr().err


def test_regel3_ein_pfad_im_satz_haelt_die_mappe_auf(vm, mappe_ordner, tmp_path, capsys):
    """Der Satz eines ungemessenen Bildes kommt aus seiner Herkunft — und kann einen Pfad
    tragen. Dann wird **nichts** geschrieben, und das Feld steht in der Meldung."""
    p = projekt.oeffne(mappe_ordner)["projekt"]
    p["bilder"][1]["herkunft"]["grund"] = "NICHT GEMESSEN: Blender fehlt unter /opt/blender/bin."
    projekt.speichere(p, mappe_ordner)
    ziel = tmp_path / "mappe"
    assert vm.main(["--ordner", str(mappe_ordner), "--nach", str(ziel)]) == 2
    fehler = capsys.readouterr().err
    assert "Regel 3" in fehler and "bilder[1].flaeche.satz" in fehler and "absoluter Pfad" in fehler
    assert not ziel.exists()


@pytest.mark.parametrize("text, erwartet", [
    ("/home/jemand/x", "absoluter Pfad"),
    ("liegt in ~/mappe", "heimrelativer Pfad"),
    (r"C:\Users\x", "Laufwerkspfad"),
    (r"\\server\freigabe\x", "Netzpfad"),
])
def test_regel3_findet_jede_pfadform(vm, text, erwartet):
    assert any(erwartet in f for f in vm.regel3_funde({"a": [text]}))


def test_regel3_laesst_gewoehnliche_saetze_durch(vm):
    for text in ("BESTANDEN · 0.84/0.65", "und/oder", "Blick Süd-Ost", "Entwurf — nicht geprüft",
                 "2026-10-28T13:00:00Z"):
        assert vm.regel3_funde(text) == [], text


def test_regel3_findet_rechner_und_benutzernamen(vm, tmp_path):
    kennungen = [("rechner-im-keller", "der Rechnername"), ("jemand", "der Benutzername")]
    assert vm.regel3_funde("gerechnet auf rechner-im-keller", kennungen) == [
        "Text: der Rechnername"]
    assert vm.regel3_funde({"jemand": 1}, kennungen) == ["jemand: der Benutzername"]
    assert vm.regel3_funde("jemandes Haus", kennungen) == [], "nur ganze Wörter"
    # UND DIE DER EIGENEN MASCHINE werden wirklich gesucht.
    gesucht = dict((w, t) for t, w in vm._kennungen_der_maschine(tmp_path))
    assert gesucht["der Projektordner"] == str(tmp_path.resolve())


def test_nur_png_geht_in_die_mappe(vm, mappe_ordner, tmp_path, capsys):
    p = projekt.oeffne(mappe_ordner)["projekt"]
    (mappe_ordner / "foto.jpg").write_bytes(b"\xff\xd8\xff")
    projekt.vermerke_bild(p, bild="foto.jpg", schicht="ai-imaging-layer")
    projekt.speichere(p, mappe_ordner)
    assert vm.main(["--ordner", str(mappe_ordner), "--nach", str(tmp_path / "m"),
                    "--bild", "foto.jpg"]) == 2
    assert "nur PNG" in capsys.readouterr().err


def test_ohne_begleitdaten_weist_kaputtes_ab(vm):
    with pytest.raises(vm.MappenFehler):
        vm.ohne_begleitdaten(b"GIF89a")
    with pytest.raises(vm.MappenFehler):
        vm.ohne_begleitdaten(vm.PNG_KENNUNG + struct.pack(">I", 999) + b"IHDR" + b"\0" * 8)


# ======================================================== 4 · nichts Fremdes überschreiben

def test_ein_fremder_ordner_wird_nicht_ueberschrieben(vm, tmp_path, capsys):
    ziel = tmp_path / "fremd"
    ziel.mkdir()
    (ziel / "notiz.txt").write_text("bleibt")
    assert vm.main(["--beispiel", str(ziel)]) == 2
    assert "nichts überschrieben" in capsys.readouterr().err
    assert sorted(p.name for p in ziel.iterdir()) == ["notiz.txt"]


def test_eine_fruehere_mappe_wird_ersetzt_aber_nichts_daneben(vm, mappe_ordner, tmp_path, capsys):
    ziel = tmp_path / "mappe"
    assert vm.main(["--beispiel", str(ziel)]) == 0
    assert vm.main(["--ordner", str(mappe_ordner), "--nach", str(ziel)]) == 0
    assert sorted(p.name for p in ziel.iterdir()) == ["lauf-a.png", "lauf-b.png",
                                                       "vorfuehrmappe.json"], "alte Platzhalter weg"
    (ziel / "notiz.txt").write_text("fremd")
    assert vm.main(["--beispiel", str(ziel)]) == 2
    assert "mehr als die frühere Vorführmappe" in capsys.readouterr().err
    assert (ziel / "lauf-a.png").exists(), "abgewiesen heisst: nichts gelöscht"


def test_gleiche_dateinamen_aus_verschiedenen_laeufen_bekommen_eine_nummer(vm, tmp_path):
    """Die Bildstufe nennt ihr Bild nach dem Startwert (``render_0.png``), jeder Lauf in
    seinem eigenen Ordner — flach in der Mappe hiessen zwei Blicke gleich."""
    ordner = tmp_path / "projekt"
    ordner.mkdir()
    (tmp_path / "m.glb").write_bytes(b"glTF")
    p = projekt.neu(ordner, tmp_path / "m.glb", name="Testbau")
    for lauf in ("lauf-1", "lauf-2", "lauf-3"):
        (ordner / lauf).mkdir()
        bildschreiben.schreibe_farb_png(ordner / lauf / "render_0.png", [(9, 9, 9)] * 4, 2, 2)
        projekt.vermerke_bild(p, bild=f"{lauf}/render_0.png", schicht="ai-imaging-layer")
    projekt.speichere(p, ordner)
    assert vm.main(["--ordner", str(ordner), "--nach", str(tmp_path / "m")]) == 0
    m = _lies(tmp_path / "m")
    assert [b["datei"] for b in m["bilder"]] == ["render_0.png", "render_0-2.png", "render_0-3.png"]
    assert [b["flaeche"]["bild"] for b in m["bilder"]] == [b["datei"] for b in m["bilder"]]
