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
# Nur fuer die Modus-Konstante. Der Name `kameras` ist in `verarbeite` lokal
# belegt (die Kameraliste der Szene) — darum wird das Modul ausschliesslich in
# der Vorgabe von `verarbeiter` benutzt, wo noch Modulgeltung herrscht.
from . import kameras as _kameras_modul
from . import komposition as _komposition
from . import kosmo_szene as _kosmo_szene
from . import prompts, render
from . import sonne as _sonne
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
               "warnungen": (), "vertragsvorgaben": ()}

    try:
        auftrag = bruecke.lies_auftrag(ordner, fremde_freigabe_gilt=fremde_freigabe_gilt)
    except bruecke.BrueckenError as fehler:
        antwort["grund"] = f"Auftrag nicht lesbar: {fehler}"
        return antwort

    antwort["job_id"] = auftrag.get("job_id") or ordner.name
    antwort["warnungen"] = tuple(auftrag.get("warnungen") or ())
    antwort["vertragsvorgaben"] = tuple(auftrag.get("vertragsvorgaben") or ())

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
    # NACH dem Vertragsergebnis und nach setze_status: Der Befund ist unsere eigene
    # Buchführung, nicht Teil der Abmachung — er darf die Reihenfolge nicht stören, an
    # der die fremde Oberfläche hängt.
    _befund_ablegen(ordner, auftrag, ergebnis, antwort)
    return antwort


#: Dateiname des vollständigen Befunds, neben dem Vertragsergebnis.
DATEI_BEFUND = "befund.json"


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
            ((ergebnis.get("stil_urteil") or {}).get("stil")), szene.get("backbone")),
        "warnungen_auftrag": list(antwort.get("warnungen") or ()),
        "vertragsvorgaben": list(antwort.get("vertragsvorgaben") or ()),
        "wache": antwort.get("wache"),
    }
    try:
        (Path(ordner) / DATEI_BEFUND).write_text(
            _json.dumps(_ohne_pfade(inhalt), ensure_ascii=False, indent=1),
            encoding="utf-8")
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

    **Der Anlass ist eine Messung am eigenen Ausgabetext.** Ohne Geländestand meldet die
    Kompositionsprüfung für *jede* Kamera zwei Warnungen: den unzuverlässigen
    Bezugspunkt und die Neigung. Bei zwölf Kameras sind das zwölf von zwölf, immer
    dieselben zwei. Eine Warnung, die bei jedem Lauf und für jede Kamera erscheint, ist
    kein Signal mehr — es ist dasselbe Versagen wie ein Wächter, der nie greift, nur von
    der anderen Seite.

    Beide sind dabei **richtig**. Der Bezugspunkt ist aus einer glb gar nicht besser zu
    wissen (dort gibt es kein Gelände), und die Neigung bleibt, bis die Vorgabe auf
    `MODUS_SHIFT` wechselt. Sie sind also keine Befunde über *diesen* Auftrag, sondern
    Eigenschaften der Eingabe — und gehören einmal genannt, nicht dreimal.

    Was nur einen Teil der Kameras betrifft, bleibt einzeln aufgeführt: **das** ist die
    Zeile, die jemanden hinsehen lässt.
    """
    beurteilt = [k for k in kameras if (k.get("komposition") or {}).get("beurteilt")]
    zeilen: list = []

    unbeurteilt = [k.get("kamera") for k in kameras
                   if (k.get("komposition") or {}).get("beurteilt") is False]
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

    bauteile = befund.get("prompt_bauteile") or ()
    if bauteile:
        zeilen.append(f"Prompt nennt Bauteile: {', '.join(str(b) for b in bauteile)} — "
                      f"hat die Geometrie sie? Wenn nicht, erfindet sie das Bildmodell.")

    urteil = befund.get("geometrie_urteil") or {}
    spanne = urteil.get("kameraspanne") or {}
    if spanne.get("n_gemessen"):
        teil = (f"Geometrie: {spanne.get('schlechtester'):.4f} "
                f"(schlechteste von {spanne['n_gemessen']} Kameras")
        if spanne.get("bester") is not None and spanne["n_gemessen"] > 1:
            teil += f", beste {spanne['bester']:.4f}"
        zeilen.append(teil + ")")
    elif spanne:
        zeilen.append("Geometrie: UNGEMESSEN — keine Kamera lieferte einen Wert.")

    kameras = befund.get("kameras") or []
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

    doppelt = [(k.get("kamera"), k.get("doppelt_von")) for k in kameras
               if k.get("doppelt_von")]
    if doppelt:
        zeilen.append(
            "Nicht neu gerendert (identische Soll-Karte): "
            + ", ".join(f"{a} ist mit {b} identisch" for a, b in doppelt)
            + " — zweizaehlige Drehsymmetrie laesst die beiden Ueber-Eck-Ansichten "
              "zusammenfallen. Das Bild wurde uebernommen, und die Ansicht zaehlt in "
              "der Kameraspanne NICHT als zweite Ziehung")

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
                      f"(auf-vis-20260825-15, Posten 4)")

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


def verarbeiter(*, out_wurzel=None, auto_richtungen=AUTO_RICHTUNGEN,
                up_axis: str = ANGENOMMENE_HOCHACHSE, schwelle: float | None = None,
                stillstand_frist_s: float | None = None, stil: str | None = None,
                nullprobe: bool = True, seeds=VORGABE_SEEDS,
                kamera_modus: str = _kameras_modul.MODUS_SHIFT,
                brennweite_mm: float | None = None,
                gelaende_z: float | None = None,
                gelaende_erwartet: bool = True,
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

        # ABBESTELLT. Bis zum 26.08.2026 las die Kette `skip: true` und rechnete
        # trotzdem — der Abholer meldete es sogar selbst («BESTELLT UND NICHT
        # AUSGEFUEHRT»), und im Lauf vom 25.08. wurde es belegt (auf-vis-20260825-15,
        # Posten 2). Wer etwas abbestellt, bekam es geliefert und zahlte die GPU-Zeit.
        #
        # ENTSCHIEDEN (Claude, 26.08.2026, Owner-Freigabe «entscheiden und um 20:00
        # vorlegen»): ueberspringen heisst KEIN Bild, aber SEHR WOHL eine Antwort. Gar
        # nichts zurueckzugeben liesse die bestellende Seite haengen — sie kann nicht
        # unterscheiden, ob wir uebersprungen haben oder abgestuerzt sind. Ein Ergebnis
        # mit leerer Bildliste und einem Grund kann sie lesen.
        if szene.get("ueberspringen"):
            return {
                "bilder": [],
                "geometrie_urteil": None,
                "stil_urteil": None,
                "kameras": [],
                "zeiten": {"gesamt": 0.0},
                "uebersprungen": True,
                "grund": ("Der Auftrag traegt `skip: true` und wurde NICHT gerendert. "
                          "Das ist keine Stoerung und kein Urteil ueber die Geometrie — "
                          "es wurde nichts gemessen, weil nichts bestellt war."),
            }

        kameras = szene.get("kameras")
        if kameras == "auto" or not isinstance(kameras, list):
            aufgaben = [{"kuerzel": r, "richtung": r, "brennweite_mm": brennweite_mm}
                        for r in auto_richtungen]
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
        # Welche Soll-Karte schon gerendert wurde, und von welcher Kamera. Siehe
        # `_sollkennung`: Bei einem Quader fallen `sSE` und `nNW` zusammen.
        gesehen: dict[str, dict] = {}
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
                kamera_modus=kamera_modus,
                gelaende_z=gelaende_z,
                # Der Sonnenstand der Bestellung. Bis zum 26.08.2026 lief er ins Leere:
                # Ein Auftrag mit Abendstand wurde gerendert, als waere er nicht
                # gestellt worden — mit einem sauberen, gut belichteten, falschen Bild.
                sonne=szene.get("sonne"),
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

            rahmung = _rahmung_vor_dem_render(bericht)
            komposition = _komposition_vor_dem_render(bericht)
            for lage in (rahmung, komposition):
                if lage.get("abbruch"):
                    break
            else:
                lage = None
            if lage is not None:
                urteile.append(dict(_uebersprungenes_urteil(kuerzel, lage),
                                    rahmung=rahmung, komposition=komposition))
                zeiten[str(kuerzel)] = round(time.monotonic() - beginn, 1)
                continue

            # Die Soll-Karte kommt aus der EXR, nicht aus dem PNG: nur sie trägt die
            # Silhouette exakt. Das PNG war die Eingabe des Modells, die EXR ist der
            # Massstab.
            soll, breite, hoch = soll_lesen(bericht)
            maskenbefund = _maske_bauen(bericht, gelaende_erwartet=gelaende_erwartet)

            # DIE DOPPELTE ANSICHT. Zweizaehlige Drehsymmetrie laesst die beiden
            # Ueber-Eck-Ansichten der HABS/NPS-Regel zusammenfallen; bei einem Quader
            # sind `sSE` und `nNW` byte-identisch. 24,5 s Diffusion fuer ein Bild, das
            # schon dalag (auf-vis-20260824-12) — und gerade bei den einfachen
            # Demofaellen.
            kennung = _sollkennung(soll, breite, hoch)
            zwilling = gesehen.get(kennung) if kennung else None
            if zwilling is not None:
                urteile.append(dict(zwilling["urteil"], kamera=kuerzel,
                                    doppelt_von=zwilling["kamera"]))
                zeiten[str(kuerzel)] = round(time.monotonic() - beginn, 1)
                continue

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
                          # Welches Bild zu diesem Urteil gehoert. Steht bis zum
                          # 26.08.2026 nur in `bilder`, und dort ohne Zuordnung — bei
                          # einer uebernommenen Ansicht waere sonst nicht mehr
                          # feststellbar, welches Bild gemeint ist.
                          bild_png=ergebnis["bild_png"],
                          # Auch wenn nicht abgebrochen wurde: Die gerechnete Lage
                          # gehoert an das Urteil. Ein Lauf knapp ueber der Schwelle
                          # sieht sonst aus wie einer mit Luft.
                          rahmung=rahmung,
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
                          # Die Kompositionsprüfung — bis zum 23.08.2026 rief SIE
                          # niemand, obwohl `komposition.py` 1400 Zeilen gerechnetes
                          # Fachwissen trägt. Ein Regelwerk, das nur seine eigenen Tests
                          # beurteilt, beurteilt nichts. Hier bekommt es die Kamera zu
                          # sehen, mit der wirklich gerendert wurde.
                          komposition=komposition,
                          maskenbefund=maskenbefund, maskenanker=maskenanker,
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
            urteil["doppelt_von"] = None
            urteile.append(urteil)
            if kennung:
                gesehen[kennung] = {"kamera": kuerzel, "urteil": urteil}
            zeiten[str(kuerzel)] = round(time.monotonic() - beginn, 1)

        zeiten["gesamt"] = round(time.monotonic() - beginn_gesamt, 1)
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
        }

    return verarbeite


#: Bilder aus dem Multipass, die VOR dem Renderlauf ganz da sein muessen.
#:
#: ``depth_png`` ist die Konditionierung — ohne sie gibt es keinen Lauf. ``beauty_png``
#: geht im Bildbearbeitungsmodus als ``image`` mit hinein. ``material_id_png`` traegt die
#: Maske. Alle drei werden von einem Subprozess geschrieben, und alle drei werden erst
#: Sekunden spaeter gelesen.
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


def _sollkennung(soll, breite, hoehe) -> str | None:
    """Eine Kennzahl der **Soll-Tiefenkarte** — zwei gleiche Karten, zwei gleiche Kennungen.

    **Der Anlass ist ein Renderlauf für nichts** (HomeStation, `auf-vis-20260824-12`): Bei
    einem Quader sind die Ansichten ``sSE`` und ``nNW`` **byte-identisch**. Ein Quader hat
    zweizählige Drehsymmetrie, und die beiden Über-Eck-Ansichten der HABS/NPS-Regel fallen
    dann zusammen. 24,5 s Diffusion für ein Bild, das schon dalag — gerade bei den
    einfachen Demofällen.

    **Warum an der Soll-Karte und nicht an der Hüllbox.** Die Hüllbox hat *immer*
    zweizählige Symmetrie; aus ihr allein liesse sich das nicht entscheiden, ohne bei
    jedem realen Bauwerk falschen Alarm zu schlagen — ein Haus mit Eingang auf einer Seite
    steckt in derselben Box wie eines ohne. Die Soll-Karte entscheidet es zuverlässig,
    und sie liegt **vor** dem teuren Bildrender vor.

    Gerundet wird auf sechs Nachkommastellen: Zwei Läufe derselben Geometrie sollen
    dieselbe Kennung ergeben, auch wenn das letzte Bit einer Fliesskommazahl abweicht.
    Zwei *verschiedene* Ansichten unterscheiden sich um Grössenordnungen mehr.

    Returns:
        Ein Hexstring, oder ``None``, wenn die Karte nicht lesbar ist. ``None`` heisst
        **nicht vergleichbar** und führt nie zu einer Doppelung — im Zweifel wird
        gerendert, denn ein fehlendes Bild ist teurer als ein doppeltes.
    """
    import hashlib

    if soll is None or not breite or not hoehe:
        return None
    h = hashlib.sha256()
    h.update(f"{int(breite)}x{int(hoehe)}|".encode())
    try:
        for zeile in soll:
            for wert in zeile:
                h.update(f"{float(wert):.6f};".encode())
    except (TypeError, ValueError):
        return None
    return h.hexdigest()


def _rahmung_vor_dem_render(bericht: dict) -> dict:
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
    lage = kameras.rahmungsverhaeltnis(bericht.get("bbox"),
                                       bericht.get("bbox_bauwerk"))
    lage = dict(lage, weg=weg, note=bericht.get("bbox_bauwerk_note") or "",
                deckungsgrad=kameras.DECKUNGSGRAD)
    if weg != "abgeleitet":
        lage["abbruch"] = None
        lage["abbruch_grund"] = (
            f"Die Kamera kam auf dem Weg {weg!r} zustande, nicht aus der Huellbox. Der "
            f"Deckungsgrad beschreibt diesen Lauf darum NICHT, und es wird nichts "
            f"abgebrochen. Die gerechnete Bildbreite steht trotzdem da — als Auskunft, "
            f"nicht als Urteil.")
    return lage


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


def _kamera_ueber_dach(kamera: dict) -> dict:
    """Steht die Kamera **höher als das Bauwerk**? — die eine ohne Bild prüfbare Bedingung.

    Sie ist rein arithmetisch (Augenhöhe minus Geländestand gegen Bauwerkshöhe) und
    braucht nichts als den Kamerablock des Multipass-Berichts. Genau darum steht sie
    hier: Das Regelwerk in :mod:`aiimaging.komposition` wirft an dieser Stelle, und die
    Ausnahme fiel bis zum 26.08.2026 **nach** der Diffusion an.

    Returns:
        ``{abbruch, grund}``. ``abbruch`` ist ``False``, wenn sich die Frage nicht stellen
        lässt — eine fehlende Zahl ist **kein** Abbruchgrund, sondern eine fehlende Zahl.
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
        ``abbruch`` und ``abbruch_grund``.

    .. important::
       **Abgebrochen wird nur bei einer benannten Bedingung** (:func:`_kamera_ueber_dach`),
       nicht bei jeder Ausnahme des Regelwerks. Der Unterschied ist gemessen worden, und
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

    kamera = bericht.get("kamera")
    ueber_dach = _kamera_ueber_dach(kamera)
    try:
        urteil = _k.beurteile_bericht(kamera)
    except Exception as fehler:                # noqa: BLE001 — siehe Docstring
        urteil = {"beurteilt": False,
                  "grund": (f"Das Regelwerk konnte nicht urteilen: "
                            f"{type(fehler).__name__}: {fehler}. NICHT GEMESSEN — das "
                            f"ist etwas anderes als 'die Aufnahme taugt nicht'.")}

    if not ueber_dach["abbruch"]:
        return dict(urteil, abbruch=False, abbruch_grund="")
    return dict(urteil, abbruch=True, grund=ueber_dach["grund"], abbruch_grund=(
        f"NICHT RENDERN: {ueber_dach['grund']} Diese Pruefung braucht KEIN Bild; sie "
        f"stand bis zum 26.08.2026 hinter der Diffusion und hat dort eine fertige "
        f"Bilddatei kommentiert, statt sie zu verhindern (auf-vis-20260826-16)."))


def _uebersprungenes_urteil(kuerzel, rahmung: dict) -> dict:
    """Das Urteil einer Kamera, die **gar nicht erst gerendert** wurde.

    Es trägt ``score: None`` und ``gemessen: False``, und das ist die ganze Absicht:
    :func:`_schlechtestes` wertet ein Urteil ohne Wert als das schlechteste überhaupt,
    :func:`_kameraspanne` zählt es **nicht** als gemessen. Ein übersprungener Lauf
    verbessert also nichts und verschwindet nirgends — er ist *nicht gemessen*, und das
    ist weder bestanden noch durchgefallen.
    """
    return {"kamera": kuerzel, "score": None, "bestanden": None, "gemessen": False,
            "zustaendig": False, "bild_png": None, "rahmung": rahmung,
            "grund": rahmung.get("abbruch_grund") or rahmung.get("grund", "")}


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
                             "ausgewaehlt": False, "vorsprung": None, "grund": grund}

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
    erg = dict(sieger["_erg"], bild_png=ziel_png)
    auswahl = {"gewaehlt": sieger["seed"], "ausgewaehlt": ausgewaehlt, "grund": grund,
               "vorsprung": vorsprung,
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


def _maske_bauen(bericht: dict, *, gelaende_erwartet: bool = True) -> dict:
    """Die Bauwerksmaske aus dem Material-ID-Pass — oder eine benannte Lücke.

    **Warum ein Fehlschlag hier den Lauf nicht aufhält.** Die Maske ist die *zusätzliche*
    Messung, nicht die einzige; der Score über das ganze Bild entsteht ohnehin. Ein
    Auftrag, der an einer fehlenden Materialtabelle scheiterte, wäre ein Auftrag ohne
    Bild — und das ist teurer als eine ungemessene Zusatzfrage.

    **Warum er trotzdem nicht verschwindet.** Ohne diesen Befund sähe ein Lauf ohne Maske
    hinterher aus wie einer mit Maske und ohne Auffälligkeit. Genau diese Verwechslung
    ist der Grund, warum das ganze Modul die Dreiteilung durchhält.

    **Und warum ``gelaende_erwartet`` hier durchgereicht wird.** Ein reines Gebäude-IFC
    bringt **gar kein Gelände** mit — der eine ``IfcSite`` darin trägt keine Geometrie und
    taucht in der Ausgabe nicht auf (HomeStation, `BEFUND_2026-08-24_IFC-LESER.md`, an
    neun echten Dateien gemessen). Die Maske meldet dann «kein Gelände erkannt», und das
    ist ein **Fehlalarm und kein Befund**: Es fehlt nichts, es war nie welches da.

    Bis zum 24.08.2026 kam der Schalter hier nicht an — er stand in :mod:`aiimaging.maske`
    und war von aussen nicht erreichbar. Dieselbe Naht-Sache wie bei Brennweite und
    Geländestand: einstellbar im Modul, nicht im Betrieb.

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
        gebaut = maske_modul.bauwerksmaske_aus_lauf(
            png, bericht, gelaende_erwartet=gelaende_erwartet)
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
        ``{n, n_gemessen, n_doppelt, bester, schlechtester, spanne, streuung,
        abschlag_streuungen, hinweis}``. ``streuung`` ist ``None`` bei weniger als drei
        gemessenen Kameras — aus zweien lässt sie sich ausrechnen und sagt nichts.

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
        hinweis = (f"Keine der {n} Kameras ist gemessen. Das gemeldete Urteil ist "
                   f"UNGEPRUEFT, nicht durchgefallen.")
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

    return {
        "n": n,
        "n_gemessen": len(messbar),
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
