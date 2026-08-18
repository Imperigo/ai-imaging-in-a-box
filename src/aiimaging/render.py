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
import time
from dataclasses import dataclass
from pathlib import Path

from aiimaging import backbone

#: Die Konditionierung, die dieses Modul bedient. Alles andere braucht eine eigene
#: Adapterschicht und wird abgelehnt (siehe Modul-Docstring).
KOND_DEPTH_CONTROLNET = backbone.KOND_DEPTH_CONTROLNET

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
    2. **Konditionierungsart** — ``integriertes_edit`` hat keine Depth-ControlNet-Naht.
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
        if eintrag.konditionierung != KOND_DEPTH_CONTROLNET:
            maengel.append(
                f"Backbone {eintrag.name!r} konditioniert über "
                f"{eintrag.konditionierung!r}, nicht über {KOND_DEPTH_CONTROLNET!r}. "
                f"Für diese Familie existiert die Depth-ControlNet-Naht nicht; sie "
                f"braucht eine eigene Adapterschicht. Solange die fehlt, wird hier "
                f"nicht gerendert — ein Render ohne Tiefenkonditionierung erfindet die "
                f"Kubatur, und genau das soll dieses Projekt verhindern."
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

def lade_modell(backbone_name: str, modell_wurzel=None):
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
    if eintrag.konditionierung != KOND_DEPTH_CONTROLNET:
        raise RenderError(
            f"Backbone {eintrag.name!r} konditioniert über {eintrag.konditionierung!r} "
            f"und hat keine Depth-ControlNet-Naht. Es fehlt eine eigene Adapterschicht."
        )

    wurzel = Path(modell_wurzel) if modell_wurzel is not None else standard_modell_wurzel(eintrag.name)
    bestand = backbone.vorhandene_dateien(eintrag.name, wurzel)
    if not bestand["vollstaendig"]:
        raise RenderError(
            f"Gewichte für {eintrag.name!r} unvollständig unter {bestand['wurzel']!r} "
            f"(Verzeichnis existiert: {bestand['wurzel_existiert']}). Es fehlen: "
            f"{', '.join(bestand['fehlend'])}."
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

    pipeline = DiffusionPipeline.from_pretrained(str(wurzel), torch_dtype=torch.bfloat16)
    pipeline.to("cuda" if torch.cuda.is_available() else "cpu")
    return _pipeline_adapter(pipeline, eintrag, torch)


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


def _pipeline_adapter(pipeline, eintrag, torch):
    """Aus einer ``diffusers``-Pipeline ein Modell im Sinne dieses Moduls machen.

    **Ungeprüft.** Diese Funktion ist die einzige Stelle des Moduls, die hier nie
    ausgeführt werden kann: Es gibt weder ``torch`` noch Gewichte. Sie ist bewusst so
    kurz wie möglich gehalten, damit die ungeprüfte Fläche klein bleibt — alles
    Entscheidbare (Lizenz, Konditionierung, Parameter, Ergebnisaufbau) liegt ausserhalb
    und ist geprüft.

    Die genaue Verdrahtung des ControlNet unterscheidet sich je Backbone-Familie
    (Qwen, SDXL, SD3.5 nehmen die Tiefenkarte an verschiedenen Argumenten entgegen).
    Diese erste Fassung reicht die Tiefenkarte als ``control_image`` durch; ob das für
    jede Familie trägt, ist auf der HomeStation zu belegen und gehört dann hierher — es
    ist keine Aussage, die dieser Rechner treffen kann.
    """
    def modell(parameter: dict) -> str:
        from PIL import Image           # Pillow (MIT-CMU) — ebenfalls nur hier

        tiefe = Image.open(parameter["depth_png"]).convert("RGB")
        generator = torch.Generator(device=pipeline.device).manual_seed(parameter["seed"])

        argumente = {
            "prompt": parameter["prompt"],
            "negative_prompt": parameter["negativ_prompt"] or None,
            "control_image": tiefe,
            "controlnet_conditioning_scale": parameter["controlnet_staerke"],
            "num_inference_steps": parameter["schritte"],
            "generator": generator,
        }
        if parameter["modus"] == MODUS_IMAGE_EDIT:
            argumente["image"] = Image.open(parameter["beauty_png"]).convert("RGB")
            argumente["strength"] = parameter["denoise"]

        bild = pipeline(**argumente).images[0]
        ziel = parameter["ausgabe_png"] or str(
            Path(parameter["depth_png"]).with_name(f"render_{parameter['seed']}.png")
        )
        bild.save(ziel)
        return ziel

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
        "modell_wurzel": str(wurzel),
    }


def _hinweise(a: RenderAuftrag, parameter: dict, lizenz: dict) -> tuple[str, ...]:
    """Was auffällt, ohne ein Mangel zu sein.

    Der Unterschied zu einem Mangel: Ein Hinweis hält den Lauf nicht auf. Er verhindert
    aber, dass etwas **stillschweigend** wirkungslos bleibt — ein gesetztes ``denoise``
    ohne Ausgangsbild wird nicht kommentarlos verworfen, sondern benannt.
    """
    hinweise: list[str] = []
    if parameter["modus"] == MODUS_TXT2IMG and a.denoise != 0.0:
        hinweise.append(
            f"denoise={a.denoise} bleibt im Modus '{MODUS_TXT2IMG}' wirkungslos: Ohne "
            f"'beauty_png' gibt es kein Ausgangsbild, das überschrieben werden könnte."
        )
    if a.ausgabe_png is None:
        hinweise.append(
            "Ohne 'ausgabe_png' bestimmt das Modell den Ablageort. Damit entfällt der "
            "Schutz gegen ein liegengebliebenes Bild aus einem früheren Lauf."
        )
    hinweise.extend(lizenz["auflagen"])
    return tuple(hinweise)


def _ergebnis(status: str, parameter: dict, *, bild_png=None, dauer_s: float = 0.0,
              error=None, maengel=(), lizenz=None, hinweise=()) -> dict:
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
    }


def rendere(a: RenderAuftrag, *, modell=None, _lader=None) -> dict:
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

    Returns:
        ``{status, bild_png, seed, backbone, parameter, dauer_s, error, maengel, lizenz,
        hinweise}``.

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
        )
    dauer = time.perf_counter() - beginn

    bild_png = antwort.get("bild_png") if isinstance(antwort, dict) else antwort
    if not isinstance(bild_png, str) or not bild_png.strip():
        return _ergebnis(
            STATUS_FEHLER, parameter, dauer_s=dauer, lizenz=lizenz, hinweise=hinweise,
            error=(f"Das Modell lieferte keinen Bildpfad, sondern {antwort!r}. Der "
                   f"Vertrag der Naht ist: ein Pfad, oder ein Wörterbuch mit 'bild_png'."),
        )
    if not Path(bild_png).is_file():
        return _ergebnis(
            STATUS_FEHLER, parameter, dauer_s=dauer, lizenz=lizenz, hinweise=hinweise,
            error=(f"Das Modell meldete {bild_png!r}, dort liegt aber keine Datei. Ein "
                   f"gemeldeter Pfad ist kein Bild — deshalb wird nachgesehen."),
        )

    return _ergebnis(STATUS_OK, parameter, bild_png=bild_png, dauer_s=dauer,
                     lizenz=lizenz, hinweise=hinweise)


__all__ = [
    "MAX_SCHRITTE", "MAX_SEED", "MODUS_IMAGE_EDIT", "MODUS_TXT2IMG",
    "STATUSSE", "STATUS_ABGELEHNT", "STATUS_FEHLER", "STATUS_OK",
    "VORGABE_BACKBONE", "RenderAuftrag", "RenderError",
    "lade_modell", "pruefe_auftrag", "rendere", "standard_modell_wurzel",
]
