"""Bilder **schreiben** — die Gegenseite zu :mod:`aiimaging.bildlesen`, reine stdlib.

Warum es dieses Modul gibt (HomeStation-Befund, 2026-08-18)
-----------------------------------------------------------
Die normalisierte Tiefenkarte ``tiefe_norm.png`` entstand bisher **in Blender**: Der
Runner schrieb die EXR, lud sie mit ``bpy.data.images.load`` wieder ein und rechnete sie
um. Auf Blender 5.2 bricht dieser Weg — und zwar an einer Stelle, die man nicht erwartet:

    Blender 5.2 kann die Datei, die es schreiben **muss**, selbst nicht wieder einlesen.
    Der File-Output-Knoten lässt dort nur noch ``OPEN_EXR_MULTILAYER`` zu; eine so
    geschriebene Datei lädt ``bpy.data.images.load`` als **0×0 mit 0 Kanälen**. Eine
    einschichtige EXR lädt im selben Lauf als 64×64 mit 4 Kanälen — es liegt also am
    Multilayer-Leseweg, nicht an der Datei.

Die Datei ist in Ordnung: :func:`aiimaging.bildlesen.lies_exr_tiefe_stdlib` holt aus
derselben 5.2-Datei 11 151 Geometriepixel zwischen 17,9 und 26,6 m heraus — dieselben
Zahlen, die Blender 4.2 aus seiner eigenen (einschichtigen) EXR meldet.

Daraus folgt eine Verschiebung der Naht, nicht ein Flicken: **Die Normalisierung gehört
auf die Produktseite.** Sie ist reine Arithmetik auf einem Zahlenfeld — es gibt keinen
Grund, dafür ein GPL-Programm zu starten, dessen Leseweg sich zwischen zwei Fassungen
ändert. Der Runner tut jetzt nur noch, was allein Blender kann: rendern.

Das ist zugleich Regel 4 in ihrer schärfsten Lesart: Was ohne Blender geht, geht ohne
Blender — und ist damit ohne GPU, ohne Oberfläche und ohne Prozessgrenze testbar.

Was der Wechsel an den Zahlen ändert — gemessen, nicht behauptet
----------------------------------------------------------------
Gegen die letzte in Blender 4.2 erzeugte Referenz (256×256, dieselbe Szene) gemessen:

* ``min_m``, ``max_m`` und ``n_geometriepixel`` sind **identisch**.
* Von 65 536 Bildpunkten weichen **18** um genau **einen** von 65 535 Quantisierungs-
  schritten ab, kein einziger um mehr. Grösste Abweichung im normalisierten Bereich:
  7,7 · 10⁻⁶ — das ist eine **halbe** Quantisierungsstufe.

Die Ursache ist bekannt und harmlos: Blender rechnet in float32, dieses Modul in Pythons
float64. Wo ein Zwischenwert genau auf der Rundungsgrenze liegt, fällt er mal so, mal so.
Eine float32-Nachbildung wäre möglich, aber sie würde die Reihenfolge von NumPy-Operationen
nachahmen, die niemand zusichert — falsche Genauigkeit statt echter. Darum ist ab jetzt
**dieses Modul die Referenz** und nicht mehr Blender.

Warum überhaupt ein eigener PNG-Schreiber
------------------------------------------
Aus demselben Grund wie beim Leser: Das Paket hat **keine** Laufzeitabhängigkeiten
(``pyproject.toml``), und ein 16-Bit-Graustufen-PNG ist mit ``zlib`` aus der stdlib in
gut hundert Zeilen geschrieben. Pillow einzuziehen hiesse, für ein gelöstes Problem eine
Abhängigkeit samt Binäranteil und ungeprüfter Lizenzlage aufzunehmen.
"""
from __future__ import annotations

import math
import struct
import zlib
from collections.abc import Sequence
from pathlib import Path

#: Ab diesem Abstand gilt ein Bildpunkt als Hintergrund, nicht als Geometrie.
#:
#: Cycles schreibt für Strahlen, die nichts treffen, keinen Sonderwert, sondern eine sehr
#: grosse Zahl (Grössenordnung 1e10). 1e7 Meter sind 10 000 km — jenseits jedes Bauwerks
#: und weit unterhalb dessen, was der Hintergrund liefert. Der Wert ist mit Absicht
#: derselbe wie im Blender-Runner; er steht hier, damit die Produktseite ihn nicht aus
#: einem Modul importieren muss, das nur in Blender lauffähig ist.
HINTERGRUND_AB_M = 1.0e7

#: Grauwert des Hintergrunds im normalisierten PNG. Siehe `KONVENTION`.
HINTERGRUND_GRAUWERT = 0.0

KONVENTION = (
    "nah = hell (ControlNet); Hintergrund = 0. Das entfernteste Geometriepixel liegt "
    "ebenfalls bei 0 und ist im PNG nicht vom Hintergrund zu unterscheiden — wer die "
    "Silhouette exakt braucht, nimmt die EXR."
)

RUECKRECHNUNG = "meter = max_m - grau * (max_m - min_m), grau in 0..1"

#: Der dunkelste Grauwert, den **geklemmte Geometrie** noch bekommen darf.
#:
#: **Der Anlass ist ein Fehlschlag der ersten Fassung vom 16.09.2026, gemessen:** Geklemmt
#: wurde auf ``max_m``, und das ergibt nach der Formel oben Grauwert genau 0.0 — also
#: :data:`HINTERGRUND_GRAUWERT`. Die geklemmte Fernsichtebene war damit im PNG **byte-gleich
#: mit dem Himmel**::
#:
#:     geklemmte Geometrie {0.0}   echter Hintergrund {0.0}   unterscheidbar: nein
#:
#: Das ist nicht nur hässlich, es ist genau der Silhouettenverlust, vor dem
#: :mod:`aiimaging.bildlesen` an anderer Stelle warnt — nur absichtlich herbeigeführt und
#: für 1,14 % der Punkte statt für den einen hintersten. Die Silhouette entsteht aus
#: „Grauwert > Hintergrund"; geklemmte Punkte fielen heraus, und ``geom_iou`` fiele mit
#: ihnen. **Eine Kennzahl, die stimmt, während das Bild schlechter wird, ist die falsche
#: Kennzahl** — hier wäre es umgekehrt schlimmer: Das Bild bliebe gleich, die Kennzahl
#: würde schlechter, und niemand wüsste warum.
#:
#: **Warum ein ganzer 8-Bit-Schritt und nicht ein halber.** Der erste Versuch war ein
#: halber (1/510) mit der Begründung, er überlebe beide Bittiefen. Nachgemessen überlebt
#: er sie nicht::
#:
#:     Boden 1/510:  16 Bit → Stufe 128 (≠ 0, gut)   8 Bit → Stufe 0 (KOLLISION)
#:     Boden 1/255:  16 Bit → Stufe 257 (≠ 0, gut)   8 Bit → Stufe 1 (≠ 0, gut)
#:
#: Ein halber Schritt rundet auf null, das ist die Bedeutung von „halb". Unsere
#: ``tiefe_norm.png`` ist 16-Bit, der 8-Bit-Fall wäre also gar nicht unser Weg — aber
#: eine Begründung, die nur für den Weg gilt, den man ohnehin geht, trägt nichts. Ein
#: ganzer 8-Bit-Schritt kostet 0,39 % des Wertebereichs; dagegen stehen die 192 Fachen,
#: die die Lücken-Trennung überhaupt erst einbringt.
#:
#: **Gesetzt und nicht kalibriert**, aber die Richtung ist zwingend: Irgendein Wert echt
#: über null muss es sein, sonst ist die Geometrie weg.
GEKLEMMT_MINDESTGRAU = 1.0 / 255.0

#: Ab welchem Faktor die Lücken-Messung einen Satz in ``warnungen`` wert ist.
#:
#: Verglichen wird, wie breit der Wertebereich **jetzt** ist (``max_m - min_m``) und wie
#: breit er mit der Lücken-Obergrenze **wäre** (``max_m_luecke - min_m``). Der Quotient
#: sagt, um welchen Faktor der Kern — also das Bauwerk — an Auflösung gewänne.
#:
#: **Der Faktor kann nie unter 3 liegen, und das bestimmt die Schwelle mit.** Eine Lücke
#: gilt erst ab Verhältnis 3 (``geometrie_qa.MINDEST_LUECKEN_VERHAELTNIS``); der nächste
#: Wert über der Obergrenze liegt also mindestens beim Dreifachen, und das grösste Mass
#: liegt nochmals darüber. Aus ``faktor = (max_m - min_m) / (obergrenze - min_m)`` mit
#: ``max_m ≥ 3 · obergrenze`` und ``0 < min_m < obergrenze`` folgt ``faktor > 3`` — immer.
#: Eine Schwelle bei 2 wäre darum ein Wächter, der nie schweigt und deshalb nichts sagt.
#:
#: **Warum 10.0.** Der reproduzierte Fall vom 11.09.2026 ergibt 193.7 (Wertebereich
#: 1598.25 m gegen 8.25 m) — der Kern bekommt ein halbes Prozent des Wertebereichs, und
#: genau das war die flachgedrückte Karte. Der kleinstmögliche Fall liegt knapp über 3;
#: dort hat der Kern noch ein Drittel des Bereichs, und ein Satz darüber wäre eine Meldung
#: über den Normalfall. 10 heisst: Der Kern nutzt weniger als ein Zehntel — bei 8 Bit sind
#: das unter 26 von 255 Graustufen für das ganze Bauwerk.
#:
#: **Diese Schwelle ist GESETZT und nicht kalibriert.** Geprüft ist sie an zwei Punkten
#: (193.7 meldet, 3.33 schweigt), nicht an einer Messreihe über mehrere Räume eingestellt.
LUECKE_WARNT_AB_FAKTOR = 10.0


class SchreibError(ValueError):
    """Es lässt sich kein sinnvolles Bild aus diesen Daten schreiben."""


# ── PNG ───────────────────────────────────────────────────────────────────────────────

def _block(art: bytes, nutzlast: bytes) -> bytes:
    """Ein PNG-Block: Länge, Kennung, Nutzlast, CRC32 über Kennung **und** Nutzlast."""
    return (struct.pack(">I", len(nutzlast)) + art + nutzlast
            + struct.pack(">I", zlib.crc32(art + nutzlast) & 0xFFFFFFFF))


def _paeth(a: int, b: int, c: int) -> int:
    """Der Paeth-Prädiktor der PNG-Spezifikation (links, oben, oben-links)."""
    p = a + b - c
    pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
    if pa <= pb and pa <= pc:
        return a
    return b if pb <= pc else c


def _zeile_filtern(zeile: bytes, vorige: bytes, bpp: int) -> bytes:
    """Eine Bildzeile filtern — und zwar in der Art, die sie am kleinsten macht.

    PNG erlaubt je Zeile einen von fünf Filtern. Welcher der beste ist, hängt vom Inhalt
    ab; die Spezifikation empfiehlt dafür die Summe der absoluten Abweichungen als
    Schätzer (der „minimum sum of absolute differences"-Heuristik von libpng). Genau die
    steht hier.

    Der Nutzen ist nicht nur Plattenplatz: Ein Schreiber, der alle fünf Filter benutzt,
    prüft nebenbei den Entfilterer in :mod:`aiimaging.bildlesen` an echten Daten — die
    Tests lesen zurück, was hier entsteht.
    """
    kandidaten = []

    # 0 — None
    kandidaten.append((0, bytes(zeile)))
    # 1 — Sub: Differenz zum linken Nachbarn
    sub = bytearray(len(zeile))
    for i, wert in enumerate(zeile):
        links = zeile[i - bpp] if i >= bpp else 0
        sub[i] = (wert - links) & 0xFF
    kandidaten.append((1, bytes(sub)))
    # 2 — Up: Differenz zur Zeile darüber
    up = bytearray(len(zeile))
    for i, wert in enumerate(zeile):
        up[i] = (wert - vorige[i]) & 0xFF
    kandidaten.append((2, bytes(up)))
    # 3 — Average
    avg = bytearray(len(zeile))
    for i, wert in enumerate(zeile):
        links = zeile[i - bpp] if i >= bpp else 0
        avg[i] = (wert - ((links + vorige[i]) >> 1)) & 0xFF
    kandidaten.append((3, bytes(avg)))
    # 4 — Paeth
    pae = bytearray(len(zeile))
    for i, wert in enumerate(zeile):
        links = zeile[i - bpp] if i >= bpp else 0
        oben_links = vorige[i - bpp] if i >= bpp else 0
        pae[i] = (wert - _paeth(links, vorige[i], oben_links)) & 0xFF
    kandidaten.append((4, bytes(pae)))

    # Die Heuristik liest die Bytes als **vorzeichenbehaftet**: Ein Wert von 255 ist als
    # -1 zu verstehen und damit eine kleine Abweichung, keine grosse.
    def kosten(daten: bytes) -> int:
        return sum(b if b < 128 else 256 - b for b in daten)

    art, daten = min(kandidaten, key=lambda k: kosten(k[1]))
    return bytes([art]) + daten


def schreibe_graustufen_png(ziel, werte: Sequence[float], breite: int, hoehe: int, *,
                            bittiefe: int = 16) -> Path:
    """Grauwerte 0..1 → Graustufen-PNG. Reine stdlib.

    Args:
        werte: ``breite * hoehe`` Werte in 0..1, zeilenweise von **oben** nach unten —
            also in derselben Reihenfolge, in der
            :func:`aiimaging.bildlesen.lies_png_graustufen` sie zurückgibt. Werte
            ausserhalb 0..1 werden beschnitten, statt einen Fehler zu werfen: Sie
            entstehen bei Rundung an den Rändern, und ein Abbruch dafür wäre eine
            Strenge ohne Nutzen. **``inf`` zählt dazu** — es ist der Grenzfall von
            „ausserhalb" und wird auf Weiss bzw. Schwarz beschnitten. Das ist kein
            Kuriosum: :func:`aiimaging.bildlesen.tiefen_aus_png` gibt für jeden
            Hintergrundpunkt genau ``inf`` zurück, wer eine gelesene Karte
            zurückschreibt trifft es sofort.

            ``nan`` dagegen ist **kein** Randfall von „zu gross", sondern *kein Wert*.
            Es zu beschneiden hiesse zu entscheiden, ob ein Loch in den Daten schwarz
            oder weiss ist — und diese Entscheidung gehört dem Aufrufer, nicht dem
            Schreiber. Darum ein :class:`SchreibError` mit der Fundstelle.
        bittiefe: 16 (Vorgabe) oder 8. 16 ist die Vorgabe, weil 8 Bit eine 30 m tiefe
            Szene in 12-cm-Stufen zerlegt — sichtbare Terrassen auf jeder schrägen Fläche.

    Returns:
        Den geschriebenen Pfad.

    Raises:
        SchreibError: Masse und Wertezahl passen nicht zusammen, die Bittiefe ist weder
            8 noch 16, oder ein Wert ist ``nan``.
    """
    ziel = Path(ziel)
    if bittiefe not in (8, 16):
        raise SchreibError(f"bittiefe: 8 oder 16 erwartet, war {bittiefe!r}.")
    if breite <= 0 or hoehe <= 0:
        raise SchreibError(f"Masse müssen positiv sein, waren {breite}×{hoehe}.")
    if len(werte) != breite * hoehe:
        raise SchreibError(
            f"{len(werte)} Werte für {breite}×{hoehe} = {breite * hoehe} Bildpunkte. "
            f"Ein Bild mit fehlenden Werten wäre stillschweigend verschoben."
        )

    hoechst = (1 << bittiefe) - 1
    bpp = bittiefe // 8

    roh = bytearray()
    vorige = bytes(breite * bpp)
    for y in range(hoehe):
        zeile = bytearray()
        for x in range(breite):
            i = y * breite + x
            v = werte[i]
            if v != v:                                   # nan — der einzige Wert, der
                raise SchreibError(                      # sich selbst ungleich ist
                    f"Wert an Stelle {i} (Zeile {y}, Spalte {x}) ist nan. Das ist kein "
                    f"Grauwert ausserhalb des Bereichs, sondern gar keiner — und ob ein "
                    f"Loch in den Daten schwarz oder weiss werden soll, kann nur der "
                    f"Aufrufer entscheiden. Wer Hintergrund meint, schreibt 0.0."
                )
            # `inf` vor der Multiplikation abfangen: `int(round(inf))` wirft
            # OverflowError statt zu beschneiden. Unendlich ist hier der Grenzfall von
            # „ausserhalb 0..1" und bekommt darum dieselbe Regel wie 1e9 oder -3.
            if v == float("inf"):
                n = hoechst
            elif v == float("-inf"):
                n = 0
            else:
                n = int(round(v * hoechst))
                n = 0 if n < 0 else (hoechst if n > hoechst else n)
            zeile += struct.pack(">H", n) if bittiefe == 16 else bytes([n])
        zeile = bytes(zeile)
        roh += _zeile_filtern(zeile, vorige, bpp)
        vorige = zeile

    ihdr = struct.pack(">IIBBBBB", breite, hoehe, bittiefe, 0, 0, 0, 0)
    ziel.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + _block(b"IHDR", ihdr)
        + _block(b"IDAT", zlib.compress(bytes(roh), 6))
        + _block(b"IEND", b"")
    )
    return ziel


def schreibe_farb_png(ziel, farben: Sequence[Sequence[int]], breite: int,
                      hoehe: int) -> Path:
    """``(r, g, b)``-Tripel in 0..255 → 8-Bit-RGB-PNG. Reine stdlib.

    Das Gegenstück zu :func:`aiimaging.bildlesen.lies_png_farben`, und aus demselben
    Grund gebaut: Ein **Material-ID-Pass** trägt Kennfarben, keine Helligkeiten. Ohne
    einen Schreiber dafür wäre ``aiimaging.maske`` nur mit Blender prüfbar — also mit
    GPU, GPL-Prozess und Minuten je Lauf. Ein Modul, das sich nur mit dem Werkzeug
    prüfen lässt, dessen Ausgabe es liest, ist nicht geprüft, sondern nur benutzt.

    **Warum 8 Bit ohne Wahlmöglichkeit.** Der Multipass schreibt den Material-ID-Pass
    fest mit ``color_depth = "8"``, und die Zuordnung Farbe → Material vergleicht Byte
    für Byte. Eine 16-Bit-Fassung wäre eine Datei, die es in dieser Kette nicht gibt —
    und der Leser lehnt sie mit Begründung ab. Ein Schalter dafür wäre ein Schalter für
    einen Fehlerfall.

    **Warum Ganzzahlen und keine Anteile.** Aus ``0.15`` wird über ``round(0.15 * 255)``
    der Wert 38; aus ``38/255`` wieder 0.15. Das trifft — aber es lädt dazu ein, eine
    Kennfarbe zu skalieren, und eine skalierte Kennung kennzeichnet nichts mehr. Wer
    Grauwerte in 0..1 schreiben will, nimmt :func:`schreibe_graustufen_png`.

    Args:
        farben: ``breite * hoehe`` Tripel ``(r, g, b)`` mit ganzen Zahlen in 0..255,
            zeilenweise von **oben** nach unten — dieselbe Reihenfolge, die
            :func:`aiimaging.bildlesen.lies_png_farben` zurückgibt.
        breite, hoehe: Bildmasse.

    Returns:
        Den geschriebenen Pfad.

    Raises:
        SchreibError: Masse und Anzahl passen nicht zusammen, ein Eintrag hat nicht
            genau drei Werte, oder ein Wert liegt ausserhalb 0..255. Anders als bei
            :func:`schreibe_graustufen_png` wird hier **nicht** beschnitten: Ein Grauwert
            über 1.0 ist ein Rundungsrest, ein Farbwert über 255 ist ein Denkfehler in
            der Palette — und aus 256 stillschweigend 255 zu machen erzeugte zwei
            Materialien mit derselben Kennfarbe.
    """
    ziel = Path(ziel)
    if breite <= 0 or hoehe <= 0:
        raise SchreibError(f"Masse müssen positiv sein, waren {breite}×{hoehe}.")
    if len(farben) != breite * hoehe:
        raise SchreibError(
            f"{len(farben)} Farben für {breite}×{hoehe} = {breite * hoehe} Bildpunkte. "
            f"Ein Bild mit fehlenden Werten wäre stillschweigend verschoben."
        )

    roh = bytearray()
    vorige = bytes(breite * 3)
    for y in range(hoehe):
        zeile = bytearray()
        for x in range(breite):
            i = y * breite + x
            farbe = farben[i]
            if len(farbe) != 3:
                raise SchreibError(
                    f"Farbe an Stelle {i} (Zeile {y}, Spalte {x}) hat {len(farbe)} statt "
                    f"3 Werte. Erwartet wird (r, g, b); ein Alphakanal gehört nicht in "
                    f"eine Kennfarbe."
                )
            for kanal in farbe:
                if not isinstance(kanal, int) or isinstance(kanal, bool) \
                        or not 0 <= kanal <= 255:
                    raise SchreibError(
                        f"Farbe an Stelle {i} (Zeile {y}, Spalte {x}) ist {tuple(farbe)!r}. "
                        f"Erwartet werden ganze Zahlen in 0..255."
                    )
                zeile.append(kanal)
        zeile = bytes(zeile)
        roh += _zeile_filtern(zeile, vorige, 3)
        vorige = zeile

    ihdr = struct.pack(">IIBBBBB", breite, hoehe, 8, 2, 0, 0, 0)
    ziel.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + _block(b"IHDR", ihdr)
        + _block(b"IDAT", zlib.compress(bytes(roh), 6))
        + _block(b"IEND", b"")
    )
    return ziel


# ── Normalisierung ────────────────────────────────────────────────────────────────────

def _luecke_messen(tiefe: Sequence[float],
                   hintergrund_ab_m: float) -> tuple[dict | None, str | None]:
    """Die Lücken-Messung, so verpackt, dass sie die Normierung **nie** umwerfen kann.

    Zurück kommt ``(befund, fehlersatz)``. Genau eines von beiden ist ``None``.

    Warum das Abfangen: Die Messung ist eine Zugabe, die Normierung ist der Auftrag. Eine
    Zugabe, die den Auftrag scheitern lässt, ist keine. ``ferne_abtrennen`` prüft seine
    Eingabe strenger als diese Funktion (Wahrheitswerte, Zahlen in Textform, eine
    unbrauchbare Schranke) — wo es abbricht, steht hinterher **NICHT GEMESSEN** und ein
    Satz, der sagt warum, und nicht ein Abbruch des ganzen Schreibwegs.
    """
    from aiimaging import geometrie_qa      # lokal wie in `tiefe_exr_zu_png`, siehe dort

    try:
        befund = geometrie_qa.ferne_abtrennen(tiefe, hintergrund_grenze=hintergrund_ab_m)
    except Exception as e:                   # Befund als Feld, nicht als Absturz
        return None, (
            f"Die Lücken-Messung ist nicht gelaufen ({type(e).__name__}: {e}) — die "
            f"Obergrenze aus der Lücke ist NICHT GEMESSEN. Die Normierung darunter ist "
            f"davon unberührt; sie hat diese Zahl nie benutzt."
        )
    # `kanten` kommt als Tupel. Das Ergebnis landet über `tiefe_exr_zu_png` im Report und
    # damit in JSON, wo aus einem Tupel beim Zurücklesen eine Liste wird. Wer die Datei
    # mit dem Speicherabbild vergleicht, sähe sonst einen Unterschied, den es nicht gibt.
    bericht = dict(befund)
    bericht["kanten"] = list(befund["kanten"])
    bericht["warnungen"] = list(befund["warnungen"])
    return bericht, None


def normalisiere_tiefe(tiefe: Sequence[float], *,
                       hintergrund_ab_m: float = HINTERGRUND_AB_M,
                       ferne_trennen: bool = False) -> tuple[list[float], dict]:
    """Meterwerte → Grauwerte 0..1 (*nah = hell*) plus die Angaben zur Rückrechnung.

    Warum nicht Blenders ``Normalize``-Knoten
    -----------------------------------------
    Er normalisiert über **alle** Bildpunkte, also auch über den Hintergrund mit seinen
    ~1e10 Metern. Das Gebäude landete dann in den untersten Promille des Wertebereichs
    und wäre gleichmässig schwarz. Deshalb wird hier mit einer ausdrücklichen
    Hintergrundschranke gerechnet.

    Warum die Schranke allein nicht reicht — reproduziert am 16.09.2026
    -------------------------------------------------------------------
    Die HomeStation meldete am 11.09.2026 eine flachgedrückte Tiefenkarte (Mittel 0.9869,
    98.7 % der Punkte über 0.99) und hielt das für einen Fehler ihrer eigenen Normierung
    über ein 99er-Perzentil. Es ist **diese** Normierung hier. An der gemeldeten Verteilung
    nachgerechnet — Innenraum 1.75 bis 10 m mit 2000 Punkten, dazu 23 Punkte einer
    Fernsichtebene bei 1600 m::

        max_m = 1600.0, min_m = 1.75
        Mittel über dem Innenraum: 0.9974
        Anteil aller Punkte über 0.99: 0.989

    Der Grund: ``max_m`` ist das grösste gültige Mass unterhalb von ``hintergrund_ab_m``
    (1e7). Eine Fernsichtebene bei 1600 m liegt weit darunter, gilt also als Geometrie und
    frisst den ganzen Wertebereich. Die feste Schranke löst nur den **extremen** Fall
    (Cycles' ~1e10 für Strahlen ins Leere); sie setzt genau wie ein festes Perzentil
    voraus, dass man vorher weiss, wo die Ferne anfängt. Weiss man nicht — das weiss nur
    das Bild.

    Die Messung läuft immer, das Verhalten ist aus
    -----------------------------------------------
    ``normalisierung`` trägt darum in **jeder** geschriebenen Karte, wie sie ausgesehen
    hätte: ``max_m_luecke`` (die Obergrenze aus der eigenen Lücke der Verteilung, siehe
    :func:`aiimaging.geometrie_qa.ferne_abtrennen`), ``luecke`` (der ganze Befund) und
    ``ferne_getrennt`` (ob wirklich danach normiert wurde). Ohne diese Zahl kann niemand
    entscheiden, ob der Schalter umgelegt werden soll — und wer zuerst umlegt, verliert
    die Messung, mit der er es hätte begründen können.

    Args:
        ferne_trennen: Ob ``max_m`` die Lücken-Obergrenze wird statt das grösste gültige
            Mass. **Vorgabe ist AUS.** Das ist keine Vorsicht, sondern eine Hausregel:
            Die HomeStation führt unseren Code aus diesem Repo aus, ein ``git pull`` dort
            ändert sonst still, was gerechnet wird. Eine Verhaltensänderung wird angesagt,
            BEVOR sie ankommt — sonst sieht sie drüben wie ein Fehler aus.

            Ist der Schalter an und eine Lücke gemessen, wird alles darüber **geklemmt**
            und nicht zu Hintergrund gemacht: Es *ist* Geometrie, nur zu weit weg, um
            Auflösung zu verdienen. Findet die Messung **keine** Lücke, bleibt alles wie
            bisher — NICHT GEMESSEN darf nie zu einer erfundenen Grenze werden.

    Returns:
        ``(grau, normalisierung)``. Ohne ``min_m``/``max_m`` in ``normalisierung`` ist
        das PNG nicht mehr in Meter zurückzurechnen — und genau das braucht die
        Geometrie-QA.

    Raises:
        SchreibError: kein einziger Geometriepixel. Das ist kein Randfall, sondern heisst,
            dass die Kamera nichts sieht — und darüber schweigend ein schwarzes Bild zu
            schreiben wäre die teuerste Art, es zu erfahren.
    """
    gueltig = [i for i, t in enumerate(tiefe)
               if t == t and t not in (float("inf"), float("-inf"))
               and 0.0 < t < hintergrund_ab_m]
    if not gueltig:
        raise SchreibError(
            f"Tiefenbild enthält keinen einzigen Geometriepixel "
            f"(alle {len(tiefe)} Werte sind ≤ 0, nicht endlich oder ≥ {hintergrund_ab_m:g} m). "
            f"Prüfe Kamera und Szene, nicht die Schranke."
        )

    min_m = min(tiefe[i] for i in gueltig)
    max_m_gemessen = max(tiefe[i] for i in gueltig)

    warnungen: list[str] = []
    luecke, fehlersatz = _luecke_messen(tiefe, hintergrund_ab_m)
    if fehlersatz:
        warnungen.append(fehlersatz)
    max_m_luecke = luecke["obergrenze"] if luecke else None

    # ── Umschalten oder nicht, und in beiden Fällen: warum ───────────────────────────
    max_m = max_m_gemessen
    ferne_getrennt = False
    if max_m_luecke is None:
        if ferne_trennen:
            # Der Schalter ist an und es passiert trotzdem nichts. Das gehört gesagt:
            # Ein Aufruf, der wirkungslos bleibt und schweigt, sieht aus wie einer, der
            # gewirkt hat.
            warnungen.append(
                "ferne_trennen ist gesetzt, aber es wurde KEINE taugliche Lücke gemessen "
                "— normiert wurde wie bisher über das grösste gültige Mass. NICHT "
                "GEMESSEN wird hier nicht zu einer erfundenen Grenze.")
    # Eine Vertragsprüfung an `ferne_abtrennen`: Die Obergrenze ist dort die UNTERE Kante
    # einer Lücke, über der noch mindestens ein Wert liegt — sie ist also immer kleiner als
    # das grösste Mass. Trifft das einmal nicht mehr zu, wird hier nichts umgeschaltet,
    # statt eine Skala zu bauen, die niemand gemeint hat. Der `else`-Zweig darunter ist der
    # Grund, warum das eine Prüfung mit Stimme ist und nicht bloss ein stilles `elif`.
    elif max_m_luecke < max_m_gemessen:
        # Die Lücke liegt auf dem KLEINSTEN Wert: Der Kern hätte keine Breite mehr, alle
        # Geometrie bekäme denselben Grauwert. Das ist eine Maske und keine Tiefenkarte —
        # dieselbe Regel wie bei „keine Lücke gefunden": lieber die alte Skala als eine
        # Grenze, die nichts mehr trennt. Derselbe Zweig hält auch die Division im
        # Warnzweig darunter von der Null fern; die Mutationsprobe M7 (16.09.2026) hat
        # genau das gezeigt, indem sie eine ZeroDivisionError über zwei Punkten erzeugte.
        if max_m_luecke <= min_m:
            warnungen.append(
                f"Die Lücke liegt bei {max_m_luecke:g} m und damit auf dem nächsten Punkt "
                f"({min_m:g} m) — der Kern hätte keine Breite mehr und jede Geometrie "
                f"denselben Grauwert. NICHT umgeschaltet, auch wenn ferne_trennen gesetzt "
                f"ist.")
        elif ferne_trennen:
            max_m = max_m_luecke
            ferne_getrennt = True
        else:
            # GESETZTE Schwelle, siehe `LUECKE_WARNT_AB_FAKTOR`. Der Satz nennt beide
            # Zahlen, damit die Entscheidung ohne einen zweiten Lauf zu treffen ist.
            faktor = (max_m_gemessen - min_m) / (max_m_luecke - min_m)
            if faktor >= LUECKE_WARNT_AB_FAKTOR:
                warnungen.append(
                    f"Normiert wurde über max_m = {max_m_gemessen:g} m; die eigene Lücke "
                    f"der Verteilung liegt bei {max_m_luecke:g} m. Der Kern bekäme damit "
                    f"den {faktor:.4g}-fachen Wertebereich. NICHT umgeschaltet — "
                    f"ferne_trennen ist aus, und das bleibt es, bis es angesagt ist. Die "
                    f"Schwelle für diesen Satz (Faktor {LUECKE_WARNT_AB_FAKTOR:g}) ist "
                    f"gesetzt und nicht kalibriert.")
    else:
        # Der Vertrag von `ferne_abtrennen` ist gebrochen: gemessen wurde eine Obergrenze,
        # die NICHT unter dem grössten gültigen Mass liegt. Umgeschaltet wird darum nicht —
        # aber geschwiegen wird auch nicht. Bis zur Prüfung vom 16.09.2026 fiel dieser Fall
        # stumm durch: `max_m_luecke` stand als Zahl im Bericht, `ferne_getrennt` auf False,
        # und in `warnungen` nichts. Wer den Schalter gesetzt hatte, sah einen wirkungslosen
        # Aufruf, der wie ein wirksamer aussah — derselbe Fehlschlag, gegen den der Satz im
        # Zweig „keine Lücke gemessen" geschrieben ist, nur eine Verzweigung weiter.
        warnungen.append(
            f"Die Lücken-Messung meldet die Obergrenze {max_m_luecke:g} m, und die liegt "
            f"NICHT unter dem grössten gültigen Mass ({max_m_gemessen:g} m). Damit ist die "
            f"Zusage von ferne_abtrennen verletzt (die Obergrenze ist dort die untere Kante "
            f"einer Lücke, über der noch etwas liegt). NICHT umgeschaltet — eine Skala aus "
            f"einer Zahl zu bauen, die so nicht gemeint sein kann, wäre schlimmer als die "
            f"alte Skala.")

    spanne = (max_m - min_m) or 1.0          # eine ebene Fläche frontal: Spanne 0

    grau = [HINTERGRUND_GRAUWERT] * len(tiefe)
    n_geklemmt = 0
    for i in gueltig:
        t = tiefe[i]
        if ferne_getrennt and t > max_m:
            # GEKLEMMT, nicht ausgeblendet: Der Punkt bleibt Geometrie und zählt in
            # `n_geometriepixel` mit; er verliert nur seine Auflösung.
            #
            # Geklemmt wird auf den DUNKELSTEN Wert und nicht auf den hellsten. „nah =
            # hell" heisst: Was weiter weg ist, wird dunkler, und die Fernsichtebene ist
            # das Fernste im Bild. Auf 1.0 zu klemmen gäbe ihr den Grauwert des NÄCHSTEN
            # Punktes und drehte die Tiefenordnung für diese Punkte um — genau der Fehler,
            # gegen den die Konvention geschrieben ist (die Rangkorrelation der
            # Geometrie-QA meldete dann −1 auf korrekter Geometrie).
            t = max_m
            n_geklemmt += 1
        # nah = hell (ControlNet-Konvention). Der Hintergrund bleibt 0.0 — unendlich fern
        # ist der Grenzfall von „dunkel", nicht ein eigener Sonderfall.
        wert = 1.0 - (t - min_m) / spanne
        if ferne_getrennt:
            # DER BODEN, UND ER GILT FUER ALLE GEOMETRIE DIESES LAUFS, nicht nur fuer die
            # geklemmten Punkte. Zoege man ihn nur bei den geklemmten hoch, waeren sie
            # HELLER als die echten hintersten Punkte — die Tiefenordnung stuende auf dem
            # Kopf, und zwar genau bei den Punkten, die am weitesten weg sind. Ein Boden
            # fuer alle verschiebt die Ordnung nicht, er staucht sie um einen halben
            # 8-Bit-Schritt. Siehe GEKLEMMT_MINDESTGRAU.
            #
            # NUR im eingeschalteten Fall: Mit ausgeschaltetem Schalter bleibt die
            # Rechnung Bit fuer Bit die von vorher. Die HomeStation faehrt diesen Code
            # aus unserem Repo — was sie nicht bestellt hat, aendert sich nicht.
            wert = GEKLEMMT_MINDESTGRAU + wert * (1.0 - GEKLEMMT_MINDESTGRAU)
        grau[i] = wert

    # ── Die gefährlichste Stelle: Wer Meter zurückrechnet, muss das Klemmen sehen ─────
    #
    # RUECKRECHNUNG bleibt WÖRTLICH gültig — die Formel ist dieselbe, und `max_m` ist
    # weiterhin die Zahl, gegen die normiert wurde. Was sich ändert, ist die BEDEUTUNG des
    # Ergebnisses für die geklemmten Punkte: Sie tragen Grauwert 0 und ergeben
    # zurückgerechnet genau `max_m` Meter. Das ist eine UNTERGRENZE ihrer Entfernung und
    # keine Messung. `max_m` allein verrät das nicht; darum stehen drei Felder daneben:
    #
    #   geklemmt_ab_m   ab welcher Entfernung abgeschnitten wurde (None = gar nicht)
    #   n_geklemmt      wie viele Punkte es trifft
    #   max_m_gemessen  wie weit sie tatsächlich reichen — die Zahl geht NICHT verloren
    #
    # Dazu ein Satz im Klartext in `rueckrechnung_vorbehalt`, weil ein fremder Auswerter
    # `rueckrechnung` liest und nicht diesen Kommentar. Ohne ihn hielte er geklemmte
    # Punkte für echte Messwerte an der Grenze — ein Fehlschlag, der wie ein Erfolg
    # aussieht.
    vorbehalt = None
    if ferne_getrennt:
        vorbehalt = (
            f"ACHTUNG: {n_geklemmt} von {len(gueltig)} Geometriepunkten wurden bei "
            f"{max_m:g} m abgeschnitten (ferne_trennen). Die Formel in `rueckrechnung` "
            f"gilt unverändert, aber für diese Punkte liefert sie {max_m:g} m als "
            f"UNTERGRENZE und nicht als Messwert — tatsächlich reichen sie bis "
            f"{max_m_gemessen:g} m. Sie tragen Grauwert 0 und sind im PNG weder "
            f"untereinander noch vom Hintergrund zu unterscheiden; wer echte Entfernungen "
            f"braucht, nimmt die EXR."
        )

    return grau, {
        "min_m": float(min_m),
        "max_m": float(max_m),
        "konvention": KONVENTION,
        "hintergrund_grauwert": HINTERGRUND_GRAUWERT,
        # DIE FORMEL, UND SIE IST IM EINGESCHALTETEN FALL EINE ANDERE. Der Boden unter
        # der Geometrie (GEKLEMMT_MINDESTGRAU) staucht die Skala; wer weiter mit der
        # alten Formel raeumt, bekommt jeden Punkt um bis zu einen halben 8-Bit-Schritt
        # zu weit nach hinten. Das ist wenig — und genau darum gefaehrlich: Es faellt
        # niemandem auf. Ein Feld, das in zwei Faellen dasselbe sagt und zwei
        # verschiedene Dinge meint, ist schlimmer als zwei Felder.
        "rueckrechnung": (RUECKRECHNUNG if not ferne_getrennt else
                          "meter = max_m - (grau - boden) / (1 - boden) * (max_m - min_m), "
                          "grau in boden..1, boden = geklemmt_mindestgrau"),
        "geklemmt_mindestgrau": GEKLEMMT_MINDESTGRAU if ferne_getrennt else None,
        "n_geometriepixel": len(gueltig),
        # Wer den Wert später anders setzt, soll in der Datei sehen, wogegen gemessen
        # wurde — die Schranke bestimmt min_m und max_m mit.
        "hintergrund_ab_m": float(hintergrund_ab_m),
        "quelle": "produkt",
        # Die Messung, die IMMER läuft — auch wenn der Schalter aus ist.
        "max_m_luecke": None if max_m_luecke is None else float(max_m_luecke),
        "luecke": luecke,
        "ferne_getrennt": ferne_getrennt,
        # Was das Klemmen für die Rückrechnung heisst. `max_m_gemessen` steht immer da,
        # auch ungeklemmt — dann ist es dasselbe wie `max_m`, und genau das darf man sehen.
        "geklemmt_ab_m": float(max_m) if ferne_getrennt else None,
        "n_geklemmt": n_geklemmt,
        "max_m_gemessen": float(max_m_gemessen),
        "rueckrechnung_vorbehalt": vorbehalt,
        "warnungen": warnungen,
    }


def tiefe_exr_zu_png(exr, ziel_png, *, hintergrund_ab_m: float = HINTERGRUND_AB_M,
                     bittiefe: int = 16, ferne_trennen: bool = False,
                     timeout: int = 300, _leser=None, _starte=None) -> dict:
    """EXR in Metern → normalisiertes Graustufen-PNG. Der ganze Weg, ohne Blender.

    Das ist die Stelle, die :func:`aiimaging.seams.glb_zu_multipass` nach dem Blender-Lauf
    aufruft. Sie ersetzt den Schritt, der bis zum 18.08.2026 im Runner stand.

    Args:
        ferne_trennen: **Nur durchgereicht, Vorgabe AUS** — siehe
            :func:`normalisiere_tiefe`. Ohne dieses Argument wäre der Schalter von der
            Kette aus gar nicht erreichbar, also ein Schalter ohne Draht. Die Messung
            (``max_m_luecke``, ``luecke``, ``ferne_getrennt``) steht ohnehin in jedem
            zurückgegebenen Bericht und damit in jedem Report.
        timeout, _starte: **Die Prozessgrenze, die hier versteckt liegt.** Die Vorgabe
            :func:`aiimaging.bildlesen.lies_exr_tiefe` liest zuerst mit der stdlib und
            fällt bei EXR-Spielarten, die sie nicht kann (PIZ, DWAA/B, B44, PXR24,
            gekachelt, mehrteilig), auf ``blender --background`` zurück. Ein
            adversarialer Prüfer hat das am 18.08.2026 nachgewiesen: Ohne diese beiden
            Argumente startete ``seams.glb_zu_multipass`` einen zweiten Blender-Prozess
            **ohne injizierbare Naht und mit fremdem Zeitlimit** (300 s statt der 900 s
            des Aufrufers) — die einzige Prozessgrenze des Projekts ohne Naht, gegen das
            Muster von ``seams._starte``, ``bildlesen._starte`` und ``render.modell``.
        _leser: Naht für Tests — eine Funktion ``pfad -> (werte, breite, hoehe)``.
            Wer sie setzt, umgeht ``timeout`` und ``_starte`` mitsamt dem Rückfall.

    Returns:
        Das ``depth_normalisierung``-Dictionary, ergänzt um ``breite`` und ``hoehe``.

    Hinweis zum Rückfall: Er geht ausgerechnet über ``bpy.data.images.load`` — den
    Leseweg, dessen Bruch auf Blender 5.x der Anlass dieses ganzen Moduls war. Auf 5.x
    hilft er also nicht; er bleibt für 4.x und für exotische Kompressionen.
    """
    from aiimaging import bildlesen

    if _leser is not None:
        werte, breite, hoehe = _leser(Path(exr))
    else:
        werte, breite, hoehe = bildlesen.lies_exr_tiefe(
            Path(exr), timeout=timeout, _starte=_starte)
    grau, normalisierung = normalisiere_tiefe(
        werte, hintergrund_ab_m=hintergrund_ab_m, ferne_trennen=ferne_trennen)
    schreibe_graustufen_png(ziel_png, grau, breite, hoehe, bittiefe=bittiefe)
    normalisierung["breite"] = breite
    normalisierung["hoehe"] = hoehe
    normalisierung["bittiefe"] = bittiefe
    return normalisierung


__all__ = [
    "GEKLEMMT_MINDESTGRAU", "HINTERGRUND_AB_M", "HINTERGRUND_GRAUWERT", "KONVENTION",
    "RUECKRECHNUNG",
    "LUECKE_WARNT_AB_FAKTOR",
    "SchreibError",
    "normalisiere_tiefe", "schreibe_farb_png", "schreibe_graustufen_png",
    "tiefe_exr_zu_png",
    "MIN_KANTE_FASSUNG",
    "base64_zeichen", "bildgroesse", "kleinere_fassung", "passt_unter",
]


# ======================================================================================
# Kontrollbilder — was ein Bild OHNE Geometrie auf derselben Soll-Karte erreicht
# ======================================================================================

#: Die Kontrollbilder, die eine Nullprobe ausmachen.
#:
#: **Warum es sie gibt.** Am 20.08.2026 hat die HomeStation ungefragt vier Bilder durch
#: die Geometrie-QA geschickt, die *nicht* aus dem Bildmodell stammten
#: (`auf-20260820-21`). Ergebnis: **Weisses Rauschen erreichte 0.7217 und bestand damit
#: das Gate von 0.65** — mehr als jeder der fünf echten Läufe derselben Messung.
#:
#: Der Grund liegt nicht am Rauschen: Ein monokularer Schätzer legt in *jedes* Bild eine
#: zum Horizont laufende Bodenebene, und eine Szene mit viel Boden **ist** so eine Rampe.
#:
#:     Ein Score sagt erst etwas, wenn danebensteht, was **nichts** erreicht.
#:
#: Dieselbe Medizin, die ``stil_qa`` seit dem 18.08. nimmt.
KONTROLLARTEN = ("rauschen", "grau", "verlauf")

#: Fester Startwert für das Rauschen. **Eine Nullprobe, die bei jedem Aufruf anders
#: ausfällt, ist keine** — der Anker wäre dann selbst eine Zufallsgrösse, und ein Score
#: liesse sich nicht zweimal gleich einordnen.
KONTROLL_SEED = 20260820



# ── Wie gross ist das Bild? ───────────────────────────────────────────────────────────
#
# GEMESSEN AM 03.09.2026, ENTSCHIEDEN AM 04.09.2026. Bis gestern stand hier ein DECKEL:
# 1 048 576, abgeschrieben vom Tor in KosmoOrbit (`vis-jobs.ts`). Er hat die Demolaeufe
# 15 und 17 gestoppt, indem der Knopf «Aufs Blatt» das Regelergebnis der eigenen Kette
# abwies.
#
# WARUM ER GEFALLEN IST. Drei Messungen, keine Meinung:
#
#   * DER DECKEL HIESS 1.0 MB UND WAR 0.79 MB. Verglichen wurden Base64-ZEICHEN,
#     umgerechnet und gemeldet wurden ROHBYTES. 1 048 576 Zeichen sind 786 432 Byte —
#     0.75 MiB, also 0.79 MB. Wer der Meldung folgte und auf «knapp unter 1.0 MB»
#     verkleinerte, wurde ein zweites Mal abgewiesen: 1 000 000 Byte ergeben 1 333 336
#     Zeichen und reissen den Deckel um 27 %.
#   * 60 VON 66 NUTZBILDERN dieser Kette lagen darueber, Median 1 277 231 Byte gegen
#     786 432. Die Ablehnung war der Normalfall, nicht der Ausreisser — eine Kette,
#     deren Regelausgabe die eigene naechste Stufe zu 91 % abweist, hat kein Bildproblem,
#     sondern ein Grenzproblem.
#   * EIN TECHNISCHER GRUND fuer genau diese Zahl war nirgends auffindbar.
#
# Owner-Entscheid vom 04.09.2026: «Deckel weg.» Das Tor faellt drueben in seiner Lane,
# diese Seite zieht nach.
#
# WAS FAELLT UND WAS BLEIBT — die Unterscheidung ist der ganze Punkt:
#
#   FAELLT: der ZWANG. Es gibt keinen Vorgabewert mehr, unter den irgendetwas
#           verkleinert wird, und der Abholer legt keine kleinere Kopie mehr an, um die
#           ihn niemand gebeten hat. `passt_aufs_blatt` heisst nicht mehr so, weil das
#           Blatt nichts mehr zurueckweist: Eine Funktion, die `False` sagen kann, wo
#           gar keine Grenze mehr steht, ist die naechste Meldung, die eine Grenze
#           erfindet.
#   BLEIBT: die MESSUNG (`bildgroesse`). Wie gross ihre Bilder sind, muss die Kette
#           weiter wissen und sagen duerfen — ohne sie waere der Befund vom 03.09. nie
#           erhoben worden. Der Deckel war falsch; die Zahl, die ihn ueberfuehrt hat,
#           war es nicht.
#   BLEIBT: das WERKZEUG (`kleinere_fassung`). Wer ein Bild bewusst verkleinern will,
#           kann das weiter — aber er muss sagen, WIE KLEIN. Die Grenze ist ein
#           Argument, kein Vorgabewert.
#
# DIE EINHEIT. Gemessen wird eine DATEI, und eine Datei hat BYTES. Darum ist jede Grenze
# hier eine BYTE-Zahl: An genau dieser Kreuzung ist die alte gestorben. `base64_zeichen`
# bleibt als Umrechnung — wer base64 kodiert, braucht sie —, aber jede Meldung, die eine
# Grenze nennt, nennt sie in derselben Einheit wie die gemessene Groesse. Das prueft
# `tests/test_bildgroesse.py` Zahl fuer Zahl und nicht ein Mensch beim Lesen.
#
# ZAHLEN OHNE TAUSENDERTRENNER. Die Meldungen unten schreiben `786432` und nicht
# `786 432`, damit die Probe die Zahlen aus dem Satz zurueckholen und gegen die Einheit
# halten kann. Eine Meldung, die keine Probe lesen kann, ist wieder nur eine Behauptung.

#: Unter diese Kantenlaenge verkleinert :func:`kleinere_fassung` nicht.
#:
#: Ab hier ist das Bild als Ansicht eines Bauwerks nicht mehr zu gebrauchen, und ein
#: Ergebnis, das nur noch eine Groesse einhaelt, beantwortet die Frage nicht mehr, fuer
#: die es erzeugt wurde. Wird die Grenze erreicht, meldet :func:`kleinere_fassung`
#: ``passt=False`` — sie schummelt sich nicht darunter.
MIN_KANTE_FASSUNG = 400


def base64_zeichen(n_byte: int) -> int:
    """Wieviele Base64-Zeichen ``n_byte`` Rohbytes ergeben. Drei Bytes → vier Zeichen."""
    if n_byte < 0:
        raise SchreibError(f"n_byte: nicht negativ erwartet, war {n_byte}.")
    return 4 * ((n_byte + 2) // 3)


def bildgroesse(png) -> dict:
    """Wie gross ist diese Datei — **ohne Urteil**, weil es keine Grenze mehr gibt.

    Das ist die Haelfte, die den Deckel ueberlebt hat. Sie nennt beide Zahlen, die eine
    Bilddatei hat, jede mit ihrer Einheit: die Datei in **Byte**, und ihre base64-Fassung
    in **Zeichen**. Beides steht nebeneinander und nichts wird ineinander umgerechnet und
    dann anders beschriftet — genau das war der Fehler.

    Returns:
        ``{bytes, zeichen, text}``.
    """
    pfad = Path(png)
    if not pfad.is_file():
        raise SchreibError(f"Es gibt keine Datei {str(pfad)!r}.")
    n = pfad.stat().st_size
    zeichen = base64_zeichen(n)
    return {"bytes": n, "zeichen": zeichen,
            "text": f"{n} Byte, base64 {zeichen} Zeichen."}


def passt_unter(png, *, deckel_byte: int) -> dict:
    """Liegt die Datei unter einer **genannten** Grenze? Gerechnet wird in Byte.

    **Es gibt keinen Vorgabewert, und das ist Absicht.** Diese Kette kennt seit dem
    04.09.2026 keine Grenze mehr von sich aus; wer eine will, nennt sie. Ein
    Vorgabewert waere genau der stille Deckel zurueck, den der Owner entfernt hat.

    ``deckel_byte`` ist eine **Byte**-Zahl, weil ``bytes`` eine Byte-Zahl ist. Wer in
    Base64-Zeichen deckeln will, rechnet mit :func:`base64_zeichen` um — und bekommt die
    Zeichenzahlen im Befund gleich mitgeliefert.

    Returns:
        ``{passt, bytes, zeichen, deckel_byte, deckel_zeichen, grund}``.
    """
    if deckel_byte < 1:
        raise SchreibError(
            f"deckel_byte: mindestens 1 erwartet, war {deckel_byte}. Eine Grenze von 0 "
            f"kann keine Datei einhalten.")
    gemessen = bildgroesse(png)
    n, zeichen = gemessen["bytes"], gemessen["zeichen"]
    deckel_zeichen = base64_zeichen(deckel_byte)
    passt = n <= deckel_byte
    lage = "darunter" if passt else "darueber"
    grund = (f"{n} Byte gegen eine Grenze von {deckel_byte} Byte — {lage}. "
             f"In Base64 sind das {zeichen} Zeichen gegen {deckel_zeichen} Zeichen.")
    return {"passt": passt, "bytes": n, "zeichen": zeichen,
            "deckel_byte": deckel_byte, "deckel_zeichen": deckel_zeichen, "grund": grund}


def _kastenmittel(farben, breite: int, hoehe: int, neu_breite: int, neu_hoehe: int):
    """Kastenmittel — jeder Zielpunkt ist der Mittelwert seines Quellrechtecks.

    **Nicht der naechste Nachbar.** Ein Render traegt duenne Linien (Fenstersprossen,
    Gelaenderstaebe); der naechste Nachbar laesst sie je nach Raster verschwinden oder
    springen, das Kastenmittel graut sie ab. Fuer eine Ansicht ist das Zweite richtig.
    """
    zeilen = [(y * hoehe // neu_hoehe, max(y * hoehe // neu_hoehe + 1,
                                           (y + 1) * hoehe // neu_hoehe))
              for y in range(neu_hoehe)]
    spalten = [(x * breite // neu_breite, max(x * breite // neu_breite + 1,
                                              (x + 1) * breite // neu_breite))
               for x in range(neu_breite)]
    raus = []
    for y0, y1 in zeilen:
        versatz = [zy * breite for zy in range(y0, y1)]
        for x0, x1 in spalten:
            r = g = b = n = 0
            for v in versatz:
                for i in range(v + x0, v + x1):
                    p = farben[i]
                    r += p[0]; g += p[1]; b += p[2]; n += 1
            raus.append((r // n, g // n, b // n))
    return raus


def kleinere_fassung(quelle_png, ziel_png, *, deckel_byte: int,
                     min_kante: int = MIN_KANTE_FASSUNG, max_versuche: int = 8) -> dict:
    """Eine verkleinerte Kopie unter eine **genannte** Byte-Grenze. Das Original bleibt.

    **Ein Werkzeug, kein Zwang.** Seit dem 04.09.2026 ruft die Kette das hier nicht mehr
    von selbst; es steht bereit, wenn jemand ein Bild bewusst kleiner haben will. Wie
    klein, sagt ``deckel_byte`` — es gibt keinen Vorgabewert.

    Passt die Quelle schon, wird sie unveraendert kopiert und ``verkleinert=False``
    gemeldet — eine Fassung, die nichts tut, ist besser als eine, die vorsichtshalber
    Aufloesung wegwirft.

    Sonst wird verkleinert, bis es passt. Der erste Faktor ist gerechnet und nicht
    geraten: Die Dateigroesse waechst naeherungsweise mit der Punktzahl, also mit dem
    Quadrat der Kantenlaenge — ``sqrt(Deckel / Ist)``, mit etwas Sicherheitsabstand, weil
    ein verkleinertes Bild pro Punkt schlechter komprimiert (weniger gleichfoermige
    Flaechen). Trifft es nicht, geht es in Schritten weiter.

    **Was diese Funktion NICHT tut: sich unter die Grenze schummeln.** Erreicht sie
    ``min_kante``, ohne darunter zu kommen, meldet sie ``passt=False``. Ein Bild ueber
    der Grenze bleibt ein Bild ueber der Grenze; ein Ergebnis, das nur noch eine Zahl
    einhaelt und nichts mehr zeigt, waere eine Antwort auf die falsche Frage.

    Returns:
        ``{passt, verkleinert, bytes, zeichen, breite, hoehe, faktor, versuche,
        quelle_bytes, deckel_byte, warnungen}``.
    """
    from aiimaging import bildlesen        # lokal wie in `tiefe_exr_zu_png`, siehe dort

    quelle, ziel = Path(quelle_png), Path(ziel_png)
    vorher = passt_unter(quelle, deckel_byte=deckel_byte)
    if vorher["passt"]:
        if ziel != quelle:
            ziel.write_bytes(quelle.read_bytes())
        farben, breite, hoehe = bildlesen.lies_png_farben(quelle)
        return {"passt": True, "verkleinert": False, "bytes": vorher["bytes"],
                "zeichen": vorher["zeichen"], "breite": breite, "hoehe": hoehe,
                "faktor": 1.0, "versuche": 0, "quelle_bytes": vorher["bytes"],
                "deckel_byte": deckel_byte, "warnungen": []}

    farben, breite, hoehe = bildlesen.lies_png_farben(quelle)
    faktor = math.sqrt(deckel_byte / vorher["bytes"]) * 0.95
    warnungen, versuche = [], 0
    letzte = None

    for _ in range(max_versuche):
        neu_b = max(1, int(round(breite * faktor)))
        neu_h = max(1, int(round(hoehe * faktor)))
        if min(neu_b, neu_h) < min_kante:
            warnungen.append(
                f"Unter {min_kante} px Kantenlaenge wird nicht verkleinert: Ein Bild, das "
                f"nur noch eine Groesse einhaelt, zeigt das Bauwerk nicht mehr. Die "
                f"Grenze von {deckel_byte} Byte ist mit dieser Quelle "
                f"({vorher['bytes']} Byte) nicht erreichbar.")
            break
        versuche += 1
        schreibe_farb_png(ziel, _kastenmittel(farben, breite, hoehe, neu_b, neu_h),
                          neu_b, neu_h)
        letzte = (neu_b, neu_h, faktor)
        jetzt = passt_unter(ziel, deckel_byte=deckel_byte)
        if jetzt["passt"]:
            return {"passt": True, "verkleinert": True, "bytes": jetzt["bytes"],
                    "zeichen": jetzt["zeichen"], "breite": neu_b, "hoehe": neu_h,
                    "faktor": faktor, "versuche": versuche,
                    "quelle_bytes": vorher["bytes"], "deckel_byte": deckel_byte,
                    "warnungen": warnungen}
        faktor *= 0.85

    if letzte is None:
        b_end = h_end = 0
        f_end = faktor
        n_end = vorher["bytes"]
    else:
        b_end, h_end, f_end = letzte
        n_end = ziel.stat().st_size
    if not warnungen:
        warnungen.append(
            f"Nach {versuche} Versuchen bleibt die Fassung ueber {deckel_byte} Byte. Das "
            f"ist ein Befund und kein Fehlschlag der Kette — gemeldet wird die Groesse, "
            f"die erreicht wurde, nicht eine, die passt.")
    return {"passt": False, "verkleinert": versuche > 0, "bytes": n_end,
            "zeichen": base64_zeichen(n_end), "breite": b_end, "hoehe": h_end,
            "faktor": f_end, "versuche": versuche, "quelle_bytes": vorher["bytes"],
            "deckel_byte": deckel_byte, "warnungen": warnungen}

def kontrollwerte(art: str, breite: int, hoehe: int, *, seed: int = KONTROLL_SEED):
    """Die Grauwerte eines Kontrollbildes — ohne Datei, damit es prüfbar bleibt.

    * ``rauschen`` — gleichverteiltes weisses Rauschen. Der **härteste** der drei: Er ist
      der einzige, der in der Messung vom 20.08. das Gate bestanden hat.
    * ``grau`` — eine leere Fläche mit 0.5. Belegt, was ein Bild ohne jede Information
      erreicht.
    * ``verlauf`` — ein Verlauf **quer** zur Bildachse, also strukturlos in Bezug auf die
      Tiefe. Er prüft, ob schon ein blosser Helligkeitsgradient reicht.

    Gerechnet wird mit :mod:`random` und festem Startwert — nicht mit ``os.urandom``:
    Reproduzierbarkeit ist hier wichtiger als Güte des Zufalls, und ein Anker, der bei
    jedem Aufruf anders ausfällt, ist kein Anker.

    Raises:
        SchreibError: unbekannte Art, oder unbrauchbare Bildmasse.
    """
    if art not in KONTROLLARTEN:
        raise SchreibError(
            f"Unbekannte Kontrollart {art!r}. Bekannt: {', '.join(KONTROLLARTEN)}."
        )
    if breite < 1 or hoehe < 1:
        raise SchreibError(f"Bildmasse {breite}×{hoehe} ergeben kein Bild.")

    n = breite * hoehe
    if art == "grau":
        return [0.5] * n
    if art == "verlauf":
        # Quer, also von links nach rechts — eine Tiefenrampe läuft von unten nach oben.
        # Der Verlauf soll gerade NICHT wie eine Bodenebene aussehen.
        teiler = max(1, breite - 1)
        return [(x / teiler) for _ in range(hoehe) for x in range(breite)]

    import random

    wuerfel = random.Random(seed)
    return [wuerfel.random() for _ in range(n)]


def schreibe_kontrollbild(ziel, art: str, breite: int, hoehe: int, *,
                          seed: int = KONTROLL_SEED, bittiefe: int = 8) -> Path:
    """Ein Kontrollbild als PNG — die Datei, die der Tiefenschätzer bekommt.

    Acht Bit statt sechzehn: Das Bild soll dem gleichen, das ein Bildmodell liefert, und
    ein 16-Bit-Rauschen wäre kein realistischerer Anker, sondern ein anderer.
    """
    return schreibe_graustufen_png(
        ziel, kontrollwerte(art, breite, hoehe, seed=seed), breite, hoehe,
        bittiefe=bittiefe)
