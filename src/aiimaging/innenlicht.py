"""Licht für eine Kamera im Raum — und die Helligkeit jedes Blender-Bilds, gemessen.

**Anlass (Generalprobe auf-20261027-373, S9 / B8):** Der IFC-Weg mit Innenraum lief durch,
aber das Schönbild der Kamera «Innenraum» war **schwarz** (mittlere Helligkeit 1 von 255).
Der Runner beleuchtet jede Szene von aussen — Sonne und Himmel (Himmelsbild oder kühles
Umgebungslicht). Im Raum kommt davon nur an, was durch Glas fällt. Die IFC der Probe
(``demohaus-r57.ifc``) füllt aber jede Öffnung mit einem **deckenden** Körper — Fenster und
Türen sind Quader ohne Scheibe (im Bild «Fenster als Holzfelder»). Der Raum ist damit eine
geschlossene Kiste: kein Strahl der Sonne und keiner des Himmels erreicht die Kamera.
Der frühere Innenraum (auf-20260922-141, auf-20261001-230) war eine andere Datei; wie dort
Licht hineinkam, ist nicht nachgemessen.

**Was dieses Modul entscheidet — rein, ohne ``bpy`` (Regel 4):**

* :func:`lage` — steht die Kamera *innen*, *aussen* oder *in einem Bauteil*? Gelesen an zehn
  Strahlen, die der Runner von der Kamera aus schiesst (Decke, Boden, acht Richtungen in der
  Waagrechten): Innen ist, wer eine Decke über sich hat und ringsum Wände.
* :func:`lichtplan` — wo die Raumleuchte hängt: eine Fläche knapp unter der Decke, über der
  Raummitte, so gross wie ein Teil des Raums, mit einer Startleistung je Bodenfläche.
* :func:`nachstellen` — um welchen Faktor die Leistung nach einer kleinen Vorprobe steigt
  oder sinkt, damit das Bild die Zielhelligkeit trifft. Die Startleistung ist gesetzt, nicht
  gemessen; erst die Vorprobe misst — mit Material, Tonwertkurve und Belichtung dieses Laufs.
* :func:`helligkeit` — die mittlere Helligkeit eines Bilds in Grauwerten (0–255), für den
  Blender-Bericht **jeder** Kamera.
* :func:`vermerk` — der Satz für ``verdict.hinweise``, mit «INNENBILD ZU DUNKEL», wenn eine
  Innenkamera trotz allem unter :data:`ZU_DUNKEL_255` bleibt.

**Aussen ändert sich nichts.** Eine Kamera, die nicht als innen erkannt ist, bekommt kein
Licht; ihr Bild wird nur gemessen.
"""
from __future__ import annotations

import math
from collections.abc import Mapping, Sequence

_D = math.sqrt(0.5)

#: Die zehn Strahlen von der Kamera aus (Welt, z oben). Die Namen der Waagrechten sind
#: Himmelsrichtungen in Blender-Achsen (+x Ost, +y Nord) — nur Namen, keine Aussage über
#: den Norden des Bauwerks.
STRAHLEN: dict[str, tuple[float, float, float]] = {
    "oben": (0.0, 0.0, 1.0), "unten": (0.0, 0.0, -1.0),
    "o": (1.0, 0.0, 0.0), "no": (_D, _D, 0.0), "n": (0.0, 1.0, 0.0), "nw": (-_D, _D, 0.0),
    "w": (-1.0, 0.0, 0.0), "sw": (-_D, -_D, 0.0), "s": (0.0, -1.0, 0.0), "so": (_D, -_D, 0.0),
}
WAAGRECHT: tuple[str, ...] = ("o", "no", "n", "nw", "w", "sw", "s", "so")

#: Höchstens so hoch darf die Decke über dem Auge liegen, damit sie als Decke gilt. Ein
#: Geschoss misst 2,4–4 m; 8 m lassen eine Halle zu, aber keinen Baum über der Strasse.
DECKE_HOECHSTENS_M = 8.0
#: Höchstens so weit darf eine Wand in der Waagrechten liegen. Weiter weg ist kein Raum mehr.
WAND_HOECHSTENS_M = 30.0
#: Mindestens so viele der acht Waagrechten müssen eine Wand treffen. Eine offene Tür oder ein
#: Durchgang darf zwei Strahlen entkommen lassen; eine Kamera vor einer Fassade unter einem
#: Vordach trifft drei bis fünf.
MIN_WAENDE = 6
#: Ein Treffer von der **Rückseite** einer Fläche so nah heisst: Das Auge steckt im Körper.
BAUTEIL_HOECHSTENS_M = 0.6
#: Mindestens so viele der neun Strahlen (Decke und Waagrechte) müssen dafür von hinten treffen.
MIN_RUECKSEITEN = 5

#: Startleistung der Raumleuchte je m² geschätzter Bodenfläche (Blender-Watt). **Gesetzt,
#: nicht gemessen** — die Vorprobe stellt nach (:func:`nachstellen`).
LEISTUNG_JE_M2_W = 60.0
LEISTUNG_MIN_W = 100.0
LEISTUNG_MAX_W = 20000.0
#: Wie viel der Raumbreite die Leuchte einnimmt, und ihre Grenzen.
LEUCHTE_ANTEIL = 0.6
LEUCHTE_MIN_M = 0.5
LEUCHTE_MAX_M = 6.0
#: So weit hängt die Leuchte unter der getroffenen Decke.
LEUCHTE_UNTER_DECKE_M = 0.03
#: Fehlt ein Strahl (Tür offen), gilt diese halbe Raumbreite.
HALBE_BREITE_ERSATZ_M = 2.0
#: Die Lichtfarbe — ein neutrales, leicht warmes Weiss (keine Messung, eine Setzung).
LICHTFARBE = (1.0, 0.95, 0.88)

#: Die Helligkeit, auf die die Vorprobe zielt (mittlerer Grauwert von 255): ein heller,
#: nicht ausgebrannter Innenraum. Gesetzt.
ZIEL_255 = 115.0
#: Unter diesem Mittel heisst ein Innenbild «zu dunkel». 373 lag bei 1; ein Raum, in dem
#: Wände und Boden zu erkennen sind, liegt erfahrungsgemäss über 60. Gesetzt.
ZU_DUNKEL_255 = 35.0
#: Der Faktor einer Nachstellung bleibt zwischen 1/16 und 16 (vier Blenden je Richtung).
FAKTOR_GRENZE = 16.0
#: Unter dieser Abweichung (in Blenden) wird nicht mehr nachgestellt.
GENAU_GENUG_EV = 0.25
#: Höchstens so viele Bildpunkte liest :func:`helligkeit` (gleichmässig ausgedünnt).
HELLIGKEIT_HOECHSTENS_PUNKTE = 60000

#: Der Anfang der Sätze in ``verdict.hinweise`` — Proben und Auswerter suchen danach.
SATZ_ZU_DUNKEL = "INNENBILD ZU DUNKEL"
SATZ_IN_BAUTEIL = "INNENKAMERA IN EINEM BAUTEIL"
SATZ_INNENLICHT = "INNENLICHT"

LAGE_INNEN = "innen"
LAGE_AUSSEN = "aussen"
LAGE_IN_BAUTEIL = "in_bauteil"
LAGE_UNBEKANNT = "unbekannt"


def _treffer(treffer: Mapping, name: str) -> tuple[float | None, bool]:
    """``(abstand_m, rueckseite)`` eines Strahls — ``(None, False)``, wenn er nichts traf."""
    t = treffer.get(name) if isinstance(treffer, Mapping) else None
    if not isinstance(t, Mapping):
        return None, False
    try:
        d = float(t.get("abstand_m"))
    except (TypeError, ValueError):
        return None, False
    if not math.isfinite(d) or d < 0.0:
        return None, False
    return d, bool(t.get("rueckseite"))


def lage(treffer: Mapping | None) -> dict:
    """Steht die Kamera innen, aussen oder in einem Bauteil?

    Args:
        treffer: je Name aus :data:`STRAHLEN` ``{abstand_m, rueckseite}`` oder ``None`` (der
            Strahl traf nichts). ``rueckseite`` heisst: Die getroffene Fläche zeigt von der
            Kamera weg — der Strahl kam von innerhalb eines Körpers.

    Returns:
        ``{lage, decke_m, boden_m, waende, rueckseiten, grund}``. ``lage`` ist
        :data:`LAGE_INNEN`, :data:`LAGE_AUSSEN`, :data:`LAGE_IN_BAUTEIL` oder
        :data:`LAGE_UNBEKANNT` (keine Strahlen — nicht gemessen, nie «aussen»).
    """
    if not isinstance(treffer, Mapping) or not treffer:
        return {"lage": LAGE_UNBEKANNT, "decke_m": None, "boden_m": None, "waende": None,
                "rueckseiten": None,
                "grund": "Keine Strahlen geschossen — die Lage der Kamera ist NICHT GEMESSEN."}
    decke, decke_hinten = _treffer(treffer, "oben")
    boden, _ = _treffer(treffer, "unten")
    rueckseiten = 0
    for n in ("oben",) + WAAGRECHT:
        d, hinten = _treffer(treffer, n)
        if d is not None and hinten and d <= BAUTEIL_HOECHSTENS_M:
            rueckseiten += 1
    waende = 0
    for n in WAAGRECHT:
        d, hinten = _treffer(treffer, n)
        if d is not None and not hinten and d <= WAND_HOECHSTENS_M:
            waende += 1
    befund = {"decke_m": None if decke is None else round(decke, 3),
              "boden_m": None if boden is None else round(boden, 3),
              "waende": waende, "rueckseiten": rueckseiten}
    if rueckseiten >= MIN_RUECKSEITEN:
        return dict(befund, lage=LAGE_IN_BAUTEIL,
                    grund=(f"{rueckseiten} von 9 Strahlen treffen eine Fläche von hinten, "
                           f"keine weiter als {BAUTEIL_HOECHSTENS_M:g} m — das Auge steckt in "
                           f"einer Wand oder Decke."))
    hat_decke = decke is not None and not decke_hinten and decke <= DECKE_HOECHSTENS_M
    if hat_decke and waende >= MIN_WAENDE:
        return dict(befund, lage=LAGE_INNEN,
                    grund=(f"Decke {decke:.2f} m über dem Auge, Wände in {waende} von 8 "
                           f"Richtungen — die Kamera steht in einem Raum."))
    return dict(befund, lage=LAGE_AUSSEN,
                grund=("keine Decke über dem Auge" if not hat_decke else
                       f"Wände nur in {waende} von 8 Richtungen (nötig {MIN_WAENDE})"))


def lichtplan(auge: Sequence[float], treffer: Mapping) -> dict:
    """Wo die Raumleuchte hängt, wie gross sie ist und mit welcher Leistung sie beginnt.

    Die Leuchte liegt :data:`LEUCHTE_UNTER_DECKE_M` unter der getroffenen Decke, über der Mitte
    zwischen den Wänden in Ost-West und Nord-Süd (nicht über dem Auge: eine Kamera nahe der
    Wand bekäme sonst ein Licht, das nur die Wand hinter ihr trifft).
    """
    ax, ay, az = (float(v) for v in auge)
    decke, _ = _treffer(treffer, "oben")
    if decke is None:
        raise ValueError("Ohne Decke über dem Auge gibt es keinen Lichtplan.")

    def halb(n: str) -> float:
        d, hinten = _treffer(treffer, n)
        return HALBE_BREITE_ERSATZ_M if d is None or hinten or d > WAND_HOECHSTENS_M else d

    o, w, n, s = halb("o"), halb("w"), halb("n"), halb("s")
    breite_x, breite_y = o + w, n + s
    groesse_x = min(LEUCHTE_MAX_M, max(LEUCHTE_MIN_M, breite_x * LEUCHTE_ANTEIL))
    groesse_y = min(LEUCHTE_MAX_M, max(LEUCHTE_MIN_M, breite_y * LEUCHTE_ANTEIL))
    flaeche = breite_x * breite_y
    leistung = min(LEISTUNG_MAX_W, max(LEISTUNG_MIN_W, LEISTUNG_JE_M2_W * flaeche))
    return {"ort": [round(ax + (o - w) / 2.0, 4), round(ay + (n - s) / 2.0, 4),
                    round(az + decke - LEUCHTE_UNTER_DECKE_M, 4)],
            "groesse_m": [round(groesse_x, 3), round(groesse_y, 3)],
            "raum_m": [round(breite_x, 3), round(breite_y, 3)],
            "bodenflaeche_m2": round(flaeche, 2),
            "leistung_w": round(leistung, 1), "farbe": list(LICHTFARBE)}


def _linear(g255: float) -> float:
    """Ein sRGB-Grauwert (0–255) als lineare Helligkeit (0–1)."""
    c = max(0.0, min(1.0, float(g255) / 255.0))
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def nachstellen(mittel_255: float | None, leistung_w: float, *,
                ziel_255: float = ZIEL_255) -> dict:
    """Um welchen Faktor die Leuchte heller oder dunkler wird, damit das Bild das Ziel trifft.

    Gerechnet im Linearen (das Licht addiert sich linear; der Grauwert ist sRGB-kodiert). Die
    Tonwertkurve (AgX/Filmic) ist nicht linear — darum höchstens zwei Runden im Runner und
    der Faktor in :data:`FAKTOR_GRENZE`.

    Returns:
        ``{faktor, leistung_w, abweichung_ev, fertig}`` — ``fertig`` heisst: näher als
        :data:`GENAU_GENUG_EV` am Ziel, nichts mehr zu tun.
    """
    if mittel_255 is None:
        return {"faktor": 1.0, "leistung_w": float(leistung_w), "abweichung_ev": None,
                "fertig": True}
    ist = _linear(mittel_255)
    soll = _linear(ziel_255)
    if ist <= 1e-6:
        faktor = FAKTOR_GRENZE
        abweichung = None
    else:
        abweichung = math.log2(ist / soll)
        if abs(abweichung) < GENAU_GENUG_EV:
            return {"faktor": 1.0, "leistung_w": float(leistung_w),
                    "abweichung_ev": round(abweichung, 3), "fertig": True}
        faktor = soll / ist
    faktor = max(1.0 / FAKTOR_GRENZE, min(FAKTOR_GRENZE, faktor))
    return {"faktor": round(faktor, 4), "leistung_w": round(float(leistung_w) * faktor, 1),
            "abweichung_ev": None if abweichung is None else round(abweichung, 3),
            "fertig": False}


def helligkeit(pixel: Sequence[float], kanaele: int = 4, *,
               hoechstens: int = HELLIGKEIT_HOECHSTENS_PUNKTE) -> dict:
    """Die mittlere Helligkeit eines Bilds in Grauwerten (0–255).

    ``pixel`` ist die flache Liste, wie Blender sie liefert (``Image.pixels``: Werte 0–1, je
    Punkt ``kanaele`` Werte); bei einer 8-Bit-PNG sind es die gespeicherten, sRGB-kodierten
    Werte. Gewichtet nach Rec. 709 (0,2126 R + 0,7152 G + 0,0722 B) auf den kodierten Werten —
    dasselbe Mass wie «mittlere Helligkeit 1 von 255» in 373. Alpha zählt nicht.

    Returns:
        ``{mittel_255, n}`` — ``mittel_255`` ``None`` bei einem leeren Bild.
    """
    k = int(kanaele)
    if k < 3:
        raise ValueError(f"Mindestens drei Kanäle nötig, waren {k}.")
    punkte = len(pixel) // k
    if punkte <= 0:
        return {"mittel_255": None, "n": 0}
    schritt = max(1, -(-punkte // max(1, int(hoechstens))))   # aufgerundet
    summe = 0.0
    n = 0
    for p in range(0, punkte, schritt):
        i = p * k
        summe += 0.2126 * pixel[i] + 0.7152 * pixel[i + 1] + 0.0722 * pixel[i + 2]
        n += 1
    return {"mittel_255": round(summe / n * 255.0, 2), "n": n}


def zu_dunkel(mittel_255) -> bool:
    """Liegt dieses Mittel unter :data:`ZU_DUNKEL_255`? ``None`` (nicht gemessen) ist nie dunkel."""
    try:
        return float(mittel_255) < ZU_DUNKEL_255
    except (TypeError, ValueError):
        return False


def vermerk(bericht: Mapping | None, kamera) -> dict | None:
    """Der Vermerk einer Kamera aus ihrem Blender-Bericht — ``{kamera, satz, …}`` oder ``None``.

    Nur für Kameras, die als innen oder in einem Bauteil erkannt sind; eine Aussenkamera
    bekommt keinen Satz (ihre Helligkeit steht nur im Bericht).
    """
    if not isinstance(bericht, Mapping):
        return None
    innen = bericht.get("innenlicht")
    if not isinstance(innen, Mapping):
        return None
    wo = innen.get("lage")
    mittel = (bericht.get("helligkeit") or {}).get("mittel_255") \
        if isinstance(bericht.get("helligkeit"), Mapping) else None
    name = str(kamera)
    if wo == LAGE_IN_BAUTEIL:
        satz = (f"{SATZ_IN_BAUTEIL}, Kamera {name!r}: {innen.get('grund')} Der Standpunkt "
                f"muss in den Raum gerückt werden.")
    elif wo == LAGE_INNEN:
        if zu_dunkel(mittel):
            satz = (f"{SATZ_ZU_DUNKEL}, Kamera {name!r}: mittlere Helligkeit {mittel:.0f} von "
                    f"255 (Schwelle {ZU_DUNKEL_255:.0f}), obwohl eine Raumleuchte gesetzt "
                    f"war — das Bild taugt nicht als Grundlage.")
        else:
            leuchte = innen.get("leuchte") or {}
            satz = (f"{SATZ_INNENLICHT}, Kamera {name!r}: Kamera im Raum, Tageslicht kommt "
                    f"nicht hinein — Raumleuchte an der Decke gesetzt"
                    + (f" ({float(leuchte['leistung_w']):.0f} W)"
                       if leuchte.get("leistung_w") is not None else "")
                    + (f", mittlere Helligkeit {mittel:.0f} von 255." if mittel is not None
                       else "."))
    else:
        return None
    return {"kamera": name, "lage": wo, "mittel_255": mittel,
            "zu_dunkel": wo == LAGE_INNEN and zu_dunkel(mittel), "satz": satz}


def vermerk_satz(v) -> str:
    """Der Satz eines :func:`vermerk` für ``verdict.hinweise`` — oder ``""``."""
    if not isinstance(v, Mapping) or not isinstance(v.get("satz"), str):
        return ""
    return v["satz"]
