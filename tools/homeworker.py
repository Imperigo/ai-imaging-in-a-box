#!/usr/bin/env python3
"""Der Ausführende auf der HomeStation — holt Aufträge aus dem Repo, führt sie aus, legt Ergebnisse ab.

Gedacht für: Ubuntu 24.04, RTX 5090 (32 GB), Ryzen 9 9950X, Modelle unter ``/ai``.

Aufruf
------
    git pull
    python3 tools/homeworker.py --repo . --liste          # was liegt an?
    python3 tools/homeworker.py --repo . --alle           # alles Unerledigte abarbeiten
    python3 tools/homeworker.py --repo . --auftrag auf-20260818-01
    git add auftraege/ergebnisse && git commit && git push

Die Hardware-Schranke
---------------------
Die RTX 5090 löst unter ungebremster Volllast die Netzteil-Schutzschaltung aus. Dieses
Skript startet einen GPU-Auftrag darum **nur**, wenn die Karte frei ist — und im Zweifel
gar nicht (fail-closed). Lässt sich der Zustand nicht feststellen, wird abgelehnt, nicht
geraten: Ein übersprungener Auftrag kostet Wartezeit, ein abgestürzter Rechner mehr.

Die Leistungsgrenze setzt dieses Skript **nicht** selbst — dafür braucht es
Administratorrechte (``nvidia-smi -pl 400``). Es prüft aber, ob sie gesetzt ist, und
sagt, was zu tun wäre.

Regel 3
-------
Zurück ins Repo gehen **nur Zahlen**: Messwerte, Urteile, Laufzeiten, Dateinamen. Die
Bilder bleiben hier. `auftrag.baue_ergebnis` weist eingebettete Bilddaten ab.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aiimaging import auftrag as auf  # noqa: E402


# ── GPU-Zustand ──────────────────────────────────────────────────────────────────────

def gpu_zustand() -> dict:
    """Leistungsaufnahme, belegter Speicher und Leistungsgrenze der Karte.

    ``verfuegbar=False`` heisst: Zustand unbekannt. Das ist ausdrücklich **kein** grünes
    Licht — der Aufrufer behandelt es als Ablehnungsgrund.
    """
    if not shutil.which("nvidia-smi"):
        return {"verfuegbar": False, "grund": "nvidia-smi nicht gefunden"}
    try:
        roh = subprocess.run(
            ["nvidia-smi",
             "--query-gpu=name,power.draw,memory.used,memory.total,power.limit",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=30, check=False)
    except (OSError, subprocess.SubprocessError) as e:
        return {"verfuegbar": False, "grund": f"nvidia-smi nicht ausführbar: {e}"}
    if roh.returncode != 0:
        return {"verfuegbar": False, "grund": f"nvidia-smi Code {roh.returncode}"}

    # `splitlines()[0]` stand bis zum 18.08.2026 **ausserhalb** des try/except: Lieferte
    # nvidia-smi eine leere Ausgabe (Code 0, aber nichts darin — kommt bei Treiber-Neustart
    # und in Containern vor), warf es IndexError statt „Zustand unbekannt" zu melden. Ein
    # Absturz an dieser Stelle ist nicht fail-closed, sondern gar kein Verhalten.
    zeilen = roh.stdout.strip().splitlines()
    if not zeilen:
        return {"verfuegbar": False, "grund": "nvidia-smi lieferte keine Ausgabe"}
    teile = [t.strip() for t in zeilen[0].split(",")]
    try:
        return {
            "verfuegbar": True,
            "name": teile[0],
            "leistung_w": float(teile[1]),
            "speicher_belegt_gb": float(teile[2]) / 1024.0,
            "speicher_gesamt_gb": float(teile[3]) / 1024.0,
            "leistungsgrenze_w": float(teile[4]),
        }
    except (IndexError, ValueError) as e:
        return {"verfuegbar": False, "grund": f"nvidia-smi unverständlich: {e}"}


def darf_starten(zustand: dict, auflagen: dict) -> tuple[bool, str]:
    """Fail-closed: Nur bei nachweislich freier Karte und gesetzter Grenze grünes Licht.

    Drei Löcher, gefunden am 18.08.2026 von der ersten Testsammlung, die dieses Skript je
    bekommen hat — alle drei **fail-open**, also genau das Gegenteil dessen, was der
    Docstring zusagte:

    1. ``nur_bei_leerlauf: false`` schaltete nicht nur das Leerlauf-Gate ab, sondern auch
       die Prüfung der Leistungsgrenze. ``auftraege/README.md`` führt beide als
       **getrennte** Auflagen, und die Leistungsgrenze ist die, an der der Rechner hängt:
       Sie schützt vor der Netzteil-Schutzschaltung, nicht vor einem belegten Speicher.
    2. Mit ``nur_bei_leerlauf: false`` wurde auch bei völlig unbekanntem GPU-Zustand
       gestartet.
    3. Fehlte ``leistungsgrenze_w`` im Zustand, rechnete die Prüfung mit ``0`` weiter und
       gab frei. **Ein unbekannter Wert ist kein niedriger Wert** — das ist dieselbe
       Verwechslung, die dieses Projekt am Report schon zweimal bezahlt hat.

    Die Reihenfolge ist jetzt umgedreht: Erst der Zustand, dann die Leistungsgrenze
    (immer), und erst zuletzt das Leerlauf-Gate, das als einziges abschaltbar ist.
    """
    # Zuerst: Wissen wir überhaupt etwas? Ohne das ist jede weitere Prüfung eine
    # Rechnung auf fehlenden Zahlen. Gilt auch bei abgeschaltetem Leerlauf-Gate — der
    # Auftrag darf die Messung überspringen, nicht die Unkenntnis.
    if not zustand.get("verfuegbar"):
        return False, f"GPU-Zustand unbekannt ({zustand.get('grund')}) — im Zweifel nicht starten"

    # Dann die Leistungsgrenze. **Nicht abschaltbar**, denn sie ist die Auflage, an der
    # der ganze Rechner hängt.
    soll = auflagen.get("leistungsgrenze_w", auf.LEISTUNGSGRENZE_W)
    ist = zustand.get("leistungsgrenze_w")
    if ist is None:
        return False, (f"Leistungsgrenze der Karte unbekannt — nvidia-smi hat sie nicht "
                       f"gemeldet. Unbekannt ist nicht dasselbe wie niedrig. Prüfen mit:  "
                       f"nvidia-smi --query-gpu=power.limit --format=csv")
    if ist > soll + 1:
        return False, (f"Leistungsgrenze steht bei {ist:.0f} W, gefordert sind {soll} W. "
                       f"Setzen mit:  sudo nvidia-smi -pl {soll}")

    # Zuletzt das Leerlauf-Gate. Es darf ein Auftrag abschalten: Wer weiss, dass er die
    # Karte teilen will, teilt sie — das kostet Zeit, nicht Hardware.
    if not auflagen.get("nur_bei_leerlauf", True):
        return True, (f"Leerlauf-Gate im Auftrag abgeschaltet; Leistungsgrenze "
                      f"{ist:.0f} W ≤ {soll} W ist trotzdem geprüft")

    grenze_w = auflagen.get("leerlauf_schwelle_w", auf.GPU_LEERLAUF_W)
    grenze_gb = auflagen.get("leerlauf_schwelle_mem_gb", auf.GPU_LEERLAUF_MEM_GB)
    if zustand["leistung_w"] >= grenze_w:
        return False, f"GPU zieht {zustand['leistung_w']:.0f} W (≥ {grenze_w} W) — nicht frei"
    if zustand["speicher_belegt_gb"] >= grenze_gb:
        return False, (f"GPU hat {zustand['speicher_belegt_gb']:.1f} GB belegt "
                       f"(≥ {grenze_gb} GB) — fremdes Modell geladen")

    return True, "GPU frei, Leistungsgrenze in Ordnung"


# ── Ausführung ───────────────────────────────────────────────────────────────────────

def _geometrie_bereitstellen(satz: dict, repo: Path) -> str:
    """Die Geometrie besorgen — erzeugen oder auf den Pfad verweisen.

    Bei ``synthetisch`` wird sie hier erzeugt; es reist nichts über das Repo (Regel 3).
    """
    geom = satz["geometrie"]
    if geom.get("synthetisch"):
        ziel = repo / "build" / "testbau.ifc"
        subprocess.run([sys.executable, str(repo / "tools" / "make_test_ifc.py"), str(ziel)],
                       check=True, capture_output=True, text=True)
        return str(ziel)
    pfad = geom.get("pfad")
    if not Path(pfad).is_file():
        raise FileNotFoundError(f"Geometrie nicht gefunden: {pfad}")
    return pfad


#: Für wen dieses Werkzeug arbeitet. Alles andere lässt es liegen.
#:
#: **Der Befund kommt vom Gerät** (`auf-20260828-64`, 28.08.2026): *«homeworker liest das
#: worker-Feld nirgends»*. Von 23 offenen Aufträgen wären **fünf beim falschen Empfänger**
#: durchgelaufen — alle mit ``art: qa``, alle im Multipass-Zweig, alle mit
#: ``status: ok, urteil: {"multipass": "ok"}``. **Grün und leer.**
#:
#: Und das Ergebnis wäre nicht folgenlos: Ein geschriebenes Ergebnis heisst in diesem
#: Projekt *beantwortet*. Die HomeStation hätte damit vier Vertragsfragen an einen fremden
#: Worker geschlossen, ohne dass jemand sie je gelesen hätte.
#:
#: `auftrag.py` verlangt das Feld seit dem 22.08.2026 als **Pflicht** — es wurde nur nie
#: gelesen. *Eine Pflichtangabe, die niemand liest, ist eine Zeile Text.*
#:
#: **Zuerst dieser Filter, dann der Takt** (`auf-20260826-59`): Ein Takt ohne ihn schlösse
#: beim ersten Durchgang fünf fremde Aufträge. Genau in dieser Reihenfolge verlangt es
#: `auf-20260828-64`, V1.
EIGENER_WORKER = "local"

#: Aus welcher Richtung ein Auftrag ohne Angabe aufgenommen wird.
#:
#: **Bis zum 28.08.2026 gab der Homeworker GAR KEINE Kamera weiter** — er rief
#: ``glb_zu_tiefenkarte`` nur mit Auflösung und Samples. Der Runner stellte dann seine
#: **Notkamera**: Blenders eigene 50-mm-Optik an einem Ort, der mit Augenhöhe nichts zu
#: tun hat. Der Bericht sagte es auch (``weg: rueckfall``), aber niemand las es.
#:
#: Der Owner hat es am fertigen Bild gesehen: *«die kamera vom endbild ist nicht auf
#: augenhoehe mensch»*. Mit einer angeforderten Richtung rechnet ``kameras.kamerasatz``
#: den Standort — **1,70 m über dem Gelände**, waagrecht, mit Versatz statt Neigung.
#:
#: **Warum ausgerechnet eine diagonale Richtung.** Gemessen am 28.08.2026 über acht
#: Richtungen derselben Szene: Auf den vier frontalen Richtungen fallen **5 von 20** guten
#: Fällen unter ``PAAR_RHO_SCHWELLE``, auf den vier diagonalen **keiner**. Frontale
#: Ansichten sind nicht unmessbar — aber sie sind die schlechtere Vorgabe.
VORGABE_KAMERA = "sSE"

#: Kameraangaben, die ein Auftrag setzen darf. Sie werden **nur weitergereicht, wenn sie
#: dastehen** — ein ``None`` würde die gerechnete Vorgabe überschreiben.
_KAMERA_PARAMS = ("augenhoehe", "gelaende_z", "kamera_modus", "kamera_huellbox",
                  "brennweite", "deckungsgrad", "bias_grad", "shift_y")

#: Was die einzelnen Pfade an `params` tatsächlich verbrauchen. Wird ein Auftrag mit
#: Angaben gestellt, die hier nicht stehen, ist er hier nicht ausführbar — und das muss
#: er sagen, statt etwas anderes zu messen.
_GENUTZTE_PARAMS = {
    "out_dir", "aufloesung", "samples", "kamera",
    "prompt", "negativ_prompt", "backbone", "seed", "schritte",
    "controlnet_staerke", "denoise", "mit_beauty", "modell_wurzel",
    "schaetzer", "schwelle", "gelaende_erwartet",
} | set(_KAMERA_PARAMS)


def _unverstandene_params(_art: str, params: dict) -> list[str]:
    """Welche ``params`` dieser Auftrag mitbringt, die kein Pfad hier verbraucht.

    Der Anlass, 18.08.2026: `auf-20260818-10` und `-11` sind beide `art: "qa"` und
    verlangen eine Schwellenstudie bzw. eine Einbetter-Messung. Der `qa`-Pfad kann
    beides nicht — er misst den Blender-Multipass. Ohne diese Prüfung wären beide
    Aufträge mit ``status: ok, urteil: {multipass: ok}`` zurückgekommen: grün, und ohne
    eine einzige der verlangten Zahlen.

    Das ist dieselbe Bauart Fehler, vor der der Kommentar weiter unten warnt — nur eine
    Ebene höher. Dort ging es um ein fehlendes Artefakt, hier um einen fehlenden
    Auswerter. Beide Male ist die stille Variante die schlimme: Ein Auftrag, der
    abbricht, kostet einen Lauf; ein Auftrag, der grün und leer zurückkommt, kostet das
    Vertrauen in alle anderen.

    Bewusst eine **Positivliste**: Eine Sperrliste müsste jede künftige Auftragsart
    vorhersehen. Was hier nicht steht, wird nicht verbraucht — das ist am Quelltext
    ablesbar und veraltet nicht still.

    Die Liste gilt **artübergreifend**, nicht je Art. Ein ``prompt`` an einem
    ``multipass``-Auftrag ist bekanntes Vokabular, das dieser Pfad nur nicht braucht —
    harmlos, und die bestehenden Tests stellen genau solche Aufträge. Gemeint ist der
    andere Fall: ``stoerungen``, ``einbetter``, ``staerken`` stehen nirgends im
    Wortschatz dieses Skripts und sagen damit, dass ein **anderer Auswerter** verlangt
    ist. Die Grenze läuft zwischen „hier ungenutzt" und „hier unbekannt".
    """
    return sorted(set(params) - _GENUTZTE_PARAMS)


def fuehre_aus(satz: dict, repo: Path, *, _render_modell=None, _tiefen_modell=None) -> dict:
    """Einen Auftrag ausführen und ein Ergebnis bauen.

    Für ``multipass`` und ``qa`` genügt Blender; ``render`` braucht zusätzlich das
    Bildmodell und den Tiefenschätzer.

    Args:
        _render_modell, _tiefen_modell: Nähte für Tests — fertige Modelle, die
            durchgereicht statt geladen werden. Dieselbe Bauform wie ``modell`` in
            ``render.rendere`` und ``_starte`` in ``seams``. Ohne sie wäre dieses Skript
            nur auf einem Rechner mit GPU und 20 GB Gewichten prüfbar, also faktisch gar
            nicht — und ausgerechnet der Teil, der unbeaufsichtigt läuft, bliebe ungeprüft.
    """
    from aiimaging import seams

    beginn = time.monotonic()
    art = satz["art"]
    params = satz.get("params") or {}

    unverstanden = _unverstandene_params(art, params)
    if unverstanden:
        return auf.baue_ergebnis(
            auftrag_id=satz["auftrag_id"], status="fehler",
            urteil={"auftrag": "hier nicht ausfuehrbar",
                    "nicht_verstandene_params": unverstanden},
            fehler=(
                f"Dieser Auftrag verlangt {', '.join(unverstanden)} — davon weiss dieses "
                f"Skript nichts. Der Pfad fuer art={art!r} misst den Blender-Multipass "
                f"und sonst nichts. Ohne diese Pruefung kaeme der Lauf als "
                f"'status: ok, urteil: {{multipass: ok}}' zurueck und haette keine "
                f"einzige der verlangten Zahlen gemessen — gruen und leer. Wer den "
                f"Auftrag fahren will, braucht eine Auswertung, die diese Angaben "
                f"verbraucht."),
            dauer_s=round(time.monotonic() - beginn, 1), umgebung=_umgebung())

    ifc = _geometrie_bereitstellen(satz, repo)
    aus = Path(params.get("out_dir") or (repo / "build" / satz["auftrag_id"]))
    aus.mkdir(parents=True, exist_ok=True)

    glb_bericht = seams.ifc_zu_glb(ifc, str(aus / "modell.glb"))
    if glb_bericht.get("status") != "ok":
        return auf.baue_ergebnis(
            auftrag_id=satz["auftrag_id"], status="fehler",
            fehler=f"IFC→glb: {glb_bericht.get('error')}",
            dauer_s=round(time.monotonic() - beginn, 1))

    # DIE KAMERA WIRD ANGEFORDERT — bis zum 28.08.2026 stand hier keine, und der Runner
    # stellte darum seine Notkamera. Ein Demolauf zeigte dann Blenders 50-mm-Optik von
    # irgendwoher statt eines Bildes auf Augenhoehe.
    kamera_gaben = {n: params[n] for n in _KAMERA_PARAMS if params.get(n) is not None}
    blender_bericht = seams.glb_zu_tiefenkarte(
        glb_bericht["glb_path"], aus, up_axis=glb_bericht["up_axis"],
        aufloesung=params.get("aufloesung", 512), samples=params.get("samples", 32),
        kamera=params.get("kamera") or VORGABE_KAMERA, **kamera_gaben)

    if art == "render":
        return _render_und_qa(satz, blender_bericht, glb_bericht, aus, params, beginn,
                              _render_modell=_render_modell,
                              _tiefen_modell=_tiefen_modell)

    # Nur Zahlen und Dateinamen — nie Bildinhalte (Regel 3).
    messwerte = {
        "n_elements": glb_bericht.get("n_elements"),
        "n_triangles": glb_bericht.get("n_triangles"),
        "bbox_size_m": blender_bericht.get("bbox_size_m"),
        "n_meshes": blender_bericht.get("n_meshes"),
        "depth_exr_kanaele": blender_bericht.get("depth_exr_kanaele"),
        "depth_exr_format": blender_bericht.get("depth_exr_format"),
        "depth_normalisierung": blender_bericht.get("depth_normalisierung"),
        "depth_png_fehler": blender_bericht.get("depth_png_fehler"),
        "dateien": [Path(p).name for p in aus.glob("*") if p.is_file()],
    }

    # Seit dem 18.08.2026 ist eine gescheiterte Normalisierung für `seams` **nicht mehr
    # tödlich** — die EXR ist das massgebliche Artefakt, das PNG nur ihre Ableitung.
    # Für einen Auftrag gilt das nicht, und der Grund ist die Geschichte dieses Ordners:
    #
    # `auf-20260818-01` bis `-05` sind allesamt `art: "multipass"` und haben `fehler`
    # zurückgemeldet — genau daran wurde die Blender-5.2-Sperre überhaupt gefunden. Ohne
    # diese Prüfung käme derselbe Lauf jetzt als `status: ok, urteil: {multipass: ok}`
    # zurück, und die einzige Spur wäre ein fehlender Dateiname in einer Liste. Das ist
    # dieselbe Bauart Fehler wie das Lexikon-Verzeichnis, das Einträge versprach, die es
    # nie gab: unauffindbar, weil als erledigt abgehakt.
    #
    # Ein Auftrag ist ein Bericht an jemanden, der nicht danebensteht. Er muss lauter
    # sein als eine Bibliotheksfunktion, nicht leiser.
    if not blender_bericht.get("depth_png"):
        return auf.baue_ergebnis(
            auftrag_id=satz["auftrag_id"], status="fehler", messwerte=messwerte,
            urteil={"multipass": "unvollstaendig",
                    "was_fehlt": "tiefe_norm.png",
                    "was_da_ist": "die EXR mit den echten Metern (siehe depth_exr_kanaele)"},
            fehler=("Multipass lief, aber ohne normalisierte Tiefenkarte: "
                    + (blender_bericht.get("depth_png_fehler")
                       or blender_bericht.get("error") or "kein Grund genannt")),
            dauer_s=round(time.monotonic() - beginn, 1),
            umgebung=_umgebung())

    return auf.baue_ergebnis(
        auftrag_id=satz["auftrag_id"], status="ok",
        messwerte=messwerte,
        urteil={"multipass": "ok"},
        dauer_s=round(time.monotonic() - beginn, 1),
        umgebung=_umgebung())


#: Felder, deren Wert ein Pfad ist und die darum gekürzt werden müssen.
_PFADFELDER = ("bild_png", "depth_png", "beauty_png", "ausgabe_png", "modell_wurzel",
               "depth_exr", "material_id_png")


def _nur_dateinamen(wert):
    """Pfade auf Dateinamen kürzen — Regel 3, ausführbar statt als Bitte.

    Der Befund, der diese Funktion nötig machte (18.08.2026, adversariale Prüfung): Vier
    Felder trugen den **vollen Pfad des Arbeitsverzeichnisses der HomeStation** in ein
    öffentliches Repo — `geometrie_qa.bild_png` sowie `depth_png`, `beauty_png` und
    `ausgabe_png` in `render.parameter`. Für `render.bild` war derselbe Pfad ausdrücklich
    gekürzt worden; die anderen vier blieben ganz, weil sie tiefer im Ergebnis lagen.

    Das ist die verräterischste Sorte Regel-3-Verstoss: kein Bild, keine Geometrie — nur
    ein Pfad. Aber ein Pfad trägt Benutzernamen, Ordnerstruktur und, sobald einmal mit
    echten Projekten gearbeitet wird, Büro- und Kundennamen. `CLAUDE.md` nennt genau das:
    „Auch keine Büro-, Kunden- oder Projektnamen in Pfaden."

    Rekursiv, weil die Felder in verschachtelten Wörterbüchern sitzen. Was kein Pfadfeld
    ist, bleibt unverändert — dies ist keine allgemeine Bereinigung, sondern eine
    Positivliste.
    """
    if isinstance(wert, dict):
        return {k: (Path(v).name if k in _PFADFELDER and isinstance(v, str) and v
                    else _nur_dateinamen(v))
                for k, v in wert.items()}
    if isinstance(wert, (list, tuple)):
        return [_nur_dateinamen(v) for v in wert]
    return wert


def _render_und_qa(satz: dict, blender_bericht: dict, glb_bericht: dict,
                   aus: Path, params: dict, beginn: float, *,
                   _render_modell=None, _tiefen_modell=None) -> dict:
    """Die Stufe, für die es diesen Rechner gibt: Bildmodell, dann Messung.

    Bis zum 18.08.2026 meldete `art: "render"` hier `uebersprungen` — der Adapter in
    `aiimaging.render` war gebaut, aber **nie ausgeführt**, weil im Entwicklungscontainer
    weder GPU noch Gewichte liegen. Das ist die offene Fläche, die dieser Weg schliesst.

    Vier Dinge werden hier zum ersten Mal gleichzeitig geprüft, und sie sind bewusst
    **einzeln** berichtet, damit ein Bruch in der Mitte nicht die Erkenntnis der ersten
    Hälfte mitnimmt:

    1. Lädt und läuft der diffusers-Adapter mit echten Gewichten überhaupt?
    2. Genügt Depth-Anything-V2-**Small** (das einzige unter Regel 1 zulässige) auf einem
       Architekturbild — oder braucht die Metrik ein Modell, das wir nicht nehmen dürfen?
    3. Liefert die Geometrie-Metrik auf einem **erzeugten** Bild plausible Zahlen? Bisher
       ist sie nur an synthetischen Karten belegt (treu 0.99, halluziniert 0.24).
    4. Trägt die Schwelle 0.65 auf dieser Naht? Sie ist an wenigen Fällen gesetzt und auf
       einem echten Render noch nie gemessen worden.

    Regel 3: Zurück reisen nur Zahlen, Urteile und **Dateinamen**. Die Bilder bleiben auf
    der HomeStation.
    """
    from aiimaging import bildlesen, maske, render, tiefenschaetzer

    messwerte = {
        "bbox_size_m": blender_bericht.get("bbox_size_m"),
        "n_meshes": blender_bericht.get("n_meshes"),
        "n_triangles": glb_bericht.get("n_triangles"),
        "depth_exr_kanaele": blender_bericht.get("depth_exr_kanaele"),
        "depth_exr_format": blender_bericht.get("depth_exr_format"),
        "depth_png_fehler": blender_bericht.get("depth_png_fehler"),
    }

    # Der Lizenzentscheid fällt **vor** dem Render, nicht danach.
    #
    # Bisher flog ein unter Regel 1 gesperrter Schätzer erst in der QA-Stufe heraus — als
    # Ausnahme, hinter der GPU-Stunde, und sie nahm die Messwerte der ersten Hälfte mit.
    # Das ist die Reihenfolge, die `render.rendere` schon richtig macht („Regel 1
    # entscheidet, bevor 20 GB Gewichte auf die GPU wandern"); hier fehlte sie.
    #
    # Regel 1 ist keine Zusatzprüfung am Ende, sondern die erste Frage.
    try:
        tiefenschaetzer.fordere_zulaessigen(
            params.get("schaetzer", tiefenschaetzer.VORGABE_TIEFENSCHAETZER))
    except Exception as e:
        return auf.baue_ergebnis(
            auftrag_id=satz["auftrag_id"], status="fehler", messwerte=messwerte,
            urteil={"regel_1": "abgelehnt", "stufe": "vor dem Render"},
            fehler=f"Tiefenschätzer unter Regel 1 nicht zulässig: {e}",
            dauer_s=round(time.monotonic() - beginn, 1), umgebung=_umgebung())

    depth_png = blender_bericht.get("depth_png")
    if not depth_png:
        return auf.baue_ergebnis(
            auftrag_id=satz["auftrag_id"], status="fehler", messwerte=messwerte,
            fehler=("Kein `depth_png` — ohne Tiefenkarte gibt es keine Konditionierung, "
                    "und ein Render ohne sie wäre genau die erfundene Kubatur, gegen die "
                    "dieses Projekt antritt. Grund siehe `depth_png_fehler`."),
            dauer_s=round(time.monotonic() - beginn, 1), umgebung=_umgebung())

    # ── 1 · Der Render ────────────────────────────────────────────────────────────────
    a = render.RenderAuftrag(
        depth_png=depth_png,
        prompt=params.get("prompt", ""),
        negativ_prompt=params.get("negativ_prompt", ""),
        backbone=params.get("backbone", render.VORGABE_BACKBONE),
        seed=params.get("seed", 0),
        schritte=params.get("schritte", 20),
        controlnet_staerke=params.get("controlnet_staerke", 0.8),
        denoise=params.get("denoise", 0.6),
        # Der Beauty-Pass als Anker macht daraus echtes Image-Edit statt txt2img. Er ist
        # optional, weil genau das eine der Fragen ist, die gemessen werden sollen.
        beauty_png=(blender_bericht.get("beauty_png")
                    if params.get("mit_beauty", True) else None),
        ausgabe_png=str(aus / "render.png"),
        modell_wurzel=params.get("modell_wurzel"),
    )
    r = render.rendere(a, modell=_render_modell)
    messwerte["render"] = {
        "status": r["status"], "seed": r.get("seed"), "backbone": r.get("backbone"),
        "dauer_s": r.get("dauer_s"), "parameter": _nur_dateinamen(r.get("parameter")),
        "lizenz": r.get("lizenz"), "maengel": r.get("maengel"),
        "hinweise": r.get("hinweise"),
        "bild": Path(r["bild_png"]).name if r.get("bild_png") else None,
    }
    if r["status"] != "ok":
        return auf.baue_ergebnis(
            auftrag_id=satz["auftrag_id"], status="fehler", messwerte=messwerte,
            urteil={"render": r["status"], "grund": r.get("error") or r.get("maengel")},
            fehler=f"Render {r['status']}: {r.get('error') or r.get('maengel')}",
            dauer_s=round(time.monotonic() - beginn, 1), umgebung=_umgebung())

    # ── 2 · Die Messung ───────────────────────────────────────────────────────────────
    # Die Soll-Karte kommt aus der EXR, nicht aus dem PNG: nur sie trägt die Silhouette
    # exakt (siehe `bildlesen`, Modul-Docstring). Das PNG war die Eingabe des Modells,
    # die EXR ist der Massstab.
    try:
        soll, breite, hoehe = bildlesen.tiefen_aus_report(blender_bericht)
    except Exception as e:
        return auf.baue_ergebnis(
            auftrag_id=satz["auftrag_id"], status="fehler", messwerte=messwerte,
            fehler=f"Soll-Tiefenkarte nicht lesbar: {type(e).__name__}: {e}",
            dauer_s=round(time.monotonic() - beginn, 1), umgebung=_umgebung())

    # DIE MASKE GEHOERT HIER HEREIN, und bis zum 26.08.2026 kam sie nicht.
    #
    # Ohne sie bleiben `rho_maske`, Kante und Paarurteil ungemessen — genau die Masse,
    # die die ABWESENHEIT eines Bauwerks fangen. Der Score ueber das ganze Bild fangt sie
    # nicht: Ein leeres Grundstueck erreichte dort 0.9530 und bestand das Tor
    # (auf-20260821-26). Dieses Skript ist der Weg, auf dem die HomeStation ihre
    # Render-Auftraege abarbeitet — die Luecke sass also dort, wo wirklich gemessen wird.
    #
    # Gefunden wurde sie durch Zaehlen von der anderen Seite: `qa_gegen_soll` hat drei
    # Aufrufstellen, und nur der Abholer reichte eine Maske herein.
    # `gelaende_erwartet` kommt aus den Auftragsparametern — dieselbe Erklaerung wie
    # `--kein-gelaende` beim Abholer, nur dass sie hier im Auftrag steht statt an der
    # Kommandozeile. Vorgabe ist True: Wer nichts sagt, bekommt die strengere Lesart, und
    # eine ausgefallene Maske ist dann ein Befund und keine stille Annahme.
    maskenbefund = maske.maske_aus_bericht(
        blender_bericht,
        gelaende_erwartet=bool(params.get("gelaende_erwartet", True)))
    # OHNE `_nur_dateinamen` reist hier der volle Pfad des Arbeitsverzeichnisses mit —
    # `maske_aus_bericht` gibt `material_id_png` zurueck, damit sich eine Maske
    # zurueckverfolgen laesst. Regel 3, und der Waechter in `test_homeworker` hat es beim
    # ersten Versuch gefangen. Die Maske selbst (Tausende Wahrheitswerte) faellt ohnehin
    # heraus: Ein Ergebnis traegt Zahlen und Text, keine Bilddaten.
    messwerte["maskenbefund"] = _nur_dateinamen(
        {k: v for k, v in maskenbefund.items() if k != "maske"})

    qa = tiefenschaetzer.qa_gegen_soll(
        r["bild_png"], soll, breite=breite, hoehe=hoehe, modell=_tiefen_modell,
        schaetzer=params.get("schaetzer", tiefenschaetzer.VORGABE_TIEFENSCHAETZER),
        schwelle=params.get("schwelle", None) or geometrie_schwelle(),
        maske=maskenbefund.get("maske"),
    )
    messwerte["geometrie_qa"] = _nur_dateinamen(qa)

    # `status` des Auftrags bildet ab, ob **gemessen** wurde — nicht, ob das Bild besteht.
    # Ein Render, der die Schwelle reisst, ist ein gelungener Auftrag mit einem klaren
    # Befund; ihn als Fehler zu melden würde die Auftragsliste unlesbar machen.
    return auf.baue_ergebnis(
        auftrag_id=satz["auftrag_id"],
        status="ok" if qa["status"] == "ok" else "fehler",
        messwerte=messwerte,
        urteil={
            "render": "ok",
            "gemessen": qa["status"] == "ok",
            "bestanden": qa.get("bestanden"),
            "score": qa.get("score"),
            "begruendung": qa.get("begruendung"),
        },
        fehler=qa.get("error"),
        dauer_s=round(time.monotonic() - beginn, 1), umgebung=_umgebung())


def geometrie_schwelle() -> float:
    """Die Bestehensgrenze der Geometrie-QA — aus dem Kern, nicht hier nochmal getippt.

    Eine zweite Stelle mit derselben Zahl wäre genau die Art stiller Abweichung, die
    dieses Projekt zu vermeiden versucht: Wer die Schwelle in der Schwellenstudie
    (Phase 4) ändert, änderte sonst nur die eine Hälfte.
    """
    from aiimaging import geometrie_qa
    return geometrie_qa.SCHWELLE_GEOMETRIE


def _umgebung() -> dict:
    """Was den Messwert später einordnen lässt. Ohne das ist eine Zahl wertlos."""
    z = gpu_zustand()
    return {
        "gpu": z.get("name") if z.get("verfuegbar") else "keine",
        "leistungsgrenze_w": z.get("leistungsgrenze_w"),
        "python": sys.version.split()[0],
        "blender": shutil.which("blender") or "/opt/blender/blender",
    }


# ── Kommandozeile ────────────────────────────────────────────────────────────────────

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Aufträge aus dem Repo auf der HomeStation ausführen.")
    ap.add_argument("--repo", default=".", help="Repo-Wurzel")
    ap.add_argument("--liste", action="store_true", help="nur zeigen, was unerledigt ist")
    ap.add_argument("--alle", action="store_true", help="alles Unerledigte abarbeiten")
    ap.add_argument("--auftrag", default=None, help="einen bestimmten Auftrag")
    ap.add_argument("--gpu", action="store_true", help="nur den GPU-Zustand zeigen")
    ap.add_argument("--hoechstens", type=int, default=None, metavar="N",
                    help="hoechstens N Auftraege je Durchgang (fuer den Takt eines Dienstes)")
    a = ap.parse_args(argv)
    repo = Path(a.repo).resolve()

    if a.gpu:
        print(json.dumps(gpu_zustand(), indent=2, ensure_ascii=False))
        return 0

    alle_offenen = auf.unerledigt(repo)

    # FREMDE AUFTRAEGE WERDEN NICHT ANGEFASST — und ausdruecklich auch nicht mit einem
    # Ergebnis geschlossen. Ein geschriebenes Ergebnis heisst hier "beantwortet"; eine
    # Ablehnung waere also schlimmer als Schweigen. Sie werden GEZAEHLT und genannt,
    # damit niemand sie fuer erledigt haelt.
    fremd = [s for s in alle_offenen if s.get("worker") != EIGENER_WORKER]
    offen = [s for s in alle_offenen if s.get("worker") == EIGENER_WORKER]
    if fremd:
        print(f"{len(fremd)} Auftraege sind nicht fuer {EIGENER_WORKER!r} und bleiben "
              f"liegen (kein Ergebnis geschrieben):")
        for s in fremd:
            print(f"  {s['auftrag_id']}  -> {s.get('worker')!r}")
        print()

    if a.auftrag:
        gewaehlt = [s for s in alle_offenen if s["auftrag_id"] == a.auftrag]
        if not gewaehlt:
            print(f"Kein unerledigter Auftrag {a.auftrag!r}.")
            return 1
        if gewaehlt[0].get("worker") != EIGENER_WORKER:
            print(f"{a.auftrag} ist fuer {gewaehlt[0].get('worker')!r}, nicht fuer "
                  f"{EIGENER_WORKER!r}. Es wird nichts ausgefuehrt und nichts "
                  f"geschrieben — ein Ergebnis von hier waere eine Antwort, die niemand "
                  f"gegeben hat.")
            return 1
        offen = gewaehlt

    if a.liste or not (a.alle or a.auftrag):
        if not offen:
            print("Nichts unerledigt.")
            return 0
        print(f"{len(offen)} unerledigt fuer {EIGENER_WORKER!r}:")
        for s in offen:
            print(f"  {s['auftrag_id']}  [{s['art']}]  {s['beschreibung'][:70]}")
        return 0

    # EIN DECKEL JE DURCHGANG — fuer den Betrieb als Dienst.
    #
    # `--alle` kann zwoelf Auftraege bedeuten, und ein Renderlauf dauert Minuten. Ein
    # Takt, der erst nach Stunden zurueckkommt, ist keiner: Die Karte bleibt belegt, ein
    # dringender Auftrag wartet hinter elf alten, und ein haengender Lauf haelt die ganze
    # Reihe auf. Der Abholer loest dasselbe mit `--hoechstens 1`; hier stand es bis zum
    # 26.08.2026 nicht zur Verfuegung, und darum lief der Homeworker nur von Hand.
    #
    # Die Reihenfolge bleibt die der Ablage — wer den aeltesten zuerst will, sagt es mit
    # `--auftrag`. Eine eigene Sortierung hier waere eine Betriebsentscheidung an der
    # falschen Stelle.
    if a.hoechstens is not None:
        if a.hoechstens < 1:
            print(f"--hoechstens {a.hoechstens}: mindestens 1, sonst laeuft nichts.")
            return 1
        offen = offen[:a.hoechstens]

    zustand = gpu_zustand()
    for satz in offen:
        frei, grund = darf_starten(zustand, satz.get("auflagen") or {})
        print(f"\n=== {satz['auftrag_id']} [{satz['art']}] — {grund}")
        if not frei and satz["art"] == "render":
            ergebnis = auf.baue_ergebnis(auftrag_id=satz["auftrag_id"], status="abgelehnt",
                                         fehler=grund, umgebung=_umgebung())
        else:
            try:
                ergebnis = fuehre_aus(satz, repo)
            except Exception as e:                       # noqa: BLE001
                ergebnis = auf.baue_ergebnis(auftrag_id=satz["auftrag_id"], status="fehler",
                                             fehler=f"{type(e).__name__}: {e}",
                                             umgebung=_umgebung())
        pfad = auf.schreibe_ergebnis(ergebnis, repo)
        print(f"    → {ergebnis['status']}  ({pfad.relative_to(repo)})")

    print("\nFertig. Jetzt:  git add auftraege/ergebnisse && git commit -m '...' && git push")
    return 0


if __name__ == "__main__":
    sys.exit(main())
