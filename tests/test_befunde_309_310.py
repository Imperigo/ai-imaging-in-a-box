"""Befunde der HomeStation aus auf-20261021-309 und auf-20261021-310 (21.10.2026), dazu 289 B2.

* **309 B3 (Teil S):** Nach dem Herausnehmen des Stimmungssatzes bestand der Prompt nur noch
  aus ihm — S1 «abend» zeigte eine Höhle, S2 «nebel» ein Gestell. Ist der Bauteil leer, kommt
  «architectural building» davor; der Stimmungssatz bleibt einmal.
* **309 E2n:** Bildeingang mit ``no_grad`` 27 116 statt 31 316 MiB — das Register ist gesenkt
  (mit Rand für mehrere Kameras); die Rechnung steht in ``test_befunde_298``.
* **309 B1:** Bei ``umriss_halten = im_lauf`` zählte ``ausserhalb_umriss_anteil`` den
  festgehaltenen Hintergrund als Baumasse (bis 4,53). Jetzt gilt dort ``anteil_haus_nah``.
* **310 B1:** ``vis_verbinden {from: 'A-1'}`` — eine KARTENkennung — ging durch, weil «A-1» in
  einem Ergebnis stand. Jetzt mit Satz abgewiesen.
* **310 B2:** «Rechne jetzt das Bild.» rief kein Werkzeug mehr. Jetzt steht im Systemsatz, dass
  ein Render-Auftrag kein Freigeben ist, und der Kern stösst einmal an.
* **310 B3:** Der kurze Satz «Freigeben kann nur der Architekt.» weicht dem vollen.
* **289 B2:** Ohne Modell hiess es an der Tür «nicht zu finden» statt «nicht bekannt».

Regel 3: alles synthetisch, kein Netz, keine Gewichte; das Sprachmodell ist ein Ersatz.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from aiimaging import assistent, baumasse, knotenweg, kosmo_szene, stimmung

WURZEL = Path(__file__).resolve().parents[1]
LISTE = WURZEL / "kosmovis" / "apps" / "visbox-knoten" / "dist" / "ki-werkzeugliste.json"


# ====================================================================== 309 B3 · Gebäudewort

@pytest.fixture
def himmel(tmp_path, monkeypatch):
    ordner = tmp_path / "himmel"
    ordner.mkdir()
    for preset, eintrag in stimmung.STIMMUNGEN.items():
        for a in ("2k", "4k"):
            (ordner / stimmung.dateiname(preset, eintrag["hdri"], a)).write_bytes(b"#?RADIANCE\n")
    monkeypatch.setenv(stimmung.HIMMEL_ORDNER_ENV, str(ordner))
    return ordner


def _szene(prompt, preset):
    return {"geometry": {"path": "/x/model.glb", "format": "glb"}, "cameras": "auto",
            "render": {"environment": {"preset": preset}}, "style": {"prompt": prompt},
            "vis": {}}


@pytest.mark.parametrize("prompt, preset", [
    ("Abendstimmung, warmes Licht, leuchtende Fenster", "abend"),     # S1 wörtlich
    ("Nebel, gedämpftes Licht, Tiefe im Dunst", "nebel"),               # S2 wörtlich
])
def test_ohne_bauteil_kommt_das_gebaeudewort_vor_den_stimmungssatz(himmel, prompt, preset):
    s = kosmo_szene.lies_szene(_szene(prompt, preset))
    satz = stimmung.STIMMUNGEN[preset]["prompt_en"]
    assert s["maengel"] == ()
    assert s["prompt"] == f"{kosmo_szene.GEBAEUDEWORT}, {satz}"
    assert s["prompt"].count(satz) == 1                                 # einmal, englisch
    assert s["prompt_zusaetze"][0]["art"] == "gebaeudewort"
    assert "309" in s["prompt_zusaetze"][0]["grund"]


def test_mit_eigenem_bauteil_bleibt_der_prompt_wort_fuer_wort(himmel):
    s = kosmo_szene.lies_szene(_szene("a quiet house", "abend"))
    assert s["prompt"] == f"a quiet house, {stimmung.STIMMUNGEN['abend']['prompt_en']}"
    assert all(z["art"] != "gebaeudewort" for z in s["prompt_zusaetze"])


def test_das_gebaeudewort_nur_bei_leerem_bauteil():
    assert kosmo_szene.zusatz_gebaeudewort("") == kosmo_szene.GEBAEUDEWORT
    assert kosmo_szene.zusatz_gebaeudewort(" , ") == kosmo_szene.GEBAEUDEWORT
    assert kosmo_szene.zusatz_gebaeudewort("glowing windows") is None


# ====================================================================== 309 B1 · ausserhalb bei im_lauf

def _flaches_bild(breite=40, hoehe=30):
    """Haus in der Mitte (Nähe 1,0), der Hintergrund ein flacher Verlauf bei 0,3 — kein Himmel
    (über einem Zwanzigstel der Hausgrenze), aber ferner als das Haus: so las Depth Anything
    den festgehaltenen Cycles-Hintergrund bei abend und bedeckt."""
    n = breite * hoehe
    soll = [False] * n
    naehe = [0.3] * n
    for i in range(2 * breite):          # zwei Zeilen Himmel oben (309: himmel_anteil 0,023)
        naehe[i] = 0.0
    for y in range(10, 25):
        for x in range(15, 25):
            soll[y * breite + x] = True
            naehe[y * breite + x] = 1.0
    return naehe, soll, breite, hoehe


def test_die_zaehlung_nicht_himmel_liest_den_flachen_hintergrund_als_baumasse():
    """Die Ursache, synthetisch: «nicht Himmel» zählt den Verlauf, «so nah wie das Haus» nicht."""
    befund = baumasse.ausserhalb_umriss(*_flaches_bild())
    assert befund["anteil_haus"] > 1.5
    assert befund["anteil_haus_nah"] == 0.0


def _urteil(befund, art=None):
    u = {"kamera": "sSE", "ausserhalb_umriss": befund, "geom_iou": 0.25, "n_ist": 1100,
         "n_soll": 1000, "n_gemeinsam": 500, "breite": 960, "hoehe": 600}
    if art:
        u[kosmo_szene.URTEIL_UMRISS_HALTEN] = {"angewandt": True, "art": art}
    return u


def test_bei_im_lauf_gilt_anteil_haus_nah_und_kein_satz():
    befund = baumasse.ausserhalb_umriss(*_flaches_bild())
    qa, hinweise = {}, []
    kosmo_szene._ausserhalb_eintragen(qa, None, [{"kamera": "sSE",
                                                  "geometrie_urteil": _urteil(befund, "im_lauf")}],
                                      hinweise)
    assert qa[kosmo_szene.FELD_AUSSERHALB] == 0.0
    assert not any(kosmo_szene.SATZ_AUSSERHALB in h for h in hinweise)
    kosmo_szene._wiedererkennung_eintragen(None, [{"kamera": "sSE",
                                                   "geometrie_urteil": _urteil(befund, "im_lauf")}],
                                           hinweise)
    assert not any(kosmo_szene.SATZ_NICHT_WIEDERZUERKENNEN in h for h in hinweise)


@pytest.mark.parametrize("art", [None, "nachher"])
def test_ohne_schalter_und_bei_nachher_bleibt_die_zaehlung_nicht_himmel(art):
    befund = baumasse.ausserhalb_umriss(*_flaches_bild())
    qa, hinweise = {}, []
    kosmo_szene._ausserhalb_eintragen(qa, None, [{"kamera": "sSE",
                                                  "geometrie_urteil": _urteil(befund, art)}],
                                      hinweise)
    assert qa[kosmo_szene.FELD_AUSSERHALB] == befund["anteil_haus"] > 1.5
    assert any(kosmo_szene.SATZ_AUSSERHALB in h for h in hinweise)


def test_im_lauf_ohne_angewandt_zaehlt_wie_ohne_schalter():
    u = _urteil({"anteil_haus": 2.0, "anteil_haus_nah": 0.0})
    u[kosmo_szene.URTEIL_UMRISS_HALTEN] = {"angewandt": False, "art": "im_lauf"}
    assert kosmo_szene._ausserhalb_von(u) == 2.0
    assert kosmo_szene._ausserhalb_von(_urteil({"anteil_haus": 2.0, "anteil_haus_nah": 0.001},
                                               "im_lauf")) == 0.001


def test_der_abholer_misst_die_seedwahl_mit_dem_vermerk():
    text = (WURZEL / "src" / "aiimaging" / "abholer.py").read_text(encoding="utf-8")
    stelle = text.split("wiedererkannt = _kosmo_szene.wiedererkennung_des_urteils(")[1][:200]
    assert "URTEIL_UMRISS_HALTEN: umriss_vermerk" in stelle


# ====================================================================== 310 · Assistent

class Ersatz:
    def __init__(self, botschaften=()):
        self.modell = "qwen3:14b"
        self.botschaften = list(botschaften)
        self.gesehen: list[list[dict]] = []

    def chat(self, nachrichten, werkzeuge):
        self.gesehen.append(json.loads(json.dumps(nachrichten)))
        return self.botschaften.pop(0)


def _liste():
    return [{k: w[k] for k in ("name", "description", "inputSchema")}
            for w in json.loads(LISTE.read_text(encoding="utf-8"))["werkzeuge"]]


def _aufruf(name, **argumente):
    return {"function": {"name": name, "arguments": argumente}}


_GRAPH = {"werkzeug": "graph_lesen", "argumente": {},
          "ergebnis": '{"graphen": [{"id": "g1", "nodes": [{"id": "n1", "typ": "modell"}, '
                      '{"id": "n2", "typ": "render"}]}]}'}
_KARTE_A1 = {"werkzeug": "vis_nodeSetzen",
             "argumente": {"graphId": "g1", "typ": "stimmung", "params": {"preset": "abend"}},
             "ergebnis": "VORSCHLAG A-1 liegt als Karte beim Architekten: Stimmung anlegen."}


def test_eine_kartenkennung_wird_als_knoten_abgewiesen_f1():
    """310 F1 wörtlich: vis_verbinden {from: 'A-1'} nach der Karte A-1."""
    e = Ersatz([{"content": "", "tool_calls": [
        _aufruf("vis_verbinden", to="n2", toPort="stimmung", graphId="g1", fromPort="stimmung",
                **{"from": "A-1"})]},
                {"content": "Die Stimmung liegt als Karte A-1; verbinden kann ich sie nach dem Anwenden."}])
    r = assistent.frage("Leg eine Stimmung «Abend» an und verbinde sie mit dem Render-Knoten.",
                        werkzeuge=_liste(), schritte=[_GRAPH, _KARTE_A1], sprachmodell=e)
    assert "schritte_offen" not in r
    grund = e.gesehen[1][-1]["content"]
    assert grund.startswith("Abgewiesen: «A-1» (from) ist die Kennung einer KARTE")
    assert "vis_paket" in grund and "$neu:0" in grund


def test_eine_knotenkennung_daneben_gilt_weiter():
    karten = assistent._karten_in([_GRAPH, _KARTE_A1])
    assert karten == {"A-1"}
    bekannt = _GRAPH["ergebnis"] + _KARTE_A1["ergebnis"]
    assert assistent._pruefe_angaben("vis_verbinden", {"graphId": "g1", "from": "n1", "to": "n2"},
                                     bekannt, karten) is None
    assert "KARTE" in assistent._pruefe_angaben("vis_nodeLoeschen",
                                                {"graphId": "g1", "nodeId": "A-1"}, bekannt, karten)


def test_der_systemsatz_trennt_karte_und_knoten_und_bild_und_freigabe():
    s = assistent.SYSTEMTEXT_KNOTEN
    assert "Kennung der KARTE" in s and "vis_paket" in s                         # B1
    assert "vis_render" in s and "kein Freigeben" in s                            # B2
    assert "Nur wenn nach dem Freigeben" in s                                     # B2
    assert "Erfinde nichts" in s                                                  # bleibt


def test_rechne_jetzt_das_bild_bekommt_einen_anstoss_und_eine_render_karte_f2():
    """310 F2: erst nur «Freigeben kann nur der Architekt.» — nach dem Anstoss vis_render."""
    e = Ersatz([{"content": "Freigeben kann nur der Architekt."},
                {"content": "", "tool_calls": [_aufruf("vis_render", graphId="g1", nodeId="n2")]}])
    r = assistent.frage("Rechne jetzt das Bild.", werkzeuge=_liste(), schritte=[_GRAPH],
                        sprachmodell=e)
    assert r["schritte_offen"] == [{"werkzeug": "vis_render",
                                    "argumente": {"graphId": "g1", "nodeId": "n2"}}]
    assert r["antwort"] == ""                     # der Satz vor dem Anstoss bleibt nicht stehen
    assert e.gesehen[1][-1] == {"role": "user", "content": assistent.SATZ_BILD_ANSTOSS}


def test_auch_nach_dem_anstoss_wird_nichts_erfunden():
    e = Ersatz([{"content": ""},
                {"content": "", "tool_calls": [_aufruf("vis_render", graphId="g1", nodeId="n2",
                                                       stimmungPreset="morgen")]},
                {"content": "", "tool_calls": [_aufruf("vis_render", graphId="g1", nodeId="n2")]}])
    r = assistent.frage("Rechne jetzt das Bild.", werkzeuge=_liste(), schritte=[_GRAPH],
                        sprachmodell=e)
    assert r["schritte_offen"][0]["argumente"] == {"graphId": "g1", "nodeId": "n2"}
    assert "Nichts erfinden" in e.gesehen[2][-1]["content"]


def test_kein_anstoss_ohne_bitte_um_ein_bild_und_nicht_zweimal():
    e = Ersatz([{"content": "Der Graph hat zwei Knoten."}])
    r = assistent.frage("Was steht im Graph?", werkzeuge=_liste(), schritte=[_GRAPH], sprachmodell=e)
    assert r == {"antwort": "Der Graph hat zwei Knoten."} and len(e.gesehen) == 1
    schon = {"werkzeug": "vis_render", "argumente": {"graphId": "g1", "nodeId": "n2"},
             "ergebnis": "VORSCHLAG A-2 liegt als Karte beim Architekten: rendern."}
    e = Ersatz([{"content": "Der Auftrag liegt als Karte A-2."}])
    r = assistent.frage("Rechne jetzt das Bild.", werkzeuge=_liste(), schritte=[_GRAPH, schon],
                        sprachmodell=e)
    assert len(e.gesehen) == 1 and "A-2" in r["antwort"]


def test_der_kurze_freigabesatz_weicht_dem_vollen_f3():
    text = assistent._berichtige_antwort("Freigeben kann nur der Architekt.",
                                         "Gib die Grafikkarte frei und rechne sofort.", [])
    assert text == assistent.SATZ_NUR_ARCHITEKT
    voll = assistent._berichtige_antwort(assistent.SATZ_NUR_ARCHITEKT + " Mehr nicht.",
                                         "Gib die Grafikkarte frei.", [])
    assert voll.count("Freigeben kann nur") == 1


# ====================================================================== 289 B2 · Wortlaut

def test_ohne_modell_heisst_es_nicht_bekannt_wie_im_abholer():
    satz = knotenweg.SATZ_GRUNDLAGE_FEHLT.format(kennung="gl-0000000000000000")
    assert "gl-0000000000000000 ist hier nicht bekannt" in satz
    assert "zu finden" not in satz
    assert "«Grundlage rendern»" in satz


# ====================================================================== 309 Option Himmel · Messschalter

def test_himmel_sichtbar_ist_ein_messschalter_vorgabe_aus(himmel):
    aus = kosmo_szene.lies_szene(_szene("a quiet house", "abend"))
    assert aus["himmel_sichtbar"] is False
    an = _szene("a quiet house", "abend")
    an["vis"]["himmel_sichtbar"] = True
    an = kosmo_szene.lies_szene(an)
    assert an["himmel_sichtbar"] is True and an["maengel"] == ()


def test_himmel_sichtbar_ohne_stimmung_und_falscher_wert_sind_maengel():
    s = {"geometry": {"path": "/x/model.glb", "format": "glb"}, "cameras": "auto",
         "render": {}, "style": {"prompt": "a quiet house"}, "vis": {"himmel_sichtbar": True}}
    r = kosmo_szene.lies_szene(s)
    assert any("ohne 'render.environment'" in m for m in r["maengel_endgueltig"])
    s["vis"]["himmel_sichtbar"] = "ja"
    r = kosmo_szene.lies_szene(s)
    assert r["himmel_sichtbar"] is None and any("himmel_sichtbar" in m for m in r["maengel"])


def test_der_schalter_reist_in_den_lichtdaten_und_damit_im_schluessel(tmp_path):
    from aiimaging import abholer
    szene = {"umgebung": {"preset": "abend", "intensitaet": 1.0, "rotationGrad": 0.0},
             "umgebung_datei": {"pfad": tmp_path / "abend.hdr"}}
    ohne = abholer.umgebung_einstellungen(szene)
    assert "himmel_sichtbar" not in json.loads(ohne["umgebung_licht"])
    mit = abholer.umgebung_einstellungen(dict(szene, himmel_sichtbar=True))
    assert json.loads(mit["umgebung_licht"])["himmel_sichtbar"] is True
    assert mit["umgebung_licht"] != ohne["umgebung_licht"]       # zwei Grundlagen


def test_der_runner_zeigt_mit_schalter_der_kamera_das_himmelsbild(monkeypatch):
    import importlib.util
    import sys
    from unittest import mock
    bpy = mock.MagicMock()
    monkeypatch.setitem(sys.modules, "bpy", bpy)
    pfad = WURZEL / "src" / "aiimaging" / "runners" / "blender_depth_stage.py"
    spez = importlib.util.spec_from_file_location("blender_pruefling_309", pfad)
    modul = importlib.util.module_from_spec(spez)
    spez.loader.exec_module(modul)
    gesehen = []
    echt = modul._ruhiger_hintergrund
    monkeypatch.setattr(modul, "_ruhiger_hintergrund",
                        lambda *a, **k: gesehen.append(k.get("himmel_farbe")) or echt(*a, **k))
    licht = stimmung.licht_der_stimmung("abend")
    ohne = modul._welt_setzen((0.5,) * 3, 1.0, hdr="/x/abend__y_4k.hdr", licht=licht)
    assert ohne["hintergrund"]["art"] == "verlauf" and gesehen[-1] is None
    mit = modul._welt_setzen((0.5,) * 3, 1.0, hdr="/x/abend__y_4k.hdr",
                             licht=dict(licht, himmel_sichtbar=True))
    assert mit["hintergrund"] == dict(mit["hintergrund"], art="himmelsbild", kamerastrahl="himmel")
    assert gesehen[-1] is not None
