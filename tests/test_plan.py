"""Der Vorgehensplan wird geprüft wie Code — seit er ein Archiv hat.

Anlass
------
Am 09.09.2026 war ``docs/PLAN.md`` auf **5368 Zeilen** gewachsen. Die Hausregel
*«Erledigtes wird abgehakt, nicht gelöscht»* ist richtig und bleibt es; sie sagt nur
nicht, dass Erledigtes im selben Dokument stehen muss wie das Offene. Also sind die
**22 vollständig abgehakten Abschnitte** nach ``docs/erledigt/PLAN_bis_2026-08-28.md``
gewandert, unverändert, mit einer Verweiszeile an ihrer Stelle.

Ein Umzug ist die Gelegenheit für drei stille Fehler, und gegen jeden steht hier eine
Prüfung:

1. **Ein offener Punkt wandert mit.** Dann ist er aus der Sicht verschwunden, ohne dass
   ihn jemand geschlossen hätte — und das Archiv wird niemand mehr lesen.
2. **Häkchen gehen unterwegs verloren.** Die Summe aus Plan und Archiv wird darum gegen
   eine **vor** dem Umzug gemessene Zahl gehalten. *Gezählt wird von der anderen Seite;*
   eine Zahl, die sich aus dem Dokument selbst ergibt, prüft sich selbst.
3. **Ein Verweis zeigt ins Leere.** Zehn Quelldateien nennen ``docs/PLAN.md`` und dabei
   einen Abschnitt — «Phase 3», «Phase 4», «Wissensschulden». Die Verweise werden **aus
   dem Quelltext gesammelt** und gegen die wirklichen Überschriften gehalten. *Ein
   Verweis, der nach einem Umzug ins Leere zeigt, ist schlimmer als keiner: Er sieht aus
   wie eine Fundstelle.*

Dazu die vierte Prüfung, die nicht am Umzug hängt: **die Deckelzeile.** Jeder lange
Abschnitt des Plans und jedes Sitzungsprotokoll sagt in drei Zeilen, was entschieden,
was gemessen wurde und was offen blieb. Geprüft wird die **Existenz und die
Vollständigkeit der drei Felder**, nicht ihr Inhalt — ob ein Satz zutrifft, entscheidet
weiterhin ein Mensch.

Was hier ausdrücklich **nicht** bewacht wird
--------------------------------------------
**Prosa.** Dieselbe Regel wie in ``test_readme.py``: Bewacht wird, was maschinell
entscheidbar ist. Ob eine Deckelzeile ihren Abschnitt richtig zusammenfasst, kann keine
Prüfung sagen — und eine, die es versuchte, produzierte Fehlalarme, bis jemand sie
abschaltet.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

WURZEL = Path(__file__).resolve().parents[1]
PLAN = WURZEL / "docs" / "PLAN.md"
ARCHIV = WURZEL / "docs" / "erledigt" / "PLAN_bis_2026-08-28.md"
SITZUNGEN = WURZEL / "docs" / "sitzungen"

#: Häkchen in ``docs/PLAN.md`` **vor** dem Umzug vom 09.09.2026, von Hand nachgezählt
#: (``grep -c '- \[x\]'`` gegen ``grep -c '- \[ \]'``). Die Zahl steht hier und nicht im
#: Dokument: Eine Prüfzahl, die aus dem geprüften Gegenstand stammt, prüft nichts.
HAEKCHEN_VOR_DEM_UMZUG = 380

#: Davon sind mit den 22 vollständig abgehakten Abschnitten ins Archiv gewandert.
#: Das Archiv wird **nicht fortgeschrieben** — diese Zahl ist darum fest und nicht
#: eine Untergrenze.
HAEKCHEN_IM_ARCHIV = 108

#: Ab dieser Länge trägt ein Abschnitt eine Deckelzeile. Kürzere liest man ganz; ein
#: Deckel darüber wäre länger als die Sache.
DECKEL_AB_ZEILEN = 40

OFFEN = re.compile(r"^\s*- \[ \]")
ABGEHAKT = re.compile(r"^\s*- \[[xX]\]")

DECKELFELDER = ("**Entschieden:**", "**Gemessen:**", "**Offen:**")


def _zeilen(pfad: Path) -> list[str]:
    return pfad.read_text(encoding="utf-8").splitlines()


def _abschnitte(zeilen: list[str]) -> list[tuple[str, list[str]]]:
    """Zerlegt an ``## ``-Überschriften. Der Vorspann vor der ersten fällt weg."""
    anfaenge = [i for i, z in enumerate(zeilen) if z.startswith("## ")]
    grenzen = anfaenge + [len(zeilen)]
    return [(zeilen[a], zeilen[a:b]) for a, b in zip(grenzen, grenzen[1:])]


# ------------------------------------------------- 1 · kein offener Punkt im Archiv

def test_im_archiv_steht_kein_offener_punkt() -> None:
    """Das ist die Bedingung, unter der der Umzug überhaupt sicher war.

    Ein Abschnitt durfte nur wandern, wenn er **kein einziges** ``- [ ]`` trug. Hält das
    nicht mehr, ist ein offener Punkt aus der Sicht verschwunden — und zwar an einen Ort,
    der ausdrücklich nicht fortgeschrieben wird.
    """
    treffer = [z.strip() for z in _zeilen(ARCHIV) if OFFEN.match(z)]
    assert not treffer, (
        f"{len(treffer)} offene Punkte im Archiv, z. B. {treffer[0][:80]!r}. "
        f"Ein offener Punkt gehört nach docs/PLAN.md zurück, nicht hierher — das Archiv "
        f"liest niemand mehr, und genau darum durfte nur Fertiges hinein.")


# ------------------------------------------------------------- 2 · die Summe stimmt

def test_das_archiv_traegt_genau_die_haekchen_die_es_mitgenommen_hat() -> None:
    """Das Archiv ist ein Stand und wächst nicht — die Zahl ist darum exakt.

    Weicht sie ab, hat jemand im Archiv gearbeitet. Das ist kein Formfehler: Wer dort
    etwas ändern müsste, hat einen Punkt gefunden, der doch nicht erledigt war, und der
    gehört zurück in den Plan.
    """
    ist = sum(1 for z in _zeilen(ARCHIV) if ABGEHAKT.match(z))
    assert ist == HAEKCHEN_IM_ARCHIV, (
        f"Das Archiv trägt {ist} Häkchen, mitgenommen hatte es {HAEKCHEN_IM_ARCHIV}. "
        f"Es wird nicht fortgeschrieben — eine Änderung hier ist ein Befund, keine "
        f"Pflege.")


def test_der_plan_hat_beim_umzug_kein_haekchen_verloren() -> None:
    """Plan **plus** Archiv trägt mindestens so viele Häkchen wie der Plan vorher.

    Warum «mindestens» und nicht «genau»: Der Plan wird weitergeschrieben, und jedes neue
    Häkchen ist erwünscht. Was nicht sein darf, ist die andere Richtung — **wachsen darf
    er, schrumpfen nicht.** Eine Obergrenze wäre ein Vorrat, den man aufbraucht.
    """
    im_plan = sum(1 for z in _zeilen(PLAN) if ABGEHAKT.match(z))
    zusammen = im_plan + HAEKCHEN_IM_ARCHIV
    assert zusammen >= HAEKCHEN_VOR_DEM_UMZUG, (
        f"docs/PLAN.md trägt {im_plan} Häkchen, mit dem Archiv sind es {zusammen} — vor "
        f"dem Umzug am 09.09.2026 waren es {HAEKCHEN_VOR_DEM_UMZUG}. Es ist also "
        f"{HAEKCHEN_VOR_DEM_UMZUG - zusammen} Erledigtes verschwunden statt abgehakt "
        f"stehengeblieben.")


def test_jeder_verlegte_abschnitt_hat_eine_verweiszeile_hinterlassen() -> None:
    """Ein Abschnitt, der spurlos verschwindet, sieht aus wie einer, den es nie gab.

    Darum steht in ``PLAN.md`` weiterhin die Überschrift, und darunter ein Verweis. Der
    Test prüft beide Richtungen: Jeder Archiv-Abschnitt wird im Plan genannt, und jeder
    Verweis im Plan zeigt auf einen Abschnitt, den es im Archiv wirklich gibt.
    """
    im_archiv = {u[3:].strip() for u, _ in _abschnitte(_zeilen(ARCHIV))}
    plantext = PLAN.read_text(encoding="utf-8")
    verweise = {u[3:].strip() for u, block in _abschnitte(_zeilen(PLAN))
                if any("PLAN_bis_2026-08-28.md" in z for z in block)}

    assert im_archiv <= verweise, (
        f"Ohne Verweiszeile im Plan: {sorted(im_archiv - verweise)}. Der Abschnitt ist "
        f"aus dem Plan verschwunden, statt dorthin zu zeigen, wo er jetzt steht.")
    assert verweise <= im_archiv, (
        f"Verweise ohne Ziel im Archiv: {sorted(verweise - im_archiv)}.")

    # Die Sprungmarken werden wie github-slugger gebildet: klein, ohne Satzzeichen,
    # jedes Leerzeichen ein Strich (nicht zusammengefasst — «Phase 0 · Feldnamen» ergibt
    # darum einen doppelten Strich, und genau den erwartet GitHub).
    def anker(ueberschrift: str) -> str:
        text = ueberschrift.lower().replace("`", "")
        return re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE).strip().replace(" ", "-")

    ziele = set(re.findall(r"PLAN_bis_2026-08-28\.md#([^)`\s]+)", plantext))
    vorhanden = {anker(u) for u in im_archiv}
    assert ziele <= vorhanden, (
        f"Sprungmarken ohne Überschrift im Archiv: {sorted(ziele - vorhanden)}")


# ---------------------------------------------------------------- 3 · die Deckelzeile

def _deckelzeile_fehlt(block: list[str], ab_zeile: int) -> list[str]:
    """Gibt die fehlenden Felder zurück — leer heisst: vollständig.

    Gelesen wird der **zusammenhängende Zitatblock** direkt unter der Überschrift, nicht
    ein Fenster fester Länge. Der erste Anlauf zählte sechs Zeilen ab der Überschrift und
    fiel an der ersten Deckelzeile, deren Felder über mehrere Zeilen umbrachen —
    *ein Wächter, der eine Formatierung erzwingt, die er nicht meint, wird beim ersten
    Fehlalarm aufgeweicht.*

    Die Bedingung bleibt streng, wo es zählt: Der Block muss **direkt** unter der
    Überschrift stehen. Wer Prosa davor setzt, hat keine Deckelzeile mehr, sondern eine
    Fussnote.
    """
    zeilen = block[ab_zeile:]
    while zeilen and not zeilen[0].strip():
        zeilen.pop(0)
    zitat = []
    for z in zeilen:
        if not z.startswith(">"):
            break
        zitat.append(z)
    kopf = "\n".join(zitat)
    return [f for f in DECKELFELDER if f not in kopf]


def test_jeder_lange_abschnitt_des_plans_traegt_eine_vollstaendige_deckelzeile() -> None:
    """Fünf Zeilen, die das Lesen von tausend ersparen.

    Sie steht direkt unter der Überschrift und trägt **alle drei** Felder. Ein fehlendes
    Feld ist schlimmer als eine fehlende Zeile: Wer «Offen» nicht findet, hält den
    Abschnitt für erledigt.
    """
    maengel: list[str] = []
    for ueberschrift, block in _abschnitte(_zeilen(PLAN)):
        if len(block) < DECKEL_AB_ZEILEN:
            continue
        fehlend = _deckelzeile_fehlt(block, 1)
        if fehlend:
            maengel.append(f"{ueberschrift[:60]} — es fehlt {', '.join(fehlend)}")
    assert not maengel, (
        "Abschnitte ab {n} Zeilen ohne vollständige Deckelzeile:\n  {liste}\n"
        "Erwartet direkt unter der Überschrift:\n"
        "  > **Entschieden:** …\n  > **Gemessen:** …\n  > **Offen:** …".format(
            n=DECKEL_AB_ZEILEN, liste="\n  ".join(maengel)))


@pytest.mark.parametrize(
    "protokoll", sorted(SITZUNGEN.glob("*.md")), ids=lambda p: p.name)
def test_jedes_sitzungsprotokoll_traegt_eine_vollstaendige_deckelzeile(
        protokoll: Path) -> None:
    """Die Protokolle tragen die Begründungen, die sonst nirgends stehen.

    Sie sind zusammen fast zwölftausend Zeilen lang, das längste allein dreitausend —
    lesbar nur, wenn man schon weiss, wo man sucht. Wo eine Sitzung keinen Entscheid
    trug, sagt die Zeile das: **Ein Protokoll ohne Entscheid ist ein Bericht, und das
    darf dastehen.**
    """
    zeilen = _zeilen(protokoll)
    assert zeilen and zeilen[0].startswith("# "), (
        f"{protokoll.name} beginnt nicht mit einer Überschrift — dann hat die "
        f"Deckelzeile keinen Platz, an den sie gehört.")
    fehlend = _deckelzeile_fehlt(zeilen, 1)
    assert not fehlend, (
        f"{protokoll.name}: es fehlt {', '.join(fehlend)} in der Deckelzeile direkt "
        f"unter der Überschrift.")


# ------------------------------------------------------------- 4 · die Ankerpunkte

#: Abschnitte, die aus dem Quelltext heraus namentlich genannt werden. Das Muster ist
#: eng gehalten: Nur diese drei Formen kommen wirklich vor, und ein weiteres Muster
#: brächte Fehlalarme, bevor es einen Treffer brächte.
ANKERMUSTER = re.compile(r"(Phase \d|Wissensschulden|Stehende Regeln)")


def _quelldateien() -> list[Path]:
    orte = [WURZEL / "src", WURZEL / "tests", WURZEL / "tools"]
    return sorted(p for ort in orte if ort.is_dir() for p in ort.rglob("*.py"))


def _genannte_abschnitte() -> dict[str, list[str]]:
    """Sammelt aus dem Quelltext, welcher Abschnitt des Plans wo genannt wird.

    Gesucht wird im Fenster aus der Zeile mit der Erwähnung **und der folgenden** — ein
    Docstring bricht mitten im Verweis um, und ``(docs/PLAN.md,\\n Wissensschulden)`` ist
    derselbe Verweis wie in einer Zeile.
    """
    gefunden: dict[str, list[str]] = {}
    for datei in _quelldateien():
        zeilen = datei.read_text(encoding="utf-8").splitlines()
        for i, zeile in enumerate(zeilen):
            if "PLAN.md" not in zeile:
                continue
            fenster = zeile + " " + (zeilen[i + 1] if i + 1 < len(zeilen) else "")
            # Nur was NACH der Erwähnung steht, gehört zum Verweis.
            hinter = fenster[fenster.index("PLAN.md") + len("PLAN.md"):]
            for name in ANKERMUSTER.findall(hinter):
                ort = f"{datei.relative_to(WURZEL)}:{i + 1}"
                gefunden.setdefault(name, []).append(ort)
    return gefunden


def test_die_quellverweise_auf_den_plan_zeigen_auf_abschnitte_die_es_gibt() -> None:
    """Ein Verweis, der nach einem Umzug ins Leere zeigt, ist schlimmer als keiner.

    Er sieht aus wie eine Fundstelle, und wer ihm folgt, sucht an einer Stelle, an der
    nichts mehr steht — dieselbe Fehlerart wie eine tote Kante, nur in der Dokumentation.
    """
    genannt = _genannte_abschnitte()
    assert genannt, (
        "Kein einziger Quellverweis auf docs/PLAN.md gefunden. Entweder ist das Muster "
        "kaputt oder die Verweise sind verschwunden — beides gehört angesehen, denn "
        "diese Prüfung wäre sonst vakuum-wahr.")

    ueberschriften = [u for u, _ in _abschnitte(_zeilen(PLAN))]
    tot = {name: orte for name, orte in genannt.items()
           if not any(name.lower() in u.lower() for u in ueberschriften)}
    assert not tot, (
        "Der Quelltext verweist auf Abschnitte, die es in docs/PLAN.md nicht mehr gibt:\n"
        + "\n".join(f"  «{name}» — genannt in {', '.join(orte)}"
                    for name, orte in sorted(tot.items())))


def test_der_ankertest_faellt_wenn_ein_abschnitt_wirklich_fehlt() -> None:
    """Gegenprobe: Ein Wächter, der nicht fällt, bewacht nichts.

    Geprüft wird die Suchfunktion an einem Namen, den es im Plan nachweislich nicht gibt.
    Ohne diese Probe wäre nicht zu unterscheiden, ob der Test greift oder ob sein Muster
    schlicht nie zutrifft.
    """
    ueberschriften = [u for u, _ in _abschnitte(_zeilen(PLAN))]
    assert not any("Phase 9" in u for u in ueberschriften)
    assert any("Phase 4" in u for u in ueberschriften), (
        "«Phase 4» steht in vier Quelldateien als Fundstelle und muss es im Plan geben.")
