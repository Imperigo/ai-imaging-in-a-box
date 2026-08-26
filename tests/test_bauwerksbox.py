"""Die Kamera soll die Hüllbox des BAUWERKS rahmen, nicht die der ganzen Szene.

**Der grösste gemessene Fehler dieser Woche** (HomeStation, `auf-13`/`auf-35`, 24.08.2026):
Ein Quader auf einer Platte mit zehnfacher Grundfläche füllt bei `cameras: auto` **1,9 %**
des Bildes, und das Geometrie-Tor kann rechnerisch nicht bestehen. Bei 70 % Bildbreite
entsteht dagegen ein Score von 0,9599.

*Die Kamera rahmt die Szene, gemessen wird das Bauwerk — das ist der Bruch.*

**Ohne eine zweite Hüllbox ist er nicht einmal feststellbar.** Der Runner kennt die
IFC-Klasse jedes Bauteils — er schreibt sie in den Knotennamen —, führte aber nur *eine*
Box. Diese Datei prüft die zweite: die der gebauten Substanz, ohne Gelände.

**Regel 2:** Der Runner wird über den **Dateipfad** geladen, nicht als `aiimaging`-Modul —
derselbe Weg wie in `test_ifc_glb_filter.py`. Ein `import aiimaging.runners…` wäre der
Anfang genau des Weges, den `test_prozessgrenze.py` verbietet.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

from aiimaging import maske

RUNNER = (Path(__file__).resolve().parents[1]
          / "src" / "aiimaging" / "runners" / "ifc_to_glb_runner.py")


def _runner():
    spez = importlib.util.spec_from_file_location("ifc_bauwerksbox_pruefling", RUNNER)
    modul = importlib.util.module_from_spec(spez)
    spez.loader.exec_module(modul)
    return modul


# --------------------------------------------------------------------------------------
# 1 · Die Geländeregel — an zwei Stellen, und darum geprüft
# --------------------------------------------------------------------------------------

def test_der_runner_kennt_ifcsite_als_gelaende():
    modul = _runner()

    assert modul.ist_gelaende_typ("IfcSite") is True
    assert modul.ist_gelaende_typ("IfcWall") is False
    assert modul.ist_gelaende_typ("IfcSlab") is False, (
        "eine Bodenplatte ist gebaute Substanz und kein Gelaende — der Unterschied ist "
        "genau der, um den es hier geht")


def test_die_beiden_gelaenderegeln_passen_zusammen():
    """**Der Test ersetzt den Import, den es nicht geben darf.**

    Der Runner läuft im `.venv-ifc` und darf sich nicht darauf verlassen, das Produkt-Paket
    zu erreichen (Regel 2). Also steht die Liste an zwei Stellen — und eine Zahl an zwei
    Stellen ist an einer davon bereits falsch, sobald sie auseinanderlaufen.

    Geprüft wird nicht Gleichheit, sondern **Verträglichkeit**: Was der Runner als Gelände
    aussortiert, muss die Maskenregel ebenfalls als Gelände erkennen. Die Maskenregel darf
    mehr kennen — sie sieht Materialnamen, nicht IFC-Klassen.
    """
    modul = _runner()

    for typ in modul.GELAENDE_TYPEN:
        knotenname = f"{typ}_1a2b3c"
        assert maske.ist_gelaende(knotenname, maske.GELAENDE_MUSTER), (
            f"{typ!r} sortiert der Runner als Gelaende aus, die Maskenregel erkennt es "
            f"aber nicht — dann steckt es spaeter doch im Bauwerk")


def test_ein_bauteil_ist_nicht_zugleich_gelaende_und_uebersprungen():
    """Die beiden Listen des Runners beantworten verschiedene Fragen und dürfen sich
    nicht überschneiden.

    `NICHT_GEBAUTE_SUBSTANZ` fliegt ganz raus (Luft, Ausschnitte). `GELAENDE_TYPEN` bleibt
    in der glb — es soll gerendert werden, nur nicht gerahmt.
    """
    modul = _runner()

    assert not set(modul.GELAENDE_TYPEN) & set(modul.NICHT_GEBAUTE_SUBSTANZ)
    for typ in modul.GELAENDE_TYPEN:
        assert modul.ist_gebaute_substanz(typ) is True, (
            "Gelaende bleibt in der glb — es wird gerendert, nur nicht gerahmt")


# --------------------------------------------------------------------------------------
# 2 · Die zweite Box wird berichtet — und nicht durch die erste ersetzt
# --------------------------------------------------------------------------------------

def test_der_bericht_fuehrt_beide_boxen_getrennt():
    """`bbox_bauwerk` darf **nie** stillschweigend die Szenenbox sein.

    Das wäre genau die Verwechslung, gegen die das Feld gebaut ist — und sie fiele
    niemandem auf, weil beide Felder dann plausible Zahlen trügen.
    """
    quelle = RUNNER.read_text(encoding="utf-8")

    assert '"bbox_bauwerk"' in quelle
    assert "None if bau_min is None" in quelle, (
        "ohne gebaute Substanz gehoert dort None — kein Rueckfall auf die Szenenbox")
    assert "bbox_bauwerk_note" in quelle, (
        "das Feld braucht seinen Bezugsrahmen dabei; 'bbox' hat seinen auch")


def test_die_zweite_box_haengt_an_der_gelaenderegel_und_nicht_am_zufall():
    quelle = RUNNER.read_text(encoding="utf-8")

    assert "if not ist_gelaende_typ(produkt.is_a()):" in quelle


def test_der_runner_laedt_weiterhin_ohne_ifcopenshell():
    """Die Ergänzung darf die Ladbarkeit nicht kosten.

    Dieses Environment hat kein `.venv-ifc`; eine Regel, die sich nur dort prüfen lässt,
    wo die Bibliothek liegt, wird nie geprüft.
    """
    modul = _runner()

    assert callable(modul.ist_gelaende_typ)
    assert callable(modul.ist_gebaute_substanz)


# --------------------------------------------------------------------------------------
# 3 · Der Name muss den Export überleben — gemessen am 26.08.2026
# --------------------------------------------------------------------------------------
#
# Der Befund in einem Satz: Die Geländeplatte unserer Testgeometrie ist ein `IfcSlab`
# namens `Gelaende`. Der Typfilter fasst sie nicht (die `IfcSite` selbst trägt keine
# Geometrie), und die Namensregel drüben konnte sie nicht fassen, weil der Knotenname
# `IfcSlab_<guid>` lautete — der IFC-Name war weg. **Beide Filter blind, jeder aus einem
# anderen Grund.**
#
# Gemessen an `build/mit_gelaende.ifc`: `bbox_bauwerk` war 20 × 20 m statt 8 × 5 m, der
# Breitenanteil 1.0 statt 0.40 und die wirksame Bildbreite 0.70 statt 0.28. Der
# Rahmungsriegel war damit auf genau dem Fall wirkungslos, für den er gebaut ist.

class _Produkt:
    """Das Wenige, was `_knotenname` von einem IFC-Produkt liest."""

    def __init__(self, typ, name, guid):
        self._typ, self.Name, self.GlobalId = typ, name, guid

    def is_a(self):
        return self._typ


def test_der_knotenname_traegt_den_ifc_namen():
    modul = _runner()

    name = modul._knotenname(_Produkt("IfcSlab", "Gelaende", "2eYuY4S81HqRN8GZ4SZVcP"))

    assert name.startswith("IfcSlab_Gelaende_")
    assert maske.ist_gelaende(name) is True, (
        "Der Knotenname ist die EINZIGE Auskunft, die den glb-Export überlebt. Wenn die "
        "Geländeregel ihn nicht mehr fassen kann, ist die Bauwerksbox gleich der "
        "Szenenbox — und der Rahmungsriegel sieht einen Breitenanteil von 1.0.")


def test_der_alte_knotenname_wurde_von_der_regel_nicht_gefasst():
    """Die Gegenprobe. **Ohne sie zeigte der Test oben nur, dass irgendein Name passt.**

    Genau diese Form stand bis zum 26.08.2026 im Runner.
    """
    assert maske.ist_gelaende("IfcSlab_2eYuY4S81HqRN8GZ4SZVcP") is False


def test_ohne_namen_bleibt_die_alte_form():
    """Ein Produkt ohne Namen kann nichts überliefern — dann ist die kurze Form richtig."""
    modul = _runner()

    for leer in (None, "", "   "):
        assert modul._knotenname(_Produkt("IfcWall", leer, "abc")) == "IfcWall_abc"


def test_der_name_steht_vor_der_globalid():
    """**Blender kürzt Objektnamen bei 63 Byte.**

    Stünde der Name hinten, fiele er dort weg — und mit ihm die einzige Auskunft, die den
    Export überlebt. Was überläuft, ist die GlobalId; die braucht drüben niemand.
    """
    modul = _runner()
    lang = "Gelaende " + "x" * 200

    name = modul._knotenname(_Produkt("IfcSlab", lang, "2eYuY4S81HqRN8GZ4SZVcP"))

    assert name.index("Gelaende") < name.index("2eYuY4S8")
    assert len(name) <= 63, f"{len(name)} Byte — Blender würde kürzen: {name!r}"
    assert maske.ist_gelaende(name) is True


def test_leerzeichen_werden_zu_unterstrichen():
    """Ein Objektname mit Leerzeichen ist in Blender unhandlich — die Regel greift trotzdem."""
    modul = _runner()

    name = modul._knotenname(_Produkt("IfcSlab", "Gelaende Nord", "abc"))

    assert " " not in name
    assert maske.ist_gelaende(name) is True


def test_ein_gelaender_ist_kein_gelaende():
    """Die Wortgrenzen tragen auch in der neuen Form.

    *Sonst hätte der Anschluss des Namens ein Loch in die andere Richtung gerissen:* Ein
    Geländer, ein Bodenplatte, ein Geländemodell — keines davon ist Gelände.
    """
    modul = _runner()

    for typ, name in (("IfcRailing", "Gelaender"), ("IfcSlab", "Bodenplatte"),
                      ("IfcWall", "Wand-Sued")):
        knoten = modul._knotenname(_Produkt(typ, name, "abc"))
        assert maske.ist_gelaende(knoten) is False, knoten


# --------------------------------------------------------------------------------------
# 4 · Und einmal durch die ganze Kette — der Test, der den Befund gefunden hätte
# --------------------------------------------------------------------------------------

def _ifc_fehlt() -> bool:
    from aiimaging import seams
    try:
        return not Path(seams.finde_ifc_python()).exists()
    except Exception:                                  # noqa: BLE001
        return True


def _blender_fehlt() -> bool:
    import shutil
    return not shutil.which("blender") and not Path("/opt/blender/blender").exists()


@pytest.mark.skipif(_ifc_fehlt() or _blender_fehlt(),
                    reason=".venv-ifc oder Blender fehlt")
def test_die_bauwerksbox_trennt_das_gelaende_wirklich_ab(tmp_path):
    """IFC → glb → Blender, mit Gelände. **Die Probe, die den Befund gefunden hätte.**

    Bis zum 26.08.2026 kam hier ``bbox_bauwerk == bbox`` heraus (20 × 20 m), weil der
    IFC-Name den Export nicht überlebte. Kein einziger Test lief über diesen Weg — die
    Bauwerksbox war an Attrappen geprüft, an denen die Namen stimmten.

    *Eine Attrappe, die den Fehler nicht kennt, kann ihn auch nicht finden.*
    """
    import subprocess
    from aiimaging.seams import ifc_zu_glb, glb_zu_multipass

    ifc = tmp_path / "mit_gelaende.ifc"
    subprocess.run([sys.executable, "tools/make_test_ifc.py", str(ifc), "--gelaende"],
                   check=True, capture_output=True,
                   cwd=Path(__file__).resolve().parents[1])

    glb = tmp_path / "g.glb"
    assert ifc_zu_glb(ifc, glb)["status"] == "ok"

    bericht = glb_zu_multipass(glb, tmp_path / "out", up_axis="Y", kamera="sSE",
                               aufloesung=128, samples=1, timeout=900)
    assert bericht["status"] == "ok", bericht.get("error")

    szene = bericht["bbox"]
    bau = bericht.get("bbox_bauwerk")
    assert bau is not None, f"Keine Bauwerksbox: {bericht.get('bbox_bauwerk_note')}"

    breit_szene = max(szene[1][0] - szene[0][0], szene[1][1] - szene[0][1])
    breit_bau = max(bau[1][0] - bau[0][0], bau[1][1] - bau[0][1])

    assert breit_szene > 15.0, "Die Geländeplatte fehlt — dann prüft dieser Test nichts."
    assert breit_bau < 10.0, (
        f"Die Bauwerksbox ist {breit_bau:.1f} m breit und damit so gross wie die Szene "
        f"({breit_szene:.1f} m). Das Gelände ist nicht abgetrennt — genau der Zustand vom "
        f"26.08.2026, in dem der Rahmungsriegel einen Breitenanteil von 1.0 sah.")


@pytest.mark.skipif(_ifc_fehlt() or _blender_fehlt(),
                    reason=".venv-ifc oder Blender fehlt")
def test_der_rahmungsriegel_greift_bei_einem_bauwerk_auf_einem_grundstueck(tmp_path):
    """Und das Urteil, auf das es ankommt.

    Gemessen: Breitenanteil **0,40**, wirksame Bildbreite **0,28** — weit unter der
    Abbruchschwelle 0,65. Die HomeStation hat für 30 % Bildbreite einen Score von
    **0,0** gemessen (`auf-vis-20260825-15`, Posten 1).
    """
    import subprocess
    from aiimaging import abholer
    from aiimaging.seams import ifc_zu_glb, glb_zu_multipass

    ifc = tmp_path / "mit_gelaende.ifc"
    subprocess.run([sys.executable, "tools/make_test_ifc.py", str(ifc), "--gelaende"],
                   check=True, capture_output=True,
                   cwd=Path(__file__).resolve().parents[1])
    glb = tmp_path / "g.glb"
    ifc_zu_glb(ifc, glb)
    bericht = glb_zu_multipass(glb, tmp_path / "out", up_axis="Y", kamera="sSE",
                               aufloesung=128, samples=1, timeout=900)

    lage = abholer._rahmung_vor_dem_render(bericht)

    assert lage["breitenanteil"] < 0.6, (
        f"Breitenanteil {lage['breitenanteil']:.3f} — das Bauwerk füllt die Szene, also "
        f"ist das Gelände wieder mitgezählt.")
    assert lage["abbruch"] is True, (
        f"wirksame Bildbreite {lage['wirksame_bildbreite']:.3f}, Abbruch "
        f"{lage['abbruch']}. Ein Bauwerk auf einem Grundstück ist der Fall, für den "
        f"dieser Riegel gebaut wurde.")


@pytest.mark.skipif(_ifc_fehlt(), reason=".venv-ifc fehlt")
def test_der_torwaechter_an_der_echten_huellbox_dieser_kette(tmp_path):
    """**M0 aus `auf-20260826-45`, hier gerechnet statt beauftragt.**

    Der Auftrag verlangt die Gegenprobe *«zuerst, an synthetischer Geometrie»*: dieselbe
    Hüllbox einmal wie erzeugt, einmal mal 1000, einmal geteilt durch 1000. *«Schlägt das
    nicht an, ist der Torwächter kaputt und alles Weitere wertlos.»*

    Sie braucht keine GPU — nur `.venv-ifc`, und das liegt hier. Gemessen am 26.08.2026:

    ===============  ==============  ====================  =================
    Fall             grösste Kante   Entscheidung          ``verdacht_faktor``
    ===============  ==============  ====================  =================
    wie erzeugt      8,0 m           ``annehmen``          ``None``
    mal 1000         8000,0 m        ``ablehnen_massstab`` 1000,0
    geteilt 1000     0,008 m         ``ablehnen_massstab`` 0,001
    ===============  ==============  ====================  =================

    Was der HomeStation bleibt, ist M1 bis M4: **die Häufigkeit am echten Bestand.** Die
    kann hier niemand messen — echte Dateien liegen nach Regel 3 nicht in diesem Repo.

    *Der Unterschied ist der ganze Sinn der Zweiteilung:* Was ohne ihre Daten und ohne ihre
    Karte geht, gehört hierher und nicht in einen Auftrag.
    """
    import subprocess
    from aiimaging import torwaechter
    from aiimaging.seams import ifc_zu_glb

    ifc = tmp_path / "t.ifc"
    subprocess.run([sys.executable, "tools/make_test_ifc.py", str(ifc)],
                   check=True, capture_output=True,
                   cwd=Path(__file__).resolve().parents[1])
    bericht = ifc_zu_glb(ifc, tmp_path / "t.glb")
    assert bericht["status"] == "ok", bericht.get("error")
    bbox = bericht["bbox"]

    def _skaliert(faktor):
        return [[v * faktor for v in bbox[0]], [v * faktor for v in bbox[1]]]

    wie_erzeugt = torwaechter.torwaechter({"status": "ok", "bbox": bbox})
    assert wie_erzeugt["entscheidung"] == "annehmen", (
        f"Die selbst erzeugte Geometrie wird abgelehnt: {wie_erzeugt}")

    zu_gross = torwaechter.torwaechter({"status": "ok", "bbox": _skaliert(1000.0)})
    assert zu_gross["entscheidung"] == "ablehnen_massstab"
    assert zu_gross["massstab"]["verdacht_faktor"] == 1000.0

    zu_klein = torwaechter.torwaechter({"status": "ok", "bbox": _skaliert(0.001)})
    assert zu_klein["entscheidung"] == "ablehnen_massstab"
    assert zu_klein["massstab"]["verdacht_faktor"] == 0.001
