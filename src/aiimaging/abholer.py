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

import time
from pathlib import Path

from . import bruecke, fortschritt, maske as maske_modul

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


class AbholerError(ValueError):
    """Der Abholer ist falsch aufgesetzt. Erbt von ``ValueError`` wie alle Fehler hier."""


def _zeit(_uhr) -> float:
    return float((_uhr or time.time)())


def waisen(store, *, frist_s: float = WAISENFRIST_S, _uhr=None) -> list[dict]:
    """Aufträge, die auf ``running`` stehen und die niemand mehr bearbeitet.

    Sie werden **gemeldet und nicht neu eingereiht**. Ein zweiter Lauf desselben Auftrags
    kostet eine GPU-Stunde und erzeugt womöglich ein zweites Bild unter derselben Kennung;
    ob das gewollt ist, weiss der Betreiber.

    Erkannt an der Änderungszeit des **Laufzettels**, nicht an einem Feld darin. Ein Feld
    müsste jemand fortschreiben, und genau dieser Jemand ist im Waisenfall gestorben.

    Returns:
        Liste von ``{verzeichnis, job_id, still_seit_s, detail}``, nach Verzeichnis
        sortiert.
    """
    jetzt = _zeit(_uhr)
    gefunden: list[dict] = []
    for ordner in bruecke.offene_auftraege(store, nur_status=(bruecke.STATUS_RUNNING,)):
        zettel = ordner / bruecke.DATEI_LAUFZETTEL
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
                f"'{bruecke.STATUS_RUNNING}', ohne dass sich sein Laufzettel geändert "
                f"hätte (Frist {frist_s / 3600:.1f} h). Der bearbeitende Lauf ist "
                f"vermutlich gestorben. **Nicht** automatisch neu eingereiht: Ein "
                f"zweiter Lauf kostet eine GPU-Stunde und kann ein zweites Bild unter "
                f"derselben Kennung erzeugen. Das ist eine Entscheidung des Betreibers."
            ),
        })
    return gefunden


def hole_einen(verzeichnis, *, verarbeite, fremde_freigabe_gilt: bool = False,
               darf_rechnen=None, wache_bauen=None,
               beobachtungs_takt_s: float = fortschritt.BEOBACHTUNGS_TAKT_S) -> dict:
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

    Returns:
        ``{tat, job_id, verzeichnis, grund, ergebnis, wache}``. ``tat`` ist eine der
        ``TAT_*``-Konstanten. ``wache`` ist der Bericht des Beobachters oder ``None``,
        wenn keine Wache gebaut wurde.

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
               "verzeichnis": ordner, "grund": "", "ergebnis": None, "wache": None}

    try:
        auftrag = bruecke.lies_auftrag(ordner, fremde_freigabe_gilt=fremde_freigabe_gilt)
    except bruecke.BrueckenError as fehler:
        antwort["grund"] = f"Auftrag nicht lesbar: {fehler}"
        return antwort

    antwort["job_id"] = auftrag.get("job_id") or ordner.name

    if auftrag["maengel"]:
        antwort["grund"] = (
            "Der Auftrag hat Mängel, die einen Lauf verbieten:\n- "
            + "\n- ".join(auftrag["maengel"])
        )
        return antwort

    darf, warum = _karte_frei(auftrag["laufzettel"], darf_rechnen)
    if not darf:
        antwort["grund"] = warum
        return antwort

    # Ab hier wird gerechnet. Erst jetzt auf `running` — vorher hätte ein
    # liegengelassener Auftrag ausgesehen, als arbeite jemand an ihm.
    bruecke.setze_status(ordner, bruecke.STATUS_RUNNING)
    beobachter = _beobachter_bauen(auftrag, wache_bauen, beobachtungs_takt_s, antwort)
    if beobachter is not None:
        beobachter.start()
    try:
        ergebnis = verarbeite(auftrag)
    except Exception as fehler:            # noqa: BLE001 — jeder Fehler ist ein Ergebnis
        bruecke.setze_status(ordner, bruecke.STATUS_ERROR, fehler=str(fehler))
        antwort.update(tat=TAT_FEHLER, grund=(
            f"Verarbeitung gescheitert: {type(fehler).__name__}: {fehler}. Der Auftrag "
            f"ist auf '{bruecke.STATUS_ERROR}' gesetzt — ein Auftrag ohne Antwort ist "
            f"für den Wartenden dasselbe wie ein hängender Rechner."))
        return antwort
    finally:
        # Auch auf dem Fehlerweg: Ein Faden, den niemand anhält, läuft weiter und sieht
        # einem Auftrag zu, den es nicht mehr gibt.
        if beobachter is not None:
            antwort["wache"] = beobachter.stop()

    if not isinstance(ergebnis, dict):
        bruecke.setze_status(ordner, bruecke.STATUS_ERROR,
                             fehler="verarbeite lieferte kein Wörterbuch")
        antwort.update(tat=TAT_FEHLER, grund=(
            f"verarbeite lieferte {type(ergebnis).__name__} statt eines Wörterbuchs mit "
            f"'bilder'. Der Auftrag ist auf '{bruecke.STATUS_ERROR}' gesetzt."))
        return antwort

    geschrieben = bruecke.schreibe_ergebnis(
        ordner, ergebnis.get("bilder") or [],
        job_id=auftrag.get("job_id"),
        geometrie_urteil=ergebnis.get("geometrie_urteil"),
        stil_urteil=ergebnis.get("stil_urteil"),
        zeiten=_zeiten_mit_stillstand(ergebnis.get("zeiten"), antwort["wache"]),
    )
    antwort.update(tat=TAT_VERARBEITET, ergebnis=geschrieben,
                   grund=f"{len(ergebnis.get('bilder') or [])} Bild(er) geschrieben.")
    return antwort


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


def _karte_frei(laufzettel: dict, darf_rechnen) -> tuple[bool, str]:
    """Darf gerechnet werden? — die Auflage des Auftrags gegen die Auskunft der Maschine.

    ``idle_window_only`` ist die Auflage der fremden Seite und heisst dasselbe wie unser
    ``nur_bei_leerlauf``. Fehlt die Auskunft, wird **nicht** gerechnet: „ungeprüft" ist
    nicht „in Ordnung" — dieselbe Regel wie in :mod:`aiimaging.belichtung` und
    :mod:`aiimaging.fortschritt`.
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
        return True, ""
    return False, (f"Der Auftrag trägt 'idle_window_only' und die Karte ist nicht frei: "
                   f"{warum}")


def durchgang(store, *, verarbeite, fremde_freigabe_gilt: bool = False,
              darf_rechnen=None, hoechstens: int | None = None,
              waisenfrist_s: float = WAISENFRIST_S, wache_bauen=None,
              beobachtungs_takt_s: float = fortschritt.BEOBACHTUNGS_TAKT_S,
              _uhr=None) -> dict:
    """**Ein** Durchgang über den Ablageort. Kein Dauerlauf, keine Schleife, kein Schlaf.

    Warum kein Dauerlauf: Wer wie oft nachsieht, ist eine Betriebsfrage — Cron, Dienst,
    Aufruf von Hand —, und sie gehört nicht in eine Bibliothek. Eine Bibliothek mit
    eingebauter ``while True``-Schleife lässt sich nicht prüfen, nicht einbetten und nicht
    sauber beenden.

    Aufträge werden in der Reihenfolge ihres Eingangs bearbeitet (``bruecke.offene_auftraege``
    sortiert nach dem Zeitstempel im Verzeichnisnamen). Wer zuerst kam, wird zuerst
    bedient; alles andere wäre für den Wartenden nicht nachvollziehbar.

    Args:
        hoechstens: höchstens so viele Aufträge in diesem Durchgang. ``None`` heisst alle.
            Nützlich für einen Rechner, der zwischendurch etwas anderes tun soll.

    Jeder Auftrag bekommt seine **eigene** Wache: ``wache_bauen`` wird je Auftrag
    gerufen. Eine geteilte Wache trüge die Stillstandsuhr des Vorgängers in den nächsten
    Lauf und meldete dort einen Stillstand, den es nie gab.

    Returns:
        ``{gesehen, verarbeitet, fehler, liegengelassen, waisen, ergebnisse, gestanden}``.
        ``gestanden`` zählt die Läufe, bei denen die Wache einen Stillstand sah.
        ``ergebnisse`` sind die Antworten von :func:`hole_einen` in Bearbeitungsreihenfolge.
    """
    offen = bruecke.offene_auftraege(store)
    if hoechstens is not None:
        if isinstance(hoechstens, bool) or not isinstance(hoechstens, int):
            raise AbholerError(f"hoechstens muss eine ganze Zahl sein: {hoechstens!r}")
        if hoechstens < 0:
            raise AbholerError(f"hoechstens darf nicht negativ sein: {hoechstens}")
        offen = offen[:hoechstens]

    ergebnisse = [
        hole_einen(ordner, verarbeite=verarbeite,
                   fremde_freigabe_gilt=fremde_freigabe_gilt, darf_rechnen=darf_rechnen,
                   wache_bauen=wache_bauen, beobachtungs_takt_s=beobachtungs_takt_s)
        for ordner in offen
    ]
    verwaist = waisen(store, frist_s=waisenfrist_s, _uhr=_uhr)

    return {
        "gesehen": len(offen),
        "verarbeitet": sum(1 for e in ergebnisse if e["tat"] == TAT_VERARBEITET),
        "fehler": sum(1 for e in ergebnisse if e["tat"] == TAT_FEHLER),
        "liegengelassen": sum(1 for e in ergebnisse if e["tat"] == TAT_LIEGENGELASSEN),
        "gestanden": sum(1 for e in ergebnisse if (e.get("wache") or {}).get("gestanden")),
        "waisen": verwaist,
        "ergebnisse": ergebnisse,
    }


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

#: Welche Richtung gerendert wird, wenn die Szene ``cameras: "auto"`` sagt.
#:
#: **Eine**, nicht zwölf. Wie viele automatische Standpunkte ein Auftrag wert ist, ist
#: eine Betriebs- und keine Programmentscheidung — zwölf Standpunkte sind zwölf
#: GPU-Läufe. Der Aufrufer kann es überschreiben.
AUTO_RICHTUNGEN = ("sSE",)


def verarbeiter(*, out_wurzel=None, auto_richtungen=AUTO_RICHTUNGEN,
                up_axis: str = ANGENOMMENE_HOCHACHSE, schwelle: float | None = None,
                stillstand_frist_s: float | None = None, stil: str | None = None,
                nullprobe: bool = True, seeds=(0,),
                _multipass=None, _rendere=None, _qa=None, _soll=None,
                _belichtung=None, _render_modell=None, _tiefen_modell=None):
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
    rendern = _rendere or render.rendere
    messen = _qa or tiefenschaetzer.qa_gegen_soll
    soll_lesen = _soll or bildlesen.tiefen_aus_report
    belichtung_pruefen = _belichtung or _bel.pruefe_bild
    grenze = geometrie_qa.SCHWELLE_GEOMETRIE if schwelle is None else schwelle
    rahmen = _bel.rahmen_fuer(stil) if stil else None

    def verarbeite(auftrag: dict) -> dict:
        szene = auftrag["szene"]
        ordner = Path(auftrag["verzeichnis"])
        ziel = Path(out_wurzel) / ordner.name if out_wurzel else Path(auftrag["ausgabe"])
        ziel.mkdir(parents=True, exist_ok=True)

        kameras = szene.get("kameras")
        if kameras == "auto" or not isinstance(kameras, list):
            aufgaben = [{"kuerzel": r, "richtung": r} for r in auto_richtungen]
        else:
            aufgaben = [dict(k, kuerzel=k.get("kuerzel") or f"kamera{i}")
                        for i, k in enumerate(kameras)]
        if not aufgaben:
            raise AbholerError(
                "Der Auftrag nennt keine einzige Kamera, und auch keine automatische "
                "Richtung ist eingestellt. Es gibt nichts zu rendern."
            )

        bilder: list[str] = []
        urteile: list[dict] = []
        zeiten: dict[str, float] = {}
        beginn_gesamt = time.monotonic()

        for aufgabe in aufgaben:
            kuerzel = aufgabe["kuerzel"]
            aus = ziel / str(kuerzel)
            aus.mkdir(parents=True, exist_ok=True)
            beginn = time.monotonic()

            bericht = multipass(
                str(auftrag["modell"]), aus, up_axis=up_axis,
                aufloesung=szene.get("aufloesung", 512), hoehe=szene.get("hoehe"),
                samples=szene.get("samples", 128),
                kamera=aufgabe.get("richtung"),
                auge=aufgabe.get("auge"), blick_auf=aufgabe.get("blick_auf"),
                brennweite=aufgabe.get("brennweite_mm"),
                stillstand_frist_s=stillstand_frist_s,
            )
            tiefe = bericht.get("depth_png")
            if not tiefe:
                raise AbholerError(
                    f"Kamera {kuerzel!r}: keine Tiefenkarte. Ohne sie gibt es keine "
                    f"Konditionierung, und ein Render ohne sie wäre genau die erfundene "
                    f"Kubatur, gegen die dieses Projekt antritt. Grund: "
                    f"{bericht.get('depth_png_fehler')}"
                )

            # Die Soll-Karte kommt aus der EXR, nicht aus dem PNG: nur sie trägt die
            # Silhouette exakt. Das PNG war die Eingabe des Modells, die EXR ist der
            # Massstab.
            soll, breite, hoch = soll_lesen(bericht)
            maskenbefund = _maske_bauen(bericht)

            def _rendere_seed(seed, ziel_png):
                erg = rendern(
                    render.RenderAuftrag(
                        depth_png=tiefe,
                        prompt=szene.get("prompt", ""),
                        controlnet_staerke=szene.get("controlnet_staerke", 0.8),
                        backbone=szene.get("backbone") or render.VORGABE_BACKBONE,
                        beauty_png=bericht.get("beauty_png"),
                        seed=seed,
                        ausgabe_png=ziel_png,
                    ),
                    modell=_render_modell,
                )
                if erg.get("status") != "ok":
                    raise AbholerError(
                        f"Kamera {kuerzel!r}, seed {seed}: Render {erg.get('status')} — "
                        f"{erg.get('error') or erg.get('maengel')}"
                    )
                return erg

            ergebnis, urteil, auswahl = _bester_seed(
                seeds, aus, kuerzel, _rendere_seed,
                lambda png: messen(png, soll, breite=breite, hoehe=hoch,
                                   modell=_tiefen_modell, schwelle=grenze,
                                   maske=maskenbefund.get("maske")),
                maske_da=maskenbefund.get("maske") is not None)
            bilder.append(ergebnis["bild_png"])
            anker = None
            maskenanker = None
            if nullprobe:
                anker, maskenanker = _nullprobe(
                    aus, soll, breite, hoch, bildschreiben=bildschreiben,
                    messen=messen, grenze=grenze, tiefen_modell=_tiefen_modell,
                    maske=maskenbefund.get("maske"))
            urteil = dict(urteil, kamera=kuerzel, nullanker=anker,
                          seedauswahl=auswahl,
                          maskenbefund=maskenbefund, maskenanker=maskenanker,
                          einordnung=geometrie_qa.einordnung(
                              urteil.get("score"), anker, schwelle=grenze),
                          belichtung=_belichtung_urteil(
                              ergebnis["bild_png"], stil, rahmen, belichtung_pruefen))
            urteile.append(urteil)
            zeiten[str(kuerzel)] = round(time.monotonic() - beginn, 1)

        zeiten["gesamt"] = round(time.monotonic() - beginn_gesamt, 1)
        return {
            "bilder": bilder,
            "geometrie_urteil": _schlechtestes(urteile),
            "stil_urteil": _stil_urteil_aus_belichtung(urteile, stil),
            "kameras": urteile,
            "zeiten": zeiten,
        }

    return verarbeite


def _nullprobe(ordner, soll, breite, hoehe, *, bildschreiben, messen, grenze,
               tiefen_modell=None, maske=None) -> tuple[dict | None, dict | None]:
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
                            modell=tiefen_modell, schwelle=grenze, maske=maske)
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


def _bester_seed(seeds, aus, kuerzel, rendere_seed, messe, *, maske_da: bool):
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

    if len(seeds) == 1 or not maske_da:
        erg = rendere_seed(seeds[0], ziel_png)
        urteil = messe(erg["bild_png"])
        grund = ("Nur ein Seed angefordert." if len(seeds) == 1 else
                 f"{len(seeds)} Seeds angefordert, aber es gibt KEINE Bauwerksmaske — "
                 f"und ohne sie kein Mass, nach dem sich auswaehlen liesse. Der Score "
                 f"ueber das ganze Bild taugt dafuer nicht (auf-20260821-26: ein Bild "
                 f"ohne Bauwerk erreichte dort 0.9848 gegen 0.9703 fuer das perfekte). "
                 f"Gerendert wurde seed {seeds[0]}; die uebrigen sind UNGEMESSEN.")
        return erg, urteil, {"gewaehlt": seeds[0], "kandidaten": [seeds[0]],
                             "ausgewaehlt": False, "grund": grund}

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
                           "bild": erg["bild_png"], "_erg": erg, "_urteil": urteil})

    messbar = [k for k in kandidaten if k["gerichtet"] is not None]
    if not messbar:
        # Alle ungemessen: dann ist der erste so gut wie jeder andere, und das gehoert
        # gesagt statt kaschiert.
        sieger = kandidaten[0]
        grund = ("Keiner der Seeds lieferte ein Maskenurteil — ausgewaehlt wurde nicht, "
                 "sondern der erste genommen. UNGEMESSEN, nicht bestanden.")
        ausgewaehlt = False
    else:
        sieger = max(messbar, key=lambda k: k["gerichtet"])
        werte = [k["gerichtet"] for k in messbar]
        grund = (f"Bester von {len(messbar)} gemessenen Seeds nach 'gerichtet' "
                 f"(Polaritaet x rho ueber der Maske, +1 perfekt). "
                 f"Spanne {min(werte):+.4f} bis {max(werte):+.4f}.")
        ausgewaehlt = True

    shutil.copyfile(sieger["bild"], ziel_png)
    erg = dict(sieger["_erg"], bild_png=ziel_png)
    auswahl = {"gewaehlt": sieger["seed"], "ausgewaehlt": ausgewaehlt, "grund": grund,
               "kandidaten": [{"seed": k["seed"], "gerichtet": k["gerichtet"],
                               "paarurteil": k.get("paarurteil")} for k in kandidaten]}
    _auswahl_ablegen(aus, kuerzel, auswahl)
    return erg, sieger["_urteil"], auswahl


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


def _maske_bauen(bericht: dict) -> dict:
    """Die Bauwerksmaske aus dem Material-ID-Pass — oder eine benannte Lücke.

    **Warum ein Fehlschlag hier den Lauf nicht aufhält.** Die Maske ist die *zusätzliche*
    Messung, nicht die einzige; der Score über das ganze Bild entsteht ohnehin. Ein
    Auftrag, der an einer fehlenden Materialtabelle scheiterte, wäre ein Auftrag ohne
    Bild — und das ist teurer als eine ungemessene Zusatzfrage.

    **Warum er trotzdem nicht verschwindet.** Ohne diesen Befund sähe ein Lauf ohne Maske
    hinterher aus wie einer mit Maske und ohne Auffälligkeit. Genau diese Verwechslung
    ist der Grund, warum das ganze Modul die Dreiteilung durchhält.

    Returns:
        ``{maske, gemessen, grund, ...}``. ``maske`` ist ``None``, wenn sie sich nicht
        bauen liess — dann bleibt der Maskenweg in der QA ungemessen.
    """
    png = bericht.get("material_id_png")
    if not png:
        return {"maske": None, "gemessen": False, "grund": (
            "Kein Material-ID-Pass im Bericht. Ohne ihn gibt es keine Bauwerksmaske — und "
            "damit keine Antwort auf die Frage, ob im Bild überhaupt ein Bauwerk steht. "
            "Der Lauf geht weiter; die Frage bleibt UNGEMESSEN.")}
    try:
        gebaut = maske_modul.bauwerksmaske_aus_lauf(png, bericht)
    except Exception as fehler:        # noqa: BLE001 — siehe Docstring
        return {"maske": None, "gemessen": False, "grund": (
            f"Bauwerksmaske nicht baubar: {type(fehler).__name__}: {fehler}")}
    if gebaut.get("maske") is None:
        return dict(gebaut, gemessen=False, grund=" ".join(gebaut.get("warnungen") or [])
                    or "Die Geländeregel hat nicht gegriffen.")
    return dict(gebaut, gemessen=True, grund="")


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
