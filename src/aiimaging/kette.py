"""Die Bildkette als Knotengraph — bauen, ausführen, zwischenspeichern.

Wozu dieses Modul da ist
------------------------
``graph.py`` trägt seit Phase 2 den Kern: typisierter DAG, topologische Sortierung,
Artefakt-Cache mit Inhalts-Hashing. Benutzt hat ihn bis hierher niemand — es gab keine
echten Knoten zu verketten. Jetzt gibt es sie (IFC→glb, Multipass, Render,
Geometrie-QA), und ``werkzeuge.enqueue_render`` verdrahtet sie als **gerade Abfolge**:
fest verdrahtet, ohne Zwischenspeicher, ohne Wiedereinstieg.

Dieses Modul ist der Schritt von der Abfolge zum Graphen. Der Unterschied ist nicht
Vokabular, sondern messbar:

* Wer nur den **Prompt** ändert, darf die teure Geometriestufe nicht erneut rechnen.
* Wer die **Geometrie** ändert, muss alles dahinter neu rechnen.

Beides entsteht **allein** aus den Inhalts-Hashes: Der Hash eines Knotens enthält die
Hashes seiner Vorgänger (``graph.inhalts_hash``). Es gibt in diesem Modul keine einzige
Zeile programmierter Invalidierung — es gibt nichts zu invalidieren, weil ein geänderter
Vorgänger schlicht einen anderen Schlüssel ergibt. Wo eine Regel „bei Änderung von X
lösche Y" stünde, wäre sie der erste Ort, an dem der Cache eines Tages falsche Treffer
liefert.

Innerer und äusserer Graph
--------------------------
Von aussen ist unsere ganze Bildkette **ein** Knoten in KosmoOrbits Pipeline; innen ist
sie selbst ein Graph (``docs/EINBINDUNG_KOSMOORBIT_2026-08-14.md``, Kap. 2). Der
Unterschied zeigt sich genau hier, im Datenfluss:

* **Aussen** (KosmoOrbit, ``mergeInputs``): Kanten entstehen über **Feldnamen-Gleichheit**,
  die Ausgaben aller Vorgänger werden übereinandergelegt und weitergereicht.
* **Innen** (hier): Kanten sind **Knoten-IDs**, und jeder Knoten bekommt die Ausgaben
  seiner Vorgänger als Liste **in der Reihenfolge seiner Eingänge** — nicht verschmolzen.
  Die QA-Stufe hat zwei Eingänge (Soll aus dem Multipass, Ist aus dem Render); würden sie
  verschmolzen, wäre nicht mehr entscheidbar, welches ``depth_png`` gemeint ist.

Der Bild-Eingang — und wo er heute endet
----------------------------------------
Seit dem 19.09.2026 kann ein Bild **zurück in eine Rechnung**: ``ART_NACHRENDER`` hat
einen zweiten Eingangsslot für ``bild_png``, und ``ART_BILDQUELLE`` holt eine Bilddatei
von der Platte in den Graphen (``haenge_nachrender_an``). Damit existiert der Pfad für
«Hineinskizzieren»: rendern → die PNG öffnen und hineinzeichnen → dieselbe Datei als
Bildquelle → nachrendern.

**Drei Grenzen, und sie sind gemessen, nicht befürchtet:**

1. **Die Tiefenkarte bleibt Pflicht.** ``render.RenderAuftrag.depth_png`` hat keinen
   Vorgabewert, und ``render.pruefe_auftrag`` lehnt einen Auftrag ohne sie ab. Für das
   Hineinskizzieren ist das richtig — der Strich soll in derselben Geometrie landen. Eine
   **reine** Bildbearbeitung ohne Modell («Photoshop ersetzen») geht damit **nicht**: Sie
   bräuchte einen Auftrag, der ein Bild ohne Geometrie annimmt.
2. **Ob das Ausgangsbild beim Modell ankommt, hängt an der Pipeline.** Hat sie keinen
   eigenen Steuereingang, bekommt die Tiefenkarte den einen Bildeingang und das
   Ausgangsbild fällt weg. Für ``qwen-image-edit-2511`` ist das am Gerät gemessen
   (``auf-20260818-09``); für alle anderen ist es **nicht gemessen**. Siehe
   :func:`bildeingang_lage`.
3. **Der fremde Vertrag hat kein Feld dafür.** ``kosmo_szene.BEKANNTE_FELDER`` kennt kein
   Eingangsbild, und ein erfundenes Feld wird als unbekannt **abgelehnt**. Der Weg über
   KosmoOrbit existiert also nicht; aus Python heraus existiert er (Regel 4).

Zwei Schichten, und jedes Bild weiss, welche es ist
--------------------------------------------------
**Owner-Entscheid 19.09.2026, nachmittags** — und er berichtigt den Bau vom Vormittag:

* **Layer 1, der Geometrielayer.** Aus dem Modell gerechnet, gegen die Tiefenkarte
  gemessen. Er trägt ein **eigenes** Geometrie-Urteil.
* **Layer 2, der AI-Imaging-Layer.** Pixelbasiert, darauf aufgesetzt — Hineingezeichnetes,
  Lichtstimmung, Materialvarianten; der Lightroom- und Photoshop-Ersatz. Er trägt **kein
  eigenes** Geometrie-Urteil, wohl aber das **seiner Basis**.

Am Vormittag hatte die Kette gelernt, ein von Hand bearbeitetes Bild mit einem Vorbehalt
zu versehen (:data:`FELD_HANDEINGRIFF`): Die Prüfung meldet «nicht anwendbar». Das ist
richtig und war zu grob — mit dem eigenen Urteil verschwand auch das Urteil über die
Geometrie **darunter**. Bei einer Variantenstudie will genau das jemand wissen.

    *Ein Vorbehalt soll die Auskunft einschränken, nicht sie löschen.*

Getragen wird das von :data:`FELD_SCHICHT` (welche Schicht dieses Bild ist) und
:data:`FELD_BASIS` (das Urteil der Basis, ausdrücklich als fremdes). Die beiden Urteile
stehen unter **verschiedenen Namen auf verschiedenen Ebenen** und sind nie verwechselbar:
``bestanden`` ist immer das eigene, ``basis['geometrie_bestanden']`` immer das der Basis.
Wo der Block herkommt und warum er nie zwischengespeichert wird, steht bei
:func:`schichtbefund`.

Zwei Wege nebeneinander
-----------------------
``werkzeuge.enqueue_render`` bleibt unangetastet, bis diese Kette belegt ist. Zwei Wege
nebeneinander sind vorübergehend in Ordnung; ein halb umgebauter ist es nicht.

Abhängigkeiten: nur stdlib und das eigene Paket. Kein ``bpy``, kein ``ifcopenshell``,
kein ``torch`` auf Modulebene — die ganze Kette läuft mit Attrappen ohne GPU und ohne
Blender durch (siehe ``AUSFUEHRER``).
"""
from __future__ import annotations

import re
import shutil
import tempfile
import time
from collections.abc import Callable, Sequence
from pathlib import Path

from aiimaging import (
    backbone, bildlesen, contracts, geometrie_qa, glbbox, maske, raumkamera, render,
    seams, tiefenschaetzer, torwaechter,
)
from aiimaging.graph import (
    ArtefaktCache, Bedarf, Graph, GraphError, Knoten, inhalts_hash, pruefe_bedarf,
)

# --------------------------------------------------------------------------------------
# Namen
# --------------------------------------------------------------------------------------

#: Knotenarten der Standardkette. Die Art entscheidet, **welche** Funktion rechnet
#: (``AUSFUEHRER``); die Knoten-ID entscheidet nur, wie verdrahtet wird. Beide fallen in
#: der Standardkette zufällig zusammen — verlassen darf sich darauf nichts.
ART_GEOMETRIE = "geometrie"
ART_MULTIPASS = "multipass"
ART_RENDER = "render"
ART_QA = "qa"

#: Zwei Arten **ausserhalb** der Standardkette: der Bild-Eingang.
#:
#: **Der Befund, der sie erzwingt** (`docs/PLAN_BIS_FEBRUAR_2027.md`, November, und hier
#: am 19.09.2026 nachgemessen): Der `render`-Knoten hat genau einen Eingangsslot, und der
#: muss ein Multipass sein (``BEDARF[ART_RENDER]``). Ein Bild kann im Graphen entstehen
#: und verglichen werden — **zurück in eine Rechnung kommt es nie.** Damit haben
#: «Hineinskizzieren» und «Photoshop ersetzen» keinen Pfad.
#:
#: Warum zwei **neue** Arten und nicht ein zweiter Slot am `render`-Knoten: ``Bedarf``
#: kennt keinen wahlweisen Slot. Ein zweiter deklarierter Slot machte jeden heutigen
#: `render`-Knoten zu einem Verdrahtungsfehler (``pruefe_bedarf`` → ``fehlender-eingang``,
#: Schwere ``error``) — ein neues Tor, das sperrt, was gestern lief. Die bestehende Kette
#: bleibt darum Zeile für Zeile, wie sie war.
#:
#: ``ART_BILDQUELLE`` ist der Weg, auf dem **ein Mensch** wieder hereinkommt: eine Datei
#: von der Platte, mit Inhalts-Hash. Ohne sie könnte nur Maschine an Maschine reichen —
#: und genau dazwischen sitzt der Architekt, der in das Bild hineinzeichnet.
ART_BILDQUELLE = "bildquelle"
ART_NACHRENDER = "nachrender"

#: Das Feld, mit dem ein Bild mitführt, dass ein **Mensch** daran war.
#:
#: **Owner-Entscheid 19.09.2026.** Zeichnet jemand einen Balkon ins Bild, den das Modell
#: nicht hat, misst die Geometrie-QA genau die Abweichung, die der Mensch **absichtlich**
#: erzeugt hat. Drei Antworten waren möglich, und die gewählte ist die dritte:
#:
#: * *Prüfen wie bisher* — dann fällt **jedes** hineingezeichnete Bild durch. Eine
#:   Warnung, die immer kommt, liest nach dem dritten Mal niemand mehr.
#: * *Gar nicht prüfen* — dann trägt das Bild danach **keine Auskunft**, und später sieht
#:   ihm niemand an, ob es je geprüft war.
#: * **«Nicht anwendbar»** — die Prüfung läuft, und ihr Urteil lautet weder bestanden noch
#:   durchgefallen. *Die dritte Antwort dieses Projekts, angewandt auf den Handeingriff.*
#:
#: **Und es wird VERERBT.** Ein Nachrender eines Nachrenders trägt es weiter, und eine
#: Bildquelle setzt es von sich aus: Eine Datei, die von der Platte kommt, ist per
#: Definition nicht aus dieser Rechnung. *Ein Vorbehalt, der beim Weiterrechnen verfällt,
#: ist keiner — er ist eine Fussnote mit Verfallsdatum.*
FELD_HANDEINGRIFF = "handeingriff"

#: **Die zwei Schichten** — Owner-Entscheid 19.09.2026.
#:
#: Bis hierher kannte die Kette nur *ein* Bild: aus dem Modell gerechnet, gegen die
#: Tiefenkarte gemessen. Der Handeingriff hat daneben einen zweiten Fall aufgemacht, und
#: die erste Fassung hat ihn zu grob behandelt — sie warf mit dem eigenen Urteil auch das
#: Urteil ueber die Geometrie darunter weg. *Ein Vorbehalt soll die Auskunft
#: einschraenken, nicht sie loeschen.*
#:
#: * :data:`SCHICHT_GEOMETRIE` — **Layer 1, der Geometrielayer.** Aus dem Modell
#:   gerechnet, gegen die Tiefenkarte messbar. Er traegt ein **eigenes**
#:   Geometrie-Urteil: bestanden, durchgefallen oder nicht gemessen.
#: * :data:`SCHICHT_AI_IMAGING` — **Layer 2, der AI-Imaging-Layer.** Pixelbasiert, auf
#:   Layer 1 aufgesetzt: Hineingezeichnetes, Lichtstimmung, Materialvarianten. Er traegt
#:   **kein eigenes** Geometrie-Urteil, wohl aber das **seiner Basis**.
#:
#: **Layer 1 ist der Normalfall.** Layer 2 entsteht heute aus zwei Quellen — einem
#: Handeingriff (:data:`FELD_HANDEINGRIFF`) und einer Bildquelle von der Platte — und
#: kuenftig aus einer Rechnung ohne Modell. Ein Nachrender auf einem unberuehrten Render
#: bleibt Layer 1: Er rechnet weiter gegen dieselbe Tiefenkarte, und sein Bild ist gegen
#: sie messbar.
SCHICHT_GEOMETRIE = "geometrielayer"
SCHICHT_AI_IMAGING = "ai-imaging-layer"

#: Das Feld, mit dem **jedes Bildergebnis sagt, welche Schicht es ist**. Es steht im
#: Knotenergebnis und geht damit in den Zwischenspeicher — das darf es, weil es allein
#: aus den Eingaengen dieses Knotens folgt und aus nichts sonst.
FELD_SCHICHT = "schicht"

#: Das Feld, in dem ein Layer-2-Bild **das Urteil seiner Basis** mitfuehrt — und zwar
#: ausdruecklich als *fremdes* Urteil.
#:
#: **Die Trennung ist bindend** (Owner-Vorgabe 19.09.2026): Das eigene Urteil steht in
#: ``bestanden``, das der Basis in ``basis[BASIS_BESTANDEN]``. Zwei verschiedene Namen auf
#: zwei verschiedenen Ebenen. Ein Feld, in dem einmal das eigene und einmal das fremde
#: Urteil steht, waere genau der Fehler, gegen den dieses Projekt seit Wochen
#: anschreibt — darum heisst der Schluessel im Block **nicht** ``bestanden``.
#:
#: ``None`` fuer den ganzen Block heisst: Dieses Bild ist selbst Layer 1, es hat keine
#: Basis unter sich. Ein Block mit ``geometrie_bestanden = None`` heisst etwas anderes:
#: Es gibt eine Basis, aber ueber sie ist **nichts gemessen**.
FELD_BASIS = "basis"

#: Die Schluessel des Basis-Blocks. Aufgezaehlt statt hingeschrieben, damit ein Leser
#: nicht raten muss und ein Tippfehler auffaellt.
BASIS_KNOTEN = "knoten"                    #: Wer die Basis gerechnet hat (Knoten-ID).
BASIS_BILD = "bild"                        #: Welches Bild die Basis ist (Pfad).
BASIS_BESTANDEN = "geometrie_bestanden"    #: DAS URTEIL DER BASIS — nie das eigene.
BASIS_URTEIL_VON = "urteil_von"            #: Welcher QA-Knoten es gefaellt hat.
BASIS_HERKUNFT = "herkunft"                #: WIE die Basis bestimmt wurde.
BASIS_GRUND = "grund"                      #: Klartext, auch und gerade bei ``None``.

#: Wie eine Basis bestimmt wurde. Ohne diese Angabe waere die Basis eine Behauptung ohne
#: Herkunft — und eine Behauptung ohne Herkunft ist in diesem Projekt keine Auskunft.
HERKUNFT_BILDKETTE = "ueber die Bildkette"
HERKUNFT_GEOMETRIE = "ueber dieselbe Geometrie"

#: Knoten-IDs der Standardkette.
KNOTEN_GEOMETRIE = "geometrie"
KNOTEN_MULTIPASS = "multipass"
KNOTEN_RENDER = "render"
KNOTEN_QA = "qa"

#: Knoten-IDs des Bild-Eingangs. Sie tragen eine laufende Nummer, sobald mehr als eine
#: Runde angehängt wird (siehe :func:`haenge_nachrender_an`) — zwei Runden im selben
#: Graphen sind der Normalfall und keine Ausnahme.
KNOTEN_BILDQUELLE = "bildquelle"
KNOTEN_NACHRENDER = "nachrender"

#: Zustände eines Knotens im Lauf.
#:
#: ``abgelehnt`` ist bewusst von ``fehler`` getrennt und wird **wortgleich** aus
#: ``render.py`` und dem Torwächter übernommen: „der Auftrag verletzt eine Regel" ist
#: etwas anderes als „es wurde versucht und ging schief". Wer beides zu ``fehler``
#: verschmilzt, sucht später die Ursache im falschen Lager.
STATUS_OK = "ok"
STATUS_ABGELEHNT = "abgelehnt"
STATUS_FEHLER = "fehler"
STATUS_UEBERSPRUNGEN = "uebersprungen"

#: Welche Parameter eines Knotens **Eingabedateien** benennen. Ihr Inhalt fliesst in den
#: Hash, ihr **Pfad** nicht (``graph.inhalts_hash``, Argument ``param_dateien``).
#:
#: Warum nur die Geometriestufe darin steht: Alles weitere Material entsteht **in** der
#: Kette. Die glb des Multipass kommt aus der Geometriestufe, und deren Hash steckt
#: bereits im Vorgänger-Hash. Die grosse Datei ein zweites Mal zu lesen kostete Zeit und
#: brächte keine einzige zusätzliche Aussage.
EINGABEDATEIEN: dict[str, tuple[str, ...]] = {
    ART_GEOMETRIE: ("ifc_path", "glb_path"),
    # DER GRUND, WARUM DER BILD-EINGANG ÜBERHAUPT FUNKTIONIEREN KANN. Ein Mensch
    # zeichnet in ein Bild und speichert es — **unter demselben Namen**. Stünde
    # ``bild_png`` nicht hier, ginge nur der Pfad in den Hash, der Hash bliebe gleich,
    # und der Zwischenspeicher lieferte das Bild von vor der Zeichnung zurück. Die
    # Zeichnung wäre verschwunden, und zwar lautlos.
    ART_BILDQUELLE: ("bild_png",),
}

#: Endungen von Ausgabefeldern, die auf eine Datei zeigen. Gebraucht beim Cache-Treffer:
#: siehe ``_fehlende_ausgabedateien``.
_DATEIFELD_ENDUNGEN = ("_png", "_exr", "_glb", "_path")

#: Was jede Knotenart von ihren Vorgängern **braucht** und was sie **zusagt**
#: (``graph.Bedarf``). Zwei Dinge hängen daran, und beide sind aus einem gemessenen
#: Fehler entstanden:
#:
#: * ``pruefe_kette`` prüft einen Graphen damit, **ohne ihn auszuführen** — das
#:   Gegenstück zu KosmoOrbits ``pipelineReadiness`` für den inneren Graphen.
#: * ``fuehre_aus`` verwirft damit einen Cache-Eintrag, dessen Pflichtfeld leer ist oder
#:   dessen zugesagte Datei fehlt. Genau das fehlte, als in Sitzung 07 ein
#:   Multipass-Eintrag mit ``depth_png=None`` als Treffer gültig blieb und die Stufe nie
#:   wieder gerechnet wurde.
#:
#: Die Tabelle steht hier und nicht in ``graph.py``: Welche Felder es gibt, weiss die
#: Bildkette, nicht der Ablaufkern — dieselbe Grenze wie bei ``AUSFUEHRER``.
#:
#: **Was sich nicht ausdrücken lässt.** Die QA liest das Soll bevorzugt aus der EXR und
#: fällt auf das PNG zurück (``bildlesen.tiefen_aus_report``); gebraucht wird also
#: *eines von beiden*. Eine flache Pflichtliste kann kein Entweder-oder — dieselbe Grenze
#: wie bei ``required`` im äusseren Vertrag (siehe ``mcp_schemas``, Modul-Docstring).
#: Deklariert ist darum ``depth_png``: Es ist das Feld, ohne das der Multipass-Knoten
#: ohnehin nicht als gelungen gilt, und es ist das, was die Renderstufe konditioniert.
BEDARF: dict[str, Bedarf] = {
    ART_GEOMETRIE: Bedarf(
        liefert=("glb_path", "up_axis"),
        dateien=("glb_path",),
    ),
    ART_MULTIPASS: Bedarf(
        braucht=(("glb_path",),),
        liefert=("depth_png",),
        # Wahlweise und darum nicht in ``liefert``: Der Beauty-Pass lässt sich
        # abschalten, und die EXR fehlt, wenn der Runner nur das PNG geschrieben hat.
        # Genannt sind sie trotzdem — steht ein Pfad drin, muss die Datei auch daliegen.
        dateien=("depth_png", "depth_exr", "beauty_png", "material_id_png"),
    ),
    ART_RENDER: Bedarf(
        braucht=(("depth_png",),),
        liefert=("bild_png",),
        dateien=("bild_png",),
    ),
    ART_QA: Bedarf(
        # Slot 0 ist das Soll (Multipass), Slot 1 das Ist (Render) — die Reihenfolge ist
        # Bedeutung, und genau darum ist ``braucht`` je Slot aufgeschrieben.
        braucht=(("depth_png",), ("bild_png",)),
        liefert=("bestanden",),
    ),
    # --- Der Bild-Eingang ------------------------------------------------------------
    ART_BILDQUELLE: Bedarf(
        # Kein ``braucht``: Dieser Knoten hat keine Vorgänger. Er ist ein Quellknoten wie
        # die Geometriestufe, nur dass seine Quelle ein Bild ist.
        liefert=("bild_png",),
        dateien=("bild_png",),
    ),
    ART_NACHRENDER: Bedarf(
        # ZWEI SLOTS, UND DIE REIHENFOLGE IST BEDEUTUNG — dieselbe Bauform wie die QA.
        # Slot 0 trägt die Geometrie (Tiefenkarte aus dem Multipass), Slot 1 das Bild,
        # auf dem weitergerechnet wird. Verschmölzen sie, wäre nicht mehr entscheidbar,
        # welches der beiden Bilder das Ausgangsbild ist und welches die Konditionierung.
        #
        # Slot 1 nimmt ``bild_png`` und damit **jeden** Knoten, der eines zusagt: einen
        # ``render``, einen ``bildquelle``, oder einen weiteren ``nachrender``. Der Weg
        # Bild → Rechnung → Bild ist damit beliebig oft hintereinander möglich.
        braucht=(("depth_png",), ("bild_png",)),
        liefert=("bild_png",),
        dateien=("bild_png",),
    ),
}

#: Was in einem Verzeichnisnamen stehen darf. Die Knotenart ist freier Text und darf den
#: Arbeitsordner nicht verlassen — dieselbe Überlegung wie beim Cache-Schlüssel in
#: ``graph.ArtefaktCache._pfad``.
_UNSICHER = re.compile(r"[^0-9A-Za-z._-]+")


class KettenError(RuntimeError):
    """Die Kette ist nicht schlüssig beschrieben oder wird falsch benutzt.

    Bewusst getrennt von ``GraphError``: Der Graph-Kern meldet Fehler an der *Struktur*
    (doppelte ID, unbekannter Eingang, Kreis), dieses Modul meldet Fehler an der
    *Bildkette* (weder IFC noch glb, kein Prompt, keine Ausführerfunktion für eine Art).

    Ein gescheiterter **Knoten** wirft nicht — er wird zum Ergebnis mit
    ``status='fehler'``. Geworfen wird nur, wo es nichts zu protokollieren gäbe, weil
    noch gar nicht gerechnet wurde. Dieselbe Linie wie ``RenderError`` in ``render.py``.
    """


# --------------------------------------------------------------------------------------
# Bau
# --------------------------------------------------------------------------------------

def _als_bbox(bbox) -> list[list[float]] | None:
    """bbox in die Form bringen, die ein ``Knoten`` tragen kann — oder ablehnen.

    ``Knoten.params`` verlangt eine verlustfreie JSON-Runde und weist Tupel darum ab.
    Eine bbox kommt aber ganz natürlich als Tupel daher. Die Umwandlung Tupel→Liste ist
    reine Schreibweise und keine Bedeutungsänderung, deshalb wird sie hier vorgenommen
    statt dem Aufrufer aufgebürdet. Alles, was **inhaltlich** keine bbox ist, fliegt.
    """
    if bbox is None:
        return None
    if isinstance(bbox, (str, bytes)) or not isinstance(bbox, Sequence) or len(bbox) != 2:
        raise KettenError(
            f"bbox erwartet [[xmin,ymin,zmin],[xmax,ymax,zmax]], war {bbox!r}."
        )
    ecken: list[list[float]] = []
    for ecke in bbox:
        if isinstance(ecke, (str, bytes)) or not isinstance(ecke, Sequence) or len(ecke) != 3:
            raise KettenError(f"bbox-Ecke erwartet drei Zahlen, war {ecke!r}.")
        werte = []
        for wert in ecke:
            if isinstance(wert, bool) or not isinstance(wert, (int, float)):
                raise KettenError(f"bbox enthält keine Zahl: {wert!r}.")
            werte.append(float(wert))
        ecken.append(werte)
    return ecken


def baue_kette(
    *,
    ifc_path: str | Path | None = None,
    glb_path: str | Path | None = None,
    up_axis=None,
    bbox=None,
    prompt: str | None = None,
    negativ_prompt: str = "",
    backbone: str = render.VORGABE_BACKBONE,
    seed: int = 0,
    schritte: int = 20,
    controlnet_staerke: float = 0.8,
    denoise: float = 0.6,
    nutze_beauty: bool = True,
    aufloesung: int = 512,
    samples: int = 16,
    beauty: bool = True,
    material_id: bool = True,
    qa: bool = True,
    qa_schwelle: float = geometrie_qa.SCHWELLE_GEOMETRIE,
    gelaende_erwartet: bool = True,
    hintergrund: float | None = None,
    schaetzer: str = tiefenschaetzer.VORGABE_TIEFENSCHAETZER,
    hintergrund_strategie: str = tiefenschaetzer.HG_WIE_SOLL,
    hintergrund_anteil: float | None = None,
    # ── DIE ELF, DIE DER ABHOLER BESTELLEN KONNTE UND DIESER WEG NICHT ───────────────
    #
    # Gemessen am 21.09.2026, nicht vermutet: `seams.glb_zu_multipass` nimmt 21 Angaben
    # an. Der Abholer bestellt 17 davon, dieser Weg bestellte **8**. Elf Dinge waren
    # ueber den Graphen nicht erreichbar — darunter der Sonnenstand, die Blickrichtung,
    # die Rahmung und die Augenhoehe, also genau das, was eine Architektin einstellen
    # will.
    #
    # Das ist derselbe Fehler, den der Abholer am 26.08.2026 an sich selbst gefunden hat
    # («drei Kameraparameter, die der Runner seit jeher kennt und die auf diesem Weg NIE
    # ankamen»), eine Ebene hoeher:
    #
    #     *Eine Faehigkeit, die der Runner hat und die ueber einen der Wege nicht
    #     bestellbar ist, gibt es fuer jeden, der diesen Weg benutzt, nicht.*
    #
    # `None` heisst hier ueberall NICHT ANGEFASST: Dann gelten die Vorgaben des Runners,
    # und jede bisher ueber diesen Weg gemessene Aufnahme bleibt reproduzierbar. Dieser
    # Zusatz ist rein additiv — er aendert kein Verhalten, er macht eines erreichbar.
    kamera=None,
    kamera_modus: str | None = None,
    kamera_huellbox=None,
    sonne=None,
    gelaende_z: float | None = None,
    hoehe: float | None = None,
    deckungsgrad: float | None = None,
    augenhoehe: float | None = None,
    bias_grad: float | None = None,
    stillstand_frist_s: float | None = None,
    multipass_timeout: float | None = None,
    # DER STANDPUNKT VON HAND — die letzten drei der gemessenen Luecke.
    #
    # Sie waren ueber diesen Weg nur MITTELBAR erreichbar: ueber `innenraum`, das sie
    # ausrechnen laesst. Wer eine Aussenkamera an eine bestimmte Stelle setzen will — die
    # naheliegendste Bedienhandlung ueberhaupt —, konnte das nicht.
    #
    # ZWEI QUELLEN FUER DASSELBE WERDEN ABGEWIESEN, nicht stillschweigend geordnet: Wer
    # `innenraum` UND `auge` angibt, bekommt einen Satz statt einer Auswahl. Eine
    # Vorrangregel waere genau die Sorte Entscheidung, an die sich spaeter niemand
    # erinnert — und die falsche Kamera sieht man dem Bild nicht an.
    auge=None,
    blick_auf=None,
    brennweite: float | None = None,
) -> Graph:
    """Die Standardkette als Graph: ``geometrie → multipass → render → qa``.

    Args:
        ifc_path: IFC-Eingang. Genau eines von ``ifc_path`` und ``glb_path``.
        glb_path: glb-Eingang, wenn die Konversion schon anderswo lief.
        up_axis: Up-Achse der glb. **Pflicht bei glb-Eingang**, verboten bei IFC-Eingang
            (dort bestimmt sie der Runner). Der Phase-0-Befund in Person: KosmoDraw
            liefert Z-up, KosmoVis Y-up, und ein Default wäre eine stille Verdrehung.
        bbox: ``[[xmin,ymin,zmin],[xmax,ymax,zmax]]`` in Metern. Bei IFC-Eingang liefert
            sie die Konversion selbst; bei glb-Eingang ist sie die einzige Grundlage des
            Torwächters — ohne sie wird abgelehnt (siehe ``_fuehre_geometrie``).
        prompt: Was zu sehen sein soll. Pflicht.
        negativ_prompt, backbone, seed, schritte, controlnet_staerke, denoise:
            siehe ``render.RenderAuftrag``.
        nutze_beauty: Den Beauty-Pass als Anker verwenden (``image_edit``) statt aus dem
            Nichts zu beginnen (``txt2img``). Steht als Parameter im Knoten, damit die
            Betriebsart im Hash landet — sonst gälte ein txt2img-Ergebnis als Treffer für
            einen image_edit-Auftrag.
        aufloesung, samples, beauty, material_id: siehe ``seams.glb_zu_multipass``.
        qa: ``False`` lässt den QA-Knoten weg. Für Läufe, die nur ein Bild wollen.
        qa_schwelle, hintergrund: siehe ``geometrie_qa.geometrie_gate``.
        schaetzer, hintergrund_strategie, hintergrund_anteil: siehe
            ``tiefenschaetzer.qa_gegen_soll``. Der Schätzername gehört in die Parameter
            und damit in den Hash: Ein Urteil, das mit einem anderen Schätzer entstanden
            ist, ist ein anderes Urteil.

    Returns:
        Ein ``Graph`` mit drei bzw. vier Knoten. Er wird **nicht** ausgeführt — Bau und
        Lauf sind getrennt, damit ein Graph auch nur angeschaut, serialisiert oder von
        Hand verändert werden kann.

    Raises:
        KettenError: Eingang fehlt, ist doppelt oder ist unvollständig beschrieben.

    **Warum die QA zwei Eingänge hat.** Die Aufgabenstellung nennt die Kette als gerade
    Folge, die Sache selbst ist aber verzweigt: Die QA vergleicht die Soll-Tiefe aus dem
    Multipass mit der Ist-Tiefe aus dem erzeugten Bild. Sie hängt also an **beiden**
    Stufen, nicht nur an der letzten. Genau darum ist die Kette ein Graph und keine
    Liste — und darum ist ``eingaenge`` eine Reihenfolge und keine Menge: Slot 0 ist
    Soll, Slot 1 ist Ist.
    """
    if bool(ifc_path) == bool(glb_path):
        raise KettenError(
            "Genau einer der beiden Eingänge wird gebraucht: ifc_path (dann konvertiert "
            "die Kette selbst) oder glb_path (dann ist die Konversion schon gelaufen). "
            f"Bekommen: ifc_path={ifc_path!r}, glb_path={glb_path!r}."
        )
    if not isinstance(prompt, str) or not prompt.strip():
        raise KettenError(
            f"prompt fehlt oder ist leer ({prompt!r}). Die Kubatur kommt aus der "
            f"Tiefenkarte, aber Material, Licht und Stimmung kommen aus dem Prompt — "
            f"ohne ihn ist nicht beschrieben, was entstehen soll."
        )

    geometrie_params: dict = {"bbox": _als_bbox(bbox)}
    if ifc_path:
        if up_axis is not None:
            raise KettenError(
                "up_axis zusammen mit ifc_path ist widersprüchlich: Bei IFC-Eingang "
                "bestimmt der Konversionsrunner die Achse und meldet sie im Report. Ein "
                "hier gesetzter Wert wäre entweder überflüssig oder eine Behauptung, die "
                "der Runner gleich widerlegt."
            )
        geometrie_params["ifc_path"] = str(ifc_path)
    else:
        # Wirft ContractError, wenn die Achse fehlt oder nicht deutbar ist — die Prüfung
        # gehört an den Bau, nicht in den Lauf: Ein Graph, der schon beim Aufschreiben
        # falsch ist, soll nicht erst nach der Konversion auffallen.
        try:
            geometrie_params["up_axis"] = contracts.normalize_up_axis(up_axis)
        except contracts.ContractError as fehler:
            raise KettenError(f"glb-Eingang ohne brauchbare up_axis: {fehler}") from fehler
        geometrie_params["glb_path"] = str(glb_path)

    knoten = [
        Knoten(id=KNOTEN_GEOMETRIE, art=ART_GEOMETRIE, params=geometrie_params),
        Knoten(
            id=KNOTEN_MULTIPASS,
            art=ART_MULTIPASS,
            params={
                "aufloesung": int(aufloesung),
                "samples": int(samples),
                "beauty": bool(beauty),
                "material_id": bool(material_id),
                # SIE STEHEN IM KNOTEN UND DAMIT IM HASH — das ist der Punkt. Ein Bild
                # mit Abendsonne darf nicht als Treffer fuer eine Bestellung mit
                # Mittagssonne gelten. Genau so ein Treffer waere der teuerste Ausgang:
                # Der Lauf gelingt, das Bild liegt da, und niemand sieht ihm an, dass er
                # etwas anderes bestellt hatte.
                **{name: wert for name, wert in {
                    "kamera": kamera,
                    "kamera_modus": kamera_modus,
                    "kamera_huellbox": kamera_huellbox,
                    "sonne": sonne,
                    "gelaende_z": gelaende_z,
                    "hoehe": hoehe,
                    "deckungsgrad": deckungsgrad,
                    "augenhoehe": augenhoehe,
                    "bias_grad": bias_grad,
                    "stillstand_frist_s": stillstand_frist_s,
                    "multipass_timeout": multipass_timeout,
                    "auge": auge,
                    "blick_auf": blick_auf,
                    "brennweite": brennweite,
                }.items() if wert is not None},
            },
            eingaenge=(KNOTEN_GEOMETRIE,),
        ),
        Knoten(
            id=KNOTEN_RENDER,
            art=ART_RENDER,
            params={
                "prompt": prompt,
                "negativ_prompt": negativ_prompt,
                "backbone": backbone,
                "seed": int(seed),
                "schritte": int(schritte),
                "controlnet_staerke": float(controlnet_staerke),
                "denoise": float(denoise),
                "nutze_beauty": bool(nutze_beauty),
            },
            eingaenge=(KNOTEN_MULTIPASS,),
        ),
    ]
    if qa:
        knoten.append(Knoten(
            id=KNOTEN_QA,
            art=ART_QA,
            params={
                "schwelle": float(qa_schwelle),
                "hintergrund": None if hintergrund is None else float(hintergrund),
                "schaetzer": schaetzer,
                "hintergrund_strategie": hintergrund_strategie,
                # OB IN DIESER SZENE UEBERHAUPT GELAENDE STEHT — eine Erklaerung des
                # Aufrufers, keine Annahme des Moduls. Ein reines Gebaeude-IFC bringt gar
                # kein Gelaende mit; die Gelaenderegel meldet dann «nicht erkannt», die
                # Maske faellt aus, und mit ihr das zweite Tor. Der Abholer hat dafuer
                # `--kein-gelaende`; bis zum 26.08.2026 hatte die Kette nichts.
                "gelaende_erwartet": bool(gelaende_erwartet),
                "hintergrund_anteil": (None if hintergrund_anteil is None
                                       else float(hintergrund_anteil)),
            },
            # Reihenfolge ist Bedeutung: Slot 0 = Soll (Multipass), Slot 1 = Ist (Render).
            eingaenge=(KNOTEN_MULTIPASS, KNOTEN_RENDER),
        ))
    return Graph(knoten)


def haenge_nachrender_an(
    graph: Graph,
    *,
    prompt: str,
    eingangsbild: str | Path | None = None,
    bildquelle_knoten: str | None = None,
    multipass_knoten: str = KNOTEN_MULTIPASS,
    negativ_prompt: str = "",
    backbone: str | None = None,
    seed: int | None = None,
    schritte: int | None = None,
    controlnet_staerke: float | None = None,
    denoise: float = 0.6,
    id_vorsatz: str | None = None,
) -> Graph:
    """Einen Bild-Eingang an einen bestehenden Graphen hängen: **Bild rein, Bild raus.**

    Das ist die zweite Hälfte des Entwurfsablaufs, und bis zum 19.09.2026 gab es sie
    nicht: Ein Bild konnte im Graphen entstehen und geprüft werden, aber nie wieder in
    eine Rechnung zurück.

    Args:
        graph: Ein bestehender Graph, üblicherweise aus :func:`baue_kette`. Er wird
            **nicht verändert** — zurück kommt ein neuer Graph mit denselben Knoten und
            den angehängten dazu. ``Knoten`` ist ``frozen``, und ein Graph, der sich unter
            dem Aufrufer ändert, hätte einen anderen Hash, als der Aufrufer glaubt.
        prompt: Was am Bild geändert werden soll. **Pflicht und bewusst ohne Vorgabe:**
            Der Prompt des ersten Renders beschreibt, was entstehen sollte; dieser hier
            beschreibt, was sich ändern soll. Denselben Text zweimal zu nehmen wäre eine
            Vorgabe, die fast immer falsch ist.
        eingangsbild: Eine Bilddatei von der Platte — **der Weg, auf dem ein Mensch
            hereinkommt.** Gesetzt, entsteht ein ``bildquelle``-Knoten davor. ``None``
            heisst: Das Ausgangsbild kommt aus dem Graphen selbst.
        bildquelle_knoten: Die ID des Knotens, dessen ``bild_png`` als Ausgangsbild
            dient. ``None`` und ohne ``eingangsbild`` heisst :data:`KNOTEN_RENDER`.
            Genau eines von beiden — ``eingangsbild`` und ``bildquelle_knoten`` zugleich
            wäre zwei Ausgangsbilder für einen Eingang.
        multipass_knoten: Woher die Tiefenkarte kommt. Sie bleibt Pflicht: Der Strich
            soll in **derselben** Geometrie landen wie das Bild, in das er gezeichnet
            wurde.
        backbone, seed, schritte, controlnet_staerke: ``None`` übernimmt den Wert des
            Renderknotens dieses Graphen, sofern es einen gibt — sonst die Vorgaben von
            :func:`baue_kette`. Ein zweiter Lauf mit stillschweigend anderen Einstellungen
            wäre ein Vergleich zwischen zwei Sachen.
        denoise: Wieviel vom Ausgangsbild überschrieben wird, 0..1. Klein heisst: Die
            Zeichnung bleibt stehen und wird nur angeglichen. Gross heisst: Das Modell
            rechnet fast neu. **Der Vorgabewert 0.6 ist GESETZT und nicht gemessen** — er
            ist derselbe wie in :class:`aiimaging.render.RenderAuftrag`, damit nicht zwei
            Orte zwei Zahlen führen.
        id_vorsatz: Vorsatz für die neuen Knoten-IDs, z.B. ``"runde2"``. ``None`` wählt
            selbst einen freien Namen. Zwei Runden im selben Graphen sind der Normalfall.

    Returns:
        Ein neuer ``Graph``. Er wird **nicht** ausgeführt.

    Raises:
        KettenError: Der Graph ist keiner, ein genannter Knoten fehlt, ``prompt`` ist
            leer, oder es sind zwei Ausgangsbilder genannt.

    **Was diese Funktion nicht von sich aus anhängt: eine QA-Stufe** — und was passiert,
    wenn man sie anhängt, ist seit dem 19.09.2026 entschieden.

    Die Geometrie-QA vergleicht das Bild mit der Tiefenkarte des Modells. Zeichnet jemand
    einen Balkon hinein, der im Modell nicht steht, misst sie genau die Abweichung, die
    der Mensch **absichtlich** erzeugt hat.

    **Owner-Entscheid: Das Urteil lautet dann «nicht anwendbar».** Nicht durchgefallen
    (sonst fiele jedes bearbeitete Bild durch, und eine Warnung, die immer kommt, wird
    nicht gelesen) und nicht übersprungen (sonst trüge das Bild keine Auskunft mehr).
    ``bestanden`` ist ``None``, ``status`` bleibt ``ok``, und der Grund steht im Klartext
    daneben.

    Getragen wird das von :data:`FELD_HANDEINGRIFF`, und es **wird vererbt**: Eine
    Bildquelle setzt es, ein Nachrender reicht es weiter. *Ein Vorbehalt, der beim
    Weiterrechnen verfällt, ist keiner.*

    **Und seit dem Nachmittag desselben Tages verschwindet damit nicht mehr alles.** Das
    Bild ist dann Layer 2 (:data:`SCHICHT_AI_IMAGING`) und führt das Urteil **seiner
    Basis** mit — welches Layer-1-Bild darunter liegt, von welchem Knoten es stammt und
    wie es dort ausgegangen ist (:data:`FELD_BASIS`, gefüllt von :func:`schichtbefund`).
    Acht Varianten auf derselben geprüften Geometrie sind damit als solche erkennbar.

    Wer die Stufe anhängen will, tut es mit ``eingaenge=(multipass, nachrender)``.
    """
    if not isinstance(graph, Graph):
        raise KettenError(
            f"haenge_nachrender_an erwartet einen Graph, bekam {type(graph).__name__}."
        )
    if not isinstance(prompt, str) or not prompt.strip():
        raise KettenError(
            f"prompt fehlt oder ist leer ({prompt!r}). Ein Nachrender ohne Anweisung "
            f"wäre ein zweiter Lauf, der dasselbe noch einmal versucht."
        )
    if eingangsbild is not None and bildquelle_knoten is not None:
        raise KettenError(
            "eingangsbild und bildquelle_knoten zugleich: Das wären zwei Ausgangsbilder "
            "für einen Eingang. Genau eines von beiden."
        )
    if multipass_knoten not in graph.knoten:
        raise KettenError(
            f"Den Knoten {multipass_knoten!r} gibt es in diesem Graphen nicht. "
            f"Vorhanden: {sorted(graph.knoten)}. Ohne Tiefenkarte gibt es keine "
            f"Konditionierung — und ohne sie erfände das Modell die Kubatur."
        )

    quelle = bildquelle_knoten
    if eingangsbild is None and quelle is None:
        quelle = KNOTEN_RENDER
    if quelle is not None and quelle not in graph.knoten:
        raise KettenError(
            f"Den Knoten {quelle!r} gibt es in diesem Graphen nicht. "
            f"Vorhanden: {sorted(graph.knoten)}."
        )

    # Die Einstellungen des vorhandenen Renderknotens übernehmen, soweit nichts anderes
    # gesagt ist. Zwei Läufe mit stillschweigend verschiedenem Backbone oder Seed sähen
    # aus wie ein Vergleich und wären keiner.
    # ACHTUNG beim Weiterbauen: Der Parameter `backbone` verdeckt in dieser Funktion das
    # gleichnamige Modul. Wer hier einen Registry-Zugriff braucht, holt ihn über
    # `render.backbone` oder benennt die lokale Variable um — ein `backbone.hole(...)`
    # an dieser Stelle riefe einen String auf.
    vorlage: dict = {}
    for kid in sorted(graph.knoten):
        if graph.knoten[kid].art in (ART_RENDER, ART_NACHRENDER):
            vorlage = graph.knoten[kid].params
            break

    def _wahl(wert, name, vorgabe):
        if wert is not None:
            return wert
        return vorlage.get(name, vorgabe)

    vorsatz = id_vorsatz or _freier_vorsatz(graph)
    quelle_id = f"{vorsatz}-{KNOTEN_BILDQUELLE}"
    nach_id = f"{vorsatz}-{KNOTEN_NACHRENDER}"
    for kid in (quelle_id, nach_id):
        if kid in graph.knoten:
            raise KettenError(
                f"Die Knoten-ID {kid!r} ist schon vergeben. Ein anderer 'id_vorsatz' "
                f"löst das; ein stilles Überschreiben wäre ein anderer Graph, als der "
                f"Aufrufer aufgeschrieben hat."
            )

    neue: list[Knoten] = []
    if eingangsbild is not None:
        neue.append(Knoten(id=quelle_id, art=ART_BILDQUELLE,
                           params={"bild_png": str(eingangsbild)}))
        quelle = quelle_id

    neue.append(Knoten(
        id=nach_id,
        art=ART_NACHRENDER,
        params={
            "prompt": prompt,
            "negativ_prompt": negativ_prompt,
            "backbone": _wahl(backbone, "backbone", render.VORGABE_BACKBONE),
            "seed": int(_wahl(seed, "seed", 0)),
            "schritte": int(_wahl(schritte, "schritte", 20)),
            "controlnet_staerke": float(_wahl(controlnet_staerke,
                                              "controlnet_staerke", 0.8)),
            "denoise": float(denoise),
        },
        # Reihenfolge ist Bedeutung: Slot 0 = Geometrie (Tiefenkarte), Slot 1 = Bild.
        eingaenge=(multipass_knoten, quelle),
    ))
    return Graph(list(graph.knoten.values()) + neue)


def _freier_vorsatz(graph: Graph) -> str:
    """Ein Namensvorsatz, den dieser Graph noch nicht trägt: ``runde2``, ``runde3``, …

    Von Hand vergebene IDs kollidieren irgendwann, und eine Kollision meldet ``Graph``
    zwar — aber erst, wenn der Aufrufer schon alles aufgeschrieben hat. Billiger ist ein
    Name, der von vornherein frei ist.
    """
    n = 2
    while any(kid.startswith(f"runde{n}-") for kid in graph.knoten):
        n += 1
    return f"runde{n}"


# --------------------------------------------------------------------------------------
# Die Ausführer — eine Funktion je Knotenart
# --------------------------------------------------------------------------------------
#
# Vertrag jeder Ausführerfunktion:
#
#     fn(*, knoten: Knoten, eingaben: list[dict], out_dir: Path) -> dict
#
# `eingaben` sind die Ausgaben der Vorgänger **in der Reihenfolge der Eingänge**.
# `out_dir` ist ein Arbeitsverzeichnis, das allein diesem Knoten und diesem Hash gehört
# (siehe `_arbeitsverzeichnis`); es existiert bereits, wenn die Funktion gerufen wird.
#
# Zurück kommt ein dict. Trägt es ein Feld `status`, entscheidet dieses über Erfolg;
# fehlt es, gilt der Knoten als gelungen. Der Vorgabewert ist Absicht: Die Runner-Reports
# aus `seams.py` tragen teils keinen Status, und eine Attrappe im Test soll nicht drei
# Pflichtfelder ausfüllen müssen, um „hat geklappt" zu sagen.


def _raeume_lesen(ifc_path) -> dict | None:
    """Räume und ihre Kamerastandpunkte — oder eine benannte Lücke.

    **Warum das an dieser Stelle steht.** Räume gibt es nur in der IFC. Sobald daraus eine
    glb geworden ist, sind Wände und Böden Dreiecke ohne Raumbegriff — der einzige Moment,
    in dem die Frage beantwortbar ist, ist **vor** der Umwandlung.

    **Warum ein Fehlschlag hier die Kette nicht anhält.** Innenaufnahmen sind eine
    Zugabe; der Aussenweg funktioniert ohne sie. Eine Kette, die an einer unlesbaren
    Raumliste stürbe, lieferte kein einziges Bild, statt eines ohne Innenansichten. Der
    Befund verschwindet trotzdem nicht — sonst sähe eine Datei ohne Räume aus wie eine,
    die nie gefragt wurde.
    """
    try:
        bericht = seams.ifc_raeume(str(ifc_path))
    except Exception as fehler:      # noqa: BLE001 — siehe Docstring
        return {"status": "fehler", "raeume": [],
                "grund": f"Räume nicht lesbar: {type(fehler).__name__}: {fehler}"}
    if bericht.get("status") != "ok":
        return {"status": bericht.get("status"), "raeume": [],
                "grund": bericht.get("error") or "Der Raumleser meldete keinen Erfolg."}

    mit_standpunkten = []
    for raum in bericht.get("raeume") or []:
        try:
            punkte = raumkamera.standpunkte(raum)
        except raumkamera.RaumkameraError as fehler:
            punkte = {"raum": raum.get("name"), "standpunkte": [], "n_brauchbar": 0,
                      "befund": f"Kein Standpunkt berechenbar: {fehler}"}
        mit_standpunkten.append({"raum": raum, "kamera": punkte})
    return {"status": "ok", "raeume": mit_standpunkten,
            "n_mit_standpunkt": sum(1 for r in mit_standpunkten
                                    if r["kamera"]["n_brauchbar"] > 0),
            "grund": ""}


def _erste_bbox(*kandidaten):
    """Die erste bbox, die wirklich eine ist — ``None`` zaehlt nicht als Angabe.

    Gebraucht, weil ``dict.get(schluessel, ersatz)`` den Ersatz **nur bei fehlendem
    Schluessel** liefert. Ein gesetztes ``None`` gewinnt dort gegen den Ersatz, und genau
    daran ist am 21.09.2026 der ganze Kettenweg gescheitert.
    """
    for kandidat in kandidaten:
        if kandidat is not None:
            return kandidat
    return None


def _bbox_aus_glb(glb_path, up_axis: str):
    """Die Szenenbox aus der glb selbst — oder ``None``, wenn sie nicht lesbar ist.

    Das ``None`` ist hier die dritte Antwort und keine Ausrede: Wer die Datei nicht lesen
    kann, weiss nicht, ob der Massstab stimmt, und der Torwaechter lehnt danach mit
    seiner eigenen Begruendung ab. Was diese Funktion **nicht** tun darf, ist raten — eine
    erfundene Ausdehnung wuerde die Massstabspruefung stillschweigend bestehen lassen.
    """
    try:
        return glbbox.bauwerksbox(glb_path, up_axis=up_axis)["bbox_szene"]
    except (glbbox.GlbError, OSError, KeyError):
        return None


def _fuehre_geometrie(*, knoten: Knoten, eingaben: list[dict], out_dir: Path) -> dict:
    """IFC → glb (Subprozess im ``.venv-ifc``) oder glb durchreichen — dann Torwächter.

    Der Torwächter läuft in **beiden** Fällen und nicht als eigener Knoten. Begründung:
    Er ist reine Rechnung auf der bbox, kostet nichts und beantwortet dieselbe Frage wie
    die Stufe selbst — „ist diese Geometrie brauchbar?". Ein eigener Knoten brächte einen
    zweiten Cache-Eintrag für null Rechenzeit.

    Lehnt der Torwächter ab, ist der Knoten ``abgelehnt`` und alles dahinter wird
    übersprungen. Das ist der Zweck der Stufe: Ein um Faktor 1000 fehlskaliertes Modell
    soll auffallen, **bevor** Blender und GPU laufen.
    """
    p = knoten.params
    if p.get("ifc_path"):
        bericht = seams.ifc_zu_glb(p["ifc_path"], str(out_dir / "modell.glb"))
        if bericht.get("status") != "ok":
            return {
                "status": STATUS_FEHLER,
                "error": f"IFC→glb meldete {bericht.get('status')!r}: {bericht.get('error')}",
                "bericht": bericht,
            }
        raeume = _raeume_lesen(p["ifc_path"])
        ausgaben = {
            "glb_path": bericht.get("glb_path"),
            # Räume gibt es NUR auf dem IFC-Weg. Aus einer glb lassen sie sich nicht
            # gewinnen: Dort sind Wände und Böden Dreiecke, kein Raumbegriff. Wer über
            # `glb_path` einsteigt, bekommt darum `raeume: None` — nicht gemessen, nicht
            # „keine Räume".
            "raeume": raeume,
            "up_axis": bericht.get("up_axis", "Y"),
            # `bericht.get("bbox", p.get("bbox"))` STAND HIER, UND DAS IST DIE FALLE:
            # Traegt der Report den Schluessel `bbox` mit dem Wert None, gibt `.get` die
            # None zurueck und nicht den Ersatz. Der zweite Parameter greift nur bei
            # FEHLENDEM Schluessel, nie bei einem gesetzten None — derselbe Griff, der am
            # 21.09.2026 schon `homeworker._darf_starten` zu Fall gebracht hat.
            "bbox": _erste_bbox(bericht.get("bbox"), p.get("bbox")),
            "n_elements": bericht.get("n_elements"),
            "n_triangles": bericht.get("n_triangles"),
        }
    else:
        ausgaben = {
            "glb_path": p["glb_path"],
            "raeume": None,
            "up_axis": p["up_axis"],
            # HIER STAND NUR `p.get("bbox")`, UND DAS HAT DEN GANZEN WEG GESPERRT.
            #
            # Am 21.09.2026 von der HomeStation auf ZWEI unabhaengigen Wegen gemeldet
            # (`auf-20260921-127` am Graphenweg, `auf-20260921-136` am Produktweg): Der
            # Lauf bricht am ERSTEN Knoten mit «Konversion meldet status='ok', traegt
            # aber keine brauchbare bbox (None)». Der Torwaechter hatte recht — er bekam
            # wirklich keine. Nur lag das nicht am Modell, sondern daran, dass beim
            # glb-Eingang niemand die Ausdehnung mitgibt: Der Produktweg wandelt die IFC
            # beim Import und uebergibt der Kette danach nur noch den glb-Pfad.
            #
            # **Eine Angabe, die das Programm aus der Datei selbst ausrechnen kann, darf
            # es nicht vom Aufrufer verlangen.** Die Ausdehnung einer glb steht in der
            # glb; sie zu fordern hiess, denjenigen scheitern zu lassen, der die Datei
            # vorlegt, aber ihre Masse nicht kennt.
            #
            # Gemessen wird hier die SZENENbox und nicht die Bauwerksbox, weil der
            # Torwaechter den Massstab der Konversion prueft — und dafuer zaehlt, was in
            # der Datei steht, nicht was davon Bauwerk ist. Der Weg ueber die
            # Bauwerksbox ist der fuer die Kamera; die beiden duerfen nicht verwechselt
            # werden.
            #
            # Eine ausdrueckliche `bbox` des Aufrufers gewinnt weiterhin: Wer sie kennt,
            # hat sie meist aus einer Quelle, die mehr weiss als die Datei.
            "bbox": _erste_bbox(p.get("bbox"), _bbox_aus_glb(p["glb_path"], p["up_axis"])),
            "n_elements": None,
            "n_triangles": None,
        }

    urteil = torwaechter.torwaechter({"status": "ok", "bbox": ausgaben["bbox"]})
    ausgaben["torwaechter"] = urteil
    ausgaben["empfiehlt_neuzentrierung"] = bool(urteil.get("empfiehlt_neuzentrierung"))
    if urteil["entscheidung"] != torwaechter.ENTSCHEIDUNG_ANNEHMEN:
        ausgaben["status"] = STATUS_ABGELEHNT
        ausgaben["error"] = f"Torwächter: {urteil['begruendung']}"
        return ausgaben
    ausgaben["status"] = STATUS_OK
    ausgaben["error"] = None
    return ausgaben


def _fuehre_multipass(*, knoten: Knoten, eingaben: list[dict], out_dir: Path) -> dict:
    """glb → Beauty, Tiefe (EXR + PNG), Material-ID über ``blender --background``.

    Die teuerste Stufe der Kette und darum der eigentliche Grund für den
    Zwischenspeicher: Sie darf bei einer blossen Prompt-Änderung nicht wieder anlaufen.
    """
    if not eingaben:
        return {"status": STATUS_FEHLER, "error": "Multipass ohne Vorgänger — keine glb."}
    geometrie = eingaben[0]
    glb_path = geometrie.get("glb_path")
    if not glb_path:
        return {"status": STATUS_FEHLER,
                "error": f"Vorgänger lieferte kein 'glb_path': {sorted(geometrie)}"}

    p = knoten.params
    # Innenansicht: NUR auf ausdrückliche Bestellung. Ein Auftrag, der nicht danach
    # gefragt hat, soll keine Innenaufnahme bekommen — und ein Auftrag, der danach
    # gefragt hat und sie nicht bekommen kann, soll scheitern statt aussen zu rendern.
    # VON HAND GESETZT — oder aus dem Innenraum gerechnet. **Beides zugleich gibt es
    # nicht**, und die Pruefung steht HIER und nicht in `baue_kette`.
    #
    # Der erste Anlauf legte sie dorthin — und sie waere toter Code gewesen: `innenraum`
    # ist gar kein Parameter von `baue_kette`, es wird von aussen an den Knoten gesetzt.
    # Der Fall kann dort also nie eintreten, und die Abfrage haette nie ausgeloest.
    #
    #     *Ein Waechter an einer Stelle, an der der Fall nicht vorkommt, ist kein
    #     Waechter. Er ist eine Beruhigung.*
    #
    # An dieser Stelle koennen beide Angaben wirklich nebeneinander am Knoten stehen, und
    # genau hier wird abgewiesen statt geordnet: Eine Vorrangregel waere eine Entscheidung,
    # an die sich spaeter niemand erinnert — und die falsche Kamera sieht man dem Bild
    # nicht an.
    von_hand = [n for n in ("auge", "blick_auf", "brennweite") if p.get(n) is not None]
    if von_hand and p.get("innenraum"):
        return {"status": STATUS_FEHLER,
                "error": (f"Standpunkt zweimal bestellt: `innenraum` rechnet ihn aus, und "
                          f"{', '.join(von_hand)} gibt ihn vor. Welcher gilt, entscheidet "
                          f"dieses Modul nicht.")}

    auge = p.get("auge")
    blick_auf = p.get("blick_auf")
    brennweite = p.get("brennweite")
    if p.get("innenraum"):
        wunsch = p["innenraum"]
        wahl = raumkamera.waehle(geometrie.get("raeume"),
                                 raum=wunsch.get("raum"),
                                 art=wunsch.get("art", raumkamera.ART_FRONTAL))
        if not wahl["gefunden"]:
            return {"status": STATUS_FEHLER,
                    "error": ("Innenansicht verlangt, aber kein Standpunkt: "
                              + wahl["grund"]),
                    "innenraum": wahl}
        auge = list(wahl["standpunkt"]["auge"])
        blick_auf = list(wahl["standpunkt"]["blick_auf"])
        # **Die Brennweite gehört zum Standpunkt, nicht zur Szene.** `raumkamera` rechnet
        # das Sichtfeld mit ``BRENNWEITE_INNEN_MM`` (24 mm) und prüft es gegen die belegte
        # 16-mm-Grenze; wer nur Auge und Blickziel hinüberreicht, bekommt drüben den
        # Rückfall des Runners — **50 mm**.
        #
        # Gemessen am 09.09.2026 (`docs/INNENANSICHT_2026-09-09.md`), Raum-Nord frontal,
        # 800 × 496: Bei 50 mm trägt die ganze Tiefenkarte **einen einzigen Wert** —
        # Spanne 0,000 m, eine Stufe, 100 % des Bildes auf einer Ebene. Bei 24 mm sind es
        # 1,191 m über 73 Stufen. *Eine Tiefenkarte aus einem Wert kann keine Rangordnung
        # tragen; die Geometrie-QA misst dort nichts mehr.*
        #
        # Dieselbe Naht-Sache wie Brennweite und Geländestand am 23.08. und wie
        # `gelaende_erwartet` am 24.08.: im Modul längst gerechnet, auf dem Weg nicht
        # durchgereicht. Zum vierten Mal — und darum steht sie hier mit ihrer Messung.
        brennweite = (wahl["standpunkt"].get("sichtfeld") or {}).get("brennweite_mm")

    # WAS NICHT IM KNOTEN STEHT, WIRD NICHT UEBERGEBEN — und damit gilt drueben die
    # Vorgabe des Runners. Ein `None` durchzureichen waere etwas anderes: Es setzte den
    # Wert ausdruecklich auf nichts und ueberschriebe damit die Vorgabe.
    #
    # `multipass_timeout` heisst hier so und drueben `timeout`. Der Name ist bewusst
    # verschieden: In `baue_kette` gibt es schon andere Fristen, und ein zweites `timeout`
    # waere die Sorte Feldname, bei der man spaeter raten muss, welche Frist gemeint war.
    # `auge`, `blick_auf` und `brennweite` stehen NICHT in dieser Liste: Sie gehen weiter
    # unten als eigene Argumente mit, und zweimal uebergeben waere ein TypeError.
    weiter = {name: p[name] for name in
              ("kamera", "kamera_modus", "kamera_huellbox", "sonne", "gelaende_z",
               "hoehe", "deckungsgrad", "augenhoehe", "bias_grad", "stillstand_frist_s")
              if name in p}
    if "multipass_timeout" in p:
        weiter["timeout"] = p["multipass_timeout"]

    bericht = seams.glb_zu_multipass(
        glb_path, out_dir,
        up_axis=geometrie.get("up_axis"),
        aufloesung=p["aufloesung"], samples=p["samples"],
        beauty=p["beauty"], material_id=p["material_id"],
        auge=auge, blick_auf=blick_auf, brennweite=brennweite,
        **weiter,
    )
    bericht.setdefault("status", STATUS_OK)

    # Die Naht ist bewusst nachsichtig: Scheitert die Normalisierung, bleibt der
    # Blender-Lauf gültig, weil die EXR mit den echten Metern das massgebliche Artefakt
    # ist (siehe `seams._tiefe_nachbearbeiten`). **Für diesen Knoten gilt das nicht.**
    #
    # Der Unterschied ist nicht Geschmack, sondern der Zwischenspeicher. Ein Knoten mit
    # `status="ok"` wird gespeichert; Gescheitertes nicht. Ohne diese Prüfung liefe
    # folgendes — und es ist gemessen, nicht befürchtet:
    #
    #   1. Der Multipass läuft, das PNG scheitert, der Knoten gilt als `ok`.
    #   2. Der Eintrag landet im Cache. `_fehlende_ausgabedateien` fängt ihn nicht ab:
    #      Es prüft nur Felder mit einem nicht-leeren Text als Wert, und `depth_png`
    #      ist `None`.
    #   3. Wird die Ursache behoben, ändert sich am Cache-Schlüssel nichts — er hängt an
    #      Parametern und Vorgänger-Hashes, nicht an der Umgebung. Der Treffer bleibt,
    #      der Ausführer wird nie wieder gerufen, und die Kette scheitert für immer eine
    #      Stufe später mit einer Meldung, die auf den falschen Knoten zeigt.
    #
    # Drei Läufe, ein einziger Blender-Start, und der dritte hätte gelingen müssen. Ein
    # vergifteter Cache-Eintrag ist teurer als ein neu gerechneter Render.
    #
    # Der Knoten braucht das PNG: Sein Nachfolger konditioniert das Bildmodell damit.
    # Was der Nachfolger braucht, darf hier nicht als gelungen gelten.
    #
    # **Warum die Regel stehenbleibt, obwohl der Kern den Fall inzwischen selbst fängt.**
    # Schritt 2 stimmt so nicht mehr: ``BEDARF`` nennt ``depth_png`` als Pflichtfeld, und
    # ein Eintrag mit leerem Pflichtfeld ist kein Treffer (``_cache_maengel``). Der Cache
    # bliebe also auch ohne diese Zeilen brauchbar — er würde nur bei jedem Lauf neu
    # rechnen, statt den Fehlschlag gar nicht erst zu speichern. Was die Regel zusätzlich
    # leistet, ist die **Meldung am richtigen Knoten**: Ohne sie meldet erst die
    # Renderstufe ein fehlendes Feld, und die Ursache liegt eine Stufe davor. Sitzung 07
    # hat genau daran gelernt, dass ein Bericht lauter sein muss als eine
    # Bibliotheksfunktion — `auf-01` bis `auf-05` haben die Blender-5.2-Sperre nur
    # deshalb gefunden, weil der Multipass `fehler` zurückmeldete und nicht `ok` mit
    # einem fehlenden Dateinamen in einer Liste.
    if not bericht.get("depth_png"):
        grund = bericht.get("depth_png_fehler") or bericht.get("error") or "kein Grund genannt"
        return {**bericht, "status": STATUS_FEHLER,
                "error": (f"Multipass lieferte keine normalisierte Tiefenkarte: {grund} "
                          f"(Die EXR kann trotzdem in Ordnung sein — sie steht in "
                          f"`depth_exr`. Ohne das PNG gibt es aber keine Konditionierung "
                          f"für die Renderstufe.)")}
    return bericht


def render_ausfuehrer(*, modell=None, _lader=None,
                      schrittzaehler=None) -> Callable[..., dict]:
    """Baut die Render-Stufe — mit optional injiziertem Bildmodell.

    Warum eine Fabrik und nicht einfach eine Funktion: Ein Modell ist ein Objekt und kann
    nicht in ``Knoten.params`` stehen, denn die müssen JSON-fähig sein (sie gehen in den
    Hash). Die Naht ``modell=`` aus ``render.rendere`` muss also von aussen an den
    Ausführer gebunden werden, bevor der Lauf beginnt. Wer nichts injiziert, bekommt die
    Vorgabe: ``render.rendere`` lädt selbst — und braucht dann Gewichte und GPU.

    ``render.rendere`` beantwortet auch das Scheitern mit einem Ergebnis
    (``status='abgelehnt'``/``'fehler'``) statt mit einer Ausnahme. Das passt hier
    unverändert durch, weil dieses Modul dieselben Statuswörter benutzt.

    ``schrittzaehler`` wird durchgereicht. Es ist **der einzige belegte Fortschritt, den
    dieses Projekt hat**: Er zählt Diffusionsschritte, die wirklich gerechnet wurden —
    nicht das Weiterleben eines Prozesses. Bis zum 21.09.2026 war die Naht in
    ``render.rendere`` vorhanden und **von der Kette aus nicht erreichbar**; damit gab es
    sie für jeden, der über den Graphen rechnet, nicht.

        *Eine Naht, die nur der direkte Aufrufer erreicht, gibt es für den Weg nicht, den
        das Produkt wirklich geht.*
    """
    def fuehre_render(*, knoten: Knoten, eingaben: list[dict], out_dir: Path) -> dict:
        if not eingaben:
            return {"status": STATUS_FEHLER,
                    "error": "Render ohne Vorgänger — keine Tiefenkarte."}
        multipass = eingaben[0]
        depth_png = multipass.get("depth_png")
        if not depth_png:
            return {"status": STATUS_FEHLER,
                    "error": (
                        f"Vorgänger lieferte kein 'depth_png'. Grund des Vorgängers: "
                        f"{multipass.get('depth_png_fehler') or multipass.get('error') or 'nicht genannt'}. "
                        f"Vorhandene Felder: {sorted(multipass)}")}

        p = knoten.params
        auftrag = render.RenderAuftrag(
            depth_png=depth_png,
            prompt=p["prompt"],
            negativ_prompt=p["negativ_prompt"],
            backbone=p["backbone"],
            seed=p["seed"],
            schritte=p["schritte"],
            controlnet_staerke=p["controlnet_staerke"],
            denoise=p["denoise"],
            beauty_png=multipass.get("beauty_png") if p.get("nutze_beauty", True) else None,
            ausgabe_png=str(out_dir / "bild.png"),
        )
        # LAYER 1, UND ZWAR IMMER. Dieses Bild ist aus dem Modell gerechnet und gegen
        # dessen Tiefenkarte messbar — es ist der Geometrielayer in Person. Das Feld wird
        # auch an ein gescheitertes Ergebnis gehaengt: Welche Schicht gemeint war, bleibt
        # auch dann die Auskunft, wenn die Rechnung nicht durchkam.
        # DER SCHRITTZAEHLER NUR, WENN ES IHN GIBT. Ihn immer als `None` zu uebergeben
        # waere gleichwertig — aber `render.rendere` unterscheidet «kein Zaehler» von
        # «Zaehler, den die Pipeline nicht annimmt», und diese Unterscheidung soll durch
        # unseren Aufruf nicht verschwinden.
        weiter = {"schrittzaehler": schrittzaehler} if schrittzaehler is not None else {}
        return dict(render.rendere(auftrag, modell=modell, _lader=_lader, **weiter),
                    **{FELD_SCHICHT: SCHICHT_GEOMETRIE})

    return fuehre_render


def _fuehre_bildquelle(*, knoten: Knoten, eingaben: list[dict], out_dir: Path) -> dict:
    """Ein Bild von der Platte in den Graphen holen — **die Stelle, an der ein Mensch
    wieder hereinkommt.**

    Zwischen dem erzeugten Bild und dem nächsten Render sitzt niemand, den der Graph
    kennt: Der Architekt öffnet die PNG, zeichnet einen Balkon hinein, speichert. Der
    Graph kann diesen Schritt nicht rechnen — aber er kann sein Ergebnis **lesen**, und
    zwar so, dass eine zweite Zeichnung auch eine zweite Rechnung auslöst
    (``EINGABEDATEIEN``).

    **Die Datei wird kopiert, nicht verwiesen**, und das ist keine Umständlichkeit. Der
    Zwischenspeicher legt Pfade ab, keine Bilder (``graph.ArtefaktCache``). Bliebe hier
    der Originalpfad stehen, zeigte ein alter Cache-Eintrag nach der nächsten Zeichnung
    auf **neuen** Inhalt: Der Schlüssel spräche von der ersten Fassung, die Datei
    enthielte die zweite. Genau der Fehler, den ``_arbeitsverzeichnis`` für alle anderen
    Stufen schon verhindert — die Kopie liegt im hashbenannten Ordner und ändert sich
    nicht mehr.

    Geprüft wird mit ``bildlesen.pruefe_png``: Signatur und Blockprüfsummen, ohne das
    Bild zu entpacken. Das kostet fast nichts und fängt die umbenannte JPG ebenso wie die
    halb geschriebene Datei — hier, wo der Dateiname steht, und nicht drei Stufen später
    in der Bildbibliothek, wo die Meldung die Datei gar nicht mehr nennt.
    """
    quelle = knoten.params.get("bild_png")
    if not quelle:
        return {"status": STATUS_FEHLER,
                "error": ("Der Bildquellen-Knoten hat keinen Parameter 'bild_png'. Ohne "
                          "Dateinamen gibt es nichts zu lesen.")}

    befund = bildlesen.pruefe_png(quelle)
    if not befund["lesbar"]:
        return {"status": STATUS_FEHLER, "error": befund["grund"],
                "groesse_byte": befund["groesse_byte"]}

    ziel = out_dir / "eingang.png"
    try:
        shutil.copyfile(quelle, ziel)
    except OSError as fehler:
        return {"status": STATUS_FEHLER,
                "error": (f"Das Bild liess sich nicht in den Arbeitsordner kopieren: "
                          f"{type(fehler).__name__}: {fehler}")}

    return {
        "status": STATUS_OK,
        "bild_png": str(ziel),
        # ABSICHTLICH NICHT ``herkunft_path``: Felder auf ``_path`` werden beim
        # Cache-Treffer auf Existenz geprüft (``_fehlende_ausgabedateien``). Ein gültiger
        # Eintrag verfiele dann, sobald jemand seine Zeichnung aufräumt — obwohl die
        # Kopie im Arbeitsordner unverändert daliegt. Die Herkunft ist eine Notiz für
        # Menschen, keine Zusage über eine Datei.
        "herkunft": str(quelle),
        "groesse_byte": befund["groesse_byte"],
        # HIER ENTSTEHT DER VORBEHALT. Eine Datei von der Platte ist nicht aus dieser
        # Rechnung — was zwischen dem letzten Lauf und jetzt damit geschehen ist, weiss
        # niemand hier. Ob jemand wirklich gezeichnet hat, ist damit NICHT gesagt; gesagt
        # ist nur, dass es niemand ausschliessen kann. Für ein Urteil über die
        # Geometrietreue ist das dasselbe.
        FELD_HANDEINGRIFF: True,
        # UND DAMIT IST DIESES BILD STUFE ZWEI. Eine Datei von der Platte ist nicht gegen
        # die Tiefenkarte dieses Laufs gerechnet worden — sie ist pixelbasiert entstanden,
        # irgendwo zwischen dem letzten Lauf und jetzt. Der AI-Imaging-Layer faengt hier
        # an, und er faengt genau hier an und keine Stufe frueher.
        FELD_SCHICHT: SCHICHT_AI_IMAGING,
        "error": None,
    }


def nachrender_ausfuehrer(*, modell=None, _lader=None) -> Callable[..., dict]:
    """Baut die Nachrender-Stufe: **rechnen auf einem Bild, das schon da ist.**

    Der Unterschied zu ``render_ausfuehrer`` ist genau ein Slot. Dort kommt das
    Ausgangsbild aus dem Multipass (der Beauty-Pass aus Blender, und nur er); hier kommt
    es aus Slot 1 und darf von überall stammen — aus einem früheren Render, aus einem
    weiteren Nachrender, oder aus einer Datei, in die ein Mensch hineingezeichnet hat.

    Die Tiefenkarte bleibt Pflicht, und das ist eine Entscheidung und kein Rest:
    ``render.RenderAuftrag`` verlangt sie (``depth_png`` ohne Vorgabewert), weil ohne
    Konditionierung das Modell die Kubatur erfindet — der Fall, gegen den dieses Projekt
    antritt. Für das Hineinskizzieren ist das **richtig**: Der Strich soll in derselben
    Geometrie landen, in der das Bild entstanden ist. Für eine reine Bildbearbeitung ohne
    Geometrie ist es eine **Grenze**, und sie ist oben im Modulkopf benannt.

    ``bildeingang_lage`` wird mitgemeldet, nicht geprüft: Ob das Ausgangsbild beim Modell
    **ankommt**, entscheidet die geladene Pipeline (siehe die Funktion). Ein Riegel wäre
    hier falsch — wir wüssten ihn nur für einen einzigen Backbone zu setzen, und ein
    Riegel auf ungemessener Grundlage sperrt irgendwann das Richtige.
    """
    def fuehre_nachrender(*, knoten: Knoten, eingaben: list[dict], out_dir: Path) -> dict:
        if len(eingaben) < 2:
            return {"status": STATUS_FEHLER,
                    "error": ("Der Nachrender braucht zwei Eingänge: Slot 0 Multipass "
                              "(Tiefenkarte als Konditionierung), Slot 1 ein Bild "
                              "('bild_png') als Ausgangsbild. Ohne Slot 1 wäre er ein "
                              "gewöhnlicher Render — und der heisst 'render'.")}
        multipass, bildeingang = eingaben[0], eingaben[1]

        depth_png = multipass.get("depth_png")
        if not depth_png:
            return {"status": STATUS_FEHLER,
                    "error": (f"Slot 0 lieferte kein 'depth_png'. Grund des Vorgängers: "
                              f"{multipass.get('depth_png_fehler') or multipass.get('error') or 'nicht genannt'}. "
                              f"Vorhandene Felder: {sorted(multipass)}")}

        ausgangsbild = bildeingang.get("bild_png")
        if not ausgangsbild:
            return {"status": STATUS_FEHLER,
                    "error": (f"Slot 1 lieferte kein 'bild_png' — es gibt also kein "
                              f"Ausgangsbild, auf dem weitergerechnet werden könnte. "
                              f"Grund des Vorgängers: "
                              f"{bildeingang.get('error') or 'nicht genannt'}. "
                              f"Vorhandene Felder: {sorted(bildeingang)}")}

        p = knoten.params
        auftrag = render.RenderAuftrag(
            depth_png=depth_png,
            prompt=p["prompt"],
            negativ_prompt=p["negativ_prompt"],
            backbone=p["backbone"],
            seed=p["seed"],
            schritte=p["schritte"],
            controlnet_staerke=p["controlnet_staerke"],
            # DIESE ZWEI ZEILEN SIND DER GANZE BILD-EINGANG. `denoise` bestimmt, wieviel
            # vom Ausgangsbild überlebt; `beauty_png` IST das Ausgangsbild. Ohne die
            # zweite Zeile wäre dieser Knoten ein zweiter Text-zu-Bild-Lauf, der nur so
            # aussieht, als hätte er das Bild gesehen.
            denoise=p["denoise"],
            beauty_png=ausgangsbild,
            ausgabe_png=str(out_dir / "bild.png"),
        )
        ergebnis = render.rendere(auftrag, modell=modell, _lader=_lader)
        lage = bildeingang_lage(p["backbone"])
        # DER VORBEHALT WIRD VERERBT, und zwar aus dem Bildeingang. Ein Nachrender auf
        # einem unberührten Render trägt ihn nicht; einer auf einer Bildquelle oder auf
        # einem weiteren Nachrender trägt ihn. So wandert er genau so weit, wie der
        # Handeingriff reicht — und nicht weiter.
        handeingriff = bool(bildeingang.get(FELD_HANDEINGRIFF))
        # WELCHE SCHICHT DIESE RUNDE IST — und sie folgt aus dem Eingang, nicht aus einer
        # Ansage. Ein Nachrender auf einem unberuehrten Render rechnet weiter gegen
        # dieselbe Tiefenkarte: Sein Bild ist gegen sie messbar, also Layer 1. Ein
        # Nachrender auf einer Bildquelle oder auf einer weiteren Layer-2-Runde rechnet
        # auf Pixeln, die niemand mehr gegen das Modell halten kann: Layer 2.
        #
        # Die Schicht wird aus dem Eingang GELESEN und nicht vom Aufrufer ERKLAERT. Eine
        # erklaerte Schicht waere eine Behauptung, die kein Lauf widerlegen kann.
        schicht = SCHICHT_AI_IMAGING if handeingriff else SCHICHT_GEOMETRIE
        return dict(ergebnis, ausgangsbild=ausgangsbild, bildeingang_lage=lage,
                    **{FELD_HANDEINGRIFF: handeingriff, FELD_SCHICHT: schicht})

    return fuehre_nachrender


def bildeingang_lage(backbone_name: str) -> dict:
    """Kommt das Ausgangsbild auf diesem Backbone **beim Modell an**?

    Die Frage sieht überflüssig aus und ist sie nicht. ``render._pipeline_adapter``
    übergibt die Tiefenkarte als ``control_image`` und das Ausgangsbild als ``image`` —
    aber **nur, wenn die Pipeline beide Eingänge hat.** Kennt sie kein ``control_image``,
    bekommt die Tiefenkarte den einen vorhandenen Bildeingang, und das Ausgangsbild fällt
    weg (``render.py``, Zweig ``if "control_image" in verworfen``). Der Lauf gelingt,
    das Bild ist da, und vom Hineingezeichneten ist nichts übrig.

    Returns:
        ``{backbone, konditionierung, traegt, grund, beleg}``.

        ``traegt`` ist ``False`` oder ``None``. **``None`` heisst NICHT GEMESSEN** —
        weder bestanden noch durchgefallen. ``True`` steht hier für **keinen** Backbone,
        und das ist kein Versehen: Es gäbe erst nach einem Lauf an echten Gewichten etwas
        zu behaupten, und hier gibt es weder GPU noch Gewichte.

    Der einzige gemessene Fall ist ``qwen-image-edit-2511``: ``auf-20260818-09`` hat am
    Gerät belegt, dass ``QwenImageEditPlusPipeline`` weder ``control_image`` noch
    ``strength`` kennt (siehe ``backbone.py``, Eintrag qwen). Dort fällt das Ausgangsbild
    nachweislich weg — ausgerechnet auf dem Backbone, dessen Konditionierungsart
    «integriertes Edit» heisst.
    """
    try:
        eintrag = backbone.hole(backbone_name)
    except backbone.BackboneError as fehler:
        return {"backbone": backbone_name, "konditionierung": None, "traegt": None,
                "grund": str(fehler),
                "beleg": "kein Registry-Eintrag — über diesen Namen ist nichts bekannt"}

    if eintrag.name == "qwen-image-edit-2511":
        return {
            "backbone": eintrag.name, "konditionierung": eintrag.konditionierung,
            "traegt": False,
            "grund": ("Diese Pipeline hat genau einen Bildeingang, und den bekommt die "
                      "Tiefenkarte. Das Ausgangsbild wird überschrieben — das "
                      "Hineingezeichnete erreicht das Modell nicht."),
            "beleg": "auf-20260818-09, am Gerät gemessen (siehe backbone.py, Eintrag qwen)",
        }

    if eintrag.konditionierung == backbone.KOND_INTEGRIERTES_EDIT:
        return {
            "backbone": eintrag.name, "konditionierung": eintrag.konditionierung,
            "traegt": None,
            "grund": ("Nicht gemessen. Diese Konditionierungsart hat typischerweise einen "
                      "einzigen Bildeingang; hat diese Pipeline keinen eigenen "
                      "Steuereingang, überschreibt die Tiefenkarte das Ausgangsbild — so "
                      "wie bei qwen-image-edit-2511 gemessen."),
            "beleg": "NICHT GEMESSEN — braucht einen Lauf an echten Gewichten",
        }

    return {
        "backbone": eintrag.name, "konditionierung": eintrag.konditionierung,
        "traegt": None,
        "grund": ("Nicht gemessen. Eine ControlNet-Pipeline hat einen eigenen "
                  "Steuereingang für die Tiefenkarte; ob sie daneben ein Ausgangsbild "
                  "annimmt, hängt daran, ob es die img2img-Fassung ist. Der Adapter "
                  "meldet es nach dem Lauf in den Hinweisen."),
        "beleg": "NICHT GEMESSEN — braucht einen Lauf an echten Gewichten",
    }


def qa_ausfuehrer(*, modell=None, _lader=None) -> Callable[..., dict]:
    """Baut die QA-Stufe — Soll aus dem Multipass, Ist aus dem erzeugten Bild.

    Der Bogen schliesst sich hier: ``bildlesen.tiefen_aus_report`` liefert das Soll in
    Metern, ``tiefenschaetzer.qa_gegen_soll`` schätzt das Ist aus dem Bild, markiert
    dessen Hintergrund und lässt ``geometrie_qa.geometrie_gate`` urteilen. Die Naht
    ``modell=`` wird wie beim Render von aussen gebunden (siehe ``render_ausfuehrer``);
    ohne Injektion lädt der Schätzer selbst und braucht Gewichte.

    **Ein nicht bestandenes Gate ist kein gescheiterter Knoten.** Der Knoten hat gerechnet
    und ein Urteil geliefert; dass das Urteil „durchgefallen" lautet, ist sein Ergebnis
    und nicht sein Fehlschlag. Würde daraus ``status='fehler'``, verschwände das Urteil
    hinter einem Skip — und ausgerechnet der interessanteste Fall des Projekts, die
    erkannte Halluzination, wäre nicht mehr als Messwert lesbar. ``qa_gegen_soll`` hält es
    genauso: ``status`` beschreibt die Messung, ``bestanden`` das Urteil.

    ``breite`` und ``hoehe`` aus dem Soll werden mitgegeben, damit eine Ist-Karte anderer
    Grösse **auffällt**. Ohne diesen Abgleich verglichen sich zwei Karten punktweise, die
    verschiedene Bildausschnitte zeigen — und das Ergebnis sähe wie eine Messung aus.
    """
    def fuehre_qa(*, knoten: Knoten, eingaben: list[dict], out_dir: Path) -> dict:
        if len(eingaben) < 2:
            return {"status": STATUS_FEHLER,
                    "error": ("QA braucht zwei Eingänge: Slot 0 Multipass (Soll), "
                              "Slot 1 Render (Ist).")}
        multipass, render_ergebnis = eingaben[0], eingaben[1]
        bild_png = render_ergebnis.get("bild_png")
        if not bild_png:
            return {"status": STATUS_FEHLER,
                    "error": f"Vorgänger lieferte kein 'bild_png': {sorted(render_ergebnis)}"}

        # ── Hat ein Mensch das Bild angefasst? ───────────────────────────────────────
        #
        # OWNER-ENTSCHEID 19.09.2026, und er ist die dritte Antwort, angewandt auf den
        # Handeingriff. Zeichnet jemand einen Balkon hinein, den das Modell nicht hat,
        # misst diese Stufe genau die Abweichung, die der Mensch ABSICHTLICH erzeugt hat.
        # Sie fiele durch — zu Recht und zugleich sinnlos.
        #
        # Gewählt wurde weder «wie bisher prüfen» (dann fällt jedes bearbeitete Bild
        # durch, und eine Warnung, die immer kommt, wird nicht gelesen) noch «gar nicht
        # prüfen» (dann trägt das Bild keine Auskunft, und später sieht ihm niemand an, ob
        # es je geprüft war), sondern: **Die Prüfung läuft nicht, und das Urteil lautet
        # NICHT ANWENDBAR.**
        #
        # `bestanden` ist `None` — weder bestanden noch durchgefallen, wie überall in
        # diesem Projekt. `status` ist AUSDRÜCKLICH NICHT `fehler`: Es ist nichts
        # schiefgegangen, und ein Fehlerstatus liesse den Knoten übersprungen aussehen.
        #
        # Und die Messung wird gar nicht erst gefahren: Eine Zahl, die niemand deuten
        # darf, ist keine Auskunft, sondern eine Einladung, sie doch zu deuten.
        if render_ergebnis.get(FELD_HANDEINGRIFF):
            return {
                "status": STATUS_OK,
                "bestanden": None,
                "nicht_anwendbar": True,
                "grund": (
                    "NICHT ANWENDBAR: An diesem Bild wurde von Hand gearbeitet. Die "
                    "Geometrie-Prüfung vergleicht ein Bild mit der Tiefenkarte des "
                    "Modells — was jemand hineingezeichnet hat, steht dort nicht, und "
                    "die Abweichung wäre genau das, was er wollte. Das Urteil ist darum "
                    "weder bestanden noch durchgefallen: Die Frage «folgt dieses Bild dem "
                    "Modell?» ist für dieses Bild nicht mehr die richtige. Das Urteil "
                    "über die Geometrie DARUNTER steht davon unberührt im Feld 'basis' — "
                    "es ist das Urteil der Basis und ausdrücklich nicht das dieses Bildes."
                ),
                "bild_png": bild_png,
                "handeingriff": True,
                # WELCHE SCHICHT GEPRÜFT WURDE. Bewusst nicht ``schicht``: Dieser Knoten
                # ist kein Bild, und ein gleichnamiges Feld auf Bild und Urteil wäre die
                # erste Stelle, an der jemand das eine für das andere hält.
                "beurteilte_schicht": SCHICHT_AI_IMAGING,
                # DAS URTEIL DER BASIS, DURCHGEREICHT — nie selbst gefällt. Was hier
                # ankommt, hat das beurteilte Bild mitgebracht; gefüllt wird es im Lauf
                # (siehe ``schichtbefund``), weil nur dort beide Zweige des Graphen
                # sichtbar sind. ``None`` heisst: Über eine Basis ist hier nichts bekannt.
                FELD_BASIS: render_ergebnis.get(FELD_BASIS),
                "error": None,
            }

        p = knoten.params
        # Lizenz zuerst, vor dem Lesen der EXR: Regel 1 ist die bindendste und billigste
        # Prüfung, und ein Lauf mit einem Non-Commercial-Schätzer soll an der Lizenz
        # scheitern und nicht zufällig erst an einer fehlenden Datei. Dieselbe Reihenfolge
        # wie in ``render.pruefe_auftrag``.
        tiefenschaetzer.fordere_zulaessigen(p["schaetzer"])

        soll, breite, hoehe = bildlesen.tiefen_aus_report(multipass)
        # DIE MASKE AUS DEMSELBEN MULTIPASS — bis zum 26.08.2026 reichte dieser Knoten
        # keine herein, und damit blieben `rho_maske`, Kante und Paarurteil in jedem
        # Kettenlauf ungemessen. Das sind die Masse, die die ABWESENHEIT eines Bauwerks
        # fangen; der Score ueber das ganze Bild fangt sie nicht (ein leeres Grundstueck
        # erreichte dort 0.9530 und bestand das Tor, `auf-20260821-26`).
        #
        # Ein Fehlschlag beim Maskenbau haelt den Knoten NICHT auf — `maske_aus_bericht`
        # gibt dann eine benannte Luecke zurueck, und `qa_gegen_soll` meldet den fehlenden
        # Maskenweg von sich aus. Ein Lauf ohne Bild waere teurer als eine ungemessene
        # Zusatzfrage.
        maskenbefund = maske.maske_aus_bericht(
            multipass, gelaende_erwartet=p.get("gelaende_erwartet", True))
        # DER GRUND MUSS MIT — sonst ist «kein Maskenweg» eine Meldung ohne Antwort.
        # Genau das hat die HomeStation am 26.08.2026 beanstandet: Der Grund stand im
        # Maskenbefund je Kamera, also in einer Datei, die man aufschlagen muss, waehrend
        # oben auf dem Schirm ein Score steht. Die Maske selbst bleibt draussen: Sie ist
        # eine lange Folge von Wahrheitswerten und gehoert nicht in ein Knotenergebnis.
        ohne_maske = {k: v for k, v in maskenbefund.items() if k != "maske"}
        urteil = tiefenschaetzer.qa_gegen_soll(
            bild_png, soll,
            schaetzer=p["schaetzer"], modell=modell, _lader=_lader,
            schwelle=p["schwelle"], hintergrund=p.get("hintergrund"),
            hintergrund_strategie=p["hintergrund_strategie"],
            hintergrund_anteil=p.get("hintergrund_anteil"),
            breite=breite, hoehe=hoehe,
            maske=maskenbefund.get("maske"),
        )
        # `bestanden` aus `urteil` ist und bleibt das EIGENE Urteil dieses Bildes.
        # Daneben steht die Basis — bei einem Layer-1-Bild üblicherweise `None`, denn es
        # IST die Basis und hat keine unter sich.
        return dict(urteil, maskenbefund=ohne_maske,
                    beurteilte_schicht=SCHICHT_GEOMETRIE,
                    **{FELD_BASIS: render_ergebnis.get(FELD_BASIS)})

    return fuehre_qa


#: Knotenart → Ausführerfunktion. **Die Test-Naht dieses Moduls.**
#:
#: Dieselbe Bauform wie ``_starte`` in ``seams.py`` und ``modell`` in ``render.py``: Die
#: Ablaufsteuerung kennt keine einzige Fremdabhängigkeit, sie ruft nur, was in dieser
#: Tabelle steht. Mit Attrappen läuft die ganze Kette ohne Blender, ohne ``.venv-ifc``,
#: ohne GPU und ohne ein einziges Gewicht durch — und genau das macht den Nachweis über
#: den Zwischenspeicher überhaupt erst führbar: Man kann die Aufrufe zählen.
AUSFUEHRER: dict[str, Callable[..., dict]] = {
    ART_GEOMETRIE: _fuehre_geometrie,
    ART_MULTIPASS: _fuehre_multipass,
    ART_RENDER: render_ausfuehrer(),
    ART_QA: qa_ausfuehrer(),
    ART_BILDQUELLE: _fuehre_bildquelle,
    ART_NACHRENDER: nachrender_ausfuehrer(),
}


# --------------------------------------------------------------------------------------
# Lauf
# --------------------------------------------------------------------------------------

def standard_out_dir() -> Path:
    """Wo Knotenausgaben landen, solange nichts anderes gesagt ist.

    Unter ``/tmp``, aus demselben Grund wie ``werkzeuge.job_verzeichnis``: Die Pfad-
    Sandbox des Ökosystems verlangt ``$HOME`` oder ``/tmp``, und ``/tmp`` ist die
    zurückhaltendere Wahl.
    """
    return Path(tempfile.gettempdir()) / "aiimaging-kette"


def _arbeitsverzeichnis(out_dir: Path, art: str, schluessel: str) -> Path:
    """Ein Verzeichnis je Knoten **und Hash**: ``<out_dir>/<art>-<hash[:16]>``.

    Das ist keine Kosmetik, sondern die Bedingung dafür, dass der Cache nicht lügt. Der
    Cache speichert Pfade, nicht Bilder (``graph.ArtefaktCache``). Schrieben zwei Läufe
    derselben Stufe in denselben Ordner, zeigte ein alter Eintrag nach dem zweiten Lauf
    auf **neuen** Inhalt — der Schlüssel spräche von Lauf A, die Datei enthielte Lauf B.
    Ein Cache, der falsche Treffer liefert, ist schlimmer als keiner: Der Fehler taucht
    erst im fertigen Bild auf.

    16 Hexzeichen sind 64 Bit; für ein paar tausend Einträge ist das reichlich, und der
    Ordnername bleibt lesbar. Der Cache-Schlüssel selbst bleibt der volle Hash.
    """
    return out_dir / f"{_UNSICHER.sub('_', art)}-{schluessel[:16]}"


def _knoten_hash(knoten: Knoten, vorgaenger_hashes: list[str]) -> str:
    """Der Inhalts-Hash eines Knotens — Schlüssel des Zwischenspeichers.

    Er entsteht aus Art, Parametern, den Hashes der Vorgänger und dem **Inhalt** der
    Eingabedateien (``EINGABEDATEIEN``). Nicht aus Pfaden, nicht aus Zeitstempeln: Eine
    umbenannte, inhaltlich gleiche IFC soll denselben Hash ergeben, eine neu geschriebene
    und inhaltlich andere unter gleichem Namen einen anderen.

    Diese Funktion war bis Sitzung 07 eine eigene Hashvorbereitung: Sie baute einen
    Zweitknoten, in dem die Pfadparameter durch eine Marke ersetzt waren, weil
    ``graph.inhalts_hash`` die Parameter vollständig einrechnete und der Schlüssel sonst
    am Dateinamen hinge — ein verschobener Projektordner verwürfe den ganzen
    Zwischenspeicher. Die Ausnahmeliste steht jetzt im Kern (``param_dateien``), wo sie
    hingehört; hier bleibt nur noch, **welche** Parameter Pfade sind. Das weiss die
    Bildkette, nicht der Ablaufkern.

    Die Hashes sind dieselben wie vorher — die Marke und die Reihenfolge der gehashten
    Dateien haben sich nicht geändert. Ein bestehender Zwischenspeicher bleibt gültig.
    """
    return inhalts_hash(knoten, vorgaenger_hashes,
                        param_dateien=EINGABEDATEIEN.get(knoten.art, ()))


def _fehlende_ausgabedateien(ausgaben: dict) -> list[str]:
    """Welche Dateien, die ein Cache-Eintrag verspricht, es nicht mehr gibt.

    Ein Treffer im Zwischenspeicher ist nur so viel wert wie die Dateien, auf die er
    zeigt. Sie liegen ausserhalb des Caches (bewusst — sonst gäbe es zwei Orte der
    Wahrheit), also kann sie jemand gelöscht haben: ein aufgeräumtes ``/tmp``, ein
    ``rm -rf`` auf dem Ausgabeordner. Dann ist der Eintrag kein Treffer, sondern eine
    Zusage ins Leere; die Stufe rechnet neu.

    Umgekehrt gilt weiter, was dieses Projekt mehrfach bezahlt hat: Die Existenz einer
    Datei ist kein Beleg für ihren Inhalt. Deshalb ist die Existenzprüfung hier auch nur
    eine **Verwerfungs**-Bedingung — der Beleg für den Inhalt kommt aus dem Hash und aus
    dem Arbeitsverzeichnis, das an ihm hängt.

    Diese Funktion errät Dateifelder an der Endung und ist seit Sitzung 07 nur noch das
    erste von zwei Netzen; das zweite zählt sie auf (``BEDARF``). Sie bleibt, weil sie
    auch fängt, was keine Art deklariert hat — siehe ``_cache_maengel``.
    """
    fehlt = []
    for feld, wert in sorted(ausgaben.items()):
        if not isinstance(wert, str) or not wert:
            continue
        if not feld.endswith(_DATEIFELD_ENDUNGEN):
            continue
        if not Path(wert).exists():
            fehlt.append(feld)
    return fehlt


def _cache_maengel(art: str, ausgaben: dict, bedarf: dict[str, Bedarf]) -> list[str]:
    """Warum ein gefundener Eintrag **kein** Treffer ist. Leer heisst: brauchbar.

    Zwei Netze übereinander, und das ist Absicht:

    * ``_fehlende_ausgabedateien`` errät Dateifelder an der Endung. Es fängt auch, was
      keine Art deklariert hat — dafür fängt es nur, was als nicht-leerer Text dasteht.
    * ``BEDARF`` zählt die Felder auf. Es fängt genau das, wo das erste Netz reisst: ein
      **leeres** Pflichtfeld. In Sitzung 07 war das ``depth_png = None`` — der Eintrag
      galt als Treffer, die teure Stufe wurde nie wieder gerechnet, und die Kette
      scheiterte für immer eine Stufe später mit einer Meldung, die auf den falschen
      Knoten zeigte.

    Ein Netz allein wäre kürzer; das zweite kostet drei Zeilen und hat den bisher
    teuersten Fehler dieses Projekts gefangen.
    """
    fehlende = _fehlende_ausgabedateien(ausgaben)
    maengel = [f"Datei zum Feld {feld!r} fehlt." for feld in fehlende]
    eigen = bedarf.get(art)
    if eigen is not None:
        # Doppelmeldungen werden in Kauf genommen: Bei einer fehlenden Datei sagen beide
        # Netze dasselbe. Das ist der Preis dafür, dass keines vom anderen abhängt.
        maengel.extend(eigen.maengel(ausgaben))
    return maengel


def _knoteneintrag(
    art: str, status: str, *, aus_cache: bool, dauer_s: float,
    dauer_s_original: float | None = None, hash: str | None = None,
    arbeits_dir: str | None = None, ausgaben: dict | None = None,
    error: str | None = None, grund: str | None = None,
    cache_fehler: str | None = None,
) -> dict:
    """Ein Knotenergebnis in immer derselben Gestalt.

    Alle Felder immer, auch wenn sie leer sind — wer einen Lauf auswertet, soll nicht bei
    jedem Zugriff ``.get`` mit Vorgabewert schreiben müssen, und ein fehlendes Feld soll
    nicht wie ein anderer Fall aussehen als ein leeres.

    Zu den zwei Dauern: ``dauer_s`` ist die Zeit, die **dieser Lauf** an diesem Knoten
    verbracht hat (bei einem Cache-Treffer nahe null). ``dauer_s_original`` ist die Zeit,
    die die gespeicherte Rechnung gekostet hat. Erst die zweite Zahl macht sichtbar, was
    der Zwischenspeicher wert ist; die erste allein sagte nur, dass es schnell ging.
    """
    return {
        "art": art,
        "status": status,
        "aus_cache": aus_cache,
        "dauer_s": round(float(dauer_s), 4),
        "dauer_s_original": (None if dauer_s_original is None
                             else round(float(dauer_s_original), 4)),
        "hash": hash,
        "arbeits_dir": arbeits_dir,
        "ausgaben": ausgaben if ausgaben is not None else {},
        "error": error,
        "grund": grund,
        "cache_fehler": cache_fehler,
    }


def pruefe_kette(graph: Graph, *, bedarf: dict[str, Bedarf] | None = None) -> list[dict]:
    """Einen Ketten-Graphen prüfen, **ohne ihn auszuführen**.

    Das Gegenstück zu KosmoOrbits ``pipelineReadiness`` für den inneren Graphen (siehe
    ``BEDARF``). Gemeldet wird, was sich vor dem Rechnen sagen lässt: ein Knoten, dem ein
    Eingang fehlt, und eine Kante, die das erwartete Feld nicht trägt.

    Args:
        graph: der zu prüfende Graph, üblicherweise aus ``baue_kette``.
        bedarf: Knotenart → ``Bedarf``. ``None`` nimmt ``BEDARF``.

    Returns:
        Liste von Befunden ``{knoten, art, befund, schwere, detail}``. **Leer heisst
        verdrahtet.** Die Gestalt ist dieselbe wie bei
        ``mcp_schemas.pruefe_verdrahtbarkeit``, damit beide Ebenen gleich gelesen werden.

    Der Nutzen liegt in der Reihenfolge, nicht im Befund: Ein von Hand geschriebener oder
    aus JSON gelesener Graph soll seine Verdrahtungsfehler melden, bevor Blender startet
    — nicht nach der teuersten Stufe.
    """
    return pruefe_bedarf(graph, BEDARF if bedarf is None else bedarf)


# --------------------------------------------------------------------------------------
# Die zweite Schicht: welches Bild steht worauf — und welches Urteil gehoert wem
# --------------------------------------------------------------------------------------
#
# OWNER-ENTSCHEID 19.09.2026. Ein Layer-2-Bild traegt kein eigenes Geometrie-Urteil, wohl
# aber das seiner Basis. Das ist mehr, als ein einzelner Knoten wissen kann, und darum
# steht es hier und nicht in einer Ausfuehrerfunktion:
#
# * Ein Knoten sieht seine Vorgaenger. Das Urteil ueber sein Ausgangsbild faellt aber ein
#   QA-Knoten im NEBENZWEIG — der haengt am selben Render, nicht an ihm. Ein Knoten kann
#   es also gar nicht wissen, und was er nicht wissen kann, soll er nicht behaupten.
# * Ein Urteil aus dem Zwischenspeicher waere ein Urteil aus einem ANDEREN LAUF. Der Hash
#   eines Nachrenders enthaelt die Parameter der QA nicht; ein mitgespeichertes Basisurteil
#   ueberdauerte damit eine geaenderte Schwelle, ohne dass es jemandem auffiele. Deshalb
#   wird der Basis-Block NIE mitgespeichert, sondern nach jedem Lauf frisch gelesen.
#
# Gelesen wird aus dem Graphen und aus den Ergebnissen desselben Laufs — nie aus einer
# Angabe des Aufrufers. Eine erklaerte Basis waere eine Behauptung, die kein Lauf
# widerlegen kann.


def _ist_bildart(art: str) -> bool:
    """Bringt diese Knotenart ein Bild hervor? Nur solche Knoten haben eine Schicht."""
    return art in (ART_RENDER, ART_BILDQUELLE, ART_NACHRENDER)


def _ausgaben_von(knoten_ergebnisse: dict, kid: str) -> dict:
    """Die Ausgaben eines Knotens aus einem Laufergebnis — leer, wenn es sie nicht gibt."""
    eintrag = knoten_ergebnisse.get(kid) or {}
    return eintrag.get("ausgaben") or {}


def schicht_von(art: str, ausgaben: dict) -> str:
    """Welche Schicht ein Bildergebnis ist: :data:`SCHICHT_GEOMETRIE` oder
    :data:`SCHICHT_AI_IMAGING`.

    Zuerst wird gelesen, was der Knoten selbst gesagt hat (:data:`FELD_SCHICHT`). Der
    Rueckfall darunter ist kein Schoenheitsfehler, sondern der Grund, warum diese Funktion
    ueberhaupt eine ist: **Eintraege im Zwischenspeicher, die vor dem 19.09.2026 entstanden
    sind, tragen das Feld nicht.** Ohne Rueckfall sagte ein Cache-Treffer «keine Schicht»,
    und ein bearbeitetes Bild saehe nach einem Neustart aus wie ein gerechnetes.

    Der Rueckfall liest denselben Sachverhalt aus dem, was es damals schon gab: die
    Bildquelle ist immer Stufe zwei, und sonst entscheidet der Handeingriff.
    """
    wert = ausgaben.get(FELD_SCHICHT)
    if wert in (SCHICHT_GEOMETRIE, SCHICHT_AI_IMAGING):
        return wert
    if art == ART_BILDQUELLE:
        return SCHICHT_AI_IMAGING
    return SCHICHT_AI_IMAGING if ausgaben.get(FELD_HANDEINGRIFF) else SCHICHT_GEOMETRIE


def _schicht_im_graphen(graph: Graph, knoten_ergebnisse: dict, kid: str,
                        memo: dict[str, str], pfad: frozenset = frozenset()) -> str:
    """Die Schicht eines Bildknotens — aus seinem Ergebnis, sonst **aus dem Graphen**.

    Warum es beide Wege braucht: Nach einem Lauf steht die Schicht im Knotenergebnis, und
    das ist die verlaesslichste Quelle — sie kommt von der Stufe selbst. Vorher (und bei
    einem Eintrag aus der Zeit vor dem 19.09.2026) steht sie dort nicht, und dann ist sie
    trotzdem bestimmt: Eine Bildquelle ist **immer** Stufe zwei, und ein Nachrender ist,
    was sein Bildeingang ist. Ein Graph kann seine Schichten also nennen, bevor er
    gerechnet hat — derselbe Unterschied zwischen Bau und Lauf wie ueberall hier.

    ``pfad`` schuetzt gegen einen von Hand gebauten Graphen mit Kreis; ``memo`` spart die
    Wiederholung, wenn acht Varianten auf derselben Kette stehen.
    """
    if kid in memo:
        return memo[kid]
    knoten = graph.knoten[kid]
    ausgaben = _ausgaben_von(knoten_ergebnisse, kid)
    if (ausgaben.get(FELD_SCHICHT) in (SCHICHT_GEOMETRIE, SCHICHT_AI_IMAGING)
            or FELD_HANDEINGRIFF in ausgaben):
        wert = schicht_von(knoten.art, ausgaben)
    elif knoten.art == ART_BILDQUELLE:
        wert = SCHICHT_AI_IMAGING
    elif (knoten.art == ART_NACHRENDER and len(knoten.eingaenge) >= 2
          and knoten.eingaenge[1] in graph.knoten
          and _ist_bildart(graph.knoten[knoten.eingaenge[1]].art)
          and knoten.eingaenge[1] not in pfad):
        wert = _schicht_im_graphen(graph, knoten_ergebnisse, knoten.eingaenge[1],
                                   memo, pfad | {kid})
    else:
        wert = schicht_von(knoten.art, ausgaben)
    memo[kid] = wert
    return wert


def _basisblock(*, knoten=None, bild=None, bestanden=None, urteil_von=None,
                herkunft: str = "", grund: str = "") -> dict:
    """Ein Basis-Block in immer derselben Gestalt — alle Felder immer, auch die leeren.

    Dieselbe Linie wie ``_knoteneintrag``: Ein fehlendes Feld soll nicht wie ein anderer
    Fall aussehen als ein leeres. Und der Schluessel fuer das Urteil heisst
    :data:`BASIS_BESTANDEN` und nicht ``bestanden`` — wer den Block versehentlich flach
    zieht, soll kein zweites ``bestanden`` bekommen, das neben dem eigenen steht.
    """
    return {
        BASIS_KNOTEN: knoten,
        BASIS_BILD: bild,
        BASIS_BESTANDEN: bestanden,
        BASIS_URTEIL_VON: urteil_von,
        BASIS_HERKUNFT: herkunft,
        BASIS_GRUND: grund,
    }


def _basis_ueber_bildkette(graph: Graph, knoten_ergebnisse: dict, kid: str,
                           memo: dict[str, str]) -> str | None:
    """Rueckwaerts durch die Bildeingaenge, bis ein Layer-1-Bild kommt. ``None``: keines.

    **Warum die ERSTE Basis gilt und nicht die jeweils vorige** — Layer 2 auf Layer 2 auf
    Layer 2: Die vorige Runde ist selbst Layer 2 und hat darum gar kein eigenes
    Geometrie-Urteil. Wer sie als Basis naehme, reichte ein Urteil weiter, das sie selbst
    nur geerbt hat: Hoerensagen zweiter Ordnung, und mit jeder Runde eine Quelle weiter
    weg. Gemessen wurde genau einmal — an dem letzten Bild, das noch aus dem Modell kam.
    Das ist die Basis, und sie bleibt es, solange weitergerechnet wird.

    Slot 1 ist der Bildeingang des Nachrenders (Slot 0 ist die Tiefenkarte). Die
    Besuchtmenge schuetzt gegen einen von Hand gebauten Graphen mit Kreis: ``fuehre_aus``
    haette so einen zwar schon zurueckgewiesen, aber diese Funktion laeuft auch allein.
    """
    aktuell = kid
    gesehen = {kid}
    while True:
        knoten = graph.knoten.get(aktuell)
        if knoten is None or knoten.art != ART_NACHRENDER or len(knoten.eingaenge) < 2:
            return None
        vor = knoten.eingaenge[1]
        if vor in gesehen or vor not in graph.knoten:
            return None
        gesehen.add(vor)
        art = graph.knoten[vor].art
        if not _ist_bildart(art):
            return None
        if _schicht_im_graphen(graph, knoten_ergebnisse, vor, memo) == SCHICHT_GEOMETRIE:
            return vor
        aktuell = vor


def _geometriequelle(graph: Graph, kid: str) -> str | None:
    """Der Knoten an Slot 0 eines Bildknotens — die Stufe, aus der seine Tiefenkarte kommt."""
    knoten = graph.knoten.get(kid)
    if knoten is None or not knoten.eingaenge:
        return None
    return knoten.eingaenge[0]


def _basis_ueber_geometrie(graph: Graph, knoten_ergebnisse: dict, kid: str,
                           memo: dict[str, str]) -> tuple[str | None, str]:
    """Das Layer-1-Bild, das auf **derselben Geometrie** steht. ``(knoten|None, grund)``.

    Der zweite Weg, und der haeufigere: Wer ein Bild oeffnet, hineinzeichnet und speichert,
    bringt es als ``bildquelle`` zurueck — **von der Platte**, ohne Kante zum Render, aus
    dem es entstanden ist. Die Bildkette reisst an dieser Stelle, und zwar unvermeidlich:
    Was ein Mensch zwischen zwei Laeufen tut, steht in keinem Graphen.

    Was **nicht** reisst, ist die Geometrie. Der Nachrender haengt an Slot 0 an derselben
    Multipass-Stufe wie der Render, dessen Bild geprueft wurde. Ueber die gilt die Aussage,
    um die es geht: *die Geometrie unter diesem Bild ist geprueft.*

    **Und genau so weit geht sie auch.** Dass die Zeichnung aus jenem Render stammt, ist
    hier NICHT bewiesen — beweisbar ist, dass beide auf derselben Tiefenkarte stehen.
    Darum traegt der Block seine :data:`BASIS_HERKUNFT` mit: Wer ihn liest, sieht, worauf
    die Zuordnung beruht, und kann sie bestreiten.

    Mehrdeutig heisst ``None``: Stehen zwei Layer-1-Bilder auf derselben Geometrie, waere
    jede Wahl geraten. Ein geratenes Urteil ist schlimmer als keines.
    """
    quelle = _geometriequelle(graph, kid)
    if quelle is None:
        return None, ("Dieses Bild haengt an keiner Geometriestufe — es gibt nichts, "
                      "worueber sich eine gemeinsame Basis bestimmen liesse.")
    kandidaten = [
        k for k in sorted(graph.knoten)
        if k != kid and _ist_bildart(graph.knoten[k].art)
        and _geometriequelle(graph, k) == quelle
        and _schicht_im_graphen(graph, knoten_ergebnisse, k, memo) == SCHICHT_GEOMETRIE
    ]
    if not kandidaten:
        return None, (f"Auf der Geometrie {quelle!r} steht in diesem Graphen kein "
                      f"Layer-1-Bild — es gibt keine geprueft Basis, auf die sich dieses "
                      f"Bild berufen koennte.")
    if len(kandidaten) > 1:
        return None, (f"Auf der Geometrie {quelle!r} stehen mehrere Layer-1-Bilder "
                      f"({', '.join(kandidaten)}). Welches die Basis ist, waere geraten — "
                      f"und ein geratenes Urteil ist schlimmer als keines.")
    return kandidaten[0], ""


def _urteil_ueber(graph: Graph, knoten_ergebnisse: dict,
                  basis_id: str) -> tuple[object, str | None, str]:
    """Das Geometrie-Urteil ueber ein Layer-1-Bild. ``(bestanden, qa_knoten, grund)``.

    Gesucht wird der QA-Knoten, dessen **Ist-Eingang** (Slot 1) genau dieses Bild ist.
    ``bestanden`` kommt unveraendert aus dessen Ausgaben: ``True``, ``False`` oder
    ``None`` — und ``None`` heisst hier wie ueberall NICHT GEMESSEN, nicht
    durchgefallen.

    **Ein durchgefallenes Basisurteil wird ausdruecklich weitergereicht.** Es ist die
    unangenehmste Auskunft dieses Blocks und die wichtigste: Wer acht Varianten auf einer
    Geometrie rechnet, die die Pruefung nicht bestanden hat, soll das an jeder der acht
    sehen.
    """
    qas = [k for k in sorted(graph.knoten)
           if graph.knoten[k].art == ART_QA
           and len(graph.knoten[k].eingaenge) >= 2
           and graph.knoten[k].eingaenge[1] == basis_id]
    if not qas:
        return None, None, ("Zu diesem Bild gibt es in diesem Graphen keine "
                            "Geometrie-Pruefung. Das Urteil der Basis ist damit NICHT "
                            "GEMESSEN — weder bestanden noch durchgefallen.")

    urteile = []
    for k in qas:
        eintrag = knoten_ergebnisse.get(k) or {}
        if eintrag.get("status", STATUS_OK) != STATUS_OK:
            continue
        ausgaben = eintrag.get("ausgaben") or {}
        if "bestanden" not in ausgaben:
            continue
        urteile.append((k, ausgaben["bestanden"]))
    if not urteile:
        return None, None, (f"Die Pruefung {', '.join(qas)} hat in diesem Lauf kein "
                            f"Urteil geliefert (nicht gelaufen, uebersprungen oder "
                            f"gescheitert). NICHT GEMESSEN.")
    werte = {w for _, w in urteile}
    if len(werte) > 1:
        return None, None, (f"Mehrere Pruefungen urteilen ueber dasselbe Bild und "
                            f"widersprechen sich ({', '.join(k for k, _ in urteile)}). "
                            f"Ein Urteil auszuwaehlen hiesse, das andere zu verschweigen.")
    qa_id, bestanden = urteile[0]
    if bestanden is None:
        return None, qa_id, (f"Die Pruefung {qa_id!r} lief, hat aber kein Urteil "
                             f"gefaellt. NICHT GEMESSEN.")
    return bestanden, qa_id, ""


def schichtbefund(graph: Graph, knoten_ergebnisse: dict | None = None) -> dict[str, dict]:
    """Je Knoten-ID die Felder zur **zweiten Schicht** — zum Nachtragen an die Ausgaben.

    Args:
        graph: der gelaufene (oder nur gebaute) Graph.
        knoten_ergebnisse: die Auswertung je Knoten-ID aus ``fuehre_aus`` (``ergebnis
            ["knoten"]``). ``None`` heisst: nur den Graphen ansehen. Dann steht die
            Schicht schon fest, das Urteil der Basis aber noch nicht — es gibt es erst,
            wenn gerechnet wurde.

    Returns:
        ``{knoten_id: felder}``. Bildknoten bekommen :data:`FELD_SCHICHT` und
        :data:`FELD_BASIS`, QA-Knoten ``beurteilte_schicht`` und :data:`FELD_BASIS`.
        :data:`FELD_BASIS` ist ``None`` fuer ein Layer-1-Bild — **es ist die Basis und hat
        keine unter sich.**

    **Was diese Funktion nie tut: das Feld ``bestanden`` anfassen.** Sie legt daneben,
    nie darueber. Das eigene Urteil eines Knotens bleibt, was sein Ausfuehrer gesagt hat;
    das fremde steht im Block und heisst dort anders.
    """
    ergebnisse = knoten_ergebnisse or {}
    nachtrag: dict[str, dict] = {}
    basen: dict[str, dict | None] = {}
    memo: dict[str, str] = {}

    for kid in sorted(graph.knoten):
        art = graph.knoten[kid].art
        if not _ist_bildart(art):
            continue
        schicht = _schicht_im_graphen(graph, ergebnisse, kid, memo)
        if schicht == SCHICHT_GEOMETRIE:
            # LAYER 1 BEKOMMT KEINEN BASIS-BLOCK, und das ist die Aussage und kein Loch:
            # Er ist selbst die Basis. Ein Block mit lauter None saehe aus wie «Basis
            # vorhanden, nichts gemessen» — etwas ganz anderes.
            basen[kid] = None
            nachtrag[kid] = {FELD_SCHICHT: schicht, FELD_BASIS: None}
            continue

        basis_id = _basis_ueber_bildkette(graph, ergebnisse, kid, memo)
        herkunft, grund = HERKUNFT_BILDKETTE, ""
        if basis_id is None:
            basis_id, grund = _basis_ueber_geometrie(graph, ergebnisse, kid, memo)
            herkunft = HERKUNFT_GEOMETRIE if basis_id is not None else ""

        if basis_id is None:
            block = _basisblock(grund=grund)
        else:
            bestanden, qa_id, urteilsgrund = _urteil_ueber(graph, ergebnisse, basis_id)
            block = _basisblock(
                knoten=basis_id,
                bild=_ausgaben_von(ergebnisse, basis_id).get("bild_png"),
                bestanden=bestanden, urteil_von=qa_id,
                herkunft=herkunft, grund=urteilsgrund)
        basen[kid] = block
        nachtrag[kid] = {FELD_SCHICHT: schicht, FELD_BASIS: block}

    for kid in sorted(graph.knoten):
        knoten = graph.knoten[kid]
        if knoten.art != ART_QA or len(knoten.eingaenge) < 2:
            continue
        beurteilt = knoten.eingaenge[1]
        if beurteilt not in graph.knoten or not _ist_bildart(graph.knoten[beurteilt].art):
            continue
        # DIE BASIS DES URTEILS IST DIE BASIS DES BEURTEILTEN BILDES — der Pruefer erbt
        # sie, er bestimmt sie nicht. Und sein eigenes `bestanden` bleibt unberuehrt:
        # Beide Urteile stehen nebeneinander, unter verschiedenen Namen.
        nachtrag[kid] = {
            "beurteilte_schicht": _schicht_im_graphen(graph, ergebnisse, beurteilt, memo),
            FELD_BASIS: basen.get(beurteilt),
        }
    return nachtrag


def fuehre_aus(
    graph: Graph,
    *,
    cache: ArtefaktCache | None = None,
    ausfuehrer: dict[str, Callable[..., dict]] | None = None,
    out_dir: str | Path | None = None,
    bedarf: dict[str, Bedarf] | None = None,
    pruefe_verdrahtung: bool = False,
    melder: Callable[[dict], None] | None = None,
) -> dict:
    """Einen Ketten-Graphen abarbeiten: topologisch, zwischengespeichert, skip-on-error.

    Args:
        graph: Der Graph, üblicherweise aus ``baue_kette``.
        cache: Zwischenspeicher. ``None`` heisst: kein Speichern und kein Nachsehen —
            jede Stufe rechnet. Sinnvoll für einen Lauf, dessen Ergebnis niemand
            wiederverwenden wird, und für Tests, die genau das prüfen wollen.
        ausfuehrer: Knotenart → Funktion. ``None`` nimmt ``AUSFUEHRER``. Die Tabelle
            **ersetzt** die Vorgabe, sie ergänzt sie nicht: Wer nur eine Stufe austauschen
            will, schreibt ``{**kette.AUSFUEHRER, "render": attrappe}`` und sieht dabei,
            was er sonst noch ruft. Eine stille Ergänzung hiesse, dass ein Test, der eine
            Attrappe vergisst, unbemerkt Blender startet.
        out_dir: Wurzel der Arbeitsverzeichnisse. Vorgabe ``standard_out_dir()``.
        bedarf: Knotenart → ``Bedarf``. ``None`` nimmt ``BEDARF``. Daran hängt, welche
            Felder ein Cache-Eintrag zusagen muss, um als Treffer zu gelten. Eine Art
            ohne Eintrag wird nicht geprüft — dann greift nur die Endungs-Heuristik
            (``_fehlende_ausgabedateien``), wie vor Sitzung 07.
        melder: ``(ereignis: dict) -> None``, gerufen **vor** und **nach** jedem Knoten.
            ``None`` heisst: niemand sieht zu, und es wird nichts gerufen.

            **Wozu es das gibt** (21.09.2026): Ein Lauf über den Graphen dauert Minuten
            und meldete bis dahin *gar nichts*, bis er fertig war. Von aussen sieht ein
            rechnender Lauf dann genauso aus wie ein hängender.

                *Ein Fortschritt, den niemand sieht, sieht aus wie ein Absturz.*

            Die Ereignisse tragen ``art`` (``knoten_beginnt`` / ``knoten_fertig``),
            ``knoten``, ``knotenart``, ``nummer``, ``von`` — und beim Ende zusätzlich
            ``status``, ``aus_cache`` und ``dauer_s``.

            **Ein Fehler im Melder reisst den Lauf nicht mit.** Er wird geschluckt und
            beim nächsten Ereignis wieder versucht: *Ein Rückruf, der die Rechnung
            mitreisst, ist teurer als gar keiner* — die GPU-Zeit ist schon bezahlt.
        pruefe_verdrahtung: ``True`` prüft den Graphen **vor dem ersten Knoten** gegen
            ``bedarf`` und bricht bei einem ``error``-Befund ab. Vorgabe ``False``, weil
            ein Graph mit unbekannten Knotenarten (Attrappen, Versuche) weiterhin laufen
            können soll; wer eine echte Kette rechnet, schaltet es ein und zahlt den
            Verdrahtungsfehler nicht mit GPU-Zeit.

    Returns:
        ``{status, reihenfolge, knoten, dauer_s, out_dir, gerechnet, cache_treffer,
        uebersprungen, gescheitert, error}``.

        ``knoten`` ist die Auswertung je Knoten-ID, jeweils mit ``status``, ``aus_cache``,
        ``dauer_s``, ``dauer_s_original``, ``hash``, ``arbeits_dir``, ``ausgaben``,
        ``error``, ``grund`` und ``cache_fehler``.

    Raises:
        KettenError: ``graph`` ist kein Graph, oder für eine vorkommende Knotenart gibt
            es keine Ausführerfunktion. Beides wird **vor** dem ersten Knoten geprüft:
            Eine halb gelaufene Kette, die in der Mitte an einer fehlenden Zuordnung
            hängenbleibt, hinterlässt Dateien, die zu nichts gehören.
        ZyklusError: der Graph hat keine Rechenreihenfolge (aus ``graph.py``).

    Der Ablauf, und warum er so ist
    -------------------------------
    1. **Reihenfolge** aus ``topologische_reihenfolge`` — bei Gleichrang immer die
       kleinste ID zuerst, damit zwei Läufe dasselbe Protokoll ergeben.
    2. **Hash** aus Parametern, Vorgänger-Hashes und Dateiinhalten. Der Hash ist der
       Cache-Schlüssel *und* der Name des Arbeitsverzeichnisses.
    3. **Nachsehen** im Cache. Treffer heisst: Die Ausführerfunktion wird **gar nicht
       gerufen**. Das ist der ganze Nutzen — nicht „schneller", sondern „nicht".
    4. **Rechnen**, wenn kein Treffer. Gelingt es, wandert das Ergebnis in den Cache.
    5. **Überspringen** aller Nachfolger eines gescheiterten Knotens
       (``graph.nachfolger_transitiv``). Mit halben Eingaben weiterzurechnen erzeugt im
       besten Fall Zeitverlust und im schlechtesten ein plausibel aussehendes Bild auf
       falscher Grundlage.

    **Gescheitertes wird nicht gespeichert.** Ein Fehlschlag sagt meist etwas über die
    Umgebung (Blender fehlt, GPU belegt, Datei weg) und nicht über die Rechnung. Ihn zu
    speichern hiesse, ein behobenes Problem beim nächsten Lauf aus dem Cache erneut zu
    melden — der Cache würde zum Gedächtnis für Pannen.
    """
    if not isinstance(graph, Graph):
        raise KettenError(
            f"fuehre_aus erwartet einen Graph, bekam {type(graph).__name__}. Ein dict "
            f"wird über Graph.from_dict gelesen."
        )
    tabelle = dict(AUSFUEHRER if ausfuehrer is None else ausfuehrer)
    tabelle_bedarf = dict(BEDARF if bedarf is None else bedarf)
    wurzel = Path(out_dir) if out_dir is not None else standard_out_dir()

    if pruefe_verdrahtung:
        # Vor der Reihenfolge: Auch ein Graph mit Kreis soll seine Verdrahtungsfehler
        # nennen, statt sie hinter dem Kreis verschwinden zu lassen.
        schwer = [b for b in pruefe_bedarf(graph, tabelle_bedarf) if b["schwere"] == "error"]
        if schwer:
            raise KettenError(
                "Der Graph ist nicht verdrahtet: "
                + "; ".join(f"{b['knoten']}: {b['detail']}" for b in schwer)
            )

    reihenfolge = graph.topologische_reihenfolge()

    ohne_ausfuehrer = sorted({graph.knoten[kid].art for kid in reihenfolge} - set(tabelle))
    if ohne_ausfuehrer:
        raise KettenError(
            f"Für die Knotenart(en) {ohne_ausfuehrer} gibt es keine Ausführerfunktion. "
            f"Bekannt: {sorted(tabelle)}. Die Zuordnung Art → Code liegt bewusst "
            f"ausserhalb von graph.py; fehlt sie, ist der Graph nicht ausführbar."
        )

    knoten_ergebnisse: dict[str, dict] = {}
    hashes: dict[str, str] = {}
    uebersprungen: dict[str, str] = {}      # Knoten-ID → Grund
    gescheitert: list[str] = []
    beginn_gesamt = time.perf_counter()

    def _melde(ereignis: dict) -> None:
        """Den Melder rufen — und **niemals** daran scheitern. Siehe Docstring."""
        if melder is None:
            return
        try:
            melder(ereignis)
        except Exception:                          # noqa: BLE001 — Absicht, siehe oben
            pass

    for nummer, kid in enumerate(reihenfolge, start=1):
        knoten = graph.knoten[kid]
        _melde({"art": "knoten_beginnt", "knoten": kid, "knotenart": knoten.art,
                "nummer": nummer, "von": len(reihenfolge)})

        try:
            if kid in uebersprungen:
                knoten_ergebnisse[kid] = _knoteneintrag(
                    knoten.art, STATUS_UEBERSPRUNGEN, aus_cache=False, dauer_s=0.0,
                    grund=uebersprungen[kid],
                )
                continue

            vorgaenger = graph.vorgaenger(kid)
            eingaben = [knoten_ergebnisse[v]["ausgaben"] for v in vorgaenger]
            beginn = time.perf_counter()

            try:
                schluessel = _knoten_hash(knoten, [hashes[v] for v in vorgaenger])
            except GraphError as fehler:
                # Häufigster Fall: Die Eingabedatei gibt es nicht. Das ist ein Fehler dieses
                # Knotens und kein Grund, den ganzen Lauf abzubrechen — die Kette meldet ihn
                # wie jeden anderen und überspringt, was dahinter hängt.
                knoten_ergebnisse[kid] = _knoteneintrag(
                    knoten.art, STATUS_FEHLER, aus_cache=False,
                    dauer_s=time.perf_counter() - beginn,
                    error=f"Hash nicht bildbar: {fehler}",
                )
                gescheitert.append(kid)
                for nachfolger in graph.nachfolger_transitiv([kid]):
                    uebersprungen.setdefault(nachfolger, f"Vorgänger {kid!r} ist gescheitert.")
                continue

            hashes[kid] = schluessel
            arbeit = _arbeitsverzeichnis(wurzel, knoten.art, schluessel)

            # --- 1) Nachsehen ------------------------------------------------------------
            lese_fehler = None
            try:
                eintrag = cache.hole(schluessel) if cache is not None else None
            except GraphError as fehler:
                # Ein unlesbarer Eintrag ist ein Fund und kein Grund, den Lauf abzubrechen.
                # ``hole`` meldet ihn laut, weil dort niemand weiterrechnet; hier ist die
                # richtige Antwort dieselbe wie bei einem Fehltreffer — rechnen, und den
                # Grund ins Protokoll schreiben. Ein Stapellauf soll nicht an einer fremden
                # Datei im Cache-Ordner sterben.
                eintrag, lese_fehler = None, str(fehler)
            if eintrag is not None:
                gespeichert = eintrag.get("ausgaben") or {}
                maengel = _cache_maengel(knoten.art, gespeichert, tabelle_bedarf)
                if maengel:
                    # Treffer im Schlüssel, aber der Eintrag hält nicht, was er zusagt. Kein
                    # Treffer also — es wird gerechnet, und der Eintrag wird dabei überschrieben.
                    eintrag = None
                    lese_fehler = "Eintrag verworfen: " + " ".join(maengel)
                else:
                    knoten_ergebnisse[kid] = _knoteneintrag(
                        knoten.art, eintrag.get("status", STATUS_OK), aus_cache=True,
                        dauer_s=time.perf_counter() - beginn,
                        dauer_s_original=eintrag.get("dauer_s"),
                        hash=schluessel, arbeits_dir=str(arbeit), ausgaben=gespeichert,
                    )
                    continue

            # --- 2) Rechnen --------------------------------------------------------------
            arbeit.mkdir(parents=True, exist_ok=True)
            try:
                antwort = tabelle[knoten.art](knoten=knoten, eingaben=eingaben, out_dir=arbeit)
            except Exception as fehler:                  # noqa: BLE001 — bewusst breit
                # Bewusst jede Ausnahme: Was hinter einer Prozessgrenze passiert, ist nicht
                # vorhersagbar (SeamError, CUDA-OOM, kaputte EXR, ein Fehler im eigenen
                # Adapter). Ein Stapelabbruch mitten in einer Serie kostet die ganze Serie;
                # ein protokollierter Fehlschlag kostet einen Knoten. Dieselbe Abwägung wie
                # in ``render.rendere``.
                antwort = {"status": STATUS_FEHLER, "error": f"{type(fehler).__name__}: {fehler}"}

            dauer = time.perf_counter() - beginn

            if not isinstance(antwort, dict):
                antwort = {
                    "status": STATUS_FEHLER,
                    "error": (f"Ausführer für {knoten.art!r} lieferte {type(antwort).__name__}, "
                              f"erwartet ist ein dict mit den Ausgaben des Knotens."),
                }
            status = antwort.get("status", STATUS_OK)

            cache_fehler = lese_fehler
            if status == STATUS_OK and cache is not None:
                eigen = tabelle_bedarf.get(knoten.art)
                try:
                    cache.lege_ab(schluessel, {
                        "art": knoten.art, "status": status,
                        "ausgaben": antwort, "dauer_s": round(dauer, 4),
                    }, zusagen=() if eigen is None else eigen.zugesagte_dateien(antwort))
                except GraphError as fehler:
                    # Der Knoten hat gerechnet und ist gelungen — er wird nicht nachträglich
                    # für gescheitert erklärt, nur weil sein Ergebnis nicht speicherbar ist.
                    # Stillschweigend übergangen wird es aber auch nicht: Ohne diese Meldung
                    # sähe man nur, dass der Cache nie greift, und suchte an der falschen
                    # Stelle.
                    cache_fehler = str(fehler)

            knoten_ergebnisse[kid] = _knoteneintrag(
                knoten.art, status, aus_cache=False, dauer_s=dauer, dauer_s_original=dauer,
                hash=schluessel, arbeits_dir=str(arbeit), ausgaben=antwort,
                error=antwort.get("error"), cache_fehler=cache_fehler,
            )

            if status != STATUS_OK:
                gescheitert.append(kid)
                for nachfolger in graph.nachfolger_transitiv([kid]):
                    uebersprungen.setdefault(
                        nachfolger, f"Vorgänger {kid!r} endete mit status={status!r}.")

        finally:
            # NACH JEDEM KNOTEN, AUF JEDEM WEG. Der Rumpf verlaesst die Runde an
            # fuenf Stellen mit `continue`; ein Melden an jeder einzelnen haette
            # eine davon vergessen, und der Knoten, der nie fertig meldet, bleibt
            # in der Anzeige fuer immer am Rechnen.
            #
            #     *Ein Waechter an vier von fuenf Ausgaengen bewacht den fuenften
            #     nicht — und genau durch den geht der seltene Fall.*
            fertig = knoten_ergebnisse.get(kid) or {}
            _melde({"art": "knoten_fertig", "knoten": kid, "knotenart": knoten.art,
                    "nummer": nummer, "von": len(reihenfolge),
                    "status": fertig.get("status"),
                    "aus_cache": fertig.get("aus_cache"),
                    "dauer_s": fertig.get("dauer_s")})
    # --- 3) Die zweite Schicht nachtragen --------------------------------------------
    #
    # NACH dem Lauf und NICHT waehrend: Das Urteil ueber die Basis faellt ein QA-Knoten im
    # Nebenzweig, und ob der vor oder nach dem Nachrender an der Reihe war, entscheidet
    # die topologische Reihenfolge. Wer waehrend des Laufs nachtruege, bekaeme je nach
    # Sortierung einmal ein Urteil und einmal «nicht gemessen» — dieselbe Frage, zwei
    # Antworten. Hier ist alles gerechnet, und die Antwort haengt an nichts als am Graphen.
    #
    # NACH dem Ablegen im Zwischenspeicher und nicht davor: Der Basis-Block darf nicht
    # mitgespeichert werden (siehe ``schichtbefund``). Diese Reihenfolge ist der ganze
    # Schutz davor — ein Urteil aus einem anderen Lauf waere kein Urteil ueber diesen.
    #
    # ADDITIV, ausdruecklich: Es wird nur danebengelegt. Kein bestehendes Feld aendert
    # sich, und ``bestanden`` schon gar nicht.
    for kid, zusatz in schichtbefund(graph, knoten_ergebnisse).items():
        eintrag = knoten_ergebnisse.get(kid)
        if eintrag is None:
            continue
        eintrag["ausgaben"] = {**(eintrag["ausgaben"] or {}), **zusatz}

    treffer = sum(1 for e in knoten_ergebnisse.values() if e["aus_cache"])
    gerechnet = sum(1 for e in knoten_ergebnisse.values()
                    if not e["aus_cache"] and e["status"] != STATUS_UEBERSPRUNGEN)
    return {
        "status": STATUS_OK if not gescheitert else STATUS_FEHLER,
        "reihenfolge": reihenfolge,
        "knoten": knoten_ergebnisse,
        "dauer_s": round(time.perf_counter() - beginn_gesamt, 4),
        "out_dir": str(wurzel),
        "gerechnet": gerechnet,
        "cache_treffer": treffer,
        "uebersprungen": sorted(uebersprungen),
        "gescheitert": gescheitert,
        "error": None if not gescheitert else "; ".join(
            f"{kid}: {knoten_ergebnisse[kid]['error']}" for kid in gescheitert),
    }


__all__ = [
    "ART_BILDQUELLE", "ART_GEOMETRIE", "ART_MULTIPASS", "ART_NACHRENDER", "ART_QA",
    "ART_RENDER",
    "AUSFUEHRER", "BEDARF", "EINGABEDATEIEN",
    "BASIS_BESTANDEN", "BASIS_BILD", "BASIS_GRUND", "BASIS_HERKUNFT", "BASIS_KNOTEN",
    "BASIS_URTEIL_VON", "HERKUNFT_BILDKETTE", "HERKUNFT_GEOMETRIE",
    "FELD_BASIS", "FELD_HANDEINGRIFF", "FELD_SCHICHT",
    "SCHICHT_AI_IMAGING", "SCHICHT_GEOMETRIE",
    "KNOTEN_BILDQUELLE", "KNOTEN_GEOMETRIE", "KNOTEN_MULTIPASS", "KNOTEN_NACHRENDER",
    "KNOTEN_QA", "KNOTEN_RENDER",
    "STATUS_ABGELEHNT", "STATUS_FEHLER", "STATUS_OK", "STATUS_UEBERSPRUNGEN",
    "KettenError",
    "baue_kette", "bildeingang_lage", "fuehre_aus", "haenge_nachrender_an",
    "nachrender_ausfuehrer", "pruefe_kette", "qa_ausfuehrer", "render_ausfuehrer",
    "schicht_von", "schichtbefund", "standard_out_dir",
]
