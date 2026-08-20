"""Räume aus einer IFC — die Fixture, die Naht und der echte Lauf durch das `.venv-ifc`.

Worum es geht
-------------
Das Projekt konnte Gebäude bisher nur von aussen: ``kameras.py`` rechnet ausschliesslich
Standpunkte um eine Hüllbox herum, und ``WANDABSTAND_M = 10.0`` macht eine Innenaufnahme
**rechnerisch unmöglich** — in einem 4 m breiten Zimmer gibt es keinen zulässigen
Standpunkt. Der Grund, warum das nicht einfach zu beheben war, liegt eine Ebene tiefer:
Es gab **kein einziges ``IfcSpace``** im ganzen Projekt, weder in der Testgeometrie noch
im Leser. Ohne Räume gibt es nichts, worin ein Standpunkt liegen könnte.

Diese Datei prüft die Voraussetzung, nicht den Innenraum-Modus.

Vier Gruppen, bewusst getrennt
------------------------------
**A · Die Fixture, ohne Konverter.** Reine Textprüfung an der erzeugten Datei: dass der
Schalter wirklich aus ist, wenn er aus ist; dass zwei Räume entstehen und nicht einer;
dass die Millimeter-Variante **die Zahlen** mitrechnet und nicht nur die Einheitenzeile
umstellt. Läuft überall — kein ``ifcopenshell``, kein Netz, keine GPU.

**B · Die Naht, ohne venv.** ``seams.ifc_raeume`` bekommt ein ``_starte``-Doppelgänger
hereingereicht. Geprüft wird, **was** aufgerufen worden wäre und wie die Naht auf einen
scheiternden, einen stummen und einen schwatzhaften Runner reagiert. Es wird kein Prozess
gestartet.

**C · Der echte Lauf** (übersprungen, wenn ``.venv-ifc`` fehlt). Alle vier Kombinationen
aus Schema und Einheit durch den echten Runner, und die Zahlen dahinter verglichen. Das
ist der eigentliche Beleg: Schema und Einheit ändern die **Datei**, nicht die **Räume**.

**D · Was der Runner NICHT kann.** Die wichtigste Gruppe. Ein Leser, der Räume
stillschweigend weglässt, ist schlimmer als einer, der gar nichts findet: Der Aufrufer
sähe drei Räume und hielte sie für alle. Drei Operationen am Dateitext — Geometrie
wegnehmen, Rechteck durch Kreis ersetzen, Extrusion schief stellen — müssen jeweils zu
einem **benannten Befund** führen, und der Raum muss trotzdem in der Liste stehen.

Die dritte davon hat den Entwurf noch geändert: Bei einer schiefen Extrusion ist der
Fussbodenumriss einwandfrei gelesen, und nur der **Bezugspunkt der Höhe** ist weg. Ein
einziges Urteil hätte hier entweder eine gültige Messung weggeworfen oder eine erfundene
Höhe geliefert. Seither gibt es zwei: ``befund`` für den Grundriss, ``hoehe_befund`` für
die Höhe.
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
from aiimaging import seams
from aiimaging.seams import SeamError, ifc_raeume

# ======================================================================================
# Festwerte
# ======================================================================================

#: Die vier Kombinationen, dieselben wie in ``test_testgeometrie.py``.
KOMBINATIONEN = [
    pytest.param("IFC4", None, id="ifc4-meter"),
    pytest.param("IFC4", "MILLI", id="ifc4-millimeter"),
    pytest.param("IFC2X3", None, id="ifc2x3-meter"),
    pytest.param("IFC2X3", "MILLI", id="ifc2x3-millimeter"),
]

#: So viele Räume schreibt ``--raeume``. Die Zahl wird mitgeprüft, damit kein Test
#: dadurch grün bleibt, dass er gar keinen Raum gefunden hat.
ANZAHL_RAEUME = 2

#: Attributzahl von ``IFCSPACE`` — **in beiden Schemata elf.** Anders als bei ``IfcWall``
#: ist die Zahl hier kein Unterscheidungsmerkmal; der Unterschied sitzt in der Bedeutung
#: des zehnten Attributs. Geprüft wird die Zahl trotzdem: Sie ist die billigste Art zu
#: merken, dass jemand ein Attribut vergessen oder eines zuviel geschrieben hat.
RAUM_ATTRIBUTE = 11

#: Stellung der Felder in ``IFCSPACE`` (nullbasiert), soweit hier gebraucht.
RAUM_NAME, RAUM_ORT, RAUM_SHAPE, RAUM_LANGNAME, RAUM_ZEHNTES = 2, 5, 6, 7, 9

#: Die Längeneinheitszeile der Meter-Variante, und dieselbe auf Millimeter gestellt.
#: **Nur** die Zeile — die Zahlen bleiben. Das ist der kaputte Export, nicht die
#: Millimeter-Variante.
EINHEIT_METER = "IFCSIUNIT(*,.LENGTHUNIT.,$,.METRE.)"
EINHEIT_MILLI = "IFCSIUNIT(*,.LENGTHUNIT.,.MILLI.,.METRE.)"

#: Die Wandhöhe der Testgeometrie. Sie steht hier, weil sie **nicht** herauskommen darf:
#: Wer die Geschoss- oder Wandhöhe für eine Raumhöhe hält, macht genau den Fehler, gegen
#: den der ganze Bezugspunkt-Aufwand gebaut ist.
WANDHOEHE_M = 3.0

_RE_ENTITAET = re.compile(r"^#(\d+)=\s*([A-Za-z0-9]+)\((.*)\);\s*$")


# ======================================================================================
# Werkzeuge
# ======================================================================================

def _lade_fixturemodul():
    """``tools/make_test_ifc.py`` als Modul laden — ``tools/`` ist kein Paket."""
    pfad = REPO / "tools" / "make_test_ifc.py"
    spezifikation = importlib.util.spec_from_file_location("make_test_ifc_raeume", pfad)
    modul = importlib.util.module_from_spec(spezifikation)
    spezifikation.loader.exec_module(modul)
    return modul


FIXTURE = _lade_fixturemodul()


def erzeuge(ziel: Path, *, schema="IFC4", vorsatz=None, mit_raeumen=True) -> Path:
    """Eine Spielart der Testgeometrie schreiben und den Pfad zurückgeben."""
    ziel.parent.mkdir(parents=True, exist_ok=True)
    return FIXTURE.erzeuge_ifc(ziel, schema=schema, vorsatz=vorsatz, mit_raeumen=mit_raeumen)


def entitaeten(text: str, name: str) -> list[list[str]]:
    """Alle Vorkommen einer STEP-Entität als Feldlisten.

    Zerlegt mit ``herkunft._step_felder`` — demselben klammertreuen Zerleger, den das
    Projekt ohnehin hat und der dort geprüft ist. Ein zweiter, hier hingeschriebener
    Zerleger wäre eine zweite Meinung darüber, was ein Feld ist.
    """
    treffer = []
    for zeile in text.splitlines():
        gefunden = _RE_ENTITAET.match(zeile.strip())
        if gefunden and gefunden.group(2).upper() == name.upper():
            treffer.append(hk._step_felder(gefunden.group(3)))
    return treffer


def karte(text: str) -> dict:
    """``#12`` → ``(Typname, Felder)`` für die ganze Datei.

    Damit lassen sich Verweise verfolgen, statt Zeilen zu erraten. Die drei Operationen
    in Gruppe D hängen daran: Sie müssen **genau** die Geometrie eines **bestimmten**
    Raums treffen und nicht irgendeine ähnlich aussehende Zeile — sonst prüfte der Test
    etwas anderes, als sein Name sagt.
    """
    aus = {}
    for zeile in text.splitlines():
        gefunden = _RE_ENTITAET.match(zeile.strip())
        if gefunden:
            aus[f"#{gefunden.group(1)}"] = (gefunden.group(2).upper(),
                                            hk._step_felder(gefunden.group(3)))
    return aus


def _verweis(feld: str) -> str:
    """Der erste ``#n``-Verweis in einem Feld."""
    treffer = re.search(r"#\d+", feld)
    assert treffer, f"kein Verweis in {feld!r}"
    return treffer.group(0)


def raum_zeile(text: str, name: str) -> tuple[str, str, list[str]]:
    """``(id, Rohzeile, Felder)`` des ``IFCSPACE`` mit diesem Namen."""
    for zeile in text.splitlines():
        gefunden = _RE_ENTITAET.match(zeile.strip())
        if gefunden and gefunden.group(2).upper() == "IFCSPACE":
            felder = hk._step_felder(gefunden.group(3))
            if felder[RAUM_NAME] == f"'{name}'":
                return f"#{gefunden.group(1)}", zeile, felder
    raise AssertionError(f"Kein IFCSPACE namens {name!r} in der Datei")


def koerper_von(text: str, name: str) -> tuple[str, list[str]]:
    """``(id, Felder)`` des ``IFCEXTRUDEDAREASOLID``, der zu diesem Raum gehört.

    Der Weg ist der, den auch der Runner geht: Raum → ProductDefinitionShape →
    ShapeRepresentation → Items. Ihn hier nachzugehen ist Absicht: Trifft die Operation
    den falschen Körper, fällt der Test auf und nicht der Runner.
    """
    k = karte(text)
    _, _, felder = raum_zeile(text, name)
    shape = k[_verweis(felder[RAUM_SHAPE])]
    rep = k[_verweis(shape[1][2])]
    posten = k[_verweis(rep[1][3])]
    assert posten[0] == "IFCEXTRUDEDAREASOLID", posten[0]
    return _verweis(rep[1][3]), posten[1]


def _ersetze_zeile(text: str, ident: str, neu: str) -> str:
    """Eine ganze Entitätszeile austauschen — und darauf bestehen, dass es geklappt hat.

    Ein ``replace``, das nichts ersetzt, gibt den Text unverändert zurück und macht den
    Test grün, ohne dass er irgendetwas geprüft hätte. Genau diese Sorte Grün hat dieses
    Projekt schon einmal beschäftigt.
    """
    alt = [z for z in text.splitlines() if z.strip().startswith(f"{ident}= ")]
    assert len(alt) == 1, f"{ident} kommt {len(alt)}× vor — die Fixture hat sich geändert"
    ersetzt = text.replace(alt[0], neu)
    assert ersetzt != text, f"Der Austausch von {ident} hat nichts bewirkt"
    return ersetzt


def ohne_geometrie(text: str, name: str) -> str:
    """Einem Raum die ``Representation`` wegnehmen — er bleibt, seine Form geht."""
    ident, zeile, felder = raum_zeile(text, name)
    felder[RAUM_SHAPE] = "$"
    return _ersetze_zeile(text, ident, f"{ident}= IFCSPACE({','.join(felder)});")


def mit_kreisprofil(text: str, name: str) -> str:
    """Das Rechteckprofil eines Raums durch einen Kreis ersetzen.

    Ein Kreis ist ein gültiges IFC-Profil und **kein Polygon**. Wer daraus einen Grundriss
    machte, erfände eine Auflösung, die in der Datei nicht steht.
    """
    _, koerper = koerper_von(text, name)
    profil_id = _verweis(koerper[0])
    art, felder = karte(text)[profil_id]
    assert art == "IFCRECTANGLEPROFILEDEF", art
    radius = float(felder[3]) / 2.0
    return _ersetze_zeile(
        text, profil_id,
        f"{profil_id}= IFCCIRCLEPROFILEDEF({felder[0]},{felder[1]},{felder[2]},"
        f"{radius:.6f});")


def mit_schiefer_extrusion(text: str, name: str) -> str:
    """Die Extrusionsrichtung eines Raums um 45° kippen.

    ``(0.,1.,1.)`` ist bewusst **nicht** waagerecht: Eine zur lokalen Z-Achse senkrechte
    Extrusionsrichtung verletzt eine informelle Festlegung von IFC, und dann prüfte dieser
    Test eine ungültige Datei statt eines schiefen Raums. So ist die Datei gültig und der
    Raum bloss schief — genau der Fall, für den der Befund gedacht ist.
    """
    _, koerper = koerper_von(text, name)
    richtung_id = _verweis(koerper[2])
    art, _ = karte(text)[richtung_id]
    assert art == "IFCDIRECTION", art
    return _ersetze_zeile(text, richtung_id, f"{richtung_id}= IFCDIRECTION((0.,1.,1.));")


def welt_ring(raum: dict) -> list[tuple[float, float]]:
    """Der erwartete Grundriss eines Fixture-Raums in Weltkoordinaten, in Metern."""
    ex, ey = raum["einfuegepunkt"]
    return [(round(ex + rx, 6), round(ey + ry, 6)) for rx, ry in raum["ring_relativ"]]


def zyklisch_gleich(a, b) -> bool:
    """Sind zwei Ringe dasselbe Polygon — gleiche Reihenfolge, beliebiger Startpunkt?

    Nicht einfach ``set(a) == set(b)``: Das hielte ein Polygon und sein überkreuztes
    Gegenstück für gleich. Und nicht ``a == b``: Wo ein Ring anfängt, ist eine
    Schreibweise und keine Eigenschaft — beim Rechteckprofil stehen die Ecken gar nicht
    in der Datei, sie entstehen erst beim Lesen. Der **Umlaufsinn** bleibt aber eine
    Eigenschaft, und darum wird nicht rückwärts verglichen.
    """
    a = [tuple(round(float(v), 6) for v in p) for p in a]
    b = [tuple(round(float(v), 6) for v in p) for p in b]
    if len(a) != len(b) or not a:
        return False
    return any(a[i:] + a[:i] == b for i in range(len(a)))


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


class Ergebnis:
    """Doppelgänger eines ``subprocess.CompletedProcess`` — nur, was die Naht ausliest."""

    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode, self.stdout, self.stderr = returncode, stdout, stderr


class Aufrufer:
    """Ersatz für ``_starte``: merkt sich die Kommandos, statt Prozesse zu starten."""

    def __init__(self, ergebnis=None):
        self.ergebnis = ergebnis or Ergebnis(stdout=json.dumps({"status": "ok"}))
        self.kommandos: list[list[str]] = []
        self.timeouts: list[int] = []

    def __call__(self, cmd, timeout):
        self.kommandos.append(list(cmd))
        self.timeouts.append(timeout)
        return self.ergebnis

    @property
    def kommando(self) -> list[str]:
        assert len(self.kommandos) == 1, f"erwartet: ein Aufruf, war {len(self.kommandos)}"
        return self.kommandos[0]


def verweigerer(cmd, timeout):
    """``_starte``, das nie aufgerufen werden darf — belegt, dass vorher abgebrochen wurde."""
    raise AssertionError(f"Es wurde ein Prozess gestartet, obwohl nichts da war: {cmd}")


@pytest.fixture
def ifc_python_attrappe(monkeypatch):
    """Ein Pfad, der das ``.venv-ifc``-Python vertritt — ausgeführt wird er nie."""
    monkeypatch.setenv("AIIMAGING_IFC_PYTHON", "/attrappe/venv-ifc/bin/python")
    return "/attrappe/venv-ifc/bin/python"


# ======================================================================================
# 0 · Selbstproben der Werkzeuge
#
# Ein Testwerkzeug, das immer wahr sagt, macht jede Prüfung darüber wertlos. Diese Datei
# hat drei davon; sie werden hier gegen ihre eigene Behauptung gehalten.
# ======================================================================================

def test_zyklisch_gleich_erkennt_verschobenen_startpunkt():
    """Wo ein Ring anfängt, ist Schreibweise — dasselbe Polygon bleibt dasselbe."""
    assert zyklisch_gleich([(0, 0), (1, 0), (1, 1)], [(1, 0), (1, 1), (0, 0)])


def test_zyklisch_gleich_lehnt_umgekehrten_umlaufsinn_ab():
    """Gegenprobe: Der Umlaufsinn ist eine Eigenschaft und keine Schreibweise.

    Ohne diesen Test wäre :func:`zyklisch_gleich` womöglich ein Mengenvergleich — und
    dann prüften alle Grundriss-Vergleiche dieser Datei nur noch, dass die richtigen
    Punkte vorkommen, in beliebiger Reihenfolge.
    """
    assert not zyklisch_gleich([(0, 0), (1, 0), (1, 1)], [(1, 1), (1, 0), (0, 0)])


def test_zyklisch_gleich_lehnt_verschiedene_laenge_ab():
    assert not zyklisch_gleich([(0, 0), (1, 0), (1, 1)], [(0, 0), (1, 0)])


def test_ersetze_zeile_meldet_einen_nicht_greifenden_austausch(tmp_path):
    """Selbstprobe der Operationen aus Gruppe D: Was nichts trifft, muss auffallen."""
    text = erzeuge(tmp_path / "a.ifc").read_text(encoding="utf-8")
    with pytest.raises(AssertionError):
        _ersetze_zeile(text, "#999999", "#999999= IFCDIRECTION((0.,0.,1.));")


# ======================================================================================
# A · Die Fixture — ohne Konverter
# ======================================================================================

@pytest.mark.parametrize("schema, vorsatz", KOMBINATIONEN)
def test_ohne_schalter_gibt_es_keinen_einzigen_raum(tmp_path, schema, vorsatz):
    """Der Schalter ist aus, wenn er aus ist — und das ist keine Kleinigkeit.

    Jede bestehende Messung des Projekts hängt an der Testgeometrie, wie sie war. Ein
    Raum ist zwar innen und ändert die Hüllbox nicht, aber er ist ein weiteres
    ``IfcProduct`` mit Geometrie: ``ifc_zu_glb`` zählte danach andere Elemente und
    Dreiecke. Eine stillschweigend geänderte Testgeometrie macht eine Messreihe
    unbrauchbar, ohne dass es auffällt.
    """
    text = erzeuge(tmp_path / "ohne.ifc", schema=schema, vorsatz=vorsatz,
                   mit_raeumen=False).read_text(encoding="utf-8")
    assert "IFCSPACE" not in text.upper()


@pytest.mark.parametrize("schema, vorsatz", KOMBINATIONEN)
def test_mit_schalter_stehen_zwei_raeume_darin(tmp_path, schema, vorsatz):
    """Zwei und nicht einer: Ein Verfahren, das nur an einem Raum geprüft wird, kann an
    einer Konstanten hängen, die zufällig passt."""
    text = erzeuge(tmp_path / "mit.ifc", schema=schema, vorsatz=vorsatz).read_text("utf-8")
    raeume = entitaeten(text, "IFCSPACE")
    assert len(raeume) == ANZAHL_RAEUME
    assert {f["name"] for f in FIXTURE.RAEUME} == {r[RAUM_NAME].strip("'") for r in raeume}


@pytest.mark.parametrize("schema, vorsatz", KOMBINATIONEN)
def test_jeder_raum_hat_elf_attribute(tmp_path, schema, vorsatz):
    """``IfcSpace`` hat in **beiden** Schemata elf Attribute — die Zahl trennt sie nicht.

    Bei ``IfcWall`` tut sie es (neun gegen acht), und genau darum steht dieser Test hier:
    Wer die Wand-Lehre auf den Raum überträgt und ein Attribut weglässt, bekommt eine
    ungültige Datei, die ein nachsichtiger Leser trotzdem liest.
    """
    text = erzeuge(tmp_path / "mit.ifc", schema=schema, vorsatz=vorsatz).read_text("utf-8")
    raeume = entitaeten(text, "IFCSPACE")
    assert raeume, "keine Räume gefunden — der Test prüfte sonst eine leere Menge"
    assert [len(r) for r in raeume] == [RAUM_ATTRIBUTE] * len(raeume)


@pytest.mark.parametrize("schema", ["IFC4", "IFC2X3"])
def test_das_zehnte_attribut_ist_in_beiden_schemata_INTERNAL(tmp_path, schema):
    """Dasselbe Wort, zwei verschiedene Aufzählungen — und in beiden richtig gemeint.

    IFC2X3 hat an zehnter Stelle ``InteriorOrExteriorSpace`` (``IfcInternalOrExternalEnum``),
    IFC4 hat dort ``PredefinedType`` (``IfcSpaceTypeEnum``). ``.INTERNAL.`` ist in beiden
    Aufzählungen enthalten. Wer stattdessen das IFC4-übliche ``.SPACE.`` schriebe, machte
    die IFC2X3-Datei ungültig — **ohne dass die Attributzahl es verriete.** Dass es hier
    gutgeht, ist ein Zufall; dass wir uns darauf verlassen, ist eine Entscheidung, und die
    steht darum in einem Test.
    """
    text = erzeuge(tmp_path / "mit.ifc", schema=schema).read_text(encoding="utf-8")
    raeume = entitaeten(text, "IFCSPACE")
    assert raeume
    assert {r[RAUM_ZEHNTES] for r in raeume} == {".INTERNAL."}


def test_ein_raum_hat_einen_langen_namen_und_einer_keinen(tmp_path):
    """``LongName`` ist optional — und ein fehlendes Feld muss später ``None`` werden, nicht ``""``.

    Die Fixture lässt genau einen der beiden leer. Wären beide gefüllt, könnte niemand
    zeigen, dass der Leser den Unterschied macht.
    """
    text = erzeuge(tmp_path / "mit.ifc").read_text(encoding="utf-8")
    lang = sorted(r[RAUM_LANGNAME] for r in entitaeten(text, "IFCSPACE"))
    assert lang == ["$", "'Aufenthalt Nord'"]


def test_raeume_haengen_am_geschoss_ueber_aggregation_nicht_ueber_einlagerung(tmp_path):
    """Ein Raum wird dem Geschoss **zugeordnet**, nicht darin **eingelagert**.

    ``IfcRelContainedInSpatialStructure`` ist für Bauteile gedacht; ein Raum dort drin
    machte die Datei für einen strengen Leser ungültig. Geprüft wird beides: dass er in
    der Aggregation steht **und** dass er nicht in der Einlagerung steht — die zweite
    Hälfte ist die, die wirklich beisst.
    """
    text = erzeuge(tmp_path / "mit.ifc").read_text(encoding="utf-8")
    ids = {raum_zeile(text, r["name"])[0] for r in FIXTURE.RAEUME}
    assert len(ids) == ANZAHL_RAEUME

    aggregiert = {v for f in entitaeten(text, "IFCRELAGGREGATES")
                  for v in re.findall(r"#\d+", f[5])}
    eingelagert = {v for f in entitaeten(text, "IFCRELCONTAINEDINSPATIALSTRUCTURE")
                   for v in re.findall(r"#\d+", f[4])}
    assert ids <= aggregiert
    assert not (ids & eingelagert)


def test_die_millimeter_variante_rechnet_die_raumzahlen_mit(tmp_path):
    """Die wichtigste Prüfung der Gruppe A — und der Fall, den sie **ausschliesst**.

    Eine Datei, die die Einheitenzeile auf ``.MILLI.`` stellt und die Zahlen metergross
    lässt, ist ein **kaputter Export** und keine Testgeometrie. Ein Test, der nur nach
    ``.MILLI.`` sucht, hielte beides für dasselbe. Geprüft wird darum an einer konkreten
    Zahl aus dem Grundriss des L-förmigen Raums: 7,4 m Länge werden zu 7400 mm.
    """
    meter = erzeuge(tmp_path / "m.ifc").read_text(encoding="utf-8")
    milli = erzeuge(tmp_path / "mm.ifc", vorsatz="MILLI").read_text(encoding="utf-8")

    assert EINHEIT_METER in meter and EINHEIT_MILLI in milli
    assert "IFCCARTESIANPOINT((7.400000,2.200000))" in meter
    assert "IFCCARTESIANPOINT((7400.000000,2200.000000))" in milli
    assert "IFCCARTESIANPOINT((7.400000,2.200000))" not in milli


def test_die_fixture_raeume_fuellen_das_wandinnere_lueckenlos(tmp_path):
    """Selbstprobe der Zahlen in :data:`RAEUME` — sie sollen zueinander passen, nicht bloss
    nebeneinander stehen.

    Innenmass ist ``(8,0 − 2·0,3) × (5,0 − 2·0,3)``. Die beiden Raumflächen müssen das
    genau ergeben. Wer die Fixture später ändert und diese Probe reisst, hat entweder
    einen Raum verschoben oder eine Fläche falsch notiert — beides würde sonst erst in
    einem Grundriss auffallen, den niemand nachrechnet.
    """
    innen = (FIXTURE.LAENGE_X - 2 * FIXTURE.WANDDICKE) * (FIXTURE.BREITE_Y - 2 * FIXTURE.WANDDICKE)
    assert round(sum(r["flaeche"] for r in FIXTURE.RAEUME), 6) == round(innen, 6)


def test_die_beiden_raeume_unterscheiden_sich_in_jeder_pruefbaren_groesse():
    """Zwei gleiche Räume wären ein Raum in zweifacher Ausfertigung.

    Fläche, Höhe, Fussbodenhöhe und die Art, wie der Grundriss in der Datei steht — in
    allen vieren müssen sie auseinandergehen. Sonst könnte ein Leser die Werte des einen
    für den anderen ausgeben, ohne dass ein Test es merkte.
    """
    a, b = FIXTURE.RAEUME
    assert a["flaeche"] != b["flaeche"]
    assert a["hoehe"] != b["hoehe"]
    assert a["z_unten"] != b["z_unten"]
    assert a["profil"] != b["profil"]
    assert WANDHOEHE_M not in (a["hoehe"], b["hoehe"]), (
        "Keine Raumhöhe darf zufällig die Wandhöhe sein — sonst bliebe die "
        "Verwechslung von Raum- und Geschosshöhe unbemerkt."
    )


def test_zwei_laeufe_ergeben_dieselbe_datei(tmp_path):
    """Ohne Determinismus wäre kein Test reproduzierbar und jeder Lauf erzeugte einen Diff."""
    a = erzeuge(tmp_path / "a.ifc").read_text(encoding="utf-8")
    b = erzeuge(tmp_path / "b.ifc").read_text(encoding="utf-8")
    assert a.replace("a.ifc", "X") == b.replace("b.ifc", "X")


def test_kommandozeile_kennt_den_schalter(tmp_path):
    """Der übliche Weg ist der Aufruf als Skript — er muss dasselbe liefern wie der Aufruf."""
    ziel = tmp_path / "cli.ifc"
    lauf = subprocess.run(
        [sys.executable, str(REPO / "tools" / "make_test_ifc.py"), str(ziel), "--raeume"],
        capture_output=True, text=True, timeout=120, check=False)
    assert lauf.returncode == 0, lauf.stderr
    assert len(entitaeten(ziel.read_text(encoding="utf-8"), "IFCSPACE")) == ANZAHL_RAEUME
    assert "--raeume" in FIXTURE.GEBRAUCH


def test_ein_tippfehler_erzeugt_weiterhin_keine_datei(tmp_path):
    """Rückwärtssicherung: Der neue Schalter darf die Schalterprüfung nicht aufweichen.

    ``--help`` schrieb einmal eine IFC namens ``--help`` ins Arbeitsverzeichnis. Wer die
    Filterliste erweitert, ohne die Prüfung mitzuziehen, holt das zurück.
    """
    lauf = subprocess.run(
        [sys.executable, str(REPO / "tools" / "make_test_ifc.py"),
         str(tmp_path / "x.ifc"), "--raume"],
        capture_output=True, text=True, timeout=120, check=False)
    assert lauf.returncode == 2
    assert not (tmp_path / "x.ifc").exists()
    assert not list(tmp_path.glob("--*"))


# ======================================================================================
# B · Die Naht — ohne venv, ohne Prozess
# ======================================================================================

def test_naht_ruft_das_fremde_venv_mit_dem_raeume_runner_auf(ifc_python_attrappe, tmp_path):
    """LGPL-Auflage 1: Der Runner läuft im eigenen venv, nicht im Produkt-Interpreter."""
    aufrufer = Aufrufer(Ergebnis(stdout=json.dumps({"status": "ok", "n_raeume": 0})))

    bericht = ifc_raeume(tmp_path / "b.ifc", _starte=aufrufer)

    assert aufrufer.kommando[0] == ifc_python_attrappe
    assert aufrufer.kommando[1] == str(seams.IFC_RAEUME_RUNNER)
    assert aufrufer.kommando[2] == str(tmp_path / "b.ifc")
    assert bericht["n_raeume"] == 0


def test_naht_nimmt_nicht_den_glb_runner(ifc_python_attrappe, tmp_path):
    """Gegenprobe: Zwei Runner im selben Verzeichnis sind eine Verwechslung mit Ansage."""
    aufrufer = Aufrufer()
    ifc_raeume(tmp_path / "b.ifc", _starte=aufrufer)
    assert str(seams.IFC_RUNNER) not in aufrufer.kommando


def test_naht_reicht_die_frist_durch(ifc_python_attrappe, tmp_path):
    """Ohne durchgereichte Frist liefe ein hängender Subprozess unbegrenzt weiter."""
    aufrufer = Aufrufer()
    ifc_raeume(tmp_path / "b.ifc", timeout=17, _starte=aufrufer)
    assert aufrufer.timeouts == [17]


def test_naht_meldet_rueckgabewert_ungleich_null(ifc_python_attrappe, tmp_path):
    """Ein gescheiterter Subprozess wird zum ``SeamError`` — kein stilles Weiterlaufen."""
    aufrufer = Aufrufer(Ergebnis(returncode=2, stderr="ifcopenshell: Datei nicht lesbar"))

    with pytest.raises(SeamError) as fehler:
        ifc_raeume(tmp_path / "b.ifc", _starte=aufrufer)

    assert "Code 2" in str(fehler.value)
    assert "nicht lesbar" in str(fehler.value), "Die Meldung des Runners muss durch"


def test_naht_zieht_die_diagnose_des_runners_dem_rauschen_der_bibliothek_vor(
        ifc_python_attrappe, tmp_path):
    """Der Runner meldet **auf stdout**, die fremde Bibliothek rauscht auf stderr.

    Gemessen am 22.08.2026: Bei einer Datei, die keine IFC ist, steht auf stdout
    ``"Unable to parse IFC SPF header"`` — und auf stderr ein ``KeyError`` aus einem
    Destruktor von ifcopenshell 0.8.5, der mit der Ursache nichts zu tun hat. Wer nur
    stderr zeigt, zeigt ausgerechnet das Rauschen und verschweigt die Diagnose.
    """
    aufrufer = Aufrufer(Ergebnis(
        returncode=1,
        stdout=json.dumps({"status": "error", "error": "Unable to parse IFC SPF header"}),
        stderr="KeyError: 705176704"))

    with pytest.raises(SeamError) as fehler:
        ifc_raeume(tmp_path / "b.ifc", _starte=aufrufer)

    meldung = str(fehler.value)
    assert "Unable to parse IFC SPF header" in meldung
    assert meldung.index("Unable to parse") < meldung.index("KeyError"), (
        "Die Diagnose gehört vor das Rauschen — wer zuerst liest, liest zuerst die Ursache")


def test_naht_meldet_nicht_json_ausgabe(ifc_python_attrappe, tmp_path):
    """Die Verständigung läuft über JSON — was das nicht ist, wird als Nahtfehler gemeldet."""
    with pytest.raises(SeamError, match="kein JSON"):
        ifc_raeume(tmp_path / "b.ifc",
                   _starte=Aufrufer(Ergebnis(stdout="Segmentation fault (core dumped)")))


def test_naht_meldet_leere_ausgabe(ifc_python_attrappe, tmp_path):
    """Auch ein stummer Runner ist ein Fehler: Ohne Report weiss der Aufrufer nichts."""
    with pytest.raises(SeamError, match="kein JSON"):
        ifc_raeume(tmp_path / "b.ifc", _starte=Aufrufer(Ergebnis(stdout="")))


def test_naht_startet_nichts_ohne_venv(monkeypatch, tmp_path):
    """Fehlt das ``.venv-ifc``, wird gar kein Prozess versucht — und schon gar nicht der eigene.

    Ein Rückfall auf ``sys.executable`` holte GPL-CGAL in den Produktprozess. Der
    ``verweigerer`` belegt, dass vor dem Start abgebrochen wurde.
    """
    monkeypatch.delenv("AIIMAGING_IFC_PYTHON", raising=False)
    monkeypatch.setattr(Path, "exists", lambda self: False)

    with pytest.raises(SeamError, match=".venv-ifc"):
        ifc_raeume(tmp_path / "b.ifc", _starte=verweigerer)


def test_runner_wird_vom_kern_nicht_importiert():
    """Die Naht kennt den Runner als **Pfad** — die einzige erlaubte Bezugnahme."""
    assert isinstance(seams.IFC_RAEUME_RUNNER, Path)
    assert seams.IFC_RAEUME_RUNNER.name == "ifc_raeume_runner.py"
    assert seams.IFC_RAEUME_RUNNER.exists()
    assert not [m for m in sys.modules if m.startswith("aiimaging.runners")]


# ======================================================================================
# C · Der echte Lauf durch das `.venv-ifc`
# ======================================================================================

@ohne_konverter
@pytest.mark.parametrize("schema, vorsatz", KOMBINATIONEN)
def test_echter_lauf_findet_beide_raeume(tmp_path, schema, vorsatz):
    """Der eigentliche Beleg: Schema und Einheit ändern die **Datei**, nicht die **Räume**.

    Alle vier Kombinationen müssen dieselben zwei Räume mit denselben Zahlen ergeben —
    in Metern, gleichgültig ob die Datei Meter oder Millimeter erklärt hat, und
    gleichgültig ob sie IFC4 oder IFC2X3 ist. Zehn von 40 echten Dateien waren IFC2X3,
    25 von 40 standen in Millimetern (`auf-20260818-08`).
    """
    ifc = erzeuge(tmp_path / "r.ifc", schema=schema, vorsatz=vorsatz)
    bericht = ifc_raeume(ifc)

    assert bericht["status"] == "ok"
    assert bericht["schema"] == schema
    assert bericht["n_raeume"] == ANZAHL_RAEUME
    assert bericht["n_mit_grundriss"] == ANZAHL_RAEUME
    assert bericht["n_ohne_grundriss"] == 0
    assert len(bericht["raeume"]) == ANZAHL_RAEUME

    nach_namen = {r["name"]: r for r in bericht["raeume"]}
    for soll in FIXTURE.RAEUME:
        ist = nach_namen[soll["name"]]
        assert ist["befund"] is None, ist["befund"]
        assert zyklisch_gleich(ist["grundriss_m"], welt_ring(soll)), (
            f"{soll['name']}: {ist['grundriss_m']} statt {welt_ring(soll)}")
        assert ist["flaeche_m2"] == pytest.approx(soll["flaeche"], abs=1e-6)
        assert ist["hoehe_m"] == pytest.approx(soll["hoehe"], abs=1e-6)
        assert ist["z_unten_m"] == pytest.approx(soll["z_unten"], abs=1e-6)
        assert ist["geschoss_name"] == "EG"
        assert ist["geschoss_global_id"]
        assert ist["umlaufsinn"] == "gegen_uhrzeigersinn"


@ohne_konverter
@pytest.mark.parametrize("schema, vorsatz", KOMBINATIONEN)
def test_echter_lauf_erklaert_die_einheit_der_datei(tmp_path, schema, vorsatz):
    """Was die Datei erklärt hat, gehört in den Bericht — sonst ist die Umrechnung unbelegt."""
    bericht = ifc_raeume(erzeuge(tmp_path / "r.ifc", schema=schema, vorsatz=vorsatz))
    einheit = bericht["einheit"]

    assert einheit["laengeneinheit"] == "METRE"
    assert einheit["vorsatz"] == vorsatz
    assert einheit["meter_je_einheit"] == (0.001 if vorsatz == "MILLI" else 1.0)
    assert bericht["masse_plausibel"] is True


@ohne_konverter
def test_die_hoehe_traegt_ihren_bezugspunkt_mit(tmp_path):
    """**Eine Zahl ohne Bezugspunkt ist in diesem Projekt keine Zahl.**

    Im Kopf von ``kameras.py`` steht, was diese Sorgfalt kostet, wenn sie fehlt: Eine
    Kamerahöhe „absolut" gemeint kam bei einem Bauwerk auf 400 m über Meer vierhundert
    Meter unter dem Erdgeschoss zu liegen. Darum muss jeder gemessene Raum sagen, **worauf**
    sich seine Höhe bezieht — und die Erklärung muss die drei Verwechslungen ausdrücklich
    benennen, gegen die sie gebaut ist.
    """
    bericht = ifc_raeume(erzeuge(tmp_path / "r.ifc"))
    raeume = bericht["raeume"]
    assert len(raeume) == ANZAHL_RAEUME

    for raum in raeume:
        assert raum["hoehe_bezug"] == "raumkoerper_ab_unterkante"
        erklaerung = raum["hoehe_begruendung"].lower()
        assert "z_unten_m" in erklaerung
        assert "lichte" in erklaerung and "geschosshöhe" in erklaerung
        assert "über meer" in erklaerung
    assert "über meer" in bericht["hoehe_bezug_erklaerung"].lower()


@ohne_konverter
def test_die_raumhoehe_ist_nicht_die_wandhoehe(tmp_path):
    """Die Verwechslung, die am nächsten liegt — und die dieser Fixture nicht passieren kann.

    Die Wände sind 3,00 m hoch, die Räume 2,70 m und 2,40 m. Ein Leser, der statt des
    Raumkörpers die Geschoss- oder Wandhöhe ausgäbe, käme auf 3,00 m und fiele hier durch.
    """
    bericht = ifc_raeume(erzeuge(tmp_path / "r.ifc"))
    hoehen = sorted(r["hoehe_m"] for r in bericht["raeume"])
    assert hoehen == [2.4, 2.7]
    assert WANDHOEHE_M not in hoehen


@ohne_konverter
def test_fehlende_felder_kommen_als_none_nicht_als_leerer_text(tmp_path):
    """``None`` heisst *nicht gemessen* — ``""`` hiesse *gemessen und leer*. Nicht dasselbe."""
    bericht = ifc_raeume(erzeuge(tmp_path / "r.ifc"))
    nach_namen = {r["name"]: r for r in bericht["raeume"]}

    assert nach_namen["Raum-Nord"]["lang_name"] == "Aufenthalt Nord"
    assert nach_namen["Raum-Sued"]["lang_name"] is None


@ohne_konverter
def test_beide_profilarten_werden_gelesen_und_benannt(tmp_path):
    """Punktzug und Rechteck — beide kommen in echten Dateien vor, beide müssen gehen.

    Und der Bericht sagt, **welcher** Weg es war. Der Rechteck-Fall ist der schärfere:
    Seine Ecken stehen nirgends in der Datei, sie entstehen erst aus Breite, Tiefe und
    zwei Platzierungen.
    """
    bericht = ifc_raeume(erzeuge(tmp_path / "r.ifc"))
    quellen = {r["name"]: r["grundriss_quelle"] for r in bericht["raeume"]}

    assert quellen["Raum-Nord"] == "IfcArbitraryClosedProfileDef/IfcPolyline"
    assert quellen["Raum-Sued"] == "IfcRectangleProfileDef"


@ohne_konverter
def test_der_geschlossene_punktzug_erzeugt_keine_kante_der_laenge_null(tmp_path):
    """``IfcPolyline`` wiederholt den ersten Punkt am Ende — das gehört zur Schreibweise.

    Bliebe er stehen, hätte jeder Raum eine Kante der Länge null. In jeder späteren
    Auswertung — Punkt-in-Polygon, Sichtprüfung — ist die ein Sonderfall, den niemand
    behandelt.
    """
    bericht = ifc_raeume(erzeuge(tmp_path / "r.ifc"))
    nord = next(r for r in bericht["raeume"] if r["name"] == "Raum-Nord")

    assert len(nord["grundriss_m"]) == len(FIXTURE.RAEUME[0]["ring_relativ"])
    assert nord["grundriss_m"][0] != nord["grundriss_m"][-1]


@ohne_konverter
def test_eine_datei_ohne_raeume_ist_kein_fehler_sondern_ein_befund(tmp_path):
    """Die meisten IFC-Dateien tragen gar keine ``IfcSpace``.

    Daraus einen Fehlerstatus zu machen hiesse, einer gültigen Datei die Schuld für eine
    leere Antwort zu geben. Der Bericht sagt darum ``ok`` — und **nennt** es trotzdem,
    damit niemand die Null für ein Ergebnis hält.
    """
    ifc = erzeuge(tmp_path / "leer.ifc", mit_raeumen=False)
    bericht = ifc_raeume(ifc)

    assert bericht["status"] == "ok"
    assert bericht["n_raeume"] == 0
    assert bericht["raeume"] == []
    assert any("IfcSpace" in w for w in bericht["warnungen"])
    assert bericht["masse_plausibel"] is None, "nichts gemessen ist kein Urteil"


@ohne_konverter
def test_eine_datei_die_keine_ifc_ist_wird_zum_seamerror(tmp_path):
    """Der Runner meldet den Fehler als Report, die Naht macht daraus eine Ausnahme."""
    kaputt = tmp_path / "keine.ifc"
    kaputt.write_text("Das ist keine IFC-Datei.\n", encoding="utf-8")

    with pytest.raises(SeamError) as fehler:
        ifc_raeume(kaputt)

    # Und die Meldung nennt die Ursache, nicht bloss den Rückgabewert. Genau hier kommt
    # das Rauschen aus dem ifcopenshell-Destruktor durch — es darf die Diagnose nicht
    # verdrängen.
    assert "header" in str(fehler.value).lower()


# ======================================================================================
# D · Was der Runner NICHT kann — und wie er es sagt
#
# Ein stilles Weglassen wäre der schlimmste Ausgang: Der Aufrufer sähe drei Räume und
# hielte sie für alle. Jede der drei Operationen unten nimmt der Fixture etwas weg, das
# der Runner braucht — und jedes Mal muss der Raum **trotzdem in der Liste stehen**.
# ======================================================================================

def _kaputte_datei(tmp_path, operation, name="Raum-Sued") -> Path:
    """Die Fixture erzeugen, an **einem** Raum etwas wegnehmen und die Datei zurückgeben."""
    text = erzeuge(tmp_path / "r.ifc").read_text(encoding="utf-8")
    ziel = tmp_path / "kaputt.ifc"
    ziel.write_text(operation(text, name), encoding="utf-8")
    return ziel


@ohne_konverter
@pytest.mark.parametrize("operation, erwarteter_code", [
    (ohne_geometrie, "keine_repraesentation"),
    (mit_kreisprofil, "profil_nicht_polygonal"),
])
def test_ein_raum_ohne_lesbaren_grundriss_verschwindet_nicht(tmp_path, operation,
                                                             erwarteter_code):
    """Er steht in der Liste, sein Grundriss ist ``None``, und ein Befund sagt warum.

    Geprüft wird an **einem** der beiden Räume — der andere muss unversehrt durchkommen.
    Das ist die zweite Hälfte der Zusicherung: Ein Leser, der beim ersten Problem alles
    hinwirft, wäre genauso unbrauchbar wie einer, der schweigt.
    """
    bericht = ifc_raeume(_kaputte_datei(tmp_path, operation))

    assert bericht["n_raeume"] == ANZAHL_RAEUME, "der Raum wurde weggelassen"
    assert bericht["n_mit_grundriss"] == 1
    assert bericht["n_ohne_grundriss"] == 1

    nach_namen = {r["name"]: r for r in bericht["raeume"]}
    kaputt = nach_namen["Raum-Sued"]
    assert kaputt["grundriss_m"] is None
    assert kaputt["flaeche_m2"] is None, "None heisst nicht gemessen, nicht 0"
    assert kaputt["hoehe_m"] is None
    assert kaputt["hoehe_bezug"] is None, "ohne Höhe darf kein Bezugspunkt behauptet werden"
    assert kaputt["befund"]["code"] == erwarteter_code
    assert kaputt["hoehe_befund"]["code"] == "hoehe_ohne_grundriss"
    assert len(kaputt["befund"]["text"]) > 40, "ein Befund ohne Satz hilft niemandem"

    heil = nach_namen["Raum-Nord"]
    assert heil["befund"] is None
    assert heil["grundriss_m"] and heil["hoehe_m"] == pytest.approx(2.7)


@ohne_konverter
def test_eine_schiefe_extrusion_kostet_die_hoehe_und_nicht_den_grundriss(tmp_path):
    """Zwei Messungen, zwei Urteile — der Fall, der diese Trennung erzwungen hat.

    Bei einer schiefen Extrusion steht der Umriss des Fussbodens einwandfrei in der Datei;
    er ist das Profil, und das hängt nicht an der Richtung. Weg ist nur der Bezugspunkt
    der Höhe: Der Körper schert über dem Boden weg. Wer hier den Grundriss mitwegwirft,
    wirft eine gültige Messung weg — wer eine Höhe liefert, erfindet sie.
    """
    bericht = ifc_raeume(_kaputte_datei(tmp_path, mit_schiefer_extrusion))

    assert bericht["n_raeume"] == ANZAHL_RAEUME
    assert bericht["n_mit_grundriss"] == ANZAHL_RAEUME, "der Fussbodenumriss bleibt gültig"
    assert bericht["n_mit_hoehe"] == 1
    assert bericht["n_ohne_hoehe"] == 1

    schief = next(r for r in bericht["raeume"] if r["name"] == "Raum-Sued")
    assert schief["befund"] is None
    assert zyklisch_gleich(schief["grundriss_m"], welt_ring(FIXTURE.RAEUME[1]))
    assert schief["hoehe_m"] is None
    assert schief["z_unten_m"] is None
    assert schief["hoehe_bezug"] is None
    assert schief["hoehe_befund"]["code"] == "extrusion_nicht_senkrecht"


@ohne_konverter
def test_der_schiefe_raum_behaelt_seine_kennung_und_sein_geschoss(tmp_path):
    """Was gemessen werden konnte, bleibt gemessen — auch wenn der Rest scheitert.

    Kennung, Name und Geschoss hängen nicht an der Geometrie. Sie mit der Höhe zusammen
    wegzuwerfen wäre der bequeme Weg und der falsche: Der Aufrufer wüsste dann nicht
    einmal mehr, **welcher** Raum ihm fehlt.
    """
    ziel = _kaputte_datei(tmp_path, mit_schiefer_extrusion)
    kaputt = next(r for r in ifc_raeume(ziel)["raeume"] if r["name"] == "Raum-Sued")

    assert kaputt["global_id"]
    assert kaputt["geschoss_name"] == "EG"
    assert kaputt["hoehe_begruendung"], "auch das Nicht-Messen braucht eine Begründung"


@ohne_konverter
def test_die_beiden_urteile_stimmen_mit_den_beiden_zaehlern_ueberein(tmp_path):
    """Die Zusicherung als Test: ``grundriss_m is None`` **genau dann**, wenn ``befund`` steht.

    Ohne diese Prüfung könnte ein Bericht einen Grundriss liefern *und* einen Befund
    dazu — und niemand wüsste, welchem von beiden zu glauben ist.
    """
    for datei in (erzeuge(tmp_path / "heil.ifc"),
                  _kaputte_datei(tmp_path, mit_kreisprofil),
                  _kaputte_datei(tmp_path, mit_schiefer_extrusion)):
        bericht = ifc_raeume(datei)
        assert bericht["raeume"], f"{datei.name}: keine Räume — der Test prüfte nichts"
        for raum in bericht["raeume"]:
            assert (raum["grundriss_m"] is None) == (raum["befund"] is not None), raum
            assert (raum["hoehe_m"] is None) == (raum["hoehe_befund"] is not None), raum
        assert bericht["n_mit_grundriss"] == sum(
            1 for r in bericht["raeume"] if r["grundriss_m"] is not None)
        assert bericht["n_mit_hoehe"] == sum(
            1 for r in bericht["raeume"] if r["hoehe_m"] is not None)


@ohne_konverter
def test_ein_kaputter_export_wird_benannt_statt_geglaettet(tmp_path):
    """Millimeter erklärt, Meterzahlen getragen — das ist keine gültige Eingabe.

    Zwei von 40 echten Dateien waren so (`auf-20260818-08`). Der Bericht darf das nicht
    glätten: Er muss ``masse_plausibel = False`` sagen **und** den Faktor nennen, der die
    Abweichung erklärt. Ein blosses „unplausibel" kostet jedes Mal einen Menschen, der
    nachsieht; eine Diagnose sagt ihm, wo.
    """
    meter = erzeuge(tmp_path / "m.ifc").read_text(encoding="utf-8")
    assert EINHEIT_METER in meter, "die Fixture hat ihre Einheitenzeile geändert"
    ziel = tmp_path / "kaputt.ifc"
    ziel.write_text(meter.replace(EINHEIT_METER, EINHEIT_MILLI), encoding="utf-8")

    bericht = ifc_raeume(ziel)

    assert bericht["einheit"]["meter_je_einheit"] == 0.001
    assert bericht["masse_plausibel"] is False
    assert "KAPUTTER EXPORT" in bericht["masse_befund"]
    assert "0.001" in bericht["masse_befund"]
    # Die Räume selbst werden trotzdem gemeldet — mit den winzigen Zahlen, die
    # herauskommen. Sie stillschweigend hochzuskalieren hiesse, den Export zu reparieren,
    # von dem wir gerade sagen, dass er kaputt ist.
    nord = next(r for r in bericht["raeume"] if r["name"] == "Raum-Nord")
    assert nord["hoehe_m"] == pytest.approx(0.0027, abs=1e-9)


@ohne_konverter
def test_der_kaputte_export_faellt_ohne_die_gegenprobe_gar_nicht_auf(tmp_path):
    """Gegenprobe zur Gegenprobe: Die gesunde Datei muss ``masse_plausibel = True`` ergeben.

    Ohne diesen Test bliebe der vorige auch dann grün, wenn ``masse_plausibel`` immer
    ``False`` wäre — und eine Prüfung, die alles beanstandet, prüft nichts.
    """
    bericht = ifc_raeume(erzeuge(tmp_path / "gesund.ifc", vorsatz="MILLI"))

    assert bericht["masse_plausibel"] is True
    assert "KAPUTTER EXPORT" not in bericht["masse_befund"]
