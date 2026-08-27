"""DER EINBAU — was gebaut ist, was davon in der Software steht, und wer es einbaut.

Warum es dieses Modul gibt (Owner-Auftrag 26.08.2026)
-----------------------------------------------------
Der Owner hat an diesem Abend das Ziel geradegerückt:

    *«Sorge dafür, dass andere Worker immer alles einbauen in die Software — das ist
    Endziel. Du verteilst, wo was hin muss, und du bist verantwortlich, dass sie es
    einbauen und mir dann bestätigst.»*

Damit ist gebauter Code **kein Ergebnis mehr**, sondern eine Zwischenstufe. Das Ergebnis
ist Code, der in KosmoOrbit läuft — und dazwischen liegen drei fremde Wartende: die
HomeStation, der Cloud-Worker und der UI-Worker.

**Warum das ein Werkzeug braucht und keinen Vorsatz.** Verantwortung für etwas, das
anderswo geschieht, lässt sich nur führen, wenn der Rückstand **zählbar** ist. Am
26.08.2026 lagen fünfzehn Aufträge unbeantwortet, und diese Zahl entstand, indem jemand
zwei Verzeichnisse von Hand verglich. Was von Hand gezählt wird, wird irgendwann nicht
mehr gezählt — dieselbe Lehre wie bei `docs/EINBAU_STAND.md` selbst, dessen Vorläufer
sieben Tage lang niemand fortschrieb.

Was dieses Modul beantwortet
-----------------------------
1. **Welcher Auftrag liegt wie lange unbeantwortet, und bei wem?** — :func:`rueckstand`.
   Nach Worker getrennt, denn ein Rückstand beim UI-Worker verlangt einen anderen
   Handgriff als einer bei der HomeStation.
2. **Welcher Posten des Einbaus hat gar keinen Adressaten?** — :func:`ohne_adressat`.
   Bis zum 26.08.2026 durfte ein offener Posten ausdrücklich «niemand» nennen. Unter dem
   Auftrag oben ist das keine zulässige Antwort mehr: Ein Posten ohne Adressaten wird nie
   eingebaut, und niemandem fällt es auf.
3. **Beides zusammen** — :func:`bericht`, die Vorlage für die Bestätigung an den Owner.

Was es ausdrücklich NICHT beantwortet
--------------------------------------
**Ob ein Worker den Auftrag gut ausgeführt hat.** Dieses Modul zählt Zustellung und
Antwort, nicht Güte. Ein Ergebnis mit ``status: fehler`` gilt hier als *beantwortet* —
die Frage ist gestellt und eine Antwort ist da. Ob sie taugt, steht in den Befunden.

**Ob ein Posten wirklich eingebaut ist.** Es liest, was `EINBAU_STAND.md` behauptet, und
prüft nur, dass jede Behauptung einen Adressaten hat. Der Beleg selbst wird von
``tests/test_einbau_stand.py`` geprüft.

Reine Standardbibliothek, keine Oberfläche (Regeln 3 und 4). Alle Ausgaben sind Zahlen
und kurzer Text — kein Pfad, der einen Benutzernamen tragen könnte.
"""
from __future__ import annotations

import re
from datetime import date, datetime, timezone
from pathlib import Path

from aiimaging import auftrag as _auftrag

#: Eine Zeile der Einbau-Tabelle: ``| A1 | Posten | Zustand | Seit | Beleg |``
#:
#: **Der Buchstabe ist offen, und das ist der Punkt.** Die erste Fassung dieses Ausdrucks
#: stand als ``[AB]\d+`` im Wächter — und als am 26.08.2026 ein **Weg C** dazukam, hat er
#: dessen sechs Zeilen stillschweigend übersprungen. Ein Wächter mit fest eingebautem
#: Alphabet hört auf zu wachen, sobald ein neuer Buchstabe auftaucht, und sagt nichts.
ZEILE = re.compile(r"^\|\s*([A-Z]+\d+)\s*\|(.+)\|\s*$")

#: Wie eine Auftragskennung im Beleg aussieht: ``auf-20260826-58``.
#:
#: **Gesucht wird der Adressat, nicht sein Fehlen** — und das ist eine Berichtigung vom
#: 26.08.2026. Die erste Fassung suchte nach dem Wort «niemand» im Beleg. Sie hat sich am
#: selben Abend selbst gefangen: Kaum stand in einer Zeile der Satz *«stand bis heute als
#: «niemand» da»*, meldete sie den Posten weiter als unbesetzt, obwohl er längst einen
#: Auftrag trug.
#:
#: *Eine Prüfung auf die Abwesenheit eines Wortes prüft die Prosa, nicht die Sache.* Ein
#: Adressat ist da, wenn ein Auftrag genannt ist — das ist positiv belegbar und steht
#: nicht in der Formulierung.
AUFTRAGSKENNUNG = re.compile(r"auf-\d{8}-\d+")

#: Das Wort, mit dem ein offener Posten bis zum 26.08.2026 sagen durfte, dass ihn niemand
#: treibt. Es steht hier nur noch, damit die alte Angabe erkennbar bleibt.
OHNE_ADRESSAT = "niemand"

#: Ampeln der Legende — sie sagen, WO ein Posten liegt, nicht wie er steht.
AMPELN = ("🟩", "🟥")

#: Die Wörter, mit denen ein Zustand anfängt. **Genau diese** — ein weiteres wäre eine
#: neue Kategorie und gehört nicht still eingeführt.
#:
#: ``gebaut, am gerät unbestätigt`` ist am 26.08.2026 dazugekommen, mit Weg C: Was bei
#: der HomeStation über ``git pull`` ankommt, ist bei uns fertig und drüben ungeprüft.
#: Weder ``erledigt`` noch ``offen`` trifft das — es ist die dritte Antwort dieses
#: Projekts, angewandt auf den Einbau.
ZUSTAENDE = ("erledigt", "halb", "entschieden, nicht gebaut", "offen",
             "gebaut, am gerät unbestätigt")

#: Zustände, die als **noch nicht in der Software** gelten. ``halb`` gehört dazu — ein
#: halb eingebauter Posten ist einer, an dem noch etwas fehlt, und genau die fehlen sonst.
#: ``gebaut, am gerät unbestätigt`` ebenso: Gebaut ist seit dem Owner-Auftrag vom
#: 26.08.2026 kein Ergebnis mehr, sondern eine Zwischenstufe.
OFFENE_ZUSTAENDE = tuple(z for z in ZUSTAENDE if z != "erledigt")


class EinbauError(ValueError):
    """Das Einbaublatt lässt sich so nicht lesen."""


def _spalten(rest: str) -> list[str]:
    return [s.strip() for s in rest.split("|")]


def _ohne_auszeichnung(roh: str) -> str:
    for ampel in AMPELN:
        roh = roh.replace(ampel, "")
    return roh.replace("*", "").strip()


def posten(blatt) -> list[dict]:
    """Die Tabellenzeilen von ``EINBAU_STAND.md`` als Zahlen und Text.

    Args:
        blatt: Pfad auf das Blatt oder sein Inhalt als Zeichenkette.

    Returns:
        Je Zeile ``{kennung, posten, zustand, seit, beleg, offen}``. ``offen`` sagt, ob der
        Zustand in :data:`OFFENE_ZUSTAENDE` steht — also ob noch etwas einzubauen ist.

    Raises:
        EinbauError: Das Blatt enthält keine einzige lesbare Zeile. Ein leeres Ergebnis
            wäre sonst nicht von «alles erledigt» zu unterscheiden, und das ist genau die
            Verwechslung, gegen die dieses Modul gebaut ist.
    """
    text = blatt if isinstance(blatt, str) else Path(blatt).read_text(encoding="utf-8")
    aus: list[dict] = []
    for zeile in text.splitlines():
        treffer = ZEILE.match(zeile)
        if not treffer:
            continue
        spalten = _spalten(treffer.group(2))
        if len(spalten) < 4:
            continue
        zustand = _ohne_auszeichnung(spalten[1]).lower()
        aus.append({
            "kennung": treffer.group(1),
            "posten": _ohne_auszeichnung(spalten[0]),
            "zustand": zustand,
            "seit": _ohne_auszeichnung(spalten[2]),
            "beleg": spalten[3],
            "offen": any(zustand.startswith(z) for z in OFFENE_ZUSTAENDE),
        })
    if not aus:
        raise EinbauError(
            "Kein einziger Posten gelesen. Entweder ist das Blatt leer, oder die Tabelle "
            "hat eine andere Gestalt als erwartet — beides sähe von aussen aus wie "
            "«nichts offen», und das ist die gefährlichere der beiden Lesarten."
        )
    return aus


def ohne_adressat(blatt) -> list[dict]:
    """Offene Posten, die **niemand** treibt.

    Bis zum 26.08.2026 war ``niemand`` eine zulässige Angabe: besser ausdrücklich
    unbesetzt als stillschweigend. Seit dem Owner-Auftrag desselben Abends ist der Einbau
    das Ziel, und damit ist ein Posten ohne Adressaten kein ehrlicher Zustand mehr,
    sondern ein Rückstand — er wird nie eingebaut, und niemandem fällt es auf.

    **Gesucht wird der Adressat, nicht sein Fehlen:** Ein Posten gilt als besetzt, wenn
    sein Beleg eine Auftragskennung nennt. Siehe :data:`AUFTRAGSKENNUNG` — die erste
    Fassung suchte nach dem Wort «niemand» und hat sich damit an der eigenen Erklärung
    verschluckt.
    """
    return [p for p in posten(blatt)
            if p["offen"] and not AUFTRAGSKENNUNG.search(p["beleg"])]


def _tage_her(zeitstempel: str, heute: date) -> int | None:
    """Alter in Tagen — ``None``, wenn der Zeitstempel nicht lesbar ist."""
    try:
        gestellt = datetime.fromisoformat(str(zeitstempel).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    return (heute - gestellt.astimezone(timezone.utc).date()).days


def rueckstand(repo_wurzel, *, heute: date | None = None) -> dict:
    """Unbeantwortete Aufträge, nach Worker getrennt und nach Alter geordnet.

    **Warum nach Worker getrennt.** Die drei können nicht dasselbe, und ein Rückstand
    verlangt je nach Adressat einen anderen Handgriff: Bei der HomeStation heisst er
    «läuft der Dienst?», beim Cloud-Worker «liegt eine Vertragsfrage quer?», beim
    UI-Worker «hat er unser Repo gezogen?». Eine Gesamtzahl verwischt das.

    Args:
        repo_wurzel: Wurzel des Repos.
        heute: Bezugstag für das Alter. Ohne Angabe der heutige. **Er ist ein Parameter,
            damit ein Test nicht mit der Uhr rechnen muss** — eine Zusicherung, die morgen
            anders ausgeht, ist keine.

    Returns:
        ``{n, je_worker, aelteste_tage, eintraege}``. Jeder Eintrag trägt
        ``{auftrag_id, worker, art, tage, beschreibung}`` — **keine Pfade**, Regel 3.
    """
    stichtag = heute or datetime.now(timezone.utc).date()
    eintraege = []
    for satz in _auftrag.unerledigt(repo_wurzel):
        tage = _tage_her(satz.get("erstellt"), stichtag)
        eintraege.append({
            "auftrag_id": satz.get("auftrag_id"),
            "worker": satz.get("worker"),
            "art": satz.get("art"),
            "tage": tage,
            "beschreibung": str(satz.get("beschreibung") or "")[:120],
        })
    eintraege.sort(key=lambda e: (-(e["tage"] if e["tage"] is not None else -1),
                                  str(e["auftrag_id"])))
    je_worker = {w: [e for e in eintraege if e["worker"] == w] for w in _auftrag.WORKER}
    alter = [e["tage"] for e in eintraege if e["tage"] is not None]
    return {
        "n": len(eintraege),
        "je_worker": {w: len(v) for w, v in je_worker.items()},
        "aelteste_tage": max(alter) if alter else None,
        "eintraege": eintraege,
    }


def bericht(repo_wurzel, blatt=None, *, heute: date | None = None) -> dict:
    """Beides zusammen — die Vorlage für die Bestätigung an den Owner.

    Returns:
        ``{rueckstand, ohne_adressat, offene_posten, n_posten, bereit}``.

        ``bereit`` ist ``True``, wenn **kein** Posten ohne Adressaten dasteht. Es sagt
        ausdrücklich **nicht**, dass alles eingebaut ist — nur, dass für alles, was noch
        fehlt, jemand benannt ist. Das ist der Teil, für den ich hafte; der Einbau selbst
        geschieht drüben.
    """
    wurzel = Path(repo_wurzel)
    seite = blatt or wurzel / "docs" / "EINBAU_STAND.md"
    alle = posten(seite)
    verwaist = ohne_adressat(seite)
    return {
        "rueckstand": rueckstand(wurzel, heute=heute),
        "ohne_adressat": verwaist,
        "offene_posten": [p for p in alle if p["offen"]],
        "n_posten": len(alle),
        "bereit": not verwaist,
    }


__all__ = [
    "AMPELN", "AUFTRAGSKENNUNG", "OFFENE_ZUSTAENDE", "OHNE_ADRESSAT", "ZEILE",
    "ZUSTAENDE",
    "EinbauError", "bericht", "ohne_adressat", "posten", "rueckstand",
]
