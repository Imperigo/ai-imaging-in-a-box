"""Befunde der Generalprobe auf-20261022-327 (Protokoll 74 §225) — was im Kern behoben ist.

* **B1 / S5 rot — die Vorschau hält den Umriss.** Bis 0.3.31 entfiel bei ``vis.guete:
  'vorschau'`` die Vorgabe ``vis.umriss_halten: 'im_lauf'`` (Entscheid 126) mit dem Grund «die
  Vorschau rechnet immer gleich (Entscheid 104)». Entscheid 104 sagt aber nur, WOMIT die
  Vorschau rechnet (z-image-turbo, ein Startwert, 8 Schritte, kleineres KI-Bild). Die Vorschau
  bekam so die halbe M2: den Stoff vorne (der allein weiter über den Umriss baut, 303: M1 3,08
  gegen K 2,19), ohne den Halt — 161/179 % Baumasse neben dem Haus. Jetzt gilt die Vorgabe
  auch dort; die Vorschau rechnet immer z-image-turbo, an dem der Halt gemessen ist.
* **B2 / S6 gelb — der Satz «KI-BILD OHNE GRUNDLAGENBILD» stimmt mit M2.** Mit Umriss halten
  im Lauf kommt das Cycles-Bild ausserhalb des Hauses sehr wohl an; der Satz sagte trotzdem
  «Material, Licht und Ausschnitt malt das Modell frei». Er behält seinen Anfang (die
  Knotenansicht sucht danach) und sagt jetzt «im Haus NICHT angekommen».
* **B8 — Hintergrund und Prompt-Sätze im Ergebnis.** ``umgebung.hintergrund`` stand nur im
  Bericht der Kamera, ``prompt_zusaetze`` nur im Befund (so las es 319). Kein Rückschritt im
  Code — aber die Generalprobe suchte im Ergebnis. Jetzt stehen beide auch in ``angewandt``:
  ``environment.hintergrund_je_kamera`` und ``prompt_zusaetze``.

Regel 3: alles synthetisch, Blender und Bildmodell sind Attrappen.
"""
from __future__ import annotations

from aiimaging import abholer, backbone, kosmo_szene

from test_grundlage_varianten import _vertrag
from test_varianten_vorgabe_e126 import _szene, himmel  # noqa: F401 — Fixture
from test_vorschau_guete import _attrappen, _rechne


# ================================================================ B1: die Vorschau haelt den Umriss

def test_die_vorschau_bekommt_m2_ganz(himmel):  # noqa: F811
    s = kosmo_szene.lies_szene(_szene(guete="vorschau"))
    assert s["maengel"] == ()
    assert s["umriss_halten"] == "im_lauf"
    assert s["prompt"].startswith("monolithic exposed concrete building")
    assert {k: v["herkunft"] for k, v in s["messschalter"].items()} == {
        "material_vorne": "vorgabe", "umriss_halten": "vorgabe", "himmel_sichtbar": "vorgabe",
        # A0051b («Immer vom Render», Owner-Entscheid 31.10.2026): auch die Vorschau startet vom Grundbild.
        "bildeingang": "vorgabe"}
    assert s["bildeingang"] == kosmo_szene.BILDEINGANG_VORGABE


def test_die_vorschau_haelt_den_umriss_auch_wenn_ein_anderes_bildmodell_bestellt_ist(himmel):  # noqa: F811
    # Die Vorschau rechnet immer VORSCHAU_BACKBONE (Entscheid 104) — massgeblich ist dieses,
    # nicht das bestellte. In voller Guete entfaellt der Halt am ungemessenen Modell weiter.
    assert backbone.VORSCHAU_BACKBONE in kosmo_szene.UMRISS_IM_LAUF_GEMESSEN
    vorschau = kosmo_szene.lies_szene(_szene(guete="vorschau", backbone="qwen-image-2.1"),
                                      streng=False)
    assert vorschau["umriss_halten"] == "im_lauf"
    voll = kosmo_szene.lies_szene(_szene(guete="voll", backbone="qwen-image-2.1"), streng=False)
    assert voll["umriss_halten"] is None
    assert "nicht gemessen" in voll["messschalter"]["umriss_halten"]["grund"]


def test_ausdruecklich_bestellt_ist_bei_der_vorschau_kein_mangel_mehr(himmel):  # noqa: F811
    s = kosmo_szene.lies_szene(_szene(guete="vorschau", umriss_halten="im_lauf"))
    assert s["maengel"] == () and s["umriss_halten"] == "im_lauf"
    aus = kosmo_szene.lies_szene(_szene(guete="vorschau", umriss_halten=False))
    assert aus["umriss_halten"] is None                     # «aus» gewinnt weiter


def test_der_vorschaulauf_reicht_die_freigabe_ans_bildmodell(tmp_path, monkeypatch):
    """Durch den ganzen Abholer, ohne den Schalter zu nennen: Die Vorschau-Kamera bekommt die
    Freigabemaske, mit 8 Schritten auf dem Vorschau-Modell — wie die volle Guete."""
    from test_material_und_umriss import _lauf
    monkeypatch.setattr(abholer, "ki_mindest_lange_seite", lambda _name: None)
    ordner, antwort, protokoll = _lauf(tmp_path, monkeypatch, guete="vorschau")
    mit_maske = [a for a in protokoll["render"] if a.umriss_halten_png]
    assert mit_maske and len(mit_maske) == len(protokoll["render"])
    assert {a.schritte for a in mit_maske} == {8}
    assert {a.backbone for a in mit_maske} == {backbone.VORSCHAU_BACKBONE}
    assert antwort["ergebnis"]["angewandt"]["messschalter"]["umriss_halten"] == {
        "wert": "im_lauf", "herkunft": "vorgabe"}


# ================================================================ B2: der Satz mit Umriss im Lauf

_MODUS = {"bestellt": "image_edit", "gerechnet": "txt2img", "abweichung": True}


def test_ohne_umriss_bleibt_der_satz_wortgleich():
    satz = kosmo_szene.modus_satz("sSE", _MODUS, "z-image-turbo")
    assert satz.startswith(kosmo_szene.SATZ_OHNE_GRUNDLAGENBILD)
    assert "ist beim Bildmodell 'z-image-turbo' NICHT angekommen" in satz
    assert "Material, Licht und Ausschnitt malt das Modell frei" in satz


def test_mit_umriss_im_lauf_sagt_der_satz_im_haus():
    satz = kosmo_szene.modus_satz("sSE", _MODUS, "z-image-turbo", umriss_im_lauf=True)
    assert satz.startswith(kosmo_szene.SATZ_OHNE_GRUNDLAGENBILD)   # die Knotenansicht sucht ihn
    assert "im Haus NICHT angekommen" in satz
    assert "ausserhalb des Hauses gilt das Cycles-Bild" in satz
    assert "Ausschnitt malt das Modell frei" not in satz


def test_der_satz_folgt_dem_vermerk_am_urteil():
    angewandt = {"angewandt": True, "art": "im_lauf"}
    assert kosmo_szene.umriss_im_lauf_angewandt(angewandt)
    assert not kosmo_szene.umriss_im_lauf_angewandt(dict(angewandt, angewandt=None))
    assert not kosmo_szene.umriss_im_lauf_angewandt(dict(angewandt, art="nachher"))
    assert not kosmo_szene.umriss_im_lauf_angewandt(None)
    hinweise: list = []
    kosmo_szene._modus_eintragen(None, [{"kamera": "nNW", "modus": dict(_MODUS),
                                         "engine": {"name": "z-image-turbo"},
                                         kosmo_szene.URTEIL_UMRISS_HALTEN: angewandt}], hinweise)
    assert len(hinweise) == 1 and "im Haus NICHT angekommen" in hinweise[0]


# ================================================================ B8: Hintergrund und Prompt-Saetze

def test_der_hintergrund_kommt_aus_dem_bericht_ohne_farben_und_datei():
    bericht = {"umgebung": {"datei": "abend__x_4k.hdr", "hintergrund": {
        "art": "himmelsbild", "kamerastrahl": "himmel", "horizont": [1, 1, 1],
        "zenit": [0, 0, 1], "weg": "himmelsbild", "grund": ""}}}
    assert abholer.hintergrund_aus_bericht(bericht) == {"art": "himmelsbild",
                                                        "kamerastrahl": "himmel"}
    assert abholer.hintergrund_aus_bericht({}) is None
    assert abholer.hintergrund_aus_bericht(None) is None


def test_angewandt_traegt_hintergrund_und_prompt_saetze(himmel):  # noqa: F811
    szene = kosmo_szene.lies_szene(_szene())
    angewandt = abholer.angewandt_der_szene(
        szene, hintergrund_je_kamera={"sSE": {"art": "himmelsbild", "kamerastrahl": "himmel"}})
    assert angewandt["environment"]["hintergrund_je_kamera"] == {
        "sSE": {"art": "himmelsbild", "kamerastrahl": "himmel"}}
    arten = [z["art"] for z in angewandt["prompt_zusaetze"]]
    assert "stimmung" in arten and "material_vorne" in arten
    # ohne Bericht kein leeres Feld
    assert "hintergrund_je_kamera" not in abholer.angewandt_der_szene(szene)["environment"]


def test_der_lauf_schreibt_die_prompt_saetze_ins_ergebnis(tmp_path, monkeypatch):
    monkeypatch.setattr(abholer, "ki_mindest_lange_seite", lambda _name: None)
    _protokoll, attrappen = _attrappen(tmp_path)
    ordner, antwort = _rechne(tmp_path, attrappen, "voll-saetze", guete="voll",
                              leerer_hintergrund=True)
    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort["grund"]
    im_ergebnis = _vertrag(ordner)["angewandt"]["prompt_zusaetze"]
    assert im_ergebnis == abholer.lies_befund(ordner)["prompt_zusaetze"]
    assert [z["art"] for z in im_ergebnis] == ["leerer_hintergrund"]


# ================================================================ S11: Lizenz offen bis ins Ergebnis

def test_lizenz_offen_steht_am_ergebnis_als_engine_license_open():
    # S11 meldete «result.lizenz_offen fehlt». Regel 1 (E128) verlangt am Lauf `lizenz_offen`
    # (Parameter des Bildmodells, Befund `engine.lizenz_offen`) und am Ergebnis
    # `engine_license_open: true` — beides stand in 327 da. Ein drittes Feld gibt es nicht.
    felder = kosmo_szene.engine_felder({"name": "qwen-image-2.1", "lizenz": "x",
                                        "lizenz_offen": True})
    assert felder["engine_license_open"] is True and "lizenz_offen" not in felder
    assert "engine_license_open" not in kosmo_szene.engine_felder({"name": "z-image-turbo"})
