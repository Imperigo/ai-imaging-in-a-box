"""Ergebnis 344 (K4) — die Warnung «HAUS KAUM SICHTBAR» hängt am Kontrast am Umriss.

**Ergebnis auf-20261023-344 (Heim-PC, E-NEU und sSE, mittags und abends):** Mittags war das
Haus von Auge klar zu sehen, trotzdem stand «HAUS KAUM SICHTBAR» — Mittelwert −19,6 / −5,0,
Umriss 51,7 / 54,3. Sonnenseite (114/150), Schattenseite, Dach und Fenster mitteln sich auf
88/104, der Hintergrund liegt bei 106/108. Abends Mittel 72,1 / 41,7, Umriss 50,4 / 71,0.
Die Umrisszahl trifft das Auge, der Mittelwert täuscht.

Jetzt: je Kamera am Umriss (Schwelle ``belichtung.KONTRAST_UMRISS_SCHWELLE`` = 15); fehlt der
Umriss, gilt der Mittelwert wie bis 344. Der Mittelwert wird weiter berichtet.

Die Schwelle ist nachgerechnet, nicht am Gerät gemessen: an den acht Stimmungsbildern aus
auf-20261020-293 (im Repo) mit Augenurteil der HomeStation — die letzte Probe hier rechnet sie
nach. Jede andere Probe ist gegen den alten Stand rot. Regel 3: alle Zahlen synthetisch oder
aus den synthetischen Testbauten.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from aiimaging import belichtung, kosmo_szene

KAUM = kosmo_szene.SATZ_KAUM_SICHTBAR


def _urteil(kamera, mittel, umriss=None):
    kontrast = {"kontrast": mittel}
    if umriss is not None:
        kontrast["umriss"] = {"betrag": umriss, "kontrast": -umriss}
    return {"kamera": kamera, "score": None, "bestanden": None, "kontrast": kontrast}


def _ergebnis(*kameras):
    je = [{"kamera": k[0], "geometrie_urteil": _urteil(*k)} for k in kameras]
    return kosmo_szene.als_ergebnis("vis-1-abcdef", [f"{i}.png" for i in range(len(je))],
                                    geometrie_urteil=je[0]["geometrie_urteil"], je_kamera=je)


def _saetze(e):
    return [h for h in e["hinweise"] if h.startswith(KAUM)]


# ====================================================================== die 344-Werte

def test_344_mittags_keine_warnung_mehr():
    """GEGEN ALT ROT: «HAUS KAUM SICHTBAR … -5.0» stand, das Auge sah das Haus klar."""
    e = _ergebnis(("E-NEU", -19.6, 51.7), ("sSE", -5.0, 54.3))
    assert _saetze(e) == []
    # Der Mittelwert wird weiter berichtet, mit dem Umriss derselben Kamera daneben.
    assert e["qa"][kosmo_szene.FELD_KONTRAST] == -5.0
    assert e["qa"][kosmo_szene.FELD_KONTRAST_UMRISS] == 54.3


def test_344_abends_keine_warnung():
    e = _ergebnis(("E-NEU", 72.1, 50.4), ("sSE", 41.7, 71.0))
    assert _saetze(e) == []
    assert e["qa"][kosmo_szene.FELD_KONTRAST] == 41.7


# ====================================================================== kaum sichtbar am Umriss

def test_kaum_sichtbar_am_umriss_warnt_auch_bei_gutem_mittelwert():
    """GEGEN ALT ROT: Mittel +30 lag über 20 — keine Warnung, obwohl die Kante verschwimmt."""
    e = _ergebnis(("Eingang", 30.0, 8.0))
    satz, = _saetze(e)
    assert "'Eingang'" in satz and "am Umriss nur um 8.0" in satz
    assert "Schwelle 15" in satz and "+30.0" in satz, "Mittelwert steht dabei"


def test_kaum_sichtbar_aus_einem_bild():
    """Ein Haus, gleich hell wie der Himmel daneben: Umriss ~0 → Warnung, am echten Rechenweg."""
    b, h = 40, 30
    haus = [10 <= x < 30 and 10 <= y < h for y in range(h) for x in range(b)]
    farben = [(132, 132, 132) if m else (130, 130, 130) for m in haus]
    befund = belichtung.kontrast_haus_hintergrund(farben, b, h, haus=haus,
                                                   hintergrund=[not m for m in haus])
    assert befund["umriss"]["betrag"] < belichtung.KONTRAST_UMRISS_SCHWELLE
    urteil = {"kamera": "sSE", "score": None, "bestanden": None, "kontrast": befund}
    e = kosmo_szene.als_ergebnis("vis-1-abcdef", ["a.png"], geometrie_urteil=urteil,
                                 je_kamera=[{"kamera": "sSE", "geometrie_urteil": urteil}])
    assert len(_saetze(e)) == 1 and "am Umriss" in _saetze(e)[0]


def test_die_schlechteste_kamera_am_umriss_wird_genannt():
    e = _ergebnis(("A", -2.0, 40.0), ("B", 25.0, 12.0), ("C", 60.0, 5.0))
    satz, = _saetze(e)
    assert "'C'" in satz and "5.0" in satz
    assert e["qa"][kosmo_szene.FELD_KONTRAST] == -2.0, "qa bleibt beim kleinsten Mittelwert"


# ====================================================================== Rückfall ohne Umriss

def test_ohne_umriss_gilt_der_mittelwert():
    """Alte Läufe (vor 343) und fehlgeschlagene Umriss-Messung: Regel wie bis 344."""
    e = _ergebnis(("s", 42.0), ("sSE", -3.5))
    satz, = _saetze(e)
    assert "'sSE'" in satz and "-3.5" in satz and "es gilt der Mittelwert" in satz
    assert kosmo_szene.FELD_KONTRAST_UMRISS not in e["qa"], "kein null"
    assert _saetze(_ergebnis(("s", 42.0))) == []


def test_gemischt_je_kamera_die_eigene_regel():
    """Kamera A hat den Umriss (sichtbar), B nicht (Mittel −8) → Warnung für B."""
    e = _ergebnis(("A", -5.0, 54.0), ("B", -8.0))
    satz, = _saetze(e)
    assert "'B'" in satz and "es gilt der Mittelwert" in satz


def test_die_regel_als_funktion():
    s = belichtung.KONTRAST_UMRISS_SCHWELLE
    assert belichtung.haus_kaum_sichtbar(-5.0, 54.3) == (False, "umriss")
    assert belichtung.haus_kaum_sichtbar(30.0, s - 0.1) == (True, "umriss")
    assert belichtung.haus_kaum_sichtbar(30.0, s) == (False, "umriss")
    assert belichtung.haus_kaum_sichtbar(-3.5, None) == (True, "mittelwert")
    assert belichtung.haus_kaum_sichtbar(42.0, None) == (False, "mittelwert")
    assert belichtung.haus_kaum_sichtbar(None, None) == (None, "")
    assert belichtung.haus_kaum_sichtbar(-3.5, True) == (True, "mittelwert"), "bool zählt nicht"
    assert "nicht am Geraet gemessen" in belichtung.KONTRAST_UMRISS_HERKUNFT


# ====================================================================== die Schwelle, nachgerechnet

_BILDER = (Path(__file__).resolve().parents[1] / "auftraege" / "ergebnisse"
           / "auf-20261020-293-bilder")

#: Augenurteil der HomeStation in auf-20261020-293 (``1_stimmungen.*.bild_kurz``).
_KAUM = ("winter", "morgen", "nebel", "bedeckt", "blaue-stunde")
_LESBAR = ("abend", "weiss", "mittag")


def test_die_schwelle_trennt_die_293_bilder():
    """Die einzigen Fälle mit echtem «kaum sichtbar»: Umriss nachgerechnet, Maske aus dem
    kontrastreichen Abendbild derselben Kamera (der ID-Pass liegt nicht im Repo)."""
    np = pytest.importorskip("numpy")
    image = pytest.importorskip("PIL.Image")

    def lade(name):
        a = np.asarray(image.open(_BILDER / f"1-stimmung-{name}-sSE.png").convert("RGB"),
                       dtype=float)
        return a, 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]

    _, grau = lade("abend")
    hoehe, breite = grau.shape
    zeile = np.median(np.concatenate([grau[:, :40], grau[:, -40:]], 1), 1)[:, None]
    abstand = np.abs(grau - zeile)
    y = np.arange(hoehe)[:, None]
    haus = (abstand > 6) & (y < 185)                       # über der Platte
    platte = (abstand > 2) & (y >= 183) & (y <= 199)
    grund = ~haus & ~platte
    umriss = {}
    for name in _KAUM + _LESBAR:
        farben, _ = lade(name)
        befund = belichtung.kontrast_am_umriss(
            [tuple(p) for p in farben.reshape(-1, 3)], breite, hoehe,
            haus=haus.ravel().tolist(), hintergrund=grund.ravel().tolist())
        umriss[name] = befund["betrag"]
    s = belichtung.KONTRAST_UMRISS_SCHWELLE
    assert max(umriss[n] for n in _KAUM) < s <= min(umriss[n] for n in _LESBAR), umriss
    # Die alte Zahl 20 hätte abend (~18) und weiss (~19) fälschlich gewarnt.
    assert min(umriss[n] for n in _LESBAR) < belichtung.KONTRAST_SCHWELLE
