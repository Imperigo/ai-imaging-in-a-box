"""Was aus einer IFC NICHT in die glb gehört — und dass es gezählt wird.

**Der Anlass kam vom Gerät und stand nicht im Auftrag** (`auf-20260822-32`, 21.08.2026):
Die aus `make_test_ifc.py --raeume` erzeugte glb trägt sieben Meshes — ein `IfcSlab`,
vier `IfcWall` und **zwei `IfcSpace`**. Der Verdeckungstest stiess darauf, weil sein
getroffenes Objekt in einem Raum nicht die Wand war, sondern der Raumkörper selbst.

Ein `IfcSpace` ist Luft. Als Mesh ist es ein **massiver Quader**, und eine Innenaufnahme
steht mitten darin: Die Tiefenkarte sähe eine graue Fläche unmittelbar vor dem Objektiv,
in jedem Raum, in dem je gerendert wird. Aufgefallen wäre das erst beim ersten
Innenraum-Render — und dann als „das Bildmodell liefert Grau".

Geprüft wird hier **ohne `ifcopenshell`**: Die Auswahl ist eine Liste von Typnamen und
eine reine Funktion darüber. Das ist Absicht — dieses Environment hat kein `.venv-ifc`,
und eine Regel, die sich nur dort prüfen lässt, wo die Bibliothek liegt, wird nie geprüft.
"""
import importlib.util
from pathlib import Path

import pytest

RUNNER = (Path(__file__).resolve().parents[1]
          / "src" / "aiimaging" / "runners" / "ifc_to_glb_runner.py")


def _runner():
    """Den Runner als Datei laden — **nicht** als `aiimaging`-Modul.

    Ein `import aiimaging.runners.ifc_to_glb_runner` wäre der Anfang genau des Weges,
    den `tests/test_prozessgrenze.py` verbietet. Der Ladeweg über den Dateipfad hält die
    Prozessgrenze ein: Er zieht `ifcopenshell` nicht mit, weil dessen Import in der
    Funktion steht und nicht im Modulkopf.
    """
    spez = importlib.util.spec_from_file_location("ifc_glb_pruefling", RUNNER)
    modul = importlib.util.module_from_spec(spez)
    spez.loader.exec_module(modul)
    return modul


def test_der_runner_laedt_ohne_ifcopenshell():
    """Die Voraussetzung dieser ganzen Datei — und zugleich eine Aussage über den Aufbau."""
    with pytest.raises(ImportError):
        import ifcopenshell  # noqa: F401
    assert _runner().NICHT_GEBAUTE_SUBSTANZ


def test_raeume_und_ausschnitte_sind_keine_gebaute_substanz():
    ist = _runner().ist_gebaute_substanz
    assert ist("IfcSpace") is False
    assert ist("IfcOpeningElement") is False


def test_waende_boeden_und_daecher_bleiben_drin():
    """Die Gegenprobe. Eine Liste, die zu viel ausschliesst, ist schlimmer als keine —
    sie löscht das Bauwerk und sieht dabei sorgfältig aus."""
    ist = _runner().ist_gebaute_substanz
    for typ in ("IfcWall", "IfcWallStandardCase", "IfcSlab", "IfcRoof", "IfcColumn",
                "IfcBeam", "IfcWindow", "IfcDoor", "IfcStair", "IfcRailing",
                "IfcCovering", "IfcCurtainWall", "IfcMember", "IfcPlate",
                "IfcBuildingElementProxy"):
        assert ist(typ) is True, typ


def test_fenster_und_tueren_bleiben_der_ausschnitt_geht():
    """Der Unterschied, an dem sich alles entscheidet.

    `IfcWindow` ist das Bauteil — Rahmen und Glas, es gehört ins Bild. Der
    `IfcOpeningElement` daneben ist das **Loch**, das aus der Wand geschnitten wurde. Wer
    ihn mitnimmt, mauert jedes Fenster wieder zu, und zwar mit einem Körper, der genau
    die Fensterform hat.
    """
    ist = _runner().ist_gebaute_substanz
    assert ist("IfcWindow") is True and ist("IfcDoor") is True
    assert ist("IfcOpeningElement") is False


def test_die_liste_bleibt_klein_und_begruendet():
    """Jeder Eintrag braucht seinen eigenen Grund im Docstring — eine Sammelbegründung
    lädt zum Weiterwachsen ein, und eine wachsende Ausschlussliste löscht irgendwann
    etwas Gebautes."""
    modul = _runner()
    assert len(modul.NICHT_GEBAUTE_SUBSTANZ) <= 6
    quelle = RUNNER.read_text(encoding="utf-8")
    for typ in modul.NICHT_GEBAUTE_SUBSTANZ:
        assert quelle.count(typ) >= 2, (
            f"{typ} steht in der Liste, aber nirgends mit einer Begründung daneben"
        )


def test_kein_typ_steht_doppelt():
    liste = _runner().NICHT_GEBAUTE_SUBSTANZ
    assert len(set(liste)) == len(liste)


def test_ein_aufzug_ist_gebaute_substanz_und_bleibt_drin():
    """Ein Befund aus der Lesermessung vom 24.08.2026, an unserem Runner bestätigt.

    In `zug_kosmodraw_gebaeude.ifc` steht ein `IfcTransportElement` — ein **Aufzug**. Der
    fremde Klassifikator kennt den Typ nicht und legt ihn nach «Unbekannt»; wer
    stromabwärts auf die Klasse filtert, verliert ihn. Unser Runner behält ihn, und das ist
    richtig: Ein Aufzug ist gebaute Substanz und gehört ins Bild.

    Aus derselben Datei ebenfalls belegt: 132 `IfcStairFlight`.
    """
    modul = _runner()

    assert modul.ist_gebaute_substanz("IfcTransportElement") is True
    assert modul.ist_gebaute_substanz("IfcStairFlight") is True
    assert modul.ist_gebaute_substanz("IfcSpace") is False, (
        "die Gegenprobe — sonst hiesse der Test nur, dass alles durchgeht")
