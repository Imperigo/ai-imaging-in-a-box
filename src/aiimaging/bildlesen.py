"""BILDLESEN — der Weg von der Bilddatei zu den Zahlen, die die Geometrie-QA erwartet.

Das Loch, das dieses Modul schliesst
------------------------------------
``geometrie_qa.geometrie_score(soll, ist)`` nimmt **Zahlenfolgen** entgegen und liest
bewusst keine Dateien (siehe dort, Abschnitt „Was dieses Modul bewusst *nicht* tut“).
Der Multipass in ``runners/blender_depth_stage.py`` schreibt aber **Dateien**:

* ``tiefe_0001.exr`` — 32-Bit-EXR, echte Meter, die Grundlage der QA.
* ``tiefe_norm.png`` — 16-Bit-Graustufen, normalisiert, Konvention *nah = hell*.

Zwischen beidem gab es keinen Weg. Die Metrik war damit gebaut, aber nicht anwendbar.
Dieses Modul ist genau dieser Weg — und nichts darüber hinaus: Es liest, es rechnet
zurück, es urteilt nicht. Jede Deutung (Hintergrundmarke, Schwelle, Score) bleibt in
``geometrie_qa``.

Die Lizenzfrage — und warum am Ende keine Abhängigkeit dazukommt
----------------------------------------------------------------
„Lizenz vor Technik“ ist stehende Regel (``docs/PLAN.md``). Geprüft wurde vor der
Technikwahl, nicht danach:

**PNG.** Vollständig aus der Standardbibliothek lesbar: ``zlib`` plus die PNG-
Spezifikation (IHDR, IDAT, die fünf Zeilenfilter). Eine Bildbibliothek wäre hier eine
Abhängigkeit ohne Gegenwert. Pillow (MIT-CMU, permissiv) wäre lizenzrechtlich zulässig,
brächte aber einen grossen Binäranteil mit fremden Codecs mit — genau die Sorte
Abhängigkeit, die unter „Binärabhängigkeiten ungeprüft“ in den Wissensschulden steht.
**Entscheidung: reine stdlib.**

**EXR.** Hier lag die eigentliche Entwurfsarbeit. Erwogen und *abgelehnt*:

* ``imageio`` (BSD-2-Clause) — die Bibliothek selbst ist permissiv, ihr EXR-Weg läuft
  aber klassisch über das **FreeImage**-Plugin, und FreeImage steht unter FIPL **oder
  GPL-2.0/GPL-3.0**. Das ist ein **GPL-Fund** und wird hier ausdrücklich als solcher
  gemeldet (Regel 1). Er ist aus Sekundärwissen benannt, nicht gegen die LICENSE-Datei
  geprüft — für eine *Ablehnung* genügt der Verdacht, für eine Aufnahme genügte er nie.
* ``OpenImageIO`` (Apache-2.0) — die Quelle ist permissiv, die ausgelieferten Wheels
  bündeln aber OpenEXR, libtiff, libraw und je nach Bau ffmpeg. Deren Lizenzen (u.a.
  LGPL, teils GPL bei bestimmten Bauten) sind nicht geprüft. Dieselbe Falle wie beim
  ifcopenshell-Wheel, das statisch GPL-lizenziertes CGAL mitbringt.
* ``OpenEXR``-Bindings (BSD-3-Clause) — von den drei die sauberste, aber immer noch ein
  kompiliertes Paket samt gebündelter Fremdbibliotheken. Und, entscheidend: unnötig.

**Der Befund, der die Frage erledigt hat.** Die EXR, die dieses Projekt selbst erzeugt,
ist *scanline*-organisiert, einkanalig, 32-Bit-FLOAT und **ZIP-komprimiert** — ZIP ist
in OpenEXR nichts anderes als ``zlib`` plus zwei triviale Nachbearbeitungsschritte
(Prädiktor, Byte-Entflechtung). Damit ist auch die EXR aus der Standardbibliothek
lesbar. Gegengeprüft am echten Bild: Der Leser unten liefert dieselben Werte wie
Blender, bis auf das letzte Bit.

**Entscheidung: keine neue Abhängigkeit.** Der Hauptweg ist reine stdlib. Was er nicht
kann — PIZ, DWAA/DWAB, B44, PXR24, gekachelte oder mehrteilige Dateien — wird nicht
geraten, sondern abgewiesen; und dafür gibt es den **Rückfall über die schon bestehende
Prozessgrenze zu Blender** (``runners/blender_exr_lesen.py``). Blender ist bereits als
GPL-Komponente im ``NOTICE`` deklariert und hat die Datei ohnehin geschrieben. Der
Rückfall meldet sich als Warnung, er passiert nie stillschweigend.

Warum der stdlib-Weg der Hauptweg ist und nicht bloss eine Abkürzung: Die QA soll
überall laufen, auch dort, wo kein Blender installiert ist (Regel 4). Wäre das Lesen der
Soll-Tiefenkarte an ein GPL-Binary gebunden, wäre die Metrik faktisch doch wieder an
eine schwere Umgebung geknüpft — und der Satz „reine stdlib“ in ``geometrie_qa`` nur noch
die halbe Wahrheit.

Die dokumentierte Falle: das PNG kann die Silhouette nicht
----------------------------------------------------------
Im normalisierten PNG gilt *nah = hell*, und der Hintergrund ist 0. Das **entfernteste
Geometriepixel** liegt aber ebenfalls bei 0 — beide sind schwarz, beide nicht
unterscheidbar. Aus dem PNG allein ist die Silhouette also **nicht** exakt
rekonstruierbar. Der Runner sagt das in seinem Report-Feld ``depth_normalisierung``, und
dieses Modul tut nicht so, als ginge es doch:

* ``tiefen_aus_png`` verlangt eine ausdrückliche Entscheidung, wie Grauwert 0 zu deuten
  ist, und **warnt** (``SilhouettenVerlust``) mit Zahlen, sobald solche Punkte vorkommen.
* ``png_befund`` liefert dieselbe Auskunft maschinenlesbar, für Berichte statt für Logs.
* Wer die Silhouette exakt braucht, nimmt die EXR. Das ist keine Empfehlung, sondern die
  einzige richtige Antwort.

Abhängigkeiten: keine. ``zlib``, ``struct``, ``array``, ``json``, ``subprocess`` — alles
Standardbibliothek. Kein ``bpy``, kein ``ifcopenshell``, keine Bildbibliothek.
"""
from __future__ import annotations

import json
import math
import struct
import subprocess
import sys
import tempfile
import warnings
import zlib
from array import array
from itertools import accumulate, chain
from pathlib import Path

from aiimaging.seams import SeamError, finde_blender

#: Der Runner jenseits der Prozessgrenze. Wird als **Pfad** geführt, nie importiert —
#: er braucht ``bpy`` (Regel 2). Dieselbe Bauart wie ``seams.BLENDER_RUNNER``.
EXR_RUNNER = Path(__file__).resolve().parent / "runners" / "blender_exr_lesen.py"

PNG_SIGNATUR = b"\x89PNG\r\n\x1a\n"

#: Erste vier Bytes einer OpenEXR-Datei (0x01312f76, little-endian gespeichert).
EXR_MAGIC = b"\x76\x2f\x31\x01"

#: Wie Grauwert 0 im normalisierten PNG gedeutet wird. Es gibt keine richtige Antwort —
#: siehe „Die dokumentierte Falle“ im Modul-Docstring. Darum eine Wahl mit Namen statt
#: einer stillen Vorgabe.
GRAU_NULL_HINTERGRUND = "hintergrund"
GRAU_NULL_GEOMETRIE = "geometrie"

#: Woher die Tiefenkarte zu einem Blender-Report genommen wird.
QUELLE_AUTO = "auto"
QUELLE_EXR = "exr"
QUELLE_PNG = "png"


class BildError(ValueError):
    """Die Datei ist nicht das, was sie sein müsste — oder gar nicht lesbar.

    Bewusst ein Fehler und kein Ersatzwert: Ein halb gelesenes Bild ergäbe eine
    Zahlenfolge, die aussieht wie eine Messung und keine ist. Genau davor schützt
    ``geometrie_qa`` an seiner Eingangsseite, und diese Seite hält es genauso.

    Erbt von ``ValueError``, damit bestehendes ``except ValueError`` weiter greift —
    dieselbe Wahl wie bei ``geometrie_qa.QaError``.
    """


class EXRVarianteError(BildError):
    """Die EXR ist in Ordnung, aber in einer Spielart, die der stdlib-Leser nicht kann.

    Eigene Klasse, weil daran eine Entscheidung hängt: Nur *diese* Lage rechtfertigt den
    Rückfall auf den Blender-Subprozess. Eine kaputte oder abgeschnittene Datei tut es
    nicht — für die wäre ein drei Sekunden teurer Prozessstart nur eine langsamere Art,
    denselben Fehler zu melden.

    ``grund`` trägt den Kurzgrund ohne Rahmentext. Er hängt hier als Attribut, damit der
    Rückfall ihn nicht aus der fertigen Fehlermeldung zurückschneiden muss — solches
    Zerschneiden von Text ist genau die Stelle, an der später ein Satz kaputtgeht.
    """

    def __init__(self, meldung: str, grund: str = ""):
        super().__init__(meldung)
        self.grund = grund or meldung


class SilhouettenVerlust(UserWarning):
    """Aus diesem PNG ist die Silhouette nicht exakt rekonstruierbar.

    Warnung und nicht Fehler: Das Zurückrechnen *funktioniert*, es verliert nur etwas.
    Wer den Verlust kennt und in Kauf nimmt, soll weiterarbeiten können; wer ihn nicht
    kennt, soll ihn nicht übersehen können.
    """


class BlenderRueckfall(UserWarning):
    """Der stdlib-Leser hat abgelehnt, es läuft jetzt ein GPL-Subprozess.

    Das ist keine Nebensache: Ab hier hängt das Ergebnis an einem installierten Blender.
    Ein stiller Rückfall würde eine Umgebungsanforderung einführen, die niemand bemerkt,
    bis sie auf einer anderen Maschine fehlt.
    """


# ======================================================================================
# PNG — reine Standardbibliothek
# ======================================================================================

#: Farbtyp → Kanäle je Pixel. Nur Graustufen; RGB (2), Palette (3) und RGBA (6) fehlen
#: hier absichtlich, sie sind keine Tiefenkarten und werden mit Begründung abgewiesen.
_PNG_GRAUSTUFEN_KANAELE = {0: 1, 4: 2}      # Grau, Grau + Alpha

_PNG_FARBTYP_NAME = {
    0: "Graustufen", 2: "RGB", 3: "Palette", 4: "Graustufen+Alpha", 6: "RGBA",
}


def _png_bloecke(daten: bytes, pfad):
    """Die Blöcke einer PNG-Datei durchlaufen und dabei **jede Prüfsumme prüfen**.

    Der CRC-Test kostet fast nichts und fängt genau den Fall, an dem sich dieses Projekt
    schon zweimal die Finger verbrannt hat: eine Datei, die existiert und trotzdem nicht
    das enthält, was ihr Name behauptet (abgebrochener Schreibvorgang, halb kopiert).
    Existenz ist kein Beleg für Inhalt.
    """
    pos = 8
    while pos + 8 <= len(daten):
        laenge = int.from_bytes(daten[pos:pos + 4], "big")
        typ = daten[pos + 4:pos + 8]
        ende = pos + 8 + laenge
        if ende + 4 > len(daten):
            raise BildError(
                f"{pfad}: Block {typ!r} ist abgeschnitten — die Datei endet mitten "
                f"darin. Ein unvollständiges PNG wird nicht halb gelesen."
            )
        inhalt = daten[pos + 8:ende]
        soll = int.from_bytes(daten[ende:ende + 4], "big")
        ist = zlib.crc32(typ + inhalt) & 0xFFFFFFFF
        if ist != soll:
            raise BildError(
                f"{pfad}: Prüfsumme des Blocks {typ!r} stimmt nicht "
                f"({ist:08x} statt {soll:08x}). Die Datei ist beschädigt."
            )
        pos = ende + 4
        yield typ, inhalt
        if typ == b"IEND":
            return
    raise BildError(f"{pfad}: kein IEND-Block — die Datei ist unvollständig.")


def _entfiltern(roh: bytes, breite: int, hoehe: int, bpp: int, pfad) -> bytearray:
    """Die fünf PNG-Zeilenfilter rückgängig machen (Spezifikation, Kapitel 9).

    Jede Zeile trägt vorn ein Filterbyte und bezieht sich auf ihren linken Nachbarn
    (``bpp`` Bytes zurück) und auf die Zeile darüber. Ein PNG-Schreiber wählt den Filter
    pro Zeile frei; ein Leser, der nur einen davon kann, liest die meisten Dateien still
    falsch statt gar nicht. Darum alle fünf.

    Für die Arten 0 (None) und 2 (Up) gibt es abgekürzte Wege: Sie hängen nicht vom
    *bereits entfilterten* linken Nachbarn ab und brauchen deshalb keine Schleife über
    Vorgängerwerte. Bei 512×512×2 Byte ist das der Unterschied zwischen einem spürbaren
    und einem unmerklichen Aufruf — und der Tiefen-Pass ist der heisse Pfad dieses Moduls.
    """
    zeilenlaenge = breite * bpp
    erwartet = hoehe * (zeilenlaenge + 1)
    if len(roh) < erwartet:
        raise BildError(
            f"{pfad}: entpackte Bilddaten sind zu kurz ({len(roh)} statt {erwartet} "
            f"Bytes für {breite}×{hoehe}). Die Datei behauptet mehr, als sie enthält."
        )

    aus = bytearray()
    vorherige = bytes(zeilenlaenge)
    p = 0
    for y in range(hoehe):
        art = roh[p]
        p += 1
        zeile = bytearray(roh[p:p + zeilenlaenge])
        p += zeilenlaenge

        if art == 0:                                    # None
            pass
        elif art == 2:                                  # Up
            zeile = bytearray((a + b) & 0xFF for a, b in zip(zeile, vorherige))
        elif art == 1:                                  # Sub
            for i in range(bpp, zeilenlaenge):
                zeile[i] = (zeile[i] + zeile[i - bpp]) & 0xFF
        elif art == 3:                                  # Average
            for i in range(zeilenlaenge):
                links = zeile[i - bpp] if i >= bpp else 0
                zeile[i] = (zeile[i] + ((links + vorherige[i]) >> 1)) & 0xFF
        elif art == 4:                                  # Paeth
            for i in range(zeilenlaenge):
                links = zeile[i - bpp] if i >= bpp else 0
                oben = vorherige[i]
                schraeg = vorherige[i - bpp] if i >= bpp else 0
                p_a, p_b, p_c = (abs(oben - schraeg), abs(links - schraeg),
                                 abs(links + oben - 2 * schraeg))
                vorhersage = links if (p_a <= p_b and p_a <= p_c) else (
                    oben if p_b <= p_c else schraeg)
                zeile[i] = (zeile[i] + vorhersage) & 0xFF
        else:
            raise BildError(
                f"{pfad}: unbekannte PNG-Filterart {art} in Zeile {y}. Die "
                f"Spezifikation kennt 0 bis 4 — hier stimmt etwas Grundsätzliches nicht."
            )

        aus += zeile
        vorherige = zeile
    return aus


def lies_png_graustufen(pfad) -> tuple[list[float], int, int]:
    """16- oder 8-Bit-Graustufen-PNG → ``(Werte 0..1, Breite, Hoehe)``. Reine stdlib.

    Die Werte laufen zeilenweise **von oben nach unten**, wie sie in der Datei stehen —
    dieselbe Reihenfolge, die auch ``lies_exr_tiefe`` liefert. Ohne diese Zusage wären
    die beiden Karten nicht indexgleich, und ``geometrie_qa`` setzt Indexgleichheit
    voraus (dort Vorbehalt 5: ein Versatz wird nicht erkannt, nur bestraft).

    Skaliert wird auf ``0..1`` durch Teilen durch den Maximalwert der Bittiefe (255 bzw.
    65535). Das macht den Rückgabewert von der Bittiefe unabhängig — die Rückrechnung in
    Meter braucht einen Anteil, keine Rohzahl.

    Args:
        pfad: Pfad zur PNG-Datei.

    Returns:
        ``(werte, breite, hoehe)`` mit ``len(werte) == breite * hoehe``.

    Raises:
        BildError: keine PNG-Datei, beschädigt (Prüfsummentest), verschränkt (Adam7),
            farbig statt Graustufen, oder eine Bittiefe unter 8. Alles davon wird
            gemeldet und nicht gedeutet: Ein RGB-Bild als Tiefenkarte zu lesen hiesse,
            aus einer Farbe eine Entfernung zu erfinden.
    """
    werte, breite, hoehe, _bittiefe = _png_lesen(pfad)
    return werte, breite, hoehe


def _png_lesen(pfad) -> tuple[list[float], int, int, int]:
    """Wie ``lies_png_graustufen``, gibt aber zusätzlich die Bittiefe zurück.

    Die Bittiefe interessiert nur ``png_befund`` — für den Quantisierungsschritt. Sie aus
    den gelesenen Werten zurückzuschliessen (etwa über den kleinsten Wert über 0) wäre
    eine Schätzung, die bei einem Bild aus wenigen Grautönen falsch ausgeht. Lieber eine
    interne Funktion mehr als eine geratene Zahl in einem Bericht.
    """
    pfad = Path(pfad)
    try:
        daten = pfad.read_bytes()
    except OSError as fehler:
        raise BildError(f"{pfad} lässt sich nicht lesen: {fehler}") from fehler

    if daten[:8] != PNG_SIGNATUR:
        raise BildError(
            f"{pfad} ist kein PNG (Signatur {daten[:8]!r}). Die Endung sagt nichts über "
            f"den Inhalt."
        )

    kopf = None
    idat = bytearray()
    for typ, inhalt in _png_bloecke(daten, pfad):
        if typ == b"IHDR":
            if len(inhalt) != 13:
                raise BildError(f"{pfad}: IHDR hat {len(inhalt)} statt 13 Bytes.")
            kopf = struct.unpack(">IIBBBBB", inhalt)
        elif typ == b"IDAT":
            idat += inhalt

    if kopf is None:
        raise BildError(f"{pfad}: kein IHDR-Block — die Datei hat keinen Kopf.")
    breite, hoehe, bittiefe, farbtyp, kompression, filtermethode, verschraenkt = kopf

    if breite == 0 or hoehe == 0:
        raise BildError(f"{pfad}: Bildgrösse {breite}×{hoehe} — ein leeres Bild.")
    if kompression != 0 or filtermethode != 0:
        raise BildError(
            f"{pfad}: Kompressionsverfahren {kompression} / Filtermethode "
            f"{filtermethode}. Die Spezifikation kennt nur 0/0."
        )
    if verschraenkt != 0:
        raise BildError(
            f"{pfad}: verschränktes PNG (Adam7). Der Multipass schreibt keine solchen "
            f"Dateien; sie hier zu deuten hiesse, sieben Teilbilder zu einer Reihenfolge "
            f"zusammenzuraten."
        )
    if farbtyp not in _PNG_GRAUSTUFEN_KANAELE:
        raise BildError(
            f"{pfad}: Farbtyp {farbtyp} ({_PNG_FARBTYP_NAME.get(farbtyp, 'unbekannt')}). "
            f"Eine Tiefenkarte hat genau eine Dimension — aus drei Farbkanälen eine "
            f"Entfernung zu machen wäre geraten, nicht gelesen."
        )
    if bittiefe not in (8, 16):
        raise BildError(
            f"{pfad}: Bittiefe {bittiefe}. Unterstützt sind 8 und 16 Bit; 1, 2 und 4 Bit "
            f"packen mehrere Pixel in ein Byte und kommen als Tiefenkarte nicht vor "
            f"(bei 4 Bit wären das 16 Stufen für die ganze Bautiefe)."
        )

    try:
        roh = zlib.decompress(bytes(idat))
    except zlib.error as fehler:
        raise BildError(f"{pfad}: IDAT lässt sich nicht entpacken: {fehler}") from fehler

    kanaele = _PNG_GRAUSTUFEN_KANAELE[farbtyp]
    bpp = kanaele * (bittiefe // 8)
    aus = _entfiltern(roh, breite, hoehe, bpp, pfad)

    n = breite * hoehe
    if bittiefe == 8:
        grau = aus if kanaele == 1 else aus[0::bpp]
        werte = [wert / 255.0 for wert in grau]
    else:
        zahlen = array("H")
        zahlen.frombytes(bytes(aus))
        if sys.byteorder == "little":
            # PNG legt Mehrbytewerte big-endian ab. `array` liest in Maschinenordnung —
            # ohne diesen Tausch käme auf jeder üblichen Maschine Unsinn heraus, und zwar
            # plausibel aussehender Unsinn.
            zahlen.byteswap()
        werte = [zahlen[i * kanaele] / 65535.0 for i in range(n)]

    return werte, breite, hoehe, bittiefe


# ======================================================================================
# Rückrechnung PNG → Meter
# ======================================================================================

def _normalisierung_lesen(normalisierung) -> tuple[float, float]:
    """``depth_normalisierung`` aus dem Blender-Report prüfen → ``(min_m, max_m)``.

    Streng, weil die beiden Zahlen der einzige Bezug zwischen einem Grauwert und einem
    Meter sind. Fehlt oder stimmt hier etwas nicht, ist jedes Ergebnis danach eine
    Entfernung ohne Grundlage — und die sähe genauso aus wie eine echte.
    """
    if not isinstance(normalisierung, dict):
        raise BildError(
            f"normalisierung: dict erwartet (das Feld `depth_normalisierung` aus dem "
            f"Blender-Report), war {type(normalisierung).__name__}."
        )
    fehlend = [name for name in ("min_m", "max_m") if name not in normalisierung]
    if fehlend:
        raise BildError(
            f"normalisierung: {fehlend} fehlt/fehlen. Ohne min_m und max_m ist das PNG "
            f"nicht in Meter zurückzurechnen — es ist dann nur noch ein Graubild."
        )

    gelesen = []
    for name in ("min_m", "max_m"):
        wert = normalisierung[name]
        if isinstance(wert, bool) or not isinstance(wert, (int, float)):
            raise BildError(
                f"normalisierung[{name!r}]: Zahl erwartet, war {wert!r} "
                f"({type(wert).__name__})."
            )
        wert = float(wert)
        if not math.isfinite(wert):
            raise BildError(f"normalisierung[{name!r}] ist {wert!r} — keine Länge.")
        gelesen.append(wert)

    min_m, max_m = gelesen
    if min_m > max_m:
        raise BildError(
            f"normalisierung: min_m {min_m} liegt hinter max_m {max_m}. Vertauscht "
            f"kehrte die Rückrechnung die Tiefenordnung um — und die Rangkorrelation "
            f"meldete brav −1, ohne dass an der Geometrie etwas falsch wäre."
        )
    if min_m <= 0.0:
        raise BildError(
            f"normalisierung: min_m {min_m} ist nicht positiv. Der Abstand eines Punktes "
            f"zur Kamera ist es immer; ein solcher Report stammt nicht aus diesem "
            f"Multipass."
        )
    return min_m, max_m


def tiefen_aus_png(pfad, normalisierung: dict, *,
                   grau_null: str = GRAU_NULL_HINTERGRUND) -> list[float]:
    """Normalisiertes PNG + ``depth_normalisierung`` aus dem Report → echte Meter.

    Rückrechnung, genau wie der Runner sie im Feld ``rueckrechnung`` angibt::

        meter = max_m - grau * (max_m - min_m)      # grau in 0..1, nah = hell

    **Die Falle, und was hier damit geschieht.** Der Hintergrund liegt im PNG bei
    Grauwert 0 — und das entfernteste Geometriepixel ebenfalls. Aus dem PNG allein sind
    die beiden nicht zu trennen. Es gibt keine Deutung, die dabei nichts verliert:

    * ``grau_null="hintergrund"`` (Vorgabe) gibt für Grauwert 0 ``math.inf`` zurück.
      ``geometrie_qa.silhouette`` liest das als Hintergrund. **Preis:** Die hintersten
      Geometriepunkte fallen aus der Silhouette heraus — sie fehlen, statt falsch zu
      sein. Vorgabe, weil ein zu kleiner Bau eine ehrlichere Auskunft ist als ein Bau,
      der bis in den Himmel reicht.
    * ``grau_null="geometrie"`` gibt für Grauwert 0 ``max_m`` zurück. **Preis:** Der
      ganze leere Himmel gilt dann als Geometrie in max_m Entfernung; ``geom_iou`` wird
      dadurch strukturell zu gross, und das Gate urteilt zu milde.

    Sobald überhaupt Nullpunkte vorkommen, wird das als ``SilhouettenVerlust`` **gewarnt**
    — mit Anzahl und Anteil. Wer die Silhouette exakt braucht, nimmt die EXR
    (``lies_exr_tiefe``); dort steht der Hintergrund als eigener, sehr grosser Wert.

    Args:
        pfad: das ``tiefe_norm.png`` des Multipass.
        normalisierung: Feld ``depth_normalisierung`` aus ``blender-report.json``.
        grau_null: ``GRAU_NULL_HINTERGRUND`` oder ``GRAU_NULL_GEOMETRIE``, siehe oben.

    Returns:
        Tiefen in Metern, zeilenweise von oben, ``breite * hoehe`` Einträge.

    Raises:
        BildError: PNG nicht lesbar, Normalisierung unbrauchbar, oder ``grau_null``
            unbekannt. Eine unbekannte Deutungsvorgabe wird nicht auf die Vorgabe
            zurückgesetzt — das wäre eine Entscheidung im Namen des Aufrufers.
    """
    if grau_null not in (GRAU_NULL_HINTERGRUND, GRAU_NULL_GEOMETRIE):
        raise BildError(
            f"grau_null: {grau_null!r} ist unbekannt. Erlaubt sind "
            f"{GRAU_NULL_HINTERGRUND!r} und {GRAU_NULL_GEOMETRIE!r} — welche der beiden "
            f"Deutungen gilt, kann dieses Modul nicht für den Aufrufer entscheiden."
        )
    min_m, max_m = _normalisierung_lesen(normalisierung)
    grau, breite, hoehe = lies_png_graustufen(pfad)
    return _rueckrechnen(grau, breite, hoehe, min_m, max_m, grau_null, Path(pfad).name)


def _rueckrechnen(grau: list[float], breite: int, hoehe: int, min_m: float, max_m: float,
                  grau_null: str, name: str) -> list[float]:
    """Grauwerte 0..1 → Meter, samt Warnung über den unvermeidlichen Verlust.

    Eigene Funktion, damit ``tiefen_aus_report`` Breite und Höhe aus demselben Lesevorgang
    bekommt, statt die Datei ein zweites Mal zu öffnen — und damit es die Rückrechnung nur
    an einer Stelle gibt.
    """
    spanne = max_m - min_m
    ersatz = math.inf if grau_null == GRAU_NULL_HINTERGRUND else max_m
    tiefen: list[float] = []
    n_null = 0
    for wert in grau:
        if wert == 0.0:
            n_null += 1
            tiefen.append(ersatz)
        else:
            tiefen.append(max_m - wert * spanne)

    if n_null:
        anteil = n_null / (breite * hoehe)
        if grau_null == GRAU_NULL_HINTERGRUND:
            folge = (f"Sie gelten hier als Hintergrund (inf). Die hintersten "
                     f"Geometriepunkte fallen damit aus der Silhouette — geom_iou wird "
                     f"eher zu klein.")
        else:
            folge = (f"Sie gelten hier als Geometrie in {max_m:.3f} m. Damit zählt auch "
                     f"der leere Himmel zur Silhouette — geom_iou wird zu gross und das "
                     f"Gate urteilt zu milde.")
        warnings.warn(
            SilhouettenVerlust(
                f"{name}: {n_null} von {breite * hoehe} Punkten "
                f"({anteil:.1%}) haben Grauwert 0. Hintergrund und entferntestes "
                f"Geometriepixel sind im normalisierten PNG nicht unterscheidbar. "
                f"{folge} Exakt geht die Silhouette nur aus der EXR."
            ),
            stacklevel=4,      # durch _rueckrechnen und tiefen_aus_png hindurch zum Aufrufer
        )
    return tiefen


def png_befund(pfad, normalisierung: dict) -> dict:
    """Was aus diesem PNG **nicht** hervorgeht — in Zahlen statt in Prosa.

    Dieselbe Auskunft wie die ``SilhouettenVerlust``-Warnung, nur maschinenlesbar: für
    Auswertungen und Berichte, die den Vorbehalt mitführen sollen, statt ihn in einem
    Logfile stehen zu lassen. Rechnet nichts zurück und trifft keine Wahl.

    Returns:
        ``{breite, hoehe, n_pixel, n_grau_null, anteil_grau_null, n_grau_eins,
        min_m, max_m, quantisierungsschritt_m, hinweis}``

        ``quantisierungsschritt_m`` ist die feinste Tiefendifferenz, die das PNG noch
        auflöst: ``(max_m - min_m) / (2^bittiefe - 1)``. Sie ist die Untergrenze jeder
        Abweichung, die man zwischen PNG und EXR misst — kleiner kann es nicht werden,
        und wer eine kleinere Abweichung meldet, hat sich verrechnet.
    """
    min_m, max_m = _normalisierung_lesen(normalisierung)
    grau, breite, hoehe, bittiefe = _png_lesen(pfad)
    n = breite * hoehe
    n_null = sum(1 for wert in grau if wert == 0.0)
    n_eins = sum(1 for wert in grau if wert == 1.0)
    stufen = (1 << bittiefe) - 1

    return {
        "breite": breite,
        "hoehe": hoehe,
        "bittiefe": bittiefe,
        "n_pixel": n,
        "n_grau_null": n_null,
        "anteil_grau_null": n_null / n,
        "n_grau_eins": n_eins,
        "min_m": min_m,
        "max_m": max_m,
        "quantisierungsschritt_m": (max_m - min_m) / stufen,
        "hinweis": (
            "Grauwert 0 trägt zwei Bedeutungen: Hintergrund und entferntestes "
            "Geometriepixel. Aus diesem PNG allein ist die Silhouette nicht exakt "
            "rekonstruierbar — dafür ist die EXR zuständig."
        ),
    }


# ======================================================================================
# EXR — stdlib-Weg
# ======================================================================================

_EXR_KOMPRESSION = {
    0: "NONE", 1: "RLE", 2: "ZIPS", 3: "ZIP", 4: "PIZ",
    5: "PXR24", 6: "B44", 7: "B44A", 8: "DWAA", 9: "DWAB",
}

#: Wie viele Bildzeilen in einem komprimierten Block stecken. Nur für die Verfahren, die
#: dieser Leser beherrscht — die übrigen werden vorher abgewiesen.
_EXR_ZEILEN_JE_BLOCK = {0: 1, 2: 1, 3: 16}

#: Pixeltyp → (Name, struct-Code, Bytes). UINT fehlt bewusst: Ein ganzzahliger Kanal ist
#: keine Entfernung in Metern, und ihn als solche zu lesen wäre geraten.
_EXR_PIXELTYP = {1: ("HALF", "e", 2), 2: ("FLOAT", "f", 4)}
_EXR_PIXELTYP_NAME = {0: "UINT", 1: "HALF", 2: "FLOAT"}

#: In welcher Reihenfolge nach dem Tiefenkanal gesucht wird, wenn die Datei mehrere hat.
#: ``V`` schreibt Blender für einen einkanaligen Compositor-Ausgang, ``Z`` ist der
#: OpenEXR-übliche Tiefenkanal, ``R``/``Y`` sind die Rückfälle für RGB- bzw. Luma-Ausgaben.
#: Gesucht wird auch hinter einem Ebenen-Praefix (``tiefe_.V``) — siehe ``_tiefenkanal``.
_EXR_TIEFENKANAELE = ("V", "Z", "R", "Y")


def _c_string(daten: bytes, p: int) -> tuple[str, int]:
    """Nullterminierte Zeichenkette ab ``p`` lesen → ``(Text, Position dahinter)``."""
    ende = daten.find(b"\0", p)
    if ende < 0:
        raise BildError("EXR-Kopf: nullterminierte Zeichenkette ohne Abschluss.")
    return daten[p:ende].decode("utf-8", "replace"), ende + 1


def exr_kopf(pfad) -> dict:
    """Den EXR-Kopf lesen und sagen, **ob** und **warum nicht** er hier lesbar ist.

    Das Diagnosewerkzeug zur Entscheidung zwischen stdlib-Weg und Blender-Rückfall. Es
    dekodiert keine Bilddaten und ist damit auch bei Dateien brauchbar, die dieser Leser
    nicht öffnen kann — genau dann braucht man es.

    Returns:
        ``{breite, hoehe, kompression, kompression_name, kanaele, line_order,
        gekachelt, mehrteilig, tief, version, ohne_blender_lesbar, grund,
        _daten_offset}``

        ``kanaele`` ist eine Liste von ``{name, typ, typ_name, bytes, x_sampling,
        y_sampling}``. ``grund`` ist ``None``, wenn der stdlib-Weg trägt, sonst ein
        Klartextsatz.

    Raises:
        BildError: keine EXR-Datei oder ein beschädigter Kopf.
    """
    pfad = Path(pfad)
    try:
        daten = pfad.read_bytes()
    except OSError as fehler:
        raise BildError(f"{pfad} lässt sich nicht lesen: {fehler}") from fehler
    return _exr_kopf_aus_bytes(daten, pfad)


def _exr_kopf_aus_bytes(daten: bytes, pfad) -> dict:
    if daten[:4] != EXR_MAGIC:
        raise BildError(
            f"{pfad} ist keine OpenEXR-Datei (Signatur {daten[:4]!r}). Auch hier gilt: "
            f"die Endung sagt nichts über den Inhalt."
        )
    if len(daten) < 8:
        raise BildError(f"{pfad}: Datei endet vor dem Versionsfeld.")

    (versionsfeld,) = struct.unpack("<I", daten[4:8])
    version = versionsfeld & 0xFF
    gekachelt = bool(versionsfeld & 0x0200)
    tief = bool(versionsfeld & 0x0800)
    mehrteilig = bool(versionsfeld & 0x1000)

    attribute: dict[str, tuple[str, bytes]] = {}
    p = 8
    while True:
        if p >= len(daten):
            raise BildError(f"{pfad}: EXR-Kopf endet ohne Abschlussbyte.")
        if daten[p] == 0:
            p += 1
            break
        name, p = _c_string(daten, p)
        typ, p = _c_string(daten, p)
        if p + 4 > len(daten):
            raise BildError(f"{pfad}: EXR-Attribut {name!r} ohne Längenangabe.")
        (groesse,) = struct.unpack("<i", daten[p:p + 4])
        p += 4
        if groesse < 0 or p + groesse > len(daten):
            raise BildError(f"{pfad}: EXR-Attribut {name!r} reicht über das Dateiende.")
        attribute[name] = (typ, daten[p:p + groesse])
        p += groesse

    for pflicht in ("channels", "dataWindow", "compression", "lineOrder"):
        if pflicht not in attribute:
            raise BildError(f"{pfad}: EXR-Kopf ohne Pflichtattribut {pflicht!r}.")

    rohkanaele = attribute["channels"][1]
    kanaele = []
    q = 0
    while q < len(rohkanaele) and rohkanaele[q] != 0:
        name, q = _c_string(rohkanaele, q)
        if q + 16 > len(rohkanaele):
            raise BildError(f"{pfad}: Kanalliste bricht bei {name!r} ab.")
        typ, _linear, x_sampling, y_sampling = struct.unpack("<iB3xii", rohkanaele[q:q + 16])
        q += 16
        kanaele.append({
            "name": name,
            "typ": typ,
            "typ_name": _EXR_PIXELTYP_NAME.get(typ, f"unbekannt({typ})"),
            "bytes": _EXR_PIXELTYP.get(typ, (None, None, 0))[2],
            "x_sampling": x_sampling,
            "y_sampling": y_sampling,
        })
    if not kanaele:
        raise BildError(f"{pfad}: EXR ohne Kanäle.")

    x_min, y_min, x_max, y_max = struct.unpack("<iiii", attribute["dataWindow"][1])
    breite, hoehe = x_max - x_min + 1, y_max - y_min + 1
    if breite <= 0 or hoehe <= 0:
        raise BildError(f"{pfad}: leeres dataWindow ({breite}×{hoehe}).")

    kompression = attribute["compression"][1][0]
    line_order = attribute["lineOrder"][1][0]

    grund = _warum_nicht_ohne_blender(kompression, line_order, kanaele,
                                      gekachelt, mehrteilig, tief)
    return {
        "breite": breite, "hoehe": hoehe,
        "x_min": x_min, "y_min": y_min, "x_max": x_max, "y_max": y_max,
        "kompression": kompression,
        "kompression_name": _EXR_KOMPRESSION.get(kompression, f"unbekannt({kompression})"),
        "kanaele": kanaele,
        "line_order": line_order,
        "gekachelt": gekachelt, "mehrteilig": mehrteilig, "tief": tief,
        "version": version,
        "ohne_blender_lesbar": grund is None,
        "grund": grund,
        "_daten_offset": p,
    }


def _tiefenkanal(kanaele: list[dict]) -> tuple[int, dict] | tuple[None, None]:
    """Welcher Kanal trägt die Tiefe? → ``(Index in der Kanalliste, Kanal)``.

    Bei genau einem Kanal ist die Frage beantwortet. Bei mehreren entscheidet die
    **Vorrangliste** ``_EXR_TIEFENKANAELE``, nicht die Reihenfolge in der Datei: EXR führt
    Kanäle alphabetisch, und alphabetisch stünde in einer Datei mit ``R`` und ``V`` das
    ``R`` vorn — obwohl ``V`` der Kanal ist, den Blender für einen einwertigen Ausgang
    schreibt. Nach Dateireihenfolge zu wählen läse dann still den falschen Kanal.

    Eine gemeinsame Funktion für Leser und Diagnose, damit nicht auseinanderläuft, was
    ``exr_kopf`` meldet und was ``lies_exr_tiefe_stdlib`` wirklich nimmt.
    """
    if len(kanaele) == 1:
        return 0, kanaele[0]
    namen = [k["name"] for k in kanaele]

    # Erst der genaue Name.
    for gesucht in _EXR_TIEFENKANAELE:
        if gesucht in namen:
            index = namen.index(gesucht)
            return index, kanaele[index]

    # Dann der Name hinter einem Ebenen-Praefix. Multilayer-EXR stellt den Ebenennamen
    # punktgetrennt voran (`tiefe_.V`, `ViewLayer.Depth.Z`) — das ist OpenEXR-Konvention,
    # kein Sonderfall. Blender 5.2 schreibt am File-Output-Knoten NUR noch Multilayer
    # (belegt an der HomeStation, auf-20260818-03), also ist dieser Weg dort der normale.
    # Ohne ihn faende der Leser den Tiefenkanal nicht und fiele unnoetig auf Blender
    # zurueck — bei einer Datei, die er problemlos selbst lesen kann.
    for gesucht in _EXR_TIEFENKANAELE:
        for index, name in enumerate(namen):
            if name.rsplit(".", 1)[-1] == gesucht:
                return index, kanaele[index]
    return None, None


def _warum_nicht_ohne_blender(kompression, line_order, kanaele,
                              gekachelt, mehrteilig, tief) -> str | None:
    """Ein Satz, warum der stdlib-Weg diese Datei nicht kann — oder ``None``.

    Bewusst als eigene Funktion: Die Liste der Grenzen ist die ehrlichste Beschreibung
    dieses Lesers, und sie soll an genau einer Stelle stehen — sonst driftet das, was
    ``exr_kopf`` meldet, von dem weg, was ``lies_exr_tiefe_stdlib`` wirklich tut.
    """
    if mehrteilig:
        return "mehrteilige EXR (multipart)"
    if tief:
        return "Deep-EXR (mehrere Abtastwerte je Bildpunkt)"
    if gekachelt:
        return "gekachelte EXR (tiled statt scanline)"
    if kompression not in _EXR_ZEILEN_JE_BLOCK:
        name = _EXR_KOMPRESSION.get(kompression, f"unbekannt({kompression})")
        return (f"Kompression {name} — dieser Leser kann NONE, ZIPS und ZIP, weil das "
                f"reines zlib ist; alles andere bräuchte einen eigenen Codec")
    if line_order not in (0, 1):
        return f"lineOrder {line_order} (RANDOM_Y)"

    _, kanal = _tiefenkanal(kanaele)
    if kanal is None:
        namen = [k["name"] for k in kanaele]
        return (f"kein Tiefenkanal gefunden — vorhanden sind {namen}, gesucht wird "
                f"{list(_EXR_TIEFENKANAELE)}")
    if kanal["typ"] not in _EXR_PIXELTYP:
        return (f"Kanal {kanal['name']!r} ist {kanal['typ_name']} — eine Entfernung in "
                f"Metern ist FLOAT oder HALF, nicht UINT")
    if kanal["x_sampling"] != 1 or kanal["y_sampling"] != 1:
        return (f"Kanal {kanal['name']!r} ist unterabgetastet "
                f"({kanal['x_sampling']}/{kanal['y_sampling']})")
    # Auch die ANDEREN Kanäle müssen bekannt sein: Ihre Bytebreite bestimmt den Versatz
    # des Tiefenkanals innerhalb der Bildzeile. Ein unbekannter Nachbar verschöbe das
    # Fenster — und herausgelesen würde eine Zahlenfolge, die aussieht wie eine Tiefe.
    unbekannt = [k["name"] for k in kanaele if k["typ"] not in _EXR_PIXELTYP]
    if unbekannt:
        return (f"Kanäle {unbekannt} haben einen Typ, dessen Grösse dieser Leser nicht "
                f"kennt — damit stimmt schon der Zeilenversatz nicht")
    return None


def _zip_entpacken(roh: bytes) -> bytearray:
    """OpenEXR-ZIP/ZIPS-Block → Rohbytes. ``zlib`` plus die zwei Nachbearbeitungen.

    OpenEXR packt vor dem Deflate zweimal um, damit Gleitkommazahlen überhaupt
    komprimierbar werden:

    1. **Prädiktor** — gespeichert werden Differenzen zu Nachbarbytes, nicht die Bytes
       selbst. Rückwärts ist das eine laufende Summe: ``b[i] = b[i-1] + b[i] - 128``
       (mod 256).
    2. **Byte-Entflechtung** — die erste Hälfte des Blocks enthält alle geradzahligen
       Bytepositionen, die zweite alle ungeraden. Zusammengehörige Bytes eines Wertes
       liegen dadurch beim Packen weit auseinander, gleichartige nah beieinander.

    Die laufende Summe steht hier als ``accumulate`` und nicht als Indexschleife: Weil
    ``& 0xFF`` mit der Addition verträglich ist (Rechnen modulo 256), darf man erst alles
    aufsummieren und die Maske ganz am Schluss anlegen. Ergebnis identisch, rund doppelt
    so schnell — und bei einem 512er-Bild sind das ein paar hunderttausend Schritte.
    """
    b = zlib.decompress(roh)
    if not b:
        return bytearray()
    summiert = accumulate(chain((b[0],), (wert - 128 for wert in b[1:])))
    entfaltet = bytes(wert & 0xFF for wert in summiert)

    haelfte = (len(entfaltet) + 1) // 2
    aus = bytearray(len(entfaltet))
    aus[0::2] = entfaltet[:haelfte]
    aus[1::2] = entfaltet[haelfte:]
    return aus


def lies_exr_tiefe_stdlib(pfad) -> tuple[list[float], int, int]:
    """32-Bit-EXR → echte Meter, **ohne** jede Abhängigkeit und ohne Blender.

    Beherrscht genau die Spielart, die dieses Projekt selbst erzeugt und die im
    Renderer-Alltag die übliche ist: scanline, lineOrder INCREASING/DECREASING_Y,
    Kompression NONE/ZIPS/ZIP, Kanaltyp FLOAT oder HALF. Alles andere wird als
    ``EXRVarianteError`` abgewiesen — nicht geraten.

    Die Werte laufen zeilenweise **von oben nach unten**, also in derselben Reihenfolge
    wie bei ``lies_png_graustufen``. In der EXR-Datei ist das die natürliche Ordnung
    (``y`` wächst nach unten); Blenders ``image.pixels`` läuft dagegen von unten nach
    oben, weshalb der Runner jenseits der Grenze eigens spiegelt. Beide Wege liefern
    daher dasselbe.

    Hintergrundpunkte kommen zurück, wie sie in der Datei stehen — bei Cycles sind das
    sehr grosse Zahlen in der Grössenordnung 1e10. Sie werden hier **nicht** auf ``inf``
    oder ``None`` umgesetzt: Was Hintergrund ist, entscheidet ``geometrie_qa.silhouette``
    anhand seiner Marke, und diese Entscheidung gehört nicht in einen Dateileser.

    Returns:
        ``(tiefen_in_metern, breite, hoehe)``.

    Raises:
        EXRVarianteError: gültige EXR in einer nicht unterstützten Spielart. Nur dieser
            Fall rechtfertigt den Blender-Rückfall.
        BildError: keine EXR, beschädigt oder abgeschnitten.
    """
    pfad = Path(pfad)
    try:
        daten = pfad.read_bytes()
    except OSError as fehler:
        raise BildError(f"{pfad} lässt sich nicht lesen: {fehler}") from fehler

    kopf = _exr_kopf_aus_bytes(daten, pfad)
    if kopf["grund"] is not None:
        raise EXRVarianteError(
            f"{pfad}: {kopf['grund']}. Diese Datei ist in Ordnung, nur nicht in der "
            f"Spielart, die ohne Fremdbibliothek lesbar ist — `lies_exr_tiefe` fällt "
            f"dafür auf den Blender-Subprozess zurück.",
            kopf["grund"],
        )

    breite, hoehe = kopf["breite"], kopf["hoehe"]
    kanaele = kopf["kanaele"]
    index, kanal = _tiefenkanal(kanaele)
    _, code, groesse = _EXR_PIXELTYP[kanal["typ"]]

    # Ein Scanline-Block enthält alle Kanäle nacheinander, jeder über die volle Breite.
    # Die Kanäle stehen dabei in der Reihenfolge der Kanalliste (die EXR alphabetisch
    # führt) — der Versatz des gesuchten Kanals ist damit die Summe der davor liegenden.
    versatz = sum(breite * k["bytes"] for k in kanaele[:index])
    zeilenbytes = sum(breite * k["bytes"] for k in kanaele)

    zeilen_je_block = _EXR_ZEILEN_JE_BLOCK[kopf["kompression"]]
    n_bloecke = (hoehe + zeilen_je_block - 1) // zeilen_je_block
    p = kopf["_daten_offset"]
    if p + 8 * n_bloecke > len(daten):
        raise BildError(f"{pfad}: Blocktabelle reicht über das Dateiende.")
    offsets = struct.unpack(f"<{n_bloecke}Q", daten[p:p + 8 * n_bloecke])

    y_min, y_max = kopf["y_min"], kopf["y_max"]
    werte = [0.0] * (breite * hoehe)
    gesehen = bytearray(hoehe)
    for offset in offsets:
        if offset + 8 > len(daten):
            raise BildError(f"{pfad}: Blockanfang {offset} liegt hinter dem Dateiende.")
        y, groesse_block = struct.unpack("<ii", daten[offset:offset + 8])
        if groesse_block < 0 or offset + 8 + groesse_block > len(daten):
            raise BildError(f"{pfad}: Block bei y={y} reicht über das Dateiende.")
        roh = daten[offset + 8:offset + 8 + groesse_block]

        n_zeilen = min(zeilen_je_block, y_max - y + 1)
        erwartet = n_zeilen * zeilenbytes
        if groesse_block == erwartet:
            # Half die Kompression nichts, legt OpenEXR den Block unkomprimiert ab. Das
            # ist erlaubt und kommt bei Rauschen regelmässig vor.
            block = roh
        elif kopf["kompression"] == 0:
            raise BildError(
                f"{pfad}: unkomprimierter Block bei y={y} hat {groesse_block} statt "
                f"{erwartet} Bytes."
            )
        else:
            try:
                block = _zip_entpacken(roh)
            except zlib.error as fehler:
                raise BildError(
                    f"{pfad}: Block bei y={y} lässt sich nicht entpacken: {fehler}"
                ) from fehler
            if len(block) != erwartet:
                raise BildError(
                    f"{pfad}: Block bei y={y} ergibt {len(block)} statt {erwartet} Bytes."
                )

        for i in range(n_zeilen):
            zeile = y - y_min + i
            if not 0 <= zeile < hoehe:
                raise BildError(f"{pfad}: Block meldet Zeile {zeile} ausserhalb des Bildes.")
            anfang = i * zeilenbytes + versatz
            stueck = block[anfang:anfang + breite * groesse]
            werte[zeile * breite:(zeile + 1) * breite] = struct.unpack(
                f"<{breite}{code}", stueck)
            gesehen[zeile] = 1

    fehlend = gesehen.count(0)
    if fehlend:
        raise BildError(
            f"{pfad}: {fehlend} von {hoehe} Bildzeilen fehlen in der Blocktabelle. Eine "
            f"lückenhafte Tiefenkarte sähe aus wie eine mit Löchern in der Geometrie."
        )
    return werte, breite, hoehe


# ======================================================================================
# EXR — Rückfall über die Prozessgrenze zu Blender
# ======================================================================================

def _default_starte(cmd: list[str], timeout: int) -> subprocess.CompletedProcess:
    """Derselbe Subprozessaufruf wie in ``seams`` — hier eigenständig, damit dieses
    Modul die Naht nicht aus einem privaten Namen des Nachbarn borgt."""
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=False)


def lies_exr_tiefe_ueber_blender(pfad, *, timeout: int = 300,
                                 _starte=None) -> tuple[list[float], int, int]:
    """32-Bit-EXR → echte Meter, über ``blender --background`` als Subprozess.

    Der Rückfall für EXR-Spielarten, die ``lies_exr_tiefe_stdlib`` nicht kann (PIZ,
    DWAA/DWAB, B44, PXR24, gekachelt, mehrteilig). Blender ist ohnehin der Erzeuger
    dieser Dateien und steht als GPL-Komponente bereits im ``NOTICE``; ihn zu rufen
    kostet keine neue Lizenzentscheidung, nur Zeit.

    Der Runner schreibt die Tiefe als rohe ``float32``-Datei (little-endian) neben einen
    JSON-Report. **Nicht als JSON-Zahlenliste:** Ein 512er-Bild sind 262 144 Werte; als
    Text wären das mehrere Megabyte, die beide Seiten parsen müssten, mit einer
    Rundungsfrage obendrein. Roh ist es exakt, klein und in drei Zeilen ``array`` wieder
    einzulesen.

    Args:
        pfad: die EXR-Datei.
        timeout: Sekunden bis zum Abbruch des Subprozesses.
        _starte: Testnaht, ersetzt den Subprozessaufruf. Ohne sie wäre dieser Weg nur
            auf Rechnern mit Blender prüfbar — dieselbe Bauart wie in ``seams``.

    Returns:
        ``(tiefen_in_metern, breite, hoehe)``, zeilenweise von oben — der Runner spiegelt
        Blenders von unten laufende Pixelreihenfolge, damit beide Wege indexgleich sind.

    Raises:
        SeamError: Blender ist nicht auffindbar. Bewusst nicht in ``BildError``
            umgetauft: Nicht die Datei ist das Problem, sondern die Umgebung.
        BildError: der Lauf scheitert oder liefert keinen brauchbaren Report.
    """
    pfad = Path(pfad)
    if not pfad.exists():
        raise BildError(f"{pfad} gibt es nicht.")
    starte = _starte or _default_starte
    binaer = finde_blender()

    with tempfile.TemporaryDirectory(prefix="aiimaging-exr-") as ordner:
        out = Path(ordner)
        cmd = [binaer, "--background", "--factory-startup",
               "--python", str(EXR_RUNNER), "--",
               "--exr", str(pfad), "--out", str(out)]
        ergebnis = starte(cmd, timeout)

        bericht = out / "exr-report.json"
        # Zwei unabhängige Bedingungen, beide notwendig — dieselbe Lehre wie in `seams`:
        # Blender kann 0 melden und trotzdem nichts geschrieben haben.
        if ergebnis.returncode != 0:
            raise BildError(
                f"EXR-Lesen über Blender endete mit Code {ergebnis.returncode}:\n"
                f"{(ergebnis.stderr or ergebnis.stdout or '').strip()[-1200:]}"
            )
        if not bericht.exists():
            raise BildError(
                f"EXR-Lesen über Blender schrieb keinen Report:\n"
                f"{(ergebnis.stderr or ergebnis.stdout or '').strip()[-1200:]}"
            )
        try:
            report = json.loads(bericht.read_text(encoding="utf-8"))
        except json.JSONDecodeError as fehler:
            raise BildError(f"Report des EXR-Runners ist kein JSON: {fehler}") from fehler

        if report.get("status") != "ok":
            raise BildError(f"EXR-Runner meldet Fehler: {report.get('error')}")
        for feld in ("breite", "hoehe", "roh_datei"):
            if feld not in report:
                raise BildError(f"Report des EXR-Runners ohne Feld {feld!r}.")

        breite, hoehe = int(report["breite"]), int(report["hoehe"])
        roh_datei = Path(report["roh_datei"])
        if not roh_datei.is_absolute():
            roh_datei = out / roh_datei
        try:
            rohdaten = roh_datei.read_bytes()
        except OSError as fehler:
            raise BildError(
                f"Rohdatei des EXR-Runners fehlt: {roh_datei} ({fehler})"
            ) from fehler

    erwartet = breite * hoehe * 4
    if len(rohdaten) != erwartet:
        raise BildError(
            f"Rohdatei hat {len(rohdaten)} statt {erwartet} Bytes für {breite}×{hoehe} "
            f"float32-Werte."
        )
    zahlen = array("f")
    zahlen.frombytes(rohdaten)
    if sys.byteorder != "little":
        # Der Runner schreibt ausdrücklich little-endian; `array` liest in
        # Maschinenordnung. Auf big-endian-Maschinen käme sonst plausibler Unsinn heraus.
        zahlen.byteswap()
    return list(zahlen), breite, hoehe


def lies_exr_tiefe(pfad, *, timeout: int = 300,
                   _starte=None) -> tuple[list[float], int, int]:
    """32-Bit-EXR → echte Meter. Erst ohne Abhängigkeit, notfalls über die Prozessgrenze.

    Der Weg, den Aufrufer nehmen sollen. Er versucht zuerst ``lies_exr_tiefe_stdlib`` —
    das trifft auf jede EXR zu, die dieses Projekt selbst schreibt, und braucht weder
    Blender noch eine Bildbibliothek. Nur wenn die Datei in einer nicht unterstützten
    Spielart vorliegt (``EXRVarianteError``), fällt er auf ``blender --background``
    zurück und **meldet das als Warnung** (``BlenderRueckfall``).

    Warum die Warnung nötig ist: Ab dem Rückfall hängt das Ergebnis an einem installierten
    GPL-Binary. Das darf man tun — es ist eine Prozessgrenze, keine Einverleibung —, aber
    man darf es nicht unbemerkt tun, sonst wandert eine Umgebungsanforderung in den Code,
    die erst auf einer fremden Maschine auffällt.

    Eine **beschädigte** Datei löst den Rückfall nicht aus (``BildError`` statt
    ``EXRVarianteError``). Ein Prozessstart würde denselben Fehler nur langsamer melden.

    Args:
        pfad: die EXR-Datei.
        timeout: Sekunden für den Subprozess, falls es dazu kommt.
        _starte: Testnaht für den Subprozessaufruf, siehe ``lies_exr_tiefe_ueber_blender``.

    Returns:
        ``(tiefen_in_metern, breite, hoehe)``, zeilenweise von oben.
    """
    try:
        return lies_exr_tiefe_stdlib(pfad)
    except EXRVarianteError as fehler:
        warnings.warn(
            BlenderRueckfall(
                f"{Path(pfad).name}: {fehler.grund}. Der stdlib-Leser kann diese Datei "
                f"nicht, also wird jetzt `blender --background` als Subprozess gestartet "
                f"— ab hier braucht dieser Aufruf ein installiertes Blender."
            ),
            stacklevel=2,
        )
        return lies_exr_tiefe_ueber_blender(pfad, timeout=timeout, _starte=_starte)


# ======================================================================================
# Die Naht zur Geometrie-QA
# ======================================================================================

def tiefen_aus_report(report: dict, *, quelle: str = QUELLE_AUTO,
                      grau_null: str = GRAU_NULL_HINTERGRUND,
                      timeout: int = 300, _starte=None) -> tuple[list[float], int, int]:
    """Blender-Report → Soll-Tiefenkarte für ``geometrie_qa.geometrie_score``.

    Das ist der eigentliche Handgriff, für den es dieses Modul gibt: Was
    ``seams.glb_zu_multipass`` zurückgibt, geht hier hinein, und heraus kommt, was
    ``geometrie_score`` als ``soll`` erwartet.

    Args:
        report: das Rückgabe-Dictionary von ``seams.glb_zu_multipass`` bzw. der Inhalt
            von ``blender-report.json``.
        quelle: ``QUELLE_AUTO`` nimmt die EXR, wenn es sie gibt, sonst das PNG.
            ``QUELLE_EXR`` und ``QUELLE_PNG`` erzwingen den jeweiligen Weg.
        grau_null: nur für den PNG-Weg, siehe ``tiefen_aus_png``.
        timeout, _starte: nur für den EXR-Weg, falls er auf Blender zurückfällt.

    Returns:
        ``(tiefen_in_metern, breite, hoehe)``.

    Raises:
        BildError: der Report nennt keine brauchbare Quelle, oder die genannte Datei
            fehlt.

    **Warum die EXR den Vorrang hat.** Nur sie trägt die Silhouette exakt; das PNG kann
    Hintergrund und entferntestes Geometriepixel nicht trennen (siehe Modul-Docstring).
    Der PNG-Weg ist der Rückfall für den Fall, dass nur noch das normalisierte Bild
    vorliegt — und er meldet seinen Verlust selbst.
    """
    if not isinstance(report, dict):
        raise BildError(f"report: dict erwartet, war {type(report).__name__}.")
    if quelle not in (QUELLE_AUTO, QUELLE_EXR, QUELLE_PNG):
        raise BildError(
            f"quelle: {quelle!r} ist unbekannt. Erlaubt sind {QUELLE_AUTO!r}, "
            f"{QUELLE_EXR!r} und {QUELLE_PNG!r}."
        )

    exr = report.get("depth_exr")
    png = report.get("depth_png")
    nimm_exr = quelle == QUELLE_EXR or (quelle == QUELLE_AUTO and exr and Path(exr).exists())

    if nimm_exr:
        if not exr:
            raise BildError(
                "Report nennt kein Feld `depth_exr` — ohne EXR gibt es die Silhouette "
                "nicht exakt; mit quelle='png' liesse sich das PNG nehmen, samt seinem "
                "dokumentierten Verlust."
            )
        return lies_exr_tiefe(exr, timeout=timeout, _starte=_starte)

    if not png:
        raise BildError(
            "Report nennt weder eine lesbare `depth_exr` noch ein `depth_png`. Der Lauf "
            "hat keine Tiefenkarte hinterlassen — der Report sagt das im Feld `error`."
        )
    normalisierung = report.get("depth_normalisierung")
    if not normalisierung:
        raise BildError(
            "Report nennt ein `depth_png`, aber keine `depth_normalisierung`. Ohne "
            "min_m/max_m ist das PNG nicht in Meter zurückzurechnen."
        )
    if grau_null not in (GRAU_NULL_HINTERGRUND, GRAU_NULL_GEOMETRIE):
        raise BildError(f"grau_null: {grau_null!r} ist unbekannt.")
    min_m, max_m = _normalisierung_lesen(normalisierung)
    grau, breite, hoehe = lies_png_graustufen(png)
    tiefen = _rueckrechnen(grau, breite, hoehe, min_m, max_m, grau_null, Path(png).name)
    return tiefen, breite, hoehe


__all__ = [
    # SeamError wird mit ausgegeben, damit Aufrufer `except (BildError, SeamError)`
    # schreiben können, ohne zusätzlich `seams` importieren zu müssen: Das eine meint
    # "die Datei taugt nicht", das andere "die Umgebung fehlt".
    "BildError", "BlenderRueckfall", "EXRVarianteError", "SeamError", "SilhouettenVerlust",
    "EXR_RUNNER", "GRAU_NULL_GEOMETRIE", "GRAU_NULL_HINTERGRUND",
    "QUELLE_AUTO", "QUELLE_EXR", "QUELLE_PNG",
    "exr_kopf", "lies_exr_tiefe", "lies_exr_tiefe_stdlib", "lies_exr_tiefe_ueber_blender",
    "lies_png_graustufen", "png_befund", "tiefen_aus_png", "tiefen_aus_report",
]
