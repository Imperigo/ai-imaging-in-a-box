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


# ------------------------- Der Zwischenspeicher auf dem Weg, den das Produkt geht
#
# GEMESSEN AM 21.09.2026: Drei Laeufe hintereinander auf derselben Mappe ergaben
# `cache_treffer=0`. Jeder Klick auf «Rechnen» rechnete den Blender-Lauf und das Bild neu,
# auch wenn sich nichts geaendert hatte.
#
# Der Zwischenspeicher ist gebaut und durch drei Beweise belegt (05, 23, 29). Auf dem Weg,
# den das Produkt geht, war er NICHT EINGESCHALTET — dieselbe Sorte Luecke wie beim
# Schrittzaehler am selben Tag.
#
#     Eine Faehigkeit, die ueber den Weg des Produkts nicht erreichbar ist, gibt es fuer
#     den Benutzer nicht.

class Zaehlbank(Werkbank):
    """Eine Werkbank, die mitzaehlt, wie oft jede Stufe wirklich gerufen wurde.

    *Ein Treffer im Speicher ist erst dann einer, wenn die Stufe NICHT gelaufen ist* —
    und das sagt nur der Zaehler, nicht die Zahl im Bericht.
    """

    def __init__(self, **kw):
        super().__init__(**kw)
        self.aufrufe = {"geometrie": 0, "multipass": 0, "render": 0, "qa": 0}

    def geometrie(self, **kw):
        self.aufrufe["geometrie"] += 1
        return super().geometrie(**kw)

    def multipass(self, **kw):
        self.aufrufe["multipass"] += 1
        return super().multipass(**kw)

    def render(self, **kw):
        self.aufrufe["render"] += 1
        return super().render(**kw)

    def qa(self, **kw):
        self.aufrufe["qa"] += 1
        return super().qa(**kw)


def test_der_zweite_lauf_rechnet_blender_und_bild_NICHT_neu(tmp_path):
    """**Die Probe, um die es geht.** Nicht die Zahl im Bericht, sondern der Zaehler:
    Die teuren Stufen duerfen beim zweiten Lauf gar nicht gerufen werden."""
    _melde_mappe(tmp_path)
    bank = Zaehlbank()

    arbeitsgang.rechne(tmp_path, ausfuehrer=bank.tabelle())
    arbeitsgang.rechne(tmp_path, ausfuehrer=bank.tabelle())

    assert bank.aufrufe["geometrie"] == 1, "die Geometrie wurde zweimal gerechnet"
    assert bank.aufrufe["multipass"] == 1, "Blender lief zweimal"
    assert bank.aufrufe["render"] == 1, "das Bild wurde zweimal gerechnet"


def test_eine_andere_schwelle_faellt_ein_neues_urteil(tmp_path):
    """**Die Probe, die ich zuerst falsch geschrieben hatte** — und die Berichtigung ist
    der interessantere Teil.

    Ich hatte behauptet, der QA-Knoten duerfe ueberhaupt nie aus dem Speicher kommen. Das
    ist nicht die Regel aus E20. Dort geht es um das **Basis-Urteil** eines
    Layer-2-Bildes: Das faellt ein Knoten im NEBENZWEIG, dessen Parameter nicht im Hash
    der Bildstufe stehen — abgelegt waere es ein Urteil aus einem anderen Lauf.

    Der QA-Knoten selbst haengt sehr wohl an seinen eigenen Parametern. Die wirkliche
    Frage lautet darum:

        *Aendert sich die Schwelle, faellt das Urteil neu?*

    Waere es anders, hiesse ein verschobener Riegel: dasselbe Urteil, andere Schwelle —
    und niemand saehe es dem Ergebnis an.
    """
    _melde_mappe(tmp_path)
    bank = Zaehlbank()

    arbeitsgang.rechne(tmp_path, ausfuehrer=bank.tabelle())
    arbeitsgang.rechne(tmp_path, ausfuehrer=bank.tabelle(), qa_schwelle=0.42)

    assert bank.aufrufe["qa"] == 2, (
        "Die Schwelle wurde verschoben und das Urteil kam aus dem Speicher — dann misst "
        "die Mappe gegen einen Riegel, den es nicht mehr gibt.")


def test_ohne_aenderung_bleibt_das_urteil_dasselbe(tmp_path):
    """Die Gegenprobe. Ein Urteil, das sich ohne Anlass aendert, waere schlimmer als eines,
    das steht — und ein QA-Knoten, der IMMER neu rechnet, verdeckte das."""
    _melde_mappe(tmp_path)
    bank = Zaehlbank()

    arbeitsgang.rechne(tmp_path, ausfuehrer=bank.tabelle())
    arbeitsgang.rechne(tmp_path, ausfuehrer=bank.tabelle())

    p = projekt.oeffne(tmp_path)["projekt"]
    assert len({b["geometrie_bestanden"] for b in p["bilder"]}) == 1


def test_eine_geaenderte_einstellung_rechnet_nur_das_noetige_neu(tmp_path):
    """Der ganze Zweck des Graphen: Ein neuer Prompt kostet das Bild, nicht Blender."""
    _melde_mappe(tmp_path)
    bank = Zaehlbank()

    arbeitsgang.rechne(tmp_path, ausfuehrer=bank.tabelle())
    arbeitsgang.rechne(tmp_path, ausfuehrer=bank.tabelle(), prompt="ein anderes Haus")

    assert bank.aufrufe["multipass"] == 1, "Blender lief wegen eines Prompts noch einmal"
    assert bank.aufrufe["render"] == 2, "das Bild haette neu gerechnet werden muessen"


def test_ohne_speicher_rechnet_jede_stufe_wieder(tmp_path):
    """Die Gegenprobe. `cache=None` heisst ausdruecklich **kein Speicher** — und ohne
    diese Probe waere ein Speicher, der IMMER trifft, ebenso gruen."""
    _melde_mappe(tmp_path)
    bank = Zaehlbank()

    arbeitsgang.rechne(tmp_path, ausfuehrer=bank.tabelle(), cache=None)
    arbeitsgang.rechne(tmp_path, ausfuehrer=bank.tabelle(), cache=None)

    assert bank.aufrufe["multipass"] == 2


def test_der_speicher_liegt_in_der_mappe(tmp_path):
    """Damit eine kopierte Mappe ihren Speicher mitnimmt. Ein Eintrag, dessen Dateien
    fehlen, wird ohnehin verworfen — ein Umzug kostet hoechstens einen neuen Lauf."""
    _melde_mappe(tmp_path)
    arbeitsgang.rechne(tmp_path, ausfuehrer=Werkbank().tabelle())

    assert (tmp_path / arbeitsgang.SPEICHERORDNER).is_dir()


# --------------------------------------------------- Eine Datei, ein Eintrag

def test_derselbe_lauf_zweimal_ergibt_EIN_bild_in_der_mappe(tmp_path):
    """*Eine Liste von Bildern, in der dieselbe Datei dreimal steht, ist keine Liste von
    Bildern — sie ist eine Liste von Klicks.*"""
    _melde_mappe(tmp_path)
    for _ in range(3):
        arbeitsgang.rechne(tmp_path, ausfuehrer=Werkbank().tabelle())

    p = projekt.oeffne(tmp_path)["projekt"]
    namen = [b["bild"] for b in p["bilder"]]

    assert len(namen) == len(set(namen)) == 1, namen


def test_die_laeufe_zaehlen_trotzdem_alle_mit(tmp_path):
    """**Die Gegenprobe, ohne die die vorige falsch waere.** Ein Lauf ist eine Tatsache
    ueber dieses Projekt; nur das ERZEUGNIS gibt es einmal."""
    _melde_mappe(tmp_path)
    for _ in range(3):
        arbeitsgang.rechne(tmp_path, ausfuehrer=Werkbank().tabelle())

    assert len(projekt.oeffne(tmp_path)["projekt"]["laeufe"]) == 3


def test_ein_anderes_bild_bekommt_einen_eigenen_eintrag(tmp_path):
    """Sonst waere die Regel «eine Datei, ein Eintrag» eine Regel «ein Bild, fertig»."""
    _melde_mappe(tmp_path)
    arbeitsgang.rechne(tmp_path, ausfuehrer=Werkbank().tabelle())
    arbeitsgang.rechne(tmp_path, ausfuehrer=Werkbank().tabelle(), prompt="etwas anderes")

    assert len(projekt.oeffne(tmp_path)["projekt"]["bilder"]) == 2


def test_ein_neu_gerechnetes_bild_bleibt_an_seiner_stelle(tmp_path):
    """**Diese Probe fehlte, und eine Mutationsprobe hat es gezeigt.**

    Der Quelltext behauptete «an derselben Stelle, nicht hinten angehaengt» — und eine
    Mutation, die den Eintrag ans Ende schiebt, blieb gruen.

        *Die Reihenfolge einer Bilderliste ist eine Auskunft: Sie sagt, was zuerst
        entstand. Wer sie beim Neurechnen umstellt, nimmt sie ihr — und es faellt
        niemandem auf, weil beide Listen dieselben Bilder enthalten.*
    """
    _melde_mappe(tmp_path)
    arbeitsgang.rechne(tmp_path, ausfuehrer=Werkbank().tabelle())
    erstes = projekt.oeffne(tmp_path)["projekt"]["bilder"][0]["bild"]

    arbeitsgang.rechne(tmp_path, ausfuehrer=Werkbank().tabelle(), prompt="ein zweites")
    zweites = projekt.oeffne(tmp_path)["projekt"]["bilder"][1]["bild"]

    # Und jetzt das ERSTE noch einmal — es muss vorn bleiben.
    arbeitsgang.rechne(tmp_path, ausfuehrer=Werkbank().tabelle())

    namen = [b["bild"] for b in projekt.oeffne(tmp_path)["projekt"]["bilder"]]
    assert namen == [erstes, zweites], namen


def test_das_erste_entstehen_bleibt_stehen_und_das_letzte_kommt_dazu(tmp_path):
    """Beide Zeitpunkte sagen etwas: der erste die Herkunft, der letzte die Aktualitaet
    des Urteils. Einen davon zu ueberschreiben verliert eine Auskunft."""
    _melde_mappe(tmp_path)
    arbeitsgang.rechne(tmp_path, ausfuehrer=Werkbank().tabelle())
    vorher = projekt.oeffne(tmp_path)["projekt"]["bilder"][0]

    arbeitsgang.rechne(tmp_path, ausfuehrer=Werkbank().tabelle())
    nachher = projekt.oeffne(tmp_path)["projekt"]["bilder"][0]

    assert nachher["erzeugt"] == vorher["erzeugt"], "die Herkunft wurde ueberschrieben"
    assert nachher["zuletzt_vermerkt"] >= vorher["zuletzt_vermerkt"]


# ---------------------------- Zwei Laeufe auf derselben Mappe — stiller Datenverlust
#
# GEMESSEN AM 21.09.2026: Zwei Laeufe gleichzeitig, beide meldeten Erfolg, und danach
# stand EIN Bild und EIN Lauf in der Mappe. Der zweite hatte den ersten ueberschrieben:
# Beide lesen die Mappe, beide schreiben sie, der letzte gewinnt.
#
#     Ein Fehlschlag, der wie ein Erfolg aussieht, wird nicht gefunden — er wird geglaubt.
#
# Und es ist kein Laborfall: Sobald ein iPad und ein Rechner am selben Projekt haengen,
# ist das Montagmorgen.

def test_der_zweite_gleichzeitige_lauf_wird_abgelehnt(tmp_path):
    """**Abgelehnt, nicht stillschweigend ueberschrieben.** Eine Ablehnung sieht man."""
    _melde_mappe(tmp_path)
    sperre = arbeitsgang._nimm_sperre(tmp_path)
    try:
        with pytest.raises(arbeitsgang.ArbeitsgangError) as fehler:
            arbeitsgang.rechne(tmp_path, ausfuehrer=Werkbank().tabelle())
        assert "läuft schon" in str(fehler.value)
    finally:
        sperre.unlink(missing_ok=True)


def test_nach_dem_lauf_ist_die_mappe_wieder_frei(tmp_path):
    """Sonst waere die erste Rechnung die letzte."""
    _melde_mappe(tmp_path)
    arbeitsgang.rechne(tmp_path, ausfuehrer=Werkbank().tabelle())

    assert not (tmp_path / arbeitsgang.SPERRDATEI).exists()
    arbeitsgang.rechne(tmp_path, ausfuehrer=Werkbank().tabelle(), prompt="noch einmal")


def test_auch_ein_GESCHEITERTER_lauf_gibt_die_mappe_frei(tmp_path):
    """**Der Fall, den man beim Bauen vergisst.**

    *Eine Sperre, die ein abgebrochener Lauf stehenlaesst, blockiert die Mappe fuer
    Stunden — und der naechste Mensch sieht nur, dass nichts geht.*
    """
    _melde_mappe(tmp_path)

    # ZWEI SORTEN SCHEITERN, und sie nehmen verschiedene Wege durch den Code.
    #
    # 1) Eine Stufe faellt. Das ist KEINE Ausnahme — `fuehre_aus` faengt sie ab
    #    (skip-on-error) und traegt den Fehlschlag als Tatsache ein.
    tabelle = Werkbank(render_faellt=True).tabelle()
    ergebnis = arbeitsgang.rechne(tmp_path, ausfuehrer=tabelle)
    assert ergebnis["lauf"]["status"] != "ok"
    assert not (tmp_path / arbeitsgang.SPERRDATEI).exists(), "Sperre nach Fehlschlag"

    # 2) `rechne` selbst wirft — hier, weil das Modell ein anderes geworden ist. Dieser
    #    Weg verlaesst die Funktion ueber eine Ausnahme, und auch dann muss das `finally`
    #    greifen.
    modell = tmp_path / "m.glb"
    modell.write_bytes(modell.read_bytes() + b"\n")
    with pytest.raises(arbeitsgang.ArbeitsgangError):
        arbeitsgang.rechne(tmp_path, ausfuehrer=Werkbank().tabelle())

    assert not (tmp_path / arbeitsgang.SPERRDATEI).exists(), "Sperre nach Ausnahme"


def test_eine_liegengebliebene_sperre_wird_uebernommen(tmp_path):
    """*Eine Sperre, die man nur von Hand loesen kann, wird von Hand geloescht — und zwar
    auch dann, wenn sie gerade zu Recht steht.*"""
    import os
    import time as zeit

    _melde_mappe(tmp_path)
    sperre = arbeitsgang._nimm_sperre(tmp_path)
    alt = zeit.time() - arbeitsgang.SPERRFRIST_S - 60
    os.utime(sperre, (alt, alt))

    ergebnis = arbeitsgang.rechne(tmp_path, ausfuehrer=Werkbank().tabelle())

    assert ergebnis["vermerkt"] >= 1


def test_eine_frische_sperre_wird_NICHT_uebernommen(tmp_path):
    """Die Gegenprobe. Ohne sie waere eine Sperre, die IMMER uebernommen wird, ebenso
    gruen — und der stille Datenverlust waere zurueck."""
    _melde_mappe(tmp_path)
    sperre = arbeitsgang._nimm_sperre(tmp_path)
    try:
        with pytest.raises(arbeitsgang.ArbeitsgangError):
            arbeitsgang.rechne(tmp_path, ausfuehrer=Werkbank().tabelle())
    finally:
        sperre.unlink(missing_ok=True)


def test_in_der_sperre_steht_kein_benutzer_und_kein_rechnername(tmp_path):
    """Regel 3 gilt auch fuer eine Datei, die nur ein paar Sekunden lebt — eine Mappe
    wandert mit, und wer sie weitergibt, gibt alles darin weiter."""
    import getpass
    import socket

    _melde_mappe(tmp_path)
    sperre = arbeitsgang._nimm_sperre(tmp_path)
    try:
        inhalt = sperre.read_text(encoding="utf-8")
        assert getpass.getuser() not in inhalt
        assert socket.gethostname() not in inhalt
        assert "begonnen" in inhalt and "pid" in inhalt
    finally:
        sperre.unlink(missing_ok=True)


def test_die_sperre_wird_vor_dem_oeffnen_genommen():
    """**Die Reihenfolge ist die ganze Wirkung.**

    Laege die Sperre spaeter, haette der zweite Lauf die Mappe schon gelesen, bevor der
    erste sie geschrieben hat — und genau diese veraltete Kopie wuerde er am Ende
    zurueckschreiben. Der Datenverlust waere derselbe, nur schwerer zu finden.
    """
    from pathlib import Path as P

    quelle = P(arbeitsgang.__file__).read_text(encoding="utf-8")
    kopf = quelle.split("    wurzel = Path(wurzel)\n    # DIE SPERRE ZUERST", 1)[1] \
                 .split("\ndef ", 1)[0]

    assert kopf.index("_nimm_sperre") < kopf.index("_rechne_gesperrt")
