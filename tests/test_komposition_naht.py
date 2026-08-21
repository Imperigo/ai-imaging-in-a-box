"""Die Naht zwischen dem Regelwissen und den wirklichen Kameras.

**Der Anlass ist ein Befund über dieses Repo selbst.** `komposition.py` — 1400 Zeilen
gerechnetes fotografisches Fachwissen, mit Belegstufen, Quellenangaben und 117 eigenen
Tests — war bis zum 23.08.2026 von **nichts** aufgerufen ausser eben diesen Tests. Kein
Lauf hat je eine seiner Zahlen zu sehen bekommen.

Das ist die tote Kante dieses Projekts in ihrer bisher grössten Ausführung, und sie fällt
nicht auf: Ein ungenutztes Modul ist grün wie jedes andere, seine Testabdeckung sieht
vorbildlich aus, und die Suite meldet nichts. Ein Regelwerk, das nur seine eigenen Tests
beurteilt, beurteilt nichts.

Die Tests hier prüfen darum nicht das Regelwissen — das tut `test_komposition.py` —,
sondern **dass es ankommt**.
"""
import pytest

from aiimaging import kameras, komposition

BBOX = [[0.0, 0.0, 0.0], [40.0, 26.0, 15.0]]


# ======================================================================================
# Die Wahrheitstafel: das Urteil unterscheidet, was es unterscheiden soll
# ======================================================================================

def _arten(satz):
    """Die Warnungen nach ihrem ersten Wort — 'Neigung', 'Bezugspunkt', 'Abstand'."""
    beurteilt = komposition.beurteile_kamerasatz(satz)
    return sorted({w.split(": ", 1)[1].split(" ", 1)[0]
                   for w in beurteilt["warnungen"]})


def test_die_vier_faelle_ergeben_vier_verschiedene_urteile():
    """Vier Läufe, zwei Schalter, vier verschiedene Antworten.

    Wäre die Prüfung nur angeschlossen und nicht wirksam, sähen alle vier gleich aus.
    """
    def satz(modus, gelaende_z):
        return kameras.kamerasatz(BBOX, modus=modus, seitenverhaeltnis=1.0,
                                  gelaende_z=gelaende_z)

    assert _arten(satz(kameras.MODUS_GEKIPPT, None)) == ["Bezugspunkt", "Neigung"]
    assert _arten(satz(kameras.MODUS_GEKIPPT, 0.0)) == ["Neigung"]
    assert _arten(satz(kameras.MODUS_SHIFT, None)) == ["Bezugspunkt"]
    assert _arten(satz(kameras.MODUS_SHIFT, 0.0)) == [], (
        "waagrechte Kamera und erklärter Geländestand — hier ist nichts mehr zu melden"
    )


def test_alle_waagrecht_trennt_die_beiden_modi():
    """Die eine Zahl, auf die es normativ ankommt. Sie steht getrennt, weil sie in den
    vielen Warnungen sonst untergeht."""
    gekippt = komposition.beurteile_kamerasatz(kameras.kamerasatz(BBOX))
    geshiftet = komposition.beurteile_kamerasatz(
        kameras.kamerasatz(BBOX, modus=kameras.MODUS_SHIFT))
    assert gekippt["alle_waagrecht"] is False
    assert geshiftet["alle_waagrecht"] is True


def test_die_konvergenz_wird_beziffert_und_nicht_nur_behauptet():
    """Eine Warnung, die nur „nicht waagrecht" sagt, hilft niemandem beim Abwägen."""
    urteil = komposition.beurteile_kamerasatz(
        kameras.kamerasatz(BBOX, kuerzel=["sSE"], gelaende_z=0.0))["kameras"][0]
    assert 0.0 < urteil["konvergenz"] < 0.20
    assert "%" in " ".join(urteil["warnungen"])


def test_die_hoehe_ist_die_ueber_gelaende_und_nicht_die_der_huellbox():
    """Bei einem Untergeschoss sind das zwei verschiedene Zahlen — und die falsche
    ergäbe einen zu grossen Mindestabstand, also eine zu strenge Prüfung."""
    ohne_keller = komposition.beurteile_kamerasatz(
        kameras.kamerasatz(BBOX, kuerzel=["n"], gelaende_z=0.0))
    mit_keller = komposition.beurteile_kamerasatz(
        kameras.kamerasatz(BBOX, kuerzel=["n"], gelaende_z=3.0))
    assert ohne_keller["gebaeudehoehe_m"] == pytest.approx(15.0)
    assert mit_keller["gebaeudehoehe_m"] == pytest.approx(12.0)


def test_das_seitenverhaeltnis_der_kamera_schlaegt_die_vorgabe_des_regelwerks():
    """`SENSOR_HOEHE_HOCH_MM` ist die Hochlage. Für ein quadratisches Bild stehengelassen
    ergäbe sie einen zu grossen Bildwinkel und damit einen zu KLEINEN Mindestabstand —
    eine Prüfung, die zu milde urteilt, ist schlimmer als keine."""
    quadrat = komposition.beurteile_kamerasatz(
        kameras.kamerasatz(BBOX, kuerzel=["n"], seitenverhaeltnis=1.0,
                           gelaende_z=0.0))["kameras"][0]
    quer = komposition.beurteile_kamerasatz(
        kameras.kamerasatz(BBOX, kuerzel=["n"], seitenverhaeltnis=16 / 9,
                           gelaende_z=0.0))["kameras"][0]
    assert quer["mindestabstand"]["abstand_m"] > quadrat["mindestabstand"]["abstand_m"], (
        "das flachere Format sieht weniger Höhe und verlangt mehr Abstand"
    )


def test_der_shift_wird_wirklich_mitbeurteilt_und_nicht_nur_mitgereicht():
    """Sonst wäre die Beurteilung des Shift-Modus die Beurteilung einer anderen Kamera.

    Die Mutation ``shift_mm=... → shift_mm=0.0`` überlebte zuerst: Kein Test schaute auf
    eine Grösse, in die der Shift überhaupt eingeht. Er tut es an zwei Stellen —
    Mindestabstand und Bodenanteil —, und beide werden hier beziffert.

    Der Wert **ohne** Shift ist dabei der aussagekräftigere: Er ist exakt 0,5. Das ist
    keine Rundung, sondern die Aussage der Recherche (§4.4) — bei waagrechter Kamera ohne
    Shift liegt der Horizont **immer exakt in der Bildmitte**, unabhängig von Abstand,
    Brennweite und Format. Genau die Hälfte des Bildes ist Boden.
    """
    kamera = kameras.kamerasatz(BBOX, modus=kameras.MODUS_SHIFT, kuerzel=["sSE"],
                                gelaende_z=0.0, seitenverhaeltnis=1.0)["kameras"][0]
    assert kamera["shift_mm"] > 0.5, "ohne Shift prüft dieser Test nichts"

    def urteil(k):
        return komposition.beurteile_kamera(k, gebaeudehoehe_m=15.0, gelaende_z=0.0,
                                            bezugspunkt="terrain_an_kamera")

    mit = urteil(kamera)
    ohne = urteil(dict(kamera, shift_mm=0.0))

    assert ohne["bodenanteil"] == pytest.approx(0.5, abs=1e-9), (
        "waagrecht und ungeshiftet heisst: der Horizont sitzt in der Bildmitte"
    )
    assert mit["bodenanteil"] < ohne["bodenanteil"], (
        "nach oben geshiftet zeigt das Bild weniger Boden"
    )
    assert mit["mindestabstand"]["abstand_m"] < ohne["mindestabstand"]["abstand_m"], (
        "hier bindet das Dach — der Shift schafft oben Platz und erlaubt weniger Abstand"
    )


# ======================================================================================
# Der Produktivweg — der Kamerasatz wird in Blender gerechnet, beurteilt wird hier
# ======================================================================================

def _bericht(**kw):
    """Ein Kamerablock, wie ihn der Runner meldet."""
    kamera = kameras.kamerasatz(BBOX, kuerzel=["sSE"], gelaende_z=0.0,
                                **{k: v for k, v in kw.items()
                                   if k in ("modus", "seitenverhaeltnis")})["kameras"][0]
    block = {
        "weg": "abgeleitet", "kuerzel": kamera["kuerzel"],
        "auge": list(kamera["auge"]), "abstand_m": kamera["abstand_m"],
        "brennweite_mm": kamera["brennweite_mm"],
        "seitenverhaeltnis": kamera["seitenverhaeltnis"],
        "neigung_grad": kamera["neigung_grad"], "shift_mm": kamera["shift_mm"],
        "gelaende_z": 0.0, "gelaende_bezug": "terrain_an_kamera",
        "gebaeudehoehe_m": 15.0,
    }
    block.update({k: v for k, v in kw.items() if k not in ("modus", "seitenverhaeltnis")})
    return block


def test_ein_berichteter_kamerablock_wird_beurteilt():
    urteil = komposition.beurteile_bericht(_bericht())
    assert urteil["beurteilt"] is True
    assert urteil["kuerzel"] == "sSE"
    assert urteil["neigung_grad"] > 0.0


def test_der_shift_modus_kommt_auch_ueber_den_bericht_sauber_an():
    urteil = komposition.beurteile_bericht(_bericht(modus=kameras.MODUS_SHIFT))
    assert urteil["neigung_grad"] == 0.0
    assert urteil["warnungen"] == [], "waagrecht und erklärter Boden — nichts zu melden"


@pytest.mark.parametrize("fehlend", komposition.BERICHTSFELDER)
def test_ein_unvollstaendiger_bericht_wird_gemeldet_statt_geraten(fehlend):
    """Der Rückfallweg des Runners setzt die Kamera ohne Rechnung. Dann gibt es nichts
    zu beurteilen — und ein Ersatzwert sähe aus wie eine Prüfung und wäre keine."""
    urteil = komposition.beurteile_bericht(_bericht(**{fehlend: None}))
    assert urteil["beurteilt"] is False
    assert fehlend in urteil["grund"]


def test_kein_kamerablock_ist_auch_eine_antwort():
    for kaputt in (None, "nichts", 42, []):
        assert komposition.beurteile_bericht(kaputt)["beurteilt"] is False


# ======================================================================================
# Die Naht selbst — ein Test am Baustein ersetzt keinen Test an der Naht
# ======================================================================================

def test_der_abholer_haengt_die_beurteilung_an_jede_kamera(tmp_path, monkeypatch):
    """Der Weg eines echten Auftrags. Ohne diesen Test wäre die Verdrahtung genau die
    Fehlerart, gegen die dieses Modul überhaupt angeschlossen wurde."""
    from aiimaging import abholer

    bild = tmp_path / "bild.png"

    def multipass(glb, aus, **kw):
        from pathlib import Path
        tiefe = Path(aus) / "tiefe_norm.png"
        tiefe.write_bytes(b"\x89PNG\r\n\x1a\n")
        return {"depth_png": str(tiefe), "kamera": _bericht()}

    def rendere(auftrag, **kw):
        bild.write_bytes(b"\x89PNG\r\n\x1a\n")
        return {"status": "ok", "bild_png": str(bild), "hinweise": ()}

    verarbeite = abholer.verarbeiter(
        out_wurzel=tmp_path, nullprobe=False,
        _multipass=multipass, _rendere=rendere,
        _qa=lambda *a, **k: {"score": 0.9, "bestanden": True},
        _soll=lambda *a, **k: ([[0.0]], 1, 1))

    auftrag = {"modell": tmp_path / "m.glb", "job_id": "vis-1-aaaaaa",
               "verzeichnis": tmp_path,
               "szene": {"kameras": "auto", "aufloesung": 64, "hoehe": 64,
                         "samples": 1, "prompt": "a house"}}
    ergebnis = verarbeite(auftrag)

    assert ergebnis["kameras"], "ohne Kameras prüft dieser Test nichts"
    for kamera in ergebnis["kameras"]:
        assert kamera["komposition"]["beurteilt"] is True, (
            "die Kompositionsprüfung muss an jeder Kamera hängen — sonst ist sie wieder "
            "das, was sie ein halbes Jahr lang war: ungerufen"
        )
        assert kamera["komposition"]["konvergenz"] is not None
