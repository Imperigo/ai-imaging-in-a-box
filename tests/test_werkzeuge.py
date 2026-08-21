"""Die MCP-Naht als Ganzes — enqueue, query, Vorprüfung.

Bewacht vor allem den Freeze-Schutz: `enqueue_render` darf unter keinen Umständen die
GPU anrühren, und der Status folgt allein dem Freigabe-Token. Ein Sprachmodell soll
Aufträge einstellen können, ohne Hardware blockieren zu können.
"""
from __future__ import annotations

import pytest

from aiimaging import jobs, torwaechter, werkzeuge


@pytest.fixture(autouse=True)
def eigenes_job_verzeichnis(tmp_path, monkeypatch):
    """Nie ins echte Auftragsverzeichnis schreiben — Tests dürfen nichts hinterlassen."""
    monkeypatch.setenv(werkzeuge.UMGEBUNG_JOBS, str(tmp_path / "jobs"))
    return tmp_path


@pytest.fixture
def glb_eingang(tmp_path):
    """Eine glb-Eingabe, die den Vertrag erfüllt — Inhalt ist hier gleichgültig."""
    glb = tmp_path / "bau.glb"
    glb.write_bytes(b"glTF-Attrappe")
    return {"glb_path": str(glb), "up_axis": "Y", "bbox": [[0, 0, 0], [8, 5, 3]],
            "out_dir": str(tmp_path / "aus")}


# ── Freeze-Schutz ────────────────────────────────────────────────────────────────────

def test_ohne_token_bleibt_der_auftrag_auf_freigabe_wartend(glb_eingang):
    """Der Regelfall. Ohne Freigabe wird nichts gerechnet — das ist der Freeze-Schutz."""
    assert werkzeuge.enqueue_render(glb_eingang)["status"] == jobs.STATUS_AWAITING


def test_mit_gueltigem_token_wird_eingereiht(glb_eingang):
    """Erst eine gültige Freigabe stellt den Auftrag in die Warteschlange."""
    ergebnis = werkzeuge.enqueue_render({**glb_eingang, "approval_token": "CONFIRMED_RENDER_owner"})
    assert ergebnis["status"] == jobs.STATUS_QUEUED


@pytest.mark.parametrize("token", ["", "FOO", "confirmed_render_owner", "CONFIRMED_RENDER_"])
def test_untaugliche_token_reihen_nicht_ein(glb_eingang, token):
    """Beinahe-richtige Token sind der gefährliche Fall — sie dürfen nicht durchrutschen."""
    ergebnis = werkzeuge.enqueue_render({**glb_eingang, "approval_token": token})
    assert ergebnis["status"] == jobs.STATUS_AWAITING


def test_enqueue_meldet_niemals_running(glb_eingang):
    """Dieses Werkzeug führt nichts aus. Meldete es `running`, wäre der Schutz hinfällig."""
    assert werkzeuge.enqueue_render(glb_eingang)["status"] != jobs.STATUS_RUNNING


# ── Der Phase-0-Befund, an der Naht ──────────────────────────────────────────────────

def test_glb_ohne_up_achse_wird_abgelehnt(tmp_path):
    """Der Kern von Phase 0: keine Vermutung über die Orientierung, auch nicht hier."""
    ergebnis = werkzeuge.enqueue_render(
        {"glb_path": str(tmp_path / "b.glb"), "out_dir": str(tmp_path)})

    assert ergebnis["job_id"] is None
    assert "up_axis" in ergebnis["error"]


def test_kein_auftrag_bei_abgelehnter_geometrie(tmp_path):
    """Ein Auftrag auf kaputter Geometrie verbrennt später GPU-Zeit, um doch zu scheitern."""
    ergebnis = werkzeuge.enqueue_render({
        "glb_path": str(tmp_path / "b.glb"), "up_axis": "Y",
        "bbox": [[0, 0, 0], [8000, 5000, 3000]],          # mm-als-m
        "out_dir": str(tmp_path)})

    assert ergebnis["job_id"] is None
    assert jobs.liste_jobs(werkzeuge.job_verzeichnis()) == []


def test_z_up_geometrie_wird_angenommen_und_vermerkt(tmp_path):
    """KosmoDraw-Geometrie ist gültig — sie wird angenommen, die Drehung passiert später."""
    ergebnis = werkzeuge.enqueue_render({
        "glb_path": str(tmp_path / "b.glb"), "up_axis": "Z",
        "bbox": [[0, 0, 0], [8, 5, 3]], "out_dir": str(tmp_path)})

    assert ergebnis["status"] == jobs.STATUS_AWAITING
    assert ergebnis["up_axis"] == "Z"


# ── Antwortform ──────────────────────────────────────────────────────────────────────

def test_fehlerantwort_traegt_alle_felder_des_schemas(tmp_path):
    """KosmoOrbit prüft gegen das outputSchema — eine verkürzte Antwort verdeckt die Ursache."""
    voll = set(werkzeuge.enqueue_render(
        {"glb_path": str(tmp_path / "b.glb"), "up_axis": "Y",
         "bbox": [[0, 0, 0], [8, 5, 3]], "out_dir": str(tmp_path)}))
    knapp = set(werkzeuge.enqueue_render({"out_dir": str(tmp_path)}))

    assert voll == knapp


def test_geometry_ref_zeigt_auf_die_glb(glb_eingang):
    """`geometry_ref` ist der Ökosystem-Begriff — nachgelagerte Knoten erwarten ihn."""
    ergebnis = werkzeuge.enqueue_render(glb_eingang)
    assert ergebnis["geometry_ref"] == ergebnis["glb_path"] == glb_eingang["glb_path"]


def test_fremde_felder_aus_mergeinputs_stoeren_nicht(glb_eingang):
    """mergeInputs reicht ALLE Vorgängerfelder durch — wir nehmen nur, was uns angeht."""
    ergebnis = werkzeuge.enqueue_render(
        {**glb_eingang, "n_vertices": 123, "layers": [{"x": 1}], "voellig_fremd": "egal"})

    assert ergebnis["status"] == jobs.STATUS_AWAITING


# ── query ────────────────────────────────────────────────────────────────────────────

def test_query_liest_den_abgelegten_auftrag(glb_eingang):
    """Die natürliche Kette enqueue → query muss ohne Handarbeit tragen."""
    jid = werkzeuge.enqueue_render(glb_eingang)["job_id"]

    gelesen = werkzeuge.query_render({"job_id": jid})

    assert gelesen["job_id"] == jid
    assert gelesen["status"] == jobs.STATUS_AWAITING
    assert gelesen["error"] is None


def test_query_ohne_job_id_meldet_das_pflichtfeld():
    """Kein Traceback im Cockpit — eine Fehlermeldung, die den Grund nennt."""
    assert "job_id" in werkzeuge.query_render({})["error"]


def test_query_auf_unbekannten_auftrag_meldet_sauber():
    """Ein unbekannter Auftrag ist ein Ergebnis, keine Ausnahme."""
    antwort = werkzeuge.query_render({"job_id": "vis-20260101000000-aaaaaa"})
    assert antwort["error"] and antwort["status"] is None


def test_query_wehrt_pfad_trickserei_ab():
    """Eine job_id ist ein Name, kein Pfad."""
    assert werkzeuge.query_render({"job_id": "../../etc/passwd"})["error"]


# ── Vorprüfung ───────────────────────────────────────────────────────────────────────

def test_vorpruefung_faengt_fehlskalierung_ohne_auftrag():
    """Rein rechnend — sie soll vor den Render gehängt werden können."""
    ergebnis = werkzeuge.check_geometry({"bbox": [[0, 0, 0], [8000, 5000, 3000]]})

    assert ergebnis["entscheidung"] == torwaechter.ENTSCHEIDUNG_ABLEHNEN_MASSSTAB
    assert jobs.liste_jobs(werkzeuge.job_verzeichnis()) == []


def test_vorpruefung_nimmt_plausibles_gebaeude_an():
    assert werkzeuge.check_geometry({"bbox": [[0, 0, 0], [8, 5, 3]]})["entscheidung"] == \
        torwaechter.ENTSCHEIDUNG_ANNEHMEN


def test_vorpruefung_ohne_geometrie_meldet_statt_zu_raten():
    assert werkzeuge.check_geometry({})["entscheidung"] == \
        torwaechter.ENTSCHEIDUNG_ABLEHNEN_KONVERSION


def test_ruftabelle_deckt_alle_werkzeuge_ab():
    """Ein neues Werkzeug im Vertrag ohne Eintrag hier wäre im Cockpit sichtbar, aber tot."""
    from aiimaging.mcp_schemas import WERKZEUGE
    assert set(werkzeuge.RUFTABELLE) == set(WERKZEUGE)


# ======================================================================================
# Die Selbstauskunft — bisher ungeprüft, obwohl sie das Aushängeschild der Lane ist
# ======================================================================================

def test_die_selbstauskunft_haelt_ihren_eigenen_vertrag():
    """Ein Auskunftswerkzeug, dessen Antwort nicht zum eigenen Schema passt, ist die
    Pointe seines eigenen Zwecks: Es soll dem Ökosystem sagen, was hier gilt."""
    from aiimaging.mcp_schemas import WERKZEUG_FAEHIGKEITEN, werkzeug

    antwort = werkzeuge.capabilities({})
    schema = werkzeug(WERKZEUG_FAEHIGKEITEN)["outputSchema"]

    for pflicht in schema["required"]:
        assert pflicht in antwort, f"Pflichtfeld {pflicht!r} fehlt in der Antwort"
    unbekannt = set(antwort) - set(schema["properties"])
    assert not unbekannt, (
        f"Die Antwort trägt Felder, die ihr Schema nicht kennt: {sorted(unbekannt)}. "
        f"Eine Oberfläche, die gegen das Schema baut, sieht sie nie."
    )


def test_die_selbstauskunft_bleibt_an_den_konstanten_haengen():
    """Abgeschriebene Zahlen veralten still. Diese sind es nicht — der Test hält sie fest."""
    from aiimaging import geometrie_qa, sprache
    from aiimaging.mcp_schemas import WERKZEUGE

    antwort = werkzeuge.capabilities({})
    assert antwort["werkzeuge"] == sorted(WERKZEUGE)
    assert antwort["geometrie_schwelle"] == geometrie_qa.SCHWELLE_GEOMETRIE
    assert antwort["prompt_sprache"]["verfahren"] == sprache.VERFAHREN_GLOSSAR


def test_die_behauptete_uebersetzung_wird_am_verhalten_geprueft():
    """`uebersetzt_deutsch: true` ist eine Behauptung — hier wird sie zur Messung.

    Der Unterschied ist der ganze Punkt dieses Projekts: Eine Selbstauskunft, die nur
    ein `True` trägt, bleibt auch dann grün, wenn jemand die Übersetzung morgen
    ausbaut. Also wird gegen den echten Weg geprüft, den ein Auftrag nimmt.
    """
    from aiimaging import kosmo_szene

    antwort = werkzeuge.capabilities({})
    gelesen = kosmo_szene.lies_szene({
        "schema": kosmo_szene.SCHEMA_SZENE,
        "geometry": {"path": "/irgendwo/haus.glb"},
        "style": {"prompt": "bedeckter Himmel, keine Menschen"},
    })

    assert antwort["prompt_sprache"]["uebersetzt_deutsch"] is True
    assert gelesen["prompt"] == "overcast sky, no people", (
        "die Lane behauptet zu übersetzen — dann muss sie es auch tun"
    )
    assert gelesen["prompt_original"] == "bedeckter Himmel, keine Menschen", (
        "und der ursprüngliche Wortlaut darf dabei nicht verloren gehen"
    )
    for feld in antwort["prompt_sprache"]["deklariert_in"]:
        assert feld in gelesen, f"als deklariert genanntes Feld {feld!r} gibt es gar nicht"


def test_die_vorbehalte_nennen_die_prompt_umschreibung():
    """Wer `style.prompt` schickt, bekommt womöglich einen anderen zurück, als er schickte.

    Das ist keine Fähigkeit, sondern ein Eingriff in die Eingabe des Aufrufers — und
    gehört darum dorthin, wo auch die unkalibrierte Schwelle steht.
    """
    text = " ".join(werkzeuge.capabilities({})["vorbehalte"]).lower()
    assert "prompt" in text and "uebersetzt" in text.replace("übersetzt", "uebersetzt")
    assert "prompt_original" in text, "die Rettungsleine gehört in denselben Satz"
