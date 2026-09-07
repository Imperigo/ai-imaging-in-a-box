"""Die Innenkamera rechnet eine Brennweite — und bis heute kam sie nicht an.

Anlass, und er ist gemessen
---------------------------
``raumkamera`` rechnet für jeden Innenstandpunkt ein Sichtfeld: 24 mm
(:data:`raumkamera.BRENNWEITE_INNEN_MM`), die sichtbare Breite an der Zielwand, und die
**nötige** Brennweite, wenn die Wand nicht ins Bild passt — gegen die belegte Grenze von
16 mm (*Airbnb: „never capture wider than 16mm"*). Über die Prozessgrenze ging davon
nichts: ``kette._fuehre_multipass`` reichte Auge und Blickziel hinüber und liess die
Brennweite fallen. Der Runner stellt dann seinen Rückfall — **50 mm**.

Gemessen am 09.09.2026 an der echten Kette (``docs/INNENANSICHT_2026-09-09.md``),
Raum-Nord frontal, 800 × 496, Blender 4.2:

===============  ==========  ============  ==============================
Brennweite       Spanne      Tiefenstufen  grösste Ebene, Anteil am Bild
===============  ==========  ============  ==============================
24 mm            1,191 m     73            78,8 %
**50 mm**        **0,000 m** **1**         **100,0 %**
===============  ==========  ============  ==============================

Bei 50 mm trägt die ganze Tiefenkarte **einen einzigen Wert**. Das ist nicht „etwas
ungenauer": Eine Rangkorrelation über eine Karte ohne jede Ordnung misst nichts, und die
Geometrie-QA hängt an Tiefenrängen. Der Rückfall macht die Aufnahme also nicht schlechter,
sondern **unmessbar** — und nichts daran sieht nach einem Fehler aus.

Warum das hier steht und nicht nur im Docstring
-----------------------------------------------
Es ist zum vierten Mal dieselbe Sache: Brennweite und Geländestand am 23.08.,
``gelaende_erwartet`` am 24.08., die drei Kameraparameter am 26.08. — im Modul längst
gerechnet, auf dem Weg nicht durchgereicht. *«Einstellbar» ist eine Zusage, die man an
der Naht prüfen muss und nicht am Modul.*

Und die Probe treibt darum den **Aufrufer**, nicht die Rechnung: Ein Wächter, der den
Aufruf selbst nachbaut, bewacht seine eigene Nachbildung — die Regel steht seit dem
01.09. im Projekt und ist am 09.09. schon einmal verletzt worden.
"""
from __future__ import annotations

import pytest

from aiimaging import raumkamera
from aiimaging.graph import Knoten

#: Der Raum aus ``tools/make_test_ifc.py --raeume``, wie ihn der Raumleser liefert.
#: Abgeschrieben wäre hier falsch — es sind die Zahlen, die ``seams.ifc_raeume`` an der
#: erzeugten Datei misst (26,62 m² und 5,94 m², Sitzung 11).
RAUM_SUED = {"name": "Raum-Sued", "z_unten_m": 0.1, "hoehe_m": 2.4,
             "grundriss_m": [[7.7, 0.3], [7.7, 2.5], [5.0, 2.5], [5.0, 0.3]]}


def _raeume_ausgabe(raum: dict) -> dict:
    return {"status": "ok",
            "raeume": [{"raum": raum, "kamera": raumkamera.standpunkte(raum)}]}


def _spion(monkeypatch, tmp_path):
    """Fängt den echten Aufruf von ``seams.glb_zu_multipass`` ab und merkt sich alles."""
    import aiimaging.kette as kette_modul

    gesehen: dict = {}

    def multipass(glb, out, **kw):
        gesehen.update(kw)
        return {"status": "ok", "depth_exr": str(tmp_path / "t.exr"),
                "depth_png": str(tmp_path / "t.png")}

    monkeypatch.setattr(kette_modul.seams, "glb_zu_multipass", multipass)
    return kette_modul, gesehen


def test_die_brennweite_der_innenkamera_erreicht_den_runner(monkeypatch, tmp_path):
    """24 mm werden gerechnet — und müssen ankommen, sonst stellt der Runner 50 mm."""
    kette_modul, gesehen = _spion(monkeypatch, tmp_path)

    knoten = Knoten(id="mp", art=kette_modul.ART_MULTIPASS,
                    params={"aufloesung": 512, "samples": 8, "beauty": True,
                            "material_id": True,
                            "innenraum": {"raum": "Raum-Sued", "art": "frontal"}})
    kette_modul._fuehre_multipass(
        knoten=knoten,
        eingaben=[{"glb_path": "m.glb", "up_axis": "Y",
                   "raeume": _raeume_ausgabe(RAUM_SUED)}],
        out_dir=tmp_path)

    assert gesehen.get("brennweite") == pytest.approx(raumkamera.BRENNWEITE_INNEN_MM), (
        "Die Innenkamera rechnet 24 mm, angekommen ist "
        f"{gesehen.get('brennweite')!r}. Ohne sie stellt der Runner 50 mm — und bei "
        "50 mm trug die Tiefenkarte des Raum-Nord gemessen EINEN EINZIGEN WERT.")


def test_die_brennweite_stammt_aus_dem_standpunkt_und_nicht_aus_einer_konstanten(
        monkeypatch, tmp_path):
    """Die Zahl wird **gelesen**, nicht nachgeschlagen — sonst veraltet sie an zwei Orten.

    ``raumkamera`` kann je Standpunkt eine andere Brennweite nennen: ``noetige_brennweite``
    steht bereit, wenn die Zielwand bei 24 mm nicht ins Bild passt. Eine hier
    abgeschriebene 24 wäre genau die Sorte Zahl, an der dieses Projekt schon dreimal
    hängengeblieben ist (0,2269, die 9,46°, die beiden 28er).
    """
    kette_modul, gesehen = _spion(monkeypatch, tmp_path)

    raeume = _raeume_ausgabe(RAUM_SUED)
    frontal = [s for s in raeume["raeume"][0]["kamera"]["standpunkte"]
               if s["art"] == raumkamera.ART_FRONTAL][0]
    frontal["sichtfeld"]["brennweite_mm"] = 19.5      # eine andere als die Konstante

    knoten = Knoten(id="mp", art=kette_modul.ART_MULTIPASS,
                    params={"aufloesung": 512, "samples": 8, "beauty": True,
                            "material_id": True,
                            "innenraum": {"raum": "Raum-Sued", "art": "frontal"}})
    kette_modul._fuehre_multipass(
        knoten=knoten,
        eingaben=[{"glb_path": "m.glb", "up_axis": "Y", "raeume": raeume}],
        out_dir=tmp_path)

    assert gesehen.get("brennweite") == pytest.approx(19.5), (
        "Die Brennweite wurde nicht aus dem Standpunkt gelesen, sondern aus einer "
        "Konstanten geholt. Dann kann `noetige_brennweite` nie ankommen.")


def test_der_aussenweg_bekommt_keine_brennweite_untergeschoben(monkeypatch, tmp_path):
    """``None`` heisst «nicht angefasst» und nicht «null» — und der Runner hat eine Vorgabe.

    Der Aussenweg holt seine Brennweite aus ``kameras.BRENNWEITE_MM`` (35 mm,
    Owner-Setzung 23.08.). Ihm hier eine Innenbrennweite mitzugeben, änderte **jede**
    Aussenaufnahme — und zwar still.
    """
    kette_modul, gesehen = _spion(monkeypatch, tmp_path)

    knoten = Knoten(id="mp", art=kette_modul.ART_MULTIPASS,
                    params={"aufloesung": 512, "samples": 8, "beauty": True,
                            "material_id": True})
    kette_modul._fuehre_multipass(
        knoten=knoten,
        eingaben=[{"glb_path": "m.glb", "up_axis": "Y", "raeume": None}],
        out_dir=tmp_path)

    assert gesehen.get("brennweite") is None, (
        f"Der Aussenweg bekam brennweite={gesehen.get('brennweite')!r}. Damit änderte "
        f"sich jede Aussenaufnahme, ohne dass es jemand bestellt hätte.")


def test_ein_standpunkt_ohne_sichtfeld_bricht_nicht_ab(monkeypatch, tmp_path):
    """Fehlt das Sichtfeld, gilt wieder die Vorgabe des Runners — nicht ein Absturz.

    Der Fall ist heute nicht erreichbar, weil ``standpunkte`` das Sichtfeld immer setzt.
    Er steht hier, weil die Alternative ein ``KeyError`` mitten im Multipass wäre — und
    ein Absturz wegen einer **fehlenden Zusatzangabe** ist teurer als eine Aufnahme mit
    der Vorgabe.
    """
    kette_modul, gesehen = _spion(monkeypatch, tmp_path)

    raeume = _raeume_ausgabe(RAUM_SUED)
    for s in raeume["raeume"][0]["kamera"]["standpunkte"]:
        s.pop("sichtfeld", None)

    knoten = Knoten(id="mp", art=kette_modul.ART_MULTIPASS,
                    params={"aufloesung": 512, "samples": 8, "beauty": True,
                            "material_id": True,
                            "innenraum": {"raum": "Raum-Sued", "art": "frontal"}})
    ergebnis = kette_modul._fuehre_multipass(
        knoten=knoten,
        eingaben=[{"glb_path": "m.glb", "up_axis": "Y", "raeume": raeume}],
        out_dir=tmp_path)

    assert ergebnis.get("status") != kette_modul.STATUS_FEHLER
    assert gesehen.get("brennweite") is None
    assert gesehen.get("auge") is not None, "der Standpunkt selbst muss weiterhin ankommen"
