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

import pytest

from aiimaging import auftrag as auf
from aiimaging import einbau

BLATT = """
| # | Posten | Zustand | Seit | Beleg |
|---|---|---|---|---|
| A1 | Etwas Fertiges | 🟩 **erledigt** | 2026-08-19 | `pyproject.toml` |
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
    assert stand["je_worker"] == {"local": 1, "cloud": 1, "ui": 1}
    assert stand["aelteste_tage"] == 6
    assert [e["auftrag_id"] for e in stand["eintraege"]][0] == "auf-20260820-01", (
        "der älteste zuerst — er ist der, der am ehesten vergessen wurde"
    )


def test_ein_beantworteter_auftrag_zaehlt_nicht_mehr(tmp_path):
    """Die Gegenprobe zum Rückstand. Sonst zählte er Aufträge und nicht Rückstand.

    **Beantwortet heisst beantwortet, nicht gut beantwortet.** Ein Ergebnis mit
    ``status: fehler`` ist eine Antwort — die Frage ist gestellt und beschieden. Ob sie
    taugt, steht in den Befunden und nicht in dieser Zählung.
    """
    _lege_ab(tmp_path, "auf-20260826-04", auf.WORKER_LOCAL, "2026-08-26T10:00:00Z")
    assert einbau.rueckstand(tmp_path, heute=date(2026, 8, 26))["n"] == 1

    auf.schreibe_ergebnis(
        auf.baue_ergebnis(auftrag_id="auf-20260826-04", status="fehler"), tmp_path)

    assert einbau.rueckstand(tmp_path, heute=date(2026, 8, 26))["n"] == 0


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
