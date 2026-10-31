"""Die Skizze führt das Bild — auch in der Knotenansicht (Owner-Entscheid 96, 15.10.2026).

Bis zum 15.10.2026 konnte nur die Seite «aus Skizze rechnen». Die Knotenansicht bestellt seither
mit ``RenderScene.skizze`` ({quelle: "mappe", name, anweisung?}); der Server vermerkt die Mappe
neben dem Auftrag (nie im Browser), und der Abholer rechnet den Auftrag über DENSELBEN Weg wie
die Seite: :func:`aiimaging.arbeitsgang.rechne_skizze`.

Geprüft wird hier, ohne GPU, über den Produktweg Annehmen → Freigeben → Abholen:

* Der Nachrender bekommt die Skizze AUF IHRER UNTERLAGE und die Anweisung als Prompt.
* Das Ergebnis trägt das Bild, «nicht anwendbar» als Urteil, die Auskunft woraus es entstand,
  und auf dem Vorgabemodell «SKIZZE NICHT ANGEKOMMEN» zuvorderst im Grund.
* Ein Modell mit offener Lizenz (E128) bleibt markiert bis ins Ergebnis.
* Die Skizze ist danach «gerechnet», wie auf der Seite.
* Ein Auftrag ohne Skizze bleibt, was er war; eine fehlende oder verworfene Skizze sagt es.

Regel 3: Alles hier entsteht aus ein paar Bytes; Bildquelle, Nachrender und Prüfung sind echt,
Geometrie, Multipass, Bildstufe und Bildmodell Attrappen (Muster ``test_skizze_auf_unterlage``).
"""
from __future__ import annotations

import json
import struct
import zlib
from pathlib import Path

import pytest

from aiimaging import abholer, arbeitsgang, bildlesen, bildschreiben, bruecke, kette, knotenweg
from aiimaging import kosmo_szene, projekt
from aiimaging.kette import (ART_BILDQUELLE, ART_GEOMETRIE, ART_MULTIPASS, ART_NACHRENDER,
                             ART_QA, ART_RENDER)

ROT, BLAU = (255, 0, 0), (0, 0, 255)
KENNUNG = "vis-1790500000-5e1a00"


def _rgba_png(pfad, breite, hoehe, punkte, grund=(0, 0, 0, 0)) -> Path:
    roh = bytearray()
    for y in range(hoehe):
        roh.append(0)
        for x in range(breite):
            roh += bytes(punkte.get((x, y), grund))

    def block(art, nutz):
        return (struct.pack(">I", len(nutz)) + art + nutz
                + struct.pack(">I", zlib.crc32(art + nutz) & 0xFFFFFFFF))

    pfad = Path(pfad)
    pfad.parent.mkdir(parents=True, exist_ok=True)
    pfad.write_bytes(b"\x89PNG\r\n\x1a\n"
                     + block(b"IHDR", struct.pack(">IIBBBBB", breite, hoehe, 8, 6, 0, 0, 0))
                     + block(b"IDAT", zlib.compress(bytes(roh)))
                     + block(b"IEND", b""))
    return pfad


def _einfarbig(pfad, breite, hoehe, farbe) -> Path:
    pfad = Path(pfad)
    pfad.parent.mkdir(parents=True, exist_ok=True)
    return bildschreiben.schreibe_farb_png(pfad, [farbe] * (breite * hoehe), breite, hoehe)


class _Modell:
    """Das Bildmodell des Nachrenders — es rechnet nichts, es **liest**, was ankommt."""

    def __init__(self) -> None:
        self.auftraege: list[dict] = []
        self.eingaenge: list = []

    def __call__(self, parameter: dict) -> dict:
        self.auftraege.append(dict(parameter))
        self.eingaenge.append(bildlesen.lies_png_farben(parameter["beauty_png"]))
        _einfarbig(parameter["ausgabe_png"], 2, 2, (9, 9, 9))
        # A0065: meldet den bestellten Modus wie der echte Adapter (Engstelle in render.rendere).
        return {"bild_png": parameter["ausgabe_png"], "hinweise": [], "schritte_gerechnet": None,
                "modus_bestellt": parameter["modus"], "modus_gerechnet": parameter["modus"]}


def _tabelle(modell) -> dict:
    def geometrie(*, knoten, eingaben, out_dir):
        glb = Path(out_dir) / "modell.glb"
        glb.write_text("glb", encoding="utf-8")
        return {"glb_path": str(glb), "up_axis": "Y", "bbox": [[0, 0, 0], [8, 5, 3]]}

    def multipass(*, knoten, eingaben, out_dir):
        tiefe = bildschreiben.schreibe_graustufen_png(Path(out_dir) / "tiefe_norm.png",
                                                      [0.5] * 4, 2, 2)
        return {"status": "ok", "depth_png": str(tiefe),
                "beauty_png": str(_einfarbig(Path(out_dir) / "beauty.png", 2, 2, (5, 5, 5)))}

    def render(*, knoten, eingaben, out_dir):
        return {"status": "ok",
                "bild_png": str(_einfarbig(Path(out_dir) / "bild.png", 4, 4, BLAU))}

    return {ART_GEOMETRIE: geometrie, ART_MULTIPASS: multipass, ART_RENDER: render,
            ART_BILDQUELLE: kette.AUSFUEHRER[ART_BILDQUELLE],
            ART_NACHRENDER: kette.nachrender_ausfuehrer(modell=modell),
            ART_QA: kette.qa_ausfuehrer()}


@pytest.fixture
def mappe(tmp_path):
    """Eine Mappe mit Prüfung (qa an), einem Bild aus dem Modell und einer Skizze darauf."""
    js = json.dumps({"asset": {"version": "2.0", "generator": "Testfixture"}}).encode()
    js += b" " * (-len(js) % 4)
    block = struct.pack("<II", len(js), 0x4E4F534A) + js
    glb = tmp_path / "quelle" / "haus.glb"
    glb.parent.mkdir(parents=True, exist_ok=True)
    glb.write_bytes(struct.pack("<4sII", b"glTF", 2, 12 + len(block)) + block)
    wurzel = tmp_path / "Probemappe"
    arbeitsgang.lege_an(wurzel, glb, name="Probehaus",
                        einstellungen={"prompt": "Abendlicht", "seed": 7, "up_axis": "Y",
                                       "qa": True})
    # Die Unterlage ohne Prüfung — die echte Prüfung auf einem Bild aus dem Modell braucht
    # den Tiefenschätzer. Die Skizze darauf prüft «nicht anwendbar», ohne ihn.
    (unterlage,) = arbeitsgang.rechne(wurzel, ausfuehrer=_tabelle(_Modell()), qa=False)["bilder"]
    _rgba_png(wurzel / "skizze-a.png", 4, 4, {(1, 1): (*ROT, 255)})
    p = projekt.oeffne(wurzel)["projekt"]
    projekt.vermerke_skizze(p, skizze="skizze-a.png", ueber=unterlage, bemerkung="ein Vordach")
    projekt.speichere(p, wurzel)
    return wurzel


def _szene(**skizze) -> dict:
    s = {"schema": "kosmovis.render-scene/v1", "cameras": "auto",
         "render": {"resolution": [1600, 1000], "samples": 128, "faithful": 0.8},
         "style": {"mode": "none", "prompt": "Wohnhaus im Abendlicht"},
         "vis": {"skip": False, "backbone": skizze.pop("backbone", "z-image-turbo"),
                 "upscale": False},
         "geometry": {"format": "glb"}, "out": ""}
    if skizze:
        s["skizze"] = {"quelle": "mappe", **skizze}
    return s


def _glb(mappe) -> bytes:
    """Das Modell, das die Knotenansicht mitschickt — in Visbox das der Mappe."""
    return (Path(mappe).parent / "quelle" / "haus.glb").read_bytes()


def _bestellen_und_freigeben(ablage, mappe, szene) -> Path:
    zettel = knotenweg.lege_an(ablage, szene, _glb(mappe), "model.glb", kennung=KENNUNG,
                               mappe=Path(mappe).name, mappe_pfad=mappe)
    knotenweg.freigeben(ablage, KENNUNG, zettel["approval_token"])
    return Path(ablage) / KENNUNG


def _abholen(ordner, modell):
    return abholer.hole_einen(
        ordner, verarbeite=abholer.verarbeiter(_skizzen_ausfuehrer=_tabelle(modell)),
        darf_rechnen=lambda: (True, "frei"))


def _ergebnis(ordner) -> dict:
    return json.loads((Path(ordner) / bruecke.DATEI_ERGEBNIS).read_text(encoding="utf-8"))


# ======================================================================================
# 1 · Annehmen: die Mappe bleibt am Heim-PC
# ======================================================================================

def test_eine_skizze_vermerkt_ihre_mappe_neben_dem_auftrag_nie_im_laufzettel(tmp_path, mappe):
    ablage = tmp_path / "ablage"
    zettel = knotenweg.lege_an(ablage, _szene(name="skizze-a.png"), b"glTF", "model.glb",
                               kennung=KENNUNG, mappe=mappe.name, mappe_pfad=mappe)
    ordner = ablage / KENNUNG
    assert knotenweg.mappe_des_auftrags(ordner) == mappe.resolve()
    # Der Laufzettel nennt die Mappe beim Namen, ihren Pfad nicht (den Pfad der Ablage trug er
    # schon vorher unter `scene` — die Form der Bruecke, hier nicht geaendert).
    assert zettel["mappe"] == "Probemappe"
    assert str(mappe) not in json.dumps(zettel)
    assert str(mappe) not in json.dumps(knotenweg.lies(ablage, KENNUNG))
    # Die Datei ist nicht abrufbar: `artefakt` liefert nichts, was mit einem Punkt beginnt.
    with pytest.raises(knotenweg.KnotenwegError):
        knotenweg.artefakt(ablage, KENNUNG, knotenweg.DATEI_MAPPE)


def test_ohne_skizze_kein_vermerk_und_der_auftrag_wie_bisher(tmp_path, mappe):
    ablage = tmp_path / "ablage"
    knotenweg.lege_an(ablage, _szene(), b"glTF", "model.glb", kennung=KENNUNG,
                      mappe=mappe.name, mappe_pfad=mappe)
    assert not (ablage / KENNUNG / knotenweg.DATEI_MAPPE).exists()
    assert knotenweg.mappe_des_auftrags(ablage / KENNUNG) is None
    assert kosmo_szene.lies_szene(_szene() | {"geometry": {"path": "m.glb", "format": "glb"}})[
        "skizze"] is None


@pytest.mark.parametrize("fall,satz", [
    ("ohne_mappe", "nur aus einer offenen Mappe"),
    ("unbekannt", "steht nicht (mehr) in der Mappe «Probemappe»"),
    ("verworfen", "steht nicht (mehr) in der Mappe «Probemappe»"),
])
def test_eine_skizze_die_es_nicht_gibt_wird_beim_annehmen_mit_satz_abgewiesen(
        tmp_path, mappe, fall, satz):
    name = "skizze-weg.png" if fall == "unbekannt" else "skizze-a.png"
    if fall == "verworfen":
        p = projekt.oeffne(mappe)["projekt"]
        projekt.markiere_skizze(p, skizze="skizze-a.png", stand=projekt.SKIZZE_VERWORFEN)
        projekt.speichere(p, mappe)
    with pytest.raises(knotenweg.KnotenwegError) as fehler:
        knotenweg.lege_an(tmp_path / "ablage", _szene(name=name), b"glTF", "model.glb",
                          kennung=KENNUNG, mappe=mappe.name,
                          mappe_pfad=None if fall == "ohne_mappe" else mappe)
    assert satz in str(fehler.value)
    assert not (tmp_path / "ablage" / KENNUNG).exists()


# ======================================================================================
# 2 · Lesen: das Feld des Vertrags
# ======================================================================================

def _gelesen(**s) -> dict:
    szene = _szene() | {"geometry": {"path": "m.glb", "format": "glb"}} | s
    return kosmo_szene.lies_szene(szene)


def test_das_feld_skizze_wird_gelesen_und_nicht_als_unbekannt_abgewiesen():
    g = _gelesen(skizze={"quelle": "mappe", "name": "skizze-a.png",
                         "anweisung": "a wooden balcony"})
    assert g["maengel"] == ()
    assert g["skizze"]["name"] == "skizze-a.png"
    assert g["skizze"]["anweisung_original"] == "a wooden balcony"
    assert "skizze" in kosmo_szene.DURCHGEREICHT
    ohne = _gelesen(skizze={"quelle": "mappe", "name": "skizze-a.png"})
    assert ohne["maengel"] == () and ohne["skizze"]["anweisung"] is None


@pytest.mark.parametrize("skizze,s,teil", [
    ({"quelle": "upload", "name": "a.png"}, {}, "'skizze.quelle'"),
    ({"quelle": "mappe"}, {}, "'skizze.name'"),
    ({"quelle": "mappe", "name": "a.png", "anweisung": ""}, {}, "'skizze.anweisung'"),
    ({"quelle": "mappe", "name": "a.png", "bild": "data:"}, {}, "skizze.bild"),
    ({"quelle": "mappe", "name": "a.png"},
     {"cameras": [{"position": [0, 1, 9], "target": [0, 1, 0], "up_axis": "y"}]}, "'cameras'"),
    ({"quelle": "mappe", "name": "a.png"},
     {"vis": {"skip": True, "backbone": "z-image-turbo"}}, "'vis.skip: true'"),
    ({"quelle": "mappe", "name": "a.png"}, {"interior": {"rooms": "auto"}}, "'interior'"),
])
def test_was_mit_einer_skizze_nicht_geht_ist_ein_mangel(skizze, s, teil):
    g = _gelesen(skizze=skizze, **s)
    assert any(teil in m for m in g["maengel"]), g["maengel"]


def test_der_anfang_des_satzes_ist_derselbe_wie_in_der_kette():
    assert kette.HINWEIS_SKIZZE_NICHT_ANGEKOMMEN.startswith(
        kosmo_szene.SKIZZE_NICHT_ANGEKOMMEN_ANFANG)
    assert kette.HINWEIS_SKIZZE_EIGENER_START.startswith(kosmo_szene.SKIZZE_EIGENER_START_ANFANG)


# ======================================================================================
# 3 · Rechnen: derselbe Weg wie die Seite
# ======================================================================================

def test_die_skizze_fuehrt_das_bild_ueber_den_weg_der_seite(tmp_path, mappe):
    ordner = _bestellen_und_freigeben(
        tmp_path / "ablage", mappe, _szene(name="skizze-a.png", anweisung="a wooden balcony"))
    modell = _Modell()
    antwort = _abholen(ordner, modell)
    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort["grund"]

    # Der Nachrender bekam die Skizze AUF IHRER UNTERLAGE: blau, mit dem roten Strich.
    (farben, breite, hoehe) = modell.eingaenge[-1]
    assert (breite, hoehe) == (4, 4)
    assert farben[1 * 4 + 1] == ROT and farben[0] == BLAU
    assert modell.auftraege[-1]["prompt"] == "a wooden balcony"
    # ... und gerechnet wurde in IHRER Mappe, nicht in der Ablage des Auftrags.
    assert modell.auftraege[-1]["beauty_png"].startswith(str(mappe))

    ergebnis = _ergebnis(ordner)
    assert len(ergebnis["images"]) == 1
    assert (ordner / ergebnis["images"][0]).is_file()
    verdict = ergebnis["qa"]["verdict"]
    assert verdict["passed"] is False
    # Auf dem Vorgabemodell geht die Skizze seit dem 25.10.2026 ueber den eigenen Start (Stärke aus
    # dem Register) — zuvorderst gesagt, mit «ungemessen» statt «nicht angekommen».
    assert verdict["reason"].startswith(kosmo_szene.SKIZZE_EIGENER_START_ANFANG)
    # Entscheid 154 (nach auf-20261025-371): 0,55 aus dem Register.
    assert modell.auftraege[-1]["bildeingang_staerke"] == 0.55
    assert "NICHT ANWENDBAR (Handeingriff)" in verdict["reason"]
    assert any(h.startswith("AUS SKIZZE GERECHNET: 'skizze-a.png'") for h in verdict["hinweise"])
    assert ergebnis["lieferstatus"] == "geliefert"
    assert ergebnis["qa_je_kamera"][0]["kamera"] == abholer.KAMERA_SKIZZE
    assert ergebnis["engine_used"] == "z-image-turbo"
    assert "engine_license_open" not in ergebnis

    # Wie auf der Seite: die Skizze ist «gerechnet», ihr Bild steht in der Mappe.
    p = projekt.oeffne(mappe)["projekt"]
    letzte = [e for e in p["skizzen"] if e["skizze"] == "skizze-a.png"][-1]
    assert letzte["stand"] == projekt.SKIZZE_GERECHNET
    befund = abholer.lies_befund(ordner)
    assert befund["skizze"]["anweisung_aus"] == "bestellung"
    assert str(tmp_path) not in json.dumps(befund)


def test_ohne_anweisung_gilt_die_bemerkung_der_skizze(tmp_path, mappe):
    ordner = _bestellen_und_freigeben(tmp_path / "ablage", mappe, _szene(name="skizze-a.png"))
    modell = _Modell()
    assert _abholen(ordner, modell)["tat"] == abholer.TAT_VERARBEITET
    assert modell.auftraege[-1]["prompt"] == "a canopy"  # übersetzt seit Ergebnis 352 S3
    assert any("Anweisung aus der Bemerkung der Skizze" in h
               for h in _ergebnis(ordner)["qa"]["verdict"]["hinweise"])


def test_ein_modell_mit_offener_lizenz_bleibt_markiert_bis_ins_ergebnis(tmp_path, mappe):
    ordner = _bestellen_und_freigeben(
        tmp_path / "ablage", mappe,
        _szene(name="skizze-a.png", anweisung="a balcony", backbone="qwen-image-2.1"))
    modell = _Modell()
    antwort = _abholen(ordner, modell)
    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort["grund"]
    ergebnis = _ergebnis(ordner)
    assert ergebnis["engine_used"] == "qwen-image-2.1"
    assert ergebnis["engine_license_open"] is True
    # Ungemessen ist nicht «kommt nicht an»: kein solcher Satz.
    assert kosmo_szene.SKIZZE_NICHT_ANGEKOMMEN_ANFANG not in ergebnis["qa"]["verdict"]["reason"]


def test_eine_skizze_die_waehrend_des_wartens_verworfen_wurde_sagt_es(tmp_path, mappe):
    ordner = _bestellen_und_freigeben(tmp_path / "ablage", mappe, _szene(name="skizze-a.png"))
    p = projekt.oeffne(mappe)["projekt"]
    projekt.markiere_skizze(p, skizze="skizze-a.png", stand=projekt.SKIZZE_VERWORFEN)
    projekt.speichere(p, mappe)
    antwort = _abholen(ordner, _Modell())
    assert antwort["tat"] == abholer.TAT_FEHLER
    zettel = json.loads((ordner / bruecke.DATEI_LAUFZETTEL).read_text(encoding="utf-8"))
    assert zettel["status"] == bruecke.STATUS_ERROR
    assert "ist verworfen" in json.dumps(zettel, ensure_ascii=False)


def test_ein_auftrag_mit_skizze_aber_ohne_mappe_sagt_warum(tmp_path, mappe):
    ordner = _bestellen_und_freigeben(tmp_path / "ablage", mappe, _szene(name="skizze-a.png"))
    (ordner / knotenweg.DATEI_MAPPE).unlink()
    antwort = _abholen(ordner, _Modell())
    assert antwort["tat"] == abholer.TAT_FEHLER
    assert abholer.SATZ_SKIZZE_OHNE_MAPPE in antwort["grund"]


def test_ein_auftrag_ohne_skizze_geht_nicht_in_den_skizzenweg(tmp_path, mappe):
    """Gegenprobe: ohne `skizze` ruft der Abholer `rechne_skizze` nie."""
    gerufen = []
    verarbeite = abholer.verarbeiter(
        _rechne_skizze=lambda *a, **k: gerufen.append(1),
        _multipass=lambda *a, **k: (_ for _ in ()).throw(RuntimeError("Modellweg erreicht")))
    zettel = knotenweg.lege_an(tmp_path / "ablage", _szene(), _glb(mappe), "model.glb",
                               kennung=KENNUNG, mappe=mappe.name, mappe_pfad=mappe)
    knotenweg.freigeben(tmp_path / "ablage", KENNUNG, zettel["approval_token"])
    antwort = abholer.hole_einen(tmp_path / "ablage" / KENNUNG, verarbeite=verarbeite,
                                 darf_rechnen=lambda: (True, "frei"))
    assert gerufen == []
    assert "Modellweg erreicht" in antwort["grund"]


def test_der_server_gibt_den_pfad_der_mappe_an_lege_an(tmp_path, monkeypatch):
    """Der Server reicht den Pfad durch — als Argument, nie in die Antwort."""
    import importlib.util
    import sys
    flaeche = Path(__file__).resolve().parents[1] / "oberflaeche"
    sys.path.insert(0, str(flaeche))
    try:
        import server
    finally:
        sys.path.remove(str(flaeche))
    quelle = Path(server.__file__).read_text(encoding="utf-8")
    assert "mappe_pfad=aus_mappe or None" in quelle
    assert importlib.util.find_spec("aiimaging.knotenweg") is not None
