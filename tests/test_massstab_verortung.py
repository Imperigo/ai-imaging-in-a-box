"""Der Massstab des Splats aus der Verortung — gelesen zur Auskunft, gesagt im Urteil.

KosmoPrepare (14.10.2026) schreibt in ``splat.verortung.json`` einen Block ``massstab``: Wert
aus der Bewegung der Kamera (IMU), Unsicherheit, eine Gegenprobe aus der Einzelbildtiefe und
eine **Ampel**, die KosmoPrepare setzt. Visbox rechnet damit nicht (die Lage steht in
``context.transform``), sondern sagt im Urteil, wie verlässlich der Massstab ist.

Das Beispiel unten hat KosmoPrepare mit echten Zahlen geschickt, **ohne Ortsangaben** (Regel 3).
"""
from __future__ import annotations

import json

import pytest

from aiimaging import kosmo_szene as ks

#: Wörtlich wie von KosmoPrepare geschickt (14.10.2026), dazu `drift_rel`.
BEISPIEL = {"massstab": {
    "wert": 5.094, "einheit": "m je Modelleinheit (COLMAP = Splat)", "unsicherheit_abs": 0.275,
    "unsicherheit_rel": 0.054, "herkunft": "imu",
    "verfahren": "IMU-Beschleunigung gegen COLMAP-Bahn, Band 0.05-0.5 Hz, Median ueber 21 "
                 "Fenster zu 10s",
    "imu": {"zeitversatz_s": 0.232, "drehung_rest_grad": 0.171, "gyro_skala": 0.9969,
            "fenster_streuung": 0.468, "korrelation_global": 0.8837},
    "gegenprobe": {"herkunft": "moge-2 (metrische Einzelbildtiefe)", "wert": 6.1322,
                   "streuung_bilder": 1.1429, "abweichung_rel": 0.204},
    "ampel": "gelb", "handlung": "uebernehmen, Hinweis zeigen und um ein Kontrollmass bitten",
    "gruende": ["Unsicherheit A 5.4 % > 5 %", "Gegenprobe weicht 20 % ab (> 15 %)"],
    "drift_rel": 0.08}}


def _datei(tmp_path, inhalt, name="splat.verortung.json"):
    p = tmp_path / "geheim" / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(inhalt if isinstance(inhalt, str) else json.dumps(inhalt), encoding="utf-8")
    return p


def test_gelb_sagt_unsicher_mit_gruenden_und_bittet_um_ein_kontrollmass(tmp_path):
    vermerk, saetze = ks.massstab_aus_verortung(_datei(tmp_path, BEISPIEL))
    assert vermerk == {"wert": 5.094, "einheit": "m je Modelleinheit (COLMAP = Splat)",
                       "unsicherheit_rel": 0.054, "herkunft": "imu", "ampel": "gelb",
                       "gegenprobe_rel": 0.204, "drift_rel": 0.08}
    (satz,) = saetze                                  # 8 % Drift: kein eigener Satz
    assert "UNSICHER" in satz and "5.09 m je Modelleinheit" in satz and "± 5 %" in satz
    assert "Gegenprobe weicht 20 % ab" in satz and "Kontrollmass" in satz
    assert "IMU" in satz


@pytest.mark.parametrize("ampel, muss, darf_nicht", [
    ("gruen", "aus der Bewegung der Kamera (IMU): 5.09", "UNSICHER"),
    ("grün", "aus der Bewegung der Kamera (IMU): 5.09", "Kontrollmass"),
    ("rot", "NICHT VERLAESSLICH", "5.09"),
    ("violett", "ohne bekannte Ampel", "UNSICHER"),
])
def test_jede_ampel_hat_ihren_satz(tmp_path, ampel, muss, darf_nicht):
    roh = json.loads(json.dumps(BEISPIEL))
    roh["massstab"]["ampel"] = ampel
    vermerk, (satz,) = ks.massstab_aus_verortung(_datei(tmp_path, roh))
    assert muss in satz and darf_nicht not in satz, satz


def test_ein_handmass_gewinnt_und_wird_so_genannt(tmp_path):
    roh = {"massstab": {"wert": 5.3, "herkunft": "hand", "ampel": "gruen"}}
    _, (satz,) = ks.massstab_aus_verortung(_datei(tmp_path, roh))
    assert satz == "KONTEXT, Massstab von Hand gemessen: 5.30 m je Modelleinheit."


def test_drift_ueber_zehn_prozent_bekommt_einen_eigenen_satz(tmp_path):
    roh = json.loads(json.dumps(BEISPIEL))
    roh["massstab"]["drift_rel"] = 0.12
    _, saetze = ks.massstab_aus_verortung(_datei(tmp_path, roh))
    assert len(saetze) == 2 and "entlang des Wegs um 12 %" in saetze[1]


def test_ohne_datei_oder_block_kein_satz_unlesbar_ein_satz_ohne_pfad(tmp_path):
    assert ks.massstab_aus_verortung(tmp_path / "fehlt.json") == (None, [])
    assert ks.massstab_aus_verortung(_datei(tmp_path, {"lage": {}})) == (None, [])
    vermerk, (satz,) = ks.massstab_aus_verortung(_datei(tmp_path, "{kaputt"))
    assert vermerk is None and "nicht lesbar" in satz
    assert str(tmp_path) not in satz and "geheim" not in satz


def test_die_bestellung_traegt_den_satz_ins_urteil_und_den_vermerk_ohne_pfad(tmp_path):
    ply = tmp_path / "splat.ply"
    ply.write_bytes(b"ply\n")
    verortung = _datei(tmp_path, BEISPIEL)
    k = ks.kontext_aus_szene({"kind": "splat", "ply": str(ply), "verortung": str(verortung),
                              "fit": "behelf"})
    assert not k["maengel"] and k["massstab"]["ampel"] == "gelb"
    assert any("Massstab UNSICHER" in h for h in k["hinweise"])
    vermerk = ks.kontext_vermerk(k)
    assert vermerk["massstab"]["wert"] == 5.094
    assert str(tmp_path) not in json.dumps(vermerk, ensure_ascii=False)
    assert any("Massstab UNSICHER" in s for s in ks.kontext_saetze(vermerk))
