"""Zwei Schichten, und jedes Bild weiss, welche es ist.

Woher dieser Test kommt
-----------------------
**Owner-Entscheid 19.09.2026**, und er berichtigt den Bau vom selben Tag:

    «Es wird sozusagen Stufe zwei, Layer aktiv — also ein AI-Imaging-Layer, wo
    pixelbasierte Anpassungen gemacht werden koennen, also Lightroom- und
    Photoshop-Ersatz ueber AI Imaging. Das wird auf den Geometrielayer draufgesetzt,
    fuer Variantenstudien etc.»

Am Vormittag hatte die Kette gelernt, ein von Hand bearbeitetes Bild mit einem Vorbehalt
zu versehen: Die Geometrie-Pruefung meldet «nicht anwendbar». Das ist richtig und war zu
grob — mit dem eigenen Urteil verschwand auch das Urteil ueber die **Geometrie darunter**.
Bei einer Variantenstudie will genau das jemand wissen.

    **Ein Vorbehalt soll die Auskunft einschraenken, nicht sie loeschen.**

Was hier gehalten wird
----------------------
1. Jedes Bildergebnis sagt, welche Schicht es ist.
2. Das Urteil der Basis wird mitgefuehrt und ueberlebt beliebig viele Layer-2-Runden.
3. Die Basis ist benennbar — zwei Varianten auf derselben Basis sind als solche erkennbar.
4. Die beiden Urteile sind **nie verwechselbar**: Ein geerbtes Urteil ist kein eigenes.

Ohne GPU, ohne Gewichte, ohne Blender
-------------------------------------
Alles laeuft mit Attrappen. Regel 3: Jedes Bild entsteht hier, aus zwei Handvoll Bytes.
"""
from __future__ import annotations

import struct
import zlib
from pathlib import Path

import pytest

from aiimaging import kette
from aiimaging.graph import ArtefaktCache, Graph, Knoten
from aiimaging.kette import (
    ART_BILDQUELLE,
    ART_GEOMETRIE,
    ART_MULTIPASS,
    ART_NACHRENDER,
    ART_QA,
    ART_RENDER,
    BASIS_BESTANDEN,
    BASIS_BILD,
    BASIS_GRUND,
    BASIS_HERKUNFT,
    BASIS_KNOTEN,
    BASIS_URTEIL_VON,
    FELD_BASIS,
    FELD_HANDEINGRIFF,
    FELD_SCHICHT,
    HERKUNFT_BILDKETTE,
    HERKUNFT_GEOMETRIE,
    KNOTEN_MULTIPASS,
    KNOTEN_QA,
    KNOTEN_RENDER,
    SCHICHT_AI_IMAGING,
    SCHICHT_GEOMETRIE,
    baue_kette,
    fuehre_aus,
    haenge_nachrender_an,
    schicht_von,
    schichtbefund,
)

BBOX_HAUS = [[0.0, 0.0, 0.0], [8.0, 5.0, 3.0]]


def schreibe_png(pfad, werte=(0, 64, 128, 255)) -> Path:
    """Ein gueltiges 2x2-Graustufen-PNG. Echt und nicht behauptet — `bildlesen.pruefe_png`
    liest die Blockpruefsummen und weist ein Textfile mit der Endung `.png` zu Recht ab."""
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
    """Ein Bildmodell, das nichts rechnet und eine echte Datei hinterlaesst."""

    def __call__(self, parameter: dict) -> dict:
        ziel = parameter["ausgabe_png"]
        schreibe_png(ziel, werte=(10, 20, 30, 40))
        return {"bild_png": ziel, "hinweise": [], "schritte_gerechnet": None}


class Werkbank:
    """Attrappen fuer die teuren Stufen; Bildquelle und Nachrender laufen **echt**.

    Das Urteil der QA-Attrappe haengt an der Schwelle im Knoten (``schwelle < 0.8``).
    Das ist kein Spieltrieb, sondern die Naht fuer die Mutationsprobe weiter unten: Sie
    braucht **zwei Laeufe, in denen dieselbe Bildstufe aus dem Speicher kommt und das
    Urteil trotzdem ein anderes ist.**
    """

    def __init__(self, *, bestanden=None) -> None:
        self._bestanden = bestanden

    def tabelle(self) -> dict:
        return {
            ART_GEOMETRIE: self.geometrie,
            ART_MULTIPASS: self.multipass,
            ART_RENDER: self.render,
            ART_QA: self.qa,
            ART_BILDQUELLE: kette.AUSFUEHRER[ART_BILDQUELLE],
            ART_NACHRENDER: kette.nachrender_ausfuehrer(modell=Modellattrappe()),
        }

    def geometrie(self, *, knoten, eingaben, out_dir):
        glb = out_dir / "modell.glb"
        glb.write_text("glb", encoding="utf-8")
        return {"status": "ok", "glb_path": str(glb), "up_axis": "Y", "bbox": BBOX_HAUS}

    def multipass(self, *, knoten, eingaben, out_dir):
        return {"status": "ok", "depth_png": str(schreibe_png(out_dir / "tiefe.png"))}

    def render(self, *, knoten, eingaben, out_dir):
        # BEWUSST OHNE `schicht`: So sieht ein Eintrag aus, der vor dem 19.09.2026
        # entstanden ist. Der Rueckfall in `schicht_von` muss ihn richtig einordnen.
        return {"status": "ok",
                "bild_png": str(schreibe_png(out_dir / "bild.png", werte=(9, 9, 9, 9)))}

    def qa(self, *, knoten, eingaben, out_dir):
        bestanden = (self._bestanden if self._bestanden is not None
                     else knoten.params["schwelle"] < 0.8)
        return {"status": "ok", "bestanden": bestanden, "score": 0.91}


def baue_lauf(tmp_path, *, zeichnung=None, qa_schwelle=0.65, runden=1, **kwargs):
    """Die Kette mit QA, dahinter ``runden`` Layer-2-Runden auf einer Zeichnung."""
    glb = tmp_path / "m.glb"
    glb.write_text("glb", encoding="utf-8")
    graph = baue_kette(glb_path=str(glb), up_axis="Y", prompt="ein Haus",
                       qa_schwelle=qa_schwelle, **kwargs)
    if zeichnung is not None:
        graph = haenge_nachrender_an(graph, prompt="waermeres Licht",
                                     eingangsbild=str(zeichnung), id_vorsatz="runde2")
        for n in range(3, 3 + runden - 1):
            graph = haenge_nachrender_an(graph, prompt=f"Variante {n}",
                                         bildquelle_knoten=f"runde{n - 1}-nachrender",
                                         id_vorsatz=f"runde{n}")
    return graph


# ======================================================================================
# 1 · Jedes Bildergebnis sagt, welche Schicht es ist
# ======================================================================================

def test_ein_render_ist_layer_eins(tmp_path):
    """Der Normalfall. Aus dem Modell gerechnet, gegen die Tiefenkarte messbar."""
    tiefe = schreibe_png(tmp_path / "tiefe.png")
    ausgaben = kette.render_ausfuehrer(modell=Modellattrappe())(
        knoten=Knoten(id="r", art=ART_RENDER, eingaenge=("m",), params={
            "prompt": "p", "negativ_prompt": "", "backbone": "z-image-turbo", "seed": 0,
            "schritte": 4, "controlnet_staerke": 0.8, "denoise": 0.6,
            "nutze_beauty": False}),
        eingaben=[{"status": "ok", "depth_png": str(tiefe)}], out_dir=tmp_path)

    assert ausgaben[FELD_SCHICHT] == SCHICHT_GEOMETRIE


def test_eine_bildquelle_ist_layer_zwei(tmp_path):
    """Eine Datei von der Platte ist nicht gegen die Tiefenkarte dieses Laufs gerechnet.

    Hier faengt der AI-Imaging-Layer an — und zwar genau hier und keine Stufe frueher.
    """
    quelle = schreibe_png(tmp_path / "gezeichnet.png")
    (raus := tmp_path / "raus").mkdir()
    ausgaben = kette.AUSFUEHRER[ART_BILDQUELLE](
        knoten=Knoten(id="q", art=ART_BILDQUELLE, params={"bild_png": str(quelle)}),
        eingaben=[], out_dir=raus)

    assert ausgaben[FELD_SCHICHT] == SCHICHT_AI_IMAGING
    assert ausgaben[FELD_HANDEINGRIFF] is True


@pytest.mark.parametrize("bildeingang, erwartet", [
    ({"bild_png": "r.png"}, SCHICHT_GEOMETRIE),
    ({"bild_png": "z.png", FELD_HANDEINGRIFF: True}, SCHICHT_AI_IMAGING),
])
def test_der_nachrender_liest_seine_schicht_aus_dem_eingang(tmp_path, bildeingang,
                                                            erwartet):
    """**Die Gegenprobe zur Schichtzuweisung, in beide Richtungen.**

    Ein Nachrender auf einem unberuehrten Render rechnet weiter gegen dieselbe
    Tiefenkarte — sein Bild bleibt messbar, also Layer 1. Einer auf einer Zeichnung
    rechnet auf Pixeln, die niemand mehr gegen das Modell halten kann: Layer 2.

    Ohne den ersten Fall waere «setze immer Layer 2» ebenso gruen, und jedes Bild des
    Projekts waere ungeprueft. Ohne den zweiten waere «setze immer Layer 1» gruen, und die
    zweite Schicht gaebe es gar nicht.
    """
    tiefe = schreibe_png(tmp_path / "tiefe.png")
    bild = schreibe_png(tmp_path / bildeingang["bild_png"])
    ausgaben = kette.nachrender_ausfuehrer(modell=Modellattrappe())(
        knoten=Knoten(id="n", art=ART_NACHRENDER, eingaenge=("m", "b"), params={
            "prompt": "p", "negativ_prompt": "", "backbone": "z-image-turbo", "seed": 0,
            "schritte": 4, "controlnet_staerke": 0.8, "denoise": 0.4}),
        eingaben=[{"status": "ok", "depth_png": str(tiefe)},
                  dict(bildeingang, bild_png=str(bild))],
        out_dir=tmp_path)

    assert ausgaben[FELD_SCHICHT] == erwartet


def test_ein_alter_speichereintrag_ohne_das_feld_wird_trotzdem_eingeordnet():
    """Der Rueckfall in ``schicht_von``, und warum er kein Schoenheitsfehler ist.

    Eintraege im Zwischenspeicher, die vor dem 19.09.2026 entstanden sind, tragen das
    Feld nicht. Ohne Rueckfall saehe ein bearbeitetes Bild nach einem Neustart aus wie
    ein gerechnetes — und genau das ist der Fehler, gegen den die ganze Schichtung steht.
    """
    assert schicht_von(ART_BILDQUELLE, {}) == SCHICHT_AI_IMAGING
    assert schicht_von(ART_NACHRENDER, {FELD_HANDEINGRIFF: True}) == SCHICHT_AI_IMAGING
    assert schicht_von(ART_NACHRENDER, {}) == SCHICHT_GEOMETRIE
    assert schicht_von(ART_RENDER, {}) == SCHICHT_GEOMETRIE


# ======================================================================================
# 2 · Das Urteil der Basis — mitgefuehrt, benannt, und nie das eigene
# ======================================================================================

def test_ein_geerbtes_urteil_ist_nie_ein_eigenes(tmp_path):
    """**Die Falle, die der Owner benannt haben wollte** — und die Probe, die sie ausschliesst.

    Die Basis hat bestanden. Das Layer-2-Bild darauf darf deshalb an **keiner** Stelle
    aussehen, als haette es selbst die Geometriepruefung bestanden. Geprueft wird nicht
    ein Feld, sondern **jedes** Feld, das wie ein Urteil heisst: Wer dem Ergebnis kuenftig
    ein zweites ``bestanden`` hinzufuegt, faellt hier auf.
    """
    graph = baue_lauf(tmp_path, zeichnung=schreibe_png(tmp_path / "gezeichnet.png"))
    lauf = fuehre_aus(graph, ausfuehrer=Werkbank().tabelle(), out_dir=tmp_path / "out")
    assert lauf["status"] == "ok", lauf["error"]

    eigenes = lauf["knoten"][KNOTEN_QA]["ausgaben"]
    assert eigenes["bestanden"] is True, "die Basis selbst hat bestanden"

    nachrender = lauf["knoten"]["runde2-nachrender"]["ausgaben"]
    basis = nachrender[FELD_BASIS]
    assert nachrender[FELD_SCHICHT] == SCHICHT_AI_IMAGING
    assert basis[BASIS_BESTANDEN] is True, "das Urteil der Basis wird mitgefuehrt"

    # ── Und nun die Falle: Nirgends darf daraus ein eigenes Urteil werden. ──────────
    for feld, wert in nachrender.items():
        if "bestanden" in feld:
            assert wert is None, (
                f"Das Feld {feld!r} des Layer-2-Bildes traegt {wert!r}. Ein geerbtes "
                f"Urteil ist kein eigenes — sieht es je so aus, als haette Layer 2 die "
                f"Geometriepruefung bestanden, ist der Bau falsch.")
    assert "bestanden" not in basis, (
        "Der Basis-Block darf kein Feld 'bestanden' haben. Wer ihn flach zieht, bekaeme "
        "sonst zwei gleichnamige Urteile nebeneinander — genau die Verwechslung, gegen "
        "die dieses Projekt seit Wochen anschreibt.")


def test_die_pruefung_eines_layer_zwei_bildes_meldet_beides_getrennt(tmp_path):
    """«Nicht anwendbar» fuer die eigene Geometrie — **und** das Urteil der Basis daneben.

    Das ist der ganze Sinn der Berichtigung: Die Auskunft wird eingeschraenkt, nicht
    geloescht. Wer das Bild ansieht, erfaehrt zweierlei, und zwar unter zwei Namen.
    """
    graph = baue_lauf(tmp_path, zeichnung=schreibe_png(tmp_path / "gezeichnet.png"))
    graph = Graph(list(graph.knoten.values()) + [Knoten(
        id="runde2-qa", art=ART_QA, eingaenge=(KNOTEN_MULTIPASS, "runde2-nachrender"),
        params=dict(graph.knoten[KNOTEN_QA].params))])

    # DIE ECHTE QA-STUFE FUER DAS LAYER-2-BILD, die Attrappe fuer das Layer-1-Bild: Die
    # erste braucht keine Gewichte (sie misst ja gerade nicht), die zweite wuerde ohne
    # GPU und Gewichte scheitern — und ein gescheiterter Vorgaenger haette kein Urteil,
    # das sich vererben liesse. Geprueft wird hier also der Zweig, um den es geht.
    werkbank = Werkbank()
    echt = kette.qa_ausfuehrer()

    def qa(*, knoten, eingaben, out_dir):
        if eingaben[1].get(FELD_HANDEINGRIFF):
            return echt(knoten=knoten, eingaben=eingaben, out_dir=out_dir)
        return werkbank.qa(knoten=knoten, eingaben=eingaben, out_dir=out_dir)

    lauf = fuehre_aus(graph, ausfuehrer={**werkbank.tabelle(), ART_QA: qa},
                      out_dir=tmp_path / "out")
    urteil = lauf["knoten"]["runde2-qa"]["ausgaben"]

    assert urteil["bestanden"] is None, "das EIGENE Urteil: weder bestanden noch durch"
    assert urteil["nicht_anwendbar"] is True
    assert urteil["beurteilte_schicht"] == SCHICHT_AI_IMAGING
    assert urteil[FELD_BASIS][BASIS_BESTANDEN] is True, "das Urteil der BASIS"
    assert urteil[FELD_BASIS][BASIS_KNOTEN] == KNOTEN_RENDER, "und es ist benannt"
    assert "basis" in urteil["grund"].lower(), (
        "der Klartext muss sagen, dass das zweite Urteil das der Basis ist — sonst "
        "steht eine Zahl da, die jeder fuer das eigene Urteil haelt")


def test_layer_eins_bekommt_keinen_basis_block(tmp_path):
    """Er **ist** die Basis. Ein Block mit lauter ``None`` saehe aus wie «Basis vorhanden,
    nichts gemessen» — etwas ganz anderes."""
    graph = baue_lauf(tmp_path, zeichnung=schreibe_png(tmp_path / "gezeichnet.png"))
    lauf = fuehre_aus(graph, ausfuehrer=Werkbank().tabelle(), out_dir=tmp_path / "out")

    assert lauf["knoten"][KNOTEN_RENDER]["ausgaben"][FELD_BASIS] is None
    assert lauf["knoten"][KNOTEN_RENDER]["ausgaben"][FELD_SCHICHT] == SCHICHT_GEOMETRIE
    assert lauf["knoten"][KNOTEN_QA]["ausgaben"][FELD_BASIS] is None
    assert lauf["knoten"][KNOTEN_QA]["ausgaben"]["bestanden"] is True, (
        "und die gewoehnliche Kette geht aus wie zuvor — die Schichtung legt daneben, "
        "nie darueber")


def test_eine_durchgefallene_basis_wird_weitergereicht(tmp_path):
    """**Die unangenehme Auskunft, und sie wird nicht unterschlagen.**

    Wer acht Varianten auf einer Geometrie rechnet, die die Pruefung nicht bestanden hat,
    soll das an jeder der acht sehen. Ein Basisurteil, das nur im guten Fall mitkaeme,
    waere Werbung und keine Pruefung.
    """
    graph = baue_lauf(tmp_path, zeichnung=schreibe_png(tmp_path / "gezeichnet.png"))
    lauf = fuehre_aus(graph, ausfuehrer=Werkbank(bestanden=False).tabelle(),
                      out_dir=tmp_path / "out")

    basis = lauf["knoten"]["runde2-nachrender"]["ausgaben"][FELD_BASIS]
    assert basis[BASIS_BESTANDEN] is False
    assert basis[BASIS_KNOTEN] == KNOTEN_RENDER
    assert basis[BASIS_URTEIL_VON] == KNOTEN_QA


def test_eine_ungemessene_basis_ist_None_und_nicht_False(tmp_path):
    """**Die dritte Antwort bleibt.** Ohne QA-Knoten gibt es kein Urteil — und ``None``
    heisst NICHT GEMESSEN, nicht «durchgefallen» und nicht «leer».

    Ein ``False`` an dieser Stelle waere die teuerste Verwechslung dieses Projekts in
    klein: eine ungemessene Geometrie, die wie eine durchgefallene aussieht.
    """
    graph = baue_lauf(tmp_path, zeichnung=schreibe_png(tmp_path / "gezeichnet.png"),
                      qa=False)
    lauf = fuehre_aus(graph, ausfuehrer=Werkbank().tabelle(), out_dir=tmp_path / "out")

    basis = lauf["knoten"]["runde2-nachrender"]["ausgaben"][FELD_BASIS]
    assert basis[BASIS_KNOTEN] == KNOTEN_RENDER, "die Basis selbst ist bekannt"
    assert basis[BASIS_BESTANDEN] is None
    assert basis[BASIS_URTEIL_VON] is None
    assert "NICHT GEMESSEN" in basis[BASIS_GRUND], (
        "und es steht im Klartext da — eine Leerstelle ohne Grund liest sich wie ein "
        "Versehen")


def test_die_basis_bleibt_die_erste_ueber_mehrere_runden(tmp_path):
    """Layer 2 auf Layer 2 auf Layer 2 — die Basis bleibt die **erste**.

    Die vorige Runde ist selbst Layer 2 und hat gar kein eigenes Geometrie-Urteil. Wer sie
    als Basis naehme, reichte ein Urteil weiter, das sie nur geerbt hat: Hoerensagen
    zweiter Ordnung, mit jeder Runde eine Quelle weiter weg. Gemessen wurde genau einmal.
    """
    graph = baue_lauf(tmp_path, zeichnung=schreibe_png(tmp_path / "gezeichnet.png"),
                      runden=3)
    lauf = fuehre_aus(graph, ausfuehrer=Werkbank().tabelle(), out_dir=tmp_path / "out")
    assert lauf["status"] == "ok", lauf["error"]

    for runde in ("runde2-nachrender", "runde3-nachrender", "runde4-nachrender"):
        ausgaben = lauf["knoten"][runde]["ausgaben"]
        assert ausgaben[FELD_SCHICHT] == SCHICHT_AI_IMAGING, runde
        assert ausgaben[FELD_BASIS][BASIS_KNOTEN] == KNOTEN_RENDER, (
            f"{runde} muesste auf {KNOTEN_RENDER!r} zeigen, zeigt aber auf "
            f"{ausgaben[FELD_BASIS][BASIS_KNOTEN]!r} — die Basis ist weitergewandert")
        assert ausgaben[FELD_BASIS][BASIS_BESTANDEN] is True

    # Die spaeteren Runden haengen an der Bildkette und muessen den Umweg ueber die
    # Geometrie gar nicht erst gehen — der Unterschied steht in der Herkunft.
    assert (lauf["knoten"]["runde2-nachrender"]["ausgaben"][FELD_BASIS][BASIS_HERKUNFT]
            == HERKUNFT_GEOMETRIE), (
        "Die Zeichnung kam von der Platte: Die Bildkette reisst dort, und die Basis wird "
        "ueber die gemeinsame Geometrie bestimmt.")


def test_zwei_varianten_auf_derselben_basis_sind_als_solche_erkennbar(tmp_path):
    """**Ohne das taugt der Begriff «Variantenstudie» nicht.**

    Acht Bildvarianten auf derselben geprueften Geometrie: Jede muss dieselbe Basis
    nennen — denselben Knoten **und** dasselbe Bild. Ein Urteil ohne Herkunft waere eine
    Behauptung.
    """
    zeichnung = schreibe_png(tmp_path / "gezeichnet.png")
    graph = baue_lauf(tmp_path, zeichnung=zeichnung)
    for n in range(3, 10):
        graph = haenge_nachrender_an(graph, prompt=f"Variante {n}",
                                     bildquelle_knoten="runde2-bildquelle",
                                     id_vorsatz=f"runde{n}")
    lauf = fuehre_aus(graph, ausfuehrer=Werkbank().tabelle(), out_dir=tmp_path / "out")
    assert lauf["status"] == "ok", lauf["error"]

    varianten = [kid for kid in lauf["knoten"] if kid.endswith("-nachrender")]
    assert len(varianten) == 8
    basen = {lauf["knoten"][kid]["ausgaben"][FELD_BASIS][BASIS_KNOTEN]
             for kid in varianten}
    bilder = {lauf["knoten"][kid]["ausgaben"][FELD_BASIS][BASIS_BILD]
              for kid in varianten}
    assert basen == {KNOTEN_RENDER}, "alle acht stehen auf derselben Basis"
    assert len(bilder) == 1 and bilder != {None}, (
        "und die Basis ist nicht nur benannt, sondern auf ein Bild gezeigt")


def test_die_basis_bleibt_offen_wenn_sie_mehrdeutig_waere(tmp_path):
    """**Ein geratenes Urteil ist schlimmer als keines.**

    Stehen zwei Layer-1-Bilder auf derselben Geometrie, waere jede Wahl geraten. Ohne
    diese Probe koennte der Bau sich stillschweigend das erstbeste Bild nehmen — und die
    Auskunft saehe genauso aus wie eine belegte.
    """
    graph = baue_lauf(tmp_path, zeichnung=schreibe_png(tmp_path / "gezeichnet.png"))
    zweiter = Knoten(id="render-b", art=ART_RENDER, eingaenge=(KNOTEN_MULTIPASS,),
                     params=dict(graph.knoten[KNOTEN_RENDER].params, seed=7))
    lauf = fuehre_aus(Graph(list(graph.knoten.values()) + [zweiter]),
                      ausfuehrer=Werkbank().tabelle(), out_dir=tmp_path / "out")

    basis = lauf["knoten"]["runde2-nachrender"]["ausgaben"][FELD_BASIS]
    assert basis[BASIS_KNOTEN] is None
    assert basis[BASIS_BESTANDEN] is None
    assert "geraten" in basis[BASIS_GRUND]
    assert KNOTEN_RENDER in basis[BASIS_GRUND] and "render-b" in basis[BASIS_GRUND], (
        "der Grund nennt die Kandidaten — sonst kann niemand entscheiden, was zu tun ist")


def test_ueber_die_bildkette_ohne_umweg_ueber_die_geometrie(tmp_path):
    """Steht das Layer-2-Bild **im** Graphen auf seiner Basis, ist sie direkt nachweisbar.

    Heute kommt dieser Fall nicht vor, und das ist kein Versehen: Layer 2 entsteht
    derzeit nur aus einem Handeingriff, und der kommt als Datei von der Platte — die
    Bildkette reisst dort zwangslaeufig. Der Owner hat am 19.09.2026 aber eine dritte
    Ursache benannt, die es geben wird: **eine Rechnung ohne Modell.** Die saesse direkt
    auf einem Layer-1-Bild, ohne Umweg ueber die Platte.

    Dieser Test spielt genau das vor — eine Stufe, die ihr Ergebnis als Stufe zwei
    ausweist, ohne dass ein Mensch eine Datei angefasst hat. Er haelt den Weg offen, der
    sonst ungeprueft im Code staende, und er zeigt den Unterschied, auf den es ankommt:
    In der Herkunft steht die **Bildkette** (belegt) und nicht die gemeinsame Geometrie
    (plausibel zugeordnet).
    """
    werkbank = Werkbank()
    echt = werkbank.tabelle()[ART_NACHRENDER]

    def rechnung_ohne_modell(*, knoten, eingaben, out_dir):
        # Die kuenftige dritte Ursache, als Attrappe: pixelbasiert gerechnet, und das
        # Ergebnis sagt es von sich aus — nicht geerbt, nicht von Hand erklaert.
        return dict(echt(knoten=knoten, eingaben=eingaben, out_dir=out_dir),
                    **{FELD_SCHICHT: SCHICHT_AI_IMAGING})

    graph = haenge_nachrender_an(baue_lauf(tmp_path), prompt="Lichtstimmung",
                                 bildquelle_knoten=KNOTEN_RENDER, id_vorsatz="stufe2")
    lauf = fuehre_aus(graph, ausfuehrer={**werkbank.tabelle(),
                                         ART_NACHRENDER: rechnung_ohne_modell},
                      out_dir=tmp_path / "out")
    assert lauf["status"] == "ok", lauf["error"]

    ausgaben = lauf["knoten"]["stufe2-nachrender"]["ausgaben"]
    basis = ausgaben[FELD_BASIS]
    assert ausgaben[FELD_SCHICHT] == SCHICHT_AI_IMAGING
    assert basis[BASIS_KNOTEN] == KNOTEN_RENDER
    assert basis[BASIS_HERKUNFT] == HERKUNFT_BILDKETTE, (
        "hier ist die Basis belegt und nicht nur plausibel zugeordnet")
    assert basis[BASIS_BESTANDEN] is True


# ======================================================================================
# 3 · Mutationsproben
# ======================================================================================

def test_das_basisurteil_kommt_aus_DIESEM_lauf_und_nie_aus_dem_speicher(tmp_path):
    """**Die Mutationsprobe, die den ganzen Bauplatz erklaert.**

    Zwei Laeufe, ein Zwischenspeicher. Zwischen ihnen aendert sich **nur die Schwelle der
    Pruefung**, und die QA-Attrappe urteilt daraufhin anders. Die Bildstufen sind davon
    unberuehrt: Ihr Hash enthaelt die QA-Parameter nicht, sie kommen aus dem Speicher.

    Waere das Basisurteil im Knotenergebnis mitgespeichert worden, traege der zweite Lauf
    das Urteil des ersten — ein Urteil aus einem anderen Lauf, hinter einer unveraenderten
    Zahl. Genau darum wird der Basis-Block nach dem Lauf frisch gelesen und nie abgelegt.
    """
    zeichnung = schreibe_png(tmp_path / "gezeichnet.png")
    cache = ArtefaktCache(tmp_path / "cache")
    werkbank = Werkbank()

    erster = fuehre_aus(baue_lauf(tmp_path, zeichnung=zeichnung, qa_schwelle=0.65),
                        cache=cache, ausfuehrer=werkbank.tabelle(),
                        out_dir=tmp_path / "out")
    zweiter = fuehre_aus(baue_lauf(tmp_path, zeichnung=zeichnung, qa_schwelle=0.95),
                         cache=cache, ausfuehrer=werkbank.tabelle(),
                         out_dir=tmp_path / "out")

    assert zweiter["knoten"]["runde2-nachrender"]["aus_cache"] is True, (
        "Voraussetzung der Probe: Die Bildstufe selbst wird NICHT neu gerechnet.")
    assert erster["knoten"]["runde2-nachrender"]["ausgaben"][FELD_BASIS][BASIS_BESTANDEN] \
        is True
    assert zweiter["knoten"]["runde2-nachrender"]["ausgaben"][FELD_BASIS][BASIS_BESTANDEN] \
        is False, (
        "Das Urteil der Basis folgt dem neuen Lauf. Kaeme es aus dem Speicher, staende "
        "hier True — ein Urteil, das eine geaenderte Schwelle ueberlebt hat.")


def test_der_basis_block_erreicht_den_zwischenspeicher_nicht(tmp_path):
    """Die Gegenprobe zur Mutationsprobe, an der Quelle statt am Ergebnis.

    Ohne sie bliebe die Trennung eine Behauptung ueber die Reihenfolge zweier Zeilen.
    """
    zeichnung = schreibe_png(tmp_path / "gezeichnet.png")
    cache = ArtefaktCache(tmp_path / "cache")
    lauf = fuehre_aus(baue_lauf(tmp_path, zeichnung=zeichnung), cache=cache,
                      ausfuehrer=Werkbank().tabelle(), out_dir=tmp_path / "out")

    eintrag = cache.hole(lauf["knoten"]["runde2-nachrender"]["hash"])
    assert eintrag is not None, "Voraussetzung: die Stufe wurde ueberhaupt abgelegt"
    assert FELD_BASIS not in eintrag["ausgaben"], (
        "Ein abgelegtes Basisurteil waere ein Urteil aus einem anderen Lauf.")
    assert eintrag["ausgaben"][FELD_SCHICHT] == SCHICHT_AI_IMAGING, (
        "Die SCHICHT dagegen darf mit: Sie folgt allein aus den Eingaengen dieses "
        "Knotens, und die stecken im Hash.")


def test_schichtbefund_fasst_bestanden_nie_an(tmp_path):
    """*Ein Waechter, der alles durchwinkt, bewacht nichts.*

    ``schichtbefund`` legt daneben, nie darueber. Waere es je anders, koennte ein
    geerbtes Urteil das eigene ueberschreiben — und niemand saehe es dem Ergebnis an.
    """
    graph = baue_lauf(tmp_path, zeichnung=schreibe_png(tmp_path / "gezeichnet.png"))
    nachtrag = schichtbefund(graph, {})
    for kid, felder in nachtrag.items():
        assert "bestanden" not in felder, kid
    assert set(nachtrag) >= {KNOTEN_RENDER, KNOTEN_QA, "runde2-bildquelle",
                             "runde2-nachrender"}


def test_schichtbefund_laeuft_auch_ohne_lauf(tmp_path):
    """Ein Graph, der noch nicht gerechnet hat, kann seine Schichten schon nennen.

    Das Urteil der Basis kann er nicht — es gibt es erst nach einer Messung. Genau das
    ist der Unterschied zwischen Bau und Lauf, den dieses Modul ueberall zieht.
    """
    graph = baue_lauf(tmp_path, zeichnung=schreibe_png(tmp_path / "gezeichnet.png"))
    nachtrag = schichtbefund(graph)

    assert nachtrag["runde2-nachrender"][FELD_SCHICHT] == SCHICHT_AI_IMAGING
    assert nachtrag["runde2-nachrender"][FELD_BASIS][BASIS_KNOTEN] == KNOTEN_RENDER
    assert nachtrag["runde2-nachrender"][FELD_BASIS][BASIS_BESTANDEN] is None
