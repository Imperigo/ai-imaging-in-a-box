"""Woher kommt diese Datei, und was sagt sie selbst über sich? — die Connector-Schicht.

Warum es dieses Modul gibt
--------------------------
`docs/PLAN.md` führt unter Phase 4 „Connectors: ArchiCAD über IFC4, Rhino über glTF".
Ein Connector ist dabei **kein Import-Filter** — IFC und glTF liest das Projekt längst.
Was fehlt, ist die Antwort auf die Frage, die zwischen zwei Autorenprogrammen wirklich
unterschiedlich ausfällt:

    In welcher Einheit sind die Zahlen, und wo ist oben?

Beides wurde bisher **nicht gelesen, sondern vorausgesetzt.** Das ist die Lücke.

Die Einheit — und die Annahme, die sich beim Messen als falsch erwies
---------------------------------------------------------------------
Dieses Modul entstand aus der Annahme, ein ArchiCAD-Export in Millimetern käme als Gebäude
von 8000 × 5000 × 3250 Metern an, weil niemand im Projekt die Einheitenzeile liest.

**Die Annahme ist falsch, und zwar gemessen** (18.08.2026): Eine realistische
ArchiCAD-Datei — `.MILLI.` in der Einheitenzuweisung *und* tausendfach grössere
Koordinaten — läuft durch `seams.ifc_zu_glb` und kommt bei exakt **8,0 × 5,0 × 3,25 m**
heraus. IfcOpenShell wendet den Einheitenfaktor selbst an. Der Torwächter nimmt an.

**Für ArchiCAD über IFC4 braucht es also keine Umrechnung.** Das ist ein Ergebnis, kein
Versäumnis: Ein Connector, der ein gelöstes Problem noch einmal löst, verdoppelt es.

Wofür das Einheitenlesen trotzdem gut ist: als **Gegenprobe**
--------------------------------------------------------------
Beim Messen fiel der Fall auf, den es wirklich gibt. Nimmt man dieselbe Datei, setzt aber
nur die Einheit auf `.MILLI.` und lässt die Zahlen metergross, entsteht ein Bauwerk von
8 Millimetern. Der Torwächter fängt es — mit der Meldung *„Massstab unplausibel …
**Verdacht** auf Einheitenfehler um Faktor 0,001"*.

Ein Verdacht. Mit dem Dateikopf daneben wird daraus eine **Diagnose**: Die Datei erklärt
Millimeter, trägt aber Zahlen in Metergrösse — der Export ist kaputt, und zwar in einer
benennbaren Weise. Das leistet :func:`pruefe_einheit_gegen_masse`.

Der Unterschied ist nicht kosmetisch. Ein Verdacht kostet jedes Mal einen Menschen, der
nachsieht; eine Diagnose sagt ihm, wo.

Die Up-Achse — und warum sie hier NICHT bequemer wird
------------------------------------------------------
Phase 0 hat festgestellt: **glTF 2.0 kennt kein Up-Achsen-Feld**, und die Erzeuger im
Ökosystem sind sich uneinig (KosmoDraw Z-up, KosmoVis Y-up). Darum ist `up_axis` in
`contracts.normalize_up_axis` ein **Pflichtfeld ohne Vorgabewert** — ein Default wäre eine
stille Verdrehung.

Dieses Modul hebelt das **nicht** aus. Es unterscheidet drei Fälle, und der Unterschied
ist die ganze Sache:

* :data:`BELEGT` — die Datei sagt es, überprüfbar. **Nur IFC.** Die Norm legt fest, dass
  ein IFC-Modell Z-up ist; das ist keine Konvention eines Herstellers, sondern der
  Standard. Ein belegter Wert ist eine Messung und darf verwendet werden.
* :data:`VERMUTET` — der Erzeuger ist bekannt und seine Gewohnheit auch, aber die Datei
  selbst sagt nichts. **Der Normalfall bei glTF.** Eine Vermutung darf **nicht**
  stillschweigend zur Vorgabe werden; sie wird zurückgegeben, damit ein Mensch oder ein
  Aufrufer sie bestätigt.
* :data:`UNBEKANNT` — nichts davon. Dann bleibt es beim Pflichtfeld.

**Die Regel dieses Moduls:** Es *deutet*, es *entscheidet* nicht. Wer aus einer Vermutung
eine Tatsache macht, tut das an einer Stelle, wo es steht.

Was dieses Modul NICHT leistet
-------------------------------
Es hat **keine ArchiCAD-, Revit- oder Rhino-Datei gesehen.** Die Einträge in
:data:`HERKUENFTE` sind aus den Formatspezifikationen und der Dokumentation abgeleitet und
im Feld `beleg` als solche gekennzeichnet. Die IFC-Einheitenzeile ist Norm und damit sicher;
welche Zeichenkette ArchiCAD in `FILE_NAME` schreibt, ist es nicht. Wer eine echte Datei
hat, trägt den gemessenen Wert ein und ändert `beleg` — dafür ist das Feld da.
"""
from __future__ import annotations

import json
import re
import struct
from dataclasses import dataclass
from pathlib import Path

#: Wie gut die Up-Achse belegt ist.
BELEGT = "belegt"
VERMUTET = "vermutet"
UNBEKANNT = "unbekannt"

#: Wieviel vom Dateianfang gelesen wird, wenn die Datei gross ist.
#:
#: Eine echte IFC kann hunderte Megabyte haben; der Kopf und die Einheitenzuweisung stehen
#: aber am Anfang, weil der Rest auf sie verweist und STEP-Verweise vorwärts gerichtet
#: sind. Zwei Megabyte sind grosszügig. **Findet sich in diesem Fenster nichts, wird das
#: gemeldet** — nicht als „keine Einheit gefunden" (das hiesse: es gibt keine), sondern als
#: „im gelesenen Anfang nicht gefunden".
LESEFENSTER_BYTE = 2 * 1024 * 1024

#: SI-Vorsätze aus ISO 10303 / IFC, als Faktor auf die Grundeinheit.
SI_VORSAETZE: dict[str, float] = {
    "EXA": 1e18, "PETA": 1e15, "TERA": 1e12, "GIGA": 1e9, "MEGA": 1e6, "KILO": 1e3,
    "HECTO": 1e2, "DECA": 1e1,
    "DECI": 1e-1, "CENTI": 1e-2, "MILLI": 1e-3, "MICRO": 1e-6, "NANO": 1e-9,
    "PICO": 1e-12, "FEMTO": 1e-15, "ATTO": 1e-18,
}


class HerkunftError(ValueError):
    """Die Datei lässt sich nicht als IFC oder glTF deuten."""


@dataclass(frozen=True)
class Herkunft:
    """Ein Autorenprogramm und das, was es gewohnheitsmässig schreibt.

    `beleg` ist bewusst ein eigenes Feld: Bei IFC ist die Up-Achse Norm, bei glTF ist sie
    Herstellergewohnheit — und der Unterschied darf nicht im Kopf des Lesers bleiben.
    """

    name: str
    #: Teilzeichenketten, an denen der Erzeuger erkannt wird. Kleingeschrieben verglichen.
    kennungen: tuple[str, ...]
    up_axis: str | None
    sicherheit: str
    beleg: str
    bemerkung: str = ""


HERKUENFTE: tuple[Herkunft, ...] = (
    Herkunft(
        name="ArchiCAD",
        kennungen=("archicad", "graphisoft"),
        up_axis="Z_UP", sicherheit=BELEGT,
        beleg="IFC-Norm (ISO 16739): ein IFC-Modell ist Z-up. Nicht Herstellergewohnheit.",
        bemerkung=("Exportiert üblicherweise in **Millimetern**. Die Einheit steht in der "
                   "Datei und wird gelesen — geraten wird sie nicht."),
    ),
    Herkunft(
        name="Revit",
        kennungen=("revit", "autodesk"),
        up_axis="Z_UP", sicherheit=BELEGT,
        beleg="IFC-Norm (ISO 16739).",
        bemerkung="Exportiert üblicherweise in Millimetern.",
    ),
    Herkunft(
        name="IfcOpenShell",
        kennungen=("ifcopenshell",),
        up_axis="Z_UP", sicherheit=BELEGT,
        beleg="IFC-Norm (ISO 16739). Der eigene Konverter dieses Projekts.",
    ),
    Herkunft(
        name="Rhino",
        kennungen=("rhino", "rhinoceros", "mcneel"),
        up_axis=None, sicherheit=UNBEKANNT,
        beleg=("KEINE Aussage möglich. Rhinos Modellraum ist Z-up, die glTF-Norm schreibt "
               "Y-up vor, und Rhinos Exporter hat dafür einen **Schalter**. Was in der "
               "Datei steht, hängt also an einer Einstellung, die die Datei nicht "
               "mitteilt."),
        bemerkung=("Der ehrlichste Fall im ganzen Modul: Hier ist die Vermutung nicht "
                   "schwach, sondern unmöglich. Der Aufrufer muss `up_axis` angeben."),
    ),
    Herkunft(
        name="Blender",
        kennungen=("blender",),
        up_axis="Y_UP", sicherheit=VERMUTET,
        beleg=("Blenders glTF-Exporter rechnet nach Norm auf Y-up um; das ist die "
               "Vorgabe seines Exporters, aber abschaltbar."),
    ),
    Herkunft(
        name="KosmoDraw",
        kennungen=("kosmodraw",),
        up_axis="Z_UP", sicherheit=VERMUTET,
        beleg=("Phase-0-Befund vom 14.08.2026 aus der Lektüre von KosmoDraw, siehe "
               "docs/EINBINDUNG_KOSMOORBIT_2026-08-14.md §8. Aus dem Quelltext gelesen, "
               "nicht an einer Datei gemessen."),
    ),
    Herkunft(
        name="KosmoVis",
        kennungen=("kosmovis",),
        up_axis="Y_UP", sicherheit=VERMUTET,
        beleg="Phase-0-Befund vom 14.08.2026, ebenda. Aus der Dokumentation, nicht gemessen.",
    ),
)


def _erkenne(text: str) -> Herkunft | None:
    """Welcher Erzeuger steckt in dieser Zeichenkette? ``None``, wenn keiner passt."""
    klein = (text or "").lower()
    for h in HERKUENFTE:
        if any(k in klein for k in h.kennungen):
            return h
    return None


# ── IFC ──────────────────────────────────────────────────────────────────────────────

_RE_SIUNIT = re.compile(
    r"IFCSIUNIT\s*\(\s*[^,]*,\s*\.LENGTHUNIT\.\s*,\s*(\$|\.([A-Z]+)\.)\s*,\s*\.([A-Z_]+)\.",
    re.IGNORECASE)
_RE_CONVUNIT = re.compile(
    r"IFCCONVERSIONBASEDUNIT\s*\(\s*[^,]*,\s*\.LENGTHUNIT\.\s*,\s*'([^']*)'", re.IGNORECASE)
_RE_SCHEMA = re.compile(r"FILE_SCHEMA\s*\(\s*\(\s*'([^']*)'", re.IGNORECASE)
_RE_FILENAME = re.compile(r"FILE_NAME\s*\((.*?)\)\s*;", re.IGNORECASE | re.DOTALL)


def lies_ifc_kopf(pfad) -> dict:
    """Kopf und Längeneinheit einer IFC-Datei lesen. Reine stdlib, ohne IfcOpenShell.

    Warum ohne IfcOpenShell: Es lebt jenseits einer Prozessgrenze in eigenem venv
    (Regel 1/2). Für zwei Zeilen Kopf einen Subprozess zu starten, wäre eine
    Prozessgrenze für eine Textsuche — und die Antwort wird gebraucht, **bevor**
    entschieden ist, ob konvertiert wird.

    Returns:
        ``{schema, laengeneinheit, vorsatz, meter_je_einheit, erzeuger, herkunft,
        up_axis, sicherheit, begruendung, warnungen, vollstaendig_gelesen}``

        ``meter_je_einheit`` ist der Faktor, mit dem die Zahlen der Datei in Meter
        übergehen: 1.0 bei Metern, 0.001 bei Millimetern. ``None`` heisst **nicht 1.0**,
        sondern *unbekannt* — wer das verwechselt, baut den mm-als-m-Fehler ein, den der
        `torwaechter` fängt.

    Raises:
        HerkunftError: Die Datei ist keine STEP/IFC-Datei oder nicht lesbar.
    """
    pfad = Path(pfad)
    try:
        roh = pfad.read_bytes()[:LESEFENSTER_BYTE]
    except OSError as fehler:
        raise HerkunftError(f"{pfad} lässt sich nicht lesen: {fehler}") from fehler
    vollstaendig = pfad.stat().st_size <= LESEFENSTER_BYTE
    text = roh.decode("utf-8", errors="replace")

    if "ISO-10303-21" not in text[:200].upper():
        raise HerkunftError(
            f"{pfad.name} beginnt nicht mit ISO-10303-21 — das ist keine STEP/IFC-Datei. "
            f"Die ersten Zeichen: {text[:60]!r}"
        )

    warnungen: list[str] = []
    schema_treffer = _RE_SCHEMA.search(text)
    schema = schema_treffer.group(1).upper() if schema_treffer else None
    if schema is None:
        warnungen.append("FILE_SCHEMA nicht gefunden — die Schemafassung bleibt offen.")

    erzeuger = _erzeuger_aus_file_name(text)
    herkunft = _erkenne(erzeuger or "")

    einheit, vorsatz, faktor = _laengeneinheit(text, warnungen)

    # Die Up-Achse ist bei IFC **Norm**, nicht Gewohnheit: ISO 16739 legt Z-up fest. Das
    # gilt unabhängig davon, ob der Erzeuger erkannt wurde — und ist damit der einzige
    # Fall im Projekt, in dem `up_axis` aus der Datei folgt statt aus einer Zusage.
    up_axis, sicherheit = "Z_UP", BELEGT
    begruendung = (
        "IFC ist nach ISO 16739 Z-up. Das folgt aus dem Format, nicht aus dem "
        "Erzeugerprogramm — darum belegt und nicht bloss vermutet."
    )

    if not vollstaendig:
        warnungen.append(
            f"Nur die ersten {LESEFENSTER_BYTE // 1024} kB wurden gelesen "
            f"(Datei: {pfad.stat().st_size // 1024} kB). Kopf und Einheitenzuweisung "
            f"stehen normalerweise darin; wurde nichts gefunden, heisst das 'im "
            f"gelesenen Anfang nicht gefunden' und nicht 'nicht vorhanden'."
        )

    return {
        "format": "IFC",
        "schema": schema,
        "laengeneinheit": einheit,
        "vorsatz": vorsatz,
        "meter_je_einheit": faktor,
        "erzeuger": erzeuger,
        "herkunft": herkunft.name if herkunft else None,
        "up_axis": up_axis,
        "sicherheit": sicherheit,
        "begruendung": begruendung,
        "warnungen": warnungen,
        "vollstaendig_gelesen": vollstaendig,
    }


def _step_felder(inhalt: str) -> list[str]:
    """Die Parameter einer STEP-Entität zerlegen — auf oberster Ebene, klammertreu.

    Ein blosses ``split(",")`` genügt nicht: Die Autoren- und Organisationsfelder von
    ``FILE_NAME`` sind selbst Listen (``('Muster','Zweiter')``), und ein Komma darin
    verschöbe jedes Feld danach. Genau diese Verschiebung ist der Grund, warum hier
    **nach Position** gelesen wird und nicht nach „die letzten drei nichtleeren".
    """
    felder: list[str] = []
    tiefe = 0
    in_text = False
    aktuell: list[str] = []
    i = 0
    while i < len(inhalt):
        z = inhalt[i]
        if in_text:
            aktuell.append(z)
            if z == "'":
                # Zwei Hochkommas hintereinander sind ein escaptes Hochkomma (ISO 10303-21).
                if i + 1 < len(inhalt) and inhalt[i + 1] == "'":
                    aktuell.append("'")
                    i += 2
                    continue
                in_text = False
        elif z == "'":
            in_text = True
            aktuell.append(z)
        elif z == "(":
            tiefe += 1
            aktuell.append(z)
        elif z == ")":
            tiefe -= 1
            aktuell.append(z)
        elif z == "," and tiefe == 0:
            felder.append("".join(aktuell).strip())
            aktuell = []
        else:
            aktuell.append(z)
        i += 1
    felder.append("".join(aktuell).strip())
    return felder


#: Position der beiden Felder in ``FILE_NAME``, die das erzeugende Programm nennen.
#:
#: ISO 10303-21 legt die Reihenfolge fest:
#: ``FILE_NAME(name, time_stamp, author, organization, preprocessor_version,
#: originating_system, authorization)`` — also Index 4 und 5, nullbasiert.
FILE_NAME_ERZEUGERFELDER = (4, 5)


def _erzeuger_aus_file_name(text: str) -> str | None:
    """Das erzeugende Programm aus ``FILE_NAME`` lesen — **nach Position**.

    Der Befund, der diese Funktion nötig machte (18.08.2026, Testabnahme dieses Moduls):
    Die erste Fassung sammelte *alle* nichtleeren Zeichenketten aus ``FILE_NAME`` und nahm
    die letzten drei. In der Testgeometrie sind nur drei Felder gefüllt — **Dateiname**,
    Zeitstempel und Beschreibung —, und damit landete der Dateiname in der Erkennung:

        `rhino-haus.ifc` → ``herkunft == "Rhino"``

    obwohl das Erzeugerfeld Rhino nirgends nennt. **Wer eine Datei umbenannte, änderte
    ihre Herkunft.** Das ist keine ungenaue Erkennung, das ist eine falsche.

    Gelesen werden jetzt nur ``preprocessor_version`` und ``originating_system`` — die
    beiden Felder, die die Norm für genau diesen Zweck vorsieht. Dateiname, Autor und
    Organisation bleiben **draussen**: Ein Autorenfeld „Blenderweg 12" hätte sonst
    „Blender" ergeben, und `revit`, `rhino` oder `autodesk` stecken ebenso leicht in einem
    Personen- oder Projektnamen.

    Warum das bei glTF weniger heikel wäre, hier aber nicht: Bei IFC ist die Up-Achse
    ohnehin Norm, eine Fehlerkennung kostet nur eine falsche Bemerkung. Bei glTF
    entschiede derselbe Fehlgriff darüber, welche Achse einem Menschen zur **Bestätigung**
    vorgeschlagen wird — und das ist die Sorte Hilfestellung, die man bestätigt, ohne
    nachzusehen.
    """
    treffer = _RE_FILENAME.search(text)
    if not treffer:
        return None
    felder = _step_felder(treffer.group(1))
    teile: list[str] = []
    for i in FILE_NAME_ERZEUGERFELDER:
        if i < len(felder):
            wert = felder[i].strip()
            if wert.startswith("'") and wert.endswith("'") and len(wert) >= 2:
                wert = wert[1:-1].replace("''", "'")
            if wert and wert != "$":
                teile.append(wert)
    return " | ".join(teile) or None


def _laengeneinheit(text: str, warnungen: list[str]) -> tuple[str | None, str | None, float | None]:
    """Die Längeneinheit aus dem IFC-Text → ``(Einheit, Vorsatz, Meter je Einheit)``."""
    treffer = _RE_SIUNIT.search(text)
    if treffer:
        vorsatz = (treffer.group(2) or "").upper() or None
        einheit = treffer.group(3).upper()
        if einheit != "METRE":
            warnungen.append(
                f"Längeneinheit ist '{einheit}', nicht METRE. Das ist zulässig, aber "
                f"ungewöhnlich — der Umrechnungsfaktor bleibt hier offen."
            )
            return einheit, vorsatz, None
        faktor = SI_VORSAETZE.get(vorsatz, 1.0) if vorsatz else 1.0
        if vorsatz and vorsatz not in SI_VORSAETZE:
            warnungen.append(f"Unbekannter SI-Vorsatz '{vorsatz}' — Faktor bleibt offen.")
            return einheit, vorsatz, None
        return einheit, vorsatz, faktor

    umrechnung = _RE_CONVUNIT.search(text)
    if umrechnung:
        # Zoll, Fuss und Ähnliches. Der Faktor steht in einem eigenen Objekt, auf das
        # verwiesen wird — das aufzulösen hiesse, einen STEP-Parser zu bauen.
        warnungen.append(
            f"Längeneinheit ist eine Umrechnungseinheit ('{umrechnung.group(1)}', also "
            f"z. B. Zoll oder Fuss). Ihr Faktor steht in einem verwiesenen Objekt und "
            f"wird hier NICHT aufgelöst — dafür bräuchte es einen STEP-Parser. Der "
            f"Umrechnungsfaktor bleibt offen, damit niemand 1.0 dafür hält."
        )
        return umrechnung.group(1), None, None

    warnungen.append(
        "Keine Längeneinheit gefunden. Der Faktor bleibt offen — ihn auf 1.0 zu setzen "
        "wäre genau der mm-als-m-Fehler, den der torwaechter danach abfangen müsste."
    )
    return None, None, None


# ── glTF / glb ───────────────────────────────────────────────────────────────────────

def lies_gltf_kopf(pfad) -> dict:
    """Kopf einer glTF- oder glb-Datei lesen. Reine stdlib.

    Returns:
        ``{format, version, generator, herkunft, up_axis, sicherheit, begruendung,
        warnungen}``.

        ``up_axis`` ist hier **oft ``None``** — und das ist der Punkt. glTF 2.0 kennt kein
        Up-Achsen-Feld (Phase-0-Befund). Was hier herauskommt, ist bestenfalls eine
        Vermutung aus dem Erzeugernamen, und sie ist als solche gekennzeichnet.

    Raises:
        HerkunftError: keine deutbare glTF/glb-Datei.
    """
    pfad = Path(pfad)
    try:
        roh = pfad.read_bytes()
    except OSError as fehler:
        raise HerkunftError(f"{pfad} lässt sich nicht lesen: {fehler}") from fehler

    if roh[:4] == b"glTF":
        daten = _glb_json(roh, pfad)
        format_name = "glb"
    else:
        try:
            daten = json.loads(roh.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as fehler:
            raise HerkunftError(
                f"{pfad.name} ist weder binäres glb (Kennung 'glTF') noch lesbares "
                f"JSON: {fehler}"
            ) from fehler
        format_name = "gltf"

    if not isinstance(daten, dict):
        raise HerkunftError(
            f"{pfad.name}: Der JSON-Inhalt ist ein {type(daten).__name__}, kein Objekt. "
            f"Eine glTF-Datei ist nach Norm ein JSON-Objekt; eine Liste oder ein blosser "
            f"Wert ist keine deutbare glTF-Datei."
        )
    asset = daten.get("asset") or {}
    generator = asset.get("generator")
    herkunft = _erkenne(generator or "")

    warnungen = [
        "glTF 2.0 kennt kein Up-Achsen-Feld (Phase-0-Befund). Was hier steht, ist aus "
        "dem Erzeugernamen geschlossen — die Datei selbst sagt nichts dazu."
    ]
    if herkunft is None:
        up_axis, sicherheit = None, UNBEKANNT
        begruendung = (
            f"Erzeuger {generator!r} ist keiner der bekannten. Ohne Erkennung und ohne "
            f"Feld in der Datei bleibt die Up-Achse offen — `up_axis` bleibt Pflichtfeld."
        )
    elif herkunft.up_axis is None:
        up_axis, sicherheit = None, UNBEKANNT
        begruendung = f"{herkunft.name}: {herkunft.beleg}"
    else:
        up_axis, sicherheit = herkunft.up_axis, herkunft.sicherheit
        begruendung = f"{herkunft.name}: {herkunft.beleg}"

    return {
        "format": format_name,
        "version": asset.get("version"),
        "generator": generator,
        "herkunft": herkunft.name if herkunft else None,
        "up_axis": up_axis,
        "sicherheit": sicherheit,
        "begruendung": begruendung,
        "warnungen": warnungen,
    }


def _glb_json(roh: bytes, pfad: Path) -> dict:
    """Den JSON-Abschnitt aus einem binären glb holen (Norm: Kopf 12 Byte, dann Blöcke)."""
    if len(roh) < 20:
        raise HerkunftError(f"{pfad.name} ist zu kurz für eine glb-Datei ({len(roh)} Byte).")
    _, version, _ = struct.unpack("<III", roh[:12])
    if version != 2:
        raise HerkunftError(
            f"{pfad.name} meldet glb-Fassung {version}. Dieses Projekt setzt glTF 2.0 "
            f"voraus; Fassung 1 hat einen anderen Aufbau und wird nicht geraten."
        )
    laenge, art = struct.unpack("<II", roh[12:20])
    if art != 0x4E4F534A:                                  # 'JSON'
        raise HerkunftError(
            f"{pfad.name}: Der erste Block ist nicht JSON (Kennung {art:#x}). Die Norm "
            f"verlangt JSON als ersten Block."
        )
    stueck = roh[20:20 + laenge]
    try:
        return json.loads(stueck.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as fehler:
        raise HerkunftError(f"{pfad.name}: JSON-Block nicht lesbar: {fehler}") from fehler


# ── Gemeinsamer Eingang ──────────────────────────────────────────────────────────────

def deute(pfad) -> dict:
    """IFC oder glTF — je nach Datei das Richtige lesen.

    Für Aufrufer, die nur eine Datei haben und nicht wissen wollen, welches Format es ist.
    Entschieden wird am **Inhalt**, nicht an der Dateiendung: Eine Endung ist eine
    Behauptung des Benennenden, der Dateianfang ist eine des Erzeugers.
    """
    pfad = Path(pfad)
    try:
        anfang = pfad.open("rb").read(64)
    except OSError as fehler:
        raise HerkunftError(f"{pfad} lässt sich nicht lesen: {fehler}") from fehler
    if b"ISO-10303-21" in anfang.upper():
        return lies_ifc_kopf(pfad)
    return lies_gltf_kopf(pfad)


def fordere_up_axis(kopf: dict, *, angabe=None) -> str:
    """Die Up-Achse festlegen — aus der Datei, aus der Angabe, oder gar nicht.

    Das ist die Stelle, an der aus einer Deutung ein Entscheid wird, und sie steht
    ausdrücklich **nicht** in :func:`lies_gltf_kopf`. Die Reihenfolge:

    1. Eine **ausdrückliche Angabe** des Aufrufers hat immer Vorrang — auch vor einem
       belegten Wert. Wer die Datei besser kennt als ihr Kopf, darf das sagen.
    2. Sonst ein :data:`BELEGT`-Wert. Der stammt aus dem Format selbst (IFC/ISO 16739).
    3. Eine :data:`VERMUTET`-Deutung genügt **nicht**. Sie wird in der Fehlermeldung
       genannt, damit der Aufrufer sie bestätigen kann — aber sie wird nicht angenommen.

    Warum Punkt 3 so hart ist: Genau hier wollte Phase 0 keinen Default, und eine
    Vermutung, die sich selbst durchwinkt, **ist** ein Default mit besserer Begründung.
    Eine stille Verdrehung von Tiefenkarte, Kamera und Geometrie-QA ist der teuerste
    Fehler dieser Kette, weil das Ergebnis plausibel aussieht.

    Raises:
        HerkunftError: wenn weder eine Angabe noch ein belegter Wert vorliegt.
    """
    from aiimaging import contracts

    if angabe is not None:
        return contracts.normalize_up_axis(angabe)
    if kopf.get("sicherheit") == BELEGT and kopf.get("up_axis"):
        return contracts.normalize_up_axis(kopf["up_axis"])

    vermutung = ""
    if kopf.get("up_axis"):
        vermutung = (
            f" Vermutet wird {kopf['up_axis']} ({kopf.get('begruendung')}) — eine "
            f"Vermutung reicht hier aber nicht: Sie wäre ein Default mit besserer "
            f"Begründung, und Phase 0 wollte an dieser Stelle keinen."
        )
    raise HerkunftError(
        f"Die Up-Achse steht nicht fest und muss angegeben werden.{vermutung} "
        f"Erzeuger: {kopf.get('generator') or kopf.get('erzeuger')!r}, "
        f"Format: {kopf.get('format')}."
    )


# ── Gegenprobe: sagt die Datei dasselbe wie ihre Zahlen? ─────────────────────────────

def pruefe_einheit_gegen_masse(kopf: dict, bbox) -> dict:
    """Erklärte Einheit gegen die tatsächlich herausgekommenen Masse halten.

    Der Fall, für den das gebaut ist, ist **nicht** „die Datei ist in Millimetern" — das
    löst IfcOpenShell selbst, gemessen am 18.08.2026 (siehe Modul-Docstring). Der Fall ist
    der kaputte Export: Die Datei **erklärt** Millimeter, trägt aber Zahlen in
    Metergrösse. Dann steht am Ende ein Bauwerk von acht Millimetern.

    Der `torwaechter` fängt das bereits — aber nur als *Verdacht* („Verdacht auf
    Einheitenfehler um Faktor 0,001"), weil er nur die Masse sieht und nicht den Kopf.
    Mit beidem nebeneinander wird daraus eine Aussage darüber, **was** nicht
    zusammenpasst.

    Args:
        kopf: Rückgabe von :func:`lies_ifc_kopf`.
        bbox: ``[[xmin,ymin,zmin],[xmax,ymax,zmax]]`` **nach** der Konversion, in Metern —
            also aus dem Report von ``seams.ifc_zu_glb``.

    Returns:
        ``{stimmig, erklaerte_einheit, meter_je_einheit, groesste_kante_m, befund}``.
        ``stimmig`` ist ``None``, wenn sich nichts sagen lässt — kein Urteil aus Mangel an
        Angabe, dieselbe Haltung wie in ``geometrie_qa``.
    """
    faktor = kopf.get("meter_je_einheit")
    einheit = kopf.get("laengeneinheit")
    vorsatz = kopf.get("vorsatz")
    erklaert = f"{vorsatz.lower() if vorsatz else ''}{(einheit or '?').lower()}"

    try:
        lo, hi = bbox
        kante = max(float(hi[i]) - float(lo[i]) for i in range(3))
    except (TypeError, ValueError, IndexError):
        return {"stimmig": None, "erklaerte_einheit": erklaert,
                "meter_je_einheit": faktor, "groesste_kante_m": None,
                "befund": "bbox nicht deutbar — ohne Masse gibt es nichts zu vergleichen."}

    if faktor is None:
        return {"stimmig": None, "erklaerte_einheit": erklaert,
                "meter_je_einheit": None, "groesste_kante_m": kante,
                "befund": ("Die Datei nennt keine auswertbare Längeneinheit. Ohne sie ist "
                           "die Gegenprobe nicht möglich — der Torwächter bleibt die "
                           "einzige Instanz, und er kann nur den Verdacht äussern.")}

    # Ein Bauwerk liegt zwischen einem Meter und einem Kilometer. Dieselben Schranken wie
    # im torwaechter, damit nicht zwei Stellen zwei Meinungen über 'plausibel' haben.
    from aiimaging import torwaechter as tw
    plausibel = tw.MIN_GEBAEUDE_M <= kante <= tw.MAX_GEBAEUDE_M
    if plausibel:
        return {"stimmig": True, "erklaerte_einheit": erklaert, "meter_je_einheit": faktor,
                "groesste_kante_m": kante,
                "befund": (f"Die Datei erklärt {erklaert} (Faktor {faktor:g}), und nach der "
                           f"Konversion steht ein Bauwerk von {kante:.3g} m. Beides passt "
                           f"zusammen.")}

    # Passt es nicht, ist die Richtung die Auskunft: Zu klein um genau den erklärten
    # Faktor heisst, die Zahlen waren nie in der erklärten Einheit.
    if faktor != 1.0 and tw.MIN_GEBAEUDE_M <= kante / faktor <= tw.MAX_GEBAEUDE_M:
        befund = (
            f"KAPUTTER EXPORT, benennbar: Die Datei erklärt {erklaert} (Faktor {faktor:g}), "
            f"heraus kommen aber nur {kante:.3g} m. Rechnet man den erklärten Faktor "
            f"heraus, ergäbe das {kante / faktor:.3g} m — ein plausibles Bauwerk. Die "
            f"Zahlen in der Datei standen also in Metern, während die Einheitenzuweisung "
            f"{erklaert} behauptet. Nicht der Konverter ist schuld, sondern der Export."
        )
    else:
        befund = (
            f"Die Datei erklärt {erklaert} (Faktor {faktor:g}), heraus kommen {kante:.3g} m "
            f"— kein plausibles Bauwerk. Der erklärte Faktor erklärt die Abweichung aber "
            f"nicht; die Ursache liegt woanders als in der Einheit."
        )
    return {"stimmig": False, "erklaerte_einheit": erklaert, "meter_je_einheit": faktor,
            "groesste_kante_m": kante, "befund": befund}


__all__ = [
    "BELEGT", "HERKUENFTE", "HerkunftError", "Herkunft", "LESEFENSTER_BYTE",
    "SI_VORSAETZE", "UNBEKANNT", "VERMUTET",
    "FILE_NAME_ERZEUGERFELDER",
    "deute", "fordere_up_axis", "lies_gltf_kopf", "lies_ifc_kopf",
    "pruefe_einheit_gegen_masse",
]
