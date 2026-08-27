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

from collections.abc import Sequence
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


def block(satz: dict) -> str:
    """Der Auftrag als ein Text, den der Owner ohne Nachdenken weiterreichen kann.

    Args:
        satz: Ein Auftrag, wie ihn :func:`aiimaging.auftrag.schreibe_auftrag` ablegt.

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
    for auflage in satz.get("auflagen") or []:
        teile.append(_punkt(str(auflage)))
    teile += ["", "WAS ZURUECKKOMMEN SOLL"]
    for frage in satz.get("rueckgabe") or []:
        teile.append(_punkt(str(frage)))

    rueckweg = RUECKWEG.get(worker)
    if rueckweg:
        teile += ["", "RUECKWEG", _punkt(rueckweg.format(kennung=kennung), "  ")]
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


def offene_blocks(repo_wurzel, *, worker: str | None = None) -> list[tuple[str, str]]:
    """Alle unbeantworteten Aufträge als Blöcke, älteste zuerst.

    Args:
        worker: Nur diesen Adressaten. Ohne Angabe alle — was beim Weiterreichen selten
            gemeint ist, weshalb `tools/auftragspost.py` die Angabe verlangt.

    Returns:
        Je Auftrag ``(kennung, block)``.
    """
    aus = []
    for satz in _auftrag.unerledigt(Path(repo_wurzel)):
        if worker and satz.get("worker") != worker:
            continue
        kennung = satz.get("auftrag_id") or "(ohne Kennung)"
        try:
            aus.append((kennung, block(satz)))
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


__all__ = ["BREITE", "RUECKWEG", "PostError", "block", "lege_ab", "offene_blocks"]
