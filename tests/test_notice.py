"""Das `NOTICE` ist die ausführbare Seite von Regel 1 — also wird es geprüft wie Code.

Warum diese Datei am 26.08.2026 entstand
----------------------------------------
Regel 1 ist die oberste Regel dieses Projekts: permissive Lizenzen, **kein GPL/AGPL**, und
LGPL nur unter drei Auflagen — hinter einer Prozessgrenze, unverändert, austauschbar und
**deklariert**. Deklariert wird im `NOTICE`.

Geprüft war bis dahin die **Herkunft** einer Lizenzangabe in den drei Registries
(`tests/test_lizenzquelle.py`). Das `NOTICE` selbst prüfte nichts — obwohl es die Stelle
ist, an der die Auflagen behauptet werden.

**Der erste Lauf hat sofort etwas gefunden:** Der Eintrag `libquadmath` (LGPL-2.1-or-later)
nennt die Auflagen 2 und 3 wörtlich — *«Unveraendert verwendet, austauschbar»* — und die
**erste nicht**. Nachgezählt wird numpy an genau einer Stelle im Produktpfad importiert,
womit libquadmath den Produktprozess erreicht. Der Eintrag las sich, als wären alle drei
Auflagen erfüllt. Er steht jetzt mit dem, was wirklich gilt, im `NOTICE`.

Was hier geprüft wird, und was nicht
------------------------------------
Geprüft wird, ob eine **Copyleft-Zeile ohne Auflösung** dasteht: Ein Block, dessen Lizenz
GPL, LGPL oder AGPL nennt, muss entweder eine **Prozessgrenze** oder eine **Ausnahme**
benennen, die das Copyleft aufhebt. Beides sind gültige Auflösungen, und beide kommen in
diesem `NOTICE` vor — `libgomp` etwa steht unter GPL-3.0 *mit* GCC-Ausnahme und braucht
keine Grenze.

**Nicht geprüft wird, ob eine Lizenzangabe stimmt.** Das kann nur, wer das Artefakt öffnet;
in diesem Projekt hat das ein Bericht getan (`docs/LIZENZPRUEFUNG_BINAER_2026-08-18.md`, 39
Pakete, 79 Fremdkomponenten). Ein Test, der so täte, wäre eine Behauptung über eine
Behauptung.
"""
from __future__ import annotations

import re
import tomllib
from pathlib import Path

import pytest

WURZEL = Path(__file__).resolve().parents[1]
NOTICE = WURZEL / "NOTICE"

#: Trennlinie zwischen zwei Komponentenblöcken: genau 80 Bindestriche auf einer Zeile.
TRENNER = re.compile(r"^-{80}$", re.M)

#: Was eine Copyleft-Lizenz ist — die Fälle, die Regel 1 einen Riegel entgegensetzt.
COPYLEFT = re.compile(r"\b(?:A?GPL|LGPL)\b")

#: Die Zeile, mit der ein Copyleft-Block seine Auflösung **erklärt** statt sie im
#: Fliesstext anzudeuten.
#:
#: **Warum als Feld und nicht als Wortsuche — nachgewiesen und nicht vermutet.** Der erste
#: Entwurf dieser Datei suchte im Blocktext nach «Prozessgrenze», «Subprozess» und
#: Verwandtem. Die Mutationsprobe hat ihn widerlegt: Der `libgomp`-Block **erklärt im
#: Konjunktiv**, was man täte, wenn die GCC-Ausnahme nicht griffe — *«dann waere der
#: Ausweg derselbe wie zweimal zuvor: ein eigenes Environment und ein Subprozessaufruf»*.
#: Der Wortfilter hielt diesen Konjunktiv für eine Zusage. Nimmt man die Ausnahme aus dem
#: Text heraus, blieb der Test **grün**.
#:
#: *Ein Wächter, der sich von einem Konjunktiv täuschen lässt, bewacht die gefährlichste
#: Stelle nicht: die, an der jemand ausführlich begründet, warum etwas in Ordnung sei.*
MARKE = re.compile(r"^AUFLOESUNG:\s*(\S+)", re.M)

#: Die drei zugelassenen Werte. ``KEINE`` ist ein **benannter offener Punkt** und keine
#: Auflösung — er ist zugelassen, damit ein ungelöster Fall im `NOTICE` sichtbar stehen
#: kann, statt in einem Absatz zu verschwinden.
AUFLOESUNGEN = ("Prozessgrenze", "Lizenzausnahme", "KEINE")

#: Welche Einträge heute **ohne** Auflösung dastehen — mit dem Grund, und einzeln.
#:
#: Dieselbe Bauart und dieselbe Gefahr wie ``ABSICHTLICH`` in `tools/tote_kanten.py`:
#: *Eine wachsende Liste hier ist ein Zeichen dafür, dass weggesehen statt geprüft wird.*
#: Sie ist darum kurz zu halten, und jeder Eintrag ist eine Owner-Frage und kein Freibrief.
OFFEN_UND_BENANNT = {
    "libquadmath": (
        "LGPL-2.1-or-later, statisch im numpy-Wheel. numpy wird an genau EINER Stelle im "
        "Produktpfad importiert (`aiimaging.render`, verzögert, für die Umrechnung einer "
        "16-Bit-Tiefenkarte) — damit erreicht libquadmath den Produktprozess. Nach der "
        "LGPL selbst unproblematisch (unverändert, austauschbar); die Hausregel in "
        "CLAUDE.md ist strenger und verlangt die Prozessgrenze auch hier. Ob sie für eine "
        "LGPL-Komponente gilt, die in einem BSD-3-Wheel mitreist, ist eine Owner-Frage."),
}

#: Blöcke, die keine Komponenten sind: Kopf des Dokuments und leere Abschnitte.
def _bloecke() -> list[str]:
    roh = TRENNER.split(NOTICE.read_text(encoding="utf-8"))
    return [b.strip() for b in roh if b.strip()]


def _kopfzeile(block: str) -> str:
    return block.splitlines()[0].strip()


def _ist_komponente(block: str) -> bool:
    """Der Dokumentkopf ist keine Komponente — er trägt Copyright und Einleitung."""
    return not _kopfzeile(block).startswith("AI Imaging in a Box")


def _komponenten() -> list[str]:
    return [b for b in _bloecke() if _ist_komponente(b)]


def test_es_gibt_ueberhaupt_komponentenbloecke():
    """Ohne diese Zusicherung wäre jede folgende vakuumwahr.

    Ein `NOTICE`, dessen Trennlinien jemand umformatiert, ergäbe genau einen Block — und
    alle Prüfungen darunter liefen über eine leere Liste und wären grün.
    """
    bloecke = _komponenten()
    assert len(bloecke) >= 8, (
        f"Nur {len(bloecke)} Komponentenblöcke gefunden. Entweder ist das `NOTICE` "
        f"geschrumpft, oder die Trennlinie aus 80 Bindestrichen ist es.")


@pytest.mark.parametrize("block", _komponenten(), ids=lambda b: _kopfzeile(b)[:40])
def test_jede_copyleft_zeile_hat_ihre_aufloesung(block):
    """Regel 1, maschinell: GPL/LGPL steht nie unaufgelöst da.

    **Der Fund, für den diese Zusicherung geschrieben wurde:** `libquadmath` nannte
    Unveränderlichkeit und Austauschbarkeit — die Auflagen 2 und 3 — und die Prozessgrenze
    nicht. Ein Eintrag, der zwei von drei Auflagen aufzählt, liest sich wie einer, der
    alle drei erfüllt.
    """
    if not COPYLEFT.search(block):
        pytest.skip("keine Copyleft-Lizenz in diesem Block")
    treffer = MARKE.findall(block)
    assert len(treffer) == 1, (
        f"Der Block {_kopfzeile(block)!r} nennt eine Copyleft-Lizenz und trägt "
        f"{len(treffer)} Zeilen 'AUFLOESUNG:'. Genau eine gehört dorthin — keine heisst "
        f"unerklärt, zwei heisst uneinig.")
    assert treffer[0] in AUFLOESUNGEN, (
        f"{_kopfzeile(block)!r}: unbekannte Auflösung {treffer[0]!r}. Zugelassen sind "
        f"{', '.join(AUFLOESUNGEN)}.")


def test_es_gibt_wirklich_beide_aufloesungen():
    """Die Gegenprobe: Sonst prüfte die Zusicherung oben womöglich nur eine Hälfte.

    Käme im ganzen `NOTICE` nur *eine* der beiden Auflösungen vor, wäre der andere Zweig
    nie gelaufen — und niemand wüsste, dass er nicht trägt. Gemessen am 26.08.2026:
    fünfmal Prozessgrenze, einmal Lizenzausnahme.
    """
    werte = [MARKE.findall(b)[0] for b in _komponenten()
             if COPYLEFT.search(b) and MARKE.findall(b)]
    assert "Prozessgrenze" in werte, "Kein Block löst über die Prozessgrenze auf."
    assert "Lizenzausnahme" in werte, (
        "Kein Block löst über eine Lizenzausnahme auf. Wenn `libgomp` verschwunden ist, "
        "prüft dieser Zweig ab jetzt nichts mehr.")


@pytest.mark.parametrize("block", _komponenten(), ids=lambda b: _kopfzeile(b)[:40])
def test_jeder_ungeloeste_fall_steht_in_der_liste(block):
    """``AUFLOESUNG: KEINE`` ist zugelassen — aber nur benannt, nie im Vorbeigehen.

    Ohne diese Zusicherung wäre die Marke ein Schlupfloch: Man schreibt ``KEINE`` an einen
    neuen Copyleft-Eintrag, der Test ist grün, und der Fund verschwindet in der Datei.
    """
    treffer = MARKE.findall(block)
    if not treffer or treffer[0] != "KEINE":
        pytest.skip("aufgelöst oder kein Copyleft")
    kopf = _kopfzeile(block).split()[0]
    assert kopf in OFFEN_UND_BENANNT, (
        f"{kopf!r} steht mit 'AUFLOESUNG: KEINE' im `NOTICE`, aber nicht in "
        f"OFFEN_UND_BENANNT. Ein ungelöster Copyleft-Fall ist nach CLAUDE.md ausdrücklich "
        f"zu melden — er gehört mit seinem Grund in diese Liste und in die Entscheidliste "
        f"der Sitzung, nicht bloss in einen Absatz.")


def test_die_liste_der_offenen_faelle_ist_nicht_verwaist():
    """Kein Eintrag darf sich auf etwas beziehen, das es nicht mehr gibt.

    Sonst bliebe ein erledigter Fall für immer als offen vermerkt — und die Liste, deren
    Länge das Warnsignal ist, wäre kein Signal mehr.
    """
    text = NOTICE.read_text(encoding="utf-8")
    for name in OFFEN_UND_BENANNT:
        assert name in text, (
            f"{name!r} steht als offener Fall in dieser Datei, kommt im `NOTICE` aber "
            f"nicht mehr vor. Wenn er erledigt ist, gehört auch der Eintrag hier weg.")
    offene = [_kopfzeile(b).split()[0] for b in _komponenten()
              if MARKE.findall(b) and MARKE.findall(b)[0] == "KEINE"]
    assert set(offene) == set(OFFEN_UND_BENANNT), (
        f"Im `NOTICE` offen: {sorted(set(offene))}; in der Liste: "
        f"{sorted(OFFEN_UND_BENANNT)}. Die beiden müssen dasselbe sagen.")


def test_kein_agpl_und_keine_nichtkommerzielle_lizenz_als_bestandteil():
    """Die zwei Fälle, für die Regel 1 keine Auflösung kennt.

    AGPL erstreckt sich über das Netzwerk und ist damit auch hinter einer Prozessgrenze
    nicht eingehegt; eine Non-Commercial-Klausel schliesst den Zweck dieser Arbeit aus.
    **Beide dürfen im `NOTICE` vorkommen — aber nur als ausgeschlossene Funde**, und der
    Ausschluss muss danebenstehen.
    """
    # **Nur die Komponentenblöcke**, nicht der Dokumentkopf. Der nennt seit dem
    # 26.08.2026 «GPL, LGPL, AGPL» als die Lizenzarten, die eine `AUFLOESUNG:`-Zeile
    # tragen — das ist ein Kategoriename und kein Bestandteil. *Der erste Entwurf las die
    # ganze Datei und fiel prompt über den eigenen neuen Kopf: ein Wächter, der die
    # Erklärung seiner selbst für einen Fund hält.*
    text = "\n".join(_komponenten())
    for begriff in ("AGPL", "NonCommercial", "non-commercial", "CC-BY-NC"):
        for treffer in re.finditer(re.escape(begriff), text):
            umfeld = text[max(0, treffer.start() - 400):treffer.end() + 400]
            assert re.search(r"ausgeschlossen|NICHT (?:zulaessig|zulässig|verwendet)|"
                             r"nicht verwertbar|kommt nicht|abgelehnt", umfeld), (
                f"{begriff!r} steht im `NOTICE`, ohne dass in der Nähe steht, dass es "
                f"ausgeschlossen ist. Für diese beiden Fälle kennt Regel 1 keine "
                f"Auflösung — auch keine Prozessgrenze.")


def test_die_zusage_ueber_null_laufzeitabhaengigkeiten_stimmt():
    """Das `NOTICE` behauptet etwas über eine andere Datei im Repo — also wird es geprüft.

    Der Satz *«pyproject.toml fuehrt null Laufzeitabhaengigkeiten»* trägt die ganze
    Begründung dafür, dass `torch` und `diffusers` **keine** Abhängigkeiten dieses Pakets
    sind. Kommt eine einzige Zeile unter ``dependencies``, wird aus der Begründung eine
    falsche Aussage — und zwar an der einen Stelle, an der Dritte sich auf sie verlassen.
    """
    text = NOTICE.read_text(encoding="utf-8")
    assert "null Laufzeitabhaengigkeiten" in text, (
        "Die Zusage steht nicht mehr im `NOTICE`. Wenn sie absichtlich weg ist, gehört "
        "diese Prüfung ebenfalls weg — dann trägt sie nichts mehr.")
    projekt = tomllib.loads((WURZEL / "pyproject.toml").read_text(encoding="utf-8"))
    abhaengigkeiten = projekt["project"].get("dependencies") or []
    assert not abhaengigkeiten, (
        f"Das `NOTICE` sagt «null Laufzeitabhaengigkeiten», `pyproject.toml` führt "
        f"{abhaengigkeiten}. Eine der beiden Stellen ist falsch, und die im `NOTICE` ist "
        f"diejenige, die jemand ausserhalb dieses Repos liest.")


def test_die_belege_die_das_notice_nennt_existieren():
    """Ein Beleg, der auf eine gelöschte Funktion zeigt, ist schlimmer als keiner.

    Dieselbe Prüfung wie in `tests/test_readme.py` — und aus demselben Grund: Das `NOTICE`
    nennt `lora.lizenz_des_ergebnisses` und `pruefe_auftrag` als **ausführbare** Antwort
    auf die Frage, welche Lizenz ein trainiertes LoRA erbt.
    """
    from aiimaging import lora
    text = NOTICE.read_text(encoding="utf-8")
    for name in ("lizenz_des_ergebnisses", "pruefe_auftrag"):
        assert name in text, f"{name!r} steht nicht mehr im `NOTICE`."
        assert callable(getattr(lora, name, None)), (
            f"Das `NOTICE` nennt `aiimaging.lora.{name}` als ausführbaren Beleg, die "
            f"Funktion ist aber nicht aufrufbar.")
