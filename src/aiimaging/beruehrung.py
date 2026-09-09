"""Ob eine spätere Änderung eine veröffentlichte Messung **berührt**.

Die Hälfte, die der Stempel nicht abdeckt
-----------------------------------------
:mod:`aiimaging.messstand` verbindet eine Messung mit dem Commit, auf dem sie steht. Das
beantwortet die Frage *«Fahre ich dieselbe Software?»* — und **nur** die. Die schwierigere
Frage stellte sich am 01.09.2026 und blieb acht Tage lang ungestellt:

    Ich habe `kameras.py` geändert. **Welche veröffentlichten Zahlen gehen mich das an?**

Am 01.09. lautete die Antwort: sieben Dokumente. Gemerkt hat es niemand, weil niemand
danach gesucht hat — und weil es nichts gab, wonach man hätte suchen können.

Was dieses Modul kann, und was nicht
------------------------------------
Es zählt auf, **welche Kernmodule** sich zwischen dem Stand eines Dokuments und heute
geändert haben, und hält das gegen die **Grundlage**, die das Dokument selbst nennt::

    **Grundlage:** kameras, maske, tiefenschaetzer

Daraus werden drei Antworten — und die dritte ist die wichtigste:

======================  =====================================================
``unberuehrt``          Kein Modul der genannten Grundlage hat sich geändert.
``beruehrt``            Mindestens eines hat sich geändert; welches, steht dabei.
``nicht feststellbar``  Das Dokument nennt keine Grundlage, oder sein Stand ist
                        in diesem Repo nicht auffindbar.
======================  =====================================================

**Ein Dokument ohne Grundlage gilt nicht als unberührt.** Das ist der ganze Unterschied
zwischen diesem Modul und einem, das nur beruhigt: Wer nichts angibt, bekommt kein «alles
in Ordnung», sondern die Liste dessen, was sich überhaupt bewegt hat, und darf selbst
nachsehen.

**«Berührt» heisst ansehen, nicht falsch.** Gezählt wird je **Modul**, und ein Modul ist
gröber als eine Zahl: Die erste Meldung dieses Werkzeugs betraf ein Dokument, dessen
Grundlage sich geändert hatte — an der **Anlauffrist einer Prozesswache**, also an etwas,
das nicht ändert, was gerechnet wird. Die Meldung war trotzdem richtig. *Ein Werkzeug, das
nur meldet, was sicher falsch ist, meldet fast nie etwas — und dann verlässt sich niemand
mehr darauf, dass Schweigen etwas heisst.*

*Und die zweite Grenze gehört dazugesagt:* Die Grundlage ist eine **Angabe des Verfassers**, keine
Messung. Wer ein Modul vergisst, bekommt ein `unberuehrt`, das nichts wert ist. Das lässt
sich nicht abfangen, ohne die Abhängigkeiten einer Messung zu verfolgen — und das kann
dieses Repo heute nicht. Es steht hier, damit niemand mehr aus dem Wort schliesst, als
darin ist.
"""

from __future__ import annotations

import re
import subprocess
from datetime import date
from pathlib import Path

from aiimaging import messstand

#: Die Zeile, mit der ein Dokument sagt, worauf seine Zahlen stehen.
MARKE_GRUNDLAGE = "**Grundlage:**"

#: Die Zeile, mit der ein Dokument sagt, bis wohin jemand **hingesehen** hat.
#:
#: Ohne sie meldet dieses Werkzeug ein einmal berührtes Dokument bis in alle Ewigkeit —
#: auch dann, wenn längst jemand nachgesehen und festgestellt hat, dass die Änderung die
#: Zahlen nicht bewegt. *Ein Wächter, der nach der Klärung weiterruft, wird abgestellt,
#: und dann ruft er auch beim nächsten Mal nicht.* Wer nachsieht, trägt den Stand ein, bis
#: zu dem er gesehen hat; gemessen wird ab da.
MARKE_NACHGESEHEN = "**Nachgesehen bis:**"

#: Ab diesem Tag muss ein Messdokument seine Grundlage nennen.
#:
#: Einen Tag nach :data:`aiimaging.messstand.STICHTAG`, und aus demselben Grund wie dort:
#: Welche Module eine Messung vom Vortag trägt, liesse sich nur vermuten. *Eine Regel
#: rückwirkend mit Vermutungen zu erfüllen ist schlimmer, als sie erst ab morgen zu
#: haben.* Wo die Grundlage nachträglich **feststellbar** war — aus den Importen des
#: Skripts, das ein Dokument nachbaubar macht —, wurde sie trotzdem eingetragen. Das ist
#: kein Widerspruch: Sie steht dort abgelesen und nicht geraten.
STICHTAG_GRUNDLAGE = date(2026, 9, 10)

#: Wo der Kern liegt. Änderungen ausserhalb (Werkzeuge, Dokumente, Proben) berühren eine
#: Messung nicht — sie ändern nicht, was gerechnet wird.
KERN = "src/aiimaging"

#: Die drei Antworten.
UNBERUEHRT = "unberuehrt"
BERUEHRT = "beruehrt"
UNKLAR = "nicht feststellbar"

_MODULNAME = re.compile(r"[a-z_][a-z0-9_]*")


class BeruehrungError(ValueError):
    """Die Frage liess sich nicht stellen — nicht: sie wurde mit «nein» beantwortet."""


def _git(argumente: list[str], repo) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(["git", "-C", str(repo), *argumente],
                              capture_output=True, text=True, timeout=30, check=False)
    except (OSError, subprocess.SubprocessError) as fehler:
        raise BeruehrungError(f"git nicht aufrufbar: {fehler}") from fehler


def _wurzel(repo=None) -> Path:
    return Path(repo) if repo else Path(__file__).resolve().parents[2]


def stand_aus_dokument(pfad) -> str | None:
    """Der Commit, den ein Dokument in seiner Codestand-Zeile nennt — oder ``None``."""
    text = Path(pfad).read_text(encoding="utf-8", errors="ignore")
    for zeile in text.splitlines():
        if zeile.startswith(messstand.MARKE):
            treffer = re.search(r"`([0-9a-f]{7,40})`", zeile)
            return treffer.group(1) if treffer else None
    return None


def nachgesehen_aus_dokument(pfad) -> str | None:
    """Der Stand, bis zu dem jemand dieses Dokument durchgesehen hat — oder ``None``."""
    text = Path(pfad).read_text(encoding="utf-8", errors="ignore")
    for zeile in text.splitlines():
        if zeile.startswith(MARKE_NACHGESEHEN):
            treffer = re.search(r"`([0-9a-f]{7,40})`", zeile)
            return treffer.group(1) if treffer else None
    return None


def grundlage_aus_dokument(pfad) -> list[str] | None:
    """Die Module, auf die sich ein Dokument beruft — oder ``None``, wenn es keine nennt.

    ``None`` und ``[]`` sind **nicht** dasselbe: ``None`` heisst «nicht gesagt», ``[]``
    heisst «ausdrücklich keines» — geschrieben als ``**Grundlage:** keine``. Eine leere
    Zeile ist dagegen keine Angabe und zählt wie eine fehlende.
    """
    text = Path(pfad).read_text(encoding="utf-8", errors="ignore")
    for zeile in text.splitlines():
        if zeile.startswith(MARKE_GRUNDLAGE):
            rest = zeile[len(MARKE_GRUNDLAGE):]
            # Nur was in Grave-Akzenten steht oder als blosser Name dasteht — der Satz
            # dahinter («, alle drei ueber die Prozessgrenze») ist Prosa und kein Modul.
            rest = rest.split("—")[0].split(" - ")[0]
            namen = [n for n in _MODULNAME.findall(rest.replace("`", " ").lower())]
            # «keine» ist eine ANGABE und keine fehlende Angabe. Ein Dokument, das nichts
            # aus unserem Kern misst — eine Literaturdurchsicht etwa —, trägt trotzdem
            # eine Codestand-Zeile, weil die Regel sie an das Datum im Namen knüpft. Ohne
            # dieses Wort stünde es für immer unter «nicht feststellbar», und eine Liste,
            # in der Unklarheiten stehen, die keine sind, liest bald niemand mehr.
            if namen == ["keine"]:
                return []
            return namen or None
    return None


def geaenderte_module(seit: str, bis: str = "HEAD", repo=None) -> list[str]:
    """Welche Kernmodule sich zwischen zwei Ständen geändert haben.

    Raises:
        BeruehrungError: Einer der beiden Stände ist in diesem Repo nicht auffindbar.
            **Kein leeres Ergebnis in diesem Fall** — eine leere Liste heisst hier «nichts
            hat sich geändert», und das wäre die falscheste aller Antworten auf «diesen
            Commit kenne ich nicht».
    """
    wurzel = _wurzel(repo)
    for stand in (seit, bis):
        pruefung = _git(["rev-parse", "--verify", f"{stand}^{{commit}}"], wurzel)
        if pruefung.returncode != 0:
            raise BeruehrungError(
                f"Stand {stand!r} ist in {wurzel} nicht auffindbar. Möglich ist beides: "
                f"ein Tippfehler, oder ein Commit, den dieses Arbeitsverzeichnis nie "
                f"gesehen hat. Was davon, sagt niemand — und darum wird hier nicht "
                f"geraten.")
    lauf = _git(["diff", "--name-only", f"{seit}..{bis}", "--", KERN], wurzel)
    if lauf.returncode != 0:
        raise BeruehrungError(f"git diff schlug fehl: {lauf.stderr.strip() or 'leer'}")

    module = set()
    for pfad in lauf.stdout.splitlines():
        p = Path(pfad.strip())
        if p.suffix == ".py" and p.name != "__init__.py":
            module.add(p.stem)
    return sorted(module)


def beruehrung(dokument, *, bis: str = "HEAD", repo=None) -> dict:
    """Berührt die Entwicklung seit dem Stand dieses Dokuments seine Zahlen?

    Returns:
        ``{datei, stand, grundlage, geaendert, betroffen, zustand, grund}``.
        ``zustand`` ist :data:`UNBERUEHRT`, :data:`BERUEHRT` oder :data:`UNKLAR`.
    """
    pfad = Path(dokument)
    stand = stand_aus_dokument(pfad)
    nachgesehen = nachgesehen_aus_dokument(pfad)
    grundlage = grundlage_aus_dokument(pfad)
    # Gemessen wird ab dem SPÄTEREN der beiden Stände. Wer nachgesehen hat, hat die
    # Strecke davor erledigt; sie noch einmal zu melden hiesse, seine Arbeit zu ignorieren.
    von = nachgesehen or stand
    satz = {"datei": pfad.name, "stand": stand, "nachgesehen": nachgesehen, "von": von,
            "grundlage": grundlage, "geaendert": [], "betroffen": [],
            "zustand": UNKLAR, "grund": ""}

    if stand is None:
        satz["grund"] = (f"Das Dokument nennt keinen Codestand ({messstand.MARKE}). "
                         f"Ohne Anfangspunkt gibt es keine Strecke, die man ansehen kann.")
        return satz

    try:
        geaendert = geaenderte_module(von, bis, repo)
    except BeruehrungError as fehler:
        satz["grund"] = str(fehler)
        return satz
    satz["geaendert"] = geaendert

    if grundlage is None:
        satz["grund"] = (
            f"Das Dokument nennt keine Grundlage ({MARKE_GRUNDLAGE} <Module>). Seit "
            f"`{von}` haben sich {len(geaendert)} Kernmodule geändert; ob eines davon "
            f"diese Messung trägt, kann nur der Verfasser sagen. "
            f"**Das ist nicht «unberührt».**")
        return satz

    if not grundlage:
        satz["zustand"] = UNBERUEHRT
        satz["grund"] = ("Das Dokument beruft sich ausdrücklich auf kein Kernmodul "
                         f"({MARKE_GRUNDLAGE} keine). Was sich im Kern ändert, geht es "
                         "nichts an.")
        return satz

    betroffen = sorted(set(grundlage) & set(geaendert))
    satz["betroffen"] = betroffen
    if betroffen:
        satz["zustand"] = BERUEHRT
        satz["grund"] = (f"Seit `{von}` geändert: {', '.join(betroffen)} — und genau "
                         f"darauf beruft sich dieses Dokument.")
    else:
        satz["zustand"] = UNBERUEHRT
        nachsatz = (f" (nachgesehen bis `{nachgesehen}`)" if nachgesehen else "")
        satz["grund"] = (f"Keines der genannten Module ({', '.join(grundlage)}) hat sich "
                         f"seit `{von}` geändert{nachsatz}. Gilt nur, soweit die Grundlage "
                         f"vollständig angegeben ist — sie ist eine Angabe, keine Messung.")
    return satz


def durchsicht(docs_ordner, *, bis: str = "HEAD", repo=None) -> list[dict]:
    """Alle Dokumente mit Codestand-Zeile, jedes mit seiner Antwort.

    Sortiert: erst das Berührte, dann das Unklare, dann das Unberührte. *Wer eine Liste
    von oben liest, soll oben das finden, was er ansehen muss.*
    """
    ordner = Path(docs_ordner)
    reihe = {BERUEHRT: 0, UNKLAR: 1, UNBERUEHRT: 2}
    ergebnisse = [beruehrung(p, bis=bis, repo=repo)
                  for p in sorted(ordner.glob("*.md"))
                  if messstand.MARKE in p.read_text(encoding="utf-8", errors="ignore")]
    return sorted(ergebnisse, key=lambda s: (reihe[s["zustand"]], s["datei"]))


def ohne_grundlage(docs_ordner) -> list[str]:
    """Messdokumente ab :data:`STICHTAG_GRUNDLAGE`, die ihre Grundlage nicht nennen.

    Gesucht wird nach denselben Regeln wie in :func:`aiimaging.messstand.ohne_codestand`
    — Datum im Namen, dieselbe Ausnahmeliste. Zwei Wächter, ein Begriff von «Messdokument»:
    Liefen sie nach verschiedenen Regeln, hiesse dasselbe Wort an zwei Stellen zweierlei.
    """
    ordner = Path(docs_ordner)
    fehlend = []
    for p in sorted(ordner.glob("*.md")):
        if p.name in messstand.AUSNAHMEN:
            continue
        wann = messstand._datum_im_namen(p.name)
        if wann is None or wann < STICHTAG_GRUNDLAGE:
            continue
        if MARKE_GRUNDLAGE not in p.read_text(encoding="utf-8", errors="ignore"):
            fehlend.append(p.name)
    return fehlend


__all__ = ["BERUEHRT", "KERN", "MARKE_GRUNDLAGE", "MARKE_NACHGESEHEN",
           "STICHTAG_GRUNDLAGE", "UNBERUEHRT", "UNKLAR", "BeruehrungError", "beruehrung",
           "durchsicht", "geaenderte_module", "grundlage_aus_dokument",
           "nachgesehen_aus_dokument", "ohne_grundlage", "stand_aus_dokument"]
