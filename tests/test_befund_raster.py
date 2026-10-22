"""Ein Befund ist Buchführung, kein Bildspeicher — Visbox-Mac-Prüfliste 0.3.35 (22.10.2026).

Im Auftrag mit vier Standpunkten (Grundbild und KI) war ``befund.json`` 93 MB gross. Die
Bauwerksmaske (``maskenbefund.maske``) und die Lage der Umgebung (``maskenbefund.kontext_pixel``)
sind Listen mit einem Wahrheitswert je Bildpunkt; mit ``indent=1`` stand jeder auf einer eigenen
Zeile, je Kamera, und das Urteil der massgebenden Kamera noch einmal unter ``geometrie_urteil``.

Seither stehen im Befund nur Verweis und Kennzahlen; die Rohdaten liegen gepackt daneben
(``befund_raster.json``) und kommen über ``abholer.lies_raster`` verlustfrei zurück. Synthetisch
(Regel 3): ein Streifenmuster, kein Bild aus einem Auftrag.
"""
import json

from aiimaging import abholer

BREITE, HOEHE = 400, 250  # 100 000 Bildpunkte — ein Sechzehntel eines 1600×1000-Bildes


def _maske(versatz: int = 0) -> list[bool]:
    return [((i + versatz) // 37) % 3 == 0 for i in range(BREITE * HOEHE)]


def _ergebnis(kameras: int = 4) -> dict:
    urteile = []
    for k in range(kameras):
        urteile.append({"kamera": f"k{k}", "rho": 0.8,
                        "maskenbefund": {"maske": _maske(k), "n_bildpunkte": BREITE * HOEHE,
                                         "kontext_pixel": _maske(k + 11),
                                         "gelaende_namen": ["Gelaende"]}})
    # Wie im Lauf: das Geometrie-Urteil IST das Urteil der massgebenden Kamera (dasselbe Objekt).
    return {"kameras": urteile, "geometrie_urteil": urteile[0], "bilder": []}


def test_der_befund_bleibt_klein_und_traegt_verweis_und_kennzahlen(tmp_path):
    ergebnis = _ergebnis()
    abholer._befund_ablegen(tmp_path, {"job_id": "vis-1792688229-591d59"}, ergebnis, {})
    befund = tmp_path / abholer.DATEI_BEFUND
    # Ohne Auslagerung wären es bei 4 Kameras × 2 Raster (+1 doppelt) rund 7 MB; mit ihr ein paar KB.
    assert befund.stat().st_size < 20_000, befund.stat().st_size
    gelesen = abholer.lies_befund(tmp_path)
    mb = gelesen["kameras"][1]["maskenbefund"]
    assert mb["maske"] == {"ausgelagert": abholer.DATEI_BEFUND_RASTER,
                           "schluessel": "$.kameras[1].maskenbefund.maske",
                           "laenge": BREITE * HOEHE, "wahr": sum(_maske(1))}
    assert mb["n_bildpunkte"] == BREITE * HOEHE and mb["gelaende_namen"] == ["Gelaende"]


def test_die_rohdaten_kommen_verlustfrei_zurueck(tmp_path):
    ergebnis = _ergebnis()
    abholer._befund_ablegen(tmp_path, {"job_id": "x"}, ergebnis, {})
    gelesen = abholer.lies_befund(tmp_path)
    for k in range(4):
        mb = gelesen["kameras"][k]["maskenbefund"]
        assert abholer.lies_raster(tmp_path, mb["maske"]) == _maske(k)
        assert abholer.lies_raster(tmp_path, mb["kontext_pixel"]) == _maske(k + 11)
    raster = tmp_path / abholer.DATEI_BEFUND_RASTER
    assert raster.stat().st_size < 200_000, "gepackt: ein Bit je Bildpunkt, zlib"


def test_ein_doppelt_vorkommendes_raster_wird_einmal_abgelegt(tmp_path):
    abholer._befund_ablegen(tmp_path, {"job_id": "x"}, _ergebnis(), {})
    gelesen = abholer.lies_befund(tmp_path)
    assert (gelesen["geometrie_urteil"]["maskenbefund"]["maske"]["schluessel"]
            == "$.kameras[0].maskenbefund.maske")
    roh = json.loads((tmp_path / abholer.DATEI_BEFUND_RASTER).read_text(encoding="utf-8"))
    assert len(roh["raster"]) == 8  # 4 Kameras × (maske, kontext_pixel), nicht 10


def test_auch_das_kameraurteil_lagert_aus(tmp_path):
    urteil = _ergebnis(1)["kameras"][0]
    abholer._urteil_ablegen(tmp_path / "k0", urteil)
    datei = tmp_path / "k0" / abholer.DATEI_URTEIL
    assert datei.stat().st_size < 10_000
    verweis = json.loads(datei.read_text(encoding="utf-8"))["urteil"]["maskenbefund"]["maske"]
    assert verweis["ausgelagert"] == abholer.DATEI_URTEIL_RASTER
    assert abholer.lies_raster(tmp_path / "k0", verweis) == _maske(0)


def test_kurze_listen_und_kleine_masken_bleiben_im_befund(tmp_path):
    klein = {"kameras": [{"maskenbefund": {"maske": [True, False, True]}}],
             "bilder": ["a.png"]}
    abholer._befund_ablegen(tmp_path, {"job_id": "x"}, klein, {})
    gelesen = abholer.lies_befund(tmp_path)
    assert gelesen["kameras"][0]["maskenbefund"]["maske"] == [True, False, True]
    assert not (tmp_path / abholer.DATEI_BEFUND_RASTER).exists(), "ohne Raster keine Rasterdatei"


def test_ein_fehlender_oder_fremder_verweis_ist_eine_auskunft(tmp_path):
    assert abholer.lies_raster(tmp_path, None) is None
    assert abholer.lies_raster(tmp_path, [True]) is None
    assert abholer.lies_raster(tmp_path, {"ausgelagert": "befund_raster.json",
                                          "schluessel": "$.x", "laenge": 3}) is None
