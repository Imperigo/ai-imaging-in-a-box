"""Die Skizze kommt **auf ihrer Unterlage** beim Nachrender an — über den Produktweg.

Befund vom 22.09.2026: ``arbeitsgang.rechne_skizze`` gab die Zeichnung **allein** als
Eingangsbild an den Nachrender (``kette.haenge_nachrender_an(eingangsbild=<skizze>)``).
Die App liefert Striche auf durchsichtigem Grund (1536 x 1024), mit ``ueber`` = dem Bild
darunter; die Bildstufe liest das Ausgangsbild ohne Alpha, und durchsichtig wurde
**schwarz**. Das Bild, auf das gezeichnet wurde, kam gar nicht an.

Geprüft wird hier, was der Nachrender **wirklich bekommt**: Ein Bildmodell-Ersatz liest
die Datei, die ihm als ``beauty_png`` übergeben wird, Bildpunkt für Bildpunkt — über
``rechne_skizze`` mit echter Bildquelle und echtem Nachrender. Nur Geometrie und Multipass
sind Attrappen.

Regel 3: Alle Bilder entstehen hier aus ein paar Bytes.
"""
from __future__ import annotations

import json
import struct
import zlib
from pathlib import Path

import pytest

from aiimaging import arbeitsgang, bildlesen, bildschreiben, kette, projekt
from aiimaging.kette import (ART_BILDQUELLE, ART_GEOMETRIE, ART_MULTIPASS, ART_NACHRENDER,
                             ART_QA, ART_RENDER)

ROT, BLAU = (255, 0, 0), (0, 0, 255)
NACHRENDER = f"{arbeitsgang.SKIZZEN_VORSATZ}-{kette.KNOTEN_NACHRENDER}"


# ======================================================================================
# Werkzeug
# ======================================================================================

def _rgba_png(pfad, breite: int, hoehe: int, punkte: dict,
              grund=(0, 0, 0, 0)) -> Path:
    """Ein RGBA-PNG (Farbtyp 6) wie aus der App: durchsichtiger Grund (PencilKit schreibt
    dort 0,0,0,0), und an den Stellen aus ``punkte`` ``{(x, y): (r, g, b, a)}``."""
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


def _einfarbig(pfad, breite: int, hoehe: int, farbe) -> Path:
    pfad = Path(pfad)
    pfad.parent.mkdir(parents=True, exist_ok=True)
    return bildschreiben.schreibe_farb_png(pfad, [farbe] * (breite * hoehe), breite, hoehe)


class _Modell:
    """Das Bildmodell des Nachrenders — es rechnet nichts, es **liest**, was ankommt."""

    def __init__(self) -> None:
        self.eingaenge: list[tuple[list, int, int]] = []

    def __call__(self, parameter: dict) -> dict:
        self.eingaenge.append(bildlesen.lies_png_farben(parameter["beauty_png"]))
        _einfarbig(parameter["ausgabe_png"], 2, 2, (9, 9, 9))
        return {"bild_png": parameter["ausgabe_png"], "hinweise": [],
                "schritte_gerechnet": None}


def _tabelle(modell, *, unterlage=(4, 4, BLAU)) -> dict:
    """Geometrie, Multipass und die Bildstufe aus dem Modell als Attrappen; Bildquelle,
    Nachrender und Prüfung ECHT. Die Bildstufe malt die Unterlage: einfarbig."""
    breite, hoehe, farbe = unterlage

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
                "bild_png": str(_einfarbig(Path(out_dir) / "bild.png", breite, hoehe, farbe))}

    return {ART_GEOMETRIE: geometrie, ART_MULTIPASS: multipass, ART_RENDER: render,
            ART_BILDQUELLE: kette.AUSFUEHRER[ART_BILDQUELLE],
            ART_NACHRENDER: kette.nachrender_ausfuehrer(modell=modell),
            ART_QA: kette.qa_ausfuehrer()}


@pytest.fixture
def mappe(tmp_path):
    js = json.dumps({"asset": {"version": "2.0", "generator": "Testfixture"}}).encode()
    js += b" " * (-len(js) % 4)
    block = struct.pack("<II", len(js), 0x4E4F534A) + js
    glb = tmp_path / "quelle" / "haus.glb"
    glb.parent.mkdir(parents=True, exist_ok=True)
    glb.write_bytes(struct.pack("<4sII", b"glTF", 2, 12 + len(block)) + block)
    wurzel = tmp_path / "projekt"
    arbeitsgang.lege_an(wurzel, glb, name="Probehaus",
                        einstellungen={"prompt": "Abendlicht", "seed": 7, "up_axis": "Y",
                                       "qa": False})
    return wurzel


def _unterlage_rechnen(mappe, **wie) -> str:
    """Ein Bild aus dem Modell in die Mappe — die Unterlage, auf die gezeichnet wird."""
    ergebnis = arbeitsgang.rechne(mappe, ausfuehrer=_tabelle(_Modell(), **wie))
    (name,) = ergebnis["bilder"]
    return name


def _skizze_ablegen(mappe, name, punkte, *, ueber, breite=4, hoehe=4,
                    grund=(0, 0, 0, 0)) -> str:
    """Wie die Fläche: Datei schreiben, in der Mappe vermerken, speichern."""
    _rgba_png(Path(mappe) / name, breite, hoehe, punkte, grund)
    p = projekt.oeffne(mappe)["projekt"]
    projekt.vermerke_skizze(p, skizze=name, ueber=ueber, bemerkung="ein Vordach")
    projekt.speichere(p, mappe)
    return name


def _bild(mappe, knoten=NACHRENDER) -> dict:
    treffer = [b for b in projekt.oeffne(mappe)["projekt"]["bilder"]
               if b["herkunft"]["knoten"] == knoten]
    assert len(treffer) == 1, treffer
    return treffer[0]


# ======================================================================================
# Über den Produktweg: was der Nachrender bekommt
# ======================================================================================

def test_das_eingangsbild_traegt_die_unterlage_und_die_striche(mappe):
    """Der Kern des Befunds: Unterlage **und** Striche im Eingangsbild, Alpha verrechnet.

    Ein Strich deckt ganz, einer halb, der Rest ist durchsichtig — dort muss die
    Unterlage durchscheinen, nicht Schwarz."""
    unterlage = _unterlage_rechnen(mappe)
    _skizze_ablegen(mappe, "skizze-a.png", {(0, 0): (*ROT, 255), (1, 0): (*ROT, 128)},
                    ueber=unterlage)
    modell = _Modell()

    arbeitsgang.rechne_skizze(mappe, "skizze-a.png", ausfuehrer=_tabelle(modell))

    ((farben, breite, hoehe),) = modell.eingaenge
    assert (breite, hoehe) == (4, 4)
    assert farben[0] == ROT, "der deckende Strich ist da"
    assert farben[1] == (128, 0, 127), "der halbe Strich ist halb über der Unterlage"
    assert set(farben[2:]) == {BLAU}, "wo nichts gezeichnet ist, liegt die Unterlage"
    herkunft = _bild(mappe)["herkunft"]["unterlage"]
    assert herkunft["bild"] == unterlage
    assert herkunft["gestreckt"] is False
    assert (mappe / herkunft["eingangsbild"]).is_file()


def test_ohne_unterlage_liegt_die_skizze_auf_grau_und_nicht_auf_schwarz(mappe):
    """``ueber`` fehlt: gezeichnet auf leerem Grund. Durchsichtig wird das neutrale Grau
    (``NEUTRALER_GRUND``) — bis zum 22.09.2026 wurde es Schwarz."""
    _skizze_ablegen(mappe, "skizze-b.png", {(2, 3): (*ROT, 255)}, ueber=None,
                    breite=6, hoehe=4)
    modell = _Modell()

    arbeitsgang.rechne_skizze(mappe, "skizze-b.png", ausfuehrer=_tabelle(modell))

    ((farben, breite, hoehe),) = modell.eingaenge
    assert (breite, hoehe) == (6, 4), "ohne Unterlage bleibt die Grösse der Skizze"
    assert farben[3 * 6 + 2] == ROT
    assert (0, 0, 0) not in farben
    assert set(farben) == {ROT, arbeitsgang.NEUTRALER_GRUND}
    assert _bild(mappe)["herkunft"]["unterlage"]["bild"] is None


def test_verkleinert_wird_ein_duenner_strich_blasser_aber_nicht_unsichtbar(mappe):
    """Blatt 8x8 auf ein Bild 4x4: Eine Linie von einem Bildpunkt Breite fällt in Kästen
    von 2x2, zur Hälfte deckend. Ungewichtet gemittelt käme die Farbe des durchsichtigen
    Grundes hinein — hier ein durchsichtiges Grün, damit man es sähe; es bleibt Rot über
    Blau."""
    unterlage = _unterlage_rechnen(mappe)
    _skizze_ablegen(mappe, "skizze-c.png", {(0, y): (*ROT, 255) for y in range(8)},
                    ueber=unterlage, breite=8, hoehe=8, grund=(0, 255, 0, 0))
    modell = _Modell()

    arbeitsgang.rechne_skizze(mappe, "skizze-c.png", ausfuehrer=_tabelle(modell))

    ((farben, breite, hoehe),) = modell.eingaenge
    assert (breite, hoehe) == (4, 4), "die Grösse ist die der Unterlage"
    assert [farben[y * 4] for y in range(4)] == [(128, 0, 128)] * 4
    assert set(farben[y * 4 + x] for y in range(4) for x in range(1, 4)) == {BLAU}


def test_ein_anderes_seitenverhaeltnis_wird_gestreckt_und_steht_am_bild(mappe):
    unterlage = _unterlage_rechnen(mappe)
    _skizze_ablegen(mappe, "skizze-d.png", {}, ueber=unterlage, breite=6, hoehe=4)

    arbeitsgang.rechne_skizze(mappe, "skizze-d.png", ausfuehrer=_tabelle(_Modell()))

    herkunft = _bild(mappe)["herkunft"]["unterlage"]
    assert herkunft["gestreckt"] is True
    assert "GESTRECKT" in herkunft["grund"]


@pytest.mark.parametrize("fall", ["nicht-in-der-mappe", "datei-fehlt"])
def test_eine_fehlende_unterlage_wird_abgewiesen_statt_still_grau(mappe, fall):
    """Wer auf ein Bild gezeichnet hat, meinte dieses Bild. Ohne es wird **nicht**
    gerechnet — vor Grau wäre es eine andere Bestellung, die aussieht wie die richtige."""
    unterlage = _unterlage_rechnen(mappe)
    if fall == "nicht-in-der-mappe":
        ueber = "laeufe/gibt-es-nicht.png"
    else:
        ueber = unterlage
        (mappe / unterlage).unlink()
    _skizze_ablegen(mappe, "skizze-e.png", {(0, 0): (*ROT, 255)}, ueber=ueber)
    modell = _Modell()
    laeufe_vorher = len(projekt.oeffne(mappe)["projekt"]["laeufe"])

    with pytest.raises(arbeitsgang.ArbeitsgangError, match="Unterlage|gezeichnet"):
        arbeitsgang.rechne_skizze(mappe, "skizze-e.png", ausfuehrer=_tabelle(modell))

    assert modell.eingaenge == []
    assert len(projekt.oeffne(mappe)["projekt"]["laeufe"]) == laeufe_vorher


def test_eine_halb_durchsichtige_unterlage_liegt_selbst_auf_grau(tmp_path):
    """Hat die Unterlage einen Alphakanal, wird sie zuerst auf den neutralen Grund
    gesetzt — sonst käme dort, wo sie durchsichtig ist, wieder Schwarz heraus."""
    skizze = _rgba_png(tmp_path / "s.png", 2, 1, {(0, 0): (*ROT, 255)})
    unterlage = _rgba_png(tmp_path / "u.png", 2, 1, {(0, 0): (*BLAU, 255)})

    ergebnis = arbeitsgang.setze_auf_unterlage(skizze, tmp_path / "e.png",
                                               unterlage=unterlage)

    farben, _, _ = bildlesen.lies_png_farben(ergebnis["bild"])
    assert farben == [ROT, arbeitsgang.NEUTRALER_GRUND]
