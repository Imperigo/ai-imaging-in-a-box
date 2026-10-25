"""Entscheid 153 (Owner, 25.10.2026, über die Zentrale): Qwen-Image darf für Skizzen in «Voll» ohne Klick.

Wortlaut: «Ja, Qwen-Image darf für Skizzen in Vollautomatik ohne Klick laufen.»

* «Voll» + Bild AUS EINER SKIZZE + ``qwen-image-2.1`` → ohne Karte, ohne «Freigeben» in die Reihe,
  gezählt zur Grenze von 5 je Stunde, und markiert (``lizenz_offen`` bleibt am Lauf, der Laufzettel
  sagt es mit dem Satz von Entscheid 153).
* Jedes andere Bild mit Qwen-Image 2.1 bleibt eine Karte (E146 unverändert), ebenso jedes Modell
  mit ``nur_forschung`` — auch aus einer Skizze.
* Die Grenze gilt: ist sie erreicht, wartet auch die Skizze auf «Freigeben».
* E128 Auflage 1 unverändert: Qwen ist nie Vorgabe — ohne Wahl rechnet eine Skizze auf
  ``z-image-turbo`` (und dort seit dem 25.10.2026 über den eigenen Start).

Regel 3: alles synthetisch.
"""
from __future__ import annotations

import re
from pathlib import Path

from aiimaging import backbone, bruecke, knotenweg

from test_knotenweg import SZENE
from test_mappenpaket import _mappe

WURZEL = Path(__file__).resolve().parents[1]
WIRT = WURZEL / "kosmovis" / "apps" / "visbox-knoten" / "src"
T0 = 1_790_000_000.0


class _Uhr:
    def __init__(self, t: float = T0):
        self.t = t

    def __call__(self) -> float:
        return self.t


def _lege(ablage, uhr, mappe, *, n=0, skizze=True, **vis):
    szene = dict(SZENE, vis={**SZENE["vis"], **vis},
                 style={**(SZENE.get("style") or {}), "prompt": "ein Vordach"})
    if skizze:
        szene["skizze"] = {"quelle": "mappe", "name": "skizze-a.png"}
    return knotenweg.lege_an(ablage, szene, b"glTF-bytes", "model.glb",
                             kennung=f"vis-{int(uhr())}-{n:06x}", mappe=mappe.name,
                             mappe_pfad=mappe, ohne_klick=True, _uhr=uhr)


def test_voll_skizze_mit_qwen_geht_ohne_klick_gezaehlt_und_markiert(tmp_path):
    uhr, mappe = _Uhr(), _mappe(tmp_path, "Hof")
    z = _lege(tmp_path / "ablage", uhr, mappe, backbone="qwen-image-2.1")
    assert z["status"] == bruecke.STATUS_QUEUED, z
    assert z[knotenweg.FELD_FREIGABE]["ohne_klick"] is True
    vermerk = z[knotenweg.FELD_VOLL]
    assert vermerk["zustand"] == knotenweg.ZUSTAND_FREI and vermerk["entscheid"] == "153"
    assert "offene Lizenz" in vermerk["satz"] and "markiert" in vermerk["satz"]
    # GEZAEHLT wie jeder andere Lauf ohne Klick.
    assert knotenweg.voll_stand(tmp_path / "ablage", _uhr=uhr)["laeufe"] == 1
    # MARKIERT bleibt der Lauf im Register (E128 Auflage 2) — daraus kommt engine_license_open.
    assert backbone.hole("qwen-image-2.1").lizenz_offen


def test_voll_ohne_skizze_mit_qwen_bleibt_eine_karte(tmp_path):
    uhr, mappe = _Uhr(), _mappe(tmp_path, "Hof")
    z = _lege(tmp_path / "ablage", uhr, mappe, skizze=False, backbone="qwen-image-2.1")
    assert z["status"] == bruecke.STATUS_AWAITING
    assert z[knotenweg.FELD_VOLL]["zustand"] == knotenweg.ZUSTAND_LIZENZ
    assert knotenweg.voll_stand(tmp_path / "ablage", _uhr=uhr)["laeufe"] == 0


def test_ist_die_grenze_erreicht_wartet_auch_die_skizze(tmp_path):
    uhr, mappe = _Uhr(), _mappe(tmp_path, "Hof")
    ablage = tmp_path / "ablage"
    for i in range(knotenweg.VOLL_GRENZE):
        assert _lege(ablage, uhr, mappe, n=i, skizze=False,
                     backbone="z-image-turbo")["status"] == bruecke.STATUS_QUEUED
        uhr.t += 60
    z = _lege(ablage, uhr, mappe, n=99, backbone="qwen-image-2.1")
    assert z["status"] == bruecke.STATUS_AWAITING
    assert z[knotenweg.FELD_VOLL]["zustand"] == knotenweg.ZUSTAND_GRENZE


def test_die_lizenzregel_je_fall():
    mit = {"skizze": {"quelle": "mappe", "name": "s.png"}}
    assert knotenweg.voll_lizenz_mangel({**mit, "vis": {"backbone": "qwen-image-2.1"}}) is None
    assert knotenweg.voll_lizenz_mangel({"vis": {"backbone": "qwen-image-2.1"}})
    # Forschung, nicht kommerziell, unbekannt: auch aus einer Skizze nur nach einem Klick.
    for bm in ("flux-krea", "sdxl", "gibts-nicht"):
        assert knotenweg.voll_lizenz_mangel({**mit, "vis": {"backbone": bm}}), bm
    assert knotenweg.voll_lizenz_mangel(
        {**mit, "vis": {"backbone": "qwen-image-2.1", "research_only": True}})
    # Ohne Wahl: die Vorgabe z-image-turbo — Qwen ist nie Vorgabe (E128 Auflage 1).
    assert knotenweg.voll_lizenz_mangel({**mit, "vis": {}}) is None


def test_die_freigabe_folgt_dem_register_und_gilt_nur_fuer_qwen():
    assert knotenweg.voll_skizzen_bildmodelle() == ("qwen-image-2.1",)
    for kuerzel in knotenweg.voll_skizzen_bildmodelle():
        eintrag = backbone.hole(knotenweg.kosmo_szene.BACKBONE_VON_FREMD[kuerzel])
        assert eintrag.lizenz_offen and not eintrag.nur_forschung
        assert kuerzel not in knotenweg.voll_bildmodelle()
    assert knotenweg.voll_stand(WURZEL / "gibtsnicht")[
        "skizzen_bildmodelle"] == ["qwen-image-2.1"]


def test_die_knotenansicht_haelt_dieselbe_regel():
    """voll-render.ts: dieselbe Liste, nur fuer vis.render MIT Skizze am Render-Knoten."""
    ts = (WIRT / "voll-render.ts").read_text(encoding="utf-8")
    liste = re.search(r"VOLL_SKIZZEN_BILDMODELLE: readonly string\[\] = \[([^\]]*)\]", ts).group(1)
    assert tuple(re.findall(r"'([^']+)'", liste)) == knotenweg.voll_skizzen_bildmodelle()
    assert "toPort === 'skizze'" in ts
    # Nie Vorgabe: die Vorgabe bleibt z-image-turbo.
    assert "VOLL_VORGABE_BILDMODELL = 'z-image-turbo'" in ts
