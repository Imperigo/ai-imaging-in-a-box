"""Die Prozessgrenzen: Aufrufe an IfcOpenShell und Blender.

Dieses Modul ist die einzige Stelle, an der das Produkt fremde Programme startet — und
es startet sie **immer** als eigenständige Prozesse, nie als Import.

Warum das so gebaut ist
-----------------------
* **Blender** (GPL-2.0-or-later) → `blender --background --python <runner>` (Regel 2)
* **IfcOpenShell** (LGPL-3.0-or-later, Wheel enthält GPL-lizenziertes CGAL) → eigenes
  venv, eigener Prozess (LGPL-Präzisierung zu Regel 1)

Beides ist GPL-rechtlich eine Aggregation: Die fremden Programme bleiben unter ihrer
Lizenz, der Code hier bleibt Apache-2.0. Die Verständigung läuft ausschliesslich über
Dateien und Prozess-Rückgabewerte.

Dieses Modul importiert weder `bpy` noch `ifcopenshell` — und darf es nie.

Test-Naht
---------
Jede Funktion nimmt ein optionales `_starte`, mit dem der Subprozessaufruf ersetzt
werden kann. Ohne das wären die Nahtstellen nur auf Rechnern prüfbar, auf denen Blender
installiert ist; mit ihm lässt sich die Aufrufkonstruktion überall testen.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

from aiimaging import fortschritt
from aiimaging.contracts import ContractError, needs_rotation

_RUNNER_DIR = Path(__file__).resolve().parent / "runners"

IFC_RUNNER = _RUNNER_DIR / "ifc_to_glb_runner.py"
IFC_RAEUME_RUNNER = _RUNNER_DIR / "ifc_raeume_runner.py"
BLENDER_RUNNER = _RUNNER_DIR / "blender_depth_stage.py"


class SeamError(RuntimeError):
    """Ein Subprozess ist fehlgeschlagen oder seine Voraussetzung fehlt."""


def _default_starte(cmd: list[str], timeout: int) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=False)


#: Wie oft eine überwachte Ausführung nachsieht. Zwei Sekunden wie im Altbestand — die
#: Zahl ist eine Setzung und keine Messung, sie steht darum als Parameter.
TAKT_S = 2.0

#: **Gemessen am 20.08.2026, Blender 4.2, Cycles auf CPU, 512×512, 3000 Samples ohne
#: adaptives Sampling, stdout in eine Datei umgeleitet.**
#:
#: Blender schreibt in diesem Aufbau seine Standardausgabe in einem sehr regelmässigen
#: Takt: Über einen Lauf von 190 Sekunden wuchs die Datei **sechsmal**, und zwar bei
#: 34, 66, 98, 130, 162 und 190 Sekunden — also exakt alle **32 Sekunden**, insgesamt um
#: 937 Bytes. Zwei Läufe (194 s und 190 s) ergaben dasselbe Bild.
#:
#: Das ist der Unterschied zwischen „es gibt kein Signal" und „es gibt eines mit grober
#: Körnung". Die Ausgabe **taugt** als belegtes Fortschrittszeichen — aber eine Frist
#: unter einem Takt bräche jeden gesunden Lauf ab, und zwar zuverlässig.
#:
#: **Vorbehalt, der dazugehört:** gemessen auf der CPU, in einem Container, an einer
#: Spielzeugszene. Ob GPU-Cycles auf der HomeStation denselben Takt hält, ist offen und
#: beauftragt. Wer die Zahl übernimmt, übernimmt diesen Vorbehalt mit.
BLENDER_TAKT_S = 32.0

#: **Und auf der GPU gibt es gar keinen Takt.** Gemessen von der HomeStation am
#: 19.08.2026 (`auf-20260820-18`), Blender 5.2.0 LTS, OptiX auf einer RTX 5090,
#: 220 000 Samples, zwei Läufe **auf die Zehntelsekunde identisch**:
#:
#: Die Ausgabedatei wächst **dreimal** — bei 1,0 s, bei 2,0 s und bei 177,0 s.
#: Dazwischen **175 Sekunden absolute Stille**, und in den 739 Bytes steht keine einzige
#: Fortschrittszeile; die einzige Render-Zeile ist die Schlussmeldung ``Saved:``.
#:
#: Das ist kein langsamer Takt, sondern **keiner**: Anfang und Ende, nichts dazwischen.
#: Der Takt von 32 s ist damit ein Artefakt der CPU-Messung und **nicht übertragbar**.
BLENDER_GPU_STILLE_S = 175.0

#: Der Dateiname des Herzschlags, den unser Runner schreibt. **Dieselbe Zeichenkette wie
#: `blender_depth_stage.HERZSCHLAG_DATEI`** — ein Dateiname, den zwei Seiten einer
#: Prozessgrenze unabhängig raten, ist eine tote Kante mit Ansage.
HERZSCHLAG_DATEI = "herzschlag.txt"

#: Vorgabetakt des Herzschlags im Runner, in Sekunden — und seit dem 20.08.2026
#: **eingeschaltet**, nicht mehr nur möglich.
#:
#: Gemessen auf beiden Maschinen, jeweils zweimal und jeweils deckungsgleich:
#:
#: * **CPU** (Blender 4.2, hier): 22 Schläge über 42 s, längste Lücke 2,1 s.
#: * **GPU** (`auf-20260820-19`, Blender 5.2.0 LTS, OptiX auf einer RTX 5090, 220 000
#:   Samples): **88 Schläge über 176,6 s, längste Lücke 2,10 s**, Nummern lückenlos von
#:   1 bis 88, kein einziger Sprung. Beide Läufe identisch.
#:
#: **Der Kontrast ist der Beleg:** Dieselbe Szene, dieselbe Dauer, derselbe Rechner wie in
#: `auf-20260820-18` — dort schwieg Blenders Standardausgabe **175 Sekunden am Stück**.
#: Der Unterschied liegt also nicht am Renderer und nicht am Gerät, sondern daran, *wer*
#: schreibt: Cycles schweigt, ein eigener Faden nicht. Auch unter OptiX gibt Cycles die
#: GIL frei.
HERZSCHLAG_TAKT_S = 2.0

#: Wie viele ausgefallene Schläge nötig sind, bevor die Wache anschlägt.
#:
#: Fünf statt zwei, weil ein Faden ins Hintertreffen geraten kann, ohne dass etwas kaputt
#: ist — eine ausgelastete Maschine, ein Dateisystem, das kurz hängt. Bei einem Takt von
#: 2 s macht das eine Frist von 10 s: immer noch **neunzigmal** früher als der
#: Gesamt-Timeout von 900 s.
#:
#: Gegen die Messung gehalten ist der Abstand komfortabel: Die grösste je beobachtete
#: Lücke war **2,10 s** — die Frist liegt fast beim Fünffachen davon.
HERZSCHLAG_AUSFAELLE = 5

#: Die kleinste Frist, die wir für einen Blender-Lauf zulassen — **es gibt keine.**
#:
#: Solange die Standardausgabe zwischen Start und Ende schweigt, bricht **jede** Frist,
#: die kürzer ist als der ganze Lauf, einen gesunden Lauf ab. Und wie lange ein Lauf
#: dauert, weiss man vorher nicht — das ist ja der Grund, warum es eine Wache gibt.
#: Es gibt darum keinen zulässigen Wert, und :func:`glb_zu_multipass` weist jeden ab.
#:
#: Die Zahl steht trotzdem hier, weil sie eine **Messung** ist und weil der Weg dorthin
#: lehrreich war: Sie war die Antwort auf die CPU-Messung und wäre auf der Maschine, die
#: wirklich rechnet, ein Werkzeug zur Zerstörung jedes Laufs über 98 Sekunden gewesen.
BLENDER_FRIST_MIN_S = 3 * BLENDER_TAKT_S


def starter_mit_wache(wache=None, *, frist_s: float | None = None,
                      takt_s: float = TAKT_S, _schlaf=None, _popen=None, _uhr=None):
    """Einen Starter bauen, der während des Laufs auf **Stillstand** achtet.

    Der Rückgabewert hat dieselbe Gestalt wie :func:`_default_starte` — ``(cmd, timeout)``
    hinein, ``CompletedProcess`` heraus — und lässt sich darum überall dort einsetzen, wo
    dieses Modul ein ``_starte`` entgegennimmt. **Das ist der ganze Grund, warum es diese
    Naht gibt:** Die Überwachung ist ein *anderer Starter*, keine Änderung am Vertrag.

    Warum das nötig ist: :func:`subprocess.run` blockiert bis zum Ende. Wer während des
    Laufs etwas bemerken will, muss den Prozess selbst starten und nachsehen. Der
    Gesamt-Timeout bleibt daneben bestehen — er fängt den Fall, den keine Wache fängt:
    einen Lauf, der stetig vorankommt und trotzdem zu lange dauert.

    Args:
        wache: eine :class:`aiimaging.fortschritt.Wache` **mit eigener Quelle** (aus
            ``wache_fuer_datei`` oder ``wache_fuer_verzeichnis``). Eine Wache auf ein
            blosses Statuswort taugt hier nicht: Ein Subprozess sagt uns von sich aus
            nichts, und ein erfundenes Statuswort wäre der Selbstbetrug, gegen den
            ``fortschritt.py`` gebaut ist.
        frist_s: Statt einer eigenen Wache — dann wacht der Starter über **seine eigene
            Standardausgabe**. Das löst ein Henne-Ei-Problem: Die Ausgabedatei entsteht
            erst beim Start, eine von aussen gebaute Wache könnte ihren Pfad also gar
            nicht kennen. Je Aufruf entsteht eine frische Wache — eine wiederverwendete
            trüge die Stillstandsuhr des vorigen Laufs mit.
        takt_s: Abstand zwischen zwei Blicken.

    Genau eines von ``wache`` und ``frist_s`` ist anzugeben. Beides zugleich wäre eine
    stille Vorrangfrage, und keines von beidem hiesse „überwachen ohne zu sagen woran".

    Der Prozess wird **nur bei einem belegten Stillstand** beendet. Eine blosse Warnung
    beendet nichts — dieselbe Regel wie in :mod:`aiimaging.fortschritt`: Was nicht belegt
    ist, darf nicht verurteilen. Hier kommt das nicht vor, weil beide Quellen belegt
    sind; die Bedingung steht trotzdem im Code und nicht nur im Docstring.

    **Ausgaben laufen über temporäre Dateien**, nicht über Pipes. Wer bei ``PIPE`` pollt
    statt zu lesen, blockiert den Kindprozess, sobald der Puffer voll ist — und Blender
    ist gesprächig. Der Lauf bliebe dann stehen, und zwar durch die Wache, die den
    Stillstand verhindern soll.
    """
    if (wache is None) == (frist_s is None):
        raise SeamError(
            "starter_mit_wache braucht GENAU EINES von 'wache' und 'frist_s'. Beides "
            "zugleich wäre eine stille Vorrangfrage; keines von beidem hiesse "
            "überwachen, ohne zu sagen woran."
        )
    schlaf = _schlaf or time.sleep
    oeffne = _popen or subprocess.Popen
    uhr = _uhr or time.monotonic

    def starte(cmd: list[str], timeout: int) -> subprocess.CompletedProcess:
        with tempfile.TemporaryDirectory(prefix="aiimaging-lauf-") as tmp:
            aus = Path(tmp) / "stdout.txt"
            fehler = Path(tmp) / "stderr.txt"
            diese = wache if wache is not None else fortschritt.wache_fuer_datei(
                aus, frist_s=frist_s, name="Standardausgabe des Laufs", _uhr=_uhr)
            prozess = oeffne(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            faeden = [_giesse(prozess.stdout, aus), _giesse(prozess.stderr, fehler)]
            try:
                beginn = float(uhr())
                try:
                    while True:
                        code = prozess.poll()
                        if code is not None:
                            break
                        befund = diese.blick()
                        if befund["schwere"] == fortschritt.SCHWERE_FEHLER:
                            prozess.kill()
                            prozess.wait()
                            raise SeamError(
                                f"Lauf abgebrochen wegen Stillstand: {befund['detail']} "
                                f"Der Gesamt-Timeout ({timeout} s) wäre erst in "
                                f"{max(0.0, timeout - (float(uhr()) - beginn)):.0f} s "
                                f"gegriffen."
                            )
                        if float(uhr()) - beginn > timeout:
                            prozess.kill()
                            prozess.wait()
                            raise subprocess.TimeoutExpired(cmd, timeout)
                        schlaf(takt_s)
                except BaseException:
                    if prozess.poll() is None:
                        prozess.kill()
                        prozess.wait()
                    raise
            finally:
                for faden in faeden:
                    if faden is not None:
                        faden.join(timeout=30)
            return subprocess.CompletedProcess(
                cmd, prozess.returncode,
                aus.read_text(encoding="utf-8", errors="replace")
                if aus.exists() else "",
                fehler.read_text(encoding="utf-8", errors="replace")
                if fehler.exists() else "",
            )

    return starte


def _giesse(quelle, ziel: Path):
    """Einen Ausgabestrom **laufend** in eine Datei giessen, in einem eigenen Faden.

    Zwei Fliegen mit einer Klappe, und beide sind gemessen:

    **Erstens** läuft der Puffer nie voll. Wer bei ``PIPE`` nur pollt statt zu lesen,
    blockiert den Kindprozess, sobald der Puffer voll ist — der Lauf bliebe stehen, und
    zwar durch genau die Wache, die den Stillstand verhindern soll. Ein Faden, der
    ununterbrochen liest, kann das nicht passieren.

    **Zweitens** wächst die Datei genau dann, wenn der Prozess schreibt. Sie ist damit
    dasselbe belegte Fortschrittszeichen wie eine echte Umleitung — ohne deren Preis.

    Und der Preis wäre hoch. Am 19.08.2026 hat die HomeStation gemessen: Das
    Snap-Paket von **Blender 5.2.0 LTS** — das einzige dort mit OptiX und CUDA —
    **beendet sich bei einer Umleitung nach `>` in eine Datei nach 1,3 Sekunden mit
    Rückgabewert 0, ohne Ausgabe und ohne Bild.** Gegengeprüft an vier Ablageorten,
    jedes Mal null Byte, jedes Mal kein Bild. Über eine Pipe rendert dasselbe Blender
    einwandfrei.

    Ein Erfolgsmeldung ohne Ergebnis ist die teuerste Sorte Fehler, die dieses Projekt
    kennt. Diese Funktion ist die Antwort darauf.

    Returns:
        Den laufenden Faden, oder ``None``, wenn es nichts zu giessen gibt (der Fall bei
        Test-Attrappen ohne echte Ströme).
    """
    if quelle is None:
        return None

    # `read1` gibt zurück, was DA ist, statt auf die volle Blockgrösse zu warten. Damit
    # wächst die Datei so prompt wie bei byteweisem Lesen, ohne dessen Preis — zwei
    # Millionen Systemaufrufe für zwei Megabyte. Attrappen ohne `read1` fallen auf `read`
    # zurück.
    lies = getattr(quelle, "read1", None) or quelle.read

    def giessen():
        try:
            with open(ziel, "wb") as datei:
                while True:
                    block = lies(65536)
                    if not block:
                        break
                    datei.write(block)
                    datei.flush()
        except (OSError, ValueError):
            return
        finally:
            try:
                quelle.close()
            except Exception:      # noqa: BLE001 — beim Aufräumen zählt nur, dass es endet
                pass

    faden = threading.Thread(target=giessen, daemon=True)
    faden.start()
    return faden


def finde_ifc_python() -> str:
    """Pfad zum Python des `.venv-ifc`.

    Reihenfolge: Umgebungsvariable, dann das venv im Projektwurzelverzeichnis. Bewusst
    **kein** Rückfall auf `sys.executable` — das wäre genau der Fehlgriff, den die
    Prozessgrenze verhindern soll: ifcopenshell (und damit GPL-CGAL) liefe dann im
    Produkt-Environment.
    """
    if (env := os.environ.get("AIIMAGING_IFC_PYTHON")):
        return env
    kandidat = Path(__file__).resolve().parents[2] / ".venv-ifc" / "bin" / "python"
    if kandidat.exists():
        return str(kandidat)
    raise SeamError(
        ".venv-ifc nicht gefunden. Anlegen mit:\n"
        "    python3 -m venv .venv-ifc && .venv-ifc/bin/pip install ifcopenshell trimesh numpy\n"
        "Oder AIIMAGING_IFC_PYTHON setzen. Ein Rückfall auf das Produkt-Python findet "
        "bewusst nicht statt — er würde GPL-Code in diesen Prozess holen."
    )


def finde_blender() -> str:
    """Pfad zum Blender-Binary (Umgebungsvariable, dann PATH, dann /opt/blender)."""
    if (env := os.environ.get("AIIMAGING_BLENDER")):
        return env
    if (gefunden := shutil.which("blender")):
        return gefunden
    if (opt := Path("/opt/blender/blender")).exists():
        return str(opt)
    raise SeamError(
        "Blender nicht gefunden. AIIMAGING_BLENDER setzen oder blender in den PATH legen."
    )


def ifc_zu_glb(ifc_path, glb_path, *, timeout: int = 300, _starte=None) -> dict:
    """IFC → glb (Y-up) über den Subprozess im `.venv-ifc`.

    **IFC4 *und* IFC2X3.** Hier stand bis zum 18.08.2026 „IFC4". Das war eine Behauptung
    über eine Datei, die niemand gesehen hatte: An 40 echten Dateien (`auf-20260818-08`)
    waren 30 IFC4 und **10 IFC2X3 — und alle zehn davon kamen aus ArchiCAD**. Wer nur
    gegen IFC4 prüft, prüft nicht gegen das, was das verbreitetste Autorenprogramm
    tatsächlich liefert.

    Beide Schemata sind hier durch den echten Konverter gemessen, in Metern und in
    Millimetern, jeweils mit demselben Ergebnis (8,0 × 5,0 × 3,25 m).

    Returns:
        Report des Runners mit `glb_path`, `up_axis`, `bbox`, `n_elements`, `n_triangles`.

    Raises:
        SeamError: venv fehlt, Subprozess scheitert oder liefert keinen lesbaren Report.
    """
    starte = _starte or _default_starte
    cmd = [finde_ifc_python(), str(IFC_RUNNER), str(ifc_path), str(glb_path)]

    ergebnis = starte(cmd, timeout)
    if ergebnis.returncode != 0:
        raise SeamError(
            f"IFC→glb fehlgeschlagen (Code {ergebnis.returncode}):\n"
            f"{(ergebnis.stderr or ergebnis.stdout or '').strip()[:800]}"
        )
    try:
        return json.loads(ergebnis.stdout)
    except json.JSONDecodeError as e:
        raise SeamError(f"Runner lieferte kein JSON: {e}\n{ergebnis.stdout[:400]}") from e


def _fehlertext(ergebnis) -> str:
    """Die aussagekräftigste Fehlermeldung aus einem gescheiterten Lauf.

    Warum nicht einfach ``stderr``: Der Raum-Runner schreibt seine Diagnose als **Report
    auf stdout** und meldet den Fehlschlag über den Rückgabewert. Auf stderr landet
    derweil, was die fremde Bibliothek dort hinterlässt — bei ifcopenshell 0.8.5 zum
    Beispiel ein ``KeyError`` aus einem Destruktor beim Herunterfahren des Interpreters,
    der mit der Ursache nichts zu tun hat.

    Gemessen am 22.08.2026 an einer Datei, die keine IFC ist: Auf stdout stand
    ``"Unable to parse IFC SPF header"``, auf stderr die Destruktor-Meldung. Wer nur
    stderr zeigt, zeigt dem Aufrufer ausgerechnet das Rauschen und verschweigt die
    Diagnose.

    Darum: erst der ``error``-Eintrag des Reports, dann stderr, dann die rohe Ausgabe.
    Beides zusammen, wenn es beides gibt — was die fremde Bibliothek sagt, kann bei einem
    Absturz die einzige Spur sein.
    """
    teile: list[str] = []
    try:
        report = json.loads(ergebnis.stdout)
        if isinstance(report, dict) and report.get("error"):
            teile.append(str(report["error"]))
    except (json.JSONDecodeError, TypeError):
        pass
    if (ergebnis.stderr or "").strip():
        teile.append(ergebnis.stderr.strip())
    if not teile and (ergebnis.stdout or "").strip():
        teile.append(ergebnis.stdout.strip())
    return "\n".join(teile)[:800] or "(keine Ausgabe)"


def ifc_raeume(ifc_path, *, timeout: int = 300, _starte=None) -> dict:
    """Räume (``IfcSpace``) aus einer IFC — über den Subprozess im `.venv-ifc`.

    Gebaut wie :func:`ifc_zu_glb` und aus demselben Grund: `ifcopenshell` bringt statisch
    gelinktes GPL-CGAL mit und darf nach Regel 1 nur jenseits einer Prozessgrenze laufen.
    Diese Funktion ist die diesseitige Hälfte davon — sie startet ein Programm und liest
    JSON, sie importiert nichts.

    Sie ist die **Voraussetzung** für Innenaufnahmen, nicht deren Umsetzung: `kameras.py`
    rechnet ausschliesslich Standpunkte um eine Hüllbox herum, und ``WANDABSTAND_M = 10.0``
    macht eine Innenaufnahme rechnerisch unmöglich. Bevor sich daran etwas ändern lässt,
    muss bekannt sein, wo die Räume sind. Hier steht nur das.

    **IFC4 *und* IFC2X3**, in Metern *und* in Millimetern — alle vier Kombinationen sind
    durch den echten Runner gemessen und ergeben dieselben Räume (siehe
    ``tests/test_raeume.py``, Gruppe C). Die Messung an 40 echten Dateien
    (`auf-20260818-08`) sagt, warum das nötig ist: 25 von 40 standen in Millimetern, und
    alle zehn ArchiCAD-Dateien waren IFC2X3.

    Args:
        ifc_path: Die zu lesende IFC-Datei.
        timeout: Frist des Subprozesses in Sekunden.
        _starte: Testnaht — ersetzt den Subprozessaufruf, damit die Aufrufkonstruktion
            auch ohne `.venv-ifc` prüfbar bleibt.

    Returns:
        Report des Runners: ``status``, ``schema``, ``einheit``, ``n_raeume``,
        ``n_mit_grundriss``, ``n_ohne_grundriss``, ``n_mit_hoehe``, ``n_ohne_hoehe``,
        ``raeume``, ``masse_plausibel``, ``masse_befund``, ``warnungen``.

        Je Raum: ``global_id``, ``name``, ``lang_name``, ``geschoss_global_id``,
        ``geschoss_name``, ``grundriss_m`` (Polygon in der Waagerechten, in Metern),
        ``grundriss_quelle``, ``umlaufsinn``, ``flaeche_m2``, ``z_unten_m``, ``hoehe_m``,
        ``hoehe_bezug``, ``hoehe_begruendung``, ``befund``, ``hoehe_befund``,
        ``hinweise``.

        **Zwei Urteile, nicht eines.** ``grundriss_m is None`` genau dann, wenn ``befund``
        gesetzt ist; ``hoehe_m is None`` genau dann, wenn ``hoehe_befund`` gesetzt ist.
        Der Fall, der das erzwungen hat, ist die schiefe Extrusion: Der Fussbodenumriss
        steht dann einwandfrei in der Datei, aber der Körper darüber schert weg. Ein
        einziges Urteil hätte entweder eine gültige Messung weggeworfen oder eine
        erfundene Höhe geliefert.

        **Der Bezugspunkt der Höhe ist Teil der Antwort, nicht ihr Beiwerk:**
        ``hoehe_m`` ist die Länge des modellierten Raumkörpers **nach oben ab**
        ``z_unten_m``, und ``z_unten_m`` liegt in IFC-Weltkoordinaten — nicht über Meer,
        nicht über Gelände. Dieses Projekt hat an genau dieser Verwechslung schon zweimal
        verloren (siehe Modulkopf von ``kameras.py``: eine Kamerahöhe „absolut" gemeint
        landete bei einem Bauwerk auf 400 m über Meer vierhundert Meter unter dem
        Erdgeschoss).

        **Kein Raum wird stillschweigend weggelassen.** ``len(raeume) == n_raeume`` ist die
        Zahl der ``IfcSpace`` in der Datei; ein Raum ohne lesbaren Grundriss steht mit
        ``grundriss_m = None`` und einem ``befund`` da. Sonst sähe der Aufrufer drei Räume
        und hielte sie für alle.

        **Null Räume sind kein Fehler**, sondern ein Befund: Die meisten IFC-Dateien tragen
        gar keine ``IfcSpace``. Der Report sagt dann ``status: "ok"``, ``n_raeume: 0`` und
        nennt es in ``warnungen``.

    Raises:
        SeamError: venv fehlt, Subprozess scheitert oder liefert keinen lesbaren Report.
    """
    starte = _starte or _default_starte
    cmd = [finde_ifc_python(), str(IFC_RAEUME_RUNNER), str(ifc_path)]

    ergebnis = starte(cmd, timeout)
    if ergebnis.returncode != 0:
        raise SeamError(
            f"IFC-Räume fehlgeschlagen (Code {ergebnis.returncode}):\n"
            f"{_fehlertext(ergebnis)}"
        )
    try:
        return json.loads(ergebnis.stdout)
    except json.JSONDecodeError as e:
        raise SeamError(f"Runner lieferte kein JSON: {e}\n{ergebnis.stdout[:400]}") from e


def _multipass_argumente(glb_path, out_dir, *, drehen: bool, aufloesung: int, samples: int,
                         beauty: bool, material_id: bool, kamera=None,
                         auge=None, blick_auf=None, brennweite=None,
                         kamera_modus=None, shift_y=None,
                         gelaende_z=None, hoehe=None,
                         herzschlag_takt_s=None, kamera_huellbox=None) -> list[str]:
    """Die Argumente hinter dem `--`-Trenner — eine Stelle für Lauf und Trockenlauf.

    Wären sie zweimal geschrieben, könnten `glb_zu_multipass` und
    `baue_kommando_multipass` auseinanderlaufen — und dann prüfte der Test ein Kommando,
    das so nie gestartet wird.

    Zur Kamera gibt es zwei Wege, und ohne Angabe bleibt es beim Rückfall des Runners:

    * ``kamera`` — ein Richtungskürzel aus :mod:`aiimaging.kameras`. Der Standort wird
      dann **im Runner** aus der dort gemessenen Hüllbox abgeleitet. Das ist der sichere
      Weg, weil er keine Annahme über Bezugssysteme macht: Ob die Hüllbox aus dem IFC nach
      Export, Import und einer möglichen Z-up-Drehung noch dieselbe ist, gehört gemessen
      und nicht angenommen.
    * ``auge`` und ``blick_auf`` — fertige Koordinaten. Wer sie schickt, hat selbst
      gerechnet und trägt die Verantwortung für das Bezugssystem.

    Raises:
        SeamError: ``auge`` ohne ``blick_auf`` (oder umgekehrt). Ein Standort ohne
            Blickziel beschreibt keine Kamera, und der Runner würde erst nach dem
            Blender-Start abbrechen — Minuten später, für nichts.
    """
    argumente = [
        "--glb", str(glb_path), "--out", str(out_dir),
        "--aufloesung", str(aufloesung), "--samples", str(samples),
    ]
    if (auge is None) != (blick_auf is None):
        raise SeamError(
            "auge und blick_auf gehören zusammen: "
            f"auge={auge!r}, blick_auf={blick_auf!r}. Ein Standort ohne Blickziel "
            "beschreibt keine Kamera."
        )
    # ZAHLENWERTE IMMER IN DER GLEICHHEITSZEICHEN-FORM.
    #
    # AM GERAET GEFUNDEN (19.08.2026, erster echter Auftrag der fremden Bruecke): Der
    # Auftrag trug drei Kameras. Zwei liefen, die dritte — Kuerzel "Innenraum", `auge`
    # [-6.854, 1.6, 6.854] — brach ab mit
    #
    #     blender: error: argument --auge: expected one argument
    #
    # `argparse` haelt jedes Wort mit fuehrendem Minus fuer eine Option. `--auge` stand
    # damit ohne Wert da, und `-6.854,1.6,6.854` galt als unbekanntes Flag. Die
    # Gleichheitszeichen-Form `--auge=-6.854,...` ist der dokumentierte Weg daran vorbei:
    # Was hinter dem `=` steht, wird nie mehr als Option gelesen.
    #
    # Warum es so lange gutging: Jede bis dahin gemessene Kamera stand vor dem Bauwerk,
    # also im positiven Bereich. Eine Innenraumkamera steht im Gebaeude — und dort ist
    # mindestens eine Koordinate fast immer negativ. Der Fehler war nicht selten, er war
    # unerreichbar, solange niemand nach innen schaute.
    #
    # Betroffen ist JEDER Zahlenwert, nicht nur `--auge`: Ein Gelaende unter dem Nullpunkt
    # (`--gelaende-z`) und eine Huellbox mit negativer Ecke tragen dasselbe Minus.
    if auge is not None:
        argumente += [f"--auge={_punkt(auge, 'auge')}",
                      f"--blick-auf={_punkt(blick_auf, 'blick_auf')}"]
    elif kamera is not None:
        argumente += ["--kamera", str(kamera)]
    if brennweite is not None:
        argumente += [f"--brennweite={float(brennweite)}"]
    # Der Kameramodus geht in die Rechnung des Runners, `shift_y` stellt das Objektiv.
    # Beide `None` heisst „nicht angefasst" — der Runner behält dann seinen gekippten
    # Weg, und jede bisher gemessene Aufnahme bleibt reproduzierbar.
    if kamera_modus is not None:
        argumente += [f"--kamera-modus={str(kamera_modus)}"]
    if shift_y is not None:
        argumente += [f"--shift-y={float(shift_y)}"]
    if gelaende_z is not None:
        argumente += [f"--gelaende-z={float(gelaende_z)}"]
    if hoehe is not None:
        argumente += ["--hoehe", str(int(hoehe))]
    if herzschlag_takt_s is not None:
        argumente += ["--herzschlag-s", str(float(herzschlag_takt_s))]
    if kamera_huellbox is not None:
        lo, hi = kamera_huellbox
        argumente += ["--kamera-huellbox="
                      + ",".join(str(float(v)) for v in (*lo, *hi))]
    if drehen:
        argumente.append("--rotiere-z-up")
    if not beauty:
        argumente.append("--ohne-beauty")
    if not material_id:
        argumente.append("--ohne-material-id")
    return argumente


def _punkt(wert, name: str) -> str:
    """``(1, 2, 3)`` → ``"1.0,2.0,3.0"`` — die Form, die der Runner liest.

    Raises:
        SeamError: nicht drei endliche Zahlen. Hier abzufangen statt im Runner spart
            einen Blender-Start: Der Fehler ist an drei Zahlen erkennbar, und der Lauf
            dahinter kostet Minuten.
    """
    try:
        werte = [float(w) for w in wert]
    except (TypeError, ValueError) as e:
        raise SeamError(f"{name} muss drei Zahlen sein, war: {wert!r}") from e
    if len(werte) != 3 or any(w != w or w in (float("inf"), float("-inf")) for w in werte):
        raise SeamError(f"{name} muss drei endliche Zahlen sein, war: {wert!r}")
    return ",".join(repr(w) for w in werte)


def glb_zu_multipass(glb_path, out_dir, *, up_axis, aufloesung: int = 512,
                     samples: int = 16, beauty: bool = True, material_id: bool = True,
                     kamera=None, auge=None, blick_auf=None, brennweite=None,
                     kamera_modus=None, shift_y=None,
                     gelaende_z=None, hoehe=None,
                     timeout: int = 900, stillstand_frist_s: float | None = None,
                     herzschlag_takt_s: float | None = HERZSCHLAG_TAKT_S,
                     kamera_huellbox=None, _starte=None) -> dict:
    """glb → Cycles-Multipass über `blender --background`.

    Vier Ausgaben, in zwei Renderdurchgängen: Beauty und Tiefe (EXR in Metern plus
    normalisiertes 16-Bit-PNG, nah = hell) entstehen gemeinsam, die Material-ID braucht
    einen eigenen Durchgang — ihr Emissions-Override würde sonst das Beauty-Bild in eine
    flache Farbfläche verwandeln.

    `up_axis` ist **Pflicht**, kein Vorgabewert. Der Grund ist der Phase-0-Befund: Zwei
    Erzeuger im Ökosystem liefern beide ein Feld `glb_path`, aber mit unterschiedlicher
    Orientierung (KosmoDraw Z-up, KosmoVis Y-up). Ein Default wäre eine stille
    Verdrehung von Tiefenkarte, Kamera und späterer Geometrie-QA.

    Args:
        beauty: `False` unterdrückt nur das Schreiben des Beauty-PNG. Gerendert wird der
            Durchgang trotzdem — die Tiefe ist ein Pass desselben Renders und hinge sonst
            in der Luft. Spart Plattenplatz, keine Rechenzeit.
        material_id: `False` lässt den zweiten Durchgang ganz aus und spart damit
            tatsächlich Rechenzeit.
        kamera_huellbox: ``(lo, hi)`` — die Hüllbox, auf die sich die **Kamera** bezieht.
            Ohne Angabe alle Meshes. Nötig, sobald die Szene **Gelände** trägt: Eine
            Geländeplatte bläht die Hüllbox auf, die Kamera zieht sich zurück, und der
            Geometrieanteil des Bildes *sinkt* (am 20.08.2026 gemessen: 6,9 % statt 21,9 %).
            Der Bericht beschreibt weiterhin, was dasteht — die Kamera rahmt, was gezeigt
            werden soll. Zwei verschiedene Fragen, zwei verschiedene Hüllboxen.
        herzschlag_takt_s: Die **Herzschlagwache**, seit dem 20.08.2026 **eingeschaltet**
            (``None`` schaltet sie ab). Der Runner
            schreibt dann alle so viele Sekunden ein Lebenszeichen nach
            ``<out>/herzschlag.txt``, und dieser Aufruf bricht ab, wenn
            :data:`HERZSCHLAG_AUSFAELLE` Schläge nacheinander ausbleiben.
            **Das ist die Antwort auf die Messung vom 20.08.2026:** Blenders eigene
            Ausgabe schweigt auf der GPU zwischen Start und Ende, taugt also nicht; ein
            Faden, den wir selbst starten, läuft weiter, weil Cycles die GIL freigibt
            (gemessen: 61 Schläge in 118 s, während ``render_stats`` und
            ``bpy.app.timers`` **null** Mal feuerten).
            **Was er belegt und was nicht:** Ein ausbleibender Herzschlag heisst
            zuverlässig, dass der Prozess tot oder eingefroren ist. Ein *laufender*
            belegt **keinen Fortschritt** — ein festgefahrener Cycles-Kern schlägt
            weiter. Die Wache schlägt nur auf Stille an, und nur darauf.
            *Warum jetzt voreingestellt:* Am 20.08. auf der GPU nachgemessen
            (`auf-20260820-19`) — 88 Schläge, längste Lücke 2,10 s, keine verlorenen
            Nummern. Vorher war es eine Vermutung von der CPU, und Vermutungen bleiben in
            diesem Projekt ausgeschaltet. Der Preis ist ein Faden und rund zehn Bytes je
            zwei Sekunden; der Gewinn ist, dass ein hängender Lauf nach 10 statt nach 900
            Sekunden auffällt.
        stillstand_frist_s: **Wird immer abgewiesen** — der Parameter bleibt nur
            bestehen, damit ein Aufrufer eine Begründung bekommt statt eines
            ``TypeError``. Blenders Standardausgabe schweigt auf der GPU zwischen Start
            und Ende (gemessen: 175 s am Stück, `auf-20260820-18`), und damit gibt es
            keine Frist, die einen Hänger fängt, ohne gesunde Läufe abzubrechen.
            *Diese Zeile stand am Vormittag desselben Tages noch anders.* Sie erlaubte
            96 Sekunden, hergeleitet aus einer CPU-Messung — auf der Maschine, die
            wirklich rechnet, wäre das ein Werkzeug zur Zerstörung jedes Laufs über
            98 Sekunden gewesen.

    Returns:
        Report des Runners mit `beauty_png`, `material_id_png`, `depth_exr`, `depth_png`,
        `n_materialien` und `depth_normalisierung` (min/max in Metern, für die Rückrechnung
        des PNG in echte Tiefen).

        `depth_png` und `depth_normalisierung` kommen **nicht** aus Blender, sondern
        werden hier nachgerechnet — siehe :func:`_tiefe_nachbearbeiten`. Scheitert das,
        steht der Grund in `depth_png_fehler` und der Lauf gilt trotzdem als gelungen:
        Die EXR mit den echten Metern ist das massgebliche Artefakt.

    Raises:
        ContractError: `up_axis` fehlt oder ist nicht deutbar.
        SeamError: Blender fehlt oder der Lauf scheitert.
    """
    # Die Abweisung steht VOR jeder Starterwahl. Sonst verschluckt der Herzschlag-Zweig
    # sie, seit er voreingestellt ist — und ein Aufrufer, der stillstand_frist_s setzt,
    # bekäme stillschweigend etwas anderes als bestellt.
    if stillstand_frist_s is not None:
        raise SeamError(
            f"stillstand_frist_s={stillstand_frist_s} s — für Blenders STANDARDAUSGABE "
            f"gibt es keinen zulässigen Wert, und das ist gemessen und nicht "
            f"vorsichtshalber.\n"
            f"Auf der GPU (auf-20260820-18: Blender 5.2.0 LTS, OptiX, RTX 5090, zwei "
            f"Läufe auf die Zehntelsekunde identisch) wächst sie genau dreimal: bei "
            f"1,0 s, bei 2,0 s und bei {BLENDER_GPU_STILLE_S + 2:.0f} s. Dazwischen "
            f"{BLENDER_GPU_STILLE_S:.0f} Sekunden Stille, ohne eine einzige "
            f"Fortschrittszeile. Das ist kein langsamer Takt, sondern keiner.\n"
            f"Damit bricht JEDE Frist, die kürzer ist als der ganze Lauf, einen gesunden "
            f"Lauf ab — und wie lange ein Lauf dauert, weiss man vorher nicht; das ist "
            f"der Grund, warum es eine Wache gibt.\n"
            f"**Was du stattdessen willst, gibt es schon:** 'herzschlag_takt_s' ist "
            f"voreingestellt und schreibt ein eigenes Lebenszeichen, statt auf Cycles zu "
            f"warten. Auf derselben Karte gemessen (auf-20260820-19): 88 Schläge über "
            f"176 s, längste Lücke 2,10 s."
        )

    if _starte is not None:
        starte = _starte
    elif herzschlag_takt_s is not None:
        starte = starter_mit_wache(
            fortschritt.wache_fuer_datei(
                Path(out_dir) / HERZSCHLAG_DATEI,
                frist_s=HERZSCHLAG_AUSFAELLE * herzschlag_takt_s,
                name="Herzschlag des Blender-Laufs"),
            takt_s=min(TAKT_S, herzschlag_takt_s))
    else:
        starte = _default_starte
    drehen = needs_rotation(up_axis)          # wirft ContractError, wenn up_axis fehlt

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Ausgaben eines frueheren Laufs VOR dem Start entfernen — nicht nur den Report.
    #
    # Vorgeschichte: In Sitzung 03 wurde der Report geloescht, weil ein abgestuerzter Lauf
    # sich sonst am liegengebliebenen Report gesundmeldete. In Sitzung 05 stellte sich
    # heraus, dass dasselbe eine Datei weiter noch galt: Der Runner erklaerte den Lauf fuer
    # gelungen, sobald eine `tiefe_*.exr` im Verzeichnis lag — auch die des Vorlaufs. Weil
    # `out_dir` ueblicherweise wiederverwendet wird, verwies ein gescheiterter Lauf dann auf
    # das Bild von gestern.
    #
    # Die Lehre, die dieses Projekt mehrfach gelernt hat: Die Existenz einer Datei ist kein
    # Beleg fuer ihren Inhalt. Darum wird hier abgeraeumt statt geprueft.
    bericht = out_dir / "blender-report.json"
    bericht.unlink(missing_ok=True)
    for muster in ("tiefe_*.exr", "tiefe_norm.png", "material_id.png", "beauty_*.png"):
        for alt_datei in out_dir.glob(muster):
            alt_datei.unlink(missing_ok=True)

    cmd = [
        finde_blender(), "--background", "--factory-startup",
        "--python", str(BLENDER_RUNNER), "--",
        *_multipass_argumente(glb_path, out_dir, drehen=drehen, aufloesung=aufloesung,
                              samples=samples, beauty=beauty, material_id=material_id,
                              kamera=kamera, auge=auge, blick_auf=blick_auf,
                              brennweite=brennweite, kamera_modus=kamera_modus,
                              shift_y=shift_y, gelaende_z=gelaende_z,
                              hoehe=hoehe, herzschlag_takt_s=herzschlag_takt_s,
                              kamera_huellbox=kamera_huellbox),
    ]

    ergebnis = starte(cmd, timeout)

    # Zwei unabhaengige Bedingungen, beide notwendig: Der Prozess muss sauber geendet
    # haben UND einen Report hinterlassen haben. Nur die Datei zu pruefen genuegt nicht
    # (siehe oben), nur den Rueckgabewert auch nicht — Blender kann 0 melden und am
    # Compositor gescheitert sein.
    if ergebnis.returncode != 0:
        raise SeamError(
            f"Blender endete mit Code {ergebnis.returncode}:\n"
            f"{(ergebnis.stderr or ergebnis.stdout or '').strip()[-1500:]}"
        )
    if not bericht.exists():
        raise SeamError(
            f"Blender schrieb keinen Report (Code {ergebnis.returncode}):\n"
            f"{(ergebnis.stderr or ergebnis.stdout or '').strip()[-1500:]}"
        )
    report = json.loads(bericht.read_text(encoding="utf-8"))
    if not isinstance(report, dict):
        raise SeamError(
            f"blender-report.json enthält kein Objekt, sondern "
            f"{type(report).__name__}. Eine abgeschnittene oder fremde Datei — der Lauf "
            f"ist damit nicht deutbar."
        )
    return _tiefe_nachbearbeiten(report, out_dir, timeout=timeout, _starte=starte)


def _tiefe_nachbearbeiten(report: dict, out_dir: Path, *, timeout: int = 300,
                          _starte=None) -> dict:
    """Aus der EXR das normalisierte PNG rechnen — auf dieser Seite der Prozessgrenze.

    Bis zum 18.08.2026 tat das der Runner selbst. Der Schritt ist hierher gewandert,
    weil Blender 5.2 die Multilayer-EXR, die es dort schreiben **muss**, selbst nicht
    wieder einlesen kann (`bpy.data.images.load` liefert 0×0 mit 0 Kanälen). Die volle
    Begründung samt Messwerten steht in :mod:`aiimaging.bildschreiben`.

    Warum das die bessere Naht ist, unabhängig vom Fehler: Eine Normalisierung ist
    Arithmetik auf einem Zahlenfeld. Sie hier zu rechnen heisst, sie **ohne Blender,
    ohne GPU und ohne Prozessgrenze** testen zu können — Regel 4 in ihrer schärfsten
    Lesart. Und es gibt nur noch **einen** Weg zum PNG statt eines je Blender-Fassung;
    zwei Wege wären eine stille Abweichung, die niemand bemerkt.

    Der Schritt ist bewusst **nicht** tödlich: Scheitert er, bleibt der Blender-Lauf
    gültig. Die EXR ist das massgebliche Artefakt — sie trägt echte Meter, das PNG ist
    ihre verlustbehaftete Ableitung für das Bildmodell. Was schiefging, steht in
    `depth_png_fehler`, nicht in einem Traceback.
    """
    from aiimaging import bildschreiben               # spät, damit `seams` leicht bleibt

    # Überschreiben, nicht ergänzen. Diese Naht ist ab jetzt der einzige Erzeuger von
    # `depth_png`; ein Wert, der schon im Report stand, stammt aus einem Runner, der
    # nicht mehr normalisiert — also aus einem früheren Lauf oder einer fremden Fassung.
    # Ihn stehen zu lassen hiesse, auf eine Datei zu zeigen, die niemand geschrieben hat.
    # Das ist dieselbe Lehre wie beim Abräumen der Altdateien weiter oben: Ein Feld im
    # Report ist kein Beleg für eine Datei auf der Platte.
    report["depth_png"] = None
    report["depth_normalisierung"] = None
    report["depth_png_fehler"] = None

    exr = report.get("depth_exr")
    if not exr:
        report["depth_png_fehler"] = "Report nennt keine `depth_exr` — nichts zu normalisieren."
        return report
    if not Path(exr).exists():
        report["depth_png_fehler"] = f"`depth_exr` zeigt auf {exr}, dort liegt nichts."
        return report

    ziel = Path(out_dir) / "tiefe_norm.png"
    try:
        # `timeout` und `_starte` weiterreichen: Der stdlib-Leser kann nicht jede
        # EXR-Spielart, und sein Rückfall ist ein zweiter Blender-Prozess. Ohne diese
        # beiden Argumente liefe er ohne Naht und mit einem Zeitlimit, das der Aufrufer
        # nie gesetzt hat.
        normalisierung = bildschreiben.tiefe_exr_zu_png(
            exr, ziel, timeout=timeout, _starte=_starte)
    except Exception as e:                              # Befund als Feld, nicht als Absturz
        report["depth_png_fehler"] = f"{type(e).__name__}: {e}"
        return report

    # Nachsehen statt behaupten — dieselbe Prüfung, die `render.rendere` am Ende macht.
    # Ein Schreiber, der einen Pfad zurückgibt, ohne etwas zu hinterlassen, ist ein
    # Fehlschlag und kein Erfolg mit fehlender Datei.
    if not ziel.is_file() or ziel.stat().st_size == 0:
        report["depth_png_fehler"] = (
            f"Die Normalisierung meldete Erfolg, aber {ziel.name} fehlt oder ist leer."
        )
        return report

    report["depth_normalisierung"] = normalisierung
    report["depth_png"] = str(ziel)
    return report


def baue_kommando_multipass(glb_path, out_dir, *, up_axis, aufloesung: int = 512,
                            samples: int = 16, beauty: bool = True,
                            material_id: bool = True, kamera=None, auge=None,
                            blick_auf=None, brennweite=None,
                            kamera_modus=None, shift_y=None,
                            gelaende_z=None, hoehe=None,
                            herzschlag_takt_s: float | None = HERZSCHLAG_TAKT_S,
                            ) -> list[str]:
    """Nur das Blender-Kommando bauen, ohne es auszuführen.

    Für Tests und zur Fehlersuche: zeigt, ob die Prozessgrenze richtig konstruiert ist —
    insbesondere, ob `--rotiere-z-up` bei Z-up-Quellen gesetzt wird.
    """
    return [
        "blender", "--background", "--factory-startup",
        "--python", str(BLENDER_RUNNER), "--",
        *_multipass_argumente(glb_path, out_dir, drehen=needs_rotation(up_axis),
                              aufloesung=aufloesung, samples=samples,
                              beauty=beauty, material_id=material_id,
                              kamera=kamera, auge=auge, blick_auf=blick_auf,
                              brennweite=brennweite, kamera_modus=kamera_modus,
                              shift_y=shift_y, gelaende_z=gelaende_z,
                              hoehe=hoehe,
                              herzschlag_takt_s=herzschlag_takt_s),
    ]


# ── Alte Namen ───────────────────────────────────────────────────────────────────────
# Der Lauf liefert seit dem Multipass nicht mehr nur eine Tiefenkarte, sondern vier
# Ausgaben; `…_tiefenkarte` benennt also nur noch einen Teil dessen, was passiert. Die
# alten Namen bleiben als Alias stehen, weil sie in `docs/`, in bestehenden Tests und in
# der MCP-Anbindung vorkommen: Ein blosses Umbenennen wäre ein stiller Bruch für jeden
# Aufrufer ausserhalb dieses Repos — und die Prozessgrenze ist genau die Stelle, an der
# dieses Projekt keine stillen Brüche will. Neuer Code nimmt die `…_multipass`-Namen.
glb_zu_tiefenkarte = glb_zu_multipass
baue_kommando_tiefenkarte = baue_kommando_multipass


__all__ = [
    "ContractError", "SeamError",
    "baue_kommando_multipass", "baue_kommando_tiefenkarte",
    "finde_blender", "finde_ifc_python",
    "glb_zu_multipass", "glb_zu_tiefenkarte", "ifc_raeume", "ifc_zu_glb",
]
