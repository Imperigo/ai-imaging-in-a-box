"""Der **Arbeitsgang** — hier kommen Import, Kette und Projekt zusammen.

Warum es diese Schicht gibt und warum sie dünn ist
--------------------------------------------------
Seit dem 21.09.2026 gibt es zwei neue Bausteine: :mod:`aiimaging.importeur` holt ein
Modell herein, :mod:`aiimaging.projekt` hält fest, was daraus wurde. Beide waren
**an keiner Stelle verdrahtet** — sie konnten etwas, und niemand rief sie.

    *Ein gebautes Modul ohne Aufrufer ist kein Werkzeug, sondern ein Vorrat.*

Dieses Modul ist der Aufrufer. Es ist die **einzige** Stelle, an der die drei zusammen
vorkommen, und es tut selbst nichts: Es wandelt nicht um, es rendert nicht, es misst
nicht. Es ruft in einer Reihenfolge, die begründbar ist, und schreibt danach auf, was
herauskam.

**Warum das eine eigene Datei ist und nicht eine Funktion in einem der drei.**
Käme sie in :mod:`aiimaging.projekt`, müsste das Projekt die Kette kennen — und damit
wäre die Mappe, in der die Arbeit liegt, an die Art gebunden, wie gerechnet wird. Käme
sie in :mod:`aiimaging.kette`, müsste die Kette wissen, wohin ihr Ergebnis gehört.
Beides sind Kopplungen, die man später nicht mehr auflöst.

Zwei Entscheide, die man beim Lesen sofort merkt
------------------------------------------------
**1 · Ein verändertes Modell hält den Lauf an — aber es lässt sich übergehen.**
:func:`rechne` weigert sich, wenn das Modell seit dem letzten Öffnen ein anderes geworden
oder verschwunden ist. Das ist **nicht** dasselbe wie die Regel «beim Öffnen wird nichts
repariert»: Öffnen ist harmlos, *Rechnen schreibt ein Urteil in die Mappe.* Ein Urteil,
das gegen ein anderes Gebäude gemessen wurde und unter dem alten Modellnamen steht, ist
schlimmer als gar keines.

Wer es trotzdem will — etwa, um zwei Stände zu vergleichen —, sagt ``trotz_aenderung=True``.
Dann läuft es, **und an jedem erzeugten Bild steht, unter welchem Modellstand es entstand.**

    *Ein Riegel, den man nicht aufmachen kann, wird umgangen. Einer, dessen Öffnen im
    Ergebnis steht, wird benutzt und bleibt sichtbar.*

**2 · Jedes erzeugte Bild wird vermerkt — auch das ohne Urteil.**
Das Urteil kommt aus dem QA-Knoten desselben Laufs; gibt es keinen, steht ``None`` da.
Nicht «nichts», sondern ``None`` mit Grund. Ein Bild ohne Eintrag wäre später von einem
Bild ohne Prüfung nicht zu unterscheiden — und beide sähen aus wie ein bestandenes.

Was die App braucht (22.09.2026, Entscheide 16, 30, 31, 32)
------------------------------------------------------------
Die iPad-App zeigt, was in der Mappe steht — was die Mappe nicht trägt, kann sie nicht
zeigen. Seither trägt jedes Bild **Score und Schwelle** seiner Prüfung (``None``: nicht
gemessen), :func:`rechne` kennt den **Entwurf** (``entwurf=True``), die
**Variantenreihe** über Startwerte (``varianten=n``) und das **Anhalten**
(``abbrechen=``), und :func:`rechne_skizze` rechnet eine abgelegte Skizze — oder mehrere
als Ebenen-Reihe. Bewacht in ``tests/test_mappe_fuer_die_app.py``, über diesen Weg und
mit der Mappe frisch von der Platte.

Regel 4: Aufrufbar aus reinem Python. Die Ausführer der Kette lassen sich übergeben; ohne
GPU und ohne Blender läuft dieses Modul mit Attrappen vollständig durch.
"""
from __future__ import annotations

import copy
import datetime
import hashlib
import inspect
import json
import math
import secrets
import time
from pathlib import Path

from aiimaging import bildlesen, bildschreiben, importeur, kette, projekt, render
# DIE KLASSEN DIREKT, nicht das Modul: `graph` heisst hier unten der GRAPH
# dieses Laufs, und ein Modulname, den eine lokale Zuweisung verdeckt, ist
# ein Fehler, der erst beim Aufruf auffaellt.
from aiimaging.graph import ArtefaktCache, Graph, Knoten
# DERSELBE GRUND: `varianten` heisst in `rechne` die ANZAHL der Laeufe.
from aiimaging.varianten import VariantenError, saatreihe

__all__ = ["ANGABEFELDER", "ArbeitsgangError", "EINGANGSORDNER", "ENTWURF_SCHRITTE",
           "ENTWURF_VERMERK", "MESSFELDER", "NACHHOLEN_HOECHSTENS", "NEUTRALER_GRUND",
           "SKIZZEN_VORSATZ", "VARIANTEN_ARTEN", "VARIANTEN_EBENEN",
           "VARIANTEN_HOECHSTENS", "VARIANTEN_STARTWERTE", "entwurfsargumente",
           "lege_an", "pruefe_varianten", "rechne", "rechne_skizze",
           "setze_auf_unterlage"]


class ArbeitsgangError(ValueError):
    """Der Ablauf kann so nicht laufen — und der Satz sagt, was fehlt.

    **Nicht** für einen schlechten Lauf: Eine Kette, die scheitert, liefert ein Ergebnis
    mit ``status`` und ``error``, und das wird vermerkt statt geworfen. Geworfen wird nur,
    was den Lauf gar nicht erst zulässt.
    """


def lege_an(wurzel, modell, *, name: str | None = None,
            einstellungen: dict | None = None, timeout: float | None = None,
            _starte=None) -> dict:
    """Ein Modell hereinholen **und** die Mappe dazu anlegen — in einem Griff.

    Args:
        wurzel: Der Projektordner.
        modell: Die Modelldatei in irgendeinem Format aus :data:`importeur.WEGE`.
        name: Anzeigename des Projekts.
        einstellungen: Was der Lauf später braucht (Backbone, Auflösung, Prompt …).
        timeout: Gesamtfrist für die Umwandlung. **Nicht** für den Raumleser, der bei
            einer IFC seit dem 22.09.2026 zusätzlich einmal läuft (eigener Subprozess
            im ``.venv-ifc``, eigene Frist) — das Anlegen einer IFC dauert dadurch
            spürbar länger.

    Returns:
        ``{projekt, import_bericht, pfad}``. Das Projekt ist **geschrieben**.

    Raises:
        ArbeitsgangError: Die Umwandlung selbst ist gescheitert (Blender fehlt, Subprozess
            ohne Bericht). Ein **abgelehntes** Modell ist kein Fehler — es steht als
            Befund im Projekt, samt dem Satz, was zu tun wäre.

    **Warum die glb neben der Projektdatei landet und das Quellmodell nicht.**
    Das Quellmodell bleibt, wo es ist (*eine Kopie wäre eine zweite Wahrheit*). Die daraus
    gerechnete glb ist dagegen ein **Erzeugnis dieses Projekts** und gehört hinein: Sie
    entsteht hier, sie ist hier reproduzierbar, und sie hat ausserhalb keinen Ort.
    """
    wurzel = Path(wurzel)
    p = projekt.neu(wurzel, modell, name=name, einstellungen=einstellungen)

    zusatz = {}
    if timeout is not None:
        zusatz["timeout"] = timeout
    bericht = importeur.importiere(modell, wurzel / "modell.glb",
                                   _starte=_starte, **zusatz)

    # DER IMPORTBERICHT GEHOERT INS PROJEKT, und zwar vollstaendig. Er sagt, ueber welchen
    # Weg das Modell hereinkam und was dabei NICHT geprueft wurde (`treue`). Spaeter ist
    # das nicht mehr zu rekonstruieren: Die glb allein sagt nicht, woraus sie entstand.
    # DIE HOCHACHSE — und hier entscheidet sich, ob wir sie WISSEN oder nur glauben.
    #
    # glTF kennt kein Feld dafuer, und die Erzeuger im Oekosystem sind sich uneinig. Ein
    # Vorgabewert waere eine stille Verdrehung: Tiefenkarte, Kamera und Pruefung kippen
    # dann GEMEINSAM und sind darum in sich stimmig. *Ein Fehlschlag, der wie ein Erfolg
    # aussieht, wird nicht gefunden — er wird geglaubt.*
    #
    # Es gibt genau zwei Faelle, und sie sind verschieden viel wert:
    #
    #   UMGEWANDELT (Weg `ifc` oder `blender`) — dann ist die glb UNSER Erzeugnis, und
    #       beide Wege schreiben Y-up. Das ist keine Annahme ueber eine fremde Datei,
    #       sondern eine Tatsache ueber unseren eigenen Lauf; der Bericht sagt sie.
    #
    #   DURCHGEREICHT — dann ist es eine fremde glb, und wir wissen NICHTS. Hier wird
    #       nicht geraten. Der Lauf verlangt die Angabe spaeter ausdruecklich.
    hochachse = bericht.get("bericht", {}).get("up_axis") if bericht["status"] == "ok" else None
    steht_fest = bool(hochachse) and bericht["weg"] != importeur.WEG_DURCHGEREICHT

    p["import"] = {
        "status": bericht["status"],
        "weg": bericht["weg"],
        # RELATIV ZUR MAPPE. Die glb liegt DARIN — ein absoluter Pfad ueberlebt die
        # Saeuberung nach Regel 3 nicht und zeigt danach auf nichts. Gefunden am
        # 21.09.2026 von Beweis 31.
        "glb": projekt.pfad_fuer_die_mappe(bericht["glb_path"], wurzel)
               if bericht.get("glb_path") else bericht.get("glb_path"),
        "format": bericht["format"],
        "treue": bericht["treue"],
        "hochachse": hochachse if steht_fest else None,
        "hochachse_steht_fest": steht_fest,
        "hinweise": list(bericht.get("hinweise") or ()),
        "grund": bericht.get("grund"),
        "naechster_schritt": bericht.get("naechster_schritt"),
        "raeume": _raeume_beim_anlegen(modell, bericht, _starte),
    }
    pfad = projekt.speichere(p, wurzel)
    return {"projekt": p, "import_bericht": bericht, "pfad": pfad}


def _raeume_beim_anlegen(modell, bericht: dict, _starte) -> dict | None:
    """Die Räume einer IFC, **jetzt** gelesen — solange es die IFC noch gibt.

    **Der Befund (22.09.2026, nachgefahren):** Die Innenansicht war über die Oberfläche
    bestellbar, über die Mappe aber nicht lieferbar. Räume gibt es nur in der IFC; die
    Mappe rechnet später aus der umgewandelten glb, in der Wände und Böden Dreiecke ohne
    Raumbegriff sind. :func:`rechne` warf ``ifc_path`` weg, und jeder Lauf mit
    ``innenraum`` endete im Fehlerknoten «Innenansicht verlangt, aber kein Standpunkt».

    **Warum beim Anlegen und nicht bei jedem Lauf.** Beim Anlegen ist das Quellmodell
    sicher da, und die glb entsteht im selben Griff aus derselben Datei. Die Räume
    liegen in IFC-Koordinaten, dieselbe Annahme wie beim Einstieg über ``ifc_path`` —
    ob sie zur umgewandelten glb passen, ist **am Gerät unbestätigt**
    (``auf-20260922-141``). Bei jedem Lauf nachzulesen
    hiesse, einen Subprozess ins ``.venv-ifc`` pro Klick zu starten, und gegen eine IFC,
    die sich seither geändert haben kann.

    **Derselbe Weg wie beim IFC-Einstieg der Kette** (``kette._raeume_lesen``): Subprozess
    jenseits der Prozessgrenze, ein Fehlschlag hält nichts an und steht als Befund in der
    Raumliste (Regel 1, IfcOpenShell bleibt drüben).

    Returns:
        Die Raumliste, oder ``None`` — **nicht gelesen**: Das Modell kam nicht als IFC
        (eine glb, ein FBX … hat keinen Raumbegriff), oder der Import wurde abgelehnt.
        ``{"raeume": []}`` heisst dagegen: gelesen, keine gefunden.
    """
    if bericht.get("status") != "ok" or bericht.get("weg") != importeur.WEG_IFC:
        return None
    return kette._raeume_lesen(modell, _starte=_starte)


def _urteil_zu(graph, knoten_ergebnisse: dict, bild_knoten: str):
    """Welches Urteil gehört zu diesem Bildknoten? ``(urteil, grund, qa_id)``.

    ``urteil`` ist ``True``, ``False`` oder ``None`` — und ``None`` heisst **nicht
    gemessen**, mit einem Grund daneben. Widersprechen sich zwei Prüfungen über dasselbe
    Bild, ist das Urteil ebenfalls ``None``: *Eines auszuwählen hiesse, das andere zu
    verschweigen.*
    """
    passende = [k for k in sorted(graph.knoten)
                if graph.knoten[k].art == kette.ART_QA
                and len(graph.knoten[k].eingaenge) >= 2
                and graph.knoten[k].eingaenge[1] == bild_knoten]
    if not passende:
        return None, ("Zu diesem Bild gibt es in diesem Lauf keine Geometrie-Prüfung. "
                      "NICHT GEMESSEN — weder bestanden noch durchgefallen."), None

    urteile = []
    angehalten = []
    for k in passende:
        eintrag = knoten_ergebnisse.get(k) or {}
        if eintrag.get("status") == kette.STATUS_ABGEBROCHEN:
            angehalten.append(k)
        if eintrag.get("status") != kette.STATUS_OK:
            continue
        ausgaben = eintrag.get("ausgaben") or {}
        if "bestanden" in ausgaben:
            urteile.append((k, ausgaben["bestanden"], _grund_der_pruefung(k, ausgaben)))

    if not urteile and angehalten:
        # ANGEHALTEN, BEVOR GEPRUEFT WURDE (Entscheid 31) — ein eigener Satz, weil «nicht
        # gelaufen» hier einen Grund hat, den der Mensch selbst gesetzt hat.
        return None, (f"Der Lauf wurde angehalten, bevor die Prüfung "
                      f"{', '.join(angehalten)} an der Reihe war. Das Bild ist fertig, "
                      f"geprüft wurde es nicht. NICHT GEMESSEN — weder bestanden noch "
                      f"durchgefallen."), None
    if not urteile:
        return None, (f"Die Prüfung {', '.join(passende)} hat in diesem Lauf kein Urteil "
                      f"geliefert (nicht gelaufen, übersprungen oder gescheitert). "
                      f"NICHT GEMESSEN."), None
    werte = {w for _, w, _ in urteile}
    if len(werte) > 1:
        return None, (f"Mehrere Prüfungen urteilen über dasselbe Bild und widersprechen "
                      f"sich ({', '.join(k for k, _, _ in urteile)}). Eines auszuwählen "
                      f"hiesse, das andere zu verschweigen."), None
    qa_id, urteil, grund = urteile[0]
    return urteil, grund, qa_id


def _grund_der_pruefung(qa_id: str, ausgaben: dict) -> str:
    """Der Satz, mit dem eine Prüfung ihr Urteil begründet — **nie** ``None``.

    **Der Befund (22.09.2026):** Hier stand ``ausgaben.get("grund")``. Die
    Geometrieprüfung (``tiefenschaetzer.qa_gegen_soll`` über ``kette.qa_ausfuehrer``)
    liefert ihren Satz aber unter ``begruendung`` — nachgestellt am echten Ausführer mit
    einer Attrappe als Schätzer: ``begruendung`` gesetzt, ``grund`` fehlt. Am Bild stand
    darum zu **jedem** gemessenen Urteil der Grund ``None``. Nur der Weg «von Hand
    bearbeitet» (``nicht_anwendbar``) schreibt ``grund``; darum werden beide gelesen, und
    ``begruendung`` zuerst.

    **Ein leerer Satz zählt wie ein fehlender.** Das Urteil von ``qa_gegen_soll`` trägt
    heute immer einen gefüllten Satz; die Regel ist Vorsicht für einen Ausführer, der
    das nicht tut (``geometrie_qa`` legt in Teilergebnissen ``""`` an), kein Befund.
    Liefert die Prüfung gar keinen, steht das ausdrücklich da, statt ``None``.

    **Und ein Urteil ``None`` bekommt den Vorbehalt vorangestellt.** Fehlt der Maskenweg,
    setzt ``qa_gegen_soll`` ``bestanden`` auf ``None``, lässt die Begründung aber beim
    Score («Score 1.000 ≥ Schwelle 0.65 …»). Allein neben ein nicht gemessenes Bild
    gestellt, liest sich dieser Satz wie ein bestandenes Urteil. Der Handeingriff
    (``nicht_anwendbar``) sagt es selbst und bleibt, wie er ist.
    """
    satz = None
    for schluessel in ("begruendung", "grund"):
        wert = ausgaben.get(schluessel)
        if wert:
            satz = str(wert)
            break
    if satz is None:
        satz = f"Die Prüfung {qa_id} hat zu ihrem Urteil keine Begründung mitgeliefert."
    if ausgaben.get("bestanden") is None and ausgaben.get("nicht_anwendbar") is not True:
        satz = (f"Die Prüfung {qa_id} hat gerechnet, aber kein Urteil gefällt — NICHT "
                f"GEMESSEN, weder bestanden noch durchgefallen. Was sie dazu meldet: "
                f"{satz}")
    return satz


#: Die Sperrdatei in der Mappe. Sie verhindert, dass zwei Läufe gleichzeitig in
#: dieselbe Mappe schreiben.
SPERRDATEI = "lauf.sperre"

#: Ab wann eine Sperre als **liegengeblieben** gilt und übernommen werden darf.
#:
#: **Vier Stunden, und die Zahl ist eine Setzung mit Begründung.** Sie muss deutlich über
#: dem längsten erwarteten Lauf liegen: Der Multipass hat eine Gesamtfrist von fünfzehn
#: Minuten, und ein Bild auf dem Auslagerungsweg kann ein Vielfaches davon brauchen. Vier
#: Stunden sind auch dann noch reichlich, wenn jemand über Nacht eine Reihe fährt.
#:
#: *Eine Frist, die knapp über dem Normalfall liegt, bricht genau die Sperre, die gerade
#: am meisten schützt — die des langen Laufs.*
SPERRFRIST_S = 4 * 3600


def _sperralter(pfad: Path) -> float | None:
    """Wie alt diese Sperre ist — **vorsichtig gerechnet.**

    Zwei Quellen, und es gilt die **jüngere**:

    ``st_mtime``
        Wann das Dateisystem sagt, dass geschrieben wurde.
    der Inhalt
        Wann der Lauf selbst sagt, dass er begonnen hat.

    **Warum nicht einfach die eine.** Liegt die Mappe auf einem Netzlaufwerk, kommt
    ``st_mtime`` von der **Uhr des Servers** und ``time.time()`` von der des Rechners.
    Gehen die beiden auseinander — und das tun sie —, sieht eine frische Sperre alt aus.
    Sie würde übernommen, und der stille Datenverlust wäre zurück.

        *Eine Sperre, die eine falsch gehende Uhr aufbricht, ist keine Sperre. Sie ist
        eine Verzögerung.*

    **Die jüngere gewinnt**, und das ist die sichere Richtung: Im Zweifel wird **nicht**
    übernommen. Der Preis ist eine Mappe, die länger blockiert bleibt; die Meldung sagt,
    wie man sie löst. Der Preis der anderen Richtung wäre verlorene Arbeit, die niemand
    bemerkt.

    Returns:
        Das Alter in Sekunden, oder ``None`` — **unbekannt, nicht null.** Eine Sperre,
        deren Alter niemand kennt, wird nicht übernommen.
    """
    alter = []
    try:
        alter.append(time.time() - pfad.stat().st_mtime)
    except OSError:
        pass
    try:
        satz = json.loads(pfad.read_text(encoding="utf-8"))
        begonnen = datetime.datetime.fromisoformat(
            str(satz["begonnen"]).replace("Z", "+00:00"))
        alter.append((datetime.datetime.now(datetime.timezone.utc) - begonnen)
                     .total_seconds())
    except (OSError, ValueError, KeyError, TypeError):
        # EINE SPERRE OHNE LESBAREN INHALT ist nicht «alt», sondern unbekannt. Sie kann
        # von einem Lauf stammen, der gerade zwischen Anlegen und Schreiben steht.
        pass
    return min(alter) if alter else None


def _nimm_sperre(wurzel: Path) -> Path:
    """Die Mappe für diesen Lauf sperren — oder begründet ablehnen.

    **Der Anlass ist gemessen** (21.09.2026): Zwei Läufe gleichzeitig auf derselben Mappe
    meldeten **beide Erfolg**, und danach stand **ein** Bild und **ein** Lauf in der
    Mappe. Der zweite hatte den ersten überschrieben: Beide lesen die Mappe, beide
    schreiben sie, der letzte gewinnt.

        *Ein Fehlschlag, der wie ein Erfolg aussieht, wird nicht gefunden — er wird
        geglaubt.*

    Und es ist kein Laborfall: Sobald ein iPad und ein Rechner am selben Projekt hängen,
    ist das Montagmorgen.

    **Angelegt wird mit ``O_EXCL``** — das Betriebssystem entscheidet, wer zuerst da war.
    Eine Prüfung «gibt es die Datei schon?» mit anschliessendem Schreiben hätte genau
    dazwischen dieselbe Lücke wie das Problem, das sie lösen soll.

    **Und eine liegengebliebene Sperre blockiert nicht ewig.** Stirbt ein Lauf, bleibt
    seine Datei stehen; nach :data:`SPERRFRIST_S` darf der nächste sie übernehmen. *Eine
    Sperre, die man nur von Hand lösen kann, wird von Hand gelöscht — und zwar auch dann,
    wenn sie gerade zu Recht steht.*

    In der Datei stehen **Zeitpunkt und Prozessnummer, sonst nichts**: Kein Benutzer- und
    kein Rechnername (Regel 3).

    Raises:
        ArbeitsgangError: Es läuft schon einer, und seine Sperre ist frisch.
    """
    import os

    pfad = Path(wurzel) / SPERRDATEI
    try:
        kennung = os.open(pfad, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        alter = _sperralter(pfad)
        if alter is not None and alter > SPERRFRIST_S:
            # UEBERNOMMEN, und es steht im Lauf. Wer spaeter sucht, warum zwei Laeufe
            # dieselbe Mappe angefasst haben, findet hier den Grund.
            pfad.unlink(missing_ok=True)
            return _nimm_sperre(wurzel)
        raise ArbeitsgangError(
            f"In dieser Mappe läuft schon eine Rechnung"
            + (f" (seit {alter / 60:.0f} Minuten)" if alter is not None else "")
            + ".\n"
            f"Zwei gleichzeitige Läufe schreiben beide in dieselbe Projektdatei, und der "
            f"zweite überschriebe die Ergebnisse des ersten — BEIDE meldeten dabei "
            f"Erfolg.\n"
            f"Warten, bis der erste fertig ist. Ist er abgestürzt, wird die Sperre nach "
            f"{SPERRFRIST_S // 3600} Stunden von selbst frei; wer nicht warten will, "
            f"löscht {SPERRDATEI!r} in der Mappe.")

    with os.fdopen(kennung, "w", encoding="utf-8") as datei:
        # KEIN BENUTZER- UND KEIN RECHNERNAME (Regel 3, dieses Repo ist oeffentlich, und
        # eine Mappe wandert mit).
        json.dump({"begonnen": _jetzt_iso(), "pid": os.getpid()}, datei)
    return pfad


def _jetzt_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).replace(
        microsecond=0).isoformat().replace("+00:00", "Z")


#: Was die Bildstufe über ihren eigenen Lauf **misst** — und was bis zum 22.09.2026
#: nirgends in der Mappe ankam.
#:
#: **Der Befund (22.09.2026):** Der Lauf schrieb sechs Zusammenfassungsfelder in die
#: Mappe (Status, Dauer, Treffer …) und liess alles stehen, was die Renderstufe über
#: *diesen* Lauf gemessen hatte. Nachgestellt mit einem Knoten, der
#: ``modus_bestellt='image_edit'``, ``modus_gerechnet='txt2img'`` und den Satz
#: «BESTELLT WAR …» meldete: In der geschriebenen Projektdatei kam keines dieser
#: Wörter vor.
#:
#: Und es wiegt schwer, weil ``modus_abweichung`` am 21.09.2026 **eigens** verdrahtet
#: wurde — es war eine Funktion vor dem Leser weggeworfen worden. Eine Ebene später
#: wurde es wieder weggeworfen.
#:
#:     *Eine Auskunft, die eine Ebene früher wegfällt, als der Leser sie braucht, gibt
#:     es für den Leser nicht — und es ist gleichgültig, welche Ebene es war.*
MESSFELDER = ("modus_bestellt", "modus_gerechnet", "modus_abweichung",
              "hinweise", "schritte_gerechnet", "geraeteweg")


def _messung_zu(ausgaben: dict) -> dict:
    """Was ein Bildknoten über seinen Lauf gemeldet hat — **jedes Feld, auch das leere.**

    Ein Feld, das der Knoten nicht führt, steht hier als ``None``: **nicht gemessen.**
    Es wird nicht weggelassen und nicht auf ``False`` oder ``0`` gezogen — sonst wäre in
    der Mappe eine schweigende Naht von einer meldenden nicht zu unterscheiden, und
    genau diese Unterscheidung ist der Zweck von ``modus_abweichung``.

    ``hinweise`` ist der einzige Sonderfall: ``[]`` heisst **gemessen und nichts zu
    sagen**, ``None`` heisst **nicht gemessen**. Die beiden sind verschieden viel wert.
    """
    messung = {}
    for feld in MESSFELDER:
        # EINE EIGENE KOPIE, nicht der Wert aus dem Knotenergebnis. `geraeteweg` ist ein
        # Woerterbuch, und das Knotenergebnis geht als `lauf` an den Aufrufer zurueck.
        # Siehe `rechne`, Befund «geteilte Objekte» vom 22.09.2026.
        wert = copy.deepcopy(ausgaben.get(feld))
        if feld == "hinweise" and wert is not None:
            # TUPEL ZU LISTE — die Projektdatei ist JSON, und `hinweise` kommt aus
            # `render._ergebnis` als Tupel herein.
            wert = list(wert)
        messung[feld] = wert
    return messung


#: Was die Bildstufe über ihren Lauf **angibt**, ohne es zu messen — und was bis zum
#: 22.09.2026 auf dem Weg in die Mappe wegfiel.
#:
#: **Der Befund (22.09.2026):** ``render._ergebnis`` liefert neben den
#: :data:`MESSFELDER` auch ``lizenz`` (die Lizenzprüfung des benutzten Gewichts,
#: ``backbone.pruefe_lizenz``) und ``maengel`` (warum ein Auftrag abgelehnt wurde).
#: Keines der beiden kam in der Projektdatei an.
#:
#: **Getrennt von den Messfeldern, weil eine Lizenz keine Messung ist.** Sie steht im
#: Datensatz des Gewichts und nicht im Lauf; wer sie unter «gemessen» fände, hielte sie
#: für etwas, das dieser Lauf festgestellt hat.
#:
#: **Wo sie stehen, und warum an beiden Stellen.** An jedem Bild unter ``herkunft`` —
#: Regel 1 ist die Lizenz, und die Frage «unter welcher Lizenz entstand dieses Bild?»
#: stellt sich am einzelnen Bild, das womöglich ohne seinen Lauf weitergegeben wird. Und
#: im Lauf unter ``angaben`` je Bildknoten, **auch ohne Bild**: Ein abgelehnter Auftrag
#: hat kein Bild, und gerade seine ``maengel`` (oft die Lizenz selbst) fielen sonst weg.
#:
#: ``None`` heisst wie überall **nicht angegeben**. ``maengel == []`` heisst: geprüft
#: und nichts gefunden — die beiden sind verschieden viel wert.
ANGABEFELDER = ("lizenz", "maengel")


def _angaben_zu(ausgaben: dict) -> dict:
    """``lizenz`` und ``maengel`` eines Bildknotens — als eigene Kopie, ``None`` bleibt
    ``None``. Siehe :data:`ANGABEFELDER`."""
    angaben = {}
    for feld in ANGABEFELDER:
        wert = copy.deepcopy(ausgaben.get(feld))
        if feld == "maengel" and wert is not None:
            # TUPEL ZU LISTE, derselbe Grund wie bei `hinweise`.
            wert = list(wert)
        angaben[feld] = wert
    return angaben


#: Vorgabewert für ``cache``: der Zwischenspeicher liegt **in der Mappe**.
#:
#: **Eigenes Wort statt ``None``**, weil ``None`` in diesem Projekt überall
#: *nicht gemessen / nicht angefasst* heisst — und hier etwas anderes bedeuten müsste.
#: So bleibt ``cache=None`` ausdrücklich **kein Speicher**, und das ist prüfbar.
SPEICHER_IN_DER_MAPPE = "in-der-mappe"

#: Wie der Ordner des Zwischenspeichers in der Mappe heisst.
SPEICHERORDNER = "speicher"


#: Wieviele Diffusionsschritte ein **Entwurfslauf** höchstens rechnet (Entscheid 30:
#: «schnell, ohne Geometrieprüfung»).
#:
#: **GESETZT, nicht gemessen** (22.09.2026). Acht Schritte sind weniger als die Hälfte der
#: Vorgabe von :func:`aiimaging.kette.baue_kette` (20); wie viel Zeit das auf der
#: HomeStation spart und wie das Bild dabei aussieht, ist **am Gerät unbestätigt**. Die
#: Zahl steht an einer Stelle, damit sie nach der Messung an einer Stelle geändert wird.
ENTWURF_SCHRITTE = 8

#: Der Vermerk an jedem Bild eines Entwurfslaufs — das blaue Zeichen aus Entscheid 30.
#: Fester Anfang, damit eine Anzeige ihn erkennt, ohne den Rest zu deuten.
ENTWURF_VERMERK = "Entwurf — nicht geprüft"

#: Die zwei Arten einer Variantenreihe (Entscheid 32: «drei Startwerte oder drei
#: Ebenen»). Startwerte rechnet :func:`rechne`, Ebenen :func:`rechne_skizze`.
VARIANTEN_STARTWERTE = "startwerte"
VARIANTEN_EBENEN = "ebenen"
VARIANTEN_ARTEN = (VARIANTEN_STARTWERTE, VARIANTEN_EBENEN)

#: Wieviele Varianten eine Reihe höchstens hat. **GESETZT, nicht gemessen:** Entscheid 18
#: zeigt drei nebeneinander; acht lassen Luft für einen Vergleich, und eine Bestellung von
#: tausend über das Netz hielte die HomeStation nicht für Stunden fest.
VARIANTEN_HOECHSTENS = 8


def rechne(wurzel, *, trotz_aenderung: bool = False, ausfuehrer=None,
           cache=SPEICHER_IN_DER_MAPPE, melder=None, abbrechen=None,
           entwurf: bool = False, varianten: int | None = None,
           art: str = VARIANTEN_STARTWERTE, **kettenargumente) -> dict:
    """Die Kette für ein Projekt fahren — **und jedes Bild samt Urteil eintragen.**

    Args:
        wurzel: Der Projektordner.
        trotz_aenderung: ``True`` lässt rechnen, obwohl das Modell ein anderes geworden
            oder verschwunden ist. Der Modellstand steht dann **an jedem erzeugten Bild**.
        ausfuehrer: Knotenart → Funktion, wie bei :func:`aiimaging.kette.fuehre_aus`.
            Ohne Angabe die echten — dann braucht es Blender, Gewichte und eine GPU.
        cache: Zwischenspeicher der Kette. Vorgabe ist
            :data:`SPEICHER_IN_DER_MAPPE` — dann liegt er unter ``<mappe>/speicher``.
            ``None`` heisst ausdrücklich **kein Speicher**, jede Stufe rechnet.

            **Der Anlass ist gemessen** (21.09.2026): Bis dahin fuhr der Produktweg
            **ohne** Speicher. Drei Läufe hintereinander auf derselben Mappe ergaben
            ``cache_treffer=0`` — jeder Klick auf «Rechnen» rechnete den Blender-Lauf und
            das Bild neu, auch wenn sich nichts geändert hatte.

            *Der Zwischenspeicher ist gebaut, durch drei Beweise belegt — und auf dem Weg,
            den das Produkt geht, war er nicht eingeschaltet.* Dieselbe Sorte Lücke wie
            beim Schrittzähler am selben Tag.

            **Er liegt in der Mappe und nicht daneben**, damit eine kopierte Mappe ihren
            Speicher mitnimmt. Ein Eintrag, dessen Dateien fehlen, wird von
            ``fuehre_aus`` ohnehin verworfen — ein Umzug kostet darum höchstens einen
            neuen Lauf, nie ein falsches Ergebnis.
        melder: ``(ereignis: dict) -> None``, gerufen vor und nach jedem Knoten — und
            **zusätzlich nach jedem Diffusionsschritt** der Bildstufe. ``None`` heisst:
            niemand sieht zu.

            Die Schritte kommen als ``{"art": "schritt", "schritt": n}``. Sie sind der
            **einzige belegte Fortschritt** dieses Projekts: gezählt wird, was wirklich
            gerechnet wurde. Was ein Blender-Lauf meldet, ist dagegen ein *Lebens*zeichen
            und kein Fortschritt — die beiden dürfen in einer Anzeige nie gleich aussehen.

            Bei einer Variantenreihe kommt vor jeder Variante
            ``{"art": "variante_beginnt", "nummer": i, "von": n, "gruppe": id}`` — die
            Knotennummern beginnen danach wieder bei eins.

            **Der Zähler wird nur dann eingehängt, wenn kein eigener ``ausfuehrer``
            übergeben ist.** Wer die Tabelle selbst mitbringt, hat seine Gründe, und eine
            stille Ersetzung darin wäre genau die Sorte Überraschung, gegen die
            ``fuehre_aus`` die Tabelle ausdrücklich *ersetzen* statt ergänzen lässt.
        abbrechen: ``() -> bool``, gefragt vor jedem Knoten (Entscheid 31) — siehe
            :func:`aiimaging.kette.fuehre_aus` — und in einer Reihe **auch zwischen zwei
            Varianten** (seit dem 22.09.2026). Sagt sie ``True``, läuft kein Knoten mehr
            und **keine weitere Variante**; was fertig ist, wird wie immer vermerkt, und
            der Lauf steht mit ``abgebrochen: True`` in der Mappe. Kam das Anhalten
            zwischen zwei Varianten, lief die letzte regulär zu Ende: Dann ist der
            Rückgabewert ``abgebrochen: True``, der Lauf in der Mappe ``abgebrochen:
            False``, und an ihm steht ``varianten_nicht_begonnen``.
        entwurf: ``True`` rechnet einen **Entwurf** (Entscheid 30): höchstens
            :data:`ENTWURF_SCHRITTE` Schritte und **keine Geometrieprüfung**. Jedes Bild
            trägt ``entwurf: True``, das Urteil ``None`` und als Grund
            :data:`ENTWURF_VERMERK` — nie «bestanden». ``qa=True`` im selben Aufruf wird
            abgewiesen; ein ``qa`` aus den Einstellungen der Mappe wird überstimmt.
        varianten: ``None`` für einen Lauf, sonst 2 … :data:`VARIANTEN_HOECHSTENS` Läufe
            als **eine Variantenreihe** (Entscheid 32).
        art: Die Art der Reihe. Hier nur :data:`VARIANTEN_STARTWERTE`: Die Läufe
            unterscheiden sich **nur im Startwert**, nach der Vorschrift von
            :func:`aiimaging.varianten.saatreihe` (``seed``, ``seed+1``, …). Ebenen
            rechnet :func:`rechne_skizze`.
        **kettenargumente: alles Weitere an :func:`aiimaging.kette.baue_kette` (Prompt,
            Seed, Auflösung …). Was im Projekt unter ``einstellungen`` steht, wird
            **vorangestellt** und hier überschrieben — *die Mappe trägt die Vorgabe, der
            Aufruf das Besondere.*

    Returns:
        ``{projekt, lauf, laeufe, vermerkt, bilder, modell_stand, pfad, abgebrochen,
        variantengruppe, varianten_nicht_begonnen}``. ``lauf`` ist der letzte
        Kettenlauf, ``laeufe`` alle (einer je Variante); ``vermerkt`` ist die Zahl der
        eingetragenen Bilder, ``bilder`` ihre Namen. ``variantengruppe`` ist die Kennung
        der Reihe oder ``None``. Das Projekt ist **geschrieben**.

    Raises:
        ArbeitsgangError: Kein Modell zum Rechnen, das Modell hat sich geändert und
            ``trotz_aenderung`` ist nicht gesetzt, oder Entwurf/Varianten sind so nicht
            bestellbar.

    **Warum ein Lauf, der scheitert, trotzdem eingetragen wird.** Ein gescheiterter Lauf
    ist eine Tatsache über dieses Projekt. Ihn wegzuwerfen hiesse, dass zwei Zustände
    gleich aussehen: «wurde nie versucht» und «wurde versucht und ging nicht». Dasselbe
    gilt für einen abgebrochenen.

    **Und was der Lauf gemessen hat, wird mitgeschrieben** (22.09.2026). Im Lauf stehen
    ``modus_abweichungen`` (die Fälle, in denen etwas anderes gerechnet als bestellt
    wurde), ``modus_ungemessen`` (die Knoten, die dazu nichts gemeldet haben) und
    ``messungen`` je Bildknoten; dieselbe Messung hängt unter ``herkunft.messung`` an
    jedem eingetragenen Bild — **als eigene Kopie**, nicht als dasselbe Objekt. Siehe
    :data:`MESSFELDER`. Lizenz und Mängel der Bildstufe stehen im Lauf unter ``angaben``
    und am Bild unter ``herkunft.lizenz`` / ``herkunft.maengel``; siehe
    :data:`ANGABEFELDER`. Score und Schwelle der Prüfung stehen am Bild unter ``score``
    und ``schwelle`` — **nur, wenn die Prüfung geurteilt hat**; sonst dort ``None``, und
    die gemeldeten Werte stehen unter ``herkunft.messung.score``/``schwelle``.

    **Kollidiert das Speichern** mit einem fremden neueren Stand (ein Name, eine Skizze,
    die während des Laufs kamen), werden die Vermerke auf den frischen Stand
    nachgetragen; siehe :func:`_vermerke_und_speichere`.
    """
    pruefe_varianten(varianten, art)
    if art == VARIANTEN_EBENEN:
        raise ArbeitsgangError(
            "Ebenen-Varianten entstehen aus Skizzen — eine je Ebene. Sie rechnet "
            "rechne_skizze mit einer Liste von Skizzen; rechne kennt nur Startwerte.")
    return _unter_sperre(
        wurzel, trotz_aenderung=trotz_aenderung, ausfuehrer=ausfuehrer, cache=cache,
        melder=melder, abbrechen=abbrechen, entwurf=entwurf, varianten=varianten,
        skizzen=None, anweisung=None, kettenargumente=kettenargumente)


def rechne_skizze(wurzel, skizze, *, anweisung: str | None = None,
                  trotz_aenderung: bool = False, ausfuehrer=None,
                  cache=SPEICHER_IN_DER_MAPPE, melder=None, abbrechen=None,
                  entwurf: bool = False, **kettenargumente) -> dict:
    """Eine abgelegte Skizze **rechnen lassen** — sie wird zum Eingangsbild eines
    Nachrenders (:func:`aiimaging.kette.haenge_nachrender_an`).

    Args:
        wurzel: Der Projektordner.
        skizze: Der Dateiname einer Skizze der Mappe (``skizzen[].skizze``) — oder eine
            **Liste** von zweien bis :data:`VARIANTEN_HOECHSTENS`: Dann entsteht je Skizze
            ein Lauf, und alle Bilder tragen eine gemeinsame Variantengruppe der Art
            :data:`VARIANTEN_EBENEN` (Entscheid 32, «drei Ebenen»).
        anweisung: Was sich am Bild ändern soll — der Prompt des Nachrenders. ``None``
            nimmt die ``bemerkung`` der Skizze; ist die leer, wird abgewiesen.
            **Bewusst nicht** der Prompt der Mappe: Der beschreibt, was entstehen soll,
            diese Anweisung, was sich ändern soll (siehe ``haenge_nachrender_an``).
        trotz_aenderung, ausfuehrer, cache, melder, abbrechen, entwurf: wie bei
            :func:`rechne`.
        **kettenargumente: wie bei :func:`rechne`. Backbone, Startwert, Schritte,
            ControlNet-Stärke und ``denoise`` gehen an den Nachrender.

    Returns:
        Wie :func:`rechne`.

    Raises:
        ArbeitsgangError: Die Skizze steht nicht (oder mehrfach) in der Mappe, ist
            verworfen, ihre Datei fehlt, ihre Unterlage fehlt, eines der beiden Bilder ist
            kein lesbares PNG, oder es gibt keine Anweisung — sowie alles, was
            :func:`rechne` abweist.

    **Der Graph** ist ``geometrie → multipass → skizze-bildquelle → skizze-nachrender``,
    ohne ``geometrie → render``: Das Bild aus dem Modell braucht dieser Lauf nicht, und
    es zu rechnen kostete eine volle Bildstufe. Die Prüfung hängt an, wenn sie nicht
    abgeschaltet ist — sie urteilt auf einer Skizze **«nicht anwendbar»** (Owner-Entscheid
    19.09.2026), und genau dieser Satz steht dann am Bild.

    **Danach ist die Skizze «gerechnet»** und ihr ``ergebnis`` nennt das Bild — aber nur,
    wenn eines entstand. Scheitert der Lauf oder wird er angehalten, bleibt sie offen:
    *gezeichnet ist nicht gerechnet*, und angefangen auch nicht.

    **Das Eingangsbild ist die Skizze AUF IHRER UNTERLAGE** (seit dem 22.09.2026): dem
    Bild, das die Mappe unter ``ueber`` nennt, sonst :data:`NEUTRALER_GRUND` — mit dem
    Alphakanal verrechnet, siehe :func:`setze_auf_unterlage`. Es liegt unter
    :data:`EINGANGSORDNER` in der Mappe und steht am Bild unter ``herkunft.unterlage``.
    Nennt die Skizze eine Unterlage, die es nicht (mehr) gibt, wird abgewiesen.

    **Auf dem Vorgabemodell kommt die Skizze nicht an** (gemessen, ``auf-20260919-123``).
    Gerechnet wird trotzdem; der Satz :data:`aiimaging.kette.HINWEIS_SKIZZE_NICHT_ANGEKOMMEN`
    steht dann zuvorderst in ``herkunft.messung.hinweise`` am Bild.
    """
    if isinstance(skizze, (list, tuple)):
        namen = [str(s) for s in skizze]
    else:
        namen = [str(skizze)] if skizze is not None else []
    if not namen or any(not n.strip() for n in namen):
        raise ArbeitsgangError("Welche Skizze gerechnet werden soll, ist nicht gesagt.")
    if len(set(namen)) != len(namen):
        raise ArbeitsgangError(
            "Dieselbe Skizze steht zweimal in der Liste. Zwei Ebenen aus derselben "
            "Zeichnung wären dieselbe Variante unter zwei Namen.")
    if len(namen) > 1:
        pruefe_varianten(len(namen), VARIANTEN_EBENEN)
    return _unter_sperre(
        wurzel, trotz_aenderung=trotz_aenderung, ausfuehrer=ausfuehrer, cache=cache,
        melder=melder, abbrechen=abbrechen, entwurf=entwurf,
        varianten=len(namen) if len(namen) > 1 else None,
        skizzen=namen, anweisung=anweisung, kettenargumente=kettenargumente)


def pruefe_varianten(varianten, art) -> None:
    """Ist eine Reihe so bestellbar? Wirft :class:`ArbeitsgangError` mit Satz, sonst nichts.

    **Öffentlich seit dem 22.09.2026**, weil die Fläche sie ruft, damit eine falsche
    Bestellung sofort abgewiesen wird und nicht erst im Laufstand (Befund der Durchsicht
    D-SERVER: Sie rief die Funktion unter ihrem privaten Namen — eine Abhängigkeit, die
    beim nächsten Umbau still bricht).
    """
    if art not in VARIANTEN_ARTEN:
        raise ArbeitsgangError(
            f"art ist eine aus {', '.join(VARIANTEN_ARTEN)} — war {art!r}.")
    if varianten is None:
        return
    if isinstance(varianten, bool) or not isinstance(varianten, int):
        raise ArbeitsgangError(
            f"varianten ist eine ganze Zahl oder None — war {varianten!r}.")
    if varianten < 2 or varianten > VARIANTEN_HOECHSTENS:
        raise ArbeitsgangError(
            f"Eine Variantenreihe hat 2 bis {VARIANTEN_HOECHSTENS} Läufe, bestellt waren "
            f"{varianten}. Ein einzelner Lauf ist keine Reihe — dafür varianten=None.")


def _unter_sperre(wurzel, **angaben) -> dict:
    wurzel = Path(wurzel)
    # DIE SPERRE ZUERST, VOR DEM OEFFNEN. Laege sie spaeter, haette der zweite Lauf die
    # Mappe schon gelesen, bevor der erste sie geschrieben hat — und genau diese Kopie
    # wuerde er am Ende zurueckschreiben.
    sperre = _nimm_sperre(wurzel)
    try:
        return _rechne_gesperrt(wurzel, **angaben)
    finally:
        # AUCH BEIM SCHEITERN. Eine Sperre, die ein abgebrochener Lauf stehenlaesst,
        # blockiert die Mappe fuer Stunden — und der naechste Mensch sieht nur, dass
        # nichts geht.
        Path(sperre).unlink(missing_ok=True)


def _raeume_der_mappe(p: dict) -> dict | None:
    """Die Räume, die :func:`lege_an` in der Mappe abgelegt hat — oder ``None``.

    **Eine Mappe von vor dem 22.09.2026 trägt gar keinen Eintrag.** Kam ihr Modell als
    IFC, sind die Räume nicht «keine», sondern **nie gelesen** — und der Grund, den die
    Kette dann nennen würde («über eine glb eingestiegen … oder nichts gefunden»), wäre
    für diese Mappe falsch. Darum wird hier abgewiesen, mit dem Satz, was zu tun ist.

    Kam das Modell nicht als IFC, ist ``None`` die ehrliche Antwort, alt wie neu: Aus
    einer glb gibt es keinen Raumbegriff, und die Kette sagt das selbst.

    Raises:
        ArbeitsgangError: IFC-Mappe ohne Raumeintrag.
    """
    einfuhr = p.get("import") or {}
    if "raeume" not in einfuhr and einfuhr.get("weg") == importeur.WEG_IFC:
        raise ArbeitsgangError(
            "Eine Innenansicht ist bestellt, aber in dieser Mappe stehen keine Räume: Sie "
            "wurde angelegt, bevor die Mappe die Räume der IFC mitführte (22.09.2026). "
            "Gelesen wurden sie für diese Mappe nie — das heisst NICHT, dass das Modell "
            "keine hat.\n"
            "Die Mappe muss in einem neuen Projektordner neu angelegt werden (lege_an "
            "mit derselben IFC); dabei werden die Räume einmal gelesen. Aussenansichten "
            "rechnet diese Mappe weiterhin wie bisher.")
    return einfuhr.get("raeume")


def entwurfsargumente(args: dict, kettenargumente: dict) -> dict:
    """Die Einstellungen eines Entwurfslaufs: keine Prüfung, höchstens
    :data:`ENTWURF_SCHRITTE` Schritte. Siehe :func:`rechne`.

    Öffentlich aus demselben Grund wie :func:`pruefe_varianten`: Die Fläche rechnet
    damit die Schrittzahl, die sie vor dem Lauf ansagt.
    """
    if kettenargumente.get("qa") is True:
        raise ArbeitsgangError(
            "entwurf=True und qa=True im selben Aufruf widersprechen sich: Ein Entwurf "
            "ist der Lauf OHNE Geometrieprüfung (Entscheid 30). Für ein geprüftes Bild "
            "ohne entwurf rechnen.")
    vorgabe = inspect.signature(kette.baue_kette).parameters["schritte"].default
    schritte = args.get("schritte")
    try:
        schritte = vorgabe if schritte is None else int(schritte)
    except (TypeError, ValueError) as fehler:
        raise ArbeitsgangError(f"schritte ist keine ganze Zahl: {schritte!r}") from fehler
    return {**args, "qa": False, "schritte": min(schritte, ENTWURF_SCHRITTE)}


def _baue_grundgraph(glb: str, args: dict, p: dict):
    graph = kette.baue_kette(glb_path=glb, **args)
    # DIE RAEUME AUS DER MAPPE, ABER NUR BEI EINER INNENBESTELLUNG (Befund 22.09.2026).
    # Ohne `innenraum` bleiben Graph und Hash genau die bisherigen — sonst rechnete jeder
    # alte Lauf einer IFC-Mappe neu, nur weil jetzt Raeume in ihr stehen.
    if args.get("innenraum"):
        graph = kette.mit_raeumen(graph, _raeume_der_mappe(p))
    return graph


#: Der Namensvorsatz der Knoten eines Skizzenlaufs: ``skizze-bildquelle``,
#: ``skizze-nachrender``, ``skizze-qa``.
SKIZZEN_VORSATZ = "skizze"


#: Der Grund, auf den eine Skizze **ohne Unterlage** gesetzt wird: ein mittleres Grau.
#:
#: **Der Befund (22.09.2026):** Die App liefert Striche auf **durchsichtigem** Grund
#: (1536 x 1024, die Deckkraft steckt nur im Alphakanal), die Webfläche ebenso. Die
#: Bildstufe liest das Ausgangsbild ohne Alpha (``Image.open(…).convert("RGB")`` in
#: :mod:`aiimaging.render`) — durchsichtig wurde dort **schwarz**, und das Bild, auf das
#: gezeichnet wurde, kam gar nicht erst mit. Der Nachrender rechnete also auf roten
#: Strichen vor Schwarz.
#:
#: **Warum Grau, und warum GESETZT und nicht gemessen.** Ohne Unterlage gibt es kein
#: Bild, dessen Helligkeit das Ergebnis erben soll. **Angenommen, nicht gemessen**
#: (Durchsicht der Welle 2, 22.09.2026: Hier stand es wie ein Befund): Schwarz (der alte,
#: stille Zustand) zöge das Bild bei ``denoise`` unter eins ins Dunkle, Weiss ins
#: Überbelichtete — kein Lauf hat das je verglichen. Der dunkle Blattgrund der App
#: (#191d23) ist eine Bühnenfarbe und keine Aussage über das Bild. Die Mitte der Skala
#: drückt, so die Annahme, in keine Richtung. Ob ein anderes Grau (oder Grau überhaupt)
#: bessere Bilder gibt, ist **gesetzt, nicht gemessen**; die Zahl steht an einer Stelle.
#: Bewacht ist nur, dass der Grund dieser Konstante folgt und nicht Schwarz ist
#: (``tests/test_skizze_auf_unterlage.py``).
NEUTRALER_GRUND = (128, 128, 128)

#: Wohin in der Mappe das zusammengesetzte Eingangsbild eines Skizzenlaufs geschrieben
#: wird — ``<mappe>/eingang/<stamm>-<pruefsumme>.png``. In der Mappe, damit es mit ihr
#: umzieht und nachzusehen ist, was der Nachrender wirklich bekam. Den Namen bildet
#: :func:`_eingangsname`.
EINGANGSORDNER = "eingang"


def _rgba(pfad):
    """Ein PNG als vier Kanäle in 0..255 — ``(r, g, b, alpha | None, breite, hoehe)``.

    **Über** ``bildlesen._png_entpacken``, den eigenen PNG-Leser, und nicht über ein
    Bildpaket (Regel 1, keine neue Abhängigkeit). Die öffentlichen Leser dort übergehen
    den Alphakanal absichtlich (``lies_png_luminanz``, ``lies_png_farben``) — hier ist er
    der Gegenstand, darum der Weg eine Ebene tiefer.

    ``alpha`` ist ``None``, wenn die Datei keinen Alphakanal hat (Farbtyp 0 oder 2): Dann
    deckt jeder Bildpunkt ganz. Bei 16 Bit zählt das **höherwertige Byte** — eine Stufe
    von 256 Abweichung höchstens, für ein Eingangsbild der Bildstufe ohne Belang.
    Ein ``tRNS``-Block (eine einzelne durchsichtige Farbe) wird nicht gedeutet.

    Raises:
        bildlesen.BildError: keine PNG-Datei, beschädigt, verschränkt, Palette.
    """
    aus, breite, hoehe, bittiefe, farbtyp, _kanaele, bpp = bildlesen._png_entpacken(pfad)
    tief = bittiefe // 8

    def kanal(k: int) -> bytes:
        return bytes(aus[k * tief::bpp])

    if farbtyp == 0:
        grau = kanal(0)
        return grau, grau, grau, None, breite, hoehe
    if farbtyp == 4:
        grau = kanal(0)
        return grau, grau, grau, kanal(1), breite, hoehe
    if farbtyp == 2:
        return kanal(0), kanal(1), kanal(2), None, breite, hoehe
    return kanal(0), kanal(1), kanal(2), kanal(3), breite, hoehe


def _mische(oben: int, unten: int, alpha: int) -> int:
    """Ein Kanal: ``oben`` mit Deckung ``alpha`` (0..255) über ``unten``, gerundet."""
    return (oben * alpha + unten * (255 - alpha) + 127) // 255


def setze_auf_unterlage(skizze, ziel, *, unterlage=None) -> dict:
    """Eine Skizze auf ihre Unterlage setzen — **das Eingangsbild des Nachrenders.**

    Args:
        skizze: Die Zeichnung als PNG, üblicherweise mit durchsichtigem Grund.
        ziel: Wohin das Ergebnis geschrieben wird (8-Bit-RGB-PNG, ohne Alpha).
        unterlage: Das Bild, auf das gezeichnet wurde, als PNG — oder ``None``: Dann
            liegt die Skizze auf :data:`NEUTRALER_GRUND`.

    Returns:
        ``{bild, breite, hoehe, gestreckt}``. ``gestreckt`` ist ``True``, wenn Skizze
        und Unterlage nicht dasselbe Seitenverhältnis haben (mehr als ein Prozent).

    **Gerechnet wird mit dem Alphakanal**, Bildpunkt für Bildpunkt:
    ``Strich · α + Unterlage · (1 − α)``. Durchsichtig heisst Unterlage, halb deckend
    heisst halb — genau das, was die App auf dem Schirm zeigt, wenn eine Ebene mit
    halber Deckkraft über einem Bild liegt.

    **Die Grösse ist die der Unterlage.** Sie ist das Bild, das gegen die Tiefenkarte
    gerechnet wurde; ihre Bildpunkte bleiben unberührt, und die Skizze wird auf sie
    abgebildet — Blatt auf Bild, Rand auf Rand, beim Verkleinern als Kastenmittel mit
    Deckung gewichtet (ein dünner Strich wird blasser, verschwindet aber nicht). Dass die
    App die Unterlage **blattfüllend** zeigt, ist eine Annahme und **am Gerät
    unbestätigt**; weicht das Seitenverhältnis ab, wird gestreckt, und ``gestreckt``
    sagt es. Ohne Unterlage bleibt die Grösse der Skizze.

    Hat die Unterlage selbst einen Alphakanal, liegt sie zuerst auf dem neutralen Grund —
    sonst würde dort, wo sie durchsichtig ist, wieder Schwarz daraus.

    Raises:
        bildlesen.BildError: Skizze oder Unterlage sind kein lesbares PNG.
    """
    sr, sg, sb_, sa, s_breite, s_hoehe = _rgba(skizze)
    if unterlage is None:
        t_breite, t_hoehe = s_breite, s_hoehe
        n = t_breite * t_hoehe
        ur, ug, ub = (bytes([NEUTRALER_GRUND[0]]) * n, bytes([NEUTRALER_GRUND[1]]) * n,
                      bytes([NEUTRALER_GRUND[2]]) * n)
    else:
        ur, ug, ub, ua, t_breite, t_hoehe = _rgba(unterlage)
        if ua is not None:
            gr, gg, gb = NEUTRALER_GRUND
            ur = bytes(_mische(ur[i], gr, ua[i]) for i in range(len(ua)))
            ug = bytes(_mische(ug[i], gg, ua[i]) for i in range(len(ua)))
            ub = bytes(_mische(ub[i], gb, ua[i]) for i in range(len(ua)))

    gestreckt = abs(s_breite * t_hoehe - t_breite * s_hoehe) > 0.01 * t_breite * s_hoehe
    farben = []
    if (s_breite, s_hoehe) == (t_breite, t_hoehe):
        for i in range(t_breite * t_hoehe):
            a = 255 if sa is None else sa[i]
            if a == 255:
                farben.append((sr[i], sg[i], sb_[i]))
            elif a == 0:
                farben.append((ur[i], ug[i], ub[i]))
            else:
                farben.append((_mische(sr[i], ur[i], a), _mische(sg[i], ug[i], a),
                               _mische(sb_[i], ub[i], a)))
    else:
        # KASTENMITTEL, MIT DER DECKUNG GEWICHTET. Jeder Zielpunkt nimmt das Rechteck der
        # Skizze, das auf ihn faellt; die Farbe zaehlt nur so weit, wie sie deckt. Ein
        # ungewichtetes Mittel mischte das Schwarz der durchsichtigen Punkte (PencilKit
        # schreibt dort 0,0,0,0) in jeden Strichrand.
        zeilen = [(y * s_hoehe // t_hoehe, max(y * s_hoehe // t_hoehe + 1,
                                                (y + 1) * s_hoehe // t_hoehe))
                  for y in range(t_hoehe)]
        spalten = [(x * s_breite // t_breite, max(x * s_breite // t_breite + 1,
                                                   (x + 1) * s_breite // t_breite))
                   for x in range(t_breite)]
        j = 0
        for y0, y1 in zeilen:
            for x0, x1 in spalten:
                summe_a = summe_r = summe_g = summe_b = 0
                zahl = 0
                for zy in range(y0, y1):
                    for i in range(zy * s_breite + x0, zy * s_breite + x1):
                        a = 255 if sa is None else sa[i]
                        summe_a += a
                        summe_r += a * sr[i]
                        summe_g += a * sg[i]
                        summe_b += a * sb_[i]
                        zahl += 1
                voll = 255 * zahl
                rest = voll - summe_a
                farben.append(((summe_r + ur[j] * rest + voll // 2) // voll,
                               (summe_g + ug[j] * rest + voll // 2) // voll,
                               (summe_b + ub[j] * rest + voll // 2) // voll))
                j += 1

    ziel = Path(ziel)
    ziel.parent.mkdir(parents=True, exist_ok=True)
    bildschreiben.schreibe_farb_png(ziel, farben, t_breite, t_hoehe)
    return {"bild": ziel, "breite": t_breite, "hoehe": t_hoehe, "gestreckt": gestreckt}


def _eingangsname(skizze: str) -> str:
    """Der Dateiname des Eingangsbilds einer Skizze: ``<stamm>-<pruefsumme>.png``.

    **Eindeutig je Skizzenname** (Durchsicht der Welle 2, 22.09.2026): Bis dahin hiess es
    ``<stamm>.png``. Zwei Skizzen mit gleichem Stamm aus verschiedenen Unterordnern
    (``a/skizze.png``, ``b/skizze.png``) schrieben in einer Ebenen-Reihe **dieselbe
    Datei** — und weil alle Eingangsbilder vor dem ersten Lauf entstehen, rechneten beide
    Ebenen auf dem Eingang der zweiten. Die Prüfsumme (die ersten zwölf Zeichen des
    SHA-256 über den Namen, wie er in der Mappe steht) trennt sie; der Stamm bleibt
    davor, damit ein Mensch im Ordner sieht, wozu die Datei gehört.

    **Gleich bei jedem Lauf derselben Skizze**, und das mit Absicht: Eine laufende
    Nummer änderte den Pfad, der als Parameter in den Graphen geht, und damit jeden
    Zwischenspeicher-Schlüssel dahinter.
    """
    summe = hashlib.sha256(str(skizze).encode("utf-8")).hexdigest()[:12]
    return f"{Path(str(skizze)).stem}-{summe}.png"


def _eingangsbild(p: dict, wurzel: Path, name: str, pfad_skizze: Path, ueber) -> dict:
    """Die Skizze auf ihre Unterlage aus der Mappe setzen: ``{pfad, herkunft}``.

    ``ueber`` ist der Bildname, den die Mappe an der Skizze führt (``skizzen[].ueber``).
    **Er muss ein Bild dieser Mappe sein**, dessen Datei in der Mappe liegt. Fehlt es,
    wird abgewiesen, und zwar **nicht** still auf den neutralen Grund ausgewichen: Wer auf
    ein Bild gezeichnet hat, meinte dieses Bild. Ein Balkon vor Grau ist eine andere
    Bestellung als ein Balkon an diesem Haus — und sie sähe im Ergebnis aus wie die
    richtige.

    Raises:
        ArbeitsgangError: Die Unterlage steht nicht in der Mappe, liegt ausserhalb, fehlt,
            oder eines der beiden Bilder ist kein lesbares PNG.
    """
    unterlage = None
    if ueber is not None:
        kennt = [b for b in (p.get("bilder") or [])
                 if isinstance(b, dict) and b.get("bild") == ueber]
        if not kennt:
            raise ArbeitsgangError(
                f"Die Skizze {name!r} wurde auf {ueber!r} gezeichnet, aber dieses Bild steht "
                f"nicht in der Mappe. Ohne ihre Unterlage wird sie nicht gerechnet: Vor "
                f"einem neutralen Grund wäre es eine andere Bestellung, die aussieht wie "
                f"die richtige.")
        unterlage = Path(projekt.loese_pfad(ueber, wurzel))
        try:
            drin = unterlage.resolve().is_relative_to(Path(wurzel).resolve())
        except OSError:
            drin = False
        if not drin or not unterlage.is_file():
            raise ArbeitsgangError(
                f"Die Unterlage {ueber!r} der Skizze {name!r} liegt nicht als Datei in der "
                f"Mappe. Die Mappe nennt sie, aber es gibt nichts, worauf die Skizze "
                f"gesetzt werden könnte.")

    ziel = Path(wurzel) / EINGANGSORDNER / _eingangsname(name)
    try:
        gesetzt = setze_auf_unterlage(pfad_skizze, ziel, unterlage=unterlage)
    except (bildlesen.BildError, bildschreiben.SchreibError) as fehler:
        raise ArbeitsgangError(
            f"Die Skizze {name!r} liess sich nicht auf ihre Unterlage setzen: "
            f"{fehler}") from fehler
    # DIESE SAETZE STEHEN SEIT DEM 23.09.2026 NEBEN DEM BILD (der Server der Flaeche
    # reicht sie ohne Unterlage und gestreckt als Hinweis durch) — sie sind fuer einen
    # Menschen geschrieben, nicht fuer die Fehlersuche.
    if ueber is None:
        grund = (f"Ohne Unterlage gezeichnet — gerechnet auf neutralem Grau "
                 f"{NEUTRALER_GRUND} statt auf einem Bild.")
    elif gesetzt["gestreckt"]:
        grund = (f"Auf {ueber!r} gesetzt; Skizze und Unterlage haben nicht dasselbe "
                 f"Seitenverhältnis — die Skizze wurde auf das Bild GESTRECKT und sitzt "
                 f"darum verzerrt darauf.")
    else:
        grund = f"Auf {ueber!r} gesetzt, Blatt auf Bild."
    return {"pfad": gesetzt["bild"],
            "herkunft": {"bild": ueber,
                         "eingangsbild": projekt.pfad_fuer_die_mappe(gesetzt["bild"], wurzel),
                         "breite": gesetzt["breite"], "hoehe": gesetzt["hoehe"],
                         "gestreckt": gesetzt["gestreckt"], "grund": grund}}


def _skizzengraph(glb: str, args: dict, p: dict, *, pfad: Path, anweisung: str):
    """``geometrie → multipass → bildquelle(skizze) → nachrender [→ qa]``.

    Der Nachrender übernimmt Backbone, Startwert, Schritte, ControlNet-Stärke,
    Negativprompt und ``denoise`` aus dem Renderknoten, den :func:`kette.baue_kette` mit
    denselben Einstellungen gebaut hätte — ausdrücklich übergeben, weil dieser
    Renderknoten danach aus dem Graphen fällt.
    """
    voll = _baue_grundgraph(glb, args, p)
    vorlage = voll.knoten[kette.KNOTEN_RENDER].params
    qa_vorlage = voll.knoten.get(kette.KNOTEN_QA)
    grund = Graph([k for k in voll.knoten.values()
                   if k.art not in (kette.ART_RENDER, kette.ART_QA)])
    graph = kette.haenge_nachrender_an(
        grund, prompt=anweisung, eingangsbild=str(pfad),
        negativ_prompt=vorlage["negativ_prompt"], backbone=vorlage["backbone"],
        seed=vorlage["seed"], schritte=vorlage["schritte"],
        controlnet_staerke=vorlage["controlnet_staerke"], denoise=vorlage["denoise"],
        id_vorsatz=SKIZZEN_VORSATZ)
    if qa_vorlage is not None:
        # DIESELBE PRUEFUNG, auf das neue Bild gerichtet (Slot 0 Soll, Slot 1 Ist). Auf
        # einer Skizze urteilt sie «nicht anwendbar» — und dieser Satz ist mehr wert als
        # «in diesem Lauf keine Pruefung», weil er sagt, WARUM.
        graph = Graph(list(graph.knoten.values()) + [Knoten(
            id=f"{SKIZZEN_VORSATZ}-{kette.KNOTEN_QA}", art=kette.ART_QA,
            params=dict(qa_vorlage.params),
            eingaenge=(kette.KNOTEN_MULTIPASS,
                       f"{SKIZZEN_VORSATZ}-{kette.KNOTEN_NACHRENDER}"))])
    return graph


def _skizze_der_mappe(p: dict, wurzel: Path, name: str, anweisung):
    """Die Skizze nachschlagen: ``(pfad, anweisung, ueber)`` — oder begründet abweisen.

    ``ueber`` ist das Bild, auf das gezeichnet wurde, oder ``None`` (leerer Grund)."""
    treffer = [e for e in (p.get("skizzen") or [])
               if isinstance(e, dict) and e.get("skizze") == name]
    if len(treffer) != 1:
        raise ArbeitsgangError(
            f"Die Skizze {name!r} steht {len(treffer)}-mal in dieser Mappe. Gerechnet wird "
            f"nur eine, die genau einmal dasteht — bei zweien wäre die Wahl geraten.")
    eintrag = treffer[0]
    if eintrag.get("stand") == projekt.SKIZZE_VERWORFEN:
        raise ArbeitsgangError(
            f"Die Skizze {name!r} ist verworfen — bewusst liegengelassen. Sie wird nicht "
            f"still wieder aufgenommen; wer sie doch will, legt sie neu ab.")
    pfad = projekt.loese_pfad(name, wurzel)
    if not Path(pfad).is_file():
        raise ArbeitsgangError(
            f"Die Datei der Skizze {name!r} liegt nicht in der Mappe. Die Mappe nennt sie, "
            f"aber es gibt nichts zu rechnen.")
    text = anweisung if anweisung is not None else eintrag.get("bemerkung")
    if not isinstance(text, str) or not text.strip():
        raise ArbeitsgangError(
            f"Zur Skizze {name!r} fehlt die Anweisung, was sich am Bild ändern soll — "
            f"weder als anweisung noch als Bemerkung der Skizze. Der Prompt der Mappe "
            f"wird bewusst nicht genommen: Er beschreibt, was entstehen soll, nicht was "
            f"sich ändern soll.")
    ueber = eintrag.get("ueber")
    return Path(pfad), text, (str(ueber) if ueber else None)


def _gruppenkennung(art: str) -> str:
    # KEIN BENUTZER- UND KEIN RECHNERNAME (Regel 3): Zeit und ein paar Zufallszeichen.
    zeit = _jetzt_iso().replace("-", "").replace(":", "")
    return f"{art}-{zeit}-{secrets.token_hex(3)}"


def _startwerte(args: dict, n: int) -> list[int]:
    """Die Startwerte einer Reihe, nach der Vorschrift von :func:`varianten.saatreihe`.

    Die Vorschrift wird **dort** geholt und nicht nachgebaut: ``seed``, ``seed+1``, …,
    kein Umbruch am Rand. Eine zweite Fassung derselben Regel wäre an einer der beiden
    Stellen bereits veraltet.
    """
    start = args.get("seed")
    try:
        start = 0 if start is None else int(start)
        reihe = saatreihe(
            render.RenderAuftrag(depth_png="", prompt=str(args.get("prompt") or "")),
            n, erster_seed=start)
    except (TypeError, ValueError, VariantenError) as fehler:
        raise ArbeitsgangError(f"Die Startwerte der Reihe sind so nicht bildbar: "
                               f"{fehler}") from fehler
    return [a.seed for a in reihe]


def _melde_sicher(melder, ereignis: dict) -> None:
    if melder is None:
        return
    try:
        melder(ereignis)
    except Exception:                              # noqa: BLE001 — wie in fuehre_aus
        pass


def _rechne_gesperrt(wurzel, *, trotz_aenderung, ausfuehrer, cache, melder, abbrechen,
                     entwurf, varianten, skizzen, anweisung, kettenargumente) -> dict:
    """Der Lauf selbst. Siehe :func:`rechne` — hier steht nur, was **innerhalb** der
    Sperre geschieht."""
    if entwurf is not True and entwurf is not False:
        raise ArbeitsgangError(f"entwurf ist True oder False — war {entwurf!r}.")
    auf = projekt.oeffne(wurzel)
    p, stand = auf["projekt"], auf["modell_stand"]

    if stand in (projekt.MODELL_VERAENDERT, projekt.MODELL_FEHLT) and not trotz_aenderung:
        raise ArbeitsgangError(
            f"{auf['modell_grund']}\n"
            f"Gerechnet wird darum nicht: Ein Urteil, das gegen ein anderes Gebäude "
            f"gemessen wurde und unter dem alten Modellnamen in der Mappe steht, ist "
            f"schlimmer als gar keines. Wer es trotzdem will — etwa um zwei Stände zu "
            f"vergleichen —, ruft mit trotz_aenderung=True; dann steht an jedem Bild, "
            f"unter welchem Modellstand es entstand.")

    glb = (p.get("import") or {}).get("glb")
    if glb:
        # DIE ANGABE IST RELATIV ZUR MAPPE — hier wird sie wieder zu einem Pfad auf
        # dieser Platte. Siehe `projekt.loese_pfad`.
        glb = str(projekt.loese_pfad(glb, wurzel))
    if not glb:
        raise ArbeitsgangError(
            "In diesem Projekt liegt keine umgewandelte Geometrie. Es ist vermutlich "
            "nicht über `lege_an` entstanden, oder der Import wurde abgelehnt — der "
            "Grund steht dann unter 'import'.")

    # DIE MAPPE TRAEGT DIE VORGABE, DER AUFRUF DAS BESONDERE. Anders herum muesste man
    # jede Einstellung bei jedem Lauf wiederholen, und der erste vergessene Wert faellt
    # niemandem auf — er sieht aus wie eine Entscheidung.
    args = {**(p.get("einstellungen") or {}), **kettenargumente}
    args.pop("ifc_path", None)

    # DIE HOCHACHSE WIRD NICHT GERATEN, und das ist die einzige Stelle, an der dieses
    # Modul den Aufrufer wirklich um etwas bittet.
    if not args.get("up_axis"):
        einfuhr = p.get("import") or {}
        if einfuhr.get("hochachse_steht_fest"):
            args["up_axis"] = einfuhr["hochachse"]
        else:
            raise ArbeitsgangError(
                "Welche Achse oben ist, steht für dieses Modell nicht fest. Es kam als "
                "glTF herein, und glTF hat kein Feld dafür — die Erzeuger im Ökosystem "
                "sind sich uneinig.\n"
                "Geraten wird hier nicht: Eine falsche Angabe verdreht Tiefenkarte, "
                "Kamera und Prüfung GEMEINSAM. Das Ergebnis ist dann in sich stimmig und "
                "vollständig falsch, und es fällt nirgends auf.\n"
                "Angeben mit up_axis='Y' oder up_axis='Z'. Wer es nicht weiss: Eine IFC "
                "trägt die Angabe selbst — der Weg über IFC beantwortet die Frage, statt "
                "sie zu stellen.")

    if entwurf:
        args = entwurfsargumente(args, kettenargumente)

    # DER PLAN: ein Eintrag je Lauf. Alle Graphen werden VOR dem ersten Lauf gebaut —
    # ein Baufehler in Variante drei soll nicht erst auffallen, wenn zwei schon gerechnet
    # sind.
    plaene = []
    if skizzen:
        art = VARIANTEN_EBENEN
        for name in skizzen:
            pfad_skizze, text, ueber = _skizze_der_mappe(p, wurzel, name, anweisung)
            # DIE SKIZZE AUF IHRE UNTERLAGE, BEVOR SIE IN DEN GRAPHEN GEHT (Befund
            # 22.09.2026): Bis dahin ging die Zeichnung allein hinein, auf durchsichtigem
            # Grund, und die Bildstufe machte daraus rote Striche vor Schwarz. Siehe
            # `setze_auf_unterlage`. Auch das VOR dem ersten Lauf: Eine fehlende Unterlage
            # der dritten Ebene soll nicht erst auffallen, wenn zwei gerechnet sind.
            eingang = _eingangsbild(p, wurzel, name, pfad_skizze, ueber)
            plaene.append({"args": args, "skizze": name, "anweisung": text,
                           "unterlage": eingang["herkunft"],
                           "graph": _skizzengraph(glb, args, p, pfad=eingang["pfad"],
                                                  anweisung=text)})
    elif varianten:
        art = VARIANTEN_STARTWERTE
        for startwert in _startwerte(args, varianten):
            eigene = {**args, "seed": startwert}
            plaene.append({"args": eigene, "skizze": None, "anweisung": None,
                           "unterlage": None, "graph": _baue_grundgraph(glb, eigene, p)})
    else:
        art = None
        plaene.append({"args": args, "skizze": None, "anweisung": None,
                       "unterlage": None, "graph": _baue_grundgraph(glb, args, p)})

    gruppe_id = _gruppenkennung(art) if len(plaene) > 1 else None

    if cache is SPEICHER_IN_DER_MAPPE:
        cache = ArtefaktCache(wurzel / SPEICHERORDNER)

    tabelle = ausfuehrer
    if melder is not None and ausfuehrer is None:
        tabelle = {**kette.AUSFUEHRER,
                   kette.ART_RENDER: kette.render_ausfuehrer(
                       schrittzaehler=lambda n: melder({"art": "schritt", "schritt": n}))}

    laeufe, gerechnet = [], []
    nicht_begonnen = 0
    zwischen_angehalten = False
    for nummer, plan in enumerate(plaene, start=1):
        if laeufe and laeufe[-1].get("status") == kette.STATUS_ABGEBROCHEN:
            # ANGEHALTEN HEISST: AUCH KEINE WEITERE VARIANTE. Sonst liefe nach dem Klick
            # die naechste Reihe an und wuerde erst an ihrem ersten Knoten gestoppt.
            nicht_begonnen = len(plaene) - nummer + 1
            break
        if laeufe and _haelt_an(abbrechen):
            # UND AUCH NICHT, WENN DER KLICK WAEHREND DES LETZTEN KNOTENS KAM (Befund der
            # Durchsicht D-KERN, 22.09.2026, nachgestellt): Dann lief die Variante davor
            # regulaer zu Ende, ihr Status ist `ok`, und die naechste begann trotzdem —
            # angehalten erst vor ihrem ersten Knoten, mit einem leeren Lauf in der
            # Mappe. Gefragt wird darum auch ZWISCHEN den Varianten.
            nicht_begonnen = len(plaene) - nummer + 1
            zwischen_angehalten = True
            break
        gruppe = None
        if gruppe_id is not None:
            gruppe = {"id": gruppe_id, "art": art, "nummer": nummer, "von": len(plaene)}
            if art == VARIANTEN_STARTWERTE:
                gruppe["seed"] = plan["args"].get("seed")
            if art == VARIANTEN_EBENEN:
                gruppe["skizze"] = plan["skizze"]
            _melde_sicher(melder, {"art": "variante_beginnt", "nummer": nummer,
                                   "von": len(plaene), "gruppe": gruppe_id})
        lauf = kette.fuehre_aus(plan["graph"], ausfuehrer=tabelle, cache=cache,
                                melder=melder, abbrechen=abbrechen,
                                out_dir=str(wurzel / "laeufe"))
        laeufe.append(lauf)
        gerechnet.append((plan, lauf, gruppe))

    # WAS NICHT BEGANN, STEHT AM LETZTEN LAUF DER REIHE — in der Mappe, nicht nur im
    # Rueckgabewert. Sonst saehe eine Reihe, die nach zwei von drei Varianten angehalten
    # wurde, in der Mappe aus wie eine Reihe aus zweien.
    p, pfad, vermerkt, bilder = _vermerke_und_speichere(
        p, wurzel, gerechnet, stand, entwurf=entwurf,
        nicht_begonnen=nicht_begonnen if gruppe_id is not None else None)
    return {"projekt": p, "lauf": laeufe[-1], "laeufe": laeufe, "vermerkt": vermerkt,
            "bilder": bilder, "modell_stand": stand, "pfad": pfad,
            "abgebrochen": (laeufe[-1].get("status") == kette.STATUS_ABGEBROCHEN
                            or zwischen_angehalten),
            "variantengruppe": gruppe_id, "varianten_nicht_begonnen": nicht_begonnen}


def _haelt_an(abbrechen) -> bool:
    """Die Abbruchfrage **zwischen** zwei Varianten — wie in ``kette.fuehre_aus``: Eine
    Frage, die selbst scheitert, hält nichts an. Die nächste Variante stellt sie vor
    ihrem ersten Knoten ohnehin wieder, und dort steht ein Scheitern im Ergebnis
    (``abbruchfrage_fehler``)."""
    if abbrechen is None:
        return False
    try:
        return bool(abbrechen())
    except Exception:                              # noqa: BLE001 — wie in fuehre_aus
        return False


#: Wie oft ein Lauf seine Vermerke auf einen **fremden neueren** Stand der Mappe
#: nachträgt, bevor er aufgibt. Siehe :func:`_vermerke_und_speichere`.
#:
#: **GESETZT, nicht gemessen.** Während ein Lauf rechnet, schreiben nur kurze Wege in
#: die Mappe (Namen, Skizzen ablegen, Einstellungen) — jeder davon in Millisekunden.
#: Dreimal hintereinander genau zwischen Öffnen und Speichern getroffen zu werden, wäre
#: ein Gerät, das in Schleife schreibt; dann ist Melden die richtige Antwort.
NACHHOLEN_HOECHSTENS = 3


def _vermerke_und_speichere(p: dict, wurzel: Path, gerechnet: list, stand, *,
                            entwurf: bool, nicht_begonnen) -> tuple:
    """Alle Läufe in die Mappe eintragen und speichern — **auf dem neuesten Stand.**

    **Der Befund (Durchsicht D-KERN, 22.09.2026, nachgestellt):** Der Lauf öffnete die
    Mappe zu Beginn und speicherte sie am Ende. Benannte das iPad in der Zwischenzeit ein
    Bild (``projekt.benenne`` nimmt die Laufsperre nicht) oder legte eine Skizze ab, lag
    auf der Platte ein neuerer Stand; ``speichere`` warf :class:`projekt.ProjektKollision`,
    und **alle Vermerke des Laufs fehlten** — Bilder, Urteile, der Lauf selbst. Die
    Dateien lagen da, die Mappe kannte sie nicht.

    **Nachholen statt Sperren.** Die Laufsperre auch für ``benenne`` zu nehmen hiesse,
    dass während eines Laufs (bis zu Stunden) kein Name vergeben und keine Skizze
    abgelegt werden kann — und die Skizze kommt gerade dann, wenn der Mensch wartet.
    Stattdessen trägt der Lauf, wenn er kollidiert, seine Vermerke **auf den frischen
    Stand** noch einmal ein. Bilder und Läufe fügt er nur **hinzu** — derselbe Grund,
    aus dem die Fläche das Ablegen einer Skizze wiederholen darf. Ein Name, den der andere
    vergab, bleibt: ``vermerke_bild`` übernimmt ihn vom Eintrag, den es ersetzt.

    **Nur hinzufügen stimmt an einer Stelle nicht, und dort wird nachgesehen:** am
    Skizzeneintrag. ``markiere_skizze`` **überschreibt** ``stand`` und ``ergebnis``. Wurde
    die Skizze während des Laufs verworfen, drehte das Nachholen sie still zurück auf
    «gerechnet» (Durchsicht der Welle 2, 22.09.2026). Seither entscheidet
    :func:`_vermerke_skizze_des_laufs` auf dem frischen Stand — siehe dort.

    Returns:
        ``(projekt, pfad, vermerkt, bildnamen)`` — das Projekt ist das **gespeicherte**.

    Raises:
        projekt.ProjektKollision: Auch nach :data:`NACHHOLEN_HOECHSTENS` Versuchen lag
            jedes Mal ein neuerer Stand da.
    """
    for versuch in range(1, NACHHOLEN_HOECHSTENS + 1):
        vermerkt, bilder = 0, []
        for i, (plan, lauf, gruppe) in enumerate(gerechnet):
            letzter = i == len(gerechnet) - 1
            zahl, namen = _trage_ein(p, wurzel, plan, lauf, stand, entwurf=entwurf,
                                     gruppe=gruppe,
                                     nicht_begonnen=nicht_begonnen if letzter else (
                                         0 if nicht_begonnen is not None else None))
            vermerkt += zahl
            bilder.extend(namen)
            if plan["skizze"] is not None and namen:
                # GERECHNET HEISST: EIN BILD IST DARAUS ENTSTANDEN. Ohne Bild bleibt die
                # Skizze, wie sie war — ein gescheiterter oder angehaltener Lauf hat
                # nichts aus ihr gemacht.
                _vermerke_skizze_des_laufs(p, plan["skizze"], namen[-1])
        try:
            return p, projekt.speichere(p, wurzel), vermerkt, bilder
        except projekt.ProjektKollision:
            if versuch == NACHHOLEN_HOECHSTENS:
                raise
            # DER FRISCHE STAND, und darauf dasselbe noch einmal. Die eigene Kopie ist
            # ueberholt; was der andere geschrieben hat, steht nur in der neuen.
            p = projekt.oeffne(wurzel)["projekt"]
    raise AssertionError("unerreichbar")  # pragma: no cover


def _vermerke_skizze_des_laufs(p: dict, skizze: str, bild: str) -> None:
    """An der Skizze eines Laufs vermerken, was daraus wurde — **ohne einen Entscheid
    zurückzudrehen, der während des Laufs fiel.**

    * **Verworfen** (während des Laufs, auf dem frischen Stand): Sie **bleibt verworfen**.
      Das Ergebnis wird vermerkt — das Bild ist entstanden und steht in der Mappe, und
      die Skizze soll es nennen können —, der Stand nicht. *Wer eine Skizze verwirft,
      während sie rechnet, hat entschieden; ein Lauf, der danach fertig wird, weiss nichts
      Neueres.* Bis zum 22.09.2026 (Durchsicht der Welle 2) wurde sie still «gerechnet».
    * **Nicht (mehr) genau einmal in der Mappe:** nichts vermerkt. ``markiere_skizze``
      würfe hier, und die Ausnahme nähme **alle** Vermerke des Laufs mit — genau der
      Verlust, gegen den das Nachholen gebaut ist. Das Bild nennt seine Skizze weiter
      (``herkunft.skizze``).
    * Sonst: «gerechnet», mit diesem Bild als Ergebnis.

    Bewacht über den Produktweg (eine Sonde verwirft bzw. entfernt die Skizze mitten im
    Lauf) in ``tests/test_durchsicht_w2b_kern_server.py``.
    """
    treffer = [e for e in (p.get("skizzen") or [])
               if isinstance(e, dict) and e.get("skizze") == skizze]
    if len(treffer) != 1:
        return
    if treffer[0].get("stand") == projekt.SKIZZE_VERWORFEN:
        projekt.markiere_skizze(p, skizze=skizze, stand=projekt.SKIZZE_VERWORFEN,
                                ergebnis=bild)
        return
    projekt.markiere_skizze(p, skizze=skizze, stand=projekt.SKIZZE_GERECHNET, ergebnis=bild)


def _zahl_zu(knoten_ergebnisse: dict, qa_id: str | None) -> tuple:
    """``(score, schwelle)`` der Prüfung, die das Urteil gefällt hat — oder ``None``.

    Nur aus **dieser** Prüfung: Eine Zahl aus einer anderen stünde neben einem Urteil,
    das sie nicht begründet. Was keine endliche Zahl ist (fehlt, Text, ``True``, NaN),
    wird ``None`` — **nicht gemessen**, nie 0.
    """
    if qa_id is None:
        return None, None
    ausgaben = (knoten_ergebnisse.get(qa_id) or {}).get("ausgaben") or {}

    def _zahl(wert):
        if isinstance(wert, bool) or not isinstance(wert, (int, float)):
            return None
        return float(wert) if math.isfinite(float(wert)) else None

    return _zahl(ausgaben.get("score")), _zahl(ausgaben.get("schwelle"))


def _trage_ein(p: dict, wurzel: Path, plan: dict, lauf: dict, stand, *,
               entwurf: bool, gruppe: dict | None,
               nicht_begonnen: int | None = None) -> tuple[int, list[str]]:
    """Die Bilder eines Kettenlaufs und den Lauf selbst in die Mappe schreiben (im
    Speicher; geschrieben wird in :func:`_vermerke_und_speichere`).

    **Rein im Ergebnis:** Zweimal auf zwei Stände derselben Mappe angewandt, schreibt es
    zweimal dasselbe hinzu — darauf beruht das Nachholen nach einer Kollision.

    Returns:
        ``(vermerkt, bildnamen)``.
    """
    graph, args = plan["graph"], plan["args"]
    knoten_ergebnisse = lauf.get("knoten") or {}
    schichten = kette.schichtbefund(graph, knoten_ergebnisse)

    # WAS DIE BILDSTUFE GEMESSEN HAT — EINMAL EINGESAMMELT, ZWEIMAL GEBRAUCHT: an jedem
    # Bild (Herkunft) und im Lauf (Zusammenfassung). Siehe `MESSFELDER`, Befund
    # 22.09.2026.
    #
    # ÜBER ALLE BILDKNOTEN, nicht nur über die mit einem Bild: Ein Knoten, der gescheitert
    # ist, hat womöglich trotzdem gemessen, auf welchem Weg er lief — und dass er NICHTS
    # gemeldet hat, ist selbst eine Auskunft. Ein fehlender Eintrag wäre von einem
    # Knoten, den es nie gab, nicht zu unterscheiden.
    messungen = {}
    angaben = {}
    for kid in sorted(graph.knoten):
        if kette._ist_bildart(graph.knoten[kid].art):
            ausgaben_kid = (knoten_ergebnisse.get(kid) or {}).get("ausgaben") or {}
            messungen[kid] = _messung_zu(ausgaben_kid)
            # LIZENZ UND MAENGEL, Befund 22.09.2026 — siehe `ANGABEFELDER`.
            angaben[kid] = _angaben_zu(ausgaben_kid)

    # DIE ABWEICHUNG STEHT VORNE UND NICHT IN EINER HINWEISLISTE. Derselbe Grund wie in
    # `render._ergebnis` (Befund `auf-20260921-130`): Wer Hinweise überfliegt, sieht
    # ausgerechnet den nicht, der den Lauf entwertet. Eine Liste, die man abfragen kann,
    # wird abgefragt.
    #
    # `hinweise` ALS EIGENE KOPIE (Befund 22.09.2026): Bis dahin war es dieselbe Liste
    # wie in `messungen[kid]` und — ueber die flache Kopie in `projekt.vermerke_bild` —
    # wie an der Herkunft des Bildes. Eine Aenderung an einer der drei Stellen aenderte
    # still die beiden anderen.
    modus_abweichungen = [
        {"knoten": kid, "bestellt": m["modus_bestellt"],
         "gerechnet": m["modus_gerechnet"], "hinweise": copy.deepcopy(m["hinweise"])}
        for kid, m in sorted(messungen.items()) if m["modus_abweichung"] is True]
    # UND DIE DRITTE ANTWORT DANEBEN. Ohne diese Liste hiesse eine leere Abweichungsliste
    # zweierlei: «keine Abweichung» und «niemand hat hingesehen». Die beiden dürfen in
    # einer Mappe nicht gleich aussehen.
    modus_ungemessen = [kid for kid, m in sorted(messungen.items())
                        if m["modus_abweichung"] is None]

    vermerkt, namen = 0, []
    for kid in sorted(graph.knoten):
        if not kette._ist_bildart(graph.knoten[kid].art):
            continue
        eintrag = knoten_ergebnisse.get(kid) or {}
        bild = (eintrag.get("ausgaben") or {}).get("bild_png")
        if not bild:
            # KEIN BILD, KEIN EINTRAG — und das ist kein Verschweigen: Ein Knoten ohne
            # Ausgabe hat nichts erzeugt, was in einer Bildliste stehen koennte. Dass er
            # lief und scheiterte, steht im Lauf, und der Lauf wird mitgeschrieben.
            continue
        if plan["skizze"] is not None and graph.knoten[kid].art == kette.ART_BILDQUELLE:
            # DIE SKIZZE SELBST IST KEIN ERZEUGTES BILD. Die Bildquelle reicht sie nur
            # herein (als Kopie im Arbeitsordner); in der Mappe steht sie schon unter
            # `skizzen`. Als Bild vermerkt, stuende dieselbe Zeichnung zweimal da.
            continue

        if entwurf:
            # ENTWURF — NICHT GEPRUEFT (Entscheid 30). Der Graph hat keine Pruefung; das
            # Urteil ist darum None, und der Grund sagt, dass es ein Entwurf ist und
            # nicht bloss «keine Pruefung in diesem Lauf».
            urteil, qa_id = None, None
            grund = (f"{ENTWURF_VERMERK}: schnell gerechnet, ohne Geometrieprüfung "
                     f"(Entscheid 30). NICHT GEMESSEN — weder bestanden noch "
                     f"durchgefallen.")
        else:
            urteil, grund, qa_id = _urteil_zu(graph, knoten_ergebnisse, kid)
        score, schwelle = _zahl_zu(knoten_ergebnisse, qa_id)
        # DIE ZAHL GEHOERT ANS BILD NUR MIT IHREM URTEIL (Befund der Durchsicht D-KERN,
        # 22.09.2026, nachgestellt): Liefert die Pruefung `bestanden=None` — der Maskenweg
        # fehlt, sie hat gerechnet, aber nicht geurteilt —, stand ihr Score trotzdem unter
        # `score`/`schwelle` am Bild. Neben «nicht gemessen» las sich das wie eine Messung
        # («0.91 · Schwelle 0.65»). Die Zahl geht darum nicht verloren, sondern in die
        # Herkunft (`herkunft.messung`), wo sie als das steht, was sie ist: ein Wert ohne
        # Urteil.
        messung = copy.deepcopy(messungen.get(kid)) or {}
        messung["score"], messung["schwelle"] = score, schwelle
        if urteil is None:
            score, schwelle = None, None
        felder = schichten.get(kid) or {}
        herkunft = {
            "knoten": kid,
            "grund": grund,
            "urteil_von": qa_id,
            "backbone": args.get("backbone"),
            "prompt": args.get("prompt"),
            "seed": args.get("seed"),
            # DER MODELLSTAND GEHOERT AN JEDES BILD, nicht nur in den Lauf. Wer
            # spaeter ein einzelnes Bild ansieht, sieht sonst nicht, dass es gegen
            # ein inzwischen geaendertes Modell gerechnet wurde.
            "modell_stand": stand,
            # WAS DIESER KNOTEN GEMESSEN HAT, AN SEINEM BILD. Wer ein einzelnes Bild
            # ansieht, muss sehen koennen, dass es als `txt2img` entstand, obwohl
            # `image_edit` bestellt war — sonst sieht ein entwertetes Bild aus wie
            # jedes andere.
            #
            # EINE EIGENE KOPIE, und das ist ein gefangener Fehler (22.09.2026):
            # `projekt.vermerke_bild` kopiert die Herkunft nur flach. Ohne Kopie hier
            # war diese Messung DASSELBE Objekt wie `lauf["messungen"][kid]` — wer
            # sie am Bild berichtigte, schrieb still den Lauf mit um, und umgekehrt.
            #
            # DAZU `score` UND `schwelle` DER PRUEFUNG `urteil_von`, wie sie gemeldet
            # wurden — auch ohne Urteil (siehe oben). Nur hier, nicht im Lauf: Der Lauf
            # sammelt, was die BILDSTUFE gemessen hat.
            "messung": messung,
            # UNTER WELCHER LIZENZ DAS BILD ENTSTAND, und was am Auftrag bemaengelt
            # wurde — siehe `ANGABEFELDER`. Wieder als eigene Kopie.
            "lizenz": copy.deepcopy(angaben[kid]["lizenz"]),
            "maengel": copy.deepcopy(angaben[kid]["maengel"]),
        }
        if plan["skizze"] is not None:
            # WORAUS ES ENTSTAND. Die Skizze nennt ihr Bild (`ergebnis`), das Bild seine
            # Skizze — ein Verweis in nur einer Richtung waere von der anderen Seite
            # nicht zu finden.
            herkunft["skizze"] = plan["skizze"]
            herkunft["anweisung"] = plan["anweisung"]
            # UND WORAUF SIE GESETZT WURDE — das Eingangsbild, das der Nachrender wirklich
            # bekam (Befund 22.09.2026, siehe `setze_auf_unterlage`).
            herkunft["unterlage"] = copy.deepcopy(plan.get("unterlage"))
        name = projekt.pfad_fuer_die_mappe(bild, wurzel)
        projekt.vermerke_bild(
            # RELATIV ZUR MAPPE — zum dritten Mal derselbe Grund (Beweis 31, 21.09.2026):
            # Ein absoluter Pfad ueberlebt die Saeuberung nach Regel 3 nicht. Und hier
            # haengt mehr daran als die Lesbarkeit: Die Flaeche liefert nur Bilder
            # AUS DEM PROJEKTORDNER aus und kennt sie am relativen Namen. Ein absoluter
            # Name waere dort gar kein Bild.
            p, bild=name,
            schicht=felder.get(kette.FELD_SCHICHT, kette.SCHICHT_GEOMETRIE),
            urteil=urteil,
            basis=felder.get(kette.FELD_BASIS),
            herkunft=herkunft,
            score=score, schwelle=schwelle, entwurf=entwurf,
            variantengruppe=gruppe)
        vermerkt += 1
        namen.append(name)

    p.setdefault("laeufe", []).append({
        "status": lauf.get("status"),
        "gerechnet": lauf.get("gerechnet"),
        "cache_treffer": lauf.get("cache_treffer"),
        "gescheitert": lauf.get("gescheitert"),
        "dauer_s": lauf.get("dauer_s"),
        "error": lauf.get("error"),
        "modell_stand": stand,
        "bilder_vermerkt": vermerkt,
        # WAS DER LAUF GEMESSEN HAT, GEHOERT IN DIE MAPPE — und zwar die Abweichung
        # zuerst. Befund 22.09.2026: Bis hierher standen im Lauf nur sechs
        # Zusammenfassungsfelder, und alles Gemessene blieb im Knotenergebnis liegen.
        "modus_abweichungen": modus_abweichungen,
        "modus_ungemessen": modus_ungemessen,
        "messungen": messungen,
        # LIZENZ UND MAENGEL JE BILDKNOTEN, auch ohne Bild (22.09.2026). Siehe
        # `ANGABEFELDER`.
        "angaben": angaben,
        # ANGEHALTEN (Entscheid 31) — als eigenes Feld und nicht nur im Status, damit
        # «abgebrochen» und «gescheitert» sich nicht ein Wort teilen muessen.
        "abgebrochen": lauf.get("status") == kette.STATUS_ABGEBROCHEN,
        "abgebrochene_knoten": list(lauf.get("abgebrochen") or []),
        "entwurf": entwurf,
        "variantengruppe": dict(gruppe) if gruppe else None,
        "skizze": plan["skizze"],
        # WIEVIELE VARIANTEN DER REIHE NACH DIESEM LAUF NICHT MEHR BEGANNEN — `None`
        # ausserhalb einer Reihe, 0 in der Reihe, wo es weiterging.
        "varianten_nicht_begonnen": nicht_begonnen,
    })
    return vermerkt, namen
