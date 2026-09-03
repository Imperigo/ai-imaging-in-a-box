"""Die Aufträge im Repo werden geprüft wie Code — sie sind der einzige Draht zur Hardware.

Anlass, und er ist gezählt und nicht vermutet
---------------------------------------------
`CLAUDE.md` verlangt seit dem **22.08.2026**: *«Was der Worker wissen muss, steht in der
Auftragsdatei.»* Aus demselben Absatz stammt das Pflichtfeld ``worker`` — und **das ist in
`auftrag.pruefe_auftrag` gelandet, die Anweisung nicht.** Halb im Code, halb nur im Text.

Aufgefallen ist es bei der Triage der toten Kanten am 26.08.2026
(`docs/TOTE_KANTEN_TRIAGE_2026-08-26.md`, Abschnitt D.2): ``auftrag.baue_auftrag`` hat
keinen Aufrufer, Aufträge entstehen von Hand — und von Hand geschriebene Dateien prüft
niemand. Vier Aufträge waren seit dem Regeltag ohne ein Feld ``anweisung`` hinausgegangen,
und an demselben Tag hat sich das Format **zweimal still geändert** (``anweisung`` kam
dazu, ``rueckgabe`` wurde von einem Wörterbuch zu einer Liste), ohne dass die Bibliothek
davon erfuhr.

**Eine Hausregel ohne Wächter ist eine Bitte.**

Was hier ausdrücklich nicht geprüft wird
----------------------------------------
**Ob eine Anweisung gut ist.** Das kann keine Maschine, und der Versuch endete in diesem
Projekt schon einmal bei einem Treffer auf fünf Fehlalarme. Geprüft wird, ob sie
**vorhanden** ist und nicht bloss ein Stummel — mehr verspricht diese Datei nicht.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from aiimaging import auftrag as auftrag_modul

WURZEL = Path(__file__).resolve().parents[1]
OFFEN = WURZEL / "auftraege" / "offen"

#: Ab wann die Regel gilt, dass ein Auftrag seine Anweisung **in sich** trägt.
#: Owner-Wunsch, festgehalten in `CLAUDE.md`. Ältere Aufträge sind davon frei — sie
#: rückwirkend zu verurteilen hiesse, eine Regel auf eine Zeit anzuwenden, in der sie
#: nicht galt, und der Wächter fiele bei jedem Lauf auf etwas, das niemand mehr ändert.
REGEL_GILT_AB = "2026-08-22"

#: Wann ein Anweisungstext als Stummel gilt.
#:
#: **Gemessen, nicht gesetzt** (26.08.2026, über alle 46 Dateien in `auftraege/offen/`):
#:
#: * Seit dem Regeltag trägt der **kürzeste** Auftrag **2568** Zeichen Anweisung (n = 18).
#: * Davor gingen sie bis auf **207** Zeichen hinunter (n = 28).
#:
#: Die Regel hat also messbar etwas geändert. Die Schranke liegt bewusst bei weniger als
#: der **Hälfte** des kürzesten wirklichen Auftrags und beim **Fünffachen** des kürzesten
#: Stummels: Sie soll einen Platzhalter fangen, nicht einen knappen, aber vollständigen
#: Auftrag bedrängen. *Eine lange Anweisung ist damit nicht als gute nachgewiesen — nur
#: eine sehr kurze als unvollständige.*
ANWEISUNG_MINDESTZEICHEN = 1000


def _auftragsdateien() -> list[Path]:
    return sorted(OFFEN.glob("*.json"))


def _unbeantwortet() -> set[str]:
    """Die Kennungen, auf die noch jemand antworten soll — gegen den abgeleiteten Zustand.

    *Nicht gegen den Ordner:* `auftraege/offen/` führt auch die längst beantworteten.
    """
    return {a["auftrag_id"] for a in auftrag_modul.unerledigt(WURZEL)}


def _lies(pfad: Path) -> dict:
    return json.loads(pfad.read_text(encoding="utf-8"))


def _anweisungstext(satz: dict) -> str:
    """Die Anweisung, wo immer sie steht.

    Zwei Formen sind zugelassen und beide sind belegt: seit dem 26.08.2026 ein eigenes
    Feld ``anweisung`` mit ``beschreibung`` als Überschrift; davor der Fliesstext in
    ``beschreibung``. **Die ältere Form wird nicht nachträglich umgeschrieben** — vier der
    Aufträge, die sie benutzen, sind unbeantwortet unterwegs, und einen laufenden Auftrag
    umzuformatieren hiesse, die Frage zu ändern, während jemand daran arbeitet.
    """
    return str(satz.get("anweisung") or satz.get("beschreibung") or "")


def _erstellt_am(satz: dict) -> str:
    return str(satz.get("erstellt", ""))[:10]


def test_es_gibt_ueberhaupt_auftraege():
    """Ohne diese Zusicherung wäre die ganze Datei vakuumwahr.

    Ein Wächter über eine leere Dateiliste ist grün und bewacht nichts — genau der Fall,
    den `tools/vakuumprobe.py` in diesem Projekt sucht.
    """
    dateien = _auftragsdateien()
    assert len(dateien) >= 40, (
        f"Nur {len(dateien)} Auftragsdateien unter {OFFEN}. Wenn das Verzeichnis "
        f"umgezogen ist, prüft diese Datei ab sofort nichts mehr.")


@pytest.mark.parametrize("pfad", _auftragsdateien(), ids=lambda p: p.stem)
def test_jeder_auftrag_haelt_den_vertrag(pfad):
    """Dieselbe Prüfung, die `auftrag.baue_auftrag` beim Bauen anwendet — nur an der Datei.

    *Der Unterschied ist der ganze Zweck:* Die Prüfung gab es, aber sie lief nur auf dem
    Weg über die Bibliothek, und diesen Weg nimmt kein einziger Auftrag dieses Repos.
    """
    maengel = auftrag_modul.pruefe_auftrag(_lies(pfad))
    assert not maengel, f"{pfad.name}: " + "; ".join(maengel)


@pytest.mark.parametrize("pfad", _auftragsdateien(), ids=lambda p: p.stem)
def test_die_kennung_stimmt_mit_dem_dateinamen(pfad):
    """Sonst lässt sich eine Antwort ihrer Frage nicht zuordnen.

    Das Ergebnis kommt unter der Kennung zurück, die **im** Auftrag steht; gesucht wird es
    aber unter dem Dateinamen. Gehen die auseinander, liegt die Antwort da und gilt als
    ausstehend.
    """
    satz = _lies(pfad)
    assert satz.get("auftrag_id") == pfad.stem, (
        f"{pfad.name} trägt die Kennung {satz.get('auftrag_id')!r}.")


@pytest.mark.parametrize("pfad", _auftragsdateien(), ids=lambda p: p.stem)
def test_jeder_auftrag_sagt_was_zurueckkommen_soll(pfad):
    """``rueckgabe`` ist die halbe Anweisung.

    Ein Auftrag, der nicht sagt, was zurückkommen soll, bekommt das, was der Worker für
    naheliegend hält — und die Frage bleibt offen, obwohl gerechnet wurde. Zugelassen sind
    beide Formen: das Wörterbuch der älteren Aufträge und die Liste seit dem 26.08.2026.
    """
    satz = _lies(pfad)
    rueckgabe = satz.get("rueckgabe")
    assert isinstance(rueckgabe, (dict, list)) and rueckgabe, (
        f"{pfad.name}: 'rueckgabe' fehlt oder ist leer ({rueckgabe!r}).")

    # UND SEIT DEM 01.09.2026 REICHT DIE FORM NICHT MEHR.
    #
    # Der Satz oben — «Zugelassen sind beide Formen» — hat den Test fuer 42 Dateien
    # wirkungslos gemacht. Die Woerterbuchform ist naemlich die TRANSPORTANGABE (wohin,
    # nur Zahlen, ein allgemeiner Hinweis) und nennt keinen einzigen Rueckgabepunkt. Fuenf
    # offene Auftraege gingen so hinaus; ihr Abschnitt «WAS ZURUECKKOMMEN SOLL» lautete
    # `verzeichnis / nur_zahlen / hinweis`. Drei davon lagen bei den beiden Adressaten,
    # die noch nie geantwortet haben.
    #
    # *Eine Form zu pruefen ist nicht dasselbe, wie ihren Inhalt zu pruefen.*
    #
    # Die Schaerfe gilt nur fuer UNBEANTWORTETE Auftraege: Ein beantworteter wird nicht
    # mehr gelesen, und seine Form nachtraeglich zu aendern hiesse, an einer Frage zu
    # arbeiten, die niemand mehr stellt.
    if satz.get("auftrag_id") not in _unbeantwortet():
        return
    punkte = auftrag_modul.rueckgabepunkte(satz)
    assert punkte, (
        f"{pfad.name} ist unbeantwortet und nennt keinen einzelnen Rueckgabepunkt — "
        f"nur die Transportangabe {sorted(rueckgabe)!r}. Der Empfaenger liest damit "
        f"unter «WAS ZURUECKKOMMEN SOLL» die Schluesselnamen und erfaehrt nicht, woran "
        f"er erkennt, dass er fertig ist.")


@pytest.mark.parametrize("pfad", _auftragsdateien(), ids=lambda p: p.stem)
def test_auftraege_ab_dem_regeltag_tragen_ihre_anweisung_in_sich(pfad):
    """Die Hausregel vom 22.08.2026, zum ersten Mal maschinell.

    Geprüft wird gegen das **Erstelldatum im Auftrag** und nicht gegen das Datum in der
    Kennung: Zwei Aufträge dieses Repos sind nach Mitternacht entstanden und tragen darum
    eine Kennung vom Vortag. *Ein Wächter, der an einer solchen Kleinigkeit fällt, wird
    abgeschaltet und bewacht danach gar nichts.*
    """
    satz = _lies(pfad)
    if _erstellt_am(satz) < REGEL_GILT_AB:
        pytest.skip(f"vor {REGEL_GILT_AB} erstellt — die Regel galt noch nicht")
    text = _anweisungstext(satz)
    assert len(text) >= ANWEISUNG_MINDESTZEICHEN, (
        f"{pfad.name}: Die Anweisung hat {len(text)} Zeichen, gefordert sind "
        f"{ANWEISUNG_MINDESTZEICHEN}. Was zu tun ist, in welcher Reihenfolge, was "
        f"zurückkommen soll und was NICHT getan werden soll — das gehört in die "
        f"Auftragsdatei und nicht in den Chat.")


def test_der_regeltag_trennt_wirklich_zwei_gruppen():
    """Die Gegenprobe: Ohne sie wäre `REGEL_GILT_AB` ein Datum ohne Wirkung.

    Läge auch vor dem Regeltag jeder Auftrag über der Schranke, prüfte der Test darüber
    nichts — er wäre grün, weil alles grün ist, und niemand wüsste es. Gemessen am
    26.08.2026: davor hinunter bis 207 Zeichen, danach nicht unter 2568.
    """
    davor, danach = [], []
    for pfad in _auftragsdateien():
        satz = _lies(pfad)
        (danach if _erstellt_am(satz) >= REGEL_GILT_AB else davor).append(
            len(_anweisungstext(satz)))
    assert davor and danach, "Eine der beiden Gruppen ist leer — der Vergleich trägt nicht."
    assert min(davor) < ANWEISUNG_MINDESTZEICHEN <= min(danach), (
        f"Die Schranke trennt nicht mehr: vor dem Regeltag mindestens {min(davor)} "
        f"Zeichen, danach mindestens {min(danach)}, Schranke {ANWEISUNG_MINDESTZEICHEN}. "
        f"Wenn das kein Fehler ist, gehört die Schranke neu gemessen — nicht verschoben.")


def test_die_bibliothek_kann_das_geltende_format_bauen():
    """Der Grund, warum D.2 überhaupt auffiel.

    `baue_auftrag` hat keinen Aufrufer, und darum ist vier Tage lang niemandem aufgefallen,
    dass sie das seit dem 22.08.2026 geltende Format gar nicht erzeugen konnte. Diese
    Zusicherung hält die Bibliothek an dem fest, was die Dateien wirklich tragen.
    """
    satz = auftrag_modul.baue_auftrag(
        auftrag_id="auf-20260826-99", art="qa", beschreibung="Überschrift",
        worker=auftrag_modul.WORKER_LOCAL, anweisung="x" * ANWEISUNG_MINDESTZEICHEN)
    assert satz["anweisung"] == "x" * ANWEISUNG_MINDESTZEICHEN
    assert not auftrag_modul.pruefe_auftrag(satz)


def test_eine_leere_anweisung_erzeugt_kein_feld():
    """Ein leeres ``anweisung`` wäre schlimmer als gar keins — es sähe gefüllt aus."""
    satz = auftrag_modul.baue_auftrag(
        auftrag_id="auf-20260826-98", art="qa", beschreibung="Überschrift", anweisung="   ")
    assert "anweisung" not in satz


# ======================================================================================
# Der Rang ist eine Reihenfolge, und eine Reihenfolge hat keine Doppelten
# ======================================================================================
#
# Am 02.09.2026 trugen zwei offene `local`-Auftraege beide den Rang 3 — die HomeStation
# hatte den Rang uebernommen und ihn ohne Kenntnis der bestehenden Reihe vergeben. Bei
# `--hoechstens 1` entscheidet dann wieder der Dateiname, welcher zuerst laeuft: genau
# das, wogegen es den Rang gibt.

def test_kein_rang_kommt_bei_einem_adressaten_zweimal_vor():
    """**Zwei Auftraege auf demselben Platz sind keine Reihenfolge, sondern eine
    Behauptung.**"""
    from collections import Counter
    for worker in auftrag_modul.WORKER:
        raenge = [a.get("rang") for a in auftrag_modul.unerledigt(WURZEL)
                  if a.get("worker") == worker and a.get("rang") is not None]
        doppelt = [r for r, n in Counter(raenge).items() if n > 1]
        assert not doppelt, f"{worker}: Rang {doppelt} mehrfach vergeben"


def test_jeder_offene_auftrag_traegt_einen_rang():
    """*Der Rang ist freiwillig im Vertrag* — die rund sechzig beantworteten Auftraege
    haben keinen, und sie nachtraeglich zu nummerieren hiesse, eine Zahl zu erfinden.

    **Fuer die OFFENEN ist er es nicht.** Wer auf eine Antwort wartet, sagt auch, worauf
    zuerst — sonst waehlt der Zufall des Dateinamens, und bei `--hoechstens 1` waehlt er
    jeden Takt aufs Neue denselben.
    """
    ohne = [a["auftrag_id"] for a in auftrag_modul.unerledigt(WURZEL)
            if a.get("rang") is None]
    assert not ohne, (
        f"{len(ohne)} offene Auftraege ohne Rang: {ohne[:6]}. Wer einen Auftrag stellt, "
        f"sagt auch, wo er in der Reihe steht.")


def test_die_raenge_sind_lueckenlos_von_eins_an():
    """Eine Lücke ist kein Fehler der Rechnung, aber eine Frage: *Ist da einer
    herausgefallen?* Lückenlos zu nummerieren beantwortet sie, bevor sie gestellt wird."""
    for worker in auftrag_modul.WORKER:
        raenge = sorted(a.get("rang") for a in auftrag_modul.unerledigt(WURZEL)
                        if a.get("worker") == worker and a.get("rang") is not None)
        if not raenge:
            continue
        assert raenge == list(range(1, len(raenge) + 1)), (worker, raenge)
