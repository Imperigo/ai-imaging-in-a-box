"""Fortschritt, Vorschau und Teilbild am Heim-PC — die Abmachung vom 20.10.2026.

Abgemacht ist am Auftrag ein Feld ``progress`` (``{phase, pct, kamera_i, kamera_n,
vorschau, rest_s}``) und, nur bei ``cancelled``, ein ``teilbild``. Geprüft wird an der
**Naht** (``hole_einen`` → ``verarbeiter`` → Laufzettel), mit denselben Attrappen für
Blender und Bildmodell wie im Kettenlauf vom 26.08.2026 — für beide Ablagen.

Regel 3: alle Modelle, Kameras und Kennungen synthetisch.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from aiimaging import abholer, bruecke, eigene_quelle, jobs, knotenweg, werkzeuge

from test_grundlage_varianten import _mit_schoenbild, _ordner, _vertrag
from test_kettenlauf_26august import _auftragsordner, _kette, _minimale_glb

JOB = "vis-1-abcdef"


class _Uhr:
    """Jeder Blick auf die Uhr rückt sie um zehn Sekunden vor — eine Restzeit ohne Warten."""

    def __init__(self):
        self.t = 0.0

    def __call__(self):
        self.t += 10.0
        return self.t


def _mitschreiber():
    """Ein ``_melde``, das jeden Aufruf festhält und dann wirklich schreibt."""
    gemeldet: list[dict] = []

    def melde(ordner, progress, *, dateien=None):
        gemeldet.append(dict(progress))
        return abholer.melde_fortschritt(ordner, progress, dateien=dateien)

    return gemeldet, melde


def _lauf(tmp_path, ordner, attrappen, **kw):
    verarbeite = abholer.verarbeiter(out_wurzel=tmp_path / "aus", nullprobe=False,
                                     **attrappen, **kw)
    return abholer.hole_einen(ordner, fremde_freigabe_gilt=True, verarbeite=verarbeite)


def _zettel(ordner) -> dict:
    return json.loads((ordner / bruecke.DATEI_LAUFZETTEL).read_text(encoding="utf-8"))


# ======================================================================================
# Die Folge der Meldungen
# ======================================================================================

def test_drei_kameras_melden_phasen_kameras_und_wachsenden_fortschritt(tmp_path):
    ordner = _auftragsordner(tmp_path)
    _protokoll, attrappen = _kette(tmp_path)
    gemeldet, melde = _mitschreiber()

    antwort = _lauf(tmp_path, ordner, _mit_schoenbild(attrappen), _melde=melde, _uhr=_Uhr())

    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort["grund"]
    # Je Kamera: blender, blender mit Vorschau, bildmodell, pruefung — und am Ende 1.0.
    folge = [(m["kamera_i"], m["phase"]) for m in gemeldet]
    erwartet = [(i, p) for i in (1, 2, 3)
                for p in ("blender", "blender", "bildmodell", "pruefung")] + [(3, "pruefung")]
    assert folge == erwartet
    assert {m["kamera_n"] for m in gemeldet} == {3}
    anteile = [m["pct"] for m in gemeldet]
    assert anteile == sorted(anteile), "der Fortschritt laeuft nie rueckwaerts"
    assert anteile[0] == 0.0 and anteile[-1] == 1.0
    assert all(0.0 <= p <= 1.0 for p in anteile)


def test_die_restzeit_fehlt_bis_eine_kamera_fertig_ist(tmp_path):
    ordner = _auftragsordner(tmp_path)
    _protokoll, attrappen = _kette(tmp_path)
    gemeldet, melde = _mitschreiber()

    _lauf(tmp_path, ordner, _mit_schoenbild(attrappen), _melde=melde, _uhr=_Uhr())

    erste = [m for m in gemeldet if m["kamera_i"] == 1]
    assert all(m["rest_s"] is None for m in erste), "ohne fertige Kamera keine Schaetzung"
    spaeter = [m for m in gemeldet if m["kamera_i"] > 1]
    assert all(isinstance(m["rest_s"], int) and m["rest_s"] >= 0 for m in spaeter)
    assert gemeldet[-1]["rest_s"] == 0


def test_am_ende_steht_der_letzte_fortschritt_neben_done(tmp_path):
    ordner = _auftragsordner(tmp_path)
    _protokoll, attrappen = _kette(tmp_path)

    _lauf(tmp_path, ordner, _mit_schoenbild(attrappen))

    zettel = _zettel(ordner)
    assert zettel["status"] == bruecke.STATUS_DONE
    assert zettel["progress"]["phase"] == "pruefung"
    assert zettel["progress"]["pct"] == 1.0
    assert bruecke.FELD_TEILBILD not in zettel, "ein Teilbild nur bei cancelled"
    bruecke.pruefe_fortschritt(zettel["progress"])  # die Abmachung haelt


# ======================================================================================
# Die Vorschau
# ======================================================================================

def test_die_vorschau_liegt_als_artefakt_und_wird_ausgeliefert(tmp_path):
    ordner = _auftragsordner(tmp_path)
    _protokoll, attrappen = _kette(tmp_path)
    gemeldet, melde = _mitschreiber()

    _lauf(tmp_path, ordner, _mit_schoenbild(attrappen), _melde=melde)

    genannt = [m["vorschau"] for m in gemeldet if m.get("vorschau")]
    assert genannt[0] == "s__vorschau.png"
    assert genannt[-1] == "nNW__vorschau.png", "die juengste Kamera"
    for name in ("s__vorschau.png", "sSE__vorschau.png", "nNW__vorschau.png"):
        assert knotenweg.artefakt(tmp_path, JOB, name).is_file()
    # Die erste Meldung mit Vorschau kommt, bevor das Bildmodell anfaengt.
    erste = next(i for i, m in enumerate(gemeldet) if m.get("vorschau"))
    assert gemeldet[erste]["phase"] == "blender"


def test_ohne_schoenbild_nennt_der_fortschritt_keine_vorschau(tmp_path):
    ordner = _auftragsordner(tmp_path)
    _protokoll, attrappen = _kette(tmp_path)
    gemeldet, melde = _mitschreiber()

    antwort = _lauf(tmp_path, ordner, attrappen, _melde=melde)

    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort["grund"]
    assert not any(m.get("vorschau") for m in gemeldet)


def test_mit_wiederverwendeter_grundlage_dient_deren_schoenbild(tmp_path):
    protokoll, attrappen = _kette(tmp_path)
    attrappen = _mit_schoenbild(attrappen)
    erster = _ordner(tmp_path, "erster", skip=True)
    assert _lauf(tmp_path, erster, attrappen)["tat"] == abholer.TAT_VERARBEITET
    kennung = _vertrag(erster)["grundlage"]["id"]
    blender_vorher = len(protokoll["multipass"])

    variante = _ordner(tmp_path, "variante", vis={"grundlage": kennung, "seed": 1})
    gemeldet, melde = _mitschreiber()
    antwort = _lauf(tmp_path, variante, attrappen, _melde=melde)

    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort["grund"]
    assert len(protokoll["multipass"]) == blender_vorher, "kein Blender"
    assert [m["vorschau"] for m in gemeldet if m.get("vorschau")][-1] == "nNW__vorschau.png"
    assert (variante / "s__vorschau.png").is_file()


# ======================================================================================
# Der Abbruch und das Teilbild
# ======================================================================================

def _bricht_ab_bei(attrappen, schluessel, ordner, *, nach: int = 1):
    """Die Attrappe ``schluessel`` setzt beim ``nach``-ten Aufruf den Auftrag auf
    ``cancelled`` — so, wie es «Abbrechen» in der Knotenansicht tut."""
    echt = attrappen[schluessel]
    zaehler = {"n": 0}

    def mit_abbruch(*a, **kw):
        erg = echt(*a, **kw)
        zaehler["n"] += 1
        if zaehler["n"] == nach:
            knotenweg.abbrechen(ordner.parent, ordner.name)
        return erg

    return dict(attrappen, **{schluessel: mit_abbruch})


def test_ein_abbruch_zwischen_den_kameras_liefert_das_ki_bild_als_teilbild(tmp_path):
    ordner = _auftragsordner(tmp_path)
    protokoll, attrappen = _kette(tmp_path)
    attrappen = _bricht_ab_bei(_mit_schoenbild(attrappen), "_rendere", ordner)

    antwort = _lauf(tmp_path, ordner, attrappen)

    assert antwort["tat"] == abholer.TAT_ABGEBROCHEN, antwort["grund"]
    assert len(protokoll["render"]) == 1, "nach dem Abbruch wird nichts mehr gerechnet"
    zettel = _zettel(ordner)
    assert zettel["status"] == bruecke.STATUS_CANCELLED, "der Abbruch bleibt stehen"
    assert zettel["teilbild"] == antwort["teilbild"] == "s__teilbild.png"
    assert knotenweg.artefakt(tmp_path, JOB, "s__teilbild.png").is_file()
    # Ohne Guetewerte: kein Vertragsergebnis, kein QA-Block, kein Fehler.
    assert not (ordner / bruecke.DATEI_ERGEBNIS).exists()
    assert "qa" not in zettel and "error" not in zettel


def test_ein_abbruch_vor_dem_ersten_ki_bild_liefert_das_cycles_bild(tmp_path):
    ordner = _auftragsordner(tmp_path)
    protokoll, attrappen = _kette(tmp_path)
    attrappen = _bricht_ab_bei(_mit_schoenbild(attrappen), "_multipass", ordner)

    antwort = _lauf(tmp_path, ordner, attrappen)

    assert antwort["tat"] == abholer.TAT_ABGEBROCHEN, antwort["grund"]
    assert protokoll["render"] == [], "das Bildmodell laeuft nach dem Abbruch nicht an"
    assert antwort["teilbild"] == "s__teilbild.png"
    assert (ordner / "s__teilbild.png").read_bytes() == (ordner / "s__vorschau.png").read_bytes()


def test_ein_abbruch_ohne_jedes_bild_hat_kein_teilbild(tmp_path):
    ordner = _auftragsordner(tmp_path)
    protokoll, attrappen = _kette(tmp_path)
    knotenweg.abbrechen(tmp_path, JOB)
    # Der Auftrag steht schon vor dem Lauf auf cancelled; `hole_einen` wird hier direkt
    # gerufen, um den Blick vor der ersten Kamera zu pruefen.
    verarbeite = abholer.verarbeiter(out_wurzel=tmp_path / "aus", nullprobe=False,
                                     **attrappen)
    auftrag = bruecke.lies_auftrag(ordner, fremde_freigabe_gilt=True)

    with pytest.raises(abholer.AuftragAbgebrochen) as abbruch:
        verarbeite(auftrag)

    assert abbruch.value.teilbild is None
    assert protokoll["multipass"] == []


def test_ein_verarbeiter_ohne_blick_schreibt_nicht_done_ueber_den_abbruch(tmp_path):
    """Die zweite Sicherung in ``hole_einen``: Bis zum 20.10.2026 setzte ein fertiger Lauf
    ``done`` über ein ``cancelled``, das während des Laufs gesetzt worden war."""
    ordner = _auftragsordner(tmp_path)
    bild = tmp_path / "aus" / "s" / "bild.png"
    bild.parent.mkdir(parents=True)
    bild.write_bytes(b"\x89PNG-attrappe")

    def verarbeite(auftrag):
        knotenweg.abbrechen(tmp_path, JOB)
        return {"bilder": [str(bild)]}

    antwort = abholer.hole_einen(ordner, fremde_freigabe_gilt=True, verarbeite=verarbeite)

    assert antwort["tat"] == abholer.TAT_ABGEBROCHEN
    assert _zettel(ordner)["status"] == bruecke.STATUS_CANCELLED
    assert antwort["teilbild"] == "s__teilbild.png"
    assert not (ordner / bruecke.DATEI_ERGEBNIS).exists()


def test_ein_durchgang_zaehlt_den_abbruch(tmp_path):
    ordner = _auftragsordner(tmp_path / "ablage")
    _protokoll, attrappen = _kette(tmp_path)
    attrappen = _bricht_ab_bei(_mit_schoenbild(attrappen), "_rendere", ordner)

    bericht = abholer.durchgang(
        tmp_path / "ablage", fremde_freigabe_gilt=True,
        verarbeite=abholer.verarbeiter(out_wurzel=tmp_path / "aus", nullprobe=False,
                                       **attrappen))

    assert bericht["abgebrochen"] == 1 and bericht["fehler"] == 0


# ======================================================================================
# Ein Schreibfehler kostet kein Bild
# ======================================================================================

def test_ein_fortschritt_der_sich_nicht_schreiben_laesst_bricht_den_lauf_nicht(tmp_path):
    ordner = _auftragsordner(tmp_path)
    _protokoll, attrappen = _kette(tmp_path)
    versuche = []

    def kaputt(ordner, progress, *, dateien=None):
        versuche.append(progress)
        raise OSError("Platte voll (Attrappe)")

    antwort = _lauf(tmp_path, ordner, _mit_schoenbild(attrappen), _melde=kaputt)

    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort["grund"]
    assert versuche, "versucht wurde es"
    assert _zettel(ordner)["status"] == bruecke.STATUS_DONE
    assert "progress" not in _zettel(ordner)


def test_ein_unlesbarer_status_ist_kein_abbruch(tmp_path):
    ordner = _auftragsordner(tmp_path)
    _protokoll, attrappen = _kette(tmp_path)

    def wirft(_ordner):
        raise OSError("gerade geschrieben (Attrappe)")

    antwort = _lauf(tmp_path, ordner, attrappen, _abgebrochen=wirft)

    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort["grund"]


# ======================================================================================
# Die eigene Ablage
# ======================================================================================

def _eigener_auftrag(tmp_path, monkeypatch):
    ablage = tmp_path / "aiimaging-jobs"
    monkeypatch.setenv(werkzeuge.UMGEBUNG_JOBS, str(ablage))
    glb = tmp_path / "modell.glb"
    glb.write_bytes(_minimale_glb())
    bestellt = werkzeuge.enqueue_render({
        "glb_path": str(glb), "up_axis": "Y", "bbox": [[0, 0, 0], [20, 15, 10]],
        "out_dir": str(tmp_path / "out"), "approval_token": jobs.TOKEN_PRAEFIX + "TEST"})
    assert bestellt["error"] is None, bestellt
    return ablage, bestellt["job_id"]


def _durchgang_eigen(tmp_path, ablage, attrappen):
    return abholer.durchgang(
        ablage, quelle=eigene_quelle, darf_rechnen=lambda: (True, "frei"),
        verarbeite=abholer.verarbeiter(out_wurzel=tmp_path / "aus", nullprobe=False,
                                       **attrappen))


def test_die_eigene_ablage_traegt_fortschritt_und_vorschau(tmp_path, monkeypatch):
    ablage, job_id = _eigener_auftrag(tmp_path, monkeypatch)
    _protokoll, attrappen = _kette(tmp_path)

    bericht = _durchgang_eigen(tmp_path, ablage, _mit_schoenbild(attrappen))

    assert bericht["verarbeitet"] == 1, bericht["ergebnisse"]
    satz = jobs.lies_job(job_id, ablage / job_id)
    assert satz["status"] == jobs.STATUS_DONE
    assert satz["progress"]["pct"] == 1.0 and satz["progress"]["phase"] == "pruefung"
    assert satz["progress"]["vorschau"] == "nNW__vorschau.png"
    assert (ablage / job_id / "nNW__vorschau.png").is_file()
    # Der Automat wurde nicht umgangen: Der Verlauf zaehlt nur Zustaende.
    assert [v["status"] for v in satz["verlauf"]][-2:] == ["running", "done"]


def test_die_eigene_ablage_bekommt_beim_abbruch_ihr_teilbild(tmp_path, monkeypatch):
    ablage, job_id = _eigener_auftrag(tmp_path, monkeypatch)
    protokoll, attrappen = _kette(tmp_path)
    echt = attrappen["_rendere"]

    def rendere(a, **kw):
        erg = echt(a, **kw)
        jobs.setze_status(job_id, jobs.STATUS_CANCELLED, ablage / job_id)
        return erg

    bericht = _durchgang_eigen(tmp_path, ablage,
                               dict(_mit_schoenbild(attrappen), _rendere=rendere))

    assert bericht["abgebrochen"] == 1, bericht["ergebnisse"]
    satz = jobs.lies_job(job_id, ablage / job_id)
    assert satz["status"] == jobs.STATUS_CANCELLED
    assert satz["teilbild"] == "s__teilbild.png"
    assert (ablage / job_id / "s__teilbild.png").is_file()
    assert not (ablage / job_id / eigene_quelle.DATEI_ERGEBNIS).exists()
    assert len(protokoll["render"]) == 1


# ======================================================================================
# Die Abmachung selbst
# ======================================================================================

@pytest.mark.parametrize("falsch", [
    {"phase": "rendern", "pct": 0.5},
    {"phase": "blender", "pct": 1.5},
    {"phase": "blender", "pct": True},
    {"phase": "blender", "pct": 0.1, "kamera_i": 0},
    {"phase": "blender", "pct": 0.1, "vorschau": "s/vorschau.png"},
    {"phase": "blender", "pct": 0.1, "vorschau": ""},
    {"phase": "blender", "pct": 0.1, "rest_s": -1},
    {"phase": "blender", "pct": 0.1, "eta": 3},
])
def test_was_nicht_zur_abmachung_passt_wird_abgewiesen(falsch):
    with pytest.raises(bruecke.BrueckenError):
        bruecke.pruefe_fortschritt(falsch)


def test_setze_fortschritt_laesst_status_und_andere_felder_stehen(tmp_path):
    ordner = _auftragsordner(tmp_path)
    vorher = _zettel(ordner)

    bruecke.setze_fortschritt(ordner, {"phase": "blender", "pct": 0.0, "rest_s": None})

    nachher = _zettel(ordner)
    assert nachher["status"] == vorher["status"]
    assert nachher["approval_token"] == vorher["approval_token"]
    assert nachher["progress"] == {"phase": "blender", "pct": 0.0, "rest_s": None}


def test_ein_teilbild_gibt_es_nur_bei_cancelled(tmp_path):
    ordner = _auftragsordner(tmp_path)
    (ordner / "s__teilbild.png").write_bytes(b"x")

    with pytest.raises(bruecke.BrueckenError):
        bruecke.setze_teilbild(ordner, "s__teilbild.png")
    assert "teilbild" not in _zettel(ordner)
