"""Die Naht zum ArchitekturKosmos — geprüft ohne Netz, ohne GPU, ohne Nachbarsystem.

``kosmo_naht.py`` ist aus den zwölf Befunden von ``docs/OEKOSYSTEM_2026-08-18.md``
(Kapitel 7) entstanden. Der Satz, der sie alle teuer macht, steht dort so:

    **KosmoOrbit verdrahtet Knoten über Feldnamen-Gleichheit — und meldet keinen Fehler,
    wenn die Kante nicht entsteht.**

Eine Übersetzung, die einen Fehler still verschluckt, ist darum schlimmer als keine.
Diese Datei prüft in fünf Gruppen, dass sie es nicht tut:

1. **Das Token bleibt, wo es hingehört: nirgends.** Der Owner-Entscheid vom 18.08.2026
   ist nur so viel wert, wie er ausführbar ist — geprüft wird deshalb am ganzen
   serialisierten Auftragssatz und an der geschriebenen Datei, nicht an einem Feld.
2. **Die Auflösung** — der Typunterschied (`int` gegen `"BxH"`), den eine blosse
   Umbenennung nicht gelöst hätte, samt benanntem Verlust beim Vorgabewert
   ``"1920x1440"`` des Ökosystems.
3. **Die Kennung** ist einseitig unverträglich, und sie wird nicht umgeschrieben. Das
   ist Absicht und leicht zu „reparieren"; der Test hier soll rot werden, wenn es jemand
   tut.
4. **Die Feldübersetzung** in beide Richtungen, mitsamt der Frage, was ein Rundlauf
   verliert und ob er es sagt.
5. **``pruefe_kanten``** — der Unterschied zwischen „passt nicht" und „passt nicht ohne
   Übersetzung" ist der ganze Zweck des Moduls.

Alle Daten sind synthetisch (Regel 3). Es wird nichts importiert ausser stdlib, pytest
und der Bibliothek selbst.
"""
from __future__ import annotations

import json

import pytest

from aiimaging import jobs, kosmo_naht
from aiimaging.jobs import TOKEN_PRAEFIX
from aiimaging.kosmo_naht import (
    FREMDES_JOB_ID_MUSTER,
    JOB_FELDER,
    MCP_FELDER,
    NahtError,
    als_kosmo_auftrag,
    aufloesung_zu_resolution,
    aus_kosmo_auftrag,
    pruefe_kanten,
    resolution_zu_aufloesung,
)

#: Ein Token, wie es der Mensch am Cockpit erteilt — dieselbe Form wie in ``test_jobs``.
GUELTIG = TOKEN_PRAEFIX + "nutzer-hat-bestaetigt"

#: Unsere Kennung: vierzehnstellige Zeit. Sie besteht **auch** deren Muster.
KENNUNG = "vis-20260818120000-abc123"

#: Deren Kennung: zehnstellige Unix-Zeit. Sie besteht unser Muster **nicht**.
IHRE_KENNUNG = "vis-1755530000-a1b2c3"

#: Synthetische Auftragsparameter (Regel 3: nichts, was nach Büro, Kunde oder Projekt
#: klingt). ``aufloesung`` ist absichtlich dabei — sie ist der teuerste der zwölf Befunde.
PARAMS = {"glb_path": "/synthetisch/wuerfel.glb", "up_axis": "Y", "aufloesung": 512}

#: Die Felder, die der Vertrag ``VIS-JOB-INFRA-KONTRAKT-2026-06-17`` in der Auftragsdatei
#: nennt (docs/OEKOSYSTEM_2026-08-18.md, Kap. 7.3).
VERTRAGSFELDER = {
    "job_id", "kind", "status", "created_at", "approval_token", "idle_window_only",
    "params", "progress", "phase", "outputs", "error",
}


def _unser_satz(*, token=None, **rest) -> dict:
    """Ein Auftragssatz, wie ihn ``jobs.baue_job`` liefert — die Vorbedingung fast überall."""
    return jobs.baue_job(job_id=KENNUNG, art="depth", params=PARAMS,
                         approval_token=token, **rest)


def _ihr_satz(**rest) -> dict:
    """Ein Auftragssatz in deren Feldern, von Hand gebaut — so käme er von drüben herein."""
    satz = {
        "job_id": IHRE_KENNUNG,
        "kind": "render",
        "status": "awaiting_approval",
        "created_at": "2026-08-18T12:00:00+00:00",
        "updated_at": "2026-08-18T12:00:00+00:00",
        "idle_window_only": True,
        "params": {"resolution": "1920x1440", "up_axis": "Z"},
        "progress": 0.0,
        "phase": "queued",
        "outputs": None,
        "error": None,
    }
    satz.update(rest)
    return satz


# --------------------------------------------------------------------------------------
# 1 · Das Token bleibt, wo es hingehört: nirgends
# --------------------------------------------------------------------------------------

def test_ohne_token_traegt_der_uebersetzte_satz_keines():
    """Die Vorgabe ist ``None`` — und zwar als **Feld**, nicht als Auslassung.

    Ein fehlendes ``approval_token`` liesse den Leser rätseln, ob wir es vergessen haben.
    Ein leeres sagt: Wir führen es, und es ist keines erteilt.
    """
    fremd = als_kosmo_auftrag(_unser_satz())

    assert "approval_token" in fremd
    assert fremd["approval_token"] is None
    assert TOKEN_PRAEFIX not in json.dumps(fremd, ensure_ascii=False)


def test_mit_token_steht_es_nur_im_uebersetzten_satz():
    """Der Augenblick des Übergangs: aus dem Gedächtnis des Aufrufers in den fremden Satz."""
    unser = _unser_satz()

    fremd = als_kosmo_auftrag(unser, approval_token=GUELTIG)

    assert fremd["approval_token"] == GUELTIG
    assert TOKEN_PRAEFIX not in json.dumps(unser, ensure_ascii=False), (
        "Der übergebene Satz wurde verändert — das Token ist auf unsere Seite gelaufen."
    )


def test_das_token_steht_nie_in_unserem_auftragssatz():
    """**Der wichtigste Test dieser Datei.**

    Geprüft wird über den ganzen serialisierten Satz und nicht über ein einzelnes Feld:
    Ein Token, das irgendwo in ``params``, ``verlauf`` oder einem später ergänzten Feld
    landete, wäre über eine Feldprüfung unsichtbar. Beide Wege zur Freigabe werden
    abgedeckt — das Token beim Bauen und das Token bei ``freigeben``.
    """
    sofort = jobs.baue_job(job_id=KENNUNG, art="depth", params=PARAMS,
                           approval_token=GUELTIG)

    assert sofort["status"] == jobs.STATUS_QUEUED
    assert sofort["freigegeben"] is True
    assert TOKEN_PRAEFIX not in json.dumps(sofort, ensure_ascii=False)


def test_das_token_steht_auch_nach_freigeben_nicht_im_satz(tmp_path):
    """Der zweite Weg nach ``queued``: die nachträgliche Freigabe."""
    jobs.schreibe_job(_unser_satz(), tmp_path)

    nachher = jobs.freigeben(KENNUNG, GUELTIG, tmp_path)

    assert nachher["status"] == jobs.STATUS_QUEUED
    assert nachher["freigegeben"] is True
    assert TOKEN_PRAEFIX not in json.dumps(nachher, ensure_ascii=False)


def test_die_geschriebene_auftragsdatei_enthaelt_kein_token(tmp_path):
    """Der Beweis am Dateisystem — die Zusage gilt der Platte, nicht dem Speicher.

    Geprüft wird der rohe Text **jeder** Datei im Verzeichnis, nicht der gelesene Satz:
    Wer die Zusage nur über ``lies_job`` prüft, prüft die Serialisierung nicht mit.
    """
    jobs.schreibe_job(jobs.baue_job(job_id=KENNUNG, art="depth", params=PARAMS,
                                    approval_token=GUELTIG), tmp_path)
    zweite = "vis-20260818120001-abc124"
    jobs.schreibe_job(jobs.baue_job(job_id=zweite, art="depth", params=PARAMS), tmp_path)
    jobs.freigeben(zweite, GUELTIG, tmp_path)

    dateien = sorted(tmp_path.iterdir())

    assert len(dateien) == 2, f"unerwartete Reste im Verzeichnis: {dateien}"
    for datei in dateien:
        roh = datei.read_text(encoding="utf-8")
        assert TOKEN_PRAEFIX not in roh, f"Token in {datei.name} gelandet"
        assert json.loads(roh)["freigegeben"] is True


#: Beinahe-Token, jedes ein realistischer Fehlgriff (dieselbe Liste wie in ``test_jobs``,
#: aus demselben Grund: ``als_kosmo_auftrag`` prüft ausdrücklich mit ``jobs``' Massstab).
UNBRAUCHBARE_TOKEN = [
    ("leer", ""),
    ("nur das Präfix", TOKEN_PRAEFIX),
    ("Präfix mit Leerzeichen-Rest", TOKEN_PRAEFIX + "   "),
    ("fremdes Wort", "FOO"),
    ("kleingeschrieben", "confirmed_render_ja"),
    ("Präfix nicht am Anfang", "bitte " + TOKEN_PRAEFIX + "ja"),
    ("kein str", 1),
    ("bool", True),
]


@pytest.mark.parametrize("name, token", UNBRAUCHBARE_TOKEN,
                         ids=[n for n, _ in UNBRAUCHBARE_TOKEN])
def test_unbrauchbares_token_wird_abgewiesen_statt_weitergereicht(name, token):
    """Ein durchgereichtes Beinahe-Token erzeugte drüben einen Auftrag, der ohne
    erkennbaren Grund liegen bleibt — genau die Fehlerklasse aus Kap. 7.2."""
    with pytest.raises(NahtError, match="approval_token"):
        als_kosmo_auftrag(_unser_satz(), approval_token=token)


def test_gegenprobe_ein_gueltiges_token_kommt_durch():
    """Ohne diese Gegenprobe bewiese der Test darüber nur, dass gar nichts durchkommt."""
    fremd = als_kosmo_auftrag(_unser_satz(), approval_token=TOKEN_PRAEFIX + "x")

    assert fremd["approval_token"] == TOKEN_PRAEFIX + "x"


def test_der_benannte_preis_ist_echt(tmp_path):
    """Der Modul-Docstring nennt den Preis; hier steht er als ausführbarer Satz.

    Der **übersetzte** Satz ist eine Datei mit einem Token darin, sobald ihn jemand
    schreibt — und er ist schreibbar, weil er ``job_id`` und einen bekannten ``status``
    trägt. Die Naht macht die Weitergabe möglich und nicht unvermeidlich; dieser Test
    hält fest, wo die Entscheidung liegt: beim Schreibenden, nicht in einer Vorgabe.
    """
    fremd = als_kosmo_auftrag(_unser_satz(token=GUELTIG), approval_token=GUELTIG)

    pfad = jobs.schreibe_job(fremd, tmp_path)

    assert TOKEN_PRAEFIX in pfad.read_text(encoding="utf-8"), (
        "Der Preis ist im Docstring benannt — verschwindet er, ist der Docstring falsch."
    )


def test_ein_token_in_params_wird_abgewiesen(tmp_path):
    """**Die Restlücke der Token-Regel — geschlossen am 18.08.2026.**

    `jobs.baue_job` kopierte `params` unbesehen, `schreibe_job` schrieb sie. Wer das Token
    als *Parameter* durchreichte, schrieb es damit in die Auftragsdatei — und
    `freigegeben` blieb trotzdem `False`. **Das Schlimmste beider Welten:** Die Befugnis
    lag offen, und wirken tat sie nicht.

    Der Weg dorthin war der normale, nicht der ausgefallene: Der MCP-Vertrag des
    Ökosystems führt `owner_approval_token` als **Eingabefeld**, und Eingabefelder landen
    bei uns in `params`.

    Geprüft wird auf **beides** — den Schlüsselnamen und den Wert. Nur eines von beidem
    liesse die jeweils andere Hälfte offen.
    """
    for params, was in (
            ({"approval_token": jobs.TOKEN_PRAEFIX + "ja"}, "unser Schlüsselname"),
            ({"owner_approval_token": jobs.TOKEN_PRAEFIX + "ja"}, "ihr Schlüsselname"),
            ({"harmlos": jobs.TOKEN_PRAEFIX + "versteckt"}, "Wert unter harmlosem Namen"),
            ({"tief": {"drin": [jobs.TOKEN_PRAEFIX + "x"]}}, "verschachtelt"),
    ):
        with pytest.raises(jobs.JobError) as fehler:
            jobs.baue_job(job_id=jobs.neue_job_id(), art="render", params=params)
        assert "Token" in str(fehler.value), was

    # Gegenprobe: gewöhnliche Parameter gehen durch. Ohne sie wäre der Test auch grün,
    # wenn `baue_job` jeden Parametersatz abwiese.
    satz = jobs.baue_job(job_id=jobs.neue_job_id(), art="render",
                         params={"aufloesung": 512, "prompt": "haus"})
    assert satz["params"]["aufloesung"] == 512



def test_der_vorgabewert_des_oekosystems_ist_der_normalfall():
    """``"1920x1440"`` ist die Vorgabe drüben — also der Fall, der wirklich eintritt.

    Er ist nicht quadratisch, unser Feld kennt nur eine Kantenlänge. Genommen wird die
    kleinere: Wer ein Bild in eine kleinere Fläche zwingt, verliert Rand; wer es
    vergrössert, erfindet Fläche. Der Hinweis muss **beide** Kanten nennen, sonst kann
    niemand nachrechnen, was verloren ging.
    """
    gedeutet = resolution_zu_aufloesung("1920x1440")

    assert gedeutet["aufloesung"] == 1440
    assert gedeutet["breite"] == 1920
    assert gedeutet["hoehe"] == 1440
    assert gedeutet["verlustfrei"] is False
    assert gedeutet["hinweis"] is not None
    assert "1920" in gedeutet["hinweis"] and "1440" in gedeutet["hinweis"]


def test_quadratische_aufloesung_ist_verlustfrei_und_schweigt():
    """Kein Verlust, kein Hinweis — ein Hinweis ohne Anlass stumpft die anderen ab."""
    gedeutet = resolution_zu_aufloesung("512x512")

    assert gedeutet["aufloesung"] == 512
    assert gedeutet["verlustfrei"] is True
    assert gedeutet["hinweis"] is None


@pytest.mark.parametrize("wert", ["1920", "axb", "", 1920, None, "1920x", "x1440",
                                  "1920x1440x2", "0x0", "-5x5"], ids=repr)
def test_unlesbare_resolution_wird_abgewiesen(wert):
    """Nicht raten. Eine geratene Auflösung rendert still in der falschen Grösse — genau
    das, was Kap. 7.2 als teuersten der zwölf Befunde nennt."""
    with pytest.raises(NahtError, match="resolution"):
        resolution_zu_aufloesung(wert)


@pytest.mark.parametrize("kante", [1, 64, 512, 768, 1024, 1440, 4096])
def test_rundlauf_der_aufloesung(kante):
    """Hin und zurück ohne Verlust — solange quadratisch, und quadratisch sind wir immer."""
    assert resolution_zu_aufloesung(aufloesung_zu_resolution(kante))["aufloesung"] == kante


def test_aufloesung_in_params_wird_beim_uebersetzen_getauscht():
    """Der Befund in seiner konkreten Form: ``aufloesung: 512`` → ``resolution: "512x512"``."""
    fremd = als_kosmo_auftrag(_unser_satz())

    assert fremd["params"]["resolution"] == "512x512"
    assert "aufloesung" not in fremd["params"]
    assert fremd["params"]["up_axis"] == "Y", "die übrigen Parameter bleiben unberührt"


def test_unbrauchbare_aufloesung_im_auftrag_faellt_an_der_naht_auf():
    """Lieber hier als drüben: ein Auftrag mit ``aufloesung: 0`` wird nicht übersetzt."""
    satz = jobs.baue_job(job_id=KENNUNG, art="depth", params={"aufloesung": 0})

    with pytest.raises(NahtError, match="aufloesung"):
        als_kosmo_auftrag(satz)


# --------------------------------------------------------------------------------------
# 3 · Die Kennung ist einseitig unverträglich — und das bleibt so
# --------------------------------------------------------------------------------------

def test_die_unvertraeglichkeit_ist_einseitig():
    """Unsere Kennung besteht deren Muster, deren besteht unseres nicht.

    Das ist keine Symmetrie, sondern eine Richtung: Wir lehnen fremde Aufträge ab, sie
    nehmen unsere an.
    """
    assert FREMDES_JOB_ID_MUSTER.fullmatch(KENNUNG), "sie nähmen unsere Kennung an"
    assert FREMDES_JOB_ID_MUSTER.fullmatch(IHRE_KENNUNG)
    assert jobs.JOB_ID_MUSTER.fullmatch(KENNUNG)
    assert jobs.JOB_ID_MUSTER.fullmatch(IHRE_KENNUNG) is None, "wir nehmen ihre nicht an"


def test_fremde_kennung_wird_gelesen_aber_als_ungueltig_gemeldet():
    """Lesbar ja, ablegbar nein — und die Auskunft darüber ist ausdrücklich."""
    unser = aus_kosmo_auftrag(_ihr_satz())

    assert unser["kennung_bei_uns_gueltig"] is False
    assert unser["art"] == "render", "der Satz wird trotzdem vollständig gelesen"
    assert any("Kennung" in h for h in unser["hinweise"])


def test_unsere_kennung_gilt_auch_im_fremden_satz():
    """Die Gegenprobe: kommt ein Auftrag mit unserer Kennung zurück, ist er ablegbar."""
    unser = aus_kosmo_auftrag(_ihr_satz(job_id=KENNUNG))

    assert unser["kennung_bei_uns_gueltig"] is True
    assert not any("Kennung" in h for h in unser["hinweise"])


@pytest.mark.parametrize("fremde_kennung", [IHRE_KENNUNG, "job-42", "", None],
                         ids=repr)
def test_die_kennung_wird_nicht_umgeschrieben(fremde_kennung):
    """**Absicht, kein Versäumnis.** Eine Kennung stillschweigend zu übersetzen hiesse,
    zwei Systemen dieselbe Sache unter zwei Namen zu geben.

    Dieser Test ist die Bremse gegen eine gut gemeinte Reparatur: Wer hier eine
    Umrechnung einbaut — etwa Unix-Zeit nach ``JJJJMMTTHHMMSS`` —, macht ihn rot.
    """
    unser = aus_kosmo_auftrag(_ihr_satz(job_id=fremde_kennung))

    assert unser["job_id"] == fremde_kennung


def test_ein_so_gelesener_auftrag_ist_bei_uns_nicht_ablegbar():
    """Die Auskunft ist keine Meinung: ``jobs`` weist den Satz tatsächlich ab.

    ``_pruefe_job_id`` liesse ``vis-1755530000-a1b2c3`` als Dateinamen zwar zu — die
    Prüfung, die greift, ist die des Musters, und sie steht in ``baue_job``s Aufrufern.
    Geprüft wird darum am Muster selbst, an dem auch ``kennung_bei_uns_gueltig`` hängt.
    """
    unser = aus_kosmo_auftrag(_ihr_satz())

    assert unser["kennung_bei_uns_gueltig"] is False
    assert jobs.JOB_ID_MUSTER.fullmatch(str(unser["job_id"])) is None


# --------------------------------------------------------------------------------------
# 4 · Die Feldübersetzung, in beide Richtungen
# --------------------------------------------------------------------------------------

@pytest.mark.parametrize("unser_name, ihr_name", sorted(JOB_FELDER.items()))
def test_jedes_feldpaar_wird_uebersetzt(unser_name, ihr_name):
    """Jedes Paar aus ``JOB_FELDER`` einmal — hin und zurück, mit unterscheidbarem Wert."""
    satz = _unser_satz()
    satz[unser_name] = f"markierung-{unser_name}"

    fremd = als_kosmo_auftrag(satz)

    assert fremd[ihr_name] == f"markierung-{unser_name}"
    assert unser_name not in fremd, "unser Name darf drüben nicht zusätzlich auftauchen"
    assert aus_kosmo_auftrag(fremd)[unser_name] == f"markierung-{unser_name}"


def test_rundlauf_erhaelt_die_uebersetzten_werte():
    """Der ganze Satz auf einmal: Was durch beide Richtungen läuft, kommt gleich an."""
    unser = _unser_satz()
    unser["ergebnis"] = {"depth_png": "/synthetisch/aus/tiefe_norm.png"}
    unser["fehler"] = None

    zurueck = aus_kosmo_auftrag(als_kosmo_auftrag(unser))

    for feld in ("job_id", "status", "idle_window_only", *JOB_FELDER):
        assert zurueck[feld] == unser[feld], f"{feld} hat den Rundlauf nicht überlebt"
    assert zurueck["params"] == unser["params"]


def test_progress_und_phase_stehen_leer_statt_zu_fehlen():
    """Ein leeres Feld ist eine Aussage, ein fehlendes nicht.

    Wir führen weder Fortschritt noch Phase (Kap. 7.3). Wer den übersetzten Satz liest,
    soll das **finden**, statt es zu vermissen und für einen Übertragungsfehler zu halten.
    """
    fremd = als_kosmo_auftrag(_unser_satz())

    assert "progress" in fremd and fremd["progress"] is None
    assert "phase" in fremd and fremd["phase"] is None


def test_der_uebersetzte_satz_traegt_die_felder_des_vertrags():
    """Alles, was der Vertrag in der Auftragsdatei nennt, ist vorhanden."""
    fremd = als_kosmo_auftrag(_unser_satz())

    assert VERTRAGSFELDER <= set(fremd), f"fehlt: {sorted(VERTRAGSFELDER - set(fremd))}"


def test_fremde_freigabe_wird_uebernommen_das_token_nicht():
    """Die Tatsache der Freigabe ja, die Befugnis nein."""
    unser = aus_kosmo_auftrag(_ihr_satz(approval_token=GUELTIG, status="queued"))

    assert unser["freigegeben"] is True
    assert TOKEN_PRAEFIX not in json.dumps(unser, ensure_ascii=False), (
        "Das fremde Token ist auf unsere Seite gelaufen."
    )


@pytest.mark.parametrize("name, token", UNBRAUCHBARE_TOKEN,
                         ids=[n for n, _ in UNBRAUCHBARE_TOKEN])
def test_fremdes_token_in_falscher_form_gilt_nicht_und_wird_gesagt(name, token):
    """Fail-closed **und** laut: keine Freigabe, und ein Hinweis, warum nicht.

    Still auf ``False`` zu fallen wäre genau der Fehler aus Kap. 7.2 mit umgekehrtem
    Vorzeichen — eine Freigabe, die niemand als fehlend erkennt.
    """
    unser = aus_kosmo_auftrag(_ihr_satz(approval_token=token, job_id=KENNUNG))

    assert unser["freigegeben"] is False
    if token not in ("", 0, False):     # ein leeres Token ist keine Behauptung
        assert any("approval_token" in h for h in unser["hinweise"]), unser["hinweise"]


def test_fehlendes_fremdes_token_erzeugt_keinen_laerm():
    """Kein Token ist keine Falschmeldung — dafür gibt es keinen Hinweis.

    Der Satz von drüben trägt ``"1920x1440"``; **dieser** Hinweis bleibt und soll bleiben.
    Was fehlen muss, ist eine Meldung über ein Token, das gar nicht behauptet wurde.
    """
    unser = aus_kosmo_auftrag(_ihr_satz(job_id=KENNUNG))

    assert unser["freigegeben"] is False
    assert not any("approval_token" in h for h in unser["hinweise"])


def test_fremde_resolution_wird_mit_hinweis_gedeutet():
    """Der Normalfall von drüben: ``"1920x1440"`` in den Parametern."""
    unser = aus_kosmo_auftrag(_ihr_satz())

    assert unser["params"]["aufloesung"] == 1440
    assert "resolution" not in unser["params"]
    assert any("1920x1440" in h for h in unser["hinweise"])


@pytest.mark.parametrize("satz", [None, [], "job", 42, ()], ids=repr)
def test_als_kosmo_auftrag_weist_nicht_woerterbuecher_ab(satz):
    with pytest.raises(NahtError, match="Kein Auftragssatz"):
        als_kosmo_auftrag(satz)


def test_als_kosmo_auftrag_verlangt_eine_kennung():
    """Ein Satz ohne ``job_id`` ist drüben nicht ablegbar — die Datei heisst danach."""
    with pytest.raises(NahtError, match="Kein Auftragssatz"):
        als_kosmo_auftrag({"art": "depth", "params": {}})


@pytest.mark.parametrize("satz", [None, [], "job", 42], ids=repr)
def test_aus_kosmo_auftrag_weist_nicht_woerterbuecher_ab(satz):
    with pytest.raises(NahtError, match="Kein Auftragssatz"):
        aus_kosmo_auftrag(satz)


def test_der_uebergebene_satz_wird_nicht_veraendert():
    """Übersetzen ist Lesen. Ein Aufrufer darf seinen Satz danach weiterverwenden."""
    unser = _unser_satz()
    vorher = json.dumps(unser, sort_keys=True, ensure_ascii=False)

    als_kosmo_auftrag(unser, approval_token=GUELTIG)

    assert json.dumps(unser, sort_keys=True, ensure_ascii=False) == vorher


def test_was_der_rundlauf_fallen_laesst_ist_hier_aufgezaehlt():
    """Der Rundlauf verliert vier Felder — dieser Test nennt sie beim Namen.

    ``schema``, ``verlauf`` und ``freigegeben_am`` haben im Vertrag kein Gegenstück und
    fallen weg; ``freigegeben`` überlebt nur dem Namen nach, weil es drüben aus dem Token
    neu gebildet wird. Keiner dieser Verluste erzeugt einen Hinweis. Das ist heute so
    gewollt (der Vertrag kennt die Felder nicht), aber es soll aufgeschrieben sein — wer
    ein Feld ergänzt, sieht hier, dass es die Naht nicht überlebt.
    """
    unser = _unser_satz()

    zurueck = aus_kosmo_auftrag(als_kosmo_auftrag(unser))

    assert set(unser) - set(zurueck) == {"schema", "verlauf", "freigegeben_am"}
    assert set(zurueck) - set(unser) == {"kennung_bei_uns_gueltig", "hinweise"}


def test_verlorene_freigabe_im_rundlauf_wird_gemeldet():
    """**Die stille tote Kante in der eigenen Naht — behoben am 18.08.2026.**

    Ein Auftrag mit `status="queued"` ist per Definition freigegeben; sonst stünde er auf
    `awaiting_approval`. Kam er aus dem Rundlauf ohne brauchbares Token zurück, sagten
    Status und Freigabe einander widersprechende Dinge — und das Ergebnis **schwieg
    dazu**, mit leerer `hinweise`-Liste.

    Das ist strukturell exakt der Fehler, gegen den dieses Modul gebaut wurde: nicht ein
    Abbruch, sondern eine Angabe, die einfach nicht ankommt. Ihn ausgerechnet hier zu
    haben, war die unangenehmste Art, ihn zu lernen.

    **Repariert wurde er nicht durch Setzen von `freigegeben`** — das erfände eine
    Befugnis aus einem Statuswort. Repariert wurde er durch *Sagen*.
    """
    satz = jobs.baue_job(job_id=jobs.neue_job_id(), art="render",
                         params={"aufloesung": 512},
                         approval_token=jobs.TOKEN_PRAEFIX + "abc123")
    assert satz["status"] == jobs.STATUS_QUEUED

    zurueck = aus_kosmo_auftrag(als_kosmo_auftrag(satz))

    assert zurueck["status"] == jobs.STATUS_QUEUED
    assert zurueck["freigegeben"] is False, "eine Befugnis wird nicht erfunden"
    assert zurueck["hinweise"], "die Widersprüchlichkeit muss gesagt werden"
    assert any("queued" in h and "kein brauchbares Token" in h
               for h in zurueck["hinweise"]), zurueck["hinweise"]

    # Gegenprobe: Wird das Token beim Übergang mitgegeben, entsteht kein Hinweis.
    mit = aus_kosmo_auftrag(als_kosmo_auftrag(
        satz, approval_token=jobs.TOKEN_PRAEFIX + "abc123"))
    assert mit["freigegeben"] is True
    assert not any("kein brauchbares Token" in h for h in mit["hinweise"])



def test_aufloesung_gegen_resolution_ist_nicht_tot_sondern_uebersetzbar():
    """Der ganze Zweck des Moduls in einem Test.

    KosmoOrbit sähe hier zwei Knoten, zwischen denen keine Kante entsteht, und meldete
    nichts. Wir melden: Es gibt eine Kante, sie braucht nur eine Übersetzung.
    """
    befund = pruefe_kanten({"aufloesung"}, {"resolution"})

    assert befund["uebersetzbar"] == ["aufloesung → resolution"]
    assert befund["tot_bei_uns"] == []
    assert befund["tot_bei_ihnen"] == []
    assert befund["verbunden"] == []


@pytest.mark.parametrize("unser_feld, ihr_feld", sorted(MCP_FELDER.items()))
def test_jedes_mcp_feldpaar_gilt_als_uebersetzbar(unser_feld, ihr_feld):
    befund = pruefe_kanten({unser_feld}, {ihr_feld})

    assert befund["uebersetzbar"] == [f"{unser_feld} → {ihr_feld}"]


def test_ein_feld_ohne_gegenstueck_ist_tot():
    """``torwaechter`` ist der Befund aus Kap. 7.2: Wir geben es aus, niemand liest es."""
    befund = pruefe_kanten({"torwaechter"}, {"kind", "resolution"})

    assert befund["tot_bei_uns"] == ["torwaechter"]
    assert befund["uebersetzbar"] == []
    assert sorted(befund["tot_bei_ihnen"]) == ["kind", "resolution"]


def test_die_echten_feldmengen_gegeneinander():
    """Was heute wirklich passt — die Ausgabe von ``jobs.baue_job`` gegen den Vertrag.

    Kein erfundenes Beispiel, sondern der Stand vom 18.08.2026 als ausführbare Notiz:

    * **verbunden** sind vier Felder, die zufällig gleich heissen.
    * **übersetzbar** sind vier weitere — das ist der Ertrag dieses Moduls.
    * **tot bei uns** bleibt, was der Vertrag nicht kennt (``schema``, ``verlauf``,
      ``freigegeben``, ``freigegeben_am``) und ``geaendert``, weil der Vertragsauszug
      ``updated_at`` nicht aufführt.
    * **tot bei ihnen** bleiben ``progress``, ``phase`` — und ``approval_token``: Es hat
      bei uns kein Feld, weil es keines haben **soll**. Der Weg dorthin ist das Argument
      von :func:`als_kosmo_auftrag`, nicht eine Kante.
    """
    unsere = set(_unser_satz())

    befund = pruefe_kanten(unsere, VERTRAGSFELDER)

    assert befund["verbunden"] == ["idle_window_only", "job_id", "params", "status"]
    assert befund["uebersetzbar"] == ["art → kind", "ergebnis → outputs",
                                      "erstellt → created_at", "fehler → error"]
    assert befund["tot_bei_uns"] == ["freigegeben", "freigegeben_am", "geaendert",
                                     "schema", "verlauf"]
    assert befund["tot_bei_ihnen"] == ["approval_token", "phase", "progress"]


def test_pruefe_kanten_nimmt_beliebige_mengenartige_eingaben():
    """Listen, Mengen, Schlüsselsichten — ein Aufrufer soll nicht erst umbauen müssen."""
    aus_liste = pruefe_kanten(["aufloesung", "art"], ["resolution", "kind"])
    aus_dict = pruefe_kanten({"aufloesung": 512, "art": "depth"},
                             {"resolution": "512x512", "kind": "depth"})

    assert aus_liste == aus_dict
    assert aus_liste["uebersetzbar"] == ["art → kind", "aufloesung → resolution"]


# --------------------------------------------------------------------------------------
# 6 · Das Modul selbst
# --------------------------------------------------------------------------------------

def test_naht_error_ist_ein_value_error():
    """Wer heute ``ValueError`` fängt, fängt die Naht mit — kein stiller Durchmarsch."""
    assert issubclass(NahtError, ValueError)


def test_kosmo_naht_haengt_nur_an_jobs_und_stdlib():
    """Regel 4 und die Prozessgrenze: kein ``bpy``, kein UI, kein Netz an der Naht."""
    quelle = (kosmo_naht.__file__)
    text = open(quelle, encoding="utf-8").read()

    for verboten in ("import bpy", "import ifcopenshell", "import requests",
                     "import torch", "urllib.request"):
        assert verboten not in text, f"{verboten} an der Naht gefunden"
