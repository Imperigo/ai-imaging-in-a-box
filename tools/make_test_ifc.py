#!/usr/bin/env python3
"""Erzeugt eine synthetische IFC4-Datei — ein einfaches Gebäude aus vier Wänden und einer Platte.

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
            x: float, y: float, z: float, grund: str) -> tuple[str, str]:
    """Ein extrudierter Quader als IfcProductDefinitionShape + zugehörige Platzierung.

    `x`, `y`, `z` bezeichnen die **Minimum-Ecke** des Quaders, nicht seine Mitte. Das
    ist die Sicht, in der die Aufrufer rechnen (Wandflucht, Plattenrand); IFC selbst
    sieht es anders: `IFCRECTANGLEPROFILEDEF` ist auf seinen Platzierungspunkt
    zentriert und spannt von −breite/2 bis +breite/2. Diese Umrechnung gehört genau
    hierher — sonst müsste jeder Aufrufer die halben Masse mitschleppen und jeder
    vergessene Halbierungsschritt verschöbe ein Bauteil unbemerkt.
    """
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


def erzeuge_ifc(ziel: Path) -> Path:
    """Schreibt die synthetische IFC4 nach `ziel` und gibt den Pfad zurück."""
    s = _Step()
    g = iter(range(1, 10_000))

    # ── Einheiten: SI-Meter. Ohne explizite Einheit ist der Massstab Auslegungssache —
    #    genau die Fehlerklasse (mm-als-m), die den Torwächter später beschäftigen wird.
    laenge = s.add("IFCSIUNIT(*,.LENGTHUNIT.,$,.METRE.)")
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
                         0.0, 0.0, -PLATTENDICKE, ort_gesch)
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
        shape, ort = _quader(s, kontext, bw, bt, HOEHE_Z, px, py, 0.0, ort_gesch)
        bauteile.append(s.add(
            f"IFCWALL('{_ifc_guid(next(g))}',$,'{name}',$,$,{ort},{shape},$,$)"
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
        "FILE_SCHEMA(('IFC4'));\n"
        "ENDSEC;\n"
        "DATA;\n" + "\n".join(s.lines) + "\nENDSEC;\n"
        "END-ISO-10303-21;\n"
    )
    ziel.parent.mkdir(parents=True, exist_ok=True)
    ziel.write_text(text, encoding="utf-8")
    return ziel


if __name__ == "__main__":
    ziel = Path(sys.argv[1] if len(sys.argv) > 1 else "build/testbau.ifc")
    p = erzeuge_ifc(ziel)
    print(f"{p}  ({p.stat().st_size} Bytes, {len(p.read_text().splitlines())} Zeilen)")
