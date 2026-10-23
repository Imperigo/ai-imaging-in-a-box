"""Folgen der Gegenprobe 328 (Demo-Kette in der Knotenansicht) und von Ergebnis 329 (22.10.2026, Protokoll 74 §229).

Die Logik der Knotenansicht prüft ``vitest`` (``kosmovis/apps/visbox-knoten/test/varianten.test.tsx``, drüben
``kv-varianten-grundlage.test.tsx``). Hier bewacht:

* S8 — der Kern meldet je Kamera ``geometry.status: not_applicable``, wenn das Urteil dieser Kamera «nicht
  entscheidbar» ist (Haus unter 20 % des Bildes). Vorher stand dort ``passed: false`` mit ``status: measured``,
  und Bildvergleich und Kuratieren lasen «durchgefallen», wo der Grund «NICHT BEURTEILBAR» sagt.
* S6/S7 — der Varianten-Knoten nennt die Grundlage des Render-Knotens (Verdrahtung in der Kopie).
* S9 — «Exportieren» an den Varianten, und der Dateiname beginnt in Visbox mit der Mappe.
* 329 — der Taktgeber des Abholers fragt alle 10 s statt alle 30 s.
"""
from __future__ import annotations

from pathlib import Path

from aiimaging import kosmo_szene

WURZEL = Path(__file__).resolve().parents[1]
KV = WURZEL / "kosmovis"
WIRT = KV / "apps" / "visbox-knoten"
VIS = KV / "apps" / "kosmo-orbit" / "src" / "modules" / "vis"


def _lies(pfad: Path) -> str:
    return pfad.read_text(encoding="utf-8")


def _urteil(kamera: str, **mehr) -> dict:
    # Erfundene Zahlen in der Form, die der Abholer fuer «Haus unter 20 %» liefert (Entscheid 70).
    u = {"kamera": kamera, "score": 0.2019, "bestanden": None, "geom_iou": 0.3, "n_gemeinsam": 900,
         "spearman": 0.6, "gesamtwert_anwendbar": False, "anteil_soll": 0.117}
    u.update(mehr)
    return u


def _ergebnis(*urteile: dict) -> dict:
    roh = kosmo_szene.als_ergebnis("vis-1792653432-f6c27c", [f"{u['kamera']}.png" for u in urteile],
                                   geometrie_urteil=urteile[0],
                                   je_kamera=[{"kamera": u["kamera"], "geometrie_urteil": u} for u in urteile])
    return roh


def test_s8_nicht_entscheidbar_heisst_je_kamera_not_applicable():
    e = _ergebnis(_urteil("sSE"), _urteil("nNW", anteil_soll=0.129))
    assert "NICHT BEURTEILBAR (Gebaeudeanteil)" in e["qa"]["verdict"]["reason"]
    for satz in e["qa_je_kamera"]:
        assert satz["geometry"]["passed"] is False  # ihr Vertrag: ein Wahrheitswert
        assert satz["geometry"]["status"] == "not_applicable"


def test_s8_bestanden_und_durchgefallen_bleiben_wie_sie_waren():
    ok = _urteil("sSE", bestanden=True, score=0.8, gesamtwert_anwendbar=True)
    fehl = _urteil("nNW", bestanden=False, score=0.4, gesamtwert_anwendbar=True)
    e = _ergebnis(ok, fehl)
    je = {s["kamera"]: s["geometry"] for s in e["qa_je_kamera"]}
    assert je["sSE"]["passed"] is True and "status" not in je["sSE"]
    assert je["nNW"]["passed"] is False and "status" not in je["nNW"]


def test_s8_ohne_zahl_bleibt_es_bei_nicht_gemessen():
    leer = _urteil("sSE", score=None, geom_iou=None, spearman=None, n_gemeinsam=0)
    e = _ergebnis(leer)
    geo = e["qa_je_kamera"][0]["geometry"]
    # Keine Zahl: kein «not_applicable» — das spaetere `_qa_mit_status` setzt «not_measured».
    assert geo.get("status") != "not_applicable"


def test_s8_der_qa_block_des_laufs_bleibt_unberuehrt():
    e = _ergebnis(_urteil("sSE"))
    assert "status" not in e["qa"]["geometry"]


def test_s6_der_varianten_knoten_nennt_die_grundlage_des_render_knotens():
    jobs = _lies(VIS / "vis-jobs.ts")
    rumpf = jobs[jobs.index("export function sendeGraphRenderAuftrag("):]
    # Seit der Gegenprobe 330 (B2) steht die Regel in `grundlageDerVariante` — dieselbe fuer Versand und
    # Zeitschaetzung (bewusst umgestellt, `tests/test_gegenprobe_330.py`).
    assert "if (variante && opts?.grundlage === undefined) {" in rumpf
    # Geraeteprobe R56 (Protokoll 74 §264, bewusst umgestellt): gefragt wird mit dem Stand der Grundlage —
    # dem der Variante, oder bei einer Teilmenge der Kameras dem mit allen Kameras des Render-Knotens.
    assert "standDerGrundlageFuerVariante(doc, rohKnoten, variante.kameras, node?.params ?? {}, standJetzt, opts)" in rumpf
    assert "grundlageDerVariante(node?.params, standGrundlage, { entwurf: !!variante.entwurf, ohneKi })" in rumpf
    assert "kiFest = { ...kiFest, grundlage: g.id, seed: g.seed };" in rumpf


def test_s9_export_an_den_varianten_und_der_name_der_mappe():
    raster = _lies(VIS / "VariantenRaster.tsx")
    assert "<BildAblageZeile" in raster and 'testid="varianten-raster-gross"' in raster
    assert "exportZusatz: exportZusatzDerZelle(gross, bestellung)" in raster
    main = _lies(WIRT / "src" / "main.tsx")
    assert "registriereExportStamm(offeneMappeName);" in main
    assert "export function offeneMappeName(): string | null {" in _lies(WIRT / "src" / "mappe.ts")


def test_329_der_taktgeber_fragt_alle_10_s():
    timer = _lies(WURZEL / "betrieb" / "kosmo-abholer.timer")
    assert "OnUnitInactiveSec=10s" in timer
    assert "OnUnitInactiveSec=30s" not in timer
