"""Die Standpunkt-Studie — ohne Blender, ohne GPU.

*Der Anlass ist ein Folgeposten ohne Adressaten.* Die HomeStation hat am 01.09.2026 den
Kameraabstand berichtigt und in derselben Meldung geschrieben, die Streuung des
Flächenanteils falle am gedrungenen Bau von 2,3 auf 1,17 — «das schwächt
`guete_standpunkt` bei kompakten Bauten, und das ist ein Folgeposten, kein Nebensatz».

Ein Posten ohne Adressaten wird nie eingebaut, und es fällt keinem auf. Diese Studie ist
die Antwort darauf, und sie ist hier messbar: `kamerasatz` rechnet aus einer Hüllbox.
"""

import importlib.util
from pathlib import Path

from aiimaging import kameras


def _studie():
    pfad = Path(__file__).resolve().parents[1] / "tools" / "studie_standpunkte.py"
    spec = importlib.util.spec_from_file_location("werkzeug_studie_standpunkte", pfad)
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul


def test_die_formen_decken_wuerfelig_bis_langgestreckt_ab():
    """Eine Studie über Grundriss-Verhältnisse braucht verschiedene Verhältnisse — sonst
    misst sie einen Punkt und nennt ihn eine Kurve."""
    m = _studie()
    verhaeltnisse = [max(x, y) / min(x, y) for _, (x, y, _z) in m.FORMEN]
    assert min(verhaeltnisse) == 1.0, "ein würfeliger Grundriss gehört dazu"
    assert max(verhaeltnisse) >= 4.0, "und ein deutlich langgestreckter"


def test_der_wuerfel_hat_nur_eine_gueteklasse():
    """**Der Kernbefund.** Acht taugliche Standpunkte, ein einziger Wert: Die Rangfolge
    ordnet dort gar nichts."""
    z = _studie().messe("wuerfel", (20.0, 20.0, 20.0))
    assert z["n_tauglich"] == 8
    assert z["n_gueteklassen"] == 1
    assert z["n_gleichstand"] == 16


def test_keine_form_bringt_mehr_als_zwei_gueteklassen():
    m = _studie()
    for name, masse in m.FORMEN:
        assert m.messe(name, masse)["n_gueteklassen"] <= 2, name


def test_der_flaechenanteil_entscheidet_fast_nie():
    """Die Gegenprobe, die die Studie trägt: Ersetzt man ihn durch eine Konstante, ändert
    sich der beste Standpunkt in fünf von sechs Formen **nicht**."""
    m = _studie()
    entscheidet = [name for name, masse in m.FORMEN
                   if m.messe(name, masse)["flaechenanteil_entscheidet"]]
    assert len(entscheidet) == 1, entscheidet


def test_beim_riegel_zeigt_der_flaechenanteil_sogar_in_die_andere_richtung():
    """Der Sieger trägt **weniger** Bildfläche als die Unterlegenen — `zweite_fassade`
    überstimmt ihn. *Ein Mass, das man überstimmen muss, trägt die Auswahl nicht.*"""
    masse = (60.0, 12.0, 15.0)
    satz = kameras.kamerasatz([[0.0, 0.0, 0.0], list(masse)])
    bester = max(k.get("flaechenanteil") or 0.0 for k in satz["kameras"])
    bewertet = [(kameras.guete_standpunkt(k, masse, bester_flaechenanteil=bester), k)
                for k in satz["kameras"]]
    tauglich = [(g, k) for g, k in bewertet if g["taugt"]]
    sieger = max(tauglich, key=lambda p: p[0]["guete"])
    unterlegen = min(tauglich, key=lambda p: p[0]["guete"])
    assert sieger[0]["flaeche_norm"] < unterlegen[0]["flaeche_norm"]


def test_die_studie_nennt_keine_echten_bauten():
    """Regel 3, und hier ist sie leicht einzuhalten: Die Formen sind Kantenlängen."""
    m = _studie()
    for name, _masse in m.FORMEN:
        assert name.isascii() and name.islower()
