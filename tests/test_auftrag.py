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


# ======================================================================================
# Der abgeleitete Zustand — der Ordner zählte nicht, was er behauptete
# ======================================================================================

def _hinlegen(tmp_path, kennung="auf-20260828-01", worker=None):
    from aiimaging import auftrag as auf
    satz = {
        "schema": auf.SCHEMA_AUFTRAG, "worker": worker or auf.WORKER_LOCAL,
        "auftrag_id": kennung, "art": "qa", "beschreibung": "Eine Frage.",
        "anweisung": "Was zu tun ist.", "erstellt": "2026-08-28T00:00:00Z",
        "geometrie": {"synthetisch": True, "pfad": None,
                      "erzeugen_mit": "python3 tools/make_test_ifc.py build/t.ifc"},
        "params": {}, "auflagen": ["keine"], "rueckgabe": ["V1 nichts"],
    }
    auf.schreibe_auftrag(satz, tmp_path)
    return kennung


def test_ohne_ergebnis_ist_ein_auftrag_offen(tmp_path):
    from aiimaging import auftrag as auf
    k = _hinlegen(tmp_path)
    assert auf.zustand(k, tmp_path) == auf.ZUSTAND_OFFEN


def test_status_ok_beantwortet_ihn(tmp_path):
    from aiimaging import auftrag as auf
    k = _hinlegen(tmp_path)
    auf.schreibe_ergebnis(auf.baue_ergebnis(auftrag_id=k, status="ok"), tmp_path)
    assert auf.zustand(k, tmp_path) == auf.ZUSTAND_BEANTWORTET
    assert auf.unerledigt(tmp_path) == []


@pytest.mark.parametrize("status", ["fehler", "abgelehnt", "uebersprungen"])
def test_gerechnet_ist_nicht_beantwortet(tmp_path, status):
    """**Der Kern des Entscheids vom 28.08.2026.**

    Ein Auftrag, dessen Ergebnis `fehler` sagt, ist gerechnet worden — beantwortet ist er
    nicht. Bis dahin galt er als erledigt, und acht Aufträge verschwanden so aus der
    Zählung, ohne dass jemand sie beantwortet hätte.
    """
    from aiimaging import auftrag as auf
    k = _hinlegen(tmp_path)
    auf.schreibe_ergebnis(auf.baue_ergebnis(auftrag_id=k, status=status), tmp_path)
    assert auf.zustand(k, tmp_path) == auf.ZUSTAND_GERECHNET
    assert [a["auftrag_id"] for a in auf.unerledigt(tmp_path)] == [k]


def test_ein_weiterleitungsvermerk_ist_keine_antwort(tmp_path):
    """**Gemessen, nicht ausgedacht:** Von zwei `cloud`-Aufträgen mit Ergebnis waren
    zwei von zwei Weiterleitungsvermerke (`auf-20260828-64`).

    Sie tragen `status: ok` — und sind trotzdem keine Antwort. Darum wird `art` **vor**
    `status` gelesen.
    """
    from aiimaging import auftrag as auf
    k = _hinlegen(tmp_path)
    satz = auf.baue_ergebnis(auftrag_id=k, status="ok")
    satz["art"] = "weitergereicht_und_teilbeantwortet"
    auf.schreibe_ergebnis(satz, tmp_path)

    assert auf.zustand(k, tmp_path) == auf.ZUSTAND_WEITERGEREICHT
    assert [a["auftrag_id"] for a in auf.unerledigt(tmp_path)] == [k], (
        "weitergereicht heisst: liegt bei jemand anderem — die Frage ist offen")


def test_ein_zurueckgezogener_auftrag_ist_gegenstandslos(tmp_path):
    """Und **nicht** unbeantwortet. Das sind zwei verschiedene Aussagen."""
    from aiimaging import auftrag as auf
    k = _hinlegen(tmp_path)
    satz = auf.baue_ergebnis(auftrag_id=k, status="ok")
    satz["art"] = "zurueckgezogen"
    auf.schreibe_ergebnis(satz, tmp_path)

    assert auf.zustand(k, tmp_path) == auf.ZUSTAND_ZURUECKGEZOGEN
    assert auf.unerledigt(tmp_path) == []


def test_die_fuenf_zustaende_sind_genau_diese():
    """Von der anderen Seite gezählt. Ein sechster wäre eine neue Kategorie und gehört
    nicht still eingeführt."""
    from aiimaging import auftrag as auf
    assert set(auf.ZUSTAENDE) == {
        "offen", "beantwortet", "gerechnet, nicht beantwortet",
        "weitergereicht", "zurueckgezogen"}
    assert set(auf.UNBEANTWORTET) == {
        "offen", "gerechnet, nicht beantwortet", "weitergereicht"}
    assert auf.ZUSTAND_BEANTWORTET not in auf.UNBEANTWORTET
    assert auf.ZUSTAND_ZURUECKGEZOGEN not in auf.UNBEANTWORTET, (
        "gegenstandslos ist etwas anderes als unbeantwortet")


def test_es_gibt_eine_adresse_fuer_diese_sitzung():
    """Drei Empfänger und kein Absender: Die Vokabel kannte nur eine Richtung."""
    from aiimaging import auftrag as auf
    assert auf.WORKER_KERN in auf.WORKER
    assert len(set(auf.WORKER)) == 4


def test_zustaende_zaehlt_jeden_auftrag(tmp_path):
    from aiimaging import auftrag as auf
    a = _hinlegen(tmp_path, "auf-20260828-01")
    b = _hinlegen(tmp_path, "auf-20260828-02")
    auf.schreibe_ergebnis(auf.baue_ergebnis(auftrag_id=b, status="ok"), tmp_path)

    alle = auf.zustaende(tmp_path)
    assert alle == {a: auf.ZUSTAND_OFFEN, b: auf.ZUSTAND_BEANTWORTET}


def test_ein_kaputter_auftrag_wird_beim_lesen_gemeldet_und_blockiert_die_anderen_nicht(
        tmp_path):
    """**Der Vorschlag der HomeStation** (`auf-20260828-64`, V4) — und ihr eigener Anlass.

    Ihr `auf-63` trug eine Art, die es nicht gibt, und kein `rueckgabe`-Feld. Die Datei
    kam an `schreibe_auftrag` **vorbei** in den Ordner und hat eine ganze Testsammlung rot
    gemacht — zwei Tage lang, und niemand sah warum. `pruefe_auftrag` lief bis dahin nur
    beim **Schreiben**.

    *Gemeldet und nicht geworfen: Eine Prüfung, die den ganzen Ordner unlesbar macht, wird
    abgeschaltet.*
    """
    import json as _json
    from aiimaging import auftrag as auf

    gut = _hinlegen(tmp_path, "auf-20260828-01")
    ordner = tmp_path / auf.VERZ_OFFEN
    (ordner / "auf-20260828-02.json").write_text(_json.dumps({
        "schema": auf.SCHEMA_AUFTRAG, "worker": auf.WORKER_LOCAL,
        "auftrag_id": "auf-20260828-02", "art": "vertrag",
        "beschreibung": "Eine Art, die es nicht gibt.",
        "geometrie": {"synthetisch": True, "pfad": None, "erzeugen_mit": "x"},
        "auflagen": ["keine"],
    }), encoding="utf-8")

    saetze = {a["auftrag_id"]: a for a in auf.offene_auftraege(tmp_path)}
    assert set(saetze) == {gut, "auf-20260828-02"}, "der kaputte blockiert den guten nicht"
    assert not saetze[gut].get("maengel")
    assert any("vertrag" in m for m in saetze["auf-20260828-02"]["maengel"])


def test_ein_fehlerfreier_auftrag_traegt_kein_maengelfeld(tmp_path):
    """Die Gegenprobe — sonst müsste jeder Leser auf eine leere Liste prüfen."""
    from aiimaging import auftrag as auf
    _hinlegen(tmp_path)
    assert "maengel" not in auf.offene_auftraege(tmp_path)[0]


# ======================================================================================
# `art: frage` — die Vokabel kannte drei Sorten Lauf und keine Sorte Frage
# ======================================================================================

def test_frage_ist_eine_art_aber_kein_lauf():
    """**Der Befund vom 01.09.2026, gezählt am eigenen Bestand.**

    Neun der siebzehn offenen `local`-Aufträge trugen `art: qa` und waren gar keine
    Läufe — *«Welche Zahl war 0.6909?»*, *«Warum reicht `/api/mcp/tools` keine Schemata
    durch?»*. **Nicht einer** von den neun war ein Lauf.

    Sie standen auf `qa`, weil es keinen anderen Wert gab. *Eine Ablage, die es nicht
    geben dürfte, füllt sich von selbst.*
    """
    from aiimaging import auftrag as auf
    assert auf.ART_FRAGE in auf.ARTEN
    assert auf.ART_FRAGE not in auf.ARTEN_LAUF
    assert auf.ARTEN_LAUF < auf.ARTEN, "die Läufe sind eine echte Teilmenge"


def test_die_arten_sind_genau_diese_vier():
    """Von der anderen Seite gezählt — eine fünfte wäre eine neue Kategorie und gehört
    nicht still eingeführt."""
    from aiimaging import auftrag as auf
    assert set(auf.ARTEN) == {"multipass", "render", "qa", "frage"}
    assert set(auf.ARTEN_LAUF) == {"multipass", "render", "qa"}


def test_ein_frage_auftrag_ist_ein_gueltiger_auftrag(tmp_path):
    """Er wird geschrieben und gelesen wie jeder andere — nur nicht ausgeführt."""
    from aiimaging import auftrag as auf
    k = _hinlegen(tmp_path, "auf-20260901-01")
    satz = auf.offene_auftraege(tmp_path)[0]
    satz["art"] = auf.ART_FRAGE
    assert auf.pruefe_auftrag(satz) == []


def test_eine_frage_ohne_ergebnis_bleibt_offen(tmp_path):
    """Sie zählt weiter zum Rückstand. **Umtypisieren beantwortet nichts** — es sagt nur,
    wer antworten kann."""
    from aiimaging import auftrag as auf
    k = _hinlegen(tmp_path, "auf-20260901-02")
    assert auf.zustand(k, tmp_path) == auf.ZUSTAND_OFFEN
    assert [a["auftrag_id"] for a in auf.unerledigt(tmp_path)] == [k]


# ======================================================================================
# Der Deckel — was von Hand eingehalten wird, wird irgendwann nicht mehr eingehalten
# ======================================================================================

def _viele(tmp_path, worker, n, ab=1):
    from aiimaging import auftrag as auf
    for i in range(ab, ab + n):
        satz = {
            "schema": auf.SCHEMA_AUFTRAG, "worker": worker,
            "auftrag_id": f"auf-20260901-{i:02d}", "art": "qa",
            "beschreibung": f"Frage Nummer {i}.", "anweisung": "Was zu tun ist.",
            "erstellt": f"2026-09-01T{i:02d}:00:00Z",
            "geometrie": {"synthetisch": True, "pfad": None, "erzeugen_mit": "x"},
            "params": {}, "auflagen": ["keine"], "rueckgabe": ["V1 nichts"],
        }
        auf.schreibe_auftrag(satz, tmp_path)


def test_unter_dem_deckel_geht_es_durch(tmp_path):
    from aiimaging import auftrag as auf
    _viele(tmp_path, auf.WORKER_LOCAL, auf.DECKEL_JE_WORKER - 1)
    assert len(auf.unerledigt(tmp_path)) == auf.DECKEL_JE_WORKER - 1


def test_am_deckel_wird_abgewiesen_und_die_aeltesten_werden_genannt(tmp_path):
    """**Eine Fehlermeldung, die nur «zu viele» sagt, verschiebt die Arbeit des
    Nachsehens auf den nächsten.**"""
    from aiimaging import auftrag as auf
    _viele(tmp_path, auf.WORKER_LOCAL, auf.DECKEL_JE_WORKER)

    with pytest.raises(auf.DeckelError) as fehler:
        _viele(tmp_path, auf.WORKER_LOCAL, 1, ab=90)

    text = str(fehler.value)
    assert "auf-20260901-01" in text, "der aelteste wird beim Namen genannt"
    assert str(auf.DECKEL_JE_WORKER) in text
    assert "Erst schliessen, dann stellen" in text


def test_der_deckel_gilt_je_adressat_und_nicht_insgesamt(tmp_path):
    """Ein voller `local` sperrt `cloud` nicht — die drei können nicht dasselbe."""
    from aiimaging import auftrag as auf
    _viele(tmp_path, auf.WORKER_LOCAL, auf.DECKEL_JE_WORKER)
    _viele(tmp_path, auf.WORKER_CLOUD, 1, ab=50)
    assert len([a for a in auf.unerledigt(tmp_path)
                if a.get("worker") == auf.WORKER_CLOUD]) == 1


def test_ein_beantworteter_auftrag_macht_wieder_platz(tmp_path):
    """**Der ganze Zweck.** Der Deckel sperrt nicht das Denken, sondern das Anhäufen."""
    from aiimaging import auftrag as auf
    _viele(tmp_path, auf.WORKER_LOCAL, auf.DECKEL_JE_WORKER)
    with pytest.raises(auf.DeckelError):
        _viele(tmp_path, auf.WORKER_LOCAL, 1, ab=90)

    auf.schreibe_ergebnis(
        auf.baue_ergebnis(auftrag_id="auf-20260901-01", status="ok"), tmp_path)
    _viele(tmp_path, auf.WORKER_LOCAL, 1, ab=90)          # jetzt geht es


def test_ein_zurueckgezogener_auftrag_macht_ebenfalls_platz(tmp_path):
    """Auch das ist ein Schliessen — nur eines, das zugibt, dass die Frage weg ist."""
    from aiimaging import auftrag as auf
    _viele(tmp_path, auf.WORKER_LOCAL, auf.DECKEL_JE_WORKER)
    e = auf.baue_ergebnis(auftrag_id="auf-20260901-02", status="ok")
    e["art"] = "zurueckgezogen"
    auf.schreibe_ergebnis(e, tmp_path)
    _viele(tmp_path, auf.WORKER_LOCAL, 1, ab=91)


def test_einen_bestehenden_auftrag_zu_aendern_faellt_nicht_unter_den_deckel(tmp_path):
    """Sonst liesse sich am Deckel kein Auftrag mehr **berichtigen** — und genau das war
    heute nötig, neun Mal."""
    from aiimaging import auftrag as auf
    _viele(tmp_path, auf.WORKER_LOCAL, auf.DECKEL_JE_WORKER)
    satz = auf.offene_auftraege(tmp_path)[0]
    satz["art"] = auf.ART_FRAGE
    auf.schreibe_auftrag(satz, tmp_path)                  # dieselbe Kennung: erlaubt
