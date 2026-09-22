"""Vier stille Stellen derselben Familie in der Kompositionsprüfung (Durchsicht 22.09.2026).

**(a) Der Rat schaltete die Prüfung ab.** `kameras.berichtsfelder_aus_stellung` schreibt
bei gesetztem Geländestand `gelaende_bezug="gesetzt"`; `komposition.BEZUGSPUNKTE` kannte
den Namen nicht, `kamerahoehe` warf, und der Abholer meldete «Komposition NICHT
beurteilbar». Genau der Handgriff, den `abholer._kompositionszeilen` empfiehlt
(`--gelaende-z`), schaltete damit die ganze Prüfung ab. Nachgetragen ist der Name als
**ungeprüfte Angabe** (`verlaesslich: None`) — nicht als verlässlicher Bezug.

**(b) Der Rollwinkel war eine Konstante.** `aufnahme` gab 0° zurück, ohne dass je ein
Aufrufer einen Rollwinkel gemeldet hätte. Fehlend bleibt jetzt fehlend.

**(c) Ein None ohne Namen.** `beurteile_kamerasatz` sagte `alle_waagrecht=None`, aber
nicht, welche Kamera die Neigung nicht gemeldet hatte.

**(d) Eine Zusage über ein anderes Modul, ohne Wächter.** «Neigungsangabe» und «Neigung»
sind absichtlich zwei Wörter, damit `abholer._kompositionszeilen` eine fehlende Angabe
und eine festgestellte Abweichung nicht zu einer Zeile verschmilzt.

Geprüft wird die Wirkung am Ergebnis, und wo es geht über den Weg, den ein Auftrag
wirklich nimmt: `abholer._komposition_vor_dem_render`.
"""
from __future__ import annotations

from aiimaging import abholer, kameras, komposition

BBOX = [[-8.0, -5.0, 0.0], [8.0, 5.0, 15.0]]


def _block(gelaende_z=None, **kw) -> dict:
    """Ein Kamerablock, wie ihn der Runner auf dem **vorgegebenen** Weg schreibt."""
    block = {
        "weg": "vorgegeben",
        "kuerzel": "sSE",
        "auge": [0.0, -35.0, 1.7],
        "blick_auf": [0.0, 0.0, 7.5],
        "brennweite_mm": 35.0,
        "seitenverhaeltnis": 1.0,
    }
    block.update(kameras.berichtsfelder_aus_stellung(
        block["auge"], block["blick_auf"], BBOX, brennweite_mm=35.0,
        gelaende_z=gelaende_z))
    block.update(kw)
    return block


def _produktweg(block: dict) -> dict:
    return abholer._komposition_vor_dem_render({"kamera": block})


def _zeilen(*paare) -> list:
    """Die Kurzbefund-Zeilen, gebaut aus Urteilen des Produktwegs."""
    return abholer._kompositionszeilen(
        [{"kamera": kuerzel, "komposition": urteil} for kuerzel, urteil in paare])


def _satz(*bloecke) -> dict:
    return {"kameras": list(bloecke), "gelaende_z": 0.0,
            "gelaende_bezug": "huellbox_unterkante",
            "mitte": [0.0, 0.0, 7.5], "masse_m": [16.0, 10.0, 15.0]}


# ======================================================================================
# (a) Ein gesetzter Geländestand — die Prüfung läuft, und die Angabe bleibt eine Angabe
# ======================================================================================

def test_ein_gesetzter_gelaendestand_laesst_die_pruefung_auf_dem_produktweg_laufen():
    """Der Befund selbst: mit `gelaende_z` war die Aufnahme «nicht beurteilbar»."""
    urteil = _produktweg(_block(gelaende_z=0.0))

    assert urteil["beurteilt"] is True, (
        f"wer den Geländestand setzt, darf die Prüfung nicht abschalten: {urteil['grund']}")
    assert urteil["kamerahoehe"]["bezugspunkt"] == "gesetzt"
    assert urteil["abbruch"] is False
    assert not any("NICHT beurteilbar" in z for z in _zeilen(("sSE", urteil)))


def test_der_empfohlene_handgriff_wirkt_und_der_rat_verschwindet():
    """Ohne Geländestand steht der Rat da; befolgt, entfällt er — und die Prüfung bleibt."""
    ohne = _zeilen(("sSE", _produktweg(_block())))
    mit = _zeilen(("sSE", _produktweg(_block(gelaende_z=0.0))))

    assert any("--gelaende-z" in z for z in ohne), "Vorbedingung: der Rat steht da"
    assert mit, "mit gesetztem Geländestand muss es weiterhin etwas zu melden geben"
    text = " | ".join(mit)
    assert "--gelaende-z" not in text, (
        "der Rat, den Geländestand zu setzen, darf nach dem Befolgen nicht stehen bleiben")
    assert "Bezugspunkt" not in text
    assert "Geländeangabe" in text, (
        "die gesetzte Angabe ist ungeprüft — das muss jemand lesen können, sonst sähe sie "
        "aus wie ein verlässlicher Bezug")


def test_die_gesetzte_angabe_wird_nicht_still_zum_verlaesslichen_bezug():
    """Weder «schiefgegangen» noch «verlässlich»: die dritte Antwort, mit eigenem Wortlaut."""
    gesetzt = komposition.kamerahoehe(1.70, bezugspunkt="gesetzt")
    terrain = komposition.kamerahoehe(1.70, bezugspunkt="terrain_an_kamera")

    assert gesetzt["verlaesslich"] is None
    assert any("NICHT GEPRÜFT" in w for w in gesetzt["warnungen"])
    assert not any("schiefgegangen" in w for w in gesetzt["warnungen"])
    assert gesetzt["warnungen"] != terrain["warnungen"], (
        "eine Angabe des Betreibers und ein Bezug am Gelände dürfen nicht gleich lauten")


# ======================================================================================
# (b) Der Rollwinkel — fehlend bleibt fehlend
# ======================================================================================

def test_ein_nicht_gemeldeter_rollwinkel_bleibt_auf_dem_produktweg_leer():
    urteil = _produktweg(_block())

    assert urteil["rollwinkel_grad"] is None, (
        "0° hiesse «Kamera nicht verkantet» — gemeldet hat das niemand")
    assert "NICHT GEMESSEN" in urteil["rollwinkel_vorbehalt"], (
        "ein None ohne benannten Grund wird geraten")


def test_ein_gemeldeter_rollwinkel_bleibt_eine_messung_und_eine_abweichung_wird_gemeldet():
    """Gegenprobe: Der Weg ist nicht verstopft — gemeldet wird gerechnet und gewarnt."""
    null = _produktweg(_block(rollwinkel_grad=0.0))
    schief = _produktweg(_block(rollwinkel_grad=3.0))

    assert null["rollwinkel_grad"] == 0.0
    assert null["rollwinkel_vorbehalt"] is None
    assert schief["rollwinkel_grad"] == 3.0
    assert any(w.startswith("Rollwinkel 3° statt 0°") for w in schief["warnungen"])


# ======================================================================================
# (c) Der Kamerasatz nennt, wer die Neigung nicht gemeldet hat
# ======================================================================================

def test_der_kamerasatz_nennt_die_kamera_ohne_neigungsangabe():
    satz = komposition.beurteile_kamerasatz(_satz(
        _block(neigung_grad=0.0, shift_mm=0.0), _block(kuerzel="nNW")))

    assert satz["alle_waagrecht"] is None
    assert satz["neigung_nicht_gemessen"] == ("nNW",)
    assert "nNW" in satz["alle_waagrecht_grund"]
    assert "sSE" not in satz["alle_waagrecht_grund"], "die gemessene Kamera ist nicht schuld"


def test_ein_gemessener_satz_nennt_niemanden_und_ein_leerer_sagt_warum():
    gemessen = komposition.beurteile_kamerasatz(_satz(_block(neigung_grad=0.0,
                                                             shift_mm=0.0)))
    leer = komposition.beurteile_kamerasatz(_satz())

    assert gemessen["alle_waagrecht"] is True
    assert gemessen["neigung_nicht_gemessen"] == ()
    assert gemessen["alle_waagrecht_grund"] == ""
    assert leer["alle_waagrecht"] is None
    assert leer["neigung_nicht_gemessen"] == ()
    assert leer["alle_waagrecht_grund"], "auch ohne Kamera braucht das None seinen Grund"


# ======================================================================================
# (d) Die Zusage über den Abholer — fehlend und gekippt bleiben zwei Zeilen
# ======================================================================================

def test_eine_ungemessene_und_eine_gekippte_kamera_ergeben_zwei_getrennte_zeilen():
    """Über den Produktweg: Urteile aus `_komposition_vor_dem_render`, Zeilen aus dem
    Kurzbefund. Verschmölzen die beiden, stünde «alle 2 Kameras: Neigung» da — und aus
    einer Nichtmessung würde eine Abweichung, die niemand festgestellt hat."""
    ungemessen = _produktweg(_block())
    gekippt = _produktweg(_block(kuerzel="nNW", neigung_grad=9.46, shift_mm=0.0))
    zeilen = _zeilen(("sSE", ungemessen), ("nNW", gekippt))

    nur_sse = [z for z in zeilen if "nur sSE" in z]
    nur_nnw = [z for z in zeilen if "nur nNW" in z]
    assert len(nur_sse) == 1 and len(nur_nnw) == 1, zeilen
    assert "Neigungsangabe" in nur_sse[0]
    assert "Neigung" in nur_nnw[0].split(": ", 1)[1].split(", ")
    assert "Neigungsangabe" not in nur_nnw[0]
    assert not any("alle 2 Kameras" in z and "Neigung" in z.split(": ", 1)[1].split(", ")
                   for z in zeilen)
