"""Jede Kamera spricht im Vertrag, und `geometry_gates` ist auf dem Produktweg gefuellt.

**Durchsicht vom 22.09.2026, Posten C8 und C10 im Einbau-Stand.** Nachgestellt am
Produktweg — `abholer.hole_einen` mit `abholer.verarbeiter`, geschrieben ueber
`bruecke.schreibe_ergebnis` in die Datei, die die fremde Warteschlange liest — mit zwei
Kameras, von denen die NICHT schlechteste den Widerspruch traegt:

* ``verdict.reason`` lautete «Geometrie 0.7 gegen 0.65», sonst nichts. Der Widerspruch
  «SCORE BESTEHT, MASKENWEG WIDERSPRICHT» der besseren Kamera fiel weg.
* ``geometry_gates`` fehlte in der Datei ganz.
* ``qa_je_kamera`` trug nur ``[{"kamera": …}, {"kamera": …}]`` — zwei gemessene Kameras
  als *nicht gemessen*, weil das Urteil aus ``qa_gegen_soll`` kein Feld ``gemessen``
  traegt, sondern ``status: "ok"``.

Gelesen wird darum immer die **geschriebene Datei**, nicht der Rueckgabewert einer
inneren Funktion: *Eine Naht, die nur der direkte Aufrufer erreicht, gibt es fuer das
Produkt nicht.*

Die Attrappen fuer Multipass, Render und Soll-Karte kommen aus ``test_abholer._kette``;
ersetzt wird nur die Geometriemessung, und zwar mit einem Urteil in der Form, die
``tiefenschaetzer.qa_gegen_soll`` wirklich liefert (``status``, kein ``gemessen``).
"""
from __future__ import annotations

import json
from pathlib import Path

from aiimaging import abholer, bruecke, eigene_quelle, jobs, werkzeuge

from test_abholer import _auftrag, _kette, _minimale_glb

# Die schlechtere Kamera: Score 0.70, beide Tore bestanden, Maskenweg einverstanden.
SAUBER = {"status": "ok", "score": 0.70, "bestanden": True, "geom_iou": 0.93,
          "spearman": 0.70, "schwelle": 0.65,
          "rho_maske": {"rho": 0.60, "gerichtet": 0.60, "anteil_maske": 0.30},
          "paarurteil": {"gemessen": True, "bestanden": True, "zustaendig": True,
                         "rho": 0.60, "anteil": 0.80}}

# Die BESSERE Kamera traegt den Widerspruch — die Zahlen des verschwundenen Bauwerks,
# gemessen am 26.08.2026: Score 0.951, geom_iou 1.000, rho_maske -0.018.
WIDERSPRUCH = {"status": "ok", "score": 0.951, "bestanden": True, "geom_iou": 1.0,
               "spearman": 0.90, "schwelle": 0.65,
               "rho_maske": {"rho": -0.018, "gerichtet": -0.018, "anteil_maske": 0.30},
               "paarurteil": {"gemessen": True, "bestanden": False, "zustaendig": True,
                              "rho": -0.018, "anteil": 0.10}}

# Eine Kamera, deren Messung nicht lief.
FEHLER = {"status": "fehler", "score": None, "bestanden": False, "geom_iou": None,
          "error": "Schaetzer nicht geladen"}

# Eine GEMESSENE Kamera ohne Maskenweg: Score besteht, aber ohne Maske gibt
# `qa_gegen_soll` `bestanden: None` zurueck (nicht beurteilbar). `rho_maske` fehlt, also
# ist Tor A nicht gemessen — `zwei_tore` meldet fail-closed `bestanden: False`.
MASKENLOS = {"status": "ok", "score": 0.90, "bestanden": None, "geom_iou": 0.93,
             "spearman": 0.87, "schwelle": 0.65, "n_gemeinsam": 120,
             "rho_maske": None, "paarurteil": None}

# Keine gemeinsame Silhouette (Demolauf 14): kein Score, `geom_iou` 0.0, aber der
# Maskenweg hat gemessen und ist durchgefallen. So liefert es `qa_gegen_soll`: Ohne
# Score ist `bestanden` False, nicht None.
KEINE_SILHOUETTE = {"status": "ok", "score": None, "bestanden": False, "geom_iou": 0.0,
                    "spearman": None, "schwelle": 0.65, "n_gemeinsam": 0,
                    "rho_maske": {"rho": -0.05, "gerichtet": -0.05, "anteil_maske": 0.30},
                    "paarurteil": {"gemessen": True, "bestanden": False,
                                   "zustaendig": True, "rho": -0.05, "anteil": 0.10}}


def _szene():
    return {
        "schema": bruecke.kosmo_szene.SCHEMA_SZENE,
        "geometry": {"path": "model.glb", "format": "glb"},
        "cameras": [
            {"name": "Eingang", "position": [0, -20, 1.3], "target": [0, 0, 1.3],
             "fov": 60, "up_axis": "z"},
            {"name": "Uebersicht", "position": [0, -60, 38], "target": [0, 0, 5],
             "fov": 50, "up_axis": "z"},
        ],
        "render": {"resolution": [512, 512], "samples": 64, "faithful": 0.8},
        "style": {"prompt": "ein Haus"},
        "vis": {"backbone": "qwen"},
    }


def _vertragsdatei(tmp_path, *, eingang, uebersicht, soll=None, gemessen=None) -> dict:
    """Ein Auftrag mit zwei Kameras durch den Produktweg; zurueck kommt die DATEI.

    ``soll`` ersetzt die Soll-Karte der Attrappe (fuer die Zwillingsansicht);
    ``gemessen`` sammelt die Kameraordner, deren Bild wirklich gemessen wurde.
    """
    ordner = _auftrag(tmp_path, szene=_szene())
    _, attrappen = _kette()

    def qa(bild, soll, **kw):
        if Path(bild).name.startswith("nullprobe_"):
            return {"status": "ok", "score": 0.30, "bestanden": False}
        if gemessen is not None:
            gemessen.append(Path(bild).parent.name)
        return dict(uebersicht if "Uebersicht" in str(bild) else eingang)

    attrappen["_qa"] = qa
    if soll is not None:
        attrappen["_soll"] = soll
    antwort = abholer.hole_einen(
        ordner, fremde_freigabe_gilt=True,
        verarbeite=abholer.verarbeiter(out_wurzel=tmp_path / "aus", **attrappen))
    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort["grund"]
    return json.loads((ordner / bruecke.DATEI_ERGEBNIS).read_text(encoding="utf-8"))


# --------------------------------------------------------------------------------------
# (a) Nicht nur die schlechteste Kamera spricht
# --------------------------------------------------------------------------------------

def test_der_widerspruch_der_nicht_schlechtesten_kamera_steht_im_vertragsgrund(tmp_path):
    """Der Kernfall: Die SCHLECHTERE Kamera besteht sauber, die BESSERE traegt den
    Widerspruch. Vor dem 22.09.2026 stand davon nichts in ``verdict.reason``."""
    erg = _vertragsdatei(tmp_path, eingang=SAUBER, uebersicht=WIDERSPRUCH)

    # Vorbedingung: Der `qa`-Block beschreibt wirklich die andere, schlechtere Kamera —
    # sonst prueft diese Probe den alten Satz und nicht den neuen.
    assert erg["qa"]["geometry"]["geometry_fidelity"] == 0.70
    grund = erg["qa"]["verdict"]["reason"]
    assert "MASKENWEG WIDERSPRICHT bei Kamera 'Uebersicht'" in grund, grund
    assert "-0.018" in grund, "der Satz nennt die Zahl, an der der Widerspruch haengt"
    # Die saubere Kamera bekommt KEINEN Satz — sonst waere es eine Ausredenmaschine.
    assert "Kamera 'Eingang'" not in grund


def test_ohne_widerspruch_schweigt_der_satz_je_kamera(tmp_path):
    """Die Gegenprobe: Zwei saubere Kameras, kein Satz."""
    erg = _vertragsdatei(tmp_path, eingang=SAUBER, uebersicht=dict(SAUBER, score=0.80))

    assert "MASKENWEG WIDERSPRICHT" not in erg["qa"]["verdict"]["reason"]
    assert "UNGEPRUEFT bei Kamera" not in erg["qa"]["verdict"]["reason"]


def test_qa_je_kamera_traegt_auf_dem_produktweg_den_geometrieblock(tmp_path):
    """Zwei GEMESSENE Kameras kamen bis zum 22.09.2026 nur mit ihrem Namen an — in der
    Lesart des Vertrags: *nicht gemessen*."""
    erg = _vertragsdatei(tmp_path, eingang=SAUBER, uebersicht=WIDERSPRUCH)

    je = {e["kamera"]: e for e in erg["qa_je_kamera"]}
    assert je["Eingang"]["geometry"]["geometry_fidelity"] == 0.70
    assert je["Uebersicht"]["geometry"]["geometry_fidelity"] == 0.951


def test_eine_kamera_mit_gescheiterter_messung_traegt_weiter_nur_ihren_namen(tmp_path):
    """Die dritte Antwort bleibt: ``status: fehler`` ist nicht gemessen, kein Block mit
    ``passed: false``, der sich als durchgefallen laese."""
    erg = _vertragsdatei(tmp_path, eingang=FEHLER, uebersicht=SAUBER)

    je = {e["kamera"]: e for e in erg["qa_je_kamera"]}
    assert je["Eingang"] == {"kamera": "Eingang"}
    assert "geometry" in je["Uebersicht"]


# --------------------------------------------------------------------------------------
# (b) `geometry_gates` auf dem Produktweg
# --------------------------------------------------------------------------------------

def test_geometry_gates_ist_auf_dem_produktweg_gefuellt(tmp_path):
    """Die Zahlen stammen von DERSELBEN Kamera wie der `qa`-Block — ``geom_iou`` heisst
    in beiden dasselbe (siehe `_pruefe_ein_name_eine_zahl`)."""
    erg = _vertragsdatei(tmp_path, eingang=SAUBER, uebersicht=dict(SAUBER, score=0.80))

    tore = erg["geometry_gates"]
    assert tore["camera"] == "Eingang"
    assert tore["rho_mask"] == 0.60 and tore["rho_mask_status"] == "ok"
    assert tore["geom_iou"] == erg["qa"]["geometry"]["geom_iou"] == 0.93
    assert tore["passed"] is True
    # Ohne Gegenprobe wird nichts freigegeben, und der Block sagt es selbst.
    assert tore["counter_check_status"] == "fehlt"
    assert tore["released"] is False
    assert "geom_iou_widerspruch" not in tore["fail_reasons"]


def test_geometry_gates_rechnet_die_andere_kamera_ein(tmp_path):
    """Die bessere Kamera faellt an Tor A (rho_maske -0.018 < 0.10). Ohne das Einrechnen
    stuende im Block ``passed: true`` — das Urteil der schlechteren allein."""
    erg = _vertragsdatei(tmp_path, eingang=SAUBER, uebersicht=WIDERSPRUCH)

    tore = erg["geometry_gates"]
    assert tore["passed"] is False
    assert tore["released"] is False
    assert "kamera_nicht_bestanden:Uebersicht" in tore["fail_reasons"]
    assert tore["reason"].startswith("NICHT BESTANDEN wegen Kamera 'Uebersicht'")


def test_geometry_gates_meldet_eine_ungemessene_kamera_ausdruecklich(tmp_path):
    """Ist die Kamera des Urteils nicht gemessen, steht der Block trotzdem da — als
    NICHT GEMESSEN mit Grund, nicht als fehlendes Feld und nicht als ``passed: false``."""
    erg = _vertragsdatei(tmp_path, eingang=FEHLER, uebersicht=SAUBER)

    tore = erg["geometry_gates"]
    assert tore["status"] == "fehlt"
    assert tore["passed"] is None
    assert tore["released"] is False
    assert tore["rho_mask"] is None and tore["geom_iou"] is None
    assert tore["reason"].startswith("NICHT GEMESSEN")
    assert "kamera_nicht_gemessen" in tore["fail_reasons"]


# --------------------------------------------------------------------------------------
# (c) Nachproben der Durchsicht vom 22.09.2026 — jede an der geschriebenen Datei
# --------------------------------------------------------------------------------------

def test_der_grund_widerspricht_dem_feld_nicht_wenn_die_eigene_fehlt_und_eine_andere_faellt(
        tmp_path):
    """Eigene Kamera NICHT GEMESSEN, eine andere faellt GEMESSEN durch: ``passed`` ist
    ``false``. Bis zur Nachprobe endete der Grund trotzdem mit «'passed: null' … heissen
    hier ungeprueft» — ein Satz, der dem Feld daneben widersprach."""
    erg = _vertragsdatei(tmp_path, eingang=FEHLER, uebersicht=WIDERSPRUCH)

    tore = erg["geometry_gates"]
    assert tore["camera"] == "Eingang" and tore["status"] == "fehlt"
    assert tore["passed"] is False
    assert "kamera_nicht_bestanden:Uebersicht" in tore["fail_reasons"]
    assert "'passed: null'" not in tore["reason"], tore["reason"]
    assert "'passed: false' kommt von Kamera 'Uebersicht'" in tore["reason"], tore["reason"]


def test_eine_andere_kamera_ohne_maske_zaehlt_nicht_als_durchgefallen(tmp_path):
    """Tor A ohne ``rho_maske`` ist fail-closed ``bestanden: False`` — aber NICHT
    GEMESSEN. Fuer die Kamera selbst ist das richtig; als «andere Kamera faellt durch»
    waere es eine Aussage ueber ein Bild, die niemand gemessen hat."""
    erg = _vertragsdatei(tmp_path, eingang=SAUBER, uebersicht=MASKENLOS)

    tore = erg["geometry_gates"]
    assert tore["camera"] == "Eingang"
    assert "kamera_nicht_bestanden:Uebersicht" not in tore["fail_reasons"], tore
    assert tore["passed"] is True
    assert not tore["reason"].startswith("NICHT BESTANDEN wegen")


def test_der_widerspruch_der_schlechtesten_kamera_steht_genau_einmal(tmp_path):
    """Traegt die SCHLECHTESTE Kamera den Widerspruch, spricht der Gesamtsatz fuer sie —
    und der Satz je Kamera nennt sie nicht ein zweites Mal."""
    erg = _vertragsdatei(tmp_path, eingang=WIDERSPRUCH, uebersicht=dict(SAUBER, score=0.99))

    grund = erg["qa"]["verdict"]["reason"]
    # Vorbedingung: Die Widerspruchskamera ist wirklich die des `qa`-Blocks.
    assert erg["qa"]["geometry"]["geometry_fidelity"] == 0.951
    assert grund.count("MASKENWEG WIDERSPRICHT") == 1, grund
    assert "bei Kamera 'Eingang'" not in grund


def test_ein_paarurteil_ohne_entscheid_widerspricht_nicht(tmp_path):
    """``paarurteil.bestanden: None`` heisst: der Maskenweg hat NICHT entschieden. Das
    ist Schweigen, kein Widerspruch — ein Satz dazu waere eine Aussage ohne Messung."""
    schweigt = dict(WIDERSPRUCH, paarurteil={"gemessen": False, "bestanden": None,
                                             "zustaendig": True, "rho": None,
                                             "anteil": None})
    erg = _vertragsdatei(tmp_path, eingang=SAUBER, uebersicht=schweigt)

    assert "MASKENWEG WIDERSPRICHT" not in erg["qa"]["verdict"]["reason"]


def test_geometry_gates_kommt_auch_ueber_die_eigene_ablage_an(tmp_path, monkeypatch):
    """Der zweite Weg: ein ueber den MCP-Einlass bestellter Auftrag, abgeholt aus der
    eigenen Ablage und ueber ``eigene_quelle.schreibe_ergebnis`` geschrieben. Der
    Kommentar am Kameraurteil sagt, das Torurteil erreiche «beide Quellen» — hier steht
    die zweite. Drei Kameras (``cameras: auto``); ``sSE`` traegt den Widerspruch."""
    ablage = tmp_path / "aiimaging-jobs"
    monkeypatch.setenv(werkzeuge.UMGEBUNG_JOBS, str(ablage))
    glb = tmp_path / "modell.glb"
    glb.write_bytes(_minimale_glb())
    bestellt = werkzeuge.enqueue_render({
        "glb_path": str(glb), "up_axis": "Y", "bbox": [[0, 0, 0], [20, 15, 10]],
        "out_dir": str(tmp_path / "out"), "approval_token": jobs.TOKEN_PRAEFIX + "TEST"})
    assert bestellt["error"] is None, bestellt

    _, attrappen = _kette()
    je_ordner = {"s": SAUBER, "sSE": WIDERSPRUCH, "nNW": dict(SAUBER, score=0.80)}

    def qa(bild, soll, **kw):
        if Path(bild).name.startswith("nullprobe_"):
            return {"status": "ok", "score": 0.30, "bestanden": False}
        return dict(je_ordner[Path(bild).parent.name])

    attrappen["_qa"] = qa
    bericht = abholer.durchgang(
        ablage, quelle=eigene_quelle, darf_rechnen=lambda: (True, "frei"),
        verarbeite=abholer.verarbeiter(out_wurzel=tmp_path / "aus", **attrappen))
    assert bericht["verarbeitet"] == 1, bericht["ergebnisse"]

    datei = ablage / bestellt["job_id"] / eigene_quelle.DATEI_ERGEBNIS
    erg = json.loads(datei.read_text(encoding="utf-8"))
    tore = erg["geometry_gates"]
    assert tore["camera"] == "s"
    assert tore["geom_iou"] == erg["qa"]["geometry"]["geom_iou"] == 0.93
    assert "kamera_nicht_bestanden:sSE" in tore["fail_reasons"]
    assert "kamera_nicht_bestanden:nNW" not in tore["fail_reasons"]
    assert "MASKENWEG WIDERSPRICHT bei Kamera 'sSE'" in erg["qa"]["verdict"]["reason"]


def test_ohne_gemeinsame_silhouette_ist_geom_iou_auch_in_den_toren_nicht_gemessen(tmp_path):
    """``verdict.reason`` nennt ``geom_iou: 0.0`` ohne gemeinsame Silhouette eine
    FEHLENDE MESSUNG. ``geometry_gates`` fuehrte dieselbe 0.0 als gemessen
    (``geom_iou_status: ok``) — zwei Aussagen ueber eine Zahl in einer Datei."""
    erg = _vertragsdatei(tmp_path, eingang=KEINE_SILHOUETTE, uebersicht=SAUBER)

    grund = erg["qa"]["verdict"]["reason"]
    assert "FEHLENDE MESSUNG" in grund, grund
    tore = erg["geometry_gates"]
    assert tore["camera"] == "Eingang"
    assert tore["geom_iou"] is None
    assert tore["geom_iou_status"] != "ok"
    assert "geom_iou_nicht_gemessen" in tore["fail_reasons"]
    # Der `qa`-Block bleibt byte-identisch: Dort steht die 0.0 weiter, der Satz ordnet sie.
    assert erg["qa"]["geometry"]["geom_iou"] == 0.0
    assert "geom_iou_widerspruch" not in tore["fail_reasons"]


def test_eine_gemessene_kamera_ohne_maske_traegt_ihren_vorbehalt(tmp_path):
    """``bestanden: None`` wird in ``qa_je_kamera`` zu ``passed: false`` — der fremde
    Vertrag fuehrt ``passed`` als Wahrheitswert, ``null`` geht dort nicht. Der Gesamtblock
    loest das mit einem Satz in ``verdict.reason``; dieselbe Form gilt je Kamera. Ohne
    den Satz laese sich die Kamera als durchgefallen."""
    erg = _vertragsdatei(tmp_path, eingang=SAUBER, uebersicht=MASKENLOS)

    je = {e["kamera"]: e for e in erg["qa_je_kamera"]}
    assert je["Uebersicht"]["geometry"]["passed"] is False
    grund = erg["qa"]["verdict"]["reason"]
    satz = next((t for t in grund.split("; ")
                 if t.startswith("UNGEPRUEFT bei Kamera 'Uebersicht'")), None)
    assert satz is not None, grund
    assert "'passed: false' heisst hier nicht durchgefallen" in satz
    assert "KEIN MASKENWEG" in satz
    assert "Kamera 'Eingang'" not in grund


def test_der_vorbehalt_der_schlechtesten_kamera_steht_nur_einmal(tmp_path):
    """Ist die maskenlose Kamera die schlechteste, traegt der Gesamtsatz ihren Vorbehalt
    schon — ein zweiter Satz je Kamera waere dieselbe Auskunft doppelt."""
    erg = _vertragsdatei(tmp_path, eingang=dict(MASKENLOS, score=0.66), uebersicht=SAUBER)

    grund = erg["qa"]["verdict"]["reason"]
    assert erg["qa"]["geometry"]["geometry_fidelity"] == 0.66
    assert grund.count("KEIN MASKENWEG") == 1, grund
    assert "UNGEPRUEFT bei Kamera" not in grund


def test_die_zwillingsansicht_der_eigenen_kamera_ist_keine_andere_kamera(tmp_path):
    """Zwei gleiche Soll-Karten: ``Uebersicht`` wird nicht gerendert, sondern uebernimmt
    Bild und Urteil von ``Eingang`` (``doppelt_von``). Faellt ``Eingang`` an Tor A durch,
    steht das im Block — nicht ein zweites Mal als «andere Kamera faellt durch»."""
    gemessen: list = []
    erg = _vertragsdatei(tmp_path, eingang=WIDERSPRUCH, uebersicht=SAUBER,
                         soll=lambda bericht: ([[0.0, 1.0], [2.0, 3.0]], 2, 2),
                         gemessen=gemessen)

    # Vorbedingung: Es gab wirklich einen Zwilling — gemessen wurde nur `Eingang`.
    assert set(gemessen) == {"Eingang"}, gemessen
    tore = erg["geometry_gates"]
    assert tore["camera"] == "Eingang"
    assert tore["passed"] is False
    assert "kamera_nicht_bestanden:Uebersicht" not in tore["fail_reasons"], tore
    assert not tore["reason"].startswith("NICHT BESTANDEN wegen")
