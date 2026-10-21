"""«Variante erzeugen» ohne Modelldatei — der Fehler aus der Test-App R48 (21.10.2026).

Nachgestellt ist genau die Bestellkette am Gerät: Zuerst «Grundlage rendern» (``vis.skip``,
alle Passes), danach «Variante erzeugen» in Vorschau-Guete. Die Variante kommt so, wie ihr
Vertrag sie seit dem Fehler-Nachgang vom 20.10.2026 schickt (``render-scene.ts``,
``vis.grundlage``; ``vis-jobs.ts`` ``modellBleibtDaheim``): mit ``vis.grundlage``, mit
LEEREM ``geometry.path`` und **ohne** ``model.glb`` im Auftragsordner.

Bis dahin liess der Abholer sie liegen — «render-scene ohne 'geometry.path'» —, und die
Variante rechnete nie. Seither rechnet sie aus der abgelegten Grundlage; das Modell nimmt sie
vom Auftrag, der die Grundlage gerechnet hat. Fehlt auch die Grundlage, bleibt der klare Satz.

Regel 3: Modell, Kameras und Kennungen synthetisch.
"""
from __future__ import annotations

import json

import pytest

from aiimaging import abholer, bruecke, kosmo_szene

from test_grundlage_varianten import _mit_schoenbild
from test_kettenlauf_26august import _kette, _minimale_glb

GRUNDLAGE_JOB = "vis-1792595787-962e13"
VARIANTE_JOB = "vis-1792595849-002a06"


def _job(ablage, job_id, *, szene, mit_modell):
    """Ein Auftragsordner in der Form der fremden Warteschlange, alle in EINER Ablage."""
    ordner = ablage / job_id
    ordner.mkdir(parents=True)
    (ordner / bruecke.DATEI_LAUFZETTEL).write_text(json.dumps({
        "job_id": job_id, "status": "queued",
        "approval_token": bruecke.TOKEN_VORSATZ + "deadbeef"}), encoding="utf-8")
    (ordner / bruecke.DATEI_SZENE).write_text(json.dumps(szene), encoding="utf-8")
    if mit_modell:
        (ordner / bruecke.DATEI_MODELL).write_bytes(_minimale_glb())
    return ordner


def _bestellung(ordner_pfad, *, vis):
    return {"schema": "kosmovis.render-scene/v1",
            "geometry": {"path": ordner_pfad, "format": "glb"},
            "cameras": "auto",
            "render": {"samples": 8, "faithful": 0.8},
            "style": {"prompt": "overcast sky, no people"},
            "vis": vis}


def _lauf(tmp_path, ordner, attrappen):
    verarbeite = abholer.verarbeiter(out_wurzel=tmp_path / "aus", nullprobe=False,
                                     **attrappen)
    return abholer.hole_einen(ordner, fremde_freigabe_gilt=True, verarbeite=verarbeite)


def _vertrag(ordner) -> dict:
    return json.loads((ordner / bruecke.DATEI_ERGEBNIS).read_text(encoding="utf-8"))


def _grundlage_rendern(tmp_path, attrappen):
    """Schritt 1 der Kette: «Grundlage rendern» — mit Modell, nur Cycles."""
    ablage = tmp_path / "ablage"
    ordner = _job(ablage, GRUNDLAGE_JOB, mit_modell=True, szene=_bestellung(
        str(ablage / GRUNDLAGE_JOB / bruecke.DATEI_MODELL), vis={"skip": True}))
    antwort = _lauf(tmp_path, ordner, attrappen)
    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort["grund"]
    return ablage, _vertrag(ordner)["grundlage"]["id"]


def _variante(ablage, kennung):
    """Schritt 2: «Variante erzeugen», Vorschau — wie die App sie schickt: ohne Modell."""
    return _job(ablage, VARIANTE_JOB, mit_modell=False, szene=_bestellung(
        "", vis={"grundlage": kennung, "guete": "vorschau"}))


def test_die_variante_ohne_modell_wird_gerechnet(tmp_path):
    protokoll, attrappen = _kette(tmp_path)
    attrappen = _mit_schoenbild(attrappen)
    ablage, kennung = _grundlage_rendern(tmp_path, attrappen)
    blender_vorher = len(protokoll["multipass"])

    ordner = _variante(ablage, kennung)
    antwort = _lauf(tmp_path, ordner, attrappen)

    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort["grund"]
    assert len(protokoll["multipass"]) == blender_vorher, "kein neuer Blender-Lauf"
    assert len(protokoll["render"]) == 3, "je Kamera ein KI-Lauf"
    vertrag = _vertrag(ordner)
    assert vertrag["grundlage"] == {"id": kennung, "wiederverwendet": True}
    assert len(vertrag["images"]) == 3


def test_die_variante_nimmt_das_modell_des_grundlage_laufs(tmp_path):
    _protokoll, attrappen = _kette(tmp_path)
    attrappen = _mit_schoenbild(attrappen)
    ablage, kennung = _grundlage_rendern(tmp_path, attrappen)

    auftrag = bruecke.lies_auftrag(_variante(ablage, kennung), fremde_freigabe_gilt=True)

    assert auftrag["modell"] == ablage / GRUNDLAGE_JOB / bruecke.DATEI_MODELL
    assert not auftrag["maengel"], auftrag["maengel"]


def test_ohne_das_modell_rechnet_sie_aus_der_grundlage_allein(tmp_path):
    """Das Modell des ersten Laufs ist weg — die Grundlage traegt Bestand und Modellstand."""
    protokoll, attrappen = _kette(tmp_path)
    attrappen = _mit_schoenbild(attrappen)
    ablage, kennung = _grundlage_rendern(tmp_path, attrappen)
    (ablage / GRUNDLAGE_JOB / bruecke.DATEI_MODELL).unlink()

    ordner = _variante(ablage, kennung)
    auftrag = bruecke.lies_auftrag(ordner, fremde_freigabe_gilt=True)
    assert auftrag["modell"] is None and not auftrag["maengel"]
    assert any("Variante ohne Modelldatei" in w for w in auftrag["warnungen"])

    antwort = _lauf(tmp_path, ordner, attrappen)
    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort["grund"]
    assert len(protokoll["render"]) == 3
    abgelegt = json.loads((tmp_path / "aus" / abholer.GRUNDLAGEN_ORDNER
                           / f"{kennung}.json").read_text(encoding="utf-8"))
    assert "modellstand" in abgelegt and "bestand" in abgelegt
    befund = abholer.lies_befund(ordner)
    assert befund["kameras"][0]["modellstand"] == abgelegt["modellstand"]


def test_ohne_modell_und_mit_unbekannter_grundlage_bleibt_der_klare_satz(tmp_path):
    protokoll, attrappen = _kette(tmp_path)
    ordner = _variante(tmp_path / "ablage", "gl-0123456789abcdef")

    antwort = _lauf(tmp_path, ordner, _mit_schoenbild(attrappen))

    assert antwort["tat"] != abholer.TAT_VERARBEITET
    assert "nicht bekannt" in antwort["grund"]
    assert "Grundlage rendern" in antwort["grund"]
    assert protokoll["multipass"] == [] and protokoll["render"] == []


def test_ohne_pfad_und_ohne_grundlage_bleibt_es_liegen_mit_satz(tmp_path):
    protokoll, attrappen = _kette(tmp_path)
    ordner = _job(tmp_path / "ablage", VARIANTE_JOB, mit_modell=False,
                  szene=_bestellung("", vis={"guete": "vorschau"}))

    antwort = _lauf(tmp_path, ordner, _mit_schoenbild(attrappen))

    assert antwort["tat"] == abholer.TAT_LIEGENGELASSEN
    assert "ohne 'geometry.path'" in antwort["grund"]
    assert "vis.grundlage" in antwort["grund"]
    assert protokoll["multipass"] == []


@pytest.mark.parametrize("vis", [{}, {"grundlage": "vis-1-abcdef"}, {"grundlage": None}])
def test_lies_szene_ohne_pfad_verlangt_eine_gueltige_kennung(vis):
    with pytest.raises(kosmo_szene.SzenenError, match="ohne 'geometry.path'"):
        kosmo_szene.lies_szene(_bestellung("", vis=vis))


def test_lies_szene_ohne_pfad_mit_grundlage():
    szene = kosmo_szene.lies_szene(_bestellung(
        "", vis={"grundlage": "gl-0123456789abcdef", "guete": "vorschau"}))
    assert szene["geometrie"] is None
    assert szene["grundlage"] == "gl-0123456789abcdef"
    assert not szene["maengel"], szene["maengel"]
