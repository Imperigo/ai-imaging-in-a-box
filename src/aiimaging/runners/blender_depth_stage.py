#!/usr/bin/env python3
"""RUNNER — glb → Cycles-Multipass. Läuft INNERHALB von Blender, nie im Produkt.

Warum dieses Skript ein eigener Prozess ist
-------------------------------------------
Blender steht unter GPL-2.0-or-later (Binär-Releases GPL-3.0-or-later). Ein `import bpy`
im Produkt-Environment zöge das strengere Linking-Argument nach sich und machte das
Produkt GPL. Regel 2 zieht die Grenze deshalb am **Prozessaufruf**:

    blender --background --python blender_depth_stage.py -- <argumente>

Das ist GPL-rechtlich eine Aggregation. Blender bleibt GPL, der Apache-2.0-Code dieses
Projekts bleibt Apache-2.0.

**Dieses Modul darf aus `aiimaging` heraus niemals importiert werden** — ausserhalb von
Blender existiert `bpy` nicht, und innerhalb wäre der Import die verbotene Verbindung.
`tests/test_prozessgrenze.py` erzwingt das.

Die drei Ausgaben — und die vierte, die hier NICHT mehr entsteht
----------------------------------------------------------------
1. **Beauty** (`beauty_.png`) — das gewöhnliche gerenderte Bild. Beleuchtet von einer
   Sonne plus gleichmässigem Umgebungslicht. Bewusst schlicht und fest verdrahtet: Die
   Lichtstimmung ist nicht Gegenstand dieser Phase, die Reproduzierbarkeit schon.
2. **Material-ID** (`material_id.png`) — pro Material eine flache, unbeleuchtete
   Farbfläche. Dient später als Segmentierungsmaske für die Geometrie-QA.
3. **Tiefe roh** (`tiefe_0001.exr` bzw. `tiefe_.exr`) — 32-Bit-EXR über den Compositor,
   mit **echten Meterwerten**. Das ist die Grundlage der Geometrie-QA.

Die normalisierte Tiefenkarte (`tiefe_norm.png`) entstand bis zum 18.08.2026 ebenfalls
hier — sie wurde aus der eben geschriebenen EXR zurückgelesen und umgerechnet. Dieser
Schritt ist auf die **Produktseite** gewandert, nach
:mod:`aiimaging.bildschreiben`; `seams.glb_zu_multipass` führt ihn nach dem Blender-Lauf
aus. Der Grund ist ein Befund von der HomeStation (Blender 5.2.0 LTS, am Gerät gemessen):

    Blender 5.2 kann die Datei, die es schreiben **muss**, selbst nicht wieder einlesen.
    Der File-Output-Knoten lässt dort nur `OPEN_EXR_MULTILAYER` zu, und eine so
    geschriebene Datei lädt `bpy.data.images.load` als **0×0 mit 0 Kanälen**. Eine
    einschichtige EXR lädt im selben Lauf als 64×64 mit 4 Kanälen.

Die Datei ist dabei in Ordnung — `aiimaging.bildlesen.lies_exr_tiefe_stdlib` holt aus
derselben 5.2-Datei 11 151 Geometriepixel zwischen 17,9 und 26,6 m heraus, exakt die
Zahlen, die Blender 4.2 aus seiner eigenen EXR meldet. Es lag am Multilayer-Leseweg.

Die Lehre ist allgemeiner als der Fehler: Eine Normalisierung ist Arithmetik auf einem
Zahlenfeld. Sie in einem GPL-Programm auszuführen, dessen Leseweg sich zwischen zwei
Fassungen ändert, bringt keinen Gewinn und ein Risiko. Der Runner tut ab jetzt nur noch,
was allein Blender kann: rendern.

Zwei Renderdurchgänge, kein Kompromiss
--------------------------------------
Beauty und Tiefe entstehen im **selben** Durchgang (die Tiefe ist ein View-Layer-Pass,
sie kostet keinen zweiten Strahl). Die Material-ID braucht dagegen einen **eigenen**
Durchgang: Sie ersetzt jedes Material durch einen Emissions-Shader, und dieser Eingriff
würde das Beauty-Bild in dieselbe flache Farbfläche verwandeln.

Warum die Farben unbeleuchtet sein müssen
-----------------------------------------
Eine Material-ID-Farbe ist eine *Kennung*, kein Aussehen. Sähe sie Licht, wären zwei
Wände desselben Materials in Sonne und Schatten zwei verschiedene Farben — die Maske
wäre unbrauchbar. Emissions-Shader (mit schwarzer Welt und einem einzigen Sample)
liefern den Farbwert exakt so, wie er gesetzt wurde.

Aufruf (immer über `aiimaging.seams`, nicht von Hand):
    blender --background --python blender_depth_stage.py -- \
        --glb <in.glb> --out <verzeichnis> [--aufloesung 512] [--samples 16] \
        [--rotiere-z-up] [--ohne-beauty] [--ohne-material-id]
"""
from __future__ import annotations

import colorsys
import json
import math
import os
import sys
import time
from pathlib import Path

import bpy  # noqa: E402  — nur innerhalb von Blender vorhanden; siehe Modul-Docstring

#: Goldener Winkel als Anteil eines Vollkreises (1/φ²). Die Farbtöne der Material-IDs
#: werden damit über den HSV-Farbkreis verteilt: h = (i * GOLDENER_WINKEL) % 1.0.
#: Der Grund ist eine Eigenschaft der Zahl selbst — weil sie irrational ist, liegen auch
#: aufeinanderfolgende Indizes weit auseinander, und die Folge häuft sich nie. Eine
#: gleichmässige Teilung (h = i/n) bräuchte dagegen die Gesamtzahl im Voraus und änderte
#: bei jedem neuen Material sämtliche bisherigen Farben.
GOLDENER_WINKEL = 0.618033988749895

#: Sättigung und Helligkeit der ID-Farben. Fest, damit sich die Farben allein im Farbton
#: unterscheiden — das ist die Achse, auf der der Goldene Winkel den Abstand garantiert.
ID_SAETTIGUNG = 0.85
ID_HELLIGKEIT = 1.00

#: Ab diesem Wert gilt ein Tiefenpixel als Hintergrund. Cycles schreibt für Strahlen ins
#: Leere keinen Fehlwert, sondern eine sehr grosse Zahl (Grössenordnung 1e10). Ohne diese
#: Schranke risse ein einziges Hintergrundpixel die Normalisierung auseinander und das
#: ganze Gebäude wäre schwarz.
HINTERGRUND_AB_M = 1.0e7


def _argumente():
    """Argumente hinter dem `--`-Trenner lesen (davor gehört alles Blender)."""
    import argparse

    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--glb", required=True)
    ap.add_argument("--out", required=True)
    # `--aufloesung` ist die BREITE. `--hoehe` fehlt heisst quadratisch — so war es bis
    # zum 19.08.2026 immer, und jede bisher gemessene Zahl hängt daran.
    ap.add_argument("--aufloesung", type=int, default=512)
    # Sonnenstand. `None` heisst NICHT VORGEGEBEN — die Vorgabewerte stehen in
    # `aiimaging.sonne` und nicht hier, siehe `_vorgabe`.
    ap.add_argument("--sonne-hoehe", type=float, default=None,
                    help="Grad ueber dem Horizont; ohne Angabe gilt aiimaging.sonne")
    ap.add_argument("--sonne-azimut", type=float, default=None,
                    help="Grad nach --sonne-konvention")
    ap.add_argument("--sonne-konvention", default=None,
                    help="von_sueden (Vorgabe) oder von_norden")
    ap.add_argument("--hoehe", type=int, default=None,
                    help="Bildhöhe in Punkten. Ohne Angabe quadratisch. Das "
                         "Seitenverhältnis geht in den Bildwinkel und damit in den "
                         "Kameraabstand ein — es ist keine Zuschneidefrage.")
    ap.add_argument("--samples", type=int, default=16)
    ap.add_argument("--rotiere-z-up", action="store_true",
                    help="Quelle ist Z-up (z.B. kosmodraw_export_glb) → vor dem Rendern drehen")
    ap.add_argument("--ohne-beauty", action="store_true",
                    help="Beauty-Bild nicht schreiben (der Durchgang läuft trotzdem — die "
                         "Tiefe hängt an ihm)")
    ap.add_argument("--ohne-material-id", action="store_true",
                    help="zweiten Renderdurchgang auslassen; spart etwa die halbe Rechenzeit")
    # --- Kamera: drei Wege, und der Bericht sagt, welcher gegriffen hat ----------------
    ap.add_argument("--auge", default=None,
                    help="Kamerastandort 'x,y,z' in Metern. Hat Vorrang vor --kamera. "
                         "Der Weg für einen Aufrufer, der selbst gerechnet hat.")
    ap.add_argument("--blick-auf", default=None,
                    help="Blickziel 'x,y,z' in Metern. Pflicht zusammen mit --auge.")
    ap.add_argument("--kamera", default=None,
                    help="Richtungskürzel aus aiimaging.kameras (n, e, s, w, nNE, …). "
                         "Der Standort wird dann aus der gemessenen Hüllbox dieser Szene "
                         "abgeleitet — also im selben Bezugssystem, in dem gerendert wird.")
    # KEINE Vorgabe. Ohne Angabe bleibt Blenders eigene Brennweite stehen — siehe
    # `_kamera_setzen`: Der Rückfall ist die Bezugsgrösse aller bisherigen Messungen,
    # und eine stillschweigend geänderte Optik verschöbe sie alle.
    ap.add_argument("--brennweite", type=float, default=None)
    ap.add_argument("--kamera-modus", dest="kamera_modus", default=None,
                    help="'gekippt' (Vorgabe) oder 'shift'. Wirkt nur zusammen mit "
                         "--kamera: Der Modus geht in `kameras.kamerasatz`, und der von "
                         "dort gerechnete Shift wird gestellt. Ein ausdrücklich "
                         "gesetztes --shift-y schlägt ihn.")
    ap.add_argument("--shift-y", dest="shift_y", type=float, default=None,
                    help="Objektiv-Shift nach oben, als Anteil der GRÖSSEREN Sensorkante "
                         "(Blenders Einheit). Gesetzt heisst: waagrechte Kamera, "
                         "senkrechte Kanten bleiben senkrecht. Gerechnet wird er in "
                         "`kameras.MODUS_SHIFT`; hier wird er nur gestellt.")
    ap.add_argument("--bias", type=float, default=35.0)
    ap.add_argument("--augenhoehe", type=float, default=1.70)
    # KEIN fester Vorgabewert hier. Am 23.08.2026 sind zwei abgeschriebene 28.0
    # aufgefallen, die beim Wechsel der Brennweite still auseinandergelaufen
    # waeren; dies ist dieselbe Stelle fuer den Deckungsgrad. None heisst: was
    # die Bibliothek sagt.
    ap.add_argument("--deckungsgrad", type=float, default=None)
    ap.add_argument("--gelaende-z", type=float, default=None,
                    help="Geländehöhe im Weltsystem. Ohne Angabe die Unterkante der "
                         "Hüllbox — bei einem Untergeschoss stünde die Kamera sonst im Keller.")
    ap.add_argument("--kamera-huellbox", default=None,
                    help="Sechs Zahlen 'x0,y0,z0,x1,y1,z1' — die Hüllbox, auf die sich "
                         "die KAMERA bezieht. Ohne Angabe alle Meshes. Gebraucht, sobald "
                         "die Szene Gelände trägt: Ein Geländestück blaeht die Hüllbox "
                         "auf, die Kamera zieht sich zurück, und das Gebäude wird kleiner "
                         "statt grösser. Am 20.08.2026 gemessen — siehe _bbox_aller_meshes.")
    ap.add_argument("--herzschlag-s", type=float, default=None,
                    help="Alle so viele Sekunden ein Lebenszeichen nach "
                         "<out>/herzschlag.txt schreiben. Ohne Angabe: keines. Siehe "
                         "`_herzschlag_starten` — es ist ein LEBENSzeichen und kein "
                         "Fortschrittszeichen, und der Unterschied ist der ganze Punkt.")
    return ap.parse_args(argv)


#: Name der Datei, in die der Herzschlag geschrieben wird. Auch auf der anderen Seite der
#: Prozessgrenze bekannt (``aiimaging.seams.HERZSCHLAG_DATEI``) — ein Dateiname, den zwei
#: Seiten unabhängig raten, ist eine tote Kante mit Ansage.
HERZSCHLAG_DATEI = "herzschlag.txt"


def _herzschlag_starten(ziel, takt_s: float):
    """Einen Faden starten, der während des Renderns ein Lebenszeichen schreibt.

    **Warum ein eigener Faden und keiner der beiden naheliegenden Haken.** Am 20.08.2026
    an Blender 4.2 gemessen, alle drei Kandidaten im selben Lauf, 512×512 mit 3000 Samples
    ohne adaptives Sampling:

    ===========================  ==========================================
    ``bpy.app.handlers.render_stats``  registriert, **null** Aufrufe während des Renders
    ``bpy.app.timers``                 **null** Aufrufe während des Renders
    ein einfacher ``threading.Thread``  **61** Einträge, alle 2 s, durchgehend
    ===========================  ==========================================

    Cycles gibt während des Renderns die GIL frei; ein gewöhnlicher Python-Faden läuft
    also weiter, während ``bpy.ops.render.render()`` den Hauptfaden blockiert. Die beiden
    dokumentierten Haken tun es nicht.

    **Und jetzt die Einschränkung, ohne die dieser Faden schädlich wäre.**

        Was hier entsteht, ist ein **Lebenszeichen** und kein **Fortschrittszeichen**.

    Es belegt: Der Prozess lebt, und sein Python-Interpreter kommt zum Zug. Es belegt
    **nicht**, dass der Renderer vorankommt — ein Cycles-Kern, der sich festgefahren hat,
    ohne den Prozess mitzunehmen, schlägt weiter. Wer aus einem laufenden Herzschlag auf
    Fortschritt schliesst, macht genau den Fehler, gegen den
    :mod:`aiimaging.fortschritt` gebaut ist.

    Der Umkehrschluss trägt dagegen: Ein **ausbleibender** Herzschlag heisst zuverlässig,
    dass der Prozess tot, eingefroren oder vom Betriebssystem angehalten ist. Und genau
    darauf — und nur darauf — schlägt die Wache an.

    Geschrieben wird **angehängt**, damit die Datei wächst: Eine Datei gleicher Grösse mit
    neuem Zeitstempel ist auf manchen Dateisystemen nicht von einer unveränderten zu
    unterscheiden.

    Returns:
        ``(faden, stoppen)`` — ``stoppen`` ist ein Ereignis, das den Faden beendet.
    """
    import threading

    ziel = Path(ziel)
    stoppen = threading.Event()
    beginn = time.monotonic()

    def schlagen():
        schlag = 0
        while not stoppen.is_set():
            schlag += 1
            try:
                with open(ziel, "a", encoding="utf-8") as datei:
                    datei.write(f"{schlag} {time.monotonic() - beginn:.1f}\n")
                    datei.flush()
                    os.fsync(datei.fileno())
            except OSError:
                # Ein Herzschlag, der sich nicht schreiben lässt, darf den Lauf nicht
                # mitnehmen. Sein Ausbleiben meldet die Wache ohnehin.
                pass
            stoppen.wait(takt_s)

    faden = threading.Thread(target=schlagen, name="herzschlag", daemon=True)
    faden.start()
    return faden, stoppen


def _punkt_aus_text(text, name: str):
    """``'12.5,-30,1.7'`` → ``(12.5, -30.0, 1.7)``.

    Raises:
        RuntimeError: nicht drei endliche Zahlen. Eine halb gelesene Kameraposition wäre
            schlimmer als gar keine — das Bild entstünde und zeigte etwas anderes als
            gemeint, ohne dass irgendwo ein Fehler stünde.
    """
    teile = [t.strip() for t in str(text).split(",")]
    if len(teile) != 3:
        raise RuntimeError(f"{name} braucht drei durch Komma getrennte Zahlen, war: {text!r}")
    try:
        werte = tuple(float(t) for t in teile)
    except ValueError as e:
        raise RuntimeError(f"{name} enthält keine Zahl: {text!r}") from e
    if any(w != w or w in (float("inf"), float("-inf")) for w in werte):
        raise RuntimeError(f"{name} enthält nan oder inf: {text!r}")
    return werte


def _vorgabe(a, feld: str, aus_der_bibliothek):
    """Der Wert vom Aufrufer — oder der aus der Bibliothek, **nicht** einer von hier.

    **Der Anlass sind zwei abgeschriebene ``28.0``** (23.08.2026): Die Brennweite war im
    Kern längst einstellbar, und zwei fest verdrahtete Kopien an der Aussenkante wären beim
    Wechsel auf 35 mm still auseinandergelaufen. Ein Vorgabewert, der an zwei Stellen
    steht, ist an einer davon bereits falsch — nur merkt es niemand, solange beide gleich
    sind.

    Darum steht in ``argparse`` ``None`` und hier die einzige Quelle.
    """
    wert = getattr(a, feld, None) if a is not None else None
    return float(aus_der_bibliothek if wert is None else wert)


def _kameras_modul():
    """``aiimaging.kameras`` von hier aus erreichbar machen — oder ``None``.

    Blenders Python kennt dieses Projekt nicht. Der Pfad wird darum aus der Lage dieser
    Datei abgeleitet (``src/aiimaging/runners/`` → ``src``), nicht aus einer Umgebung.

    **Die Richtung des Imports ist die erlaubte.** Der Runner darf aus dem Produkt lesen;
    verboten ist nur der umgekehrte Weg — ein ``import`` dieses Skripts aus ``aiimaging``
    heraus zöge ``bpy`` in das Produkt-Environment (Regel 2, `tests/test_prozessgrenze.py`).
    ``kameras`` ist reine stdlib-Arithmetik und bringt nichts mit.

    ``None`` statt einer Ausnahme: Ein fehlendes Modul soll den Lauf nicht abbrechen,
    sondern in den Rückfall führen — und der Bericht sagt es dann ausdrücklich.
    """
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
        from aiimaging import kameras                      # noqa: PLC0415
        return kameras
    except Exception:                                      # noqa: BLE001
        return None


def _szene_leeren() -> None:
    """Blenders Standardszene (Würfel, Licht, Kamera) entfernen — sie verfälscht die Tiefe."""
    bpy.ops.wm.read_factory_settings(use_empty=True)


def _huellbox_aus_text(text: str):
    """``"x0,y0,z0,x1,y1,z1"`` → ``(lo, hi)``. Sechs Zahlen, keine fünf und keine sieben."""
    teile = [t.strip() for t in str(text).split(",")]
    if len(teile) != 6:
        raise SystemExit(
            f"--kamera-huellbox braucht genau sechs Zahlen 'x0,y0,z0,x1,y1,z1', "
            f"bekam {len(teile)}: {text!r}")
    try:
        z = [float(t) for t in teile]
    except ValueError as fehler:
        raise SystemExit(f"--kamera-huellbox enthält keine Zahlen: {text!r}") from fehler
    lo, hi = z[:3], z[3:]
    for i in range(3):
        if hi[i] < lo[i]:
            raise SystemExit(
                f"--kamera-huellbox: Achse {i} läuft rückwärts ({lo[i]} > {hi[i]}). "
                f"Die Reihenfolge ist x0,y0,z0,x1,y1,z1 — erst die untere Ecke.")
    return lo, hi


def _bbox_aller_meshes():
    """Achsparallele Bounding-Box aller Mesh-Objekte in Weltkoordinaten.

    **Nicht immer die richtige Grundlage für die Kamera** — und das ist am 20.08.2026
    gemessen worden. Bekommt der Testbau eine Geländeplatte in 2,5-facher Gebäudespanne,
    wächst die Hüllbox von 8 × 5 m auf 20 × 20 m. Die Kamera zieht sich entsprechend
    zurück, und der Geometrieanteil des Bildes **sinkt** von 6,9 % auf 0,9 %: Eine flache
    Platte, von 1,70 m Augenhöhe aus gesehen, füllt fast keine Bildfläche.

    Mit **fester** Kamera — also dem gleichen Standpunkt für beide Szenen — geht derselbe
    Anteil von 21,9 % auf 51,8 % **hinauf**. Das Gelände wirkt also genau wie erhofft;
    was nicht wirkt, ist die Kamera, die es mitrahmt.

    Wer Gelände in der Szene hat, gibt der Kamera darum ``--kamera-huellbox`` mit: die
    Hüllbox des **Bauwerks**. Die Kamera rahmt dann, was gezeigt werden soll, und nicht
    alles, was dasteht.
    """
    lo = [float("inf")] * 3
    hi = [float("-inf")] * 3
    for obj in bpy.data.objects:
        if obj.type != "MESH":
            continue
        for ecke in obj.bound_box:
            welt = obj.matrix_world @ __import__("mathutils").Vector(ecke)
            for i in range(3):
                lo[i] = min(lo[i], welt[i])
                hi[i] = max(hi[i], welt[i])
    if lo[0] == float("inf"):
        raise RuntimeError("keine Mesh-Geometrie in der Szene")
    return lo, hi


def _maske_modul():
    """``aiimaging.maske`` von hier aus erreichbar machen — oder ``None``.

    Dieselbe Bauart und dieselbe Begründung wie :func:`_kameras_modul`: Der Runner darf
    aus dem Produkt lesen, nur der umgekehrte Weg ist verboten (Regel 2).

    **Warum nicht einfach hier eine Wortliste hinschreiben.** Die Geländeregel steht in
    :data:`aiimaging.maske.GELAENDE_MUSTER` und :data:`aiimaging.maske.GELAENDE_WOERTER`,
    und sie ist diese Woche zweimal geschärft worden. Eine zweite Kopie an der
    Aussenkante wäre bei der nächsten Schärfung still auseinandergelaufen — genau der
    Fehler, gegen den :func:`_vorgabe` gebaut ist.
    """
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
        from aiimaging import maske                        # noqa: PLC0415
        return maske
    except Exception:                                      # noqa: BLE001
        return None


def _sonne_modul():
    """``aiimaging.sonne`` von hier aus erreichbar machen — oder ``None``.

    Dieselbe Bauart und Begründung wie :func:`_kameras_modul`: Der Runner darf aus dem
    Produkt lesen, nur der umgekehrte Weg ist verboten (Regel 2). ``sonne`` ist reine
    Trigonometrie und bringt nichts mit.
    """
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
        from aiimaging import sonne                         # noqa: PLC0415
        return sonne
    except Exception:                                      # noqa: BLE001
        return None


def _bbox_bauwerk():
    """Die Hüllbox der **gebauten Substanz** — Meshes, deren Name kein Gelände nennt.

    **Der Anlass ist ein Owner-Einwand** (`auf-vis-20260825-15`, Posten 1): Die Prüfung,
    ob die Geometrie überhaupt etwas hergibt, lief bisher **nach** der Diffusion. Sie
    kann davor laufen — es fehlte nur diese eine Zahl im Bericht.

    Der IFC-Runner führt seit dem 24.08. dieselbe Zahl (``bbox_bauwerk`` aus
    ``IfcSite``-Filterung). Hier ist die Lage schlechter: Nach GLB-Export und Import
    steht kein IFC-Typ mehr zur Verfügung, nur noch der **Objektname**. Entschieden wird
    darum mit :func:`aiimaging.maske.ist_gelaende` — derselben Regel, mit der später die
    Maske gebaut wird. Eine Szene, in der Gelände und Bauwerk in **einem** Objekt
    stecken, ist damit nicht auflösbar; sie meldet das Bauwerk als das ganze Objekt und
    ist an der Hüllboxgrösse zu erkennen.

    Returns:
        ``(lo, hi, note)`` — ``lo``/``hi`` sind ``None``, wenn nichts feststellbar war;
        ``note`` sagt dann **warum**.

    .. note::
       **Kein Rückfall auf die Szenenbox.** Findet sich keine gebaute Substanz, kommt
       ``None`` zurück und nicht die Box von allem. Die Szenenbox stillschweigend als
       Bauwerksbox auszugeben hiesse, den Bruch zwischen Rahmung und Messung genau dort
       zuzudecken, wo er gemessen werden soll — und der Bericht sähe dann gesund aus.
    """
    maske = _maske_modul()
    if maske is None:
        return None, None, ("'aiimaging.maske' ist von diesem Blender aus nicht "
                            "erreichbar — die Gelaenderegel konnte NICHT angewendet "
                            "werden. Das ist etwas anderes als 'es gibt kein Gelaende'.")

    lo = [float("inf")] * 3
    hi = [float("-inf")] * 3
    n = 0
    gelaende = []
    for obj in bpy.data.objects:
        if obj.type != "MESH":
            continue
        if maske.ist_gelaende(obj.name):
            gelaende.append(obj.name)
            continue
        n += 1
        for ecke in obj.bound_box:
            welt = obj.matrix_world @ __import__("mathutils").Vector(ecke)
            for i in range(3):
                lo[i] = min(lo[i], welt[i])
                hi[i] = max(hi[i], welt[i])

    if n == 0:
        return None, None, (
            f"Kein einziges Mesh-Objekt blieb nach der Gelaenderegel uebrig "
            f"({len(gelaende)} als Gelaende erkannt). Entweder besteht die Szene nur aus "
            f"Gelaende — dann ist der Auftrag ohne Bauwerk —, oder die Namen tragen die "
            f"Unterscheidung nicht. Es wird NICHT auf die Szenenbox zurueckgefallen.")
    if not gelaende:
        return lo, hi, ("Kein Objekt wurde als Gelaende erkannt; die Bauwerksbox ist "
                        "hier gleich der Szenenbox. Das ist ein gueltiges Ergebnis und "
                        "kein Rueckfall — aber ein Bruch zwischen Rahmung und Messung "
                        "ist damit auch nicht feststellbar.")
    return lo, hi, ""


def _kamera_setzen(lo, hi, a=None):
    """Die Kamera stellen — auf drei Wegen, und der Bericht sagt, welcher gegriffen hat.

    1. **``--auge`` und ``--blick-auf``** — der Aufrufer hat gerechnet, hier wird nur
       gestellt. Das ist der saubere Weg: Die Rechnung liegt dann diesseits der
       Prozessgrenze und ist ohne Blender prüfbar.
    2. **``--kamera <kürzel>``** — der Standort wird aus der **hier gemessenen** Hüllbox
       abgeleitet (`aiimaging.kameras`). Das ist der sichere Weg, weil er keine Annahme
       über Bezugssysteme macht: Die Zahlen stammen aus derselben Szene, in der gerendert
       wird. Ein Aufrufer, der die Hüllbox aus dem IFC kennt, kennt sie in *seinem*
       Achsensystem — und ob das nach Export, Import und einer möglichen Z-up-Drehung noch
       dasselbe ist, gehört gemessen und nicht angenommen.
    3. **Rückfall** — diagonal von vorn-oben, wie bis zum 18.08.2026 als einziger Weg.
       Nicht komponiert, nur brauchbar. Er greift ohne Angabe und wenn `aiimaging` von
       hier aus nicht erreichbar ist; **beides steht dann im Bericht**.

    Returns:
        ``(kamera, mitte, spanne, herkunft)`` — ``herkunft`` ist der Block, der in den
        Bericht wandert. Eine Ausgabe soll sagen, wie sie entstanden ist.
    """
    import mathutils

    mitte = mathutils.Vector([(lo[i] + hi[i]) / 2.0 for i in range(3)])
    spanne = max(hi[i] - lo[i] for i in range(3)) or 1.0
    # `None` heisst: nicht angefasst. Der Rückfall behält damit Blenders eigene
    # Brennweite — er ist die Bezugsgrösse aller bisher gemessenen Tiefenkarten, und wer
    # seine Optik ändert, verschiebt rückwirkend jede Zahl, die daran kalibriert wurde.
    brennweite = getattr(a, "brennweite", None)
    # Ausdrücklich gesetzt schlägt gerechnet. `None` heisst hier wie bei der Brennweite
    # „nicht angefasst", nicht „null" — der Unterschied entscheidet, ob der aus
    # `--kamera-modus shift` gerechnete Wert überhaupt zum Zug kommt.
    shift_y = getattr(a, "shift_y", None)

    auge = ziel = None
    herkunft = {"weg": "rueckfall", "kuerzel": None,
                "begruendung": "Keine Kamera angegeben — diagonal von vorn-oben, "
                               "brauchbar, aber nicht komponiert."}

    if a is not None and getattr(a, "auge", None):
        if not getattr(a, "blick_auf", None):
            raise RuntimeError("--auge ohne --blick-auf: Ein Standort ohne Blickziel "
                               "beschreibt keine Kamera.")
        auge = mathutils.Vector(_punkt_aus_text(a.auge, "--auge"))
        ziel = mathutils.Vector(_punkt_aus_text(a.blick_auf, "--blick-auf"))
        herkunft = {"weg": "vorgegeben", "kuerzel": getattr(a, "kamera", None),
                    "begruendung": "Standort und Blickziel kamen als Zahlen herein; "
                                   "hier wurde nur gestellt."}

    elif a is not None and getattr(a, "kamera", None):
        kameras = _kameras_modul()
        if kameras is None:
            herkunft["begruendung"] = (
                f"--kamera {a.kamera!r} war gesetzt, aber 'aiimaging.kameras' ist von "
                f"diesem Blender aus nicht erreichbar. Es wurde der Rückfall gestellt — "
                f"das Bild zeigt NICHT die angeforderte Richtung."
            )
        else:
            if brennweite is None:
                brennweite = kameras.BRENNWEITE_MM
            satz = kameras.kamerasatz(
                [list(lo), list(hi)], kuerzel=[a.kamera],
                brennweite_mm=brennweite,
                bias_grad=float(getattr(a, "bias", 35.0)),
                augenhoehe_m=float(getattr(a, "augenhoehe", 1.70)),
                deckungsgrad=_vorgabe(a, "deckungsgrad", kameras.DECKUNGSGRAD),
                gelaende_z=getattr(a, "gelaende_z", None),
                # Das TATSÄCHLICHE Seitenverhältnis dieses Laufs, nicht eine Annahme.
                # Bis zum 19.08.2026 stand hier fest 1.0 mit dem Kommentar „der Runner
                # rendert quadratisch" — was stimmte, aber `prompts.Stil.seitenverhaeltnis`
                # damit zu einer TOTEN KANTE machte: geschrieben, nie gelesen. Genau die
                # Fehlerart, gegen die dieses Projekt seit Phase 0 antritt.
                seitenverhaeltnis=a.aufloesung / (a.hoehe or a.aufloesung),
                # KEINE EIGENE VORGABE HIER — und das ist eine Berichtigung vom
                # 28.08.2026, die fuenf Tage zu spaet kommt.
                #
                # Bis heute stand hier `or kameras.MODUS_GEKIPPT`. Die Zeile ist am
                # 21.08. entstanden und war da richtig. Am 23.08. hat der Owner
                # entschieden, dass MODUS_SHIFT die Vorgabe ist — `auf-33` hatte das
                # Verhalten am Geraet in fuenf Faellen bestaetigt —, und `kameras.py`
                # wurde entsprechend geaendert. Der Runner nicht.
                #
                # Ergebnis: JEDER Lauf seither stand `gekippt`, mit shift_y 0.0, obwohl
                # die Bibliothek `shift` sagte. Gemessen am 28.08. an zwei Berichten.
                #
                # DARUM WIRD DER SCHLUESSEL JETZT WEGGELASSEN, wenn niemand ihn setzt:
                # Eine Vorgabe, die an zwei Stellen steht, geht beim naechsten Entscheid
                # wieder auseinander — und es faellt niemandem auf, weil beide Stellen
                # fuer sich schluessig aussehen.
                **({"modus": a.kamera_modus}
                   if getattr(a, "kamera_modus", None) else {}),
            )
            k = satz["kameras"][0]
            auge = mathutils.Vector(k["auge"])
            ziel = mathutils.Vector(k["blick_auf"])
            # Der gerechnete Shift wird gestellt — es sei denn, jemand hat von Hand
            # einen gesetzt. Ohne diese Zeile wäre `MODUS_SHIFT` eine tote Kante: Die
            # Kamera stünde waagrecht, ohne Shift, und das Bauwerk sässe zu hoch im Bild.
            if shift_y is None:
                shift_y = k["shift_y"]
            herkunft = {
                "weg": "abgeleitet", "kuerzel": k["kuerzel"],
                "azimut_grad": k["azimut_grad"],
                "modus": k["modus"],
                "neigung_grad": k["neigung_grad"],
                "shift_mm": k["shift_mm"],
                "massgebend": k["massgebend"],
                "durchlaeufe": k["durchlaeufe"],
                # Wenn der Eckentest nicht aufging, steht das hier — und nicht nur in
                # einem Bild, das jemand später schief findet.
                "vollstaendig": k["vollstaendig"],
                # Der Füllgrad sagt, was der Eckentest nicht sagt: ob das Bauwerk das
                # Bild auch AUSFÜLLT. Zu klein fällt keiner Prüfung auf, die nur nach
                # "passt es hinein" fragt.
                "fuellgrad": k["fuellgrad"],
                "abstand_m": k["abstand_m"],
                "seitenverhaeltnis": k["seitenverhaeltnis"],
                "gelaende_z": satz["gelaende_z"],
                # Woher der Nullpunkt kommt und wie hoch das Bauwerk ÜBER IHM ist.
                # Beides braucht die Kompositionsprüfung diesseits der Prozessgrenze —
                # ohne sie könnte sie nur raten, und eine ratende Prüfung urteilt zu mild.
                "gelaende_bezug": satz["gelaende_bezug"],
                "gebaeudehoehe_m": round(
                    satz["mitte"][2] + satz["masse_m"][2] / 2.0 - satz["gelaende_z"], 4),
                "warnungen": list(k["warnungen"]),
                "begruendung": k["begruendung"],
            }

    if auge is None:
        auge = mitte + mathutils.Vector((1.6, -2.0, 1.2)) * spanne
        ziel = mitte

    kam_daten = bpy.data.cameras.new("Kamera")
    if brennweite is not None:
        kam_daten.lens = brennweite

    # Der Sensorbezug wird AUSDRÜCKLICH gestellt, nicht Blender überlassen.
    #
    # `kameras.bildwinkel` setzt die Sensorbreite fest auf 36 mm und leitet die Höhe aus
    # dem Seitenverhältnis ab. Blenders Vorgabe `AUTO` bezieht `sensor_width` dagegen auf
    # die GRÖSSERE Bildkante. Für Quer- und Quadratformate ist das dasselbe — und alle
    # bisherigen Läufe waren quer oder quadratisch, weshalb es nie auffiel. Für ein
    # HOCHFORMAT ist es das nicht: Dort wären unser Bildwinkel und Blenders Bildwinkel
    # verschieden, still, und in beiden Richtungen falsch — die Tiefenkarte zeigte einen
    # anderen Ausschnitt als die Geometrie-QA erwartet. Der Hausstil ist quadratisch bis
    # hochformatig; der Fall steht also bevor.
    kam_daten.sensor_fit = "HORIZONTAL"
    _km = _kameras_modul()
    if _km is not None:
        kam_daten.sensor_width = _km.SENSOR_BREITE_MM
    if shift_y is not None:
        kam_daten.shift_y = float(shift_y)

    kam = bpy.data.objects.new("Kamera", kam_daten)
    bpy.context.scene.collection.objects.link(kam)
    kam.location = auge
    kam.rotation_mode = "QUATERNION"
    kam.rotation_quaternion = (ziel - auge).to_track_quat("-Z", "Y")
    bpy.context.scene.camera = kam

    # Die tatsächlich gestellte Brennweite, nicht die angeforderte: Beim Rückfall steht
    # hier Blenders eigene, und genau das soll ablesbar sein.
    herkunft["brennweite_mm"] = round(float(kam_daten.lens), 4)
    # Was WIRKLICH an der Kamera steht, nicht was bestellt war — dieselbe Regel wie bei
    # der Brennweite. Ohne diese Zeilen wäre ein nicht angekommener Shift von einem
    # angekommenen nicht zu unterscheiden.
    herkunft["shift_y"] = round(float(kam_daten.shift_y), 6)
    herkunft["sensor_fit"] = str(kam_daten.sensor_fit)
    herkunft["sensor_breite_mm"] = round(float(kam_daten.sensor_width), 4)
    herkunft["auge"] = [round(float(v), 4) for v in auge]
    herkunft["blick_auf"] = [round(float(v), 4) for v in ziel]

    # Die Felder, ohne die die Kompositionspruefung nicht urteilen kann. Auf dem
    # GERECHNETEN Weg stehen sie laengst; auf dem VORGEGEBENEN — und so schickt die
    # Oberflaeche ihre Kameras — fehlten sie, und `komposition.beurteilt` war dort IMMER
    # false (HomeStation, 24.08.2026). Das Regelwerk lief also genau dort nicht, wo Bilder
    # fuer Menschen entstehen.
    #
    # Die Zahlen fehlten nicht, sie wurden nur nie ausgerechnet: Standort, Blickziel und
    # Huellbox liegen alle vor. Gerechnet wird in der BIBLIOTHEK (Regel 4) — ist sie von
    # diesem Blender aus nicht erreichbar, bleibt das Feld leer und die Pruefung sagt
    # weiterhin ehrlich «nicht beurteilbar», statt aus geratenen Zahlen zu urteilen.
    if any(herkunft.get(f) is None for f in
           ("abstand_m", "gelaende_z", "gelaende_bezug", "gebaeudehoehe_m")):
        kameras = _kameras_modul()
        if kameras is not None and hasattr(kameras, "berichtsfelder_aus_stellung"):
            abgeleitet = kameras.berichtsfelder_aus_stellung(
                list(auge), list(ziel), [list(lo), list(hi)],
                brennweite_mm=float(kam_daten.lens),
                gelaende_z=getattr(a, "gelaende_z", None) if a is not None else None)
            for feld, wert in abgeleitet.items():
                herkunft.setdefault(feld, wert)
            herkunft["berichtsfelder"] = "aus der Stellung abgeleitet"
        else:
            herkunft["berichtsfelder"] = (
                "FEHLEN: 'aiimaging.kameras' ist von diesem Blender aus nicht erreichbar. "
                "Die Kompositionspruefung kann nicht urteilen — geraten wird nicht.")
    return kam, mitte, spanne, herkunft


# --------------------------------------------------------------------------------------
# Beleuchtung — schlicht, aber vorhanden
# --------------------------------------------------------------------------------------

def _welt_setzen(farbe, staerke: float) -> None:
    """Gleichmässiges Umgebungslicht als Welt-Hintergrund setzen.

    `read_factory_settings(use_empty=True)` löscht auch die Welt. Ohne sie rendert Cycles
    vor absolutem Schwarz und ohne jede Aufhellung — genau der Zustand, in dem das
    Beauty-Bild des Vorgängerstands unsichtbar blieb.
    """
    welt = bpy.data.worlds.new("Welt")
    hintergrund = _welt_hintergrund(welt)
    hintergrund.inputs["Color"].default_value = (*farbe, 1.0)
    hintergrund.inputs["Strength"].default_value = staerke
    bpy.context.scene.world = welt


#: Die Drehung, die dieser Runner bis zum 26.08.2026 unbedingt setzte.
#:
#: Sie steht hier als **Rückfall** — und nur als der. Ist ``aiimaging.sonne`` von diesem
#: Blender aus nicht erreichbar, wird sie gestellt, und der Bericht sagt es ausdrücklich.
#: Die Zahlen dahinter (40° über dem Horizont, 35° östlich von Süden) stehen in
#: ``aiimaging.sonne``; der alte Kommentar an dieser Stelle nannte **beide falsch**.
RUECKFALL_SONNE_EULER = (math.radians(50.0), 0.0, math.radians(35.0))


def _sonne_setzen(mitte, spanne: float, a=None):
    """Eine einzelne Sonne — **nach der Bestellung**, wenn eine vorliegt.

    Eine Sonne (Richtungslicht) statt einer Punktlichtquelle, weil ihre Wirkung nicht vom
    Abstand abhängt: Dieselben Winkel liefern bei einem Reihenhaus dieselbe Helligkeit
    wie bei einem Hochhaus. Damit bleibt das Bild über verschiedene Bauten hinweg
    vergleichbar, ohne dass irgendetwas an der Geometrie nachgeführt werden müsste.

    **Bis zum 26.08.2026 stand hier eine feste Drehung**, und der Sonnenstand einer
    Bestellung lief ins Leere: Ein Auftrag mit Abendstand wurde gerendert, als wäre er
    nicht gestellt worden — mit einem sauberen, gut belichteten, falschen Bild
    (`kosmo_szene.STEHENGEBLIEBEN`, Feld ``sonne``).

    Gerechnet wird in :mod:`aiimaging.sonne` und nicht hier (Regel 4). Ist das Modul von
    diesem Blender aus nicht erreichbar, greift :data:`RUECKFALL_SONNE_EULER`, und der
    Bericht sagt es — ein stiller Rückfall wäre genau der Fehler, gegen den dieser Runner
    an drei anderen Stellen bereits abgesichert ist.

    Returns:
        ``(sonne, befund)``. ``befund`` ist das Wörterbuch aus
        :func:`aiimaging.sonne.lage`, ergänzt um ``weg`` — oder ein Rückfallvermerk.
    """
    licht = bpy.data.lights.new("Sonne", type="SUN")
    licht.energy = 2.0
    licht.angle = math.radians(3.0)      # weiche Schattenkanten, nicht rasiermesserscharf
    objekt = bpy.data.objects.new("Sonne", licht)
    bpy.context.scene.collection.objects.link(objekt)
    # Position ist bei einer Sonne bedeutungslos, nur die Drehung zählt. Sie wird trotzdem
    # über der Szene abgelegt, damit ein späterer Blick in die .blend nicht verwirrt.
    objekt.location = (mitte[0], mitte[1], mitte[2] + spanne * 2.0)

    modul = _sonne_modul()
    if modul is None:
        objekt.rotation_euler = RUECKFALL_SONNE_EULER
        return objekt, {"weg": "rueckfall", "bestellt": (), "hoehe_grad": None,
                        "azimut_grad": None, "konvention": None,
                        "euler": list(RUECKFALL_SONNE_EULER),
                        "grund": ("'aiimaging.sonne' ist von diesem Blender aus nicht "
                                  "erreichbar. Es wurde die feste Drehung gestellt — ein "
                                  "bestellter Sonnenstand ist damit NICHT bedient.")}
    try:
        befund = modul.lage(getattr(a, "sonne_hoehe", None),
                            getattr(a, "sonne_azimut", None),
                            konvention=(getattr(a, "sonne_konvention", None)
                                        or modul.VORGABE_KONVENTION))
    except modul.SonnenError as fehler:
        # Ein unbrauchbarer Sonnenstand haelt den Lauf NICHT auf — aber er wird auch
        # nicht stillschweigend durch die Vorgabe ersetzt. Der Bericht traegt den Grund.
        objekt.rotation_euler = RUECKFALL_SONNE_EULER
        return objekt, {"weg": "rueckfall", "bestellt": (), "hoehe_grad": None,
                        "azimut_grad": None, "konvention": None,
                        "euler": list(RUECKFALL_SONNE_EULER),
                        "grund": f"Bestellter Sonnenstand unbrauchbar: {fehler}"}

    objekt.rotation_euler = befund["euler"]
    weg = "bestellt" if befund["bestellt"] else "vorgabe"
    return objekt, dict(befund, weg=weg, euler=list(befund["euler"]), grund="")


# --------------------------------------------------------------------------------------
# Material-ID — Farbverteilung über den Goldenen Winkel
# --------------------------------------------------------------------------------------

def _id_farbe_srgb(index: int):
    """Anzeigefarbe (sRGB, 0..1) für den Material-Index `index`.

    Der Farbton läuft über den Goldenen Winkel, Sättigung und Helligkeit sind fest.
    """
    h = (index * GOLDENER_WINKEL) % 1.0
    return colorsys.hsv_to_rgb(h, ID_SAETTIGUNG, ID_HELLIGKEIT)


def _srgb_zu_linear(c: float) -> float:
    """sRGB-Anzeigewert → linearer Renderwert (die Umkehrung dessen, was das PNG tut).

    Cycles rechnet linear, PNG speichert sRGB-kodiert. Würde die Anzeigefarbe direkt als
    Emissionsfarbe gesetzt, käme im PNG die zweimal kodierte Farbe an. Über diesen Schritt
    steht am Ende **exakt** die Palette in der Datei, die `_id_farbe_srgb` beschreibt — die
    QA kann später Bildfarbe und Report-Tabelle Byte für Byte vergleichen.
    """
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _emissions_material(name: str, farbe_srgb) -> "bpy.types.Material":
    """Ein Material, das genau eine Farbe abstrahlt und kein Licht empfängt."""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    baum = mat.node_tree
    baum.nodes.clear()
    emission = baum.nodes.new("ShaderNodeEmission")
    emission.inputs["Color"].default_value = (*(_srgb_zu_linear(k) for k in farbe_srgb), 1.0)
    emission.inputs["Strength"].default_value = 1.0
    ausgang = baum.nodes.new("ShaderNodeOutputMaterial")
    baum.links.new(emission.outputs["Emission"], ausgang.inputs["Surface"])
    return mat


def _material_id_zuweisen() -> tuple[list[dict], int]:
    """Jedem Material eine ID-Farbe geben und die Szene darauf umstellen.

    Returns:
        (Tabelle, Anzahl echter Materialien). Die Tabelle trägt pro ID-Eintrag Index,
        Name, Herkunft und Farbe — ohne sie liesse sich aus dem Bild nicht zurücklesen,
        welche Fläche welches Material war.

    Warum **nicht** `view_layer.material_override`
    ----------------------------------------------
    Der View-Layer-Override kennt genau *ein* Material für die ganze Ebene. Er kann das
    Beleuchtungsmodell austauschen, aber nicht pro Material unterscheiden — mit ihm wäre
    das Bild einfarbig und als Maske wertlos. Dieselbe Wirkung (nichts vom Original
    bleibt sichtbar, alles emittiert) entsteht hier stattdessen slotweise. Das ist
    strenger als ein Override: Ein Objekt mit mehreren Material-Slots behält seine
    Aufteilung, jede Teilfläche bekommt ihre eigene Farbe.

    Rückfall ohne Materialien
    -------------------------
    Trägt ein Mesh gar kein Material, bekommt es **objektweise** eine eigene ID. Sonst
    verschmölze eine materiallose Szene zu einer einzigen Fläche. Genau das ist der
    Normalfall der aktuellen Kette: `ifc_to_glb_runner.py` überträgt nur Geometrie, keine
    IfcMaterial-Zuordnung — die glb kommt ohne Materialien in Blender an. Die Herkunft
    steht deshalb in jedem Eintrag (`quelle`), damit niemand eine Objekt-Maske für eine
    Material-Maske hält.
    """
    tabelle: list[dict] = []
    nach_material: dict[str, int] = {}
    n_echte_materialien = len(bpy.data.materials)

    def eintragen(name: str, quelle: str) -> "bpy.types.Material":
        index = len(tabelle)
        farbe = _id_farbe_srgb(index)
        mat = _emissions_material(f"MATID_{index:03d}_{name}", farbe)
        tabelle.append({
            "index": index,
            "name": name,
            "quelle": quelle,
            "farbe_srgb": [round(k, 6) for k in farbe],
            "farbe_srgb_8bit": [int(round(k * 255.0)) for k in farbe],
        })
        return mat

    # Nach Namen sortiert, damit zwei Läufe dieselben Indizes und damit dieselben Farben
    # vergeben. Ohne feste Reihenfolge wäre die Maske nicht reproduzierbar.
    meshes = sorted((o for o in bpy.data.objects if o.type == "MESH"), key=lambda o: o.name)
    for obj in meshes:
        belegt = [s for s in obj.material_slots if s.material is not None]
        if not belegt:
            obj.data.materials.clear()
            obj.data.materials.append(eintragen(obj.name, "objekt"))
            continue
        for slot in obj.material_slots:
            if slot.material is None:
                continue
            name = slot.material.name
            if name not in nach_material:
                nach_material[name] = len(tabelle)
                slot.material = eintragen(name, "material")
            else:
                slot.material = bpy.data.materials[
                    f"MATID_{nach_material[name]:03d}_{name}"
                ]

    return tabelle, n_echte_materialien


# --------------------------------------------------------------------------------------
# Tiefe
# --------------------------------------------------------------------------------------
# Verdeckungstest — der Strahlenschuss, den `kameras.ziehe_bis_frei` hereingereicht bekommt
# --------------------------------------------------------------------------------------
#
# `aiimaging.kameras.ziehe_bis_frei` rechnet die Schrittlogik — 12 % der Reststrecke,
# Untergrenze, Stopp am Hüllbox-Rand — und lässt sich `_sicht_frei(auge, blick_auf)`
# hereinreichen. Diesseits gibt es die Antwort nicht: Ob etwas im Weg steht, weiss nur
# die Szene, und die lebt in Blender. Hier steht sie.
#
# **Für Innenräume ist das keine Kür.** Eine Kamera im Raum kann in einer Wand stehen oder
# durch sie hindurchschauen; `raumkamera.py` prüft nur die Lage im Raumumriss und sagt
# ausdrücklich, dass das notwendig und nicht hinreichend ist. Das hier ist die andere
# Hälfte.

#: Wie nah ein Treffer am Blickziel liegen darf, um noch als „das Ziel selbst" zu gelten.
#:
#: **Ohne diese Toleranz meldete der Test IMMER eine Verdeckung.** Das Blickziel liegt in
#: aller Regel *auf* einer Oberfläche — bei der frontalen Innenaufnahme auf der Zielwand,
#: aussen auf dem Bauwerk. Ein Strahl dorthin trifft also etwas, und zwar genau das, was
#: er treffen soll. Verdeckt ist er erst, wenn er **vorher** auf etwas anderes trifft.
#:
#: 5 cm sind eine Setzung: gross genug für Rundungen und für ein Ziel, das ein paar
#: Millimeter in der Wand liegt, klein genug, dass ein davorstehendes Möbel auffällt.
ZIELTOLERANZ_M = 0.05


def _sicht_frei(auge, blick_auf, *, toleranz_m: float = ZIELTOLERANZ_M) -> dict:
    """Steht zwischen Kamera und Blickziel etwas im Weg?

    Args:
        auge, blick_auf: Weltkoordinaten als Dreiergruppen.

    Returns:
        ``{frei, getroffen, abstand_ziel_m, abstand_treffer_m, objekt, grund}``.
        ``frei`` ist ``None``, wenn sich die Frage nicht stellen lässt — Auge und Ziel
        fallen zusammen. Das ist **nicht gemessen** und nicht „frei".

    **Die Semantik ist die Stelle, an der man sich vertut.** Naiv gefragt — *„trifft der
    Strahl etwas?"* — lautet die Antwort praktisch immer ja, denn das Blickziel liegt auf
    einer Oberfläche. Gefragt ist stattdessen: **Trifft er etwas, das NÄHER liegt als das
    Ziel?** Alles andere ist das Ziel selbst.

    Es wird **nichts abgebrochen und nichts korrigiert.** Diese Funktion beantwortet eine
    Frage; was ein „nein" kostet, weiss die Schrittlogik diesseits der Prozessgrenze.
    """
    import mathutils

    a = mathutils.Vector(auge)
    z = mathutils.Vector(blick_auf)
    richtung = z - a
    weite = richtung.length
    if weite <= 1e-9:
        return {"frei": None, "getroffen": None, "abstand_ziel_m": 0.0,
                "abstand_treffer_m": None, "objekt": None,
                "grund": ("Auge und Blickziel fallen zusammen — es gibt keine Sichtlinie, "
                          "auf der etwas stehen könnte. NICHT GEMESSEN.")}
    richtung.normalize()

    szene = bpy.context.scene
    tiefe = bpy.context.evaluated_depsgraph_get()
    # Ein Hauch Versatz, damit der Strahl nicht auf der Fläche startet, auf der die
    # Kamera womöglich sitzt — sonst trifft er beim Start sich selbst.
    start = a + richtung * 1e-4
    treffer, _ort, _normale, _index, objekt, _matrix = szene.ray_cast(
        tiefe, start, richtung, distance=weite + toleranz_m)

    if not treffer:
        # Nichts getroffen, auch das Ziel nicht — die Sicht ist frei, aber am Ziel steht
        # nichts. Das ist ein anderer Befund als „frei mit Ziel" und wird als solcher
        # gemeldet.
        return {"frei": True, "getroffen": False, "abstand_ziel_m": weite,
                "abstand_treffer_m": None, "objekt": None,
                "grund": ("Nichts auf der Sichtlinie — auch am Blickziel nicht. Die Sicht "
                          "ist frei; ob dort etwas STEHEN sollte, sagt dieser Test nicht.")}

    abstand = (_ort - a).length
    frei = abstand >= weite - toleranz_m
    return {
        "frei": frei, "getroffen": True, "abstand_ziel_m": round(weite, 6),
        "abstand_treffer_m": round(abstand, 6),
        "objekt": getattr(objekt, "name", None),
        "grund": ("" if frei else
                  f"Verdeckt: {getattr(objekt, 'name', '?')!r} steht {weite - abstand:.3f} m "
                  f"vor dem Blickziel."),
    }


# --------------------------------------------------------------------------------------

def _kompositor_baum(szene):
    """Den Kompositor-Knotenbaum holen — versionsfest über Blender 4.x und 5.x.

    **Belegt auf echter Hardware (2026-08-18, HomeStation, Auftrag `auf-20260818-01`):**
    Blender 5.0 hat `Scene.node_tree` entfernt. Der Kompositor ist dort ein eigener
    Datenblock und hängt unter `Scene.compositing_node_group`; `use_nodes` ist abgekündigt.
    Auf 4.2 LTS — wogegen dieser Runner ursprünglich gebaut und geprüft wurde — gilt
    weiterhin der alte Weg.

    Die Weiche prüft die **Fähigkeit**, nicht die Versionsnummer: `hasattr` bleibt richtig,
    auch wenn Blender die Umstellung in einer anderen Fassung nachzieht als angenommen.
    """
    if hasattr(szene, "compositing_node_group"):          # Blender 5.x
        baum = szene.compositing_node_group
        if baum is None:
            baum = bpy.data.node_groups.new("Kompositor", "CompositorNodeTree")
            szene.compositing_node_group = baum
        return baum
    szene.use_nodes = True                                # Blender <= 4.x
    return szene.node_tree


def _kompositor_abschalten(szene) -> None:
    """Den Kompositor für den Material-ID-Durchgang stilllegen — ebenfalls versionsfest."""
    if hasattr(szene, "compositing_node_group"):
        szene.compositing_node_group = None
    else:
        szene.use_nodes = False


def _welt_hintergrund(welt):
    """Den Hintergrund-Knoten einer Welt holen. `World.use_nodes` ist ab 5.0 abgekündigt."""
    if not getattr(welt, "use_nodes", False) and hasattr(welt, "use_nodes"):
        try:
            welt.use_nodes = True
        except Exception:                                 # ab Blender 6.0 entfernt
            pass
    return welt.node_tree.nodes["Background"]



def _exr_kanalnamen(pfad) -> list[str]:
    """Die Kanalnamen einer EXR aus ihrem Kopf lesen — ohne Fremdbibliothek.

    Reine Diagnose fuer den Report: `aiimaging.bildlesen` sucht den Tiefenkanal nach
    Namen, und Multilayer-EXR benennt ihn anders als eine einkanalige Datei. Die Namen
    gehoeren darum in den Report — sonst kostet jede Formataenderung einen weiteren
    Rundlauf zur HomeStation.
    """
    try:
        roh = Path(pfad).read_bytes()
        i = roh.index(b"chlist", roh.index(b"channels")) + len(b"chlist") + 1 + 4
        namen = []
        while i < len(roh) and roh[i] != 0 and len(namen) < 64:
            ende = roh.index(b"\x00", i)
            namen.append(roh[i:ende].decode("utf-8", "replace"))
            i = ende + 1 + 16
        return namen
    except Exception as e:                                # noqa: BLE001 — reine Diagnose
        return [f"<nicht lesbar: {type(e).__name__}>"]


def _api_befund(knoten) -> str:
    """Die tatsaechlich vorhandene API eines Knotens als Text.

    Wird nur im Fehlerfall gerufen. Der Grund: Ein Rundlauf zur HomeStation kostet den
    Owner einen Handgriff, also soll ein Fehlschlag mehr zurueckbringen als einen
    Traceback. Blender 5.x hat den File-Output-Knoten mehrfach umgebaut
    (`base_path` -> `directory`/`file_name`, `file_slots` -> `file_output_items`), und
    Raten hat hier schon zwei Rundlaeufe gekostet.
    """
    felder = sorted(a for a in dir(knoten) if not a.startswith("_"))
    zeilen = [f"API-Befund fuer {type(knoten).__name__}:", f"  Attribute: {', '.join(felder)}"]
    for name in ("file_slots", "file_output_items", "layer_slots"):
        s = getattr(knoten, name, None)
        if s is not None:
            zeilen.append(f"  {name}: {type(s).__name__}, "
                          f"Methoden {sorted(m for m in dir(s) if not m.startswith('_'))}")
    try:
        zeilen.append(f"  Eingaenge: {[e.name for e in knoten.inputs]}")
    except Exception:
        pass
    zeilen.append(f"  Blender: {bpy.app.version_string}")
    return "\n".join(zeilen)


def _compositor_auf_tiefe(out_dir: Path) -> str:
    """View-Layer-Z-Pass über den Compositor als 32-Bit-EXR ausgeben.

    Der Umweg über den Compositor ist der Grund, warum hier volles Blender nötig ist und
    Cycles allein nicht genügt: `use_pass_z` liefert die Tiefe erst über einen
    Node-Graph als Datei mit echten Meterwerten.
    """
    szene = bpy.context.scene
    szene.view_layers[0].use_pass_z = True
    baum = _kompositor_baum(szene)
    baum.nodes.clear()

    render_layer = baum.nodes.new("CompositorNodeRLayers")
    ausgabe = baum.nodes.new("CompositorNodeOutputFile")

    # Ausgabeort — Blender 5.0 hat `base_path` in `directory` + `file_name` getrennt.
    # Belegt auf der HomeStation (auf-20260818-02): AttributeError auf `base_path`.
    if hasattr(ausgabe, "base_path"):                     # <= 4.x
        ausgabe.base_path = str(out_dir)
    else:                                                 # 5.x
        ausgabe.directory = str(out_dir)
        ausgabe.file_name = "tiefe_"

    # Dateiformat. Blender 5.2 laesst am File-Output-Knoten nur noch OPEN_EXR_MULTILAYER
    # zu, 4.2 dagegen das einkanalige OPEN_EXR — und das ist uns lieber, weil
    # `aiimaging.bildlesen` es bitgenau selbst liest.
    #
    # Zwei Anlaeufe sind hier gescheitert, beide lehrreich:
    #   auf-20260818-03: "OPEN_EXR" fest zugewiesen -> wirft auf 5.2.
    #   auf-20260818-04: die erlaubten Werte ueber `bl_rna...enum_items` erfragt -> die
    #     Liste ist STATISCH und nennt alle 16 Formate, auch die nicht zuweisbaren. Am
    #     Knoten zu fragen war also genauso unzuverlaessig wie zu raten (Diagnose des
    #     lokalen Workers auf der HomeStation).
    #
    # Was bleibt: es versuchen und den Fehlschlag hinnehmen. Ein frischer Knoten steht in
    # 5.2 bereits auf OPEN_EXR_MULTILAYER, das Ergebnis ist also brauchbar. Gefangen wird
    # `TypeError` — am Geraet gemessen, nicht angenommen; `ValueError` griffe daneben.
    try:
        ausgabe.format.file_format = "OPEN_EXR"
    except TypeError:
        pass                                              # 5.x: bleibt bei MULTILAYER
    ausgabe.format.color_depth = "32"
    # OPEN_EXR kennt in dieser Einstellung nur RGB/RGBA. Blender schreibt die Tiefe aber
    # als EINEN Kanal namens "V" in die Datei — nachgemessen 2026-08-18 am erzeugten
    # Header. Der frühere Kommentar behauptete hier drei Kanaele und einen "R"-Kanal; das
    # war falsch und stand seit Phase 1 so da. Wer die EXR von aussen liest, muss nach "V"
    # suchen, nicht nach "R" (siehe `aiimaging.bildlesen`, das eine Vorrangliste benutzt).
    ausgabe.format.color_mode = "RGB"

    # Eingangsslot — `file_slots` heisst ab 5.0 `file_output_items`, und der Name eines
    # Eintrags steht dort unter `.name` statt unter `.path`. Weil die genaue Signatur von
    # `new()` sich zwischen den Fassungen unterscheidet, wird sie NICHT geraten: Es werden
    # mehrere bekannte Aufrufformen versucht, und schlaegt alles fehl, meldet der Runner
    # die tatsaechlich vorhandene API zurueck (siehe `_api_befund`) — ein Fehlschlag soll
    # Fakten liefern, nicht nur einen Traceback.
    slot_name = "tiefe_"
    sammlung = getattr(ausgabe, "file_slots", None)
    if sammlung is None:
        sammlung = getattr(ausgabe, "file_output_items", None)
    if sammlung is None:
        raise RuntimeError("Weder file_slots noch file_output_items: " + _api_befund(ausgabe))

    try:
        sammlung.clear()
    except Exception:                                     # manche Fassungen kennen kein clear()
        pass

    # Die Reihenfolge IST die Weiche — keine Versionsabfrage. Auf 4.2 greift die erste
    # Form (`file_slots.new(name)`), die Schleife bricht dort ab, der 4.2-Pfad bleibt
    # unberuehrt. Erst wenn sie scheitert, kommen die getypten Formen von 5.x.
    #
    # HomeStation-Befund 18.08. (Blender 5.2.0 LTS, am Geraet gemessen):
    #   Signatur: `NodeCompositorFileOutputItems.new(socket_type, name)`
    #   gueltig:      RGBA, VECTOR, FLOAT
    #   NICHT gueltig: COLOR und VALUE (TypeError), IMAGE (RuntimeError)
    # Der bisherige Kandidat "COLOR" war also ausgerechnet einer der ungueltigen —
    # darum scheiterten alle vier Versuche und der Slot entstand nie.
    #
    # FLOAT steht vor RGBA, weil eine Tiefenkarte EIN Wert je Pixel ist und kein
    # Farbwert; der Depth-Ausgang der Render-Layer ist ein Value-Socket. RGBA bleibt
    # als Rueckfall, falls eine Fassung FLOAT nicht fuehrt.
    letzter = None
    for versuch in (lambda: sammlung.new(slot_name),
                    lambda: sammlung.new(name=slot_name),
                    lambda: sammlung.new("FLOAT", slot_name),
                    lambda: sammlung.new("RGBA", slot_name),
                    lambda: sammlung.new("COLOR", slot_name),
                    lambda: sammlung.new()):
        try:
            versuch()
            letzter = None
            break
        except Exception as e:                            # noqa: BLE001 — naechste Form probieren
            letzter = e
    if letzter is not None:
        raise RuntimeError(f"Eingangsslot nicht anlegbar ({letzter}). {_api_befund(ausgabe)}")

    # Der Eingang heisst je nach Fassung wie der Slot oder schlicht "Image".
    ziel = ausgabe.inputs.get(slot_name) or (ausgabe.inputs[0] if len(ausgabe.inputs) else None)
    if ziel is None:
        raise RuntimeError("Kein Eingang am File-Output-Knoten. " + _api_befund(ausgabe))
    baum.links.new(render_layer.outputs["Depth"], ziel)
    return ausgabe.format.file_format


# --------------------------------------------------------------------------------------
# Ablauf
# --------------------------------------------------------------------------------------

def _renderparameter_setzen(a) -> None:
    """Engine, Sampling und Farbverwaltung — für beide Durchgänge gemeinsam."""
    szene = bpy.context.scene
    szene.render.engine = "CYCLES"
    szene.cycles.samples = a.samples
    szene.cycles.device = "CPU"                          # in dieser Umgebung gibt es keine GPU
    szene.render.resolution_x = a.aufloesung
    szene.render.resolution_y = a.hoehe or a.aufloesung
    szene.render.resolution_percentage = 100
    # Standard statt AgX: AgX ist ein Filmlook mit weicher Kompression der Lichter. Für ein
    # Bild, das gleich wieder maschinell ausgewertet wird, ist eine nachvollziehbare
    # Zuordnung von Renderwert zu Bildwert wichtiger als ein schönes Rollover.
    szene.view_settings.view_transform = "Standard"
    szene.view_settings.look = "None"


def _frisch(pfad: Path, seit: float) -> bool:
    """Wurde diese Datei in DIESEM Lauf geschrieben?

    Blosse Existenz genügt nicht: `out_dir` wird üblicherweise wiederverwendet, und eine
    liegengebliebene Datei aus einem früheren Lauf sähe genauso aus wie ein Erfolg. Die
    Erfolgsmeldung hinge dann an fremden Bytes.
    """
    return pfad.exists() and pfad.stat().st_mtime >= seit


def main() -> int:
    a = _argumente()
    out_dir = Path(a.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    beginn = time.time() - 1.0                           # 1 s Luft für grobe mtime-Auflösung

    herzschlag = None
    if getattr(a, "herzschlag_s", None):
        herzschlag = _herzschlag_starten(out_dir / HERZSCHLAG_DATEI, a.herzschlag_s)

    _szene_leeren()
    bpy.ops.import_scene.gltf(filepath=a.glb)

    if getattr(a, "rotiere_z_up", False):
        # Quelle war Z-up (glTF verlangt Y-up). Ohne diese Drehung läge der Bau auf der
        # Seite — und Tiefenkarte, Kamera und Geometrie-QA wären still verdreht.
        #
        # DAS VORZEICHEN IST −90° UND NICHT +90°, und das ist seit dem 01.09.2026
        # GEMESSEN statt hergeleitet (Sitzung 16 führte diesen Fall ausdrücklich als
        # NICHT GEMESSEN). Blenders glTF-Import rechnet selbst schon Y-up → Z-up, das
        # ist R_x(+90): Datei (fx,fy,fz) → Blender (fx,−fz,fy). Steht in der Datei
        # bereits Z-up, muss diese Drehung RÜCKGÄNGIG gemacht werden, nicht wiederholt.
        #
        # An einer echten Z-up-glb (103,84 × 57,15 × 27,10 m, Fuss bei z = −0,437 m)
        # dreimal im selben Blender-Lauf gemessen:
        #
        #   ohne Drehung   z 61,512 … 118,662   Masse 103,84 × 27,10 × 57,15   liegt auf der Seite
        #   mit +90°       z −26,664 …   0,437  Masse 103,84 × 57,15 × 27,10   STEHT AUF DEM KOPF
        #   mit −90°       z  −0,437 …  26,664  Masse 103,84 × 57,15 × 27,10   richtig
        #
        # Die Masse allein entlarven +90° nicht: R_x(180) lässt jede Kantenlänge gleich
        # und kippt nur die Vorzeichen. Nur die Lage der Box verrät es — das Dach lag
        # 26,7 m UNTER dem Nullpunkt. Ein Bericht, der bloss `bbox_size_m` zeigt, hätte
        # den Fehler nie gemeldet.
        import mathutils
        dreh = mathutils.Matrix.Rotation(math.radians(-90.0), 4, "X")
        for obj in bpy.data.objects:
            if obj.parent is None:
                obj.matrix_world = dreh @ obj.matrix_world

    lo, hi = _bbox_aller_meshes()
    # Und daneben die Box der gebauten Substanz. Sie ENTSCHEIDET hier nichts — der Runner
    # rahmt weiterhin, was ihm gesagt wird. Sie wird berichtet, damit diesseits der
    # Prozessgrenze VOR dem Bildlauf entscheidbar ist, ob die Rahmung ein Urteil zulaesst.
    bau_lo, bau_hi, bau_note = _bbox_bauwerk()
    # Die Kamera darf sich auf eine ANDERE Hüllbox beziehen als der Bericht: Der Bericht
    # beschreibt, was dasteht; die Kamera rahmt, was gezeigt werden soll.
    kam_lo, kam_hi = (_huellbox_aus_text(a.kamera_huellbox)
                      if getattr(a, "kamera_huellbox", None) else (lo, hi))
    _, _, _, kamera_herkunft = _kamera_setzen(kam_lo, kam_hi, a)
    mitte = [(lo[i] + hi[i]) / 2.0 for i in range(3)]
    spanne = max(hi[i] - lo[i] for i in range(3)) or 1.0

    _renderparameter_setzen(a)
    szene = bpy.context.scene

    # ── Durchgang 1: Beauty + Tiefe ────────────────────────────────────────────────────
    # Umgebungsstärke 0.25 zu Sonnenstärke 2.0: gemessen, nicht geschätzt. Mit 1.0/3.0
    # lag das Bild im Mittel bei 0.83 von 1.0 — durchgehend ausgebrannt, die Fassaden
    # ohne Zeichnung. Die Schattenseite soll dunkel bleiben, ohne zuzulaufen.
    _welt_setzen((0.55, 0.60, 0.68), 0.25)               # kühles, gleichmässiges Umgebungslicht
    _, sonne_befund = _sonne_setzen(mitte, spanne, a)
    szene.cycles.use_denoising = True                    # 8 Samples auf CPU rauschen sichtbar
    szene.render.image_settings.file_format = "PNG"
    szene.render.image_settings.color_mode = "RGBA"
    szene.render.image_settings.color_depth = "8"
    beauty_png = out_dir / "beauty_.png"
    szene.render.filepath = str(out_dir / "beauty_")

    exr_format = "unbekannt"
    try:
        exr_format = _compositor_auf_tiefe(out_dir)
    except Exception as e:
        # Jeder Fehler im Kompositor-Aufbau soll die tatsaechliche API mitliefern.
        # Blender 5.x hat diesen Bereich mehrfach umgebaut, und jeder Rundlauf zur
        # HomeStation kostet den Owner einen Handgriff — ein Fehlschlag muss darum mehr
        # zurueckbringen als die blosse Meldung, dass etwas fehlt.
        befund = ""
        try:
            szene = bpy.context.scene
            baum = _kompositor_baum(szene)
            knoten = baum.nodes.new("CompositorNodeOutputFile")
            befund = "\n" + _api_befund(knoten)
        except Exception as e2:
            befund = f"\n(API-Befund nicht erhebbar: {e2})"
        raise RuntimeError(f"Kompositor-Aufbau gescheitert: {e}{befund}") from e
    bpy.ops.render.render(write_still=not a.ohne_beauty)

    exr_kandidaten = [p for p in sorted(out_dir.glob("tiefe_*.exr")) if _frisch(p, beginn)]
    exr = exr_kandidaten[0] if exr_kandidaten else None

    # ── Durchgang 2: Material-ID ──────────────────────────────────────────────────────
    tabelle: list[dict] = []
    n_materialien = len(bpy.data.materials)
    material_id_png = out_dir / "material_id.png"
    if not a.ohne_material_id:
        tabelle, n_materialien = _material_id_zuweisen()
        # Der Compositor darf hier nicht mitlaufen: Er schriebe die (unveränderte) Tiefe
        # ein zweites Mal über dieselbe Datei.
        _kompositor_abschalten(szene)
        _welt_setzen((0.0, 0.0, 0.0), 0.0)               # schwarzer Grund, Farbwert 0 = "nichts"
        # Ein Sample, kein Denoiser, keine Bounces: Jedes Pixel trägt genau die gesetzte
        # Farbe. Mehr Samples würden Kanten mischen und neue, falsche IDs erfinden.
        szene.cycles.samples = 1
        szene.cycles.use_denoising = False
        szene.cycles.max_bounces = 0
        szene.cycles.transparent_max_bounces = 0
        # Rekonstruktionsfilter aus: Bei Breite 1.5 darf ein Sample in ein Nachbarpixel
        # fallen und trägt dort eine fremde ID ein. Bei 0.0 bleibt jedes Sample in seinem
        # Pixel, die Kanten sitzen hart.
        szene.render.filter_size = 0.0
        # Dithering aus. Es streut vor der 8-Bit-Quantisierung Rauschen ein — für ein
        # Foto richtig (es verhindert Banding), für eine Kennung falsch: Gemessen wurden
        # damit 19 statt 5 Farben, weil jede ID um ±1 zerfaserte und selbst der schwarze
        # Grund zwischen 0 und 1 sprang.
        szene.render.dither_intensity = 0.0
        szene.render.filepath = str(out_dir / "material_id")
        bpy.ops.render.render(write_still=True)

    # ── Die Normalisierung passiert NICHT mehr hier ───────────────────────────────────
    # `tiefe_norm.png` entsteht seit dem 18.08.2026 auf der Produktseite
    # (`aiimaging.bildschreiben.tiefe_exr_zu_png`, aufgerufen von
    # `seams.glb_zu_multipass`). Begründung im Modul-Docstring: Blender 5.2 kann die
    # Multilayer-EXR, die es dort schreiben muss, selbst nicht wieder einlesen.
    #
    # Die Felder `depth_png` und `depth_normalisierung` bleiben im Report stehen und
    # bleiben `None`. Sie zu streichen wäre ein stiller Bruch für jeden Leser des
    # Reports; `None` ist eine Aussage, ein fehlender Schlüssel ist keine.
    fehler = None if exr is not None else "Compositor schrieb keine EXR"

    erwartet = {
        "depth_exr": exr if exr is not None else None,
        "beauty_png": beauty_png if not a.ohne_beauty else None,
        "material_id_png": material_id_png if not a.ohne_material_id else None,
    }
    fehlend = [name for name, pfad in erwartet.items()
               if pfad is not None and not _frisch(Path(pfad), beginn)]
    if fehlend and fehler is None:
        fehler = "nicht geschrieben: " + ", ".join(sorted(fehlend))

    report = {
        # Bestandsfelder — Bedeutung unverändert, damit seams.py und die Tests tragen.
        "status": "ok" if fehler is None else "error",
        "depth_exr": str(exr) if exr is not None else None,
        # Woher die Kamera kam — vorgegeben, abgeleitet oder Rückfall. Ohne diese Angabe
        # ist einem Bild später nicht mehr anzusehen, ob es die angeforderte Ansicht
        # zeigt oder die Notlösung.
        "kamera": kamera_herkunft,
        "bbox": [lo, hi],
        "bbox_size_m": [hi[i] - lo[i] for i in range(3)],
        # Die zweite Huellbox — die der gebauten Substanz. Ohne sie ist der Bruch
        # zwischen Rahmung und Messung nicht feststellbar, und die Pruefung der
        # Geometrie kann nicht VOR dem Bildlauf stattfinden (Owner-Einwand,
        # auf-vis-20260825-15 Posten 1). `None` heisst NICHT FESTSTELLBAR, nie
        # "in Ordnung" — `bbox_bauwerk_note` sagt, woran es lag.
        "bbox_bauwerk": ([bau_lo, bau_hi] if bau_lo is not None else None),
        "bbox_bauwerk_note": bau_note,
        # Welcher Sonnenstand gestellt wurde, unter welcher Azimutkonvention, und ob er
        # BESTELLT war oder die Vorgabe ist. Bis zum 26.08.2026 lief der Sonnenstand
        # einer Bestellung ins Leere, und das Bild sah trotzdem richtig aus.
        "sonne": sonne_befund,
        # Mit welchem Deckungsgrad die Kamera gestellt wurde. **Die Zahl gehoert an die
        # Bedingung, unter der sie gemessen wurde** — und bis zum 26.08.2026 stand sie
        # nirgends im Bericht. Der Rahmungsriegel diesseits der Grenze rechnete darum mit
        # der Konstanten der Bibliothek und schrieb sie auch so ins Urteil, gleichgueltig
        # womit dieser Lauf wirklich gestellt worden war. Ein Vergleichslauf bei 0.55
        # gegen 0.70 (auf-20260825-41) haette ein Urteil bekommen, das ueber den anderen
        # Lauf spricht.
        "deckungsgrad": float(_vorgabe(a, "deckungsgrad", _kameras_modul().DECKUNGSGRAD)),
        "n_meshes": sum(1 for o in bpy.data.objects if o.type == "MESH"),
        "aufloesung": a.aufloesung,
        "hoehe": a.hoehe or a.aufloesung,
        "seitenverhaeltnis": a.aufloesung / (a.hoehe or a.aufloesung),
        "rotiert": bool(getattr(a, "rotiere_z_up", False)),
        "blender": bpy.app.version_string,
        "error": fehler,
        # Neu mit dem Multipass.
        "beauty_png": str(beauty_png) if _frisch(beauty_png, beginn) else None,
        "material_id_png": str(material_id_png) if _frisch(material_id_png, beginn) else None,
        # Bleibt None: Der Runner normalisiert nicht mehr. `seams.glb_zu_multipass`
        # trägt hier den Pfad nach, den es selbst geschrieben hat.
        "depth_png": None,
        "n_materialien": n_materialien,
        "material_id_tabelle": tabelle,
        "material_id_quelle": sorted({e["quelle"] for e in tabelle}) or None,
        "depth_normalisierung": None,           # siehe `depth_png`
        "samples": a.samples,
        # Diagnose fuer den externen Leser: Multilayer-EXR benennt Kanaele anders als eine
        # einkanalige Datei ("tiefe_.V" statt "V"), und `aiimaging.bildlesen` sucht nach
        # Namen. Ohne diese Angabe kostete jede Formataenderung einen weiteren Rundlauf.
        "depth_exr_kanaele": _exr_kanalnamen(exr) if exr is not None else [],
        "depth_exr_format": exr_format,
    }
    if herzschlag is not None:
        # Der Faden ist daemonisch und stürbe auch von selbst — aber ein Herzschlag, der
        # nach dem letzten Bild noch weiterschlägt, ist ein Lebenszeichen für einen
        # Zustand, den es nicht mehr gibt.
        _faden, stoppen = herzschlag
        stoppen.set()
        _faden.join(timeout=5.0)
        report["herzschlag"] = str(out_dir / HERZSCHLAG_DATEI)

    (out_dir / "blender-report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print("BLENDER_REPORT " + json.dumps(report, ensure_ascii=False))
    return 0 if fehler is None else 1


if __name__ == "__main__":
    sys.exit(main())
