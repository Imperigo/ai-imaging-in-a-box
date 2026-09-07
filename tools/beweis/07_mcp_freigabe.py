#!/usr/bin/env python3
"""BEWEIS 07 — Der Freeze-Schutz der MCP-Naht (``aiimaging.werkzeuge.enqueue_render``/
``query_render``, ``aiimaging.jobs``) hält, an ECHTEN Aufrufen geprüft: Ein Auftrag ohne
Freigabe-Token bleibt auf ``awaiting_approval`` und rührt nichts an, was eine GPU
belegen würde; erst ein gültiges Token bringt ihn auf ``queued``; und der zweite, davon
unabhängige Riegel — ``jobs.setze_status`` — verweigert ``queued`` als Zielstatus
GRUNDSÄTZLICH, also auch am direkten Modulaufruf vorbei am MCP-Werkzeug, und zwar
unabhängig davon, ob der Auftrag gerade auf ``awaiting_approval`` oder schon auf
``queued`` steht.

Was bewiesen wird
------------------
1. ``mcp_server.rufe_werkzeug("aiimaging_enqueue_render", …)`` OHNE ``approval_token``
   ergibt ``status == "awaiting_approval"``. Derselbe Auftrag, zweimal über
   ``aiimaging_query_render`` gelesen, bestätigt das — und beide Male ist
   ``images == []``: Es ist nichts entstanden, was einen Render voraussetzt.
2. Derselbe Aufruf MIT einem gültigen ``CONFIRMED_RENDER_…``-Token ergibt
   ``status == "queued"`` — echt, nicht behauptet: ``jobs.baue_job`` entscheidet allein
   über ``jobs.ist_gueltiges_token``.
3. ``jobs.setze_status(job_id, "queued", …)`` — der Weg AM Werkzeug vorbei, direkt in
   der Ablage — wird für BEIDE Aufträge mit ``jobs.UebergangError`` abgewiesen: für den
   noch wartenden ebenso wie für den bereits freigegebenen. Das ist die zweite Hälfte
   des Gates, und sie prüft nicht den Ausgangszustand — der Code weist ``"queued"`` als
   Ziel ab, bevor er den Auftrag überhaupt liest (``jobs.py``, ``setze_status``, erste
   Zeilen). Nach dem verweigerten Versuch wird JEDER Auftrag ein drittes Mal über
   ``query_render`` gelesen: der Status ist unverändert derselbe wie vor dem Versuch.

Woran man es im Bild sieht
---------------------------
Zwei Zeilen, oben "ohne Token" (bernsteinfarben = ``awaiting_approval``), unten "mit
Token" (grün = ``queued``). Jede Zeile: drei Felder, durch Pfeile verbunden —
``enqueue`` → ``query`` (1. Lesung) → ``query`` (2. Lesung, NACH dem verweigerten
``setze_status``-Versuch). Auf dem zweiten Pfeil sitzt ein rotes Feld mit weissem
Kreuz: der abgewiesene Versuch, direkt auf ``queued`` zu setzen. Unter dem zweiten und
dritten Feld je ein kleines Quadrat — gefüllt hiesse ``images`` sei nicht leer (wäre
ein Fehlalarm: GPU liefe an); hohl heisst, es ist leer, wie erwartet. Beide Zeilen
enden mit demselben Farbton, mit dem sie begonnen haben: Der verweigerte Versuch hat
sichtbar NICHTS verändert. Ganz unten, durch eine Fuge getrennt, zwei weitere
Quadrate: die echte Dateizahl in ``out_dir`` je Auftrag (0 und 0) — der Beleg, dass
kein Renderprozess je geschrieben hat.

Kein Feld in diesem Bild ist geschätzt. Jede Farbe, jedes Quadrat und jeder
Dateiname im Ergebnis stammt aus einem echten Rückgabewert desselben Laufs, der auch
die Konsolenausgabe erzeugt (siehe unten).

Läuft vollständig hier — kein Blender, keine GPU
--------------------------------------------------
Die Geometrie kommt aus ``tools/make_test_glb.py`` (reine stdlib, kein IFC, kein
Blender) und wird direkt als ``glb_path`` eingespeist — der IFC→glb-Zweig von
``enqueue_render`` (der einen Subprozess im ``.venv-ifc`` startet) wird darum in
diesem Beweis gar nicht erst betreten; das ist Gegenstand von Beweis 01. Ausgeführt
wird ausschliesslich: Vertragsprüfung (``contracts``), Torwächter (``torwaechter``),
Auftragsablage (``jobs``) — alles reine Python. Der Auftragsspeicher liegt in einem
frischen Wegwerf-Verzeichnis unter ``tempfile.gettempdir()`` (überschrieben über
``AIIMAGING_JOB_DIR``, siehe ``werkzeuge.job_verzeichnis``), damit dieser Lauf keine
Spuren neben echten Aufträgen hinterlässt und keine von einem vorherigen Lauf liest.

Aufruf:
    python3 tools/beweis/07_mcp_freigabe.py [ziel_verzeichnis]

Ohne Argument schreibt es nach ``build/beweis/07_mcp_freigabe/``.
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

WURZEL = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(WURZEL / "src"))
sys.path.insert(0, str(WURZEL / "tools"))

from aiimaging import bildschreiben, glbbox, jobs, mcp_server, werkzeuge  # noqa: E402
from aiimaging.mcp_schemas import WERKZEUG_ENQUEUE, WERKZEUG_QUERY  # noqa: E402

import make_test_glb  # noqa: E402

ZIEL_VORGABE = WURZEL / "build" / "beweis" / "07_mcp_freigabe"

FARBE_HINTERGRUND = (238, 238, 235)
FARBE_AWAITING = (205, 150, 60)      # bernstein — awaiting_approval
FARBE_QUEUED = (70, 150, 70)         # grün — queued
FARBE_BLOCKIERT = (190, 60, 50)      # rot — abgewiesener Versuch
FARBE_PFEIL = (150, 150, 150)
FARBE_RAHMEN = (30, 30, 30)
FARBE_FUGE = (20, 20, 20)
FARBE_MARKER_HOHL = (170, 170, 170)


# ----------------------------------------------------------------------------------
# Minimaler Rasterizer — dasselbe Muster wie in den Nachbar-Beweisen (01/05/06): es
# gibt im Projekt keinen, weil bildschreiben.py bewusst ohne Bibliothek auskommt.
# ----------------------------------------------------------------------------------

def _neues_bild(breite: int, hoehe: int, hg=FARBE_HINTERGRUND) -> list:
    return [hg] * (breite * hoehe)


def _rechteck(px: list, breite: int, hoehe: int, x0, y0, x1, y1, farbe) -> None:
    xa, xb = sorted((max(0, int(round(x0))), min(breite, int(round(x1)))))
    ya, yb = sorted((max(0, int(round(y0))), min(hoehe, int(round(y1)))))
    for y in range(ya, yb):
        px[y * breite + xa:y * breite + xb] = [farbe] * (xb - xa)


def _rahmen(px: list, breite: int, hoehe: int, x0, y0, x1, y1, farbe, dicke: int = 4) -> None:
    _rechteck(px, breite, hoehe, x0, y0, x1, y0 + dicke, farbe)
    _rechteck(px, breite, hoehe, x0, y1 - dicke, x1, y1, farbe)
    _rechteck(px, breite, hoehe, x0, y0, x0 + dicke, y1, farbe)
    _rechteck(px, breite, hoehe, x1 - dicke, y0, x1, y1, farbe)


def _diagonale(px: list, breite: int, hoehe: int, x0, y0, x1, y1, farbe, dicke=6) -> None:
    """Dicke Diagonale durch lineare Interpolation — ``bildschreiben`` kennt nur
    achsparallele Rechtecke, ein Kreuz braucht schräge Striche. Nur hier gebraucht."""
    schritte = int(max(abs(x1 - x0), abs(y1 - y0), 1))
    for i in range(schritte + 1):
        t = i / schritte
        x = x0 + (x1 - x0) * t
        y = y0 + (y1 - y0) * t
        _rechteck(px, breite, hoehe, x - dicke / 2, y - dicke / 2, x + dicke / 2, y + dicke / 2, farbe)


def _pfeil(px: list, breite: int, hoehe: int, x0, y1_mitte, x1, farbe, dicke=12) -> None:
    """Waagrechter Pfeil von ``x0`` nach ``x1`` auf Höhe ``y1_mitte``, Spitze als
    gefülltes Dreieck — dasselbe Muster wie ``05_der_graph._pfeilspitze``."""
    _rechteck(px, breite, hoehe, x0, y1_mitte - dicke / 2, x1 - 14, y1_mitte + dicke / 2, farbe)
    spitze = x1
    groesse = 16
    for d in range(groesse + 1):
        halb = d * 0.6
        _rechteck(px, breite, hoehe, spitze - d, y1_mitte - halb, spitze - d + 2,
                  y1_mitte + halb + 1, farbe)


def _quadrat(px: list, breite: int, hoehe: int, cx, cy, seite, farbe, *, hohl=False) -> None:
    x0, x1 = cx - seite / 2, cx + seite / 2
    y0, y1 = cy - seite / 2, cy + seite / 2
    if hohl:
        _rahmen(px, breite, hoehe, x0, y0, x1, y1, farbe, dicke=4)
    else:
        _rechteck(px, breite, hoehe, x0, y0, x1, y1, farbe)


def _blockade(px: list, breite: int, hoehe: int, cx, cy, seite=56) -> None:
    """Rotes Feld mit weissem Kreuz — der abgewiesene ``setze_status``-Versuch."""
    _rechteck(px, breite, hoehe, cx - seite / 2, cy - seite / 2, cx + seite / 2, cy + seite / 2,
              FARBE_BLOCKIERT)
    rand = seite * 0.22
    _diagonale(px, breite, hoehe, cx - seite / 2 + rand, cy - seite / 2 + rand,
              cx + seite / 2 - rand, cy + seite / 2 - rand, (250, 250, 250), dicke=7)
    _diagonale(px, breite, hoehe, cx + seite / 2 - rand, cy - seite / 2 + rand,
              cx - seite / 2 + rand, cy + seite / 2 - rand, (250, 250, 250), dicke=7)


# ----------------------------------------------------------------------------------
# Echte Aufrufe — dieselbe Naht, über die auch KosmoOrbit spräche
# (mcp_server.rufe_werkzeug), plus der direkte Modulaufruf für den zweiten Riegel.
# ----------------------------------------------------------------------------------

def enqueue(glb_pfad: Path, bbox, out_dir: Path, *, token: str | None) -> dict:
    argumente = {
        "glb_path": str(glb_pfad),
        "up_axis": "Y",
        "bbox": bbox,
        "out_dir": str(out_dir),
    }
    if token is not None:
        argumente["approval_token"] = token
    return mcp_server.rufe_werkzeug(WERKZEUG_ENQUEUE, argumente)


def query(job_id: str) -> dict:
    return mcp_server.rufe_werkzeug(WERKZEUG_QUERY, {"job_id": job_id})


def versuche_direkte_freigabe(job_id: str) -> tuple[bool, str]:
    """``jobs.setze_status(job_id, "queued", …)`` direkt aufrufen — am Werkzeug vorbei.

    Returns:
        ``(abgewiesen, meldung)`` — ``abgewiesen`` ist ``True``, wenn
        ``jobs.UebergangError`` geflogen ist (der erwartete, gewollte Fall).
    """
    verzeichnis = werkzeuge.auftrags_ordner(job_id)
    try:
        jobs.setze_status(job_id, jobs.STATUS_QUEUED, verzeichnis)
        return False, "KEIN Fehler — queued wurde gesetzt (Gate gebrochen!)"
    except jobs.UebergangError as e:
        return True, str(e)


def zaehle_dateien(out_dir: Path) -> int:
    """Echte Dateizahl in ``out_dir`` — der Beleg, dass kein Renderprozess geschrieben
    hat. Ein nicht existierendes Verzeichnis zählt als 0, nicht als Fehler: Für den
    glb-Zweig von ``enqueue_render`` wird ``out_dir`` gar nicht erst angelegt."""
    if not out_dir.is_dir():
        return 0
    return sum(1 for p in out_dir.rglob("*") if p.is_file())


# ----------------------------------------------------------------------------------
# Zeichnen
# ----------------------------------------------------------------------------------

BREITE = 1440
RAND = 60
BOX_W = 380
BOX_H = 170
LUECKE = 90
REIHENBLOCK_H = 170 + 10 + 46
ABSTAND_REIHEN = 50
FUGENDICKE = 10
UNTEN_H = 170


def _x_boxen():
    x0a = RAND
    x1a = x0a + BOX_W
    x0b = x1a + LUECKE
    x1b = x0b + BOX_W
    x0c = x1b + LUECKE
    x1c = x0c + BOX_W
    return (x0a, x1a), (x0b, x1b), (x0c, x1c)


def main() -> int:
    ziel = Path(sys.argv[1]) if len(sys.argv) > 1 else ZIEL_VORGABE
    ziel.mkdir(parents=True, exist_ok=True)
    geschrieben: list[Path] = []

    # ---- Wegwerf-Arbeitsverzeichnis: eigener Auftragsspeicher, eigene Geometrie ----
    arbeit = Path(tempfile.mkdtemp(prefix="aiimaging-beweis07-"))
    os.environ[werkzeuge.UMGEBUNG_JOBS] = str(arbeit / "jobs")
    print(f"Auftragsspeicher (Wegwerf, dieser Lauf): {arbeit / 'jobs'}")

    glb_pfad = arbeit / "modell.glb"
    make_test_glb.main([str(glb_pfad)])
    box = glbbox.bauwerksbox(glb_pfad, up_axis="Y")
    bbox = box["bbox_bauwerk"] or box["bbox_szene"]
    print(f"Echte Geometrie: {glb_pfad.name}, bbox_bauwerk={box['bbox_bauwerk']} "
          f"(Regel 'ist_gelaende' trennt {box['n_gelaende']} Gelände- von "
          f"{box['n_bauwerk']} Bauwerksknoten)")

    out_dir_a = arbeit / "out_a"
    out_dir_b = arbeit / "out_b"

    # ---- (1) OHNE Token ------------------------------------------------------
    antwort_a = enqueue(glb_pfad, bbox, out_dir_a, token=None)
    if antwort_a.get("error"):
        raise SystemExit(f"enqueue_render (ohne Token) schlug fehl: {antwort_a['error']}")
    job_a = antwort_a["job_id"]
    print(f"(1) enqueue_render ohne Token -> job {job_a}, status={antwort_a['status']!r}")
    assert antwort_a["status"] == jobs.STATUS_AWAITING, antwort_a["status"]

    abfrage_a1 = query(job_a)
    print(f"    query_render #1 -> status={abfrage_a1['status']!r}, "
          f"images={abfrage_a1['images']!r}")

    # ---- (2) MIT gültigem Token -----------------------------------------------
    antwort_b = enqueue(glb_pfad, bbox, out_dir_b, token="CONFIRMED_RENDER_beweis07")
    if antwort_b.get("error"):
        raise SystemExit(f"enqueue_render (mit Token) schlug fehl: {antwort_b['error']}")
    job_b = antwort_b["job_id"]
    print(f"(2) enqueue_render mit gueltigem Token -> job {job_b}, "
          f"status={antwort_b['status']!r}")
    assert antwort_b["status"] == jobs.STATUS_QUEUED, antwort_b["status"]

    abfrage_b1 = query(job_b)
    print(f"    query_render #1 -> status={abfrage_b1['status']!r}, "
          f"images={abfrage_b1['images']!r}")

    # ---- (3) setze_status("queued") DIREKT — am Werkzeug vorbei, für BEIDE -----
    abgewiesen_a, meldung_a = versuche_direkte_freigabe(job_a)
    abgewiesen_b, meldung_b = versuche_direkte_freigabe(job_b)
    print(f"(3) jobs.setze_status(job_a={job_a}, 'queued') "
          f"-> {'abgewiesen' if abgewiesen_a else 'DURCHGEKOMMEN'}: {meldung_a}")
    print(f"    jobs.setze_status(job_b={job_b}, 'queued') "
          f"-> {'abgewiesen' if abgewiesen_b else 'DURCHGEKOMMEN'}: {meldung_b}")
    assert abgewiesen_a and abgewiesen_b, "Gate gebrochen — setze_status hat queued gesetzt"

    abfrage_a2 = query(job_a)
    abfrage_b2 = query(job_b)
    print(f"    query_render #2 (nach dem Versuch) job_a -> status={abfrage_a2['status']!r}")
    print(f"    query_render #2 (nach dem Versuch) job_b -> status={abfrage_b2['status']!r}")
    assert abfrage_a2["status"] == abfrage_a1["status"] == jobs.STATUS_AWAITING
    assert abfrage_b2["status"] == abfrage_b1["status"] == jobs.STATUS_QUEUED

    dateien_a = zaehle_dateien(out_dir_a)
    dateien_b = zaehle_dateien(out_dir_b)
    print(f"Echte Dateizahl out_dir_a={dateien_a}, out_dir_b={dateien_b} "
          f"(0 heisst: kein Renderprozess ist je gelaufen)")

    # ---- Bild -------------------------------------------------------------------
    hoehe = RAND + REIHENBLOCK_H + ABSTAND_REIHEN + REIHENBLOCK_H + ABSTAND_REIHEN \
        + FUGENDICKE + ABSTAND_REIHEN + UNTEN_H + RAND
    px = _neues_bild(BREITE, hoehe)

    (xa0, xa1), (xb0, xb1), (xc0, xc1) = _x_boxen()

    def zeile(y0, farbe, bilder_query1, bilder_query2) -> None:
        ym = y0 + BOX_H / 2
        for x0, x1 in ((xa0, xa1), (xb0, xb1), (xc0, xc1)):
            _rechteck(px, BREITE, hoehe, x0, y0, x1, y0 + BOX_H, farbe)
            _rahmen(px, BREITE, hoehe, x0, y0, x1, y0 + BOX_H, FARBE_RAHMEN, dicke=3)
        _pfeil(px, BREITE, hoehe, xa1, ym, xb0, FARBE_PFEIL)
        _pfeil(px, BREITE, hoehe, xb1, ym, xc0, FARBE_PFEIL)
        _blockade(px, BREITE, hoehe, (xb1 + xc0) / 2, ym)

        marker_y = y0 + BOX_H + 30
        for (x0, x1), bilder in (((xb0, xb1), bilder_query1), ((xc0, xc1), bilder_query2)):
            cx = (x0 + x1) / 2
            if bilder:
                _quadrat(px, BREITE, hoehe, cx, marker_y, 30, FARBE_BLOCKIERT)
            else:
                _quadrat(px, BREITE, hoehe, cx, marker_y, 30, FARBE_MARKER_HOHL, hohl=True)

    y_reihe1 = RAND
    zeile(y_reihe1, FARBE_AWAITING, abfrage_a1["images"], abfrage_a2["images"])

    y_reihe2 = y_reihe1 + REIHENBLOCK_H + ABSTAND_REIHEN
    zeile(y_reihe2, FARBE_QUEUED, abfrage_b1["images"], abfrage_b2["images"])

    y_fuge = y_reihe2 + REIHENBLOCK_H + ABSTAND_REIHEN
    _rechteck(px, BREITE, hoehe, 0, y_fuge, BREITE, y_fuge + FUGENDICKE, FARBE_FUGE)

    # ---- unten: echte Dateizahl in out_dir_a / out_dir_b -----------------------
    y_unten = y_fuge + FUGENDICKE + ABSTAND_REIHEN
    cx_a = (xa0 + xb1) / 2
    cx_b = (xb0 + xc1) / 2
    for cx, n in ((cx_a, dateien_a), (cx_b, dateien_b)):
        if n:
            _quadrat(px, BREITE, hoehe, cx, y_unten + UNTEN_H / 2, 90, FARBE_BLOCKIERT)
        else:
            _quadrat(px, BREITE, hoehe, cx, y_unten + UNTEN_H / 2, 90, FARBE_MARKER_HOHL, hohl=True)

    name = (
        f"07_mcp_freigabe_ohne-token-{antwort_a['status']}"
        f"_mit-token-{antwort_b['status']}"
        f"_setze-status-queued-verweigert-{int(abgewiesen_a) + int(abgewiesen_b)}x"
        f"_gpu-dateien-{dateien_a + dateien_b}.png"
    )
    pfad = ziel / name
    bildschreiben.schreibe_farb_png(pfad, px, BREITE, hoehe)
    geschrieben.append(pfad)

    for p in geschrieben:
        print(p)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
