"""Ergebnis auf-20261024-347: Die Deckung misst nur im Haus — und die KI-Zeit nennt das Laden.

1. **Deckung im Haus.** In der Vorschau von 347 stieg die Kanten-IoU über das ganze Bild von
   0,202 auf 0,297 (über die Schwelle 0,25), weil die Bäume als Umfeld aus dem Cycles-Bild kommen
   und ihre Kanten decken; der Satz «FORM WEICHT VOM GRUNDBILD AB» fiel weg, obwohl das Haus
   übermalt war. Seither zählt die Deckung nur in der Bauwerksmaske ohne Umfeld und Gelände.
2. **Die Schwelle bleibt 0,25** — gegengeprüft an den Haus-Werten aus 337/339/340/346/347.
3. **KI-Zeit:** Das Bildmodell meldet, wie viel seiner Dauer Laden war (``laden_s``), und das
   Kameraurteil trägt beides (``ki_zeit``).

Synthetisch, ohne GPU.
"""
from __future__ import annotations

from pathlib import Path

from aiimaging import abholer, bildschreiben, farbabgleich, kosmo_szene, render, varianten as v

# ============================================================ ein Haus und ein Baum daneben

B, H = 80, 40
HAUS_ID, BAUM_ID = (200, 10, 10), (10, 200, 10)
TABELLE = [{"index": 0, "name": "Fassade_Holz", "farbe_srgb_8bit": list(HAUS_ID)},
           {"index": 1, "name": "Baum_Laub", "farbe_srgb_8bit": list(BAUM_ID)}]
LATTE, FUGE = (170, 130, 90), (120, 90, 60)


def _haus(x, y):
    return 2 <= x < 26 and 6 <= y < 36


def _baum(x, y):
    return 30 <= x < 78 and 2 <= y < 38


def _grund(x, y):
    if _haus(x, y):
        return FUGE if x % 4 == 0 else LATTE            # Lattung mit Fugen
    if _baum(x, y):
        return (40, 90, 40) if (x // 2 + y // 2) % 2 else (110, 160, 100)   # Laub
    return (150, 190, 230)


def _ki_uebermalt(x, y):
    """Wie die Vorschau in 347: das Haus glatt zugemalt, der Baum aus dem Cycles-Bild."""
    return LATTE if _haus(x, y) else _grund(x, y)


def _bild(f):
    return [f(x, y) for y in range(H) for x in range(B)]


def _kennung(x, y):
    return HAUS_ID if _haus(x, y) else (BAUM_ID if _baum(x, y) else (0, 0, 0))


NUR_HAUS = _bild(_haus)
HAUS_UND_BAUM = _bild(lambda x, y: _haus(x, y) or _baum(x, y))   # die Maske vor 0.3.52


def _png(pfad, farben):
    bildschreiben.schreibe_farb_png(pfad, farben, B, H)
    return str(pfad)


def test_ueber_das_ganze_bild_deckt_der_baum_das_zugemalte_haus_zu():
    """Der Fehler aus 347, nachgestellt: ganz über der Schwelle, im Haus weit darunter."""
    ki, grund = _bild(_ki_uebermalt), _bild(_grund)
    ganz = farbabgleich.kanten_iou(ki, grund, B, H)
    haus = farbabgleich.kanten_iou(ki, grund, B, H, bereich=NUR_HAUS)
    assert ganz >= v.DECKUNG_KANTEN_IOU_SCHWELLE          # alt: «deckungsgleich», kein Satz
    assert haus < v.DECKUNG_KANTEN_IOU_SCHWELLE
    # Dieselben Karten, einmal gerechnet: die Teilfunktionen ergeben dasselbe.
    ka, kb = farbabgleich.kantenkarten(ki, grund, B, H)
    assert farbabgleich.kanten_iou_aus_karten(ka, kb) == ganz
    assert farbabgleich.kanten_iou_aus_karten(ka, kb, bereich=NUR_HAUS) == haus


def test_deckung_aus_bildern_misst_im_haus_und_nennt_den_bereich(tmp_path):
    grund = _png(tmp_path / "g.png", _bild(_grund))
    ki = _png(tmp_path / "k.png", _bild(_ki_uebermalt))
    d = v.deckung_aus_bildern(ki, grund, True, maske=NUR_HAUS)
    assert d["urteil"] == v.FORM_WEICHT_AB and d["warnung"] is True
    assert d["bereich"] == v.DECKUNG_BEREICH_HAUS and d["n_haus"] == sum(NUR_HAUS)
    assert d["kanten_iou_ganz"] >= v.DECKUNG_KANTEN_IOU_SCHWELLE
    # Ein gehaltenes Haus bleibt deckungsgleich.
    gehalten = v.deckung_aus_bildern(grund, grund, True, maske=NUR_HAUS)
    assert gehalten["urteil"] == v.DECKUNGSGLEICH and gehalten["kanten_iou"] == 1.0


def test_umfeld_in_der_maske_faellt_ueber_den_id_pass_heraus(tmp_path):
    """Liegt der Baum noch in der Maske (Stand vor 0.3.52), nimmt ihn der ID-Pass heraus."""
    grund = _png(tmp_path / "g.png", _bild(_grund))
    ki = _png(tmp_path / "k.png", _bild(_ki_uebermalt))
    idpass = _png(tmp_path / "id.png", _bild(_kennung))
    ohne_tabelle = v.deckung_aus_bildern(ki, grund, True, maske=HAUS_UND_BAUM)
    assert ohne_tabelle["urteil"] == v.DECKUNGSGLEICH       # Baum zählt mit — der Fall von 347
    mit = v.deckung_aus_bildern(ki, grund, True, maske=HAUS_UND_BAUM,
                                material_id_png=idpass, tabelle=TABELLE)
    assert mit["urteil"] == v.FORM_WEICHT_AB and mit["n_haus"] == sum(NUR_HAUS)


def test_ohne_brauchbare_maske_misst_sie_ganz_und_sagt_es(tmp_path):
    grund = _png(tmp_path / "g.png", _bild(_grund))
    ki = _png(tmp_path / "k.png", _bild(_ki_uebermalt))
    ohne = v.deckung_aus_bildern(ki, grund, True)
    assert ohne["bereich"] == v.DECKUNG_BEREICH_GANZ and "keine Bauwerksmaske" in ohne["bereich_grund"]
    assert ohne["kanten_iou"] == ohne["kanten_iou_ganz"]
    schief = v.deckung_aus_bildern(ki, grund, True, maske=[True] * 7)
    assert schief["bereich"] == v.DECKUNG_BEREICH_GANZ and "7 Punkte" in schief["bereich_grund"]
    winzig = [False] * (B * H)
    winzig[B * 10 + 10] = True
    klein = v.deckung_aus_bildern(ki, grund, True, maske=winzig)
    assert klein["bereich"] == v.DECKUNG_BEREICH_GANZ and "unter 1%" in klein["bereich_grund"]


def test_abholer_reicht_maske_und_id_pass_durch(tmp_path):
    grund = _png(tmp_path / "g.png", _bild(_grund))
    ki = _png(tmp_path / "k.png", _bild(_ki_uebermalt))
    bericht = {"material_id_png": _png(tmp_path / "id.png", _bild(_kennung)),
               "material_id_tabelle": TABELLE}
    d = abholer.deckung_der_kamera(ki, grund, HAUS_UND_BAUM, bericht)
    assert d["urteil"] == v.FORM_WEICHT_AB and d["bereich"] == v.DECKUNG_BEREICH_HAUS
    # Ohne Maske wie bisher (ganz) — die alte Aufrufform gilt weiter.
    assert abholer.deckung_der_kamera(ki, grund)["bereich"] == v.DECKUNG_BEREICH_GANZ


def test_der_satz_folgt_der_haus_zahl_im_ergebnis():
    """Die Zahl in ``qa_je_kamera[].deckung`` ist jetzt die im Haus; der Satz folgt ihr —
    und die Oberfläche liest zuerst den Satz (``formWeichtAbLautErgebnis``)."""
    u = {"kamera": "sSE", "score": 0.95, "bestanden": True, "geom_iou": 0.96}
    je = [dict(u, deckung=0.103)]                     # 347 T3 im Haus (ganz wäre 0,297)
    aus = kosmo_szene.als_ergebnis("vis-1", ["sSE.png"], geometrie_urteil=u, je_kamera=je)
    assert any(h.startswith(kosmo_szene.SATZ_FORM_WEICHT_AB) for h in aus["qa"]["verdict"]["hinweise"])
    voll = kosmo_szene.als_ergebnis("vis-2", ["sSE.png"], geometrie_urteil=u,
                                    je_kamera=[dict(u, deckung=0.6775)])
    assert not any(h.startswith(kosmo_szene.SATZ_FORM_WEICHT_AB)
                   for h in voll["qa"]["verdict"].get("hinweise", []))


# ============================================================ 2 · die Schwelle, im Haus geprüft

#: Kanten-IoU in der Bauwerksmaske, aus den Ergebnissen (Augenurteil «Form wie Grundbild»).
HAUS_WERTE = {
    "346 S2m Vorschau": (0.0942, False), "347 T3 Vorschau": (0.103, False),
    "339 KS": (0.1153, False), "337 K / 340 V-0": (0.2073, False), "337 K-S": (0.2102, False),
    "337 BI65-S": (0.2702, True), "337 BI65": (0.2732, True), "337 BI50": (0.3337, True),
    "340 V-A": (0.3754, True), "339 BS50": (0.4384, True), "346 V06": (0.5246, True),
    "347 T2 voll": (0.6775, True), "346 S3": (0.7447, True),
}


def test_die_schwelle_trennt_auch_im_haus():
    for lauf, (iou, form_ja) in HAUS_WERTE.items():
        assert (v.deckung(True, iou)["urteil"] == v.DECKUNGSGLEICH) is form_ja, lauf
    nein = max(i for i, ja in HAUS_WERTE.values() if not ja)
    ja = min(i for i, ja in HAUS_WERTE.values() if ja)
    assert nein < v.DECKUNG_KANTEN_IOU_SCHWELLE < ja
    assert "nur im Haus" in v.DECKUNG_HERKUNFT


def test_die_oberflaeche_fuehrt_dieselbe_zahl():
    """Die Rückfall-Schwelle drüben (``DECKUNG_SCHWELLE``) bleibt gleich — darum blieb 0,25."""
    ts = (Path(__file__).resolve().parents[1] / "kosmovis" / "apps" / "kosmo-orbit" / "src"
          / "modules" / "vis" / "grossansicht.ts")
    if ts.is_file():
        assert f"DECKUNG_SCHWELLE = {v.DECKUNG_KANTEN_IOU_SCHWELLE};" in ts.read_text(encoding="utf-8")


# ============================================================ 3 · KI-Zeit mit Ladeanteil

class _Modell:
    def __call__(self, parameter):
        from conftest import MINI_PNG
        Path(parameter["ausgabe_png"]).write_bytes(MINI_PNG)
        return parameter["ausgabe_png"]


def _auftrag(tmp_path):
    from conftest import MINI_PNG
    tiefe = tmp_path / "tiefe.png"
    tiefe.write_bytes(MINI_PNG)
    return render.RenderAuftrag(depth_png=str(tiefe), prompt="a house",
                                backbone="z-image-turbo", seed=1,
                                ausgabe_png=str(tmp_path / "bild.png"))


def test_das_bildmodell_meldet_seine_ladezeit(tmp_path, monkeypatch):
    monkeypatch.setattr(render, "gib_grafikspeicher_frei", lambda: {"satz": "frei"})
    geladen = render.rendere(_auftrag(tmp_path), _lader=lambda name, wurzel=None: _Modell())
    assert geladen["status"] == "ok", geladen["error"]
    assert isinstance(geladen["laden_s"], float) and 0.0 <= geladen["laden_s"] <= geladen["dauer_s"]
    uebergeben = render.rendere(_auftrag(tmp_path), modell=_Modell())
    assert uebergeben["laden_s"] is None                  # nichts geladen: reine Rechenzeit
    def lader(name, wurzel=None):
        return _Modell()

    with render.ein_modell_je_auftrag():
        erst = render.rendere(_auftrag(tmp_path), _lader=lader)
        dann = render.rendere(_auftrag(tmp_path), _lader=lader)
    assert erst["laden_s"] is not None and dann["laden_s"] is None   # zweites aus dem Vorrat


def test_das_kameraurteil_traegt_die_ki_zeit():
    assert abholer.ki_zeit_aus({"dauer_s": 52.8, "laden_s": 19.5}) == {
        "dauer_s": 52.8, "laden_s": 19.5, "rechnen_s": 33.3}
    assert abholer.ki_zeit_aus({"dauer_s": 33.0, "laden_s": None}) == {
        "dauer_s": 33.0, "laden_s": None, "rechnen_s": 33.0}
    assert abholer.ki_zeit_aus({"dauer_s": True}) is None
    assert abholer.ki_zeit_aus(None) is None
    quelle = Path(abholer.__file__).read_text(encoding="utf-8")
    assert "ki_zeit=ki_zeit_aus(ergebnis)" in quelle
