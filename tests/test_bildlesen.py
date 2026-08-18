"""Von der Bilddatei zu den Zahlen — und was dabei ehrlich verloren geht.

Drei Sorten Tests, bewusst getrennt
-----------------------------------
1. **Ohne alles.** PNG- und EXR-Leser gegen Dateien, die dieser Test selbst schreibt.
   Das ist der grösste Teil und läuft überall — kein Blender, keine GPU, keine
   Bildbibliothek. Genau das ist der Punkt: Wäre der Leser nur mit Blender prüfbar,
   hätte er seine Existenzberechtigung verfehlt.
2. **Die Testnaht.** Der Blender-Rückfall über ein eingesetztes ``_starte``. Prüft die
   Aufrufkonstruktion und — wichtiger — dass der Rückfall *nicht* passiert, wo er nicht
   hingehört.
3. **Mit Blender** (``@pytest.mark.skipif``). Der eine Test, der die Zusage belegt, um
   die es geht: stdlib-Weg und Blender-Weg liefern dieselben Zahlen.

Warum hier ein PNG- **und** ein EXR-Schreiber steht
---------------------------------------------------
Ein Leser lässt sich nur an Dateien prüfen, deren Inhalt man vorher kennt. Beide
Schreiber sind reine Standardbibliothek und erzeugen die Testdaten im Repo (Regel 3:
Testdaten sind synthetisch und erzeugbar). Der PNG-Schreiber kann jede der fünf
Filterarten erzwingen — Blender verwendet im echten Bild vier davon, und ein Leser, der
nur eine kann, liest die übrigen nicht falsch, sondern *plausibel* falsch.
"""
from __future__ import annotations

import ast
import json
import math
import random
import struct
import subprocess
import zlib
from pathlib import Path

import pytest

from aiimaging import bildlesen, geometrie_qa, seams
from aiimaging.bildlesen import (
    BildError,
    BlenderRueckfall,
    EXRVarianteError,
    SilhouettenVerlust,
    exr_kopf,
    lies_exr_tiefe,
    lies_exr_tiefe_stdlib,
    lies_exr_tiefe_ueber_blender,
    lies_png_graustufen,
    png_befund,
    tiefen_aus_png,
    tiefen_aus_report,
)

#: Der Runner jenseits der Grenze. Wird **gelesen**, nie importiert — er braucht ``bpy``.
RUNNER_QUELLE = bildlesen.EXR_RUNNER.read_text(encoding="utf-8")


def blender_fehlt() -> bool:
    """Ist in dieser Umgebung ein Blender-Binary erreichbar?"""
    try:
        return not Path(seams.finde_blender()).exists()
    except seams.SeamError:
        return True


ohne_blender = pytest.mark.skipif(
    blender_fehlt(), reason="Blender nicht vorhanden — der Lauf über die Prozessgrenze entfällt"
)


# ======================================================================================
# Werkzeuge: PNG und EXR schreiben — beides reine Standardbibliothek
# ======================================================================================

def _block(typ: bytes, inhalt: bytes) -> bytes:
    """Ein PNG-Block mit Länge, Typ, Inhalt und korrekter Prüfsumme."""
    return (len(inhalt).to_bytes(4, "big") + typ + inhalt
            + (zlib.crc32(typ + inhalt) & 0xFFFFFFFF).to_bytes(4, "big"))


def _filtere(zeile: bytes, vorherige: bytes, art: int, bpp: int) -> bytes:
    """Eine Bildzeile mit der gewünschten PNG-Filterart kodieren (Vorwärtsrichtung)."""
    aus = bytearray(len(zeile))
    for i, wert in enumerate(zeile):
        links = zeile[i - bpp] if i >= bpp else 0
        oben = vorherige[i]
        schraeg = vorherige[i - bpp] if i >= bpp else 0
        if art == 0:
            vorhersage = 0
        elif art == 1:
            vorhersage = links
        elif art == 2:
            vorhersage = oben
        elif art == 3:
            vorhersage = (links + oben) >> 1
        elif art == 4:
            p_a, p_b, p_c = (abs(oben - schraeg), abs(links - schraeg),
                             abs(links + oben - 2 * schraeg))
            vorhersage = links if (p_a <= p_b and p_a <= p_c) else (
                oben if p_b <= p_c else schraeg)
        else:
            raise AssertionError(art)
        aus[i] = (wert - vorhersage) & 0xFF
    return bytes(aus)


def schreibe_png(ziel: Path, breite: int, hoehe: int, werte, *, bittiefe: int = 16,
                 farbtyp: int = 0, filterarten=None, verschraenkt: int = 0) -> Path:
    """Ein Graustufen-PNG mit vorgegebenen Rohwerten und wählbaren Zeilenfiltern.

    ``werte`` sind ganze Zahlen in ``0..2^bittiefe-1``, zeilenweise von oben.
    ``filterarten`` ist eine Liste je Zeile (0..4); ohne Angabe wird durchgewechselt,
    damit ein einzelner Aufruf schon alle fünf Filter durchläuft.
    """
    kanaele = 1 if farbtyp == 0 else 2
    bpp = kanaele * (bittiefe // 8)
    if filterarten is None:
        filterarten = [y % 5 for y in range(hoehe)]

    roh = bytearray()
    vorherige = bytes(breite * bpp)
    for y in range(hoehe):
        zeile = bytearray()
        for x in range(breite):
            wert = werte[y * breite + x]
            if bittiefe == 8:
                zeile.append(wert & 0xFF)
            else:
                zeile += wert.to_bytes(2, "big")
            if kanaele == 2:                            # Alpha, wird vom Leser übergangen
                zeile += (b"\xff" if bittiefe == 8 else b"\xff\xff")
        roh.append(filterarten[y])
        gefiltert = _filtere(bytes(zeile), vorherige, filterarten[y], bpp)
        roh += gefiltert
        vorherige = bytes(zeile)

    ihdr = struct.pack(">IIBBBBB", breite, hoehe, bittiefe, farbtyp, 0, 0, verschraenkt)
    ziel.parent.mkdir(parents=True, exist_ok=True)
    ziel.write_bytes(bildlesen.PNG_SIGNATUR + _block(b"IHDR", ihdr)
                     + _block(b"IDAT", zlib.compress(bytes(roh)))
                     + _block(b"IEND", b""))
    return ziel


def _zip_packen(daten: bytes) -> bytes:
    """Umkehrung von ``bildlesen._zip_entpacken``: entflechten, Differenzen, deflate."""
    verflochten = bytes(daten[0::2]) + bytes(daten[1::2])
    diff = bytearray(len(verflochten))
    if verflochten:
        diff[0] = verflochten[0]
        for i in range(1, len(verflochten)):
            diff[i] = (verflochten[i] - verflochten[i - 1] + 128) & 0xFF
    return zlib.compress(bytes(diff), 6)


def schreibe_exr(ziel: Path, breite: int, hoehe: int, kanaldaten: dict, *,
                 kompression: int = 3, pixeltyp: int = 2, line_order: int = 0,
                 versionsflaggen: int = 0, sampling=(1, 1)) -> Path:
    """Eine scanline-EXR mit vorgegebenen Kanälen schreiben.

    ``kanaldaten`` bildet Kanalnamen auf Wertelisten ab (zeilenweise von oben). Die
    Kanäle werden alphabetisch abgelegt, wie es die Spezifikation verlangt — genau
    deshalb kann der Leser sich nicht auf die Dateireihenfolge verlassen, wenn er den
    Tiefenkanal sucht.
    """
    namen = sorted(kanaldaten)
    code = {1: "e", 2: "f", 0: "I"}[pixeltyp]

    kopfteile = bytearray()

    def attribut(name: str, typ: str, roh: bytes) -> None:
        kopfteile.extend(name.encode() + b"\0" + typ.encode() + b"\0"
                         + struct.pack("<i", len(roh)) + roh)

    kanalliste = bytearray()
    for name in namen:
        kanalliste += name.encode() + b"\0" + struct.pack("<iB3xii", pixeltyp, 0, *sampling)
    kanalliste += b"\0"
    attribut("channels", "chlist", bytes(kanalliste))
    attribut("compression", "compression", bytes([kompression]))
    attribut("dataWindow", "box2i", struct.pack("<iiii", 0, 0, breite - 1, hoehe - 1))
    attribut("displayWindow", "box2i", struct.pack("<iiii", 0, 0, breite - 1, hoehe - 1))
    attribut("lineOrder", "lineOrder", bytes([line_order]))
    attribut("pixelAspectRatio", "float", struct.pack("<f", 1.0))
    attribut("screenWindowCenter", "v2f", struct.pack("<ff", 0.0, 0.0))
    attribut("screenWindowWidth", "float", struct.pack("<f", 1.0))
    kopfteile.append(0)

    zeilen_je_block = {0: 1, 1: 1, 2: 1, 3: 16}.get(kompression, 16)
    n_bloecke = (hoehe + zeilen_je_block - 1) // zeilen_je_block

    bloecke = []
    for b in range(n_bloecke):
        y0 = b * zeilen_je_block
        n_zeilen = min(zeilen_je_block, hoehe - y0)
        roh = bytearray()
        for y in range(y0, y0 + n_zeilen):
            for name in namen:
                werte = kanaldaten[name][y * breite:(y + 1) * breite]
                if pixeltyp == 0:                       # UINT trägt ganze Zahlen
                    werte = [int(w) for w in werte]
                roh += struct.pack(f"<{breite}{code}", *werte)
        if kompression == 0:
            nutzlast = bytes(roh)
        else:
            gepackt = _zip_packen(bytes(roh))
            # Die Spezifikation erlaubt, einen Block roh abzulegen, wenn Packen nichts
            # bringt. Rauschen löst das aus — und der Leser muss beides können.
            nutzlast = gepackt if len(gepackt) < len(roh) else bytes(roh)
        bloecke.append((y0, nutzlast))

    kopf = bildlesen.EXR_MAGIC + struct.pack("<I", 2 | versionsflaggen) + bytes(kopfteile)
    offset = len(kopf) + 8 * n_bloecke
    tabelle = bytearray()
    koerper = bytearray()
    for y0, nutzlast in bloecke:
        tabelle += struct.pack("<Q", offset + len(koerper))
        koerper += struct.pack("<ii", y0, len(nutzlast)) + nutzlast

    ziel.parent.mkdir(parents=True, exist_ok=True)
    ziel.write_bytes(kopf + bytes(tabelle) + bytes(koerper))
    return ziel


#: Eine Normalisierung, wie der Multipass sie meldet — runde Zahlen, damit sich die
#: Rückrechnung im Kopf nachrechnen lässt.
NORM = {"min_m": 10.0, "max_m": 20.0,
        "rueckrechnung": "meter = max_m - grau * (max_m - min_m), grau in 0..1"}


# ======================================================================================
# 1 · PNG — der Leser, der ohne alles auskommen muss
# ======================================================================================

def test_der_schreiber_und_der_leser_sind_zueinander_invers(tmp_path):
    """Vorbedingung für alles Weitere: Was hier geschrieben wird, kommt so zurück.

    Ohne diesen Test prüften die folgenden nur, dass zwei eigene Fehler sich gegenseitig
    aufheben.
    """
    werte = [(y * 251 + x * 37) % 65536 for y in range(9) for x in range(7)]
    pfad = schreibe_png(tmp_path / "probe.png", 7, 9, werte)

    gelesen, breite, hoehe = lies_png_graustufen(pfad)

    assert (breite, hoehe) == (7, 9)
    assert [round(w * 65535) for w in gelesen] == werte


@pytest.mark.parametrize("art", [0, 1, 2, 3, 4],
                         ids=["None", "Sub", "Up", "Average", "Paeth"])
@pytest.mark.parametrize("bittiefe", [8, 16])
def test_alle_fuenf_zeilenfilter_werden_richtig_aufgeloest(tmp_path, art, bittiefe):
    """Ein Schreiber wählt den Filter je Zeile frei — ein Leser muss alle fünf können.

    Blender selbst verwendet im echten Tiefenbild vier davon (gemessen: None, Sub, Up,
    Paeth). Ein Leser, der einen Filter nicht beherrscht, scheitert nicht laut, sondern
    liefert plausible falsche Zahlen — die schlimmste Sorte Fehler in einer Messkette.
    """
    grenze = (1 << bittiefe) - 1
    zufall = random.Random(art * 100 + bittiefe)
    werte = [zufall.randrange(grenze + 1) for _ in range(11 * 6)]
    pfad = schreibe_png(tmp_path / f"f{art}_{bittiefe}.png", 11, 6, werte,
                        bittiefe=bittiefe, filterarten=[art] * 6)

    gelesen, _, _ = lies_png_graustufen(pfad)

    assert [round(w * grenze) for w in gelesen] == werte


def test_sechzehn_bit_werden_big_endian_gelesen(tmp_path):
    """PNG legt Mehrbytewerte big-endian ab — vertauscht sähe das Bild trotzdem aus wie eines.

    ``0x0100`` (256) und ``0x0001`` (1) unterscheiden sich nur in der Bytefolge. Ein
    Leser mit falscher Ordnung liefert für ein Verlaufsbild ein anderes Verlaufsbild,
    kein sichtbares Chaos.
    """
    pfad = schreibe_png(tmp_path / "endian.png", 3, 1, [1, 256, 65535],
                        filterarten=[0])

    gelesen, _, _ = lies_png_graustufen(pfad)

    assert [round(w * 65535) for w in gelesen] == [1, 256, 65535]


def test_werte_kommen_als_anteil_von_null_bis_eins(tmp_path):
    """Die Skalierung macht den Rückgabewert bittiefenunabhängig.

    Dieselbe Helligkeit muss in 8 und 16 Bit dieselbe Zahl ergeben — sonst hinge die
    Rückrechnung in Meter an einem Dateiformatdetail.
    """
    acht = schreibe_png(tmp_path / "a8.png", 3, 1, [0, 255, 51], bittiefe=8, filterarten=[0])
    sechzehn = schreibe_png(tmp_path / "a16.png", 3, 1, [0, 65535, 13107],
                            bittiefe=16, filterarten=[0])

    werte8, _, _ = lies_png_graustufen(acht)
    werte16, _, _ = lies_png_graustufen(sechzehn)

    assert werte8[0] == werte16[0] == 0.0
    assert werte8[1] == werte16[1] == 1.0
    assert werte8[2] == pytest.approx(0.2, abs=1e-4)
    assert werte16[2] == pytest.approx(0.2, abs=1e-4)


def test_graustufen_mit_alpha_liefert_den_grauwert(tmp_path):
    """Farbtyp 4 trägt zwei Kanäle je Pixel — gelesen wird der erste, nicht jeder zweite."""
    werte = [0, 20000, 40000, 65535, 1, 2]
    pfad = schreibe_png(tmp_path / "grau_alpha.png", 3, 2, werte, farbtyp=4)

    gelesen, breite, hoehe = lies_png_graustufen(pfad)

    assert (breite, hoehe) == (3, 2)
    assert [round(w * 65535) for w in gelesen] == werte


def test_zeilen_laufen_von_oben_nach_unten(tmp_path):
    """Die Reihenfolge ist eine Zusage, keine Nebensache.

    ``geometrie_qa`` setzt Indexgleichheit voraus und erkennt einen Versatz nicht — es
    bestraft ihn nur als schlechteren Score, ohne die Ursache zu nennen. Eine gekippte
    Karte wäre also ein unsichtbarer Fehler.
    """
    werte = [0, 0, 65535, 65535]                        # obere Zeile dunkel, untere hell
    pfad = schreibe_png(tmp_path / "oben_unten.png", 2, 2, werte, filterarten=[0, 0])

    gelesen, _, _ = lies_png_graustufen(pfad)

    assert gelesen[:2] == [0.0, 0.0], "die erste gelesene Zeile ist die oberste"
    assert gelesen[2:] == [1.0, 1.0]


# ── Was der Leser abweist ────────────────────────────────────────────────────────────

def test_datei_ohne_png_signatur_wird_abgewiesen(tmp_path):
    """Die Endung sagt nichts über den Inhalt — geprüft wird die Signatur."""
    pfad = tmp_path / "kein.png"
    pfad.write_bytes(b"GIF89a" + b"\0" * 100)

    with pytest.raises(BildError, match="kein PNG"):
        lies_png_graustufen(pfad)


def test_beschaedigte_pruefsumme_wird_gemeldet(tmp_path):
    """Existenz ist kein Beleg für Inhalt — die wiederkehrende Lehre dieses Projekts.

    Ein halb geschriebenes oder halb kopiertes Bild sieht wie ein Bild aus. Der CRC-Test
    kostet fast nichts und fängt genau das.
    """
    pfad = schreibe_png(tmp_path / "kaputt.png", 4, 4, [0] * 16)
    roh = bytearray(pfad.read_bytes())
    roh[-6] ^= 0xFF                                     # ein Byte im IDAT-Bereich kippen
    pfad.write_bytes(bytes(roh))

    with pytest.raises(BildError, match="Prüfsumme"):
        lies_png_graustufen(pfad)


def test_abgeschnittene_datei_wird_nicht_halb_gelesen(tmp_path):
    """Ein unvollständiges Bild ergäbe eine unvollständige Tiefenkarte — mit Löchern,
    die wie fehlende Geometrie aussähen."""
    pfad = schreibe_png(tmp_path / "kurz.png", 8, 8, [0] * 64)
    pfad.write_bytes(pfad.read_bytes()[:40])

    with pytest.raises(BildError):
        lies_png_graustufen(pfad)


def test_farbbild_wird_nicht_zur_tiefenkarte_umgedeutet(tmp_path):
    """Aus drei Farbkanälen eine Entfernung zu machen wäre geraten, nicht gelesen."""
    ihdr = struct.pack(">IIBBBBB", 2, 2, 8, 2, 0, 0, 0)   # Farbtyp 2 = RGB
    roh = b"".join(b"\0" + bytes([1, 2, 3, 4, 5, 6]) for _ in range(2))
    pfad = tmp_path / "rgb.png"
    pfad.write_bytes(bildlesen.PNG_SIGNATUR + _block(b"IHDR", ihdr)
                     + _block(b"IDAT", zlib.compress(roh)) + _block(b"IEND", b""))

    with pytest.raises(BildError, match="Farbtyp"):
        lies_png_graustufen(pfad)


def test_verschraenktes_png_wird_abgewiesen(tmp_path):
    """Adam7 zerlegt das Bild in sieben Durchgänge — eine Reihenfolge zu raten wäre falsch."""
    pfad = schreibe_png(tmp_path / "adam7.png", 4, 4, [0] * 16, verschraenkt=1)

    with pytest.raises(BildError, match="verschränkt"):
        lies_png_graustufen(pfad)


def test_zu_geringe_bittiefe_wird_abgewiesen(tmp_path):
    """4 Bit wären 16 Stufen für die ganze Bautiefe — als Tiefenkarte sinnlos."""
    ihdr = struct.pack(">IIBBBBB", 2, 2, 4, 0, 0, 0, 0)
    roh = b"\0\x12" * 2
    pfad = tmp_path / "vier_bit.png"
    pfad.write_bytes(bildlesen.PNG_SIGNATUR + _block(b"IHDR", ihdr)
                     + _block(b"IDAT", zlib.compress(roh)) + _block(b"IEND", b""))

    with pytest.raises(BildError, match="Bittiefe"):
        lies_png_graustufen(pfad)


def test_fehlende_datei_wird_gemeldet(tmp_path):
    with pytest.raises(BildError):
        lies_png_graustufen(tmp_path / "gibtsnicht.png")


# ======================================================================================
# 2 · Die Rückrechnung in Meter — und die dokumentierte Falle
# ======================================================================================

def test_rueckrechnung_folgt_der_formel_aus_dem_report(tmp_path):
    """``meter = max_m - grau * (max_m - min_m)`` — genau so, wie der Runner es angibt.

    Nah = hell: Grauwert 1 muss die **kleinste** Entfernung ergeben. Verdreht wäre die
    Tiefenordnung umgekehrt, und die Rangkorrelation meldete −1 auf einer völlig
    korrekten Geometrie.
    """
    pfad = schreibe_png(tmp_path / "verlauf.png", 3, 1, [65535, 32768, 16384],
                        filterarten=[0])

    meter = tiefen_aus_png(pfad, NORM)

    assert meter[0] == pytest.approx(10.0), "Grauwert 1 (hell) ist der nächste Punkt"
    assert meter[1] == pytest.approx(15.0, abs=1e-3)
    assert meter[2] == pytest.approx(17.5, abs=1e-3)


def test_ebene_flaeche_frontal_ergibt_eine_einzige_entfernung(tmp_path):
    """Sonderfall aus dem Runner: Ist die Spanne 0, liegt alles bei Grauwert 1.

    Rückgerechnet muss daraus wieder genau ``max_m`` werden — und nicht etwa 0 oder eine
    Division durch die Spanne.
    """
    pfad = schreibe_png(tmp_path / "eben.png", 2, 1, [65535, 65535], filterarten=[0])

    meter = tiefen_aus_png(pfad, {"min_m": 12.5, "max_m": 12.5})

    assert meter == [12.5, 12.5]


def test_grauwert_null_gilt_als_hintergrund_und_wird_gewarnt(tmp_path):
    """Die Falle: Hintergrund und entferntestes Geometriepixel sind beide schwarz.

    Vorgabe ist ``inf`` — ``geometrie_qa.silhouette`` liest das als Hintergrund. Der
    Preis (die hintersten Punkte fehlen) wird nicht verschwiegen, sondern gewarnt.
    """
    pfad = schreibe_png(tmp_path / "mit_null.png", 4, 1, [0, 0, 32768, 65535],
                        filterarten=[0])

    with pytest.warns(SilhouettenVerlust, match="2 von 4"):
        meter = tiefen_aus_png(pfad, NORM)

    assert meter[0] == meter[1] == math.inf
    assert geometrie_qa.silhouette(meter) == [False, False, True, True]


def test_grauwert_null_laesst_sich_als_geometrie_deuten(tmp_path):
    """Die Gegenwahl — mit ihrem eigenen, benannten Preis.

    Dann zählt der leere Himmel zur Silhouette und ``geom_iou`` wird zu gross. Es gibt
    keine verlustfreie Deutung; es gibt nur die Wahl, welchen Verlust man nimmt.
    """
    pfad = schreibe_png(tmp_path / "mit_null2.png", 2, 1, [0, 65535], filterarten=[0])

    with pytest.warns(SilhouettenVerlust, match="Himmel"):
        meter = tiefen_aus_png(pfad, NORM, grau_null=bildlesen.GRAU_NULL_GEOMETRIE)

    assert meter == [20.0, 10.0]
    assert geometrie_qa.silhouette(meter) == [True, True]


def test_ohne_schwarze_punkte_wird_nicht_gewarnt(tmp_path, recwarn):
    """Eine Warnung, die immer kommt, wird überlesen. Diese kommt nur, wenn es sie braucht."""
    pfad = schreibe_png(tmp_path / "ohne_null.png", 3, 1, [1, 32768, 65535], filterarten=[0])

    tiefen_aus_png(pfad, NORM)

    assert [w for w in recwarn if issubclass(w.category, SilhouettenVerlust)] == []


def test_unbekannte_deutung_wird_nicht_stillschweigend_ersetzt(tmp_path):
    """Ein Tippfehler in ``grau_null`` darf nicht in der Vorgabe verschwinden —
    das wäre eine Entscheidung im Namen des Aufrufers."""
    pfad = schreibe_png(tmp_path / "x.png", 2, 1, [0, 65535], filterarten=[0])

    with pytest.raises(BildError, match="grau_null"):
        tiefen_aus_png(pfad, NORM, grau_null="hintergrundd")


@pytest.mark.parametrize("norm, muster", [
    ({"max_m": 20.0}, "min_m"),
    ({"min_m": 20.0, "max_m": 10.0}, "hinter"),
    ({"min_m": 0.0, "max_m": 10.0}, "positiv"),
    ({"min_m": float("nan"), "max_m": 10.0}, "keine Länge"),
    ({"min_m": "10", "max_m": 20.0}, "Zahl erwartet"),
    ("kein dict", "dict erwartet"),
])
def test_unbrauchbare_normalisierung_wird_abgewiesen(tmp_path, norm, muster):
    """Die beiden Zahlen sind der einzige Bezug zwischen Grauwert und Meter.

    Stimmt hier etwas nicht, ist alles danach eine Entfernung ohne Grundlage — und die
    sähe genauso aus wie eine echte. Vertauschte Grenzen sind der heimtückischste Fall:
    Sie kehren die Tiefenordnung um, und die Rangkorrelation meldete brav −1.
    """
    pfad = schreibe_png(tmp_path / "y.png", 2, 1, [0, 65535], filterarten=[0])

    with pytest.raises(BildError, match=muster):
        tiefen_aus_png(pfad, norm)


def test_png_befund_beziffert_den_verlust_maschinenlesbar(tmp_path):
    """Dieselbe Auskunft wie die Warnung — für Berichte statt für Logfiles."""
    pfad = schreibe_png(tmp_path / "befund.png", 4, 1, [0, 0, 0, 65535], filterarten=[0])

    befund = png_befund(pfad, NORM)

    assert befund["n_pixel"] == 4
    assert befund["n_grau_null"] == 3
    assert befund["anteil_grau_null"] == 0.75
    assert befund["n_grau_eins"] == 1
    # 16 Bit über 10 m Spanne: 10 / 65535 m je Stufe. Das ist die Untergrenze jeder
    # Abweichung, die man zwischen PNG und EXR messen kann.
    assert befund["quantisierungsschritt_m"] == pytest.approx(10.0 / 65535)


# ======================================================================================
# 3 · EXR — der stdlib-Weg
# ======================================================================================

@pytest.mark.parametrize("kompression, name", [(0, "NONE"), (2, "ZIPS"), (3, "ZIP")])
def test_exr_rundlauf_je_kompression(tmp_path, kompression, name):
    """Die drei Verfahren, die reines ``zlib`` sind — mehr braucht dieses Projekt nicht.

    Die Höhe ist mit 20 bewusst grösser als die 16 Zeilen eines ZIP-Blocks: Sonst
    entstünde nur ein einziger, voller Block und der Umgang mit dem angebrochenen
    letzten bliebe ungeprüft.
    """
    werte = [round(10.0 + (y * 13 + x) * 0.25, 3) for y in range(20) for x in range(7)]
    pfad = schreibe_exr(tmp_path / f"{name}.exr", 7, 20, {"V": werte},
                        kompression=kompression)

    gelesen, breite, hoehe = lies_exr_tiefe_stdlib(pfad)

    assert (breite, hoehe) == (7, 20)
    assert gelesen == pytest.approx(werte, abs=1e-4)
    assert exr_kopf(pfad)["kompression_name"] == name


def test_unkomprimierbarer_block_wird_roh_abgelegt_und_gelesen(tmp_path):
    """Bringt Packen nichts, legt OpenEXR den Block roh ab — der Leser muss beides können.

    Rauschen löst genau das aus. Ein Leser, der immer ein zlib-Paket erwartet, scheitert
    an einer völlig regelkonformen Datei.
    """
    zufall = random.Random(7)
    werte = [zufall.uniform(1.0, 1e6) for _ in range(16 * 32)]
    pfad = schreibe_exr(tmp_path / "rauschen.exr", 16, 32, {"V": werte})

    gelesen, _, _ = lies_exr_tiefe_stdlib(pfad)

    assert gelesen == pytest.approx(werte, rel=1e-6)


def test_half_kanal_wird_gelesen(tmp_path):
    """16-Bit-Gleitkomma ist eine gültige Tiefendarstellung — nur eine gröbere."""
    werte = [1.0, 2.5, 100.0, 1024.0]
    pfad = schreibe_exr(tmp_path / "half.exr", 4, 1, {"V": werte}, pixeltyp=1)

    gelesen, _, _ = lies_exr_tiefe_stdlib(pfad)

    assert gelesen == pytest.approx(werte, rel=1e-3)
    assert exr_kopf(pfad)["kanaele"][0]["typ_name"] == "HALF"


def test_zeilen_laufen_von_oben_nach_unten_wie_beim_png(tmp_path):
    """Beide Leser müssen dieselbe Reihenfolge liefern, sonst sind die Karten nicht indexgleich."""
    werte = [float(y) for y in range(24) for _ in range(5)]
    pfad = schreibe_exr(tmp_path / "zeilen.exr", 5, 24, {"V": werte})

    gelesen, breite, _ = lies_exr_tiefe_stdlib(pfad)

    assert gelesen[:breite] == [0.0] * breite, "die erste gelesene Zeile ist y=0, also oben"
    assert gelesen[-breite:] == [23.0] * breite


def test_hintergrundwerte_kommen_unveraendert_zurueck(tmp_path):
    """Der Leser deutet nicht. Was Hintergrund ist, entscheidet ``geometrie_qa``.

    Cycles schreibt für Strahlen ins Leere ~1e10. Diese Zahl hier auf ``inf`` oder
    ``None`` umzusetzen wäre eine Deutung — und sie läge im falschen Modul.
    """
    werte = [12.0, 1e10, 13.0, 1e10]
    pfad = schreibe_exr(tmp_path / "himmel.exr", 4, 1, {"V": werte})

    gelesen, _, _ = lies_exr_tiefe_stdlib(pfad)

    assert gelesen[1] == pytest.approx(1e10, rel=1e-6)
    assert geometrie_qa.silhouette(gelesen) == [True, False, True, False]


def test_tiefenkanal_wird_nach_vorrang_gewaehlt_nicht_nach_dateireihenfolge(tmp_path):
    """Der Fehlgriff, der still den falschen Kanal läse.

    EXR führt Kanäle alphabetisch: In einer Datei mit ``R`` und ``V`` steht ``R`` vorn.
    ``V`` ist aber der Kanal, den Blender für einen einwertigen Compositor-Ausgang
    schreibt. Nach Dateireihenfolge zu wählen ergäbe eine Zahlenfolge, die aussieht wie
    eine Tiefenkarte und die falschen Werte trägt.
    """
    pfad = schreibe_exr(tmp_path / "zwei.exr", 3, 2,
                        {"R": [1.0] * 6, "V": [42.0] * 6})

    gelesen, _, _ = lies_exr_tiefe_stdlib(pfad)

    assert gelesen == [42.0] * 6


def test_rgb_ohne_v_faellt_auf_den_r_kanal_zurueck(tmp_path):
    """Ohne ``V`` und ``Z`` bleibt ``R`` — so schreibt der Multipass-Runner es an."""
    pfad = schreibe_exr(tmp_path / "rgb.exr", 2, 2,
                        {"R": [5.0] * 4, "G": [0.0] * 4, "B": [0.0] * 4})

    gelesen, _, _ = lies_exr_tiefe_stdlib(pfad)

    assert gelesen == [5.0] * 4


# ── Was der EXR-Leser ehrlich abweist ────────────────────────────────────────────────

@pytest.mark.parametrize("bau, muster", [
    ({"kompression": 4}, "PIZ"),
    ({"kompression": 8}, "DWAA"),
    ({"kompression": 5}, "PXR24"),
    ({"versionsflaggen": 0x0200}, "gekachelt"),
    ({"versionsflaggen": 0x1000}, "mehrteilig"),
    ({"pixeltyp": 0}, "UINT"),
    ({"sampling": (2, 2)}, "unterabgetastet"),
])
def test_nicht_unterstuetzte_spielart_wird_benannt_statt_geraten(tmp_path, bau, muster):
    """Jede Grenze dieses Lesers wird gesagt, nicht überspielt.

    Und sie wird als ``EXRVarianteError`` gesagt — daran hängt die Entscheidung, ob der
    Blender-Rückfall überhaupt sinnvoll ist. Die Datei ist in Ordnung; nur dieser Weg
    kann sie nicht.
    """
    pfad = schreibe_exr(tmp_path / "exotisch.exr", 4, 4, {"V": [1.0] * 16}, **bau)

    with pytest.raises(EXRVarianteError, match=muster):
        lies_exr_tiefe_stdlib(pfad)

    kopf = exr_kopf(pfad)
    assert kopf["ohne_blender_lesbar"] is False
    assert muster.lower() in kopf["grund"].lower()


def test_kopf_meldet_lesbarkeit_fuer_die_eigenen_dateien(tmp_path):
    """Die Diagnose muss zum Leser passen, sonst ist sie wertlos."""
    pfad = schreibe_exr(tmp_path / "normal.exr", 4, 4, {"V": [1.0] * 16})

    kopf = exr_kopf(pfad)

    assert kopf["ohne_blender_lesbar"] is True
    assert kopf["grund"] is None
    assert (kopf["breite"], kopf["hoehe"]) == (4, 4)


def test_kanalname_ohne_tiefenbedeutung_wird_gemeldet(tmp_path):
    """Aus einem ``diffuse``-Kanal eine Entfernung zu lesen wäre reines Raten."""
    pfad = schreibe_exr(tmp_path / "fremd.exr", 2, 2,
                        {"alpha": [1.0] * 4, "diffuse": [2.0] * 4})

    with pytest.raises(EXRVarianteError, match="kein Tiefenkanal"):
        lies_exr_tiefe_stdlib(pfad)


def test_datei_ohne_exr_signatur_wird_abgewiesen(tmp_path):
    pfad = tmp_path / "keine.exr"
    pfad.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\0" * 64)

    with pytest.raises(BildError, match="keine OpenEXR"):
        lies_exr_tiefe_stdlib(pfad)


def test_abgeschnittene_exr_ist_ein_fehler_und_keine_variante(tmp_path):
    """Wichtige Unterscheidung: Eine kaputte Datei rechtfertigt keinen Prozessstart.

    Blender würde denselben Fehler melden, nur drei Sekunden später.
    """
    pfad = schreibe_exr(tmp_path / "kurz.exr", 8, 20, {"V": [1.0] * 160})
    pfad.write_bytes(pfad.read_bytes()[:-50])

    with pytest.raises(BildError) as fehler:
        lies_exr_tiefe_stdlib(pfad)
    assert not isinstance(fehler.value, EXRVarianteError)


# ======================================================================================
# 4 · Der Blender-Rückfall — über die Testnaht, ohne Blender
# ======================================================================================

class Ergebnis:
    """Doppelgänger eines ``subprocess.CompletedProcess``."""

    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode, self.stdout, self.stderr = returncode, stdout, stderr


class Aufrufer:
    """Ersatz für ``_starte``: merkt sich das Kommando und legt Report plus Rohdatei ab."""

    def __init__(self, werte=None, breite=2, hoehe=2, *, report=None, returncode=0):
        self.werte = [1.0, 2.0, 3.0, 4.0] if werte is None else werte
        self.breite, self.hoehe = breite, hoehe
        self.report = report
        self.returncode = returncode
        self.kommandos: list[list[str]] = []

    def __call__(self, cmd, timeout):
        self.kommandos.append(list(cmd))
        out = Path(cmd[cmd.index("--out") + 1])
        roh = out / "tiefe.f32"
        roh.write_bytes(struct.pack(f"<{len(self.werte)}f", *self.werte))
        report = self.report if self.report is not None else {
            "status": "ok", "roh_datei": str(roh),
            "breite": self.breite, "hoehe": self.hoehe, "error": None,
        }
        (out / "exr-report.json").write_text(json.dumps(report), encoding="utf-8")
        return Ergebnis(self.returncode)

    @property
    def kommando(self) -> list[str]:
        assert len(self.kommandos) == 1
        return self.kommandos[0]


def test_rueckfall_startet_blender_ohne_oberflaeche_und_ohne_benutzerprofil(tmp_path, monkeypatch):
    """Regel 2 auch für diesen Runner: Subprozess, keine UI, kein Benutzerprofil."""
    monkeypatch.setenv("AIIMAGING_BLENDER", "/attrappe/blender")
    pfad = schreibe_exr(tmp_path / "piz.exr", 2, 2, {"V": [0.0] * 4}, kompression=4)
    aufrufer = Aufrufer()

    with pytest.warns(BlenderRueckfall):
        werte, breite, hoehe = lies_exr_tiefe(pfad, _starte=aufrufer)

    assert (werte, breite, hoehe) == ([1.0, 2.0, 3.0, 4.0], 2, 2)
    cmd = aufrufer.kommando
    assert cmd[0] == "/attrappe/blender"
    assert "--background" in cmd and "--factory-startup" in cmd
    assert cmd[cmd.index("--python") + 1] == str(bildlesen.EXR_RUNNER)
    assert cmd.index("--") > cmd.index("--python")
    assert cmd[cmd.index("--exr") + 1] == str(pfad)


def test_der_rueckfall_meldet_sich_und_passiert_nie_stillschweigend(tmp_path, monkeypatch):
    """Ab hier hängt das Ergebnis an einem installierten GPL-Binary.

    Das ist erlaubt — es ist eine Prozessgrenze, keine Einverleibung. Aber es ist eine
    Umgebungsanforderung, und die darf nicht unbemerkt in den Code wandern; sonst fällt
    sie erst auf einer fremden Maschine auf.
    """
    monkeypatch.setenv("AIIMAGING_BLENDER", "/attrappe/blender")
    pfad = schreibe_exr(tmp_path / "dwaa.exr", 2, 2, {"V": [0.0] * 4}, kompression=8)

    with pytest.warns(BlenderRueckfall, match="blender --background"):
        lies_exr_tiefe(pfad, _starte=Aufrufer())


def test_lesbare_datei_startet_keinen_subprozess(tmp_path, recwarn):
    """Der Hauptweg ist der stdlib-Weg — sonst wäre die ganze Übung sinnlos."""
    pfad = schreibe_exr(tmp_path / "zip.exr", 4, 4, {"V": [7.0] * 16})

    def niemals(cmd, timeout):
        raise AssertionError(f"Blender wurde gestartet, obwohl nicht nötig: {cmd}")

    werte, _, _ = lies_exr_tiefe(pfad, _starte=niemals)

    assert werte == [7.0] * 16
    assert [w for w in recwarn if issubclass(w.category, BlenderRueckfall)] == []


def test_beschaedigte_datei_loest_keinen_rueckfall_aus(tmp_path):
    """Ein Prozessstart wäre nur eine langsamere Art, denselben Fehler zu melden."""
    pfad = tmp_path / "muell.exr"
    pfad.write_bytes(b"nicht einmal die Signatur stimmt")

    def niemals(cmd, timeout):
        raise AssertionError("Blender wurde für eine kaputte Datei gestartet")

    with pytest.raises(BildError):
        lies_exr_tiefe(pfad, _starte=niemals)


def test_fehlermeldung_des_runners_wird_durchgereicht(tmp_path, monkeypatch):
    """Der Runner meldet Fehler als Report, nicht als Traceback — das muss ankommen."""
    monkeypatch.setenv("AIIMAGING_BLENDER", "/attrappe/blender")
    pfad = schreibe_exr(tmp_path / "a.exr", 2, 2, {"V": [0.0] * 4})
    aufrufer = Aufrufer(report={"status": "error", "error": "RuntimeError: kein Bild"})

    with pytest.raises(BildError, match="kein Bild"):
        lies_exr_tiefe_ueber_blender(pfad, _starte=aufrufer)


def test_rohdatei_falscher_laenge_wird_nicht_verwertet(tmp_path, monkeypatch):
    """Behauptete Bildgrösse und gelieferte Bytes müssen zusammenpassen.

    Sonst entstünde eine Karte, die zu kurz ist — und ``geometrie_qa`` verglich sie
    stillschweigend gegen eine andere Punktmenge.
    """
    monkeypatch.setenv("AIIMAGING_BLENDER", "/attrappe/blender")
    pfad = schreibe_exr(tmp_path / "b.exr", 2, 2, {"V": [0.0] * 4})
    aufrufer = Aufrufer(werte=[1.0, 2.0], breite=4, hoehe=4)     # 2 Werte, 16 behauptet

    with pytest.raises(BildError, match="Bytes"):
        lies_exr_tiefe_ueber_blender(pfad, _starte=aufrufer)


def test_abbruch_des_subprozesses_wird_gemeldet(tmp_path, monkeypatch):
    monkeypatch.setenv("AIIMAGING_BLENDER", "/attrappe/blender")
    pfad = schreibe_exr(tmp_path / "c.exr", 2, 2, {"V": [0.0] * 4})

    with pytest.raises(BildError, match="Code 137"):
        lies_exr_tiefe_ueber_blender(
            pfad, _starte=lambda cmd, timeout: Ergebnis(137, "", "Killed"))


def test_fehlende_datei_startet_keinen_prozess(tmp_path):
    def niemals(cmd, timeout):
        raise AssertionError("Blender wurde für eine nicht vorhandene Datei gestartet")

    with pytest.raises(BildError):
        lies_exr_tiefe_ueber_blender(tmp_path / "weg.exr", _starte=niemals)


# ======================================================================================
# 5 · Die Naht zur Geometrie-QA
# ======================================================================================

@pytest.fixture
def kleiner_lauf(tmp_path):
    """Ein Report, wie ``seams.glb_zu_multipass`` ihn zurückgibt — mit echten Dateien."""
    werte = [10.0, 12.0, 1e10, 20.0]
    exr = schreibe_exr(tmp_path / "tiefe_0001.exr", 2, 2, {"V": werte})
    # Dasselbe Bild normalisiert: nah = hell, Hintergrund 0. Der hinterste
    # Geometriepunkt (20.0) landet dabei ebenfalls auf 0 — die dokumentierte Falle.
    grau = [round((1.0 - (w - 10.0) / 10.0) * 65535) if w < 1e7 else 0 for w in werte]
    png = schreibe_png(tmp_path / "tiefe_norm.png", 2, 2, grau, filterarten=[0, 0])
    return {
        "status": "ok",
        "depth_exr": str(exr),
        "depth_png": str(png),
        "depth_normalisierung": {"min_m": 10.0, "max_m": 20.0},
    }


def test_report_liefert_die_soll_tiefenkarte_aus_der_exr(kleiner_lauf):
    """Der Handgriff, für den es dieses Modul gibt: Report hinein, QA-Eingabe heraus."""
    werte, breite, hoehe = tiefen_aus_report(kleiner_lauf)

    assert (breite, hoehe) == (2, 2)
    assert werte[:2] == [10.0, 12.0]
    assert werte[2] == pytest.approx(1e10, rel=1e-6)


def test_exr_hat_vorrang_weil_nur_sie_die_silhouette_traegt(kleiner_lauf):
    """Der Unterschied ist genau der dokumentierte Verlust — hier an vier Punkten sichtbar.

    Die EXR kennt drei Geometriepunkte, das PNG nur zwei: Der hinterste liegt dort bei
    Grauwert 0 und ist vom Himmel nicht zu unterscheiden.
    """
    aus_exr, _, _ = tiefen_aus_report(kleiner_lauf, quelle=bildlesen.QUELLE_EXR)
    with pytest.warns(SilhouettenVerlust):
        aus_png, _, _ = tiefen_aus_report(kleiner_lauf, quelle=bildlesen.QUELLE_PNG)

    assert sum(geometrie_qa.silhouette(aus_exr)) == 3
    assert sum(geometrie_qa.silhouette(aus_png)) == 2


def test_ohne_exr_faellt_der_report_auf_das_png_zurueck(kleiner_lauf):
    """Liegt nur noch das normalisierte Bild vor, geht es weiter — mit gemeldetem Verlust."""
    kleiner_lauf["depth_exr"] = None

    with pytest.warns(SilhouettenVerlust):
        werte, breite, hoehe = tiefen_aus_report(kleiner_lauf)

    assert (breite, hoehe) == (2, 2)
    assert werte[0] == pytest.approx(10.0)


def test_report_ohne_jede_tiefenkarte_wird_gemeldet():
    with pytest.raises(BildError, match="weder"):
        tiefen_aus_report({"status": "error", "depth_exr": None, "depth_png": None})


def test_png_ohne_normalisierung_ist_kein_tiefenbild(tmp_path):
    """Ohne min_m/max_m ist das PNG ein Graubild, keine Messung."""
    png = schreibe_png(tmp_path / "t.png", 2, 1, [0, 65535], filterarten=[0])

    with pytest.raises(BildError, match="normalisierung"):
        tiefen_aus_report({"depth_exr": None, "depth_png": str(png)})


def test_die_metrik_laeuft_auf_echten_dateien_statt_auf_listen(tmp_path):
    """Der eigentliche Zweck: ``geometrie_score`` auf Zahlen **aus Bilddateien**.

    Eine Tiefenkarte gegen sich selbst muss 1.0 ergeben — das ist die Probe darauf, dass
    zwischen Datei und Metrik nichts verrutscht. Genug Punkte, um über
    ``MIN_GEMEINSAME_PUNKTE`` zu kommen; sonst bliebe der Score ``None``.
    """
    werte = [10.0 + (y * 7 + x) * 0.1 for y in range(8) for x in range(8)]
    exr = schreibe_exr(tmp_path / "selbst.exr", 8, 8, {"V": werte})
    gelesen, _, _ = lies_exr_tiefe(exr)

    ergebnis = geometrie_qa.geometrie_score(gelesen, gelesen)

    assert ergebnis["score"] == 1.0
    assert ergebnis["spearman"] == 1.0
    assert ergebnis["geom_iou"] == 1.0
    assert ergebnis["n_gemeinsam"] == 64
    assert ergebnis["warnungen"] == []


def test_png_und_exr_derselben_szene_stimmen_bis_auf_die_quantisierung_ueberein(tmp_path):
    """Die Abweichung zwischen beiden Wegen darf nur die 16-Bit-Rundung sein.

    Mehr wäre ein Fehler in der Rückrechnung — und weniger ist rechnerisch unmöglich:
    Ein halber Quantisierungsschritt ist die Untergrenze.
    """
    min_m, max_m = 10.0, 20.0
    # Die Werte schöpfen die Spanne genau aus: Der letzte Punkt liegt auf max_m und
    # landet im PNG damit auf Grauwert 0 — das ist der dokumentierte Verlust, an genau
    # einem Punkt vorführbar.
    werte = [min_m + i / 80 * (max_m - min_m) for i in range(81)]
    exr = schreibe_exr(tmp_path / "s.exr", 9, 9, {"V": werte})
    grau = [round((1.0 - (w - min_m) / (max_m - min_m)) * 65535) for w in werte]
    png = schreibe_png(tmp_path / "s.png", 9, 9, grau)

    aus_exr, _, _ = lies_exr_tiefe(exr)
    with pytest.warns(SilhouettenVerlust):
        aus_png = tiefen_aus_png(png, {"min_m": min_m, "max_m": max_m})

    schritt = (max_m - min_m) / 65535
    paare = [(a, b) for a, b in zip(aus_exr, aus_png) if math.isfinite(b)]
    assert len(paare) == 80, "genau der hinterste Punkt fällt im PNG weg"
    assert max(abs(a - b) for a, b in paare) < schritt


# ======================================================================================
# 6 · Die Prozessgrenze bleibt, wo sie war
# ======================================================================================

def test_bildlesen_importiert_kein_bpy():
    """Regel 2 für dieses Modul. Der Gesamtscan liegt in ``test_prozessgrenze.py``;
    hier steht die konkrete Versuchung dieser Aufgabe."""
    quelle = Path(bildlesen.__file__).read_text(encoding="utf-8")
    module = set()
    for knoten in ast.walk(ast.parse(quelle)):
        if isinstance(knoten, ast.Import):
            module.update(a.name.split(".")[0] for a in knoten.names)
        elif isinstance(knoten, ast.ImportFrom) and knoten.level == 0 and knoten.module:
            module.add(knoten.module.split(".")[0])

    assert "bpy" not in module and "ifcopenshell" not in module
    assert not any(m.startswith("aiimaging.runners") for m in module)


def test_der_neue_runner_liegt_jenseits_der_grenze_und_wird_nur_als_pfad_gefuehrt():
    """Wie ``seams.BLENDER_RUNNER``: ein ``Path``, kein Import."""
    assert isinstance(bildlesen.EXR_RUNNER, Path)
    assert bildlesen.EXR_RUNNER.exists()
    assert bildlesen.EXR_RUNNER.parent.name == "runners"
    assert "import bpy" in RUNNER_QUELLE


def test_der_runner_spiegelt_die_zeilenreihenfolge():
    """Die stille Falle jenseits der Grenze — und der Grund, warum sie im Code steht.

    Blenders ``image.pixels`` beginnt in der **unteren** Bildzeile, die EXR-Datei und
    jedes PNG beginnen oben. Ohne Spiegelung wäre die Karte des Rückfallwegs gegenüber
    dem stdlib-Weg senkrecht gekippt — und das Ergebnis sähe weiterhin aus wie eine
    Tiefenkarte. Prüfbar ist das ohne Blender nur am Quelltext; mit Blender prüft es
    ``test_beide_wege_liefern_dieselben_zahlen``.
    """
    assert "[::-1]" in RUNNER_QUELLE
    assert "Non-Color" in RUNNER_QUELLE, "sonst rechnete die Farbverwaltung die Meter um"


def test_keine_bildbibliothek_im_produkt():
    """Die Lizenzentscheidung dieses Moduls, in ausführbarer Form.

    Weder Pillow noch imageio noch OpenImageIO — der PNG-Weg ist ``zlib``, der EXR-Weg
    ebenfalls, und was darüber hinausgeht, läuft über die schon bestehende
    Prozessgrenze zu Blender.
    """
    quelle = Path(bildlesen.__file__).read_text(encoding="utf-8")
    baum = ast.parse(quelle)
    module = set()
    for knoten in ast.walk(baum):
        if isinstance(knoten, ast.Import):
            module.update(a.name.split(".")[0] for a in knoten.names)
        elif isinstance(knoten, ast.ImportFrom) and knoten.level == 0 and knoten.module:
            module.add(knoten.module.split(".")[0])

    for verboten in ("PIL", "Pillow", "imageio", "OpenImageIO", "OpenEXR", "cv2", "numpy"):
        assert verboten not in module, f"{verboten} ist eine Lizenz- und Umgebungsentscheidung"


# ======================================================================================
# 7 · Mit Blender — die eine Zusage, die nur ein echter Lauf belegt
# ======================================================================================

@ohne_blender
def test_beide_wege_liefern_dieselben_zahlen(tmp_path):
    """stdlib-Leser und Blender-Rückfall müssen bis aufs Bit übereinstimmen.

    Das ist der Test, der die ganze Konstruktion trägt: Wären die beiden Wege verschieden
    — in der Zeilenreihenfolge, in der Kanalwahl, in der Farbverwaltung —, hinge das
    Ergebnis der Geometrie-QA davon ab, ob zufällig Blender installiert war.

    Die EXR wird hier geschrieben statt gerendert: Ein Cycles-Durchgang kostete Minuten
    und prüfte nichts, was diese Datei nicht auch prüft.
    """
    werte = [10.0 + (y * 17 + x * 3) * 0.05 for y in range(20) for x in range(11)]
    pfad = schreibe_exr(tmp_path / "beide.exr", 11, 20, {"V": werte})

    ohne, breite_a, hoehe_a = lies_exr_tiefe_stdlib(pfad)
    ueber, breite_b, hoehe_b = lies_exr_tiefe_ueber_blender(pfad)

    assert (breite_a, hoehe_a) == (breite_b, hoehe_b) == (11, 20)
    assert ohne == ueber, "die beiden Wege sind auseinandergelaufen"


@ohne_blender
def test_runner_meldet_seine_kopfdaten(tmp_path):
    """Der Report des Runners trägt, was der Leser braucht — und etwas zur Diagnose."""
    werte = [5.0] * 8 + [1e10] * 8
    pfad = schreibe_exr(tmp_path / "kopf.exr", 4, 4, {"V": werte})
    out = tmp_path / "aus"
    out.mkdir()

    ergebnis = subprocess.run(
        [seams.finde_blender(), "--background", "--factory-startup",
         "--python", str(bildlesen.EXR_RUNNER), "--",
         "--exr", str(pfad), "--out", str(out)],
        capture_output=True, text=True, timeout=300, check=False)

    assert ergebnis.returncode == 0, ergebnis.stderr[-2000:]
    report = json.loads((out / "exr-report.json").read_text(encoding="utf-8"))
    assert report["status"] == "ok", report["error"]
    assert (report["breite"], report["hoehe"]) == (4, 4)
    assert report["dtype"] == "<f4"
    assert report["n_geometriepixel"] == 8, "die acht Hintergrundwerte zählen nicht mit"
    assert report["min_m"] == pytest.approx(5.0)
