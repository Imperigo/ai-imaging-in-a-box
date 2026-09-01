"""Die drei Befunde aus Demolauf 12 (01.09.2026) — jeder als Probe.

Alle drei sind am Gerät entstanden, nicht am Schreibtisch, und alle drei haben
gemeinsam, dass **etwas Gebautes nicht angeschlossen war**:

1. ``up_axis`` ist im fremden Vertrag Pflichtfeld ohne Vorgabewert, wird gesendet, für
   die Geometrie angewandt — und für eine mitgelieferte Kameraliste verworfen.
2. Der Bericht entsteht erst am Ende. Ein Absturz an Kamera 2 vernichtete das fertige,
   gemessene Urteil von Kamera 1.
3. Der Abholer kannte den Grund, warum er nicht rechnet, und sagte ihn ins Journal.
   Der Auftrag trug ihn nicht — obwohl der fremde Vertrag ein Feld dafür führt.

Die Zahlen in den Kamerafällen sind die **echten** aus dem Auftrag
``vis-1788277501-b799e4`` und die daran gemessene Hüllbox seiner ``model.glb``. Sie
stehen hier als Literale, weil die Datei ein flüchtiger Auftrag in ``/tmp`` war und die
Probe sie überleben soll (REGEL 3: keine Benutzerpfade).
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from aiimaging import abholer, bruecke, contracts, eigene_quelle, jobs, kosmo_szene
from conftest import MINI_PNG

# ======================================================================================
# Die Zahlen des Vorfalls
# ======================================================================================

#: Die beiden Kameras, wie der Auto-Kamera-Knoten sie schickte — wörtlich.
KAMERAS_DES_VORFALLS = [
    {"name": "Eingang", "position": [121.238, 0.615, 23.878],
     "target": [121.238, 11.135, -90.087], "fov": 55, "up_axis": "y"},
    {"name": "Uebersicht", "position": [289.958, 53.553, 55.513],
     "target": [121.238, 14.165, -90.087], "fov": 45, "up_axis": "y"},
]

#: Die Hüllbox der ``model.glb`` dieses Auftrags in **Blenders** Weltsystem, gemessen mit
#: ``glbbox.bauwerksbox(..., up_axis="Y")`` (2725 Knoten).
HUELLBOX_BLENDER = ([68.513, 60.482, -0.985], [173.963, 119.692, 29.314])


# ======================================================================================
# POSTEN 1 · Der Achsenbruch — die Drehung muss BEIDE treffen
# ======================================================================================

def test_eine_y_up_kameraliste_wird_mitgedreht():
    """Die Geometrie wird beim Import gedreht. Die Kamera muss dieselbe Drehung erfahren.

    Blenders glTF-Import rechnet Y-up nach Z-up um (``R_x(+90)``). Eine Kamera, die in
    Dateikoordinaten hereinkommt, muss durch dieselbe Drehung — sonst steht sie in einem
    anderen Achsensystem als das Bauwerk, das sie zeigen soll.
    """
    kamera = kosmo_szene.spec_zu_kamera(KAMERAS_DES_VORFALLS[0])
    assert kamera["auge"] == pytest.approx((121.238, -23.878, 0.615))
    assert kamera["blick_auf"] == pytest.approx((121.238, 90.087, 11.135))
    # Und die BESTELLTEN Zahlen bleiben lesbar: Ohne sie wäre eine gedrehte Kamera von
    # einer ungedrehten im Bericht nicht mehr zu unterscheiden.
    assert kamera["auge_bestellt"] == pytest.approx((121.238, 0.615, 23.878))
    assert kamera["up_axis"] == "y"


def test_das_gedrehte_blickziel_trifft_die_mitte_der_huellbox():
    """Der Beleg, dass die Drehung die RICHTIGE ist — und nicht bloss irgendeine.

    Beide Kameras des Vorfalls zielen auf denselben Punkt. Gedreht liegt er **exakt**
    auf der Mitte der Szenenbox in x und y. Ungedreht liegt er 89 m unter der tiefsten
    Geometrie. Zwei Kameras, zwei Treffer, ein Zufall wäre das nicht.
    """
    lo, hi = HUELLBOX_BLENDER
    mitte_x = (lo[0] + hi[0]) / 2.0
    mitte_y = (lo[1] + hi[1]) / 2.0
    for spec in KAMERAS_DES_VORFALLS:
        ziel = kosmo_szene.spec_zu_kamera(spec)["blick_auf"]
        assert ziel[0] == pytest.approx(mitte_x, abs=1e-3)
        assert ziel[1] == pytest.approx(mitte_y, abs=1e-3)
        assert lo[2] <= ziel[2] <= hi[2], "und die Höhe liegt im Bauwerk"

    # Die Gegenprobe: ROH ist derselbe Punkt weit unterhalb von allem.
    roh_z = KAMERAS_DES_VORFALLS[0]["target"][2]
    assert roh_z < lo[2] - 80.0, (
        "Ohne diese Zeile prüfte der Test nur, dass die Drehung etwas tut — nicht, dass "
        "sie nötig war.")


def test_eine_z_up_kameraliste_wird_NICHT_gedreht():
    """Der zweite Fall des Pflichtfelds: Wer Z-up sendet, rechnet schon in unserer Achse.

    Ohne diese Probe wäre die Drehung eine, die immer greift — und dann wäre das
    Pflichtfeld wieder überflüssig, nur mit umgekehrtem Vorzeichen des Fehlers.
    """
    kamera = kosmo_szene.spec_zu_kamera(
        {"name": "sSE", "position": [10.0, -20.0, 1.7], "target": [0.0, 0.0, 5.0],
         "fov": 50, "up_axis": "z"})
    assert kamera["auge"] == pytest.approx((10.0, -20.0, 1.7))
    assert kamera["blick_auf"] == pytest.approx((0.0, 0.0, 5.0))
    # Und die Achse steht im Ergebnis. Auch das fehlte: Bis zum 01.09.2026 las die Naht
    # das Feld gar nicht — «nicht gedreht» und «Achse nie gelesen» sahen von aussen
    # gleich aus, und nur der eine der beiden Fälle war richtig.
    assert kamera["up_axis"] == "z"


def test_eine_kameraspec_ohne_up_axis_wird_abgewiesen():
    """PFLICHTFELD OHNE VORGABEWERT — hier wie drüben.

    ``CameraSpec.up_axis`` ist ``z.enum(['y','z'])`` ohne Default. Es steht dort wegen
    eines früheren Vorfalls; es hier zu ignorieren und eine Achse anzunehmen, hiesse den
    Riegel zu umgehen, der genau dafür gebaut wurde.
    """
    with pytest.raises(kosmo_szene.SzenenError, match="up_axis"):
        kosmo_szene.spec_zu_kamera(
            {"name": "n", "position": [1, 2, 3], "target": [0, 0, 0], "fov": 50})


def test_eine_unbekannte_hochachse_wird_nicht_geraten():
    with pytest.raises(kosmo_szene.SzenenError, match="up_axis"):
        kosmo_szene.spec_zu_kamera(
            {"position": [1, 2, 3], "target": [0, 0, 0], "up_axis": "x"})


def test_unsere_eigenen_kameraspecs_tragen_die_hochachse_mit():
    """Die Gegenrichtung — und sie war ebenfalls kaputt, nur unbemerkt.

    ``CameraSpec.up_axis`` ist bei ihnen Pflicht. Eine Spec ohne dieses Feld wird von
    ihrem eigenen Schema **abgewiesen**; wir haben also Aufträge gebaut, die drüben gar
    nicht durchkommen. ``"z"`` ist keine Wahl: ``kameras.kamerasatz`` rechnet aus der
    Hüllbox des Blender-Berichts, und die steht in Blenders Weltsystem.
    """
    spec = kosmo_szene.kamera_zu_spec(
        {"kuerzel": "sSE", "auge": (1.0, 2.0, 3.0), "blick_auf": (4.0, 5.0, 6.0),
         "brennweite_mm": 35.0})
    assert spec["up_axis"] == "z"


def test_der_rundlauf_bleibt_verlustfrei():
    """Hin und zurück muss dieselbe Kamera ergeben — sonst hat die Drehung sie verbogen."""
    unsere = {"kuerzel": "n", "auge": (1.0, 2.0, 3.0), "blick_auf": (4.0, 5.0, 6.0),
              "brennweite_mm": 35.0}
    spec = kosmo_szene.kamera_zu_spec(unsere)
    # Ein Rundlauf ueber eine Spec, die ihr Schema ABWEIST, ist kein Rundlauf, sondern
    # eine Rechnung ueber ein Zwischenergebnis, das nie ankommt.
    assert "up_axis" in spec, "sonst weist ihr zod-Schema die Spec ab"
    zurueck = kosmo_szene.spec_zu_kamera(spec)
    assert zurueck["auge"] == pytest.approx(unsere["auge"])
    assert zurueck["blick_auf"] == pytest.approx(unsere["blick_auf"])


def test_die_drehung_ist_dieselbe_wie_die_der_geometrie():
    """Eine ZWEITE Fassung derselben Formel wäre die Falle noch einmal.

    ``contracts.blender_gltf_import_dreht`` schreibt aus, was Blenders Importer mit der
    Geometrie tut. Die Kamera muss durch genau diese Rechnung — nicht durch eine
    danebenstehende, die heute dasselbe ergibt und morgen nicht mehr.
    """
    for punkt in ((1.0, 2.0, 3.0), (-4.5, 0.0, 7.25), (0.0, 0.0, 0.0)):
        assert (kosmo_szene.kamera_nach_blender(punkt, "y")
                == pytest.approx(contracts.blender_gltf_import_dreht(punkt)))


# --------------------------------------------------------------------------------------
# … und wenn es doch schiefgeht, muss es LAUT sein
# --------------------------------------------------------------------------------------

def test_ein_sehstrahl_an_der_szene_vorbei_faellt_auf():
    """Die Zahlen des Vorfalls, ungedreht — der Riegel muss sie erkennen."""
    lage = abholer._blick_trifft_szene({
        "kamera": {"auge": KAMERAS_DES_VORFALLS[0]["position"],
                   "blick_auf": KAMERAS_DES_VORFALLS[0]["target"]},
        "bbox": [list(HUELLBOX_BLENDER[0]), list(HUELLBOX_BLENDER[1])]})
    assert lage["abbruch"] is True
    assert lage["geprueft"] is True
    assert "up_axis" in lage["grund"], "der Grund muss die häufigste Ursache nennen"


def test_derselbe_sehstrahl_gedreht_faellt_nicht_auf():
    """Die Gegenprobe. Ohne sie riegelte der Riegel vielleicht einfach immer."""
    kamera = kosmo_szene.spec_zu_kamera(KAMERAS_DES_VORFALLS[0])
    lage = abholer._blick_trifft_szene({
        "kamera": {"auge": list(kamera["auge"]), "blick_auf": list(kamera["blick_auf"])},
        "bbox": [list(HUELLBOX_BLENDER[0]), list(HUELLBOX_BLENDER[1])]})
    assert lage["abbruch"] is False
    assert lage["geprueft"] is True


def test_ohne_huellbox_wird_nicht_geurteilt():
    """Eine fehlende Hüllbox ist keine verfehlte Kamera, sondern eine fehlende Hüllbox."""
    lage = abholer._blick_trifft_szene({"kamera": {"auge": [0, 0, 0],
                                                   "blick_auf": [1, 1, 1]}})
    assert lage["abbruch"] is False
    assert lage["geprueft"] is False


# ======================================================================================
# Attrappen für die Kette — mit Hüllbox und Kamerablock, anders als in `test_abholer`
# ======================================================================================

def _bericht(out, *, auge, blick_auf):
    """Ein Multipass-Bericht, wie der Runner ihn schreibt — verkürzt, aber echt."""
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    for name in ("tiefe.png", "beauty.png"):
        (out / name).write_bytes(MINI_PNG)
    (out / "tiefe.exr").write_bytes(b"\x76\x2f\x31\x01EXR-Attrappe")
    return {
        "depth_png": str(out / "tiefe.png"),
        "beauty_png": str(out / "beauty.png"),
        "depth_exr": str(out / "tiefe.exr"),
        "bbox": [list(HUELLBOX_BLENDER[0]), list(HUELLBOX_BLENDER[1])],
        "kamera": {"weg": "vorgegeben", "auge": list(auge), "blick_auf": list(blick_auf)},
    }


def _kette_mit_kameras(*, bricht_bei=None):
    """Attrappen, die den Kamerablock durchreichen. ``bricht_bei`` lässt EINE scheitern."""
    protokoll = {"multipass": [], "render": []}

    def multipass(glb, out, **kw):
        protokoll["multipass"].append(kw)
        return _bericht(out, auge=kw["auge"], blick_auf=kw["blick_auf"])

    def rendere(a, **kw):
        protokoll["render"].append(a)
        if bricht_bei is not None and bricht_bei in str(a.ausgabe_png):
            # Wörtlich der Fehler aus Demolauf 12 — ein Gerätefehler mitten im Auftrag.
            return {"status": "fehler", "error": (
                "RuntimeError: Expected all tensors to be on the same device")}
        Path(a.ausgabe_png).parent.mkdir(parents=True, exist_ok=True)
        Path(a.ausgabe_png).write_bytes(b"png")
        return {"status": "ok", "bild_png": a.ausgabe_png}

    def soll(bericht):
        return [0.0, 1.0, 2.0, 3.0], 2, 2

    def qa(bild, soll_werte, **kw):
        if Path(bild).name.startswith("nullprobe_"):
            return {"status": "ok", "score": 0.30, "bestanden": False}
        return {"status": "ok", "score": 0.91, "bestanden": True,
                "rho_maske": {"gerichtet": 0.77, "anteil_maske": 0.31},
                "geom_iou": 0.88}

    return protokoll, dict(_multipass=multipass, _rendere=rendere, _soll=soll, _qa=qa)


def _auftrag_mit_kameras(basis, kameras, *, name="vis-1788277501-b799e4"):
    ordner = basis / name
    ordner.mkdir(parents=True, exist_ok=True)
    (ordner / bruecke.DATEI_LAUFZETTEL).write_text(json.dumps(
        {"job_id": name, "status": bruecke.STATUS_QUEUED,
         "approval_token": "CONFIRMED_RENDER_a1b2c3d4"}), encoding="utf-8")
    (ordner / bruecke.DATEI_SZENE).write_text(json.dumps({
        "schema": kosmo_szene.SCHEMA_SZENE,
        "geometry": {"path": "model.glb", "format": "glb"},
        "cameras": kameras,
        "render": {"resolution": [512, 512], "samples": 64, "faithful": 0.8},
        "style": {"prompt": "ein Haus"},
        "vis": {"backbone": "qwen"},
    }), encoding="utf-8")
    (ordner / bruecke.DATEI_MODELL).write_bytes(b"glTF\x02\x00\x00\x00")
    return ordner


# ======================================================================================
# POSTEN 2 · Ein Urteil darf nicht an einem späteren Absturz sterben
# ======================================================================================

def test_das_urteil_der_ersten_kamera_ueberlebt_den_absturz_der_zweiten(tmp_path):
    """Demolauf 12, Posten 2 — und der Grund, warum der Maskenweg dreimal nichts sagte.

    Kamera 1 läuft durch und wird gemessen. Kamera 2 stürzt am Gerätefehler ab. Der
    Auftrag geht auf ``error`` — richtig so —, aber das, was Kamera 1 gekostet hat,
    muss auf der Platte liegen.
    """
    kameras = [
        {"name": "eins", "position": [121.238, -80.0, 12.0],
         "target": [121.238, 90.087, 11.135], "fov": 50, "up_axis": "z"},
        {"name": "zwei", "position": [230.0, 90.0, 12.0],
         "target": [121.238, 90.087, 11.135], "fov": 50, "up_axis": "z"},
    ]
    ordner = _auftrag_mit_kameras(tmp_path, kameras)
    _protokoll, attrappen = _kette_mit_kameras(bricht_bei="zwei")
    aus = tmp_path / "aus"

    antwort = abholer.hole_einen(
        ordner, fremde_freigabe_gilt=True,
        verarbeite=abholer.verarbeiter(out_wurzel=aus, **attrappen))

    assert antwort["tat"] == abholer.TAT_FEHLER, "der Absturz bleibt ein Absturz"
    # DER NAME STEHT HIER ALS LITERAL, und die Zeile darunter haelt ihn gegen die
    # Konstante. Das ist dieselbe Einbahnstrasse wie bei
    # `contracts.blender_gltf_import_dreht`: Waere hier nur `abholer.DATEI_URTEIL`
    # gepruegt, schluege die Probe an der alten Fassung mit einem `AttributeError` fehl
    # — richtig rot, aber aus dem falschen Grund. Sie soll an der FEHLENDEN DATEI
    # scheitern, denn das war der Befund.
    datei = aus / ordner.name / "eins" / "urteil.json"
    assert datei.is_file(), (
        "Das gemessene Urteil der ersten Kamera ist mit dem Prozess gestorben. Genau "
        "das war Demolauf 12: In keinem Ausgabeordner lag rho_maske, geom_iou oder "
        "paarurteil — obwohl Kamera 1 vollständig durchgelaufen war.")
    assert abholer.DATEI_URTEIL == datei.name, "ein Name, an einer Stelle entschieden"
    abgelegt = json.loads(datei.read_text(encoding="utf-8"))
    assert abgelegt["kamera"] == "eins"
    assert abgelegt["urteil"]["score"] == pytest.approx(0.91)
    assert abgelegt["urteil"]["rho_maske"]["gerichtet"] == pytest.approx(0.77)
    assert abgelegt["urteil"]["geom_iou"] == pytest.approx(0.88)


def test_das_abgelegte_urteil_traegt_keine_benutzerpfade(tmp_path):
    """REGEL 3 — die Datei liegt im Auftragsverzeichnis der fremden Oberfläche."""
    kameras = [{"name": "eins", "position": [121.238, -80.0, 12.0],
                "target": [121.238, 90.087, 11.135], "fov": 50, "up_axis": "z"}]
    ordner = _auftrag_mit_kameras(tmp_path, kameras)
    _protokoll, attrappen = _kette_mit_kameras()
    aus = tmp_path / "aus"
    abholer.hole_einen(ordner, fremde_freigabe_gilt=True,
                       verarbeite=abholer.verarbeiter(out_wurzel=aus, **attrappen))
    text = (aus / ordner.name / "eins" / abholer.DATEI_URTEIL).read_text(encoding="utf-8")
    assert str(tmp_path) not in text
    assert "/home/" not in text


def test_auch_eine_uebersprungene_kamera_hinterlaesst_ihr_urteil(tmp_path):
    """Ein Riegel VOR dem Bildlauf ist ein Befund und muss ebenso überleben."""
    kameras = [{"name": "daneben", "position": KAMERAS_DES_VORFALLS[0]["position"],
                "target": KAMERAS_DES_VORFALLS[0]["target"], "fov": 55, "up_axis": "z"}]
    ordner = _auftrag_mit_kameras(tmp_path, kameras)
    protokoll, attrappen = _kette_mit_kameras()
    aus = tmp_path / "aus"
    abholer.hole_einen(ordner, fremde_freigabe_gilt=True,
                       verarbeite=abholer.verarbeiter(out_wurzel=aus, **attrappen))

    assert protokoll["render"] == [], (
        "Der Sehstrahl verfehlt die Szene — es darf gar nicht erst gerendert werden.")
    abgelegt = json.loads(
        (aus / ordner.name / "daneben" / abholer.DATEI_URTEIL).read_text(encoding="utf-8"))
    assert abgelegt["urteil"]["gemessen"] is False
    assert "Sehstrahl verfehlt" in abgelegt["urteil"]["grund"]

    # UND DER FREMDE VERTRAG BEKOMMT DEN RICHTIGEN GRUND, nicht den nächstbesten.
    #
    # Beim Bauen fast passiert: `_uebersprungenes_urteil` legt seinen Riegel unter
    # `rahmung` ab, und `_nicht_gerendert_kurz` liest ihn dort. Der Blickfeldbefund wäre
    # damit als Rahmungsfall herausgegangen — «Das Bauwerk füllt zu wenig der
    # Bildbreite», für eine Kamera, die das Bauwerk gar nicht anschaut, mit einer
    # Bildbreite, die nie gemessen wurde. Ein falscher Grund ist schlimmer als keiner.
    ergebnis = json.loads((ordner / bruecke.DATEI_ERGEBNIS).read_text(encoding="utf-8"))
    begruendung = ergebnis["qa"]["verdict"]["reason"]
    assert "an der Szene vorbei" in begruendung, (
        f"Der fremde Vertrag nennt nicht den Blickfeldbefund: {begruendung!r}")
    assert "Rahmung" not in begruendung, "und schon gar nicht den falschen Grund"


def test_ein_liegengelassener_auftrag_traegt_seinen_grund(tmp_path):
    """Demolauf 12, Posten 3. Der Grund stand im Journal, der Auftrag hatte ihn nicht.

    ``message`` ist **ihr** Feld, wörtlich aus ``render-result.ts``: «Menschlicher
    Zusatztext (z. B. Abbruch-/Wartegrund), UI-lesbar.» Es lag bereit und wurde nie
    beschrieben.
    """
    ordner = _auftrag_mit_kameras(tmp_path, "auto")
    zettel = json.loads((ordner / bruecke.DATEI_LAUFZETTEL).read_text(encoding="utf-8"))
    zettel["idle_window_only"] = True
    (ordner / bruecke.DATEI_LAUFZETTEL).write_text(json.dumps(zettel), encoding="utf-8")

    def belegt():
        return False, "Auslastung 12 % (Grenze 10 %)."

    antwort = abholer.hole_einen(
        ordner, verarbeite=lambda a: pytest.fail("es darf nicht gerechnet werden"),
        fremde_freigabe_gilt=True, darf_rechnen=belegt)

    assert antwort["tat"] == abholer.TAT_LIEGENGELASSEN
    assert antwort["grund_vermerkt"] is True
    nachher = json.loads((ordner / bruecke.DATEI_LAUFZETTEL).read_text(encoding="utf-8"))
    assert nachher["status"] == bruecke.STATUS_QUEUED, (
        "Der Status ist richtig — der Auftrag WARTET wirklich. Fehlte nur das Warum.")
    assert "Auslastung 12 %" in nachher[bruecke.FELD_MELDUNG]
    assert "idle_window_only" in nachher[bruecke.FELD_MELDUNG]


def test_auch_eine_fehlende_freigabe_ist_ein_grund(tmp_path):
    """Der zweite Weg, auf dem ein Auftrag liegen bleibt — dieselbe Auskunft."""
    ordner = _auftrag_mit_kameras(tmp_path, "auto")
    antwort = abholer.hole_einen(ordner, verarbeite=lambda a: pytest.fail("nein"))
    assert antwort["tat"] == abholer.TAT_LIEGENGELASSEN
    zettel = json.loads((ordner / bruecke.DATEI_LAUFZETTEL).read_text(encoding="utf-8"))
    assert zettel[bruecke.FELD_MELDUNG]


def test_ein_auftrag_der_laeuft_traegt_die_begruendung_von_gestern_nicht_mehr(tmp_path):
    """Sonst wäre ein rechnender Auftrag von einem wartenden nicht zu unterscheiden."""
    ordner = _auftrag_mit_kameras(tmp_path, "auto")
    bruecke.vermerke_grund(ordner, "Karte war belegt.")
    assert bruecke.FELD_MELDUNG in json.loads(
        (ordner / bruecke.DATEI_LAUFZETTEL).read_text(encoding="utf-8"))

    abholer.hole_einen(ordner, verarbeite=lambda a: {"bilder": []},
                       fremde_freigabe_gilt=True)
    nachher = json.loads((ordner / bruecke.DATEI_LAUFZETTEL).read_text(encoding="utf-8"))
    assert bruecke.FELD_MELDUNG not in nachher


def test_der_grund_wird_auf_BEIDEN_wegen_vermerkt(tmp_path):
    """Ein Auftrag aus dem Cockpit und einer aus der Oberfläche antworten gleich.

    Sonst hinge die Auskunft daran, welchen Weg die Bestellung genommen hat — und genau
    solche einseitigen Riegel zählt ``test_riegel_auf_beiden_wegen`` sonst nach.
    """
    kennung = jobs.neue_job_id()
    satz = jobs.baue_job(job_id=kennung, art="render", params={"x": 1},
                         approval_token=None)
    ordner = tmp_path / kennung
    ordner.mkdir()
    jobs.schreibe_job(satz, ordner)

    eigene_quelle.vermerke_grund(ordner, "Die Karte ist nicht frei.")
    nachher = jobs.lies_job(kennung, ordner)
    assert nachher["meldung"] == "Die Karte ist nicht frei."
    assert nachher["status"] == satz["status"], "kein Statuswechsel durch einen Kommentar"

    eigene_quelle.vermerke_grund(ordner, "")
    assert "meldung" not in jobs.lies_job(kennung, ordner)


# ======================================================================================
# NEBENBEFUND · Der Bericht des Abholers nannte nie einen Zustand
# ======================================================================================

def test_der_bericht_nennt_den_zustand_und_nicht_ein_fragezeichen(capsys):
    """Im Journal von Demolauf 12 steht 24 Mal ``vis-…: ? — …``.

    ``_berichte`` fragte den Eintrag nach ``status``. ``hole_einen`` liefert diesen
    Schlüssel nicht — es liefert ``tat``. Der Vorgabewert des ``get`` hat den fehlenden
    Schlüssel als Auskunft verkleidet: **jede** Zeile trug ein Fragezeichen, und der
    Grund daneben liess es wie eine Eigenheit des Einzelfalls aussehen.
    """
    import importlib.util

    pfad = Path(__file__).resolve().parents[1] / "tools" / "abholen.py"
    spez = importlib.util.spec_from_file_location("abholen_probe", pfad)
    modul = importlib.util.module_from_spec(spez)
    spez.loader.exec_module(modul)

    modul._berichte({
        "gesehen": 1, "verarbeitet": 0, "fehler": 0, "liegengelassen": 1,
        "ergebnisse": [{
            "job_id": "vis-1788277501-b799e4",
            "tat": abholer.TAT_LIEGENGELASSEN,
            "grund": ("Der Auftrag trägt 'idle_window_only' und die Karte ist nicht "
                      "frei: Auslastung 12 % (Grenze 10 %)."),
            "wache": None, "verzeichnis": "",
        }],
    })
    zeile = next(z for z in capsys.readouterr().out.splitlines()
                 if "vis-1788277501-b799e4" in z)
    assert abholer.TAT_LIEGENGELASSEN in zeile
    assert "?" not in zeile.split("—")[0], (
        "Der Zustand stand nie da — nur ein Fragezeichen, das nach einem Sonderfall "
        "aussah und in Wahrheit ein falscher Schlüsselname war.")
