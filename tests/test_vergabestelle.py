"""Wer vergibt Rang und Laufnummer, wenn vier Lanes in eine Warteschlange schreiben?

Der Anlass, und er ist an einem Abend zweimal angefallen
--------------------------------------------------------
Am 09.09.2026 legte eine fremde Lane ``auf-20260907-86`` mit **Rang 2** ab, den
``auf-20260907-82`` schon trug. Eine Stunde später legte dieselbe Lane
``auf-20260907-87`` ab — **Rang 3**, den unser Auftrag inzwischen trug, **und dieselbe
Laufnummer 87** wie unser eigener von jenem Tag. Beide Male wurde ``main`` rot.

Am 25.08. war es schon einmal so: ``auf-20260823-38`` und ``auf-20260824-38``, und der
Merksatz stand danach im Plan — *von Hand gezählt heisst irgendwann doppelt.*

Die Diagnose, und sie trifft nicht die fremde Lane
---------------------------------------------------
``tests/test_auftraege.py`` **verlangt** eine lückenlose Rangreihe je Adressat und
**sagte niemandem**, welcher Rang frei ist. ``auftrag.neue_auftrag_id`` steht seit Phase 0
da und **formatierte nur** — sie kannte den Bestand nicht und hätte die doppelte
Laufnummer auch dort nicht verhindert, wo ich sie benutzt hätte.

> **Eine Vorschrift ohne Vergabestelle verlagert die Arbeit auf den, der zuletzt kommt.**

Darum wird die Kollision hier **an der Quelle** beseitigt statt hinterher gemeldet. Was
ausdrücklich *nicht* gebaut wird: eine automatische Umnummerierung fremder Dateien. Der
Rang ist das Dringlichkeitssignal einer Lane, und ihn zu überschreiben wäre derselbe
Eingriff, den ich am 09.09. zweimal abgelehnt habe.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from aiimaging import auftrag as auf


def _ablage(wurzel: Path, offen: dict[str, dict] | None = None,
            ergebnisse: tuple[str, ...] = ()) -> Path:
    """Ein Auftragsordner mit echten Dateien — nicht mit einer Liste im Speicher.

    Die Vergabestelle liest die **Platte**; eine Attrappe darüber prüfte nur unsere
    eigene Nachbildung.
    """
    (wurzel / auf.VERZ_OFFEN).mkdir(parents=True, exist_ok=True)
    (wurzel / auf.VERZ_ERGEBNISSE).mkdir(parents=True, exist_ok=True)
    for kennung, satz in (offen or {}).items():
        (wurzel / auf.VERZ_OFFEN / f"{kennung}.json").write_text(
            json.dumps(satz), encoding="utf-8")
    for kennung in ergebnisse:
        (wurzel / auf.VERZ_ERGEBNISSE / f"{kennung}.json").write_text(
            json.dumps({"auftrag_id": kennung, "status": "ok"}), encoding="utf-8")
    return wurzel


def _satz(kennung: str, worker: str = "local", rang: int | None = None) -> dict:
    satz = {"schema": auf.SCHEMA_AUFTRAG, "auftrag_id": kennung, "art": "qa",
            "worker": worker, "beschreibung": "Eine Frage.",
            "anweisung": "Eine Anweisung.", "erstellt": "2026-09-09T00:00:00Z",
            "geometrie": {"synthetisch": True, "pfad": None,
                          "erzeugen_mit": "python3 tools/make_test_ifc.py build/t.ifc"},
            "params": {}, "auflagen": ["keine"], "rueckgabe": ["V1 nichts"]}
    if rang is not None:
        satz["rang"] = rang
    return satz


# ------------------------------------------------------------- die Laufnummer

def test_der_fall_vom_09_09_2026_liefert_88_und_nicht_87(tmp_path):
    """Genau die Lage, in der ``main`` rot wurde — und sie muss ausgehen.

    Ein Bestand, in dem ``auf-20260907-87`` einer fremden Lane liegt, darf für uns
    **nicht** wieder 87 vergeben, auch nicht unter einem anderen Datum.

    **Die Zahlen hier sind fest und folgen nicht dem echten Ordner.** Beim dritten
    Zusammenstoss desselben Abends hat ein zu breiter Rename sie mitgezogen und diese
    Probe rot gemacht — *eine Probe, die den historischen Fall festhält, darf sich nicht
    mit dem heutigen Bestand ändern, sonst hält sie ihn nicht mehr fest.*
    """
    _ablage(tmp_path, {"auf-20260907-86": _satz("auf-20260907-86"),
                       "auf-20260907-87": _satz("auf-20260907-87")})
    assert auf.naechste_laufnummer(tmp_path) == 88
    assert auf.neue_auftrag_id("20260909", repo_wurzel=tmp_path) == "auf-20260909-88"


def test_eine_beantwortete_nummer_ist_vergeben(tmp_path):
    """Sonst lägen zwei verschiedene Fragen unter einem Namen.

    Und die Antwort auf die eine zeigte auf die andere — dieselbe Verwechslung wie bei
    einem Weiterleitungsvermerk, der als Antwort gezählt wurde (28.08.).
    """
    _ablage(tmp_path, {"auf-20260909-03": _satz("auf-20260909-03")},
            ergebnisse=("auf-20260901-09",))
    assert auf.naechste_laufnummer(tmp_path) == 10, (
        "Die 09 ist beantwortet und damit vergeben — sie steht nur nicht mehr in `offen/`.")


def test_datumsuebergreifend_gezaehlt_und_nicht_je_tag(tmp_path):
    """Die Kennung trägt ein Datum; gezählt wird über alle Tage.

    Am 25.08. trugen ``auf-20260823-38`` und ``auf-20260824-38`` dieselbe Nummer an
    verschiedenen Tagen. Wer je Tag zählt, baut genau diesen Fall wieder.
    """
    _ablage(tmp_path, {"auf-20260823-38": _satz("auf-20260823-38"),
                       "auf-20260901-12": _satz("auf-20260901-12")})
    assert auf.naechste_laufnummer(tmp_path) == 39


def test_ein_leerer_bestand_beginnt_bei_eins(tmp_path):
    _ablage(tmp_path)
    assert auf.naechste_laufnummer(tmp_path) == 1
    assert auf.neue_auftrag_id("20260909", repo_wurzel=tmp_path) == "auf-20260909-01"


def test_ohne_repo_bleibt_die_kennung_wortgleich_wie_seit_phase_0(tmp_path):
    """Kein bestehender Aufrufer ändert sein Verhalten.

    Die Vergabestelle ist ein **Angebot** an den, der einen Auftrag schreibt, und keine
    stille Umstellung — sonst wären alle Tests, die eine feste Kennung erwarten, plötzlich
    von einem Verzeichnisinhalt abhängig.
    """
    _ablage(tmp_path, {"auf-20260907-87": _satz("auf-20260907-87")})
    assert auf.neue_auftrag_id("20260909", laufnummer=3) == "auf-20260909-03"


def test_eine_mitgegebene_nummer_ist_die_untergrenze_und_nicht_die_antwort(tmp_path):
    """Wer 5 verlangt und einen Bestand bis 87 hat, bekommt 88 — nicht 5.

    *Eine Vergabestelle, die eine belegte Nummer durchwinkt, weil jemand sie gewünscht
    hat, ist keine.*
    """
    _ablage(tmp_path, {"auf-20260907-87": _satz("auf-20260907-87")})
    assert auf.neue_auftrag_id("20260909", laufnummer=5,
                               repo_wurzel=tmp_path) == "auf-20260909-88"


def test_fremde_dateinamen_bringen_die_zaehlung_nicht_durcheinander(tmp_path):
    """Was nicht wie eine Kennung aussieht, wird nicht als eine gelesen.

    Im Ordner liegen auch ``zustellung.json`` und Handnotizen; eine Zählung, die daran
    stolpert, wäre schlimmer als keine.
    """
    _ablage(tmp_path, {"auf-20260909-07": _satz("auf-20260909-07")})
    (tmp_path / auf.VERZ_OFFEN / "notiz.json").write_text("{}", encoding="utf-8")
    (tmp_path / auf.VERZ_OFFEN / "auf-vis-20260826-16.json").write_text(
        "{}", encoding="utf-8")
    assert auf.naechste_laufnummer(tmp_path) == 8


# ------------------------------------------------------------------- der Rang

def test_der_naechste_rang_schliesst_die_reihe_lueckenlos_an(tmp_path):
    """Genau das, was ``tests/test_auftraege.py`` verlangt — und bisher nicht anbot."""
    _ablage(tmp_path, {f"auf-20260909-0{i}": _satz(f"auf-20260909-0{i}", rang=i)
                       for i in (1, 2, 3)})
    assert auf.naechster_rang("local", tmp_path) == 4


def test_eine_luecke_wird_gefuellt_und_nicht_umgangen(tmp_path):
    """Der kleinste **freie** Rang, nicht der grösste plus eins.

    Sonst entstünde bei jeder beantworteten Zwischennummer eine Lücke — und der Wächter,
    der Lückenlosigkeit verlangt, fiele über die eigene Vergabestelle.
    """
    _ablage(tmp_path, {"auf-20260909-01": _satz("auf-20260909-01", rang=1),
                       "auf-20260909-03": _satz("auf-20260909-03", rang=3)})
    assert auf.naechster_rang("local", tmp_path) == 2


def test_jeder_adressat_hat_seine_eigene_reihe(tmp_path):
    """`local` und `cloud` teilen sich keine Ränge — sie sind zwei Warteschlangen."""
    _ablage(tmp_path, {"auf-20260909-01": _satz("auf-20260909-01", "local", 1),
                       "auf-20260909-02": _satz("auf-20260909-02", "local", 2),
                       "auf-20260909-03": _satz("auf-20260909-03", "cloud", 1)})
    assert auf.naechster_rang("local", tmp_path) == 3
    assert auf.naechster_rang("cloud", tmp_path) == 2
    assert auf.naechster_rang("ui", tmp_path) == 1


def test_ein_auftrag_ohne_rang_belegt_keinen(tmp_path):
    """``rang`` ist freiwillig. Ein fehlender darf die Reihe nicht verschieben."""
    _ablage(tmp_path, {"auf-20260909-01": _satz("auf-20260909-01", rang=1),
                       "auf-20260909-02": _satz("auf-20260909-02")})
    assert auf.naechster_rang("local", tmp_path) == 2


def test_die_vergabe_und_der_waechter_sagen_dasselbe(tmp_path):
    """Die Gegenprobe von der anderen Seite — sonst prüft die Zahl sich selbst.

    Wer die vergebenen Ränge nimmt und den vergebenen anhängt, muss eine lückenlose Reihe
    von eins an bekommen. Genau das ist die Zusicherung, an der ``main`` heute zweimal
    zerbrochen ist.
    """
    _ablage(tmp_path, {f"auf-20260909-0{i}": _satz(f"auf-20260909-0{i}", rang=i)
                       for i in (1, 2, 3, 4)})
    raenge = sorted([a["rang"] for a in auf.unerledigt(tmp_path)]
                    + [auf.naechster_rang("local", tmp_path)])
    assert raenge == list(range(1, len(raenge) + 1))


# ------------------------------------------- die Auskunft steht dort, wo gezaehlt wird

def test_der_einbau_stand_nennt_die_naechste_freie_nummer_und_den_rang():
    """Eine Vergabestelle, die man kennen müsste, um sie zu finden, findet niemand.

    `tools/einbau.py` wird ohnehin gelesen, bevor jemand einen Auftrag schreibt — die
    Auskunft gehört in **die** Zeile und nicht in eine Funktion daneben.

    Gefahren wird gegen das **echte** Repo und nicht gegen einen gebauten Ordner: Der
    Bericht braucht das Einbau-Blatt, und eines nachzubauen hiesse, die eigene
    Nachbildung zu prüfen. Verglichen wird darum nicht mit festen Zahlen, sondern mit dem,
    was die beiden Funktionen sagen — *die Frage ist, ob die Auskunft ankommt, nicht wie
    sie heute lautet.*
    """
    from aiimaging import einbau

    wurzel = Path(__file__).resolve().parents[1]
    vergabe = einbau.bericht(wurzel)["vergabe"]

    assert vergabe["laufnummer"] == auf.naechste_laufnummer(wurzel)
    assert vergabe["laufnummer"] > 1, (
        "In einem Repo mit achtzig abgelegten Auftraegen kann die naechste freie Nummer "
        "nicht die erste sein — dann liest die Zaehlung den Ordner nicht.")
    for worker in (auf.WORKER_LOCAL, auf.WORKER_CLOUD, auf.WORKER_UI):
        assert vergabe["raenge"][worker] == auf.naechster_rang(worker, wurzel)


def test_die_gemeldete_nummer_ist_wirklich_frei():
    """Die Gegenprobe von der anderen Seite — sonst prüft die Auskunft sich selbst.

    Gelesen werden die Dateinamen im Ordner, nicht die Funktion noch einmal.
    """
    wurzel = Path(__file__).resolve().parents[1]
    frei = auf.naechste_laufnummer(wurzel)
    belegt = {p.stem.rsplit("-", 1)[-1]
              for verz in (auf.VERZ_OFFEN, auf.VERZ_ERGEBNISSE)
              for p in (wurzel / verz).glob("auf-*.json")}
    assert f"{frei:02d}" not in belegt and str(frei) not in belegt
