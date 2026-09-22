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

Und seit dem 18.09.2026 reicht das Feld allein nicht mehr: Bei FLUX.2-klein hängt die
Lizenz an der **Grösse** — 4B ist Apache-2.0, 9B ist Non-Commercial. Ein Riegel, der auf
den Namen schaut, lässt die 9B-Fassung durch, sobald jemand sie einträgt. Darum steht
die Lizenz solcher Familien in :data:`GROESSENGEBUNDENE_FAMILIEN` und nicht im Eintrag;
:func:`groessen_riegel` urteilt daraus, und zwar an drei Stellen — beim Eintragen, beim
Auswählen und beim Prüfen.

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

import re
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


#: Modellfamilien, bei denen die Lizenz **an der Grösse hängt** und nicht am Namen.
#:
#: BEFUND DER KARTIERUNG 18.09.2026: Bei FLUX.2-klein tragen zwei Fassungen denselben
#: Namen und zwei verschiedene Lizenzen —
#:
#:     FLUX.2-klein-4B   Apache-2.0                      unter Regel 1 zulässig
#:     FLUX.2-klein-9B   FLUX.2 [klein] Non-Commercial   unter Regel 1 AUSGESCHLOSSEN
#:
#: Ein Riegel, der auf den Namen „flux2-klein" schaut, hält die 9B-Fassung für die
#: 4B-Fassung. Das ist kein Randfall, sondern der wahrscheinlichste Weg: Ein neuer
#: Eintrag entsteht durch Abschreiben des benachbarten, und wer ``flux2-klein-9b`` aus
#: ``flux2-klein-4b`` kopiert, erbt dabei ``lizenz="Apache-2.0"`` und
#: ``kommerziell_nutzbar=True``. Der Datensatz behauptet dann etwas Falsches — und jede
#: Prüfung, die allein den Datensatz liest, bestätigt es.
#:
#: Darum steht die Lizenz dieser Familien **hier** und nicht im Eintrag: Die Tabelle ist
#: die Quelle, das Feld ``lizenz`` des Eintrags nur seine Behauptung. Widersprechen sich
#: beide, gewinnt die Tabelle. Das ist der ganze Unterschied zwischen einem Riegel und
#: einer Beschriftung.
#:
#: **UND HIER IST SEINE GRENZE, gegnerisch gemessen am 18.09.2026.** Die Tabelle
#: entscheidet ueber die Lizenz — aber ob sie ueberhaupt greift, haengt allein an den
#: Bezeichnern des Eintrags, und die sind drei Zeichenketten. Nachgestellt::
#:
#:     name="bfl-klein-9b"  modell_id="black-forest-labs/bfl2klein9b"
#:     parameter_b=9.0      lizenz="Apache-2.0"   kommerziell_nutzbar=True
#:
#:     _eintrag       ANGENOMMEN
#:     pruefe_lizenz  zulaessig=True
#:     waehle         enthaelt den Eintrag
#:
#: Alle drei Standorte durch. **Beide Spuren zu lesen halbiert die Luecke, es schliesst
#: sie nicht** — wer beide aendert, ist draussen. Der Satz unten («Ein Riegel, der nur
#: eine der beiden Spuren liest, ist durch das Aendern der anderen zu umgehen») bleibt
#: richtig, aber er sagt nicht, dass das Aendern BEIDER ebenso wirkt.
#:
#: Schliessen laesst sich das von hier aus nicht: Es braeuchte eine Angabe, die nicht im
#: Eintrag steht — die Groesse der Gewichte auf der Platte oder eine Pruefsumme. Beides
#: ist eine Messung am Geraet und liegt als Auftrag bei der HomeStation
#: (``auf-20260918-116``). Bis dahin gilt: Dieser Riegel faengt den ABSCHREIBFEHLER, und
#: nur den. Gegen jemanden, der beide Bezeichner umschreibt, ist er keine Sicherung.
GROESSENGEBUNDENE_FAMILIEN: dict[str, dict] = {
    "FLUX.2-klein": {
        # Woran die Familie erkannt wird — an ``name`` UND an ``modell_id``, beide
        # kleingeschrieben. Beide, weil beide veränderlich sind: Fehler 1 derselben
        # Kartierung war eine falsche ``modell_id`` bei richtigem ``name``, und der
        # umgekehrte Fall ist genauso möglich. Ein Riegel, der nur eine der beiden
        # Spuren liest, ist durch das Ändern der anderen zu umgehen.
        "kennmuster": ("flux2-klein", "flux.2-klein", "flux2_klein"),
        # Die einzige Grösse dieser Familie, die permissiv lizenziert ist.
        # Geprüft an Modellkarte UND LICENSE.md des 4B-Repos (Apache-2.0-Volltext).
        "freie_groessen_b": {4.0: "Apache-2.0"},
        # Bekannt gesperrte Grössen, mit der Lizenz, die dort wirklich gilt. Sie stehen
        # namentlich da, damit die Meldung sagen kann WARUM — nicht bloss „nicht in der
        # Freiliste".
        "gesperrte_groessen_b": {9.0: "FLUX.2 [klein] Non-Commercial License"},
        "quelle": "geprueft 2026-09-18 "
                  "(https://huggingface.co/black-forest-labs/FLUX.2-klein-4B)",
    },
}

#: Toleranz beim Vergleich der Parameterzahl, in Milliarden.
#:
#: GESETZT, nicht gemessen. ``parameter_b`` ist eine Grössenordnung („4B") und kein
#: Datenblatt — 4.0 und 4.03 sind dieselbe Fassung. Eng genug gewählt, dass 4 und 9
#: niemals zusammenfallen können.
#:
#: **Das Fenster ist absichtlich unsymmetrisch angewandt** (Gegenprüfung 18.09.2026):
#: Die Freiliste vergleicht mit ``<``, die Sperrliste mit ``<=``. Ein Riegel, der
#: fail-closed sein soll, darf am Rand nicht öffnen — bei genau 4.5 ist „das ist die
#: 4B-Fassung" eine Behauptung und keine Ablesung, und der vorherige Stand (``<=``
#: auf beiden Seiten) liess sie durch. Beim Sperren ist dasselbe Fenster umgekehrt
#: richtig: Dort schadet ein Rand zu viel nichts, und ein Rand zu wenig öffnet.
GROESSEN_TOLERANZ_B = 0.5


#: Tiefenkonvention: nah = grosser Grauwert (hell). **Das ist unsere `tiefe_norm.png`.**
#: Entspricht der Disparitätskonvention aus :mod:`aiimaging.tiefenschaetzer`.
POL_NAH_HELL = "nah_hell"

#: Tiefenkonvention: nah = kleiner Grauwert (dunkel). Das Gegenteil unserer Karte.
POL_NAH_DUNKEL = "nah_dunkel"

#: Nicht gemessen. Es wird dann NICHT gedreht — raten hiesse, mit halber
#: Wahrscheinlichkeit die Geometrie zu spiegeln, und zwar lautlos.
POL_UNBEKANNT = "unbekannt"

TIEFENPOLARITAETEN = (POL_NAH_HELL, POL_NAH_DUNKEL, POL_UNBEKANNT)

#: Was der Multipass dieses Projekts schreibt. Der Bezugspunkt jeder Umkehrfrage.
UNSERE_POLARITAET = POL_NAH_HELL


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
        vram_gb: Der VRAM-Bedarf in GB — **entweder gemessen oder geschätzt**, und
            welches von beidem, sagt ``vram_gemessen``. Die Schätzung steht in
            :func:`_vram_schaetzung`.
        vram_gemessen: Ob ``vram_gb`` aus einer **Messung am Gerät** stammt.
            **Vorgabe ist ``False``, und das ist die sichere Richtung.** Wer einen Eintrag
            hinzufügt und das Feld vergisst, bekommt die vorsichtigere Behandlung; wer es
            andersherum voreinstellte, bekäme sie genau dann nicht, wenn er es vergisst.
            Wofür der Unterschied zählt, steht bei ``render.MESSUNG_ZUSCHLAG``.
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
    vram_gemessen: bool = False
    lizenz_quelle: str = QUELLE_UNGEPRUEFT

    # --- Die zweite Hälfte der Naht ----------------------------------------------------
    #
    # BEFUND (`docs/BACKBONE_CONTROLNET_2026-08-18.md`, 18.08.2026): Ein Depth-ControlNet
    # ist **nie ein Modell, sondern immer zwei** — das Basismodell und das ControlNet, in
    # getrennten Repos mit getrennten Lizenzen. Die Registry kannte bis hierher nur eine
    # Lizenz und hat damit systematisch die halbe Naht geprüft. Das ist keine
    # Ungenauigkeit, sondern ein Loch in Regel 1: Ein Apache-2.0-Basismodell mit einem
    # nicht-kommerziellen ControlNet ergibt eine nicht-kommerzielle Kette, und
    # `pruefe_lizenz` hätte „zulässig" gemeldet.
    #
    # Bei FLUX ist genau das der Fall — dort sind alle drei verbreiteten Depth-ControlNets
    # *selbst* nicht-kommerziell lizenziert, ein permissives Basismodell würde also nichts
    # retten.
    #
    # ``None`` heisst NICHT „keines nötig", sondern **„noch nicht benannt"**. Bei
    # ``KOND_DEPTH_CONTROLNET`` ist das ein Mangel, den :func:`pruefe_lizenz` meldet.
    controlnet_id: str | None = None
    controlnet_lizenz: str | None = None
    controlnet_lizenz_quelle: str = QUELLE_UNGEPRUEFT

    #: Ordnername der ControlNet-Gewichte **neben** der Modellwurzel, wenn sie dort
    #: liegen. ``None`` heisst: kein zweites Verzeichnis, das ControlNet steckt in der
    #: Basis (oder es gibt keines).
    #:
    #: **Warum das ein eigenes Feld ist und nicht aus ``controlnet_id`` abgeleitet wird:**
    #: Der Ordner auf der Platte heisst ``z-image-controlnet-union``, die Repo-Kennung
    #: ``alibaba-pai/Z-Image-Turbo-Fun-Controlnet-Union``. Aus dem einen folgt das andere
    #: nicht. Eine Ableitung wäre eine Vermutung, und sie schlüge erst beim Laden fehl.
    controlnet_ordner: str | None = None

    #: Welche Tiefenkonvention das ControlNet dieses Modells **erwartet**.
    #:
    #: Einer aus :data:`TIEFENPOLARITAETEN`. Unsere ``tiefe_norm.png`` ist
    #: :data:`POL_NAH_HELL` — nah = grosser Grauwert. Erwartet ein ControlNet das
    #: Gegenteil, muss die Karte **vor** der Übergabe umgedreht werden.
    #:
    #: AM GERÄT GEMESSEN (`auf-20260818-13`, 18.08.2026): Bei Z-Image ist genau das der
    #: Fall, und der Unterschied ist kein Feinschliff — |spearman| springt von 0.38–0.52
    #: auf 0.79–0.85, also auf rund das Doppelte, bei jeder ControlNet-Stärke.
    #:
    #: **Das war der teuerste ungeprüfte Punkt der ganzen Kette.** Keine Modellkarte sagt
    #: die Konvention. Eine verkehrte Polarität erklärt einen schlechten Score
    #: vollständig — und sie sieht nach einem Problem des Bildmodells aus, während sie
    #: eines der Übergabe ist. Darum steht sie hier als Feld und nicht als Annahme.
    #:
    #: :data:`POL_UNBEKANNT` heisst: nicht gemessen. Dann wird **nicht** gedreht, und
    #: :func:`aiimaging.render.rendere` sagt in den Hinweisen, dass ein schlechter Score
    #: hier eine harmlose Erklärung haben könnte.
    tiefen_polaritaet: str = "unbekannt"

    #: ``guidance_scale`` dieses Modells — wie stark der Prompt das Bild zwingt.
    #:
    #: ``None`` heisst **nicht** „egal", sondern „für dieses Modell nicht bestimmt". Dann
    #: greift die Vorgabe von ``diffusers`` (meist 5.0 oder 7.5), und das ist eine fremde
    #: Entscheidung, keine eigene — :func:`aiimaging.render.rendere` sagt das als Hinweis.
    #:
    #: Der Wert ist nicht kosmetisch. Destillierte Turbo-Modelle sind darauf trainiert,
    #: OHNE Führung zu laufen; 5.0 liefert dort überzeichnete Bilder. Und unterhalb von
    #: 1.0 schaltet ``diffusers`` die klassifikatorfreie Führung ganz ab — **womit der
    #: negative Prompt wirkungslos wird, ohne dass jemand es merkt.** Dieselbe
    #: Fehlerklasse wie bei `controlnet_staerke` an einer Pipeline ohne ControlNet
    #: (`auf-20260818-09`), nur an einem anderen Argument.
    fuehrung: float | None = None


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


#: Eine Grössenangabe in einem Bezeichner: Ziffern, dann ``b``, dann Wortende.
#: ``"flux2-klein-9b"`` ergibt ``9``, ``"black-forest-labs/flux.2-klein-4b"`` ergibt ``4``.
#: Das ``flux2`` am Anfang ergibt nichts — dort folgt kein ``b`` — und ``labs`` ebenso
#: wenig, weil davor keine Ziffer steht.
_GROESSE_IM_BEZEICHNER = re.compile(r"(\d+(?:[.,]\d+)?)\s*b(?![a-z0-9])")


def _groessen_behauptungen(spuren) -> set[float]:
    """Welche Grössen behaupten Name und Kennung dieses Eintrags — in Milliarden?

    Nicht die Grösse des Modells, sondern das, was seine Bezeichner darüber sagen. Für
    ``groessen_riegel`` ist das die zweite, unabhängige Spur neben ``parameter_b``: Beide
    stehen in derselben Zeile der Registry, aber sie werden von Hand getrennt gepflegt,
    und darum gehen sie auseinander, wenn jemand nur eine davon ändert.

    Leere Menge heisst **nicht gemessen** — die Bezeichner sagen nichts über die Grösse.
    Dann gibt es hier nichts gegenzuprüfen, und ``parameter_b`` bleibt die einzige
    Angabe. Eine leere Menge ist also keine Bestätigung.
    """
    gefunden: set[float] = set()
    for spur in spuren:
        for treffer in _GROESSE_IM_BEZEICHNER.finditer(spur):
            gefunden.add(float(treffer.group(1).replace(",", ".")))
    return gefunden


def groessen_riegel(backbone) -> dict:
    """Hängt die Lizenz dieses Eintrags an seiner GRÖSSE — und hält sie dann stand?

    Warum es diesen Riegel überhaupt gibt
    -------------------------------------
    :func:`pruefe_lizenz` liest die Felder des Eintrags. Das ist richtig, solange der
    Eintrag die Wahrheit sagt — und genau das ist bei FLUX.2-klein nicht verlässlich:
    Dieselbe Familie trägt unter demselben Namen zwei Lizenzen, und welche gilt,
    entscheidet die Parameterzahl. Ein Eintrag, der von der 4B-Fassung abgeschrieben
    ist, bringt deren ``lizenz="Apache-2.0"`` mit, auch wenn er auf die 9B-Gewichte
    zeigt. Der Datensatz lügt dann nicht böswillig, er ist bloss kopiert.

    Dieser Riegel steht darum **über** dem Datensatz: Sagt
    :data:`GROESSENGEBUNDENE_FAMILIEN` nein, hilft kein Lizenzfeld im Eintrag.

    Returns:
        ``{familie, greift, groesse_b, erwartete_lizenz, zulaessig, grund, auflagen}``.

        ``zulaessig`` ist **dreiwertig**, wie bei :func:`_pruefe_controlnet`:

        * ``None`` — dieser Riegel hat zu diesem Eintrag nichts zu sagen, weil er
          keiner grössengebundenen Familie angehört. Das heisst **nicht** „in
          Ordnung", sondern „andere Frage"; die Lizenzprüfung urteilt weiter.
        * ``True``  — die Grösse steht in der Freiliste der Familie.
        * ``False`` — sie steht nicht darin. FAIL-CLOSED: auch eine Grösse, deren
          Lizenz schlicht niemand nachgesehen hat, wird nicht durchgelassen.

        ``grund`` hält die drei Fälle des ``False`` auseinander —
        ``"bekannt_nicht_kommerziell"`` (nachgesehen und ausgeschlossen),
        ``"nicht_freigegebene_groesse"`` (nicht nachgesehen) und
        ``"groessenangabe_widerspruechlich"`` (der Eintrag sagt zwei Grössen, siehe
        :func:`_groessen_behauptungen`). Durchgefallen und nicht gemessen bleiben damit
        unterscheidbar, obwohl alle drei dasselbe Tor schliessen.
    """
    spuren = (str(backbone.name).lower(), str(backbone.modell_id).lower())
    familie = None
    daten = None
    for kandidat, tabelle in GROESSENGEBUNDENE_FAMILIEN.items():
        if any(muster in spur for spur in spuren for muster in tabelle["kennmuster"]):
            familie, daten = kandidat, tabelle
            break

    groesse = float(backbone.parameter_b)

    if daten is None:
        # `bestaetigt_durch` ist hier `None` und nicht `()`: Es wurde gar nicht erst
        # gefragt, weil keine groessengebundene Familie greift. `()` hiesse «gefragt, und
        # kein Bezeichner deckt die Groesse» — die dritte Antwort gilt auch fuer dieses
        # Feld.
        return {"familie": None, "greift": False, "groesse_b": groesse,
                "erwartete_lizenz": None, "zulaessig": None,
                "grund": "keine_groessengebundene_familie",
                "bestaetigt_durch": None, "auflagen": ()}

    # --- Und `parameter_b` ist auch bloss ein Feld des Eintrags ------------------------
    #
    # BEFUND DER GEGENPRÜFUNG 18.09.2026, GEMESSEN: Bis hierher ersetzte dieser Riegel
    # das Vertrauen in `lizenz` durch Vertrauen in `parameter_b` — ein Feld derselben
    # Zeile, genauso mitkopiert. Ein Eintrag mit name="flux2-klein-9b",
    # modell_id=".../FLUX.2-klein-9B" und parameter_b=4.0 kam durch alle drei Standorte:
    # `groessen_riegel` sagte zulaessig=True, `pruefe_lizenz` sagte zulässig, `waehle`
    # gab ihn aus, und `_eintrag` nahm ihn an. Also genau der Fall, gegen den der Riegel
    # gebaut ist, ein Feld weiter links.
    #
    # Und es ist der WAHRSCHEINLICHERE Kopierfehler: Wer `flux2-klein-4b` abschreibt,
    # ändert zuerst den Namen — das ist der Schlüssel, ohne den der Eintrag nicht
    # entsteht — und übersieht die Zahl darunter. Die Annahme des vorherigen Standes war
    # die umgekehrte: Name und Grösse gerichtet, nur die Lizenz vergessen.
    #
    # Der Ausweg braucht keine neue Quelle: Name und Kennung TRAGEN die Grösse bereits
    # („-9B"), und dieser Riegel liest beide ohnehin. Widersprechen sie `parameter_b`,
    # ist nicht entscheidbar, welche der beiden Angaben stimmt — und dann wird nicht
    # geraten, sondern geschlossen. FAIL-CLOSED, vor der Freiliste, damit die Freiliste
    # den Widerspruch nicht überstimmen kann.
    behauptet = _groessen_behauptungen(spuren)
    abweichend = sorted(b for b in behauptet if abs(groesse - b) > GROESSEN_TOLERANZ_B)

    # BEFUND 18.09.2026, gegnerisch geprueft: «nicht gemessen» und «doppelt belegt»
    # ergaben BYTEWEISE DASSELBE Urteil. Nachgestellt mit zwei 4B-Eintraegen —
    # modell_id '…/FLUX.2-klein-4B' (Groesse zweifach belegt) und '…/FLUX.2-klein' (die
    # Bezeichner schweigen) — kamen zwei identische dicts heraus:
    #
    #     zulaessig=True, grund='freigegebene_groesse', erwartete_lizenz='Apache-2.0',
    #     auflagen=()
    #
    # Der Docstring von `_groessen_behauptungen` sagt ausdruecklich: «Eine leere Menge
    # ist also keine Bestaetigung.» Im Urteil war sie genau das. Wer den zweiten Fall
    # liest, kann nicht erkennen, dass allein `parameter_b` geurteilt hat — also genau
    # das Feld, dem dieser Riegel nicht allein glauben soll.
    #
    # `bestaetigt_durch` traegt darum mit, WELCHE Bezeichner die Groesse decken. Leeres
    # Tupel heisst: keiner. Das ist kein Ausschlussgrund — es gibt zulaessige Eintraege
    # ohne Groesse im Namen — aber es ist ein Unterschied, und er gehoert ins Urteil und
    # nicht in den Kopf des Lesers.
    bestaetigt_durch = tuple(
        feld for feld, spur in (("name", spuren[0]), ("modell_id", spuren[1]))
        if any(abs(groesse - b) <= GROESSEN_TOLERANZ_B
               for b in _groessen_behauptungen((spur,)))
    )
    if abweichend:
        return {"familie": familie, "greift": True, "groesse_b": groesse,
                "erwartete_lizenz": None, "zulaessig": False,
                "grund": "groessenangabe_widerspruechlich",
                "bestaetigt_durch": bestaetigt_durch,
                "auflagen": (
                    f"WIDERSPRUCH IN DER GRÖSSE: Der Eintrag '{backbone.name}' führt "
                    f"parameter_b={groesse:g}, seine Bezeichner nennen aber "
                    f"{', '.join(f'{b:g}B' for b in abweichend)} "
                    f"(name='{backbone.name}', modell_id='{backbone.modell_id}'). Bei "
                    f"der Familie '{familie}' entscheidet die Grösse über die Lizenz — "
                    f"welche der beiden Angaben stimmt, ist von hier aus nicht "
                    f"entscheidbar. Der Eintrag wird darum abgewiesen und nicht auf "
                    f"Verdacht der freundlicheren Lesart zugeschlagen. Wer ihn braucht, "
                    f"bringt Bezeichner und parameter_b in Übereinstimmung.",
                )}

    for frei, lizenz in daten["freie_groessen_b"].items():
        if abs(groesse - frei) < GROESSEN_TOLERANZ_B:
            auflagen: list[str] = []
            if backbone.lizenz != lizenz:
                # Die Grösse ist freigegeben, aber der Eintrag nennt eine andere Lizenz
                # als die Tabelle. Einer von beiden ist veraltet — und weil die Tabelle
                # die Quelle ist, ist es der Eintrag. Gemeldet statt still übernommen.
                auflagen.append(
                    f"WIDERSPRUCH: Für {groesse:g}B der Familie '{familie}' gilt "
                    f"'{lizenz}' ({daten['quelle']}), der Eintrag '{backbone.name}' "
                    f"traegt '{backbone.lizenz}'. Die Tabelle ist die Quelle."
                )
            if not bestaetigt_durch:
                # Kein Ausschluss, aber ein Vorbehalt: Hier hat `parameter_b` allein
                # entschieden, und eine zweite Spur, die widersprechen koennte, gibt es
                # nicht. Er steht in `auflagen`, weil das die Stelle ist, die gelesen
                # wird.
                auflagen.append(
                    f"NUR EINE SPUR: Weder Name noch Kennung des Eintrags "
                    f"'{backbone.name}' nennen eine Groesse. Ueber die Lizenz entschied "
                    f"damit allein das Feld parameter_b={groesse:g} — die Gegenprobe, "
                    f"die ein Abschreibfehler ausloesen wuerde, gibt es hier nicht."
                )
            return {"familie": familie, "greift": True, "groesse_b": groesse,
                    "erwartete_lizenz": lizenz, "zulaessig": True,
                    "grund": "freigegebene_groesse",
                    "bestaetigt_durch": bestaetigt_durch,
                    "auflagen": tuple(auflagen)}

    for gesperrt, lizenz in daten.get("gesperrte_groessen_b", {}).items():
        if abs(groesse - gesperrt) <= GROESSEN_TOLERANZ_B:
            return {"familie": familie, "greift": True, "groesse_b": groesse,
                    "erwartete_lizenz": lizenz, "zulaessig": False,
                    "grund": "bekannt_nicht_kommerziell",
                    "bestaetigt_durch": bestaetigt_durch,
                    "auflagen": (
                        f"Die Familie '{familie}' lizenziert nach GRÖSSE. Die "
                        f"{groesse:g}B-Fassung steht unter '{lizenz}' und ist unter "
                        f"Regel 1 AUSGESCHLOSSEN — gleichgültig, was der Eintrag "
                        f"'{backbone.name}' im Feld 'lizenz' behauptet "
                        f"('{backbone.lizenz}'), und gleichgültig, wie sehr sein Name "
                        f"der zugelassenen Fassung ähnelt. Der Ausschluss erstreckt "
                        f"sich auf daraus abgeleitete LoRAs.",
                    )}

    frei_genannt = ", ".join(f"{g:g}B" for g in sorted(daten["freie_groessen_b"]))
    return {"familie": familie, "greift": True, "groesse_b": groesse,
            "erwartete_lizenz": None, "zulaessig": False,
            "grund": "nicht_freigegebene_groesse",
            "bestaetigt_durch": bestaetigt_durch,
            "auflagen": (
                f"Die Familie '{familie}' lizenziert nach GRÖSSE; freigegeben ist "
                f"allein {frei_genannt}. Die {groesse:g}B-Fassung ('{backbone.name}') "
                f"ist keine davon, und ihre Lizenz ist NICHT geprüft. Sie wird darum "
                f"abgewiesen und nicht durchgewunken — nicht gemessen ist kein "
                f"Freibrief. Wer sie braucht, liest ihre Lizenz am Original und trägt "
                f"die Grösse in GROESSENGEBUNDENE_FAMILIEN nach.",
            )}


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

    # Der früheste der drei Standorte des Grössenriegels (siehe `groessen_riegel`):
    # Ein widersprüchlicher Eintrag kommt gar nicht erst in die Tabelle, und zwar beim
    # Import — also bei uns, nicht auf der Maschine der Nutzerin.
    #
    # Abgewiesen wird NUR der Widerspruch, nicht der Ausschluss: Ein ehrlich als
    # nicht-kommerziell deklarierter Eintrag darf in der Registry stehen, genau wie
    # `flux1-dev`. Ein ausgeschlossenes Modell, das gar nicht erst auftaucht, kann auch
    # nicht als ausgeschlossen gemeldet werden.
    riegel = groessen_riegel(backbone)
    if riegel["zulaessig"] is False and backbone.kommerziell_nutzbar:
        raise BackboneError(
            f"{backbone.name}: {riegel['auflagen'][0]} Der Eintrag führt trotzdem "
            f"kommerziell_nutzbar=True — so ist er unter Regel 1 nicht eintragbar."
        )
    if riegel["zulaessig"] is True and riegel["auflagen"]:
        raise BackboneError(f"{backbone.name}: {riegel['auflagen'][0]}")

    BACKBONES[backbone.name] = backbone


# Der Vorgabe-Backbone steht ZUERST: `waehle()` gibt die Registry-Reihenfolge
# zurueck, und `waehle()[0]` ist damit die Empfehlung. Bis zum 18.08.2026 stand
# hier qwen-image-edit-2511 — der Wechsel ist bei VORGABE_BACKBONE begruendet.
_eintrag(Backbone(
    name="z-image-turbo",
    modell_id="Tongyi-MAI/Z-Image-Turbo",
    parameter_b=6.0,
    lizenz="Apache-2.0",
    kommerziell_nutzbar=True,
    konditionierung=KOND_DEPTH_CONTROLNET,
    # GEMESSEN, nicht geschätzt (`auf-20260818-13`, HomeStation, zweimal bestätigt in
    # `auf-20260820-21` und `-22`): Basis + ControlNet-Union in bfloat16 belegen
    # **23 391 MiB** Spitze — transformer 11.46, text_encoder 7.49, controlnet 4.24,
    # vae 0.16 GiB. Die Schätzung aus der Parameterzahl lag bei 14.4 und zählte das
    # ControlNet nicht mit; wir laden es aber immer mit, sonst gibt es keine
    # Konditionierung. Der Docstring von `_vram_schaetzung` verlangt genau diesen
    # Austausch: «wer eine gemessene Zahl hat, trägt sie an die Stelle der Schätzung ein».
    #
    # ZWEITE MESSUNG, 08.09.2026 (`auf-20260909-92`, HomeStation, diffusers 0.39.0,
    # ControlNet über `from_single_file`, 512 x 512, 4-s-Raster über den ganzen Lauf):
    # **25 671 / 25 663 / 25 677 MiB** Spitze, also rund **25,1 GiB** — 9,7 % über der
    # ersten Messung. Zwei Zahlen, zwei Bedingungen; keine von beiden ist falsch.
    #
    # HIER STEHT DIE GRÖSSERE, und das ist eine Entscheidung über die Richtung des
    # Fehlers: Dieses Feld beantwortet «passt es auf die Karte?». Eine zu kleine Zahl
    # lässt `waehle(max_vram_gb=24)` dieses Modell durchgehen, und der Lauf stirbt am
    # Speicher — eine zu grosse verweigert nur einen Lauf, der vielleicht ginge. Von den
    # beiden Irrtümern ist der zweite der billigere.
    # DRITTE MESSUNG, 21.09.2026 (`auf-20260918-114`, HomeStation): **22,89 GB** —
    # niedriger als beide vorigen, weil Basis und ControlNet dort **67 Parameter teilen**
    # und nur einmal im Speicher stehen. Die Zahl bleibt trotzdem bei 25,1, und zwar aus
    # demselben Grund wie oben: Dieses Feld beantwortet «passt es auf die Karte?», und von
    # den beiden Irrtümern ist der zu grosse der billigere. Drei Messungen, drei
    # Bedingungen — 22,89 / 23,4 / 25,1 —, keine davon falsch.
    vram_gb=25.1,
    vram_gemessen=True,
    dateien=_DIFFUSERS_DATEIEN,
    # Geprüft 2026-08-18 an der Modellkarte selbst: Front-Matter "license: apache-2.0".
    # https://huggingface.co/Tongyi-MAI/Z-Image-Turbo — Repo offen, nicht gated.
    lizenz_quelle=QUELLE_MODELLKARTE,
    # Die Basis ALLEIN ist kein ControlNet: `DiffusionPipeline.from_pretrained` liefert
    # eine `ZImagePipeline` ohne Steuereingang. Die Naht entsteht erst über
    # `ZImageControlNetPipeline` mit diesem zweiten Repo — `control_image` und
    # `controlnet_conditioning_scale` (Vorgabe 0.75, empfohlenes Fenster 0.65–1.00) stehen
    # dort wörtlich in der Signatur von diffusers v0.39.0. Damit ist `controlnet_staerke`
    # dieses Projekts nicht erfunden, sondern die Angabe der Modellkarte.
    # Destilliert ("Turbo"): auf 8 Schritte OHNE klassifikatorfreie Führung trainiert.
    # 0.0 ist hier der richtige Wert, nicht ein ausgeschalteter — und er bedeutet
    # zugleich, dass ein negativer Prompt an diesem Modell nichts ausrichtet.
    fuehrung=0.0,
    # AM GERÄT GEMESSEN (auf-20260818-13): Mit unserer Karte (nah = hell) liegt
    # |spearman| bei 0.38–0.52, mit umgedrehter bei 0.79–0.85 — bei JEDER
    # ControlNet-Stärke rund das Doppelte. Das ControlNet erwartet nah = dunkel.
    tiefen_polaritaet=POL_NAH_DUNKEL,
    controlnet_id="alibaba-pai/Z-Image-Turbo-Fun-Controlnet-Union",
    controlnet_ordner="z-image-controlnet-union",
    controlnet_lizenz="Apache-2.0",
    # Front-Matter "license: apache-2.0"; das Ursprungsprojekt VideoX-Fun trägt eine
    # Apache-2.0-LICENSE im Volltext. Geprüft 2026-08-18.
    controlnet_lizenz_quelle=QUELLE_MODELLKARTE,
))

_eintrag(Backbone(
    name="qwen-image-edit-2511",
    modell_id="Qwen/Qwen-Image-Edit-2511",
    parameter_b=20.0,
    lizenz="Apache-2.0",
    kommerziell_nutzbar=True,
    # KORREKTUR 2026-08-18, am Gerät gemessen (auf-20260818-09, erster echter Render):
    # Dieser Eintrag führte `KOND_DEPTH_CONTROLNET`. Das ist über die tatsächlich
    # geladene Pipeline **falsch**. `QwenImageEditPlusPipeline` kennt weder einen
    # `control_image`-Eingang noch `controlnet_conditioning_scale` noch `strength`:
    #
    #   * Die Tiefenkarte wird als `image` übergeben und **ersetzt dabei den
    #     Beauty-Pass** — die Konditionierung ist Bildbearbeitung, nicht ControlNet.
    #   * `controlnet_staerke` und `denoise` sind **wirkungslos**. Eine Vergleichsreihe
    #     über 0.6/0.8/1.0 hätte dreimal dasselbe Bild geliefert und **wie ein Befund
    #     ausgesehen** — genau davor hat der Lauf bewahrt.
    #
    # Das trifft die Beschreibung von `controlnet_staerke` in `render.RenderAuftrag`
    # („die eigentliche Regler des Projekts") für den Vorgabe-Backbone: Es gibt ihn hier
    # nicht. Wer ihn braucht, nimmt einen Eintrag mit echter ControlNet-Naht.
    #
    # Die Angabe gilt für **diese Pipeline**, nicht zwingend für das Modell: Ob
    # Qwen-Image-Edit über einen anderen Weg eine Depth-ControlNet-Naht hat, ist NICHT
    # geprüft. Darum korrigiert statt gestrichen.
    konditionierung=KOND_INTEGRIERTES_EDIT,
    vram_gb=_vram_schaetzung(20.0),
    dateien=_DIFFUSERS_DATEIEN,
    # Als einziger Eintrag am Original geprüft (Modellkarte, Lagebeurteilung Kap. 4).
    # Das ist der Grund, warum gerade dieses Modell die Vorgabe ist: permissiv UND belegt.
    lizenz_quelle=QUELLE_MODELLKARTE,
    # PRÄZISIERUNG 19.08.2026 (`docs/KI_MODULE_BESTAND_2026-08-19.md`): `auf-20260818-09`
    # hat gemessen, dass `QwenImageEditPlusPipeline` **kein** ControlNet ist — das bleibt
    # richtig. Es war aber nicht die ganze Geschichte: Für die Qwen-Familie existiert ein
    # **separates** ControlNet (`qwen_image_controlnet_union`), das der ältere Bestand
    # über den ComfyUI-Weg einbindet. `KOND_INTEGRIERTES_EDIT` beschreibt also die
    # Pipeline, die wir benutzen, und NICHT die Familie.
    #
    # Wer daraus liest „Qwen kann kein ControlNet", liest falsch. Nachgetragen, damit die
    # Registry nicht eine engere Aussage macht, als die Messung hergibt — der Eintrag
    # `qwen-image-2512` trägt den ControlNet-Weg bereits.
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
    # Geprüft 2026-08-18 an der Modellkarte: Front-Matter "license: apache-2.0".
    controlnet_id="alibaba-pai/Qwen-Image-2512-Fun-Controlnet-Union",
    controlnet_lizenz="Apache-2.0",
    controlnet_lizenz_quelle=QUELLE_MODELLKARTE,
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
    # Front-Matter "license: apache-2.0", KEINE LICENSE-Datei im Repo. Geprüft
    # 2026-08-18. Das ControlNet ist damit freier als das Basismodell — die
    # Regel-1-Spannung dieses Eintrags liegt allein auf der Basis.
    controlnet_id="xinsir/controlnet-depth-sdxl-1.0",
    controlnet_lizenz="Apache-2.0",
    controlnet_lizenz_quelle=QUELLE_MODELLKARTE,
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
    # Anders als das Basismodell ist das ControlNet-Repo NICHT gated und trägt die
    # LICENSE.md im Volltext (Stability AI Community License, 5. Juli 2024). Geprüft
    # 2026-08-18 — der einzige Eintrag, dessen zweite Hälfte besser belegt ist als seine
    # erste.
    controlnet_id="stabilityai/stable-diffusion-3.5-large-controlnet-depth",
    controlnet_lizenz="Stability AI Community License",
    controlnet_lizenz_quelle=QUELLE_MODELLKARTE,
))

_eintrag(Backbone(
    name="flux2-klein-4b",
    # KORREKTUR 18.09.2026 (Kartierung): Hier stand "black-forest-labs/FLUX.2-klein".
    # Diese Kennung gibt es auf Hugging Face nicht — der Abruf endet mit 401, weil ein
    # nicht existierendes Repo von einem gesperrten nicht zu unterscheiden ist. Die
    # Gewichte liegen unter ".../FLUX.2-klein-4B".
    #
    # WO DAS AUFSCHLÄGT — und wo nicht (nachgeprüft 18.09.2026): NICHT beim Laden. Kein
    # Pfad dieser Software lädt je über `modell_id`; `render.lade_modell` liest ein
    # lokales Verzeichnis, und das leitet `render.standard_modell_wurzel` aus `name` ab,
    # nicht aus der Kennung. Die einzige Stelle, die `modell_id` überhaupt anfasst, ist
    # das Berichtsfeld in `render` — sie wird gelesen, nicht aufgerufen.
    #
    # Genau deshalb ist die Zeile trotzdem keine Kleinigkeit: Sie ist die Anweisung an
    # den Menschen, der die Gewichte holt. Falsch, gibt Hugging Face 401 zurück, weil ein
    # nicht existierendes Repo von einem gesperrten nicht zu unterscheiden ist — die
    # Meldung spricht dann von Zugangsrechten, wo ein Tippfehler steht, und sie erscheint
    # bei der Nutzerin, nie bei uns. Eine falsche Angabe, gegen die kein Lauf anschlägt,
    # braucht eine Probe.
    modell_id="black-forest-labs/FLUX.2-klein-4B",
    # 4.0 ist hier nicht nur Grössenordnung, sondern LIZENZTRAGEND: Für diese Familie
    # entscheidet die Parameterzahl über die Lizenz (siehe GROESSENGEBUNDENE_FAMILIEN).
    # Wer sie ändert, ändert die Lizenzlage — `groessen_riegel` hält dagegen.
    parameter_b=4.0,
    lizenz="Apache-2.0",
    kommerziell_nutzbar=True,
    # Die Falle dieses Eintrags: permissiv lizenziert und damit unter Regel 1 einwandfrei
    # — aber OHNE klassisches Depth-ControlNet. Wer nur nach der Lizenz filtert, wählt
    # ein Modell, für das die Naht dieses Projekts nicht existiert.
    konditionierung=KOND_INTEGRIERTES_EDIT,
    # GEMESSEN, nicht mehr geschätzt (`auf-20260918-114`, HomeStation, 21.09.2026, über
    # 78 Läufe, Spitze auf der Karte): **15,55 GB**. Die Schätzung aus der Parameterzahl
    # stand bei **9,6** und war um 62 Prozent zu klein.
    #
    # DER GRUND IST LEHRREICH UND GILT NICHT NUR HIER: Der Textgeber (Qwen3) ist bei
    # diesem Modell **so gross wie der Transformer selbst**. Eine Schätzung, die von der
    # Parameterzahl des Bildteils ausgeht, kann ihn darum nicht kennen — sie unterschätzt
    # jedes Modell mit grossem Textgeber, und zwar systematisch.
    #
    #     *Eine Faustformel, die einen ganzen Bestandteil nicht sieht, irrt nicht zufällig.*
    #
    # WAS SICH DADURCH AM PRODUKT ÄNDERT: Der Auftrag `auf-20260918-114` nannte dieses
    # Modell «9,6 GB, laptoptauglich» und das grosse «34 GB, zu gross». Beide Zahlen waren
    # falsch. Gemessen stehen sich **15,55** und **22,89** GB gegenüber — auf einem
    # MacBook M1 Max mit 32 GB Gesamtspeicher ist das kleine bequem und das grosse knapp,
    # aber nicht ausgeschlossen. Wer die Grenze zieht, zieht sie an diesen zwei Zahlen.
    #
    # NACHTRAG 21.09.2026 (E21): Die Frage nach dem Laptop ist zurueckgezogen — Referenz
    # ist wieder die HomeStation, und der Vorgabe-Backbone bleibt `z-image-turbo`. Die
    # gemessene Zahl bleibt trotzdem hier stehen: Sie ist eine Messung und keine Meinung,
    # und sie ersetzt eine Schaetzung, die um 62 Prozent danebenlag. *Was gemessen ist,
    # wird nicht dadurch unrichtig, dass die Frage sich erledigt hat.*
    vram_gb=15.55,
    vram_gemessen=True,
    dateien=_DIFFUSERS_DATEIEN,
    # Geprüft 2026-08-18 an Modellkarte UND LICENSE.md des 4B-Repos: Front-Matter
    # "license: apache-2.0", LICENSE.md ist der Apache-2.0-Volltext.
    # https://huggingface.co/black-forest-labs/FLUX.2-klein-4B
    # Zwei Befunde dazu im Prüfbericht, beide am 18.09.2026 gerichtet: (a) die frühere
    # modell_id "black-forest-labs/FLUX.2-klein" existiert nicht (401) — steht oben
    # richtig; (b) Apache-2.0 gilt nur für die 4B-Grösse, FLUX.2-klein-9B steht unter der
    # FLUX Non-Commercial License. Die Lizenz hängt an der Grösse, und seit (b) hängt
    # auch der Riegel dort: GROESSENGEBUNDENE_FAMILIEN statt Namensvergleich.
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
    # FLUX ist BEIDSEITIG zu: Alle drei verbreiteten Depth-ControlNets stehen selbst
    # unter der FLUX.1-[dev]-Non-Commercial-Lizenz. Selbst ein permissives
    # FLUX-Basismodell würde die Naht darum nicht retten. Geprüft 2026-08-18.
    controlnet_id="jasperai/Flux.1-dev-Controlnet-Depth",
    controlnet_lizenz="FLUX.1 [dev] Non-Commercial License",
    controlnet_lizenz_quelle=QUELLE_MODELLKARTE,
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


#: Der Vorgabe-Backbone — **gewechselt am 18.08.2026, nach drei Messungen.**
#:
#: Bis dahin stand hier ``qwen-image-edit-2511``, mit der Begründung „Apache-2.0, am
#: Original geprüft, natives Depth-ControlNet". Der dritte Teil war schlicht falsch, und
#: das ist am Gerät herausgekommen:
#:
#: * ``auf-20260818-09``: ``QwenImageEditPlusPipeline`` kennt weder ``control_image`` noch
#:   ``controlnet_conditioning_scale``. **Es ist kein ControlNet.** Die Angabe stammte aus
#:   einem einzigen Satz einer Lagebeurteilung, der Qwen-Edit gar nicht nannte.
#: * ``auf-20260818-10``: Was daraus folgt — die Nullprobe durch die ganze Kette ergibt
#:   spearman **+0.005**. Von der Tiefenordnung bleibt nichts übrig; drei verschieden
#:   gestörte Vorgaben ergeben auf zwölf Stellen denselben Score.
#: * ``auf-20260818-13``: ``z-image-turbo`` + Fun-ControlNet-Union kommt unter denselben
#:   Bedingungen auf **-0.853**, ist rund **hundertfach schneller** (1.4 s statt 150 s je
#:   Bild), und die ControlNet-Stärke wirkt nachweislich — alle sechs Prüfsummen
#:   verschieden. Beide Repos Apache-2.0, beide am Original geprüft.
#:
#: **Warum überhaupt gewechselt wird, obwohl der Score noch durchfällt:** Er hängt an
#: ``geom_iou``, und dessen Deckel ist nach ``auf-20260818-12`` eine Sache der
#: Silhouetten-Auswahl, nicht des Backbones — selbst ein perfektes Bild kam unter der
#: alten Regel nur auf 0.256. Die beiden Baustellen sind unabhängig. Einen Vorgabewert
#: stehenzulassen, von dem **gemessen** ist, dass er die Geometrie gar nicht überträgt,
#: wäre die schlechtere Wahl — auch wenn der Nachfolger die Schwelle noch nicht reisst.
#:
#: Ehrliche Grenze: Ein Lauf, eine Szene, ein Seed. Dass Z-Image über verschiedene
#: Bauwerke trägt, ist damit nicht gezeigt.
VORGABE_BACKBONE = "z-image-turbo"

#: Der frühere Vorgabewert. Steht hier, damit ein alter Lauf im Protokoll deutbar bleibt
#: und niemand ihn versehentlich für einen Messfehler hält.
FRUEHERER_VORGABE_BACKBONE = "qwen-image-edit-2511"

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
        # Der zweite Standort des Grössenriegels, und der unumgehbare: `waehle` liest
        # die Registry direkt und ruft `pruefe_lizenz` nicht auf. Ein Riegel allein in
        # der Lizenzprüfung liesse also genau den Weg offen, über den ein Modell
        # tatsächlich ausgewählt wird.
        #
        # Er hängt an `kommerziell` wie der Filter darüber — aus demselben Grund:
        # `kommerziell=False` lockert die Anforderung für Forschung und
        # Vergleichsmessungen, und es wäre inkonsequent, dort `flux1-dev` zu zeigen,
        # aber eine 9B-Fassung zu verbergen. Für die Auslieferung zählt die Vorgabe,
        # und die ist `True`.
        if kommerziell and groessen_riegel(backbone)["zulaessig"] is False:
            continue
        # DER DRITTE FILTER, und aus demselben Grund wie der Grössenriegel darüber:
        # `waehle` liest die Registry direkt und ruft `pruefe_lizenz` nicht auf. Stünde
        # der Owner-Entscheid vom 22.09.2026 nur in der Lizenzprüfung, bliebe genau der
        # Weg offen, über den ein Modell tatsächlich ausgewählt wird — `sdxl-juggernaut`
        # ist `kommerziell_nutzbar` und käme durch den ersten Filter.
        #
        #     *Eine Sperre an einem von zwei Wegen ist keine Sperre.*
        if kommerziell and not lizenzquelle.ist_permissiv(backbone.lizenz):
            continue
        if max_vram_gb is not None and backbone.vram_gb > max_vram_gb:
            continue
        if konditionierung is not None and backbone.konditionierung != konditionierung:
            continue
        treffer.append(backbone)
    return treffer


def _pruefe_controlnet(backbone) -> dict:
    """Die Lizenz der **zweiten** Hälfte einer ControlNet-Naht.

    Warum das eine eigene Prüfung braucht
    -------------------------------------
    Ein Depth-ControlNet ist nie ein Modell, sondern immer zwei: das Basismodell und das
    ControlNet, in getrennten Repos, unter getrennten Lizenzen. Die Registry kannte bis
    zum 18.08.2026 nur eine Lizenz — und hat damit bei jedem Eintrag mit
    ``KOND_DEPTH_CONTROLNET`` die halbe Naht beurteilt und die andere Hälfte als geprüft
    ausgegeben.

    Das ist nicht theoretisch. Bei FLUX sind **alle drei** verbreiteten Depth-ControlNets
    selbst nicht-kommerziell lizenziert; ein permissives FLUX-Basismodell hätte hier
    „zulässig" ergeben, und die Kette wäre trotzdem unverkäuflich gewesen
    (`docs/BACKBONE_CONTROLNET_2026-08-18.md`, Kap. 2.1 und 4.5).

    Returns:
        dict mit ``noetig``, ``benannt``, ``id``, ``lizenz``, ``lizenz_quelle``,
        ``lizenz_belegt``, ``zulaessig`` und ``auflagen``.

        ``zulaessig`` ist **dreiwertig**: ``True`` (permissiv belegt), ``False``
        (ausgeschlossen), ``None`` (nicht beurteilbar, weil nicht benannt). ``None`` ist
        nicht dasselbe wie ``True`` — und genau diese Gleichsetzung war der Fehler.
    """
    noetig = backbone.konditionierung == KOND_DEPTH_CONTROLNET
    benannt = backbone.controlnet_id is not None
    auflagen: list[str] = []

    if not noetig:
        # Ein integriertes Edit-Modell braucht kein zweites Repo. Ist trotzdem eines
        # eingetragen, ist das ein Widerspruch im Datensatz und kein stiller Zusatz.
        if benannt:
            auflagen.append(
                f"Widerspruch im Datensatz: '{backbone.name}' ist als "
                f"'{backbone.konditionierung}' geführt, trägt aber ein ControlNet "
                f"('{backbone.controlnet_id}'). Eines von beidem ist falsch."
            )
        return {"noetig": False, "benannt": benannt, "id": backbone.controlnet_id,
                "lizenz": backbone.controlnet_lizenz,
                "lizenz_quelle": backbone.controlnet_lizenz_quelle,
                "lizenz_belegt": False, "zulaessig": None, "auflagen": tuple(auflagen)}

    if not benannt:
        # NICHT `zulaessig=False` — das wäre eine Behauptung über eine Lizenz, die
        # niemand gelesen hat. Aber auch nicht `True`: Die Naht ist unvollständig
        # beschrieben, und wer sie bauen will, muss das zweite Repo erst suchen.
        auflagen.append(
            f"UNVOLLSTÄNDIG: '{backbone.name}' ist als Depth-ControlNet geführt, aber "
            f"das dazugehörige ControlNet-Repo ist nicht benannt. Damit ist die halbe "
            f"Naht ungeprüft — Basismodell und ControlNet tragen getrennte Lizenzen, und "
            f"die Kette ist so frei wie ihr unfreiestes Glied."
        )
        return {"noetig": True, "benannt": False, "id": None,
                "lizenz": None, "lizenz_quelle": backbone.controlnet_lizenz_quelle,
                "lizenz_belegt": False, "zulaessig": None, "auflagen": tuple(auflagen)}

    lizenz = backbone.controlnet_lizenz or ""
    belegt = ist_belegt(backbone.controlnet_lizenz_quelle)

    if lizenz in PERMISSIVE_LIZENZEN:
        zulaessig = True
    elif "Non-Commercial" in lizenz or "non-commercial" in lizenz:
        zulaessig = False
        auflagen.append(
            f"Das ControlNet '{backbone.controlnet_id}' steht unter '{lizenz}' und ist "
            f"damit nicht kommerziell nutzbar — unabhängig davon, wie frei das "
            f"Basismodell ist."
        )
    else:
        zulaessig = True
        auflagen.append(
            f"Das ControlNet '{backbone.controlnet_id}' steht unter '{lizenz}' — keine "
            f"der unter Regel 1 genannten permissiven Lizenzen. Vor Auslieferung im "
            f"Original prüfen, so wie beim Basismodell auch."
        )

    hinweis = hinweis_zur_herkunft(backbone.controlnet_lizenz_quelle)
    if hinweis is not None:
        auflagen.append(
            f"ControlNet '{backbone.controlnet_id}': {hinweis} — vor produktivem Einsatz "
            f"an der Modellkarte prüfen."
        )

    return {"noetig": True, "benannt": True, "id": backbone.controlnet_id,
            "lizenz": backbone.controlnet_lizenz,
            "lizenz_quelle": backbone.controlnet_lizenz_quelle,
            "lizenz_belegt": belegt, "zulaessig": zulaessig, "auflagen": tuple(auflagen)}


def pruefe_lizenz(name: str) -> dict:
    """Darf dieser Backbone unter Regel 1 in ein ausgeliefertes Produkt?

    Returns:
        ``{name, lizenz, kommerziell_nutzbar, zulaessig, auflagen, lizenz_quelle,
        lizenz_belegt, lizenz_hinweis, begruendung, controlnet, groessen_riegel,
        regel_1_spannung}``.

        ``controlnet`` und ``groessen_riegel`` tragen die beiden Teilurteile als Daten
        weiter, statt sie nur als Satz in ``auflagen`` abzulegen — ein Aufrufer soll sie
        nicht aus Text zurückgewinnen müssen. In beiden heisst ``zulaessig: None`` „andere
        Frage", nicht „in Ordnung".

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
        # Regel 1.
        #
        # OWNER-ENTSCHEID 22.09.2026: «Nur zum Messen, nie ausgeliefert» — wie FLUX.
        #
        # Bis dahin stand hier `zulaessig = True`, und das war seit dem 18.08.2026
        # ausdrücklich als offene Frage markiert (`lizenzquelle.regel_1_spannung`): Der
        # Einbetter schloss DINOv3 mit der Begründung aus, Regel 1 verlange «permissiv,
        # nicht bloss erlaubt», und diese Registry liess dieselbe Klasse von Lizenz zu.
        # Dieselbe Frage, entgegengesetztes Urteil — einen Monat lang.
        #
        # *Eine Spannung, die man meldet und nicht auflöst, wird nach einem Monat nicht
        # mehr gelesen.* Aufgelöst hat sie der Owner, nicht dieser Code.
        #
        # Die Auflagen werden trotzdem weiter gesammelt: Wer das Modell zum Vergleich
        # heranzieht, soll wissen, woran er wäre, wenn er es je ausliefern wollte.
        zulaessig = False
        if "Community" in backbone.lizenz:
            auflagen.append(
                "Freie Nutzung nur unterhalb der Umsatzschwelle von 1 Mio USD pro Jahr. "
                "Darüber ist eine kommerzielle Lizenz nötig — das ist eine Bedingung, "
                "die kein Code prüfen kann und die beim Wachsen des Betriebs zutrifft."
            )
            # Nachgetragen 2026-08-18 aus dem Volltext der LICENSE.md, die im
            # ControlNet-Repo lesbar ist (das Basismodell selbst ist gated). Beide
            # Auflagen standen bisher nirgends — und beide treffen genau das, was dieses
            # Projekt tut.
            auflagen.append(
                "NENNUNGSPFLICHT: Die Lizenz verlangt den Hinweis 'Powered by Stability "
                "AI' bei Weitergabe. Das betrifft nicht nur das NOTICE, sondern jede "
                "Auslieferung eines damit erzeugten Bildes im Produkt."
            )
            auflagen.append(
                "Die Ausgaben dürfen NICHT verwendet werden, um fremde Basismodelle zu "
                "verbessern oder zu trainieren. Für dieses Projekt unmittelbar "
                "einschlägig: Ein LoRA auf Bildern dieses Modells wäre ein Verstoss, "
                "auch wenn das LoRA selbst auf einem freien Backbone sässe."
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
            f"{backbone.name}: '{backbone.lizenz}' erlaubt kommerzielle Nutzung, ist aber "
            f"keine der vier Lizenzen, die Regel 1 nennt (MIT, Apache-2.0, BSD, MPL-2.0). "
            f"Owner-Entscheid 22.09.2026: nur zum Messen und Vergleichen, NIE im "
            f"ausgelieferten Produkt — dieselbe Behandlung wie FLUX. Was eine Auslieferung "
            f"verlangen würde: " + " ".join(auflagen)
        )

    # --- Die Lizenz hängt manchmal an der GRÖSSE, nicht am Namen ------------------------
    #
    # Der dritte Standort des Grössenriegels — der, an dem geurteilt wird. Alles bis
    # hierher liest die Felder des Eintrags; genau die sind es aber, die beim Abschreiben
    # eines benachbarten Eintrags mitwandern. Der Riegel steht darum ÜBER dem Datensatz:
    # Sagt die Tabelle nein, hilft kein `lizenz="Apache-2.0"` im Eintrag.
    # Der Stand VOR dem Riegel, und er entscheidet unten, ob die Begründung ersetzt oder
    # ergänzt wird. Eine leere Liste heisst: Der Satz oben behauptet Bedingungslosigkeit.
    # Eine gefüllte heisst: Er trägt seine Auflagen bereits mit — dann ist er nicht
    # widerlegt, sondern unvollständig, und Ersetzen wäre Löschen.
    auflagen_vor_dem_riegel = list(auflagen)

    riegel = groessen_riegel(backbone)
    if riegel["zulaessig"] is False:
        auflagen.extend(riegel["auflagen"])
        if zulaessig:
            begruendung = (
                f"{backbone.name}: Nach dem Lizenzfeld des Eintrags wäre dieses Modell "
                f"zulässig — nach seiner GRÖSSE ist es das nicht. "
                + " ".join(riegel["auflagen"])
            )
        else:
            # Der ältere Ausschlussgrund bleibt stehen; zwei Gründe sind zwei Gründe.
            begruendung += " HINZU KOMMT: " + " ".join(riegel["auflagen"])
        zulaessig = False
    elif riegel["auflagen"]:
        auflagen.extend(riegel["auflagen"])
        # Die Begründung wird ERSETZT, nicht ergänzt — aber nur dort, wo bis hierher ein
        # Freispruch stand. GEMESSEN 18.09.2026: Bis dahin wanderte der WIDERSPRUCH nur
        # in `auflagen`, während `begruendung` weiterhin wörtlich „ist permissiv und OHNE
        # WEITERE AUFLAGE mit Regel 1 vereinbar" sagte — ein Satz bestritt den anderen.
        # Wer nur die Begründung liest (und das tut jede Fehlermeldung, die sie
        # durchreicht), erfuhr nie, dass Tabelle und Eintrag auseinandergehen.
        #
        # Anhängen genügt dort nicht: Der alte Satz behauptet Bedingungslosigkeit, und die
        # ist jetzt widerlegt. Eine widerlegte Behauptung mit einem „aber" stehen zu
        # lassen, heisst sie stehen zu lassen.
        #
        # BERICHTIGT AM 18.09.2026, und der erste Anlauf war schlimmer als das Problem:
        # Ersetzt wurde BEDINGUNGSLOS, mit der Begründung «Der Ausgang bleibt
        # `zulaessig=True` — die Grösse ist ja freigegeben». Diese Prämisse ist falsch.
        # `zulaessig` kann hier längst `False` sein, denn die Lizenzprüfung oben läuft
        # zuerst. Nachgestellt mit einem 4B-Eintrag, dessen Lizenzfeld auf
        # nicht-kommerziell steht:
        #
        #     zulaessig         False          (richtig)
        #     begruendung       „Die Grösse ist unter Regel 1 freigegeben, aber …"
        #     verschwunden      „erlaubt keine kommerzielle Nutzung",
        #                       „Unter Regel 1 AUSGESCHLOSSEN", der Satz über LoRAs
        #
        # Das Urteil war richtig und der Satz daneben las sich wie ein Etikettenstreit.
        # **Ein Fehlschlag, der wie ein Erfolg aussieht, wird nicht gefunden — er wird
        # geglaubt**, und hier ging es um einen Lizenzausschluss.
        #
        # Steht also schon ein Ausschlussgrund, wird er VORANGESTELLT und der Widerspruch
        # kommt hinzu: zwei Gründe sind zwei Gründe, genau wie im Zweig darüber.
        #
        # ZWEITER BEFUND DERSELBEN DURCHSICHT: Ersetzt wurde auch dort, wo die alte
        # Begründung ihre eigenen Auflagen schon mittrug. Nachgestellt mit einem
        # 4B-Eintrag auf 'Stability AI Community License': `zulaessig` blieb `True`, und
        # aus der Begründung fielen die Umsatzschwelle von 1 Mio USD, die Nennungspflicht
        # 'Powered by Stability AI' und das Trainingsverbot heraus — alle drei standen
        # danach nur noch in `auflagen`. Dasselbe Loch, eine Ebene tiefer.
        #
        # Die Unterscheidung ist darum nicht `zulaessig`, sondern **ob der alte Satz
        # etwas behauptet hat, das jetzt widerlegt ist**:
        #
        #   keine Auflagen vorher  → der Satz sagt „bedingungslos". Widerlegt. ERSETZEN.
        #   Auflagen vorher        → der Satz trägt seine Bedingungen mit. Nicht
        #                            widerlegt, nur unvollständig. ERGÄNZEN.
        if zulaessig and not auflagen_vor_dem_riegel:
            begruendung = (
                f"{backbone.name}: Die Grösse ist unter Regel 1 freigegeben, aber die "
                f"Lizenzangabe des Eintrags deckt sich nicht mit der geprüften Quelle. "
                + " ".join(riegel["auflagen"])
            )
        else:
            begruendung += (
                " HINZU KOMMT: Die Grösse selbst wäre unter Regel 1 freigegeben, aber "
                "die Lizenzangabe des Eintrags deckt sich nicht mit der geprüften "
                "Quelle. " + " ".join(riegel["auflagen"])
            )

    # --- Die zweite Hälfte der Naht ---------------------------------------------------
    #
    # Ein Depth-ControlNet ist immer zwei Modelle. Bis zum 18.08.2026 hat diese Funktion
    # nur das Basismodell geprüft und damit systematisch die halbe Naht beurteilt.
    controlnet = _pruefe_controlnet(backbone)
    auflagen.extend(controlnet["auflagen"])
    if controlnet["zulaessig"] is False:
        # Die Kette ist so frei wie ihr unfreiestes Glied. Ein permissives Basismodell
        # rettet ein nicht-kommerzielles ControlNet nicht — beide Gewichte laufen im
        # selben Bild zusammen.
        #
        # Die Begründung wird ERGÄNZT, nicht ersetzt. War das Basismodell schon
        # ausgeschlossen, ist das der ältere und schwerere Grund; ihn zu überschreiben
        # hiesse, einen Ausschluss durch einen anderen zu verdecken — und dabei ginge
        # der Satz über die abgeleiteten LoRAs verloren, der beim Stil-Training zuschlägt.
        if zulaessig:
            begruendung = (
                f"{backbone.name}: Das Basismodell wäre zulässig, das dazugehörige "
                f"ControlNet '{backbone.controlnet_id}' ({backbone.controlnet_lizenz}) "
                f"ist es nicht. Unter Regel 1 AUSGESCHLOSSEN — eine Naht ist so frei wie "
                f"ihr unfreiestes Glied."
            )
        else:
            begruendung += (
                f" HINZU KOMMT: Auch das ControlNet '{backbone.controlnet_id}' steht "
                f"unter '{backbone.controlnet_lizenz}'. Die Naht ist damit BEIDSEITIG "
                f"zu — selbst ein permissives Basismodell derselben Familie würde sie "
                f"nicht retten."
            )
        zulaessig = False

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
        # Die zweite Hälfte der Naht, als eigenes Feld statt als Textprobe in `auflagen`.
        "controlnet": controlnet,
        # Die Grössenfrage ebenso: als Datum, nicht als Satz, den ein Aufrufer wieder
        # auseinandernehmen müsste. `zulaessig: None` heisst hier „andere Frage", nicht
        # „in Ordnung" — siehe `groessen_riegel`.
        "groessen_riegel": riegel,
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
