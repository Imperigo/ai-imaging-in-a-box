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

Regel 4: Aufrufbar aus reinem Python. Die Ausführer der Kette lassen sich übergeben; ohne
GPU und ohne Blender läuft dieses Modul mit Attrappen vollständig durch.
"""
from __future__ import annotations

import copy
import datetime
import json
import time
from pathlib import Path

from aiimaging import importeur, kette, projekt
# DIE KLASSE DIREKT, nicht das Modul: `graph` heisst hier unten der GRAPH
# dieses Laufs, und ein Modulname, den eine lokale Zuweisung verdeckt, ist
# ein Fehler, der erst beim Aufruf auffaellt.
from aiimaging.graph import ArtefaktCache

__all__ = ["ANGABEFELDER", "ArbeitsgangError", "MESSFELDER", "lege_an", "rechne"]


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
        timeout: Gesamtfrist für die Umwandlung.

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
    }
    pfad = projekt.speichere(p, wurzel)
    return {"projekt": p, "import_bericht": bericht, "pfad": pfad}


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
    for k in passende:
        eintrag = knoten_ergebnisse.get(k) or {}
        if eintrag.get("status") != kette.STATUS_OK:
            continue
        ausgaben = eintrag.get("ausgaben") or {}
        if "bestanden" in ausgaben:
            urteile.append((k, ausgaben["bestanden"], _grund_der_pruefung(k, ausgaben)))

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


def rechne(wurzel, *, trotz_aenderung: bool = False, ausfuehrer=None,
           cache=SPEICHER_IN_DER_MAPPE, melder=None, **kettenargumente) -> dict:
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

            **Der Zähler wird nur dann eingehängt, wenn kein eigener ``ausfuehrer``
            übergeben ist.** Wer die Tabelle selbst mitbringt, hat seine Gründe, und eine
            stille Ersetzung darin wäre genau die Sorte Überraschung, gegen die
            ``fuehre_aus`` die Tabelle ausdrücklich *ersetzen* statt ergänzen lässt.
        **kettenargumente: alles Weitere an :func:`aiimaging.kette.baue_kette` (Prompt,
            Seed, Auflösung …). Was im Projekt unter ``einstellungen`` steht, wird
            **vorangestellt** und hier überschrieben — *die Mappe trägt die Vorgabe, der
            Aufruf das Besondere.*

    Returns:
        ``{projekt, lauf, vermerkt, modell_stand, pfad}``. ``vermerkt`` ist die Zahl der
        eingetragenen Bilder. Das Projekt ist **geschrieben**.

    Raises:
        ArbeitsgangError: Kein Modell zum Rechnen, oder das Modell hat sich geändert und
            ``trotz_aenderung`` ist nicht gesetzt.

    **Warum ein Lauf, der scheitert, trotzdem eingetragen wird.** Ein gescheiterter Lauf
    ist eine Tatsache über dieses Projekt. Ihn wegzuwerfen hiesse, dass zwei Zustände
    gleich aussehen: «wurde nie versucht» und «wurde versucht und ging nicht».

    **Und was der Lauf gemessen hat, wird mitgeschrieben** (22.09.2026). Im Lauf stehen
    ``modus_abweichungen`` (die Fälle, in denen etwas anderes gerechnet als bestellt
    wurde), ``modus_ungemessen`` (die Knoten, die dazu nichts gemeldet haben) und
    ``messungen`` je Bildknoten; dieselbe Messung hängt unter ``herkunft.messung`` an
    jedem eingetragenen Bild — **als eigene Kopie**, nicht als dasselbe Objekt. Siehe
    :data:`MESSFELDER`. Lizenz und Mängel der Bildstufe stehen im Lauf unter ``angaben``
    und am Bild unter ``herkunft.lizenz`` / ``herkunft.maengel``; siehe
    :data:`ANGABEFELDER`.
    """
    wurzel = Path(wurzel)
    # DIE SPERRE ZUERST, VOR DEM OEFFNEN. Laege sie spaeter, haette der zweite Lauf die
    # Mappe schon gelesen, bevor der erste sie geschrieben hat — und genau diese Kopie
    # wuerde er am Ende zurueckschreiben.
    sperre = _nimm_sperre(wurzel)
    try:
        return _rechne_gesperrt(
            wurzel, trotz_aenderung=trotz_aenderung, ausfuehrer=ausfuehrer, cache=cache,
            melder=melder, **kettenargumente)
    finally:
        # AUCH BEIM SCHEITERN. Eine Sperre, die ein abgebrochener Lauf stehenlaesst,
        # blockiert die Mappe fuer Stunden — und der naechste Mensch sieht nur, dass
        # nichts geht.
        Path(sperre).unlink(missing_ok=True)


def _rechne_gesperrt(wurzel, *, trotz_aenderung, ausfuehrer, cache, melder,
                     **kettenargumente) -> dict:
    """Der Lauf selbst. Siehe :func:`rechne` — hier steht nur, was **innerhalb** der
    Sperre geschieht."""
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

    graph = kette.baue_kette(glb_path=glb, **args)

    if cache is SPEICHER_IN_DER_MAPPE:
        cache = ArtefaktCache(wurzel / SPEICHERORDNER)

    tabelle = ausfuehrer
    if melder is not None and ausfuehrer is None:
        tabelle = {**kette.AUSFUEHRER,
                   kette.ART_RENDER: kette.render_ausfuehrer(
                       schrittzaehler=lambda n: melder({"art": "schritt", "schritt": n}))}

    lauf = kette.fuehre_aus(graph, ausfuehrer=tabelle, cache=cache, melder=melder,
                            out_dir=str(wurzel / "laeufe"))
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

    vermerkt = 0
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

        urteil, grund, qa_id = _urteil_zu(graph, knoten_ergebnisse, kid)
        felder = schichten.get(kid) or {}
        projekt.vermerke_bild(
            # RELATIV ZUR MAPPE — zum dritten Mal derselbe Grund (Beweis 31, 21.09.2026):
            # Ein absoluter Pfad ueberlebt die Saeuberung nach Regel 3 nicht. Und hier
            # haengt mehr daran als die Lesbarkeit: Die Oberflaeche liefert nur Bilder
            # AUS DEM PROJEKTORDNER aus und kennt sie am relativen Namen. Ein absoluter
            # Name waere dort gar kein Bild.
            p, bild=projekt.pfad_fuer_die_mappe(bild, wurzel),
            schicht=felder.get(kette.FELD_SCHICHT, kette.SCHICHT_GEOMETRIE),
            urteil=urteil,
            basis=felder.get(kette.FELD_BASIS),
            herkunft={
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
                "messung": copy.deepcopy(messungen.get(kid)),
                # UNTER WELCHER LIZENZ DAS BILD ENTSTAND, und was am Auftrag bemaengelt
                # wurde — siehe `ANGABEFELDER`. Wieder als eigene Kopie.
                "lizenz": copy.deepcopy(angaben[kid]["lizenz"]),
                "maengel": copy.deepcopy(angaben[kid]["maengel"]),
            })
        vermerkt += 1

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
    })
    pfad = projekt.speichere(p, wurzel)
    return {"projekt": p, "lauf": lauf, "vermerkt": vermerkt,
            "modell_stand": stand, "pfad": pfad}
