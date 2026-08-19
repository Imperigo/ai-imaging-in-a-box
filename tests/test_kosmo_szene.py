"""Die Szenennaht — und die drei Stellen, an denen wir dem fremden Vertrag NICHT folgen.

Der fremde Vertrag (`kosmovis.render-scene/v1` und `render-result/v2`) ist gut gebaut.
Er schreibt aber an drei Stellen Vorgabewerte fest, von denen wir inzwischen **gemessen**
haben, dass sie nicht stimmen. Sie stillschweigend zu bedienen hiesse, einen bekannten
Fehler in eine fremde Oberfläche zu tragen, wo ihn niemand mehr findet.

Die Feldnamen hier sind **wörtlich aus den Schemadateien gelesen**, nicht aus einem
Bericht abgeschrieben. In diesem Ökosystem erzeugt ein erratener Feldname keine
Fehlermeldung, sondern eine tote Kante.
"""
from __future__ import annotations

import math

import pytest

from aiimaging import geometrie_qa, stil_qa
from aiimaging import kosmo_szene as ks


def szene(**kw) -> dict:
    """Eine gültige fremde Szene; ``kw`` überschreibt einzelne Blöcke."""
    grund = {
        "schema": ks.SCHEMA_SZENE,
        "geometry": {"path": "/synthetisch/modell.glb", "format": "glb"},
        "out": "/synthetisch/aus",
        "render": {"resolution": [1600, 1000], "samples": 128, "faithful": 0.8},
        "style": {"mode": "none", "refs": [], "prompt": ""},
        "vis": {"skip": False, "backbone": "qwen", "upscale": False},
    }
    grund.update(kw)
    return grund


# --------------------------------------------------------------------------------------
# 1 · Brennweite und Bildwinkel
# --------------------------------------------------------------------------------------

def test_der_rundlauf_ist_verlustfrei():
    """Hin und zurück muss dieselbe Zahl ergeben — sonst driftet die Naht bei jedem Lauf."""
    for f in (24.0, 28.0, 35.0, 50.0, 85.0):
        assert ks.fov_zu_brennweite(ks.brennweite_zu_fov(f)) == pytest.approx(f)


def test_die_bekannten_werte_stimmen():
    """28 mm auf Kleinbild sind rund 65° horizontal — nachrechenbar, nicht geraten."""
    assert ks.brennweite_zu_fov(28.0) == pytest.approx(65.47, abs=0.01)
    assert ks.brennweite_zu_fov(50.0) == pytest.approx(39.60, abs=0.01)


def test_die_achse_des_fremden_fov_ist_eine_annahme_und_steht_dabei():
    """Die gefährlichste Sorte Unklarheit: Beide Lesarten liefern eine plausible Zahl.

    Der fremde Vertrag nennt sein Feld schlicht ``fov`` und sagt nicht, um welche Achse
    es geht. Bei einem 16:9-Bild ist der Unterschied fast ein Faktor zwei. Wir legen uns
    fest — und schreiben dazu, dass es eine Festlegung ist.
    """
    import inspect
    quelle = inspect.getdoc(ks.brennweite_zu_fov)
    assert "horizontal" in quelle
    assert "Annahme und keine Messung" in quelle


@pytest.mark.parametrize("kaputt", [0.0, -28.0, float("nan"), float("inf"), "28", True])
def test_unbrauchbare_brennweite_wird_abgewiesen(kaputt):
    with pytest.raises(ks.SzenenError):
        ks.brennweite_zu_fov(kaputt)


def test_eine_brennweite_ausserhalb_ihrer_spanne_faellt_hier_auf_und_nicht_dort():
    """Ihr Schema lässt nur 10–120° zu und weist den Auftrag sonst ab.

    Ein abgewiesener Auftrag zwei Stufen später ist teurer als ein Fehler hier: Dort
    fehlt der Zusammenhang, und der Owner sieht nur, dass nichts passiert.
    """
    with pytest.raises(ks.SzenenError, match="würde den Auftrag abweisen"):
        ks.kamera_zu_spec({"kuerzel": "n", "auge": (0, 0, 1.7),
                           "blick_auf": (0, 10, 5), "brennweite_mm": 8.0})


def test_kameras_ueberstehen_den_rundlauf():
    satz = {"kuerzel": "nNE", "auge": (12.5, -30.0, 1.7),
            "blick_auf": (0.0, 0.0, 5.7), "brennweite_mm": 28.0}
    zurueck = ks.spec_zu_kamera(ks.kamera_zu_spec(satz))
    assert zurueck["kuerzel"] == "nNE"
    assert zurueck["auge"] == pytest.approx(satz["auge"])
    assert zurueck["blick_auf"] == pytest.approx(satz["blick_auf"])
    assert zurueck["brennweite_mm"] == pytest.approx(28.0)


@pytest.mark.parametrize("kaputt", [
    {"target": [0, 0, 0], "fov": 50},                       # position fehlt
    {"position": [0, 0], "target": [0, 0, 0], "fov": 50},   # zwei statt drei
    {"position": [0, 0, "x"], "target": [0, 0, 0]},         # keine Zahl
    None, 42,
])
def test_unbrauchbare_kameraspec_wird_abgewiesen(kaputt):
    with pytest.raises(ks.SzenenError):
        ks.spec_zu_kamera(kaputt)


# --------------------------------------------------------------------------------------
# 2 · Das Backbone, das sich dort nicht ausdrücken lässt
# --------------------------------------------------------------------------------------

def test_unser_vorgabe_backbone_passt_jetzt_in_ihre_liste():
    """**Umgedreht am 19.08.2026 — der Befund ist erledigt, nicht überbrückt.**

    Hier stand bis dahin das Gegenteil: Unser Vorgabewert liess sich dort nicht
    ausdrücken, und das war ausdrücklich **zu melden statt zu überbrücken**. Genau das
    ist geschehen — die Meldung ging hinüber, und der fremde Vertrag führt
    ``z-image-turbo`` jetzt selbst.

    Der Test dreht sich damit um, und das ist der ganze Sinn der damaligen Fassung: Sie
    hat die Lücke festgehalten, bis jemand sie schloss. Ein Test, der eine Lücke
    beschreibt, gehört geändert, wenn die Lücke zu ist — nicht vorher.

    *Und die Lehre aus dem Demolauf, der es aufdeckte:* Ihre Seite zu ergänzen genügte
    nicht. Die Naht trägt erst, wenn **beide** Listen den Namen kennen.
    """
    from aiimaging.backbone import VORGABE_BACKBONE
    antwort = ks.backbone_nach_fremd(VORGABE_BACKBONE)
    assert antwort["ausdrueckbar"] is True
    assert antwort["kuerzel"] == VORGABE_BACKBONE


def test_flux2_klein_ist_entgegen_dem_ersten_anschein_zulaessig():
    """Eine Berichtigung an mir selbst, die ein Test gefangen hat.

    Im ersten Entwurf stand hier — und im Modul-Docstring —, „zwei der vier fremden
    Einträge sind FLUX und damit unter Regel 1 ausgeschlossen". **Das ist falsch.**
    ``flux2-klein`` ist FLUX.2-klein und **Apache-2.0**; ausgeschlossen ist allein
    ``flux-krea``, wofür wir folgerichtig gar keinen Registry-Eintrag haben.

    Eine falsche Aussage über den Vertrag eines anderen wäre die peinlichste Sorte
    Fehler — und in einem Docstring wäre sie nie wieder aufgefallen.
    """
    antwort = ks.backbone_von_fremd("flux2-klein")
    assert antwort["bekannt"] is True
    assert antwort["zulaessig"] is True


def test_ein_unbekanntes_fremdes_backbone_faellt_nicht_auf_die_vorgabe_zurueck():
    """Ein stillschweigend ersetztes Modell wäre ein anderes Bild unter demselben Auftrag."""
    antwort = ks.backbone_von_fremd("gibtsnicht")
    assert antwort["name"] is None
    assert antwort["bekannt"] is False
    assert "NICHT auf die Vorgabe zurückgefallen" in antwort["begruendung"]


def test_flux_krea_hat_bewusst_keine_entsprechung():
    """Es ist ein FLUX-Ableger — wir haben keinen Eintrag dafür und sollen keinen bekommen."""
    assert "flux-krea" in ks.FREMDE_BACKBONES
    assert "flux-krea" not in ks.BACKBONE_VON_FREMD


def test_ein_unbekanntes_backbone_ist_ein_mangel_und_keine_warnung():
    """Ohne Backbone wüssten wir nicht, womit wir rendern — das hält den Lauf auf."""
    gelesen = ks.lies_szene(szene(vis={"backbone": "flux-krea"}))
    assert any("keine Entsprechung" in m for m in gelesen["maengel"])


# --------------------------------------------------------------------------------------
# 3 · Ihre Szene lesen
# --------------------------------------------------------------------------------------

def test_die_aufloesung_ist_dort_ein_paar_und_traegt_das_seitenverhaeltnis():
    """Unsere Kette rendert seit dem 19.08. nicht mehr zwingend quadratisch — gut so."""
    gelesen = ks.lies_szene(szene())
    assert (gelesen["aufloesung"], gelesen["hoehe"]) == (1600, 1000)


def test_faithful_wird_abgebildet_und_der_verlust_dabei_benannt():
    """Ein einzelner Regler von 0 bis 1 kann drei Grössen nicht ausdrücken.

    Und die Wirkung ist nicht einmal monoton: `auf-20260818-13` hat 0.80 besser gemessen
    als 1.00. Wer „treuer" will und hochdreht, bekommt weniger.
    """
    gelesen = ks.lies_szene(szene())
    assert gelesen["controlnet_staerke"] == 0.8
    text = " ".join(gelesen["warnungen"])
    assert "nicht monoton" in text
    assert "denoise" in text


def test_ein_format_das_wir_nicht_koennen_ist_ein_mangel():
    """Abgelehnt, statt zwei Stufen später unverständlich zu scheitern."""
    gelesen = ks.lies_szene(szene(geometry={"path": "/x/m.fbx", "format": "fbx"}))
    assert any("verarbeiten wir nicht" in m for m in gelesen["maengel"])
    assert "fbx" in ks.FREMDE_FORMATE and "fbx" not in ks.UNSERE_FORMATE


def test_gespeicherte_kameras_sind_ein_mangel_und_kein_stiller_ersatz():
    """Sonst rendern wir andere Blickwinkel als bestellt — und niemand merkt es."""
    gelesen = ks.lies_szene(szene(cameras="saved"))
    assert any("stillschweigend" in m for m in gelesen["maengel"])


def test_eine_kameraliste_wird_uebersetzt():
    gelesen = ks.lies_szene(szene(cameras=[
        {"name": "n", "position": [0, -50, 1.7], "target": [0, 0, 5], "fov": 65.47}]))
    assert gelesen["kameras"][0]["kuerzel"] == "n"
    assert gelesen["kameras"][0]["brennweite_mm"] == pytest.approx(28.0, abs=0.01)


def test_eine_fremde_schemakennung_wird_gemeldet_und_nicht_verweigert():
    """Der Vertrag kann sich ändern — dann stimmt hier vielleicht ein Feldname nicht mehr."""
    gelesen = ks.lies_szene(szene(schema="kosmovis.render-scene/v9"))
    assert any("Schemakennung" in w for w in gelesen["warnungen"])


def test_ohne_geometrie_gibt_es_nichts_zu_rendern():
    with pytest.raises(ks.SzenenError, match="geometry.path"):
        ks.lies_szene({"out": "/x"})


def test_eine_fehlende_sonnenangabe_wird_nicht_verschwiegen():
    """Unser Runner setzt eine feste Sonne — der Sonnenstand des Auftrags wird ignoriert."""
    assert any("Sonnenangabe" in w for w in ks.lies_szene(szene())["warnungen"])


# --------------------------------------------------------------------------------------
# 4 · Das Ergebnis — und die Schwelle, die wir NICHT übernehmen
# --------------------------------------------------------------------------------------

def geo_urteil(score=0.80, bestanden=True) -> dict:
    return {"score": score, "spearman": -0.95, "geom_iou": 0.7,
            "schwelle": geometrie_qa.SCHWELLE_GEOMETRIE, "bestanden": bestanden}


def stil_urteil(score=0.75, bestanden=True) -> dict:
    return {"score": score, "schwelle": stil_qa.SCHWELLE_STIL,
            "einbetter_name": "siglip2-base", "bestanden": bestanden}


def test_wir_senden_niemals_ihre_stil_schwelle_von_0_30():
    """**Die wichtigste Zusicherung dieses Moduls.**

    Ihr Vertrag hat ``threshold: 0.3`` als Vorgabe. Wir haben an 4950 Bildpaaren
    gemessen, dass der Boden von SigLIP 2 bei 0.526 liegt — gegen 0.30 besteht **jedes
    beliebige Bildpaar** (`auf-20260818-11`). Ein Abzeichen „Stil bestanden" gegen 0.30
    bedeutet nichts.

    Ihn zu bedienen hiesse, einen bekannten Fehler in eine fremde Oberfläche zu tragen,
    wo ihn niemand mehr findet.
    """
    ergebnis = ks.als_ergebnis("vis-1-abc123", ["/x/a.png"], stil_urteil=stil_urteil())
    assert ergebnis["qa"]["style"]["threshold"] == stil_qa.SCHWELLE_STIL
    assert ergebnis["qa"]["style"]["threshold"] > 0.5
    assert ergebnis["qa"]["style"]["threshold"] != 0.3


def test_wir_senden_niemals_ihr_verfahren_dinov3():
    """Unser Einbetter ist seit Sitzung 06 SigLIP 2. Ein falsches Verfahren im Abzeichen
    macht die Zahl unvergleichbar — und niemand sieht es der Zahl an."""
    ergebnis = ks.als_ergebnis("vis-1-abc123", [], stil_urteil=stil_urteil())
    assert ergebnis["qa"]["style"]["method"] == "siglip2-base"
    assert ergebnis["qa"]["style"]["method"] != "dinov3"


def test_die_abweichung_wird_ausdruecklich_gemeldet():
    """Wer in der fremden Oberfläche ein Abzeichen sieht, soll den Massstab nachlesen können."""
    ergebnis = ks.als_ergebnis("vis-1-abc123", [], stil_urteil=stil_urteil())
    text = " ".join(ergebnis["hinweise"])
    assert "0.526" in text and "auf-20260818-11" in text


def test_das_urteil_nennt_wogegen_geprueft_wurde():
    """Ein rotes Abzeichen ohne Massstab zwingt zum Rückfragen."""
    ergebnis = ks.als_ergebnis("vis-1-abc123", [], geometrie_urteil=geo_urteil(),
                               stil_urteil=stil_urteil())
    grund = ergebnis["qa"]["verdict"]["reason"]
    assert "Geometrie" in grund and "Stil" in grund
    assert str(geometrie_qa.SCHWELLE_GEOMETRIE) in grund


def test_beide_gates_muessen_bestehen():
    beide = ks.als_ergebnis("vis-1-abc123", [], geometrie_urteil=geo_urteil(),
                            stil_urteil=stil_urteil())
    assert beide["qa"]["verdict"]["passed"] is True
    einer = ks.als_ergebnis("vis-1-abc123", [], geometrie_urteil=geo_urteil(bestanden=False),
                            stil_urteil=stil_urteil())
    assert einer["qa"]["verdict"]["passed"] is False


def test_ohne_qa_heisst_nicht_durchgefallen_sondern_ungeprueft():
    """Ihr Vertrag kennt für ``verdict.passed`` nur wahr und falsch.

    Wir haben sonst überall ein drittes „nicht messbar" — hier lässt es sich nicht
    ausdrücken. Also steht es im Grund, statt verlorenzugehen.
    """
    ergebnis = ks.als_ergebnis("vis-1-abc123", ["/x/a.png"])
    assert ergebnis["qa"]["verdict"]["passed"] is False
    assert "NICHT durchgefallen" in ergebnis["qa"]["verdict"]["reason"]


def test_die_geometrie_kennzahlen_gehen_einzeln_mit():
    """Ihr Vertrag verlangt `spearman` und `geom_iou` getrennt — nicht nur den Score."""
    ergebnis = ks.als_ergebnis("vis-1-abc123", [], geometrie_urteil=geo_urteil())
    g = ergebnis["qa"]["geometry"]
    assert g["spearman"] == -0.95 and g["geom_iou"] == 0.7
    assert g["geometry_fidelity"] == 0.80


def test_eine_unpassende_auftragskennung_wird_gemeldet_und_nicht_umbenannt():
    """Eine Kennung ist die Klammer zwischen Auftrag, Bildern und Protokoll.

    Wer sie an der Naht still ändert, macht ein Ergebnis unauffindbar — und die fremde
    Warteschlange weist sie ohnehin erst bei sich ab, nicht bei uns.
    """
    ergebnis = ks.als_ergebnis("unser-eigener-name", [])
    assert ergebnis["job_id"] == "unser-eigener-name"        # NICHT umbenannt
    assert any("abgewiesen" in h for h in ergebnis["hinweise"])


@pytest.mark.parametrize("kennung,passt", [
    ("vis-1-abc123", True), ("vis-1755600000-0f9e2a", True),
    ("vis-1-ABC123", False), ("vis-abc-123456", False), ("job-1-abc123", False),
    ("", False), (None, False), (42, False),
])
def test_die_form_der_fremden_kennung_wird_woertlich_geprueft(kennung, passt):
    assert ks.pruefe_job_id(kennung)["passt"] is passt


def test_die_strikte_fassung_traegt_nur_ihre_felder():
    """Ihr Schema lässt Zusatzfelder in der Regel durch — „in der Regel" ist keine Zusage."""
    voll = ks.als_ergebnis("vis-1-abc123", [], stil_urteil=stil_urteil())
    strikt = ks.nur_vertragsfelder(voll)
    assert "hinweise" in voll and "hinweise" not in strikt
    assert set(strikt) <= {"schema", "job_id", "images", "ai_variant", "qa", "timings"}


def test_die_schemakennung_steht_im_ergebnis():
    assert ks.als_ergebnis("vis-1-abc123", [])["schema"] == ks.SCHEMA_ERGEBNIS


# ======================================================================================
# Die eigene Schwelle ist noch kein Gate — und das steht in den Daten
# ======================================================================================

def test_ohne_nullprobe_wird_die_eigene_schwelle_als_unkalibriert_gemeldet():
    """**Eine Ehrlichkeitspflicht gegenüber der Gegenseite.**

    Wir werfen ihrem Vertrag vor, seine Stil-Schwelle von 0.30 sei kein Gate. Es wäre
    unredlich, dabei zu verschweigen, was wir am 20.08.2026 über die **eigene** gemessen
    haben: Weisses Rauschen erreicht 0.7217 und besteht damit; ein perfektes Bild erreicht
    auf einer freigestellten Szene nur 0.64 und besteht nicht.

    Der Satz muss dort stehen, wo das Abzeichen gelesen wird — nicht nur in einem
    Übergabeblatt, das niemand aufschlägt, während er auf ein Häkchen sieht.
    """
    ergebnis = ks.als_ergebnis("vis-1787123048-098c6e", ["a.png"],
                            geometrie_urteil={"score": 0.71, "bestanden": True})
    assert "NICHT kalibriert" in ergebnis["qa"]["verdict"]["reason"]
    hinweise = " ".join(ergebnis["hinweise"])
    assert "weisses Rauschen" in hinweise
    assert "0.7217" in hinweise
    assert "noch nicht kalibriert" in hinweise


def test_mit_nullprobe_entfaellt_die_warnung():
    """Sobald ein Anker vorliegt, ist der Score eingeordnet und die Warnung überflüssig."""
    ergebnis = ks.als_ergebnis("vis-1787123048-098c6e", ["a.png"],
                            geometrie_urteil={"score": 0.71, "bestanden": True,
                                              "nullanker": {"rauschen": 0.30}})
    assert "NICHT kalibriert" not in ergebnis["qa"]["verdict"]["reason"]
    assert not [h for h in ergebnis["hinweise"] if "kalibriert" in h]


def test_ohne_geometrie_urteil_keine_geometriewarnung():
    """Wo nichts gemessen wurde, wird auch nichts über eine Schwelle behauptet."""
    ergebnis = ks.als_ergebnis("vis-1787123048-098c6e", ["a.png"])
    assert not [h for h in ergebnis["hinweise"] if "Geometrie-Schwelle" in h]
    assert "Keine QA gelaufen" in ergebnis["qa"]["verdict"]["reason"]


def test_die_warnung_ueberlebt_die_beschraenkung_auf_vertragsfelder():
    """`nur_vertragsfelder` wirft die Hinweise weg — der Satz im verdict bleibt.

    Wer strikt gegen das fremde Schema sendet, soll die Warnung trotzdem sehen: Sie steht
    in `verdict.reason`, und das ist ein Vertragsfeld.
    """
    ergebnis = ks.als_ergebnis("vis-1787123048-098c6e", ["a.png"],
                            geometrie_urteil={"score": 0.71, "bestanden": True})
    knapp = ks.nur_vertragsfelder(ergebnis)
    assert "hinweise" not in knapp
    assert "NICHT kalibriert" in knapp["qa"]["verdict"]["reason"]


# ---------------------------------------------------------------------------------------
# Die Naht ist zweiseitig — Demolauf 1, 19.08.2026
# ---------------------------------------------------------------------------------------
#
# Der fremde Vertrag bekam `z-image-turbo` auf unsere Meldung hin. Beim naechsten Lauf
# wies DIESE Seite den Namen ab, weil `FREMDE_BACKBONES` nicht mitgewachsen war. Ein
# vollstaendiger Auftrag blieb liegen, mit richtiger Begruendung und ohne Wirkung.

def test_unser_vorgabe_backbone_ist_von_drueben_erreichbar():
    """Was wir selbst als Vorgabe fahren, muss der fremde Vertrag benennen koennen."""
    from aiimaging import backbone as _b
    from aiimaging import kosmo_szene as _k
    assert _b.VORGABE_BACKBONE in _k.FREMDE_BACKBONES
    assert _k.BACKBONE_VON_FREMD[_b.VORGABE_BACKBONE] == _b.VORGABE_BACKBONE


def test_jedes_zulaessige_fremde_kuerzel_hat_eine_zuordnung():
    """Ausser `flux-krea` — das ist unter Regel 1 ausgeschlossen und soll fehlen."""
    from aiimaging import kosmo_szene as _k
    ohne = [k for k in _k.FREMDE_BACKBONES if k not in _k.BACKBONE_VON_FREMD]
    assert ohne == ["flux-krea"], f"ohne Zuordnung: {ohne}"
