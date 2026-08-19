"""Die Brückenaufträge — und die Freigabe, die keine ist.

Die Brücke der Designzentrale legt drei Dateien in ein Verzeichnis und **wartet**. Sie
rendert nichts. Genau diese Rolle spielt unser Homeworker schon für unsere eigenen
Aufträge; dieses Modul ist die Übersetzung dazwischen.

Der Befund, um den es hier vor allem geht, steht in ihrem `create_job`::

    "approval_token": f"CONFIRMED_RENDER_{secrets.token_hex(4)}"

**Jeder Auftrag kommt mit einer Freigabe an, die kein Mensch erteilt hat.**
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from aiimaging import bruecke


TOKEN = "CONFIRMED_RENDER_deadbeef"


def auftrag(tmp_path, *, name="vis-1755600000-0f9e2a", status="queued",
            token=TOKEN, mit_modell=True, szene=None) -> Path:
    """Ein Auftragsverzeichnis in der Form, die die fremde Brücke wirklich anlegt."""
    d = tmp_path / name
    d.mkdir(parents=True, exist_ok=True)
    if mit_modell:
        (d / bruecke.DATEI_MODELL).write_bytes(b"glTF\x02\x00\x00\x00")
    (d / bruecke.DATEI_SZENE).write_text(json.dumps(szene or {
        "schema": "kosmovis.render-scene/v1",
        "geometry": {"path": str(d / "model.glb"), "format": "glb"},
        "out": str(d / "out"),
        "render": {"resolution": [1600, 1000], "samples": 128, "faithful": 0.8},
        "vis": {"backbone": "qwen"},
    }))
    zettel = {"job_id": name, "status": status,
              "scene": str(d / bruecke.DATEI_SZENE), "idle_window_only": True,
              "created_at": "2026-08-19T06:00:00Z"}
    if token is not None:
        zettel["approval_token"] = token
    (d / bruecke.DATEI_LAUFZETTEL).write_text(json.dumps(zettel))
    return d


# --------------------------------------------------------------------------------------
# 1 · Die Freigabe, die keine ist
# --------------------------------------------------------------------------------------

def test_der_fremde_token_gilt_ohne_entscheid_NICHT(tmp_path):
    """**Der wichtigste Test dieser Datei.**

    Der Token stammt von der Brücke selbst. Er sieht aus wie unserer, heisst wie unserer
    und bedeutet etwas anderes. Unser `enqueue_render` lässt einen Auftrag ohne
    menschliche Freigabe liegen und rührt die Grafikkarte nicht an — das ist der
    Freeze-Schutz. Wer die fremde Warteschlange bedient, hebelt ihn aus, **ohne dass
    irgendwo etwas rot wird**.
    """
    gelesen = bruecke.lies_auftrag(auftrag(tmp_path))
    assert gelesen["freigegeben"] is False
    assert "kein Mensch" in gelesen["freigabe_grund"].replace("Kein Mensch", "kein Mensch")
    assert any("Freigabe-Token" in m for m in gelesen["maengel"])


def test_der_betreiber_kann_es_ausdruecklich_entscheiden(tmp_path):
    """Unbequem und richtig: Es ist eine Entscheidung des Betreibers, keine des Programms."""
    gelesen = bruecke.lies_auftrag(auftrag(tmp_path), fremde_freigabe_gilt=True)
    assert gelesen["freigegeben"] is True
    assert "ausdrückliche Entscheidung" in gelesen["freigabe_grund"]


def test_der_grund_nennt_die_stelle_im_fremden_code(tmp_path):
    """Ein Verdacht kostet jedes Mal einen Menschen, der nachsieht — eine Diagnose nicht."""
    grund = bruecke.lies_auftrag(auftrag(tmp_path))["freigabe_grund"]
    assert "create_job" in grund
    assert "token_hex" in grund
    assert "fremde_freigabe_gilt=True" in grund


def test_ohne_token_bleibt_der_auftrag_liegen(tmp_path):
    """Das ist der Freeze-Schutz und kein Fehler — auch mit ausdrücklichem Entscheid."""
    for entscheid in (False, True):
        gelesen = bruecke.lies_auftrag(auftrag(tmp_path, token=None),
                                       fremde_freigabe_gilt=entscheid)
        assert gelesen["freigegeben"] is False
        assert "keinen Freigabe-Token" in gelesen["freigabe_grund"]


@pytest.mark.parametrize("token", ["ja bitte", "RENDER_OK", "confirmed_render_x", 42])
def test_ein_token_falscher_form_gilt_nie(tmp_path, token):
    gelesen = bruecke.lies_auftrag(auftrag(tmp_path, token=token),
                                   fremde_freigabe_gilt=True)
    assert gelesen["freigegeben"] is False
    assert "vereinbarte Form" in gelesen["freigabe_grund"]


# --------------------------------------------------------------------------------------
# 2 · Lesen
# --------------------------------------------------------------------------------------

def test_die_szene_kommt_uebersetzt_zurueck(tmp_path):
    gelesen = bruecke.lies_auftrag(auftrag(tmp_path))
    assert gelesen["szene"]["aufloesung"] == 1600
    assert gelesen["szene"]["hoehe"] == 1000
    assert gelesen["szene"]["controlnet_staerke"] == 0.8


def test_die_szene_wird_NEBEN_dem_laufzettel_gelesen_und_nicht_ueber_seinen_pfad(tmp_path):
    """Der Pfad im Laufzettel ist absolut und stammt von einem fremden Rechner.

    Er zeigt dort auf ein Verzeichnis, das es bei uns nicht gibt. Nur die Datei neben dem
    Laufzettel liegt sicher hier — und das ist die einzige, der man trauen kann.
    """
    d = auftrag(tmp_path)
    zettel = json.loads((d / bruecke.DATEI_LAUFZETTEL).read_text())
    zettel["scene"] = "/gibt/es/hier/nicht/render-scene.json"
    (d / bruecke.DATEI_LAUFZETTEL).write_text(json.dumps(zettel))
    assert bruecke.lies_auftrag(d)["szene"]["aufloesung"] == 1600


def test_eine_fehlende_geometrie_ist_ein_mangel(tmp_path):
    gelesen = bruecke.lies_auftrag(auftrag(tmp_path, mit_modell=False))
    assert any("Geometrie fehlt" in m for m in gelesen["maengel"])


def test_ein_ordner_mit_falschem_namen_wird_gelesen_aber_gemeldet(tmp_path):
    """Ihre eigene Auflistung übergeht solche Ordner möglicherweise — das ist der Grund."""
    gelesen = bruecke.lies_auftrag(auftrag(tmp_path, name="mein-eigener-ordner"))
    assert any("Form der fremden" in w for w in gelesen["warnungen"])


def test_ohne_verzeichnis_gibt_es_nichts_zu_lesen(tmp_path):
    with pytest.raises(bruecke.BrueckenError, match="Kein Auftragsverzeichnis"):
        bruecke.lies_auftrag(tmp_path / "gibtsnicht")


def test_ein_unlesbarer_laufzettel_wird_benannt(tmp_path):
    d = auftrag(tmp_path)
    (d / bruecke.DATEI_LAUFZETTEL).write_text("{kein json")
    with pytest.raises(bruecke.BrueckenError, match="kein lesbares JSON"):
        bruecke.lies_auftrag(d)


# --------------------------------------------------------------------------------------
# 3 · Die Warteschlange
# --------------------------------------------------------------------------------------

def test_offene_auftraege_kommen_in_eingangsreihenfolge(tmp_path):
    """Der Verzeichnisname trägt den Zeitstempel — wer zuerst kam, wird zuerst bedient.

    Alles andere wäre für den Wartenden nicht nachvollziehbar.
    """
    auftrag(tmp_path, name="vis-1755600300-bbbbbb")
    auftrag(tmp_path, name="vis-1755600100-aaaaaa")
    namen = [d.name for d in bruecke.offene_auftraege(tmp_path)]
    assert namen == ["vis-1755600100-aaaaaa", "vis-1755600300-bbbbbb"]


def test_nur_wartende_auftraege(tmp_path):
    auftrag(tmp_path, name="vis-1755600100-aaaaaa", status="queued")
    auftrag(tmp_path, name="vis-1755600200-bbbbbb", status="done")
    assert [d.name for d in bruecke.offene_auftraege(tmp_path)] == ["vis-1755600100-aaaaaa"]


def test_halb_geschriebene_ordner_werden_uebersprungen_und_nicht_gemeldet(tmp_path):
    """Sie sind der Normalfall, während die Brücke gerade schreibt.

    Wer sie melden wollte, bekäme bei jedem Durchlauf eine Warnung über einen Ordner, der
    eine Sekunde später in Ordnung ist — und würde die Warnungen bald überlesen.
    """
    (tmp_path / "vis-1755600100-aaaaaa").mkdir()                       # noch kein Zettel
    (tmp_path / "vis-1755600200-bbbbbb").mkdir()
    (tmp_path / "vis-1755600200-bbbbbb" / bruecke.DATEI_LAUFZETTEL).write_text("{halb")
    auftrag(tmp_path, name="vis-1755600300-cccccc")
    assert [d.name for d in bruecke.offene_auftraege(tmp_path)] == ["vis-1755600300-cccccc"]


def test_fremde_ordner_werden_nicht_angefasst(tmp_path):
    (tmp_path / "irgendwas").mkdir()
    (tmp_path / "irgendwas" / bruecke.DATEI_LAUFZETTEL).write_text('{"status":"queued"}')
    assert bruecke.offene_auftraege(tmp_path) == []


def test_ein_fehlender_ablageort_ist_kein_absturz(tmp_path):
    assert bruecke.offene_auftraege(tmp_path / "gibtsnicht") == []


# --------------------------------------------------------------------------------------
# 4 · Schreiben
# --------------------------------------------------------------------------------------

def test_das_ergebnis_liegt_VOR_dem_status(tmp_path):
    """**Die ganze Sorgfalt dieser Funktion steckt in der Reihenfolge.**

    Die fremde Oberfläche liest den Laufzettel; steht dort `done`, holt sie das Ergebnis.
    Wer den Laufzettel zuerst setzt, erzeugt ein Zeitfenster, in dem sie ein Ergebnis
    sucht, das noch nicht da ist — und einen Fehler meldet, den niemand nachstellen kann.
    """
    d = auftrag(tmp_path)
    bruecke.schreibe_ergebnis(d, ["/wo/auch/immer/cam-01.png"])
    assert (d / bruecke.DATEI_ERGEBNIS).is_file()
    assert json.loads((d / bruecke.DATEI_LAUFZETTEL).read_text())["status"] == "done"
    # Und die Datei ist vollständig, nicht halb geschrieben:
    json.loads((d / bruecke.DATEI_ERGEBNIS).read_text())


def test_bilder_werden_auf_dateinamen_gekuerzt(tmp_path):
    """Ihre Oberfläche holt Bilder über einen Endpunkt, der nur den Namen kennt.

    Ein absoluter Pfad ginge dort ins Leere — und trüge nebenbei einen Rechnernamen nach
    draussen (Regel 3).
    """
    d = auftrag(tmp_path)
    bruecke.schreibe_ergebnis(d, ["/home/jemand/geheim/out/cam-01.png"])
    ergebnis = json.loads((d / bruecke.DATEI_ERGEBNIS).read_text())
    assert ergebnis["images"] == ["cam-01.png"]
    assert "geheim" not in (d / bruecke.DATEI_ERGEBNIS).read_text()


def test_das_ergebnis_traegt_ihre_schemakennung(tmp_path):
    d = auftrag(tmp_path)
    bruecke.schreibe_ergebnis(d, [])
    ergebnis = json.loads((d / bruecke.DATEI_ERGEBNIS).read_text())
    assert ergebnis["schema"] == "kosmovis.render-result/v2"
    assert ergebnis["job_id"] == "vis-1755600000-0f9e2a"


def test_unsere_hinweise_stehen_nicht_in_der_datei(tmp_path):
    """Ihr Schema kennt sie nicht — geschrieben wird die strikte Fassung."""
    d = auftrag(tmp_path)
    bruecke.schreibe_ergebnis(d, [])
    assert "hinweise" not in json.loads((d / bruecke.DATEI_ERGEBNIS).read_text())


def test_ein_fehlschlag_setzt_status_und_grund(tmp_path):
    d = auftrag(tmp_path)
    bruecke.setze_status(d, bruecke.STATUS_ERROR, fehler="Torwächter: Massstab")
    zettel = json.loads((d / bruecke.DATEI_LAUFZETTEL).read_text())
    assert zettel["status"] == "error"
    assert zettel["error"] == "Torwächter: Massstab"
    assert "updated_at" in zettel


def test_ein_unbekannter_status_wird_abgewiesen(tmp_path):
    """Es wird nicht auf einen Vorgabewert zurückgesetzt — welcher gilt, kann dieses
    Modul nicht für den Aufrufer entscheiden."""
    with pytest.raises(bruecke.BrueckenError, match="Unbekannter Status"):
        bruecke.setze_status(auftrag(tmp_path), "fertig-glaub-ich")


def test_der_status_wird_atomar_geschrieben(tmp_path):
    """Die fremde Oberfläche liest im Sekundentakt; ein halbes JSON wäre für sie ein
    Fehler, und sie hätte recht."""
    d = auftrag(tmp_path)
    bruecke.setze_status(d, bruecke.STATUS_RUNNING)
    assert not list(d.glob("*.teil")), "die Zwischendatei ist liegengeblieben"


def test_ohne_kennung_gibt_es_kein_ergebnis(tmp_path):
    d = auftrag(tmp_path)
    zettel = json.loads((d / bruecke.DATEI_LAUFZETTEL).read_text())
    del zettel["job_id"]
    (d / bruecke.DATEI_LAUFZETTEL).write_text(json.dumps(zettel))
    with pytest.raises(bruecke.BrueckenError, match="job_id"):
        bruecke.schreibe_ergebnis(d, [])


def test_die_qa_wandert_mit_ihren_feldnamen_hinein(tmp_path):
    """Und mit UNSEREN Schwellen — siehe `kosmo_szene.als_ergebnis`."""
    from aiimaging import stil_qa
    d = auftrag(tmp_path)
    bruecke.schreibe_ergebnis(
        d, ["cam-01.png"],
        geometrie_urteil={"score": 0.8, "spearman": -0.9, "geom_iou": 0.7,
                          "schwelle": 0.65, "bestanden": True},
        stil_urteil={"score": 0.7, "schwelle": stil_qa.SCHWELLE_STIL,
                     "einbetter_name": "siglip2-base", "bestanden": True})
    qa = json.loads((d / bruecke.DATEI_ERGEBNIS).read_text())["qa"]
    assert qa["geometry"]["geom_iou"] == 0.7
    assert qa["style"]["threshold"] == stil_qa.SCHWELLE_STIL     # NICHT ihre 0.3
    assert qa["verdict"]["passed"] is True
