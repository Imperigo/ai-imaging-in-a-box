"""BACKBONE-REGISTRY — der Modell-Austauschbarkeits-Vertrag, als Daten.

Warum dieses Modul existiert
----------------------------
Der Entwurfsgedanke aus der Lagebeurteilung (Kapitel 4) lautet: **Nicht das Modell ist
der Vertrag, sondern die Konditionierung.** Wird jeder Backbone über dieselbe
Depth-ControlNet-Naht angesprochen — Tiefenkarte hinein, Bild heraus —, dann ist ein
Modellwechsel ein Registry-Eintrag und kein Umbau der Bildkette.

Damit das trägt, muss die Registry **Daten** sein und nicht Code: eine Tabelle, die man
liest, filtert und prüft, ohne ein einziges Gewicht zu laden. Genau deshalb ist dieses
Modul auf einem Rechner ohne GPU vollständig testbar. Das ist kein Behelf — es ist die
Eigenschaft, die den Vertrag überhaupt zu einem Vertrag macht.

Die Lizenz steht im Code, nicht nur in der Doku
-----------------------------------------------
Regel 1 verlangt permissive Lizenzen und schliesst Non-Commercial-Modellgewichte aus.
Eine Regel, die nur in einer Markdown-Datei steht, wird beim nächsten „probier doch mal
FLUX" umgangen. Darum trägt jeder Eintrag seine Lizenz und sein
``kommerziell_nutzbar``-Flag mit sich, ``waehle(kommerziell=True)`` filtert danach, und
``tests/test_backbone.py`` hält fest, dass FLUX.1-dev und FLUX.2-dev dort **niemals**
erscheinen. Regel 1 in ausführbarer Form.

Zwei Konditionierungsarten, und warum die Unterscheidung früh gehört
--------------------------------------------------------------------
* ``depth_controlnet`` — die Qwen-Familie, SDXL und SD3.5 nehmen eine Tiefenkarte über
  ein ControlNet entgegen. Das ist die Naht, auf die dieses Projekt setzt.
* ``integriertes_edit`` — FLUX.2 und HiDream verlassen das ControlNet-Paradigma
  zugunsten integrierten Multi-Reference-Editings. Sie brauchen **je eine eigene
  Adapterschicht**.

Die Lagebeurteilung nennt das ausdrücklich als etwas, das „bei der Entwurfsentscheidung
einzuplanen, nicht später zu entdecken" ist. Deshalb steht die Art im Datensatz: Wer
einen Backbone auswählt, sieht sofort, ob die vorhandene Naht trägt oder ob eine
Adapterschicht fehlt — statt es beim ersten Render zu merken.

Was dieses Modul bewusst *nicht* tut
------------------------------------
Es lädt nichts, es rechnet nichts, es ruft keine GPU. ``vorhandene_dateien`` schaut nur
nach, ob Dateien auf der Platte liegen. Das Laden der Gewichte gehört hinter dieselbe
Prozessgrenze wie alles Schwere (siehe ``seams.py``).

Abhängigkeiten: keine fremden. Reine stdlib plus ``aiimaging.lizenzquelle`` (das
ebenfalls nur stdlib benutzt) — kein ``torch``, kein ``diffusers``, kein ``bpy``.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

# Die Herkunfts-Vokabel liegt seit dem 18.08.2026 in einem eigenen Modul, weil sie drei
# Registries gemeinsam gehört (backbone, einbetter, tiefenschaetzer) und vorher in jeder
# anders geschrieben war — siehe aiimaging/lizenzquelle.py. Die Namen werden hier weiter
# geführt, damit bestehende Importe aus `aiimaging.backbone` gültig bleiben.
from aiimaging import lizenzquelle
from aiimaging.lizenzquelle import (  # noqa: F401  (bewusste Weitergabe)
    QUELLE_GEPRUEFT_PRAEFIX,
    QUELLE_MODELLKARTE,
    QUELLE_SEKUNDAER,
    QUELLE_UNGEPRUEFT,
    hinweis_zur_herkunft,
    ist_belegt,
)

#: Konditionierung über eine Tiefenkarte via ControlNet — die Naht dieses Projekts.
KOND_DEPTH_CONTROLNET = "depth_controlnet"

#: Integriertes Multi-Reference-Editing statt ControlNet. Braucht eine eigene
#: Adapterschicht; die Depth-Naht trägt hier NICHT.
KOND_INTEGRIERTES_EDIT = "integriertes_edit"

#: Alle gültigen Konditionierungsarten. Ein Wert ausserhalb dieser Menge ist ein Tippfehler
#: und wird als Fehler gemeldet, nicht als leeres Ergebnis zurückgegeben.
KONDITIONIERUNGEN = (KOND_DEPTH_CONTROLNET, KOND_INTEGRIERTES_EDIT)

#: Lizenznamen, die ohne weitere Auflage unter Regel 1 fallen.
#: Weitergeführt aus `lizenzquelle`, damit die Regel an EINER Stelle steht. Drei
#: Kopien derselben Liste laufen früher oder später auseinander.
PERMISSIVE_LIZENZEN = lizenzquelle.PERMISSIVE_LIZENZEN


class BackboneError(ValueError):
    """Unbekannter Backbone oder unbrauchbares Auswahlkriterium.

    Bewusst laut: Ein Tippfehler im Modellnamen darf nicht als „kein passendes Modell
    gefunden" durchgehen — das ist derselbe stille Fehlgriff, gegen den der Torwächter
    antritt.
    """


@dataclass(frozen=True)
class Backbone:
    """Ein Bildmodell als Datensatz — alles, was man vor dem ersten Laden wissen muss.

    Args:
        name: Schlüssel in :data:`BACKBONES`. Kleingeschrieben, mit Bindestrichen.
        modell_id: Hugging-Face-Repo-Kennung, so wie sie ``diffusers`` erwartet.
        parameter_b: Parameterzahl in Milliarden. Grobe Grössenordnung, kein Datenblatt.
        lizenz: Lizenzname der **Gewichte**, nicht des Codes. Modellgewichte zählen unter
            Regel 1 mit.
        kommerziell_nutzbar: Ob die Gewichte kommerziell eingesetzt werden dürfen.
            Bei ``False`` ist der Backbone unter Regel 1 ausgeschlossen — auch für daraus
            abgeleitete LoRAs.
        konditionierung: Einer der Werte aus :data:`KONDITIONIERUNGEN`.
        vram_gb: Grobe Schätzung des VRAM-Bedarfs (siehe :func:`_vram_schaetzung`).
            **Nicht gemessen** — hier existiert keine GPU.
        dateien: Pfade relativ zur Modellwurzel, die vorliegen müssen, damit ein Lauf
            überhaupt starten kann. Ordner (diffusers-Unterordner) sind zulässig.
        lizenz_quelle: Wie gut die Lizenzangabe belegt ist — eine der Vokabeln aus
            :mod:`aiimaging.lizenzquelle` oder ein Vermerk der Form
            ``"geprueft <datum> (<url>)"``. Vorgabe ist die zurückhaltendste Annahme.
            Ob ein Wert ein Beleg ist, beantwortet
            :func:`aiimaging.lizenzquelle.ist_belegt` und kein Vergleich von Hand.

    ``frozen=True``, weil die Registry ein Nachschlagewerk ist und kein Zustand. Ein
    versehentliches ``BACKBONES["..."].kommerziell_nutzbar = True`` an einer beliebigen
    Stelle im Programm würde Regel 1 lautlos aushebeln.
    """

    name: str
    modell_id: str
    parameter_b: float
    lizenz: str
    kommerziell_nutzbar: bool
    konditionierung: str
    vram_gb: float
    dateien: tuple[str, ...]
    lizenz_quelle: str = QUELLE_UNGEPRUEFT


def _vram_schaetzung(parameter_b: float) -> float:
    """Grobe VRAM-Schätzung in GB aus der Parameterzahl.

    Rechnung: Gewichte in bf16 (2 Byte je Parameter) plus ein Fünftel Aufschlag für
    Aktivierungen, Text-Encoder und VAE. Für 20B ergibt das 48 GB — plausibel für eine
    Karte der 48-GB-Klasse und deutlich über einer 24-GB-Karte.

    Die Zahl ist eine **Schätzung, keine Messung**: Auf diesem Rechner gibt es weder GPU
    noch Gewichte. Quantisierung (fp8, GGUF) und Offloading senken den Bedarf erheblich;
    wer eine gemessene Zahl hat, trägt sie an die Stelle der Schätzung ein — die Tests
    prüfen nur die untere Schranke (die Gewichte müssen mindestens hineinpassen), nicht
    die Formel, damit eine echte Messung sie ersetzen darf.
    """
    return round(parameter_b * 2.0 * 1.2, 1)


#: Dateien eines Modells im diffusers-Ordnerformat. Es sind Ordner, keine Einzeldateien —
#: ``vorhandene_dateien`` prüft darum auf Existenz, nicht auf „ist eine Datei".
_DIFFUSERS_DATEIEN = ("model_index.json", "transformer", "vae", "text_encoder", "tokenizer")


#: Die Registry. Reihenfolge ist bedeutungstragend: Der Vorgabe-Backbone steht zuoberst,
#: und :func:`waehle` gibt in dieser Reihenfolge zurück. Wer nur den ersten Treffer
#: nimmt, bekommt damit die empfohlene Wahl.
#:
#: Alle Angaben stammen aus ``docs/LAGEBEURTEILUNG_2026-08-14.md`` Kapitel 4. Die Spalte
#: „Geprüft" von dort steht hier als ``lizenz_quelle`` — sie gehört mit, weil Regel 1 an
#: diesen Angaben hängt und nicht jede von ihnen am Original gelesen ist.
#:
#: Stand nach der Lizenzprüfung vom 18.08.2026 (``docs/LIZENZPRUEFUNG_2026-08-18.md``):
#: Die Mehrheit der Einträge ist inzwischen belegt, offen bleiben SD3.5 (gar nicht
#: geprüft) und die beiden FLUX-dev-Gewichte (nur sekundär bekannt — sie sind unter
#: Regel 1 ohnehin ausgeschlossen, weshalb die Prüfung dort nachrangig ist). Welche
#: Einträge das genau sind, sagt nicht dieser Kommentar, sondern
#: :func:`aiimaging.lizenzquelle.ist_belegt` — ein Kommentar veraltet, eine Prüfung nicht.
BACKBONES: dict[str, Backbone] = {}


def _eintrag(backbone: Backbone) -> None:
    """Trägt einen Backbone ein und hält dabei die Invarianten der Registry."""
    if backbone.name in BACKBONES:
        raise BackboneError(f"Doppelter Registry-Schlüssel: {backbone.name!r}")
    if backbone.konditionierung not in KONDITIONIERUNGEN:
        raise BackboneError(
            f"{backbone.name}: unbekannte Konditionierung {backbone.konditionierung!r}. "
            f"Erlaubt: {', '.join(KONDITIONIERUNGEN)}."
        )
    BACKBONES[backbone.name] = backbone


_eintrag(Backbone(
    name="qwen-image-edit-2511",
    modell_id="Qwen/Qwen-Image-Edit-2511",
    parameter_b=20.0,
    lizenz="Apache-2.0",
    kommerziell_nutzbar=True,
    konditionierung=KOND_DEPTH_CONTROLNET,
    vram_gb=_vram_schaetzung(20.0),
    dateien=_DIFFUSERS_DATEIEN,
    # Als einziger Eintrag am Original geprüft (Modellkarte, Lagebeurteilung Kap. 4).
    # Das ist der Grund, warum gerade dieses Modell die Vorgabe ist: permissiv UND belegt.
    lizenz_quelle=QUELLE_MODELLKARTE,
))

_eintrag(Backbone(
    name="qwen-image-2512",
    modell_id="Qwen/Qwen-Image-2512",
    parameter_b=20.0,
    lizenz="Apache-2.0",
    kommerziell_nutzbar=True,
    konditionierung=KOND_DEPTH_CONTROLNET,
    vram_gb=_vram_schaetzung(20.0),
    dateien=_DIFFUSERS_DATEIEN,
    # Geprüft 2026-08-18 an der Modellkarte selbst: Front-Matter "license: apache-2.0".
    # https://huggingface.co/Qwen/Qwen-Image-2512 — Repo offen, nicht gated.
    lizenz_quelle=QUELLE_MODELLKARTE,
))

_eintrag(Backbone(
    name="z-image-turbo",
    modell_id="Tongyi-MAI/Z-Image-Turbo",
    parameter_b=6.0,
    lizenz="Apache-2.0",
    kommerziell_nutzbar=True,
    konditionierung=KOND_DEPTH_CONTROLNET,
    vram_gb=_vram_schaetzung(6.0),
    dateien=_DIFFUSERS_DATEIEN,
    # Geprüft 2026-08-18 an der Modellkarte selbst: Front-Matter "license: apache-2.0".
    # https://huggingface.co/Tongyi-MAI/Z-Image-Turbo — Repo offen, nicht gated.
    lizenz_quelle=QUELLE_MODELLKARTE,
))

_eintrag(Backbone(
    name="sdxl-juggernaut",
    modell_id="RunDiffusion/Juggernaut-XL-v9",
    # UNet ~2.6B plus zwei Text-Encoder — Grössenordnung, kein Datenblatt.
    parameter_b=3.5,
    # KORREKTUR 2026-08-18 (Lizenzprüfung, docs/LIZENZPRUEFUNG_2026-08-18.md): Der Eintrag
    # führte "OpenRAIL++-M". Die Modellkarte deklariert aber die ältere Variante —
    # Front-Matter "license: creativeml-openrail-m", im Text "CreativeML Open RAIL-M
    # license". Beides ist nutzungsbeschränkt und damit unter Regel 1 gleich zu behandeln;
    # der Bezeichner war trotzdem falsch und wird hier auf die belegte Fassung gesetzt.
    # ACHTUNG, ungelöst: Dieselbe Modellkarte verbietet zusätzlich den Einsatz "behind
    # paid API services" ohne gesonderte Lizenz. Diese Schranke trägt das Feld
    # kommerziell_nutzbar=True nicht — Owner-Entscheid nötig, siehe Prüfbericht.
    lizenz="CreativeML OpenRAIL-M",
    kommerziell_nutzbar=True,
    konditionierung=KOND_DEPTH_CONTROLNET,
    vram_gb=_vram_schaetzung(3.5),
    # Einzeldatei-Checkpoint plus separates Depth-ControlNet: SDXL bringt die Naht nicht
    # mit, das ControlNet ist ein eigenes Modell. Dafür ist das Ökosystem riesig — das
    # macht SDXL zum Rückfall, wenn für einen neueren Backbone kein ControlNet existiert.
    dateien=("juggernaut_xl.safetensors", "controlnet-depth-sdxl"),
    # Am Original gelesen, in der reichen Form: Der Vermerk trägt Datum UND URL und sagt
    # damit nicht nur, DASS geprüft wurde, sondern wogegen. `ist_belegt` erkennt ihn seit
    # dem 18.08.2026 als Beleg — vorher tat es das nicht, und `pruefe_lizenz` meldete
    # diesen Eintrag weiter als "NICHT geprüft" (Prüfbericht Abschnitt 5). Der Vermerk
    # bleibt bewusst in dieser Form stehen statt auf QUELLE_MODELLKARTE einzudampfen:
    # Das Schlagwort wäre die ärmere Angabe.
    lizenz_quelle="geprueft 2026-08-18 (https://huggingface.co/RunDiffusion/Juggernaut-XL-v9)",
))

_eintrag(Backbone(
    name="sd35-large",
    modell_id="stabilityai/stable-diffusion-3.5-large",
    parameter_b=8.0,
    lizenz="Stability AI Community License",
    # Frei unter 1 Mio USD Jahresumsatz — also kommerziell nutzbar, aber an eine
    # Bedingung geknüpft, die kein Code prüfen kann. pruefe_lizenz meldet die Auflage.
    kommerziell_nutzbar=True,
    konditionierung=KOND_DEPTH_CONTROLNET,
    vram_gb=_vram_schaetzung(8.0),
    dateien=_DIFFUSERS_DATEIEN,
    lizenz_quelle=QUELLE_UNGEPRUEFT,
))

_eintrag(Backbone(
    name="flux2-klein-4b",
    modell_id="black-forest-labs/FLUX.2-klein",
    parameter_b=4.0,
    lizenz="Apache-2.0",
    kommerziell_nutzbar=True,
    # Die Falle dieses Eintrags: permissiv lizenziert und damit unter Regel 1 einwandfrei
    # — aber OHNE klassisches Depth-ControlNet. Wer nur nach der Lizenz filtert, wählt
    # ein Modell, für das die Naht dieses Projekts nicht existiert.
    konditionierung=KOND_INTEGRIERTES_EDIT,
    vram_gb=_vram_schaetzung(4.0),
    dateien=_DIFFUSERS_DATEIEN,
    # Geprüft 2026-08-18 an Modellkarte UND LICENSE.md des 4B-Repos: Front-Matter
    # "license: apache-2.0", LICENSE.md ist der Apache-2.0-Volltext.
    # https://huggingface.co/black-forest-labs/FLUX.2-klein-4B
    # Zwei Befunde dazu im Prüfbericht: (a) die oben eingetragene modell_id
    # "black-forest-labs/FLUX.2-klein" existiert nicht (401), die Gewichte liegen unter
    # ".../FLUX.2-klein-4B"; (b) Apache-2.0 gilt nur für die 4B-Grösse — FLUX.2-klein-9B
    # steht unter der FLUX Non-Commercial License. Die Lizenz hängt an der Grösse.
    lizenz_quelle=QUELLE_MODELLKARTE,
))

_eintrag(Backbone(
    name="flux1-dev",
    modell_id="black-forest-labs/FLUX.1-dev",
    parameter_b=12.0,
    lizenz="FLUX.1 [dev] Non-Commercial License",
    # AUSGESCHLOSSEN unter Regel 1. Der Eintrag bleibt trotzdem in der Registry: Ein
    # ausgeschlossenes Modell, das gar nicht erst auftaucht, kann auch nicht als
    # ausgeschlossen gemeldet werden — und die Testprobe „waehle(kommerziell=True) gibt
    # es niemals zurück" wäre ohne den Eintrag vakuös.
    kommerziell_nutzbar=False,
    konditionierung=KOND_DEPTH_CONTROLNET,
    vram_gb=_vram_schaetzung(12.0),
    dateien=_DIFFUSERS_DATEIEN,
    lizenz_quelle=QUELLE_SEKUNDAER,
))

_eintrag(Backbone(
    name="flux2-dev",
    modell_id="black-forest-labs/FLUX.2-dev",
    parameter_b=32.0,
    lizenz="FLUX.2 [dev] Non-Commercial License",
    kommerziell_nutzbar=False,
    konditionierung=KOND_INTEGRIERTES_EDIT,
    vram_gb=_vram_schaetzung(32.0),
    dateien=_DIFFUSERS_DATEIEN,
    lizenz_quelle=QUELLE_SEKUNDAER,
))


#: Der Vorgabe-Backbone: Apache-2.0, am Original geprüft, natives Depth-ControlNet.
#: Die einzige Kombination in der Registry, die alle drei Eigenschaften belegt hat.
VORGABE_BACKBONE = "qwen-image-edit-2511"

#: Der schnelle Pfad für Vorschauen: 6B, 8 Schritte, Apache-2.0. Ein Vorschaubild soll in
#: Sekunden dastehen; die Geometrie-QA läuft trotzdem, nur eben auf einem gröberen Bild.
VORSCHAU_BACKBONE = "z-image-turbo"

#: Der Rückfall: riesiges ControlNet-Ökosystem. Wenn für einen neueren Backbone kein
#: passendes Depth-ControlNet existiert, trägt SDXL die Naht sicher.
RUECKFALL_BACKBONE = "sdxl-juggernaut"


def hole(name: str) -> Backbone:
    """Backbone nach Namen — oder ein Fehler, der die bekannten Namen nennt.

    Raises:
        BackboneError: Name unbekannt, leer oder kein String. Die Meldung listet die
            vorhandenen Schlüssel, weil ein Tippfehler sonst zu einer Suche im Quelltext
            zwingt.
    """
    if not isinstance(name, str) or not name.strip():
        raise BackboneError(f"Backbone-Name fehlt oder ist kein Text: {name!r}")
    try:
        return BACKBONES[name]
    except KeyError:
        raise BackboneError(
            f"Unbekannter Backbone {name!r}. Bekannt: {', '.join(sorted(BACKBONES))}."
        ) from None


def waehle(*, kommerziell: bool = True, max_vram_gb: float | None = None,
           konditionierung: str | None = None) -> list[Backbone]:
    """Alle Backbones, die den Anforderungen genügen — in Registry-Reihenfolge.

    Args:
        kommerziell: ``True`` (Vorgabe) verlangt kommerzielle Nutzbarkeit und schliesst
            damit FLUX.1-dev und FLUX.2-dev aus. ``False`` **lockert** diese Anforderung;
            es filtert nicht auf Non-Commercial, sondern hebt den Filter auf. Der Fall
            existiert für Forschung und Vergleichsmessungen — nicht für Auslieferung.
        max_vram_gb: Obergrenze für die geschätzte VRAM-Last. ``None`` heisst „egal".
        konditionierung: Auf eine Konditionierungsart einschränken. Wer die
            Depth-ControlNet-Naht bedienen will, gibt hier :data:`KOND_DEPTH_CONTROLNET`
            an und bekommt garantiert kein Modell, das eine eigene Adapterschicht bräuchte.

    Returns:
        Liste, möglicherweise leer. Die Reihenfolge ist die der Registry, und die stellt
        den Vorgabe-Backbone nach vorn — ``waehle()[0]`` ist damit die empfohlene Wahl,
        solange sie die Kriterien erfüllt.

    Raises:
        BackboneError: ``konditionierung`` ist unbekannt oder ``max_vram_gb`` ist keine
            positive Zahl. Beides würde sonst eine leere Liste erzeugen, und eine leere
            Liste liest sich wie „kein Modell passt" statt wie „deine Anfrage war falsch".

    Regel 1 lebt in der Vorgabe ``kommerziell=True``: Wer nichts sagt, bekommt nichts
    Ausgeschlossenes. ``tests/test_backbone.py`` hält das fest.
    """
    if konditionierung is not None and konditionierung not in KONDITIONIERUNGEN:
        raise BackboneError(
            f"Unbekannte Konditionierung {konditionierung!r}. "
            f"Erlaubt: {', '.join(KONDITIONIERUNGEN)}."
        )
    if max_vram_gb is not None:
        if isinstance(max_vram_gb, bool) or not isinstance(max_vram_gb, (int, float)):
            raise BackboneError(f"max_vram_gb ist keine Zahl: {max_vram_gb!r}")
        if max_vram_gb <= 0:
            raise BackboneError(f"max_vram_gb muss positiv sein, war {max_vram_gb!r}")

    treffer = []
    for backbone in BACKBONES.values():
        if kommerziell and not backbone.kommerziell_nutzbar:
            continue
        if max_vram_gb is not None and backbone.vram_gb > max_vram_gb:
            continue
        if konditionierung is not None and backbone.konditionierung != konditionierung:
            continue
        treffer.append(backbone)
    return treffer


def pruefe_lizenz(name: str) -> dict:
    """Darf dieser Backbone unter Regel 1 in ein ausgeliefertes Produkt?

    Returns:
        ``{name, lizenz, kommerziell_nutzbar, zulaessig, auflagen, lizenz_quelle,
        lizenz_belegt, lizenz_hinweis, begruendung}``.

        ``zulaessig`` ist die Antwort auf „darf verwendet werden", ``auflagen`` sagt
        „unter welchen Bedingungen". Beides getrennt, weil zwei Einträge (SDXL mit den
        CreativeML-OpenRAIL-M-Nutzungsauflagen **und** der Anbieterschranke gegen
        entgeltliche API-Dienste, SD3.5 mit der Umsatzschwelle) kommerziell nutzbar sind,
        aber eben nicht bedingungslos. Ein einzelnes Ja/Nein müsste eines von beidem
        unterschlagen.

    Raises:
        BackboneError: Backbone unbekannt.

    Die Prüfung liest nur den Datensatz. Sie ersetzt keine juristische Prüfung — und wo
    die Lizenzangabe selbst nicht am Original geprüft ist (``lizenz_quelle``), sagt die
    Begründung das ausdrücklich, statt eine Sicherheit vorzutäuschen.
    """
    backbone = hole(name)
    auflagen: list[str] = []

    if not backbone.kommerziell_nutzbar:
        zulaessig = False
        begruendung = (
            f"{backbone.name}: Lizenz '{backbone.lizenz}' erlaubt keine kommerzielle "
            f"Nutzung. Unter Regel 1 AUSGESCHLOSSEN — Modellgewichte zählen mit. Der "
            f"Ausschluss erstreckt sich auf abgeleitete LoRAs: Ein darauf trainierter "
            f"Stil ist genauso wenig verkaufbar wie das Modell selbst. Ein "
            f"verkaufbarer Stil muss auf einem Apache-2.0-Backbone aufsetzen."
        )
    elif backbone.lizenz in PERMISSIVE_LIZENZEN:
        zulaessig = True
        begruendung = (
            f"{backbone.name}: '{backbone.lizenz}' ist permissiv und ohne weitere "
            f"Auflage mit Regel 1 vereinbar. Auch abgeleitete LoRAs bleiben frei."
        )
    else:
        # Kommerziell nutzbar, aber die Lizenz ist keine der vier permissiven aus
        # Regel 1. Solche Fälle werden nicht stillschweigend durchgewinkt: Die Auflage
        # gehört benannt, damit sie im NOTICE landet und beim Wachsen des Büros
        # wieder aufschlägt.
        zulaessig = True
        if "Community" in backbone.lizenz:
            auflagen.append(
                "Freie Nutzung nur unterhalb der Umsatzschwelle von 1 Mio USD pro Jahr. "
                "Darüber ist eine kommerzielle Lizenz nötig — das ist eine Bedingung, "
                "die kein Code prüfen kann und die beim Wachsen des Betriebs zutrifft."
            )
        if "OpenRAIL" in backbone.lizenz:
            auflagen.append(
                f"'{backbone.lizenz}' enthält Nutzungsauflagen (verbotene "
                f"Verwendungszwecke), die an jeden Weitergabeempfänger durchgereicht "
                f"werden müssen."
            )
        if backbone.name == "sdxl-juggernaut":
            # Wörtlich von der Modellkarte, abgerufen 2026-08-18: "This model may not be
            # deployed behind paid API services without explicit licensing."
            #
            # Diese Schranke liegt OBERHALB der RAIL-Lizenz und ist an keiner der
            # bisherigen Kategorien ablesbar: `kommerziell_nutzbar=True` bleibt richtig
            # (persönliche und gestalterische Arbeit ist frei), aber unvollständig. Ein
            # eigenes Feld dafür wäre eine Registry für Einzelfälle — darum steht sie hier
            # als benannte Auflage, wo sie gelesen wird.
            auflagen.append(
                "ZUSÄTZLICH, oberhalb der Lizenz: Der Anbieter untersagt den Einsatz "
                "'behind paid API services' ohne gesonderte Lizenz (Modellkarte, geprüft "
                "2026-08-18). Für einen lokal laufenden Arbeitsplatz unerheblich — für "
                "einen entgeltlichen Renderdienst nicht. Wer das vorhat, klärt es vorher."
            )
        if not auflagen:
            auflagen.append(
                f"'{backbone.lizenz}' ist keine der unter Regel 1 genannten permissiven "
                f"Lizenzen. Vor Auslieferung im Original prüfen."
            )
        begruendung = (
            f"{backbone.name}: '{backbone.lizenz}' erlaubt kommerzielle Nutzung, aber "
            f"nicht bedingungslos. " + " ".join(auflagen)
        )

    hinweis = hinweis_zur_herkunft(backbone.lizenz_quelle)
    if hinweis is not None:
        # Auch ein 'zulaessig: True' bleibt eine Behauptung, solange die Lizenz nicht am
        # Original gelesen wurde. Das gehört in dieselbe Antwort, nicht in eine Fussnote.
        auflagen.append(f"{hinweis} — vor produktivem Einsatz an der Modellkarte prüfen.")
        begruendung += f" ({hinweis}.)"

    return {
        # Sichtbar, nicht entschieden — siehe lizenzquelle.regel_1_spannung.
        "regel_1_spannung": lizenzquelle.regel_1_spannung(
            backbone.name, backbone.lizenz, zulaessig),
        "name": backbone.name,
        "lizenz": backbone.lizenz,
        "kommerziell_nutzbar": backbone.kommerziell_nutzbar,
        "zulaessig": zulaessig,
        "auflagen": tuple(auflagen),
        "lizenz_quelle": backbone.lizenz_quelle,
        # Die Antwort auf „ist die Herkunft ein Beleg?" als Datum statt als Textprobe.
        # Ohne dieses Feld musste ein Aufrufer auf Zeichenketten suchen — und traf dabei
        # das Wort „geprüft" auch in Auflagen, die mit der Herkunft nichts zu tun haben
        # (Juggernaut: „Modellkarte, geprüft 2026-08-18"). Genau daran ist ein Test
        # hängengeblieben, der etwas anderes zu prüfen glaubte.
        "lizenz_belegt": ist_belegt(backbone.lizenz_quelle),
        # Derselbe Satz, den die Auflage oben trägt — hier noch einmal für sich, damit
        # alle drei Registries dieselbe Form beantworten (``None`` heisst: belegt).
        "lizenz_hinweis": hinweis,
        "begruendung": begruendung,
    }


def vorhandene_dateien(name: str, modell_wurzel) -> dict:
    """Welche der benötigten Dateien liegen unter ``modell_wurzel`` — und welche fehlen?

    Args:
        name: Backbone-Name.
        modell_wurzel: Verzeichnis, in dem die Gewichte dieses Backbones liegen
            (``str`` oder ``Path``).

    Returns:
        ``{name, wurzel, wurzel_existiert, vorhanden, fehlend, vollstaendig}``.

        ``vollstaendig`` ist nur dann ``True``, wenn nichts fehlt. Eine nicht existierende
        Wurzel ist kein Fehler, sondern der Normalfall vor dem ersten Download: Dann
        fehlen schlicht alle Dateien und ``wurzel_existiert`` sagt, warum.

    Raises:
        BackboneError: Backbone unbekannt.

    Geprüft wird nur **Existenz**, nicht Grösse, Hash oder Ladbarkeit. Das ist Absicht:
    Diese Funktion soll auf jedem Rechner laufen, auch ohne GPU und ohne Gewichte, und
    beantworten „lohnt sich der Versuch überhaupt?" — bevor ein Subprozess startet und
    nach zwei Minuten mit einem Traceback zurückkommt.
    """
    backbone = hole(name)
    wurzel = Path(modell_wurzel)

    vorhanden: list[str] = []
    fehlend: list[str] = []
    for eintrag in backbone.dateien:
        # exists() statt is_file(): diffusers legt Modelle in Unterordnern ab
        # (transformer/, vae/), und ein Ordner ist hier eine ebenso gültige Einheit.
        (vorhanden if (wurzel / eintrag).exists() else fehlend).append(eintrag)

    return {
        "name": backbone.name,
        "wurzel": str(wurzel),
        "wurzel_existiert": wurzel.is_dir(),
        "vorhanden": tuple(vorhanden),
        "fehlend": tuple(fehlend),
        "vollstaendig": not fehlend,
    }
