"""Eine IFC-Bestellung aus KosmoOrbit wird angenommen und umgewandelt — Befund 22.09.2026.

Was gemessen wurde (die Einbausperre)
-------------------------------------
KosmoOrbit schreibt eine hochgeladene IFC **unverändert** in den Auftragsordner; nur die
Dateiendung folgt ``geometry.format`` (Antwort auf auf-20260909-91, V3_V4, übertragen am
22.09.2026). Eine IFC-Bestellung liegt also als ``model.ifc`` da. Bis zu diesem Tag:

(a) suchte ``bruecke.lies_auftrag`` nur ``model.glb`` — jede IFC-Bestellung, also jede
    Innenraum-Bestellung, blieb mit «Die Geometrie fehlt: model.glb» liegen;
(b) hätte ``abholer.verarbeiter`` die IFC unverwandelt an den Multipass gegeben.

Was diese Datei bewacht, über den Produktweg
--------------------------------------------
``bruecke.lies_auftrag`` → ``abholer.hole_einen`` → ``abholer.verarbeiter``:

1. Die Brücke nimmt ``model.ifc`` genau dann, wenn ``format: 'ifc'`` bestellt ist. Liegt
   die andere Datei statt oder neben der bestellten, weist sie mit Satz ab.
2. Der Abholer wandelt die IFC über ``seams.ifc_zu_glb`` in den Arbeitsordner, fragt das
   Tor, und der Multipass bekommt die **glb** — mit der Hochachse, die der Umwandler
   meldet.
3. Scheitert die Umwandlung (oder sagt das Tor ``ablehnen_konversion``), steht der Auftrag
   auf ``error`` mit Satz, und es liegt **kein** Ergebnis da.
4. Ein unplausibler Massstab wird gemeldet und sperrt nicht — dieselbe Linie wie
   ``abholer._massstab_gemeldet``.
5. Eine abbestellte IFC wird nicht umgewandelt.

6. Mit eingerichtetem ``.venv-ifc`` (sonst übersprungen): eine synthetische IFC aus
   ``tools/make_test_ifc.py --raeume`` durch den **echten** Umwandler und den **echten**
   Raumleser — die Innenansicht kommt am Multipass an, und das Auge liegt in der
   Szenenbox der UMGEWANDELTEN glb. Ebenso die reale Form (``interior`` mit benannten
   Kameras in IFC-Koordinaten). Nur Multipass und Render sind dort Attrappen.

7. Durchsicht 23.09.2026: Eine Umwandlung, die Erfolg meldet und keine Datei hinterlässt,
   wird nicht gerechnet; die Empfehlung des Tors zur Neuzentrierung steht als Warnung im
   Befund; der Modellstand einer abbestellten IFC steht im Befund; und eine Szene, die
   sich nicht lesen lässt (``format`` kein Text, ``geometry`` kein Block, Kamera ohne
   ``up_axis``), nimmt nicht mehr den ganzen Durchgang mit.

In 1 bis 5 ist ``seams.ifc_zu_glb`` eine Attrappe, die eine gültige Minimal-glb schreibt:
Die Proben sollen nicht davon abhängen, ob der Unterprozess (Regel 1, Prozessgrenze)
eingerichtet ist. Ob KosmoOrbit wirklich ``model.ifc`` schreibt, steht in der Antwort
drüben und ist hier NICHT nachgemessen — am Gerät unbestätigt.

Regel 3: IFC, glb und Szene sind synthetisch.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from aiimaging import abholer, bruecke, kosmo_szene, seams

from test_abholer import _auftrag, _kette, _minimale_glb

#: Eine kleine, gültige IFC — nur Kopf und eine Einheit. Mehr sieht der Sichtgang nicht
#: an, und mehr braucht die Attrappe des Umwandlers nicht.
IFC_TEXT = (
    "ISO-10303-21;\n"
    "HEADER;\n"
    "FILE_DESCRIPTION((''),'');\n"
    "FILE_NAME('model.ifc','2026-09-22T00:00:00',(''),(''),'','Testfixture','');\n"
    "FILE_SCHEMA(('IFC4'));\n"
    "ENDSEC;\n"
    "DATA;\n"
    "#1=IFCSIUNIT(*,.LENGTHUNIT.,$,.METRE.);\n"
    "ENDSEC;\nEND-ISO-10303-21;\n")

#: Die Hüllbox eines synthetischen Testbaus, 8 × 5 × 3,25 m, in IFC-Metern (Z oben).
BBOX_TESTBAU = [[0.0, 0.0, 0.0], [8.0, 5.0, 3.25]]


def ifc_szene(**zusatz) -> dict:
    szene = {
        "schema": kosmo_szene.SCHEMA_SZENE,
        "geometry": {"path": "model.ifc", "format": "ifc"},
        "cameras": "auto",
        "render": {"resolution": [512, 512], "samples": 64, "faithful": 0.8},
        "style": {"prompt": "ein Haus"},
        "vis": {"backbone": "qwen"},
    }
    szene.update(zusatz)
    return szene


def ifc_auftrag(basis, szene=None, *, glb_daneben=False):
    """Ein Auftragsordner, wie die Brücke ihn für ``format: 'ifc'`` anlegt."""
    ordner = _auftrag(basis, szene=szene or ifc_szene(), mit_modell=False)
    (ordner / bruecke.DATEI_MODELL_IFC).write_text(IFC_TEXT, encoding="utf-8")
    if glb_daneben:
        (ordner / bruecke.DATEI_MODELL).write_bytes(_minimale_glb())
    return ordner


def umwandler(protokoll: list, *, bericht=None, fehler=None, schreibt=True):
    """Attrappe für ``seams.ifc_zu_glb``: schreibt eine gültige Minimal-glb und meldet.

    ``bericht`` ergänzt oder überschreibt Felder des Reports; ``fehler`` wird geworfen
    wie ein gescheiterter Unterprozess. ``schreibt=False`` meldet Erfolg, ohne die Datei
    anzulegen.
    """
    def ifc_zu_glb(ifc_path, glb_path, **kw):
        protokoll.append({"ifc": ifc_path, "glb": glb_path})
        if fehler is not None:
            raise fehler
        if schreibt:
            Path(glb_path).write_bytes(_minimale_glb("IfcOpenShell-Attrappe"))
        return {"status": "ok", "glb_path": glb_path, "up_axis": "Y",
                "bbox": BBOX_TESTBAU, "n_elements": 6, "n_triangles": 72,
                **(bericht or {})}
    return ifc_zu_glb


def lauf(tmp_path, ordner, **einstellungen):
    protokoll, attrappen = _kette()
    attrappen.update(einstellungen)
    antwort = abholer.hole_einen(
        ordner, fremde_freigabe_gilt=True,
        verarbeite=abholer.verarbeiter(out_wurzel=tmp_path / "aus", nullprobe=False,
                                       **attrappen))
    return antwort, protokoll


def _zettel(ordner) -> dict:
    return json.loads((ordner / bruecke.DATEI_LAUFZETTEL).read_text(encoding="utf-8"))


# --------------------------------------------------------------------------------------
# 1 · Die Brücke nimmt model.ifc — und nur, wenn ifc bestellt ist
# --------------------------------------------------------------------------------------

def test_eine_ifc_bestellung_mit_model_ifc_hat_keinen_geometriemangel(tmp_path):
    """**Die Einbausperre (a).** Vor dem 22.09.2026: «Die Geometrie fehlt: model.glb»."""
    gelesen = bruecke.lies_auftrag(ifc_auftrag(tmp_path), fremde_freigabe_gilt=True)

    assert gelesen["maengel"] == ()
    assert gelesen["modell"].name == bruecke.DATEI_MODELL_IFC


@pytest.mark.parametrize("fmt, liegt, stichwort", [
    ("ifc", (bruecke.DATEI_MODELL,), "passt nicht zur Bestellung"),
    ("ifc", (bruecke.DATEI_MODELL, bruecke.DATEI_MODELL_IFC), "UND"),
    ("ifc", (), "Die Geometrie fehlt: model.ifc"),
    ("glb", (bruecke.DATEI_MODELL_IFC,), "passt nicht zur Bestellung"),
    ("glb", (bruecke.DATEI_MODELL, bruecke.DATEI_MODELL_IFC), "UND"),
])
def test_die_falsche_oder_eine_zweite_geometrie_wird_mit_satz_abgewiesen(
        tmp_path, fmt, liegt, stichwort):
    """Kein stilles Raten, welche Datei gemeint ist: Drüben gibt ein Widerspruch zwischen
    Format und Endung ein 400 (auf-91 V3_V4) — kommt er hier trotzdem an, hört er einen
    Satz."""
    ordner = _auftrag(tmp_path, szene=ifc_szene(
        geometry={"path": f"model.{fmt}", "format": fmt}), mit_modell=False)
    for name in liegt:
        if name == bruecke.DATEI_MODELL_IFC:
            (ordner / name).write_text(IFC_TEXT, encoding="utf-8")
        else:
            (ordner / name).write_bytes(_minimale_glb())

    def nie(auftrag):
        raise AssertionError("eine abgewiesene Bestellung wird nicht gerechnet")

    antwort = abholer.hole_einen(ordner, verarbeite=nie, fremde_freigabe_gilt=True)

    assert antwort["tat"] == abholer.TAT_LIEGENGELASSEN
    assert stichwort in antwort["grund"]
    assert _zettel(ordner)["status"] == bruecke.STATUS_QUEUED


# --------------------------------------------------------------------------------------
# 2 · Der Abholer wandelt um, und der Multipass bekommt die glb
# --------------------------------------------------------------------------------------

def test_eine_ifc_bestellung_kommt_als_umgewandelte_glb_am_multipass_an(
        tmp_path, monkeypatch):
    """**Die Einbausperre (b).** Vor dem 22.09.2026 reichte ``verarbeite`` das Modell
    unverwandelt an den Multipass — eine IFC dort, wo Blender eine glb erwartet. (Dass es
    nie so weit kam, lag nur an der Sperre (a) davor.)"""
    gerufen: list = []
    monkeypatch.setattr(seams, "ifc_zu_glb", umwandler(gerufen))
    ordner = ifc_auftrag(tmp_path)
    glb_am_multipass: list = []

    protokoll, attrappen = _kette()
    echter_multipass = attrappen["_multipass"]

    def multipass(glb, out, **kw):
        glb_am_multipass.append(glb)
        return echter_multipass(glb, out, **kw)

    attrappen["_multipass"] = multipass
    antwort = abholer.hole_einen(
        ordner, fremde_freigabe_gilt=True,
        verarbeite=abholer.verarbeiter(out_wurzel=tmp_path / "aus", nullprobe=False,
                                       **attrappen))

    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort["grund"]
    assert len(gerufen) == 1
    assert gerufen[0]["ifc"].endswith(bruecke.DATEI_MODELL_IFC)
    arbeitsordner = tmp_path / "aus" / ordner.name
    assert gerufen[0]["glb"] == str(arbeitsordner / abholer.DATEI_UMGEWANDELT)
    assert glb_am_multipass and all(g == gerufen[0]["glb"] for g in glb_am_multipass), (
        "jede Kamera rechnet auf der umgewandelten glb, keine auf der IFC")
    assert all(kw["up_axis"] == "Y" for kw in protokoll["multipass"]), (
        "die Achse, die der Umwandler meldet — nicht die Annahme des Abholers")

    befund = abholer.lies_befund(ordner)
    assert befund["hochachse"] == {"wert": "Y", "quelle": "umwandlung"}
    assert befund["umwandlung"]["quelle"] == bruecke.DATEI_MODELL_IFC
    assert befund["umwandlung"]["torwaechter"]["entscheidung"] == "annehmen"
    assert befund["umwandlung"]["glb_path"] == abholer.DATEI_UMGEWANDELT, (
        "Regel 3: im Befund nur der Dateiname")
    assert _zettel(ordner)["status"] == bruecke.STATUS_DONE


def test_eine_glb_bestellung_wird_nicht_umgewandelt(tmp_path, monkeypatch):
    """Die Gegenprobe: Der bisherige Weg ruft keinen Umwandler."""
    def nie(*a, **kw):
        raise AssertionError("eine glb wird nicht umgewandelt")

    monkeypatch.setattr(seams, "ifc_zu_glb", nie)
    ordner = _auftrag(tmp_path)
    antwort, protokoll = lauf(tmp_path, ordner)

    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort["grund"]
    assert abholer.lies_befund(ordner)["umwandlung"] is None


# --------------------------------------------------------------------------------------
# 3 · Scheitert die Umwandlung, liegt der Auftrag mit Satz — nicht als fertig
# --------------------------------------------------------------------------------------

@pytest.mark.parametrize("attrappe, stichwort", [
    (dict(fehler=seams.SeamError("IFC→glb fehlgeschlagen (Code 1):\nkeine Geometrie")),
     "nicht in eine glb umwandeln"),
    (dict(bericht={"bbox": None}), "traegt nicht"),
    (dict(bericht={"status": "error", "error": "keine Geometrie im IFC"}),
     "traegt nicht"),
])
def test_eine_gescheiterte_umwandlung_wird_nicht_als_fertig_gemeldet(
        tmp_path, monkeypatch, attrappe, stichwort):
    gerufen: list = []
    monkeypatch.setattr(seams, "ifc_zu_glb", umwandler(gerufen, **attrappe))
    ordner = ifc_auftrag(tmp_path)

    antwort, protokoll = lauf(tmp_path, ordner)

    assert antwort["tat"] == abholer.TAT_FEHLER
    assert stichwort in antwort["grund"]
    assert protokoll["multipass"] == [], "nichts ersatzweise gerechnet"
    zettel = _zettel(ordner)
    assert zettel["status"] == bruecke.STATUS_ERROR
    assert stichwort in zettel["error"], "der Satz steht am Auftrag, nicht nur im Journal"
    assert not (ordner / bruecke.DATEI_ERGEBNIS).exists(), "kein Ergebnis, das fertig sagt"


def test_eine_umwandlung_die_erfolg_meldet_ohne_datei_wird_nicht_gerechnet(
        tmp_path, monkeypatch):
    """Durchsicht 23.09.2026 (Mangel 4): Der Umwandler sagt ``status: ok``, das Tor
    nimmt an — und ``modell.glb`` liegt nicht da. Gerechnet wird nur auf einer Datei, die
    da ist; bis dahin war dieser Zweig unbewacht."""
    monkeypatch.setattr(seams, "ifc_zu_glb", umwandler([], schreibt=False))
    ordner = ifc_auftrag(tmp_path)

    antwort, protokoll = lauf(tmp_path, ordner)

    assert antwort["tat"] == abholer.TAT_FEHLER
    assert "liegt nicht im Arbeitsordner" in antwort["grund"]
    assert protokoll["multipass"] == []
    assert _zettel(ordner)["status"] == bruecke.STATUS_ERROR


# --------------------------------------------------------------------------------------
# 4 · Der Massstab wird gemeldet, nicht gesperrt
# --------------------------------------------------------------------------------------

def test_ein_unplausibler_massstab_der_umwandlung_wird_gemeldet_und_sperrt_nicht(
        tmp_path, monkeypatch):
    """Dieselbe Linie wie ``abholer._massstab_gemeldet``: Die Fehlalarmrate am Bestand ist
    ungemessen, und eine IFC strenger zu prüfen als dieselbe Geometrie als glb hiesse,
    dass das Format über die Sperre entscheidet."""
    in_millimetern = [[0.0, 0.0, 0.0], [8000.0, 5000.0, 3250.0]]
    monkeypatch.setattr(seams, "ifc_zu_glb",
                        umwandler([], bericht={"bbox": in_millimetern}))
    ordner = ifc_auftrag(tmp_path)

    antwort, _ = lauf(tmp_path, ordner)

    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort["grund"]
    tor = abholer.lies_befund(ordner)["umwandlung"]["torwaechter"]
    assert tor["entscheidung"] == "ablehnen_massstab"
    assert "Massstab" in tor["begruendung"]


def test_die_empfehlung_zur_neuzentrierung_steht_als_warnung_im_befund(
        tmp_path, monkeypatch):
    """Durchsicht 23.09.2026 (Mangel 5): ``_ifc_umwandeln`` übernahm vom Tor nur
    Entscheidung und Begründung — ``empfiehlt_neuzentrierung`` fiel still weg. Ein
    synthetischer Testbau in Landeskoordinaten (8 × 5 × 3 m, weit vom Ursprung): Das Tor
    nimmt an und empfiehlt, neu zu zentrieren. Befolgt wird es nicht, gesagt schon."""
    weit_weg = [[2600000.0, 1200000.0, 400.0], [2600008.0, 1200005.0, 403.0]]
    monkeypatch.setattr(seams, "ifc_zu_glb", umwandler([], bericht={"bbox": weit_weg}))
    ordner = ifc_auftrag(tmp_path)

    antwort, protokoll = lauf(tmp_path, ordner)

    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort["grund"]
    assert protokoll["multipass"], "sie sperrt nichts"
    umwandlung = abholer.lies_befund(ordner)["umwandlung"]
    assert umwandlung["torwaechter"]["entscheidung"] == "annehmen"
    assert umwandlung["torwaechter"]["empfiehlt_neuzentrierung"] is True
    assert len(umwandlung["warnungen"]) == 1
    assert "neu zu zentrieren" in umwandlung["warnungen"][0]
    assert "zentriert NICHT neu" in umwandlung["warnungen"][0]


def test_ohne_empfehlung_bleibt_die_warnung_leer(tmp_path, monkeypatch):
    """Die Gegenprobe: der Testbau am Ursprung."""
    monkeypatch.setattr(seams, "ifc_zu_glb", umwandler([]))
    ordner = ifc_auftrag(tmp_path)

    antwort, _ = lauf(tmp_path, ordner)

    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort["grund"]
    umwandlung = abholer.lies_befund(ordner)["umwandlung"]
    assert umwandlung["torwaechter"]["empfiehlt_neuzentrierung"] is False
    assert umwandlung["warnungen"] == []


# --------------------------------------------------------------------------------------
# 5 · Abbestellt: keine Umwandlung
# --------------------------------------------------------------------------------------

def test_eine_abbestellte_ifc_wird_nicht_umgewandelt(tmp_path, monkeypatch):
    def nie(*a, **kw):
        raise AssertionError("wer abbestellt, bekommt keinen Unterprozess")

    monkeypatch.setattr(seams, "ifc_zu_glb", nie)
    ordner = ifc_auftrag(tmp_path, ifc_szene(vis={"backbone": "qwen", "skip": True}))

    antwort, protokoll = lauf(tmp_path, ordner)

    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort["grund"]
    assert protokoll["multipass"] == []
    assert antwort["ergebnis"]["qa"]["verdict"]["reason"].startswith("ABBESTELLT")
    # Der Modellstand sagt «nicht geprüft», mit Grund — und nicht, was der glb-Leser
    # über eine IFC gemeldet hätte (Durchsicht 23.09.2026, Mangel 4).
    from aiimaging import modellstand

    stand = abholer.lies_befund(ordner)["modellstand"]
    assert stand["geprueft"] is False
    assert stand["urteil"] == modellstand.UNGEPRUEFT
    assert stand["grund"].startswith("Abbestellt: Die IFC wurde nicht")


# --------------------------------------------------------------------------------------
# 6 · Der echte Umwandler, wenn er da ist
# --------------------------------------------------------------------------------------

def _konverter_fehlt() -> bool:
    try:
        return not Path(seams.finde_ifc_python()).exists()
    except seams.SeamError:
        return True


@pytest.mark.skipif(_konverter_fehlt(),
                    reason=".venv-ifc fehlt — der Lauf ueber die Prozessgrenze entfaellt")
def test_eine_innenbestellung_laeuft_durch_den_echten_umwandler_und_raumleser(tmp_path):
    """Die synthetische IFC mit Räumen, echt umgewandelt und echt gelesen. Attrappen sind
    nur Multipass und Render — die Innenansicht muss mit einem Auge IM Raum ankommen, und
    der Multipass bekommt eine glb, die der Umwandler wirklich geschrieben hat."""
    from aiimaging import raumkamera

    ordner = _auftrag(tmp_path, szene=ifc_szene(interior={"rooms": "auto"}),
                      mit_modell=False)
    repo = Path(__file__).resolve().parents[1]
    erzeugt = subprocess.run(
        [sys.executable, str(repo / "tools" / "make_test_ifc.py"),
         str(ordner / bruecke.DATEI_MODELL_IFC), "--raeume"],
        capture_output=True, text=True, timeout=120, check=False)
    assert erzeugt.returncode == 0, erzeugt.stderr

    glb_am_multipass: list = []
    protokoll, attrappen = _kette()
    echter_multipass = attrappen["_multipass"]

    def multipass(glb, out, **kw):
        glb_am_multipass.append(Path(glb))
        return echter_multipass(glb, out, **kw)

    attrappen["_multipass"] = multipass
    antwort = abholer.hole_einen(
        ordner, fremde_freigabe_gilt=True,
        verarbeite=abholer.verarbeiter(out_wurzel=tmp_path / "aus", nullprobe=False,
                                       **attrappen))

    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort["grund"]
    assert len(protokoll["multipass"]) == 1
    assert glb_am_multipass[0].suffix == ".glb" and glb_am_multipass[0].is_file()
    assert glb_am_multipass[0].read_bytes()[:4] == b"glTF"
    kw = protokoll["multipass"][0]
    assert kw["up_axis"] == "Y"
    innen = abholer.lies_befund(ordner)["innenansicht"]
    assert innen and innen["raum"], "ein Raum aus der IFC wurde gewaehlt"
    raeume = seams.ifc_raeume(str(ordner / bruecke.DATEI_MODELL_IFC))["raeume"]
    grundriss = next(r["grundriss_m"] for r in raeume if r["name"] == innen["raum"])
    assert raumkamera.ist_innen(kw["auge"][:2], grundriss), "das Auge steht im Raum"
    # UND IN DER GEOMETRIE, DIE BLENDER BEKOMMT (Durchsicht 23.09.2026, Mangel 6). Die
    # Zusicherung darüber ist zirkulär — Auge und Grundriss stammen vom selben Raumleser.
    # Diese hier liest die umgewandelte glb selbst und rechnet sie so in Weltkoordinaten,
    # wie Blenders glTF-Import es tut (`glbbox.nach_welt`).
    assert _in_box(kw["auge"], _weltbox(glb_am_multipass[0])), (
        "das Auge liegt in der Szenenbox der umgewandelten glb")


def _weltbox(glb):
    from aiimaging import glbbox

    return glbbox.bauwerksbox(glb, up_axis="Y")["bbox_szene"]


def _in_box(punkt, box, spiel=1e-6) -> bool:
    lo, hi = box
    return all(lo[i] - spiel <= float(punkt[i]) <= hi[i] + spiel for i in range(3))


@pytest.mark.skipif(_konverter_fehlt(),
                    reason=".venv-ifc fehlt — der Lauf ueber die Prozessgrenze entfaellt")
def test_die_reale_innenbestellung_laeuft_durch_den_echten_umwandler(tmp_path):
    """Die REALE Form (auf-91 V1): ``model.ifc``, ``interior`` und benannte Kameras in
    IFC-Koordinaten mit ``up_axis: 'z'`` — durch den echten Umwandler. Kein Raum wird
    gelesen; die Kameras kommen unverändert am Multipass an und liegen in der Szenenbox
    der umgewandelten glb. Das ist die Annahme, auf der die reale Form steht: IFC-Meter
    mit Z oben SIND nach Umwandlung (Z→Y) und Blender-Import (Y→Z) Weltkoordinaten.

    Was hier NICHT geprüft ist: dass KosmoOrbit seine Kameras wirklich in diesen
    Koordinaten rechnet — am Gerät unbestätigt."""
    from aiimaging import raumkamera

    kameras = [{"name": "Innen-Sued", "position": [6.35, 0.8, 1.3],
                "target": [6.35, 2.4, 1.3], "fov": 70, "up_axis": "z"}]
    ordner = _auftrag(tmp_path, szene=ifc_szene(interior={"rooms": "auto"},
                                                cameras=kameras), mit_modell=False)
    repo = Path(__file__).resolve().parents[1]
    erzeugt = subprocess.run(
        [sys.executable, str(repo / "tools" / "make_test_ifc.py"),
         str(ordner / bruecke.DATEI_MODELL_IFC), "--raeume"],
        capture_output=True, text=True, timeout=120, check=False)
    assert erzeugt.returncode == 0, erzeugt.stderr

    glb_am_multipass: list = []
    protokoll, attrappen = _kette()
    echter_multipass = attrappen["_multipass"]

    def multipass(glb, out, **kw):
        glb_am_multipass.append(Path(glb))
        return echter_multipass(glb, out, **kw)

    def nie(_modell):
        raise AssertionError("die Standpunkte kamen mit — kein Raum zu lesen")

    attrappen.update(_multipass=multipass, _raeume=nie)
    antwort = abholer.hole_einen(
        ordner, fremde_freigabe_gilt=True,
        verarbeite=abholer.verarbeiter(out_wurzel=tmp_path / "aus", nullprobe=False,
                                       **attrappen))

    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort["grund"]
    assert [kw["auge"] for kw in protokoll["multipass"]] == [(6.35, 0.8, 1.3)]
    assert glb_am_multipass[0].read_bytes()[:4] == b"glTF"
    assert _in_box(protokoll["multipass"][0]["auge"], _weltbox(glb_am_multipass[0]))
    # Gegenprobe gegen den echten Raumleser — hier nur zur Einordnung der synthetischen
    # Zahlen, nicht als Teil des Produktwegs: Das Auge steht im Raum «Raum-Sued».
    raeume = seams.ifc_raeume(str(ordner / bruecke.DATEI_MODELL_IFC))["raeume"]
    sued = next(r["grundriss_m"] for r in raeume if r["name"] == "Raum-Sued")
    assert raumkamera.ist_innen([6.35, 0.8], sued)
    befund = abholer.lies_befund(ordner)
    assert befund["innenansicht"]["standpunkt"] == kosmo_szene.INNEN_STANDPUNKT_MITGESANDT
    grund = antwort["ergebnis"]["qa"]["verdict"]["reason"]
    assert "INNENANSICHT BESTELLT" in grund


# --------------------------------------------------------------------------------------
# 7 · Eine unlesbare Szene hält diesen Auftrag auf — nicht den Durchgang
# --------------------------------------------------------------------------------------

def test_ein_format_das_kein_text_ist_ist_ein_mangel_mit_satz(tmp_path):
    """Durchsicht 23.09.2026 (Mangel 7), nachgestellt: ``format: 5`` warf in
    ``lies_szene`` einen AttributeError (``.lower()``), und der kam aus
    ``abholer.hole_einen`` heraus. Jetzt: ein Mangel, der Auftrag bleibt mit Satz liegen."""
    ordner = _auftrag(tmp_path, szene=ifc_szene(
        geometry={"path": "model.glb", "format": 5}))

    def nie(auftrag):
        raise AssertionError("eine abgewiesene Bestellung wird nicht gerechnet")

    antwort = abholer.hole_einen(ordner, verarbeite=nie, fremde_freigabe_gilt=True)

    assert antwort["tat"] == abholer.TAT_LIEGENGELASSEN
    assert "'geometry.format' ist 5 und kein Text" in antwort["grund"]
    assert "geometry.format" in _zettel(ordner)[bruecke.FELD_MELDUNG]


@pytest.mark.parametrize("szene, stichwort", [
    (dict(geometry="model.glb"), "statt eines Blocks"),
    (dict(geometry={"format": "glb"}), "geometry.path"),
    (dict(geometry={"path": "model.glb", "format": "glb"},
          cameras=[{"name": "n", "position": [1, 2, 3], "target": [0, 0, 0],
                    "fov": 50}]), "up_axis"),
])
def test_eine_unlesbare_szene_nimmt_den_durchgang_nicht_mit(tmp_path, szene, stichwort):
    """Durchsicht 23.09.2026: ``lies_szene`` wirft ``SzenenError``, wenn es nichts zu
    rendern gibt — und ``hole_einen`` fing nur ``BrueckenError``. Ein einziger solcher
    Auftrag warf aus dem ``durchgang`` heraus, und der zweite, lesbare Auftrag daneben
    wurde nie angesehen. Jetzt bleibt der unlesbare liegen, der lesbare läuft."""
    kaputt = _auftrag(tmp_path, "vis-1787123048-000001", szene=ifc_szene(**szene))
    heil = _auftrag(tmp_path, "vis-1787123048-000002")

    bericht = abholer.durchgang(tmp_path, verarbeite=lambda a: {"bilder": []},
                                fremde_freigabe_gilt=True)

    taten = {e["job_id"]: e for e in bericht["ergebnisse"]}
    assert taten[kaputt.name]["tat"] == abholer.TAT_LIEGENGELASSEN
    assert "nicht lesbar" in taten[kaputt.name]["grund"]
    assert stichwort in taten[kaputt.name]["grund"]
    assert taten[heil.name]["tat"] == abholer.TAT_VERARBEITET
