"""Ein Auftrag als **ein** Block, den man weiterreichen kann.

Warum es dieses Modul gibt
--------------------------
Zwei der drei Worker lesen unser Repo: die HomeStation und der UI-Worker. Ein Auftrag
erreicht sie über ``git pull``.

**Der Cloud-Worker hat unser Repo nicht.** Er hält den Vertrag und die Warteschlange von
KosmoOrbit; unser Ablageort ist für ihn nicht erreichbar. Damit liegt jeder
``worker: "cloud"``-Auftrag an einer Stelle, die sein Adressat nicht lesen kann — und der
einzige Bote ist der Owner.

``auftraege/README.md`` verlangt seit dem 18.08.2026, dass jeder Auftrag mit einem
**kopierbaren Prompt** kommt: *«Die Auftragsdatei ist die Hälfte. Die andere ist der Text,
den der Owner ohne Nachdenken weiterreichen kann — fertig formuliert, in einem Block.»*
Geschrieben hat den bisher niemand, und für die HomeStation fiel es nicht auf, weil sie
die Datei ohnehin sieht.

*Ein Auftrag, den sein Adressat nicht erreichen kann, ist kein Rückstand bei ihm. Er ist
einer bei uns.*

Was der Block enthält — und was nicht
--------------------------------------
Er ist **selbsttragend**: Wer ihn liest, braucht das Repo nicht. Beschreibung, Anweisung
im Volltext, Auflagen und die Rückgabefragen stehen darin, weil ein Auftrag, der auf
etwas verweist, das der Empfänger erst suchen muss, ein halber Auftrag ist.

**Nicht** enthalten ist irgendein Pfad aus dieser Umgebung. Regel 3 gilt für den Block wie
für die Datei, und :func:`aiimaging.auftrag.pruefe_auftrag` hat das schon geprüft, bevor
die Datei geschrieben wurde — hier wird es ein zweites Mal geprüft, weil der Block **das
Repo verlässt** und die Datei nicht.
"""

from __future__ import annotations

import json
import os
import tempfile
from collections.abc import Sequence
from datetime import date, datetime, timezone
from pathlib import Path

from aiimaging import auftrag as _auftrag

#: Wie breit der Block umbrochen wird. Er landet in fremden Eingabefeldern, und dort ist
#: eine feste Breite freundlicher als eine, die vom Fenster abhängt.
BREITE = 88

#: Was je Worker über den Rückweg zu sagen ist. **Der Rückweg gehört in den Block**: Ein
#: Auftrag ohne Rückweg erzeugt eine Antwort, die niemand findet.
RUECKWEG = {
    "local": ("Antwort als `auftraege/ergebnisse/{kennung}.json` ins Repo, committen und "
              "pushen. Der Auftrag gilt als unerledigt, solange diese Datei fehlt."),
    "ui": ("Antwort als `auftraege/ergebnisse/{kennung}.json` ins Repo, committen und "
           "pushen — ihr habt unser Repo als Quelle."),
    "cloud": ("Antwort als Text zurück an den Owner. **Ihr habt unser Repo nicht**, also "
              "gibt es keinen Dateiweg; die Antwort wird von uns als "
              "`auftraege/ergebnisse/{kennung}.json` abgelegt."),
}

#: Der **Zustellbeleg** — nur für Adressaten, von denen noch nie eine Antwort kam.
#:
#: Gemessen am 01.09.2026: `ui` hat auf vier Aufträge in sieben Tagen **nie** geantwortet,
#: `cloud` auf sieben in zehn Tagen ebenfalls nie — die beiden Ergebnisse dort sind
#: Weiterleitungsvermerke der HomeStation und keine Antworten des Adressaten.
#:
#: **Damit ist zweierlei möglich, und die beiden verlangen Gegenteiliges:** Entweder liegt
#: die Frage quer und braucht Zeit — dann warten wir. Oder niemand sieht in das
#: Verzeichnis, und dann ist es *kein Rückstand bei ihnen, sondern einer beim Absender*,
#: und weitere Aufträge dorthin sind verlorene Arbeit. Aus dem Schweigen allein ist das
#: nicht zu unterscheiden; beides sieht gleich aus.
#:
#: Der Beleg trennt sie. Er verlangt **keine inhaltliche Antwort** — nur einen Satz mit
#: Datum. Wer die Frage nicht beantworten kann, kann trotzdem bestätigen, dass er sie
#: gelesen hat, und dann wissen wir, worauf wir warten.
#:
#: *Er steht hier und nicht in den elf Dateien: Elf Dateien sind elf Gelegenheiten, ihn
#: bei einer zu vergessen — und die zwölfte hätte ihn gar nicht.*
ZUSTELLBELEG = (
    "**ZUERST, UND VOR DER INHALTLICHEN ANTWORT:** Bitte ein Satz zurück, dass diese "
    "Datei bei euch angekommen ist, mit Datum. Mehr nicht — keine Messung, keine "
    "Zusage, kein Termin. Grund: Auf {n_offen} Auftraege an euch ist bis heute "
    "({stand}) keine Antwort gekommen, und wir koennen von hier aus nicht "
    "unterscheiden, ob die Fragen bei euch querliegen oder ob niemand in dieses "
    "Verzeichnis sieht. Das Erste waere Warten, das Zweite waere ein Fehler bei UNS — "
    "und wir wuerden weiter Auftraege an eine Stelle legen, die keiner liest. "
    "Ein Satz von euch entscheidet das."
)

def zustellbeleg_stand(heute: date | None = None) -> str:
    """Der Stichtag im :data:`ZUSTELLBELEG` — **gerechnet, nicht gepflegt**.

    **Warum das keine Vorgabe mehr ist, und der Beleg dafür ist dieser Wert selbst.**
    Bis zum 06.09.2026 stand hier ein Datum als Konstante, mit einem Kommentar daneben:
    *«wer die Post neu erzeugt, zieht darum dieses Datum mit»*. Am 03.09. wurde es
    nachgezogen, weil es zwei Tage alt geworden war. Am 06.09. ging die Post erneut
    hinaus — und trug wieder das Datum vom 03.

    *Ein Kommentar, der einen Menschen an etwas erinnert, ist kein Wächter.* Er ist beim
    ersten Mal gelesen worden, beim zweiten Mal von derselben Hand übergangen und hätte
    beim dritten Mal genauso versagt. Die Zahl daneben (``n_offen``) war jedes Mal
    richtig, weil sie **gezählt** wurde.

    Der Stichtag ist jetzt der Tag, an dem der Block entsteht. Damit kann er nicht mehr
    hinter der Zählung zurückbleiben, neben der er steht.

    Args:
        heute: Für Proben einsetzbar. Ohne Angabe der heutige Tag.
    """
    return (heute or date.today()).strftime("%d.%m.%Y")


class PostError(ValueError):
    """Der Auftrag lässt sich nicht als Block ausgeben."""


def _umbruch(text: str, breite: int = BREITE) -> str:
    """Zeilen umbrechen — **ohne** eingerückte oder tabellarische Zeilen anzutasten.

    Die Anweisungen tragen Messwerttabellen und Befehlszeilen. Ein Umbruch mitten in einer
    Tabellenzeile macht sie unlesbar, und unlesbar heisst hier: wird nicht gelesen.
    """
    aus: list[str] = []
    for zeile in text.splitlines():
        if len(zeile) <= breite or zeile[:1] in (" ", "\t", "|"):
            aus.append(zeile)
            continue
        rest, gebaut = zeile, ""
        for wort in rest.split(" "):
            if gebaut and len(gebaut) + 1 + len(wort) > breite:
                aus.append(gebaut)
                gebaut = wort
            else:
                gebaut = f"{gebaut} {wort}".strip()
        aus.append(gebaut)
    return "\n".join(aus)


def _punkt(text: str, zeichen: str = "  * ") -> str:
    """Ein Aufzählungspunkt mit hängendem Einzug.

    **Warum nicht einfach :func:`_umbruch`:** Der lässt eingerückte Zeilen in Ruhe, weil
    Tabellen und Befehlszeilen sonst zerbrechen — und ein Punkt beginnt mit Einzug. Er
    käme also ungebrochen durch, und die Rückgabefragen sind die längsten Zeilen des
    ganzen Blocks.
    """
    breite = BREITE - len(zeichen)
    worte, zeilen, gebaut = text.split(" "), [], ""
    for wort in worte:
        if gebaut and len(gebaut) + 1 + len(wort) > breite:
            zeilen.append(gebaut)
            gebaut = wort
        else:
            gebaut = f"{gebaut} {wort}".strip()
    zeilen.append(gebaut)
    einzug = " " * len(zeichen)
    return "\n".join((zeichen if i == 0 else einzug) + z for i, z in enumerate(zeilen))


def block(satz: dict, *, zustellbeleg: int = 0) -> str:
    """Der Auftrag als ein Text, den der Owner ohne Nachdenken weiterreichen kann.

    Args:
        satz: Ein Auftrag, wie ihn :func:`aiimaging.auftrag.schreibe_auftrag` ablegt.
        zustellbeleg: Zahl der offenen Aufträge bei diesem Adressaten. **Ab 1 wird
            :data:`ZUSTELLBELEG` angehängt**, sonst nicht. Null heisst: Dieser Adressat
            hat schon einmal geantwortet, wir wissen also, dass er liest — dann wäre die
            Bitte eine Dauerwarnung, und die verdeckt die echten.

    Raises:
        PostError: Der Auftrag ist unvollständig, oder er trägt einen Pfad aus dieser
            Umgebung. **Der Block verlässt das Repo** — was hier durchrutscht, ist
            draussen.
    """
    maengel = _auftrag.pruefe_auftrag(satz)
    if maengel:
        raise PostError(
            f"Der Auftrag ist nicht vollständig und darf so nicht hinausgehen: "
            f"{'; '.join(maengel)}")

    kennung = satz["auftrag_id"]
    worker = satz["worker"]

    # OHNE RUECKGABE GEHT KEIN BLOCK HINAUS, und das ist strenger als
    # `auftrag.pruefe_auftrag` — dort ist `rueckgabe` kein Pflichtfeld.
    #
    # Der Unterschied hat einen Grund: Die Datei kann man nachbessern, solange sie im
    # Repo liegt. Der Block ist das, was der Empfaenger LIEST, und ein Auftrag, der nicht
    # sagt, woran man erkennt, dass er beantwortet ist, erzeugt drueben Arbeit und hier
    # keine Antwort. Genau dieser Mangel steckte am 27.08.2026 in `auf-20260827-63`.
    if not (satz.get("rueckgabe") or []):
        raise PostError(
            f"{kennung} sagt nicht, was zurueckkommen soll. Ein Block ohne Rueckgabe ist "
            f"eine Mitteilung, kein Auftrag — der Empfaenger kann nicht erkennen, wann er "
            f"fertig ist.")
    anweisung = str(satz.get("anweisung") or "").strip()
    beschreibung = str(satz.get("beschreibung") or "").strip()

    # AUFTRAEGE VOR DEM 26.08.2026 HABEN KEIN `anweisung`-FELD — ihre ganze Anweisung
    # steckt in `beschreibung`. Sie deshalb nicht ausgeben zu koennen, waere die
    # Buchstabentreue, die den aeltesten Posten des Rueckstands unzustellbar macht.
    # Fehlt `anweisung`, ist `beschreibung` alles, was es gibt — dann ist sie die
    # Anweisung, und sie steht nicht zweimal da.
    if not anweisung:
        anweisung, beschreibung = beschreibung, ""
    if not anweisung:
        raise PostError(
            f"{kennung} trägt weder Anweisung noch Beschreibung. Ein Block ohne sie wäre "
            f"ein Verweis auf eine Datei, die der Empfänger nicht hat — genau das, was "
            f"die Hausregel seit dem 22.08.2026 verbietet.")

    teile = [
        f"AUFTRAG {kennung}  ·  an: {worker}",
        "=" * BREITE,
        "",
    ]
    if beschreibung:
        teile += [_umbruch(beschreibung), ""]
    teile += [
        anweisung,
        "",
        "-" * BREITE,
        "AUFLAGEN",
    ]
    # UEBER `auflagen` UND `rueckgabe` WIRD NICHT MEHR ROH GEZAEHLT.
    #
    # Beide Felder tragen zwei Formen: ein Woerterbuch in den aelteren Auftraegen, eine
    # Liste von Saetzen in den neueren. Ueber ein Woerterbuch zu zaehlen ergibt die
    # SCHLUESSELNAMEN — `leistungsgrenze_w`, `verzeichnis`, `nur_zahlen` —, und die Werte
    # verschwanden lautlos. Fuenf offene Auftraege gingen so hinaus, drei davon an die
    # beiden Adressaten, die noch nie geantwortet haben.
    for auflage in _auftrag.auflagen_text(satz):
        teile.append(_punkt(str(auflage)))
    teile += ["", "WAS ZURUECKKOMMEN SOLL"]
    punkte = _auftrag.rueckgabepunkte(satz)
    for frage in punkte:
        teile.append(_punkt(str(frage)))
    if not punkte:
        # DIE FORM WAR DA, DER INHALT NICHT — und der Wachter oben hat sie durchgelassen,
        # weil ein Woerterbuch mit drei Transportschluesseln wahr ist.
        #
        # Nicht abweisen: Buchstabentreue, die den aeltesten Posten des Rueckstands
        # unzustellbar macht, ist derselbe Fehler wie eine fehlende Anweisung stumm
        # durchzulassen. Aber sichtbar sagen, was fehlt.
        teile.append(_punkt(
            "Dieser Auftrag nennt keine EINZELNEN Rueckgabepunkte — er traegt nur die "
            "Transportangabe (wohin, nur Zahlen). Was zurueckkommen soll, steht in der "
            "Anweisung oben. Wenn etwas unklar bleibt, fragt lieber nach, statt zu "
            "raten: Das ist ein Mangel bei uns und keiner bei euch."))

    rueckweg = RUECKWEG.get(worker)
    if rueckweg:
        teile += ["", "RUECKWEG", _punkt(rueckweg.format(kennung=kennung), "  ")]
    if zustellbeleg:
        teile += ["", "ZUSTELLBELEG",
                  _punkt(ZUSTELLBELEG.format(n_offen=zustellbeleg,
                                             stand=zustellbeleg_stand()), "  ")]
    teile += ["", "=" * BREITE]

    text, ersetzt = _auftrag.ohne_kennungen("\n".join(teile))
    if ersetzt:
        # ERSETZEN STATT ABLEHNEN — dieselbe Entscheidung wie in `auftrag.ohne_kennungen`,
        # und aus demselben Grund: Einen Auftrag zurueckzuweisen, weil ein Benutzername
        # darin steckt, hiesse, ihn gar nicht zu verschicken.
        #
        # ABER NICHT STILL. Die Datei vermerkt die Zahl der Ersetzungen; der Block hat
        # kein Feld dafuer, also steht sie sichtbar darin. Und eine Ersetzung ist hier
        # ueberhaupt ein Befund: `schreibe_auftrag` hat schon geputzt, als die Datei
        # entstand — was hier noch auftaucht, ist auf einem anderen Weg hereingekommen.
        text += (f"\n(Hinweis: {ersetzt} Pfadangabe(n) aus der Entwicklungsumgebung "
                 f"wurden durch «{_auftrag.NUTZER_ERSATZ}» ersetzt — Regel 3. Dass hier "
                 f"ueberhaupt etwas zu ersetzen war, ist ungewoehnlich: Die Auftragsdatei "
                 f"wird beim Schreiben schon geputzt.)\n")
    return text


def zustellbeleg_fuer(satz: dict, repo_wurzel) -> int:
    """Braucht dieser Auftrag einen Zustellbeleg? — die Zahl der offenen bei seinem
    Adressaten, oder ``0``.

    **Warum die Entscheidung hier steht und nicht beim Aufrufer.** Sie hängt an einer
    Tatsache über den Adressaten — *hat er je geantwortet?* —, und die kennt kein Aufrufer
    besser als diese Funktion. Sie stand am 01.09.2026 zuerst mitten in
    :func:`offene_blocks`, und der zweite Weg — ``tools/auftragspost.py --auftrag`` —
    ging daran vorbei: Der erste so verschickte Auftrag desselben Abends kam **ohne**
    Beleg bei einem Adressaten an, der noch nie geantwortet hatte.

    *Dieselbe Sorte Fehler, die dieser Tag schon zweimal gefunden hat: Die Entscheidung
    lag auf einem Weg, und der andere liess sie stillschweigend weg.*
    """
    wurzel = Path(repo_wurzel)
    if satz.get("worker") not in set(_auftrag.nie_geantwortet(wurzel)):
        return 0
    return sum(1 for a in _auftrag.unerledigt(wurzel)
               if a.get("worker") == satz.get("worker"))


def offene_blocks(repo_wurzel, *, worker: str | None = None) -> list[tuple[str, str]]:
    """Alle unbeantworteten Aufträge als Blöcke, älteste zuerst.

    Args:
        worker: Nur diesen Adressaten. Ohne Angabe alle — was beim Weiterreichen selten
            gemeint ist, weshalb `tools/auftragspost.py` die Angabe verlangt.

    Returns:
        Je Auftrag ``(kennung, block)``.

    **Der Zustellbeleg wird hier entschieden und nicht vom Aufrufer.** Er hängt an einer
    Tatsache über den Adressaten — *hat er je geantwortet?* —, und die kennt der Aufrufer
    nicht besser als diese Funktion. Ein Aufrufer, der ihn setzen müsste, würde ihn
    irgendwann vergessen; der schweigende Adressat bekäme dann wieder eine Datei ohne
    Rückfrage, und wir stünden vor demselben ununterscheidbaren Schweigen wie vorher.
    """
    wurzel = Path(repo_wurzel)
    offene = _auftrag.unerledigt(wurzel)

    aus = []
    for satz in offene:
        if worker and satz.get("worker") != worker:
            continue
        kennung = satz.get("auftrag_id") or "(ohne Kennung)"
        try:
            aus.append((kennung, block(satz,
                                       zustellbeleg=zustellbeleg_fuer(satz, wurzel))))
        except PostError as fehler:
            # EIN UNZUSTELLBARER AUFTRAG DARF DIE UEBRIGEN NICHT VERDECKEN. Er wird als
            # eigener Block gemeldet, nicht uebersprungen: Ein still weggelassener
            # Auftrag sieht hinterher aus wie keiner.
            aus.append((kennung, f"AUFTRAG {kennung}  ·  NICHT ZUSTELLBAR\n"
                                 + "=" * BREITE + f"\n\n{fehler}\n"))
    aus.sort(key=lambda p: p[0])
    return aus


def lege_ab(blocks: Sequence[tuple[str, str]], verzeichnis) -> list[Path]:
    """Die Blöcke als ``<kennung>.md`` ablegen — dort, wo der Adressat hinsieht.

    Args:
        verzeichnis: Zielordner. **Der Pfad wird nirgends im Repo festgeschrieben** — er
            zeigt in ein fremdes Repo, und dessen Aufbau gehört nicht in ein öffentliches.

    Returns:
        Die geschriebenen Pfade, in derselben Reihenfolge.

    *Die Dateien werden bei jedem Lauf überschrieben. Wer in ihnen antwortet, verliert die
    Antwort — deshalb steht das in der Erklärung, die neben ihnen liegt.*
    """
    ordner = Path(verzeichnis)
    ordner.mkdir(parents=True, exist_ok=True)
    aus = []
    for kennung, text in blocks:
        ziel = ordner / f"{kennung}.md"
        ziel.write_text(text + "\n", encoding="utf-8")
        aus.append(ziel)
    return aus


#: Die Adressaten, die einen Auftrag **nicht über unser Repo** bekommen, sondern nur
#: über die abgelegten Blöcke. Für sie ist «im Repo abgelegt» und «beim Adressaten
#: angekommen» zweierlei — und nur das Zweite zählt.
ZUSTELLUNG_NOETIG = (_auftrag.WORKER_CLOUD, _auftrag.WORKER_UI)

#: Wo vermerkt wird, welche Kennungen schon als Block hinausgegangen sind. **Im Vermerk
#: steht kein Pfad** — nur Kennung und Zeitpunkt. Das Zielverzeichnis zeigt in ein
#: fremdes Repo, und dessen Aufbau gehört nicht in ein öffentliches (Regel 3).
ZUSTELLUNG_DATEI = "auftraege/zustellung.json"


def _zustellvermerk(repo_wurzel) -> dict:
    pfad = Path(repo_wurzel) / ZUSTELLUNG_DATEI
    if not pfad.is_file():
        return {}
    try:
        gelesen = json.loads(pfad.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        # EIN KAPUTTER VERMERK HEISST «NICHTS ZUGESTELLT», nicht «alles zugestellt».
        # Die strengere Auslegung ist hier die sichere: Sie führt zu einer Auslieferung
        # zu viel, die andere zu einem Auftrag, der nie ankommt.
        return {}
    return gelesen if isinstance(gelesen, dict) else {}


def vermerke_zustellung(repo_wurzel, kennungen, *, wann: str | None = None) -> int:
    """Festhalten, dass diese Kennungen als Block hinausgegangen sind.

    Returns:
        Wie viele Kennungen **neu** eingetragen wurden. Wer auch die schon vermerkten
        zählen will, zieht diese Zahl von der Zahl der (verschiedenen) Kennungen ab.

    **Die erste Zustellung zählt; ein zweiter Vermerk überschreibt sie nicht** — dieselbe
    Regel wie bei :func:`vermerke_gesehen`. Befund 22.09.2026, beim Verschicken selbst
    passiert: ``tools/auftragspost.py ui --vermerken`` setzte den Zeitpunkt ALLER offenen
    ui-Aufträge auf «jetzt», auch den von ``auf-20260909-99``, der seit dem 21.09.2026
    draussen war. Der Vermerk hätte ab da behauptet, der Auftrag sei erst heute
    hinausgegangen. Verfälscht wird damit der **gespeicherte Verlauf** — heute rechnet
    kein Leser das Alter aus diesem Zeitpunkt (``einbau`` nimmt ``erstellt``). Aber
    jede künftige Auswertung sähe einen Auftrag jünger, als er ist, und zwar in der
    gefährlichen Richtung: weniger Rückstand.

    **Einen Weg zum Neudatieren gibt es absichtlich nicht.** Ein erneut verschickter
    Block ändert nichts daran, seit wann der Adressat den Auftrag haben *kann*; genau das
    datiert der Vermerk. War die erste Zustellung eine Falschangabe (wie am 19.09.2026,
    als ``--nach`` ins eigene Repo zeigte), ist die Abhilfe, den falschen Eintrag aus
    :data:`ZUSTELLUNG_DATEI` zu **entfernen** — von Hand und mit einem Commit, der sagt
    warum —, nicht ihn mit einem neuen Datum zu überdecken. Ein Schalter dafür läge einen
    Tastendruck neben ``--vermerken`` und machte die bequemere Wahrheit zur billigsten.

    **Wozu, und der Fehler, der es ausgelöst hat.** Am 03.09.2026 lagen ``auf-70`` und
    ``auf-72`` seit zwei bzw. einem Tag in ``auftraege/offen/`` — und **nirgends sonst**.
    Der letzte Postlauf war vom 01.09.; seither war zwar abgelegt, aber nichts
    ausgeliefert worden. In jeder Zählung standen sie als Rückstand beim Adressaten,
    und nach unserem eigenen Satz war es einer beim Absender:

        *Ein Auftrag, den sein Adressat nicht erreichen kann, ist kein Rückstand bei
        ihm — er ist einer beim Absender.*

    Gemerkt hat es niemand, weil es nichts zu merken gab: Abgelegt und ausgeliefert
    sahen in jeder Liste gleich aus. Seither sind es zwei Zustände.

    Raises:
        PostError: ``kennungen`` ist eine einzelne Zeichenkette (siehe unten).
    """
    # DIE ARGUMENTE HABEN AM 17.09.2026 DIE PLAETZE GETAUSCHT, und ein alter Aufruf soll
    # das erfahren statt es zu erraten. Bis dahin hiess es hier `(kennungen, repo_wurzel)`
    # und in `vermerke_gesehen` `(repo_wurzel, kennungen)` — dieselbe Datei, zwei
    # Reihenfolgen. Ueberall sonst in diesem Modul steht die Repo-Wurzel zuerst
    # (`offene_blocks`, `gesehen_vermerke`, `warum_keine_antwort`), also war DIESE Funktion
    # der Ausreisser.
    #
    # Ein vertauschter Aufruf braeche ohnehin — aber mit `TypeError: expected str, bytes or
    # os.PathLike object, not list` aus dem Inneren von `pathlib`, und daran sieht niemand,
    # was er falsch gemacht hat. Ein Wegweiser kostet drei Zeilen.
    if isinstance(repo_wurzel, (list, tuple, set)) and not isinstance(kennungen, (list, tuple, set)):
        raise PostError(
            f"Die Argumente stehen vertauscht: seit dem 17.09.2026 heisst es "
            f"vermerke_zustellung(repo_wurzel, kennungen) — die Repo-Wurzel zuerst, wie "
            f"ueberall sonst in diesem Modul. Bekommen habe ich "
            f"{type(repo_wurzel).__name__} als Wurzel und {type(kennungen).__name__} als "
            f"Kennungen.")

    if isinstance(kennungen, str):
        # DERSELBE FEHLER WIE IN `vermerke_gesehen`, nur älter — am 16.09.2026 beim
        # Absichern der neuen Ablage auch hier nachgemessen:
        # `vermerke_zustellung("auf-1", wurzel)` legte fünf Zustellvermerke an («a», «u»,
        # «f», «-», «1»). Und hier wiegt er schwerer als drüben: Der echte Auftrag bleibt
        # dabei als NICHT ZUGESTELLT stehen — also in genau der Lage, die «unser Fehler»
        # heisst — während das Buch mit fünf Kennungen gefüllt ist, die es nicht gibt.
        # Ein Fehlschlag, der wie ein Erfolg aussieht, wird nicht gefunden; er wird
        # geglaubt. Darum laut statt still.
        raise PostError(
            f"«{kennungen}» ist eine einzelne Kennung und keine Folge. Eine Zeichenkette "
            f"würde Buchstabe für Buchstabe vermerkt — bitte [{kennungen!r}] übergeben.")
    vermerk = _zustellvermerk(repo_wurzel)
    zeit = wann or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    neu = 0
    for kennung in kennungen:
        schluessel = str(kennung)
        # EIN BESTEHENDER ZEITPUNKT BLEIBT STEHEN (Befund 22.09.2026, siehe oben). Bis
        # dahin stand hier eine blanke Zuweisung, und jeder Postlauf datierte alle
        # offenen Aufträge auf seinen eigenen Zeitpunkt um.
        if schluessel in vermerk:  # die erste Zustellung bleibt stehen
            continue
        vermerk[schluessel] = zeit
        neu += 1
    if neu:
        pfad = Path(repo_wurzel) / ZUSTELLUNG_DATEI
        pfad.parent.mkdir(parents=True, exist_ok=True)
        pfad.write_text(json.dumps(vermerk, indent=2, ensure_ascii=False,
                                   sort_keys=True) + "\n", encoding="utf-8")
    return neu


#: Wo vermerkt wird, dass ein Adressat einen Auftrag **gesehen** hat — dieselbe Bauform
#: wie :data:`ZUSTELLUNG_DATEI`, und aus demselben Grund kein Pfad darin (Regel 3).
#:
#: **Der dritte Zustand des Rückwegs.** Bis zum 16.09.2026 kannte dieses Repo auf dem
#: Rückweg zwei Tatsachen: hinausgegangen (Zustellvermerk) und beantwortet (Ergebnis).
#: Dazwischen lag alles, was :func:`warum_keine_antwort` nur *vermuten* kann — ein
#: zugestellter Auftrag ohne Antwort ist gelesen und verworfen, ungelesen liegengeblieben
#: oder gar nie angekommen, und von hier aus sieht das dreierlei gleich aus.
#:
#: Diese Ablage trägt die eine Auskunft, die wir uns nicht selbst geben können: dass
#: drüben jemand hingesehen hat. Sie kommt **vom Adressaten** (Zustellbeleg, Nebensatz in
#: einem Ergebnis, mündlich über den Owner) und wird von Hand oder von `tools/` eingetragen.
GESEHEN_DATEI = "auftraege/gesehen.json"

#: Wir selbst. Ein Blickvermerk unter diesem Namen wird abgewiesen — siehe
#: :func:`vermerke_gesehen`. Die Konstante steht hier und nicht als Zeichenkette im
#: Code, damit der Riegel mitwandert, wenn der Adressat einmal anders heisst.
SELBST = "kern"


def _schreibe_atomar(pfad: Path, daten: dict) -> Path:
    """Die Ablage in einem Zug ersetzen — **nie halb beschrieben zurücklassen**.

    Warum hier strenger als beim Zustellvermerk: Eine unlesbare ``gesehen.json`` lässt
    :func:`gesehen_vermerke` absichtlich hart fehlschlagen. Damit wäre eine abgebrochene
    Schreiboperation kein Schönheitsfehler, sondern ein Repo, in dem die Rückstandsfrage
    gar nicht mehr beantwortet werden kann. Der Zustellvermerk verkraftet eine zerrissene
    Datei (er liest sie als «nichts zugestellt»); diese hier nicht — also darf sie gar
    nicht erst entstehen.
    """
    pfad.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(daten, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    kennung, zwischenpfad = tempfile.mkstemp(dir=str(pfad.parent), suffix=".tmp")
    try:
        with os.fdopen(kennung, "w", encoding="utf-8") as datei:
            datei.write(text)
            datei.flush()
            # OHNE fsync LIEGT DER INHALT NUR IM PUFFER DES BETRIEBSSYSTEMS. `os.replace`
            # wäre dann zwar unteilbar, aber unteilbar auf eine leere Datei.
            os.fsync(datei.fileno())
        os.replace(zwischenpfad, pfad)
    except BaseException:
        try:
            os.unlink(zwischenpfad)
        except OSError:
            pass
        raise
    return pfad


def gesehen_vermerke(repo_wurzel) -> dict:
    """Die Ablage :data:`GESEHEN_DATEI` lesen.

    Returns:
        Je Kennung ``{"am": ISO-Zeit, "von": worker, "bemerkung": str | None}``. Eine
        **fehlende** Datei heisst «noch nie hat jemand einen Blick bestätigt» — das ist
        der Normalzustand dieses Repos und kein Befund.

    Raises:
        PostError: Die Datei ist da und nicht lesbar.

    **Warum das hier hart fehlschlägt und beim Zustellvermerk nicht.** Der Zustellvermerk
    liest eine kaputte Datei als «nichts zugestellt»: Die strengere Auslegung kostet dort
    eine Auslieferung zu viel, die mildere einen Auftrag, der nie ankommt. Hier gibt es
    diese sichere Richtung nicht. Ein leeres Ergebnis hiesse «niemand hat hingesehen» und
    würde eine bestätigte Tatsache still in eine Vermutung zurückverwandeln — ein
    unlesbares Buch heisst weder «nichts gesehen» noch «alles gesehen». *Die dritte
    Antwort: nicht messbar ist weder bestanden noch durchgefallen*, und sie wird laut.
    """
    pfad = Path(repo_wurzel) / GESEHEN_DATEI
    if not pfad.is_file():
        return {}
    try:
        gelesen = json.loads(pfad.read_text(encoding="utf-8"))
    except (OSError, ValueError) as fehler:
        raise PostError(
            f"{GESEHEN_DATEI} ist da und nicht lesbar ({fehler}). Diese Ablage wird NICHT "
            f"als leer gelesen: «leer» hiesse «niemand hat hingesehen», und das wäre eine "
            f"Aussage über den Adressaten, die aus einer kaputten Datei stammt.") from fehler
    if not isinstance(gelesen, dict):
        raise PostError(
            f"{GESEHEN_DATEI} trägt kein Wörterbuch, sondern {type(gelesen).__name__}. "
            f"Auch das wird nicht als leer gelesen — siehe oben.")
    return gelesen


def vermerke_gesehen(repo_wurzel, kennungen, *, von: str,
                     bemerkung: str | None = None, jetzt: str | None = None) -> int:
    """Festhalten, dass ein Adressat diese Aufträge **gesehen** hat.

    Args:
        kennungen: Die Auftragskennungen, für die ein Blick bestätigt ist.
        von: Wer hingesehen hat — einer aus :data:`aiimaging.auftrag.WORKER`. Ohne diese
            Angabe wäre der Vermerk wertlos: «jemand hat es gesehen» beantwortet keine
            der Fragen, für die es ihn gibt.
        bemerkung: Woher wir es wissen (ein Satz), oder ``None``. ``None`` heisst **nicht
            gemessen** — nicht «ohne Anlass». Ein leerer Text wird zu ``None``: Er sähe in
            der Ablage aus wie eine Bemerkung, die jemand geschrieben hat, und wäre keine.
        jetzt: Für Proben einsetzbar. Ohne Angabe die aktuelle UTC-Zeit.

    Returns:
        Wie viele Kennungen **neu** eingetragen wurden.

    **Ein zweiter Vermerk überschreibt den ersten nicht.** Der erste Blick ist der, der
    zählt: Er beantwortet die Frage, ob der Auftrag angekommen ist, und er datiert, seit
    wann der Adressat ihn kennt. Ein späterer Eintrag mit heutigem Datum wäre eine zweite
    Wahrheit — und zwar die bequemere, weil sie den Auftrag jedes Mal wieder jung aussehen
    liesse. *Der Vermerk soll den Fall finden, nicht ihn zudecken* (derselbe Satz wie beim
    Zustellvermerk am 03.09.2026, und derselbe Grund).

    Raises:
        PostError: ``von`` ist kein bekannter Adressat. Ein Tippfehler dort erzeugt einen
            Vermerk, den keine Auswertung je einem Worker zuordnet.
        PostError: ``kennungen`` ist eine einzelne Zeichenkette (siehe unten).
    """
    if isinstance(kennungen, str):
        # EINE ZEICHENKETTE IST AUCH EINE FOLGE — und zwar eine von Buchstaben. Gemessen
        # am 16.09.2026: `vermerke_gesehen(wurzel, "auf-1", von="ui")` trug fuenf
        # Vermerke ein («a», «u», «f», «-», «1») und meldete `5` zurueck. Kein Aufruf
        # waere je gescheitert, kein Auftrag je gefunden worden, und der Rueckstand haette
        # ab da eine Zahl getragen, die nichts zaehlt. Darum hier laut statt still.
        raise PostError(
            f"«{kennungen}» ist eine einzelne Kennung und keine Folge. Eine Zeichenkette "
            f"wuerde Buchstabe fuer Buchstabe vermerkt — bitte [{kennungen!r}] uebergeben.")
    if von not in _auftrag.WORKER:
        raise PostError(
            f"«{von}» ist kein bekannter Adressat ({', '.join(_auftrag.WORKER)}). Ein "
            f"Vermerk unter einem unbekannten Namen wird von keiner Auswertung gefunden.")
    if von == SELBST:
        # DER GANZE ZWECK DIESER ABLAGE IST DIE AUSKUNFT VOM ADRESSATEN. Alle anderen
        # Lagen von `warum_keine_antwort` lesen unsere eigene Buchfuehrung; diese eine
        # liest etwas, das nur drueben jemand wissen kann. Ein Vermerk mit `von="kern"`
        # hiesse «wir haben gesehen, dass wir es geschrieben haben» — er schluege die
        # beiden Vermutungslagen, obwohl er selbst nichts als eine dritte Vermutung ist.
        #
        # Das waere der teuerste Fehler, den diese Ablage machen kann: Sie wuerde eine
        # Zahl liefern, die aussieht wie eine Tatsache von drueben, und sie kaeme von uns.
        raise PostError(
            f"«{SELBST}» sind wir selbst — ein Blickvermerk von uns ueber uns ist keine "
            f"Auskunft. Diese Ablage traegt das eine, was wir uns NICHT selbst geben "
            f"koennen: dass drueben jemand hingesehen hat. Ein Eintrag von hier waere "
            f"eine Vermutung im Gewand einer Tatsache.")

    vermerk = gesehen_vermerke(repo_wurzel)
    zeit = jetzt or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    # Ein leerer oder nur aus Leerzeichen bestehender Text SIEHT in der Ablage aus wie
    # eine Bemerkung, die jemand geschrieben hat, und ist keine. Er wird zu None, und
    # None heisst hier NICHT GEMESSEN — nicht «ohne Anlass».
    bemerkung = str(bemerkung).strip() if bemerkung is not None else None
    bemerkung = bemerkung or None
    neu = 0
    for kennung in kennungen:
        schluessel = str(kennung)
        if schluessel in vermerk:
            continue
        vermerk[schluessel] = {"am": zeit, "von": von, "bemerkung": bemerkung}
        neu += 1
    if neu:
        _schreibe_atomar(Path(repo_wurzel) / GESEHEN_DATEI, vermerk)
    return neu



#: Wie jung ein Auftrag sein darf, bevor sein Ausbleiben überhaupt etwas heisst.
#:
#: Zwei Tage, und die Zahl ist bewusst grosszügig: Die Worker arbeiten in Sitzungen, nicht
#: im Takt. *Ein Auftrag von gestern, der noch keine Antwort hat, ist kein Befund.*
FRIST_FRISCH_TAGE = 2

#: Die fünf Lagen, in denen ein unbeantworteter Auftrag stehen kann.
#:
#: **Warum es mehr als eine ist.** Bis zum 16.09.2026 kannte dieses Repo nur
#: «unbeantwortet». Am selben Tag stand der Rückstand bei 18 Aufträgen, der älteste 25
#: Tage, und **seit acht Tagen hatte keiner der drei Worker geantwortet** — aber ob drüben
#: niemand arbeitete, ob die Aufträge nicht ankamen, oder ob sie ankamen und liegen
#: blieben, liess sich nicht unterscheiden.
#:
#: Für den **Hinweg** gibt es diese Unterscheidung seit dem 03.09.2026: der
#: Zustellvermerk. Für den **Rückweg** gab es sie nicht.
#:
#: *Und der Unterschied trägt eine Handlung:* Bei ``NICHT_ZUGESTELLT`` liegt der Fehler
#: bei uns. Bei ``AKTIV_UEBERGANGEN`` hat der Adressat gearbeitet und diesen einen liegen
#: lassen — dort ist eine Nachfrage angebracht. Bei ``KEIN_LEBENSZEICHEN`` wäre sie es
#: nicht: Wer seit Wochen nichts schickt, hat die Nachfrage vielleicht ebenso wenig
#: gesehen wie den Auftrag. **Erst messen, dann mahnen.**
#:
#: **Die fünfte kam am 16.09.2026 dazu, und sie ist die einzige, die nicht geraten ist.**
#: Die vier anderen lesen unsere eigene Ablage — wann der Auftrag entstand, ob er
#: hinausging, wann der Adressat zuletzt irgendetwas beantwortet hat. ``GESEHEN_OHNE_ANTWORT``
#: liest eine Auskunft *vom Adressaten* (:data:`GESEHEN_DATEI`). Darum schlägt sie die
#: beiden Vermutungslagen: **Ein bestätigter Blick ist stärker als jeder Schluss aus dem
#: Antwortverhalten** — auch dann, wenn dieser Adressat seit Wochen nichts geschickt hat.
NICHT_ZUGESTELLT = "nicht zugestellt"
FRISCH = "frisch"
GESEHEN_OHNE_ANTWORT = "gesehen, ohne antwort"
AKTIV_UEBERGANGEN = "aktiv, diesen uebergangen"
KEIN_LEBENSZEICHEN = "kein lebenszeichen"

LAGEN = (NICHT_ZUGESTELLT, FRISCH, GESEHEN_OHNE_ANTWORT, AKTIV_UEBERGANGEN,
         KEIN_LEBENSZEICHEN)


def _tag(wert) -> str:
    """Die ersten zehn Zeichen eines Zeitstempels — oder ``""``."""
    return str(wert or "")[:10]


def warum_keine_antwort(repo_wurzel, *, heute=None,
                        frist_tage: int = FRIST_FRISCH_TAGE) -> list[dict]:
    """Je unbeantwortetem Auftrag: **warum** die Antwort fehlt, soweit das hier messbar ist.

    Fünf Lagen (:data:`LAGEN`), und die Unterscheidung ist der ganze Zweck:

    ``nicht zugestellt``
        Der Auftrag ist nie hinausgegangen. **Unser Fehler**, nicht seiner.

    ``frisch``
        Jünger als ``frist_tage``. Noch keine Aussage — die Worker arbeiten in Sitzungen,
        nicht im Takt.

    ``gesehen, ohne antwort``
        Zu diesem Auftrag liegt ein Vermerk in :data:`GESEHEN_DATEI`: Der Adressat hat ihn
        **gesehen** und nicht beantwortet. *Hier ist eine Nachfrage angebracht, und sie
        kann sich auf den Vermerk berufen statt auf eine Vermutung.*

    ``aktiv, diesen uebergangen``
        Der Adressat hat **nach** diesem Auftrag etwas anderes beantwortet. Er war also
        da, und dieser eine blieb liegen. *Hier ist eine Nachfrage angebracht.*

    ``kein lebenszeichen``
        Seit diesem Auftrag kam von diesem Adressaten **gar nichts**. Das heisst
        ausdrücklich **nicht** «er ignoriert uns» — es heisst, dass wir es nicht wissen.
        Wer seit Wochen nichts schickt, hat eine Mahnung vielleicht ebenso wenig gesehen
        wie den Auftrag.

    **Was diese Funktion nicht kann, und das gehört an ihre Antwort:** Vier der fünf
    Lagen lesen nur unsere Seite. Ein zugestellter Auftrag, dessen Adressat schweigt, kann
    gelesen und verworfen, ungelesen liegengeblieben oder nie angekommen sein — von hier
    aus sieht das dreierlei gleich aus. Nur ``gesehen, ohne antwort`` beruht auf einer
    Auskunft *vom Adressaten*, und die kommt nicht von selbst: Sie muss über
    :func:`vermerke_gesehen` eingetragen werden. **Ohne Vermerk bleibt es beim Raten**, und
    das Raten heisst dann ``kein lebenszeichen`` und nicht «in Ordnung».

    Returns:
        Je Auftrag ``{auftrag_id, worker, erstellt, tage, lage, grund}``, älteste zuerst.
    """
    from datetime import date as _date

    wurzel = Path(repo_wurzel)
    stichtag = heute or _date.today()
    vermerk = _zustellvermerk(wurzel)
    # KEIN `try` DARUM. Eine unlesbare `gesehen.json` reisst diese Auswertung ab, statt
    # sie mit Vermutungen weiterlaufen zu lassen — siehe `gesehen_vermerke`.
    gesehen = gesehen_vermerke(wurzel)
    verhalten = _auftrag.antwortverhalten(wurzel)

    # WANN HAT DIESER ADRESSAT ZULETZT GEANTWORTET — je Adressat ein Tag.
    letzte = {w: _tag((verhalten.get(w) or {}).get("letzte_antwort"))
              for w in _auftrag.WORKER}

    aus: list[dict] = []
    for a in sorted(_auftrag.unerledigt(wurzel), key=lambda x: str(x.get("erstellt", ""))):
        kennung = a.get("auftrag_id")
        worker = a.get("worker")
        erstellt = _tag(a.get("erstellt"))
        try:
            tage = (stichtag - _date.fromisoformat(erstellt)).days
        except ValueError:
            tage = None

        if worker in ZUSTELLUNG_NOETIG and kennung not in vermerk:
            lage = NICHT_ZUGESTELLT
            grund = ("Nie hinausgegangen. Das ist ein Rueckstand bei UNS und keiner beim "
                     "Adressaten — er kann nicht beantworten, was er nicht hat.")
        elif tage is not None and tage < frist_tage:
            lage = FRISCH
            grund = (f"Erst {tage} Tag(e) alt. Die Worker arbeiten in Sitzungen und nicht "
                     f"im Takt; darunter sagt ein Ausbleiben nichts.")
        elif kennung in gesehen:
            # ER SCHLÄGT DIE BEIDEN VERMUTUNGSLAGEN, ABER NICHT `nicht zugestellt`.
            #
            # Gegen `AKTIV_UEBERGANGEN` und `KEIN_LEBENSZEICHEN` gewinnt er, weil beide
            # aus dem Antwortverhalten geschlossen sind und dieser hier bestätigt ist.
            #
            # Gegen `NICHT_ZUGESTELLT` verliert er, obwohl «gesehen» die Zustellung
            # logisch einschliesst: Stehen beide Angaben gegeneinander, ist das ein Fehler
            # in UNSERER Buchführung — der Zustellvermerk wurde beim Ausliefern
            # vergessen. Wer ihn hier vom Blickvermerk zudecken lässt, verliert die
            # einzige Stelle, an der dieses Versäumnis noch auffällt. Und die
            # Handlungsanweisung wäre die falsche: nachfragen statt die eigene Ablage
            # in Ordnung bringen.
            eintrag = gesehen.get(kennung)
            if not isinstance(eintrag, dict):
                # EIN VON HAND EINGETRAGENER ZEITSTEMPEL statt des Wörterbuchs. Daran
                # abzustürzen hiesse, eine richtige Auskunft wegen ihrer Form zu
                # verwerfen — die Kennung steht da, und das ist die Aussage.
                eintrag = {"am": eintrag, "von": worker, "bemerkung": None}
            am = _tag(eintrag.get("am")) or "unbekannt"
            bemerkung = str(eintrag.get("bemerkung") or "").strip()
            lage = GESEHEN_OHNE_ANTWORT
            grund = (f"{worker} hat ihn gesehen (vermerkt am {am}) und nicht beantwortet. "
                     f"Eine Nachfrage ist angebracht und kann sich auf den Vermerk berufen "
                     f"statt auf eine Vermutung.")
            if bemerkung:
                grund += f" Vermerk: {bemerkung}"
        elif letzte.get(worker) and letzte[worker] > erstellt:
            lage = AKTIV_UEBERGANGEN
            grund = (f"{worker} hat am {letzte[worker]} geantwortet, also NACH diesem "
                     f"Auftrag vom {erstellt}. Er war da und hat diesen liegen lassen — "
                     f"hier ist eine Nachfrage angebracht.")
        else:
            lage = KEIN_LEBENSZEICHEN
            seit = letzte.get(worker) or "nie"
            grund = (f"Seit diesem Auftrag kam von {worker} gar nichts (letzte Antwort: "
                     f"{seit}). Das heisst NICHT, dass er uns uebergeht — es heisst, dass "
                     f"wir es nicht wissen. Eine Mahnung haette er vielleicht ebenso wenig "
                     f"gesehen wie den Auftrag.")

        aus.append({"auftrag_id": kennung, "worker": worker, "erstellt": erstellt,
                    "tage": tage, "lage": lage, "grund": grund})
    return aus


def unzugestellt(repo_wurzel) -> list[dict]:
    """Offene Aufträge an :data:`ZUSTELLUNG_NOETIG`, die noch nie ausgeliefert wurden.

    Returns:
        Je Auftrag ``{auftrag_id, worker, erstellt}``, älteste zuerst. **Leer heisst:
        alles, was offen ist, ist auch draussen** — nicht, dass es gelesen wurde. Ob es
        gelesen wird, sagt allein der :data:`ZUSTELLBELEG`.
    """
    vermerk = _zustellvermerk(repo_wurzel)
    offen = [a for a in _auftrag.unerledigt(repo_wurzel)
             if a.get("worker") in ZUSTELLUNG_NOETIG
             and a.get("auftrag_id") not in vermerk]
    offen.sort(key=lambda a: str(a.get("erstellt", "")))
    return [{"auftrag_id": a.get("auftrag_id"), "worker": a.get("worker"),
             "erstellt": a.get("erstellt")} for a in offen]


__all__ = ["AKTIV_UEBERGANGEN", "BREITE", "FRISCH", "SELBST", "FRIST_FRISCH_TAGE", "GESEHEN_DATEI",
           "GESEHEN_OHNE_ANTWORT", "KEIN_LEBENSZEICHEN",
           "LAGEN", "NICHT_ZUGESTELLT", "RUECKWEG", "ZUSTELLUNG_DATEI", "ZUSTELLUNG_NOETIG",
           "PostError", "warum_keine_antwort",
           "block", "gesehen_vermerke", "lege_ab", "offene_blocks", "unzugestellt",
           "vermerke_gesehen", "vermerke_zustellung", "zustellbeleg_stand"]
