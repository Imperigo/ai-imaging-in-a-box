"""Jede Schriftfarbe der Oberfläche muss sich von ihrem Untergrund abheben — gerechnet.

**Der Befund, der diese Datei ausgelöst hat** (22.09.2026, beim Übertragen der Farben in
den iPad-Entwurf): Das Rot für **durchgefallen** (`#c2554f`) erreichte auf dem dunklen
Grund ein Kontrastverhältnis von **4.06** und auf einem Feld **3.70** — unter dem
Mindestmass von 4.5 für gewöhnliche Schriftgrösse.

Es traf ausgerechnet die eine Aussage, die niemand überlesen darf, und sie war von allen
dreien die am schlechtesten lesbare.

> *Ein Warnzeichen, das man nur bei guter Beleuchtung liest, warnt bei schlechter nicht.*

**Warum der Wächter rechnet statt zu vergleichen:** Eine Liste erlaubter Farbwerte wäre
ein Wächter über den Text und nicht über die Wirkung — sie fiele bei jeder Umbenennung
und bei keiner echten Verschlechterung. Hier wird aus der Datei gelesen, welche Farben es
gibt und welche davon als **Schriftfarbe** verwendet werden, und dann wird das Verhältnis
nach der Formel ausgerechnet, die auch Prüfwerkzeuge benutzen.

**Was das Verhältnis ist, für wen es später liest:** eine Zahl dafür, wie deutlich sich
Schrift von ihrem Untergrund abhebt. 1 zu 1 hiesse unsichtbar. Sie folgt aus den beiden
Farben und ist damit keine Geschmacksfrage.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

SEITE = Path(__file__).resolve().parents[1] / "oberflaeche" / "seite.html"

#: Das Mindestmass für gewöhnliche Schriftgrösse. Ab 24 px genügten 3.0 — die Oberfläche
#: setzt ihre farbigen Aussagen aber bei 12 bis 14 px, also gilt der strengere Wert.
MINDESTMASS = 4.5

#: Die beiden deckenden Flächenfarben, die als Untergrund vorkommen. Sie werden unten
#: aus der Datei gelesen; hier stehen nur ihre **Namen**, damit der Wächter nicht an
#: einer zweiten Farbliste hängt.
FLAECHEN = ("grund", "feld")


def _linear(kanal: int) -> float:
    c = kanal / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def helligkeit(hexwert: str) -> float:
    """Die relative Helligkeit einer Farbe, wie die Prüfformel sie versteht."""
    h = hexwert.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return 0.2126 * _linear(r) + 0.7152 * _linear(g) + 0.0722 * _linear(b)


def verhaeltnis(a: str, b: str) -> float:
    """Das Kontrastverhältnis zweier Farben — die Zahl, um die es geht."""
    la, lb = helligkeit(a), helligkeit(b)
    hell, dunkel = max(la, lb), min(la, lb)
    return (hell + 0.05) / (dunkel + 0.05)


def _quelle() -> str:
    return SEITE.read_text(encoding="utf-8")


def farbtafel() -> dict[str, str]:
    """Alle ``--name: #hex`` aus der Datei — nicht aus einer zweiten Liste hier."""
    return {name: wert for name, wert in
            re.findall(r"--([a-z-]+)\s*:\s*(#[0-9a-fA-F]{6})", _quelle())}


def auflage_ueber(hintergrund: tuple[int, int, int]) -> str:
    """Der Streifen auf dem Bild, ausgerechnet über einem gegebenen Bildpunkt.

    Der Streifen ist halbdurchsichtig — also hängt seine Helligkeit vom **Bild** ab, und
    das Bild gehört niemandem. Gerechnet wird darum über Schwarz und über Weiss, und
    beide müssen halten.

    **Der Fall, der das nötig machte:** Mit 0.82 Deckkraft hob ein weisses Bild den
    Streifen auf etwa `#343639`, und dort fielen alle vier farbigen Aussagen durch.
    *Ein Abzeichen, dessen Lesbarkeit vom Bild abhängt, auf dem es sitzt, ist auf dem
    hellen Bild keines.*
    """
    treffer = re.search(r"background:\s*rgba\((\d+),\s*(\d+),\s*(\d+),\s*([\d.]+)\)",
                        _quelle())
    assert treffer, "der Streifen unter dem Abzeichen steht nicht mehr als rgba() da"
    r, g, b = (int(treffer.group(i)) for i in (1, 2, 3))
    a = float(treffer.group(4))
    misch = tuple(round(a * kanal + (1 - a) * unter)
                  for kanal, unter in zip((r, g, b), hintergrund))
    return "#%02x%02x%02x" % misch


def untergruende() -> dict[str, str]:
    """Alle Untergründe, auf denen farbige Schrift steht — aus der Datei abgeleitet."""
    tafel = farbtafel()
    wo = {name: tafel[name] for name in FLAECHEN if name in tafel}
    wo["auflage_ueber_schwarzem_bild"] = auflage_ueber((0, 0, 0))
    wo["auflage_ueber_weissem_bild"] = auflage_ueber((255, 255, 255))
    return wo


def schriftfarben() -> set[str]:
    """Welche Farbtoken irgendwo als ``color:`` gesetzt werden.

    Abgeleitet und nicht aufgezählt: Wer morgen eine vierte farbige Aussage einführt,
    bekommt den Wächter geschenkt. *Ein Wächter, den man beim Erweitern von Hand
    nachziehen muss, wird beim Erweitern vergessen.*
    """
    return set(re.findall(r"\bcolor\s*:\s*var\(--([a-z-]+)\)", _quelle()))


# --------------------------------------------------------------------------------------
# 1 · Die Formel selbst — sonst prüft der Rest sich gegen einen Rechenfehler
# --------------------------------------------------------------------------------------

def test_die_formel_kennt_ihre_beiden_enden():
    assert verhaeltnis("#ffffff", "#000000") == pytest.approx(21.0, abs=0.01)
    assert verhaeltnis("#777777", "#777777") == pytest.approx(1.0, abs=0.01)


def test_die_formel_ist_richtungsfrei():
    assert verhaeltnis("#14161a", "#e2776f") == pytest.approx(
        verhaeltnis("#e2776f", "#14161a"))


# --------------------------------------------------------------------------------------
# 2 · Der Riegel über die Oberfläche
# --------------------------------------------------------------------------------------

def test_die_oberflaeche_kennt_ihre_farben():
    tafel = farbtafel()
    for pflicht in ("grund", "feld", "schrift", "leise",
                    "bestanden", "durchgefallen", "ungemessen"):
        assert pflicht in tafel, f"--{pflicht} steht nicht mehr in der Farbtafel"


def test_jede_schriftfarbe_haelt_das_mindestmass():
    """**Der eigentliche Riegel** — und er rechnet, statt eine Liste zu vergleichen."""
    tafel = farbtafel()
    zu_schwach = []
    for token in sorted(schriftfarben()):
        if token not in tafel:
            continue
        for wo, grund in untergruende().items():
            k = verhaeltnis(tafel[token], grund)
            if k < MINDESTMASS:
                zu_schwach.append(f"--{token} ({tafel[token]}) auf {wo}: {k:.2f}")

    assert not zu_schwach, (
        f"{len(zu_schwach)} Farbpaar(e) unter {MINDESTMASS}: {zu_schwach}. Eine Aussage, "
        f"die man nur bei guter Beleuchtung liest, wird bei schlechter nicht gelesen.")


def test_das_rot_ist_der_fall_von_dem_dieser_waechter_kommt():
    """Die Gegenprobe: Der alte Wert fällt durch, der neue kommt durch.

    Ohne diese Zeile stünde nirgends, dass der Wächter den gemeldeten Fall wirklich
    fängt — *ein Wächter an einer Stelle, an der der Fall nicht vorkommt, ist kein
    Wächter.*
    """
    assert verhaeltnis("#c2554f", farbtafel()["feld"]) < MINDESTMASS
    assert verhaeltnis(farbtafel()["durchgefallen"],
                       farbtafel()["feld"]) >= MINDESTMASS


def test_eine_bedeutung_traegt_eine_farbe_auf_beiden_flaechen():
    """Browserseite und iPad-Entwurf müssen für dasselbe Urteil denselben Wert führen.

    Sonst sehen zwei Flächen desselben Werkzeugs verschieden aus, und niemand weiss,
    welche gilt. Der Entwurf lebt ausserhalb des Repos; festgehalten ist der Wert in
    `docs/ENTSCHEIDE_IPAD_2026-09-21.md`, und diese Zeile hält ihn hier fest.
    """
    assert farbtafel()["durchgefallen"] == "#e2776f"


def test_der_streifen_haelt_auch_ueber_einem_weissen_bild():
    """Der zweite Fall, den dieser Wächter am Tag seiner Entstehung gefunden hat.

    Er stand nicht auf der Liste der Dinge, nach denen gesucht wurde — er fiel an, weil
    der Wächter über **alle** Untergründe rechnet statt über die, an die jemand gedacht
    hat.
    """
    hell = auflage_ueber((255, 255, 255))
    tafel = farbtafel()
    for token in ("bestanden", "durchgefallen", "ungemessen", "leise"):
        assert verhaeltnis(tafel[token], hell) >= MINDESTMASS, (
            f"--{token} auf dem Streifen ueber einem weissen Bild: "
            f"{verhaeltnis(tafel[token], hell):.2f}")


def test_die_alte_deckkraft_faellt_durch():
    """Gegenprobe: Mit 0.82 wäre der Streifen über Weiss zu hell gewesen."""
    alt = tuple(round(0.82 * k + 0.18 * 255) for k in (8, 10, 13))
    alt_hex = "#%02x%02x%02x" % alt
    assert verhaeltnis(farbtafel()["bestanden"], alt_hex) < MINDESTMASS
