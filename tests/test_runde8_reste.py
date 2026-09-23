"""Runde 8 — die Reste der Durchsicht der 7c, nachgestellt am 23.09.2026.

Befunde (jeder zuerst selbst nachgefahren)
------------------------------------------
K1. ``kosmo_szene.kamera_zu_spec`` nahm ``auge [inf, 0, 0]`` und ``blick_auf [nan, 0, 0]``
    still an und gab ``position [inf, …]`` in eine CameraSpec; ``kamera_nach_blender``
    gab ``(inf, 0.0, 0.0)`` zurück. Nur ``spec_zu_kamera`` prüfte die Endlichkeit.
    Nebenfund: Der Satz über eine unlesbare Kamera rief ``repr`` jeder Zahl, und eine
    ganze Zahl mit über 4300 Stellen warf dabei selbst ``ValueError``.
K2. ``kosmo_naht.resolution_zu_aufloesung`` (fremd → unser) kannte keine Obergrenze:
    ``"100000x100000"`` wurde still ``aufloesung 100000``; über 4300 Ziffern warf
    ``int(...)`` einen nackten ``ValueError`` statt ``NahtError``.
K3. ``render.faithful: 5.0`` ging ohne Mangel durch und stand als
    ``controlnet_staerke 5.0`` in der Szene. Der Vertrag sagt «0..1».
K4. ``kosmo_naht.als_kosmo_auftrag`` warf ``NahtError`` bei JEDEM Auftrag aus
    ``werkzeuge.enqueue_render`` ohne Auflösung — dort steht ``"aufloesung": None``, und
    übersetzt wurde auch das ``None``. Dieselbe Form im Rückweg (``resolution: null``).
K5. Kein Befund, sondern ein Entscheid, der gehalten werden muss: Der Runner nennt
    ``deckungsgrad_wirkungslos`` auch OHNE Bestellung, die drei Kamerawerte der Runde 7
    nur mit. Der Grund ist ein Leser — ``abholer._rahmung_vor_dem_render`` braucht den
    Satz für «nicht gerahmt». Bewacht über den echten Runner (Attrappe von ``bpy``) und
    den Verarbeiter des Abholers.

Bewacht über den Weg, den das Produkt geht: Brücke → ``durchgang``, ``enqueue_render`` →
eigene Ablage → Naht, Runner-``main`` → Abholer. ``kamera_zu_spec`` hat im Produkt keinen
Aufrufer (nur ``tools/beweis/21``) und wird darum direkt gerufen.

Regel 3: Szenen, Aufträge und Punkte sind synthetisch.
"""
from __future__ import annotations

import math

import pytest

from aiimaging import abholer, bruecke, jobs, kosmo_naht, kosmo_szene, werkzeuge
from aiimaging.kosmo_naht import NahtError
from aiimaging.kosmo_szene import SzenenError

from test_abholer import _auftrag
from test_runde7_kamera import AUGE, BESTELLUNGEN, _bericht
from test_runde7b_einlass import (
    _argumente,
    _durchgang_eigen,
    _laufzettel,
    _rahmung_ueber_den_verarbeiter,
    _szene,
)
# Die Fixture wird nur ueber `request.getfixturevalue` geholt — siehe test_runde7b_einlass.
from test_runde7b_einlass import store  # noqa: F401 (Fixture)

#: Eine ganze Zahl mit 5001 Stellen: `repr` wirft darauf ab Python 3.11 `ValueError`.
UEBER_4300 = 10**5000

GUTE_KAMERA = {"kuerzel": "k", "auge": [40.0, -30.0, 1.7], "blick_auf": [10.0, 8.0, 4.5],
               "brennweite_mm": 35.0}


# ======================================================================================
# K1 · Ein Punkt im Unendlichen ist kein Standpunkt — auch auf dem Hinweg
# ======================================================================================

@pytest.mark.parametrize("feld, punkt", [
    ("auge", [math.inf, 0.0, 0.0]),
    ("auge", [0.0, -math.inf, 1.7]),
    ("blick_auf", [math.nan, 0.0, 0.0]),
    ("blick_auf", [0.0, 0.0, 1e999]),
], ids=["auge_inf", "auge_minus_inf", "blick_nan", "blick_1e999"])
def test_kamera_zu_spec_weist_einen_nicht_endlichen_punkt_ab(feld, punkt):
    """**Der Wächter von K1.** Bis zur Runde 8 kam hier eine CameraSpec mit ``inf``
    heraus; ihr Schema hätte sie drüben abgewiesen oder, schlimmer, gerechnet."""
    with pytest.raises(SzenenError, match=f"Kamera '{feld}' enthaelt keine endlichen"):
        kosmo_szene.kamera_zu_spec(dict(GUTE_KAMERA, **{feld: punkt}))


def test_gegenprobe_eine_endliche_kamera_geht_hin_und_zurueck():
    """Die Prüfung nimmt nichts weg, was ging: hin als CameraSpec, zurück als Kamera."""
    spec = kosmo_szene.kamera_zu_spec(GUTE_KAMERA)
    zurueck = kosmo_szene.spec_zu_kamera(spec)
    assert list(zurueck["auge"]) == GUTE_KAMERA["auge"]
    assert list(zurueck["blick_auf"]) == GUTE_KAMERA["blick_auf"]
    assert zurueck["brennweite_mm"] == pytest.approx(35.0)


@pytest.mark.parametrize("achse", ["y", "z"])
@pytest.mark.parametrize("punkt", [[math.inf, 0, 0], [0, math.nan, 0], [0, 0, -math.inf]],
                         ids=["inf", "nan", "minus_inf"])
def test_kamera_nach_blender_weist_einen_nicht_endlichen_punkt_ab(achse, punkt):
    """Öffentlich und ohne eigene Prüfung gab sie ``(inf, 0.0, 0.0)`` zurück — gedreht
    wie ungedreht."""
    with pytest.raises(SzenenError, match="keine endlichen Zahlen"):
        kosmo_szene.kamera_nach_blender(punkt, achse)


def test_gegenprobe_kamera_nach_blender_dreht_weiter():
    assert kosmo_szene.kamera_nach_blender([1, 2, 3], "z") == (1.0, 2.0, 3.0)
    assert kosmo_szene.kamera_nach_blender([1, 2, 3], "y") == pytest.approx((1.0, -3.0, 2.0))


@pytest.mark.parametrize("aufruf", [
    lambda: kosmo_szene.kamera_zu_spec(dict(GUTE_KAMERA, auge=[UEBER_4300, 0, 0])),
    lambda: kosmo_szene.kamera_nach_blender([UEBER_4300, 0, 0], "z"),
    lambda: kosmo_szene.spec_zu_kamera({"name": "k", "position": [UEBER_4300, 0, 0],
                                        "target": [1, 1, 1], "fov": 50, "up_axis": "z"}),
], ids=["kamera_zu_spec", "kamera_nach_blender", "spec_zu_kamera"])
def test_der_satz_ueber_eine_riesige_zahl_wird_nicht_selbst_zum_fehler(aufruf):
    """Nebenfund K1: ``repr`` der Liste warf ``ValueError`` (Grenze der Umwandlung in
    Text) — aus dem Satz, der den Fehler erklären sollte. Seither die Stellenzahl."""
    with pytest.raises(SzenenError, match="ganze Zahl mit rund 5001 Stellen"):
        aufruf()


# ======================================================================================
# K2 · Der Rückweg der Naht hält dieselbe Obergrenze wie der Hinweg
# ======================================================================================

GRENZE = kosmo_szene.KANTE_HOECHSTENS


@pytest.mark.parametrize("wert", [f"{GRENZE + 1}x512", f"512x{GRENZE + 1}",
                                  "100000x100000", "1" * 5000 + "x5", "5x" + "9" * 30],
                         ids=["breite", "hoehe", "beide", "ueber_4300_ziffern",
                              "dreissig_ziffern"])
def test_eine_zu_grosse_fremde_resolution_ist_ein_nahtfehler(wert):
    """**Der Wächter von K2**, über den Weg, den ein fremder Auftrag nimmt:
    ``aus_kosmo_auftrag``. Bis zur Runde 8 wurde ``100000x100000`` still
    ``aufloesung 100000``, und 5000 Ziffern warfen nackten ``ValueError``."""
    fremd = {"job_id": "vis-1700000000-aaaaaa", "status": "queued",
             "params": {"resolution": wert}}
    with pytest.raises(NahtError, match="zu gross"):
        kosmo_naht.aus_kosmo_auftrag(fremd)


@pytest.mark.parametrize("wert, erwartet", [
    (f"{GRENZE}x{GRENZE}", GRENZE), ("000512x512", 512), ("1920x1440", 1440)],
    ids=["grenze", "fuehrende_nullen", "vorgabe_drueben"])
def test_gegenprobe_was_die_regel_annimmt_kommt_als_kante_an(wert, erwartet):
    fremd = {"job_id": "vis-1700000000-aaaaaa", "status": "queued",
             "params": {"resolution": wert}}
    assert kosmo_naht.aus_kosmo_auftrag(fremd)["params"]["aufloesung"] == erwartet


def test_hin_und_zurueck_dieselbe_grenze():
    """Eine Regel, nicht zwei: Was der Hinweg an der Grenze annimmt, nimmt der Rückweg
    auch, und was er abweist, weist der Rückweg ab."""
    assert kosmo_naht.resolution_zu_aufloesung(
        kosmo_naht.aufloesung_zu_resolution(GRENZE))["aufloesung"] == GRENZE
    for richtung in (lambda: kosmo_naht.aufloesung_zu_resolution(GRENZE + 1),
                     lambda: kosmo_naht.resolution_zu_aufloesung(f"{GRENZE + 1}x1")):
        with pytest.raises(NahtError, match="zu gross"):
            richtung()


# ======================================================================================
# K3 · faithful ist ein Regler von 0 bis 1
# ======================================================================================

def _durchgang_mit_szenen(basis):
    """Wie ``_durchgang_bruecke``, aber der Verarbeiter merkt sich die gelesene Szene."""
    gesehen: list = []

    def verarbeite(auftrag):
        gesehen.append(auftrag["szene"])
        return {"bilder": []}

    bericht = abholer.durchgang(basis, verarbeite=verarbeite, fremde_freigabe_gilt=True,
                                darf_rechnen=lambda: (True, "frei"))
    return bericht, gesehen


@pytest.mark.parametrize("wert", [5.0, -0.1, 1.0000001, 2, -1e-300],
                         ids=["fuenf", "minus", "knapp_ueber_eins", "zwei_ganz",
                              "winzig_negativ"])
def test_faithful_ausserhalb_von_null_bis_eins_haelt_nur_seinen_auftrag_auf(
        tmp_path, wert):
    """**Der Wächter von K3**, über Brücke und ``durchgang``: Mangel mit Satz am
    Laufzettel, kein Abbildungssatz in den Vertragsvorgaben, und der zweite Auftrag
    wird gerechnet."""
    kaputt = _auftrag(tmp_path, "vis-1700000000-aaaaaa", szene=_szene(faithful=wert))
    gut = _auftrag(tmp_path, "vis-1700000001-bbbbbb")

    bericht, gesehen = _durchgang_mit_szenen(tmp_path)

    assert len(gesehen) == 1, "nur der zweite Auftrag wurde gerechnet"
    assert gut.name == bericht["ergebnisse"][1]["job_id"]
    antwort = bericht["ergebnisse"][0]
    assert antwort["tat"] == abholer.TAT_LIEGENGELASSEN
    satz = f"'render.faithful' ist {wert!r}, erwartet war eine endliche Zahl ab 0 bis 1"
    assert satz in antwort["grund"], antwort["grund"]
    assert satz in _laufzettel(kaputt)[bruecke.FELD_MELDUNG]
    assert not [v for v in antwort["vertragsvorgaben"] if "controlnet_staerke" in v]


@pytest.mark.parametrize("wert", [0, 0.0, 0.8, 1, 1.0], ids=repr)
def test_gegenprobe_faithful_im_bereich_kommt_als_controlnet_staerke_an(tmp_path, wert):
    """Die Grenzen selbst gelten als angenommen — und die Zahl kommt beim Verarbeiter
    an, wie bestellt."""
    _auftrag(tmp_path, "vis-1700000000-aaaaaa", szene=_szene(faithful=wert))

    bericht, gesehen = _durchgang_mit_szenen(tmp_path)

    assert bericht["verarbeitet"] == 1, bericht["ergebnisse"][0]["grund"]
    assert gesehen[0]["controlnet_staerke"] == float(wert)


def test_der_mcp_einlass_nimmt_kein_faithful_an(tmp_path, request):
    """Die Aussage an ``REGEL_TREUE``, dass die Regel am MCP-Einlass nicht gebraucht
    wird, über den Produktweg: ``faithful`` im Aufruf erreicht weder den abgelegten
    Auftrag noch die Szene, die der Abholer liest — dort gilt die Vorgabe des Vertrags.
    Fällt dieser Test, nimmt der Einlass ``faithful`` an, und dann gehört
    ``REGEL_TREUE`` auch dorthin."""
    ablage = request.getfixturevalue("store")
    antwort = werkzeuge.enqueue_render(_argumente(tmp_path, faithful=5.0))
    assert antwort["status"] == jobs.STATUS_QUEUED, antwort
    satz = jobs.lies_job(antwort["job_id"], ablage / antwort["job_id"])
    assert not {"faithful", "treue", "controlnet_staerke"} & set(satz["params"])

    bericht, gesehen = _durchgang_eigen(ablage)
    assert bericht["verarbeitet"] == 1, bericht["ergebnisse"][0]["grund"]
    assert gesehen[0]["controlnet_staerke"] == 0.8


# ======================================================================================
# K4 · None heisst nicht bestellt — auch an der Naht
# ======================================================================================

def test_ein_auftrag_ohne_aufloesung_laesst_sich_in_ihren_vertrag_uebersetzen(
        tmp_path, request):
    """**Der Wächter von K4**, über den Produktweg: ``enqueue_render`` ohne Auflösung
    legt ``"aufloesung": None`` ab; die Naht übersetzt den Auftrag, statt ihn
    abzuweisen, und setzt KEIN ``resolution`` — dann gilt drüben ihre Vorgabe."""
    ablage = request.getfixturevalue("store")
    antwort = werkzeuge.enqueue_render(_argumente(tmp_path))
    satz = jobs.lies_job(antwort["job_id"], ablage / antwort["job_id"])
    assert satz["params"]["aufloesung"] is None, "Vorbedingung: so legt der Einlass ab"
    assert satz["params"]["samples"] is None

    fremd = kosmo_naht.als_kosmo_auftrag(satz)

    assert "resolution" not in fremd["params"] and "aufloesung" not in fremd["params"]
    assert fremd["params"]["samples"] is None, "die übrigen Felder gehen, wie sie sind"
    zurueck = kosmo_naht.aus_kosmo_auftrag(fremd)
    assert zurueck["params"].get("aufloesung") is None


def test_gegenprobe_eine_bestellte_aufloesung_wird_weiter_uebersetzt(tmp_path, request):
    ablage = request.getfixturevalue("store")
    antwort = werkzeuge.enqueue_render(_argumente(tmp_path, aufloesung=768))
    satz = jobs.lies_job(antwort["job_id"], ablage / antwort["job_id"])

    fremd = kosmo_naht.als_kosmo_auftrag(satz)

    assert fremd["params"]["resolution"] == "768x768"
    assert kosmo_naht.aus_kosmo_auftrag(fremd)["params"]["aufloesung"] == 768


def test_ihr_resolution_null_heisst_auch_bei_uns_nicht_bestellt():
    """Dieselbe Form im Rückweg: ``resolution: null`` warf ``NahtError``."""
    fremd = {"job_id": "vis-1700000000-aaaaaa", "status": "queued",
             "params": {"resolution": None, "samples": 64}}
    unser = kosmo_naht.aus_kosmo_auftrag(fremd)
    assert unser["params"]["aufloesung"] is None
    assert "resolution" not in unser["params"]
    assert unser["params"]["samples"] == 64


def test_gegenprobe_eine_unbrauchbare_aufloesung_faellt_weiter_auf():
    """``None`` ist nicht bestellt, ``0`` ist falsch bestellt — das bleibt ein Fehler."""
    satz = jobs.baue_job(job_id=jobs.neue_job_id(), art="render", params={"aufloesung": 0})
    with pytest.raises(NahtError, match="aufloesung"):
        kosmo_naht.als_kosmo_auftrag(satz)


# ======================================================================================
# K5 · Der Deckungsgrad nennt seinen Grund auch ohne Bestellung, die drei anderen nicht
# ======================================================================================

def test_ohne_bestellung_bekommt_der_abholer_seinen_grund_fuer_nicht_gerahmt(
        monkeypatch, tmp_path):
    """**Der Wächter von K5**, über den echten Runner (``main`` mit Attrappe von
    ``bpy``) und den Verarbeiter des Abholers: Standpunkt von Hand, NICHTS bestellt.

    Der Runner nennt ``deckungsgrad_wirkungslos`` — und genau dieser Satz steht im
    Urteil des Abholers als Grund für «nicht gerahmt». Die drei Werte der Runde 7 bleiben
    ohne Satz; sie haben keinen Leser."""
    lauf = tmp_path / "runner"
    lauf.mkdir()
    bericht = _bericht(monkeypatch, lauf, *AUGE)
    assert bericht["kamera"]["weg"] == "vorgegeben"
    grund = bericht["deckungsgrad_wirkungslos"]
    assert bericht["deckungsgrad"] is None
    assert isinstance(grund, str) and "Bestellt war keiner" in grund, grund
    for name in BESTELLUNGEN:
        assert bericht[name] is None and bericht[f"{name}_wirkungslos"] is None, name

    felder = {"kamera": bericht["kamera"], "deckungsgrad": None,
              "deckungsgrad_wirkungslos": grund,
              **{f"{n}_wirkungslos": bericht[f"{n}_wirkungslos"] for n in BESTELLUNGEN}}
    abholung = tmp_path / "abholung"
    abholung.mkdir()
    for rahmung in _rahmung_ueber_den_verarbeiter(abholung, felder):
        assert rahmung["deckungsgrad_quelle"] == "nicht_gerahmt"
        assert rahmung["deckungsgrad_wirkungslos"] == grund
        assert grund in rahmung["grund"], rahmung["grund"]
        assert "nennt keinen Grund" not in rahmung["grund"]


def test_gegenprobe_ohne_den_satz_des_runners_fehlt_dem_abholer_der_grund(tmp_path):
    """Was der Satz trägt, zeigt sein Fehlen: Dann steht im Urteil nur, dass der Bericht
    keinen Grund nennt. Das ist der Grund, warum der Deckungsgrad nicht an die drei
    anderen angeglichen wurde."""
    for rahmung in _rahmung_ueber_den_verarbeiter(
            tmp_path, {"kamera": {"weg": "vorgegeben"}, "deckungsgrad": None,
                       "deckungsgrad_wirkungslos": None}):
        assert "nennt keinen Grund" in rahmung["grund"], rahmung["grund"]

