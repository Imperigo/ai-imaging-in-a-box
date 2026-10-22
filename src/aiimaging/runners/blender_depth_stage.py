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
        [--rotiere-z-up] [--ohne-beauty] [--ohne-material-id] \
        [--kontext-ply <splat.ply> [--kontext-matrix=m0,...,m15]]
"""
from __future__ import annotations

import colorsys
import json
import math
import os
import re
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
    # Licht der Sonne (B161, 24.09.2026). `None` heisst nicht bestellt: Dann bleiben die
    # festen 2.0 und 3 Grad, und der Bericht sagt es.
    ap.add_argument("--sonne-staerke", type=float, default=None,
                    help="sun.energy; ohne Angabe 2.0")
    ap.add_argument("--sonne-kelvin", type=float, default=None,
                    help="Farbtemperatur; ohne Angabe weiss")
    ap.add_argument("--sonne-winkel", type=float, default=None,
                    help="Winkeldurchmesser in Grad (sun.angle); ohne Angabe 3.0")
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
                    help="'shift' oder 'gekippt'; ohne Angabe gilt die Vorgabe von "
                         "aiimaging.kameras (seit 23.08.2026 'shift'). Wirkt nur zusammen "
                         "mit --kamera: Der Modus geht in `kameras.kamerasatz`, und der "
                         "von dort gerechnete Shift wird gestellt. Ein ausdrücklich "
                         "gesetztes --shift-y schlägt ihn. Auf den anderen Wegen meldet "
                         "der Bericht ihn als wirkungslos (kamera_modus_wirkungslos).")
    ap.add_argument("--shift-y", dest="shift_y", type=float, default=None,
                    help="Objektiv-Shift nach oben, als Anteil der GRÖSSEREN Sensorkante "
                         "(Blenders Einheit). Gesetzt heisst: waagrechte Kamera, "
                         "senkrechte Kanten bleiben senkrecht. Gerechnet wird er in "
                         "`kameras.MODUS_SHIFT`; hier wird er nur gestellt.")
    # KEINE Vorgabe hier, sondern `None` — und das nicht nur wegen der einen Quelle
    # (siehe `_vorgabe`). Befund 23.09.2026: Mit `default=35.0` / `1.70` war eine
    # Bestellung von der Vorgabe nicht mehr zu unterscheiden, und der Bericht konnte
    # darum nicht sagen, ob auf dem Weg `vorgegeben` eine Augenhoehe BESTELLT und
    # uebergangen wurde. Die Zahlen gelten unveraendert: `kameras.BIAS_GRAD` und
    # `kameras.AUGENHOEHE_M` sind dieselben 35.0 und 1.70.
    ap.add_argument("--bias", type=float, default=None)
    ap.add_argument("--augenhoehe", type=float, default=None)
    # KEIN fester Vorgabewert hier. Am 23.08.2026 sind zwei abgeschriebene 28.0
    # aufgefallen, die beim Wechsel der Brennweite still auseinandergelaufen
    # waeren; dies ist dieselbe Stelle fuer den Deckungsgrad. None heisst: was
    # die Bibliothek sagt.
    ap.add_argument("--deckungsgrad", type=float, default=None)
    # FESTER ABSTAND (Knoten «Kamera», `cameras_auto.abstand {art: 'fest'}`, 20.10.2026): in
    # Metern waagrecht von der Mitte. Nur auf dem Weg «abgeleitet» (mit --kamera); der
    # Eckentest meldet dann nur und schiebt nicht nach (`kameras.kamerasatz`).
    ap.add_argument("--abstand-fest", dest="abstand_fest", type=float, default=None)
    ap.add_argument("--gelaende-z", type=float, default=None,
                    help="Geländehöhe im Weltsystem. Ohne Angabe die Unterkante der "
                         "Hüllbox — bei einem Untergeschoss stünde die Kamera sonst im Keller.")
    ap.add_argument("--kamera-huellbox", default=None,
                    help="Sechs Zahlen 'x0,y0,z0,x1,y1,z1' — die Hüllbox, auf die sich "
                         "die KAMERA bezieht. Ohne Angabe alle Meshes. Gebraucht, sobald "
                         "die Szene Gelände trägt: Ein Geländestück blaeht die Hüllbox "
                         "auf, die Kamera zieht sich zurück, und das Gebäude wird kleiner "
                         "statt grösser. Am 20.08.2026 gemessen — siehe _bbox_aller_meshes.")
    ap.add_argument("--kamera-ausschnitt", action="store_true",
                    help="Lange, flache Bauwerke als Ausschnitt zeigen (Entscheid 75), auch "
                         "ohne --kamera-huellbox: wenn das Bauwerk die Szene ist.")
    ap.add_argument("--herzschlag-s", type=float, default=None,
                    help="Alle so viele Sekunden ein Lebenszeichen nach "
                         "<out>/herzschlag.txt schreiben. Ohne Angabe: keines. Siehe "
                         "`_herzschlag_starten` — es ist ein LEBENSzeichen und kein "
                         "Fortschrittszeichen, und der Unterschied ist der ganze Punkt.")
    # DER KONTEXT (Owner-Entscheid 76, 08.10.2026): ein Splat als UMGEBUNG. Ohne Angabe
    # entsteht nichts davon — kein Objekt, kein Berichtsblock, keine Zusatzdatei —, und
    # jeder Lauf ohne Splat bleibt, was er war. Siehe `_kontext_laden`.
    ap.add_argument("--kontext-ply", dest="kontext_ply", default=None,
                    help="3DGS-PLY (Kugel-Notloesung) oder Netz-PLY mit Flaechen (aus der "
                         "Splat-Bruecke) als Umgebung: sichtbar in Beauty und Tiefe, NICHT "
                         "in Huellbox, Rahmung und Bauwerksmaske. Erkannt am PLY-Kopf")
    ap.add_argument("--kontext-matrix", dest="kontext_matrix", default=None,
                    help="16 Zahlen 'm0,...,m15', 4x4 ZEILENWEISE, Lage des Splats in der "
                         "glTF-Welt (Meter, Y oben). Ohne Angabe die Einheit. Siehe "
                         "aiimaging.kontext")
    # DIE STIMMUNG (Entscheide 107/110/113, 20.10.2026): ein Himmelsbild (HDRI, CC0, am
    # Heim-PC) als Welt. Ohne Angabe bleibt die feste Welt mit Sonne, Wort fuer Wort.
    ap.add_argument("--umgebung-hdr", dest="umgebung_hdr", default=None,
                    help="Himmelsbild (.hdr) als Welt: Environment Texture, Mapping (Drehung "
                         "um Z), Background. Keine Sonnenlampe, ausser eine Sonne ist "
                         "bestellt (--sonne-*). Der ID-Pass bleibt vor Schwarz.")
    ap.add_argument("--umgebung-staerke", dest="umgebung_staerke", type=float, default=None,
                    help="Staerke des Himmelsbilds (Background Strength), Vorgabe 1.0.")
    ap.add_argument("--umgebung-drehung", dest="umgebung_drehung", type=float, default=None,
                    help="Drehung des Himmelsbilds um die Hochachse, Grad. Ohne Angabe: "
                         "mit --umgebung-licht je Kamera so, dass die Sonne seitlich der "
                         "Blickachse steht (sonne_seitlich_grad), sonst 0.")
    # BELICHTUNG UND TOENUNG JE STIMMUNG (auf-20261020-292, B1/B3): Daten aus
    # `aiimaging.stimmung`. Nur mit --umgebung-hdr wirksam; dann rechnet das Schoenbild mit
    # der Tonwertkurve AgX (sonst Filmic), der ID-Pass weiter mit «Standard».
    ap.add_argument("--umgebung-belichtung", dest="umgebung_belichtung", type=float,
                    default=None,
                    help="Belichtung in Blendenstufen (view_settings.exposure), nur mit "
                         "Himmelsbild; Vorgabe 0.")
    ap.add_argument("--umgebung-toenung", dest="umgebung_toenung", default=None,
                    help="Toenung des Himmelslichts 'r,g,b' (linear, Helligkeit 1), nur mit "
                         "Himmelsbild.")
    # LICHT MIT SCHATTEN JE STIMMUNG (auf-20261020-293): die Daten aus
    # `stimmung.licht_der_stimmung` als JSON — Sonne ja/nein, Staerken, Winkel, Look,
    # Richtung und Abstand des Hintergrunds, Grau der Platte. Nur mit --umgebung-hdr wirksam;
    # ohne den Schalter rechnet die Stimmung wie vor 293 (keine Lampe, kein Grau).
    ap.add_argument("--umgebung-licht", dest="umgebung_licht", default=None,
                    help="Lichtdaten der Stimmung als JSON (aiimaging.stimmung."
                         "licht_der_stimmung): Sonnenlampe aus der Richtung der Sonne im "
                         "Himmelsbild, Fuelllicht, Look, Hintergrund mit Abstand, graue Platte.")
    ap.add_argument("--materialien", dest="materialien", default=None,
                    help="Materialwahl je Bauteil-Art (JSON aus abholer.materialwahl_ablegen): "
                         "Principled BSDF mit Box-Projektion, Rauheit, Relief (Bump aus der "
                         "Hoehe), Toenung. Nicht gewaehlte Arten behalten ihr Material, "
                         "Gelaende bleibt immer, wie es ist.")
    ap.add_argument("--umgebung-weiss", dest="umgebung_weiss", action="store_true",
                    help="Stimmung «weiss» (Entscheid 113): alle Oberflaechen ein diffuses "
                         "Weiss wie ein Gipsmodell, Rauheit hoch.")
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


def _deckungsgrad_befund(a, herkunft: dict) -> dict:
    """Die beiden Berichtsfelder zum Deckungsgrad — **so, wie er gewirkt hat.**

    **Befund 22.09.2026** (Anlass ``auf-20260922-137``: zwei Deckungsgrade, dieselbe
    Tiefenkarte, mit einer Attrappe von ``bpy`` am ``main`` nachgefahren): Gelesen wird
    der Deckungsgrad nur auf dem Weg ``abgeleitet`` — dort rechnet ``kameras.kamerasatz``
    mit ihm den Abstand. Mit ``--auge``/``--blick-auf`` (``vorgegeben``) und ohne Kamera
    (``rueckfall``) greift er nirgends. Der Bericht schrieb ihn trotzdem auf jedem Weg
    hinein, und wer ihn las, bekam eine Rahmung gemeldet, die nie gestellt wurde.

    Returns:
        ``{"deckungsgrad": ..., "deckungsgrad_wirkungslos": ...}``. Auf dem Weg
        ``abgeleitet`` die gerechnete Zahl und ``None`` (es gibt keinen Grund zu melden);
        sonst ``None`` — **nicht gerahmt**, weder mit der Vorgabe noch mit der Bestellung
        — und ein Satz, warum. Beide Felder stehen immer da.

    **Der Satz steht auch OHNE Bestellung — anders als bei** :func:`_kamerawerte_befund`
    (entschieden 23.09.2026, Runde 8, und mit Absicht nicht angeglichen). Der Grund ist
    ein Leser: ``abholer._rahmung_vor_dem_render`` liest ``deckungsgrad_wirkungslos``
    als Begründung für «nicht gerahmt», auch wenn niemand einen Deckungsgrad bestellt
    hat. Die Rahmung ist dort eine Rechengrundlage des Urteils (Bildbreite, Knie,
    Abbruch), nicht bloss eine Bestellung; fehlt der Satz, steht im Urteil nur «nennt
    keinen Grund dafuer». Die drei Werte in :func:`_kamerawerte_befund` haben keinen
    solchen Leser. Bewacht über Runner und Abholer in ``tests/test_runde8_reste.py``.
    """
    if herkunft.get("weg") == "abgeleitet":
        return {"deckungsgrad": herkunft["deckungsgrad"], "deckungsgrad_wirkungslos": None}
    bestellt = getattr(a, "deckungsgrad", None) if a is not None else None
    grund = (f"Die Kamera kam auf dem Weg {herkunft.get('weg')!r} zustande. Der "
             f"Deckungsgrad wirkt nur auf dem Weg 'abgeleitet' (Kamera aus der Huellbox "
             f"gerechnet); hier hat er nichts gerahmt. ")
    grund += (f"Bestellt war {float(bestellt)} — die Bestellung ist an diesem Bild "
              f"wirkungslos." if bestellt is not None else "Bestellt war keiner.")
    return {"deckungsgrad": None, "deckungsgrad_wirkungslos": grund}


#: Die drei Kameraangaben, die — wie der Deckungsgrad — nur auf dem Weg ``abgeleitet``
#: wirken: ``(Berichtsname, Schalter im Namensraum, Feld in der Herkunft)``.
#: Der Berichtsname ist der Name, unter dem sie bestellt werden (``kette.baue_kette``,
#: ``seams.glb_zu_multipass``) — wer ``augenhoehe`` bestellt, findet
#: ``augenhoehe_wirkungslos``.
_NUR_ABGELEITET = (
    ("augenhoehe", "augenhoehe", "augenhoehe_m"),
    ("bias_grad", "bias", "bias_grad"),
    ("kamera_modus", "kamera_modus", "modus"),
)


def _kamerawerte_befund(a, herkunft: dict) -> dict:
    """Augenhoehe, Bias und Kameramodus im Bericht — **so, wie sie gewirkt haben.**

    **Befund 23.09.2026** (nachgelesen, dieselbe Fehlerart wie der Deckungsgrad am
    22.09.2026): ``kameras.kamerasatz`` rechnet mit allen dreien, und aufgerufen wird es
    nur auf dem Weg ``abgeleitet``. Mit ``--auge``/``--blick-auf`` (``vorgegeben``) und im
    ``rueckfall`` greifen sie nirgends — angenommen wurden sie trotzdem auf jedem Weg, und
    der Bericht sagte dazu nichts.

    **Gemeldet als wirkungslos wird nur, was BESTELLT war** — ausdruecklich uebergeben,
    also nicht ``None`` im Namensraum. Entschieden 23.09.2026: Eine Vorgabe, die niemand
    bestellt hat, ist nicht «wirkungslos bestellt»; ein Satz dazu stuende auf JEDEM Bild
    mit vorgegebenem Standpunkt und verdraengte den einen Fall, in dem jemand wirklich
    etwas bestellt hat, das nicht ankam. Darum tragen ``--bias`` und ``--augenhoehe`` seit
    demselben Tag ``None`` statt ihrer Zahl als Vorgabe — sonst waere «bestellt» hier
    nicht feststellbar.

    **Anders als beim Deckungsgrad**, und das ist kein Versehen (Runde 8, 23.09.2026):
    :func:`_deckungsgrad_befund` nennt seinen Grund auch ohne Bestellung, weil der
    Abholer ihn als Begründung für «nicht gerahmt» liest (``abholer.
    _rahmung_vor_dem_render``). Augenhöhe, Bias und Kameramodus liest dort niemand — ein
    Satz ohne Bestellung hätte keinen Leser und nur die Verdrängung als Wirkung. Bewacht
    über Runner und Abholer in ``tests/test_runde8_reste.py``.

    Returns:
        Je Angabe zwei Felder, beide immer da: ``<name>`` und ``<name>_wirkungslos``.
        Auf ``abgeleitet`` der Wert, mit dem die Kamera gerechnet wurde (bestellt oder
        Vorgabe der Bibliothek), und ``None``. Sonst ``None`` — **nicht gestellt** — und
        ein Satz, warum, wenn die Angabe bestellt war; ohne Bestellung ``None``.
    """
    weg = herkunft.get("weg")
    befund = {}
    for name, schalter, feld in _NUR_ABGELEITET:
        if weg == "abgeleitet":
            befund[name] = herkunft.get(feld)
            befund[f"{name}_wirkungslos"] = None
            continue
        bestellt = getattr(a, schalter, None) if a is not None else None
        befund[name] = None
        if bestellt is None:
            befund[f"{name}_wirkungslos"] = None
            continue
        warum = ("der Standpunkt kam von Hand (--auge/--blick-auf) und wurde nur gestellt"
                 if weg == "vorgegeben" else
                 "es wurde der Rueckfall gestellt (keine Kamera angegeben, oder "
                 "'aiimaging.kameras' von diesem Blender aus nicht erreichbar)")
        befund[f"{name}_wirkungslos"] = (
            f"Bestellt war {name} {bestellt!r}, aber die Kamera kam auf dem Weg {weg!r} "
            f"zustande: {warum}. {name} wirkt nur auf dem Weg 'abgeleitet' (Kamera aus "
            f"dem Richtungskuerzel gerechnet) — an diesem Bild ist die Bestellung "
            f"wirkungslos.")
    return befund


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


#: Die Marke am Kontext-Objekt (eine Objekteigenschaft). An ihr — und nur an ihr — erkennen
#: Hüllbox, Material-ID-Tabelle und Meshzählung, dass ein Objekt NICHT zum Modell gehört.
#: Ein Name wäre die schwächere Wahl: Ein Bauteil darf heissen, wie es will.
KONTEXT_MARKE = "aiimaging_kontext"
KONTEXT_OBJEKT = "Kontext_Splat"
#: Der Name des Netzes aus der Splat-Brücke (13.10.2026) — ein anderer als beim Splat, damit
#: die Material-ID-Tabelle sagt, welcher Weg gezeichnet wurde.
KONTEXT_NETZ_OBJEKT = "Kontext_Netz"
KONTEXT_FARBE = "kontext_farbe"
KONTEXT_RADIUS = "kontext_radius"
#: Was ein 3DGS-PLY mindestens tragen muss. ``rot_*`` fehlt mit Absicht: Kugeln haben keine
#: Ausrichtung.
KONTEXT_SPALTEN = ("f_dc_0", "f_dc_1", "f_dc_2", "opacity", "scale_0", "scale_1", "scale_2")


def _ist_kontext(obj) -> bool:
    """Gehört dieses Objekt zum Kontext (Splat) und damit NICHT zum Modell?"""
    try:
        return bool(obj.get(KONTEXT_MARKE))
    except Exception:                                      # noqa: BLE001
        return False


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
        if obj.type != "MESH" or _ist_kontext(obj):
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


def _glbbox_modul():
    """``aiimaging.glbbox`` von hier aus erreichbar machen — oder ``None``.

    Dieselbe Bauart und dieselbe Begründung wie :func:`_maske_modul`. Geholt wird genau
    **eine** Zahl: :data:`aiimaging.glbbox.GERINGE_SCHRUMPFUNG`, die Schwelle, ab der
    eine Bauwerksbox als „hat nicht gegriffen" gilt.

    **Warum sie nicht hier hingeschrieben wird.** Sie steht drüben unter einer
    Herleitung — 2,1 % an einer Bestandsdatei gegen 40 % am Testbau — und bewegt sich
    mit der nächsten Messung. Eine Kopie an der Aussenkante liefe dabei still
    auseinander; genau diese Falle hat dieses Projekt bei der Geländeregel selbst schon
    einmal bezahlt.
    """
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
        from aiimaging import glbbox                        # noqa: PLC0415
        return glbbox
    except Exception:                                      # noqa: BLE001
        return None


def _achsen_modul():
    """``aiimaging.contracts`` von hier aus erreichbar machen — oder ``None``.

    Dieselbe Bauart wie :func:`_sonne_modul`: Der Runner darf aus dem Produkt lesen, nur
    der umgekehrte Weg ist verboten (Regel 2). ``contracts`` ist reine Vertragsarithmetik
    und bringt nichts mit.
    """
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
        from aiimaging import contracts                     # noqa: PLC0415
        return contracts
    except Exception:                                      # noqa: BLE001
        return None


def _gelaendeform_modul():
    """``aiimaging.gelaendeform`` von hier aus erreichbar machen — oder ``None``.

    Dieselbe Bauart und Begründung wie :func:`_sonne_modul` und :func:`_achsen_modul`:
    Der Runner darf aus dem Produkt **lesen**, nur der umgekehrte Weg ist verboten
    (Regel 2). ``gelaendeform`` ist reine Arithmetik über Hüllboxen — kein ``bpy``, keine
    Dateien, nur stdlib.

    **Ist es nicht erreichbar, bleibt es bei der Namensregel — und der Bericht sagt das.**
    Ein stiller Rückfall wäre hier besonders teuer: Er sähe aus wie «die Form hat nichts
    gefunden», und richtig wäre «die Form wurde nie gefragt».
    """
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
        from aiimaging import gelaendeform                   # noqa: PLC0415
        return gelaendeform
    except Exception:                                      # noqa: BLE001
        return None


def _kontext_modul():
    """``aiimaging.kontext`` von hier aus erreichbar machen — oder ``None``.

    Dieselbe Bauart wie :func:`_sonne_modul`. Von dort kommen die gesetzten Zahlen
    (Deckkraftschwelle, Radiuskappung), die Lage als Matrix und der Fingerabdruck — damit
    sie diesseits der Prozessgrenze prüfbar sind. **Ohne das Modul wird abgebrochen**,
    nicht geraten: Ein geratener Achsentausch legte den Splat auf die Seite, und das Bild
    sähe trotzdem aus wie eines mit Umgebung.
    """
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
        from aiimaging import kontext                       # noqa: PLC0415
        return kontext
    except Exception:                                      # noqa: BLE001
        return None


def _kontext_netz_modul():
    """``aiimaging.kontext_netz`` von hier aus erreichbar machen — oder ``None``.

    Dieselbe Bauart wie :func:`_kontext_modul`. Von dort kommt die Erkennung, ob die
    Kontextdatei ein Netz ist (PLY-Kopf mit Flächen). **Ohne das Modul bleibt es beim
    Splat-Weg** — der hält bei einer Datei, die kein Splat ist, mit Grund an (fehlende
    Spalten), statt zu raten.
    """
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
        from aiimaging import kontext_netz                  # noqa: PLC0415
        return kontext_netz
    except Exception:                                      # noqa: BLE001
        return None


#: Die Höhenachse in **Blenders Weltkoordinaten**: Z, also Index 2.
#:
#: **Sie steht hier als benannte Zahl, weil sie eine andere ist als drüben.**
#: :mod:`aiimaging.gelaendeform` hat die Vorgabe ``hoch=1`` — glTF, Y oben, so wie
#: :func:`aiimaging.glbbox.knotenboxen` die Boxen liefert. Hier ist die Datei längst
#: importiert und gedreht.
#:
#: *Ein falscher Achsenindex machte Wände flach und Böden aufragend — und keine Massprobe
#: sähe es.* Genau die Klasse Fehler, die am 01.09.2026 ein Gebäude auf den Kopf gestellt
#: hat: ``R_x(180)`` lässt jede Kantenlänge gleich, nur die Vorzeichen kippen. Darum wird
#: der Wert **ausdrücklich übergeben** und nicht geerbt.
HOCHACHSE_BLENDER = 2

#: Der Formbefund, wenn die Form nichts gesagt hat.
#:
#: **Er steht als eigene Vorgabe da, damit er auf JEDEM Rueckgabeweg gleich aussieht.**
#: Ein Feld, das mal da ist und mal nicht, zwingt jeden Leser zu einer Fallunterscheidung,
#: die er vergessen wird — und dann liest er `None` als «kein Gelaende» statt als «nicht
#: gefragt».
LEERER_FORMBEFUND = {"entschieden_durch": "keine", "gelaende_namen": ()}


def _namensbefund(gelaende) -> dict:
    """Der Befund, wenn die NAMENSREGEL getrennt hat — ``"name"`` mit ihren Namen.

    **Anlass (Ergebnis auf-20261022-334):** Die Namensregel trennte das Gelände der
    KosmoDraw-glb (Rahmung 0,509 enger), der Bericht sagte aber ``entschieden_durch:
    "keine"`` mit leerer Namensliste — ``"name"`` kannte nur ``glbbox.bauwerksbox``. Jetzt
    sagen beide Wege dasselbe: ``"name"``, sobald die Wortliste etwas getrennt hat und die
    Form nicht entschieden hat; ``"keine"`` nur, wenn nichts getrennt hat.

    **Was sich dadurch NICHT ändert:** Der Abholer überträgt Namen an die Bauwerksmaske nur
    bei ``"form"`` (``_formgelaende_aus_bericht``) — die Maske findet Namen der Wortliste
    selbst. Materialwahl, Plattengrau und Vorprobe prüfen jedes Objekt ohnehin mit derselben
    Wortliste (``maske.ist_gelaende``); dieselben Namen zusätzlich als Menge ändern nichts.
    """
    if not gelaende:
        return LEERER_FORMBEFUND
    return {"entschieden_durch": "name", "gelaende_namen": tuple(dict.fromkeys(gelaende))}


def _form_zweitmeinung(alle_knoten, gelaende):
    """Die Formregel befragen — **nur wenn die Namensregel nichts getrennt hat**.

    Dieselbe Bauart wie in :func:`aiimaging.glbbox.bauwerksbox` seit dem 07.09.2026, und
    aus demselben Grund: *Eine zweite Regel widerspricht der ersten; eine Zweitmeinung
    spricht nur, wenn die erste schweigt.*

    Returns:
        ``{"entschieden_durch": …, "gelaende_namen": (…)}`` — ``"form"`` nur, wenn die
        Form wirklich etwas gefunden hat, das die Namensregel nicht hatte. ``"keine"``
        heisst hier auch: **nicht gefragt** oder **nicht erreichbar**, und der Bericht
        unterscheidet das über die Notiz.
    """
    gf = _gelaendeform_modul()
    if gf is None or not alle_knoten:
        return {"entschieden_durch": "keine", "gelaende_namen": ()}
    try:
        befund = gf.gelaende_knoten(alle_knoten, hoch=HOCHACHSE_BLENDER)
    except Exception:                                      # noqa: BLE001
        # KEINE AUSKUNFT IST BESSER ALS EINE GERATENE — dieselbe Entscheidung wie in
        # `glbbox._zweitmeinung`. Eine Szene ohne Ausdehnung gibt keine Anteile her.
        return {"entschieden_durch": "keine", "gelaende_namen": ()}
    gefunden = [n for n in befund["gelaende"] if n not in set(gelaende)]
    # ALLES WAERE GELAENDE — dann trennt die Form nichts, und eine leere Bauwerksbox
    # waere schlimmer als eine zu grosse.
    if not gefunden or len(befund["gelaende"]) == len(alle_knoten):
        return {"entschieden_durch": "keine", "gelaende_namen": ()}
    return {"entschieden_durch": "form",
            "gelaende_namen": tuple(dict.fromkeys(befund["gelaende"]))}


def _nur_dort_materialien(objektnamen) -> list[str]:
    """Ursprungsnamen der Materialien, die NUR an diesen Objekten haengen — sortiert.

    Gelesen vor jedem Tausch der Slots; ein Material, das auch ein anderes Mesh-Objekt
    traegt, faellt heraus (es truege im ID-Pass dieselbe Farbe wie das Bauwerk).
    """
    namen = set(objektnamen or ())
    if not namen:
        return []
    dort, sonst = set(), set()
    for obj in (o for o in bpy.data.objects if o.type == "MESH" and not _ist_kontext(o)):
        ziel = dort if obj.name in namen else sonst
        for slot in obj.material_slots:
            if slot.material is not None:
                ziel.add(slot.material.get(URSPRUNG_MARKE) or slot.material.name)
    return sorted(m for m in dort - sonst if m)


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
        ``(lo, hi, note, schrumpfung)`` — ``lo``/``hi`` sind ``None``, wenn nichts
        feststellbar war; ``note`` sagt dann **warum**. ``schrumpfung`` ist der Anteil
        Grundriss-Diagonale, den die Bauwerksbox gegenüber der Szenenbox verloren hat,
        oder ``None``, wenn es keine Bauwerksbox gibt.

    .. note::
       **Kein Rückfall auf die Szenenbox.** Findet sich keine gebaute Substanz, kommt
       ``None`` zurück und nicht die Box von allem. Die Szenenbox stillschweigend als
       Bauwerksbox auszugeben hiesse, den Bruch zwischen Rahmung und Messung genau dort
       zuzudecken, wo er gemessen werden soll — und der Bericht sähe dann gesund aus.

    .. warning::
       **Und der stillste Fall ist nicht der leere Befund, sondern der wirkungslose**
       (gemessen am 02.09.2026). Bis dahin gab diese Funktion eine **leere** Notiz
       zurück, sobald die Regel auch nur *einen* Knoten als Gelände zählte — gleich, ob
       die Box danach um 80 % kleiner war oder um 2 %.

       An zwei echten Dateien gemessen, mit :func:`aiimaging.glbbox.bauwerksbox` auf
       derselben Regel: Auf einer Bestandsdatei sortierte die Regel 10 von 4771 Knoten
       aus und die Rahmung wurde um **2,3 %** enger; auf einem Geländemodell 1 von 112
       und **1,7 %**. Beide Male hätte hier nichts gestanden — und `rahmung.note` wie
       `massstab.note` im Abholer hätten eine Bauwerksbox gemeldet, die keine ist.

       ``glbbox`` sagt diesen Fall seit dem 01.09.2026; dieser Weg schwieg. *Zwei Wege
       zur selben Zahl sollen bei derselben Lage dieselbe Auskunft geben* — deshalb
       steht die Meldung jetzt auf beiden.
    """
    maske = _maske_modul()
    if maske is None:
        return None, None, ("'aiimaging.maske' ist von diesem Blender aus nicht "
                            "erreichbar — die Gelaenderegel konnte NICHT angewendet "
                            "werden. Das ist etwas anderes als 'es gibt kein Gelaende'."), None, LEERER_FORMBEFUND

    lo = [float("inf")] * 3
    hi = [float("-inf")] * 3
    szene_lo = [float("inf")] * 3
    szene_hi = [float("-inf")] * 3
    n = 0
    gelaende = []
    alle_knoten = []
    # Der grösste Knoten, den die Regel als BAUWERK gezählt hat — an ihm hängt die
    # Auskunft, welches Wort der Regel fehlt, wenn die Box nichts verliert.
    groesster = ("", 0.0)
    for obj in bpy.data.objects:
        if obj.type != "MESH" or _ist_kontext(obj):
            continue
        ecken = [obj.matrix_world @ __import__("mathutils").Vector(e)
                 for e in obj.bound_box]
        for welt in ecken:
            for i in range(3):
                szene_lo[i] = min(szene_lo[i], welt[i])
                szene_hi[i] = max(szene_hi[i], welt[i])
        o_lo = [min(w[i] for w in ecken) for i in range(3)]
        o_hi = [max(w[i] for w in ecken) for i in range(3)]
        # ALLE KNOTEN, auch die als Gelaende erkannten: Die Formregel braucht die ganze
        # Szene als Bezug, sonst bedeutet kein einziger ihrer drei Anteile etwas.
        alle_knoten.append((obj.name, o_lo, o_hi))
        if maske.ist_gelaende(obj.name):
            gelaende.append(obj.name)
            continue
        n += 1
        b = math.hypot(o_hi[0] - o_lo[0], o_hi[1] - o_lo[1])
        if b > groesster[1]:
            groesster = (obj.name, b)
        for i in range(3):
            lo[i] = min(lo[i], o_lo[i])
            hi[i] = max(hi[i], o_hi[i])

    if n == 0:
        return None, None, (
            f"Kein einziges Mesh-Objekt blieb nach der Gelaenderegel uebrig "
            f"({len(gelaende)} als Gelaende erkannt). Entweder besteht die Szene nur aus "
            f"Gelaende — dann ist der Auftrag ohne Bauwerk —, oder die Namen tragen die "
            f"Unterscheidung nicht. Es wird NICHT auf die Szenenbox zurueckgefallen."), None, LEERER_FORMBEFUND

    # Gemessen an der Grundriss-Diagonale, und die Wahl ist geliehen und nicht neu
    # getroffen: `glbbox.bauwerksbox` rechnet genauso, mit der Herleitung an Ort und
    # Stelle (die weiteste Kamera hängt an sqrt(dx² + dy²), nicht an max(dx, dy)).
    b_szene = math.hypot(szene_hi[0] - szene_lo[0], szene_hi[1] - szene_lo[1])
    b_bau = math.hypot(hi[0] - lo[0], hi[1] - lo[1])
    schrumpfung = (1.0 - b_bau / b_szene) if b_szene > 0.0 else 0.0

    # OHNE NAMENSTREFFER ERST DIE FORM FRAGEN (auf-20261021-316, B3). Bis zum 21.10.2026
    # kehrte dieser Weg hier zurueck, bevor die Form gefragt war — `glbbox.bauwerksbox`
    # fragt sie gerade in diesem Fall. Die Steine-Probe von KosmoDraw zeigte den Bruch: Die
    # Rahmung (glbbox) erkannte den Boden «boden» an der Gestalt, der Bericht dieses Wegs
    # nicht, und die Bauwerksmaske zaehlte ihn als Bauwerk. Jetzt faellt der Fall in den
    # Zweig unter der Schwelle (Schrumpfung 0) und bekommt dieselbe Auskunft wie dort.
    kein_gelaende_satz = (
        "Kein Objekt wurde als Gelaende erkannt; die Bauwerksbox ist "
        "hier gleich der Szenenbox. Das ist ein gueltiges Ergebnis und "
        "kein Rueckfall — aber ein Bruch zwischen Rahmung und Messung "
        "ist damit auch nicht feststellbar.")
    glbbox = _glbbox_modul()
    if not gelaende and glbbox is None:
        return lo, hi, kein_gelaende_satz, schrumpfung, LEERER_FORMBEFUND
    if glbbox is None:
        return lo, hi, (
            f"Die Gelaenderegel hat {len(gelaende)} Objekt(e) aussortiert und die Rahmung "
            f"damit um {schrumpfung:.1%} enger gemacht. Ob das viel oder wenig ist, steht "
            f"hier NICHT: 'aiimaging.glbbox' ist von diesem Blender aus nicht erreichbar, "
            f"und die Schwelle dafuer (GERINGE_SCHRUMPFUNG) wird nicht geraten."), schrumpfung, _namensbefund(gelaende)

    if schrumpfung < glbbox.GERINGE_SCHRUMPFUNG:
        # DIE ZWEITMEINUNG, an derselben Schwelle wie in `glbbox.bauwerksbox`.
        #
        # Der Docstring dieser Funktion verlangt sie seit dem 02.09.2026 selbst: *«Zwei
        # Wege zur selben Zahl sollen bei derselben Lage dieselbe Auskunft geben.»*
        # Damals ging es um den wirkungslosen Befund; seit dem 07.09. gilt derselbe Satz
        # fuer die Formregel, und dieser Weg schwieg wieder.
        form = _form_zweitmeinung(alle_knoten, gelaende)
        if form["entschieden_durch"] == "form":
            namen = set(form["gelaende_namen"])
            bau = [k for k in alle_knoten if k[0] not in namen]
            if bau:
                lo = [min(k[1][i] for k in bau) for i in range(3)]
                hi = [max(k[2][i] for k in bau) for i in range(3)]
                b_bau = math.hypot(hi[0] - lo[0], hi[1] - lo[1])
                schrumpfung = (1.0 - b_bau / b_szene) if b_szene > 0.0 else 0.0
                return lo, hi, (
                    f"DIE NAMENSREGEL HAT FAST NICHTS GETRENNT — die FORM hat "
                    f"entschieden. {len(namen)} Objekt(e) sind an ihrer Gestalt als "
                    f"Gelaende erkannt (gross im Grundriss, flach, unten), die Rahmung "
                    f"wird dadurch um {schrumpfung:.1%} enger. Ihre Namen tragen keines "
                    f"der Woerter aus maske.GELAENDE_WOERTER; sie stehen im Bericht "
                    f"unter 'bbox_bauwerk_gelaende_namen' und erreichen von dort die "
                    f"Bauwerksmaske."), schrumpfung, form
        if not gelaende:
            return lo, hi, kein_gelaende_satz, schrumpfung, LEERER_FORMBEFUND
        return lo, hi, (
            f"Die Gelaenderegel hat {len(gelaende)} Objekt(e) aussortiert, die Rahmung "
            f"wird davon aber nur um {schrumpfung:.1%} enger — unter "
            f"{glbbox.GERINGE_SCHRUMPFUNG:.0%}. Das SIEHT nach einer Bauwerksbox aus und "
            f"wirkt wie keine. DER GROESSTE KNOTEN, DEN DIE REGEL HIER ALS BAUWERK "
            f"ZAEHLT, heisst '{groesster[0]}' und spannt {groesster[1]:.2f} m auf, also "
            f"{(groesster[1] / b_szene if b_szene > 0.0 else 0.0):.0%} der Szene — wenn "
            f"das kein Bauteil ist, fehlt der Regel genau sein Wort. Wer eine wirksame "
            f"Box braucht, ergaenzt die REGEL an ihrer einen Stelle "
            f"(maske.GELAENDE_WOERTER) — nicht diesen Aufruf."), schrumpfung, _namensbefund(gelaende)
    # DIE NAMENSREGEL HAT WIRKSAM GETRENNT (Ergebnis 334): «name», wie in `glbbox`.
    return lo, hi, "", schrumpfung, _namensbefund(gelaende)


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
            # DIE EINZIGE STELLE, AN DER DER DECKUNGSGRAD AUF DIE KAMERA WIRKT — und
            # darum die einzige, von der der Bericht ihn als gewirkt uebernimmt
            # (`_deckungsgrad_befund` liest ihn sonst nur, um den Grund zu nennen).
            # Befund 22.09.2026 (auf-20260922-137, zwei Deckungsgrade, dieselbe
            # Tiefenkarte): Der Bericht schrieb ihn bis dahin auf JEDEM Weg hinein.
            deckungsgrad = _vorgabe(a, "deckungsgrad", kameras.DECKUNGSGRAD)
            satz = kameras.kamerasatz(
                [list(lo), list(hi)], kuerzel=[a.kamera],
                brennweite_mm=brennweite,
                bias_grad=_vorgabe(a, "bias", kameras.BIAS_GRAD),
                augenhoehe_m=_vorgabe(a, "augenhoehe", kameras.AUGENHOEHE_M),
                deckungsgrad=deckungsgrad,
                gelaende_z=getattr(a, "gelaende_z", None),
                # LANGE, FLACHE BAUWERKE ALS AUSSCHNITT (Entscheid 75, 08.10.2026) — nur,
                # wenn nach dem BAUWERK gerahmt wird (`--kamera-huellbox`). Auf der
                # Szenenbox waere eine grosse Gelaendeplatte «lang und flach», und der
                # Ausschnitt hebelte den Rahmungsriegel aus, der genau dieses Bild nicht
                # rendern soll (`test_kettenlauf_echt`, Grundstueck).
                # Seit auf-20261008-271 auch mit `--kamera-ausschnitt`: Ohne Gelaende ist die
                # Szene das Bauwerk, und genau die lange Halle bekam nie eine Bauwerksbox.
                ausschnitt=bool(getattr(a, "kamera_huellbox", None)
                                or getattr(a, "kamera_ausschnitt", False)),
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
                **({"abstand_fest_m": a.abstand_fest}
                   if getattr(a, "abstand_fest", None) is not None else {}),
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
                # Der Deckungsgrad, mit dem DIESE Kamera gerechnet wurde. Er steht nur
                # auf diesem Weg da, weil er nur hier gewirkt hat.
                "deckungsgrad": deckungsgrad,
                "azimut_grad": k["azimut_grad"],
                "modus": k["modus"],
                # WAS DIE RECHNUNG WIRKLICH BENUTZT HAT, aus `kamerasatz` zurueckgelesen
                # und nicht aus den Schaltern abgeschrieben (Befund 23.09.2026). Nur
                # dieser Weg rechnet mit Augenhoehe und Bias — auf `vorgegeben` und
                # `rueckfall` stehen sie darum nicht hier, siehe `_kamerawerte_befund`.
                "augenhoehe_m": satz["augenhoehe_m"],
                "bias_grad": satz["bias_grad"],
                "neigung_grad": k["neigung_grad"],
                "shift_mm": k["shift_mm"],
                "massgebend": k["massgebend"],
                "durchlaeufe": k["durchlaeufe"],
                # Wenn der Eckentest nicht aufging, steht das hier — und nicht nur in
                # einem Bild, das jemand später schief findet.
                "vollstaendig": k["vollstaendig"],
                # Gewollter Ausschnitt eines langen, flachen Bauwerks (Entscheid 75) —
                # dann ist `vollstaendig` False ohne gescheiterten Eckentest.
                "ausschnitt": bool(k.get("ausschnitt")),
                # Der Füllgrad sagt, was der Eckentest nicht sagt: ob das Bauwerk das
                # Bild auch AUSFÜLLT. Zu klein fällt keiner Prüfung auf, die nur nach
                # "passt es hinein" fragt.
                "fuellgrad": k["fuellgrad"],
                "abstand_m": k["abstand_m"],
                "abstand_fest_m": satz.get("abstand_fest_m"),
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

def _stimmung_modul():
    """``aiimaging.stimmung`` von hier aus — dieselbe Bauart wie :func:`_maske_modul`.

    Von dort kommen die Farben des ruhigen Hintergrunds (:func:`hintergrund_aus_himmel`) und
    die Reihenfolge der Tonwertkurven (:data:`TONWERTE`) — eine zweite Fassung hier liefe
    beim nächsten Tausch auseinander.
    """
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
        from aiimaging import stimmung                       # noqa: PLC0415
        return stimmung
    except Exception:                                      # noqa: BLE001
        return None


#: Der Grund, wenn die Farben nicht aus dem Himmelsbild zu lesen sind: ein ruhiges Grau.
#: Der Hintergrund bleibt auch dann ruhig — das Himmelsbild wird NIE zum Fotohintergrund.
RUECKFALL_HINTERGRUND = {"horizont": [0.62, 0.64, 0.66], "zenit": [0.45, 0.50, 0.58]}

#: Wie gross das Himmelsbild für die zwei Hintergrundfarben verkleinert wird.
HIMMEL_PROBE_GROESSE = (128, 64)


def _himmelsfarben(bild) -> dict:
    """Horizont- und Zenitfarbe des Himmelsbilds — oder :data:`RUECKFALL_HINTERGRUND`.

    Auf einer verkleinerten Kopie gemessen (4096 × 2048 als Liste wären 33 Mio. Zahlen);
    die Kopie wird danach wieder entfernt. Nie eine Ausnahme: Ein Hintergrund ist kein Grund,
    einen Lauf scheitern zu lassen — der Bericht sagt, welcher Weg galt.
    """
    modul = _stimmung_modul()
    if modul is None:
        return dict(RUECKFALL_HINTERGRUND, weg="rueckfall",
                    grund="aiimaging.stimmung ist von hier nicht lesbar.")
    kopie = None
    try:
        kopie = bild.copy()
        b, h = HIMMEL_PROBE_GROESSE
        kopie.scale(b, h)
        punkte = list(kopie.pixels[:])
        kanaele = int(getattr(kopie, "channels", 4) or 4)
        farben = modul.hintergrund_aus_himmel(punkte, b, h, kanaele=kanaele)
        # DIE SONNE IM HIMMELSBILD (auf-20261020-293, Punkt 2) — auf derselben Kopie.
        try:
            sonne = modul.sonne_aus_himmel(punkte, b, h, kanaele=kanaele)
        except Exception as fehler:                        # noqa: BLE001
            sonne = {"gefunden": False, "weg": "rueckfall",
                     "grund": f"Sonne nicht lesbar: {fehler}"}
        farben = dict(farben, sonne=sonne)
    except Exception as fehler:                            # noqa: BLE001
        return dict(RUECKFALL_HINTERGRUND, weg="rueckfall",
                    grund=f"Himmelsbild nicht lesbar fuer den Hintergrund: {fehler}")
    finally:
        if kopie is not None:
            try:
                bpy.data.images.remove(kopie)
            except Exception:                              # noqa: BLE001
                pass
    if not farben.get("horizont") or not farben.get("zenit"):
        return dict(RUECKFALL_HINTERGRUND, weg="rueckfall",
                    grund="Himmelsbild ohne Punkte ueber dem Horizont.")
    return dict(farben, weg="himmelsbild", grund="")


#: Der Name des Background-Knotens, den die Kamera sieht (der ruhige Verlauf).
RUHIGER_GRUND = "Ruhiger_Grund"
#: Der Name des RGB-Knotens mit der Bodenfarbe unter dem Horizont (Ergebnis 335) — die
#: Vorprobe findet ihn und stellt ihn nach ``stimmung.boden_zum_faktor``.
BODEN_FARBE = "Boden_Farbe"


def _ruhiger_hintergrund(welt, licht_ausgang, staerke: float, farben: dict, toenung,
                         himmel_farbe=None, boden=None) -> None:
    """Kamerastrahlen sehen einen Verlauf, alle anderen Strahlen das Himmelsbild.

    **Anlass (auf-20261020-292, B2):** Das Himmelsbild stand als Fotohintergrund da — ein
    Bodenfoto mit Wald und Felsen, das Haus schwebte davor. **Entscheid: «Is Camera Ray»**
    (Light Path) statt eines transparenten Films mit nachträglichem Grund: Das Bild bleibt
    deckend (kein Alphakanal, den der KI-Schritt oder eine Vorschau falsch läse), Licht und
    Spiegelungen kommen weiter aus dem Himmelsbild, und der ID-Pass und die Tiefe sind nicht
    betroffen — der ID-Pass baut seine Welt neu (schwarz), die Tiefe misst Geometrie, nicht
    die Welt. Der Verlauf geht vom Horizont (und darunter) zum Zenit, in den Medianfarben
    dieses Himmels, mit derselben Stärke und Tönung.

    **Messschalter «Himmel sichtbar»** (``himmel_farbe``, auf-20261021-309 Option Himmel; nur
    mit ``vis.himmel_sichtbar``, Vorgabe aus): Die Kamera sieht dann das Himmelsbild selbst
    (dieselbe gekappte, getönte Farbe wie das Fülllicht) statt des Verlaufs. Der Knoten trägt
    denselben Namen (:data:`RUHIGER_GRUND`), damit die Vorprobe ihn wie den Verlauf auf den
    Abstand zum Haus stellt (309: Faktor morgen 1,0, abend 0,72, bedeckt 3,2).

    **Boden bis zum Horizont** (``boden``, Ergebnis auf-20261022-334; nur zusammen mit
    ``himmel_farbe``): ``{boden, dunst, dunst_grad}`` aus ``stimmung.boden_bis_horizont``.
    Über dem Horizont (Blickrichtung Z > 0) bleibt das Himmelsbild; darunter sieht die Kamera
    die Bodenfarbe, in den letzten ``dunst_grad`` Grad weich in die Horizontfarbe übergehend
    — statt der unteren Hälfte des Himmelsbilds. Nur der Kamerastrahl: Licht und
    Spiegelungen bleiben beim Himmelsbild (``licht_ausgang``).
    """
    baum = welt.node_tree
    tf = list(toenung) if toenung else [1.0, 1.0, 1.0]
    horizont = (*(float(c) * t for c, t in zip(farben["horizont"], tf)), 1.0)
    zenit = (*(float(c) * t for c, t in zip(farben["zenit"], tf)), 1.0)
    koord = baum.nodes.new("ShaderNodeTexCoord")
    trenne = baum.nodes.new("ShaderNodeSeparateXYZ")
    baum.links.new(koord.outputs["Generated"], trenne.inputs["Vector"])
    bereich = baum.nodes.new("ShaderNodeMapRange")
    bereich.inputs["From Min"].default_value = 0.0
    bereich.inputs["From Max"].default_value = math.sin(math.radians(45.0))
    bereich.inputs["To Min"].default_value = 0.0
    bereich.inputs["To Max"].default_value = 1.0
    try:
        bereich.clamp = True
    except Exception:                                      # noqa: BLE001
        pass
    baum.links.new(trenne.outputs["Z"], bereich.inputs["Value"])
    verlauf = (himmel_farbe if himmel_farbe is not None
               else _mix_farbe(baum, bereich.outputs["Result"], horizont, zenit))
    if himmel_farbe is not None and boden:
        verlauf = _boden_unter_horizont(baum, trenne.outputs["Z"], verlauf, boden)
    grund = baum.nodes.new("ShaderNodeBackground")
    # Mit Namen, damit die Vorprobe (`_hintergrund_abstimmen`, auf-20261020-293) ihn wiederfindet.
    grund.name = RUHIGER_GRUND
    baum.links.new(verlauf, grund.inputs["Color"])
    grund.inputs["Strength"].default_value = float(staerke)
    weg = baum.nodes.new("ShaderNodeLightPath")
    mischung = baum.nodes.new("ShaderNodeMixShader")
    baum.links.new(weg.outputs["Is Camera Ray"], mischung.inputs[0])
    baum.links.new(licht_ausgang, mischung.inputs[1])
    baum.links.new(grund.outputs["Background"], mischung.inputs[2])
    ausgabe = next((k for k in baum.nodes if getattr(k, "type", "") == "OUTPUT_WORLD"), None)
    if ausgabe is None:
        ausgabe = baum.nodes.new("ShaderNodeOutputWorld")
    baum.links.new(mischung.outputs["Shader"], ausgabe.inputs["Surface"])


def _boden_unter_horizont(baum, hoehe, himmel_farbe, boden: dict):
    """Unter dem Horizont Boden, darüber der Himmel — gibt den Farbausgang zurück.

    ``hoehe`` ist die Z-Komponente der Blickrichtung (Generated, Länge 1, Z oben). Die Kette:
    Dunst = MapRange(Z: −sin(dunst_grad)…0 → 0…1) mischt Boden → Horizontfarbe; «über dem
    Horizont» = Math GREATER_THAN(Z, 0) wählt dann zwischen diesem Boden und dem Himmelsbild.
    Die Kante liegt genau auf dem Horizont des Himmelsbilds; die Platte, die näher ist,
    verdeckt den Welt-Boden ohnehin.
    """
    dunst = baum.nodes.new("ShaderNodeMapRange")
    dunst.inputs["From Min"].default_value = -math.sin(
        math.radians(float(boden.get("dunst_grad") or 0.0)))
    dunst.inputs["From Max"].default_value = 0.0
    dunst.inputs["To Min"].default_value = 0.0
    dunst.inputs["To Max"].default_value = 1.0
    try:
        dunst.clamp = True
    except Exception:                                      # noqa: BLE001
        pass
    baum.links.new(hoehe, dunst.inputs["Value"])
    # DIE BODENFARBE ALS EIGENER KNOTEN (Ergebnis 335): die Vorprobe stellt sie nach ihrem
    # Faktor (`stimmung.boden_zum_faktor`) — hoechstens so hell wie die Platte.
    farbe = baum.nodes.new("ShaderNodeRGB")
    farbe.name = BODEN_FARBE
    farbe.outputs["Color"].default_value = (*(float(c) for c in boden["boden"]), 1.0)
    unten = _mix_farbe(baum, dunst.outputs["Result"], farbe.outputs["Color"],
                       (*(float(c) for c in boden["dunst"]), 1.0))
    oben = baum.nodes.new("ShaderNodeMath")
    oben.operation = "GREATER_THAN"
    baum.links.new(hoehe, oben.inputs[0])
    oben.inputs[1].default_value = 0.0
    return _mix_farbe(baum, oben.outputs["Value"], unten, himmel_farbe)


def _drehung_der_welt(drehung_grad, licht, sonne: dict, kamera_azimut) -> dict:
    """Die Drehung des Himmelsbilds — bestellt, zur Kamera gerechnet, oder die Vorgabe 0.

    **Seit auf-20261020-294 (B1):** Ohne bestellte Drehung (``--umgebung-drehung`` fehlt)
    und mit Lichtdaten, die ``sonne_seitlich_grad`` nennen, wird das Bild JE KAMERA so
    gedreht, dass die Sonne seitlich der Blickachse steht (``stimmung.drehung_zur_kamera``,
    reine Rechnung). Eine bestellte Drehung hat Vorrang — Wort für Wort wie bisher. Ohne
    Lichtdaten (vor 293) bleibt es bei 0.

    Returns:
        ``{drehung_grad, weg, grund, kamera_azimut_grad?, seitlich_grad?, seite?}`` — ``weg``
        ``bestellt``, ``zur_kamera`` oder ``vorgabe``.
    """
    if drehung_grad is not None:
        return {"drehung_grad": float(drehung_grad), "weg": "bestellt", "grund": ""}
    seitlich = (licht or {}).get("sonne_seitlich_grad")
    if not seitlich:
        return {"drehung_grad": 0.0, "weg": "vorgabe", "grund": ""}
    modul = _stimmung_modul()
    azimut_bild = (sonne or {}).get("azimut_bild_grad")
    if modul is None or not hasattr(modul, "drehung_zur_kamera"):
        return {"drehung_grad": 0.0, "weg": "vorgabe",
                "grund": "aiimaging.stimmung ist von hier nicht lesbar — Drehung 0."}
    if kamera_azimut is None or azimut_bild is None:
        return {"drehung_grad": 0.0, "weg": "vorgabe",
                "grund": ("Ohne Blickrichtung der Kamera oder Sonnenrichtung im Himmelsbild "
                          "keine Drehung zur Kamera — Drehung 0.")}
    seite = (licht or {}).get("sonne_seite") or "links"
    return {"drehung_grad": modul.drehung_zur_kamera(azimut_bild, kamera_azimut,
                                                     seitlich_grad=float(seitlich),
                                                     seite=seite),
            "weg": "zur_kamera", "grund": "", "kamera_azimut_grad": round(kamera_azimut, 3),
            "seitlich_grad": float(seitlich), "seite": seite}


def _boden_der_welt(farben: dict, toenung, licht, staerke: float = 1.0) -> dict | None:
    """Die Bodenfarbe unter dem Horizont (``stimmung.boden_bis_horizont``) — oder ``None``.

    Nur mit ``boden_bis_horizont`` in den Lichtdaten (Abholer, nur mit sichtbarem Himmel);
    ohne es bleibt der Kamerastrahl Wort für Wort wie vor 334. Nie eine Ausnahme.

    **Seit Ergebnis 335** mit dem Licht der Platte: dieselbe Lampe, die
    :func:`_lampe_der_stimmung` gleich danach stellt (``stimmung.lampe_aus_himmel``, reine
    Rechnung, aus der Sonne dieses Himmelsbilds — die Drehung ändert ihre Höhe nicht), und das
    Fülllicht aus ``e_himmel_h``. Fehlt die Sonnenanalyse (Rückfall ohne ``e_himmel_h``), bleibt
    der Boden von 334 (Albedo × mittlerer Himmel). Eine ausdrücklich bestellte Sonne
    (``render.sun``) kennt diese Rechnung nicht — sie gilt für das Licht der Stimmung.
    """
    if not (licht and licht.get("boden_bis_horizont") is True):
        return None
    modul = _stimmung_modul()
    if modul is None or not hasattr(modul, "boden_bis_horizont"):
        return None
    sonne = farben.get("sonne") or {}
    lampe = None
    if sonne.get("e_himmel_h") and sonne.get("richtung_bild") and hasattr(
            modul, "lampe_aus_himmel"):
        try:
            lampe = modul.lampe_aus_himmel(sonne, licht, staerke=float(staerke),
                                           toenung=toenung)
        except Exception:                                  # noqa: BLE001
            lampe = None
    try:
        return modul.boden_bis_horizont(farben["horizont"], farben["zenit"],
                                        albedo=licht.get("gelaende_grau"), toenung=toenung,
                                        lampe=lampe, e_himmel_h=sonne.get("e_himmel_h"),
                                        staerke=float(staerke),
                                        fuell_staerke=licht.get("fuell_staerke"))
    except TypeError:
        # Ein aelteres stimmung-Modul ohne die Lichtangaben: der Boden von 334.
        try:
            return modul.boden_bis_horizont(farben["horizont"], farben["zenit"],
                                            albedo=licht.get("gelaende_grau"),
                                            toenung=toenung)
        except Exception:                                  # noqa: BLE001
            return None
    except Exception:                                      # noqa: BLE001
        return None


def _welt_setzen(farbe, staerke: float, *, hdr=None, drehung_grad: float | None = 0.0,
                 toenung=None, licht=None, kamera_azimut=None):
    """Umgebungslicht als Welt setzen — gleichmässig, oder aus einem Himmelsbild.

    `read_factory_settings(use_empty=True)` löscht auch die Welt. Ohne sie rendert Cycles
    vor absolutem Schwarz und ohne jede Aufhellung — genau der Zustand, in dem das
    Beauty-Bild des Vorgängerstands unsichtbar blieb.

    **Mit Himmelsbild** (``hdr``, Entscheide 107/110, 20.10.2026): Texture Coordinate
    (Generated) → Mapping (Drehung um Z, ``drehung_grad``) → Environment Texture →
    Background (``staerke``). Die Datei wird unverändert geladen (CC0, Regel 1). Der
    ID-Pass ruft diese Funktion danach OHNE ``hdr`` — sein Grund bleibt schwarz.

    **Seit auf-20261020-292 (B2/B3):** Das Himmelsbild gibt nur noch Licht und Spiegelungen;
    die Kamera sieht einen ruhigen Verlauf (:func:`_ruhiger_hintergrund`). ``toenung``
    (``(r, g, b)``, linear, aus ``stimmung.toenung_fuer``) färbt Licht und Grund.

    **Seit auf-20261020-293 (Punkt 2), mit ``licht``** (den Daten der Stimmung): Das
    Himmelsbild ist nur noch **Fülllicht** (Stärke × ``fuell_staerke``). Bei einer Stimmung
    mit Sonne wird seine Sonnenscheibe gekappt (Vector Math «Minimum» auf die Schwelle aus
    ``stimmung.sonne_aus_himmel``) — die Sonnenlampe (:func:`_sonne_setzen`) übernimmt sie,
    aus derselben Richtung, sonst stünde die Sonne doppelt da. Ohne ``licht`` bleibt alles
    wie vor 293.

    **Seit auf-20261020-294 (B1):** ``drehung_grad`` ``None`` heisst «nicht bestellt»; mit
    ``licht`` und ``kamera_azimut`` (Richtung Haus → Kamera) dreht :func:`_drehung_der_welt`
    das Bild so, dass die Sonne seitlich der Kamera steht. Gestellt wird die Drehung erst
    nach dem Lesen der Sonne — sie hängt an deren Richtung im Bild.

    Returns:
        ``None`` ohne Himmelsbild, sonst ``{datei, staerke, drehung_grad, groesse, toenung,
        hintergrund, licht?}`` — nur der Dateiname, kein Pfad (Regel 3).
    """
    welt = bpy.data.worlds.new("Welt")
    hintergrund = _welt_hintergrund(welt)
    hintergrund.inputs["Color"].default_value = (*farbe, 1.0)
    hintergrund.inputs["Strength"].default_value = staerke
    bpy.context.scene.world = welt
    if not hdr:
        return None
    baum = welt.node_tree
    koord = baum.nodes.new("ShaderNodeTexCoord")
    abbild = baum.nodes.new("ShaderNodeMapping")
    himmel = baum.nodes.new("ShaderNodeTexEnvironment")
    himmel.image = bpy.data.images.load(str(hdr), check_existing=True)
    baum.links.new(koord.outputs["Generated"], abbild.inputs["Vector"])
    baum.links.new(abbild.outputs["Vector"], himmel.inputs["Vector"])
    farben = _himmelsfarben(himmel.image)
    sonne = farben.get("sonne") or {}
    # DIE DREHUNG NACH DER SONNE (auf-20261020-294, B1): bestellt, sonst zur Kamera.
    drehung = (_drehung_der_welt(drehung_grad, licht, sonne, kamera_azimut) if licht else
               {"drehung_grad": float(drehung_grad or 0.0),
                "weg": "bestellt" if drehung_grad is not None else "vorgabe", "grund": ""})
    drehung_grad = drehung["drehung_grad"]
    abbild.inputs["Rotation"].default_value = (0.0, 0.0, math.radians(float(drehung_grad)))
    # DAS FUELLLICHT (auf-20261020-293): mit `licht` nur ein Teil des Himmelsbilds, und bei
    # einer Stimmung mit Sonne ohne seine Sonnenscheibe — die Lampe uebernimmt sie.
    fuell = float((licht or {}).get("fuell_staerke") or 1.0) if licht else 1.0
    kappung = (float(sonne["kappung"]) if licht and licht.get("sonne")
               and sonne.get("gefunden") and sonne.get("kappung") else None)
    farbausgang = himmel.outputs["Color"]
    if kappung is not None:
        kappen = baum.nodes.new("ShaderNodeVectorMath")
        kappen.operation = "MINIMUM"
        kappen.inputs[1].default_value = (kappung, kappung, kappung)
        baum.links.new(farbausgang, kappen.inputs[0])
        farbausgang = kappen.outputs["Vector"]
    if toenung:
        faerben = baum.nodes.new("ShaderNodeVectorMath")
        faerben.operation = "MULTIPLY"
        faerben.inputs[1].default_value = tuple(float(k) for k in toenung)
        baum.links.new(farbausgang, faerben.inputs[0])
        farbausgang = faerben.outputs["Vector"]
    baum.links.new(farbausgang, hintergrund.inputs["Color"])
    hintergrund.inputs["Strength"].default_value = staerke * fuell
    # Der ruhige Grund mit derselben Staerke wie das Fuelllicht; die Vorprobe stellt ihn
    # danach auf den Abstand zum Haus (`_hintergrund_abstimmen`). Mit dem Messschalter
    # «Himmel sichtbar» (nur ueber die Lichtdaten, Vorgabe aus) ist es das Himmelsbild selbst.
    himmel_sichtbar = bool(licht and licht.get("himmel_sichtbar") is True)
    # BODEN BIS ZUM HORIZONT (Ergebnis 334): nur mit sichtbarem Himmel und dem Lichtdatum.
    boden = _boden_der_welt(farben, toenung, licht, staerke) if himmel_sichtbar else None
    _ruhiger_hintergrund(welt, hintergrund.outputs["Background"], staerke * fuell, farben,
                         toenung, himmel_farbe=farbausgang if himmel_sichtbar else None,
                         boden=boden)
    befund = {"datei": Path(str(hdr)).name, "staerke": float(staerke),
              "drehung_grad": float(drehung_grad),
              "groesse": [int(v) for v in himmel.image.size],
              "toenung": list(toenung) if toenung else None,
              "hintergrund": {"art": "himmelsbild" if himmel_sichtbar else "verlauf",
                              "kamerastrahl": "himmel" if himmel_sichtbar else "ruhig",
                              "horizont": list(farben["horizont"]),
                              "zenit": list(farben["zenit"]), "weg": farben["weg"],
                              "grund": farben["grund"]}}
    if boden is not None:
        befund["hintergrund"]["boden"] = boden
    if licht:
        befund["drehung"] = drehung
        befund["licht"] = {"fuell_staerke": fuell, "staerke_fuelllicht": staerke * fuell,
                           "sonnenscheibe_gekappt": kappung is not None, "kappung": kappung,
                           "herkunft": licht.get("herkunft_licht")}
        befund["himmel_sonne"] = sonne or None
    return befund


#: Die Tonwertkurven, falls ``aiimaging.stimmung`` nicht lesbar ist — dieselbe Reihenfolge.
RUECKFALL_TONWERTE = ("AgX", "Filmic")


def _look_setzen(szene, transform, look) -> dict:
    """Die kontrastreichere Fassung der Tonwertkurve (auf-20261020-293, Punkt 4).

    Blender nennt sie je Fassung anders: «AgX - Medium High Contrast» (4.x, mit Vorsatz der
    Kurve) oder nur «Medium High Contrast». Beide werden versucht, die erste, die greift,
    gilt; greift keine, bleibt «None» — und der Grund steht im Bericht (Rückfall mit Grund).
    """
    versucht = []
    for name in (f"{transform} - {look}", str(look)):
        try:
            szene.view_settings.look = name
        except Exception as fehler:                        # noqa: BLE001
            versucht.append(f"{name}: {fehler}")
            continue
        return {"look": name, "look_grund": ""}
    try:
        szene.view_settings.look = "None"
    except Exception:                                      # noqa: BLE001
        pass
    return {"look": "None", "look_grund": ("Look nicht vorhanden in diesem Blender: "
                                           + "; ".join(versucht))}


def _tonwerte_setzen(szene, belichtung_ev, look=None) -> dict:
    """Tonwertkurve und Belichtung für das Schönbild MIT Himmelsbild (auf-20261020-292, B1).

    Versucht der Reihe nach ``stimmung.TONWERTE`` (AgX, Filmic) — die erste, die dieses
    Blender kennt, gilt; kennt es keine, bleibt «Standard», und der Bericht sagt es. Der
    ID-Pass stellt danach :func:`_tonwerte_zurueck` — seine Kennfarben brauchen «Standard».
    """
    modul = _stimmung_modul()
    reihe = tuple(getattr(modul, "TONWERTE", RUECKFALL_TONWERTE) or RUECKFALL_TONWERTE)
    gesetzt = None
    versucht = []
    for name in reihe:
        try:
            szene.view_settings.view_transform = name
        except Exception as fehler:                        # noqa: BLE001
            versucht.append(f"{name}: {fehler}")
            continue
        gesetzt = name
        break
    try:
        szene.view_settings.look = "None"
    except Exception:                                      # noqa: BLE001
        pass
    ev = float(belichtung_ev or 0.0)
    szene.view_settings.exposure = ev
    befund = {"tonwerte": gesetzt or "Standard", "belichtung_ev": ev,
              "grund": ("" if gesetzt else
                        "Keine der Tonwertkurven ist in diesem Blender vorhanden: "
                        + "; ".join(versucht))}
    # DER LOOK DER STIMMUNG (auf-20261020-293, Punkt 4) — nur, wenn bestellt und eine Kurve
    # griff; ohne bleibt der Bericht der von 292.
    if look and gesetzt:
        befund.update(_look_setzen(szene, gesetzt, look))
    return befund


def _tonwerte_zurueck(szene) -> None:
    """«Standard», Belichtung 0 — für den ID-Pass, dessen Kennfarben exakt bleiben müssen."""
    szene.view_settings.view_transform = "Standard"
    szene.view_settings.look = "None"
    try:
        szene.view_settings.exposure = 0.0
    except Exception:                                      # noqa: BLE001
        pass


#: Was eine bestellte Sonne ausmacht — ist eines davon gesetzt, bleibt die Sonnenlampe auch
#: mit Himmelsbild (Entscheid 110: sonst doppeltes Licht, ausser die Sonne ist bestellt).
SONNE_SCHALTER = ("sonne_hoehe", "sonne_azimut", "sonne_staerke", "sonne_kelvin",
                  "sonne_winkel")


def _sonne_bestellt(a) -> bool:
    return any(getattr(a, name, None) is not None for name in SONNE_SCHALTER)


#: Das diffuse Weiss des Gipsmodells (Entscheid 113) — linear, leicht warm, nie reines Weiss
#: (reines Weiss frisst unter einem hellen Himmel aus).
GIPS_FARBE = (0.80, 0.79, 0.77)
GIPS_RAUHEIT = 1.0
#: Woran ein Material dieses Runners zu erkennen ist, und welches es ersetzte.
MATERIAL_MARKE = "aiimaging_materialwahl"
URSPRUNG_MARKE = "aiimaging_ursprung"


def _gips_material():
    """Ein diffuses Weiss, Rauheit hoch — der Gips des Weissmodells."""
    mat = bpy.data.materials.new("Gips_Weissmodell")
    mat.use_nodes = True
    baum = mat.node_tree
    baum.nodes.clear()
    diffus = baum.nodes.new("ShaderNodeBsdfDiffuse")
    diffus.inputs["Color"].default_value = (*GIPS_FARBE, 1.0)
    diffus.inputs["Roughness"].default_value = GIPS_RAUHEIT
    ausgang = baum.nodes.new("ShaderNodeOutputMaterial")
    baum.links.new(diffus.outputs["BSDF"], ausgang.inputs["Surface"])
    mat[MATERIAL_MARKE] = "gips"
    return mat


def _ersetze_slots(obj, neues_material, behalten=None) -> int:
    """Jeden Slot eines Objekts durch ``neues_material(ursprungsname)`` ersetzen.

    Der Name des ersetzten Materials reist als :data:`URSPRUNG_MARKE` am neuen mit —
    ``_material_id_zuweisen`` vergibt die Kennung danach unter dem ALTEN Namen, und die
    Bauwerksmaske (sie liest Namen) sieht dasselbe wie ohne Oberflaeche. Ein Objekt ohne
    Material bekommt einen Slot mit leerem Ursprung und bleibt dort ein «objekt».

    ``behalten(material)`` (optional): ein Slot, für den es ``True`` sagt, bleibt, wie er ist
    — heute die Scheibe bei der Materialwahl «fenster» (:func:`_ist_glas`).
    """
    belegt = [s for s in obj.material_slots if s.material is not None]
    if not belegt:
        obj.data.materials.clear()
        obj.data.materials.append(neues_material(""))
        return 1
    n = 0
    for slot in belegt:
        if behalten is not None and behalten(slot.material):
            continue
        slot.material = neues_material(slot.material.get(URSPRUNG_MARKE, slot.material.name))
        n += 1
    return n


#: Wörter, an denen ein Materialname als Scheibe gilt (KosmoOrbit-glb: «Glas»).
GLAS_WOERTER = ("glas", "glass", "verglasung", "glazing")


def _ist_glas(material) -> bool:
    """Ist dieses Material eine Scheibe? Name (:data:`GLAS_WOERTER`) oder Durchlass > 0.

    **Anlass (Mac-Demolauf 22.10.2026, Fund 3):** Die Art «fenster» meint die Rahmen
    (``materialwahl.ART_IM_SATZ``: «frames»), aber die Scheibe einer KosmoOrbit-glb trägt
    dieselbe Art (``kind: opening``) — eine gewählte Fenster-Textur machte das Glas deckend.
    Der Durchlass kommt aus dem glTF-Import (``KHR_materials_transmission`` → «Transmission
    Weight», vor Blender 4 «Transmission»).
    """
    if material is None:
        return False
    name = str(getattr(material, "name", "") or "").lower()
    if any(w in name for w in GLAS_WOERTER):
        return True
    baum = getattr(material, "node_tree", None)
    for knoten in (getattr(baum, "nodes", None) or ()):
        if getattr(knoten, "type", "") != "BSDF_PRINCIPLED":
            continue
        for eingang in ("Transmission Weight", "Transmission"):
            try:
                wert = float(knoten.inputs[eingang].default_value)
            except Exception:                              # noqa: BLE001
                continue
            if wert > 0.0:
                return True
    return False


#: Die höchste Rauheit einer Scheibe im Schönbild (Ergebnis 332, 22.10.2026). Der IFC-Stil
#: lieferte 1,0 mit, und das Glas sah aus wie mattes Milchglas — ohne Spiegelung und ohne
#: Durchblick. Die KosmoOrbit-glb liefert ihr Glas mit 0,05. Gesetzt, nicht gemessen.
GLAS_RAUHEIT_HOECHSTENS = 0.05
#: Wie weit eine Rauheit über :data:`GLAS_RAUHEIT_HOECHSTENS` liegen darf und doch als «schon
#: so» gilt (Ergebnis 333): Blender speichert Zahlen in einfacher Genauigkeit und liest die
#: 0,05 der glb als 0,0500000007 — das ist grösser als 0,05, und das Glas wurde als «gesetzt»
#: gezählt, obwohl nichts zu tun war. Der Wert blieb richtig, der Bericht nicht.
GLAS_RAUHEIT_TOLERANZ = 1e-6


def _glas_klar(materialien=None) -> dict:
    """Jedes Material mit Durchlass (> 0) bekommt höchstens :data:`GLAS_RAUHEIT_HOECHSTENS`.

    Nur Principled-BSDF mit «Transmission Weight» (vor Blender 4 «Transmission») über 0 — der
    Durchlass kommt aus der Datei (``KHR_materials_transmission``), nicht aus einem Namen.
    Eine Rauheit, die an einer Karte hängt, bleibt (verbunden heisst: die Datei meint sie).
    Rückgabe ``{materialien, rauheit}``: wie viele gesetzt wurden.
    """
    gesetzt = 0
    for mat in (materialien if materialien is not None else bpy.data.materials):
        baum = getattr(mat, "node_tree", None)
        for knoten in (getattr(baum, "nodes", None) or ()):
            if getattr(knoten, "type", "") != "BSDF_PRINCIPLED":
                continue
            durchlass = 0.0
            for eingang in ("Transmission Weight", "Transmission"):
                try:
                    durchlass = float(knoten.inputs[eingang].default_value)
                    break
                except Exception:                          # noqa: BLE001
                    continue
            if durchlass <= 0.0:
                continue
            try:
                rau = knoten.inputs["Roughness"]
                if getattr(rau, "is_linked", False):
                    continue
                if float(rau.default_value) > GLAS_RAUHEIT_HOECHSTENS + GLAS_RAUHEIT_TOLERANZ:
                    rau.default_value = GLAS_RAUHEIT_HOECHSTENS
                    gesetzt += 1
            except Exception:                              # noqa: BLE001
                continue
    return {"materialien": gesetzt, "rauheit": GLAS_RAUHEIT_HOECHSTENS}


def _materialwahl_modul():
    """``aiimaging.materialwahl`` von hier aus — dieselbe Bauart wie :func:`_maske_modul`.

    Die Zuordnung «welche Art ist dieses Bauteil» steht dort (ohne Blender prüfbar); eine
    zweite Liste hier liefe beim nächsten Bauteil auseinander.
    """
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
        from aiimaging import materialwahl                  # noqa: PLC0415
        return materialwahl
    except Exception:                                      # noqa: BLE001
        return None


def _merkmal(obj, *namen):
    """Ein Custom Property am Objekt oder an einem Elternteil — der glTF-Import legt die
    ``extras`` eines Knotens dort ab (``obj["kind"]``)."""
    while obj is not None:
        for name in namen:
            try:
                wert = obj.get(name)
            except Exception:                              # noqa: BLE001
                wert = None
            if wert not in (None, ""):
                return wert
        obj = getattr(obj, "parent", None)
    return None


def _ifc_name(obj) -> str:
    """Der IFC-Knotenname (``IfcWall_…``) des Objekts oder eines Elternteils, sonst sein Name."""
    kette = obj
    while kette is not None:
        if _ist_ifc_knoten(kette.name):
            return kette.name
        kette = getattr(kette, "parent", None)
    return obj.name


def _bauteil_art(obj, wahl_modul, maske, gelaende_namen) -> str:
    """Die Art eines Objekts nach :func:`aiimaging.materialwahl.art_von` — Gelände über die
    Geländeregel (Name des Objekts oder eines seiner Materialien) und die Formprüfung."""
    return _bauteil_art_herkunft(obj, wahl_modul, maske, gelaende_namen)[0]


def _eltern_namen(obj) -> list:
    namen, kette = [], getattr(obj, "parent", None)
    while kette is not None:
        namen.append(kette.name)
        kette = getattr(kette, "parent", None)
    return namen


def _bauteil_art_herkunft(obj, wahl_modul, maske, gelaende_namen) -> tuple:
    """``(art, herkunft)`` — wie :func:`_bauteil_art`, dazu woher die Art kommt (N5,
    :func:`aiimaging.materialwahl.art_und_herkunft`); die Namensregel sieht auch die Namen der
    Elternteile."""
    name = _ifc_name(obj)
    namen = [obj.name, name] + [s.material.name for s in obj.material_slots
                                if s.material is not None]
    gelaende = any(n in gelaende_namen for n in namen) or (
        maske is not None and any(maske.ist_gelaende(n) for n in namen))
    merkmale = dict(kind=_merkmal(obj, "kind"),
                    predefined=_merkmal(obj, "PredefinedType", "predefined_type"),
                    opening_type=_merkmal(obj, "openingType", "opening_type"),
                    ist_gelaende=gelaende)
    if not hasattr(wahl_modul, "art_und_herkunft"):
        return wahl_modul.art_von(name, **merkmale), "unbekannt"
    return wahl_modul.art_und_herkunft(name, namen=[obj.name, *_eltern_namen(obj)], **merkmale)


def _mix_farbe(baum, faktor, a, b):
    """Zwei Farben mischen — ``ShaderNodeMix`` (ab 3.4), sonst ``ShaderNodeMixRGB``.

    ``faktor`` ist eine Zahl oder ein Ausgang (dann verbunden); ``a``/``b`` ein Ausgang oder
    eine Farbe (RGBA-Tupel). Gibt den Farbausgang zurück.
    """
    try:
        mix = baum.nodes.new("ShaderNodeMix")
        mix.data_type = "RGBA"
        eingaenge = [x for x in mix.inputs if getattr(x, "type", "") == "RGBA"]
        ausgang = next(x for x in mix.outputs if getattr(x, "type", "") == "RGBA")
        fak = mix.inputs["Factor"]
    except Exception:                                      # noqa: BLE001
        mix = baum.nodes.new("ShaderNodeMixRGB")
        eingaenge = [mix.inputs["Color1"], mix.inputs["Color2"]]
        ausgang = mix.outputs["Color"]
        fak = mix.inputs["Fac"]
    if isinstance(faktor, (int, float)):
        fak.default_value = float(faktor)
    else:
        baum.links.new(faktor, fak)
    for ziel, quelle in zip(eingaenge[:2], (a, b)):
        if isinstance(quelle, tuple):
            ziel.default_value = quelle
        else:
            baum.links.new(quelle, ziel)
    return ausgang


def _hex_linear(farbe: str):
    rgb = [int(farbe[i:i + 2], 16) / 255.0 for i in (1, 3, 5)]
    return (*(_srgb_zu_linear(k) for k in rgb), 1.0)


#: Die Box-Projektion mischt an den Kanten der drei Ebenen — 0,2 (Bauplan F4).
BOX_UEBERBLENDUNG = 0.2


def _material_aus_wahl(art: str, wahl: dict, ursprung: str):
    """Ein Principled BSDF aus einer Materialwahl (Bauplan F4, Entscheide 111/113).

    Texture Coordinate «Object» → Mapping (Massstab 1/massstab_m, Drehung um die Hochachse)
    → Image Texture je Karte in **Box-Projektion** (Überblendung :data:`BOX_UEBERBLENDUNG`).
    Farbe gemischt mit der Tönung (Faktor = Stärke), Rauheit als Non-Color, **Bump aus der
    Höhe** (Stärke = relief) statt Normal-Map, weil die Box-Projektion keine Tangenten hat.
    Ein Bild, das nicht quadratisch ist, wird in der Hochachse nach seinem Seitenverhältnis
    gestreckt (gelesen, nicht angenommen — Concrete002). Mit ``fugen`` (Holzlattung)
    schneidet eine Streifenmaske über x+y Fugen hinein: dunkel und im Relief vertieft.
    """
    mat = bpy.data.materials.new(f"Materialwahl_{art}_{wahl['id']}")
    mat.use_nodes = True
    baum = mat.node_tree
    baum.nodes.clear()
    karten = wahl.get("karten") or {}
    koord = baum.nodes.new("ShaderNodeTexCoord")
    abbild = baum.nodes.new("ShaderNodeMapping")
    massstab = float(wahl.get("massstab_m") or 1.0)
    bilder = {}
    for karte in ("Color", "Roughness", "Displacement"):
        if karten.get(karte):
            bild = bpy.data.images.load(karten[karte], check_existing=True)
            if karte != "Color":
                bild.colorspace_settings.name = "Non-Color"
            bilder[karte] = bild
    breite, hoehe = (list(getattr(bilder.get("Color"), "size", None) or ()) + [0, 0])[:2]
    seiten = (float(breite) / float(hoehe)) if breite and hoehe else 1.0
    abbild.inputs["Scale"].default_value = (1.0 / massstab, 1.0 / massstab,
                                            seiten / massstab)
    abbild.inputs["Rotation"].default_value = (
        0.0, 0.0, math.radians(float(wahl.get("drehungGrad") or 0.0)))
    baum.links.new(koord.outputs["Object"], abbild.inputs["Vector"])

    def textur(karte):
        knoten = baum.nodes.new("ShaderNodeTexImage")
        knoten.image = bilder[karte]
        knoten.projection = "BOX"
        knoten.projection_blend = BOX_UEBERBLENDUNG
        baum.links.new(abbild.outputs["Vector"], knoten.inputs["Vector"])
        return knoten

    shader = baum.nodes.new("ShaderNodeBsdfPrincipled")
    ausgang = baum.nodes.new("ShaderNodeOutputMaterial")
    farbe = textur("Color").outputs["Color"]
    toenung = wahl.get("toenung")
    if toenung:
        farbe = _mix_farbe(baum, toenung["staerke"], farbe, _hex_linear(toenung["farbe"]))
    fugen = wahl.get("fugen")
    fuge = None
    if fugen:
        # Streifen ueber x+y der Objektkoordinate: Periode Latte+Fuge, Fuge = Anteil am Ende.
        periode = float(fugen["latte_m"]) + float(fugen["fuge_m"])
        trennen = baum.nodes.new("ShaderNodeSeparateXYZ")
        baum.links.new(koord.outputs["Object"], trennen.inputs["Vector"])
        summe = baum.nodes.new("ShaderNodeMath")
        summe.operation = "ADD"
        baum.links.new(trennen.outputs["X"], summe.inputs[0])
        baum.links.new(trennen.outputs["Y"], summe.inputs[1])
        geteilt = baum.nodes.new("ShaderNodeMath")
        geteilt.operation = "DIVIDE"
        baum.links.new(summe.outputs["Value"], geteilt.inputs[0])
        geteilt.inputs[1].default_value = periode
        rest = baum.nodes.new("ShaderNodeMath")
        rest.operation = "FRACT"
        baum.links.new(geteilt.outputs["Value"], rest.inputs[0])
        groesser = baum.nodes.new("ShaderNodeMath")
        groesser.operation = "GREATER_THAN"
        baum.links.new(rest.outputs["Value"], groesser.inputs[0])
        groesser.inputs[1].default_value = float(fugen["latte_m"]) / periode
        fuge = groesser.outputs["Value"]
        dunkel = float(fugen.get("dunkel", 0.25))
        # In der Fuge die Farbe abgedunkelt (Faktor = Maske).
        farbe = _mix_farbe(baum, fuge, farbe, (dunkel * 0.2, dunkel * 0.17, dunkel * 0.14, 1.0))
    baum.links.new(farbe, shader.inputs["Base Color"])
    if "Roughness" in bilder:
        baum.links.new(textur("Roughness").outputs["Color"], shader.inputs["Roughness"])
    if "Displacement" in bilder and float(wahl.get("relief") or 0.0) > 0.0:
        hoehe_knoten = textur("Displacement").outputs["Color"]
        if fuge is not None:
            senke = baum.nodes.new("ShaderNodeMath")
            senke.operation = "SUBTRACT"
            baum.links.new(hoehe_knoten, senke.inputs[0])
            baum.links.new(fuge, senke.inputs[1])
            hoehe_knoten = senke.outputs["Value"]
        bump = baum.nodes.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = float(wahl["relief"])
        bump.inputs["Distance"].default_value = 0.02 * massstab
        baum.links.new(hoehe_knoten, bump.inputs["Height"])
        baum.links.new(bump.outputs["Normal"], shader.inputs["Normal"])
    baum.links.new(shader.outputs["BSDF"], ausgang.inputs["Surface"])
    mat[MATERIAL_MARKE] = art
    mat[URSPRUNG_MARKE] = ursprung
    return mat


def _materialien_setzen(a, gelaende_namen=()) -> dict:
    """Die Materialwahl je Bauteil-Art auf die Szene legen — **vor dem Schönbild**.

    Heisst nicht wie im Bauplan nach dem Knoten «Oberfläche»: Das Wort meint in diesem
    Projekt die Bedienoberfläche, und der Kern darf sie in Kleinschreibung nicht nennen
    (Wächter in den Proben, «der Kern weiss von der Fläche nichts»).

    Je Objekt die Art (:func:`_bauteil_art`); Gelände nie; nicht gewählte Arten behalten
    ihr glb-Material («aus dem Modell»). Je (Art, ersetztes Material) entsteht ein Material,
    das den alten Namen als :data:`URSPRUNG_MARKE` trägt — ``_material_id_zuweisen`` vergibt
    danach dieselben Kennungen wie ohne Wahl.
    """
    wahl_modul = _materialwahl_modul()
    if wahl_modul is None:
        raise RuntimeError(
            "aiimaging.materialwahl ist von hier nicht lesbar, und --materialien braucht dort "
            "die Zuordnung der Bauteil-Arten. Ohne sie wird nicht gerechnet — ein Bild mit den "
            "Materialien des Modells saehe aus wie eines mit den gewaehlten.")
    satz = json.loads(Path(a.materialien).read_text(encoding="utf-8"))
    arten = satz.get("arten") or {}
    maske = _maske_modul()
    neu: dict = {}
    zaehlung = {art: 0 for art in (*wahl_modul.ARTEN, wahl_modul.ART_GELAENDE)}
    gesetzt = {art: 0 for art in arten}
    # Was je Art NICHT ersetzt wurde, und warum — Scheiben (Glas bleibt Glas) und benannte
    # Materialien eines Bauteils ohne Art (N5). Je Art die Zahl der behaltenen Slots.
    scheiben = {art: 0 for art in arten}
    aus_datei = {art: 0 for art in arten}
    unbestimmt = 0
    benannt = getattr(wahl_modul, "ist_benanntes_material", None)
    for obj in sorted((o for o in bpy.data.objects if o.type == "MESH" and not _ist_kontext(o)),
                      key=lambda o: o.name):
        art, herkunft = _bauteil_art_herkunft(obj, wahl_modul, maske, set(gelaende_namen))
        zaehlung[art] = zaehlung.get(art, 0) + 1
        ohne_art = herkunft == getattr(wahl_modul, "HERKUNFT_UNBESTIMMT", None)
        unbestimmt += 1 if ohne_art else 0
        if art not in arten:
            continue

        def material(ursprung, _art=art):
            schluessel = (_art, ursprung)
            if schluessel not in neu:
                neu[schluessel] = _material_aus_wahl(_art, arten[_art], ursprung)
            return neu[schluessel]

        def behalten(m, _art=art, _ohne_art=ohne_art):
            # DIE SCHEIBE BLEIBT GLAS (Mac-Demolauf 22.10.2026): «fenster» ersetzt die Rahmen.
            # Nur dort — eine andere Wahl auf einem Objekt mit Glas ersetzt es (Probe 331).
            if _art == "fenster" and _ist_glas(m):
                scheiben[_art] += 1
                return True
            # N5: Ein Bauteil, über das die Datei nichts sagt (kein kind, kein Ifc-Präfix, kein
            # Wort im Namen), behält sein BENANNTES Material — «Beton», «Baum», «Terrasse».
            if _ohne_art and benannt is not None and benannt(getattr(m, "name", "")):
                aus_datei[_art] += 1
                return True
            return False

        if _ersetze_slots(obj, material, behalten=behalten):
            gesetzt[art] += 1
    return {"arten": {art: {"id": w.get("id"), "asset": w.get("asset"),
                            "groesse": w.get("groesse"), "objekte": gesetzt[art],
                            "scheiben_behalten": scheiben[art],
                            "datei_material_behalten": aus_datei[art],
                            "karten": sorted(Path(p).name for p in (w.get("karten") or {}).values())}
                      for art, w in arten.items()},
            "objekte_je_art": zaehlung,
            "objekte_ohne_art": unbestimmt,
            # Punkt 4 (Ergebnis 332): «nicht_getroffen: fenster» las sich wie ein Fehlschlag,
            # war aber gewollt (das Fenster war nur Glas). Jetzt getrennt nach dem Grund; das
            # alte Feld bleibt mit derselben Bedeutung für bestehende Leser.
            "ohne_bauteil": sorted(art for art in arten if zaehlung.get(art, 0) == 0),
            "nur_behalten": sorted(art for art, n in gesetzt.items()
                                   if n == 0 and zaehlung.get(art, 0) > 0),
            "nicht_getroffen": sorted(art for art, n in gesetzt.items() if n == 0),
            "lesart": ("ohne_bauteil: die Datei hat kein Bauteil dieser Art; nur_behalten: es "
                       "gibt sie, aber alle Flaechen blieben wie in der Datei (Glas, benanntes "
                       "Material ohne Art) — beides gewollt, kein Fehler")}


def _alles_weiss() -> dict:
    """Stimmung «weiss»: jedes Mesh des Modells (nicht der Splat) als Gipsmodell."""
    gips = {}

    def neu(ursprung):
        if ursprung not in gips:
            m = _gips_material()
            m[URSPRUNG_MARKE] = ursprung
            gips[ursprung] = m
        return gips[ursprung]

    n = 0
    for obj in bpy.data.objects:
        if obj.type == "MESH" and not _ist_kontext(obj):
            _ersetze_slots(obj, neu)
            n += 1
    return {"weiss": True, "objekte": n, "farbe_linear": list(GIPS_FARBE),
            "rauheit": GIPS_RAUHEIT}


def _ist_gelaende_objekt(obj, maske, gelaende_namen) -> bool:
    """Gelände nach derselben Regel wie :func:`_bauteil_art` — Name, IFC-Knoten, Material."""
    namen = [obj.name, _ifc_name(obj)] + [s.material.name for s in obj.material_slots
                                          if s.material is not None]
    return any(n in gelaende_namen for n in namen) or (
        maske is not None and any(maske.ist_gelaende(n) for n in namen))


def _gelaende_grau(grau, gelaende_namen=()) -> dict:
    """Die Geländeplatte als ruhiges Neutralgrau (auf-20261020-293, Punkt 3).

    **Anlass:** Die Platte war hellgrau wie der Himmel — Schatten waren auf ihr nicht zu
    sehen. Ohne gewähltes Material (die Materialwahl fasst Gelände nie an) bekommt sie ein
    diffuses Grau, leicht dunkler; bei «weiss» ein helleres, damit das Gipsmodell darauf
    steht. Wie beim Gips trägt das neue Material den alten Namen (:data:`URSPRUNG_MARKE`) —
    der ID-Pass und die Bauwerksmaske sehen dasselbe wie vorher.
    """
    maske = _maske_modul()
    farbe = tuple(float(c) for c in grau)
    neu: dict = {}

    def material(ursprung):
        if ursprung not in neu:
            mat = bpy.data.materials.new("Gelaende_Grau")
            mat.use_nodes = True
            baum = mat.node_tree
            baum.nodes.clear()
            diffus = baum.nodes.new("ShaderNodeBsdfDiffuse")
            diffus.inputs["Color"].default_value = (*farbe, 1.0)
            diffus.inputs["Roughness"].default_value = 1.0
            ausgang = baum.nodes.new("ShaderNodeOutputMaterial")
            baum.links.new(diffus.outputs["BSDF"], ausgang.inputs["Surface"])
            mat[MATERIAL_MARKE] = "gelaende_grau"
            mat[URSPRUNG_MARKE] = ursprung
            neu[ursprung] = mat
        return neu[ursprung]

    n = 0
    for obj in list(bpy.data.objects):
        if obj.type == "MESH" and not _ist_kontext(obj) and _ist_gelaende_objekt(
                obj, maske, set(gelaende_namen)):
            _ersetze_slots(obj, material)
            n += 1
    return {"objekte": n, "farbe_linear": list(farbe)}


#: Wie klein die Vorprobe rechnet (Prozent der Bildgrösse) und mit wie vielen Samples —
#: genug für einen Mittelwert über das Haus, ein Bruchteil des Schönbilds.
VORPROBE_PROZENT = 25
VORPROBE_SAMPLES = 16
VORPROBE_ORDNER = "_vorprobe"


def _hintergrund_abstimmen(szene, out_dir: Path, licht: dict, umgebung: dict,
                           gelaende_namen=()) -> dict:
    """Den ruhigen Hintergrund auf einen festen Abstand zum Haus stellen (auf-20261020-293, 1).

    **Anlass:** Das Haus verschwand bei winter, morgen, nebel und bedeckt im Hintergrund
    (Kontrast −0,5 bis −8,6 Grauwerte). Der Verlauf hatte die Medianfarben des Himmels und war
    so hell wie das diffus beleuchtete Haus; Stärke und Belichtung skalieren beide gleich.

    **Entscheid: eine kleine Vorprobe, kein zweites Schönbild.** Ein Viertel der Grösse,
    16 Samples, ohne Entrauschen, mit durchsichtigem Hintergrund und ohne Gelände vor der
    Kamera (Schatten und Aufhellung bleiben): Deckend ist dort nur das Haus, und seine
    mittlere Helligkeit ist **gemessen** — mit Material, Sonne und Geometrie dieses Laufs.
    Eine Schätzung aus dem Himmel allein kennt weder das Material noch die Ausrichtung der
    Fassaden; ein nachträglich eingesetzter Hintergrund (Kompositor) gäbe Säume an den Kanten
    und änderte das Schönbild, das der KI-Schritt als Eingang bekommt. Gerechnet wird der
    Abstand in Blendenstufen (linear, vor Tonwertkurve und Belichtung, die beide gleich
    verschieben) mit ``stimmung.hintergrund_mit_abstand`` — **seit auf-20261020-295 gegen
    das Haus im Mittel in Stufen** (``stimmung.HAUS_MASS``), derselben Grösse, die
    ``qa.kontrast_haus_hintergrund`` am Bild misst; das lineare Mittel gehörte bei «abend»
    der Sonnenseite und liess den Hintergrund hell neben der Schattenseite stehen; nur die Stärke des Verlaufs
    ändert sich (Kamerastrahl), der Farbton bleibt. Danach wird alles zurückgestellt — der
    durchsichtige Film gilt NUR hier, nie im Schönbild.

    Nie eine Ausnahme: Misslingt die Vorprobe, bleibt der Verlauf, und der Bericht sagt es;
    ``qa.kontrast_haus_hintergrund`` misst danach am Schönbild ohnehin nach.
    """
    import shutil
    beginn = time.time()
    modul = _stimmung_modul()
    welt = bpy.context.scene.world
    grund = welt.node_tree.nodes.get(RUHIGER_GRUND) if welt is not None else None
    if modul is None or grund is None:
        return {"weg": "ohne", "faktor": 1.0,
                "grund": "Kein ruhiger Grund oder aiimaging.stimmung nicht lesbar."}
    r = szene.render
    vorher = {"prozent": r.resolution_percentage, "samples": szene.cycles.samples,
              "entrauschen": szene.cycles.use_denoising, "film": r.film_transparent,
              "format": r.image_settings.file_format, "tiefe": r.image_settings.color_depth,
              "modus": r.image_settings.color_mode, "pfad": r.filepath}
    maske = _maske_modul()
    versteckt = [o for o in bpy.data.objects
                 if o.type == "MESH" and (_ist_kontext(o) or _ist_gelaende_objekt(
                     o, maske, set(gelaende_namen)))]
    ordner = Path(out_dir) / VORPROBE_ORDNER
    befund = {"weg": "vorprobe", "prozent": VORPROBE_PROZENT, "samples": VORPROBE_SAMPLES}
    try:
        for o in versteckt:
            o.visible_camera = False
        r.resolution_percentage = VORPROBE_PROZENT
        szene.cycles.samples = VORPROBE_SAMPLES
        szene.cycles.use_denoising = False
        r.film_transparent = True
        r.image_settings.file_format = "OPEN_EXR"
        r.image_settings.color_depth = "32"
        r.image_settings.color_mode = "RGBA"
        ordner.mkdir(parents=True, exist_ok=True)
        r.filepath = str(ordner / "haus_")
        bpy.ops.render.render(write_still=True)
        datei = next(iter(sorted(ordner.glob("haus_*.exr"))), None)
        if datei is None:
            raise RuntimeError("Die Vorprobe schrieb kein Bild.")
        bild = bpy.data.images.load(str(datei))
        try:
            # Ohne `haus_mass` in den Lichtdaten das lineare Mittel wie bis 295.
            haus = modul.haus_leuchtdichte(list(bild.pixels[:]),
                                           kanaele=int(getattr(bild, "channels", 4) or 4),
                                           mass=licht.get("haus_mass") or "linear")
        finally:
            bpy.data.images.remove(bild)
        if haus["leuchtdichte"] is None:
            raise RuntimeError("In der Vorprobe ist kein deckender Hauspunkt.")
        staerke = float(grund.inputs["Strength"].default_value)
        tf = list(umgebung.get("toenung") or (1.0, 1.0, 1.0))
        farben = umgebung.get("hintergrund") or {}
        horizont = [float(c) * t * staerke for c, t in zip(farben["horizont"], tf)]
        zenit = [float(c) * t * staerke for c, t in zip(farben["zenit"], tf)]
        abstand = modul.hintergrund_mit_abstand(
            horizont, zenit, haus["leuchtdichte"],
            abstand_ev=float(licht.get("hintergrund_abstand_ev") or 1.0),
            richtung=licht.get("hintergrund_richtung") or "auto")
        # DER SICHTBARE HIMMEL PASST ZUR STIMMUNG (Ergebnis 333): Die Regel ist fuer den
        # Verlauf gebaut; auf das echte Himmelsbild (Entscheid 126) wirkt sie begrenzt —
        # daemmrig hoechstens eine Blende dunkler, hell nie unter die Staerke der Stimmung.
        # Nur mit `himmel_sichtbar` und der Untergrenze in den Lichtdaten; sonst wie bisher.
        untergrenze = (licht.get("himmel_untergrenze")
                       if licht.get("himmel_sichtbar") is True else None)
        if untergrenze and hasattr(modul, "himmel_begrenzen"):
            abstand = modul.himmel_begrenzen(
                abstand, untergrenze, staerke_vorher=staerke,
                staerke_stimmung=float(umgebung.get("staerke") or staerke))
        grund.inputs["Strength"].default_value = staerke * abstand["faktor"]
        # DER BODEN HOECHSTENS SO HELL WIE DIE PLATTE (Ergebnis 335): Der Faktor gilt fuer
        # Himmel und Boden zugleich; hellt er nur den Himmel auf (Untergrenze, mittag), wird
        # die Bodenfarbe zurueckgeteilt. Ohne Bodenknoten (vor 334) nichts.
        befund.update(_boden_nachstellen(welt, modul, abstand["faktor"]))
        # WIE DAS HAUS GEMESSEN WURDE (auf-20261020-295, N1): in Blendenstufen, wie die
        # Grauwerte der Pruefung — beide Mittel stehen im Bericht.
        befund.update(abstand, n_haus=haus["n"], staerke_vorher=staerke,
                      staerke_nachher=staerke * abstand["faktor"],
                      haus_mass=haus.get("mass", "linear"),
                      haus_linear=haus.get("linear", haus["leuchtdichte"]),
                      haus_stufen=haus.get("stufen"))
    except Exception as fehler:                            # noqa: BLE001
        befund.update(weg="ohne", faktor=1.0, grund=f"Vorprobe misslang: {fehler}")
    finally:
        for o in versteckt:
            o.visible_camera = True
        r.resolution_percentage = vorher["prozent"]
        szene.cycles.samples = vorher["samples"]
        szene.cycles.use_denoising = vorher["entrauschen"]
        r.film_transparent = vorher["film"]
        r.image_settings.file_format = vorher["format"]
        r.image_settings.color_depth = vorher["tiefe"]
        r.image_settings.color_mode = vorher["modus"]
        r.filepath = vorher["pfad"]
        shutil.rmtree(ordner, ignore_errors=True)
    befund["dauer_s"] = round(time.time() - beginn, 2)
    return befund


def _boden_nachstellen(welt, modul, faktor) -> dict:
    """Die Bodenfarbe nach dem Faktor der Vorprobe (``stimmung.boden_zum_faktor``).

    Gibt ``{boden_nach_vorprobe}`` zurück (die gestellte Farbe) oder ``{}`` ohne Bodenknoten
    bzw. ohne die Rechnung. Nie eine Ausnahme — der Boden bleibt dann, wie er war.
    """
    try:
        knoten = welt.node_tree.nodes.get(BODEN_FARBE)
    except Exception:                                      # noqa: BLE001
        return {}
    if knoten is None or not hasattr(modul, "boden_zum_faktor"):
        return {}
    try:
        vorher = [float(c) for c in list(knoten.outputs["Color"].default_value)[:3]]
        neu = modul.boden_zum_faktor(vorher, faktor)
        knoten.outputs["Color"].default_value = (*neu, 1.0)
        return {"boden_nach_vorprobe": neu}
    except Exception as fehler:                            # noqa: BLE001
        return {"boden_nach_vorprobe": None, "boden_grund": f"Boden nicht gestellt: {fehler}"}


#: Die Drehung, die dieser Runner bis zum 26.08.2026 unbedingt setzte.
#:
#: Sie steht hier als **Rückfall** — und nur als der. Ist ``aiimaging.sonne`` von diesem
#: Blender aus nicht erreichbar, wird sie gestellt, und der Bericht sagt es ausdrücklich.
#: Die Zahlen dahinter (40° über dem Horizont, 35° östlich von Süden) stehen in
#: ``aiimaging.sonne``; der alte Kommentar an dieser Stelle nannte **beide falsch**.
RUECKFALL_SONNE_EULER = (math.radians(50.0), 0.0, math.radians(35.0))


def _licht_der_stimmung(a):
    """Die Lichtdaten aus ``--umgebung-licht`` — ``None`` ohne (dann das Licht von vor 293)."""
    roh = getattr(a, "umgebung_licht", None)
    if not roh:
        return None
    try:
        licht = json.loads(roh) if isinstance(roh, str) else dict(roh)
    except (TypeError, ValueError) as fehler:
        raise RuntimeError(f"--umgebung-licht ist kein JSON-Objekt: {fehler}") from fehler
    if not isinstance(licht, dict):
        raise RuntimeError("--umgebung-licht ist kein JSON-Objekt.")
    return licht


#: Die Sonne, wenn das Himmelsbild nicht lesbar war: 40° hoch, aus Südosten — derselbe
#: Stand wie :data:`RUECKFALL_SONNE_EULER`, als Richtung.
_H, _A = math.radians(40.0), math.radians(-55.0)
RUECKFALL_HIMMEL_SONNE = {"gefunden": False, "weg": "rueckfall", "e_himmel_h": 1.0,
                          "richtung_bild": [math.cos(_H) * math.cos(_A),
                                            math.cos(_H) * math.sin(_A), math.sin(_H)]}


def _lampe_der_stimmung(mitte, spanne: float, a, licht: dict, umgebung: dict | None):
    """Die Lampe einer Stimmung (auf-20261020-293, Punkt 2): harte Sonne oder weiche Lampe.

    Richtung, Stärke, Winkel und Farbe rechnet ``stimmung.lampe_aus_himmel`` (reine Rechnung,
    ohne Blender); hier wird sie nur gestellt. Die Sonne kommt aus GENAU der Richtung der
    Scheibe im Himmelsbild, gedreht wie das Bild (``--umgebung-drehung``) — tiefe Sonne am
    Morgen und Abend gibt Streiflicht. Ohne Scheibe (bedeckt, Nebel, blaue Stunde, Studio)
    eine weiche Lampe mit grossem Winkel aus dem hellsten Bereich.
    """
    modul = _stimmung_modul()
    analyse = (umgebung or {}).get("himmel_sonne") or {}
    if not analyse.get("richtung_bild"):
        analyse = dict(RUECKFALL_HIMMEL_SONNE)
    toenung = (umgebung or {}).get("toenung")
    staerke = float((umgebung or {}).get("staerke") or 1.0)
    drehung = float((umgebung or {}).get("drehung_grad") or 0.0)
    if modul is None:
        return None, {"weg": "rueckfall", "bestellt": (), "lampe": None,
                      "grund": "aiimaging.stimmung ist von hier nicht lesbar — keine Lampe."}
    lampe = modul.lampe_aus_himmel(analyse, licht, drehung_grad=drehung, staerke=staerke,
                                   toenung=toenung)
    # WIE WEIT NEBEN DER BLICKACHSE (auf-20261020-294, B1) — 294 zaehlte es von Hand nach.
    kamera_azimut = ((umgebung or {}).get("drehung") or {}).get("kamera_azimut_grad")
    neben_achse = (modul.winkel_zur_blickachse(lampe["azimut_welt_grad"], kamera_azimut)
                   if kamera_azimut is not None and hasattr(modul, "winkel_zur_blickachse")
                   else None)
    daten = bpy.data.lights.new("Sonne", type="SUN")
    daten.energy = float(lampe["energie"])
    daten.angle = math.radians(float(lampe["winkel_grad"]))
    daten.color = tuple(lampe["farbe"])
    objekt = bpy.data.objects.new("Sonne", daten)
    bpy.context.scene.collection.objects.link(objekt)
    objekt.location = (mitte[0], mitte[1], mitte[2] + spanne * 2.0)
    euler = modul.euler_fuer_richtung(lampe["richtung_welt"])
    objekt.rotation_euler = euler
    return objekt, {"weg": "himmelsbild_" + lampe["art"], "bestellt": (),
                    "hoehe_grad": lampe["hoehe_grad"], "azimut_grad": lampe["azimut_welt_grad"],
                    "konvention": "blender_welt_x_gegen_uhrzeiger", "euler": list(euler),
                    "staerke": lampe["energie"], "winkel_grad": lampe["winkel_grad"],
                    "farbe_linear": lampe["farbe"], "lampe": lampe,
                    "drehung_grad": drehung,
                    "drehung_weg": ((umgebung or {}).get("drehung") or {}).get("weg"),
                    "winkel_zur_blickachse_grad": neben_achse,
                    "grund": lampe["grund"]}


def _sonne_setzen(mitte, spanne: float, a=None, umgebung=None):
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
    if getattr(a, "umgebung_hdr", None) and not _sonne_bestellt(a):
        # SEIT auf-20261020-293: MIT DEN LICHTDATEN DER STIMMUNG EINE LAMPE AUS DEM BILD.
        # Das Himmelsbild bleibt Fuelllicht (seine Sonnenscheibe gekappt, `_welt_setzen`),
        # die Lampe kommt aus der Richtung seiner Sonne — kein doppeltes Licht.
        licht = _licht_der_stimmung(a)
        if licht is not None:
            return _lampe_der_stimmung(mitte, spanne, a, licht, umgebung)
        # MIT HIMMELSBILD KEINE SONNENLAMPE (Entscheid 110): Das Bild traegt seine Sonne
        # selbst; beide zusammen gaeben doppeltes Licht. Eine bestellte Sonne bleibt.
        return None, {"weg": "himmelsbild", "bestellt": (), "hoehe_grad": None,
                      "azimut_grad": None, "konvention": None, "euler": None,
                      "grund": ("Keine Sonnenlampe: Das Himmelsbild der Stimmung traegt "
                                "das Licht, und render.sun war nicht bestellt.")}
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
    # DAS LICHT DER SONNE (B161, 24.09.2026). Geprüft in `aiimaging.sonne.licht` —
    # dieselben Grenzen wie ihr Vertrag. Unbrauchbar heisst hier: feste Werte behalten
    # und den Grund in den Bericht, wie beim Stand.
    licht_befund = {"staerke": licht.energy, "winkel_grad": math.degrees(licht.angle),
                    "kelvin": None, "farbe_linear": None, "licht_bestellt": (),
                    "licht_grund": ""}
    try:
        bestellt = modul.licht(getattr(a, "sonne_staerke", None),
                               getattr(a, "sonne_kelvin", None),
                               getattr(a, "sonne_winkel", None))
    except (modul.SonnenError, AttributeError) as fehler:
        licht_befund["licht_grund"] = f"Bestelltes Sonnenlicht nicht gesetzt: {fehler}"
    else:
        if bestellt["staerke"] is not None:
            licht.energy = bestellt["staerke"]
        if bestellt["winkel_grad"] is not None:
            licht.angle = math.radians(bestellt["winkel_grad"])
        if bestellt["farbe_linear"] is not None:
            licht.color = bestellt["farbe_linear"]
        licht_befund.update(staerke=licht.energy, winkel_grad=math.degrees(licht.angle),
                            kelvin=bestellt["kelvin"],
                            farbe_linear=(list(bestellt["farbe_linear"])
                                          if bestellt["farbe_linear"] else None),
                            licht_bestellt=list(bestellt["licht_bestellt"]))
    return objekt, dict(befund, weg=weg, euler=list(befund["euler"]), grund="",
                        **licht_befund)


# --------------------------------------------------------------------------------------
# Kontext — ein Splat als Umgebung (Owner-Entscheid 76, 08.10.2026)
# --------------------------------------------------------------------------------------
#
# **Sichtbar, aber nicht gemessen.** Der Splat steht in Beauty und Tiefe; Hüllbox,
# Kamera und Bauwerksmaske sehen ihn nicht. Das ist an drei Stellen gesichert:
#
# 1. **Reihenfolge.** Er wird erst NACH Hüllbox und Kamera geladen (siehe `main`). Rahmung,
#    Sichtprüfung der Kamera (`_sicht_frei`) und Sonnenstand sind dann schon gerechnet —
#    mit der Szene, wie sie ohne Splat wäre.
# 2. **Marke.** Das Objekt trägt :data:`KONTEXT_MARKE`; `_bbox_aller_meshes`,
#    `_bbox_bauwerk`, die Meshzählung und `_material_id_zuweisen` lassen es aus. Die Marke
#    schützt, falls jemand die Reihenfolge einmal ändert.
# 3. **Eigene Kennung.** Im Material-ID-Pass bekommt er einen Eintrag mit
#    ``quelle: "kontext"`` — als LETZTEN, damit jede Kennfarbe des Modells dieselbe bleibt
#    wie ohne Splat. ``aiimaging.maske`` nimmt solche Einträge vor jeder Regel heraus.
#
# **Verdecken darf er.** Steht Splat-Geometrie zwischen Kamera und Bauwerk, verdeckt sie es
# in Tiefe, Beauty und Maske — so sieht die Kamera es auch. Wieviel, misst
# `_verdeckung_messen` und meldet es im Bericht.


def _kontext_laden(a) -> tuple:
    """Den Splat einlesen, zu Punkten machen, einfärben und in die Welt des Modells legen.

    Returns:
        ``(objekt, setze_material_knoten, befund)``. Der Knoten ist der «Set Material» der
        Geometry Nodes — der Material-ID-Pass tauscht dort das Material.

    Wie gerechnet wird (die Zahlen stehen in ``aiimaging.kontext``, GESETZT):

    * **Punkte:** jeder Gaussian wird ein Punkt («Mesh to Points»), Cycles rendert ihn
      als Kugel. Verworfen wird, was unter ``DECKKRAFT_MIN`` liegt
      (``sigmoid(opacity)``), und was nicht endlich ist.
    * **Farbe:** SH-Grad 0, ``rgb = clamp(0,5 + SH_C0 · f_dc)``. Der Wert ist eine
      Bildfarbe (sRGB); als Emission wird er linear gesetzt, damit im PNG dieselbe Farbe
      steht. Emission und nicht Principled: Die Farbe eines Splats IST schon das Licht der
      Aufnahme; noch einmal beleuchtet, sähe er doppelt belichtet aus.
    * **Radius:** Mittel der zwei grössten ``exp(scale_i)``, mit dem Massstab der Matrix in Meter
      der Welt gerechnet und auf ``[RADIUS_MIN_M, RADIUS_MAX_M]`` gekappt.
    * **Lage:** ``kontext.matrix_nach_blender`` — die Matrix gilt in der glTF-Welt, und der
      Splat bekommt dieselbe Drehung wie das Modell beim Import.

    Raises:
        RuntimeError: Modul nicht erreichbar, Datei unlesbar, Spalten fehlen, nichts übrig.
            **Abbruch statt leerem Bild:** Wer einen Splat bestellt und ein Bild ohne
            bekommt, hält es für eines mit.
    """
    import mathutils
    import numpy as np                                   # mit Blender ausgeliefert

    kx = _kontext_modul()
    if kx is None:
        raise RuntimeError(
            "aiimaging.kontext ist von hier nicht lesbar, und der Kontext braucht von dort "
            "Lage, Schwellen und Fingerabdruck. Ohne sie wird kein Splat geladen — ein "
            "geratener Achsentausch legte ihn auf die Seite.")
    pfad = Path(a.kontext_ply)
    # DAS NETZ AUS DER SPLAT-BRUECKE (Owner-Entscheid 79, 13.10.2026): Traegt die Datei
    # Flaechen, ist sie ein Netz und wird wie ein Objekt geladen. Erkannt am PLY-Kopf
    # (`element face`), nicht am Namen und nicht an einem Schalter — ein Schalter, der zur
    # Datei nicht passt, legte ein Netz als Punktwolke an oder umgekehrt.
    kn = _kontext_netz_modul()
    if kn is not None and kn.art_der_datei(pfad) == "netz":
        return _kontext_netz_laden(a, kx, kn)
    befund = {"quelle": "splat-ply", **kx.fingerabdruck(pfad)}
    roh_matrix = None
    if getattr(a, "kontext_matrix", None):
        roh_matrix = [float(t) for t in str(a.kontext_matrix).split(",")]
    m_blender = kx.matrix_nach_blender(roh_matrix,
                                       z_up_quelle=bool(getattr(a, "rotiere_z_up", False)))
    welt = mathutils.Matrix([m_blender[4 * z:4 * z + 4] for z in range(4)])
    massstab = kx.matrix_massstab(m_blender)

    vorher = set(bpy.data.objects)
    # Achsen ausdrücklich als Einheit: Der PLY-Import dreht sonst nach seinen Vorgaben,
    # und die Lage hängt allein an der Matrix.
    bpy.ops.wm.ply_import(filepath=str(pfad), forward_axis="Y", up_axis="Z",
                          global_scale=1.0)
    neu = [o for o in bpy.data.objects if o not in vorher]
    if len(neu) != 1 or neu[0].type != "MESH":
        raise RuntimeError(f"Der PLY-Import von {pfad.name!r} ergab {len(neu)} Objekt(e) "
                           f"statt eines Meshes.")
    roh = neu[0]
    netz = roh.data
    n = len(netz.vertices)
    fehlend = [s for s in KONTEXT_SPALTEN if s not in netz.attributes]
    if fehlend:
        raise RuntimeError(
            f"{pfad.name!r} ist kein 3DGS-Splat: Es fehlen {fehlend}. Eine gewöhnliche "
            f"Punktwolke hat keine Deckkraft und keine Skala; was hier daraus würde, wäre "
            f"geraten.")

    def spalte(name):
        werte = np.empty(n, dtype=np.float32)
        netz.attributes[name].data.foreach_get("value", werte)
        return werte.astype(np.float64)

    lage = np.empty(n * 3, dtype=np.float32)
    netz.vertices.foreach_get("co", lage)
    lage = lage.reshape(n, 3).astype(np.float64)
    f_dc = np.stack([spalte(f"f_dc_{i}") for i in range(3)], axis=1)
    skala = np.stack([spalte(f"scale_{i}") for i in range(3)], axis=1)
    with np.errstate(over="ignore", invalid="ignore"):
        deckkraft = 1.0 / (1.0 + np.exp(-spalte("opacity")))
        radius_splat = np.sort(np.exp(skala), axis=1)[:, 1:].mean(axis=1)
    endlich = (np.isfinite(lage).all(axis=1) & np.isfinite(f_dc).all(axis=1)
               & np.isfinite(radius_splat) & np.isfinite(deckkraft))
    dicht = deckkraft >= kx.DECKKRAFT_MIN
    behalten = endlich & dicht
    k = int(behalten.sum())
    n_rest = sum(1 for at in netz.attributes if at.name.startswith("f_rest_"))
    bpy.data.objects.remove(roh, do_unlink=True)
    bpy.data.meshes.remove(netz)
    if k == 0:
        raise RuntimeError(
            f"Vom Splat {pfad.name!r} bleibt nichts: {n} Punkte gelesen, alle unter der "
            f"Deckkraft {kx.DECKKRAFT_MIN} oder nicht endlich.")

    farbe = np.clip(0.5 + kx.SH_C0 * f_dc[behalten], 0.0, 1.0)
    linear = np.where(farbe <= 0.04045, farbe / 12.92, ((farbe + 0.055) / 1.055) ** 2.4)
    rgba = np.concatenate([linear, np.ones((k, 1))], axis=1)
    welt_radius = radius_splat[behalten] * massstab
    gekappt = np.clip(welt_radius, kx.RADIUS_MIN_M, kx.RADIUS_MAX_M)

    netz = bpy.data.meshes.new(KONTEXT_OBJEKT)
    netz.vertices.add(k)
    netz.vertices.foreach_set("co", lage[behalten].astype(np.float32).ravel())
    attr = netz.attributes.new(KONTEXT_FARBE, "FLOAT_COLOR", "POINT")
    attr.data.foreach_set("color", rgba.astype(np.float32).ravel())
    attr = netz.attributes.new(KONTEXT_RADIUS, "FLOAT", "POINT")
    # Der Radius steht im Objektraum; die Matrix skaliert ihn danach wieder auf Weltmass.
    attr.data.foreach_set("value", (gekappt / massstab).astype(np.float32))
    obj = bpy.data.objects.new(KONTEXT_OBJEKT, netz)
    bpy.context.scene.collection.objects.link(obj)
    obj[KONTEXT_MARKE] = True
    obj.matrix_world = welt
    # Er leuchtet nicht auf das Modell und spiegelt sich nicht darin: Emission mit der
    # Stärke 1 wäre sonst eine Lichtquelle aus Tausenden Kugeln. Schatten wirft er.
    for strahl in ("visible_diffuse", "visible_glossy", "visible_transmission",
                   "visible_volume_scatter"):
        if hasattr(obj, strahl):
            setattr(obj, strahl, False)

    material = bpy.data.materials.new("KONTEXT_Splat")
    material.use_nodes = True
    baum = material.node_tree
    baum.nodes.clear()
    attribut = baum.nodes.new("ShaderNodeAttribute")
    attribut.attribute_type = "GEOMETRY"
    attribut.attribute_name = KONTEXT_FARBE
    emission = baum.nodes.new("ShaderNodeEmission")
    emission.inputs["Strength"].default_value = 1.0
    ausgang = baum.nodes.new("ShaderNodeOutputMaterial")
    baum.links.new(attribut.outputs["Color"], emission.inputs["Color"])
    baum.links.new(emission.outputs["Emission"], ausgang.inputs["Surface"])

    gruppe = bpy.data.node_groups.new("Kontext_Punkte", "GeometryNodeTree")
    gruppe.interface.new_socket(name="Geometry", in_out="INPUT",
                                socket_type="NodeSocketGeometry")
    gruppe.interface.new_socket(name="Geometry", in_out="OUTPUT",
                                socket_type="NodeSocketGeometry")
    rein = gruppe.nodes.new("NodeGroupInput")
    raus = gruppe.nodes.new("NodeGroupOutput")
    zu_punkten = gruppe.nodes.new("GeometryNodeMeshToPoints")
    zu_punkten.mode = "VERTICES"
    radius = gruppe.nodes.new("GeometryNodeInputNamedAttribute")
    radius.data_type = "FLOAT"
    radius.inputs["Name"].default_value = KONTEXT_RADIUS
    setze = gruppe.nodes.new("GeometryNodeSetMaterial")
    setze.inputs["Material"].default_value = material
    gruppe.links.new(rein.outputs[0], zu_punkten.inputs["Mesh"])
    gruppe.links.new(radius.outputs["Attribute"], zu_punkten.inputs["Radius"])
    gruppe.links.new(zu_punkten.outputs["Points"], setze.inputs["Geometry"])
    gruppe.links.new(setze.outputs["Geometry"], raus.inputs[0])
    modifikator = obj.modifiers.new("Kontext_Punkte", "NODES")
    modifikator.node_group = gruppe

    # Hüllbox der behaltenen Mittelpunkte in der Welt — gegen sie prüft die Probe die Lage.
    m = np.array(m_blender, dtype=np.float64).reshape(4, 4)
    punkte_welt = lage[behalten] @ m[:3, :3].T + m[:3, 3]
    befund.update({
        "punkte_gelesen": n,
        "punkte_gerendert": k,
        "verworfen_deckkraft": int((endlich & ~dicht).sum()),
        "verworfen_ungueltig": int((~endlich).sum()),
        "deckkraft_schwelle": kx.DECKKRAFT_MIN,
        "farbe": "SH-Grad 0: clamp(0.5 + SH_C0 * f_dc), als Emission; f_rest nicht gelesen",
        "f_rest_spalten_ignoriert": n_rest,
        "radius_m": {
            "regel": ("Mittel der zwei groessten exp(scale_i), mal Massstab der Matrix, "
                      "gekappt"),
            "untergrenze": kx.RADIUS_MIN_M, "obergrenze": kx.RADIUS_MAX_M,
            "min": round(float(gekappt.min()), 6), "max": round(float(gekappt.max()), 6),
            "median": round(float(np.median(gekappt)), 6),
            "gekappt_unten": int((welt_radius < kx.RADIUS_MIN_M).sum()),
            "gekappt_oben": int((welt_radius > kx.RADIUS_MAX_M).sum()),
        },
        "matrix_angewandt": roh_matrix is not None,
        "matrix_bedeutung": ("4x4 zeilenweise, glTF-Welt (Meter, Y oben); in Blender: "
                             "[Z-up-Korrektur] * R_x(+90) * M"),
        "matrix_blender": [round(w, 9) for w in m_blender],
        # Mittelpunkte, ohne Radius — dieselbe Welt wie `bbox` (Blender, Z oben).
        "huellbox": [[round(float(v), 6) for v in punkte_welt.min(axis=0)],
                     [round(float(v), 6) for v in punkte_welt.max(axis=0)]],
        "zaehlt_zur_bauwerksbox": False,
        "zaehlt_zur_rahmung": False,
    })
    return obj, setze, befund


#: Eigenschaft am Kontext-Objekt: wie viele Materialien es in ``bpy.data`` gebracht hat. Der
#: Splat und die PLY bringen eines, das texturierte OBJ eines je Bild. Ohne die Zahl stiege
#: ``n_materialien`` des Berichts mit der Umgebung — und der Bericht sprach vom Modell.
KONTEXT_MATERIALZAHL = "aiimaging_kontext_materialien"


def _kontext_materialzahl(obj) -> int:
    """Wie viele Materialien der Kontext mitgebracht hat (ohne Angabe: eines, wie bisher)."""
    try:
        return int(obj.get(KONTEXT_MATERIALZAHL, 1))
    except (TypeError, ValueError):
        return 1


def _kontext_textur_materialien(obj, materialien_vorher, pfad) -> tuple:
    """Die Materialien des OBJ-Imports zu **Emission 1 aus der Bildtextur** umbauen.

    **Emission mit der Stärke 1**, aus demselben Grund wie bei Splat und Eckfarben: Die Textur
    IST das Licht der Aufnahme; beleuchtet (etwa ein Teil Selbstleuchten plus Sonne) sähe sie
    doppelt belichtet aus oder, im Schatten der Sonne, dunkler als fotografiert. Die
    HomeStation hat Emission 1 als scharf und farbtreu gesehen (14.10.2026). Das Bild liest
    Blender als sRGB und rechnet es linear; als Emission gesetzt steht im PNG wieder die Farbe
    der Textur.

    Gebaut wird **in den vorhandenen Materialien** (je ``usemtl`` eines, wie der Import sie
    anlegt) — keine zusätzlichen: ``n_materialien`` zählt so nur, was der Import brachte
    (:data:`KONTEXT_MATERIALZAHL`). Ein Material ohne Bild wird neutrales Grau, gesagt im Befund.

    Returns:
        ``(None, textur)`` — kein Material für den «Set Material» (er wählt im Beauty nichts
        aus), und ``textur = {materialien, bilder, ohne_bild, groessen}`` für den Befund.
    """
    netz = obj.data
    bilder: list = []
    ohne_bild = 0
    for k, slot in enumerate(obj.material_slots):
        mat = slot.material
        if mat is None:
            continue
        if mat in materialien_vorher:
            # Nie ein Material des MODELLS umbauen — sollte der Import eines nach Namen
            # wiederverwenden, bekommt die Umgebung eine Kopie (das Beauty des Bauwerks
            # bleibt, wie es war).
            mat = mat.copy()
            slot.material = mat
        bild = None
        if mat.use_nodes and mat.node_tree is not None:
            bild = next((n.image for n in mat.node_tree.nodes
                         if n.type == "TEX_IMAGE" and n.image is not None), None)
        mat.name = f"KONTEXT_Textur_{k:02d}"
        mat.use_nodes = True
        baum = mat.node_tree
        baum.nodes.clear()
        emission = baum.nodes.new("ShaderNodeEmission")
        emission.inputs["Strength"].default_value = 1.0
        ausgang = baum.nodes.new("ShaderNodeOutputMaterial")
        if bild is not None:
            knoten = baum.nodes.new("ShaderNodeTexImage")
            knoten.image = bild
            knoten.interpolation = "Linear"
            # Am Rand jeder Kachel nicht auf die gegenüberliegende Seite greifen: Die Fuge
            # der Abwicklung ist 2 Bildpunkte breit.
            knoten.extension = "EXTEND"
            baum.links.new(knoten.outputs["Color"], emission.inputs["Color"])
            if bild not in bilder:
                bilder.append(bild)
        else:
            ohne_bild += 1
            emission.inputs["Color"].default_value = (0.2, 0.2, 0.2, 1.0)
        baum.links.new(emission.outputs["Emission"], ausgang.inputs["Surface"])
    if not len(netz.materials):
        # Ein OBJ ganz ohne Material: ein graues, damit die Umgebung nicht rosa erscheint.
        mat = bpy.data.materials.new("KONTEXT_Textur_00")
        mat.use_nodes = True
        baum = mat.node_tree
        baum.nodes.clear()
        emission = baum.nodes.new("ShaderNodeEmission")
        emission.inputs["Color"].default_value = (0.2, 0.2, 0.2, 1.0)
        ausgang = baum.nodes.new("ShaderNodeOutputMaterial")
        baum.links.new(emission.outputs["Emission"], ausgang.inputs["Surface"])
        netz.materials.append(mat)
        ohne_bild += 1
    groessen = []
    for b in bilder:
        try:
            groessen.append([int(b.size[0]), int(b.size[1])])
        except Exception:                                  # noqa: BLE001 — nur Befund
            groessen.append(None)
    return None, {"materialien": len(netz.materials), "bilder": len(bilder),
                  "ohne_bild": ohne_bild, "groessen": groessen,
                  "schattierung": "Emission 1 aus der Bildtextur"}


def _kontext_netz_laden(a, kx, kn) -> tuple:
    """Das Netz aus der Splat-Brücke als Umgebung laden (Owner-Entscheid 79, 13.10.2026).

    Dieselben Zusagen wie der Kugel-Weg, damit alles danach dieselbe Szene sieht:
    **dieselbe Matrix** (``kontext.matrix_nach_blender`` — das Netz steht im System des
    Splats), **dieselbe Marke** :data:`KONTEXT_MARKE` (aus Hüllbox, Bauwerksbox, Meshzählung
    und Material-ID-Zuweisung ausgeschlossen), **dieselbe Kennung** im Material-ID-Pass
    (``quelle: "kontext"``, über einen «Set Material»-Knoten wie beim Splat, damit
    :func:`_material_id_zuweisen` unverändert tauschen kann).

    **Emission aus der Eckpunktfarbe**, aus demselben Grund wie beim Splat: Die Farbe ist das
    Licht der Aufnahme; noch einmal beleuchtet, sähe die Umgebung doppelt belichtet aus. Der
    PLY-Import von Blender 4.2 liest die Farbe als sRGB und legt sie linear ab (hier
    nachgesehen: 200 → 0,5776) — als Emission gesetzt steht im PNG wieder die Farbe der Datei.

    **Das texturierte OBJ** (Fassung 3 der RealityScan-Brücke, 14.10.2026): Import mit
    ``wm.obj_import`` (ein Objekt, Achsen als Einheit wie die PLY), dann **Emission 1 aus der
    Bildtextur** je Material (:func:`_kontext_textur_materialien`). Der «Set Material» bleibt
    für den Material-ID-Pass, wählt im Beauty aber nichts aus — sonst ersetzte er die Textur.

    Returns:
        ``(objekt, setze_material_knoten, befund)`` wie :func:`_kontext_laden`.
    """
    import mathutils
    import numpy as np                                   # mit Blender ausgeliefert

    pfad = Path(a.kontext_ply)
    befund = {"quelle": kn.QUELLE_NETZ, **kx.fingerabdruck(pfad)}
    roh_matrix = None
    if getattr(a, "kontext_matrix", None):
        roh_matrix = [float(t) for t in str(a.kontext_matrix).split(",")]
    m_blender = kx.matrix_nach_blender(roh_matrix,
                                       z_up_quelle=bool(getattr(a, "rotiere_z_up", False)))
    welt = mathutils.Matrix([m_blender[4 * z:4 * z + 4] for z in range(4)])

    vorher = set(bpy.data.objects)
    materialien_vorher = set(bpy.data.materials)
    # DAS TEXTURIERTE NETZ (Fassung 3 der RealityScan-Bruecke, 14.10.2026) kommt als OBJ mit
    # MTL und Bildern daneben. Erkannt am Inhalt (`kontext_netz.ist_obj`), nicht am Schalter.
    ist_obj = bool(getattr(kn, "ist_obj", None)) and kn.ist_obj(pfad)
    if ist_obj:
        # Achsen ausdrücklich als Einheit, wie bei der PLY — sonst drehte der OBJ-Import nach
        # seiner Vorgabe (−Z vorn, Y oben) ein zweites Mal. Die Exportdatei von RealityScan
        # dreht um 90° um X (`settingsRotation`) und gibt so die Koordinaten der Aufnahme
        # zurück, im System des Splats — dieselbe Lage wie die PLY von Fassung 2; in die Welt
        # legt es wie dort allein die Matrix. Ein Objekt, nicht eines je `o`/`g`: Marke,
        # Matrix und «Set Material» gelten dem Ganzen.
        bpy.ops.wm.obj_import(filepath=str(pfad), forward_axis="Y", up_axis="Z",
                              global_scale=1.0, use_split_objects=False,
                              use_split_groups=False)
    else:
        # Achsen ausdrücklich als Einheit, wie beim Splat: Die Lage hängt allein an der Matrix.
        bpy.ops.wm.ply_import(filepath=str(pfad), forward_axis="Y", up_axis="Z",
                              global_scale=1.0, import_colors="SRGB")
    neu = [o for o in bpy.data.objects if o not in vorher]
    if len(neu) != 1 or neu[0].type != "MESH":
        raise RuntimeError(f"Der {'OBJ' if ist_obj else 'PLY'}-Import von {pfad.name!r} ergab "
                           f"{len(neu)} Objekt(e) statt eines Netzes.")
    obj = neu[0]
    obj.name = KONTEXT_NETZ_OBJEKT
    netz = obj.data
    if len(netz.polygons) == 0:
        raise RuntimeError(f"{pfad.name!r} trägt nach dem Import keine Flächen.")
    obj[KONTEXT_MARKE] = True
    obj.matrix_world = welt
    for strahl in ("visible_diffuse", "visible_glossy", "visible_transmission",
                   "visible_volume_scatter"):
        if hasattr(obj, strahl):
            setattr(obj, strahl, False)

    textur = None
    if ist_obj:
        material, textur = _kontext_textur_materialien(obj, materialien_vorher, pfad)
        farbattribut = None
    else:
        farbattribut = netz.color_attributes[0].name if len(netz.color_attributes) else None
        material = bpy.data.materials.new("KONTEXT_Netz")
        material.use_nodes = True
        baum = material.node_tree
        baum.nodes.clear()
        emission = baum.nodes.new("ShaderNodeEmission")
        emission.inputs["Strength"].default_value = 1.0
        ausgang = baum.nodes.new("ShaderNodeOutputMaterial")
        if farbattribut is not None:
            attribut = baum.nodes.new("ShaderNodeAttribute")
            attribut.attribute_type = "GEOMETRY"
            attribut.attribute_name = farbattribut
            baum.links.new(attribut.outputs["Color"], emission.inputs["Color"])
        else:
            # Ohne Eckpunktfarbe ein neutrales Grau — und gesagt, im Befund unten.
            emission.inputs["Color"].default_value = (0.2, 0.2, 0.2, 1.0)
        baum.links.new(emission.outputs["Emission"], ausgang.inputs["Surface"])
        netz.materials.clear()
    # Wie viele Materialien die Umgebung in `bpy.data` gebracht hat — die Zahl der
    # Materialien im Bericht ist die des MODELLS (`_kontext_materialzahl`).
    obj[KONTEXT_MATERIALZAHL] = len(set(bpy.data.materials) - materialien_vorher)

    gruppe = bpy.data.node_groups.new("Kontext_Netz", "GeometryNodeTree")
    gruppe.interface.new_socket(name="Geometry", in_out="INPUT",
                                socket_type="NodeSocketGeometry")
    gruppe.interface.new_socket(name="Geometry", in_out="OUTPUT",
                                socket_type="NodeSocketGeometry")
    rein = gruppe.nodes.new("NodeGroupInput")
    raus = gruppe.nodes.new("NodeGroupOutput")
    setze = gruppe.nodes.new("GeometryNodeSetMaterial")
    setze.inputs["Material"].default_value = material
    if textur is not None:
        # DIE TEXTUR SITZT IN DEN SLOTS — je Bild ein Material. Der «Set Material» ersetzte sie
        # alle durch eines; darum waehlt er im Beauty NICHTS aus und erst der Material-ID-Pass
        # schaltet ihn ein (`_material_id_zuweisen`, «Selection» an).
        setze.inputs["Selection"].default_value = False
    gruppe.links.new(rein.outputs[0], setze.inputs["Geometry"])
    gruppe.links.new(setze.outputs["Geometry"], raus.inputs[0])
    modifikator = obj.modifiers.new("Kontext_Netz", "NODES")
    modifikator.node_group = gruppe

    n = len(netz.vertices)
    lage = np.empty(n * 3, dtype=np.float32)
    netz.vertices.foreach_get("co", lage)
    lage = lage.reshape(n, 3).astype(np.float64)
    m = np.array(m_blender, dtype=np.float64).reshape(4, 4)
    punkte_welt = lage @ m[:3, :3].T + m[:3, 3]
    befund.update({
        "ecken": n,
        "dreiecke": int(sum(len(p.vertices) - 2 for p in netz.polygons)),
        "punkte_gelesen": None,
        "punkte_gerendert": None,
        "format": "obj" if ist_obj else "ply",
        "farbe": ("Textur als Emission (Staerke 1, sRGB des Bildes)" if textur is not None
                  and textur["bilder"]
                  else "keine Textur in der Datei — neutrales Grau als Emission" if ist_obj
                  else "Eckpunktfarbe als Emission (sRGB der Datei)" if farbattribut
                  else "keine Eckpunktfarbe in der Datei — neutrales Grau als Emission"),
        "textur": textur,
        "matrix_angewandt": roh_matrix is not None,
        "matrix_bedeutung": ("4x4 zeilenweise, glTF-Welt (Meter, Y oben); in Blender: "
                             "[Z-up-Korrektur] * R_x(+90) * M"),
        "matrix_blender": [round(w, 9) for w in m_blender],
        # Ecken des Netzes — dieselbe Welt wie `bbox` (Blender, Z oben).
        "huellbox": [[round(float(v), 6) for v in punkte_welt.min(axis=0)],
                     [round(float(v), 6) for v in punkte_welt.max(axis=0)]],
        "zaehlt_zur_bauwerksbox": False,
        "zaehlt_zur_rahmung": False,
    })
    return obj, setze, befund


#: Name der Material-ID ohne Kontext — derselbe Durchgang, der Splat ausgeblendet.
MATERIAL_ID_OHNE_KONTEXT = "material_id_ohne_kontext.png"


def _verdeckung_messen(ohne_png: Path, mit_png: Path) -> dict:
    """Wieviele Bildpunkte des MODELLS der Splat verdeckt — aus zwei Material-ID-Bildern.

    Ein Modellpunkt ist einer, der ohne Splat nicht schwarz ist (Bauwerk und Gelände des
    Modells). Verdeckt ist er, wenn derselbe Punkt mit Splat eine andere Kennfarbe trägt:
    Eine andere Farbe an dieser Stelle kann nur der Splat davor sein. Billig, weil der
    Material-ID-Pass ein Sample ohne Lichtwege ist.
    """
    import numpy as np

    def lies(pfad):
        bild = bpy.data.images.load(str(pfad), check_existing=False)
        try:
            b, h = bild.size
            werte = np.empty(b * h * bild.channels, dtype=np.float32)
            bild.pixels.foreach_get(werte)
            return np.rint(werte.reshape(h * b, bild.channels)[:, :3] * 255.0).astype(int)
        finally:
            bpy.data.images.remove(bild)

    ohne, mit = lies(ohne_png), lies(mit_png)
    modell = ohne.any(axis=1)
    verdeckt = modell & (ohne != mit).any(axis=1)
    n_modell, n_verdeckt = int(modell.sum()), int(verdeckt.sum())
    return {"modellpunkte_ohne_kontext": n_modell, "davon_verdeckt": n_verdeckt,
            "anteil": (round(n_verdeckt / n_modell, 6) if n_modell else None),
            "grund": ("Modellpunkte = nicht schwarz im Material-ID-Pass ohne Splat (Bauwerk "
                      "und Gelaende des Modells); verdeckt = dort mit Splat eine andere "
                      "Kennfarbe.")}


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


#: Knotennamen aus unserer IFC-Umwandlung: ``IfcWall_Wand-Sued_<GlobalId>`` (siehe
#: ``ifc_to_glb_runner._knotenname``), ein geteiltes Bauteil mit Anhang ``_1``.
IFC_KNOTEN = re.compile(r"^Ifc[A-Z][A-Za-z0-9]*_")


def _ist_ifc_knoten(name: str) -> bool:
    """Stammt ein Objekt aus unserer IFC-Umwandlung? — am Namen, denn nur er überlebt
    den glb-Export."""
    return bool(IFC_KNOTEN.match(str(name)))


def _material_id_modul():
    """``aiimaging.material_id`` von hier aus — dieselbe Bauart wie :func:`_maske_modul`.

    Anders als dort gibt es KEINEN Rueckfall: Ohne Plan keine Kennungen, und eine zweite,
    alte Planung hier waere genau der Fehler aus auf-20261021-316. Fehlt das Modul, scheitert
    der Material-ID-Pass laut.
    """
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from aiimaging import material_id                       # noqa: PLC0415
    return material_id


def _material_id_zuweisen(kontext=None) -> tuple[list[dict], int]:
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
    Trägt ein Mesh gar kein Material, bekommt es **objektweise** eine eigene ID — teilen
    sich mehrere Objekte ein Mesh, **eine je Mesh** (seit auf-20261021-316, siehe
    :mod:`aiimaging.material_id`; ein Material bekommt ohnehin eine Kennung, nie eine je
    Objekt). Sonst
    verschmölze eine materiallose Szene zu einer einzigen Fläche. Bis zum 08.10.2026 war
    das der Normalfall der Kette: `ifc_to_glb_runner.py` übertrug nur Geometrie. Seither
    übernimmt er die `IfcSurfaceStyle` der Datei (F6) — aber nur sie; ein Bauteil ohne
    Stil kommt weiter ohne Material an, und eine Datei ganz ohne Stile ergibt dieselbe
    materiallose glb wie zuvor. Darum bleibt beides nebeneinander möglich, und die
    Herkunft steht in jedem Eintrag (`quelle`), damit niemand eine Objekt-Maske für eine
    Material-Maske hält.

    Der Kontext (Splat, 08.10.2026)
    -------------------------------
    ``kontext`` ist ``(objekt, setze_material_knoten)`` aus :func:`_kontext_laden` oder
    ``None``. Der Splat bekommt seinen Eintrag mit ``quelle: "kontext"`` **als letzten** —
    jede Kennfarbe des Modells bleibt damit dieselbe wie ohne Splat. Sein Material sitzt
    nicht in einem Slot, sondern im «Set Material» seiner Geometry Nodes und wird dort
    getauscht.
    """
    # DER PLAN STEHT VOR JEDEM EINGRIFF (auf-20261021-316, B2). Bis zum 21.10.2026 wurde hier
    # Objekt fuer Objekt geplant UND getauscht. Bei geteilten Meshes (19 600 ausgerollte
    # Backstein-Instanzen, ein Mesh) las das zweite Objekt am Mesh schon «MATID_000_backstein»
    # statt «backstein», vergab dafuer eine neue Kennung «MATID_001_MATID_000_backstein» —
    # 19 605 Eintraege, Namen bis 255 Zeichen verkettet, Kennfarben doppelt. Jetzt werden die
    # URSPRUENGLICHEN Namen zuerst gelesen und der Plan ohne Blender gerechnet
    # (`aiimaging.material_id`, eine Kennung je Material, ohne Material je Mesh); getauscht
    # wird danach.
    plan_modul = _material_id_modul()
    # Die Materialien dieses Runners (Oberflaeche, Gips) zaehlen nicht als «echte» — sie
    # ersetzen welche, die weiter in `bpy.data.materials` stehen.
    n_echte_materialien = sum(1 for m in bpy.data.materials if not m.get(MATERIAL_MARKE))
    # Nach Namen sortiert, damit zwei Läufe dieselben Indizes und damit dieselben Farben
    # vergeben. Ohne feste Reihenfolge wäre die Maske nicht reproduzierbar.
    meshes = sorted((o for o in bpy.data.objects if o.type == "MESH" and not _ist_kontext(o)),
                    key=lambda o: o.name)
    beschreibung = []
    for obj in meshes:
        # Ein Slot, den `_ersetze_slots` an ein Objekt OHNE Material gehaengt hat (leerer
        # Ursprung), zaehlt nicht als belegt: Das Objekt bleibt ein «objekt» wie zuvor.
        # Der Name des ERSETZTEN Materials, wenn eine Oberflaeche gesetzt wurde — die
        # Maske liest Namen und soll dasselbe sehen wie ohne Oberflaeche.
        slots = []
        for s in obj.material_slots:
            if s.material is None or s.material.get(URSPRUNG_MARKE, None) == "":
                slots.append(None)
            else:
                slots.append(s.material.get(URSPRUNG_MARKE) or s.material.name)
        # EIN BAUTEIL AUS UNSERER IFC BEKOMMT SEINE ID JE OBJEKT — auch mit Material
        # (Befund 08.10.2026, nach F6). Die Bauwerksmaske liest diese Tabelle: Gelaenderegel
        # und Katalog-Nullbefund arbeiten auf KNOTENnamen («IfcSlab_Gelaende_…»), nicht auf
        # Materialnamen («Beton»). Die Farben bleiben in der glb und im Beauty; nur die
        # Kennung hier bleibt, was sie vor F6 war.
        beschreibung.append({"name": obj.name, "mesh": obj.data.name, "slots": slots,
                             "ifc": _ist_ifc_knoten(obj.name)})
    plan = plan_modul.plane_material_ids(beschreibung, _id_farbe_srgb)
    tabelle: list[dict] = plan["tabelle"]
    kennung: dict[int, "bpy.types.Material"] = {
        e["index"]: _emissions_material(plan_modul.kennungsname(e["index"], e["name"]),
                                        e["farbe_srgb"])
        for e in tabelle}
    for obj in meshes:
        z = plan["zuweisung"][obj.name]
        if z["art"] == "objekt":
            if z["am_objekt"]:
                # Ein IFC-Bauteil an einem geteilten Mesh: Die Kennung haengt am OBJEKT,
                # sonst traegt das Mesh nur die des letzten Objekts.
                if not obj.material_slots:
                    obj.data.materials.append(None)
                for slot in obj.material_slots:
                    slot.link = "OBJECT"
                    slot.material = kennung[z["index"]]
            else:
                obj.data.materials.clear()
                obj.data.materials.append(kennung[z["index"]])
            continue
        for slot, index in zip(obj.material_slots, z["indizes"]):
            if index is not None:
                slot.material = kennung[index]

    def eintragen(name: str, quelle: str) -> "bpy.types.Material":
        # NUR NOCH FUER DEN KONTEXT, als letzter Eintrag — mit der naechsten freien Farbe.
        index = len(tabelle)
        belegt = {tuple(e["farbe_srgb_8bit"]) for e in tabelle}
        folge = index
        while True:
            farbe = _id_farbe_srgb(folge)
            acht = tuple(int(round(k * 255.0)) for k in farbe)
            if acht not in belegt or folge > index + plan_modul.FARBSUCHE_HOECHSTENS:
                break
            folge += 1
        tabelle.append({
            "index": index,
            "name": name,
            "quelle": quelle,
            "farbe_srgb": [round(k, 6) for k in farbe],
            "farbe_srgb_8bit": list(acht),
        })
        return _emissions_material(plan_modul.kennungsname(index, name), farbe)

    if kontext is not None:
        obj, setze = kontext
        setze.inputs["Material"].default_value = eintragen(obj.name, "kontext")
        # Beim texturierten Netz waehlt der Knoten im Beauty nichts aus (die Textur sitzt in
        # den Slots); hier gilt die Kennung fuer alle Flaechen.
        if "Selection" in setze.inputs:
            setze.inputs["Selection"].default_value = True
        # Das Material des Splats ist keines des Modells; `n_materialien` bleibt die Zahl
        # von ohne Splat (beim texturierten Netz: ohne seine Materialien je Bild).
        n_echte_materialien -= _kontext_materialzahl(obj)

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
    # CPU IST GEMESSEN, NICHT ERZWUNGEN — und der Unterschied ist der Grund dafuer,
    # dass hier ein Block steht und kein Halbsatz.
    #
    # Hier stand: «in dieser Umgebung gibt es keine GPU». Das war ein Satz ueber die
    # UMGEBUNG, und er ist nur im Entwicklungscontainer wahr. Auf der HomeStation steht
    # eine RTX 5090; dort las ihn jemand, sah eine ungenutzte Karte und haette
    # umgestellt. *Ein Kommentar, der eine falsche Tatsache behauptet, laedt zu genau
    # der Aenderung ein, die er verhindern sollte.*
    #
    # Gemessen am 06.09.2026 auf der HomeStation, n=3 je Seite, drei Konfigurationen,
    # ueber die echte Produktionsfunktion und mit OptiX auf einer Kopie ausserhalb des
    # Repos:
    #
    #   * OptiX ist bei den real genutzten 8-128 Samples auf 512 px in ALLEN drei
    #     Konfigurationen 10-35 % LANGSAMER. Der feste Anlaufaufwand uebersteigt die
    #     Ersparnis beim Rechnen.
    #   * Es wurde wirklich auf der Karte gerechnet: VRAM 631 -> 4338 MiB unter Last.
    #     Die Gegenprobe haette dem Befund widersprechen koennen und tat es nicht.
    #   * Die Ergebnisse sind NICHT gleich. Bei 876 Dreiecken weichen Kantenpixel der
    #     Material-ID-Maske ab, bis 217/255 bei 28 von 262144 Pixeln. Ein Wechsel waere
    #     also nicht nur langsamer, er wuerde auch Zahlen verschieben.
    #
    # NACHGEMESSEN AM 21.10.2026 (auf-20261021-314, Teil 8; RTX 5090, 1600 x 1000, 128 Samples,
    # Stimmung mittag mit Himmelsbild, drei Kameras, je Geraet zweimal, wieder auf einer Kopie
    # ausserhalb des Repos):
    #
    #   * Direkt gerufen ist OptiX jetzt schneller: 4,4 s je Kamera gegen 5,5-5,7 s auf der
    #     CPU (bei grossem Bild und Himmelsbild traegt die Ersparnis den Anlauf).
    #   * AUF DEM WEG DES ABHOLERS (seams.glb_zu_multipass) sind beide gleich: 7,4 s je
    #     Kamera, in beiden Laeufen. Die Ersparnis kommt im Produkt nicht an.
    #   * OptiX belegt 3,9 GB Grafikspeicher mehr (1404 -> 5256 MiB) — Speicher, den sich
    #     Blender mit dem Bildmodell teilt, das bis ~27,9 GB braucht.
    #   * Die Bilder sind jetzt gleich: Material-ID ohne einen abweichenden Bildpunkt, Tiefe
    #     hoechstens 0,03 mm, Schoenbild nur Rauschen (hoechstens 2/255).
    #
    # Der Grund fuer CPU ist damit weiter die Messung: kein Zeitgewinn am echten Weg, aber
    # 3,9 GB weniger Spielraum auf der Karte. (Die verschobenen Kantenpixel vom 06.09. sind
    # bei diesem Testbau nicht mehr aufgetreten — sie sind kein Grund mehr, der Speicher ist es.)
    szene.cycles.device = "CPU"
    szene.render.resolution_x = a.aufloesung
    szene.render.resolution_y = a.hoehe or a.aufloesung
    szene.render.resolution_percentage = 100
    # Standard statt AgX: AgX ist ein Filmlook mit weicher Kompression der Lichter. Für ein
    # Bild, das gleich wieder maschinell ausgewertet wird, ist eine nachvollziehbare
    # Zuordnung von Renderwert zu Bildwert wichtiger als ein schönes Rollover.
    # MIT HIMMELSBILD GILT ES NICHT MEHR (auf-20261020-292, B1): Dort stellt `main` danach
    # AgX/Filmic und die Belichtung der Stimmung (`_tonwerte_setzen`) — ohne Himmelsbild
    # bleibt es Wort fuer Wort hier.
    szene.view_settings.view_transform = "Standard"
    szene.view_settings.look = "None"


def _bedarf_befund() -> dict:
    """Der Block ``bedarf`` im Blender-Bericht — mit einem Satz, warum es nichts zu entscheiden gab.

    **Der Anlass ist eine leere Stelle, an der ein Satz angesagt war** (HomeStation,
    `auf-20260924-173`, Zusatz A4). Die Ansage zu Stufe 3 versprach den Satz «im Blender-/
    Render-Bericht unter bedarf.grund». Wer den Blender-Bericht öffnete, fand dort keinen
    ``bedarf`` — nur die leeren ``grund``-Felder von Sonne und Sichtlinie, die «nichts zu
    melden» heissen. Die Antwort war darum «LEER», und den Grund nannte allein das
    Abholer-Protokoll.

    **Warum der Blender-Lauf selbst keine Rechnung hat:** Cycles rechnet auf der CPU, und
    das ist gemessen, nicht erzwungen (siehe :func:`_renderparameter_setzen`). Über
    Grafikspeicher wird in dieser Stufe also nicht entschieden — es gibt keine Zahl, die
    gegen den freien Kartenspeicher gestellt würde. Das ist die dritte Antwort und keine
    Lücke: *nichts zu entscheiden* ist etwas anderes als *nicht gemeldet*, und nur ein
    Satz macht die beiden unterscheidbar.

    Dieselbe Form wie ``render._bedarfsbericht`` — alle Zahlenfelder ``None`` heisst
    **nicht bestimmt**, nie null —, damit ein Leser beide Berichte gleich liest. Der Satz
    sagt auch, wo die Entscheidung steht, die es wirklich gab: beim Bildmodell.

    Rein und ohne ``bpy``, damit eine Probe ihn diesseits der Prozessgrenze rufen kann.
    """
    return {"quelle": "nichts zu entscheiden", "summe_byte": None, "groesster_byte": None,
            "zuschlag": None, "verlangt_byte": None, "frei_byte": None,
            "spielraum_byte": None, "geraet": "cpu",
            "grund": ("Blender rechnet auf der CPU (Cycles; gemessen am 06.09.2026 und "
                      "21.10.2026: auf dem Weg des Abholers mit OptiX nicht schneller, 7,4 s "
                      "je Kamera, aber 3,9 GB mehr Grafikspeicher). "
                      "In dieser Stufe wird darum kein Grafikspeicher verteilt, und es gab "
                      "nichts zu entscheiden. Wie das BILDMODELL auf die Karte gelegt wurde, "
                      "steht im Ergebnis des Bildlaufs unter geraeteweg.bedarf.grund.")}


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
        # DIE ZAHL KOMMT AUS DEM PRODUKT, nicht aus diesem Skript. Sie stand hier als
        # Literal und trug fuenf Tage lang das falsche Vorzeichen — hinter der
        # Prozessgrenze, wo keine Probe hinreicht. In `aiimaging.contracts` haengt sie an
        # zwei Waechtern: dem Rundlauf `z_up_korrektur(import(p)) == p` und der
        # Gegenprobe, die zeigt, dass eine Massprobe den Fehler NICHT sehen kann.
        #
        # OHNE DAS MODUL WIRD ABGEBROCHEN, nicht geraten — anders als bei der Sonne, wo
        # ein Rueckfall auf die Vorgabe harmlos ist. Hier hiesse Raten entweder «Bau
        # liegt auf der Seite» oder «Bau steht auf dem Kopf», und der zweite Fall ist
        # gerade der, den keine Massprobe verraet. Ein zweiter Vorgabewert an dieser
        # Stelle waere die doppelte Vorgabe, die am 23.08. fuenf Tage lang die Kamera
        # kippen liess.
        _achsen = _achsen_modul()
        if _achsen is None:
            raise RuntimeError(
                "aiimaging.contracts ist von hier nicht lesbar, und --rotiere-z-up "
                "braucht von dort das Vorzeichen der Drehung. Ein geratener Wert waere "
                "hier teurer als ein Abbruch: Mit dem falschen steht das Bauwerk auf dem "
                "Kopf, und KEINE Massprobe zeigt es an.")
        import mathutils
        dreh = mathutils.Matrix.Rotation(
            math.radians(_achsen.DREHUNG_Z_UP_GRAD), 4, "X")
        for obj in bpy.data.objects:
            if obj.parent is None:
                obj.matrix_world = dreh @ obj.matrix_world

    lo, hi = _bbox_aller_meshes()
    # Und daneben die Box der gebauten Substanz. Sie ENTSCHEIDET hier nichts — der Runner
    # rahmt weiterhin, was ihm gesagt wird. Sie wird berichtet, damit diesseits der
    # Prozessgrenze VOR dem Bildlauf entscheidbar ist, ob die Rahmung ein Urteil zulaesst.
    bau_lo, bau_hi, bau_note, bau_schrumpfung, bau_form = _bbox_bauwerk()
    # Vor jedem Tausch der Slots lesen — danach tragen sie Ersatz- und Kennungsmaterialien.
    # Nur fuer die FORM: Der Abholer liest die Materiale nur bei «form» (Namen der Wortliste
    # findet die Maske selbst) — mit «name» (Ergebnis 334) bleibt die Liste leer wie bisher.
    bau_materialien = (_nur_dort_materialien(bau_form["gelaende_namen"])
                       if bau_form["entschieden_durch"] == "form" else [])
    # Die Kamera darf sich auf eine ANDERE Hüllbox beziehen als der Bericht: Der Bericht
    # beschreibt, was dasteht; die Kamera rahmt, was gezeigt werden soll.
    kam_lo, kam_hi = (_huellbox_aus_text(a.kamera_huellbox)
                      if getattr(a, "kamera_huellbox", None) else (lo, hi))
    _, _, _, kamera_herkunft = _kamera_setzen(kam_lo, kam_hi, a)
    # DER KONTEXT KOMMT ERST JETZT — nach Hüllbox, Bauwerksbox und Kamera. Alles, was
    # gemessen und gerahmt wird, ist damit schon gerechnet, und zwar an der Szene ohne
    # Splat. Siehe `_kontext_laden`.
    kontext = None
    kontext_befund = None
    if getattr(a, "kontext_ply", None):
        k_obj, k_setze, kontext_befund = _kontext_laden(a)
        kontext = (k_obj, k_setze)
    mitte = [(lo[i] + hi[i]) / 2.0 for i in range(3)]
    spanne = max(hi[i] - lo[i] for i in range(3)) or 1.0

    _renderparameter_setzen(a)
    szene = bpy.context.scene

    # ── Durchgang 1: Beauty + Tiefe ────────────────────────────────────────────────────
    # Umgebungsstärke 0.25 zu Sonnenstärke 2.0: gemessen, nicht geschätzt. Mit 1.0/3.0
    # lag das Bild im Mittel bei 0.83 von 1.0 — durchgehend ausgebrannt, die Fassaden
    # ohne Zeichnung. Die Schattenseite soll dunkel bleiben, ohne zuzulaufen.
    # MIT HIMMELSBILD (Entscheid 110): das Bild als Welt, Staerke und Drehung wie bestellt.
    umgebung_befund = None
    licht = _licht_der_stimmung(a) if getattr(a, "umgebung_hdr", None) else None
    # DIE BLICKRICHTUNG DIESER KAMERA (auf-20261020-294, B1): Je Kamera ein eigener
    # Blender-Lauf, also hier genau eine — das Himmelsbild dreht sich zu ihr.
    _stimmung_m = _stimmung_modul() if licht is not None else None
    kamera_azimut = (_stimmung_m.kamera_azimut_grad(kamera_herkunft.get("auge"),
                                                    kamera_herkunft.get("blick_auf"))
                     if _stimmung_m is not None and hasattr(_stimmung_m, "kamera_azimut_grad")
                     and isinstance(kamera_herkunft, dict) else None)
    if getattr(a, "umgebung_hdr", None):
        toenung = None
        if getattr(a, "umgebung_toenung", None):
            toenung = tuple(float(k) for k in str(a.umgebung_toenung).split(","))
            if len(toenung) != 3:
                raise RuntimeError(f"--umgebung-toenung braucht drei Zahlen 'r,g,b', war "
                                   f"{a.umgebung_toenung!r}.")
        umgebung_befund = _welt_setzen(
            (0.55, 0.60, 0.68),
            1.0 if a.umgebung_staerke is None else float(a.umgebung_staerke),
            hdr=a.umgebung_hdr,
            # `None` = nicht bestellt: mit Lichtdaten zur Kamera gedreht (294, B1), sonst 0.
            drehung_grad=None if a.umgebung_drehung is None else float(a.umgebung_drehung),
            toenung=toenung, licht=licht, kamera_azimut=kamera_azimut)
        # TONWERTE MIT HIMMELSBILD (auf-20261020-292, B1): AgX bzw. Filmic und die
        # Belichtung der Stimmung — nur fuer das Schoenbild, der ID-Pass stellt zurueck.
        # Seit auf-20261020-293 (Punkt 4) mit dem kontrastreicheren Look der Stimmung.
        umgebung_befund["ansicht"] = _tonwerte_setzen(
            szene, getattr(a, "umgebung_belichtung", None),
            look=(licht or {}).get("look"))
    else:
        _welt_setzen((0.55, 0.60, 0.68), 0.25)           # kühles, gleichmässiges Umgebungslicht
    _, sonne_befund = _sonne_setzen(mitte, spanne, a, umgebung=umgebung_befund)
    # DIE OBERFLAECHEN VOR DEM SCHOENBILD (Entscheid 113): «weiss» macht alles zum
    # Gipsmodell. Der ID-Pass danach vergibt seine Kennungen unter den alten Namen.
    material_befund = None
    if getattr(a, "umgebung_weiss", False):
        material_befund = _alles_weiss()
    elif getattr(a, "materialien", None):
        material_befund = _materialien_setzen(a, bau_form.get("gelaende_namen") or ())
    # GLAS SIEHT AUS WIE GLAS (Ergebnis 332): nach der Materialwahl, die Scheiben behaelt; nicht
    # beim Gipsmodell, das alles zu Gips macht.
    glas_befund = None if getattr(a, "umgebung_weiss", False) else _glas_klar()
    szene.cycles.use_denoising = True                    # 8 Samples auf CPU rauschen sichtbar
    if licht is not None and umgebung_befund is not None:
        # DIE PLATTE GRAU (auf-20261020-293, Punkt 3) — nach Gips und Materialwahl, die
        # beide das Gelaende nicht anfassen bzw. «weiss» es zu Gips machte.
        if licht.get("gelaende_grau"):
            umgebung_befund["gelaende"] = _gelaende_grau(
                licht["gelaende_grau"], bau_form.get("gelaende_namen") or ())
        # DER HINTERGRUND MIT ABSTAND ZUM HAUS (auf-20261020-293, Punkt 1): die Vorprobe,
        # bevor der Kompositor fuer die Tiefe steht und das Schoenbild rechnet.
        umgebung_befund["hintergrund_abstand"] = _hintergrund_abstimmen(
            szene, out_dir, licht, umgebung_befund, bau_form.get("gelaende_namen") or ())
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
    n_materialien = len(bpy.data.materials) - (_kontext_materialzahl(kontext[0])
                                               if kontext is not None else 0)
    material_id_png = out_dir / "material_id.png"
    if not a.ohne_material_id:
        tabelle, n_materialien = _material_id_zuweisen(kontext)
        # Der Compositor darf hier nicht mitlaufen: Er schriebe die (unveränderte) Tiefe
        # ein zweites Mal über dieselbe Datei.
        _kompositor_abschalten(szene)
        _welt_setzen((0.0, 0.0, 0.0), 0.0)               # schwarzer Grund, Farbwert 0 = "nichts"
        # DIE KENNFARBEN BRAUCHEN «STANDARD» (auf-20261020-292): Mit Himmelsbild rechnet das
        # Schoenbild mit AgX und Belichtung; beide verschoeben jede Kennfarbe, und die
        # Bauwerksmaske laese andere Namen. Zurueck, bevor der ID-Pass rechnet.
        _tonwerte_zurueck(szene)
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
        if kontext is not None:
            # ERST OHNE SPLAT, derselbe Durchgang. Das Bild ist die Gegenprobe: Es muss
            # gleich dem Material-ID-Bild eines Laufs ohne Kontext sein, und aus beiden
            # zusammen ergibt sich, was der Splat verdeckt (`_verdeckung_messen`).
            kontext[0].hide_render = True
            szene.render.filepath = str(out_dir / MATERIAL_ID_OHNE_KONTEXT[:-4])
            bpy.ops.render.render(write_still=True)
            kontext[0].hide_render = False
        szene.render.filepath = str(out_dir / "material_id")
        bpy.ops.render.render(write_still=True)
        if kontext is not None:
            ohne_png = out_dir / MATERIAL_ID_OHNE_KONTEXT
            kontext_befund["material_id"] = next(
                ({"index": e["index"], "quelle": e["quelle"],
                  "farbe_srgb_8bit": e["farbe_srgb_8bit"]}
                 for e in tabelle if e["quelle"] == "kontext"), None)
            # Nur der Dateiname: Er liegt neben `material_id.png` (Regel 3, kein Pfad).
            kontext_befund["material_id_ohne_kontext_png"] = (
                MATERIAL_ID_OHNE_KONTEXT if _frisch(ohne_png, beginn) else None)
            try:
                kontext_befund["verdeckung"] = _verdeckung_messen(ohne_png, material_id_png)
            except Exception as e:                       # noqa: BLE001
                kontext_befund["verdeckung"] = {"anteil": None,
                                                "grund": f"nicht messbar: {e}"}
    elif kontext is not None:
        kontext_befund["material_id"] = None
        kontext_befund["verdeckung"] = {
            "anteil": None, "grund": "Ohne Material-ID-Pass nicht gemessen."}

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
        # Wieviel Grundriss-Diagonale die Regel der Rahmung ueberhaupt genommen
        # hat. DIE ZAHL, AN DER EINE WIRKUNGSLOSE BAUWERKSBOX ZU ERKENNEN IST:
        # Ohne sie sieht eine Box, die 2 % bringt, im Bericht genauso aus wie
        # eine, die 35 % bringt. `None` heisst: es gibt keine Bauwerksbox.
        "bbox_bauwerk_schrumpfung": bau_schrumpfung,
        # WELCHE REGEL DIE BAUWERKSBOX BESTIMMT HAT — und die Namen, an denen die
        # Bauwerksmaske anknuepfen kann.
        #
        # *Beide Felder stehen IMMER da*, auch wenn nichts gefunden wurde (dann "keine"
        # und leer). Ein Feld, das mal da ist und mal nicht, zwingt jeden Leser zu einer
        # Fallunterscheidung, die er vergessen wird.
        #
        # Nur Namen und ein Wort, keine Boxen und keine Merkmale: Was die Bildseite
        # braucht, ist die Liste. Die drei Merkmale je Knoten bleiben auf der Boxseite
        # (`glbbox`), wo man sie nachrechnen kann.
        "bbox_bauwerk_entschieden_durch": bau_form["entschieden_durch"],
        "bbox_bauwerk_gelaende_namen": list(bau_form["gelaende_namen"]),
        # DIE MATERIALNAMEN DAZU (auf-20261021-316, B3): Die Tabelle der Bauwerksmaske traegt
        # Materialnamen, die Form Objektnamen — Deckung null (NAMENSDECKUNG_2026-09-08). Ein
        # Material, das NUR an Form-Gelaende haengt, ist Gelaende; ein geteiltes nicht.
        "bbox_bauwerk_gelaende_materialien": bau_materialien,
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
        #
        # UND NUR, WO ER GEWIRKT HAT (Befund 22.09.2026): Auf den Wegen `vorgegeben`
        # und `rueckfall` wird er nie gelesen, und bis dahin stand er trotzdem hier —
        # zwei Bestellungen mit 0.55 und 0.70 ergaben dieselbe Tiefenkarte und zwei
        # verschiedene Zahlen im Bericht. Dort steht jetzt `None` (NICHT GERAHMT) und
        # daneben `deckungsgrad_wirkungslos` mit dem Grund. Nebenbei faellt damit der
        # Absturz weg, den `_kameras_modul().DECKUNGSGRAD` auf dem Rueckfall ohne
        # erreichbare Bibliothek ausgeloest haette.
        **_deckungsgrad_befund(a, kamera_herkunft),
        # DIESELBE REGEL FUER AUGENHOEHE, BIAS UND KAMERAMODUS (Befund 23.09.2026): Sie
        # wirken nur auf `abgeleitet`. Dort steht der benutzte Wert; sonst `None` (NICHT
        # GESTELLT) und, wenn bestellt, `<name>_wirkungslos` mit dem Grund.
        **_kamerawerte_befund(a, kamera_herkunft),
        "n_meshes": sum(1 for o in bpy.data.objects if o.type == "MESH" and not _ist_kontext(o)),
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
        # WARUM ES HIER NICHTS ZU ENTSCHEIDEN GAB (auf-20260924-173, Zusatz A4): Der Satz
        # war «unter bedarf.grund» angesagt, und der Bericht hatte keinen `bedarf`. Siehe
        # `_bedarf_befund`.
        "bedarf": _bedarf_befund(),
        # Diagnose fuer den externen Leser: Multilayer-EXR benennt Kanaele anders als eine
        # einkanalige Datei ("tiefe_.V" statt "V"), und `aiimaging.bildlesen` sucht nach
        # Namen. Ohne diese Angabe kostete jede Formataenderung einen weiteren Rundlauf.
        "depth_exr_kanaele": _exr_kanalnamen(exr) if exr is not None else [],
        "depth_exr_format": exr_format,
    }
    if umgebung_befund is not None:
        # Nur, wenn ein Himmelsbild bestellt war — sonst bleibt der Bericht der bisherige.
        report["umgebung"] = umgebung_befund
    if material_befund is not None:
        report["materialien"] = material_befund
    if glas_befund is not None and glas_befund["materialien"]:
        report["glas_klar"] = glas_befund
    if kontext_befund is not None:
        # NUR WENN BESTELLT. Ohne Splat bleibt der Bericht Feld fuer Feld der bisherige —
        # bewacht in tests/test_kontext_splat.py. Fehlt der Block, war keiner bestellt.
        report["kontext"] = kontext_befund
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
