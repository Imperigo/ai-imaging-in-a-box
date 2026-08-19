"""Abholer — der Ablauf zwischen den Bausteinen, die es schon gab.

Geprüft wird hier **kein Rendern**, sondern die Reihenfolge und die Entscheidungen davor.
Genau die waren am 19.08.2026 der Befund: In `/tmp/kosmo-jobs/` lag ein vollständiger
Auftrag, und niemand holte ihn ab.
"""
from __future__ import annotations

import json
import os

import pytest

from aiimaging import abholer, bruecke


# ======================================================================================
# Ein Auftragsverzeichnis, wie die Brücke es anlegt
# ======================================================================================

def _auftrag(basis, name="vis-1787123048-098c6e", *, status=bruecke.STATUS_QUEUED,
             token="CONFIRMED_RENDER_a1b2c3d4", idle_only=False, mit_modell=True,
             szene=None):
    ordner = basis / name
    ordner.mkdir(parents=True, exist_ok=True)
    zettel = {"job_id": name, "status": status, "engine": "cycles"}
    if token is not None:
        zettel["approval_token"] = token
    if idle_only:
        zettel["idle_window_only"] = True
    (ordner / bruecke.DATEI_LAUFZETTEL).write_text(json.dumps(zettel), encoding="utf-8")
    (ordner / bruecke.DATEI_SZENE).write_text(json.dumps(szene or {
        "schema": bruecke.kosmo_szene.SCHEMA_SZENE,
        "geometry": {"path": "model.glb", "format": "glb"},
        "cameras": "auto",
        "render": {"resolution": [512, 512], "samples": 64, "faithful": 0.8},
        "style": {"prompt": "ein Haus", "mode": "none"},
        "vis": {"backbone": "qwen"},
    }), encoding="utf-8")
    if mit_modell:
        (ordner / bruecke.DATEI_MODELL).write_bytes(b"glTF\x02\x00\x00\x00")
    return ordner


def _erfolg(bilder=("a.png",)):
    def verarbeite(auftrag):
        return {"bilder": list(bilder)}
    return verarbeite


def _nie_aufgerufen(auftrag):
    raise AssertionError("verarbeite darf hier gar nicht erst gerufen werden")


# ======================================================================================
# Der Befund: der Auftrag wird abgeholt
# ======================================================================================

def test_ein_freigegebener_auftrag_wird_verarbeitet(tmp_path):
    ordner = _auftrag(tmp_path)
    antwort = abholer.hole_einen(ordner, verarbeite=_erfolg(),
                                 fremde_freigabe_gilt=True)
    assert antwort["tat"] == abholer.TAT_VERARBEITET
    assert (ordner / bruecke.DATEI_ERGEBNIS).is_file()
    zettel = json.loads((ordner / bruecke.DATEI_LAUFZETTEL).read_text(encoding="utf-8"))
    assert zettel["status"] == bruecke.STATUS_DONE


def test_das_ergebnis_liegt_da_bevor_der_laufzettel_es_verspricht(tmp_path):
    """Wer den Laufzettel zuerst setzt, erzeugt ein Zeitfenster, in dem die fremde
    Oberfläche ein Ergebnis sucht, das noch nicht da ist."""
    ordner = _auftrag(tmp_path)
    abholer.hole_einen(ordner, verarbeite=_erfolg(), fremde_freigabe_gilt=True)
    ergebnis = (ordner / bruecke.DATEI_ERGEBNIS).stat().st_mtime_ns
    zettel = (ordner / bruecke.DATEI_LAUFZETTEL).stat().st_mtime_ns
    assert ergebnis <= zettel


# ======================================================================================
# Ohne menschliche Freigabe wird nicht gerechnet
# ======================================================================================

def test_ohne_freigabe_bleibt_der_auftrag_liegen_und_die_karte_unberuehrt(tmp_path):
    ordner = _auftrag(tmp_path)
    antwort = abholer.hole_einen(ordner, verarbeite=_nie_aufgerufen)
    assert antwort["tat"] == abholer.TAT_LIEGENGELASSEN
    assert "Brücke SELBST" in antwort["grund"]
    zettel = json.loads((ordner / bruecke.DATEI_LAUFZETTEL).read_text(encoding="utf-8"))
    assert zettel["status"] == bruecke.STATUS_QUEUED, "nicht einmal auf 'running'"


def test_ein_auftrag_ganz_ohne_token_bleibt_auch_mit_erlaubnis_liegen(tmp_path):
    ordner = _auftrag(tmp_path, token=None)
    antwort = abholer.hole_einen(ordner, verarbeite=_nie_aufgerufen,
                                 fremde_freigabe_gilt=True)
    assert antwort["tat"] == abholer.TAT_LIEGENGELASSEN
    assert "keinen Freigabe-Token" in antwort["grund"]


def test_ein_auftrag_ohne_geometrie_wird_nicht_gerechnet(tmp_path):
    ordner = _auftrag(tmp_path, mit_modell=False)
    antwort = abholer.hole_einen(ordner, verarbeite=_nie_aufgerufen,
                                 fremde_freigabe_gilt=True)
    assert antwort["tat"] == abholer.TAT_LIEGENGELASSEN
    assert "model.glb" in antwort["grund"]


# ======================================================================================
# Die Karte entscheidet mit — und zwar fail-closed
# ======================================================================================

def test_idle_window_only_ohne_auskunft_heisst_nicht_rechnen(tmp_path):
    """Ungeprüft ist nicht dasselbe wie in Ordnung. Das Loch hat Sitzung 07 viermal
    gefunden."""
    ordner = _auftrag(tmp_path, idle_only=True)
    antwort = abholer.hole_einen(ordner, verarbeite=_nie_aufgerufen,
                                 fremde_freigabe_gilt=True, darf_rechnen=None)
    assert antwort["tat"] == abholer.TAT_LIEGENGELASSEN
    assert "fail-open" in antwort["grund"]


def test_idle_window_only_bei_belegter_karte(tmp_path):
    ordner = _auftrag(tmp_path, idle_only=True)
    antwort = abholer.hole_einen(
        ordner, verarbeite=_nie_aufgerufen, fremde_freigabe_gilt=True,
        darf_rechnen=lambda: (False, "312 W, 18 GB belegt"))
    assert antwort["tat"] == abholer.TAT_LIEGENGELASSEN
    assert "312 W" in antwort["grund"]


def test_idle_window_only_bei_freier_karte(tmp_path):
    ordner = _auftrag(tmp_path, idle_only=True)
    antwort = abholer.hole_einen(
        ordner, verarbeite=_erfolg(), fremde_freigabe_gilt=True,
        darf_rechnen=lambda: (True, "13 W"))
    assert antwort["tat"] == abholer.TAT_VERARBEITET


def test_ohne_idle_auflage_wird_die_karte_nicht_gefragt(tmp_path):
    ordner = _auftrag(tmp_path, idle_only=False)

    def nie():
        raise AssertionError("ohne Auflage gibt es nichts zu fragen")

    assert abholer.hole_einen(ordner, verarbeite=_erfolg(), fremde_freigabe_gilt=True,
                              darf_rechnen=nie)["tat"] == abholer.TAT_VERARBEITET


# ======================================================================================
# Ein Fehler ist ein Ergebnis
# ======================================================================================

def test_ein_gescheiterter_lauf_bekommt_eine_begruendung_statt_stille(tmp_path):
    """Ein Auftrag ohne Antwort ist für den Wartenden dasselbe wie ein hängender Rechner."""
    ordner = _auftrag(tmp_path)

    def kracht(auftrag):
        raise RuntimeError("Blender endete mit Code 1")

    antwort = abholer.hole_einen(ordner, verarbeite=kracht, fremde_freigabe_gilt=True)
    assert antwort["tat"] == abholer.TAT_FEHLER
    zettel = json.loads((ordner / bruecke.DATEI_LAUFZETTEL).read_text(encoding="utf-8"))
    assert zettel["status"] == bruecke.STATUS_ERROR
    assert "Blender endete mit Code 1" in json.dumps(zettel)


def test_auch_ein_unsinniger_rueckgabewert_ist_ein_fehler_und_keine_stille(tmp_path):
    ordner = _auftrag(tmp_path)
    antwort = abholer.hole_einen(ordner, verarbeite=lambda a: "fertig!",
                                 fremde_freigabe_gilt=True)
    assert antwort["tat"] == abholer.TAT_FEHLER
    assert "statt eines Wörterbuchs" in antwort["grund"]
    zettel = json.loads((ordner / bruecke.DATEI_LAUFZETTEL).read_text(encoding="utf-8"))
    assert zettel["status"] == bruecke.STATUS_ERROR


def test_erst_kurz_vor_dem_rechnen_auf_running(tmp_path):
    """Vorher hätte ein liegengelassener Auftrag ausgesehen, als arbeite jemand an ihm."""
    ordner = _auftrag(tmp_path)
    gesehen = []

    def merke(auftrag):
        zettel = json.loads(
            (ordner / bruecke.DATEI_LAUFZETTEL).read_text(encoding="utf-8"))
        gesehen.append(zettel["status"])
        return {"bilder": ["a.png"]}

    abholer.hole_einen(ordner, verarbeite=merke, fremde_freigabe_gilt=True)
    assert gesehen == [bruecke.STATUS_RUNNING]


def test_verarbeite_muss_aufrufbar_sein(tmp_path):
    with pytest.raises(abholer.AbholerError, match="aufrufbar"):
        abholer.hole_einen(_auftrag(tmp_path), verarbeite="rendere bitte")


def test_ein_unlesbares_verzeichnis_wird_gemeldet_statt_geworfen(tmp_path):
    leer = tmp_path / "vis-1787123048-000000"
    leer.mkdir()
    antwort = abholer.hole_einen(leer, verarbeite=_nie_aufgerufen)
    assert antwort["tat"] == abholer.TAT_LIEGENGELASSEN
    assert "nicht lesbar" in antwort["grund"]


# ======================================================================================
# Waisen: gemeldet, nicht wiederbelebt
# ======================================================================================

def test_eine_waise_wird_gemeldet(tmp_path):
    ordner = _auftrag(tmp_path, status=bruecke.STATUS_RUNNING)
    alt = os.stat(ordner / bruecke.DATEI_LAUFZETTEL).st_mtime - 10_000
    os.utime(ordner / bruecke.DATEI_LAUFZETTEL, (alt, alt))
    gefunden = abholer.waisen(tmp_path)
    assert len(gefunden) == 1
    assert gefunden[0]["job_id"] == ordner.name
    assert "Nicht** automatisch neu eingereiht" in gefunden[0]["detail"]


def test_eine_waise_wird_nicht_neu_eingereiht(tmp_path):
    """Ein zweiter Lauf kostet eine GPU-Stunde und kann ein zweites Bild unter derselben
    Kennung erzeugen."""
    ordner = _auftrag(tmp_path, status=bruecke.STATUS_RUNNING)
    alt = os.stat(ordner / bruecke.DATEI_LAUFZETTEL).st_mtime - 10_000
    os.utime(ordner / bruecke.DATEI_LAUFZETTEL, (alt, alt))
    bericht = abholer.durchgang(tmp_path, verarbeite=_nie_aufgerufen,
                                fremde_freigabe_gilt=True)
    assert bericht["gesehen"] == 0, "eine Waise ist nicht 'queued'"
    assert len(bericht["waisen"]) == 1
    zettel = json.loads((ordner / bruecke.DATEI_LAUFZETTEL).read_text(encoding="utf-8"))
    assert zettel["status"] == bruecke.STATUS_RUNNING, "unangetastet"


def test_ein_frisch_laufender_auftrag_ist_keine_waise(tmp_path):
    _auftrag(tmp_path, status=bruecke.STATUS_RUNNING)
    assert abholer.waisen(tmp_path) == []


def test_die_waisenfrist_liegt_weit_ueber_der_laengsten_renderdauer():
    """Sonst erklärt sie einen laufenden Auftrag zur Waise."""
    assert abholer.WAISENFRIST_S >= 8 * 900


# ======================================================================================
# Durchgang: einer, nicht endlos
# ======================================================================================

def test_durchgang_bearbeitet_in_der_reihenfolge_des_eingangs(tmp_path):
    for name in ("vis-1787123003-cccccc", "vis-1787123001-aaaaaa",
                 "vis-1787123002-bbbbbb"):
        _auftrag(tmp_path, name)
    reihenfolge = []

    def merke(auftrag):
        reihenfolge.append(auftrag["job_id"])
        return {"bilder": []}

    bericht = abholer.durchgang(tmp_path, verarbeite=merke, fremde_freigabe_gilt=True)
    assert reihenfolge == ["vis-1787123001-aaaaaa", "vis-1787123002-bbbbbb",
                           "vis-1787123003-cccccc"]
    assert bericht["verarbeitet"] == 3


def test_durchgang_zaehlt_die_drei_ausgaenge_getrennt(tmp_path):
    _auftrag(tmp_path, "vis-1787123001-aaaaaa")
    _auftrag(tmp_path, "vis-1787123002-bbbbbb", token=None)      # liegengelassen
    _auftrag(tmp_path, "vis-1787123003-cccccc")

    def mal_so_mal_so(auftrag):
        if auftrag["job_id"].endswith("cccccc"):
            raise RuntimeError("kaputt")
        return {"bilder": ["a.png"]}

    bericht = abholer.durchgang(tmp_path, verarbeite=mal_so_mal_so,
                                fremde_freigabe_gilt=True)
    assert (bericht["gesehen"], bericht["verarbeitet"], bericht["fehler"],
            bericht["liegengelassen"]) == (3, 1, 1, 1)


def test_hoechstens_begrenzt_den_durchgang(tmp_path):
    for i in range(4):
        _auftrag(tmp_path, f"vis-178712300{i}-aaaaa{i}")
    bericht = abholer.durchgang(tmp_path, verarbeite=_erfolg(),
                                fremde_freigabe_gilt=True, hoechstens=2)
    assert bericht["gesehen"] == 2 and bericht["verarbeitet"] == 2


def test_ein_leerer_ablageort_ist_kein_fehler(tmp_path):
    bericht = abholer.durchgang(tmp_path / "gibtsnicht", verarbeite=_nie_aufgerufen)
    assert bericht["gesehen"] == 0 and bericht["waisen"] == []


@pytest.mark.parametrize("wert", [-1, True, 1.5])
def test_unbrauchbares_hoechstens_wird_abgewiesen(tmp_path, wert):
    with pytest.raises(abholer.AbholerError):
        abholer.durchgang(tmp_path, verarbeite=_erfolg(), hoechstens=wert)


def test_der_abholer_schlaeft_nie(tmp_path, monkeypatch):
    """Wer wie oft nachsieht, ist eine Betriebsfrage — Cron, Dienst, Aufruf von Hand.

    Eine Bibliothek, die selbst wartet, lässt sich nicht einbetten und nicht sauber
    beenden. Geprüft am Verhalten und nicht am Wortlaut des Quelltextes: Ein Test, der
    nach `while True` sucht, findet den eigenen Docstring.
    """
    import time as _time
    monkeypatch.setattr(_time, "sleep",
                        lambda *a: pytest.fail("der Abholer darf nicht schlafen"))
    for i in range(3):
        _auftrag(tmp_path, f"vis-178712300{i}-aaaaa{i}")
    bericht = abholer.durchgang(tmp_path, verarbeite=_erfolg(),
                                fremde_freigabe_gilt=True)
    assert bericht["verarbeitet"] == 3


def test_jeder_auftrag_wird_genau_einmal_angefasst(tmp_path):
    """Ein zweiter Lauf desselben Auftrags kostet eine GPU-Stunde."""
    for i in range(3):
        _auftrag(tmp_path, f"vis-178712300{i}-aaaaa{i}")
    gezaehlt = []
    abholer.durchgang(tmp_path, fremde_freigabe_gilt=True,
                      verarbeite=lambda a: gezaehlt.append(a["job_id"]) or {"bilder": []})
    assert len(gezaehlt) == len(set(gezaehlt)) == 3


def test_ein_zweiter_durchgang_fasst_erledigte_nicht_wieder_an(tmp_path):
    _auftrag(tmp_path)
    abholer.durchgang(tmp_path, verarbeite=_erfolg(), fremde_freigabe_gilt=True)
    zweiter = abholer.durchgang(tmp_path, verarbeite=_nie_aufgerufen,
                                fremde_freigabe_gilt=True)
    assert zweiter["gesehen"] == 0


# ======================================================================================
# Der Weg durch unsere Kette — je Kamera einmal
# ======================================================================================

def _kette(*, scores=(0.8,), fehlt_tiefe=False, render_status="ok"):
    """Attrappen für Multipass, Render, Soll-Karte und QA. Zählt, was gerufen wurde."""
    protokoll = {"multipass": [], "render": [], "qa": []}
    werte = list(scores)

    def multipass(glb, out, **kw):
        protokoll["multipass"].append(kw)
        from pathlib import Path as P
        P(out).mkdir(parents=True, exist_ok=True)
        if fehlt_tiefe:
            return {"depth_png": None, "depth_png_fehler": "Kompositor kaputt"}
        return {"depth_png": str(P(out) / "tiefe.png"),
                "beauty_png": str(P(out) / "beauty.png"),
                "depth_exr": str(P(out) / "tiefe.exr")}

    def rendere(a, **kw):
        protokoll["render"].append(a)
        if render_status != "ok":
            return {"status": render_status, "error": "kein Modell"}
        from pathlib import Path as P
        P(a.ausgabe_png).parent.mkdir(parents=True, exist_ok=True)
        P(a.ausgabe_png).write_bytes(b"png")
        return {"status": "ok", "bild_png": a.ausgabe_png}

    def soll(bericht):
        return [0.0, 1.0, 2.0, 3.0], 2, 2

    def qa(bild, soll_werte, **kw):
        protokoll["qa"].append(kw)
        wert = werte.pop(0) if werte else 0.5
        return {"status": "ok", "score": wert, "bestanden": wert >= 0.65,
                "schwelle": kw.get("schwelle")}

    return protokoll, dict(_multipass=multipass, _rendere=rendere, _soll=soll, _qa=qa)


def test_drei_kameras_ergeben_drei_bilder_und_drei_urteile(tmp_path):
    """Der echte Auftrag vom 19.08.2026 trug genau drei Kameras."""
    szene = {
        "schema": bruecke.kosmo_szene.SCHEMA_SZENE,
        "geometry": {"path": "model.glb", "format": "glb"},
        "cameras": [
            {"name": "Eingang", "position": [0, -20, 1.3], "target": [0, 0, 1.3],
             "fov": 60},
            {"name": "Uebersicht", "position": [0, -60, 38], "target": [0, 0, 5],
             "fov": 50},
            {"name": "Innenraum", "position": [1, 1, 1.6], "target": [4, 4, 1.6],
             "fov": 80},
        ],
        "render": {"resolution": [512, 512], "samples": 64, "faithful": 0.8},
        "style": {"prompt": "ein Haus"},
        "vis": {"backbone": "qwen"},
    }
    ordner = _auftrag(tmp_path, szene=szene)
    protokoll, attrappen = _kette(scores=(0.9, 0.7, 0.8))
    antwort = abholer.hole_einen(
        ordner, fremde_freigabe_gilt=True,
        verarbeite=abholer.verarbeiter(out_wurzel=tmp_path / "aus", **attrappen))

    assert antwort["tat"] == abholer.TAT_VERARBEITET
    assert len(protokoll["multipass"]) == 3, "je Kamera ein eigener Multipass"
    assert len(protokoll["render"]) == 3
    ergebnis = json.loads((ordner / bruecke.DATEI_ERGEBNIS).read_text(encoding="utf-8"))
    assert len(ergebnis["images"]) == 3


def test_je_kamera_eine_eigene_tiefenkarte(tmp_path):
    """Ein Bild gegen die Tiefenkarte einer anderen Kamera zu messen ergäbe eine Zahl,
    und die Zahl wäre Unsinn."""
    szene = {
        "geometry": {"path": "model.glb", "format": "glb"},
        "cameras": [
            {"name": "a", "position": [0, -20, 2], "target": [0, 0, 2], "fov": 60},
            {"name": "b", "position": [20, 0, 2], "target": [0, 0, 2], "fov": 60},
        ],
        "render": {"resolution": [512, 512]},
        "style": {"prompt": "x"},
        "vis": {"backbone": "qwen"},
    }
    ordner = _auftrag(tmp_path, szene=szene)
    protokoll, attrappen = _kette(scores=(0.9, 0.9))
    abholer.hole_einen(ordner, fremde_freigabe_gilt=True,
                       verarbeite=abholer.verarbeiter(out_wurzel=tmp_path / "aus",
                                                      **attrappen))
    augen = [kw["auge"] for kw in protokoll["multipass"]]
    assert augen == [(0.0, -20.0, 2.0), (20.0, 0.0, 2.0)]


def test_das_schlechteste_urteil_zaehlt_und_nicht_der_mittelwert(tmp_path):
    """Ein Mittelwert liesse ein durchgefallenes Bild hinter zwei bestandenen
    verschwinden."""
    szene = {
        "geometry": {"path": "model.glb", "format": "glb"},
        "cameras": [{"name": f"k{i}", "position": [0, -20, 2], "target": [0, 0, 2],
                     "fov": 60} for i in range(3)],
        "render": {"resolution": [512, 512]}, "style": {"prompt": "x"},
        "vis": {"backbone": "qwen"},
    }
    ordner = _auftrag(tmp_path, szene=szene)
    _, attrappen = _kette(scores=(0.95, 0.20, 0.90))
    abholer.hole_einen(ordner, fremde_freigabe_gilt=True,
                       verarbeite=abholer.verarbeiter(out_wurzel=tmp_path / "aus",
                                                      **attrappen))
    ergebnis = json.loads((ordner / bruecke.DATEI_ERGEBNIS).read_text(encoding="utf-8"))
    assert ergebnis["qa"]["geometry"]["geometry_fidelity"] == 0.20
    assert ergebnis["qa"]["geometry"]["passed"] is False


def test_ein_ungemessenes_urteil_ist_das_schlechteste_von_allen():
    """Ungemessen ist nicht in Ordnung — dieselbe Regel wie überall sonst."""
    schlecht = abholer._schlechtestes([
        {"score": 0.9, "kamera": "a"},
        {"score": None, "kamera": "b"},
        {"score": 0.1, "kamera": "c"},
    ])
    assert schlecht["kamera"] == "b"


def test_ohne_kameras_wird_nichts_gerendert(tmp_path):
    ordner = _auftrag(tmp_path)
    _, attrappen = _kette()
    antwort = abholer.hole_einen(
        ordner, fremde_freigabe_gilt=True,
        verarbeite=abholer.verarbeiter(out_wurzel=tmp_path / "aus",
                                       auto_richtungen=(), **attrappen))
    assert antwort["tat"] == abholer.TAT_FEHLER
    assert "keine einzige Kamera" in antwort["grund"]


def test_auto_rendert_eine_richtung_und_nicht_zwoelf(tmp_path):
    """Zwölf Standpunkte sind zwölf GPU-Läufe. Wie viele ein Auftrag wert ist, ist eine
    Betriebsentscheidung."""
    ordner = _auftrag(tmp_path)          # die Vorgabeszene sagt cameras: "auto"
    protokoll, attrappen = _kette()
    abholer.hole_einen(ordner, fremde_freigabe_gilt=True,
                       verarbeite=abholer.verarbeiter(out_wurzel=tmp_path / "aus",
                                                      **attrappen))
    assert len(protokoll["multipass"]) == 1
    assert protokoll["multipass"][0]["kamera"] == abholer.AUTO_RICHTUNGEN[0]


def test_ohne_tiefenkarte_wird_nicht_gerendert(tmp_path):
    """Ein Render ohne Konditionierung wäre genau die erfundene Kubatur, gegen die
    dieses Projekt antritt."""
    ordner = _auftrag(tmp_path)
    protokoll, attrappen = _kette(fehlt_tiefe=True)
    antwort = abholer.hole_einen(
        ordner, fremde_freigabe_gilt=True,
        verarbeite=abholer.verarbeiter(out_wurzel=tmp_path / "aus", **attrappen))
    assert antwort["tat"] == abholer.TAT_FEHLER
    assert "Kompositor kaputt" in antwort["grund"]
    assert protokoll["render"] == [], "gar nicht erst gerendert"


def test_ein_gescheiterter_render_wird_nicht_als_bild_gezaehlt(tmp_path):
    ordner = _auftrag(tmp_path)
    _, attrappen = _kette(render_status="fehler")
    antwort = abholer.hole_einen(
        ordner, fremde_freigabe_gilt=True,
        verarbeite=abholer.verarbeiter(out_wurzel=tmp_path / "aus", **attrappen))
    assert antwort["tat"] == abholer.TAT_FEHLER
    assert not (ordner / bruecke.DATEI_ERGEBNIS).exists()


def test_die_angenommene_hochachse_steht_als_konstante_und_wird_benutzt(tmp_path):
    """kosmovis.render-scene/v1 hat kein Feld dafür. Die Annahme wandert darum in den
    Code und nicht in einen Kopf."""
    ordner = _auftrag(tmp_path)
    protokoll, attrappen = _kette()
    abholer.hole_einen(ordner, fremde_freigabe_gilt=True,
                       verarbeite=abholer.verarbeiter(out_wurzel=tmp_path / "aus",
                                                      **attrappen))
    assert protokoll["multipass"][0]["up_axis"] == abholer.ANGENOMMENE_HOCHACHSE
    assert abholer.ANGENOMMENE_HOCHACHSE == "Y_UP", "die glTF-Spezifikation sagt Y-up"


def test_prompt_und_treue_der_szene_kommen_beim_render_an(tmp_path):
    ordner = _auftrag(tmp_path)
    protokoll, attrappen = _kette()
    abholer.hole_einen(ordner, fremde_freigabe_gilt=True,
                       verarbeite=abholer.verarbeiter(out_wurzel=tmp_path / "aus",
                                                      **attrappen))
    a = protokoll["render"][0]
    assert a.prompt == "ein Haus"
    assert a.controlnet_staerke == 0.8


def test_die_stil_qa_laeuft_hier_nicht_und_das_ergebnis_sagt_es(tmp_path):
    """Sie braucht ein Referenzset, das uns gehört. Die Lücke ist sichtbar, nicht still."""
    ordner = _auftrag(tmp_path)
    _, attrappen = _kette()
    abholer.hole_einen(ordner, fremde_freigabe_gilt=True,
                       verarbeite=abholer.verarbeiter(out_wurzel=tmp_path / "aus",
                                                      **attrappen))
    ergebnis = json.loads((ordner / bruecke.DATEI_ERGEBNIS).read_text(encoding="utf-8"))
    assert "style" not in ergebnis["qa"]
    assert "geometry" in ergebnis["qa"]


def test_die_zeiten_werden_je_kamera_und_gesamt_berichtet(tmp_path):
    ordner = _auftrag(tmp_path)
    _, attrappen = _kette()
    abholer.hole_einen(ordner, fremde_freigabe_gilt=True,
                       verarbeite=abholer.verarbeiter(out_wurzel=tmp_path / "aus",
                                                      **attrappen))
    ergebnis = json.loads((ordner / bruecke.DATEI_ERGEBNIS).read_text(encoding="utf-8"))
    assert "gesamt" in ergebnis["timings"]
    assert abholer.AUTO_RICHTUNGEN[0] in ergebnis["timings"]


# ======================================================================================
# Belichtung — dazugeschaltet, nicht aufhaltend
# ======================================================================================

def test_ohne_stil_wird_die_belichtung_gar_nicht_gemessen(tmp_path):
    """Eine Belichtungsschwelle ist keine Eigenschaft guter Belichtung, sondern eines
    Stils. Ohne Stil gibt es nichts, wogegen man prüfen könnte."""
    ordner = _auftrag(tmp_path)
    protokoll, attrappen = _kette()
    gerufen = []
    abholer.hole_einen(
        ordner, fremde_freigabe_gilt=True,
        verarbeite=abholer.verarbeiter(
            out_wurzel=tmp_path / "aus",
            _belichtung=lambda b, r: gerufen.append(b) or {"bestanden": True},
            **attrappen))
    assert gerufen == []


def test_mit_stil_wird_je_kamera_gemessen(tmp_path):
    ordner = _auftrag(tmp_path)
    _, attrappen = _kette()
    gerufen = []

    def pruefe(bild, rahmen):
        gerufen.append(rahmen.slug)
        return {"bestanden": True, "schwere": "ok", "zusammenfassung": "gut"}

    verarbeite = abholer.verarbeiter(out_wurzel=tmp_path / "aus", stil="kosmo_standard",
                                     _belichtung=pruefe, **attrappen)
    antwort = abholer.hole_einen(ordner, fremde_freigabe_gilt=True,
                                 verarbeite=verarbeite)
    assert antwort["tat"] == abholer.TAT_VERARBEITET
    assert gerufen == ["kosmo_standard"]


def test_ein_stil_ohne_rahmen_bekommt_keinen_untergeschoben(tmp_path):
    """Das wäre ein Urteil über einen Stil anhand der Zahlen eines anderen — und es stünde
    nirgends, dass es so war."""
    from aiimaging import belichtung
    assert belichtung.rahmen_fuer("morgennebel") is None

    urteil = abholer._belichtung_urteil("bild.png", "morgennebel", None,
                                        lambda b, r: pytest.fail("darf nicht rufen"))
    assert urteil["gemessen"] is False
    assert "NICHT auf einen anderen zurückgefallen" in urteil["grund"]


def test_nicht_verlangt_und_nicht_gemessen_sind_zweierlei():
    """Und beides ist etwas anderes als 'in Ordnung'."""
    from aiimaging import belichtung
    assert abholer._belichtung_urteil("b.png", None, None, None) is None

    ohne_rahmen = abholer._belichtung_urteil("b.png", "gibtsnicht", None, None)
    assert ohne_rahmen is not None and ohne_rahmen["gemessen"] is False


def test_eine_gerissene_belichtung_haelt_den_auftrag_nicht_auf(tmp_path):
    """Ein Bild, das die Belichtung reisst, ist ein Befund und kein Fehler.

    Die Geometrie entscheidet über `passed`, die Belichtung erklärt.
    """
    ordner = _auftrag(tmp_path)
    _, attrappen = _kette(scores=(0.9,))
    antwort = abholer.hole_einen(
        ordner, fremde_freigabe_gilt=True,
        verarbeite=abholer.verarbeiter(
            out_wurzel=tmp_path / "aus", stil="kosmo_standard",
            _belichtung=lambda b, r: {"bestanden": False, "schwere": "error"},
            **attrappen))
    assert antwort["tat"] == abholer.TAT_VERARBEITET
    ergebnis = json.loads((ordner / bruecke.DATEI_ERGEBNIS).read_text(encoding="utf-8"))
    assert ergebnis["qa"]["geometry"]["passed"] is True


def test_ein_fehler_beim_messen_nimmt_den_lauf_nicht_mit(tmp_path):
    """Ein unlesbares Bild ist ein Befund der Geometrie-QA, die dasselbe Bild ohnehin
    anfasst — hier wäre es ein zweiter Abbruch aus demselben Grund."""
    ordner = _auftrag(tmp_path)
    _, attrappen = _kette()

    def kaputt(bild, rahmen):
        raise OSError("Bild nicht lesbar")

    antwort = abholer.hole_einen(
        ordner, fremde_freigabe_gilt=True,
        verarbeite=abholer.verarbeiter(out_wurzel=tmp_path / "aus",
                                       stil="kosmo_standard",
                                       _belichtung=kaputt, **attrappen))
    assert antwort["tat"] == abholer.TAT_VERARBEITET


def test_das_belichtungsurteil_haengt_am_kameraurteil(tmp_path):
    """Damit sichtbar bleibt, WELCHE Kamera zu hell war — nicht nur, dass eine es war."""
    szene = {
        "geometry": {"path": "model.glb", "format": "glb"},
        "cameras": [{"name": "a", "position": [0, -20, 2], "target": [0, 0, 2], "fov": 60},
                    {"name": "b", "position": [20, 0, 2], "target": [0, 0, 2], "fov": 60}],
        "render": {"resolution": [512, 512]}, "style": {"prompt": "x"},
        "vis": {"backbone": "qwen"},
    }
    ordner = _auftrag(tmp_path, szene=szene)
    _, attrappen = _kette(scores=(0.9, 0.8))
    gesehen = {}

    def merke(auftrag):
        ergebnis = abholer.verarbeiter(
            out_wurzel=tmp_path / "aus", stil="kosmo_standard",
            _belichtung=lambda b, r: {"bestanden": b.endswith("a.png")},
            **attrappen)(auftrag)
        gesehen.update({u["kamera"]: u["belichtung"]["bestanden"]
                        for u in ergebnis["kameras"]})
        return ergebnis

    abholer.hole_einen(ordner, fremde_freigabe_gilt=True, verarbeite=merke)
    assert gesehen == {"a": True, "b": False}
