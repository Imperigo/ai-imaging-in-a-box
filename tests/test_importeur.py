"""Der Importeur — **Schritt 1, und er entscheidet, ob es einen zweiten gibt.**

Diese Sammlung prüft nicht, ob eine Datei umgewandelt wird. Sie prüft die vier Stellen,
an denen ein Importeur still falsch sein kann:

1. Er wandelt um, was er hätte durchreichen sollen, und verliert dabei etwas.
2. Er schickt eine Datei in den Subprozess, deren Inhalt nicht zu ihrer Endung passt.
3. Er meldet Erfolg, ohne dass jemand die Umwandlung nachgeprüft hat.
4. Er sagt nein, ohne zu sagen, wie es doch ginge.

**Ohne Blender, ohne ``.venv-ifc``, ohne GPU.** Jeder Subprozess ist eine Attrappe, jede
Datei entsteht hier aus zwei Handvoll Bytes (Regel 3).

**Und dieser Satz stimmte am 21.09.2026 einen halben Tag lang nicht.** Neun dieser Proben
starteten zwar keinen Prozess — sie riefen aber ``seams.finde_blender()``, und das bricht
ab, wenn kein Blender installiert ist. Auf dieser Maschine liegt eines unter
``/opt/blender``; die Proben waren grün und behaupteten in ihrem eigenen Kopf etwas
Falsches.

Gefunden hat es die Prüfung auf ``main``, im **ersten Lauf** nach ihrer Einrichtung.

    *Eine Probe, die ohne Subprozess auskommt, aber nicht ohne das Werkzeug, prüft
    nebenbei die Einrichtung der Maschine — und meldet deren Fehlen als ihren eigenen
    Fehlschlag.*

Seither täuscht :func:`blender_vorhanden` das Werkzeug vor. Die Attrappe ist damit
vollständig: Weg, Aufruf und Bericht sind gesetzt, und **nichts** an diesen Proben hängt
noch an der Maschine, auf der sie laufen.
"""
from __future__ import annotations

import ast
import json
import struct
from pathlib import Path

import pytest

from aiimaging import importeur


# ----------------------------------------------------------------- die Attrappen

@pytest.fixture(autouse=True)
def blender_vorhanden(monkeypatch):
    """Tut so, als sei Blender installiert — ohne es je zu starten.

    ``autouse``, und das ist Absicht: Die Alternative wäre, sie an neun Proben einzeln zu
    schreiben, und die zehnte vergässe sie. *Ein Wächter, den man an jeder Stelle von Hand
    setzen muss, fehlt irgendwann an einer.*
    """
    monkeypatch.setattr(importeur.seams, "finde_blender", lambda: "/nicht/benutzt/blender")


class _Lauf:
    """Was ``subprocess.run`` zurückgibt, so weit der Importeur es ansieht."""

    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def _blender_attrappe(bericht: dict, *, returncode: int = 0, schreibe: bool = True):
    """Ein Blender, das den übergebenen Bericht schreibt — und sonst nichts tut."""
    def starte(cmd, timeout):
        if schreibe:
            ziel = Path(cmd[cmd.index("--report") + 1])
            ziel.parent.mkdir(parents=True, exist_ok=True)
            ziel.write_text(json.dumps(bericht, ensure_ascii=False), encoding="utf-8")
        return _Lauf(returncode=returncode, stderr="Blender meldet sich nicht.")
    return starte


def _guter_bericht(glb: Path, **mehr) -> dict:
    grund = {"status": "ok", "glb_path": str(glb), "quelle_format": "Autodesk FBX",
             "quelle_endung": ".fbx", "blender": "4.2.0", "up_axis": "Y",
             "bbox": [[0.0, 0.0, 0.0], [8.0, 5.0, 3.25]],
             "n_elements": 12, "n_triangles": 240, "warnungen": [], "error": None}
    grund.update(mehr)
    return grund


@pytest.fixture
def fbx(tmp_path):
    """Eine Datei, die vorn wie eine FBX aussieht — mehr sieht der Sichtgang nicht an."""
    pfad = tmp_path / "entwurf.fbx"
    pfad.write_bytes(b"Kaydara FBX Binary  \x00" + b"\x00" * 64)
    return pfad


@pytest.fixture
def glb(tmp_path):
    js = json.dumps({"asset": {"version": "2.0", "generator": "Rhino"}}).encode()
    js += b" " * (-len(js) % 4)
    block = struct.pack("<II", len(js), 0x4E4F534A) + js
    pfad = tmp_path / "entwurf.glb"
    pfad.write_bytes(struct.pack("<4sII", b"glTF", 2, 12 + len(block)) + block)
    return pfad


# ------------------------------------------------- 1 · die Wege, und dass sie sich decken

def test_die_drei_wege_sind_vollstaendig_und_ueberschneidungsfrei() -> None:
    """Jede Endung hat genau einen Weg — sonst entscheidet die Reihenfolge im Wörterbuch."""
    assert importeur.WEGE[".glb"] == importeur.WEG_DURCHGEREICHT
    assert importeur.WEGE[".gltf"] == importeur.WEG_DURCHGEREICHT
    assert importeur.WEGE[".ifc"] == importeur.WEG_IFC
    for endung in importeur.FORMATE_BLENDER:
        assert importeur.WEGE[endung] == importeur.WEG_BLENDER


def test_die_formattabelle_deckt_sich_mit_der_des_runners() -> None:
    """Eine Doppelung ohne Wächter wird zur Abweichung.

    Der Runner darf aus dem Produkt nicht importiert werden — er braucht ``bpy``. Seine
    Tabelle wird darum **als Quelltext gelesen**, nicht ausgeführt. Ohne diese Probe
    könnte der Runner ein Format lernen, das die Produktseite nicht anbietet, und
    umgekehrt: Der Importeur schickte dann eine Datei los, die drüben niemand liest.
    """
    quelle = (Path(importeur.__file__).parent / "runners"
              / "blender_import_runner.py").read_text(encoding="utf-8")
    baum = ast.parse(quelle)
    runner_formate = None
    for knoten in ast.walk(baum):
        if isinstance(knoten, ast.AnnAssign) and getattr(knoten.target, "id", "") == "IMPORTEURE":
            runner_formate = {schluessel.value for schluessel in knoten.value.keys}
    assert runner_formate is not None, "IMPORTEURE im Runner nicht gefunden"

    # Der Runner liest auch glb/gltf — die Produktseite reicht sie durch, statt sie
    # umzuwandeln. Das ist der einzige erlaubte Unterschied, und er steht hier benannt.
    assert runner_formate - {".glb", ".gltf"} == set(importeur.FORMATE_BLENDER)


def test_ein_unbekanntes_format_ist_eine_aussage_ueber_uns() -> None:
    assert importeur.weg_fuer_endung(".skp") is None
    assert importeur.kann_importieren(".skp") is False
    assert importeur.kann_importieren(".FBX") is True, "Grossschreibung darf nichts ändern"


# ------------------------------------------------------------- 2 · durchreichen statt wandeln

def test_eine_glb_wird_durchgereicht_und_nicht_durch_blender_geschickt(glb, tmp_path) -> None:
    """Eine Umwandlung ohne Zweck kann nur verlieren.

    Würde die glb durch Blender laufen, gingen Materialnamen, Hierarchie und Extras
    verloren — und niemand sähe es der Ausgabe an, weil am Ende wieder eine glb dasteht.
    """
    gerufen = []

    def starte(cmd, timeout):
        gerufen.append(cmd)
        return _Lauf()

    bericht = importeur.importiere(glb, tmp_path / "raus.glb", _starte=starte)

    assert gerufen == [], "Für eine glb darf kein Subprozess starten"
    assert bericht["status"] == "ok"
    assert bericht["weg"] == importeur.WEG_DURCHGEREICHT
    assert bericht["glb_path"] == str(glb), "Das Ziel ist die Quelle selbst, keine Kopie"
    assert not (tmp_path / "raus.glb").exists(), "Eine Kopie wäre eine zweite Wahrheit"
    assert bericht["bericht"]["umgewandelt"] is False


# ----------------------------------------------------- 3 · der Inhalt schlägt die Endung

def test_eine_umbenannte_jpg_kommt_nicht_in_den_subprozess(tmp_path) -> None:
    """Der Sichtgang läuft **vor** der Endungsfrage.

    Eine JPG namens ``modell.glb`` hat eine Endung, die wir können, und einen Inhalt, den
    wir nicht können. Wer die Endung zuerst fragt, spart den Sichtgang und bezahlt ihn
    mit einem Fehler aus einer fremden Bibliothek.
    """
    pfad = tmp_path / "modell.glb"
    pfad.write_bytes(b"\xff\xd8\xff\xe0" + b"\x00" * 64)
    gerufen = []

    bericht = importeur.importiere(
        pfad, tmp_path / "raus.glb",
        _starte=lambda cmd, timeout: (gerufen.append(cmd), _Lauf())[1])

    assert gerufen == []
    assert bericht["status"] == "abgelehnt"
    assert "Bild" in bericht["grund"]
    assert bericht["naechster_schritt"], "Eine Absage ohne Ausweg ist eine halbe Auskunft"


def test_eine_datei_die_es_nicht_gibt_wird_als_solche_gemeldet(tmp_path) -> None:
    bericht = importeur.importiere(tmp_path / "fehlt.fbx", tmp_path / "raus.glb",
                                   _starte=lambda cmd, timeout: _Lauf())
    assert bericht["status"] == "abgelehnt"
    assert bericht["glb_path"] is None
    assert bericht["naechster_schritt"]


def test_ein_format_ohne_weg_bekommt_trotzdem_einen_naechsten_schritt(tmp_path) -> None:
    """Auch die Absage ist eine Auskunft — und sie nennt den gangbaren Weg."""
    pfad = tmp_path / "entwurf.xyz"
    pfad.write_bytes(b"irgendwas\x00" * 8)

    bericht = importeur.importiere(pfad, tmp_path / "raus.glb",
                                   _starte=lambda cmd, timeout: _Lauf())

    assert bericht["status"] == "abgelehnt"
    assert bericht["weg"] is None
    assert "glTF" in bericht["naechster_schritt"] or "IFC" in bericht["naechster_schritt"]


# ------------------------------------------------------------------ 4 · der Blender-Weg

def test_eine_fbx_geht_durch_blender_und_der_bericht_kommt_zurueck(fbx, tmp_path) -> None:
    ziel = tmp_path / "raus.glb"
    gerufen = []

    def starte(cmd, timeout):
        gerufen.append(cmd)
        return _blender_attrappe(_guter_bericht(ziel))(cmd, timeout)

    bericht = importeur.importiere(fbx, ziel, _starte=starte)

    assert bericht["status"] == "ok"
    assert bericht["weg"] == importeur.WEG_BLENDER
    assert bericht["glb_path"] == str(ziel)
    assert bericht["bericht"]["n_triangles"] == 240

    cmd = gerufen[0]
    assert "--background" in cmd, "Blender darf keine Oberfläche öffnen"
    assert "--factory-startup" in cmd, "Fremde Voreinstellungen dürfen nicht mitreden"
    assert cmd[cmd.index("--python") + 1].endswith("blender_import_runner.py")


def test_der_bericht_schlaegt_den_rueckgabewert(fbx, tmp_path) -> None:
    """Blender gibt auf manchen Maschinen auch nach einem gelungenen Lauf ≠ 0 zurück.

    Wer zuerst den Rückgabewert liest, wirft einen gelungenen Import weg — und schickt
    jemanden eine Fehlersuche machen, die es nicht gibt.
    """
    ziel = tmp_path / "raus.glb"
    bericht = importeur.importiere(
        fbx, ziel, _starte=_blender_attrappe(_guter_bericht(ziel), returncode=1))
    assert bericht["status"] == "ok"


def test_ohne_bericht_ist_es_ein_fehler_des_werkzeugs_und_kein_befund(fbx, tmp_path) -> None:
    """Kein Bericht heisst: Der Lauf hat nicht stattgefunden. Das ist keine Dateifrage."""
    with pytest.raises(importeur.ImporteurError) as fehler:
        importeur.importiere(fbx, tmp_path / "raus.glb",
                             _starte=_blender_attrappe({}, returncode=2, schreibe=False))
    assert "keinen Bericht" in str(fehler.value)


def test_ein_gemeldeter_importfehler_kommt_als_satz_und_nicht_als_traceback(fbx, tmp_path) -> None:
    schlecht = {"status": "error", "glb_path": None,
                "error": "RuntimeError: Unsupported FBX version 6100"}
    with pytest.raises(importeur.ImporteurError) as fehler:
        importeur.importiere(fbx, tmp_path / "raus.glb",
                             _starte=_blender_attrappe(schlecht, returncode=1))
    assert "6100" in str(fehler.value), "Die Diagnose darf nicht verlorengehen"
    assert fbx.name in str(fehler.value)


def test_eine_warnung_des_runners_erreicht_den_aufrufer(tmp_path) -> None:
    """Eine STL trägt nur Dreiecke — und das muss ankommen, nicht im Bericht versacken."""
    pfad = tmp_path / "entwurf.stl"
    pfad.write_bytes(b"solid test\n" + b"\x00" * 64)
    ziel = tmp_path / "raus.glb"
    warnung = "STL trägt nur Dreiecke — keine Bauteile, keine Räume."

    bericht = importeur.importiere(
        pfad, ziel,
        _starte=_blender_attrappe(_guter_bericht(ziel, warnungen=[warnung],
                                                 quelle_endung=".stl")))

    assert warnung in bericht["hinweise"]


# ------------------------------------------------------- 5 · nicht geprüft ist nicht in Ordnung

def test_ohne_erwartung_bleibt_die_treue_ausdruecklich_ungeprueft(fbx, tmp_path) -> None:
    """``None`` heisst NICHT GEPRÜFT — und nie «in Ordnung».

    Das ist die teuerste Stelle des Moduls. Ein ``True`` hier trüge eine verdrehte
    Geometrie durch die ganze Kette, und am Ende sähe es nach schlechter Bildqualität
    aus statt nach einem Importfehler.
    """
    ziel = tmp_path / "raus.glb"
    bericht = importeur.importiere(fbx, ziel,
                                   _starte=_blender_attrappe(_guter_bericht(ziel)))
    assert bericht["treue"] is None


def test_mit_erwartung_wird_die_umwandlung_wirklich_nachgerechnet(fbx, tmp_path) -> None:
    ziel = tmp_path / "raus.glb"
    bericht = importeur.importiere(
        fbx, ziel, erwartung={"huellbox_m": (8.0, 5.0, 3.25), "n_dreiecke": 240},
        _starte=_blender_attrappe(_guter_bericht(ziel)))

    assert bericht["treue"] is not None
    assert bericht["treue"]["stimmt"] is True
    assert bericht["treue"]["gemessen"] is True


def test_eine_falsche_huellbox_faellt_auf(fbx, tmp_path) -> None:
    """Der Fall, um dessentwillen es die Nachrechnung gibt: 1000-fach zu gross."""
    ziel = tmp_path / "raus.glb"
    gross = _guter_bericht(ziel, bbox=[[0.0, 0.0, 0.0], [8000.0, 5000.0, 3250.0]])

    bericht = importeur.importiere(
        fbx, ziel, erwartung={"huellbox_m": (8.0, 5.0, 3.25)},
        _starte=_blender_attrappe(gross))

    assert bericht["treue"]["stimmt"] is False
    assert bericht["treue"]["diagnose"], "Ein Massstabsfehler hat einen Namen"


# ---------------------------------------------------------------- 6 · was weitergereicht wird

def test_die_hochachse_wird_weitergereicht_und_nicht_entschieden(fbx, tmp_path) -> None:
    """Der Importeur sagt, was der Sichtgang weiss — und ob es feststeht."""
    ziel = tmp_path / "raus.glb"
    bericht = importeur.importiere(fbx, ziel,
                                   _starte=_blender_attrappe(_guter_bericht(ziel)))
    assert "hochachse" in bericht
    assert "hochachse_steht_fest" in bericht
