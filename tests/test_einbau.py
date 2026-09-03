"""``aiimaging.einbau`` — das Instrument, mit dem die Einbau-Verantwortung führbar wird.

Warum es dieses Modul und diese Tests gibt
-------------------------------------------
Owner-Auftrag vom 26.08.2026: *«Sorge dafür, dass andere Worker immer alles einbauen in
die Software — das ist Endziel. Du verteilst, wo was hin muss, und du bist verantwortlich,
dass sie es einbauen und mir dann bestätigst.»*

Verantwortung für etwas, das **anderswo** geschieht, lässt sich nur führen, wenn der
Rückstand zählbar ist. Am selben Abend lagen siebzehn Aufträge unbeantwortet, und diese
Zahl entstand, indem jemand zwei Verzeichnisse von Hand verglich. *Was von Hand gezählt
wird, wird irgendwann nicht mehr gezählt.*

Zwei Befunde über die erste Fassung stehen hier als Tests, weil sie beide vom Instrument
selbst handeln und beide unbemerkt geblieben wären:

* **Der Wächter hatte ein festes Alphabet.** ``[AB]\\d+`` — als ein Weg C dazukam, waren
  sechs Posten unbewacht und nichts wurde rot.
* **Der Melder suchte nach dem Fehlen eines Wortes.** Er hat sich an der eigenen Erklärung
  verschluckt: Kaum stand in einer Zeile *«stand bis heute als niemand da»*, galt der
  Posten wieder als unbesetzt. Ein Adressat wird jetzt **positiv** belegt.
"""
from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from aiimaging import auftrag as auf
from aiimaging import einbau

BLATT = """
| # | Posten | Zustand | Seit | Beleg |
|---|---|---|---|---|
| A1 | Etwas Fertiges | 🟩 **erledigt** | 2026-08-19 | **belegt im Repo:** `pyproject.toml` |
| A2 | Etwas Offenes | 🟥 **offen** | — | `auftraege/offen/auf-20260826-99.json` |
| B1 | Etwas Halbes | 🟩 **halb** | 2026-08-23 | `auf-20260826-98` und Prosa |
| C1 | Etwas Gebautes | 🟩 **gebaut, am Gerät unbestätigt** | 2026-08-26 | `auf-20260826-97` |
| C2 | Etwas Verwaistes | 🟥 **offen** | — | **niemand** — bisher nicht verteilt |
"""


def test_jede_tabellenzeile_wird_gelesen_egal_welcher_buchstabe():
    """**Der Befund über den Wächter selbst.**

    Sein Ausdruck stand als ``[AB]\\\\d+`` da. Ein Weg C kam dazu, und sechs Posten waren
    unbewacht — ohne dass ein einziger Test rot wurde. Ein Wächter mit fest eingebautem
    Alphabet hört auf zu wachen, sobald ein neuer Buchstabe auftaucht.
    """
    kennungen = [p["kennung"] for p in einbau.posten(BLATT)]

    assert kennungen == ["A1", "A2", "B1", "C1", "C2"]
    assert "C1" in kennungen, "der Buchstabe darf nicht fest eingebaut sein"


def test_ein_leeres_blatt_ist_ein_fehler_und_kein_leerer_stand():
    """«Nichts gelesen» und «nichts offen» sehen sonst gleich aus — und die zweite Lesart
    ist die gefährlichere."""
    with pytest.raises(einbau.EinbauError, match="Kein einziger Posten"):
        einbau.posten("# Ein Blatt ganz ohne Tabelle\n")


def test_gebaut_aber_unbestaetigt_gilt_als_noch_nicht_eingebaut():
    """Die dritte Antwort, auf den Einbau angewandt.

    Was bei uns fertig ist und drüben ungeprüft, ist weder erledigt noch offen. Es als
    erledigt zu führen wäre genau der Selbstbetrug, gegen den der Owner-Auftrag steht:
    Gebaut ist eine Zwischenstufe, kein Ergebnis.
    """
    offen = {p["kennung"] for p in einbau.posten(BLATT) if p["offen"]}

    assert offen == {"A2", "B1", "C1", "C2"}
    assert "A1" not in offen
    assert "gebaut, am gerät unbestätigt" in einbau.OFFENE_ZUSTAENDE
    assert "erledigt" not in einbau.OFFENE_ZUSTAENDE


def test_der_adressat_wird_positiv_belegt_und_nicht_aus_der_prosa_erschlossen():
    """**Die Berichtigung vom selben Abend.**

    Die erste Fassung suchte nach dem Wort «niemand». Sie hat sich an der eigenen
    Erklärung verschluckt: Sobald eine Zeile den Satz *«stand bis heute als niemand da»*
    trug, galt der Posten wieder als unbesetzt — obwohl er längst einen Auftrag hatte.

    *Eine Prüfung auf die Abwesenheit eines Wortes prüft die Prosa, nicht die Sache.*
    """
    verwaist = [p["kennung"] for p in einbau.ohne_adressat(BLATT)]

    assert verwaist == ["C2"], "nur die Zeile ohne Auftragskennung"

    mit_wort = BLATT.replace("| C1 | Etwas Gebautes | 🟩 **gebaut, am Gerät unbestätigt** "
                             "| 2026-08-26 | `auf-20260826-97` |",
                             "| C1 | Etwas Gebautes | 🟩 **gebaut, am Gerät unbestätigt** "
                             "| 2026-08-26 | `auf-20260826-97`, stand früher als «niemand» da |")
    assert [p["kennung"] for p in einbau.ohne_adressat(mit_wort)] == ["C2"], (
        "das Wort in der Erklärung darf den Adressaten nicht wegnehmen"
    )


def test_ein_erledigter_posten_ohne_auftrag_ist_kein_rueckstand():
    """Die Gegenprobe. Erledigt heisst erledigt — dort treibt zu Recht niemand mehr etwas.

    Ohne sie prüfte der Test darüber nur, dass irgendetwas gefunden wird, und nicht, dass
    die **richtige** Menge gefunden wird.
    """
    nur_erledigt = ("| # | P | Z | S | B |\n|---|---|---|---|---|\n"
                    "| A1 | Fertig | 🟩 **erledigt** | 2026-08-19 | `pyproject.toml` |\n")

    assert einbau.posten(nur_erledigt)[0]["offen"] is False
    assert einbau.ohne_adressat(nur_erledigt) == []


# ── Der Rückstand ────────────────────────────────────────────────────────────────────

def _lege_ab(wurzel, kennung: str, worker: str, erstellt: str) -> None:
    satz = auf.baue_auftrag(auftrag_id=kennung, art="qa", worker=worker,
                            beschreibung="Eine Frage", anweisung="Bitte messen.")
    satz["erstellt"] = erstellt
    auf.schreibe_auftrag(satz, wurzel)


def test_der_rueckstand_trennt_nach_worker(tmp_path):
    """**Warum getrennt und nicht als Gesamtzahl.**

    Die drei Worker können nicht dasselbe, und ein Rückstand verlangt je nach Adressat
    einen anderen Handgriff: bei der HomeStation «läuft der Dienst?», beim Cloud-Worker
    «liegt eine Vertragsfrage quer?», beim UI-Worker «hat er unser Repo gezogen?». Eine
    Gesamtzahl verwischt das.
    """
    _lege_ab(tmp_path, "auf-20260820-01", auf.WORKER_LOCAL, "2026-08-20T10:00:00Z")
    _lege_ab(tmp_path, "auf-20260825-02", auf.WORKER_CLOUD, "2026-08-25T10:00:00Z")
    _lege_ab(tmp_path, "auf-20260826-03", auf.WORKER_UI, "2026-08-26T10:00:00Z")

    stand = einbau.rueckstand(tmp_path, heute=date(2026, 8, 26))

    assert stand["n"] == 3
    assert stand["je_worker"] == {"local": 1, "cloud": 1, "ui": 1, "kern": 0}, (
        "seit dem 28.08.2026 gibt es einen vierten Empfaenger — diese Sitzung selbst")
    assert stand["aelteste_tage"] == 6
    assert [e["auftrag_id"] for e in stand["eintraege"]][0] == "auf-20260820-01", (
        "der älteste zuerst — er ist der, der am ehesten vergessen wurde"
    )


def test_ein_beantworteter_auftrag_zaehlt_nicht_mehr(tmp_path):
    """Die Gegenprobe zum Rückstand. Sonst zählte er Aufträge und nicht Rückstand.

    **Bis zum 28.08.2026 stand hier das Gegenteil**, und dieser Docstring sagte:
    *«Beantwortet heisst beantwortet, nicht gut beantwortet. Ein Ergebnis mit
    ``status: fehler`` ist eine Antwort.»* Der Test schrieb ``fehler`` und erwartete, dass
    der Rückstand auf null fällt.

    **Die Messung vom Gerät hat das widerlegt** (`auf-20260828-64`): Von zwei
    ``cloud``-Aufträgen mit Ergebnis waren **zwei von zwei** Weiterleitungsvermerke, ein
    weiteres trug ``status: erledigt`` mit leeren Messwerten. Nach der alten Regel galten
    acht Aufträge als erledigt, die niemand beantwortet hat.

    *Ein Ergebnis zu haben heisst nicht, beantwortet zu sein.* Owner-Entscheid vom
    28.08.2026: Der Zustand wird abgeleitet, mit fünf Werten — und nur ``ok`` beantwortet.
    """
    _lege_ab(tmp_path, "auf-20260826-04", auf.WORKER_LOCAL, "2026-08-26T10:00:00Z")
    assert einbau.rueckstand(tmp_path, heute=date(2026, 8, 26))["n"] == 1

    auf.schreibe_ergebnis(
        auf.baue_ergebnis(auftrag_id="auf-20260826-04", status="fehler"), tmp_path)
    assert einbau.rueckstand(tmp_path, heute=date(2026, 8, 26))["n"] == 1, (
        "gerechnet und nicht beantwortet ist kein erledigter Posten")
    assert auf.zustand("auf-20260826-04", tmp_path) == auf.ZUSTAND_GERECHNET

    auf.schreibe_ergebnis(
        auf.baue_ergebnis(auftrag_id="auf-20260826-04", status="ok"), tmp_path)
    assert einbau.rueckstand(tmp_path, heute=date(2026, 8, 26))["n"] == 0
    assert auf.zustand("auf-20260826-04", tmp_path) == auf.ZUSTAND_BEANTWORTET


def test_der_rueckstand_traegt_keine_pfade(tmp_path):
    """Regel 3. Der Stand reist in eine Bestätigung an den Owner — und ein Pfad aus dieser
    Umgebung trüge einen Benutzernamen mit."""
    _lege_ab(tmp_path, "auf-20260826-05", auf.WORKER_LOCAL, "2026-08-26T10:00:00Z")

    eintrag = einbau.rueckstand(tmp_path, heute=date(2026, 8, 26))["eintraege"][0]

    assert set(eintrag) == {"auftrag_id", "worker", "art", "tage", "beschreibung"}
    assert not [w for w in eintrag.values() if isinstance(w, str) and "/" in w]


def test_der_bericht_ist_erst_bereit_wenn_jeder_posten_einen_adressaten_hat(tmp_path):
    """``bereit`` sagt **nicht**, dass alles eingebaut ist.

    Es sagt, dass für alles, was fehlt, jemand benannt ist — der Teil, für den ich hafte.
    Der Einbau selbst geschieht drüben, und ihn hier als erledigt zu führen wäre dieselbe
    Verwechslung, gegen die der ganze Auftrag steht.
    """
    blatt = tmp_path / "stand.md"
    blatt.write_text(BLATT, encoding="utf-8")
    assert einbau.bericht(tmp_path, blatt)["bereit"] is False

    blatt.write_text(BLATT.replace("**niemand** — bisher nicht verteilt",
                                   "`auf-20260826-96`"), encoding="utf-8")
    bericht = einbau.bericht(tmp_path, blatt)

    assert bericht["bereit"] is True
    assert len(bericht["offene_posten"]) == 4, (
        "vier Posten fehlen weiterhin in der Software — bereit heisst NICHT eingebaut"
    )

    # Und seit dem 27.08.2026 haengt `bereit` an einer ZWEITEN Bedingung: Nimmt man der
    # erledigten Zeile die Angabe, worauf ihr Beleg ruht, ist der Bericht wieder nicht
    # bereit — obwohl jeder offene Posten seinen Adressaten behalten hat.
    blatt.write_text(BLATT.replace("**niemand** — bisher nicht verteilt",
                                   "`auf-20260826-96`")
                          .replace("**belegt im Repo:** `pyproject.toml`",
                                   "`pyproject.toml`"), encoding="utf-8")
    ohne = einbau.bericht(tmp_path, blatt)
    assert ohne["bereit"] is False
    assert ohne["ohne_adressat"] == []


# ======================================================================================
# Worauf ein Beleg ruht — der Wächter, der am 27.08.2026 gefehlt hat
# ======================================================================================

BLATT_KOPF = "| # | Posten | Zustand | Seit | Beleg |\n|---|---|---|---|---|\n"


def _blatt(*zeilen: str) -> str:
    return BLATT_KOPF + "".join(z + "\n" for z in zeilen)


def test_erledigt_ohne_angabe_wird_gemeldet(tmp_path):
    """**Der Fall B8.** Sechs Tage erledigt, während drüben eine ältere Fassung lief."""
    blatt = _blatt("| B8 | Ein bestellter Render wird ausgefuehrt | 🟩 **erledigt** | "
                   "2026-08-26 | `tools/abholen.py` |")
    maengel = einbau.ohne_geraetebeweis(blatt, tmp_path)
    assert [m["kennung"] for m in maengel] == ["B8"]
    assert maengel[0]["mangel"] == "keine angabe"
    assert "nicht was auf dem Gerät läuft" in maengel[0]["grund"]


def test_belegt_im_repo_genuegt_fuer_eine_reine_repo_aussage(tmp_path):
    blatt = _blatt("| A1 | `mcp<2` festschreiben | 🟩 **erledigt** | 2026-08-19 | "
                   "**belegt im Repo:** `pyproject.toml` |")
    assert einbau.ohne_geraetebeweis(blatt, tmp_path) == []


def test_belegt_im_repo_genuegt_NICHT_wenn_ein_schalter_darin_steht(tmp_path):
    """**Die B8-Falle wörtlich.** Der Schalter war im Repo und auf dem Gerät nicht."""
    blatt = _blatt("| B8 | Ein bestellter Render wird ausgefuehrt | 🟩 **erledigt** | "
                   "2026-08-26 | **belegt im Repo:** `tools/abholen.py --eigener-store` |")
    maengel = einbau.ohne_geraetebeweis(blatt, tmp_path)
    assert [m["mangel"] for m in maengel] == ["repo trotz gerätezeichen"]


def test_belegt_im_repo_genuegt_NICHT_bei_einer_diensteinheit(tmp_path):
    blatt = _blatt("| C1 | Der Abholer laeuft als Dienst | 🟩 **erledigt** | 2026-08-22 | "
                   "**belegt im Repo:** `betrieb/kosmo-abholer.service` |")
    assert [m["mangel"] for m in einbau.ohne_geraetebeweis(blatt, tmp_path)] == [
        "repo trotz gerätezeichen"]


def test_belegt_am_geraet_braucht_einen_BEANTWORTETEN_auftrag(tmp_path):
    """Ein Auftrag, der noch offen liegt, ist keine Rückmeldung von dort."""
    blatt = _blatt("| C1 | Der Abholer laeuft als Dienst | 🟩 **erledigt** | 2026-08-22 | "
                   "**belegt am Gerät:** `auf-20260822-31` |")
    maengel = einbau.ohne_geraetebeweis(blatt, tmp_path)
    assert [m["mangel"] for m in maengel] == ["gerät ohne antwort"]

    _lege_ab(tmp_path, "auf-20260822-31", auf.WORKER_LOCAL, "2026-08-22T10:00:00Z")
    auf.schreibe_ergebnis(
        auf.baue_ergebnis(auftrag_id="auf-20260822-31", status="ok"), tmp_path)
    assert einbau.ohne_geraetebeweis(blatt, tmp_path) == []


def test_belegt_am_geraet_geht_auch_mit_einer_uhrzeit(tmp_path):
    """Die schwächere der beiden Arten — und die einzige, die eine Messung ohne
    Ergebnisdatei überhaupt buchbar macht."""
    blatt = _blatt("| B8 | Ein bestellter Render wird ausgefuehrt | 🟩 **erledigt** | "
                   "2026-08-27 | **belegt am Gerät:** Messung 27.08.2026, 18:54:11 "
                   "aufgegriffen |")
    assert einbau.ohne_geraetebeweis(blatt, tmp_path) == []


def test_eine_uhrzeit_allein_genuegt_nicht_ohne_die_angabe(tmp_path):
    """Sonst würde jede Zeile mit einem Zeitstempel durchrutschen."""
    blatt = _blatt("| B8 | Ein bestellter Render wird ausgefuehrt | 🟩 **erledigt** | "
                   "2026-08-27 | Messung 18:54:11, `tools/abholen.py` |")
    assert [m["mangel"] for m in einbau.ohne_geraetebeweis(blatt, tmp_path)] == [
        "keine angabe"]


def test_offene_posten_muessen_gar_nichts_belegen(tmp_path):
    """Die Prüfung gilt nur für *erledigt*. Ein offener Posten behauptet nichts."""
    blatt = _blatt("| C9 | Die Paarschwellen sind kalibriert | 🟥 **offen** | — | "
                   "`auf-20260827-61.json`, `tools/abholen.py --eigener-store` |",
                   "| C7 | Der Homeworker hat einen Takt | 🟩 **gebaut, am Gerät "
                   "unbestätigt** | 2026-08-26 | `betrieb/kosmo-worker.service` |")
    assert einbau.ohne_geraetebeweis(blatt, tmp_path) == []


def test_beantwortete_auftraege_zaehlt_die_antwort_und_nicht_den_auftrag(tmp_path):
    _lege_ab(tmp_path, "auf-20260827-99", auf.WORKER_LOCAL, "2026-08-27T10:00:00Z")
    assert einbau.beantwortete_auftraege(tmp_path) == set()

    auf.schreibe_ergebnis(
        auf.baue_ergebnis(auftrag_id="auf-20260827-99", status="ok"), tmp_path)
    assert einbau.beantwortete_auftraege(tmp_path) == {"auf-20260827-99"}


def test_ohne_ergebnisordner_faellt_nichts_um(tmp_path):
    assert einbau.beantwortete_auftraege(tmp_path) == set()


def test_bereit_ist_falsch_sobald_ein_beleg_nicht_sagt_worauf_er_ruht(tmp_path):
    """Der Rückgabewert des Werkzeugs hängt daran — er soll ein Skript scheitern lassen."""
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "EINBAU_STAND.md").write_text(_blatt(
        "| B8 | Ein bestellter Render wird ausgefuehrt | 🟩 **erledigt** | 2026-08-26 | "
        "`tools/abholen.py` |"), encoding="utf-8")
    satz = einbau.bericht(tmp_path)
    assert satz["bereit"] is False
    assert satz["ohne_adressat"] == [], "der Mangel liegt NICHT beim Adressaten"
    assert len(satz["ohne_geraetebeweis"]) == 1


def test_ein_weiterleitungsvermerk_gilt_nicht_als_beantwortet(tmp_path):
    """**Derselbe Fehler eine Ebene tiefer** (28.08.2026).

    `beantwortete_auftraege` zählte die **Datei** und nicht ihren Inhalt — genau der
    Fehler, gegen den sie gebaut wurde. Aufgefallen ist er, als der abgeleitete Zustand
    dazukam: `auf-20260822-31` trägt `status: ok` und
    `art: weitergereicht_und_teilbeantwortet`, galt als Antwort und war ein
    Weiterleitungsvermerk — **und zwei erledigte Posten des Einbau-Stands beriefen sich
    darauf.**

    *Eine Datei im Ergebnisordner belegt, dass jemand geantwortet hat — nicht, dass er die
    Frage beantwortet hat.*
    """
    _lege_ab(tmp_path, "auf-20260826-07", auf.WORKER_LOCAL, "2026-08-26T10:00:00Z")

    satz = auf.baue_ergebnis(auftrag_id="auf-20260826-07", status="ok")
    satz["art"] = "weitergereicht_und_teilbeantwortet"
    auf.schreibe_ergebnis(satz, tmp_path)
    assert einbau.beantwortete_auftraege(tmp_path) == set(), (
        "eine Ergebnisdatei allein ist keine Antwort")

    auf.schreibe_ergebnis(
        auf.baue_ergebnis(auftrag_id="auf-20260826-07", status="ok"), tmp_path)
    assert einbau.beantwortete_auftraege(tmp_path) == {"auf-20260826-07"}


def test_ein_gerechneter_aber_unbeantworteter_auftrag_belegt_nichts(tmp_path):
    _lege_ab(tmp_path, "auf-20260826-08", auf.WORKER_LOCAL, "2026-08-26T10:00:00Z")
    auf.schreibe_ergebnis(
        auf.baue_ergebnis(auftrag_id="auf-20260826-08", status="fehler"), tmp_path)
    assert einbau.beantwortete_auftraege(tmp_path) == set()


# ======================================================================================
# Die Zeile, die neben dem Rückstand fehlte
# ======================================================================================

def test_der_bericht_traegt_das_antwortverhalten_je_adressat(tmp_path):
    """*Ein Rückstand sagt, wie viel bei jemandem liegt. Er sagt nicht, ob dort überhaupt
    jemand ist.* Beide Lagen sahen bis zum 01.09.2026 gleich aus."""
    auf.schreibe_auftrag(
        auf.baue_auftrag(auftrag_id="auf-a", art="qa", beschreibung="x",
                              worker=auf.WORKER_UI), tmp_path)
    satz = einbau.bericht(tmp_path, BLATT)
    assert satz["antwortverhalten"][auf.WORKER_UI]["n_antworten"] == 0


def test_die_ausgabe_nennt_einen_stummen_adressaten_beim_namen(tmp_path, capsys):
    """Die Zahl allein liest sich wie jeder andere Rückstand. Der Zusatz ist der Befund."""
    auf.schreibe_auftrag(
        auf.baue_auftrag(auftrag_id="auf-a", art="qa", beschreibung="x",
                              worker=auf.WORKER_UI), tmp_path)
    _mit_blatt(tmp_path)
    _einbau_cli().main(["--repo", str(tmp_path)])
    ausgabe = capsys.readouterr().out
    assert "NIE GEANTWORTET" in ausgabe


def test_ein_adressat_mit_antwort_wird_nicht_als_stumm_gemeldet(tmp_path, capsys):
    """Die Gegenprobe. Ohne sie stünde der Satz bei jedem — eine Dauerwarnung."""
    auf.schreibe_auftrag(
        auf.baue_auftrag(auftrag_id="auf-a", art="qa", beschreibung="x",
                              worker=auf.WORKER_LOCAL), tmp_path)
    auf.schreibe_auftrag(
        auf.baue_auftrag(auftrag_id="auf-b", art="qa", beschreibung="x",
                              worker=auf.WORKER_LOCAL), tmp_path)
    auf.schreibe_ergebnis(
        auf.baue_ergebnis(auftrag_id="auf-b", status="ok"), tmp_path)
    _mit_blatt(tmp_path)
    _einbau_cli().main(["--repo", str(tmp_path)])
    assert "NIE GEANTWORTET" not in capsys.readouterr().out


# ---------------------------------------------------------------------------------
# NICHT AUSGELIEFERT — ein Rueckstand beim ABSENDER (03.09.2026)
# ---------------------------------------------------------------------------------


def test_der_bericht_meldet_auftraege_die_nie_hinausgegangen_sind(tmp_path, capsys):
    """**Der Befund vom 03.09.2026.** Zwei `ui`-Auftraege lagen zwei bzw. einen Tag im
    Repo und waren nirgends sonst. In dieser Liste sahen sie aus wie jeder andere
    Rueckstand — und waren keiner beim Adressaten, sondern einer bei uns."""
    auf.schreibe_auftrag(
        auf.baue_auftrag(auftrag_id="auf-c", art="frage", beschreibung="x",
                         worker=auf.WORKER_UI), tmp_path)
    _mit_blatt(tmp_path)
    _einbau_cli().main(["--repo", str(tmp_path)])
    ausgabe = capsys.readouterr().out
    assert "NICHT AUSGELIEFERT" in ausgabe
    assert "auf-c" in ausgabe
    assert "auftragspost.py" in ausgabe, (
        "Eine Meldung ohne Abhilfe verschiebt das Nachsehen auf den naechsten.")


def test_ein_ausgelieferter_auftrag_steht_nicht_in_dieser_meldung(tmp_path, capsys):
    """Die Gegenprobe — sonst stuende die Zeile immer da und waere nach drei Tagen
    unsichtbar, wie jede Dauerwarnung."""
    from aiimaging import auftragspost
    auf.schreibe_auftrag(
        auf.baue_auftrag(auftrag_id="auf-c", art="frage", beschreibung="x",
                         worker=auf.WORKER_UI), tmp_path)
    auftragspost.vermerke_zustellung(["auf-c"], tmp_path)
    _mit_blatt(tmp_path)
    _einbau_cli().main(["--repo", str(tmp_path)])
    assert "NICHT AUSGELIEFERT" not in capsys.readouterr().out


def _einbau_cli():
    import importlib.util
    pfad = Path(__file__).resolve().parents[1] / "tools" / "einbau.py"
    spec = importlib.util.spec_from_file_location("werkzeug_einbau", pfad)
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul


def _mit_blatt(wurzel):
    """Der Einstieg liest `docs/EINBAU_STAND.md` — ohne Blatt gibt es keinen Bericht."""
    ordner = Path(wurzel) / "docs"
    ordner.mkdir(parents=True, exist_ok=True)
    (ordner / "EINBAU_STAND.md").write_text(BLATT, encoding="utf-8")
