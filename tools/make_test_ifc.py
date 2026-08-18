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
    python3 tools/make_test_ifc.py [ziel.ifc]
"""
from __future__ import annotations

import sys
import uuid
from pathlib import Path

# Gebäudemass in Metern. Asymmetrisch, damit Verdrehungen sichtbar werden.
LAENGE_X, BREITE_Y, HOEHE_Z = 8.0, 5.0, 3.0
WANDDICKE, PLATTENDICKE = 0.30, 0.25

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


def erzeuge_ifc(ziel: Path, *, schema: str = "IFC4", vorsatz: str | None = None) -> Path:
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
    """
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
        f"IFCPROJECT('{_ifc_guid(next(g))}',$,'Testfixture',"
        f"'Synthetische Geometrie - keine Projektdaten',$,$,$,({kontext}),{einheiten})"
    )

    ort_site = s.add(f"IFCLOCALPLACEMENT($,{s.platzierung()})")
    site = s.add(f"IFCSITE('{_ifc_guid(next(g))}',$,'Gelaende',$,$,{ort_site},$,$,.ELEMENT.,$,$,$,$,$)")
    ort_bau = s.add(f"IFCLOCALPLACEMENT({ort_site},{s.platzierung()})")
    gebaeude = s.add(f"IFCBUILDING('{_ifc_guid(next(g))}',$,'Testbau',$,$,{ort_bau},$,$,.ELEMENT.,$,$,$)")
    ort_gesch = s.add(f"IFCLOCALPLACEMENT({ort_bau},{s.platzierung()})")
    geschoss = s.add(
        f"IFCBUILDINGSTOREY('{_ifc_guid(next(g))}',$,'EG',$,$,{ort_gesch},$,$,.ELEMENT.,0.)"
    )

    s.add(f"IFCRELAGGREGATES('{_ifc_guid(next(g))}',$,$,$,{projekt},({site}))")
    s.add(f"IFCRELAGGREGATES('{_ifc_guid(next(g))}',$,$,$,{site},({gebaeude}))")
    s.add(f"IFCRELAGGREGATES('{_ifc_guid(next(g))}',$,$,$,{gebaeude},({geschoss}))")

    bauteile = []

    # Bodenplatte — bündig mit der Wandaussenflucht und ganz unter Null, damit die
    # erwartete Gesamt-Bounding-Box eine glatte Prüfgrösse bleibt.
    shape, ort = _quader(s, kontext, LAENGE_X, BREITE_Y, PLATTENDICKE,
                         0.0, 0.0, -PLATTENDICKE, ort_gesch, einheit_je_meter=einheit_je_meter)
    bauteile.append(s.add(
        f"IFCSLAB('{_ifc_guid(next(g))}',$,'Bodenplatte',$,$,{ort},{shape},$,.FLOOR.)"
    ))

    # Vier Wände. Die Y-Wände sind um die Wanddicke verkuerzt, damit die Ecken nicht
    # doppelt Volumen tragen — sonst waeren spaetere Mengenauswertungen falsch.
    innen_y = BREITE_Y - 2 * WANDDICKE
    for name, (bw, bt, px, py) in {
        "Wand-Sued":  (LAENGE_X, WANDDICKE, 0.0, 0.0),
        "Wand-Nord":  (LAENGE_X, WANDDICKE, 0.0, BREITE_Y - WANDDICKE),
        "Wand-West":  (WANDDICKE, innen_y, 0.0, WANDDICKE),
        "Wand-Ost":   (WANDDICKE, innen_y, LAENGE_X - WANDDICKE, WANDDICKE),
    }.items():
        shape, ort = _quader(s, kontext, bw, bt, HOEHE_Z, px, py, 0.0, ort_gesch, einheit_je_meter=einheit_je_meter)
        bauteile.append(s.add(
            # IFC4 kennt bei IfcWall ein neuntes Attribut (PredefinedType), IFC2X3
            # nicht. Ein Attribut zuviel macht die Datei für einen strengen Leser
            # ungültig — und ArchiCAD 28 exportiert nach Messung an zehn echten Dateien
            # IFC2X3 (`auf-20260818-08`).
            f"IFCWALL('{_ifc_guid(next(g))}',$,'{name}',$,$,{ort},{shape},$"
            + (",$)" if schema == "IFC4" else ")")
        ))

    s.add(
        f"IFCRELCONTAINEDINSPATIALSTRUCTURE('{_ifc_guid(next(g))}',$,$,$,"
        f"({','.join(bauteile)}),{geschoss})"
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


if __name__ == "__main__":
    # Zweites und drittes Argument optional: Schema und SI-Vorsatz. Ohne sie bleibt es
    # bei IFC4 in Metern — der Stand, auf den alle bestehenden Tests gebaut sind.
    ziel = Path(sys.argv[1] if len(sys.argv) > 1 else "build/testbau.ifc")
    schema = sys.argv[2] if len(sys.argv) > 2 else "IFC4"
    vorsatz = sys.argv[3] if len(sys.argv) > 3 else None
    p = erzeuge_ifc(ziel, schema=schema, vorsatz=(vorsatz or None))
    print(f"{p}  ({p.stat().st_size} Bytes, {len(p.read_text().splitlines())} Zeilen)")
