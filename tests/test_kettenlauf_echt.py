"""Die ganze Kette mit **echtem Blender** — nur die Diffusion ist eine Attrappe.

Warum es diese Datei zusätzlich zu `test_kettenlauf_26august.py` gibt
---------------------------------------------------------------------
Jene Datei prüft dieselben acht Riegel an der Naht, mit Attrappen für Blender *und*
Diffusion. Ihr Docstring begründete das so:

    *«Ohne Attrappen liefe hier gar nichts — und ein Test, der nicht läuft, prüft nichts.»*

**Der Satz war falsch, und er ist am 26.08.2026 widerlegt worden:** `/opt/blender/blender`
und `.venv-ifc` liegen in diesem Container. Nur was ``torch`` braucht — die Diffusion und
der Tiefenschätzer — läuft hier nicht.

Und der Unterschied ist an genau diesem Tag teuer geworden. Die Bauwerksbox war seit dem
25.08. geprüft — an Attrappen, in denen die Objektnamen stimmten. Über die wirkliche Kette
lief kein einziger Test, und dort war sie **gleich der Szenenbox**, weil der IFC-Name den
glb-Export nicht überlebte. Der Rahmungsriegel sah einen Breitenanteil von 1,0, wo 0,4
richtig war.

    **Eine Attrappe, die den Fehler nicht kennt, kann ihn nicht finden.**

Was hier echt ist, und was nicht
--------------------------------
============================  ==================================================
IFC → glb                     **echt** (`.venv-ifc`, IfcOpenShell)
glb → Multipass               **echt** (Blender, Cycles)
Hüllboxen, Kamera, Sonne      **echt** — vom Runner gerechnet und gemeldet
Die acht Riegel               **echt**, auf echten Berichten
Diffusion                     Attrappe (braucht ``torch``)
Geometrie-QA                  Attrappe (der Tiefenschätzer braucht ``torch``)
============================  ==================================================

*Damit ist alles echt, was Geometrie ist* — und genau dort lagen die Befunde dieses Tages.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from aiimaging import abholer, bruecke
from conftest import MINI_PNG

WURZEL = Path(__file__).resolve().parents[1]


def _blender_fehlt() -> bool:
    return not shutil.which("blender") and not Path("/opt/blender/blender").exists()


def _ifc_fehlt() -> bool:
    from aiimaging import seams
    try:
        return not Path(seams.finde_ifc_python()).exists()
    except Exception:                                  # noqa: BLE001
        return True


ohne_kette = pytest.mark.skipif(
    _blender_fehlt() or _ifc_fehlt(), reason="Blender oder .venv-ifc fehlt")


def _echte_glb(tmp_path, *schalter) -> Path:
    """Eine wirklich erzeugte glb — kein `b"glTF\\x02\\x00\\x00\\x00"`."""
    from aiimaging.seams import ifc_zu_glb
    ifc = tmp_path / "bau.ifc"
    subprocess.run([sys.executable, "tools/make_test_ifc.py", str(ifc), *schalter],
                   check=True, capture_output=True, cwd=WURZEL)
    glb = tmp_path / "model.glb"
    bericht = ifc_zu_glb(ifc, glb)
    assert bericht["status"] == "ok", bericht.get("error")
    return glb


def _auftragsordner(tmp_path, glb: Path, *, sonne=None, kameras="auto") -> Path:
    ordner = tmp_path / "vis-1-abcdef"
    ordner.mkdir(parents=True)
    (ordner / bruecke.DATEI_LAUFZETTEL).write_text(json.dumps({
        "job_id": "vis-1-abcdef", "status": "queued",
        "approval_token": bruecke.TOKEN_VORSATZ + "deadbeef"}), encoding="utf-8")
    szene = {"geometry": {"path": str(ordner / bruecke.DATEI_MODELL), "format": "glb"},
             "cameras": kameras,
             # 256 x 256 statt der Vertragsvorgabe 1600 x 1000: Diese Datei prüft
             # Wege und Urteile, keine Bildinhalte. Bei voller Auflösung kostete sie
             # mehr Zeit als die ganze übrige Testsammlung — und ein Test, der so lange
             # läuft, wird abgeschaltet.
             "render": {"samples": 1, "faithful": 0.8, "resolution": [256, 256]},
             "style": {"prompt": "overcast sky, no people"},
             "vis": {}}
    if sonne is not None:
        szene["render"]["sun"] = sonne
    (ordner / bruecke.DATEI_SZENE).write_text(json.dumps(szene), encoding="utf-8")
    shutil.copy(glb, ordner / bruecke.DATEI_MODELL)
    return ordner


@pytest.fixture(scope="module")
def frei(tmp_path_factory):
    """Ein einziger echter Lauf ohne Gelände — für alle Tests des gesunden Falls.

    **Modulweit, nicht je Test.** Ein Durchgang ist IFC → glb → dreimal Blender; je Test
    zu wiederholen kostete die Testsammlung mehr als alles andere zusammen. Was danach
    geprüft wird, sind Dateien und Wörterbücher — die ändern sich nicht mehr.
    """
    if _blender_fehlt() or _ifc_fehlt():
        pytest.skip("Blender oder .venv-ifc fehlt")
    ordner_tmp = tmp_path_factory.mktemp("kette_frei")
    glb = _echte_glb(ordner_tmp)
    auftrag = _auftragsordner(ordner_tmp, glb, sonne={"elevation": 12, "azimuth": 60})
    return _lauf(ordner_tmp, auftrag)


@pytest.fixture(scope="module")
def auf_grundstueck(tmp_path_factory):
    """Derselbe Bau, aber auf einer Platte von 20 × 20 m — der Fall des Riegels."""
    if _blender_fehlt() or _ifc_fehlt():
        pytest.skip("Blender oder .venv-ifc fehlt")
    ordner_tmp = tmp_path_factory.mktemp("kette_grundstueck")
    glb = _echte_glb(ordner_tmp, "--gelaende")
    auftrag = _auftragsordner(ordner_tmp, glb)
    return _lauf(ordner_tmp, auftrag)


def _lauf(tmp_path, ordner, **kw):
    """Nur Diffusion und QA sind Attrappen. Blender läuft wirklich.

    Returns:
        ``(antwort, protokoll, ausgabewurzel)``. Die dritte Angabe ist nötig, weil ein
        Test sonst im **geteilten** Temp-Verzeichnis von pytest sucht und dort die
        Berichte fremder Tests findet. *Allein gelaufen war er grün, in der ganzen
        Sammlung rot* — die unangenehmste Sorte Testfehler.
    """
    protokoll = {"render": []}

    def rendere(auftrag, **_):
        protokoll["render"].append(auftrag)
        ziel = Path(auftrag.ausgabe_png)
        ziel.parent.mkdir(parents=True, exist_ok=True)
        ziel.write_bytes(MINI_PNG)
        return {"status": "ok", "bild_png": str(ziel), "hinweise": ()}

    verarbeite = abholer.verarbeiter(
        out_wurzel=tmp_path / "aus", nullprobe=False,
        _rendere=rendere,
        _qa=lambda *a, **k: {"score": 0.9, "bestanden": True},
        _tiefen_modell=object(),
        **kw)
    antwort = abholer.hole_einen(ordner, fremde_freigabe_gilt=True,
                                 verarbeite=verarbeite)
    return antwort, protokoll, tmp_path / "aus"


# ======================================================================================
# 1 · Der gesunde Lauf — echtes Bauwerk, echte Kamera, echte Riegel
# ======================================================================================

@ohne_kette
def test_ein_freistehendes_bauwerk_laeuft_durch_die_ganze_kette(frei):
    """Ohne Gelände füllt das Bauwerk die Szene — die Rahmung trägt, und es wird gerendert.

    Gemessen: Füllgrad **0,700**, ``massgebend: "breite"``, Breitenanteil 1,0.
    """
    antwort, protokoll, _ = frei

    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort["grund"]
    assert protokoll["render"], (
        "Kein einziger Renderaufruf — ein Riegel hat den gesunden Fall aufgehalten. "
        f"Grund: {antwort.get('befund_kurz') or antwort['grund']}")
    assert antwort["ergebnis"]["images"], "Ein gesunder Lauf liefert Bilder."


@ohne_kette
def test_der_bestellte_sonnenstand_kommt_bis_in_den_bericht(frei):
    """Von der Bestellung über die Naht bis in Blender und zurück — in einem Zug.

    Bis zum 26.08.2026 lief der Sonnenstand ins Leere. Geprüft war das danach an drei
    Stellen einzeln; **über die ganze Kette lief es nie.**
    """
    antwort, _, ausgabe = frei

    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort["grund"]
    berichte = [p for p in ausgabe.rglob("*.json")
                if "sonne" in p.read_text(encoding="utf-8")]
    assert berichte, "Kein Multipass-Bericht mit Sonnenblock im Ausgabeordner."
    sonne = json.loads(berichte[0].read_text(encoding="utf-8"))["sonne"]
    assert sonne["hoehe_grad"] == 12.0 and sonne["azimut_grad"] == 60.0, sonne
    assert set(sonne["bestellt"]) == {"hoehe", "azimut"}, (
        "`bestellt` unterscheidet eine Bestellung von der Vorgabe — über die ganze Kette "
        "hinweg, nicht nur im Runner.")


# ======================================================================================
# 2 · Das Bauwerk auf dem Grundstück — der Fall, für den der Riegel gebaut ist
# ======================================================================================

@ohne_kette
def test_ein_bauwerk_auf_einem_grundstueck_wird_nicht_gerendert(auf_grundstueck):
    """**Die Prüfung, die den Befund vom 26.08.2026 gefunden hätte.**

    8 × 5 m Bauwerk auf einer Platte von 20 × 20 m. Die Kamera rahmt die Szene, das
    Bauwerk füllt **28 %** der Bildbreite — und die HomeStation hat für 30 % einen Score
    von **0,0** gemessen (`auf-vis-20260825-15`, Posten 1).

    Vor der Behebung des Knotennamens lief dieser Fall **durch**: Die Bauwerksbox war
    gleich der Szenenbox, der Breitenanteil 1,0, die wirksame Bildbreite 0,70.
    """
    antwort, protokoll, _ = auf_grundstueck

    assert not protokoll["render"], (
        "Es wurde gerendert. Das Bauwerk füllt 28 % der Bildbreite — ein Bild davon ist "
        "GPU-Zeit für eine Vorlage, die nachweislich nichts trägt.")
    befund = abholer.lies_befund(antwort.get("verzeichnis") or "")
    zeilen = "\n".join(abholer.befund_kurz(befund))
    assert "NICHT GERENDERT (Rahmung)" in zeilen, zeilen


@ohne_kette
def test_und_der_grund_steht_im_ergebnis_und_nicht_nur_im_logbuch(auf_grundstueck):
    """Ein übersprungener Lauf, dem man den Grund nicht ansieht, ist ein verlorener Lauf."""
    antwort, _, _ = auf_grundstueck

    grund = antwort["ergebnis"]["qa"]["verdict"]["reason"]
    assert grund.startswith("NICHT GERENDERT (Rahmung)"), (
        f"Der Vertragsgrund nennt die Rahmung nicht: {grund!r}\n"
        f"Bis zum 26.08.2026 stand hier nur «NICHT GEMESSEN … ein Lauf fehlt» — "
        f"absichtlich verweigert und abgestürzt sahen im Vertrag gleich aus.")
    assert "%" in grund, "Die gemessene Bildbreite gehört in denselben Satz."
    assert antwort["ergebnis"]["qa"]["verdict"]["passed"] is not True, (
        "Ein Auftrag, für den kein einziges Bild entstand, darf nicht als bestanden gelten.")


@ohne_kette
def test_der_gesunde_lauf_traegt_keine_solche_zeile(frei):
    """**Die Gegenprobe.** Ein Vertragsgrund, der immer «NICHT GERENDERT» sagt, sagt nichts."""
    antwort, protokoll, _ = frei

    assert protokoll["render"], "Der gesunde Fall muss rendern."
    assert "NICHT GERENDERT" not in antwort["ergebnis"]["qa"]["verdict"]["reason"]
