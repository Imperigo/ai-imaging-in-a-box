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
        "params": {},
        # DIE HARDWARE-AUFLAGEN GEHOEREN HIER HIN, seit dem 01.09.2026 auch geprueft.
        # Vorher stand hier `["keine"]` — also genau die Prosaform, die `darf_starten`
        # zum Absturz brachte. *Die Attrappe baute die kaputte Gestalt nach, und darum
        # konnte keine Probe den Fehler sehen.*
        "auflagen": {"leistungsgrenze_w": auf.LEISTUNGSGRENZE_W,
                     "nur_bei_leerlauf": True,
                     "hinweise": ["keine"]},
        "rueckgabe": ["V1 nichts"],
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
            "params": {},
            "auflagen": {"leistungsgrenze_w": auf.LEISTUNGSGRENZE_W,
                         "nur_bei_leerlauf": True},
            "rueckgabe": ["V1 nichts"],
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


# ======================================================================================
# Hat dieser Adressat je geantwortet?
# ======================================================================================
#
# Der Anlass ist eine Messung vom 01.09.2026: `ui` trug vier Aufträge und hatte NIE
# geantwortet, `cloud` sieben und ebenfalls nie — die zwei Ergebnisse dort waren
# Weiterleitungsvermerke der HomeStation. In einer Rückstandsliste sieht das aus wie jeder
# andere Rückstand, und es verlangt das Gegenteil: nicht Geduld, sondern einen anderen
# Zustellweg.

def _mit_ergebnis(tmp_path, kennung, worker, *, art=None, **ergebnis):
    """Auftrag ablegen, wahlweise mit Ergebnis.

    ``art`` wird NACH `baue_ergebnis` gesetzt, weil die Funktion kein solches Feld kennt:
    Die beiden Weiterleitungsvermerke, um die es hier geht, sind von Hand geschrieben
    worden. *Genau darum hat sie niemand als Sonderfall bemerkt.*
    """
    auf.schreibe_auftrag(auf.baue_auftrag(auftrag_id=kennung, art="qa",
                                          beschreibung="x", worker=worker), tmp_path)
    if ergebnis:
        satz = auf.baue_ergebnis(auftrag_id=kennung, **ergebnis)
        if art:
            satz["art"] = art
        auf.schreibe_ergebnis(satz, tmp_path)


def test_ein_adressat_ohne_ergebnis_hat_nie_geantwortet(tmp_path):
    _mit_ergebnis(tmp_path, "auf-a", auf.WORKER_UI)
    verhalten = auf.antwortverhalten(tmp_path)
    assert verhalten[auf.WORKER_UI]["n_antworten"] == 0
    assert verhalten[auf.WORKER_UI]["letzte_antwort"] is None


def test_ein_weiterleitungsvermerk_ist_keine_antwort(tmp_path):
    """**Der Fehler, den diese Funktion messen soll.** Ein Vermerk trägt `status: ok` —
    über die Ergebnisdatei gezählt hätte `cloud` wie ein antwortender Adressat ausgesehen.
    Er steht als eigene Zahl daneben, nicht in der ersten."""
    _mit_ergebnis(tmp_path, "auf-a", auf.WORKER_CLOUD, status="ok",
                  art="weitergereicht — Vertragsfragen, keine Messung")
    verhalten = auf.antwortverhalten(tmp_path)
    assert verhalten[auf.WORKER_CLOUD]["n_antworten"] == 0
    assert verhalten[auf.WORKER_CLOUD]["n_weitergereicht"] == 1
    assert verhalten[auf.WORKER_CLOUD]["letzte_antwort"] is None


def test_ein_fehlschlag_ist_keine_antwort_aber_auch_keine_weiterleitung(tmp_path):
    _mit_ergebnis(tmp_path, "auf-a", auf.WORKER_LOCAL, status="fehler")
    verhalten = auf.antwortverhalten(tmp_path)
    assert verhalten[auf.WORKER_LOCAL]["n_antworten"] == 0
    assert verhalten[auf.WORKER_LOCAL]["n_gerechnet"] == 1


def test_eine_echte_antwort_wird_gezaehlt_und_datiert(tmp_path):
    _mit_ergebnis(tmp_path, "auf-a", auf.WORKER_LOCAL, status="ok")
    verhalten = auf.antwortverhalten(tmp_path)
    assert verhalten[auf.WORKER_LOCAL]["n_antworten"] == 1
    assert verhalten[auf.WORKER_LOCAL]["letzte_antwort"], "ohne Datum ist es keine Auskunft"


def test_die_juengste_antwort_gewinnt(tmp_path):
    _mit_ergebnis(tmp_path, "auf-a", auf.WORKER_LOCAL)
    _mit_ergebnis(tmp_path, "auf-b", auf.WORKER_LOCAL)
    auf.schreibe_ergebnis({**auf.baue_ergebnis(auftrag_id="auf-a", status="ok"),
                           "beendet": "2026-08-01T10:00:00Z"}, tmp_path)
    auf.schreibe_ergebnis({**auf.baue_ergebnis(auftrag_id="auf-b", status="ok"),
                           "beendet": "2026-08-28T11:19:01Z"}, tmp_path)
    assert (auf.antwortverhalten(tmp_path)[auf.WORKER_LOCAL]["letzte_antwort"]
            == "2026-08-28T11:19:01Z")


def test_nie_geantwortet_nennt_nur_adressaten_bei_denen_etwas_liegt(tmp_path):
    """*Ein Adressat ohne offene Aufträge schweigt zu Recht.* Gefragt ist nicht «wer war
    still?», sondern «wo warten wir auf jemanden, der sich noch nie gemeldet hat?»."""
    _mit_ergebnis(tmp_path, "auf-a", auf.WORKER_UI)                      # offen, stumm
    _mit_ergebnis(tmp_path, "auf-b", auf.WORKER_LOCAL, status="ok")      # hat geantwortet
    assert auf.nie_geantwortet(tmp_path) == [auf.WORKER_UI]


def test_wer_einmal_geantwortet_hat_gilt_nicht_mehr_als_stumm(tmp_path):
    """Die Gegenprobe: Ein einziger Beleg reicht, und die Rückfrage hört auf. Sonst wäre
    sie eine Dauerwarnung — und die verdeckt die echten."""
    _mit_ergebnis(tmp_path, "auf-a", auf.WORKER_UI, status="ok")
    _mit_ergebnis(tmp_path, "auf-b", auf.WORKER_UI)
    assert auf.nie_geantwortet(tmp_path) == []


# ======================================================================================
# Der Rang — welcher Auftrag zuerst gerechnet wird
# ======================================================================================

def test_ein_rang_der_keine_zahl_ist_wird_gemeldet():
    """*Er sortierte still ans Ende und saehe im Auftrag trotzdem gesetzt aus.*"""
    satz = auf.baue_auftrag(auftrag_id="auf-a", art="qa", beschreibung="x")
    satz["rang"] = "zwei"
    assert any("rang" in m for m in auf.pruefe_auftrag(satz))


@pytest.mark.parametrize("boese", [0, -1, 1.5, True])
def test_null_negativ_gebrochen_und_wahr_sind_keine_raenge(boese):
    """`True` steht ausdruecklich dabei: In Python ist es eine ganze Zahl mit dem Wert 1
    und waere sonst der Rang der Spitze."""
    satz = auf.baue_auftrag(auftrag_id="auf-a", art="qa", beschreibung="x")
    satz["rang"] = boese
    assert any("rang" in m for m in auf.pruefe_auftrag(satz))


def test_ein_auftrag_ohne_rang_bleibt_gueltig():
    """Rund sechzig bestehende haben keinen. Ein Pflichtfeld haette sie alle angefasst,
    um eine Zahl zu erfinden."""
    assert auf.pruefe_auftrag(
        auf.baue_auftrag(auftrag_id="auf-a", art="qa", beschreibung="x")) == []


def test_kleinerer_rang_kommt_zuerst():
    geordnet = auf.nach_rang([{"auftrag_id": "b", "rang": 9},
                              {"auftrag_id": "a", "rang": 2}])
    assert [x["auftrag_id"] for x in geordnet] == ["a", "b"]


def test_ohne_rang_kommt_nach_allen_mit_rang():
    geordnet = auf.nach_rang([{"auftrag_id": "a"},
                              {"auftrag_id": "z", "rang": 4}])
    assert [x["auftrag_id"] for x in geordnet] == ["z", "a"], (
        "Ein Auftrag ohne Rang darf einen gesetzten nicht ueberholen, nur weil sein "
        "Dateiname frueher kommt.")


def test_bei_gleichem_rang_entscheidet_die_kennung():
    """Sonst haenge die Reihenfolge an der Reihenfolge des Einlesens — und die ist keine."""
    geordnet = auf.nach_rang([{"auftrag_id": "b", "rang": 1},
                              {"auftrag_id": "a", "rang": 1}])
    assert [x["auftrag_id"] for x in geordnet] == ["a", "b"]


# ======================================================================================
# Ein Feldname, zwei Bedeutungen
# ======================================================================================
#
# `auflagen` ist in den älteren Aufträgen das Wörterbuch, das der Runner liest, und in den
# neueren eine Liste von Sätzen für einen Menschen. `rueckgabe` ist einmal die
# Transportangabe und einmal die Liste der Fragen. Bis zum 01.09.2026 prüfte nichts, welche
# Form vorliegt — mit zwei Folgen, die beide teuer waren.

def test_die_maschinenauflagen_kommen_aus_dem_woerterbuch():
    satz = auf.baue_auftrag(auftrag_id="auf-a", art="multipass", beschreibung="x")
    assert auf.auflagen_maschine(satz)["leistungsgrenze_w"] == auf.LEISTUNGSGRENZE_W


def test_eine_prosaliste_ergibt_leere_maschinenauflagen_statt_eines_absturzes():
    """**Der Fehler, gegen den es die Funktion gibt.** `darf_starten` ruft `.get`; an einer
    Liste gab das `AttributeError`, und zwar ausserhalb der Absicherung der Schleife."""
    satz = auf.baue_auftrag(auftrag_id="auf-a", art="multipass", beschreibung="x")
    satz["auflagen"] = ["Nichts am Vertrag aendern", "Regel 3"]
    assert auf.auflagen_maschine(satz) == {}


def test_die_prosaauflagen_verlieren_die_werte_des_woerterbuchs_nicht():
    """Über das Wörterbuch gezählt kamen die SCHLÜSSELNAMEN heraus — die Werte
    verschwanden lautlos in jedem Block, der hinausging."""
    satz = auf.baue_auftrag(auftrag_id="auf-a", art="multipass", beschreibung="x")
    text = " ".join(auf.auflagen_text(satz))
    assert "400" in text, "die Zahl, an der der Rechner haengt, fehlte im Block"
    assert "Netzteil" in text, "der Hinweis stand nur als Schluesselname da"


def test_hinweise_stehen_vor_den_schluesselwerten():
    satz = auf.baue_auftrag(auftrag_id="auf-a", art="multipass", beschreibung="x")
    satz["auflagen"]["hinweise"] = ["ZUERST DIES"]
    assert auf.auflagen_text(satz)[0] == "ZUERST DIES"


def test_die_transportangabe_ist_kein_rueckgabepunkt():
    """*Der Wächter, den eine Form zufriedenstellte.* Ein Wörterbuch mit `verzeichnis`,
    `nur_zahlen` und `hinweis` ist wahr — und nennt keinen einzigen Rückgabepunkt."""
    satz = auf.baue_auftrag(auftrag_id="auf-a", art="multipass", beschreibung="x")
    assert satz["rueckgabe"], "die Transportangabe ist vorhanden"
    assert auf.rueckgabepunkte(satz) == [], "und trotzdem sagt sie nicht, was zurueckkommt"


def test_eine_liste_von_fragen_sind_rueckgabepunkte():
    satz = auf.baue_auftrag(auftrag_id="auf-a", art="multipass", beschreibung="x")
    satz["rueckgabe"] = ["V1 welcher Weg?", "V2 und warum?"]
    assert auf.rueckgabepunkte(satz) == ["V1 welcher Weg?", "V2 und warum?"]


# ── Die Hardware-Auflagen als ausführbarer Vertrag ───────────────────────────────────

def test_ein_local_auftrag_ohne_leistungsgrenze_ist_ungueltig():
    """Die 400-W-Auflage steht seit dem ersten Tag in `CLAUDE.md` und war nie ausführbar —
    darum ist sie ab dem 26.08.2026 unbemerkt aus 15 von 17 offenen Aufträgen
    verschwunden, als `auflagen` zur Prosaliste wurde."""
    satz = auf.baue_auftrag(auftrag_id="auf-a", art="multipass", beschreibung="x")
    satz["auflagen"] = ["Nur Prosa"]
    assert any("leistungsgrenze_w" in m for m in auf.pruefe_auftrag(satz))


def test_ein_local_auftrag_ohne_leerlauf_gate_ist_ungueltig():
    satz = auf.baue_auftrag(auftrag_id="auf-a", art="multipass", beschreibung="x")
    del satz["auflagen"]["nur_bei_leerlauf"]
    assert any("nur_bei_leerlauf" in m for m in auf.pruefe_auftrag(satz))


@pytest.mark.parametrize("worker", [auf.WORKER_CLOUD, auf.WORKER_UI, auf.WORKER_KERN])
def test_von_den_anderen_wird_keine_leistungsgrenze_verlangt(worker):
    """**Die Gegenprobe, und sie ist keine Formsache.** Sie haben keine Karte. Eine
    Auflage, die den Leser nicht betrifft, wird überblättert — und mit ihr die nächste."""
    satz = auf.baue_auftrag(auftrag_id="auf-a", art="qa", beschreibung="x", worker=worker)
    satz["auflagen"] = ["An unserem Code ist nichts zu aendern"]
    assert auf.pruefe_auftrag(satz) == []


def test_ein_neuer_local_auftrag_ohne_auflagen_wird_gar_nicht_erst_geschrieben(tmp_path):
    satz = auf.baue_auftrag(auftrag_id="auf-a", art="multipass", beschreibung="x")
    satz["auflagen"] = ["Nur Prosa"]
    with pytest.raises(auf.AuftragError, match="leistungsgrenze_w"):
        auf.schreibe_auftrag(satz, tmp_path)


# ======================================================================================
# Ein unbekannter Status ist keine Antwort
# ======================================================================================
#
# Owner-Entscheid 02.09.2026. Gezählt am selben Morgen: Drei Ergebnisse trugen einen
# Status, den `baue_ergebnis` gar nicht schreibt — von Hand geschrieben, an der Prüfung
# vorbei: `teilweise` («Die übrigen Teile folgen»), `teilweise — gerettet aus einem
# abgebrochenen Lauf`, `erledigt`. Alle drei galten als beantwortet. Der erste sagt in
# seinem eigenen Text, dass er es nicht ist.

def test_ein_erfundener_status_beantwortet_nichts(tmp_path):
    _mit_ergebnis(tmp_path, "auf-a", auf.WORKER_LOCAL, status="ok")
    # ...und dann von Hand ueberschrieben, so wie es wirklich geschah:
    pfad = tmp_path / auf.VERZ_ERGEBNISSE / "auf-a.json"
    satz = json.loads(pfad.read_text(encoding="utf-8"))
    satz["status"] = "teilweise"
    pfad.write_text(json.dumps(satz), encoding="utf-8")

    assert auf.zustand("auf-a", tmp_path) == auf.ZUSTAND_GERECHNET
    assert [a["auftrag_id"] for a in auf.unerledigt(tmp_path)] == ["auf-a"]


def test_die_bekannten_status_bleiben_was_sie_waren(tmp_path):
    """Die Gegenprobe. Ohne sie wäre der Test darüber auch grün, wenn **jeder** Status
    als offen gälte — und dann wäre nie ein Auftrag beantwortet."""
    _mit_ergebnis(tmp_path, "auf-ok", auf.WORKER_LOCAL, status="ok")
    _mit_ergebnis(tmp_path, "auf-fehler", auf.WORKER_LOCAL, status="fehler")
    assert auf.zustand("auf-ok", tmp_path) == auf.ZUSTAND_BEANTWORTET
    assert auf.zustand("auf-fehler", tmp_path) == auf.ZUSTAND_GERECHNET


def test_ein_erfundener_status_wird_beim_bauen_gar_nicht_erst_angenommen():
    """Die Prüfung in `baue_ergebnis` und die Liste in `zustand` sind **dieselbe** Liste.
    Zwei Listen wären die doppelte Vorgabe, an der genau diese Ergebnisse entstanden."""
    with pytest.raises(auf.AuftragError, match="teilweise"):
        auf.baue_ergebnis(auftrag_id="auf-a", status="teilweise")


def test_die_fehlermeldung_sagt_was_ein_erfundener_status_bewirkt():
    """*Er schliesst den Auftrag nicht — er lässt ihn im Rückstand stehen.* Wer das
    vorher weiss, schreibt keinen."""
    with pytest.raises(auf.AuftragError, match="Rueckstand"):
        auf.baue_ergebnis(auftrag_id="auf-a", status="erledigt")


def test_erfundene_status_werden_benannt_und_nicht_nur_gezaehlt(tmp_path):
    """*«Offen» allein sagt nicht, dass jemand etwas mitteilen WOLLTE und dafür ein
    eigenes Wort erfunden hat.*"""
    _mit_ergebnis(tmp_path, "auf-a", auf.WORKER_LOCAL, status="ok")
    pfad = tmp_path / auf.VERZ_ERGEBNISSE / "auf-a.json"
    satz = json.loads(pfad.read_text(encoding="utf-8"))
    satz.update({"status": "teilweise", "art": "Die uebrigen Teile folgen."})
    pfad.write_text(json.dumps(satz), encoding="utf-8")

    funde = auf.ergebnisse_mit_unbekanntem_status(tmp_path)

    assert [f["auftrag_id"] for f in funde] == ["auf-a"]
    assert funde[0]["status"] == "teilweise"
    assert "uebrigen Teile" in funde[0]["art"]


def test_ein_sauberes_ergebnis_taucht_dort_nicht_auf(tmp_path):
    """Die Gegenprobe — sonst stünde die Meldung unter jedem Lauf und wäre eine
    Dauerwarnung."""
    _mit_ergebnis(tmp_path, "auf-a", auf.WORKER_LOCAL, status="ok")
    assert auf.ergebnisse_mit_unbekanntem_status(tmp_path) == []


def test_der_deckel_nennt_sich_selbst_eine_selbstbindung(tmp_path):
    """**Owner-Entscheid 02.09.2026.** Er wirkt nur in `schreibe_auftrag`; die HomeStation
    legt ihre Dateien selbst an und kommt daran vorbei. *Ein Deckel, der nur den bindet,
    der ihn eingeführt hat, bremst niemanden — er darf dann aber nicht so tun.*"""
    for i in range(auf.DECKEL_JE_WORKER):
        _mit_ergebnis(tmp_path, f"auf-{i:02d}", auf.WORKER_LOCAL)
    with pytest.raises(auf.DeckelError, match="Selbstbindung"):
        auf.schreibe_auftrag(
            auf.baue_auftrag(auftrag_id="auf-zuviel", art="qa", beschreibung="x"),
            tmp_path)


def test_eine_von_hand_abgelegte_datei_faellt_nicht_unter_den_deckel(tmp_path):
    """Die Gegenprobe, und sie hält den Entscheid fest: Der Weg an `schreibe_auftrag`
    vorbei bleibt offen — er ist nicht vergessen worden, er ist gewollt."""
    ordner = tmp_path / auf.VERZ_OFFEN
    ordner.mkdir(parents=True)
    (tmp_path / auf.VERZ_ERGEBNISSE).mkdir(parents=True)
    # ALLE von Hand abgelegt — so, wie die HomeStation es tut. Ueber `schreibe_auftrag`
    # waere schon die Vorbereitung am Deckel gescheitert, und genau das ist der Punkt.
    for i in range(auf.DECKEL_JE_WORKER + 3):
        satz = auf.baue_auftrag(auftrag_id=f"auf-{i:02d}", art="qa", beschreibung="x")
        (ordner / f"auf-{i:02d}.json").write_text(json.dumps(satz), encoding="utf-8")

    offen = {a["auftrag_id"] for a in auf.unerledigt(tmp_path)}

    assert len(offen) == auf.DECKEL_JE_WORKER + 3, (
        "Elf Auftraege liegen da, obwohl der Deckel bei acht steht — der Weg an "
        "schreibe_auftrag vorbei ist nicht vergessen worden, er ist gewollt.")
