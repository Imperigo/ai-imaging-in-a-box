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

from . import bruecke

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
               darf_rechnen=None) -> dict:
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

    Returns:
        ``{tat, job_id, verzeichnis, grund, ergebnis}``. ``tat`` ist eine der
        ``TAT_*``-Konstanten.
    """
    if not callable(verarbeite):
        raise AbholerError(
            "verarbeite muss aufrufbar sein. Der Abholer rendert nicht selbst — was mit "
            "einem Auftrag geschieht, wird hereingereicht, damit die Reihenfolge dieses "
            "Moduls ohne GPU prüfbar bleibt."
        )
    ordner = Path(verzeichnis)
    antwort = {"tat": TAT_LIEGENGELASSEN, "job_id": ordner.name,
               "verzeichnis": ordner, "grund": "", "ergebnis": None}

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
    try:
        ergebnis = verarbeite(auftrag)
    except Exception as fehler:            # noqa: BLE001 — jeder Fehler ist ein Ergebnis
        bruecke.setze_status(ordner, bruecke.STATUS_ERROR, fehler=str(fehler))
        antwort.update(tat=TAT_FEHLER, grund=(
            f"Verarbeitung gescheitert: {type(fehler).__name__}: {fehler}. Der Auftrag "
            f"ist auf '{bruecke.STATUS_ERROR}' gesetzt — ein Auftrag ohne Antwort ist "
            f"für den Wartenden dasselbe wie ein hängender Rechner."))
        return antwort

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
        zeiten=ergebnis.get("zeiten"),
    )
    antwort.update(tat=TAT_VERARBEITET, ergebnis=geschrieben,
                   grund=f"{len(ergebnis.get('bilder') or [])} Bild(er) geschrieben.")
    return antwort


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
              waisenfrist_s: float = WAISENFRIST_S, _uhr=None) -> dict:
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

    Returns:
        ``{gesehen, verarbeitet, fehler, liegengelassen, waisen, ergebnisse}``.
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
                   fremde_freigabe_gilt=fremde_freigabe_gilt, darf_rechnen=darf_rechnen)
        for ordner in offen
    ]
    verwaist = waisen(store, frist_s=waisenfrist_s, _uhr=_uhr)

    return {
        "gesehen": len(offen),
        "verarbeitet": sum(1 for e in ergebnisse if e["tat"] == TAT_VERARBEITET),
        "fehler": sum(1 for e in ergebnisse if e["tat"] == TAT_FEHLER),
        "liegengelassen": sum(1 for e in ergebnisse if e["tat"] == TAT_LIEGENGELASSEN),
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
                stillstand_frist_s: float | None = None,
                _multipass=None, _rendere=None, _qa=None, _soll=None,
                _render_modell=None, _tiefen_modell=None):
    """Baut das ``verarbeite``, das :func:`hole_einen` durch unsere Kette schickt.

    Je Kamera ein Durchgang: **Multipass → Render → Geometrie-QA**. Ein Auftrag mit drei
    Kameras — wie der echte vom 19.08.2026 — ergibt drei Bilder und drei Urteile.

    Warum je Kamera ein eigener Multipass: Die Tiefenkarte ist der Massstab, gegen den das
    erzeugte Bild gemessen wird, und sie gilt nur für **den einen** Blickwinkel, aus dem
    sie entstand. Ein Bild gegen die Tiefenkarte einer anderen Kamera zu messen ergäbe
    eine Zahl, und die Zahl wäre Unsinn.

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
    from . import bildlesen, geometrie_qa, render, seams, tiefenschaetzer

    multipass = _multipass or seams.glb_zu_multipass
    rendern = _rendere or render.rendere
    messen = _qa or tiefenschaetzer.qa_gegen_soll
    soll_lesen = _soll or bildlesen.tiefen_aus_report
    grenze = geometrie_qa.SCHWELLE_GEOMETRIE if schwelle is None else schwelle

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

            ergebnis = rendern(
                render.RenderAuftrag(
                    depth_png=tiefe,
                    prompt=szene.get("prompt", ""),
                    controlnet_staerke=szene.get("controlnet_staerke", 0.8),
                    backbone=szene.get("backbone") or render.VORGABE_BACKBONE,
                    beauty_png=bericht.get("beauty_png"),
                    ausgabe_png=str(aus / f"{kuerzel}.png"),
                ),
                modell=_render_modell,
            )
            if ergebnis.get("status") != "ok":
                raise AbholerError(
                    f"Kamera {kuerzel!r}: Render {ergebnis.get('status')} — "
                    f"{ergebnis.get('error') or ergebnis.get('maengel')}"
                )
            bilder.append(ergebnis["bild_png"])

            # Die Soll-Karte kommt aus der EXR, nicht aus dem PNG: nur sie trägt die
            # Silhouette exakt. Das PNG war die Eingabe des Modells, die EXR ist der
            # Massstab.
            soll, breite, hoch = soll_lesen(bericht)
            urteil = messen(ergebnis["bild_png"], soll, breite=breite, hoehe=hoch,
                            modell=_tiefen_modell, schwelle=grenze)
            urteil = dict(urteil, kamera=kuerzel)
            urteile.append(urteil)
            zeiten[str(kuerzel)] = round(time.monotonic() - beginn, 1)

        zeiten["gesamt"] = round(time.monotonic() - beginn_gesamt, 1)
        return {
            "bilder": bilder,
            "geometrie_urteil": _schlechtestes(urteile),
            "kameras": urteile,
            "zeiten": zeiten,
        }

    return verarbeite


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
