"""Die dritte Antwort muss durch die Vertragsgrenze — sonst ist sie auf halbem Weg verloren.

**Der Anlass sind zwei Befunde derselben Tage.** Am 23.08. hat dieses Projekt eine dritte
Antwort eingeführt: *nicht zuständig*, neben *bestanden* und *durchgefallen*. Am selben
Abend meldete die HomeStation, dass die Oberfläche unser Ergebnis wegen `null` verwirft —
zwei fertige Bilder lagen ungesehen auf der Platte.

Seit **P-NULLGEOMETRIE** (KosmoOrbit, 24.08.2026) nehmen die **Zahlenfelder** null an,
`threshold` eingeschlossen. Damit steht die Hälfte: Die Zahlen stehen richtig auf `null`.

**Was `null` nicht kann, ist `passed`.** Das ist im fremden Vertrag ein Wahrheitswert und
trägt kein Drittes. Ein `bestanden: None` unserer Seite wird dort unweigerlich zu
`passed: false` — und sieht aus wie ein durchgefallenes Bild.

Diese Datei prüft, dass der **Satz daneben** die drei Lagen unterscheidet. `reason` ist ein
Vertragsfeld und überlebt `nur_vertragsfelder`; ein eigenes Statusfeld täte das nicht — und
was kein Vertragsfeld ist, landet daneben oder gar nicht.

Die drei Lagen verlangen **verschiedene Handgriffe**, und genau darum müssen sie
unterscheidbar sein:

    nicht gemessen    → einen Lauf nachholen
    nicht zuständig   → andere Szene oder anderer Schätzer
    Rahmung zu weit   → näher heranfahren
"""
from __future__ import annotations

import pytest

from aiimaging import kosmo_szene as k

JOB = "vis-1-abcdef"


def _reason(urteil: dict) -> str:
    e = k.als_ergebnis(JOB, ["a.png"], geometrie_urteil=urteil)
    return e["qa"]["verdict"]["reason"]


def _passed(urteil: dict) -> bool:
    return k.als_ergebnis(JOB, ["a.png"],
                          geometrie_urteil=urteil)["qa"]["verdict"]["passed"]


# --------------------------------------------------------------------------------------
# 1 · Die drei Lagen sind unterscheidbar
# --------------------------------------------------------------------------------------

def test_nicht_gemessen_sagt_dass_ein_lauf_fehlt():
    grund = _reason({"score": None, "bestanden": None})

    assert "NICHT GEMESSEN" in grund
    assert "ein Lauf fehlt" in grund


def test_nicht_zustaendig_sagt_dass_die_szene_es_nicht_hergibt():
    """Nicht beantwortbar ist etwas anderes als unbeantwortet.

    Ein Lauf mehr hilft hier nicht — hinter dem Umriss steht kein Himmel, und das bleibt
    so, egal wie oft man rendert.
    """
    grund = _reason({"score": 0.9, "bestanden": None,
                     "paarurteil": {"zustaendig": False}})

    assert "NICHT ZUSTAENDIG" in grund
    assert "nicht beantwortbar" in grund


def test_die_rahmung_sagt_dass_naeher_heranfahren_hilft():
    """Und ausdrücklich, dass eine gesenkte Schwelle nicht hilft.

    Ohne diesen Halbsatz ist die naheliegendste Reaktion auf ein rotes Abzeichen die
    falsche — dieses Projekt hat den Satz «wer die Schwelle senkt, hat aufgegeben» nicht
    umsonst an drei Stellen stehen.
    """
    grund = _reason({"score": 0.1, "bestanden": None,
                     "torchance": {"lage": "zu_klein"}})

    assert "NICHT BEURTEILBAR (Rahmung)" in grund
    assert "naehere Kamera" in grund
    assert "gesenkte Schwelle nicht" in grund


def test_die_rahmung_geht_der_zustaendigkeit_vor():
    """Beide zugleich: Konnte der Lauf schon aus Rahmungsgründen nicht bestehen, ist das
    die erste Auskunft — sie erklärt auch, warum das zweite Mass nichts fand.
    """
    grund = _reason({"score": 0.1, "bestanden": None,
                     "torchance": {"lage": "zu_klein"},
                     "paarurteil": {"zustaendig": False}})

    assert "Rahmung" in grund
    assert "NICHT ZUSTAENDIG" not in grund


# --------------------------------------------------------------------------------------
# 2 · Ein echter Durchfall bleibt ein echter Durchfall
# --------------------------------------------------------------------------------------

def test_ein_durchgefallenes_bild_bekommt_keine_ausrede():
    """**Die Gegenprobe, ohne die alles darüber wertlos wäre.**

    Wer jedem roten Abzeichen einen Erklärsatz beigibt, hat kein Tor mehr, sondern eine
    Ausredenmaschine.
    """
    grund = _reason({"score": 0.2, "bestanden": False, "nullanker": {"rauschen": 0.1}})

    assert "NICHT" not in grund
    assert "Geometrie 0.2 gegen" in grund


def test_ein_bestandenes_bild_bekommt_ebenfalls_keine_ausrede():
    """Dasselbe für das grüne Abzeichen — an einem **vollständigen** Lauf.

    .. note::
       **Am 26.08.2026 nachmittags ergänzt: ``rho_maske``.** Ohne dieses Feld beschreibt
       das Urteil einen Lauf, bei dem der Maskenweg *nicht* lief — und seit demselben Tag
       trägt ein solcher Lauf den Vermerk «RICHTUNG NICHT GEPRUEFT».

       *Das ist keine Ausrede, sondern das Gegenteil:* Es qualifiziert ein grünes
       Abzeichen, das sonst mehr verspräche, als gemessen wurde. Der Nachbartest dieser
       Datei sagt es selbst — *«ein grünes Abzeichen ohne Messung»* ist die gefährliche
       Richtung.

       Die Zusicherung hier bleibt: Ein Lauf, bei dem **alles** gemessen wurde, bekommt
       keinen Erklärsatz. Der neue Vermerk ist in `test_kosmo_szene.py` geprüft, samt der
       Arithmetik, aus der folgt, dass er bei einem **roten** Abzeichen nichts zu suchen
       hat.
    """
    urteil = {"score": 0.9, "bestanden": True, "nullanker": {"rauschen": 0.1},
              "rho_maske": -0.85}

    assert _passed(urteil) is True
    assert "NICHT" not in _reason(urteil)


def test_ein_bestandenes_bild_ohne_richtungspruefung_bekommt_den_vermerk():
    """**Die Gegenprobe zur Ergänzung oben.**

    Ohne sie stünde in dieser Datei nur noch, dass ein vollständiger Lauf schweigt — und
    niemand sähe, dass ein unvollständiger es nicht tut.
    """
    urteil = {"score": 0.9, "bestanden": True, "nullanker": {"rauschen": 0.1},
              "rho_maske": None}

    assert _passed(urteil) is True
    assert "RICHTUNG NICHT GEPRUEFT" in _reason(urteil)


@pytest.mark.parametrize("urteil", [
    {"score": None, "bestanden": None},
    {"score": 0.9, "bestanden": None, "paarurteil": {"zustaendig": False}},
    {"score": 0.1, "bestanden": None, "torchance": {"lage": "zu_klein"}},
])
def test_passed_bleibt_in_allen_drei_lagen_false(urteil):
    """`passed` ist im fremden Vertrag ein Wahrheitswert und trägt kein Drittes.

    Ihn auf `true` zu setzen, weil «es ja nicht durchgefallen ist», wäre genau die
    gefährliche Richtung: ein grünes Abzeichen ohne Messung.
    """
    assert _passed(urteil) is False


# --------------------------------------------------------------------------------------
# 3 · Der Satz überlebt die strenge Fassung des Vertrags
# --------------------------------------------------------------------------------------

def test_die_lage_steht_in_einem_VERTRAGSFELD_und_nicht_daneben():
    """**Sonst wäre sie die nächste tote Kante — nur über die Vertragsgrenze hinweg.**

    `nur_vertragsfelder` streicht alles, was nicht im fremden Schema steht. Ein eigenes
    `status`-Feld verschwände dort lautlos; `verdict.reason` überlebt.
    """
    ergebnis = k.als_ergebnis(JOB, ["a.png"], geometrie_urteil={
        "score": 0.9, "bestanden": None, "paarurteil": {"zustaendig": False}})

    streng = k.nur_vertragsfelder(ergebnis)

    assert "NICHT ZUSTAENDIG" in streng["qa"]["verdict"]["reason"]


def test_die_zahlen_stehen_dabei_auf_null_und_nicht_auf_einer_erfundenen_zahl():
    """0.0 hiesse «gemessen, katastrophal». `null` heisst «nicht gemessen».

    Die Verwechslung dieser beiden ist der Fehler, gegen den diese ganze QA gebaut ist —
    am 21.08. erreichte ein Bild OHNE Bauwerk 0.9848 gegen 0.9703 für das perfekte.
    """
    ergebnis = k.als_ergebnis(JOB, ["a.png"],
                              geometrie_urteil={"score": None, "bestanden": None})

    geo = ergebnis["qa"]["geometry"]
    assert geo["geometry_fidelity"] is None
    assert geo["spearman"] is None
