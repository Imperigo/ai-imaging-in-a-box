"""Der Deckel von ``geom_iou`` — woran er liegt und woran nicht.

Der Anlass
----------
``geometrie_qa.IOU_DECKEL`` hält fest, dass ``geom_iou`` an einer echten Szene bei 0.256
bzw. 0.406 deckelt, während die Schwelle 0.4225 bräuchte. Daraus wurde in `PLAN.md` eine
offene Aufgabe: *«Trägt eine Kombination `ohne_randberuehrung` plus `rand_10`?»* — **sie
zielt auf die Regel.**

Diese Datei hält die Messung fest, die zeigt, dass die Regel es **nicht** ist.

Was hier NICHT geprüft wird
---------------------------
Was ein echter Tiefenschätzer tut. Der perfekte Schätzer ist **nachgestellt** — Blenders
eigene Tiefe ohne Hintergrundmarke. Die Vorhersage über den echten Schätzer steht in
`auf-20260826-55` zur Prüfung.
"""
from __future__ import annotations

import math

import pytest

from aiimaging import deckelstudie as ds
from aiimaging import geometrie_qa

#: Eine kleine Szene von Hand: ein 4 × 4-Block Geometrie in einem 10 × 10-Bild.
#: Handgebaut und nicht gerendert, damit dieser Test ohne Blender läuft — die Aussagen
#: sind geometrisch und brauchen kein Bauwerk.
BREITE = HOEHE = 10


def _szene():
    """``(soll, karte)`` — Soll mit ``inf``-Hintergrund, Karte als perfekte Disparität."""
    soll, karte = [], []
    for y in range(HOEHE):
        for x in range(BREITE):
            drin = 3 <= x < 7 and 3 <= y < 7
            # Tiefe 5..8 m im Block, sonst Hintergrund.
            #
            # Der Hintergrund ist ein GROSSER ENDLICHER Wert und nicht `inf` — so, wie
            # Blender ihn wirklich schreibt und wie `silhouette` ihn liest
            # (`HINTERGRUND_SCHWELLE_M` = 1e6). Mit `inf` liefe dieser Test an der
            # Wirklichkeit vorbei: `geometrie_qa.spearman` weist `inf` ab, ein grosser
            # endlicher Wert geht durch — und genau daran entsteht die irreführende
            # Zahl, gegen die der letzte Test hier gebaut ist.
            tiefe = 5.0 + (x - 3) * 0.5 if drin else 1e10
            soll.append(tiefe)
            # Disparität: nah = gross. Hintergrund bekommt den KLEINSTEN Wert — so, wie
            # es sein sollte und wie ein Schätzer es gerade nicht tut.
            karte.append((1.0 / tiefe) if drin else 0.0)
    assert len(soll) == BREITE * HOEHE
    return soll, karte


def test_die_aufteilung_kommt_aus_der_sollkarte():
    """Nur die EXR weiss es exakt — jede Aussage dieser Studie hängt daran."""
    soll, _ = _szene()
    lage = ds.teile_auf(soll)
    assert lage["n_geometrie"] == 16
    assert lage["anteil"] == pytest.approx(0.16)
    assert len(lage["hintergrund"]) == 84


def test_eine_perfekte_karte_ergibt_eine_perfekte_silhouette():
    """**Die Kernaussage.** Die Regel deckelt nicht — sie erreicht 1.0."""
    soll, karte = _szene()
    r = ds.iou_gegen_soll(soll, karte, breite=BREITE, hoehe=HOEHE)
    assert r["iou"] == pytest.approx(1.0)
    assert r["rho_geometrie"] == pytest.approx(1.0)


# ── Fall A · Rauschen auf der Geometrie ──────────────────────────────────────────────

def test_rauschen_auf_der_geometrie_laesst_die_silhouette_weitgehend_stehen():
    """Die Regel ist gegen Ordnungsfehler **innerhalb** der Geometrie robust.

    An der gerenderten Szene gemessen: Selbst bei |rho| 0.393 bleibt IoU bei 0.765.
    """
    soll, karte = _szene()
    gestoert = ds.rauschen_auf_geometrie(soll, karte, 0.05, saat=1)
    r = ds.iou_gegen_soll(soll, gestoert, breite=BREITE, hoehe=HOEHE)
    assert r["iou"] > 0.9, (
        "Schon geringes Rauschen auf der Geometrie zerstört die Silhouette — dann misst "
        "diese Studie etwas anderes als gedacht."
    )


def test_das_rauschen_laesst_den_hintergrund_in_ruhe():
    """Sonst wäre Fall A nicht von Fall B zu trennen, und die ganze Trennung wertlos."""
    soll, karte = _szene()
    gestoert = ds.rauschen_auf_geometrie(soll, karte, 0.5, saat=1)
    lage = ds.teile_auf(soll)
    assert all(gestoert[i] == karte[i] for i in lage["hintergrund"])
    assert any(gestoert[i] != karte[i] for i in lage["geometrie"])


# ── Fall B · Der Hintergrund rückt hinein ────────────────────────────────────────────

def test_der_hintergrund_im_bauwerksbereich_zerstoert_die_silhouette():
    """**Der Befund.** Die Rangkorrelation bleibt exakt 1.0, IoU bricht ein.

    Das ist die Fehlerform, die zur gemessenen Produktionszahl passt: |spearman| 0.990
    bei geom_iou 0.406 — mit Ordnungsrauschen allein nicht erklärbar.
    """
    soll, karte = _szene()
    verschoben = ds.hintergrund_verschieben(soll, karte, 0.5)
    r = ds.iou_gegen_soll(soll, verschoben, breite=BREITE, hoehe=HOEHE)
    assert r["rho_geometrie"] == pytest.approx(1.0), (
        "Die Geometrie muss unangetastet bleiben — sonst vermischt der Fall die beiden "
        "Fehlerquellen, die er gerade trennen soll."
    )
    assert r["iou"] < 0.75, f"IoU {r['iou']:.3f} — der Hintergrund stört gar nicht?"


def test_ganz_hinein_geschoben_bleibt_nichts_uebrig():
    """Die Gegenprobe am Extrem: Hintergrund am nächsten Bauwerkswert."""
    soll, karte = _szene()
    r = ds.iou_gegen_soll(soll, ds.hintergrund_verschieben(soll, karte, 1.0),
                          breite=BREITE, hoehe=HOEHE)
    assert r["iou"] < 0.1


@pytest.mark.parametrize("anteil", [0.0, 0.25, 0.5, 0.75, 1.0])
def test_je_weiter_hinein_desto_schlechter(anteil):
    """Monoton — sonst wäre die Umkehrung (aus IoU auf die Lage schliessen) unzulässig."""
    soll, karte = _szene()
    r = ds.iou_gegen_soll(soll, ds.hintergrund_verschieben(soll, karte, anteil),
                          breite=BREITE, hoehe=HOEHE)
    voriges = ds.iou_gegen_soll(soll, ds.hintergrund_verschieben(soll, karte, 0.0),
                                breite=BREITE, hoehe=HOEHE)
    assert r["iou"] <= voriges["iou"] + 1e-9


# ── Die Prüfgrösse ───────────────────────────────────────────────────────────────────

def test_wo_liegt_der_himmel_bei_einer_sauberen_karte():
    """0.0 heisst: am fernsten Bauwerkswert oder darunter — sauber getrennt."""
    soll, karte = _szene()
    h = ds.wo_liegt_der_himmel(soll, karte)
    assert h["lage"] == pytest.approx(0.0) or h["ausserhalb"]


def test_wo_liegt_der_himmel_findet_die_verschiebung_wieder():
    """**Die Umkehrung, und sie ist der Zweck der Zahl.**

    Aus einem gemessenen `geom_iou` soll sich auf die Lage des Himmels schliessen lassen.
    Dafür muss die Zahl wiederfinden, was hineingelegt wurde.
    """
    soll, karte = _szene()
    for anteil in (0.25, 0.5, 0.75):
        h = ds.wo_liegt_der_himmel(soll, ds.hintergrund_verschieben(soll, karte, anteil))
        assert h["lage"] == pytest.approx(anteil, abs=0.02)


# ── Was die Studie über sich selbst sagt ────────────────────────────────────────────

def test_die_korrelation_wird_ueber_die_geometrie_gerechnet_und_nicht_ueber_alles():
    """**Der Fehler des ersten Anlaufs**, und er steht im Docstring.

    Über die ganze Karte gerechnet ist die Zahl wertlos: Die Hintergrundpunkte der
    Soll-Karte sind alle `inf` und damit rangleich; schon geringes Rauschen darauf lässt
    sie einbrechen, ohne dass sich an der Geometrie etwas geändert hätte.
    """
    soll, karte = _szene()
    gestoert = ds.hintergrund_verschieben(soll, karte, 0.5)
    ueber_geometrie = ds.iou_gegen_soll(soll, gestoert,
                                        breite=BREITE, hoehe=HOEHE)["rho_geometrie"]
    assert ueber_geometrie == pytest.approx(1.0)
    # Und die andere, falsche Rechnung — sie darf NICHT dasselbe ergeben.
    ueber_alles = abs(geometrie_qa.spearman(soll, gestoert))
    assert ueber_alles != pytest.approx(1.0), (
        "Über die ganze Karte gerechnet ergibt die Korrelation dasselbe — dann ist der "
        "Unterschied, gegen den dieser Test gebaut ist, verschwunden."
    )


def test_eine_szene_ohne_hintergrund_wird_abgelehnt():
    """Geraten wird nicht: Ohne Hintergrund gibt es keine Lage."""
    soll = [1.0] * 16
    with pytest.raises(ds.DeckelError, match="Hintergrund"):
        ds.wo_liegt_der_himmel(soll, [1.0] * 16)


def test_unterschiedlich_lange_karten_werden_abgelehnt():
    with pytest.raises(ds.DeckelError, match="unterschiedlich lang"):
        ds.teile_auf([1.0, 2.0]) if False else ds.iou_gegen_soll(
            [1.0, 2.0], [1.0], breite=1, hoehe=2)
