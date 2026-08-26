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

Abhängigkeiten: keine. Reine stdlib. ``torch`` und ``diffusers`` werden **ausschliesslich
innerhalb** von :func:`lade_modell` importiert — ein Import auf Modulebene machte
``import aiimaging.render`` auf jedem Rechner ohne GPU-Stack unmöglich und hinge damit
die halbe Bildkette an Hardware, die es hier nicht gibt.
"""
from __future__ import annotations

import math
import os
import re
import time
from dataclasses import dataclass
from pathlib import Path

from aiimaging import backbone, sprache

#: Die Konditionierung, die dieses Modul bedient. Alles andere braucht eine eigene
#: Adapterschicht und wird abgelehnt (siehe Modul-Docstring).
KOND_DEPTH_CONTROLNET = backbone.KOND_DEPTH_CONTROLNET
KOND_INTEGRIERTES_EDIT = backbone.KOND_INTEGRIERTES_EDIT
KONDITIONIERUNGEN = backbone.KONDITIONIERUNGEN

#: Vorgabe-Backbone, aus der Registry übernommen statt hier zweitgeschrieben. Ein
#: eigener Vorgabewert an dieser Stelle liefe beim nächsten Registry-Wechsel auseinander.
VORGABE_BACKBONE = backbone.VORGABE_BACKBONE

#: Umgebungsvariable für die Modellwurzel. Auf der HomeStation liegen die Gewichte unter
#: ``/ai`` (siehe ``auftrag.py``); jedes Modell in einem eigenen Unterordner mit seinem
#: Registry-Namen. Das ist eine **Setzung**, keine Messung — hier existiert kein ``/ai``.
UMGEBUNG_MODELLE = "AIIMAGING_MODELLE"
VORGABE_MODELLWURZEL = "/ai"

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


def standard_modell_wurzel(backbone_name: str) -> Path:
    """Wo die Gewichte eines Backbones vermutet werden, wenn nichts angegeben ist.

    ``$AIIMAGING_MODELLE/<backbone-name>``, ersatzweise ``/ai/<backbone-name>``. Die
    Umgebungsvariable hat Vorrang, damit die Ablage austauschbar bleibt — dasselbe
    Muster wie ``AIIMAGING_BLENDER`` in ``seams.py``.

    Reine Pfadrechnung: Es wird nichts geladen und nichts geprüft. Damit ist diese
    Funktion auch dort testbar, wo kein einziges Gewicht liegt.
    """
    wurzel = os.environ.get(UMGEBUNG_MODELLE) or VORGABE_MODELLWURZEL
    return Path(wurzel) / backbone_name


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

    erwartet = None
    if eintrag.vram_gb:
        # Die Registry trägt für dieses Backbone eine GEMESSENE Zahl; die Platte trägt
        # eine irreführende (s. `_lege_auf_geraet`). Die grösste Einzelkomponente wird
        # als Hälfte der Summe angesetzt — grob, aber auf der sicheren Seite: sie ist
        # nie grösser, und ein zu grosser Wert wählt höchstens den langsameren Weg.
        summe = int(eintrag.vram_gb * 2**30)
        erwartet = (summe, summe // 2)
    geraet, entflechtung = _lege_auf_geraet(pipeline, wurzel, torch, erwartet=erwartet)

    modell = _pipeline_adapter(pipeline, eintrag, torch, schrittzaehler=schrittzaehler)
    modell.geraet = geraet
    modell.entflechtung = entflechtung
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
    # Die zwei Prüfungen stehen VOR dem Import: Ein fehlender Ordner ist kein Grund,
    # erst 20 GB Bibliothekscode zu laden — und so bleiben sie ohne GPU-Stack prüfbar,
    # dieselbe Trennung wie in `lade_modell` selbst.
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

    from diffusers import ZImageControlNetModel, ZImageControlNetPipeline

    controlnet = ZImageControlNetModel.from_single_file(str(dateien[0]),
                                                       torch_dtype=torch.bfloat16)
    pipeline = ZImageControlNetPipeline.from_pretrained(str(wurzel), controlnet=controlnet,
                                                       torch_dtype=torch.bfloat16)
    return pipeline, f"ZImageControlNetPipeline + from_single_file({dateien[0].name})"


#: Vielfaches der Gewichtsgrösse, das frei sein muss, damit das ganze Modell auf der Karte
#: bleiben darf. Gemessen auf der HomeStation (`auf-20260818-09`): Qwen-Image-Edit-2511 in
#: bfloat16 belegt 29,57 GiB auf einer Karte mit 31,36 GiB nutzbar — voll geladen, und dann
#: scheitert die Bilderzeugung an einer Anforderung von **18 MiB**. Die Gewichte passen also,
#: die Aktivierungen nicht mehr. Der Zuschlag deckt genau diese Differenz ab.
GERAETE_ZUSCHLAG = 1.25


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


def _lege_auf_geraet(pipeline, wurzel, torch, *, erwartet=None) -> tuple[str, dict | None]:
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

    Returns:
        ``(weg, entflechtung)``. ``entflechtung`` ist ``None`` auf den beiden Wegen, die
        **nicht** auslagern — dort wird :func:`_entflechte_controlnet` bewusst nicht
        gerufen, weil seine 1,35 GiB einen gesunden Lauf erst in die Auslagerung drängen
        könnten. ``None`` heisst hier also *nicht nötig gewesen*, und der Grund steht in
        dieser Zeile.
    """
    if not torch.cuda.is_available():
        pipeline.to("cpu")
        return "cpu", None

    frei, _gesamt = torch.cuda.mem_get_info()
    summe, groesster = _gewichte_byte(wurzel) if erwartet is None else erwartet

    if not summe:                                  # nichts messbar: wie bisher verfahren
        pipeline.to("cuda")
        return "cuda", None

    if frei >= summe * GERAETE_ZUSCHLAG:
        pipeline.to("cuda")
        return "cuda", None

    # Ab hier wird ausgelagert — und erst ab hier ist die Verflechtung toedlich. Siehe
    # `_entflechte_controlnet`: Sie kostet Speicher, und Speicher ist genau das, woran
    # dieser Weg schon haengt.
    entflechtung = _entflechte_controlnet(pipeline)

    if frei >= groesster * GERAETE_ZUSCHLAG:
        # diffusers holt jede Komponente einzeln auf die Karte und legt sie danach zurück.
        pipeline.enable_model_cpu_offload()
        return "cuda+auslagerung", entflechtung

    # Selbst die grösste Komponente passt nicht am Stück. Dann wandern die Untermodule
    # einzeln — deutlich langsamer, aber der Lauf kommt durch. Ein Abbruch kostet ihn ganz.
    pipeline.enable_sequential_cpu_offload()
    return "cuda+schichtauslagerung", entflechtung


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
        import numpy as np                    # NumPy (BSD-3) — nur für diesen Fall
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

        genommen, verworfen = _vertraegliche_argumente(pipeline, argumente)
        hinweise = []

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
                               "guidance_scale", "strength", "callback_on_step_end")]
        if uebrig:
            hinweise.append(f"Nicht übergeben, weil unbekannt: {', '.join(uebrig)}.")

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
                "schritte_gerechnet": gerechnet[0] or None}

    modell.backbone = eintrag.name       # zur Fehlersuche: welches Modell steckt drin
    return modell


# --------------------------------------------------------------------------------------
# Der Lauf
# --------------------------------------------------------------------------------------

def _baue_parameter(a: RenderAuftrag, eintrag) -> dict:
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
        "tiefe_invertiert": (getattr(eintrag, "tiefen_polaritaet", backbone.POL_UNBEKANNT)
                             == backbone.POL_NAH_DUNKEL),
        # Auftrag schlägt Registry schlägt fremde Vorgabe. `None` bleibt `None` und wird
        # unten als solches gemeldet — ein eingesetzter Ersatzwert wäre eine Erfindung.
        "fuehrung": (float(a.fuehrung) if a.fuehrung is not None
                     else (float(eintrag.fuehrung) if getattr(eintrag, "fuehrung", None)
                           is not None else None)),
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
    """
    eintrag = backbone.BACKBONES.get(backbone_name)
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
    if parameter["tiefe_invertiert"]:
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

    if parameter["fuehrung"] is None:
        hinweise.append(
            f"Für '{parameter['backbone']}' ist keine Führung (guidance_scale) bestimmt. "
            f"Es greift die Vorgabe von diffusers — eine fremde Entscheidung, keine "
            f"eigene. Bei einem destillierten Turbo-Modell ist sie nachweislich falsch."
        )
    elif parameter["fuehrung"] <= 1.0 and a.negativ_prompt:
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
        ``{geraet, ladeweg, gemeldet, grund}``. ``gemeldet`` ist ``False``, wenn kein
        Modell geladen wurde **oder** das übergebene Modell die Angaben nicht führt — die
        Dreiteilung dieses Projekts: ``geraet=None`` heisst **unbekannt**, nie „CPU".
    """
    if modell is None:
        return {"geraet": None, "ladeweg": None, "entflechtung": None, "gemeldet": False,
                "grund": "Es wurde nichts geladen — der Auftrag kam nicht so weit."}
    geraet = getattr(modell, "geraet", None)
    if geraet is None:
        return {"geraet": None, "ladeweg": getattr(modell, "ladeweg", None),
                "entflechtung": getattr(modell, "entflechtung", None),
                "gemeldet": False,
                "grund": ("Das Modell fuehrt keine Geraeteangabe. So sieht eine Attrappe "
                          "aus, und so saehe auch ein fremder Lader aus — UNBEKANNT ist "
                          "hier nicht dasselbe wie 'auf der CPU'.")}
    return {"geraet": str(geraet), "ladeweg": getattr(modell, "ladeweg", None),
            # Ob dem ControlNet vor dem Auslagern eigene Kopien gegeben wurden. `None`
            # auf den Wegen, die nicht auslagern — siehe `_lege_auf_geraet`.
            "entflechtung": getattr(modell, "entflechtung", None),
            "gemeldet": True, "grund": ""}


def _ergebnis(status: str, parameter: dict, *, bild_png=None, dauer_s: float = 0.0,
              error=None, maengel=(), lizenz=None, hinweise=(),
              schritte_gerechnet=None, geraeteweg=None) -> dict:
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
    }


def rendere(a: RenderAuftrag, *, modell=None, _lader=None,
            schrittzaehler=None) -> dict:
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
    parameter = _baue_parameter(a, eintrag)
    hinweise = _hinweise(a, parameter, lizenz)

    if maengel:
        # Kein Laden, kein Rechnen, keine GPU. Die Ablehnung ist das Ergebnis.
        return _ergebnis(STATUS_ABGELEHNT, parameter, error="; ".join(maengel),
                         maengel=maengel, lizenz=lizenz, hinweise=hinweise)

    if a.ausgabe_png is not None:
        # Siehe Docstring, Punkt 2: abräumen statt hinterher prüfen.
        Path(a.ausgabe_png).unlink(missing_ok=True)

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
        return _ergebnis(
            STATUS_FEHLER, parameter, dauer_s=time.perf_counter() - beginn,
            error=f"{type(fehler).__name__}: {fehler}", lizenz=lizenz, hinweise=hinweise,
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
        hinweise = tuple(hinweise) + tuple(antwort.get("hinweise") or ())
        gerechnet = antwort.get("schritte_gerechnet")
    else:
        bild_png = antwort
        gerechnet = None
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
                     geraeteweg=geraeteweg)


__all__ = [
    "MAX_SCHRITTE", "MAX_SEED", "MODUS_IMAGE_EDIT", "MODUS_TXT2IMG",
    "STATUSSE", "STATUS_ABGELEHNT", "STATUS_FEHLER", "STATUS_OK",
    "VORGABE_BACKBONE", "RenderAuftrag", "RenderError",
    "lade_modell", "pruefe_auftrag", "rendere", "standard_modell_wurzel",
]
