"""Unsere eigene Auftragsablage als Quelle für den Abholer.

Der Befund, der dieses Modul nötig gemacht hat
----------------------------------------------
Nachgezählt am 26.08.2026: ``werkzeuge.enqueue_render`` — der MCP-Einlass, also der Weg,
den ein Knoten in KosmoOrbit nimmt — legte den Auftrag unter ``job_verzeichnis()`` ab.
``grep`` über ``src`` und ``tools`` ergab **genau einen** Leser dieses Verzeichnisses:
``query_render``, die Statusabfrage. Der Abholer las die **Brücke**, ``tools/homeworker.py``
das Repo.

    Ein Knoten in KosmoOrbit konnte einen Render bestellen, und niemand führte ihn aus.

Mit Freigabe-Token ging der Auftrag sogar auf ``queued`` — er sah also aus, als sei er
unterwegs. Das ist dieselbe Sorte Befund wie die toten Kanten dieser Woche, nur an der
Naht, die uns überhaupt erst zu einem Teil von KosmoOrbit macht.

Warum eine zweite Quelle und kein zweiter Ausführer
---------------------------------------------------
Der Abholer trägt die Riegel vor dem Render, die Kameraschleife, die Startwertauswahl und
die Doppel-QA. Ihn zur zweiten Quelle zu öffnen kostet dieses Modul; die MCP-Naht zum
zweiten Ausführer auszubauen hiesse, dieselbe Fachlogik ein zweites Mal zu bauen — mit
zwei Sätzen von Zusagen, die auseinanderlaufen, sobald einer der beiden gepflegt wird.
**Regel 4 sagt dasselbe: Die MCP-Schicht ist Übersetzung, keine Logik.**

Die Form der Ablage
-------------------
Ein Auftrag ist ein **Verzeichnis** ``<store>/<job_id>/`` mit ``<job_id>.json`` darin —
dieselbe Form wie bei der Brücke, damit Befund, Vertragsergebnis und Ausgabeordner
danebenliegen können. Vorher lagen die Auftragsdateien flach nebeneinander; ein Befund
hätte dann keinen Ort gehabt.

Was dieses Modul mit ``bruecke`` gemeinsam hat, ist kein Zufall: Beide bedienen dieselben
sechs Namen, die der Abholer braucht (``QUELLEN_FEHLER``, ``STATUS_RUNNING``,
``STATUS_ERROR``, ``offene_auftraege``, ``laufzettel_pfad``, ``lies_auftrag``,
``setze_status``, ``schreibe_ergebnis``). Das ist der ganze Vertrag einer Quelle.
"""
from __future__ import annotations

from pathlib import Path

from aiimaging import jobs, kosmo_naht, kosmo_szene

#: Die Statuswerte, die der Abholer setzt. Sie kommen aus ``jobs`` und heissen dort
#: gleich wie im fremden Vertrag — eine der wenigen Stellen, an denen sich die beiden
#: Vokabulare von selbst decken.
STATUS_QUEUED = jobs.STATUS_QUEUED
STATUS_RUNNING = jobs.STATUS_RUNNING
STATUS_ERROR = jobs.STATUS_ERROR
STATUS_DONE = jobs.STATUS_DONE

#: Der Fehler, den der Abholer beim Lesen abfängt. Die Brücke nennt ihn
#: ``BrueckenError``; welcher es ist, entscheidet die Quelle, nicht der Abholer.
QUELLEN_FEHLER = jobs.JobError

#: Wie das Vertragsergebnis heisst — derselbe Name wie bei der Brücke, weil ihn ihre
#: Oberfläche liest und ein zweiter Name nur ein zweiter Ort zum Nachsehen wäre.
DATEI_ERGEBNIS = "render-result.json"


def laufzettel_pfad(verzeichnis) -> Path:
    """Die Datei, an deren Änderungszeit ein Waisenlauf erkannt wird.

    Bei der Brücke ist es ``job.json``, hier die Auftragsdatei selbst. Der Abholer fragt
    danach, statt einen festen Dateinamen anzunehmen — sonst hätte die zweite Quelle den
    Waisenfund still ausgeschaltet, und das wäre genau die Art Lücke, gegen die dieses
    Modul gebaut ist.
    """
    ordner = Path(verzeichnis)
    return ordner / f"{ordner.name}{jobs.DATEI_ENDUNG}"


def offene_auftraege(store, *, nur_status=(STATUS_QUEUED,)) -> list[Path]:
    """Alle Auftragsverzeichnisse, die auf Arbeit warten — ältestes zuerst.

    Sortiert nach Verzeichnisnamen; die Kennung trägt den Zeitstempel, also ist das die
    Reihenfolge des Eingangs.

    Verzeichnisse ohne oder mit unlesbarer Auftragsdatei werden **übersprungen, nicht
    gemeldet** — dieselbe Entscheidung wie bei der Brücke: Sie sind der Normalfall,
    während gerade geschrieben wird.
    """
    ordner = Path(store)
    if not ordner.is_dir():
        return []
    treffer = []
    for d in sorted(ordner.iterdir()):
        if not d.is_dir():
            continue
        try:
            satz = jobs.lies_job(d.name, d)
        except (jobs.JobError, FileNotFoundError, OSError):
            continue
        if nur_status is None or satz.get("status") in nur_status:
            treffer.append(d)
    return treffer


def lies_auftrag(verzeichnis, *, fremde_freigabe_gilt: bool = False) -> dict:
    """Einen eigenen Auftrag in die Form lesen, die der Abholer erwartet.

    Args:
        fremde_freigabe_gilt: **Hat hier keine Bedeutung** und wird nur angenommen, damit
            beide Quellen denselben Aufruf vertragen. Der Schalter betrifft den Token der
            fremden Brücke; unsere Ablage prägt keinen — sie führt gar keinen (siehe
            ``jobs._wehre_token_in_params_ab``), und die Freigabe steckt bereits im
            Status. Wer ihn hier setzt, bekommt das als Warnung gesagt statt einer
            stillen Nichtwirkung.

    Returns:
        Dieselben Felder wie :func:`aiimaging.bruecke.lies_auftrag`, plus ``hochachse``
        und ``ausserhalb``: Angaben, die unser MCP-Eingang kennt und für die
        ``kosmovis.render-scene/v1`` **kein Feld hat** (siehe
        :data:`aiimaging.kosmo_naht.NICHT_IM_VERTRAG`). Sie stehen daneben statt in einem
        Feld, das drüben niemand liest.

    Raises:
        QUELLEN_FEHLER: Verzeichnis oder Auftragsdatei fehlen oder sind unlesbar.
    """
    ordner = Path(verzeichnis)
    if not ordner.is_dir():
        raise QUELLEN_FEHLER(f"Kein Auftragsverzeichnis: {ordner}")

    satz = jobs.lies_job(ordner.name, ordner)

    warnungen: list[str] = []
    maengel: list[str] = []

    if fremde_freigabe_gilt:
        warnungen.append(
            "`fremde_freigabe_gilt` wurde gesetzt, betrifft aber allein den Token der "
            "fremden Brücke. Dieser Auftrag stammt aus unserer eigenen Ablage; seine "
            "Freigabe steht im Status. Der Schalter bewirkt hier nichts."
        )

    try:
        uebersetzt = kosmo_naht.als_render_scene(satz)
    except kosmo_naht.NahtError as fehler:
        raise QUELLEN_FEHLER(f"Auftrag nicht als Szene lesbar: {fehler}") from fehler
    warnungen.extend(uebersetzt["hinweise"])

    szene = kosmo_szene.lies_szene(uebersetzt["szene"])
    warnungen.extend(szene["warnungen"])
    maengel.extend(szene["maengel"])

    modell = Path(szene["geometrie"]) if szene.get("geometrie") else None
    if modell is None or not modell.is_file():
        maengel.append(
            f"Die Geometrie fehlt: {modell} ist keine lesbare Datei. Der Auftrag nennt "
            f"einen Pfad, der zur Zeit des Laufs nicht mehr da ist — bei einem Auftrag "
            f"aus dem Cockpit ist das der Regelfall nach einem Neustart, nicht die "
            f"Ausnahme."
        )
        modell = None

    freigegeben = satz.get("status") == STATUS_QUEUED
    if freigegeben:
        grund = (f"Der Auftrag steht auf {STATUS_QUEUED!r} — dorthin führt allein "
                 f"`jobs.freigeben` mit gültigem Token.")
    else:
        grund = (f"Der Auftrag steht auf {satz.get('status')!r} und ist nicht "
                 f"freigegeben. Nur `jobs.freigeben` mit einem {jobs.TOKEN_PRAEFIX}…-"
                 f"Token führt nach {STATUS_QUEUED!r}; ein Abholer kann sich die "
                 f"Freigabe nicht selbst erteilen.")
        maengel.append(grund)

    ausgabe = Path(szene["out"]) if szene.get("out") else ordner / "out"

    return {
        "job_id": satz.get("job_id"),
        "status": satz.get("status"),
        "verzeichnis": ordner,
        # Der Abholer liest daraus `idle_window_only` — unser Satz führt dasselbe Feld
        # unter demselben Namen, also ist der Satz selbst der Laufzettel.
        "laufzettel": satz,
        "szene": szene,
        "modell": modell,
        "ausgabe": ausgabe,
        "freigegeben": freigegeben,
        "freigabe_grund": grund,
        "hochachse": uebersetzt["ausserhalb"].get("up_axis"),
        "ausserhalb": uebersetzt["ausserhalb"],
        "warnungen": tuple(warnungen),
        "vertragsvorgaben": tuple(szene["vertragsvorgaben"]),
        "maengel": tuple(maengel),
    }


def setze_status(verzeichnis, status: str, *, fehler: str | None = None) -> dict:
    """Den Auftrag fortschreiben — über den Automaten aus :mod:`aiimaging.jobs`.

    **Nicht am Automaten vorbei.** ``jobs.setze_status`` prüft den Übergang und lässt
    ``queued`` gar nicht erst setzen; dorthin führt allein ``freigeben`` mit gültigem
    Token. Diese Quelle greift also nicht selbst in die Datei, sondern benutzt dieselbe
    Tür wie jeder andere — sonst wäre der Abholer der eine Aufrufer, für den das Gate
    nicht gilt.
    """
    ordner = Path(verzeichnis)
    return jobs.setze_status(ordner.name, status, ordner, fehler=fehler)


def vermerke_grund(verzeichnis, grund: str) -> dict:
    """Warum dieser Auftrag liegen bleibt — an den Auftragssatz, ohne Statuswechsel.

    Dieselbe Naht wie :func:`aiimaging.bruecke.vermerke_grund`, damit ein liegen
    gebliebener Auftrag auf **beiden** Wegen dieselbe Auskunft trägt. Ein Auftrag aus
    dem Cockpit und einer aus der Oberfläche sollen sich darin nicht unterscheiden —
    sonst hinge die Antwort daran, welchen Weg die Bestellung genommen hat.

    Geht über :func:`aiimaging.jobs.vermerke_meldung` und damit **nicht** am Automaten
    vorbei: Der Status wird nicht angefasst, nur der Klartext.
    """
    ordner = Path(verzeichnis)
    return jobs.vermerke_meldung(ordner.name, ordner, grund)


def schreibe_ergebnis(verzeichnis, bilder, *, job_id: str | None = None,
                      geometrie_urteil=None, stil_urteil=None, zeiten=None,
                      nicht_gerendert=(),
                      status: str = STATUS_DONE, uebersprungen: bool = False) -> dict:
    """Das Vertragsergebnis danebenlegen und den Auftrag fortschreiben — in dieser Reihenfolge.

    Die Reihenfolge ist dieselbe Sorgfalt wie bei der Brücke: Wer den Status zuerst setzt,
    erzeugt ein Zeitfenster, in dem ein Leser ein Ergebnis sucht, das noch nicht da ist.

    Geschrieben wird **derselbe** Vertrag (``kosmovis.render-result/v2``) unter demselben
    Dateinamen wie bei der Brücke. Ein Auftrag aus dem Cockpit und einer aus der
    Oberfläche sollen sich im Ergebnis nicht unterscheiden — sonst hinge die Form der
    Antwort daran, welchen Weg die Bestellung genommen hat.
    """
    ordner = Path(verzeichnis)
    satz = jobs.lies_job(ordner.name, ordner)
    kennung = job_id or satz.get("job_id")
    if not kennung:
        raise QUELLEN_FEHLER(
            "Kein 'job_id' — weder übergeben noch im Auftrag. Ein Ergebnis ohne Kennung "
            "lässt sich keinem Auftrag zuordnen."
        )

    namen = [Path(b).name for b in (bilder or [])]
    ergebnis = kosmo_szene.als_ergebnis(
        kennung, namen, geometrie_urteil=geometrie_urteil,
        stil_urteil=stil_urteil, zeiten=zeiten, uebersprungen=uebersprungen,
        nicht_gerendert=nicht_gerendert)

    # ZUERST das Ergebnis, DANN der Status — siehe Docstring.
    _schreibe_atomar(ordner / DATEI_ERGEBNIS, kosmo_szene.nur_vertragsfelder(ergebnis))
    # Das Ergebnis wandert zusätzlich IN den Auftragssatz: `query_render` liest ihn, und
    # ein MCP-Aufrufer soll die Bilder finden, ohne den Dateinamen der Brücke zu kennen.
    jobs.setze_status(ordner.name, status, ordner,
                      ergebnis={"images": namen,
                                "depth_exr": (satz.get("ergebnis") or {}).get("depth_exr")})
    return ergebnis


def _schreibe_atomar(ziel: Path, inhalt: dict) -> None:
    """Erst daneben schreiben, dann umbenennen — dieselbe Vorsicht wie in ``jobs``."""
    import json

    ziel.parent.mkdir(parents=True, exist_ok=True)
    neben = ziel.with_suffix(ziel.suffix + ".neu")
    neben.write_text(json.dumps(inhalt, ensure_ascii=False, indent=2) + "\n",
                     encoding="utf-8")
    neben.replace(ziel)


__all__ = [
    "DATEI_ERGEBNIS", "QUELLEN_FEHLER",
    "STATUS_DONE", "STATUS_ERROR", "STATUS_QUEUED", "STATUS_RUNNING",
    "laufzettel_pfad", "lies_auftrag", "offene_auftraege", "schreibe_ergebnis",
    "setze_status",
]
