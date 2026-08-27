"""``docs/EINBAU_STAND.md`` — die Landkarte des Einbaus, gegen die Wirklichkeit gehalten.

Warum es diesen Wächter gibt
----------------------------
``docs/COCKPIT_BESTAND_2026-08-19.md`` §4 hat den Weg in KosmoOrbit vollständig
aufgelistet — und danach hat niemand Buch geführt. Sieben Tage später waren vier Posten
still erledigt und mehrere still noch offen; welche, konnte niemand sagen. ``README.md``
trug in derselben Zeit den entgegengesetzten Fehler und meldete eine Registrierung als
«nicht ausgeführt», die längst gelaufen war.

**Eine Aufstellung, die stimmte, als sie geschrieben wurde**, ist die geduldigste Form
der toten Kante: Sie fällt nie auf, und wenn eines Tages jemand hinsieht, steht seit
Wochen Unsinn darin.

Dieser Wächter prüft darum genau zwei Dinge — und **keine Prosa**:

* Ein Posten, der als erledigt geführt wird, nennt einen **Beleg, den es gibt**.
  Ein Beleg, der auf eine gelöschte Datei zeigt, ist schlimmer als keiner.
* Ein Posten, der als offen geführt wird, nennt einen **Auftrag, der offen liegt** —
  oder ausdrücklich **niemand**. Damit kann kein Posten still verwaisen.

Was hier NICHT geprüft wird: ob ein Posten gut gelöst ist, ob die Beschreibung stimmt,
ob die Reihenfolge sinnvoll ist. Ein Wächter auf Prosa fände einen Treffer auf fünf
Fehlalarme — das ist am 26.08.2026 einmal ausprobiert und verworfen worden.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from aiimaging import einbau

REPO = Path(__file__).resolve().parents[1]
BLATT = REPO / "docs" / "EINBAU_STAND.md"

#: Eine Tabellenzeile: ``| A1 | Posten | Zustand | Seit | Beleg |``
#:
#: **Aus ``aiimaging.einbau`` geholt, nicht hier nachgebaut** — und der Anlass ist ein
#: Befund über diesen Wächter selbst (26.08.2026): Der Ausdruck stand hier als
#: ``[AB]\d+``, und als ein **Weg C** dazukam, hat er dessen sechs Zeilen stillschweigend
#: übersprungen. Sechs Posten waren unbewacht, und nichts wurde rot.
#:
#: *Ein Wächter mit fest eingebautem Alphabet hört auf zu wachen, sobald ein neuer
#: Buchstabe auftaucht.* ``test_der_waechter_sieht_jede_zeile_der_tabelle`` hält dagegen.
ZEILE = einbau.ZEILE

#: Was in Rückwärtsstrichen steht.
PFAD = re.compile(r"`([^`]+)`")

#: ``betrieb/kosmo-abholer.{service,timer}`` — eine Schreibweise für zwei Dateien.
KLAMMER = re.compile(r"^(.*)\{([^}]+)\}(.*)$")

#: ``kosmo_szene.als_ergebnis`` — ein Beleg kann auch auf ein Symbol zeigen statt auf
#: eine Datei. Das ist der SCHÄRFERE Beleg: Eine Datei kann bleiben, während die Funktion
#: darin verschwindet.
SYMBOL = re.compile(r"^([a-z_][a-z0-9_]*)\.([A-Za-z_][A-Za-z0-9_]*)$")

#: Die Wörter, mit denen ein Zustand anfängt — **aus ``aiimaging.einbau``**, nicht hier
#: nachgebaut. Zwei Listen derselben Kategorien an zwei Stellen driften auseinander, und
#: die Stelle, die zuerst veraltet, ist immer die im Test.
ZUSTAENDE = einbau.ZUSTAENDE

OFFEN = REPO / "auftraege" / "offen"

#: Die Ampeln der Legende. Sie sagen, WO ein Posten liegt, nicht wie er steht — beim
#: Lesen des Zustands stören sie darum nur.
AMPELN = ("🟩", "🟥")


def _zustand(spalten: list[str]) -> str:
    """Die Zustandsspalte ohne Ampel und Auszeichnung."""
    roh = spalten[1].replace("*", "")
    for ampel in AMPELN:
        roh = roh.replace(ampel, "")
    return roh.strip().lower()


def _zeilen() -> list[tuple[str, list[str]]]:
    """Die Tabellenzeilen als ``(kennung, spalten)``."""
    ergebnis = []
    for roh in BLATT.read_text(encoding="utf-8").splitlines():
        treffer = ZEILE.match(roh)
        if not treffer:
            continue
        spalten = [s.strip() for s in treffer.group(2).split("|")]
        ergebnis.append((treffer.group(1), spalten))
    return ergebnis


def _pfade(text: str) -> list[Path]:
    """Alles in Rückwärtsstrichen mit einem ``/`` darin — nur das ist ein Pfad im Repo.

    Ein blosser Dateiname wie ``befund.json`` ist **kein** Pfad: Er kommt in der
    Beschreibung vor, nicht als Beleg, und liegt zur Laufzeit ausserhalb des Repos.
    """
    gefunden = []
    for roh in PFAD.findall(text):
        roh = roh.split()[0].rstrip(",.;:")
        # Ein Pfad hat einen Schrägstrich — oder er ist eine Datei, die im Wurzelordner
        # wirklich liegt (`pyproject.toml`, `NOTICE`). Ein blosser Dateiname wie
        # `befund.json` ist dagegen KEIN Beleg: Er kommt in der Beschreibung vor und
        # liegt zur Laufzeit ausserhalb des Repos.
        if "/" not in roh and not (REPO / roh).is_file():
            continue
        klammer = KLAMMER.match(roh)
        namen = ([f"{klammer.group(1)}{t}{klammer.group(3)}"
                  for t in klammer.group(2).split(",")] if klammer else [roh])
        gefunden.extend(REPO / n for n in namen)
    return gefunden


def _symbole(text: str) -> list[tuple[str, str]]:
    """Belege der Form ``modul.symbol``, sofern es das Modul bei uns gibt."""
    gefunden = []
    for roh in PFAD.findall(text):
        roh = roh.split()[0].rstrip(",.;:")
        treffer = SYMBOL.match(roh)
        if treffer and (REPO / "src" / "aiimaging" / f"{treffer.group(1)}.py").is_file():
            gefunden.append((treffer.group(1), treffer.group(2)))
    return gefunden


ZEILEN = _zeilen()


def test_das_blatt_gibt_es_ueberhaupt():
    assert BLATT.is_file(), f"{BLATT.name} fehlt — dann gibt es wieder keinen Stand."
    assert ZEILEN, "Das Blatt hat keine Tabellenzeilen. Ein Stand ohne Posten ist keiner."


def test_die_nummerierung_hat_keine_luecken():
    """Ein fehlender Posten ist von einem erledigten nicht zu unterscheiden."""
    for buchstabe in ("A", "B"):
        nummern = sorted(int(k[1:]) for k, _ in ZEILEN if k.startswith(buchstabe))
        assert nummern == list(range(1, len(nummern) + 1)), (
            f"Weg {buchstabe} ist lückenhaft: {nummern}. Wer einen Posten streicht, "
            f"streicht ihn aus der Erinnerung — abgehakt wird, nicht gelöscht."
        )


@pytest.mark.parametrize("kennung,spalten", ZEILEN, ids=[k for k, _ in ZEILEN])
def test_jeder_posten_nennt_einen_bekannten_zustand(kennung, spalten):
    zustand = _zustand(spalten)
    assert any(zustand.startswith(z) for z in ZUSTAENDE), (
        f"{kennung}: Zustand {zustand!r} ist keiner der bekannten "
        f"({', '.join(ZUSTAENDE)}). Eine neue Kategorie gehört benannt und nicht "
        f"nebenbei eingeführt."
    )


@pytest.mark.parametrize("kennung,spalten", ZEILEN, ids=[k for k, _ in ZEILEN])
def test_jeder_beleg_zeigt_auf_etwas_das_es_gibt(kennung, spalten):
    """Ein Beleg auf eine gelöschte Datei ist schlimmer als keiner."""
    fehlend = [p for p in _pfade(spalten[-1]) if not p.exists()]
    assert not fehlend, (
        f"{kennung} beruft sich auf: {', '.join(str(p.relative_to(REPO)) for p in fehlend)} "
        f"— es gibt sie nicht. Entweder ist der Posten nicht mehr erledigt, oder der "
        f"Beleg ist umgezogen."
    )


@pytest.mark.parametrize("kennung,spalten", ZEILEN, ids=[k for k, _ in ZEILEN])
def test_jedes_belegte_symbol_gibt_es_wirklich(kennung, spalten):
    """Der schärfere Beleg: Eine Datei kann bleiben, während die Funktion darin verschwindet."""
    import importlib

    fehlend = []
    for modulname, symbol in _symbole(spalten[-1]):
        modul = importlib.import_module(f"aiimaging.{modulname}")
        if not hasattr(modul, symbol):
            fehlend.append(f"{modulname}.{symbol}")
    assert not fehlend, (
        f"{kennung} beruft sich auf {', '.join(fehlend)} — gibt es nicht (mehr). Ein "
        f"Beleg, der auf eine gelöschte Funktion zeigt, ist schlimmer als keiner."
    )


@pytest.mark.parametrize("kennung,spalten", ZEILEN, ids=[k for k, _ in ZEILEN])
def test_jeder_erledigte_posten_hat_ueberhaupt_einen_beleg(kennung, spalten):
    """Sonst wäre «erledigt» eine Behauptung — und genau daran ist die alte Liste zerfallen."""
    zustand = _zustand(spalten)
    if not zustand.startswith(("erledigt", "halb", "entschieden")):
        return
    assert _pfade(spalten[-1]) or _symbole(spalten[-1]) or "Sitzung" in spalten[-1], (
        f"{kennung} gilt als {zustand!r} und nennt weder Datei noch Symbol noch Sitzung "
        f"als Beleg. Wer eine Aussage über den Code in ein Dokument schreibt, sieht "
        f"vorher in den Code."
    )
    assert spalten[2].strip() not in ("", "—"), (
        f"{kennung} gilt als {zustand!r} und trägt kein Datum. Eine Zahl gehört an die "
        f"Bedingung, unter der sie gemessen wurde — ein Zustand an den Tag, an dem er galt."
    )


@pytest.mark.parametrize("kennung,spalten", ZEILEN, ids=[k for k, _ in ZEILEN])
def test_jeder_offene_posten_nennt_einen_auftrag_oder_ausdruecklich_niemanden(kennung, spalten):
    """Damit kein Posten still verwaist.

    «niemand» ist ausdrücklich erlaubt — und ausdrücklich zu schreiben. Der Unterschied
    zwischen «keiner treibt das» und «keiner hat daran gedacht» ist der ganze Zweck.
    """
    zustand = _zustand(spalten)
    if not zustand.startswith("offen"):
        return
    beleg = spalten[-1]
    if "niemand" in beleg.lower():
        return
    auftraege = [p for p in _pfade(beleg) if "auftraege" in str(p)]
    assert auftraege, (
        f"{kennung} ist offen, nennt aber weder einen Auftrag noch ausdrücklich "
        f"«niemand». Ein offener Posten ohne Treiber ist ein vergessener."
    )
    liegen = [p for p in auftraege if p.parent == OFFEN and p.is_file()]
    assert liegen, (
        f"{kennung} verweist auf einen Auftrag, der nicht (mehr) in "
        f"{OFFEN.relative_to(REPO)} liegt. Ist er beantwortet, gehört der Posten "
        f"fortgeschrieben."
    )


def test_das_blatt_wird_vom_readme_erwaehnt():
    """Eine Landkarte, die niemand findet, ist die alte Lage mit einer Datei mehr."""
    readme = (REPO / "README.md").read_text(encoding="utf-8")
    assert "EINBAU_STAND" in readme, (
        "Das README verweist nicht auf den Einbau-Stand. Was der Owner erst "
        "zusammensuchen muss, existiert nicht."
    )


# ── Dass die Prüfungen oben überhaupt etwas prüfen ──────────────────────────────────
#
# Die Vakuumprobe hat es gefunden: Sechs Zeilen nennen **keinen Pfad** (sie berufen sich
# auf ein Symbol oder auf «niemand»), und für sie war `test_jeder_beleg_zeigt_auf_etwas`
# eine Zusicherung über eine leere Liste. Jede Zeile ist zwar von *irgendeiner* der drei
# Prüfungen erfasst — aber das stand nirgends, und es liess sich nicht nachlesen.
#
# Die beiden Tests hier schliessen das: Der erste zählt je Zeile die prüfbaren
# Referenzen, der zweite ist die **Gegenprobe** — er zeigt am selben Mechanismus, dass
# sich die Sammlung im umgekehrten Fall füllt.

@pytest.mark.parametrize("kennung,spalten", ZEILEN, ids=[k for k, _ in ZEILEN])
def test_jede_zeile_ist_ueberhaupt_pruefbar(kennung, spalten):
    """Jede Zeile nennt einen Pfad, ein Symbol, eine Sitzung — oder ausdrücklich «niemand».

    Ohne diesen Test kann eine Zeile alle drei Prüfungen bestehen, indem sie nichts sagt,
    worauf sie sich beziehen liesse.
    """
    beleg = spalten[-1]
    referenzen = len(_pfade(beleg)) + len(_symbole(beleg))
    assert referenzen or "niemand" in beleg.lower() or "Sitzung" in beleg, (
        f"{kennung} nennt weder Datei noch Symbol noch Sitzung noch «niemand». Die "
        f"Zeile ist damit von keiner Prüfung erfasst — sie sagt etwas, das sich nicht "
        f"nachsehen lässt."
    )


def test_der_waechter_sieht_jede_zeile_der_tabelle():
    """**Von der anderen Seite gezählt — und der Anlass ist dieser Wächter selbst.**

    Sein Zeilenausdruck stand bis zum 26.08.2026 als ``[AB]\\d+`` hier. Als an jenem Abend
    ein **Weg C** dazukam, hat er dessen sechs Zeilen stillschweigend übersprungen: Sechs
    Posten waren unbewacht, alle Tests grün.

    *Ein Wächter mit fest eingebautem Alphabet hört auf zu wachen, sobald ein neuer
    Buchstabe auftaucht* — und er sagt es nicht, denn eine Zeile, die er nicht sieht, kann
    er auch nicht bemängeln.

    Dieser Test zählt die Zeilen darum **unabhängig** vom Ausdruck des Wächters: alles,
    was wie ``| X<Ziffer> |`` aussieht, muss auch bei ihm ankommen.
    """
    roh = re.findall(r"^\|\s*([A-Za-z]+\d+)\s*\|", BLATT.read_text(encoding="utf-8"),
                     re.MULTILINE)
    gesehen = [k for k, _ in _zeilen()]

    assert roh, "keine einzige Tabellenzeile gefunden — dann prüft dieser Test nichts"
    assert sorted(roh) == sorted(gesehen), (
        f"Der Wächter übersieht {sorted(set(roh) - set(gesehen))}. Eine Zeile, die er "
        f"nicht sieht, kann er auch nicht bemängeln."
    )


def test_die_pruefung_der_belege_faellt_bei_einem_falschen_pfad():
    """Die Gegenprobe. Ein Wächter, der nicht fällt, bewacht nichts.

    Sie läuft an einer erfundenen Zeile und nicht am Blatt — das Blatt zu verbiegen, um
    zu sehen, ob der Test rot wird, hiesse, es dafür kaputtzumachen.
    """
    erfunden = "Beleg: `src/aiimaging/gibt_es_nicht.py`"
    assert [p for p in _pfade(erfunden) if not p.exists()], (
        "Ein Pfad auf eine nicht vorhandene Datei wird nicht als fehlend erkannt — "
        "dann meldet der Wächter oben auch bei einem echten Fehler nichts."
    )
    echt = "Beleg: `src/aiimaging/abholer.py`"
    assert not [p for p in _pfade(echt) if not p.exists()]


def test_die_pruefung_der_symbole_faellt_bei_einem_falschen_namen():
    """Dieselbe Gegenprobe für den schärferen Beleg."""
    import importlib

    modul = importlib.import_module("aiimaging.abholer")
    assert not hasattr(modul, "gibt_es_nicht")
    assert _symbole("`abholer.gibt_es_nicht`") == [("abholer", "gibt_es_nicht")], (
        "Ein Symbolbeleg wird gar nicht erst erkannt — dann prüft der Wächter oben "
        "nie eines."
    )
    assert hasattr(modul, "verarbeiter")
