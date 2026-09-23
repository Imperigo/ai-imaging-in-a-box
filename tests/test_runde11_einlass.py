"""Runde 11 am Einlass: die zweite Tür am Freigabe-Tor und die Geometriefelder aus einer Quelle.

Zwei Befunde der Prüfung vom 23.09.2026, beide über den Weg bewacht, den das Produkt geht
(``werkzeuge.enqueue_render`` → eigene Ablage → ``abholer.durchgang`` mit
``eigene_quelle`` und einer Attrappe als Verarbeiter):

A · DIE ZWEITE TÜR. Ein Renderauftrag darf nur mit Freigabe von ``awaiting_approval``
    nach ``queued``. ``jobs.freigeben`` prüft das — auf Wunsch gegen das Tokenbuch
    (``mit_buch``, Vorgabe aus). ``jobs.baue_job`` stellte aber selbst auf ``queued``,
    allein nach der FORM des Tokens, und der MCP-Einlass ging genau durch diese Tür. Mit
    eingeschalteter Buchprüfung wäre sie offen geblieben. Und ``eigene_quelle`` glaubte
    dem ``queued`` im File.

    Seither geht ``baue_job`` durch dieselbe Tür (``_freigabe_pruefen`` /
    ``_freigabe_vollziehen``) mit derselben Vorgabe (``jobs.FREIGABE_MIT_BUCH``), der
    Auftrag trägt den Abdruck des Tokens, und ``eigene_quelle`` nimmt bei vorhandenem
    Tokenbuch nur, was das Buch für genau diesen Auftrag als verbraucht führt.

B · DIE VIER GEOMETRIEFELDER. Sie standen dreimal von Hand da (``contracts``,
    ``werkzeuge``, ``mcp_schemas``). Seither ist ``contracts.LANE_FIELDS`` die Quelle.

Alle Daten synthetisch (Regel 3).
"""
from __future__ import annotations

import json

import pytest

from aiimaging import (abholer, contracts, eigene_quelle, jobs, mcp_schemas, seams,
                       werkzeuge)

MUSTER = jobs.TOKEN_PRAEFIX + "TEST"


@pytest.fixture()
def store(tmp_path, monkeypatch):
    """Eine eigene Ablage — nie die des Benutzers."""
    ziel = tmp_path / "aiimaging-jobs"
    monkeypatch.setenv(werkzeuge.UMGEBUNG_JOBS, str(ziel))
    return ziel


@pytest.fixture()
def glb(tmp_path):
    pfad = tmp_path / "wuerfel.glb"
    pfad.write_bytes(b"glTF-Attrappe")
    return pfad


def _bestelle(glb, **zusatz) -> dict:
    argumente = {"glb_path": str(glb), "up_axis": "Y",
                 "bbox": [[0, 0, 0], [20, 15, 10]], "approval_token": MUSTER}
    argumente.update(zusatz)
    return werkzeuge.enqueue_render(argumente)


def _auftragsdatei(store, job_id):
    return store / job_id / f"{job_id}{jobs.DATEI_ENDUNG}"


def _satz(store, job_id) -> dict:
    return json.loads(_auftragsdatei(store, job_id).read_text(encoding="utf-8"))


def _durchgang(store) -> tuple[dict, list]:
    gesehen: list = []

    def verarbeite(auftrag):
        gesehen.append(auftrag)
        return {"bilder": ["kamera_s.png"], "geometrie_urteil": {"passed": True},
                "stil_urteil": None, "kameras": [], "zeiten": {"gesamt": 1.0}}

    bericht = abholer.durchgang(store, verarbeite=verarbeite, quelle=eigene_quelle,
                                darf_rechnen=lambda: (True, "frei"))
    return bericht, gesehen


def _von_hand_auf_queued(store, job_id) -> None:
    """Das Statuswort direkt in die Datei — so, wie es jeder mit Dateizugriff könnte."""
    datei = _auftragsdatei(store, job_id)
    satz = json.loads(datei.read_text(encoding="utf-8"))
    satz["status"] = jobs.STATUS_QUEUED
    datei.write_text(json.dumps(satz), encoding="utf-8")


def _alle_texte(wurzel) -> list[tuple[str, str]]:
    return [(p.name, p.read_text(encoding="utf-8"))
            for p in sorted(wurzel.rglob("*")) if p.is_file()]


# ── A · Die Tür: heute gleich ─────────────────────────────────────────────────────────

def test_muster_token_ohne_buch_wird_ueber_den_mcp_weg_queued_wie_heute(store, glb):
    """Für heutige Aufrufer ändert sich nichts: Status, Rückgabe, Freigabefelder."""
    antwort = _bestelle(glb)

    assert antwort["error"] is None
    assert antwort["status"] == jobs.STATUS_QUEUED
    satz = _satz(store, antwort["job_id"])
    assert satz["status"] == jobs.STATUS_QUEUED
    assert satz["freigegeben"] is True
    assert satz["freigegeben_am"] == satz["erstellt"]
    assert "meldung" not in satz
    # Neu und bewusst: Der Verlauf zeigt die Tür, wie bei einer nachträglichen Freigabe.
    assert [e["status"] for e in satz["verlauf"]] == [jobs.STATUS_AWAITING,
                                                      jobs.STATUS_QUEUED]
    assert not (store / jobs.TOKENBUCH).exists(), "ohne Buchprüfung entsteht kein Buch"

    bericht, gesehen = _durchgang(store)
    assert bericht["verarbeitet"] == 1 and len(gesehen) == 1, bericht["ergebnisse"]


def test_der_auftrag_traegt_den_abdruck_und_das_token_steht_nirgends(store, glb):
    """Der Abdruck ist derselbe wie im Tokenbuch — das Token selbst in keiner Datei."""
    antwort = _bestelle(glb)

    satz = _satz(store, antwort["job_id"])
    assert satz[jobs.FELD_ABDRUCK] == jobs._fingerabdruck(MUSTER)
    for name, text in _alle_texte(store):
        assert MUSTER not in text, f"Token im Klartext in {name}"
        assert jobs.TOKEN_PRAEFIX not in text, f"Tokenform in {name}"


def test_baue_job_stellt_nicht_selbst_auf_queued(monkeypatch):
    """Nimmt man die Tür weg, bleibt der Auftrag stehen — ``queued`` kommt nur durch sie.

    Die Wirkung, nicht der Quelltext: Wäre in ``baue_job`` noch ein eigener Weg nach
    ``queued``, käme das Muster-Token hier trotzdem durch.
    """
    monkeypatch.setattr(jobs, "_freigabe_vollziehen", lambda satz, *a, **k: satz)

    satz = jobs.baue_job(job_id="vis-20260923120000-abc123", art="render", params={},
                         approval_token=MUSTER)

    assert satz["status"] == jobs.STATUS_AWAITING
    assert satz["freigegeben"] is False


def test_abgewiesenes_token_steht_als_meldung_nicht_still(store, glb):
    """Was angenommen wird und nicht wirkt, wird gesagt — ohne das Token zu nennen."""
    antwort = _bestelle(glb, approval_token="bitte-rechnen")

    assert antwort["status"] == jobs.STATUS_AWAITING
    meldung = _satz(store, antwort["job_id"]).get("meldung") or ""
    assert "abgewiesen" in meldung and jobs.TOKEN_PRAEFIX in meldung
    assert "bitte-rechnen" not in meldung


def test_ohne_token_keine_meldung(store, glb):
    antwort = _bestelle(glb, approval_token=None)

    assert antwort["status"] == jobs.STATUS_AWAITING
    assert "meldung" not in _satz(store, antwort["job_id"])


# ── A · Die Tür: mit Buchprüfung geschlossen, an EINER Stelle geschaltet ───────────────

def test_mit_buch_kommt_ein_nie_ausgegebenes_token_nicht_ueber_freigeben(tmp_path,
                                                                        monkeypatch):
    monkeypatch.setattr(jobs, "FREIGABE_MIT_BUCH", True)
    jobs.schreibe_job(jobs.baue_job(job_id="a1", art="render", params={}), tmp_path)

    with pytest.raises(jobs.JobError, match="ausgegeben"):
        jobs.freigeben("a1", MUSTER, tmp_path)

    assert jobs.lies_job("a1", tmp_path)["status"] == jobs.STATUS_AWAITING


def test_mit_buch_kommt_ein_nie_ausgegebenes_token_nicht_ueber_enqueue_render(
        store, glb, monkeypatch):
    """Der Befund selbst: Dieselbe eine Vorgabe schliesst auch den MCP-Einlass."""
    monkeypatch.setattr(jobs, "FREIGABE_MIT_BUCH", True)
    jobs.token_ausgeben(store)                     # ein Buch gibt es, dieses Token nicht

    antwort = _bestelle(glb)

    assert antwort["error"] is None
    assert antwort["status"] == jobs.STATUS_AWAITING
    satz = _satz(store, antwort["job_id"])
    assert satz["status"] == jobs.STATUS_AWAITING and satz["freigegeben"] is False
    assert "nie" in satz["meldung"] and "ausgegeben" in satz["meldung"]
    assert jobs.FELD_ABDRUCK not in satz

    bericht, gesehen = _durchgang(store)
    assert bericht["gesehen"] == 0 and not gesehen


def test_mit_buch_und_ohne_buch_verzeichnis_geht_die_tuer_nicht_auf(monkeypatch):
    """Nicht prüfbar ist nicht dasselbe wie geprüft."""
    monkeypatch.setattr(jobs, "FREIGABE_MIT_BUCH", True)

    satz = jobs.baue_job(job_id="a1", art="render", params={}, approval_token=MUSTER)

    assert satz["status"] == jobs.STATUS_AWAITING
    assert "Verzeichnis des Tokenbuchs" in satz["meldung"]


def test_mit_buch_und_ausgegebenem_token_rechnet_der_auftrag_genau_einmal(
        store, glb, monkeypatch):
    """Die Gegenprobe: Ein ausgegebenes Token öffnet die Tür — und nur einmal."""
    monkeypatch.setattr(jobs, "FREIGABE_MIT_BUCH", True)
    token = jobs.token_ausgeben(werkzeuge.job_verzeichnis())

    erste = _bestelle(glb, approval_token=token)
    zweite = _bestelle(glb, approval_token=token)

    assert erste["status"] == jobs.STATUS_QUEUED
    assert zweite["status"] == jobs.STATUS_AWAITING
    buch = json.loads((store / jobs.TOKENBUCH).read_text(encoding="utf-8"))
    eintrag = buch[jobs._fingerabdruck(token)]
    assert eintrag["verbraucht_fuer"] == erste["job_id"]
    for name, text in _alle_texte(store):
        assert token not in text, f"Token im Klartext in {name}"

    bericht, gesehen = _durchgang(store)
    assert bericht["verarbeitet"] == 1 and len(gesehen) == 1, bericht["ergebnisse"]
    assert gesehen[0]["job_id"] == erste["job_id"]


def test_scheitert_das_entwerten_bleibt_der_auftrag_unberuehrt_und_wartet(
        store, glb, monkeypatch):
    """**Durchsicht Runde 11.** Wirft das Entwerten (Wettlauf um dasselbe Token, Buch
    dazwischen unlesbar), stand der Satz schon auf ``queued`` — mit der Meldung
    «abgewiesen». Jetzt wird zuerst entwertet und erst danach der Satz angefasst."""
    monkeypatch.setattr(jobs, "FREIGABE_MIT_BUCH", True)
    token = jobs.token_ausgeben(werkzeuge.job_verzeichnis())

    def wirft(*a, **kw):
        raise jobs.JobError("Tokenbuch zwischendurch unlesbar (Attrappe)")
    monkeypatch.setattr(jobs, "token_entwerten", wirft)

    antwort = _bestelle(glb, approval_token=token)
    assert antwort["status"] == jobs.STATUS_AWAITING
    satz = _satz(store, antwort["job_id"])
    assert satz["status"] == jobs.STATUS_AWAITING
    assert not satz.get("freigegeben")
    assert jobs.FELD_ABDRUCK not in satz
    assert "abgewiesen" in satz["meldung"]


# ── A · eigene_quelle glaubt dem Statuswort nicht mehr blind ──────────────────────────

def test_von_hand_queued_wird_ohne_buch_genommen(store, glb):
    """Ohne Tokenbuch wie bisher: Das Statuswort gilt."""
    antwort = _bestelle(glb, approval_token=None)
    _von_hand_auf_queued(store, antwort["job_id"])

    bericht, gesehen = _durchgang(store)

    assert bericht["verarbeitet"] == 1 and len(gesehen) == 1, bericht["ergebnisse"]


def test_von_hand_queued_wird_mit_buch_nicht_genommen_und_traegt_den_satz(store, glb):
    antwort = _bestelle(glb, approval_token=None)
    _von_hand_auf_queued(store, antwort["job_id"])
    jobs.token_ausgeben(store)                     # ab jetzt führt die Ablage ein Buch

    bericht, gesehen = _durchgang(store)

    assert not gesehen, "ein von Hand gesetztes queued wurde gerechnet"
    assert bericht["verarbeitet"] == 0
    satz = _satz(store, antwort["job_id"])
    assert satz["status"] == jobs.STATUS_QUEUED, "der Status bleibt, nur das Warum kommt"
    assert "Tokenbuch" in satz["meldung"] and "keinen Abdruck" in satz["meldung"]


def test_muster_token_bei_vorhandenem_buch_bleibt_liegen_auch_mit_buchpruefung_aus(
        store, glb):
    """Die Tür am Einlass ist heute noch offen (Vorgabe aus) — der Abholer nicht mehr.

    Sobald jemand Token ausgibt, rechnet kein Muster-Token mehr, auch wenn
    ``FREIGABE_MIT_BUCH`` noch aus ist.
    """
    jobs.token_ausgeben(store)
    antwort = _bestelle(glb)
    assert antwort["status"] == jobs.STATUS_QUEUED           # Einlass wie heute

    bericht, gesehen = _durchgang(store)

    assert not gesehen
    assert "nie ausgegeben" in _satz(store, antwort["job_id"])["meldung"]


def test_ausgegebenes_token_ohne_buchpruefung_bleibt_liegen(store, glb):
    """Ausgegeben, aber nicht verbraucht: dasselbe Token gälte noch einmal."""
    token = jobs.token_ausgeben(store)
    antwort = _bestelle(glb, approval_token=token)
    assert antwort["status"] == jobs.STATUS_QUEUED

    _, gesehen = _durchgang(store)

    assert not gesehen
    assert "nicht verbraucht" in _satz(store, antwort["job_id"])["meldung"]


def test_fremder_abdruck_belegt_keinen_anderen_auftrag(store, glb, monkeypatch):
    """Verbraucht für Auftrag A heisst nicht freigegeben für Auftrag B."""
    monkeypatch.setattr(jobs, "FREIGABE_MIT_BUCH", True)
    token = jobs.token_ausgeben(store)
    a = _bestelle(glb, approval_token=token)["job_id"]
    b = _bestelle(glb, approval_token=None)["job_id"]
    datei = _auftragsdatei(store, b)
    satz_b = json.loads(datei.read_text(encoding="utf-8"))
    satz_b["status"] = jobs.STATUS_QUEUED
    satz_b[jobs.FELD_ABDRUCK] = _satz(store, a)[jobs.FELD_ABDRUCK]
    datei.write_text(json.dumps(satz_b), encoding="utf-8")

    _, gesehen = _durchgang(store)

    assert [g["job_id"] for g in gesehen] == [a]
    assert "anderen Auftrag" in _satz(store, b)["meldung"]


def test_buch_im_auftragsordner_belegt_eine_freigabe_ueber_diesen_ordner(store, glb):
    """Wer ``freigeben`` mit dem Auftragsordner und Buchprüfung ruft, wird genommen."""
    job_id = _bestelle(glb, approval_token=None)["job_id"]
    ordner = store / job_id
    token = jobs.token_ausgeben(ordner)

    jobs.freigeben(job_id, token, ordner, mit_buch=True)
    _, gesehen = _durchgang(store)

    assert [g["job_id"] for g in gesehen] == [job_id]


def test_unlesbares_buch_laesst_nichts_durch(store, glb):
    """Die dritte Antwort: Über ein unlesbares Buch ist nichts zu entscheiden."""
    antwort = _bestelle(glb)
    (store / jobs.TOKENBUCH).write_text("{kein json", encoding="utf-8")

    bericht, gesehen = _durchgang(store)

    assert not gesehen
    assert "nicht lesbar" in _satz(store, antwort["job_id"])["meldung"]


# ── B · Die Geometriefelder aus einer Quelle ─────────────────────────────────────────

def test_jedes_lane_feld_steht_im_eingangsschema():
    for werkzeug in (mcp_schemas.WERKZEUG_ENQUEUE, mcp_schemas.WERKZEUG_PRUEFE):
        felder = mcp_schemas.WERKZEUGE[werkzeug]["inputSchema"]["properties"]
        for name in contracts.LANE_FIELDS:
            assert name in felder, f"{werkzeug}: {name} fehlt im inputSchema"
    assert set(contracts.LANE_FIELDS) == {"ifc_path", "glb_path", "up_axis", "bbox"}


def test_glb_felder_kommen_im_auftrag_an(store, glb):
    """Wirkung je Feld: der geschickte Wert steht im abgelegten Auftrag."""
    bbox = [[1, 2, 0], [9, 7, 4]]
    antwort = werkzeuge.enqueue_render({"glb_path": str(glb), "up_axis": "Z",
                                        "bbox": bbox})

    params = _satz(store, antwort["job_id"])["params"]
    assert params["glb_path"] == str(glb)
    assert params["up_axis"] == "Z"
    assert params["bbox"] == bbox


def test_ifc_path_kommt_bei_der_umwandlung_an(store, tmp_path, monkeypatch):
    """``ifc_path`` wird nicht abgelegt, sondern umgewandelt — die Wirkung ist der Aufruf."""
    ifc = tmp_path / "wuerfel.ifc"
    ifc.write_text("ISO-10303-21; synthetisch", encoding="utf-8")
    gerufen: list = []

    def ifc_zu_glb(quelle, ziel, *a, **k):
        gerufen.append(str(quelle))
        return {"status": "ok", "glb_path": str(ziel), "up_axis": "Y",
                "bbox": [[0, 0, 0], [8, 5, 3]], "error": None}

    monkeypatch.setattr(seams, "ifc_zu_glb", ifc_zu_glb)
    antwort = werkzeuge.enqueue_render({"ifc_path": str(ifc),
                                        "out_dir": str(tmp_path / "aus")})

    assert antwort["error"] is None, antwort["error"]
    assert gerufen == [str(ifc)]
    assert _satz(store, antwort["job_id"])["params"]["glb_path"] == str(
        tmp_path / "aus" / "modell.glb")


def test_ein_in_lane_fields_ergaenztes_feld_wird_am_einlass_angenommen(monkeypatch):
    """Der Einlass LIEST die Quelle, statt eine eigene Liste zu führen. Mehr nicht: Ob ein
    neues Feld im Auftrag etwas bewirkt, entscheidet ``enqueue_render`` (Durchsicht Runde
    11) — dieser Wächter prüft nur das Lesen."""
    monkeypatch.setattr(contracts, "LANE_FIELDS", contracts.LANE_FIELDS + ("probe_feld",))

    assert werkzeuge._geometrie_aus_argumenten({"probe_feld": 7, "fremd": 1}) == {
        "probe_feld": 7}


def test_das_schema_fuehrt_die_quelle_und_kein_eigenes_tupel():
    assert mcp_schemas.GEOMETRIE_FELDER is contracts.LANE_FIELDS
    assert tuple(mcp_schemas._GEOMETRIE_EINGANG) == contracts.LANE_FIELDS
