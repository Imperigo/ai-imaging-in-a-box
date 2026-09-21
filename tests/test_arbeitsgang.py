"""Der Arbeitsgang — **die Stelle, an der die drei Bausteine zusammenkommen.**

Importeur und Projekt waren am 21.09.2026 gebaut und **an keiner Stelle verdrahtet**.
*Ein gebautes Modul ohne Aufrufer ist kein Werkzeug, sondern ein Vorrat.*

Diese Sammlung prüft die vier Stellen, an denen ein solcher Ablauf still Schaden anrichtet:

1. Er rechnet gegen ein Modell, das inzwischen ein anderes ist, und schreibt das Urteil
   unter den alten Namen.
2. Er vergisst ein erzeugtes Bild — und ein Bild ohne Eintrag ist später von einem Bild
   ohne Prüfung nicht zu unterscheiden.
3. Er trägt ein Urteil ein, das keiner Prüfung entstammt.
4. Er wirft einen gescheiterten Lauf weg, und «nie versucht» sieht danach aus wie
   «versucht und ging nicht».

**Ohne GPU, ohne Blender, ohne Gewichte.** Alle Knoten sind Attrappen, die echte — aber
winzige — Dateien schreiben.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from aiimaging import arbeitsgang, kette, projekt
from aiimaging.kette import ART_GEOMETRIE, ART_MULTIPASS, ART_QA, ART_RENDER


# ------------------------------------------------------------------- die Attrappen

class Werkbank:
    """Ersatz-Ausführer für die vier Knotenarten.

    Die Attrappen schreiben **echte** Dateien. Eine, die nur Pfade behauptet, ergäbe bei
    jedem Lauf einen Fehltreffer im Zwischenspeicher — und der Test bewiese das Gegenteil
    dessen, was er soll.
    """

    def __init__(self, *, urteil=True, render_faellt: bool = False) -> None:
        self.urteil = urteil
        self.render_faellt = render_faellt

    def tabelle(self) -> dict:
        return {ART_GEOMETRIE: self.geometrie, ART_MULTIPASS: self.multipass,
                ART_RENDER: self.render, ART_QA: self.qa}

    def geometrie(self, *, knoten, eingaben, out_dir):
        glb = Path(out_dir) / "modell.glb"
        glb.write_text("glb", encoding="utf-8")
        return {"glb_path": str(glb), "up_axis": "Y",
                "bbox": [[0, 0, 0], [8.0, 5.0, 3.25]]}

    def multipass(self, *, knoten, eingaben, out_dir):
        tiefe, beauty = Path(out_dir) / "tiefe_norm.png", Path(out_dir) / "beauty.png"
        tiefe.write_text("tiefe", encoding="utf-8")
        beauty.write_text("beauty", encoding="utf-8")
        return {"status": "ok", "depth_png": str(tiefe), "beauty_png": str(beauty),
                "aufloesung": knoten.params["aufloesung"],
                "samples": knoten.params["samples"]}

    def render(self, *, knoten, eingaben, out_dir):
        if self.render_faellt:
            return {"status": "fehler", "error": "Die Karte ist voll."}
        bild = Path(out_dir) / "bild.png"
        bild.write_text("bild", encoding="utf-8")
        return {"status": "ok", "bild_png": str(bild), "seed": knoten.params["seed"]}

    def qa(self, *, knoten, eingaben, out_dir):
        return {"status": "ok", "bestanden": self.urteil, "score": 0.91,
                "schwelle": knoten.params["schwelle"]}


def _blender_bericht(ziel: Path) -> dict:
    return {"status": "ok", "glb_path": str(ziel), "quelle_format": "Autodesk FBX",
            "quelle_endung": ".fbx", "blender": "4.2.0", "up_axis": "Y",
            "bbox": [[0, 0, 0], [8.0, 5.0, 3.25]], "n_elements": 12,
            "n_triangles": 240, "warnungen": [], "error": None}


@pytest.fixture
def glb(tmp_path):
    """Ein gültiges glb — es geht den Weg «durchgereicht», also ohne jeden Subprozess."""
    import struct
    js = json.dumps({"asset": {"version": "2.0", "generator": "Testfixture"}}).encode()
    js += b" " * (-len(js) % 4)
    block = struct.pack("<II", len(js), 0x4E4F534A) + js
    pfad = tmp_path / "quelle" / "haus.glb"
    pfad.parent.mkdir(parents=True, exist_ok=True)
    pfad.write_bytes(struct.pack("<4sII", b"glTF", 2, 12 + len(block)) + block)
    return pfad


@pytest.fixture
def mappe(tmp_path, glb):
    """Ein angelegtes Projekt mit importierter Geometrie.

    ``up_axis`` steht hier in den Einstellungen, **weil es dort hingehört**: Die Quelle
    ist eine fremde glb, und glTF hat kein Feld für die Hochachse. Wer sie weiss, sagt sie
    einmal; wer sie nicht weiss, bekommt beim Rechnen einen Satz dazu (siehe unten).
    """
    wurzel = tmp_path / "projekt"
    arbeitsgang.lege_an(wurzel, glb, name="Wohnhaus Nord",
                        einstellungen={"prompt": "Abendlicht", "seed": 7, "up_axis": "Y"})
    return wurzel


# ----------------------------------------------------------------- 1 · Anlegen

def test_anlegen_holt_das_modell_herein_und_schreibt_die_mappe(tmp_path, glb):
    wurzel = tmp_path / "projekt"
    ergebnis = arbeitsgang.lege_an(wurzel, glb, name="Wohnhaus Nord")

    assert ergebnis["pfad"].exists()
    auf = projekt.oeffne(wurzel)
    assert auf["projekt"]["name"] == "Wohnhaus Nord"
    assert auf["projekt"]["import"]["status"] == "ok"
    assert auf["projekt"]["import"]["weg"] == "durchgereicht"


def test_der_importbericht_sagt_auch_was_NICHT_geprueft_wurde(tmp_path, glb):
    """*Nicht geprüft ist nicht in Ordnung.*

    Ohne bekannte Wahrheit kann niemand sagen, ob aus der Datei das wurde, was darin
    stand. Im Projekt steht darum ``treue: None`` — und später ist nicht mehr zu
    rekonstruieren, dass diese Frage offen war.
    """
    arbeitsgang.lege_an(tmp_path / "p", glb)
    auf = projekt.oeffne(tmp_path / "p")
    assert auf["projekt"]["import"]["treue"] is None


def test_ein_abgelehntes_modell_ist_ein_befund_und_kein_absturz(tmp_path):
    """Die Mappe entsteht trotzdem — mit dem Satz, was zu tun wäre."""
    falsch = tmp_path / "modell.glb"
    falsch.write_bytes(b"\xff\xd8\xff\xe0" + b"\x00" * 64)        # eine umbenannte JPG

    ergebnis = arbeitsgang.lege_an(tmp_path / "p", falsch)

    assert ergebnis["projekt"]["import"]["status"] == "abgelehnt"
    assert ergebnis["projekt"]["import"]["naechster_schritt"]
    assert ergebnis["pfad"].exists(), "die Mappe steht, auch wenn das Modell nicht taugt"


# --------------------------------------------------------- 2 · der Lauf und seine Bilder

def test_ein_lauf_traegt_jedes_bild_mit_seinem_urteil_ein(mappe):
    ergebnis = arbeitsgang.rechne(mappe, ausfuehrer=Werkbank().tabelle())

    assert ergebnis["vermerkt"] == 1
    bild = ergebnis["projekt"]["bilder"][0]
    assert bild["geometrie_bestanden"] is True
    assert bild["geometrie_gemessen"] is True
    assert bild["schicht"] == kette.SCHICHT_GEOMETRIE
    assert bild["herkunft"]["urteil_von"] == kette.KNOTEN_QA


def test_die_mappe_traegt_die_vorgabe_und_der_aufruf_das_besondere(mappe):
    """Sonst müsste man jede Einstellung bei jedem Lauf wiederholen.

    *Der erste vergessene Wert fällt niemandem auf — er sieht aus wie eine Entscheidung.*
    """
    ergebnis = arbeitsgang.rechne(mappe, ausfuehrer=Werkbank().tabelle(),
                                  prompt="Mittagslicht")
    herkunft = ergebnis["projekt"]["bilder"][0]["herkunft"]
    assert herkunft["prompt"] == "Mittagslicht", "der Aufruf schlägt die Mappe"
    assert herkunft["seed"] == 7, "und was er nicht sagt, kommt aus der Mappe"


def test_ohne_pruefung_steht_NICHT_GEMESSEN_da_und_kein_leeres_feld(mappe):
    """``None`` mit Grund — nicht «nichts».

    Ein Bild ohne Eintrag wäre später von einem Bild ohne Prüfung nicht zu unterscheiden,
    und beide sähen aus wie ein bestandenes.
    """
    ergebnis = arbeitsgang.rechne(mappe, ausfuehrer=Werkbank().tabelle(), qa=False)

    bild = ergebnis["projekt"]["bilder"][0]
    assert bild["geometrie_bestanden"] is None
    assert bild["geometrie_gemessen"] is False
    assert "NICHT GEMESSEN" in bild["herkunft"]["grund"]


def test_ein_durchgefallenes_urteil_wird_genauso_eingetragen(mappe):
    ergebnis = arbeitsgang.rechne(mappe, ausfuehrer=Werkbank(urteil=False).tabelle())
    assert ergebnis["projekt"]["bilder"][0]["geometrie_bestanden"] is False


def test_ein_gescheiterter_lauf_wird_nicht_weggeworfen(mappe):
    """*«Nie versucht» und «versucht und ging nicht» dürfen nicht gleich aussehen.*"""
    ergebnis = arbeitsgang.rechne(mappe,
                                  ausfuehrer=Werkbank(render_faellt=True).tabelle())

    assert ergebnis["vermerkt"] == 0, "ohne Bild kein Bildeintrag"
    laeufe = ergebnis["projekt"]["laeufe"]
    assert len(laeufe) == 1
    assert laeufe[0]["gescheitert"], "der Fehlschlag steht in der Mappe"


def test_zwei_laeufe_stehen_beide_in_der_mappe(mappe):
    arbeitsgang.rechne(mappe, ausfuehrer=Werkbank().tabelle(), prompt="Abendlicht")
    ergebnis = arbeitsgang.rechne(mappe, ausfuehrer=Werkbank().tabelle(),
                                  prompt="Mittagslicht")
    assert len(ergebnis["projekt"]["laeufe"]) == 2
    assert len(ergebnis["projekt"]["bilder"]) == 2


# --------------------------------------------------------- 2b · die Hochachse wird nicht geraten

def test_eine_fremde_glb_ohne_hochachse_haelt_den_lauf_an(tmp_path, glb):
    """**Die einzige Stelle, an der dieses Modul den Aufrufer um etwas bittet.**

    glTF hat kein Feld für die Hochachse, und die Erzeuger im Ökosystem sind sich uneinig.
    Ein Vorgabewert wäre eine stille Verdrehung: Tiefenkarte, Kamera und Prüfung kippen
    dann **gemeinsam** und sind darum in sich stimmig.

        *Ein Fehlschlag, der wie ein Erfolg aussieht, wird nicht gefunden — er wird
        geglaubt.*
    """
    wurzel = tmp_path / "ohne"
    arbeitsgang.lege_an(wurzel, glb, einstellungen={"prompt": "Abendlicht"})

    with pytest.raises(arbeitsgang.ArbeitsgangError) as fehler:
        arbeitsgang.rechne(wurzel, ausfuehrer=Werkbank().tabelle())

    text = str(fehler.value)
    assert "up_axis" in text, "die Absage nennt den Handgriff"
    assert "IFC" in text, "und den Weg, der die Frage gar nicht erst stellt"


def test_was_wir_selbst_umgewandelt_haben_braucht_keine_angabe(tmp_path, monkeypatch):
    """Bei einer glb aus **unserer** Umwandlung ist die Hochachse eine Tatsache.

    Beide Wege — IFC und Blender — schreiben Y-up. Das ist keine Annahme über eine fremde
    Datei, sondern eine Auskunft über den eigenen Lauf. Sie hier noch einmal zu erfragen
    wäre eine Frage nach etwas, das wir gerade selbst getan haben.
    """
    fbx = tmp_path / "entwurf.fbx"
    fbx.write_bytes(b"Kaydara FBX Binary  \x00" + b"\x00" * 64)
    wurzel = tmp_path / "p"

    def blender(cmd, timeout):
        ziel = Path(cmd[cmd.index("--report") + 1])
        ziel.parent.mkdir(parents=True, exist_ok=True)
        ziel.write_text(json.dumps(_blender_bericht(wurzel / "modell.glb")),
                        encoding="utf-8")
        (wurzel / "modell.glb").write_bytes(b"glTF")
        class _L:
            returncode, stdout, stderr = 0, "", ""
        return _L()

    monkeypatch.setattr(arbeitsgang.importeur.seams, "finde_blender",
                        lambda: "/nicht/benutzt/blender")
    arbeitsgang.lege_an(wurzel, fbx, einstellungen={"prompt": "Abendlicht"},
                        _starte=blender)

    auf = projekt.oeffne(wurzel)
    assert auf["projekt"]["import"]["hochachse_steht_fest"] is True
    assert auf["projekt"]["import"]["hochachse"] == "Y"

    # Und der Lauf kommt ohne Angabe durch.
    ergebnis = arbeitsgang.rechne(wurzel, ausfuehrer=Werkbank().tabelle())
    assert ergebnis["vermerkt"] == 1


def test_eine_durchgereichte_glb_behauptet_die_hochachse_nicht(tmp_path, glb):
    """*Durchgereicht heisst: Wir haben nichts getan — und wissen darum auch nichts.*"""
    arbeitsgang.lege_an(tmp_path / "p", glb)
    einfuhr = projekt.oeffne(tmp_path / "p")["projekt"]["import"]
    assert einfuhr["weg"] == "durchgereicht"
    assert einfuhr["hochachse_steht_fest"] is False
    assert einfuhr["hochachse"] is None


# ------------------------------------------------- 3 · das geänderte Modell hält den Lauf an

def test_ein_geaendertes_modell_haelt_den_lauf_an(mappe, glb):
    """**Der Kern dieses Moduls, und er widerspricht der Regel nebenan nicht.**

    Beim *Öffnen* wird nichts repariert und nichts angehalten. Beim *Rechnen* schon, denn:
    Ein Urteil, das gegen ein anderes Gebäude gemessen wurde und unter dem alten
    Modellnamen in der Mappe steht, ist schlimmer als gar keines.
    """
    glb.write_bytes(glb.read_bytes() + b"\x00" * 32)

    with pytest.raises(arbeitsgang.ArbeitsgangError) as fehler:
        arbeitsgang.rechne(mappe, ausfuehrer=Werkbank().tabelle())

    text = str(fehler.value)
    assert "geändert" in text
    assert "trotz_aenderung=True" in text, "der Riegel nennt, wie man ihn öffnet"


def test_wer_den_riegel_oeffnet_sieht_es_an_jedem_bild(mappe, glb):
    """*Ein Riegel, den man nicht aufmachen kann, wird umgangen.*

    Einer, dessen Öffnen im Ergebnis steht, wird benutzt und bleibt sichtbar.
    """
    glb.write_bytes(glb.read_bytes() + b"\x00" * 32)

    ergebnis = arbeitsgang.rechne(mappe, ausfuehrer=Werkbank().tabelle(),
                                  trotz_aenderung=True)

    assert ergebnis["modell_stand"] == projekt.MODELL_VERAENDERT
    assert ergebnis["projekt"]["bilder"][0]["herkunft"]["modell_stand"] == \
        projekt.MODELL_VERAENDERT


def test_ohne_geometrie_im_projekt_sagt_der_satz_warum(tmp_path, glb):
    """Ein Projekt von Hand angelegt, ohne Import — der Lauf sagt, was fehlt."""
    wurzel = tmp_path / "p"
    projekt.speichere(projekt.neu(wurzel, glb), wurzel)

    with pytest.raises(arbeitsgang.ArbeitsgangError, match="keine umgewandelte Geometrie"):
        arbeitsgang.rechne(wurzel, ausfuehrer=Werkbank().tabelle())


# ------------------------------------------------------------------- 4 · Regel 3 bleibt

def test_auch_der_arbeitsgang_schreibt_keinen_benutzernamen(tmp_path, glb):
    """Die Säuberung sitzt beim Schreiben — also greift sie auch hier."""
    wurzel = tmp_path / "p"
    arbeitsgang.lege_an(wurzel, glb,
                        einstellungen={"ablage": "/home/vorname-nachname/bilder"})
    text = (wurzel / projekt.PROJEKTDATEI).read_text(encoding="utf-8")
    assert "vorname-nachname" not in text and "<nutzer>" in text


# ------------------------------------------------ Der Melder — zusehen beim Rechnen
#
# Bis zum 21.09.2026 meldete ein Lauf ueber die Kette GAR NICHTS, bis er fertig war.
# Von aussen sieht ein rechnender Lauf dann genauso aus wie ein haengender.
#
#     Ein Fortschritt, den niemand sieht, sieht aus wie ein Absturz.

def _melde_mappe(tmp_path):
    """Eine Mappe, die ohne GPU und ohne Blender durch die Kette geht."""
    modell = tmp_path / "m.glb"
    modell.write_bytes(b"glTF\x02\x00\x00\x00")
    p = projekt.neu(tmp_path, modell, name="Melderprobe",
                    einstellungen={"prompt": "ein Haus", "up_axis": "Y", "schritte": 8})
    p["import"] = {"status": "ok", "weg": "ifc", "glb": str(modell), "format": ".ifc",
                   "treue": None, "hochachse": "Y", "hochachse_steht_fest": True,
                   "hinweise": []}
    projekt.speichere(p, tmp_path)
    return p


def _attrappen():
    """Die vorhandene `Werkbank` — sie schreibt echte Dateien und wird hier nicht
    nachgebaut. *Eine zweite Attrappe waere eine zweite Wahrheit ueber denselben Lauf.*"""
    return Werkbank().tabelle()


def test_jeder_knoten_meldet_beginn_und_ende(tmp_path):
    """**Die Probe, auf die es ankommt: beides, und fuer JEDEN Knoten.**

    Der Rumpf der Knotenschleife verlaesst die Runde an fuenf Stellen mit `continue`.
    Ein Melden an jeder einzelnen haette eine davon vergessen — und der Knoten, der nie
    fertig meldet, bliebe in der Anzeige fuer immer am Rechnen.
    """
    _melde_mappe(tmp_path)
    ereignisse = []

    arbeitsgang.rechne(tmp_path, ausfuehrer=_attrappen(), melder=ereignisse.append)

    begonnen = [e["knoten"] for e in ereignisse if e["art"] == "knoten_beginnt"]
    fertig = [e["knoten"] for e in ereignisse if e["art"] == "knoten_fertig"]

    assert begonnen, "kein einziger Knoten hat sich gemeldet"
    assert begonnen == fertig, (
        f"Knoten ohne Fertigmeldung: {sorted(set(begonnen) - set(fertig))}")


def test_die_nummerierung_zaehlt_wirklich_mit(tmp_path):
    """«Knoten 3 von 6» ist eine Auskunft. Waere `von` falsch, waere sie eine falsche."""
    _melde_mappe(tmp_path)
    ereignisse = []

    arbeitsgang.rechne(tmp_path, ausfuehrer=_attrappen(), melder=ereignisse.append)
    beginnt = [e for e in ereignisse if e["art"] == "knoten_beginnt"]

    assert [e["nummer"] for e in beginnt] == list(range(1, len(beginnt) + 1))
    assert all(e["von"] == len(beginnt) for e in beginnt)


def test_ein_kaputter_melder_reisst_den_lauf_nicht_mit(tmp_path):
    """*Ein Rueckruf, der die Rechnung mitreisst, ist teurer als gar keiner* — die
    GPU-Zeit ist schon bezahlt, wenn er zuschlaegt."""
    _melde_mappe(tmp_path)

    def boeser(_ereignis):
        raise RuntimeError("ich gehe immer kaputt")

    ergebnis = arbeitsgang.rechne(tmp_path, ausfuehrer=_attrappen(), melder=boeser)

    assert ergebnis["lauf"]["status"] in ("ok", "teilweise", "fehler")
    assert ergebnis["projekt"] is not None


def test_ohne_melder_wird_nichts_gerufen_und_nichts_ersetzt(tmp_path):
    """Die Gegenprobe: Der Weg ohne Zuschauer bleibt Zeile fuer Zeile der alte."""
    _melde_mappe(tmp_path)

    ergebnis = arbeitsgang.rechne(tmp_path, ausfuehrer=_attrappen())

    assert ergebnis["lauf"]["status"] in ("ok", "teilweise", "fehler")


def test_der_schrittzaehler_wird_nur_ohne_eigene_ausfuehrer_eingehaengt(tmp_path):
    """*Eine stille Ersetzung in einer mitgebrachten Tabelle waere genau die Sorte
    Ueberraschung, gegen die `fuehre_aus` die Tabelle ersetzen statt ergaenzen laesst.*

    Wer eine Attrappe fuer `render` mitbringt, bekommt sie — und nicht heimlich eine
    andere, die das echte Bildmodell laedt.
    """
    _melde_mappe(tmp_path)
    gerufen = []
    eigene = _attrappen()
    echt = eigene[ART_RENDER]

    def merk(*, knoten, eingaben, out_dir):
        gerufen.append(knoten.id)
        return echt(knoten=knoten, eingaben=eingaben, out_dir=out_dir)

    eigene[ART_RENDER] = merk
    arbeitsgang.rechne(tmp_path, ausfuehrer=eigene, melder=lambda e: None, cache=None)

    assert gerufen, "die mitgebrachte Render-Attrappe wurde NICHT gerufen"


def test_auch_ein_UEBERSPRUNGENER_knoten_meldet_fertig(tmp_path):
    """**Der Zweig, den die erste Fassung dieser Proben nicht betrat.**

    Faellt die Bildstufe, werden ihre Nachfolger uebersprungen — und der Rumpf verlaesst
    die Runde dann ueber ein `continue`, nicht ueber sein Ende. Genau dafuer steht das
    `finally` in `fuehre_aus`.

    Ohne diesen Fall waere die Probe darueber ein *Waechter an einer Stelle, an der der
    Fall nicht vorkommt* — und der uebersprungene Knoten bliebe in der Anzeige fuer immer
    am Rechnen.
    """
    _melde_mappe(tmp_path)
    ereignisse = []

    arbeitsgang.rechne(tmp_path, ausfuehrer=Werkbank(render_faellt=True).tabelle(),
                       melder=ereignisse.append)

    begonnen = [e["knoten"] for e in ereignisse if e["art"] == "knoten_beginnt"]
    fertig = {e["knoten"]: e for e in ereignisse if e["art"] == "knoten_fertig"}

    assert begonnen == list(fertig), (
        f"Knoten ohne Fertigmeldung: {sorted(set(begonnen) - set(fertig))}")
    uebersprungen = [e for e in fertig.values() if e["status"] == "uebersprungen"]
    assert uebersprungen, (
        "In diesem Lauf wurde kein Knoten uebersprungen — dann prueft diese Probe den "
        "Zweig nicht, fuer den sie geschrieben ist.")


def test_die_glb_und_die_bilder_stehen_relativ_in_der_mappe(tmp_path):
    """**Derselbe Fehler stand an drei Stellen** (Beweis 31, 21.09.2026): der Modellpfad,
    die umgewandelte glb und jeder Bildname.

    Bei den Bildern haengt mehr daran als die Lesbarkeit: Die Oberflaeche liefert nur
    Bilder **aus dem Projektordner** aus und kennt sie am relativen Namen. Ein absoluter
    Name waere dort ueberhaupt kein Bild — die Flaeche haette nie eines gezeigt.
    """
    heim = tmp_path / "home" / "jemand"
    heim.mkdir(parents=True)
    modell = heim / "m.glb"
    modell.write_bytes(b"glTF\x02\x00\x00\x00")
    mappe = heim / "projekt"

    p = projekt.neu(mappe, modell, name="Probe",
                    einstellungen={"prompt": "ein Haus", "up_axis": "Y", "schritte": 8})
    p["import"] = {"status": "ok", "weg": "ifc", "glb": "modell.glb", "format": ".ifc",
                   "treue": None, "hochachse": "Y", "hochachse_steht_fest": True,
                   "hinweise": []}
    (mappe / "modell.glb").write_bytes(b"glTF\x02\x00\x00\x00")
    projekt.speichere(p, mappe)

    arbeitsgang.rechne(mappe, ausfuehrer=Werkbank().tabelle())

    text = (mappe / projekt.PROJEKTDATEI).read_text(encoding="utf-8")
    assert "jemand" not in text and "<nutzer>" not in text, text[:300]

    fertig = projekt.oeffne(mappe)["projekt"]
    for b in fertig["bilder"]:
        assert not Path(b["bild"]).is_absolute(), b["bild"]
        assert (mappe / b["bild"]).is_file(), f"{b['bild']} zeigt ins Leere"
