#!/usr/bin/env python3
"""RUNNER — Räume (``IfcSpace``) aus einer IFC (IFC4 oder IFC2X3) → JSON.

Läuft im `.venv-ifc`, nie im Produkt-Environment.

Warum dieses Skript ein eigener Prozess ist
-------------------------------------------
Dieselbe Begründung wie bei ``ifc_to_glb_runner.py``, und sie wiegt hier keinen Deut
leichter: `ifcopenshell` steht unter LGPL-3.0-or-later, und das ausgelieferte PyPI-Wheel
bindet **CGAL statisch** ein, dessen genutzte Pakete unter **GPL-3.0-or-later** stehen.
Ein ``import ifcopenshell`` im Produkt-Environment machte das Produkt GPL.

Die Prozessgrenze löst das: eigenständiges Programm, eigenes venv, Verständigung über
Dateien und Prozess-Rückgabewerte. Es entsteht eine Aggregation, kein abgeleitetes Werk.

**Dieses Modul darf aus `aiimaging` heraus niemals importiert werden.**
`tests/test_prozessgrenze.py` erzwingt das.

Wozu das gebraucht wird
-----------------------
`aiimaging.kameras` rechnet ausschliesslich Standpunkte **um eine Hüllbox herum**, und
``WANDABSTAND_M = 10.0`` macht eine Innenaufnahme rechnerisch unmöglich — in einem 4 m
breiten Zimmer gibt es keinen zulässigen Standpunkt. Bevor sich daran etwas ändern kann,
muss überhaupt bekannt sein, **wo die Räume sind**. Genau das und nicht mehr leistet
dieses Skript: Es liefert Räume als schlichte Daten. Kamerasetzung, Standpunktwahl und
Verdeckungstest sind ausdrücklich **nicht** hier.

Der Bezugspunkt der Höhe — die Sorgfalt, an der dieses Projekt schon zweimal verloren hat
------------------------------------------------------------------------------------------
Im Kopf von ``kameras.py`` steht die Geschichte: Eine Kamerahöhe „absolut" gemeint kam bei
einem Bauwerk auf 400 m über Meer **vierhundert Meter unter dem Erdgeschoss** zu liegen.
Dieselbe Verwechslung steht im Übergabeblatt (Kapitel 4.3) auf der Gegenseite.
**Eine Zahl ohne Bezugspunkt ist in diesem Projekt keine Zahl.**

Darum trägt jeder Raum zwei getrennte Höhenangaben und einen Namen für ihren Bezug:

* ``z_unten_m`` — die **Unterkante des Raumkörpers**, in IFC-Weltkoordinaten. Das ist der
  Nullpunkt des Projekts, wie ihn die Platzierungskette (Site → Building → Storey → Space)
  ergibt. Es ist **nicht** eine Höhe über Meer und **nicht** eine Höhe über Gelände:
  ``IfcSite.RefElevation`` und eine etwaige Georeferenzierung (``IfcMapConversion``)
  werden hier bewusst **nicht** eingerechnet — sie sind eine eigene Frage mit eigenen
  Fehlerquellen.
* ``hoehe_m`` — die Länge des Raumkörpers **nach oben ab ``z_unten_m``**.

Und was ``hoehe_m`` **nicht** ist, steht in ``hoehe_bezug`` und ``hoehe_begruendung``:
Es ist die Extrusionstiefe des Raumkörpers, wie der Exporteur ihn modelliert hat. Ob das
die **lichte Raumhöhe** (bis Unterkante Decke), die **Geschosshöhe** (bis Oberkante
Rohdecke des Geschosses darüber) oder irgendetwas dazwischen ist, sagt die Datei nicht —
das ist eine Gewohnheit des erzeugenden Programms und keine Angabe im Modell. Wer die
Zahl als lichte Höhe verwendet, tut das auf eigene Rechnung; hier wird sie nicht dazu
erklärt. Kann die Höhe nicht gemessen werden, steht ``None`` da — *nicht gemessen*, nie
*in Ordnung*, nie *0*.

Nicht gelesen wird ``Qto_SpaceBaseQuantities.Height``. Das ist eine vom Exporteur
**behauptete** Zahl mit einem dritten, wieder anderen Bezugspunkt; sie hier danebenzulegen
hiesse, zwei Höhen mit zwei Bezügen auszuliefern, von denen eine ungeprüft ist. Wer sie
braucht, holt sie, wenn er weiss wofür.

Einheiten
---------
IFC-Dateien stehen oft in Millimetern: An 40 echten Dateien (`auf-20260818-08`) waren
**25 von 40** in Millimetern. Alle Längen hier gehen darum durch den Faktor aus der
``IfcUnitAssignment`` und kommen in **Metern** heraus; was die Datei erklärt hat, steht im
Report unter ``einheit``.

Eine Datei, die Millimeter deklariert und Meterzahlen trägt, ist ein **kaputter Export**
und keine gültige Eingabe. Der Report glättet das nicht, sondern meldet es unter
``masse_plausibel``/``masse_befund`` — mit dem Faktor, der die Abweichung erklärt. Das ist
dieselbe Diagnose, die ``herkunft.pruefe_einheit_gegen_masse`` für ganze Bauwerke stellt,
hier auf Raumgrössen umgestellt.

Schemata
--------
**IFC4 und IFC2X3.** Dieselbe Messung: Alle zehn ArchiCAD-Dateien waren IFC2X3. Wer nur
gegen IFC4 prüft, prüft nicht gegen das, was das verbreitetste Autorenprogramm liefert.
Bei ``IfcSpace`` unterscheiden sich die beiden Schemata **nicht in der Attributzahl** —
elf sind es hier wie dort —, sondern in der Bedeutung des zehnten Attributs. Für dieses
Skript spielt das keine Rolle: Gelesen werden ``GlobalId``, ``Name``, ``LongName``,
``ObjectPlacement`` und ``Representation``, und die heissen in beiden Schemata gleich.

Was dieses Skript NICHT kann — und warum das im Report steht
------------------------------------------------------------
Ein stilles Weglassen wäre der schlimmste Ausgang: Der Aufrufer sähe drei Räume und hielte
sie für alle. Darum gilt die Zusicherung:

    ``len(raeume) == n_raeume == Zahl der IfcSpace in der Datei`` — **immer.**

Ein Raum, dessen Grundriss sich nicht lesen lässt, verschwindet nicht, sondern steht mit
``grundriss_m = None`` und einem ``befund`` da, der sagt, **woran** es lag.

Und es sind **zwei** Urteile, nicht eines: ``grundriss_m is None`` genau dann, wenn
``befund`` gesetzt ist; ``hoehe_m is None`` genau dann, wenn ``hoehe_befund`` gesetzt ist.
Gelernt an der schiefen Extrusion — der Fussbodenumriss steht dann einwandfrei in der
Datei, aber der Körper darüber schert weg. Ein einziges Urteil hätte hier entweder eine
gültige Messung weggeworfen oder eine erfundene Höhe geliefert.

Nicht gelesen werden (jeweils mit eigenem Befundschlüssel):

* Räume ohne ``Representation`` oder ohne ``Body``-Repräsentation — sehr häufig, viele
  Exporteure schreiben Zonen ohne Körper.
* Körper, die kein ``IfcExtrudedAreaSolid`` sind: ``IfcFacetedBrep``,
  ``IfcBooleanClippingResult`` (Revit bei Schrägen), ``IfcMappedItem``. Ein
  ``IfcBooleanClippingResult`` liesse sich auspacken, indem man den Schnitt ignoriert —
  genau das wäre aber eine stillschweigend geänderte Geometrie, und ungeprüft dazu.
* ``IfcIndexedPolyCurve`` als Profilkurve (IFC4, moderne Revit-Exporte). Der
  aussichtsreichste nächste Ausbau — hier nicht gebaut, weil es dafür keine Testgeometrie
  im Repo gibt und ungeprüfter Code schlimmer ist als fehlender.
* Kreis-, Ellipsen- und andere nicht-polygonale Profile. Ein Kreis **als** Polygon
  auszugeben hiesse, eine Auflösung zu erfinden, die niemand bestellt hat.

Aufruf:
    .venv-ifc/bin/python ifc_raeume_runner.py <in.ifc> [--report r.json]
"""
from __future__ import annotations

import argparse
import json
import sys

# ======================================================================================
# Befundschlüssel — warum ein Raum keinen Grundriss bekam
#
# Maschinenlesbar UND mit Satz: Der Schlüssel ist zum Verzweigen da, der Satz für den
# Menschen, der die Datei reparieren muss. Nur einen von beiden zu liefern hiesse, eine
# der beiden Seiten im Regen stehen zu lassen.
# ======================================================================================

#: Der Raum hat gar kein ``Representation``-Attribut oder keine Repräsentationen darin.
KEINE_REPRAESENTATION = "keine_repraesentation"

#: Repräsentationen vorhanden, aber keine mit ``RepresentationIdentifier == 'Body'``.
KEINE_BODY_REPRAESENTATION = "keine_body_repraesentation"

#: Die ``Body``-Repräsentation enthält kein ``IfcExtrudedAreaSolid``.
KEIN_EXTRUSIONSKOERPER = "kein_extrusionskoerper"

#: Mehrere Extrusionskörper. Welcher der Raum ist, sagt die Datei nicht — und zu raten
#: wäre schlimmer als zu schweigen.
MEHRERE_EXTRUSIONSKOERPER = "mehrere_extrusionskoerper"

#: Die Profilart ist keine, aus der sich ein Polygon ohne Erfindung ergibt (Kreis, Ellipse).
PROFIL_NICHT_POLYGONAL = "profil_nicht_polygonal"

#: Die Profilkurve ist eine Art, die dieses Skript (noch) nicht liest.
PROFILKURVE_NICHT_UNTERSTUETZT = "profilkurve_nicht_unterstuetzt"

#: Weniger als drei verschiedene Punkte oder Fläche null — kein Polygon.
POLYGON_ENTARTET = "polygon_entartet"

# ── Und die Befunde der HÖHE. Sie sind ein eigener Satz, weil Grundriss und Höhe zwei
#    Messungen sind und nicht eine.
#
#    Der Fall, der das gelehrt hat: eine schiefe Extrusion. Der Fussbodenumriss ist dann
#    einwandfrei gelesen — er steht als Profil in der Datei —, aber der Körper darüber
#    schert weg, und eine „Höhe über der Unterkante" gibt es nicht mehr. Wer für so einen
#    Raum den Grundriss mitwegwirft, wirft eine gültige Messung weg; wer ihm eine Höhe
#    gibt, erfindet eine. Beides ist falsch, und darum gibt es zwei Urteile.

#: Es gibt keinen Grundriss, also auch keinen Bezugspunkt. ``befund`` sagt, woran es lag.
HOEHE_OHNE_GRUNDRISS = "hoehe_ohne_grundriss"

#: Die Extrusion läuft nicht senkrecht. Der Fussbodenumriss steht trotzdem — die Höhe nicht.
EXTRUSION_NICHT_SENKRECHT = "extrusion_nicht_senkrecht"

#: Die Grundrissebene ist geneigt. Dann gibt es keine **eine** Unterkante.
GRUNDRISSEBENE_NICHT_WAAGERECHT = "grundrissebene_nicht_waagerecht"

#: Die Extrusionsrichtung ist der Nullvektor.
EXTRUSIONSRICHTUNG_ENTARTET = "extrusionsrichtung_entartet"

#: Der Bezugspunkt, den :data:`hoehe_bezug` trägt, wenn eine Höhe gemessen wurde.
#:
#: Ausgeschrieben: *Länge des modellierten Raumkörpers nach oben, ab seiner eigenen
#: Unterkante* (``z_unten_m``). **Nicht** lichte Raumhöhe, **nicht** Geschosshöhe,
#: **nicht** Oberkante Rohdecke — welches davon der Exporteur gemeint hat, steht nicht in
#: der Datei.
HOEHE_BEZUG_RAUMKOERPER = "raumkoerper_ab_unterkante"

#: Wie senkrecht eine Extrusion sein muss, damit der Profilumriss der Grundriss ist.
#:
#: 0,999848 ist der Kosinus von einem Grad. Grosszügig gegen Rundungsrauschen aus
#: Rotationsmatrizen, streng gegen alles, was wirklich schief steht: Bei einem Grad
#: Neigung und 3 m Höhe wandert der Umriss um 5 cm — das ist die Grössenordnung, ab der
#: ein Standpunkt im Raum daneben liegen könnte.
SENKRECHT_TOLERANZ = 0.999848

#: Wie waagerecht die Grundrissebene sein muss, in Metern Höhenunterschied über den Ring.
#: Ein Millimeter ist mehr als jedes Rundungsrauschen und weniger als jede Absicht.
WAAGERECHT_TOLERANZ_M = 1.0e-3

#: Plausible Spanne für die **grösste waagerechte Ausdehnung eines Raums**, in Metern.
#:
#: Nicht dieselben Schranken wie in ``torwaechter`` (1 m bis 1000 m) — die gelten für ein
#: ganzes Bauwerk. Ein Raum unter einem halben Meter ist keiner (eine Besenkammer misst
#: 0,8 m), und über 200 m ist auch eine überdachte Halle hinaus. Für den Zweck der Prüfung
#: reicht das weit: Ein Faktor-1000-Fehler landet bei Millimetern oder bei Kilometern und
#: damit **weit** jenseits jeder dieser Grenzen. Eine Verwechslung ist ausgeschlossen.
MIN_RAUM_KANTE_M = 0.5
MAX_RAUM_KANTE_M = 200.0

#: Auf wie viele Nachkommastellen Meterwerte gerundet werden. Sechs sind ein Mikrometer —
#: jenseits jeder Bedeutung im Bauwesen und diesseits des Rundungsrauschens, das aus
#: Rotationsmatrizen kommt. Ohne diese Rundung trüge der Report Zahlen wie
#: ``4.699999999999999`` und jeder Vergleich zweier Läufe würde zur Glückssache.
NACHKOMMA = 6


def _r(wert: float) -> float:
    """Auf :data:`NACHKOMMA` runden — und ``-0.0`` zu ``0.0`` machen.

    ``-0.0`` ist rechnerisch dasselbe wie ``0.0``, in JSON aber ein anderer Text. Zwei
    Läufe derselben Datei sollen dieselbe Datei ergeben; sonst ist jeder Vergleich
    zweier Reports eine Diskussion über Vorzeichen von Null.
    """
    gerundet = round(float(wert), NACHKOMMA)
    return gerundet + 0.0 if gerundet != 0.0 else 0.0


def _befund(code: str, text: str) -> dict:
    """Ein Befund: Schlüssel zum Verzweigen, Satz für den Menschen."""
    return {"code": code, "text": text}


def _flaeche_signiert(ring) -> float:
    """Vorzeichenbehaftete Fläche eines Polygonrings (Gausssche Trapezformel).

    Das Vorzeichen ist die Auskunft: positiv heisst gegen den Uhrzeigersinn. Der Betrag
    ist die Fläche. Beides wird gebraucht — die Fläche als Grösse, der Umlaufsinn als
    Eigenschaft der Datei, die **nicht** stillschweigend begradigt wird. Ein Ring wird
    hier zurückgegeben, wie er in der Datei steht; wer eine Orientierung braucht, dreht
    ihn selbst und weiss dann, dass er es getan hat.
    """
    summe = 0.0
    for i in range(len(ring)):
        x1, y1 = ring[i]
        x2, y2 = ring[(i + 1) % len(ring)]
        summe += x1 * y2 - x2 * y1
    return summe / 2.0


def _ring_saeubern(punkte: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """Aufeinanderfolgende Doppelpunkte entfernen, auch den Schlusspunkt am Anfang.

    ``IfcPolyline`` einer geschlossenen Kurve wiederholt den ersten Punkt am Ende — das
    gehört zur Schreibweise und nicht zum Polygon. Bliebe er stehen, hätte jeder Raum
    eine Kante der Länge null, und die ist in jeder späteren Auswertung (Sichtprüfung,
    Punkt-in-Polygon) ein Sonderfall, den niemand behandelt.
    """
    sauber: list[tuple[float, float]] = []
    for p in punkte:
        if not sauber or abs(p[0] - sauber[-1][0]) > 1e-9 or abs(p[1] - sauber[-1][1]) > 1e-9:
            sauber.append(p)
    while len(sauber) > 1 and abs(sauber[0][0] - sauber[-1][0]) <= 1e-9 \
            and abs(sauber[0][1] - sauber[-1][1]) <= 1e-9:
        sauber.pop()
    return sauber


def _matrix_2d(position):
    """``IfcAxis2Placement2D`` als 3×3-Matrix (homogen), ``None`` wird zur Einheitsmatrix.

    Warum von Hand und nicht über ``ifcopenshell.util.placement``: Dessen Helfer sind auf
    3D-Platzierungen zugeschnitten. Die zweidimensionale Profilplatzierung ist drei Zeilen
    — und diese drei Zeilen sind der Unterschied zwischen einem Raum an seiner Stelle und
    einem Raum im Ursprung. ``IfcRectangleProfileDef`` trägt seine Ecken **nirgends** in
    der Datei; sie entstehen erst aus Breite, Tiefe und genau dieser Platzierung.
    """
    import numpy as np                    # noqa: PLC0415 — bewusst lokal, nur hier gebraucht

    if position is None:
        return np.eye(3)
    ox, oy = (list(position.Location.Coordinates) + [0.0, 0.0])[:2]
    if getattr(position, "RefDirection", None) is not None:
        rx, ry = (list(position.RefDirection.DirectionRatios) + [0.0, 0.0])[:2]
    else:
        rx, ry = 1.0, 0.0
    laenge = (rx * rx + ry * ry) ** 0.5
    if laenge == 0.0:                      # entartete Richtung — als „ungedreht" behandeln
        rx, ry, laenge = 1.0, 0.0, 1.0
    rx, ry = rx / laenge, ry / laenge
    return np.array([[rx, -ry, ox], [ry, rx, oy], [0.0, 0.0, 1.0]])


def _profil_ring(profil):
    """Die Umrisspunkte eines Profils in seinem eigenen Koordinatensystem.

    Returns:
        ``(punkte, quelle, hinweise, befund)``. ``punkte`` ist ``None``, wenn ``befund``
        gesetzt ist — beides zugleich gibt es nicht.
    """
    import numpy as np                    # noqa: PLC0415

    hinweise: list[str] = []

    if profil.is_a("IfcArbitraryClosedProfileDef"):
        if profil.is_a("IfcArbitraryProfileDefWithVoids"):
            hinweise.append(
                "Das Profil trägt Innenkurven (Aussparungen). Der gelieferte Grundriss "
                "ist nur die Aussenkontur — die Löcher fehlen darin."
            )
        kurve = profil.OuterCurve
        if not kurve.is_a("IfcPolyline"):
            return None, None, hinweise, _befund(
                PROFILKURVE_NICHT_UNTERSTUETZT,
                f"Die Profilkurve ist ein {kurve.is_a()}. Dieses Skript liest nur "
                f"IfcPolyline; alles andere würde geraten statt gelesen."
            )
        punkte = [tuple(p.Coordinates[:2]) for p in kurve.Points]
        return punkte, f"{profil.is_a()}/{kurve.is_a()}", hinweise, None

    if profil.is_a("IfcRectangleProfileDef"):
        if profil.is_a() != "IfcRectangleProfileDef":
            hinweise.append(
                f"Das Profil ist ein {profil.is_a()}; gelesen wird nur sein äusseres "
                f"Rechteck (XDim × YDim)."
            )
        bx, by = float(profil.XDim) / 2.0, float(profil.YDim) / 2.0
        # IfcRectangleProfileDef ist auf seinen Platzierungspunkt ZENTRIERT — es spannt
        # von -XDim/2 bis +XDim/2. Wer das übersieht, verschiebt jeden Raum um seine halbe
        # Grösse, und zwar gleichmässig, was besonders schlecht auffällt.
        ecken = [(-bx, -by), (bx, -by), (bx, by), (-bx, by)]
        m = _matrix_2d(profil.Position)
        punkte = [tuple((m @ np.array([x, y, 1.0]))[:2]) for x, y in ecken]
        return punkte, f"{profil.is_a()}", hinweise, None

    return None, None, hinweise, _befund(
        PROFIL_NICHT_POLYGONAL,
        f"Das Profil ist ein {profil.is_a()}. Daraus ein Polygon zu machen hiesse, eine "
        f"Auflösung zu erfinden, die in der Datei nicht steht."
    )


def _koerper_der_body_repraesentation(raum):
    """Den einen Extrusionskörper der ``Body``-Repräsentation holen.

    Returns:
        ``(solid, befund)`` — genau eines von beidem ist ``None``.
    """
    darstellung = getattr(raum, "Representation", None)
    reps = list(getattr(darstellung, "Representations", None) or []) if darstellung else []
    if not reps:
        return None, _befund(
            KEINE_REPRAESENTATION,
            "Der Raum trägt keine Geometrie. Viele Exporteure schreiben Zonen ohne "
            "Körper — dann steht der Raum in der Datei, aber seine Form nicht."
        )

    koerperreps = [r for r in reps if (r.RepresentationIdentifier or "") == "Body"]
    if not koerperreps:
        vorhanden = sorted({r.RepresentationIdentifier or "?" for r in reps})
        return None, _befund(
            KEINE_BODY_REPRAESENTATION,
            f"Der Raum hat Repräsentationen ({', '.join(vorhanden)}), aber keine 'Body'. "
            f"Gelesen wird nur der Körper — eine Fussabdruckkurve ('FootPrint') liest "
            f"dieses Skript nicht."
        )

    posten = [p for r in koerperreps for p in (r.Items or [])]
    solids = [p for p in posten if p.is_a("IfcExtrudedAreaSolid")]
    if not solids:
        arten = sorted({p.is_a() for p in posten}) or ["(leer)"]
        return None, _befund(
            KEIN_EXTRUSIONSKOERPER,
            f"Die Body-Repräsentation enthält kein IfcExtrudedAreaSolid, sondern "
            f"{', '.join(arten)}. Ein IfcBooleanClippingResult liesse sich auspacken, "
            f"indem man den Schnitt ignoriert — das wäre eine stillschweigend geänderte "
            f"Geometrie und wird hier nicht getan."
        )
    if len(solids) > 1:
        return None, _befund(
            MEHRERE_EXTRUSIONSKOERPER,
            f"Die Body-Repräsentation enthält {len(solids)} Extrusionskörper. Welcher "
            f"der Raum ist, sagt die Datei nicht; zu raten wäre schlimmer als zu schweigen."
        )
    return solids[0], None


def _geschoss_von(raum) -> tuple:
    """Das ``IfcBuildingStorey``, dem ein Raum angehört — ``(GlobalId, Name)`` oder ``(None, None)``.

    Von Hand und nicht über ``ifcopenshell.util.element.get_container``, aus einem Grund,
    der schon einmal Geld gekostet hat: Ein Helfer, dessen Suchreihenfolge man nicht
    sieht, liefert im Zweifel *irgendein* räumliches Element — und ein Raum, dem
    versehentlich das Gebäude statt das Geschoss zugeordnet wird, fällt niemandem auf.
    Hier steht die Reihenfolge da:

    1. ``Decomposes`` — der normgemässe Weg. Räume werden dem Geschoss über
       ``IfcRelAggregates`` **zugeordnet**, nicht über ``IfcRelContainedInSpatialStructure``
       **eingelagert**; letzteres ist für Bauteile gedacht.
    2. ``ContainedInStructure`` — der Weg, den manche Exporteure trotzdem nehmen. Ihn
       nicht zu kennen hiesse, an solchen Dateien ohne Not zu scheitern.

    Beide Wege laufen nach oben weiter, bis ein Geschoss kommt: Ein Raum kann in einem
    zusammengesetzten Raum stecken, der erst seinerseits im Geschoss hängt.
    """
    gesehen = set()
    kandidat = raum
    for _ in range(32):                    # Schleifenschutz: eine kaputte Datei darf nicht hängen
        if kandidat is None or kandidat.id() in gesehen:
            break
        gesehen.add(kandidat.id())
        eltern = None
        for beziehung in (getattr(kandidat, "Decomposes", None) or []):
            eltern = getattr(beziehung, "RelatingObject", None)
            break
        if eltern is None:
            for beziehung in (getattr(kandidat, "ContainedInStructure", None) or []):
                eltern = getattr(beziehung, "RelatingStructure", None)
                break
        if eltern is None:
            break
        if eltern.is_a("IfcBuildingStorey"):
            return eltern.GlobalId, eltern.Name
        kandidat = eltern
    return None, None


def _raum_lesen(raum, faktor: float) -> dict:
    """Einen ``IfcSpace`` in schlichte Daten übersetzen. Wirft nicht — meldet.

    Der Rückgabewert ist **immer** vollständig besetzt: Was nicht gemessen werden konnte,
    steht als ``None`` da, und ein Befund sagt warum. Ein Raum verschwindet nie.

    **Zwei Urteile, nicht eines.** Grundriss und Höhe sind zwei Messungen:

    * ``grundriss_m is None`` **genau dann**, wenn ``befund`` gesetzt ist,
    * ``hoehe_m is None`` **genau dann**, wenn ``hoehe_befund`` gesetzt ist.

    Gelernt an der schiefen Extrusion: Der Fussbodenumriss steht dann einwandfrei in der
    Datei, aber der Körper darüber schert weg — eine „Höhe über der Unterkante" gibt es
    nicht mehr. Wer für so einen Raum den Grundriss mitwegwirft, wirft eine gültige
    Messung weg; wer ihm eine Höhe gibt, erfindet eine.
    """
    import numpy as np                    # noqa: PLC0415
    import ifcopenshell.util.placement    # noqa: PLC0415

    geschoss_id, geschoss_name = _geschoss_von(raum)
    eintrag = {
        "global_id": raum.GlobalId,
        "name": raum.Name,                 # `$` in der Datei wird zu None, nicht zu ""
        "lang_name": getattr(raum, "LongName", None),
        "geschoss_global_id": geschoss_id,
        "geschoss_name": geschoss_name,
        "grundriss_m": None,
        "grundriss_quelle": None,
        "umlaufsinn": None,
        "flaeche_m2": None,
        "z_unten_m": None,
        "hoehe_m": None,
        "hoehe_bezug": None,
        "hoehe_begruendung": None,
        "befund": None,
        "hoehe_befund": None,
        "hinweise": [],
    }

    def ohne_hoehe(code: str, text: str) -> dict:
        """Den Eintrag mit gemessenem Grundriss und **nicht** gemessener Höhe abschliessen."""
        eintrag["hoehe_befund"] = _befund(code, text)
        eintrag["hoehe_begruendung"] = f"Nicht gemessen. {text}"
        return eintrag

    solid, befund = _koerper_der_body_repraesentation(raum)
    if befund is not None:
        eintrag["befund"] = befund
        return ohne_hoehe(HOEHE_OHNE_GRUNDRISS,
                          "Ohne Körper gibt es keine Höhe. Siehe `befund`.")

    punkte, quelle, hinweise, befund = _profil_ring(solid.SweptArea)
    eintrag["hinweise"] = list(hinweise)
    if befund is not None:
        eintrag["befund"] = befund
        return ohne_hoehe(
            HOEHE_OHNE_GRUNDRISS,
            "Ohne lesbaren Grundriss ist auch der Bezugspunkt der Höhe nicht bestimmt. "
            "Siehe `befund`.")

    # Zwei Matrizen hintereinander: erst die Lage des Körpers im Raum-Koordinatensystem
    # (`solid.Position`, in IFC4 optional), dann die Platzierungskette des Raums selbst
    # (Site → Building → Storey → Space). Wer eine davon auslässt, bekommt einen Raum an
    # der falschen Stelle — und weil alle Räume gleich falsch liegen, sieht der Grundriss
    # trotzdem plausibel aus.
    m_ort = ifcopenshell.util.placement.get_local_placement(
        getattr(raum, "ObjectPlacement", None))
    m_koerper = (ifcopenshell.util.placement.get_axis2placement(solid.Position)
                 if getattr(solid, "Position", None) is not None else np.eye(4))
    m = np.asarray(m_ort, dtype="float64") @ np.asarray(m_koerper, dtype="float64")

    welt = [m @ np.array([x, y, 0.0, 1.0]) for x, y in punkte]
    ring = _ring_saeubern([(_r(p[0] * faktor), _r(p[1] * faktor)) for p in welt])
    flaeche = _flaeche_signiert(ring)

    if len(ring) < 3 or abs(flaeche) <= 0.0:
        eintrag["befund"] = _befund(
            POLYGON_ENTARTET,
            f"Der Umriss ergibt {len(ring)} verschiedene Punkte und eine Fläche von "
            f"{abs(flaeche):.6g} m². Das ist kein Polygon."
        )
        return ohne_hoehe(HOEHE_OHNE_GRUNDRISS,
                          "Ohne Grundriss keine Höhe mit Bezugspunkt. Siehe `befund`.")

    eintrag["grundriss_m"] = [list(p) for p in ring]
    eintrag["grundriss_quelle"] = quelle
    eintrag["umlaufsinn"] = "gegen_uhrzeigersinn" if flaeche > 0 else "im_uhrzeigersinn"
    eintrag["flaeche_m2"] = _r(abs(flaeche))

    # ── Höhe. Ab hier ist der Grundriss gelesen und bleibt es auch, wenn die Höhe
    #    scheitert. Gemessen ist gemessen, auch teilweise — und was fehlt, hat einen
    #    eigenen Befund statt eines geliehenen.
    richtung = np.asarray(solid.ExtrudedDirection.DirectionRatios, dtype="float64")
    laenge = float(np.linalg.norm(richtung))
    if laenge == 0.0:
        return ohne_hoehe(
            EXTRUSIONSRICHTUNG_ENTARTET,
            "Die Extrusionsrichtung ist der Nullvektor — eine Höhe lässt sich daraus "
            "nicht ablesen. Der Grundriss steht trotzdem: Er ist das Profil, und das "
            "hängt nicht an der Richtung.")
    welt_richtung = m[:3, :3] @ (richtung / laenge)

    if abs(float(welt_richtung[2])) < SENKRECHT_TOLERANZ:
        return ohne_hoehe(
            EXTRUSION_NICHT_SENKRECHT,
            f"Die Extrusion läuft nicht senkrecht (Z-Anteil {float(welt_richtung[2]):.4f}, "
            f"verlangt sind {SENKRECHT_TOLERANZ}). Der Grundriss oben ist der Umriss des "
            f"Fussbodens und bleibt gültig; der Körper darüber schert aber weg, und eine "
            f"Höhe über dieser Unterkante gibt es damit nicht.")

    z_werte = [float(p[2]) * faktor for p in welt]
    if max(z_werte) - min(z_werte) > WAAGERECHT_TOLERANZ_M:
        return ohne_hoehe(
            GRUNDRISSEBENE_NICHT_WAAGERECHT,
            f"Die Grundrissebene ist nicht waagerecht: Die Umrisspunkte liegen "
            f"{max(z_werte) - min(z_werte):.4g} m auseinander. Es gibt also keine EINE "
            f"Unterkante, auf die sich eine Höhe beziehen könnte. Der Grundriss oben ist "
            f"die Projektion dieser geneigten Fläche in die Waagerechte.")

    hub = float(solid.Depth) * float(welt_richtung[2]) * faktor
    basis = sum(z_werte) / len(z_werte)
    if hub < 0.0:
        eintrag["hinweise"].append(
            "Die Extrusion läuft nach unten; `z_unten_m` ist das untere Ende des Körpers "
            "und nicht die Profilebene."
        )
    eintrag["z_unten_m"] = _r(min(basis, basis + hub))
    eintrag["hoehe_m"] = _r(abs(hub))
    eintrag["hoehe_bezug"] = HOEHE_BEZUG_RAUMKOERPER
    eintrag["hoehe_begruendung"] = (
        "Länge des modellierten Raumkörpers nach oben, ab `z_unten_m`. `z_unten_m` ist "
        "die Unterkante dieses Körpers in IFC-Weltkoordinaten (Projektnullpunkt, ohne "
        "IfcSite.RefElevation und ohne Georeferenzierung) — weder eine Höhe über Meer "
        "noch eine über Gelände. Ob die Höhe die LICHTE Raumhöhe, die GESCHOSSHÖHE oder "
        "etwas dazwischen meint, sagt die Datei nicht; das ist eine Gewohnheit des "
        "erzeugenden Programms und keine Angabe im Modell."
    )
    return eintrag


def _pruefe_masse(raeume: list[dict], einheit: dict) -> tuple:
    """Sind die herausgekommenen Raumgrössen plausibel? — die Gegenprobe zur Einheit.

    Der Fall, für den das gebaut ist, ist **nicht** „die Datei steht in Millimetern" — das
    rechnet der Einheitenfaktor sauber um. Der Fall ist der kaputte Export: Die Datei
    **erklärt** Millimeter und trägt Zahlen in Metergrösse. Dann kommen Räume von acht
    Millimetern heraus, und das ist keine Eingabe, die man glättet, sondern eine, die man
    meldet. Zwei von 40 echten Dateien waren so (`auf-20260818-08`).

    Returns:
        ``(plausibel, befund)``. ``plausibel`` ist ``None``, wenn **kein** Raum einen
        Grundriss hat — dann wurde nichts gemessen, und *nicht gemessen* ist kein Urteil.
    """
    kanten = []
    for r in raeume:
        if not r["grundriss_m"]:
            continue
        xs = [p[0] for p in r["grundriss_m"]]
        ys = [p[1] for p in r["grundriss_m"]]
        kanten.append(max(max(xs) - min(xs), max(ys) - min(ys)))
    if not kanten:
        return None, ("Kein Raum mit lesbarem Grundriss — es wurde nichts gemessen, was "
                      "sich gegen die erklärte Einheit halten liesse.")

    groesste = max(kanten)
    erklaert = einheit.get("erklaert") or "?"
    faktor = einheit.get("meter_je_einheit")
    if MIN_RAUM_KANTE_M <= groesste <= MAX_RAUM_KANTE_M:
        return True, (
            f"Die Datei erklärt {erklaert}, und der grösste Raum misst {groesste:.3g} m in "
            f"der Waagerechten. Das passt zusammen."
        )
    if faktor and faktor != 1.0 and MIN_RAUM_KANTE_M <= groesste / faktor <= MAX_RAUM_KANTE_M:
        return False, (
            f"KAPUTTER EXPORT, benennbar: Die Datei erklärt {erklaert} (Faktor {faktor:g}), "
            f"heraus kommt aber ein grösster Raum von {groesste:.3g} m. Rechnet man den "
            f"erklärten Faktor heraus, ergäbe das {groesste / faktor:.3g} m — ein "
            f"plausibler Raum. Die Zahlen in der Datei standen also nie in der erklärten "
            f"Einheit. Nicht der Leser ist schuld, sondern der Export."
        )
    return False, (
        f"Die Datei erklärt {erklaert}, heraus kommt ein grösster Raum von {groesste:.3g} m "
        f"— das liegt ausserhalb von {MIN_RAUM_KANTE_M} m bis {MAX_RAUM_KANTE_M} m. Der "
        f"erklärte Faktor erklärt die Abweichung nicht; die Ursache liegt woanders als in "
        f"der Einheit."
    )


def _einheit_lesen(modell) -> tuple:
    """Längeneinheit und Umrechnungsfaktor der Datei.

    Returns:
        ``(einheit, warnungen)``. ``meter_je_einheit`` ist ``None``, wenn sich nichts
        sagen lässt — das heisst **nicht 1.0**, sondern *unbekannt*. Wer das verwechselt,
        baut genau den mm-als-m-Fehler ein, den ``torwaechter`` fängt.
    """
    import ifcopenshell.util.unit          # noqa: PLC0415

    warnungen: list[str] = []
    name = vorsatz = None
    einheitsobjekt = None
    try:
        einheitsobjekt = ifcopenshell.util.unit.get_project_unit(modell, "LENGTHUNIT")
    except Exception as fehler:            # eine kaputte Einheitenzuweisung ist kein Absturz
        warnungen.append(f"Längeneinheit nicht lesbar: {type(fehler).__name__}: {fehler}")
    if einheitsobjekt is not None:
        name = getattr(einheitsobjekt, "Name", None)
        vorsatz = getattr(einheitsobjekt, "Prefix", None)

    faktor = None
    try:
        faktor = float(ifcopenshell.util.unit.calculate_unit_scale(modell))
    except Exception as fehler:
        warnungen.append(
            f"Einheitenfaktor nicht bestimmbar ({type(fehler).__name__}: {fehler}). "
            f"Alle Längen bleiben in Dateieinheiten — sie sind dann NICHT in Metern."
        )
    if faktor is None:
        warnungen.append(
            "Ohne Einheitenfaktor sind die gelieferten Zahlen keine Meter. `meter_je_"
            "einheit` steht auf None, und das heisst unbekannt und nicht 1.0."
        )

    erklaert = f"{(vorsatz or '').lower()}{(name or '?').lower()}"
    return {
        "laengeneinheit": name,
        "vorsatz": vorsatz,
        "meter_je_einheit": faktor,
        "erklaert": erklaert,
        "quelle": "IfcUnitAssignment des IfcProject",
    }, warnungen


def raeume_lesen(ifc_path: str) -> dict:
    """Alle ``IfcSpace`` einer IFC-Datei als schlichte Daten. Liefert immer einen Report.

    Zusicherung: ``len(report["raeume"]) == report["n_raeume"]`` und beides ist die Zahl
    der ``IfcSpace`` in der Datei. Ein Raum, dessen Grundriss sich nicht lesen lässt,
    steht mit ``grundriss_m = None`` und einem ``befund`` da — er wird **nie** weggelassen.

    Null Räume sind **kein Fehler**: Die meisten IFC-Dateien tragen gar keine ``IfcSpace``.
    Der Report sagt dann ``status: "ok"``, ``n_raeume: 0`` und nennt es in ``warnungen``.
    Ein Fehlerstatus dafür hiesse, einer gültigen Datei die Schuld für eine leere Antwort
    zu geben.
    """
    import ifcopenshell                    # noqa: PLC0415 — bewusst lokal: nur in diesem Prozess

    modell = ifcopenshell.open(ifc_path)
    schema = str(getattr(modell, "schema", "") or "")
    einheit, warnungen = _einheit_lesen(modell)
    faktor = einheit["meter_je_einheit"]
    # Ohne Faktor wird NICHT umgerechnet — und die Warnung oben sagt, dass die Zahlen
    # dann keine Meter sind. Still 1.0 einzusetzen wäre die bequeme Lüge.
    rechenfaktor = 1.0 if faktor is None else faktor

    if schema.upper() not in ("IFC4", "IFC2X3"):
        warnungen.append(
            f"Schemafassung {schema!r} — geprüft ist dieses Skript gegen IFC4 und IFC2X3. "
            f"Gelesen wird trotzdem; die Attributnamen könnten aber abweichen."
        )

    raeume = [_raum_lesen(raum, rechenfaktor) for raum in modell.by_type("IfcSpace")]
    if not raeume:
        warnungen.append(
            "Die Datei enthält keinen einzigen IfcSpace. Das ist kein Fehler — viele "
            "Modelle tragen gar keine Räume —, aber es heisst: Hier gibt es nichts, "
            "worauf sich eine Innenaufnahme stützen könnte."
        )

    plausibel, masse_befund = _pruefe_masse(raeume, einheit)
    mit_grundriss = sum(1 for r in raeume if r["grundriss_m"] is not None)
    mit_hoehe = sum(1 for r in raeume if r["hoehe_m"] is not None)

    return {
        "status": "ok",
        "ifc_path": str(ifc_path),
        "schema": schema or None,
        "einheit": einheit,
        "n_raeume": len(raeume),
        "n_mit_grundriss": mit_grundriss,
        "n_ohne_grundriss": len(raeume) - mit_grundriss,
        "n_mit_hoehe": mit_hoehe,
        "n_ohne_hoehe": len(raeume) - mit_hoehe,
        "raeume": raeume,
        "masse_plausibel": plausibel,
        "masse_befund": masse_befund,
        "hoehe_bezug_erklaerung": (
            "`hoehe_m` ist die Länge des modellierten Raumkörpers nach oben, ab "
            "`z_unten_m`. `z_unten_m` liegt in IFC-Weltkoordinaten (Projektnullpunkt), "
            "NICHT über Meer und NICHT über Gelände. Ob `hoehe_m` die lichte Raumhöhe "
            "oder die Geschosshöhe meint, sagt die Datei nicht."
        ),
        "warnungen": warnungen,
        "error": None,
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="IfcSpace → JSON (Meter). Läuft im .venv-ifc.")
    ap.add_argument("ifc")
    ap.add_argument("--report", default=None)
    a = ap.parse_args(argv)

    try:
        rep = raeume_lesen(a.ifc)
    except Exception as e:                 # Fehler als Report, nicht als Traceback
        rep = {"status": "error", "error": f"{type(e).__name__}: {e}",
               "ifc_path": str(a.ifc), "raeume": [], "n_raeume": 0}

    text = json.dumps(rep, indent=2, ensure_ascii=False)
    if a.report:
        with open(a.report, "w", encoding="utf-8") as fh:
            fh.write(text)
    print(text)
    return 0 if rep["status"] == "ok" else 1


if __name__ == "__main__":
    sys.exit(main())
