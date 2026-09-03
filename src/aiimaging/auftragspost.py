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
from collections.abc import Sequence
from datetime import datetime, timezone
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

#: Stichtag für :data:`ZUSTELLBELEG`. **Er steht hier als Vorgabe und nicht im Text**,
#: weil er veraltet: Sobald ein Adressat antwortet, gehört der Beleg weg und nicht eine
#: falsche Zahl hinein.
#:
#: **Er wird von Hand nachgezogen, die Zahl daneben nicht** — ``n_offen`` reicht der
#: Aufrufer aus einer frischen Zählung herein. Eine frisch gezählte Zahl neben einem
#: zwei Tage alten Datum liest sich wie ein aktueller Stand und ist keiner; wer die
#: Post neu erzeugt, zieht darum dieses Datum mit. *Nachgezogen am 03.09.2026, nachdem
#: der Beleg zwei Tage lang mit dem Datum seiner Einführung hinausging.*
ZUSTELLBELEG_STAND = "03.09.2026"


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
                                             stand=ZUSTELLBELEG_STAND), "  ")]
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


def vermerke_zustellung(kennungen, repo_wurzel, *, wann: str | None = None) -> Path:
    """Festhalten, dass diese Kennungen als Block hinausgegangen sind.

    **Wozu, und der Fehler, der es ausgelöst hat.** Am 03.09.2026 lagen ``auf-70`` und
    ``auf-72`` seit zwei bzw. einem Tag in ``auftraege/offen/`` — und **nirgends sonst**.
    Der letzte Postlauf war vom 01.09.; seither war zwar abgelegt, aber nichts
    ausgeliefert worden. In jeder Zählung standen sie als Rückstand beim Adressaten,
    und nach unserem eigenen Satz war es einer beim Absender:

        *Ein Auftrag, den sein Adressat nicht erreichen kann, ist kein Rückstand bei
        ihm — er ist einer beim Absender.*

    Gemerkt hat es niemand, weil es nichts zu merken gab: Abgelegt und ausgeliefert
    sahen in jeder Liste gleich aus. Seither sind es zwei Zustände.
    """
    vermerk = _zustellvermerk(repo_wurzel)
    zeit = wann or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    for kennung in kennungen:
        vermerk[str(kennung)] = zeit
    pfad = Path(repo_wurzel) / ZUSTELLUNG_DATEI
    pfad.parent.mkdir(parents=True, exist_ok=True)
    pfad.write_text(json.dumps(vermerk, indent=2, ensure_ascii=False,
                               sort_keys=True) + "\n", encoding="utf-8")
    return pfad


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


__all__ = ["BREITE", "RUECKWEG", "ZUSTELLUNG_DATEI", "ZUSTELLUNG_NOETIG", "PostError",
           "block", "lege_ab", "offene_blocks", "unzugestellt", "vermerke_zustellung"]
