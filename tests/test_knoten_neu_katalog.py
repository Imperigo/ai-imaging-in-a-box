"""Bauplan «Neue Knoten» Schritt K (Entscheide 109–113): der Katalog der Knotenansicht und der
Heim-PC sprechen von denselben Dingen.

Die Knotenansicht (Kopie unter ``kosmovis/``, aus KosmoOrbit übernommen) schickt Kennungen —
Stimmung, Richtungskürzel, Material — und legt für die Stimmung einen Satz in den Prompt. Der
Heim-PC kennt dieselben Kennungen aus eigenen Tabellen (``stimmung.STIMMUNGEN``,
``kameras.RICHTUNGEN``, ``materialwahl.BIBLIOTHEK``). Laufen sie auseinander, weist der Heim-PC
eine Bestellung ab, die der Knoten für gültig hält, oder der Satz steht doppelt im Prompt
(``stimmung`` prüft «schon da» am deutschen Satz). Diese Probe liest den TypeScript-Text der Kopie
und hält beide Seiten gleich.
"""
from __future__ import annotations

import re
from pathlib import Path

from aiimaging import kameras, materialwahl, stimmung

REPO = Path(__file__).resolve().parents[1]
VISGRAPH = REPO / "kosmovis" / "packages" / "kosmo-kernel" / "src" / "derive" / "visgraph.ts"
VERTRAG = REPO / "kosmovis" / "packages" / "kosmo-contracts" / "src" / "render-scene.ts"


def _block(text: str, anfang: str) -> str:
    """Der Wert einer Konstante: ab dem ersten «{» oder «[» nach dem «=» bis zur passenden Klammer."""
    i = text.index("=", text.index(anfang))
    start = min(j for j in (text.find("{", i), text.find("[", i)) if j >= 0)
    tiefe = 0
    for j in range(start, len(text)):
        c = text[j]
        if c in "{[":
            tiefe += 1
        elif c in "}]":
            tiefe -= 1
            if tiefe == 0:
                return text[start:j + 1]
    raise AssertionError(f"Block {anfang!r} nicht geschlossen")


def _visgraph() -> str:
    return VISGRAPH.read_text(encoding="utf-8")


def test_acht_stimmungen_in_derselben_reihenfolge_mit_demselben_satz():
    block = _block(_visgraph(), "export const VIS_STIMMUNGEN")
    eintraege = re.findall(r"'?([a-z-]+)'?: \{ label: '([^']+)', prompt: '([^']+)' \}", block)
    assert [k for k, _, _ in eintraege] == list(stimmung.STIMMUNGEN)
    for kennung, label, satz in eintraege:
        assert satz == stimmung.STIMMUNGEN[kennung]["prompt_de"], kennung
        assert label == stimmung.STIMMUNGEN[kennung]["label"], kennung


def test_die_liste_der_kennungen_und_der_vertrag_kennen_dieselben_acht():
    ids = re.search(r"VIS_STIMMUNG_IDS = \[([^\]]+)\]", _visgraph()).group(1)
    assert re.findall(r"'([a-z-]+)'", ids) == list(stimmung.STIMMUNGEN)
    vertrag = re.search(r"StimmungPreset = z\.enum\(\[([^\]]+)\]\)", VERTRAG.read_text(encoding="utf-8")).group(1)
    assert re.findall(r"'([a-z-]+)'", vertrag) == list(stimmung.STIMMUNGEN)


def test_richtungen_am_knoten_sind_kuerzel_des_heim_pcs():
    block = _block(_visgraph(), "export const KAMERA_RICHTUNGEN")
    kuerzel = re.findall(r"kuerzel: '([A-Za-z]+)'", block)
    assert len(kuerzel) == 8
    assert set(kuerzel) <= set(kameras.RICHTUNGEN)
    vorgabe = re.search(r"richtungen: \[([^\]]+)\] as readonly string\[\]", _visgraph()).group(1)
    assert set(re.findall(r"'([A-Za-z]+)'", vorgabe)) <= set(kuerzel)
    vertrag = re.search(r"AutoRichtung = z\.enum\(\[([^\]]+)\]\)", VERTRAG.read_text(encoding="utf-8")).group(1)
    assert set(re.findall(r"'([A-Za-z]+)'", vertrag)) == set(kameras.RICHTUNGEN)


def test_die_elf_materialien_sind_die_der_bibliothek():
    block = _block(_visgraph(), "export const VIS_MATERIAL_BIBLIOTHEK")
    eintraege = re.findall(r"\{ id: '([a-z0-9-]+)', label: '([^']+)', farbe: '#[0-9a-f]{6}' \}", block)
    assert [i for i, _ in eintraege] == list(materialwahl.BIBLIOTHEK)
    for kennung, label in eintraege:
        assert label == materialwahl.BIBLIOTHEK[kennung]["label"], kennung


def test_bauteil_arten_und_vorgaben_wie_am_heim_pc():
    arten = re.findall(r"\{ art: '([a-z]+)', label:", _block(_visgraph(), "export const VIS_BAUTEIL_ARTEN"))
    assert tuple(arten) == materialwahl.ARTEN
    vorgaben = re.search(r"MATERIAL_VORGABEN = \{ massstab_m: ([\d.]+), drehungGrad: ([\d.]+), relief: ([\d.]+) \}", _visgraph())
    assert float(vorgaben.group(1)) == materialwahl.VORGABE_MASSSTAB_M
    assert float(vorgaben.group(2)) == materialwahl.VORGABE_DREHUNG_GRAD
    assert float(vorgaben.group(3)) == materialwahl.VORGABE_RELIEF
