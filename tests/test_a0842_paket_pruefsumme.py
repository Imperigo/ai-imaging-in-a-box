"""«Paket nennt Prüfsummen» (A0842, Audit V10) — jeder Holschritt nennt ``sha256`` neben ``bytes``.

Ersetzt der Architekt am Heim-PC ein Bild durch ein gleich grosses neues, sieht der Mac an
``bytes`` allein keinen Unterschied. Der Fingerabdruck des Inhalts macht den Wechsel sichtbar;
``bytes`` bleibt für ältere Macs.

Regel 3: alles synthetisch, keine Projektdaten.
"""
from __future__ import annotations

import hashlib
import os
import struct
import time
import zlib

from aiimaging import mappenpaket, projekt

from test_mappenpaket import _mappe


def _png(farbe: tuple[int, int, int], seite: int = 4) -> bytes:
    """Ein gültiges PNG in einer Farbe — ungepackt (zlib Stufe 0), darum gleich lang je Seite."""
    def stueck(art: bytes, daten: bytes) -> bytes:
        return (struct.pack(">I", len(daten)) + art + daten
                + struct.pack(">I", zlib.crc32(art + daten) & 0xFFFFFFFF))
    zeile = b"\x00" + bytes(farbe) * seite
    return (b"\x89PNG\r\n\x1a\n"
            + stueck(b"IHDR", struct.pack(">IIBBBBB", seite, seite, 8, 2, 0, 0, 0))
            + stueck(b"IDAT", zlib.compress(zeile * seite, 0))
            + stueck(b"IEND", b""))


ROT = _png((220, 30, 30))
BLAU = _png((30, 30, 220))


def _schritt(paket: dict, weg: str) -> dict:
    return next(d for d in paket["dateien"] if d["weg"] == weg)


def _ersetze(datei, inhalt: bytes) -> None:
    """Am selben Ort überschreiben, wie es ein Bildprogramm tut. Die Änderungszeit wird um eine
    Sekunde weitergestellt: zwei Schreibvorgänge im selben Takt der Dateisystem-Uhr wären sonst
    nicht unterscheidbar — der Architekt ersetzt ein Bild nicht in derselben Millisekunde."""
    vorher = datei.stat().st_mtime_ns
    datei.write_bytes(inhalt)
    os.utime(datei, ns=(vorher + 1_000_000_000, vorher + 1_000_000_000))


def test_gleich_grosses_neues_bild_aendert_die_pruefsumme(tmp_path):
    assert len(ROT) == len(BLAU) and ROT != BLAU
    a = _mappe(tmp_path, "Hof")
    bild = a / "bild-1.png"
    _ersetze(bild, ROT)
    erst = _schritt(mappenpaket.paket(a), "bild-1.png")
    _ersetze(bild, BLAU)
    dann = _schritt(mappenpaket.paket(a), "bild-1.png")
    assert erst["bytes"] == dann["bytes"] == len(ROT)
    assert erst["sha256"] == hashlib.sha256(ROT).hexdigest()
    assert dann["sha256"] == hashlib.sha256(BLAU).hexdigest()
    assert erst["sha256"] != dann["sha256"]


def test_jeder_schritt_traegt_weg_art_bytes_und_sha256(tmp_path):
    a = _mappe(tmp_path, "Hof")
    dateien = mappenpaket.paket(a)["dateien"]
    assert [d["art"] for d in dateien] == ["modell", "skizze", "bild"]
    for d in dateien:
        # Die glb der Probe-Mappe liegt als modell.glb in ihr — darum gilt der Weg für alle drei.
        assert set(d) == {"weg", "art", "bytes", "sha256"}
        assert d["sha256"] == hashlib.sha256((a / d["weg"]).read_bytes()).hexdigest()


def test_unveraenderte_datei_wird_nur_einmal_gerechnet(tmp_path, monkeypatch):
    a = _mappe(tmp_path, "Hof")
    gerechnet: list[str] = []
    echt = mappenpaket._sha256_der_datei
    monkeypatch.setattr(mappenpaket, "_sha256_der_datei",
                        lambda pfad: gerechnet.append(pfad.name) or echt(pfad))
    erst = mappenpaket.paket(a)
    zahl = len(gerechnet)
    assert zahl == len(erst["dateien"])
    assert mappenpaket.paket(a)["dateien"] == erst["dateien"]
    assert len(gerechnet) == zahl, "derselbe Mappenstand darf nicht neu gerechnet werden"
    _ersetze(a / "bild-1.png", BLAU)
    mappenpaket.paket(a)
    assert gerechnet[zahl:] == ["bild-1.png"]


def test_grosse_datei_wird_gestreamt(tmp_path, monkeypatch):
    a = _mappe(tmp_path, "Hof")
    gross = a / "bild-1.png"
    inhalt = ROT + os.urandom(3 * mappenpaket.HASH_STUECK + 17)
    _ersetze(gross, inhalt)
    gelesen: list[int] = []
    offen = open

    class Zaehler:
        def __init__(self, f):
            self.f = f

        def __enter__(self):
            return self

        def __exit__(self, *x):
            self.f.close()

        def read(self, n=-1):
            assert 0 < n <= mappenpaket.HASH_STUECK, "nie die ganze Datei auf einmal"
            stueck = self.f.read(n)
            gelesen.append(len(stueck))
            return stueck

    monkeypatch.setattr(mappenpaket, "open", lambda p, m="rb": Zaehler(offen(p, m)), raising=False)
    assert _schritt(mappenpaket.paket(a), "bild-1.png")["sha256"] == hashlib.sha256(inhalt).hexdigest()
    assert len([n for n in gelesen if n]) >= 4


def test_hundert_bilder_zeit(tmp_path):
    """Messgrösse des Auftrags: Zeit für das Paket einer Mappe mit 100 Bildern (kalt, warm)."""
    a = _mappe(tmp_path, "Hof", bild=None)
    p = projekt.oeffne(a)["projekt"]
    for i in range(100):
        name = f"bild-{i:03d}.png"
        (a / name).write_bytes(_png((i, 255 - i, 128), seite=64))
        projekt.vermerke_bild(p, bild=name, schicht="ai-imaging-layer")
    projekt.speichere(p, a)
    t0 = time.perf_counter()
    kalt = mappenpaket.paket(a)
    t1 = time.perf_counter()
    mappenpaket.paket(a)
    t2 = time.perf_counter()
    print(f"\nA0842 Paket 100 Bilder: kalt {1000 * (t1 - t0):.1f} ms, warm {1000 * (t2 - t1):.1f} ms")
    bilder = [d for d in kalt["dateien"] if d["art"] == "bild"]
    assert len(bilder) == 100
    assert all(len(d["sha256"]) == 64 for d in bilder)
