"""Mac-Demolauf «Haus am Hang» (Visbox 0.3.34 → 0.3.35, 22.10.2026) — Funde N1, N8, N9, N4.

Die Verhaltensproben liegen beim Verhalten: XCTest im Mac-Kern (``KnotenwegeTests``,
``MacmappeTests``, über die Mac-CI), vitest in ``kosmovis/`` (Kartenzeile). Hier steht, dass die
Nähte zwischen Seite, Mac-App und Heim-PC an ihrem Platz bleiben — eine Zeile, die still
zurückgedreht wird, macht diese Probe rot.

**N1 (Vorrang):** Eine Mappe am Mac bekam nach «Datei laden …» kein Modell und keine Auswertung;
am Heim-PC entstand der Zwilling, und «An den Mac holen» legte ihn ein zweites Mal an. Der Heim-PC
tat alles richtig (``test_mappe_am_mac_laden.py``: Zwilling, Paket, keine Umstellung). Die Lücke
war die Mac-App: Der Weg ``/knoten/mappe-holen`` stand in ``Mappenkern.ziel``, aber nicht in
``Knotenwege``; die App antwortete 404, und die Seite liest 404 als «keine Mappe am Mac offen».
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
KERN = REPO / "ipad" / "Visbox.swiftpm" / "Kern"
MAC = REPO / "ipad" / "VisboxMac" / "Sources" / "VisboxMac"


def _lies(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def _swift_set(text: str, name: str) -> set[str]:
    block = re.search(rf"static let {name}: Set<String> = \[(.*?)\]", text, re.S)
    assert block, f"{name} hat seine Form geändert"
    return set(re.findall(r'"([^"]+)"', block.group(1)))


# ---------------------------------------------------------------- N1

def test_der_weg_nach_datei_laden_ist_ein_weg_der_app():
    wege = _lies(KERN / "Knotenwege.swift")
    mappe = _lies(KERN / "Macmappe.swift")
    weg = re.search(r'static let wegModellHolen = "([^"]+)"', mappe).group(1)
    assert weg in _swift_set(wege, "appwege"), "ohne ihn antwortet die App 404 (Befund N1)"
    assert weg not in _swift_set(wege, "datenwege"), "datenwege ist die Abschrift des Servers"
    assert "datenwege.contains(pfad) || appwege.contains(pfad)" in wege
    seite = _lies(REPO / "kosmovis" / "apps" / "visbox-knoten" / "src" / "mappe.ts")
    assert re.search(r"export const WEG_MODELL_HOLEN = '\./mappe-holen';", seite)
    assert weg == "/knoten/mappe-holen"


def test_der_heim_pc_kennt_den_weg_der_app_nicht():
    """Der Weg gehört nur der App — kein ``WEG_KNOTEN_*`` am Server, sonst stimmte die bewachte
    Abschrift ``datenwege`` nicht mehr, und ohne Mappe am Mac ginge er ins Leere."""
    server = _lies(REPO / "oberflaeche" / "server.py")
    assert "/knoten/mappe-holen" not in server


def test_die_seite_liest_404_als_keine_mappe_am_mac():
    """Darum war der 404 still: Die Seite hält ihn für «nicht in der App oder keine Mappe am Mac»."""
    seite = _lies(REPO / "kosmovis" / "apps" / "visbox-knoten" / "src" / "mappe.ts")
    start = seite.index("export async function holeInDieMappeAmMac")
    # Seit dem Befund «Andere Datei» (0.3.67) nur noch, wenn das Laden NICHT aus einer Mappe am Mac kam.
    assert "antwort.status === 404 && !mussAmMac) return null" in seite[start:start + 1400]
    quelle = _lies(MAC / "Start" / "Knotenquelle.swift")
    assert 'Knotenwege.appwege.contains(pfad)' in quelle
    assert '"Keine Mappe am Mac offen."' in quelle


def test_das_modell_kommt_in_die_mappe_aus_der_geladen_wurde():
    quelle = _lies(MAC / "Start" / "Knotenquelle.swift")
    assert "holeModell(aufgabe, rumpf: Knotenquelle.rumpf(aufgabe.request) ?? Data(), in: ordner)" in quelle
    assert "holeModell(von: kennung, in: ordner," in quelle
    ablage = _lies(MAC / "Start" / "Mappenablage.swift")
    start = ablage.index("func holeModell(von kennung: String, in ordner: URL")
    rumpf = ablage[start:ablage.index("private func holePaket", start)]
    # Nie mehr still zurück, wenn die Mappe fehlt; erst nach dem Holen frisch gelesen.
    assert "offenerOrdner" not in rumpf
    assert "throw Mappenfehler" in rumpf
    assert "var mappe = Mappenablage.lies(ordner) ?? vorher" in rumpf
    assert "mappe.heimMappe = kennung" in rumpf and "mappe.knoten = paket.knotenFuerMappe" in rumpf


# ---------------------------------------------------------------- N8

def test_die_app_holt_beim_oeffnen_der_mappe_nach():
    quelle = _lies(MAC / "Start" / "Knotenquelle.swift")
    start = quelle.index("case .mappe:")
    assert "holeNach(mappe, in: ordner)" in quelle[start:start + 1400]
    assert "Mappenkern.nachzuholen(" in quelle
    assert "for versuch in 1...bildVersuche" in quelle
    assert re.search(r"static let bildVersuche = [2-9]", quelle)


# ---------------------------------------------------------------- N9

def test_ohne_mappe_am_mac_bleibt_kein_alter_name_stehen():
    zentrale = _lies(MAC / "Claude" / "Kizentrale.swift")
    assert "mappenname = ordner.flatMap { Mappenablage.lies($0)?.name }" in zentrale
    # Fund A (0.3.35) bleibt: mappe_lesen liest dieselbe Mappe wie die Knotenansicht.
    assert "if case .macMappe = lesequelle, let ordner = macMappenordner" in zentrale


# ---------------------------------------------------------------- N4

@pytest.mark.parametrize("wurzel", ["kosmovis/packages/kosmo-kernel/src/commands/vis.ts"])
def test_die_loeschkarte_nennt_den_graphen(wurzel):
    """0.3.34 sagte «Render-Graph gelöscht»; seit K-10 (0.3.35) steht der Name auf der Karte."""
    vis = _lies(REPO / wurzel)
    start = vis.index("id: 'vis.graphLoeschen'")
    teil = vis[start:start + 500]
    assert "Render-Graph «${g.name}» löschen" in teil
    assert "'Render-Graph gelöscht'" not in teil
