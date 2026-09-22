"""Das **Projekt** — die Mappe, in der die Arbeit einer Person zusammenbleibt.

Warum es diese Schicht gibt, und warum sie die Fundation ist
------------------------------------------------------------
Dieses Repo kann viel: ein Modell hereinholen, Kameras rechnen, rendern, nachmessen.
Was es bis zum 21.09.2026 **nicht** kann, ist das Selbstverständlichste:

    *Ein Modell öffnen, etwas damit machen, das Fenster schliessen — und morgen dort
    weitermachen.*

Jede Fähigkeit lebt heute in ihrem eigenen Aufruf, und was dabei herauskommt, liegt in
Verzeichnissen, deren Zusammenhang nur im Kopf desjenigen besteht, der sie angelegt hat.
*Was nicht in einer Datei steht, ist weg* — dieselbe Regel, die für Sitzungsprotokolle
gilt, gilt für die Arbeit einer Architektin.

Alles, was noch kommen soll, setzt genau hier auf:

============================  ======================================================
Der Knotenbaum in der Oberfläche   braucht etwas, das er anzeigt und speichert.
Ein Gespräch mit «Kosmo»           braucht etwas, worauf es sich bezieht.
Variantenstudien                   brauchen eine **benannte Basis** und deren Urteil.
Ein Ein-Klick-Download             braucht einen Ort, an dem die Arbeit landet.
============================  ======================================================

Fünf Entscheide, und jeder hat einen Preis
------------------------------------------
**1 · Das Projekt verweist auf das Modell, es schluckt es nicht.**
Eine 500-MB-IFC in den Projektordner zu kopieren hiesse, eine **zweite Wahrheit** auf der
Platte zu haben: Wer danach die eine ändert, hat zwei Gebäude. Der Preis ist, dass ein
verschobenes Modell das Projekt unterbricht — darum sagt :func:`oeffne` ausdrücklich, ob
das Modell noch da ist und ob es sich verändert hat.

**2 · Nichts wird beim Öffnen repariert.**
Ein Projekt, dessen Modell sich geändert hat, bleibt offen und **meldet es**. Es rechnet
nicht still neu. *Ein stillschweigend behobener Zustand wandert unbemerkt weiter und taucht
später als unerklärliche Zahl wieder auf.*

**3 · Jedes Bild trägt sein Urteil, und ``None`` heisst NICHT GEMESSEN.**
Ein Bild ohne Prüfung wird **mit** dem Vermerk abgelegt, dass keine stattfand — nicht ohne
Feld. Ein fehlendes Feld liest sich später wie «war wohl in Ordnung».

**4 · Die Projektdatei ist lesbarer Text.**
Sie ist JSON, eingerückt, mit ausgeschriebenen Feldnamen. Jemand muss hineinsehen können,
ohne dieses Programm zu starten — auch in zehn Jahren, auch ohne Python.

**5 · Regel 3 wird beim Schreiben durchgesetzt, nicht erwähnt.**
Benutzernamen in Pfaden werden ersetzt, bevor die Datei entsteht. Die Zahl der Ersetzungen
steht in der Datei: *Eine Säuberung, die nicht sagt, dass sie stattfand, ist von keiner
Säuberung zu unterscheiden.*

Was dieses Modul ausdrücklich NICHT tut
---------------------------------------
Es rendert nichts, misst nichts und ruft kein fremdes Programm. Es **hält fest**, was
andere Module getan haben. Ein Projektmodul, das selbst rechnet, wird zu der Stelle, durch
die alles hindurch muss — und dann ist die Bibliothek keine Bibliothek mehr, sondern ein
Programm mit einem Einstiegspunkt (Regel 4).

Regel 4: Alles hier ist aus reinem Python aufrufbar. Keine Oberfläche, kein ``bpy``,
keine GPU, kein Netz.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from aiimaging import einlass
# REGEL 3 STEHT AN GENAU EINER STELLE, und das ist `auftrag.ohne_kennungen`. Sie hier
# nachzubauen hiesse, dieselbe Regel zweimal zu haben — und eine Regel, die an zwei
# Stellen steht, ist an einer davon bereits veraltet. Der Import geht nur in diese
# Richtung und holt eine reine Textfunktion; das Auftragswesen weiss von Projekten nichts.
from aiimaging.auftrag import ohne_kennungen

__all__ = [
    "MODELL_FEHLT", "MODELL_NICHT_PRUEFBAR", "MODELL_UNVERAENDERT", "MODELL_VERAENDERT",
    "PROJEKTDATEI", "ProjektError", "ProjektKollision", "SCHEMA",
    "VOLLE_PRUEFUNG_BIS_BYTE", "TITEL_HOECHSTENS",
    "benenne", "fingerabdruck", "markiere_skizze", "neu", "oeffne", "speichere",
    "vermerke_bild", "vermerke_skizze",
]


class ProjektError(ValueError):
    """Das Projekt selbst ist nicht brauchbar — nicht das Modell darin.

    Derselbe Unterschied wie am Einlass: Eine unbrauchbare **Modelldatei** ist ein Befund
    und steht im Projekt. Eine unlesbare **Projektdatei**, ein Ordner ohne Projekt, ein
    Schema aus der Zukunft — das sind Fehler des Werkzeugs, und sie fliegen.
    """


#: Kennung des Dateiformats. Steht in jeder Projektdatei und wird beim Öffnen geprüft.
SCHEMA = "visbox.projekt/v1"

#: Wie die Projektdatei im Projektordner heisst.
PROJEKTDATEI = "projekt.json"

#: Bis zu dieser Grösse wird die **ganze** Datei gelesen, um sie wiederzuerkennen.
#:
#: **GESETZT, nicht gemessen**, und der Grund steht hier, weil er sonst niemandem auffällt:
#: Eine 500-MB-IFC ganz zu lesen kostet bei jedem Öffnen Sekunden. Darüber wird darum nur
#: Anfang und Ende gelesen — das ist **schwächer** und wird auch so gemeldet
#: (:data:`MODELL_NICHT_PRUEFBAR` gibt es dafür nicht; der Fingerabdruck sagt selbst,
#: welche Art er ist).
VOLLE_PRUEFUNG_BIS_BYTE = 64 * 1024 * 1024

#: Wieviel bei grossen Dateien von Anfang und Ende gelesen wird.
FENSTER_BYTE = 64 * 1024

#: Das Modell liegt da und sieht aus wie beim letzten Mal.
MODELL_UNVERAENDERT = "unveraendert"
#: Das Modell liegt da, ist aber ein anderes geworden.
MODELL_VERAENDERT = "veraendert"
#: An dem Pfad liegt nichts mehr.
MODELL_FEHLT = "fehlt"
#: Es liess sich nicht feststellen — **weder ja noch nein.**
MODELL_NICHT_PRUEFBAR = "nicht_pruefbar"


class ProjektKollision(ProjektError):
    """Zwei Stände derselben Mappe — und keiner von beiden wird stillschweigend verworfen.

    Geworfen, wenn auf der Platte ein **neuerer** Stand liegt als der, aus dem heraus
    gespeichert werden soll. Das ist kein Defekt, sondern der Normalfall, sobald ein iPad
    und die HomeStation dieselbe Mappe führen.

    **Warum das eine eigene Fehlerart ist und keine Meldung im Text:** Der Aufrufer muss
    diesen Fall anders behandeln als eine kaputte Datei — er kann die Mappe neu öffnen,
    seine Änderung darauf wiederholen und erneut speichern. Eine Fehlerart lässt sich
    abfangen; ein Satz in einer Meldung lässt sich nur lesen.

        *Wer die Arbeit des anderen überschreibt, tut es nie absichtlich — er erfährt nur
        nie, dass es einen anderen gab.*
    """


def _jetzt() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def fingerabdruck(pfad, *, voll_bis_byte: int = VOLLE_PRUEFUNG_BIS_BYTE,
                  fenster_byte: int = FENSTER_BYTE) -> dict:
    """Etwas, woran sich diese Datei wiedererkennen lässt — **mit seinem Vorbehalt**.

    Args:
        pfad: Die Datei.
        voll_bis_byte: Bis zu welcher Grösse die **ganze** Datei gelesen wird. Der
            Vorgabewert ist :data:`VOLLE_PRUEFUNG_BIS_BYTE`.

            **Dass dieser Wert überhaupt übergeben werden kann, ist ein Befund vom
            21.09.2026.** Die Probe, die belegen sollte, dass die Grösse in den Abdruck
            eingeht, prüfte das gar nicht: Sie benutzte zwei *kleine* Dateien, und dort
            wird ohnehin alles gelesen — die Summen unterschieden sich schon am Inhalt.
            Die Mutationsprobe ging durch, ohne dass eine einzige Zeile fiel.

                *Ein Wächter, der nur den Weg bewacht, den man beim Schreiben im Kopf
                hatte, bewacht den anderen nicht.*

            Den Schwellenwert übergeben zu können, ist der billigste Weg, den zweiten Weg
            mit zwei Handvoll Bytes zu prüfen, statt mit 64 MB.
        fenster_byte: Wieviel auf dem zweiten Weg von Anfang und Ende gelesen wird.
            Vorgabe :data:`FENSTER_BYTE`.

            **Auch das ist ein Befund, und zwar der zweite am selben Tag.** Die berichtigte
            Probe setzte nur ``voll_bis_byte`` herunter — und fiel wieder nicht. Grund:
            Das Fenster von 64 KiB ist **grösser als die ganze Testdatei**, also wurde
            zweimal alles gelesen, und die Summen unterschieden sich erneut schon am
            Inhalt.

                *Beim ersten Anlauf prüfte der Wächter den falschen Weg. Beim zweiten
                prüfte er den richtigen — unter Bedingungen, unter denen er sich wie der
                falsche verhält.*

    Returns:
        ``{art, groesse_byte, summe}``. ``art`` ist ``"voll"`` (die ganze Datei gelesen)
        oder ``"anfang_und_ende"``. ``summe`` ist ``None``, wenn sich nichts lesen liess.

    **Warum die Art mitkommt und nicht nur die Summe.** Bei einer grossen Datei werden nur
    die ersten und letzten 64 KiB gelesen. Das erkennt eine ersetzte oder neu exportierte
    Datei zuverlässig und eine Änderung **in der Mitte einer grossen Datei möglicherweise
    nicht**. Eine Prüfsumme ohne Angabe, worüber sie läuft, behauptet mehr, als sie weiss.

    *Diese Funktion urteilt nicht. Sie beschreibt, und sie sagt, wie genau.*
    """
    pfad = Path(pfad)
    try:
        groesse = pfad.stat().st_size
    except OSError:
        return {"art": None, "groesse_byte": None, "summe": None}

    hasch = hashlib.sha256()
    try:
        with pfad.open("rb") as datei:
            if groesse <= voll_bis_byte:
                art = "voll"
                for block in iter(lambda: datei.read(1024 * 1024), b""):
                    hasch.update(block)
            else:
                art = "anfang_und_ende"
                hasch.update(datei.read(fenster_byte))
                datei.seek(max(0, groesse - fenster_byte))
                hasch.update(datei.read(fenster_byte))
    except OSError:
        return {"art": None, "groesse_byte": groesse, "summe": None}

    # DIE GROESSE GEHT IN DIE SUMME EIN. Sonst haetten zwei Dateien mit gleichem Anfang
    # und Ende, aber verschiedener Laenge, denselben Abdruck — und genau so sieht eine
    # abgeschnittene Uebertragung aus.
    hasch.update(str(groesse).encode("ascii"))
    return {"art": art, "groesse_byte": groesse, "summe": hasch.hexdigest()}


def _modellstand(gespeichert: dict, jetzt: dict) -> tuple[str, str]:
    """Vergleicht zwei Fingerabdrücke und sagt, was daraus folgt — als Satz."""
    if jetzt["groesse_byte"] is None:
        return (MODELL_FEHLT,
                "An diesem Pfad liegt keine Datei mehr. Das Projekt bleibt offen — was "
                "darin steht, ist weiterhin gültig; es lässt sich nur nichts Neues daraus "
                "rechnen, bis das Modell wieder da ist.")
    if jetzt["summe"] is None or gespeichert.get("summe") is None:
        return (MODELL_NICHT_PRUEFBAR,
                "Ob das Modell noch dasselbe ist, liess sich nicht feststellen — die "
                "Datei ist da, aber nicht lesbar. Das ist weder ein Ja noch ein Nein.")
    if jetzt["summe"] == gespeichert["summe"]:
        return (MODELL_UNVERAENDERT, "Das Modell ist dasselbe wie beim letzten Öffnen.")

    # WARUM HIER DIE ART DAZUGEHOERT: Bei «anfang_und_ende» ist ein Unterschied ein
    # sicherer Befund, eine Gleichheit aber nur ein starker Hinweis. Die Meldung sagt das,
    # statt eine Sicherheit zu behaupten, die die Methode nicht hergibt.
    return (MODELL_VERAENDERT,
            "Das Modell hat sich seit dem letzten Öffnen geändert. **Es wird nichts neu "
            "gerechnet und nichts verworfen.** Was bisher gemessen wurde, gehört zum alten "
            "Stand — und gilt dafür weiter. Wer den neuen Stand beurteilt haben will, "
            "rechnet neu; wer den alten vergleichen will, hat ihn noch.")


def pfad_fuer_die_mappe(pfad, wurzel) -> str:
    """Ein Pfad, wie er **in** der Projektdatei steht — relativ zur Mappe, wo es geht.

    **Der Anlass ist ein Produktfehler, gefunden am 21.09.2026 von Beweis 31.**

    Die Mappe wird beim Speichern von Benutzernamen befreit (Regel 3, dieses Repo ist
    öffentlich). Aus dem Heimatverzeichnis eines Menschen wurde dabei
    ``/home/<nutzer>/…`` — ein Pfad, der **auf nichts mehr zeigt**. (Ein echtes Beispiel
    steht hier nicht: Der Wächter zu Regel 3 hat genau diese Zeile beim ersten Lauf
    gemeldet, und er hatte recht.) Beim
    nächsten Öffnen meldete jedes Projekt ``modell fehlt``, und ``rechne`` verweigerte die
    Arbeit mit «keine umgewandelte Geometrie».

    **Aufgefallen ist es nie**, weil jede Probe unter ``tmp_path`` läuft — und der liegt
    unter ``/tmp`` und trägt keinen Benutzernamen.

        *Zum dritten Mal in diesem Projekt sass der Fehler genau zwischen der Attrappe und
        der echten Datei.*

    **Die Lösung ist keine Ausnahme von Regel 3, sondern der bessere Pfad.** Relativ zur
    Mappe enthält er keinen Benutzernamen — und die Mappe wird nebenbei **umziehbar**:
    Wer sie auf einen Stick kopiert, nimmt das Modell mit, und die Angabe stimmt weiter.

    Absolut bleibt es nur dort, wo kein relativer Pfad existiert (ein anderes Laufwerk
    unter Windows). Dann greift die Säuberung wie bisher, und das Projekt meldet beim
    Öffnen ehrlich, dass es das Modell nicht findet.
    """
    pfad, wurzel = Path(pfad), Path(wurzel)
    try:
        return str(_relativ(pfad, wurzel))
    except ValueError:
        # KEIN GEMEINSAMER STAMM — etwa ein anderes Laufwerk. Dann absolut, und die
        # Saeuberung macht daraus einen Pfad, der nicht mehr traegt. Das ist unschoen und
        # ehrlich: Beim Oeffnen steht «Modell fehlt», und das stimmt dann auch.
        return str(pfad)


def _relativ(pfad: Path, wurzel: Path) -> Path:
    """``pfad`` relativ zu ``wurzel`` — auch nach oben (``..``).

    ``Path.relative_to`` kann nur nach unten. Eine Modelldatei liegt aber fast immer
    **neben** der Mappe und nicht darin, und genau dieser Fall ist der häufige.
    """
    import os
    return Path(os.path.relpath(pfad.resolve(), wurzel.resolve()))


def loese_pfad(gespeichert, wurzel):
    """Aus der Angabe in der Mappe wieder einen Pfad auf dieser Platte machen.

    Ein relativer Pfad wird an der Mappe verankert, ein absoluter bleibt, wie er ist.
    Leer bleibt leer — ``""`` ist keine Datei und wird auch nicht zu einer.
    """
    if not gespeichert:
        return Path("")
    p = Path(gespeichert)
    return p if p.is_absolute() else (Path(wurzel) / p)


def neu(wurzel, modell, *, name: str | None = None, einstellungen: dict | None = None) -> dict:
    """Ein Projekt anlegen — **und dabei einmal auf das Modell sehen.**

    Args:
        wurzel: Der Projektordner. Er wird angelegt, wenn es ihn nicht gibt.
        modell: Die Modelldatei. Sie wird **nicht kopiert**, nur vermerkt.
        name: Anzeigename. Ohne Angabe der Dateiname des Modells.
        einstellungen: Frei belegbar (Backbone, Auflösung, Prompt …). Dieses Modul deutet
            nichts davon — es hält es fest.

    Returns:
        Das Projekt als ``dict``. Es ist **noch nicht geschrieben**; dafür gibt es
        :func:`speichere`.

    Raises:
        ProjektError: Der Ordner lässt sich nicht anlegen, oder dort liegt schon ein
            Projekt. **Ein unbrauchbares Modell wirft nicht** — es steht als Befund im
            Projekt, und zwar mit dem Satz, der am Einlass dafür geschrieben wurde.

    **Warum ein schlechtes Modell hier kein Fehler ist.** Wer ein Projekt anlegt, hat eine
    Absicht; ihm die Mappe zu verweigern, weil die Datei nicht taugt, nimmt ihm auch die
    Stelle, an der die Begründung stünde. *Eine Absage ohne Ausweg ist eine halbe
    Auskunft* — hier steht der Ausweg im Projekt selbst.
    """
    wurzel = Path(wurzel)
    modell = Path(modell)
    ziel = wurzel / PROJEKTDATEI
    if ziel.exists():
        raise ProjektError(
            f"In {wurzel} liegt schon ein Projekt. Es zu überschreiben wäre ein "
            f"Datenverlust ohne Rückfrage — zum Weiterarbeiten `oeffne` benutzen.")
    try:
        wurzel.mkdir(parents=True, exist_ok=True)
    except OSError as fehler:
        raise ProjektError(f"Der Projektordner liess sich nicht anlegen: {fehler}") from fehler

    try:
        befund = einlass.sichte(modell)
    except einlass.EinlassError as fehler:
        # DER SICHTGANG DARF HIER NICHT SCHEITERN LASSEN. Dass er nicht stattfinden
        # konnte, ist eine Auskunft ueber die Umstaende und kein Urteil ueber die Datei.
        befund = {"brauchbar": None, "grund": f"Der Sichtgang war nicht möglich: {fehler}",
                  "format": None, "hochachse": None, "hochachse_steht_fest": None,
                  "hinweise": [], "naechster_schritt": None}

    return {
        "schema": SCHEMA,
        "name": name or modell.stem,
        "angelegt": _jetzt(),
        "zuletzt_gespeichert": None,
        # DIE NUMMER DES STANDES — und sie steht hier, weil zwei Geraete dieselbe Mappe
        # oeffnen koennen.
        #
        # Ein iPad und die HomeStation lesen beide dieselbe Datei, arbeiten beide daran
        # und schreiben beide zurueck. Ohne diese Zahl gewinnt schlicht der Letzte, und
        # der andere verliert seine Arbeit, OHNE dass es irgendwo auffiele — dieselbe
        # Bauform wie die zwei gleichzeitigen Laeufe, die am 21.09.2026 einer den anderen
        # ueberschrieben haben, nur eine Ebene hoeher.
        #
        # Die Zahl zaehlt bei jedem Schreiben um eins hoch. Wer speichert, muss von dem
        # Stand kommen, der auf der Platte liegt; sonst wird abgelehnt statt
        # ueberschrieben. Siehe `speichere` und `ProjektKollision`.
        "stand_nr": 1,
        "modell": {
            # RELATIV ZUR MAPPE, wo es geht — siehe `pfad_fuer_die_mappe`. Ein absoluter
            # Pfad ueberlebt die Saeuberung nach Regel 3 nicht.
            "pfad": pfad_fuer_die_mappe(modell, wurzel),
            "abdruck": fingerabdruck(modell),
            # DER BEFUND VOM EINLASS WANDERT MIT, und das ist mehr als Bequemlichkeit:
            # Er sagt, was ueber Format und Hochachse feststand, ALS das Projekt entstand.
            # Spaeter ist das nicht mehr zu rekonstruieren.
            "einlass": {
                "brauchbar": befund["brauchbar"],
                "grund": befund["grund"],
                "format": befund.get("format"),
                "hochachse": befund.get("hochachse"),
                "hochachse_steht_fest": befund.get("hochachse_steht_fest"),
                "hinweise": list(befund.get("hinweise") or ()),
                "naechster_schritt": befund.get("naechster_schritt"),
            },
        },
        "einstellungen": dict(einstellungen or {}),
        "bilder": [],
        # DIE EINGABE DES ENTWURFSMODUS (E23). Sie steht hier von Anfang an leer da und
        # entsteht nicht erst beim ersten Eintrag: Ein Feld, das mal fehlt und mal nicht,
        # zwingt jeden Leser zu einer Fallunterscheidung, die nichts bedeutet.
        "skizzen": [],
        "regel3_ersetzt": 0,
    }


def _stand_auf_der_platte(ziel: Path):
    """Welche Standnummer in der Datei steht, die gerade dort liegt.

    ``None`` heisst **nicht feststellbar** und nicht «null»: keine Datei, unlesbar, oder
    eine ältere, die diese Zahl noch nicht führt. In allen drei Fällen wird geschrieben —
    eine Mappe, die vor dieser Neuerung entstanden ist, darf nicht plötzlich klemmen.
    """
    try:
        vorhanden = json.loads(ziel.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(vorhanden, dict):
        return None
    nummer = vorhanden.get("stand_nr")
    return nummer if isinstance(nummer, int) else None


def speichere(projekt: dict, wurzel) -> Path:
    """Das Projekt schreiben — atomar, und von Benutzernamen befreit.

    **Atomar**, weil ein halb geschriebenes Projekt schlimmer ist als gar keines: Es sieht
    aus wie eines und lässt sich nicht öffnen. Geschrieben wird darum daneben und dann
    umbenannt — ein Umbenennen im selben Dateisystem ist unteilbar.

    **Von Benutzernamen befreit** (Regel 3), und die Zahl der Ersetzungen steht in der
    Datei: *Eine Säuberung, die nicht sagt, dass sie stattfand, ist von keiner Säuberung
    zu unterscheiden.*

    **Und es wird nachgesehen, ob jemand anderes inzwischen geschrieben hat.** Seit dem
    22.09.2026 trägt jede Mappe eine Standnummer. Liegt auf der Platte eine höhere als die
    des Projekts, aus dem heraus gespeichert werden soll, wirft diese Funktion
    :class:`ProjektKollision` — sie schreibt **nicht**.

    Der Fall ist kein Sonderfall: Sobald ein iPad und die HomeStation dieselbe Mappe
    führen, ist er der Normalfall. Ohne die Prüfung gewänne schlicht der Letzte.

    **Was diese Prüfung NICHT leistet, und das gehört dazu:** Zwischen dem Blick auf die
    Platte und dem Umbenennen liegen Mikrosekunden. Zwei Schreibvorgänge, die in dieses
    Fenster fallen, fängt sie nicht — dafür gibt es die Laufsperre in
    :mod:`aiimaging.arbeitsgang`, die den rechnenden Weg ohnehin abdeckt. Gefangen wird
    der Fall, der in der Praxis vorkommt: zwei Geräte, die Minuten auseinander schreiben.

        *Eine Sperre, die den seltenen Fall nicht kann, ist trotzdem besser als keine —
        solange sie sagt, welchen sie nicht kann.*

    Returns:
        Der Pfad der geschriebenen Datei.

    Raises:
        ProjektKollision: Auf der Platte liegt ein neuerer Stand.
    """
    if not isinstance(projekt, dict) or projekt.get("schema") != SCHEMA:
        raise ProjektError(
            f"Das ist kein Projekt dieses Formats (erwartet {SCHEMA!r}, war "
            f"{projekt.get('schema') if isinstance(projekt, dict) else type(projekt).__name__!r}).")

    wurzel = Path(wurzel)
    wurzel.mkdir(parents=True, exist_ok=True)
    ziel = wurzel / PROJEKTDATEI

    # DER BLICK AUF DIE PLATTE, BEVOR GESCHRIEBEN WIRD.
    #
    # Ohne ihn gewinnt der Letzte, und der andere verliert seine Arbeit lautlos. Mit ihm
    # verliert niemand etwas: Wer auf einem ueberholten Stand sitzt, bekommt eine
    # Ablehnung und kann neu oeffnen, seine Aenderung wiederholen und erneut speichern.
    meiner = projekt.get("stand_nr")
    meiner = meiner if isinstance(meiner, int) else 0
    drueben = _stand_auf_der_platte(ziel)
    if drueben is not None and drueben > meiner:
        raise ProjektKollision(
            f"Diese Mappe ist inzwischen weitergeschrieben worden: Auf der Platte liegt "
            f"Stand {drueben}, dieser hier kommt von Stand {meiner}. Gespeichert wird "
            f"NICHT — sonst waere die Arbeit des anderen weg, ohne dass es jemandem "
            f"auffiele. Die Mappe neu oeffnen, die Aenderung darauf wiederholen, dann "
            f"speichern."
        )

    gesaeubert, ersetzt = _saeubere(projekt)
    gesaeubert["zuletzt_gespeichert"] = _jetzt()
    gesaeubert["regel3_ersetzt"] = ersetzt
    # HOCHGEZAEHLT WIRD AUF DEM, WAS AUF DER PLATTE LIEGT, nicht auf dem eigenen Stand.
    # Sonst schriebe ein Aufrufer, der zweimal dasselbe Projekt-Woerterbuch speichert,
    # zweimal dieselbe Nummer — und die dritte Partei haelt beide fuer denselben Stand.
    gesaeubert["stand_nr"] = max(meiner, drueben or 0) + 1
    # WAS IM ARBEITSSPEICHER LIEGT, ZIEHT MIT. Sonst traegt der Aufrufer nach dem
    # Speichern eine alte Nummer und faellt beim naechsten Speichern ueber sich selbst.
    projekt["stand_nr"] = gesaeubert["stand_nr"]

    text = json.dumps(gesaeubert, indent=2, ensure_ascii=False) + "\n"
    fd, temp = tempfile.mkstemp(dir=str(wurzel), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as datei:
            datei.write(text)
            datei.flush()
            os.fsync(datei.fileno())
        os.replace(temp, ziel)
    except BaseException:
        Path(temp).unlink(missing_ok=True)
        raise
    return ziel


def _saeubere(wert):
    """Rekursiv durch das Projekt — Zeichenketten, Listen, Wörterbücher, auch Schlüssel."""
    if isinstance(wert, str):
        return ohne_kennungen(wert)
    if isinstance(wert, dict):
        neu_dict, gesamt = {}, 0
        for schluessel, inhalt in wert.items():
            s2, ns = _saeubere(schluessel) if isinstance(schluessel, str) else (schluessel, 0)
            i2, ni = _saeubere(inhalt)
            neu_dict[s2] = i2
            gesamt += ns + ni
        return neu_dict, gesamt
    if isinstance(wert, (list, tuple)):
        neu_liste, gesamt = [], 0
        for eintrag in wert:
            e2, n = _saeubere(eintrag)
            neu_liste.append(e2)
            gesamt += n
        return neu_liste, gesamt
    return wert, 0


def oeffne(wurzel) -> dict:
    """Ein Projekt öffnen — **und sagen, ob das Modell noch dasselbe ist.**

    Returns:
        ``{projekt, modell_stand, modell_grund, pfad}``.

        ``modell_stand`` ist einer von :data:`MODELL_UNVERAENDERT`,
        :data:`MODELL_VERAENDERT`, :data:`MODELL_FEHLT`, :data:`MODELL_NICHT_PRUEFBAR`.
        ``modell_grund`` ist ein Satz für einen Menschen.

    Raises:
        ProjektError: Kein Projekt an diesem Ort, unlesbare Datei, oder ein Schema, das
            dieses Programm nicht kennt.

    **Es wird nichts repariert und nichts neu gerechnet.** Ein Projekt, dessen Modell sich
    geändert hat, öffnet sich normal und meldet es. Die bisherigen Messungen bleiben
    stehen — sie gehören zum alten Stand und gelten dafür weiter.

        *Wer beim Öffnen still neu rechnet, nimmt dem Benutzer die Möglichkeit, zwei
        Stände zu vergleichen — und das ist der häufigste Grund, überhaupt zwei zu haben.*
    """
    wurzel = Path(wurzel)
    pfad = wurzel / PROJEKTDATEI
    if not pfad.exists():
        raise ProjektError(
            f"In {wurzel} liegt kein Projekt ({PROJEKTDATEI} fehlt). Ein neues legt "
            f"`neu()` an.")
    try:
        projekt = json.loads(pfad.read_text(encoding="utf-8"))
    except (OSError, ValueError) as fehler:
        raise ProjektError(
            f"Die Projektdatei liess sich nicht lesen: {fehler}. Sie ist Text — ein Blick "
            f"hinein zeigt meist, an welcher Stelle sie abgebrochen ist.") from fehler

    if not isinstance(projekt, dict) or projekt.get("schema") != SCHEMA:
        raise ProjektError(
            f"Unbekanntes Projektformat: {projekt.get('schema') if isinstance(projekt, dict) else '—'!r}. "
            f"Dieses Programm kennt {SCHEMA!r}. Eine Datei aus einer neueren Fassung wird "
            f"NICHT versuchsweise gelesen: Was dabei fehlt, fiele niemandem auf.")

    modell = projekt.get("modell") or {}
    stand, grund = _modellstand(modell.get("abdruck") or {},
                                fingerabdruck(loese_pfad(modell.get("pfad"), wurzel)))
    return {"projekt": projekt, "modell_stand": stand, "modell_grund": grund, "pfad": pfad}


def _zahl_oder_none(wert, name: str):
    """Eine Messzahl für die Mappe — eine endliche Zahl oder ``None``, nie etwas Drittes.

    ``True`` ist in Python eine Zahl (``True == 1``) und wäre hier ein Score von 1.0, der
    aussieht wie gemessen. Darum wird ein Wahrheitswert abgewiesen, wie beim Urteil.
    """
    if wert is None:
        return None
    if isinstance(wert, bool) or not isinstance(wert, (int, float)):
        raise ProjektError(
            f"{name} ist eine Zahl oder None (nicht gemessen) — war {wert!r} "
            f"({type(wert).__name__}).")
    if not math.isfinite(float(wert)):
        raise ProjektError(
            f"{name} ist {wert!r} — keine endliche Zahl. Ein solcher Wert ist keine "
            f"Messung; nicht gemessen heisst None.")
    return float(wert)


def vermerke_bild(projekt: dict, *, bild: str, schicht: str, urteil=None,
                  basis: dict | None = None, herkunft: dict | None = None,
                  score=None, schwelle=None, entwurf: bool = False,
                  variantengruppe: dict | None = None) -> dict:
    """Ein erzeugtes Bild ins Projekt eintragen — **samt der Frage, ob es geprüft ist.**

    Args:
        bild: Dateiname des Bildes, relativ zum Projektordner.
        schicht: ``"geometrielayer"`` oder ``"ai-imaging-layer"`` (E20).
        urteil: Das Geometrie-Urteil: ``True``, ``False`` oder ``None``.
            **``None`` heisst NICHT GEMESSEN** und nie «in Ordnung».
        basis: Bei einem Bild der zweiten Stufe das Urteil seiner Unterlage — unter einem
            **anderen** Feldnamen, nie unter ``urteil``.
        herkunft: Womit es entstand (Backbone, Prompt, Startwert, Führung …).
        score, schwelle: **Die Zahl zum Urteil** (Entscheid 16: «Farbe, Wort und Zahl»),
            aus der Prüfung, die das Urteil gefällt hat. ``None`` heisst **nicht
            gemessen** — nie 0. Seit dem 22.09.2026; ältere Einträge führen die Felder
            nicht, und ihr Fehlen heisst dasselbe.
        entwurf: ``True`` für ein Bild aus einem Entwurfslauf (Entscheid 30: schnell,
            ohne Geometrieprüfung). Ein eigenes Feld, damit eine Anzeige das blaue
            Zeichen «Entwurf — nicht geprüft» von einem gewöhnlichen «nicht gemessen»
            unterscheiden kann, ohne einen Satz zu deuten. Ein Entwurf **mit** Urteil
            wird abgewiesen: Ein Entwurf ist nicht geprüft.
        variantengruppe: ``{id, art, nummer, von}`` für ein Bild aus einer Variantenreihe
            (Entscheid 32), sonst ``None``.

    Returns:
        Das geänderte Projekt. Es ist **nicht geschrieben** — dafür gibt es
        :func:`speichere`.

    **Warum das Urteil ein Pflichtfeld ist und kein Zusatz.** Ein Eintrag ohne Urteilsfeld
    liest sich später wie «war wohl in Ordnung». Hier steht immer eines da, und wenn nicht
    gemessen wurde, steht das ausdrücklich.
    """
    # `is` UND NICHT `in`, und das ist hier kein Stil, sondern ein gefangener Fehler.
    #
    # In Python gilt `1 == True` und `0 == False`. Ein `urteil not in (True, False, None)`
    # laesst darum die Zahlen 1 und 0 durch — sie landeten als Urteil in der Projektdatei
    # und saehen dort aus wie eine Entscheidung. Gefunden von der eigenen Probe am
    # 21.09.2026, beim ersten Lauf.
    #
    #     *Eine Zahl, die sich als Urteil ausgibt, ist schlimmer als gar keines: Sie
    #     beantwortet die Frage, ohne sie gestellt zu haben.*
    if urteil is not True and urteil is not False and urteil is not None:
        raise ProjektError(
            f"urteil ist True, False oder None (nicht gemessen) — war {urteil!r} "
            f"({type(urteil).__name__}). Eine vierte Möglichkeit gibt es nicht, und eine "
            f"Zahl oder ein Text an dieser Stelle wäre eine Meinung, wo ein Urteil "
            f"stehen muss.")
    if schicht not in ("geometrielayer", "ai-imaging-layer"):
        raise ProjektError(
            f"schicht ist 'geometrielayer' oder 'ai-imaging-layer' — war {schicht!r}.")
    if entwurf is not True and entwurf is not False:
        raise ProjektError(f"entwurf ist True oder False — war {entwurf!r}.")
    if entwurf and urteil is not None:
        # EIN ENTWURF IST NICHT GEPRUEFT (Entscheid 30). Traegt er trotzdem ein Urteil,
        # stuende am Bild zweierlei — das blaue Zeichen und ein gruenes oder rotes.
        raise ProjektError(
            f"Ein Entwurf ist nicht geprüft — ein Urteil ({urteil!r}) dazu wäre eine "
            f"Auskunft, die der Lauf nicht hatte.")
    if variantengruppe is not None and not isinstance(variantengruppe, dict):
        raise ProjektError(
            f"variantengruppe ist ein Wörterbuch {{id, art, nummer, von}} oder None — "
            f"war {type(variantengruppe).__name__}.")
    score = _zahl_oder_none(score, "score")
    schwelle = _zahl_oder_none(schwelle, "schwelle")

    # EINE DATEI, EIN EINTRAG — und das ist eine Entscheidung, keine Aufräumarbeit.
    #
    # **Gemessen am 21.09.2026:** Dreimal «Rechnen» ohne Änderung ergab dreimal denselben
    # Bildnamen in der Liste. Mit eingeschaltetem Zwischenspeicher ist es sogar dieselbe
    # DATEI — der zweite Lauf hat sie gar nicht neu erzeugt.
    #
    #     *Eine Liste von Bildern, in der dieselbe Datei dreimal steht, ist keine Liste
    #     von Bildern — sie ist eine Liste von Klicks.*
    #
    # Die Läufe stehen weiterhin vollständig unter `laeufe`. Was hier geführt wird, ist
    # das Erzeugnis, und das gibt es einmal.
    #
    # **Der neueste Eintrag gewinnt**, denn ein Urteil kann sich ändern, ohne dass sich
    # die Datei ändert: Wer die Schwelle verschiebt, misst dasselbe Bild neu. Die alte
    # Fassung stünde sonst neben der neuen und sähe aus wie ein zweites Bild.
    vorher = None
    for i, alt_eintrag in enumerate(projekt.get("bilder") or []):
        if alt_eintrag.get("bild") == str(bild):
            vorher = i
            break

    eintrag = {
        "bild": str(bild),
        "schicht": schicht,
        # WANN ZUERST, und wann zuletzt. Beide, weil beide etwas sagen: Das erste Mal ist
        # die Herkunft, das letzte Mal die Aktualitaet des Urteils.
        "erzeugt": (projekt["bilder"][vorher]["erzeugt"]
                    if vorher is not None else _jetzt()),
        "zuletzt_vermerkt": _jetzt(),
        # DER EIGENE NAME UEBERLEBT DAS NEURECHNEN (Entscheid 19: «nach der Zeit, ein
        # eigener Name nachtraeglich moeglich»). Derselbe Grund wie bei `erzeugt`: Wer
        # ein Bild benannt hat und es erneut vermerkt bekommt, hat es nicht umbenannt.
        "titel": (projekt["bilder"][vorher].get("titel")
                  if vorher is not None else None),
        # DAS EIGENE URTEIL HEISST `geometrie_bestanden`, das geerbte steht im Block
        # `basis` unter demselben Namen — aber eine Ebene tiefer. Ein geerbtes Urteil ist
        # kein eigenes, und die beiden duerfen nie in DEMSELBEN Feld stehen (E20).
        "geometrie_bestanden": urteil,
        "geometrie_gemessen": urteil is not None,
        # DIE ZAHL ZUM URTEIL, aus derselben Pruefung (22.09.2026). `None` heisst nicht
        # gemessen; eine 0 an dieser Stelle hiesse «gemessen und ganz schlecht».
        "score": score,
        "schwelle": schwelle,
        "entwurf": entwurf,
        "variantengruppe": dict(variantengruppe) if variantengruppe else None,
        "basis": dict(basis) if basis else None,
        "herkunft": dict(herkunft or {}),
    }
    if vorher is not None:
        # AN DERSELBEN STELLE, nicht hinten angehaengt. Die Reihenfolge einer
        # Bilderliste ist eine Auskunft — wer sie beim Neurechnen umstellt, nimmt sie ihr.
        projekt["bilder"][vorher] = eintrag
    else:
        projekt.setdefault("bilder", []).append(eintrag)
    return projekt


#: Was mit einer Skizze geschehen ist. Drei Zustände, und der mittlere ist der, den es
#: sonst nirgends gäbe.
SKIZZE_OFFEN = "offen"          #: gezeichnet, noch nicht gerechnet
SKIZZE_GERECHNET = "gerechnet"  #: ein Bild ist daraus entstanden
SKIZZE_VERWORFEN = "verworfen"  #: bewusst liegengelassen

SKIZZEN_STAENDE = (SKIZZE_OFFEN, SKIZZE_GERECHNET, SKIZZE_VERWORFEN)


def vermerke_skizze(projekt: dict, *, skizze: str, ueber: str | None = None,
                    stand: str = SKIZZE_OFFEN, bemerkung: str = "") -> dict:
    """Eine Skizze ins Projekt eintragen — **die Eingabe des Entwurfsmodus** (E23).

    Args:
        skizze: Dateiname der Skizze, relativ zum Projektordner.
        ueber: Das Bild, auf das gezeichnet wurde — oder ``None`` für eine Skizze auf
            leerem Grund. ``None`` heisst hier wirklich *ohne Unterlage* und nicht
            *unbekannt*: Wer auf etwas zeichnet, weiss, worauf.
        stand: Einer aus :data:`SKIZZEN_STAENDE`.
        bemerkung: Was gemeint war. Freitext, für einen Menschen.

    Returns:
        Das geänderte Projekt. **Nicht geschrieben** — dafür gibt es :func:`speichere`.

    **Warum eine Skizze überhaupt in die Mappe gehört, und nicht bloss als Datei daneben.**
    Sie ist im Entwurfsmodus die *Bestellung*: Sie sagt, was hinzukommen soll. Ein Bild
    daraus ist später nur zu verstehen, wenn danebensteht, **worauf** gezeichnet wurde —
    dieselbe Geometrie, ein anderer Gedanke.

        *Eine Zeichnung ohne ihre Unterlage ist ein Strichbild. Erst zusammen sind sie
        ein Entwurf.*

    **Und `stand` ist ein Pflichtfeld aus demselben Grund wie das Urteil am Bild.** Eine
    Skizze, die dasteht und von der niemand weiss, ob je etwas daraus wurde, sieht nach
    zwei Wochen aus wie erledigt. Der Vorgabewert ist darum ``offen`` und nicht leer —
    *gezeichnet ist nicht gerechnet.*
    """
    if stand not in SKIZZEN_STAENDE:
        raise ProjektError(
            f"stand ist einer aus {', '.join(SKIZZEN_STAENDE)} — war {stand!r}. "
            f"Ein erfundener Zustand wäre eine Auskunft, die niemand einlösen kann.")
    if not skizze or not str(skizze).strip():
        raise ProjektError(
            "skizze ist der Dateiname der Zeichnung und darf nicht leer sein.")
    if ueber is not None and not str(ueber).strip():
        raise ProjektError(
            "ueber ist entweder ein Bildname oder None (ohne Unterlage) — eine leere "
            "Zeichenkette ist beides nicht, und sie sähe in der Mappe aus wie 'None'.")

    eintrag = {
        "skizze": str(skizze),
        "ueber": str(ueber) if ueber is not None else None,
        "erzeugt": _jetzt(),
        "stand": stand,
        "bemerkung": str(bemerkung),
        # WAS DARAUS WURDE, als eigenes Feld. `None` heisst: noch nichts. Es hier
        # wegzulassen hiesse, den Zusammenhang spaeter aus Zeitstempeln zu raten.
        "ergebnis": None,
        # DER EIGENE NAME, nachtraeglich (Entscheid 19). `None` heisst: benannt nach der
        # Zeit, wie die Datei. Siehe `benenne`.
        "titel": None,
    }
    projekt.setdefault("skizzen", []).append(eintrag)
    return projekt


def _skizzeneintraege(projekt: dict, skizze: str) -> list[dict]:
    return [e for e in (projekt.get("skizzen") or [])
            if isinstance(e, dict) and e.get("skizze") == str(skizze)]


def markiere_skizze(projekt: dict, *, skizze: str, stand: str,
                    ergebnis=None) -> dict:
    """Den Stand einer Skizze nachführen — **und was daraus wurde**.

    Args:
        skizze: Der Dateiname, wie er in der Mappe steht.
        stand: Einer aus :data:`SKIZZEN_STAENDE`.
        ergebnis: Was daraus wurde — ein Bildname, eine Liste von Bildnamen, oder
            ``None`` (noch nichts). Bei ``gerechnet`` Pflicht: *Gerechnet ohne Ergebnis*
            wäre ein Zustand, den niemand einlösen kann.

    Returns:
        Das geänderte Projekt, **nicht geschrieben**.

    Raises:
        ProjektError: Die Skizze steht nicht (oder mehrfach) in der Mappe, der Stand ist
            unbekannt, oder «gerechnet» kommt ohne Ergebnis.
    """
    if stand not in SKIZZEN_STAENDE:
        raise ProjektError(
            f"stand ist einer aus {', '.join(SKIZZEN_STAENDE)} — war {stand!r}.")
    if stand == SKIZZE_GERECHNET and not ergebnis:
        raise ProjektError(
            "Eine Skizze ist erst «gerechnet», wenn ein Bild daraus entstanden ist — "
            "ohne Ergebnis bleibt sie offen.")
    treffer = _skizzeneintraege(projekt, skizze)
    if len(treffer) != 1:
        raise ProjektError(
            f"Die Skizze {skizze!r} steht {len(treffer)}-mal in der Mappe. Nachgeführt "
            f"wird nur ein Eintrag, der eindeutig ist — bei zweien wäre die Wahl geraten.")
    treffer[0]["stand"] = stand
    treffer[0]["ergebnis"] = (list(ergebnis) if isinstance(ergebnis, (list, tuple))
                              else ergebnis)
    return projekt


#: Wie lang ein eigener Name höchstens sein darf. **GESETZT, nicht gemessen:** lang
#: genug für einen Satz wie «Variante Süd mit Holzfassade, Abendlicht», kurz genug, dass
#: er unter ein Vorschaubild passt. Ein Name ist keine Bemerkung — die hat ihr Feld.
TITEL_HOECHSTENS = 120


def benenne(wurzel, *, titel: str | None, bild: str | None = None,
            skizze: str | None = None, von_stand: int | None = None) -> dict:
    """Einem Bild oder einer Skizze **nachträglich** einen eigenen Namen geben (E19).

    Die **Datei bleibt, wie sie heisst.** Der Name ist eine Anzeige und steht als
    ``titel`` am Eintrag; der Dateiname trägt weiter die Zeit, und alles, was auf die
    Datei zeigt (die Skizze auf ihr Bild, ein Lauf auf seine Ausgabe), zeigt weiter.

        *Umbenennen hiesse, jeden Verweis mitzunehmen — und der eine, den man vergisst,
        zeigt danach auf nichts.*

    Args:
        wurzel: Der Projektordner.
        titel: Der neue Name. ``None`` oder leer nimmt ihn zurück — dann gilt wieder der
            Name nach der Zeit.
        bild, skizze: **Genau eines** davon — der Dateiname, wie er in der Mappe steht.
        von_stand: Die Standnummer, von der der Aufrufer kommt (``stand_nr`` aus seinem
            letzten Öffnen). Gesetzt, wird wie bei :func:`speichere` abgelehnt, wenn auf
            der Platte ein neuerer Stand liegt — wer einen alten Stand vor Augen hatte,
            benennt womöglich ein Bild, das es drüben nicht mehr so gibt. ``None``: Die
            Mappe wird frisch geöffnet, und nur ein Schreiber im selben Augenblick
            kollidiert.

    Returns:
        ``{projekt, eintrag, pfad}`` — das Projekt ist **geschrieben**.

    Raises:
        ProjektError: Nicht genau eines von ``bild``/``skizze``, der Eintrag fehlt (oder
            steht bei einer Skizze mehrfach da), oder der Name ist unbrauchbar (zu lang,
            mit Zeilenumbruch oder Steuerzeichen).
        ProjektKollision: Auf der Platte liegt ein neuerer Stand als ``von_stand``.
    """
    if (bild is None) == (skizze is None):
        raise ProjektError(
            "Genau eines von bild und skizze — sonst ist nicht bestimmt, was den Namen "
            "bekommt.")
    if titel is not None and not isinstance(titel, str):
        raise ProjektError(f"titel ist Text oder None — war {type(titel).__name__}.")
    titel = (titel or "").strip() or None
    if titel is not None:
        if len(titel) > TITEL_HOECHSTENS:
            raise ProjektError(
                f"Der Name ist {len(titel)} Zeichen lang, höchstens {TITEL_HOECHSTENS} "
                f"gehen. Was länger ist, gehört in die Bemerkung.")
        if any(ord(z) < 32 or ord(z) == 127 for z in titel):
            raise ProjektError(
                "Der Name enthält einen Zeilenumbruch oder ein Steuerzeichen. Ein Name "
                "steht auf einer Zeile unter dem Bild.")

    auf = oeffne(wurzel)
    p = auf["projekt"]
    if bild is not None:
        treffer = [e for e in (p.get("bilder") or [])
                   if isinstance(e, dict) and e.get("bild") == str(bild)]
        wofuer = f"Das Bild {bild!r}"
    else:
        treffer = _skizzeneintraege(p, skizze)
        wofuer = f"Die Skizze {skizze!r}"
    if not treffer:
        raise ProjektError(f"{wofuer} steht nicht in dieser Mappe.")
    if len(treffer) > 1:
        raise ProjektError(
            f"{wofuer} steht {len(treffer)}-mal in der Mappe. Benannt wird nur ein "
            f"Eintrag, der eindeutig ist — bei zweien wäre die Wahl geraten.")
    treffer[0]["titel"] = titel

    if von_stand is not None:
        if isinstance(von_stand, bool) or not isinstance(von_stand, int):
            raise ProjektError(f"von_stand ist eine ganze Zahl — war {von_stand!r}.")
        # DER STAND DES AUFRUFERS ZAEHLT, nicht der eben gelesene. Sonst waere die
        # Pruefung in `speichere` hier immer bestanden.
        p["stand_nr"] = von_stand
    pfad = speichere(p, wurzel)
    return {"projekt": p, "eintrag": treffer[0], "pfad": pfad}
