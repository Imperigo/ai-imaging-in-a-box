#!/usr/bin/env python3
"""AUFTRAGSPOST — einen Auftrag als **einen** Block, den man weiterreichen kann.

Die dünne Schicht über :mod:`aiimaging.auftragspost`.

**Wozu es sie gibt** (27.08.2026): Zwei der drei Worker lesen unser Repo — die HomeStation
und der UI-Worker. **Der Cloud-Worker hat es nicht.** Damit liegt jeder
`worker: "cloud"`-Auftrag an einer Stelle, die sein Adressat nicht lesen kann, und der
einzige Bote ist der Owner. Ihm einen Dateipfad zu nennen, hilft nicht; er braucht einen
Text.

*Ein Auftrag, den sein Adressat nicht erreichen kann, ist kein Rückstand bei ihm — er ist
einer bei uns.*

    python tools/auftragspost.py cloud            # alle offenen an den Cloud-Worker
    python tools/auftragspost.py cloud --neueste  # nur den juengsten
    python tools/auftragspost.py --auftrag auf-20260827-63

**Der Rückweg hat seit dem 16.09.2026 einen dritten Zustand** — «gesehen». Die Bibliothek
kann ihn seit demselben Tag eintragen; einen Weg, ihn *ohne von Hand geschriebenes Python*
einzutragen, gab es nicht. Nach Regel 4 ist der Kern die Bibliothek und die Oberfläche die
dünne Schicht darüber — aber *was nur über eine selbst getippte Python-Zeile erreichbar
ist, wird nicht eingetragen*, und ein Vermerk, den niemand einträgt, unterscheidet nichts:

    python tools/auftragspost.py --gesehen auf-70 auf-72 --von ui
    python tools/auftragspost.py --gesehen auf-70 --von cloud --bemerkung "im Chat bestaetigt"
    python tools/auftragspost.py --warum          # die Lage aller offenen, aelteste zuerst
    python tools/auftragspost.py ui --warum       # nur die eines Adressaten

**Je Adressat ein Aufruf.** ``--von`` muss dem Adressaten der genannten Aufträge
entsprechen — die Auswertung liest den Adressaten des *Auftrags*, nicht das ``von`` des
Vermerks, und ein Vermerk unter dem falschen Namen liesse sie den Falschen melden. Er wäre
zudem nicht zurückzunehmen: Der erste Blick zählt, ein zweiter überschreibt ihn nie.

**Und jeder Weg für sich.** Blockversand (``--nach``, ``--vermerken``, ``--auftrag``,
``--neueste``), Blickvermerk (``--gesehen``) und Ansicht (``--warum``) lassen sich nicht
in einem Aufruf mischen; was auf dem gewählten Weg nichts täte, wird abgewiesen statt
stillschweigend übergangen.

Rückgabewert **1**, wenn zum gewählten Adressaten nichts offen ist. Das ist kein Fehler,
aber es soll sich von «hier ist dein Block» unterscheiden lassen, ohne den Text zu lesen.
Derselbe **1** meldet «nichts NEU vermerkt» und «nichts offen zu melden»; **2** ist der
Missgriff — unbekannte Kennung, unbekannter Adressat, ein ``--von``, das nicht dem
Adressaten des Auftrags gehört, ein Schalter ohne Wirkung, unlesbare Ablage.
"""
from __future__ import annotations

import argparse
import json
import sys
import textwrap
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aiimaging import auftrag as _auftrag       # noqa: E402
from aiimaging import auftragspost              # noqa: E402


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("worker", nargs="?", choices=sorted(_auftrag.WORKER),
                   help="Adressat. Ohne ihn ist --auftrag noetig — «alle Blocks auf "
                        "einmal» ist beim Weiterreichen fast nie gemeint.")
    p.add_argument("--auftrag", help="genau diese Kennung, egal ob offen oder beantwortet")
    p.add_argument("--repo", default=".", help="Wurzel des Repos (Vorgabe: hier)")
    p.add_argument("--neueste", action="store_true", help="nur den juengsten Auftrag")
    # DER ZWEITE ZUSTELLWEG HATTE KEINEN VERMERK, und das ist am 10.09.2026 aufgefallen.
    #
    # `--nach` schreibt Einzeldateien in ein FREMDES Verzeichnis und vermerkt die
    # Zustellung. Fuer `ui` und `cloud` laeuft die Zustellung aber ueber **git**: Der Block
    # liegt unter `auftraege/bloecke/`, sie haben unser Repo als Quelle, und
    # `tests/test_auftragsbloecke.py` erzwingt, dass der juengste Block jeden offenen
    # Auftrag nennt. Auf diesem Weg gab es keine Moeglichkeit, den Vermerk zu setzen —
    # `tools/einbau.py` meldete den Auftrag darum dauerhaft als NICHT AUSGELIEFERT, obwohl
    # er hinausgegangen war.
    #
    # Der Ausweg war bisher, `--nach` in ein Verzeichnis im eigenen Repo zu richten. Genau
    # das habe ich am 09.09. getan, und es legte fuenf Dateien an, die den Wortlaut aus
    # `offen/*.json` verdoppeln. *Ein Werkzeug, das man zweckentfremden muss, um eine
    # wahre Angabe zu machen, erzeugt dabei eine zweite Wahrheit.*
    p.add_argument("--vermerken", action="store_true",
                   help="nur die Zustellung vermerken, nichts schreiben — fuer den "
                        "git-Weg, bei dem der Block unter auftraege/bloecke/ liegt. "
                        "Die erste Zustellung zaehlt: ein schon vermerkter Zeitpunkt "
                        "wird nicht ueberschrieben.")
    p.add_argument("--nach", type=Path,
                   help="Blocks als <kennung>.md in dieses Verzeichnis schreiben, statt "
                        "sie zu drucken. Der Pfad wird NICHT im Repo festgeschrieben — "
                        "er zeigt auf ein fremdes Repo, und dessen Aufbau gehoert nicht "
                        "in unser oeffentliches. Ein Ziel IM eigenen Repo wird "
                        "abgewiesen: Dort abzulegen ist keine Zustellung.")
    # ── Der Rueckweg: «gesehen» eintragen und die Lage ansehen (16.09.2026) ───────────
    #
    # DIE BIBLIOTHEKSFUNKTION STAND, DER EINSTIEG FEHLTE — und damit gab es sie praktisch
    # nicht. `vermerke_gesehen` ist die einzige Auskunft dieses Repos, die NICHT aus
    # unserer eigenen Ablage geschlossen ist: dass drueben jemand hingesehen hat. Sie kommt
    # muendlich, per Zustellbeleg oder als Nebensatz in einem Ergebnis — also immer in dem
    # Moment, in dem gerade niemand ein Python-Schnipsel schreibt.
    #
    # *Faustregel der Hausregeln, hier von der anderen Seite: Was nur ueber eine selbst
    # getippte Zeile erreichbar ist, existiert nicht.* Der Vermerk waere nie eingetragen
    # worden, `warum_keine_antwort` haette dauerhaft geraten, und das Raten heisst dort
    # `kein lebenszeichen` — also genau die Lage, in der wir ausdruecklich NICHT mahnen.
    p.add_argument("--gesehen", nargs="+", metavar="KENNUNG",
                   help="vermerken, dass der Adressat diese Auftraege GESEHEN hat. "
                        "Braucht --von. Der erste Blick zaehlt: ein zweiter Vermerk "
                        "ueberschreibt den ersten nicht.")
    # KEIN `choices` HIER, UND DAS IST ABSICHT: Der Waechter gegen den unbekannten
    # Adressaten steht in `auftragspost.vermerke_gesehen`, und er soll die eine Stelle
    # bleiben. Ein zweiter, gleichlautender Waechter im Einstieg saehe aus wie Sorgfalt und
    # waere eine zweite Wahrheit — er koennte auseinanderlaufen, und dann gaelte je nach
    # Weg etwas anderes.
    p.add_argument("--von", metavar="WORKER",
                   help=f"wer hingesehen hat ({', '.join(sorted(_auftrag.WORKER))}). "
                        f"Ohne diese Angabe waere der Vermerk wertlos: «jemand hat es "
                        f"gesehen» beantwortet keine der Fragen, fuer die es ihn gibt.")
    p.add_argument("--bemerkung",
                   help="woher wir es wissen, ein Satz. Ohne Angabe steht dort NICHT "
                        "GEMESSEN — nicht «ohne Anlass».")
    p.add_argument("--warum", "--lage", action="store_true", dest="warum",
                   help="je offenem Auftrag die Lage — aelteste zuerst. Ohne diese "
                        "Ansicht muesste man die JSON-Ablage lesen, um zu sehen, ob ein "
                        "Vermerk gewirkt hat.")
    a = p.parse_args(argv)

    # DIE BEIDEN NEUEN WEGE ZUERST. Sie brauchen weder Adressat noch --auftrag, und die
    # Abfrage darunter wuerde sie sonst mit «Entweder ein Adressat oder --auftrag»
    # abweisen — eine Meldung, die auf etwas zeigt, das gar nicht fehlt.
    if a.gesehen:
        # UND DIE UMKEHRUNG DESSELBEN WAECHTERS, gemessen am 16.09.2026 beim Nachfahren:
        # `--gesehen auf-70 --von ui --nach raus/ --vermerken` trug den Blick ein, legte
        # KEINE Datei an, zog KEINEN Zustellvermerk nach — und meldete «gesehen
        # vermerkt», Rueckgabe 0. Wer das liest, haelt drei Dinge fuer geschehen, von
        # denen eines geschah. *Ein Fehlschlag, der wie ein Erfolg aussieht, wird nicht
        # gefunden; er wird geglaubt.* Die Datei hielt die Regel bisher nur in der einen
        # Richtung (--von ohne --gesehen) — in dieser war sie offen.
        stumm = _stumme_schalter(a, ("warum", "nach", "vermerken", "neueste", "auftrag",
                                     "worker"))
        if stumm:
            print(f"FEHLER: {stumm} wirkt neben --gesehen nicht. Es wurde NICHTS "
                  f"vermerkt und nichts geschrieben — der Adressat des Blicks steht in "
                  f"--von, und Blockversand und Blickvermerk sind zwei Handgriffe.",
                  file=sys.stderr)
            return 2
        return _gesehen(a)

    # EIN SCHALTER OHNE WIRKUNG IST SCHLIMMER ALS KEINER: Er sagt, etwas sei geschehen.
    # Dieselbe Regel, an der am 01.09.2026 `--nach` im `--auftrag`-Zweig aufgefallen ist —
    # hier vorweggenommen, statt sie ein zweites Mal im Gebrauch zu finden.
    if a.von or a.bemerkung:
        print("FEHLER: --von und --bemerkung gehoeren zu --gesehen und wirken sonst "
              "nirgends. Es wurde NICHTS vermerkt.", file=sys.stderr)
        return 2

    if a.warum:
        # Der Positionsadressat fehlt hier mit Absicht: Er FILTERT die Ansicht, wirkt
        # also. Die vier anderen tun neben ihr nichts.
        stumm = _stumme_schalter(a, ("nach", "vermerken", "neueste", "auftrag"))
        if stumm:
            print(f"FEHLER: {stumm} wirkt neben --warum/--lage nicht. Es wurde nichts "
                  f"geschrieben und nichts vermerkt — die Ansicht liest nur.",
                  file=sys.stderr)
            return 2
        return _warum(a)

    if not a.worker and not a.auftrag:
        p.error("Entweder ein Adressat oder --auftrag.")

    if a.auftrag:
        datei = _finde(Path(a.repo), a.auftrag)
        if datei is None:
            print(f"FEHLER: {a.auftrag} liegt weder unter auftraege/offen noch unter "
                  f"auftraege/ergebnisse.", file=sys.stderr)
            return 2
        # `--nach` GILT AUCH HIER, und das war es zuerst nicht: Dieser Zweig kehrte
        # vor der Ablage um und druckte den Block, obwohl ein Zielverzeichnis dastand.
        # Ein Schalter ohne Wirkung ist schlimmer als keiner — er sagt, etwas sei
        # geschehen. Gefunden am 01.09.2026 beim ersten Gebrauch mit --auftrag.
        satz = json.loads(datei.read_text(encoding="utf-8"))
        # DERSELBE ZUSTELLBELEG WIE AUF DEM ANDEREN WEG. Er fehlte hier zuerst, und der
        # erste so verschickte Auftrag kam ohne ihn bei einem Adressaten an, der noch nie
        # geantwortet hat — die Entscheidung lag mitten in `offene_blocks`.
        block = [(a.auftrag, auftragspost.block(
            satz, zustellbeleg=auftragspost.zustellbeleg_fuer(satz, Path(a.repo))))]
        if a.nach:
            for ziel in auftragspost.lege_ab(block, a.nach):
                print(f"geschrieben: {ziel.name}")
            _vermerke(block, a.repo)
            return 0
        if a.vermerken:
            _vermerke(block, a.repo)
            return 0
        print(block[0][1])
        return 0

    blocks = auftragspost.offene_blocks(a.repo, worker=a.worker)
    if not blocks:
        print(f"Nichts offen fuer {a.worker!r}. Es gibt nichts weiterzureichen.")
        return 1
    if a.neueste:
        blocks = blocks[-1:]

    if a.nach:
        if (drin := _zeigt_ins_eigene_repo(a.nach, a.repo)) is not None:
            print(
                f"--nach zeigt in unser EIGENES Repo ({drin}).\n"
                f"\n"
                f"Dort abzulegen ist keine Zustellung. `cloud` liest unser Repo nicht, "
                f"und was hier liegt, hat den Adressaten nicht erreicht — der Vermerk "
                f"waere eine Falschaussage, und zwar genau die, die am 09.09.2026 schon "
                f"einmal fuenf Dateien erzeugt hat.\n"
                f"\n"
                f"Gemeint ist vermutlich einer von zwei Wegen:\n"
                f"  --nach <pfad-im-fremden-repo>   der Block geht wirklich hinaus\n"
                f"  --vermerken                     der Block liegt unter "
                f"auftraege/bloecke/ und ist ueber git hinausgegangen",
                file=sys.stderr)
            return 2
        for ziel in auftragspost.lege_ab(blocks, a.nach):
            print(f"geschrieben: {ziel.name}")
        _vermerke(blocks, a.repo)
        return 0

    if a.vermerken:
        # NICHTS SCHREIBEN, NUR VERMERKEN. Der Block liegt schon unter
        # `auftraege/bloecke/` und geht ueber git hinaus; hier wird nur nachgezogen, was
        # dort bereits passiert ist.
        _vermerke(blocks, a.repo)
        return 0

    for i, (kennung, text) in enumerate(blocks):
        if i:
            print("\n")
        print(text)
    return 0


#: Wie ein Schalter in der Meldung heisst. Der Positionsadressat hat keinen Strichnamen,
#: und «worker wirkt nicht» waere fuer den Leser keine Auskunft.
def _zeigt_ins_eigene_repo(nach: Path, repo) -> str | None:
    """Liegt ``--nach`` innerhalb unseres eigenen Repos? Dann ist es keine Zustellung.

    **BEFUND 19.09.2026, und es ist derselbe Fehler zum zweiten Mal.** Am 09.09.2026 ist
    `--nach` schon einmal auf ein Verzeichnis im eigenen Repo gerichtet worden; der
    Kommentar an `--vermerken` erzaehlt es seither. Am 19.09. habe ich es wieder getan —
    `--nach auftraege/bloecke` — und damit acht Auftraege als ZUGESTELLT vermerkt, die
    nirgendwo hingegangen sind. Darunter der aelteste offene Posten des Projekts.

        Ein Kommentar ist kein Waechter.

    `cloud` liest unser Repo **nicht** (siehe :data:`auftragspost.RUECKWEG`). Eine Datei,
    die hier liegt, hat den Adressaten nicht erreicht — und ein Zustellvermerk darauf ist
    keine halbe Wahrheit, sondern eine falsche: Die Lage «nicht zugestellt» ist die
    einzige, in der eine ausbleibende Antwort UNSER Versaeumnis ist und nicht seins. Sie
    zuzudecken heisst, den eigenen Rueckstand dem Adressaten anzuhaengen.

    Returns:
        Den Pfad als Text, wenn er im Repo liegt — sonst ``None``. **Nicht** ``False``:
        Hier wird eine Lage gemeldet und kein Urteil gefaellt.

    Geprueft wird ueber aufgeloeste Pfade, damit `..` und Verknuepfungen nicht
    daran vorbeifuehren. Laesst sich ein Pfad nicht aufloesen, gilt er als
    ``None`` — ein Ziel, das es noch nicht gibt, liegt in aller Regel draussen,
    und ein Werkzeug, das am haeufigsten Fall scheitert, wird umgangen.
    """
    try:
        ziel = Path(nach).resolve()
        wurzel = Path(repo).resolve()
    except OSError:
        return None
    return str(ziel) if ziel == wurzel or wurzel in ziel.parents else None


_SCHALTERNAME = {"warum": "--warum/--lage", "nach": "--nach", "vermerken": "--vermerken",
                 "neueste": "--neueste", "auftrag": "--auftrag",
                 "worker": "der Adressat als Positionsangabe"}


def _stumme_schalter(a, namen) -> str:
    """Welche dieser Schalter gesetzt sind, aber auf dem gewaehlten Weg nichts tun.

    Returns:
        Die Namen als ein Satzstueck, oder ``""`` — **leer heisst: keiner gesetzt**, nicht
        «geprueft und in Ordnung». Der Aufrufer entscheidet, was er daraus macht.
    """
    gesetzt = [_SCHALTERNAME[n] for n in namen if getattr(a, n)]
    return ", ".join(gesetzt)


def _gesehen(a) -> int:
    """``--gesehen`` — einen bestaetigten Blick eintragen.

    Rueckgabe wie im Rest der Datei: ``0`` es wurde etwas Neues vermerkt, ``1`` es gab
    nichts Neues zu vermerken (kein Fehler, aber unterscheidbar), ``2`` Missgriff.

    **Die Reihenfolge ist der Waechter:** erst jede Kennung gegen die wirklich vorhandenen
    Auftraege pruefen, dann schreiben. Andersherum bliebe nach einem Tippfehler eine halbe
    Ablage stehen — und eine halbe Ablage sieht ordentlich aus.
    """
    wurzel = Path(a.repo)

    if not a.von:
        # OHNE ADRESSAT IST DER VERMERK WERTLOS, und wertlos ist hier schlimmer als
        # fehlend: Er stuende in der Ablage, `warum_keine_antwort` zaehlte ihn als
        # bestaetigten Blick, und niemand koennte sagen, WESSEN Blick.
        print("FEHLER: --gesehen braucht --von <worker> "
              f"({', '.join(sorted(_auftrag.WORKER))}). «Jemand hat es gesehen» "
              "beantwortet keine der Fragen, fuer die es diesen Vermerk gibt. Es wurde "
              "NICHTS vermerkt.", file=sys.stderr)
        return 2

    # EINE KENNUNG, DIE ES NICHT GIBT, WIRD ABGEWIESEN — und zwar VOR dem Schreiben.
    #
    # Ein Tippfehler legt sonst einen Vermerk fuer einen Auftrag an, den es nicht gibt.
    # Der Vermerk wirkt nie: `warum_keine_antwort` schlaegt seine Kennungen in
    # `auftraege/offen/` nach und findet diese nicht. Der ECHTE Auftrag bleibt derweil in
    # seiner Vermutungslage stehen — `kein lebenszeichen` —, waehrend die Ablage aussieht,
    # als sei fleissig bestaetigt worden. *Ein Fehlschlag, der wie ein Erfolg aussieht,
    # wird nicht gefunden; er wird geglaubt* (die fuenfte Regel, und derselbe Schaden wie
    # bei der zerlegten Zeichenkette am 16.09.2026).
    unbekannt = [k for k in a.gesehen if _finde(wurzel, k) is None]
    if unbekannt:
        print(f"FEHLER: {len(unbekannt)} Kennung(en) gibt es hier nicht: "
              f"{', '.join(unbekannt)}.\n"
              f"Gesucht wurde in auftraege/offen und auftraege/ergebnisse. Es wurde "
              f"NICHTS vermerkt — auch die uebrigen Kennungen nicht: Ein Vermerk auf einen "
              f"Auftrag, den es nicht gibt, wirkt nie, und die Ablage sieht danach "
              f"trotzdem ordentlich aus.", file=sys.stderr)
        return 2

    try:
        # DER BIBLIOTHEKSWAECHTER GEGEN DEN UNBEKANNTEN ADRESSATEN ZUERST, und zwar mit
        # LEERER Folge: Er prueft `von` und schreibt dabei nichts (keine neue Kennung,
        # also keine Ablage). So behaelt er seine Stimme — und der Waechter darunter darf
        # sich darauf verlassen, dass `von` ueberhaupt ein Adressat IST, ohne die Liste
        # der Adressaten ein zweites Mal zu fuehren.
        #
        # Ohne diesen Vorlauf sagte ein Tippfehler in `--von` nicht mehr «kein bekannter
        # Adressat», sondern «--von ist 'cloudd', aber auf-… gehoert cloud» — wahr und
        # irrefuehrend zugleich, weil es auf die Kennung zeigt statt auf den Tippfehler.
        auftragspost.vermerke_gesehen(wurzel, [], von=a.von)

        # DER BLICK GEHOERT DEM ADRESSATEN DES AUFTRAGS — sonst behauptet die Ansicht
        # etwas anderes als die Ablage. Gemessen am 16.09.2026: `--gesehen auf-02 --von
        # cloud` auf einem ui-Auftrag schrieb `"von": "cloud"` und liess
        # `warum_keine_antwort` melden «ui hat ihn gesehen». Die Auswertung liest den
        # Adressaten des AUFTRAGS und nicht das `von` des Vermerks; die beiden koennen
        # gegeneinander stehen, und die Anzeige nennt dann den Falschen.
        #
        # Und der Eintrag ist nicht zurueckzunehmen: Der erste Blick zaehlt, ein zweiter
        # ueberschreibt ihn nie — ein falsches `--von` legt eine dauerhafte Unwahrheit ab,
        # die nur von Hand aus der JSON-Datei zu entfernen ist.
        #
        # Das ist KEIN zweiter Waechter gegen den unbekannten Adressaten: Er prueft etwas,
        # das die Bibliothek gar nicht prueft, und er kann es nur hier — der Adressat
        # steht in der Auftragsdatei, und die liegt neben dem Einstieg.
        fremd = []
        for kennung in a.gesehen:
            satz = _lies(wurzel, kennung)
            # UNLESBARE AUFTRAGSDATEI HEISST NICHT GEMESSEN und ist darum kein Befund:
            # Wir wissen dann nicht, wem der Auftrag gehoert, und «wir wissen es nicht»
            # ist kein Widerspruch.
            adressat = (satz or {}).get("worker")
            if adressat and adressat != a.von:
                fremd.append(f"{kennung} gehoert {adressat}")
        if fremd:
            print(f"FEHLER: --von ist {a.von!r}, aber {'; '.join(fremd)}. Es wurde NICHTS "
                  f"vermerkt.\nDie Auswertung liest den Adressaten des AUFTRAGS und nicht "
                  f"das «von» des Vermerks — sie wuerde also den Falschen als den melden, "
                  f"der hingesehen hat. Und der Eintrag waere nicht zurueckzunehmen: Der "
                  f"erste Blick zaehlt, ein zweiter ueberschreibt ihn nie. Bitte je "
                  f"Adressat ein Aufruf.", file=sys.stderr)
            return 2

        # VORHER LESEN, UM «SCHON VERMERKT» SAGEN ZU KOENNEN. `vermerke_gesehen` meldet
        # nur die ZAHL der neuen; welche Kennung stumm blieb, weiss danach niemand mehr.
        vorher = auftragspost.gesehen_vermerke(wurzel)
        neu = auftragspost.vermerke_gesehen(wurzel, a.gesehen, von=a.von,
                                            bemerkung=a.bemerkung)
    except auftragspost.PostError as fehler:
        # EIN MISSGRIFF DES BENUTZERS IST KEIN ABSTURZ, SONDERN EINE MELDUNG. Hier landet
        # vor allem der unbekannte Adressat — der Waechter dafuer steht in der Bibliothek,
        # und diese Zeile ist seine Stimme im Einstieg.
        print(f"FEHLER: {fehler}", file=sys.stderr)
        return 2

    print(f"gesehen vermerkt: {neu} von {len(a.gesehen)} Kennung(en) NEU, von {a.von!r}.")

    schon = [k for k in a.gesehen if k in vorher]
    if schon:
        # DAS GEHOERT DEM BENUTZER GESAGT, SONST HAELT ER ES FUER EINEN FEHLSCHLAG.
        # «0 neu» ohne Erklaerung sieht aus, als haette das Werkzeug nichts getan; es hat
        # aber genau das Richtige getan.
        print("schon vermerkt, NICHT ueberschrieben — der erste Blick ist der, der "
              "zaehlt; ein zweiter Eintrag mit heutigem Datum liesse den Auftrag jedes "
              "Mal wieder jung aussehen. Das ist Absicht und kein Fehlschlag:")
        for kennung in schon:
            eintrag = vorher[kennung]
            if not isinstance(eintrag, dict):
                # EIN VON HAND EINGETRAGENER ZEITSTEMPEL statt des Woerterbuchs — dieselbe
                # Milde wie in `warum_keine_antwort`: Die Kennung steht da, und das ist
                # die Aussage.
                eintrag = {"am": eintrag, "von": None}
            am = str(eintrag.get("am") or "")[:10] or "unbekannt"
            von = eintrag.get("von") or "unbekannt"
            print(f"  * {kennung} — gesehen am {am}, von {von}")

    # `1` HEISST HIER «NICHTS NEU», wie `1` beim Postlauf «nichts offen» heisst: kein
    # Fehler, aber ohne den Text lesen zu muessen von «eingetragen» unterscheidbar.
    return 0 if neu else 1


def _warum(a) -> int:
    """``--warum`` / ``--lage`` — je offenem Auftrag, warum die Antwort fehlt.

    **Ohne diese Ansicht muesste man die JSON-Ablage lesen**, um zu sehen, ob ein Vermerk
    gewirkt hat — und wer die Ablage liest, liest sie irgendwann statt der Auswertung.
    """
    wurzel = Path(a.repo)
    try:
        befunde = auftragspost.warum_keine_antwort(wurzel)
    except auftragspost.PostError as fehler:
        # EINE UNLESBARE `gesehen.json` REISST DIE AUSWERTUNG AB — mit Absicht, siehe
        # `gesehen_vermerke`. Hier wird daraus eine Meldung und kein Stapelauszug.
        print(f"FEHLER: {fehler}", file=sys.stderr)
        return 2

    if a.worker:
        befunde = [b for b in befunde if b.get("worker") == a.worker]
    if not befunde:
        wem = f" fuer {a.worker!r}" if a.worker else ""
        print(f"Nichts offen{wem}. Es gibt keine Lage zu melden.")
        return 1

    for befund in befunde:
        tage = befund.get("tage")
        # DIE DRITTE ANTWORT: Ein unlesbares Erstelldatum heisst NICHT GEMESSEN und
        # niemals `0 Tage`. Eine Null hier waere die bequemste Luege der ganzen Ansicht —
        # sie liesse den Auftrag von heute sein.
        alter = f"{tage} Tage" if isinstance(tage, int) else "? Tage (Datum unlesbar)"
        print(f"{str(befund.get('auftrag_id')):<24} {str(befund.get('worker')):<6} "
              f"{alter:<24} {befund.get('lage')}")
        print(textwrap.fill(str(befund.get("grund") or ""), width=auftragspost.BREITE,
                            initial_indent="    ", subsequent_indent="    "))

    # DIE ZAEHLUNG JE LAGE, in der Reihenfolge von `LAGEN` — sie geht von «unser Fehler»
    # zu «wir wissen es nicht», und in derselben Reihenfolge ist zu handeln.
    print()
    zaehlung = [(lage, sum(1 for b in befunde if b.get("lage") == lage))
                for lage in auftragspost.LAGEN]
    zeile = ", ".join(f"{n}x {lage}" for lage, n in zaehlung if n)
    print(f"{len(befunde)} offen: {zeile}")
    return 0


def _vermerke(blocks, repo) -> None:
    """Den Zustellvermerk nachziehen — **nur nach dem Schreiben, nie davor**.

    Die Reihenfolge ist der ganze Punkt: Ein Vermerk vor dem Schreiben behauptet eine
    Auslieferung, die ein Fehler beim Schreiben gerade verhindert hat. Dann stünde ein
    Auftrag als zugestellt da, der nie hinausging — genau der Zustand, gegen den es
    diesen Vermerk gibt, nur mit einer Zeile mehr Beweis dafür, dass alles stimmt.

    Nur Adressaten aus :data:`aiimaging.auftragspost.ZUSTELLUNG_NOETIG` werden
    vermerkt; `local` liest das Repo selbst und braucht keine Post.
    """
    kennungen = []
    for kennung, _text in blocks:
        satz = _lies(Path(repo), kennung)
        if satz and satz.get("worker") in auftragspost.ZUSTELLUNG_NOETIG:
            kennungen.append(kennung)
    if kennungen:
        # NEU UND SCHON VERMERKT GETRENNT ZAEHLEN (Befund 22.09.2026). Bis dahin stand
        # hier «5 Kennung(en) nachgezogen», obwohl nur eine neu war — und die vier anderen
        # hatten dabei ihren ersten Zeitpunkt verloren. Die Bibliothek laesst ihn seither
        # stehen; diese Zeile sagt es, damit «0 neu» nicht wie ein Fehlschlag aussieht.
        verschieden = list(dict.fromkeys(kennungen))
        neu = auftragspost.vermerke_zustellung(repo, verschieden)
        schon = len(verschieden) - neu
        print(f"zustellvermerk: {neu} Kennung(en) NEU vermerkt, {schon} schon vermerkt")
        if schon:
            print("  schon vermerkte behalten ihren Zeitpunkt — die erste Zustellung "
                  "zaehlt, ein zweiter Vermerk ueberschreibt sie nicht.")


def _lies(wurzel: Path, kennung: str) -> dict | None:
    pfad = _finde(wurzel, kennung)
    if pfad is None:
        return None
    try:
        return json.loads(pfad.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _finde(wurzel: Path, kennung: str) -> Path | None:
    for ordner in ("offen", "ergebnisse"):
        pfad = wurzel / "auftraege" / ordner / f"{kennung}.json"
        if pfad.exists():
            return pfad
    return None


if __name__ == "__main__":                                   # pragma: no cover
    raise SystemExit(main())
