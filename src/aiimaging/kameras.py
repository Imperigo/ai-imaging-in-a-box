"""KAMERAS — wo eine Kamera stehen muss, damit das Gebäude im Bild ist.

Warum dieses Modul existiert
----------------------------
Der Vorläufer KosmoVis hat diese Rechnung schon einmal gelöst, und zwar gut. Die
Bestandsaufnahme (``docs/BLENDER_ADDON_BESTAND_2026-08-18.md``, Teil A.1/A.2) hat sie
in 83 Modulen gefunden: ``archviz_pipeline_v6_camera_math.py`` und ihren Vorläufer
``archviz_camera.py``. Beide liegen jenseits einer ``import bpy``-Zeile, die zwei ihrer
vier Funktionen gar nicht brauchen. Dieses Modul ist der Nachbau der rechnenden Hälfte
diesseits der Grenze — mit den Verbesserungen, die beim Vergleich der beiden Fassungen
sichtbar wurden.

Was hier NICHT drin ist: der Verdeckungstest per Strahlenschuss. Der braucht die Szene
und gehört in den Runner. Was hier drin ist, ist seine **Schrittlogik** — die
Sichtprüfung wird als Funktion hereingereicht (``_sicht_frei``), damit der Ablauf ohne
Blender prüfbar bleibt. Das ist die Trennung, die der Bestand nicht macht.

Der Kameravertrag — eine Entscheidung, keine Fundsache
-------------------------------------------------------
Der Bestand trägt **drei unvereinbare Kameraverträge und drei Augenhöhen**:
``look_at`` gegen ``rotation_euler`` gegen ``azimut``/``elevation``; 1.70 m absolut
gegen 1.70 m über dem Gebäudefuss gegen 1.65 m. Das ist keine Rundung, sondern eine
andere Annahme über den Menschen im Bild. Hier gilt:

* **``blick_auf`` ist die führende Form.** Ein Blickziel ist erklärbar und unabhängig
  von Rotationskonventionen. Eine Blender-Rotation lässt sich daraus jederzeit ableiten;
  zurück geht es **nicht** eindeutig, weil ein Blickvektor keine Zielentfernung kennt.
  Wer die verlustbehaftete Form führt, kann die andere nie zurückgewinnen.
* **Die Augenhöhe ist absolut und misst 1.70 m.** Absolut, weil der Betrachter auf dem
  Gelände steht und nicht auf der Unterkante der Hüllbox — bei einem Gebäude mit
  Untergeschoss sind das zwei verschiedene Orte. 1.70 m, weil das ausgereifteste
  Verfahren des Bestands und die Mehrheit der Fundstellen es so halten.

Was dieses Modul bewusst *nicht* tut
------------------------------------
Es setzt keine Kamera. Es rechnet Positionen und gibt sie mit ihrer Begründung zurück.
Das Setzen ist Sache des Runners jenseits der Prozessgrenze.

Abhängigkeiten: keine. Reine stdlib, kein numpy, kein ``bpy`` (Regel 2), aus Python
heraus ohne jede Oberfläche aufrufbar (Regel 4).
"""
from __future__ import annotations

import math

from .torwaechter import _lies_bbox

# --------------------------------------------------------------------------------------
# Die Zahlen, und warum sie so stehen
# --------------------------------------------------------------------------------------

#: Sensorbreite in Millimetern. 36 mm ist Kleinbild — die Bezugsgrösse, auf die sich
#: jede Brennweitenangabe in der Architekturfotografie stillschweigend bezieht.
SENSOR_BREITE_MM = 36.0

#: Vorgabe-Brennweite. 28 mm ist der Weitwinkel, mit dem Gebäude fotografiert werden,
#: ohne dass die Fluchten kippen. Der Bestand nutzt 28 mm (V6) und 35 mm (Vorläufer);
#: 28 mm gewinnt, weil es zum engeren Standort auf der Strasse passt.
BRENNWEITE_MM = 28.0

#: Augenhöhe in Metern, **absolut** — siehe Modulkopf. Nicht über dem Gebäudefuss.
AUGENHOEHE_M = 1.70

#: Anteil des Bildes, den das Gebäude füllen soll. Ein Wert unter 1 schiebt die Kamera
#: weiter weg und lässt Luft — das ist die „2/3-Komposition" als Zahl. 0.55 stammt aus
#: dem Bestand und ist dort erprobt.
DECKUNGSGRAD = 0.55

#: Sicherheitsrand beim Eckentest: 8 % des Bildes bleiben frei. Ohne ihn sitzt eine
#: Gebäudeecke rechnerisch genau auf der Bildkante — und liegt nach der ersten
#: Objektivverzeichnung draussen.
BILDRAND = 0.92

#: Das Blickziel liegt nicht auf Augenhöhe, sondern um diesen Anteil der Gebäudehöhe
#: darüber. Die Kamera kippt dadurch leicht nach oben, das Gebäude sitzt tiefer im Bild.
#: Der übliche Griff der Architekturfotografie.
ZIEL_ANTEIL_HOEHE = 0.20

#: Mindestabstand zur Fassade in Metern, zusätzlich zur halben Grundrissseite. Verhindert,
#: dass die analytische Rechnung eine Kamera in die Wand stellt.
WANDABSTAND_M = 10.0

#: Seitlicher Versatz bei frontalen Ansichten, als Anteil der Gebäudebreite. Eine exakt
#: mittige Frontale ist symmetrisch und damit bildlich tot.
FRONTAL_VERSATZ = 0.10

#: Vorgabe für ``bias_grad`` — siehe ``richtungen``.
BIAS_GRAD = 35.0

#: Höchstzahl der Rückschub-Durchläufe. Danach wird die letzte Position geliefert und
#: als unvollkommen gekennzeichnet. Verweigern wäre schlechter: eine Kamera, die knapp
#: schneidet, ist brauchbarer als keine.
MAX_DURCHLAEUFE = 20

#: Punkte näher als das gelten als hinter der Kamera. Nicht 0, weil die perspektivische
#: Division dort gegen unendlich läuft.
MIN_TIEFE_M = 0.5

#: Anteil der Reststrecke je Schritt beim Heranziehen vor einer Verdeckung.
ZIEH_SCHRITT = 0.12

#: Untergrenze beim Heranziehen. Näher als 6 m an das Blickziel ergibt kein Gebäudebild
#: mehr, sondern einen Fassadenausschnitt.
MIN_ZIEH_ABSTAND_M = 6.0

#: Sicherheitsabstand um die Hüllbox beim Heranziehen. Die Kamera darf nie hinein.
HUELLBOX_PUFFER_M = 3.0

#: Höchstzahl der Zieh-Schritte.
MAX_ZIEH_SCHRITTE = 8


# --------------------------------------------------------------------------------------
# Vektorrechnung, klein gehalten
# --------------------------------------------------------------------------------------

def _minus(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _plus(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def _mal(a, s):
    return (a[0] * s, a[1] * s, a[2] * s)


def _punkt(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _kreuz(a, b):
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def _laenge(a):
    return math.sqrt(_punkt(a, a))


def _normiert(a):
    """Einheitsvektor, oder ``None`` bei Nulllänge.

    ``None`` statt einer Ausnahme, weil der einzige Weg hierher ein entarteter Fall ist
    (Kamera exakt im Blickziel), den die Aufrufer als Befund melden sollen — nicht als
    Absturz.
    """
    laenge = _laenge(a)
    if laenge <= 0.0 or not math.isfinite(laenge):
        return None
    return (a[0] / laenge, a[1] / laenge, a[2] / laenge)


# --------------------------------------------------------------------------------------
# Bildwinkel
# --------------------------------------------------------------------------------------

def bildwinkel(brennweite_mm: float = BRENNWEITE_MM, *,
               seitenverhaeltnis: float = 16 / 9,
               sensor_breite_mm: float = SENSOR_BREITE_MM) -> tuple[float, float]:
    """Brennweite → ``(horizontal, vertikal)`` als Öffnungswinkel im Bogenmass.

    Der vertikale Winkel wird aus dem **Seitenverhältnis** abgeleitet, nicht aus einer
    festen Sensorhöhe. Das ist der Punkt, an dem die Bildproportion überhaupt in die
    Rechnung eingeht: Ein 16:9-Bild braucht bei gleichem Gebäude einen anderen Abstand
    als ein 4:3-Bild. Die Hauptfundstelle des Bestands rechnet mit fest verdrahteten
    27 mm Sensorhöhe und übersieht das; ihr Vorläufer macht es richtig. Hier gewinnt
    der Vorläufer.

    Raises:
        ValueError: Brennweite, Seitenverhältnis oder Sensorbreite nicht positiv-endlich.
            Ein Bildwinkel aus einer Brennweite von 0 wäre 180° — eine Zahl, die
            entsteht, aber nichts bedeutet.
    """
    for name, wert in (("brennweite_mm", brennweite_mm),
                       ("seitenverhaeltnis", seitenverhaeltnis),
                       ("sensor_breite_mm", sensor_breite_mm)):
        if not isinstance(wert, (int, float)) or isinstance(wert, bool):
            raise ValueError(f"{name} muss eine Zahl sein, war: {wert!r}")
        if not math.isfinite(float(wert)) or float(wert) <= 0.0:
            raise ValueError(f"{name} muss positiv und endlich sein, war: {wert!r}")

    sensor_hoehe_mm = sensor_breite_mm / seitenverhaeltnis
    hfov = 2.0 * math.atan(sensor_breite_mm / (2.0 * brennweite_mm))
    vfov = 2.0 * math.atan(sensor_hoehe_mm / (2.0 * brennweite_mm))
    return hfov, vfov


# --------------------------------------------------------------------------------------
# Richtungen
# --------------------------------------------------------------------------------------

#: Die zwölf Richtungen: Kürzel → (Grundazimut in Grad, Vielfaches von ``bias_grad``).
#:
#: Der Azimut zählt im Uhrzeigersinn ab Nord und beschreibt, **wo die Kamera steht** —
#: ``n`` heisst: nördlich des Gebäudes, mit Blick nach Süden.
#:
#: Vier frontal, senkrecht auf eine Fassade. Acht diagonal: Primärrichtung, dann um
#: ``bias_grad`` in einen Quadranten gedreht. ``nNE`` liest sich als „von Norden, nach
#: Nordost gedreht" — die Nordfassade führt, die Ostfassade begleitet.
#:
#: **Diese Vorzeichen sind die Stelle, an der sich der Bestand nachweislich vertan hat**
#: (die N/S-Diagonalen waren invertiert und tragen dort einen Korrekturkommentar). Darum
#: stehen sie hier als Tabelle statt als Rechnung, und darum prüft der Test jede der acht
#: Diagonalen bei ``bias_grad=45`` gegen ihre Himmelsrichtung.
RICHTUNGEN = {
    "n":   (0.0, 0),
    "e":   (90.0, 0),
    "s":   (180.0, 0),
    "w":   (270.0, 0),
    "nNE": (0.0, +1),
    "nNW": (0.0, -1),
    "eEN": (90.0, -1),
    "eES": (90.0, +1),
    "sSE": (180.0, -1),
    "sSW": (180.0, +1),
    "wWS": (270.0, -1),
    "wWN": (270.0, +1),
}

#: Die zwölf Kürzel in der Reihenfolge, in der sie ausgegeben werden: erst die vier
#: Frontalen, dann die acht Diagonalen im Uhrzeigersinn ab Nord.
RICHTUNGSFOLGE = ("n", "e", "s", "w",
                  "nNE", "eEN", "eES", "sSE", "sSW", "wWS", "wWN", "nNW")


def richtungen(bias_grad: float = BIAS_GRAD) -> dict:
    """Die zwölf Kürzel → Azimut in Grad.

    ``bias_grad`` regelt das Verhältnis der beiden sichtbaren Fassaden bei den
    Diagonalen — das ist architektonisches Bildwissen, keine Programmierung:

    * **30°** — die primäre Fassade dominiert, etwa 2/3 zu 1/3.
    * **35°** — ausgewogen, etwa 60/40. Vorgabe.
    * **45°** — echter Eckblick, 50/50. Bei genau 45° fallen je zwei Diagonalen auf
      dieselbe Himmelsrichtung; aus zwölf Richtungen werden acht verschiedene Blicke.
      Das ist kein Fehler, sondern die Aussage des Reglers.

    Raises:
        ValueError: ``bias_grad`` liegt nicht in ``(0, 90)``. Bei 0 fällt die Diagonale
            mit der Frontalen zusammen, bei 90 mit der nächsten Frontalen — in beiden
            Fällen entstünden Doppelbilder statt Eckblicken.
    """
    if isinstance(bias_grad, bool) or not isinstance(bias_grad, (int, float)):
        raise ValueError(f"bias_grad muss eine Zahl sein, war: {bias_grad!r}")
    bias = float(bias_grad)
    if not math.isfinite(bias) or not (0.0 < bias < 90.0):
        raise ValueError(
            f"bias_grad muss zwischen 0 und 90 Grad liegen (ausschliesslich), war: {bias}. "
            "Bei 0 fiele die Diagonale auf die Frontale, bei 90 auf die nächste Frontale."
        )
    return {kuerzel: (grund + faktor * bias) % 360.0
            for kuerzel, (grund, faktor) in RICHTUNGEN.items()}


def _achsen_aus_azimut(azimut_grad: float) -> tuple[tuple, tuple]:
    """Azimut → ``(standort_richtung, blick_richtung)`` in der XY-Ebene.

    Nord ist ``+Y``, Ost ``+X``, gezählt im Uhrzeigersinn — die Konvention des Kompasses,
    nicht die des Einheitskreises. Wer hier ``cos``/``sin`` vertauscht, dreht die ganze
    Anlage um 90°, und zwar unauffällig.
    """
    a = math.radians(azimut_grad)
    standort = (math.sin(a), math.cos(a), 0.0)
    return standort, (-standort[0], -standort[1], 0.0)


def sichtbare_breite(masse, azimut_grad: float) -> float:
    """Wie breit das Gebäude aus dieser Richtung erscheint, in Metern.

    Die Hüllbox ist achsparallel; aus schräger Sicht wird ihre Silhouette breiter als
    jede einzelne Seite. Die Breite quer zur Blickrichtung ist ``|dx·sin a| + |dy·cos a|``
    — für die Frontale genau ``dx`` bzw. ``dy``, für die 45°-Ecke eines quadratischen
    Grundrisses genau die Diagonale.

    **Das ist eine Verbesserung gegenüber dem Bestand, keine Übernahme.** Dort steht
    ``max(breite, tiefe, grundriss_diagonale)`` — und weil die Diagonale eines Rechtecks
    *immer* mindestens so gross ist wie jede seiner Seiten, gewinnt sie ausnahmslos. Das
    ``max`` ist toter Code, und die Folge ist eine Kamera, die auch bei der Frontalen auf
    Diagonalabstand steht. Bei einem 60 × 12 m langen Riegel sind das 61 m statt 60 m —
    harmlos. Bei einem 30 × 30 m Kubus 42 m statt 30 m: das Gebäude füllt nur noch gut
    zwei Drittel des vorgesehenen Anteils. Richtungsabhängig gerechnet verschwindet der
    Fehler ganz.
    """
    dx, dy, _ = masse
    a = math.radians(azimut_grad)
    return abs(dx * math.cos(a)) + abs(dy * math.sin(a))


def sichtbare_tiefe(masse, azimut_grad: float) -> float:
    """Wie tief das Gebäude in Blickrichtung ausgedehnt ist, in Metern.

    Die Gegenrechnung zu ``sichtbare_breite``: ``|dx·cos a| + |dy·sin a|``. Gebraucht,
    weil der Abstand zur Gebäude**mitte** gerechnet wird, die vordere Fassade aber um die
    halbe Tiefe näher steht.
    """
    dx, dy, _ = masse
    a = math.radians(azimut_grad)
    return abs(dx * math.sin(a)) + abs(dy * math.cos(a))


# --------------------------------------------------------------------------------------
# Der analytische Abstand
# --------------------------------------------------------------------------------------

def abstand_aus_bildwinkel(masse, azimut_grad: float, *,
                           hoehe_ueber_grund: float,
                           brennweite_mm: float = BRENNWEITE_MM,
                           seitenverhaeltnis: float = 16 / 9,
                           deckungsgrad: float = DECKUNGSGRAD) -> dict:
    """Wie weit die Kamera stehen muss, damit das Gebäude den vorgesehenen Anteil füllt.

    Zwei Kandidaten, der grössere gewinnt: einer, damit die Breite passt, einer für die
    Höhe. Der vertikale Bedarf wird **von der Zielhöhe aus asymmetrisch** gemessen — nach
    oben bis zur Traufe, nach unten bis zum Fuss, der grössere zählt. Eine halbe
    Gebäudehöhe anzusetzen wäre falsch, weil das Blickziel bei einem hohen Bau eben
    **nicht** in der Mitte der Fassade sitzt; bei einem zwanziggeschossigen Haus liegt es
    im ersten Fünftel.

    Args:
        masse: Kantenlängen ``(dx, dy, dz)`` in Metern.
        azimut_grad: Wo die Kamera steht, im Uhrzeigersinn ab Nord.
        hoehe_ueber_grund: Höhe des Blickziels über der Gebäudeunterkante, in Metern.

    Returns:
        dict mit ``abstand_m`` und den Zwischenwerten, die dazu geführt haben
        (``breite_m``, ``tiefe_m``, ``abstand_breite_m``, ``abstand_hoehe_m``,
        ``untergrenze_m``, ``massgebend``). Wer einen Abstand für falsch hält, soll
        nachsehen können, welcher der drei Kandidaten ihn gesetzt hat.

    Raises:
        ValueError: ``deckungsgrad`` liegt nicht in ``(0, 1]``, oder eines der Masse ist
            negativ bzw. nicht endlich.
    """
    if isinstance(deckungsgrad, bool) or not isinstance(deckungsgrad, (int, float)):
        raise ValueError(f"deckungsgrad muss eine Zahl sein, war: {deckungsgrad!r}")
    deckung = float(deckungsgrad)
    if not math.isfinite(deckung) or not (0.0 < deckung <= 1.0):
        raise ValueError(
            f"deckungsgrad muss in (0, 1] liegen, war: {deckung}. Über 1 hiesse, das "
            "Gebäude solle grösser als das Bild sein — dann ist jeder Abstand zu klein."
        )
    masse = tuple(float(m) for m in masse)
    if len(masse) != 3 or any(not math.isfinite(m) or m < 0.0 for m in masse):
        raise ValueError(f"masse muss drei nichtnegative endliche Zahlen sein, war: {masse!r}")

    hfov, vfov = bildwinkel(brennweite_mm, seitenverhaeltnis=seitenverhaeltnis)
    breite = sichtbare_breite(masse, azimut_grad)
    tiefe = sichtbare_tiefe(masse, azimut_grad)

    # Asymmetrisch von der Zielhöhe aus, siehe Docstring.
    nach_oben = max(0.0, masse[2] - hoehe_ueber_grund)
    nach_unten = max(0.0, hoehe_ueber_grund)
    halbe_hoehe = max(nach_oben, nach_unten)

    d_breite = (breite / 2.0) / math.tan(hfov / 2.0) / deckung
    d_hoehe = halbe_hoehe / math.tan(vfov / 2.0) / deckung

    # Die halbe Tiefe kommt dazu, weil bis hier zur Gebäudemitte gerechnet wurde.
    untergrenze = tiefe / 2.0 + WANDABSTAND_M
    kandidaten = {"breite": d_breite + tiefe / 2.0,
                  "hoehe": d_hoehe + tiefe / 2.0,
                  "untergrenze": untergrenze}
    massgebend = max(kandidaten, key=kandidaten.__getitem__)

    return {
        "abstand_m": kandidaten[massgebend],
        "massgebend": massgebend,
        "breite_m": breite,
        "tiefe_m": tiefe,
        "halbe_hoehe_m": halbe_hoehe,
        "abstand_breite_m": kandidaten["breite"],
        "abstand_hoehe_m": kandidaten["hoehe"],
        "untergrenze_m": untergrenze,
        "hfov_grad": math.degrees(hfov),
        "vfov_grad": math.degrees(vfov),
    }


# --------------------------------------------------------------------------------------
# Der Eckentest — passt das Gebäude wirklich ins Bild?
# --------------------------------------------------------------------------------------

def _kamerabasis(auge, blick_auf):
    """``(vorwaerts, rechts, oben)`` aus Standort und Blickziel, oder ``None``.

    ``None`` in zwei Fällen: Kamera steht im Blickziel, oder sie schaut exakt senkrecht.
    Senkrecht ist entartet, weil Welt-Z dann keine Referenz für „oben" mehr hergibt — die
    Bildrotation wäre frei wählbar. Das kommt bei Augenhöhen-Perspektiven nicht vor, aber
    eine Draufsicht ist ein legitimer Wunsch, und dann soll die Antwort ein Befund sein
    und kein stiller Unsinn.
    """
    vorwaerts = _normiert(_minus(blick_auf, auge))
    if vorwaerts is None:
        return None
    rechts = _normiert(_kreuz(vorwaerts, (0.0, 0.0, 1.0)))
    if rechts is None:
        return None
    oben = _kreuz(rechts, vorwaerts)
    return vorwaerts, rechts, oben


def ecken_im_bild(auge, blick_auf, bbox, *,
                  brennweite_mm: float = BRENNWEITE_MM,
                  seitenverhaeltnis: float = 16 / 9,
                  bildrand: float = BILDRAND) -> dict:
    """Liegen alle acht Hüllbox-Ecken im Bild?

    Geprüft werden **alle acht Ecken einzeln**, nicht die Box als Ganzes. Für jede Ecke
    wird die Tiefe entlang der Blickachse gebildet, die seitlichen Anteile werden durch
    diese Tiefe geteilt — das ist die perspektivische Division — und gegen die
    Tangenswerte des Bildwinkels verglichen.

    Der Eckentest ist der Grund, warum die analytische Rechnung allein nicht genügt: Sie
    arbeitet mit einer Ersatzausdehnung und einem Ziel in der Mitte; der Eckentest prüft
    die Wirklichkeit einschliesslich der Kippung.

    Mitgeliefert wird ``noetiger_rueckschub_m``: **wie weit** die Kamera entlang ihrer
    Blickachse zurück muss, damit alle acht Ecken hineinpassen. Diese Zahl ist nicht
    geschätzt, sondern umgestellt. Ein Rückschub um Δ entlang der Blickachse erhöht die
    Tiefe jeder Ecke um genau Δ und lässt ihre seitlichen Anteile unberührt; aus
    ``seitlich / (tiefe + Δ) ≤ grenze`` folgt unmittelbar ``Δ ≥ seitlich / grenze −
    tiefe``. Das Maximum über die acht Ecken ist die Antwort — in einem Schritt, ohne
    Tasten.

    Returns:
        dict mit ``passt`` (bool), ``max_ueberstehen`` (1.0 = genau auf der Kante,
        1.2 = 20 % zu gross fürs Bild), ``noetiger_rueckschub_m``,
        ``ecken_hinter_kamera`` und ``begruendung``. Bei entarteter Basis ``passt=False``
        mit der Begründung — nie eine Ausnahme.
    """
    gelesen = _lies_bbox(bbox)
    if gelesen is None:
        return {"passt": False, "max_ueberstehen": float("inf"),
                "noetiger_rueckschub_m": None, "ecken_hinter_kamera": 0,
                "begruendung": f"bbox unbrauchbar: {bbox!r}"}

    basis = _kamerabasis(auge, blick_auf)
    if basis is None:
        return {"passt": False, "max_ueberstehen": float("inf"),
                "noetiger_rueckschub_m": None, "ecken_hinter_kamera": 0,
                "begruendung": "Kamerabasis entartet — Kamera im Blickziel oder exakt senkrecht."}
    vorwaerts, rechts, oben = basis

    hfov, vfov = bildwinkel(brennweite_mm, seitenverhaeltnis=seitenverhaeltnis)
    grenze_h = math.tan(hfov / 2.0) * bildrand
    grenze_v = math.tan(vfov / 2.0) * bildrand

    unten, obenecke = gelesen
    ecken = [(x, y, z)
             for x in (unten[0], obenecke[0])
             for y in (unten[1], obenecke[1])
             for z in (unten[2], obenecke[2])]

    hinter = 0
    max_ueberstehen = 0.0
    noetig = 0.0
    for ecke in ecken:
        v = _minus(ecke, auge)
        tiefe = _punkt(v, vorwaerts)
        seitlich = max(abs(_punkt(v, rechts)) / grenze_h,
                       abs(_punkt(v, oben)) / grenze_v)

        # Die Tiefe, ab der diese Ecke im Bild läge — und was daran heute fehlt.
        # MIN_TIEFE_M steht mit im Maximum, damit eine Ecke direkt auf der Blickachse
        # (seitlich = 0) nicht als „passt schon" durchgeht, während sie hinter der
        # Kamera liegt.
        noetig = max(noetig, max(seitlich, MIN_TIEFE_M) - tiefe)

        if tiefe < MIN_TIEFE_M:
            hinter += 1
            continue
        max_ueberstehen = max(max_ueberstehen, seitlich / tiefe)

    if hinter:
        return {"passt": False, "max_ueberstehen": float("inf"),
                "noetiger_rueckschub_m": noetig, "ecken_hinter_kamera": hinter,
                "begruendung": f"{hinter} von 8 Hüllbox-Ecken liegen hinter der Kamera "
                               f"(Tiefe unter {MIN_TIEFE_M} m). Die Kamera steckt im "
                               f"Gebäude; {noetig:.1f} m Rückschub bringen sie heraus."}

    passt = max_ueberstehen <= 1.0
    return {
        "passt": passt,
        "max_ueberstehen": max_ueberstehen,
        "noetiger_rueckschub_m": max(0.0, noetig),
        "ecken_hinter_kamera": 0,
        "begruendung": ("Alle acht Ecken im Bild."
                        if passt else
                        f"Grösstes Überstehen {max_ueberstehen:.3f} — das Gebäude ist um "
                        f"{(max_ueberstehen - 1.0) * 100:.1f} % zu gross für den Rahmen. "
                        f"{noetig:.1f} m Rückschub schaffen Platz."),
    }


def schiebe_bis_im_bild(auge, blick_auf, bbox, *,
                        brennweite_mm: float = BRENNWEITE_MM,
                        seitenverhaeltnis: float = 16 / 9,
                        bildrand: float = BILDRAND,
                        max_durchlaeufe: int = MAX_DURCHLAEUFE) -> dict:
    """Schiebt die Kamera zurück, bis alle acht Ecken im Bild liegen.

    Der Rückschub folgt **nur der horizontalen Blickrichtung**; die Augenhöhe bleibt
    konstant. Das ist der Grund, warum das Verfahren Augenhöhen-Perspektiven liefert und
    keine Drohnenbilder — eine Kamera, die auch nach oben ausweichen darf, landet über
    kurz oder lang im Vogelflug, weil das immer die bequemere Lösung ist.

    Der Schritt ist der **gerechnete** Rückschub aus ``ecken_im_bild``, nicht ein
    getasteter. Weil er die Blickachse betrifft, die Kamera aber waagrecht ausweichen
    soll, wird er durch den Kosinus der Neigung geteilt: Ein um 20° geneigter Blick
    gewinnt bei einem Meter waagrechtem Rückschub nur 94 cm Tiefe.

    Es bleibt eine Schleife, obwohl die Rechnung exakt ist — denn der waagrechte Schub
    ändert die Blickrichtung leicht, und mit ihr die Zerlegung in „seitlich" und „tief".
    In der Praxis sind es ein bis zwei Durchläufe statt der zwanzig, die der Bestand
    veranschlagt.

    **Der Bestand tastet stattdessen**: ``(überstehen − 1) · abstand · 0.6 + 3``. Das ist
    an beiden Enden schlecht. Der Faktor 0.6 dämpft auf 60 % des Nötigen, also braucht es
    mehr Durchläufe. Und bei einer Kamera dicht an der Fassade wird das Überstehen
    zweistellig — derselbe Ausdruck erzeugt dann einen Sprung über Kilometer, und die
    Kamera steht am Ende so weit weg, dass das Gebäude ein Fleck ist. Der Eckentest sagt
    dazu „passt", denn zu klein ist er nie aufgefallen.

    Nach ``max_durchlaeufe`` wird die letzte Position geliefert und ``vollstaendig=False``
    gesetzt. **Verweigern wäre schlechter als eine gekennzeichnet unvollkommene Antwort** —
    aber stillschweigend als gelöst gelten darf sie nicht.
    """
    aktuell = (float(auge[0]), float(auge[1]), float(auge[2]))
    ziel = (float(blick_auf[0]), float(blick_auf[1]), float(blick_auf[2]))
    augenhoehe = aktuell[2]

    for durchlauf in range(max_durchlaeufe):
        pruefung = ecken_im_bild(aktuell, ziel, bbox, brennweite_mm=brennweite_mm,
                                 seitenverhaeltnis=seitenverhaeltnis, bildrand=bildrand)
        if pruefung["passt"]:
            return {"auge": aktuell, "vollstaendig": True, "durchlaeufe": durchlauf,
                    "max_ueberstehen": pruefung["max_ueberstehen"],
                    "begruendung": pruefung["begruendung"]}

        richtung = _normiert((ziel[0] - aktuell[0], ziel[1] - aktuell[1], 0.0))
        if richtung is None:
            return {"auge": aktuell, "vollstaendig": False, "durchlaeufe": durchlauf,
                    "max_ueberstehen": pruefung["max_ueberstehen"],
                    "begruendung": "Kamera steht senkrecht über dem Blickziel — ein "
                                   "horizontaler Rückschub hat keine Richtung."}

        # Der Rückschub gilt entlang der Blickachse; ausgewichen wird waagrecht.
        # Bei geneigtem Blick bringt ein waagrechter Meter weniger als einen Meter Tiefe.
        voll = _normiert(_minus(ziel, aktuell))
        neigung = abs(voll[2]) if voll else 0.0
        waagrecht = math.sqrt(max(1.0 - neigung * neigung, 1e-6))
        schub = max(pruefung["noetiger_rueckschub_m"] / waagrecht, 0.5)
        aktuell = (aktuell[0] - richtung[0] * schub,
                   aktuell[1] - richtung[1] * schub,
                   augenhoehe)

    letzte = ecken_im_bild(aktuell, ziel, bbox, brennweite_mm=brennweite_mm,
                           seitenverhaeltnis=seitenverhaeltnis, bildrand=bildrand)
    return {
        "auge": aktuell,
        "vollstaendig": letzte["passt"],
        "durchlaeufe": max_durchlaeufe,
        "max_ueberstehen": letzte["max_ueberstehen"],
        "begruendung": (f"Nach {max_durchlaeufe} Durchläufen: {letzte['begruendung']} "
                        "Die Position wird geliefert, ist aber nicht bestätigt."),
    }


# --------------------------------------------------------------------------------------
# Heranziehen vor einer Verdeckung — Schrittlogik ohne Blender
# --------------------------------------------------------------------------------------

def ziehe_bis_frei(auge, blick_auf, bbox, _sicht_frei, *,
                   schritt: float = ZIEH_SCHRITT,
                   min_abstand: float = MIN_ZIEH_ABSTAND_M,
                   puffer: float = HUELLBOX_PUFFER_M,
                   max_schritte: int = MAX_ZIEH_SCHRITTE) -> dict:
    """Zieht die Kamera heran, solange etwas die Sicht verstellt.

    Steht ein Nachbargebäude im Weg, hilft kein Rückschub — die Antwort ist, **näher**
    heranzugehen, bis der Blick am Hindernis vorbei geht. Das ist die Gegenrichtung zu
    ``schiebe_bis_im_bild``, und die beiden ziehen damit gegeneinander: Der Eckentest
    schiebt weg, der Verdeckungstest holt heran. Im Bestand laufen sie nacheinander, nicht
    in einer gemeinsamen Schleife; ob das schwingt, ist dort nie geprüft worden. Hier ist
    die Reihenfolge dieselbe, aber der Ausgang wird protokolliert — wer eine Kamera findet,
    die zwischen zwei Läufen springt, sieht es an ``schritte`` und ``abbruch``.

    Ob die Sicht frei ist, weiss nur die Szene. Darum wird ``_sicht_frei(auge, blick_auf)``
    **hereingereicht**: im Runner ein Strahlenschuss gegen den Depsgraph, im Test eine
    Funktion mit drei Zeilen. Die Schrittlogik selbst — 12 % der Reststrecke, Untergrenze,
    Stopp am erweiterten Hüllbox-Rand, konstante Augenhöhe — ist reine Rechnung und
    gehört diesseits der Grenze. **Der Bestand macht diesen Schnitt nicht**; dort steht
    ``bpy`` im Modulkopf und die halbe Datei ist dadurch unprüfbar.

    Returns:
        dict mit ``auge``, ``frei`` (bool), ``schritte`` und ``abbruch`` — eines von
        ``sicht_frei``, ``untergrenze``, ``huellbox``, ``schritte_erschoepft``,
        ``entartet``.
    """
    aktuell = (float(auge[0]), float(auge[1]), float(auge[2]))
    ziel = (float(blick_auf[0]), float(blick_auf[1]), float(blick_auf[2]))
    augenhoehe = aktuell[2]
    gelesen = _lies_bbox(bbox)

    def _in_huellbox(p):
        if gelesen is None:
            return False
        unten, oben = gelesen
        return all(min(unten[i], oben[i]) - puffer <= p[i] <= max(unten[i], oben[i]) + puffer
                   for i in range(2))

    for n in range(max_schritte):
        if _sicht_frei(aktuell, ziel):
            return {"auge": aktuell, "frei": True, "schritte": n, "abbruch": "sicht_frei"}

        richtung = _normiert((ziel[0] - aktuell[0], ziel[1] - aktuell[1], 0.0))
        if richtung is None:
            return {"auge": aktuell, "frei": False, "schritte": n, "abbruch": "entartet"}
        abstand = _laenge((ziel[0] - aktuell[0], ziel[1] - aktuell[1], 0.0))

        naechster = (aktuell[0] + richtung[0] * abstand * schritt,
                     aktuell[1] + richtung[1] * abstand * schritt,
                     augenhoehe)
        rest = _laenge((ziel[0] - naechster[0], ziel[1] - naechster[1], 0.0))
        if rest < min_abstand:
            return {"auge": aktuell, "frei": False, "schritte": n, "abbruch": "untergrenze"}
        if _in_huellbox(naechster):
            return {"auge": aktuell, "frei": False, "schritte": n, "abbruch": "huellbox"}
        aktuell = naechster

    frei = bool(_sicht_frei(aktuell, ziel))
    return {"auge": aktuell, "frei": frei, "schritte": max_schritte,
            "abbruch": "sicht_frei" if frei else "schritte_erschoepft"}


# --------------------------------------------------------------------------------------
# Der Kamerasatz
# --------------------------------------------------------------------------------------

def kamerasatz(bbox, *,
               brennweite_mm: float = BRENNWEITE_MM,
               seitenverhaeltnis: float = 16 / 9,
               deckungsgrad: float = DECKUNGSGRAD,
               augenhoehe_m: float = AUGENHOEHE_M,
               bias_grad: float = BIAS_GRAD,
               bildrand: float = BILDRAND,
               kuerzel=None) -> dict:
    """Aus einer Hüllbox die zwölf Kameras — mit Begründung je Kamera.

    Der Ablauf je Richtung: analytischer Abstand aus dem Bildwinkel, Standort auf
    Augenhöhe, Blickziel angehoben, dann der Eckentest mit Rückschub. Der Verdeckungstest
    fehlt hier bewusst — er braucht die Szene und wird im Runner über ``ziehe_bis_frei``
    nachgeschaltet.

    Args:
        bbox: ``[[xmin,ymin,zmin],[xmax,ymax,zmax]]`` in Metern, **im Weltsystem**. Die
            Augenhöhe ist absolut; eine Hüllbox mit falscher Bodenkote ergibt darum eine
            Kamera im Kellergeschoss. Der Torwächter prüft das vorher.
        kuerzel: Auswahl aus ``RICHTUNGSFOLGE``, oder ``None`` für alle zwölf.

    Returns:
        dict mit ``kameras`` (Liste in der Reihenfolge von ``RICHTUNGSFOLGE``),
        ``masse_m``, ``mitte``, ``bias_grad`` und ``unvollstaendig`` — die Kürzel der
        Kameras, deren Eckentest nicht aufging. Eine leere Liste dort ist die einzige
        Auskunft, die „alle zwölf sitzen" bedeutet.

    Raises:
        ValueError: bbox unbrauchbar, oder ``kuerzel`` enthält einen unbekannten Namen.
    """
    gelesen = _lies_bbox(bbox)
    if gelesen is None:
        raise ValueError(
            "bbox unbrauchbar. Erwartet [[xmin,ymin,zmin],[xmax,ymax,zmax]] mit sechs "
            f"endlichen Zahlen, war: {bbox!r}"
        )
    unten, oben = gelesen
    masse = tuple(abs(oben[i] - unten[i]) for i in range(3))
    mitte = tuple((oben[i] + unten[i]) / 2.0 for i in range(3))
    fuss = min(unten[2], oben[2])

    if kuerzel is None:
        gewaehlt = list(RICHTUNGSFOLGE)
    else:
        gewaehlt = list(kuerzel)
        unbekannt = [k for k in gewaehlt if k not in RICHTUNGEN]
        if unbekannt:
            raise ValueError(
                f"Unbekannte Richtungskürzel: {unbekannt}. "
                f"Bekannt sind: {', '.join(RICHTUNGSFOLGE)}"
            )

    azimute = richtungen(bias_grad)
    # Absolut, nicht über dem Gebäudefuss — siehe Modulkopf. Das Blickziel liegt darüber.
    ziel_z = augenhoehe_m + masse[2] * ZIEL_ANTEIL_HOEHE
    hoehe_ueber_grund = ziel_z - fuss

    kameras = []
    unvollstaendig = []
    for k in gewaehlt:
        azimut = azimute[k]
        rechnung = abstand_aus_bildwinkel(
            masse, azimut, hoehe_ueber_grund=hoehe_ueber_grund,
            brennweite_mm=brennweite_mm, seitenverhaeltnis=seitenverhaeltnis,
            deckungsgrad=deckungsgrad)

        standort, _ = _achsen_aus_azimut(azimut)
        ziel = (mitte[0], mitte[1], ziel_z)

        # Seitlicher Versatz nur bei den Frontalen: eine exakt mittige Frontale ist
        # symmetrisch und damit bildlich tot. Bei den Diagonalen erledigt das der Bias.
        versatz = masse[0] * FRONTAL_VERSATZ if RICHTUNGEN[k][1] == 0 else 0.0
        quer = (standort[1], -standort[0], 0.0)

        auge = (mitte[0] + standort[0] * rechnung["abstand_m"] + quer[0] * versatz,
                mitte[1] + standort[1] * rechnung["abstand_m"] + quer[1] * versatz,
                augenhoehe_m)

        geschoben = schiebe_bis_im_bild(auge, ziel, bbox, brennweite_mm=brennweite_mm,
                                        seitenverhaeltnis=seitenverhaeltnis,
                                        bildrand=bildrand)
        if not geschoben["vollstaendig"]:
            unvollstaendig.append(k)

        kameras.append({
            "kuerzel": k,
            "azimut_grad": azimut,
            "auge": geschoben["auge"],
            "blick_auf": ziel,
            "brennweite_mm": float(brennweite_mm),
            "seitenverhaeltnis": float(seitenverhaeltnis),
            "abstand_analytisch_m": rechnung["abstand_m"],
            "massgebend": rechnung["massgebend"],
            "durchlaeufe": geschoben["durchlaeufe"],
            "vollstaendig": geschoben["vollstaendig"],
            "begruendung": geschoben["begruendung"],
        })

    return {
        "kameras": kameras,
        "masse_m": masse,
        "mitte": mitte,
        "bias_grad": float(bias_grad),
        "augenhoehe_m": float(augenhoehe_m),
        "unvollstaendig": unvollstaendig,
    }
