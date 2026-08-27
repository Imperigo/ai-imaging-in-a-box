#!/usr/bin/env python3
"""Erzeugt eine synthetische IFC-Datei — ein einfaches Gebäude aus vier Wänden und einer Platte.

Wahlweise **IFC4 oder IFC2X3**, wahlweise in **Metern oder Millimetern**. Die vier
Kombinationen sind nicht Vollständigkeitsdrang, sondern gemessener Bedarf: An 40 echten
Dateien (`auf-20260818-08`, 18.08.2026) standen 30 in IFC4 und 10 in IFC2X3, 15 in Metern
und 25 in Millimetern — und **alle zehn ArchiCAD-Dateien waren IFC2X3**.

Bis dahin gab es nur IFC4 in Metern. Getestet wurde also gegen ein Format, das das
verbreitetste Autorenprogramm gar nicht liefert.

Warum dieses Skript existiert
-----------------------------
Regel 3 verbietet echte Projektdaten im Repo und verlangt, dass Testdaten **im Repo
erzeugbar** sind. Ohne synthetische Geometrie liesse sich die Kette überhaupt nicht
prüfen — und mit einer echten Bauherrschafts-IFC dürfte sie es nicht.

Bewusst ohne Abhängigkeiten: reine stdlib, kein ifcopenshell. Wer Testdaten erzeugen
will, soll dafür kein GPL-behaftetes Environment aufsetzen müssen. Die Datei wird als
STEP-Text (ISO-10303-21) direkt geschrieben.

Die Geometrie ist absichtlich asymmetrisch (L≠B, Wand ohne Symmetrie), damit eine
verdrehte Up-Achse in Tests **auffällt** statt zufällig gleich auszusehen.

Aufruf:
    python3 tools/make_test_ifc.py [ziel.ifc] [schema] [vorsatz] [--gelaende] [--raeume]

``--gelaende`` legt eine Platte in 2,5-facher Gebäudespanne darunter. **Ohne sie steht der
Testbau in der Luft**, und das ist keine Kleinigkeit: Gemessen (`auf-20260819-15`) deckelt
``geom_iou`` dann bei 0.256, und die Geometrie-Schwelle von 0.65 ist **arithmetisch
unerreichbar** — selbst ein perfektes Bild käme auf höchstens 0.505. Mit Gelände liegt der
Deckel bei 0.967.

``--raeume`` legt zwei ``IfcSpace`` ins Wandinnere. **Ohne sie hat die Testgeometrie
keinen einzigen Raum** — und damit gab es im ganzen Projekt kein Beispiel, an dem sich
das Lesen von Räumen überhaupt prüfen liess. Zwei sind es und nicht einer, weil ein
Verfahren, das nur an einem Raum geprüft wird, an einer Konstanten hängen kann, die
zufällig passt; sie unterscheiden sich in Form, Fläche, Höhe, Fussbodenhöhe **und** in
der Art, wie ihr Grundriss in der Datei geschrieben ist. Auch dieser Schalter ist
**standardmässig aus**, aus demselben Grund wie ``--gelaende``.
"""
from __future__ import annotations

import sys
import uuid
from pathlib import Path

# Gebäudemass in Metern. Asymmetrisch, damit Verdrehungen sichtbar werden.
LAENGE_X, BREITE_Y, HOEHE_Z = 8.0, 5.0, 3.0
WANDDICKE, PLATTENDICKE = 0.30, 0.25

#: Kantenlänge der **Geländeplatte** als Vielfaches der grössten Gebäudespanne.
#:
#: 2,5 — dieselbe Grösse wie die Szene ``platte_endlich`` aus `auf-20260819-15`, damit die
#: Zahlen vergleichbar bleiben.
GELAENDE_VIELFACHES = 2.5

#: Dicke der Geländeplatte. Dünn, aber nicht null: Eine Fläche ohne Dicke hat keine
#: Hüllbox-Ausdehnung in Z und verschwindet in mancher Auswertung.
GELAENDE_DICKE = 0.05

# ======================================================================================
# Das zweite Bauwerk — «Hochbau»
# ======================================================================================
#
# **Warum es das gibt.** Jede Messung dieser Umgebung stand bis zum 26.08.2026 auf EINEM
# Quader von 8 × 5 × 3 m mit sechs Bauteilen. Das ist für Einheiten, Schemata und
# Hüllboxen genau richtig — und für alles, was mit **Gliederung** zu tun hat, wertlos:
# Verdeckung, Kompositionsprüfung, die Frage, ob mehr Samples etwas kosten, und die
# Geometrie-Treue selbst verhalten sich an einem glatten Kasten anders als an einem Bau.
#
# **Die Merkmale sind nicht erfunden, sondern zitiert.** Die HomeStation hat am
# 26.08.2026 beschrieben, was ihr zweites Modell taugen lässt:
#
#     «Es ist KEIN glatter Quader. Es hat Auskragungen, ein Stuetzenraster, eine
#      gegliederte Huelle und einen Kern — also genau die Merkmale, an denen sich eine
#      Geometriepruefung bewaehren muss.»
#
# Ihr Modell dürfen wir nicht haben (Regel 3). Die **Merkmale** dürfen wir nachbauen, und
# Regel 3 verlangt ausdrücklich Testdaten, die im Repo erzeugbar sind.
#
# **Additiv, unter einem eigenen Schalter.** Der Vorgabe-Quader bleibt Byte für Byte, wie
# er war — an ihm hängt jede bestehende Messreihe, und der Modulkopf sagt selbst: *«Eine
# stillschweigend geänderte Testgeometrie macht eine Messreihe unbrauchbar, ohne dass es
# auffällt.»*

#: Grundriss und Geschosse des Hochbaus.
HB_LAENGE_X, HB_BREITE_Y = 12.0, 8.0
HB_GESCHOSSE = 5
HB_GESCHOSSHOEHE = 3.0
HB_DECKENDICKE = 0.25

#: Das Stützenraster: 3 × 3 je Geschoss, 0,30 m im Quadrat.
#:
#: Drei mal drei und nicht mehr: Die Zahl der Bauteile soll **zwei Grössenordnungen** über
#: dem Quader liegen und trotzdem in einer Datei bleiben, die man von Hand lesen kann.
HB_STUETZEN_X, HB_STUETZEN_Y = 3, 3
HB_STUETZE = 0.30

#: Der Kern — vier Wände um einen Schacht in der Mitte, durch alle Geschosse.
HB_KERN_X, HB_KERN_Y = 3.0, 3.0
HB_KERNWAND = 0.25

#: Die gegliederte Hülle: Fassadentafeln je Geschoss und Seite, mit Fugen dazwischen.
#:
#: **Sie sind der Grund, warum diese Szene für die Maske etwas taugt:** Eine Hülle aus
#: vielen benannten Tafeln lässt sich nach Material trennen, eine einzige Wand nicht.
HB_TAFELN_LANG, HB_TAFELN_KURZ = 4, 3
HB_TAFELDICKE = 0.20
HB_FUGE = 0.10

#: Die Auskragung: Wie weit die Decken der obersten Geschosse über den Grundriss ragen.
#:
#: **Sie ist das Merkmal, das die Hüllbox von der Grundfläche abkoppelt.** Ohne sie wäre
#: die Hülle die schlichte Extrusion des Grundrisses, und jede Prüfung, die Grundriss und
#: Hülle verwechselt, käme damit durch.
HB_AUSKRAGUNG = 1.5
HB_AUSKRAGUNG_AB_GESCHOSS = 3

#: Die beiden Räume, die ``--raeume`` schreibt — **in Metern, in Geschosskoordinaten.**
#:
#: Warum zwei und warum ungleich: Ein Verfahren, das nur an einem Raum geprüft wird, kann
#: an einer Konstanten hängen, die zufällig passt. Die beiden hier unterscheiden sich in
#: **jeder** Grösse, die ein Leser verwechseln könnte — Fläche, Form, Höhe *und*
#: Fussbodenhöhe. Wer die Höhe des einen Raums für die des anderen ausgibt, wird rot;
#: wer die Wandhöhe (3,0 m) für eine Raumhöhe hält, ebenso.
#:
#: ``ring_relativ`` ist der Grundriss **relativ zum Einfügepunkt** des Raums, gegen den
#: Uhrzeigersinn. Dass der Einfügepunkt nicht im Ursprung liegt, ist Absicht: Ein Leser,
#: der die Platzierungskette nicht anwendet, bekommt den Raum an der falschen Stelle.
#:
#: ``z_unten`` ist die Oberkante des Fussbodens, ab der der Raumkörper nach oben läuft.
#: Die beiden Werte sind verschieden (0,00 m und 0,10 m — ein Raum mit Hohlboden), damit
#: sichtbar wird, ob der Bezugspunkt je Raum gelesen oder einmal angenommen wurde.
#:
#: ``profil`` sagt, **wie** die Form in der Datei steht: ``"polylinie"`` als Punktzug
#: (``IfcArbitraryClosedProfileDef``), ``"rechteck"`` als zwei Zahlen plus Platzierung
#: (``IfcRectangleProfileDef``, siehe :func:`_prisma_rechteck`). Beide Schreibweisen
#: kommen in echten Dateien vor, und ein Leser, der nur eine kennt, ist an der Hälfte
#: davon blind. Der Rechteck-Raum ist dabei der schärfere Fall: Seine Punkte stehen
#: **nirgends** in der Datei, sie entstehen erst aus Breite, Tiefe, einer gedrehten
#: Profilplatzierung und der Objektplatzierung. Wer eine davon auslässt, bekommt den Raum
#: an der falschen Stelle, verkehrt herum — oder beides.
#:
#: Zusammen füllen die beiden das Wandinnere lückenlos aus: 26,62 m² + 5,94 m² = 32,56 m²
#: = 7,40 m × 4,40 m. Diese Probe ist mehr als Kosmetik — sie belegt, dass die Zahlen
#: hier zueinander passen und nicht bloss nebeneinander stehen.
RAEUME = (
    {
        "name": "Raum-Nord",
        "lang_name": "Aufenthalt Nord",
        "einfuegepunkt": (WANDDICKE, WANDDICKE),
        "z_unten": 0.00,
        "hoehe": 2.70,
        # L-förmig, damit der Grundriss ein echtes Polygon ist und kein Rechteck, das
        # sich auch aus einer Hüllbox erraten liesse.
        "ring_relativ": ((0.0, 0.0), (4.7, 0.0), (4.7, 2.2),
                         (7.4, 2.2), (7.4, 4.4), (0.0, 4.4)),
        "flaeche": 26.62,
        "profil": "polylinie",
    },
    {
        "name": "Raum-Sued",
        "lang_name": None,          # bewusst leer: fehlende Felder müssen `None` werden
        "einfuegepunkt": (5.0, WANDDICKE),
        "z_unten": 0.10,
        "hoehe": 2.40,
        "ring_relativ": ((0.0, 0.0), (2.7, 0.0), (2.7, 2.2), (0.0, 2.2)),
        "flaeche": 5.94,
        "profil": "rechteck",
    },
)

_B64 = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz_$"


def _ifc_guid(n: int) -> str:
    """Deterministische IFC-GUID (22 Zeichen) aus einer laufenden Nummer.

    Deterministisch, damit zwei Läufe dieselbe Datei ergeben — sonst wäre kein Test
    reproduzierbar und jeder Lauf erzeugte einen Diff.
    """
    u = uuid.uuid5(uuid.NAMESPACE_DNS, f"aiimaging-testfixture-{n}")
    num = u.int
    out = []
    for _ in range(22):
        num, rest = divmod(num, 64)
        out.append(_B64[rest])
    return "".join(reversed(out))


class _Step:
    """Sammelt STEP-Zeilen und vergibt fortlaufende Entity-Nummern."""

    def __init__(self) -> None:
        self.lines: list[str] = []
        self._n = 0

    def add(self, body: str) -> str:
        self._n += 1
        self.lines.append(f"#{self._n}= {body};")
        return f"#{self._n}"

    def punkt(self, x: float, y: float, z: float) -> str:
        return self.add(f"IFCCARTESIANPOINT(({x:.6f},{y:.6f},{z:.6f}))")

    def platzierung(self, x=0.0, y=0.0, z=0.0) -> str:
        return self.add(f"IFCAXIS2PLACEMENT3D({self.punkt(x, y, z)},$,$)")


def _quader(s: _Step, kontext: str, breite: float, tiefe: float, hoehe: float,
            x: float, y: float, z: float, grund: str, *,
            einheit_je_meter: float = 1.0) -> tuple[str, str]:
    """Ein extrudierter Quader als IfcProductDefinitionShape + zugehörige Platzierung.

    `x`, `y`, `z` bezeichnen die **Minimum-Ecke** des Quaders, nicht seine Mitte. Das
    ist die Sicht, in der die Aufrufer rechnen (Wandflucht, Plattenrand); IFC selbst
    sieht es anders: `IFCRECTANGLEPROFILEDEF` ist auf seinen Platzierungspunkt
    zentriert und spannt von −breite/2 bis +breite/2. Diese Umrechnung gehört genau
    hierher — sonst müsste jeder Aufrufer die halben Masse mitschleppen und jeder
    vergessene Halbierungsschritt verschöbe ein Bauteil unbemerkt.
    """
    # Alle Längen an EINER Stelle in die Dateieinheit umrechnen. Die Aufrufer rechnen
    # durchgehend in Metern; eine Millimeter-Datei trägt dieselbe wirkliche Grösse mit
    # tausendfach grösseren Zahlen. Wer hier nur die Einheitenzeile umstellte und die
    # Zahlen liesse, erzeugte einen KAPUTTEN EXPORT — genau den Fall, den
    # `herkunft.pruefe_einheit_gegen_masse` diagnostiziert, und zwei von 40 echten
    # Dateien waren so.
    e = einheit_je_meter
    breite, tiefe, hoehe = breite * e, tiefe * e, hoehe * e
    x, y, z = x * e, y * e, z * e

    nullpunkt2d = s.add("IFCCARTESIANPOINT((0.,0.))")
    platz2d = s.add(f"IFCAXIS2PLACEMENT2D({nullpunkt2d},$)")
    profil = s.add(
        f"IFCRECTANGLEPROFILEDEF(.AREA.,$,{platz2d},{breite:.6f},{tiefe:.6f})"
    )
    richtung = s.add("IFCDIRECTION((0.,0.,1.))")
    koerper = s.add(f"IFCEXTRUDEDAREASOLID({profil},{s.platzierung()},{richtung},{hoehe:.6f})")
    rep = s.add(f"IFCSHAPEREPRESENTATION({kontext},'Body','SweptSolid',({koerper}))")
    shape = s.add(f"IFCPRODUCTDEFINITIONSHAPE($,$,({rep}))")
    # Nur X und Y werden versetzt: die Extrusion läuft von der Platzierung aus nach
    # oben, in Z ist der Bezugspunkt also bereits die Unterkante.
    ort = s.add(
        f"IFCLOCALPLACEMENT({grund},{s.platzierung(x + breite / 2, y + tiefe / 2, z)})"
    )
    return shape, ort


def _prisma(s: _Step, kontext: str, ring: tuple[tuple[float, float], ...],
            hoehe: float, x: float, y: float, z: float, grund: str, *,
            einheit_je_meter: float = 1.0) -> tuple[str, str]:
    """Ein extrudiertes Prisma über einem **frei geformten** Grundriss.

    Der Unterschied zu :func:`_quader` ist nicht Bequemlichkeit, sondern der Prüfzweck:
    ``IFCRECTANGLEPROFILEDEF`` trägt seine Form in zwei Zahlen und einer Platzierung,
    ``IFCARBITRARYCLOSEDPROFILEDEF`` trägt sie als Punktzug. Ein Leser, der nur den einen
    Weg kennt, ist an echten Dateien zur Hälfte blind — beide Profilarten kommen dort vor.

    `ring` ist **relativ zum Einfügepunkt** ``(x, y)`` und **offen**: Der Schlusspunkt
    wird hier angehängt, denn ``IFCPOLYLINE`` einer geschlossenen Kurve muss den ersten
    Punkt am Ende wiederholen. Wer ihn schon im Ring mitschickt, bekommt eine Kante der
    Länge null — und die ist in jeder späteren Auswertung ein Sonderfall.

    Anders als bei :func:`_quader` gibt es hier **keine Profilplatzierung**:
    ``IfcArbitraryClosedProfileDef`` erbt von ``IfcProfileDef`` und hat gar kein
    ``Position``-Attribut. Die Punkte liegen also unmittelbar im Koordinatensystem des
    Extrusionskörpers.
    """
    e = einheit_je_meter
    punkte = [s.add(f"IFCCARTESIANPOINT(({px * e:.6f},{py * e:.6f}))") for px, py in ring]
    linie = s.add(f"IFCPOLYLINE(({','.join(punkte + [punkte[0]])}))")
    profil = s.add(f"IFCARBITRARYCLOSEDPROFILEDEF(.AREA.,$,{linie})")
    richtung = s.add("IFCDIRECTION((0.,0.,1.))")
    koerper = s.add(
        f"IFCEXTRUDEDAREASOLID({profil},{s.platzierung()},{richtung},{hoehe * e:.6f})"
    )
    rep = s.add(f"IFCSHAPEREPRESENTATION({kontext},'Body','SweptSolid',({koerper}))")
    shape = s.add(f"IFCPRODUCTDEFINITIONSHAPE($,$,({rep}))")
    ort = s.add(f"IFCLOCALPLACEMENT({grund},{s.platzierung(x * e, y * e, z * e)})")
    return shape, ort


#: Versatz der **Profilplatzierung** des Rechteck-Raums, in Metern, im Koordinatensystem
#: des Extrusionskörpers. Krumm und ungleich in X und Y, damit ein Leser, der ihn
#: auslässt, nicht zufällig richtig liegt.
RECHTECKPROFIL_VERSATZ = (0.4, -0.2)


def _prisma_rechteck(s: _Step, kontext: str, breite: float, tiefe: float, hoehe: float,
                     x: float, y: float, z: float, grund: str, *,
                     einheit_je_meter: float = 1.0) -> tuple[str, str]:
    """Ein Quader über einem ``IfcRectangleProfileDef`` — in der **unbequemsten zulässigen
    Schreibweise**.

    Warum nicht einfach :func:`_quader`: Dort steht die Profilplatzierung auf der
    Einheitsmatrix — Ursprung, keine Drehung. Ein Leser, der sie schlicht **ignoriert**,
    bekommt dann trotzdem das richtige Rechteck, und kein Test der Welt merkt es. Genau
    das war der Befund der Mutationsprobe vom 22.08.2026: Die Profilplatzierung liess sich
    aus dem Leser herausschneiden, ohne dass ein Test rot wurde.

    Hier steht sie darum bewusst schief und versetzt, und beides wird in der
    Objektplatzierung wieder herausgerechnet. Das Ergebnis in der Welt ist **exakt**
    dasselbe Rechteck wie bei :func:`_quader` — nur muss der Leser jetzt dreimal richtig
    rechnen, statt zweimal richtig und einmal gar nicht:

    * ``RefDirection = (0,1)`` dreht das Profil um 90°. Darum stehen ``XDim`` und ``YDim``
      **vertauscht** in der Datei. Wer die Drehung auslässt, bekommt ein Rechteck von
      2,2 m × 2,7 m statt 2,7 m × 2,2 m — verkehrt herum, aber plausibel aussehend.
    * ``Location`` versetzt das Profil um :data:`RECHTECKPROFIL_VERSATZ`. Wer ihn auslässt,
      bekommt den Raum um denselben Betrag verschoben.

    Beides ist in echten Dateien alltäglich: Ein gedrehter Raum ist in jedem Grundriss zu
    finden, der nicht rechtwinklig zum Nordpfeil steht.
    """
    e = einheit_je_meter
    vx, vy = RECHTECKPROFIL_VERSATZ

    ort2d = s.add(f"IFCCARTESIANPOINT(({vx * e:.6f},{vy * e:.6f}))")
    # 90°-Drehung: die lokale X-Achse des Profils zeigt in Welt-Y.
    ref2d = s.add("IFCDIRECTION((0.,1.))")
    platz2d = s.add(f"IFCAXIS2PLACEMENT2D({ort2d},{ref2d})")
    # Vertauscht, weil die Drehung sie wieder zurücktauscht.
    profil = s.add(
        f"IFCRECTANGLEPROFILEDEF(.AREA.,$,{platz2d},{tiefe * e:.6f},{breite * e:.6f})"
    )
    richtung = s.add("IFCDIRECTION((0.,0.,1.))")
    koerper = s.add(
        f"IFCEXTRUDEDAREASOLID({profil},{s.platzierung()},{richtung},{hoehe * e:.6f})"
    )
    rep = s.add(f"IFCSHAPEREPRESENTATION({kontext},'Body','SweptSolid',({koerper}))")
    shape = s.add(f"IFCPRODUCTDEFINITIONSHAPE($,$,({rep}))")
    # `Location` verschiebt den MITTELPUNKT des Profils, und die Drehung geht darüber
    # hinweg — sie dreht die Profilpunkte um diesen Mittelpunkt, nicht den Mittelpunkt
    # selbst. Abgezogen wird der Versatz darum ungedreht. (Beim ersten Versuch stand hier
    # die gedrehte Fassung; der Raum landete 0,2 m zu weit rechts und 0,6 m zu weit unten,
    # und der End-to-End-Test hat es gemeldet — wofür er da ist.)
    ort = s.add(
        f"IFCLOCALPLACEMENT({grund},"
        f"{s.platzierung((x + breite / 2 - vx) * e, (y + tiefe / 2 - vy) * e, z * e)})"
    )
    return shape, ort


def _hochbau_bauteile(s: _Step, g, kontext: str, besitz: str, ort_gesch: str,
                      schema: str, einheit_je_meter: float) -> list[str]:
    """Die Bauteile des gegliederten Zweitbaus — eine reine Komposition aus ``_quader``.

    **Kein neuer Geometriecode.** Jedes Teil ist ein extrudierter Quader; was diese Szene
    von der ersten unterscheidet, ist ihre *Zusammensetzung*, nicht ihre Grundform. Das
    ist Absicht: Ein zweiter Geometriepfad wäre eine zweite Fehlerquelle, und geprüft
    werden soll die Gliederung, nicht die Extrusion.

    Die Namen sind mit Bedacht gewählt: Keiner trifft die Geländeregel
    (:data:`aiimaging.maske.GELAENDE_WOERTER`), und jeder sagt, was das Teil ist — die
    Bauwerksmaske liest genau diese Namen.
    """
    teile: list[str] = []

    def quader(name, art, bw, bt, bh, x, y, z, zusatz=""):
        shape, ort = _quader(s, kontext, bw, bt, bh, x, y, z, ort_gesch,
                             einheit_je_meter=einheit_je_meter)
        teile.append(s.add(
            f"IFC{art}('{_ifc_guid(next(g))}',{besitz},'{name}',$,$,{ort},{shape},${zusatz})"
        ))

    # ── Bodenplatte ──────────────────────────────────────────────────────────────────
    quader("Bodenplatte", "SLAB", HB_LAENGE_X, HB_BREITE_Y, HB_DECKENDICKE,
           0.0, 0.0, -HB_DECKENDICKE, ",.FLOOR.")

    for geschoss in range(HB_GESCHOSSE):
        z_unten = geschoss * HB_GESCHOSSHOEHE
        z_decke = z_unten + HB_GESCHOSSHOEHE - HB_DECKENDICKE

        # ── Die Decke, ab HB_AUSKRAGUNG_AB_GESCHOSS auskragend ───────────────────────
        #
        # Sie ragt NUR in +Y hinaus. Eine allseitige Auskragung waere wieder symmetrisch,
        # und Symmetrie ist genau das, was diese Szene nicht sein soll — die Doppelansicht
        # faellt an zweizaehliger Drehsymmetrie zusammen (Befund 26.08.2026).
        kragt = geschoss >= HB_AUSKRAGUNG_AB_GESCHOSS
        tiefe = HB_BREITE_Y + (HB_AUSKRAGUNG if kragt else 0.0)
        quader(f"Decke_OG{geschoss:02d}" + ("_auskragend" if kragt else ""),
               "SLAB", HB_LAENGE_X, tiefe, HB_DECKENDICKE, 0.0, 0.0, z_decke, ",.FLOOR.")

        # ── Das Stuetzenraster ───────────────────────────────────────────────────────
        for ix in range(HB_STUETZEN_X):
            for iy in range(HB_STUETZEN_Y):
                x = (ix + 1) * HB_LAENGE_X / (HB_STUETZEN_X + 1) - HB_STUETZE / 2
                y = (iy + 1) * HB_BREITE_Y / (HB_STUETZEN_Y + 1) - HB_STUETZE / 2
                quader(f"Stuetze_OG{geschoss:02d}_R{ix}{iy}", "COLUMN",
                       HB_STUETZE, HB_STUETZE, HB_GESCHOSSHOEHE - HB_DECKENDICKE,
                       x, y, z_unten, "" if schema == "IFC2X3" else ",$")

        # ── Der Kern: vier Waende um einen Schacht in der Mitte ──────────────────────
        kx = (HB_LAENGE_X - HB_KERN_X) / 2.0
        ky = (HB_BREITE_Y - HB_KERN_Y) / 2.0
        kh = HB_GESCHOSSHOEHE - HB_DECKENDICKE
        for seite, (bw, bt, px, py) in {
            "Sued": (HB_KERN_X, HB_KERNWAND, kx, ky),
            "Nord": (HB_KERN_X, HB_KERNWAND, kx, ky + HB_KERN_Y - HB_KERNWAND),
            "West": (HB_KERNWAND, HB_KERN_Y - 2 * HB_KERNWAND, kx, ky + HB_KERNWAND),
            "Ost":  (HB_KERNWAND, HB_KERN_Y - 2 * HB_KERNWAND,
                     kx + HB_KERN_X - HB_KERNWAND, ky + HB_KERNWAND),
        }.items():
            quader(f"Kern_OG{geschoss:02d}_{seite}", "WALL", bw, bt, kh, px, py, z_unten,
                   "" if schema == "IFC2X3" else ",$")

        # ── Die gegliederte Huelle: Tafeln mit Fugen ─────────────────────────────────
        #
        # Die Fugen sind der Punkt. Eine durchgehende Wand waere eine Flaeche; Tafeln mit
        # Zwischenraum ergeben eine Silhouette mit Struktur — und genau daran zeigt sich,
        # ob eine Tiefenkarte den Umriss traegt.
        tafelhoehe = HB_GESCHOSSHOEHE - HB_DECKENDICKE
        breit = (HB_LAENGE_X - (HB_TAFELN_LANG + 1) * HB_FUGE) / HB_TAFELN_LANG
        for i in range(HB_TAFELN_LANG):
            x = HB_FUGE + i * (breit + HB_FUGE)
            for kante, y in (("Sued", 0.0), ("Nord", HB_BREITE_Y - HB_TAFELDICKE)):
                quader(f"Fassade_OG{geschoss:02d}_{kante}_{i}", "WALL",
                       breit, HB_TAFELDICKE, tafelhoehe, x, y, z_unten,
                       "" if schema == "IFC2X3" else ",$")
        tief = (HB_BREITE_Y - (HB_TAFELN_KURZ + 1) * HB_FUGE) / HB_TAFELN_KURZ
        for i in range(HB_TAFELN_KURZ):
            y = HB_FUGE + i * (tief + HB_FUGE)
            for kante, x in (("West", 0.0), ("Ost", HB_LAENGE_X - HB_TAFELDICKE)):
                quader(f"Fassade_OG{geschoss:02d}_{kante}_{i}", "WALL",
                       HB_TAFELDICKE, tief, tafelhoehe, x, y, z_unten,
                       "" if schema == "IFC2X3" else ",$")

    return teile


def erzeuge_ifc(ziel: Path, *, schema: str = "IFC4", vorsatz: str | None = None,
                mit_gelaende: bool = False, mit_raeumen: bool = False,
                hochbau: bool = False,
                gelaende_vielfaches: float = GELAENDE_VIELFACHES) -> Path:
    """Schreibt die synthetische IFC nach `ziel` und gibt den Pfad zurück.

    Args:
        schema: ``"IFC4"`` (Vorgabe) oder ``"IFC2X3"``. **Beide werden gebraucht.** Die
            Messung an 40 echten Dateien (`auf-20260818-08`, 18.08.2026) ergab: 30-mal
            IFC4, 10-mal IFC2X3 — und **alle zehn ArchiCAD-Dateien waren IFC2X3**. Wer
            nur gegen IFC4 prüft, prüft nicht gegen das, was ArchiCAD tatsächlich
            liefert.
        vorsatz: SI-Vorsatz der Längeneinheit, ``None`` für Meter oder ``"MILLI"``.
            Ebenfalls aus der Messung: 25 der 40 Dateien standen in Millimetern.
            Die Koordinaten werden entsprechend skaliert, damit das Bauwerk **dieselbe
            wirkliche Grösse** behält — eine Datei, die Millimeter erklärt und
            Meterzahlen trägt, wäre ein kaputter Export und keine Testgeometrie.
        mit_gelaende: Zusätzlich eine Geländeplatte unter dem Bauwerk.
        hochbau: **Das zweite Bauwerk statt des Quaders** — Stützenraster, Kern,
            gegliederte Hülle, Auskragung. Siehe den Konstantenblock ``HB_*``.
            *Es ersetzt das Bauwerk, nicht die Datei:* Einheiten, Schema, Kontext und
            Geschoss bleiben dieselben, und ``--gelaende`` wirkt weiter. **Vorgabe aus**,
            aus demselben Grund wie bei ``mit_raeumen``: An der Hüllbox 8,0 × 5,0 × 3,25 m
            und an der Zahl der Bauteile hängt jede bestehende Messreihe.
        mit_raeumen: Zusätzlich zwei ``IfcSpace`` im Wandinneren — siehe :data:`RAEUME`.
            **Vorgabe aus**, aus demselben Grund wie bei ``mit_gelaende``: Jede bestehende
            Messung hängt an der Hüllbox 8,0 × 5,0 × 3,25 m und an der Zahl der Bauteile.
            Ein Raum ist zwar innen und ändert die Hüllbox nicht, aber er ist ein weiteres
            ``IfcProduct`` mit Geometrie — ``ifc_zu_glb`` zählte danach andere Elemente und
            Dreiecke. Eine stillschweigend geänderte Testgeometrie macht eine Messreihe
            unbrauchbar, ohne dass es auffällt.
    """
    if hochbau and mit_raeumen:
        raise ValueError(
            "hochbau und mit_raeumen zugleich: Die beiden Räume aus RAEUME sind an die "
            "Wandflucht des Quaders gerechnet und lägen im Hochbau mitten im Kern. "
            "Wer Räume im zweiten Bauwerk braucht, bekommt eigene — geraten wird hier "
            "nicht."
        )
    if schema not in ("IFC4", "IFC2X3"):
        raise ValueError(f"schema: 'IFC4' oder 'IFC2X3' erwartet, war {schema!r}.")
    if vorsatz not in (None, "MILLI"):
        raise ValueError(f"vorsatz: None oder 'MILLI' erwartet, war {vorsatz!r}.")
    vorsatz_teil = "$" if vorsatz is None else f".{vorsatz}."
    einheit_je_meter = 1.0 if vorsatz is None else 1000.0
    s = _Step()
    g = iter(range(1, 10_000))

    # ── Einheiten: SI-Meter. Ohne explizite Einheit ist der Massstab Auslegungssache —
    #    genau die Fehlerklasse (mm-als-m), die den Torwächter später beschäftigen wird.
    # IfcOwnerHistory — in IFC2X3 PFLICHT, in IFC4 optional.
    #
    # BEFUND 18.08.2026 (Testabnahme dieser Fixture): Hier stand an allen dreizehn
    # IfcRoot-Ableitungen schlicht `$`. In IFC4 richtig, in IFC2X3 ein verletztes
    # Pflichtattribut — und weil die Attributzahl gleich bleibt (4), fällt es beim
    # Zählen nicht auf. IfcOpenShell liest die Datei anstandslos; erst
    # `ifcopenshell.validate` meldete **13 Fehler** „Attribute not optional".
    #
    # Die Lehre ist die des ganzen Tages, eine Ebene tiefer: Dass etwas gelesen wird,
    # ist kein Beleg dafür, dass es gültig ist. Der Konverter war nachsichtig, der
    # Prüfer nicht — und ein echter IFC-Leser beim Empfänger könnte es auch nicht sein.
    #
    # Angelegt wird sie für BEIDE Schemata: In IFC4 schadet sie nicht, und zwei Wege
    # wären eine Abweichung, die niemand bemerkt.
    person = s.add("IFCPERSON($,'Testfixture',$,$,$,$,$,$)")
    organisation = s.add("IFCORGANIZATION($,'AI Imaging in a Box',$,$,$)")
    person_org = s.add(f"IFCPERSONANDORGANIZATION({person},{organisation},$)")
    anwendung = s.add(
        f"IFCAPPLICATION({organisation},'0.0.2','AI Imaging in a Box','aiimaging')"
    )
    # Fester Zeitstempel statt `time.time()`: Die Fixture ist deterministisch, und ein
    # Zeitstempel wäre die einzige Stelle, an der zwei Läufe auseinanderliefen.
    besitz = s.add(
        f"IFCOWNERHISTORY({person_org},{anwendung},$,.NOCHANGE.,$,$,$,1767225600)"
    )

    laenge = s.add(f"IFCSIUNIT(*,.LENGTHUNIT.,{vorsatz_teil},.METRE.)")
    flaeche = s.add("IFCSIUNIT(*,.AREAUNIT.,$,.SQUARE_METRE.)")
    volumen = s.add("IFCSIUNIT(*,.VOLUMEUNIT.,$,.CUBIC_METRE.)")
    winkel = s.add("IFCSIUNIT(*,.PLANEANGLEUNIT.,$,.RADIAN.)")
    einheiten = s.add(f"IFCUNITASSIGNMENT(({laenge},{flaeche},{volumen},{winkel}))")

    welt = s.platzierung()
    kontext = s.add(
        f"IFCGEOMETRICREPRESENTATIONCONTEXT($,'Model',3,1.E-05,{welt},$)"
    )
    projekt = s.add(
        f"IFCPROJECT('{_ifc_guid(next(g))}',{besitz},'Testfixture',"
        f"'Synthetische Geometrie - keine Projektdaten',$,$,$,({kontext}),{einheiten})"
    )

    ort_site = s.add(f"IFCLOCALPLACEMENT($,{s.platzierung()})")
    site = s.add(f"IFCSITE('{_ifc_guid(next(g))}',{besitz},'Gelaende',$,$,{ort_site},$,$,.ELEMENT.,$,$,$,$,$)")
    ort_bau = s.add(f"IFCLOCALPLACEMENT({ort_site},{s.platzierung()})")
    gebaeude = s.add(f"IFCBUILDING('{_ifc_guid(next(g))}',{besitz},'Testbau',$,$,{ort_bau},$,$,.ELEMENT.,$,$,$)")
    ort_gesch = s.add(f"IFCLOCALPLACEMENT({ort_bau},{s.platzierung()})")
    geschoss = s.add(
        f"IFCBUILDINGSTOREY('{_ifc_guid(next(g))}',{besitz},'EG',$,$,{ort_gesch},$,$,.ELEMENT.,0.)"
    )

    s.add(f"IFCRELAGGREGATES('{_ifc_guid(next(g))}',{besitz},$,$,{projekt},({site}))")
    s.add(f"IFCRELAGGREGATES('{_ifc_guid(next(g))}',{besitz},$,$,{site},({gebaeude}))")
    s.add(f"IFCRELAGGREGATES('{_ifc_guid(next(g))}',{besitz},$,$,{gebaeude},({geschoss}))")

    bauteile = []

    # Gelände — eine Platte, die ÜBER das Gebäude hinausreicht. Nicht zu verwechseln mit
    # der Bodenplatte darunter: Die gehört zum Bauwerk, das Gelände ist der Grund, auf dem
    # es steht.
    #
    # **Warum es das überhaupt gibt** (nachgetragen am 20.08.2026): Ohne Gelände trägt nur
    # ein kleiner Teil des Bildes Geometrie — beim Testbau 17 %. Und je mehr leere Fläche
    # ein Bild hat, desto mehr Bodenebene erfindet der monokulare Tiefenschätzer hinein
    # (`auf-20260818-10`). Gemessen (`auf-20260819-15`) deckelt ``geom_iou`` dadurch bei
    # **0.256**, und die Geometrie-Schwelle von 0.65 ist dann **arithmetisch
    # unerreichbar**: Selbst ein perfektes Bild käme auf höchstens 0.505.
    #
    # Mit Gelände steigt der Deckel auf 0.967. **Ein Gebäude steht auf dem Boden**, und
    # eine Testszene ohne Grund misst eine Lage, die es nicht gibt.
    #
    # Vorgabe ist trotzdem **aus**: Alle bestehenden Tests hängen an der Hüllbox
    # 8,0 × 5,0 × 3,25 m, und eine stillschweigend geänderte Testgeometrie wäre genau die
    # Sorte Änderung, die eine Messreihe unbrauchbar macht, ohne dass es auffällt.
    if mit_gelaende:
        # DIE PLATTENGROESSE IST SEIT DEM 26.08.2026 EIN KNOPF, und der Anlass ist eine
        # Messluecke: Der Entscheid zum Katalogbeweis ruht auf zwei Punkten — 4,2 %
        # Bodenanteil (Verlust 0.042) und 59,8 % (ein wertloses Bild erreicht |rho| 0.92).
        # Dazwischen war nichts gemessen, und darum ist die Ausnahme so eng geraten.
        #
        # Der erste Versuch, die Strecke zu schliessen, ging ueber die KAMERA
        # (`deckungsgrad`) und trug nicht: Ueber fuenf Laeufe blieb der Bodenanteil
        # zwischen 0.000 und 0.042, weil die Platte mit 2,5-facher Gebaeudespanne
        # schlicht nicht groesser wird, wenn man weiter weg geht. Der wirkliche Hebel ist
        # die Platte selbst.
        #
        # Die Vorgabe bleibt 2,5 — jede bestehende Messreihe haengt daran, und eine
        # stillschweigend geaenderte Testgeometrie ist genau die Sorte Aenderung, die eine
        # Reihe unbrauchbar macht, ohne dass es auffaellt.
        if not isinstance(gelaende_vielfaches, (int, float)) or gelaende_vielfaches <= 0:
            raise ValueError(
                f"gelaende_vielfaches: positive Zahl erwartet, war "
                f"{gelaende_vielfaches!r}. Eine Platte der Kantenlaenge null ist kein "
                f"Gelaende, sondern ein unsichtbarer Eintrag in der Materialtabelle — "
                f"die Gelaenderegel schlueg an, und die Maske traege nichts aus."
            )
        kante = float(gelaende_vielfaches) * max(LAENGE_X, BREITE_Y)
        shape, ort = _quader(
            s, kontext, kante, kante, GELAENDE_DICKE,
            (LAENGE_X - kante) / 2.0, (BREITE_Y - kante) / 2.0,
            -PLATTENDICKE - GELAENDE_DICKE, ort_gesch,
            einheit_je_meter=einheit_je_meter)
        bauteile.append(s.add(
            f"IFCSLAB('{_ifc_guid(next(g))}',{besitz},'Gelaende',$,$,{ort},{shape},$,"
            f".BASESLAB.)"
        ))

    if hochbau:
        # DAS ZWEITE BAUWERK. Es ersetzt den Quader und laesst alles andere stehen:
        # Einheiten, Schema, Kontext, Geschoss — und ein bestelltes Gelaende darunter,
        # das oben schon geschrieben wurde.
        bauteile.extend(_hochbau_bauteile(s, g, kontext, besitz, ort_gesch, schema,
                                          einheit_je_meter))
    else:
        # Bodenplatte — bündig mit der Wandaussenflucht und ganz unter Null, damit die
        # erwartete Gesamt-Bounding-Box eine glatte Prüfgrösse bleibt.
        shape, ort = _quader(s, kontext, LAENGE_X, BREITE_Y, PLATTENDICKE,
                             0.0, 0.0, -PLATTENDICKE, ort_gesch,
                             einheit_je_meter=einheit_je_meter)
        bauteile.append(s.add(
            f"IFCSLAB('{_ifc_guid(next(g))}',{besitz},'Bodenplatte',$,$,{ort},{shape},$,"
            f".FLOOR.)"
        ))

    # Vier Wände. Die Y-Wände sind um die Wanddicke verkuerzt, damit die Ecken nicht
    # doppelt Volumen tragen — sonst waeren spaetere Mengenauswertungen falsch.
    innen_y = BREITE_Y - 2 * WANDDICKE
    for name, (bw, bt, px, py) in ({} if hochbau else {
        "Wand-Sued":  (LAENGE_X, WANDDICKE, 0.0, 0.0),
        "Wand-Nord":  (LAENGE_X, WANDDICKE, 0.0, BREITE_Y - WANDDICKE),
        "Wand-West":  (WANDDICKE, innen_y, 0.0, WANDDICKE),
        "Wand-Ost":   (WANDDICKE, innen_y, LAENGE_X - WANDDICKE, WANDDICKE),
    }).items():
        shape, ort = _quader(s, kontext, bw, bt, HOEHE_Z, px, py, 0.0, ort_gesch, einheit_je_meter=einheit_je_meter)
        bauteile.append(s.add(
            # IFC4 kennt bei IfcWall ein neuntes Attribut (PredefinedType), IFC2X3
            # nicht. Ein Attribut zuviel macht die Datei für einen strengen Leser
            # ungültig — und ArchiCAD 28 exportiert nach Messung an zehn echten Dateien
            # IFC2X3 (`auf-20260818-08`).
            f"IFCWALL('{_ifc_guid(next(g))}',{besitz},'{name}',$,$,{ort},{shape},$"
            + (",$)" if schema == "IFC4" else ")")
        ))

    s.add(
        f"IFCRELCONTAINEDINSPATIALSTRUCTURE('{_ifc_guid(next(g))}',{besitz},$,$,"
        f"({','.join(bauteile)}),{geschoss})"
    )

    # ── Räume ────────────────────────────────────────────────────────────────────────
    # Ein `IfcSpace` ist kein Bauteil, sondern ein Luftvolumen: die Zone, in der sich
    # jemand aufhält. Er gehört darum **nicht** in die Bauteilliste oben. IFC ordnet
    # Räume dem Geschoss über `IfcRelAggregates` zu (Zerlegung), nicht über
    # `IfcRelContainedInSpatialStructure` (Einlagerung) — letzteres ist für Elemente
    # gedacht, und ein Raum dort drin machte die Datei für einen strengen Leser ungültig.
    #
    # Das zehnte Attribut ist die einzige Stelle, an der sich die beiden Schemata bei
    # `IfcSpace` unterscheiden — und zwar **nicht in der Zahl** der Attribute (elf sind
    # es hier wie dort), sondern in der Bedeutung: IFC2X3 hat dort
    # `InteriorOrExteriorSpace` (`IfcInternalOrExternalEnum`), IFC4 hat `PredefinedType`
    # (`IfcSpaceTypeEnum`). `.INTERNAL.` ist in **beiden** Aufzählungen enthalten und in
    # beiden richtig gemeint — ein Zufall, aber ein geprüfter (siehe
    # `test_raeume.py::test_raum_traegt_in_beiden_schemata_INTERNAL`). Wer hier
    # stattdessen `.SPACE.` schriebe (IFC4-typisch), machte die IFC2X3-Datei ungültig,
    # **ohne dass die Attributzahl es verriete** — genau die Fehlerklasse, die schon
    # einmal dreizehn unbemerkte `OwnerHistory`-Verstösse erzeugt hat.
    if mit_raeumen:
        raeume = []
        for r in RAEUME:
            ex, ey = r["einfuegepunkt"]
            if r["profil"] == "rechteck":
                (bx, by), (tx, ty) = r["ring_relativ"][0], r["ring_relativ"][2]
                shape, ort = _prisma_rechteck(
                    s, kontext, tx - bx, ty - by, r["hoehe"],
                    ex + bx, ey + by, r["z_unten"], ort_gesch,
                    einheit_je_meter=einheit_je_meter)
            else:
                shape, ort = _prisma(
                    s, kontext, r["ring_relativ"], r["hoehe"], ex, ey, r["z_unten"],
                    ort_gesch, einheit_je_meter=einheit_je_meter)
            lang = "$" if r["lang_name"] is None else f"'{r['lang_name']}'"
            raeume.append(s.add(
                f"IFCSPACE('{_ifc_guid(next(g))}',{besitz},'{r['name']}',$,$,{ort},"
                f"{shape},{lang},.ELEMENT.,.INTERNAL.,$)"
            ))
        s.add(
            f"IFCRELAGGREGATES('{_ifc_guid(next(g))}',{besitz},$,$,{geschoss},"
            f"({','.join(raeume)}))"
        )

    text = (
        "ISO-10303-21;\n"
        "HEADER;\n"
        "FILE_DESCRIPTION(('ViewDefinition [CoordinationView]'),'2;1');\n"
        f"FILE_NAME('{ziel.name}','2026-01-01T00:00:00',(''),(''),"
        "'AI Imaging in a Box - Testfixture','',''); \n"
        f"FILE_SCHEMA(('{schema}'));\n"
        "ENDSEC;\n"
        "DATA;\n" + "\n".join(s.lines) + "\nENDSEC;\n"
        "END-ISO-10303-21;\n"
    )
    ziel.parent.mkdir(parents=True, exist_ok=True)
    ziel.write_text(text, encoding="utf-8")
    return ziel


#: Die Schalter, die keine Stellungsargumente sind. Einmal aufgeschrieben, damit die
#: Filterung unten nicht bei jedem neuen Schalter an zwei Stellen nachgezogen werden muss
#: — ein vergessener Eintrag machte den Schalter stillschweigend zum Dateinamen.
SCHALTER = ("--gelaende", "--raeume", "--hochbau")

#: Schalter MIT Wert, als Vorsilbe. Sie brauchen einen eigenen Eintrag: Die Filterung
#: unten vergleicht auf Gleichheit, und `--gelaende-vielfaches=8.0` ist mit keinem
#: Eintrag aus :data:`SCHALTER` gleich — er wuerde zum Dateinamen. Genau dieser Fehler
#: ist am 26.08.2026 beim ersten Versuch aufgetreten und vom Waechter gegen unbekannte
#: Schalter gefangen worden, der aus demselben Anlass gebaut worden war.
WERTSCHALTER = ("--gelaende-vielfaches=",)

GEBRAUCH = (
    "Gebrauch: make_test_ifc.py [ZIEL] [IFC4|IFC2X3] [MILLI] [--gelaende] [--raeume]\n"
    "                              [--hochbau]\n"
    "  ZIEL       Pfad der zu schreibenden Datei (Vorgabe: build/testbau.ifc)\n"
    "  Schema     IFC4 (Vorgabe) oder IFC2X3\n"
    "  Vorsatz    MILLI fuer Millimeter, sonst Meter\n"
    "  --gelaende zusaetzlich eine Gelaendeplatte unter dem Bauwerk\n"
    "  --gelaende-vielfaches=N Kantenlaenge der Platte als Vielfaches der\n"
    "             Gebaeudespanne (Vorgabe 2.5) — nur mit --gelaende\n"
    "  --raeume   zusaetzlich zwei IfcSpace im Wandinneren\n"
    "  --hochbau  STATT des Quaders ein gegliedertes Bauwerk: Stuetzenraster, Kern,\n"
    "             Fassadentafeln, Auskragung. Fuer Messungen, an denen ein glatter\n"
    "             Kasten nichts zeigt.\n"
)


if __name__ == "__main__":
    # Zweites und drittes Argument optional: Schema und SI-Vorsatz. Ohne sie bleibt es
    # bei IFC4 in Metern — der Stand, auf den alle bestehenden Tests gebaut sind.
    if "--help" in sys.argv[1:] or "-h" in sys.argv[1:]:
        print(GEBRAUCH, end="")
        raise SystemExit(0)
    argv = [a for a in sys.argv[1:]
            if a not in SCHALTER and not a.startswith(WERTSCHALTER)]
    mit_gelaende = "--gelaende" in sys.argv
    vielfaches = GELAENDE_VIELFACHES
    for a in sys.argv[1:]:
        if a.startswith("--gelaende-vielfaches="):
            try:
                vielfaches = float(a.split("=", 1)[1])
            except ValueError:
                print(f"{a}: nach dem Gleichheitszeichen gehoert eine Zahl.\n\n{GEBRAUCH}",
                      end="", file=sys.stderr)
                raise SystemExit(2) from None
    mit_raeumen = "--raeume" in sys.argv
    hochbau = "--hochbau" in sys.argv
    # Ein unbekannter Schalter wurde bisher zum Dateinamen: `--help` schrieb eine IFC
    # namens `--help` ins Arbeitsverzeichnis. Ein Tippfehler darf keine Datei erzeugen.
    unbekannt = [a for a in argv if a.startswith("-")]
    if unbekannt:
        print(f"Unbekannter Schalter: {unbekannt[0]}\n\n{GEBRAUCH}", end="",
              file=sys.stderr)
        raise SystemExit(2)
    ziel = Path(argv[0] if argv else "build/testbau.ifc")
    schema = argv[1] if len(argv) > 1 else "IFC4"
    vorsatz = argv[2] if len(argv) > 2 else None
    p = erzeuge_ifc(ziel, schema=schema, vorsatz=(vorsatz or None),
                    mit_gelaende=mit_gelaende, mit_raeumen=mit_raeumen,
                    hochbau=hochbau, gelaende_vielfaches=vielfaches)
    print(f"{p}  ({p.stat().st_size} Bytes, {len(p.read_text().splitlines())} Zeilen)")
