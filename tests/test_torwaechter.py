"""Die zwei Fehlerklassen, die den Vorläufer trafen — als Tests festgehalten.

``torwaechter.py`` steht vor der GPU. Er prüft sechs Zahlen, um eine Renderstunde nicht
an Geometrie zu verlieren, die schon vor dem ersten Sample falsch war:

* **Massstab** (Millimeter als Meter und umgekehrt) ist ein Quell-Datenfehler → Ablehnung.
* **Georeferenz** (LV95 bei ~2.6e6 m, float32-Quantisierung ~0.31 m) ist heilbar →
  Empfehlung zur XY-Neuzentrierung, **keine** Ablehnung, und Z bleibt unberührt.

Der wichtigste Test dieser Datei ist ``test_ok_report_mit_faktor_1000_wird_trotzdem_abgelehnt``:
Genau diese Kombination — Konversion meldet ``ok``, Geometrie liegt um Faktor 1000
daneben — ist im Vorläufer aufgetreten. Wäre der Massstabstest an ``status != "ok"``
gekoppelt, wäre er vakuös und hätte diesen Fall nie gesehen. ``test_..._ist_nicht_vakuos``
daneben belegt, dass derselbe Report ohne den Skalierungsfehler angenommen wird.

Alle Testdaten sind synthetisch (Regel 3). Kein Blender, keine GPU, kein Netz, kein IFC.
"""
from __future__ import annotations

import copy

import pytest

from aiimaging.torwaechter import (
    ENTSCHEIDUNG_ABLEHNEN_KONVERSION,
    ENTSCHEIDUNG_ABLEHNEN_MASSSTAB,
    ENTSCHEIDUNG_ANNEHMEN,
    GEOREF_SCHWELLE_M,
    MAX_GEBAEUDE_M,
    MIN_GEBAEUDE_M,
    masse_aus_bbox,
    pruefe_georeferenz,
    pruefe_massstab,
    torwaechter,
)

#: Ein plausibles kleines Gebäude, 8 × 5 × 3 m, am Ursprung. Der gesunde Fall.
BBOX_GESUND = [[0.0, 0.0, 0.0], [8.0, 5.0, 3.0]]

#: Dasselbe Gebäude, millimeter-als-meter gelesen: 8000 × 5000 × 3000 m = 8 km Kante.
BBOX_MM_ALS_M = [[0.0, 0.0, 0.0], [8000.0, 5000.0, 3000.0]]

#: Dasselbe Gebäude, meter-als-millimeter gelesen: 8 × 5 × 3 mm, ein Streichholzkopf.
BBOX_M_ALS_MM = [[0.0, 0.0, 0.0], [0.008, 0.005, 0.003]]

#: Ein 30 × 20 × 12 m Bau, verortet in LV95 (Ostwert ~2.6e6 m, Nordwert ~1.2e6 m,
#: Höhe 500 m ü. M.). Masse plausibel, Koordinaten weit vom Ursprung.
BBOX_LV95 = [[2600000.0, 1200000.0, 500.0], [2600030.0, 1200020.0, 512.0]]


def report(bbox, status="ok", **rest) -> dict:
    """Minimaler ``ifc_to_glb``-Report, wie ihn der Runner liefert — synthetisch."""
    grund = {
        "status": status,
        "glb_path": "build/synthetisch.glb",
        "up_axis": "Y",
        "bbox": bbox,
        "n_elements": 12,
        "n_triangles": 480,
        "error": None,
    }
    grund.update(rest)
    return grund


# --------------------------------------------------------------------------------------
# masse_aus_bbox
# --------------------------------------------------------------------------------------

def test_kantenlaengen_aus_bbox():
    assert masse_aus_bbox(BBOX_GESUND) == (8.0, 5.0, 3.0)


def test_verschobene_bbox_hat_dieselben_masse():
    """Die Ausdehnung hängt nicht von der Lage ab — sonst wäre LV95 schon deshalb falsch."""
    assert masse_aus_bbox([[100.0, -50.0, 20.0], [108.0, -45.0, 23.0]]) == (8.0, 5.0, 3.0)


def test_vertauschte_ecken_sind_kein_fehler():
    """Obere Ecke zuerst geschrieben: dieselbe Box, nur andere Reihenfolge."""
    assert masse_aus_bbox([[8.0, 5.0, 3.0], [0.0, 0.0, 0.0]]) == (8.0, 5.0, 3.0)


def test_ganzzahlige_koordinaten_sind_zulaessig():
    """JSON-Reports schreiben ``0`` statt ``0.0``; das ist keine Formverletzung."""
    assert masse_aus_bbox([[0, 0, 0], [8, 5, 3]]) == (8.0, 5.0, 3.0)


@pytest.mark.parametrize("kaputt", [
    None,
    [],
    [[0.0, 0.0, 0.0]],                                  # nur eine Ecke
    [[0.0, 0.0], [8.0, 5.0]],                           # zu wenige Werte je Ecke
    [0.0, 0.0, 0.0, 8.0, 5.0, 3.0],                     # flach statt geschachtelt
    [[0.0, 0.0, 0.0], [8.0, 5.0, float("nan")]],
    [[0.0, 0.0, 0.0], [8.0, 5.0, float("inf")]],
    [[0.0, 0.0, 0.0], [8.0, 5.0, "3.0"]],               # Zahl in Textform
    [[0.0, 0.0, 0.0], [8.0, 5.0, None]],
    "8x5x3",
])
def test_unbrauchbare_bbox_wirft_valueerror(kaputt):
    """Der einzige Ort im Modul, der wirft — und zwar mit einer lesbaren Erklärung."""
    with pytest.raises(ValueError):
        masse_aus_bbox(kaputt)


# --------------------------------------------------------------------------------------
# pruefe_massstab
# --------------------------------------------------------------------------------------

def test_gesundes_gebaeude_ist_plausibel_und_warnungsfrei():
    ergebnis = pruefe_massstab(BBOX_GESUND)
    assert ergebnis["plausibel"] is True
    assert ergebnis["groesste_kante_m"] == 8.0
    assert ergebnis["verdacht_faktor"] is None
    assert ergebnis["warnungen"] == []


def test_millimeter_als_meter_ergibt_faktor_1000():
    ergebnis = pruefe_massstab(BBOX_MM_ALS_M)
    assert ergebnis["plausibel"] is False
    assert ergebnis["groesste_kante_m"] == 8000.0
    assert ergebnis["verdacht_faktor"] == 1000
    assert ergebnis["warnungen"]


def test_meter_als_millimeter_ergibt_faktor_ein_tausendstel():
    ergebnis = pruefe_massstab(BBOX_M_ALS_MM)
    assert ergebnis["plausibel"] is False
    assert ergebnis["groesste_kante_m"] == pytest.approx(0.008)
    assert ergebnis["verdacht_faktor"] == 0.001
    assert ergebnis["warnungen"]


def test_verdachtsfaktor_ist_immer_ein_teiler():
    """Beide Richtungen tragen dieselbe Lesart: gemessen / faktor = wahre Masse."""
    for bbox in (BBOX_MM_ALS_M, BBOX_M_ALS_MM):
        ergebnis = pruefe_massstab(bbox)
        wahr = ergebnis["groesste_kante_m"] / ergebnis["verdacht_faktor"]
        assert MIN_GEBAEUDE_M <= wahr <= MAX_GEBAEUDE_M
        assert wahr == pytest.approx(8.0)


def test_absurde_groesse_ohne_einheitenverdacht():
    """1e9 m ist auch durch 1000 geteilt kein Gebäude — Faktor bleibt offen."""
    ergebnis = pruefe_massstab([[0.0, 0.0, 0.0], [1.0e9, 1.0, 1.0]])
    assert ergebnis["plausibel"] is False
    assert ergebnis["verdacht_faktor"] is None
    assert ergebnis["warnungen"]


def test_nullausdehnung_ist_unplausibel():
    """Beide Ecken fallen zusammen: leere Szene, nichts zu rendern."""
    ergebnis = pruefe_massstab([[4.0, 4.0, 4.0], [4.0, 4.0, 4.0]])
    assert ergebnis["plausibel"] is False
    assert ergebnis["groesste_kante_m"] == 0.0
    assert ergebnis["verdacht_faktor"] is None
    assert any("Ausdehnung" in w for w in ergebnis["warnungen"])


def test_flache_geometrie_wird_gewarnt_aber_nicht_abgelehnt():
    """Eine Geländeplatte hat kein Z — gültige Geometrie, aber erwähnenswert."""
    ergebnis = pruefe_massstab([[0.0, 0.0, 0.0], [40.0, 30.0, 0.0]])
    assert ergebnis["plausibel"] is True
    assert any("Ausdehnung 0 in Z" in w for w in ergebnis["warnungen"])


@pytest.mark.parametrize("kante,erwartet", [
    (MIN_GEBAEUDE_M, True),          # genau auf der Untergrenze: noch drin
    (MIN_GEBAEUDE_M * 0.99, False),
    (MAX_GEBAEUDE_M, True),          # genau auf der Obergrenze: noch drin
    (MAX_GEBAEUDE_M * 1.01, False),
])
def test_grenzen_sind_einschliessend(kante, erwartet):
    assert pruefe_massstab([[0.0, 0.0, 0.0], [kante, 0.5, 0.5]])["plausibel"] is erwartet


def test_massstab_bei_unbrauchbarer_bbox_lehnt_sauber_ab():
    """Kein TypeError, sondern eine Antwort mit allen Feldern und einer Warnung."""
    ergebnis = pruefe_massstab(None)
    assert ergebnis["plausibel"] is False
    assert ergebnis["groesste_kante_m"] is None
    assert ergebnis["verdacht_faktor"] is None
    assert ergebnis["warnungen"]


# --------------------------------------------------------------------------------------
# pruefe_georeferenz
# --------------------------------------------------------------------------------------

def test_ursprungsnahe_geometrie_braucht_keine_neuzentrierung():
    ergebnis = pruefe_georeferenz(BBOX_GESUND)
    assert ergebnis["georeferenziert"] is False
    assert ergebnis["empfiehlt_neuzentrierung"] is False
    assert ergebnis["quantisierung_m"] < 1.0e-5      # unter einem Hundertstel Millimeter
    assert ergebnis["warnungen"] == []


def test_lv95_wird_erkannt_und_quantisierung_berechnet():
    """LV95-Ostwert ~2.6e6 m → float32-Auflösung rund 0.31 m: sichtbares Zittern."""
    ergebnis = pruefe_georeferenz(BBOX_LV95)
    assert ergebnis["georeferenziert"] is True
    assert ergebnis["empfiehlt_neuzentrierung"] is True
    assert ergebnis["groesster_betrag_m"] == 2600030.0
    assert ergebnis["quantisierung_m"] == pytest.approx(0.31, abs=0.02)
    assert ergebnis["warnungen"]


def test_quantisierung_folgt_der_float32_mantisse():
    """Die Formel ist keine Schätzung: Betrag · 2^-23."""
    ergebnis = pruefe_georeferenz([[1.0e6, 0.0, 0.0], [1.0e6 + 10.0, 10.0, 10.0]])
    assert ergebnis["quantisierung_m"] == pytest.approx((1.0e6 + 10.0) * 2.0 ** -23)


def test_negative_koordinaten_zaehlen_mit_ihrem_betrag():
    """Ein Ostwert von -2.6e6 m ist genauso grob wie +2.6e6 m."""
    ergebnis = pruefe_georeferenz([[-2600030.0, -1200020.0, 0.0], [-2600000.0, -1200000.0, 12.0]])
    assert ergebnis["georeferenziert"] is True
    assert ergebnis["empfiehlt_neuzentrierung"] is True
    assert ergebnis["groesster_betrag_m"] == 2600030.0


@pytest.mark.parametrize("betrag,erwartet", [
    (GEOREF_SCHWELLE_M, True),           # genau auf der Schwelle: gilt als georeferenziert
    (GEOREF_SCHWELLE_M * 0.99, False),
])
def test_georeferenz_schwelle_ist_einschliessend(betrag, erwartet):
    # Die obere Ecke trägt den grössten Betrag; sie wird exakt auf den Prüfwert gelegt,
    # damit der Test wirklich die Schwelle prüft und nicht eine Zugabe von 10 m.
    ergebnis = pruefe_georeferenz([[betrag - 10.0, 0.0, 0.0], [betrag, 10.0, 10.0]])
    assert ergebnis["groesster_betrag_m"] == betrag
    assert ergebnis["georeferenziert"] is erwartet
    assert ergebnis["empfiehlt_neuzentrierung"] is erwartet


def test_grosser_z_wert_allein_empfiehlt_keine_xy_verschiebung():
    """XY-Neuzentrierung hülfe nicht, wenn die Grobheit allein in Z sitzt — dann lieber
    warnen als eine wirkungslose Empfehlung aussprechen."""
    ergebnis = pruefe_georeferenz([[0.0, 0.0, 5.0e6], [10.0, 10.0, 5.000012e6]])
    assert ergebnis["georeferenziert"] is True
    assert ergebnis["empfiehlt_neuzentrierung"] is False
    assert ergebnis["warnungen"]


def test_georeferenz_bei_unbrauchbarer_bbox_lehnt_sauber_ab():
    ergebnis = pruefe_georeferenz([[0.0, 0.0, 0.0], [8.0, 5.0, float("nan")]])
    assert ergebnis["georeferenziert"] is False
    assert ergebnis["groesster_betrag_m"] is None
    assert ergebnis["quantisierung_m"] is None
    assert ergebnis["empfiehlt_neuzentrierung"] is False
    assert ergebnis["warnungen"]


# --------------------------------------------------------------------------------------
# torwaechter — Gesamturteil
# --------------------------------------------------------------------------------------

def test_gesunder_report_wird_angenommen():
    urteil = torwaechter(report(BBOX_GESUND))
    assert urteil["entscheidung"] == ENTSCHEIDUNG_ANNEHMEN
    assert urteil["empfiehlt_neuzentrierung"] is False
    assert urteil["massstab"]["warnungen"] == []
    assert urteil["georeferenz"]["warnungen"] == []
    assert urteil["begruendung"]


def test_ok_report_mit_faktor_1000_wird_trotzdem_abgelehnt():
    """DER Fall aus dem Vorläufer: Die Konversion war zufrieden, das Modell 8 km gross.

    Der Massstabstest hängt bewusst nicht an ``status`` — sonst hätte er genau diesen
    Fehler nie gesehen.
    """
    urteil = torwaechter(report(BBOX_MM_ALS_M, status="ok"))
    assert urteil["entscheidung"] == ENTSCHEIDUNG_ABLEHNEN_MASSSTAB
    assert urteil["massstab"]["verdacht_faktor"] == 1000
    assert "1000" in urteil["begruendung"]


def test_ok_report_mit_faktor_1000_test_ist_nicht_vakuos():
    """Gegenprobe: derselbe Report, nur richtig skaliert, wird angenommen.

    Ohne diese Zeile könnte die Ablehnung oben auch von einem ganz anderen Feld des
    Reports stammen — der Test wäre wahr, aber ohne Aussage.
    """
    fehlskaliert = report(BBOX_MM_ALS_M, status="ok")
    gesund = dict(fehlskaliert, bbox=BBOX_GESUND)
    assert torwaechter(fehlskaliert)["entscheidung"] == ENTSCHEIDUNG_ABLEHNEN_MASSSTAB
    assert torwaechter(gesund)["entscheidung"] == ENTSCHEIDUNG_ANNEHMEN


def test_ok_report_mit_faktor_ein_tausendstel_wird_abgelehnt():
    urteil = torwaechter(report(BBOX_M_ALS_MM, status="ok"))
    assert urteil["entscheidung"] == ENTSCHEIDUNG_ABLEHNEN_MASSSTAB
    assert urteil["massstab"]["verdacht_faktor"] == 0.001


def test_lv95_wird_angenommen_mit_empfehlung():
    """Georeferenz ist heilbar — sie darf den Lauf nicht kosten."""
    urteil = torwaechter(report(BBOX_LV95))
    assert urteil["entscheidung"] == ENTSCHEIDUNG_ANNEHMEN
    assert urteil["empfiehlt_neuzentrierung"] is True
    assert urteil["georeferenz"]["quantisierung_m"] == pytest.approx(0.31, abs=0.02)
    assert urteil["massstab"]["plausibel"] is True


def test_empfehlung_nennt_xy_und_schont_z():
    """Z mitzuverschieben machte die Geschosshöhen falsch — das muss dastehen."""
    urteil = torwaechter(report(BBOX_LV95))
    text = urteil["begruendung"] + " ".join(urteil["georeferenz"]["warnungen"])
    assert "XY" in text
    assert "Z" in text


def test_georeferenziert_und_fehlskaliert_wird_wegen_massstab_abgelehnt():
    """Beides zugleich: Der Quellfehler entscheidet, die Empfehlung wird trotzdem
    mitgeliefert — sonst käme sie erst nach der zweiten Runde ans Licht."""
    bbox = [[2600000.0, 1200000.0, 0.0], [2630000.0, 1220000.0, 12000.0]]
    urteil = torwaechter(report(bbox))
    assert urteil["entscheidung"] == ENTSCHEIDUNG_ABLEHNEN_MASSSTAB
    assert urteil["empfiehlt_neuzentrierung"] is True


@pytest.mark.parametrize("status", ["error", "failed", None, "OK", ""])
def test_status_ungleich_ok_wird_als_konversionsfehler_abgelehnt(status):
    urteil = torwaechter(report(BBOX_GESUND, status=status))
    assert urteil["entscheidung"] == ENTSCHEIDUNG_ABLEHNEN_KONVERSION


def test_konversionsfehler_traegt_die_fehlermeldung_weiter():
    urteil = torwaechter(report(None, status="error", error="keine Geometrie im IFC"))
    assert urteil["entscheidung"] == ENTSCHEIDUNG_ABLEHNEN_KONVERSION
    assert "keine Geometrie im IFC" in urteil["begruendung"]


def test_report_ohne_status_wird_abgelehnt():
    """Ein Report ohne ``status`` ist kein Erfolg mit fehlendem Feld."""
    assert torwaechter({"bbox": BBOX_GESUND})["entscheidung"] == ENTSCHEIDUNG_ABLEHNEN_KONVERSION


@pytest.mark.parametrize("kaputt", [
    {},
    {"status": "ok"},                                                # bbox fehlt ganz
    {"status": "ok", "bbox": None},
    {"status": "ok", "bbox": []},
    {"status": "ok", "bbox": [[0.0, 0.0], [8.0, 5.0]]},              # zu wenige Werte
    {"status": "ok", "bbox": [[0.0, 0.0, 0.0]]},                     # nur eine Ecke
    {"status": "ok", "bbox": [0.0, 0.0, 0.0, 8.0, 5.0, 3.0]},        # flach
    {"status": "ok", "bbox": [[0.0, 0.0, 0.0], [8.0, 5.0, float("nan")]]},
    {"status": "ok", "bbox": [[0.0, 0.0, 0.0], [8.0, 5.0, float("inf")]]},
    {"status": "ok", "bbox": [[0.0, 0.0, 0.0], [8.0, 5.0, "3.0"]]},
    {"status": "ok", "bbox": "8x5x3"},
])
def test_kaputte_bbox_wird_als_konversionsfehler_abgelehnt(kaputt):
    """Ein Report, der Erfolg meldet und keine brauchbare bbox trägt, ist ein Defekt des
    Reports — kein Massstabsfehler der Quelle. Und er darf nie einen TypeError geben."""
    urteil = torwaechter(kaputt)
    assert urteil["entscheidung"] == ENTSCHEIDUNG_ABLEHNEN_KONVERSION
    assert urteil["massstab"]["warnungen"]


def test_nullausdehnung_wird_als_massstabsfehler_abgelehnt():
    """Die bbox ist lesbar, aber ein Punkt — das ist eine Aussage über die Geometrie."""
    urteil = torwaechter(report([[4.0, 4.0, 4.0], [4.0, 4.0, 4.0]]))
    assert urteil["entscheidung"] == ENTSCHEIDUNG_ABLEHNEN_MASSSTAB


@pytest.mark.parametrize("kein_report", [None, [], "ok", 42, ["status", "ok"]])
def test_nicht_dict_wird_sauber_abgelehnt(kein_report):
    urteil = torwaechter(kein_report)
    assert urteil["entscheidung"] == ENTSCHEIDUNG_ABLEHNEN_KONVERSION
    assert urteil["empfiehlt_neuzentrierung"] is False


def test_urteil_traegt_immer_alle_felder():
    """Jeder Rückgabepfad liefert dieselbe Form — der Aufrufer muss nichts abfragen."""
    felder = {"entscheidung", "begruendung", "massstab", "georeferenz",
              "empfiehlt_neuzentrierung"}
    for eingabe in (report(BBOX_GESUND), report(BBOX_MM_ALS_M), report(BBOX_LV95),
                    report(None, status="error"), {}, None):
        assert set(torwaechter(eingabe)) == felder


def test_report_wird_nicht_veraendert():
    """Der Torwächter urteilt, er repariert nicht — auch nicht versehentlich."""
    eingabe = report(BBOX_MM_ALS_M)
    vorher = copy.deepcopy(eingabe)
    torwaechter(eingabe)
    assert eingabe == vorher


def test_nichts_wird_stillschweigend_umgerechnet():
    """Der Verdachtsfaktor wird gemeldet — die bbox bleibt, wie sie war."""
    eingabe = report(BBOX_MM_ALS_M)
    urteil = torwaechter(eingabe)
    assert urteil["massstab"]["verdacht_faktor"] == 1000
    assert eingabe["bbox"] == BBOX_MM_ALS_M
    assert urteil["massstab"]["groesste_kante_m"] == 8000.0


def test_kern_bleibt_stdlib_und_diesseits_der_prozessgrenze():
    """Regel 2 und Regel 4: kein bpy, kein ifcopenshell, keine Fremdabhängigkeit.

    Ein Torwächter, der eine GPU-Stunde sparen soll, muss überall laufen — auch dort, wo
    weder Blender noch das ``.venv-ifc`` existiert.
    """
    import ast

    from aiimaging import torwaechter as modul

    baum = ast.parse(open(modul.__file__, encoding="utf-8").read())
    module = set()
    for knoten in ast.walk(baum):
        if isinstance(knoten, ast.Import):
            module.update(a.name.split(".")[0] for a in knoten.names)
        elif isinstance(knoten, ast.ImportFrom) and knoten.level == 0 and knoten.module:
            module.add(knoten.module.split(".")[0])
    assert module <= {"__future__", "math"}
