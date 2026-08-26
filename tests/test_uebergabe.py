"""Das Blatt für den Cloud-Worker sagt anderen Leuten, was sie bauen sollen — also wird es geprüft.

Warum es diese Datei gibt
-------------------------
`docs/EINBAU_CLOUDWORKER_2026-08-22.md` ist das einzige Dokument dieses Repos, nach dem
**jemand anders** arbeitet. Sein Kernsatz lautet:

    *Alles, was bei euch ankommen soll, braucht ein Feld in eurem Vertrag. Was kein Feld
    hat, existiert für euch nicht — egal wie fertig es bei uns ist.*

Und daraus folgt die Liste, die dieses Blatt trägt: welche bestellbaren Felder auf unserer
Seite **nichts bewirken**. Am 26.08.2026 sind zwei davon erledigt worden (`sun`, `skip`),
und dieselbe Änderung hätte das Blatt still falsch gemacht: Es hätte weiter behauptet, die
Sonne werde ignoriert, während sie längst bedient wird.

*Ein veraltetes Übergabeblatt ist teurer als gar keines* — es kostet die andere Seite
Arbeit an einer Lücke, die es nicht mehr gibt, und lässt sie eine übersehen, die es gibt.

Was hier geprüft wird, und was nicht
------------------------------------
Geprüft wird die **Übereinstimmung zweier Listen**: die stehengebliebenen Felder in
:data:`aiimaging.kosmo_szene.STEHENGEBLIEBEN` und die, die das Blatt als wirkungslos
nennt. Beide führen jetzt denselben fremden Namen — er steht seit dem 26.08. im
Tabelleneintrag selbst und ist damit nicht mehr geraten.

**Nicht geprüft wird, ob das Blatt gut erklärt.** Das kann nur ein Mensch, und dafür ist
es geschrieben.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from aiimaging import kosmo_szene

WURZEL = Path(__file__).resolve().parents[1]
BLATT = WURZEL / "docs" / "EINBAU_CLOUDWORKER_2026-08-22.md"

#: Der Abschnitt, der die wirkungslosen Felder aufzählt. **Nur dort** wird gesucht.
#:
#: Der Grund ist an diesem Tag zweimal teuer geworden: Ein Wächter, der das ganze Dokument
#: liest, schlägt an der **Prosa über sich selbst** an. Der `NOTICE`-Wächter hielt das Wort
#: «AGPL» in seiner eigenen Erklärung für einen Bestandteil, und der Regel-3-Wächter hielt
#: ein Backtick für einen Benutzernamen. Beide Male war der Fund erfunden.
ABSCHNITT = ("### N5 · Was weiterhin bestellt werden kann und nichts bewirkt",
             "### N6 ·")


def _blatt() -> str:
    return BLATT.read_text(encoding="utf-8")


def _abschnitt_n5() -> str:
    text = _blatt()
    anfang = text.index(ABSCHNITT[0])
    ende = text.index(ABSCHNITT[1], anfang)
    return text[anfang:ende]


def _tabellenzeilen() -> list[str]:
    """Die Feldnamen aus der **ersten Spalte** der Tabelle in N5.

    **Nicht** alles, was im Abschnitt in Backticks steht. Der Unterschied ist am
    26.08.2026 in der Mutationsprobe aufgefallen: Die erste Fassung sammelte jeden
    Backtick-Namen ein — auch die aus dem erklärenden Absatz darunter, der `upscale` und
    `style` beiläufig erwähnt. Eine Zeile aus der Tabelle zu entfernen liess den Test
    darum **grün**, weil der Name nebenan im Fliesstext weiterstand.

    *Ein Wächter, der eine Liste an ihrer Erwähnung statt an ihrem Eintrag prüft, prüft
    die Erwähnung.*
    """
    zeilen = []
    for z in _abschnitt_n5().splitlines():
        treffer = re.match(r"\|\s*`([a-z_.]+)`\s*\|", z)
        if treffer:
            zeilen.append(treffer.group(1))
    return zeilen


def _genannte_felder() -> set[str]:
    return set(_tabellenzeilen())


def test_der_abschnitt_existiert_ueberhaupt():
    """Ohne ihn wäre jede Zusicherung darunter vakuumwahr."""
    abschnitt = _abschnitt_n5()
    assert len(abschnitt) > 300, (
        f"Der Abschnitt N5 hat nur {len(abschnitt)} Zeichen. Wenn er umbenannt wurde, "
        f"gehört ABSCHNITT hier nachgezogen — sonst prüft diese Datei ab jetzt nichts.")


def test_jedes_stehengebliebene_feld_steht_auf_dem_blatt():
    """Was bei uns nichts bewirkt, muss die andere Seite erfahren.

    Sonst bestellt sie es weiter und wundert sich über ein Bild, das aussieht wie ohne.
    """
    genannt = _genannte_felder()
    fehlend = [e["fremd"] for e in kosmo_szene.STEHENGEBLIEBEN.values()
               if e["fremd"] not in genannt]
    assert not fehlend, (
        f"Diese Felder bewirken bei uns nichts, stehen aber nicht auf dem Blatt: "
        f"{fehlend}. Der Cloud-Worker kann sie bestellen und bekommt ein Bild, dem man "
        f"nicht ansieht, dass die Bestellung ins Leere ging.")


def test_die_tabelle_nennt_GENAU_die_wirkungslosen_felder():
    """Nicht «mindestens», sondern **genau** — in beide Richtungen.

    **Die Richtung, die am 26.08. beinahe schiefgegangen wäre:** `sun` und `skip` standen
    bis zu jenem Tag als wirkungslos auf dem Blatt. Beide werden seither bedient. Hätte
    niemand das Blatt angefasst, hätte es weiter behauptet, ein bestellter Sonnenstand
    werde ignoriert — und die andere Seite hätte an einer Lücke gearbeitet, die es nicht
    mehr gibt.

    Eine Zusicherung nur über die eine Richtung («jedes stehengebliebene Feld steht auf
    dem Blatt») hätte das **nicht** gefangen: Ein Feld, das niemand mehr ignoriert, steht
    dann einfach zusätzlich da.
    """
    auf_dem_blatt = _tabellenzeilen()
    im_code = sorted(e["fremd"] for e in kosmo_szene.STEHENGEBLIEBEN.values())
    assert sorted(auf_dem_blatt) == im_code, (
        f"Das Blatt führt {sorted(auf_dem_blatt)} als wirkungslos, der Code kennt "
        f"{im_code}.\n"
        f"  Zuviel auf dem Blatt: {sorted(set(auf_dem_blatt) - set(im_code))} — diese "
        f"Felder werden inzwischen bedient, und die andere Seite arbeitet an einer "
        f"geschlossenen Lücke.\n"
        f"  Fehlt auf dem Blatt: {sorted(set(im_code) - set(auf_dem_blatt))} — diese "
        f"kann sie bestellen und bekommt ein Bild, dem man nicht ansieht, dass die "
        f"Bestellung ins Leere ging.")


def test_jede_zeile_kommt_nur_einmal_vor():
    """Zwei Zeilen für dasselbe Feld veralten unabhängig voneinander.

    Dieselbe Fehlerart, die das Lexikon am 20.08. bei sieben Begriffen hatte.
    """
    zeilen = _tabellenzeilen()
    assert len(zeilen) == len(set(zeilen)), f"Doppelte Zeilen: {zeilen}"


@pytest.mark.parametrize("name", sorted(kosmo_szene.STEHENGEBLIEBEN))
def test_der_fremde_name_kommt_im_lesecode_wirklich_vor(name):
    """Der deklarierte fremde Name muss der sein, der wirklich gelesen wird.

    Ohne diese Probe wäre ``fremd`` ein Wunsch: Man schreibt einen hübschen Namen in die
    Tabelle, das Blatt nennt ihn, beide sind einig — und der Vertrag heisst anders.
    """
    fremd = kosmo_szene.STEHENGEBLIEBEN[name]["fremd"]
    quelle = (Path(kosmo_szene.__file__)).read_text(encoding="utf-8")
    # `style.mode` wird als `stil.get("mode")` gelesen — geprüft wird der letzte Teil.
    stueck = fremd.rsplit(".", 1)[-1]
    assert re.search(rf'\.get\(\s*"{re.escape(stueck)}"', quelle), (
        f"{name!r} deklariert den fremden Namen {fremd!r}, aber `kosmo_szene` liest "
        f"nirgends ein Feld {stueck!r}. Entweder ist die Deklaration falsch, oder das "
        f"Feld wird gar nicht mehr gelesen.")


# ======================================================================================
# Die Fragenliste — und die Zahl, die ein zweites Dokument über sie behauptet
# ======================================================================================

BLATT_LANG = WURZEL / "docs" / "UEBERGABE_VIS_2026-08-19.md"

#: Wo die nummerierte Fragenliste beginnt. Davor stehen drei gleich nummerierte Fragen
#: («Was schicke ich euch?»), die die **Gliederung** des Dokuments sind und keine offenen
#: Punkte — sie mitzuzählen ergäbe 17 statt 14 und hätte die Zahl schleichend aufgebläht.
LISTE_BEGINNT = "## Was wir von euch brauchen, in einer Liste"


def _fragen() -> list[str]:
    text = BLATT_LANG.read_text(encoding="utf-8")
    liste = text[text.index(LISTE_BEGINNT):]
    return re.findall(r"^(\d+)\. \*\*", liste, re.M)


def test_die_fragen_sind_lueckenlos_durchnummeriert():
    """Eine übersprungene Nummer heisst: Eine Frage ist verschwunden und niemand weiss welche.

    *Die Liste ist die Klammer zwischen zwei Seiten.* Wer auf «Frage 13» verweist, muss
    dieselbe Frage meinen wie der, der sie beantwortet.
    """
    nummern = [int(n) for n in _fragen()]
    assert nummern, f"Keine nummerierte Frage nach {LISTE_BEGINNT!r} gefunden."
    assert nummern == list(range(1, len(nummern) + 1)), (
        f"Die Nummerierung hat eine Lücke oder eine Dublette: {nummern}")


def test_das_kurzblatt_nennt_die_richtige_zahl():
    """Zwei Dokumente, eine Zahl — und das kürzere behauptet sie über das längere.

    **Genau diese Stelle ist am 26.08.2026 falsch geworden:** Die Liste wuchs von 14 auf
    16 (Azimutkonvention, `render.faithful`), und das Kurzblatt hätte weiter «14 Stück»
    gesagt. Eine Zahl in einem Fliesstext veraltet lautlos — das ist derselbe Befund wie
    bei der Testzahl im README, nur zwischen zwei Dokumenten.
    """
    n = len(_fragen())
    text = _blatt()
    assert f"(inzwischen {n} Stück)" in text, (
        f"Die Fragenliste hat {n} Einträge; das Kurzblatt nennt eine andere Zahl. "
        f"Wer eine Frage hinzufügt, zieht den Satz im Kurzblatt nach — er ist die "
        f"einzige Stelle, an der jemand die Zahl im Vorbeilesen mitbekommt.")


def test_die_juengsten_fragen_stehen_auch_im_langen_blatt():
    """Eine Frage, die nur in einer Auftragsdatei steht, erreicht die andere Seite nicht.

    `auf-20260826-44` trägt die beiden Vertragsfragen vom 26.08. — aber die andere Seite
    liest das Übergabeblatt, nicht unser Auftragsverzeichnis. **Ein Auftrag ist die
    Anweisung an einen Worker, kein Ersatz für die Übergabe.**
    """
    lang = BLATT_LANG.read_text(encoding="utf-8")
    for stichwort in ("azimuth", "faithful"):
        assert stichwort in lang, (
            f"{stichwort!r} kommt im ausführlichen Übergabeblatt nicht vor, obwohl es "
            f"eine offene Vertragsfrage ist.")
