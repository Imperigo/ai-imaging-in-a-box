"""Runde 7b — was angenommen wird, muss wirken; was nicht lesbar ist, hält nur sich auf.

Befunde der Durchsicht der Runde 7, nachgestellt am 23.09.2026
---------------------------------------------------------------
1. **Eine unlesbare Zahl nahm den Durchgang mit.** ``render.samples: "viele"`` (ebenso
   ``resolution: ["x", 1024]``, ``faithful: "hoch"``, ``Infinity``) warf in
   ``kosmo_szene.lies_szene`` einen nackten ``ValueError``/``OverflowError``;
   ``bruecke.lies_auftrag`` fing nur ``SzenenError``, und ``abholer.durchgang`` brach ab —
   kein weiterer Auftrag der Ablage wurde angesehen. Seither: jede Zahl ein Mangel mit
   Satz (erste Linie), und die Brücke fängt die übrigen Lesefehler (zweite Linie).
2. **Der MCP-Einlass nahm ``samples: "viele"`` an** und legte den Auftrag auf ``queued``.
   Seither weist er mit derselben Regel ab, mit der ``lies_szene`` später liest.
4. **Homeworker:** ``kamera_quelle`` war ``None`` für «Standpunkt von Hand» (``None``
   heisst hier «unbekannt»), und ``kamera`` mit NUR ``blick_auf`` hiess «zweimal bestellt».
5. **Geometrie-QA:** Ohne Score (gemeinsame Silhouette unter 32 Punkten) sagte der
   Richtungssatz, es werde «wie immer mit max(0, polaritaet * spearman)» gerechnet.
6. **Abholer:** Auf dem Weg «abgeleitet» mit ``deckungsgrad: null`` begründete das Urteil
   mit «ein anderer Kameraweg» — es ist derselbe; der Bericht widerspricht sich.

Bewacht über den Weg, den das Produkt geht: Brücke → ``durchgang``/``hole_einen``,
eigene Ablage → ``durchgang``, ``werkzeuge.enqueue_render``, ``homeworker.fuehre_aus``
bis zum Blender-Start (Attrappe), ``tiefenschaetzer.qa_gegen_soll`` mit Tiefenattrappe,
und der Verarbeiter des Abholers mit Multipass-Attrappe. Befund 3 (zwei f-Strings ohne
Platzhalter in ``kette.py``) ändert kein Verhalten und hat darum keinen Wächter hier.

Runde 7c — die Lücken, die die Durchsicht der 7b fand (nachgestellt am 23.09.2026)
------------------------------------------------------------------------------------
7. **Eine ganze Zahl mit 400 Stellen** warf ``OverflowError`` aus ``lies_zahl`` — genau
   die Ausnahme, die ``lies_zahl`` ersetzen sollte —, ebenso aus den Kamerafunktionen.
   Über die eigene Ablage riss das ``durchgang`` heraus (``eigene_quelle`` fing nur
   ``SzenenError``/``ValueError``/``TypeError``), am Einlass kam «OverflowError: …».
8. **Die zweite Linie der eigenen Ablage war ohne Wächter**: Seit der 7b wirft
   ``lies_szene`` bei ``"viele"`` nicht mehr. Seither fangen beide Wege
   ``kosmo_szene.LESEFEHLER``, bewacht mit derselben Attrappenliste auf beiden Wegen.
9. **Der Einlass prüfte und legte den rohen Wert ab**, ohne Obergrenze: ``512.0`` blieb
   ein float (und ``kosmo_naht.aufloesung_zu_resolution`` wies ihn ab), ``samples: 1e300``
   galt als angenommen. Seither dieselben Regeln (``REGEL_KANTE``, ``REGEL_SAMPLES``,
   mit Obergrenze) an Einlass, Abholer und Naht, und abgelegt wird die gelesene Zahl.
10. **Bei unlesbarem ``faithful``** stand in den Vertragsvorgaben «'faithful' (None) wird
    auf 'controlnet_staerke' abgebildet» — über eine Abbildung, die nicht stattfand.

Regel 3: Szenen, Aufträge und Karten sind synthetisch.
"""
from __future__ import annotations

import json
import math

import pytest

from aiimaging import abholer, bruecke, eigene_quelle, jobs, kosmo_szene, seams, werkzeuge

from test_abholer import _auftrag, _kette
from test_runde7_kamera import AUGE_L, BLICK_L, _hw_satz, hw
# Die Fixture wird nur ueber `request.getfixturevalue` geholt, nicht als Parameter —
# sonst meldet ruff den Parameter als Neudefinition des Imports.
from test_runde7_kamera import blender_start  # noqa: F401 (Fixture)
from test_runde7_richtung import _produktlauf


@pytest.fixture()
def bild(tmp_path):
    """Ein Bild, das existiert. Der Inhalt liest niemand — die Tiefenattrappe schätzt."""
    pfad = tmp_path / "render_1.png"
    pfad.write_bytes(b"\x89PNG\r\n\x1a\n")
    return pfad


# ======================================================================================
# 1 · Eine unlesbare Bestellung hält nur sich auf — über die Brücke
# ======================================================================================

def _szene(**render) -> dict:
    r = {"resolution": [512, 512], "samples": 64, "faithful": 0.8}
    r.update(render)
    return {"schema": kosmo_szene.SCHEMA_SZENE,
            "geometry": {"path": "model.glb", "format": "glb"},
            "cameras": "auto", "render": r,
            "style": {"prompt": "ein Haus", "mode": "none"},
            "vis": {"backbone": "qwen"}}


#: (Name, Szene, Feld, das im Mangel genannt sein muss). Die ersten fünf warfen bis zum
#: 23.09.2026; die übrigen gingen still durch und wurden anders gerechnet als bestellt.
UNLESBAR = [
    ("samples_text", _szene(samples="viele"), "'render.samples' ist 'viele'"),
    ("aufloesung_text", _szene(resolution=["x", 1024]), "'render.resolution[0]' ist 'x'"),
    ("aufloesung_unendlich", _szene(resolution=[math.inf, 1024]),
     "'render.resolution[0]' ist inf"),
    ("treue_text", _szene(faithful="hoch"), "'render.faithful' ist 'hoch'"),
    ("samples_nan", _szene(samples=math.nan), "'render.samples' ist nan"),
    ("samples_wahr", _szene(samples=True), "'render.samples' ist True"),
    ("samples_bruch", _szene(samples=1.5), "'render.samples' ist 1.5"),
    ("samples_null_stueck", _szene(samples=0), "'render.samples' ist 0"),
    ("aufloesung_negativ", _szene(resolution=[512, -5]), "'render.resolution[1]' ist -5"),
    ("render_kein_block", dict(_szene(), render="x"), "'render' ist str"),
    ("skip_als_text", dict(_szene(), vis={"backbone": "qwen", "skip": "false"}),
     "'vis.skip' ist 'false'"),
    ("refs_als_zahl", dict(_szene(), style={"prompt": "x", "refs": 5}),
     "'style.refs' ist 5"),
    ("backbone_als_liste", dict(_szene(), vis={"backbone": ["qwen"]}),
     "'vis.backbone' ist ['qwen']"),
]


def _durchgang_bruecke(basis):
    gesehen: list = []

    def verarbeite(auftrag):
        gesehen.append(auftrag["job_id"])
        return {"bilder": []}

    bericht = abholer.durchgang(basis, verarbeite=verarbeite, fremde_freigabe_gilt=True,
                                darf_rechnen=lambda: (True, "frei"))
    return bericht, gesehen


def _laufzettel(ordner) -> dict:
    return json.loads((ordner / bruecke.DATEI_LAUFZETTEL).read_text(encoding="utf-8"))


@pytest.mark.parametrize("name, szene, satz", UNLESBAR, ids=[u[0] for u in UNLESBAR])
def test_eine_unlesbare_zahl_haelt_nur_ihren_auftrag_auf(tmp_path, name, szene, satz):
    """**Der Wächter von 1.** Zwei Aufträge in der Ablage, der erste unlesbar: Der zweite
    wird trotzdem gerechnet, der erste bleibt auf ``queued`` und trägt den Satz."""
    kaputt = _auftrag(tmp_path, "vis-1700000000-aaaaaa", szene=szene)
    gut = _auftrag(tmp_path, "vis-1700000001-bbbbbb")

    bericht, gesehen = _durchgang_bruecke(tmp_path)

    assert bericht["gesehen"] == 2
    assert gesehen == [gut.name], "der zweite Auftrag wurde trotzdem gerechnet"
    antwort = bericht["ergebnisse"][0]
    assert antwort["tat"] == abholer.TAT_LIEGENGELASSEN
    assert satz in antwort["grund"], antwort["grund"]
    zettel = _laufzettel(kaputt)
    assert zettel["status"] == bruecke.STATUS_QUEUED
    assert satz in zettel[bruecke.FELD_MELDUNG], "der Grund steht am Auftrag"


def test_eine_unlesbare_zahl_ist_ein_mangel_und_ihr_feld_heisst_nicht_gelesen():
    """``None`` heisst NICHT GELESEN — nicht die Vorgabe 128 und nicht 0."""
    szene = kosmo_szene.lies_szene(_szene(samples="viele", resolution=["x", 1024]))
    assert szene["samples"] is None
    assert szene["aufloesung"] is None and szene["hoehe"] is None
    assert len(szene["maengel"]) == 2, "jedes unlesbare Feld mit eigenem Satz"


def test_gegenprobe_eine_ganze_zahl_mit_komma_null_kommt_als_zahl_an(tmp_path):
    """``64.0`` ist 64 und kein Mangel — es wirkt genau wie bestellt."""
    _auftrag(tmp_path, "vis-1700000000-aaaaaa",
             szene=_szene(samples=64.0, resolution=[512.0, 512]))
    ankunft: list = []

    bericht = abholer.durchgang(
        tmp_path, verarbeite=lambda a: ankunft.append(a["szene"]) or {"bilder": []},
        fremde_freigabe_gilt=True, darf_rechnen=lambda: (True, "frei"))

    assert bericht["verarbeitet"] == 1, bericht["ergebnisse"][0]["grund"]
    assert ankunft[0]["samples"] == 64 and isinstance(ankunft[0]["samples"], int)
    assert ankunft[0]["aufloesung"] == 512


#: Was eine Attrappe fuer ``lies_szene`` wirft — auf BEIDEN Wegen dieselbe Liste
#: (Runde 7c, 23.09.2026): Brücke und eigene Ablage fangen dieselben Fehlerarten, oder
#: einer der beiden Wächter fällt.
FEHLERARTEN = [TypeError, ValueError, AttributeError, OverflowError, ZeroDivisionError,
               KeyError, IndexError]


@pytest.mark.parametrize("art", FEHLERARTEN, ids=[a.__name__ for a in FEHLERARTEN])
def test_die_zweite_linie_faengt_was_lies_szene_uebersieht(tmp_path, monkeypatch, art):
    """Die Brücke fängt die Lesefehler, die ``lies_szene`` künftig übersieht — hier von
    einer Attrappe geworfen, die nur beim ersten Auftrag wirft."""
    fehler = art("x")
    echt = kosmo_szene.lies_szene

    def lies(fremd, **kw):
        if fremd.get("style", {}).get("prompt") == "KAPUTT":
            raise fehler
        return echt(fremd, **kw)

    monkeypatch.setattr(kosmo_szene, "lies_szene", lies)
    szene = dict(_szene(), style={"prompt": "KAPUTT"})
    kaputt = _auftrag(tmp_path, "vis-1700000000-aaaaaa", szene=szene)
    gut = _auftrag(tmp_path, "vis-1700000001-bbbbbb")

    bericht, gesehen = _durchgang_bruecke(tmp_path)

    assert gesehen == [gut.name]
    grund = bericht["ergebnisse"][0]["grund"]
    assert f"{type(fehler).__name__}" in grund and "nicht lesbar" in grund
    assert type(fehler).__name__ in _laufzettel(kaputt)[bruecke.FELD_MELDUNG]


def test_eine_kamera_im_unendlichen_haelt_nur_ihren_auftrag_auf(tmp_path):
    """``Infinity`` liest das Python-JSON, und ``float`` nahm es an: Die Kamera ging so
    an den Runner. Seither ``SzenenError`` mit Satz — über die Brücke ein Grund am
    Laufzettel, und der nächste Auftrag läuft."""
    kamera = {"name": "k1", "position": [math.inf, -30.0, 1.7],
              "target": [10.0, 8.0, 4.5], "fov": 50.0, "up_axis": "z"}
    kaputt = _auftrag(tmp_path, "vis-1700000000-aaaaaa",
                      szene=dict(_szene(), cameras=[kamera]))
    gut = _auftrag(tmp_path, "vis-1700000001-bbbbbb")

    bericht, gesehen = _durchgang_bruecke(tmp_path)

    assert gesehen == [gut.name]
    assert "keine endlichen Zahlen" in bericht["ergebnisse"][0]["grund"]
    assert "keine endlichen Zahlen" in _laufzettel(kaputt)[bruecke.FELD_MELDUNG]


@pytest.mark.parametrize("aufruf", [
    lambda: kosmo_szene.kamera_nach_blender(["x", 0, 0], "z"),
    lambda: kosmo_szene.kamera_zu_spec({"kuerzel": "k", "auge": ["x", 0, 0],
                                        "blick_auf": [1, 1, 1]}),
    # Runde 7c: eine ganze Zahl mit 400 Stellen warf OverflowError aus `float`.
    lambda: kosmo_szene.kamera_nach_blender([10**400, 0, 0], "z"),
    lambda: kosmo_szene.kamera_zu_spec({"kuerzel": "k", "auge": [10**400, 0, 0],
                                        "blick_auf": [1, 1, 1]}),
], ids=["kamera_nach_blender", "kamera_zu_spec", "kamera_nach_blender_riesig",
        "kamera_zu_spec_riesig"])
def test_die_oeffentlichen_kamerafunktionen_halten_ihre_zusage(aufruf):
    """Beide sagen ``SzenenError`` zu und warfen bei einem Text nackten ValueError —
    und bis zur Runde 7c bei einer riesigen ganzen Zahl OverflowError."""
    with pytest.raises(kosmo_szene.SzenenError, match="keine Zahlen"):
        aufruf()


# ======================================================================================
# 2 · Der MCP-Einlass weist ab, was der Abholer nicht lesen könnte
# ======================================================================================

@pytest.fixture()
def store(tmp_path, monkeypatch):
    """Eine eigene Ablage — **nie** die des Benutzers."""
    ziel = tmp_path / "aiimaging-jobs"
    monkeypatch.setenv(werkzeuge.UMGEBUNG_JOBS, str(ziel))
    return ziel


def _argumente(tmp_path, **zusatz) -> dict:
    glb = tmp_path / "modell.glb"
    glb.write_bytes(b"glTF-Attrappe")
    argumente = {"glb_path": str(glb), "up_axis": "Y", "bbox": [[0, 0, 0], [20, 15, 10]],
                 "approval_token": jobs.TOKEN_PRAEFIX + "TEST"}
    argumente.update(zusatz)
    return argumente


ABGEWIESEN = [("samples", "viele"), ("samples", True), ("samples", 0), ("samples", -3),
              ("samples", 1.5), ("samples", math.inf), ("samples", "128"),
              ("aufloesung", "gross"), ("aufloesung", 0), ("aufloesung", math.nan),
              ("aufloesung", [512, 512])]


@pytest.mark.parametrize("feld, wert", ABGEWIESEN)
def test_der_einlass_weist_eine_unbrauchbare_zahl_ab_und_legt_nichts_ab(
        tmp_path, store, feld, wert):
    """**Der Wächter von 2.** Kein Auftrag entsteht, und der Satz nennt Feld und Wert."""
    antwort = werkzeuge.enqueue_render(_argumente(tmp_path, **{feld: wert}))

    assert antwort["status"] is None and antwort["job_id"] is None
    assert f"'{feld}' ist {wert!r}" in antwort["error"], antwort["error"]
    assert not store.exists() or not any(store.iterdir()), "es wurde nichts abgelegt"


def _durchgang_eigen(store):
    gesehen: list = []

    def verarbeite(auftrag):
        gesehen.append(auftrag["szene"])
        return {"bilder": [], "geometrie_urteil": None, "stil_urteil": None,
                "kameras": [], "zeiten": {"gesamt": 0.0}}

    return abholer.durchgang(store, verarbeite=verarbeite, quelle=eigene_quelle,
                             darf_rechnen=lambda: (True, "frei")), gesehen


def test_gegenprobe_was_der_einlass_annimmt_kommt_beim_abholer_an(tmp_path, store):
    """Angenommen heisst: Es wirkt. Die Zahlen kommen über die eigene Ablage beim
    Verarbeiter an, genau wie bestellt."""
    antwort = werkzeuge.enqueue_render(_argumente(tmp_path, samples=64, aufloesung=768))
    assert antwort["status"] == jobs.STATUS_QUEUED, antwort

    bericht, gesehen = _durchgang_eigen(store)

    assert bericht["verarbeitet"] == 1, bericht["ergebnisse"][0]["grund"]
    assert gesehen[0]["samples"] == 64 and gesehen[0]["aufloesung"] == 768


@pytest.mark.parametrize("feld, wert", ABGEWIESEN)
def test_eine_regel_was_der_einlass_abweist_hielte_auch_der_abholer_auf(
        tmp_path, store, feld, wert):
    """Einlass und ``lies_szene`` urteilen mit DERSELBEN Regel: Ein Auftrag, der am
    Einlass abgewiesen würde und trotzdem in der Ablage liegt (vor der Runde 7b
    angenommen), bleibt beim Abholer mit einem Mangel liegen — er stürzt nicht und
    rechnet nicht."""
    gut = werkzeuge.enqueue_render(_argumente(tmp_path))
    satz = jobs.lies_job(gut["job_id"], store / gut["job_id"])
    satz["params"][feld] = wert
    jobs.schreibe_job(satz, store / gut["job_id"])

    bericht, gesehen = _durchgang_eigen(store)

    assert gesehen == [], "nichts gerechnet"
    antwort = bericht["ergebnisse"][0]
    assert antwort["tat"] == abholer.TAT_LIEGENGELASSEN
    assert "Mängel" in antwort["grund"] and "erwartet war" in antwort["grund"]


# ======================================================================================
# 4 · Homeworker: «von Hand» ist bekannt, und ein halber Standpunkt ist kein doppelter
# ======================================================================================

def test_homeworker_standpunkt_von_hand_heisst_von_hand_und_nicht_unbekannt(
        tmp_path, request):
    request.getfixturevalue("blender_start")
    ergebnis = hw.fuehre_aus(_hw_satz(tmp_path, auge=AUGE_L, blick_auf=BLICK_L), tmp_path)
    assert ergebnis["status"] == "ok", ergebnis["fehler"]
    befund = ergebnis["messwerte"]["kamerabestellung"]
    assert befund["kamera_quelle"] == "von_hand", befund


@pytest.mark.parametrize("kamera", ["nNW", None])
@pytest.mark.parametrize("halb, fehlt", [({"blick_auf": BLICK_L}, "auge"),
                                         ({"auge": AUGE_L}, "blick_auf")])
def test_homeworker_ein_halber_standpunkt_heisst_unvollstaendig(
        tmp_path, request, monkeypatch, kamera, halb, fehlt):
    """**Der Wächter von 4.** Mit und ohne ``kamera``: Der Satz nennt, was fehlt, und
    weder umgewandelt noch gestartet wird."""
    gestartet = request.getfixturevalue("blender_start")
    umgewandelt = []
    monkeypatch.setattr(seams, "ifc_zu_glb",
                        lambda ifc, glb, **kw: umgewandelt.append(ifc) or {})
    params = dict(halb, **({"kamera": kamera} if kamera else {}))
    ergebnis = hw.fuehre_aus(_hw_satz(tmp_path, **params), tmp_path)

    assert ergebnis["status"] == "fehler"
    assert ergebnis["urteil"] == {"auftrag": "standpunkt unvollstaendig"}
    assert f"{fehlt} fehlt" in ergebnis["fehler"], ergebnis["fehler"]
    assert "zweimal" not in ergebnis["fehler"]
    assert gestartet == [] and umgewandelt == []


# ======================================================================================
# 5 · Geometrie-QA: ohne Score wird nichts gerechnet, und der Satz sagt es
# ======================================================================================

def _richtungssatz(warnungen) -> str:
    saetze = [w for w in warnungen if "Rangkorrelation zeigt" in w
              or "Richtung ist nicht bestimmbar" in w]
    assert len(saetze) == 1, warnungen
    return saetze[0]


@pytest.mark.parametrize("schritt, steigung, vorzeichen, fall", [
    (9, 0.0, -1, "nicht bestimmbar"),     # rho nahe null, Grenze 0,459 bei 20 Punkten
    (1, 1.0, -1, "erwartete Richtung"),
    (1, 1.0, +1, "falsche Richtung"),
])
def test_ohne_score_behauptet_der_richtungssatz_keine_rechnung(
        bild, schritt, steigung, vorzeichen, fall):
    """**Der Wächter von 5**, über ``qa_gegen_soll`` (Polarität −1, wie der Homeworker)
    mit 20 gemeinsamen Punkten: kein Score, und keiner der drei Sätze spricht von einer
    Rechnung, die nicht stattfand."""
    urteil = _produktlauf(bild, 20, schritt=schritt, steigung=steigung,
                          vorzeichen=vorzeichen, breite=5)
    assert urteil["score"] is None and urteil["n_gemeinsam"] == 20, "Vorbedingung"

    satz = _richtungssatz(urteil["warnungen"])
    assert fall in satz, satz
    assert "max(0" not in satz and "abgeschnitten" not in satz
    assert "entscheidet allein der Score" not in satz
    assert "NICHT gerechnet (None, nicht 0)" in satz
    assert satz not in urteil["begruendung"], "die Begründung bleibt der Grund"


def test_gegenprobe_mit_score_bleibt_der_satz_ueber_die_rechnung(bild):
    urteil = _produktlauf(bild, schritt=235, steigung=0.0, vorzeichen=-1)
    assert urteil["score"] is not None, "Vorbedingung"
    satz = _richtungssatz(urteil["warnungen"])
    assert "Richtung ist nicht bestimmbar" in satz, "Vorbedingung: unbestimmt"
    assert "max(0, polaritaet * spearman)" in satz
    assert "NICHT gerechnet" not in satz


# ======================================================================================
# 6 · Abholer: «abgeleitet» mit null ist ein Bericht, der sich widerspricht
# ======================================================================================

def _rahmung_ueber_den_verarbeiter(tmp_path, bericht_zusatz: dict) -> list[dict]:
    ordner = _auftrag(tmp_path, szene=_szene())
    _, attrappen = _kette()
    vorher = attrappen["_multipass"]

    def multipass(glb, out, **kw):
        daten = vorher(glb, out, **kw)
        daten.update(bericht_zusatz)
        return daten

    attrappen["_multipass"] = multipass
    antwort = abholer.hole_einen(
        ordner, fremde_freigabe_gilt=True,
        verarbeite=abholer.verarbeiter(out_wurzel=tmp_path / "aus", nullprobe=False,
                                       **attrappen))
    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort["grund"]
    urteile = sorted((tmp_path / "aus" / ordner.name).glob(f"*/{abholer.DATEI_URTEIL}"))
    assert urteile, "Vorbedingung: mindestens ein Kameraurteil"
    return [json.loads(p.read_text(encoding="utf-8"))["urteil"]["rahmung"]
            for p in urteile]


def test_abgeleitet_mit_null_sagt_dass_der_bericht_sich_widerspricht(tmp_path):
    """**Der Wächter von 6**, über Brücke, ``hole_einen`` und den Verarbeiter."""
    for rahmung in _rahmung_ueber_den_verarbeiter(
            tmp_path, {"kamera": {"weg": "abgeleitet"}, "deckungsgrad": None}):
        assert rahmung["deckungsgrad_quelle"] == "nicht_gerahmt"
        assert "WIDERSPRICHT SICH" in rahmung["grund"], rahmung["grund"]
        assert "anderen Kameraweg" not in rahmung["grund"]


def test_gegenprobe_vorgegeben_mit_null_bleibt_der_andere_kameraweg(tmp_path):
    for rahmung in _rahmung_ueber_den_verarbeiter(
            tmp_path, {"kamera": {"weg": "vorgegeben"}, "deckungsgrad": None,
                       "deckungsgrad_wirkungslos": "vorgegeben: kein Deckungsgrad"}):
        assert "anderen Kameraweg" in rahmung["grund"], rahmung["grund"]
        assert "WIDERSPRICHT" not in rahmung["grund"]


# ======================================================================================
# 7 · Runde 7c: eine riesige ganze Zahl ist ein Satz, kein OverflowError
# ======================================================================================

#: 1 mit 400 Nullen — das JSON kennt keine Grenze, und Python liest sie als ``int``.
RIESIG = 10**400
RIESIG_SATZ = "ist eine ganze Zahl mit rund 401 Stellen"

KAMERA_RIESIG = {"name": "k1", "position": [RIESIG, -30.0, 1.7],
                 "target": [10.0, 8.0, 4.5], "fov": 50.0, "up_axis": "z"}

#: (Name, Szene, Satz im Grund). Alle warfen bis zur Runde 7c OverflowError.
RIESIG_UEBER_DIE_BRUECKE = [
    ("samples", _szene(samples=RIESIG), f"'render.samples' {RIESIG_SATZ}"),
    ("aufloesung", _szene(resolution=[RIESIG, 512]),
     f"'render.resolution[0]' {RIESIG_SATZ}"),
    ("treue", _szene(faithful=RIESIG), f"'render.faithful' {RIESIG_SATZ}"),
    ("kamerapunkt", dict(_szene(), cameras=[KAMERA_RIESIG]), "enthält keine Zahlen"),
    ("bildwinkel", dict(_szene(), cameras=[dict(KAMERA_RIESIG, position=[0, -30, 1.7],
                                                fov=RIESIG)]),
     "fov muss zwischen 0 und 180 Grad liegen, war: eine ganze Zahl mit rund 401"),
]


@pytest.mark.parametrize("name, szene, satz", RIESIG_UEBER_DIE_BRUECKE,
                         ids=[r[0] for r in RIESIG_UEBER_DIE_BRUECKE])
def test_eine_riesige_zahl_ueber_die_bruecke_haelt_nur_ihren_auftrag_auf(
        tmp_path, name, szene, satz):
    """**Der Wächter von 7**, über Brücke und ``durchgang``: ein Satz am Laufzettel, und
    der zweite Auftrag wird gerechnet. Der Satz stammt aus ``lies_szene`` selbst — der
    Typname der zweiten Linie steht nicht darin."""
    kaputt = _auftrag(tmp_path, "vis-1700000000-aaaaaa", szene=szene)
    gut = _auftrag(tmp_path, "vis-1700000001-bbbbbb")

    bericht, gesehen = _durchgang_bruecke(tmp_path)

    assert gesehen == [gut.name]
    grund = bericht["ergebnisse"][0]["grund"]
    assert satz in grund, grund
    assert "OverflowError" not in grund, "die erste Linie hat es benannt"
    assert satz in _laufzettel(kaputt)[bruecke.FELD_MELDUNG]


#: (Feld, Wert, Satz). Am Einlass bis zur Runde 7c angenommen oder als «OverflowError».
ZU_GROSS = [
    ("samples", RIESIG, f"'samples' {RIESIG_SATZ}"),
    ("samples", 1e300, "'samples' ist 1e+300"),
    ("samples", 2**63, f"'samples' ist {2**63}"),
    ("samples", kosmo_szene.SAMPLES_HOECHSTENS + 1,
     f"'samples' ist {kosmo_szene.SAMPLES_HOECHSTENS + 1}"),
    ("aufloesung", RIESIG, f"'aufloesung' {RIESIG_SATZ}"),
    ("aufloesung", kosmo_szene.KANTE_HOECHSTENS + 1,
     f"'aufloesung' ist {kosmo_szene.KANTE_HOECHSTENS + 1}"),
]

ZU_GROSS_IDS = ["samples-400-stellen", "samples-1e300", "samples-2hoch63",
                "samples-grenze-plus-1", "aufloesung-400-stellen", "aufloesung-grenze-plus-1"]


@pytest.mark.parametrize("feld, wert, satz", ZU_GROSS, ids=ZU_GROSS_IDS)
def test_der_einlass_weist_eine_zu_grosse_zahl_mit_satz_ab(tmp_path, store, feld, wert,
                                                           satz):
    """**Der Wächter von 7 und 9 am Einlass.** Ein Satz mit Feld und Grund, kein
    ``OverflowError``, und nichts wird abgelegt."""
    antwort = werkzeuge.enqueue_render(_argumente(tmp_path, **{feld: wert}))

    assert antwort["status"] is None and antwort["job_id"] is None
    assert satz in antwort["error"], antwort["error"]
    assert "zu gross" in antwort["error"]
    assert not store.exists() or not any(store.iterdir()), "es wurde nichts abgelegt"


@pytest.mark.parametrize("feld, wert, satz", ZU_GROSS, ids=ZU_GROSS_IDS)
def test_eine_riesige_zahl_ueber_die_eigene_ablage_haelt_nur_ihren_auftrag_auf(
        tmp_path, store, feld, wert, satz):
    """**Der Wächter von 7 über die eigene Ablage** — und von 9: Einlass und Abholer
    haben dieselbe Obergrenze. Ein Auftrag, der so in der Ablage liegt (vor der Runde 7c
    angenommen), bleibt mit einem Mangel liegen; der zweite wird gerechnet."""
    kaputt = werkzeuge.enqueue_render(_argumente(tmp_path))["job_id"]
    satz_alt = jobs.lies_job(kaputt, store / kaputt)
    satz_alt["params"][feld] = wert
    jobs.schreibe_job(satz_alt, store / kaputt)
    gut = werkzeuge.enqueue_render(_argumente(tmp_path))["job_id"]

    bericht, gesehen = _durchgang_eigen(store)

    assert bericht["gesehen"] == 2
    assert len(gesehen) == 1, "der lesbare Auftrag wurde trotzdem gerechnet"
    antworten = {a["job_id"]: a for a in bericht["ergebnisse"]}
    assert antworten[gut]["tat"] == abholer.TAT_VERARBEITET
    assert antworten[kaputt]["tat"] == abholer.TAT_LIEGENGELASSEN
    assert "zu gross" in antworten[kaputt]["grund"], antworten[kaputt]["grund"]
    assert "OverflowError" not in antworten[kaputt]["grund"]
    assert "zu gross" in jobs.lies_job(kaputt, store / kaputt)["meldung"]


def test_eine_zahl_mit_ueber_4300_stellen_ist_ebenfalls_ein_satz():
    """``repr`` einer solchen Zahl wirft selbst ``ValueError`` (Python ab 3.11) — der
    Satz nennt sie darum mit ihrer Stellenzahl."""
    zahl, satz = kosmo_szene.lies_zahl(10**5000, "render.samples",
                                       **kosmo_szene.REGEL_SAMPLES)
    assert zahl is None
    assert "ist eine ganze Zahl mit rund 5001 Stellen" in satz


# ======================================================================================
# 8 · Runde 7c: Die eigene Ablage fängt, was die Brücke fängt — dieselbe Liste
# ======================================================================================

@pytest.mark.parametrize("art", FEHLERARTEN, ids=[a.__name__ for a in FEHLERARTEN])
def test_die_zweite_linie_der_eigenen_ablage_faengt_dasselbe_wie_die_bruecke(
        tmp_path, store, monkeypatch, art):
    """**Der Wächter von 8**, über Einlass, eigene Ablage und ``durchgang``: Eine
    Attrappe für ``lies_szene`` wirft beim ersten Auftrag; er bleibt mit dem Typnamen im
    Grund liegen, und der zweite wird gerechnet. Dieselbe ``FEHLERARTEN`` wie beim
    Wächter der Brücke oben."""
    echt = kosmo_szene.lies_szene

    def lies(fremd, **kw):
        if str(fremd.get("out", "")).endswith("KAPUTT"):
            raise art("x")
        return echt(fremd, **kw)

    monkeypatch.setattr(kosmo_szene, "lies_szene", lies)
    kaputt = werkzeuge.enqueue_render(
        _argumente(tmp_path, out_dir=str(tmp_path / "KAPUTT")))["job_id"]
    gut = werkzeuge.enqueue_render(_argumente(tmp_path))["job_id"]

    bericht, gesehen = _durchgang_eigen(store)

    assert bericht["gesehen"] == 2 and len(gesehen) == 1
    antworten = {a["job_id"]: a for a in bericht["ergebnisse"]}
    assert antworten[gut]["tat"] == abholer.TAT_VERARBEITET
    grund = antworten[kaputt]["grund"]
    assert antworten[kaputt]["tat"] == abholer.TAT_LIEGENGELASSEN
    assert f"{art.__name__}" in grund and "nicht lesbar" in grund, grund
    assert art.__name__ in jobs.lies_job(kaputt, store / kaputt)["meldung"]


# ======================================================================================
# 9 · Runde 7c: abgelegt wird die gelesene Zahl — eine Regel an Einlass, Naht, Abholer
# ======================================================================================

@pytest.mark.parametrize("feld, wert, erwartet", [
    ("aufloesung", 512.0, 512),
    ("samples", 64.0, 64),
    ("samples", kosmo_szene.SAMPLES_HOECHSTENS, kosmo_szene.SAMPLES_HOECHSTENS),
    ("aufloesung", kosmo_szene.KANTE_HOECHSTENS, kosmo_szene.KANTE_HOECHSTENS),
], ids=repr)
def test_gegenprobe_angenommen_heisst_als_ganze_zahl_abgelegt_und_so_angekommen(
        tmp_path, store, feld, wert, erwartet):
    """**Der Wächter von 9.** ``512.0`` ist 512: Abgelegt wird die ganze Zahl, die
    Naht in ihren Vertrag übersetzt den Auftrag (bis zur Runde 7c wies sie ``512.0`` ab),
    und beim Verarbeiter kommt die Zahl an, wie bestellt. Die Obergrenze selbst gilt
    noch als angenommen."""
    from aiimaging import kosmo_naht

    antwort = werkzeuge.enqueue_render(_argumente(tmp_path, **{feld: wert}))
    assert antwort["status"] == jobs.STATUS_QUEUED, antwort
    satz = jobs.lies_job(antwort["job_id"], store / antwort["job_id"])
    assert satz["params"][feld] == erwartet and type(satz["params"][feld]) is int

    if feld == "aufloesung":
        fremd = kosmo_naht.als_kosmo_auftrag(satz)
        assert fremd["params"]["resolution"] == f"{erwartet}x{erwartet}"

    bericht, gesehen = _durchgang_eigen(store)
    assert bericht["verarbeitet"] == 1, bericht["ergebnisse"][0]["grund"]
    assert gesehen[0][feld] == erwartet and type(gesehen[0][feld]) is int


def test_die_naht_liest_eine_alte_float_aufloesung_wie_der_abholer():
    """Ein Auftrag, der VOR der Runde 7c mit ``512.0`` abgelegt wurde: Die Naht nimmt ihn
    als 512 (wie ``lies_szene``), statt ihn abzuweisen."""
    from aiimaging import kosmo_naht

    assert kosmo_naht.aufloesung_zu_resolution(512.0) == "512x512"
    with pytest.raises(kosmo_naht.NahtError, match="zu gross"):
        kosmo_naht.aufloesung_zu_resolution(kosmo_szene.KANTE_HOECHSTENS + 1)


# ======================================================================================
# 10 · Runde 7c: kein Satz über eine Abbildung, die nicht stattfand
# ======================================================================================

def _vorgaben_ueber_die_bruecke(tmp_path, szene) -> tuple:
    _auftrag(tmp_path, "vis-1700000000-aaaaaa", szene=szene)
    bericht, _ = _durchgang_bruecke(tmp_path)
    return bericht["ergebnisse"][0]


def test_unlesbares_faithful_wird_nicht_als_abgebildet_gemeldet(tmp_path):
    """**Der Wächter von 10**, über Brücke und ``durchgang``: Der Grund nennt das Feld,
    und die Vertragsvorgaben behaupten keine Abbildung."""
    antwort = _vorgaben_ueber_die_bruecke(tmp_path, _szene(faithful="hoch"))

    assert antwort["tat"] == abholer.TAT_LIEGENGELASSEN
    assert "'render.faithful' ist 'hoch'" in antwort["grund"]
    assert not [v for v in antwort["vertragsvorgaben"] if "controlnet_staerke" in v], \
        antwort["vertragsvorgaben"]


def test_gegenprobe_lesbares_faithful_bleibt_als_abgebildet_gemeldet(tmp_path):
    antwort = _vorgaben_ueber_die_bruecke(tmp_path, _szene(faithful=0.8))

    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort["grund"]
    assert [v for v in antwort["vertragsvorgaben"]
            if "'faithful' (0.8) wird auf 'controlnet_staerke' abgebildet" in v]
