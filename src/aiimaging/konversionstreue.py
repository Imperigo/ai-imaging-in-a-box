"""Stimmt die umgewandelte Geometrie — oder ist sie bloss **durchgelaufen**?

**Der Anlass ist eine Lücke, die beide Seiten teilen** (HomeStation,
`BEFUND_2026-08-24_IFC-LESER.md`, 24.08.2026): Neun echte IFC durch zwei Leser, 9 von 9
``ok``, null Geometriefehler — *«Belegt ist bisher nur, dass die Konversion durchläuft.
Nicht, ob die Geometrie stimmt. Kein Mass vergleicht die 27 000 Dreiecke mit dem, was in
der IFC steht.»*

**«Durchgelaufen» ist kein Qualitätsmerkmal.** Genau dieselbe Verwechslung stand am Anfang
der Geometrie-QA: Ein Score über das ganze Bild lief ebenfalls durch und beantwortete
nicht, ob im Bild ein Bauwerk steht.

**Warum das mit synthetischer Geometrie geht und mit echter nicht.** Bei einer echten IFC
kennt niemand die Wahrheit — man müsste sie mit demselben Werkzeug ausrechnen, das man
prüfen will (Kreisschluss). Bei ``tools/make_test_ifc.py`` kennen wir jede Kante, **weil
wir sie geschrieben haben**. Die Erwartung kommt darum von aussen herein und steht nicht
in diesem Modul: Eine Zahl, die an zwei Stellen steht, ist an einer davon bereits falsch.

**Was dieses Modul ausdrücklich NICHT prüft:** ob eine *echte* IFC richtig umgewandelt
wurde. Es prüft das **Werkzeug** an einem Fall, dessen Antwort feststeht. Läuft es dort
schief, läuft es überall schief; läuft es dort richtig, ist über echte Dateien nichts
bewiesen — nur etwas ausgeschlossen.

Regel 2: Dieses Modul liest ein Wörterbuch. Es importiert **keinen Runner** und kein
``ifcopenshell``.
"""
from __future__ import annotations

from collections.abc import Sequence

__all__ = ["KonversionsError", "TOLERANZ_M", "MASSSTAB_VERDACHT", "pruefe_konversion",
           "spanne_aus_bbox"]


class KonversionsError(ValueError):
    """Die Eingabe lässt sich nicht als Bericht lesen."""


#: Wieviel eine Kante abweichen darf, in Metern. **Eng, und das ist Absicht.**
#:
#: Ein Quader aus einer IFC-Extrusion wird nicht vernetzt oder angenähert — seine acht
#: Ecken stehen in der Datei. Was hier ankommt, sind Rundungsfehler von
#: Gleitkommarechnung und Einheitenumrechnung, nicht Verfahrensfehler. Wer diese Zahl
#: lockern muss, hat einen Befund und keine Toleranzfrage.
TOLERANZ_M = 1.0e-4

#: Faktoren, bei denen ein Grössenfehler **einen Namen hat** statt bloss eine Zahl zu sein.
#:
#: Die beiden häufigsten Fehler beim IFC-Lesen sind nicht «etwas ungenau», sondern grob
#: und benennbar:
#:
#: * **1000** — Millimeter als Meter gelesen (oder umgekehrt). ``IfcSIUnit`` trägt den
#:   Vorsatz ``MILLI``; wer ``IfcUnitAssignment`` überspringt, bekommt ein Haus von acht
#:   Kilometern Länge. ``make_test_ifc.py`` schreibt diesen Fall eigens (``--mm``).
#: * **100 / 10** — Zentimeter oder Dezimeter, seltener, aber dieselbe Ursache.
#: * **0.3048** — Fuss. Kommt in Dateien aus dem angelsächsischen Raum vor.
#:
#: Ein Faktor, der zu keinem davon passt, ist ein **anderer** Fehler und wird auch so
#: gemeldet — eine Diagnose zu raten wäre schlimmer als keine.
MASSSTAB_VERDACHT = {
    1000.0: "Millimeter als Meter gelesen (IfcSIUnit-Vorsatz MILLI übergangen)",
    0.001: "Meter als Millimeter gelesen",
    100.0: "Zentimeter als Meter gelesen",
    10.0: "Dezimeter als Meter gelesen",
    0.3048: "Fuss als Meter gelesen",
    3.28084: "Meter als Fuss gelesen",
}

#: Wie nah ein gemessener Faktor an einem benannten liegen muss, damit er so heisst.
MASSSTAB_NAEHE = 0.02


def spanne_aus_bbox(bbox) -> tuple[float, float, float]:
    """``[[minx,miny,minz],[maxx,maxy,maxz]]`` → die drei Kantenlängen.

    Raises:
        KonversionsError: Die Hüllbox hat nicht die Form zweier Punkte mit je drei Zahlen.
    """
    if not isinstance(bbox, Sequence) or isinstance(bbox, (str, bytes)) or len(bbox) != 2:
        raise KonversionsError(
            f"bbox muss zwei Punkte tragen (min und max), war {bbox!r}.")
    unten, oben = bbox
    for name, punkt in (("min", unten), ("max", oben)):
        if (not isinstance(punkt, Sequence) or isinstance(punkt, (str, bytes))
                or len(punkt) != 3):
            raise KonversionsError(f"bbox[{name}] braucht drei Zahlen, war {punkt!r}.")
    try:
        return tuple(float(oben[i]) - float(unten[i]) for i in range(3))
    except (TypeError, ValueError) as fehler:
        raise KonversionsError(f"bbox enthält keine Zahlen: {bbox!r}") from fehler


def _massstabsname(faktor: float) -> str | None:
    for wert, name in MASSSTAB_VERDACHT.items():
        if abs(faktor - wert) <= MASSSTAB_NAEHE * wert:
            return name
    return None


def pruefe_konversion(bericht: dict, *, huellbox_m: Sequence[float],
                      n_bauteile: int | None = None, n_dreiecke: int | None = None,
                      toleranz_m: float = TOLERANZ_M) -> dict:
    """Vergleicht den Bericht einer Umwandlung mit der **bekannten** Wahrheit.

    Args:
        bericht: Antwort des IFC→glb-Runners. Gelesen werden ``bbox`` (in nativen
            IFC-Metern, Z oben), ``n_elements`` und ``n_triangles``.
        huellbox_m: Die drei Kantenlängen, die herauskommen **müssen** — vom Aufrufer,
            nicht aus diesem Modul. Bei ``tools/make_test_ifc.py`` sind das die Zahlen,
            mit denen die Datei geschrieben wurde.
        n_bauteile, n_dreiecke: Erwartete Anzahlen, oder ``None`` für «nicht geprüft».
            ``None`` heisst hier **nicht geprüft** und nicht «egal» — es steht so im
            Ergebnis.

    Returns:
        ``{stimmt, gemessen, spanne, erwartet, abweichungen, diagnose, warnungen}``.

        * ``stimmt`` ist ``None``, solange etwas fehlt. **Nicht** ``False``: «nicht
          nachgeprüft» und «falsch umgewandelt» sind verschiedene Auskünfte, und die
          zweite schickt jemanden auf eine Fehlersuche, die es nicht gibt.
        * ``diagnose`` benennt den Fehler, wo er einen Namen hat — ein **Massstabsfehler**
          (siehe :data:`MASSSTAB_VERDACHT`) oder eine **vertauschte Achse**. Beides ist an
          IFC-Dateien üblich, und beides sieht in einer reinen Zahlenabweichung gleich aus.

    Raises:
        KonversionsError: ``bericht`` ist kein Wörterbuch, ``huellbox_m`` hat nicht drei
            Einträge, oder die Toleranz ist negativ.
    """
    if not isinstance(bericht, dict):
        raise KonversionsError(
            f"bericht ist kein Wörterbuch: {type(bericht).__name__}")
    if (not isinstance(huellbox_m, Sequence) or isinstance(huellbox_m, (str, bytes))
            or len(huellbox_m) != 3):
        raise KonversionsError(
            f"huellbox_m braucht drei Kantenlängen, war {huellbox_m!r}.")
    if toleranz_m < 0:
        raise KonversionsError(f"toleranz_m darf nicht negativ sein, war {toleranz_m}.")

    erwartet = tuple(float(w) for w in huellbox_m)
    antwort = {"stimmt": None, "gemessen": False, "spanne": None, "erwartet": erwartet,
               "abweichungen": [], "diagnose": None, "warnungen": []}

    if bericht.get("status") != "ok":
        antwort["warnungen"].append(
            f"Der Bericht meldet status={bericht.get('status')!r}, nicht 'ok'. Eine "
            f"Umwandlung, die gar nicht durchlief, ist NICHT GEPRUEFT und nicht falsch — "
            f"der Fehler steht dort: {bericht.get('error')!r}")
        return antwort
    if bericht.get("bbox") is None:
        antwort["warnungen"].append(
            "Der Bericht trägt keine Hüllbox. Ohne sie gibt es nichts zu vergleichen — "
            "NICHT GEPRUEFT.")
        return antwort

    spanne = spanne_aus_bbox(bericht["bbox"])
    antwort["spanne"] = spanne
    antwort["gemessen"] = True

    abweichungen = []
    for achse, ist, soll in zip("XYZ", spanne, erwartet):
        if abs(ist - soll) > toleranz_m:
            abweichungen.append({"achse": achse, "ist": ist, "soll": soll,
                                 "faktor": (ist / soll) if soll else None})
    antwort["abweichungen"] = abweichungen

    # ── Die Diagnose, und sie ist der eigentliche Ertrag ──────────────────────────────
    #
    # Eine Liste von Abweichungen sagt DASS etwas nicht stimmt. Die beiden haeufigsten
    # IFC-Fehler haben aber einen Namen, und wer den Namen liest, weiss sofort, wo er
    # nachsehen muss.
    if abweichungen:
        faktoren = [a["faktor"] for a in abweichungen if a["faktor"]]
        if len(abweichungen) == 3 and faktoren and all(
                abs(f - faktoren[0]) <= MASSSTAB_NAEHE * abs(faktoren[0])
                for f in faktoren):
            name = _massstabsname(faktoren[0])
            antwort["diagnose"] = (
                f"MASSSTAB: alle drei Achsen um denselben Faktor {faktoren[0]:.6g} daneben"
                + (f" — {name}." if name else
                   ". Zu keinem bekannten Einheitenfehler passend; die Ursache liegt "
                   "woanders und wird hier NICHT geraten."))
        elif sorted(round(w, 6) for w in spanne) == sorted(round(w, 6) for w in erwartet):
            antwort["diagnose"] = (
                f"ACHSEN VERTAUSCHT: Dieselben drei Kantenlängen, andere Reihenfolge — "
                f"gemessen {tuple(round(w, 4) for w in spanne)}, erwartet "
                f"{tuple(round(w, 4) for w in erwartet)}. Das Bauwerk ist nicht falsch "
                f"gross, sondern falsch gedreht; ein häufiger Fall ist eine übersehene "
                f"Z-oben/Y-oben-Umrechnung.")
        else:
            antwort["diagnose"] = (
                f"{len(abweichungen)} von 3 Achsen weichen ab, und zwar verschieden "
                f"stark. Das ist weder ein Einheiten- noch ein Drehfehler — die Geometrie "
                f"selbst ist eine andere.")

    for name, ist_wert, soll_wert in (("Bauteile", bericht.get("n_elements"), n_bauteile),
                                      ("Dreiecke", bericht.get("n_triangles"), n_dreiecke)):
        if soll_wert is None:
            continue
        if ist_wert is None:
            antwort["warnungen"].append(
                f"{name}: erwartet {soll_wert}, der Bericht nennt keine Zahl. NICHT "
                f"GEPRUEFT.")
            continue
        if int(ist_wert) != int(soll_wert):
            abweichungen.append({"achse": name, "ist": int(ist_wert),
                                 "soll": int(soll_wert), "faktor": None})

    antwort["stimmt"] = not abweichungen
    return antwort
