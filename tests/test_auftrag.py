"""Das Auftragsprotokoll zur HomeStation.

Bewacht vor allem Regel 3: Über diesen Ordner darf nichts reisen, was aus echten
Projekten stammt. Der Auftrag verweist auf Geometrie, das Ergebnis trägt nur Zahlen.
"""
from __future__ import annotations

import json

import pytest

from aiimaging import auftrag as auf


@pytest.fixture
def gueltig():
    return auf.baue_auftrag(auftrag_id="auf-20260818-01", art="multipass",
                            beschreibung="Testlauf der vollen Kette", synthetisch=True)


# ── Regel 3 in ausführbarer Form ─────────────────────────────────────────────────────

def test_ergebnis_weist_eingebettete_bilddaten_ab():
    """Ein PNG als base64 im Ergebnis wäre ein Render im Repo — genau das verbietet Regel 3."""
    with pytest.raises(auf.AuftragError, match="Bilddaten"):
        auf.baue_ergebnis(auftrag_id="auf-1", status="ok",
                          messwerte={"vorschau": "iVBORw0KGgoAAAANSUhEUg"})


def test_ergebnis_weist_data_uri_ab():
    with pytest.raises(auf.AuftragError, match="Bilddaten"):
        auf.baue_ergebnis(auftrag_id="auf-1", status="ok",
                          urteil={"bild": "data:image/png;base64,AAAA"})


def test_ergebnis_weist_verdaechtig_lange_zeichenketten_ab():
    """Auch ohne erkennbaren Präfix: 5000 Zeichen sind keine Messgrösse."""
    with pytest.raises(auf.AuftragError, match="eingebetteten Daten"):
        auf.baue_ergebnis(auftrag_id="auf-1", status="ok", messwerte={"roh": "x" * 5000})


def test_dateinamen_sind_erlaubt():
    """Gegenprobe: Der Name einer Datei ist erwünscht, nur ihr Inhalt nicht."""
    satz = auf.baue_ergebnis(auftrag_id="auf-1", status="ok",
                             messwerte={"dateien": ["tiefe_0001.exr", "beauty.png"]})
    assert satz["messwerte"]["dateien"] == ["tiefe_0001.exr", "beauty.png"]


def test_bilddaten_werden_auch_verschachtelt_gefunden():
    """Eine Prüfung nur auf oberster Ebene wäre leicht zu umgehen."""
    with pytest.raises(auf.AuftragError):
        auf.baue_ergebnis(auftrag_id="auf-1", status="ok",
                          messwerte={"tief": {"drin": ["data:image/png;base64,AA"]}})


# ── Geometriequelle ──────────────────────────────────────────────────────────────────

def test_ohne_synthetisch_braucht_es_einen_pfad():
    """Geometrie darf nicht über das Repo reisen — also muss sie drüben liegen."""
    with pytest.raises(auf.AuftragError, match="geometrie_pfad"):
        auf.baue_auftrag(auftrag_id="a", art="render", beschreibung="x", synthetisch=False)


def test_beide_quellen_zugleich_sind_mehrdeutig():
    with pytest.raises(auf.AuftragError, match="mehrdeutig"):
        auf.baue_auftrag(auftrag_id="a", art="render", beschreibung="x",
                         synthetisch=True, geometrie_pfad="/ai/x.ifc")


def test_synthetischer_auftrag_traegt_die_erzeugungsanweisung(gueltig):
    """Eine frische Sitzung auf der HomeStation muss ohne Rückfrage wissen, was zu tun ist."""
    assert "make_test_ifc" in gueltig["geometrie"]["erzeugen_mit"]


def test_beschreibung_ist_pflicht():
    """Ein Auftrag ohne Begründung ist später nicht mehr einzuordnen."""
    with pytest.raises(auf.AuftragError, match="Beschreibung"):
        auf.baue_auftrag(auftrag_id="a", art="qa", beschreibung="   ")


def test_unbekannte_art_wird_gemeldet():
    with pytest.raises(auf.AuftragError, match="Unbekannte Art"):
        auf.baue_auftrag(auftrag_id="a", art="zaubern", beschreibung="x")


# ── Hardware-Auflagen ────────────────────────────────────────────────────────────────

def test_auflagen_reisen_immer_mit(gueltig):
    """Die 5090 löst ohne Leistungsgrenze die Schutzschaltung aus — das darf nicht verloren gehen."""
    a = gueltig["auflagen"]
    assert a["leistungsgrenze_w"] == 400
    assert a["nur_bei_leerlauf"] is True
    assert a["leerlauf_schwelle_w"] == 120


def test_rueckgabehinweis_nennt_regel_3(gueltig):
    assert gueltig["rueckgabe"]["nur_zahlen"] is True


# ── Pfad-Trickserei ──────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("boese", ["../daneben", "a/b", "..", "", ".versteckt", "a\\b"])
def test_kennung_ist_ein_name_kein_pfad(boese):
    """Die Kennung wird zum Dateinamen im Repo — Positivliste statt Verbotsliste."""
    with pytest.raises(auf.AuftragError):
        auf.baue_auftrag(auftrag_id=boese, art="qa", beschreibung="x")


def test_ergebnis_kennung_wird_ebenso_geprueft():
    with pytest.raises(auf.AuftragError):
        auf.baue_ergebnis(auftrag_id="../boese", status="ok")


# ── Rundlauf über das Dateisystem ────────────────────────────────────────────────────

def test_auftrag_schreiben_und_wiederfinden(tmp_path, gueltig):
    auf.schreibe_auftrag(gueltig, tmp_path)

    gelesen = auf.offene_auftraege(tmp_path)

    assert [a["auftrag_id"] for a in gelesen] == ["auf-20260818-01"]


def test_ohne_verzeichnis_ist_die_liste_leer_und_kein_fehler(tmp_path):
    """Vor dem ersten Auftrag gibt es kein Verzeichnis — ein Poller darf nicht abbrechen."""
    assert auf.offene_auftraege(tmp_path) == []


def test_unerledigt_wird_leer_sobald_ein_ergebnis_vorliegt(tmp_path, gueltig):
    auf.schreibe_auftrag(gueltig, tmp_path)
    assert len(auf.unerledigt(tmp_path)) == 1

    auf.schreibe_ergebnis(auf.baue_ergebnis(auftrag_id=gueltig["auftrag_id"], status="ok"),
                          tmp_path)

    assert auf.unerledigt(tmp_path) == []


def test_ergebnis_vor_dem_lauf_ist_none(tmp_path, gueltig):
    auf.schreibe_auftrag(gueltig, tmp_path)
    assert auf.lies_ergebnis(gueltig["auftrag_id"], tmp_path) is None


def test_schreiben_hinterlaesst_keine_temporaeren_reste(tmp_path, gueltig):
    """Atomar: ein abgebrochener Schreibvorgang darf nichts Halbes im Repo lassen."""
    auf.schreibe_auftrag(gueltig, tmp_path)

    dateien = sorted(p.name for p in (tmp_path / auf.VERZ_OFFEN).iterdir())

    assert dateien == ["auf-20260818-01.json"]


def test_unlesbarer_auftrag_wird_gemeldet_statt_uebergangen(tmp_path):
    """Still überspringen hiesse: ein Auftrag verschwindet unbemerkt."""
    verz = tmp_path / auf.VERZ_OFFEN
    verz.mkdir(parents=True)
    (verz / "kaputt.json").write_text("{kein json", encoding="utf-8")

    with pytest.raises(auf.AuftragError, match="unlesbar"):
        auf.offene_auftraege(tmp_path)


def test_unvollstaendiger_auftrag_wird_nicht_geschrieben(tmp_path):
    with pytest.raises(auf.AuftragError, match="unvollständig"):
        auf.schreibe_auftrag({"schema": auf.SCHEMA_AUFTRAG}, tmp_path)


def test_auftrag_ist_json_faehig(gueltig):
    """Er geht über Git — er muss sich verlustfrei schreiben und lesen lassen."""
    assert json.loads(json.dumps(gueltig)) == gueltig


# ── Der echte Auftrag im Repo ────────────────────────────────────────────────────────

def test_der_abgelegte_auftrag_erfuellt_den_vertrag():
    """Was wirklich im Repo liegt, muss die Prüfung bestehen — nicht nur was Tests bauen."""
    from pathlib import Path
    wurzel = Path(__file__).resolve().parents[1]

    for satz in auf.offene_auftraege(wurzel):
        assert auf.pruefe_auftrag(satz) == [], satz["auftrag_id"]
