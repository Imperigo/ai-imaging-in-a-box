"""Ein Auftrag durch die **ganze** Kette — mit allen Riegeln vom 26.08.2026 zugleich.

**Warum diese Datei nötig ist.** An diesem Tag sind acht Prüfungen entstanden, und jede
ist für sich geprüft worden: die Rahmung vor dem Bildlauf, die Kamerahöhe gegen die
Bauwerkshöhe, die abbestellte Bestellung, die doppelte Ansicht, die Vollständigkeit der
Zwischenbilder, der Sonnenstand, die Erreichbarkeit der Schwelle, die HABS-Abdeckung.

*Acht Prüfungen, die einzeln greifen, sind noch keine Kette, die läuft.* Sie stehen alle
im selben Durchgang und in einer festen Reihenfolge, sie schreiben in dasselbe Urteil, und
mehrere von ihnen können einen Lauf abbrechen. Ob sie sich gegenseitig im Weg stehen,
zeigt kein einziger von ihnen.

Geprüft wird an der **Naht** (`hole_einen` → `verarbeiter` → Befund), mit Attrappen für
Blender und Diffusion.

.. warning::
   **Der Satz, der hier bis zum 26.08.2026 stand — «Ohne Attrappen liefe hier gar nichts»
   — war falsch.** Blender und `.venv-ifc` liegen in diesem Container; nur was ``torch``
   braucht, läuft hier nicht. Und der Unterschied war teuer: Die Bauwerksbox war an
   Attrappen geprüft, in denen die Objektnamen stimmten — über die wirkliche Kette war sie
   **gleich der Szenenbox**.

   *Eine Attrappe, die den Fehler nicht kennt, kann ihn nicht finden.*

   Diese Datei bleibt, weil sie schnell ist und die Fälle stellt, die sich mit echter
   Geometrie nur mühsam erzeugen lassen. Die Gegenstücke mit echtem Blender stehen in
   `tests/test_kettenlauf_echt.py`.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from aiimaging import abholer, bruecke
from conftest import MINI_PNG

#: Ein Bauwerk, das die Rahmung TRAEGT: 8 von 8,5 m Szenenbreite.
BBOX_SZENE = [[0.0, 0.0, 0.0], [8.5, 5.5, 12.0]]
BBOX_BAUWERK = [[0.0, 0.0, 0.0], [8.0, 5.0, 11.0]]


def _kamerablock(kuerzel):
    return {"weg": "abgeleitet", "kuerzel": kuerzel,
            "auge": [0.0, -30.0, 1.70], "blick_auf": [0.0, 0.0, 5.5],
            "abstand_m": 30.0, "brennweite_mm": 35.0, "seitenverhaeltnis": 1.6,
            "shift_mm": 0.0, "neigung_grad": 0.0,
            "gelaende_z": 0.0, "gelaende_bezug": "terrain_an_kamera",
            "gebaeudehoehe_m": 11.0}


def _auftragsordner(tmp_path, *, sonne=None, skip=False):
    ordner = tmp_path / "vis-1-abcdef"
    ordner.mkdir(parents=True)
    (ordner / bruecke.DATEI_LAUFZETTEL).write_text(json.dumps({
        "job_id": "vis-1-abcdef", "status": "queued",
        "approval_token": bruecke.TOKEN_VORSATZ + "deadbeef"}), encoding="utf-8")
    szene = {"geometry": {"path": str(ordner / "model.glb"), "format": "glb"},
             "cameras": "auto",
             "render": {"samples": 8, "faithful": 0.8},
             "style": {"prompt": "overcast sky, no people"},
             "vis": {"skip": skip}}
    if sonne is not None:
        szene["render"]["sun"] = sonne
    (ordner / bruecke.DATEI_SZENE).write_text(json.dumps(szene), encoding="utf-8")
    (ordner / bruecke.DATEI_MODELL).write_bytes(b"glTF\x02\x00\x00\x00")
    return ordner


def _kette(tmp_path, *, karten=None, kamerablock=_kamerablock,
           bbox_bauwerk=BBOX_BAUWERK):
    """Attrappen für Blender und Diffusion; zählt, was wirklich gerufen wurde."""
    protokoll = {"multipass": [], "render": []}
    folge = iter(karten or [[[float(i)]] for i in range(1, 30)])

    def multipass(glb, aus, **kw):
        protokoll["multipass"].append(kw)
        Path(aus).mkdir(parents=True, exist_ok=True)
        tiefe = Path(aus) / "tiefe_norm.png"
        tiefe.write_bytes(MINI_PNG)
        return {"depth_png": str(tiefe), "kamera": kamerablock(kw.get("kamera")),
                "bbox": BBOX_SZENE, "bbox_bauwerk": bbox_bauwerk,
                "sonne": {"weg": "vorgabe", "konvention": "von_sueden"}}

    def rendere(a, **kw):
        protokoll["render"].append(a)
        Path(a.ausgabe_png).parent.mkdir(parents=True, exist_ok=True)
        Path(a.ausgabe_png).write_bytes(MINI_PNG)
        return {"status": "ok", "bild_png": a.ausgabe_png, "hinweise": (),
                "geraeteweg": {"geraet": "cuda", "ladeweg": None, "gemeldet": True,
                               "grund": ""}}

    attrappen = {
        "_multipass": multipass, "_rendere": rendere,
        "_qa": lambda *a, **k: {"score": 0.81, "bestanden": True,
                                "geom_iou_obergrenze": 0.62,
                                "geom_iou_obergrenze_gilt": True},
        "_soll": lambda *a, **k: (next(folge), 1, 1),
    }
    return protokoll, attrappen


def _lauf(tmp_path, ordner, attrappen, **kw):
    verarbeite = abholer.verarbeiter(out_wurzel=tmp_path / "aus", nullprobe=False,
                                     **attrappen, **kw)
    return abholer.hole_einen(ordner, fremde_freigabe_gilt=True, verarbeite=verarbeite)


# ======================================================================================
# Der gesunde Lauf — alle Riegel offen
# ======================================================================================

def test_ein_gesunder_auftrag_laeuft_durch_alle_acht_riegel(tmp_path):
    """**Die wichtigste Prüfung dieser Datei.** Acht Riegel, die einzeln greifen, könnten
    sich zusammen den Weg versperren — und dann läge der Fehler in keinem von ihnen."""
    ordner = _auftragsordner(tmp_path, sonne={"elevation": 35, "azimuth": -20})
    protokoll, attrappen = _kette(tmp_path)

    antwort = _lauf(tmp_path, ordner, attrappen)

    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort["grund"]
    # `antwort["ergebnis"]` ist das VERTRAGSergebnis (kosmovis.render-result/v2), nicht
    # unser inneres. Genau diese Verwechslung hat dieser Test beim Schreiben aufgedeckt.
    assert len(antwort["ergebnis"]["images"]) == 3, "drei Richtungen, drei Bilder"
    assert len(protokoll["render"]) == 3
    assert antwort["ergebnis"]["qa"]["verdict"]["passed"] is True


def test_der_befund_traegt_alles_was_heute_dazugekommen_ist(tmp_path):
    """Jedes Feld dieses Tages **einmal** an der Naht nachgesehen. Ein Feld, das nur im
    Baustein existiert, ist die tote Kante von morgen."""
    ordner = _auftragsordner(tmp_path, sonne={"elevation": 35, "azimuth": -20})
    _protokoll, attrappen = _kette(tmp_path)
    _lauf(tmp_path, ordner, attrappen)

    befund = abholer.lies_befund(ordner)
    assert befund is not None, "der Befund wird geschrieben UND gelesen"
    assert "habs_ansichten" in befund
    assert befund["vertragsvorgaben"], "die Dauerhinweise stehen getrennt"

    kamera = befund["kameras"][0]
    for feld in ("rahmung", "komposition", "sonne", "geraeteweg", "erreichbarkeit",
                 "doppelt_von", "bild_png"):
        assert feld in kamera, feld


def test_die_bestellte_sonne_erreicht_den_multipass(tmp_path):
    """Von der Bestellung bis an die Prozessgrenze — der Weg, der bis heute früh im
    Leeren endete."""
    ordner = _auftragsordner(tmp_path, sonne={"elevation": 8, "azimuth": 250})
    protokoll, attrappen = _kette(tmp_path)
    _lauf(tmp_path, ordner, attrappen)

    assert protokoll["multipass"], "kein Multipass gelaufen"
    assert protokoll["multipass"][0]["sonne"] == {"elevation": 8, "azimuth": 250}


def test_die_angenommene_azimutkonvention_steht_neben_dem_bild(tmp_path):
    """Sie ist eine **Setzung** und keine Messung. Ein Bild, dem man die Annahme nicht
    ansieht, ist später nicht mehr einzuordnen."""
    ordner = _auftragsordner(tmp_path, sonne={"elevation": 8, "azimuth": 250})
    _protokoll, attrappen = _kette(tmp_path)
    _lauf(tmp_path, ordner, attrappen)

    sonne = abholer.lies_befund(ordner)["kameras"][0]["sonne"]
    assert sonne["konvention"] == "von_sueden"
    assert sonne["bestellt"] == ["hoehe", "azimut"]


# ======================================================================================
# Jeder Riegel einzeln — an der ganzen Kette und nicht am Baustein
# ======================================================================================

def test_eine_zu_weite_rahmung_haelt_die_ganze_kette_auf(tmp_path):
    """Nicht nur `verarbeiter`: Auch `hole_einen` darf danach kein Bild melden."""
    ordner = _auftragsordner(tmp_path)
    protokoll, attrappen = _kette(tmp_path, bbox_bauwerk=[[0, 0, 0], [1.0, 1.0, 1.0]])

    antwort = _lauf(tmp_path, ordner, attrappen)

    assert protokoll["render"] == [], "keine Diffusion bei untragbarer Rahmung"
    assert antwort["ergebnis"]["images"] == []
    zeilen = abholer.befund_kurz(abholer.lies_befund(ordner))
    assert [z for z in zeilen if "NICHT GERENDERT (Rahmung)" in z]


def test_eine_kamera_ueber_dem_dach_haelt_die_ganze_kette_auf(tmp_path):
    """Derselbe Owner-Einwand an der zweiten Stelle, an der ganzen Kette geprüft."""
    def hoch(kuerzel):
        return dict(_kamerablock(kuerzel), auge=[0.0, -30.0, 77.023])

    ordner = _auftragsordner(tmp_path)
    protokoll, attrappen = _kette(tmp_path, kamerablock=hoch)

    _lauf(tmp_path, ordner, attrappen)

    assert protokoll["render"] == []
    zeilen = abholer.befund_kurz(abholer.lies_befund(ordner))
    assert [z for z in zeilen if "nicht beurteilbar" in z]


def test_ein_abbestellter_auftrag_beruehrt_weder_blender_noch_gpu(tmp_path):
    """Die einzige Prüfung, die **vor** dem ersten Blender-Lauf greift."""
    ordner = _auftragsordner(tmp_path, skip=True)
    protokoll, attrappen = _kette(tmp_path)

    antwort = _lauf(tmp_path, ordner, attrappen)

    assert protokoll == {"multipass": [], "render": []}
    assert antwort["ergebnis"]["images"] == []
    # **Der Fund dieses Tests.** Bis er geschrieben wurde, reichte `hole_einen` das
    # `uebersprungen` NICHT an `schreibe_ergebnis` durch: Die vierte Lage war gebaut,
    # geprueft — und an der Naht nicht angeschlossen.
    assert antwort["ergebnis"]["qa"]["verdict"]["reason"].startswith("ABBESTELLT")
    assert "Abbestellt" in antwort["grund"]


def test_drei_gleiche_ansichten_kosten_einen_renderlauf(tmp_path):
    """Der Quaderfall: Bei zweizähliger Drehsymmetrie fallen die Über-Eck-Ansichten
    zusammen. Hier fallen absichtlich **alle drei** zusammen."""
    ordner = _auftragsordner(tmp_path)
    protokoll, attrappen = _kette(tmp_path, karten=[[[1.0]]] * 5)

    antwort = _lauf(tmp_path, ordner, attrappen)

    assert len(protokoll["render"]) == 1, "einmal rendern, zweimal uebernehmen"
    spanne = abholer.lies_befund(ordner)["geometrie_urteil"]["kameraspanne"]
    assert spanne["n"] == 3 and spanne["n_gemessen"] == 1 and spanne["n_doppelt"] == 2


def test_ein_halbes_zwischenbild_haelt_die_kette_auf(tmp_path):
    """Und zwar mit einem Befund über eine **Datei**, nicht mit einem Fehlschlag der
    Diffusion."""
    protokoll, attrappen = _kette(tmp_path)
    echt = attrappen["_multipass"]

    def kaputt(glb, aus, **kw):
        bericht = echt(glb, aus, **kw)
        Path(bericht["depth_png"]).write_bytes(MINI_PNG[:-6])
        return bericht

    ordner = _auftragsordner(tmp_path)
    antwort = _lauf(tmp_path, ordner, {**attrappen, "_multipass": kaputt})

    assert protokoll["render"] == []
    assert antwort["tat"] == abholer.TAT_FEHLER
    assert "unvollstaendig oder beschaedigt" in antwort["grund"]


def test_die_habs_abdeckung_steht_im_kurzbefund(tmp_path):
    """Drei Richtungen lassen nichts **fehlen** und trotzdem etwas **offen**."""
    ordner = _auftragsordner(tmp_path)
    _protokoll, attrappen = _kette(tmp_path)
    _lauf(tmp_path, ordner, attrappen)

    zeilen = abholer.befund_kurz(abholer.lies_befund(ordner))
    treffer = [z for z in zeilen if "HABS-Ansichten" in z]
    assert len(treffer) == 1 and "NICHT FESTSTELLBAR" in treffer[0]


def test_die_erreichbarkeit_erreicht_das_vertragsergebnis(tmp_path):
    """Der Deckel 0.62 bei |spearman| 0.998 ergibt höchstens 0.7869 — das **besteht**.
    Die Gegenprobe zum Fall, in dem er nicht besteht, steht in
    `tests/test_rahmung_vor_render.py`."""
    ordner = _auftragsordner(tmp_path)
    _protokoll, attrappen = _kette(tmp_path)
    antwort = _lauf(tmp_path, ordner, attrappen)

    lage = abholer.lies_befund(ordner)["geometrie_urteil"]["erreichbarkeit"]
    assert lage["erreichbar"] is True
    assert lage["hoechster_score"] == pytest.approx(0.7869, abs=0.001)
