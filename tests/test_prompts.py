"""Die Prompt-Bibliothek — und die eine Regel, aus der sie folgt.

    Ein Prompt, der Bauteile nennt, die die Geometrie nicht hat, ist eine Aufforderung
    zur Halluzination.

Am Gerät gelernt (`auf-20260818-09`): „clean flat roof" für einen oben offenen Quader,
und das Bildmodell lieferte ein Dach. Es hat nichts falsch gemacht — es tat, was dastand.

Die Tests hier prüfen darum vor allem eines: dass diese Regel **ausführbar** ist und nicht
bloss in einem Kommentar steht. Ein Grundsatz, den kein Test kennt, ist ein Vorsatz.
"""
from __future__ import annotations

import pytest

from aiimaging import prompts as p


# --------------------------------------------------------------------------------------
# 1 · Die Kategorien nennen keine Bauteile — das ist ihre eigentliche Qualität
# --------------------------------------------------------------------------------------

def test_keine_kategorie_nennt_ein_bauteil():
    """Der Befund, der die geerbte Einteilung überhaupt erst wertvoll macht.

    Die sieben Kategorien stammen aus dem älteren KosmoVis-Bestand. Beim Übernehmen fiel
    auf: Keine davon beschreibt das Gebäude. Sie beschreiben ausnahmslos, was um es herum
    und auf seinen Oberflächen liegt. Die Einteilung ist damit genau die Regel von oben,
    in Fächer gegossen — sie wurde nicht erfunden, sondern erkannt.
    """
    for kategorie in p.KATEGORIEN:
        fund = p.bauteilwaechter(kategorie + " " + p.KATEGORIE_ERKLAERUNG[kategorie])
        # Die Erklärungen dürfen Bauteile als Gegenbeispiel nennen ("NICHT welches
        # Bauteil"). Der Kategoriename selbst darf es nicht.
        assert not p.bauteilwaechter(kategorie)["gefunden"], kategorie


def test_kein_baustein_nennt_ein_bauteil():
    """Die vorgefertigten Texte müssen die Regel halten, die sie durchsetzen sollen.

    Bei den Bausteinen ist das keine Bitte, sondern eine Zusicherung: Wer einen Stil aus
    der Liste wählt, soll sich darauf verlassen können, dass der Prompt die Geometrie
    nicht überstimmt. Freitext ist die Verantwortung des Menschen — die Bibliothek nicht.
    """
    for kategorie, bausteine in p.BAUSTEINE.items():
        for b in bausteine:
            fund = p.bauteilwaechter(b.text)
            assert not fund["gefunden"], f"{kategorie}/{b.slug}: {fund['woerter']}"


def test_keine_handschrift_und_kein_negativ_nennt_ein_bauteil():
    for stil in p.STILE.values():
        for feld, text in (("handschrift", stil.handschrift), ("negativ", stil.negativ)):
            fund = p.bauteilwaechter(text)
            assert not fund["gefunden"], f"{stil.slug}.{feld}: {fund['woerter']}"


def test_ein_vollstaendig_komponierter_prompt_bleibt_sauber():
    """Die Gesamtprobe: kein Stil erzeugt in der Summe ein Bauteil."""
    for slug in p.STILE:
        fund = p.bauteilwaechter(p.komponiere(slug)["prompt"])
        assert not fund["gefunden"], (slug, fund["woerter"])


# --------------------------------------------------------------------------------------
# 2 · Der Bauteilwächter
# --------------------------------------------------------------------------------------

def test_der_waechter_faengt_genau_den_fehler_vom_18_august():
    """Der Prompt, der ein Dach auf einen offenen Quader gesetzt hat."""
    fund = p.bauteilwaechter(
        "photorealistic architectural photograph, clean flat roof, matte concrete")
    assert fund["gefunden"] is True
    assert "roof" in fund["woerter"]
    assert "Halluzination" in fund["hinweis"]


@pytest.mark.parametrize("text,erwartet", [
    ("a building with a large balcony", "balcony"),
    ("Fassade aus Sichtbeton", "fassade"),
    ("view through the windows", "windows"),
    ("das Dach ist begrünt", "dach"),
    ("wide staircase leading up", "staircase"),
])
def test_der_waechter_kennt_beide_sprachen(text, erwartet):
    """Das Eingabefeld im Knoten kennt keinen Sprachzwang.

    Ein Wächter, der nur die halbe Eingabe sieht, ist schlimmer als keiner: Er erzeugt
    das Gefühl, geprüft worden zu sein.
    """
    assert erwartet in p.bauteilwaechter(text)["woerter"]


@pytest.mark.parametrize("text", [
    "soft even daylight, no direct sun",
    "matte surfaces, true material colour",
    "one or two people in the distance, giving scale",
    "low morning fog, air washed clear after rain",
    "",
])
def test_der_waechter_schlaegt_nicht_grundlos_an(text):
    """Ein Wächter, der immer anschlägt, wird abgeschaltet."""
    assert p.bauteilwaechter(text)["gefunden"] is False


def test_teilwoerter_loesen_nicht_aus():
    """Wortgrenzen, nicht Textsuche.

    „doorway" enthält „door", „wallpaper" enthält „wall", „towering" enthält „tower".
    Ohne Wortgrenzen wäre der Wächter in jedem zweiten Satz laut — und damit stumm.
    """
    assert p.bauteilwaechter("stonewalled")["gefunden"] is False
    assert p.bauteilwaechter("towering trees")["gefunden"] is False
    assert p.bauteilwaechter("indoors")["gefunden"] is False


def test_der_waechter_meldet_jedes_wort_nur_einmal_und_in_textreihenfolge():
    fund = p.bauteilwaechter("roof over the entrance, and another roof behind")
    assert fund["woerter"] == ("roof", "entrance")


def test_der_waechter_verbietet_nichts():
    """Er meldet, er sperrt nicht — und das ist eine Entscheidung.

    Manchmal HAT die Geometrie das genannte Bauteil, und dann ist die Nennung richtig.
    Ob sie es hat, kann dieses Modul nicht wissen; es sieht nur Text. Ein Verbot wäre
    eine Behauptung über eine Datei, die hier gar nicht vorliegt.
    """
    ergebnis = p.komponiere(freitext="with a glass roof")
    assert "roof" in ergebnis["prompt"]                 # es steht drin …
    assert any("Halluzination" in h for h in ergebnis["hinweise"])   # … und es steht dabei


def test_der_hinweis_nennt_beide_moeglichkeiten():
    """Ein Hinweis, der nur eine Lesart kennt, schickt Leute in die falsche Richtung.

    Dieselbe Lehre wie bei der Geometrie-Warnung, die „erfundene Kubatur" als einzige
    Ursache nannte und an einem perfekten Bild danebenlag.
    """
    hinweis = p.bauteilwaechter("with a roof")["hinweis"]
    assert "Wenn nicht" in hinweis                       # Geometrie hat es nicht
    assert "Trägt die Geometrie sie" in hinweis          # Geometrie hat es doch


def test_unbrauchbare_eingabe_ist_kein_absturz():
    for kaputt in (None, 42, [], {}):
        assert p.bauteilwaechter(kaputt)["gefunden"] is False


# --------------------------------------------------------------------------------------
# 3 · Die Stile
# --------------------------------------------------------------------------------------

def test_der_messstil_existiert_und_ist_treue_geeignet():
    """Ohne einen messtauglichen Stil misst jede Schwelle den Geschmack mit."""
    assert p.MESS_STIL in p.STILE
    assert p.STILE[p.MESS_STIL].treue_geeignet is True
    assert p.STILE[p.MESS_STIL].empfohlene_controlnet_staerke == 1.0


def test_der_messstil_schliesst_menschen_und_bewuchs_aus():
    """Beides verdeckt das Bauwerk und verfälscht die Silhouette — also die Messung."""
    stil = p.STILE[p.MESS_STIL]
    assert stil.bausteine["people"] == "keine"
    assert stil.bausteine["vegetation"] == "keine"


def test_jeder_nicht_messtaugliche_stil_sagt_warum():
    """`treue_geeignet: False` ohne Begründung wäre ein Urteil ohne Grund.

    Und die Begründung ist jedes Mal dieselbe Art: Der Stil verändert die Silhouette
    **von sich aus**. Eine niedrige Zahl misst dann den Stil, nicht das Bildmodell.
    """
    for stil in p.STILE.values():
        if not stil.treue_geeignet:
            assert stil.warnung, f"{stil.slug} hat keine Warnung"
            assert len(stil.warnung) > 60, stil.slug


def test_jeder_stil_bedient_alle_sieben_kategorien():
    """Eine fehlende Kategorie ist eine stille Auslassung.

    Das Bildmodell füllt sie dann selbst — und zwar mit dem, was in seinen
    Trainingsbildern am häufigsten war. Bei `people` heisst das: Es setzt Menschen hinein.
    """
    for stil in p.STILE.values():
        assert set(stil.bausteine) == set(p.KATEGORIEN), stil.slug
        for kategorie, slug in stil.bausteine.items():
            p.baustein(kategorie, slug)          # wirft, wenn es ihn nicht gibt


def test_der_skizzenstil_verlangt_eine_gelockerte_controlnet_staerke():
    """Bei 1.0 entsteht ein Foto mit Bleistiftfilter, keine Zeichnung."""
    assert p.STILE["einskizziert"].empfohlene_controlnet_staerke < 0.8


def test_kein_stil_traegt_die_alten_schlagwortketten():
    """`masterpiece, best quality, 8k, trending on artstation` — bewusst nicht.

    Diese Formeln stammen aus der SD-1.5-Zeit und aus Bilddatenbanken mit
    Schlagwortlisten. Die heutigen Modelle sind an natürlicher Sprache trainiert; dort
    ist eine Adjektivkette bestenfalls wirkungslos und schlimmstenfalls ein Stilbefehl
    Richtung Fantasy-Illustration.
    """
    verboten = ("masterpiece", "best quality", "8k", "4k", "highly detailed",
                "trending on artstation", "award winning", "ultra realistic")
    for stil in p.STILE:
        text = p.komponiere(stil)["prompt"].lower()
        for wort in verboten:
            assert wort not in text, f"{stil}: {wort!r}"


# --------------------------------------------------------------------------------------
# 4 · Komposition
# --------------------------------------------------------------------------------------

def test_der_freitext_steht_vorne():
    """Was eine Person eigens hinschreibt, ist ihr wichtiger als jede Vorgabe.

    Und frühe Wörter wiegen im Bildmodell schwerer — die Reihenfolge ist keine Kosmetik.
    """
    ergebnis = p.komponiere(freitext="seen from a narrow street")
    stil = p.STILE[p.MESS_STIL]
    assert ergebnis["prompt"].startswith(stil.handschrift)
    assert ergebnis["prompt"].index("narrow street") < ergebnis["prompt"].index("overcast")


def test_ohne_freitext_entsteht_kein_leeres_komma():
    assert ", ," not in p.komponiere()["prompt"]
    assert not p.komponiere(freitext="   ")["prompt"].count(",  ")


def test_ein_abschliessendes_komma_im_freitext_wird_aufgeraeumt():
    """Menschen tippen Kommata ans Ende. Das darf keine leere Aufzählungsstelle geben."""
    assert ", ," not in p.komponiere(freitext="seen from below,")["prompt"]


def test_ersetzungen_tauschen_ein_fach_ohne_den_stil_zu_verlassen():
    """Der Knopf für „wie der Wettbewerbsstil, aber ohne Menschen"."""
    ohne = p.komponiere("wettbewerb", ersetzungen={"people": "keine"})
    assert ohne["bausteine"]["people"] == "keine"
    assert ohne["bausteine"]["light_time"] == p.STILE["wettbewerb"].bausteine["light_time"]
    assert "no people" in ohne["prompt"]


def test_die_empfohlene_controlnet_staerke_kommt_mit():
    """Der Stil weiss, wie streng die Geometrie binden muss, damit er entstehen kann."""
    assert p.komponiere("einskizziert")["controlnet_staerke"] < \
        p.komponiere(p.MESS_STIL)["controlnet_staerke"]


def test_ein_nicht_messtauglicher_stil_wird_gemeldet():
    hinweise = " ".join(p.komponiere("morgennebel")["hinweise"])
    assert "nicht geeignet" in hinweise
    assert p.MESS_STIL in hinweise            # und was stattdessen zu nehmen ist


def test_der_messstil_erzeugt_keine_warnung():
    """Ein Hinweis, der immer kommt, wird überlesen."""
    assert p.komponiere(p.MESS_STIL)["hinweise"] == ()


def test_ein_wirkungsloser_negativprompt_wird_gemeldet():
    """Der stille Fall — derselbe wie in `render.py`, hier eine Stufe früher.

    Bei einer Führung unter 1.0 rechnet diffusers nicht mehr doppelt, und genau davon
    lebt der negative Teil. Er stünde im Protokoll und nie im Bild. Destillierte
    Turbo-Modelle laufen mit 0.0.
    """
    hinweise = " ".join(p.komponiere(p.MESS_STIL, fuehrung=0.0)["hinweise"])
    assert "WIRKUNGSLOS" in hinweise


def test_ohne_angabe_der_fuehrung_wird_darueber_nichts_behauptet():
    """Was nicht bekannt ist, wird nicht gemeldet — auch nicht vorsichtshalber."""
    assert not any("WIRKUNGSLOS" in h for h in p.komponiere(p.MESS_STIL)["hinweise"])


def test_bei_ausreichender_fuehrung_kein_hinweis():
    assert not any("WIRKUNGSLOS" in h
                   for h in p.komponiere(p.MESS_STIL, fuehrung=5.0)["hinweise"])


@pytest.mark.parametrize("slug", ["gibtsnicht", "", "Messschnitt"])
def test_unbekannter_stil_nennt_die_bekannten(slug):
    """Eine Fehlermeldung, die nur „unbekannt" sagt, zwingt zum Nachschlagen im Code."""
    with pytest.raises(p.PromptError, match="Bekannt:"):
        p.komponiere(slug)


def test_unbekannte_ersetzung_wird_abgewiesen():
    with pytest.raises(p.PromptError):
        p.komponiere("wettbewerb", ersetzungen={"licht": "abendlicht"})
    with pytest.raises(p.PromptError, match="Bekannt:"):
        p.komponiere("wettbewerb", ersetzungen={"people": "gibtsnicht"})


# --------------------------------------------------------------------------------------
# 5 · Regel 4: die Oberfläche ist eine dünne Schicht
# --------------------------------------------------------------------------------------

def test_die_uebersicht_traegt_alles_was_ein_knoten_braucht():
    """Der Knoten füllt seine Felder daraus und entscheidet nichts.

    Wer keine Oberfläche hat, ruft dasselbe aus Python und bekommt dieselbe Antwort —
    das ist Regel 4 in einer Funktion.
    """
    u = p.uebersicht()
    assert [k["slug"] for k in u["kategorien"]] == list(p.KATEGORIEN)
    assert {s["slug"] for s in u["stile"]} == set(p.STILE)
    assert u["mess_stil"] == p.MESS_STIL
    for k in u["kategorien"]:
        assert k["bausteine"], k["slug"]
        assert k["erklaerung"]


def test_die_uebersicht_ist_reine_daten():
    """Sie muss durch JSON passen — sonst kann sie kein Cockpit lesen."""
    import json
    json.dumps(p.uebersicht(), ensure_ascii=False)


def test_die_uebersicht_warnt_am_freitextfeld_selbst():
    """Die Regel gehört dorthin, wo sie gebrochen wird — an das Eingabefeld."""
    text = p.uebersicht()["freitextfeld"]
    assert "Dach" in text and "erfindet" in text


def test_kein_ui_import_im_modul():
    """Regel 4: Der Kern läuft ohne Oberfläche und ohne Blender."""
    import ast
    import inspect
    baum = ast.parse(inspect.getsource(p))
    for knoten in ast.walk(baum):
        if isinstance(knoten, ast.Import):
            for name in knoten.names:
                assert name.name.split(".")[0] not in ("bpy", "tkinter", "PyQt5")
        elif isinstance(knoten, ast.ImportFrom):
            assert (knoten.module or "").split(".")[0] not in ("bpy", "tkinter", "PyQt5")


def test_die_antwort_passt_ohne_umbau_in_einen_renderauftrag():
    """Die Naht zur Renderstufe — sie soll aus drei Feldern bestehen, nicht aus Klebstoff.

    `komponiere` liefert genau die drei Grössen, die `RenderAuftrag` von der Prompt-Seite
    braucht: Text, Negativtext und die ControlNet-Stärke. Wäre dazwischen eine Umrechnung
    nötig, gäbe es einen zweiten Ort, an dem ein Stil interpretiert wird — und zwei Orte
    laufen auseinander.
    """
    from aiimaging.render import RenderAuftrag

    fertig = p.komponiere("wettbewerb")
    auftrag = RenderAuftrag(
        depth_png="/synthetisch/tiefe_norm.png",
        prompt=fertig["prompt"],
        negativ_prompt=fertig["negativ_prompt"],
        controlnet_staerke=fertig["controlnet_staerke"],
    )
    assert auftrag.prompt.startswith("a calm, precise architectural photograph")
    assert auftrag.controlnet_staerke == 0.9


def test_die_handschrift_wiederholt_den_kompositionsbaustein_nicht():
    """Ein Mangel meines eigenen ersten Entwurfs, jetzt als Regel.

    Modellfoto sagte in der Handschrift „a photograph of a physical architectural model"
    und im Kompositionsbaustein gleich noch einmal „photograph of a physical
    architectural model". Doppelt genannt heisst im Bildmodell **doppelt gewichtet** —
    der Stil überschreibt dann sich selbst und drängt alles andere aus dem Bild.

    Geprüft wird auf gemeinsame Wortfolgen von drei Wörtern; kürzere Überschneidungen
    („of the", „in a") sind normale Sprache und kein Mangel.
    """
    def dreiergruppen(text):
        w = [x.strip(",.") for x in text.lower().split()]
        return {" ".join(w[i:i + 3]) for i in range(len(w) - 2)}

    for stil in p.STILE.values():
        if not stil.handschrift:
            continue
        komposition = p.baustein("composition", stil.bausteine["composition"]).text
        gemeinsam = dreiergruppen(stil.handschrift) & dreiergruppen(komposition)
        assert not gemeinsam, f"{stil.slug}: doppelt genannt — {sorted(gemeinsam)}"


def test_kein_stil_verlangt_sonne_und_geschlossene_wolkendecke_zugleich():
    """Der zweite Mangel meines Entwurfs: Morgennebel hatte beides.

    Ein widersprüchlicher Prompt wird nicht gemittelt. Das Modell entscheidet sich für
    eine Lesart — für die, die in seinen Trainingsbildern häufiger war —, und welche das
    ist, weiss niemand. Ein Bild, dessen Zustandekommen niemand erklären kann, ist für
    dieses Projekt wertlos, auch wenn es schön ist.
    """
    for stil in p.STILE.values():
        text = p.komponiere(stil.slug)["prompt"].lower()
        sonnig = any(w in text for w in ("sunlight", "sun raking", "midday sun"))
        zu = any(w in text for w in ("heavy low clouds", "uniform overcast"))
        assert not (sonnig and zu), stil.slug
