"""Mac-Probe 0.3.66 (25.10.2026, Mappe mit einem Haus am Hang, Claude über MCP in «Voll»): der Weg ``vis_varianten``.

Drei rote Funde und ein vierter aus derselben Ursache (Protokoll 74 §293):

1. **Die Variante ohne eigene Stärke rechnete mit 0,5 statt 0,7.** Der Kern erkannte eine Variante nur an
   ``vis.grundlage``; der Varianten-Knoten schickt sie nur, wenn am Render-Knoten die Grundlage genau dieses Stands
   liegt. Jetzt sagt die Bestellung es selbst (``vis.variante: true``, KosmoVis-Zweig ``claude/kosmovis-macweg``).
2. **``standpunkte: ["sSE"]`` fiel still weg** — jetzt kommt ``cameras_auto.richtungen: ["sSE"]``; liegt eine
   Grundlage des Render-Knotens ohne ``cameras_auto`` vor, passt die Richtung als Teil ihrer gerechneten Kameras.
3. **``freies_bild`` ohne Beschreibung im Katalog** — der Katalog kommt aus der Knotenansicht (Kernbefehle); die
   Spielregel der Mac-App nennt es (Probe unten, Text, weil Swift hier nicht gebaut wird).
4. **``vis_grundlage`` rechnete Blender noch einmal**, obwohl die Variante eben eine Grundlage desselben Stands
   gerechnet hatte — die Grundlage eines Laufs des Varianten-Knotens fiel weg (KosmoVis, Probe dort).

Ohne GPU, alles synthetisch (Regel 3).
"""
from __future__ import annotations

import json
from pathlib import Path

from aiimaging import abholer, bruecke, kosmo_szene

from test_bildeingang_vorgabe_e138 import _auftragsordner, _kette, _lauf, _lauf_mit, _mit_bildeingang_meldung
from test_varianten_vorgabe_e126 import _szene, himmel  # noqa: F401 — Fixture

GL = "gl-5e1d0c3b2a491807"
WURZEL = Path(__file__).resolve().parents[1]


def _lies(**kw):
    roh = _szene(**kw.pop("vis", {}))
    roh.update(kw)
    return kosmo_szene.lies_szene(roh, streng=False)


# ================================================================ (1) die Variante als Variante

def test_variante_ohne_grundlage_rechnet_mit_07(himmel):  # noqa: F811
    s = _lies(vis={"variante": True, "guete": "voll"})
    assert not any("variante" in m or "bildeingang" in m for m in s["maengel"])
    assert s["ist_variante"] is True
    assert s["bildeingang"] == 0.7 == kosmo_szene.BILDEINGANG_VORGABE_VARIANTE
    assert s["messschalter"]["bildeingang"] == {"herkunft": "vorgabe"}


def test_ohne_marke_bleibt_das_erste_bild_bei_05(himmel):  # noqa: F811
    s = _lies(vis={"guete": "voll"})
    assert s["ist_variante"] is False and s["bildeingang"] == 0.5
    s = _lies(vis={"variante": False})
    assert s["ist_variante"] is False and s["bildeingang"] == 0.5


def test_eigene_staerke_und_freies_bild_gewinnen_auch_mit_marke(himmel):  # noqa: F811
    s = _lies(vis={"variante": True, "bildeingang": 0.5})
    assert s["bildeingang"] == 0.5 and s["messschalter"]["bildeingang"] == {"herkunft": "bestellt"}
    s = _lies(vis={"variante": True, "freies_bild": True})
    assert s["bildeingang"] is None and s["freies_bild"] is True


def test_falscher_wert_ist_ein_mangel(himmel):  # noqa: F811
    s = _lies(vis={"variante": "ja"})
    assert any("'vis.variante'" in m for m in s["maengel"])


def test_marke_mit_nur_grundlage_ist_ohne_wirkung_und_ohne_mangel(himmel):  # noqa: F811
    s = _lies(vis={"variante": True, "skip": True})
    assert not any("variante" in m for m in s["maengel"])
    assert s["bildeingang"] is None


def test_lauf_mit_marke_rechnet_07_und_sagt_vorgabe_fuer_varianten(tmp_path):
    """Durch den ganzen Abholer: die Bestellung, wie der Varianten-Knoten sie ohne Grundlage schickt."""
    antwort, protokoll = _lauf_mit(tmp_path, variante=True)
    assert protokoll["render"] and all(a.bildeingang_staerke == 0.7 for a in protokoll["render"])
    angewandt = antwort["ergebnis"]["angewandt"]
    assert angewandt["messschalter"]["bildeingang"] == {"wert": 0.7, "herkunft": "vorgabe"}
    hinweise = antwort["ergebnis"]["qa"]["verdict"].get("hinweise", [])
    assert any(h.startswith(kosmo_szene.SATZ_BILDEINGANG)
               and h.endswith("Vorgabe fuer Varianten (herkunft vorgabe, Entscheid 149).")
               for h in hinweise), hinweise


# ================================================================ (2) nur die bestellte Richtung

def test_cameras_auto_mit_einer_richtung_wird_eine_aufgabe(tmp_path):
    ordner = _auftragsordner(tmp_path / "a")
    pfad = ordner / bruecke.DATEI_SZENE
    szene = json.loads(pfad.read_text(encoding="utf-8"))
    szene["cameras"] = "auto"
    szene["cameras_auto"] = {"richtungen": ["sSE"]}
    szene["vis"].update({"variante": True})
    pfad.write_text(json.dumps(szene), encoding="utf-8")
    protokoll, attrappen = _kette(tmp_path / "k")
    antwort = _lauf(tmp_path / "l", ordner, _mit_bildeingang_meldung(attrappen))
    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort["grund"]
    assert len(protokoll["render"]) == 1
    assert all(a.bildeingang_staerke == 0.7 for a in protokoll["render"])
    assert antwort["ergebnis"]["angewandt"]["cameras_auto"]["richtungen"] == ["sSE"]


def _gelesen_auto(richtungen):
    s = _lies(cameras_auto={"richtungen": richtungen}, vis={"variante": True})
    assert not s["maengel"], s["maengel"]
    return s


def test_teil_der_richtungen_einer_grundlage_ohne_cameras_auto_passt(himmel):  # noqa: F811
    grundlage = {f: abholer._vergleichbar(_lies().get(f)) for f in abholer.GRUNDLAGE_MUSS_PASSEN}
    assert grundlage["kameras_auto"] is None
    auftrag = _gelesen_auto(["sSE"])
    assert abholer.kameras_weichen_ab(grundlage, auftrag, ["s", "sSE", "nNW", "e"]) == []
    # Eine Richtung, die die Grundlage nicht hat, passt nicht; ohne Wissen um ihre Kameras auch nicht.
    assert abholer.kameras_weichen_ab(grundlage, _gelesen_auto(["w"]), ["s", "sSE", "nNW"]) == ["kameras_auto"]
    assert abholer.kameras_weichen_ab(grundlage, auftrag) == ["kameras_auto"]
    # Eigene Werte (nicht die Vorgabe) sind ein anderer Standpunkt.
    s = _lies(cameras_auto={"richtungen": ["sSE"], "brennweite_mm": 24}, vis={"variante": True})
    assert abholer.kameras_weichen_ab(grundlage, s, ["sSE"]) == ["kameras_auto"]


def test_lies_grundlage_nimmt_die_eine_richtung(tmp_path, himmel):  # noqa: F811
    roh = _lies()
    beauty = tmp_path / "b.png"
    tiefe = tmp_path / "t.png"
    beauty.write_bytes(b"x")
    tiefe.write_bytes(b"x")
    bericht = {"beauty_png": str(beauty), "depth_png": str(tiefe)}
    abholer.lege_grundlage_ab(tmp_path, GL, job_id="vis-1-a", szene=roh,
                              berichte={k: bericht for k in ("s", "sSE", "nNW", "e")})
    satz = abholer.lies_grundlage(tmp_path, GL, _gelesen_auto(["sSE"]))
    assert satz["id"] == GL


# ================================================================ (3) der Katalog

def test_die_spielregel_der_mac_app_nennt_freies_bild_und_die_knotenansicht_beschreibt_es():
    """Den Katalog (``tools/list``) liefert die Knotenansicht aus den Kernbefehlen; Swift reicht ihn durch.

    Dort trägt ``freies_bild`` jetzt seine Zeile (``FREIES_BILD_SATZ``) und ``standpunkte`` die Richtungen — die
    Probe in der Kopie (``kv-macweg-varianten.test.ts``) liest das Schema; hier der Text der Quelle und der Bau.
    """
    vis = (WURZEL / "kosmovis/packages/kosmo-kernel/src/commands/vis.ts").read_text(encoding="utf-8")
    assert "ohne Grundbild — für ein Stimmungsbild; das Haus kann vom Modell abweichen; nicht zusammen mit einer Stärke" in vis
    assert vis.count("freies_bild: z.boolean().optional().describe(FREIES_BILD_SATZ)") == 2
    assert "standpunkte: z.array(z.string()).optional().describe(STANDPUNKTE_SATZ)" in vis
    bau = "".join(p.read_text(encoding="utf-8") for p in
                  (WURZEL / "kosmovis/apps/visbox-knoten/dist/assets").glob("index-*.js"))
    assert "das Haus kann vom Modell abweichen" in bau
    swift = (WURZEL / "ipad/Visbox.swiftpm/Kern/Mcpkern.swift").read_text(encoding="utf-8")
    assert "freies_bild: true an vis_render oder vis_varianten" in swift


def test_der_gebaute_katalog_listet_freies_bild_mit_beschreibung():
    """Die Liste, die die Mac-App Claude als ``tools/list`` gibt (Bau der Knotenansicht)."""
    liste = json.loads((WURZEL / "kosmovis/apps/visbox-knoten/dist/ki-werkzeugliste.json").read_text(encoding="utf-8"))
    werkzeuge = {w["name"]: w for w in (liste if isinstance(liste, list) else liste["werkzeuge"])}
    for name in ("vis_render", "vis_varianten"):
        feld = werkzeuge[name]["inputSchema"]["properties"]["freies_bild"]
        assert feld["type"] == "boolean"
        assert feld["description"].startswith("ohne Grundbild — für ein Stimmungsbild")
    assert "Richtungen" in werkzeuge["vis_varianten"]["inputSchema"]["properties"]["standpunkte"]["description"]


def test_die_bruecke_nimmt_eine_richtung_der_grundlage_an_eine_fremde_nicht(tmp_path):
    """``knotenweg.lege_an``: eine Variante mit ``cameras_auto {richtungen: [sSE]}`` auf einer Grundlage ohne
    ``cameras_auto`` (Richtungen des Abholers) ist kein 409 mehr; eine Richtung ausserhalb bleibt 409."""
    import pytest
    from aiimaging import knotenweg
    from test_heimfehler_auf292 import _grundlage_auftrag
    kennung = "gl-00112233445566bb"
    _grundlage_auftrag(tmp_path, kennung, {})
    angelegt = knotenweg.lege_an(tmp_path, {"cameras_auto": {"richtungen": ["sSE"]},
                                            "vis": {"grundlage": kennung, "variante": True}},
                                 b"glTF", "m.glb", kennung="vis-1792926323-a00001")
    assert angelegt["job_id"]
    with pytest.raises(knotenweg.KnotenwegError) as fehler:
        knotenweg.lege_an(tmp_path, {"cameras_auto": {"richtungen": ["n"]},
                                     "vis": {"grundlage": kennung, "variante": True}},
                          b"glTF", "m.glb", kennung="vis-1792926323-a00002")
    assert fehler.value.code == 409
