"""Von den Zahlen zurück zur Bilddatei — und was der Rückweg unterwegs kostet.

Warum dieses Testmodul den Leser mitbenutzt
-------------------------------------------
``bildschreiben`` ist die Gegenseite zu ``bildlesen``, und die beiden werden hier
gegeneinander geprüft statt jeder für sich. Das ist billiger als eine zweite,
unabhängige PNG-Implementierung im Testcode — und es hat einen Nebennutzen, der kein
Nebennutzen ist: Der Schreiber wählt seinen Zeilenfilter je Zeile nach einer Heuristik,
und wo diese Tests alle fünf Filter erzwingen, prüfen sie zugleich den Entfilterer des
Lesers an Daten, die niemand von Hand gebaut hat.

Der offensichtliche Einwand dagegen — „zwei eigene Fehler heben sich auf" — ist in
``tests/test_bildlesen.py`` schon abgeräumt: Dort steht der Leser gegen einen zweiten,
in diesem Testmodul geschriebenen PNG-Schreiber, der die fünf Filterarten *vorgibt*
statt sie zu wählen. Der Leser ist damit unabhängig belegt und taugt hier als Massstab.

Was hier trotzdem ohne den Leser geprüft wird
----------------------------------------------
Die formale Bauart der Datei — Signatur, IHDR-Felder, Prüfsummen, IEND — wird zusätzlich
mit eigenem Code aus den Rohbytes gelesen. Eine Datei, die nur der eigene Leser versteht,
wäre kein PNG, sondern ein Hausformat mit PNG-Endung; das fiele mit ``bildlesen`` allein
nicht auf.

Reine Standardbibliothek, keine GPU, kein Blender, kein Pillow, kein numpy — dasselbe
Versprechen, das das Modul selbst gibt (``pyproject.toml``: keine Laufzeitabhängigkeiten).
"""
from __future__ import annotations

import math
import random
import struct
import zlib
from pathlib import Path

import pytest

from aiimaging import bildlesen, bildschreiben
from aiimaging.bildschreiben import (
    HINTERGRUND_AB_M,
    HINTERGRUND_GRAUWERT,
    KONVENTION,
    RUECKRECHNUNG,
    SchreibError,
    normalisiere_tiefe,
    schreibe_graustufen_png,
    tiefe_exr_zu_png,
)


# ======================================================================================
# Werkzeuge: die Datei einmal ohne den Leser des Projekts auseinandernehmen
# ======================================================================================

def bloecke_roh(daten: bytes) -> list[tuple[bytes, bytes, int]]:
    """Eine PNG-Datei in ``(Kennung, Nutzlast, gespeicherte Prüfsumme)`` zerlegen.

    Bewusst ohne ``bildlesen._png_bloecke``: Diese Funktion prüft nichts, sie liest nur
    ab. Erst dadurch kann ein Test die Prüfsummen des Schreibers *selbst* nachrechnen,
    statt sich auf den Leser zu verlassen, der bei einer falschen Summe ohnehin schon
    abgebrochen hätte.
    """
    assert daten[:8] == b"\x89PNG\r\n\x1a\n"
    aus: list[tuple[bytes, bytes, int]] = []
    pos = 8
    while pos < len(daten):
        laenge = int.from_bytes(daten[pos:pos + 4], "big")
        typ = daten[pos + 4:pos + 8]
        inhalt = daten[pos + 8:pos + 8 + laenge]
        crc = int.from_bytes(daten[pos + 8 + laenge:pos + 12 + laenge], "big")
        aus.append((typ, inhalt, crc))
        pos += 12 + laenge
    return aus


def idat_entpackt(pfad: Path) -> bytes:
    """Der entpackte Bilddatenstrom — samt Filterbyte am Anfang jeder Zeile.

    Geht über ``bildlesen._png_bloecke``, weil das nebenbei jede Prüfsumme prüft: Wo
    dieser Aufruf durchläuft, ist die Datei auch für den Leser unversehrt.
    """
    daten = Path(pfad).read_bytes()
    idat = b"".join(inhalt for typ, inhalt in bildlesen._png_bloecke(daten, pfad)
                    if typ == b"IDAT")
    return zlib.decompress(idat)


def filterarten(pfad: Path) -> list[int]:
    """Welche Filterart der Schreiber je Zeile tatsächlich gewählt hat."""
    _werte, breite, hoehe, bittiefe = bildlesen._png_lesen(pfad)
    zeilenlaenge = breite * (bittiefe // 8)
    roh = idat_entpackt(pfad)
    return [roh[y * (zeilenlaenge + 1)] for y in range(hoehe)]


#: Breite der Filter-Testbilder. Klein genug für Millisekunden, breit genug, dass die
#: Kostenschätzung der Heuristik nicht am ersten Bildpunkt hängt.
FILTER_BREITE = 12


def bild_mit_allen_fuenf_filtern() -> tuple[list[float], int, int]:
    """Ein Bild, dessen acht Zeilen die Heuristik durch alle fünf Filter treiben.

    Jede Zeile ist so gebaut, dass genau ein Filter die kleinste Summe der absoluten
    (vorzeichenbehafteten) Abweichungen liefert:

    * schwarze Zeile → **None**: die Rohbytes sind schon null, kleiner geht nicht.
    * konstante helle Zeile nach der schwarzen → **Sub**: nur der erste Bildpunkt bleibt.
    * dieselbe Zeile noch einmal → **Up**: die Differenz zur Zeile darüber ist überall 0.
    * eine Zeile, die punktweise das Mittel aus linkem und oberem Nachbarn ist →
      **Average**, ebenfalls mit Rest 0.
    * ein diagonaler Verlauf → **Paeth**, der einzige Filter, der schräge Muster fasst.

    Die Werte sind Vielfache von ``1/255``. Das ist kein Zufall: In 16 Bit wird daraus
    ``b * 257``, also zweimal dasselbe Byte je Bildpunkt, und weil ``Sub``, ``Average``
    und ``Paeth`` mit ``bpp = 2`` byteweise um genau einen Bildpunkt zurückgreifen,
    fallen in beiden Bittiefen dieselben Entscheidungen. Ein Bild, zwei Bittiefen.
    """
    breite = FILTER_BREITE

    mittel = []                      # z[i] = (z[i-1] + oben[i]) >> 1, oben ist konstant
    links = 0
    for _ in range(breite):
        links = (links + 200) >> 1
        mittel.append(links)

    def diagonal(y: int) -> list[int]:
        return [(x * 7 + y * 13) % 256 for x in range(breite)]

    zeilen = [
        [0] * breite,                # None
        [200] * breite,              # Sub
        [200] * breite,              # Up
        mittel,                      # Average
        diagonal(0), diagonal(1),    # Anlauf: der Verlauf muss erst zwei Zeilen hoch sein
        diagonal(2), diagonal(3),    # Paeth
    ]
    werte = [b / 255.0 for zeile in zeilen for b in zeile]
    return werte, breite, len(zeilen)


def halbe_stufe(bittiefe: int) -> float:
    """Die grösste Abweichung, die Runden auf ein Raster dieser Bittiefe erzeugen kann."""
    return 0.5 / ((1 << bittiefe) - 1)


# ======================================================================================
# 1 · Rundlauf: was hineingeht, kommt heraus
# ======================================================================================

@pytest.mark.parametrize("bittiefe", [8, 16])
def test_geschriebene_grauwerte_kommen_bis_auf_eine_halbe_stufe_zurueck(tmp_path, bittiefe):
    """Die Grundzusage des Schreibers, und die einzige Abweichung, die er haben darf.

    Ein PNG speichert ganze Stufen; ein Grauwert dazwischen wird gerundet. Mehr als eine
    **halbe** Stufe darf dabei nie verloren gehen — wäre es mehr, wäre nicht die
    Quantisierung die Ursache, sondern ein Fehler in der Umrechnung, und der sähe im
    fertigen Bild genauso aus wie Rundung.
    """
    zufall = random.Random(bittiefe)
    breite, hoehe = 9, 7
    werte = [zufall.random() for _ in range(breite * hoehe)]

    pfad = schreibe_graustufen_png(tmp_path / f"rund{bittiefe}.png", werte, breite, hoehe,
                                   bittiefe=bittiefe)
    gelesen, b, h = bildlesen.lies_png_graustufen(pfad)

    assert (b, h) == (breite, hoehe)
    assert len(gelesen) == breite * hoehe
    abweichung = max(abs(a - e) for a, e in zip(gelesen, werte))
    assert abweichung <= halbe_stufe(bittiefe) + 1e-12
    assert abweichung > 0.0, "bei Zufallswerten muss überhaupt gerundet worden sein"


@pytest.mark.parametrize("bittiefe", [8, 16])
def test_die_raender_null_und_eins_bleiben_exakt(tmp_path, bittiefe):
    """0 und 1 sind keine Zwischenwerte — sie müssen die Kette unverfälscht überstehen.

    An ihnen hängt Bedeutung: 0 ist der Hintergrund (``HINTERGRUND_GRAUWERT``), 1 der
    nächste Punkt der Geometrie. Ein Rundungsfehler an dieser Stelle machte aus einem
    Hintergrundpunkt eine Geometrie in maximaler Entfernung.
    """
    pfad = schreibe_graustufen_png(tmp_path / f"rand{bittiefe}.png", [0.0, 1.0, 0.5], 3, 1,
                                   bittiefe=bittiefe)

    gelesen, _, _ = bildlesen.lies_png_graustufen(pfad)

    assert gelesen[0] == 0.0
    assert gelesen[1] == 1.0
    assert gelesen[2] == pytest.approx(0.5, abs=halbe_stufe(bittiefe) + 1e-12)


def test_zeilen_werden_von_oben_nach_unten_geschrieben(tmp_path):
    """Die Reihenfolge ist eine Zusage zwischen Schreiber und Leser, keine Nebensache.

    ``geometrie_qa`` setzt Indexgleichheit von Soll- und Ist-Karte voraus und erkennt
    einen Versatz nicht — es bestraft ihn nur mit einem schlechteren Score, ohne die
    Ursache zu nennen. Ein gekippt geschriebenes Bild wäre also ein unsichtbarer Fehler.
    """
    pfad = schreibe_graustufen_png(tmp_path / "oben_unten.png",
                                   [0.0, 0.0, 1.0, 1.0], 2, 2)

    gelesen, _, _ = bildlesen.lies_png_graustufen(pfad)

    assert gelesen[:2] == [0.0, 0.0], "die zuerst übergebene Zeile ist die oberste"
    assert gelesen[2:] == [1.0, 1.0]


def test_ein_bild_mit_einem_einzigen_bildpunkt_ist_zulaessig(tmp_path):
    """1×1 ist der kleinste Fall, den die Prüfungen durchlassen — er muss auch laufen.

    Bei ihm greift keine der Abkürzungen: keine linke Nachbarschaft, keine Zeile darüber.
    """
    pfad = schreibe_graustufen_png(tmp_path / "punkt.png", [0.25], 1, 1)

    gelesen, breite, hoehe = bildlesen.lies_png_graustufen(pfad)

    assert (breite, hoehe) == (1, 1)
    assert gelesen[0] == pytest.approx(0.25, abs=halbe_stufe(16))


def test_derselbe_inhalt_ergibt_dieselbe_datei(tmp_path):
    """Zweimal geschrieben, zweimal byteweise gleich.

    Nicht Selbstzweck: Ein Schreiber, dessen Ausgabe zwischen zwei Läufen wackelt, macht
    jeden Vergleich zweier Läufe zu einer Zufallsfrage — und die Vertiefungsarbeit lebt
    davon, Läufe zu vergleichen.
    """
    werte = [(i % 37) / 36.0 for i in range(6 * 5)]

    eins = schreibe_graustufen_png(tmp_path / "a.png", werte, 6, 5)
    zwei = schreibe_graustufen_png(tmp_path / "b.png", werte, 6, 5)

    assert eins.read_bytes() == zwei.read_bytes()


def test_der_geschriebene_pfad_kommt_als_pfad_zurueck(tmp_path):
    """Aufrufer sollen den Rückgabewert weiterreichen können, auch wenn sie einen
    Zeichenketten-Pfad übergeben haben."""
    ziel = tmp_path / "rueckgabe.png"

    ergebnis = schreibe_graustufen_png(str(ziel), [0.5], 1, 1)

    assert isinstance(ergebnis, Path)
    assert ergebnis == ziel
    assert ziel.exists()


# ======================================================================================
# 2 · Die fünf Zeilenfilter — der eigentliche Grund für die Heuristik
# ======================================================================================

@pytest.mark.parametrize("bittiefe", [8, 16])
def test_alle_fuenf_zeilenfilter_kommen_tatsaechlich_vor(tmp_path, bittiefe):
    """Der Zweck der Heuristik ist nicht nur Plattenplatz — das sagt das Modul selbst.

    Ein Schreiber, der immer denselben Filter wählte, liesse vier Fünftel des
    Entfilterers in ``bildlesen`` ungeprüft. Erst hier entstehen die Daten, an denen der
    Leser mit Sub, Up, Average und Paeth arbeiten muss.
    """
    werte, breite, hoehe = bild_mit_allen_fuenf_filtern()
    pfad = schreibe_graustufen_png(tmp_path / f"filter{bittiefe}.png", werte, breite, hoehe,
                                   bittiefe=bittiefe)

    arten = filterarten(pfad)

    assert set(arten) == {0, 1, 2, 3, 4}, f"gewählt wurden nur {sorted(set(arten))}"


@pytest.mark.parametrize("bittiefe", [8, 16])
def test_das_filterbild_kommt_trotz_aller_fuenf_filter_unveraendert_zurueck(tmp_path,
                                                                           bittiefe):
    """Filter dürfen nichts kosten: Sie sind Kompression, keine Umrechnung.

    Das ist der Test, um dessentwillen die Heuristik überhaupt getestet wird — er lässt
    den Entfilterer des Lesers gegen echte, gewählte (nicht vorgegebene) Filter laufen.
    """
    werte, breite, hoehe = bild_mit_allen_fuenf_filtern()
    pfad = schreibe_graustufen_png(tmp_path / f"filterrund{bittiefe}.png", werte,
                                   breite, hoehe, bittiefe=bittiefe)

    gelesen, _, _ = bildlesen.lies_png_graustufen(pfad)

    assert max(abs(a - e) for a, e in zip(gelesen, werte)) <= halbe_stufe(bittiefe) + 1e-12


def test_konstante_zeilen_werden_gegen_die_zeile_darueber_gefiltert(tmp_path):
    """Up ist für flächige Bereiche der richtige Filter — und Tiefenbilder sind flächig.

    Eine Wand füllt viele Zeilen mit fast demselben Verlauf. Fiele die Heuristik hier auf
    None zurück, wüchse das PNG um ein Vielfaches, ohne dass jemand es bemerkte.
    """
    werte = [0.5] * (8 * 4)

    pfad = schreibe_graustufen_png(tmp_path / "flaeche.png", werte, 8, 4)

    assert filterarten(pfad)[1:] == [2, 2, 2], "ab der zweiten Zeile ist Up gratis"


def test_rauschen_wird_nicht_schlechter_als_ungefiltert_abgelegt(tmp_path):
    """Wo kein Nachbar etwas vorhersagt, darf die Heuristik nichts verschlimmern.

    Die Kostenschätzung ist genau dafür da: Bei Rauschen ist jede Differenzbildung
    genauso teuer wie der Rohwert — die gewählte Zeile darf also nie *mehr* kosten als
    die ungefilterte.
    """
    zufall = random.Random(4711)
    breite, hoehe = 16, 8
    werte = [zufall.random() for _ in range(breite * hoehe)]
    pfad = schreibe_graustufen_png(tmp_path / "rauschen.png", werte, breite, hoehe,
                                   bittiefe=8)

    roh = idat_entpackt(pfad)

    def kosten(daten: bytes) -> int:
        return sum(b if b < 128 else 256 - b for b in daten)

    for y in range(hoehe):
        zeile = roh[y * (breite + 1) + 1:(y + 1) * (breite + 1)]
        ungefiltert = bytes(round(w * 255) for w in werte[y * breite:(y + 1) * breite])
        assert kosten(zeile) <= kosten(ungefiltert)


def test_jede_zeile_traegt_genau_ein_filterbyte(tmp_path):
    """Die Länge des Datenstroms ist eine harte Zusage der Spezifikation.

    Ein Byte zu viel oder zu wenig verschiebt alles Folgende — und ein Leser liest daraus
    kein Chaos, sondern ein plausibel aussehendes, falsches Bild.
    """
    breite, hoehe = 5, 6
    werte = [0.3] * (breite * hoehe)

    for bittiefe in (8, 16):
        pfad = schreibe_graustufen_png(tmp_path / f"laenge{bittiefe}.png", werte,
                                       breite, hoehe, bittiefe=bittiefe)
        roh = idat_entpackt(pfad)
        assert len(roh) == hoehe * (breite * (bittiefe // 8) + 1)
        assert all(art in (0, 1, 2, 3, 4) for art in filterarten(pfad))


# ======================================================================================
# 3 · Die Datei ist ein PNG, nicht nur etwas, das der eigene Leser versteht
# ======================================================================================

def test_signatur_blockfolge_und_iend_entsprechen_der_spezifikation(tmp_path):
    """Gegen die Rohbytes geprüft, nicht gegen den eigenen Leser.

    Ein Format, das nur das eigene Gegenstück lesen kann, ist kein PNG — und der Ausweg
    ins Werkzeug von jemand anderem (Bildbetrachter, ControlNet-Vorverarbeitung) stünde
    erst dann offen, wenn es zu spät ist.
    """
    pfad = schreibe_graustufen_png(tmp_path / "form.png", [0.1, 0.9, 0.5, 0.2], 2, 2)
    daten = pfad.read_bytes()

    assert daten[:8] == bildlesen.PNG_SIGNATUR
    bloecke = bloecke_roh(daten)
    assert [typ for typ, _, _ in bloecke] == [b"IHDR", b"IDAT", b"IEND"]
    assert bloecke[-1][1] == b"", "IEND ist leer"
    assert daten.endswith(b"\x00\x00\x00\x00IEND\xaeB`\x82"), "IEND steht am Dateiende"


@pytest.mark.parametrize("bittiefe", [8, 16])
def test_ihdr_beschreibt_das_bild_das_geschrieben_wurde(tmp_path, bittiefe):
    """Der Kopf ist die einzige Stelle, an der Breite, Höhe und Bittiefe stehen.

    Farbtyp 0 (Graustufen) ist dabei Absicht und nicht Vorgabe: ``bildlesen`` weist
    RGB-Dateien als Tiefenkarte ausdrücklich ab, weil aus drei Farbkanälen eine
    Entfernung zu machen geraten wäre. Ein Schreiber, der versehentlich RGB anschriebe,
    erzeugte Dateien, die die eigene Kette nicht mehr annimmt.
    """
    pfad = schreibe_graustufen_png(tmp_path / f"kopf{bittiefe}.png", [0.5] * 12, 4, 3,
                                   bittiefe=bittiefe)

    typ, inhalt, _crc = bloecke_roh(pfad.read_bytes())[0]

    assert typ == b"IHDR"
    assert len(inhalt) == 13
    breite, hoehe, tiefe, farbtyp, kompression, filter_, verschraenkt = struct.unpack(
        ">IIBBBBB", inhalt)
    assert (breite, hoehe) == (4, 3)
    assert tiefe == bittiefe
    assert farbtyp == 0, "Graustufen"
    assert (kompression, filter_, verschraenkt) == (0, 0, 0), "die Spezifikation kennt nur 0/0/0"


def test_jeder_block_traegt_seine_richtige_pruefsumme(tmp_path):
    """Die Prüfsumme ist der Test, an dem sich dieses Projekt schon zweimal gerettet hat.

    Sie im Schreiber falsch zu berechnen wäre besonders bitter: Die Datei sähe gut aus,
    und erst der Leser meldete sie als beschädigt — die Suche liefe dann in die falsche
    Richtung. Deshalb hier zweimal geprüft: einmal selbst nachgerechnet, einmal durch
    ``bildlesen._png_bloecke``, das jede Summe prüft.
    """
    pfad = schreibe_graustufen_png(tmp_path / "crc.png", [0.2] * 20, 5, 4)
    daten = pfad.read_bytes()

    for typ, inhalt, gespeichert in bloecke_roh(daten):
        assert gespeichert == zlib.crc32(typ + inhalt) & 0xFFFFFFFF, f"{typ!r}"

    assert [typ for typ, _ in bildlesen._png_bloecke(daten, pfad)] == [
        b"IHDR", b"IDAT", b"IEND"]


def test_ein_gekipptes_byte_faellt_dem_leser_auf(tmp_path):
    """Gegenprobe zur vorigen Zusage: Die Prüfsummen sind wirksam, nicht bloss vorhanden.

    Ohne diesen Test hiesse „alle Prüfsummen stimmen" auch dann noch, wenn der Schreiber
    sie über die falschen Bytes rechnete und der Leser denselben Fehler machte.
    """
    pfad = schreibe_graustufen_png(tmp_path / "kaputt.png", [0.4] * 16, 4, 4)
    roh = bytearray(pfad.read_bytes())
    # Ein Byte mitten in der Nutzlast des IDAT-Blocks kippen — nicht in einem Längenfeld,
    # sonst meldete der Leser „abgeschnitten" und die Prüfsumme bliebe ungeprüft.
    beginn = 8 + 12 + 13 + 8                        # Signatur, IHDR-Rahmen, IHDR, IDAT-Kopf
    roh[beginn + 2] ^= 0xFF
    pfad.write_bytes(bytes(roh))

    with pytest.raises(bildlesen.BildError, match="Prüfsumme"):
        bildlesen.lies_png_graustufen(pfad)


def test_die_bilddaten_liegen_in_einem_zlib_strom(tmp_path):
    """IDAT ist deflate-verpackt — und zwar so, dass es auch ohne den eigenen Leser aufgeht."""
    pfad = schreibe_graustufen_png(tmp_path / "zlib.png", [0.0, 1.0], 2, 1, bittiefe=8)

    _typ, inhalt, _crc = bloecke_roh(pfad.read_bytes())[1]

    assert zlib.decompress(inhalt) == b"\x00\x00\xff", "Filter None, dann die zwei Bytes"


# ======================================================================================
# 4 · Werte ausserhalb 0..1 — beschneiden statt abbrechen
# ======================================================================================

@pytest.mark.parametrize("bittiefe", [8, 16])
def test_werte_ausserhalb_null_bis_eins_werden_beschnitten(tmp_path, bittiefe):
    """Das dokumentierte Verhalten, und es muss auch wirklich beschneiden.

    Solche Werte entstehen bei Rundung an den Rändern; ein Abbruch dafür wäre eine
    Strenge ohne Nutzen. Der stille Gegenfehler wäre schlimmer: ein Überlauf, der aus
    1,0001 den Grauwert 0 machte — aus dem nächsten Punkt der Szene würde der fernste.
    """
    werte = [-42.0, -0.001, 0.5, 1.0001, 7.0]

    pfad = schreibe_graustufen_png(tmp_path / f"clamp{bittiefe}.png", werte, 5, 1,
                                   bittiefe=bittiefe)
    gelesen, _, _ = bildlesen.lies_png_graustufen(pfad)

    assert gelesen[0] == gelesen[1] == 0.0
    assert gelesen[2] == pytest.approx(0.5, abs=halbe_stufe(bittiefe) + 1e-12)
    assert gelesen[3] == gelesen[4] == 1.0


@pytest.mark.parametrize("wert, erwartet", [(math.inf, 1.0), (-math.inf, 0.0)])
def test_unendliche_werte_werden_beschnitten_wie_alles_ausserhalb(tmp_path, wert, erwartet):
    """Unendlich ist der Grenzfall von „ausserhalb 0..1" und müsste dieselbe Regel treffen."""
    pfad = schreibe_graustufen_png(tmp_path / "inf.png", [wert], 1, 1)

    gelesen, _, _ = bildlesen.lies_png_graustufen(pfad)

    assert gelesen[0] == erwartet


def test_nan_wird_als_schreibfehler_gemeldet(tmp_path):
    """Ein NaN ist kein Grauwert — und das gehört gesagt, nicht durchgereicht."""
    with pytest.raises(SchreibError):
        schreibe_graustufen_png(tmp_path / "nan.png", [math.nan], 1, 1)


# ======================================================================================
# 5 · Was der Schreiber ehrlich abweist
# ======================================================================================

def test_schreibfehler_bleibt_ein_valuefehler():
    """Bestehendes ``except ValueError`` soll weiter greifen — dieselbe Wahl wie in
    ``bildlesen.BildError`` und ``geometrie_qa.QaError``."""
    assert issubclass(SchreibError, ValueError)


@pytest.mark.parametrize("werte, breite, hoehe, muster", [
    ([0.0] * 11, 4, 3, "11 Werte"),
    ([0.0] * 13, 4, 3, "13 Werte"),
    ([], 1, 1, "0 Werte"),
])
def test_falsche_wertezahl_wird_nicht_stillschweigend_aufgefuellt(tmp_path, werte, breite,
                                                                  hoehe, muster):
    """Ein Bild mit fehlenden Werten wäre nicht leer, sondern **verschoben**.

    Genau das ist der teure Fehler: Die QA verglich dann zwei Karten, die um n Bildpunkte
    gegeneinander versetzt sind, und meldete eine schlechte Geometrie statt eines
    Datenfehlers.
    """
    with pytest.raises(SchreibError, match=muster):
        schreibe_graustufen_png(tmp_path / "x.png", werte, breite, hoehe)


@pytest.mark.parametrize("breite, hoehe", [(0, 4), (4, 0), (0, 0), (-2, 4), (4, -2)])
def test_nicht_positive_masse_werden_abgewiesen(tmp_path, breite, hoehe):
    """Ein Bild ohne Fläche gibt es nicht — und ``bildlesen`` weist es ebenfalls ab.

    Ohne diese Prüfung entstünde bei 0×0 eine formal gültige Datei, die der eigene Leser
    dann als „leeres Bild" zurückwiese: derselbe Abbruch, nur einen Arbeitsschritt zu spät.
    """
    with pytest.raises(SchreibError, match="positiv"):
        schreibe_graustufen_png(tmp_path / "x.png", [], breite, hoehe)


@pytest.mark.parametrize("bittiefe", [1, 2, 4, 24, 32, 0, -16, "16", None])
def test_andere_bittiefen_als_acht_und_sechzehn_werden_abgewiesen(tmp_path, bittiefe):
    """1, 2 und 4 Bit packen mehrere Bildpunkte in ein Byte — der Schreiber kann das nicht,
    und der Leser nähme es ohnehin nicht an (16 Stufen für die ganze Bautiefe).

    Auch die Zeichenkette ``"16"`` wird abgewiesen und nicht umgewandelt: Sie käme aus
    einer Konfigurationsdatei, und stillschweigende Umwandlung ist genau die Stelle, an
    der eine falsche Zahl unbemerkt durchrutscht.
    """
    with pytest.raises(SchreibError, match="bittiefe"):
        schreibe_graustufen_png(tmp_path / "x.png", [0.5], 1, 1, bittiefe=bittiefe)


def test_bei_abgewiesener_eingabe_entsteht_keine_halbe_datei(tmp_path):
    """Eine Datei, die existiert und nichts taugt, ist teurer als gar keine.

    „Existenz ist kein Beleg für Inhalt" ist die wiederkehrende Lehre dieses Projekts —
    der Schreiber soll sie nicht selbst noch einmal bestätigen.
    """
    ziel = tmp_path / "nie.png"

    with pytest.raises(SchreibError):
        schreibe_graustufen_png(ziel, [0.0] * 3, 2, 2)

    assert not ziel.exists()


# ======================================================================================
# 6 · normalisiere_tiefe — Meter zu Grauwerten, nah = hell
# ======================================================================================

def test_der_naechste_punkt_wird_hell_der_fernste_dunkel():
    """Die ControlNet-Konvention, und der Fehler, den ihre Umkehrung anrichtete.

    Verdreht wäre die Tiefenordnung gespiegelt: Die Rangkorrelation der Geometrie-QA
    meldete −1 auf einer völlig korrekten Geometrie, und die Suche liefe in der Szene
    statt in der Umrechnung.
    """
    grau, norm = normalisiere_tiefe([10.0, 15.0, 20.0])

    assert grau[0] == 1.0, "nah = hell"
    assert grau[2] == 0.0
    assert grau[1] == pytest.approx(0.5)
    assert (norm["min_m"], norm["max_m"]) == (10.0, 20.0)


def test_die_normalisierung_traegt_alles_was_die_rueckrechnung_braucht():
    """Ohne ``min_m``/``max_m`` ist das PNG nur noch ein Graubild.

    Die Felder sind kein Beiwerk, sondern der einzige Bezug zwischen einem Grauwert und
    einem Meter — ``bildlesen._normalisierung_lesen`` bricht ohne sie ab.
    """
    _grau, norm = normalisiere_tiefe([4.0, 8.0, 12.0])

    assert set(norm) == {
        "min_m", "max_m", "konvention", "hintergrund_grauwert", "rueckrechnung",
        "n_geometriepixel", "hintergrund_ab_m", "quelle",
        # Seit dem 16.09.2026: die Lücken-Messung, die immer läuft, und was das Klemmen
        # für die Rückrechnung hiesse. Siehe Abschnitt 6b.
        "max_m_luecke", "luecke", "ferne_getrennt",
        "geklemmt_ab_m", "n_geklemmt", "max_m_gemessen", "rueckrechnung_vorbehalt",
        "warnungen",
    }
    assert norm["konvention"] == KONVENTION
    assert norm["rueckrechnung"] == RUECKRECHNUNG
    assert norm["hintergrund_grauwert"] == HINTERGRUND_GRAUWERT
    assert norm["hintergrund_ab_m"] == HINTERGRUND_AB_M
    assert norm["quelle"] == "produkt", "nicht mehr Blender — das ist der ganze Punkt"
    assert isinstance(norm["min_m"], float) and isinstance(norm["max_m"], float)


def test_die_normalisierung_wird_vom_leser_angenommen():
    """Der Vertrag zwischen den beiden Modulen, an einer Stelle geprüft statt zweimal
    beschrieben. ``_normalisierung_lesen`` ist streng — hier zeigt sich, ob der Schreiber
    seine eigene Kette bedient."""
    _grau, norm = normalisiere_tiefe([3.0, 9.0])

    assert bildlesen._normalisierung_lesen(norm) == (3.0, 9.0)


@pytest.mark.parametrize("wert, name", [
    (HINTERGRUND_AB_M, "genau auf der Schranke"),
    (HINTERGRUND_AB_M * 10, "jenseits der Schranke"),
    (1e10, "wie Cycles es für Strahlen ins Leere schreibt"),
    (math.inf, "unendlich"),
    (-math.inf, "minus unendlich"),
    (math.nan, "keine Zahl"),
    (0.0, "null Meter"),
    (-5.0, "hinter der Kamera"),
])
def test_alles_was_keine_geometrie_ist_wird_hintergrund(wert, name):
    """Ein Wert, der keine Entfernung sein kann, darf die Skala nicht mitbestimmen.

    Das ist der Grund gegen Blenders ``Normalize``-Knoten: Er normalisiert über alle
    Bildpunkte und drückt das Gebäude damit in die untersten Promille des Wertebereichs.
    Die Schranke ist hier ausdrücklich, damit sie prüfbar ist.
    """
    grau, norm = normalisiere_tiefe([10.0, wert, 20.0])

    assert grau[1] == HINTERGRUND_GRAUWERT, name
    assert norm["n_geometriepixel"] == 2
    assert (norm["min_m"], norm["max_m"]) == (10.0, 20.0), "der Fremdwert zieht die Skala nicht"


def test_die_hintergrundschranke_laesst_sich_setzen_und_steht_im_ergebnis():
    """Wer die Schranke verschiebt, verschiebt ``min_m`` und ``max_m`` mit — deshalb
    gehört der benutzte Wert in die Datei und nicht in den Kopf des Ausführenden."""
    grau, norm = normalisiere_tiefe([10.0, 50.0, 20.0], hintergrund_ab_m=30.0)

    assert grau[1] == HINTERGRUND_GRAUWERT
    assert (norm["min_m"], norm["max_m"]) == (10.0, 20.0)
    assert norm["hintergrund_ab_m"] == 30.0
    assert norm["n_geometriepixel"] == 2


def test_eine_ebene_flaeche_frontal_teilt_nicht_durch_null():
    """Spanne 0 ist kein Kuriosum, sondern eine Wand, die die Kamera frontal ansieht.

    Ohne den Sonderfall stünde hier eine Division durch 0 — und zwar erst dann, wenn
    jemand das erste Mal genau so rendert.
    """
    grau, norm = normalisiere_tiefe([7.5, 7.5, 7.5])

    assert grau == [1.0, 1.0, 1.0], "alles gleich nah, also alles gleich hell"
    assert norm["min_m"] == norm["max_m"] == 7.5
    assert norm["n_geometriepixel"] == 3


def test_ein_einziger_geometriepunkt_ist_ebenfalls_spanne_null():
    """Derselbe Sonderfall von der anderen Seite: ein Treffer, sonst Himmel."""
    grau, norm = normalisiere_tiefe([1e10, 12.0, math.inf])

    assert grau == [0.0, 1.0, 0.0]
    assert norm["n_geometriepixel"] == 1


def test_ohne_einen_einzigen_geometriepunkt_wird_abgebrochen():
    """Ein schwarzes Bild zu schreiben wäre die teuerste Art, zu erfahren, dass die
    Kamera nichts sieht — man merkt es erst am fertigen Render.

    Die Meldung schickt bewusst zur Kamera und nicht zur Schranke: Die Schranke ist der
    seltenere Fehler, und wer an ihr dreht, verdeckt den echten.
    """
    with pytest.raises(SchreibError, match="Geometriepixel") as fehler:
        normalisiere_tiefe([1e10, math.inf, 0.0, -1.0, math.nan])

    assert "Kamera" in str(fehler.value)


def test_ein_leeres_tiefenbild_ist_ebenfalls_ein_abbruch():
    """Null Werte sind der Grenzfall von „kein Geometriepixel", nicht ein eigener Weg."""
    with pytest.raises(SchreibError, match="Geometriepixel"):
        normalisiere_tiefe([])


def test_die_grauwerte_bleiben_im_einheitsintervall():
    """Was hier herauskommt, geht ungeprüft in den Schreiber — dort würde ein Ausreisser
    beschnitten und wäre danach nicht mehr auffindbar."""
    zufall = random.Random(11)
    tiefen = [zufall.uniform(0.5, 400.0) for _ in range(200)] + [1e10] * 20

    grau, _norm = normalisiere_tiefe(tiefen)

    assert min(grau) == 0.0 and max(grau) == 1.0
    assert all(0.0 <= wert <= 1.0 for wert in grau)


# ======================================================================================
# 6b · Die Lücken-Trennung — die Messung läuft immer, das Verhalten ist aus
# ======================================================================================
#
# DER BEFUND. Die HomeStation meldete am 11.09.2026 eine flachgedrückte Tiefenkarte
# (Mittel 0.9869, 98.7 % der Punkte über 0.99) und hielt das für einen Fehler ihrer
# eigenen Normierung über ein 99er-Perzentil. Es war unsere. `normalisiere_tiefe` nimmt
# als `max_m` das grösste gültige Mass unterhalb von `hintergrund_ab_m` (1e7) — eine
# Fernsichtebene bei 1600 m liegt weit darunter, gilt also als Geometrie und frisst den
# ganzen Wertebereich. Die feste Schranke löst nur den EXTREMEN Fall; sie setzt genau wie
# ein festes Perzentil voraus, dass man vorher weiss, wo die Ferne anfängt.
#
# DIE VERTEILUNG STEHT IM TESTCODE und nicht in einer Fixture-Datei: Sie ist aus der
# Meldung nachgebildet (Innenraum 1.75..10 m mit 2000 Punkten, 23 Punkte bei 1600 m), und
# eine Probe, die ihre eigenen Zahlen zeigt, ist nachrechenbar.

def szene_elfter_september(n_innen: int = 2000, n_ferne: int = 23) -> list[float]:
    """Die Verteilung aus der HomeStation-Meldung vom 11.09.2026, hier erzeugt.

    Innenraum von 1.75 m bis 10 m, dazu eine Fernsichtebene bei 1600 m. Die 23 Punkte
    sind 1.14 % der Karte — also MEHR als das eine Prozent, das ein 99er-Perzentil
    wegschneidet. Genau daran ist der Perzentil-Weg drüben gescheitert.
    """
    innen = [1.75 + (10.0 - 1.75) * i / (n_innen - 1) for i in range(n_innen)]
    return innen + [1600.0] * n_ferne


def test_die_vorgabe_ist_aus_und_das_schuetzt_die_homestation():
    """**Die wichtigste Probe dieses Abschnitts.**

    Die HomeStation führt unseren Code aus diesem Repo aus. Ein ``git pull`` dort ändert
    sonst still, was gerechnet wird — und eine Verhaltensänderung, die nicht angesagt
    wurde, sieht drüben nicht wie eine Änderung aus, sondern wie ein Fehler.

    Geprüft wird beides: die Signatur (damit der Vorgabewert nicht unbemerkt kippt) und
    das Ergebnis (damit ein umgangener Vorgabewert nicht doch wirkt).
    """
    import inspect

    vorgabe = inspect.signature(normalisiere_tiefe).parameters["ferne_trennen"].default
    assert vorgabe is False, "Vorgabe AUS — das ist die Zusage an die HomeStation"

    _grau, norm = normalisiere_tiefe(szene_elfter_september())

    assert norm["ferne_getrennt"] is False
    assert norm["max_m"] == 1600.0, "ohne Ansage bleibt die Skala, die drüben erwartet wird"
    assert norm["geklemmt_ab_m"] is None and norm["n_geklemmt"] == 0


def test_der_befund_vom_elften_september_ist_hier_reproduziert():
    """Mit dem Schalter AUS entsteht genau die gemeldete flache Karte.

    Die Zahlen stehen in der Probe, weil sie der Grund für den ganzen Umbau sind: Mittel
    über dem Innenraum 0.9974, Anteil aller Punkte über 0.99 gleich 0.989. Die Meldung
    drüben nannte 0.9869 und 98.7 % — dieselbe Grössenordnung, mit einem anderen
    Normierungsweg erreicht.
    """
    karte = szene_elfter_september()
    grau, norm = normalisiere_tiefe(karte)
    kern = grau[:2000]

    assert (norm["min_m"], norm["max_m"]) == (1.75, 1600.0)
    assert sum(kern) / len(kern) == pytest.approx(0.9974, abs=5e-4)
    assert sum(1 for wert in grau if wert > 0.99) / len(grau) == pytest.approx(0.989, abs=5e-4)


def test_mit_dem_schalter_bekommt_der_innenraum_den_ganzen_wertebereich():
    """Dieselbe Karte, Schalter AN — und das ist der Gegenbeweis zur Probe darüber.

    Der Innenraum spreizt sich von 0 bis 1 auf; sein Mittel liegt bei 0.5 statt bei
    0.9974, und über 0.99 liegt nur noch das vorderste Prozent. Die 23 Punkte der
    Fernsichtebene sind nicht verschwunden — sie sind geklemmt.
    """
    karte = szene_elfter_september()
    grau_aus, norm_aus = normalisiere_tiefe(karte)
    grau_an, norm_an = normalisiere_tiefe(karte, ferne_trennen=True)
    kern_an = grau_an[:2000]

    assert norm_an["max_m"] == 10.0 and norm_aus["max_m"] == 1600.0
    assert norm_an["ferne_getrennt"] is True
    assert sum(kern_an) / len(kern_an) == pytest.approx(0.5, abs=1e-3)
    assert sum(1 for wert in grau_an if wert > 0.99) / len(grau_an) < 0.02
    assert norm_an["n_geklemmt"] == 23
    assert norm_an["n_geometriepixel"] == 2023, "geklemmt heisst nicht weggeworfen"


def test_die_messung_laeuft_auch_wenn_der_schalter_aus_ist():
    """In JEDER geschriebenen Karte muss stehen, wie sie ausgesehen hätte.

    Ohne diese Zahl kann niemand entscheiden, ob der Schalter umgelegt werden soll — und
    wer zuerst umlegt, verliert die Messung, mit der er es hätte begründen können.
    """
    _grau, norm = normalisiere_tiefe(szene_elfter_september())

    assert norm["ferne_getrennt"] is False, "gerechnet wurde OHNE"
    assert norm["max_m_luecke"] == 10.0, "gemessen wurde TROTZDEM"
    assert norm["luecke"]["verhaeltnis"] == pytest.approx(160.0)
    assert norm["luecke"]["anteil_geklemmt"] == pytest.approx(23 / 2023)
    assert norm["luecke"]["n_gemessen"] == 2023


def test_die_warnung_nennt_beide_zahlen_und_sagt_dass_nicht_umgeschaltet_wurde():
    """Ein Satz, der nur „Achtung" sagt, zwingt zu einem zweiten Lauf.

    Darum stehen beide Zahlen darin — die benutzte Obergrenze und die gemessene — und
    dazu, dass NICHT umgeschaltet wurde. Ausgegeben wird er über ``warnungen`` und nicht
    über ``warnings``: Das Modul bleibt leise, der Bericht nicht.
    """
    _grau, norm = normalisiere_tiefe(szene_elfter_september())

    assert len(norm["warnungen"]) == 1
    satz = norm["warnungen"][0]
    assert "1600" in satz and "10 m" in satz
    assert "NICHT umgeschaltet" in satz
    assert "193.7" in satz, "der Faktor, um den der Kern gewänne"
    assert "gesetzt und nicht kalibriert" in satz


def test_bei_kleinem_gewinn_bleibt_die_warnung_aus():
    """Ein Wächter, der bei jeder Lücke meldet, meldet nichts.

    Kern 1..10 m, ein Fernklumpen bei 30..31 m: Die Lücke ist echt (Faktor 3), aber der
    Kern bekäme nur den 3.33-fachen Wertebereich — über der rechnerischen Untergrenze von
    3 und weit unter der gesetzten Schwelle von 10. Gemessen und gemeldet wird die Lücke
    trotzdem; nur der Satz bleibt weg.
    """
    kern = [1.0 + 9.0 * i / 199 for i in range(200)]
    _grau, norm = normalisiere_tiefe(kern + [30.0, 30.5, 31.0])

    assert norm["max_m_luecke"] == 10.0, "die Lücke ist gemessen"
    assert norm["warnungen"] == [], "aber sie ist keinen Satz wert"
    faktor = (norm["max_m"] - norm["min_m"]) / (norm["max_m_luecke"] - norm["min_m"])
    assert faktor == pytest.approx(10.0 / 3.0)
    assert faktor < bildschreiben.LUECKE_WARNT_AB_FAKTOR


def test_ohne_luecke_aendert_der_schalter_nichts():
    """NICHT GEMESSEN darf nie zu einer erfundenen Grenze werden.

    Eine gleichmässige Verteilung hat kein Loch, an dem sich trennen liesse — der grösste
    Nachbarsprung liegt bei Faktor 1.02. Wer hier trotzdem klemmt, wählt eine Grenze, die
    im Bild nicht steht. Genau das war der Perzentil-Fehler vom 11.09.2026.
    """
    karte = [2.0 + 28.0 * i / 499 for i in range(500)]
    grau_aus, norm_aus = normalisiere_tiefe(karte)
    grau_an, norm_an = normalisiere_tiefe(karte, ferne_trennen=True)

    assert norm_an["max_m_luecke"] is None, "NICHT GEMESSEN, nicht 0 und nicht „keine Ferne“"
    assert grau_an == grau_aus
    assert norm_an["max_m"] == norm_aus["max_m"] == pytest.approx(30.0)
    assert norm_an["ferne_getrennt"] is False
    assert norm_an["n_geklemmt"] == 0
    # Wirkungslos UND stumm wäre der schlimmere Fall: Der Aufruf sähe aus, als hätte er
    # gewirkt.
    assert any("KEINE taugliche Lücke" in satz for satz in norm_an["warnungen"])


def test_eine_szene_ganz_ohne_ferne_meldet_nichts_auffaelliges():
    """Ein Bauwerk von 5 bis 15 m vor leerem Himmel — der Normalfall.

    Der Himmel steht bei 1e10 und ist damit Hintergrund, keine Tiefe; er zieht die Skala
    nicht und kann auch keine Lücke vortäuschen. Was hier zu sehen sein muss, ist:
    **keine Warnung.** Ein Wächter, der auch über unauffällige Karten spricht, wird
    weggehört.
    """
    karte = [5.0 + 10.0 * i / 99 for i in range(100)] + [1e10] * 20
    _grau, norm = normalisiere_tiefe(karte)

    assert norm["warnungen"] == []
    assert norm["max_m_luecke"] is None
    assert (norm["min_m"], norm["max_m"]) == (5.0, 15.0)
    assert norm["luecke"]["n_ausgelassen"] == 20, "der Himmel ist ausgelassen, nicht gemessen"


def test_eine_luecke_auf_dem_naechsten_punkt_schaltet_nicht_um():
    """Der entartete Fall: Die Trennung läge auf dem kleinsten Wert.

    Sechs Punkte bei 1 m, einer bei 100 m — die grösste Lücke sitzt auf 1 m, also auf dem
    nächsten Punkt. Umgeschaltet ergäbe das einen Kern ohne Breite: Jede Geometrie bekäme
    denselben Grauwert, das PNG wäre eine Maske und keine Tiefenkarte. Dieselbe Regel wie
    bei „keine Lücke gefunden" — lieber die alte Skala als eine Grenze, die nichts trennt.
    """
    _grau, norm = normalisiere_tiefe([1.0] * 6 + [100.0], ferne_trennen=True)

    assert norm["max_m_luecke"] == 1.0, "gemessen ist sie"
    assert norm["ferne_getrennt"] is False, "benutzt wird sie nicht"
    assert norm["max_m"] == 100.0
    assert any("keine Breite" in satz for satz in norm["warnungen"])


def test_geklemmt_wird_dunkel_und_nicht_hell():
    """**Abweichung vom Wortlaut des Auftrags, und sie ist absichtlich.**

    Der Auftrag sagt, alles über der Obergrenze werde „auf den hellsten Wert geklemmt".
    Genommen wird der DUNKELSTE. Grund: Die Konvention dieses Moduls ist *nah = hell*, und
    die Fernsichtebene ist das Fernste im Bild. Auf 1.0 geklemmt bekäme sie den Grauwert
    des NÄCHSTEN Punktes — die Tiefenordnung wäre für diese Punkte umgedreht, und die
    Rangkorrelation der Geometrie-QA meldete auf korrekter Geometrie einen negativen Wert.
    Das ist derselbe Fehler, gegen den ``test_der_naechste_punkt_wird_hell_der_fernste_dunkel``
    steht.

    Was der Auftrag mit „nicht zu Hintergrund gemacht" meint, bleibt erfüllt: Die Punkte
    zählen weiter als Geometrie (``n_geometriepixel``), sie verlieren nur ihre Auflösung.
    """
    grau, norm = normalisiere_tiefe([2.0, 4.0, 6.0] + [500.0], ferne_trennen=True)

    assert norm["ferne_getrennt"] is True and norm["max_m"] == 6.0
    assert grau[0] == 1.0, "der nächste Punkt bleibt der hellste"
    assert grau[3] == 0.0, "die Ferne ist das Dunkelste — nicht das Hellste"
    assert grau[3] < grau[2] or grau[3] == grau[2]
    assert grau == sorted(grau, reverse=True), "die Tiefenordnung bleibt monoton"


def test_die_rueckrechnung_aus_einer_geklemmten_karte_verraet_das_klemmen(tmp_path):
    """**Die gefährlichste Stelle dieser Aufgabe, und hier steht ihre Lösung.**

    Wer aus dem PNG Meter rechnet, bekommt für einen geklemmten Punkt genau ``max_m``
    zurück — und das sieht aus wie ein Messwert am Rand der Szene. Ist es nicht: Es ist
    eine UNTERGRENZE. Die Formel in ``rueckrechnung`` bleibt wörtlich gültig; was
    danebenstehen muss, sind vier Angaben:

    * ``geklemmt_ab_m`` — ab welcher Entfernung abgeschnitten wurde (``None`` = gar nicht),
    * ``n_geklemmt`` — wie viele Punkte es trifft,
    * ``max_m_gemessen`` — wie weit sie tatsächlich reichen; die Zahl geht NICHT verloren,
    * ``rueckrechnung_vorbehalt`` — derselbe Sachverhalt im Klartext, weil ein fremder
      Auswerter ``rueckrechnung`` liest und nicht unseren Quelltext.
    """
    tiefen = [2.0, 3.0, 4.0, 5.0, 900.0, 1000.0]
    grau, norm = normalisiere_tiefe(tiefen, ferne_trennen=True)
    pfad = schreibe_graustufen_png(tmp_path / "geklemmt.png", grau, 6, 1)

    assert (norm["min_m"], norm["max_m"]) == (2.0, 5.0)
    assert norm["geklemmt_ab_m"] == 5.0
    assert norm["n_geklemmt"] == 2
    assert norm["max_m_gemessen"] == 1000.0, "die echte Entfernung bleibt im Bericht stehen"
    assert "UNTERGRENZE" in norm["rueckrechnung_vorbehalt"]
    assert "1000" in norm["rueckrechnung_vorbehalt"]
    assert norm["rueckrechnung"] == RUECKRECHNUNG, "die Formel selbst ändert sich nicht"

    # Die Formel wörtlich angewandt — wie es ein fremdes Werkzeug täte.
    gelesen, _, _ = bildlesen.lies_png_graustufen(pfad)
    von_hand = [norm["max_m"] - wert * (norm["max_m"] - norm["min_m"]) for wert in gelesen]

    assert von_hand[:4] == pytest.approx(tiefen[:4], abs=3.0 / 65535)
    assert von_hand[4] == pytest.approx(5.0, abs=3.0 / 65535), "900 m kommen als 5 m zurück"
    assert von_hand[5] == pytest.approx(5.0, abs=3.0 / 65535), "1000 m ebenso"
    # Und genau deshalb steht der Vorbehalt da: DREI Punkte lesen sich als 5 m — einer
    # ist wirklich 5 m weit weg, zwei sind geklemmt. Im PNG sind sie nicht zu trennen;
    # nur `n_geklemmt` sagt, dass zwei davon keine Messwerte sind.
    an_der_grenze = sum(1 for wert in von_hand if abs(wert - norm["max_m"]) < 3.0 / 65535)
    assert an_der_grenze == 3
    assert norm["n_geklemmt"] == 2


def test_ohne_klemmen_steht_kein_vorbehalt_da_aber_die_zahl_steht_da():
    """Ein Vorbehalt, der immer dasteht, wird überlesen — also steht er nur, wenn er gilt.

    ``max_m_gemessen`` dagegen steht immer, auch ungeklemmt. Dann ist es dasselbe wie
    ``max_m``, und genau das darf man sehen: Ein Feld, das mal da ist und mal nicht,
    zwingt jeden Auswerter zu einer Fallunterscheidung, die er vergessen kann.
    """
    _grau, norm = normalisiere_tiefe([2.0, 4.0, 6.0])

    assert norm["rueckrechnung_vorbehalt"] is None
    assert norm["geklemmt_ab_m"] is None
    assert norm["n_geklemmt"] == 0
    assert norm["max_m_gemessen"] == norm["max_m"] == 6.0


def test_die_messung_wirft_die_normierung_nie_um(monkeypatch):
    """Eine Zugabe, die den Auftrag scheitern lässt, ist keine.

    Die Normierung ist der Auftrag, die Lücken-Messung ist die Zugabe. ``ferne_abtrennen``
    prüft seine Eingabe strenger als diese Funktion (Wahrheitswerte, Zahlen in Textform,
    eine unbrauchbare Schranke) — wo es abbricht, muss hinterher **NICHT GEMESSEN** stehen
    und ein Satz, der sagt warum, und nicht ein Abbruch des ganzen Schreibwegs.

    Der Abbruch wird hier eingesetzt statt herbeigeführt: Welche Eingabe die Messung heute
    umwirft, ist ihre Sache und darf sich ändern; dass ein Abbruch aufgefangen wird, ist
    unsere.
    """
    from aiimaging import geometrie_qa

    def platzt(*args, **kwargs):
        raise geometrie_qa.QaError("nachgestellt: die Messung bricht ab")

    monkeypatch.setattr(geometrie_qa, "ferne_abtrennen", platzt)

    grau, norm = normalisiere_tiefe([10.0, 20.0, 30.0], ferne_trennen=True)

    assert grau == [1.0, 0.5, 0.0], "die Normierung ist gelaufen"
    assert norm["max_m"] == 30.0 and norm["ferne_getrennt"] is False
    assert norm["max_m_luecke"] is None and norm["luecke"] is None
    assert any("NICHT GEMESSEN" in satz for satz in norm["warnungen"])
    assert any("QaError" in satz for satz in norm["warnungen"]), "und woran es lag"


def test_die_hintergrundschranke_gilt_auch_fuer_die_luecken_messung():
    """Gemessen werden muss dieselbe Karte, die auch normiert wird.

    ``hintergrund_ab_m`` entscheidet, was überhaupt als Tiefe zählt — und damit über
    ``min_m``, ``max_m`` **und** über die Werte, in denen die Lücke gesucht wird. Reichte
    das Argument nicht bis in die Messung durch, liefe die Messung auf einer anderen Karte
    als die Normierung: Die Obergrenze käme dann aus Punkten, die hier gar keine Geometrie
    mehr sind, und stünde als Zahl neben einem ``max_m``, zu dem sie nicht gehört.

    Hier: zehn Punkte 1..10 m und einer bei 500 m, Schranke 50 m. Der 500er ist damit
    Hintergrund, nicht Ferne. Die verbleibenden zehn Punkte haben kein Loch — also
    **NICHT GEMESSEN**, und mit gesetztem Schalter ein Satz dazu. Mit der Vorgabeschranke
    (1e7) gemessen wäre der 500er dabei, und die Messung meldete eine Obergrenze von 10 m,
    die hier niemand gemeint hat.
    """
    karte = [1.0 + i for i in range(10)] + [500.0]
    _grau, norm = normalisiere_tiefe(karte, hintergrund_ab_m=50.0, ferne_trennen=True)

    assert norm["luecke"]["n_gemessen"] == 10, "gemessen wird, was hier Geometrie ist"
    assert norm["luecke"]["n_ausgelassen"] == 1, "der 500er ist Hintergrund, nicht Ferne"
    assert norm["max_m_luecke"] is None, "zehn Punkte ohne Loch — NICHT GEMESSEN"
    assert norm["max_m"] == 10.0 and norm["ferne_getrennt"] is False
    assert any("KEINE taugliche Lücke" in satz for satz in norm["warnungen"])


def test_eine_obergrenze_ueber_dem_groessten_mass_wird_nicht_stumm_verworfen(monkeypatch):
    """**Der Fall, der bis zur Prüfung vom 16.09.2026 stumm durchfiel.**

    ``ferne_abtrennen`` sagt zu, dass die Obergrenze die UNTERE Kante einer Lücke ist —
    über ihr liegt also noch mindestens ein Wert, und damit ist sie kleiner als das grösste
    Mass. Hält diese Zusage einmal nicht, darf hier nicht umgeschaltet werden: Eine Skala
    aus einer Zahl, die so nicht gemeint sein kann, ist schlimmer als die alte Skala.

    Bis zur Prüfung geschah dabei aber **gar nichts** — kein Umschalten und kein Satz. Im
    Bericht stand ``max_m_luecke`` als Zahl, ``ferne_getrennt`` auf ``False``, und in
    ``warnungen`` nichts. Wer den Schalter gesetzt hatte, sah einen wirkungslosen Aufruf,
    der wie ein wirksamer aussieht — genau der Fehlschlag, gegen den der Satz im Zweig
    „keine Lücke gemessen" geschrieben ist.

    Der Vertragsbruch wird eingesetzt und nicht herbeigeführt: Mit dem heutigen
    ``ferne_abtrennen`` ist er nicht erreichbar, und eine Probe, die auf die Erreichbarkeit
    eines fremden Fehlers wartet, prüft nichts.
    """
    from aiimaging import geometrie_qa

    def zu_hoch(karte, **kwargs):
        return {"obergrenze": 1000.0, "stufen_gefunden": 1, "kanten": (1000.0,),
                "anteil_geklemmt": 0.0, "anteil_wertebereich": None, "verhaeltnis": 5.0,
                "n_gemessen": 4, "n_ausgelassen": 0, "warnungen": []}

    monkeypatch.setattr(geometrie_qa, "ferne_abtrennen", zu_hoch)

    grau, norm = normalisiere_tiefe([2.0, 3.0, 4.0, 1000.0], ferne_trennen=True)

    assert norm["ferne_getrennt"] is False, "NICHT umgeschaltet"
    assert norm["max_m"] == 1000.0 and norm["n_geklemmt"] == 0
    assert grau[0] == 1.0 and grau[3] == 0.0, "gerechnet wurde mit der alten Skala"
    assert norm["max_m_luecke"] == 1000.0, "die gemessene Zahl bleibt im Bericht stehen"
    satz = [s for s in norm["warnungen"] if "NICHT unter dem grössten" in s]
    assert len(satz) == 1, "und sie bleibt nicht unkommentiert stehen"
    assert "1000" in satz[0] and "NICHT umgeschaltet" in satz[0]


def test_der_bericht_ueberlebt_den_weg_durch_json():
    """Der Bericht landet über ``tiefe_exr_zu_png`` im Report und damit in einer Datei.

    ``ferne_abtrennen`` gibt ``kanten`` als Tupel zurück; aus JSON kommt eine Liste
    zurück. Wer die Datei gegen das Speicherabbild hält, sähe sonst einen Unterschied, den
    es nicht gibt — also wird hier schon eine Liste hinterlegt.
    """
    import json

    _grau, norm = normalisiere_tiefe(szene_elfter_september())

    assert norm["luecke"]["kanten"] == [10.0]
    assert json.loads(json.dumps(norm)) == norm


def test_der_schalter_reicht_durch_die_ganze_funktion_durch(tmp_path):
    """Ein Schalter, den die Kette nicht erreicht, ist ein Schalter ohne Draht.

    ``tiefe_exr_zu_png`` reicht ihn weiter — und auch dort ist die Vorgabe AUS.
    """
    import inspect

    tiefen = [2.0, 3.0, 4.0, 5.0, 900.0, 1000.0]
    leser = leser_mit(tiefen, 6, 1)

    vorgabe = inspect.signature(tiefe_exr_zu_png).parameters["ferne_trennen"].default
    assert vorgabe is False

    aus = tiefe_exr_zu_png(tmp_path / "x.exr", tmp_path / "aus.png", _leser=leser)
    an = tiefe_exr_zu_png(tmp_path / "x.exr", tmp_path / "an.png", _leser=leser,
                          ferne_trennen=True)

    assert aus["max_m"] == 1000.0 and aus["ferne_getrennt"] is False
    assert an["max_m"] == 5.0 and an["ferne_getrennt"] is True
    assert aus["max_m_luecke"] == an["max_m_luecke"] == 5.0, "gemessen wird in beiden Fällen"

# ======================================================================================
# 7 · Die ganze Kette: Meter → PNG → Meter
# ======================================================================================

#: Eine Szene mit 20 m Tiefe, ohne Hintergrund — damit die Genauigkeit gemessen werden
#: kann, ohne dass die Silhouettenfrage sie überlagert (die steht in Abschnitt 8).
def szene_ohne_himmel(breite: int = 12, hoehe: int = 8) -> list[float]:
    """Ein synthetisches Tiefenfeld zwischen 10 und 30 m, streng aus dem Testcode erzeugt."""
    return [10.0 + ((y * 7 + x * 5) % 41) * 0.5 for y in range(hoehe) for x in range(breite)]


@pytest.mark.parametrize("bittiefe", [8, 16])
def test_die_ganze_kette_gibt_die_meter_bis_auf_eine_halbe_stufe_zurueck(tmp_path, bittiefe):
    """Der Rundlauf, um den es dem Modul geht: Meter hinein, Meter heraus.

    Der Fehler muss in der Grössenordnung der Quantisierung liegen — mehr hiesse, dass
    irgendwo zwischen Normalisierung, Runden und Rückrechnung eine Umformung nicht
    invers ist. Weniger ginge gar nicht, und wer weniger meldet, hat sich verrechnet
    (so steht es auch bei ``bildlesen.png_befund``).

    Gedeutet wird mit ``GRAU_NULL_GEOMETRIE``: In dieser Szene gibt es keinen Himmel, und
    der fernste Punkt ist Geometrie. Die Warnung kommt trotzdem — sie hängt am Grauwert 0,
    nicht daran, ob die Deutung im Einzelfall verlustfrei ist.
    """
    breite, hoehe = 12, 8
    tiefen = szene_ohne_himmel(breite, hoehe)
    grau, norm = normalisiere_tiefe(tiefen)
    pfad = schreibe_graustufen_png(tmp_path / f"kette{bittiefe}.png", grau, breite, hoehe,
                                   bittiefe=bittiefe)

    with pytest.warns(bildlesen.SilhouettenVerlust):
        zurueck = bildlesen.tiefen_aus_png(pfad, norm,
                                           grau_null=bildlesen.GRAU_NULL_GEOMETRIE)

    schritt = (norm["max_m"] - norm["min_m"]) / ((1 << bittiefe) - 1)
    abweichung = max(abs(a - e) for a, e in zip(zurueck, tiefen))
    assert abweichung <= schritt / 2 + 1e-9, "grösser als Quantisierung — da rechnet etwas falsch"
    assert abweichung > 0.0, "ohne jede Abweichung wäre die Quantisierung nicht wirksam"


def test_die_extremwerte_der_szene_kommen_exakt_zurueck(tmp_path):
    """``min_m`` und ``max_m`` liegen genau auf Rasterpunkten (Grauwert 1 und 0).

    Sie sind die beiden Zahlen, an denen die ganze Rückrechnung hängt; ein Rundungsfehler
    ausgerechnet hier verschöbe die gesamte Skala statt eines einzelnen Punktes.
    """
    tiefen = [10.0, 13.3, 17.7, 30.0]
    grau, norm = normalisiere_tiefe(tiefen)
    pfad = schreibe_graustufen_png(tmp_path / "extrem.png", grau, 4, 1)

    with pytest.warns(bildlesen.SilhouettenVerlust):
        zurueck = bildlesen.tiefen_aus_png(pfad, norm,
                                           grau_null=bildlesen.GRAU_NULL_GEOMETRIE)

    assert zurueck[0] == pytest.approx(10.0, abs=1e-9), "der nächste Punkt"
    assert zurueck[3] == pytest.approx(30.0, abs=1e-9), "der fernste Punkt"


def test_acht_bit_zerlegt_eine_dreissig_meter_szene_in_zwoelf_zentimeter_stufen(tmp_path):
    """Die Begründung für die Vorgabe 16 Bit — nachgerechnet statt geglaubt.

    Der Docstring nennt 12-cm-Stufen und „sichtbare Terrassen auf jeder schrägen Fläche".
    Das ist keine Redewendung: Bei 30 m Szenentiefe sind es 30/255 m je Stufe, und ein
    Fenstersturz von 8 cm verschwindet darin vollständig.
    """
    tiefen = szene_ohne_himmel()
    grau, norm = normalisiere_tiefe(tiefen)
    acht = schreibe_graustufen_png(tmp_path / "acht.png", grau, 12, 8, bittiefe=8)
    sechzehn = schreibe_graustufen_png(tmp_path / "sechzehn.png", grau, 12, 8, bittiefe=16)

    befund8 = bildlesen.png_befund(acht, norm)
    befund16 = bildlesen.png_befund(sechzehn, norm)

    assert befund8["bittiefe"] == 8 and befund16["bittiefe"] == 16
    assert befund8["quantisierungsschritt_m"] == pytest.approx(20.0 / 255)
    assert befund8["quantisierungsschritt_m"] > 0.07, "gröber als ein Fenstersturz"
    assert befund16["quantisierungsschritt_m"] < 0.001
    assert befund8["quantisierungsschritt_m"] > 250 * befund16["quantisierungsschritt_m"]


def test_die_rueckrechnungsformel_gilt_wortwoertlich(tmp_path):
    """``RUECKRECHNUNG`` ist kein Kommentar, sondern eine Zusage an fremde Auswerter.

    Wer sie in einem anderen Werkzeug nachbaut, muss dieselben Meter erhalten wie
    ``bildlesen.tiefen_aus_png``. Deshalb wird sie hier von Hand nachgerechnet.
    """
    tiefen = [12.0, 18.0, 24.0, 30.0]
    grau, norm = normalisiere_tiefe(tiefen)
    pfad = schreibe_graustufen_png(tmp_path / "formel.png", grau, 4, 1)

    gelesen, _, _ = bildlesen.lies_png_graustufen(pfad)
    von_hand = [norm["max_m"] - wert * (norm["max_m"] - norm["min_m"]) for wert in gelesen]

    assert RUECKRECHNUNG == "meter = max_m - grau * (max_m - min_m), grau in 0..1"
    assert von_hand == pytest.approx(tiefen, abs=(30.0 - 12.0) / 65535)


def test_die_bildpunktreihenfolge_ueberlebt_die_ganze_kette(tmp_path):
    """Ein Versatz wäre der Fehler, den niemand sieht und alle bezahlen.

    Deshalb ein Bild, in dem jeder Bildpunkt eine andere Tiefe hat: Ein vertauschter,
    gespiegelter oder um eine Zeile verschobener Durchlauf fiele hier auf, während er in
    einem glatten Verlauf unsichtbar bliebe.
    """
    breite, hoehe = 5, 4
    tiefen = [10.0 + i for i in range(breite * hoehe)]
    grau, norm = normalisiere_tiefe(tiefen)
    pfad = schreibe_graustufen_png(tmp_path / "reihenfolge.png", grau, breite, hoehe)

    with pytest.warns(bildlesen.SilhouettenVerlust):
        zurueck = bildlesen.tiefen_aus_png(pfad, norm,
                                           grau_null=bildlesen.GRAU_NULL_GEOMETRIE)

    assert zurueck == pytest.approx(tiefen, abs=1e-3)


# ======================================================================================
# 8 · Der Verlust, den das PNG erzwingt — Eigenschaft, nicht Fehler
# ======================================================================================

def test_der_fernste_punkt_und_der_himmel_werden_im_png_ununterscheidbar(tmp_path):
    """Das ist die dokumentierte Grenze des Formats, und sie gehört festgehalten.

    ``normalisiere_tiefe`` gibt dem fernsten Geometriepunkt Grauwert 0 — denselben Wert,
    den der Hintergrund trägt. Im PNG ist danach keine Unterscheidung mehr möglich; das
    steht so in ``KONVENTION`` und wird von ``bildlesen`` als ``SilhouettenVerlust``
    gewarnt. Wer die Silhouette exakt braucht, nimmt die EXR.

    Als Fehler des Schreibers zu behandeln wäre falsch: Die Alternative wäre, einen
    Grauwert für „Hintergrund" zu reservieren und die Skala dafür zu verbiegen — dann
    trüge jedes Bild eine stille Sonderregel, die kein fremdes Werkzeug kennt.
    """
    tiefen = [12.0, 20.0, 1e10, 16.0]          # nah, fernste Geometrie, Himmel, Mitte
    grau, norm = normalisiere_tiefe(tiefen)
    assert grau[1] == grau[2] == 0.0, "fernste Geometrie und Himmel fallen schon hier zusammen"

    pfad = schreibe_graustufen_png(tmp_path / "verlust.png", grau, 4, 1)
    gelesen, _, _ = bildlesen.lies_png_graustufen(pfad)

    assert gelesen[1] == gelesen[2] == 0.0
    assert "Silhouette" in KONVENTION and "EXR" in KONVENTION

    with pytest.warns(bildlesen.SilhouettenVerlust, match="2 von 4"):
        zurueck = bildlesen.tiefen_aus_png(pfad, norm)
    assert zurueck[1] == zurueck[2] == math.inf, "der fernste Bau zählt nicht mehr zur Silhouette"


def test_der_befund_beziffert_den_verlust_fuer_geschriebene_dateien(tmp_path):
    """Dieselbe Auskunft maschinenlesbar — hier gegen ein Bild, das dieses Modul erzeugt hat.

    ``n_grau_eins`` muss genau 1 sein: Es gibt in jeder Szene genau einen nächsten Punkt,
    und wäre es mehr, hätte die Normalisierung die Skala nicht ausgeschöpft.
    """
    tiefen = [8.0, 25.0, 1e10, 1e10, 16.0, math.inf]
    grau, norm = normalisiere_tiefe(tiefen)
    pfad = schreibe_graustufen_png(tmp_path / "befund.png", grau, 6, 1)

    befund = bildlesen.png_befund(pfad, norm)

    assert befund["n_pixel"] == 6
    assert befund["n_grau_null"] == 4, "drei Hintergrundpunkte plus der fernste Bau"
    assert befund["n_grau_eins"] == 1
    assert befund["anteil_grau_null"] == pytest.approx(4 / 6)
    assert norm["n_geometriepixel"] == 3


# ======================================================================================
# 9 · tiefe_exr_zu_png — der ganze Weg, über die Testnaht statt über eine EXR-Datei
# ======================================================================================

def leser_mit(werte, breite, hoehe, protokoll=None):
    """Ein Doppelgänger von ``bildlesen.lies_exr_tiefe``: Pfad hinein, Zahlen heraus.

    Genau dafür ist der Parameter ``_leser`` da. Eine echte EXR zu schreiben prüfte hier
    nichts zusätzlich — der EXR-Leser hat seine eigenen Tests — und machte den Test von
    einem zweiten Dateiformat abhängig.
    """
    def leser(pfad):
        if protokoll is not None:
            protokoll.append(pfad)
        return list(werte), breite, hoehe
    return leser


def test_der_ganze_weg_von_der_exr_zum_png_laeuft_ohne_blender(tmp_path):
    """Die Verschiebung der Naht, um die es dem Modul geht.

    Bis zum 18.08.2026 stand dieser Schritt im Blender-Runner — und brach auf Blender 5.2,
    weil dessen Multilayer-Leseweg die eigene Datei als 0×0 lud. Hier ist er reine
    Arithmetik: kein Prozessstart, keine GPU, keine GPL-Komponente.
    """
    tiefen = [10.0, 15.0, 20.0, 1e10, 12.5, 17.5]
    ziel = tmp_path / "tiefe_norm.png"
    protokoll: list = []

    norm = tiefe_exr_zu_png(tmp_path / "tiefe_0001.exr", ziel,
                            _leser=leser_mit(tiefen, 3, 2, protokoll))

    assert protokoll == [tmp_path / "tiefe_0001.exr"], "der Leser bekommt einen Pfad"
    assert (norm["breite"], norm["hoehe"], norm["bittiefe"]) == (3, 2, 16)
    assert (norm["min_m"], norm["max_m"]) == (10.0, 20.0)
    assert norm["n_geometriepixel"] == 5
    assert norm["quelle"] == "produkt"

    gelesen, breite, hoehe = bildlesen.lies_png_graustufen(ziel)
    assert (breite, hoehe) == (3, 2)
    assert gelesen[0] == 1.0 and gelesen[2] == 0.0
    assert gelesen[3] == 0.0, "der Himmel bleibt schwarz"


def test_die_bittiefe_wird_durchgereicht_und_gemeldet(tmp_path):
    """Wer 8 Bit verlangt, bekommt 8 Bit — und findet es im Ergebnis wieder.

    Ohne das Feld liesse sich der Quantisierungsschritt später nicht mehr berechnen, ohne
    die Datei erneut zu öffnen.
    """
    ziel = tmp_path / "acht.png"

    norm = tiefe_exr_zu_png("egal.exr", ziel, bittiefe=8,
                            _leser=leser_mit([1.0, 2.0, 3.0, 4.0], 2, 2))

    assert norm["bittiefe"] == 8
    _werte, _b, _h, bittiefe = bildlesen._png_lesen(ziel)
    assert bittiefe == 8


def test_die_hintergrundschranke_reicht_bis_in_die_datei_durch(tmp_path):
    """Der Parameter darf nicht unterwegs verloren gehen — er bestimmt min_m und max_m mit."""
    ziel = tmp_path / "schranke.png"

    norm = tiefe_exr_zu_png("egal.exr", ziel, hintergrund_ab_m=100.0,
                            _leser=leser_mit([5.0, 500.0, 25.0, 15.0], 4, 1))

    assert norm["hintergrund_ab_m"] == 100.0
    assert (norm["min_m"], norm["max_m"]) == (5.0, 25.0)
    assert norm["n_geometriepixel"] == 3


def test_eine_leere_szene_bricht_ab_statt_ein_schwarzes_png_zu_hinterlassen(tmp_path):
    """Der Abbruch aus ``normalisiere_tiefe`` muss durch die ganze Funktion durchschlagen.

    Ein geschriebenes schwarzes Bild wäre hier besonders teuer: Es liefe durch die
    restliche Kette bis in den Bildgenerator und fiele erst am Ergebnis auf.
    """
    ziel = tmp_path / "leer.png"

    with pytest.raises(SchreibError, match="Geometriepixel"):
        tiefe_exr_zu_png("egal.exr", ziel, _leser=leser_mit([1e10] * 4, 2, 2))

    assert not ziel.exists()


def test_der_rundlauf_ueber_die_naht_gibt_die_meter_zurueck(tmp_path):
    """Dieselbe Genauigkeitszusage wie in Abschnitt 7, aber über die Funktion, die die
    Kette tatsächlich aufruft (``seams.glb_zu_multipass`` nach dem Blender-Lauf)."""
    tiefen = szene_ohne_himmel(8, 6)
    ziel = tmp_path / "kette.png"

    norm = tiefe_exr_zu_png("egal.exr", ziel, _leser=leser_mit(tiefen, 8, 6))

    with pytest.warns(bildlesen.SilhouettenVerlust):
        zurueck = bildlesen.tiefen_aus_png(ziel, norm,
                                           grau_null=bildlesen.GRAU_NULL_GEOMETRIE)

    schritt = (norm["max_m"] - norm["min_m"]) / 65535
    assert max(abs(a - e) for a, e in zip(zurueck, tiefen)) <= schritt / 2 + 1e-9


def test_ohne_eingesetzten_leser_ist_der_exr_leser_des_projekts_zustaendig():
    """Die Naht ist eine Testnaht, keine Konfiguration.

    Die Vorgabe muss ``bildlesen.lies_exr_tiefe`` sein — erst der stdlib-Weg und nur
    notfalls der Blender-Rückfall. Geprüft an der Signatur, damit dafür keine EXR-Datei
    und schon gar kein Blender nötig ist.
    """
    import inspect

    vorgabe = inspect.signature(tiefe_exr_zu_png).parameters["_leser"].default

    assert vorgabe is None, "die Vorgabe wird erst im Rumpf aufgelöst"
    quelle = inspect.getsource(tiefe_exr_zu_png)
    assert "bildlesen.lies_exr_tiefe" in quelle


# ======================================================================================
# Kontrollbilder — ein Score sagt erst etwas, wenn danebensteht, was NICHTS erreicht
# ======================================================================================

def test_das_rauschen_ist_reproduzierbar():
    """**Eine Nullprobe, die bei jedem Aufruf anders ausfällt, ist keine.**

    Der Anker wäre dann selbst eine Zufallsgrösse, und ein Score liesse sich nicht zweimal
    gleich einordnen.
    """
    a = bildschreiben.kontrollwerte("rauschen", 16, 8)
    b = bildschreiben.kontrollwerte("rauschen", 16, 8)
    assert a == b
    assert bildschreiben.kontrollwerte("rauschen", 16, 8, seed=1) != a


def test_das_rauschen_fuellt_die_ganze_spanne():
    werte = bildschreiben.kontrollwerte("rauschen", 64, 64)
    assert min(werte) < 0.05 and max(werte) > 0.95
    assert 0.45 < sum(werte) / len(werte) < 0.55


def test_die_graue_flaeche_ist_wirklich_leer():
    werte = bildschreiben.kontrollwerte("grau", 8, 4)
    assert set(werte) == {0.5}


def test_der_verlauf_laeuft_QUER_und_nicht_wie_eine_bodenebene():
    """Eine Tiefenrampe läuft von unten nach oben. Der Kontrollverlauf soll gerade NICHT
    so aussehen — sonst prüfte er nicht, ob ein Gradient schon reicht, sondern lieferte
    genau den Gradienten, den der Schätzer ohnehin erfindet."""
    breite, hoehe = 8, 4
    werte = bildschreiben.kontrollwerte("verlauf", breite, hoehe)
    zeilen = [werte[y * breite:(y + 1) * breite] for y in range(hoehe)]
    assert all(z == zeilen[0] for z in zeilen), "alle Zeilen gleich — also kein Verlauf in Y"
    assert zeilen[0] == sorted(zeilen[0]), "in X steigend"
    assert zeilen[0][0] == 0.0 and zeilen[0][-1] == 1.0


def test_ein_kontrollbild_ist_ein_lesbares_png(tmp_path):
    from aiimaging import bildlesen
    for art in bildschreiben.KONTROLLARTEN:
        pfad = bildschreiben.schreibe_kontrollbild(tmp_path / f"{art}.png", art, 12, 6)
        werte, breite, hoehe = bildlesen.lies_png_graustufen(pfad)
        assert (breite, hoehe) == (12, 6) and len(werte) == 72


def test_eine_unbekannte_kontrollart_wird_abgewiesen():
    with pytest.raises(bildschreiben.SchreibError, match="Bekannt:"):
        bildschreiben.kontrollwerte("beauty", 8, 8)


@pytest.mark.parametrize("breite, hoehe", [(0, 8), (8, 0), (-1, 4)])
def test_unbrauchbare_masse_werden_abgewiesen(breite, hoehe):
    with pytest.raises(bildschreiben.SchreibError, match="kein Bild"):
        bildschreiben.kontrollwerte("grau", breite, hoehe)
