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

def normalisiere_tiefe(tiefe: Sequence[float], *,
                       hintergrund_ab_m: float = HINTERGRUND_AB_M) -> tuple[list[float], dict]:
    """Meterwerte → Grauwerte 0..1 (*nah = hell*) plus die Angaben zur Rückrechnung.

    Warum nicht Blenders ``Normalize``-Knoten
    -----------------------------------------
    Er normalisiert über **alle** Bildpunkte, also auch über den Hintergrund mit seinen
    ~1e10 Metern. Das Gebäude landete dann in den untersten Promille des Wertebereichs
    und wäre gleichmässig schwarz. Deshalb wird hier mit einer ausdrücklichen
    Hintergrundschranke gerechnet.

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
    max_m = max(tiefe[i] for i in gueltig)
    spanne = (max_m - min_m) or 1.0          # eine ebene Fläche frontal: Spanne 0

    grau = [HINTERGRUND_GRAUWERT] * len(tiefe)
    for i in gueltig:
        # nah = hell (ControlNet-Konvention). Der Hintergrund bleibt 0.0 — unendlich fern
        # ist der Grenzfall von „dunkel", nicht ein eigener Sonderfall.
        grau[i] = 1.0 - (tiefe[i] - min_m) / spanne

    return grau, {
        "min_m": float(min_m),
        "max_m": float(max_m),
        "konvention": KONVENTION,
        "hintergrund_grauwert": HINTERGRUND_GRAUWERT,
        "rueckrechnung": RUECKRECHNUNG,
        "n_geometriepixel": len(gueltig),
        # Wer den Wert später anders setzt, soll in der Datei sehen, wogegen gemessen
        # wurde — die Schranke bestimmt min_m und max_m mit.
        "hintergrund_ab_m": float(hintergrund_ab_m),
        "quelle": "produkt",
    }


def tiefe_exr_zu_png(exr, ziel_png, *, hintergrund_ab_m: float = HINTERGRUND_AB_M,
                     bittiefe: int = 16, timeout: int = 300, _leser=None,
                     _starte=None) -> dict:
    """EXR in Metern → normalisiertes Graustufen-PNG. Der ganze Weg, ohne Blender.

    Das ist die Stelle, die :func:`aiimaging.seams.glb_zu_multipass` nach dem Blender-Lauf
    aufruft. Sie ersetzt den Schritt, der bis zum 18.08.2026 im Runner stand.

    Args:
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
    grau, normalisierung = normalisiere_tiefe(werte, hintergrund_ab_m=hintergrund_ab_m)
    schreibe_graustufen_png(ziel_png, grau, breite, hoehe, bittiefe=bittiefe)
    normalisierung["breite"] = breite
    normalisierung["hoehe"] = hoehe
    normalisierung["bittiefe"] = bittiefe
    return normalisierung


__all__ = [
    "HINTERGRUND_AB_M", "HINTERGRUND_GRAUWERT", "KONVENTION", "RUECKRECHNUNG",
    "SchreibError",
    "normalisiere_tiefe", "schreibe_farb_png", "schreibe_graustufen_png",
    "tiefe_exr_zu_png",
    "BLATT_DECKEL_BASE64_ZEICHEN", "BLATT_DECKEL_BYTE", "BLATT_MIN_KANTE",
    "base64_zeichen", "blattfassung", "passt_aufs_blatt",
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



# ── Das Blatt ─────────────────────────────────────────────────────────────────────────
#
# GEMESSEN AM 03.09.2026, weil Demolauf 15 und 17 an derselben Naht stehenblieben: Der
# Knopf «Aufs Blatt» in KosmoOrbit wies das Regelergebnis der eigenen Kette ab.
#
# Der Deckel steht drueben (`kosmo-orbit/.../vis-jobs.ts`, `BILD_DECKEL_BASE64_ZEICHEN`)
# und vergleicht BASE64-ZEICHEN, nicht Bytes. Das ist der Grund, warum die Meldung in die
# Irre fuehrt: Sie nennt «bis 1.0 MB», rechnet die gemessene Groesse aber in Rohbytes um
# und die Grenze nicht. Base64 macht aus drei Bytes vier Zeichen — 1 048 576 Zeichen sind
# darum 786 432 Rohbytes, also 0.75 MiB. Wer der Meldung folgt und auf 1.0 MB
# verkleinert, wird ein zweites Mal abgewiesen.
#
# WARUM DIESE ZAHLEN HIER STEHEN UND NICHT DER DECKEL GEAENDERT WIRD. Der Deckel gehoert
# einer anderen Lane und ist ein Owner-Entscheid (02.09.2026: «die Meldung verbessern, den
# Deckel nicht anfassen»). Was hier fehlte, war die andere Haelfte: Die Kette wusste
# nichts von einer Grenze, gegen die 60 von 66 ihrer Nutzbilder verstiessen (Median
# 1 277 231 Byte gegen 786 432). Eine Kette, deren Normalausgabe die eigene naechste Stufe
# nicht annimmt, ist an dieser Naht nicht anschlussfaehig — und zwar unabhaengig davon,
# wer den Deckel gesetzt hat.
#
# WARUM EINE FASSUNG UND KEINE VERKLEINERUNG DES RENDERS. Das Render ist das Produkt und
# bleibt, wie es ist. Fuer das Blatt entsteht eine BENANNTE, kleinere Kopie. Das ist die
# dritte der drei Moeglichkeiten («beides trennen»), und sie ist die einzige, die weder
# fremde Entscheide umstoesst noch Aufloesung verschenkt, wo sie gebraucht wird.

#: Der Deckel der Gegenstelle, in Base64-Zeichen. Abgelesen am 03.09.2026.
BLATT_DECKEL_BASE64_ZEICHEN = 1_048_576

#: Derselbe Deckel in Rohbytes — die Zahl, die fuer eine Bilddatei zaehlt.
#:
#: **Nicht 1 000 000 und nicht 1 048 576.** 1 048 576 Zeichen / 4 * 3 = 786 432 Byte.
#: Die Meldung der Gegenstelle nennt an dieser Stelle «1.0 MB»; das ist um den Faktor 4/3
#: zu hoch und der Grund, warum ein Verkleinern auf «knapp unter 1 MB» wieder scheitert.
BLATT_DECKEL_BYTE = BLATT_DECKEL_BASE64_ZEICHEN // 4 * 3

#: Unter diese Kantenlaenge wird nicht verkleinert.
#:
#: Ab hier ist das Bild als Ansicht eines Bauwerks nicht mehr zu gebrauchen, und ein
#: Ergebnis, das nur noch den Deckel einhaelt, beantwortet die Frage nicht mehr, fuer die
#: es erzeugt wurde. Wird die Grenze erreicht, meldet :func:`blattfassung`
#: ``passt=False`` — sie schummelt sich nicht darunter.
BLATT_MIN_KANTE = 400


def base64_zeichen(n_byte: int) -> int:
    """Wieviele Base64-Zeichen ``n_byte`` Rohbytes ergeben. Drei Bytes → vier Zeichen."""
    if n_byte < 0:
        raise SchreibError(f"n_byte: nicht negativ erwartet, war {n_byte}.")
    return 4 * ((n_byte + 2) // 3)


def passt_aufs_blatt(png, *, deckel_zeichen: int = BLATT_DECKEL_BASE64_ZEICHEN) -> dict:
    """Nimmt das Blatt diese Datei an? Rechnet in **Zeichen**, wie die Gegenstelle.

    Die Pruefung ist absichtlich hier und nicht erst am Knopf: Eine Kette soll wissen, ob
    ihr Ergebnis anschlussfaehig ist, bevor jemand klickt.

    Returns:
        ``{passt, bytes, zeichen, deckel_zeichen, deckel_byte, grund}``.
    """
    pfad = Path(png)
    if not pfad.is_file():
        raise SchreibError(f"Es gibt keine Datei {str(pfad)!r}.")
    n = pfad.stat().st_size
    zeichen = base64_zeichen(n)
    deckel_byte = deckel_zeichen // 4 * 3
    passt = zeichen <= deckel_zeichen
    if passt:
        grund = (f"{n} Byte ergeben {zeichen} Base64-Zeichen und liegen unter dem Deckel "
                 f"von {deckel_zeichen} Zeichen ({deckel_byte} Byte).")
    else:
        grund = (f"{n} Byte ergeben {zeichen} Base64-Zeichen — der Deckel liegt bei "
                 f"{deckel_zeichen} Zeichen, also bei {deckel_byte} Rohbytes (0.75 MiB). "
                 f"ACHTUNG: Die Meldung der Gegenstelle nennt hier «1.0 MB». Das ist die "
                 f"Zeichenzahl durch 1 048 576 und nicht die Byte-Grenze; wer auf 1.0 MB "
                 f"verkleinert, wird erneut abgewiesen.")
    return {"passt": passt, "bytes": n, "zeichen": zeichen,
            "deckel_zeichen": deckel_zeichen, "deckel_byte": deckel_byte, "grund": grund}


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


def blattfassung(quelle_png, ziel_png, *,
                 deckel_zeichen: int = BLATT_DECKEL_BASE64_ZEICHEN,
                 min_kante: int = BLATT_MIN_KANTE, max_versuche: int = 8) -> dict:
    """Eine verkleinerte Kopie fuer das Blatt. **Das Render bleibt unangetastet.**

    Passt die Quelle schon, wird sie unveraendert kopiert und ``verkleinert=False``
    gemeldet — eine Fassung, die nichts tut, ist besser als eine, die vorsichtshalber
    Aufloesung wegwirft.

    Sonst wird verkleinert, bis es passt. Der erste Faktor ist gerechnet und nicht
    geraten: Die Dateigroesse waechst naeherungsweise mit der Punktzahl, also mit dem
    Quadrat der Kantenlaenge — ``sqrt(Deckel / Ist)``, mit etwas Sicherheitsabstand, weil
    ein verkleinertes Bild pro Punkt schlechter komprimiert (weniger gleichfoermige
    Flaechen). Trifft es nicht, geht es in Schritten weiter.

    **Was diese Funktion NICHT tut: sich unter den Deckel schummeln.** Erreicht sie
    ``min_kante``, ohne unter den Deckel zu kommen, meldet sie ``passt=False``. Ein Bild
    ueber der Grenze bleibt ein Bild ueber der Grenze; ein Ergebnis, das nur noch den
    Deckel einhaelt und nichts mehr zeigt, waere eine Antwort auf die falsche Frage.

    Returns:
        ``{passt, verkleinert, bytes, zeichen, breite, hoehe, faktor, versuche,
        quelle_bytes, warnungen}``.
    """
    from aiimaging import bildlesen        # lokal wie in `tiefe_exr_zu_png`, siehe dort

    quelle, ziel = Path(quelle_png), Path(ziel_png)
    vorher = passt_aufs_blatt(quelle, deckel_zeichen=deckel_zeichen)
    if vorher["passt"]:
        if ziel != quelle:
            ziel.write_bytes(quelle.read_bytes())
        farben, breite, hoehe = bildlesen.lies_png_farben(quelle)
        return {"passt": True, "verkleinert": False, "bytes": vorher["bytes"],
                "zeichen": vorher["zeichen"], "breite": breite, "hoehe": hoehe,
                "faktor": 1.0, "versuche": 0, "quelle_bytes": vorher["bytes"],
                "warnungen": []}

    farben, breite, hoehe = bildlesen.lies_png_farben(quelle)
    deckel_byte = deckel_zeichen // 4 * 3
    faktor = math.sqrt(deckel_byte / vorher["bytes"]) * 0.95
    warnungen, versuche = [], 0
    letzte = None

    for _ in range(max_versuche):
        neu_b = max(1, int(round(breite * faktor)))
        neu_h = max(1, int(round(hoehe * faktor)))
        if min(neu_b, neu_h) < min_kante:
            warnungen.append(
                f"Unter {min_kante} px Kantenlaenge wird nicht verkleinert: Ein Bild, das "
                f"nur noch den Deckel einhaelt, zeigt das Bauwerk nicht mehr. Der Deckel "
                f"von {deckel_zeichen} Zeichen ({deckel_byte} Byte) ist mit dieser Quelle "
                f"({vorher['bytes']} Byte) nicht erreichbar.")
            break
        versuche += 1
        schreibe_farb_png(ziel, _kastenmittel(farben, breite, hoehe, neu_b, neu_h),
                          neu_b, neu_h)
        letzte = (neu_b, neu_h, faktor)
        jetzt = passt_aufs_blatt(ziel, deckel_zeichen=deckel_zeichen)
        if jetzt["passt"]:
            return {"passt": True, "verkleinert": True, "bytes": jetzt["bytes"],
                    "zeichen": jetzt["zeichen"], "breite": neu_b, "hoehe": neu_h,
                    "faktor": faktor, "versuche": versuche,
                    "quelle_bytes": vorher["bytes"], "warnungen": warnungen}
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
            f"Nach {versuche} Versuchen bleibt die Fassung ueber dem Deckel. Das ist ein "
            f"Befund und kein Fehlschlag der Kette — gemeldet wird die Groesse, die "
            f"erreicht wurde, nicht eine, die passt.")
    return {"passt": False, "verkleinert": versuche > 0, "bytes": n_end,
            "zeichen": base64_zeichen(n_end), "breite": b_end, "hoehe": h_end,
            "faktor": f_end, "versuche": versuche, "quelle_bytes": vorher["bytes"],
            "warnungen": warnungen}

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
