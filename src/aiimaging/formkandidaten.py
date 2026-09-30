"""Kandidaten für eine Formprüfung — Zahlen, die dem Augenurteil folgen sollen.

**Anlass (Owner-Entscheid 30.09.2026, «ja nach deiner Empfehlung», Sitzung 73 §17).** Keine der
bisherigen Zahlen erkennt verlässlich, ob die Gebäudeform im erzeugten Bild steht: ``geom_iou``
versagt beim Hochbau, ρ ist frontal niedrig auch bei stehendem Bild, und die Umrisstreue
bevorzugt kantenreiche Fälschungen (auf-186, auf-188, auf-190). Entschieden hat jedes Mal das
Auge der HomeStation — blind, vor den Zahlen. **Dieses Auge wird jetzt die Referenz**: Die
HomeStation rechnet die Kandidaten unten an ihren 88 etikettierten Bildern, und die Auswertung
(``tools/formpruefung_auswertung.py``) sagt, welcher dem Auge folgt.

Kein Kandidat hier benutzt einen Tiefenschätzer. Alle lesen nur das erzeugte Bild und die
Blender-Ebenen derselben Kamera (Soll-Tiefe, Material-ID).

Die Kandidaten
--------------
``umriss_*``
    Die Umrisstreue (:mod:`aiimaging.umriss`) — einmal an allen Soll-Sprüngen, einmal **nur an
    der Silhouette** (Bauwerk gegen Hintergrund). Die zweite Fassung fragt nicht nach
    Tiefenstufen im Inneren, die ein Bildmodell selten nachzeichnet.
``richtung``
    **Laufen die Bildkanten in dieselbe Richtung wie die Soll-Kanten?** An jedem Soll-Kantenpixel
    der Winkel zwischen dem Gradienten des Bildes und dem der Soll-Tiefe, gewichtet mit der
    Stärke der Bildkante. Eine Holztextur hat viele Kanten, aber in allen Richtungen — hier zählt
    nur, was parallel zum Umriss läuft. Zufall ergibt ``2/π`` ≈ 0,637; ``richtung_abhebung`` ist
    der Wert geteilt durch den Zufall (um 1 heisst: nicht besser als Zufall).
``flaechentrennung``
    **Sind die Flächen des Gebäudes im Bild als Flächen erkennbar?** Die Material-ID teilt das
    Bild in Flächen (Wand Süd, Wand West, Platte, Gelände, Hintergrund). Gemessen wird, welcher
    Anteil der Helligkeitsstreuung des Bildes **zwischen** diesen Flächen liegt und nicht
    **innerhalb** (η², 0 bis 1). Ein Bild, das die Form trägt, ist innerhalb einer Wand ruhig
    und springt an ihrer Grenze; ein erfundenes Motiv verteilt seine Helligkeit ohne Bezug.

Alle drei sind **Auskunft**, keine Urteile: ``urteilt`` ist ``False``, bis die Auswertung eine
Schwelle trägt. Reine stdlib (Regel 4).
"""
from __future__ import annotations

import math
from collections.abc import Sequence

from aiimaging import umriss

#: Erwartungswert von ``|cos|`` bei gleichverteilten Winkeln — der Zufall für ``richtung``.
ZUFALL_RICHTUNG = 2.0 / math.pi

#: Hintergrundmarke für die Soll-Tiefe (wie ``umriss.HINTERGRUND_AB_M``).
HINTERGRUND_AB_M = umriss.HINTERGRUND_AB_M


def _silhouette_soll(soll: Sequence[float]) -> list[float]:
    """Eine Soll-Karte, die nur noch Bauwerk gegen Hintergrund kennt — keine Tiefenstufen."""
    return [1.0 if (math.isfinite(w) and w < HINTERGRUND_AB_M) else HINTERGRUND_AB_M * 10
            for w in soll]


def _sobel(werte: Sequence[float], breite: int, hoehe: int):
    gx = [0.0] * (breite * hoehe)
    gy = [0.0] * (breite * hoehe)
    W = werte
    for y in range(1, hoehe - 1):
        o, m, u = (y - 1) * breite, y * breite, (y + 1) * breite
        for x in range(1, breite - 1):
            gx[m + x] = (W[o + x + 1] + 2 * W[m + x + 1] + W[u + x + 1]
                         - W[o + x - 1] - 2 * W[m + x - 1] - W[u + x - 1])
            gy[m + x] = (W[u + x - 1] + 2 * W[u + x] + W[u + x + 1]
                         - W[o + x - 1] - 2 * W[o + x] - W[o + x + 1])
    return gx, gy


def richtung(luminanz: Sequence[float], soll: Sequence[float], breite: int,
             hoehe: int) -> dict:
    """Laufen die Bildkanten parallel zu den Soll-Kanten? — siehe Moduldocstring.

    Returns:
        ``{status, richtung, richtung_abhebung, n}`` — ``status`` ``"ok"``,
        ``"keine_soll_kanten"`` oder ``"keine_bildkanten"`` (dann 0).
    """
    kanten = umriss.sprungkanten(soll, breite, hoehe)
    n_soll = sum(kanten)
    if n_soll == 0:
        return {"status": "keine_soll_kanten", "richtung": None, "richtung_abhebung": None,
                "n": 0}
    # Die Soll-Tiefe fuer den Gradienten: Hintergrund als etwas hinter der fernsten Geometrie,
    # damit der Umriss einen endlichen, gerichteten Sprung hat.
    endlich = [w for w in soll if math.isfinite(w) and w < HINTERGRUND_AB_M]
    fern = (max(endlich) * 1.5 + 1.0) if endlich else 1.0
    tiefe = [w if (math.isfinite(w) and w < HINTERGRUND_AB_M) else fern for w in soll]
    sgx, sgy = _sobel(tiefe, breite, hoehe)
    bgx, bgy = _sobel(luminanz, breite, hoehe)
    summe_gewicht = 0.0
    summe = 0.0
    for i, an in enumerate(kanten):
        if not an:
            continue
        sn = math.hypot(sgx[i], sgy[i])
        bn = math.hypot(bgx[i], bgy[i])
        if sn == 0 or bn == 0:
            continue
        cos = abs(sgx[i] * bgx[i] + sgy[i] * bgy[i]) / (sn * bn)
        summe += bn * cos
        summe_gewicht += bn
    if summe_gewicht == 0:
        return {"status": "keine_bildkanten", "richtung": 0.0, "richtung_abhebung": 0.0,
                "n": n_soll}
    wert = summe / summe_gewicht
    return {"status": "ok", "richtung": wert, "richtung_abhebung": wert / ZUFALL_RICHTUNG,
            "n": n_soll}


def flaechentrennung(luminanz: Sequence[float], flaechen: Sequence[int]) -> dict:
    """Welcher Anteil der Helligkeitsstreuung liegt zwischen den Flächen (η²)?

    Args:
        flaechen: je Pixel eine Flächennummer (z. B. aus der Material-ID-Farbe), gleiche
            Länge wie ``luminanz``.

    Returns:
        ``{status, eta2, n_flaechen}`` — ``eta2`` 0 bei einer grauen Fläche (keine Streuung).
    """
    if len(luminanz) != len(flaechen):
        raise ValueError("Bild und Flächenkarte sind verschieden lang.")
    n = len(luminanz)
    mittel = sum(luminanz) / n
    ss_gesamt = sum((w - mittel) ** 2 for w in luminanz)
    gruppen: dict[int, list[float]] = {}
    for w, f in zip(luminanz, flaechen):
        gruppen.setdefault(f, []).append(w)
    if ss_gesamt == 0:
        return {"status": "keine_streuung", "eta2": 0.0, "n_flaechen": len(gruppen)}
    ss_zwischen = sum(len(g) * (sum(g) / len(g) - mittel) ** 2 for g in gruppen.values())
    return {"status": "ok", "eta2": ss_zwischen / ss_gesamt, "n_flaechen": len(gruppen)}


def flaechen_aus_farben(farben: Sequence[Sequence[int]]) -> list[int]:
    """Material-ID-Farben → Flächennummern (gleiche Farbe, gleiche Fläche; Schwarz ist 0)."""
    nummer: dict[tuple, int] = {(0, 0, 0): 0}
    aus = []
    for f in farben:
        schluessel = tuple(f[:3])
        if schluessel not in nummer:
            nummer[schluessel] = len(nummer)
        aus.append(nummer[schluessel])
    return aus


def alle(luminanz: Sequence[float], soll: Sequence[float], breite: int, hoehe: int, *,
         flaechen: Sequence[int] | None = None) -> dict:
    """Alle Kandidaten für ein Bild. Fehlt die Flächenkarte, fehlt ``flaechentrennung``."""
    voll = umriss.umriss_treue(luminanz, soll, breite, hoehe)
    sil = umriss.umriss_treue(luminanz, _silhouette_soll(soll), breite, hoehe)
    rich = richtung(luminanz, soll, breite, hoehe)
    aus = {
        "umriss_abhebung": voll.get("abhebung"),
        "umriss_trefferquote": voll.get("trefferquote"),
        "umriss_praezision": voll.get("praezision"),
        "silhouette_abhebung": sil.get("abhebung"),
        "silhouette_trefferquote": sil.get("trefferquote"),
        "richtung": rich.get("richtung"),
        "richtung_abhebung": rich.get("richtung_abhebung"),
        "flaechentrennung": None,
        "urteilt": False,
    }
    if flaechen is not None:
        aus["flaechentrennung"] = flaechentrennung(luminanz, flaechen).get("eta2")
    return aus


def alle_aus_bericht(bild_png, bericht: dict) -> dict:
    """Dasselbe aus einem Blender-Bericht (``blender-report.json``) und einem Bild.

    Die Soll-Tiefe kommt wie überall aus :func:`bildlesen.tiefen_aus_report`, die Flächen aus
    dem Material-ID-Pass derselben Kamera. Eine andere Bildgrösse ist ein Befund, kein Fehler.
    """
    from aiimaging import bildlesen

    soll, breite, hoehe = bildlesen.tiefen_aus_report(bericht)
    luminanz, b, h = bildlesen.lies_png_luminanz(bild_png)
    if (b, h) != (breite, hoehe):
        return {"status": "groesse_passt_nicht", "urteilt": False,
                "grund": f"Bild {b}x{h}, Soll {breite}x{hoehe}."}
    flaechen = None
    mid = bericht.get("material_id_png")
    if mid:
        farben, fb, fh = bildlesen.lies_png_farben(mid)
        if (fb, fh) == (breite, hoehe):
            flaechen = flaechen_aus_farben(farben)
    return dict(alle(luminanz, soll, breite, hoehe, flaechen=flaechen), status="ok")


__all__ = ["ZUFALL_RICHTUNG", "alle", "alle_aus_bericht", "flaechen_aus_farben",
           "flaechentrennung", "richtung"]
