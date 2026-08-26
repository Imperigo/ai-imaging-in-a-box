"""Einstellbar ist ein Versprechen, das man an der NAHT prüft — nicht am Modul.

**Der Anlass sind zwei Fehler desselben Tages** (23.08.2026). Die Brennweite war im Kern
längst ein Parameter und kam an der Aussenkante trotzdem nicht durch: zwei fest verdrahtete
`28.0` standen im Weg, eine davon in einem Test. Der Geländestand dasselbe. Beide Male
hiess es «einstellbar», und beide Male stimmte das im Modul und nicht im Betrieb.

Diese Datei prüft die Umkehrung: **Jedes Feld, das aus der Bestellung gelesen wird, steht
in genau einer der beiden Listen** — es kommt an, oder es bleibt stehen und der Grund
steht dabei. Ein neues Feld im fremden Vertrag kann damit nicht mehr stillschweigend ins
Leere laufen.

Die Prüfung ist bewusst **nicht** «alles kommt an». Drei Felder tun es heute nicht, und
das ist ein Befund und kein Fehler dieser Datei — er gehört gemeldet, nicht wegdefiniert.
*Es waren fünf; `ueberspringen` und `sonne` sind am 26.08.2026 angeschlossen worden.*
"""
from __future__ import annotations

import pytest

from aiimaging import abholer, kosmo_szene
from aiimaging.kosmo_szene import DURCHGEREICHT, STEHENGEBLIEBEN, SzenenError
from conftest import MINI_PNG

BESTELLUNG = {"geometry": {"path": "/irgendwo/bau.glb", "format": "glb"}}


def _szene(**fremd):
    return kosmo_szene.lies_szene({**BESTELLUNG, **fremd})


# --------------------------------------------------------------------------------------
# 1 · Die Tabelle ist vollständig — das ist der eigentliche Wächter
# --------------------------------------------------------------------------------------

def test_jedes_gelesene_feld_steht_in_genau_einer_der_beiden_listen():
    """**Der Test, um dessentwillen es die Tabelle gibt.**

    Wer dem fremden Vertrag ein Feld hinzufügt und es in `lies_szene` ausliest, muss hier
    Farbe bekennen: Kommt es an, oder bleibt es stehen? Ohne diesen Test ist die dritte
    Möglichkeit die bequemste — es steht nirgends und läuft ins Leere.
    """
    gelesen = set(_szene())
    erklaert = set(DURCHGEREICHT) | set(STEHENGEBLIEBEN)

    assert gelesen - erklaert == set(), (
        "Diese Felder liest `lies_szene`, und niemand sagt, wohin sie gehen")
    assert erklaert - gelesen == set(), (
        "Diese Felder stehen in der Tabelle und werden gar nicht mehr gelesen — "
        "eine Tabelle, die Felder behauptet, die es nicht gibt, macht die Lücke "
        "unauffindbar")


def test_kein_feld_steht_in_beiden_listen():
    """«Kommt an» und «bleibt stehen» zugleich ist keine Auskunft, sondern zwei."""
    assert set(DURCHGEREICHT) & set(STEHENGEBLIEBEN) == set()


@pytest.mark.parametrize("feld", sorted(STEHENGEBLIEBEN))
def test_jeder_stehengebliebene_eintrag_sagt_auch_was_fehlt(feld):
    """Ein «wird nicht unterstützt» ohne den nächsten Schritt ist eine Sackgasse.

    Mit ihm ist es eine Aufgabe. Der Unterschied kostet zwei Sätze und entscheidet, ob
    jemand die Lücke je schliesst.
    """
    eintrag = STEHENGEBLIEBEN[feld]
    assert set(eintrag) == {"fremd", "neutral", "grund", "noetig"}, (
        "Jeder Eintrag nennt seit dem 26.08.2026 auch seinen FREMDEN Namen. Der Grund "
        "steht in `tests/test_uebergabe.py`: Das Blatt für den Cloud-Worker nennt die "
        "Felder so, wie sie im fremden Vertrag heissen, und ein Wächter hält beide "
        "Listen gegeneinander. Ohne den Namen im Code wäre die Zuordnung geraten.")
    assert eintrag["fremd"], "der fremde Name gehört benannt, nicht leer gelassen"
    assert len(eintrag["grund"]) > 40, "ein Halbsatz erklärt nichts"
    assert len(eintrag["noetig"]) > 30, "was fehlt, gehört benannt"


# --------------------------------------------------------------------------------------
# 2 · Gemeldet wird nur, was wirklich bestellt wurde
# --------------------------------------------------------------------------------------

def test_eine_leere_bestellung_meldet_nichts():
    """**Sonst wäre es die nächste Dauerwarnung.**

    Am selben Tag gemessen: Ohne Geländestand trug jede von zwölf Kameras dieselben zwei
    Warnungen. Eine Warnung, die immer erscheint, ist kein Signal mehr — es ist dasselbe
    Versagen wie ein Wächter, der nie greift, nur von der anderen Seite.
    """
    assert kosmo_szene.stehengebliebene_felder(_szene()) == ()


def test_ein_gesetzter_sonnenstand_wird_jetzt_bedient():
    """**Erledigt am 26.08.2026** — und es war der gefährlichste der fünf.

    Die Sonne stand im Blender-Runner fest. Wer einen Abendstand bestellte, bekam ein
    sauberes, gut belichtetes, **falsches** Bild — und nichts daran sah nach einem Fehler
    aus. Jetzt reicht `seams.glb_zu_multipass(sonne=…)` ihn bis in den Runner durch.

    **Die Warnung bleibt trotzdem stehen, und sie ist eine andere:** Ob der fremde
    Vertrag den Azimut von Norden oder von Süden zählt, ist nicht geklärt. Der
    Unterschied beträgt 180 Grad und vertauscht Vormittag und Nachmittag — bedient unter
    einer Annahme ist etwas anderes als bedient.
    """
    szene = _szene(render={"sun": {"elevation": 8, "azimuth": 250}})

    assert kosmo_szene.stehengebliebene_felder(szene) == ()
    assert "sonne" in DURCHGEREICHT and "sonne" not in STEHENGEBLIEBEN
    assert szene["sonne"] == {"elevation": 8, "azimuth": 250}
    assert any("ANNAHME" in w for w in szene["warnungen"]), (
        "bedient unter einer ungeklaerten Konvention ist NICHT dasselbe wie bedient")


def test_ohne_bestellte_sonne_steht_die_annahme_nicht_da():
    """Die Gegenprobe: Sie erscheint nur, wenn wirklich eine Sonne bestellt wurde — sonst
    wäre es die nächste Dauerwarnung."""
    assert not [w for w in _szene()["warnungen"] if "ANNAHME" in w]


def test_ein_abbestellter_auftrag_steht_nicht_mehr_auf_der_liste():
    """**Erledigt am 26.08.2026** — und darum steht der Test hier umgedreht.

    `skip: true` wurde bis dahin gelesen und nicht beachtet: Wer etwas ABBESTELLTE,
    bekam es geliefert und zahlte die GPU-Zeit (im Lauf belegt, `auf-vis-20260825-15`
    Posten 2). Seit `abholer.verarbeiter` es befolgt, gehört das Feld nach
    :data:`DURCHGEREICHT` — und nicht mehr auf die Liste der Bestellungen, die ins Leere
    laufen.

    Der Test bleibt stehen und misst jetzt das Gegenteil: Ein erledigter Posten, der
    stillschweigend aus einer Tabelle verschwindet, ist von einem vergessenen nicht zu
    unterscheiden.
    """
    offen = kosmo_szene.stehengebliebene_felder(_szene(vis={"skip": True}))

    assert [e["feld"] for e in offen] == []
    assert "ueberspringen" in kosmo_szene.DURCHGEREICHT
    assert "ueberspringen" not in STEHENGEBLIEBEN


def test_mehrere_zugleich_kommen_alle_und_in_der_reihenfolge_der_tabelle():
    offen = kosmo_szene.stehengebliebene_felder(
        _szene(render={"sun": {"elevation": 8}}, vis={"skip": True, "upscale": True},
               style={"mode": "referenz"}))
    felder = [e["feld"] for e in offen]

    assert felder == [f for f in STEHENGEBLIEBEN if f in felder]
    assert set(felder) == {"hochskalieren", "stil_modus"}, (
        "es sind noch DREI stehengebliebene Felder; `ueberspringen` und `sonne` sind am "
        "26.08.2026 angeschlossen worden")


def test_ein_stil_modus_none_ist_keine_bestellung():
    """Der einzige der fünf, dessen neutraler Wert kein `False` und kein `None` ist.

    Ohne den Tabelleneintrag `neutral` wäre `"none"` ein gesetzter Wert — und jede
    Bestellung ohne Stil trüge eine Meldung.
    """
    assert _szene()["stil_modus"] == "none"
    assert kosmo_szene.stehengebliebene_felder(_szene(style={"mode": "none"})) == ()


def test_keine_szene_kein_urteil():
    with pytest.raises(SzenenError, match="kein Wörterbuch"):
        kosmo_szene.stehengebliebene_felder(["sonne"])


# --------------------------------------------------------------------------------------
# 3 · Und es erreicht den Menschen am Terminal
# --------------------------------------------------------------------------------------
#
# Eine Tabelle, die niemand sieht, ist die naechste tote Kante. Dieses Projekt hat diese
# Fehlerart am 23.08.2026 dreimal an einem Tag gefunden.

def test_der_kurzbefund_nennt_was_bestellt_und_nicht_ausgefuehrt_wurde():
    befund = {"kameras": [], "stehengeblieben": [
        {"feld": "sonne", "wert": {"elevation": 8},
         "grund": "Die Sonne steht im Runner fest.", "noetig": "…"}]}

    zeilen = abholer.befund_kurz(befund)

    treffer = [z for z in zeilen if "BESTELLT UND NICHT AUSGEFUEHRT" in z]
    assert len(treffer) == 1
    assert "sonne" in treffer[0]
    assert "Die Sonne steht im Runner fest." in treffer[0], (
        "der Grund gehoert in dieselbe Zeile — wer nur den Feldnamen liest, "
        "haelt es fuer einen Tippfehler")


def test_gegenprobe_ohne_offene_bestellung_steht_die_zeile_nicht_da():
    assert not [z for z in abholer.befund_kurz({"kameras": []})
                if "BESTELLT UND NICHT AUSGEFUEHRT" in z]


# --------------------------------------------------------------------------------------
# 4 · Abbestellt heisst abbestellt — seit 26.08.2026
# --------------------------------------------------------------------------------------
#
# Belegt im ersten vollstaendigen Kettenlauf (auf-vis-20260825-15, Posten 2): Der Abholer
# meldete woertlich «BESTELLT UND NICHT AUSGEFUEHRT: ueberspringen = True» — und rechnete
# weiter. Eine Meldung ueber die eigene Nichtbeachtung ist ehrlicher als Schweigen und
# trotzdem keine Erfuellung.

def _abgestellte_kette(tmp_path, skip):
    """Ein Lauf durch `verarbeiter` mit Attrappen; gibt (ergebnis, zahl der Render)."""
    from pathlib import Path

    zaehler = {"render": 0, "multipass": 0}

    def multipass(glb, aus, **kw):
        zaehler["multipass"] += 1
        tiefe = Path(aus) / "tiefe_norm.png"
        tiefe.write_bytes(MINI_PNG)
        return {"depth_png": str(tiefe), "kamera": {"weg": "vorgegeben"}}

    def rendere(auftrag, **kw):
        zaehler["render"] += 1
        bild = Path(tmp_path) / "b.png"
        bild.write_bytes(MINI_PNG)
        return {"status": "ok", "bild_png": str(bild), "hinweise": ()}

    verarbeite = abholer.verarbeiter(
        out_wurzel=tmp_path, nullprobe=False,
        _multipass=multipass, _rendere=rendere,
        _qa=lambda *a, **k: {"score": 0.9, "bestanden": True},
        _soll=lambda *a, **k: ([[0.0]], 1, 1))

    szene = _szene(vis={"skip": skip})
    szene = dict(szene, kameras=[{"kuerzel": "sSE", "richtung": "sSE"}],
                 aufloesung=64, hoehe=64, samples=1, prompt="a house")
    ergebnis = verarbeite({"modell": Path(tmp_path) / "m.glb", "job_id": "vis-1-aaaaaa",
                           "verzeichnis": tmp_path, "szene": szene})
    return ergebnis, zaehler


def test_ein_abbestellter_auftrag_wird_nicht_gerendert(tmp_path):
    """Der Kern des Postens: keine Blender-Laufzeit, keine GPU-Zeit, kein Bild."""
    ergebnis, zaehler = _abgestellte_kette(tmp_path, True)

    assert zaehler == {"render": 0, "multipass": 0}
    assert ergebnis["bilder"] == []
    assert ergebnis["uebersprungen"] is True
    assert "skip" in ergebnis["grund"]


def test_ein_abbestellter_auftrag_bekommt_trotzdem_eine_antwort(tmp_path):
    """**Der entschiedene Teil** (26.08.2026): Überspringen heisst kein Bild, aber sehr
    wohl eine Antwort. Gar nichts zurückzugeben liesse die bestellende Seite hängen — sie
    könnte übersprungen nicht von abgestürzt unterscheiden."""
    ergebnis, _ = _abgestellte_kette(tmp_path, True)

    assert set(ergebnis) >= {"bilder", "geometrie_urteil", "kameras", "zeiten",
                             "uebersprungen", "grund"}
    assert ergebnis["geometrie_urteil"] is None, (
        "nichts gemessen — und ein erfundenes Urteil waere schlimmer als keines")


def test_ohne_skip_laeuft_alles_wie_bisher(tmp_path):
    """Die Gegenprobe, und sie ist die wichtigere: Eine Abkürzung, die immer greift,
    hätte die ganze Kette stillgelegt."""
    ergebnis, zaehler = _abgestellte_kette(tmp_path, False)

    assert zaehler == {"render": 1, "multipass": 1}
    assert len(ergebnis["bilder"]) == 1
    assert ergebnis["uebersprungen"] is False


def test_das_ergebnis_sagt_abbestellt_und_nicht_ungeprueft():
    """**Die vierte Lage an der Vertragsgrenze.**

    `passed` ist im fremden Vertrag ein Wahrheitswert und kann kein Drittes tragen — ein
    übersprungener Auftrag kommt dort also als `false` an, genau wie ein durchgefallenes
    Bild. Der Satz daneben ist die einzige Stelle, an der der Unterschied überlebt. Und
    er ist ein anderer als «ungeprüft»: Ungeprüft verlangt einen zweiten Lauf, abbestellt
    verlangt gar nichts.
    """
    ergebnis = kosmo_szene.als_ergebnis("vis-1-aaaaaa", [], uebersprungen=True)

    grund = ergebnis["qa"]["verdict"]["reason"]
    assert ergebnis["qa"]["verdict"]["passed"] is False
    assert grund.startswith("ABBESTELLT")
    assert "weder durchgefallen noch ungeprueft" in grund, (
        "der Satz muss BEIDE Fehldeutungen ausschliessen — 'nicht durchgefallen' allein "
        "liesse noch 'da fehlt ein Lauf' uebrig")
    assert "keine GPU-Zeit" in grund


def test_ohne_abbestellung_bleibt_der_satz_ungeprueft():
    """Die Gegenprobe: Sonst trüge jedes ungemessene Ergebnis das falsche Etikett — und
    ein vergessener Lauf sähe aus wie ein abbestellter."""
    ergebnis = kosmo_szene.als_ergebnis("vis-1-aaaaaa", [])

    grund = ergebnis["qa"]["verdict"]["reason"]
    assert not grund.startswith("ABBESTELLT")
    assert "ungeprüft" in grund
