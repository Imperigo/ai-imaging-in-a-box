"""Füllt das Haus weniger als 20 % des Bildes, ist das Urteil «nicht beurteilbar».

**Owner-Entscheid 08.10.2026** (Visbox-Entscheid 70, per Auswahl; Befund ``auf-20261008-265``):
Am Demohaus aus KosmoOrbit — ein Modell ohne Boden — füllte das Haus 17–20 % des Bildes. Dort
ist der Gesamtwert nach eigener Messung rechnerisch unerreichbar
(``geometrie_qa.ANTEIL_GEMESSEN_NIEDRIG``), und jedes Bild fiel durch, egal wie gut. Die
Gebäude-Prüfung kann nicht einspringen: Sie urteilt seit dem 30.09.2026 nicht
(``geometrie_qa.PAARURTEIL_URTEILT``). Also die dritte Antwort, mit Grund, und die Gebäude-Zahl
als Auskunft. Ab 20 % bleibt alles wie bisher.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from aiimaging import geometrie_qa
from aiimaging import tiefenschaetzer as ts
from test_tiefenschaetzer import attrappe

B = 32


def _szene(seite: int, *, verkehrt: bool = False):
    """Ein quadratisches Haus der Kantenlänge ``seite`` vor Himmel, mittig im Bild."""
    von = (B - seite) // 2
    bis = von + seite - 1
    maske = [(von <= x <= bis and von <= y <= bis) for y in range(B) for x in range(B)]
    soll, n = [], 0
    for m in maske:
        if m:
            soll.append(10.0 + 10.0 * n / sum(maske))
            n += 1
        else:
            soll.append(float("inf"))
    # Ist als Disparität (nah = gross); `verkehrt` dreht die Ordnung auf dem Haus um.
    ist = []
    for s in soll:
        if s == float("inf"):
            ist.append(0.001)
        else:
            ist.append(s / 400.0 if verkehrt else 1.0 / s)
    return soll, ist, maske


@pytest.fixture()
def bild(tmp_path) -> Path:
    pfad = tmp_path / "bild.png"
    pfad.write_bytes(b"\x89PNG\r\n\x1a\n")
    return pfad


def _urteil(bild, seite, **kw):
    soll, ist, maske = _szene(seite, **kw)
    return ts.qa_gegen_soll(bild, soll, modell=attrappe(ist), breite=B, hoehe=B,
                            maske=maske)


def test_die_grenze_ist_die_gemessene_untere_marke():
    assert geometrie_qa.ANTEIL_GEMESSEN_NIEDRIG == 0.20


def test_ein_kleines_haus_ist_nicht_beurteilbar_statt_durchgefallen(bild):
    urteil = _urteil(bild, 12)                      # 144 / 1024 = 14 %
    assert urteil["anteil_soll"] == pytest.approx(144 / 1024)
    assert urteil["gesamtwert_anwendbar"] is False
    assert urteil["bestanden"] is None
    assert urteil["begruendung"].startswith("Nicht beurteilbar — das Haus füllt nur 14.1%")
    assert "der Gesamtwert ist hier nicht anwendbar" in urteil["begruendung"]


def test_die_gebaeude_zahl_steht_als_auskunft_daneben(bild):
    urteil = _urteil(bild, 12)
    assert "Gebäude-Prüfung als Auskunft (nicht geeicht, urteilt nicht)" in urteil["begruendung"]
    assert urteil["rho_maske"] is not None          # gemessen, nur nicht urteilend


def test_auch_ein_schlechtes_kleines_bild_ist_nicht_durchgefallen(bild):
    """Der Entscheid sagt «statt durchgefallen» — auch dort, wo die Ordnung verkehrt ist.
    Ein Wert, der hier nicht anwendbar ist, kann weder freisprechen noch verurteilen."""
    urteil = _urteil(bild, 12, verkehrt=True)
    assert urteil["bestanden"] is None
    assert urteil["gesamtwert_anwendbar"] is False


def test_ab_zwanzig_prozent_bleibt_alles_wie_bisher(bild):
    urteil = _urteil(bild, 16)                      # 256 / 1024 = 25 %
    assert urteil["gesamtwert_anwendbar"] is True
    assert isinstance(urteil["bestanden"], bool)
    assert not urteil["begruendung"].startswith("Nicht beurteilbar")


def test_ohne_jede_geometrie_greift_die_regel_nicht(bild):
    """0 % ist kein kleines Haus, sondern keines — dafür gelten die bisherigen Wege."""
    soll = [float("inf")] * (B * B)
    urteil = ts.qa_gegen_soll(bild, soll, modell=attrappe([0.001] * (B * B)),
                              breite=B, hoehe=B)
    assert urteil.get("gesamtwert_anwendbar") is not False
    assert not urteil["begruendung"].startswith("Nicht beurteilbar")


def test_ein_nicht_beurteilbares_urteil_bleibt_im_zwischenspeicher():
    """Bis zum 08.10.2026 sagte der Prüfknoten ``bestanden`` als Pflichtfeld zu, und
    ``None`` galt als leer — jedes «nicht beurteilbar» wurde verworfen und neu gerechnet
    (an ``test_kette``: 3 statt 4 Treffer)."""
    from aiimaging import kette
    bedarf = kette.BEDARF[kette.ART_QA]
    assert bedarf.maengel({"status": "ok", "bestanden": None}) == []
    assert bedarf.maengel({"bestanden": True}) != []          # ohne status: kein Treffer


# ======================================================================================
# An der Vertragsgrenze zu KosmoOrbit: `passed` bleibt ein Wahrheitswert
# ======================================================================================
#
# Der Integrator meldete am 08.10.2026 (dringend): Sein Vertrag hat `passed: z.boolean()`;
# ein `null` wiese jedes Demohaus-Ergebnis ab. Unsere Übergabe macht aus der dritten
# Antwort schon immer `false` plus einen Satz in `verdict.reason` — hier festgehalten für
# den neuen Fall.

def _urteil_unter_zwanzig():
    return {"score": None, "spearman": None, "geom_iou": 0.0, "bestanden": None,
            "schwelle": 0.65, "anteil_soll": 0.179, "gesamtwert_anwendbar": False,
            "rho_maske": None}


def test_passed_bleibt_im_vertrag_ein_wahrheitswert():
    from aiimaging import kosmo_szene as ks
    e = ks.als_ergebnis("vis-20261008120000-abc123", ["a.png"],
                        geometrie_urteil=_urteil_unter_zwanzig())
    assert e["qa"]["geometry"]["passed"] is False
    assert e["qa"]["verdict"]["passed"] is False
    knapp = ks.nur_vertragsfelder(e)
    assert knapp["qa"]["verdict"]["passed"] is False


def test_der_grund_sagt_nicht_beurteilbar_und_nicht_durchgefallen():
    from aiimaging import kosmo_szene as ks
    e = ks.als_ergebnis("vis-20261008120000-abc123", ["a.png"],
                        geometrie_urteil=_urteil_unter_zwanzig())
    grund = ks.nur_vertragsfelder(e)["qa"]["verdict"]["reason"]
    assert grund.startswith("NICHT BEURTEILBAR (Gebaeudeanteil): Das Haus fuellt nur 17.9%")
    assert "nicht durchgefallen, sondern nicht beurteilbar" in grund
    assert "NICHT GEMESSEN" not in grund


def test_knapp_unter_zwanzig_wird_nicht_auf_zwanzig_gerundet():
    """0,199 stand am Gerät als «nur 20 % … weniger als 20 %» (``auf-20261008-267``)."""
    from aiimaging import kosmo_szene as ks
    urteil = dict(_urteil_unter_zwanzig(), anteil_soll=0.199)
    grund = ks.nur_vertragsfelder(ks.als_ergebnis(
        "vis-20261008120000-abc123", ["a.png"], geometrie_urteil=urteil))["qa"]["verdict"]["reason"]
    assert "nur 19.9%" in grund
