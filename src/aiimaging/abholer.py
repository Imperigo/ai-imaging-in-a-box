"""ABHOLER — der, der die Aufträge der Brücke wirklich abholt.

Warum dieses Modul entsteht, und zwar jetzt
--------------------------------------------
Am 19.08.2026 ist jemand die fremde Oberfläche als Nutzer durchgegangen. Die Kette trug
weiter als erwartet: Oberfläche → Graph → Knoten → Kanten → Prompt → Geometrie-Export →
Kamerasetzung → **Auftrag in der Warteschlange**. In ``/tmp/kosmo-jobs/`` lag ein
vollständiges Verzeichnis mit ``job.json``, 110 KB echter Geometrie und einer
``render-scene.json`` nach ``kosmovis.render-scene/v1``.

Und dann blieb er liegen. Zustand *„wartet auf GPU-Leerlauf"*, auch bei freier Karte.

> **Genau da hört ihre Seite auf, und genau da fängt unsere an.**

:mod:`aiimaging.bruecke` hatte zu diesem Zeitpunkt bereits alle Teile — ``offene_auftraege``,
``lies_auftrag``, ``setze_status``, ``schreibe_ergebnis``. **Nur fasste sie niemand in der
richtigen Reihenfolge an.** Das ist dieses Modul: kein neuer Baustein, sondern der
Ablauf zwischen den vorhandenen.

Was hier NICHT drinsteht
------------------------
Das Rendern. Der Abholer bekommt es als :func:`verarbeite` **hereingereicht** — dieselbe
Bauform wie ``_starte`` in ``seams.py`` und ``einbetter`` in ``stil_qa.py``. Der Grund ist
nicht Bequemlichkeit, sondern Prüfbarkeit: Die interessanten Fehler dieses Moduls sind
**Reihenfolge- und Entscheidungsfehler**, und die will man prüfen, ohne eine GPU zu
besitzen. Ein Abholer, der nur mit 20 GB Gewichten prüfbar wäre, wäre gar nicht geprüft.

Die fünf Entscheidungen, die hier fallen
----------------------------------------
1. **Ohne menschliche Freigabe wird nicht gerendert.** Die Brücke prägt ihren
   ``approval_token`` selbst (``secrets.token_hex``); er sieht aus wie unserer und
   bedeutet etwas anderes. Ob er gilt, ist eine Entscheidung des Betreibers und keine des
   Programms — siehe ``bruecke._freigabe``. Der Abholer trifft sie nicht, er reicht sie
   durch und **lässt den Auftrag sonst liegen**.
2. **Die Karte entscheidet mit.** Trägt der Laufzettel ``idle_window_only``, wird ohne
   erkennbaren Leerlauf nicht gerechnet — und bei **unbekanntem** Zustand erst recht
   nicht. Das ist die fail-closed-Regel, die uns Sitzung 07 vier Löcher gekostet hat.
3. **Die Reihenfolge beim Schreiben.** Erst das Ergebnis, dann der Laufzettel. Wer den
   Laufzettel zuerst setzt, erzeugt ein Zeitfenster, in dem die fremde Oberfläche ein
   Ergebnis sucht, das noch nicht da ist — und einen Fehler meldet, den niemand
   nachstellen kann. Diese Reihenfolge steckt bereits in ``bruecke.schreibe_ergebnis``;
   hier wird sie nicht umgangen.
4. **Ein Fehler ist ein Ergebnis.** Scheitert die Verarbeitung, wird der Auftrag auf
   ``error`` gesetzt **mit Begründung** — nicht liegengelassen. Ein Auftrag ohne Antwort
   ist für den Wartenden dasselbe wie ein hängender Rechner.
5. **Waisen werden gemeldet, nicht wiederbelebt.** Ein Auftrag, der auf ``running`` steht,
   während niemand ihn bearbeitet — weil der Rechner mitten im Lauf ausging —, wird
   **berichtet und nicht neu eingereiht**. Ein zweiter Lauf desselben Auftrags kostet eine
   GPU-Stunde und erzeugt womöglich ein zweites Bild unter derselben Kennung. Ob das
   gewollt ist, weiss der Betreiber und nicht dieses Modul.

Abhängigkeiten: :mod:`aiimaging.bruecke` und stdlib. Kein ``bpy``, keine Oberfläche
(Regeln 2 und 4).
"""
from __future__ import annotations

import math
import re
import time
from pathlib import Path

from . import bruecke, fortschritt, maske as maske_modul
# Nur fuer die Modus-Konstante. Der Name `kameras` ist in `verarbeite` lokal
# belegt (die Kameraliste der Szene) — darum wird das Modul ausschliesslich in
# der Vorgabe von `verarbeiter` benutzt, wo noch Modulgeltung herrscht.
from . import graph as _graph
from . import kameras as _kameras_modul
from . import kette as _kette
from . import komposition as _komposition
from . import kosmo_szene as _kosmo_szene
from . import prompts, raumkamera as _raumkamera, render
from . import seams as _seams
from . import sonne as _sonne
from . import belichtung as _belichtung_modul
from . import stimmung as _stimmung
from . import varianten

#: Ein Auftrag auf ``running``, dessen Laufzettel so lange nicht angefasst wurde, gilt als
#: **Waise**. Die Zahl ist eine Setzung: Sie muss deutlich über der längsten erwarteten
#: Renderdauer liegen, sonst erklärt sie einen laufenden Auftrag zur Waise. Zwei Stunden
#: sind acht Gesamt-Timeouts eines Multipass-Laufs.
WAISENFRIST_S = 7200.0

#: Was ein Durchgang mit einem Auftrag getan hat.
TAT_VERARBEITET = "verarbeitet"
TAT_FEHLER = "fehler"
TAT_LIEGENGELASSEN = "liegengelassen"
TAT_WAISE = "waise"
#: Der Auftrag wurde während des Laufs abgebrochen (``cancelled``) — siehe
#: :class:`AuftragAbgebrochen`. Der Status bleibt ``cancelled``; geschrieben wird kein
#: Ergebnis, nur das Teilbild.
TAT_ABGEBROCHEN = "abgebrochen"


class AbholerError(ValueError):
    """Der Abholer ist falsch aufgesetzt. Erbt von ``ValueError`` wie alle Fehler hier."""


class AuftragAbgebrochen(AbholerError):
    """Zwischen zwei Schritten stand der Auftrag auf ``cancelled`` — der Lauf hört hier auf.

    ``teilbild`` ist das letzte fertige Zwischenbild (Pfad dieser Maschine) oder ``None``,
    ``kamera`` die Kamera, zu der es gehört. Zugestellt wird es in :func:`hole_einen`, weil
    erst dort die Quelle bekannt ist.
    """

    def __init__(self, satz: str, *, teilbild=None, kamera=None):
        super().__init__(satz)
        self.teilbild = teilbild
        self.kamera = kamera



def _blickrichtung_satz(blickfeld: dict) -> str:
    """Der Satz zur Blickrichtung — als Funktion und nicht im f-String.

    **Er stand als mehrzeiliger Ausdruck INNERHALB eines f-Strings**, und das gibt es
    erst ab Python 3.12 (PEP 701). Dieses Repo verlangt ``>=3.11`` (`pyproject.toml`),
    und auf 3.11 liess sich `abholer.py` daraufhin nicht einmal mehr einlesen: 25
    Testdateien brachen beim Einsammeln ab, bevor eine einzige Probe lief.

    *Auf der Maschine, auf der er entstand (Python 3.14.4), war alles gruen.*
    """
    if blickfeld.get("grund"):
        return str(blickfeld["grund"])
    if blickfeld.get("geprueft"):
        return "geprueft, der Sehstrahl trifft die Szene"
    return "NICHT GEPRUEFT — der Bericht traegt keine brauchbare Huellbox oder Kamera"


def _zeit(_uhr) -> float:
    return float((_uhr or time.time)())


def waisen(store, *, frist_s: float = WAISENFRIST_S, quelle=bruecke, _uhr=None) -> list[dict]:
    """Aufträge, die auf ``running`` stehen und die niemand mehr bearbeitet.

    Sie werden **gemeldet und nicht neu eingereiht**. Ein zweiter Lauf desselben Auftrags
    kostet eine GPU-Stunde und erzeugt womöglich ein zweites Bild unter derselben Kennung;
    ob das gewollt ist, weiss der Betreiber.

    Erkannt an der Änderungszeit des **Laufzettels**, nicht an einem Feld darin. Ein Feld
    müsste jemand fortschreiben, und genau dieser Jemand ist im Waisenfall gestorben.

    Args:
        quelle: die Ablage, die gelesen wird — siehe :func:`hole_einen`. Welche Datei den
            Zeitstempel trägt, sagt sie über ``laufzettel_pfad``; ein hier angenommener
            Dateiname hätte den Waisenfund auf der zweiten Ablage still ausgeschaltet.

    Returns:
        Liste von ``{verzeichnis, job_id, still_seit_s, detail}``, nach Verzeichnis
        sortiert.
    """
    jetzt = _zeit(_uhr)
    gefunden: list[dict] = []
    for ordner in quelle.offene_auftraege(store, nur_status=(quelle.STATUS_RUNNING,)):
        zettel = quelle.laufzettel_pfad(ordner)
        try:
            alter = jetzt - zettel.stat().st_mtime
        except OSError:
            continue
        if alter <= frist_s:
            continue
        gefunden.append({
            "verzeichnis": ordner,
            "job_id": ordner.name,
            "still_seit_s": alter,
            "detail": (
                f"Auftrag {ordner.name} steht seit {alter / 3600:.1f} h auf "
                f"'{quelle.STATUS_RUNNING}', ohne dass sich sein Laufzettel geändert "
                f"hätte (Frist {frist_s / 3600:.1f} h). Der bearbeitende Lauf ist "
                f"vermutlich gestorben. **Nicht** automatisch neu eingereiht: Ein "
                f"zweiter Lauf kostet eine GPU-Stunde und kann ein zweites Bild unter "
                f"derselben Kennung erzeugen. Das ist eine Entscheidung des Betreibers."
            ),
        })
    return gefunden


def hole_einen(verzeichnis, *, verarbeite, fremde_freigabe_gilt: bool = False,
               darf_rechnen=None, wache_bauen=None,
               beobachtungs_takt_s: float = fortschritt.BEOBACHTUNGS_TAKT_S,
               quelle=bruecke, speicher_frei=None, bildeingang_karte=None,
               karte_freigeben=None) -> dict:
    """Einen einzelnen Auftrag bearbeiten — mit allen Entscheidungen davor.

    Args:
        verzeichnis: das Auftragsverzeichnis der Brücke.
        verarbeite: ``(auftrag) -> {bilder, geometrie_urteil, stil_urteil, zeiten}``.
            Wird **nur** aufgerufen, wenn alle Entscheidungen dafür gefallen sind. Wirft
            es, gilt der Auftrag als gescheitert und bekommt eine Begründung.
        fremde_freigabe_gilt: Zählt der von der Brücke selbst geprägte Token als
            menschliche Freigabe? Vorgabe ``False`` — siehe :mod:`aiimaging.bruecke`.
        darf_rechnen: ``() -> (bool, grund)``. Die Auskunft über die Grafikkarte. ``None``
            heisst **nicht** „darf immer", sondern „ungeprüft": Ein Auftrag mit
            ``idle_window_only`` wird dann liegengelassen. Bei **unbekanntem** Zustand
            nicht zu rechnen ist die fail-closed-Regel, die Sitzung 07 vier Löcher
            gekostet hat.
        wache_bauen: ``(auftrag) -> Wache | None``. Wer eine Wache liefert, bekommt sie
            **neben** dem Lauf beobachtet — ``verarbeite`` blockiert, der Abholer könnte
            währenddessen von sich aus nicht nachsehen. Warum die Wache von aussen kommt:
            Sie braucht einen Pfad, an dem sich etwas bewegt, und wo das Bild landet,
            weiss der Verarbeiter und nicht dieses Modul. ``None`` heisst **nicht** „lief
            durch", sondern **nicht beobachtet** — und genau so steht es im Bericht.
        beobachtungs_takt_s: Sekunden zwischen zwei Blicken der Wache.
        speicher_frei: ``() -> int | None`` — freier Grafikspeicher in MiB, **bevor**
            geladen wird. Liegt er unter :data:`MINDEST_FREI_MIB`, wartet der Auftrag
            mit Grund am Laufzettel (B161/B1). ``None`` als Antwort heisst «nicht
            anwendbar» (etwa: die eigenen Gewichte liegen schon auf der Karte);
            ``None`` als Parameter heisst: keine Prüfung, wie bis zum 24.09.2026.
        bildeingang_karte: ``() -> {frei_mib, eigen_mib, fremde_modelle}`` — die Lage der
            Karte für einen Auftrag mit dem Messschalter ``vis.bildeingang``
            (auf-20261021-298). Liegt ein fremdes Modell auf der Karte oder reicht der
            Speicher nicht für den gemessenen Bedarf (:func:`aiimaging.render.pruefe_bildeingang_karte`),
            endet der Auftrag mit Satz auf ``error`` — nicht laden, nicht auslagern. ``None``
            heisst: keine Prüfung, wie bis zum 21.10.2026.
        karte_freigeben: ``() -> dict | None`` — **vor jedem Auftrag, der rechnen darf**,
            die Grafikkarte freigeben: alle Modelle, die Ollama hält, auch fremde
            (Owner-Entscheid 127, 22.10.2026; im Betrieb
            :func:`aiimaging.assistent.gib_karte_frei`). Gerufen nach Lesen und Mängeln,
            **vor** allen Prüfungen der Karte — sie sollen die freigegebene Karte sehen.
            Der Befund steht in ``antwort["freigegeben"]`` und im Ergebnis unter
            ``angewandt.freigegeben``. Wirft er, läuft der Auftrag weiter (Vermerk).
            ``None``: nichts freigeben, wie bis zum 22.10.2026.
        quelle: **Woher der Auftrag kommt.** Vorgabe :mod:`aiimaging.bruecke` — die
            fremde Warteschlange. Die zweite Ablage ist :mod:`aiimaging.eigene_quelle`,
            unser eigenes Auftragsverzeichnis, in das der MCP-Einlass schreibt.

            Eine Quelle ist kein Objekt und keine Klasse, sondern acht Namen:
            ``QUELLEN_FEHLER``, ``STATUS_RUNNING``, ``STATUS_ERROR``,
            ``offene_auftraege``, ``laufzettel_pfad``, ``lies_auftrag``, ``setze_status``,
            ``schreibe_ergebnis``. Beide Module führen sie.

            Für Fortschritt und Abbruch (20.10.2026) dazu ``lies_status``,
            ``artefakt_bereitstellen``, ``setze_fortschritt`` und ``setze_teilbild``;
            fehlen sie, läuft alles wie vorher, nur ohne Fortschritt und Teilbild.

            **Warum überhaupt zwei.** Bis zum 26.08.2026 gab es zwei Nähte, die dasselbe
            versprachen, und nur eine hatte einen Ausführer: Ein über den MCP-Einlass
            bestellter Render ging auf ``queued`` und blieb dort für immer liegen. Statt
            einen zweiten Ausführer zu bauen — mit einem zweiten Satz Riegel, der
            auseinanderläuft, sobald einer gepflegt wird — bekommt der eine Ausführer
            eine zweite Quelle.

    Returns:
        ``{tat, job_id, verzeichnis, grund, ergebnis, wache, warnungen,
        vertragsvorgaben}``. ``tat`` ist
        eine der ``TAT_*``-Konstanten. ``wache`` ist der Bericht des Beobachters oder
        ``None``, wenn keine Wache gebaut wurde.

        ``warnungen`` sind die des gelesenen Auftrags (:func:`aiimaging.bruecke.lies_auftrag`)
        — darunter der Hinweis, dass ein deutscher Prompt übersetzt wurde. Sie standen
        bis zum 22.08.2026 in ``lies_auftrag`` und wurden hier **nicht weitergereicht**:
        eine tote Kante, wie sie dieses Projekt schon mehrfach gefunden hat. Eine
        Warnung, die niemanden erreicht, ist keine.

        ``vertragsvorgaben`` steht **daneben** und nicht darin: die Hinweise, die jeden
        Auftrag gleich treffen. Am 26.08.2026 nachgezählt — es sind genau drei, und
        `tools/abholen.py` zeigte damals `warnungen[:3]`. Sie füllten also alle drei
        Plätze und **verdeckten** jede echte, auftragsspezifische Warnung, die im Code
        später steht.

    Die Wache **bricht nicht ab.** Sie schreibt mit. Ein Lauf, der 1800 s brauchte und
    davon 1500 s stand, ist damit von einem unterscheidbar, der 1800 s gerechnet hat —
    und diese Unterscheidung ist der ganze Zweck: Bisher sahen beide gleich aus.
    """
    if not callable(verarbeite):
        raise AbholerError(
            "verarbeite muss aufrufbar sein. Der Abholer rendert nicht selbst — was mit "
            "einem Auftrag geschieht, wird hereingereicht, damit die Reihenfolge dieses "
            "Moduls ohne GPU prüfbar bleibt."
        )
    ordner = Path(verzeichnis)
    antwort = {"tat": TAT_LIEGENGELASSEN, "job_id": ordner.name,
               "verzeichnis": ordner, "grund": "", "ergebnis": None, "wache": None,
               "warnungen": (), "vertragsvorgaben": (),
               # Immer da, auch wenn nie etwas zu vermerken war — ein Ergebnissatz mit
               # wechselnden Schluesseln zwingt jeden Auswerter, vor dem Lesen zu
               # verzweigen. `None` heisst: es lag kein Grund an.
               "grund_vermerkt": None,
               # Der flache Name des Teilbilds, nur nach einem Abbruch (20.10.2026).
               "teilbild": None,
               # Warum die Karte frei war, wenn eine Auskunft etwas sagte — etwa, dass das
               # eigene Sprachmodell entladen wurde (auf-20261020-291). `None`: nichts gesagt.
               "karte": None,
               # Der Satz der Bildeingang-Vorpruefung allein (auf-20261021-301, A3): In
               # `karte` stand er hinter dem Entlade-Satz und fiel im Journal der Kuerzung
               # auf 200 Zeichen zum Opfer. `None`: kein Bildeingang bestellt.
               "bildeingang": None,
               # Was vor dem Auftrag von der Grafikkarte genommen wurde (Entscheid 127).
               # `None`: nicht gefragt (keine Auskunft uebergeben oder nicht so weit gekommen).
               "freigegeben": None}

    try:
        auftrag = quelle.lies_auftrag(ordner, fremde_freigabe_gilt=fremde_freigabe_gilt)
    except quelle.QUELLEN_FEHLER as fehler:
        antwort["grund"] = f"Auftrag nicht lesbar: {fehler}"
        # AUCH DIESER WARTEGRUND GEHOERT AN DEN LAUFZETTEL (Befund 23.09.2026). Eine
        # dauerhaft unlesbare Bestellung — etwa eine Szene ohne `geometry.path` — blieb
        # auf `queued`, und der Grund stand nur in dieser Antwort, also im Journal.
        # Drueben sah man denselben Zustand wie beim Demolauf 12: wartet, Grund
        # unbekannt. `_grund_vermerken` faengt seine eigenen Fehler; ist auch der
        # Laufzettel unlesbar, steht das als `grund_vermerkt: "NEIN: ..."` hier.
        _grund_vermerken(quelle, ordner, antwort)  # auch der Lesefehler
        return antwort

    antwort["job_id"] = auftrag.get("job_id") or ordner.name
    antwort["warnungen"] = tuple(auftrag.get("warnungen") or ())
    antwort["vertragsvorgaben"] = tuple(auftrag.get("vertragsvorgaben") or ())

    if auftrag["maengel"]:
        antwort["grund"] = (
            "Der Auftrag hat Mängel, die einen Lauf verbieten:\n- "
            + "\n- ".join(auftrag["maengel"])
        )
        _grund_vermerken(quelle, ordner, antwort)
        # EIN WIDERSPRUCH IN DER BESTELLUNG HEILT NICHT DURCH WARTEN (auf-20261020-290,
        # Befund 5): `vis.guete` mit `vis.skip` blieb auf `queued` und wurde alle 30 s neu
        # gelesen und liegengelassen — 21 Durchgaenge in zehn Minuten, kein Endzustand. Ein
        # solcher Auftrag endet jetzt auf `error`, mit demselben Satz in `message` und
        # `error`. Alle anderen Maengel bleiben, was sie waren: liegengelassen mit Grund.
        if auftrag.get("maengel_endgueltig"):
            # FEHLT EINE DATEI AM RECHNER (Entscheid 113: Himmelsbild, Textur), steht der Satz
            # mit ihrem Namen auch im ERGEBNIS — die Oberflaeche liest `lieferstatus_grund`.
            fehlend = tuple((auftrag.get("szene") or {}).get("fehlende_dateien") or ())
            if fehlend:
                _abweisung_ablegen(quelle, ordner, auftrag, " ".join(fehlend), antwort)
            _endgueltig_abweisen(quelle, ordner, antwort)
        return antwort

    # DIE KARTE GEHOERT DEM BILD (Owner-Entscheid 127, 22.10.2026): vor jeder Pruefung der
    # Karte alle Modelle freigeben, die Ollama haelt — auch die eines anderen Programms. Die
    # Pruefungen danach sehen die freigegebene Karte. Scheitert die Freigabe, rechnet der
    # Auftrag trotzdem; ob der Speicher reicht, sagen die Pruefungen wie bisher.
    antwort["freigegeben"] = _karte_freigeben(karte_freigeben)

    darf, warum = _karte_frei(auftrag["laufzettel"], darf_rechnen)
    if not darf:
        antwort["grund"] = warum
        _grund_vermerken(quelle, ordner, antwort)
        return antwort
    # WARUM DIE KARTE FREI WAR (auf-20261020-291): Hat der Abholer dafuer das eigene
    # Sprachmodell entladen, steht der Satz «… entladen: qwen3:14b …» hier — bis dahin
    # verwarf `_karte_frei` ihn, und das Protokoll zeigte nur das «NICHT frei» von vorher.
    antwort["karte"] = warum or None

    # ZU WENIG GRAFIKSPEICHER: WARTEN MIT GRUND, NICHT LADEN UND STERBEN (B161/B1).
    # Dieselbe Form wie oben: Status bleibt `queued`, der Grund steht am Laufzettel.
    reicht, warum = _speicher_reicht(
        speicher_frei, gerechnetes_backbone(auftrag.get("szene") or {}))
    if not reicht:
        antwort["grund"] = warum
        _grund_vermerken(quelle, ordner, antwort)
        return antwort

    # MIT BILDEINGANG: KEIN FREMDES MODELL, GENUG FUER DEN GEMESSENEN BEDARF (auf-20261021-298).
    # Abgewiesen mit Satz und nicht in die Warteschlange gelegt: Modelle von KosmoOrbit entlaedt
    # Visbox nie, ein Warten darauf koennte unbegrenzt dauern, und ein Messlauf soll einen
    # Endzustand haben.
    lage_bi = _bildeingang_lage(auftrag.get("szene") or {}, bildeingang_karte)
    if lage_bi is not None and lage_bi["reicht"] is False and \
            _bildeingang_aus_vorgabe(auftrag.get("szene") or {}):
        # DIE VORGABE WEISST NICHT AB (Entscheid 138): Kam der Bildeingang aus der Vorgabe fuer
        # Varianten und reicht die Karte nicht, rechnet die Variante ohne ihn — mit Satz. Nur
        # ein ausdruecklich bestellter Bildeingang endet wie bisher mit Abweisung.
        auftrag["szene"] = bildeingang_vorgabe_zurueckziehen(auftrag["szene"], lage_bi["satz"])
        antwort["bildeingang"] = auftrag["szene"]["messschalter"]["bildeingang"]["grund"]
        lage_bi = None
    if lage_bi is not None:
        antwort["bildeingang"] = lage_bi.get("satz") or None
    if lage_bi is not None and lage_bi["reicht"] is False:
        antwort["grund"] = lage_bi["satz"]
        antwort["karte"] = lage_bi["satz"]
        _abweisung_ablegen(quelle, ordner, auftrag, lage_bi["satz"], antwort)
        # DER SATZ AUCH IN `message` (auf-20261021-301, A1): Er stand nur in `error` und im
        # Ergebnis; die Anzeige liest `message`. Vor dem Statuswechsel, wie bei den Maengeln.
        _grund_vermerken(quelle, ordner, antwort)
        _endgueltig_abweisen(quelle, ordner, antwort)
        return antwort
    if lage_bi is not None and lage_bi.get("satz"):
        antwort["karte"] = " ".join(t for t in (antwort.get("karte"), lage_bi["satz"]) if t)

    # Ein Auftrag, der jetzt LÄUFT, darf die Begründung von vorhin nicht mehr tragen.
    # Ohne diese Zeile bliebe „die Karte war nicht frei" an einem Auftrag stehen, der
    # gerade rechnet — und wäre von einem, der noch wartet, nicht zu unterscheiden.
    _grund_vermerken(quelle, ordner, {"grund": ""})

    # Ab hier wird gerechnet. Erst jetzt auf `running` — vorher hätte ein
    # liegengelassener Auftrag ausgesehen, als arbeite jemand an ihm.
    quelle.setze_status(ordner, quelle.STATUS_RUNNING)
    beobachter = _beobachter_bauen(auftrag, wache_bauen, beobachtungs_takt_s, antwort)
    if beobachter is not None:
        beobachter.start()
    try:
        ergebnis = verarbeite(auftrag)
    except AuftragAbgebrochen as abbruch:
        # DER NUTZER HAT ABGEBROCHEN (20.10.2026). Der Status bleibt `cancelled` — er steht
        # schon dort, gesetzt von dem, der abbrach. Kein Ergebnis, keine Guetewerte; nur
        # das letzte fertige Zwischenbild als `teilbild`.
        antwort.update(tat=TAT_ABGEBROCHEN, grund=f"{abbruch} Kein Ergebnis geschrieben.")
        antwort["teilbild"] = _teilbild_zustellen(quelle, ordner, abbruch.teilbild,
                                                  abbruch.kamera)
        # DER SATZ GEHOERT AN DEN LAUFZETTEL (auf-20261020-290, 6a/6b): Er stand nur im
        # Protokoll des Abholers, `message` blieb «Vom Nutzer abgebrochen.». Der Vermerk
        # fasst den Status nicht an — `cancelled` bleibt (`vermerke_grund` unter der Sperre).
        _abbruch_vermerken(quelle, ordner, antwort)
        return antwort
    except Exception as fehler:            # noqa: BLE001 — jeder Fehler ist ein Ergebnis
        if _steht_abgebrochen_in(quelle, ordner):
            # Abgebrochen UND gescheitert: Der Abbruch gilt. `error` ueber `cancelled` zu
            # schreiben hiesse, dem Nutzer einen Fehler zu melden, den er nicht mehr
            # wartet — und in der eigenen Ablage ist `cancelled` ein Endzustand.
            antwort.update(tat=TAT_ABGEBROCHEN, grund=(
                f"Abgebrochen; der Lauf scheiterte danach an {type(fehler).__name__}: "
                f"{fehler}. Der Status bleibt '{bruecke.STATUS_CANCELLED}'."))
            _abbruch_vermerken(quelle, ordner, antwort)
            return antwort
        # WIES DAS BILDMODELL IM PROZESS DEN BILDEINGANG AB, GIBT ES EIN ERGEBNIS MIT DEM SATZ
        # (auf-20261021-300, N2) — wie bei der Vorpruefung oben: `lieferstatus: fehlgeschlagen`,
        # der Satz als `lieferstatus_grund` und in `message`. Bis 0.3.13 stand er nur in
        # `job.json/error`, und die Oberflaeche las ein Ergebnis, das es nicht gab.
        abweisung = render.bildeingang_abweisung_in(fehler)
        if abweisung:
            _abweisung_ablegen(quelle, ordner, auftrag, abweisung, antwort)
        quelle.setze_status(ordner, quelle.STATUS_ERROR, fehler=str(fehler))
        if abweisung:
            _grund_vermerken(quelle, ordner, {"grund": abweisung})
        antwort.update(tat=TAT_FEHLER, grund=(
            f"Verarbeitung gescheitert: {type(fehler).__name__}: {fehler}. Der Auftrag "
            f"ist auf '{quelle.STATUS_ERROR}' gesetzt — ein Auftrag ohne Antwort ist "
            f"für den Wartenden dasselbe wie ein hängender Rechner."))
        # REICHTE DER SPEICHER MITTEN IM LAUF NICHT, STEHT DAS AUCH IN `message`
        # (B161/B1). `error` trägt die Ausnahme wörtlich; die Anzeige drüben liest
        # `message` («Abbruch-/Wartegrund, UI-lesbar»), und dort stand bis zum 24.09.2026
        # nichts. Der Vermerk fasst den Status nicht an — er bleibt `error`.
        if ist_speichermangel(fehler):
            _grund_vermerken(quelle, ordner, {"grund": _speichermangel_satz(fehler)})
        return antwort
    finally:
        # Auch auf dem Fehlerweg: Ein Faden, den niemand anhält, läuft weiter und sieht
        # einem Auftrag zu, den es nicht mehr gibt.
        if beobachter is not None:
            antwort["wache"] = beobachter.stop()

    if not isinstance(ergebnis, dict):
        quelle.setze_status(ordner, quelle.STATUS_ERROR,
                            fehler="verarbeite lieferte kein Wörterbuch")
        antwort.update(tat=TAT_FEHLER, grund=(
            f"verarbeite lieferte {type(ergebnis).__name__} statt eines Wörterbuchs mit "
            f"'bilder'. Der Auftrag ist auf '{quelle.STATUS_ERROR}' gesetzt."))
        return antwort

    # ABGEBROCHEN NACH DEM LETZTEN BLICK (20.10.2026): Der Verarbeiter sieht zwischen den
    # Phasen nach; fiel der Abbruch in den letzten Schritt — oder kam ein Verarbeiter ohne
    # Blick —, steht hier `cancelled`. Bis zu diesem Tag schrieb der Abholer dann sein
    # Ergebnis und setzte `done` UEBER den Abbruch (Bruecke) bzw. scheiterte am Automaten
    # (eigene Ablage, `cancelled` ist dort Endzustand).
    if _steht_abgebrochen_in(quelle, ordner):
        bilder = [b for b in (ergebnis.get("bilder") or []) if Path(b).is_file()]
        antwort.update(tat=TAT_ABGEBROCHEN, grund=(
            "Abgebrochen, als der Lauf schon fertig war — kein Ergebnis geschrieben, "
            "das letzte Bild steht als Teilbild."))
        _endstand_abgebrochen(quelle, ordner)
        antwort["teilbild"] = _teilbild_zustellen(
            quelle, ordner, bilder[-1] if bilder else None,
            Path(bilder[-1]).parent.name if bilder else None)
        _abbruch_vermerken(quelle, ordner, antwort)
        return antwort

    if antwort["freigegeben"] is not None:
        # ADDITIV IM ERGEBNIS (Entscheid 127): `angewandt.freigegeben` — was vor dem Lauf von
        # der Karte genommen wurde. Auch im befund.json, das `angewandt` mitschreibt.
        ergebnis = {**ergebnis, "angewandt": {**(ergebnis.get("angewandt") or {}),
                                              "freigegeben": antwort["freigegeben"]}}
    uebersprungen = bool(ergebnis.get("uebersprungen"))
    geschrieben = quelle.schreibe_ergebnis(
        ordner, ergebnis.get("bilder") or [],
        job_id=auftrag.get("job_id"),
        geometrie_urteil=ergebnis.get("geometrie_urteil"),
        stil_urteil=ergebnis.get("stil_urteil"),
        zeiten=_zeiten_mit_stillstand(ergebnis.get("zeiten"), antwort["wache"]),
        # WARUM einzelne Kameras kein Bild bekamen. Ohne diese Durchreichung stuende im
        # Vertragsergebnis nur, DASS nichts gemessen wurde — siehe `_nicht_gerendert_kurz`.
        nicht_gerendert=_nicht_gerendert_kurz(ergebnis.get("kameras")),
        # QA JE KAMERA. Ihr Vertrag traegt das Feld seit dem 03.09.2026; wir haben es
        # acht Tage lang nicht gesendet, und der Einbau-Stand fuehrte den Posten
        # derweil als IHRE Vertragsaenderung. Gebaut heisst nicht angeschlossen —
        # dieselbe Lehre wie bei `uebersprungen` am 26.08.
        # SEIT DEM 23.09.2026 MIT DER LIEFERUNG JE KAMERA — siehe
        # `_je_kamera_mit_lieferung`. Ohne sie galt drueben fuer jedes Ergebnis die
        # Vorgabe `lieferstatus: 'geliefert'`, auch fuer eines ohne Bild.
        je_kamera=_je_kamera_mit_lieferung(ergebnis.get("kameras")),
        # Ohne diese Durchreichung stuende im Vertragsergebnis eines ABBESTELLTEN
        # Auftrags «keine QA gelaufen» — ununterscheidbar von einem vergessenen Lauf.
        # Gefunden am 26.08.2026 vom Kettenlauf-Test, nicht von den Bausteintests: Die
        # vierte Lage war gebaut, gepruft und an der NAHT nicht angeschlossen.
        uebersprungen=uebersprungen,
        **({"engine": ergebnis["engine"]} if ergebnis.get("engine") else {}),
        **({"ebenen": ergebnis["ebenen"]} if ergebnis.get("ebenen") else {}),
        **({"grundlage": ergebnis["grundlage"]} if ergebnis.get("grundlage") else {}),
        # Entscheid 104: nur, wenn der Auftrag eine Guete trug — wie `grundlage`.
        **({"guete": ergebnis["guete"]} if ergebnis.get("guete") else {}),
        # Stimmung, Kamera, Oberflaeche — wie gerechnet; nur, wenn etwas davon bestellt war.
        **({"angewandt": ergebnis["angewandt"]} if ergebnis.get("angewandt") else {}),
    )
    anzahl = len(ergebnis.get("bilder") or [])
    antwort.update(
        tat=TAT_VERARBEITET, ergebnis=geschrieben,
        grund=("Abbestellt (skip: true) — nichts gerechnet." if uebersprungen
               else f"Nur Grundlage: {anzahl} Cycles-Bild(er), kein KI-Schritt."
               if ergebnis.get("nur_grundlage")
               else f"{anzahl} Bild(er) geschrieben."))
    # NACH dem Vertragsergebnis und nach setze_status: Der Befund ist unsere eigene
    # Buchführung, nicht Teil der Abmachung — er darf die Reihenfolge nicht stören, an
    # der die fremde Oberfläche hängt.
    _befund_ablegen(ordner, auftrag, ergebnis, antwort)
    return antwort


def _steht_abgebrochen_in(quelle, ordner) -> bool:
    """Steht der Auftrag in DIESER Quelle auf ``cancelled``? Unlesbar heisst: nein."""
    lies = getattr(quelle, "lies_status", None)
    if lies is None:
        return False
    try:
        return lies(ordner) == bruecke.STATUS_CANCELLED
    except Exception:                      # noqa: BLE001 — unlesbar ist kein Abbruch
        return False


#: Der Anfang der Meldung nach einem Abbruch — wie ihn `knotenweg.abbrechen` schreibt.
SATZ_ABGEBROCHEN = "Vom Nutzer abgebrochen."


def _abbruch_vermerken(quelle, ordner, antwort: dict) -> None:
    """Den Abbruchsatz in ``message`` schreiben, ohne den Status ``cancelled`` anzufassen.

    ``message`` lautet danach «Vom Nutzer abgebrochen. Abgebrochen bei Kamera 2 von 2, vor
    dem Bildmodell. Kein Ergebnis geschrieben.» — der erste Satz bleibt, damit die Anzeige
    weiter erkennt, wer abbrach. ``grund_vermerkt`` sagt wie sonst, ob es gelang.
    """
    vermerk = {"grund": f"{SATZ_ABGEBROCHEN} {antwort.get('grund') or ''}".strip()}
    _grund_vermerken(quelle, ordner, vermerk)
    antwort["grund_vermerkt"] = vermerk.get("grund_vermerkt")


def _abweisung_ablegen(quelle, ordner, auftrag: dict, grund: str, antwort: dict) -> None:
    """Ein Ergebnis ohne Bild, ``lieferstatus: 'fehlgeschlagen'`` und dem Satz, neben den Auftrag.

    Vor dem Statuswechsel geschrieben — dieselbe Reihenfolge wie ``schreibe_ergebnis``: Wer
    ``error`` sieht, findet das Ergebnis schon vor. Scheitert das Schreiben, bleibt es bei der
    Abweisung am Laufzettel; ``antwort["ergebnis"]`` ist dann ``None``.
    """
    import json
    job_id = auftrag.get("job_id") or Path(ordner).name
    ergebnis = _kosmo_szene.nur_vertragsfelder(_kosmo_szene.als_abweisung(
        job_id, grund, angewandt=angewandt_der_szene(auftrag.get("szene") or {})))
    ziel = Path(ordner) / getattr(quelle, "DATEI_ERGEBNIS", bruecke.DATEI_ERGEBNIS)
    try:
        tmp = ziel.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(ergebnis, ensure_ascii=False, indent=2, default=list),
                       encoding="utf-8")
        tmp.replace(ziel)
    except OSError:
        return
    antwort["ergebnis"] = ergebnis


def kamerawerte_des_auftrags(szene: dict, *, auto_richtungen, brennweite_mm, kamera_modus,
                             deckungsgrad, augenhoehe) -> dict:
    """Richtungen und Kamerawerte DIESES Auftrags — aus ``cameras_auto``, sonst vom Abholer.

    Bis zum 20.10.2026 galten Richtungen, Augenhoehe, Brennweite, Deckungsgrad und
    Kameramodus nur als Einstellungen des ganzen Abholers (``verarbeiter(...)``). Der Knoten
    «Kamera» bestellt sie je Auftrag (``cameras_auto``, Vorgaben in
    ``kosmo_szene.kameras_auto_aus_szene``): senkrecht → ``MODUS_SHIFT``, frei →
    ``MODUS_GEKIPPT``; ``abstand {art: 'fest'}`` → ``abstand_fest_m``, sonst ``fuellt`` als
    Deckungsgrad.
    """
    auto = (szene or {}).get("kameras_auto")
    if not auto:
        return {"richtungen": tuple(auto_richtungen), "brennweite_mm": brennweite_mm,
                "kamera_modus": kamera_modus, "deckungsgrad": deckungsgrad,
                "augenhoehe": augenhoehe, "abstand_fest_m": None, "quelle": "abholer"}
    abstand = auto["abstand"]
    return {"richtungen": tuple(auto["richtungen"]), "brennweite_mm": auto["brennweite_mm"],
            "kamera_modus": (_kameras_modul.MODUS_SHIFT
                             if auto["perspektive"] == _kosmo_szene.PERSPEKTIVE_SENKRECHT
                             else _kameras_modul.MODUS_GEKIPPT),
            "deckungsgrad": abstand.get("fuellt") if abstand["art"] == "auto" else None,
            "augenhoehe": auto["augenhoehe_m"],
            "abstand_fest_m": abstand.get("meter") if abstand["art"] == "fest" else None,
            "quelle": "auftrag"}


def senkrecht_gestellt(aufgabe: dict) -> dict:
    """Eine mitgesandte Kamera mit ``perspektive: 'senkrecht'`` waagrecht stellen.

    Der Shift ersetzt die Kippung genau (``kameras.shift_aus_ziel``): dieselbe Richtung im
    Grundriss, das Ziel auf Augenhoehe, das Objektiv um ``shift_y`` verschoben — senkrechte
    Kanten bleiben senkrecht (Entscheid 109). Ohne ``perspektive`` oder mit ``'frei'``
    unveraendert; ohne Standort ebenso.
    """
    if aufgabe.get("perspektive") != _kosmo_szene.PERSPEKTIVE_SENKRECHT or \
            aufgabe.get("auge") is None or aufgabe.get("blick_auf") is None:
        return aufgabe
    schief = _kameras_modul.shift_aus_ziel(
        aufgabe["auge"], aufgabe["blick_auf"],
        brennweite_mm=aufgabe.get("brennweite_mm") or _kameras_modul.BRENNWEITE_MM)
    return dict(aufgabe, blick_auf=list(schief["waagrechtes_ziel"]),
                shift_y=_kameras_modul.blender_shift_y(schief["shift_mm"]),
                senkrecht={"shift_mm": round(schief["shift_mm"], 4),
                           "neigung_ersetzt_grad": round(schief["neigung_grad"], 4),
                           "warnungen": list(schief["warnungen"])})


#: Der Name der Materialwahl im Auftragsordner — lebt nur zur Laufzeit am Heim-PC.
DATEI_MATERIALWAHL = "materialwahl.json"
MATERIALWAHL_SCHEMA = "aiimaging.materialwahl/v1"


def materialwahl_ablegen(ordner, szene: dict) -> Path:
    """Die Materialwahl als JSON fuer den Runner: je Art Wahl, Karten und Fugen.

    Die Karten stehen mit ihrem Pfad am Heim-PC darin — die Datei liegt nur im
    Auftragsordner dieses Rechners und geht nie ins Ergebnis (Regel 3). «weiss» steht
    nicht hier: das Gipsmodell schaltet ``--umgebung-weiss``.
    """
    import json
    from . import materialwahl as _materialwahl
    arten = {}
    for art, wahl in (szene.get("materialien") or {}).items():
        dateien = (szene.get("materialien_dateien") or {}).get(art)
        if not dateien:
            continue
        eintrag = _materialwahl.BIBLIOTHEK[wahl["id"]]
        arten[art] = dict(wahl, asset=dateien.get("asset"), groesse=dateien.get("groesse"),
                          karten={k: str(v) for k, v in dateien["karten"].items()},
                          fugen=dict(eintrag["fugen"]) if eintrag.get("fugen") else None)
    ziel = Path(ordner) / DATEI_MATERIALWAHL
    ziel.parent.mkdir(parents=True, exist_ok=True)
    tmp = ziel.with_suffix(".json.tmp")
    tmp.write_text(json.dumps({"schema": MATERIALWAHL_SCHEMA, "arten": arten},
                              ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
    tmp.replace(ziel)
    return ziel


#: Welche Lichtdaten der Stimmung an Blender gehen (``--umgebung-licht``, auf-20261020-293).
LICHT_AN_BLENDER = ("sonne", "sonnen_staerke", "fuell_staerke", "winkel_grad", "look",
                    "hintergrund_richtung", "hintergrund_abstand_ev", "gelaende_grau",
                    "herkunft_licht",
                    # auf-20261020-294 (B1, B2): Sonne seitlich der Kamera, weicher Rueckfall.
                    "sonne_seitlich_grad", "sonne_seite", "winkel_weich_grad",
                    # auf-20261020-295 (N1): wie die Vorprobe das Haus misst.
                    "haus_mass")


def drehung_bestellt(szene: dict) -> bool:
    """Ob ``render.environment.rotationGrad`` ausdruecklich bestellt war (auf-20261020-294, B1).

    Nur dann geht die Drehung an Blender; sonst dreht der Runner das Himmelsbild je Kamera so,
    dass die Sonne seitlich der Blickachse steht. Ein ausdrueckliches ``rotationGrad`` des
    Nutzers hat Vorrang — auch ``0``.
    """
    return "rotationGrad" not in tuple((szene or {}).get("umgebung_vorgaben") or ())


def umgebung_einstellungen(szene: dict) -> dict:
    """Was die bestellte Stimmung an ``seams.glb_zu_multipass`` gibt — leer ohne Stimmung.

    ``umgebung_weiss`` bei «weiss» (Entscheid 113): alle Oberflaechen weiss wie ein
    Gipsmodell. Ohne Datei (nur bei ``vis.grundlage``, dann rechnet Blender nicht) kein Pfad.
    """
    umgebung = (szene or {}).get("umgebung")
    if not umgebung:
        return {}
    datei = (szene or {}).get("umgebung_datei") or {}
    # `dict(...)` mit Schluesselwoertern, nicht `update` — so liest die Probe der Kette
    # (tests/test_kette.py, `_was_der_abholer_bestellt`) aus dem Quelltext, was bestellt wird.
    licht = _stimmung.licht_der_stimmung(umgebung.get("preset"))
    aus = dict(umgebung_hdr=str(datei["pfad"]), umgebung_staerke=umgebung["intensitaet"],
               umgebung_belichtung=licht["belichtung_ev"]) if datei.get("pfad") else {}
    # DIE DREHUNG NUR, WENN BESTELLT (auf-20261020-294, B1): Sonst rechnet der Runner sie je
    # Kamera (Sonne `sonne_seitlich_grad` neben der Blickachse) — im Schluessel der
    # Grundlage stehen dafuer die Kamera und die Lichtdaten. Ohne Lichtdaten (eine Stimmung
    # vor 293) ginge die Vorgabe 0 wie bisher.
    if aus and (drehung_bestellt(szene) or not licht.get("sonne_seitlich_grad")):
        aus = dict(aus, umgebung_drehung=umgebung["rotationGrad"])
    if aus and licht["toenung_linear"] is not None:
        aus = dict(aus, umgebung_toenung=tuple(licht["toenung_linear"]))
    # LICHT MIT SCHATTEN (auf-20261020-293): Sonne, Fuelllicht, Look, Hintergrundabstand und
    # Grau der Platte als JSON — ein Text, damit der Schluessel der Grundlage ihn wie jeden
    # anderen Wert fasst (neue Lichtdaten, neue Grundlage).
    if aus and licht.get("sonne") is not None:
        import json as _json  # noqa: PLC0415
        lichtdaten = {k: licht[k] for k in LICHT_AN_BLENDER if k in licht}
        # DER MESSSCHALTER «HIMMEL SICHTBAR» (auf-20261021-309, Option Himmel): nur mit
        # `vis.himmel_sichtbar: true`, in den Lichtdaten — damit im Schluessel der Grundlage.
        # Ohne Schalter bleibt der Text Wort fuer Wort wie vorher.
        if szene.get("himmel_sichtbar") is True:
            lichtdaten["himmel_sichtbar"] = True
            # DER HIMMEL PASST ZUR STIMMUNG (Ergebnis 333): die Untergrenze des sichtbaren
            # Himmels — neue Lichtdaten, also neue Grundlage; der alte, zu dunkle Himmel wird
            # nicht wiederverwendet. Ohne Schalter bleibt der Text wie vorher.
            lichtdaten["himmel_untergrenze"] = _stimmung.himmel_untergrenze(
                umgebung.get("preset"))
            # BODEN BIS ZUM HORIZONT (Ergebnis 334): unter dem Horizont sieht die Kamera Boden
            # statt der unteren Haelfte des Himmelsbilds. Ein Lichtdatum, damit ein Bild von
            # vorher (gespiegelter Himmel) weder Grundlage noch Zwischenspeicher-Treffer ist.
            lichtdaten["boden_bis_horizont"] = True
            # DIE FASSUNG DES BODENS (Ergebnis 335): seither so hell und gefaerbt wie die
            # Platte unter Sonne und Himmel. Ein neues Lichtdatum, damit das dunkle Blaugrau
            # von 335 weder Grundlage noch Zwischenspeicher-Treffer ist.
            lichtdaten["boden_fassung"] = _stimmung.BODEN_FASSUNG
        aus = dict(aus, umgebung_licht=_json.dumps(lichtdaten, sort_keys=True,
                                                   ensure_ascii=False))
    if umgebung.get("preset") == _stimmung.PRESET_WEISS:
        aus = dict(aus, umgebung_weiss=True)
    return aus


def himmel_aufloesung_aus_bericht(bericht) -> str | None:
    """Die Groesse des Himmelsbilds, mit dem Blender DIESE Kamera rechnete — ``'2k'``/``'4k'``
    aus dem Dateinamen im Bericht (``umgebung.datei``, Ablageform ``<preset>__<hdri>_<2k|4k>.hdr``);
    ``None``, wenn nicht ablesbar (auf-20261021-306, B4)."""
    import re  # noqa: PLC0415
    datei = ((bericht or {}).get("umgebung") or {}).get("datei") if isinstance(bericht, dict) \
        else None
    treffer = re.search(r"_(\d+k)\.[A-Za-z]+$", str(datei or ""))
    return treffer.group(1) if treffer else None


def drehung_aus_bericht(bericht) -> float | None:
    """Die Drehung des Himmelsbilds, die Blender fuer DIESE Kamera gerechnet hat — oder ``None``.

    Nur bei ``umgebung.drehung.weg`` «zur_kamera» (auf-20261020-294, B1): Dann steht die
    wirkliche Drehung nur im Bericht der Kamera, nicht in der Bestellung.
    """
    drehung = ((bericht or {}).get("umgebung") or {}).get("drehung") \
        if isinstance(bericht, dict) else None
    if not isinstance(drehung, dict) or drehung.get("weg") != "zur_kamera":
        return None
    wert = drehung.get("drehung_grad")
    if not isinstance(wert, (int, float)) or isinstance(wert, bool):
        return None
    # In [0, 360) gelegt, auch nach dem Runden: der Vertrag nimmt 0..360, und ein fehlerhafter
    # Bericht (−5, 725) soll das Ergebnis drüben nicht verwerfen lassen.
    return round(float(wert) % 360.0, 3) % 360.0


def hintergrund_aus_bericht(bericht) -> dict | None:
    """Was hinter dem Haus stand, für DIESE Kamera — ``{art, kamerastrahl}`` aus dem
    Blender-Bericht (``umgebung.hintergrund``), auch aus einer Grundlage; ``None`` ohne Angabe.

    **Seit auf-20261022-327 (B8) im Ergebnis.** Bis dahin stand es nur im Bericht der Kamera
    (so las es 319); die Generalprobe suchte es im Ergebnis und fand es nicht. Ohne Farben und
    Datei — die Art genügt für die Frage «Himmelsbild oder Verlauf?».
    """
    hintergrund = ((bericht or {}).get("umgebung") or {}).get("hintergrund") \
        if isinstance(bericht, dict) else None
    if not isinstance(hintergrund, dict) or not hintergrund.get("art"):
        return None
    return {k: hintergrund[k] for k in ("art", "kamerastrahl") if hintergrund.get(k)}


def _einheitlich(je_kamera):
    """Der eine Wert aller Kameras — ``None``, wenn keiner da ist oder sie sich unterscheiden."""
    werte = {v for v in (je_kamera or {}).values() if v}
    return next(iter(werte)) if len(werte) == 1 else None


def _punktwolke_statt_splat(kontext: dict) -> dict | None:
    """Ist der bestellte Splat-Kontext eine **gewöhnliche Punktwolke**? Dann der Vermerk.

    Gelesen wird nur der PLY-Kopf (:func:`aiimaging.kontext_netz.fehlende_splat_felder`).
    ``None``: ein Splat, ein Netz, oder nicht sicher lesbar — dann bleibt alles wie bisher.
    """
    from . import kontext_netz as _kn

    pfad = Path(str(kontext.get("ply")))
    if not pfad.is_file():
        return None
    fehlend = _kn.fehlende_splat_felder(pfad)
    if not fehlend:
        return None
    return {"datei": pfad.name, "fehlende_felder": list(fehlend),
            "satz": _kn.satz_punktwolke_weggelassen(pfad.name, fehlend)}


def angewandt_der_szene(szene: dict, *, drehung_je_kamera: dict | None = None,
                        himmel_je_kamera: dict | None = None,
                        hintergrund_je_kamera: dict | None = None) -> dict:
    """``{environment?, cameras_auto?, materialien?}`` — was der Heim-PC rechnet, mit Vorgaben.

    Der Vertrag (mit dem Integrator, 20.10.2026) traegt fuer diese Felder keine Vorgaben;
    der Heim-PC setzt sie und nennt sie hier. Nur, was bestellt war. Ohne Pfade (Regel 3).

    **Die Drehung (auf-20261020-295, N3):** Bei ``drehung_weg`` «zur_kamera» fehlt
    ``rotationGrad`` — die Vorgabe 0 wurde nicht gerechnet, und ein Leser hielte sie fuer
    die Drehung. Stattdessen ``drehung_je_kamera {<kamera>: <grad>}`` aus dem Blender-Bericht
    je Kamera (fehlt, solange keine Kamera gerechnet hat). Bei «bestellt» bleibt
    ``rotationGrad`` wie bestellt.

    **Die Groesse des Himmelsbilds (auf-20261021-306, B4):** ``aufloesung`` kommt aus dem
    Blender-Bericht der Kameras (``himmel_je_kamera``, :func:`himmel_aufloesung_aus_bericht`) —
    auf einer wiederverwendeten Grundlage also die der Grundlage, nicht die der Guete dieser
    Bestellung (eine Vorschau auf einer 4k-Grundlage meldete «2k»). Nur ohne Bericht die Datei
    der Bestellung bzw. die Guete.
    """
    szene = szene or {}
    aus: dict = {}
    umgebung = szene.get("umgebung")
    if umgebung:
        datei = szene.get("umgebung_datei") or {}
        zusatz = next((z for z in szene.get("prompt_zusaetze") or ()
                       if z.get("art") == "stimmung"), None)
        # Gedreht wird je Kamera nur, wenn nicht bestellt UND die Stimmung eine seitliche
        # Sonne nennt — sonst geht `rotationGrad` (die Vorgabe 0) an Blender, wie
        # `umgebung_einstellungen` es tut, und bleibt hier stehen.
        bestellt = drehung_bestellt(szene)
        zur_kamera = not bestellt and bool(
            _stimmung.licht_der_stimmung(umgebung.get("preset")).get("sonne_seitlich_grad"))
        aus["environment"] = dict(
            {k: v for k, v in umgebung.items() if not zur_kamera or k != "rotationGrad"},
            aufloesung=(_einheitlich(himmel_je_kamera) or datei.get("aufloesung")
                        or _stimmung.aufloesung_fuer(szene.get("guete"))),
            datei=datei.get("datei"),
            vorgaben=list(szene.get("umgebung_vorgaben") or ()),
            gipsmodell=umgebung.get("preset") == _stimmung.PRESET_WEISS,
            # Seit auf-20261020-293 steht auch ohne bestellte Sonne eine Lampe: die harte
            # Sonne aus dem Himmelsbild (`licht.sonne`) oder eine weiche aus dem hellsten
            # Bereich. `sonnenlampe` sagt weiter nur, ob eine Sonne BESTELLT war.
            sonnenlampe=bool(szene.get("sonne")),
            # WIE GEDREHT WIRD (auf-20261020-294, B1): «zur_kamera» — je Kamera, Sonne
            # seitlich der Blickachse (die gerechnete Drehung seit 295 unter
            # `drehung_je_kamera`, `rotationGrad` fehlt); «bestellt» — `rotationGrad` wie
            # bestellt; «vorgabe» — eine Stimmung ohne seitliche Sonne, Drehung 0.
            drehung_weg=("bestellt" if bestellt else "zur_kamera" if zur_kamera
                         else "vorgabe"),
            prompt_satz=(zusatz or {}).get("satz"),
            # Belichtung, Farbtemperatur und Tonwerte je Stimmung (auf-20261020-292) —
            # Daten des Heim-PC, keine Felder des Vertrags; hier, damit das Ergebnis sagt,
            # womit gerechnet wurde.
            licht={k: v for k, v in
                   _stimmung.licht_der_stimmung(umgebung.get("preset")).items()
                   if v is not None},
            herkunft=dict(_stimmung.HERKUNFT))
        if zur_kamera and drehung_je_kamera:
            aus["environment"]["drehung_je_kamera"] = {
                str(k): float(v) for k, v in sorted(drehung_je_kamera.items())}
        # WAS HINTER DEM HAUS STAND (auf-20261022-327, B8): Himmelsbild oder Verlauf, je
        # Kamera aus dem Blender-Bericht — fehlt, solange keine Kamera gerechnet hat.
        if hintergrund_je_kamera:
            aus["environment"]["hintergrund_je_kamera"] = {
                str(k): dict(v) for k, v in sorted(hintergrund_je_kamera.items())}
    # DIE SAETZE DER KNOTEN IM PROMPT (auf-20261022-327, B8) — bis dahin nur im Befund; der
    # Vermerk zum Feld (`kosmo_szene.FELD_WEG['prompt_zusaetze']`) nannte das Ergebnis schon.
    if szene.get("prompt_zusaetze"):
        aus["prompt_zusaetze"] = [dict(z) for z in szene["prompt_zusaetze"]]
    auto = szene.get("kameras_auto")
    if auto:
        aus["cameras_auto"] = {k: (dict(v) if isinstance(v, dict) else
                                   list(v) if isinstance(v, (list, tuple)) else v)
                               for k, v in auto.items()}
        if szene.get("kameras_umgedeutet"):
            aus["cameras_auto"]["umgedeutet"] = dict(szene["kameras_umgedeutet"])
    if szene.get("materialien"):
        from . import materialwahl as _materialwahl
        dateien = szene.get("materialien_dateien") or {}
        aus["materialien"] = {
            # `toenung` fehlt, wenn keine bestellt war — ein `null` bestuende ihr
            # `.optional()` nicht.
            art: dict({k: v for k, v in wahl.items() if v is not None},
                      label=_materialwahl.BIBLIOTHEK[wahl["id"]]["label"],
                      asset=(dateien.get(art) or {}).get("asset"),
                      groesse=((dateien.get(art) or {}).get("groesse")
                               or _materialwahl.groesse_fuer(szene.get("guete"))),
                      vorgaben=list((szene.get("materialien_vorgaben") or {}).get(art) or ()),
                      herkunft=dict(_materialwahl.HERKUNFT))
            for art, wahl in szene["materialien"].items()}
    senkrecht = [k.get("kuerzel") for k in szene.get("kameras") or ()
                 if isinstance(k, dict) and k.get("perspektive")
                 == _kosmo_szene.PERSPEKTIVE_SENKRECHT]
    if senkrecht:
        aus["cameras_senkrecht"] = senkrecht
    # DER STOFF DER VARIANTE (Befund 337): Wunsch, vorher gewaehlt, und was ersetzt wurde.
    wunsch = szene.get("material_der_variante")
    if wunsch:
        aus["variante"] = {"material_wunsch": {k: v for k, v in dict(wunsch).items()
                                               if k != "satz"}}
        # DER SATZ INS ERGEBNIS (Ergebnis 339): Er stand nur in `befund.json`
        # (`warnungen_auftrag`); jetzt auch hier und in `qa.verdict.hinweise`.
        if wunsch.get("satz"):
            aus["variante"]["satz"] = wunsch["satz"]
    # DIE STIMMUNG DER VARIANTE (N6, Befund 340): wie beim Stoff der Vermerk und der Satz im
    # Ergebnis — bis dahin stand «STIMMUNG DER VARIANTE» nur in `befund.json`. Mit beiden steht
    # unter `satz` der des Stoffs (wie bisher) und unter `stimmung.satz` der der Stimmung;
    # `qa.verdict.hinweise` traegt beide (`kosmo_szene.ergebnis_saetze_der_szene`).
    stimmung_v = szene.get("stimmung_der_variante")
    if stimmung_v:
        aus.setdefault("variante", {})["stimmung"] = dict(stimmung_v)
        if stimmung_v.get("satz") and not aus["variante"].get("satz"):
            aus["variante"]["satz"] = stimmung_v["satz"]
    # DIE WEGGELASSENE PUNKTWOLKE (Geraeteprobe R59): Datei, fehlende Felder, Satz — ohne
    # Pfad. Der Satz geht von hier nach `qa.verdict.hinweise` (`ergebnis_saetze_der_szene`).
    weg = szene.get("kontext_weggelassen")
    if isinstance(weg, dict) and weg.get("satz"):
        aus["kontext_weggelassen"] = {k: weg.get(k) for k in ("datei", "fehlende_felder", "satz")}
    # DIE SCHALTER DER VARIANTEN-VORGABE (Entscheid 126): was gerechnet wurde und woher.
    schalter = messschalter_angewandt(szene)
    if schalter:
        aus["messschalter"] = schalter
    return aus


def _endgueltig_abweisen(quelle, ordner, antwort: dict) -> None:
    """Einen Auftrag mit endgültigem Mangel auf ``error`` setzen — mit dem Satz.

    Die eigene Ablage kennt ``queued → error`` nicht (``jobs.UEBERGAENGE``); dort geht es
    über ``running`` — ohne dass etwas gerechnet wird, im selben Augenblick. Scheitert auch
    das, bleibt der Auftrag liegengelassen mit Grund wie bisher, und ``antwort`` sagt es.
    """
    satz = antwort.get("grund") or "Der Auftrag widerspricht sich."
    try:
        try:
            quelle.setze_status(ordner, quelle.STATUS_ERROR, fehler=satz)
        except Exception:                  # noqa: BLE001 — der Automat der eigenen Ablage
            quelle.setze_status(ordner, quelle.STATUS_RUNNING)
            quelle.setze_status(ordner, quelle.STATUS_ERROR, fehler=satz)
    except Exception as fehler:            # noqa: BLE001 — Buchführung, kein Lauf
        antwort["grund"] = (f"{satz}\n(Nicht als Fehler beendet: {type(fehler).__name__}: "
                            f"{fehler} — der Auftrag bleibt liegen.)")
        return
    antwort["tat"] = TAT_FEHLER


def _endstand_abgebrochen(quelle, ordner) -> None:
    """Den Fortschritt auf :data:`PHASE_ABGEBROCHEN` setzen, das erreichte ``pct`` behalten.

    Für den Abbruch NACH dem letzten Blick des Verarbeiters — sonst stuende am Auftrag
    «pruefung, 1.0», als waere er fertig geworden. Ein Schreibfehler kostet nichts.
    """
    setze = getattr(quelle, "setze_fortschritt", None)
    if setze is None:
        return
    try:
        import json as _json
        datei = Path(ordner) / bruecke.DATEI_LAUFZETTEL
        if datei.is_file():
            jetzt = _json.loads(datei.read_text(encoding="utf-8")).get(bruecke.FELD_FORTSCHRITT)
        else:
            from . import jobs as _jobs  # noqa: PLC0415
            jetzt = _jobs.lies_job(Path(ordner).name, ordner).get("progress")
        setze(ordner, dict(jetzt or {"pct": 1.0}, phase=PHASE_ABGEBROCHEN, rest_s=None))
    except Exception as fehler:            # noqa: BLE001 — siehe Docstring
        import logging
        logging.getLogger(__name__).warning("Endstand nicht geschrieben: %s: %s",
                                            type(fehler).__name__, fehler)


def _teilbild_zustellen(quelle, ordner, pfad, kamera) -> str | None:
    """Das Teilbild flach in den Auftragsordner legen und am Auftrag nennen.

    Name ``<kamera>__teilbild.png`` (ohne Kamera ``teilbild.png``). Ohne Bild, ohne
    passende Quelle oder bei einem Schreibfehler: ``None`` — der Abbruch bleibt ein
    Abbruch, auch ohne Teilbild. Den Endstand des Fortschritts (Phase
    :data:`PHASE_ABGEBROCHEN`) hat der Verarbeiter schon geschrieben.
    """
    if not pfad or not Path(pfad).is_file():
        return None
    bereit = getattr(quelle, "artefakt_bereitstellen", None)
    setze = getattr(quelle, "setze_teilbild", None)
    if bereit is None or setze is None:
        return None
    name = f"{kamera}__{TEILBILD_ART}.png" if kamera else f"{TEILBILD_ART}.png"
    if not bruecke._ist_flacher_name(name):
        name = f"{TEILBILD_ART}.png"
    try:
        bereit(ordner, pfad, name)
        setze(ordner, name)
    except Exception as fehler:            # noqa: BLE001 — siehe Docstring
        import logging
        logging.getLogger(__name__).warning("Teilbild nicht zugestellt: %s: %s",
                                            type(fehler).__name__, fehler)
        return None
    return name


def _grund_vermerken(quelle, ordner, antwort: dict) -> None:
    """Den Grund, warum nichts geschah, an den Auftrag heften — nicht nur ins Journal.

    **Der Anlass ist Demolauf 12** (01.09.2026). 24 Durchgänge lang stand im Journal
    wörtlich *«Karte: NICHT frei — Auslastung 12 % (Grenze 10 %)»* und daneben
    *«Der Auftrag trägt 'idle_window_only' und die Karte ist nicht frei»*. Und
    gleichzeitig an der Oberfläche: *«WARTET — NICHT ABGEHOLT (GRUND UNBEKANNT) …
    Läuft auf der HomeStation ein Render-Abholer?»*

    Er lief und nannte den Grund alle 30 Sekunden. Nur stand der Grund im **Journal**,
    und der Auftrag trug ihn nicht. Das ist keine unglückliche Doppelmeldung, das ist
    eine fehlende Leitung: Wer den Auftrag liest — und die Oberfläche liest nichts
    anderes —, sieht ``status: "queued"`` und sonst nichts.

    Was NICHT geschieht: der Status wird nicht angefasst. ``queued`` ist richtig; der
    Auftrag wartet wirklich. Nur das WARUM kommt dazu, in das Feld, das ihr eigener
    Vertrag dafür führt (:data:`aiimaging.bruecke.FELD_MELDUNG`).

    ``antwort`` wird um ``grund_vermerkt`` ergänzt: ``True``, ``False`` mit
    Begründung — *ungeprüft ist nicht dasselbe wie in Ordnung*, und eine Buchführung,
    von der niemand weiss, ob sie stattfand, ist keine.
    """
    vermerke = getattr(quelle, "vermerke_grund", None)
    if not callable(vermerke):
        antwort["grund_vermerkt"] = (
            f"NEIN: {getattr(quelle, '__name__', quelle)!r} kennt kein "
            f"'vermerke_grund'. Der Grund steht nur im Journal — genau der Zustand, "
            f"gegen den diese Funktion gebaut ist.")
        return
    try:
        vermerke(ordner, antwort.get("grund") or "")
    except Exception as fehler:                # noqa: BLE001 — Buchführung, kein Lauf
        antwort["grund_vermerkt"] = f"NEIN: {type(fehler).__name__}: {fehler}"
        return
    antwort["grund_vermerkt"] = True


#: Dateiname des vollständigen Befunds, neben dem Vertragsergebnis.
DATEI_BEFUND = "befund.json"

#: Dateiname des Urteils EINER Kamera, in deren eigenem Ausgabeordner.
DATEI_URTEIL = "urteil.json"

#: Das Feld am Kameraurteil, das nennt, welche ausdruecklich gesetzten Rahmungswerte
#: (``kamera_modus``, ``deckungsgrad``, ``augenhoehe``, ``bias_grad``) NICHT an den
#: Runner gingen, weil die Kamera kein Richtungskuerzel hat (23.09.2026). ``None``:
#: nichts zurueckgehalten. Steht an jedem Urteil, auch an einem nicht gerenderten.
URTEIL_KAMERAWERTE_ZURUECK = "kamerawerte_zurueckgehalten"


def _urteil_ablegen(ordner, urteil: dict) -> None:
    """Das Urteil **einer** Kamera ablegen, sobald sie fertig ist.

    **Der Anlass ist Demolauf 12** (01.09.2026). Der Auftrag brach an der **zweiten**
    Kamera ab (``Expected all tensors to be on the same device``) — und das fertige,
    gemessene Urteil der **ersten** war damit weg. In keinem Ausgabeordner lag
    ``rho_maske``, ``geom_iou`` oder ``paarurteil``. Der Maskenweg sagte damit zum
    dritten Lauf in Folge nichts, jedes Mal aus einem anderen Grund: Lauf 10 fehlender
    Geländebeleg, Lauf 11 kein Diffusionsbild, Lauf 12 dieser Absturz.

    **Warum das nicht der Befund erledigt.** :func:`_befund_ablegen` schreibt alles —
    aber erst, wenn ``verarbeite`` **zurückgekehrt** ist. Eine Ausnahme in Kamera 2
    verlässt die Schleife, ``hole_einen`` fängt sie, setzt den Auftrag auf ``error``
    und kehrt zurück, ohne dass je ein Befund entstand. Alles, was Kamera 1 gekostet
    hat — Blender-Lauf, Diffusion, zwei Schätzerläufe —, ist dann nur noch Rechenzeit.

    *Ein gemessenes Urteil darf nicht an einem späteren Fehler sterben.* Darum steht
    diese Datei im Ordner **der Kamera**, nicht des Auftrags: Sie ist fertig, wenn die
    Kamera fertig ist, und was danach geschieht, geht sie nichts mehr an.

    Ein fehlgeschlagenes Ablegen darf den Lauf nicht kosten — dieselbe Entscheidung wie
    bei :func:`_befund_ablegen` und :func:`_auswahl_ablegen`. REGEL 3: Absolute Pfade
    werden auf Dateinamen gekürzt, die Datei liegt im Auftragsverzeichnis der fremden
    Oberfläche.
    """
    import json as _json

    try:
        ziel = Path(ordner)
        ziel.mkdir(parents=True, exist_ok=True)
        raster: dict = {}
        schlank = _raster_auslagern(_ohne_pfade(urteil), raster, DATEI_URTEIL_RASTER, "$.urteil")
        (ziel / DATEI_URTEIL).write_text(
            _json.dumps({"schema": "aiimaging.kameraurteil/v1",
                         "kamera": urteil.get("kamera"),
                         "urteil": schlank},
                        ensure_ascii=False, indent=1, default=str),
            encoding="utf-8")
        _raster_schreiben(ziel / DATEI_URTEIL_RASTER, raster)
    except Exception:                          # noqa: BLE001 — Buchführung, kein Lauf
        pass


def _ohne_pfade(wert):
    """Absolute Pfade auf ihren Dateinamen kürzen — **Regel 3**, rekursiv.

    Der Befund verlässt dieses Repo nicht, aber er liegt im Auftragsverzeichnis der
    fremden Oberfläche, und ein absoluter Pfad trägt den Rechnernamen und das
    Benutzerkonto nach draussen. Dasselbe Argument wie bei den Bildnamen in
    :func:`aiimaging.bruecke.schreibe_ergebnis` — dort war es bereits erledigt, hier
    wäre es beim ersten Befund wieder aufgemacht worden.

    Gekürzt wird alles, was wie ein absoluter Pfad aussieht. Ein Text, der zufällig mit
    ``/`` beginnt, verliert damit Information — die Richtung ist gewollt: Ein zu kurzer
    Pfad kostet einen Blick, ein durchgereichter Benutzername ist ein Regelbruch.
    """
    if isinstance(wert, dict):
        return {k: _ohne_pfade(v) for k, v in wert.items()}
    if isinstance(wert, (list, tuple)):
        return [_ohne_pfade(v) for v in wert]
    if isinstance(wert, Path):
        return wert.name
    if isinstance(wert, str) and wert.startswith("/") and len(wert) > 1:
        return Path(wert).name
    return wert


#: Ab so vielen Eintraegen gilt eine Liste aus Wahrheitswerten oder Zahlen als **Raster** (ein
#: Wert je Bildpunkt) und wird aus Befund und Kameraurteil ausgelagert (:func:`_raster_auslagern`).
#: Ein Bild hat Hunderttausende Bildpunkte; jede echte Aufzaehlung im Befund bleibt weit darunter.
RASTER_AB = 4096

#: Die Rohdaten der Raster neben dem Befund bzw. neben dem Kameraurteil.
DATEI_BEFUND_RASTER = "befund_raster.json"
DATEI_URTEIL_RASTER = "urteil_raster.json"

#: Wie ein Raster aus Wahrheitswerten in der Rasterdatei steht: je acht Bildpunkte ein Byte
#: (der erste im hoechsten Bit), mit zlib gepackt, als Base64-Text.
RASTER_KODIERUNG_BITS = "bits-zlib-base64"
RASTER_KODIERUNG_LISTE = "liste"


def _ist_raster(wert) -> bool:
    if not isinstance(wert, (list, tuple)) or len(wert) < RASTER_AB:
        return False
    return all(isinstance(v, (bool, int, float)) and not isinstance(v, dict) for v in wert)


def _bits_packen(werte) -> str:
    import base64 as _b64
    import zlib as _zlib

    roh = bytearray((len(werte) + 7) // 8)
    for i, v in enumerate(werte):
        if v:
            roh[i >> 3] |= 0x80 >> (i & 7)
    return _b64.b64encode(_zlib.compress(bytes(roh), 9)).decode("ascii")


def _bits_entpacken(text: str, laenge: int) -> list[bool]:
    import base64 as _b64
    import zlib as _zlib

    roh = _zlib.decompress(_b64.b64decode(text))
    return [bool(roh[i >> 3] & (0x80 >> (i & 7))) for i in range(laenge)]


def _raster_auslagern(wert, ablage: dict, datei: str, pfad: str = "$"):
    """Raster (ein Wert je Bildpunkt) aus einem Befund herausnehmen — im Befund bleiben Verweis
    und Kennzahlen, die Rohdaten kommen in ``ablage`` (Schluessel = Pfad im Befund).

    **Anlass: Visbox-Mac-Pruefliste 0.3.35 (22.10.2026).** ``befund.json`` des Auftrags mit vier
    Standpunkten (Grundbild und KI) war **93 MB** gross. Die Bauwerksmaske (``maskenbefund.maske``)
    und die Lage der Umgebung (``maskenbefund.kontext_pixel``) sind Listen mit einem Wahrheitswert
    je Bildpunkt; mit ``indent=1`` stand jeder Wert auf einer eigenen Zeile, rund zehn Bytes je
    Bildpunkt, je Kamera — und das Urteil der massgebenden Kamera ein zweites Mal unter
    ``geometrie_urteil``. Gelesen hat die Liste aus der Datei niemand: ``befund_kurz`` nennt Zahlen,
    die Werkzeuge (``beweisreihe``, ``studie_innenmessung``) lassen die Maske selbst schon weg.

    Ein Raster, das zweimal vorkommt (gleicher Inhalt), wird einmal abgelegt. Wahrheitswerte gehen
    gepackt (:data:`RASTER_KODIERUNG_BITS`, ein Bit je Bildpunkt), Zahlen als Liste. Zurueck holt
    sie :func:`lies_raster`.
    """
    gesehen: dict = {}

    def gang(w, p):
        if _ist_raster(w):
            nur_wahrheit = all(isinstance(v, bool) for v in w)
            eintrag = ({"laenge": len(w), "kodierung": RASTER_KODIERUNG_BITS,
                        "daten": _bits_packen(w)} if nur_wahrheit
                       else {"laenge": len(w), "kodierung": RASTER_KODIERUNG_LISTE,
                             "daten": list(w)})
            # Gleich ist gleich nach Inhalt — `_ohne_pfade` hat das Objekt schon kopiert.
            inhalt = (eintrag["kodierung"], len(w), str(eintrag["daten"]) if not nur_wahrheit
                      else eintrag["daten"])
            schluessel = gesehen.get(inhalt)
            if schluessel is None:
                schluessel = p
                gesehen[inhalt] = p
                ablage[p] = eintrag
            verweis = {"ausgelagert": datei, "schluessel": schluessel, "laenge": len(w)}
            if nur_wahrheit:
                verweis["wahr"] = sum(1 for v in w if v)
            return verweis
        if isinstance(w, dict):
            return {k: gang(v, f"{p}.{k}") for k, v in w.items()}
        if isinstance(w, (list, tuple)):
            return [gang(v, f"{p}[{i}]") for i, v in enumerate(w)]
        return w

    return gang(wert, pfad)


def _raster_schreiben(ziel: Path, ablage: dict) -> None:
    """Die ausgelagerten Raster schreiben — nur, wenn es welche gibt (sonst keine Datei)."""
    import json as _json

    if not ablage:
        return
    ziel.write_text(_json.dumps({"schema": "aiimaging.befund-raster/v1", "raster": ablage},
                                ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def lies_raster(verzeichnis, verweis) -> list | None:
    """Ein ausgelagertes Raster zurueck — aus seinem Verweis im Befund oder Urteil, sonst ``None``.

    Wirft nichts, wie :func:`lies_befund`: Eine fehlende oder unlesbare Rasterdatei ist eine
    Auskunft, kein Fehler.
    """
    import json as _json

    if not isinstance(verweis, dict) or not verweis.get("ausgelagert"):
        return None
    name = Path(str(verweis["ausgelagert"])).name
    try:
        daten = _json.loads((Path(verzeichnis) / name).read_text(encoding="utf-8"))
        eintrag = daten["raster"][verweis["schluessel"]]
        if eintrag["kodierung"] == RASTER_KODIERUNG_BITS:
            return _bits_entpacken(eintrag["daten"], int(eintrag["laenge"]))
        return list(eintrag["daten"])
    except (OSError, ValueError, KeyError, TypeError):
        return None


def _befund_ablegen(ordner, auftrag: dict, ergebnis: dict, antwort: dict) -> None:
    """Alles, was gemessen wurde, in **eine Datei** neben das Vertragsergebnis.

    **Warum es das gibt.** ``kosmovis.render-result/v2`` führt genau ``images``, ``qa``
    und ``timings``; alles Übrige streicht :func:`aiimaging.kosmo_szene.nur_vertragsfelder`
    heraus, und das ist richtig so — den fremden Vertrag zu erweitern ist nicht unsere
    Entscheidung.

    Nur: Bis zum 23.08.2026 hiess das, dass **nichts davon irgendwo landete**. Der
    Kompositionsbefund je Kamera, die Kameraspanne, der Maskenbefund, die Einordnung
    gegen den Nullanker, das Sprachurteil über den Prompt, die Warnungen des Auftrags —
    alles wurde gerechnet, in ein Wörterbuch gelegt und mit dem Prozess vergessen. Nur
    die Seedauswahl hatte eine eigene Datei.

    `CLAUDE.md` sagt den Satz, um den es geht: **Was nicht in einer Datei steht, ist
    weg.** Er stand dort für die Sitzungsprotokolle; er gilt für Messwerte genauso.

    Ein fehlgeschlagener Befund darf den Lauf nicht kosten — die Bilder sind da, das
    Vertragsergebnis ist geschrieben. Dieselbe Entscheidung wie bei
    :func:`_auswahl_ablegen`.
    """
    import json as _json

    szene = (auftrag.get("szene") or {})
    inhalt = {
        "schema": "aiimaging.befund/v1",
        "job_id": auftrag.get("job_id"),
        "kameras": ergebnis.get("kameras") or [],
        "geometrie_urteil": ergebnis.get("geometrie_urteil"),
        "stil_urteil": ergebnis.get("stil_urteil"),
        "zeiten": ergebnis.get("zeiten"),
        "bilder": [Path(b).name for b in (ergebnis.get("bilder") or [])],
        # Der Prompt in BEIDEN Fassungen — was gerendert wurde und was ankam.
        "prompt": szene.get("prompt"),
        "prompt_original": szene.get("prompt_original"),
        "prompt_sprache": szene.get("prompt_sprache"),
        "prompt_bauteile": list(szene.get("prompt_bauteile") or ()),
        # Was der Betreiber bestellt hat und nicht bekommt. Steht im Befund, weil es
        # sonst nirgends stünde: Der Vertrag hat für «gelesen und nicht beachtet» kein
        # Feld, und ein Bild sieht auch dann richtig aus, wenn die halbe Bestellung
        # unterwegs verlorenging.
        "stehengeblieben": [dict(e) for e in _kosmo_szene.stehengebliebene_felder(szene)],
        # Was die gewaehlten Kameras von der Dokumentationsnorm abdecken — und was nicht.
        # `komposition.fehlende_ansichten` stand seit dem 21.08.2026 ohne Aufrufer da
        # (tools/tote_kanten.py, 26.08.). Es ist keine Forderung nach zwoelf Kameras: Wie
        # viele Standpunkte ein Auftrag wert ist, ist eine Betriebsentscheidung. Es ist
        # die Auskunft, WAS DABEI WEGFAELLT.
        "habs_ansichten": _komposition.fehlende_ansichten(
            [k.get("kamera") for k in (ergebnis.get("kameras") or ())
             if k.get("kamera")]),
        # Der negative Prompt des Stils: keine Wirkung und kein Weg dorthin. Steht hier,
        # weil er sonst nirgends stuende — `komponiere` liegt nicht auf diesem Weg.
        "negativ_lage": negativ_lage(
            ((ergebnis.get("stil_urteil") or {}).get("stil")), gerechnetes_backbone(szene)),
        # Unter welcher Hochachse gerechnet wurde, und ob sie BESTELLT oder ANGENOMMEN
        # war. Der Vertrag hat kein Feld dafuer; ohne diese Zeile stuende nirgends, unter
        # welcher Voraussetzung die Geometriezahlen des Laufs ueberhaupt gelten.
        "hochachse": ergebnis.get("hochachse"),
        # Ob die Geometrie aus einer IFC umgewandelt wurde, und was das Tor dazu sagte;
        # und ob es eine Innenansicht war, aus welchem Raum (22.09.2026).
        "umwandlung": ergebnis.get("umwandlung"),
        "innenansicht": ergebnis.get("innenansicht"),
        # Der Modellstand des AUFTRAGS, auch ohne Kamera (23.09.2026): Bei einem
        # abbestellten Auftrag gibt es kein Kameraurteil, und bis dahin erreichte er
        # keine Datei — gebaut fuer «jeder Ergebnissatz», gelesen von niemandem.
        "modellstand": ergebnis.get("modellstand"),
        # Die Umgebung, wenn bestellt (Entscheid 76) — ohne Pfad, Regel 3.
        "kontext": _kosmo_szene.kontext_vermerk(szene.get("kontext")),
        # Die Skizze, wenn sie das Bild fuehrte (Entscheid 96) — ohne Pfad, Regel 3.
        "skizze": ergebnis.get("skizze"),
        # Stimmung, Kamera, Oberflaeche wie gerechnet (20.10.2026) — dieselbe Form wie im
        # Ergebnis, dazu die angefuegten Saetze der Knoten.
        "angewandt": ergebnis.get("angewandt"),
        "prompt_zusaetze": [dict(z) for z in szene.get("prompt_zusaetze") or ()],
        "warnungen_auftrag": list(antwort.get("warnungen") or ()),
        "vertragsvorgaben": list(antwort.get("vertragsvorgaben") or ()),
        "wache": antwort.get("wache"),
    }
    try:
        raster: dict = {}
        schlank = _raster_auslagern(_ohne_pfade(inhalt), raster, DATEI_BEFUND_RASTER)
        (Path(ordner) / DATEI_BEFUND).write_text(
            _json.dumps(schlank, ensure_ascii=False, indent=1),
            encoding="utf-8")
        _raster_schreiben(Path(ordner) / DATEI_BEFUND_RASTER, raster)
    except (OSError, TypeError, ValueError):
        # TypeError/ValueError: etwas im Befund ist nicht JSON-fähig. Auch das darf den
        # Lauf nicht kosten — aber es ist ein Fehler unserer Seite und kein Betriebsfall,
        # weshalb er hier NICHT stillschweigend gleich behandelt wird wie ein voller
        # Datenträger: Er steht im Grund der Antwort.
        antwort["grund"] = ((antwort.get("grund") or "") +
                            " Der Befund konnte nicht geschrieben werden.").strip()


def lies_befund(verzeichnis):
    """Den Befund eines Auftrags zurücklesen — oder ``None``.

    **Warum es diese Funktion gibt und nicht nur die schreibende.** Eine Datei, die
    geschrieben und nie gelesen wird, ist die tote Kante in ihrer geduldigsten Form: Sie
    fällt nie auf, weil niemand hinsieht, und wenn eines Tages jemand hinsieht, steht
    Unsinn darin, seit Monaten. Der Befund wird darum vom Betreiber-Werkzeug
    (`tools/abholen.py`) wirklich gelesen — damit er **trägt** und nicht nur existiert.

    Ein fehlender oder unlesbarer Befund ist kein Fehler, sondern eine Auskunft: Es gibt
    ihn nicht, mehr sagt diese Funktion nicht. Sie wirft nichts — sie wird auf einem
    Verzeichnis aufgerufen, über das nichts feststeht.
    """
    import json as _json

    pfad = Path(verzeichnis) / DATEI_BEFUND
    try:
        gelesen = _json.loads(pfad.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return gelesen if isinstance(gelesen, dict) else None


def _warnungsart(warnung: str) -> str:
    """Das erste Wort einer Warnung — ihre Art, nicht ihr Wortlaut.

    Die Warnungen aus :mod:`aiimaging.komposition` beginnen mit dem Gegenstand
    (``Bezugspunkt …``, ``Neigung 2.05° …``, ``Abstand 12.00 m …``). Nach diesem Wort
    lassen sie sich zusammenfassen, ohne ihren Text zu zerlegen — und wenn dort einmal
    etwas anderes steht, gruppiert diese Funktion eben feiner. Falsch wird sie davon
    nicht, nur ausführlicher.
    """
    return str(warnung).split(" ", 1)[0].rstrip(":")


def negativ_lage(stil: str | None, backbone_name: str | None) -> dict | None:
    """Was mit dem negativen Prompt des Stils geschieht — **nämlich nichts.**

    **Zwei Wirkungslosigkeiten übereinander, und beide sehen wie Sorgfalt aus.**

    1. **Er hat keinen Weg.** Alle sieben Stile führen einen sorgfältig geschriebenen
       negativen Prompt. Gesetzt wird er von :func:`aiimaging.prompts.komponiere` — und
       ``komponiere`` liegt **nicht** auf dem Weg, den ein Auftrag der Oberfläche nimmt.
       Der bringt seinen Prompt roh mit, und :class:`~aiimaging.render.RenderAuftrag`
       bekommt hier nie ein ``negativ_prompt``. Dieselbe Fehlerart wie beim
       Bauteilwächter, nur an einem anderen Feld.
    2. **Und er hätte auch mit Weg keine Wirkung.** Unser Vorgabe-Backbone
       ``z-image-turbo`` läuft mit ``fuehrung = 0.0``; unterhalb von
       :data:`aiimaging.render.FUEHRUNG_MINDESTENS` ist die klassifikatorfreie Führung
       abgeschaltet, und dann gibt es nichts, wovon sich ein negativer Prompt abziehen
       liesse.

    **Darum wird er hier gemeldet und nicht durchgereicht.** Ihn anzuschliessen ergäbe den
    schlechtesten Zustand von allen: Er stünde im Protokoll, sähe nach Wirkung aus und
    änderte kein Bildpunkt. Ob er auf einem Backbone mit Führung überhaupt etwas
    verbessert, ist **ungemessen** — und eine ungemessene Änderung am Bild ist kein
    Anschluss, sondern ein Eingriff.

    Returns:
        ``None``, wenn kein Stil gewählt ist oder der Stil keinen negativen Prompt führt —
        dann gibt es nichts zu melden. Sonst ``{stil, negativ, erreicht_render,
        waere_wirksam, grund}``.
    """
    if not stil:
        return None
    try:
        s = prompts.hole_stil(stil)
    except Exception:                       # noqa: BLE001 — unbekannter Stil ist anderswo ein Mangel
        return None
    if not getattr(s, "negativ", ""):
        return None
    wirkung = render.negativ_wirksam(backbone_name or render.VORGABE_BACKBONE)
    return {
        "stil": stil,
        "negativ": s.negativ,
        # Heute unveraenderlich False. Es steht trotzdem als Feld da und nicht als
        # Kommentar: Wer den Weg spaeter baut, soll hier eine Zeile aendern und nicht
        # einen Satz Prosa suchen muessen.
        "erreicht_render": False,
        "waere_wirksam": wirkung["wirksam"],
        "grund": wirkung["grund"],
    }


def _kompositionszeilen(kameras: list) -> list:
    """Kompositionsbefunde zusammenfassen — **was alle betrifft, steht einmal da.**

    **Der Anlass ist eine Messung am eigenen Ausgabetext.** Ohne Geländestand meldete die
    Kompositionsprüfung für *jede* Kamera des gerechneten Wegs zwei Warnungen: den
    unzuverlässigen Bezugspunkt und die Neigung. Bei zwölf Kameras sind das zwölf von
    zwölf, immer dieselben zwei. Eine Warnung, die bei jedem Lauf und für jede Kamera
    erscheint, ist kein Signal mehr — es ist dasselbe Versagen wie ein Wächter, der nie
    greift, nur von der anderen Seite.

    **Auf dem vorgegebenen Weg — so schickt die Oberfläche ihre Kameras — sind es seit dem
    22.09.2026 drei je Kamera:** ``Bezugspunkt``, ``Neigungsangabe`` und
    ``Shiftangabe``. Der Kamerablock dort trägt weder Neigung noch Shift, und beide
    werden seither als NICHT GEMESSEN gemeldet statt als gerechnete Null. Mit gesetztem
    Geländestand tritt ``Geländeangabe`` an die Stelle von ``Bezugspunkt``: Die Angabe
    ist ungeprüft, aber sie ist keine Hüllbox-Unterkante mehr — und der Rat unten
    (``--gelaende-z``) hängt nur an ``Bezugspunkt``, weil er nach dem Befolgen sonst
    stehen bliebe. Bis zum 22.09.2026 hat derselbe Rat die Prüfung ganz abgeschaltet:
    ``gesetzt`` war in :data:`aiimaging.komposition.BEZUGSPUNKTE` unbekannt, und die
    Zeile hiess danach «NICHT beurteilbar».

    **Eine fehlende Angabe und eine festgestellte Abweichung bleiben zwei Zeilen**
    (``Neigungsangabe`` gegen ``Neigung``), weil :func:`_warnungsart` nach dem ersten
    Wort gruppiert. Das gilt nur, solange die Warnungen in
    :func:`aiimaging.komposition.aufnahme` so beginnen; der Wächter dafür füttert diese
    Funktion mit einer ungemessenen und einer gekippten Kamera.

    Beide sind dabei **richtig**. Der Bezugspunkt ist aus einer glb gar nicht besser zu
    wissen (dort gibt es kein Gelände), und die Neigung bleibt, bis die Vorgabe auf
    `MODUS_SHIFT` wechselt. Sie sind also keine Befunde über *diesen* Auftrag, sondern
    Eigenschaften der Eingabe — und gehören einmal genannt, nicht dreimal.

    Was nur einen Teil der Kameras betrifft, bleibt einzeln aufgeführt: **das** ist die
    Zeile, die jemanden hinsehen lässt.
    """
    beurteilt = [k for k in kameras if (k.get("komposition") or {}).get("beurteilt")]
    zeilen: list = []

    # Eine Aufsicht ist nicht «nicht beurteilbar», sondern mit Absicht nicht nach diesen
    # Regeln beurteilt (Owner-Entscheid 67) — eigene Zeile, damit niemand einen Fehler sucht.
    aufsicht = [k.get("kamera") for k in kameras
                if (k.get("komposition") or {}).get("aufsicht")]
    if aufsicht:
        zeilen.append(f"Komposition nicht angewandt (Aufsicht ueber dem Dach, gerechnet): "
                      f"{', '.join(str(k) for k in aufsicht)}")
    unbeurteilt = [k.get("kamera") for k in kameras
                   if (k.get("komposition") or {}).get("beurteilt") is False
                   and not (k.get("komposition") or {}).get("aufsicht")]
    if unbeurteilt:
        zeilen.append(f"Komposition NICHT beurteilbar: "
                      f"{', '.join(str(k) for k in unbeurteilt)}")

    je_kamera = {str(k.get("kamera")): {_warnungsart(w) for w in
                                        (k.get("komposition") or {}).get("warnungen") or ()}
                 for k in beurteilt}
    alle_arten = set().union(*je_kamera.values()) if je_kamera else set()

    gemeinsam = sorted(a for a in alle_arten
                       if all(a in arten for arten in je_kamera.values()))
    if gemeinsam:
        zeile = (f"Komposition, alle {len(beurteilt)} Kameras: "
                 f"{', '.join(gemeinsam)}")
        # Was der Betreiber dagegen TUN kann, gehört in dieselbe Zeile.
        #
        # Der unbekannte Geländestand erscheint bei jedem Auftrag — er ist aus einer glb
        # nicht zu erfahren. Eine Dauerwarnung ohne Handgriff ist aber keine Warnung
        # mehr, sondern Möblierung: Sie steht da, man kann nichts tun, also liest man sie
        # nicht. Seit `verarbeiter(gelaende_z=…)` gibt es den Handgriff, und damit wird
        # aus der Klage ein Angebot.
        if "Bezugspunkt" in gemeinsam:
            zeile += "  (Geländestand mit --gelaende-z setzen, dann entfällt das)"
        zeilen.append(zeile)

    for kuerzel, arten in je_kamera.items():
        eigen = sorted(arten - set(gemeinsam))
        if eigen:
            zeilen.append(f"Komposition, nur {kuerzel}: {', '.join(eigen)}")
    return zeilen


#: Ab welchem **Vordergrundanteil der Szene** der Kurzbefund den Unterschied zwischen
#: rohem und normiertem ``geom_iou`` ueberhaupt erwaehnt.
#:
#: **Eine Setzung, keine Messung** — und sie ist bewusst nicht klein. Der geschenkte
#: Anteil ist der Vordergrundanteil der Szene; bei einem Bauwerk ohne Gelaende liegt er
#: bei 0.11. Eine Zeile darueber waere eine Dauerwarnung ueber eine Nachkommastelle und
#: wuerde die Plaetze fuellen, auf denen die echten Meldungen stehen.
#:
#: 0.25 trennt die beiden gemessenen Lagen: Quader 0.1104 und Hochbau 0.1729 schweigen,
#: die Gelaendeszene mit 0.5297 meldet sich (27.08.2026).
GESCHENKTER_ANTEIL_SCHWELLE = 0.25

#: Was ein **nicht gefahrener Maskenweg** bedeutet — der Satz, der in *beiden* Fällen
#: derselbe ist.
#:
#: Er steht genau einmal, weil zwei Fassungen desselben Satzes auseinanderlaufen, sobald
#: eine gepflegt wird. Genau das ist diesem Satz schon einmal passiert: Bis zum Abend des
#: 26.08.2026 nannte er als Folge, der Score falle auf ``abs(spearman)`` zurück — das
#: stimmte, bis :func:`qa_gegen_soll` die Polarität immer durchreichte. Die überholte
#: Fassung hätte den Leser an die falsche Stelle geschickt.
#:
#: Die **Gründe** unterscheiden sich und stehen darum je an ihrer Zeile; die **Folge**
#: ist dieselbe: ohne Maskenweg kein ``rho_maske``, keine Kante, kein Paarurteil.
MASKENWEG_FOLGE = (
    "damit bleiben rho_maske, Kante und Paarurteil ungemessen. Das sind die Masse, die "
    "die ABWESENHEIT eines Bauwerks fangen; der Score ueber das ganze Bild fangt sie "
    "nicht (ein leeres Grundstueck erreichte dort 0.9530 und bestand das Tor, "
    "auf-20260821-26).")


#: Ab wie wenig freiem Rest der Kurzbefund einen vollen Ladeweg als **knapp** meldet.
#:
#: **Eine Setzung, und sie steht hier, damit sie als Setzung erkennbar bleibt.** Gemessen
#: ist der Anlass, nicht die Grenze: Am 21.09.2026 (`auf-20260919-123`) wurde ein Lauf mit
#: 5 GiB Luft auf den Auslagerungsweg geschickt, weil die Bedarfsrechnung die
#: Aktivierungen zweimal zaehlte. Seit der Korrektur waehlt dieselbe Lage den vollen Weg —
#: und damit gibt es erstmals den umgekehrten Fehlerfall, dass der volle Weg zu knapp
#: gewaehlt wird.
#:
#: 2 GiB, weil die drei Messungen desselben Modells 22,89 … 25,1 GiB auseinanderliegen —
#: rund 2,2 GiB. Wer weniger Rest hat als die bekannte Schwankung desselben Modells, hat
#: keinen Puffer, sondern Glueck gehabt.
KNAPPER_SPIELRAUM_BYTE = 2 * 2**30


def _ist_knapp(bedarf: dict | None) -> bool:
    """War der volle Ladeweg knapp gewaehlt? ``None`` und Unbekanntes heissen **nein**.

    Nicht aus Bequemlichkeit: Eine Warnung aus einer Zahl, die es nicht gibt, ist ein
    Fehlalarm, und Fehlalarme sind das, woran ein Kurzbefund stirbt. Wo nichts gemessen
    ist, wird nichts behauptet — *die dritte Antwort, angewandt auf eine Warnung.*
    """
    if not isinstance(bedarf, dict):
        return False
    spielraum = bedarf.get("spielraum_byte")
    if not isinstance(spielraum, (int, float)):
        return False
    return 0 <= spielraum < KNAPPER_SPIELRAUM_BYTE


def _bedarfszusatz(kameras: list) -> str:
    """Die Zahlen, mit denen der Auslagerungsweg gewaehlt wurde — oder nichts.

    *Eine Entscheidung, deren Eingangszahlen nirgends stehen, ist von aussen nicht von
    einer Eigenschaft der Maschine zu unterscheiden.* Genau daran hat sich
    `auf-20260919-123` drei Wochen lang aufgehalten: Der Kurzbefund sagte, der freie
    Kartenspeicher habe entschieden — er sagte nicht, gegen welche Zahl.
    """
    for kamera in kameras:
        bedarf = (kamera.get("geraeteweg") or {}).get("bedarf")
        if isinstance(bedarf, dict) and bedarf.get("grund"):
            return f". {bedarf['grund']}"
    return ""


def _paarzeile(kamera: dict) -> str:
    """Ein gemessenes Paarurteil in einem Atemzug: ``s rho +0.7713/Anteil +0.2132``.

    Beide Beine stehen da und nicht nur das entscheidende. Wer nur den Traeger liest,
    haelt eine Kamera mit rho +0.98 und Anteil 0.06 fuer denselben Fall wie eine mit
    rho +0.72 und Anteil 0.008 — es sind aber zwei verschiedene Befunde.

    ``None`` bleibt ``None`` und wird nicht zu einer Null gerundet: Ein Bein, das nicht
    gemessen werden konnte, ist kein Bein mit dem Wert null.
    """
    paar = kamera.get("paarurteil") or {}

    def zahl(wert):
        return f"{wert:+.4f}" if isinstance(wert, (int, float)) \
            and not isinstance(wert, bool) else "UNGEMESSEN"

    return (f"{kamera.get('kamera')} rho {zahl(paar.get('rho'))}"
            f"/Anteil {zahl(paar.get('anteil'))}")


def befund_kurz(befund: dict | None) -> tuple[str, ...]:
    """Der Befund in wenigen Zeilen — für einen Menschen an einem Terminal.

    **Was hier NICHT hineingehört:** alles. Ein Werkzeug, das dreissig Zeilen je Auftrag
    ausgibt, wird überflogen, und dann übersieht man auch die eine Zeile, die zählt. Es
    steht darum nur da, was eine **Entscheidung** auslösen könnte:

    * dass der Prompt übersetzt wurde (der Betreiber hat etwas anderes geschrieben, als
      gerendert wurde),
    * die Spanne über die Kameras samt der Zahl, aus wie vielen das Urteil das
      schlechteste ist,
    * wie viele Kameras die Kompositionsprüfung beanstandet,
    * ob der Vorsprung des gewählten Startwerts belegt ist,
    * bei welchen Kameras das zweite Bein des Paartests **gar nichts messen kann**,
    * wo der **Score besteht und der Maskenweg widerspricht** — das Loch, das seit dem
      26.08.2026 offen bleibt und darum wenigstens sichtbar sein muss,
    * was der Betreiber bestellt hat und **nicht bekommt**,
    * dass der negative Prompt des Stils den Render nicht erreicht,
    * ob die Schwelle an **dieser** Maskenlage überhaupt noch etwas trennt,
    * ob der Lauf bei dieser **Rahmung** überhaupt bestehen konnte.

    Zeilen ohne Inhalt entfallen ganz. Eine Ausgabe, in der jede Zeile immer dasteht,
    liest sich nach dem dritten Mal wie eine leere.
    """
    if not isinstance(befund, dict):
        return ()

    zeilen: list[str] = []

    sprache = befund.get("prompt_sprache") or {}
    if sprache.get("noetig"):
        zeilen.append(f"Prompt uebersetzt ({sprache.get('verfahren')}): "
                      f"{sprache.get('original')!r} -> {befund.get('prompt')!r}")
        if not sprache.get("vollstaendig", True):
            zeilen.append(f"  NICHT vollstaendig uebersetzt: "
                          f"{', '.join(sprache.get('unbekannt') or ())}")

    # NUR wenn die Bestellung eine Hochachse nannte UND sie eine Drehung verlangt.
    # Ohne diese zweite Bedingung stuende die Zeile unter JEDEM Auftrag der Bruecke —
    # eine Dauerwarnung, und die verdeckt die echten. Sie ist damit selbstloeschend:
    # Sobald Y-up bestellt wird, schweigt sie wieder.
    # AUS DEM SPEICHER STATT GERECHNET. Die Zeile steht nur, wenn wirklich ein Treffer
    # dabei war — der Zwischenspeicher ist voreingestellt AUS, und ohne Treffer schweigt
    # sie. Sie ist trotzdem noetig: Ein Lauf aus dem Speicher ist schneller und sieht
    # sonst genauso aus wie ein gerechneter. Wer eine Messreihe fuehrt, muss wissen,
    # welche Bilder in DIESEM Lauf entstanden sind und welche aelter sind.
    speicher = [k for k in (befund.get("kameras") or ())
                if (k.get("zwischenspeicher") or {}).get("treffer")]
    if speicher:
        unter = sorted({str((k.get("zwischenspeicher") or {}).get("gerechnet_unter"))
                        for k in speicher})
        zeilen.append(
            f"AUS DEM ZWISCHENSPEICHER, nicht gerechnet: "
            f"{', '.join(str(k.get('kamera')) for k in speicher)} "
            f"({len(speicher)} von {len(befund.get('kameras') or ())} Kameras, "
            f"gerechnet unter Blender {', '.join(unter)}). Die Geometriestufen dieser "
            f"Kameras stammen aus einem frueheren Lauf mit denselben Einstellungen.")

    achse = befund.get("hochachse") or {}
    if achse.get("quelle") == "auftrag" and str(achse.get("wert", "")).upper().startswith("Z"):
        zeilen.append(f"Geometrie um Z-up->Y-up GEDREHT, weil der Auftrag "
                      f"up_axis={achse.get('wert')!r} nannte. Ohne diese Angabe waere "
                      f"unter Y-up gerechnet worden — Tiefenkarte, Kamera und "
                      f"Geometrie-QA gemeinsam verdreht und trotzdem plausibel.")

    bauteile = befund.get("prompt_bauteile") or ()
    if bauteile:
        zeilen.append(f"Prompt nennt Bauteile: {', '.join(str(b) for b in bauteile)} — "
                      f"hat die Geometrie sie? Wenn nicht, erfindet sie das Bildmodell.")

    kameras = befund.get("kameras") or []

    urteil = befund.get("geometrie_urteil") or {}
    spanne = urteil.get("kameraspanne") or {}
    if spanne.get("n_gemessen"):
        teil = (f"Geometrie: {spanne.get('schlechtester'):.4f} "
                f"(schlechteste von {spanne['n_gemessen']} Kameras")
        if spanne.get("bester") is not None and spanne["n_gemessen"] > 1:
            teil += f", beste {spanne['bester']:.4f}"
        zeilen.append(teil + ")")
    elif spanne:
        # «SCORE», nicht «Geometrie». Der alte Satz sprach ueber den ganzen Lauf und
        # meinte nur den Score ueber das ganze Bild — siehe die Zeile darunter.
        zeilen.append("Geometrie-SCORE: UNGEMESSEN, keine Kamera lieferte einen Wert "
                      "(ohne gemeinsame Silhouette gibt es keine Tiefenordnung zu "
                      "vergleichen).")

    # DER MASKENWEG SPRICHT AUCH DANN, WENN DER SCORE SCHWEIGT — Demolauf 14, 01.09.2026.
    #
    # Bis dahin las diese Funktion nur die Sprache des Scores. Faellt der aus, stand hier
    # genau eine Zeile: «Geometrie: UNGEMESSEN — keine Kamera lieferte einen Wert.» Die
    # beiden vorhandenen Maskenweg-Zeilen sind selbstloeschend und schweigen ausgerechnet
    # in diesem Fall: Die eine feuert nur bei `bestanden is True`, die andere nur bei
    # `zustaendig is False`.
    #
    # In Lauf 14 hiess das: Drei Kameras trugen ein GEMESSENES Paarurteil, alle drei
    # durchgefallen — und der Bericht nannte den Lauf ungemessen. Von zwei moeglichen
    # Fehlern ist das der weichere und darum der gefaehrlichere: Er laesst einen Lauf
    # harmlos aussehen, in dem ausgerechnet das Tor gesperrt hat, das die ABWESENHEIT
    # eines Bauwerks faengt (MASKENWEG_FOLGE).
    #
    # SELBSTLOESCHEND: nur wenn der Score fehlt UND der Maskenweg gemessen hat. Liegt ein
    # Score vor, traegt die Spannenzeile darueber das Urteil.
    if spanne and not spanne.get("n_gemessen"):
        gemessen = [k for k in kameras
                    if (k.get("paarurteil") or {}).get("gemessen") is True]
        urteilend = [k for k in gemessen
                     if (k.get("paarurteil") or {}).get("urteilt") is not False]
        if gemessen and not urteilend:
            # 30.09.2026: Das Paarurteil urteilt nicht mehr (auf-175) — gemessen ist ρ,
            # geprüft im Sinne eines Urteils ist nichts.
            zeilen.append(
                f"MASKENWEG GEMESSEN, URTEILT NICHT: {' · '.join(_paarzeile(k) for k in gemessen)}"
                f" — rho ist nur Auskunft, die Schwelle trennt an erzeugten Bildern nicht "
                f"(auf-20260929-175). Der Lauf ist UNGEPRUEFT, nicht durchgefallen.")
        elif gemessen:
            gefallen = [k for k in gemessen
                        if (k.get("paarurteil") or {}).get("bestanden") is False]
            schwellen = (gemessen[0].get("paarurteil") or {}).get("schwellen") or {}
            zeilen.append(
                f"MASKENWEG GEMESSEN, {len(gefallen)} von {len(gemessen)} Kameras "
                f"DURCHGEFALLEN: {' · '.join(_paarzeile(k) for k in gemessen)} "
                f"(Schwellen rho {schwellen.get('rho')}, Anteil "
                f"{schwellen.get('anteil')}). Der Lauf ist damit GEPRUEFT und "
                f"durchgefallen, NICHT ungeprueft — und zwar an dem Mass, das die "
                f"ABWESENHEIT eines Bauwerks faengt.")

    zeilen.extend(_kompositionszeilen(kameras))

    ungesichert = [k.get("kamera") for k in kameras
                   if ((k.get("seedauswahl") or {}).get("vorsprung") or {})
                   .get("belegt") is False]
    if ungesichert:
        zeilen.append(f"Seedvorsprung NICHT belegt (bestes Bild behalten, aber kein "
                      f"besserer Startwert): {', '.join(str(k) for k in ungesichert)}")

    # Ein „nicht zustaendig", das niemand sieht, ist ein bestandenes Tor mit Extraschritt.
    # Die Zeile nennt darum die Kameras UND den Handgriff: In einer Szene, in der ein
    # Nachbargebaeude hinter dem Umriss steht, ist die Existenzfrage mit diesem Schaetzer
    # nicht zu beantworten — eine andere Kamera kann sie beantwortbar machen.
    unzustaendig = [k.get("kamera") for k in kameras
                    if (k.get("paarurteil") or {}).get("zustaendig") is False]
    if unzustaendig:
        zeilen.append(f"Umrisstreue NICHT messbar (kein Himmel hinter dem Umriss, "
                      f"auf-vis-20260823-07): {', '.join(str(k) for k in unzustaendig)}"
                      f"  — nicht messbar heisst weder bestanden noch durchgefallen; "
                      f"eine Kamera mit freierem Hintergrund misst wieder")

    # DER SCORE BESTEHT, DER MASKENWEG SAGT NEIN — und das Tor liest nur den Score.
    #
    # Owner-Entscheid 26.08.2026: Das Loch bleibt vorerst offen, weil ein zweites Tor auf
    # einer PROVISORISCHEN Schwelle gute Bilder sperren wuerde und niemand weiss, wie
    # viele (PAAR_KANTENANTEIL_SCHWELLE traegt selbst den Satz, sie liege "sehr viel
    # naeher am Zufall als am Richtigen"). Aber es wird SICHTBAR — genau darum steht
    # diese Zeile hier.
    #
    # Der Anlass ist gemessen und durch die Kette bestaetigt: Ein VOLLSTAENDIG
    # verschwundenes Bauwerk gab `bestanden=True` bei Score 0.951 und geom_iou 1.000,
    # waehrend `paarurteil` durchgefallen meldete (rho_maske -0.018). geom_iou steigt
    # dort WEGEN der Abwesenheit — der Boden bleibt liegen, und das Bauwerk war die
    # einzige Stelle, an der sich Soll und Ist unterscheiden konnten
    # (docs/BRAUCHT_ES_GEOM_IOU_2026-08-26.md).
    #
    # SELBSTLOESCHEND: Sie steht nur, wenn beide Bedingungen zugleich zutreffen. Ein
    # durchgefallener Score braucht sie nicht — dort sperrt das Tor ohnehin.
    widerspruch = [k.get("kamera") for k in kameras
                   if k.get("bestanden") is True
                   and (k.get("paarurteil") or {}).get("bestanden") is False]
    if widerspruch:
        zeilen.append(
            f"SCORE BESTEHT, MASKENWEG SAGT NEIN: {', '.join(str(k) for k in widerspruch)}"
            f"  — das Tor liest nur den Score, und der kann bei viel Boden hoch bleiben, "
            f"obwohl das Bauwerk fehlt (gemessen: verschwundenes Bauwerk, Score 0.951, "
            f"geom_iou 1.000, rho_maske -0.018). Das Paarurteil sperrt hier NICHT — es "
            f"steht nur da. Wer diesem Lauf traut, traut dem Score allein")

    # WIE VIEL VON DEM geom_iou GEHOERT DEM BILD UND WIE VIEL DER SZENE?
    #
    # Owner-Entscheid 28.08.2026: Der Score bleibt unangetastet — 0.65 behaelt seine
    # Bedeutung —, aber der normierte Wert wird ausgewiesen. Grund ist eine
    # Rechenidentitaet vom Vortag: Ein KONSTANTES Bild bekommt bei `geom_iou` exakt den
    # Vordergrundanteil der Szene (auf drei Szenen auf volle Gleitkommagenauigkeit
    # belegt: 0.1104, 0.1729, 0.5297). Eine Szene, deren Geometrie die halbe Bildflaeche
    # fuellt, gibt jedem wertlosen Bild 0.53 — und 0.53 liest sich wie "zur Haelfte
    # richtig" (docs/GEOM_IOU_BODEN_UND_DECKE_2026-08-27.md).
    #
    # SELBSTLOESCHEND, und die Bedingung ist bewusst eng: Sie steht nur, wenn der Boden
    # WIRKLICH gross ist. Bei einem Bauwerk ohne Gelaende liegt er bei 0.11, und dort
    # waere die Zeile eine Dauerwarnung ueber eine Nachkommastelle.
    # DIE RICHTIGE ZAHL IST DER ANTEIL DER SZENE, NICHT DIE DIFFERENZ. Beim ersten
    # Versuch stand hier `roh - norm`, und das ist falsch: Bei einem PERFEKTEN Bild wird
    # die Differenz null (roh = norm = 1), waehrend der Boden der Szene unveraendert 0.53
    # betraegt. Ein Kriterium, das genau beim besten Bild schweigt, meldet die Sache nicht,
    # sondern ihr Gegenteil.
    schenkung = []
    for k in kameras:
        roh, norm = k.get("geom_iou"), k.get("geom_iou_norm")
        anteil = k.get("geom_iou_obergrenze")
        if roh is None or norm is None or anteil is None:
            continue
        if anteil < GESCHENKTER_ANTEIL_SCHWELLE:
            continue
        # IN WORTEN, DIE MAN OHNE DIE HERLEITUNG VERSTEHT (auf-20261021-318 B4): Bis dahin
        # «0.971 roh, 0.961 ohne den Boden (die Szene schenkt 0.253)» — «Boden» hiess hier
        # Untergrenze, wurde aber als Gelaende gelesen, und «schenkt» erklaerte nichts. Die
        # Zahl ist der Anteil des Bildes, den die GANZE Geometrie fuellt (samt Gelaende und
        # Platte, nicht die Bauwerksmaske): so viel Umriss-Treue bekaeme jedes leere Bild.
        schenkung.append(
            f"{k.get('kamera')} {roh:.3f}, davon {anteil:.3f} geschenkt — so viel bekaeme "
            f"auch ein leeres, einfarbiges Bild, weil die Geometrie samt Gelaende "
            f"{anteil * 100:.0f} % des Bildes fuellt; selbst verdient {norm:.3f}")
    if schenkung:
        zeilen.append(
            "UMRISS-TREUE (geom_iou) ZUM TEIL GESCHENKT: " + " · ".join(schenkung)
            + "  (selbst verdient: 0 = nicht besser als ein leeres Bild, 1 = deckungsgleich). "
              "Der Score rechnet weiter mit dem rohen Wert")

    # Zuletzt und ganz oben im Rang, wenn es denn vorkommt: eine Bestellung, die nicht
    # ausgefuehrt wurde. Alles Uebrige auf dieser Liste sind Befunde ueber das ERGEBNIS —
    # dies ist einer ueber die EINGABE, und der Betreiber sieht ihn sonst nirgends.
    # Die Rahmung. Diese Zeile steht bewusst weit oben: Sie sagt, ob der Lauf ueberhaupt
    # bestehen KONNTE — und wenn nicht, sind alle folgenden Zahlen Auskunft ueber die
    # Rahmung und nicht ueber das Bild.
    # Ganz oben, weil es die einzige Zeile ist, die von einem NICHT gelaufenen Render
    # berichtet. Wer sie uebersieht, sucht in den Zahlen darunter nach einem Bild, das es
    # gar nicht gibt.
    # Was die Kamerawahl von der Dokumentationsnorm abdeckt. Eine Zeile, die nur dann
    # erscheint, wenn wirklich etwas fehlt oder offen ist — bei vollstaendiger Abdeckung
    # waere sie die naechste Dauerwarnung.
    habs = befund.get("habs_ansichten") or {}
    if habs.get("fehlend") or habs.get("nicht_feststellbar"):
        zeilen.append(f"HABS-Ansichten: {habs.get('grund')}")

    nicht_gerendert = [k.get("kamera") for k in kameras
                       if (k.get("rahmung") or {}).get("abbruch") is True]
    if nicht_gerendert:
        zeilen.append(
            f"NICHT GERENDERT (Rahmung): {', '.join(str(k) for k in nicht_gerendert)} — "
            f"das Bauwerk fuellt zu wenig Bildbreite, als dass ein Urteil moeglich waere "
            f"(gemessen noetig 65 %, auf-vis-20260825-15 Posten 1). Es wurde ABSICHTLICH "
            f"kein Bild erzeugt: Bei 30 % Bildbreite ist das Ergebnis gemessen "
            f"schlechter als bei 17,5 %. Abhilfe ist eine naehere Kamera")

    # DER MASKENWEG — die Zeile, die seit dem 26.08.2026 hier fehlte.
    #
    # Gemeldet von der HomeStation: In allen vier Laeufen jenes Tages standen `rho_maske`,
    # `kante` und `paarurteil` auf None, und niemandem fiel es auf. Der Grund stand im
    # Maskenbefund je Kamera — also in einer Datei, die man aufschlagen muss, waehrend
    # oben auf dem Schirm ein Score stand.
    #
    # **Die Folge ist keine Kleinigkeit** — sie ist seit dem Abend des 26.08.2026 eine
    # ANDERE als hier zuerst stand, und die neue wiegt schwerer.
    #
    # ZUERST STAND HIER: "Ohne Maskenweg wird die gemessene Polaritaet nie angewandt, und
    # der Score faellt auf abs(spearman) zurueck." Das stimmte, als es geschrieben wurde,
    # und stimmt seit demselben Abend nicht mehr: `qa_gegen_soll` reicht die gemessene
    # Polaritaet jetzt IMMER durch, ob eine Maske da ist oder nicht.
    #
    # WAS BLEIBT, IST DER GROESSERE TEIL: Ohne Maskenweg gibt es kein `rho_maske`, keine
    # Kante und kein Paarurteil — also genau die Masse, die die ABWESENHEIT eines
    # Bauwerks fangen. Der Score ueber das ganze Bild fangt sie nicht: Ein leeres
    # Grundstueck erreichte dort 0.9530 und bestand das Tor (auf-20260821-26,
    # docs/GEOM_IOU_HALLUZINATION_2026-08-21.md). Das ist der Grund fuer diese Zeile.
    ohne_maske = [k.get("kamera") for k in kameras
                  if (k.get("maskenbefund") or {}).get("maske") is None
                  and k.get("bild_png")]
    if ohne_maske:
        erster = next((k.get("maskenbefund") or {} for k in kameras
                       if (k.get("maskenbefund") or {}).get("maske") is None), {})
        zeilen.append(
            f"MASKENWEG NICHT GEFAHREN: {', '.join(str(k) for k in ohne_maske)} — "
            f"{MASKENWEG_FOLGE} Ein bestandenes Urteil ohne Maskenweg sagt darum "
            f"nichts darueber, ob ueberhaupt gebaut wurde. "
            f"Grund: {str(erster.get('grund') or 'ohne Angabe')[:200]}")

        # WELCHE BAUSTOFFE DIE REGEL GEPRUEFT HAT — auf Rueckfrage der HomeStation
        # (auf-47, 26.08.2026): «Findet sie 11 Baustoffe und keiner heisst nach Gelaende,
        # ist das ein anderer Befund als 'keine Baustofftabelle gefunden'.»
        #
        # Die Zeile steht NUR im ersten der beiden Faelle. Sie ist damit selbstloeschend:
        # Sobald die Regel trifft oder gar nichts zu lesen war, schweigt sie wieder — und
        # eine Zeile, die immer dasteht, verdeckt die echten.
        #
        # Sie sagt dem Betreiber die ANTWORT und nicht die Frage: Wer diese Namen liest
        # und keinen Boden darunter findet, weiss, dass `--kein-gelaende` richtig ist.
        if erster.get("gelaende_befund") == maske_modul.BEFUND_KEIN_GELAENDE_BELEGT:
            geprueft = erster.get("gelaende_geprueft") or ()
            zeilen.append(
                f"  Geprueft wurden {len(geprueft)} benannte Baustoffe, keiner nach "
                f"Gelaende: {', '.join(str(n) for n in geprueft)}. Das ist ein "
                f"NULLBEFUND und keine Ratlosigkeit — er belegt aber nur, dass die REGEL "
                f"nicht anschlug. Steht kein Boden in der Liste, ist --kein-gelaende die "
                f"richtige Angabe.")

    # DERSELBE AUSFALL, DER ANDERE GRUND — UND ER WAR STUMM (nachgetragen 01.09.2026).
    #
    # Gemessen an zwei Laeufen derselben Kette:
    #
    # * Lauf 10 (28.08.): drei Diffusionsbilder, die Maske fiel am fehlenden
    #   Gelaendebeleg aus — und die Zeile darueber sagte es laut.
    # * Lauf 11 (01.09.): KEIN Bild, der Maskenweg fiel ebenfalls aus — und kein Satz
    #   sagte es. Der Kurzbefund druckte «Geometrie: 0.9000» und sonst nichts.
    #
    # **Ein stiller Uebersprung ist schlimmer als ein lauter Ausfall.** Beim lauten
    # weiss der Leser, was ihm fehlt; beim stillen liest er ein Ergebnis ohne Urteil und
    # haelt es fuer eines mit Urteil. In Lauf 11 wog das besonders: Das gerettete
    # Cycles-Bild zeigte waagrechte Platten und leeres Grau — kein Bauwerk. Die Maske ist
    # genau das Mass, das so etwas faengt.
    #
    # WARUM DIE ZEILE DARUEBER EIN BILD VERLANGT, UND DAS RICHTIG BLEIBT. Wo bereits
    # eine Zeile sagt, warum kein Bild entstand — Rahmung, Kamerahoehe, uebernommene
    # Ansicht —, waere eine zweite ueber einen Weg, den niemand fahren wollte, eine
    # Dauerwarnung. Und eine Zeile, die immer dasteht, verdeckt die echten.
    #
    # DIE LUECKE IST DIE KAMERA OHNE BILD **UND OHNE GENANNTEN GRUND**: Fuer sie
    # schweigen beide Wege — `ohne_maske` verlangt ein Bild, `_kompositionszeilen`
    # verlangt einen Abbruchgrund. Genau diese Form entsteht, wenn ein Lauf zwischen
    # Rahmungspruefung und Diffusion abbricht.
    #
    # Damit ist die Zeile selbstloeschend: Sobald irgendetwas den fehlenden Bildlauf
    # erklaert, schweigt sie wieder.
    # `"bild_png" in k` UND NICHT BLOSS `not k.get("bild_png")` — der Unterschied ist
    # gemessen und hat beim ersten Entwurf neun Tests umgeworfen. Ein Eintrag OHNE das
    # Feld sagt nicht, dass kein Bild entstand; er sagt, dass er die Frage nicht
    # beantwortet. Das Feld gibt es erst seit dem 26.08.2026 (siehe `bild_png` am
    # Kameraurteil), und aeltere Befunde tragen es nicht. Eine Zeile «es gibt kein Bild»
    # ueber einem Befund, der darueber schweigt, waere eine Behauptung ohne Messung —
    # und genau davon handelt dieser ganze Abschnitt.
    stumm = [k for k in kameras
             if isinstance(k, dict)
             and "bild_png" in k and k["bild_png"] is None
             and (k.get("maskenbefund") or {}).get("maske") is None
             and not k.get("doppelt_von")
             and not (k.get("rahmung") or {}).get("abbruch")
             and not (k.get("komposition") or {}).get("abbruch")
             # Ein nicht rechenbares Bildmodell erklaert den fehlenden Lauf schon selbst.
             and _art_ohne_bild(k) != "umgebung"]
    if stumm:
        # OB `bestanden` HIER RICHTIG STEHT — gemessen und nicht behauptet.
        #
        # Owner-Entscheid vom 26.08.2026 (`tiefenschaetzer`): Wo nicht gemessen werden
        # konnte, steht `None` und nicht `False`. `_uebersprungenes_urteil` haelt sich
        # daran. Steht dort trotzdem ein Wert, ist das ein Urteil ueber einen Lauf, der
        # nichts geprueft hat — und dann darf diese Zeile nicht das Gegenteil behaupten.
        geurteilt = [k for k in stumm if k.get("bestanden") is not None]
        if geurteilt:
            lage = ("ACHTUNG: im Befund steht trotzdem "
                    + ", ".join(f"bestanden={k.get('bestanden')!r} bei {k.get('kamera')}"
                                for k in geurteilt)
                    + " — ein Urteil ueber einen Lauf, der nichts gemessen hat.")
        else:
            lage = ("NICHT GEMESSEN heisst hier weder bestanden noch durchgefallen; "
                    "im Befund steht bestanden=None, und das ist richtig so.")
        zeilen.append(
            f"MASKENWEG NICHT GEFAHREN, WEIL ES KEIN BILD GIBT: "
            f"{', '.join(str(k.get('kamera')) for k in stumm)} — {MASKENWEG_FOLGE} "
            f"Der Unterschied zum Fall darueber: Dort lag ein Bild vor und die Maske "
            f"liess sich nicht bauen; hier fehlt das Bild selbst — und der Befund sagt "
            f"auch nicht, warum: weder Rahmung noch Kamerahoehe noch eine uebernommene "
            f"Ansicht. {lage}")

    # DIE STARTWERT-VORGABE, DIE STILL AUF EINEN ZURUECKFAELLT.
    #
    # Gemessen am 26.08.2026: Ohne Bauwerksmaske gibt es kein Mass, nach dem sich unter
    # mehreren Startwerten auswaehlen liesse — `_bester_seed` rendert dann **einen**
    # statt der drei, die der Owner am 21.08. festgelegt hat. Das ist richtig so (drei
    # ungemessene Bilder kosten dreimal GPU und sagen nichts), aber es stand nur im
    # Kameraurteil.
    #
    # **Die Folge fuer den Betreiber:** Das behaltene Bild ist der ERSTE Wurf, nicht der
    # beste. Wer die Vorgabe fuer wirksam haelt, haelt ein ungemessenes Bild fuer ein
    # ausgewaehltes.
    ohne_auswahl = [k.get("kamera") for k in kameras
                    if (k.get("seedauswahl") or {}).get("ausgewaehlt") is False
                    and k.get("bild_png")]
    if ohne_auswahl:
        erster = next(((k.get("seedauswahl") or {}) for k in kameras
                       if (k.get("seedauswahl") or {}).get("ausgewaehlt") is False), {})
        zeilen.append(
            f"KEINE STARTWERT-AUSWAHL: {', '.join(str(k) for k in ohne_auswahl)} — das "
            f"behaltene Bild ist der ERSTE Wurf und nicht der beste. "
            f"{str(erster.get('grund') or 'ohne Angabe')[:180]}")

    # WAS ALS GELAENDE EINGESTUFT WURDE — und damit aus der Bauwerksmaske fiel.
    #
    # Seit dem 26.08.2026 traegt der Knotenname den IFC-Namen mit, und die Wortregel
    # greift damit auf viel mehr als vorher. Das ist der Zweck — aber es hat eine
    # Kehrseite, und die ist gemessen: `IfcWall_Site-A` gilt als Gelaende, weil `site`
    # eines der Woerter ist. Eine so benannte Wand faellt aus der Maske.
    #
    # Die sichere Richtung ist trotzdem die neue: Gelaende IN der Maske ist der
    # schlimmere Fehler (auf einer Bodenszene erreichte weisses Rauschen 0.72). Aber wer
    # nicht sieht, WAS ausgeschlossen wurde, kann einen Fehlausschluss nicht bemerken.
    eingestuft = []
    for eintrag in kameras:
        for name in (eintrag.get("maskenbefund") or {}).get("gelaende_namen") or ():
            if name not in eingestuft:
                eingestuft.append(name)
    if eingestuft:
        zeilen.append(
            f"Als Gelaende eingestuft und aus der Maske genommen: "
            f"{', '.join(str(n) for n in eingestuft[:6])}"
            + (f" (und {len(eingestuft) - 6} weitere)" if len(eingestuft) > 6 else "")
            + " — steht hier, damit ein Fehlausschluss auffaellt")

    doppelt = [(k.get("kamera"), k.get("doppelt_von")) for k in kameras
               if k.get("doppelt_von")]
    if doppelt:
        zeilen.append(
            "Nicht neu gerendert (identische Soll-Karte): "
            + ", ".join(f"{a} ist mit {b} identisch" for a, b in doppelt)
            + " — zweizaehlige Drehsymmetrie laesst die beiden Ueber-Eck-Ansichten "
              "zusammenfallen. Das Bild wurde uebernommen, und die Ansicht zaehlt in "
              "der Kameraspanne NICHT als zweite Ziehung")

    # Der Massstab. Die Zeile steht neben der Rahmung, weil beide dasselbe sagen: Das
    # Urteil darunter handelt von der SZENE und nicht vom Bild. Abgebrochen wird hier
    # NICHTS — warum, steht in `_massstab_gemeldet`.
    beanstandet = [(k.get("kamera"), k.get("massstab") or {}) for k in kameras
                   if (k.get("massstab") or {}).get("beanstandet")]
    for kamera, lage in beanstandet:
        faktor = lage.get("verdacht_faktor")
        zeile = (f"MASSSTAB UNPLAUSIBEL bei {kamera}: groesste Kante "
                 f"{lage.get('groesste_kante_m'):.4g} m, gemessen an "
                 f"{lage.get('quelle')}. Gerendert wurde TROTZDEM")
        if faktor is not None:
            zeile += (f" — es liesse sich ein Einheitenfehler um Faktor {faktor:g} "
                      f"hineinlesen, aber derselbe Verdacht trifft jeden Bauteil-Render "
                      f"unter 1 m und jedes verirrte Mesh in 4 km Entfernung. Ob "
                      f"umgerechnet gehoert, entscheidet die QUELLE, nicht diese Kette")
        else:
            zeile += (" — ein Kontextmodell ist kein Einheitenfehler (gemessen an 40 "
                      "echten Dateien: 1002 m und 1127 m, Einheit in Ordnung)")
        if lage.get("note"):
            zeile += f". Zur Huellbox: {lage['note'][:120]}"
        zeilen.append(zeile)

    # Und derselbe Fall aus dem Regelwerk: eine Aufnahme, die gar nicht beurteilbar ist.
    # Bis zum 26.08.2026 stand dieser Riegel HINTER der Diffusion und kommentierte eine
    # fertige Bilddatei, statt sie zu verhindern (auf-vis-20260826-16).
    unbeurteilbar = [(k.get("kamera"), (k.get("komposition") or {}).get("grund"))
                     for k in kameras if (k.get("komposition") or {}).get("abbruch")]
    if unbeurteilbar:
        zeilen.append(
            "NICHT GERENDERT (Aufnahme nicht beurteilbar): "
            + "; ".join(f"{k}: {g}" for k, g in unbeurteilbar)
            + " — diese Pruefung braucht kein Bild und laeuft VOR der Diffusion")

    zu_klein = [k.get("kamera") for k in kameras
                if (k.get("torchance") or {}).get("lage") == "zu_klein"]
    if zu_klein:
        zeilen.append(f"RAHMUNG ZU WEIT: bei {', '.join(str(k) for k in zu_klein)} fuellt "
                      f"das Bauwerk so wenig Bild, dass das Geometrie-Tor GEMESSEN nicht "
                      f"bestehen kann. Das ist kein Urteil ueber das Bild. Abhilfe ist "
                      f"eine naehere Kamera, keine gesenkte Schwelle (auf-13: bei 70 % "
                      f"Bildbreite entstand Score 0.9599)")

    # Die Zahl, die sagt, ob ein Score ueberhaupt etwas ueber das Bild aussagt.
    unerreichbar = [(k.get("kamera"), (k.get("erreichbarkeit") or {}))
                    for k in kameras
                    if (k.get("erreichbarkeit") or {}).get("erreichbar") is False]
    if unerreichbar:
        zeilen.append(
            "SCHWELLE FUER DIESE AUFNAHME UNERREICHBAR: "
            + "; ".join(f"{k}: hoechstens {e.get('hoechster_score'):.4f}"
                        for k, e in unerreichbar)
            + " — auch ein perfektes Bild kaeme nicht durch. Das Urteil misst dann die "
              "SZENE und nicht das Bild (auf-vis-20260826-16)")

    bs = urteil.get("bodenspanne") or {}
    if bs.get("einig") is False:
        zeilen.append(f"KAMERAWAHL UNEINIG: roh ist {bs.get('schlechteste_roh')!r} die "
                      f"schwaechste, nach gemessenem Rauschboden "
                      f"{bs.get('schlechteste_nach_boden')!r}. Gemeldet wird die rohe "
                      f"(Owner-Entscheid 22.08.) — welche tragen soll, ist NICHT "
                      f"entschieden (auf-vis-20260824-10)")

    # Der gemessene Rauschboden dieser Maskenlage. Zwei verschiedene Zeilen, weil es zwei
    # verschiedene Befunde sind: eine Schwelle, die hier nichts mehr trennt, ist etwas
    # anderes als ein knapper Abstand.
    untragbar = [k.get("kamera") for k in kameras
                 if (k.get("bodenabstand") or {}).get("schwelle_traegt") is False]
    if untragbar:
        zeilen.append(f"SCHWELLE TRAEGT HIER NICHT: bei {', '.join(str(k) for k in untragbar)} "
                      f"liegt der gemessene Rauschboden ueber der Schwelle — das Tor liesse "
                      f"Rauschen durch. Andere Kameralage, nicht andere Schwelle "
                      f"(auf-vis-20260824-10)")

    ohne_boden = [k.get("kamera") for k in kameras
                  if (k.get("bodenabstand") or {}).get("boden") is None
                  and k.get("bodenabstand") is not None]
    if ohne_boden:
        zeilen.append(f"Kein gemessener Rauschboden fuer die Maskenlage von "
                      f"{', '.join(str(k) for k in ohne_boden)} — rho steht dort gegen "
                      f"nichts. Die Konstante gilt fuer eine ANDERE Lage")

    # Der Geraeteweg steht NUR da, wenn er nicht der schnelle war. Eine Zeile, die bei
    # jedem gesunden Lauf erscheint, wird nach dem dritten Mal nicht mehr gelesen — und
    # gerade diese zaehlt, wenn ein Lauf zwanzigmal so lange braucht wie der vorige.
    langsam = sorted({(k.get("geraeteweg") or {}).get("geraet")
                      for k in kameras
                      if (k.get("geraeteweg") or {}).get("gemeldet")
                      and (k.get("geraeteweg") or {}).get("geraet") != "cuda"})
    if langsam:
        zeilen.append(f"Bildmodell lief auf {', '.join(str(g) for g in langsam)} — nicht "
                      f"ganz auf der Karte. Das erklaert Laufzeit, nicht Qualitaet; "
                      f"entschieden hat der FREIE Kartenspeicher, nicht der Code "
                      f"(auf-vis-20260825-15, Posten 4)"
                      + _bedarfszusatz(kameras))

    # Und die Gegenrichtung, die bis zum 21.09.2026 GAR NICHT gemeldet wurde: Der volle
    # Weg kann knapp gewaehlt worden sein. Ein Lauf, der mit 200 MiB Luft auf die Karte
    # kam, ist nicht gesund — er hatte Glueck, und beim naechsten Bild in groesserer
    # Aufloesung hat er es nicht mehr. *Kein Abzeichen sieht aus wie kein Problem.*
    knapp = sorted({k.get("kamera") for k in kameras
                    if (k.get("geraeteweg") or {}).get("geraet") == "cuda"
                    and _ist_knapp((k.get("geraeteweg") or {}).get("bedarf"))})
    if knapp:
        zeilen.append(f"Voll auf der Karte, aber KNAPP bei "
                      f"{', '.join(str(k) for k in knapp)} — unter "
                      f"{KNAPPER_SPIELRAUM_BYTE // 2**30} GiB Luft. Die gemessene Spitze "
                      f"stammt von 512 x 512; ein groesseres Bild braucht mehr, und um "
                      f"wie viel mehr, ist NICHT gemessen (auf-20260919-123)")

    # Und wenn die Entflechtung nicht durchgriff, steht es hier — VOR dem Lauf, der
    # daran stirbt. Bis zum 26.08.2026 hiess dieser Fall «Expected all tensors to be on
    # the same device» und kostete drei Stunden Ursachensuche.
    verflochten = [k.get("kamera") for k in kameras
                   if ((k.get("geraeteweg") or {}).get("entflechtung") or {})
                   .get("nachher") != 0
                   and ((k.get("geraeteweg") or {}).get("entflechtung") or {})
                   .get("noetig")]
    if verflochten:
        zeilen.append(f"ControlNet-Entflechtung NICHT durchgegriffen bei "
                      f"{', '.join(str(k) for k in verflochten)} — das Auslagern teilt "
                      f"Parameter zwischen ControlNet und Transformer, und der Lauf "
                      f"stirbt dann am Geraetekonflikt (auf-vis-20260825-14)")

    neg = befund.get("negativ_lage")
    if neg and not neg.get("erreicht_render"):
        # Drei Zustaende, nicht zwei. `None` heisst UNBEKANNT (die Fuehrung ist nicht
        # bestimmt, es greift die Vorgabe von diffusers) — als "wirkungslos" zu melden
        # waere genau die Ueberbehauptung, gegen die dieses Modul steht.
        wirksam = neg.get("waere_wirksam")
        if wirksam is False:
            zusatz = "  — und auf diesem Backbone waere er ohnehin wirkungslos"
        elif wirksam is None:
            zusatz = "  (ob er auf diesem Backbone wirken wuerde, ist UNBEKANNT)"
        else:
            zusatz = "  — auf diesem Backbone wuerde er wirken, wenn er ankaeme"
        zeilen.append(f"Negativ-Prompt des Stils {neg.get('stil')!r} erreicht den Render "
                      f"NICHT{zusatz}")

    stehen = befund.get("stehengeblieben") or ()
    for eintrag in stehen:
        zeilen.append(f"BESTELLT UND NICHT AUSGEFUEHRT: {eintrag.get('feld')} "
                      f"= {eintrag.get('wert')!r} — {eintrag.get('grund')}")

    return tuple(zeilen)


def _beobachter_bauen(auftrag: dict, wache_bauen, takt_s, antwort: dict):
    """Die Wache des Aufrufers bauen lassen — und einen Fehlschlag dabei nicht verschlucken.

    Eine Wache, die beim Bauen stolpert, darf den Lauf **nicht** verhindern: Der Auftrag
    ist freigegeben, die Karte ist frei, und die Beobachtung ist die Zugabe und nicht der
    Zweck. Sie darf aber auch nicht spurlos verschwinden, sonst sieht ein unbeobachteter
    Lauf hinterher aus wie ein beobachteter ohne Befund.
    """
    if wache_bauen is None:
        return None
    if not callable(wache_bauen):
        raise AbholerError(
            f"wache_bauen muss aufrufbar sein oder None, war {type(wache_bauen).__name__}."
        )
    try:
        wache = wache_bauen(auftrag)
    except Exception as fehler:            # noqa: BLE001 — siehe Docstring
        antwort["wache"] = {"gemessen": False, "gestanden": False,
                            "schwere": fortschritt.SCHWERE_WARN,
                            "laengster_stillstand_s": None, "blicke": 0, "meldungen": 0,
                            "quellenfehler": 0, "rueckruffehler": [],
                            "detail": (f"Die Wache liess sich nicht bauen "
                                       f"({type(fehler).__name__}: {fehler}). Der Lauf "
                                       f"läuft trotzdem — aber unbeobachtet.")}
        return None
    if wache is None:
        return None
    try:
        return fortschritt.Beobachter(wache, takt_s=takt_s)
    except fortschritt.FortschrittsError as fehler:
        antwort["wache"] = {"gemessen": False, "gestanden": False,
                            "schwere": fortschritt.SCHWERE_WARN,
                            "laengster_stillstand_s": None, "blicke": 0, "meldungen": 0,
                            "quellenfehler": 0, "rueckruffehler": [],
                            "detail": f"Die Wache taugt nicht zum Beobachten: {fehler}"}
        return None


def _zeiten_mit_stillstand(zeiten, bericht: dict | None) -> dict | None:
    """Den längsten Stillstand in die ``timings`` des fremden Vertrags legen.

    Warum dorthin und nicht in unsere ``hinweise``: ``timings`` ist ein **Vertragsfeld**
    und übersteht ``kosmo_szene.nur_vertragsfelder``. Die Hinweise überstehen es nicht.
    Wer in der fremden Oberfläche wissen will, warum ein Auftrag eine halbe Stunde
    brauchte, findet die Antwort damit dort, wo er ohnehin nachsieht.

    Eingetragen wird nur, was **gemessen** ist. Ein unbeobachteter Lauf bekommt keine
    Null — eine Null hiesse „stand nie", und das wäre eine Behauptung ohne Beleg.
    """
    if not bericht or not bericht.get("gemessen"):
        return zeiten
    ergaenzt = dict(zeiten or {})
    ergaenzt["stillstand_s"] = bericht.get("laengster_stillstand_s")
    return ergaenzt


def _karte_freigeben(karte_freigeben) -> dict | None:
    """Die Freigabe der Grafikkarte vor dem Auftrag (Entscheid 127) — **wirft nie**.

    ``None`` ohne Auskunft. Scheitert die Auskunft selbst, steht das als Befund da
    (``ollama: fehler``); der Auftrag läuft weiter — die Prüfungen danach sehen die Karte
    so, wie sie ist.
    """
    if karte_freigeben is None:
        return None
    try:
        befund = karte_freigeben()
    except Exception as fehler:            # noqa: BLE001 — Auskunft, kein Riegel
        return {"ollama": "fehler", "freigegeben": [], "nicht_freigegeben": [],
                "danach_leer": None, "noch_geladen": [], "dauer_s": None,
                "satz": (f"Grafikkarte nicht freigegeben ({type(fehler).__name__}) — der "
                         f"Auftrag rechnet trotzdem.")}
    return befund if isinstance(befund, dict) else None


def karte_oder_eigenes_entladen(darf_rechnen, entlade_versuch, *, versuche: int = 5,
                                _warte=None):
    """``darf_rechnen`` mit einem zweiten Anlauf: Ist die Karte belegt, erst das eigene
    Sprachmodell der Visbox entladen lassen — dann noch einmal fragen.

    **Owner-Auflage der HomeStation (20.10.2026, zu Entscheid 106d):** Hält NUR das Modell
    des Visbox-Assistenten die Karte, und läuft keine Anfrage, darf der Abholer es entladen,
    statt zu warten. Ob das so ist, entscheidet ``entlade_versuch()``
    (:func:`aiimaging.assistent.entlade_wenn_nur_eigenes`) — hier wird nur gefragt und nach
    dem Entladen bis zu ``versuche`` Mal im Sekundentakt nachgesehen (der Speicher wird
    nicht im selben Augenblick frei). Nie ein Kosmo-Modell, nie während einer Frage: das
    prüft der Versuch, nicht diese Funktion.
    """
    import time as _time
    warte = _warte or _time.sleep

    def auskunft() -> tuple[bool, str]:
        darf, warum = darf_rechnen()
        if darf:
            return darf, warum
        try:
            versuch = entlade_versuch() or {}
        except Exception as fehler:            # noqa: BLE001 — Auskunft, kein Lauf
            versuch = {"entladen": False, "satz": f"{type(fehler).__name__}: {fehler}"}
        if versuch.get("entladen") is not True:
            satz = versuch.get("satz")
            return False, f"{warum} {satz}".strip() if satz else warum
        for _ in range(max(1, int(versuche))):
            warte(1.0)
            darf, nachher = darf_rechnen()
            if darf:
                return True, f"{versuch.get('satz')} Danach: {nachher}".strip()
        return False, f"{versuch.get('satz')} Danach weiterhin: {nachher}".strip()

    return auskunft


def _karte_frei(laufzettel: dict, darf_rechnen) -> tuple[bool, str]:
    """Darf gerechnet werden? — die Auflage des Auftrags gegen die Auskunft der Maschine.

    ``idle_window_only`` ist die Auflage der fremden Seite und heisst dasselbe wie unser
    ``nur_bei_leerlauf``. Fehlt die Auskunft, wird **nicht** gerechnet: „ungeprüft" ist
    nicht „in Ordnung" — dieselbe Regel wie in :mod:`aiimaging.belichtung` und
    :mod:`aiimaging.fortschritt`.

    **Was das Feld drüben bedeutet, ist seit dem 21.09.2026 entschieden** (E79, Antwort
    auf auf-20260911-107, übertragen am 22.09.2026): «kein anderer Renderlauf», nicht
    «Karte völlig frei»; und ein abgelehnter Lauf soll in der Warteschlange **bleiben**,
    mit sichtbarem Grund. Das Zweite tut diese Stelle: Sie fasst den Status nicht an, und
    :func:`hole_einen` heftet den Grund an den Laufzettel (bewacht in
    ``tests/test_interior_bestellung.py``). Das Erste entscheidet nicht diese Funktion,
    sondern die Auskunft ``darf_rechnen`` — im Betrieb ``tools/abholen.karte_auskunft``.
    """
    nur_leerlauf = bool(laufzettel.get("idle_window_only", False))
    if not nur_leerlauf:
        return True, ""
    if darf_rechnen is None:
        return False, (
            "Der Auftrag trägt 'idle_window_only', aber es gibt keine Auskunft über die "
            "Grafikkarte (darf_rechnen=None). Es wird NICHT gerechnet. Ungeprüft ist "
            "nicht dasselbe wie in Ordnung — und ein Auftrag, der die Karte bei "
            "unbekanntem Zustand belegt, ist genau das fail-open-Loch, das Sitzung 07 "
            "viermal gefunden hat."
        )
    darf, warum = darf_rechnen()
    if darf:
        # Der Grund geht mit — er traegt den Satz des Entladens (auf-20261020-291).
        return True, warum or ""
    return False, (f"Der Auftrag trägt 'idle_window_only' und die Karte ist nicht frei: "
                   f"{warum}")


#: Unter so viel freiem Grafikspeicher (MiB) wird **nicht geladen**, sondern gewartet.
#:
#: **Nur noch die Untergrenze für ungemessene Modelle** — seit ``auf-20260924-170`` trägt
#: jedes gemessene Modell seine eigene Grenze (``backbone.Backbone.mindest_frei_mib``).
#:
#: Ursprünglich, **vorläufig und abgeleitet, nicht gemessen** (24.09.2026, B161/B1):
#: Auf dem sparsamsten Weg (Stufe 3, ``cuda+schichtauslagerung``) hielt das
#: Bearbeitungsmodell 2,4–2,5 GiB Spitze (``auf-20260924-163`` B1/B2), das Vorgabemodell
#: in ``auf-20260923-160`` C rund 3,6 GiB. 4096 MiB liegt knapp darüber und ist zugleich
#: die Grenze, ab der ``tools/abholen.karte_auskunft`` einen fremden Belegungsgast
#: vermutet. Den echten Mindestwert je Modell misst die HomeStation (``auf-20260924-170``);
#: bis dahin ist diese Zahl eine Untergrenze mit Herkunft, keine Messung.
MINDEST_FREI_MIB = 4096


def ist_speichermangel(fehler) -> bool:
    """Ist das ein «Grafikspeicher reichte nicht»? — am Namen und am Wortlaut erkannt.

    Die Ausnahme kommt aus torch (``torch.cuda.OutOfMemoryError``), wird aber auf dem Weg
    zu uns in ``render.rendere`` zu Text und im Abholer zu einem ``AbholerError``. Darum
    wird am Text geprüft, nicht am Typ — der Typ ist hier nicht mehr da.
    """
    text = f"{type(fehler).__name__}: {fehler}"
    return "OutOfMemoryError" in text or "out of memory" in text.lower()


def _speichermangel_satz(fehler) -> str:
    return ("Abgebrochen: Der Grafikspeicher reichte während des Rechnens nicht "
            "(CUDA out of memory). Meist hält ein anderes Programm Speicher auf der "
            "Karte. Der Auftrag ist nicht gerechnet und muss neu bestellt werden. "
            f"Wortlaut: {str(fehler)[:240]}")


def mindest_frei_mib(backbone_name) -> tuple[int, str]:
    """Die Speichergrenze für DIESES Modell, und woher sie stammt.

    Gemessen am Registereintrag (``backbone.Backbone.mindest_frei_mib``, seit
    ``auf-20260924-170``), sonst :data:`MINDEST_FREI_MIB`. Ohne Modellangabe gilt das
    Vorgabemodell der Kette.
    """
    from . import backbone as _backbone, render as _render  # noqa: PLC0415
    name = backbone_name or _render.VORGABE_BACKBONE
    try:
        eintrag = _backbone.hole(name)
    except _backbone.BackboneError:
        return MINDEST_FREI_MIB, "Untergrenze (Modell unbekannt)"
    if eintrag.mindest_frei_mib is None:
        return MINDEST_FREI_MIB, f"Untergrenze ({name}: nicht gemessen)"
    return eintrag.mindest_frei_mib, f"gemessen für {name} ({eintrag.mindest_frei_beleg})"


#: Rahmt eine Richtungskamera des Abholers nach dem BAUWERK statt nach der Szene?
#:
#: **Ja, seit dem 30.09.2026 abends** — Owner-Entscheid (Sitzung 73 §13) mit Beweislauf
#: vorab: ``auf-20260930-188``, 16 Bilder, Augenurteil blind, Regel vor der Messung
#: festgelegt. Nach dem Bauwerk stand die Form in 6 von 8 Bildern, nach der Szene in 0 von 8
#: (dort erfand das Modell jedes Mal ein eigenes Motiv). Bauwerk-Anteil im Bild 17,9–21,0 %
#: gegen 2,0–4,0 %. Ein Auftrag mit eigener ``kamera_huellbox`` und Standpunkte von Hand
#: sind nicht betroffen; findet die Namensregel kein Gelände, bleibt es bei der Szene.
RAHMUNG_NACH_BAUWERK = True


def _glb_hochachse(hochachse) -> str:
    """Die Hochachse in der Schreibweise von :mod:`aiimaging.glbbox` (``"Y"``/``"Z"``).

    **Befund 08.10.2026 (beim Bau zu ``auf-20261008-271``):** Hier ging die Hochachse des
    Auftrags roh an ``glbbox.rahmungsbox`` — und ohne Angabe ist das
    :data:`ANGENOMMENE_HOCHACHSE` ``"Y_UP"``, also jeder glb-Auftrag der Brücke.
    ``glbbox`` kennt nur ``"Y"``, warf, und die Rahmung meldete «nicht lesbar — nach der
    Szene gerahmt». Die Rahmung nach dem Bauwerk (Owner-Entscheid 30.09.2026) kam auf
    diesem Weg also nie an. ``contracts.normalize_up_axis`` ist die eine Stelle für
    diese Schreibweisen.
    """
    from aiimaging import contracts
    try:
        return contracts.normalize_up_axis(hochachse or "Y")
    except Exception:                                   # noqa: BLE001 — dann wie bisher
        return str(hochachse or "Y")


def _rahmung_fuer(kamera_huellbox, modell, hochachse, richtung):
    """Die Box für die Kamera — gegeben, nach dem Bauwerk (wenn eingeschaltet), oder None."""
    if (kamera_huellbox is not None or not RAHMUNG_NACH_BAUWERK or richtung is None
            or modell is None):
        return kamera_huellbox
    from aiimaging import glbbox
    return glbbox.rahmungsbox(modell, up_axis=_glb_hochachse(hochachse))["box"]


def _ausschnitt_ohne_box(kamera_huellbox, modell, hochachse, richtung) -> bool:
    """Darf die Richtungskamera lange, flache Bauten als Ausschnitt zeigen, obwohl es
    keine Bauwerksbox gibt? **Ja, wenn das Bauwerk die Szene ist** (kein Gelände).

    **Anlass ``auf-20261008-271``:** Entscheid 75 hing an der Bauwerksbox, und die fehlt
    genau bei der Halle aus dem Splat — ohne Gelände ist Bauwerk gleich Szene. Alle neun
    Kameras zeigten die Halle ganz, auf 3,7–4,4 % des Bildes. Mit Gelände, das die
    Namensregel nicht fand, bleibt es aus: Dann wäre die Szenenbox eine Platte, und der
    Ausschnitt hebelte den Rahmungsriegel aus (``test_kettenlauf_echt``, Grundstück).
    """
    if (kamera_huellbox is not None or not RAHMUNG_NACH_BAUWERK or richtung is None
            or modell is None):
        return False
    from aiimaging import glbbox
    return bool(glbbox.rahmungsbox(modell, up_axis=_glb_hochachse(hochachse))
                .get("szene_ist_bauwerk"))


def _engine_aus(render_ergebnis) -> dict | None:
    """``{name, lizenz, fuehrung}`` aus dem Ergebnis des Bildmodells — oder ``None``.

    ``fuehrung`` bleibt ``None``, wenn der Adapter es nicht weiss; der Vertrag laesst das
    Feld dann weg (auf-155 F7: ``guidance_applied`` ist Boolean und nie null).

    **Seit dem 01.10.2026 aus** ``fuehrung_angewandt`` (C35, auf-20261001-230). Hier stand
    ``fuehrung_regler_angekommen`` — ob ein EIGENER Regler ankam. Das ist eine andere Frage,
    und fuer die Vorgabe ``z-image-turbo`` (kein eigener Regler) war sie immer ``None``:
    ``guidance_applied`` fehlte in jedem Ergebnis, obwohl dort belegt ist, dass ohne Fuehrung
    gerechnet wird (``render.fuehrung_angewandt``).
    """
    if not isinstance(render_ergebnis, dict) or not render_ergebnis.get("backbone"):
        return None
    lizenz = render_ergebnis.get("lizenz")
    parameter = render_ergebnis.get("parameter") or {}
    fuehrung = parameter.get("fuehrung_angewandt")
    return {"name": str(render_ergebnis["backbone"]),
            "lizenz": (lizenz.get("lizenz") if isinstance(lizenz, dict) else None),
            "fuehrung": fuehrung if isinstance(fuehrung, bool) else None,
            # E128: nicht verkaufbar, Lizenz offen — nur wenn der Lauf es sagt.
            "lizenz_offen": parameter.get("lizenz_offen") is True}


#: Welches Feld des Multipass-Berichts welche bestellte Ebene traegt (E124, Schritt 1).
EBENE_AUS_BERICHT = {"schoenbild": "beauty_png", "tiefe": "depth_png",
                     "material-id": "material_id_png"}


def ebenen_dieser_kamera(bericht: dict, kamera, bestellt) -> list[dict]:
    """Je bestellte Ebene ein Eintrag ``{kamera, art, datei, bedeutung, quelle}``.

    ``datei`` ist der **flache** Name ``<kamera>__<art>.png`` — ihr ``get_artifact`` nimmt
    nur ein Segment (Antwort auf auf-171, K4). ``quelle`` ist der Pfad auf dieser Maschine;
    die Bruecke kopiert von dort und streicht das Feld, bevor es hinausgeht (Regel 3).

    ``bedeutung`` ist **strukturiert, nicht Freitext** (ihre Bedingung a): Die Tiefe traegt
    ihre Grenzen in Metern und die Richtung, die Material-ID die Tabelle samt Nullfarbe.
    Fehlt die Datei, bleibt ``datei`` ``None`` und ``grund`` sagt warum — daraus wird die
    Kamera «fehlgeschlagen» (ihre Bedingung c, :func:`kosmo_szene._ebenen_mit_lieferung`).
    """
    bericht = bericht or {}
    aus: list[dict] = []
    for art in bestellt or ():
        feld = EBENE_AUS_BERICHT[art]
        quelle = bericht.get(feld)
        eintrag = {"kamera": str(kamera), "art": art, "datei": None, "bedeutung": None}
        if not quelle or not Path(quelle).is_file():
            fehler = bericht.get(feld + "_fehler")
            eintrag["grund"] = (f"Der Multipass hat kein {feld} geschrieben"
                                + (f" ({fehler})" if fehler else "") + ".")
            aus.append(eintrag)
            continue
        eintrag.update(datei=f"{kamera}__{art}.png", quelle=str(quelle),
                       bedeutung=_bedeutung_der_ebene(art, bericht))
        aus.append(eintrag)
    return aus


def _bedeutung_der_ebene(art: str, bericht: dict) -> dict:
    """Was ein Pixel dieser Ebene heisst — in Zahlen, nicht in Worten."""
    if art == "tiefe":
        n = bericht.get("depth_normalisierung") or {}
        return {"einheit": "m", "min_m": n.get("min_m"), "max_m": n.get("max_m"),
                "nah": "hell", "hintergrund_grauwert": n.get("hintergrund_grauwert", 0),
                "bittiefe": 8, "rueckrechnung": n.get("rueckrechnung")}
    if art == "material-id":
        return {"nullfarbe_srgb_8bit": [0, 0, 0],
                "tabelle": [{"index": e.get("index"), "name": e.get("name"),
                             "farbe_srgb_8bit": e.get("farbe_srgb_8bit")}
                            for e in (bericht.get("material_id_tabelle") or [])]}
    return {"renderer": "cycles", "samples": bericht.get("samples")}


def _ebenen_des_auftrags(urteile) -> list[dict]:
    """Die Ebenen aller Kameras, in der Reihenfolge der Kameras."""
    return [e for u in (urteile or ()) if isinstance(u, dict) for e in (u.get("ebenen") or ())]


def _engine_des_auftrags(urteile) -> dict | None:
    """Die Engine des Auftrags: die erste Kamera, die gerechnet hat.

    Ein Auftrag rechnet alle Kameras mit demselben Modell (``szene['backbone']``); stuenden
    doch zwei verschiedene da, faellt das Feld weg — eine Angabe fuer den ganzen Auftrag,
    die nur fuer einen Teil stimmt, ist schlechter als keine.
    """
    gesehen = [u.get("engine") for u in (urteile or ()) if isinstance(u, dict)
               and isinstance(u.get("engine"), dict)]
    if not gesehen:
        return None
    namen = {e["name"] for e in gesehen}
    return gesehen[0] if len(namen) == 1 else None


def _bildeingang_aus_vorgabe(szene: dict) -> bool:
    """Kam ``szene['bildeingang']`` aus der Vorgabe fuer Varianten (Entscheid 138)?"""
    return (((szene.get("messschalter") or {}).get("bildeingang") or {}).get("herkunft")
            == _kosmo_szene.HERKUNFT_VORGABE)


def bildeingang_vorgabe_zurueckziehen(szene: dict, grund: str) -> dict:
    """Die Szene ohne den Bildeingang der Vorgabe — Herkunft «vorgabe_entfaellt» mit Grund.

    Entscheid 138: Die Vorgabe soll eine Variante besser machen, nicht verhindern. Reicht die
    Karte fuer den Lauf mit Bildeingang nicht, rechnet die Variante wie vor dem Entscheid.
    """
    messschalter = dict(szene.get("messschalter") or {})
    messschalter["bildeingang"] = {
        "herkunft": _kosmo_szene.HERKUNFT_ENTFAELLT,
        "grund": (f"Vorgabe Bildeingang 0,5 (Entscheid 138) zurueckgezogen, die Variante rechnet "
                  f"ohne Grundbild als Start: {grund}")}
    return dict(szene, bildeingang=None, messschalter=messschalter)


def _bildeingang_lage(szene: dict, bildeingang_karte) -> dict | None:
    """Die Lage der Karte für einen Auftrag mit ``vis.bildeingang`` — oder ``None``.

    ``None``, wenn der Schalter nicht gesetzt ist oder keine Auskunft übergeben wurde. Eine
    Auskunft, die selbst scheitert, gilt als «unbekannt» (``reicht: None``), nicht als «frei».
    """
    if szene.get("bildeingang") is None or bildeingang_karte is None:
        return None
    from . import render as _render  # noqa: PLC0415
    try:
        karte = bildeingang_karte() or {}
    except Exception as fehler:                         # noqa: BLE001 — Auskunft, kein Riegel
        return {"reicht": None, "satz": (f"Bildeingang: Lage der Karte unbekannt "
                                         f"({type(fehler).__name__}) — nicht geprueft.")}
    return _render.pruefe_bildeingang_karte(
        gerechnetes_backbone(szene), frei_mib=karte.get("frei_mib"),
        eigen_mib=karte.get("eigen_mib") or 0, fremde_modelle=karte.get("fremde_modelle"))


def _speicher_reicht(speicher_frei, backbone_name=None) -> tuple[bool, str]:
    """Reicht der freie Grafikspeicher, um überhaupt zu laden? — B161/B1.

    Unbekannt (keine Auskunft, oder die Auskunft sagt ``None``) heisst hier **rechnen**,
    anders als bei ``idle_window_only``: Diese Prüfung ist neu und darf nichts sperren,
    was bis heute lief. Sie fängt den einen Fall, der bisher mit einem Absturz endete —
    ein fremdes Programm hält die Karte fast ganz.
    """
    if speicher_frei is None:
        return True, ""
    try:
        frei = speicher_frei()
    except Exception:                                   # noqa: BLE001 — Auskunft, kein Riegel
        return True, ""
    if frei is None or isinstance(frei, bool) or not isinstance(frei, (int, float)):
        return True, ""
    grenze, herkunft = mindest_frei_mib(backbone_name)
    if frei >= grenze:
        return True, ""
    return False, (
        f"Wartet: Die Grafikkarte hat nur {int(frei)} MiB frei; zum Laden braucht es auf "
        f"dem sparsamsten Weg mindestens {grenze} MiB ({herkunft}). Es wird nicht gerechnet — "
        f"der Auftrag bleibt in der Warteschlange und läuft, sobald Speicher frei wird "
        f"(meist hält ein anderes Programm ein Modell auf der Karte).")


def durchgang(store, *, verarbeite, fremde_freigabe_gilt: bool = False,
              darf_rechnen=None, hoechstens: int | None = None,
              waisenfrist_s: float = WAISENFRIST_S, wache_bauen=None,
              beobachtungs_takt_s: float = fortschritt.BEOBACHTUNGS_TAKT_S,
              quelle=bruecke, speicher_frei=None, bildeingang_karte=None,
              karte_freigeben=None, _uhr=None) -> dict:
    """**Ein** Durchgang über den Ablageort. Kein Dauerlauf, keine Schleife, kein Schlaf.

    Warum kein Dauerlauf: Wer wie oft nachsieht, ist eine Betriebsfrage — Cron, Dienst,
    Aufruf von Hand —, und sie gehört nicht in eine Bibliothek. Eine Bibliothek mit
    eingebauter ``while True``-Schleife lässt sich nicht prüfen, nicht einbetten und nicht
    sauber beenden.

    ``quelle`` sagt, **welche Ablage** durchgegangen wird — siehe :func:`hole_einen`. Ein
    Durchgang bedient genau eine; wer beide bedienen will, macht zwei Durchgänge. Das ist
    Absicht: Wieviel Arbeit ein Lauf annimmt, ist eine Betriebsfrage, und zwei Ablagen in
    einem Durchgang zu vermischen machte ``hoechstens`` mehrdeutig.

    Aufträge werden in der Reihenfolge ihres Eingangs bearbeitet (``offene_auftraege``
    sortiert nach dem Zeitstempel im Verzeichnisnamen). Wer zuerst kam, wird zuerst
    bedient; alles andere wäre für den Wartenden nicht nachvollziehbar.

    Args:
        hoechstens: höchstens so viele **Läufe** in diesem Durchgang — Aufträge, die
            wirklich angefangen wurden (``verarbeitet`` oder ``fehler``). ``None`` heisst
            alle. Nützlich für einen Rechner, der zwischendurch etwas anderes tun soll.

            **Ein liegengelassener Auftrag zählt nicht mit** (Sammel-Nachprobe
            ``auf-20261001-230``, 01.10.2026). Bis dahin wurde die Liste vor dem Lauf auf
            ``hoechstens`` gekürzt. Ein Auftrag, den die Feldkarte mit Mängeln aufhielt,
            blieb ``queued`` — richtig, so will es ihr Vertrag —, stand damit aber bei
            jedem Durchgang wieder vorn, wurde geprüft, aufgehalten, und mit
            ``--hoechstens 1`` war der Durchgang damit verbraucht. Alle späteren
            Aufträge warteten, bis jemand ``/cancel`` rief. *Ein Auftrag, der nicht
            rechnet, darf den Platz eines Auftrags, der rechnen könnte, nicht belegen.*
            Wofür ``hoechstens`` da ist — die Karte zwischendurch freizugeben —, kostet
            ein Aufhalten nicht: Es lädt nichts und rechnet nichts.

            Die Reihenfolge des Eingangs bleibt: Der aufgehaltene Auftrag wird weiter
            zuerst angesehen, sein Grund bleibt am Laufzettel, und sobald er rechnen darf,
            ist er wieder der erste. Nur sein Warten hält niemanden mehr auf.

    Jeder Auftrag bekommt seine **eigene** Wache: ``wache_bauen`` wird je Auftrag
    gerufen. Eine geteilte Wache trüge die Stillstandsuhr des Vorgängers in den nächsten
    Lauf und meldete dort einen Stillstand, den es nie gab.

    Returns:
        ``{gesehen, verarbeitet, fehler, liegengelassen, abgebrochen, waisen, ergebnisse, gestanden}``.
        ``gesehen`` zählt die Aufträge, die in diesem Durchgang angesehen wurden.
        ``gestanden`` zählt die Läufe, bei denen die Wache einen Stillstand sah.
        ``ergebnisse`` sind die Antworten von :func:`hole_einen` in Bearbeitungsreihenfolge.
    """
    offen = quelle.offene_auftraege(store)
    if hoechstens is not None:
        if isinstance(hoechstens, bool) or not isinstance(hoechstens, int):
            raise AbholerError(f"hoechstens muss eine ganze Zahl sein: {hoechstens!r}")
        if hoechstens < 0:
            raise AbholerError(f"hoechstens darf nicht negativ sein: {hoechstens}")

    ergebnisse = []
    gestartet = 0
    for ordner in offen:
        if hoechstens is not None and gestartet >= hoechstens:
            break
        antwort = hole_einen(ordner, verarbeite=verarbeite,
                             fremde_freigabe_gilt=fremde_freigabe_gilt,
                             darf_rechnen=darf_rechnen, wache_bauen=wache_bauen,
                             beobachtungs_takt_s=beobachtungs_takt_s,
                             quelle=quelle, speicher_frei=speicher_frei,
                             bildeingang_karte=bildeingang_karte,
                             karte_freigeben=karte_freigeben)
        ergebnisse.append(antwort)
        # Nur ein Lauf zaehlt gegen `hoechstens` — siehe Docstring (auf-20261001-230).
        if antwort["tat"] != TAT_LIEGENGELASSEN:
            gestartet += 1
    verwaist = waisen(store, frist_s=waisenfrist_s, quelle=quelle, _uhr=_uhr)

    bericht = {
        "gesehen": len(ergebnisse),
        "verarbeitet": sum(1 for e in ergebnisse if e["tat"] == TAT_VERARBEITET),
        "fehler": sum(1 for e in ergebnisse if e["tat"] == TAT_FEHLER),
        "liegengelassen": sum(1 for e in ergebnisse if e["tat"] == TAT_LIEGENGELASSEN),
        "abgebrochen": sum(1 for e in ergebnisse if e["tat"] == TAT_ABGEBROCHEN),
        "gestanden": sum(1 for e in ergebnisse if (e.get("wache") or {}).get("gestanden")),
        "waisen": verwaist,
        "ergebnisse": ergebnisse,
    }
    bericht["puls"] = schreibe_puls(store, bericht, _uhr=_uhr)
    return bericht


#: Der Name der Pulsdatei im Ablageort (B161/B8, 24.09.2026).
DATEI_PULS = "abholer-puls.json"
SCHEMA_PULS = "aiimaging.abholer-puls/v1"


def schreibe_puls(store, bericht: dict, *, _uhr=None) -> str:
    """Nach JEDEM Durchgang ein Lebenszeichen in den Ablageort — auch nach einem leeren.

    **Der Anlass (B161/B8):** KosmoOrbit fragte, was der Abholer meldet, wenn er läuft,
    aber nichts zu tun hat. Nachgemessen am 24.09.2026: nichts. Ein leerer Durchgang und
    ein Abholer, der gar nicht läuft, hinterliessen dieselbe Ablage, Datei für Datei —
    und ``/health`` wusste vom Abholer nichts. «Läuft, leer» war von «läuft nicht» nicht
    zu unterscheiden, und «schaut in die falsche Ablage» auch nicht.

    Die Datei trägt nur Zählungen und den Zeitpunkt; keinen Pfad (Regel 3), keine
    Auftragsinhalte. Gelesen wird sie von :func:`aiimaging.knotenweg.gesundheit` und —
    als Vorschlag — von ihrer Brücke.

    Returns:
        ``"geschrieben"`` oder ein Satz, warum nicht. Nie eine Ausnahme: Ein Puls, der den
        Durchgang umwirft, wäre ein Lebenszeichen, das tötet.
    """
    import json as _json  # noqa: PLC0415
    from datetime import datetime, timezone  # noqa: PLC0415

    ordner = Path(store)
    if not ordner.is_dir():
        # Den Ablageort NICHT anlegen: Ein Abholer, der in die falsche Ablage schaut, soll
        # dort keinen Puls hinterlassen, der nach «alles in Ordnung» aussieht.
        return "nicht geschrieben: Ablageort fehlt"
    jetzt = (_uhr or time.time)()
    puls = {
        "schema": SCHEMA_PULS,
        "zuletzt": datetime.fromtimestamp(jetzt, tz=timezone.utc).isoformat(
            timespec="seconds").replace("+00:00", "Z"),
        "zuletzt_epoch_s": round(jetzt, 3),
        "gesehen": bericht["gesehen"],
        "verarbeitet": bericht["verarbeitet"],
        "liegengelassen": bericht["liegengelassen"],
        "fehler": bericht["fehler"],
        "waisen": len(bericht["waisen"] or ()),
    }
    ziel = ordner / DATEI_PULS
    zwischen = ordner / (DATEI_PULS + ".schreibt")
    try:
        zwischen.write_text(_json.dumps(puls, ensure_ascii=False), encoding="utf-8")
        zwischen.replace(ziel)
    except OSError as fehler:
        return f"nicht geschrieben: {type(fehler).__name__}: {fehler}"
    return "geschrieben"


# ======================================================================================
# Der Weg vom Brückenauftrag durch unsere Kette
# ======================================================================================

#: Was wir annehmen, wenn die fremde Szene die Hochachse nicht nennt.
#:
#: ``kosmovis.render-scene/v1`` **hat kein Feld dafür.** Die glTF-Spezifikation schreibt
#: Y-up vor, also ist das die begründete Annahme — aber es bleibt eine Annahme, und
#: ausgerechnet an dieser Stelle hat dieses Projekt seinen Phase-0-Befund: Zwei Erzeuger
#: des Ökosystems liefern beide ein Feld ``glb_path``, mit **unterschiedlicher**
#: Orientierung. Eine verdrehte Hochachse dreht Tiefenkarte, Kamera und Geometrie-QA
#: gemeinsam — und fällt an einem einzelnen Bild nicht auf.
#:
#: Sie steht darum als benannte Konstante und wandert in jedes Ergebnis, statt still
#: mitzulaufen. Die Frage ist im Übergabeblatt gestellt.
ANGENOMMENE_HOCHACHSE = "Y_UP"

#: Welche Startwerte je Kamera gerendert werden.
#:
#: **Drei** (Owner-Entscheid 23.08.2026), vorher einer. Gerendert werden alle drei, und
#: behalten wird das nach ``gerichtet`` beste — vorausgesetzt, es gibt eine
#: Bauwerksmaske; ohne sie gibt es kein Mass, dem hier zu trauen wäre.
#:
#: **Die Kostenrechnung, die den Ausschlag gab.** Der Multipass kostet rund **97 s je
#: Kamera** (erster vollständiger Lauf, 19.08.), ein Bild des Bildmodells rund **1,3 s**.
#: Startwerte sind damit billig neben Ansichten: Zwei zusätzliche Bilder je Kamera kosten
#: rund 2,6 s gegen 97 s, dazu je eine Tiefenschätzung für die Messung. Und die
#: Seed-Streuung (0,2269) ist grösser als jeder Parametereffekt, den die Kette je gezeigt
#: hat — die Auswahl ist der billigste Qualitätssprung, den es hier gibt.
#:
#: **Feste Werte, nicht gewürfelt.** ``(0, 1, 2)`` steht hier, damit derselbe Auftrag
#: dieselben Bilder ergibt. Ein zufälliger Startwert machte jeden Lauf unwiederholbar,
#: und ohne Wiederholbarkeit gibt es keine Vergleichsreihe.
#:
#: **Was das mit dem Auftragsurteil macht, und was daran ungemessen ist.** Je Kamera wird
#: das BESTE von drei genommen, über die Kameras das SCHLECHTESTE von drei — die beiden
#: Auswahleffekte zeigen in entgegengesetzte Richtungen und sind gleich gross, *sofern*
#: die Streuung über Startwerte und die über Blickrichtungen ähnlich gross sind. Ob sie
#: das sind, ist **nicht gemessen**: 0,2269 stammt von Startwerten. Dass sich die beiden
#: Effekte aufheben, ist damit eine plausible Erwartung und kein Befund.
VORGABE_SEEDS = (0, 1, 2)


def ist_vorschau(szene: dict) -> bool:
    """Trägt die Bestellung ``vis.guete: "vorschau"``? (Owner-Entscheid 104, 20.10.2026)"""
    return (szene or {}).get("guete") == _kosmo_szene.GUETE_VORSCHAU


def gerechnetes_backbone(szene: dict) -> str:
    """Welches Bildmodell dieser Auftrag **rechnet** — nicht, welches er nennt.

    Bei der Vorschau immer :data:`aiimaging.backbone.VORSCHAU_BACKBONE`, auch wenn
    ``vis.backbone`` ein anderes nennt (Entscheid 104): Die Vorschau soll in Sekunden
    stehen, und der Demolauf vom 20.10.2026 brauchte rund neun Minuten, weil er das
    Forschungsmodell ``qwen-image-2.1`` mit 40 Schritten rechnete. Welches gerechnet hat,
    steht im Ergebnis (``engine_used``) und im Vermerk der Kamera. Sonst das bestellte,
    ohne Bestellung :data:`aiimaging.render.VORGABE_BACKBONE`.
    """
    from . import backbone as _backbone, render as _render  # noqa: PLC0415
    if ist_vorschau(szene):
        return _backbone.VORSCHAU_BACKBONE
    return (szene or {}).get("backbone") or _render.VORGABE_BACKBONE


def schritte_des_laufs(szene: dict) -> int:
    """Die Schritte des Bildmodells: Vorschau nach ``vorschau_schritte``, sonst wie bisher."""
    from . import backbone as _backbone  # noqa: PLC0415
    name = gerechnetes_backbone(szene)
    return (_backbone.vorschau_schritte_fuer(name) if ist_vorschau(szene)
            else _backbone.schritte_fuer(name))


def steuerstaerke_des_laufs(szene: dict) -> float:
    """Die Steuerstärke des Bildmodells: bei der Vorschau der Registerwert
    :attr:`aiimaging.backbone.Backbone.vorschau_steuerstaerke` (auf-20261020-292: 1,0 folgt
    dem Umriss besser als 0,8), sonst — und wenn er fehlt — ``faithful`` der Bestellung."""
    from . import backbone as _backbone  # noqa: PLC0415
    bestellt = szene.get("controlnet_staerke", 0.8)
    if ist_vorschau(szene):
        wert = _backbone.vorschau_steuerstaerke_fuer(gerechnetes_backbone(szene))
        if wert is not None:
            return float(wert)
    return bestellt


def seed_der_grundlage(geholt, kuerzel) -> int | None:
    """Der Startwert, den die Grundlage für diese Kamera behalten hat — oder ``None``.

    Ältere Grundlagen (vor dem 20.10.2026) tragen keinen; dann ``None``.
    """
    seeds = (geholt or {}).get("seeds") or {}
    wert = seeds.get(str(kuerzel)) if isinstance(seeds, dict) else None
    return wert if isinstance(wert, int) and not isinstance(wert, bool) else None


def seeds_der_kamera(szene: dict, geholt, kuerzel, seeds) -> tuple:
    """Welche Startwerte diese Kamera rechnet.

    * ``vis.seed`` bestellt: genau dieser (Nr. 84).
    * Vorschau ohne ``vis.seed``: genau EINER — der der Grundlage, sonst 0 (Entscheid 104).
      Die Auswahl aus drei kostet das Dreifache, und eine Vorschau soll schnell sein.
    * sonst ``seeds`` (Vorgabe :data:`VORGABE_SEEDS`).
    """
    if szene.get("seed") is not None:
        return (szene["seed"],)
    if ist_vorschau(szene):
        eigener = seed_der_grundlage(geholt, kuerzel)
        return (0 if eigener is None else eigener,)
    return tuple(seeds) if seeds else (0,)


#: Wohin die verkleinerten Steuerbilder der Vorschau kommen — je Kamera ein Unterordner,
#: NIE in die Grundlage: Sie bleibt, wie Blender sie schrieb, und für die volle Güte
#: wiederverwendbar.
VORSCHAU_ORDNER = "_vorschau"
#: Dasselbe für die volle Güte, wenn die bestellte Grösse nicht aufs Raster fällt
#: (auf-20261020-292, B5): Blender rechnet 960 x 600, das Bildmodell 960 x 592.
KI_RASTER_ORDNER = "_ki_raster"


#: Der Schluessel des Farbabgleich-Vermerks am Kameraurteil (Entscheid 117) — im Befund, NICHT
#: im Vertrag (``kosmo_szene.nur_vertragsfelder`` streicht ihn wie jeden fremden Schluessel).
URTEIL_FARBABGLEICH = _kosmo_szene.URTEIL_FARBABGLEICH

#: Der Schluessel des Bildeingang-Vermerks am Kameraurteil (Entscheid 117, auf-20261021-298 B1):
#: was das Bildmodell mit dem Schalter ``vis.bildeingang`` wirklich gerechnet hat. Von hier
#: erreicht er ``verdict.hinweise`` und ``angewandt.bildeingang`` im Ergebnis.
URTEIL_BILDEINGANG = _kosmo_szene.URTEIL_BILDEINGANG

#: Bis zu welcher Abweichung ``geom_iou`` vor und nach dem Farbabgleich als **gleich** gilt.
#:
#: **Befund auf-20261021-298 (B3):** ``geom_iou_gleich`` stand in allen zwölf Bildern auf
#: ``false``, obwohl die Abweichung 0,0001 bis 0,023 betrug — verglichen wurde auf 1e-9.
#: Kein Bildpunkt wandert (``kanten_iou`` 0,97–0,99); ``geom_iou`` misst aber der
#: Tiefenschaetzer **neu am Bild**, und der antwortet auch auf Farbe. 0,03 liegt knapp ueber
#: der groessten gemessenen Abweichung und unter jedem Abstand, an dem ein Urteil kippt
#: (die Satzschwelle «nicht wiederzuerkennen» liegt bei geom_iou 0,1). **Gesetzt an einer
#: Messung, nicht selbst gemessen** — die Zahl steht daneben (``geom_iou_abweichung``).
GEOM_IOU_TOLERANZ_FARBABGLEICH = 0.03


def farbabgleich_der_kamera(bild_png, schoenbild_png, ordner, *, urteil_vorher=None,
                            messen=None) -> dict:
    """Das KI-Bild einer Kamera an ihr Cycles-Bild angleichen (Entscheid 117, D1).

    Das Original kommt nach ``<ordner>/_ohne_farbabgleich/<name>`` (für die Tafel und die
    Nachprüfung), das abgeglichene Bild ersetzt das gelieferte. Der Vermerk trägt die
    Kennwerte vorher/nachher, die Kantenübereinstimmung (``kanten_iou``) und — wenn
    ``messen`` gegeben ist — ``geom_iou`` vor und nach dem Abgleich. Ein Fehler hier kostet
    das Bild nicht: Dann bleibt es unverändert, und der Vermerk sagt warum.
    """
    import shutil  # noqa: PLC0415
    from . import farbabgleich as _fa  # noqa: PLC0415

    bild = Path(bild_png)
    ohne = Path(ordner) / _fa.ORDNER_OHNE / bild.name
    try:
        ohne.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(bild, ohne)
        vermerk = _fa.gleiche_datei_ab(ohne, schoenbild_png, bild)
    except (OSError, ValueError) as fehler:
        # Das Bild bleibt, wie es war (die Kopie wird nur gelesen, `bild` erst am Ende
        # geschrieben); ValueError deckt auch einen unlesbaren PNG-Kopf ab.
        return {"angewandt": False, "methode": _fa.METHODE,
                "grund": f"Farbabgleich nicht moeglich: {type(fehler).__name__}: {fehler}"}
    vermerk["ohne_farbabgleich_png"] = f"{_fa.ORDNER_OHNE}/{bild.name}"
    if vermerk.get("angewandt") and messen is not None:
        vorher = (urteil_vorher or {}).get("geom_iou")
        try:
            nachher = (messen(str(bild)) or {}).get("geom_iou")
        except Exception as fehler:  # noqa: BLE001 — eine Nachmessung darf nichts kosten
            nachher = None
            vermerk["nachmessung_grund"] = f"{type(fehler).__name__}: {fehler}"
        vermerk["geom_iou_vorher"] = vorher
        vermerk["geom_iou_nachher"] = nachher
        abweichung = (None if vorher is None or nachher is None
                      else round(abs(float(vorher) - float(nachher)), 6))
        vermerk["geom_iou_abweichung"] = abweichung
        vermerk["geom_iou_toleranz"] = GEOM_IOU_TOLERANZ_FARBABGLEICH
        vermerk["geom_iou_gleich"] = (None if abweichung is None
                                      else abweichung <= GEOM_IOU_TOLERANZ_FARBABGLEICH)
    return vermerk


#: Der Schluessel des Vermerks «Umriss halten» am Kameraurteil (Strang Treue, 21.10.2026).
URTEIL_UMRISS_HALTEN = _kosmo_szene.URTEIL_UMRISS_HALTEN


def _ausserhalb_anteil(urteil):
    befund = (urteil or {}).get("ausserhalb_umriss") if isinstance(urteil, dict) else None
    return befund.get("anteil_haus") if isinstance(befund, dict) else None


#: Was vom Urteil des GEHALTENEN Bilds in den Vermerk geht (auf-20261021-303, B1): genau die
#: Felder, aus denen ``kosmo_szene`` die Saetze «KI BAUT UEBER DEN UMRISS HINAUS» und «HAUS IM
#: KI-BILD NICHT WIEDERZUERKENNEN» bildet — nicht mehr, damit das Kameraurteil (vor dem Halten)
#: das Urteil bleibt.
UMRISS_NACHHER_SATZFELDER = ("geom_iou", "n_ist", "n_soll", "n_gemeinsam", "score",
                             "anteil_soll", "ausserhalb_umriss", "haus_im_bild", "breite",
                             "hoehe")


def deckung_der_kamera(ki_png, grundbild_png) -> dict | None:
    """Das Deckungsurteil einer Kamera (L4-1): ``varianten.deckung_aus_bildern`` auf derselben
    Grundlage — oder ``None``, wenn KI-Bild oder Grundbild fehlen, die Masse ungleich sind oder
    das Lesen scheitert. Dann bleibt ``qa_je_kamera[].deckung`` weg (Vertrag: optional)."""
    if not ki_png or not grundbild_png or not Path(ki_png).is_file() or not Path(grundbild_png).is_file():
        return None
    try:
        urteil = varianten.deckung_aus_bildern(ki_png, grundbild_png, True)
    except Exception:                  # noqa: BLE001 — eine Zusatzauskunft haelt den Lauf nicht auf
        return None
    return urteil if urteil.get("kanten_iou") is not None else None


def _bestandsnamen(bestand) -> tuple:
    """Die Knotennamen des Bestands (``kosmo_szene.bestand_in_glb``) — leer ohne Bestand."""
    return tuple((bestand or {}).get("namen") or ()) if isinstance(bestand, dict) else ()


def _bodennamen(boden) -> tuple:
    """Knoten- und eigene Materialnamen des Bodens (``kosmo_szene.gelaende_in_glb``) — leer ohne."""
    return tuple((boden or {}).get("namen") or ()) if isinstance(boden, dict) else ()


def kontextmaske_der_kamera(bericht, ordner, kamera, bestand=None, boden=None) -> dict | None:
    """Die Kontextmaske einer Kamera (Video-Befund L4-5): Vermerk fuers Urteil, Datei daneben.

    ``None`` ohne Material-ID-Pass. Scheitert sie, steht der Grund im Vermerk — eine
    Zusatzauskunft haelt den Lauf nicht auf (dieselbe Linie wie die Bauwerksmaske). Die Datei
    ``<kamera>__kontext_maske.png`` (8 Bit, weiss = Kontext) entsteht nur, wenn es Kontext gibt.
    """
    png = (bericht or {}).get("material_id_png")
    if not png:
        return None
    namen = _bestandsnamen(bestand)
    try:
        # Der Boden mit Rolle (R56: ein TERRAIN-Element) ist Gelaende, nicht Umfeld.
        befund = maske_modul.kontextmaske_aus_lauf(png, bericht, bestand_namen=namen,
                                                   gelaende_rolle=_bodennamen(boden))
    except Exception as fehler:        # noqa: BLE001 — siehe Docstring
        return {"gemessen": False, "grund": f"{type(fehler).__name__}: {fehler}"}
    datei = None
    if befund.get("maske"):
        from . import bildschreiben  # noqa: PLC0415
        ziel = Path(ordner) / f"{kamera}__kontext_maske.png"
        bildschreiben.schreibe_graustufen_png(
            ziel, [1.0 if m else 0.0 for m in befund["maske"]],
            befund["breite"], befund["hoehe"], bittiefe=8)
        datei = ziel.name
    return maske_modul.kontext_vermerk(befund, datei)


def umriss_halten_der_kamera(bild_png, schoenbild_png, maske, breite, hoehe, ordner, *,
                             urteil_vorher=None, messen=None) -> dict:
    """Art ``nachher`` des Messschalters ``vis.umriss_halten`` (Strang Treue) an einer Kamera.

    Wie beim Farbabgleich: Das Original kommt nach ``<ordner>/_ohne_umriss_halten/<name>``,
    das gehaltene Bild ersetzt das gelieferte. Gemessen wird mit ``messen`` ein zweites Mal —
    ``geom_iou`` und ``ausserhalb_umriss_anteil`` vor und nach dem Halten stehen im Vermerk.
    Das Kameraurteil selbst bleibt das des KI-Bilds VOR dem Halten (die Seedwahl hat daran
    gewählt). Ein Fehler kostet das Bild nicht: Dann bleibt es, und der Vermerk sagt warum.
    Seit auf-20261021-303 (B1) steht das Urteil des gehaltenen Bilds unter ``urteil_nachher``
    (:data:`UMRISS_NACHHER_SATZFELDER`) — daraus kommen die Saetze zum Umriss im Ergebnis.
    """
    import shutil  # noqa: PLC0415
    from . import umrisshalt as _uh  # noqa: PLC0415

    if maske is None:
        return {"angewandt": False, "art": _uh.ART_NACHHER,
                "grund": "keine Bauwerksmaske (Material-ID-Pass oder Gelaenderegel) — ohne "
                         "sie ist nicht bekannt, wo das Haus steht"}
    if not schoenbild_png:
        return {"angewandt": False, "art": _uh.ART_NACHHER,
                "grund": "kein Cycles-Bild der Grundlage"}
    bild = Path(bild_png)
    ohne = Path(ordner) / _uh.ORDNER_OHNE / bild.name
    try:
        ohne.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(bild, ohne)
        vermerk = _uh.halte_datei(ohne, schoenbild_png, maske, int(breite), int(hoehe), bild)
    except (OSError, ValueError) as fehler:
        return {"angewandt": False, "art": _uh.ART_NACHHER,
                "grund": f"Umriss halten nicht moeglich: {type(fehler).__name__}: {fehler}"}
    vermerk["ohne_umriss_halten_png"] = f"{_uh.ORDNER_OHNE}/{bild.name}"
    vermerk["geom_iou_vorher"] = (urteil_vorher or {}).get("geom_iou")
    vermerk["ausserhalb_vorher"] = _ausserhalb_anteil(urteil_vorher)
    if messen is not None:
        try:
            nachher = messen(str(bild)) or {}
            vermerk["geom_iou_nachher"] = nachher.get("geom_iou")
            vermerk["ausserhalb_nachher"] = _ausserhalb_anteil(nachher)
            # DIE SAETZE GEHOEREN ZUM GELIEFERTEN BILD (auf-20261021-303, B1): Bis 0.3.16
            # trugen «UEBER DEN UMRISS» und «NICHT WIEDERZUERKENNEN» das Urteil von VOR dem
            # Halten — wer nur die Saetze las, hielt das gelieferte Bild fuer falsch.
            # `kosmo_szene` bildet sie jetzt hieraus; das Vorher-Urteil bleibt das Kameraurteil.
            vermerk["urteil_nachher"] = {
                k: nachher[k] for k in UMRISS_NACHHER_SATZFELDER if k in nachher}
            if "breite" not in vermerk["urteil_nachher"]:
                vermerk["urteil_nachher"].update(breite=int(breite), hoehe=int(hoehe))
        except Exception as fehler:  # noqa: BLE001 — eine Nachmessung darf nichts kosten
            vermerk["geom_iou_nachher"] = None
            vermerk["ausserhalb_nachher"] = None
            vermerk["nachmessung_grund"] = f"{type(fehler).__name__}: {fehler}"
    return vermerk


def umriss_halten_vermerk_im_lauf(render_ergebnis, freigabe) -> dict:
    """Art ``im_lauf``: was das Bildmodell gemeldet hat — ``{angewandt, art, schritte, …}``.

    ``angewandt`` ist True nur, wenn der Hintergrund in mindestens einem Schritt gehalten
    wurde (``umriss_halten_schritte`` > 0); None, wenn die Naht nichts meldete.
    """
    from . import umrisshalt as _uh  # noqa: PLC0415
    erg = render_ergebnis if isinstance(render_ergebnis, dict) else {}
    schritte = (erg.get("parameter") or {}).get("umriss_halten_schritte")
    saetze = [h for h in (erg.get("hinweise") or ()) if isinstance(h, str)
              and h.startswith(_uh.SATZ)]
    angewandt = None if schritte is None else schritte > 0
    vermerk = dict(freigabe or {}, angewandt=angewandt, art=_uh.ART_IM_LAUF,
                   schritte=schritte, hinweise=saetze)
    if angewandt is not True:
        vermerk["grund"] = (saetze[0] if saetze else
                            "das Bildmodell hat nicht gemeldet, ob der Hintergrund gehalten "
                            "wurde — UNBEKANNT")
    return vermerk


#: Welche Hinweise des Bildmodells zum Bildeingang gehoeren — am Anfang erkannt.
_BILDEINGANG_SAETZE = ("BILD UND TIEFE", "MESSSCHALTER bildeingang", "BESTELLT WAR")


def bildeingang_vermerk(render_ergebnis, staerke) -> dict:
    """Was der Messschalter ``vis.bildeingang`` an DIESER Kamera gerechnet hat (auf-298 B1).

    ``{staerke, weg, modus_bestellt, modus_gerechnet, modus_abweichung, schritte_bestellt,
    schritte_gerechnet, hinweise}`` — aus dem Ergebnis des Bildmodells. **Befund 298:** Ueber
    die Bruecke stand weder ``modus`` noch einer der beiden Saetze im Ergebnis; ob der Schalter
    gerechnet hatte, war nur ueber eine bitgleiche Nachrechnung zu sehen. ``None`` in einem
    Feld heisst: das Bildmodell hat es nicht gemeldet.
    """
    erg = render_ergebnis if isinstance(render_ergebnis, dict) else {}
    parameter = erg.get("parameter") or {}
    return {
        "staerke": float(staerke) if isinstance(staerke, (int, float)) else staerke,
        "weg": parameter.get("bildeingang_weg"),
        "modus_bestellt": erg.get("modus_bestellt"),
        "modus_gerechnet": erg.get("modus_gerechnet"),
        "modus_abweichung": erg.get("modus_abweichung"),
        "schritte_bestellt": parameter.get("schritte"),
        "schritte_gerechnet": erg.get("schritte_gerechnet"),
        "hinweise": [h for h in (erg.get("hinweise") or ())
                     if isinstance(h, str) and h.startswith(_BILDEINGANG_SAETZE)],
    }


#: Der Schluessel des Modus-Vermerks am Kameraurteil (Vertrag C17 A1, 21.10.2026): wie das
#: KI-Bild dieser Kamera entstand — bestellt, gerechnet, Abweichung. An JEDEM Lauf mit KI-Schritt,
#: nicht nur mit einem Messschalter; im Zweig «nur Grundlage» fehlt er (kein Bildmodell).
URTEIL_MODUS = "modus"


def modus_vermerk(render_ergebnis) -> dict | None:
    """``{bestellt, gerechnet, abweichung}`` aus dem Ergebnis des Bildmodells — oder ``None``.

    **Vertrag C17 A1:** ``gerechnet`` ``None`` heisst «das Bildmodell hat es nicht gemeldet»
    und ist NICHT dasselbe wie gleich; ``abweichung`` ist dann ebenfalls ``None``. ``None``
    statt eines Vermerks, wenn das Ergebnis gar keinen bestellten Modus nennt (eine Attrappe
    oder ein Ergebnis von vor dem 21.09.2026) — dann gibt es nichts zu sagen.
    """
    erg = render_ergebnis if isinstance(render_ergebnis, dict) else {}
    bestellt = erg.get("modus_bestellt")
    if not isinstance(bestellt, str):
        return None
    gerechnet = erg.get("modus_gerechnet")
    gerechnet = gerechnet if isinstance(gerechnet, str) else None
    abweichung = erg.get("modus_abweichung")
    if not isinstance(abweichung, bool):
        abweichung = None if gerechnet is None else gerechnet != bestellt
    return {"bestellt": bestellt, "gerechnet": gerechnet, "abweichung": abweichung}


def modus_des_auftrags(urteile) -> dict | None:
    """``angewandt.modus`` (Vertrag C17 A1) — der gemeinsame Wert oben, je Kamera darunter.

    * ``bestellt``/``gerechnet`` oben: der Wert, wenn alle Kameras denselben haben, sonst
      ``None``. Rechneten die Kameras verschieden, steht oben ``gerechnet`` also ``None``.
    * ``abweichung`` oben: ``True``, sobald eine Kamera abwich; sonst ``None``, wenn eine nichts
      meldete; ``False`` nur, wenn alle meldeten und keine abwich.
    * ``kameras {<kamera>: {gerechnet, abweichung}}`` — immer, damit die Anzeige je Bild lesen
      kann, ohne zu wissen, ob oben ein gemeinsamer Wert steht.

    ``None``, wenn keine Kamera einen Vermerk traegt — dann fehlt das Feld im Ergebnis.
    """
    je = {str(u.get("kamera")): u[URTEIL_MODUS] for u in (urteile or ())
          if isinstance(u, dict) and isinstance(u.get(URTEIL_MODUS), dict)}
    if not je:
        return None

    def gemeinsam(feld):
        werte = {v.get(feld) for v in je.values()}
        return next(iter(werte)) if len(werte) == 1 else None

    abweichungen = [v.get("abweichung") for v in je.values()]
    abweichung = (True if True in abweichungen else None if None in abweichungen else False)
    return {"bestellt": gemeinsam("bestellt"), "gerechnet": gemeinsam("gerechnet"),
            "abweichung": abweichung,
            "kameras": {k: {"gerechnet": v.get("gerechnet"), "abweichung": v.get("abweichung")}
                        for k, v in je.items()}}


#: Der Schluessel des KI-Vermerks am Kameraurteil (auf-20261022-336, Variantenweg): der
#: gerechnete Modus in den gelaeufigen Woertern ``img2img``/``txt2img`` und die wirksame
#: Entrauschstaerke ``denoise`` — eine Zeile, die man ohne das Register lesen kann.
URTEIL_KI = "ki"
#: Die Woerter fuer ``ki.modus``. ``img2img`` heisst: das Cycles-Bild war der Start im Haus
#: (gerechnet ``bild_und_tiefe`` oder ``image_edit``); ``txt2img``: im Haus aus reinem Rauschen.
KI_IMG2IMG = "img2img"
KI_TXT2IMG = "txt2img"
#: Der Anfang der Warnung bei einem Rueckfall — Proben und Auswerter suchen danach.
SATZ_KI_RUECKFALL = "KI-RUECKFALL AUF TXT2IMG"


def ki_vermerk(render_ergebnis, *, bildeingang_staerke=None, umriss_im_lauf: bool = False,
               modus_satz: str | None = None,
               bildeingang_abgeschaltet: bool = False) -> dict | None:
    """``{modus, denoise, denoise_bestellt, rueckfall, grundbild_im_haus, grundbild_ausserhalb,
    steuerung, steuerstaerke, warnung}`` — wie das KI-Bild DIESER Kamera entstand, oder ``None``.

    **Anlass auf-20261022-333..336 (HomeStation, demo-kritisch):** Die KI-Variante zeigte eine
    andere Fensterteilung als das Cycles-Bild; ``angewandt.modus`` sagte zwar ``image_edit``
    bestellt, ``txt2img`` gerechnet, aber in Woertern des Registers und ohne die Zahl, die
    sagt, wie viel neu gemalt wurde. Hier steht beides in den gelaeufigen Woertern:

    * ``modus`` — ``img2img`` (Cycles-Bild war der Start: gerechnet ``bild_und_tiefe`` oder
      ``image_edit``), ``txt2img`` (reines Rauschen im Haus), ``tiefe_als_bild``, ``None``
      (das Bildmodell hat nichts gemeldet — UNBEKANNT, nicht txt2img).
    * ``denoise`` — die WIRKSAME Staerke, 0..1: bei ``bild_und_tiefe`` die Staerke des
      Bildeingangs, bei ``image_edit`` ``parameter.denoise``, bei ``txt2img`` **1.0** (alles neu
      gemalt). ``denoise_bestellt`` daneben, was bestellt war (bei ``z-image-turbo`` 0,6, das
      die Pipeline verwirft).
    * ``rueckfall`` — bestellt war ein Bild als Start, gerechnet ``txt2img``; dann steht in
      ``warnung`` ein Satz, der mit :data:`SATZ_KI_RUECKFALL` beginnt (der lange Satz aus
      ``modus_satz`` haengt an). Die Warnung steht auch, wenn der Rueckfall der bekannte ist
      (``Backbone.bildeingang_traegt=False``): bekannt heisst nicht unsichtbar.

    ``bildeingang_abgeschaltet`` (Befund 340): ``vis.bildeingang: false`` war ausdruecklich
    bestellt. Dann sagt die Warnung das — und nicht «bestellt 'image_edit' (denoise 0.6)»,
    denn bestellt war keine Zahl, sondern das Abschalten des Bildeingangs.

    Kein Vertragsfeld (C17 ist ``angewandt.modus``); additiv wie die Messschalter.
    """
    erg = render_ergebnis if isinstance(render_ergebnis, dict) else {}
    bestellt = erg.get("modus_bestellt")
    if not isinstance(bestellt, str):
        return None
    parameter = erg.get("parameter") if isinstance(erg.get("parameter"), dict) else {}
    gerechnet = erg.get("modus_gerechnet") if isinstance(erg.get("modus_gerechnet"), str) else None

    def zahl(wert):
        return (float(wert) if isinstance(wert, (int, float)) and not isinstance(wert, bool)
                else None)

    staerke = zahl(bildeingang_staerke if bildeingang_staerke is not None
                   else parameter.get("bildeingang_staerke"))
    denoise_param = zahl(parameter.get("denoise"))
    if gerechnet == "bild_und_tiefe":
        modus, denoise = KI_IMG2IMG, staerke
    elif gerechnet == "image_edit":
        modus, denoise = KI_IMG2IMG, denoise_param
    elif gerechnet == "txt2img":
        modus, denoise = KI_TXT2IMG, 1.0
    elif gerechnet is None:
        modus, denoise = None, None
    else:
        modus, denoise = gerechnet, denoise_param
    if bildeingang_abgeschaltet:
        # Ergebnis 342 (h): Bestellt war das Abschalten, keine Zahl. Die 0,6 ist die Vorgabe
        # des Registers fuer `image_edit` — die hat niemand bestellt.
        denoise_bestellt = None
    elif bestellt == "bild_und_tiefe":
        denoise_bestellt = staerke
    elif bestellt == "image_edit":
        denoise_bestellt = denoise_param
    else:
        denoise_bestellt = 1.0
    rueckfall = bestellt in ("image_edit", "bild_und_tiefe") and gerechnet == "txt2img"
    warnung = None
    if rueckfall:
        wo = ("im Haus; ausserhalb gilt das Cycles-Bild (Umriss halten im Lauf)"
              if umriss_im_lauf else "im ganzen Bild")
        if bildeingang_abgeschaltet:
            # Befund 340: bestellt war nur `vis.bildeingang: false`, keine Zahl.
            warnung = (f"{SATZ_KI_RUECKFALL}: der Bildeingang ist abgeschaltet (bestellt "
                       f"'vis.bildeingang: false'), gerechnet 'txt2img' {wo} — das KI-Bild "
                       f"beginnt dort aus Rauschen, nicht aus dem Grundbild; Fensterteilung und "
                       f"Material folgen nur der Tiefenkarte. Ohne den Schalter gilt fuer "
                       f"Varianten die Vorgabe 0,5 (Entscheid 138).")
        else:
            warnung = (f"{SATZ_KI_RUECKFALL}: bestellt '{bestellt}' (denoise "
                       f"{denoise_bestellt}), gerechnet 'txt2img' {wo} — das KI-Bild beginnt "
                       f"dort aus Rauschen, nicht aus dem Grundbild; Fensterteilung und Material "
                       f"folgen nur der Tiefenkarte. Ein Weg mit dem Grundbild als Start ist "
                       f"vis.bildeingang (seit Entscheid 138 Vorgabe 0,5 fuer Varianten, wo das "
                       f"Modell ihn traegt und die Lizenz frei ist; warum er hier nicht galt, "
                       f"steht unter angewandt.messschalter.bildeingang).")
        # Beim abgeschalteten Bildeingang KEIN angehaengter Satz des Registers (Ergebnis 342,
        # h): Er sagte «bestellt 'image_edit'» und «hier nicht gerechnet», und genau das war
        # der zweite Teil der Warnung, der den Fix aus §258 am Geraet aufhob. Der erste Teil
        # sagt schon alles.
        if modus_satz and not bildeingang_abgeschaltet:
            warnung = f"{warnung} {modus_satz}"
    return {"modus": modus, "denoise": denoise, "denoise_bestellt": denoise_bestellt,
            "rueckfall": rueckfall,
            "grundbild_im_haus": None if modus is None else modus == KI_IMG2IMG,
            "grundbild_ausserhalb": bool(umriss_im_lauf) or modus == KI_IMG2IMG,
            # Die Fuehrung aus dem Register (bei z-image-turbo «depth_controlnet»: die Tiefe
            # ueber das Union-ControlNet); Kanten gehen heute nicht als Steuerbild ins Modell.
            "steuerung": parameter.get("konditionierung"),
            "steuerstaerke": zahl(parameter.get("controlnet_staerke")),
            "warnung": warnung}


def ki_des_auftrags(urteile) -> dict | None:
    """``angewandt.ki`` — gemeinsamer Modus und ``denoise`` oben, je Kamera darunter, und die
    Warnung(en) eines Rueckfalls. ``None`` ohne KI-Vermerk (dann fehlt das Feld)."""
    je = {str(u.get("kamera")): u[URTEIL_KI] for u in (urteile or ())
          if isinstance(u, dict) and isinstance(u.get(URTEIL_KI), dict)}
    if not je:
        return None

    def gemeinsam(feld):
        werte = {v.get(feld) for v in je.values()}
        return next(iter(werte)) if len(werte) == 1 else None

    warnungen = []
    for v in je.values():
        if v.get("warnung") and v["warnung"] not in warnungen:
            warnungen.append(v["warnung"])
    return {"modus": gemeinsam("modus"), "denoise": gemeinsam("denoise"),
            "rueckfall": any(v.get("rueckfall") is True for v in je.values()),
            "warnungen": warnungen,
            "kameras": {k: {f: v.get(f) for f in ("modus", "denoise", "denoise_bestellt",
                                                  "rueckfall", "grundbild_im_haus",
                                                  "grundbild_ausserhalb")}
                        for k, v in je.items()}}


#: Was aus dem Farbabgleich-Vermerk einer Kamera ins Ergebnis geht (``angewandt.farbabgleich``)
#: — die Zahlen, an denen man sieht, DASS und WIE er gerechnet hat; die Kennwerte bleiben im
#: Befund.
_FARBABGLEICH_IM_ERGEBNIS = ("angewandt", "grund", "streckung", "begrenzt", "geklippt_anteil",
                             "kanten_iou", "geom_iou_abweichung", "geom_iou_gleich")


def angewandt_mit_messschaltern(angewandt: dict | None, urteile) -> dict:
    """``angewandt`` und dazu die Messschalter aus Entscheid 117, wenn sie gerechnet haben.

    **Additiv, kein Vertragsfeld** (auf-20261021-298, B1): ``angewandt`` ist das Feld, in dem
    der Heim-PC nennt, womit er gerechnet hat; der Vertrag gibt dort keine Form vor.

    * ``bildeingang {staerke, weg, modus, kameras {<kamera>: modus_gerechnet}}`` — ``modus``
      ist der gerechnete Modus, wenn alle Kameras gleich rechneten, sonst ``None``.
    * ``farbabgleich {methode, kameras {<kamera>: {angewandt, streckung, …}}}``.
    * ``umriss_halten {art, kameras {<kamera>: {angewandt, art, schritte, hinweise, …}}}`` —
      seit auf-20261021-303 (B2), Messschalter des Strangs Treue; ``hinweise`` traegt den Satz
      des Bildmodells («Hintergrund im Fahrplan festgehalten …»).

    Dazu ``modus {bestellt, gerechnet, abweichung, kameras}`` (Vertrag C17 A1, 21.10.2026) —
    KEIN Messschalter: an jedem Lauf, dessen Kameras einen Modus-Vermerk tragen
    (:func:`modus_des_auftrags`).

    Und ``ki {modus, denoise, rueckfall, warnungen, kameras}`` (auf-20261022-336) — derselbe
    Befund in den Woertern ``img2img``/``txt2img`` mit der wirksamen Entrauschstaerke und der
    Warnung bei einem Rueckfall (:func:`ki_des_auftrags`); kein Vertragsfeld.

    Ohne Schalter bleibt ``angewandt`` Wort fuer Wort, wie es war — bis auf ``modus``.
    """
    aus = dict(angewandt or {})
    modus = modus_des_auftrags(urteile)
    if modus is not None:
        aus["modus"] = modus
    ki = ki_des_auftrags(urteile)
    if ki is not None:
        aus["ki"] = ki
    bild = {str(u.get("kamera")): u[URTEIL_BILDEINGANG] for u in (urteile or ())
            if isinstance(u, dict) and isinstance(u.get(URTEIL_BILDEINGANG), dict)}
    if bild:
        erster = next(iter(bild.values()))
        modi = {v.get("modus_gerechnet") for v in bild.values()}
        aus["bildeingang"] = {"staerke": erster.get("staerke"), "weg": erster.get("weg"),
                              "modus": next(iter(modi)) if len(modi) == 1 else None,
                              "kameras": {k: v.get("modus_gerechnet") for k, v in bild.items()}}
    farbe = {str(u.get("kamera")): u[URTEIL_FARBABGLEICH] for u in (urteile or ())
             if isinstance(u, dict) and isinstance(u.get(URTEIL_FARBABGLEICH), dict)}
    if farbe:
        from . import farbabgleich as _fa  # noqa: PLC0415
        aus["farbabgleich"] = {
            "methode": _fa.METHODE,
            "kameras": {k: {f: v[f] for f in _FARBABGLEICH_IM_ERGEBNIS if f in v}
                        for k, v in farbe.items()}}
    umriss = {str(u.get("kamera")): u[URTEIL_UMRISS_HALTEN] for u in (urteile or ())
              if isinstance(u, dict) and isinstance(u.get(URTEIL_UMRISS_HALTEN), dict)}
    if umriss:
        # UMRISS HALTEN (auf-20261021-303, B2): der Satz des Bildmodells stand nur im Befund.
        arten = {v.get("art") for v in umriss.values()}
        aus["umriss_halten"] = {
            "art": next(iter(arten)) if len(arten) == 1 else None,
            "kameras": {k: {f: v[f] for f in _UMRISS_HALTEN_IM_ERGEBNIS if f in v}
                        for k, v in umriss.items()}}
    return aus


#: Was aus dem Vermerk «Umriss halten» einer Kamera ins Ergebnis geht (``angewandt.umriss_halten``,
#: auf-20261021-303 B2) — DASS und WIE gehalten wurde, mit dem Satz des Bildmodells; die Pfade
#: der Masken und das ganze Urteil nach dem Halten bleiben im Befund.
_UMRISS_HALTEN_IM_ERGEBNIS = ("angewandt", "vorgabe", "art", "grund", "methode", "rand_px", "weich_px",
                              "anteil_frei", "schritte", "hinweise", "geom_iou_vorher",
                              "ausserhalb_vorher", "geom_iou_nachher", "ausserhalb_nachher")


def ki_mindest_lange_seite(backbone_name) -> int | None:
    """Die kleinste lange Seite des KI-Schritts für dieses Modell (auf-20261020-293 B3) —
    der Registerwert, keine Zahl hier."""
    from . import backbone as _backbone  # noqa: PLC0415
    return _backbone.ki_mindest_lange_seite_fuer(backbone_name)


def ki_steuerbilder(tiefe_png, schoenbild_png, ordner, *, vorschau: bool,
                    lange_seite=None, mindest_lange_seite=None) -> dict:
    """Die Steuerbilder in der Grösse, in der das Bildmodell rechnet.

    Vorschau: :func:`vorschau_steuerbilder` (verkleinert und gerastert). Volle Güte: nur
    gerastert (:func:`aiimaging.backbone.ki_raster_groesse`) — liegt die Grundlage schon
    auf dem Raster, bleibt alles, wie es ist (``verkleinert: False``). Das KI-Bild wird danach
    auf ``grundlage_groesse`` zurückgebracht, also auf die bestellte Grösse.

    ``mindest_lange_seite`` (:attr:`aiimaging.backbone.Backbone.ki_mindest_lange_seite`,
    auf-20261020-293 B3): Ist die Grundlage kleiner, werden die Steuerbilder für den
    KI-Schritt hochgerechnet (``hochgerechnet: True``), in beiden Güten.
    """
    if vorschau:
        return vorschau_steuerbilder(tiefe_png, schoenbild_png, ordner,
                                     lange_seite=lange_seite,
                                     mindest_lange_seite=mindest_lange_seite)
    return vorschau_steuerbilder(tiefe_png, schoenbild_png, ordner, nur_raster=True,
                                 mindest_lange_seite=mindest_lange_seite)


def _schon_im_raster_oder_zu_klein(breite: int, hoehe: int) -> bool:
    """Nichts zu tun: auf dem Raster — oder kleiner als ein Rasterfeld (dann waere jede
    Groesse falsch, und hochrechnen hiesse erfinden; die Pipeline sagt es selbst)."""
    from . import backbone as _backbone  # noqa: PLC0415
    r = _backbone.PIXEL_RASTER
    return (breite % r == 0 and hoehe % r == 0) or breite < r or hoehe < r


def vorschau_steuerbilder(tiefe_png, schoenbild_png, ordner, *, lange_seite=None,
                          nur_raster: bool = False, mindest_lange_seite=None) -> dict:
    """Tiefenkarte und Schönbild für den KI-Schritt der Vorschau verkleinern (Entscheid 104).

    Das Seitenverhältnis bleibt, die lange Seite geht auf höchstens
    :data:`aiimaging.backbone.VORSCHAU_LANGE_SEITE`, beide Seiten auf ein Vielfaches von
    :data:`aiimaging.backbone.PIXEL_RASTER`. Ist die Tiefenkarte schon klein genug, bleibt
    alles, wie es ist (``verkleinert: False``) — dann rechnet die Vorschau in der Grösse
    der Grundlage.

    Die Originale werden **nicht** angefasst: Geschrieben wird in ``ordner``.

    Returns:
        ``{tiefe_png, schoenbild_png, ki_groesse, grundlage_groesse, verkleinert, weg,
        schoenbild_grund}``. ``schoenbild_png`` ist ``None``, wenn es keines gab oder es
        sich nicht verkleinern liess — dann sagt ``schoenbild_grund`` warum (ein Schönbild
        in anderer Grösse als die Tiefe brächte eine Pipeline mit Bildeingang durcheinander).
    """
    from . import backbone as _backbone, bildschreiben  # noqa: PLC0415
    breite, hoehe = bildschreiben.png_masse(tiefe_png)
    zu_klein = (bool(mindest_lange_seite) and max(breite, hoehe) < int(mindest_lange_seite)
                and min(breite, hoehe) >= _backbone.PIXEL_RASTER)
    if nur_raster and not zu_klein and _schon_im_raster_oder_zu_klein(breite, hoehe):
        ziel_b, ziel_h = breite, hoehe
    else:
        # DIE UNTERGRENZE DES MODELLS (auf-20261020-293 B3): `backbone.ki_groesse` rechnet
        # erst wie bisher und dann, wenn noetig, auf die kleinste lange Seite hoch.
        ziel_b, ziel_h = _backbone.ki_groesse(
            breite, hoehe, vorschau=not nur_raster, mindest=mindest_lange_seite,
            lange_seite=lange_seite or _backbone.VORSCHAU_LANGE_SEITE)
    # `verkleinert` heisst seit 293 «in anderer Groesse als die Grundlage» (das KI-Bild geht
    # danach zurueck) — der Name bleibt, weil ihn Ergebnis und Proben lesen; `hochgerechnet`
    # sagt die Richtung.
    befund = {"grundlage_groesse": [breite, hoehe], "ki_groesse": [ziel_b, ziel_h],
              "verkleinert": (ziel_b, ziel_h) != (breite, hoehe),
              "hochgerechnet": ziel_b * ziel_h > breite * hoehe, "weg": None,
              "tiefe_png": str(tiefe_png), "schoenbild_png": schoenbild_png,
              "schoenbild_grund": None}
    if not befund["verkleinert"]:
        return befund
    ordner = Path(ordner)
    ordner.mkdir(parents=True, exist_ok=True)
    tiefe_klein = ordner / "tiefe.png"
    befund["weg"] = bildschreiben.skaliere_png(tiefe_png, tiefe_klein, ziel_b, ziel_h)["weg"]
    befund["tiefe_png"] = str(tiefe_klein)
    if schoenbild_png and Path(schoenbild_png).is_file():
        try:
            schoen_klein = ordner / "schoenbild.png"
            bildschreiben.skaliere_png(schoenbild_png, schoen_klein, ziel_b, ziel_h)
            befund["schoenbild_png"] = str(schoen_klein)
        except (bildschreiben.SchreibError, OSError, ValueError) as fehler:
            befund["schoenbild_png"] = None
            befund["schoenbild_grund"] = (f"Schoenbild nicht verkleinert und darum nicht "
                                          f"mitgegeben: {fehler}")
    return befund

#: Welche Richtungen gerendert werden, wenn die Szene ``cameras: "auto"`` sagt.
#:
#: **Drei** (Owner-Entscheid 23.08.2026), vorher eine. Wie viele automatische Standpunkte
#: ein Auftrag wert ist, ist eine Betriebs- und keine Programmentscheidung — jeder
#: Standpunkt ist ein GPU-Lauf —, und darum hat der Owner sie getroffen.
#:
#: **Warum genau diese drei.** HABS/NPS verlangt für die Dokumentation eines Bauwerks
#: vier Ansichten: Umgebung, Frontal und zwei Über-Eck auf **gegenüberliegenden**
#: Diagonalen. Die Umgebungsansicht ist hier weggelassen — sie zeigt ohne echtes Gelände
#: wenig, und Gelände haben wir nicht. Die übrigen drei sind:
#:
#: * ``s`` — frontal auf eine Fassade, Azimut 180°.
#: * ``sSE`` — über Eck, Azimut 145°: Süd- und Ostfassade.
#: * ``nNW`` — über Eck, Azimut 325°: Nord- und Westfassade.
#:
#: ``sSE`` und ``nNW`` liegen **exakt 180° auseinander** (nachgerechnet, nicht geschätzt).
#: Zusammen zeigen sie alle vier Fassaden; das ist die eigentliche Aussage der Norm — ein
#: Bauwerk wird nicht von einer Seite dokumentiert.
#:
#: **Für Messreihen bleibt die einzelne Richtung die saubere Wahl**, und der Aufrufer
#: kann es überschreiben: ``verarbeiter(auto_richtungen=("sSE",))``. Drei Standpunkte
#: verdreifachen die Renderzeit je Auftrag.
AUTO_RICHTUNGEN = ("s", "sSE", "nNW")

#: Nach wie vielen Sekunden ein Multipass-Lauf abgebrochen wird.
#:
#: **Uebernommen, nicht gemessen** — es ist der Vorgabewert der Naht, und ein Test haelt
#: ihn dagegen, damit die beiden nicht auseinanderlaufen.
#:
#: **Was am 26.08.2026 dazu gemessen wurde, und was es widerlegt.** In den
#: Durchreichungstabellen stand als Grund: «Eine Bestellung mit hohen Samples killt ihren
#: eigenen Lauf nach 900 s.» Nachgemessen (Blender 4.2.1 LTS, CPU, synthetischer Testbau):
#:
#:     400 px:   1 Sample 4,37 s ... 256 Samples 4,36 s   — FLACH innerhalb 1 %
#:     800 px:   4 Samples 7,58 s ... 256 Samples 11,54 s — 1,5x fuer 64x Samples
#:      32 Sa.: 400 px 4,37 s ... 1600 px 27,80 s         — 6,4x fuer 16x Pixel
#:
#: Die Pixel aendern sich bei jeder Samplezahl — die Zeit nicht. Der Aufwand steckt im
#: **festen Vorlauf**: Start, glb-Import, der zweite Durchgang fuer die Material-ID,
#: Schreiben. Nicht in den Samples.
#:
#: **Die Sorge war also auf die falsche Groesse gerichtet.** Wer einen Lauf sprengt, tut
#: es ueber die AUFLOESUNG oder ueber die Szene — und Szenenkomplexitaet drueckt kein
#: Bestellfeld aus. Ein Deckel, der aus der Bestellung gerechnet wird, schuetzte darum
#: gegen das Falsche.
#:
#: **Und was hier NICHT gemessen ist:** was davon auf einer GPU und an einem echten
#: Bauwerk uebrig bleibt. Genau diesen Fehler hat dieses Projekt schon einmal gemacht —
#: `seams.BLENDER_FRIST_MIN_S` haelt fest, dass eine CPU-Messung dort «ein Werkzeug zur
#: Zerstoerung jedes Laufs ueber 98 Sekunden» gewesen waere. Die Wiederholung auf der
#: HomeStation ist beauftragt (`auf-20260826-54`).
ZEITDECKEL_S = 900


def ausgabeort(auftrag: dict, out_wurzel=None) -> Path:
    """Wohin die Bilder DIESES Auftrags geschrieben werden — die eine Stelle, die es entscheidet.

    WARUM DAS EINE FUNKTION IST (01.09.2026): die Rechnung stand an zwei Orten — hier und in
    der Fortschrittswache von `tools/abholen.py`. Beide lasen `auftrag["ausgabe"]`, solange
    `out_wurzel` nicht gesetzt war, und fielen darum nicht auf. Mit gesetztem `out_wurzel`
    haette die Wache einen ANDEREN, leeren Ordner bewacht als den, in den geschrieben wird —
    und Stillstand gemeldet, waehrend die Bilder daneben entstanden. Ein Waechter, der am
    falschen Ort wacht, meldet Falsches; das ist teurer als keiner.

    WARUM ES DIESEN UMWEG UEBERHAUPT BRAUCHT: auf dem Brueckenweg ist der Ausgabeort von
    beiden Seiten zugenagelt. Die Bruecke erzwingt `scene["out"] = <job-dir>/out` serverseitig
    (Befund R4, gegen Schreibziel-Injektion), und `bruecke.py` rechnet ihn hier nochmals aus
    dem Auftragsordner. Beides ist richtig so. Nur liegt der Auftragsordner bei Port 8600
    bewusst unter `/tmp/kosmo-jobs` — und am 28.08.2026 lief die Kette zum ersten Mal ganz
    durch, schrieb drei Bilder, und der naechste Neustart nahm sie mit. Zehn Laeufe bis zum
    ersten Bild, und es ueberlebte den Tag nicht.

    `out_wurzel` biegt darum die AUSGABE um, nicht die Ablage der Auftraege. Der Ordnername
    bleibt der des Auftrags, damit die Zuordnung erhalten bleibt.
    """
    if out_wurzel:
        # Derselbe Ordnername wie der Auftrag — `verzeichnis` ist das Feld, das beide
        # Quellen setzen (`bruecke.lies_auftrag`, `eigene_quelle.lies_auftrag`).
        return Path(out_wurzel) / Path(auftrag["verzeichnis"]).name
    return Path(auftrag["ausgabe"])


def _raeume_des_modells(modell):
    """Die Raumliste eines Auftragsmodells — nur aus einer IFC, sonst ``None``.

    ``None`` heisst **nicht gelesen**, nicht «keine Räume»: Aus einer glb lässt sich kein
    Raumbegriff gewinnen (siehe ``kette._raeume_lesen``). Gelesen wird über denselben
    Weg wie in der Kette, also im ``.venv-ifc`` jenseits einer Prozessgrenze (Regel 1).
    """
    if modell is None or Path(modell).suffix.lower() != ".ifc":
        return None
    return _kette._raeume_lesen(modell)


def _innenaufgabe(wunsch: dict, raeume) -> dict:
    """Eine Innenbestellung → EINE Kameraaufgabe mit Standpunkt aus den Räumen.

    Dieselbe Rechnung wie ``kette._fuehre_multipass``: ``raumkamera.waehle`` sucht den
    Standpunkt, und **die Brennweite gehört zum Standpunkt** — ohne sie gilt drüben der
    Rückfall des Runners (50 mm), und bei 50 mm trug die Tiefenkarte eines Raums am
    09.09.2026 einen einzigen Wert (``docs/INNENANSICHT_2026-09-09.md``).

    Raises:
        AbholerError: kein Standpunkt — mit dem Grund aus ``raumkamera.waehle`` und dem
            des Raumlesers. Es wird **nicht** ersatzweise aussen gerendert: Wer innen
            bestellt und aussen bekommt, sieht es dem Bild nicht an.
    """
    wahl = _raumkamera.waehle(raeume, raum=wunsch.get("raum"),
                              art=wunsch.get("art") or _raumkamera.ART_FRONTAL)
    if not wahl["gefunden"]:
        leser = (raeume or {}).get("grund")
        raise AbholerError(
            "Innenansicht bestellt ('interior'), aber kein Standpunkt: " + wahl["grund"]
            + (f" Der Raumleser meldete: {leser}" if leser else "")
            + " Es wird NICHT ersatzweise aussen gerendert.")
    standpunkt = wahl["standpunkt"]
    return {
        # Ein fester Name und nicht der Raumname: Das Kuerzel wird zum Ordnernamen, und
        # ein Raumname aus einer fremden IFC kann Zeichen tragen, die dort nichts suchen.
        "kuerzel": "innen",
        "auge": list(standpunkt["auge"]),
        "blick_auf": list(standpunkt["blick_auf"]),
        "brennweite_mm": (standpunkt.get("sichtfeld") or {}).get("brennweite_mm"),
        # DER VERMERK, DASS ES EINE INNENANSICHT IST — bis zum 22.09.2026 stand er hier
        # und wurde nirgends gelesen (Durchsicht). `verarbeite` heftet ihn an das
        # Kameraurteil (`kosmo_szene.URTEIL_INNENANSICHT`), von dort erreicht er
        # urteil.json, befund.json und `verdict.reason`.
        "innenraum": {"raum": wahl["raum"], "art": standpunkt.get("art"),
                      "bestellt": wunsch.get("bestellt"),
                      "standpunkt": _kosmo_szene.INNEN_STANDPUNKT_AUS_RAEUMEN},
    }


def _mitgesandter_innenvermerk(szene: dict) -> dict | None:
    """Der Innenvermerk einer MITGESANDTEN Kamera — oder ``None``, wenn nicht innen bestellt.

    **Die reale Form** (Durchsicht 23.09.2026): KosmoOrbit sendet ``interior`` immer
    zusammen mit benannten Kameras (auf-91 V1). Bis zu diesem Tag entstand der Vermerk nur
    aus :func:`_innenaufgabe`, also bei KEINER echten Bestellung — ein Innenbild kam
    drueben ohne jeden Satz an und sah aus wie ein missratenes Aussenbild.

    Es wird **kein** Standpunkt gerechnet und kein Raum gelesen (auf-31 R6: kein zweiter
    Innenstandpunkt). ``raum`` und ``art`` bleiben ``None``: nicht von uns gewaehlt. Und
    weil die Bestellung nicht sagt, welche Kamera innen steht, traegt JEDE mitgesandte
    Kamera dieses Auftrags denselben Vermerk.
    """
    bestellt = szene.get("innen_bestellt")
    if not bestellt:
        return None
    return {"raum": None, "art": None, "bestellt": dict(bestellt),
            "standpunkt": _kosmo_szene.INNEN_STANDPUNKT_MITGESANDT}


#: Name der umgewandelten Geometrie im Arbeitsordner eines IFC-Auftrags — derselbe wie
#: in ``tools/homeworker.py`` und ``kette._fuehre_geometrie``.
DATEI_UMGEWANDELT = "modell.glb"


def _ist_ifc(modell) -> bool:
    """Ist das Auftragsmodell eine IFC? — an der Endung, die die Quelle gewaehlt hat.

    Auf dem Brueckenweg genuegt die Endung, weil sie nicht vom Absender stammt:
    ``bruecke.lies_auftrag`` nimmt ``model.ifc`` nur, wenn die Bestellung
    ``format: 'ifc'`` sagt, und hat die Datei vorher gesichtet (``einlass.sichte``).
    Die eigene Ablage reicht den Pfad der Bestellung durch; eine falsch benannte Datei
    faellt dort erst beim Umwandler auf (``seams.ifc_zu_glb`` sichtet selbst).
    """
    return modell is not None and Path(modell).suffix.lower() == ".ifc"


def _ifc_umwandeln(ifc, arbeitsordner) -> dict:
    """IFC → glb in den Arbeitsordner, dann das Tor — oder ein :class:`AbholerError` mit Satz.

    **Die Einbausperre vom 22.09.2026.** Die Bruecke legt eine IFC-Bestellung als
    ``model.ifc`` ab (auf-91 V3_V4). Der Abholer reichte das Modell bis dahin
    unverwandelt an ``seams.glb_zu_multipass`` — eine IFC dort, wo Blender eine glb
    erwartet. Gemessen ist das nie: Die Bruecke liess bis zum selben Tag keine IFC durch.

    Gemacht wie ``tools/homeworker.py`` (``seams.ifc_zu_glb`` nach ``modell.glb``, Status
    pruefen) und wie ``kette._fuehre_geometrie`` (danach ``torwaechter`` auf den Report).
    Die Umwandlung laeuft im ``.venv-ifc`` jenseits einer Prozessgrenze (Regel 1, LGPL):
    Dieses Modul startet ein Programm und liest JSON, es importiert kein ifcopenshell.

    **Was das Tor hier sperrt, und was nicht.** Gesperrt wird ``ablehnen_konversion``:
    kein Report, ``status`` nicht ``ok``, keine lesbare Huellbox — dann gibt es nichts zu
    rendern. **Gemeldet, nicht gesperrt** wird ``ablehnen_massstab``, und das weicht von
    ``kette._fuehre_geometrie`` bewusst ab: Auf diesem Weg misst ``_massstab_gemeldet``
    denselben Massstab je Kamera und bricht ausdruecklich NICHT ab, weil die
    Fehlalarmrate am Bestand ungemessen ist. Eine IFC-Bestellung strenger zu pruefen als
    dieselbe Geometrie als glb hiesse, dass das Format ueber die Sperre entscheidet.

    **Und was das Tor empfiehlt, wird gesagt, nicht verschluckt** (Durchsicht
    23.09.2026). Bis dahin fiel ``empfiehlt_neuzentrierung`` hier still weg. Befolgt wird
    die Empfehlung auf diesem Weg NICHT — niemand verschiebt die Geometrie, und mitgesandte
    Kameras stehen in den Koordinaten der IFC; eine verschobene glb liesse sie ins Leere
    schauen (Schluss, nicht gemessen). Sie steht darum als Warnung im Ergebnis.

    Returns:
        ``{quelle, glb_path, up_axis, torwaechter, n_elements, n_triangles, warnungen}``.
        ``torwaechter`` ist ``{entscheidung, begruendung, empfiehlt_neuzentrierung}`` —
        der Befund steht im Ergebnis, auch wenn er nichts sperrt. ``warnungen`` traegt
        den Satz zur Neuzentrierung, wenn das Tor sie empfiehlt, sonst ist sie leer.

    Raises:
        AbholerError: Umwandlung gescheitert, Tor sagt ``ablehnen_konversion``, oder die
            glb liegt danach nicht da. Es wird NICHT ersatzweise etwas anderes gerechnet.
    """
    from . import torwaechter as _tw

    ifc = Path(ifc)
    ziel = Path(arbeitsordner) / DATEI_UMGEWANDELT
    ziel.parent.mkdir(parents=True, exist_ok=True)
    try:
        bericht = _seams.ifc_zu_glb(str(ifc), str(ziel))
    except _seams.SeamError as fehler:
        raise AbholerError(
            f"Die IFC liess sich nicht in eine glb umwandeln: {fehler}\n"
            f"Ohne glb gibt es keine Tiefenkarte und kein Bild. Es wird nichts "
            f"ersatzweise gerechnet.") from fehler
    urteil = _tw.torwaechter(bericht)
    if urteil["entscheidung"] == _tw.ENTSCHEIDUNG_ABLEHNEN_KONVERSION:
        raise AbholerError(
            f"Die Umwandlung IFC → glb traegt nicht: {urteil['begruendung']} Es wird "
            f"nichts ersatzweise gerechnet.")
    glb = Path(bericht.get("glb_path") or ziel)
    if not glb.is_file():
        raise AbholerError(
            f"Die Umwandlung IFC → glb meldete Erfolg, aber {glb.name} liegt nicht im "
            f"Arbeitsordner. Gerechnet wird nur auf einer Datei, die da ist.")
    neuzentrierung = bool(urteil.get("empfiehlt_neuzentrierung"))
    warnungen = []
    if neuzentrierung:
        warnungen.append(
            "Das Tor empfiehlt, die Geometrie neu zu zentrieren: Sie liegt so weit vom "
            "Ursprung, dass glTF (float32) Kanten um Zentimeter bis Dezimeter springen "
            "laesst. Dieser Weg zentriert NICHT neu — gerechnet wird auf der Geometrie, "
            "wie sie kam. Kanten in Tiefenkarte und Bild koennen darum unscharf sein. "
            + " ".join((urteil.get("georeferenz") or {}).get("warnungen") or ()))
    # WAS DER DATEI FEHLT (auf-20261022-331): kein Dach, Fenster nur als Loecher, keine
    # Farben — der Runner zaehlt es, und es soll vor dem Bild dastehen, nicht erst darin.
    warnungen.extend(str(w) for w in (bericht.get("warnungen") or ()) if w)
    return {
        "quelle": ifc.name,
        "glb_path": str(glb),
        # Die Achse der UMGEWANDELTEN Datei, gemeldet vom Runner (er dreht Z-up nach Y-up
        # und sagt es). Fehlt sie, gilt die Annahme des Abholers, und `hochachse` sagt es.
        "up_axis": bericht.get("up_axis"),
        "torwaechter": {"entscheidung": urteil["entscheidung"],
                        "begruendung": urteil["begruendung"],
                        "empfiehlt_neuzentrierung": neuzentrierung},
        "n_elements": bericht.get("n_elements"),
        "n_triangles": bericht.get("n_triangles"),
        "warnungen": warnungen,
    }


def _modellstand_ohne_modell() -> dict:
    """Der Modellstand einer Variante ohne Modelldatei — ungeprueft, mit Grund (21.10.2026).

    Gilt nur, bis die Grundlage gelesen ist: Hat sie den Modellstand ihres Laufs abgelegt,
    ersetzt dieser hier (``verarbeiter``).
    """
    from . import modellstand as _ms

    return {"geprueft": False, "urteil": _ms.UNGEPRUEFT, "maengel": [], "warnungen": [],
            "quelle": None,
            "grund": ("Variante ohne Modelldatei (vis.grundlage): Es gibt keinen glb-Kopf "
                      "zu lesen, und die Grundlage hat keinen Modellstand abgelegt. NICHT "
                      "GEPRUEFT.")}


def _modellstand_nicht_umgewandelt() -> dict:
    """Der Modellstand einer ABBESTELLTEN IFC-Bestellung — ungeprueft, mit Grund.

    Der Modellstand liest den glb-Kopf. Eine abbestellte IFC wird nicht umgewandelt (das
    kostete einen Unterprozess fuer nichts), also gibt es keinen Kopf zu lesen — und
    *nicht gelesen* ist nicht *traegt*.
    """
    from . import modellstand as _ms

    return {"geprueft": False, "urteil": _ms.UNGEPRUEFT, "maengel": [], "warnungen": [],
            "quelle": None,
            "grund": ("Abbestellt: Die IFC wurde nicht in eine glb umgewandelt, und der "
                      "Modellstand liest nur den glb-Kopf. NICHT GEPRUEFT.")}


#: Der Satz, wenn ein Auftrag eine Skizze bestellt, aber keine Mappe vermerkt hat.
SATZ_SKIZZE_OHNE_MAPPE = (
    "Eine Skizze ist bestellt, aber zu diesem Auftrag ist keine Mappe vermerkt. Rechnen lässt "
    "sie sich nur in der Mappe, in der sie liegt — bestellt über die Knotenansicht von Visbox "
    "(knotenweg.lege_an vermerkt die Mappe dort). Ein Auftrag über einen anderen Weg (Brücke, "
    "MCP) kann keine Skizze tragen.")

#: Wie das eine Bild eines Skizzenlaufs in ``qa_je_kamera`` heisst — es ist keine der drei
#: Richtungen des Abholers, sondern der Standpunkt der Mappe.
KAMERA_SKIZZE = "skizze"


def skizzenlauf(auftrag: dict, *, rechne=None, ausfuehrer=None) -> dict:
    """Einen Auftrag mit ``skizze`` rechnen — **derselbe Weg wie die Seite**, nicht ein zweiter.

    **Owner-Entscheid 96 (15.10.2026):** In der Knotenansicht soll die Skizze vom iPad das Bild
    führen, wie «aus Skizze rechnen» auf der alten Visbox-Seite. Darum ruft dieser Weg
    :func:`aiimaging.arbeitsgang.rechne_skizze` in der Mappe, in der die Skizze liegt
    (:func:`aiimaging.knotenweg.mappe_des_auftrags`) — mit allem, was dort gilt: die Skizze auf
    ihrer Unterlage als Eingangsbild, die Anweisung (sonst die Bemerkung der Skizze), der
    Standpunkt und die Einstellungen der Mappe, die Prüfung «nicht anwendbar», der Satz «SKIZZE
    NICHT ANGEKOMMEN» auf einem Modell, das kein Ausgangsbild annimmt, und danach die Skizze
    «gerechnet» mit ihrem Bild. Das Bild steht damit AUCH in der Mappe, wie auf der Seite.

    **Von der Bestellung gelten:** die Skizze, die Anweisung und das Bildwerkzeug
    (``vis.backbone``). Auflösung, Samples, Treue und Sonne der Bestellung gelten für einen
    Skizzenlauf nicht — es gelten die Einstellungen der Mappe, wie auf der Seite; die
    Kameraliste weist :func:`aiimaging.kosmo_szene.skizze_unvertraeglich` schon vorher ab.
    Das mitgeschickte Modell wird nicht gerechnet: Gerechnet wird das Modell der Mappe (in
    Visbox liefert die Knotenansicht genau dieses, ``/knoten/modell.glb``).

    **Lizenz:** Ein Modell mit offener Lizenz (E128, ``qwen-image-2.1``) bleibt markiert — die
    Marke kommt aus dem Lauf (``parameter.lizenz_offen``) über :func:`_engine_aus` bis ins
    Ergebnis (``engine_license_open: true``). Nie Vorgabe: gerechnet wird, was bestellt ist.

    Raises:
        AbholerError: keine Mappe vermerkt; die Bibliothek weist die Skizze ab (verworfen,
            Datei oder Unterlage fehlt, keine Anweisung — mit ihrem Satz); kein Bild entstanden.
    """
    from . import arbeitsgang, knotenweg  # spaet: nur ein Skizzenlauf braucht sie

    rechne = rechne or arbeitsgang.rechne_skizze
    szene = auftrag["szene"]
    skizze = szene.get("skizze") or {}
    mappe = knotenweg.mappe_des_auftrags(auftrag["verzeichnis"])
    if mappe is None:
        raise AbholerError(SATZ_SKIZZE_OHNE_MAPPE)
    # AUFLAGE A1 (Integrator, 15.10.2026), HIER NOCHMALS — unabhaengig von Vertrag und Server: Der
    # Name ist ein relativer Pfad in der Mappe, und er steht dort als Skizze. Ein Auftrag kann
    # auch von Hand in die Ablage gelegt sein; was hier gerechnet wird, prueft dieser Weg selbst.
    _pruefe_skizzenname(mappe, skizze.get("name"))
    beginn = time.monotonic()
    kettenargumente = {"backbone": szene["backbone"]} if szene.get("backbone") else {}
    try:
        aus = rechne(mappe, skizze.get("name"), anweisung=skizze.get("anweisung"),
                     ausfuehrer=ausfuehrer, **kettenargumente)
    except arbeitsgang.ArbeitsgangError as fehler:
        raise AbholerError(f"Die Skizze liess sich nicht rechnen: {fehler}") from fehler

    lauf = aus.get("lauf") or {}
    knoten = lauf.get("knoten") or {}
    vorsatz = arbeitsgang.SKIZZEN_VORSATZ
    nach = (knoten.get(f"{vorsatz}-{_kette.KNOTEN_NACHRENDER}") or {}).get("ausgaben") or {}
    bild = nach.get("bild_png")
    if aus.get("abgebrochen") or not bild:
        raise AbholerError(
            "Aus der Skizze entstand kein Bild"
            + (" — der Lauf wurde angehalten." if aus.get("abgebrochen") else
               f": {lauf.get('error') or nach.get('error') or lauf.get('status') or 'ohne Angabe'}"))

    # WORAUF SIE GESETZT WURDE und von wo — aus dem Eintrag, den die Bibliothek in die Mappe
    # schrieb (dieselben Saetze wie am Bild auf der Seite).
    eintrag = next((b for b in (aus.get("projekt") or {}).get("bilder") or ()
                    if isinstance(b, dict) and (aus.get("bilder") or [None])[-1] == b.get("bild")),
                   {})
    herkunft = eintrag.get("herkunft") or {}
    vorgabe = aus.get("standpunkt_vorgabe")
    # VON WO (Entscheid 96b): vom Bild unter der Skizze, sonst von der Mappe — mit Grund.
    woher = aus.get("standpunkt_skizze") or {}
    standpunkt_saetze = [s for s in (woher.get("zeile"),
                                     (vorgabe or {}).get("satz") if vorgabe else None) if s]
    vermerk = {
        "name": skizze.get("name"),
        "anweisung": herkunft.get("anweisung") or skizze.get("anweisung"),
        "anweisung_original": skizze.get("anweisung_original"),
        "anweisung_aus": "bestellung" if skizze.get("anweisung") else "bemerkung",
        "unterlage": herkunft.get("unterlage"),
        "standpunkt": (" ".join(standpunkt_saetze) if standpunkt_saetze else
                       "Standpunkt aus den Einstellungen der Mappe, wie auf der Seite."),
        "standpunkt_von": woher.get("von"),
        "hinweise": [str(h) for h in nach.get("hinweise") or ()],
        "bild_in_der_mappe": eintrag.get("bild"),
    }
    qa = (knoten.get(f"{vorsatz}-{_kette.KNOTEN_QA}") or {}).get("ausgaben")
    if isinstance(qa, dict):
        urteil = {k: v for k, v in qa.items() if k != "bild_png"}
    else:
        urteil = {"status": "nicht_gemessen", "bestanden": None, "score": None,
                  "grund": "Die Pruefung ist in dieser Mappe abgeschaltet (Einstellung qa)."}
    urteil = dict(urteil, bild_png=bild, **{_kosmo_szene.URTEIL_SKIZZE: vermerk})
    return {
        "bilder": [bild],
        "geometrie_urteil": urteil,
        "stil_urteil": None,
        # EIN Bild, EINE «Kamera»: der Standpunkt der Mappe. `gemessen: False` — ein Bild aus
        # einer Skizze wird nicht gegen das Modell gemessen (siehe `_qa_je_kamera_eintraege`).
        "kameras": [{"kamera": KAMERA_SKIZZE, "bild_png": bild, "gemessen": False}],
        "zeiten": {"gesamt": round(time.monotonic() - beginn, 3)},
        "engine": _engine_aus(nach),
        "skizze": vermerk,
        "modellstand": aus.get("modell_stand"),
    }


def _pruefe_skizzenname(mappe, name) -> None:
    """A1 auf der Bildseite: der Name ist ein relativer Pfad, und er steht in der Mappe als
    Skizze (nicht verworfen). Wirft :class:`AbholerError` mit Satz, sonst nichts."""
    from . import knotenweg, projekt  # spaet: nur ein Skizzenlauf braucht sie

    mangel = _kosmo_szene.skizzenname_mangel(name)
    if mangel is not None:
        raise AbholerError(f"Die Skizze wird nicht gerechnet: {mangel}")
    try:
        p = projekt.oeffne(mappe)["projekt"]
    except projekt.ProjektError as fehler:
        raise AbholerError(f"Die Mappe der Skizze liess sich nicht oeffnen: {fehler}") from fehler
    if name not in {s["name"] for s in knotenweg.skizzen_der_mappe(p, hoechstens=10**6)}:
        verworfen = any(isinstance(e, dict) and e.get("skizze") == name
                        for e in p.get("skizzen") or ())
        raise AbholerError(
            f"Die Skizze {name!r} ist verworfen — bewusst liegengelassen; gerechnet wird sie nicht."
            if verworfen else
            f"Die Skizze {name!r} steht nicht als Skizze in der Mappe. Gerechnet wird nur, was "
            f"dort steht.")


# --------------------------------------------------------------------------------------
# Fortschritt, Vorschau und Teilbild (20.10.2026)
# --------------------------------------------------------------------------------------
#
# Ein Lauf mit drei Kameras dauert Minuten, und bis zu diesem Tag sah man davon nur
# «läuft». Abgemacht ist seither ein Feld ``progress`` am Auftrag (siehe
# :data:`aiimaging.bruecke.FELD_FORTSCHRITT`) und ein ``teilbild`` für den Abbruch.

#: Wie ein Kameradurchgang auf seine drei Phasen fällt — **eine Setzung, keine Messung.**
#:
#: Grundlage ist die Grössenordnung, die in diesem Modul an anderer Stelle steht: rund
#: 40 s Blender je Kamera bei Vertragsvorgaben, rund 25 s Diffusion je Startwert bei drei
#: Startwerten, dazu die Messung. Daraus ergäbe sich eher 0,3 / 0,6 / 0,1; gewählt ist
#: 0,2 / 0,7 / 0,1, weil Blender mit Zwischenspeicher oder Grundlage oft entfällt und das
#: Bildmodell der Teil ist, der wirklich wartet. Die Zahl dient nur der Anzeige — die
#: Restzeit (``rest_s``) kommt **nicht** aus ihr, sondern aus den gemessenen Dauern der
#: fertigen Kameras desselben Laufs.
FORTSCHRITT_ANTEILE = (("blender", 0.2), ("bildmodell", 0.7), ("pruefung", 0.1))

#: Der flache Name der Vorschau einer Kamera — dieselbe Form wie die Ebenen
#: (``<kamera>__<art>.png``, :func:`ebenen_dieser_kamera`).
VORSCHAU_ART = "vorschau"
TEILBILD_ART = "teilbild"

#: Die Phase am Auftrag, nachdem ein Abbruch gegriffen hat (Geräteprobe 20.10.2026). Ihr
#: Vertrag (``RenderJobProgress.phase``, render-result.ts) nimmt jede Zeichenkette; unsere
#: Prüfung (``bruecke.FORTSCHRITT_PHASEN``) kennt sie seither.
PHASE_ABGEBROCHEN = "abgebrochen"

#: Wie der Satz eines Abbruchs den Schritt nennt, der als nächstes gekommen wäre.
SCHRITT_NAMEN = {"blender": "Blender", "bildmodell": "dem Bildmodell",
                 "pruefung": "der Pruefung"}


def _quelle_des_ordners(verzeichnis):
    """Welche Ablage dieser Auftragsordner ist — erkannt an seinem Laufzettel.

    Der Verarbeiter bekommt nur den Auftrag, nicht die Quelle (``hole_einen`` reicht sie
    nicht hinein, und die Signatur ``verarbeite(auftrag)`` ist Vertrag). Beide Ablagen
    legen ihren Laufzettel unter einem eigenen Namen ab, darum genügt der Blick auf die
    Datei. ``None``: keiner von beiden — dann wird nichts gemeldet.
    """
    from . import eigene_quelle
    ordner = Path(verzeichnis)
    if (ordner / bruecke.DATEI_LAUFZETTEL).is_file():
        return bruecke
    if eigene_quelle.laufzettel_pfad(ordner).is_file():
        return eigene_quelle
    return None


def melde_fortschritt(verzeichnis, progress: dict, *, dateien=None) -> dict | None:
    """Den Fortschritt an den Auftrag schreiben — über die Quelle, zu der der Ordner gehört.

    ``dateien`` (``{flacher Name: Pfad}``) werden **vorher** in den Auftragsordner gelegt:
    Ein Fortschritt, der eine Vorschau nennt, die noch nicht dort liegt, liesse die
    Oberfläche ein Bild holen, das es nicht gibt — dieselbe Reihenfolge wie bei
    :func:`aiimaging.bruecke.schreibe_ergebnis`.

    Das ist die Vorgabe für ``verarbeiter(_melde=…)``. Wirft sie, fängt der Verarbeiter das
    ab: Ein Fortschritt, der sich nicht schreiben lässt, ist kein Grund, ein Bild zu verlieren.
    """
    quelle = _quelle_des_ordners(verzeichnis)
    if quelle is None or not hasattr(quelle, "setze_fortschritt"):
        return None
    for name, pfad in (dateien or {}).items():
        quelle.artefakt_bereitstellen(verzeichnis, pfad, name)
    return quelle.setze_fortschritt(verzeichnis, progress)


def steht_abgebrochen(verzeichnis) -> bool:
    """Steht der Auftrag **jetzt** auf ``cancelled``? Unlesbar heisst: nein.

    Unlesbar ist kein Abbruch: Ein Laufzettel, der gerade geschrieben wird, soll einen
    Lauf nicht beenden. Der nächste Blick kommt nach der nächsten Phase.
    """
    quelle = _quelle_des_ordners(verzeichnis)
    if quelle is None or not hasattr(quelle, "lies_status"):
        return False
    try:
        return quelle.lies_status(verzeichnis) == bruecke.STATUS_CANCELLED
    except Exception:                      # noqa: BLE001 — siehe Docstring
        return False


class _Fortschritt:
    """Führt Buch über den Lauf und meldet ihn — mit dem Blick auf einen Abbruch dabei.

    **Was gemeldet wird.** Je Kamera ``blender`` vor dem Multipass (oder dem Griff in die
    Grundlage), ``bildmodell`` vor dem KI-Schritt, ``pruefung`` nach dem letzten Startwert;
    ``pct`` über alle Kameras nach :data:`FORTSCHRITT_ANTEILE`, nie rückwärts. Am Ende
    ``pruefung`` mit ``pct`` 1.0 — das bleibt am Auftrag stehen, auch bei ``done``. Die
    Messung je Startwert läuft in ``_bester_seed`` mit dem Bild verzahnt und zählt darum
    zum ``bildmodell``; ``pruefung`` ist, was danach kommt (Nullprobe, Urteil).

    **Die Restzeit** ist ``None``, bis eine Kamera **gerechnet** fertig ist; danach das
    Mittel der gerechneten Kameras mal die verbleibenden, abzüglich des schon gelaufenen
    Teils der aktuellen, nie unter 0, ganze Sekunden. Übersprungene Kameras (Blickfeld,
    Rahmung, Zwilling) zählen nicht ins Mittel — sie dauern Sekundenbruchteile und
    liessen die Schätzung um die Hälfte fallen.

    **Der Abbruch** wird zwischen den Phasen nachgesehen (ein Blick in den Laufzettel).
    Ein laufender Blender- oder Bildmodellschritt wird **nicht** unterbrochen; der
    Abbruch greift beim nächsten Übergang.

    Jeder Schreibfehler wird abgefangen und protokolliert, nie weitergereicht.
    """

    def __init__(self, ordner, n: int, *, melde, abgebrochen, uhr=time.monotonic):
        self.ordner = Path(ordner)
        self.n = max(1, int(n))
        self.melde = melde
        self.abgebrochen = abgebrochen
        self.uhr = uhr
        self.i = 0
        self.beginn = None
        self.dauern: list[float] = []
        self.pct = 0.0
        self.phase_jetzt = FORTSCHRITT_ANTEILE[0][0]
        self.vorschau = None
        # JE BILD SEINE KAMERA (Geraeteprobe der HomeStation, 20.10.2026): Bis dahin gab es
        # EIN `kamera_des_bilds`, das `vorschau_da` der zweiten Kamera schon umsetzte,
        # waehrend das KI-Bild noch von der ersten war — `Schraeg__teilbild.png` war
        # bytegleich mit dem KI-Bild von «Vorne».
        self.cycles_bild = None
        self.cycles_kamera = None
        self.ki_bild = None
        self.ki_kamera = None
        self.fehler: list[str] = []

    # --- Buchführung -----------------------------------------------------------------
    def _anteil_vor(self, phase: str) -> float:
        summe = 0.0
        for name, anteil in FORTSCHRITT_ANTEILE:
            if name == phase:
                return summe
            summe += anteil
        return summe

    def rest_s(self):
        if not self.dauern:
            return None
        mittel = sum(self.dauern) / len(self.dauern)
        offen = self.n - (self.i - 1) if self.beginn is not None else self.n - self.i
        gelaufen = (self.uhr() - self.beginn) if self.beginn is not None else 0.0
        return max(0, int(round(mittel * offen - gelaufen)))

    def _sende(self, dateien=None) -> None:
        progress = {"phase": self.phase_jetzt, "pct": round(self.pct, 4),
                    "kamera_i": max(1, min(self.i, self.n)), "kamera_n": self.n,
                    "rest_s": self.rest_s()}
        if self.vorschau:
            progress["vorschau"] = self.vorschau
        try:
            self.melde(self.ordner, progress, dateien=dateien)
        except Exception as fehler:        # noqa: BLE001 — siehe Klassendoku
            self.fehler.append(f"{type(fehler).__name__}: {fehler}")
            import logging
            logging.getLogger(__name__).warning(
                "Fortschritt nicht geschrieben (der Lauf geht weiter): %s", self.fehler[-1])

    def _setze(self, phase: str, pct: float) -> None:
        self.phase_jetzt = phase
        self.pct = min(1.0, max(self.pct, pct))

    def teilbild(self) -> tuple:
        """``(pfad, kamera)`` des Teilbilds: das letzte KI-Bild, sonst das Cycles-Bild —
        und die Kamera DIESES Bilds, nicht die, bei der der Lauf gerade stand."""
        if self.ki_bild:
            return self.ki_bild, self.ki_kamera
        return self.cycles_bild, self.cycles_kamera

    def pruefe_abbruch(self, vor: str | None = None) -> None:
        """Steht der Auftrag auf ``cancelled``? Dann den Endstand melden und aufhören.

        ``vor`` ist der Schritt, der als NÄCHSTES käme — er steht im Satz (Geräteprobe
        20.10.2026: «Phase blender» hiess es auch, wenn Blender fertig war und das
        Bildmodell anstand). Der Endstand am Auftrag ist Phase :data:`PHASE_ABGEBROCHEN`
        mit dem erreichten ``pct``, ohne Restzeit — vorher blieb dort «blender, 0.6» stehen.
        """
        try:
            weg = bool(self.abgebrochen(self.ordner))
        except Exception:                  # noqa: BLE001 — unlesbar ist kein Abbruch
            weg = False
        if weg:
            schritt = SCHRITT_NAMEN.get(vor or "", None)
            satz = (f"Abgebrochen bei Kamera {max(1, min(self.i, self.n))} von {self.n}, "
                    f"vor {schritt}." if schritt else
                    f"Abgebrochen nach Kamera {self.i} von {self.n}.")
            self.phase_jetzt = PHASE_ABGEBROCHEN
            self.dauern = []               # keine Restzeit mehr
            self._sende()
            pfad, kamera = self.teilbild()
            raise AuftragAbgebrochen(satz, teilbild=pfad, kamera=kamera)

    # --- die Übergänge ---------------------------------------------------------------
    def kamera(self, i: int) -> None:
        self.i, self.beginn = i, self.uhr()
        self.pruefe_abbruch("blender")
        self._setze("blender", (i - 1) / self.n)
        self._sende()

    def vorschau_da(self, kuerzel, beauty_png) -> None:
        if not beauty_png or not Path(beauty_png).is_file():
            return
        self.cycles_bild, self.cycles_kamera = str(beauty_png), str(kuerzel)
        name = f"{kuerzel}__{VORSCHAU_ART}.png"
        if not bruecke._ist_flacher_name(name):
            return
        vorher = self.vorschau
        self.vorschau = name
        self._setze("blender", (self.i - 1 + self._anteil_vor("bildmodell")) / self.n)
        fehler_vorher = len(self.fehler)
        self._sende(dateien={name: str(beauty_png)})
        if len(self.fehler) > fehler_vorher:
            # Nicht bereitgestellt — dann nennt der Fortschritt auch keine neue Vorschau.
            self.vorschau = vorher

    def phase(self, phase: str) -> None:
        self.pruefe_abbruch(phase)
        self._setze(phase, (self.i - 1 + self._anteil_vor(phase)) / self.n)
        self._sende()

    def ki_bild_da(self, kuerzel, bild_png) -> None:
        if bild_png and Path(bild_png).is_file():
            self.ki_bild, self.ki_kamera = str(bild_png), str(kuerzel)

    def kamera_fertig(self, *, gerechnet: bool) -> None:
        if gerechnet and self.beginn is not None:
            self.dauern.append(self.uhr() - self.beginn)
        self.beginn = None
        self._setze(self.phase_jetzt, self.i / self.n)

    def ende(self) -> None:
        self.pruefe_abbruch(None)
        self._setze("pruefung", 1.0)
        self.i = self.n
        self._sende()


def verarbeiter(*, out_wurzel=None, auto_richtungen=AUTO_RICHTUNGEN,
                up_axis: str = ANGENOMMENE_HOCHACHSE, schwelle: float | None = None,
                stillstand_frist_s: float | None = None, stil: str | None = None,
                nullprobe: bool = True, seeds=VORGABE_SEEDS,
                kamera_modus: str = _kameras_modul.MODUS_SHIFT,
                brennweite_mm: float | None = None,
                gelaende_z: float | None = None,
                gelaende_erwartet: bool = True,
                rahmung_pruefen: bool = True,
                deckungsgrad: float | None = None,
                augenhoehe: float | None = None,
                bias_grad: float | None = None,
                zwischenspeicher=None,
                zeitdeckel_s: int | None = None,
                kamera_huellbox=None,
                vorschau_lange_seite: int | None = None,
                _multipass=None, _rendere=None, _qa=None, _soll=None,
                _belichtung=None, _render_modell=None, _tiefen_modell=None,
                _raeume=None, _pipeline_lage=None, _kontext_vorbereiten=None,
                _skizzen_ausfuehrer=None, _rechne_skizze=None,
                _melde=None, _abgebrochen=None, _uhr=None):
    """Baut das ``verarbeite``, das :func:`hole_einen` durch unsere Kette schickt.

    Je Kamera ein Durchgang: **Multipass → Render → Geometrie-QA**. Ein Auftrag mit drei
    Kameras — wie der echte vom 19.08.2026 — ergibt drei Bilder und drei Urteile.

    Warum je Kamera ein eigener Multipass: Die Tiefenkarte ist der Massstab, gegen den das
    erzeugte Bild gemessen wird, und sie gilt nur für **den einen** Blickwinkel, aus dem
    sie entstand. Ein Bild gegen die Tiefenkarte einer anderen Kamera zu messen ergäbe
    eine Zahl, und die Zahl wäre Unsinn.

    ``nullprobe`` misst je Kamera, was ein Bild **ohne jede Geometrie** auf derselben
    Soll-Karte erreicht — weisses Rauschen, eine graue Fläche, ein Querverlauf. Das kostet
    **keinen Renderlauf**, nur je einen Durchgang des Tiefenschätzers, und es ist der
    Unterschied zwischen einer Zahl und einer eingeordneten Zahl.

    **Warum voreingestellt:** Am 20.08.2026 gemessen (`auf-20260820-21`) erreichte weisses
    Rauschen auf einer Szene mit viel Boden **0.7217** und bestand damit das Gate von 0.65
    — mehr als jeder echte Lauf derselben Messung. Ein Score ohne Anker ist auf einer
    solchen Szene nicht einzuordnen, und ein grünes Abzeichen wäre eine Behauptung.

    ``stil`` schaltet die **Belichtungsprüfung** dazu — sie braucht einen Stil, weil eine
    Belichtungsschwelle keine Eigenschaft guter Belichtung ist, sondern eines Stils (siehe
    :mod:`aiimaging.belichtung`). Ohne Angabe wird sie **nicht** gefahren, und das
    Ergebnis sagt das; ein Stil ohne Rahmen ebenso. Ein untergeschobener Rahmen wäre ein
    Urteil über einen Stil anhand der Zahlen eines anderen.

    Sie hält **nichts** auf: Ein Bild, das die Belichtung reisst, ist ein Befund und kein
    Fehler. Die Geometrie entscheidet über `passed`, die Belichtung erklärt.

    **Die Stil-QA läuft hier nicht**, und das ist kein Versehen: Sie braucht ein
    Referenzset, das uns gehört. Die bisherigen Referenzen sind fremde Bildschirmfotos und
    taugen als Anschauung, nicht als Messgrundlage — eine Einbettung ist eine Ableitung
    des Bildes. ``kosmo_szene.als_ergebnis`` schreibt bei fehlendem Stil-Urteil
    ausdrücklich „ungeprüft" statt „durchgefallen", die Lücke ist also sichtbar und nicht
    stillschweigend.

    Alle vier Schwergewichte sind injizierbar (``_multipass``, ``_rendere``, ``_qa``,
    ``_soll``). Ohne das wäre dieser Weg nur auf einem Rechner mit Blender, GPU und 20 GB
    Gewichten prüfbar — also faktisch gar nicht.

    **Fortschritt** (20.10.2026): Während des Laufs steht am Auftrag, in welcher Phase
    welche Kamera ist, wie weit der Lauf ist, die jüngste Cycles-Vorschau und eine Restzeit
    — siehe :class:`_Fortschritt`. ``_melde`` (Vorgabe :func:`melde_fortschritt`) und
    ``_abgebrochen`` (Vorgabe :func:`steht_abgebrochen`) sind die Nähte dafür, ``_uhr`` die
    Uhr der Restzeit. Steht der Auftrag zwischen zwei Phasen auf ``cancelled``, endet der
    Lauf mit :class:`AuftragAbgebrochen`.

    **Güte** (Owner-Entscheid 104, 20.10.2026): Trägt die Bestellung ``vis.guete:
    "vorschau"``, rechnet jede Kamera mit :data:`aiimaging.backbone.VORSCHAU_BACKBONE`
    (gleich, was ``vis.backbone`` nennt), mit dessen ``vorschau_schritte``, mit genau
    einem Startwert (``vis.seed``, sonst der der Grundlage, sonst 0) und auf verkleinerten
    Steuerbildern (:func:`vorschau_steuerbilder`, lange Seite ``vorschau_lange_seite``,
    Vorgabe :data:`aiimaging.backbone.VORSCHAU_LANGE_SEITE`). Das KI-Bild wird danach auf
    die Grösse der Grundlage gebracht und **geprüft wie jedes Bild** (104a). Die Grundlage
    selbst bleibt unverändert. ``'voll'`` oder kein Feld: alles wie zuvor.

    Returns:
        Ein ``verarbeite(auftrag) -> {bilder, geometrie_urteil, zeiten, kameras}``, wie
        :func:`hole_einen` es erwartet. ``geometrie_urteil`` ist das Urteil der
        **schlechtesten** Kamera: Ein Auftrag ist so gut wie sein schwächstes Bild, und
        einen Mittelwert über Urteile zu bilden hiesse, ein durchgefallenes Bild hinter
        zwei bestandenen verschwinden zu lassen.
    """
    from . import belichtung as _bel
    from . import bildlesen, bildschreiben, geometrie_qa, render, seams, tiefenschaetzer

    multipass = _multipass or seams.glb_zu_multipass
    # Die Splat-Bruecke (Entscheid 79, 13.10.2026) — als Naht, damit der Netz-Weg ohne GPU
    # und ohne `.venv-splat` pruefbar ist.
    kontext_vorbereiten = _kontext_vorbereiten or seams.kontext_vorbereiten
    rendern = _rendere or render.rendere
    messen = _qa or tiefenschaetzer.qa_gegen_soll
    soll_lesen = _soll or bildlesen.tiefen_aus_report
    belichtung_pruefen = _belichtung or _bel.pruefe_bild
    # Die Raeume fuer eine Innenansicht. Eine Testnaht wie `_multipass`: Der echte Leser
    # startet einen Unterprozess im `.venv-ifc` (Regel 1, Prozessgrenze).
    raeume_lesen = _raeume or _raeume_des_modells
    grenze = geometrie_qa.SCHWELLE_GEOMETRIE if schwelle is None else schwelle
    rahmen = _bel.rahmen_fuer(stil) if stil else None
    # Ob das bestellte Bildmodell in DIESER diffusers rechenbar ist (auf-20261001-230). Nur
    # gefragt, wenn auch mit ihr gerechnet wird: Ein hereingereichtes `_rendere` ist nicht
    # diffusers, und deren Klassenliste sagte ueber es nichts. `_pipeline_lage` ist die
    # Naht fuer Proben mit einem Ersatzmodul.
    pipeline_lage = (_pipeline_lage if _pipeline_lage is not None
                     else (render.pipeline_lage if _rendere is None else None))

    melde = _melde or melde_fortschritt
    abgebrochen = _abgebrochen or steht_abgebrochen
    uhr = _uhr or time.monotonic

    def _verarbeite_einen(auftrag: dict) -> dict:
        szene = auftrag["szene"]
        ordner = Path(auftrag["verzeichnis"])
        # DIE SKIZZE FUEHRT DAS BILD (Owner-Entscheid 96, 15.10.2026): ein eigener Weg, aber
        # nicht nachgebaut — derselbe wie «aus Skizze rechnen» auf der Seite. Siehe
        # `skizzenlauf`. `_skizzen_ausfuehrer`/`_rechne_skizze` sind die Naehte fuer Proben.
        if szene.get("skizze") is not None:
            return skizzenlauf(auftrag, rechne=_rechne_skizze, ausfuehrer=_skizzen_ausfuehrer)
        # DER GELAENDEBEFUND DER SZENE SCHLAEGT DEN SCHALTER DES PROZESSES (22.09.2026).
        #
        # `gelaende_erwartet` hier oben ist `tools/abholen.py --kein-gelaende`: eine
        # Aussage ueber EIN Gebaeude als Dauereinstellung fuer alle Auftraege (so
        # begruendet in auf-20260901-67). Traegt die Bestellung `gelaende: true|false`,
        # gilt diese. `None` heisst nicht angefasst — dann bleibt es beim Schalter.
        gelaende_der_szene = szene.get("gelaende_erwartet")
        if gelaende_der_szene is None:
            gelaende_der_szene = gelaende_erwartet
        # DIE UMGEBUNG (Owner-Entscheid 76, 08.10.2026): `RenderScene.context`, gelesen
        # in `kosmo_szene.kontext_aus_szene`. Auf dem Produktweg haelt ein Mangel den
        # Auftrag schon vorher an (`auftrag["maengel"]`); hier steht die Abweisung fuer
        # eine von Hand gebaute Szene — ohne Umgebung zu rechnen saehe aus wie geliefert.
        kontext = szene.get("kontext")
        # EINE PUNKTWOLKE OHNE SPLAT-FELDER (Geraeteprobe R59) bricht nichts ab:
        # Auf dem Produktweg nimmt sie schon `lies_szene` heraus; hier die zweite Linie fuer
        # eine Szene, die von Hand oder auf altem Stand gebaut ist. Weggelassen mit Satz.
        if kontext is not None and kontext.get("ply"):
            weggelassen = _punktwolke_statt_splat(kontext)
            if weggelassen is not None:
                szene["kontext_weggelassen"] = weggelassen
                szene["kontext"] = kontext = None
        if kontext is not None and (kontext.get("maengel") or not kontext.get("ply")):
            raise AbholerError(
                "Umgebung (Splat) bestellt, aber nicht verwendbar: "
                + ("; ".join(kontext.get("maengel") or ()) or "keine Datei genannt"))
        # DER SPLAT WIRD ZUM NETZ (Owner-Entscheid 79, 13.10.2026) — EINMAL je Auftrag, vor
        # den Kameras; die Naht speichert das Netz nach Inhalt, eine zweite Kamera und ein
        # zweiter Auftrag mit demselben Splat rechnen es nicht neu. Fehlt die Bruecke oder
        # scheitert sie, bleibt es bei den Kugeln — mit einem Satz in `verdict.hinweise`
        # (ueber den Vermerk am Kameraurteil): ein stiller Rueckfall saehe aus wie das neue
        # Bild. Der Vermerk traegt `weg` und die Kennzahlen des Netzes, nie einen Pfad.
        if kontext is not None:
            vorbereitet = kontext_vorbereiten(kontext["ply"], matrix=kontext.get("matrix"))
            kontext = dict(
                kontext, weg=vorbereitet["weg"], netz=vorbereitet.get("netz"),
                netz_grund=vorbereitet.get("grund"), multipass_ply=vorbereitet["ply"],
                realityscan_grund=vorbereitet.get("realityscan_grund"),
                realityscan_ursache=vorbereitet.get("realityscan_ursache"),
                hinweise=[*(kontext.get("hinweise") or ()),
                          *([vorbereitet["hinweis"]] if vorbereitet.get("hinweis") else [])])
            # Auch der Befund des Auftrags (`befund.json`) liest den Kontext aus der Szene.
            szene["kontext"] = kontext
        # DIE HOCHACHSE DES AUFTRAGS SCHLAEGT DIE ANNAHME.
        #
        # `kosmovis.render-scene/v1` hat kein Feld dafuer, also gilt hier sonst
        # ANGENOMMENE_HOCHACHSE. Unser MCP-Einlass verlangt sie bei glb-Eingang aber als
        # PFLICHT — er weiss also, was der Vertrag nicht tragen kann, und bis zum
        # 26.08.2026 waere dieses Wissen an der Naht verfallen. Eine Z-up-glb waere unter
        # der Annahme Y-up gerendert worden: Tiefenkarte, Kamera und Geometrie-QA
        # gemeinsam verdreht, am einzelnen Bild nicht erkennbar.
        #
        # `eigene_quelle.lies_auftrag` reicht sie als `hochachse` heraus. Fehlt sie —
        # jeder Auftrag der Bruecke —, bleibt es bei der Annahme, und die steht als
        # solche im Bericht.
        hochachse = auftrag.get("hochachse") or up_axis
        hochachse_quelle = "auftrag" if auftrag.get("hochachse") else "annahme"
        ziel = ausgabeort(auftrag, out_wurzel)
        ziel.mkdir(parents=True, exist_ok=True)

        # DIE IFC WIRD ZUERST ZUR GLB (Einbausperre 22.09.2026, siehe `_ifc_umwandeln`).
        # Alles darunter — Modellstand, Multipass, Zwischenspeicher — arbeitet auf der
        # glb; allein der Raumleser bekommt die IFC, denn Raeume gibt es nur dort.
        #
        # Seit dem 20.10.2026 auch bei `skip` (Nr. 83): «nur Grundlage» rechnet Blender.
        modell = auftrag["modell"]
        # EINE VARIANTE OHNE MODELL (Fehler Test-App R48, 21.10.2026): Mit `vis.grundlage`
        # darf die Bestellung ohne Modelldatei kommen; gerechnet wird aus der abgelegten
        # Grundlage, Bestand und Modellstand kommen aus ihr (`lege_grundlage_ab`). Ohne
        # Grundlage bleibt ein fehlendes Modell, was es war: nichts zu rendern.
        if modell is None and szene.get("grundlage_verworfen"):
            # N6: Die Variante braucht ihre eigene Grundlage (andere Stimmung), aber das Modell
            # der bestellten Grundlage liegt nicht mehr in dieser Ablage.
            # Befund 337: ebenso, wenn sie einen anderen Fassadenstoff bestellt.
            was = ("einen anderen Fassadenstoff" if szene.get("material_der_variante")
                   and not szene.get("stimmung_der_variante") else "eine andere Stimmung")
            raise AbholerError(
                f"Die Variante traegt {was} als ihre Grundlage "
                f"{szene['grundlage_verworfen']} und braucht darum eine eigene — das Modell "
                f"dieser Grundlage liegt hier aber nicht mehr. Bitte «Grundlage rendern» mit "
                f"der Stimmung und dem Material der Variante.")
        if modell is None and not szene.get("grundlage"):
            raise AbholerError(_kosmo_szene.SATZ_OHNE_PFAD)
        umwandlung = None
        if _ist_ifc(modell):
            umwandlung = _ifc_umwandeln(modell, ziel)
            modell = umwandlung["glb_path"]
            if umwandlung.get("up_axis"):
                # Die Achse der Datei, die Blender WIRKLICH bekommt — sie hat der
                # Umwandler geschrieben und gemeldet. Eine Angabe des Auftrags spraeche
                # ueber die IFC, und die sieht Blender nicht.
                hochachse, hochachse_quelle = umwandlung["up_axis"], "umwandlung"
        # Bestand liest nur die glb, die KosmoOrbit schickt; unsere IFC-Umwandlung kennt
        # keine Rolle. `None` heisst: kein Bestand, der Bildauftrag bleibt, wie er kam.
        bestand = (None if umwandlung or modell is None
                   else _kosmo_szene.bestand_in_glb(modell))
        # DER BODEN, DEN DIE DATEI SELBST AUSWEIST (extras.role "ground", auf-20261021-316 B3):
        # Er faellt aus der Bauwerksmaske wie die Platte, auch wenn er «boden» heisst.
        # Seit dem 22.10.2026 auch nach unserer IFC-Umwandlung: Sie schreibt die Rolle an
        # Gelaende-Typen (IfcSite mit eigener Geometrie, auf-20261022-331).
        boden_rolle = (None if modell is None
                       else _kosmo_szene.gelaende_in_glb(modell))

        # DER MODELLSTAND, EINMAL JE AUFTRAG UND VOR ALLEM ANDEREN. Er ist eine Eigenschaft
        # der DATEI, nicht der Kamera, er kostet einen glb-Kopf und keine GPU-Sekunde — und
        # er ist der Befund, der drei Laeufen am 01./02.09.2026 gefehlt hat.
        #
        # Er steht VOR dem `ueberspringen`-Zweig, damit `modellstand` in JEDEM Ergebnissatz
        # dieselbe Bedeutung hat. Ein Feld, das mal da ist und mal nicht, zwingt jeden
        # Auswerter zum Verzweigen — dieselbe Regel wie bei `status` und `grund`.
        modellstand = (_modellstand_nicht_umgewandelt() if _ist_ifc(modell)
                       else _modellstand_ohne_modell() if modell is None
                       else _modellstand_gemeldet(modell))

        # NUR GRUNDLAGE (Demolauf Nr. 83, Auflage 3 des Integrators, 20.10.2026). Vom 26.08.
        # bis 20.10.2026 stand hier eine sofortige Rueckgabe ohne Bild: `skip` hiess bei uns
        # «abbestellt», in ihrem Vertrag aber «ohne KI-Schritt» (die lineart-Kopplung in
        # render-scene.ts). Das Haekchen «nur Cycles» bekam darum gar nichts — und genau
        # das rohe Blender-Bild ist der erste der zwei Schritte, die der Owner verlangt
        # (Nr. 81). Seither: Blender und Ebenen wie immer, das Cycles-Bild ist das Bild.
        nur_grundlage = bool(szene.get("ueberspringen"))
        # DIE GRUNDLAGE WIEDERVERWENDEN (Nr. 85) — vor jedem Blender-Lauf geprueft, laut.
        grundlagen_wurzel = (Path(out_wurzel) / GRUNDLAGEN_ORDNER) if out_wurzel else None
        geholt = (lies_grundlage(grundlagen_wurzel, szene["grundlage"], szene)
                  if szene.get("grundlage") else None)
        # DER HIMMEL KOMMT AUS DER GRUNDLAGE (Entscheid 126) — eine Variante rechnet kein
        # Blender; der Satz steht in `angewandt.messschalter` und von dort in den Hinweisen.
        if geholt is not None:
            szene, _ = himmel_der_grundlage(szene, geholt)
        berichte_der_grundlage = {e["kuerzel"]: e["bericht"]
                                  for e in (geholt or {}).get("kameras") or ()}
        if modell is None and geholt is not None:
            # Ohne Modell: was die Grundlage beim Rechnen ueber das Modell wusste. Eine
            # Grundlage von vor dem 21.10.2026 kennt das nicht — dann ungeprueft, kein Bestand.
            bestand = geholt.get("bestand")
            modellstand = geholt.get("modellstand") or modellstand
        berichte_neu: dict = {}
        # DIE GERECHNETE DREHUNG JE KAMERA (auf-20261020-295, N3) — aus dem Blender-Bericht,
        # fuer `angewandt.environment.drehung_je_kamera`.
        drehungen: dict = {}
        himmel_je_kamera: dict = {}
        hintergrund_je_kamera: dict = {}
        # EIN FESTER STARTWERT FUER DIE SERIE (Nr. 84): genau einer statt der Auswahl aus
        # drei — sonst behielte jede Variante womoeglich einen anderen «besten» Wurf.
        # DIE GUETE (Entscheid 104): Bei der Vorschau ein Startwert je Kamera, das schnelle
        # Bildmodell, seine Schritte und kleinere Steuerbilder — siehe `seeds_der_kamera`,
        # `gerechnetes_backbone`, `schritte_des_laufs`, `vorschau_steuerbilder`.
        vorschau = ist_vorschau(szene)

        kameras = szene.get("kameras")
        # DIE KAMERAWERTE DIESES AUFTRAGS (Knoten «Kamera», 20.10.2026): Bestellt er
        # `cameras_auto`, gelten seine Richtungen, Augenhoehe, Brennweite, Abstand und
        # Perspektive — sonst wie bisher die Einstellungen dieses Abholers.
        werte = kamerawerte_des_auftrags(
            szene, auto_richtungen=auto_richtungen, brennweite_mm=brennweite_mm,
            kamera_modus=kamera_modus, deckungsgrad=deckungsgrad, augenhoehe=augenhoehe)
        if szene.get("innenraum"):
            # DIE INNENANSICHT AUS `interior` (Befund 22.09.2026, auf-104): EINE Aufgabe,
            # ihr Standpunkt aus den Raeumen — und die Richtungen fuer `auto` fallen weg.
            # `auto` ist auch die Vorgabe, wenn `cameras` fehlt; es ist keine Bestellung
            # von Aussenansichten, `interior` dagegen ist eine von innen.
            if isinstance(kameras, list):
                # REINE ABSICHERUNG, auf dem Produktweg nicht erreichbar (Durchsicht
                # 22.09.2026): `kosmo_szene.lies_szene` setzt `innenraum` nur OHNE
                # mitgesandte Kameras. Er steht fuer eine Szene, die jemand von Hand baut
                # oder eine kuenftige Quelle liefert — bewacht an einer direkt gebauten
                # Szene in `tests/test_interior_bestellung.py`.
                raise AbholerError(
                    "Standpunkt zweimal bestellt: `innenraum` rechnet ihn aus den Raeumen, "
                    "und die Szene nennt eigene Kameras. Welcher gilt, entscheidet dieses "
                    "Modul nicht (dieselbe Regel wie `kette._fuehre_multipass`).")
            aufgaben = [_innenaufgabe(szene["innenraum"],
                                      raeume_lesen(auftrag.get("modell")))]
        elif kameras == "auto" or not isinstance(kameras, list):
            aufgaben = [{"kuerzel": r, "richtung": r, "brennweite_mm": werte["brennweite_mm"]}
                        for r in werte["richtungen"]]
        else:
            # Mitgesandte Kameras. War `interior` bestellt, reist der Vermerk an jeder
            # mit — siehe `_mitgesandter_innenvermerk` (23.09.2026).
            vermerk = _mitgesandter_innenvermerk(szene)
            # «SENKRECHT» AN EINER MITGESANDTEN KAMERA (Entscheid 109): waagrechte Achse und
            # Objektiv-Shift statt Kippen — gerechnet hier (`senkrecht_gestellt`), gestellt
            # im Runner ueber --shift-y. Ohne `perspektive` bleibt die Kamera, wie sie kam.
            aufgaben = [senkrecht_gestellt(dict(k, kuerzel=k.get("kuerzel") or f"kamera{i}",
                                                innenraum=dict(vermerk) if vermerk else None))
                        for i, k in enumerate(kameras)]
        if not aufgaben:
            raise AbholerError(
                "Der Auftrag nennt keine einzige Kamera, und auch keine automatische "
                "Richtung ist eingestellt. Es gibt nichts zu rendern."
            )
        # ZWEI QUELLEN FUER DEN STANDPUNKT (Befund 23.09.2026). Eine mitgesandte Kamera
        # wird mit `dict(k, ...)` ganz kopiert; traegt sie neben `auge`/`blick_auf` ein
        # `richtung`, ginge beides an `seams` — und der Runner laesst `auge` still
        # vorgehen. Abgewiesen wird VOR dem ersten Blender-Lauf und fuer alle Aufgaben:
        # dieselbe Regel wie bei `innenraum` oben und in `kette._fuehre_multipass`.
        # Auf dem Produktweg liefert `kosmo_szene.spec_zu_kamera` kein `richtung`; die
        # Abweisung steht fuer eine von Hand gebaute Szene oder eine kuenftige Quelle und
        # ist an einer solchen bewacht (tests/test_runde7_abholer.py).
        doppelt = [str(a.get("kuerzel")) for a in aufgaben
                   if a.get("richtung") is not None
                   and (a.get("auge") is not None or a.get("blick_auf") is not None)]
        if doppelt:
            raise AbholerError(
                f"Standpunkt zweimal bestellt: Kamera {', '.join(doppelt)} nennt ein "
                f"Richtungskuerzel (`richtung`) UND einen Standort (`auge`/`blick_auf`). "
                f"Welcher gilt, entscheidet dieses Modul nicht — der Runner liesse den "
                f"Standort still vorgehen, und das Kuerzel stuende nur noch im Auftrag.")

        # IST DAS BESTELLTE BILDMODELL HIER UEBERHAUPT RECHENBAR? — vor Blender, vor dem
        # Laden (Sammel-Nachprobe auf-20261001-230). qwen-image-2.1 war bestellbar und
        # scheiterte erst an der ersten Kamera, NACH dem Blender-Lauf, mit
        # «AttributeError: module diffusers has no attribute QwenImage21Pipeline». Fehlt
        # die Klasse, gibt es ein Ergebnis mit `lieferstatus: fehlgeschlagen` und dem Satz
        # je Kamera — eine Antwort, die drueben lesbar ist, statt eines Absturzes.
        # `None` («nicht geprueft») haelt nichts an: Ungeprueft ist nicht dasselbe wie
        # fehlend, und der Ladeweg fragt dieselbe Frage noch einmal (`render.lade_modell`).
        backbone_name = gerechnetes_backbone(szene)
        schritte_lauf = schritte_des_laufs(szene)
        lage_modell = (pipeline_lage(backbone_name) if pipeline_lage is not None
                       else {"rechenbar": None})
        if lage_modell.get("rechenbar") is False and not nur_grundlage:
            urteile_ohne = []
            for aufgabe in aufgaben:
                kuerzel = aufgabe["kuerzel"]
                urteile_ohne.append(dict(
                    _uebersprungenes_urteil(kuerzel, {"abbruch": True,
                                                      "abbruch_grund": lage_modell["satz"]}),
                    rahmung=None, komposition=None, blickfeld=None,
                    modellstand=modellstand, umgebung=dict(lage_modell),
                    **{_kosmo_szene.URTEIL_INNENANSICHT: aufgabe.get("innenraum")}))
                _urteil_ablegen(ziel / str(kuerzel), urteile_ohne[-1])
            return {
                "bilder": [], "geometrie_urteil": None, "stil_urteil": None,
                "kameras": urteile_ohne, "zeiten": {"gesamt": 0.0},
                "uebersprungen": False, "grund": lage_modell["satz"],
                "hochachse": {"wert": hochachse, "quelle": hochachse_quelle},
                "modellstand": modellstand, "engine": None, "ebenen": [],
                "umwandlung": umwandlung,
                "innenansicht": next((a.get("innenraum") for a in aufgaben
                                      if a.get("innenraum")), None),
            }

        # DIE BLENDER-FASSUNG, EINMAL JE AUFTRAG. Sie gehoert in den Cache-Schluessel
        # (4.2 und 5.2 sind zwei Renderer) und kostet 0,22 s — je Kamera abgefragt waere
        # sie eine Verschwendung, je Auftrag ist sie unter der Messgrenze.
        fassung = _blender_fassung() if zwischenspeicher is not None else ""
        # Die Materialwahl fuer den Runner — einmal je Auftrag, nur wenn bestellt und
        # Blender rechnet (mit `vis.grundlage` fehlen die Dateien und werden nicht gebraucht).
        materialwahl_datei = (materialwahl_ablegen(ziel, szene)
                              if szene.get("materialien_dateien") else None)

        bilder: list[str] = []
        urteile: list[dict] = []
        zeiten: dict[str, float] = {}
        # Welche Soll-Karte schon gerendert wurde, und von welcher Kamera. Siehe
        # `_finde_zwilling`: Bei einem Quader fallen `sSE` und `nNW` zusammen.
        gesehen: list[dict] = []
        beginn_gesamt = time.monotonic()
        # DER FORTSCHRITT AM AUFTRAG (20.10.2026) — siehe `_Fortschritt`. Er sieht zwischen
        # den Phasen auch nach, ob der Auftrag abgebrochen wurde.
        fort = _Fortschritt(ordner, len(aufgaben), melde=melde, abgebrochen=abgebrochen,
                            uhr=uhr)

        for nummer, aufgabe in enumerate(aufgaben, start=1):
            kuerzel = aufgabe["kuerzel"]
            fort.kamera(nummer)
            # Der Innenvermerk dieser Aufgabe, an JEDES ihrer Urteile — auch an eines,
            # das nicht gerendert wurde: Auch dort ist die Frage, WOHER der Standpunkt
            # kam, die erste, die jemand stellt. `None`: `interior` war nicht bestellt.
            # Bewacht fuer die beiden Abbrueche vor dem Bild (Blickfeld, Komposition) in
            # tests/test_interior_bestellung.py (23.09.2026). Am Zwilling ist nur die
            # WIRKUNG bewacht: seine Zeile `**innen` ist gleichwertig zu ihrem Fehlen, weil
            # das Vorbild denselben Vermerk traegt (siehe dort).
            innen = {_kosmo_szene.URTEIL_INNENANSICHT: aufgabe.get("innenraum")}
            # DIE RAHMUNGSWERTE REISEN NUR MIT EINER RICHTUNG (Befund 23.09.2026).
            # `kamera_modus`, `deckungsgrad`, `augenhoehe` und `bias_grad` liest der
            # Runner allein auf dem Weg «abgeleitet», wo `kameras.kamerasatz` aus dem
            # Kuerzel den Standort rechnet. Bis heute gingen sie bei JEDER Aufgabe mit,
            # auch bei einer mitgesandten oder Innenkamera (`auge`) — `kamera_modus`
            # sogar immer, denn seine Vorgabe ist MODUS_SHIFT und nie `None`. Wirkung
            # hatten sie dort keine; jetzt gehen sie dort gar nicht erst hin.
            #
            # Was ein Aufrufer ausdruecklich gesetzt hat und hier zurueckbleibt, steht
            # als Satz am Urteil dieser Kamera, statt still zu verfallen. Die Vorgabe
            # MODUS_SHIFT zaehlt dabei nicht als Bestellung: Sie ist von einem
            # ausdruecklich gesetzten MODUS_SHIFT nicht zu unterscheiden.
            mit_richtung = aufgabe.get("richtung") is not None
            zurueck = [] if mit_richtung else [
                f"{name}={wert!r}" for name, wert in (
                    ("kamera_modus", None if werte["kamera_modus"] == _kameras_modul.MODUS_SHIFT
                     else werte["kamera_modus"]),
                    ("deckungsgrad", werte["deckungsgrad"]),
                    ("augenhoehe", werte["augenhoehe"]),
                    ("bias_grad", bias_grad))
                if wert is not None]
            innen[URTEIL_KAMERAWERTE_ZURUECK] = (
                f"Nicht an den Runner gegangen: {', '.join(zurueck)}. Diese Kamera "
                f"kommt ohne Richtungskuerzel (Standort gegeben oder Rueckfall), und "
                f"diese Werte wirken nur, wo der Standort aus einer Richtung gerechnet "
                f"wird — hier waeren sie wirkungslos gewesen." if zurueck else None)
            aus = ziel / str(kuerzel)
            aus.mkdir(parents=True, exist_ok=True)
            beginn = time.monotonic()

            einstellungen = dict(
                glb_path=str(modell), up_axis=hochachse,
                # DIE BOX, NACH DER DIE KAMERA RAHMT. `None` heisst: nach der SZENE, und
                # das ist der Fall, fuer den der Rahmungsriegel gebaut wurde — er lehnt
                # dann Laeufe ab, ohne je die Box zu reichen, die sie heilen wuerde.
                #
                # Gemessen am 26.08.2026 am gegliederten Testbau MIT Gelaendeplatte
                # (20 x 20 m Szene, 12 x 9,5 x 15 m Bauwerk, Kamera sSE, 400 px):
                #
                #     ohne kamera_huellbox   anteil_bauwerk 0,0788
                #     mit  kamera_huellbox   anteil_bauwerk 0,1730     Faktor 2,2
                #
                # WOHER DIE BOX KOMMT, ist die offene Haelfte. Drei Wege, jeder mit
                # seinem Preis, und keiner davon ist umsonst:
                #
                #   (a) Ein ZWEITER Blender-Lauf je Kamera — der erste liefert
                #       `bbox_bauwerk`, der zweite rahmt danach. Verdoppelt die
                #       Blenderzeit: bei Vertragsvorgaben rund 80 s statt 40 s je Kamera.
                #       Mit dem Zwischenspeicher zahlt man das nur beim ERSTEN Auftrag
                #       einer Geometrie — bei einer Messreihe ueber Prompts also einmal.
                #   (b) Ein eigener, LEICHTER Laeufer, der die glb nur liest und die
                #       Box nach der Namensregel rechnet. **Gibt es seit dem 01.09.2026:
                #       `aiimaging.glbbox`.** Die Schaetzung von 1-2 s war um mehr als
                #       eine Zehnerpotenz zu pessimistisch — gemessen 0,08 s an 4771
                #       Meshes und 25 MB, weil glTF die Huellbox je Mesh im JSON-Kopf
                #       fuehrt und die Dreiecke nie gelesen werden muessen. Kein
                #       Unterprozess, keine Abhaengigkeit, keine Prozessgrenze.
                #
                #       ABER: Auf der Bestandsdatei vom 28.08.2026 bringt er nur
                #       2,3 % engere Rahmung (358,02 -> 350,33 m), weil deren Gelaende
                #       `Toposolid`, `Sub-Division` und `Umgebung - Gras` heisst und
                #       keines dieser Woerter in `maske.GELAENDE_WOERTER` steht. Der
                #       Weg traegt; die REGEL, die er befragt, sieht dieses Gelaende
                #       nicht. `glbbox` meldet das als `schrumpfung`, damit eine
                #       wirkungslose Box nicht wie eine wirksame aussieht. Richtig
                #       erkannt waeren es 234,43 m gewesen, also -34,5 %.
                #   (c) Der IFC-Report. Er fuehrt `bbox_bauwerk` — und ist auf genau
                #       diesem Fall FALSCH: Sein Typfilter ist `("IfcSite",)`, die
                #       Gelaendeplatte ist ein `IfcSlab` namens `Gelaende`, und die Box
                #       kam am 26.08.2026 gemessen gleich der SZENENBOX zurueck
                #       (20 x 20 m statt 12 x 9,5 m). Die Blender-Seite trifft es
                #       richtig, weil der Knotenname seit dem Morgen den IFC-Namen
                #       traegt — die IFC-Seite nicht.
                #
                # Der Entscheid liegt bei `auf-41` (G3). Bis dahin: wer die Box hat,
                # reicht sie; wer nicht, rahmt nach der Szene wie bisher.
                kamera_huellbox=_rahmung_fuer(kamera_huellbox, modell, hochachse,
                                              aufgabe.get("richtung")),
                aufloesung=szene.get("aufloesung", 512), hoehe=szene.get("hoehe"),
                samples=szene.get("samples", 128),
                kamera=aufgabe.get("richtung"),
                kamera_modus=werte["kamera_modus"] if mit_richtung else None,
                gelaende_z=gelaende_z,
                # Der Sonnenstand der Bestellung. Bis zum 26.08.2026 lief er ins Leere:
                # Ein Auftrag mit Abendstand wurde gerendert, als waere er nicht
                # gestellt worden — mit einem sauberen, gut belichteten, falschen Bild.
                sonne=szene.get("sonne"),
                auge=aufgabe.get("auge"), blick_auf=aufgabe.get("blick_auf"),
                brennweite=aufgabe.get("brennweite_mm"),
                # DREI KAMERAPARAMETER, die der Runner seit jeher kennt und die bis zum
                # 26.08.2026 auf diesem Weg NIE ankamen — `seams` setzte keinen davon.
                #
                # `deckungsgrad` ist der wichtigste: `auf-20260825-41` vergleicht
                # Bildpaare bei 0,55 gegen 0,70, und diese Messung war ueber den
                # Produktivweg gar nicht durchfuehrbar. `augenhoehe` ist die Groesse, um
                # die Frage 7 des Uebergabeblatts mit KosmoOrbit kreist.
                #
                # `None` heisst NICHT ANGEFASST: Dann gelten die Vorgaben des Runners, und
                # jede bisher gemessene Aufnahme bleibt reproduzierbar.
                # Seit dem 23.09.2026 nur mit Richtung — siehe `mit_richtung` oben.
                deckungsgrad=werte["deckungsgrad"] if mit_richtung else None,
                augenhoehe=werte["augenhoehe"] if mit_richtung else None,
                bias_grad=bias_grad if mit_richtung else None,
                stillstand_frist_s=stillstand_frist_s,
                # DER ZEITDECKEL, seit dem 26.08.2026 bestellbar. Er wird IMMER gesetzt,
                # auch auf seinen Vorgabewert — ein «durchgereicht, wenn bestellt» waere
                # ein dritter Zustand neben den beiden Tabellen, und genau gegen die
                # dritte Moeglichkeit sind sie gebaut.
                timeout=ZEITDECKEL_S if zeitdeckel_s is None else zeitdeckel_s,
            )
            # DER AUSSCHNITT OHNE GELAENDE — nur, wenn er gilt; sonst bleiben Einstellungen
            # und Speicherschluessel die bisherigen.
            if (einstellungen.get("kamera_huellbox") is None
                    and _ausschnitt_ohne_box(kamera_huellbox, modell, hochachse,
                                             aufgabe.get("richtung"))):
                einstellungen["kamera_ausschnitt"] = True
            # DER SPLAT ALS UMGEBUNG — nur, wenn bestellt. Ohne ihn bleiben Einstellungen
            # und Speicherschluessel Wort fuer Wort die bisherigen.
            if kontext is not None:
                # Das Netz aus der Bruecke, sonst der Splat selbst (Kugel-Notloesung).
                einstellungen["kontext_ply"] = kontext.get("multipass_ply") or kontext["ply"]
                if kontext.get("matrix") is not None:
                    einstellungen["kontext_matrix"] = list(kontext["matrix"])

            # DER FESTE ABSTAND und der SHIFT EINER SENKRECHTEN KAMERA — nur, wenn bestellt.
            if mit_richtung and werte["abstand_fest_m"] is not None:
                einstellungen.update(dict(abstand_fest_m=werte["abstand_fest_m"]))
            if not mit_richtung and aufgabe.get("shift_y") is not None:
                einstellungen.update(dict(shift_y=aufgabe["shift_y"]))
            # DIE STIMMUNG (Entscheide 107/110/113) — nur, wenn bestellt; ohne sie bleiben
            # Einstellungen und Speicherschluessel Wort fuer Wort die bisherigen.
            einstellungen.update(umgebung_einstellungen(szene))
            # DIE MATERIALIEN JE ART (Entscheide 107/111/113) — als JSON im Auftragsordner,
            # einmal je Auftrag geschrieben; ohne Bestellung kein Schluessel.
            if materialwahl_datei is not None:
                einstellungen.update(dict(materialien_json=str(materialwahl_datei)))

            # DER ZWISCHENSPEICHER. `None` heisst AUS, und das ist die Vorgabe: Ein
            # Gedaechtnis, das niemand bestellt hat, ist die unangenehmste Art von
            # Ueberraschung.
            if geholt is not None and str(kuerzel) not in berichte_der_grundlage:
                # Diese Kamera hat in der Grundlage kein Bild (sie sah dort an der Szene
                # vorbei) — neu gerechnet wird nicht, das waere eine andere Grundlage.
                urteile.append(dict(_uebersprungenes_urteil(kuerzel, {
                    "abbruch": True,
                    "abbruch_grund": (f"Die Grundlage {geholt['id']} hat fuer diese Kamera "
                                      f"kein Bild; bitte die Grundlage neu rendern.")}),
                    rahmung=None, komposition=None, blickfeld=None,
                    modellstand=modellstand, **innen))
                _urteil_ablegen(aus, urteile[-1])
                zeiten[str(kuerzel)] = round(time.monotonic() - beginn, 1)
                fort.kamera_fertig(gerechnet=False)
                continue
            schluessel = (multipass_schluessel(einstellungen, blender=fassung)
                          if zwischenspeicher is not None and geholt is None else None)
            aus_speicher = (None if geholt is not None
                            else _aus_dem_zwischenspeicher(zwischenspeicher, schluessel))
            if geholt is not None:
                # AUS DER GRUNDLAGE (Nr. 85): Kamera, Tiefe, Ebenen, Schoenbild des ersten
                # Laufs — kein Blender, keine Auto-Kamera. Der Vermerk sagt woher.
                bericht = dict(berichte_der_grundlage[str(kuerzel)])
                bericht["zwischenspeicher"] = {"treffer": True, "schluessel": None,
                                               "grundlage": geholt["id"],
                                               "gerechnet_unter": bericht.get("blender")}
            elif aus_speicher is not None:
                bericht = dict(aus_speicher)
                # WOHER DAS BILD KOMMT, steht im Bericht. Ohne diese drei Zeilen saehe ein
                # Lauf aus dem Speicher genauso aus wie ein gerechneter — nur schneller,
                # und niemand wuesste warum. Genau die Sorte stiller Unterschied, gegen
                # die dieses Projekt an fuenf Stellen dieses Tages angetreten ist.
                bericht["zwischenspeicher"] = {"treffer": True, "schluessel": schluessel,
                                               "gerechnet_unter": bericht.get("blender")}
            else:
                bericht = multipass(einstellungen.pop("glb_path"), aus, **einstellungen)
                # DER WEG DER UMGEBUNG REIST MIT (Entscheid 81, 13.10.2026): Am Weg prueft
                # `kette._cache_maengel`, ob ein Eintrag nach dem Ein- oder Ausschalten von
                # RealityScan noch ein Treffer ist — derselbe Vermerk wie im Kettenknoten.
                if kontext is not None and isinstance(bericht, dict):
                    bericht.setdefault("kontext_weg", {
                        "weg": kontext.get("weg"),
                        "realityscan_ursache": kontext.get("realityscan_ursache")})
                # ABGELEGT WIRD, WAS ALS TREFFER TAUGEN WUERDE — dieselbe Pruefung, nicht
                # eine zweite. Der erste Anlauf fragte hier nach `status == "ok"`, und das
                # war eine ANDERE Bedingung als die beim Lesen: Ein Bericht ohne
                # `status`-Feld wurde nie abgelegt, ohne dass irgendwo stand warum.
                #
                # Zwei Bedingungen fuer dieselbe Frage laufen auseinander, sobald eine
                # gepflegt wird — derselbe Grund, aus dem der Abholer eine zweite QUELLE
                # bekam und keinen zweiten Ausfuehrer.
                if (zwischenspeicher is not None
                        and not _kette._cache_maengel("multipass", bericht, _kette.BEDARF)):
                    # ZUSAGEN sind die Dateien, auf die der Eintrag zeigt. Ohne sie weiss
                    # er nicht, wovon er redet: Er speichert Pfade, nicht Bilder, und ein
                    # Pfad allein ist eine Behauptung. `graph.ArtefaktCache.hole` prueft
                    # sie bei jedem Zugriff — ein aufgeraeumtes /tmp genuegt sonst.
                    zusagen = [bericht[f] for f in _kette.BEDARF["multipass"].dateien
                               if isinstance(bericht.get(f), str) and bericht[f]]
                    zwischenspeicher.lege_ab(schluessel, bericht, zusagen=zusagen)
                bericht["zwischenspeicher"] = {"treffer": False, "schluessel": schluessel,
                                               "gerechnet_unter": bericht.get("blender")}
            # DER REFERENZPUNKT DER BESTELLUNG IM KAMERABERICHT (Ergebnis auf-20261022-341, e):
            # `kosmo_szene.spec_zu_kamera` liest ihn, und er stand danach nur in der abgelegten
            # Bestellung. Er wird nicht angewandt (`position` traegt die Zahl schon im
            # Weltsystem) — er sagt, worauf sich die Augenhoehe drueben bezog, und reist darum
            # am Kamerabericht mit: in die Komposition (`augenhoehe.referenzpunkt`), in
            # befund.json und in die Grundlage. Auf allen drei Wegen (gerechnet, Speicher,
            # Grundlage), und nur, wenn bestellt.
            bericht = _referenzpunkt_eintragen(bericht, aufgabe.get("referenzpunkt"))
            # DIE VORSCHAU: das Cycles-Bild dieser Kamera, sobald es da ist — gerechnet, aus
            # dem Zwischenspeicher oder aus der Grundlage (dort dient deren Schoenbild).
            if isinstance(bericht, dict):
                fort.vorschau_da(kuerzel, bericht.get("beauty_png"))
                drehung = drehung_aus_bericht(bericht)
                if drehung is not None:
                    drehungen[str(kuerzel)] = drehung
                # Womit Blender den Himmel rechnete — auch aus einer Grundlage (306, B4).
                himmel = himmel_aufloesung_aus_bericht(bericht)
                if himmel is not None:
                    himmel_je_kamera[str(kuerzel)] = himmel
                hintergrund = hintergrund_aus_bericht(bericht)
                if hintergrund is not None:
                    hintergrund_je_kamera[str(kuerzel)] = hintergrund

            # ZUERST DIE BLICKRICHTUNG, DANN DIE TIEFENKARTE — die Reihenfolge ist der
            # Punkt. Eine Kamera, die an der Szene vorbeischaut, erzeugt ein LEERES
            # Tiefenbild, und die Meldung darueber kommt aus der Normalisierung
            # («Tiefenbild enthaelt keinen einzigen Geometriepixel … Pruefe Kamera und
            # Szene, nicht die Schranke»). Sie ist richtig und nennt die Ursache nicht.
            # Stuende dieser Riegel darunter, bekaeme man in genau dem Fall, fuer den er
            # gebaut ist, weiterhin die andere Meldung.
            blickfeld = _blick_trifft_szene(bericht)
            if blickfeld["abbruch"]:
                # `rahmung` wird AUSDRUECKLICH auf None gesetzt und nicht mit dem
                # Blickfeldbefund gefuellt. `_uebersprungenes_urteil` legt seinen
                # Riegel unter diesem Namen ab, und `_nicht_gerendert_kurz` liest ihn
                # dort: Ein Blickfeldbefund unter `rahmung` haette die fremde Seite
                # «Das Bauwerk fuellt zu wenig der Bildbreite» lesen lassen — fuer eine
                # Kamera, die das Bauwerk ueberhaupt nicht anschaut. Ein falscher Grund
                # ist schlimmer als keiner.
                urteile.append(dict(_uebersprungenes_urteil(kuerzel, blickfeld),
                                    massstab=_massstab_gemeldet(bericht),
                                    rahmung=None, komposition=None,
                                    blickfeld=blickfeld, modellstand=modellstand,
                                    **innen))
                _urteil_ablegen(aus, urteile[-1])
                zeiten[str(kuerzel)] = round(time.monotonic() - beginn, 1)
                fort.kamera_fertig(gerechnet=False)
                continue

            tiefe = bericht.get("depth_png")
            if not tiefe:
                raise AbholerError(
                    f"Kamera {kuerzel!r}: keine Tiefenkarte. Ohne sie gibt es keine "
                    f"Konditionierung, und ein Render ohne sie wäre genau die erfundene "
                    f"Kubatur, gegen die dieses Projekt antritt. Grund: "
                    f"{bericht.get('depth_png_fehler')}\n"
                    f"Blickrichtung: {_blickrichtung_satz(blickfeld)}"
                )

            # DIE PRUEFUNG VOR DEM BILDLAUF. Sie steht hier und nicht weiter unten,
            # weil alles darunter Geld kostet: Startwerte, Diffusion, Schaetzerlaeufe.
            # Gemessen ist, dass ein Lauf bei 30 % Bildbreite SCHLECHTER ausgeht als bei
            # 17,5 % — Rendern ist hier nicht "ein schwaecheres Ergebnis", sondern gar
            # keines (auf-vis-20260825-15, Posten 1).
            # Sind die Zwischenbilder ueberhaupt ganz da? Ein halb geschriebenes PNG
            # faellt sonst erst in der Diffusion auf — mit einer Meldung aus der
            # Bildbibliothek, die keine Datei nennt (auf-vis-20260826-16).
            bilderlage = _bilder_vollstaendig(bericht)
            if not bilderlage["vollstaendig"]:
                raise AbholerError(
                    f"Kamera {kuerzel!r}: ein Zwischenbild des Multipass ist "
                    f"unvollstaendig oder beschaedigt. {bilderlage['grund']}\n"
                    f"Das ist ein Befund ueber eine DATEI und keiner ueber die "
                    f"Geometrie. Gerendert wird darauf nicht — ein Lauf auf einer halben "
                    f"Tiefenkarte ist genau die erfundene Kubatur, gegen die dieses "
                    f"Projekt antritt.")

            # Der Massstab wird GEMELDET und bricht nichts ab — siehe
            # `_massstab_gemeldet`. Er steht darum ausdruecklich NICHT in der Schleife
            # darunter: Rahmung und Kamerahoehe sind Eigenschaften der KAMERA, die eine
            # andere Blickrichtung heilen kann. Der Massstab ist eine Eigenschaft der
            # GEOMETRIE und bei jeder Kamera derselbe.
            # IN DIE GRUNDLAGE kommt jede Kamera, deren Multipass ganz da ist (Nr. 85).
            if geholt is None:
                berichte_neu[str(kuerzel)] = {k: v for k, v in bericht.items()
                                              if k != "zwischenspeicher"}
            # DIE BESTELLTEN EBENEN (E124, Schritt 1) — hier, weil der Multipass jetzt ganz
            # da ist; auch eine Kamera, die spaeter ausgesetzt wird, hat sie.
            ebenen = ebenen_dieser_kamera(bericht, kuerzel, szene.get("ebenen"))
            massstab = _massstab_gemeldet(bericht)
            rahmung = _rahmung_vor_dem_render(
                bericht, gerahmte_box=einstellungen.get("kamera_huellbox"))
            if not rahmung_pruefen and rahmung.get("abbruch"):
                rahmung = _rahmung_abgeschaltet(rahmung)
            komposition = _komposition_vor_dem_render(bericht)
            # DIE HOEHE INS ERGEBNIS (Ergebnis auf-20261022-341, c) — siehe `kamerahoehe_vermerk`.
            hoehe_vermerk = kamerahoehe_vermerk(komposition, bericht, kuerzel)
            if nur_grundlage:
                # DAS CYCLES-BILD IST DAS BILD (Nr. 83/81). Rahmung und Komposition werden
                # gemeldet und halten nichts an: Sie schuetzen den KI-Schritt, und der
                # findet hier nicht statt. Gemessen wird nichts — die Geometrie IST das Modell.
                urteile.append(_urteil_nur_grundlage(
                    kuerzel, bericht, aus, rahmung=rahmung, komposition=komposition,
                    massstab=massstab, blickfeld=blickfeld, modellstand=modellstand,
                    ebenen=ebenen, sonne=_sonne.aus_bestellung(szene.get("sonne")),
                    innen=innen))
                # DIE STIMMUNG WIRD AUCH HIER GEMESSEN (auf-20261020-293, Punkt 6): Bis dahin
                # stand die Messung nur im KI-Zweig, und dieser Zweig kehrte vorher mit
                # `continue` zurueck — `qa.ueberstrahlt_anteil` fehlte gerade bei dem Lauf,
                # dessen Bild das Cycles-Bild IST. Die Maske wird dafuer hier gebaut (sie liest
                # nur den ID-Pass), und nur mit Stimmung.
                #
                # DER MASKENBEFUND AUCH OHNE KI-SCHRITT (auf-20261021-320, B6): Bis dahin baute
                # dieser Zweig die Maske nur fuer die Stimmung und legte ihren Befund nicht ab —
                # ein Lauf «nur Grundlage» trug darum weder `maskenbefund` noch
                # `gelaende_quelle`, und ob die Rolle «ground» griff, liess sich am Lauf selbst
                # nicht belegen. Jetzt steht der Befund wie im KI-Zweig am Urteil.
                maskenbefund_grundlage = _maske_bauen(
                    bericht, gelaende_erwartet=gelaende_der_szene,
                    gelaende_zusatz=_formgelaende_aus_bericht(bericht),
                    bestand_namen=_bestandsnamen(bestand),
                    gelaende_rolle=_bodennamen(boden_rolle))
                urteile[-1]["maskenbefund"] = maskenbefund_grundlage
                urteile[-1][_kosmo_szene.URTEIL_KAMERAHOEHE] = hoehe_vermerk
                if szene.get("umgebung"):
                    urteile[-1].update(_stimmungsmessung(szene, bericht,
                                                         maskenbefund_grundlage.get("maske")))
                # DIE KONTEXTMASKE GEHOERT ZUR GRUNDLAGE (auf-20261021-313, B2): Sie liest nur
                # den Material-ID-Pass, und eine Variante auf dieser Grundlage rechnet sie
                # sonst erst im KI-Lauf. Dieselbe Datei und derselbe Vermerk wie dort.
                kontext_grundlage = kontextmaske_der_kamera(bericht, aus, kuerzel, bestand,
                                                                boden_rolle)
                if kontext_grundlage is not None:
                    urteile[-1]["kontext_maske"] = kontext_grundlage
                bilder.append(urteile[-1]["bild_png"])
                _urteil_ablegen(aus, urteile[-1])
                zeiten[str(kuerzel)] = round(time.monotonic() - beginn, 1)
                fort.kamera_fertig(gerechnet=True)
                continue
            for lage in (rahmung, komposition):
                if lage.get("abbruch"):
                    break
            else:
                lage = None
            if lage is not None:
                urteile.append(dict(_uebersprungenes_urteil(kuerzel, lage),
                                    massstab=massstab, rahmung=rahmung,
                                    komposition=komposition, blickfeld=blickfeld,
                                    modellstand=modellstand, ebenen=ebenen, **innen))
                _urteil_ablegen(aus, urteile[-1])
                zeiten[str(kuerzel)] = round(time.monotonic() - beginn, 1)
                fort.kamera_fertig(gerechnet=False)
                continue

            # Die Soll-Karte kommt aus der EXR, nicht aus dem PNG: nur sie trägt die
            # Silhouette exakt. Das PNG war die Eingabe des Modells, die EXR ist der
            # Massstab.
            soll, breite, hoch = soll_lesen(bericht)

            # DER STRUKTURWERT DER TIEFENKARTE — hier und NICHT oben beim Rahmungsriegel.
            #
            # Der Riegel steht zwanzig Zeilen hoeher, weil alles darunter Geld kostet
            # (der Kommentar dort nennt die Messung dazu). Die Soll-Karte gibt es aber
            # erst hier: `bildlesen.tiefen_aus_report` faellt notfalls auf die EXR zurueck
            # und startet dafuer einen zweiten Blender-Prozess, Zeitlimit 300 s.
            # `soll_lesen` nach oben zu ziehen, damit die Struktur schon beim Riegel
            # danebensteht, machte aus einem billigen Abbruch einen teuren — eine
            # Verschlechterung, auch wenn die neue Zahl schoener aussaehe.
            #
            # RECHTZEITIG IST DIE WARNUNG TROTZDEM: Sie steht vor der Diffusion, und die
            # ist die teure Stufe (je Startwert ein eigener Lauf, siehe `_bester_seed`).
            # Verloren geht durch das Nachtragen nichts, denn die Struktur entscheidet
            # ohnehin nicht: `kameras.struktur_nachtragen` laesst `abbruch` unberuehrt,
            # solange die Warnschwelle ungeeicht ist (auf-20260912-108).
            try:
                rahmung = dict(
                    _kameras_modul.struktur_nachtragen(rahmung, soll, breite=breite),
                    struktur_fehler="")
            except Exception as fehler:  # noqa: BLE001 — Begruendung unmittelbar darunter
                # BEFUND ALS FELD, KEIN ABSTURZ — dieselbe Haltung wie bei
                # `depth_png_fehler` weiter oben: Was nicht zu messen war, wird als nicht
                # gemessen GEMELDET und nimmt den Lauf nicht mit. Die Struktur ist eine
                # Auskunft neben dem Urteil; an ihr ein gerendertes Bild scheitern zu
                # lassen, hiesse ihr genau das Gewicht zu geben, das sie ausdruecklich
                # nicht haben soll.
                #
                # Der Grund steht dabei und wird nicht verschluckt: Ein stilles
                # `struktur: None` laese sich wie «es lag keine Karte vor» — und das ist
                # etwas anderes als «die Karte war da und nicht lesbar».
                rahmung = dict(rahmung, struktur=None,
                               struktur_fehler=f"{type(fehler).__name__}: {fehler}")

            maskenbefund = _maske_bauen(
                bericht, gelaende_erwartet=gelaende_der_szene,
                gelaende_zusatz=_formgelaende_aus_bericht(bericht),
                # DER BESTAND IST NICHT DAS BAUWERK (auf-20261021-313, B1): 35,9 % der Maske.
                bestand_namen=_bestandsnamen(bestand),
                # DER BODEN MIT ROLLE AUCH NICHT (auf-20261021-316, B3).
                gelaende_rolle=_bodennamen(boden_rolle))
            # DIE KONTEXTMASKE (Video-Befund L4-5, 21.10.2026): wo Bestand, Umfeld und Splat im
            # Bild stehen — der Bestand fehlt dafuer seit 313 in der Bauwerksmaske. Als Datei
            # neben die Kamera, wenn es Kontext gibt; die Zahlen am Urteil. Noch kein Eingang
            # ins Bildmodell.
            kontext_maske = kontextmaske_der_kamera(bericht, aus, kuerzel, bestand, boden_rolle)
            # DIE UMGEBUNG ZAEHLT NICHT ALS BAUWERK (auf-20261008-271): Ihre Bildpunkte
            # werden in der Pruefung ausgeblendet — nur, wenn es sie gibt; ohne Splat
            # bleibt jeder Aufruf Wort fuer Wort der bisherige.
            kontext_pixel = maskenbefund.get("kontext_pixel")
            ausblendung = {"ausblenden": kontext_pixel} if kontext_pixel else {}
            # Fuer die Seedwahl nach dem Umriss dasselbe: Der Umriss ist der des Bauwerks,
            # nicht der der Baeume dahinter.
            soll_umriss = _ohne_umgebung(soll, kontext_pixel) if kontext_pixel else soll
            # DER MESSBODEN (Owner-Entscheid 78, auf-20261008-272): Hat das Modell keinen
            # Boden, bekommt die Soll-Karte DER PRUEFUNG eine gedachte Ebene auf Gelaendehoehe
            # — das Tiefenbild fuer das Bildmodell bleibt unberuehrt. Der Umriss fuer die
            # Seedwahl bleibt der des Bauwerks.
            soll_pruefung, trennhilfe, messboden_befund = _mit_messboden(
                soll, breite, hoch, bericht, maskenbefund)
            if trennhilfe is not None:
                ausblendung = dict(ausblendung, trennhilfe=trennhilfe)

            # DIE DOPPELTE ANSICHT. Zweizaehlige Drehsymmetrie laesst die beiden
            # Ueber-Eck-Ansichten der HABS/NPS-Regel zusammenfallen; bei einem Quader
            # sind `sSE` und `nNW` byte-identisch. 24,5 s Diffusion fuer ein Bild, das
            # schon dalag (auf-vis-20260824-12) — und gerade bei den einfachen
            # Demofaellen.
            # SEIT DEM 24.09.2026 MIT TOLERANZ UND AUF DER FLACHEN KARTE (auf-169): Hier stand
            # ein Abgleich exakter Kennungen, und er griff im Betrieb NIE — die Karte kommt
            # flach aus `tiefen_aus_report`, `_sollkennung` erwartete Zeilen und gab still
            # «nicht vergleichbar» zurück; und selbst richtig gelesen unterscheiden sich
            # zwei gegenüberliegende Ansichten eines Quaders um 1e-5 m Rechenrauschen.
            zwilling = _finde_zwilling(gesehen, soll, breite, hoch)
            if zwilling is not None:
                # `**innen`: der Vermerk DIESER Aufgabe, nicht der des Vorbilds. Heute
                # sind beide gleich — alle Aufgaben eines Auftrags tragen denselben
                # Vermerk —, die Zeile ist also gleichwertig zu ihrem Fehlen (Durchsicht
                # 23.09.2026). Bewacht ist die WIRKUNG: Ein Zwilling einer mitgesandten
                # Innenkamera traegt den Vermerk (tests/test_interior_bestellung.py).
                urteile.append(dict(zwilling["urteil"], kamera=kuerzel,
                                    doppelt_von=zwilling["kamera"],
                                    # Die EIGENEN Ebenen — der Multipass lief auch hier;
                                    # die des Vorbilds truegen dessen Kameranamen.
                                    ebenen=ebenen, **innen,
                                    # Der Zwilling ist nicht gerechnet worden; die
                                    # Saetze zu Aufsicht und Bildauftrag traegt sein
                                    # Vorbild.
                                    **{_kosmo_szene.URTEIL_AUFSICHT: None,
                                       _kosmo_szene.URTEIL_BILDAUFTRAG: None,
                                       _kosmo_szene.URTEIL_KAMERAHOEHE: None}))
                _urteil_ablegen(aus, urteile[-1])
                zeiten[str(kuerzel)] = round(time.monotonic() - beginn, 1)
                fort.kamera_fertig(gerechnet=False)
                continue

            # DER BILDAUFTRAG EINER INNENKAMERA (Sammel-Nachprobe auf-20261001-230): KosmoOrbit
            # schickt EINEN Prompt fuer alle Kameras, und der war «… Tageslicht, klarer
            # Himmel». Die Innenkamera bekam darum eine Fassade mit Himmel — das
            # Cycles-Schoenbild derselben Kamera zeigte den Raum. Siehe `_bildauftrag_innen`.
            bildauftrag = _bildauftrag_innen(szene.get("prompt", ""), aufgabe.get("innenraum"),
                                             soll)
            prompt_kamera = bildauftrag["gerechnet"] if bildauftrag else szene.get("prompt", "")
            # DER BESTAND (Splat-Demo 08.10.2026): Koerper mit `extras.role = "existing"`
            # bekommen den Zusatz «ohne Schrift» — siehe `kosmo_szene.BESTAND_ZUSATZ`.
            bestand_auftrag = _kosmo_szene.bildauftrag_bestand(prompt_kamera, bestand)
            if bestand_auftrag:
                prompt_kamera = bestand_auftrag["gerechnet"]

            # DIE STEUERBILDER DER VORSCHAU (Entscheid 104): verkleinerte Kopien neben der
            # Kamera, die Grundlage bleibt, wie Blender sie schrieb. Bei der vollen Guete
            # gehen die Originale hin wie bisher.
            # SEIT auf-20261020-292 (B5) AUCH BEI «VOLL», wenn die bestellte Groesse nicht
            # aufs Raster faellt: Blender rechnet die bestellte Groesse, das Bildmodell eine
            # gerasterte, und sein Bild geht danach auf die bestellte zurueck.
            # SEIT auf-20261020-293 (B3) MIT DER UNTERGRENZE DES MODELLS: Auf einer kleinen
            # Grundlage (480 px) fand die Vorschau das Haus nicht — die Steuerbilder gehen
            # dann hochgerechnet in den KI-Schritt, das Bild danach zurueck.
            steuer = ki_steuerbilder(tiefe, bericht.get("beauty_png"),
                                     aus / (VORSCHAU_ORDNER if vorschau else KI_RASTER_ORDNER),
                                     vorschau=vorschau, lange_seite=vorschau_lange_seite,
                                     mindest_lange_seite=ki_mindest_lange_seite(backbone_name))
            seeds_kamera = seeds_der_kamera(szene, geholt, kuerzel, seeds)
            # DER MESSSCHALTER «UMRISS HALTEN IM LAUF» (Strang Treue): die Freigabemaske der
            # Kamera — nur mit Schalter und Maske; sonst bleibt der Auftrag Wort fuer Wort.
            umriss_freigabe, umriss_vermerk = None, None
            if szene.get("umriss_halten") == "im_lauf":
                from . import umrisshalt as _uh  # noqa: PLC0415
                if maskenbefund.get("maske") is None:
                    umriss_vermerk = {"angewandt": False, "art": _uh.ART_IM_LAUF,
                                      "grund": "keine Bauwerksmaske — ohne sie ist nicht "
                                               "bekannt, wo das Haus steht"}
                else:
                    try:
                        umriss_freigabe = aus / _uh.ORDNER_MASKE / f"{kuerzel}__freigabe.png"
                        umriss_vermerk = _uh.schreibe_freigabe_png(
                            umriss_freigabe, maskenbefund["maske"], breite, hoch)
                    except (OSError, ValueError) as fehler:
                        # Ein Messschalter kostet das Bild nicht: ohne Freigabe rechnet der
                        # Lauf wie ohne Schalter, und der Vermerk sagt warum.
                        umriss_freigabe = None
                        umriss_vermerk = {"angewandt": False, "art": _uh.ART_IM_LAUF,
                                          "grund": f"Freigabe nicht baubar: "
                                                   f"{type(fehler).__name__}: {fehler}"}

            def _rendere_seed(seed, ziel_png):
                # Bei einer verkleinerten Vorschau entsteht das KI-Bild klein neben der
                # Kamera und wird danach auf die Groesse der Grundlage gebracht — die
                # Pruefung misst Punkt fuer Punkt gegen dieselbe Soll-Karte wie bei «voll».
                klein = steuer is not None and steuer["verkleinert"]
                roh_png = (str(aus / (VORSCHAU_ORDNER if vorschau else KI_RASTER_ORDNER)
                               / Path(ziel_png).name) if klein else ziel_png)
                erg = rendern(
                    render.RenderAuftrag(
                        depth_png=steuer["tiefe_png"] if steuer else tiefe,
                        prompt=prompt_kamera,
                        # Vorschau: der Registerwert (auf-20261020-292, Punkt 7), sonst
                        # `faithful` der Bestellung.
                        controlnet_staerke=steuerstaerke_des_laufs(szene),
                        backbone=backbone_name,
                        # Die Bestellung kennt kein Schrittfeld; es gilt die Modellkarte
                        # des Eintrags, sonst 20 (auf-20260930-208) — bei der Vorschau
                        # `vorschau_schritte` des Eintrags (Entscheid 104).
                        schritte=schritte_lauf,
                        beauty_png=(steuer["schoenbild_png"] if steuer
                                    else bericht.get("beauty_png")),
                        seed=seed,
                        ausgabe_png=roh_png,
                        # Messschalter «Cycles-Bild und Tiefe» (Entscheid 117) — None: aus,
                        # und dann ist der Auftrag Wort fuer Wort der von vorher.
                        bildeingang_staerke=szene.get("bildeingang"),
                        # Messschalter «Umriss halten im Lauf» (Strang Treue) — None: aus.
                        umriss_halten_png=(str(umriss_freigabe) if umriss_freigabe
                                           else None),
                    ),
                    modell=_render_modell,
                )
                if erg.get("status") != "ok":
                    raise AbholerError(
                        f"Kamera {kuerzel!r}, seed {seed}: Render {erg.get('status')} — "
                        f"{erg.get('error') or erg.get('maengel')}"
                    )
                if klein:
                    from . import bildschreiben as _bs  # noqa: PLC0415
                    gb, gh = steuer["grundlage_groesse"]
                    _bs.skaliere_png(erg["bild_png"], ziel_png, gb, gh)
                    erg = dict(erg, bild_png=str(ziel_png), ki_bild_klein=erg["bild_png"])
                return erg

            fort.phase("bildmodell")
            ergebnis, urteil, auswahl = _bester_seed(
                seeds_kamera, aus, kuerzel, _rendere_seed,
                lambda png: messen(png, soll_pruefung, breite=breite, hoehe=hoch,
                                   modell=_tiefen_modell, schwelle=grenze,
                                   maske=maskenbefund.get("maske"), **ausblendung),
                maske_da=maskenbefund.get("maske") is not None,
                soll=soll_umriss, breite=breite, hoehe=hoch)
            # DER FARBABGLEICH (Entscheid 117, D1) — nur mit `vis.farbabgleich: true`. Die
            # Pruefung oben hat das KI-Bild OHNE Abgleich gemessen; der Abgleich verschiebt
            # keinen Bildpunkt. Das Original bleibt daneben liegen, und `geom_iou` wird am
            # abgeglichenen Bild ein zweites Mal gemessen, damit der Beweis am Geraet steht.
            # UMRISS HALTEN (Strang Treue) — nur mit `vis.umriss_halten`. «nachher» mischt hier,
            # VOR dem Farbabgleich; «im_lauf» hat im Bildmodell gerechnet und meldet es.
            if szene.get("umriss_halten") == "nachher":
                umriss_vermerk = umriss_halten_der_kamera(
                    ergebnis["bild_png"], bericht.get("beauty_png"), maskenbefund.get("maske"),
                    breite, hoch, aus, urteil_vorher=urteil,
                    messen=lambda png: messen(png, soll_pruefung, breite=breite, hoehe=hoch,
                                              modell=_tiefen_modell, schwelle=grenze,
                                              maske=maskenbefund.get("maske"), **ausblendung))
            elif umriss_freigabe is not None:
                umriss_vermerk = umriss_halten_vermerk_im_lauf(ergebnis, umriss_vermerk)
            farbvermerk = None
            if szene.get("farbabgleich"):
                farbvermerk = farbabgleich_der_kamera(
                    ergebnis["bild_png"], bericht.get("beauty_png"), aus,
                    urteil_vorher=urteil,
                    messen=lambda png: messen(png, soll_pruefung, breite=breite, hoehe=hoch,
                                              modell=_tiefen_modell, schwelle=grenze,
                                              maske=maskenbefund.get("maske"), **ausblendung))
            bilder.append(ergebnis["bild_png"])
            fort.ki_bild_da(kuerzel, ergebnis["bild_png"])
            fort.phase("pruefung")
            anker = None
            maskenanker = None
            if nullprobe:
                # DIE NULLANKER EINMAL JE SOLL-KARTE (auf-20261020-290, Befund 5): Sie
                # haengen allein an Soll-Karte, Maske, Ausblendung und Schaetzer — eine
                # Variante auf derselben Grundlage hat genau diese Eingaben, und bis hierher
                # mass sie die drei Kontrollbilder je Kamera neu (rund 18 s). Gemerkt nach
                # INHALT, nicht nach Namen: andere Eingabe, anderer Schluessel.
                anker, maskenanker = _nullprobe_gemerkt(
                    grundlagen_wurzel,
                    lambda: _nullprobe(
                        aus, soll_pruefung, breite, hoch, bildschreiben=bildschreiben,
                        messen=messen, grenze=grenze, tiefen_modell=_tiefen_modell,
                        maske=maskenbefund.get("maske"), **ausblendung),
                    soll=soll_pruefung, breite=breite, hoehe=hoch, messen=messen,
                    maske=maskenbefund.get("maske"), ausblendung=ausblendung, grenze=grenze)
            # DECKUNG (Video-Befund L4-1, Knoten-Vertrag v0.1.10): Kanten-IoU des KI-Bilds gegen
            # das Grundbild (Cycles) — nur, wenn beide da und gleich gross sind; sonst kein Feld.
            deckung = deckung_der_kamera(ergebnis.get("bild_png"), bericht.get("beauty_png"))
            urteil = dict(urteil, kamera=kuerzel, nullanker=anker,
                          seedauswahl=auswahl,
                          # Welches Bild zu diesem Urteil gehoert. Steht bis zum
                          # 26.08.2026 nur in `bilder`, und dort ohne Zuordnung — bei
                          # einer uebernommenen Ansicht waere sonst nicht mehr
                          # feststellbar, welches Bild gemeint ist.
                          bild_png=ergebnis["bild_png"],
                          # Auch wenn nicht abgebrochen wurde: Die gerechnete Lage
                          # gehoert an das Urteil. Ein Lauf knapp ueber der Schwelle
                          # sieht sonst aus wie einer mit Luft.
                          rahmung=rahmung,
                          # Ob die Geometrie ueberhaupt plausible Masse hat. Der Riegel
                          # dafuer war seit langem gebaut und lief auf DIESEM Weg
                          # nirgends — nachgezaehlt am 26.08.2026.
                          massstab=massstab,
                          # Unter welcher Annahme die Sonne gestellt wurde. Der
                          # Runner berichtet es auch, aber sein Bericht liegt neben
                          # dem Bild und dieses Urteil im Befund — und die
                          # Azimutkonvention ist eine SETZUNG, keine Messung
                          # (auf-20260826-44 fragt danach).
                          sonne=_sonne.aus_bestellung(szene.get("sonne")),
                          # Auf welchem Weg das Bildmodell lief. Seit dem 19.08.2026
                          # gemessen, bis zum 26.08. nirgends geschrieben — und darum
                          # sah ein Lauf, der am freien Kartenspeicher scheiterte, wie
                          # ein Rueckfall im Code aus (auf-vis-20260825-15, Posten 4).
                          geraeteweg=ergebnis.get("geraeteweg"),
                          # WOMIT GERECHNET WURDE (auf-155 F7, zugesagt 29.09.2026):
                          # Modell, Lizenz, ob die Fuehrung ankam — aus dem Ergebnis des
                          # Bildmodells, nicht aus der Bestellung.
                          engine=_engine_aus(ergebnis),
                          # Die Kompositionsprüfung — bis zum 23.08.2026 rief SIE
                          # niemand, obwohl `komposition.py` 1400 Zeilen gerechnetes
                          # Fachwissen trägt. Ein Regelwerk, das nur seine eigenen Tests
                          # beurteilt, beurteilt nichts. Hier bekommt es die Kamera zu
                          # sehen, mit der wirklich gerendert wurde.
                          komposition=komposition,
                          maskenbefund=maskenbefund, maskenanker=maskenanker,
                          kontext_maske=kontext_maske,
                          **({"deckung": deckung} if deckung else {}),
                          # Der Boden DIESER Maskenlage — er wurde seit jeher gemessen
                          # und nie gelesen. Seit `auf-vis-20260824-10` ist er die
                          # entscheidende Zahl: Der Schaetzer hat ein festes Ortsfeld,
                          # und dieselbe Maske verschoben ergibt rho von -0.62 bis +0.65.
                          # Konnte dieser Lauf ueberhaupt bestehen? Aus der RAHMUNG
                          # allein beantwortbar, und zwar VOR dem Renderlauf. Gemessen:
                          # Bei anteil_maske 0.0193 ist geom_iou 0.000183, bei 0.3051
                          # dagegen 0.9323 — Faktor 647 dazwischen (auf-35/auf-13).
                          # Die Kamera rahmt die SZENE, gemessen wird das BAUWERK.
                          torchance=geometrie_qa.torchance(
                              ((urteil.get("rho_maske") or {}).get("anteil_maske"))),
                          bodenabstand=geometrie_qa.rho_gegen_gemessenen_boden(
                              ((urteil.get("rho_maske") or {}).get("gerichtet")),
                              maskenanker),
                          # Was diese Aufnahme BESTENFALLS erreichen kann. Steht neben
                          # dem Score, weil ein Score ohne seinen Deckel nicht sagt, ob
                          # er etwas ueber das BILD oder ueber die SZENE aussagt.
                          erreichbarkeit=_erreichbarkeit_dieser_szene(
                              urteil, schwelle=grenze),
                          einordnung=geometrie_qa.einordnung(
                              urteil.get("score"), anker, schwelle=grenze),
                          belichtung=_belichtung_urteil(
                              ergebnis["bild_png"], stil, rahmen, belichtung_pruefen))
            # DIE ZWEI TORE JE KAMERA — Befund der Durchsicht vom 22.09.2026: Der Block
            # `geometry_gates` war in `kosmo_szene.als_ergebnis` gebaut, auf diesem Weg
            # aber nie gefuellt. Er steht hier am Kameraurteil, weil er so ueber
            # `geometrie_urteil` UND `je_kamera` beide Quellen erreicht, ohne dass eine
            # ihre Schreibfunktion aendern muss. Siehe `_zwei_tore_dieser_kamera`.
            # Bewacht fuer BEIDE Quellen an der geschriebenen Datei: Bruecke und eigene
            # Ablage in `tests/test_vertrag_jede_kamera_spricht.py`.
            urteil[_kosmo_szene.URTEIL_ZWEI_TORE] = _zwei_tore_dieser_kamera(urteil)
            # DIE UMRISSTREUE GILT NICHT, WENN DAS HAUS FEHLT (auf-20261020-295, N2): Bei
            # geom_iou unter 0,1 sagt die Seedwahl nach Kanten nichts ueber das Haus — der
            # Vermerk steht an der Auswahl, der Satz in `verdict.hinweise`.
            # Seit auf-20261021-296: auch bei zu viel «Haus» im Bild oder weit ueber den
            # Umriss gebaut (N1), und `umriss_gilt` steht IMMER, wenn geom_iou gemessen ist —
            # true wie false (N6); ein fehlendes Feld hiess sonst «nicht geprueft» und
            # «gilt» zugleich. `umriss_grund` nur bei false.
            # Mit dem Vermerk «Umriss halten», der erst unten ans Urteil kommt: Bei «im_lauf»
            # zaehlt die Baumasse ausserhalb «so nah wie das Haus» (auf-20261021-309, B1).
            wiedererkannt = _kosmo_szene.wiedererkennung_des_urteils(
                dict(urteil, **{URTEIL_UMRISS_HALTEN: umriss_vermerk})
                if umriss_vermerk is not None else urteil)
            if wiedererkannt is not None and isinstance(urteil.get("seedauswahl"), dict):
                urteil["seedauswahl"] = dict(urteil["seedauswahl"],
                                             umriss_gilt=wiedererkannt["gilt"])
                if not wiedererkannt["gilt"]:
                    urteil["seedauswahl"]["umriss_grund"] = wiedererkannt["grund"]
            urteil["doppelt_von"] = None
            # OB DIE GEOMETRIESTUFE GERECHNET ODER GEHOLT WURDE. Sie steht am
            # Kameraurteil und nicht nur im Multipassbericht, weil `befund_kurz` und
            # jede spaetere Auswertung von hier lesen — und weil eine Messreihe wissen
            # muss, welche Bilder in DIESEM Lauf entstanden sind.
            urteil["zwischenspeicher"] = bericht.get("zwischenspeicher")
            # DIE GERECHNETE POSE (Nr. 68/85) — damit eine Auto-Kamera als feste weiterlebt.
            urteil["pose"] = pose_aus_bericht(bericht)
            urteil["blickfeld"] = blickfeld
            # Der Modellstand steht auch am KAMERAURTEIL und nicht nur im Ergebnissatz:
            # `_urteil_ablegen` schreibt es sofort auf die Platte, und ab dort ueberlebt
            # der Befund jeden Fehler einer spaeteren Kamera. Dieselbe Ueberlegung wie
            # bei `blickfeld` und `zwischenspeicher` eine Zeile darueber.
            urteil["modellstand"] = modellstand
            urteil["ebenen"] = ebenen
            urteil.update(innen)
            # DIE AUFSICHT AM URTEIL (Owner-Entscheid 67, 01.10.2026): nur an einer Kamera,
            # die wirklich gerechnet wurde — der Satz dazu sagt «gerechnet», und das soll
            # stimmen. Am Urteil und nicht als eigener Uebergabewert, aus demselben Grund
            # wie `URTEIL_INNENANSICHT`: Das Kameraurteil reist schon durch beide Quellen.
            urteil[_kosmo_szene.URTEIL_AUFSICHT] = (
                dict(komposition["aufsicht"], kamera=str(kuerzel))
                if komposition.get("aufsicht") else None)
            urteil[_kosmo_szene.URTEIL_BILDAUFTRAG] = (
                dict(bildauftrag, kamera=str(kuerzel)) if bildauftrag else None)
            # DIE HOEHE DER KAMERA (Ergebnis auf-20261022-341, c) — dieselbe Art Auskunft.
            urteil[_kosmo_szene.URTEIL_KAMERAHOEHE] = hoehe_vermerk
            # DIE UMGEBUNG AM URTEIL (Entscheid 76) — ohne Pfad, mit dem verdeckten Anteil
            # DIESER Kamera. Von hier erreicht sie `verdict.hinweise`.
            urteil[_kosmo_szene.URTEIL_KONTEXT] = _kosmo_szene.kontext_vermerk(kontext, bericht)
            # BESTAND FEHLT bei bestellter Umgebung: eine Warnung (Integrator, auf-283).
            urteil[_kosmo_szene.URTEIL_BESTAND] = _kosmo_szene.bestand_vermerk(bestand_auftrag,
                                                                               kontext)
            urteil["messboden"] = messboden_befund
            # SEIT auf-20261020-294 (B5) AUCH BEI «VOLL», wenn hochgerechnet: Die Untergrenze
            # wirkte dort (1024 x 640 statt 960 x 600), und kein Vermerk sagte es.
            urteil[_kosmo_szene.URTEIL_GUETE] = (
                _guete_vermerk(szene, backbone_name, schritte_lauf, auswahl, steuer)
                if vorschau else _guete_vermerk_voll(backbone_name, steuer))
            # UEBERSTRAHLUNG AM HAUS (auf-20261020-292, B1) — nur mit Stimmung: Anteil voll
            # weisser Bildpunkte des Cycles-Bilds auf der Bauwerksmaske. Eine Auskunft, kein
            # Tor; `qa.ueberstrahlt_anteil` im Ergebnis.
            # Seit auf-20261020-293 mit dem Kontrast Haus – Hintergrund, beides in
            # `_stimmungsmessung` (derselbe Aufruf im Zweig «nur Grundlage»).
            urteil.update(_stimmungsmessung(szene, bericht, maskenbefund.get("maske")))
            # DER KONTRAST AM KI-BILD (Ergebnis 334): daneben, nicht statt — dieselbe Maske und
            # derselbe ID-Pass, am gelieferten Bild (nach «Umriss halten nachher» und
            # Farbabgleich, die es an Ort und Stelle ersetzen). Keine Warnung haengt daran.
            kontrast_ki = _kontrast_am_ki_bild(szene, bericht, ergebnis.get("bild_png"),
                                               maskenbefund.get("maske"))
            if kontrast_ki is not None:
                urteil[_kosmo_szene.URTEIL_KONTRAST_KI] = kontrast_ki
            # HAELT DAS KI-BILD DIE FENSTER (Mac-Befund 23.10.2026, «haus-am-hang»)? Am
            # gelieferten Bild, an den Glas-Bildpunkten des ID-Passes — nur mit Glas im ID-Pass;
            # ein Satz nur unter der Schwelle (`kosmo_szene._fenster_eintragen`), kein Tor.
            fenster = fenster_der_kamera(ergebnis.get("bild_png"), bericht,
                                         maskenbefund.get("maske"))
            if fenster is not None:
                urteil[_kosmo_szene.URTEIL_FENSTER] = fenster
            if farbvermerk is not None:
                # Nur mit Schalter — ohne ihn traegt das Urteil keinen neuen Schluessel.
                urteil[URTEIL_FARBABGLEICH] = farbvermerk
            if umriss_vermerk is not None:
                # AUS DER VORGABE FUER VARIANTEN (Entscheid 126) — der Satz am Bild sagt es;
                # ein NICHT angewandter Vorgabe-Schalter bleibt im Vermerk, ohne Satz.
                if ((szene.get("messschalter") or {}).get("umriss_halten") or {}).get(
                        "herkunft") == _kosmo_szene.HERKUNFT_VORGABE:
                    umriss_vermerk = dict(umriss_vermerk, vorgabe=True)
                urteil[URTEIL_UMRISS_HALTEN] = umriss_vermerk
            # WIE DAS BILD ENTSTAND (Vertrag C17 A1): an jedem KI-Lauf, nicht nur mit
            # `vis.bildeingang` — bis dahin stand eine Abweichung nur als Satz im Ergebnis.
            modus = modus_vermerk(ergebnis)
            if modus is not None:
                # SEIT auf-20261021-312 (B3) MIT SATZ, wenn das Bild anders gerechnet wurde als
                # bestellt — im Befund je Kamera; `angewandt.modus` bleibt in seiner Form (C17).
                # Mit «Umriss halten im Lauf» kam das Cycles-Bild ausserhalb des Hauses an —
                # der Satz sagt es (auf-20261022-327, B2).
                satz = _kosmo_szene.modus_satz(
                    kuerzel, modus, ergebnis.get("backbone") or backbone_name,
                    umriss_im_lauf=_kosmo_szene.umriss_im_lauf_angewandt(umriss_vermerk),
                    # Ergebnis 342 (h): mit `vis.bildeingang: false` war nicht 'image_edit'
                    # bestellt, sondern das Abschalten — der Satz sagt das.
                    bildeingang_abgeschaltet=_bildeingang_abgeschaltet(szene))
                urteil[URTEIL_MODUS] = dict(modus, satz=satz) if satz else modus
                # IN GELAEUFIGEN WOERTERN (auf-20261022-336): img2img/txt2img und die wirksame
                # Entrauschstaerke, dazu die Warnung bei einem Rueckfall auf txt2img.
                ki = ki_vermerk(ergebnis, bildeingang_staerke=szene.get("bildeingang"),
                                umriss_im_lauf=_kosmo_szene.umriss_im_lauf_angewandt(
                                    umriss_vermerk), modus_satz=satz,
                                bildeingang_abgeschaltet=_bildeingang_abgeschaltet(szene))
                if ki is not None:
                    urteil[URTEIL_KI] = ki
            if szene.get("bildeingang") is not None:
                # Ebenso der Bildeingang (auf-20261021-298, B1): was gerechnet wurde, aus dem
                # Ergebnis des Bildmodells, nicht aus der Bestellung.
                urteil[URTEIL_BILDEINGANG] = bildeingang_vermerk(ergebnis,
                                                                 szene.get("bildeingang"))
                if _bildeingang_aus_vorgabe(szene):
                    # Aus der Vorgabe fuer Varianten (Entscheid 138) — der Satz am Bild sagt es.
                    urteil[URTEIL_BILDEINGANG]["vorgabe"] = True
            urteile.append(urteil)
            # SOFORT ABLEGEN, nicht am Ende des Auftrags — siehe `_urteil_ablegen`.
            # Ab hier ueberlebt dieses Urteil jeden Fehler einer spaeteren Kamera.
            _urteil_ablegen(aus, urteil)
            flach = _flache_karte(soll)
            if flach is not None:
                gesehen.append({"soll": flach, "breite": breite, "hoehe": hoch,
                                "kamera": kuerzel, "urteil": urteil})
            zeiten[str(kuerzel)] = round(time.monotonic() - beginn, 1)
            fort.kamera_fertig(gerechnet=True)

        # Ein letzter Blick auf den Abbruch, dann 1.0 — das bleibt am Auftrag stehen.
        fort.ende()
        zeiten["gesamt"] = round(time.monotonic() - beginn_gesamt, 1)
        # DIE GRUNDLAGE DIESES LAUFS (Nr. 85): geholt → dieselbe Kennung; gerechnet →
        # abgelegt unter einer neuen. Ohne Ablage (kein --out-wurzel) keine Kennung —
        # eine Kennung, die nichts wiederfindet, waere ein leeres Versprechen.
        grundlage = None
        if geholt is not None:
            grundlage = {"id": geholt["id"], "wiederverwendet": True}
        elif berichte_neu and grundlagen_wurzel is not None:
            kennung = grundlage_kennung(auftrag.get("job_id") or ordner.name, berichte_neu)
            lege_grundlage_ab(grundlagen_wurzel, kennung,
                              job_id=auftrag.get("job_id") or ordner.name,
                              szene=szene, berichte=berichte_neu,
                              seeds=_gewaehlte_seeds(urteile),
                              bestand=bestand, modellstand=modellstand)
            grundlage = {"id": kennung, "wiederverwendet": False}
        # Die gemeldete Zahl traegt mit, wie sie entstanden ist — siehe `_kameraspanne`.
        # Ohne das waere der Uebergang von einer auf drei Kameras eine stille
        # Verschaerfung des Gates gewesen.
        schlechtestes = _schlechtestes(urteile)
        if schlechtestes is not None:
            schlechtestes = dict(schlechtestes, kameraspanne=_kameraspanne(urteile),
                                 # Die zweite Rechnung daneben: dieselbe Auswahl, aber
                                 # gegen den je Kamera GEMESSENEN Rauschboden. Sie
                                 # entscheidet nichts und deckt auf, wenn das Ortsfeld
                                 # des Schaetzers die Reihenfolge dreht.
                                 bodenspanne=_bodenspanne(urteile))

        return {
            "bilder": bilder,
            "geometrie_urteil": schlechtestes,
            "stil_urteil": _stil_urteil_aus_belichtung(urteile, stil),
            "kameras": urteile,
            "zeiten": zeiten,
            # Immer da, wie `status` in `render._ergebnis`: Ein Ergebnissatz mit
            # wechselnden Schluesseln zwingt jeden Auswerter, vor dem Lesen zu
            # verzweigen.
            "uebersprungen": False,
            "grund": "",
            "nur_grundlage": nur_grundlage,
            "grundlage": grundlage,
            # Entscheid 104: nur, wenn bestellt — sonst fehlt das Feld im Ergebnis.
            "guete": szene.get("guete"),
            # Was fuer Stimmung, Kamera und Oberflaeche gerechnet wurde (20.10.2026) — seit
            # auf-20261021-298 (B1) auch die Messschalter, wenn sie gesetzt waren.
            "angewandt": angewandt_mit_messschaltern(
                angewandt_der_szene(szene, drehung_je_kamera=drehungen,
                                    himmel_je_kamera=himmel_je_kamera,
                                    hintergrund_je_kamera=hintergrund_je_kamera), urteile),
            # UNTER WELCHER HOCHACHSE gerendert wurde, und ob sie bestellt oder
            # angenommen war. Eine Zahl gehoert an die Bedingung, unter der sie gemessen
            # wurde — und dies ist die Bedingung, unter der die Geometrie-QA ueberhaupt
            # etwas bedeutet: Unter falscher Annahme sind alle Werte des Laufs
            # gemeinsam verdreht und trotzdem plausibel.
            "hochachse": {"wert": hochachse, "quelle": hochachse_quelle},
            # OB DIESES MODELL TRAEGT, WAS GEBAUT WURDE. Immer da, auch bei
            # `uebersprungen` — ein Ergebnissatz mit wechselnden Schluesseln zwingt jeden
            # Auswerter, vor dem Lesen zu verzweigen (dieselbe Regel wie bei `status`).
            "modellstand": modellstand,
            # Womit gerechnet wurde, fuer den ganzen Auftrag (auf-155 F7). `None`, wenn keine
            # Kamera gerechnet hat — dann fehlen die Felder im Vertrag, statt zu raten.
            "engine": _engine_des_auftrags(urteile),
            # Die bestellten Ebenen aller Kameras (E124, Schritt 1); leer, wenn keine bestellt.
            "ebenen": _ebenen_des_auftrags(urteile),
            # WAS AUS DER IFC WURDE — `None`, wenn keine umgewandelt wurde (glb-Auftrag).
            # Traegt das Urteil des Tors auch dann, wenn es nichts gesperrt hat.
            "umwandlung": umwandlung,
            # Der Innenvermerk des Auftrags, wenn `interior` bestellt war — mit einem
            # Standpunkt aus den Raeumen oder mit mitgesandten Kameras (23.09.2026).
            "innenansicht": next((a.get("innenraum") for a in aufgaben
                                  if a.get("innenraum")), None),
        }

    def verarbeite(auftrag: dict) -> dict:
        # EIN BILDMODELL JE AUFTRAG (07.10.2026, auf-20261001-221): alle Kameras und
        # Startwerte dieser Bestellung rechnen mit EINEM geladenen Modell; am Ende wird es
        # freigegeben, auch nach einem Fehler. Wirkt nur, wenn `rendere` selbst laedt —
        # `tools/abholen.py` uebergibt sein EinmalGeladen als `_render_modell`, und fuer
        # diesen Weg aendert sich nichts.
        with render.ein_modell_je_auftrag():
            return _verarbeite_einen(auftrag)

    return verarbeite


# --------------------------------------------------------------------------------------
# Was `verarbeiter` weiterreicht — und was nicht
# --------------------------------------------------------------------------------------
#
# **Der Anlass ist derselbe wie an der Nachbarnaht** (`kosmo_szene.DURCHGEREICHT`): Am
# 23.08.2026 hat dieses Projekt zweimal an einem Tag denselben Fehler gemacht, beide Male
# an einer Naht. Die Brennweite war im Kern längst einstellbar und kam an der Aussenkante
# trotzdem nicht durch; der Geländestand ebenso. Beide Male hiess es «einstellbar», und
# beide Male stimmte das im Modul und nicht im Betrieb.
#
# **Einstellbar ist ein Versprechen, das man an der Naht prüft, nicht am Modul.** Gezählt
# am 26.08.2026: `glb_zu_multipass` hat 18 echte Einstellungen, `verarbeiter` reicht 12
# durch; `RenderAuftrag` hat 12 Felder, gesetzt werden 7. Nirgends stand, welche der zehn
# Absicht sind und welche Lücken — und genau diese dritte Möglichkeit, «steht nirgends»,
# ist die bequemste.
#
# Die Tabellen erfinden keine neue Arbeit. Sie **sammeln** vier bereits bekannte offene
# Punkte an der Naht, an der sie wirken, statt sie über drei Dokumente zu verteilen.

#: Parameter von :func:`aiimaging.seams.glb_zu_multipass`, die **keine Einstellung** sind.
#:
#: ``glb_path`` und ``out_dir`` sind positionell und beschreiben, woran gearbeitet wird;
#: ``_starte`` ist die Testnaht. Sie stehen hier benannt und nicht als Zahl im Test —
#: eine Ausnahme ohne Begründung ist ein Loch mit Namen.
MULTIPASS_KEINE_EINSTELLUNG = ("glb_path", "out_dir", "_starte")

#: Einstellungen des Multipass, die **ankommen** — mit der Stelle, an der sie herkommen.
MULTIPASS_DURCHGEREICHT = {
    "up_axis": "verarbeiter(up_axis=…); ein Auftrag mit eigener `hochachse` schlaegt sie",
    "kamera_huellbox": "verarbeiter(kamera_huellbox=…). Der SCHALTER ist seit dem "
                       "26.08.2026 da, die HERKUNFT seit dem 01.09.2026: "
                       "`aiimaging.glbbox.bauwerksbox(glb)` liefert sie in 0,08 s "
                       "ohne Blender (Weg b). Offen ist damit nicht mehr der Weg, "
                       "sondern die REGEL: Auf der Bestandsdatei vom 28.08.2026 "
                       "greift die Namensregel kaum (-2,3 % statt -34,5 %), weil "
                       "deren Gelaende `Toposolid` heisst. Wirkung mit tauglicher "
                       "Box: anteil_bauwerk 0,0788 ohne, 0,1730 mit. `auf-41` (G3)",
    "timeout": "verarbeiter(zeitdeckel_s=…), Vorgabe ZEITDECKEL_S. Die alte Begruendung "
               "fuer die Luecke — «hohe Samples sprengen den Deckel» — ist am "
               "26.08.2026 gemessen widerlegt; siehe ZEITDECKEL_S",
    # Seit dem 26.08.2026 nachmittags. Sie standen vorher NIRGENDS in diesen Tabellen,
    # weil `seams.glb_zu_multipass` sie gar nicht kannte — die Naht setzte sie nie, und
    # damit fehlten sie auch der Zaehlung. Aufgefallen beim Abgleich der 23
    # argparse-Schalter des Runners gegen den Text von `seams.py`.
    "deckungsgrad": "verarbeiter(deckungsgrad=…), None heisst Vorgabe des Runners",
    "augenhoehe": "verarbeiter(augenhoehe=…), None heisst Vorgabe des Runners",
    "bias_grad": "verarbeiter(bias_grad=…), None heisst Vorgabe des Runners",
    "aufloesung": "szene['aufloesung'] aus der Bestellung",
    "hoehe": "szene['hoehe'] aus der Bestellung",
    "samples": "szene['samples'] aus der Bestellung",
    "kamera": "je Kameraaufgabe: aufgabe['richtung']",
    "kamera_modus": "verarbeiter(kamera_modus=…), Vorgabe MODUS_SHIFT",
    "gelaende_z": "verarbeiter(gelaende_z=…) bzw. tools/abholen.py --gelaende-z",
    "sonne": "szene['sonne'] — seit 26.08.2026, siehe aiimaging.sonne",
    "auge": "je Kameraaufgabe: aufgabe['auge'], wenn die Bestellung Zahlen mitschickt",
    "blick_auf": "je Kameraaufgabe: aufgabe['blick_auf']",
    "brennweite": "je Kameraaufgabe: aufgabe['brennweite_mm']",
    "stillstand_frist_s": "verarbeiter(stillstand_frist_s=…)",
    # Seit 08.10.2026 (Owner-Entscheid 76), Feldnamen vom Integrator.
    "kontext_ply": "szene['kontext']['ply'] aus RenderScene.context.ply "
                   "(kosmo_szene.kontext_aus_szene); nur wenn bestellt. Seit 13.10.2026 "
                   "(Entscheid 79) das daraus gerechnete NETZ (seams.kontext_vorbereiten); "
                   "ohne Splat-Bruecke der Splat selbst als Kugel-Notloesung",
    "kontext_matrix": "szene['kontext']['matrix'] aus RenderScene.context.transform "
                      "(16 Zahlen zeilenweise, glTF-Welt); fehlt sie, die Einheit",
    # Seit auf-20261008-271: der Ausschnitt auch ohne Gelaende.
    # Seit 20.10.2026 (Knoten «Stimmung», Entscheide 107/110/113): das Himmelsbild der
    # bestellten Stimmung, aus `render.environment` ueber `kosmo_szene.umgebung_aus_szene`.
    "umgebung_hdr": "umgebung_einstellungen(szene) ← render.environment (Datei am Heim-PC)",
    # Seit 20.10.2026 (Knoten «Kamera»): `cameras_auto.abstand {art: 'fest'}`.
    "abstand_fest_m": "kamerawerte_des_auftrags(szene) ← cameras_auto.abstand.meter",
    # Seit 20.10.2026 (Knoten «Material»): die Wahl je Art als JSON im Auftragsordner.
    "materialien_json": "materialwahl_ablegen(ziel, szene) ← render.materialien",
    # Bis 20.10.2026 STEHENGEBLIEBEN («der Runner rechnet ihn selbst») — das gilt weiter fuer
    # jede Richtungskamera. Neu: eine MITGESANDTE Kamera mit `perspektive: 'senkrecht'`
    # (Entscheid 109) bekommt ihn hier gerechnet (`senkrecht_gestellt`, kameras.shift_aus_ziel).
    "shift_y": "senkrecht_gestellt(aufgabe) ← CameraSpec.perspektive 'senkrecht'",
    "umgebung_staerke": "umgebung_einstellungen(szene) ← render.environment.intensitaet",
    "umgebung_drehung": ("umgebung_einstellungen(szene) ← render.environment.rotationGrad, nur "
                         "wenn bestellt (sonst dreht der Runner je Kamera, auf-20261020-294 B1)"),
    "umgebung_weiss": "umgebung_einstellungen(szene) ← render.environment.preset 'weiss'",
    # Seit auf-20261020-292: Belichtung und Toenung je Stimmung (Daten in aiimaging.stimmung).
    "umgebung_belichtung": "umgebung_einstellungen(szene) ← stimmung.STIMMUNGEN[preset]"
                           "['belichtung_ev']",
    "umgebung_toenung": "umgebung_einstellungen(szene) ← stimmung.toenung_fuer(kelvin der "
                        "Stimmung); fehlt ohne Farbtemperatur",
    # Seit auf-20261020-293: Licht mit Schatten je Stimmung (Daten in aiimaging.stimmung).
    "umgebung_licht": "umgebung_einstellungen(szene) ← stimmung.licht_der_stimmung(preset) "
                      "(Sonne, Fuelllicht, Look, Hintergrundabstand, Grau der Platte) als JSON",
    "kamera_ausschnitt": "_ausschnitt_ohne_box(...) — nur Richtungskamera ohne eigene Box, "
                         "wenn die Rahmung meldet: Bauwerk = Szene",
}

#: Einstellungen, die `verarbeiter` **nicht** setzt — mit dem Grund und dem, was fehlt.
#:
#: ``vorgabe`` ist der Wert, der stattdessen gilt. Der Test hält ihn **gegen die wirkliche
#: Signatur**: Ändert jemand ``beauty`` auf ``False`` oder ``timeout`` auf 300, wird er
#: rot. Eine Tabelle, die von Hand gepflegt werden muss, veraltet — an diesem einen Tag
#: schon zweimal nachgewiesen.
MULTIPASS_STEHENGEBLIEBEN = {
    "beauty": {
        "vorgabe": True,
        "absicht": True,
        "grund": "Der Vorgabewert ist der einzige, der auf diesem Weg trägt: "
                 "`verarbeiter` liest `bericht['beauty_png']` als `RenderAuftrag."
                 "beauty_png`. Mit `False` fiele die ganze Kette still von "
                 "Bildbearbeitung auf reines Text-zu-Bild zurück.",
        "noetig": "NICHTS. Wer den Beauty-Pass abschaltet, schaltet damit den "
                  "Betriebsmodus der ganzen Kette um und muss das ausdrücklich tun.",
    },
    "material_id": {
        "vorgabe": True,
        "absicht": True,
        "grund": "`_maske_bauen` baut die Bauwerksmaske aus `material_id_png`. Ohne sie "
                 "gibt es weder rho über der Maske noch die Auswahl unter drei "
                 "Startwerten — und `_bester_seed` fährt dann nur einen.",
        "noetig": "NICHTS. Ohne Maske gäbe es kein zweites Bein des Paartests.",
    },
    "herzschlag_takt_s": {
        "vorgabe": 2.0,
        "absicht": True,
        "grund": "Der Vorgabewert IST die eingeschaltete Wache, gemessen am 20.08.2026 "
                 "(`auf-20260820-19`: 88 Schläge, längste Lücke 2,10 s). Der einzige "
                 "andere sinnvolle Wert wäre `None`, und das hiesse: Wache aus.",
        "noetig": "NICHTS. Ein anderer Takt bräuchte eine Messung, die zeigt, dass die "
                  "heutige Wache zu grob oder zu teuer ist — beides ist widerlegt.",
    },
}

#: Felder von :class:`aiimaging.render.RenderAuftrag`, die `verarbeiter` **setzt**.
RENDER_DURCHGEREICHT = {
    "depth_png": ("der normalisierte Tiefenpass aus dem Multipass — bei der Vorschau "
                  "eine verkleinerte Kopie (vorschau_steuerbilder)"),
    "prompt": "szene['prompt'] — bereits übersetzt (kosmo_szene.lies_szene)",
    "backbone": ("gerechnetes_backbone: bei vis.guete 'vorschau' immer "
                 "backbone.VORSCHAU_BACKBONE, sonst szene['backbone'], sonst "
                 "render.VORGABE_BACKBONE"),
    "controlnet_staerke": "szene['controlnet_staerke'] aus 'faithful'",
    "beauty_png": "bericht['beauty_png'] — schaltet den Bildbearbeitungsmodus ein",
    "seed": ("je Durchgang aus VORGABE_SEEDS, siehe _bester_seed; genau einer bei vis.seed "
             "oder bei der Vorschau (seeds_der_kamera)"),
    "ausgabe_png": "Ablageort je Kamera und Startwert",
    "bildeingang_staerke": ("szene['bildeingang'] aus dem Messschalter vis.bildeingang "
                            "(Entscheid 117) — None, wenn nicht gesetzt"),
    "umriss_halten_png": ("Freigabemaske der Kamera aus umrisshalt.schreibe_freigabe_png, nur "
                          "mit vis.umriss_halten 'im_lauf' (Strang Treue) — sonst None"),
}

#: Felder, die `verarbeiter` **nicht** setzt — mit dem Grund und dem, was fehlt.
RENDER_STEHENGEBLIEBEN = {
    "negativ_prompt": {
        "vorgabe": "",
        "absicht": True,
        "grund": "Anschliessen wäre hier der SCHLECHTERE Zustand, und das ist gemessen: "
                 "`z-image-turbo` läuft mit `fuehrung = 0.0`, und unterhalb 1.0 ist die "
                 "klassifikatorfreie Führung aus. Der negative Prompt stünde dann im "
                 "Protokoll und änderte keinen Bildpunkt — eine Angabe, die aussieht, "
                 "als hätte sie gewirkt. `negativ_lage` meldet die Lage bereits.",
        "noetig": "Ein Backbone mit Führung über 1.0, oder der Entscheid, die sieben "
                  "Negativ-Prompts der Stile zu löschen. Steht als Frage in `auf-38`.",
    },
    "fuehrung": {
        "vorgabe": None,
        "absicht": True,
        "grund": "`None` heisst: die des Backbones. Ein Wert hier überstimmte eine "
                 "gemessene Modelleigenschaft mit einer Setzung.",
        "noetig": "NICHTS, solange die Führung am Backbone-Eintrag steht. Wer sie hier "
                  "setzen wollte, müsste erst begründen, warum er es besser weiss.",
    },
    "modell_wurzel": {
        "vorgabe": None,
        "absicht": True,
        "grund": "Auflösung über `$AIIMAGING_MODELLE` — die Umgebung entscheidet, wo "
                 "Gewichte liegen, nicht die Bestellung. Seit dem 26.08. meldet "
                 "`render.modellwurzel_lage`, wenn der Pfad nicht existiert.",
        "noetig": "NICHTS. Ein Pfad aus der Bestellung wäre Regel 3 gefährlich nahe — "
                  "er trüge einen Rechnernamen durch die Naht.",
    },
    "schritte": {
        "vorgabe": 20,
        "absicht": False,
        # SEIT 30.09.2026 TEILWEISE GESCHLOSSEN: `Backbone.schritte_vorgabe` gibt es; belegt
        # ist es für qwen-image-2.1 (40, Modellkarte, auf-208). Für z-image-turbo nicht
        # gesetzt — die 8 aus der Registry-Notiz sind nicht gegen 20 gemessen.
        # SEIT 20.10.2026 (Entscheid 104) rechnet die VORSCHAU mit den 8 Schritten
        # (`Backbone.vorschau_schritte`, `schritte_des_laufs`); die volle Güte bleibt bei 20,
        # bis Auftrag 288 die Frage misst.
        "grund": "Eine LÜCKE gegen die eigene Registry: `backbone.py` sagt zu "
                 "`z-image-turbo` wörtlich «destilliert, auf 8 Schritte OHNE "
                 "klassifikatorfreie Führung trainiert». Der Vorgabewert ist 20, und es "
                 "gibt am Backbone-Eintrag kein Feld, über das die 8 je greifen könnten. "
                 "Das sind 2,5-fache Rechenzeit gegen eine dokumentierte Modellangabe — "
                 "ungemessen, in beide Richtungen.",
        "noetig": "Ein Feld `schritte` am Backbone-Eintrag, und eine Messung, ob 8 "
                  "Schritte auf diesem Modell wirklich reichen. Der fremde Vertrag "
                  "trägt dafür kein Feld — gefragt als F5 in `auf-44`.",
    },
    "denoise": {
        "vorgabe": 0.6,
        "absicht": False,
        "grund": "Eine LÜCKE, und eine inhaltlich schwere: Der Bildbearbeitungsmodus ist "
                 "auf diesem Weg IMMER an, weil `beauty_png` gesetzt wird. `denoise` "
                 "bestimmt damit, wieviel vom Blender-Render überlebt — und zusätzlich "
                 "die Zahl der wirklich gerechneten Schritte (`schritte × denoise`). Die "
                 "Bestellung kann `faithful` auf `controlnet_staerke` abbilden; den "
                 "zweiten, gleich starken Regler kann sie nicht.",
        "noetig": "Dieselbe Auskunft wie bei `schritte`: was `faithful` steuern soll. "
                  "`auf-44`, F5.",
    },
}


#: Bilder aus dem Multipass, die VOR dem Renderlauf ganz da sein muessen.
#:
#: ``depth_png`` ist die Konditionierung — ohne sie gibt es keinen Lauf. ``beauty_png``
#: geht im Bildbearbeitungsmodus als ``image`` mit hinein. ``material_id_png`` traegt die
#: Maske. Alle drei werden von einem Subprozess geschrieben, und alle drei werden erst
#: Sekunden spaeter gelesen.
# --------------------------------------------------------------------------------------
# Der Zwischenspeicher um den Multipass
# --------------------------------------------------------------------------------------
#
# **Warum er sich lohnt, in Zahlen dieser Umgebung** (26.08.2026, Blender 4.2.1 LTS, CPU,
# der synthetische Testbau 8 × 5 × 3 m):
#
#     256 px,   8 Samples:   2,1 s
#     800 px,  32 Samples:   7,5 s
#    1600 px, 128 Samples:  40,0 s      ← die Vorgaben des Vertrags
#
# Drei Kameras sind damit **zwei Minuten Blender je Auftrag** — auf einem trivialen
# Quader. Und jeder Lauf, der nur den Prompt ändert, zahlt sie erneut: Der Abholer fährt
# die Stufen als gerade Abfolge, ohne Gedächtnis. Für eine Messreihe über Prompts oder
# Stilstärken ist das der ganze Kostenblock.
#
# **Die Voraussetzung ist gemessen und nicht angenommen.** Zweimal dasselbe gerechnet:
#
#   * `ifc_zu_glb` ist **byte-gleich** reproduzierbar. Der Schlüssel über den glb-INHALT
#     ist damit stabil — das ist die Bedingung, an der ein Inhalts-Cache sonst still
#     scheitert.
#   * `glb_zu_multipass` ist **pixelgleich**, aber NICHT bytegleich: Blender stempelt die
#     Uhrzeit in jede Ausgabe (`tEXt Date` im PNG, `Date`-Attribut im EXR). Gemessen: drei
#     von 30 659 Bytes im EXR, 33 von 64 235 im PNG — und die Bilddaten selbst identisch.
#
# **Die zweite Messung ist die wichtigere**, und sie hat eine Folge über diesen Cache
# hinaus: *Byte-Gleichheit ist bei Blender-Ausgaben kein Mass für Gleichheit.* Wer einen
# Treffer dadurch prüfen wollte, dass er die Ausgaben neu hasht, bekäme **nie** einen.
# `graph.ArtefaktCache` prüft darum die **Existenz** der zugesagten Dateien, und das ist
# hier nicht Bequemlichkeit, sondern das einzig Richtige.

#: Einstellungen des Multipass, die **nicht in den Schlüssel** gehören — mit dem Grund.
#:
#: Sie ändern nicht das Bild, sondern den Betrieb. Stünden sie im Schlüssel, verwürfe eine
#: geänderte Wachfrist den ganzen Zwischenspeicher, obwohl sich am Ergebnis nichts ändert.
#:
#: Die Liste ist die **Umkehrung** von `MULTIPASS_DURCHGEREICHT`: Dort steht, was ankommt;
#: hier, was ankommt und trotzdem folgenlos für das Bild ist. Beides gehört benannt — eine
#: Auslassung ohne Begründung ist ein Loch mit Namen.
MULTIPASS_NICHT_IM_SCHLUESSEL = {
    "out_dir": "Wohin geschrieben wird. Genau darum geht es: Derselbe Schnitt in einem "
               "anderen Ordner ist dasselbe Bild.",
    "timeout": "Ein Abbruchdeckel. Er entscheidet, OB ein Lauf abgebrochen wird, nicht "
               "WAS er rechnet — dasselbe Bild unter einem anderen Deckel ist dasselbe Bild.",
    "stillstand_frist_s": "Die Wachfrist. Sie beobachtet den Lauf und ändert ihn nicht.",
    "herzschlag_takt_s": "Der Herzschlag des Runners — reine Betriebsanzeige.",
    "_starte": "Die Testnaht.",
}


def _blender_fassung(_lauf=None) -> str:
    """Welche Blender-Fassung hier rechnet — für den Schlüssel.

    **Sie gehört hinein, und das ist gemessen begründbar:** Dieses Projekt fährt auf 4.2
    *und* 5.2, und zwei Fassungen sind zwei Renderer. Ein Eintrag, den 4.2 erzeugt hat,
    unter 5.2 als Treffer zu nehmen hiesse, ein Bild zu benutzen, das dieser Rechner so
    nie erzeugt hätte — und der Unterschied fiele erst am fertigen Bild auf.

    Kostet 0,22 s und wird **einmal je Lauf** abgefragt, nicht je Kamera.

    Lässt sich die Fassung nicht feststellen, ist das **kein Abbruch** und auch kein
    stiller Rückfall auf «egal»: Es kommt eine Marke in den Schlüssel, die zu keinem
    ermittelten Wert passt. Der Lauf rechnet dann neu, statt einen fremden Eintrag zu
    nehmen — *nicht feststellbar ist kein Abbruchgrund, aber auch keine Erlaubnis.*
    """
    import subprocess                                        # noqa: PLC0415

    lauf = _lauf or (lambda: subprocess.run(
        [_seams.finde_blender(), "--version"], capture_output=True, text=True, timeout=60))
    try:
        ausgabe = lauf().stdout or ""
    except Exception as fehler:                              # noqa: BLE001
        return f"unbekannt:{type(fehler).__name__}"
    erste = next((z.strip() for z in ausgabe.splitlines() if z.strip()), "")
    return erste or "unbekannt:leer"


# --------------------------------------------------------------------------------------
# Die Grundlage (Owner-Grundsatz Nr. 85, Demolauf 16.10.2026; Vertrag 20.10.2026)
# --------------------------------------------------------------------------------------
#
# «Ein Render = EINE Blender-Grundlage (Kamera, Geometrie, Passes) → mehrere KI-Varianten,
# deckungsgleich.» Bis zum 20.10.2026 rechnete jeder Auftrag Blender und bei `cameras: auto`
# die Standpunkte neu, und der KI-Schritt zog je Kamera drei Startwerte und behielt den
# «besten» — Morgen- und Abendbild zeigten darum verschiedene Bilder (Nr. 84).
#
# Seither legt jeder Lauf, der Blender rechnet, seine Multipass-Berichte unter einer
# Kennung ab; ein Auftrag mit `vis.grundlage` holt sie und rechnet nur noch den KI-Schritt.
# Abgelegt werden BERICHTE (sie zeigen auf die Dateien im Ausgabeordner des ersten Laufs),
# nicht Kopien: Die Dateien liegen dort ohnehin, und eine zweite Kopie liefe auseinander.

#: Der Unterordner der Ausgabewurzel, in dem die Grundlagen liegen.
GRUNDLAGEN_ORDNER = "_grundlagen"
#: Das Schema einer abgelegten Grundlage.
GRUNDLAGE_SCHEMA = "aiimaging.grundlage/v1"
#: Woran eine Grundlage zum Auftrag passen muss (Auflage 4 des Integrators, 20.10.2026):
#: Wer ueber `vis_render` ohne Knoten bestellt, sieht keine Anzeige «veraltet» — also lehnt
#: der Heim-PC selbst ab, laut und mit Grund.
#: Seit 20.10.2026 auch die Stimmung (`umgebung`, Entscheid 110): Eine Variante mit anderer
#: Stimmung braucht ihre eigene Grundlage — das Himmelsbild steht im Cycles-Bild.
#: Ebenso die Materialien je Art (Knoten «Material», 20.10.2026): Sie stehen im Cycles-Bild.
GRUNDLAGE_MUSS_PASSEN = ("aufloesung", "hoehe", "samples", "kameras", "kameras_auto",
                         "umgebung", "materialien")


#: Die Kamerafelder unter :data:`GRUNDLAGE_MUSS_PASSEN` — sie passen auch als TEILMENGE
#: (Geräteprobe R56, 23.10.2026), siehe :func:`kameras_weichen_ab`.
GRUNDLAGE_KAMERAFELDER = ("kameras", "kameras_auto")


def kameras_weichen_ab(grundlage: dict, auftrag: dict) -> list[str]:
    """Welche Kamerafelder des Auftrags nicht zur Grundlage passen — ``[]``, wenn sie passen.

    Beide Seiten in der Form von :func:`_vergleichbar` (``bestellt`` der Grundlage bzw. die
    gelesene Szene). **Anlass (Geräteprobe R56, 23.10.2026):** Eine Variante mit 2 von 3
    Kameras einer Grundlage galt als «Kameras weichen ab», obwohl die Grundbilder dieser zwei
    Kameras längst da lagen. Seither passt eine **Teilmenge**:

    * mitgesandte Kameras (``kameras`` als Liste, ``kameras_auto`` gleich): jede bestellte
      Kamera steht in der Grundlage mit derselben Kennung (``kuerzel``) und Wort für Wort
      derselben Pose (Auge, Ziel, Brennweite, Achse, Perspektive). Ohne Kennung keine
      Zuordnung — dann gilt nur das Ganze.
    * ``kameras_auto``: alle Werte gleich, die Richtungen eine Teilmenge.

    Eine neue, verschobene oder umbenannte Kamera passt weiter nicht — die Grundbilder wären
    ein anderer Standpunkt.
    """
    ak, nk = grundlage.get("kameras"), auftrag.get("kameras")
    aa, na = grundlage.get("kameras_auto"), auftrag.get("kameras_auto")
    ganz = [f for f in GRUNDLAGE_KAMERAFELDER
            if _vergleichbar(grundlage.get(f)) != _vergleichbar(auftrag.get(f))]
    if not ganz:
        return []
    if ganz == ["kameras"] and isinstance(ak, list) and isinstance(nk, list) and nk:
        alt = {k.get("kuerzel"): k for k in ak if isinstance(k, dict)}
        kuerzel = [k.get("kuerzel") for k in nk if isinstance(k, dict)]
        if (len(alt) == len(ak) and None not in alt and len(kuerzel) == len(nk)
                and None not in kuerzel and len(set(kuerzel)) == len(kuerzel)
                and all(_vergleichbar(alt.get(k.get("kuerzel"))) == _vergleichbar(k)
                        for k in nk)):
            return []
    if ganz == ["kameras_auto"] and isinstance(aa, dict) and isinstance(na, dict):
        ar, nr = aa.get("richtungen"), na.get("richtungen")
        ohne = lambda d: _vergleichbar({f: v for f, v in d.items() if f != "richtungen"})  # noqa: E731
        if (isinstance(ar, list) and isinstance(nr, list) and nr
                and len(set(nr)) == len(nr) and set(nr) <= set(ar) and ohne(aa) == ohne(na)):
            return []
    return ganz


def grundlage_weicht_ab(grundlage: dict, auftrag: dict) -> list[str]:
    """Die Felder aus :data:`GRUNDLAGE_MUSS_PASSEN`, in denen der Auftrag von der Grundlage
    abweicht — die Kameras mit :func:`kameras_weichen_ab` (Teilmenge passt, R56)."""
    abweichend = [f for f in GRUNDLAGE_MUSS_PASSEN if f not in GRUNDLAGE_KAMERAFELDER
                  and _vergleichbar(grundlage.get(f)) != _vergleichbar(auftrag.get(f))]
    kamera = set(kameras_weichen_ab(grundlage, auftrag))
    return [f for f in GRUNDLAGE_MUSS_PASSEN if f in abweichend or f in kamera]


def grundlage_kennung(job_id: str, kuerzel) -> str:
    """Die Kennung einer Grundlage: ``gl-`` und 16 Hexzeichen, aus Auftrag und Kameras."""
    import hashlib
    import json
    roh = json.dumps({"job": str(job_id), "kameras": sorted(map(str, kuerzel))},
                     sort_keys=True)
    return "gl-" + hashlib.sha256(roh.encode("utf-8")).hexdigest()[:16]


def _grundlage_pfad(wurzel, kennung: str) -> Path:
    if not _kosmo_szene.GRUNDLAGE_KENNUNG.match(str(kennung)):
        raise AbholerError(f"Keine Grundlage-Kennung: {kennung!r}.")
    return Path(wurzel) / f"{kennung}.json"


def _vergleichbar(wert):
    """Ein Wert in der Form, in der er auch nach JSON hin und zurueck aussieht."""
    import json
    return json.loads(json.dumps(wert, sort_keys=True, default=str))


def lege_grundlage_ab(wurzel, kennung: str, *, job_id, szene: dict, berichte: dict,
                      seeds: dict | None = None, bestand: dict | None = None,
                      modellstand: dict | None = None) -> Path:
    """Die Grundlage eines Laufs ablegen — atomar, damit nie eine halbe gelesen wird.

    ``seeds`` (``{kuerzel: startwert}``, seit 20.10.2026) ist der Startwert, den jede Kamera
    dieses Laufs behalten hat. Eine Vorschau auf dieser Grundlage ohne ``vis.seed`` rechnet
    genau ihn (Entscheid 104) — sonst stuende ihr Bild neben einem anderen Wurf.

    ``bestand`` und ``modellstand`` (seit 21.10.2026) sind, was der Lauf ueber das Modell
    wusste. Eine Variante ohne Modelldatei (``vis.grundlage``, leerer ``geometry.path``)
    nimmt sie von hier — sonst fehlte ihr der Bestandszusatz im Prompt, und sie waere ein
    anderer Bildauftrag als eine Variante mit Modell.
    """
    import json
    ziel = _grundlage_pfad(wurzel, kennung)
    ziel.parent.mkdir(parents=True, exist_ok=True)
    satz = {"schema": GRUNDLAGE_SCHEMA, "id": kennung, "job_id": str(job_id),
            "bestellt": {f: _vergleichbar(szene.get(f)) for f in GRUNDLAGE_MUSS_PASSEN},
            "sonne": _vergleichbar(szene.get("sonne")),
            "seeds": {str(k): int(v) for k, v in (seeds or {}).items()
                      if isinstance(v, int) and not isinstance(v, bool)},
            "kameras": [{"kuerzel": str(k), "bericht": _vergleichbar(b)}
                        for k, b in berichte.items()],
            "bestand": _vergleichbar(bestand), "modellstand": _vergleichbar(modellstand),
            # MIT ODER OHNE HIMMEL (Entscheid 126): steht im Cycles-Bild der Grundlage. Eine
            # Grundlage von vor dem 21.10.2026 kennt das Feld nicht — sie ist ohne Himmel.
            "himmel_sichtbar": szene.get("himmel_sichtbar") is True}
    tmp = ziel.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(satz, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(ziel)
    return ziel


def lies_grundlage(wurzel, kennung: str, szene: dict) -> dict:
    """Die abgelegte Grundlage — geprueft gegen den Auftrag, sonst laut abgewiesen.

    Abgewiesen wird, wenn die Kennung unbekannt ist, wenn eine ihrer Dateien fehlt, oder
    wenn Aufloesung, Hoehe, Samples oder Kameras des Auftrags nicht die der Grundlage sind
    (Auflage 4). **Nie** wird still neu gerechnet: Eine Variante auf einer anderen
    Grundlage waere genau die nicht deckungsgleiche, gegen die Nr. 85 antritt.
    """
    import json
    if wurzel is None:
        raise AbholerError(
            f"vis.grundlage {kennung!r} bestellt, aber dieser Abholer hat keine Ablage fuer "
            f"Grundlagen (kein --out-wurzel). Ohne Ablage gibt es nichts wiederzuverwenden.")
    pfad = _grundlage_pfad(wurzel, kennung)
    if not pfad.is_file():
        raise AbholerError(
            f"Grundlage {kennung!r} ist hier nicht bekannt. Bitte zuerst «Grundlage rendern» "
            f"(oder einen Lauf ohne vis.grundlage) — neu gerechnet wird nicht still, weil die "
            f"Variante sonst nicht deckungsgleich waere.")
    satz = json.loads(pfad.read_text(encoding="utf-8"))
    # Die Kameras passen auch als Teilmenge (Geräteprobe R56, `kameras_weichen_ab`).
    abweichend = grundlage_weicht_ab(satz.get("bestellt") or {}, szene)
    if abweichend:
        raise AbholerError(
            f"Grundlage {kennung!r} passt nicht zum Auftrag: {', '.join(abweichend)} "
            f"{'weicht' if len(abweichend) == 1 else 'weichen'} ab. Eine Variante entsteht "
            f"aus DERSELBEN Grundlage — bitte die Grundlage neu rendern oder die Werte der "
            f"Grundlage bestellen.")
    for eintrag in satz.get("kameras") or ():
        bericht = eintrag.get("bericht") or {}
        fehlt = [f for f in ("depth_png", "beauty_png")
                 if not (isinstance(bericht.get(f), str) and Path(bericht[f]).is_file())]
        if fehlt:
            raise AbholerError(
                f"Grundlage {kennung!r}, Kamera {eintrag.get('kuerzel')!r}: "
                f"{', '.join(fehlt)} fehlt auf der Platte. Die Grundlage ist nicht mehr "
                f"vollstaendig — bitte neu rendern.")
    return satz


def himmel_der_grundlage(szene: dict, geholt: dict) -> tuple[dict, str | None]:
    """``(szene, satz)`` — ``himmel_sichtbar`` einer Variante an ihre Grundlage gehalten.

    Der Himmel steht im Cycles-Bild der GRUNDLAGE (Lichtdaten an Blender); eine Variante
    rechnet kein Blender. Seit Entscheid 126 ist der Himmel Vorgabe — eine Variante auf einer
    Grundlage OHNE Himmel (vor 126 gerechnet, oder mit ``false`` bestellt) waere sonst still
    ein Bild, das «Himmel» meldet und den Verlauf zeigt.

    * Kam der Wert aus der **Vorgabe** (nicht bestellt): es gilt der Wert der Grundlage, mit
      Satz, wenn er von der Vorgabe abweicht (Herkunft «grundlage»).
    * War er **ausdruecklich bestellt** und weicht ab: laut abgewiesen, wie jedes andere Feld,
      das nicht zur Grundlage passt — neu gerechnet wird nicht still.
    """
    in_grundlage = geholt.get("himmel_sichtbar") is True
    gerechnet = szene.get("himmel_sichtbar") is True
    if gerechnet == in_grundlage:
        return szene, None
    herkunft = ((szene.get("messschalter") or {}).get("himmel_sichtbar") or {}).get("herkunft")
    if herkunft == _kosmo_szene.HERKUNFT_BESTELLT:
        raise AbholerError(
            f"Grundlage {geholt.get('id')!r} passt nicht zum Auftrag: sie ist "
            f"{'mit' if in_grundlage else 'ohne'} sichtbaren Himmel gerechnet, bestellt ist "
            f"'vis.himmel_sichtbar: {str(gerechnet).lower()}'. Der Himmel steht im Cycles-Bild "
            f"der Grundlage — bitte die Grundlage neu rendern oder den Schalter weglassen.")
    satz = (f"HIMMEL WIE IN DER GRUNDLAGE: Die Grundlage {geholt.get('id')} ist "
            f"{'mit' if in_grundlage else 'ohne'} sichtbaren Himmel gerechnet; die Variante "
            f"behaelt ihn so (Vorgabe waere {'aus' if in_grundlage else 'an'}). Fuer den "
            f"Himmel hinter dem Haus die Grundlage neu rendern.")
    messschalter = dict(szene.get("messschalter") or {})
    messschalter["himmel_sichtbar"] = {"herkunft": _kosmo_szene.HERKUNFT_GRUNDLAGE,
                                       "grund": satz}
    return dict(szene, himmel_sichtbar=in_grundlage, messschalter=messschalter), satz


def messschalter_angewandt(szene: dict) -> dict | None:
    """``angewandt.messschalter`` (Entscheid 126) — je Schalter der Varianten-Vorgabe der
    gerechnete Wert und woher er kam: ``{<name>: {wert, herkunft, grund?}}``. ``None``, wenn
    die Szene keine Herkunft traegt (alte Szene)."""
    herkunft = szene.get("messschalter")
    if not isinstance(herkunft, dict) or not herkunft:
        return None
    return {name: dict({"wert": _messschalter_wert(szene, name)}, **eintrag)
            for name, eintrag in sorted(herkunft.items())}


def _bildeingang_abgeschaltet(szene: dict) -> bool:
    """``vis.bildeingang: false`` ausdruecklich bestellt (Befund 340) — fuer den Satz des
    Rueckfalls in :func:`ki_vermerk`."""
    eintrag = (szene.get("messschalter") or {}).get("bildeingang") or {}
    return (isinstance(eintrag, dict)
            and eintrag.get("herkunft") == _kosmo_szene.HERKUNFT_BESTELLT
            and not szene.get("bildeingang"))


def _messschalter_wert(szene: dict, name: str):
    """Der gerechnete Wert eines Messschalters — **aus heisst ``false``, nie ``null``.**

    Die Szene trägt einen ausgeschalteten Schalter als ``None`` (``lies_umriss_halten`` gibt für
    ``false`` und «nicht bestellt» dasselbe zurück). Im Ergebnis stand darum bei
    ``vis.umriss_halten: false`` ``{wert: null, herkunft: bestellt}`` (auf-20261021-317 B4,
    319 B4) — in der Wirkung richtig, im Wort aber nicht, was bestellt war. ``material_vorne``
    liest, ob der Satz wirklich vorne im Prompt steht.
    """
    if name == "material_vorne":
        return any(z.get("art") == "material_vorne" and z.get("satz")
                   for z in szene.get("prompt_zusaetze") or ())
    wert = szene.get(name)
    return False if wert is None else wert


def _gewaehlte_seeds(urteile) -> dict:
    """``{kamera: behaltener Startwert}`` der gerechneten Kameras — für die Grundlage."""
    raus = {}
    for u in urteile or ():
        gewaehlt = ((u or {}).get("seedauswahl") or {}).get("gewaehlt")
        if u.get("kamera") is not None and isinstance(gewaehlt, int) \
                and not isinstance(gewaehlt, bool) and not u.get("doppelt_von"):
            raus[str(u["kamera"])] = gewaehlt
    return raus


def _guete_vermerk(szene, backbone_name, schritte, auswahl, steuer) -> dict:
    """Was die Vorschau an der Rechnung dieser Kamera geändert hat (Entscheid 104).

    Steht am Kameraurteil unter :data:`aiimaging.kosmo_szene.URTEIL_GUETE` und trägt den
    Satz in ``verdict.reason``. ``backbone_bestellt`` ist, was ``vis.backbone`` nannte
    (``None``: nichts) — weicht es ab, steht hier, dass die Vorschau es übergangen hat.
    """
    bestellt = szene.get("backbone")
    vermerk = {
        "guete": _kosmo_szene.GUETE_VORSCHAU,
        "backbone": backbone_name,
        "backbone_bestellt": bestellt,
        "schritte": schritte,
        "steuerstaerke": steuerstaerke_des_laufs(szene),
        "steuerstaerke_bestellt": szene.get("controlnet_staerke", 0.8),
        "seed": (auswahl or {}).get("gewaehlt"),
        "ki_groesse": list((steuer or {}).get("ki_groesse") or ()) or None,
        "grundlage_groesse": list((steuer or {}).get("grundlage_groesse") or ()) or None,
        "verkleinert": bool((steuer or {}).get("verkleinert")),
        "weg": (steuer or {}).get("weg"),
        "hinweise": [],
    }
    # HOCHGERECHNET (auf-20261020-293 B3): nur, wenn es geschah — sonst bleibt der Vermerk
    # Feld fuer Feld der bisherige.
    if (steuer or {}).get("hochgerechnet"):
        vermerk["hochgerechnet"] = True
        vermerk["hinweise"].append(
            f"Die Grundlage {steuer['grundlage_groesse'][0]}x{steuer['grundlage_groesse'][1]} "
            f"ist kleiner als die Untergrenze von {backbone_name!r}; der KI-Schritt rechnet "
            f"{steuer['ki_groesse'][0]}x{steuer['ki_groesse'][1]} und bringt sein Bild auf "
            f"die Grundlage zurueck.")
    if bestellt and bestellt != backbone_name:
        vermerk["hinweise"].append(
            f"Bestellt war {bestellt!r}; die Vorschau rechnet immer {backbone_name!r}. Fuer "
            f"das bestellte Modell 'Voll' waehlen.")
    if vermerk["steuerstaerke"] != vermerk["steuerstaerke_bestellt"]:
        vermerk["hinweise"].append(
            f"Bestellt war faithful {vermerk['steuerstaerke_bestellt']}; die Vorschau steuert "
            f"immer mit {vermerk['steuerstaerke']} (Registerwert von {backbone_name!r}).")
    if (steuer or {}).get("schoenbild_grund"):
        vermerk["hinweise"].append(steuer["schoenbild_grund"])
    return vermerk


def _guete_vermerk_voll(backbone_name, steuer) -> dict | None:
    """Der Vermerk der vollen Güte — nur, wenn der KI-Schritt hochgerechnet hat (294, B5).

    Bei «voll» blieb der Vermerk bis dahin leer, auch wenn die Grundlage (960 × 600) unter der
    Untergrenze des Modells lag und der KI-Schritt 1024 × 640 rechnete. Dieselben Felder wie
    bei der Vorschau, soweit sie hier etwas sagen (Grösse, Weg, Satz); ohne Hochrechnung
    ``None`` wie bisher. Kein Vorschausatz in ``verdict.reason`` — der hängt an der Güte,
    nicht an diesem Vermerk (``kosmo_szene.als_ergebnis``).
    """
    if not (steuer or {}).get("hochgerechnet"):
        return None
    ki, grund = steuer["ki_groesse"], steuer["grundlage_groesse"]
    return {"guete": _kosmo_szene.GUETE_VOLL, "backbone": backbone_name,
            "ki_groesse": list(ki), "grundlage_groesse": list(grund),
            "verkleinert": bool(steuer.get("verkleinert")), "hochgerechnet": True,
            "weg": steuer.get("weg"),
            "hinweise": [f"Die Grundlage {grund[0]}x{grund[1]} ist kleiner als die Untergrenze "
                         f"von {backbone_name!r}; der KI-Schritt rechnet {ki[0]}x{ki[1]} und "
                         f"bringt sein Bild auf die Grundlage zurueck."]}


def pose_aus_bericht(bericht: dict) -> dict | None:
    """Die GERECHNETE Kamera als ``CameraSpec`` in Blenders Achse (``up_axis: "z"``).

    So kann sie unveraendert als feste Kamera zurueck in einen Auftrag (Nr. 68): Unsere
    Lesung nimmt ``z`` ohne Drehung. ``None``, wenn der Bericht die Stellung nicht nennt.
    """
    herkunft = (bericht or {}).get("kamera")
    if not isinstance(herkunft, dict) or not herkunft.get("auge") or not herkunft.get("blick_auf"):
        return None
    try:
        spec = _kosmo_szene.kamera_zu_spec(herkunft)
    except _kosmo_szene.SzenenError:
        return None
    return {"position": list(spec["position"]), "target": list(spec["target"]),
            "fov": spec["fov"], "up_axis": "z"}


def multipass_schluessel(einstellungen: dict, *, blender: str) -> str:
    """Der Cache-Schlüssel eines Multipass-Aufrufs.

    Er beantwortet genau eine Frage — *würde dieselbe Rechnung dasselbe Bild liefern?* —
    und benutzt dafür `graph.inhalts_hash`, nicht eine eigene Rechnung. Die Marke
    `glb_path` steht in `param_dateien`: Der **Inhalt** der glb zählt, ihr Pfad nicht.
    Ein verschobener Projektordner verwirft den Zwischenspeicher sonst, obwohl sich an
    der Geometrie nichts geändert hat.

    Args:
        einstellungen: Was an `seams.glb_zu_multipass` geht, `glb_path` eingeschlossen.
        blender: Die Fassung, die rechnet — siehe :func:`_blender_fassung`.
    """
    params = {k: v for k, v in einstellungen.items()
              if k not in MULTIPASS_NICHT_IM_SCHLUESSEL}
    params["_blender"] = blender
    knoten = _graph.Knoten(id="multipass", art="multipass", params=params)
    # Der Codestand kommt aus derselben Zeile wie im Zwischenspeicher der Mappe
    # (`kette.FASSUNGEN`): Wer den Multipass hochzählt, verwirft beide Speicher, nicht
    # nur einen. Bei der Anfangsfassung bleibt der Schlüssel bitgleich mit dem bisherigen.
    # `kontext_ply` (Entscheid 76): Der INHALT des Splats zaehlt, sein Pfad nicht —
    # ein neu aufgenommener Splat unter altem Namen ist kein Treffer. Ohne ihn in den
    # Einstellungen bleibt der Schluessel bitgleich.
    return _graph.inhalts_hash(knoten, [], param_dateien=("glb_path", "kontext_ply", "umgebung_hdr",
                                             "materialien_json"),
                               fassung=_kette.fassung_von(_kette.ART_MULTIPASS))


def _aus_dem_zwischenspeicher(cache, schluessel: str) -> dict | None:
    """Ein brauchbarer Eintrag — oder ``None``, und dann wird gerechnet.

    **Geprüft wird mit `kette._cache_maengel`, nicht mit einer eigenen Prüfung.** Sie
    legt zwei Netze übereinander: eines errät Dateifelder an der Endung, das andere zählt
    die Pflichtfelder aus `kette.BEDARF` auf. Das zweite kostet drei Zeilen und hat in
    Sitzung 07 den bisher teuersten Fehler dieses Projekts gefangen — einen Eintrag mit
    `depth_png = None`, der als Treffer galt, sodass die teure Stufe nie wieder lief und
    die Kette für immer eine Stufe später scheiterte.
    """
    if cache is None:
        return None
    eintrag = cache.hole(schluessel)
    if not isinstance(eintrag, dict):
        return None
    if _kette._cache_maengel("multipass", eintrag, _kette.BEDARF):
        return None
    return eintrag


# --------------------------------------------------------------------------------------
# Welcher Riegel auf welchem Weg laeuft
# --------------------------------------------------------------------------------------
#
# **Der Anlass.** Bis zum 26.08.2026 gab es zwei Nähte, die dasselbe versprachen — den
# Szenenvertrag der Brücke und die Werkzeugnaht (MCP) — und **nur eine hatte einen
# Ausführer**. Ein über KosmoOrbit bestellter Render ging auf ``queued`` und blieb dort.
# Seit die zweite Ablage bedient wird (:mod:`aiimaging.eigene_quelle`), laufen beide Wege
# durch **dasselbe** ``verarbeiter`` — und genau das soll nicht unbemerkt aufhören.
#
# Die Tabelle ist gegen die dritte Möglichkeit gebaut, wie ihre Nachbarn: Ein Riegel läuft
# auf **beiden** Wegen, oder er läuft auf einem und **sagt warum**. «Steht nirgends» ist
# die bequemste Auskunft und die einzige, die hier nicht vorgesehen ist.

#: Beide Wege, unter den Namen ihrer Quellenmodule.
WEGE = ("bruecke", "eigene_quelle")

#: Jeder Riegel vor dem Bildlauf — mit dem Ort, an dem er gerufen wird, und den Wegen,
#: auf denen er greift.
#:
#: ``ort`` ist die Funktion, aus der heraus er gerufen wird; ``wege`` sind die Quellen,
#: für die er gilt. ``begruendung`` ist **Pflicht, sobald ``wege`` nicht beide nennt** —
#: ein einseitiger Riegel ohne Grund ist eine Lücke mit gutem Gewissen.
RIEGEL: dict[str, dict] = {
    "_blick_trifft_szene": {
        "ort": "verarbeiter",
        "wege": WEGE,
        "was": "Trifft der Sehstrahl von `auge` nach `blick_auf` die Huellbox der Szene "
               "ueberhaupt? Ohne Schwellenwert — eine Kamera, die an der Szene "
               "vorbeischaut, erzeugt ein leeres Tiefenbild, und die Meldung darueber "
               "kaeme sonst aus der Normalisierung und spraeche von der Schranke statt "
               "von der Kamera (Demolauf 12, 01.09.2026). Er steht ausdruecklich VOR "
               "der Tiefenpruefung und gilt auf BEIDEN Kamerawegen — anders als "
               "`_rahmung_vor_dem_render`, das auf dem vorgegebenen Weg zu Recht "
               "schweigt und ihn damit ganz ungeprueft liess.",
    },
    "_bilder_vollstaendig": {
        "ort": "verarbeiter",
        "wege": WEGE,
        "was": "Sind die Zwischenbilder des Multipass ganz da? Ein halb geschriebenes "
               "PNG fiele sonst erst in der Diffusion auf, mit einer Meldung aus der "
               "Bildbibliothek, die keine Datei nennt.",
    },
    "_massstab_gemeldet": {
        "ort": "verarbeiter",
        "wege": WEGE,
        "was": "Der Massstab der Geometrie. MELDET und bricht nicht ab — er ist eine "
               "Eigenschaft der Geometrie und bei jeder Kamera dieselbe, also kann ihn "
               "keine andere Blickrichtung heilen.",
    },
    "_modellstand_gemeldet": {
        "ort": "verarbeiter",
        "wege": WEGE,
        "was": "Trägt das Modell, was sein Erzeuger schreiben kann? MELDET und bricht "
               "nicht ab — aus demselben Grund wie `_massstab_gemeldet`: Wie oft der "
               "Bestand hier `zurueck` sagt, ist ungemessen, weil es die Prüfung bis zum "
               "02.09.2026 nicht gab. Er kennt DREI Zustände, und `ungeprueft` ist "
               "ausdrücklich KEIN Bestehen — sonst wäre er die Prüfung, die alles "
               "durchwinkt, was sie nicht kennt.",
    },
    "_rahmung_vor_dem_render": {
        "ort": "verarbeiter",
        "wege": WEGE,
        "was": "Füllt das Bauwerk das Bild genug, damit die Geometriezahl etwas heisst?",
    },
    "_komposition_vor_dem_render": {
        "ort": "verarbeiter",
        "wege": WEGE,
        "was": "Steht die Kamera an einem Ort, von dem aus das Bild etwas zeigt — "
               "einschliesslich der Frage, ob sie über dem Dach schwebt "
               "(`_kamera_ueber_dach`).",
    },
    "_kamera_ueber_dach": {
        "ort": "_komposition_vor_dem_render",
        "wege": WEGE,
        "was": "Die Kamera über der Dachkante: ein Bild von oben auf ein Bauwerk, das "
               "von der Strasse aus dokumentiert werden sollte.",
    },
    "_karte_frei": {
        "ort": "hole_einen",
        "wege": WEGE,
        "was": "Leerlauftor: `idle_window_only` gegen die Auskunft über die Karte. Ohne "
               "Auskunft wird NICHT gerechnet — ungeprüft ist nicht in Ordnung.",
    },
    "torwaechter.torwaechter": {
        "ort": "werkzeuge.enqueue_render",
        "wege": ("eigene_quelle",),
        "was": "Der Riegel gegen Einheitenfehler, VOR der Auftragsanlage.",
        "begruendung": (
            "Einseitig, und zwar an der Stelle, die es nur auf diesem Weg gibt: Der "
            "MCP-Einlass ENTSCHEIDET, ob ein Auftrag überhaupt entsteht, und kann ihn "
            "darum ablehnen, bevor er existiert. Bei der Brücke liegt der Auftrag "
            "bereits, wenn wir ihn sehen — dort ist der Massstab eine Meldung "
            "(`_massstab_gemeldet`) und keine Ablehnung. Beide Wege prüfen ihn also; nur "
            "die Folge ist eine andere, weil die Lage eine andere ist."
        ),
    },
}

#: Funktionen, die ein ``abbruch``-Feld anfassen und trotzdem **keine** Riegel sind.
#:
#: Sie stehen benannt da, weil der Wächter von der anderen Seite zählt: Er sucht jede
#: Funktion, die ``abbruch`` führt, und verlangt sie in :data:`RIEGEL`. Eine Ausnahme ohne
#: Begründung wäre ein Loch mit Namen.
KEINE_RIEGEL = {
    "verarbeiter": "die Schleife selbst — sie liest die Urteile der Riegel, sie fällt keines",
    "befund_kurz": "Leser: macht aus abgelegten Urteilen Zeilen für einen Menschen",
    "_nicht_gerendert_kurz": "Leser: gruppiert die Gründe nach Art für das Vertragsergebnis",
    "_art_ohne_bild": "Leser: sagt, welcher Riegel eine Kamera ohne Bild liess — für den "
                      "Vertragsgrund und den Lieferstatus je Kamera (23.09.2026)",
    "_rahmung_abgeschaltet": "das Gegenteil eines Riegels — `rahmung_pruefen=False` "
                             "abbilden, ohne dass ein abgeschalteter Lauf wie ein "
                             "bestandener aussieht",
}


MULTIPASS_BILDER = ("depth_png", "beauty_png", "material_id_png")


def _bilder_vollstaendig(bericht: dict) -> dict:
    """Sind die Zwischenbilder dieses Laufs **ganz da**? — vor dem teuren Schritt.

    **Der Anlass ist ein Fehlschlag mitten in einem Mehrkamera-Auftrag** (HomeStation,
    `auf-vis-20260826-16`, 26.08.2026): ``OSError: image file is truncated``, und die
    **erste** Kamera war durchgelaufen. Die Meldung kommt aus der Bildbibliothek, nennt
    keine Datei und fällt dort an, wo gerechnet wird — nicht dort, wo geschrieben wurde.

    :func:`aiimaging.bildlesen.pruefe_png` beantwortet die Frage mit der **Prüfsumme jedes
    Blocks**, ohne den Bildinhalt zu entpacken. Das kostet fast nichts, und es macht aus
    einem Fehlschlag der Diffusion einen benannten Befund über eine Datei.

    Returns:
        ``{vollstaendig, geprueft, beschaedigt, grund}``. Dateien, die der Bericht gar
        nicht nennt, werden **nicht** beanstandet: ``beauty_png`` fehlt bei
        ``--ohne-beauty`` mit Absicht, und ein fehlendes Feld ist etwas anderes als eine
        halbe Datei.
    """
    from . import bildlesen

    geprueft, beschaedigt, gruende = [], [], []
    for feld in MULTIPASS_BILDER:
        pfad = bericht.get(feld)
        if not pfad:
            continue
        lage = bildlesen.pruefe_png(pfad)
        geprueft.append(feld)
        if not lage["lesbar"]:
            beschaedigt.append(feld)
            gruende.append(f"{feld}: {lage['grund']}")
    return {"vollstaendig": not beschaedigt, "geprueft": tuple(geprueft),
            "beschaedigt": tuple(beschaedigt), "grund": " | ".join(gruende)}


#: Bis zu welcher Abweichung zwei Soll-Karten als DIESELBE Ansicht gelten (Meter).
#:
#: Gemessen am 24.09.2026 (Blender 4.2.1, Testbau 8 × 5 × 3 m, ``sSE`` gegen ``nNW``, 128 ×
#: 80 Punkte): gleiche Maske, grösste Abweichung **9,5·10⁻⁶ m** — Rechenrauschen der
#: EXR bei rund 10 m Abstand. Zwei wirklich verschiedene Ansichten unterscheiden sich
#: um Dezimeter bis Meter. Ein Millimeter liegt zwei Grössenordnungen über dem Rauschen
#: und drei unter jedem echten Unterschied.
ZWILLING_TOLERANZ_M = 1e-3


def _flache_karte(soll) -> list[float] | None:
    """Die Soll-Karte als flache Liste — so, wie ``tiefen_aus_report`` sie liefert.

    Zeilenweise Listen (die Form der älteren Proben) werden flach gemacht. ``None``, wenn
    etwas darin keine Zahl ist.
    """
    if soll is None:
        return None
    flach: list[float] = []
    try:
        for eintrag in soll:
            if isinstance(eintrag, (list, tuple)):
                flach.extend(float(w) for w in eintrag)
            else:
                flach.append(float(eintrag))
    except (TypeError, ValueError):
        return None
    return flach


#: Wie viele Bildpunkte zweier Soll-Karten abweichen duerfen, und sie gelten trotzdem als
#: DIESELBE Ansicht — als Anteil aller Punkte, und nur an der Silhouettenkante.
#:
#: **Anlass auf-20261020-290 (6c):** Am Quader 8 × 3 × 5 m waren ``sSE`` und ``nNW`` in
#: 1 587 197 von 1 587 200 Punkten gleich (p99 6·10⁻⁶ m), aber 3 Punkte an der Unterkante
#: der Silhouette waren in der einen Ansicht Geometrie und in der anderen Hintergrund —
#: Kantenrauschen der Rasterung. Bis dahin verlangte der Vergleich JEDEN Punkt gleich, und
#: der Zwilling wurde nicht erkannt (zwei Kameras voll gerechnet). 2·10⁻⁵ sind bei
#: 1600 × 992 rund 31 Punkte; eine echte zweite Ansicht unterscheidet sich in Tausenden, und
#: ausserhalb der Kante zaehlt schon EIN abweichender Punkt.
ZWILLING_KANTENANTEIL = 2e-5


def _ist_hintergrund(wert: float) -> bool:
    """Hintergrund ist, was nicht endlich ist ODER die Marke des Renderers traegt.

    Cycles schreibt fuer «nichts getroffen» keine Unendlichkeit, sondern eine endliche, sehr
    grosse Zahl (1e10). Bis zum 20.10.2026 galt hier nur ``isfinite`` — ein Punkt mit 1e10
    neben einem mit 9,3 m war darum keine Maskenabweichung, sondern «10 Milliarden Meter
    Tiefenunterschied». Die Grenze ist dieselbe wie bei der Silhouette der Pruefung
    (:data:`aiimaging.geometrie_qa.HINTERGRUND_SCHWELLE_M`): eine Regel, eine Stelle.
    """
    import math

    from .geometrie_qa import HINTERGRUND_SCHWELLE_M
    return not math.isfinite(wert) or wert >= HINTERGRUND_SCHWELLE_M


def _an_der_kante(karte: list[float], i: int, breite: int | None, hoehe: int | None) -> bool:
    """Liegt Punkt ``i`` an der Silhouettenkante — hat er einen Nachbarn mit anderer Maske?"""
    if not breite or not hoehe or len(karte) != breite * hoehe:
        return False
    y, x = divmod(i, breite)
    selbst = _ist_hintergrund(karte[i])
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            ny, nx = y + dy, x + dx
            if (dy or dx) and 0 <= ny < hoehe and 0 <= nx < breite \
                    and _ist_hintergrund(karte[ny * breite + nx]) != selbst:
                return True
    return False


def _gleiche_ansicht(a: list[float], b: list[float], *,
                     toleranz_m: float = ZWILLING_TOLERANZ_M,
                     breite: int | None = None, hoehe: int | None = None,
                     kantenanteil: float = ZWILLING_KANTENANTEIL) -> bool:
    """Zeigen zwei Soll-Karten dieselbe Ansicht? Gleiche Maske, Abweichung ≤ Toleranz.

    Hintergrund ist nicht endlich ODER ≥ der Marke (:func:`_ist_hintergrund`). Mit ``breite``
    und ``hoehe`` duerfen hoechstens ``kantenanteil`` aller Punkte abweichen — und nur
    solche an der Silhouettenkante (in beiden Karten). Ohne Masse gilt die strenge
    Regel: jeder Punkt gleich.
    """
    import math

    from .geometrie_qa import HINTERGRUND_SCHWELLE_M as grenze
    if len(a) != len(b):
        return False
    erlaubt = int(len(a) * kantenanteil) if breite and hoehe else 0
    abweichend: list[int] = []
    endlich = math.isfinite
    for i, (x, y) in enumerate(zip(a, b)):
        if x == y:
            continue
        # Dasselbe wie `_ist_hintergrund`, hier ausgeschrieben: 1,6 Mio. Punkte je Paar.
        hx = not endlich(x) or x >= grenze
        hy = not endlich(y) or y >= grenze
        if hx != hy or (not hx and abs(x - y) > toleranz_m):
            abweichend.append(i)
            if len(abweichend) > erlaubt:
                return False
    # IN BEIDEN KARTEN AN DER KANTE: Ein Loch mitten in der Fassade ist in der Karte mit
    # dem Loch auch «Kante» (sein Nachbar ist Geometrie) — in der anderen nicht.
    return all(_an_der_kante(a, i, breite, hoehe) and _an_der_kante(b, i, breite, hoehe)
               for i in abweichend)


def _finde_zwilling(gesehen: list[dict], soll, breite, hoehe) -> dict | None:
    """Die erste schon gerenderte Kamera dieses Auftrags mit derselben Ansicht, oder ``None``.

    ``None`` auch, wenn die Karte nicht lesbar ist — im Zweifel wird gerendert, denn ein
    fehlendes Bild ist teurer als ein doppeltes.
    """
    flach = _flache_karte(soll)
    if flach is None or not breite or not hoehe:
        return None
    for vorbild in gesehen:
        if (vorbild["breite"], vorbild["hoehe"]) == (breite, hoehe) \
                and _gleiche_ansicht(vorbild["soll"], flach, breite=breite, hoehe=hoehe):
            return vorbild
    return None


def _rahmung_vor_dem_render(bericht: dict, *, gerahmte_box=None) -> dict:
    """Kann dieser Lauf bei DIESER Rahmung überhaupt etwas zeigen — **vor** dem Bildlauf?

    **Der Anlass ist ein Owner-Einwand** (`auf-vis-20260825-15`, Posten 1, 25.08.2026),
    nachdem die Kette zum ersten Mal ganz durchgelaufen war:

      *«Das sollte natuerlich gar nicht so weit kommen — die Modelle muessen pruefen, ob
      die Geometrie richtig ist und richtig darstellt, BEVOR AI Imaging startet.»*

    Und der Einwand traf einen zweiten Befund derselben Nacht: :func:`kameras.rahmungsverhaeltnis`
    und ``bbox_bauwerk`` waren **gebaut und ungenutzt** — ausser Tests kein einziger
    Aufrufer. Die sechste tote Kante dieser Woche, und die einzige, die niemand von
    aussen gemeldet hat, weil sie nach aussen wie eine gelöste Aufgabe aussah.

    **Warum das hier steht und nicht im Runner.** Der Runner rahmt, was ihm gesagt wird;
    er entscheidet nicht über Aufträge. Und die Rechnung ist reine Arithmetik — im Runner
    wäre sie eine Fähigkeit, die ohne Blender niemand hätte (Regel 4).

    Returns:
        Das Ergebnis von :func:`kameras.rahmungsverhaeltnis`, ergänzt um ``weg`` (wie die
        Kamera zustande kam) und ``note`` (warum die Bauwerksbox fehlt, falls sie fehlt).

    .. important::
       ``abbruch`` wird auf ``None`` gesetzt, wenn die Kamera **nicht** aus der Hüllbox
       abgeleitet wurde. Die Rechnung geht von :data:`kameras.DECKUNGSGRAD` aus, und der
       beschreibt nur den abgeleiteten Weg. Wer Standort und Blickziel als Zahlen
       hereingibt, hat gerahmt — und einen solchen Auftrag mit einer Zahl abzubrechen,
       die auf ihn nicht zutrifft, wäre schlimmer als gar keine Prüfung.
    """
    from . import kameras

    weg = (bericht.get("kamera") or {}).get("weg")
    # WELCHE BOX DIE KAMERA GERAHMT HAT (auf-20261020-290, Befund 4). Seit dem 30.09.2026
    # rahmt die Richtungskamera nach dem BAUWERK (`_rahmung_fuer`, `--kamera-huellbox`); der
    # Bericht nennt unter `bbox` aber weiter die SZENE. Gerechnet wurde darum «Fuellgrad der
    # Bauwerksbox × Bauwerk/Szene» — der Anteil des Bauwerks an der Platte zum zweiten Mal:
    # Haus 12 m auf Platte 40 m, 0,70 × 0,30 = 21 % statt 70 %, und JEDE Szene mit
    # Gelaendeplatte wurde abgelehnt. Gemessen wird jetzt gegen die Box, die gerahmt wurde.
    # Nur auf dem abgeleiteten Weg — nur dort hat der Runner eine Box gerahmt.
    szene_box = (gerahmte_box if gerahmte_box is not None and weg == "abgeleitet"
                 else bericht.get("bbox"))

    # DER DECKUNGSGRAD DIESES LAUFS, nicht der der Bibliothek.
    #
    # Bis zum Nachmittag des 26.08.2026 stand hier `kameras.DECKUNGSGRAD` — und zwar
    # sowohl in der Rechnung als auch als Angabe im Urteil. Das war ein Verstoss gegen den
    # Satz, unter dem dieser ganze Tag steht: **Eine Zahl gehoert an die Bedingung, unter
    # der sie gemessen wurde.** Der Riegel sprach ueber einen Lauf mit 0.70, auch wenn der
    # Lauf mit 0.55 gestellt worden war — und `auf-20260825-41` vergleicht genau diese
    # beiden Werte miteinander.
    #
    # Aeltere Berichte tragen das Feld nicht. Dann gilt die Vorgabe, und `quelle` sagt es:
    # NICHT FESTSTELLBAR wird nicht zu FESTGESTELLT, nur weil eine Konstante zur Hand ist.
    #
    # FEHLT UND NULL SIND ZWEI AUSSAGEN (Befund 23.09.2026). Seit dem 22.09.2026 meldet
    # der Runner `deckungsgrad` nur auf dem Weg «abgeleitet» und sonst `null` samt
    # `deckungsgrad_wirkungslos` (`_deckungsgrad_befund` dort). Hier stand
    # `bericht.get(...)`, und das liest das Fehlen und das `null` gleich: Jeder Bericht
    # einer vorgegebenen Kamera bekam die Vorgabe 0,70 mit Quelle «vorgabe» ins Urteil
    # und dazu die Rechnung, die auf ihr ruht — genau die Rahmung, von der der Runner
    # gerade gesagt hatte, dass sie nie gestellt wurde. Die Vorgabe gilt darum NUR, wenn
    # das Feld fehlt (alter Runner) oder keine Zahl ist; `null` heisst NICHT GERAHMT.
    # Bewacht ueber Bruecke, Abholer und Verarbeiter in tests/test_runde7_abholer.py.
    wirkungslos = None
    if "deckungsgrad" not in bericht:
        deckungsgrad, quelle, unlesbar = kameras.DECKUNGSGRAD, "vorgabe", None
    elif bericht["deckungsgrad"] is None:
        deckungsgrad, quelle, unlesbar = None, "nicht_gerahmt", None
        wirkungslos = (bericht.get("deckungsgrad_wirkungslos") or (
            "Der Bericht meldet keinen Deckungsgrad (null) und nennt keinen Grund dafuer."))
    elif (isinstance(bericht["deckungsgrad"], (int, float))
          and not isinstance(bericht["deckungsgrad"], bool)):
        deckungsgrad, quelle, unlesbar = float(bericht["deckungsgrad"]), "bericht", None
    else:
        # `True` ist in Python eine Zahl und waere eine Rahmung von 100 %. Das Feld
        # steht da, sagt aber nichts Lesbares — also gilt die Vorgabe, und zwar als
        # Vorgabe benannt (bis zum 23.09.2026 stand hier Quelle «bericht»).
        deckungsgrad, quelle = kameras.DECKUNGSGRAD, "vorgabe"
        unlesbar = bericht["deckungsgrad"]

    # DER GEMESSENE FUELLGRAD SCHLAEGT DEN SOLLWERT.
    #
    # Am 26.08.2026 durch Blender gemessen: `kamerasatz` haelt den Deckungsgrad ab etwa
    # 8 m Bauwerkskante exakt ein — darunter uebernimmt der Mindestabstand, und bei 4 m
    # steht im Bericht `massgebend: "untergrenze"` mit einem Fuellgrad von 0.553 statt
    # 0.700. Ein Riegel, der mit dem Sollwert rechnet, waere dort zu milde.
    #
    # Nur vom ABGELEITETEN Weg: Kam die Kamera als Zahlenpaar herein, hat `kamerasatz`
    # nichts gerechnet, und `fuellgrad` steht gar nicht im Bericht.
    kamera = bericht.get("kamera") or {}
    gemessen = kamera.get("fuellgrad") if weg == "abgeleitet" else None

    if deckungsgrad is None:
        # NICHT GERAHMT: keine wirksame Bildbreite, kein Knie, kein Abbruch. Gerechnet
        # wird nur der Breitenanteil (Bauwerk zu Szene), denn der haengt allein an den
        # beiden Huellboxen — mit der Einheitsrahmung 1,0 ist die Bildbreite genau er,
        # und alles, was auf einer Rahmung ruhen wuerde, wird danach geleert.
        lage = kameras.rahmungsverhaeltnis(szene_box,
                                           bericht.get("bbox_bauwerk"),
                                           deckungsgrad=1.0)
        #
        # ZWEI SAETZE, NICHT EINER (Durchsicht der Runde 7, 23.09.2026). Auf dem Weg
        # «abgeleitet» ist der Satz «die Vorgabe sprach ueber einen anderen Kameraweg»
        # falsch — es IST der Weg, auf dem der Deckungsgrad wirkt, und der Runner meldet
        # dort immer eine Zahl. Ein `null` dort ist ein Bericht, der sich widerspricht;
        # das wird gesagt statt einer Begruendung, die nicht zutrifft. Eingesetzt wird die
        # Vorgabe auch hier nicht: Ob mit ihr gerahmt wurde, belegt der Bericht nicht.
        if weg == "abgeleitet":
            satz = (f"NICHT GERAHMT, UND DER BERICHT WIDERSPRICHT SICH: Die Kamera kam "
                    f"auf dem Weg 'abgeleitet' zustande — dem einzigen, auf dem der "
                    f"Runner einen Deckungsgrad stellt und meldet —, und trotzdem steht "
                    f"dort null. {wirkungslos} Mit welchem Deckungsgrad gerahmt wurde, "
                    f"ist damit nicht feststellbar; die Vorgabe der Bibliothek wird nicht "
                    f"eingesetzt, weil sie eine Rahmung behaupten wuerde, die der Bericht "
                    f"nicht belegt.")
        else:
            satz = (f"NICHT GERAHMT: {wirkungslos} Ohne Deckungsgrad gibt es keine "
                    f"wirksame Bildbreite; die Vorgabe der Bibliothek sprach ueber einen "
                    f"anderen Kameraweg und wird hier nicht eingesetzt.")
        lage.update(wirksame_bildbreite=None, traegt=None, abbruch=None,
                    abbruch_grund="", basis=None, grundlage=None,
                    grund=(satz
                           + (f" {lage['grund']}" if lage.get("breitenanteil") is None
                              else "")))
    else:
        lage = kameras.rahmungsverhaeltnis(szene_box,
                                           bericht.get("bbox_bauwerk"),
                                           deckungsgrad=deckungsgrad,
                                           gemessener_fuellgrad=gemessen)
    lage = dict(lage, weg=weg, note=bericht.get("bbox_bauwerk_note") or "",
                gerahmt_nach=("kamerabox" if szene_box is not bericht.get("bbox")
                              else "szene"),
                deckungsgrad=deckungsgrad, deckungsgrad_quelle=quelle,
                deckungsgrad_wirkungslos=wirkungslos,
                massgebend=kamera.get("massgebend"))
    if quelle == "vorgabe" and lage.get("abbruch"):
        lage["abbruch_grund"] += (
            " ACHTUNG: Der Bericht nennt keinen Deckungsgrad"
            + (f" (das Feld steht da, ist aber keine Zahl: {unlesbar!r})"
               if unlesbar is not None else "")
            + "; gerechnet wurde mit der "
            f"Vorgabe {kameras.DECKUNGSGRAD}. Wurde dieser Lauf mit einem anderen "
            f"gestellt, spricht diese Zahl ueber einen anderen Lauf. Runner ab dem "
            f"26.08.2026 melden das Feld.")
    if weg != "abgeleitet":
        lage["abbruch"] = None
        lage["abbruch_grund"] = (
            f"Die Kamera kam auf dem Weg {weg!r} zustande, nicht aus der Huellbox. Der "
            f"Deckungsgrad beschreibt diesen Lauf darum NICHT, und es wird nichts "
            f"abgebrochen. "
            + ("Eine Bildbreite wird nicht gerechnet — der Runner meldet, dass kein "
               "Deckungsgrad gewirkt hat." if deckungsgrad is None else
               "Die gerechnete Bildbreite steht trotzdem da — als Auskunft, nicht als "
               "Urteil (ein Runner ab dem 22.09.2026 meldet auf diesem Weg keinen "
               "Deckungsgrad)."))
    return lage


def _nicht_gerendert_kurz(kameras) -> tuple[str, ...]:
    """Warum einzelne Kameras **absichtlich** kein Bild bekamen — für den fremden Vertrag.

    **Der Anlass ist am 26.08.2026 über die wirkliche Kette gemessen** worden, nicht an
    Attrappen: Ein Auftrag auf einer Geometrie mit Gelände wurde von allen drei Kameras
    abgelehnt (Bauwerk füllt 28 % der Bildbreite), und das Vertragsergebnis sagte nur
    *«NICHT GEMESSEN … ein Lauf fehlt»*. Unsere eigene Befunddatei sagte es genau — die
    andere Seite bekam davon nichts.

    *Absichtlich verweigert und abgestürzt sahen im Vertrag gleich aus.*

    Zusammengefasst wird **nach Grund und nicht je Kamera**: Drei Kameras mit demselben
    Grund ergeben eine Zeile mit drei Kürzeln, nicht drei Zeilen. Ein Vertragsfeld, das
    bei zwölf Kameras zwölfmal dasselbe sagt, wird überflogen.

    Returns:
        Kurze Sätze, höchstens einer je Grundart. Leer, wenn jede Kamera ein Bild bekam.
    """
    if not kameras:
        return ()

    # Gruppiert wird nach der ART, nicht nach dem fertigen Satz. Sonst trennt schon eine
    # Nachkommastelle zwei Kameras in zwei Zeilen — gemessen: 27.9 % und 28.0 % ergaben
    # zwei Zeilen fuer denselben Befund.
    nach_art: dict[str, list] = {}
    anteile: dict[str, list] = {}
    for eintrag in kameras:
        if not isinstance(eintrag, dict):
            continue
        # DER ZWILLING HAT KEIN EIGENES BILD, auch wenn `bild_png` an ihm steht (Befund
        # 23.09.2026): Er wird als `dict(zwilling["urteil"], kamera=…, doppelt_von=…)`
        # gebaut und erbt so das Bild seines Vorbilds. Hier stand bis dahin
        # `or eintrag.get("bild_png")` — jeder Zwilling eines gerenderten Vorbilds fiel
        # darum weg, bevor `_art_ohne_bild` «doppelt» sagen konnte, und `verdict.reason`
        # schwieg ueber ihn; genannt war er nur in `lieferstatus_grund` und im eigenen
        # Kurzbefund. Uebersprungen wird jetzt nur, wer ein Bild UND kein Vorbild hat.
        # BEWACHT ist der Zwillingsfall (tests/test_runde11_zwilling.py, Produktweg). Das
        # Ueberspringen eigener Bilder ist Abwehr und NICHT bewacht: `_art_ohne_bild` gibt
        # fuer sie heute ohnehin None — eine Mutation dieser Zeile ueberlebt (Durchsicht).
        if eintrag.get("bild_png") and not eintrag.get("doppelt_von"):
            continue
        art = _art_ohne_bild(eintrag)
        if art is None:
            continue
        if art == "rahmung":
            wert = (eintrag["rahmung"] or {}).get("wirksame_bildbreite")
            if isinstance(wert, float):
                anteile.setdefault(art, []).append(wert)
        if art == "umgebung":
            anteile.setdefault(art, []).append(str(eintrag["umgebung"].get("satz") or ""))
        nach_art.setdefault(art, []).append(str(eintrag.get("kamera")))

    return tuple(_satz_ohne_bild(art, ", ".join(kuerzel), anteile.get(art))
                 for art, kuerzel in nach_art.items())


def _art_ohne_bild(eintrag: dict) -> str | None:
    """WARUM eine Kamera kein eigenes Bild hat: ``doppelt``, ``blickfeld``, ``rahmung``,
    ``kamerahoehe`` — oder ``None``, wenn das Urteil keinen dieser Gruende traegt.

    Herausgeloest am 23.09.2026, damit der Vertragsgrund (:func:`_nicht_gerendert_kurz`)
    und der Lieferstatus je Kamera (:func:`_lieferung_der_kamera`) dieselbe Einteilung
    lesen. Zwei Einteilungen derselben Frage laufen auseinander, sobald eine gepflegt
    wird.
    """
    if (eintrag.get("umgebung") or {}).get("rechenbar") is False:
        # ZUERST: Ein Bildmodell, das hier gar nicht rechnen kann, ist kein Befund ueber
        # die Kamera — keine ihrer Fragen wurde gestellt (auf-20261001-230).
        return "umgebung"
    if eintrag.get("doppelt_von"):
        return "doppelt"
    if (eintrag.get("blickfeld") or {}).get("abbruch"):
        # ZUERST GEFRAGT. Eine Kamera, die an der Szene vorbeischaut, ist kein
        # Rahmungsfall — bei ihr gibt es gar nichts zu rahmen. Stuende die Frage
        # weiter unten, faenge der Rahmungszweig sie ab, sobald er je ein `abbruch`
        # traegt, und die fremde Seite laese eine Bildbreite, die nie gemessen wurde.
        return "blickfeld"
    if (eintrag.get("rahmung") or {}).get("abbruch"):
        return "rahmung"
    if (eintrag.get("komposition") or {}).get("abbruch"):
        return "kamerahoehe"
    return None


def _satz_ohne_bild(art: str, namen: str, werte=None) -> str:
    """Der Satz zu :func:`_art_ohne_bild` — fuer eine Kamera oder eine Gruppe.

    ``werte`` sind die wirksamen Bildbreiten der Rahmungsfaelle; ohne sie steht «zu
    wenig» und keine erfundene Zahl. Bei ``umgebung`` ist es der Satz aus
    :func:`aiimaging.render.pipeline_lage` — fuer alle Kameras derselbe.
    """
    if art == "umgebung":
        satz = (werte or ["Das Bildmodell ist in dieser Render-Umgebung nicht rechenbar."])[0]
        return f"NICHT GERECHNET (Bildmodell), {namen}: {satz}"
    if art == "rahmung":
        werte = werte or []
        spanne = (f"{min(werte):.1%}" if len(set(round(w, 3) for w in werte)) <= 1
                  else f"{min(werte):.1%}–{max(werte):.1%}") if werte else "zu wenig"
        return (f"NICHT GERENDERT (Rahmung), {namen}: Das Bauwerk fuellt {spanne} der "
                f"Bildbreite, gemessen noetig sind "
                f"{_kameras_modul.BILDBREITE_ABBRUCH:.0%}")
    if art == "blickfeld":
        return (f"NICHT GERENDERT (Kamera schaut an der Szene vorbei), {namen}: Der "
                f"Sehstrahl von Standort zu Blickziel trifft die Huellbox der Geometrie "
                f"nicht. Haeufigste Ursache: eine Kameraliste in Dateikoordinaten — "
                f"`up_axis` der CameraSpec pruefen")
    if art == "kamerahoehe":
        return (f"NICHT GERENDERT (Aufnahme nicht beurteilbar), {namen}: Die Kamera steht "
                f"ueber dem Dach — nach HABS/NPS keine Architekturaufnahme")
    return f"Nicht neu gerendert (identische Soll-Karte), {namen}"


def _rahmung_abgeschaltet(rahmung: dict) -> dict:
    """Der Rahmungsriegel, den der Aufrufer ausdrücklich abbestellt hat.

    **Warum es diesen Schalter gibt.** Der Riegel verhindert Läufe, deren Bild die Vorlage
    nicht trägt — und genau solche Bilder braucht eine Messung, die wissen will, *wie
    schlecht* eine Rahmung aussieht. `auf-20260825-41` vergleicht die Deckungsgrade 0,55
    und 0,70 an Bildpaaren; der ältere Wert liegt unter :data:`kameras.BILDBREITE_ABBRUCH`,
    und ohne diesen Schalter lieferte der halbe Vergleich statt eines Bildes einen Abbruch.

    *Ein Riegel, der eine absichtliche Vergleichsmessung verhindert, steht an dieser Stelle
    falsch.* Er wird darum abbestellbar — aber nicht unsichtbar.

    **Der Vermerk steht im Urteil und nicht im Logbuch.** Ein Ergebnis ohne ihn wäre von
    einem nicht zu unterscheiden, das den Riegel *bestanden* hat — und das ist genau die
    Verwechslung, gegen die dieser ganze Tag gebaut ist.
    """
    vorher = rahmung.get("abbruch_grund") or rahmung.get("grund") or ""
    return dict(rahmung, abbruch=False, abgeschaltet=True, abbruch_grund="",
                grund=(f"RAHMUNGSRIEGEL ABGESCHALTET (rahmung_pruefen=False). Der Lauf "
                       f"waere abgebrochen worden — der urspruengliche Grund lautete: "
                       f"{vorher} Gerechnet wurde trotzdem, auf ausdrueckliche Anweisung "
                       f"des Aufrufers. Gedacht ist das fuer Messungen, die eine schlechte "
                       f"Rahmung SEHEN wollen."))


def _erreichbarkeit_dieser_szene(urteil: dict, *, schwelle: float) -> dict | None:
    """Was diese Szene **bestenfalls** erreichen kann — mit der gemessenen Obergrenze.

    **Der Anlass ist der letzte Absatz eines Berichts** (HomeStation, `auf-vis-20260826-16`,
    26.08.2026): *«Die `geom_iou_obergrenze` ist womöglich die aussagekräftigere Zahl als
    der Score selbst, und sie steht heute nur im Befund, nicht in der Meldung.»*

    Der Fall dahinter ist eindrücklich: Dieselbe Geometrie — ein elfgeschossiges Wohnhaus
    ohne Fassade — wird aus der Dreiviertelansicht zu einem **Parkhaus** mit Autos auf
    jeder Ebene und frontal zu einem **zweigeschossigen Haus mit Lamellenfenster**. Der
    Score liegt bei 0.4971 gegen die Schwelle 0.65.

    :func:`aiimaging.geometrie_qa.erreichbarkeit` rechnet daraus den höchsten Score, den
    die Szene überhaupt hergeben kann. Sie steht seit dem 22.08.2026 im Modul und hatte
    **ausser Tests keinen Aufrufer** — die siebte tote Kante dieser Woche.

    Returns:
        ``None``, wenn die Obergrenze hier **keine** ist. Das ist der Normalfall bei jeder
        Hintergrundstrategie ausser :data:`aiimaging.tiefenschaetzer.HG_KEINE`, und es ist
        gemessen: *«geom_iou_obergrenze ist keine Obergrenze — das gemessene geom_iou
        liegt bei drei Stufen darüber»* (HomeStation, 24.08.2026). Eine Erreichbarkeit aus
        einer Zahl zu rechnen, die keine Schranke ist, wäre eine Auskunft mit
        Dezimalpunkt und ohne Deckung.
    """
    from . import geometrie_qa

    if not urteil.get("geom_iou_obergrenze_gilt"):
        return None
    deckel = urteil.get("geom_iou_obergrenze")
    if not isinstance(deckel, (int, float)) or isinstance(deckel, bool):
        return None
    try:
        return geometrie_qa.erreichbarkeit(iou_deckel=float(deckel), schwelle=schwelle,
                                           name="diese Aufnahme")
    except geometrie_qa.QaError:
        return None


def _massstab_gemeldet(bericht: dict) -> dict:
    """Hat die Geometrie plausible Masse? — **gemeldet, nicht abgebrochen.**

    **Der Riegel dafür ist seit langem gebaut und lief auf diesem Weg nirgends.**
    :mod:`aiimaging.torwaechter` nennt in seinem eigenen Docstring den Anlass: *«Eine
    Konversion kann sauber `ok` melden und die Geometrie trotzdem um Faktor 1000
    danebenliegen. Der Runner war zufrieden, das Modell 30 km gross, und der Fehler fiel
    erst am fertigen Bild auf.»*

    Nachgezählt am 26.08.2026: ``torwaechter`` kommt in ``abholer.py``, ``bruecke.py`` und
    ``tools/abholen.py`` **nullmal** vor. Er hing an ``werkzeuge.enqueue_render`` und an
    ``kette.py`` (ohne Aufrufer) — nicht an dem Weg, den ein Auftrag der Oberfläche nimmt.

    Warum hier **nichts** abgebrochen wird
    --------------------------------------
    Der erste Entwurf brach ab, sobald ``pruefe_massstab`` einen ``verdacht_faktor``
    nannte — mit der Begründung, das sei eine *benannte* Bedingung wie bei
    :func:`_kamera_ueber_dach`. **Das war falsch, und eine Gegenprüfung hat es gezeigt.**
    Nachgerechnet an der Funktion selbst:

    =============  ==========  ===================================================
    grösste Kante  Faktor      was das hiesse
    =============  ==========  ===================================================
    0,003–1,0 m    ``0.001``   **jeder Bauteil-Render** — eine Tür, ein Fensterdetail
    3000–10⁶ m     ``1000``    auch **ein einziges verirrtes Mesh** 4 km daneben
    =============  ==========  ===================================================

    Ein ``verdacht_faktor`` ist **kein Beleg für einen Einheitenfehler**. Er sagt nur,
    dass eine Division ein plausibles Ergebnis liefert. Ein Vermessungspunkt, den jemand
    versehentlich mitexportiert hat, bläht die Szenenbox auf 4 km und bekäme die
    Diagnose «Millimeter als Meter gelesen» — die wäre schlicht falsch.

    **Und die Zahl, die diese Entscheidung tragen müsste, hat niemand:** Wie oft der
    Torwächter auf dem echten Bestand ``ablehnen_massstab`` sagt, ist ungemessen — er lief
    ja nie. Gefragt ist das in einem eigenen Auftrag. *Ein Riegel, der scharfgestellt wird,
    bevor seine Fehlalarmrate bekannt ist, lehnt Aufträge ab und niemand weiss, welche.*

    Warum der Bericht **gebaut** und nicht durchgereicht wird
    ---------------------------------------------------------
    ``status`` heisst im Multipass-Bericht etwas anderes als in einem
    ``ifc_to_glb``-Report: dort «die Konversion ist gelungen», hier «die Ausgabedateien
    wurden frisch geschrieben». Dazu ist der Fehlerzweig auf diesem Weg gar nicht
    erreichbar — ``seams.glb_zu_multipass`` wirft bei einem Fehlschlag ``SeamError``, ein
    Bericht mit ``status != "ok"`` kommt hier nie an. Es wird darum ``{"status": "ok",
    "bbox": …}`` gebaut, genau wie in :mod:`aiimaging.werkzeuge` und :mod:`aiimaging.kette`.

    Returns:
        ``{geprueft, quelle, note, entscheidung, beanstandet, groesste_kante_m,
        verdacht_faktor, grund}``. ``geprueft`` ist ``False``, wenn gar keine Hüllbox
        vorlag — **nicht messen ist nicht bestehen**, und jeder Lauf von vor dem
        25.08.2026 sieht so aus.

    .. note::
       **Bevorzugt wird ``bbox_bauwerk``, Rückfall auf ``bbox``, und ``quelle`` sagt
       welche.** Der Grund steht im Torwächter selbst: An 40 echten Dateien fielen zwei
       Modelle mit 1002 m und 1127 m durch — Gelände samt Umgebung, Einheit völlig in
       Ordnung. ``note`` trägt mit, warum die Bauwerksbox fehlt, wenn sie fehlt: Sie ist
       ``None``, sobald ``aiimaging.maske`` aus Blender nicht erreichbar war, und sie ist
       die ganze Szene, wenn Gelände und Bauwerk in **einem** Objekt stecken. In beiden
       Fällen misst man am Ende doch die Geländeplatte, und das darf nicht unsichtbar sein.
    """
    from . import torwaechter as _tw

    bau = bericht.get("bbox_bauwerk")
    bbox = bau if bau is not None else bericht.get("bbox")
    quelle = ("bbox_bauwerk" if bau is not None
              else ("bbox" if bbox is not None else None))

    urteil = _tw.torwaechter({"status": "ok", "bbox": bbox})
    massstab = urteil.get("massstab") or {}
    entscheidung = urteil.get("entscheidung")
    return {
        "geprueft": quelle is not None
        and entscheidung != _tw.ENTSCHEIDUNG_ABLEHNEN_KONVERSION,
        "quelle": quelle,
        "note": bericht.get("bbox_bauwerk_note") or "",
        "entscheidung": entscheidung,
        "beanstandet": entscheidung == _tw.ENTSCHEIDUNG_ABLEHNEN_MASSSTAB,
        "groesste_kante_m": massstab.get("groesste_kante_m"),
        "verdacht_faktor": massstab.get("verdacht_faktor"),
        "grund": urteil.get("begruendung", ""),
    }


def _modellstand_gemeldet(pfad) -> dict:
    """Liegt das Modell hinter seinem Erzeuger zurück? — **einmal je Auftrag, gemeldet.**

    **Der Anlass.** Am 01. und 02.09.2026 sind drei Läufe hintereinander mit
    ``lauf16.glb`` gefahren: 4 Netze, 4 Primitive, **0 Materialien** — obwohl der Export
    seit dem 01.09.2026 welche schreibt — und aus einem IFC mit **0 IfcDoor**, obwohl der
    Erzeuger am Regelgeschossblatt 151 Türen misst. Alle drei Läufe waren grün. Nichts in
    dieser Kette hat gefragt, ob das Modell trägt, was gebaut wurde.

    Warum **je Auftrag** und nicht je Kamera: Der Modellstand ist eine Eigenschaft der
    DATEI, wie der Massstab eine der Geometrie ist (:func:`_massstab_gemeldet`). Der
    Unterschied: Der Massstab steht in der Hüllbox und ist erst nach dem Multipass
    bekannt, hier genügt der glb-Kopf. Der Befund liegt deshalb **vor** dem ersten
    Blender-Start und kostet nichts.

    Warum **gemeldet und nicht abgebrochen**: dieselbe Linie wie beim Massstab, und aus
    demselben Grund. Wie oft der Bestand hier ``zurueck`` sagt, ist ungemessen — es gab
    die Prüfung ja nicht. Ein Riegel, der scharfgestellt wird, bevor seine Fehlalarmrate
    bekannt ist, lehnt Aufträge ab, und niemand weiss welche. Der Befund steht im Urteil
    und im Ergebnissatz; wer ihn zum Abbruch machen will, hat dann Zahlen dafür.

    Returns:
        ``{geprueft, urteil, maengel, warnungen, quelle, grund}``. ``geprueft`` ist nur
        bei :data:`aiimaging.modellstand.TRAEGT` ``True`` — **ungeprüft ist nicht
        bestanden**, und ein Befund, der die Datei gar nicht lesen konnte, erst recht
        nicht. ``quelle`` nennt die Datei, aus der das Modell entstand (Name, Bytes,
        SHA-256), sofern sie es selbst mitteilt: die Antwort auf «welches Modell fährt
        hier eigentlich», die bisher nirgends stand.
    """
    from . import glbbox as _glbbox
    from . import modellstand as _ms

    try:
        befund = _ms.pruefe(pfad)
    except (_glbbox.GlbError, OSError) as e:
        # Ein Lesefehler ist ein Befund über die DATEI und keiner über den Modellstand.
        # Er darf trotzdem nicht als bestanden durchgehen — sonst wäre «unlesbar» der
        # bequemste Weg an der Prüfung vorbei.
        #
        # REGEL 3: Die Meldung der glb-Leser nennt den vollen Pfad, und dieser Befund
        # landet im Auftragsverzeichnis der fremden Oberfläche. `_ohne_pfade` greift
        # hier NICHT — es kürzt nur Zeichenketten, die MIT einem Schrägstrich beginnen,
        # und ein Pfad mitten im Satz bleibt stehen. Er wird darum an der Quelle
        # ersetzt, nicht beim Ablegen.
        name = Path(pfad).name
        return {"geprueft": False, "urteil": _ms.UNGEPRUEFT, "maengel": [],
                "warnungen": [], "quelle": None,
                "grund": (f"Modellstand nicht lesbar: {type(e).__name__}: "
                          f"{str(e).replace(str(pfad), name)}")}
    return {"geprueft": _ms.bestanden(befund), "urteil": befund["urteil"],
            "maengel": befund["maengel"], "warnungen": befund["warnungen"],
            "quelle": befund["quelle"], "grund": befund["begruendung"]}


def _formgelaende_aus_bericht(bericht: dict) -> tuple:
    """Die Geländenamen, die im Lauf die **Form** gefunden hat — sonst leer.

    Die Brücke von der Boxseite zur Bildseite. `blender_depth_stage._bbox_bauwerk` fragt
    seit dem 09.09.2026 `aiimaging.gelaendeform`, wenn die Namensregel fast nichts
    getrennt hat, und legt das Ergebnis in den Bericht. Von dort erreicht es
    `maske.bauwerksmaske(gelaende_zusatz=…)`.

    **Warum nur bei ``"form"`` und nicht, sobald Namen dastehen.** Hat die *Namensregel*
    entschieden, findet die Maske dieselben Namen ohnehin selbst — die Übertragung wäre
    wirkungslos und stünde trotzdem als ``gelaende_quelle: "name+form"`` im Befund.
    *Eine Herkunftsangabe, die eine Absicht meldet statt einer Wirkung, ist keine.*

    **Und warum die Namen hier passen, anders als sonst.** Gemessen am 08.09.2026
    (`docs/NAMENSDECKUNG_2026-09-08.md`): Materialnamen und Knotennamen decken sich zu
    **0 %**. Hier decken sie sich nicht zufällig, sondern **baulich**: `_bbox_bauwerk`
    und `_material_id_zuweisen` lesen beide ``obj.name`` desselben Blender-Objekts.
    """
    if str(bericht.get("bbox_bauwerk_entschieden_durch") or "") != "form":
        return ()
    namen = bericht.get("bbox_bauwerk_gelaende_namen") or []
    # UND IHRE EIGENEN MATERIALE (auf-20261021-316, B3): Traegt die Tabelle Materialnamen,
    # deckt sich kein Objektname — der Runner meldet darum die Materiale, die NUR an
    # Form-Gelaende haengen. Ein geteiltes Material steht dort nicht.
    materialien = bericht.get("bbox_bauwerk_gelaende_materialien") or []
    return tuple(dict.fromkeys(str(n) for n in [*namen, *materialien]))


def _kamera_ueber_dach(kamera: dict) -> dict:
    """Steht die Kamera **höher als das Bauwerk**? — die eine ohne Bild prüfbare Bedingung.

    Sie ist rein arithmetisch (Augenhöhe minus Geländestand gegen Bauwerkshöhe) und
    braucht nichts als den Kamerablock des Multipass-Berichts. Genau darum steht sie
    hier: Das Regelwerk in :mod:`aiimaging.komposition` wirft an dieser Stelle, und die
    Ausnahme fiel bis zum 26.08.2026 **nach** der Diffusion an.

    Returns:
        ``{abbruch, grund}``. ``abbruch`` ist ``False``, wenn sich die Frage nicht stellen
        lässt — eine fehlende Zahl ist **kein** Abbruchgrund, sondern eine fehlende Zahl.
        Der Name ``abbruch`` ist geblieben; seit dem Owner-Entscheid 67 (01.10.2026)
        heisst ``True`` «Aufsicht» und hält nichts mehr an (:func:`_komposition_vor_dem_render`).
    """
    if not isinstance(kamera, dict):
        return {"abbruch": False, "grund": ""}
    auge = kamera.get("auge")
    hoehe = kamera.get("gebaeudehoehe_m")
    boden = kamera.get("gelaende_z")
    try:
        kamerahoehe = float(auge[2]) - float(boden)
        gebaeude = float(hoehe)
    except (TypeError, ValueError, IndexError, KeyError):
        return {"abbruch": False, "grund": ""}
    if gebaeude <= 0.0 or kamerahoehe <= gebaeude:
        return {"abbruch": False, "grund": ""}
    return {"abbruch": True, "grund": (
        f"kamerahoehe_m ({kamerahoehe:.3f}) liegt ueber gebaeudehoehe_m ({gebaeude:.3f}). "
        f"Dann schaut die Kamera auf das Dach herab, und 'Dach und Fuss im Bild' ist die "
        f"falsche Frage.")}


#: Wörter, mit denen ein Bildauftrag eine AUSSENANSICHT bestellt — englisch, denn der
#: Prompt ist an dieser Stelle schon übersetzt (`kosmo_szene.lies_szene`, «klarer Himmel»
#: wird «clear sky»). Bewusst kurz: gestrichen wird nur, was von innen nicht zu sehen sein
#: KANN (Himmel, Wolken, Horizont, die Fassade, «aussen»). Material und Licht bleiben —
#: «heller Putz» und «Tageslicht» gibt es auch im Raum.
AUSSENWOERTER = ("sky", "skies", "cloud", "clouds", "cloudy", "horizon", "facade", "façade",
                 "facades", "exterior", "outdoor", "outdoors", "outside")

#: Was einer Innenkamera vorangestellt wird.
INNEN_VORSATZ = "interior view, inside the room"


def _bildauftrag_innen(prompt: str, innenvermerk, soll) -> dict | None:
    """Der Bildauftrag einer **Innenkamera** — ohne Aussenwörter, mit «interior view» vorn.

    **Der Befund (Sammel-Nachprobe ``auf-20261001-230``, C19):** KosmoOrbit schickt einen
    Prompt für alle Kameras eines Auftrags — dort «Wohnhaus, heller Putz, Holzfenster,
    Tageslicht, klarer Himmel». Die Innenkamera bekam damit ein KI-Bild mit Fassade und
    Himmel, während das Cycles-Schönbild derselben Kamera den Raum zeigte. Die Tiefenkarte
    sagte «Raum», der Text «Himmel», und der Text gewann.

    **Das Kleinste, das trägt:** Segmente des Prompts (durch Komma getrennt), die ein Wort
    aus :data:`AUSSENWOERTER` tragen, fallen weg, und :data:`INNEN_VORSATZ` kommt vorn
    dazu. Sonst bleibt der Text, wie bestellt; was geändert wurde, steht am Urteil und als
    Auskunft in ``verdict.hinweise`` — ein still umgeschriebener Auftrag wäre ein anderes
    Bild unter demselben Namen.

    **Wann eine Kamera innen steht**, entscheidet nicht der Name, sondern der Beleg:

    * ``interior`` muss bestellt sein (``innenvermerk`` gesetzt) — ohne Bestellung wird
      nichts umgeschrieben, auch nicht bei einer Kamera dicht vor einer Wand;
    * und dann entweder ein Standpunkt, den WIR aus den Räumen gerechnet haben
      (``aus_raeumen``), oder — bei mitgesandten Kameras, deren Raum wir nicht kennen —
      eine **randlose Soll-Karte**: Geometrie in jedem Bildpunkt, kein Hintergrund. Von
      aussen sieht eine Kamera Himmel oder Leere neben dem Bauwerk; von innen nicht.
      Die Grenze dieser Regel: Eine Aussenkamera desselben Auftrags, deren Bild ganz von
      einer Wand gefüllt ist, gälte auch als innen. Ihr Himmel wäre dann ohnehin nicht
      im Bild.

    Ob das am Gerät wirkt, ist **ungemessen** (kein GPU-Lauf hier) — die HomeStation muss
    dieselbe Innenkamera einmal mit und ohne diese Anpassung rechnen.

    Returns:
        ``{bestellt, gerechnet, entfernt, vorsatz, grund}`` oder ``None``, wenn nichts
        angepasst wird.
    """
    if not isinstance(innenvermerk, dict) or not isinstance(prompt, str):
        return None
    if innenvermerk.get("standpunkt") == _kosmo_szene.INNEN_STANDPUNKT_AUS_RAEUMEN:
        grund = "Standpunkt aus den Raeumen der IFC gerechnet"
    else:
        flach = _flache_karte(soll)
        if not flach:
            return None
        from . import geometrie_qa
        if not all(geometrie_qa.silhouette(flach)):
            return None
        grund = ("interior bestellt und die Soll-Karte traegt in jedem Bildpunkt Geometrie "
                 "(kein Himmel, keine Leere: die Kamera steht innen)")
    muster = re.compile(r"\b(" + "|".join(re.escape(w) for w in AUSSENWOERTER) + r")\b",
                        re.IGNORECASE)
    teile = [t.strip() for t in prompt.split(",")]
    entfernt = [t for t in teile if t and muster.search(t)]
    bleibt = [t for t in teile if t and not muster.search(t)]
    gerechnet = ", ".join([INNEN_VORSATZ, *bleibt])
    return {"bestellt": prompt, "gerechnet": gerechnet, "entfernt": entfernt,
            "vorsatz": INNEN_VORSATZ, "grund": grund}


def _blick_trifft_szene(bericht: dict) -> dict:
    """Schaut diese Kamera die Szene überhaupt AN? — ohne Bild und ohne Schwellenwert.

    **Der Anlass ist Demolauf 12** (01.09.2026). Eine mitgelieferte Kameraliste kam in
    glTF-Koordinaten herein (``up_axis: "y"``), die Geometrie wurde beim Import nach
    Z-up gedreht, die Kamera nicht. Der Blender-Lauf meldete sich als **gelungen** —
    er hat getan, was dastand — und hinterliess ein Tiefenbild ohne einen einzigen
    Geometriepixel und eine ``material_id`` mit genau einer Farbe. Erst die
    Normalisierung fiel darüber, mit einer Meldung über die **Schranke** statt über
    die Kamera.

    Die Frage ist ohne freien Parameter zu beantworten: Trifft der Sehstrahl von
    ``auge`` nach ``blick_auf`` die Hüllbox der Szene? Das ist die
    Slab-Schnittprüfung eines Strahls gegen einen achsparallelen Quader — kein
    Schwellenwert, keine Deckungsgrad-Annahme, keine Frage des Geschmacks. Ein
    Sehstrahl, der die Box verfehlt, kann kein Bauwerk abbilden.

    An den Zahlen des Vorfalls gemessen (Box ``x 68.513…173.963 · y 60.482…119.692 ·
    z −0.985…29.314``)::

        gestellt  auge (121.238,  0.615, 23.878)  blick_auf (121.238, 11.135, −90.087)  VERFEHLT
        gedreht   auge (121.238, −23.878, 0.615)  blick_auf (121.238, 90.087,  11.135)  trifft

    **Warum hier und nicht im Runner.** Der Runner rahmt, was ihm gesagt wird; die
    Rechnung ist reine Arithmetik und gehört diesseits der Prozessgrenze (Regel 4).
    Und warum nicht in :func:`_rahmung_vor_dem_render`: Der Rahmungsriegel setzt
    ``abbruch`` ausdrücklich auf ``None``, wenn die Kamera **nicht** abgeleitet wurde —
    aus gutem Grund, denn sein Deckungsgrad beschreibt nur den abgeleiteten Weg. Damit
    war der vorgegebene Weg, auf dem die Oberfläche ihre Kameras schickt, **gar nicht
    geprüft**. Diese Frage hier gilt auf beiden Wegen gleich, weil sie keine Rahmung
    beurteilt, sondern die Blickrichtung.

    Returns:
        ``{abbruch, grund, geprueft}``. ``abbruch`` ist ``False``, wenn sich die Frage
        nicht stellen lässt — eine fehlende Hüllbox ist **keine** verfehlte Kamera,
        sondern eine fehlende Hüllbox, und ``geprueft`` sagt welches von beidem.
    """
    kamera = bericht.get("kamera") if isinstance(bericht, dict) else None
    box = bericht.get("bbox") if isinstance(bericht, dict) else None
    if not isinstance(kamera, dict) or not isinstance(box, (list, tuple)) or len(box) != 2:
        return {"abbruch": False, "grund": "", "geprueft": False}
    try:
        auge = [float(v) for v in kamera["auge"]]
        ziel = [float(v) for v in kamera["blick_auf"]]
        lo = [float(v) for v in box[0]]
        hi = [float(v) for v in box[1]]
    except (TypeError, ValueError, KeyError, IndexError):
        return {"abbruch": False, "grund": "", "geprueft": False}
    if len(auge) != 3 or len(ziel) != 3 or len(lo) != 3 or len(hi) != 3:
        return {"abbruch": False, "grund": "", "geprueft": False}

    richtung = [ziel[i] - auge[i] for i in range(3)]
    if not any(abs(r) > 0.0 for r in richtung):
        # Auge und Blickziel fallen zusammen. Das ist keine verfehlte Kamera, das ist
        # gar keine — und der Runner haette daran schon zerbrochen.
        return {"abbruch": False, "grund": "", "geprueft": False}

    nah, fern = 0.0, float("inf")
    for i in range(3):
        if abs(richtung[i]) == 0.0:
            if not (min(lo[i], hi[i]) <= auge[i] <= max(lo[i], hi[i])):
                nah, fern = 1.0, 0.0
                break
            continue
        t1 = (min(lo[i], hi[i]) - auge[i]) / richtung[i]
        t2 = (max(lo[i], hi[i]) - auge[i]) / richtung[i]
        nah = max(nah, min(t1, t2))
        fern = min(fern, max(t1, t2))
    if nah <= fern:
        return {"abbruch": False, "grund": "", "geprueft": True}

    return {"abbruch": True, "geprueft": True, "grund": (
        f"Der Sehstrahl verfehlt die Szene. auge={[round(v, 3) for v in auge]}, "
        f"blick_auf={[round(v, 3) for v in ziel]}, Huellbox "
        f"{[round(v, 3) for v in lo]}…{[round(v, 3) for v in hi]} — kein Punkt des "
        f"Strahls liegt im Quader. Ein Bild davon zeigt kein Bauwerk, und die "
        f"Geometriezahl darauf waere eine Zahl ueber nichts.\n"
        f"HAEUFIGSTE URSACHE: eine Kameraliste in DATEIKOORDINATEN. Blenders "
        f"glTF-Import dreht Y-up nach Z-up (R_x(+90)); eine mitgelieferte Kamera muss "
        f"dieselbe Drehung erfahren. `kosmo_szene.spec_zu_kamera` liest dafuer das "
        f"Pflichtfeld `up_axis` der CameraSpec — wer den Runner direkt aufruft, dreht "
        f"selbst (`kosmo_szene.kamera_nach_blender`).")}


def _referenzpunkt_eintragen(bericht, referenzpunkt):
    """Den ``referenzpunkt`` der Bestellung an den Kamerablock des Berichts — als Kopie.

    Ohne Bestellung oder ohne Kamerablock bleibt der Bericht, wie er ist (dasselbe Objekt).
    Kopiert wird der Block, nicht verändert: Der Bericht kann aus dem Zwischenspeicher oder
    der Grundlage stammen, und dort soll nichts still mitwachsen (Ergebnis 341, e).
    """
    if not referenzpunkt or not isinstance(bericht, dict) \
            or not isinstance(bericht.get("kamera"), dict):
        return bericht
    return dict(bericht, kamera=dict(bericht["kamera"], referenzpunkt=str(referenzpunkt)))


def kamerahoehe_vermerk(komposition, bericht, kuerzel) -> dict | None:
    """``{kamera, satz}`` fuer ``verdict.hinweise`` — die Hoehe dieser Kamera, wenn sie keine
    Augenhoehe ist; sonst ``None``.

    **Anlass (Ergebnis auf-20261022-341, c):** Die Warnungen des Kerns zur Hoehe
    (``komposition.augenhoehe.grund``, ``komposition.kamerahoehe.warnungen``) standen nur in
    ``befund.json``. Wie die Saetze zu Stoff und Stimmung der Variante gehoeren sie ins
    Ergebnis. Ein Satz je Kamera, beginnend mit :data:`aiimaging.kosmo_szene.SATZ_KAMERAHOEHE`:

    * die Augenhoehe-Auskunft, wenn der Standpunkt **nicht** augenhoch ist (ihr Satz nennt den
      Bezug und, wo gemessen, das Gelaende am Standpunkt);
    * die Warnungen der Kamerahoehe aus dem Regelwerk dazu;
    * «GELAENDESTAND NICHT FESTSTELLBAR» aus dem Kamerabericht, wenn kein Gelaende am
      Standpunkt gemessen ist (ist es gemessen, sagt der erste Satz die Hoehe darueber).

    Kein Satz bei einer Aufsicht (sie hat ihren eigenen, ``URTEIL_AUFSICHT``) und keiner, wenn
    der Standpunkt augenhoch ist: Eine Dauerwarnung an jedem Bild verdeckte die echten Faelle.
    **Ausnahme seit Ergebnis auf-20261023-343 (3):** Ruht «augenhoch» auf einem ungemessenen
    Bezug und traegt der Kamerabericht «GELAENDESTAND NICHT FESTSTELLBAR», kommt der Satz doch
    — mit der Auskunft und dieser Warnung.
    """
    komp = komposition if isinstance(komposition, dict) else {}
    if komp.get("aufsicht"):
        return None
    auge = komp.get("augenhoehe") if isinstance(komp.get("augenhoehe"), dict) else {}
    kam = (bericht or {}).get("kamera") if isinstance(bericht, dict) else None
    anfang = _kameras_modul.GELAENDE_UNBEKANNT.split(":")[0]
    gelaendestand = ([str(w) for w in kam.get("warnungen") or () if str(w).startswith(anfang)]
                     if isinstance(kam, dict) and kam.get("gelaende_am_standpunkt_z") is None
                     else [])
    # DER GELAENDESTAND-SATZ AUCH BEI «AUGENHOCH» (Ergebnis auf-20261023-343, 3): Die
    # Auto-Kamera sSE hiess «1.70 m ueber der Huellbox-Unterkante — augenhoch», stand aber 1,32 m
    # ueber dem Boden, und «GELAENDESTAND NICHT FESTSTELLBAR» blieb im Kamerabericht. Ruht das
    # Urteil auf einem ungemessenen Bezug und traegt der Bericht diese Warnung, reist sie mit —
    # dann ist auch ein «augenhoch» nur so gut wie ihr Bezug.
    if auge.get("augenhoch") is not False and not (
            gelaendestand and auge.get("bezug") != "terrain_an_kamera"):
        return None
    teile = [str(auge.get("grund") or "")]
    hoehe = komp.get("kamerahoehe") if isinstance(komp.get("kamerahoehe"), dict) else {}
    if auge.get("augenhoch") is False:
        teile += [str(w) for w in hoehe.get("warnungen") or () if w]
    teile += gelaendestand
    satz = " ".join(t for t in teile if t)
    return {"kamera": str(kuerzel),
            "satz": f"{_kosmo_szene.SATZ_KAMERAHOEHE}, Kamera {str(kuerzel)!r}: {satz}"}


def _komposition_vor_dem_render(bericht: dict) -> dict:
    """Die Kompositionsprüfung — **vor** dem Bildlauf statt danach.

    **Der Anlass sind Zeitstempel eines einzigen Auftrags** (HomeStation,
    `auf-vis-20260826-16`, 26.08.2026), auf die Sekunde aus dem Dateisystem::

        08:47:12  Blender fertig, 40 Meshes, Tiefenkarte und Material-IDs liegen vor
        08:47:49  das fertige Diffusionsbild wird geschrieben
        08:47:58  Auftrag auf 'error': «kamerahoehe_m (77.023) liegt ueber
                  gebaeudehoehe_m (21.3)»

    **Der Riegel arbeitet richtig und zu spät.** Er verhindert die Rechnung nicht, er
    kommentiert sie — und hinterlässt ein plausibel aussehendes Bild im Ausgabeordner,
    das er selbst gleich darauf für untauglich erklärt. Die beiden Zahlen, die er
    vergleicht, lagen **37 Sekunden vor dem Bild** vor.

    Die Trennung, nach der hier verschoben wird, ist die des Berichts:

    * **Ohne das erzeugte Bild prüfbar** — Kamerahöhe gegen Bauwerkshöhe, Rahmung, leere
      Szene. Gehört vor die Diffusion.
    * **Erst danach prüfbar** — ``geometrie_score`` aus ``rho_maske`` und ``geom_iou``.
      Bleibt hinten, denn dafür braucht es das Bild.

    Returns:
        Das Urteil von :func:`aiimaging.komposition.beurteile_bericht`, ergänzt um
        ``abbruch``, ``abbruch_grund`` und ``aufsicht`` (``None``, oder bei einer Kamera
        über dem Dach ``{kamerahoehe_m, gebaeudehoehe_m, grund}``).

    .. important::
       **Seit dem Owner-Entscheid 67 (01.10.2026) bricht hier nichts mehr ab.** Die eine
       benannte Bedingung (:func:`_kamera_ueber_dach`) hielt eine Kamera über dem Dach
       vor dem Render an; jetzt wird sie gerechnet und als ``aufsicht`` vermerkt — siehe
       den Kommentar am Ende. ``abbruch`` bleibt im Urteil, immer ``False``, damit jeder
       Leser dieselben Schlüssel findet.

       **Abgebrochen wurde nur bei einer benannten Bedingung**, nicht bei jeder Ausnahme
       des Regelwerks. Der Unterschied ist gemessen worden, und
       zwar beim Bauen dieser Funktion: ``KompositionError`` trägt auch
       *«Unbekannter bezugspunkt»* — ein **Eingabefehler**, kein Befund über die Aufnahme.
       Jede Ausnahme zum Abbruch zu machen hiesse, aus «wir konnten nicht prüfen» ein
       «durchgefallen» zu machen. Das ist die dritte Antwort dieses Projekts, und sie
       gilt hier wie überall.

       Blosse ``warnungen`` brechen ebenfalls **nichts** ab: Ein Regelwerk, das jede
       Beanstandung zum Abbruch macht, liefert am Ende gar keine Bilder mehr — Warnungen
       sind zum Lesen da, nicht zum Verhindern.
    """
    from . import komposition as _k

    from . import kameras as _kam

    kamera = bericht.get("kamera")
    ueber_dach = _kamera_ueber_dach(kamera)
    # DIE ANDERE RICHTUNG DERSELBEN FRAGE. Der Dachriegel faengt die Kamera, die zu hoch
    # steht, um «Dach und Fuss im Bild» zu fragen. Er sagt aber nichts darueber, ob ein
    # Standpunkt, der KEIN Abbruch ist, die BESTELLUNG erfuellt: Bestellt waren drei
    # augenhohe Perspektiven. Bis zum 03.09.2026 stand in keinem Lauf eine Zahl dazu.
    auge = _kam.augenhoehe_befund(kamera) if isinstance(kamera, dict) else None
    try:
        urteil = _k.beurteile_bericht(kamera)
    except Exception as fehler:                # noqa: BLE001 — siehe Docstring
        urteil = {"beurteilt": False,
                  "grund": (f"Das Regelwerk konnte nicht urteilen: "
                            f"{type(fehler).__name__}: {fehler}. NICHT GEMESSEN — das "
                            f"ist etwas anderes als 'die Aufnahme taugt nicht'.")}

    if not ueber_dach["abbruch"]:
        return dict(urteil, augenhoehe=auge, abbruch=False, abbruch_grund="",
                    aufsicht=None)
    # ÜBER DEM DACH WIRD GERECHNET, MIT VORBEHALT (Owner-Entscheid 67, 01.10.2026).
    #
    # Bis dahin stand hier ein Abbruch: «NICHT RENDERN … nach HABS/NPS keine
    # Architekturaufnahme». Die Sammel-Nachprobe am echten KosmoOrbit (auf-20261001-230)
    # zeigte die Folge: Seine Auto-Kamera «Übersicht» steht 16,3 m hoch bei 6 m Gebaeude,
    # und damit war JEDER Auto-Auftrag `lieferstatus: fehlgeschlagen`. Eine Aufsicht ist
    # eine gewollte Ansicht, keine missratene Augenhoehe.
    #
    # Was fuer sie GILT und was nicht — die Trennung ist die der Frage, nicht der Kamera:
    #   * NICHT: das Regelwerk in `komposition` (Dach und Fuss im Bild, Horizont am
    #     Baukoerper, Neigung/Shift, Bodenanteil). Es beschreibt die Aufnahme in
    #     Augenhoehe nach HABS/NPS und wirft bei einer Kamera ueber dem Dach selbst
    #     (`mindestabstand`). Darum `beurteilt: False` mit einem Satz, der das sagt —
    #     nicht «durchgefallen», sondern «nicht diese Frage».
    #   * WEITER: alles, was vom Standpunkt nicht abhaengt — Blickfeld (trifft der
    #     Sehstrahl die Szene), Rahmungsbefund, Zwillingsabgleich, Geometrie-QA (Tiefe
    #     gegen Bild, Maskenweg, zwei Tore) und Belichtung. Die Tiefenkarte einer
    #     Aufsicht ist so gut ein Massstab wie die einer Augenhoehe.
    #   * AUSKUNFT: der Augenhoehe-Befund bleibt stehen («zu hoch») — er zaehlt, wieviele
    #     bestellte augenhohe Perspektiven es WAREN, und eine Aufsicht ist keine.
    # Augenhoehe-Kameras bleiben unveraendert streng: Fuer sie aendert sich hier nichts.
    hoehe_kamera = _zahl_oder_none(
        (auge or {}).get("kamerahoehe_m") if isinstance(auge, dict) else None)
    return dict(
        urteil, augenhoehe=auge, abbruch=False, abbruch_grund="", beurteilt=False,
        grund=(f"AUFSICHT — Regelwerk fuer Architekturaufnahmen in Augenhoehe NICHT "
               f"angewandt: {ueber_dach['grund']} Gerechnet wird trotzdem (Owner-Entscheid "
               f"67); das ist weder bestanden noch durchgefallen, sondern nicht diese "
               f"Frage."),
        aufsicht={"kamerahoehe_m": hoehe_kamera,
                  "gebaeudehoehe_m": _zahl_oder_none((kamera or {}).get("gebaeudehoehe_m")),
                  "grund": ueber_dach["grund"]})


def _qa_je_kamera_eintraege(kameras) -> list[dict]:
    """Aus unseren Kameraurteilen die Eintraege fuer ihr ``qa_je_kamera``.

    **Eine Kamera, die nicht gemessen wurde, traegt nur ihren Namen** — kein
    Geometrieblock. Das ist Absicht und die dritte Antwort an dieser Stelle: Ein Block
    mit ``geometry_fidelity: null`` und ``passed: false`` laese sich als
    *durchgefallen*, und genau der Unterschied ist hier der Punkt. Wer den Namen ohne
    Block sieht, weiss: diese Ansicht wurde nicht beurteilt.
    """
    aus: list[dict] = []
    for k in kameras or ():
        if not isinstance(k, dict):
            continue
        name = k.get("kamera")
        if not name:
            continue
        satz = {"kamera": str(name)}
        if _kamera_gemessen(k):
            satz["geometrie_urteil"] = k
        elif k.get("ueberstrahlt") or k.get("kontrast"):
            # DIE MESSUNG DER STIMMUNG AUCH OHNE GEOMETRIEURTEIL (auf-20261020-293, Punkt 6):
            # «nur Grundlage» ist nicht gemessen, sein Cycles-Bild aber schon — Ueberstrahlung
            # und Kontrast gehoeren je Kamera ins Ergebnis, ohne einen Geometrieblock.
            satz["stimmung"] = {k2: k[k2] for k2 in ("ueberstrahlt", "kontrast") if k.get(k2)}
        # Aufsicht und angepasster Bildauftrag reisen auch an einer Kamera, deren Messung
        # nicht lief: Gerechnet ist sie trotzdem, und `als_ergebnis` sammelt die Saetze von
        # hier (E67 / auf-20261001-230). Kein Vertragsfeld — `kosmo_szene._qa_je_kamera`
        # liest es nicht hinaus.
        for schluessel in (_kosmo_szene.URTEIL_AUFSICHT, _kosmo_szene.URTEIL_BILDAUFTRAG,
                           # Die Hoehe der Kamera (Ergebnis 341, c) — ebenso kein Vertragsfeld.
                           _kosmo_szene.URTEIL_KAMERAHOEHE,
                           # Die Messschalter (auf-20261021-298, B1) — ebenso kein Vertragsfeld.
                           _kosmo_szene.URTEIL_BILDEINGANG, _kosmo_szene.URTEIL_FARBABGLEICH,
                           # Strang Treue, ebenso kein Vertragsfeld.
                           _kosmo_szene.URTEIL_UMRISS_HALTEN,
                           # Wie das Bild entstand, mit Satz bei Abweichung (auf-20261021-312
                           # B3) — die Zeile in `angewandt.modus` baut `modus_des_auftrags`.
                           URTEIL_MODUS,
                           # Dasselbe in gelaeufigen Woertern, mit denoise (auf-20261022-336).
                           URTEIL_KI):
            if k.get(schluessel):
                satz[schluessel] = k[schluessel]
        aus.append(satz)
    return aus


#: Wie viele Bilder eine bestellte Kamera bekommt: **genau eines** (23.09.2026).
#:
#: Am Code abgelesen, nicht angenommen: `verarbeiter` haengt je gerenderter Kamera genau
#: ein Bild an `bilder` an — das des besten Startwerts, von `_bester_seed` unter
#: ``<kamera>.png`` abgelegt. Die uebrigen Startwerte sind KANDIDATEN der Auswahl und
#: keine Lieferung; sie erscheinen nicht in ``images``. Ihr ``render-scene``-Vertrag hat
#: kein Feld fuer mehrere Bilder je Kamera, soweit wir ihn lesen
#: (`kosmo_szene.BEKANNTE_FELDER`). Bestellt ist also eine Ansicht, und eine Ansicht ist
#: ein Bild.
BILDER_JE_KAMERA = 1


def _lieferung_der_kamera(urteil: dict) -> dict:
    """Die vier Lieferfelder einer Kamera — ``kosmo_szene.FELDER_LIEFERUNG``.

    **Die Einteilung (23.09.2026), und ihr Massstab.** Ihr Vertrag trennt
    ``uebersprungen`` — ein regulaerer Weg, auf dem absichtlich kein Bild entsteht,
    eingefuehrt fuer ``skip: true`` (erg-20260917-37 F3) — von ``fehlgeschlagen``. Die
    Frage, die hier entscheidet: *Muss die bestellende Seite etwas aendern, um dieses
    Bild zu bekommen?* Ja: ``fehlgeschlagen``. Nein: ``uebersprungen``.

    * **Gerendert** (``bild_png``, kein Zwilling): ``geliefert``, 1 von 1. Ob die QA
      bestand, ist eine andere Frage und steht im ``geometry``-Block daneben.
    * **Zwilling** (``doppelt_von``): ``uebersprungen``, 0 von 1. Die Ansicht ist
      geliefert — als Bild der anderen Kamera —, und niemand muss etwas tun. Ein
      eigenes Bild gibt es nicht; ``bilder_ist`` zaehlt Bilder, nicht Ansichten.
    * **Abbruch vor dem Render** (Blickfeld, Rahmung; bis zum 01.10.2026 auch die
      Kamerahoehe, seit E67 gerechnet): ``fehlgeschlagen``, 0 von 1. Absichtlich von
      UNS, aber nicht von der Bestellung: Wer das Bild will, muss die Kamera aendern.
      Unter ``uebersprungen`` saehe das aus wie ein Zustand, in dem nichts zu tun ist.
    * **Bildmodell hier nicht rechenbar** (``umgebung``, auf-20261001-230):
      ``fehlgeschlagen``, 0 von 1, mit dem Satz aus ``render.pipeline_lage``. Wer das
      Bild will, muss ein anderes Modell bestellen — oder wir die Umgebung nachruesten.
    * **Kein Bild ohne benannten Grund**: ``fehlgeschlagen`` mit dem Grund des Urteils.
      Auf dem Produktweg heute nicht erreichbar; steht da, damit ein kuenftiger Weg ohne
      Bild nicht still als geliefert durchgeht.

    Der Grund bei Abbruechen ist derselbe Satz, den ``verdict.reason`` schon traegt
    (:func:`_satz_ohne_bild`) — eine Auskunft, zwei Orte, ein Wortlaut.
    """
    name = urteil.get("kamera")
    soll = BILDER_JE_KAMERA
    vorbild = urteil.get("doppelt_von")
    art = _art_ohne_bild(urteil)
    if vorbild:
        # Der Zwilling traegt das `bild_png` seines Vorbilds (abgelesen am 23.09.2026:
        # `dict(zwilling["urteil"], kamera=…, doppelt_von=…)`). Darum ZUERST gefragt —
        # sonst zaehlte ein Bild zweimal, und die Summe der Kameras stimmte nicht mehr
        # mit `images` ueberein.
        return {"lieferstatus": _kosmo_szene.LIEFERSTATUS_UEBERSPRUNGEN,
                "lieferstatus_grund": (
                    f"{_satz_ohne_bild('doppelt', str(name))}: dieselbe Ansicht wie "
                    f"Kamera {str(vorbild)!r}, deren Bild sie zeigt — kein eigenes Bild"),
                "bilder_soll": soll, "bilder_ist": 0}
    if urteil.get("bild_png"):
        return {"lieferstatus": _kosmo_szene.LIEFERSTATUS_GELIEFERT,
                "lieferstatus_grund": "", "bilder_soll": soll, "bilder_ist": soll}
    if art == "umgebung":
        grund = _satz_ohne_bild(art, str(name), [urteil["umgebung"].get("satz")])
    elif art is not None:
        breite = (urteil.get("rahmung") or {}).get("wirksame_bildbreite")
        grund = _satz_ohne_bild(art, str(name),
                                [breite] if isinstance(breite, float) else None)
    else:
        grund = (f"KEIN BILD, {name}: Das Kameraurteil nennt keinen der bekannten "
                 f"Abbruchgruende. {urteil.get('grund') or 'Ohne Angabe.'}")
    return {"lieferstatus": _kosmo_szene.LIEFERSTATUS_FEHLGESCHLAGEN,
            "lieferstatus_grund": grund, "bilder_soll": soll, "bilder_ist": 0}


def _je_kamera_mit_lieferung(kameras) -> list[dict]:
    """:func:`_qa_je_kamera_eintraege` — und an jedem Eintrag die Lieferung der Kamera.

    Eintrag fuer Eintrag ueber dieselbe Funktion, damit ein Urteil, das dort
    uebergangen wird (kein Name), auch hier keinen Eintrag bekommt.
    """
    aus: list[dict] = []
    for urteil in kameras or ():
        eintrag = _qa_je_kamera_eintraege([urteil])
        if eintrag:
            zusatz = {}
            # Startwert und Pose (Nr. 85/68), nur wenn der Lauf sie kennt.
            seed = (urteil.get("seedauswahl") or {}).get("gewaehlt")
            if isinstance(seed, int) and not isinstance(seed, bool):
                zusatz["seed"] = seed
            if isinstance(urteil.get("pose"), dict):
                zusatz["pose"] = urteil["pose"]
            # Deckung (L4-1): die Kanten-IoU, nur wenn gemessen.
            iou = (urteil.get("deckung") or {}).get("kanten_iou")
            if isinstance(iou, (int, float)) and not isinstance(iou, bool) and 0.0 <= iou <= 1.0:
                zusatz["deckung"] = float(iou)
            aus.append(dict(eintrag[0], **_lieferung_der_kamera(urteil), **zusatz))
    return aus


def _kamera_gemessen(urteil: dict) -> bool:
    """Wurde diese Kamera gemessen? ``gemessen`` gilt, wo es steht — sonst ``status``.

    **Nachgestellt am 22.09.2026 am Produktweg:** Hier stand ``k.get("gemessen")``. Das
    Feld setzt aber nur :func:`_uebersprungenes_urteil` (auf ``False``); ein Urteil aus
    ``tiefenschaetzer.qa_gegen_soll`` traegt stattdessen ``status: "ok"``. Zwei gemessene
    Kameras kamen darum in ``qa_je_kamera`` als ``[{"kamera": …}, {"kamera": …}]`` an —
    nur Namen, also *nicht gemessen*, obwohl beide gemessen waren. Die Proben dieser
    Funktion setzten ``gemessen: True`` von Hand und sahen den Fehler nie.

    Ein Urteil mit ``status`` ausser ``"ok"`` (``abgelehnt``, ``fehler``) gilt weiter als
    nicht gemessen: Es traegt keine Zahl, und ein Block mit ``passed: false`` laese sich
    als durchgefallen.
    """
    gemessen = urteil.get("gemessen")
    if gemessen is not None:
        return gemessen is True
    return urteil.get("status") == "ok"


def _zahl_oder_none(wert):
    """Eine endliche Zahl — oder ``None``, und dann heisst es NICHT GEMESSEN.

    ``geometrie_qa.zwei_tore`` wirft bei allem, was weder Zahl noch ``None`` ist. Ein
    kaputtes Feld an einer Kamera darf hier aber nicht den ganzen Auftrag mitnehmen; es
    wird zu *nicht gemessen*, und genau so steht es danach im Block. ``bool`` zaehlt
    nicht als Zahl (``True >= 0.10`` waere wahr).
    """
    if isinstance(wert, bool) or not isinstance(wert, (int, float)):
        return None
    return float(wert) if math.isfinite(wert) else None


def _zwei_tore_dieser_kamera(urteil: dict) -> dict | None:
    """Das Urteil aus :func:`geometrie_qa.zwei_tore` fuer EINE gemessene Kamera.

    **Tor A** liest ``rho_maske.gerichtet`` — denselben Wert, den
    ``geometrie_qa.paarurteil`` liest; ein negatives ``rho`` (vertauschte Tiefe) faellt
    damit durch, wie es soll. **Tor B** liest ``geom_iou``, dieselbe Zahl wie
    ``qa.geometry.geom_iou`` — ausser ohne gemeinsame Silhouette: Dort ist sie eine
    fehlende Messung, und Tor B bekommt ``None``.

    **Ohne Gegenprobe.** Eine fremde Geometrie wird auf diesem Weg nicht gerechnet; das
    Urteil sagt das selbst (``counter_check_status: fehlt``, ``released: false``). Es ist
    damit *vorlaeufig* — aber es steht da, statt still zu fehlen.
    """
    from . import geometrie_qa
    # Eine Kamera, deren Messung gar nicht lief (`status: fehler`), bekommt KEIN Urteil
    # und nicht eines aus zwei `None`: `zwei_tore(None, None)` ist fail-closed und
    # meldete `passed: false` — fuer ein Bild, ueber das nichts bekannt ist.
    if not _kamera_gemessen(urteil):
        return None
    maske = urteil.get("rho_maske")
    rho = _zahl_oder_none(maske.get("gerichtet") if isinstance(maske, dict) else None)
    # OHNE GEMEINSAME SILHOUETTE ist `geom_iou` 0.0 eine FEHLENDE MESSUNG (Durchsicht
    # 22.09.2026): So nennt es `verdict.reason` im selben Ergebnis, und Tor B darf dieselbe
    # Zahl nicht als gemessen fuehren. Siehe `kosmo_szene.keine_gemeinsame_silhouette`.
    # RANDLOSE SOLL-SILHOUETTE (Sammel-Nachprobe auf-20261001-230, Innenkamera mit
    # geom_iou 1.0): Die Zahl misst nichts, Tor B bekommt sie nicht — und das Tor sagt,
    # dass sie NICHT ANWENDBAR ist, nicht bloss «nicht gemessen».
    randlos = _kosmo_szene.soll_silhouette_randlos(urteil)
    iou = (None if randlos or _kosmo_szene.keine_gemeinsame_silhouette(urteil)
           else _zahl_oder_none(urteil.get("geom_iou")))
    tore = geometrie_qa.zwei_tore(rho, iou)
    if randlos:
        grund = f"geom_iou NICHT ANWENDBAR: {_kosmo_szene.SATZ_GEOM_IOU_RANDLOS}."
        tore["tor_dieses"] = dict(tore["tor_dieses"], nicht_anwendbar=grund)
        tore["warnungen"] = [*(tore.get("warnungen") or ()), grund]
    return tore


#: Die Engine eines Laufs ohne KI-Schritt: Blenders Cycles, als Prozess (Regel 2). Eine
#: Lizenz wird nicht gemeldet — das Bild ist kein Werk des Programms, und `engine_license`
#: spricht im Vertrag ueber Bildmodelle.
ENGINE_NUR_GRUNDLAGE = {"name": "cycles", "lizenz": None, "fuehrung": None,
                        "lizenz_offen": False}


def _stimmungsmessung(szene: dict, bericht: dict, maske) -> dict:
    """Was am Cycles-Bild einer Stimmung gemessen wird — leer ohne Stimmung.

    * ``ueberstrahlt`` (auf-20261020-292, B1): Anteil voll weisser Bildpunkte am Haus.
    * ``kontrast`` (auf-20261020-293, Punkt 1): Grauwert des Hauses minus Hintergrund daneben.

    Beides Auskunft, kein Tor; im Ergebnis ``qa.ueberstrahlt_anteil`` und
    ``qa.kontrast_haus_hintergrund``. **Eine Stelle für beide Zweige** — mit und ohne
    KI-Schritt —, damit kein Zweig sie wieder vergisst (293, Punkt 6).
    """
    if not (szene or {}).get("umgebung"):
        return {}
    schoen = (bericht or {}).get("beauty_png")
    return {"ueberstrahlt": _belichtung_modul.ueberstrahlt_aus_png(schoen, maske=maske),
            "kontrast": _belichtung_modul.kontrast_aus_pngs(
                schoen, (bericht or {}).get("material_id_png"), maske=maske)}


def _kontrast_am_ki_bild(szene: dict, bericht: dict, ki_png, maske) -> dict | None:
    """Der Kontrast Haus – Hintergrund am **KI-Bild** — ``None`` ohne Stimmung.

    **Anlass (Ergebnis auf-20261022-334):** ``qa.kontrast_haus_hintergrund`` wird am
    Cycles-Bild gemessen; bei der KI-Variante «mittag» stand dort −27,7, das KI-Haus war aber
    heller als der Himmel (grob +37). Jetzt steht die Zahl am KI-Bild daneben
    (``qa.kontrast_haus_hintergrund_ki``), gemessen mit :func:`belichtung.kontrast_aus_pngs`
    — derselben Formel, derselben Bauwerksmaske und demselben ID-Pass wie am Cycles-Bild.
    Eine Auskunft: Die Warnung «HAUS KAUM SICHTBAR» bleibt am Cycles-Wert.
    Passt das KI-Bild in der Grösse nicht zum ID-Pass, sagt der Befund ``grund``.
    """
    if not (szene or {}).get("umgebung"):
        return None
    return _belichtung_modul.kontrast_aus_pngs(
        ki_png, (bericht or {}).get("material_id_png"), maske=maske)


def fenster_der_kamera(ki_png, bericht, maske) -> dict | None:
    """«Fenster gehalten» einer Kamera (Mac-Befund 23.10.2026) — ``None`` ohne Glas im ID-Pass.

    :func:`aiimaging.varianten.fenster_aus_bildern` am gelieferten KI-Bild gegen das
    Cycles-Bild, an den Glas-Bildpunkten des Material-ID-Passes in der Bauwerksmaske. Ohne Glas
    im ID-Pass bleibt das Feld weg (kein Haus muss Fenster haben); sonst steht der Befund da,
    auch «nicht gemessen» mit Grund. Nie eine Ausnahme — eine Zusatzauskunft haelt keinen Lauf.
    """
    bericht = bericht or {}
    if not varianten.glasfarben(bericht.get("material_id_tabelle")):
        return None
    try:
        return varianten.fenster_aus_bildern(
            ki_png, bericht.get("beauty_png"), bericht.get("material_id_png"),
            bericht.get("material_id_tabelle"), maske=maske)
    except Exception as fehler:        # noqa: BLE001 — eine Zusatzauskunft haelt den Lauf nicht auf
        return {"anteil": None, "gehalten": None, "grund": f"Fenster nicht messbar: {fehler}"}


def _urteil_nur_grundlage(kuerzel, bericht, aus, *, rahmung, komposition, massstab,
                          blickfeld, modellstand, ebenen, sonne, innen) -> dict:
    """Das Urteil einer Kamera, deren Bild das Cycles-Bild ist (Nr. 83/81, 20.10.2026).

    Nicht gemessen (``score: None``) und doch geliefert: Die Geometrie-QA misst, ob ein
    BILDMODELL dem Modell folgt; ohne Bildmodell gibt es nichts zu messen — das Bild IST
    das Modell. Es traegt dieselben Felder wie ein gerechnetes, damit kein Leser verzweigt.
    """
    import shutil
    schoen = bericht.get("beauty_png")
    if not (isinstance(schoen, str) and Path(schoen).is_file()):
        raise AbholerError(
            f"Kamera {kuerzel!r}: «nur Grundlage» bestellt, aber der Multipass hat kein "
            f"Schoenbild (beauty_png) geschrieben. Ohne es gibt es kein Bild zu liefern. "
            f"Grund laut Bericht: {bericht.get('beauty_png_fehler')}")
    ziel = Path(aus) / f"{kuerzel}.png"
    shutil.copyfile(schoen, ziel)
    urteil = dict(_uebersprungenes_urteil(kuerzel, rahmung or {}),
                  grund=("Nur Grundlage: das Cycles-Bild, kein KI-Schritt — nicht gemessen, "
                         "weil kein Bildmodell gerechnet hat."),
                  bild_png=str(ziel), nur_grundlage=True, doppelt_von=None,
                  rahmung=rahmung, komposition=komposition, massstab=massstab,
                  blickfeld=blickfeld, modellstand=modellstand, ebenen=ebenen,
                  sonne=sonne, engine=dict(ENGINE_NUR_GRUNDLAGE),
                  zwischenspeicher=bericht.get("zwischenspeicher"),
                  pose=pose_aus_bericht(bericht), **innen)
    urteil[_kosmo_szene.URTEIL_AUFSICHT] = None
    urteil[_kosmo_szene.URTEIL_BILDAUFTRAG] = None
    return urteil


def _uebersprungenes_urteil(kuerzel, rahmung: dict) -> dict:
    """Das Urteil einer Kamera, die **gar nicht erst gerendert** wurde.

    Es trägt ``score: None`` und ``gemessen: False``, und das ist die ganze Absicht:
    :func:`_schlechtestes` wertet ein Urteil ohne Wert als das schlechteste überhaupt,
    :func:`_kameraspanne` zählt es **nicht** als gemessen. Ein übersprungener Lauf
    verbessert also nichts und verschwindet nirgends — er ist *nicht gemessen*, und das
    ist weder bestanden noch durchgefallen.
    """
    # `zwei_tore: None` ausdruecklich und nicht weggelassen (22.09.2026): Ist diese Kamera
    # die schlechteste, liest `kosmo_szene.als_ergebnis` daran, dass der Block
    # `geometry_gates` als NICHT GEMESSEN erscheinen soll — statt ganz zu fehlen, was
    # von «nie angeschlossen» nicht zu unterscheiden waere.
    return {"kamera": kuerzel, "score": None, "bestanden": None, "gemessen": False,
            "zustaendig": False, "bild_png": None, "rahmung": rahmung,
            "grund": rahmung.get("abbruch_grund") or rahmung.get("grund", ""),
            _kosmo_szene.URTEIL_ZWEI_TORE: None}


def _mit_messboden(soll, breite, hoehe, bericht, maskenbefund):
    """Die Trennhilfe aus dem Messboden — oder ``None``, mit dem Grund im Befund.

    **Nur zum Trennen** (Owner-Entscheid 78, Nachtrag 13.10.2026): Zurueck kommt die
    unveraenderte Soll-Karte und, wenn angewandt, die Liste der Punkte, an denen der Boden
    laege — fuer ``qa_gegen_soll(trennhilfe=…)``. Sie zaehlen nur beim Trennen von Haus und
    Hintergrund im Bild, nicht im Score.

    Nur, wenn die Maske GEMESSEN hat (``gemessen`` True). **Befund ``auf-20261008-274``
    C3:** Bis dahin genuegte ``gelaende_erkannt`` False — auch bei einer ungemessenen Maske,
    und am Testbau mit (unerkannter) Gelaendeplatte lag dann ein Messboden 25 cm unter der
    Platte.

    **Seit auf-20261020-293 (B4) auch MIT erkanntem Gelaende.** Die Vorschau auf dem Testbau
    (Platte 40 x 30 m, Kamera knapp darueber) meldete ``n_soll = n_ist = 67541`` und
    ``n_gemeinsam = 0``, obwohl das Haus deckungsgleich lag (Umriss 0,81). Ursache ist
    nicht die Bildgroesse (gemessen wird auf der Grundlage, das KI-Bild geht vorher auf ihre
    Grösse zurueck, und eine andere Länge weist ``qa_gegen_soll`` ab), sondern derselbe Fall
    wie 272: Das Bild malt VOR der endlichen Platte Boden, die Soll-Karte hat dort Himmel,
    und die Auswahl «die n naechsten Punkte» nimmt den gemalten Vordergrund statt des Hauses.
    Die Trennhilfe zaehlt nur beim Trennen (Score und Anteil bleiben die des Hauses) und
    belegt nur HINTERGRUND-Punkte der Soll-Karte — die Platte selbst bleibt, wie sie ist.

    Returns:
        ``(soll, trennhilfe_oder_None, befund_oder_None)``.
    """
    from aiimaging import messboden as _messboden
    befund_maske = maskenbefund or {}
    if befund_maske.get("gemessen") is not True or befund_maske.get("gelaende_erkannt") not in (
            False, True):
        return soll, None, None
    if not soll or isinstance(soll[0], (list, tuple)) or breite is None or hoehe is None:
        return soll, None, None
    try:
        neu, befund = _messboden.mit_messboden(soll, int(breite), int(hoehe),
                                               (bericht or {}).get("kamera") or {})
    except _messboden.MessbodenError as fehler:
        return soll, None, {"angewandt": False, "grund": str(fehler)}
    trennhilfe = [a != b for a, b in zip(neu, soll)]
    angewandt = befund["n_boden"] > 0
    return soll, (trennhilfe if angewandt else None), dict(
        befund, angewandt=angewandt, nur_zum_trennen=True,
        neben_gelaende=befund_maske.get("gelaende_erkannt") is True)


def _ohne_umgebung(soll, kontext_pixel):
    """Die Soll-Karte mit der Umgebung als Hintergrund (``inf``) — flach oder zeilenweise.

    Passt die Laenge nicht, bleibt die Karte, wie sie war: Geraten wird nicht.
    """
    import math as _math
    if soll and isinstance(soll[0], (list, tuple)):
        flach = [w for zeile in soll for w in zeile]
        if len(flach) != len(kontext_pixel):
            return soll
        aus, i = [], 0
        for zeile in soll:
            aus.append([_math.inf if kontext_pixel[i + j] else w for j, w in enumerate(zeile)])
            i += len(zeile)
        return aus
    if len(soll) != len(kontext_pixel):
        return soll
    return [_math.inf if k else w for w, k in zip(soll, kontext_pixel)]


#: Wo die gemerkten Nullanker liegen — unter der Ablage der Grundlagen.
NULLANKER_ORDNER = "_nullanker"
#: Die Fassung der Rechnung hinter den Ankern. Wer an `_nullprobe`, an den Kontrollbildern
#: oder an der Messung etwas aendert, das die Anker verschiebt, zaehlt hier hoch — dann
#: gilt kein gemerkter Anker mehr.
NULLANKER_FASSUNG = 1


def nullanker_schluessel(soll, breite, hoehe, *, messen=None, maske=None,
                         ausblendung=None, grenze=None) -> str:
    """Der Inhaltsschluessel der Nullanker: Soll-Karte, Masse, Maske, Ausblendung, Schaetzer.

    Alles, wovon :func:`_nullprobe` abhaengt, geht hinein — die Kontrollbilder sind fest
    (``bildschreiben.KONTROLL_SEED``), der Schaetzer ist der der Messung. Gleicher
    Schluessel heisst gleiche Eingaben, also gleiche Anker.
    """
    import array
    import hashlib
    import json as _json

    from . import bildschreiben as _bs, tiefenschaetzer as _ts
    h = hashlib.sha256()
    h.update(_json.dumps({
        "fassung": NULLANKER_FASSUNG, "breite": breite, "hoehe": hoehe,
        "schaetzer": _ts.VORGABE_TIEFENSCHAETZER,
        "messung": f"{getattr(messen, '__module__', '')}.{getattr(messen, '__qualname__', '')}",
        "arten": list(_bs.KONTROLLARTEN), "seed": _bs.KONTROLL_SEED,
        "grenze": grenze}, sort_keys=True)
        .encode("utf-8"))
    h.update(array.array("d", (float(x) for x in soll)).tobytes())
    aus = ausblendung or {}
    for teil in (maske, aus.get("ausblenden"), aus.get("trennhilfe")):
        h.update(b"|-" if teil is None else b"|+")
        if teil is not None:
            h.update(bytes(1 if t else 0 for t in teil))
    return h.hexdigest()[:32]


def _nullprobe_gemerkt(wurzel, rechne, *, soll, breite, hoehe, messen=None, maske=None,
                       ausblendung=None, grenze=None):
    """Die Nullanker aus dem Gedaechtnis, sonst gerechnet und gemerkt.

    Ohne Ablage der Grundlagen (kein ``--out-wurzel``) wird immer gerechnet — wie bisher.
    Ein unlesbarer oder fehlender Eintrag heisst ebenfalls rechnen; gemerkt wird nur, was
    sich messen liess (mindestens ein Anker).
    """
    import json as _json
    if wurzel is None or breite is None or hoehe is None:
        return rechne()
    try:
        schluessel = nullanker_schluessel(soll, breite, hoehe, messen=messen, maske=maske,
                                          ausblendung=ausblendung, grenze=grenze)
    except (TypeError, ValueError):
        return rechne()
    datei = Path(wurzel) / NULLANKER_ORDNER / f"{schluessel}.json"
    try:
        satz = _json.loads(datei.read_text(encoding="utf-8"))
        return satz.get("anker"), satz.get("maskenanker")
    except (OSError, ValueError, AttributeError):
        pass
    anker, maskenanker = rechne()
    if anker or maskenanker:
        try:
            datei.parent.mkdir(parents=True, exist_ok=True)
            tmp = datei.with_suffix(".json.tmp")
            tmp.write_text(_json.dumps({"anker": anker, "maskenanker": maskenanker}),
                           encoding="utf-8")
            tmp.replace(datei)
        except OSError:
            pass
    return anker, maskenanker


def _nullprobe(ordner, soll, breite, hoehe, *, bildschreiben, messen, grenze,
               tiefen_modell=None, maske=None,
               ausblenden=None, trennhilfe=None) -> tuple[dict | None, dict | None]:
    """Was Bilder **ohne jede Geometrie** auf dieser Soll-Karte erreichen.

    Die Anker werden **gemessen und nicht nachgeschlagen.** Eine Tabelle nach Szenennamen
    hätte zwei Fehler: Der Aufrufer kennt den Namen nicht, und zwei Szenen desselben
    Namens sind nicht dieselbe Szene. Der Anker gehört zur **Soll-Karte**, und die liegt
    vor.

    Kostet keinen Renderlauf — nur je einen Durchgang des Tiefenschätzers auf einem
    synthetischen Bild.

    Ein einzelner gescheiterter Anker macht die Nullprobe **nicht** wertlos: Gemeldet wird,
    was gemessen wurde. Scheitert alles, gibt es ``None``, und :func:`geometrie_qa.einordnung`
    sagt dann ausdrücklich, dass keine Einordnung vorliegt — statt eine zu erfinden.

    **Zwei Ankersätze aus EINEM Durchgang** (seit 22.08.): der Score über das ganze Bild
    und, wenn eine Maske vorliegt, ρ und Kante über der Maske. Die Kontrollbilder werden
    dabei nur **einmal** geschrieben und einmal geschätzt — ein zweiter Durchgang würde
    die Schätzerläufe verdoppeln, ohne eine einzige neue Zahl zu liefern.

    Getrennt zurückgegeben und nicht vermischt: Der erste Satz ist ``{art: score}`` und
    wird von :func:`geometrie_qa.einordnung` als **Zahlen** gelesen; der zweite ist
    ``{art: {rho, kante}}``. Beide in ein Wörterbuch zu legen hiesse, einen reservierten
    Schlüssel zu erfinden, der mit einer Kontrollart kollidieren kann.

    **Warum der Maskenboden je Soll-Karte gemessen wird und nicht nachgeschlagen:**
    :data:`geometrie_qa.RAUSCHBODEN_UEBER_MASKE` (−0.5207) stammt aus **einer** Szene
    (`auf-20260821-24`), und die Schwelle des Paartests bezieht sich darauf. Eine feste
    Zahl für alle Szenen ist genau der Fehler, an dem die Geometrie-Schwelle 0.65
    gescheitert ist.
    """
    if breite is None or hoehe is None:
        return None, None
    anker: dict[str, float] = {}
    maskenanker: dict[str, dict] = {}
    for art in bildschreiben.KONTROLLARTEN:
        try:
            bild = bildschreiben.schreibe_kontrollbild(
                Path(ordner) / f"nullprobe_{art}.png", art, int(breite), int(hoehe))
            urteil = messen(str(bild), soll, breite=breite, hoehe=hoehe,
                            modell=tiefen_modell, schwelle=grenze, maske=maske,
                            **({"ausblenden": ausblenden} if ausblenden else {}),
                            # Seit E78a (13.10.2026): Ohne diesen Parameter brach jeder
                            # Auftrag ohne Gelaende mit Nullprobe ab (auf-20261013-275,
                            # Fehler 3) — die Proben liefen alle mit nullprobe=False.
                            **({"trennhilfe": trennhilfe} if trennhilfe else {}))
        except Exception:      # noqa: BLE001 — ein Anker darf den Auftrag nicht mitnehmen
            continue
        if not urteil:
            continue
        if urteil.get("score") is not None:
            anker[art] = float(urteil["score"])
        rho = (urteil.get("rho_maske") or {}).get("gerichtet")
        kante = (urteil.get("kante") or {}).get("gerichtet")
        if rho is not None or kante is not None:
            maskenanker[art] = {"rho": rho, "kante": kante}
    return (anker or None), (maskenanker or None)


def _belichtung_urteil(bild, stil, rahmen, pruefen) -> dict | None:
    """Die Belichtung eines Bildes — oder eine benannte Lücke.

    Gibt ``None`` **nur**, wenn gar kein Stil verlangt wurde. Ist ein Stil verlangt und
    hat keinen Rahmen, entsteht ein Wörterbuch mit ``gemessen: False`` und dem Grund —
    denn *nicht gemessen* ist etwas anderes als *nicht verlangt*, und beides ist etwas
    anderes als *in Ordnung*.

    Ein Fehler beim Messen hält den Auftrag **nicht** auf: Ein unlesbares Bild ist ein
    Befund der Geometrie-QA, die dasselbe Bild ohnehin anfasst; hier wäre es ein zweiter
    Abbruch aus demselben Grund.
    """
    if not stil:
        return None
    if rahmen is None:
        return {"gemessen": False, "stil": stil, "grund": (
            f"Für den Stil {stil!r} gibt es keinen Belichtungsrahmen. Es wird NICHT auf "
            f"einen anderen zurückgefallen — das wäre ein Urteil über einen Stil anhand "
            f"der Zahlen eines anderen, und es stünde nirgends, dass es so war.")}
    try:
        urteil = pruefen(bild, rahmen)
    except Exception as fehler:      # noqa: BLE001 — siehe Docstring
        return {"gemessen": False, "stil": stil,
                "grund": f"Belichtung nicht messbar: {type(fehler).__name__}: {fehler}"}
    return dict(urteil, gemessen=True)


#: Wie das Stil-Urteil zustande kam, wenn es aus dem Belichtungsrahmen stammt.
#:
#: **Warum das ein eigener Name sein muss.** Der fremde Vertrag führt für den Stil ein
#: Feld ``style_score`` und meint damit eine **Bildähnlichkeit** — eine Zahl aus dem
#: Vergleich zweier Einbettungen. Unser Stil-Urteil ist seit dem Owner-Entscheid vom
#: 21.08.2026 etwas anderes: ein **fest formulierter** Stil, geprüft gegen einen
#: gemessenen Belichtungsrahmen (Mittel ± 2σ aus `auf-20260818-14`). Beides beantwortet
#: dieselbe Frage — *sieht das aus wie gewollt?* —, aber mit verschiedenen Mitteln.
#:
#: Ein Abzeichen, das nicht sagt, womit es verdient wurde, ist eine stille Falschaussage.
#: Darum wandert dieser Name in ``method``, und ``style_score`` bleibt **leer**: Eine
#: Belichtungsprüfung hat keinen natürlichen Skalar, und einen zu erfinden wäre genau die
#: Bequemlichkeit, gegen die dieses Projekt gebaut ist.
VERFAHREN_BELICHTUNG = "belichtungsrahmen"


#: Wonach unter mehreren Startwerten ausgewählt wird: ``"umriss"`` oder ``"rho"``.
#:
#: **«umriss» seit dem 30.09.2026 abends** (Owner-Entscheid «1», Regel vor der Messung
#: festgelegt, Sitzung 73 §11/§16). Bestätigungsreihe ``auf-20260930-190`` (36 Bilder,
#: Bauwerksrahmung, Auge blind): In 5 von 5 Fällen mit einem richtig stehenden Bild setzte
#: die Umrisstreue ein solches auf Platz 1, ρ nur in 3 — ρ wählte einmal eine Öffnung in
#: einer Glaswand, einmal einen Glaskörper in einer Fassade. **Vorbehalt, ausdrücklich:**
#: Zählt man «unklar» als richtig, liegen beide gleichauf (6 von 6); und in ``auf-186``
#: (nach der Szene gerahmt) war es umgekehrt. Mit ``"rho"`` gilt die alte Auswahl.
SEEDAUSWAHL_NACH = "umriss"


def _umriss_abhebung(bild_png, soll, breite, hoehe):
    """Die Abhebung der Umrisstreue — oder ``None``, wenn sie nicht messbar ist."""
    if soll is None or not breite or not hoehe:
        return None
    from aiimaging import umriss
    try:
        aus = umriss.umriss_aus_dateien(bild_png, soll, breite, hoehe)
    except Exception:                                    # noqa: BLE001
        return None
    wert = aus.get("abhebung")
    return float(wert) if isinstance(wert, (int, float)) else None


def _formpruefung(bild_png, soll, breite, hoehe):
    """Die Formprüfung als Auskunft (``auf-20260930-195``) — oder ``None``, wenn nicht messbar."""
    if soll is None or not breite or not hoehe:
        return None
    from aiimaging import bildlesen, formkandidaten
    try:
        luminanz, b, h = bildlesen.lies_png_luminanz(bild_png)
        if (b, h) != (breite, hoehe):
            return None
        return formkandidaten.formpruefung(luminanz, soll, breite, hoehe)
    except Exception:                                    # noqa: BLE001
        return None


def _bester_seed(seeds, aus, kuerzel, rendere_seed, messe, *, maske_da: bool,
                 soll=None, breite=None, hoehe=None):
    """Mehrere Seeds rendern und den besten behalten — oder begründet nur einen.

    **Warum es das gibt (gemessen am 22.08.2026, `docs/POLARITAET_UND_STAERKE_2026-08-22.md`):**
    Bei identischen Einstellungen liefert derselbe Aufbau einmal ρ = −0.91 und einmal
    −0.27. Über neun Läufe: Mittel −0.66, Streuung **0.2269** — und damit **grösser als
    jeder Parametereffekt**, den die Kette noch hergibt (Stärke 0.65 ↔ 1.00: 0.10 bis
    0.14). Drei von neun Läufen erreichten die Schwelle, sechs nicht.

    Solange das so ist, ist die Auswahl über mehrere Seeds der billigste Qualitätssprung
    der ganzen Kette: Ein Bild kostet rund 1,3 Sekunden, die Messung je Bild einen
    Tiefenschätzer-Durchgang. Aus dem Mittel wird der beste von dreien.

    **Ausgewählt wird nach ``gerichtet``** (Polarität × ρ über der Bauwerksmaske, +1
    perfekt) — **nicht** nach ``score``. Der Score über das ganze Bild belohnt auf einer
    Bodenszene die Bodenfläche und hat am 21.08. ein Bild OHNE Bauwerk höher bewertet als
    das perfekte (`auf-20260821-26`). Wer danach auswählte, wählte das Falsche.

    **Ohne Maske wird NICHT ausgewählt.** Dann gibt es kein Mass, dem hier zu trauen wäre,
    und die Funktion rendert genau einen Seed und sagt, warum. Eine Auswahl nach einem
    Mass, das die Abwesenheit belohnt, wäre schlechter als keine.

    Returns:
        ``(ergebnis, urteil, auswahl)``. ``auswahl`` trägt **alle** Seeds mit ihren
        Werten, nicht nur den Sieger: Wer nur den besten sähe, hielte die Kette für
        besser, als sie ist.
    """
    import shutil

    seeds = list(seeds) if seeds else [0]
    ziel_png = str(aus / f"{kuerzel}.png")
    vorsprung = None

    if len(seeds) == 1 or not maske_da:
        erg = rendere_seed(seeds[0], ziel_png)
        urteil = messe(erg["bild_png"])
        grund = ("Nur ein Seed angefordert." if len(seeds) == 1 else
                 f"{len(seeds)} Seeds angefordert, aber es gibt KEINE Bauwerksmaske — "
                 f"und ohne sie kein Mass, nach dem sich auswaehlen liesse. Der Score "
                 f"ueber das ganze Bild taugt dafuer nicht (auf-20260821-26: ein Bild "
                 f"ohne Bauwerk erreichte dort 0.9848 gegen 0.9703 fuer das perfekte). "
                 f"Gerendert wurde seed {seeds[0]}; die uebrigen sind UNGEMESSEN.")
        # `vorsprung: None` steht hier ausdrücklich und fehlt nicht bloss. Ein
        # abwesender Schlüssel zwingt jeden Leser zu einem `.get(...)` und damit zu der
        # Frage, ob „nicht da" nun „kein Vorsprung" heisst oder „nicht geprüft". Es
        # heisst: nicht geprüft, denn es gab nichts zu vergleichen.
        return erg, urteil, {"gewaehlt": seeds[0], "kandidaten": [seeds[0]],
                             "ausgewaehlt": False, "vorsprung": None, "grund": grund,
                             "formpruefung": _formpruefung(erg["bild_png"], soll, breite,
                                                           hoehe)}

    kandidaten = []
    for seed in seeds:
        png = str(aus / f"{kuerzel}_seed{seed}.png")
        erg = rendere_seed(seed, png)
        urteil = messe(erg["bild_png"])
        # Die Form ist AM CODE ABGELESEN, nicht geraten: `qa_gegen_soll` reicht
        # `_maskenweg` mit `**` durch, also stehen `rho_maske`, `kante` und `paarurteil`
        # ganz oben — und `gerichtet` liegt IN `rho_maske` (tiefenschaetzer.py:1128,
        # geometrie_qa.rho_ueber_maske). Ein erster Versuch griff auf `urteil["maske"]`
        # zu; das gibt es nicht, und die Auswahl waere still auf «ungemessen» gefallen.
        rm = urteil.get("rho_maske")
        gerichtet = rm.get("gerichtet") if isinstance(rm, dict) else None
        paar = urteil.get("paarurteil")
        kandidaten.append({"seed": seed, "gerichtet": gerichtet, "paarurteil": paar,
                           "abhebung": _umriss_abhebung(erg["bild_png"], soll, breite, hoehe),
                           "bild": erg["bild_png"], "_erg": erg, "_urteil": urteil})

    nach_umriss = [k for k in kandidaten if k["abhebung"] is not None]
    messbar = [k for k in kandidaten if k["gerichtet"] is not None]
    if SEEDAUSWAHL_NACH == "umriss" and nach_umriss:
        sieger = max(nach_umriss, key=lambda k: k["abhebung"])
        werte = sorted((k["abhebung"] for k in nach_umriss), reverse=True)
        # Kein belegter Vorsprung: Den Boden der Umrisstreue zwischen zwei Wuerfen hat
        # niemand gemessen — ihn am Boden von rho zu pruefen, verglich zwei Masse.
        vorsprung = None
        grund = (f"Bester von {len(nach_umriss)} Seeds nach der UMRISSTREUE (abhebung, "
                 f"Kanten im Bild an den Soll-Spruengen; um 1 heisst Zufall). Spanne "
                 f"{min(werte):.3f} bis {max(werte):.3f}. Seit 30.09.2026 (auf-190); "
                 f"rho steht als Auskunft daneben. Ob der Vorsprung ueber dem Rauschen "
                 f"liegt, ist UNGEMESSEN.")
        ausgewaehlt = True
    elif not messbar:
        # Alle ungemessen: dann ist der erste so gut wie jeder andere, und das gehoert
        # gesagt statt kaschiert.
        sieger = kandidaten[0]
        grund = ("Keiner der Seeds lieferte ein Maskenurteil — ausgewaehlt wurde nicht, "
                 "sondern der erste genommen. UNGEMESSEN, nicht bestanden.")
        ausgewaehlt = False
    else:
        sieger = max(messbar, key=lambda k: k["gerichtet"])
        werte = sorted((k["gerichtet"] for k in messbar), reverse=True)
        # IST der Sieger besser — oder hatte er nur Glück?
        #
        # Die Handlung bleibt dieselbe: Das bestbewertete Bild wird behalten, und das ist
        # richtig, denn man nimmt den besten Wurf, den man hat. Die BEHAUPTUNG ist eine
        # andere: „Seed X ist besser als Seed Y" hält nur, wenn der Abstand grösser ist
        # als das Rauschen der Kette. Gemessen sind dort 0.2269 — mehr als jeder
        # Parametereffekt, den die Kette hergibt.
        #
        # Geprüft wird gegen den UNABHÄNGIG gemessenen Boden, nicht gegen die Streuung
        # dieser drei Werte: Wer den Bestwert einer Reihe an der Streuung derselben Reihe
        # misst, misst im Kreis.
        vorsprung = (varianten.ist_unterschied_belegt(
            werte[0], werte[1], varianten.GEMESSENER_BODEN)
            if len(werte) > 1 else None)
        grund = (f"Bester von {len(messbar)} gemessenen Seeds nach 'gerichtet' "
                 f"(Polaritaet x rho ueber der Maske, +1 perfekt). "
                 f"Spanne {min(werte):+.4f} bis {max(werte):+.4f}.")
        if vorsprung is not None and not vorsprung["belegt"]:
            grund += (f" ABER: {vorsprung['begruendung']} Das behaltene Bild ist der "
                      f"beste WURF, nicht der bessere Seed — wer diesen Startwert "
                      f"kuenftig bevorzugt, bevorzugt Rauschen.")
        elif vorsprung is not None:
            grund += f" Der Vorsprung ist belegt: {vorsprung['begruendung']}"
        ausgewaehlt = True

    shutil.copyfile(sieger["bild"], ziel_png)
    _groesse_ablegen(aus, kuerzel, ziel_png)
    erg = dict(sieger["_erg"], bild_png=ziel_png)
    auswahl = {"gewaehlt": sieger["seed"], "ausgewaehlt": ausgewaehlt, "grund": grund,
               "vorsprung": vorsprung,
               # Auskunft seit auf-195, urteilt nicht: die Umrisstreue folgt dem Auge.
               "formpruefung": _formpruefung(sieger["bild"], soll, breite, hoehe),
               "nach": SEEDAUSWAHL_NACH if any(k.get("abhebung") is not None
                                                for k in kandidaten) else "rho",
               "kandidaten": [{"seed": k["seed"], "gerichtet": k["gerichtet"],
                               "abhebung": k.get("abhebung"),
                               "paarurteil": k.get("paarurteil")} for k in kandidaten]}
    _auswahl_ablegen(aus, kuerzel, auswahl)
    return erg, sieger["_urteil"], auswahl


def _groesse_ablegen(aus, kuerzel, bild_png) -> None:
    """Die **Groesse** des Bildes neben das Bild legen. Nur die Zahl, kein Urteil.

    **Was hier bis zum 04.09.2026 stand und warum es weg ist.** Bis gestern legte diese
    Funktion eine verkleinerte Kopie an, sobald das Bild ueber dem Deckel der Gegenstelle
    lag (1 048 576 Base64-Zeichen = 786 432 Byte). Das war bei **60 von 66** Nutzbildern
    der Fall, Median 1 277 231 Byte — also fast immer. Der Owner hat den Deckel am
    04.09.2026 entfernt («Deckel weg»), nachdem die Messung vom 03.09. gezeigt hatte,
    dass er 1.0 MB HIESS und 0.79 MB WAR und dass ein technischer Grund fuer die Zahl
    nirgends auffindbar ist.

    **Die Messung bleibt, der Zwang faellt.** Eine Kette, die ihre eigene Ausgabegroesse
    nicht kennt, haette diesen Befund nie erheben koennen — die Zahl war das Werkzeug,
    das den Deckel ueberfuehrt hat, und sie hat nichts verbrochen. Was faellt, ist die
    ungefragte zweite Datei: Niemand hat um eine kleinere Kopie gebeten, und wer eine
    will, ruft :func:`aiimaging.bildschreiben.kleinere_fassung` mit einer Grenze, die er
    selbst nennt.

    Wie ``_auswahl_ablegen``: Ein Fehlschlag hier darf den Lauf nicht kosten. Das Bild
    ist da; die Groesse ist eine Auskunft ueber es, keine Stufe.
    """
    import json as _json

    from . import bildschreiben        # lokal wie in `_verarbeite`, siehe dort

    try:
        (Path(aus) / f"{kuerzel}_groesse.json").write_text(
            _json.dumps(bildschreiben.bildgroesse(bild_png),
                        ensure_ascii=False, indent=1),
            encoding="utf-8")
    except (OSError, ValueError):        # SchreibError ist ein ValueError
        pass


def _auswahl_ablegen(aus, kuerzel, auswahl) -> None:
    """Den Auswahlbericht **neben die Bilder** schreiben — der Vertrag trägt ihn nicht.

    ``kosmovis.render-result/v2`` führt genau ``images``, ``qa`` und ``timings``. Der
    Auswahlbericht passt dort nicht hinein, und den fremden Vertrag zu erweitern ist nicht
    meine Entscheidung. Verloren gehen darf er trotzdem nicht: **Wer nur den Sieger sieht,
    hält die Kette für besser, als sie ist** — genau die Verwechslung, gegen die dieses
    Projekt seit dem Rauschanker antritt.

    Also eine Datei daneben. Sie verlässt das Repo nie und trägt nur Zahlen.
    """
    import json as _json
    try:
        (Path(aus) / f"{kuerzel}_seedauswahl.json").write_text(
            _json.dumps(auswahl, ensure_ascii=False, indent=1), encoding="utf-8")
    except OSError:
        # Ein fehlgeschlagener Bericht darf den Lauf nicht kosten — das Bild ist da, die
        # Auswahl ist getroffen, und `auswahl` geht ohnehin auch im Urteil mit.
        pass


#: Die Maskenbeschaffung ist am 26.08.2026 nach :mod:`aiimaging.maske` gewandert.
#:
#: **Der Anlass war eine Zaehlung von der anderen Seite:** `qa_gegen_soll` hat drei
#: Aufrufstellen — diesen Abholer, `kette.py` und `tools/homeworker.py`. Nur diese eine
#: reichte eine Maske herein. Die beiden anderen massen den Maskenweg gar nicht, und
#: niemand sagte es; die Zeile im Kurzbefund gibt es nur hier.
#:
#: Solange die Funktion privat im Abholer stand, konnte keine der beiden sie rufen, ohne
#: sie zu verdoppeln. Jetzt steht sie an der Stelle, an der die Maske ohnehin gebaut wird.
_maske_bauen = maske_modul.maske_aus_bericht


def _stil_urteil_aus_belichtung(urteile: list[dict], stil: str | None) -> dict | None:
    """Aus den Belichtungsurteilen der Kameras ein Stil-Urteil für den Vertrag machen.

    **Was dieser Entscheid möglich gemacht hat.** Bis zum 21.08.2026 lief die Stil-QA im
    Abholer bewusst **nicht**: Sie war an ein Referenzset gebunden, das es nicht gibt, und
    fremde Bilder können es nicht sein (eine Einbettung ist eine Ableitung des Bildes).
    Der Owner hat sich an jenem Tag für einen **fest formulierten** Hausstil entschieden —
    und damit ist die Frage nicht mehr *„ähnelt das unseren Referenzen"*, sondern *„liegt
    das im gemessenen Rahmen"*. Diese Frage können wir beantworten.

    Gewertet wird das **schwächste** Bild, wie überall hier: Ein Auftrag ist so gut wie
    seine schlechteste Kamera, und ein Mittelwert liesse ein durchgefallenes Bild hinter
    zwei bestandenen verschwinden.

    Returns:
        ``None``, wenn gar kein Stil verlangt war — *nicht verlangt* ist etwas anderes als
        *nicht gemessen*. Sonst ein Wörterbuch mit ``score: None`` (siehe
        :data:`VERFAHREN_BELICHTUNG`), ``bestanden``, ``gemessen`` und dem Verfahren.
    """
    if not stil:
        return None
    belichtungen = [u.get("belichtung") for u in urteile if u.get("belichtung")]
    if not belichtungen:
        return {"score": None, "schwelle": None, "bestanden": None, "gemessen": False,
                "verfahren": VERFAHREN_BELICHTUNG, "stil": stil,
                "einbetter_name": f"{VERFAHREN_BELICHTUNG}/{stil}",
                "grund": (f"Stil {stil!r} war verlangt, aber kein einziges Bild wurde auf "
                          f"die Belichtung geprüft. Ungeprüft ist nicht in Ordnung.")}

    ungemessen = [b for b in belichtungen if not b.get("gemessen")]
    if ungemessen:
        return {"score": None, "schwelle": None, "bestanden": None, "gemessen": False,
                "verfahren": VERFAHREN_BELICHTUNG, "stil": stil,
                "einbetter_name": f"{VERFAHREN_BELICHTUNG}/{stil}",
                "grund": ungemessen[0].get("grund", "Belichtung nicht messbar.")}

    # Alle gemessen: Es zählt das schwächste Bild.
    schlechtestes = min(belichtungen, key=lambda b: bool(b.get("bestanden")))
    return {"score": None, "schwelle": None,
            "bestanden": bool(schlechtestes.get("bestanden")), "gemessen": True,
            "verfahren": VERFAHREN_BELICHTUNG, "stil": stil,
            "einbetter_name": f"{VERFAHREN_BELICHTUNG}/{stil}",
            "grund": schlechtestes.get("zusammenfassung", "")}


def _bodenspanne(urteile: list[dict]) -> dict | None:
    """Vergleicht die Kameras **gegen ihren jeweils eigenen Rauschboden** — und meldet, wenn
    das eine andere schwächste Kamera ergibt als der rohe Vergleich.

    **Warum das seit dem 24.08.2026 nötig ist.** Der Schätzer hat ein festes Ortsfeld
    (:data:`geometrie_qa.RAUSCHBODEN_UEBER_MASKE`): Wo die Maske im Bild liegt, bestimmt
    den Nullpunkt von ρ — über 96 Bildpunkte hinweg gemessen von −0,62 bis +0,65, **mit
    Vorzeichenwechsel**.

    **Und unsere Kameras liegen genau in dieser Grössenordnung auseinander.** Nachgerechnet
    für `MODUS_SHIFT`, den Vorgabemodus seit dem 23.08., bei 1600 × 992:

        Flachbau  8 m auf 40 m   Shift  2,0 mm →  89 px senkrecht
        Wohnhaus 15 m auf 35 m   Shift  5,8 mm → 258 px
        Wohnhaus 15 m auf 25 m   Shift  8,1 mm → 361 px
        Grenze MAX_SHIFT_MM 12 mm            → 533 px

    Ein bis fünf Schritte des Rasters also, auf dem der Rauschboden um mehr als eine ganze
    ρ-Einheit wandert. **Zwei Kameras desselben Auftrags vergleichen damit Zahlen auf
    verschiedenen Skalen.**

    **Die Regel wird trotzdem nicht geändert** — «schlechteste bleibt» ist ein
    Owner-Entscheid vom 22.08. Was hier entsteht, ist die **zweite Rechnung daneben**:
    dieselbe Auswahl, aber nach ρ **minus dem gemessenen Boden dieser Kamera**. Stimmen
    beide überein, ist die Sache ohne Folgen; weichen sie ab, ist das ein Befund, den
    jemand entscheiden muss — und kein stiller Skalenfehler.

    Returns:
        ``None``, wenn weniger als zwei Kameras einen Bodenabstand haben — dann gibt es
        nichts zu vergleichen. Sonst ``{schlechteste_roh, schlechteste_nach_boden,
        einig, n, hinweis}``.
    """
    mit_boden = [u for u in urteile or []
                 if isinstance((u.get("bodenabstand") or {}).get("abstand"), (int, float))
                 and isinstance(((u.get("rho_maske") or {}).get("gerichtet")), (int, float))]
    if len(mit_boden) < 2:
        return None

    roh = min(mit_boden, key=lambda u: u["rho_maske"]["gerichtet"])
    nach_boden = min(mit_boden, key=lambda u: u["bodenabstand"]["abstand"])
    einig = roh.get("kamera") == nach_boden.get("kamera")

    if einig:
        hinweis = (f"Roh und nach Rauschboden dieselbe schwaechste Kamera "
                   f"({roh.get('kamera')}) — die Ortsfeld-Frage hat hier keine Folgen.")
    else:
        hinweis = (
            f"UNEINIG: Roh ist {roh.get('kamera')!r} die schwaechste Kamera "
            f"(rho {roh['rho_maske']['gerichtet']:+.4f}), nach Abzug des GEMESSENEN "
            f"Rauschbodens aber {nach_boden.get('kamera')!r} "
            f"(Abstand {nach_boden['bodenabstand']['abstand']:+.4f} gegen "
            f"{roh['bodenabstand']['abstand']:+.4f}). Der Unterschied ist das Ortsfeld des "
            f"Schaetzers: Wo die Maske im Bild liegt, verschiebt den Nullpunkt von rho um "
            f"mehr als eine ganze Einheit (auf-vis-20260824-10). Welche der beiden Zahlen "
            f"das Urteil tragen soll, ist NICHT entschieden — gemeldet wird weiterhin die "
            f"rohe, weil das der Owner-Entscheid vom 22.08. ist.")
    return {"schlechteste_roh": roh.get("kamera"),
            "schlechteste_nach_boden": nach_boden.get("kamera"),
            "einig": einig, "n": len(mit_boden), "hinweis": hinweis}


def _kameraspanne(urteile: list[dict]) -> dict:
    """Wie die eine gemeldete Zahl aus mehreren Kameras entstanden ist.

    **Der Anlass ist eine Nebenwirkung, die niemand entschieden hat.** Am 23.08.2026
    gingen die automatischen Richtungen von einer auf drei. Das Urteil eines Auftrags ist
    das seiner schwächsten Kamera — richtig so —, aber ein **Minimum fällt mit der Zahl
    der Ziehungen**, ganz ohne dass sich an der Sache etwas ändert. Das Gate wurde damit
    strenger, und zwar um rund 0,845 Streuungen
    (:func:`aiimaging.geometrie_qa.minimum_abschlag`).

    Wäre die Streuung zwischen Kameras so gross wie die einzige, die dieses Projekt
    gemessen hat (0,2269 über Startwerte), wären das **0,19** — mehr als jeder
    Parametereffekt, den die Kette je gezeigt hat.

    Die Regel wird deshalb nicht geändert; sie ist gut begründet. Was sich ändert, ist,
    dass die gemeldete Zahl **mitträgt, wie sie entstanden ist**: aus wie vielen Kameras,
    wie weit sie auseinanderlagen, und was das Minimum daran kostet.

    Returns:
        ``{n, n_gemessen, n_paar_gemessen, n_paar_durchgefallen, n_doppelt, bester,
        schlechtester, spanne, streuung, abschlag_streuungen, hinweis}``. ``streuung``
        ist ``None`` bei weniger als drei gemessenen Kameras — aus zweien lässt sie sich
        ausrechnen und sagt nichts.

        ``n_gemessen`` zählt **Scores**, ``n_paar_gemessen`` die gemessenen
        **Paarurteile**. Die beiden laufen auseinander, und genau daran hing Demolauf 14:
        Ohne gemeinsame Silhouette gibt es keinen Score, den Maskenweg aber sehr wohl.

        ``n`` zählt **alle** Ansichten, ``n_gemessen`` nur die eigenständigen mit Wert.
        Eine Ansicht mit ``doppelt_von`` ist **keine zweite Ziehung**: Sie fällt aus
        ``n_gemessen``, aus der Streuung und aus dem Abschlag heraus. Mitgezählt wäre sie
        eine stille Verschärfung — dieselbe Fehlerart wie am 23.08.2026, als drei
        Ansichten das Gate ungefragt strenger machten.
    """
    # Lokal importiert wie in `verarbeiter`: Der Modulkopf dieses Moduls bleibt leicht,
    # damit `import aiimaging` nicht die halbe Kette mitzieht.
    from . import geometrie_qa

    # Eine DOPPELTE Ansicht ist keine zweite Ziehung. Sie zaehlt hier nicht mit, und
    # zwar in beide Richtungen: Der Auswahleffekt eines Minimums haengt an der Zahl der
    # UNABHAENGIGEN Ziehungen, und die gemeldete Streuung ebenso. Wer sie mitzaehlte,
    # verschaerfte das Gate still — genau der Fehler vom 23.08.2026, als drei Ansichten
    # ungefragt strenger wurden (auf-vis-20260824-12, Doppelansicht).
    eigen = [u for u in urteile or [] if not u.get("doppelt_von")]
    werte = [u.get("score") for u in eigen]
    messbar = [float(w) for w in werte if isinstance(w, (int, float))
               and not isinstance(w, bool)]
    n = len(urteile or [])
    n_doppelt = len(urteile or []) - len(eigen)
    abschlag = geometrie_qa.minimum_abschlag(len(messbar))

    streuung = None
    if len(messbar) >= 3:
        mittel = sum(messbar) / len(messbar)
        streuung = (sum((w - mittel) ** 2 for w in messbar) / len(messbar)) ** 0.5

    if not messbar:
        # «UNGEPRUEFT» GILT NUR, WENN AUCH DAS ZWEITE TOR SCHWIEG — Demolauf 14.
        #
        # `n_gemessen` zaehlt Scores, der Satz sprach aber ueber den ganzen Lauf. In
        # Lauf 14 hatte keine Kamera einen Score (`n_gemeinsam` 0) und JEDE ein
        # gemessenes, durchgefallenes Paarurteil — gemeldet wurde trotzdem
        # «UNGEPRUEFT, nicht durchgefallen». Genau verkehrt herum: Der Lauf ist an dem
        # Tor gescheitert, das die ABWESENHEIT eines Bauwerks faengt, und sah im
        # Bericht harmlos aus.
        paare = [(u.get("paarurteil") or {}) for u in eigen]
        gemessene_paare = [p for p in paare if p.get("gemessen") is True]
        gefallene_paare = [p for p in gemessene_paare if p.get("bestanden") is False]
        if gemessene_paare and all(p.get("urteilt") is False for p in gemessene_paare):
            hinweis = (
                f"Keine der {n} Kameras hat einen SCORE. Der Maskenweg hat an "
                f"{len(gemessene_paare)} von {len(eigen)} rho gemessen, URTEILT aber nicht "
                f"(Schwelle nicht geeicht, auf-20260929-175) — das gemeldete Urteil ist "
                f"UNGEPRUEFT, nicht durchgefallen.")
        elif gemessene_paare:
            hinweis = (
                f"Keine der {n} Kameras hat einen SCORE. Der Maskenweg hat aber an "
                f"{len(gemessene_paare)} von {len(eigen)} gemessen, davon "
                f"{len(gefallene_paare)} DURCHGEFALLEN — das gemeldete Urteil ist damit "
                f"geprueft und nicht ungeprueft.")
        else:
            hinweis = (f"Keine der {n} Kameras ist gemessen — weder Score noch "
                       f"Maskenweg. Das gemeldete Urteil ist UNGEPRUEFT, nicht "
                       f"durchgefallen.")
    elif len(messbar) == 1:
        hinweis = ("Eine gemessene Kamera — das gemeldete Urteil IST ihr Urteil, ohne "
                   "Auswahleffekt.")
    else:
        hinweis = (
            f"Gemeldet wird das SCHLECHTESTE von {len(messbar)} gemessenen Kameras "
            f"(Spanne {min(messbar):.4f} bis {max(messbar):.4f}). Ein Minimum faellt mit "
            f"der Zahl der Ziehungen: bei {len(messbar)} liegt es rechnerisch "
            f"{abschlag:.3f} Streuungen unter dem Mittel, auch wenn sich an der Sache "
            f"nichts aendert. Wer dieses Ergebnis mit einem aelteren aus EINER Kamera "
            f"vergleicht, vergleicht zwei verschieden strenge Masse."
        )

    if n_doppelt:
        hinweis += (
            f" {n_doppelt} der {n} Ansichten war mit einer anderen IDENTISCH und zaehlt "
            f"hier NICHT mit — bei zweizaehliger Drehsymmetrie fallen die beiden "
            f"Ueber-Eck-Ansichten zusammen. Mitgezaehlt waere es eine stille "
            f"Verschaerfung: Das Minimum faellt mit der Zahl der Ziehungen, und eine "
            f"Wiederholung ist keine Ziehung."
        )

    # Als ZAHL und nicht nur im Fliesstext. Ein Hinweis, den nur ein Mensch lesen kann,
    # ist derselbe Fehler eine Etage hoeher: Die Auskunft war da und kam nicht an.
    paare_alle = [(u.get("paarurteil") or {}) for u in eigen]
    paar_gemessen = [p for p in paare_alle if p.get("gemessen") is True]

    return {
        "n": n,
        "n_gemessen": len(messbar),
        "n_paar_gemessen": len(paar_gemessen),
        "n_paar_durchgefallen": sum(1 for p in paar_gemessen
                                    if p.get("bestanden") is False),
        "n_doppelt": n_doppelt,
        "bester": max(messbar) if messbar else None,
        "schlechtester": min(messbar) if messbar else None,
        "spanne": (max(messbar) - min(messbar)) if len(messbar) > 1 else None,
        "streuung": streuung,
        "abschlag_streuungen": abschlag,
        "hinweis": hinweis,
    }


def _schlechtestes(urteile: list[dict]) -> dict | None:
    """Das Urteil der schwächsten Kamera — **kein Mittelwert**.

    Ein Mittelwert über Urteile liesse ein durchgefallenes Bild hinter zwei bestandenen
    verschwinden. Ein Auftrag ist so gut wie sein schwächstes Bild.

    Urteile ohne Wert (``score is None`` — die Messung ist gar nicht gelaufen) gelten als
    die schlechtesten überhaupt: *ungemessen* ist nicht *in Ordnung*.
    """
    if not urteile:
        return None
    return min(urteile, key=lambda u: (u.get("score") is not None,
                                       u.get("score") if u.get("score") is not None else 0.0))
