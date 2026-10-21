"""Farbabgleich: das KI-Bild bekommt die Farbstimmung des Cycles-Bilds — und sonst nichts.

**Anlass** (Entscheid 117, 21.10.2026, Variante A; Planblatt «Licht ins KI-Bild», Option D1):
Das KI-Bild liest nur die Tiefe; Licht und Farben der Stimmung sieht man nur im Cycles-Bild
(auf-20261021-296). Dieser Schritt bringt **Mittel und Streuung** jeder Farbachse des KI-Bilds
auf die des Cycles-Bilds. Er ist ein Messschalter (``vis.farbabgleich``, Vorgabe aus) und kein
Feld des Vertrags.

**Was er nicht tut, und das ist der Entwurf:** Kein Bildpunkt wandert. Jeder neue Farbwert
hängt nur vom alten Farbwert **desselben** Punkts und von sechs Zahlen für das ganze Bild ab
— keine Nachbarschaft, keine Maske, kein Weichzeichner. Darum kann sich an der Form nichts
verschieben (Grundsatz E97: das KI-Bild bleibt Entwurf, die Geometrie gehört dem Modell).

**Warum nicht in Lab und nicht je Bereich:**

* *Die Achsen sind Helligkeit Y (Rec.709, dieselbe Gewichtung, mit der*
  :func:`aiimaging.bildlesen.lies_png_luminanz` *liest) und zwei Farbdifferenzen* (B−Y, R−Y).
  Alle drei sind linear in R, G, B. Damit ist die neue Helligkeit eine **positive lineare
  Abbildung der alten** (``Y' = s·Y + c``, s > 0), und die Kantenprüfung
  (:func:`aiimaging.umriss.bildkanten`: Sobel, Schwelle als Quantil je Bild) findet dieselben
  Kanten — die Kantenstärken werden alle mit demselben ``s`` gestreckt, ihre Reihenfolge
  bleibt. In Lab wäre die Helligkeit nicht linear, und dieser Beweis ginge nicht.
  Abweichungen entstehen nur beim Runden auf 8 Bit und wo ein Kanal an 0 oder 255 anschlägt;
  beides wird gezählt (``geklippt_anteil``, ``kanten_iou``).
* *Nicht getrennt nach Haus, Boden, Himmel* (im Planblatt als D1 erwogen): Die Masken stammen
  aus dem Modell, das KI-Bild weicht davon ab (geom_iou 0,38–0,49 in 296). Drei Abgleiche mit
  verschiedenen Zahlen schüfen an jeder Maskengrenze, die nicht auf einer Bildkante liegt, eine
  **neue** Kante — also genau eine Formänderung.

Die Streckung je Achse ist auf :data:`STRECKUNG_GRENZEN` begrenzt: Ein fast einfarbiges
KI-Bild bekäme sonst eine zehnfache Streuung und Rauschen statt Farbe. Wo begrenzt wurde,
steht es im Vermerk.

Abhängigkeiten: nur :mod:`aiimaging.bildlesen`, :mod:`aiimaging.bildschreiben` und
:mod:`aiimaging.umriss` — reine stdlib, kein numpy (der Kern rechnet ohne, siehe
``pyproject.toml``). Laufzeit am 960 x 600-Bild im Container (21.10.2026): 2,7 s Abgleich und
1,0 s Kantenvergleich, ohne Lesen und Schreiben der Dateien; am Heim-PC fragt auf-20261021-298.
"""
from __future__ import annotations

import math
from pathlib import Path
from typing import Sequence

from . import bildlesen, bildschreiben, umriss

#: Die Rec.709-Gewichte — dieselben wie beim Lesen der Helligkeit (eine Quelle).
LR, LG, LB = bildlesen.LUMA_R, bildlesen.LUMA_G, bildlesen.LUMA_B

#: Kennung der Methode im Vermerk.
METHODE = "mittel_streuung_y_cb_cr_rec709_global"

#: Wie weit die Streuung einer Achse höchstens gestreckt oder gestaucht wird.
#: **Gesetzt, nicht gemessen** — 0,5 bis 2,0 lässt einen deutlichen Abgleich zu und
#: verhindert, dass ein fast einfarbiges Bild sein Rauschen verzehnfacht.
STRECKUNG_GRENZEN = (0.5, 2.0)

#: Die Achsen in der Reihenfolge des Vermerks.
ACHSEN = ("y", "cb", "cr")

#: Unterordner neben den Kamerabildern, in dem das KI-Bild **ohne** Abgleich liegen bleibt —
#: damit die Tafel beide zeigen kann und die Prüfung nachvollziehbar bleibt.
ORDNER_OHNE = "_ohne_farbabgleich"


class FarbabgleichError(ValueError):
    """Die beiden Bilder lassen sich nicht abgleichen (Grösse, leer)."""


def _achsen(farben: Sequence[Sequence[int]]) -> tuple[list[float], list[float], list[float]]:
    y = [LR * r + LG * g + LB * b for r, g, b in farben]
    cb = [f[2] - w for f, w in zip(farben, y)]
    cr = [f[0] - w for f, w in zip(farben, y)]
    return y, cb, cr


def _mittel_streuung(werte: Sequence[float]) -> tuple[float, float]:
    n = len(werte)
    if n == 0:
        raise FarbabgleichError("Ein Bild ohne Bildpunkte lässt sich nicht abgleichen.")
    mittel = math.fsum(werte) / n
    var = math.fsum((w - mittel) ** 2 for w in werte) / n
    return mittel, math.sqrt(max(var, 0.0))


def kennwerte(farben: Sequence[Sequence[int]]) -> dict:
    """Mittel und Streuung je Achse — ``{"y": {"mittel", "streuung"}, "cb": …, "cr": …}``."""
    aus = {}
    for name, werte in zip(ACHSEN, _achsen(farben)):
        m, s = _mittel_streuung(werte)
        aus[name] = {"mittel": round(m, 4), "streuung": round(s, 4)}
    return aus


def _streckung(s_ki: float, s_vorlage: float) -> tuple[float, bool]:
    unten, oben = STRECKUNG_GRENZEN
    if s_ki <= 1e-9:
        # Eine flache Achse hat nichts zu strecken; sie wird nur verschoben.
        return 1.0, False
    roh = s_vorlage / s_ki
    begrenzt = min(oben, max(unten, roh))
    return begrenzt, begrenzt != roh


def _abstand(a: dict, b: dict) -> float:
    """Wie weit zwei Kennwerte auseinanderliegen: euklidisch über Mittel und Streuung."""
    return round(math.sqrt(sum((a[k][f] - b[k][f]) ** 2
                               for k in ACHSEN for f in ("mittel", "streuung"))), 4)


def gleiche_ab(farben_ki: Sequence[Sequence[int]],
               farben_vorlage: Sequence[Sequence[int]]) -> tuple[list[tuple[int, int, int]], dict]:
    """Die reine Funktion: ``(neue Farben, Vermerk)``. Gleiche Länge, gleiche Reihenfolge.

    Jeder Ausgabepunkt ist eine Funktion allein seines Eingabepunkts (siehe Moduldocstring).
    Die Vorlage darf eine andere Grösse haben — von ihr werden nur sechs Zahlen gelesen; die
    Datei-Fassung :func:`gleiche_datei_ab` verlangt trotzdem gleiche Masse, weil ein
    Cycles-Bild in anderer Grösse auf einen anderen Ausschnitt deuten kann.
    """
    if not farben_ki or not farben_vorlage:
        raise FarbabgleichError("KI-Bild oder Vorlage ist leer.")
    y, cb, cr = _achsen(farben_ki)
    vor = kennwerte(farben_ki)
    ziel = kennwerte(farben_vorlage)
    abbildung = {}
    begrenzt = []
    for name, werte in zip(ACHSEN, (y, cb, cr)):
        m_k, s_k = _mittel_streuung(werte)
        m_v, s_v = ziel[name]["mittel"], ziel[name]["streuung"]
        s, grenze = _streckung(s_k, s_v)
        if grenze:
            begrenzt.append(name)
        # w' = (w - m_k) * s + m_v  =  s * w + c
        abbildung[name] = (s, m_v - s * m_k)
    (sy, cy), (sb, ccb), (sr, ccr) = abbildung["y"], abbildung["cb"], abbildung["cr"]
    neu: list[tuple[int, int, int]] = []
    geklippt = 0
    for wy, wb, wr in zip(y, cb, cr):
        ny = sy * wy + cy
        nb = sb * wb + ccb + ny
        nr = sr * wr + ccr + ny
        ng = (ny - LR * nr - LB * nb) / LG
        punkt = []
        for k in (nr, ng, nb):
            g = int(round(k))
            if g < 0 or g > 255:
                geklippt += 1
                g = 0 if g < 0 else 255
            punkt.append(g)
        neu.append((punkt[0], punkt[1], punkt[2]))
    nach = kennwerte(neu)
    vermerk = {
        "angewandt": True,
        "methode": METHODE,
        "vorlage": "cycles_schoenbild",
        "kennwerte_ki": vor,
        "kennwerte_vorlage": ziel,
        "kennwerte_nachher": nach,
        "streckung": {k: round(v[0], 4) for k, v in abbildung.items()},
        "begrenzt": begrenzt,
        "streckung_grenzen": list(STRECKUNG_GRENZEN),
        # «Nur Farbe nähert sich»: der Abstand zur Vorlage vorher und nachher.
        "abstand_vorher": _abstand(vor, ziel),
        "abstand_nachher": _abstand(nach, ziel),
        # Anteil der Kanalwerte, die an 0 oder 255 anschlugen — dort ist Y' nicht mehr genau
        # s·Y + c, und dort allein kann eine Kante kippen.
        "geklippt_anteil": round(geklippt / (3 * len(neu)), 6),
        "bildpunkte_verschoben": False,
    }
    return neu, vermerk


def kanten_iou(farben_a: Sequence[Sequence[int]], farben_b: Sequence[Sequence[int]],
               breite: int, hoehe: int) -> float | None:
    """Wie gleich die Kantenkarten zweier gleich grosser Bilder sind (1,0 = identisch).

    Dieselbe Kantenprüfung wie die Umrisstreue (:func:`aiimaging.umriss.bildkanten`).
    ``None``, wenn keines der beiden Bilder eine Kante hat.
    """
    def lum(farben):
        return [(LR * r + LG * g + LB * b) / 255.0 for r, g, b in farben]
    ka = umriss.bildkanten(lum(farben_a), breite, hoehe)
    kb = umriss.bildkanten(lum(farben_b), breite, hoehe)
    beide = sum(1 for a, b in zip(ka, kb) if a and b)
    eines = sum(1 for a, b in zip(ka, kb) if a or b)
    return None if eines == 0 else round(beide / eines, 6)


def gleiche_datei_ab(ki_png, vorlage_png, ziel_png, *, kanten_pruefen: bool = True) -> dict:
    """Die Datei-Fassung: KI-Bild lesen, abgleichen, nach ``ziel_png`` schreiben.

    ``ziel_png`` darf ``ki_png`` sein (dann wird überschrieben — der Aufrufer legt das
    Original vorher ab). Fehlt die Vorlage oder passt die Grösse nicht, wird **nichts**
    geschrieben, und der Vermerk sagt warum (``angewandt: False``, ``grund``): Ein Bild ohne
    Abgleich ist ein gültiges Bild, ein Abgleich gegen einen anderen Ausschnitt nicht.
    """
    if not vorlage_png or not Path(vorlage_png).is_file():
        return {"angewandt": False, "methode": METHODE,
                "grund": "Kein Cycles-Bild (Schoenbild) zu dieser Kamera — es gibt keine "
                         "Vorlage, an die die Farben angeglichen werden koennten."}
    farben_ki, b_k, h_k = bildlesen.lies_png_farben(ki_png)
    farben_v, b_v, h_v = bildlesen.lies_png_farben(vorlage_png)
    if (b_k, h_k) != (b_v, h_v):
        return {"angewandt": False, "methode": METHODE,
                "grund": f"KI-Bild {b_k}x{h_k}, Cycles-Bild {b_v}x{h_v}: ungleiche Masse "
                         f"koennen auf einen anderen Ausschnitt deuten, und ein Abgleich "
                         f"dagegen waere eine stille Annahme."}
    neu, vermerk = gleiche_ab(farben_ki, farben_v)
    if kanten_pruefen:
        vermerk["kanten_iou"] = kanten_iou(farben_ki, neu, b_k, h_k)
    bildschreiben.schreibe_farb_png(ziel_png, neu, b_k, h_k)
    vermerk["breite"], vermerk["hoehe"] = b_k, h_k
    return vermerk


__all__ = ["ACHSEN", "FarbabgleichError", "METHODE", "ORDNER_OHNE", "STRECKUNG_GRENZEN",
           "gleiche_ab", "gleiche_datei_ab", "kanten_iou", "kennwerte"]
