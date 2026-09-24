"""RENDER — die Bildmodell-Stufe: Tiefenkarte hinein, Bild heraus.

Warum dieses Modul existiert
----------------------------
Zwischen der Geometrie (Blender-Multipass) und der QA (Geometrie- und Stil-Gate) fehlte
bisher das Stück, das überhaupt ein Bild erzeugt. Es ist zugleich das Stück mit der
grössten Versuchung, unprüfbar zu werden: Ein Bildmodell braucht eine GPU, 20 GB
Gewichte und ``torch``. Wäre die Verdrahtung an diese drei Dinge gebunden, liesse sich
hier — im Entwicklungscontainer ohne GPU — kein einziger Satz über sie beweisen.

Darum ist dieses Modul in zwei Teile geschnitten, und der Schnitt ist der eigentliche
Entwurf:

* Der **Kern** — Parameterprüfung, Backbone-Auflösung, Lizenzentscheid, Aufbau des
  Parameter- und Ergebnissatzes — ist reine stdlib. Er ist hier vollständig prüfbar.
* Die **Naht zum Modell** ist ein einziger injizierbarer Aufruf. Im Test ist das eine
  Attrappe, auf der HomeStation der Aufruf des echten Modells. Dieselbe Bauform wie
  ``_starte`` in ``seams.py`` und ``einbetter`` in ``stil_qa.py``.

Auf der HomeStation (RTX 5090, 32 GB) wird nur die Attrappe durch echte Gewichte
ersetzt. Alles andere — welcher Backbone erlaubt ist, welche Parameter unsinnig sind,
was im Ergebnis steht — ist dann bereits geprüft.

Warum nicht ComfyUI
-------------------
ComfyUI steht unter **GPL-3.0** und ist als Kernbestandteil unter Regel 1
ausgeschlossen. Die Bilderzeugung läuft deshalb direkt über ``diffusers``
(Apache-2.0) — nicht als Notlösung, sondern weil das die einzige Variante ist, die als
Bibliothek in ein permissiv lizenziertes Produkt eingeht (Regel 4: ohne Oberfläche
aufrufbar).

Der Vertrag zwischen Geometrie und Bild: die Depth-ControlNet-Naht
-------------------------------------------------------------------
Die in Blender gerenderte, normalisierte Tiefenkarte (``tiefe_norm.png``, nah = hell)
konditioniert das Modell. Das ist der ganze Punkt des Projekts: Das Modell soll die
**echte Kubatur übernehmen**, statt sich eine plausible auszudenken. Ein Render ohne
diese Konditionierung ist ein hübsches Bild von irgendeinem Haus — genau der Fall, den
``gate.py`` als belegten Anlass des Doppel-Gates beschreibt.

Daraus folgt eine harte Ablehnung: Backbones mit ``integriertes_edit`` (FLUX.2, HiDream)
haben **keine** Depth-ControlNet-Naht. Für sie fehlt eine eigene Adapterschicht. Dieses
Modul tut nicht so, als ginge es — es lehnt ab und sagt warum.

Regel 1 im ausführbaren Pfad
----------------------------
``backbone.pruefe_lizenz`` entscheidet, ob gerendert wird. Ein nicht kommerziell
nutzbares Modell (FLUX.1-dev, FLUX.2-dev) wird abgelehnt, **bevor** irgendetwas geladen
wird. Eine Lizenzregel, die nur in der Doku steht, wird beim nächsten „probier doch mal
FLUX" umgangen; eine, die den Lauf abbricht, nicht.

Warum Ablehnungen ein Ergebnis sind und keine Ausnahme
-------------------------------------------------------
:func:`rendere` wirft bei einer Ablehnung **nicht**, sondern liefert ein Ergebnis mit
``status='abgelehnt'`` und einer Begründung. Die Überlegung ist dieselbe wie in
``gate.py``: Eine Ausnahme kann jemand fangen und weiterlaufen; ein protokolliertes
``status='abgelehnt'`` mit ``bild_png=None`` kann niemand mit einem Erfolg verwechseln.
Dazu kommt der praktische Grund: Das Ergebnis reist über ``auftrag.baue_ergebnis``
zurück von der HomeStation, und dessen Statuswörter (``ok``, ``fehler``, ``abgelehnt``)
sind genau die hier verwendeten. Eine Ausnahme müsste der Ausführende erst wieder in
einen Satz übersetzen — und dabei ginge die Begründung verloren.

Geworfen wird nur dort, wo es gar kein sinnvolles Ergebnis geben kann: in
:func:`lade_modell` (kein ``torch``, keine Gewichte) und wenn :func:`rendere` etwas
bekommt, das gar kein :class:`RenderAuftrag` ist — dann gibt es keine Parameter, die man
protokollieren könnte.

Wo die Gewichte liegen — und warum das eine Startsperre war
------------------------------------------------------------
Bis zum 18.09.2026 stand hier ``VORGABE_MODELLWURZEL = "/ai"``. Das ist eine Konvention
der HomeStation; auf dem MacBook, das jetzt die Zielhardware ist, liegt ``/ai`` direkt
unter der nicht beschreibbaren Systemwurzel, und auf Windows gibt es den Pfad gar nicht.
Der erste Start einer fremden Maschine endete damit in einem Rechtefehler aus dem Inneren
einer Bibliothek, bevor ein einziges Modell geladen war.

Neu gilt eine Leiter aus drei Stufen (:func:`modellwurzel`): ``$AIIMAGING_MODELLE``,
dann ``/ai`` **falls vorhanden**, dann der Anwendungsdatenort des Betriebssystems
(:func:`anwendungsdaten_wurzel`).

Was sich für die HomeStation ändert — und was nicht
....................................................
Sie fährt denselben Code aus demselben Repo; ein ``git pull`` dort darf ihr Verhalten
nicht unangesagt ändern. **Gemessen** (`auf-20260823-36`, `auf-20260826-42`) läuft sie
mit gesetztem ``AIIMAGING_MODELLE=/mnt/data/ai-models/diffusers`` — Stufe 1, und die ist
unverändert. Für jeden Lauf, der die Variable setzt, ändert sich also nichts.

``/ai`` existiert dort **nicht**: `auf-20260823-36` sagt es ausdrücklich, und
`auf-20260823-38` zeigt es gemessen (*«unter '/ai/sdxl-juggernaut' (Verzeichnis
existiert: False)»*). Stufe 2 trifft auf der HomeStation also nicht — sie ist kein
Bestandsschutz, sondern eine Rückfalllinie für jede Maschine, die ``/ai`` doch führt.

Damit bleibt **eine** Verhaltensänderung drüben, und sie wird hier benannt statt
behauptet weg zu sein: Ein Lauf **ohne** ``AIIMAGING_MODELLE`` nannte bisher
``/ai/<modell>`` in seiner Meldung und nennt jetzt den Anwendungsdatenort. Der Lauf
scheitert in beiden Fällen (die Gewichte liegen weder hier noch dort) — nur der genannte
Pfad ist ein anderer. Das ist die Art Änderung, die nach CLAUDE.md angesagt gehört,
bevor sie ankommt.

Abhängigkeiten: keine. Reine stdlib. ``torch`` und ``diffusers`` werden **ausschliesslich
innerhalb** von :func:`lade_modell` importiert — ein Import auf Modulebene machte
``import aiimaging.render`` auf jedem Rechner ohne GPU-Stack unmöglich und hinge damit
die halbe Bildkette an Hardware, die es hier nicht gibt.
"""
from __future__ import annotations

import math
import os
import platform
import re
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path, PurePosixPath, PureWindowsPath

from aiimaging import backbone, sprache

#: Die Konditionierung, die dieses Modul bedient. Alles andere braucht eine eigene
#: Adapterschicht und wird abgelehnt (siehe Modul-Docstring).
KOND_DEPTH_CONTROLNET = backbone.KOND_DEPTH_CONTROLNET
KOND_INTEGRIERTES_EDIT = backbone.KOND_INTEGRIERTES_EDIT
KONDITIONIERUNGEN = backbone.KONDITIONIERUNGEN

#: Vorgabe-Backbone, aus der Registry übernommen statt hier zweitgeschrieben. Ein
#: eigener Vorgabewert an dieser Stelle liefe beim nächsten Registry-Wechsel auseinander.
VORGABE_BACKBONE = backbone.VORGABE_BACKBONE

# --------------------------------------------------------------------------------------
# Wo die Gewichte liegen — drei Stufen, und die erste gehört der Umgebung
# --------------------------------------------------------------------------------------

#: Umgebungsvariable für die Modellwurzel. Sie hat Vorrang vor allem anderen: Wer eine
#: eigene Ablage hat, nennt sie hier und behält sie. Dasselbe Muster wie
#: ``AIIMAGING_BLENDER`` in ``seams.py``.
UMGEBUNG_MODELLE = "AIIMAGING_MODELLE"

#: Die Ablage der HomeStation (siehe ``auftrag.py``): Dort liegen die Gewichte unter
#: ``/ai``, jedes Modell in einem eigenen Unterordner mit seinem Registry-Namen.
#:
#: Der Pfad wird **vor** dem Betriebssystem-Vorgabeort geprüft — aber nur, wenn es ihn
#: als Verzeichnis wirklich gibt. Auf einem MacBook gibt es ihn nicht (``/`` ist dort die
#: nicht beschreibbare Wurzel), auf Windows kennt ihn niemand; dort fällt die Stufe still
#: weg. Sie kostet einen ``is_dir``-Aufruf.
#:
#: **Diese Stufe ist NICHT der Bestandsschutz der HomeStation** — das wäre eine bequeme
#: Behauptung, und sie ist gemessen falsch: `auf-20260823-36` hält fest, dass ``/ai``
#: *«auf dieser Maschine nicht existiert»*, und `auf-20260823-38` zeigt es im Lauf
#: (*«Verzeichnis existiert: False»*). Die HomeStation bleibt bei ihrer Ablage, weil sie
#: ``AIIMAGING_MODELLE`` setzt — Stufe 1, gemessen in `auf-20260823-36` und
#: `auf-20260826-42`. Was diese Stufe leistet, ist schmaler: Jede Maschine, die ``/ai``
#: **doch** führt, behält es, ohne etwas zu setzen. Der Rest steht im Modul-Docstring,
#: samt der einen Verhaltensänderung, die drüben bleibt.
ALTWURZEL_HOMESTATION = "/ai"

#: Woher die Wurzel stammt. Die Auskunft gehört ins Ergebnis: „nicht gefunden" braucht
#: je nach Herkunft einen anderen Handgriff (Variable setzen / Variable berichtigen /
#: Ordner anlegen).
HERKUNFT_UMGEBUNG = "umgebung"
HERKUNFT_ALTWURZEL = "altwurzel"
HERKUNFT_ANWENDUNGSDATEN = "anwendungsdaten"

#: Ordnername unter den Anwendungsdaten. Gross auf macOS und Windows, klein unter XDG —
#: so schreiben es die jeweiligen Konventionen, und ein Ordner, der aussieht wie die
#: Nachbarn, wird von seinem Besitzer wiedererkannt.
ANWENDUNG = "Visbox"
ANWENDUNG_KLEIN = "visbox"

#: Unterordner unter dem Anwendungsordner. Getrennt, weil unter denselben Anwendungsdaten
#: später anderes liegen kann (Zwischenstände, Protokolle) und Gewichte zweistellige
#: Gigabyte gross sind — wer aufräumt, soll einen Ordner treffen können.
UNTERORDNER_MODELLE = "modelle"


def _ist_absolut(wert, system) -> bool:
    """Ist dieser Pfad **auf dem gemeinten System** absolut?

    **Der Anlass** (Gegenpruefung 18.09.2026, gemessen und nicht vermutet): Bis dahin
    stand hier schlicht ``Path(wert).is_absolute()``. ``Path`` ist aber der Pfadtyp des
    *laufenden* Rechners — auf Linux eine ``PosixPath``, und die haelt
    ``C:/Users/nutzer/AppData/Local`` fuer **relativ**. Der Windows-Zweig fiel damit auf
    jedem Linux-Rechner immer durch die Pruefung; was danach herauskam, war der Rueckfall
    ``heim/AppData/Local`` und nie der gelesene Wert. Belegt wurde das so: Ersetzt man in
    :func:`anwendungsdaten_wurzel` ``LOCALAPPDATA`` durch ``APPDATA``, blieben vorher
    **alle** Proben gruen — ein Waechter, der nicht faellt, bewacht nichts.

    Die Naht ``system=`` gibt es genau dafuer, dass der Windows- und der macOS-Weg auch
    auf einem Linux-Container belegbar sind. Eine Naht, die etwas anderes rechnet als die
    Zielmaschine, belegt aber nichts — also wird hier nach den Regeln des **gemeinten**
    Systems gerechnet: ``PureWindowsPath`` fuer Windows, sonst ``PurePosixPath``. Beide
    rechnen rein, ohne das Dateisystem anzufassen.

    Auf echtem Windows ist ``Path`` eine ``WindowsPath`` und damit selbst eine
    ``PureWindowsPath``; dort aendert sich das Urteil nicht. Was sich aendert, steht bei
    :func:`anwendungsdaten_wurzel`.
    """
    # `os.fspath` und nicht der Wert selbst: Wird ein fertiger Pfad eines **anderen**
    # Geschmacks uebergeben (eine `PosixPath` etwa), uebernimmt `PureWindowsPath` dessen
    # bereits zerlegte Teile, statt neu zu zerlegen — `PureWindowsPath(PosixPath(
    # "C:/Users/nutzer")).is_absolute()` ergibt **False** (gemessen, Python 3.11). Ueber
    # die Zeichenkette wird neu gelesen, und nur das beantwortet die gestellte Frage.
    text = os.fspath(wert)
    if system == "Windows":
        return PureWindowsPath(text).is_absolute()
    return PurePosixPath(text).is_absolute()


def anwendungsdaten_wurzel(*, system=None, umgebung=None, heim=None) -> Path:
    """Der Ort, an dem dieses Betriebssystem Anwendungsdaten erlaubt.

    **Der Anlass** (18.09.2026, Umstellung auf Visbox): Zielhardware war damals der Laptop
    einer Studierenden — ein MacBook M1 Max, nicht mehr die HomeStation. *Diese Prämisse
    ist am 21.09.2026 zurückgenommen worden (E21); diese Funktion bleibt.* Sie ersetzt
    einen Pfad, der nur auf einer Maschine existiert, durch den je System üblichen Ort —
    das ist unter Regel 4 richtig, gleich welche Maschine die Referenz ist. Der bisherige
    Vorgabepfad ``/ai`` ist dort ein Ordner direkt unter der Systemwurzel, und die ist
    nicht beschreibbar. Wer Visbox startet, bekommt einen Rechtefehler aus dem Inneren
    einer Bibliothek, bevor ein einziges Modell geladen wird. Auf Windows gibt es ``/ai``
    überhaupt nicht.

    Gewählt wird je System der übliche Ort — **gesetzt** nach der jeweiligen Konvention,
    nicht gemessen:

    * **macOS**: ``~/Library/Application Support/Visbox/modelle``. Apple sieht
      *Application Support* für Daten vor, die eine Anwendung selbst anlegt und die der
      Benutzer nicht direkt bearbeitet.
    * **Windows**: ``%LOCALAPPDATA%\\Visbox\\modelle`` — **Local**, nicht *Roaming*:
      Roaming wird zwischen Maschinen synchronisiert, und zwanzig Gigabyte Gewichte durch
      ein Firmennetz zu schieben ist kein Versehen, das man einer Studentin zumutet.
    * **Linux und alles übrige**: ``$XDG_DATA_HOME/visbox/modelle``, ersatzweise
      ``~/.local/share/visbox/modelle`` (XDG Base Directory Specification).

    Die XDG-Spezifikation verlangt ausdrücklich, eine **relative** Angabe in
    ``XDG_DATA_HOME`` zu ignorieren; dasselbe gilt hier für ``LOCALAPPDATA``. Ein
    relativer Modellpfad zeigte je nach Arbeitsverzeichnis woandershin — das ist genau
    die Sorte Fehler, die als Modellfehler missverstanden wird.

    **Und dasselbe gilt für ``heim``** (Gegenprüfung 18.09.2026): Bis dahin prüfte diese
    Funktion die beiden Variablen und das Heimverzeichnis nicht. ``heim="~"`` ergab
    ``~/.local/share/visbox/modelle`` — relativ, also genau der Fehler, den der Absatz
    darüber beschreibt. Erreichbar ist das nicht nur über die Naht: ``expanduser("~")``
    gibt ``"~"`` unverändert zurück, wenn sich weder ``HOME`` noch ein Eintrag in der
    Benutzerdatenbank finden lässt. Siehe den Ersatz unten im Code.

    **Absolut nach den Regeln welches Systems?** Nach denen von ``system`` — siehe
    :func:`_ist_absolut`. Das ist eine **Verhaltensänderung** gegenüber dem Stand vor dem
    18.09.2026, und sie betrifft genau einen Fall: einen Aufruf mit ``system="Windows"``
    auf einem Nicht-Windows-Rechner. Ein Windows-Pfad mit Laufwerksbuchstabe
    (``C:/…``) galt dort bisher als relativ und wurde still verworfen; jetzt gilt er als
    absolut und wird verwendet — also so, wie es die Zielmaschine täte. Auf echtem
    Windows, macOS und Linux ändert sich nichts.

    Args:
        system: Naht für die Probe. ``None`` heisst :func:`platform.system`. Nur so lässt
            sich der macOS- und der Windows-Weg auf einem Linux-Container belegen — ohne
            diese Naht wäre der Befund, um den es hier geht, unprüfbar.
        umgebung: Naht für die Probe. ``None`` heisst ``os.environ``.
        heim: Naht für die Probe. ``None`` heisst das Heimverzeichnis dieses Benutzers.

    Reine Pfadrechnung — mit **einer** Ausnahme, und die steht hier, weil ein Satz, der
    eine Eigenschaft behauptet, die nicht gilt, schlimmer ist als gar keiner: Lässt sich
    das Heimverzeichnis nicht ermitteln, fragt der Ersatz einmal
    :func:`tempfile.gettempdir`, und der legt beim ersten Aufruf eine Probedatei an und
    entfernt sie wieder. Auf jedem Rechner mit Heimverzeichnis — also in jedem normalen
    Lauf — wird nichts angelegt, nichts geprüft und nichts geladen.
    """
    system = platform.system() if system is None else system
    umgebung = os.environ if umgebung is None else umgebung
    # `expanduser("~")` statt `Path.home()`: Es wirft nicht, wenn sich das
    # Heimverzeichnis nicht ermitteln lässt. Ein Import, der wegen eines fehlenden HOME
    # abbricht, machte das ganze Modul unbenutzbar — und dieses Modul wird importiert,
    # lange bevor jemand ein Gewicht sucht.
    heim = Path(os.path.expanduser("~")) if heim is None else Path(heim)
    if not _ist_absolut(heim, system):
        # Der Ersatz ist der Temporärordner: absolut, vorhanden, beschreibbar. Er ist
        # keine gute Ablage für zwanzig Gigabyte Gewichte — aber `modellwurzel_lage`
        # nennt ihn dann im Klartext samt Handgriff, und das ist mehr, als ein relativer
        # Pfad je zugelassen hätte. Abbrechen fällt aus (siehe oben), und ein relatives
        # Ergebnis durchzulassen wäre das, was diese Funktion für `XDG_DATA_HOME` und
        # `LOCALAPPDATA` ausdrücklich abwehrt.
        heim = Path(tempfile.gettempdir())

    if system == "Darwin":
        return heim / "Library" / "Application Support" / ANWENDUNG / UNTERORDNER_MODELLE
    if system == "Windows":
        lokal = umgebung.get("LOCALAPPDATA")
        basis = Path(lokal) if lokal and _ist_absolut(lokal, system) \
            else heim / "AppData" / "Local"
        return basis / ANWENDUNG / UNTERORDNER_MODELLE
    xdg = umgebung.get("XDG_DATA_HOME")
    basis = Path(xdg) if xdg and _ist_absolut(xdg, system) \
        else heim / ".local" / "share"
    return basis / ANWENDUNG_KLEIN / UNTERORDNER_MODELLE


#: Der Vorgabeort dieses Rechners, einmal beim Import gerechnet. Er bleibt ein
#: beschreibbarer Name (und keine Funktion), weil Proben ihn ersetzen und weil ein
#: Herkunftspfad, den man nicht nennen kann, in keiner Fehlermeldung auftaucht.
#: **Setzung**, keine Messung: Ob dort etwas liegt, sagt :func:`modellwurzel_lage`.
VORGABE_MODELLWURZEL = str(anwendungsdaten_wurzel())

#: Obergrenze für die Schrittzahl. Nicht physikalisch begründet, sondern als Schutz vor
#: dem Tippfehler: ``schritte=2000`` läuft nicht falsch, es läuft stundenlang und
#: blockiert die einzige GPU des Projekts. Wer mehr braucht, hebt die Grenze bewusst an.
MAX_SCHRITTE = 200

#: Obergrenze für den Seed. 2**32-1 ist die Grenze, die ``numpy`` verträgt; ``torch``
#: könnte mehr, aber ein Seed, der nur in einem der beiden Räume gültig ist, ist für die
#: Reproduzierbarkeit wertlos.
MAX_SEED = 2 ** 32 - 1

#: Statuswörter. Wortgleich mit ``auftrag.baue_ergebnis`` — ein Render-Ergebnis soll
#: ohne Übersetzung in ein HomeStation-Ergebnis passen.
STATUS_OK = "ok"
STATUS_ABGELEHNT = "abgelehnt"
STATUS_FEHLER = "fehler"
STATUSSE = (STATUS_OK, STATUS_ABGELEHNT, STATUS_FEHLER)

#: Betriebsarten. Beide konditionieren über die Tiefenkarte; sie unterscheiden sich
#: darin, ob es ein Ausgangsbild gibt, das überschrieben wird.
MODUS_TXT2IMG = "txt2img"
MODUS_IMAGE_EDIT = "image_edit"


class RenderError(RuntimeError):
    """Der Render kann nicht einmal versucht werden.

    Bewusst eine Ausnahme und kein Ergebnis: Sie fliegt nur dort, wo es nichts zu
    protokollieren gäbe — kein ``torch``, keine Gewichte, oder gar kein Auftrag. Alles,
    was einen Auftrag hat, wird als Ergebnis mit ``status`` und ``error`` beantwortet
    (siehe Modul-Docstring).
    """


@dataclass(frozen=True)
class RenderAuftrag:
    """Ein Bildauftrag — alles, was einen Render vollständig bestimmt.

    Args:
        depth_png: Normalisierte Tiefenkarte aus dem Blender-Multipass (nah = hell).
            **Pflicht.** Ohne sie gäbe es keine Konditionierung, und das Modell erfände
            eine Kubatur — genau der Fall, gegen den dieses Projekt antritt.
        prompt: Was zu sehen sein soll. Die Kubatur kommt aus der Tiefenkarte, der Prompt
            trägt Material, Licht und Stimmung.
        negativ_prompt: Was nicht zu sehen sein soll.
        backbone: Name aus :data:`aiimaging.backbone.BACKBONES`. **Kein freier Text** —
            der Eintrag entscheidet über Lizenz und Konditionierungsart.
        seed: Startwert des Zufalls. Gehört zwingend ins Ergebnis: Ohne ihn ist ein
            Render nicht wiederholbar, und ohne Wiederholbarkeit gibt es keine
            Schwellenstudie.
        schritte: Anzahl Diffusionsschritte.
        controlnet_staerke: Wie stark die Tiefenkarte das Bild bindet, 0..1. Klein heisst
            freier und schöner, gross heisst geometrietreuer. Diese Zahl ist der
            eigentliche Regler des Projekts — sie gehört deshalb ins Ergebnis.
        fuehrung: ``guidance_scale`` — wie stark der Prompt das Bild zwingt. ``None``
            übernimmt den Wert des Backbones; hat auch der keinen, greift die Vorgabe von
            ``diffusers``, und das Ergebnis sagt es als Hinweis. Unterhalb von 1.0 ist der
            **negative Prompt wirkungslos**, weil die klassifikatorfreie Führung dann
            abgeschaltet ist.
        denoise: Wie stark das Ausgangsbild überschrieben wird, 0..1. Wirkt nur, wenn
            ``beauty_png`` gesetzt ist (Modus ``image_edit``); ohne Ausgangsbild gibt es
            nichts zu überschreiben. Der Wert wird dann nicht heimlich verworfen, sondern
            als Hinweis im Ergebnis vermerkt.
        beauty_png: Beauty-Pass aus dem Multipass als Anker. Gesetzt heisst echtes
            Image-Edit statt txt2img — das Modell arbeitet am gerenderten Bild weiter,
            statt aus dem Nichts zu beginnen.
        ausgabe_png: Wohin das Bild geschrieben werden soll. ``None`` überlässt die Wahl
            dem Modell — dann entfällt allerdings der Schutz gegen ein liegengebliebenes
            Bild aus einem früheren Lauf (siehe :func:`rendere`).
        modell_wurzel: Verzeichnis der Gewichte dieses Backbones. ``None`` heisst
            :func:`standard_modell_wurzel`. Wird **nicht** geprüft, solange ein fertiges
            Modell übergeben wird — sonst wäre kein Testlauf ohne Gewichte möglich.

    ``frozen=True``: Ein Auftrag ist das Protokoll dessen, was gerechnet wurde. Würde ihn
    jemand während des Laufs verändern, stimmte das protokollierte Ergebnis nicht mehr
    mit der Rechnung überein — und die Reproduzierbarkeit wäre eine Behauptung.
    """

    depth_png: str
    prompt: str
    negativ_prompt: str = ""
    backbone: str = VORGABE_BACKBONE
    seed: int = 0
    schritte: int = 20
    controlnet_staerke: float = 0.8
    denoise: float = 0.6
    fuehrung: float | None = None
    beauty_png: str | None = None
    ausgabe_png: str | None = None
    modell_wurzel: str | None = None


def modellwurzel(*, umgebung=None) -> tuple[Path, str]:
    """Welche Modellwurzel auf diesem Rechner gilt — **und woher sie kommt**.

    Drei Stufen, in dieser Reihenfolge, und die Reihenfolge ist der ganze Entwurf:

    1. ``$AIIMAGING_MODELLE`` — die Umgebung gewinnt immer. Sie ist der Weg, auf dem eine
       Maschine ihre Ablage festschreibt, ohne dass wir Code ändern.
    2. :data:`ALTWURZEL_HOMESTATION` (``/ai``) — **aber nur, wenn es den Ordner gibt.**
       Wer ``/ai`` führt, behält es, ohne etwas zu setzen; bei einer Studentin fällt die
       Stufe durch. Sie ist ausdrücklich **nicht** der Bestandsschutz der HomeStation:
       Dort gibt es ``/ai`` gemessen nicht (`auf-20260823-36`, `auf-20260823-38`), dort
       trifft Stufe 1. Siehe :data:`ALTWURZEL_HOMESTATION`.
    3. :data:`VORGABE_MODELLWURZEL` — der Anwendungsdatenort dieses Betriebssystems
       (siehe :func:`anwendungsdaten_wurzel`).

    Returns:
        ``(wurzel, herkunft)`` mit ``herkunft`` aus :data:`HERKUNFT_UMGEBUNG`,
        :data:`HERKUNFT_ALTWURZEL`, :data:`HERKUNFT_ANWENDUNGSDATEN`.

    Args:
        umgebung: Naht für die Probe. ``None`` heisst ``os.environ`` — **und nur dann**
            liefert Stufe 3 die Modulkonstante :data:`VORGABE_MODELLWURZEL`.

            Das war bis zum 18.09.2026 anders, und es war eine halbe Naht (gemessen):
            ``modellwurzel(umgebung={"XDG_DATA_HOME": "/erfundenes/xdg"})`` ergab den
            Anwendungsdatenort *dieses* Rechners, während
            ``anwendungsdaten_wurzel(umgebung=dasselbe)`` ``/erfundenes/xdg/…`` ergab.
            Stufe 3 las eben die Konstante, und die wird **einmal beim Import** gerechnet.
            Eine Naht, die nur zwei von drei Stufen erreicht, kann die dritte nicht
            prüfen — sie sieht bloss so aus.

            Neu: Wird eine Umgebung übergeben, rechnet auch Stufe 3 mit ihr. Das ist eine
            **Verhaltensänderung**, und sie trifft ausschliesslich Aufrufe mit
            ``umgebung=``; ohne Argument bleibt alles, wie es war — auch für Proben, die
            :data:`VORGABE_MODELLWURZEL` ersetzen.
    """
    # WARUM vorher gemerkt: Eine Zeile später ist `umgebung` in beiden Fällen belegt, und
    # die Unterscheidung wäre verloren. Sie lautet nicht „ist das os.environ?", sondern
    # „hat der Aufrufer eine Umgebung genannt?" — nur im zweiten Fall darf Stufe 3 die
    # Modulkonstante übergehen, die Proben absichtlich ersetzen.
    eigene_umgebung = umgebung is not None
    umgebung = os.environ if umgebung is None else umgebung
    if (gesetzt := umgebung.get(UMGEBUNG_MODELLE)):
        return Path(gesetzt), HERKUNFT_UMGEBUNG
    alt = Path(ALTWURZEL_HOMESTATION)
    try:
        alt_vorhanden = alt.is_dir()
    except OSError:
        # Ein unlesbarer Ort ist keine Antwort, also zählt er nicht als Treffer. Auf
        # einem gesperrten Laufwerk soll der Start nicht an dieser Frage scheitern.
        alt_vorhanden = False
    if alt_vorhanden:
        return alt, HERKUNFT_ALTWURZEL
    if eigene_umgebung:
        return anwendungsdaten_wurzel(umgebung=umgebung), HERKUNFT_ANWENDUNGSDATEN
    return Path(VORGABE_MODELLWURZEL), HERKUNFT_ANWENDUNGSDATEN


def standard_modell_wurzel(backbone_name: str) -> Path:
    """Wo die Gewichte eines Backbones vermutet werden, wenn nichts angegeben ist.

    :func:`modellwurzel` plus der Registry-Name als Unterordner. Die Umgebungsvariable
    hat Vorrang, damit die Ablage austauschbar bleibt — dasselbe Muster wie
    ``AIIMAGING_BLENDER`` in ``seams.py``.

    Es wird **nichts geladen und nichts angelegt** — aber der Satz „nichts geprüft", der
    hier bis zum 18.09.2026 stand, war falsch (Gegenprüfung desselben Tages): Stufe 2 von
    :func:`modellwurzel` fragt das Dateisystem einmal, ob es
    :data:`ALTWURZEL_HOMESTATION` als Verzeichnis gibt. Ein ``is_dir``-Aufruf, mehr nicht,
    und ein Fehler daraus wird dort gefangen.

    Was der Satz sagen wollte, gilt weiterhin: Diese Funktion ist auch dort aufrufbar, wo
    kein einziges Gewicht liegt, und sie sagt nichts darüber, ob dort etwas liegt — das
    beantwortet :func:`modellwurzel_lage`.
    """
    return modellwurzel()[0] / backbone_name


def schreibprobe(pfad) -> dict:
    """Dürfte dort etwas angelegt werden? — gefragt am nächsten vorhandenen Elternordner.

    Warum der Elternordner: Die Modellwurzel selbst gibt es ja gerade nicht, sonst stünde
    die Frage nicht. Beschreibbar sein muss der Ort, an dem sie entstünde.

    Returns:
        ``{pfad, anker, beschreibbar, grund}``. ``beschreibbar`` ist ``None``, wenn die
        Frage **nicht gemessen** werden konnte — nicht ``False``: „darf nicht" und „weiss
        nicht" verlangen verschiedene Handgriffe, und die dritte Antwort dieses Projekts
        heisst nicht „in Ordnung".

    Reine Dateisystemauskunft, kein Schreibversuch: Eine Probedatei in einem fremden
    Ordner anzulegen ist eine Nebenwirkung, und Nebenwirkungen beim Nachsehen sind der
    Anfang von Schäden. ``os.access`` kann bei ausgefallenen Rechtemodellen (ACLs,
    Netzlaufwerke) irren — deshalb trägt die Meldung einen Handgriff und kein Urteil.
    """
    ziel = Path(pfad).expanduser()
    anker = None
    for kandidat in (ziel, *ziel.parents):
        try:
            if kandidat.is_dir():
                anker = kandidat
                break
        except OSError as fehler:
            return {"pfad": str(ziel), "anker": None, "beschreibbar": None,
                    "grund": f"Der Ort liess sich nicht befragen ({fehler})."}
    if anker is None:
        return {"pfad": str(ziel), "anker": None, "beschreibbar": None,
                "grund": "Kein vorhandener Elternordner gefunden — nicht gemessen."}
    try:
        erlaubt = os.access(anker, os.W_OK | os.X_OK)
    except OSError as fehler:
        return {"pfad": str(ziel), "anker": str(anker), "beschreibbar": None,
                "grund": f"Die Rechte liessen sich nicht lesen ({fehler})."}
    return {"pfad": str(ziel), "anker": str(anker), "beschreibbar": bool(erlaubt),
            "grund": ""}


def _wegweiser(wurzel: Path, probe: dict) -> str:
    """Der Satz, der aus einer Diagnose einen Handgriff macht.

    Ohne ihn endet die Meldung bei „gibt es nicht", und der Leser darf raten, ob er einen
    Ordner anlegen, eine Variable setzen oder den Rechner wechseln soll.
    """
    if probe["beschreibbar"] is None:
        return (f" Ob sich {str(wurzel)!r} anlegen lässt, wurde NICHT GEMESSEN "
                f"({probe['grund']}). Handgriff: einen Ordner anlegen, in dem Sie "
                f"schreiben dürfen, und {UMGEBUNG_MODELLE} darauf setzen.")
    if probe["beschreibbar"]:
        return (f" Der Ort lässt sich anlegen ({probe['anker']!r} ist beschreibbar): "
                f"Ordner {str(wurzel)!r} erzeugen und die Gewichte hineinlegen — oder "
                f"{UMGEBUNG_MODELLE} auf eine vorhandene Ablage setzen.")
    return (f" Und dort darf nichts angelegt werden: {probe['anker']!r} ist für Sie "
            f"nicht beschreibbar. Das ist kein Modellfehler und keine kaputte "
            f"Installation. Handgriff: {UMGEBUNG_MODELLE} auf einen Ordner setzen, in "
            f"dem Sie schreiben dürfen.")


def modellwurzel_lage(backbone_name: str) -> dict:
    """Liegt dort, wo die Gewichte vermutet werden, überhaupt etwas? — **und woher der Pfad kommt**.

    **Der Anlass ist ein stiller Rückfall** (HomeStation, `auf-vis-20260826-16`,
    26.08.2026): Ohne gesetztes ``AIIMAGING_MODELLE`` fällt der Lauf auf
    :data:`VORGABE_MODELLWURZEL` zurück und bricht erst viel später ab mit
    *«Gewichte für 'z-image-turbo' unvollständig»*. Die Meldung nennt das Modell und
    verschweigt, dass der Pfad, unter dem gesucht wurde, gar nicht existiert — und der
    Suchende prüft dann das Modell statt die Umgebung.

    *Ein Ersatzpfad, der nirgends existiert, ist keine Vorgabe, sondern ein Ratefehler mit
    Schrägstrich.*

    **Der zweite Anlass** (18.09.2026): Auf einem MacBook war der Ersatzpfad ``/ai`` nicht
    nur leer, sondern unanlegbar — ``/`` ist dort nicht beschreibbar. Wer der bisherigen
    Meldung folgte und den Ordner anlegte, bekam einen Rechtefehler statt einer Antwort.
    Darum steht hier jetzt auch, **ob** sich der Ort anlegen lässt.

    Returns:
        ``{wurzel, herkunft, aus_umgebung, existiert, beschreibbar, schreibanker,
        umgebung, grund}``. ``grund`` ist ``""``, wenn nichts zu sagen ist;
        ``beschreibbar`` ist ``None``, wenn die Frage nicht gemessen werden konnte, und
        ebenfalls ``None``, wenn sie sich nicht stellt (der Ordner ist da).

    Reine Pfad- und Dateisystemauskunft: Es wird nichts geladen und nichts angelegt. Damit
    bleibt die Funktion dort prüfbar, wo kein einziges Gewicht liegt — also hier.
    """
    basis, herkunft = modellwurzel()
    wurzel = basis / backbone_name
    existiert = wurzel.is_dir()

    if existiert:
        # Keine Schreibprobe: Zum Laden von Gewichten muss niemand schreiben dürfen, und
        # eine Meldung, die bei jedem gesunden Lauf mitläuft, wird nach drei Tagen
        # überlesen.
        return {"wurzel": str(wurzel), "herkunft": herkunft,
                "aus_umgebung": herkunft == HERKUNFT_UMGEBUNG, "existiert": True,
                "beschreibbar": None, "schreibanker": None,
                "umgebung": UMGEBUNG_MODELLE, "grund": ""}

    probe = schreibprobe(wurzel)
    if herkunft == HERKUNFT_UMGEBUNG:
        grund = (f"{UMGEBUNG_MODELLE} zeigt auf {str(wurzel.parent)!r}, und dort liegt "
                 f"kein Ordner {backbone_name!r}. Der Pfad ist gesetzt und trifft nicht.")
    elif herkunft == HERKUNFT_ALTWURZEL:
        grund = (f"{UMGEBUNG_MODELLE} ist NICHT gesetzt; es gilt die vorhandene Ablage "
                 f"{ALTWURZEL_HOMESTATION!r}, und dort liegt kein Ordner "
                 f"{backbone_name!r}. Das ist keine Aussage ueber das Modell, sondern "
                 f"ueber die Umgebung (auf-vis-20260826-16).")
    else:
        grund = (f"{UMGEBUNG_MODELLE} ist NICHT gesetzt; es gilt der Vorgabeort dieses "
                 f"Betriebssystems {str(wurzel.parent)!r}, und dort liegt kein Ordner "
                 f"{backbone_name!r}. Das ist keine Aussage ueber das Modell, sondern "
                 f"ueber die Umgebung — wer hier das Modell prueft, sucht am falschen "
                 f"Ort (auf-vis-20260826-16).")
    grund += _wegweiser(wurzel, probe)

    return {"wurzel": str(wurzel), "herkunft": herkunft,
            "aus_umgebung": herkunft == HERKUNFT_UMGEBUNG, "existiert": False,
            "beschreibbar": probe["beschreibbar"], "schreibanker": probe["anker"],
            "umgebung": UMGEBUNG_MODELLE, "grund": grund}


# --------------------------------------------------------------------------------------
# Prüfung — der ganze Entscheid, bevor irgendetwas Teures passiert
# --------------------------------------------------------------------------------------

def _pruefe_anteil(wert, bezeichnung: str, maengel: list[str]) -> None:
    """Eine Zahl in ``[0, 1]``. ``bool`` zählt nicht als Zahl.

    ``True`` als Stärke wäre 1.0 und liefe stillschweigend durch — es ist aber immer ein
    Irrtum, und stillschweigend zurechtbiegen tut dieses Projekt nirgends.
    """
    if isinstance(wert, bool) or not isinstance(wert, (int, float)):
        maengel.append(f"{bezeichnung} ist keine Zahl: {wert!r}")
        return
    zahl = float(wert)
    if not math.isfinite(zahl):
        maengel.append(f"{bezeichnung} ist nicht endlich: {wert!r}")
    elif not (0.0 <= zahl <= 1.0):
        maengel.append(
            f"{bezeichnung} liegt mit {zahl} ausserhalb von 0..1. Ausserhalb dieses "
            f"Bereichs ist der Wert nicht definiert — er wird nicht geklemmt."
        )


def _pruefe_datei(pfad, bezeichnung: str, maengel: list[str]) -> None:
    """Ein Eingabebild muss vorliegen. Existenz, nicht Inhalt.

    Warum überhaupt: Ein fehlendes Bild fällt sonst erst auf, nachdem 20 GB Gewichte
    geladen sind. Dieselbe Überlegung wie ``backbone.vorhandene_dateien`` — die billige
    Frage zuerst stellen.
    """
    if not isinstance(pfad, str) or not pfad.strip():
        maengel.append(f"{bezeichnung} fehlt oder ist kein Pfad: {pfad!r}")
        return
    if not Path(pfad).is_file():
        maengel.append(f"{bezeichnung} liegt nicht vor: {pfad!r}")


def pruefe_auftrag(a: RenderAuftrag) -> list[str]:
    """Alle Mängel eines Auftrags auf einmal. Leere Liste heisst: in Ordnung.

    Returns:
        Liste von Sätzen für Menschen. **Alle** Mängel, nicht nur der erste — wer einen
        Auftrag von Hand baut, soll nicht fünfmal hintereinander scheitern.

    Geprüft wird, in dieser Reihenfolge:

    1. **Lizenz** (Regel 1) — ein nicht kommerziell nutzbares Modell ist ausgeschlossen,
       und zwar bevor eine einzige Datei angefasst wird.
    2. **Konditionierungsart** — bis zum 18.08.2026 wies diese Prüfung alles ab, was
       nicht ``depth_controlnet`` war, mit der Begründung, es fehle eine Adapterschicht.
       **Der erste echte Render hat das widerlegt** (`auf-20260818-09`): Der Adapter
       trägt ``integriertes_edit`` sehr wohl — er übergibt die Tiefenkarte als ``image``.
       Was er nicht kann, ist ein Regler dafür; das meldet er je Lauf als Hinweis.
       Abgewiesen wird darum nur noch eine **unbekannte** Art.
    3. Eingabedateien, dann Zahlenbereiche.

    Die Reihenfolge ist Absicht: Die bindendste und billigste Prüfung zuerst. Ein
    FLUX-dev-Auftrag soll nicht daran scheitern, dass zufällig auch der Prompt leer war —
    er soll an der Lizenz scheitern.

    Diese Funktion rührt **kein** Modell an und prüft **nicht**, ob Gewichte vorliegen.
    Das ist der Grund, warum sie hier ohne GPU vollständig geprüft werden kann; ob die
    Gewichte da sind, weiss erst :func:`lade_modell`.
    """
    if not isinstance(a, RenderAuftrag):
        return [f"Kein RenderAuftrag, sondern {type(a).__name__}."]

    maengel: list[str] = []

    # --- Backbone, Lizenz, Konditionierung ------------------------------------------
    try:
        eintrag = backbone.hole(a.backbone)
    except backbone.BackboneError as fehler:
        # Der Registry-Fehler nennt bereits die bekannten Namen — nicht umformulieren,
        # sonst geht die Liste verloren.
        maengel.append(str(fehler))
        eintrag = None

    if eintrag is not None:
        lizenz = backbone.pruefe_lizenz(eintrag.name)
        if not lizenz["zulaessig"]:
            maengel.append(
                f"Backbone {eintrag.name!r} ist unter Regel 1 ausgeschlossen: "
                f"{lizenz['begruendung']}"
            )
        if eintrag.konditionierung not in KONDITIONIERUNGEN:
            maengel.append(
                f"Backbone {eintrag.name!r} nennt eine unbekannte Konditionierungsart "
                f"{eintrag.konditionierung!r}. Bekannt: {', '.join(KONDITIONIERUNGEN)}."
            )

    # --- Eingaben --------------------------------------------------------------------
    _pruefe_datei(a.depth_png, "Tiefenkarte (depth_png)", maengel)
    if a.beauty_png is not None:
        _pruefe_datei(a.beauty_png, "Ausgangsbild (beauty_png)", maengel)

    if not isinstance(a.prompt, str) or not a.prompt.strip():
        maengel.append(
            "Prompt ist leer. Die Tiefenkarte gibt die Kubatur vor, aber Material, "
            "Licht und Stimmung stehen nur im Prompt."
        )
    if not isinstance(a.negativ_prompt, str):
        maengel.append(f"negativ_prompt ist kein Text: {a.negativ_prompt!r}")

    # --- Zahlen ----------------------------------------------------------------------
    if isinstance(a.seed, bool) or not isinstance(a.seed, int):
        maengel.append(f"seed ist keine ganze Zahl: {a.seed!r}")
    elif not (0 <= a.seed <= MAX_SEED):
        maengel.append(
            f"seed {a.seed} liegt ausserhalb von 0..{MAX_SEED}. Ein Seed ausserhalb "
            f"dieses Bereichs wird von den Zufallsgeneratoren unterschiedlich gedeutet "
            f"— derselbe Auftrag ergäbe dann je nach Rechner ein anderes Bild."
        )

    if isinstance(a.schritte, bool) or not isinstance(a.schritte, int):
        maengel.append(f"schritte ist keine ganze Zahl: {a.schritte!r}")
    elif a.schritte <= 0:
        maengel.append(
            f"schritte muss positiv sein, war {a.schritte}. Null Schritte ergeben kein "
            f"Bild, sondern Rauschen — und würden trotzdem als Render protokolliert."
        )
    elif a.schritte > MAX_SCHRITTE:
        maengel.append(
            f"schritte {a.schritte} übersteigt die Grenze {MAX_SCHRITTE}. Das ist fast "
            f"immer ein Tippfehler und blockiert die einzige GPU des Projekts."
        )

    _pruefe_anteil(a.controlnet_staerke, "controlnet_staerke", maengel)
    _pruefe_anteil(a.denoise, "denoise", maengel)

    # --- Ausgabeort ------------------------------------------------------------------
    if a.ausgabe_png is not None:
        if not isinstance(a.ausgabe_png, str) or not a.ausgabe_png.strip():
            maengel.append(f"ausgabe_png ist kein Pfad: {a.ausgabe_png!r}")
        else:
            elternteil = Path(a.ausgabe_png).parent
            if not elternteil.is_dir():
                # Vor dem Lauf feststellbar, nach dem Lauf teuer: Ein Bild, das nach
                # zwei Minuten Rechenzeit nirgends hin geschrieben werden kann, ist ein
                # verlorener Lauf.
                maengel.append(
                    f"Ausgabeverzeichnis {str(elternteil)!r} existiert nicht — das Bild "
                    f"könnte nach dem Lauf nicht abgelegt werden."
                )

    return maengel


# --------------------------------------------------------------------------------------
# Die Naht zum Modell
# --------------------------------------------------------------------------------------

#: Was die Bildmodell-Stufe zum Rechnen importiert. :func:`umgebung_da` fragt genau diese.
RENDER_PAKETE = ("torch", "diffusers")


def umgebung_da(*, finde=None) -> dict:
    """Kann **dieser** Python die Bildmodell-Stufe rechnen? — ohne etwas zu importieren.

    Der Befund, aus dem das entstand (`auf-20260924-164`, B4): Die HomeStation startete den
    Abholer mit dem System-Python. Die Probe meldete den Auftrag «frei», und erst beim
    Rendern kam «torch/diffusers nicht verfügbar» — der Auftrag endete mit Fehler. Der
    Dienst läuft mit einer eigenen Render-Umgebung; ein Aufruf von Hand mit dem falschen
    Python fällt erst auf, wenn es zu spät ist.

    Gefragt wird mit ``importlib.util.find_spec``: Es sagt, ob ein Paket **gefunden**
    würde, ohne es zu laden. ``torch`` zu importieren kostete Sekunden und Speicher — für
    eine Probe, die nur wissen will, ob es da ist, der falsche Preis.

    Returns:
        ``{"da": bool, "fehlend": tuple[str, ...], "satz": str}``
    """
    import importlib.util

    finde = finde or importlib.util.find_spec
    fehlend = []
    for name in RENDER_PAKETE:
        try:
            gefunden = finde(name) is not None
        except (ImportError, ValueError):
            gefunden = False
        if not gefunden:
            fehlend.append(name)
    if not fehlend:
        return {"da": True, "fehlend": (), "satz": "da (" + ", ".join(RENDER_PAKETE) + ")"}
    return {"da": False, "fehlend": tuple(fehlend),
            "satz": (f"FEHLT — {', '.join(fehlend)} mit diesem Python nicht auffindbar. "
                     f"Ein Auftrag würde angenommen und scheiterte erst beim Rendern. Den "
                     f"Abholer mit der Render-Umgebung starten (der, mit der der Dienst "
                     f"läuft).")}


def lade_modell(backbone_name: str, modell_wurzel=None, *, schrittzaehler=None):
    """Ein Bildmodell laden — die einzige Stelle, die ``torch`` und ``diffusers`` kennt.

    Args:
        backbone_name: Name aus der Registry.
        modell_wurzel: Verzeichnis der Gewichte. ``None`` heisst
            :func:`standard_modell_wurzel`.

    Returns:
        Ein **Aufrufbares** ``modell(parameter: dict) -> str | dict``. Der Rückgabewert
        ist der Pfad des geschriebenen PNG (oder ein Wörterbuch mit ``bild_png``).

        Der Vertrag der Naht ist absichtlich so schmal: ein Wörterbuch hinein, ein Pfad
        heraus. Alles, was Tensoren, Bildobjekte oder CUDA-Geräte kennt, bleibt hinter
        dieser Funktion. Deshalb kommt :func:`rendere` ohne ``torch`` aus — und deshalb
        genügt im Test eine Funktion von drei Zeilen als Modell.

    Raises:
        RenderError: Backbone unbekannt, unter Regel 1 ausgeschlossen, falsche
            Konditionierungsart, Gewichte unvollständig, oder ``torch``/``diffusers``
            nicht vorhanden.

    Die Prüfreihenfolge ist bindend: **Lizenz zuerst.** Ein ausgeschlossenes Modell soll
    nicht daran scheitern, dass seine Gewichte fehlen — es soll an Regel 1 scheitern,
    auch dann, wenn jemand die 24 GB bereits heruntergeladen hat.

    Warum der Import hier drin steht
    --------------------------------
    ``import torch`` auf Modulebene machte ``import aiimaging.render`` auf jedem Rechner
    ohne GPU-Stack unmöglich — und damit auch die Parameterprüfung, die Backbone-Wahl
    und jeden Test darüber. Der Import gehört in die Funktion, die das Modell wirklich
    lädt. ``tests/test_render.py`` hält das fest.
    """
    eintrag = _hole_oder_wirf(backbone_name)

    lizenz = backbone.pruefe_lizenz(eintrag.name)
    if not lizenz["zulaessig"]:
        raise RenderError(
            f"Backbone {eintrag.name!r} wird nicht geladen: {lizenz['begruendung']}"
        )
    if eintrag.konditionierung not in KONDITIONIERUNGEN:
        raise RenderError(
            f"Backbone {eintrag.name!r} nennt eine unbekannte Konditionierungsart "
            f"{eintrag.konditionierung!r}. Bekannt: {', '.join(KONDITIONIERUNGEN)}."
        )

    wurzel = Path(modell_wurzel) if modell_wurzel is not None else standard_modell_wurzel(eintrag.name)
    bestand = backbone.vorhandene_dateien(eintrag.name, wurzel)
    if not bestand["vollstaendig"]:
        raise RenderError(
            f"Gewichte für {eintrag.name!r} unvollständig unter {bestand['wurzel']!r} "
            f"(Verzeichnis existiert: {bestand['wurzel_existiert']}). Es fehlen: "
            f"{', '.join(bestand['fehlend'])}."
            + _einzeldatei_hinweis(eintrag, wurzel)
        )

    try:
        # NUR HIER. Siehe Docstring — und tests/test_render.py, das prüft, dass diese
        # beiden Namen nach 'import aiimaging.render' nicht in sys.modules liegen.
        import torch
        from diffusers import DiffusionPipeline
    except ImportError as fehler:
        raise RenderError(
            f"torch/diffusers nicht verfügbar ({fehler}). Die Bildmodell-Stufe läuft nur "
            f"dort, wo der GPU-Stack installiert ist — im Entwicklungscontainer gibt es "
            f"ihn nicht. Für Tests und Trockenläufe 'modell=' oder '_lader=' übergeben."
        ) from fehler

    if eintrag.konditionierung == KOND_DEPTH_CONTROLNET and eintrag.controlnet_id:
        pipeline, weg = _lade_mit_controlnet(eintrag, wurzel, torch)
    else:
        pipeline = DiffusionPipeline.from_pretrained(str(wurzel), torch_dtype=torch.bfloat16)
        weg = None

    erwartet = _erwarteter_bedarf(eintrag)
    geraet, entflechtung, bedarf = _lege_auf_geraet(
        pipeline, wurzel, torch, erwartet=erwartet,
        erwartet_gemessen=_bedarf_ist_gemessen(eintrag))

    modell = _pipeline_adapter(pipeline, eintrag, torch, schrittzaehler=schrittzaehler)
    modell.geraet = geraet
    modell.entflechtung = entflechtung
    modell.bedarf = bedarf
    if weg:
        modell.ladeweg = weg
    return modell


def _lade_mit_controlnet(eintrag, wurzel, torch):
    """Basis **plus** ControlNet — der Ladeweg, ohne den es keine Konditionierung gibt.

    **Der Befund, aus dem das entstand (Demolauf 2, 19.08.2026):** Bis hierher rief
    :func:`lade_modell` schlicht ``DiffusionPipeline.from_pretrained`` und bekam für
    ``z-image-turbo`` eine blanke ``ZImagePipeline`` — reines Text-zu-Bild, **ohne
    Steuereingang**. Der Adapter reichte die Tiefenkarte darum als ``image`` durch, und
    auch das kennt sie nicht: ``TypeError: got an unexpected keyword argument 'image'``.

    Bitter daran ist nicht der Fehler, sondern was er über die Messungen sagt: Jede Zahl
    dieses Projekts zu ``z-image-turbo`` — `auf-13`, `auf-21`, `auf-22` — entstand über
    eine **von Hand** gebaute ``ZImageControlNetPipeline`` in einem Messskript. Der Weg,
    den die Anwendung geht, hat diese Pipeline nie bekommen. Die Messungen bleiben
    gültig; sie haben einen Pfad gemessen, den niemand ausser dem Messenden benutzt.

    **Warum ``from_single_file``:** Das ControlNet-Repo liefert **kein**
    diffusers-Verzeichnis; ``from_pretrained`` bricht dort mit *«Error no file named
    config.json»* ab (`auf-20260818-13`). Die Einzeldatei ist nicht der bequemere, sondern
    der einzige Weg.
    """
    # Die Prüfungen stehen VOR dem Import: Ein fehlender Ordner ist kein Grund,
    # erst 20 GB Bibliothekscode zu laden — und so bleiben sie ohne GPU-Stack prüfbar,
    # dieselbe Trennung wie in `lade_modell` selbst.
    #
    # Zuerst die Familie (Befund 22.09.2026, `auf-20260922-138`): Bis dahin standen hier
    # die Z-Image-Klassen fest, für jeden Eintrag. Jetzt folgen sie aus
    # `eintrag.controlnet_familie`, und eine Familie ohne bekannte Klassen wird
    # abgewiesen — eine fremde Klasse zu nehmen, hiesse ein Modell mit dem Bauplan eines
    # anderen zu laden, und der Fehler käme erst nach dem Herunterladen der Gewichte.
    klassen = CONTROLNET_KLASSEN.get(eintrag.controlnet_familie)
    if klassen is None:
        raise RenderError(
            f"Backbone {eintrag.name!r} nennt ein ControlNet ({eintrag.controlnet_id!r}), "
            f"aber für seine Familie {eintrag.controlnet_familie!r} ist keine "
            f"Pipeline-Klasse bekannt. Bekannt: {', '.join(sorted(CONTROLNET_KLASSEN))}. "
            f"Mit der Klasse einer anderen Familie wird nicht geladen — das Modell hätte "
            f"den falschen Bauplan."
        )
    modell_klasse, pipeline_klasse = klassen

    if not eintrag.controlnet_ordner:
        raise RenderError(
            f"Backbone {eintrag.name!r} nennt ein ControlNet ({eintrag.controlnet_id!r}), "
            f"aber keinen Ordner, in dem seine Gewichte liegen. Ohne 'controlnet_ordner' "
            f"lässt sich der Ort nicht erraten — die Repo-Kennung ist kein Pfad."
        )
    ordner = Path(wurzel).parent / eintrag.controlnet_ordner
    dateien = sorted(ordner.glob("*.safetensors")) if ordner.is_dir() else []
    if not dateien:
        raise RenderError(
            f"ControlNet-Gewichte für {eintrag.name!r} nicht gefunden: {str(ordner)!r} "
            f"(Verzeichnis existiert: {ordner.is_dir()}). Erwartet wird dort eine "
            f"'.safetensors'-Datei. Ohne sie gibt es keine Konditionierung, und ein Lauf "
            f"ohne sie wäre genau die erfundene Kubatur, gegen die dieses Projekt antritt."
        )

    import diffusers

    fehlend = [k for k in (modell_klasse, pipeline_klasse) if not hasattr(diffusers, k)]
    if fehlend:
        raise RenderError(
            f"Die installierte diffusers-Fassung kennt {', '.join(fehlend)} nicht — für "
            f"{eintrag.name!r} (Familie {eintrag.controlnet_familie!r}) gibt es damit "
            f"keinen ControlNet-Ladeweg."
        )
    ControlNetModell = getattr(diffusers, modell_klasse)
    ControlNetPipeline = getattr(diffusers, pipeline_klasse)

    controlnet = ControlNetModell.from_single_file(str(dateien[0]),
                                                  torch_dtype=torch.bfloat16)
    pipeline = ControlNetPipeline.from_pretrained(str(wurzel), controlnet=controlnet,
                                                  torch_dtype=torch.bfloat16)
    return pipeline, f"{pipeline_klasse} + from_single_file({dateien[0].name})"


#: Familie -> (ControlNet-Modellklasse, Pipeline-Klasse) in ``diffusers``. Der Schlüssel
#: ist ``Backbone.controlnet_familie``. Namen statt Klassen, weil ``diffusers`` erst im
#: Ladeweg importiert wird — siehe :func:`lade_modell`.
#:
#: **Stand der Belege, 22.09.2026:**
#:
#: * ``"z-image"`` — AM GERÄT GEMESSEN: Diese beiden Klassen sind der Weg, über den
#:   alle Z-Image-Messungen liefen (`auf-20260818-13`, `auf-20260909-92`).
#: * ``"qwen-image"`` — **AM GERÄT UNBESTÄTIGT.** Die Namen sind die Qwen-Image-
#:   ControlNet-Klassen von ``diffusers``, wie sie hier ohne installierte Bibliothek
#:   angenommen werden. Nicht geprüft ist, (a) ob die Fassung auf der HomeStation sie
#:   führt, (b) ob ``from_single_file`` für diese Modellklasse geht und (c) ob das
#:   ControlNet ``alibaba-pai/Qwen-Image-2512-Fun-Controlnet-Union`` überhaupt in diese
#:   Klasse passt. Belegt ist allein, dass es nicht mehr die Z-Image-Klasse ist.
CONTROLNET_KLASSEN: dict[str, tuple[str, str]] = {
    "z-image": ("ZImageControlNetModel", "ZImageControlNetPipeline"),
    "qwen-image": ("QwenImageControlNetModel", "QwenImageControlNetPipeline"),
}


#: Vielfaches der **Plattengrösse**, das frei sein muss, damit das ganze Modell auf der
#: Karte bleiben darf. Gemessen auf der HomeStation (`auf-20260818-09`):
#: Qwen-Image-Edit-2511 in bfloat16 belegt 29,57 GiB auf einer Karte mit 31,36 GiB
#: nutzbar — voll geladen, und dann scheitert die Bilderzeugung an einer Anforderung von
#: **18 MiB**. Die Gewichte passen also, die Aktivierungen nicht mehr. Der Zuschlag deckt
#: genau diese Differenz ab: von den Gewichten zum Laufzeitbedarf.
GERAETE_ZUSCHLAG = 1.25

#: Vielfaches einer **gemessenen Spitze**, das frei sein muss. Deutlich kleiner, und das
#: ist der ganze Punkt.
#:
#: **Anlass, und er ist gemessen** (`auf-20260919-123`, HomeStation, 21.09.2026): Der
#: Vorgabe-Backbone lief auf der Werkstattmaschine **überhaupt nicht mehr**. Frei waren
#: 30 717 MiB, gemessen gebraucht hatte derselbe Lauf 25 671 MiB — er passte mit über
#: 5 GiB Luft. Verlangt wurden trotzdem 32 128 MiB, also wurde ausgelagert, und der
#: Auslagerungsweg starb an einem Gerätekonflikt.
#:
#: **Der Fehler war nicht die Zahl, sondern der Zuschlag darauf.** ``GERAETE_ZUSCHLAG``
#: führt von der *Gewichtsgrösse* zum *Laufzeitbedarf* — er bezahlt die Aktivierungen.
#: ``vram_gb`` aus der Registry ist aber bereits eine **Spitze im Betrieb**, Aktivierungen
#: eingeschlossen. Beides zu multiplizieren zählt dieselbe Sache zweimal.
#:
#: **Warum trotzdem nicht 1,0:** Dieselbe Spitze schwankt mit den Bedingungen. Für
#: ``z-image-turbo`` liegen drei Messungen vor — 22,89 / 23,4 / 25,1 GiB —, das sind
#: **9,7 %** zwischen der kleinsten und der grössten. Die Registry trägt bereits die
#: grösste; dieser Zuschlag deckt eine weitere Bedingungsänderung derselben Grösse ab.
#:
#: **Was er NICHT abdeckt, und das steht hier, damit es niemand für abgedeckt hält:**
#: Alle drei Messungen sind bei 512 x 512 entstanden. Ein deutlich grösseres Bild
#: braucht mehr Aktivierungen, und um wie viel mehr, ist nicht gemessen. Der Spielraum
#: einer Entscheidung steht darum in jedem Ergebnis (`geraeteweg.bedarf`).
#:
#: **Und er gilt NUR für eine gemessene Zahl** (berichtigt am 21.09.2026, wenige Stunden
#: nach dem Einbau). Der erste Wurf hat ihn auf jedes ``vram_gb`` der Registry angewandt —
#: dort stehen aber **fünf von sieben** Einträgen als *Schätzung* aus der Parameterzahl.
#: Eine Schätzung ist keine Spitze, und die ganze Begründung dieses Zuschlags
#: («Aktivierungen sind schon drin») trägt für sie nicht.
#:
#: *Ein Zuschlag, der mit einer Messung begründet ist, darf nicht auf eine Schätzung
#: angewandt werden — sonst ist die Begründung eine Erzählung über die eigenen Daten.*
#:
#: Wo ``vram_gemessen`` nicht ``True`` ist, gilt darum weiter ``GERAETE_ZUSCHLAG``. Das ist
#: der Zustand von vor dem 21.09.2026, und die sichere Richtung: Eine unbelegte Zahl
#: bekommt mehr Luft, nicht weniger.
MESSUNG_ZUSCHLAG = 1.10


def _gewichte_byte(wurzel) -> tuple[int, int]:
    """Wie gross die Gewichte auf der Platte sind — insgesamt und als grösster Einzelteil.

    Der zweite Wert ist der entscheidende: Komponentenweises Auslagern hilft nur, solange
    die **grösste einzelne** Komponente noch auf die Karte passt. Bei
    ``Qwen-Image-Edit-2511`` ist der Transformer allein 38 GiB — mehr als eine
    32-GiB-Karte hat. Die Summe hätte das nicht verraten.

    Returns:
        ``(summe, groesster_teil)`` in Byte; ``(0, 0)``, wenn sich nichts lesen lässt.
    """
    try:
        wurzel = Path(wurzel)
        summe = 0
        groesster = 0
        for teil in wurzel.iterdir():
            if teil.name.startswith("."):
                continue
            gross = (sum(p.stat().st_size for p in teil.rglob("*") if p.is_file())
                     if teil.is_dir() else teil.stat().st_size)
            summe += gross
            groesster = max(groesster, gross)
        return summe, groesster
    except OSError:
        return 0, 0


def _geteilte_parameter(a, b) -> set:
    """Parameterobjekte, die **beiden** Modulen gehören — erkannt an ihrer Identität.

    Nicht am Wert und nicht am Namen: Zwei Module können denselben Tensor tragen, ohne
    dass die Namen es verraten, und zwei gleich aussehende Tensoren sind noch keine
    geteilten. ``id()`` beantwortet genau die gestellte Frage.
    """
    ids_b = {id(t) for t in b.parameters()}
    return {id(t) for t in a.parameters()} & ids_b


def _entflechte_controlnet(pipeline) -> dict:
    """Dem ControlNet **eigene** Kopien der Untermodule geben, die es mit dem Transformer teilt.

    **Der Befund ist gemessen** (HomeStation, `auf-vis-20260825-14`, 25.08.2026):
    ``ZImageControlNetPipeline`` teilt **67 Parameter** zwischen ControlNet und
    Transformer — darunter den **ersten**. ``accelerate`` prüft beim Auslagern nur, wo der
    erste Parameter eines Moduls liegt; sobald das ControlNet umgezogen ist, gilt der
    Transformer damit als erledigt, und **454 von 521** seiner Parameter bleiben auf der
    CPU. Der erste Diffusionsschritt stirbt dann an
    ``Expected all tensors to be on the same device``.

    **Es ist kein Rückfall im Code.** Beide Fassungen sind seit dem 18.08.2026
    unberührt; ausgelöst hat es der **freie** Kartenspeicher. Voll auf der Karte läuft
    derselbe Auftrag in 26 Sekunden durch.

    .. important::
       **Nur vor dem Auslagern rufen, nie auf dem vollen Weg.** Die Kopien kosten rund
       1,35 GiB. Auf einer Karte, auf der 29,25 GiB verlangt und 28,89 frei waren, wäre
       das genau die Sorte Zuschlag, die einen gesunden Lauf erst in den Auslagerungsweg
       drängt — die Reparatur würde den Schaden anrichten, gegen den sie gebaut ist.

    Kopiert werden die **direkten Kinder** des ControlNets, die geteilte Parameter
    führen. Nicht das ganze ControlNet: Das wäre dieselbe Wirkung zum vielfachen Preis.

    Returns:
        ``{noetig, kopiert, vorher, nachher, grund}``. ``nachher > 0`` heisst, dass die
        Entflechtung **nicht** durchgriff — dann steht es da, statt dass ein Lauf später
        an einer Stelle stirbt, an der niemand mehr nach der Ursache sucht.
    """
    import copy

    controlnet = getattr(pipeline, "controlnet", None)
    transformer = getattr(pipeline, "transformer", None)
    if controlnet is None or transformer is None:
        return {"noetig": False, "kopiert": (), "vorher": None, "nachher": None,
                "grund": ("Diese Pipeline führt kein ControlNet neben einem Transformer "
                          "— die Verflechtung kann hier nicht auftreten.")}

    try:
        vorher = len(_geteilte_parameter(controlnet, transformer))
    except Exception as fehler:                    # noqa: BLE001 — siehe unten
        return {"noetig": None, "kopiert": (), "vorher": None, "nachher": None,
                "grund": (f"Die geteilten Parameter liessen sich nicht zaehlen "
                          f"({type(fehler).__name__}: {fehler}). UNBEKANNT — nicht "
                          f"'keine'.")}

    if not vorher:
        return {"noetig": False, "kopiert": (), "vorher": 0, "nachher": 0,
                "grund": "ControlNet und Transformer teilen keinen Parameter."}

    kopiert = []
    try:
        for name, kind in list(controlnet.named_children()):
            if _geteilte_parameter(kind, transformer):
                setattr(controlnet, name, copy.deepcopy(kind))
                kopiert.append(name)
        nachher = len(_geteilte_parameter(controlnet, transformer))
    except Exception as fehler:                    # noqa: BLE001
        # Bewusst breit und bewusst ohne Abbruch: Ohne diese Reparatur stirbt der Lauf
        # auf dem Auslagerungsweg ohnehin. Ein Fehlschlag HIER darf ihn nicht zusaetzlich
        # um die Meldung bringen, an der die Ursache erkennbar ist.
        return {"noetig": True, "kopiert": tuple(kopiert), "vorher": vorher,
                "nachher": None,
                "grund": (f"Die Entflechtung ist gescheitert ({type(fehler).__name__}: "
                          f"{fehler}). Der Lauf geht weiter und wird auf dem "
                          f"Auslagerungsweg voraussichtlich an einem Geraetekonflikt "
                          f"sterben — die Ursache steht damit wenigstens hier.")}

    if nachher:
        grund = (f"NICHT DURCHGEGRIFFEN: {nachher} von {vorher} Parametern sind weiter "
                 f"geteilt, obwohl {len(kopiert)} Untermodule kopiert wurden. Das "
                 f"Auslagern wird voraussichtlich scheitern.")
    else:
        grund = (f"{vorher} geteilte Parameter aufgeloest, indem {len(kopiert)} "
                 f"Untermodule kopiert wurden ({', '.join(kopiert)}). Kosten rund "
                 f"1,35 GiB (gemessen, auf-vis-20260825-14).")
    return {"noetig": True, "kopiert": tuple(kopiert), "vorher": vorher,
            "nachher": nachher, "grund": grund}


def _bedarf_ist_gemessen(eintrag) -> bool:
    """Steht in ``vram_gb`` dieses Eintrags eine **Messung** oder eine Schätzung?

    Alles, was nicht ausdrücklich ``True`` sagt, gilt als Schätzung — auch ein fehlendes
    Feld und auch ein fremdes Objekt ohne dieses Feld. *Die sichere Richtung: Eine Zahl,
    von der niemand weiss, woher sie kommt, ist keine Messung.*
    """
    return getattr(eintrag, "vram_gemessen", False) is True


def _erwarteter_bedarf(eintrag) -> tuple[int, int] | None:
    """Der Bedarf aus der **Registry**, oder ``None``, wenn dort keine Messung steht.

    Die Registry trägt für manche Backbones eine GEMESSENE Spitze; die Platte trägt eine
    irreführende Zahl (s. :func:`_lege_auf_geraet`). Die grösste Einzelkomponente wird als
    Hälfte der Summe angesetzt — grob, aber auf der sicheren Seite: sie ist nie grösser,
    und ein zu grosser Wert wählt höchstens den langsameren Weg.

    **Eigene Funktion seit dem 21.09.2026**, und zwar damit eine Probe sie rufen kann.
    Solange die Rechnung mitten in :func:`lade_modell` stand, liess sich die eine Frage,
    an der `auf-20260919-123` hing — *wählt der Vorgabe-Backbone auf dieser Karte den
    vollen Weg?* — nur beantworten, indem man sie in der Probe nachbaute. *Eine Probe, die
    die geprüfte Rechnung nachbaut, prüft ihre eigene Kopie.*
    """
    if not getattr(eintrag, "vram_gb", None):
        return None
    summe = int(eintrag.vram_gb * 2**30)
    return summe, summe // 2


#: Woher die Zahl stammt, mit der über den Ladeweg entschieden wurde. Vier Werte, weil es
#: vier Lagen gibt — und die letzte ist nicht «null», sondern **unbekannt**.
#:
#: Die Registry liefert **zwei** davon: eine Messung am Gerät oder eine Schätzung aus der
#: Parameterzahl. Sie stehen im selben Feld und sind nicht dasselbe; welches von beidem,
#: sagt ``Backbone.vram_gemessen``.
QUELLE_MESSUNG = "gemessene Spitze (Registry)"
QUELLE_SCHAETZUNG = "Schaetzung aus der Parameterzahl (Registry)"
QUELLE_PLATTE = "Groesse der Gewichtsdateien auf der Platte"
QUELLE_KEINE = "nicht bestimmbar"


def _bedarfsbericht(*, quelle, summe, groesster, zuschlag, frei, grund="") -> dict:
    """Mit welcher Zahl und mit wie viel Spielraum der Ladeweg entschieden wurde.

    **Der Anlass ist ein Lauf, der drei Wochen lang falsch entschied, ohne es zu sagen**
    (`auf-20260919-123`): Frei 30 717 MiB, wirklich gebraucht 25 671 MiB, verlangt
    32 128 MiB. Aus dem Ergebnis war keine dieser drei Zahlen zu lesen — nur der gewählte
    Weg, und der sah aus wie eine Eigenschaft der Maschine statt wie eine Rechnung.

    *Eine Entscheidung, deren Eingangszahlen nirgends stehen, ist von aussen nicht von
    einer Eigenschaft der Maschine zu unterscheiden.*

    ``spielraum_byte`` ist ``frei - verlangt``. **Negativ heisst ausgelagert**, und je
    näher an null, desto knapper war es — genau die Zahl, an der sich später ablesen
    lässt, ob ein Zuschlag getroffen hat oder bloss Glück hatte.

    Returns:
        ``{quelle, summe_byte, groesster_byte, zuschlag, verlangt_byte, frei_byte,
        spielraum_byte, grund}``. Jedes Feld darf ``None`` sein und heisst dann
        **unbekannt** — nie null.
    """
    verlangt = int(summe * zuschlag) if (summe and zuschlag) else None
    spielraum = (frei - verlangt) if (verlangt is not None and frei is not None) else None
    if not grund:
        grund = (f"Entschieden an {quelle}: {summe / 2**20:.0f} MiB x {zuschlag} = "
                 f"{verlangt / 2**20:.0f} MiB verlangt, {frei / 2**20:.0f} MiB frei."
                 if verlangt is not None and frei is not None else "")
    return {"quelle": quelle, "summe_byte": summe, "groesster_byte": groesster,
            "zuschlag": zuschlag, "verlangt_byte": verlangt, "frei_byte": frei,
            "spielraum_byte": spielraum, "grund": grund}


def _lege_auf_geraet(pipeline, wurzel, torch, *, erwartet=None,
                     erwartet_gemessen=None) -> tuple[str, dict | None, dict]:
    """Modell auf die Karte legen — ganz, komponentenweise, schichtweise, oder gar nicht.

    ``erwartet`` ist ``(summe_byte, groesster_byte)`` und **schlägt die Plattengrösse**.

    **Warum es das gibt (Demolauf 2, 19.08.2026):** Die Plattengrösse ist keine
    Speichergrösse. ``z-image-turbo`` liegt mit einem **fp32**-Transformer auf der Platte —
    23 GB — und wiegt in bfloat16 11,46 GiB. Wer die Datei misst, kommt auf 38,6 GiB,
    entscheidet sich gegen die Karte und lagert aus, obwohl 23,4 GiB bequem hineinpassen.
    Genau das ist passiert, und die Auslagerung scheiterte danach an einem Geräte-
    konflikt. Eine gemessene Zahl aus der Registry ist hier richtiger als jede Datei.

    Entschieden wird an dem, was die Karte **jetzt** frei hat, nicht an ihrem Namen und
    nicht an einer Fassungsnummer: ``torch.cuda.mem_get_info`` fragt den Treiber. Dieselbe
    Karte kann je nach dem, was sonst darauf liegt (ein Sprachmodell etwa), verschiedene
    Antworten verdienen. Ein Schwellenwert nach Kartenmodell wäre schon falsch, sobald
    jemand daneben ein zweites Modell lädt.

    Die drei Stufen kosten aufsteigend Zeit und retten aufsteigend mehr:

    ============================  =====================================================
    ``cuda``                      alles resident — schnellster Weg
    ``cuda+auslagerung``          je eine Komponente resident (``model_cpu_offload``)
    ``cuda+schichtauslagerung``   je ein Untermodul resident (``sequential_cpu_offload``)
    ============================  =====================================================

    Belegt auf der HomeStation (`auf-20260818-09`): Auf der RTX 5090 (31,4 GiB nutzbar)
    scheitert Stufe 1 an einer Anforderung von 18 MiB bei 29,57 GiB belegt, und Stufe 2
    scheitert ebenfalls — weil der Transformer mit 38 GiB grösser ist als die Karte.
    Erst Stufe 3 trägt. Wer nur die Summe prüft, wählt Stufe 2 und scheitert erneut.

    **Der Zuschlag hängt daran, WOHER die Zahl kommt** (Befund `auf-20260919-123`): Eine
    Plattengrösse ist noch kein Laufzeitbedarf und bekommt ``GERAETE_ZUSCHLAG``; eine
    gemessene Spitze *ist* der Laufzeitbedarf und bekommt nur ``MESSUNG_ZUSCHLAG``. Wer
    beide gleich behandelt, zählt die Aktivierungen zweimal — und schickt einen Lauf, der
    mit 5 GiB Luft auf die Karte passt, auf den Auslagerungsweg.

    ``erwartet_gemessen`` sagt, ob ``erwartet`` aus einer Messung stammt. **Nur ``True``
    bekommt den kleinen Zuschlag**; ``False`` und ``None`` (unbekannt) bekommen den
    grossen. Eine Registry-Zahl kann auch eine Schätzung aus der Parameterzahl sein, und
    auf die trifft die Begründung des kleinen Zuschlags nicht zu.

    Returns:
        **Drei** Werte, nicht zwei — die Annotation behauptete bis zum 21.09.2026 zwei.
        Gemeldet von der HomeStation (`auf-20260921-131`), die diese Naht fuer eine Probe
        ersetzt hat und an ``ValueError: too many values to unpack (expected 2, got 3)``
        scheiterte. *Wer eine Naht fuer eine Probe ersetzt — und genau dafuer ist sie
        gebaut —, liest die Annotation und baut danach.* Ausgerechnet der dritte Wert ist
        der interessanteste: Er traegt Quelle, Zuschlag und Spielraum.

        ``(weg, entflechtung, bedarf)``. ``entflechtung`` ist ``None`` auf den beiden
        Wegen, die **nicht** auslagern — dort wird :func:`_entflechte_controlnet` bewusst
        nicht gerufen, weil seine 1,35 GiB einen gesunden Lauf erst in die Auslagerung
        drängen könnten. ``None`` heisst hier also *nicht nötig gewesen*, und der Grund
        steht in dieser Zeile. ``bedarf`` sagt, mit welcher Zahl und mit wie viel
        Spielraum entschieden wurde — siehe :func:`_bedarfsbericht`.
    """
    if not torch.cuda.is_available():
        pipeline.to("cpu")
        return "cpu", None, _bedarfsbericht(
            quelle=QUELLE_KEINE, summe=None, groesster=None, zuschlag=None, frei=None,
            grund="Keine CUDA-Karte sichtbar — es gab nichts zu entscheiden.")

    frei, _gesamt = torch.cuda.mem_get_info()
    if erwartet is None:
        summe, groesster = _gewichte_byte(wurzel)
        quelle, zuschlag = QUELLE_PLATTE, GERAETE_ZUSCHLAG
    elif erwartet_gemessen is True:
        summe, groesster = erwartet
        quelle, zuschlag = QUELLE_MESSUNG, MESSUNG_ZUSCHLAG
    else:
        summe, groesster = erwartet
        quelle, zuschlag = QUELLE_SCHAETZUNG, GERAETE_ZUSCHLAG
    platte_groesster = None
    if erwartet is not None and erwartet_gemessen is not True:
        # DER GROESSTE BROCKEN NIE KLEINER ALS AUF DER PLATTE (Befund `auf-20260923-160`
        # C3, HomeStation, 24.09.2026). Die Schaetzung setzt ihn als Haelfte der Summe an
        # — bei `qwen-image-edit-2511` 24 GiB, auf der Platte ist der Transformer aber
        # 40,9 GB. Mit 30,6 GiB frei waehlte das Stufe 2, die den ganzen Transformer auf
        # die Karte legen muss: CUDA out of memory, auf dem Abholer-Weg bei JEDER
        # KosmoOrbit-Bestellung ohne Modellangabe. Lief nur, wenn zufaellig ein
        # Sprachmodell daneben lag und Stufe 3 erzwang. Eine Plattengroesse kann zu gross
        # sein (fp32 auf der Platte), nie zu klein — und ein zu grosser Wert waehlt
        # hoechstens den langsameren Weg. Eine GEMESSENE Spitze bleibt davon unberuehrt.
        _summe_platte, platte_groesster = _gewichte_byte(wurzel)
        groesster = max(groesster or 0, platte_groesster) or groesster

    if not summe:                                  # nichts messbar: wie bisher verfahren
        pipeline.to("cuda")
        return "cuda", None, _bedarfsbericht(
            quelle=QUELLE_KEINE, summe=None, groesster=None, zuschlag=None, frei=frei,
            grund=("Der Bedarf liess sich nicht bestimmen. Dann wird der volle Weg "
                   "gewaehlt — UNBEKANNT ist kein Grund zum Auslagern, und der volle Weg "
                   "meldet sein Scheitern wenigstens sofort."))

    bericht = _bedarfsbericht(quelle=quelle, summe=summe, groesster=groesster,
                              zuschlag=zuschlag, frei=frei)
    if platte_groesster and platte_groesster >= groesster and erwartet is not None \
            and platte_groesster > erwartet[1]:
        bericht["grund"] += (f" Groesster Einzelteil nach der Platte: "
                             f"{platte_groesster / 2**20:.0f} MiB (die Schaetzung sagte "
                             f"{erwartet[1] / 2**20:.0f} MiB).")

    if frei >= summe * zuschlag:
        pipeline.to("cuda")
        return "cuda", None, bericht

    # Ab hier wird ausgelagert — und erst ab hier ist die Verflechtung toedlich. Siehe
    # `_entflechte_controlnet`: Sie kostet Speicher, und Speicher ist genau das, woran
    # dieser Weg schon haengt.
    entflechtung = _entflechte_controlnet(pipeline)

    if frei >= groesster * zuschlag:
        # diffusers holt jede Komponente einzeln auf die Karte und legt sie danach zurück.
        pipeline.enable_model_cpu_offload()
        return "cuda+auslagerung", entflechtung, bericht

    # Selbst die grösste Komponente passt nicht am Stück. Dann wandern die Untermodule
    # einzeln — deutlich langsamer, aber der Lauf kommt durch. Ein Abbruch kostet ihn ganz.
    pipeline.enable_sequential_cpu_offload()
    return "cuda+schichtauslagerung", entflechtung, bericht


#: Orte, an denen eine Einzeldatei-Ablage vermutet wird, wenn das diffusers-Verzeichnis
#: fehlt. Die ComfyUI-Pfade stehen hier, weil ComfyUI im Ökosystem die verbreitetste
#: Ablage ist — nicht, weil dieses Projekt es benutzt (es ist GPL, siehe Lagebeurteilung).
EINZELDATEI_SUCHORTE = (
    "/ai", "/mnt/data/ComfyUI/models/diffusion_models",
    "/mnt/data/ComfyUI/models/checkpoints", "/mnt/data/ComfyUI/models/unet",
)

#: Endungen, die eine Einzeldatei-Ablage von Gewichten tragen kann.
EINZELDATEI_ENDUNGEN = (".safetensors", ".ckpt", ".gguf", ".sft")


def finde_einzeldatei_gewichte(eintrag, wurzel, *, suchorte=None) -> list[str]:
    """Liegen die Gewichte vielleicht als **Einzeldatei** statt als diffusers-Verzeichnis?

    Der Befund, aus dem das entstand (HomeStation, `auf-20260818-07`): Die Gewichte für
    Qwen-Image-Edit **waren** auf der Maschine — als
    `qwen_image_edit_2511_fp8mixed.safetensors`, eine ComfyUI-Einzeldatei. Der Adapter
    meldete „Gewichte unvollständig … es fehlen model_index.json, transformer, vae,
    text_encoder, tokenizer" und liess damit den Eindruck entstehen, es sei nichts da.

    Das ist derselbe Unterschied wie bei :func:`aiimaging.herkunft.pruefe_einheit_gegen_masse`:
    Ein **Verdacht** („da fehlt etwas") kostet jedes Mal einen Menschen, der nachsieht;
    eine **Diagnose** („es ist da, aber im falschen Format, und zwar hier") sagt ihm, wo.

    Gesucht wird nach Namensbestandteilen des Backbones. Die Suche ist bewusst flach und
    auf wenige Orte begrenzt: Sie soll einen Hinweis geben, nicht die Platte durchkämmen.

    Args:
        suchorte: Naht für Tests. ``None`` nimmt :data:`EINZELDATEI_SUCHORTE`.

    Returns:
        Gefundene Pfade als Text, höchstens fünf. Leer heisst: nichts gefunden — was
        **nicht** heisst, dass nichts da ist.
    """
    teile = [t for t in re.split(r"[-_]", eintrag.name.lower()) if len(t) > 2]
    orte = [Path(o) for o in (suchorte if suchorte is not None else EINZELDATEI_SUCHORTE)]
    orte.append(Path(wurzel).parent)

    treffer: list[str] = []
    gesehen: set[str] = set()
    for ort in orte:
        try:
            if not ort.is_dir():
                continue
            for datei in sorted(ort.iterdir()):
                if not datei.is_file() or datei.suffix.lower() not in EINZELDATEI_ENDUNGEN:
                    continue
                klein = datei.name.lower()
                # Alle Namensteile müssen vorkommen — sonst meldete "qwen" auch jedes
                # andere Qwen-Modell, und ein falscher Hinweis ist schlechter als keiner.
                if all(t in klein for t in teile) and str(datei) not in gesehen:
                    gesehen.add(str(datei))
                    treffer.append(str(datei))
                    if len(treffer) >= 5:
                        return treffer
        except OSError:
            continue                                   # unlesbarer Ort ist kein Fehler
    return treffer


def _einzeldatei_hinweis(eintrag, wurzel) -> str:
    """Der Satz, der aus „fehlt" ein „liegt hier, aber falsch" macht. Leer, wenn nichts da."""
    treffer = finde_einzeldatei_gewichte(eintrag, wurzel)
    if not treffer:
        return ""
    return (
        "\n\nABER: Es liegen Gewichte mit passendem Namen als EINZELDATEI vor:\n  "
        + "\n  ".join(treffer)
        + "\n\nDas ist kein Pfadproblem, sondern ein FORMATPROBLEM. Diese Naht ruft "
          "`DiffusionPipeline.from_pretrained` und braucht das diffusers-Verzeichnis "
          "(model_index.json plus je einen Unterordner für transformer, vae, "
          "text_encoder, tokenizer). Eine ComfyUI-Einzeldatei bringt dieselben Gewichte "
          "mit, aber ohne die Konfigurationsdateien, aus denen diffusers die Pipeline "
          "zusammensetzt. `modell_wurzel` umzustellen hilft darum nicht.\n"
          "Wege: das diffusers-Repo des Modells laden, oder die Einzeldatei umwandeln — "
          "beides ist ein Owner-Entscheid und passiert nicht stillschweigend hier."
    )


def _hole_oder_wirf(backbone_name: str):
    """Registry-Eintrag holen; ``BackboneError`` wird zu ``RenderError``.

    Warum die Umwandlung: Wer ``render`` benutzt, soll ``RenderError`` fangen müssen und
    nicht zusätzlich die Ausnahmeklasse eines Nachbarmoduls kennen. Die ursprüngliche
    Meldung (mit der Liste der bekannten Namen) bleibt vollständig erhalten.
    """
    try:
        return backbone.hole(backbone_name)
    except backbone.BackboneError as fehler:
        raise RenderError(str(fehler)) from fehler


def _generator_geraet(pipeline, torch) -> str:
    """Auf welchem Gerät der Zufallsgenerator sitzt.

    Nicht ``pipeline.device``: Bei schichtweiser Auslagerung liegt kein Modulteil mehr
    fest auf der Karte, und diffusers meldet dann ``meta`` — ein Platzhalter ohne
    Speicher. ``torch.Generator(device="meta")`` bricht mit *„META device type not an
    accelerator"* ab, und zwar erst beim Aufruf, nicht beim Laden (belegt auf der
    HomeStation, `auf-20260818-09`).

    Der Seed muss aber genau dann tragen, wenn ausgelagert wird — sonst ist die
    Wiederholvorschrift ausgerechnet auf der kleinen Karte keine mehr. Darum wird ein
    **echtes** Gerät gewählt, und ``cpu`` ist dabei der verlässliche Boden: Ein
    CPU-Generator funktioniert in jeder Auslagerungsstufe und liefert überall dieselbe
    Folge.
    """
    geraet = getattr(pipeline, "device", None)
    art = getattr(geraet, "type", None)
    if art in (None, "meta"):
        return "cuda" if torch.cuda.is_available() else "cpu"
    return str(geraet)


def _als_diffusers_rueckruf(schrittzaehler):
    """Unseren einfachen Zähler in die Gestalt bringen, die ``diffusers`` erwartet.

    Deren ``callback_on_step_end`` wird als ``(pipe, schritt, zeit, wörterbuch)`` gerufen
    und **muss** ein Wörterbuch zurückgeben — gibt es ``None`` zurück, bricht der Lauf
    mitten im Sampling ab. Unser Zähler soll davon nichts wissen müssen; er bekommt nur
    die Schrittnummer.

    Der Zähler wird **abgeschirmt**: Wirft er, wird das geschluckt. Ein Fortschrittszähler,
    der einen laufenden Render abbricht, kostet mehr, als er je einbringt — und der
    Abbruch käme dazu als Fehler des Renderers daher, nicht als seiner.
    """
    def rueckruf(pipe, schritt, zeit, kwargs):
        try:
            schrittzaehler(int(schritt) + 1)
        except Exception:      # noqa: BLE001 — siehe Docstring
            pass
        return kwargs

    return rueckruf


def _vertraegliche_argumente(pipeline, argumente: dict) -> tuple[dict, list[str]]:
    """Nur übergeben, was die Pipeline auch entgegennimmt.

    Gelesen wird die Signatur von ``pipeline.__call__`` — also das, was die geladene
    Pipeline **kann**, nicht das, was ihr Name vermuten lässt. Nimmt sie ``**kwargs``
    entgegen, lässt sich nichts ausschliessen, und es geht alles durch.

    Warum überhaupt filtern statt einfach zu übergeben: Ein ``TypeError`` mitten im Lauf
    kostet den ganzen Auftrag, und die Meldung nennt immer nur das **erste** unbekannte
    Argument. Wer drei falsche Argumente hat, erfährt das in drei Läufen.

    Returns:
        ``(genommen, verworfen)`` — die übergebbaren Argumente und die Namen der
        weggelassenen, sortiert.
    """
    import inspect

    try:
        parameter = inspect.signature(pipeline.__call__).parameters
    except (TypeError, ValueError):
        # Eine Pipeline ohne lesbare Signatur ist kein Grund, den Lauf abzubrechen —
        # dann gilt wieder „alles durchreichen", wie vor dieser Weiche.
        return dict(argumente), []

    if any(p.kind is inspect.Parameter.VAR_KEYWORD for p in parameter.values()):
        return dict(argumente), []

    genommen = {k: v for k, v in argumente.items() if k in parameter}
    return genommen, sorted(set(argumente) - set(genommen))


def ist_controlnet_naht(pipeline, genommene_argumente) -> bool:
    """Trägt diese Pipeline ein ControlNet — auch wenn sie kein ``control_image`` kennt?

    Warum diese Frage nicht am Namen entschieden wird
    -------------------------------------------------
    Die ControlNet-Familien nennen ihren Steuereingang verschieden.
    ``QwenImageControlNetPipeline``, ``StableDiffusion3ControlNetPipeline`` und
    ``ZImageControlNetPipeline`` nehmen ``control_image``;
    **``StableDiffusionXLControlNetPipeline`` nennt ihn schlicht ``image``** und kennt
    ``control_image`` überhaupt nicht (dort heisst so das Ausgangsbild der
    Img2Img-Variante — dieselbe Zeichenkette, die andere Bedeutung).

    Ohne diese Unterscheidung meldete der Adapter für SDXL, die Konditionierung sei
    „Bildbearbeitung, nicht ControlNet". Das ist der **spiegelbildliche Fehler** zu
    `auf-20260818-09`: dort wurde eine fehlende Naht für vorhanden gehalten, hier würde
    eine tragende für kaputt erklärt. Beide kosten dasselbe — einen Menschen, der
    nachsieht, und beim zweiten Mal sieht er nicht mehr nach.

    Entschieden wird an zwei ablesbaren Merkmalen, keinem geratenen: Wer
    ``controlnet_conditioning_scale`` annimmt, hat eine ControlNet-Stärke zu regeln; wer
    ein ``controlnet``-Attribut trägt, hat ein ControlNet geladen. Der Modellname und
    die Fassungsnummer bleiben aussen vor — beide haben sich in diesem Projekt schon
    einmal als unzuverlässig erwiesen.

    Args:
        pipeline: Die ``diffusers``-Pipeline.
        genommene_argumente: Die Argumente, die sie tatsächlich annimmt
            (aus :func:`_vertraegliche_argumente`).
    """
    if "controlnet_conditioning_scale" in genommene_argumente:
        return True
    return getattr(pipeline, "controlnet", None) is not None


def _tiefe_als_rgb(bild):
    """Tiefenkarte nach RGB — **skaliert, nicht geklippt**.

    **DER FEHLER, DEN DAS BEHEBT (20.08.2026), und er erklärt ein halbes Dutzend
    Messungen rückwirkend.** Unser Multipass schreibt ``tiefe_norm.png`` als 16-Bit-PNG
    (PIL-Modus ``I;16``). Bis hierher stand an dieser Stelle schlicht
    ``Image.open(pfad).convert("RGB")`` — und PIL **klippt** dabei bei 255, statt den
    Wertebereich zu skalieren. Am Gerät gemessen, an unserer eigenen Karte::

        roh (I;16)              235 verschiedene Werte, sauberer Tiefenverlauf
        nach convert("RGB")       2 verschiedene Werte — 40 % schwarz, 60 % weiss

    **Das ControlNet hat nie eine Tiefenkarte gesehen. Es hat eine Schwarzweiss-Schablone
    gesehen.** Damit ist erklärt, was `auf-20260820-22` gemessen und nicht verstanden hat:
    *«die Naht transportiert die Silhouette und nicht die Tiefenordnung»* — eine Silhouette
    war buchstäblich alles, was ankam. Und warum |ρ| dort über **alle** Varianten flach
    bei 0.45–0.49 lag, auch mit abgeschalteter Konditionierung: Eine Schablone trägt keine
    Ordnung, die sich übertragen liesse.

    **Der Beleg, dass es die Ursache war** (gleiche Szene, gleicher Prompt, n = 3 Seeds,
    ρ über der Bauwerksmaske — je negativer, desto besser)::

        16 Bit, geklippt      Mittel -0.1393   stdabw 0.1004
        8 Bit, skaliert       Mittel -0.7445   stdabw 0.1635
        perfektes Blenderbild        -0.9874
        weisses Rauschen             -0.5207

    Der Unterschied ist das 3,7-Fache der grösseren Streuung, und **jeder** skalierte Lauf
    schlägt **jeden** geklippten. Der beste erreicht −0.9059 und liegt damit nahe am
    perfekten Bild.

    *Warum es so lange unentdeckt blieb:* Die Schablone trägt die **Silhouette** exakt —
    und ``geom_iou`` misst genau die. Die eine Zahl, die wir hatten, war blind für den
    Verlust; sie lag bei 0.95, während die Tiefe verschwunden war.
    """
    from PIL import Image                     # Pillow (MIT-CMU) — nur hier
    # `getattr` statt `bild.mode`: Die Tests dieses Moduls reichen eine Bild-Attrappe
    # herein, die nur `convert` kann. Sie soll den Weg unten nehmen, nicht hier abstuerzen
    # — die Naht ist fuer Attrappen gebaut, und das gilt auch fuer diese Abzweigung.
    if getattr(bild, "mode", "") in ("I;16", "I;16B", "I;16L", "I", "I;32"):
        # NumPy — verzögert und nur für diesen Fall. **Die Lizenzangabe „BSD-3"
        # stand hier bis zum 26.08.2026 allein, und das ist genau der Fehler, den
        # die eigene Binärprüfung dieses Projekts benannt hat:** Das numpy-Wheel
        # liefert `libquadmath` (LGPL-2.1-or-later) statisch mit, ohne es in seiner
        # Kurzangabe zu nennen (`docs/LIZENZPRUEFUNG_BINAER_2026-08-18.md`).
        # Dies ist die **einzige** Stelle, an der numpy den Produktprozess erreicht
        # — und damit die einzige, an der eine LGPL-Komponente diesseits der
        # Prozessgrenze landet. Der Zustand ist im `NOTICE` benannt und liegt als
        # Frage beim Owner; hier wird er nicht stillschweigend geändert.
        import numpy as np
        werte = np.asarray(bild, dtype=np.float64)
        spanne = float(werte.max())
        # Skaliert wird auf den TATSÄCHLICHEN Höchstwert, nicht auf 65535: Die Karte ist
        # bereits je Bild normiert, und eine zweite Normierung auf die formale Obergrenze
        # verschenkte Kontrast, sobald der Höchstwert darunter liegt.
        acht = (werte / spanne * 255.0).round().clip(0, 255).astype(np.uint8) if spanne \
            else np.zeros_like(werte, dtype=np.uint8)
        return Image.fromarray(acht, mode="L").convert("RGB")
    return bild.convert("RGB")


def _pipeline_adapter(pipeline, eintrag, torch, *, schrittzaehler=None):
    """Aus einer ``diffusers``-Pipeline ein Modell im Sinne dieses Moduls machen.

    **Ungeprüft.** Diese Funktion ist die einzige Stelle des Moduls, die hier nie
    ausgeführt werden kann: Es gibt weder ``torch`` noch Gewichte. Sie ist bewusst so
    kurz wie möglich gehalten, damit die ungeprüfte Fläche klein bleibt — alles
    Entscheidbare (Lizenz, Konditionierung, Parameter, Ergebnisaufbau) liegt ausserhalb
    und ist geprüft.

    Die genaue Verdrahtung des ControlNet unterscheidet sich je Backbone-Familie
    (Qwen, SDXL, SD3.5 nehmen die Tiefenkarte an verschiedenen Argumenten entgegen).
    Welche Argumente eine Pipeline annimmt, wird darum **an ihr selbst abgelesen**
    (:func:`_vertraegliche_argumente`) und nicht aus ihrem Namen oder ihrer Fassung
    geschlossen. Eine Pipeline ohne ``control_image`` bekommt die Tiefenkarte als
    ``image``; was sie gar nicht kennt, wird nicht übergeben, sondern **gemeldet**.

    ``schrittzaehler`` wird als ``callback_on_step_end`` an die Pipeline gereicht — der
    einzige **belegte Fortschritt**, den dieses Projekt hat: Er zählt Diffusionsschritte,
    die wirklich gerechnet wurden, statt zu bezeugen, dass ein Prozess noch lebt.
    Kennt eine Pipeline das Argument nicht, wird es wie jedes andere **gemeldet und nicht
    stillschweigend verschluckt** — ein Rückruf, der nie gerufen wird, sähe von aussen
    genauso aus wie ein hängender Lauf.

    Belegt auf der HomeStation (`auf-20260818-09`, 18.08.2026): ``Qwen-Image-Edit-2511``
    ist über ``QwenImageEditPlusPipeline`` **kein ControlNet**. Ihr ``__call__`` kennt
    weder ``control_image`` noch ``controlnet_conditioning_scale`` noch ``strength``.
    Die frühere Fassung reichte alle drei durch und scheiterte an einem ``TypeError``;
    hätte diffusers sie bloss verschluckt, wären ``controlnet_staerke`` und ``denoise``
    stillschweigend wirkungslos gewesen — und eine Vergleichsreihe über die
    ControlNet-Stärke hätte dreimal dasselbe Bild ergeben und wie ein Befund ausgesehen.
    """
    def modell(parameter: dict) -> dict:
        from PIL import Image           # Pillow (MIT-CMU) — ebenfalls nur hier

        tiefe = _tiefe_als_rgb(Image.open(parameter["depth_png"]))
        if parameter["tiefe_invertiert"]:
            # Umgedreht, weil das ControlNet dieses Backbones nah = DUNKEL erwartet und
            # unsere Karte nah = hell schreibt. Kein Kunstgriff, sondern eine Übersetzung
            # zwischen zwei Konventionen — und sie steht im Parametersatz, damit ein
            # späterer Leser nicht rätselt, welche Karte das Modell gesehen hat.
            from PIL import ImageOps                # noqa: PLC0415 — nur hier gebraucht
            tiefe = ImageOps.invert(tiefe)
        generator = torch.Generator(device=_generator_geraet(pipeline, torch)).manual_seed(
            parameter["seed"]
        )

        argumente = {
            "prompt": parameter["prompt"],
            "negative_prompt": parameter["negativ_prompt"] or None,
            "control_image": tiefe,
            "controlnet_conditioning_scale": parameter["controlnet_staerke"],
            "num_inference_steps": parameter["schritte"],
            # Ohne Angabe greift die Vorgabe der jeweiligen Pipeline — bei diffusers
            # meist 5.0 oder 7.5. Für ein destilliertes Turbo-Modell ist das falsch: Es
            # ist darauf trainiert, OHNE Führung zu laufen, und ein Wert von 5.0 liefert
            # überzeichnete Bilder bei doppelter Rechenzeit. Der Wert gehört darum in den
            # Parametersatz und nicht in die Vorgabe einer fremden Bibliothek.
            "guidance_scale": parameter["fuehrung"],
            "generator": generator,
            # Das Bild muss die Tiefenkarte treffen, sonst ist es nicht bewertbar:
            # `geometrie_qa` vergleicht Soll und Ist **indexweise** und lehnt bei
            # ungleicher Länge ab — zu Recht, denn Zuschneiden wäre eine stille
            # Reparatur. Ohne Vorgabe wählt die Pipeline ihre Lieblingsgrösse; auf der
            # HomeStation kam aus einer 512er Tiefenkarte ein 1024er Bild, und die
            # Bewertung fiel nach 184 s aus (`auf-20260818-09`). Pipelines ohne
            # `height`/`width` verlieren die Angabe unten wieder.
            "height": tiefe.height,
            "width": tiefe.width,
        }
        gerechnet = [0]

        def zaehlen(schritt: int) -> None:
            gerechnet[0] = schritt
            if schrittzaehler is not None:
                schrittzaehler(schritt)

        argumente["callback_on_step_end"] = _als_diffusers_rueckruf(zaehlen)
        if parameter["modus"] == MODUS_IMAGE_EDIT:
            argumente["image"] = Image.open(parameter["beauty_png"]).convert("RGB")
            argumente["strength"] = parameter["denoise"]

        # DER REGLER, DER WIRKT (23.09.2026, `auf-20260923-157`): Bei
        # `QwenImageEditPlusPipeline` schaltet `true_cfg_scale` die Führung, und nur
        # zusammen mit einem Negativprompt, der nicht None ist. Bis hierher ging bei leerem
        # Negativprompt `None` hin — jeder solche Lauf rechnete ohne Führung. Nur wenn der
        # Eintrag Regler UND Wert führt, kommt etwas dazu; sonst bleibt `argumente`, wie
        # es war.
        regler = parameter.get("fuehrung_regler")
        regler_wert = parameter.get("fuehrung_regler_wert")
        karte = parameter.get("negativ_prompt_karte")
        if regler is not None and regler_wert is not None:
            argumente[regler] = regler_wert
            if karte is not None:
                argumente["negative_prompt"] = karte

        genommen, verworfen = _vertraegliche_argumente(pipeline, argumente)
        hinweise = []

        if regler is not None and regler in verworfen:
            # NICHTS DAVON, auch nicht der Leer-Negativprompt: Er ist nur dazu da, die
            # Führung über diesen Regler einzuschalten. An einer Pipeline, die den Regler
            # nicht kennt, wäre er ein Eingriff in eine Rechnung, die niemand gelesen hat.
            # Es geht dann hin, was vor dem 23.09.2026 hinging.
            if karte is not None and "negative_prompt" in genommen:
                genommen["negative_prompt"] = parameter["negativ_prompt"] or None
            hinweise.append(
                f"'{regler}' ({regler_wert}) kennt diese Pipeline nicht und wurde nicht "
                f"übergeben — und mit ihm auch nicht der Leer-Negativprompt der "
                f"Modellkarte ({karte!r}); als Negativprompt ging "
                f"{genommen.get('negative_prompt')!r} hin. Der Eintrag "
                f"'{eintrag.name}' erwartet diesen Regler "
                f"({getattr(eintrag, 'fuehrung_regler_beleg', None)}); die geladene "
                f"Pipeline ist offenbar nicht die belegte. Ob hier klassifikatorfreie "
                f"Führung läuft, ist UNBEKANNT — nicht nein."
            )

        if "control_image" in verworfen:
            # Ohne eigenen Steuereingang ist die Tiefenkarte das Bild selbst — sie ist
            # der Geometrieträger, und Geometrietreue ist der Zweck des Ganzen. Ein
            # Beauty-Pass, der hier vorlag, tritt dahinter zurück: Es gibt nur einen
            # Bildeingang, und die Geometrie hat ihn nötiger als die Farbe.
            #
            # ABER: Ein fehlendes `control_image` ist NICHT gleichbedeutend mit „kein
            # ControlNet". `StableDiffusionXLControlNetPipeline` nennt ihr Steuerbild
            # schlicht `image` und kennt `control_image` gar nicht — dort ist die
            # Tiefenkarte als `image` die richtige und einzige Übergabe. Die frühere
            # Fassung hätte für SDXL gemeldet, die Konditionierung sei „Bildbearbeitung,
            # nicht ControlNet": der spiegelbildliche Fehler zu `auf-20260818-09`, eine
            # tragende Naht als kaputt gemeldet. Ein Fehlalarm kostet dasselbe wie ein
            # übersehener Fehler — einen Menschen, der nachsieht.
            #
            # Unterschieden wird an der Pipeline selbst, nicht an ihrem Namen: Wer
            # `controlnet_conditioning_scale` annimmt oder ein `controlnet`-Attribut
            # trägt, hat ein ControlNet. Beides ist ablesbar, keines ist geraten.
            if ist_controlnet_naht(pipeline, genommen):
                hinweise.append(
                    "Diese Pipeline nimmt das Steuerbild als 'image' entgegen und kennt "
                    "kein 'control_image' (so hält es die SDXL-ControlNet-Familie). Die "
                    "Tiefenkarte wurde dorthin übergeben — die ControlNet-Naht trägt."
                )
            elif "image" in genommen:
                hinweise.append(
                    "Diese Pipeline hat keinen 'control_image'-Eingang und kein "
                    "erkennbares ControlNet. Die Tiefenkarte wurde als 'image' übergeben "
                    "und ersetzt dabei den Beauty-Pass — die Konditionierung ist damit "
                    "Bildbearbeitung, nicht ControlNet."
                )
            genommen["image"] = tiefe

        for name, wert in (("controlnet_conditioning_scale", parameter["controlnet_staerke"]),
                           ("guidance_scale", parameter["fuehrung"]),
                           ("strength", parameter["denoise"])):
            if name in verworfen:
                hinweise.append(
                    f"'{name}' ({wert}) kennt diese Pipeline nicht und wurde nicht "
                    f"übergeben. Der Wert ist wirkungslos — eine Vergleichsreihe darüber "
                    f"würde identische Bilder liefern."
                )

        if "callback_on_step_end" in verworfen:
            hinweise.append(
                "Diese Pipeline kennt 'callback_on_step_end' nicht. Der Schrittzähler "
                "wurde NICHT verdrahtet — es gibt für diesen Lauf also kein belegtes "
                "Fortschrittszeichen, sondern höchstens ein Lebenszeichen. Und die Zahl "
                "der wirklich gerechneten Schritte bleibt unbekannt: 'schritte_gerechnet' "
                "ist dann None und heisst UNGEMESSEN, nicht null."
            )

        uebrig = [n for n in verworfen
                  if n not in ("control_image", "controlnet_conditioning_scale",
                               "guidance_scale", "strength", "callback_on_step_end",
                               regler)]
        if uebrig:
            hinweise.append(f"Nicht übergeben, weil unbekannt: {', '.join(uebrig)}.")

        # ══ WAS WURDE WIRKLICH GERECHNET? ══════════════════════════════════════════
        #
        # Gemessen am 21.09.2026 (`auf-20260919-123`, HomeStation, sieben Laeufe): Auf
        # `z-image-turbo` kommt das Eingangsbild UEBERHAUPT NICHT an — die Pipeline kennt
        # weder `image` noch `strength`. Alle sieben Laeufe, mit Bild und ohne, mit
        # fuenf verschiedenen `denoise`-Werten, tragen **dieselbe sha256**.
        #
        # Das heisst: Jeder Lauf mit Beauty-Anker auf diesem Backbone lief in Wahrheit
        # als `txt2img`. Und weil `modus` aus dem BESTELLTEN Anker abgeleitet wird
        # (`image_edit if beauty_png else txt2img`), stand im Parametersatz die ganze
        # Zeit `image_edit`.
        #
        #     Ein Lauf, der anders gerechnet wird als bestellt, und dessen Parametersatz
        #     die Bestellung nennt, ist nicht reproduzierbar — er ist nachstellbar mit
        #     demselben falschen Ergebnis.
        #
        # ES WIRD DARUM NICHT ABGEBROCHEN, und das ist ein Entscheid: Das Bild ist ein
        # gueltiges txt2img-Bild, die Tiefenkarte hat ueber `control_image` getragen, und
        # ein Abbruch machte den Vorgabeweg dieses Projekts unbenutzbar. Was falsch war,
        # ist nicht der Lauf — es ist die AUSKUNFT ueber ihn.
        #
        # Der Ausgang ist darum ein eigenes Feld statt eines Hinweises unter fuenfzehn:
        # `modus_gerechnet` neben `modus_bestellt`. Ein Hinweis wird gelesen oder nicht;
        # ein Feld laesst sich vergleichen, ablegen und pruefen.
        modus_bestellt = parameter["modus"]
        modus_gerechnet = modus_bestellt
        if modus_bestellt == MODUS_IMAGE_EDIT:
            # `image` allein genuegt NICHT als Beleg: Faellt `control_image` weg, wird die
            # Tiefenkarte oben in `genommen["image"]` geschrieben und ueberschreibt den
            # Anker. Dann ist `image` belegt und der Anker trotzdem verloren — genau der
            # Fall, der am 18.08.2026 an Qwen-Image-Edit gemessen wurde.
            anker_kam_an = ("image" in genommen
                            and "image" not in verworfen
                            and "control_image" not in verworfen)
            if not anker_kam_an:
                modus_gerechnet = MODUS_TXT2IMG
                hinweise.append(
                    f"BESTELLT WAR '{MODUS_IMAGE_EDIT}', GERECHNET WURDE "
                    f"'{MODUS_TXT2IMG}': Das Ausgangsbild ist bei dieser Pipeline nicht "
                    f"angekommen. Das Bild ist gueltig, aber es ist NICHT das, was "
                    f"bestellt war — eine Vergleichsreihe ueber 'denoise' liefert hier "
                    f"bitgleiche Bilder."
                )

        bild = pipeline(**genommen).images[0]

        bestellt = parameter["schritte"]
        if "callback_on_step_end" not in verworfen and gerechnet[0] != bestellt:
            hinweise.append(
                f"Gerechnet wurden {gerechnet[0]} Diffusionsschritte, bestellt waren "
                f"{bestellt}. Das ist kein Fehler, sondern die Rechnung mancher Pipelines: "
                f"Im Bildbearbeitungsmodus laufen nur 'schritte x denoise' Schritte "
                f"(hier {bestellt} x {parameter['denoise']} = "
                f"{int(bestellt * parameter['denoise'])}). **Der Parametersatz nennt die "
                f"bestellte Zahl** — wer zwei Läufe über die Schrittzahl vergleicht, "
                f"vergleicht in Wahrheit diese hier."
            )

        ziel = parameter["ausgabe_png"] or str(
            Path(parameter["depth_png"]).with_name(f"render_{parameter['seed']}.png")
        )
        bild.save(ziel)
        return {"bild_png": ziel, "hinweise": hinweise,
                "schritte_gerechnet": gerechnet[0] or None,
                # KAM DER FUEHRUNGSREGLER AN? (Durchsicht Runde 12.) Der Parametersatz
                # nennt, was der Eintrag BESTELLT; ob die geladene Pipeline es nahm, weiss
                # nur diese Stelle. None: kein Regler bestellt.
                "fuehrung_regler_angekommen": (None if regler is None or regler_wert is None
                                               else regler in genommen),
                # ZWEI FELDER, NICHT EINES. Sie sind meistens gleich, und genau darum
                # faellt der Fall auf, in dem sie es nicht sind.
                "modus_bestellt": modus_bestellt,
                "modus_gerechnet": modus_gerechnet}

    modell.backbone = eintrag.name       # zur Fehlersuche: welches Modell steckt drin
    return modell


# --------------------------------------------------------------------------------------
# Der Lauf
# --------------------------------------------------------------------------------------

def _baue_parameter(a: RenderAuftrag, eintrag, *,
                    tiefe_invertieren: bool | None = None) -> dict:
    """Alles, was den Lauf bestimmt, in einem Wörterbuch — die Wiederholvorschrift.

    Warum vollständig und nicht nur „das Wichtigste": Die Schwellenstudie (Phase 4)
    vergleicht Läufe miteinander. Fehlt ein einziger Parameter im Protokoll, lässt sich
    ein Unterschied zwischen zwei Bildern nicht mehr einer Ursache zuordnen — und die
    Messung ist wertlos. Der Satz ist zugleich das, was die Naht an das Modell übergibt:
    Was nicht hier steht, kann das Modell nicht benutzt haben.
    """
    modus = MODUS_IMAGE_EDIT if a.beauty_png else MODUS_TXT2IMG
    wurzel = a.modell_wurzel if a.modell_wurzel is not None else str(
        standard_modell_wurzel(eintrag.name)
    )
    return {
        "backbone": eintrag.name,
        "modell_id": eintrag.modell_id,
        "konditionierung": eintrag.konditionierung,
        "modus": modus,
        "depth_png": a.depth_png,
        "beauty_png": a.beauty_png,
        "ausgabe_png": a.ausgabe_png,
        "prompt": a.prompt,
        "negativ_prompt": a.negativ_prompt,
        "seed": a.seed,
        "schritte": a.schritte,
        "controlnet_staerke": float(a.controlnet_staerke),
        "denoise": float(a.denoise),
        # Was das Modell erwartet, und ob wir darum drehen. Beides in den Parametersatz:
        # Die Tiefenkarte auf der Platte ist unverändert, das Modell sieht aber
        # womöglich ihr Negativ — ohne diesen Eintrag wäre ein Lauf nicht nachvollziehbar.
        "tiefen_polaritaet_modell": getattr(eintrag, "tiefen_polaritaet",
                                            backbone.POL_UNBEKANNT),
        #
        # DER MESSSCHALTER (23.09.2026) schlaegt das Register, und nur er. Ohne ihn ist die
        # Zeile die von vorher; mit ihm steht daneben, dass und womit ueberschrieben wurde
        # — `None` heisst: nicht ueberschrieben, das Register galt.
        "tiefe_invertiert": (bool(tiefe_invertieren) if tiefe_invertieren is not None
                             else getattr(eintrag, "tiefen_polaritaet",
                                          backbone.POL_UNBEKANNT)
                             == backbone.POL_NAH_DUNKEL),
        "tiefe_invertiert_ueberschrieben": tiefe_invertieren,
        # Auftrag schlägt Registry schlägt fremde Vorgabe. `None` bleibt `None` und wird
        # unten als solches gemeldet — ein eingesetzter Ersatzwert wäre eine Erfindung.
        "fuehrung": (float(a.fuehrung) if a.fuehrung is not None
                     else (float(eintrag.fuehrung) if getattr(eintrag, "fuehrung", None)
                           is not None else None)),
        # DER REGLER, DER WIRKT (23.09.2026, `auf-20260923-157`): Bei
        # `qwen-image-edit-2511` ist das `true_cfg_scale`, nicht `guidance_scale`. Name und
        # Wert stehen am Eintrag; `None` heisst nicht bestimmt, und dann geht NICHTS
        # zusätzlich an die Pipeline — die Argumente aller übrigen Einträge bleiben die
        # von vorher (tests/test_runde12_fuehrung.py, Schnappschuss).
        "fuehrung_regler": getattr(eintrag, "fuehrung_regler", None),
        "fuehrung_regler_wert": (float(eintrag.fuehrung_regler_wert)
                                 if getattr(eintrag, "fuehrung_regler_wert", None)
                                 is not None else None),
        # Der Leer-Negativprompt der Modellkarte, wie er BESTELLT ist: nur bei leerem
        # eigenem Negativprompt und nur, wenn der Eintrag ihn führt. Ob er ankam, sagt
        # `fuehrung_regler_angekommen` (Durchsicht Runde 12: vorher behauptete dieser
        # Kommentar «wenn er hingeht», auch an einer Pipeline, die ihn verwarf). `None` heisst
        # — wie bei `tiefe_invertiert_ueberschrieben` — nicht ersetzt; dann geht der
        # eigene Negativprompt unverändert hin. `negativ_prompt` oben bleibt die
        # Bestellung und wird nicht umgeschrieben.
        "negativ_prompt_karte": (getattr(eintrag, "leer_negativ_prompt", None)
                                 if not a.negativ_prompt
                                 and getattr(eintrag, "fuehrung_regler", None) is not None
                                 else None),
        # Ob Regler (und Leerprompt) bei der geladenen Pipeline ANKAMEN — erst nach dem
        # Lauf bekannt, von `rendere` aus der Antwort des Adapters eingetragen. `None`
        # heisst: kein Regler bestellt, oder die Naht meldet es nicht (Attrappe, fremdes
        # Modell) — nicht «nein».
        "fuehrung_regler_angekommen": None,
        "modell_wurzel": str(wurzel),
    }


#: Unterhalb dieser Führung ist die klassifikatorfreie Führung abgeschaltet — und damit
#: der negative Prompt wirkungslos. Keine Setzung dieses Projekts, sondern die Bauart des
#: Verfahrens: Ohne zweiten, ungeführten Durchlauf gibt es nichts, wovon sich der negative
#: Prompt abziehen liesse.
FUEHRUNG_MINDESTENS = 1.0


def negativ_wirksam(backbone_name: str, *, fuehrung: float | None = None) -> dict:
    """Kann ein negativer Prompt auf diesem Backbone **überhaupt** etwas bewirken?

    **Die Frage ist vor dem Rendern zu stellen und nicht danach.** Ein negativer Prompt,
    der unterhalb von :data:`FUEHRUNG_MINDESTENS` mitgeschickt wird, erscheint im
    Protokoll und ändert kein einziges Bildpunkt. Das ist die unangenehmste Sorte
    Wirkungslosigkeit: Sie sieht wie Sorgfalt aus.

    Und sie trifft **unseren Vorgabefall**: ``z-image-turbo`` ist ein destilliertes
    Turbo-Modell und läuft mit ``fuehrung = 0.0``.

    Args:
        fuehrung: Ausdrücklich gesetzte Führung; ``None`` heisst «die des Backbones».

    Returns:
        ``{wirksam, fuehrung, mindestens, backbone, grund}``. ``wirksam`` ist ``None``,
        wenn die Führung **unbestimmt** ist — dann greift die Vorgabe von ``diffusers``,
        eine fremde Entscheidung, und was sie ist, wissen wir hier nicht. Nicht ``False``:
        Das hiesse «wirkt nicht», und behauptet würde damit etwas Ungemessenes.

        **Geurteilt wird über den Regler, der wirkt** (Befund 23.09.2026,
        `auf-20260923-157`). Führt der Eintrag einen eigenen
        :attr:`~aiimaging.backbone.Backbone.fuehrung_regler` (bei
        ``qwen-image-edit-2511``: ``true_cfg_scale``), dann entscheidet dessen Wert gegen
        :data:`FUEHRUNG_MINDESTENS`, nicht ``fuehrung``/``guidance_scale`` — die dort
        nichts schaltet. ``fuehrung`` in der Antwort ist dann der Wert dieses Reglers; ein
        mitgegebenes ``fuehrung`` ändert das Urteil nicht und wird im Grund genannt.
    """
    eintrag = backbone.BACKBONES.get(backbone_name)
    regler = getattr(eintrag, "fuehrung_regler", None)
    regler_wert = getattr(eintrag, "fuehrung_regler_wert", None)
    if regler is not None and regler_wert is not None:
        return _negativ_wirksam_ueber_regler(eintrag, fuehrung)
    wert = fuehrung
    if wert is None and eintrag is not None:
        wert = getattr(eintrag, "fuehrung", None)

    antwort = {"wirksam": None, "fuehrung": wert, "mindestens": FUEHRUNG_MINDESTENS,
               "backbone": backbone_name, "grund": ""}
    if eintrag is None and fuehrung is None:
        antwort["grund"] = (
            f"Backbone {backbone_name!r} ist unbekannt, und es wurde keine Führung "
            f"mitgegeben. Ob ein negativer Prompt wirkt, ist damit UNBEKANNT — nicht nein.")
        return antwort
    if wert is None:
        antwort["grund"] = (
            f"Für {backbone_name!r} ist keine Führung bestimmt; es greift die Vorgabe von "
            f"diffusers. Ob ein negativer Prompt wirkt, hängt damit an einer fremden "
            f"Entscheidung und ist hier UNBEKANNT — nicht nein.")
        return antwort

    antwort["wirksam"] = wert > FUEHRUNG_MINDESTENS
    if antwort["wirksam"]:
        antwort["grund"] = (
            f"Führung {wert} liegt über {FUEHRUNG_MINDESTENS} — die klassifikatorfreie "
            f"Führung ist aktiv, ein negativer Prompt kann wirken.")
    else:
        antwort["grund"] = (
            f"Führung {wert} schaltet die klassifikatorfreie Führung ab. Ein negativer "
            f"Prompt bliebe WIRKUNGSLOS: Er stünde im Protokoll und nicht im Bild. Wer "
            f"ihn braucht, setzt die Führung über {FUEHRUNG_MINDESTENS}; wer das "
            f"Turbo-Modell braucht, verzichtet auf ihn.")
    return antwort


def _guidance_satz(eintrag, fuehrung) -> str:
    """Was ``fuehrung`` (``guidance_scale``) bei diesem Eintrag ausrichtet — ein Satz.

    Nur bei BELEGTER Wirkungslosigkeit (``guidance_scale_wirkungslos is True``) gibt es
    einen Satz; sonst ist das nicht bestimmt, und die Aufrufer sagen es mit ihren
    bisherigen Worten. Leer heisst: kein Beleg.
    """
    if getattr(eintrag, "guidance_scale_wirkungslos", None) is not True:
        return ""
    genannt = ("Es ist keine gesetzt" if fuehrung is None
               else f"fuehrung={fuehrung} geht zwar als guidance_scale hin")
    regler = getattr(eintrag, "fuehrung_regler", None)
    folge = (f"die Führung läuft über '{regler}'" if regler is not None
             else "der Wert richtet nichts aus")
    return (f"guidance_scale ist bei den Gewichten von '{eintrag.name}' belegt "
            f"WIRKUNGSLOS ({eintrag.guidance_scale_beleg}). {genannt} — das ist hier "
            f"keine fremde Entscheidung, sondern gleichgültig: {folge}.")


def _negativ_wirksam_ueber_regler(eintrag, fuehrung) -> dict:
    """:func:`negativ_wirksam` für einen Eintrag mit eigenem Führungsregler.

    Dieselbe Rückgabeform ``{wirksam, fuehrung, mindestens, backbone, grund}``. Die
    Schwelle ist dieselbe wie bei ``guidance_scale``: diffusers rechnet die Führung bei
    ``QwenImageEditPlusPipeline`` nur mit ``true_cfg_scale > 1`` (Z.719,
    `auf-20260923-157`) — und mit einem Negativprompt, der nicht None ist. Ein
    mitgegebener Negativprompt ist nie None; fehlt er, geht der Leer-Negativprompt der
    Modellkarte hin, sofern der Eintrag ihn führt.
    """
    regler, wert = eintrag.fuehrung_regler, float(eintrag.fuehrung_regler_wert)
    wirksam = wert > FUEHRUNG_MINDESTENS
    teile = [f"Auf '{eintrag.name}' schaltet '{regler}' die klassifikatorfreie Führung, "
             f"nicht guidance_scale ({eintrag.fuehrung_regler_beleg})."]
    if wirksam:
        teile.append(
            f"'{regler}' = {wert} liegt über {FUEHRUNG_MINDESTENS} — die Führung läuft, ein "
            f"negativer Prompt kann wirken.")
        if getattr(eintrag, "leer_negativ_prompt", None) is not None:
            teile.append(
                f"Ohne eigenen Negativprompt geht der Leer-Negativprompt der Modellkarte "
                f"({eintrag.leer_negativ_prompt!r}) hin, damit sie anspringt.")
    else:
        teile.append(
            f"'{regler}' = {wert} liegt nicht über {FUEHRUNG_MINDESTENS} — die Führung ist "
            f"abgeschaltet, ein negativer Prompt bliebe WIRKUNGSLOS.")
    if fuehrung is not None:
        satz = _guidance_satz(eintrag, fuehrung)
        teile.append(satz or f"Die mitgegebene fuehrung={fuehrung} (guidance_scale) "
                             f"entscheidet hier nicht darüber.")
    return {"wirksam": wirksam, "fuehrung": wert, "mindestens": FUEHRUNG_MINDESTENS,
            "backbone": eintrag.name, "grund": " ".join(teile)}


def _hinweise(a: RenderAuftrag, parameter: dict, lizenz: dict) -> tuple[str, ...]:
    """Was auffällt, ohne ein Mangel zu sein.

    Der Unterschied zu einem Mangel: Ein Hinweis hält den Lauf nicht auf. Er verhindert
    aber, dass etwas **stillschweigend** wirkungslos bleibt — ein gesetztes ``denoise``
    ohne Ausgangsbild wird nicht kommentarlos verworfen, sondern benannt.
    """
    hinweise: list[str] = []

    # Die letzte Stelle, an der ein deutscher Prompt noch auffallen kann.
    #
    # Übersetzt wird weiter vorne (`kosmo_szene.lies_szene`, `prompts.komponiere`) — hier
    # steht nur noch die Kontrolle. Sie ist trotzdem nötig: Ein `RenderAuftrag` lässt sich
    # von Hand bauen, aus einem Skript, aus einem Auftrag, und dann kommt der Text an
    # keiner Übersetzung vorbei. Eine Warnung im Ergebnis erreicht denjenigen, der das
    # Bild ansieht; ein Hinweis in einem Modul, das nicht aufgerufen wurde, erreicht
    # niemanden. Sie warnt nur beim entschiedenen Fall — siehe `sprache.sprachwarnung`.
    warnung = sprache.sprachwarnung(a.prompt if isinstance(a.prompt, str) else "")
    if warnung:
        hinweise.append(warnung)
    if isinstance(a.negativ_prompt, str) and a.negativ_prompt.strip() \
            and sprache.sprachwarnung(a.negativ_prompt):
        hinweise.append(
            "Auch der Negativ-Prompt sieht nicht englisch aus. Er wirkt damit "
            "doppelt wenig: schon der positive Teil wird auf Deutsch schlechter "
            "verstanden, und der negative wirkt ohnehin nur oberhalb einer Führung "
            "von 1.0."
        )

    if parameter["modus"] == MODUS_TXT2IMG and a.denoise != 0.0:
        hinweise.append(
            f"denoise={a.denoise} bleibt im Modus '{MODUS_TXT2IMG}' wirkungslos: Ohne "
            f"'beauty_png' gibt es kein Ausgangsbild, das überschrieben werden könnte."
        )
    if parameter.get("tiefe_invertiert_ueberschrieben") is not None:
        # MESSSCHALTER STATT REGISTER. Die beiden Saetze darunter sprechen vom Register
        # («am Geraet gemessen», «nicht gemessen») — sie stimmten hier nicht mehr.
        register = (parameter["tiefen_polaritaet_modell"] == backbone.POL_NAH_DUNKEL)
        hinweise.append(
            f"MESSSCHALTER tiefe_invertieren={parameter['tiefe_invertiert_ueberschrieben']}"
            f": Die Tiefenkarte wird für '{parameter['backbone']}' "
            f"{'UMGEDREHT' if parameter['tiefe_invertiert'] else 'NICHT umgedreht'} "
            f"übergeben — das Register "
            f"({parameter['tiefen_polaritaet_modell']}) hätte "
            f"{'gedreht' if register else 'nicht gedreht'}. Nur für Messungen; die "
            f"Datei auf der Platte bleibt unverändert.")
    elif parameter["tiefe_invertiert"]:
        hinweise.append(
            f"Die Tiefenkarte wird für '{parameter['backbone']}' UMGEDREHT übergeben: "
            f"Unsere Karte schreibt nah = hell, dieses ControlNet erwartet nah = dunkel "
            f"(am Gerät gemessen). Die Datei auf der Platte bleibt unverändert — das "
            f"Modell sieht ihr Negativ."
        )
    elif parameter["tiefen_polaritaet_modell"] == backbone.POL_UNBEKANNT:
        # NICHT drehen. Raten hiesse, mit halber Wahrscheinlichkeit die Geometrie zu
        # spiegeln, und zwar lautlos. Aber schweigen wäre schlimmer: Ein schlechter Score
        # hat hier womöglich eine harmlose Erklärung, und ohne diesen Satz sucht jemand
        # tagelang am Bildmodell.
        hinweise.append(
            f"Für '{parameter['backbone']}' ist nicht gemessen, welche Tiefenkonvention "
            f"sein ControlNet erwartet. Es wird NICHT gedreht — raten hiesse, mit halber "
            f"Wahrscheinlichkeit die Geometrie zu spiegeln. Falls der Geometrie-Score "
            f"schlecht ausfällt: Das kann allein daran liegen. Bei z-image-turbo hat die "
            f"Umkehrung |spearman| von 0.38–0.52 auf 0.79–0.85 gehoben."
        )

    # ÜBER DEN REGLER, DER WIRKT (Befund 23.09.2026, `auf-20260923-157`). Bei
    # `qwen-image-edit-2511` sprach der Satz darunter von guidance_scale und einer
    # «fremden Entscheidung» — über einen Regler, den diese Gewichte gar nicht lesen,
    # während die Führung über `true_cfg_scale` lief oder (ohne Negativprompt) gar nicht.
    eintrag = backbone.BACKBONES.get(parameter["backbone"])
    regler = parameter.get("fuehrung_regler")
    if regler is not None and parameter.get("fuehrung_regler_wert") is not None:
        wert = parameter["fuehrung_regler_wert"]
        beleg = getattr(eintrag, "fuehrung_regler_beleg", None)
        if parameter.get("negativ_prompt_karte") is not None:
            negativ = (
                f"Ohne eigenen Negativprompt ist der Leer-Negativprompt der Modellkarte "
                f"({parameter['negativ_prompt_karte']!r}) bestellt statt None — mit None "
                f"schaltet die Pipeline die Führung ab, und genau so liefen solche Läufe "
                f"bis zum 23.09.2026. Ob Regler und Leerprompt ankamen, steht im Feld "
                f"'fuehrung_regler_angekommen'.")
        elif a.negativ_prompt:
            negativ = (f"Der eigene Negativprompt ({a.negativ_prompt!r}) geht "
                       f"unverändert hin.")
        else:
            negativ = ("Ein Leer-Negativprompt ist für dieses Modell nicht bestimmt; es "
                       "geht None hin. Ob die Pipeline dann führt, ist UNBEKANNT.")
        if wert > FUEHRUNG_MINDESTENS:
            # Die zwei Durchgänge nur, wo ein Negativprompt hingeht — sonst ist unbekannt,
            # ob überhaupt geführt wird (Durchsicht Runde 12).
            doppelt = ("" if parameter.get("negativ_prompt_karte") is None
                       and not a.negativ_prompt else
                       " Die Führung rechnet zwei Transformer-Durchgänge je Schritt statt "
                       "einem; wie viel Rechenzeit das kostet, ist nicht gemessen.")
            hinweise.append(
                f"FÜHRUNG über '{regler}' = {wert} für '{parameter['backbone']}' "
                f"({beleg}). {negativ}{doppelt} Kennt die geladene Pipeline '{regler}' "
                f"nicht, geht beides nicht hin, und ein eigener Hinweis sagt das.")
        else:
            hinweise.append(
                f"'{regler}' = {wert} für '{parameter['backbone']}' liegt nicht über "
                f"{FUEHRUNG_MINDESTENS} — die klassifikatorfreie Führung ist abgeschaltet, "
                f"ein negativer Prompt bleibt WIRKUNGSLOS ({beleg}).")

    guidance = _guidance_satz(eintrag, parameter["fuehrung"])
    if guidance:
        hinweise.append(guidance)
    elif parameter["fuehrung"] is None:
        hinweise.append(
            f"Für '{parameter['backbone']}' ist keine Führung (guidance_scale) bestimmt. "
            f"Es greift die Vorgabe von diffusers — eine fremde Entscheidung, keine "
            f"eigene. Bei einem destillierten Turbo-Modell ist sie nachweislich falsch."
        )
    elif parameter["fuehrung"] <= 1.0 and a.negativ_prompt and regler is None:
        # Nur ohne eigenen Regler: Wo einer steht, urteilt der Satz oben (23.09.2026).
        # Der stille Fall: Der negative Prompt steht im Protokoll, im Bild wirkt er nicht.
        hinweise.append(
            f"fuehrung={parameter['fuehrung']} schaltet die klassifikatorfreie Führung "
            f"ab. Der negative Prompt ({a.negativ_prompt!r}) bleibt damit WIRKUNGSLOS — "
            f"er steht im Protokoll, aber nicht im Bild. Wer ihn braucht, setzt die "
            f"Führung über 1.0; wer das Turbo-Modell braucht, verzichtet auf ihn."
        )
    if a.ausgabe_png is None:
        hinweise.append(
            "Ohne 'ausgabe_png' bestimmt das Modell den Ablageort. Damit entfällt der "
            "Schutz gegen ein liegengebliebenes Bild aus einem früheren Lauf."
        )
    hinweise.extend(lizenz["auflagen"])
    return tuple(hinweise)


def _geraeteweg(modell) -> dict:
    """Auf welchem Weg das Modell wirklich gelaufen ist — für das Protokoll.

    **Der Anlass sind drei verlorene Stunden** (HomeStation, `auf-vis-20260825-15`,
    Posten 4): :func:`lade_modell` setzt ``modell.geraet`` und ``modell.ladeweg`` seit
    dem 19.08.2026 — und **kein Aufrufer hat sie je irgendwohin geschrieben**. Darum sah
    der Unterschied zwischen dem gelungenen Lauf vom 20.08. und dem Fehlschlag vom
    25.08. wie ein Rückfall im Code aus, obwohl sich am Code nichts geändert hatte: Es
    war der freie Kartenspeicher, der zwischen zwei Ladewegen entschied. Zwei bis vier
    Zehntel Gigabyte.

    Der billigste Posten der ganzen Liste, und der mit dem grössten Hebel: Eine Zahl, die
    gemessen wird und nirgends landet, ist für jede spätere Untersuchung nicht vorhanden.

    Returns:
        ``{geraet, ladeweg, entflechtung, bedarf, gemeldet, grund}``. ``gemeldet`` ist ``False``, wenn kein
        Modell geladen wurde **oder** das übergebene Modell die Angaben nicht führt — die
        Dreiteilung dieses Projekts: ``geraet=None`` heisst **unbekannt**, nie „CPU".
    """
    if modell is None:
        return {"geraet": None, "ladeweg": None, "entflechtung": None, "bedarf": None,
                "gemeldet": False,
                "grund": "Es wurde nichts geladen — der Auftrag kam nicht so weit."}
    geraet = getattr(modell, "geraet", None)
    if geraet is None:
        return {"geraet": None, "ladeweg": getattr(modell, "ladeweg", None),
                "entflechtung": getattr(modell, "entflechtung", None),
                "bedarf": getattr(modell, "bedarf", None),
                "gemeldet": False,
                "grund": ("Das Modell fuehrt keine Geraeteangabe. So sieht eine Attrappe "
                          "aus, und so saehe auch ein fremder Lader aus — UNBEKANNT ist "
                          "hier nicht dasselbe wie 'auf der CPU'.")}
    return {"geraet": str(geraet), "ladeweg": getattr(modell, "ladeweg", None),
            # Ob dem ControlNet vor dem Auslagern eigene Kopien gegeben wurden. `None`
            # auf den Wegen, die nicht auslagern — siehe `_lege_auf_geraet`.
            "entflechtung": getattr(modell, "entflechtung", None),
            # Mit welcher Zahl und mit wie viel Spielraum der Weg gewaehlt wurde. Ohne
            # dieses Feld sieht eine Rechnung von aussen aus wie eine Eigenschaft der
            # Maschine — genau der Irrtum von `auf-20260919-123`.
            "bedarf": getattr(modell, "bedarf", None),
            "gemeldet": True, "grund": ""}


def _ergebnis(status: str, parameter: dict, *, bild_png=None, dauer_s: float = 0.0,
              error=None, maengel=(), lizenz=None, hinweise=(),
              schritte_gerechnet=None, geraeteweg=None,
              modus_bestellt=None, modus_gerechnet=None) -> dict:
    """Der Ergebnissatz — eine Form für alle drei Ausgänge.

    Ein einheitlicher Satz ist kein Selbstzweck: Wer ein Ergebnis auswertet, soll
    ``ergebnis['seed']`` lesen können, ohne vorher den Status zu verzweigen. Auch eine
    Ablehnung trägt darum die vollständigen Parameter — gerade sie: Sonst steht im
    Protokoll „abgelehnt" ohne die Angabe, was abgelehnt wurde.
    """
    return {
        "status": status,
        "bild_png": bild_png,
        "seed": parameter["seed"],
        "backbone": parameter["backbone"],
        "parameter": parameter,
        "dauer_s": round(float(dauer_s), 3),
        "error": error,
        "maengel": tuple(maengel),
        "lizenz": lizenz,
        "hinweise": tuple(hinweise),
        # None heisst UNGEMESSEN und nicht null — dieselbe Dreiteilung wie überall in
        # diesem Projekt. Eine Pipeline ohne `callback_on_step_end` lässt uns darüber im
        # Dunkeln, und das ist etwas anderes, als hätte sie keinen Schritt gerechnet.
        "schritte_gerechnet": schritte_gerechnet,
        # Auf welchem Weg das Modell lief. Steht auch bei einer Ablehnung da — dann
        # eben mit `gemeldet: False` und dem Grund. Siehe `_geraeteweg`.
        "geraeteweg": geraeteweg if geraeteweg is not None else _geraeteweg(None),
        # WAS BESTELLT WAR UND WAS GERECHNET WURDE — und bis zum 21.09.2026 stand hier
        # NICHTS davon.
        #
        # Die beiden Felder wurden im Adapter gebaut, mit einem langen Kommentar
        # begruendet («ein Hinweis wird gelesen oder nicht; ein Feld laesst sich
        # vergleichen») — und dann in `rendere` nie aus der Antwort gelesen. Die
        # HomeStation hat es an drei Laeufen gemessen (`auf-20260921-134`): beide Felder
        # None, obwohl ein Ausgangsbild bestellt und von der Pipeline verworfen worden
        # war. Genau der Fall, fuer den sie gebaut sind.
        #
        # *Eine Auskunft, die eine Funktion frueher wegwirft als der Leser sie braucht,
        # gibt es fuer den Leser nicht.*
        #
        # `modus_bestellt` ist immer bekannt — es steht im Auftrag. `modus_gerechnet`
        # darf None sein: Dann hat die Naht nichts gemeldet, und das ist die dritte
        # Antwort und kein «war gleich».
        "modus_bestellt": modus_bestellt if modus_bestellt is not None
                          else parameter.get("modus"),
        "modus_gerechnet": modus_gerechnet,
        # Eine Zahl statt eines Satzes: Wer zwei Laeufe vergleicht, fragt dieses Feld ab
        # und liest keine Hinweisliste. None heisst auch hier NICHT GEMESSEN.
        "modus_abweichung": (None if modus_gerechnet is None
                             else bool(modus_gerechnet != (modus_bestellt
                                                           if modus_bestellt is not None
                                                           else parameter.get("modus")))),
    }



def _leere_grafikspeicher() -> None:
    """``torch.cuda.empty_cache()``, wenn es torch und eine Karte gibt — sonst nichts."""
    try:
        import torch  # noqa: PLC0415 — nur hier, und nur wenn schon ein Fehler da ist
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    except Exception:                                   # noqa: BLE001 — Aufräumen, kein Urteil
        pass

def rendere(a: RenderAuftrag, *, modell=None, _lader=None,
            schrittzaehler=None, tiefe_invertieren: bool | None = None) -> dict:
    """Einen Bildauftrag ausführen — oder begründet ablehnen.

    Args:
        a: Der Auftrag.
        modell: Ein fertiges Modell ``modell(parameter: dict) -> str | dict``. Übergeben
            heisst: nichts wird geladen. **Das ist die Test-Naht** — mit einer Attrappe
            läuft diese Funktion ohne GPU, ohne ``torch`` und ohne ein einziges Gewicht
            vollständig durch. Dieselbe Bauform wie ``_starte`` in ``seams.py``.
        _lader: Ersatz für :func:`lade_modell`, Signatur
            ``(backbone_name, modell_wurzel) -> modell``. Für Tests, die auch das Laden
            beobachten wollen. Unterstrich, weil es eine Naht ist und keine Einstellung.
        schrittzaehler: ``(schritt: int) -> None``, gerufen nach **jedem**
            Diffusionsschritt. **Das ist der einzige belegte Fortschritt, den dieses
            Projekt hat** — er zählt Schritte, die wirklich gerechnet wurden, nicht bloss
            das Weiterleben eines Prozesses (vergleiche den Herzschlag des Blender-Laufs,
            der ausdrücklich ein *Lebens*zeichen ist).
            Kennt die Pipeline ``callback_on_step_end`` nicht, steht das als Hinweis im
            Ergebnis; verdrahtet wird dann nichts. Ein Rückruf, der nie gerufen wird,
            sähe von aussen genauso aus wie ein hängender Lauf.
        tiefe_invertieren: **Messschalter, nur für Messungen** (23.09.2026). ``None``
            (Vorgabe): Das Register entscheidet (``tiefen_polaritaet`` des Backbones).
            ``True``/``False`` überschreiben es; ``parameter['tiefe_invertiert']`` ist
            dann dieser Wert, ``parameter['tiefe_invertiert_ueberschrieben']`` nennt ihn,
            und ein Hinweis sagt, was das Register getan hätte. Anderes als
            ``None``/``True``/``False`` wird **abgelehnt**, nicht gedeutet.
            **Bewusst kein Feld von** :class:`RenderAuftrag`: Dessen Felder sind die
            Bestellung und werden an der Naht des Abholers gezählt
            (``abholer.RENDER_DURCHGEREICHT``/``RENDER_STEHENGEBLIEBEN``); ein
            Messschalter gehört nicht in diese Zählung. Ins Protokoll kommt er trotzdem —
            über den Parametersatz.

    Returns:
        ``{status, bild_png, seed, backbone, parameter, dauer_s, error, maengel, lizenz,
        hinweise, schritte_gerechnet, geraeteweg}``.

        ``geraeteweg`` sagt, **auf welchem Weg** das Modell lief (``cuda``,
        ``cuda+auslagerung``, ``cuda+schichtauslagerung``, ``cpu``) — siehe
        :func:`_geraeteweg`. Die Angabe wurde seit dem 19.08.2026 gemessen und bis zum
        26.08. nirgends geschrieben.

        ``schritte_gerechnet`` ist die Zahl der **wirklich gerechneten**
        Diffusionsschritte, gezählt am Rückruf der Pipeline. Sie kann von
        ``parameter['schritte']`` abweichen — im Bildbearbeitungsmodus rechnen viele
        Pipelines nur ``schritte × denoise``. ``None`` heisst **ungemessen** (die Pipeline
        kennt keinen Rückruf), nicht null.

        * ``status='ok'`` — ``bild_png`` zeigt auf eine Datei, die es wirklich gibt.
        * ``status='abgelehnt'`` — der Auftrag verletzt den Vertrag (Lizenz,
          Konditionierung, Parameter, fehlende Eingabe). **Es wurde nichts geladen und
          nichts gerechnet.** ``maengel`` nennt alle Gründe.
        * ``status='fehler'`` — es wurde versucht, und es ging schief. ``error`` trägt
          die Meldung.

    Raises:
        RenderError: nur, wenn ``a`` gar kein :class:`RenderAuftrag` ist. Dann gibt es
            keine Parameter, die man in ein Ergebnis schreiben könnte.

    Reihenfolge, und warum sie so ist
    ---------------------------------
    1. Prüfen (:func:`pruefe_auftrag`) — **vor** jedem Ladeversuch. Regel 1 entscheidet,
       bevor 20 GB Gewichte auf die GPU wandern.
    2. Ein liegengebliebenes ``ausgabe_png`` löschen. Diese Lehre hat das Projekt schon
       einmal bezahlt (``seams.py``, Sitzung 05): Ein abgestürzter Lauf meldete sich am
       Bild des Vorlaufs gesund. Die Existenz einer Datei ist kein Beleg für ihren
       Inhalt — also wird abgeräumt statt geprüft.
    3. Modell holen, Modell rufen.
    4. Nachsehen, ob die versprochene Datei wirklich existiert. Ein Modell, das einen
       Pfad zurückgibt, ohne etwas zu schreiben, ist ein Fehlschlag — kein Erfolg mit
       fehlender Datei.
    """
    if not isinstance(a, RenderAuftrag):
        raise RenderError(
            f"rendere() braucht einen RenderAuftrag, bekam {type(a).__name__}. Ohne "
            f"Auftrag gibt es keine Parameter — und ohne Parameter kein Ergebnis, das "
            f"man protokollieren könnte."
        )

    maengel = pruefe_auftrag(a)
    if not (tiefe_invertieren is None or isinstance(tiefe_invertieren, bool)):
        # Ein Mangel und keine Ausnahme: Es gibt einen Auftrag, also gibt es ein Ergebnis.
        # Gedeutet wird nicht — «ja» oder 1 als wahr zu lesen hiesse raten, welche Karte
        # das Modell sehen sollte.
        maengel = list(maengel) + [
            f"tiefe_invertieren muss None, True oder False sein, war "
            f"{tiefe_invertieren!r}."]
        tiefe_invertieren = None

    # Der Eintrag kann fehlen (unbekannter Backbone). Dann trägt das Ergebnis den
    # angefragten Namen und einen Ersatzsatz — besser als gar kein Protokoll.
    try:
        eintrag = backbone.hole(a.backbone)
    except backbone.BackboneError:
        eintrag = None

    if eintrag is None:
        parameter = {
            "backbone": a.backbone, "modell_id": None, "konditionierung": None,
            "modus": MODUS_IMAGE_EDIT if a.beauty_png else MODUS_TXT2IMG,
            "depth_png": a.depth_png, "beauty_png": a.beauty_png,
            "ausgabe_png": a.ausgabe_png, "prompt": a.prompt,
            "negativ_prompt": a.negativ_prompt, "seed": a.seed, "schritte": a.schritte,
            "controlnet_staerke": a.controlnet_staerke, "denoise": a.denoise,
            "modell_wurzel": a.modell_wurzel,
        }
        return _ergebnis(STATUS_ABGELEHNT, parameter, error="; ".join(maengel),
                         maengel=maengel)

    lizenz = backbone.pruefe_lizenz(eintrag.name)
    parameter = _baue_parameter(a, eintrag, tiefe_invertieren=tiefe_invertieren)
    hinweise = _hinweise(a, parameter, lizenz)

    if maengel:
        # Kein Laden, kein Rechnen, keine GPU. Die Ablehnung ist das Ergebnis.
        return _ergebnis(STATUS_ABGELEHNT, parameter, error="; ".join(maengel),
                         maengel=maengel, lizenz=lizenz, hinweise=hinweise)

    if a.ausgabe_png is not None:
        # Siehe Docstring, Punkt 2: abräumen statt hinterher prüfen.
        Path(a.ausgabe_png).unlink(missing_ok=True)

    if modell is None and _lader is None and a.modell_wurzel is None:
        # Erst hier, und nicht in `pruefe_auftrag`: Wer ein fertiges Modell oder einen
        # eigenen Lader uebergibt, sucht nichts auf der Platte — eine Ablehnung waere
        # dort eine Aussage ueber eine Ablage, die niemand benutzt.
        lage = modellwurzel_lage(eintrag.name)
        if not lage["existiert"]:
            return _ergebnis(
                STATUS_ABGELEHNT, parameter, lizenz=lizenz,
                hinweise=tuple(hinweise) + (lage["grund"],),
                error=lage["grund"], maengel=(lage["grund"],))

    beginn = time.perf_counter()
    try:
        if modell is None:
            lader = _lader or lade_modell
            # Der Zähler geht NUR an den echten Lader. Ein Test-Lader mit fester
            # Signatur soll nicht daran scheitern, dass wir hier ein Argument mehr
            # durchreichen — und ein Test, der den Zähler beobachten will, übergibt ein
            # `modell` und braucht den Lader gar nicht.
            if _lader is None and schrittzaehler is not None:
                modell = lader(eintrag.name, a.modell_wurzel,
                               schrittzaehler=schrittzaehler)
            else:
                modell = lader(eintrag.name, a.modell_wurzel)
        antwort = modell(parameter)
    except Exception as fehler:                       # noqa: BLE001 — bewusst breit
        # Bewusst jede Ausnahme: Was ein fremdes Modell wirft, ist nicht vorhersagbar
        # (CUDA-OOM, kaputte Gewichte, ein Fehler in unserem eigenen Adapter). Ein
        # Stapelabbruch mitten in einer Serie kostet die ganze Serie; ein
        # 'status=fehler' mit Meldung kostet einen Auftrag und bleibt protokolliert.
        #
        # GRAFIKSPEICHER (B161/B1, 24.09.2026): Der Satz steht VOR der Ausnahme, und der
        # Zwischenspeicher von torch wird geleert — sonst hält der gescheiterte Versuch
        # den Speicher fest, den der nächste Auftrag braucht.
        text = f"{type(fehler).__name__}: {fehler}"
        if "OutOfMemoryError" in text or "out of memory" in text.lower():
            _leere_grafikspeicher()
            text = ("Grafikspeicher reichte nicht (Weg "
                    f"{getattr(modell, 'geraet', None) or 'unbekannt'}) — " + text)
        return _ergebnis(
            STATUS_FEHLER, parameter, dauer_s=time.perf_counter() - beginn,
            error=text, lizenz=lizenz, hinweise=hinweise,
            # Gerade hier: Ein Fehlschlag SAGT erst etwas, wenn dabeisteht, auf welchem
            # Weg er passiert ist. `modell` kann noch None sein, wenn schon das Laden
            # scheiterte — dann steht das da, und nicht nichts.
            geraeteweg=_geraeteweg(modell),
        )
    dauer = time.perf_counter() - beginn
    geraeteweg = _geraeteweg(modell)

    if isinstance(antwort, dict):
        bild_png = antwort.get("bild_png")
        # Was der Adapter beim Aufruf bemerkt hat, gehört ins Protokoll und nicht in die
        # Konsole: erst hier ist bekannt, welche Argumente die geladene Pipeline wirklich
        # genommen hat. Ein wirkungsloser Parameter, der nur im Auftrag steht und nirgends
        # ankommt, ist genau die stillschweigende Unwirksamkeit, die `_hinweise` verhindert.
        # DIE ABWEICHUNG STEHT VORNE UND NICHT UNTER FUENFZEHN ANDEREN.
        #
        # Die HomeStation hat es am 21.09.2026 aus der Praxis gemeldet
        # (`auf-20260921-130`): In `auf-20260919-123` stand die entscheidende Auskunft
        # woertlich da — als Hinweis unter vier anderen, und darum ueberlesen. Wer
        # Hinweise ueberfliegt, sieht den einen nicht, der den Lauf entwertet.
        eigene = tuple(antwort.get("hinweise") or ())
        vorn = tuple(h for h in eigene if h.startswith("BESTELLT WAR"))
        hinweise = vorn + tuple(hinweise) + tuple(h for h in eigene if h not in vorn)
        gerechnet = antwort.get("schritte_gerechnet")
        parameter["fuehrung_regler_angekommen"] = antwort.get("fuehrung_regler_angekommen")
        modus_bestellt = antwort.get("modus_bestellt")
        modus_gerechnet = antwort.get("modus_gerechnet")
    else:
        bild_png = antwort
        gerechnet = None
        modus_bestellt = None
        modus_gerechnet = None
    if not isinstance(bild_png, str) or not bild_png.strip():
        return _ergebnis(
            STATUS_FEHLER, parameter, dauer_s=dauer, lizenz=lizenz, hinweise=hinweise,
            geraeteweg=geraeteweg,
            error=(f"Das Modell lieferte keinen Bildpfad, sondern {antwort!r}. Der "
                   f"Vertrag der Naht ist: ein Pfad, oder ein Wörterbuch mit 'bild_png'."),
        )
    if not Path(bild_png).is_file():
        return _ergebnis(
            STATUS_FEHLER, parameter, dauer_s=dauer, lizenz=lizenz, hinweise=hinweise,
            geraeteweg=geraeteweg,
            error=(f"Das Modell meldete {bild_png!r}, dort liegt aber keine Datei. Ein "
                   f"gemeldeter Pfad ist kein Bild — deshalb wird nachgesehen."),
        )

    return _ergebnis(STATUS_OK, parameter, bild_png=bild_png, dauer_s=dauer,
                     lizenz=lizenz, hinweise=hinweise, schritte_gerechnet=gerechnet,
                     geraeteweg=geraeteweg, modus_bestellt=modus_bestellt,
                     modus_gerechnet=modus_gerechnet)


__all__ = [
    "MAX_SCHRITTE", "MAX_SEED", "MODUS_IMAGE_EDIT", "MODUS_TXT2IMG",
    "STATUSSE", "STATUS_ABGELEHNT", "STATUS_FEHLER", "STATUS_OK",
    "VORGABE_BACKBONE", "RenderAuftrag", "RenderError",
    "ALTWURZEL_HOMESTATION", "HERKUNFT_ALTWURZEL", "HERKUNFT_ANWENDUNGSDATEN",
    "HERKUNFT_UMGEBUNG", "UMGEBUNG_MODELLE", "VORGABE_MODELLWURZEL",
    "anwendungsdaten_wurzel", "lade_modell", "modellwurzel", "modellwurzel_lage",
    "pruefe_auftrag", "rendere", "schreibprobe", "standard_modell_wurzel",
]
