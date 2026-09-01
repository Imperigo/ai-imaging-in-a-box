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

#: Wie ein **erledigter** Posten sagt, worauf sein Beleg ruht: ``belegt im Repo`` oder
#: ``belegt am Gerät: …``.
#:
#: **Der Anlass ist der teuerste Buchführungsfehler dieses Projekts** (27.08.2026): ``B8``
#: stand sechs Tage als *erledigt*, weil die eingecheckte Diensteinheit den nötigen
#: Schalter trug. Die **installierte** stammte vom 20.08. und kannte ihn nicht — jeder über
#: den MCP-Einlass bestellte Render blieb liegen, während hier stand, es sei behoben.
#:
#: Der Wächter konnte das nicht sehen: Er prüft, ob ein Beleg **existiert**, und der
#: existierte. *Eine Datei im Repo belegt, was jemand geschrieben hat, nicht was auf dem
#: Gerät läuft.*
#:
#: **Verifiziert wird hier nichts** — das kann dieses Modul nicht, und es soll auch nicht
#: so tun. Es verlangt nur, dass die Zeile **sagt**, welcher Art ihr Beleg ist. Danach ist
#: prüfbar, was vorher Auslegung war.
BELEG_REPO = re.compile(r"belegt im Repo", re.IGNORECASE)
BELEG_GERAET = re.compile(r"belegt am Ger[äa]t", re.IGNORECASE)

#: Was in einem Beleg verrät, dass die Aussage **nicht** im Repo entschieden wird: ein
#: Kommandozeilenschalter, eine systemd-Einheit, ein Pfad nach ``betrieb/``.
#:
#: Alle drei sagen etwas darüber, **wie etwas aufgerufen wird** — und das steht nicht in
#: der Datei, sondern in der Installation. ``B8`` nannte ``tools/abholen.py
#: --eigener-store``: Der Schalter war im Repo und auf dem Gerät nicht.
GERAETEZEICHEN = (
    re.compile(r"`[^`]*\s--[a-z][a-z0-9-]*"),      # ein Schalter im Beleg
    re.compile(r"\.(service|timer)\b"),            # eine systemd-Einheit
    re.compile(r"\bbetrieb/"),                      # der Ordner für Betriebsdateien
)

#: Eine Uhrzeit im Beleg — die zweite zulässige Art, ``belegt am Gerät`` einzulösen.
#:
#: **Warum eine Uhrzeit und nicht irgendein Satz.** Eine Messung, die drüben stattgefunden
#: hat, trägt eine Uhr; eine Behauptung nicht. Das ist keine starke Prüfung — sie liesse
#: sich hinschreiben —, aber sie kann eines nicht: durch das Zeigen auf eine Datei im Repo
#: erfüllt werden. Genau das war der Fehler bei ``B8``.
#:
#: Die stärkere Art bleibt der beantwortete Auftrag. Diese hier gibt es, weil sonst eine
#: **wirklich am Gerät gemachte** Messung ohne Ergebnisdatei nicht buchbar wäre — und was
#: sich nicht buchen lässt, wird untertrieben statt eingetragen.
MESSZEIT = re.compile(r"\b\d{1,2}:\d{2}(:\d{2})?\b")

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


def beantwortete_auftraege(repo_wurzel) -> set[str]:
    """Welche Aufträge **wirklich beantwortet** sind — nach dem abgeleiteten Zustand.

    **Gezählt wird die Antwort, nicht der Auftrag.** Eine Auftragsdatei belegt, dass
    jemand etwas verlangt hat; erst die Ergebnisdatei belegt, dass drüben jemand
    hingesehen hat.

    **Und bis zum 28.08.2026 zählte diese Funktion die DATEI und nicht ihren Inhalt** —
    derselbe Fehler eine Ebene tiefer als der, gegen den sie gebaut wurde. Aufgefallen ist
    er, als der abgeleitete Zustand dazukam: ``auf-20260822-31`` trägt ``status: ok`` und
    ``art: weitergereicht_und_teilbeantwortet``. Es galt als Antwort und war ein
    Weiterleitungsvermerk — und **zwei erledigte Posten des Einbau-Stands beriefen sich
    darauf**.

    *Eine Datei im Ergebnisordner belegt, dass jemand geantwortet HAT — nicht, dass er die
    Frage beantwortet hat.*
    """
    return {kennung for kennung, zustand
            in _auftrag.zustaende(Path(repo_wurzel)).items()
            if zustand == _auftrag.ZUSTAND_BEANTWORTET}


def ohne_geraetebeweis(blatt, repo_wurzel) -> list[dict]:
    """Erledigte Posten, deren Beleg nicht sagt, **worüber** er etwas aussagt.

    Drei Mängel, jeder mit eigener Begründung im Rückgabewert:

    ``keine angabe``
        Der Posten steht auf *erledigt* und sagt nicht, ob sein Beleg im Repo oder am
        Gerät liegt. Bis zum 27.08.2026 war das die Regel — und genau so ist ``B8`` sechs
        Tage lang als erledigt geführt worden, während auf dem Gerät die Fassung vom
        20.08. lief.

    ``repo trotz gerätezeichen``
        Der Posten behauptet *belegt im Repo*, sein Beleg nennt aber einen
        Kommandozeilenschalter, eine systemd-Einheit oder einen Pfad nach ``betrieb/``.
        **Das ist die B8-Falle wörtlich:** Alle drei sagen etwas darüber, wie etwas
        aufgerufen wird, und das steht nicht in der Datei, sondern in der Installation.

    ``gerät ohne antwort``
        Der Posten behauptet *belegt am Gerät* und löst das nicht ein. Zwei Arten sind
        zugelassen: ein Auftrag, auf den drüben **geantwortet** wurde, oder die **Uhrzeit**
        einer Messung dort. Ein Auftrag, der noch offen liegt, ist keine Rückmeldung.

        *Die Uhrzeit ist die schwächere der beiden und steht trotzdem hier: Sonst wäre
        eine wirklich am Gerät gemachte Messung ohne Ergebnisdatei nicht buchbar — und was
        sich nicht buchen lässt, wird untertrieben statt eingetragen. Was sie nicht kann,
        ist der Punkt: durch das Zeigen auf eine Datei im Repo erfüllt zu werden.*

    **Was diese Prüfung NICHT tut:** Sie sieht auf keinem Gerät nach. Das kann sie nicht,
    und sie soll auch nicht so tun. Sie verlangt, dass die Zeile ihre Art des Belegs
    **nennt** — danach ist prüfbar, was vorher Auslegung war.

    Returns:
        Je Mangel ``{kennung, posten, mangel, grund}``. Leere Liste heisst: jede erledigte
        Zeile sagt, worauf sie ruht.
    """
    beantwortet = beantwortete_auftraege(repo_wurzel)
    aus: list[dict] = []
    for eintrag in posten(blatt):
        if eintrag["zustand"] != "erledigt":
            continue
        beleg = eintrag["beleg"]
        am_geraet = bool(BELEG_GERAET.search(beleg))
        im_repo = bool(BELEG_REPO.search(beleg))

        if not am_geraet and not im_repo:
            aus.append({**_kurz(eintrag), "mangel": "keine angabe", "grund": (
                "Erledigt, ohne zu sagen, ob der Beleg im Repo oder am Gerät liegt. "
                "Eine Datei im Repo belegt, was jemand geschrieben hat, nicht was auf "
                "dem Gerät läuft (B8, 27.08.2026).")})
            continue

        if im_repo and not am_geraet:
            getroffen = [z.pattern for z in GERAETEZEICHEN if z.search(beleg)]
            if getroffen:
                aus.append({**_kurz(eintrag), "mangel": "repo trotz gerätezeichen",
                            "grund": (
                    "Behauptet «belegt im Repo», nennt aber einen Schalter, eine "
                    "Diensteinheit oder einen Pfad nach betrieb/. Alle drei sagen etwas "
                    "darüber, WIE etwas aufgerufen wird — und das steht nicht in der "
                    f"Datei, sondern in der Installation. Getroffen: {getroffen[0]}")})
            continue

        genannt = set(AUFTRAGSKENNUNG.findall(beleg))
        if not (genannt & beantwortet) and not MESSZEIT.search(beleg):
            offen = ", ".join(sorted(genannt)) or "gar keinen"
            aus.append({**_kurz(eintrag), "mangel": "gerät ohne antwort", "grund": (
                f"Behauptet «belegt am Gerät», nennt aber weder einen beantworteten "
                f"Auftrag (genannt: {offen}) noch eine Uhrzeit einer Messung dort. Eine "
                f"Behauptung über ein fremdes Gerät braucht eine Rückmeldung von dort "
                f"oder eine Uhr.")})
    return aus


def _kurz(eintrag: dict) -> dict:
    return {"kennung": eintrag["kennung"], "posten": eintrag["posten"][:70]}


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
        ``{rueckstand, ohne_adressat, ohne_geraetebeweis, offene_posten, n_posten,
        bereit}``.

        ``bereit`` ist ``True``, wenn **kein** Posten ohne Adressaten dasteht **und** jede
        erledigte Zeile sagt, worauf ihr Beleg ruht. Es sagt ausdrücklich **nicht**, dass
        alles eingebaut ist — nur, dass für alles, was noch fehlt, jemand benannt ist, und
        dass nichts als fertig geführt wird, ohne zu sagen wo. Das ist der Teil, für den
        ich hafte; der Einbau selbst geschieht drüben.

        *Die zweite Bedingung ist am 27.08.2026 dazugekommen, nachdem ``B8`` sechs Tage
        als erledigt geführt worden war, während auf dem Gerät eine ältere Fassung lief.*
    """
    wurzel = Path(repo_wurzel)
    seite = blatt or wurzel / "docs" / "EINBAU_STAND.md"
    alle = posten(seite)
    verwaist = ohne_adressat(seite)
    unbelegt = ohne_geraetebeweis(seite, wurzel)
    return {
        "rueckstand": rueckstand(wurzel, heute=heute),
        # WIE OFT DIESER ADRESSAT JE GEANTWORTET HAT — die Zahl, die neben dem Rückstand
        # fehlte. Ein Rückstand sagt, wie viel bei jemandem liegt; er sagt nicht, ob dort
        # überhaupt jemand ist. Am 01.09.2026 lagen elf der 28 offenen Aufträge bei zwei
        # Adressaten, von denen noch NIE eine Antwort gekommen war.
        "antwortverhalten": _auftrag.antwortverhalten(wurzel),
        "ohne_adressat": verwaist,
        "ohne_geraetebeweis": unbelegt,
        "offene_posten": [p for p in alle if p["offen"]],
        "n_posten": len(alle),
        "bereit": not verwaist and not unbelegt,
    }


__all__ = [
    "AMPELN", "AUFTRAGSKENNUNG", "BELEG_GERAET", "BELEG_REPO", "GERAETEZEICHEN",
    "MESSZEIT", "OFFENE_ZUSTAENDE", "OHNE_ADRESSAT", "ZEILE", "ZUSTAENDE",
    "EinbauError", "beantwortete_auftraege", "bericht", "ohne_adressat",
    "ohne_geraetebeweis", "posten", "rueckstand",
]
