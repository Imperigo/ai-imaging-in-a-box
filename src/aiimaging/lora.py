"""LoRA-Stiltraining als **Subprozess** — die Stelle, an der Regel 1 und Regel 3 sich treffen.

Warum es dieses Modul gibt
--------------------------
`docs/PLAN.md` nennt unter Phase 4: *„LoRA-Stiltraining über kohya oder ai-toolkit als
Subprozess"*. Ein LoRA ist eine kleine Zusatzschicht zu einem Bildmodell, die einen Stil
trägt — für ein Architekturbüro der eigentliche Wert der ganzen Kette: das Modell malt
dann *im eigenen Haus-Stil*, nicht in dem des Internets.

Genau darum ist diese Naht die heikelste im Projekt. **Sie ist die einzige Stelle, an der
beide harten Regeln gleichzeitig greifen — und beide müssen ausführbar sein, nicht bloss
aufgeschrieben.**

Regel 1: Ein LoRA erbt die Lizenz seiner Grundlage
---------------------------------------------------
Ein LoRA ist ohne sein Grundmodell nutzlos — es ist eine Differenz zu dessen Gewichten.
`CLAUDE.md` zieht daraus die Folge ausdrücklich:

    „Modellgewichte zählen mit: Non-Commercial-Lizenzen (FLUX.1-dev, FLUX.2-dev) sind
    ausgeschlossen, **auch für daraus abgeleitete LoRAs**."

Ein auf FLUX-dev trainierter Haus-Stil ist also nicht verkaufbar — und das merkt man
normalerweise erst, wenn die GPU-Stunden schon bezahlt sind. :func:`pruefe_auftrag` lehnt
solche Aufträge **vor** dem ersten Rechenschritt ab, so wie
``backbone.waehle(kommerziell=True)`` FLUX-dev gar nicht erst anbietet.

Regel 3: Trainingsdaten sind das genaue Gegenteil von synthetisch
------------------------------------------------------------------
Ein Stil-LoRA wird auf **echten Bildern des Büros** trainiert. Das ist sein Zweck. Und
genau das darf nach Regel 3 nie ins Repo:

    „Keine Bürodaten, keine Kundenprojekte … Keine LoRAs oder Checkpoints, die auf solchen
    Daten trainiert wurden. Auch keine Büro-, Kunden- oder Projektnamen in Pfaden."

Dieses Modul weist darum einen Datensatz **innerhalb des Repos** ab — nicht als Warnung,
sondern als Fehler. Das ist dieselbe ausführbare Form wie ``auftrag._wehre_bilddaten_ab``:
Eine Regel, die nur in einer Datei steht, wird an einem müden Abend gebrochen.

Regel 2 und 4: die Prozessgrenze, ein drittes Mal
--------------------------------------------------
Der Trainer läuft als eigener Prozess in eigenem Environment, wie Blender und
IfcOpenShell. Das ist hier keine Lizenznotwendigkeit — kohya ist Apache-2.0, ai-toolkit
ist MIT, beide am Original geprüft (18.08.2026) — sondern eine praktische: Ein Trainer
zieht `torch`, `accelerate`, `bitsandbytes` und die halbe CUDA-Laufzeit nach. Nichts
davon gehört in ein Produkt-venv, das mit **null** Laufzeitabhängigkeiten auskommt.

Was dieses Modul NICHT leistet
-------------------------------
**Es hat nie ein Training ausgeführt.** Hier gibt es keine GPU, keine Gewichte und keinen
Trainer. Gebaut ist der Vertrag: die Prüfung, das Kommando, die Naht. Ob die
Kommandozeilen der beiden Trainer in ihrer heutigen Fassung genau so heissen, ist aus
deren Dokumentation übernommen und **nicht gemessen** — jeder Eintrag sagt das im Feld
``beleg``. Das ist derselbe Vorbehalt wie bei ``herkunft.HERKUENFTE``, und er wird
genauso aufgelöst: von jemandem, der das Gerät hat.
"""
from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from aiimaging import backbone

#: Umgebungsvariable für das Python des Trainer-Environments.
UMGEBUNG_TRAINER_PYTHON = "AIIMAGING_LORA_PYTHON"

#: Umgebungsvariable für das Verzeichnis, in dem der Trainer selbst liegt.
UMGEBUNG_TRAINER_WURZEL = "AIIMAGING_LORA_TRAINER"


class LoraError(ValueError):
    """Ein Trainingsauftrag verletzt den Vertrag — oder der Lauf ist gescheitert."""


@dataclass(frozen=True)
class Trainer:
    """Ein LoRA-Trainer samt Lizenzlage und Aufrufform.

    ``beleg`` trennt Geprüftes von Übernommenem. Die **Lizenz** ist am Original gelesen;
    die **Kommandozeile** stammt aus der Dokumentation und ist hier nie ausgeführt worden.
    Beides in einem Feld zu führen wäre die Art Ungenauigkeit, die dieses Projekt schon
    zweimal Geld gekostet hat.
    """

    name: str
    lizenz: str
    lizenz_quelle: str
    skript: str
    #: Wie ein benannter Parameter auf der Kommandozeile heisst.
    flaggen: dict[str, str]
    beleg: str


TRAINER: dict[str, Trainer] = {
    "kohya": Trainer(
        name="kohya",
        lizenz="Apache-2.0",
        lizenz_quelle=("geprueft 2026-08-18 "
                       "(https://raw.githubusercontent.com/kohya-ss/sd-scripts/main/LICENSE)"),
        skript="sdxl_train_network.py",
        flaggen={
            "basis": "--pretrained_model_name_or_path",
            "datensatz": "--train_data_dir",
            "ausgabe": "--output_dir",
            "rang": "--network_dim",
            "schritte": "--max_train_steps",
            "lernrate": "--learning_rate",
            "aufloesung": "--resolution",
            "seed": "--seed",
        },
        beleg=("Lizenz am Original gelesen. Die Flaggennamen stammen aus der "
               "Projektdokumentation und sind hier NIE ausgeführt worden — dieses "
               "Environment hat weder GPU noch Trainer."),
    ),
    "ai-toolkit": Trainer(
        name="ai-toolkit",
        lizenz="MIT",
        lizenz_quelle=("geprueft 2026-08-18 "
                       "(https://raw.githubusercontent.com/ostris/ai-toolkit/main/LICENSE)"),
        skript="run.py",
        flaggen={},
        beleg=("Lizenz am Original gelesen (MIT, Copyright 2024 Ostris, LLC). "
               "ai-toolkit wird über eine YAML-Konfiguration gesteuert, nicht über "
               "Flaggen — darum ist `flaggen` leer und `baue_kommando` verweigert hier "
               "die Auskunft, statt eine Kommandozeile zu erfinden."),
    ),
}

#: Vorgabe. kohya, weil seine Kommandozeile dokumentiert und abbildbar ist.
VORGABE_TRAINER = "kohya"


@dataclass(frozen=True)
class LoraAuftrag:
    """Ein Trainingsauftrag — alles, was einen Stil-LoRA vollständig bestimmt.

    Args:
        basis: Name aus :data:`aiimaging.backbone.BACKBONES`. **Kein freier Text** — der
            Eintrag entscheidet über die Lizenz des Ergebnisses, siehe
            :func:`lizenz_des_ergebnisses`.
        datensatz: Verzeichnis mit den Trainingsbildern. Liegt **auf dem Rechner, der
            trainiert**, nie im Repo (Regel 3).
        ausgabe: Wohin der LoRA geschrieben wird. Ebenfalls nie im Repo.
        rang: „Dicke" der Zusatzschicht. Klein heisst wenig Kapazität und wenig
            Überanpassung, gross das Gegenteil. Gehört ins Ergebnis: Ohne ihn ist ein
            Trainingslauf nicht wiederholbar.
        seed: Startwert. Aus demselben Grund Pflicht wie bei ``render.RenderAuftrag``.

    ``frozen=True``: Ein Auftrag ist das Protokoll dessen, was gerechnet wurde.
    """

    basis: str
    datensatz: str
    ausgabe: str
    trainer: str = VORGABE_TRAINER
    rang: int = 16
    schritte: int = 1500
    lernrate: float = 1e-4
    aufloesung: int = 1024
    seed: int = 0
    zusatzflaggen: tuple[str, ...] = field(default_factory=tuple)


def hole_trainer(name: str) -> Trainer:
    """Einen Trainer nachschlagen. Unbekannter Name ist ein Fehler, kein ``None``."""
    try:
        return TRAINER[name]
    except KeyError:
        raise LoraError(
            f"Unbekannter Trainer {name!r}. Bekannt: {', '.join(sorted(TRAINER))}"
        ) from None


def lizenz_des_ergebnisses(basis: str) -> dict:
    """Welche Lizenz trägt der **fertige LoRA**? — die Frage, die niemand rechtzeitig stellt.

    Ein LoRA ist eine Differenz zu den Gewichten seiner Grundlage und ohne sie nutzlos.
    Er erbt darum deren Lizenzlage. Ein auf einem Non-Commercial-Modell trainierter
    Haus-Stil ist nicht verkaufbar — und zwar unabhängig davon, wem die Trainingsbilder
    gehören und wieviel Rechenzeit hineinging.

    ``CLAUDE.md`` sagt das ausdrücklich („auch für daraus abgeleitete LoRAs"); hier steht
    es ausführbar.

    Returns:
        ``{basis, basis_lizenz, lora_lizenz, verkaufbar, begruendung, regel_1_spannung}``.
    """
    lizenz = backbone.pruefe_lizenz(basis)
    verkaufbar = bool(lizenz["zulaessig"])
    if verkaufbar:
        begruendung = (
            f"Der LoRA erbt die Lage von {basis}: '{lizenz['lizenz']}'. "
            + (lizenz["begruendung"] or "")
        )
    else:
        begruendung = (
            f"Der LoRA wäre NICHT verwertbar. Er erbt die Lage von {basis}: "
            f"'{lizenz['lizenz']}'. {lizenz['begruendung']} Ein Stil, der auf einer "
            f"nicht verwertbaren Grundlage sitzt, ist genauso wenig verkaufbar wie sie — "
            f"und das ändert sich weder durch eigene Trainingsbilder noch durch "
            f"Rechenzeit."
        )
    return {
        "basis": basis,
        "basis_lizenz": lizenz["lizenz"],
        "lora_lizenz": lizenz["lizenz"],
        "verkaufbar": verkaufbar,
        "begruendung": begruendung,
        "auflagen": lizenz.get("auflagen", []),
        "regel_1_spannung": lizenz.get("regel_1_spannung"),
    }


def _repo_wurzel() -> Path:
    return Path(__file__).resolve().parents[2]


def liegt_im_repo(pfad) -> bool:
    """Liegt dieser Pfad innerhalb des Projektverzeichnisses?

    Aufgelöst wird über :meth:`Path.resolve`, damit ein ``..``-Umweg oder eine
    symbolische Verknüpfung die Prüfung nicht aushebelt. Das ist dieselbe Sorgfalt wie
    bei der Pfad-Trickserei-Abwehr in ``jobs.py``: Wer eine Regel ausführbar macht, muss
    auch den bequemen Weg daran vorbei schliessen.
    """
    try:
        Path(pfad).resolve().relative_to(_repo_wurzel())
        return True
    except (ValueError, OSError, TypeError):
        # TypeError kam am 18.08. bei der Testabnahme dazu: `datensatz=None` liess
        # `Path(None)` fliegen, und `pruefe_auftrag` warf statt eine Mängelliste zu
        # liefern — das Gegenteil dessen, was es zusagt. Ein unbrauchbarer Pfad ist
        # nicht „im Repo", sondern unbrauchbar; das sagt die Typprüfung unten.
        return False


def pruefe_modell_wurzel(basis: str, modell_wurzel) -> str | None:
    """Zeigt ``modell_wurzel`` überhaupt auf die Gewichte, über die geurteilt wurde?

    **Das Loch, das die Testabnahme fand (18.08.2026), und es sass in einer Regel, die
    ausführbar sein sollte:** :func:`lizenz_des_ergebnisses` urteilt über den *Namen*
    ``basis``. ``modell_wurzel`` zeigt auf die *tatsächlichen* Gewichte — und wurde
    nirgends dagegen gehalten. Damit lief das hier anstandslos durch::

        baue_kommando(LoraAuftrag(basis="qwen-image-edit-2511", ...),
                      modell_wurzel="/ai/flux1-dev")

    Ergebnis: eine vollständige Kommandozeile mit ``--pretrained_model_name_or_path
    /ai/flux1-dev`` — trainiert auf einem Non-Commercial-Modell, ausgewiesen als
    ``verkaufbar=True``. Regel 1 war gegen den müden Abend abgesichert, aber nicht gegen
    jemanden, der ``modell_wurzel`` kennt.

    **Was diese Prüfung leistet und was nicht.** Sie vergleicht den Verzeichnisnamen mit
    dem Registry-Namen. Das ist eine **Namensprüfung, keine Inhaltsprüfung** — was
    wirklich in dem Verzeichnis liegt, weiss sie nicht, und wer ein FLUX-Verzeichnis in
    ``qwen-image-edit-2511`` umbenennt, kommt weiterhin durch. Der Riegel richtet sich
    gegen das Versehen und gegen die bequeme Abkürzung, nicht gegen Vorsatz. Das
    aufzuschreiben ist wichtiger, als es zu verschweigen: Eine Prüfung, deren Grenze
    niemand kennt, wird für mehr gehalten, als sie ist.

    Returns:
        Einen Mängelsatz, oder ``None``, wenn nichts einzuwenden ist.
    """
    if modell_wurzel is None:
        return None
    try:
        name = Path(modell_wurzel).resolve().name
    except (TypeError, OSError):
        return f"modell_wurzel: {modell_wurzel!r} ist kein brauchbarer Pfad."
    if name == basis:
        return None
    fremd = name in backbone.BACKBONES
    hinweis = ""
    if fremd:
        lage = backbone.pruefe_lizenz(name)
        hinweis = (f" Das Verzeichnis heisst wie der Registry-Eintrag {name!r} "
                   f"('{lage['lizenz']}', verwertbar: {lage['zulaessig']}) — die "
                   f"Lizenzprüfung lief aber gegen {basis!r}.")
    return (
        f"REGEL 1: `basis` ist {basis!r}, `modell_wurzel` zeigt aber auf ein Verzeichnis "
        f"namens {name!r}.{hinweis} Über die Lizenz des LoRA entscheiden die Gewichte, "
        f"die tatsächlich trainiert werden, nicht der Name im Auftrag. Entweder `basis` "
        f"richtigstellen oder eine Wurzel angeben, die dazu passt. "
        f"(Namensprüfung, keine Inhaltsprüfung — siehe pruefe_modell_wurzel.)"
    )


def pruefe_auftrag(a: LoraAuftrag, *, modell_wurzel=None) -> list[str]:
    """Alle Mängel eines Auftrags — **vor** der ersten GPU-Sekunde.

    Die Reihenfolge ist bindend und dieselbe wie in ``render.rendere``: **Lizenz zuerst.**
    Ein Auftrag auf einer nicht verwertbaren Grundlage soll nicht daran scheitern, dass
    das Datensatzverzeichnis fehlt — er soll an Regel 1 scheitern, auch dann, wenn alles
    andere in Ordnung ist.

    Returns:
        Liste von Klartextsätzen. Leer heisst: nichts eingewendet. **Kein Wahrheitswert** —
        wer ablehnt, soll sagen können, warum, und zwar vollständig statt beim ersten
        Fund abbrechend.
    """
    maengel: list[str] = []
    if not isinstance(a, LoraAuftrag):
        raise LoraError(
            f"pruefe_auftrag braucht einen LoraAuftrag, bekam {type(a).__name__}."
        )

    # 1 — Regel 1, und zwar zuerst.
    try:
        erbe = lizenz_des_ergebnisses(a.basis)
        if not erbe["verkaufbar"]:
            maengel.append(f"REGEL 1: {erbe['begruendung']}")
        elif erbe.get("regel_1_spannung"):
            # Kein Mangel — aber es soll nicht erst nach dem Training auffallen.
            maengel.append(
                f"HINWEIS (kein Abbruch): {erbe['regel_1_spannung']} Der LoRA erbte "
                f"diese Lage."
            )
    except backbone.BackboneError as fehler:
        maengel.append(f"Grundmodell unbekannt: {fehler}")
    if (wurzel_mangel := pruefe_modell_wurzel(a.basis, modell_wurzel)) is not None:
        maengel.append(wurzel_mangel)

    # 2 — Regel 3: Der Datensatz gehört nicht ins Repo.
    if liegt_im_repo(a.datensatz):
        maengel.append(
            f"REGEL 3: Das Datensatzverzeichnis {a.datensatz!r} liegt IM Repo. "
            f"Ein Stil-LoRA wird auf echten Bildern des Büros trainiert — das ist sein "
            f"Zweck und genau das, was nie ins Repo darf. Auch dann nicht, wenn die "
            f"Bilder später wieder gelöscht werden: Die Git-Historie behält sie."
        )
    if liegt_im_repo(a.ausgabe):
        maengel.append(
            f"REGEL 3: Das Ausgabeverzeichnis {a.ausgabe!r} liegt IM Repo. Ein auf "
            f"Bürodaten trainierter LoRA gehört ebenso wenig hinein wie die Bilder "
            f"selbst — `CLAUDE.md` nennt beides in einem Satz."
        )

    # 3 — Der Trainer.
    try:
        trainer = hole_trainer(a.trainer)
        if trainer.lizenz not in ("Apache-2.0", "MIT", "BSD-3-Clause", "BSD-2-Clause",
                                  "MPL-2.0"):
            maengel.append(
                f"REGEL 1: Trainer {trainer.name} steht unter '{trainer.lizenz}' und ist "
                f"keine der vier permissiven Lizenzen."
            )
    except LoraError as fehler:
        maengel.append(str(fehler))

    # 4 — Zahlen, die ein Training überhaupt erst sinnvoll machen.
    for name, wert, unten in (("rang", a.rang, 1), ("schritte", a.schritte, 1),
                              ("aufloesung", a.aufloesung, 64)):
        if not isinstance(wert, int) or isinstance(wert, bool) or wert < unten:
            maengel.append(f"{name}: ganze Zahl ab {unten} erwartet, war {wert!r}.")
    if not isinstance(a.lernrate, (int, float)) or isinstance(a.lernrate, bool) \
            or not 0 < a.lernrate < 1:
        maengel.append(
            f"lernrate: Zahl zwischen 0 und 1 erwartet, war {a.lernrate!r}. Übliche "
            f"Werte liegen bei 1e-4 bis 1e-5."
        )
    for feld in ("datensatz", "ausgabe"):
        if not isinstance(getattr(a, feld), (str, Path)) or not str(getattr(a, feld)).strip():
            maengel.append(f"{feld}: nichtleerer Pfad erwartet, war {getattr(a, feld)!r}.")

    # Zweites Loch aus derselben Testabnahme: `zusatzflaggen` wurde ungeprüft ans Ende
    # gehängt. `("--pretrained_model_name_or_path", "/ai/flux1-dev")` erzeugte ein
    # Kommando, in dem die Flagge zweimal steht — und bei einer argparse-Kommandozeile
    # gewinnt die spätere. Damit hätte man an jeder Prüfung dieses Moduls vorbeitrainiert.
    #
    # Ob kohya das tatsächlich so auswertet, ist hier NICHT gemessen (kein Trainer, keine
    # GPU). Aber eine Flagge, die diese Naht selbst setzt, ein zweites Mal zuzulassen,
    # ist auch ohne Messung eine schlechte Idee: Der Auftrag im Protokoll sagte dann
    # etwas anderes als das Kommando.
    try:
        eigene = set(hole_trainer(a.trainer).flaggen.values())
    except LoraError:
        eigene = set()
    doppelt = sorted(eigene.intersection(str(z) for z in a.zusatzflaggen))
    if doppelt:
        maengel.append(
            f"zusatzflaggen setzt Flaggen erneut, die diese Naht selbst vergibt: "
            f"{', '.join(doppelt)}. Bei einer argparse-Kommandozeile gewinnt die "
            f"spätere — der Auftrag im Protokoll sagte dann etwas anderes als das "
            f"Kommando, und über `--pretrained_model_name_or_path` liesse sich die "
            f"ganze Lizenzprüfung umgehen."
        )
    return maengel


def finde_trainer_python() -> str:
    """Pfad zum Python des Trainer-Environments.

    Bewusst **kein** Rückfall auf ``sys.executable`` — dieselbe Entscheidung wie bei
    ``seams.finde_ifc_python``, und aus demselben Grund: Ein Trainer zieht `torch`,
    `accelerate` und die CUDA-Laufzeit nach. Liefe er im Produkt-Python, wäre das
    Produkt-venv genau das nicht mehr, was ``pyproject.toml`` zusagt — ein Paket ohne
    Laufzeitabhängigkeiten.
    """
    if (env := os.environ.get(UMGEBUNG_TRAINER_PYTHON)):
        return env
    raise LoraError(
        f"Kein Trainer-Environment gefunden. {UMGEBUNG_TRAINER_PYTHON} auf das Python "
        f"eines eigenen venv setzen, in dem der Trainer installiert ist. Ein Rückfall "
        f"auf das Produkt-Python findet bewusst nicht statt — er holte torch und die "
        f"CUDA-Laufzeit in ein Environment, das ohne Abhängigkeiten auskommen soll."
    )


def finde_trainer_wurzel(trainer: Trainer) -> Path:
    """Verzeichnis, in dem der Trainer selbst liegt."""
    if (env := os.environ.get(UMGEBUNG_TRAINER_WURZEL)):
        return Path(env)
    raise LoraError(
        f"Verzeichnis von {trainer.name} nicht bekannt. {UMGEBUNG_TRAINER_WURZEL} setzen."
    )


def baue_kommando(a: LoraAuftrag, *, modell_wurzel=None) -> list[str]:
    """Nur das Kommando bauen, ohne es auszuführen.

    Dieselbe Bauform wie ``seams.baue_kommando_multipass``, und aus demselben Grund: Man
    kann prüfen, ob die Prozessgrenze richtig konstruiert ist, ohne eine GPU zu besitzen.

    Raises:
        LoraError: Der Auftrag hat Mängel, oder der Trainer wird nicht über eine
            Kommandozeile gesteuert. **Für ai-toolkit wird hier bewusst nichts
            zurückgegeben** — es nimmt eine YAML-Konfiguration entgegen, und eine
            erfundene Kommandozeile wäre schlimmer als eine ehrliche Absage.
    """
    if (maengel := pruefe_auftrag(a, modell_wurzel=modell_wurzel)):
        harte = [m for m in maengel if not m.startswith("HINWEIS")]
        if harte:
            raise LoraError("Auftrag abgelehnt: " + " | ".join(harte))

    trainer = hole_trainer(a.trainer)
    if not trainer.flaggen:
        raise LoraError(
            f"{trainer.name} wird nicht über Flaggen gesteuert: {trainer.beleg} Für "
            f"diesen Trainer muss eine Konfigurationsdatei geschrieben werden; dieses "
            f"Modul erfindet dafür keine Kommandozeile."
        )

    # Spät importiert: `render` kennt die Ablage der Gewichte, und die soll an EINER
    # Stelle stehen. Ein Import auf Modulebene wäre trotzdem falsch — dieses Modul soll
    # auch dort lesbar bleiben, wo die Renderstufe gar nicht gebraucht wird.
    from aiimaging import render

    wurzel = Path(modell_wurzel) if modell_wurzel is not None \
        else render.standard_modell_wurzel(a.basis)
    f = trainer.flaggen
    return [
        finde_trainer_python(), str(finde_trainer_wurzel(trainer) / trainer.skript),
        f["basis"], str(wurzel),
        f["datensatz"], str(a.datensatz),
        f["ausgabe"], str(a.ausgabe),
        f["rang"], str(a.rang),
        f["schritte"], str(a.schritte),
        f["lernrate"], str(a.lernrate),
        f["aufloesung"], f"{a.aufloesung},{a.aufloesung}",
        f["seed"], str(a.seed),
        *a.zusatzflaggen,
    ]


def _default_starte(cmd: list[str], timeout: int) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)


def trainiere(a: LoraAuftrag, *, timeout: int = 86400, modell_wurzel=None,
              _starte=None) -> dict:
    """Einen LoRA trainieren — oder begründet ablehnen.

    Args:
        timeout: Vorgabe 24 Stunden. Ein Stiltraining ist das Längste, was diese Kette
            tut; ein knapper Wert bräche einen Lauf kurz vor dem Ziel ab.
        _starte: Die Naht. Dieselbe Bauform wie ``seams._starte`` — mit einer Attrappe
            läuft diese Funktion ohne GPU und ohne Trainer vollständig durch.

    Returns:
        ``{status, lora, lizenz, parameter, maengel, hinweise, error}``. ``status`` ist
        ``abgelehnt``, wenn der Vertrag verletzt ist (**nichts wurde gerechnet**),
        ``fehler``, wenn der Lauf scheiterte, und ``ok`` nur dann, wenn die versprochene
        Datei danach wirklich existiert — dieselbe Nachprüfung wie in ``render.rendere``.
    """
    maengel = pruefe_auftrag(a, modell_wurzel=modell_wurzel)
    harte = [m for m in maengel if not m.startswith("HINWEIS")]
    hinweise = [m for m in maengel if m.startswith("HINWEIS")]
    parameter = {
        "basis": a.basis, "trainer": a.trainer, "rang": a.rang,
        "schritte": a.schritte, "lernrate": a.lernrate,
        "aufloesung": a.aufloesung, "seed": a.seed,
    }
    if harte:
        return {"status": "abgelehnt", "lora": None, "lizenz": None,
                "parameter": parameter, "maengel": harte, "hinweise": hinweise,
                "error": None}

    try:
        cmd = baue_kommando(a, modell_wurzel=modell_wurzel)
    except LoraError as fehler:
        return {"status": "abgelehnt", "lora": None, "lizenz": None,
                "parameter": parameter, "maengel": [str(fehler)], "hinweise": hinweise,
                "error": None}

    starte = _starte or _default_starte
    ergebnis = starte(cmd, timeout)
    if ergebnis.returncode != 0:
        return {"status": "fehler", "lora": None,
                "lizenz": lizenz_des_ergebnisses(a.basis), "parameter": parameter,
                "maengel": [], "hinweise": hinweise,
                "error": (ergebnis.stderr or ergebnis.stdout or "").strip()[-1500:]}

    # Nachsehen statt behaupten — ein Trainer, der 0 meldet und nichts schreibt, ist ein
    # Fehlschlag. Dieselbe Lehre wie überall in diesem Projekt.
    treffer = sorted(Path(a.ausgabe).glob("*.safetensors")) if Path(a.ausgabe).is_dir() else []
    if not treffer:
        return {"status": "fehler", "lora": None,
                "lizenz": lizenz_des_ergebnisses(a.basis), "parameter": parameter,
                "maengel": [], "hinweise": hinweise,
                "error": (f"Der Trainer endete mit 0, aber in {a.ausgabe!r} liegt keine "
                          f"*.safetensors. Die Existenz eines Rückgabewerts ist kein "
                          f"Beleg für eine Datei.")}
    return {"status": "ok", "lora": str(treffer[-1]),
            "lizenz": lizenz_des_ergebnisses(a.basis), "parameter": parameter,
            "maengel": [], "hinweise": hinweise, "error": None}


__all__ = [
    "TRAINER", "UMGEBUNG_TRAINER_PYTHON", "UMGEBUNG_TRAINER_WURZEL", "VORGABE_TRAINER",
    "LoraAuftrag", "LoraError", "Trainer",
    "baue_kommando", "finde_trainer_python", "finde_trainer_wurzel", "hole_trainer",
    "pruefe_modell_wurzel",
    "liegt_im_repo", "lizenz_des_ergebnisses", "pruefe_auftrag", "trainiere",
]
