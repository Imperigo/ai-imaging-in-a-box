"""KONTEXT — die Umgebung im Bild: ein **Splat** neben dem Bauwerk (Owner-Entscheid 76).

Was hier steht und was nicht
----------------------------
Ein Splat (3D-Gaussian-Splatting, ``.ply``) ist eine Aufnahme der Umgebung. Seit dem
08.10.2026 läuft er im Multipass **als Umgebung** mit: sichtbar in Beauty und Tiefe —
**gemessen wird weiter nur das Bauwerk**. Hüllbox, Rahmung der Kamera und Bauwerksmaske
bleiben auf dem Modell.

Gerendert wird hinter der Prozessgrenze (``runners/blender_depth_stage.py``,
``_kontext_laden``). Dieses Modul ist die **Produktseite** davon: die Zahlen, die das Bild
bestimmen, die Lage des Splats als Matrix und der Fingerabdruck der Datei. Alles reine
stdlib, ohne ``bpy`` (Regel 2), aus Python heraus prüfbar (Regel 4) — derselbe Grund, aus
dem :data:`aiimaging.contracts.DREHUNG_Z_UP_GRAD` nicht im Runner steht: *Was hinter der
Prozessgrenze steht, erreicht keine Probe.*

Die Lage: glTF-Welt, zeilenweise
--------------------------------
Die Matrix kommt im Vertrag als ``RenderScene.context.transform`` (Integrator,
08.10.2026): **16 Zahlen, eine 4×4-Matrix, zeilenweise** (``m[0..3]`` ist die erste
Zeile, die Verschiebung steht in ``m[3], m[7], m[11]``), und sie bildet den Splat in die
**glTF-Welt** ab — Meter, **Y oben**, dieselbe Welt wie ``model.glb``.

Blender sieht diese Welt nicht: Sein glTF-Import dreht die glb von Y oben nach Z oben,
``R_x(+90)`` (:func:`aiimaging.contracts.blender_gltf_import_dreht`). Der Splat muss
**dieselbe** Drehung bekommen, sonst liegt er neben dem Modell auf der Seite:

    M_blender = [Z-up-Korrektur] · R_x(+90) · M

Die Z-up-Korrektur (``R_x(−90)``) nur, wenn die glb selbst schon Z oben trug
(``--rotiere-z-up``) — dann wird das Modell zurückgedreht, und der Splat mit ihm. *Er
bekommt genau, was das Modell bekommt.* Ohne Matrix gilt die Einheit **in der glTF-Welt**,
also ebenfalls mit der Drehung.

Was gesetzt und nicht gemessen ist
----------------------------------
:data:`DECKKRAFT_MIN`, :data:`RADIUS_MIN_M` und :data:`RADIUS_MAX_M` sind **GESETZT**. Ein
Splat besteht aus weichen, halbdurchsichtigen Ellipsoiden; Cycles rendert hier **harte
Kugeln**. Das ist eine Näherung, und ihre Zahlen sind Setzungen, keine Messung — welche
Werte an echten Splats das schönste Bild geben, ist am Heim-PC zu messen.
"""
from __future__ import annotations

import hashlib
import math
from pathlib import Path

__all__ = [
    "DECKKRAFT_MIN", "KontextError", "MATRIX_EINHEIT", "RADIUS_MAX_M", "RADIUS_MIN_M",
    "SH_C0", "fingerabdruck", "matrix_massstab", "matrix_nach_blender", "pruefe_matrix",
    "GLAETTE_MIN_PX", "GLAETTE_PX_JE_128", "glaette_radius", "glaette_tiefe",
    "schliesse_umgebung",
]


class KontextError(ValueError):
    """Diese Angabe zum Kontext lässt sich nicht deuten — und ein Ersatzwert wäre schlimmer.

    Ein Splat an der falschen Stelle sähe im Bild aus wie einer an der richtigen.
    """


#: Der Koeffizient der Kugelflächenfunktion nullten Grades, ``1 / (2·√π)``.
#:
#: **SH-Grad 0** ist der richtungsunabhängige Teil der Farbe eines Gaussians. Gerechnet
#: wird ``rgb = clamp(0,5 + SH_C0 · f_dc, 0, 1)`` — die Formel der verbreiteten
#: Trainingsprogramme. Die höheren Grade (``f_rest_*``, Glanz je Blickrichtung) werden
#: **nicht** gelesen: Ein Bild aus einer Richtung braucht sie nicht, und Kugeln in Cycles
#: können sie nicht tragen.
SH_C0 = 0.28209479177387814

#: Unter dieser Deckkraft (``sigmoid(opacity)``) wird ein Punkt **verworfen**. GESETZT.
#:
#: Warum überhaupt verwerfen: Cycles rendert jeden Punkt als **undurchsichtige** Kugel. Ein
#: Gaussian mit 3 % Deckkraft — im Splat ein Hauch, oft Rauschen in der Luft — würde
#: hier zu einer festen Kugel und verdeckte, was dahinter steht, womöglich das Bauwerk.
#: Warum 0,10 und nicht 1/255 (die Schwelle der Rasterer): Dort trägt ein schwacher
#: Gaussian schwach bei, hier ganz oder gar nicht.
DECKKRAFT_MIN = 0.10

#: Die Kappung des Punktradius in Metern (Welt), unten und oben. GESETZT.
#:
#: Der Radius je Punkt ist das **Mittel der zwei grössten Achsen** ``exp(scale_i)``. Ein
#: flacher Gaussian — der häufigste Fall, er sitzt auf einer Fläche — behält damit seine
#: Breite, eine Nadel wird halbiert. *Erster Anlauf (08.10.2026) war das Mittel aller drei:*
#: Am synthetischen Boden blieben die Kugeln dann kleiner als ihr Abstand, und die Tiefe
#: hatte Löcher bis zum Hintergrund. Das Maximum hätte Nadeln zu Bällen aufgebläht. Unter 1 cm verschwindet ein Punkt zwischen den Bildpunkten; über
#: 50 cm sind es in echten Splats meist Hintergrundwolken, die als Kugel das Bild verstellen.
RADIUS_MIN_M = 0.01
RADIUS_MAX_M = 0.50

#: Die Einheitsmatrix, zeilenweise — die Lage «so, wie die Datei es sagt», in der glTF-Welt.
MATRIX_EINHEIT = (1.0, 0.0, 0.0, 0.0,
                  0.0, 1.0, 0.0, 0.0,
                  0.0, 0.0, 1.0, 0.0,
                  0.0, 0.0, 0.0, 1.0)

#: Um wieviel Grad Blenders glTF-Import um X dreht (Y oben → Z oben). Eine Aussage über
#: ein fremdes Programm — darum als Zahl, siehe
#: :func:`aiimaging.contracts.blender_gltf_import_dreht` (dort mit derselben Begründung).
GLTF_IMPORT_GRAD = 90.0


def pruefe_matrix(werte) -> tuple[float, ...]:
    """16 Zahlen → die Matrix als Tupel, zeilenweise — oder ein Satz, warum nicht.

    Geprüft wird: genau 16 endliche Zahlen, die letzte Zeile ``0 0 0 1`` (eine Lage, keine
    Projektion) und ein drehbarer 3×3-Teil (Determinante nicht null). Spiegelungen sind
    erlaubt: Ein Splat aus einem linkshändigen Programm kann eine brauchen.

    Raises:
        KontextError: mit dem Grund.
    """
    if isinstance(werte, (str, bytes)) or not hasattr(werte, "__iter__"):
        raise KontextError(f"Die Matrix ist {werte!r} — erwartet sind 16 Zahlen, zeilenweise.")
    zahlen = list(werte)
    if len(zahlen) != 16:
        raise KontextError(
            f"Die Matrix hat {len(zahlen)} statt 16 Zahlen. Eine 4×4-Matrix, zeilenweise; "
            f"eine halbe Lage wird nicht ergänzt.")
    try:
        m = tuple(float(z) for z in zahlen)
    except (TypeError, ValueError) as fehler:
        raise KontextError(f"Die Matrix enthält etwas, das keine Zahl ist: {zahlen!r}") from fehler
    if any(isinstance(z, bool) for z in zahlen) or not all(math.isfinite(z) for z in m):
        raise KontextError(f"Die Matrix enthält nan, inf oder Wahrheitswerte: {zahlen!r}")
    if max(abs(m[12]), abs(m[13]), abs(m[14]), abs(m[15] - 1.0)) > 1e-9:
        raise KontextError(
            f"Die letzte Zeile ist {list(m[12:])} statt [0, 0, 0, 1]. Steht die "
            f"Verschiebung dort, ist die Matrix spaltenweise geschrieben — der Vertrag "
            f"verlangt zeilenweise (Verschiebung in m[3], m[7], m[11]).")
    if abs(_det3(m)) < 1e-12:
        raise KontextError("Der Drehteil der Matrix ist entartet (Determinante null) — "
                           "der Splat fiele auf eine Fläche oder einen Punkt zusammen.")
    return m


def _det3(m) -> float:
    a, b, c, d, e, f, g, h, i = m[0], m[1], m[2], m[4], m[5], m[6], m[8], m[9], m[10]
    return a * (e * i - f * h) - b * (d * i - f * g) + c * (d * h - e * g)


def _mal(a, b) -> tuple[float, ...]:
    return tuple(sum(a[4 * z + k] * b[4 * k + s] for k in range(4))
                 for z in range(4) for s in range(4))


def _dreh_x(grad: float) -> tuple[float, ...]:
    bogen = math.radians(grad)
    c, s = round(math.cos(bogen), 15) + 0.0, round(math.sin(bogen), 15) + 0.0
    return (1.0, 0.0, 0.0, 0.0,
            0.0, c, -s, 0.0,
            0.0, s, c, 0.0,
            0.0, 0.0, 0.0, 1.0)


def matrix_nach_blender(m=None, *, z_up_quelle: bool = False) -> tuple[float, ...]:
    """Die Lage aus der glTF-Welt in Blenders Welt: ``[Z-up-Korrektur] · R_x(+90) · M``.

    Args:
        m: 16 Zahlen zeilenweise oder ``None`` (Einheit in der glTF-Welt).
        z_up_quelle: Die glb trug selbst schon Z oben (``--rotiere-z-up``). Dann wird das
            Modell mit :data:`aiimaging.contracts.DREHUNG_Z_UP_GRAD` zurückgedreht — und
            der Splat bekommt dieselbe Drehung, damit er beim Modell bleibt.

    Returns:
        Die Matrix für ``matrix_world``, zeilenweise.
    """
    from aiimaging import contracts                      # noqa: PLC0415 — stdlib-Modul
    gesamt = _mal(_dreh_x(GLTF_IMPORT_GRAD), pruefe_matrix(MATRIX_EINHEIT if m is None else m))
    if z_up_quelle:
        gesamt = _mal(_dreh_x(contracts.DREHUNG_Z_UP_GRAD), gesamt)
    return tuple(round(w, 12) + 0.0 for w in gesamt)


def matrix_massstab(m) -> float:
    """Der mittlere Massstab einer Lage: ``|det|^(1/3)`` des Drehteils.

    Gebraucht für den Radius: Die Kappung :data:`RADIUS_MIN_M`/:data:`RADIUS_MAX_M` gilt
    in **Metern der Welt**, der Radius steht aber im Splat. Wer den Splat mit der Matrix
    verdoppelt, verdoppelt auch die Punkte — gekappt wird danach.
    """
    return abs(_det3(pruefe_matrix(m))) ** (1.0 / 3.0)


def fingerabdruck(pfad) -> dict:
    """Name, Grösse und sha256 einer Splat-Datei — **ohne ihren Pfad**.

    Regel 3: Ein Pfad trägt auf der HomeStation einen Benutzernamen, und der Bericht geht
    nach aussen. Name und Prüfsumme sagen, *welcher* Splat es war, ohne zu sagen, wo er lag.

    Raises:
        KontextError: Die Datei fehlt oder ist leer.
    """
    p = Path(pfad)
    if not p.is_file():
        raise KontextError(f"Splat-Datei {p.name!r} gibt es nicht (oder sie ist keine Datei).")
    summe = hashlib.sha256()
    with open(p, "rb") as datei:
        for stueck in iter(lambda: datei.read(1 << 20), b""):
            summe.update(stueck)
    groesse = p.stat().st_size
    if groesse == 0:
        raise KontextError(f"Splat-Datei {p.name!r} ist leer.")
    return {"datei": p.name, "bytes": groesse, "sha256": summe.hexdigest()}


# ======================================================================================
# GLÄTTEN (Owner-Entscheid 77, 08.10.2026)
# ======================================================================================
#
# **Anlass ``auf-20261008-271``:** Am echten Splat malte Z-Image in allen 18 Bildern
# «Konfetti» — Kreisscheiben statt Bäume. Die Aufnahme ist lückig (70 % der Punkte unter
# der Deckkraft verworfen), und im Tiefenbild stand die Umgebung als Streuung einzelner
# Scheiben. Der Owner hat entschieden: **glätten.** Die Lücken zwischen den Punkten werden
# gefüllt (nur dort, wo vorher Hintergrund war — nie auf dem Bauwerk), und die Tiefe der
# Umgebung wird über ein Fenster gemittelt. Reine stdlib, linear in der Bildgrösse.

#: Halbe Fensterbreite in Bildpunkten je 128 Bildpunkte Bildbreite. GESETZT, nicht gemessen
#: (512 px → 4, 1024 px → 8); ob es das Konfetti nimmt, misst die HomeStation.
GLAETTE_PX_JE_128 = 1.0
GLAETTE_MIN_PX = 2


def glaette_radius(breite: int) -> int:
    """Der Radius für :func:`schliesse_umgebung` und :func:`glaette_tiefe` bei dieser Breite."""
    return max(GLAETTE_MIN_PX, int(round(int(breite) * GLAETTE_PX_JE_128 / 128.0)))


def _zeilen_max(werte: list[bool], breite: int, hoehe: int, r: int) -> list[bool]:
    """Jeder Punkt wird wahr, wenn in seiner Zeile im Abstand ``≤ r`` einer wahr ist."""
    aus = [False] * len(werte)
    for y in range(hoehe):
        z = y * breite
        letzter = -10 ** 9                       # Lage des letzten wahren Punkts links
        naechster = [10 ** 9] * breite           # Lage des nächsten wahren Punkts rechts
        n = 10 ** 9
        for x in range(breite - 1, -1, -1):
            if werte[z + x]:
                n = x
            naechster[x] = n
        for x in range(breite):
            if werte[z + x]:
                letzter = x
            aus[z + x] = (x - letzter <= r) or (naechster[x] - x <= r)
    return aus


def _transponiert(werte: list, breite: int, hoehe: int) -> list:
    return [werte[y * breite + x] for x in range(breite) for y in range(hoehe)]


def _dehne(werte: list[bool], breite: int, hoehe: int, r: int) -> list[bool]:
    zeilen = _zeilen_max(werte, breite, hoehe, r)
    spalten = _zeilen_max(_transponiert(zeilen, breite, hoehe), hoehe, breite, r)
    return _transponiert(spalten, hoehe, breite)


def schliesse_umgebung(umgebung, frei, breite: int, hoehe: int,
                       radius: int | None = None) -> list[bool]:
    """Die Lücken der Umgebung schliessen — **nur auf freien Punkten** (Hintergrund).

    Morphologisches Schliessen (erst dehnen, dann wieder schrumpfen) mit einem quadratischen
    Fenster der halben Breite ``radius``: Was zwischen zwei Umgebungspunkten liegt, wird
    Umgebung; die Aussenkante bleibt, wo sie war. Ein Punkt des Bauwerks wird nie Umgebung —
    gefüllt wird nur, wo ``frei`` wahr ist.
    """
    n = int(breite) * int(hoehe)
    if len(umgebung) != n or len(frei) != n:
        raise KontextError(f"Umgebung/frei passen nicht zu {breite}×{hoehe}.")
    r = glaette_radius(breite) if radius is None else int(radius)
    # Mit einem Rand von `r` falschen Punkten rechnen: Ausserhalb des Bildes ist keine
    # Umgebung — sonst bliebe beim Schrumpfen am Bildrand stehen, was nur gedehnt war.
    bp, hp = breite + 2 * r, hoehe + 2 * r
    gepolstert = [False] * (bp * hp)
    for y in range(hoehe):
        for x in range(breite):
            gepolstert[(y + r) * bp + x + r] = bool(umgebung[y * breite + x])
    gedehnt = _dehne(gepolstert, bp, hp, r)
    # Schrumpfen = Dehnen des Komplements.
    geschrumpft = [not w for w in _dehne([not w for w in gedehnt], bp, hp, r)]
    innen = [geschrumpft[(y + r) * bp + x + r] for y in range(hoehe) for x in range(breite)]
    return [bool(u) or (bool(g) and bool(f)) for u, g, f in zip(umgebung, innen, frei)]


def glaette_tiefe(tiefe, umgebung, breite: int, hoehe: int, radius: int | None = None,
                  *, gueltig_bis_m: float = 1.0e7) -> tuple[list[float], dict]:
    """Die Tiefe auf der (geschlossenen) Umgebung über ein Fenster mitteln.

    Gemittelt werden nur gültige Tiefen der Umgebung (endlich, ``0 < t < gueltig_bis_m``);
    ein gefüllter Punkt bekommt so die Tiefe seiner Nachbarn. Punkte ausserhalb der
    Umgebung bleiben **unverändert** — das Bauwerk wird nicht angefasst. Ein Umgebungspunkt
    ohne gültigen Nachbarn im Fenster bleibt, wie er war.

    Returns:
        ``(tiefe_neu, befund)`` — ``befund = {radius_px, n_umgebung, n_gefuellt}``.
    """
    n = int(breite) * int(hoehe)
    if len(tiefe) != n or len(umgebung) != n:
        raise KontextError(f"Tiefe/Umgebung passen nicht zu {breite}×{hoehe}.")
    r = glaette_radius(breite) if radius is None else int(radius)

    def ok(i):
        t = tiefe[i]
        return umgebung[i] and math.isfinite(t) and 0.0 < t < gueltig_bis_m

    w1 = breite + 1
    summe = [0.0] * (w1 * (hoehe + 1))           # Integralbilder
    zahl = [0] * (w1 * (hoehe + 1))
    for y in range(hoehe):
        zs, zz = 0.0, 0
        for x in range(breite):
            i = y * breite + x
            if ok(i):
                zs += tiefe[i]
                zz += 1
            k = (y + 1) * w1 + (x + 1)
            summe[k] = summe[k - w1] + zs
            zahl[k] = zahl[k - w1] + zz
    neu = list(tiefe)
    n_gefuellt = 0
    for y in range(hoehe):
        y0, y1 = max(0, y - r), min(hoehe, y + r + 1)
        for x in range(breite):
            i = y * breite + x
            if not umgebung[i]:
                continue
            x0, x1 = max(0, x - r), min(breite, x + r + 1)
            c = zahl[y1 * w1 + x1] - zahl[y0 * w1 + x1] - zahl[y1 * w1 + x0] + zahl[y0 * w1 + x0]
            if c == 0:
                continue
            s = summe[y1 * w1 + x1] - summe[y0 * w1 + x1] - summe[y1 * w1 + x0] + summe[y0 * w1 + x0]
            if not ok(i):
                n_gefuellt += 1
            neu[i] = s / c
    return neu, {"radius_px": r, "n_umgebung": int(sum(1 for u in umgebung if u)),
                 "n_gefuellt": n_gefuellt}
