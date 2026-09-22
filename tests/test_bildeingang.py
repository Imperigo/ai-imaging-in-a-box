"""Der Bild-Eingang: ein Bild zurück in eine Rechnung.

Woher dieser Test kommt
-----------------------
``docs/PLAN_BIS_FEBRUAR_2027.md`` nennt im November-Abschnitt den wichtigsten
Einzelposten des Monats:

    Der ``render``-Knoten hat heute keinen Bild-Eingang. Bilder können im Graphen nur
    verglichen und aufs Blatt gelegt werden — nie wieder in eine Rechnung zurück. Damit
    haben Schritt 5 (Hineinskizzieren) und Schritt 6 (Photoshop ersetzen) keinen Pfad,
    nicht einmal einen halben.

Der erste Test hier hält **genau diesen Befund** fest, damit er nicht zur Erinnerung
wird: Ein ``render``-Knoten, der von einem ``render``-Knoten gespeist wird, ist ein
Verdrahtungsfehler. Alles Weitere prüft den Weg, der seit dem 19.09.2026 daneben
existiert — ``bildquelle`` und ``nachrender``.

Ohne GPU, ohne Gewichte, ohne Blender
-------------------------------------
Das Bildmodell ist überall eine Attrappe, die den Parametersatz aufschreibt, den sie
bekommen hat. Genau darauf kommt es an: Die Frage dieses Moduls ist nicht, wie das Bild
aussieht, sondern **ob das Ausgangsbild überhaupt bis zum Modell durchkommt.**

Regel 3: Alle Bilder entstehen hier, aus zwei Handvoll Bytes. Kein echtes Projektbild,
kein absoluter Pfad mit einem Benutzernamen darin.
"""
from __future__ import annotations

import struct
import zlib
from collections import Counter
from pathlib import Path

import pytest

from aiimaging import kette, render
from aiimaging.graph import ArtefaktCache, Graph, Knoten
from aiimaging.kette import (
    ART_BILDQUELLE,
    ART_GEOMETRIE,
    ART_MULTIPASS,
    ART_NACHRENDER,
    ART_QA,
    ART_RENDER,
    KNOTEN_MULTIPASS,
    KNOTEN_RENDER,
    KettenError,
    baue_kette,
    fuehre_aus,
    haenge_nachrender_an,
    pruefe_kette,
)

#: Eine bbox in plausiblen Gebäudemassen — der Torwächter lässt sie durch.
BBOX_HAUS = [[0.0, 0.0, 0.0], [8.0, 5.0, 3.0]]


# ======================================================================================
# Werkzeug: winzige, aber echte PNG-Dateien
# ======================================================================================

def schreibe_png(pfad, werte=(0, 64, 128, 255)) -> Path:
    """Ein gültiges 2×2-Graustufen-PNG mit vorgegebenen Werten.

    **Echt und nicht behauptet**, weil ``bildlesen.pruefe_png`` die Blockprüfsummen liest
    und ein Textfile mit der Endung ``.png`` zu Recht ablehnt. Die Werte sind Argument,
    damit zwei Bilder unter **demselben Dateinamen** verschiedenen Inhalt haben können —
    das ist der Fall «jemand hat in das Bild hineingezeichnet und gespeichert».
    """
    breite = hoehe = 2
    roh = b"".join(b"\x00" + bytes(werte[z * breite:(z + 1) * breite]) for z in range(hoehe))

    def block(art, nutz):
        return (struct.pack(">I", len(nutz)) + art + nutz
                + struct.pack(">I", zlib.crc32(art + nutz) & 0xFFFFFFFF))

    pfad = Path(pfad)
    pfad.parent.mkdir(parents=True, exist_ok=True)
    pfad.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + block(b"IHDR", struct.pack(">IIBBBBB", breite, hoehe, 8, 0, 0, 0, 0))
        + block(b"IDAT", zlib.compress(roh))
        + block(b"IEND", b"")
    )
    return pfad


class Modellattrappe:
    """Ein Bildmodell, das nichts rechnet und alles aufschreibt.

    Die Naht ist ``render.rendere(auftrag, modell=…)``; das Modell wird mit dem
    Parametersatz gerufen und liefert einen Pfad zurück. Mehr braucht es nicht — was uns
    interessiert, ist ``parameter['beauty_png']``.
    """

    def __init__(self) -> None:
        self.gesehen: list[dict] = []

    def __call__(self, parameter: dict) -> dict:
        self.gesehen.append(dict(parameter))
        ziel = parameter["ausgabe_png"]
        schreibe_png(ziel, werte=(10, 20, 30, 40))
        return {"bild_png": ziel, "hinweise": [], "schritte_gerechnet": None}


# ======================================================================================
# 1 · Der Befund: der `render`-Knoten hat keinen Bild-Eingang
# ======================================================================================

def test_der_render_knoten_nimmt_kein_bild_entgegen(tmp_path):
    """**Der Befund aus dem Novemberplan, hier festgenagelt.**

    Ein zweiter ``render``-Knoten hinter dem ersten ist strukturell erlaubt — der
    Graph-Kern kennt keine Knotenarten und verdrahtet, was man ihm sagt. Er trägt
    trotzdem nichts: ``BEDARF[ART_RENDER]`` erwartet in Slot 0 eine Tiefenkarte, und ein
    Render liefert keine. Das ist die tote Kante des inneren Graphen.

    Der Test bleibt stehen, auch nachdem ``ART_NACHRENDER`` existiert. Er beschreibt
    keinen Mangel, den wir beheben wollen, sondern die **Grenze der bestehenden Art** —
    wer sie verschiebt, soll es hier sehen.
    """
    g = baue_kette(glb_path="/tmp/m.glb", up_axis="Y", prompt="ein Haus", qa=False)
    zweiter = Knoten(id="render2", art=ART_RENDER,
                     params=dict(g.knoten[KNOTEN_RENDER].params),
                     eingaenge=(KNOTEN_RENDER,))
    befunde = pruefe_kette(Graph(list(g.knoten.values()) + [zweiter]))

    schwer = [b for b in befunde if b["schwere"] == "error"]
    assert [b["knoten"] for b in schwer] == ["render2"]
    assert schwer[0]["befund"] == "fehlendes-feld"
    assert "depth_png" in schwer[0]["detail"]

    # Und im Lauf ist es genauso: Er scheitert, statt still ein Bild ohne Konditionierung
    # zu erzeugen.
    ausgaben = kette.AUSFUEHRER[ART_RENDER](
        knoten=zweiter, eingaben=[{"status": "ok", "bild_png": "/tmp/voriges.png"}],
        out_dir=tmp_path)
    assert ausgaben["status"] == "fehler"
    assert "depth_png" in ausgaben["error"]


# ======================================================================================
# 2 · Die Bildquelle: der Weg, auf dem ein Mensch hereinkommt
# ======================================================================================

def test_die_bildquelle_holt_eine_datei_in_den_graphen(tmp_path):
    zeichnung = schreibe_png(tmp_path / "zeichnung.png")
    knoten = Knoten(id="q", art=ART_BILDQUELLE, params={"bild_png": str(zeichnung)})
    arbeit = tmp_path / "arbeit"
    arbeit.mkdir()

    ausgaben = kette.AUSFUEHRER[ART_BILDQUELLE](knoten=knoten, eingaben=[], out_dir=arbeit)

    assert ausgaben["status"] == "ok", ausgaben.get("error")
    kopie = Path(ausgaben["bild_png"])
    assert kopie.is_file()
    assert kopie.read_bytes() == zeichnung.read_bytes(), "die Kopie ist inhaltsgleich"
    assert kopie.parent == arbeit, (
        "Die Kopie liegt im hashbenannten Arbeitsordner. Bliebe der Originalpfad stehen, "
        "zeigte ein alter Cache-Eintrag nach der nächsten Zeichnung auf neuen Inhalt.")
    assert ausgaben["herkunft"] == str(zeichnung)


def test_die_bildquelle_weist_eine_umbenannte_fremddatei_ab(tmp_path):
    """Existenz ist kein Beleg für Inhalt — und die Meldung soll hier fallen.

    Ohne diese Prüfung scheiterte erst die Bildbibliothek zwei Stufen später, mit einer
    Meldung, die die Datei nicht mehr nennt. Genau der Fehlerweg, den ``bruecke`` am
    19.09.2026 für ``model.glb`` geschlossen hat.
    """
    falsch = tmp_path / "zeichnung.png"
    falsch.write_bytes(b"\xff\xd8\xff\xe0 in Wahrheit ein JPEG")
    knoten = Knoten(id="q", art=ART_BILDQUELLE, params={"bild_png": str(falsch)})

    ausgaben = kette.AUSFUEHRER[ART_BILDQUELLE](knoten=knoten, eingaben=[],
                                                out_dir=tmp_path)
    assert ausgaben["status"] == "fehler"
    assert "PNG-Signatur" in ausgaben["error"]
    assert str(falsch) in ausgaben["error"], "die Meldung nennt die Datei"


def test_die_bildquelle_ohne_dateinamen_meldet_das(tmp_path):
    knoten = Knoten(id="q", art=ART_BILDQUELLE, params={})
    ausgaben = kette.AUSFUEHRER[ART_BILDQUELLE](knoten=knoten, eingaben=[],
                                                out_dir=tmp_path)
    assert ausgaben["status"] == "fehler" and "bild_png" in ausgaben["error"]


# ======================================================================================
# 3 · Der Nachrender: das Ausgangsbild kommt beim Auftrag an
# ======================================================================================

def _nachrender_knoten(**abweichungen) -> Knoten:
    params = {"prompt": "ein Balkon dazu", "negativ_prompt": "",
              "backbone": render.VORGABE_BACKBONE, "seed": 0, "schritte": 8,
              "controlnet_staerke": 0.8, "denoise": 0.35}
    params.update(abweichungen)
    return Knoten(id="nach", art=ART_NACHRENDER, params=params,
                  eingaenge=(KNOTEN_MULTIPASS, "q"))


def test_das_ausgangsbild_kommt_als_beauty_png_beim_modell_an(tmp_path):
    """**Die Kernzusicherung dieses Moduls.**

    ``beauty_png`` ist das Feld, über das ein Bild in ``render.rendere`` überhaupt an das
    Modell gelangt (``render._baue_parameter``: gesetzt heisst Modus ``image_edit``,
    und der Adapter übergibt es als ``image``). Käme hier ``None`` an, liefe ein zweiter
    Text-zu-Bild-Lauf, der nur so aussieht, als hätte er das Bild gesehen — und die
    Zeichnung wäre lautlos weg.
    """
    tiefe = schreibe_png(tmp_path / "tiefe.png")
    zeichnung = schreibe_png(tmp_path / "eingang.png", werte=(1, 2, 3, 4))
    modell = Modellattrappe()

    ausgaben = kette.nachrender_ausfuehrer(modell=modell)(
        knoten=_nachrender_knoten(),
        eingaben=[{"status": "ok", "depth_png": str(tiefe)},
                  {"status": "ok", "bild_png": str(zeichnung)}],
        out_dir=tmp_path)

    assert ausgaben["status"] == "ok", ausgaben.get("error")
    assert len(modell.gesehen) == 1
    gesehen = modell.gesehen[0]
    assert gesehen["beauty_png"] == str(zeichnung), "das Ausgangsbild erreicht das Modell"
    assert gesehen["depth_png"] == str(tiefe), "die Tiefenkarte bleibt die Konditionierung"
    assert gesehen["modus"] == render.MODUS_IMAGE_EDIT
    assert gesehen["denoise"] == pytest.approx(0.35), (
        "denoise bestimmt, wieviel vom Ausgangsbild überlebt — ohne ihn ist der "
        "Bild-Eingang ein Regler ohne Wirkung")
    assert ausgaben["ausgangsbild"] == str(zeichnung)


def test_der_nachrender_ohne_zweiten_eingang_meldet_das(tmp_path):
    ausgaben = kette.nachrender_ausfuehrer(modell=Modellattrappe())(
        knoten=_nachrender_knoten(),
        eingaben=[{"status": "ok", "depth_png": str(schreibe_png(tmp_path / "t.png"))}],
        out_dir=tmp_path)
    assert ausgaben["status"] == "fehler"
    assert "zwei Eingänge" in ausgaben["error"]


def test_der_nachrender_ohne_bild_in_slot_eins_meldet_das(tmp_path):
    """Kein Bild heisst kein Nachrender — **nicht** ein stiller Rückfall auf txt2img.

    Der Rückfall wäre der teure Fehler: Der Lauf gelänge, das Bild wäre da, und niemand
    sähe, dass das Ausgangsbild gefehlt hat.
    """
    ausgaben = kette.nachrender_ausfuehrer(modell=Modellattrappe())(
        knoten=_nachrender_knoten(),
        eingaben=[{"status": "ok", "depth_png": str(schreibe_png(tmp_path / "t.png"))},
                  {"status": "fehler", "error": "die Zeichnung war kein PNG"}],
        out_dir=tmp_path)
    assert ausgaben["status"] == "fehler"
    assert "bild_png" in ausgaben["error"]
    assert "die Zeichnung war kein PNG" in ausgaben["error"], (
        "der Grund des Vorgängers gehört in die Meldung, sonst sucht jemand hier")


# ======================================================================================
# 4 · Kommt das Bild beim Modell wirklich an? — die gemessene Antwort
# ======================================================================================

def test_bildeingang_lage_meldet_den_gemessenen_verlust():
    """Auf ``qwen-image-edit-2511`` fällt das Ausgangsbild weg — am Gerät gemessen.

    Der Witz daran, und er gehört in einen Test statt in eine Fussnote: Es ist
    ausgerechnet der Backbone, dessen Konditionierungsart «integriertes Edit» heisst.
    """
    lage = kette.bildeingang_lage("qwen-image-edit-2511")
    assert lage["traegt"] is False
    assert "auf-20260818-09" in lage["beleg"]


def test_bildeingang_lage_sagt_nicht_gemessen_statt_ja():
    """``None`` heisst NICHT GEMESSEN — weder bestanden noch durchgefallen.

    Für keinen Backbone steht hier ``True``. Das ist Absicht: Es gäbe erst nach einem
    Lauf an echten Gewichten etwas zu behaupten, und hier gibt es keine.

    Angepasst 22.09.2026: ``z-image-turbo`` stand hier und hielt damit den alten Stand
    fest — gemessen ist er seit ``auf-20260919-123`` (trägt NICHT). Sein Urteil prüft
    ``tests/test_bildeingang_register.py``; hier bleiben die ungemessenen Einträge.
    """
    for name in ("flux2-klein-4b", "qwen-image-2512", "sdxl-juggernaut"):
        lage = kette.bildeingang_lage(name)
        assert lage["traegt"] is None, name
        assert "NICHT GEMESSEN" in lage["beleg"], name

    assert kette.bildeingang_lage("gibtsnicht")["traegt"] is None


# ======================================================================================
# 5 · Der Bau: die Schleife hängt an einer bestehenden Kette
# ======================================================================================

def test_die_schleife_ist_verdrahtet():
    """**Leer heisst verdrahtet** — keine tote Kante, kein fehlender Slot."""
    g = baue_kette(glb_path="/tmp/m.glb", up_axis="Y", prompt="ein Haus")
    mit = haenge_nachrender_an(g, prompt="ein Balkon dazu",
                               eingangsbild="/tmp/zeichnung.png")
    assert pruefe_kette(mit) == []
    assert {k.art for k in mit.knoten.values()} <= set(kette.AUSFUEHRER), (
        "jede Art im Graphen hat eine Ausführerfunktion")


def test_der_nachrender_kann_auch_am_ersten_render_haengen():
    """Ohne Datei dazwischen: Maschine an Maschine, zwei Rechnungen hintereinander."""
    g = baue_kette(glb_path="/tmp/m.glb", up_axis="Y", prompt="ein Haus", qa=False)
    mit = haenge_nachrender_an(g, prompt="mehr Abendlicht")
    nach = mit.knoten["runde2-nachrender"]
    assert nach.eingaenge == (KNOTEN_MULTIPASS, KNOTEN_RENDER)
    assert pruefe_kette(mit) == []


def test_zwei_runden_hintereinander():
    """Der Weg Bild → Rechnung → Bild ist beliebig oft möglich, nicht einmal."""
    g = baue_kette(glb_path="/tmp/m.glb", up_axis="Y", prompt="ein Haus", qa=False)
    eins = haenge_nachrender_an(g, prompt="ein Balkon dazu",
                                eingangsbild="/tmp/a.png")
    zwei = haenge_nachrender_an(eins, prompt="jetzt Abendlicht",
                                bildquelle_knoten="runde2-nachrender")
    assert "runde3-nachrender" in zwei.knoten
    assert zwei.knoten["runde3-nachrender"].eingaenge == (KNOTEN_MULTIPASS,
                                                          "runde2-nachrender")
    assert pruefe_kette(zwei) == []


def test_der_urgraph_bleibt_unveraendert():
    """``Knoten`` ist ``frozen``; ein Graph, der sich unter dem Aufrufer ändert, hätte
    einen anderen Hash, als der Aufrufer glaubt."""
    g = baue_kette(glb_path="/tmp/m.glb", up_axis="Y", prompt="ein Haus")
    vorher = sorted(g.knoten)
    haenge_nachrender_an(g, prompt="ein Balkon dazu", eingangsbild="/tmp/z.png")
    assert sorted(g.knoten) == vorher


def test_der_nachrender_uebernimmt_die_einstellungen_des_renders():
    """Zwei Läufe mit stillschweigend verschiedenem Backbone sähen aus wie ein Vergleich
    und wären keiner."""
    g = baue_kette(glb_path="/tmp/m.glb", up_axis="Y", prompt="ein Haus",
                   backbone="sdxl-juggernaut", seed=4711, schritte=12,
                   controlnet_staerke=0.55, qa=False)
    mit = haenge_nachrender_an(g, prompt="ein Balkon dazu")
    p = mit.knoten["runde2-nachrender"].params
    assert p["backbone"] == "sdxl-juggernaut"
    assert p["seed"] == 4711 and p["schritte"] == 12
    assert p["controlnet_staerke"] == pytest.approx(0.55)


@pytest.mark.parametrize("kwargs, stueck", [
    ({"prompt": "  "}, "prompt"),
    ({"prompt": "x", "eingangsbild": "/tmp/a.png", "bildquelle_knoten": "render"},
     "zwei Ausgangsbilder"),
    ({"prompt": "x", "bildquelle_knoten": "gibtsnicht"}, "gibtsnicht"),
    ({"prompt": "x", "multipass_knoten": "gibtsnicht"}, "gibtsnicht"),
])
def test_der_bau_lehnt_unschluessiges_ab(kwargs, stueck):
    g = baue_kette(glb_path="/tmp/m.glb", up_axis="Y", prompt="ein Haus", qa=False)
    with pytest.raises(KettenError) as fehler:
        haenge_nachrender_an(g, **kwargs)
    assert stueck in str(fehler.value)


# ======================================================================================
# 6 · Der Lauf: eine neue Zeichnung löst eine neue Rechnung aus
# ======================================================================================

class Werkbank:
    """Zählende Attrappen für Geometrie, Multipass und Render.

    Sie schreiben **echte** Dateien, wenn auch winzige: ``fuehre_aus`` verwirft einen
    Cache-Eintrag, dessen versprochene Dateien nicht mehr existieren. Eine Attrappe, die
    nur Pfade behauptet, ergäbe bei jedem Lauf einen Fehltreffer — und der Test bewiese
    das Gegenteil dessen, was er soll.
    """

    def __init__(self, modell) -> None:
        self.aufrufe: Counter = Counter()
        self._modell = modell

    def tabelle(self) -> dict:
        return {
            ART_GEOMETRIE: self.geometrie,
            ART_MULTIPASS: self.multipass,
            ART_RENDER: self.render,
            ART_QA: self.qa,
            # ECHT, nicht nachgebaut: Bildquelle und Nachrender sind das, was hier
            # geprüft wird. Eine Attrappe an dieser Stelle prüfte die Attrappe.
            ART_BILDQUELLE: self.gezaehlt(ART_BILDQUELLE),
            ART_NACHRENDER: self.gezaehlt(
                ART_NACHRENDER, kette.nachrender_ausfuehrer(modell=self._modell)),
        }

    def gezaehlt(self, art, echt=None):
        echt = echt or kette.AUSFUEHRER[art]

        def huelle(*, knoten, eingaben, out_dir):
            self.aufrufe[art] += 1
            return echt(knoten=knoten, eingaben=eingaben, out_dir=out_dir)
        return huelle

    def geometrie(self, *, knoten, eingaben, out_dir):
        self.aufrufe[ART_GEOMETRIE] += 1
        glb = out_dir / "modell.glb"
        glb.write_text("glb", encoding="utf-8")
        return {"status": "ok", "glb_path": str(glb), "up_axis": "Y", "bbox": BBOX_HAUS}

    def multipass(self, *, knoten, eingaben, out_dir):
        self.aufrufe[ART_MULTIPASS] += 1
        tiefe = schreibe_png(out_dir / "tiefe_norm.png")
        return {"status": "ok", "depth_png": str(tiefe)}

    def render(self, *, knoten, eingaben, out_dir):
        self.aufrufe[ART_RENDER] += 1
        return {"status": "ok",
                "bild_png": str(schreibe_png(out_dir / "bild.png", werte=(9, 9, 9, 9)))}

    def qa(self, *, knoten, eingaben, out_dir):
        self.aufrufe[ART_QA] += 1
        return {"status": "ok", "bestanden": True, "score": 0.9}


def test_eine_neue_zeichnung_loest_eine_neue_rechnung_aus(tmp_path):
    """**Der eigentliche Beweis, dass die Schleife für einen Menschen taugt.**

    Der Ablauf ist der des Architekten: rendern, die PNG öffnen, einen Balkon
    hineinzeichnen, **unter demselben Namen speichern**, noch einmal rechnen lassen.

    Gezählt wird, nicht gemessen: Wird der Nachrender nach der zweiten Zeichnung ein
    zweites Mal gerufen? Eine Zusicherung auf die Laufzeit wäre eine Beobachtung mit
    Rauschen; die Zahl der Aufrufe ist der Beweis. Und die teuren Stufen davor dürfen
    **nicht** noch einmal laufen — ein Bild-Eingang, der die Geometrie neu rechnet, wäre
    unbenutzbar.
    """
    zeichnung = schreibe_png(tmp_path / "zeichnung.png", werte=(1, 1, 1, 1))
    modell = Modellattrappe()
    werkbank = Werkbank(modell)
    cache = ArtefaktCache(tmp_path / "cache")

    graph = haenge_nachrender_an(
        baue_kette(glb_path=str(tmp_path / "m.glb"), up_axis="Y", prompt="ein Haus",
                   qa=False),
        prompt="ein Balkon dazu", eingangsbild=str(zeichnung))
    (tmp_path / "m.glb").write_text("glb", encoding="utf-8")

    def starte():
        return fuehre_aus(graph, cache=cache, ausfuehrer=werkbank.tabelle(),
                          out_dir=tmp_path / "out")

    erster = starte()
    assert erster["status"] == "ok", erster["error"]
    assert werkbank.aufrufe[ART_NACHRENDER] == 1
    assert modell.gesehen[0]["beauty_png"].endswith("eingang.png")

    # Derselbe Graph, dieselbe Datei, nichts geändert: nichts wird neu gerechnet.
    starte()
    assert werkbank.aufrufe[ART_NACHRENDER] == 1, "ohne Änderung rechnet nichts neu"

    # Jetzt zeichnet jemand hinein und speichert unter DEMSELBEN Namen.
    schreibe_png(zeichnung, werte=(200, 200, 200, 200))
    dritter = starte()

    assert dritter["status"] == "ok", dritter["error"]
    assert werkbank.aufrufe[ART_BILDQUELLE] == 2, (
        "Die neue Zeichnung hat denselben Pfad und anderen Inhalt. Ginge nur der Pfad in "
        "den Hash, käme das Bild von vor der Zeichnung aus dem Zwischenspeicher zurück.")
    assert werkbank.aufrufe[ART_NACHRENDER] == 2, "die Zeichnung wird wirklich gerechnet"
    assert werkbank.aufrufe[ART_GEOMETRIE] == 1, "die Geometrie lief ein zweites Mal"
    assert werkbank.aufrufe[ART_MULTIPASS] == 1, "der Multipass lief ein zweites Mal"
    assert werkbank.aufrufe[ART_RENDER] == 1, "der erste Render lief ein zweites Mal"

    # Und das Modell hat wirklich das NEUE Bild gesehen, nicht bloss einen neuen Pfad.
    assert Path(modell.gesehen[-1]["beauty_png"]).read_bytes() == zeichnung.read_bytes()


# ======================================================================================
# Der Owner-Entscheid vom 19.09.2026: «nicht anwendbar» nach einem Handeingriff
# ======================================================================================

def test_nach_einem_handeingriff_ist_das_urteil_NICHT_ANWENDBAR(tmp_path):
    """**Die dritte Antwort, angewandt auf den Handeingriff** — Owner-Entscheid 19.09.2026.

    Zeichnet jemand einen Balkon ins Bild, den das Modell nicht hat, misst die
    Geometrie-QA genau die Abweichung, die der Mensch ABSICHTLICH erzeugt hat. Drei
    Antworten waren moeglich:

    * *Pruefen wie bisher* — dann faellt **jedes** bearbeitete Bild durch, und eine
      Warnung, die immer kommt, liest nach dem dritten Mal niemand mehr.
    * *Gar nicht pruefen* — dann traegt das Bild **keine Auskunft**, und spaeter sieht ihm
      niemand an, ob es je geprueft war.
    * **«Nicht anwendbar»** — gewaehlt.

    `bestanden` ist darum `None`: weder bestanden noch durchgefallen. Und `status` bleibt
    ausdruecklich `ok` — es ist nichts schiefgegangen, und ein Fehlerstatus liesse den
    Knoten uebersprungen aussehen.
    """
    urteil = kette.qa_ausfuehrer()(
        knoten=Knoten(id="qa", art=ART_QA, params={"schaetzer": "x", "schwelle": 0.65,
                                                   "hintergrund_strategie": "y"},
                      eingaenge=("m", "n")),
        eingaben=[{"depth_png": "soll.png"},
                  {"bild_png": "bild.png", kette.FELD_HANDEINGRIFF: True}],
        out_dir=tmp_path)

    assert urteil["bestanden"] is None, "weder bestanden noch durchgefallen"
    assert urteil["status"] == "ok", (
        "nichts ist schiefgegangen — ein Fehlerstatus liesse den Knoten uebersprungen "
        "aussehen")
    assert urteil["nicht_anwendbar"] is True
    assert "von Hand" in urteil["grund"]
    assert "nicht mehr die richtige" in urteil["grund"], (
        "der Grund muss sagen, WARUM die Frage nicht passt — nicht nur, DASS sie es nicht tut")


def test_ohne_handeingriff_wird_ganz_normal_gemessen(tmp_path):
    """Die Gegenprobe. *Ein Waechter, der alles durchwinkt, bewacht nichts.*

    Ohne sie waere «melde immer nicht anwendbar» ebenso gruen — und die Geometrie-QA
    haette aufgehoert zu messen, ohne dass es jemandem auffiele.
    """
    gerufen = []

    def lader(*a, **k):
        gerufen.append(1)
        raise RuntimeError("bis hierher und nicht weiter")

    with pytest.raises(Exception):
        kette.qa_ausfuehrer(_lader=lader)(
            knoten=Knoten(id="qa", art=ART_QA,
                          params={"schaetzer": "depth-anything-v2-small", "schwelle": 0.65,
                                  "hintergrund_strategie": "perzentil"},
                          eingaenge=("m", "n")),
            eingaben=[{"depth_png": "soll.png"}, {"bild_png": "bild.png"}],
            out_dir=tmp_path)


def test_die_bildquelle_setzt_den_vorbehalt_von_sich_aus(tmp_path):
    """Eine Datei von der Platte ist nicht aus dieser Rechnung.

    Ob wirklich jemand gezeichnet hat, ist damit NICHT gesagt — gesagt ist, dass es
    niemand ausschliessen kann. Fuer ein Urteil ueber die Geometrietreue ist das dasselbe.
    """
    quelle = schreibe_png(tmp_path / "gezeichnet.png")
    # Den Arbeitsordner legt sonst `fuehre_aus` an; hier wird der Knoten einzeln gerufen.
    (raus := tmp_path / "raus").mkdir()
    ergebnis = kette.AUSFUEHRER[ART_BILDQUELLE](
        knoten=Knoten(id="q", art=ART_BILDQUELLE, params={"bild_png": str(quelle)},
                      eingaenge=()),
        eingaben=[], out_dir=raus)

    assert ergebnis[kette.FELD_HANDEINGRIFF] is True


def test_der_vorbehalt_wird_vererbt_und_verfaellt_nicht_beim_weiterrechnen(tmp_path):
    """**Ein Vorbehalt, der beim Weiterrechnen verfaellt, ist keiner.**

    Zwei Runden Nachrender auf derselben Zeichnung: Der Vorbehalt muss die zweite Runde
    ueberleben. Ohne diese Probe koennte man ihn durch eine weitere Rechnung abstreifen —
    und das Bild saehe danach aus wie eines, an dem nie jemand war.
    """
    class Modell:
        def __call__(self, **k):
            return {"bild_png": str(tmp_path / "b.png"), "status": "ok", "error": None}

    def rendere(auftrag, **k):
        return {"status": "ok", "bild_png": auftrag.ausgabe_png, "error": None}

    ausfuehrer = kette.nachrender_ausfuehrer()
    knoten = Knoten(id="nr", art=ART_NACHRENDER, eingaenge=("m", "b"), params={
        "prompt": "p", "negativ_prompt": "", "backbone": "z-image-turbo", "seed": 1,
        "schritte": 4, "controlnet_staerke": 0.8, "denoise": 0.5})

    import unittest.mock as um
    with um.patch.object(render, "rendere", rendere):
        erste = ausfuehrer(knoten=knoten, out_dir=tmp_path / "a", eingaben=[
            {"depth_png": "d.png"},
            {"bild_png": "z.png", kette.FELD_HANDEINGRIFF: True}])
        assert erste[kette.FELD_HANDEINGRIFF] is True, "erste Runde traegt ihn"

        zweite = ausfuehrer(knoten=knoten, out_dir=tmp_path / "b", eingaben=[
            {"depth_png": "d.png"}, erste])
        assert zweite[kette.FELD_HANDEINGRIFF] is True, (
            "zweite Runde ebenso — sonst liesse er sich wegrechnen")


def test_ein_unberuehrter_render_traegt_den_vorbehalt_NICHT(tmp_path):
    """Die Gegenprobe zur Vererbung: Er wandert genau so weit wie der Handeingriff.

    Ohne sie waere «setze ihn immer» ebenso gruen — und dann waere jedes Bild des
    Projekts ungeprueft, auch das, an dem nie jemand war.
    """
    def rendere(auftrag, **k):
        return {"status": "ok", "bild_png": auftrag.ausgabe_png, "error": None}

    import unittest.mock as um
    with um.patch.object(render, "rendere", rendere):
        ergebnis = kette.nachrender_ausfuehrer()(
            knoten=Knoten(id="nr", art=ART_NACHRENDER, eingaenge=("m", "r"), params={
                "prompt": "p", "negativ_prompt": "", "backbone": "z-image-turbo",
                "seed": 1, "schritte": 4, "controlnet_staerke": 0.8, "denoise": 0.5}),
            out_dir=tmp_path,
            eingaben=[{"depth_png": "d.png"}, {"bild_png": "r.png"}])

    assert ergebnis[kette.FELD_HANDEINGRIFF] is False
