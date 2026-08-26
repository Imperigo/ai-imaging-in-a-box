"""Die stille Verschärfung — und warum eine gemeldete Zahl tragen muss, wie sie entstand.

**Der Anlass ist eine Nebenwirkung einer Entscheidung, die etwas anderes bezweckte.** Am
23.08.2026 gingen die automatischen Richtungen von einer auf drei; gefragt und beantwortet
war die Renderzeit. Nicht gefragt war, was das mit dem Geometrie-Urteil macht — und das
ist das der **schwächsten** Kamera.

Ein Minimum fällt mit der Zahl der Ziehungen, ganz ohne dass sich an der Sache etwas
ändert: bei drei Ziehungen um 0,845 Streuungen. Wäre die Streuung zwischen Kameras so
gross wie die einzige, die dieses Projekt gemessen hat (0,2269 über Startwerte), wären
das **0,19** — mehr als jeder Parametereffekt, den die Kette je gezeigt hat (0,10–0,14).

Die Regel selbst bleibt: Ein Auftrag ist so gut wie sein schlechtestes Bild. Was sich
ändert, ist, dass die Zahl mitträgt, wie sie zustande kam.
"""
import math
import random
import statistics

import pytest

from aiimaging import abholer, geometrie_qa


# ======================================================================================
# Die Tabelle — nachgerechnet und nicht geglaubt
# ======================================================================================

@pytest.mark.parametrize("n, erwartet", [
    (1, 0.0), (2, 0.5642), (3, 0.8463), (4, 1.0294), (5, 1.1630),
])
def test_die_tabelle_stimmt_mit_der_extremwertstatistik(n, erwartet):
    """Die geschlossenen Werte für N ≤ 5 sind bekannt; unsere simulierten müssen sie
    treffen. Eine simulierte Tabelle, die niemand gegen die Theorie hält, ist geraten."""
    assert geometrie_qa.minimum_abschlag(n) == pytest.approx(erwartet, abs=0.005)


def test_die_tabelle_stimmt_auch_gegen_eine_eigene_simulation():
    """Gegenprobe mit anderem Startwert und anderer Zahl von Ziehungen.

    Eine Tabelle, die nur die Simulation bestätigt, aus der sie stammt, bestätigt nichts.
    """
    wuerfel = random.Random(4711)
    for n in (2, 3, 5):
        proben = [min(wuerfel.gauss(0, 1) for _ in range(n)) for _ in range(60000)]
        assert -statistics.fmean(proben) == pytest.approx(
            geometrie_qa.minimum_abschlag(n), abs=0.02), n


def test_ein_wert_ist_sein_eigenes_minimum():
    assert geometrie_qa.minimum_abschlag(1) == 0.0


def test_jenseits_der_tabelle_wird_nicht_extrapoliert():
    """Eine erfundene Zahl sähe hier genau wie eine gerechnete aus."""
    assert geometrie_qa.minimum_abschlag(len(geometrie_qa.MINIMUM_ABSCHLAG)) is not None
    assert geometrie_qa.minimum_abschlag(len(geometrie_qa.MINIMUM_ABSCHLAG) + 1) is None
    for kaputt in (0, -3, 2.5, True, "drei", None):
        assert geometrie_qa.minimum_abschlag(kaputt) is None, kaputt


def test_der_abschlag_waechst_mit_der_zahl_der_kameras():
    tabelle = [geometrie_qa.minimum_abschlag(n)
               for n in range(1, len(geometrie_qa.MINIMUM_ABSCHLAG) + 1)]
    assert tabelle == sorted(tabelle)
    assert tabelle[0] < tabelle[2] < tabelle[-1]


# ======================================================================================
# Was im Ergebnis steht
# ======================================================================================

def _urteile(*scores):
    return [{"score": s} for s in scores]


def test_bei_drei_kameras_steht_die_spanne_und_der_abschlag_dabei():
    spanne = abholer._kameraspanne(_urteile(0.81, 0.66, 0.74))

    assert spanne["n"] == spanne["n_gemessen"] == 3
    assert spanne["bester"] == pytest.approx(0.81)
    assert spanne["schlechtester"] == pytest.approx(0.66)
    assert spanne["spanne"] == pytest.approx(0.15)
    assert spanne["abschlag_streuungen"] == pytest.approx(0.8453, abs=0.005)
    assert "SCHLECHTESTE" in spanne["hinweis"]


def test_bei_einer_kamera_gibt_es_keinen_auswahleffekt_und_das_steht_da():
    """Die Gegenprobe. Ohne sie stünde in jedem Ergebnis derselbe Satz, und niemand
    wüsste, ob er etwas bedeutet."""
    spanne = abholer._kameraspanne(_urteile(0.72))

    assert spanne["abschlag_streuungen"] == 0.0
    assert spanne["spanne"] is None
    assert spanne["streuung"] is None
    assert "ohne Auswahleffekt" in spanne["hinweis"]
    assert "SCHLECHTESTE" not in spanne["hinweis"]


def test_aus_zwei_werten_wird_keine_streuung_behauptet():
    """Ausrechnen liesse sie sich. Sie sagt nur nichts — dieselbe Regel wie in
    `varianten.rauschboden`."""
    assert abholer._kameraspanne(_urteile(0.8, 0.6))["streuung"] is None
    assert abholer._kameraspanne(_urteile(0.8, 0.6, 0.7))["streuung"] is not None


def test_ungemessene_kameras_zaehlen_mit_und_verschwinden_nicht():
    """Wer nur die gemessenen zählte, läse aus einer geschrumpften Reihe einen zu
    kleinen Auswahleffekt."""
    spanne = abholer._kameraspanne(_urteile(0.8, None, None))

    assert spanne["n"] == 3
    assert spanne["n_gemessen"] == 1
    assert spanne["abschlag_streuungen"] == 0.0, (
        "der Abschlag richtet sich nach den GEMESSENEN — eine ungemessene Kamera hat "
        "an keiner Auswahl teilgenommen"
    )


def test_gar_nichts_gemessen_heisst_ungeprueft_und_nicht_durchgefallen():
    spanne = abholer._kameraspanne(_urteile(None, None, None))

    assert spanne["schlechtester"] is None
    assert spanne["abschlag_streuungen"] is None
    assert "UNGEPRUEFT" in spanne["hinweis"]


def test_die_groessenordnung_die_den_anlass_gab():
    """0,845 Streuungen × 0,2269 ≈ 0,19 — und die Parametereffekte der Kette liegen bei
    0,10 bis 0,14. Die Zahl steht hier, weil sie der Grund für dieses ganze Modul ist."""
    from aiimaging import varianten

    kosten = geometrie_qa.minimum_abschlag(3) * varianten.GEMESSENE_SEED_STREUUNG
    assert kosten == pytest.approx(0.19, abs=0.01)
    assert kosten > 0.14, "groesser als jeder gemessene Parametereffekt"


# ======================================================================================
# Die Naht — ein Test am Baustein ersetzt keinen Test an der Naht
# ======================================================================================

def _verschiedene_sollkarten():
    """Je Aufruf eine andere Soll-Karte — siehe `tests/test_doppelansicht.py`."""
    zaehler = iter(range(1, 999))
    return lambda *a, **k: ([[float(next(zaehler))]], 1, 1)


def test_die_spanne_haengt_am_geometrie_urteil_des_auftrags(tmp_path):
    """Sonst wäre die ganze Rechnung eine tote Kante, und die Verschärfung bliebe still."""
    bild = tmp_path / "b.png"
    scores = iter([0.81, 0.66, 0.74])

    def multipass(glb, aus, **kw):
        from pathlib import Path
        tiefe = Path(aus) / "tiefe_norm.png"
        tiefe.write_bytes(b"\x89PNG\r\n\x1a\n")
        return {"depth_png": str(tiefe), "kamera": {"weg": "rueckfall"}}

    def rendere(auftrag, **kw):
        bild.write_bytes(b"\x89PNG\r\n\x1a\n")
        return {"status": "ok", "bild_png": str(bild), "hinweise": ()}

    verarbeite = abholer.verarbeiter(
        out_wurzel=tmp_path, nullprobe=False,
        _multipass=multipass, _rendere=rendere,
        _qa=lambda *a, **k: {"score": next(scores), "bestanden": True},
        # Je Kamera eine ANDERE Soll-Karte — drei byte-identische waeren seit dem
        # 26.08.2026 eine erkannte Doppelansicht, und `n_gemessen` waere dann 1.
        _soll=_verschiedene_sollkarten())

    ergebnis = verarbeite({"modell": tmp_path / "m.glb", "job_id": "vis-1-aaaaaa",
                           "verzeichnis": tmp_path,
                           "szene": {"kameras": "auto", "aufloesung": 64, "hoehe": 64,
                                     "samples": 1, "prompt": "a house"}})

    assert len(ergebnis["kameras"]) == 3, "die Vorgabe faehrt drei Richtungen"
    spanne = ergebnis["geometrie_urteil"]["kameraspanne"]
    assert spanne["n_gemessen"] == 3
    assert spanne["schlechtester"] == pytest.approx(0.66)
    assert ergebnis["geometrie_urteil"]["score"] == pytest.approx(0.66), (
        "gemeldet wird weiterhin das schlechteste — die Regel aendert sich nicht, "
        "nur ihre Sichtbarkeit"
    )
