"""Variantenreihen — und die Frage, ab wann ein Unterschied einer ist.

Der wichtigste Test dieser Datei ist nicht der, der eine Reihe baut, sondern
:func:`test_ein_unterschied_unter_dem_rauschboden_ist_kein_befund`. Er hält fest, wofür
das Modul überhaupt gebaut wurde.
"""
from __future__ import annotations

import pytest

from aiimaging import geometrie_qa, render, varianten


@pytest.fixture
def basis():
    return render.RenderAuftrag(depth_png="t.png", prompt="ein Haus", seed=100,
                                ausgabe_png="/aus/bild.png")


# ======================================================================================
# Der Grund für dieses Modul
# ======================================================================================

def test_ein_unterschied_unter_dem_rauschboden_ist_kein_befund():
    """Dieselbe Denkweise wie bei der Stil-Schwelle: erst den Boden messen, dann urteilen.

    Fünf Läufe mit **identischen Parametern** streuen um 0.019. Zwei Läufe, die sich um
    0.03 unterscheiden, unterscheiden sich damit **nicht** — wer hier einen Effekt
    behauptet, behauptet ihn über das Rauschen der Kette.
    """
    boden = varianten.rauschboden([0.61, 0.63, 0.60, 0.65, 0.62])
    assert boden["belastbar"]

    nah = varianten.ist_unterschied_belegt(0.61, 0.64, boden)
    assert nah["belegt"] is False
    assert "Zufall und kein Befund" in nah["begruendung"]

    weit = varianten.ist_unterschied_belegt(0.61, 0.85, boden)
    assert weit["belegt"] is True
    assert weit["grenze"] == pytest.approx(2.0 * boden["streuung"])


def test_die_schwelle_ist_dieselbe_wie_bei_der_stil_qa():
    """Zwei Begriffe von 'deutlich mehr als Zufall' in einem Projekt wären einer zu viel."""
    from aiimaging import stil_qa
    assert varianten.K_STREUUNGEN == stil_qa.K_STREUUNGEN == 2.0


# ======================================================================================
# Rauschboden
# ======================================================================================

def test_zu_wenige_laeufe_ergeben_keine_streuung_sondern_None():
    """Aus zwei Werten lässt sich eine Streuung ausrechnen, aber sie sagt nichts."""
    boden = varianten.rauschboden([0.6, 0.7])
    assert boden["streuung"] is None and boden["belastbar"] is False
    assert "sagt nichts" in boden["begruendung"]


def test_ungemessene_laeufe_zaehlen_mit_damit_niemand_sich_taeuscht():
    """Sonst läse jemand aus einer geschrumpften Reihe eine kleine Streuung."""
    boden = varianten.rauschboden([0.6, None, 0.62, None, 0.61])
    assert boden["n"] == 3 and boden["n_ungemessen"] == 2
    assert "2 Läufe ungemessen" in boden["begruendung"]


def test_eine_reihe_nur_aus_ungemessenen_ist_nicht_belastbar():
    boden = varianten.rauschboden([None, None, None, None])
    assert boden["belastbar"] is False and boden["n"] == 0


def test_eine_streuung_von_null_ist_belastbar_und_bedeutet_etwas():
    """Wenn fünf Seeds exakt dasselbe ergeben, ist jeder Unterschied ein Befund."""
    boden = varianten.rauschboden([0.5] * 5)
    assert boden["belastbar"] and boden["streuung"] == 0.0
    assert varianten.ist_unterschied_belegt(0.5, 0.5001, boden)["belegt"] is True


def test_ohne_belastbaren_boden_wird_nichts_belegt():
    boden = varianten.rauschboden([0.6, 0.9])
    urteil = varianten.ist_unterschied_belegt(0.6, 0.9, boden)
    assert urteil["belegt"] is False
    assert urteil["abstand"] == pytest.approx(0.3), "der Abstand wird trotzdem genannt"
    assert "keinen belastbaren Rauschboden" in urteil["begruendung"]


def test_ein_ungemessener_lauf_belegt_weder_unterschied_noch_gleichheit():
    boden = varianten.rauschboden([0.6, 0.61, 0.62, 0.6])
    urteil = varianten.ist_unterschied_belegt(0.6, None, boden)
    assert urteil["belegt"] is False
    assert "es folgt gar nichts" in urteil["begruendung"]


# ======================================================================================
# Saatreihe
# ======================================================================================

def test_die_saatreihe_zaehlt_den_seed_hoch(basis):
    reihe = varianten.saatreihe(basis, 4)
    assert [a.seed for a in reihe] == [100, 101, 102, 103]
    assert all(a.prompt == basis.prompt for a in reihe)
    assert all(a.controlnet_staerke == basis.controlnet_staerke for a in reihe)


def test_die_ausgabepfade_werden_nummeriert(basis):
    """Sonst überschriebe jede Variante die vorige, und am Ende läge ein Bild da, wo
    fünf erwartet werden."""
    reihe = varianten.saatreihe(basis, 3)
    assert [a.ausgabe_png for a in reihe] == [
        "/aus/bild_00.png", "/aus/bild_01.png", "/aus/bild_02.png"]
    assert len(set(a.ausgabe_png for a in reihe)) == 3


def test_ohne_ausgabepfad_bleibt_er_leer(basis):
    """Dann wählt der Renderer selbst — und er nimmt den Seed in den Namen."""
    ohne = render.RenderAuftrag(depth_png="t.png", prompt="x")
    assert all(a.ausgabe_png is None for a in varianten.saatreihe(ohne, 3))


def test_ein_pfad_ohne_endung_wird_trotzdem_nummeriert(basis):
    ohne = render.RenderAuftrag(depth_png="t.png", prompt="x", ausgabe_png="/aus/bild")
    assert varianten.saatreihe(ohne, 2)[1].ausgabe_png == "/aus/bild_01"


def test_ein_ueberlaufender_seed_wird_abgewiesen_statt_umgebrochen(basis):
    """Zwei Varianten mit demselben Seed wären dasselbe Bild unter zwei Namen."""
    hoch = render.RenderAuftrag(depth_png="t.png", prompt="x", seed=render.MAX_SEED - 1)
    varianten.saatreihe(hoch, 2)                      # geht gerade noch
    with pytest.raises(varianten.VariantenError, match="Umgebrochen wird NICHT"):
        varianten.saatreihe(hoch, 3)


@pytest.mark.parametrize("anzahl", [0, -1, 1.5, True])
def test_unbrauchbare_anzahl_wird_abgewiesen(basis, anzahl):
    with pytest.raises(varianten.VariantenError):
        varianten.saatreihe(basis, anzahl)


# ======================================================================================
# Kontrollierte Reihe — der feste Seed ist der ganze Punkt
# ======================================================================================

def test_die_kontrollierte_reihe_haelt_den_seed_fest(basis):
    reihe = varianten.kontrollierte_reihe(basis, "controlnet_staerke", [0.6, 0.8, 1.0])
    assert [a.controlnet_staerke for a in reihe] == [0.6, 0.8, 1.0]
    assert {a.seed for a in reihe} == {100}, "ein mitlaufender Seed macht die Reihe wertlos"


def test_der_seed_darf_nicht_gefahren_werden(basis):
    with pytest.raises(varianten.VariantenError, match="SAATREIHE"):
        varianten.kontrollierte_reihe(basis, "seed", [1, 2, 3])


def test_ein_feld_das_keine_groesse_ist_wird_abgewiesen(basis):
    """`ausgabe_png` ist ein Ablageort und keine Grösse, die man durchfährt."""
    with pytest.raises(varianten.VariantenError, match="keine Grösse"):
        varianten.kontrollierte_reihe(basis, "ausgabe_png", ["/a.png", "/b.png"])


def test_ein_unbekanntes_feld_nennt_die_fahrbaren(basis):
    with pytest.raises(varianten.VariantenError, match="controlnet_staerke"):
        varianten.kontrollierte_reihe(basis, "gibtsnicht", [1, 2])


def test_ein_einzelner_wert_ist_keine_reihe(basis):
    with pytest.raises(varianten.VariantenError, match="mindestens zwei Werte"):
        varianten.kontrollierte_reihe(basis, "denoise", [0.6])


def test_doppelte_werte_werden_abgewiesen(basis):
    """Bei festem Seed ergibt derselbe Wert zweimal dasselbe Bild — in der Auswertung
    sähe das wie eine Bestätigung aus."""
    with pytest.raises(varianten.VariantenError, match="Doppelte Werte"):
        varianten.kontrollierte_reihe(basis, "denoise", [0.6, 0.8, 0.6])


def test_auch_ein_prompt_laesst_sich_fahren(basis):
    reihe = varianten.kontrollierte_reihe(basis, "prompt", ["ein Haus", "ein Turm"])
    assert [a.prompt for a in reihe] == ["ein Haus", "ein Turm"]


# ======================================================================================
# Auswählen — und "keine besteht" ist eine Antwort
# ======================================================================================

def test_keine_variante_besteht_und_das_wird_gesagt():
    """Der geerbte Bewerter liefert immer eine beste, auch wenn alle unbrauchbar sind.

    Das ist die Sorte Antwort, die eine Frage beendet, ohne sie zu beantworten.
    """
    urteil = varianten.waehle([{"score": 0.2}, {"score": 0.4}, {"score": 0.31}],
                              schwelle=0.65)
    assert urteil["index"] == 1, "die beste wird trotzdem genannt"
    assert urteil["bestanden"] is False
    assert urteil["n_bestanden"] == 0
    assert "KEINE Variante besteht" in urteil["begruendung"]
    assert "beste von schlechten" in urteil["begruendung"]


def test_die_schwelle_kommt_von_aussen_und_nicht_aus_der_charge():
    """Der eigentliche Unterschied zum Geerbten: Zwei Chargen bleiben vergleichbar.

    Dieselben Werte, einmal gegen die echte Schwelle und einmal gegen eine mildere — das
    Urteil ändert sich, die Zahlen nicht. Beim min-max-Bewerter wäre die beste Variante
    beide Male 100.
    """
    werte = [{"score": 0.60}, {"score": 0.70}]
    streng = varianten.waehle(werte, schwelle=geometrie_qa.SCHWELLE_GEOMETRIE)
    mild = varianten.waehle(werte, schwelle=0.5)
    assert streng["beste"]["score"] == mild["beste"]["score"] == 0.70
    assert streng["n_bestanden"] == 1 and mild["n_bestanden"] == 2


def test_eine_einzelne_variante_bekommt_ihren_echten_wert():
    """Der geerbte Bewerter gibt bei einer einzelnen Variante pauschal 50 — unabhängig
    vom Bild."""
    assert varianten.waehle([{"score": 0.9}], schwelle=0.65)["bestanden"] is True
    assert varianten.waehle([{"score": 0.1}], schwelle=0.65)["bestanden"] is False


def test_ungemessene_varianten_werden_uebersprungen_und_gezaehlt():
    urteil = varianten.waehle([{"score": None}, {"score": 0.8}, {"score": None}],
                              schwelle=0.65)
    assert urteil["index"] == 1 and urteil["n_ungemessen"] == 2
    assert "2 ungemessen" in urteil["begruendung"]


def test_nur_ungemessene_heisst_ungeprueft_und_nicht_durchgefallen():
    urteil = varianten.waehle([{"score": None}, {"score": None}], schwelle=0.65)
    assert urteil["beste"] is None and urteil["bestanden"] is False
    assert "UNGEPRÜFT und nicht durchgefallen" in urteil["begruendung"]


def test_eine_leere_liste_ist_kein_absturz():
    assert varianten.waehle([], schwelle=0.65)["begruendung"] == "Keine Variante vorgelegt."


def test_das_beiwerk_der_besten_bleibt_erhalten():
    """Wer die beste Variante hat, will auch wissen, welcher Seed sie war."""
    urteil = varianten.waehle(
        [{"score": 0.3, "seed": 7}, {"score": 0.9, "seed": 8}], schwelle=0.65)
    assert urteil["beste"]["seed"] == 8


# ======================================================================================
# Der ganze Weg, an einer Attrappe
# ======================================================================================

def test_saatreihe_rauschboden_und_urteil_zusammen(basis):
    """Erst den Boden messen, dann die kontrollierte Reihe beurteilen — in dieser
    Reihenfolge, sonst bedeutet die zweite nichts."""
    scores = {100: 0.61, 101: 0.63, 102: 0.60, 103: 0.65, 104: 0.62}

    boden = varianten.rauschboden(
        [scores[a.seed] for a in varianten.saatreihe(basis, 5)])
    assert boden["belastbar"] and boden["streuung"] < 0.02

    # Kontrollierte Reihe: die Treue-Stärke wirkt, der Seed steht fest.
    reihe = varianten.kontrollierte_reihe(basis, "controlnet_staerke", [0.4, 0.8])
    assert {a.seed for a in reihe} == {100}
    gemessen = [{"score": 0.45, "staerke": 0.4}, {"score": 0.82, "staerke": 0.8}]

    urteil = varianten.ist_unterschied_belegt(
        gemessen[0]["score"], gemessen[1]["score"], boden)
    assert urteil["belegt"] is True

    wahl = varianten.waehle(gemessen, schwelle=geometrie_qa.SCHWELLE_GEOMETRIE)
    assert wahl["beste"]["staerke"] == 0.8 and wahl["bestanden"] is True
