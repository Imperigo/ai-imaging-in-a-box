"""Kommt ein über den MCP-Einlass bestellter Render beim Abholer an?

Der Befund, der diese Datei nötig gemacht hat
---------------------------------------------
Nachgezählt am 26.08.2026: ``werkzeuge.enqueue_render`` legte den Auftrag in einem
Verzeichnis ab, das **niemand ausführte**. Ein Knoten in KosmoOrbit konnte einen Render
bestellen, der Auftrag ging mit Freigabe sogar auf ``queued`` — und blieb dort.

Der Test unten ist darum kein Bausteintest, sondern die **Gegenprobe zum Anschluss**: Er
geht den ganzen Weg von ``enqueue_render`` bis zum geschriebenen Vertragsergebnis. Nur
der Renderlauf selbst ist eine Attrappe; alles davor und danach ist echt.
"""
from __future__ import annotations

import json

import pytest

from aiimaging import abholer, eigene_quelle, jobs, kosmo_naht, werkzeuge

TOKEN = jobs.TOKEN_PRAEFIX + "TEST"


@pytest.fixture()
def store(tmp_path, monkeypatch):
    """Eine eigene Ablage — **nie** die des Benutzers."""
    ziel = tmp_path / "aiimaging-jobs"
    monkeypatch.setenv(werkzeuge.UMGEBUNG_JOBS, str(ziel))
    return ziel


@pytest.fixture()
def glb(tmp_path):
    """Eine Datei, die es gibt. Der Inhalt spielt keine Rolle — geladen wird sie hier nie."""
    pfad = tmp_path / "modell.glb"
    pfad.write_bytes(b"glTF-Attrappe")
    return pfad


def _bestelle(glb, **zusatz) -> dict:
    argumente = {"glb_path": str(glb), "up_axis": "Y",
                 "bbox": [[0, 0, 0], [20, 15, 10]], "approval_token": TOKEN}
    argumente.update(zusatz)
    return werkzeuge.enqueue_render(argumente)


def _attrappe(gesehen: list):
    def verarbeite(auftrag):
        gesehen.append(auftrag)
        return {"bilder": ["kamera_s.png"], "geometrie_urteil": {"passed": True},
                "stil_urteil": None, "kameras": [], "zeiten": {"gesamt": 1.0}}
    return verarbeite


# ── Der Anschluss selbst ─────────────────────────────────────────────────────────────

def test_ein_ueber_mcp_bestellter_render_wird_auch_ausgefuehrt(store, glb):
    """**Die Gegenprobe zum Anschluss.** Vor dem 26.08.2026 blieb dieser Auftrag liegen."""
    antwort = _bestelle(glb)
    assert antwort["error"] is None
    assert antwort["status"] == jobs.STATUS_QUEUED

    gesehen: list = []
    bericht = abholer.durchgang(store, verarbeite=_attrappe(gesehen),
                                quelle=eigene_quelle,
                                darf_rechnen=lambda: (True, "frei"))

    assert bericht["gesehen"] == 1, "Der Abholer hat die eigene Ablage nicht gefunden."
    assert bericht["verarbeitet"] == 1, bericht["ergebnisse"]
    assert len(gesehen) == 1, "Der Auftrag erreichte die Kette nicht."

    nachher = werkzeuge.query_render({"job_id": antwort["job_id"]})
    assert nachher["status"] == jobs.STATUS_DONE
    assert nachher["images"] == ["kamera_s.png"]


def test_das_vertragsergebnis_liegt_neben_dem_auftrag(store, glb):
    """Denselben Vertrag unter demselben Dateinamen wie bei der Brücke.

    Sonst hinge die Form der Antwort daran, welchen Weg die Bestellung genommen hat.
    """
    antwort = _bestelle(glb)
    abholer.durchgang(store, verarbeite=_attrappe([]), quelle=eigene_quelle,
                      darf_rechnen=lambda: (True, "frei"))
    datei = store / antwort["job_id"] / eigene_quelle.DATEI_ERGEBNIS
    assert datei.is_file(), "Kein render-result.json neben dem Auftrag."
    inhalt = json.loads(datei.read_text(encoding="utf-8"))
    assert inhalt["job_id"] == antwort["job_id"]


def test_ohne_freigabe_wird_nichts_gerechnet(store, glb):
    """Der Freeze-Schutz gilt auf diesem Weg genauso — er ist der Sinn der Dreiteilung."""
    antwort = _bestelle(glb, approval_token=None)
    assert antwort["status"] == jobs.STATUS_AWAITING

    gesehen: list = []
    bericht = abholer.durchgang(store, verarbeite=_attrappe(gesehen),
                                quelle=eigene_quelle,
                                darf_rechnen=lambda: (True, "frei"))
    assert bericht["gesehen"] == 0, "Ein nicht freigegebener Auftrag wurde angefasst."
    assert not gesehen


def test_die_vorgabeaufloesung_kommt_aus_dem_vertrag_und_nicht_aus_dem_einlass(store, glb):
    """Bis zum 26.08.2026 setzte der MCP-Einlass 512 — eine zweite Vorgabe für dieselbe Sache.

    Derselbe Auftrag ergab damit je nach Weg ein anderes Bild, ohne dass es irgendwo stand.
    """
    _bestelle(glb)
    gesehen: list = []
    abholer.durchgang(store, verarbeite=_attrappe(gesehen), quelle=eigene_quelle,
                      darf_rechnen=lambda: (True, "frei"))
    szene = gesehen[0]["szene"]
    assert szene["aufloesung"] != 512, (
        "Der MCP-Einlass setzt wieder eine eigene Auflösung. Es gibt genau eine Stelle, "
        "an der eine Vorgabe stehen darf, und das ist der Vertrag."
    )
    assert szene["aufloesung"] == 1600


def test_eine_bestellte_aufloesung_kommt_an(store, glb):
    """Sonst wäre das Feld ein Bedienelement ohne Wirkung."""
    _bestelle(glb, aufloesung=768)
    gesehen: list = []
    abholer.durchgang(store, verarbeite=_attrappe(gesehen), quelle=eigene_quelle,
                      darf_rechnen=lambda: (True, "frei"))
    assert gesehen[0]["szene"]["aufloesung"] == 768


# ── Die Hochachse: was der Vertrag nicht tragen kann ────────────────────────────────

def test_die_hochachse_des_auftrags_erreicht_den_auftrag(store, glb):
    """``kosmovis.render-scene/v1`` hat kein Feld dafür — sie steht darum daneben.

    Ohne das wäre eine Z-up-glb unter der Annahme Y-up gerendert worden: Tiefenkarte,
    Kamera und Geometrie-QA gemeinsam verdreht, am einzelnen Bild nicht erkennbar.
    """
    _bestelle(glb, up_axis="Z")
    gesehen: list = []
    abholer.durchgang(store, verarbeite=_attrappe(gesehen), quelle=eigene_quelle,
                      darf_rechnen=lambda: (True, "frei"))
    assert gesehen[0]["hochachse"] == "Z"


def test_ein_auftrag_der_bruecke_hat_keine_hochachse_und_das_ist_kein_fehler():
    """Die Annahme bleibt die Annahme — und wird als solche gemeldet, nicht verschwiegen."""
    uebersetzt = kosmo_naht.als_render_scene(
        {"job_id": "x", "params": {"glb_path": "/tmp/x.glb"}})
    assert "up_axis" not in uebersetzt["ausserhalb"]
    assert any("Y-up" in h for h in uebersetzt["hinweise"]), (
        "Eine unausgesprochene Annahme ist die schlimmste Sorte."
    )


# ── Die Quelle selbst ────────────────────────────────────────────────────────────────

def test_eine_fehlende_geometrie_ist_ein_mangel_und_kein_absturz(store, glb):
    """Bei einem Auftrag aus dem Cockpit ist das nach einem Neustart der Regelfall."""
    antwort = _bestelle(glb)
    glb.unlink()
    auftrag = eigene_quelle.lies_auftrag(store / antwort["job_id"])
    assert auftrag["maengel"], "Eine verschwundene glb fiel niemandem auf."
    assert auftrag["modell"] is None


def test_fremde_freigabe_wirkt_hier_nicht_und_sagt_es(store, glb):
    """Ein Schalter ohne Wirkung, der schweigt, ist schlimmer als ein fehlender."""
    antwort = _bestelle(glb)
    auftrag = eigene_quelle.lies_auftrag(store / antwort["job_id"],
                                         fremde_freigabe_gilt=True)
    assert any("bewirkt hier nichts" in w for w in auftrag["warnungen"])


def test_der_abholer_kann_sich_die_freigabe_nicht_selbst_erteilen(store, glb):
    """``queued`` führt allein über ``jobs.freigeben`` mit gültigem Token."""
    antwort = _bestelle(glb, approval_token=None)
    ordner = store / antwort["job_id"]
    with pytest.raises(jobs.UebergangError):
        eigene_quelle.setze_status(ordner, jobs.STATUS_QUEUED)


def test_offene_auftraege_uebergeht_was_kein_auftrag_ist(store, glb):
    """Während geschrieben wird, liegt regelmässig Halbfertiges herum."""
    _bestelle(glb)
    (store / "kein-auftrag").mkdir()
    (store / "kein-auftrag" / "kein-auftrag.json").write_text("{kaputt", encoding="utf-8")
    assert len(eigene_quelle.offene_auftraege(store)) == 1


def test_der_waisenfund_wirkt_auch_auf_dieser_ablage(store, glb):
    """Die zweite Quelle darf ihn nicht still ausschalten — darum ``laufzettel_pfad``."""
    antwort = _bestelle(glb)
    ordner = store / antwort["job_id"]
    eigene_quelle.setze_status(ordner, jobs.STATUS_RUNNING)
    gefunden = abholer.waisen(store, frist_s=0.0, quelle=eigene_quelle,
                              _uhr=lambda: 10**12)
    assert [w["job_id"] for w in gefunden] == [antwort["job_id"]]
