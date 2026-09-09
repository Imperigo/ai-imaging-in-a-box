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
import json as _json
from pathlib import Path

from aiimaging import auftrag as _auftrag
from aiimaging import auftragspost as _post

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
        # EIN UNBEKANNTER ZUSTAND IST EIN FEHLER UND KEIN «NICHT OFFEN».
        #
        # Gefunden am 09.09.2026 an einem eigenen Ausrutscher: Für C7 stand hier eine
        # Ampel, die `AMPELN` nicht kennt (⬛ statt 🟩). Das Zeichen blieb im Text stehen,
        # der Zustand hiess damit «⬛ entschieden, nicht gebaut», und `startswith` traf
        # keinen der offenen Zustände. Der Posten verschwand aus der Zählung — der Stand
        # sprang von 22 auf 21, und **das sah aus wie Fortschritt.**
        #
        # Genau die Lesart, gegen die drei Zeilen weiter unten schon ein Riegel steht: Ein
        # unlesbares Blatt sähe von aussen aus wie «nichts offen». Eine unlesbare ZEILE
        # sieht aus wie «dieser eine Posten ist fertig», und das fällt niemandem auf.
        if not any(zustand.startswith(z) for z in ZUSTAENDE):
            raise EinbauError(
                f"Posten {treffer.group(1)}: unbekannter Zustand {zustand!r}. Erlaubt "
                f"sind {', '.join(ZUSTAENDE)} — und eine Ampel aus {' '.join(AMPELN)}. "
                f"Ein Zustand, den dieses Modul nicht kennt, zählte sonst als erledigt: "
                f"Der Posten fiele aus dem Rückstand, ohne dass jemand ihn eingebaut hat."
            )
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


def unverarbeitete_antworten(repo_wurzel, *, docs_ordner: str = "docs") -> list[dict]:
    """Antworten, die **beantwortet und nirgends aufgeschrieben** sind.

    Der Anlass ist eine Frage des Owners vom 09.09.2026 — *«sind alle Aufgaben vom
    Homeworker von dir erledigt?»* — und die Antwort war **nein**: Drei Antworten der
    HomeStation lagen zwei Tage ungelesen, und alle drei kippten etwas
    (`auf-20260907-81`, `-82`, `-83`).

    **Warum sie durchrutschen konnten, ist der eigentliche Befund.** :func:`rueckstand`
    zählt Aufträge **ohne** Antwort. Diese drei hatten eine — sie verschwanden damit aus
    jeder Zählung, **bevor** irgendjemand geprüft hatte, ob die Antwort verarbeitet wurde.
    *Zwischen «beantwortet» und «gelesen» lag in diesem Repo kein Zähler.*

    Als **gelesen** gilt eine Antwort, wenn ihre Auftragskennung irgendwo unter ``docs/``
    steht — im Plan, im Sitzungsprotokoll, im Einbau-Stand oder in einem Bericht. Das ist
    absichtlich **kein Merkmal, das man setzen kann**: Ein Häkchen liesse sich anhaken,
    ohne die Antwort gelesen zu haben. Wer eine Kennung in den Plan schreibt, hat den
    Befund aufgeschrieben — und genau daran hängt die Regel des Projekts, dass jede
    Erfolgsmeldung an etwas hängen muss, das vom Erzähler unabhängig ist.

    **Was diese Zahl NICHT sagt, gemessen bei der Einführung:** Von den fünf Antworten,
    die sie am 09.09.2026 zuerst meldete, waren **drei sachlich längst verarbeitet** — nur
    ohne ihre Kennung. Der CPU-Befund aus `auf-20260826-54` steht seit dem 06.09. als
    gemessener Block im Runner, die Kamerastreuung aus `auf-20260823-35` in `PLAN.md` und
    in `varianten.py`, und `auf-20260818-04` war zurückgezogen. *Die Funktion misst, ob
    jemand die Kennung aufgeschrieben hat, nicht ob jemand den Befund verstanden hat.* Sie
    ist ein Anlass nachzusehen und kein Vorwurf — aber die drei, die am selben Tag
    wirklich ungelesen waren, hätte sie am ersten Tag gemeldet.

    Args:
        repo_wurzel: Wurzel des Repos.
        docs_ordner: Der Ordner, in dem nachgesehen wird. Nur zum Prüfen gedacht.

    Returns:
        Je Antwort ``{kennung, beendet, datei}``, nach Kennung sortiert.

    Raises:
        EinbauError: Der Dokumentordner fehlt oder trägt kein einziges Markdown. Ohne
            ihn sähe **jede** Antwort unverarbeitet aus — die harmlosere Lesart wäre
            «alles gelesen», und die ist hier die falsche.
    """
    wurzel = Path(repo_wurzel)
    ordner = wurzel / docs_ordner
    texte = list(ordner.rglob("*.md")) if ordner.is_dir() else []
    if not texte:
        raise EinbauError(
            f"Kein einziges Markdown unter {ordner}. Ohne die Dokumente lässt sich nicht "
            f"sagen, welche Antwort aufgeschrieben wurde — und jede Antwort sähe "
            f"unverarbeitet aus."
        )
    geschrieben = "\n".join(d.read_text(encoding="utf-8", errors="ignore") for d in texte)

    aus: list[dict] = []
    for datei in sorted((wurzel / "auftraege" / "ergebnisse").glob("auf-*.json")):
        try:
            inhalt = _json.loads(datei.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        kennung = inhalt.get("auftrag_id") if isinstance(inhalt, dict) else None
        if not kennung or kennung in geschrieben:
            continue
        if any(a["kennung"] == kennung for a in aus):
            continue
        aus.append({"kennung": kennung,
                    "beendet": inhalt.get("beendet") or "",
                    "datei": datei.name})
    return sorted(aus, key=lambda a: a["kennung"])


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


def _beruehrte_messungen(wurzel) -> dict:
    """``{"beruehrt": [...]}`` — oder ein leeres Wörterbuch, wenn die Frage hier nicht geht.

    Eingekapselt, damit `bericht` nicht daran scheitert: `aiimaging.beruehrung` braucht ein
    echtes git-Repo, und `bericht` läuft in Proben auch über blosse Ordner.
    """
    docs = Path(wurzel) / "docs"
    if not docs.is_dir():
        return {}
    from aiimaging import beruehrung as _ber
    reihe = _ber.durchsicht(docs, repo=wurzel)
    # BEIDE LISTEN, und die zweite ist der Grund fuer diese Funktion. `beruehrt` sagt
    # «ansehen»; `unklar` sagt «hier laesst sich nicht einmal fragen» — ein Dokument ohne
    # Grundlagenzeile, oder eines, dessen Stand dieses Arbeitsverzeichnis nie gesehen hat.
    # Nur die erste Liste zu melden hiesse, das Unklare als unberuehrt zu zaehlen, und
    # genau das ist die stille Fehlmeldung, gegen die dieses Modul gebaut ist.
    return {
        "beruehrt": [{"datei": s["datei"], "betroffen": s["betroffen"]}
                     for s in reihe if s["zustand"] == _ber.BERUEHRT],
        "beruehrt_unklar": [s["datei"] for s in reihe if s["zustand"] == _ber.UNKLAR],
    }


def wartet_auf_beantwortetes(repo_wurzel, blatt=None, *, heute: date | None = None) -> list[dict]:
    """Offene Posten, deren **treibende Aufträge alle schon beantwortet sind**.

    **Der blinde Fleck, den das hier schliesst** (09.09.2026). Der Einbau-Stand zählt
    Posten, und der Rückstand zählt Aufträge *ohne* Antwort. Zwischen beidem liegt ein
    Zustand, den niemand zählte: **Der Posten steht offen, und die Antwort, auf die er
    wartet, liegt längst da.** Beim ersten Lauf traf das auf **21 der 23** offenen Posten
    zu, den ältesten seit dem 28.08. — zwölf Tage.

    **Das ist eine Frage und kein Befund** — dieselbe Unterscheidung wie bei
    :mod:`aiimaging.beruehrung`: *ansehen, nicht falsch.* Eine Antwort kann den Posten
    schliessen, ihn ausdrücklich **nicht** schliessen, oder nur einen Teil betreffen. Was
    davon gilt, sagt keine Zählung — das sagt, wer die Antwort liest. Diese Funktion sagt
    nur, **wo hinzusehen ist**, und dass 21 von 23 dort stehen, ist selbst der Befund: Der
    Einbau-Stand ist gegen die Antworten nie abgeglichen worden.

    Verwandt mit :func:`unverarbeitete_antworten`, eine Ebene höher: Dort ist die Antwort
    nirgends aufgeschrieben, hier ist sie aufgeschrieben und der **Posten** nicht
    nachgezogen. *Ein Posten, der auf etwas wartet, das schon da ist, sieht in jeder
    Zählung aus wie einer, an dem gearbeitet wird.*

    Gemeldet wird nur, wenn **alle** genannten Aufträge beantwortet sind. Steht daneben
    noch einer offen, wartet der Posten zu Recht.

    Returns:
        Je Posten ``{kennung, zustand, auftraege, seit_tagen}``. ``seit_tagen`` zählt ab
        der **jüngsten** Antwort — die frühere kann den Posten nicht geschlossen haben,
        wenn eine spätere noch aussteht.
    """
    wurzel = Path(repo_wurzel)
    seite = blatt or wurzel / "docs" / "EINBAU_STAND.md"
    beantwortet = beantwortete_auftraege(wurzel)
    stichtag = heute or datetime.now(timezone.utc).date()

    wartend = []
    for p in posten(seite):
        if not p["offen"]:
            continue
        ids = AUFTRAGSKENNUNG.findall(p.get("beleg", ""))
        if not ids or not all(i in beantwortet for i in ids):
            continue
        tage = []
        for i in ids:
            satz = _auftrag.lies_ergebnis(i, wurzel) or {}
            wann = str(satz.get("beendet") or "")[:10]
            try:
                tage.append((stichtag - date.fromisoformat(wann)).days)
            except ValueError:
                pass
        wartend.append({"kennung": p["kennung"], "zustand": p["zustand"],
                        "auftraege": sorted(set(ids)),
                        "seit_tagen": min(tage) if tage else None})
    return wartend


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
        # ERGEBNISSE MIT EINEM STATUS, DEN DER VERTRAG NICHT KENNT. Sie zaehlen seit dem
        # 02.09.2026 als offen — und stehen hier, weil «offen» allein nicht sagt, dass
        # jemand etwas mitteilen WOLLTE und dafuer ein eigenes Wort erfunden hat.
        "unbekannter_status": _auftrag.ergebnisse_mit_unbekanntem_status(wurzel),
        # ABGELEGT IST NICHT AUSGELIEFERT. Am 03.09.2026 lagen zwei Auftraege an `ui`
        # seit zwei bzw. einem Tag im Repo und waren nie hinausgegangen — sie zaehlten
        # als Rueckstand beim Adressaten und waren einer beim Absender. Beide Zustaende
        # sahen in dieser Liste vorher gleich aus.
        "unzugestellt": _post.unzugestellt(wurzel),
        # WER UEBER DEM DECKEL LIEGT. Seit dem 07.09.2026 sperrt `schreibe_auftrag`
        # nicht mehr — der Deckel meldet. Gerechnet wird er hier aus dem Rueckstand und
        # nicht beim Schreiben: So gilt er fuer JEDEN offenen Auftrag, auch fuer die von
        # Hand abgelegten, und genau die liefen bisher still vorbei.
        "ueber_deckel": {w: n for w, n in rueckstand(wurzel, heute=heute)["je_worker"].items()
                         if n > _auftrag.DECKEL_JE_WORKER},
        # WAS ALS NAECHSTES FREI IST — die Auskunft, die bisher niemand hatte.
        #
        # Am 09.09.2026 hat eine fremde Lane an einem Abend zweimal `main` rot gemacht:
        # erst mit einem belegten Rang, eine Stunde spaeter mit Rang UND Laufnummer.
        # `tests/test_auftraege.py` VERLANGT eine lueckenlose Reihe je Adressat und sagte
        # niemandem, welche Zahl frei ist. *Eine Vorschrift ohne Vergabestelle verlagert
        # die Arbeit auf den, der zuletzt kommt.*
        #
        # Sie steht hier und nicht nur als Funktion, weil dieses Werkzeug ohnehin gelesen
        # wird, bevor jemand einen Auftrag schreibt — und eine Auskunft, die man kennen
        # muesste, um sie zu finden, findet niemand.
        "vergabe": {
            "laufnummer": _auftrag.naechste_laufnummer(wurzel),
            "raenge": {w: _auftrag.naechster_rang(w, wurzel)
                       for w in (_auftrag.WORKER_LOCAL, _auftrag.WORKER_CLOUD,
                                 _auftrag.WORKER_UI)},
        },
        # ANTWORTEN, DIE NIEMAND AUFGESCHRIEBEN HAT. Der Owner hat am 09.09.2026
        # gefragt, ob alle Aufgaben vom Homeworker erledigt seien — und die Antwort war
        # NEIN: Drei Antworten lagen zwei Tage ungelesen, und alle drei kippten etwas.
        #
        # Der Rueckstand konnte sie nicht melden, denn er zaehlt Auftraege OHNE Antwort.
        # Diese drei hatten eine. *Zwischen «beantwortet» und «gelesen» lag hier kein
        # Zaehler* — und ein beantworteter Auftrag verschwand damit aus jeder Zaehlung,
        # bevor jemand die Antwort gelesen hatte.
        "unverarbeitet": unverarbeitete_antworten(wurzel),
        # POSTEN, DIE AUF ETWAS WARTEN, DAS SCHON DA IST. Siehe
        # `wartet_auf_beantwortetes` — am 09.09.2026 waren es zehn, der aelteste seit
        # vierzehn Tagen.
        "wartet_auf_beantwortetes": wartet_auf_beantwortetes(wurzel, blatt, heute=heute),
        # MESSUNGEN, DEREN BODEN SICH BEWEGT HAT (09.09.2026). Dieselbe Begruendung wie
        # bei der Vergabestelle: Was von Hand gezaehlt wird, wird irgendwann nicht mehr
        # gezaehlt. Der Anlass war der 01.09. — eine eigene Aenderung entwertete sieben
        # veroeffentlichte Dokumente, und acht Tage lang hat es niemand bemerkt.
        #
        # STILL, WENN DIE FRAGE HIER NICHT GESTELLT WERDEN KANN: In einem Probeordner ohne
        # git gibt es keinen Codestand, gegen den sich vergleichen liesse. Dann fehlt der
        # Schluessel ganz, statt eine Null zu melden — eine Null hiesse «nichts beruehrt»,
        # und das waere die falscheste aller Antworten auf «hier ist nichts messbar».
        **_beruehrte_messungen(wurzel),
        "ohne_adressat": verwaist,
        "ohne_geraetebeweis": unbelegt,
        "offene_posten": [p for p in alle if p["offen"]],
        "n_posten": len(alle),
        "bereit": not verwaist and not unbelegt,
    }


__all__ = [
    "AMPELN", "AUFTRAGSKENNUNG", "BELEG_GERAET", "BELEG_REPO", "GERAETEZEICHEN",
    "unverarbeitete_antworten",
    "MESSZEIT", "OFFENE_ZUSTAENDE", "OHNE_ADRESSAT", "ZEILE", "ZUSTAENDE",
    "EinbauError", "beantwortete_auftraege", "bericht", "ohne_adressat",
    "ohne_geraetebeweis", "posten", "rueckstand", "wartet_auf_beantwortetes",
]
