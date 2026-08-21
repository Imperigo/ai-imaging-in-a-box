"""Die Werkzeuge hinter der MCP-Naht — hier liegt die Logik, nicht im Server.

Warum getrennt vom Server
-------------------------
Regel 4: Jede Fähigkeit muss aus Python heraus nutzbar sein, ohne dass eine Oberfläche
läuft. Diese Funktionen sind darum gewöhnliche Bibliotheksaufrufe mit gewöhnlichen
Rückgabewerten — `mcp_server.py` reicht sie nur durch. Wer das MCP-SDK nicht installiert,
verliert die Anbindung an KosmoOrbit und sonst nichts.

Die Dreiteilung
---------------
KosmoOrbits Ausführungspfad ist read-only und fail-closed; ein GPU-Render ist das nicht.
Deshalb:

* `enqueue_render` bereitet vor und **legt ab** — konvertiert, prüft, schreibt einen
  Auftrag. Rührt die GPU nicht an.
* `query_render` liest.
* Die Ausführung geschieht ausserhalb der Pipeline, durch einen Scheduler, nur bei
  gültiger Freigabe.

Ohne Freigabe-Token bleibt jeder Auftrag auf `awaiting_approval`. Das ist der
Freeze-Schutz: Ein Sprachmodell soll Aufträge einstellen können, ohne Hardware blockieren
zu können.
"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

from aiimaging import contracts, jobs, seams, torwaechter
from aiimaging.mcp_schemas import (
    LANE,
    WERKZEUGE,
    WERKZEUG_ENQUEUE,
    WERKZEUG_FAEHIGKEITEN,
    WERKZEUG_PRUEFE,
    WERKZEUG_QUERY,
)

#: Wo Aufträge liegen. Überschreibbar, damit Tests nicht ins Benutzerverzeichnis schreiben.
UMGEBUNG_JOBS = "AIIMAGING_JOB_DIR"


def job_verzeichnis() -> Path:
    """Auftragsverzeichnis; unter `/tmp`, solange nichts anderes gesetzt ist.

    Die Pfad-Sandbox des Ökosystems verlangt `$HOME` oder `/tmp` — `/tmp` ist die
    zurückhaltendere Wahl, weil dort nichts Dauerhaftes des Benutzers liegt.
    """
    return Path(os.environ.get(UMGEBUNG_JOBS, Path(tempfile.gettempdir()) / "aiimaging-jobs"))


def _geometrie_aus_argumenten(args: dict) -> dict:
    """Die Geometriefelder aus einem MCP-Aufruf herausziehen.

    `mergeInputs` reicht sämtliche Vorgängerfelder durch — der Aufruf enthält also weit
    mehr, als uns angeht. Wir nehmen nur, was wir kennen, und lassen den Rest liegen.
    """
    geom = {}
    for feld in ("ifc_path", "glb_path", "up_axis", "bbox"):
        if args.get(feld) is not None:
            geom[feld] = args[feld]
    return geom


def check_geometry(args: dict) -> dict:
    """Massstab und Georeferenz prüfen, ohne einen Auftrag anzulegen.

    Rein rechnend — kein Subprozess, keine GPU. Gedacht, um vor den Render gehängt zu
    werden: Ein um Faktor 1000 fehlskaliertes Modell soll auffallen, bevor GPU-Zeit
    verbraucht wird.
    """
    geom = _geometrie_aus_argumenten(args)
    if not geom:
        return {"entscheidung": torwaechter.ENTSCHEIDUNG_ABLEHNEN_KONVERSION,
                "begruendung": "Weder ifc_path noch glb_path noch bbox übergeben.",
                "bbox": None, "up_axis": None,
                "empfiehlt_neuzentrierung": False, "error": None}

    urteil = torwaechter.torwaechter({"status": "ok", "bbox": geom.get("bbox")})
    return {
        "entscheidung": urteil["entscheidung"],
        "begruendung": urteil["begruendung"],
        "bbox": geom.get("bbox"),
        "up_axis": geom.get("up_axis"),
        "empfiehlt_neuzentrierung": urteil.get("empfiehlt_neuzentrierung", False),
        "error": None,
    }


def enqueue_render(args: dict) -> dict:
    """Geometrie → gegateter Render-Auftrag. Rührt die GPU nicht an.

    Ablauf: Vertrag prüfen → bei IFC-Eingang konvertieren (Subprozess im `.venv-ifc`) →
    Torwächter → Auftrag ablegen. Bricht eine Stufe, entsteht **kein** Auftrag: Ein
    Auftrag auf kaputter Geometrie würde später GPU-Zeit verbrennen, um dann doch zu
    scheitern.
    """
    geom = _geometrie_aus_argumenten(args)
    out_dir = args.get("out_dir") or str(Path(tempfile.gettempdir()) / "aiimaging-out")

    # 1) Vertrag. Hier fällt insbesondere ein fehlendes `up_axis` bei glb-Eingang auf —
    #    der Phase-0-Befund, und zwar bevor irgendetwas Teures passiert.
    try:
        szene = contracts.validate_render_scene({"geometry": geom, "out_dir": out_dir})
    except contracts.ContractError as e:
        return _fehler(f"Vertrag verletzt: {e}")

    g = szene["geometry"]
    bbox = g.get("bbox")

    # 2) Bei IFC-Eingang selbst konvertieren (Regel 4: der Kern liest eigenständig).
    if g.get("ifc_path"):
        glb_ziel = str(Path(out_dir) / "modell.glb")
        try:
            Path(out_dir).mkdir(parents=True, exist_ok=True)
            bericht = seams.ifc_zu_glb(g["ifc_path"], glb_ziel)
        except (seams.SeamError, contracts.ContractError) as e:
            return _fehler(f"IFC→glb fehlgeschlagen: {e}")
        if bericht.get("status") != "ok":
            return _fehler(f"IFC→glb meldete {bericht.get('status')!r}: {bericht.get('error')}")
        g["glb_path"] = bericht.get("glb_path")
        g["up_axis"] = bericht.get("up_axis", "Y")
        bbox = bericht.get("bbox", bbox)

    # 3) Torwächter — Massstab lehnt ab, Georeferenz empfiehlt nur.
    urteil = torwaechter.torwaechter({"status": "ok", "bbox": bbox})
    if urteil["entscheidung"] != torwaechter.ENTSCHEIDUNG_ANNEHMEN:
        return _fehler(f"Torwächter: {urteil['begruendung']}", torwaechter_urteil=urteil)

    # 4) Auftrag ablegen. Der Status folgt ALLEIN dem Token — dieses Werkzeug kann
    #    `queued` nicht selbst setzen, und das ist der Freeze-Schutz.
    satz = jobs.baue_job(
        job_id=jobs.neue_job_id(),
        art="render",
        params={
            "glb_path": g.get("glb_path"),
            "up_axis": g.get("up_axis"),
            "out_dir": out_dir,
            "bbox": bbox,
            "aufloesung": args.get("aufloesung", 512),
            "samples": args.get("samples", 16),
            "empfiehlt_neuzentrierung": urteil.get("empfiehlt_neuzentrierung", False),
        },
        approval_token=args.get("approval_token"),
    )
    jobs.schreibe_job(satz, job_verzeichnis())

    return {
        "job_id": satz["job_id"],
        "status": satz["status"],
        "geometry_ref": g.get("glb_path"),
        "glb_path": g.get("glb_path"),
        "up_axis": g.get("up_axis"),
        "bbox": bbox,
        "out_dir": out_dir,
        "torwaechter": urteil,
        "error": None,
    }


def query_render(args: dict) -> dict:
    """Status und Ergebnis eines Auftrags lesen. Rein lesend."""
    job_id = (args or {}).get("job_id")
    if not job_id:
        return {"job_id": None, "status": None, "geometry_ref": None, "depth_exr": None,
                "images": [], "erstellt": None, "geaendert": None,
                "error": "Pflichtfeld 'job_id' fehlt."}
    if not isinstance(job_id, str):
        # NICHT `str(job_id)` zurückgeben. Eine 42 als "42" zu spiegeln sähe aus, als
        # sei nach einem Auftrag dieses Namens gefragt worden — die Antwort wäre im
        # Schema und trotzdem irreführend. `None` plus die genannte Ursache ist
        # eindeutig. (Aufgefallen an der Schemaprüfung, die dieser Fall verletzte:
        # `job_id: 42 passt nicht zu type='string'`.)
        return {"job_id": None, "status": None, "geometry_ref": None, "depth_exr": None,
                "images": [], "erstellt": None, "geaendert": None,
                "error": f"'job_id' muss eine Zeichenkette sein, war "
                         f"{type(job_id).__name__}: {job_id!r}."}
    try:
        satz = jobs.lies_job(job_id, job_verzeichnis())
    except (jobs.JobError, FileNotFoundError) as e:
        return {"job_id": job_id, "status": None, "geometry_ref": None, "depth_exr": None,
                "images": [], "erstellt": None, "geaendert": None, "error": str(e)}

    params = satz.get("params") or {}
    ergebnis = satz.get("ergebnis") or {}
    return {
        "job_id": satz["job_id"],
        "status": satz["status"],
        "geometry_ref": params.get("glb_path"),
        "depth_exr": ergebnis.get("depth_exr"),
        "images": ergebnis.get("images") or [],
        "erstellt": satz.get("erstellt"),
        "geaendert": satz.get("geaendert"),
        "error": satz.get("fehler"),
    }


def _fehler(text: str, *, torwaechter_urteil: dict | None = None) -> dict:
    """Fehlerantwort im Schema von `enqueue_render`.

    Auch im Fehlerfall wird die volle Feldliste geliefert: KosmoOrbit prüft die Ausgabe
    gegen das `outputSchema`, und eine verkürzte Antwort schlüge dort auf — der Benutzer
    sähe dann einen Schemafehler statt der eigentlichen Ursache.
    """
    return {
        "job_id": None, "status": None, "geometry_ref": None, "glb_path": None,
        "up_axis": None, "bbox": None, "out_dir": None,
        "torwaechter": torwaechter_urteil or {}, "error": text,
    }


def capabilities(argumente: dict) -> dict:
    """Was diese Lane kann — und wo ihr Urteil (noch) nicht trägt.

    **Warum die Vorbehalte mit ausgeliefert werden.** Ein Auskunftswerkzeug, das nur
    Fähigkeiten aufzählt, lädt dazu ein, dem grünen Abzeichen zu glauben. Die
    Geometrie-Schwelle ist bis heute nicht kalibriert; wer diese Naht benutzt, soll das
    aus derselben Antwort erfahren und nicht erst aus einem Bericht.

    Argumentlos und ohne Nebenwirkung — siehe ``WERKZEUG_FAEHIGKEITEN``.
    """
    del argumente                     # bewusst ohne: das ist der Punkt dieses Werkzeugs
    from aiimaging import geometrie_qa as _g
    from aiimaging import kosmo_szene as _k
    return {
        "lane": LANE,
        "werkzeuge": sorted(WERKZEUGE),
        "vertraege": [_k.SCHEMA_SZENE, _k.SCHEMA_ERGEBNIS],
        "geometrie_schwelle": _g.SCHWELLE_GEOMETRIE,
        "vorbehalte": [
            "Die Geometrie-Schwelle ist NICHT kalibriert: auf einer Szene mit viel Boden "
            "besteht weisses Rauschen das Gate, auf einer mit wenig Boden faellt selbst "
            "ein perfektes Bild durch (gemessen 20.08.2026, auf-20260820-21).",
            "Die Tiefenkante misst weder Anwesenheit noch Randschaerfe, sondern ob die "
            "MEHRHEIT des Umrisses gezeichnet ist, und bricht unter dem Median zusammen "
            "statt allmaehlich zu fallen (gemessen 22.08.2026, auf-20260822-30).",
            "Die Seed-Streuung ist groesser als jeder bisher gemessene Parametereffekt. "
            "Vergleiche zwischen zwei Varianten tragen nur GEPAART ueber denselben Seed.",
        ],
    }


#: Namensaufloesung fuer den Server. Getrennt gehalten, damit `mcp_server.py` keine
#: Fallunterscheidung braucht und wirklich nur uebersetzt.
RUFTABELLE = {
    WERKZEUG_FAEHIGKEITEN: capabilities,
    WERKZEUG_ENQUEUE: enqueue_render,
    WERKZEUG_QUERY: query_render,
    WERKZEUG_PRUEFE: check_geometry,
}
