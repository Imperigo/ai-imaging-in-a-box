"""``docs/OBERFLAECHE_KOSMOVIS.md`` — kein Bedienelement ohne Wirkung.

Die Regel, die dieser Wächter durchsetzt
----------------------------------------
Die Hausregel sagt: *Was nur über einen Klick erreichbar ist, existiert nicht.* Die
Umkehrung gilt genauso, und sie ist der Kern dieses Tests:

    **Ein Regler, dessen Wert an der Naht stehenbleibt, ist schlimmer als ein fehlender
    Regler — er behauptet eine Wirkung, und der Benutzer glaubt sie.**

Solche Felder gibt es heute: `vis.upscale` bewirkt nichts (es gibt keinen
Hochskalierer), `style.mode` und `style.refs` ebenso wenig (die Stil-QA läuft nicht).
Bei `style.refs` steckt der Benutzer sogar eigene Dateien hinein — Arbeit, die verfällt.
Sie stehen benannt in :data:`aiimaging.kosmo_szene.STEHENGEBLIEBEN`.

Der Entwurf darf sie darum **nicht als Bedienelement führen**, sondern nur in der
zweiten Tabelle, die sie ausdrücklich als wirkungslos ausweist. Dieser Test hält den
Entwurf gegen die beiden Tabellen — nicht gegen sich selbst.

**Damit schliesst sich der Kreis zwischen den beiden Strängen dieses Tages:** Regel 1 des
Entwurfs ist keine Absichtserklärung mehr, sondern fällt rot, sobald jemand ein
Bedienelement für ein Feld entwirft, das an der Naht hängenbleibt.

Was hier NICHT geprüft wird: die Prosa, die Reihenfolge, die Formulierungen. Ein Wächter
auf Prosa fände einen Treffer auf fünf Fehlalarme.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from aiimaging import kosmo_szene

REPO = Path(__file__).resolve().parents[1]
BLATT = REPO / "docs" / "OBERFLAECHE_KOSMOVIS.md"

#: Die Überschriften, die die beiden Tabellen trennen. Die zweite ist die Liste der
#: ausdrücklich wirkungslosen Felder — sie DARF stehengebliebene Felder nennen, die
#: erste nicht.
UEBERSCHRIFT_ANBIETEN = "## 3 · Die Bedienelemente"
UEBERSCHRIFT_NICHT_ANBIETEN = "### Nicht anbieten"
UEBERSCHRIFT_DANACH = "## 4 · Was nach dem Lauf erscheint"

#: Eine Tabellenzeile.
ZEILE = re.compile(r"^\|(?!\s*-)(.+)\|\s*$")

#: Die Spalte, in der UNSERE Feldnamen stehen. Sie wird über die Kopfzeile gesucht und
#: nicht über eine Nummer: Eine Tabelle bekommt irgendwann eine Spalte dazu, und eine
#: Nummer im Test wäre dann still falsch.
SPALTE = "unser Feld"


def _abschnitt(von: str, bis: str) -> str:
    text = BLATT.read_text(encoding="utf-8")
    return text[text.index(von):text.index(bis)]


def _felder(abschnitt: str) -> set[str]:
    """Die Einträge der Spalte «unser Feld» eines Abschnitts.

    Nur diese eine Spalte. Ein loser Griff über die ganze Zeile fing beim ersten Anlauf
    auch Werte ein (`qwen`, `true`, `s`) und prüfte damit etwas anderes, als er behauptete.
    """
    gefunden: set[str] = set()
    kopf: list[str] | None = None
    for roh in abschnitt.splitlines():
        if roh.lstrip().startswith("|") and set(roh) <= set("|- :"):
            # Die Trennzeile unter dem Kopf. Sie ist keine Datenzeile — aber auch kein
            # Tabellenende, und sie hier NICHT zu ueberspringen hat den Kopf geloescht.
            continue
        treffer = ZEILE.match(roh)
        if not treffer:
            kopf = None
            continue
        zellen = [z.strip() for z in treffer.group(1).split("|")]
        if kopf is None:
            kopf = zellen
            continue
        if SPALTE not in kopf:
            continue
        zelle = zellen[kopf.index(SPALTE)]
        for wort in re.findall(r"`([^`]+)`", zelle):
            for teil in re.split(r"[,\s]+", wort.strip()):
                if teil:
                    gefunden.add(teil)
    return gefunden


ANGEBOTEN = _felder(_abschnitt(UEBERSCHRIFT_ANBIETEN, UEBERSCHRIFT_NICHT_ANBIETEN))
VERWEIGERT = _felder(_abschnitt(UEBERSCHRIFT_NICHT_ANBIETEN, UEBERSCHRIFT_DANACH))


def test_das_blatt_gibt_es_und_hat_beide_tabellen():
    assert BLATT.is_file()
    assert ANGEBOTEN, "Der Entwurf bietet kein einziges Bedienelement an."
    assert VERWEIGERT, (
        "Der Entwurf führt keine wirkungslosen Felder auf. Es gibt heute drei — "
        "sie zu verschweigen wäre die bequemste Art, Regel 1 zu erfüllen."
    )


@pytest.mark.parametrize("feld", sorted(ANGEBOTEN))
def test_jedes_angebotene_bedienelement_kommt_auch_an(feld):
    """**Regel 1.** Der Entwurf darf nichts anbieten, was an der Naht stehenbleibt."""
    assert feld not in kosmo_szene.STEHENGEBLIEBEN, (
        f"Der Entwurf bietet ein Bedienelement für {feld!r} an — das Feld steht in "
        f"STEHENGEBLIEBEN und bewirkt nichts:\n"
        f"  {kosmo_szene.STEHENGEBLIEBEN[feld]['grund']}\n"
        f"Ein Regler, dessen Wert an der Naht hängenbleibt, ist schlimmer als ein "
        f"fehlender — er behauptet eine Wirkung."
    )
    assert feld in kosmo_szene.DURCHGEREICHT, (
        f"{feld!r} steht in keiner der beiden Tabellen. Genau diese dritte Möglichkeit — "
        f"«steht nirgends» — ist die bequemste und die, gegen die die Tabellen gebaut "
        f"sind. Entweder kommt das Feld an, dann gehört es nach DURCHGEREICHT; oder es "
        f"bleibt stehen, dann nach STEHENGEBLIEBEN und in die zweite Tabelle."
    )


@pytest.mark.parametrize("feld", sorted(VERWEIGERT))
def test_die_zweite_tabelle_fuehrt_nur_wirklich_wirkungslose_felder(feld):
    """Sonst stünde ein Feld als wirkungslos da, das längst wirkt — und niemand böte es an."""
    assert feld in kosmo_szene.STEHENGEBLIEBEN, (
        f"{feld!r} wird als wirkungslos geführt, steht aber nicht in STEHENGEBLIEBEN. "
        f"Wirkt es inzwischen, gehört es in die erste Tabelle — sonst verzichtet die "
        f"Oberfläche auf etwas, das es gibt."
    )


def test_jedes_stehengebliebene_feld_wird_im_entwurf_ueberhaupt_erwaehnt():
    """Von der anderen Seite gezählt.

    Der Entwurf kann kein Feld vermissen, nach dem er nicht fragt. Also wird nicht der
    Entwurf abgefragt, sondern die Tabelle — und der Entwurf muss ihr standhalten.
    """
    fehlend = sorted(set(kosmo_szene.STEHENGEBLIEBEN) - VERWEIGERT)
    assert not fehlend, (
        f"Diese Felder bewirken nichts und kommen im Entwurf nicht vor: "
        f"{', '.join(fehlend)}. Eine Oberfläche, die sie stillschweigend weglässt, ist "
        f"zwar nicht falsch — aber niemand erfährt, dass sie fehlen und warum."
    )


def test_der_entwurf_nennt_zu_jedem_wirkungslosen_feld_was_fehlt():
    """«Wird nicht unterstützt» ohne den nächsten Schritt ist eine Sackgasse."""
    abschnitt = _abschnitt(UEBERSCHRIFT_NICHT_ANBIETEN, UEBERSCHRIFT_DANACH)
    for feld, eintrag in kosmo_szene.STEHENGEBLIEBEN.items():
        assert eintrag["noetig"], f"STEHENGEBLIEBEN[{feld!r}] sagt nicht, was fehlt."
    assert "was fehlt" in abschnitt.lower() or "fehlt" in abschnitt.lower(), (
        "Die zweite Tabelle sagt nicht, was jeweils fehlen würde. Mit dem nächsten "
        "Schritt ist es eine Aufgabe, ohne ihn eine Sackgasse."
    )


def test_die_dritte_antwort_steht_im_entwurf():
    """*Nicht messbar ist weder bestanden noch durchgefallen* — der Satz dieses Projekts.

    Eine Oberfläche mit zwei Zuständen rundet die dritte Lage weg, und dann sieht ein
    Lauf, der nichts messen konnte, aus wie ein durchgefallener.
    """
    text = BLATT.read_text(encoding="utf-8")
    assert "nicht gemessen" in text.lower()
    assert "ungeprüft" in text.lower()


def test_der_entwurf_traegt_die_vorbehalte_der_selbstauskunft():
    """Regel 3: Eine Zahl gehört an die Bedingung, unter der sie gemessen wurde.

    Die Vorbehalte werden von `aiimaging_capabilities` bereits mitgeliefert. Der Entwurf
    muss sie an die Zahl stellen, sonst liest sie weiterhin niemand.
    """
    text = BLATT.read_text(encoding="utf-8").lower()
    assert "nicht kalibriert" in text, (
        "Der Entwurf verschweigt, dass die Geometrie-Schwelle nicht kalibriert ist. "
        "Ein grünes Abzeichen auf einer unkalibrierten Schwelle ist schlimmer als gar "
        "keines."
    )
    assert "startwert" in text and "streuung" in text, (
        "Der Entwurf nennt die Startwert-Streuung nicht. Sie ist grösser als jeder "
        "bisher gemessene Parametereffekt — ohne diesen Hinweis vergleicht die "
        "Oberfläche Äpfel mit Birnen."
    )
