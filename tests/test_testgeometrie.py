"""Die erweiterte Testgeometrie — IFC4 *und* IFC2X3, Meter *und* Millimeter.

Warum diese Datei existiert
---------------------------
``tools/make_test_ifc.py`` kann seit dem 18.08.2026 vier Kombinationen schreiben. Bis
dahin prüfte das ganze Projekt gegen **eine** davon: IFC4 in Metern. Die Messung an 40
echten Dateien (`auf-20260818-08`) sagt, warum das zu wenig ist — 10 von 40 waren IFC2X3,
und **alle zehn ArchiCAD-Dateien** waren darunter. Wer nur IFC4 prüft, prüft nicht gegen
das, was das verbreitetste Autorenprogramm liefert.

Vier Gruppen, bewusst getrennt
------------------------------
**A · Formal richtig, ohne Konverter.** Reine Textprüfung an der erzeugten Datei:
Schemazeile, Attributzahl von ``IFCWALL``, Einheitenzeile, abgewiesene Eingaben,
Wiederholbarkeit. Läuft überall — kein ``ifcopenshell``, kein Netz, keine GPU.

**B · Die Millimeter-Variante ist eine echte Umrechnung.** Die wichtigste Gruppe, und
zwar wegen des Falls, den sie *ausschliesst*: Eine Datei, die die Einheitenzeile auf
``.MILLI.`` stellt und die Zahlen metergross lässt, ist ein **kaputter Export** und keine
Testgeometrie. Ein Test, der nur ``.MILLI.`` sucht, hielte beides für dasselbe.

**C · Mit dem echten Konverter** (übersprungen, wenn ``.venv-ifc`` fehlt). Alle vier
Kombinationen ergeben nach ``seams.ifc_zu_glb`` dasselbe Bauwerk: 8,0 × 5,0 × 3,25 m.
Das ist der eigentliche Beleg — Schema und Einheit ändern die **Datei**, nicht das
**Bauwerk**.

**D · Die Gegenprobe.** Ohne sie wäre Gruppe C vakuös: Sie bliebe auch dann grün, wenn
``herkunft.pruefe_einheit_gegen_masse`` immer ``True`` sagte. Der von Hand gebaute
kaputte Export muss ``stimmig=False`` ergeben und den Faktor herausrechnen.

**E · Der Befund.** Zwei ``xfail(strict=True)``-Tests halten fest, dass die
IFC2X3-Variante **nicht** gültiges IFC2X3 ist — siehe dort. Sie sind bewusst nicht
repariert: Das gehört in die Fixture, und die zu ändern war nicht Auftrag dieser Datei.
"""
from __future__ import annotations

import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

from conftest import REPO

from aiimaging import herkunft as hk
from aiimaging import seams, torwaechter

# ======================================================================================
# Festwerte
# ======================================================================================

#: Die vier Kombinationen, einmal aufgeschrieben. Jede Gruppe unten fährt sie durch.
KOMBINATIONEN = [
    pytest.param("IFC4", None, id="ifc4-meter"),
    pytest.param("IFC4", "MILLI", id="ifc4-millimeter"),
    pytest.param("IFC2X3", None, id="ifc2x3-meter"),
    pytest.param("IFC2X3", "MILLI", id="ifc2x3-millimeter"),
]

#: Kantenlängen des synthetischen Testbaus in Metern — **unabhängig** von Schema und
#: Einheit. 3,25 m in Z, weil die Bodenplatte (0,25 m) unter Null liegt.
SOLL_MASSE_M = (8.0, 5.0, 3.25)

#: Grösste Kante daraus. Die Zahl, an der Gruppe C hängt.
KANTE_M = 8.0

#: Attributzahl von ``IFCWALL`` je Schema. **Der einzige Unterschied im Entitätensatz
#: dieser Fixture, der die Attributzahl betrifft:** IFC4 kennt bei ``IfcWall`` ein
#: neuntes Attribut (``PredefinedType``), IFC2X3 nicht. Ein Attribut zuviel machte die
#: Datei für einen strengen Leser ungültig.
WAND_ATTRIBUTE = {"IFC4": 9, "IFC2X3": 8}

#: So viele Wände schreibt die Fixture — geprüft wird die Zahl mit, damit ein Test nicht
#: dadurch grün bleibt, dass er gar keine Wand gefunden hat.
ANZAHL_WAENDE = 4

#: Die Längeneinheitszeile der Meter-Variante. Angelpunkt der Gegenprobe in Gruppe D.
EINHEIT_METER = "IFCSIUNIT(*,.LENGTHUNIT.,$,.METRE.)"

#: Dieselbe Zeile auf Millimeter gestellt — **nur** die Zeile, die Zahlen bleiben.
EINHEIT_MILLI = "IFCSIUNIT(*,.LENGTHUNIT.,.MILLI.,.METRE.)"

#: Zeilenarten, deren Zahlen eine Länge sind. Nur sie werden beim Wechsel auf Millimeter
#: tausendfach — ``IFCDIRECTION`` trägt Richtungsvektoren, die sind einheitslos, und ein
#: skalierter Richtungsvektor wäre ein anderer Fehler als der gesuchte.
LAENGENZEILEN = ("IFCCARTESIANPOINT", "IFCRECTANGLEPROFILEDEF", "IFCEXTRUDEDAREASOLID")

#: Ein konkretes Mass aus dem Dateitext: die Gebäudelänge im Profil der Bodenplatte.
#: In Metern steht dort ``8.000000``, in Millimetern ``8000.000000``. An dieser Zahl
#: hängt Gruppe B — die blosse Anwesenheit von ``.MILLI.`` sagt über die Zahlen nichts.
PROFILMASS_METER = "8.000000"
PROFILMASS_MILLI = "8000.000000"

#: Alle Entitäten der Fixture, die von ``IfcRoot`` erben. Ihr zweites Attribut ist
#: ``OwnerHistory`` — siehe Gruppe E.
WURZELENTITAETEN = (
    "IFCPROJECT", "IFCSITE", "IFCBUILDING", "IFCBUILDINGSTOREY",
    "IFCSLAB", "IFCWALL", "IFCRELAGGREGATES", "IFCRELCONTAINEDINSPATIALSTRUCTURE",
)

#: Stellung von ``OwnerHistory`` in jeder ``IfcRoot``-Ableitung (nullbasiert).
OWNERHISTORY = 1

_RE_ENTITAET = re.compile(r"^#(\d+)=\s*([A-Za-z0-9]+)\((.*)\);\s*$")
_RE_ZAHL = re.compile(r"-?\d+\.\d*")
_RE_SIUNIT_LAENGE = re.compile(r"IFCSIUNIT\(\*,\.LENGTHUNIT\.,([^,]+),\.METRE\.\)")


# ======================================================================================
# Werkzeuge
# ======================================================================================

def _lade_fixturemodul():
    """``tools/make_test_ifc.py`` als Modul laden — ``tools/`` ist kein Paket.

    Direkt geladen und nicht über einen Subprozess, weil diese Datei Dinge prüft, die
    ein Subprozess verschluckt: Welche Ausnahme bei welcher Eingabe fliegt, und mit
    welcher Meldung. Über die Kommandozeile bliebe davon ein Rückgabewert übrig.

    Dass der übliche Weg — Aufruf als Skript — davon nicht abweicht, prüft
    :func:`test_kommandozeile_und_aufruf_liefern_dieselbe_datei` eigens.
    """
    pfad = REPO / "tools" / "make_test_ifc.py"
    spezifikation = importlib.util.spec_from_file_location("make_test_ifc_pruefling", pfad)
    modul = importlib.util.module_from_spec(spezifikation)
    spezifikation.loader.exec_module(modul)
    return modul


FIXTURE = _lade_fixturemodul()


def erzeuge(ziel: Path, *, schema: str = "IFC4", vorsatz: str | None = None) -> Path:
    """Eine Spielart der Testgeometrie schreiben und den Pfad zurückgeben."""
    ziel.parent.mkdir(parents=True, exist_ok=True)
    return FIXTURE.erzeuge_ifc(ziel, schema=schema, vorsatz=vorsatz)


def text_von(ziel: Path, *, schema: str = "IFC4", vorsatz: str | None = None) -> str:
    """Dieselbe Spielart, gleich als Text."""
    return erzeuge(ziel, schema=schema, vorsatz=vorsatz).read_text(encoding="utf-8")


def entitaeten(text: str, name: str) -> list[list[str]]:
    """Alle Vorkommen einer STEP-Entität als Feldlisten.

    Zerlegt wird mit ``herkunft._step_felder`` — dem klammertreuen Zerleger, den das
    Projekt für ``FILE_NAME`` ohnehin hat und der dort geprüft ist. Ein zweiter, hier
    hingeschriebener Zerleger wäre eine zweite Meinung darüber, was ein Feld ist; genau
    daran scheiterte schon die Erzeugererkennung (siehe ``test_herkunft.py``).
    """
    treffer = []
    for zeile in text.splitlines():
        gefunden = _RE_ENTITAET.match(zeile.strip())
        if gefunden and gefunden.group(2).upper() == name.upper():
            treffer.append(hk._step_felder(gefunden.group(3)))
    return treffer


def laengenzahlen(text: str) -> list[float]:
    """Alle Zahlen aus den längentragenden Zeilen, in Dateireihenfolge."""
    zahlen: list[float] = []
    for zeile in text.splitlines():
        if any(art in zeile for art in LAENGENZEILEN):
            zahlen += [float(z) for z in _RE_ZAHL.findall(zeile)]
    return zahlen


def laengenvorsatz(text: str) -> str:
    """Der Vorsatz der Längeneinheit, wie er im Text steht (``$`` oder ``.MILLI.``)."""
    gefunden = _RE_SIUNIT_LAENGE.search(text)
    assert gefunden, "Keine IFCSIUNIT-Längenzeile gefunden — die Fixture hat sich geändert"
    return gefunden.group(1)


def kaputter_export(meter_text: str) -> str:
    """Den kaputten Export bauen: Einheitenzeile auf Millimeter, Zahlen metergross lassen.

    Genau die Verwechslung, die zwei von 40 echten Dateien trugen. Es ist ausdrücklich
    **nicht** das, was ``vorsatz="MILLI"`` erzeugt — dort werden die Zahlen mitgerechnet.
    """
    assert EINHEIT_METER in meter_text, "Die Fixture hat ihre Einheitenzeile geändert"
    return meter_text.replace(EINHEIT_METER, EINHEIT_MILLI)


def konverter_fehlt() -> bool:
    """Steht das ``.venv-ifc`` mit ifcopenshell bereit?"""
    try:
        return not Path(seams.finde_ifc_python()).exists()
    except seams.SeamError:
        return True


ohne_konverter = pytest.mark.skipif(
    konverter_fehlt(),
    reason=".venv-ifc fehlt — die Läufe über die Prozessgrenze entfallen",
)

#: Schnipsel für den Prüfer jenseits der Prozessgrenze. ``ifcopenshell`` liegt im
#: eigenen venv (Regel 1/2) und wird hier nicht importiert, sondern aufgerufen.
_VALIDIER_SCHNIPSEL = """
import json, sys
import ifcopenshell
import ifcopenshell.validate as validate

protokoll = validate.json_logger()
validate.validate(ifcopenshell.open(sys.argv[1]), protokoll)
print(json.dumps([
    {"nachricht": str(eintrag.get("message")), "attribut": str(eintrag.get("attribute"))}
    for eintrag in protokoll.statements
    if str(eintrag.get("level")) == "error"
]))
"""


def schemafehler(ifc: Path) -> list[dict]:
    """Die Datei vom echten Schemaprüfer beurteilen lassen — über die Prozessgrenze."""
    ergebnis = subprocess.run(
        [seams.finde_ifc_python(), "-c", _VALIDIER_SCHNIPSEL, str(ifc)],
        capture_output=True, text=True, check=False)
    assert ergebnis.returncode == 0, f"Schemaprüfer scheiterte:\n{ergebnis.stderr[:800]}"
    return json.loads(ergebnis.stdout.strip().splitlines()[-1])


# ======================================================================================
# A · Die vier Kombinationen sind formal richtig — ohne Konverter
# ======================================================================================

@pytest.mark.parametrize("schema, vorsatz", KOMBINATIONEN)
def test_file_schema_traegt_das_verlangte_schema(tmp_path, schema, vorsatz):
    """Die Schemazeile ist das Erste, was jeder Leser sieht — auch ``lies_ifc_kopf``."""
    text = text_von(tmp_path / "bau.ifc", schema=schema, vorsatz=vorsatz)

    assert f"FILE_SCHEMA(('{schema}'));" in text
    assert hk.lies_ifc_kopf(tmp_path / "bau.ifc")["schema"] == schema


@pytest.mark.parametrize("schema, vorsatz", KOMBINATIONEN)
def test_ifcwall_traegt_die_attributzahl_seines_schemas(tmp_path, schema, vorsatz):
    """Der einzige echte Unterschied im Entitätensatz — und er muss gezählt werden.

    Geprüft wird die **Zahl der Attribute**, nicht die Anwesenheit der Zeile: IFC4 hat
    bei ``IfcWall`` neun (das neunte ist ``PredefinedType``), IFC2X3 acht. Wer nur nach
    ``IFCWALL`` sucht, findet beide Fassungen gleich gut — auch die falsche.
    """
    text = text_von(tmp_path / "bau.ifc", schema=schema, vorsatz=vorsatz)
    waende = entitaeten(text, "IFCWALL")

    assert len(waende) == ANZAHL_WAENDE, "Ohne Wand prüft dieser Test nichts"
    for felder in waende:
        assert len(felder) == WAND_ATTRIBUTE[schema], \
            f"{schema}: {len(felder)} Attribute statt {WAND_ATTRIBUTE[schema]}: {felder}"


def test_das_neunte_wandattribut_gibt_es_nur_in_ifc4(tmp_path):
    """Dieselbe Sache von der anderen Seite: Die beiden Fassungen sind nicht gleich lang.

    Ein Test, der nur die erwartete Zahl bestätigt, bliebe grün, wenn die Fixture beide
    Schemata gleich behandelte und die Erwartung mitwanderte. Hier stehen sie nebeneinander.
    """
    vier = entitaeten(text_von(tmp_path / "vier.ifc", schema="IFC4"), "IFCWALL")
    zweix = entitaeten(text_von(tmp_path / "zweix.ifc", schema="IFC2X3"), "IFCWALL")

    assert len(vier[0]) == len(zweix[0]) + 1
    assert vier[0][:8] == zweix[0][:8], "Die ersten acht Attribute sind in beiden dieselben"
    assert vier[0][8] == "$", "Das neunte Attribut ist PredefinedType — hier ungesetzt"


@pytest.mark.parametrize("schema", ["IFC4", "IFC2X3"])
@pytest.mark.parametrize("vorsatz, erwartet", [(None, "$"), ("MILLI", ".MILLI.")])
def test_ifcsiunit_traegt_den_verlangten_vorsatz(tmp_path, schema, vorsatz, erwartet):
    """Meter heisst ``$`` (kein Vorsatz), Millimeter heisst ``.MILLI.`` — nichts dazwischen."""
    text = text_von(tmp_path / "bau.ifc", schema=schema, vorsatz=vorsatz)

    assert laengenvorsatz(text) == erwartet


@pytest.mark.parametrize("schema, vorsatz", KOMBINATIONEN)
def test_nur_die_laengeneinheit_traegt_den_vorsatz(tmp_path, schema, vorsatz):
    """Fläche, Volumen und Winkel bleiben unangetastet.

    Ein Vorsatz auf ``.SQUARE_METRE.`` wäre kein Tippfehler, sondern eine andere Datei:
    Mengenauswertungen läsen dann Quadratmillimeter, wo Quadratmeter stehen sollten.
    """
    text = text_von(tmp_path / "bau.ifc", schema=schema, vorsatz=vorsatz)

    for art in (".AREAUNIT.", ".VOLUMEUNIT.", ".PLANEANGLEUNIT."):
        zeile = next(z for z in text.splitlines() if art in z)
        assert f"{art},$," in zeile, f"{art} hat unerwartet einen Vorsatz: {zeile}"


@pytest.mark.parametrize("schema", ["ifc4", "IFC2x3", "IFC4X3", "", None, "IFC"])
def test_ungueltiges_schema_wird_abgelehnt(tmp_path, schema):
    """Ein unbekanntes Schema still nach IFC4 zu deuten, hiesse: falsch beschriftet liefern.

    Kleinschreibung ist eigens dabei: ``'ifc4'`` sieht richtig aus und wäre in der
    ``FILE_SCHEMA``-Zeile trotzdem falsch — ISO 10303-21 schreibt den Namen gross.
    """
    with pytest.raises(ValueError) as fehler:
        erzeuge(tmp_path / "bau.ifc", schema=schema)

    meldung = str(fehler.value)
    assert "schema" in meldung
    assert "IFC4" in meldung and "IFC2X3" in meldung, "Die Meldung nennt die gültigen Werte"
    assert repr(schema) in meldung, "Die Meldung nennt den abgelehnten Wert"
    assert not (tmp_path / "bau.ifc").exists(), "Abgelehnt heisst: keine halbe Datei"


@pytest.mark.parametrize("vorsatz", ["MILLI ", "milli", "KILO", "CENTI", "", "MILLIMETER"])
def test_ungueltiger_vorsatz_wird_abgelehnt(tmp_path, vorsatz):
    """Nur ``None`` und ``"MILLI"``. Alles andere ist eine Einheit, die niemand umrechnet.

    ``"KILO"`` und ``"CENTI"`` sind gültige SI-Vorsätze und werden trotzdem abgelehnt:
    Die Fixture rechnet die Koordinaten nur für Millimeter mit. Ein durchgelassenes
    ``"KILO"`` ergäbe eine Datei, die Kilometer erklärt und Meterzahlen trägt — den
    kaputten Export also, den diese Fixture gerade nicht sein soll.
    """
    with pytest.raises(ValueError) as fehler:
        erzeuge(tmp_path / "bau.ifc", vorsatz=vorsatz)

    meldung = str(fehler.value)
    assert "vorsatz" in meldung
    assert "MILLI" in meldung and "None" in meldung
    assert repr(vorsatz) in meldung


@pytest.mark.parametrize("schema, vorsatz", KOMBINATIONEN)
def test_zweimal_erzeugt_ergibt_byteweise_dasselbe(tmp_path, schema, vorsatz):
    """Determinismus ist keine Kosmetik: Ohne ihn ist kein Lauf mit einem anderen vergleichbar.

    Gleicher Dateiname in zwei Ordnern, weil der Name über ``FILE_NAME`` in die Datei
    eingeht — verglichen wird die Erzeugung, nicht die Benennung.
    """
    erste = erzeuge(tmp_path / "a" / "bau.ifc", schema=schema, vorsatz=vorsatz)
    zweite = erzeuge(tmp_path / "b" / "bau.ifc", schema=schema, vorsatz=vorsatz)

    assert erste.read_bytes() == zweite.read_bytes()


def test_die_vier_kombinationen_sind_vier_verschiedene_dateien(tmp_path):
    """Vier Wahlmöglichkeiten, die zweimal dasselbe ergäben, wären zwei zuviel."""
    dateien = {}
    for schema, vorsatz in [("IFC4", None), ("IFC4", "MILLI"),
                            ("IFC2X3", None), ("IFC2X3", "MILLI")]:
        ordner = f"{schema}-{vorsatz or 'METER'}".lower()
        dateien[(schema, vorsatz)] = erzeuge(
            tmp_path / ordner / "bau.ifc", schema=schema, vorsatz=vorsatz).read_bytes()

    assert len(set(dateien.values())) == 4


def test_kommandozeile_und_aufruf_liefern_dieselbe_datei(tmp_path):
    """Der Weg, den ``test_herkunft.py`` und ``tools/homeworker.py`` gehen, muss derselbe sein.

    Beide rufen das Skript als Subprozess auf. Wäre die Argumentreihenfolge dort anders
    zu lesen als hier, prüfte diese Datei eine Fassung, die sonst niemand benutzt.
    """
    subprocess.run(
        [sys.executable, str(REPO / "tools" / "make_test_ifc.py"),
         str(tmp_path / "cli" / "bau.ifc"), "IFC2X3", "MILLI"],
        check=True, capture_output=True)
    direkt = erzeuge(tmp_path / "direkt" / "bau.ifc", schema="IFC2X3", vorsatz="MILLI")

    assert (tmp_path / "cli" / "bau.ifc").read_bytes() == direkt.read_bytes()


def test_unbekannter_schalter_schreibt_keine_datei(tmp_path):
    """Ein Tippfehler darf keine IFC erzeugen.

    Das Skript nahm das erste Argument als Zielpfad, ohne hinzusehen. ``--help`` schrieb
    darum eine IFC namens ``--help`` ins Arbeitsverzeichnis, und ``--gelände`` mit Umlaut
    eine Datei dieses Namens **ohne** Gelände — beides stillschweigend und mit Rückgabe 0.
    Geprüft wird an der ausbleibenden Datei, nicht am Text der Meldung.
    """
    lauf = subprocess.run(
        [sys.executable, str(REPO / "tools" / "make_test_ifc.py"), "--gelände"],
        cwd=tmp_path, capture_output=True, text=True)

    assert lauf.returncode == 2
    assert list(tmp_path.iterdir()) == []


def test_hilfe_beschreibt_alle_vier_stellschrauben(tmp_path):
    """``--help`` soll den Gebrauch nennen und nichts schreiben."""
    lauf = subprocess.run(
        [sys.executable, str(REPO / "tools" / "make_test_ifc.py"), "--help"],
        cwd=tmp_path, capture_output=True, text=True)

    assert lauf.returncode == 0
    for stelle in ("ZIEL", "IFC2X3", "MILLI", "--gelaende"):
        assert stelle in lauf.stdout
    assert list(tmp_path.iterdir()) == []


def test_ohne_angabe_bleibt_es_bei_ifc4_in_metern(tmp_path):
    """Die Vorgabe ist der Stand, auf den alle älteren Tests gebaut sind — sie darf nicht wandern."""
    text = text_von(tmp_path / "bau.ifc")

    assert "FILE_SCHEMA(('IFC4'));" in text
    assert laengenvorsatz(text) == "$"
    assert hk.lies_ifc_kopf(tmp_path / "bau.ifc")["meter_je_einheit"] == 1.0


# ======================================================================================
# B · Die Millimeter-Variante ist eine echte Umrechnung, kein kaputter Export
# ======================================================================================

@pytest.mark.parametrize("schema", ["IFC4", "IFC2X3"])
def test_millimeterdatei_traegt_tausendfache_zahlen(tmp_path, schema):
    """An einer konkreten Zahl, nicht an der Anwesenheit von ``.MILLI.``.

    Das Profilmass der Bodenplatte ist die Gebäudelänge: ``8.000000`` in Metern,
    ``8000.000000`` in Millimetern. Steht dort weiter ``8.000000``, ist die Datei ein
    kaputter Export — und der sähe an der Einheitenzeile allein genauso aus.
    """
    meter = text_von(tmp_path / "m.ifc", schema=schema)
    milli = text_von(tmp_path / "mm.ifc", schema=schema, vorsatz="MILLI")

    profil_m = next(f for f in entitaeten(meter, "IFCRECTANGLEPROFILEDEF")
                    if f[3] == PROFILMASS_METER)
    profil_mm = next(f for f in entitaeten(milli, "IFCRECTANGLEPROFILEDEF")
                     if f[3] == PROFILMASS_MILLI)

    assert profil_m[4] == "5.000000" and profil_mm[4] == "5000.000000"
    assert float(profil_mm[3]) == pytest.approx(float(profil_m[3]) * 1000.0)


@pytest.mark.parametrize("schema", ["IFC4", "IFC2X3"])
def test_alle_laengenzahlen_sind_tausendfach_und_zwar_dieselben(tmp_path, schema):
    """Nicht nur eine Zahl: **jede** Länge, in derselben Reihenfolge.

    Eine einzeln umgerechnete Zahl wäre schlimmer als gar keine Umrechnung — das Bauwerk
    fiele auseinander, und zwar nur an einer Stelle.
    """
    meter = laengenzahlen(text_von(tmp_path / "m.ifc", schema=schema))
    milli = laengenzahlen(text_von(tmp_path / "mm.ifc", schema=schema, vorsatz="MILLI"))

    assert len(meter) == len(milli) and len(meter) > 20
    assert any(z != 0.0 for z in meter), "Nur Nullen zu vergleichen wäre keine Prüfung"
    for gross, klein in zip(milli, meter):
        assert gross == pytest.approx(klein * 1000.0)


@pytest.mark.parametrize("schema", ["IFC4", "IFC2X3"])
def test_richtungsvektoren_werden_nicht_mitskaliert(tmp_path, schema):
    """``IFCDIRECTION`` ist einheitslos. Ein tausendfacher Extrusionsvektor wäre ein Fehler,
    den die Einheitenzeile nicht erklärt — und den kein Torwächter der Einheit zuschriebe.
    """
    meter = text_von(tmp_path / "m.ifc", schema=schema)
    milli = text_von(tmp_path / "mm.ifc", schema=schema, vorsatz="MILLI")

    richtungen_m = entitaeten(meter, "IFCDIRECTION")
    assert richtungen_m, "Ohne Richtungsvektor prüft dieser Test nichts"
    assert richtungen_m == entitaeten(milli, "IFCDIRECTION")


@pytest.mark.parametrize("schema", ["IFC4", "IFC2X3"])
def test_millimeterdatei_erklaert_millimeter_und_traegt_millimeterzahlen(tmp_path, schema):
    """Beides zusammen — das ist der ganze Unterschied zum kaputten Export.

    Der Kopf sagt Faktor 0,001, **und** die Zahlen sind tausendfach. Eine Datei, die nur
    das Erste tut, ist genau der Fall, den ``herkunft.pruefe_einheit_gegen_masse``
    diagnostiziert; zwei von 40 echten Dateien waren so.
    """
    pfad = erzeuge(tmp_path / "mm.ifc", schema=schema, vorsatz="MILLI")
    kopf = hk.lies_ifc_kopf(pfad)
    text = pfad.read_text(encoding="utf-8")

    assert kopf["meter_je_einheit"] == pytest.approx(0.001)
    assert kopf["vorsatz"] == "MILLI"
    assert PROFILMASS_MILLI in text, "Die Einheit ist umgestellt, die Zahlen sind es auch"


@pytest.mark.parametrize("schema", ["IFC4", "IFC2X3"])
def test_millimetervariante_ist_nicht_der_kaputte_export(tmp_path, schema):
    """Der Test, der die beiden auseinanderhält — und der ohne diese Datei fehlte.

    Der kaputte Export entsteht aus der Meter-Variante durch **eine** Textersetzung. Er
    hat denselben Kopf wie die echte Millimeter-Datei; unterscheidbar sind die beiden
    allein an den Zahlen. Wären sie gleich, hätte ``vorsatz="MILLI"`` nur die
    Einheitenzeile angefasst.
    """
    meter = text_von(tmp_path / "m.ifc", schema=schema)
    echt = text_von(tmp_path / "mm.ifc", schema=schema, vorsatz="MILLI")
    kaputt = kaputter_export(meter)

    assert laengenvorsatz(kaputt) == laengenvorsatz(echt) == ".MILLI."
    assert kaputt != echt, "Millimeter heisst mehr als eine geänderte Einheitenzeile"
    assert laengenzahlen(kaputt) == laengenzahlen(meter)
    assert laengenzahlen(kaputt) != laengenzahlen(echt)


@pytest.mark.parametrize("schema", ["IFC4", "IFC2X3"])
def test_der_kopf_allein_unterscheidet_die_beiden_nicht(tmp_path, schema):
    """Warum die Gegenprobe in Gruppe D die Konversion braucht.

    Echte Millimeter-Datei und kaputter Export sagen im Kopf **dasselbe**. Erst die
    Masse nach der Konversion trennen sie. Das festzuhalten ist der Grund, warum
    ``pruefe_einheit_gegen_masse`` eine bbox verlangt und nicht bloss einen Kopf.
    """
    meter = text_von(tmp_path / "m.ifc", schema=schema)
    (tmp_path / "kaputt.ifc").write_text(kaputter_export(meter), encoding="utf-8")
    echt = erzeuge(tmp_path / "mm.ifc", schema=schema, vorsatz="MILLI")

    kopf_kaputt = hk.lies_ifc_kopf(tmp_path / "kaputt.ifc")
    kopf_echt = hk.lies_ifc_kopf(echt)

    for feld in ("schema", "laengeneinheit", "vorsatz", "meter_je_einheit"):
        assert kopf_kaputt[feld] == kopf_echt[feld]


# ======================================================================================
# C · Mit dem echten Konverter — Schema und Einheit ändern die Datei, nicht das Bauwerk
# ======================================================================================

@pytest.fixture(scope="module")
def gemessene_kombinationen(tmp_path_factory) -> dict:
    """Alle vier Kombinationen plus zwei kaputte Exporte, wirklich durch ``ifc_zu_glb``.

    Modulweit und in einem Rutsch: Die Läufe über die Prozessgrenze sind das Teuerste,
    was diese Datei tut, und was danach geprüft wird, sind Zahlen — die ändern sich
    nicht mehr. Nachrechnen lässt sich hier nichts: Ob IfcOpenShell den Einheitenfaktor
    selbst anwendet und ob es IFC2X3 genauso liest wie IFC4, sind Tatsachenfragen über
    ein fremdes Programm.
    """
    if konverter_fehlt():
        pytest.skip(".venv-ifc fehlt")

    ordner = tmp_path_factory.mktemp("testgeometrie-gemessen")
    lagen: dict = {}
    for schema in ("IFC4", "IFC2X3"):
        for vorsatz in (None, "MILLI"):
            name = f"{schema}-{vorsatz or 'meter'}".lower()
            ifc = erzeuge(ordner / f"{name}.ifc", schema=schema, vorsatz=vorsatz)
            bericht = seams.ifc_zu_glb(ifc, ordner / f"{name}.glb")
            lagen[(schema, vorsatz)] = (ifc, hk.lies_ifc_kopf(ifc), bericht)

        # Die Gegenprobe für Gruppe D: dieselbe Meter-Datei, nur die Einheitenzeile
        # verstellt. Sie entsteht hier, damit sie durch denselben Konverterlauf geht.
        kaputt = ordner / f"{schema.lower()}-kaputt.ifc"
        kaputt.write_text(
            kaputter_export(lagen[(schema, None)][0].read_text(encoding="utf-8")),
            encoding="utf-8")
        lagen[(schema, "KAPUTT")] = (
            kaputt, hk.lies_ifc_kopf(kaputt),
            seams.ifc_zu_glb(kaputt, ordner / f"{schema.lower()}-kaputt.glb"))
    return lagen


@ohne_konverter
@pytest.mark.parametrize("schema, vorsatz", KOMBINATIONEN)
def test_alle_vier_kombinationen_ergeben_dasselbe_bauwerk(gemessene_kombinationen,
                                                          schema, vorsatz):
    """Der eigentliche Beleg dieses Auftrags: 8,0 × 5,0 × 3,25 m, viermal.

    Schema und Einheit ändern die **Datei**. Änderten sie das **Bauwerk**, wäre jede
    Zahl, die dieses Projekt aus einer ArchiCAD-Datei zieht, vom Exportformat abhängig —
    und die zehn IFC2X3-Dateien der Messung wären ein Problem statt einer Spielart.
    """
    _, _, bericht = gemessene_kombinationen[(schema, vorsatz)]

    assert bericht["status"] == "ok"
    assert torwaechter.masse_aus_bbox(bericht["bbox"]) == pytest.approx(SOLL_MASSE_M,
                                                                       rel=1e-6)


@ohne_konverter
def test_die_vier_bboxen_sind_untereinander_gleich(gemessene_kombinationen):
    """Dasselbe noch einmal ohne Sollwert — falls der Sollwert selbst einmal falsch wird.

    Vier Läufe gegen eine Konstante können gemeinsam danebenliegen. Vier Läufe gegen
    einander nicht: Hier fällt schon auf, wenn **eine** Kombination ausschert.
    """
    masse = {(schema, vorsatz): torwaechter.masse_aus_bbox(bericht["bbox"])
             for (schema, vorsatz), (_, _, bericht) in gemessene_kombinationen.items()
             if vorsatz != "KAPUTT"}

    assert len(masse) == 4
    erste = next(iter(masse.values()))
    for schluessel, gemessen in masse.items():
        assert gemessen == pytest.approx(erste, rel=1e-6), f"{schluessel} schert aus"


@ohne_konverter
@pytest.mark.parametrize("schema, vorsatz", KOMBINATIONEN)
def test_kopf_meldet_schema_und_faktor(gemessene_kombinationen, schema, vorsatz):
    """``lies_ifc_kopf`` liest beide Schemata und beide Einheiten — ohne den Konverter.

    Der Faktor ist bewusst mitgeprüft: ``None`` hiesse *unbekannt*, nicht *Meter*. Diese
    Verwechslung ist der mm-als-m-Fehler, den der Torwächter danach nur noch als Verdacht
    sähe.
    """
    _, kopf, _ = gemessene_kombinationen[(schema, vorsatz)]

    assert kopf["schema"] == schema
    assert kopf["meter_je_einheit"] == pytest.approx(1.0 if vorsatz is None else 0.001)
    assert kopf["meter_je_einheit"] is not None


@ohne_konverter
@pytest.mark.parametrize("schema, vorsatz", KOMBINATIONEN)
def test_erklaerte_einheit_und_gemessene_masse_stimmen_ueberein(gemessene_kombinationen,
                                                                schema, vorsatz):
    """Alle vier sind stimmig — Millimeter braucht keine Umrechnung, IfcOpenShell rechnet."""
    _, kopf, bericht = gemessene_kombinationen[(schema, vorsatz)]
    ergebnis = hk.pruefe_einheit_gegen_masse(kopf, bericht["bbox"])

    assert ergebnis["stimmig"] is True
    assert ergebnis["groesste_kante_m"] == pytest.approx(KANTE_M, rel=1e-6)


@ohne_konverter
@pytest.mark.parametrize("schema, vorsatz", KOMBINATIONEN)
def test_torwaechter_nimmt_alle_vier_an(gemessene_kombinationen, schema, vorsatz):
    """Vor dem Render steht der Torwächter. Lehnte er IFC2X3 ab, käme ArchiCAD nie durch."""
    _, _, bericht = gemessene_kombinationen[(schema, vorsatz)]
    urteil = torwaechter.torwaechter(bericht)

    assert urteil["entscheidung"] == torwaechter.ENTSCHEIDUNG_ANNEHMEN
    assert urteil["massstab"]["plausibel"] is True


@ohne_konverter
@pytest.mark.parametrize("schema", ["IFC4", "IFC2X3"])
def test_die_up_achse_ist_in_beiden_schemata_belegt(gemessene_kombinationen, schema):
    """ISO 16739 gilt für IFC2X3 genauso: Z-up, belegt, nicht vermutet."""
    _, kopf, _ = gemessene_kombinationen[(schema, None)]

    assert kopf["up_axis"] == "Z_UP"
    assert kopf["sicherheit"] == hk.BELEGT
    # `fordere_up_axis` gibt die normalisierte Form zurück ("Z", nicht "Z_UP") — der
    # Kopf trägt die Schreibweise der Norm, der Vertrag die des Projekts.
    assert hk.fordere_up_axis(kopf) == "Z"


# ======================================================================================
# D · Gegenprobe — damit Gruppe C nicht vakuös ist
# ======================================================================================

@ohne_konverter
@pytest.mark.parametrize("schema", ["IFC4", "IFC2X3"])
def test_kaputter_export_wird_als_solcher_erkannt(gemessene_kombinationen, schema):
    """Ohne diesen Test wäre Gruppe C auch dann grün, wenn ``stimmig`` immer ``True`` wäre.

    Die Datei erklärt Millimeter und trägt Meterzahlen. Heraus kommt ein Bauwerk von acht
    Millimetern — und der Befund muss den erklärten Faktor herausrechnen, damit aus dem
    Verdacht des Torwächters eine Diagnose wird.
    """
    _, kopf, bericht = gemessene_kombinationen[(schema, "KAPUTT")]
    ergebnis = hk.pruefe_einheit_gegen_masse(kopf, bericht["bbox"])

    assert ergebnis["stimmig"] is False
    assert ergebnis["groesste_kante_m"] == pytest.approx(KANTE_M * 0.001, rel=1e-6)
    assert "8 m" in ergebnis["befund"], "Der herausgerechnete Wert macht den Befund prüfbar"
    assert "millimetre" in ergebnis["befund"]
    assert "Export" in ergebnis["befund"]


@ohne_konverter
@pytest.mark.parametrize("schema", ["IFC4", "IFC2X3"])
def test_torwaechter_lehnt_den_kaputten_export_ab(gemessene_kombinationen, schema):
    """Der Torwächter sieht nur die Masse — und lehnt trotzdem ab, in beiden Schemata."""
    _, _, bericht = gemessene_kombinationen[(schema, "KAPUTT")]
    urteil = torwaechter.torwaechter(bericht)

    assert urteil["entscheidung"] == torwaechter.ENTSCHEIDUNG_ABLEHNEN_MASSSTAB
    assert urteil["massstab"]["verdacht_faktor"] == pytest.approx(0.001)


@ohne_konverter
@pytest.mark.parametrize("schema", ["IFC4", "IFC2X3"])
def test_echte_millimeterdatei_und_kaputter_export_gehen_auseinander(
        gemessene_kombinationen, schema):
    """Gleicher Kopf, tausendfach verschiedenes Ergebnis — die Pointe der ganzen Gruppe."""
    _, kopf_echt, bericht_echt = gemessene_kombinationen[(schema, "MILLI")]
    _, kopf_kaputt, bericht_kaputt = gemessene_kombinationen[(schema, "KAPUTT")]

    assert kopf_echt["meter_je_einheit"] == kopf_kaputt["meter_je_einheit"]
    echt = hk.pruefe_einheit_gegen_masse(kopf_echt, bericht_echt["bbox"])
    kaputt = hk.pruefe_einheit_gegen_masse(kopf_kaputt, bericht_kaputt["bbox"])

    assert echt["stimmig"] is True and kaputt["stimmig"] is False
    assert echt["groesste_kante_m"] == pytest.approx(kaputt["groesste_kante_m"] * 1000.0,
                                                     rel=1e-6)


# ======================================================================================
# E · Der Befund: die IFC2X3-Variante ist kein gültiges IFC2X3
# ======================================================================================
#
# Gesucht war, ob am Schemawechsel mehr hängt als das eine Wandattribut. Es hängt mehr
# daran, und es steht nicht in der Attributzahl:
#
#   IFC2X3:  ENTITY IfcRoot;  GlobalId : IfcGloballyUniqueId;
#                             OwnerHistory : IfcOwnerHistory;            <- PFLICHT
#   IFC4:    ENTITY IfcRoot;  GlobalId : IfcGloballyUniqueId;
#                             OwnerHistory : OPTIONAL IfcOwnerHistory;   <- optional
#
# Die Fixture schreibt an dieser Stelle durchweg `$` (nicht gesetzt). In IFC4 ist das
# richtig, in IFC2X3 verletzt es ein Pflichtattribut — in **jeder** der dreizehn
# IfcRoot-Ableitungen der Datei. Die Attributzahl bleibt dabei gleich (vier), darum
# fällt es beim Zählen nicht auf und der Konverter liest die Datei anstandslos.
#
# Dieselbe Verschärfung betrifft in IFC2X3 auch `CompositionType` (IfcSite, IfcBuilding,
# IfcBuildingStorey) sowie `Position` in IfcRectangleProfileDef und IfcExtrudedAreaSolid.
# Dort ist nichts zu tun: Die Fixture setzt diese Werte ohnehin.
#
# Nicht repariert, wie beauftragt. Die Reparatur wäre eine IfcOwnerHistory samt
# IfcPerson/IfcOrganization/IfcApplication — vier zusätzliche Entitäten, und sie gehört
# in die Fixture, nicht in deren Test.

def test_ifc2x3_setzt_die_pflichtige_ownerhistory(tmp_path):
    """Textnachweis des Befunds, ohne Konverter — er läuft auch ohne ``.venv-ifc``."""
    text = text_von(tmp_path / "bau.ifc", schema="IFC2X3")

    ohne = [(name, felder) for name in WURZELENTITAETEN
            for felder in entitaeten(text, name) if felder[OWNERHISTORY] == "$"]

    assert not ohne, (f"{len(ohne)} IfcRoot-Ableitungen ohne OwnerHistory: "
                      f"{sorted({name for name, _ in ohne})}")


def test_beide_schemata_tragen_die_ownerhistory(tmp_path):
    """**Berichtigt am 18.08.2026 — der Befund dieser Testabnahme ist behoben.**

    ``IfcRoot.OwnerHistory`` ist in IFC2X3 **Pflicht** und erst in IFC4 optional. Die
    Fixture schrieb in beiden Schemata ``$``. Weil die Attributzahl gleich bleibt (4),
    fiel es beim Zählen nicht auf, und IfcOpenShell las die Datei anstandslos — erst
    ``ifcopenshell.validate`` meldete **dreizehn** Fehler „Attribute not optional".

    > Dass etwas gelesen wird, ist kein Beleg dafür, dass es gültig ist.

    Angelegt wird die Angabe jetzt für **beide** Schemata. In IFC4 schadet sie nicht, und
    zwei Wege wären eine Abweichung, die niemand bemerkt.
    """
    for schema in ("IFC4", "IFC2X3"):
        text = text_von(tmp_path / f"{schema}.ifc", schema=schema)
        assert "IFCOWNERHISTORY(" in text, schema
        # Und sie wird auch benutzt: keine IfcRoot-Ableitung trägt mehr `$` an Stelle 2.
        for entitaet in ("IFCPROJECT", "IFCSITE", "IFCBUILDING", "IFCBUILDINGSTOREY",
                         "IFCSLAB", "IFCWALL", "IFCRELAGGREGATES",
                         "IFCRELCONTAINEDINSPATIALSTRUCTURE"):
            for zeile in [z for z in text.splitlines() if f"={entitaet}(" in z
                          or z.strip().startswith(entitaet + "(")]:
                nach_guid = zeile.split("',", 1)[1] if "'," in zeile else ""
                assert not nach_guid.startswith("$,"), f"{schema}/{entitaet}: {zeile[:70]}"


# ======================================================================================
# E · Das zweite Bauwerk — der gegliederte Hochbau
# ======================================================================================
#
# **Warum es ihn gibt.** Jede Messung dieser Umgebung stand bis zum 26.08.2026 auf EINEM
# Quader mit sechs Bauteilen. Für Einheiten, Schemata und Hüllboxen ist das genau richtig;
# für alles, was mit Gliederung zu tun hat, wertlos.
#
# Die Merkmale sind zitiert, nicht erfunden — die HomeStation über ihr eigenes Modell:
# *«Es ist KEIN glatter Quader. Es hat Auskragungen, ein Stuetzenraster, eine gegliederte
# Huelle und einen Kern — also genau die Merkmale, an denen sich eine Geometriepruefung
# bewaehren muss.»* Ihr Modell dürfen wir nicht haben (Regel 3); die Merkmale schon.

#: Die Wörter der Geländeregel. Hier wiederholt und nicht importiert, damit dieser Test
#: auch dann greift, wenn jemand die Liste drüben ändert — er soll dann rot werden und
#: nicht stillschweigend mitwandern.
GELAENDE_WOERTER_KOPIE = ("gelaende", "gelände", "terrain", "site")


def test_der_hochbau_hat_zwei_groessenordnungen_mehr_bauteile(tmp_path):
    """Sechs gegen einhunderteinundvierzig. Das ist der ganze Zweck."""
    ifc = FIXTURE.erzeuge_ifc(tmp_path / "hb.ifc", hochbau=True)
    text = ifc.read_text(encoding="utf-8")
    teile = (text.count("IFCSLAB(") + text.count("IFCCOLUMN(") + text.count("IFCWALL("))
    assert teile == 141, (
        f"{teile} Bauteile statt 141. Wer die Szene ändert, ändert jede Messung, die auf "
        f"ihr steht — dann gehört die Zahl hier mitgeändert und die Messreihe neu."
    )


def test_die_auskragung_koppelt_die_huelle_vom_grundriss_ab(tmp_path):
    """**Das Merkmal, das eine Prüfung entlarvt, die Grundriss und Hülle verwechselt.**

    Der Grundriss ist 8,0 m tief, die Hülle 9,5 m — die oberen Geschosse ragen hinaus.
    Ohne die Auskragung wäre die Hülle die schlichte Extrusion des Grundrisses, und jede
    solche Verwechslung käme damit durch.
    """
    assert FIXTURE.HB_AUSKRAGUNG > 0
    assert FIXTURE.HB_AUSKRAGUNG_AB_GESCHOSS < FIXTURE.HB_GESCHOSSE, (
        "Die Auskragung setzt erst über dem obersten Geschoss ein — dann gibt es keine.")
    ifc = FIXTURE.erzeuge_ifc(tmp_path / "hb.ifc", hochbau=True)
    assert "auskragend" in ifc.read_text(encoding="utf-8")


def test_kein_bauteilname_des_hochbaus_trifft_die_gelaenderegel(tmp_path):
    """Sonst nähme die Bauwerksmaske Teile des Bauwerks für Gelände.

    Der Fall ist nicht erfunden: `IfcWall_Site-A` gilt der Regel als Gelände, weil `site`
    eines ihrer Wörter ist. Eine so benannte Wand fiele aus der Maske.
    """
    import re

    ifc = FIXTURE.erzeuge_ifc(tmp_path / "hb.ifc", hochbau=True)
    namen = re.findall(r"IFC(?:SLAB|COLUMN|WALL)\('[^']+',[^,]+,'([^']+)'", 
                       ifc.read_text(encoding="utf-8"))
    assert namen, "Keine Bauteilnamen gefunden — dann prüft dieser Test nichts."
    treffer = [n for n in namen
               if set(re.split(r"[\s_\-.,;:/\\()\[\]]+", n.lower()))
               & set(GELAENDE_WOERTER_KOPIE)]
    assert not treffer, (
        f"Diese Bauteile des Hochbaus gelten der Geländeregel als Gelände und fielen aus "
        f"der Bauwerksmaske: {sorted(set(treffer))}"
    )


def test_der_hochbau_aendert_die_vorgabe_nicht(tmp_path):
    """**Die wichtigste Zusicherung dieser Erweiterung.**

    Der Modulkopf sagt es selbst: *«Eine stillschweigend geänderte Testgeometrie macht
    eine Messreihe unbrauchbar, ohne dass es auffällt.»* An der Hüllbox 8,0 × 5,0 × 3,25 m
    und an sechs Bauteilen hängt alles, was vor dem 26.08.2026 gemessen wurde.
    """
    ohne = FIXTURE.erzeuge_ifc(tmp_path / "a.ifc").read_text(encoding="utf-8")
    # Der Rumpf ohne die Kopfzeile mit dem Dateinamen.
    rumpf = "\n".join(z for z in ohne.splitlines() if not z.startswith("FILE_NAME"))
    assert rumpf.count("IFCWALL(") == 4
    assert rumpf.count("IFCSLAB(") == 1
    assert "IFCCOLUMN(" not in rumpf, "Der Quader hat keine Stützen."
    assert "Stuetze_" not in rumpf and "Fassade_" not in rumpf and "Kern_" not in rumpf


def test_hochbau_und_raeume_zugleich_werden_abgelehnt(tmp_path):
    """Geraten wird nicht: Die beiden Räume liegen an der Wandflucht des Quaders."""
    with pytest.raises(ValueError, match="Kern"):
        FIXTURE.erzeuge_ifc(tmp_path / "x.ifc", hochbau=True, mit_raeumen=True)


def test_der_hochbau_traegt_ein_gelaende_wenn_bestellt(tmp_path):
    """Die übrigen Schalter wirken weiter — der Hochbau ersetzt das Bauwerk, nicht die Datei."""
    ifc = FIXTURE.erzeuge_ifc(tmp_path / "hb.ifc", hochbau=True, mit_gelaende=True)
    text = ifc.read_text(encoding="utf-8")
    assert "'Gelaende'" in text
    assert "Stuetze_" in text


@pytest.mark.parametrize("schema", ["IFC4", "IFC2X3"])
def test_der_hochbau_gibt_es_in_beiden_schemata(tmp_path, schema):
    """ArchiCAD liefert IFC2X3 — eine Testszene, die es nur in IFC4 gibt, prüft die
    Hälfte der Wirklichkeit nicht."""
    ifc = FIXTURE.erzeuge_ifc(tmp_path / f"hb_{schema}.ifc", schema=schema, hochbau=True)
    assert f"FILE_SCHEMA(('{schema}'))" in ifc.read_text(encoding="utf-8")


@ohne_konverter
@pytest.mark.parametrize("schema", ["IFC4", "IFC2X3"])
def test_der_hochbau_besteht_den_schemapruefer(tmp_path, schema):
    """Vom echten Prüfer beurteilt, nicht von uns.

    Genau dieser Weg hat an der ersten Fixture dreizehn Fehler gefunden, die beim Zählen
    von Attributen unsichtbar waren.
    """
    ifc = FIXTURE.erzeuge_ifc(tmp_path / f"hb_{schema}.ifc", schema=schema, hochbau=True)
    fehler = schemafehler(ifc)
    assert not fehler, f"{len(fehler)} Schemafehler, erste drei: {fehler[:3]}"
