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
    "normalisiere_tiefe", "schreibe_graustufen_png", "tiefe_exr_zu_png",
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
