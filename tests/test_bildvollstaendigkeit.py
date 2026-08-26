"""Ein halb geschriebenes Bild faellt auf, bevor die Diffusion daran stirbt.

**Der Anlass ist ein Fehlschlag mitten in einem Mehrkamera-Auftrag** (HomeStation,
`auf-vis-20260826-16`, 26.08.2026): ``OSError: image file is truncated``, und die
**erste** Kamera war durchgelaufen.

Die Meldung kommt aus der Bildbibliothek. Sie nennt **keine Datei**, sie sagt nicht,
welcher der drei Multipass-Ausgaben es war, und sie fällt dort an, wo gerechnet wird —
nicht dort, wo geschrieben wurde. Wer sie liest, sucht den Fehler in der Diffusion.

`bildlesen` hat den passenden Prüfstein seit jeher: :func:`_png_bloecke` liest die
Blockgrenzen und prüft **jede Prüfsumme**. Das kostet fast nichts und beantwortet genau
die gestellte Frage — *ist die Datei ganz da?* — ohne den Bildinhalt zu entpacken.

*Existenz ist kein Beleg für Inhalt.* Dieser Satz steht seit dem 20.08.2026 im Projekt,
und dies ist sein dritter Anwendungsfall.
"""
from __future__ import annotations

import pytest

from aiimaging import abholer, bildlesen
from conftest import MINI_PNG


def test_ein_vollstaendiges_png_gilt_als_lesbar(tmp_path):
    ziel = tmp_path / "gut.png"
    ziel.write_bytes(MINI_PNG)

    lage = bildlesen.pruefe_png(ziel)

    assert lage["lesbar"] is True
    assert lage["bloecke"] == 3, "IHDR, IDAT, IEND"
    assert lage["grund"] == ""


def test_eine_abgeschnittene_datei_faellt_auf(tmp_path):
    """**Der gemeldete Fall.** Der IEND-Block fehlt, und das ist genau die Gestalt eines
    abgebrochenen Schreibvorgangs."""
    ziel = tmp_path / "kurz.png"
    ziel.write_bytes(MINI_PNG[:-6])

    lage = bildlesen.pruefe_png(ziel)

    assert lage["lesbar"] is False
    assert "unvollständig" in lage["grund"]
    assert str(ziel) in lage["grund"], "die Meldung MUSS die Datei nennen"


def test_eine_beschaedigte_pruefsumme_faellt_ebenfalls_auf(tmp_path):
    """Halb kopiert statt halb geschrieben — dieselbe Frage, andere Ursache. Ohne den
    CRC-Test wäre eine Datei mit richtiger Länge und falschem Inhalt in Ordnung."""
    kaputt = bytearray(MINI_PNG)
    kaputt[20] ^= 0xFF
    ziel = tmp_path / "faul.png"
    ziel.write_bytes(bytes(kaputt))

    lage = bildlesen.pruefe_png(ziel)

    assert lage["lesbar"] is False
    assert "Prüfsumme" in lage["grund"]


def test_nur_die_signatur_ist_kein_bild(tmp_path):
    """Acht Byte. Genau das schrieben die Attrappen dieses Projekts bis zum 26.08.2026 —
    und genau das ist die Gestalt, die diese Prüfung fangen soll."""
    ziel = tmp_path / "leer.png"
    ziel.write_bytes(b"\x89PNG\r\n\x1a\n")

    lage = bildlesen.pruefe_png(ziel)

    assert lage["lesbar"] is False
    assert lage["groesse_byte"] == 8


def test_eine_fehlende_datei_sagt_das_und_wirft_nicht(tmp_path):
    """Der Aufrufer entscheidet, was ein fehlendes Zwischenprodukt für ihn bedeutet."""
    lage = bildlesen.pruefe_png(tmp_path / "gibtsnicht.png")

    assert lage["lesbar"] is False
    assert "nicht lesbar" in lage["grund"]


def test_etwas_das_kein_png_ist_wird_als_solches_benannt(tmp_path):
    ziel = tmp_path / "text.png"
    ziel.write_bytes(b"das ist gar kein Bild")

    lage = bildlesen.pruefe_png(ziel)

    assert lage["lesbar"] is False
    assert "keine PNG-Signatur" in lage["grund"]


# ======================================================================================
# Die Naht — vor dem Renderlauf und nicht mittendrin
# ======================================================================================

def _bericht(tmp_path, *, tiefe_kaputt=False, ohne_beauty=False):
    tiefe = tmp_path / "tiefe_norm.png"
    tiefe.write_bytes(MINI_PNG[:-6] if tiefe_kaputt else MINI_PNG)
    bericht = {"depth_png": str(tiefe)}
    if not ohne_beauty:
        beauty = tmp_path / "beauty.png"
        beauty.write_bytes(MINI_PNG)
        bericht["beauty_png"] = str(beauty)
    return bericht


def test_alle_drei_bilder_werden_geprueft(tmp_path):
    lage = abholer._bilder_vollstaendig(_bericht(tmp_path))

    assert lage["vollstaendig"] is True
    assert set(lage["geprueft"]) == {"depth_png", "beauty_png"}


def test_ein_kaputtes_zwischenbild_wird_benannt(tmp_path):
    lage = abholer._bilder_vollstaendig(_bericht(tmp_path, tiefe_kaputt=True))

    assert lage["vollstaendig"] is False
    assert lage["beschaedigt"] == ("depth_png",)
    assert "depth_png" in lage["grund"]


def test_ein_fehlendes_feld_ist_keine_halbe_datei(tmp_path):
    """`beauty_png` fehlt bei `--ohne-beauty` mit Absicht. Ein fehlendes Feld als
    Beschädigung zu melden hiesse, eine Einstellung als Fehler auszugeben."""
    lage = abholer._bilder_vollstaendig(_bericht(tmp_path, ohne_beauty=True))

    assert lage["vollstaendig"] is True
    assert lage["geprueft"] == ("depth_png",)


def test_der_lauf_bricht_ab_bevor_gerendert_wird(tmp_path):
    """**Der ganze Zweck.** Aus einem Fehlschlag der Diffusion wird ein benannter Befund
    über eine Datei — und die GPU wird gar nicht erst angefasst."""
    from pathlib import Path

    zaehler = {"render": 0}

    def multipass(glb, aus, **kw):
        tiefe = Path(aus) / "tiefe_norm.png"
        tiefe.write_bytes(MINI_PNG[:-6])          # abgeschnitten
        return {"depth_png": str(tiefe), "kamera": {"weg": "vorgegeben"}}

    def rendere(auftrag, **kw):
        zaehler["render"] += 1
        raise AssertionError("hier darf gar nicht mehr gerendert werden")

    verarbeite = abholer.verarbeiter(
        out_wurzel=tmp_path, nullprobe=False,
        _multipass=multipass, _rendere=rendere,
        _qa=lambda *a, **k: {"score": 0.9, "bestanden": True},
        _soll=lambda *a, **k: ([[0.0]], 1, 1))

    with pytest.raises(abholer.AbholerError, match="unvollstaendig oder beschaedigt"):
        verarbeite({"modell": tmp_path / "m.glb", "job_id": "vis-1-aaaaaa",
                    "verzeichnis": tmp_path,
                    "szene": {"kameras": [{"kuerzel": "s", "richtung": "s"}],
                              "aufloesung": 64, "hoehe": 64, "samples": 1,
                              "prompt": "a house"}})

    assert zaehler["render"] == 0


def test_und_mit_heilen_bildern_laeuft_er_durch(tmp_path):
    """Die Gegenprobe. Ein Riegel, der jeden Lauf aufhält, ist von einer kaputten Kette
    nicht zu unterscheiden."""
    from pathlib import Path

    zaehler = {"render": 0}

    def multipass(glb, aus, **kw):
        tiefe = Path(aus) / "tiefe_norm.png"
        tiefe.write_bytes(MINI_PNG)
        return {"depth_png": str(tiefe), "kamera": {"weg": "vorgegeben"}}

    def rendere(auftrag, **kw):
        zaehler["render"] += 1
        bild = Path(tmp_path) / "b.png"
        bild.write_bytes(MINI_PNG)
        return {"status": "ok", "bild_png": str(bild), "hinweise": ()}

    verarbeite = abholer.verarbeiter(
        out_wurzel=tmp_path, nullprobe=False,
        _multipass=multipass, _rendere=rendere,
        _qa=lambda *a, **k: {"score": 0.9, "bestanden": True},
        _soll=lambda *a, **k: ([[0.0]], 1, 1))

    ergebnis = verarbeite({"modell": tmp_path / "m.glb", "job_id": "vis-1-aaaaaa",
                           "verzeichnis": tmp_path,
                           "szene": {"kameras": [{"kuerzel": "s", "richtung": "s"}],
                                     "aufloesung": 64, "hoehe": 64, "samples": 1,
                                     "prompt": "a house"}})

    assert zaehler["render"] == 1
    assert len(ergebnis["bilder"]) == 1
