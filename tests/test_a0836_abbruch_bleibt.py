"""A0836 «Abbruch bleibt Abbruch»: Ein bestätigter Abbruch in der eigenen Auftragsablage
wird von einer verspäteten Meldung des Rechners nicht wiederbelebt.

Herkunft: Externes Audit 24.11.2026, Befund V4. Die Audit-Probe hielt
``jobs.vermerke_fortschritt`` nach dem Lesen an, bestätigte dazwischen ``cancelled`` und
fand danach wieder ``running`` auf der Platte (Zeilen «accepted cancellation» und «after
progress»). Hier umgestellt: Mit der Sperre je Auftrag kann der Abbruch nicht mehr
*zwischen* Lesen und Schreiben der Fortschrittsmeldung bestätigt werden; er wartet, bis
sie geschrieben ist, und liest dann neu. Geprüft wird das Ergebnis auf der Platte.

Satz 2 fährt dasselbe mit zwei unabhängigen Prozessen (``multiprocessing``, Start
``spawn``), je gesondert für Fortschritt, Meldung und Teilbild.
"""
from __future__ import annotations

import multiprocessing
import threading
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from aiimaging import jobs

JOB = "vis-20261127000000-a08360"

#: Wie lange ein Gegenspieler mindestens warten muss, damit er als «gesperrt» gilt.
GESPERRT_S = 0.4
#: Obergrenze für jedes Warten, damit eine kaputte Sperre nicht den Lauf aufhängt.
GRENZE_S = 20.0


def _laufender_auftrag(ordner: Path) -> dict:
    satz = jobs.baue_job(job_id=JOB, art="render", params={})
    satz["status"] = jobs.STATUS_RUNNING
    satz["verlauf"].append({"status": jobs.STATUS_RUNNING, "zeit": satz["geaendert"]})
    jobs.schreibe_job(satz, ordner)
    return satz


def _pruefe_abbruch_auf_der_platte(ordner: Path) -> dict:
    """``cancelled`` auf der Platte, mit Zeitstempel und genau einem Verlaufseintrag."""
    satz = jobs.lies_job(JOB, ordner)
    assert satz["status"] == jobs.STATUS_CANCELLED
    abbrueche = [e for e in satz["verlauf"] if e["status"] == jobs.STATUS_CANCELLED]
    assert len(abbrueche) == 1, satz["verlauf"]
    assert satz["verlauf"][-1]["status"] == jobs.STATUS_CANCELLED
    assert abbrueche[0]["zeit"], "Der Abbruch trägt keinen Zeitstempel."
    assert satz["geaendert"] >= abbrueche[0]["zeit"]
    return satz


# --------------------------------------------------------------------------------------
# Satz 1: die Audit-Probe, umgestellt (zwei Fäden im selben Prozess)
# --------------------------------------------------------------------------------------

def test_spaeter_fortschritt_belebt_den_abbruch_nicht_wieder(tmp_path):
    _laufender_auftrag(tmp_path)
    gelesen, weiter = threading.Event(), threading.Event()
    original = jobs.lies_job

    def angehalten(*args, **kwargs):
        satz = original(*args, **kwargs)
        if threading.current_thread().name == "probe-progress":
            gelesen.set()
            assert weiter.wait(GRENZE_S)
        return satz

    ergebnis: dict = {}

    def abbrechen():
        ergebnis["satz"] = jobs.setze_status(JOB, jobs.STATUS_CANCELLED, tmp_path)

    with patch.object(jobs, "lies_job", angehalten):
        fortschritt = threading.Thread(
            name="probe-progress",
            target=lambda: jobs.vermerke_fortschritt(JOB, tmp_path, {"schritt": 1}))
        fortschritt.start()
        assert gelesen.wait(GRENZE_S)
        abbruch = threading.Thread(name="probe-cancel", target=abbrechen)
        abbruch.start()
        abbruch.join(GESPERRT_S)
        # Der Abbruch wartet, bis die angefangene Fortschrittsmeldung geschrieben ist.
        gesperrt = abbruch.is_alive()
        weiter.set()
        fortschritt.join(GRENZE_S)
        abbruch.join(GRENZE_S)

    assert not fortschritt.is_alive() and not abbruch.is_alive()
    assert ergebnis["satz"]["status"] == jobs.STATUS_CANCELLED   # «accepted cancellation»
    satz = _pruefe_abbruch_auf_der_platte(tmp_path)              # «after progress»
    assert gesperrt, "Der Abbruch lief zwischen Lesen und Schreiben des Fortschritts."
    # Der Fortschritt kam vor dem Abbruch an und bleibt stehen.
    assert satz["progress"] == {"schritt": 1}


def test_fortschritt_nach_dem_abbruch_wird_nicht_vermerkt(tmp_path):
    _laufender_auftrag(tmp_path)
    jobs.setze_status(JOB, jobs.STATUS_CANCELLED, tmp_path)
    vorher = jobs.lies_job(JOB, tmp_path)

    zurueck = jobs.vermerke_fortschritt(JOB, tmp_path, {"schritt": 2})

    assert zurueck["status"] == jobs.STATUS_CANCELLED
    assert jobs.lies_job(JOB, tmp_path) == vorher


@pytest.mark.parametrize("endzustand", [jobs.STATUS_DONE, jobs.STATUS_ERROR])
def test_fortschritt_auf_anderen_endzustaenden_wird_nicht_vermerkt(tmp_path, endzustand):
    _laufender_auftrag(tmp_path)
    jobs.setze_status(JOB, endzustand, tmp_path)
    vorher = jobs.lies_job(JOB, tmp_path)

    zurueck = jobs.vermerke_fortschritt(JOB, tmp_path, {"schritt": 2})

    assert zurueck["status"] == endzustand
    assert jobs.lies_job(JOB, tmp_path) == vorher


def test_meldung_nach_dem_abbruch_laesst_den_status_stehen(tmp_path):
    _laufender_auftrag(tmp_path)
    jobs.setze_status(JOB, jobs.STATUS_CANCELLED, tmp_path)

    jobs.vermerke_meldung(JOB, tmp_path, "Vom Nutzer abgebrochen.")

    satz = _pruefe_abbruch_auf_der_platte(tmp_path)
    assert satz["meldung"] == "Vom Nutzer abgebrochen."


def test_die_sperre_hinterlaesst_nichts_in_der_ablage(tmp_path):
    _laufender_auftrag(tmp_path)
    jobs.vermerke_fortschritt(JOB, tmp_path, {"schritt": 1})
    jobs.vermerke_meldung(JOB, tmp_path, "Knoten 1 von 3.")
    jobs.setze_status(JOB, jobs.STATUS_CANCELLED, tmp_path)
    jobs.vermerke_teilbild(JOB, tmp_path, "s__teilbild.png")
    assert [p.name for p in tmp_path.iterdir()] == [f"{JOB}{jobs.DATEI_ENDUNG}"]
    assert [s["job_id"] for s in jobs.liste_jobs(tmp_path)] == [JOB]


# --------------------------------------------------------------------------------------
# Satz 2: zwei unabhängige Prozesse mit gestaffelten Meldungen
# --------------------------------------------------------------------------------------

def _prozess_vermerk(art: str, ordner: str, gelesen, weiter) -> None:
    """Erster Prozess: liest, meldet «gelesen» und hält an, bis ``weiter`` kommt."""
    original = jobs.lies_job

    def angehalten(*args, **kwargs):
        satz = original(*args, **kwargs)
        gelesen.set()
        if not weiter.wait(GRENZE_S):
            raise SystemExit(3)
        return satz

    with patch.object(jobs, "lies_job", angehalten):
        if art == "fortschritt":
            jobs.vermerke_fortschritt(JOB, ordner, {"schritt": 1})
        elif art == "meldung":
            jobs.vermerke_meldung(JOB, ordner, "Knoten 2 von 3.")
        else:
            raise SystemExit(4)


def _prozess_abbruch(ordner: str, gelesen, fertig, teilbild: bool) -> None:
    """Zweiter Prozess, gestaffelt: bricht erst ab, wenn der erste gelesen hat."""
    if not gelesen.wait(GRENZE_S):
        raise SystemExit(3)
    jobs.setze_status(JOB, jobs.STATUS_CANCELLED, ordner)
    if teilbild:
        jobs.vermerke_teilbild(JOB, ordner, "s__teilbild.png")
    fertig.set()


def _zwei_prozesse(ordner: Path, art: str, *, teilbild: bool = False) -> bool:
    """Beide Prozesse fahren; gibt zurück, ob der Abbruch auf die Sperre warten musste."""
    ctx = multiprocessing.get_context("spawn")
    gelesen, weiter, fertig = ctx.Event(), ctx.Event(), ctx.Event()
    erster = ctx.Process(target=_prozess_vermerk, args=(art, str(ordner), gelesen, weiter))
    zweiter = ctx.Process(target=_prozess_abbruch,
                          args=(str(ordner), gelesen, fertig, teilbild))
    erster.start()
    zweiter.start()
    try:
        assert gelesen.wait(GRENZE_S), "Der erste Prozess hat nie gelesen."
        gesperrt = not fertig.wait(GESPERRT_S)
    finally:
        weiter.set()
        erster.join(GRENZE_S)
        zweiter.join(GRENZE_S)
    assert erster.exitcode == 0 and zweiter.exitcode == 0, (erster.exitcode,
                                                            zweiter.exitcode)
    return gesperrt


def test_zwei_prozesse_fortschritt(tmp_path):
    _laufender_auftrag(tmp_path)
    gesperrt = _zwei_prozesse(tmp_path, "fortschritt")
    satz = _pruefe_abbruch_auf_der_platte(tmp_path)
    assert gesperrt
    assert satz["progress"] == {"schritt": 1}

    # Ein dritter, später Fortschritt aus einem eigenen Prozess wird nicht mehr vermerkt.
    vorher = jobs.lies_job(JOB, tmp_path)
    ctx = multiprocessing.get_context("spawn")
    spaet = ctx.Process(target=jobs.vermerke_fortschritt,
                        args=(JOB, str(tmp_path), {"schritt": 9}))
    spaet.start()
    spaet.join(GRENZE_S)
    assert spaet.exitcode == 0
    assert jobs.lies_job(JOB, tmp_path) == vorher


def test_zwei_prozesse_meldung(tmp_path):
    _laufender_auftrag(tmp_path)
    gesperrt = _zwei_prozesse(tmp_path, "meldung")
    satz = _pruefe_abbruch_auf_der_platte(tmp_path)
    assert gesperrt
    assert satz["meldung"] == "Knoten 2 von 3."


def test_zwei_prozesse_teilbild(tmp_path):
    _laufender_auftrag(tmp_path)
    gesperrt = _zwei_prozesse(tmp_path, "fortschritt", teilbild=True)
    satz = _pruefe_abbruch_auf_der_platte(tmp_path)
    assert gesperrt
    assert satz["teilbild"] == "s__teilbild.png"
