"""Boden bis zum Horizont — und zwei Berichtslücken aus ``auf-20261022-334``.

**Hauptbefund (demo-relevant):** Mit sichtbarem Himmel sah die Kamera unter dem Horizont,
ausserhalb der Geländeplatte, die untere Hälfte des Himmelsbilds (spiegelnd blau bzw.
grau) — kein Boden bis zum Horizont. Ursache: Der Kamerastrahl der Welt bekam das
Himmelsbild in **jede** Richtung (``_ruhiger_hintergrund`` mit ``himmel_farbe``), und die
Himmelsbilder der Stimmungen sind «puresky»-Aufnahmen ohne Erde. Jetzt: unter dem Horizont
eine Bodenfarbe aus Plattengrau und mittlerem Himmel, nur für Kamerastrahlen.

Dazu: (2) ``bbox_bauwerk_entschieden_durch`` sagt im Blender-Weg «name», wenn die
Namensregel getrennt hat (334: «keine» trotz Rahmung 0,509 enger); (3) der Kontrast steht
zusätzlich am KI-Bild (``qa.kontrast_haus_hintergrund_ki``), ohne neue Warnung.

Ohne GPU und ohne Blender: reine Funktionen, der Runner mit Attrappen (Regel 2), der
Knotenbaum mit einer kleinen Nachbildung, die ihn für eine Blickrichtung AUSWERTET (Regel 3:
alles synthetisch).
"""
from __future__ import annotations

import json
import math
from types import SimpleNamespace

import pytest

from aiimaging import abholer, bildschreiben, kosmo_szene, stimmung

from test_heimfehler_auf292 import _runner
from test_rahmung_vor_render import _mesh, _runner_mit_objekten

# ============================================================ 1 · die Bodenfarbe, reine Rechnung


def test_der_boden_ist_plattengrau_unter_dem_mittleren_himmel():
    aus = stimmung.boden_bis_horizont([0.4, 0.5, 0.6], [0.2, 0.3, 0.8], albedo=[0.3] * 3,
                                      toenung=[1.0, 0.9, 0.8])
    assert aus["boden"] == [pytest.approx(0.3 * 0.3), pytest.approx(0.3 * 0.4 * 0.9),
                            pytest.approx(0.3 * 0.7 * 0.8)]
    assert aus["dunst"] == [pytest.approx(0.4), pytest.approx(0.45), pytest.approx(0.48)]
    assert aus["dunst_grad"] == stimmung.BODEN_DUNST_GRAD == 6.0
    # Ohne Albedo das Grau der Platte, ohne Toenung keine.
    ohne = stimmung.boden_bis_horizont([1.0] * 3, [1.0] * 3)
    assert ohne["boden"] == list(stimmung.GELAENDE_GRAU)
    assert ohne["dunst"] == [1.0] * 3
    # Der Boden ist dunkler als der Himmel ueber ihm — er liest sich als Boden.
    assert all(b < d for b, d in zip(aus["boden"], aus["dunst"]))


# ============================================================ der Weg bis Blender

def _szene(tmp_path, preset):
    return {"umgebung": {"preset": preset, "intensitaet": 1.0, "rotationGrad": 0.0},
            "umgebung_datei": {"pfad": tmp_path / f"{preset}.hdr"}}


def test_das_lichtdatum_reist_nur_mit_himmel_sichtbar(tmp_path):
    """Neue Lichtdaten = neue Grundlage und neuer Schluessel: ein Bild mit gespiegeltem
    Himmel wird nicht wiederverwendet. Ohne Schalter bleibt der Text Wort fuer Wort."""
    for preset in ("mittag", "abend"):
        ohne = abholer.umgebung_einstellungen(_szene(tmp_path, preset))["umgebung_licht"]
        assert "boden_bis_horizont" not in json.loads(ohne)
        mit = json.loads(abholer.umgebung_einstellungen(
            dict(_szene(tmp_path, preset), himmel_sichtbar=True))["umgebung_licht"])
        assert mit["boden_bis_horizont"] is True and mit["himmel_sichtbar"] is True


# ============================================================ der Knotenbaum, ausgewertet

class _Sockel:
    def __init__(self, knoten, name, typ="VALUE", wert=0.0):
        self.knoten, self.name, self.type, self.default_value = knoten, name, typ, wert


class _SockelListe(dict):
    """Sockel nach Name und nach Stelle — wie Blender (``inputs["Value"]``, ``inputs[0]``)."""

    def __init__(self, knoten, namen):
        super().__init__()
        self._reihe = []
        for name, typ in namen:
            s = _Sockel(knoten, name, typ)
            self[name] = s
            self._reihe.append(s)

    def __getitem__(self, schluessel):
        if isinstance(schluessel, int):
            return self._reihe[schluessel]
        if schluessel not in self:
            s = _Sockel(None, schluessel)
            dict.__setitem__(self, schluessel, s)
            self._reihe.append(s)
        return dict.__getitem__(self, schluessel)

    def __iter__(self):
        return iter(self._reihe)


#: Die Sockel der Knotenarten, die der Kamerastrahl braucht.
_SOCKEL = {
    "ShaderNodeTexCoord": ([], [("Generated", "VECTOR")]),
    "ShaderNodeSeparateXYZ": ([("Vector", "VECTOR")], [("X", "VALUE"), ("Y", "VALUE"),
                                                       ("Z", "VALUE")]),
    "ShaderNodeMapRange": ([("Value", "VALUE"), ("From Min", "VALUE"), ("From Max", "VALUE"),
                            ("To Min", "VALUE"), ("To Max", "VALUE")], [("Result", "VALUE")]),
    "ShaderNodeMath": ([("A", "VALUE"), ("B", "VALUE")], [("Value", "VALUE")]),
    "ShaderNodeMixRGB": ([("Fac", "VALUE"), ("Color1", "RGBA"), ("Color2", "RGBA")],
                         [("Color", "RGBA")]),
    "ShaderNodeBackground": ([("Color", "RGBA"), ("Strength", "VALUE")],
                             [("Background", "SHADER")]),
    "ShaderNodeLightPath": ([], [("Is Camera Ray", "VALUE")]),
    "ShaderNodeMixShader": ([("Fac", "VALUE"), ("Shader1", "SHADER"), ("Shader2", "SHADER")],
                            [("Shader", "SHADER")]),
    "ShaderNodeOutputWorld": ([("Surface", "SHADER")], []),
    "Himmel": ([], [("Color", "RGBA")]),
}


class _Knoten:
    def __init__(self, art):
        if art == "ShaderNodeMix":
            # Wie Blender vor 3.4: `_mix_farbe` faellt auf MixRGB zurueck.
            raise RuntimeError("ShaderNodeMix gibt es in dieser Nachbildung nicht")
        self.art, self.name, self.operation, self.clamp = art, art, "", False
        self.type = "OUTPUT_WORLD" if art == "ShaderNodeOutputWorld" else art
        rein, raus = _SOCKEL[art]
        self.inputs = _SockelListe(self, rein)
        self.outputs = _SockelListe(self, raus)


class _Knotenliste(list):
    def __init__(self, neu):
        super().__init__()
        self.new = neu


class _Baum:
    def __init__(self):
        self.verbindungen = {}
        self.knoten = self.nodes = _Knotenliste(self._neu)

    def _neu(self, art):
        k = _Knoten(art)
        self.knoten.append(k)
        return k

    @property
    def links(self):
        return SimpleNamespace(new=lambda von, nach: self.verbindungen.__setitem__(id(nach),
                                                                                  von))

    def wert(self, sockel, z, himmel):
        """Den Wert eines Ausgangs fuer die Blickrichtung (0, 0, z) auswerten."""
        k = sockel.knoten
        rein = (lambda name: self.wert(self.verbindungen[id(k.inputs[name])], z, himmel)
                if id(k.inputs[name]) in self.verbindungen
                else k.inputs[name].default_value)
        if k.art == "Himmel":
            return tuple(himmel)
        if k.art == "ShaderNodeTexCoord":
            return (0.0, 0.0, z)
        if k.art == "ShaderNodeSeparateXYZ":
            return rein("Vector")["XYZ".index(sockel.name)]
        if k.art == "ShaderNodeMapRange":
            t = (rein("Value") - rein("From Min")) / (rein("From Max") - rein("From Min"))
            t = min(1.0, max(0.0, t)) if k.clamp else t
            return rein("To Min") + t * (rein("To Max") - rein("To Min"))
        if k.art == "ShaderNodeMath":
            assert k.operation == "GREATER_THAN"
            return 1.0 if rein("A") > rein("B") else 0.0
        if k.art == "ShaderNodeMixRGB":
            f, a, b = rein("Fac"), rein("Color1"), rein("Color2")
            return tuple((1 - f) * x + f * y for x, y in zip(a[:3], b[:3]))
        raise AssertionError(f"nicht nachgebildet: {k.art}")


def _kamerastrahl():
    """Die Nachbildung mit Himmelsquelle und Licht-Ausgang; gibt (Baum, Welt, Quelle, Licht)."""
    baum = _Baum()
    welt = SimpleNamespace(node_tree=baum)
    quelle = baum._neu("Himmel")
    licht = baum._neu("ShaderNodeBackground")
    return baum, welt, quelle, licht


def _bauen(monkeypatch, boden, *, himmel=True):
    modul, _bpy = _runner(monkeypatch)
    baum, welt, quelle, licht = _kamerastrahl()
    farben = {"horizont": [0.5, 0.5, 0.5], "zenit": [0.3, 0.3, 0.3]}
    modul._ruhiger_hintergrund(welt, licht.outputs["Background"], 0.7, farben, None,
                               himmel_farbe=quelle.outputs["Color"] if himmel else None,
                               boden=boden)
    grund = next(k for k in baum.knoten if k.name == modul.RUHIGER_GRUND)
    return modul, baum, grund, licht


BODEN = stimmung.boden_bis_horizont([0.5, 0.6, 0.7], [0.3, 0.4, 0.9], albedo=[0.3] * 3)
HIMMEL = (0.2, 0.4, 0.9)


def _farbe(baum, grund, z):
    return baum.wert(baum.verbindungen[id(grund.inputs["Color"])], z, HIMMEL)


def test_ueber_dem_horizont_himmel_darunter_boden(monkeypatch):
    """Der Kern des Fixes, an der Nachbildung AUSGEWERTET — nicht nur gezaehlt."""
    _, baum, grund, _ = _bauen(monkeypatch, BODEN)
    assert _farbe(baum, grund, 0.5) == pytest.approx(HIMMEL)
    assert _farbe(baum, grund, 0.001) == pytest.approx(HIMMEL), "bis an den Horizont Himmel"
    assert _farbe(baum, grund, -0.5) == pytest.approx(BODEN["boden"]), "tief unten Boden"
    assert _farbe(baum, grund, -1.0) == pytest.approx(BODEN["boden"])
    # Direkt unter dem Horizont der Dunst (Horizontfarbe), weich zum Boden hin.
    knapp = _farbe(baum, grund, -1e-6)
    assert knapp == pytest.approx(BODEN["dunst"], abs=1e-4)
    halb = _farbe(baum, grund, -math.sin(math.radians(BODEN["dunst_grad"])) / 2)
    for h, b, d in zip(halb, BODEN["boden"], BODEN["dunst"]):
        assert min(b, d) < h < max(b, d)
    assert grund.inputs["Strength"].default_value == 0.7, "die Vorprobe stellt beide gleich"


def test_das_licht_bleibt_beim_himmelsbild(monkeypatch):
    """Nur der Kamerastrahl sieht den Boden: Is Camera Ray waehlt, das Licht (Eingang 1)
    bleibt der Ausgang des Himmelsbilds, unveraendert."""
    _, baum, grund, licht = _bauen(monkeypatch, BODEN)
    mischung = next(k for k in baum.knoten if k.art == "ShaderNodeMixShader")
    assert baum.verbindungen[id(mischung.inputs[0])].name == "Is Camera Ray"
    assert baum.verbindungen[id(mischung.inputs[1])] is licht.outputs["Background"]
    assert baum.verbindungen[id(mischung.inputs[2])] is grund.outputs["Background"]


def test_ohne_boden_bleibt_der_kamerastrahl_das_himmelsbild(monkeypatch):
    """Ohne Lichtdatum Wort fuer Wort wie vor 334 — auch unter dem Horizont Himmelsbild."""
    _, baum, grund, _ = _bauen(monkeypatch, None)
    assert not any(k.art == "ShaderNodeMath" for k in baum.knoten)
    assert _farbe(baum, grund, -0.5) == pytest.approx(HIMMEL)


def test_der_verlauf_bekommt_keinen_boden(monkeypatch):
    """Ohne sichtbaren Himmel (Verlauf) aendert sich nichts, auch mit Boden-Angabe."""
    _, baum, grund, _ = _bauen(monkeypatch, BODEN, himmel=False)
    assert not any(k.art == "ShaderNodeMath" for k in baum.knoten)
    assert _farbe(baum, grund, -0.5) == pytest.approx([0.5] * 3), "Verlauf: Horizontfarbe"


def test_welt_setzen_nimmt_den_boden_nur_mit_beiden_angaben(monkeypatch):
    modul, _ = _runner(monkeypatch)
    gesehen = []
    echt = modul._ruhiger_hintergrund
    monkeypatch.setattr(modul, "_ruhiger_hintergrund",
                        lambda *a, **k: gesehen.append(k.get("boden")) or echt(*a, **k))
    licht = stimmung.licht_der_stimmung("mittag")
    faelle = ((dict(licht, himmel_sichtbar=True, boden_bis_horizont=True), True),
              (dict(licht, himmel_sichtbar=True), False),
              (dict(licht, boden_bis_horizont=True), False),
              (licht, False))
    for daten, erwartet in faelle:
        befund = modul._welt_setzen((0.5,) * 3, 1.0, hdr="/x/mittag__y_4k.hdr", licht=daten)
        assert (gesehen[-1] is not None) is erwartet
        assert ("boden" in befund["hintergrund"]) is erwartet
    # Der Bericht traegt die Bodenfarbe aus dem Plattengrau (Rueckfallfarben der Attrappe).
    boden = modul._welt_setzen((0.5,) * 3, 1.0, hdr="/x/mittag__y_4k.hdr",
                               licht=faelle[0][0])["hintergrund"]["boden"]
    assert boden["albedo"] == list(stimmung.GELAENDE_GRAU)


def test_der_id_pass_bleibt_schwarz():
    """Der ID-Pass ruft `_welt_setzen` ohne Himmelsbild — kein Boden, kein Kamerastrahl."""
    from test_heimfehler_auf292 import RUNNER
    quelle = RUNNER.read_text(encoding="utf-8")
    assert "_welt_setzen((0.0, 0.0, 0.0), 0.0)" in quelle
    welt = quelle[quelle.index("def _welt_setzen"):]
    welt = welt[:welt.index("\ndef ")]
    assert welt.index("if not hdr:") < welt.index("_boden_der_welt(")


# ============================================================ 2 · entschieden durch «name»

def test_die_namensregel_entscheidet_und_der_bericht_sagt_name(monkeypatch):
    """334: Gelaende der KosmoDraw-glb an «gelaendeflaeche» getrennt, Rahmung 0,509 enger —
    der Bericht sagte «keine». Jetzt «name» mit den Namen, wie `glbbox.bauwerksbox`."""
    modul = _runner_mit_objekten(monkeypatch, [
        _mesh("gelaendeflaeche gewachsen [njjq9m]", (-30, -30, -2.0), (30, 30, 0.0)),
        _mesh("Wand_Nord", (0, 0, 0), (8, 5, 7)),
    ])
    lo, hi, note, schrumpfung, form = modul._bbox_bauwerk()
    assert (lo, hi, note) == ([0, 0, 0], [8, 5, 7], "")
    assert schrumpfung > 0.5
    assert form == {"entschieden_durch": "name",
                    "gelaende_namen": ("gelaendeflaeche gewachsen [njjq9m]",)}


def test_ohne_gelaende_bleibt_es_keine(monkeypatch):
    modul = _runner_mit_objekten(monkeypatch, [_mesh("Wand_Nord", (0, 0, 0), (8, 5, 7)),
                                               _mesh("Dach", (0, 0, 7), (8, 5, 9))])
    *_, form = modul._bbox_bauwerk()
    assert form == modul.LEERER_FORMBEFUND


def test_name_traegt_keine_namen_an_die_maske_weiter():
    """Der Abholer uebertraegt nur bei «form» — die Maske findet Namen der Wortliste selbst."""
    bericht = {"bbox_bauwerk_entschieden_durch": "name",
               "bbox_bauwerk_gelaende_namen": ["gelaendeflaeche"],
               "bbox_bauwerk_gelaende_materialien": []}
    assert abholer._formgelaende_aus_bericht(bericht) == ()


def test_die_materialliste_bleibt_der_form_vorbehalten():
    from test_heimfehler_auf292 import RUNNER
    quelle = RUNNER.read_text(encoding="utf-8")
    assert ('if bau_form["entschieden_durch"] == "form" else []' in quelle)


# ============================================================ 3 · Kontrast am KI-Bild

def _png(pfad, b, h, farbe_von):
    bildschreiben.schreibe_farb_png(pfad, [farbe_von(x, y) for y in range(h)
                                           for x in range(b)], b, h)
    return str(pfad)


def test_der_kontrast_am_ki_bild_steht_daneben(tmp_path):
    """Cycles: Haus dunkler als der Himmel; KI: Haus heller — beide Zahlen, eine Maske."""
    b, h = 20, 10
    haus = [(5 <= x < 15 and y >= 4) for y in range(h) for x in range(b)]
    id_png = _png(tmp_path / "id.png", b, h,
                  lambda x, y: (200, 10, 10) if (5 <= x < 15 and y >= 4) else (0, 0, 0))
    cycles = _png(tmp_path / "cycles.png", b, h,
                  lambda x, y: (60, 60, 60) if (5 <= x < 15 and y >= 4) else (120, 120, 120))
    ki = _png(tmp_path / "ki.png", b, h,
              lambda x, y: (200, 200, 200) if (5 <= x < 15 and y >= 4) else (120, 120, 120))
    szene = {"umgebung": {"preset": "mittag"}}
    bericht = {"beauty_png": cycles, "material_id_png": id_png}
    am_cycles = abholer._stimmungsmessung(szene, bericht, haus)["kontrast"]["kontrast"]
    am_ki = abholer._kontrast_am_ki_bild(szene, bericht, ki, haus)
    assert am_cycles == pytest.approx(-60.0) and am_ki["kontrast"] == pytest.approx(80.0)
    # Ohne Stimmung nichts, wie beim Cycles-Wert.
    assert abholer._kontrast_am_ki_bild({}, bericht, ki, haus) is None
    # Ein KI-Bild anderer Groesse: nicht gemessen, mit Grund — keine Ausnahme.
    schief = _png(tmp_path / "schief.png", 10, 10, lambda x, y: (1, 1, 1))
    befund = abholer._kontrast_am_ki_bild(szene, bericht, schief, haus)
    assert befund["kontrast"] is None and befund["grund"]


def _eintrag(kamera, cycles, ki):
    urteil = {"kamera": kamera, "kontrast": {"kontrast": cycles}}
    if ki is not None:
        urteil[kosmo_szene.URTEIL_KONTRAST_KI] = {"kontrast": ki}
    return {"kamera": kamera, "geometrie_urteil": urteil}


def test_qa_traegt_den_ki_kontrast_ohne_neue_warnung():
    je_kamera = [_eintrag("sSE", -27.7, 37.1), _eintrag("nNW", 45.0, -12.0)]
    qa, hinweise = {}, []
    kosmo_szene._kontrast_eintragen(qa, None, je_kamera, hinweise)
    kosmo_szene._kontrast_ki_eintragen(qa, None, je_kamera)
    assert qa[kosmo_szene.FELD_KONTRAST] == -27.7
    assert qa[kosmo_szene.FELD_KONTRAST_KI] == -12.0, "der kleinste Betrag, wie am Cycles-Bild"
    assert hinweise == [], "|-12| liegt unter 20 — aber am KI-Bild haengt keine Warnung"
    # Ohne KI-Messung (nur Grundlage) fehlt das Feld — kein null.
    leer = {}
    kosmo_szene._kontrast_ki_eintragen(leer, None, [_eintrag("sSE", 30.0, None)])
    assert kosmo_szene.FELD_KONTRAST_KI not in leer
