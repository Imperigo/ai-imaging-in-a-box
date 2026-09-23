"""Runde 7 am Abholer — vier Befunde vom 23.09.2026, bewacht über den Produktweg.

Was gefunden wurde
------------------
**B · Rahmung.** Seit dem 22.09.2026 meldet der Runner ``deckungsgrad`` nur auf dem Weg
«abgeleitet» und sonst ``null`` samt ``deckungsgrad_wirkungslos``. Der Abholer las
``null`` wie ein fehlendes Feld (alter Runner) und schrieb die Vorgabe 0,70 mit Quelle
«vorgabe» ins Urteil — genau die Rahmung, von der der Runner gerade gesagt hatte, dass
sie nie gestellt wurde.

**C/A · Zwei Quellen für den Standpunkt.** ``kamera_modus`` (Vorgabe MODUS_SHIFT, nie
``None``), ``deckungsgrad``, ``augenhoehe`` und ``bias_grad`` gingen bei **jeder**
Aufgabe an ``seams`` — auch bei einer mitgesandten Kamera mit ``auge``, wo der Runner
sie nie liest. Und eine mitgesandte Kamera wird ganz kopiert: Ein zusätzliches
``richtung`` wäre als ``kamera`` neben ``auge`` mitgegangen.

**E1 · Unlesbare Bestellung ohne Satz am Laufzettel.** Sie blieb auf ``queued``; der
Grund stand nur in der Antwort des Abholers, also im Journal.

**E2 · Unlesbare Szene in der eigenen Ablage.** ``eigene_quelle.lies_auftrag`` fing nur
``NahtError``; was ``kosmo_szene.lies_szene`` sonst warf, riss ``hole_einen`` und damit
``durchgang`` heraus. **Nachgeprüft:** ``SzenenError`` ist auf diesem Weg heute gar
nicht erreichbar (``kosmo_naht.als_render_scene`` baut stets einen Geometrieblock) —
erreichbar ist ``ValueError``: Der MCP-Einlass nimmt ``samples: "viele"`` an, setzt den
Auftrag auf ``queued``, und ``lies_szene`` scheitert an ``int("viele")``.

Wie hier bewacht wird
---------------------
Über den Weg, den das Produkt geht: Brücke bzw. eigene Ablage → ``hole_einen`` →
``verarbeiter``. Attrappen stehen nur an den Nähten, die hier nicht laufen können
(Multipass, Render, QA — aus ``tests/test_abholer.py``). Für B läuft zusätzlich der
**Runner selbst** mit einer ``bpy``-Attrappe (aus
``tests/test_deckungsgrad_wirkt_nur_abgeleitet.py``) auf genau den Argumenten, die
``seams`` aus dem Aufruf des Verarbeiters baut — der Bericht, den der Abholer liest, ist
also der Bericht des Runners und kein von Hand geschriebenes Wörterbuch.

Regel 3: Kameras, Szene und Modell sind synthetisch.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from aiimaging import (abholer, bruecke, eigene_quelle, jobs, kameras, kosmo_naht,
                       kosmo_szene, seams, werkzeuge)

from test_abholer import _auftrag, _kette
from test_deckungsgrad_wirkt_nur_abgeleitet import _runner

#: Eine mitgesandte Kamera, wie KosmoOrbit sie schickt — in Blenders Achsen (``z``),
#: damit keine Drehung dazwischenkommt. Sie steht vor der Szene der Runner-Attrappe
#: (20 x 16 x 9 m) und schaut hinein.
KAMERA = {"name": "k1", "position": [40.0, -30.0, 1.7], "target": [10.0, 8.0, 4.5],
          "fov": 50.0, "up_axis": "z"}

#: Die Felder des Runnerberichts, die der Abholer vor dem Bild liest.
RUNNER_FELDER = ("kamera", "deckungsgrad", "deckungsgrad_wirkungslos", "bbox",
                 "bbox_bauwerk")


def _szene(**zusatz) -> dict:
    szene = {
        "schema": kosmo_szene.SCHEMA_SZENE,
        "geometry": {"path": "model.glb", "format": "glb"},
        "cameras": [dict(KAMERA)],
        "render": {"resolution": [512, 512], "samples": 64, "faithful": 0.8},
        "style": {"prompt": "ein Haus", "mode": "none"},
        "vis": {"backbone": "qwen"},
    }
    szene.update(zusatz)
    return szene


def _mit_runner(monkeypatch, attrappen: dict, *, alter_runner: bool = False) -> None:
    """Die Multipass-Attrappe um den ECHTEN Runner ergänzen.

    Die Attrappe aus ``test_abholer._kette`` schreibt die Dateien, die die Kette danach
    liest, und protokolliert den Aufruf. Danach baut ``seams`` aus demselben Aufruf die
    Argumente, der Runner läuft darauf (``bpy`` ist eine Attrappe), und die Felder seines
    Berichts ersetzen die der Attrappe. ``alter_runner`` streicht die beiden
    Deckungsgradfelder, wie sie ein Runner vor dem 26.08.2026 nicht schrieb.
    """
    modul = _runner(monkeypatch)
    vorher = attrappen["_multipass"]

    def multipass(glb, out, **kw):
        daten = vorher(glb, out, **kw)
        runner_aus = Path(out) / "runner"
        argumente = seams._multipass_argumente(
            glb, runner_aus, drehen=False, aufloesung=kw["aufloesung"],
            samples=kw["samples"], beauty=True, material_id=False,
            kamera=kw.get("kamera"), auge=kw.get("auge"), blick_auf=kw.get("blick_auf"),
            brennweite=kw.get("brennweite"), kamera_modus=kw.get("kamera_modus"),
            gelaende_z=kw.get("gelaende_z"), hoehe=kw.get("hoehe"),
            deckungsgrad=kw.get("deckungsgrad"), augenhoehe=kw.get("augenhoehe"),
            bias_grad=kw.get("bias_grad"))
        monkeypatch.setattr(sys, "argv", ["blender", "--background", "--python", "x.py",
                                          "--", *argumente])
        modul.main()
        bericht = json.loads((runner_aus / "blender-report.json").read_text(
            encoding="utf-8"))
        for feld in RUNNER_FELDER:
            if alter_runner and feld.startswith("deckungsgrad"):
                continue
            daten[feld] = bericht.get(feld)
        return daten

    attrappen["_multipass"] = multipass


def _lauf(tmp_path, szene, *, monkeypatch=None, alter_runner=False, **einstellungen):
    """Brücke → ``hole_einen`` → ``verarbeiter``. Zurück: Antwort, Protokoll, Ordner."""
    ordner = _auftrag(tmp_path, szene=szene)
    protokoll, attrappen = _kette()
    if monkeypatch is not None:
        _mit_runner(monkeypatch, attrappen, alter_runner=alter_runner)
    antwort = abholer.hole_einen(
        ordner, fremde_freigabe_gilt=True,
        verarbeite=abholer.verarbeiter(out_wurzel=tmp_path / "aus", nullprobe=False,
                                       **attrappen, **einstellungen))
    return antwort, protokoll, ordner


def _urteil(tmp_path, ordner, kuerzel) -> dict:
    return json.loads((tmp_path / "aus" / ordner.name / kuerzel
                       / abholer.DATEI_URTEIL).read_text(encoding="utf-8"))["urteil"]


def _laufzettel(ordner) -> dict:
    return json.loads((ordner / bruecke.DATEI_LAUFZETTEL).read_text(encoding="utf-8"))


# ======================================================================================
# B · Rahmung: null heisst NICHT GERAHMT, nicht «Vorgabe»
# ======================================================================================

def test_eine_mitgesandte_kamera_bekommt_keine_vorgabe_ins_rahmungsurteil(
        tmp_path, monkeypatch):
    """**Der Wächter von B.** Der Runner meldet auf dem Weg «vorgegeben»
    ``deckungsgrad: null`` mit Grund; im Urteil steht dann keine 0,70, keine Quelle
    «vorgabe» und keine Bildbreite, die auf ihr ruht — dafür der Grund des Runners."""
    antwort, _, ordner = _lauf(tmp_path, _szene(), monkeypatch=monkeypatch)
    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort["grund"]

    rahmung = _urteil(tmp_path, ordner, "k1")["rahmung"]
    assert rahmung["weg"] == "vorgegeben", "Vorbedingung: der Runner lief vorgegeben"
    assert rahmung["deckungsgrad"] is None, (
        "Der Runner meldet NICHT GERAHMT — eine Zahl hier behauptet eine Rahmung, die "
        "nie gestellt wurde.")
    assert rahmung["deckungsgrad_quelle"] == "nicht_gerahmt"
    assert rahmung["wirksame_bildbreite"] is None and rahmung["basis"] is None, (
        "keine Bildbreite aus einer Vorgabe, die auf diesem Weg nicht gilt")
    assert rahmung["traegt"] is None and rahmung["abbruch"] is None
    assert rahmung["breitenanteil"] == pytest.approx(1.0), (
        "der Anteil haengt nur an den Boxen und bleibt (Bauwerk = Szene)")
    grund = rahmung["deckungsgrad_wirkungslos"]
    assert isinstance(grund, str) and "vorgegeben" in grund, (
        "Der Grund des Runners steht im Urteil, nicht nur in seinem Bericht.")
    assert grund in rahmung["grund"]
    assert "ACHTUNG" not in rahmung["abbruch_grund"]
    assert "Vorgabe" not in rahmung["abbruch_grund"]


def test_ein_alter_runner_ohne_das_feld_bekommt_weiterhin_die_vorgabe(
        tmp_path, monkeypatch):
    """Die Gegenprobe: FEHLT das Feld (Runner vor dem 26.08.2026), gilt die Vorgabe —
    als Vorgabe benannt. Ohne diese Probe zeigte der Wächter oben nur, dass nie mehr
    eine Vorgabe eingesetzt wird."""
    antwort, _, ordner = _lauf(tmp_path, _szene(), monkeypatch=monkeypatch,
                               alter_runner=True)
    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort["grund"]

    rahmung = _urteil(tmp_path, ordner, "k1")["rahmung"]
    assert rahmung["deckungsgrad"] == kameras.DECKUNGSGRAD
    assert rahmung["deckungsgrad_quelle"] == "vorgabe"
    assert rahmung["deckungsgrad_wirkungslos"] is None
    assert rahmung["wirksame_bildbreite"] is not None


def test_null_und_fehlend_sind_am_abgeleiteten_weg_zwei_aussagen():
    """Am Riegel selbst: Auf dem Weg «abgeleitet» bricht die Vorgabe ab und sagt es mit
    ACHTUNG; ein ``null`` dagegen erfindet keinen Abbruch aus einer Zahl, die es nicht
    gibt (der Runner schreibt das so nie — der Bericht widerspräche sich)."""
    basis = {"bbox": [[0, 0, 0], [100, 100, 10]],
             "bbox_bauwerk": [[0, 0, 0], [10, 10, 10]], "kamera": {"weg": "abgeleitet"}}
    fehlt = abholer._rahmung_vor_dem_render(dict(basis))
    null = abholer._rahmung_vor_dem_render(dict(basis, deckungsgrad=None))

    assert fehlt["abbruch"] is True and "ACHTUNG" in fehlt["abbruch_grund"]
    assert null["abbruch"] is None and null["deckungsgrad"] is None
    assert null["deckungsgrad_quelle"] == "nicht_gerahmt"
    assert "NICHT GERAHMT" in null["grund"]


def test_ein_unlesbares_feld_heisst_vorgabe_und_nicht_bericht():
    """``True`` ist in Python eine Zahl. Bis zum 23.09.2026 stand dann die Vorgabe mit
    Quelle «bericht» im Urteil — eine Zahl, die sich als gemeldet ausgab."""
    lage = abholer._rahmung_vor_dem_render({
        "bbox": [[0, 0, 0], [100, 100, 10]], "bbox_bauwerk": [[0, 0, 0], [10, 10, 10]],
        "kamera": {"weg": "abgeleitet"}, "deckungsgrad": True})
    assert lage["deckungsgrad"] == kameras.DECKUNGSGRAD
    assert lage["deckungsgrad_quelle"] == "vorgabe"
    assert "keine Zahl" in lage["abbruch_grund"]


# ======================================================================================
# C/A · Nie kamera und auge zugleich; Rahmungswerte nur mit Richtung
# ======================================================================================

GESETZT = {"deckungsgrad": 0.55, "augenhoehe": 1.6, "bias_grad": 30.0,
           "kamera_modus": kameras.MODUS_GEKIPPT}


def test_eine_mitgesandte_kamera_schickt_keine_rahmungswerte_an_den_multipass(tmp_path):
    """**Der Wächter von C/A.** Was hier ankommt, wäre an Blender gegangen."""
    antwort, protokoll, ordner = _lauf(tmp_path, _szene(), **GESETZT)
    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort["grund"]

    (kw,) = protokoll["multipass"]
    assert list(kw["auge"]) == KAMERA["position"]
    assert kw["kamera"] is None, "kein Richtungskuerzel neben dem Standort"
    for name in GESETZT:
        assert kw[name] is None, (
            f"{name} wirkt nur mit Richtung und darf neben `auge` nicht mitgehen")


def test_was_zurueckbleibt_steht_mit_satz_am_urteil(tmp_path):
    """Ausdrücklich gesetzt und nicht gesandt — das verfällt nicht still."""
    antwort, _, ordner = _lauf(tmp_path, _szene(), **GESETZT)
    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort["grund"]

    satz = _urteil(tmp_path, ordner, "k1")[abholer.URTEIL_KAMERAWERTE_ZURUECK]
    assert isinstance(satz, str)
    for name, wert in GESETZT.items():
        assert f"{name}={wert!r}" in satz


def test_ohne_gesetzte_werte_bleibt_der_vermerk_leer(tmp_path):
    """Die Vorgabe MODUS_SHIFT ist keine Bestellung: ohne gesetzte Werte kein Satz —
    und auch kein ``--kamera-modus`` an einer Kamera mit Standort."""
    antwort, protokoll, ordner = _lauf(tmp_path, _szene())
    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort["grund"]
    assert protokoll["multipass"][0]["kamera_modus"] is None
    assert _urteil(tmp_path, ordner, "k1")[abholer.URTEIL_KAMERAWERTE_ZURUECK] is None


def test_mit_richtung_gehen_die_werte_weiter_mit(tmp_path):
    """Die Gegenprobe: Bei ``cameras: "auto"`` rechnet der Runner aus der Richtung,
    und dort wirken die Werte — sie müssen ankommen."""
    antwort, protokoll, ordner = _lauf(tmp_path, _szene(cameras="auto"), **GESETZT)
    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort["grund"]

    assert protokoll["multipass"], "Vorbedingung: mindestens eine Richtung"
    for kw in protokoll["multipass"]:
        assert kw["kamera"] in abholer.AUTO_RICHTUNGEN and kw["auge"] is None
        for name, wert in GESETZT.items():
            assert kw[name] == wert
    kuerzel = protokoll["multipass"][0]["kamera"]
    assert _urteil(tmp_path, ordner, kuerzel)[abholer.URTEIL_KAMERAWERTE_ZURUECK] is None


def test_was_ankommt_nimmt_auch_der_argumentbauer_von_seams(tmp_path):
    """Die Naht dahinter: Was der Verarbeiter an eine Kamera mit Standort schickt, baut
    ``seams`` zu einem Kommando mit ``--auge`` und OHNE ``--kamera`` und die vier
    Rahmungsschalter."""
    antwort, protokoll, _ = _lauf(tmp_path, _szene(), **GESETZT)
    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort["grund"]
    kw = dict(protokoll["multipass"][0])
    for weg in ("up_axis", "stillstand_frist_s", "timeout", "sonne", "kamera_huellbox"):
        kw.pop(weg, None)
    argumente = seams._multipass_argumente("m.glb", tmp_path / "x", drehen=False,
                                           beauty=True, material_id=False, **kw)
    assert any(a.startswith("--auge=") for a in argumente)
    for schalter in ("--kamera", "--kamera-modus", "--deckungsgrad", "--augenhoehe",
                     "--bias"):
        assert not any(a == schalter or a.startswith(schalter + "=")
                       for a in argumente), schalter


def test_eine_mitgesandte_kamera_mit_zusaetzlicher_richtung_wird_abgewiesen(
        tmp_path, monkeypatch):
    """Zwei Quellen für den Standpunkt — dieselbe Regel wie überall. Auf dem Produktweg
    liefert ``spec_zu_kamera`` heute kein ``richtung``; die Attrappe hier steht für eine
    künftige Quelle, die es täte. Abgewiesen wird mit Satz und BEVOR Blender läuft."""
    echt = kosmo_szene.spec_zu_kamera
    monkeypatch.setattr(kosmo_szene, "spec_zu_kamera",
                        lambda spec: dict(echt(spec), richtung="sSE"))
    antwort, protokoll, ordner = _lauf(tmp_path, _szene())

    assert antwort["tat"] == abholer.TAT_FEHLER
    assert "zweimal bestellt" in antwort["grund"] and "k1" in antwort["grund"]
    assert protokoll["multipass"] == [], "abgewiesen heisst: kein Blender-Lauf"
    assert _laufzettel(ordner)["status"] == bruecke.STATUS_ERROR


# ======================================================================================
# E1 · Eine unlesbare Bestellung trägt ihren Grund am Laufzettel
# ======================================================================================

def test_eine_unlesbare_bestellung_sagt_am_laufzettel_warum_sie_liegt(tmp_path):
    """**Der Wächter von E1.** Eine Szene ohne ``geometry.path`` ist dauerhaft unlesbar.
    Sie bleibt auf ``queued`` — und drüben steht jetzt, warum."""
    szene = _szene()
    szene["geometry"] = {"format": "glb"}
    ordner = _auftrag(tmp_path, szene=szene)

    bericht = abholer.durchgang(tmp_path, verarbeite=lambda a: pytest.fail("gerechnet"),
                                fremde_freigabe_gilt=True)
    (antwort,) = bericht["ergebnisse"]
    assert antwort["tat"] == abholer.TAT_LIEGENGELASSEN
    assert antwort["grund_vermerkt"] is True
    zettel = _laufzettel(ordner)
    assert zettel["status"] == bruecke.STATUS_QUEUED, "wartet zu Recht, kein Fehler"
    assert "nicht lesbar" in zettel[bruecke.FELD_MELDUNG]
    assert "geometry.path" in zettel[bruecke.FELD_MELDUNG]


def test_nach_der_berichtigung_verschwindet_der_satz(tmp_path):
    """Die Gegenprobe: Ist die Szene wieder lesbar, läuft der Auftrag und trägt nicht
    mehr die Begründung von vorhin."""
    szene = _szene()
    szene["geometry"] = {"format": "glb"}
    ordner = _auftrag(tmp_path, szene=szene)
    abholer.hole_einen(ordner, verarbeite=lambda a: pytest.fail("gerechnet"),
                       fremde_freigabe_gilt=True)
    assert bruecke.FELD_MELDUNG in _laufzettel(ordner)

    (ordner / bruecke.DATEI_SZENE).write_text(json.dumps(_szene()), encoding="utf-8")
    antwort = abholer.hole_einen(ordner, verarbeite=lambda a: {"bilder": []},
                                 fremde_freigabe_gilt=True)
    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort["grund"]
    assert bruecke.FELD_MELDUNG not in _laufzettel(ordner)


# ======================================================================================
# E2 · Eine unlesbare Szene in der eigenen Ablage nimmt den Durchgang nicht mit
# ======================================================================================

@pytest.fixture()
def store(tmp_path, monkeypatch):
    """Eine eigene Ablage — **nie** die des Benutzers."""
    ziel = tmp_path / "aiimaging-jobs"
    monkeypatch.setenv(werkzeuge.UMGEBUNG_JOBS, str(ziel))
    return ziel


def _bestelle(tmp_path, **zusatz) -> str:
    glb = tmp_path / "modell.glb"
    glb.write_bytes(b"glTF-Attrappe")
    argumente = {"glb_path": str(glb), "up_axis": "Y", "bbox": [[0, 0, 0], [20, 15, 10]],
                 "approval_token": jobs.TOKEN_PRAEFIX + "TEST"}
    argumente.update(zusatz)
    antwort = werkzeuge.enqueue_render(argumente)
    assert antwort["status"] == jobs.STATUS_QUEUED, antwort
    return antwort["job_id"]


def _satz(store, job_id) -> dict:
    return jobs.lies_job(job_id, store / job_id)


def _durchgang(store) -> tuple[dict, list]:
    gesehen: list = []

    def verarbeite(auftrag):
        gesehen.append(auftrag["job_id"])
        return {"bilder": [], "geometrie_urteil": None, "stil_urteil": None,
                "kameras": [], "zeiten": {"gesamt": 0.0}}

    return abholer.durchgang(store, verarbeite=verarbeite, quelle=eigene_quelle,
                             darf_rechnen=lambda: (True, "frei")), gesehen


def test_eine_ueber_mcp_angenommene_unlesbare_szene_nimmt_den_durchgang_nicht_mit(
        tmp_path, store):
    """**Der Wächter von E2**, auf dem heute erreichbaren Weg: ``samples: "viele"`` geht
    durch den Einlass, und ``lies_szene`` scheitert an ``int("viele")``. Der zweite
    Auftrag der Ablage wird trotzdem angesehen und gerechnet."""
    kaputt = _bestelle(tmp_path, samples="viele")
    gut = _bestelle(tmp_path)

    bericht, gesehen = _durchgang(store)

    assert bericht["gesehen"] == 2
    assert gesehen == [gut], "der lesbare Auftrag wurde trotzdem gerechnet"
    antworten = {a["job_id"]: a for a in bericht["ergebnisse"]}
    assert antworten[kaputt]["tat"] == abholer.TAT_LIEGENGELASSEN
    assert "Szene nicht lesbar" in antworten[kaputt]["grund"]
    satz = _satz(store, kaputt)
    assert satz["status"] == jobs.STATUS_QUEUED
    assert "Szene nicht lesbar" in satz["meldung"], "E1: der Grund steht am Auftrag"


def test_ein_szenenfehler_der_uebersetzung_nimmt_den_durchgang_nicht_mit(
        tmp_path, store, monkeypatch):
    """Dieselbe Probe für ``SzenenError``. Heute unerreichbar — die Attrappe steht für
    eine künftige Übersetzung, die einen Auftrag ohne Geometrieblock liefert. Geworfen
    wird der Fehler vom echten ``lies_szene``."""
    kaputt = _bestelle(tmp_path)
    gut = _bestelle(tmp_path)
    echt = kosmo_naht.als_render_scene

    def uebersetze(satz):
        aus = echt(satz)
        if satz.get("job_id") == kaputt:
            aus = dict(aus, szene=dict(aus["szene"], geometry="kein Block"))
        return aus

    monkeypatch.setattr(kosmo_naht, "als_render_scene", uebersetze)
    bericht, gesehen = _durchgang(store)

    assert gesehen == [gut]
    antworten = {a["job_id"]: a for a in bericht["ergebnisse"]}
    assert antworten[kaputt]["tat"] == abholer.TAT_LIEGENGELASSEN
    assert "SzenenError" in antworten[kaputt]["grund"]
    assert "SzenenError" in _satz(store, kaputt)["meldung"]
