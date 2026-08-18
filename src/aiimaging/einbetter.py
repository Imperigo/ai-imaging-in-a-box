"""Registry der Bild-Einbettungsmodelle für das Stil-Gate — mit Lizenz je Modell.

Warum es dieses Modul gibt
--------------------------
Das Stil-Gate misst Ähnlichkeit zwischen Bild-Embeddings. Welches Netz diese Embeddings
erzeugt, ist keine reine Geschmacksfrage, sondern eine **Lizenzfrage** — und Regel 1
verlangt, dass sie beantwortet ist, bevor Technik gewählt wird. Wie bei
:mod:`aiimaging.backbone` steht die Lizenz darum im Code und nicht nur in der Doku.

Der Befund, der eine geerbte Annahme korrigiert (2026-08-18)
------------------------------------------------------------
Der Vorläufer KosmoVis verwendet **DINOv3**. Die Prüfung ergibt: **DINOv3 fällt unter
Regel 1 durch.**

Es steht nicht unter einer der vier zugelassenen Lizenzen (MIT, Apache-2.0, BSD,
MPL-2.0), sondern unter einer eigenen Meta-Lizenz mit drei Auflagen:

1. **Gated** — der Zugang muss beantragt werden, unter Angabe persönlicher Daten.
2. **Namensnennung** — „Built with DINOv3" muss sichtbar geführt werden.
3. **Weitergabe nur mit Lizenztext** — jede Weitergabe abgeleiteter Werke trägt die
   Vereinbarung mit.

Kommerzielle Nutzung ist dabei ausdrücklich *erlaubt*. Das ändert nichts: Regel 1
verlangt permissive Lizenzen, und eine Sonderlizenz mit Auflagen ist genau das, was sie
ausschliesst. Zudem gilt für ein öffentliches Apache-2.0-Repo: Eine gated Abhängigkeit
kann niemand nachvollziehen, der keinen Zugang beantragt hat.

**Entscheidung:** Vorgabe ist **SigLIP 2** (Apache-2.0). DINOv3 bleibt in der Registry
geführt — aber als ausgeschlossen markiert, damit der Grund auffindbar bleibt und nicht
jemand später „das nimmt doch KosmoVis auch" denkt.

Was diese Registry NICHT leistet
--------------------------------
Sie ist eine Behauptung über die Modellwelt, keine Messung an ihr. Ob SigLIP-Embeddings
den Haus-Stil ähnlich gut trennen wie DINOv3, ist **ungeprüft** — die überlieferten
Wertebereiche (Treffer ~0,5–0,6, Verfehlung ~0,06–0,13) stammen aus DINOv3-Läufen. Beim
Wechsel des Einbetters ist die Schwelle 0,30 neu zu kalibrieren; das gehört ohnehin in
die Schwellenstudie (Phase 4).
"""
from __future__ import annotations

from dataclasses import dataclass

# Dieselbe Vokabel für die Herkunft einer Lizenzangabe wie in `backbone` und
# `tiefenschaetzer`. Sie lag bis zum 18.08.2026 nur in `backbone`, und dieses Modul trug
# stattdessen freien Text — dieselbe Sache in drei Schreibweisen (Prüfbericht Abschnitt 5).
from aiimaging import lizenzquelle
from aiimaging.lizenzquelle import QUELLE_UNGEPRUEFT, hinweis_zur_herkunft, ist_belegt

#: Lizenzen, die Regel 1 zulässt.
ZUGELASSENE_LIZENZEN = frozenset({"MIT", "Apache-2.0", "BSD-3-Clause", "BSD-2-Clause", "MPL-2.0"})


class EinbetterError(ValueError):
    """Ein Einbetter ist unbekannt oder unter Regel 1 nicht zulässig."""


@dataclass(frozen=True)
class Einbetter:
    """Ein Bild-Einbettungsmodell samt Lizenzlage.

    `zulaessig` ist bewusst ein eigenes Feld und nicht aus `lizenz` abgeleitet: Bei
    DINOv3 ist die Begründung länger als „Lizenz nicht in der Liste", und sie soll am
    Modell stehen, nicht im Kopf des Lesers.
    """

    name: str
    modell_id: str
    lizenz: str
    zulaessig: bool
    begruendung: str
    dimension: int
    gated: bool = False
    #: Wie gut die Lizenzangabe belegt ist: eine Vokabel aus
    #: :mod:`aiimaging.lizenzquelle` oder ein Vermerk ``"geprueft <datum> (<url>)"``.
    lizenz_quelle: str = QUELLE_UNGEPRUEFT


EINBETTER: dict[str, Einbetter] = {
    "siglip2-base": Einbetter(
        name="siglip2-base",
        modell_id="google/siglip2-base-patch16-224",
        lizenz="Apache-2.0",
        zulaessig=True,
        begruendung="Apache-2.0, nicht gated, keine Auflagen — erfüllt Regel 1 unmittelbar.",
        dimension=768,
        # Modellkarte am 2026-08-18 selbst gelesen: Front-Matter "license: apache-2.0",
        # Repo offen (nicht gated).
        lizenz_quelle="geprueft 2026-08-18 (https://huggingface.co/google/siglip2-base-patch16-224)",
    ),
    "dinov2-base": Einbetter(
        name="dinov2-base",
        modell_id="facebook/dinov2-base",
        lizenz="Apache-2.0",
        zulaessig=True,
        begruendung=(
            "Apache-2.0. Der unmittelbare Vorgänger von DINOv3 und dessen lizenzsaubere "
            "Alternative — selbstüberwacht trainiert, also näher an DINOv3s Verhalten als "
            "ein Sprache-Bild-Modell."
        ),
        dimension=768,
        # Modellkarte am 2026-08-18 selbst gelesen: Front-Matter "license: apache-2.0",
        # Repo offen (nicht gated) — anders als DINOv3 desselben Herausgebers.
        lizenz_quelle="geprueft 2026-08-18 (https://huggingface.co/facebook/dinov2-base)",
    ),
    "openclip-vit-b32": Einbetter(
        name="openclip-vit-b32",
        modell_id="laion/CLIP-ViT-B-32-laion2B-s34B-b79K",
        lizenz="MIT",
        zulaessig=True,
        begruendung="MIT. Grosses Ökosystem, gut dokumentiert, keine Auflagen.",
        dimension=512,
        # Modellkarte am 2026-08-18 selbst gelesen: Front-Matter "license: mit".
        # Eine eigene LICENSE-Datei führt das Repo nicht — die Modellkarte ist die Quelle.
        lizenz_quelle="geprueft 2026-08-18 (https://huggingface.co/laion/CLIP-ViT-B-32-laion2B-s34B-b79K)",
    ),
    "dinov3": Einbetter(
        name="dinov3",
        modell_id="facebook/dinov3-vitl16",
        lizenz="Meta DINOv3 License (Sonderlizenz)",
        zulaessig=False,
        begruendung=(
            "AUSGESCHLOSSEN unter Regel 1. Keine der vier permissiven Lizenzen, sondern "
            "eine Sonderlizenz mit drei Auflagen: gated (Zugang unter Angabe persönlicher "
            "Daten), Pflicht zur Nennung 'Built with DINOv3', und Weitergabe nur samt "
            "Lizenztext. Kommerzielle Nutzung ist zwar erlaubt — Regel 1 verlangt aber "
            "permissiv, nicht bloss erlaubt. Für ein öffentliches Repo zudem unpraktisch: "
            "Eine gated Abhängigkeit kann niemand nachvollziehen. "
            "KosmoVis verwendet es; wir übernehmen das bewusst NICHT."
        ),
        dimension=1024,
        gated=True,
        lizenz_quelle="geprueft 2026-08-18 (ai.meta.com/resources/.../dinov3-license)",
    ),
}

#: Vorgabe. SigLIP 2, weil Apache-2.0 und nicht gated.
VORGABE_EINBETTER = "siglip2-base"


def hole(name: str) -> Einbetter:
    """Einen Einbetter nachschlagen. Unbekannter Name ist ein Fehler, kein ``None``."""
    try:
        return EINBETTER[name]
    except KeyError:
        raise EinbetterError(
            f"Unbekannter Einbetter {name!r}. Bekannt: {', '.join(sorted(EINBETTER))}"
        ) from None


def pruefe_lizenz(name: str) -> dict:
    """Die Lizenzlage eines Einbetters — für den ausführbaren Pfad, nicht nur zum Lesen.

    ``lizenz_belegt`` und ``lizenz_hinweis`` sind am 18.08.2026 dazugekommen. Vorher gab
    dieses Modul die Herkunft nur als Text weiter, und wer wissen wollte, ob sie ein
    Beleg ist, musste selbst auf Zeichenketten suchen. Genau diese Suche ist in
    ``backbone`` schiefgegangen (Prüfbericht Abschnitt 5) — die Antwort gehört darum als
    Datum in den Satz und nicht in die Auswertung jedes Aufrufers.

    ``lizenz_hinweis`` ist ``None``, wenn die Angabe belegt ist; sonst benennt es die
    Lücke. Ein Ausschluss (``zulaessig=False``) bleibt davon unberührt: Belegt oder nicht,
    die Registry entscheidet über die Zulässigkeit, dieses Feld nur über die Beweislage.
    """
    e = hole(name)
    return {
        "regel_1_spannung": lizenzquelle.regel_1_spannung(e.name, e.lizenz, e.zulaessig),
        "name": e.name,
        "lizenz": e.lizenz,
        "zulaessig": e.zulaessig,
        "gated": e.gated,
        "begruendung": e.begruendung,
        "lizenz_quelle": e.lizenz_quelle,
        "lizenz_belegt": ist_belegt(e.lizenz_quelle),
        "lizenz_hinweis": hinweis_zur_herkunft(e.lizenz_quelle),
    }


def waehle(*, nur_zulaessige: bool = True) -> list[Einbetter]:
    """Die verwendbaren Einbetter.

    Mit ``nur_zulaessige=True`` (Vorgabe) erscheint DINOv3 **nicht** — Regel 1 in
    ausführbarer Form, wie bei :func:`aiimaging.backbone.waehle`.
    """
    kandidaten = list(EINBETTER.values())
    if nur_zulaessige:
        kandidaten = [e for e in kandidaten if e.zulaessig]
    return kandidaten


def fordere_zulaessigen(name: str) -> Einbetter:
    """Einen Einbetter holen und ablehnen, wenn er unter Regel 1 nicht zulässig ist.

    Raises:
        EinbetterError: mit der vollen Begründung aus der Registry — nicht nur „geht
            nicht", sondern warum.
    """
    e = hole(name)
    if not e.zulaessig:
        raise EinbetterError(f"{e.name} ist unter Regel 1 nicht zulässig: {e.begruendung}")
    return e
