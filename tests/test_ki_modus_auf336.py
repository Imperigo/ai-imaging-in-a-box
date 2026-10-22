"""Der Variantenweg: rechnet die KI-Variante vom Grundbild aus oder aus Rauschen? (auf-336)

Anlass
------
Ergebnis auf-20261022-333..336 (HomeStation, demo-kritisch): Die KI-Variante mit
``z-image-turbo`` zeigt eine andere Fensterteilung als das Cycles-Grundbild; der Bericht
nennt ``modus.bestellt image_edit``, ``modus.gerechnet txt2img``.

Die Ursache, im Code belegt (Protokoll 74, Paragraph zu 336): Der Bildweg ist **kein
ComfyUI-Graph**, sondern ``diffusers``. Der Abholer bestellt ``image_edit`` (das Cycles-Bild
als ``image``, ``strength = denoise = 0.6``); ``render._vertraegliche_argumente`` liest die
Signatur der geladenen ``ZImageControlNetPipeline`` und verwirft ``image`` und ``strength``,
weil diese Pipeline sie nicht hat. Die Pipeline beginnt dann aus reinem Rauschen (das, was in
ComfyUI ein ``EmptyLatentImage`` waere); an die Geometrie bindet allein die Tiefe ueber das
Union-ControlNet. Ein Weg mit dem Grundbild als Start (``vis.bildeingang``, «eigener Start»)
war nach Entscheid 117a ein Messschalter; seit Entscheid 138 (22.10.2026) ist er Vorgabe 0,5 fuer
Varianten (Probe ``tests/test_bildeingang_vorgabe_e138.py``).

Diese Probe prueft ohne GPU den Graphen bis zum Modellaufruf (was die Pipeline bekommt) und
den neuen Vermerk ``ki {modus, denoise, rueckfall, warnung}`` im Ergebnis.
Regel 3: nur synthetische Platzhalter.
"""
from __future__ import annotations

from aiimaging import abholer, backbone, kosmo_szene, render

# Die Attrappen aus der Probe des Adapters — dieselben, damit hier nichts anders verdrahtet ist.
from test_render import (  # noqa: F401  (pillow_attrappe ist eine Vorrichtung)
    _adapter,
    _Bildattrappe,
    _schreibe_graustufen_png,
    pillow_attrappe,
)


class _ZImageControlNetSignatur:
    """Die Aufrufform von ``ZImageControlNetPipeline`` (diffusers 0.39.0, gelesen 21.10.2026):
    Steuerbild, Start und Fahrplan — aber weder ``image`` noch ``strength``."""

    def __init__(self):
        self.gesehen = None

    def __call__(self, *, prompt=None, negative_prompt=None, control_image=None,
                 controlnet_conditioning_scale=None, num_inference_steps=None,
                 guidance_scale=None, generator=None, height=None, width=None,
                 latents=None, sigmas=None, callback_on_step_end=None):
        self.gesehen = {"control_image": control_image, "latents": latents, "sigmas": sigmas,
                        "scale": controlnet_conditioning_scale}
        return type("Aus", (), {"images": [_Bildattrappe()]})()


def _variante(tmp_path, pipeline):
    tiefe = _schreibe_graustufen_png(tmp_path / "tiefe.png")
    grundbild = _schreibe_graustufen_png(tmp_path / "schoenbild.png")
    parameter = {
        "depth_png": str(tiefe), "beauty_png": str(grundbild), "tiefe_invertiert": False,
        "seed": 7, "prompt": "Mittagslicht", "negativ_prompt": "", "controlnet_staerke": 1.0,
        "schritte": 20, "fuehrung": 0.0, "modus": render.MODUS_IMAGE_EDIT, "denoise": 0.6,
        "konditionierung": backbone.KOND_DEPTH_CONTROLNET,
        "ausgabe_png": str(tmp_path / "ki.png")}
    # `rendere` legt den Parametersatz ans Ergebnis des Adapters; hier von Hand, wie dort.
    return dict(_adapter(pipeline)(parameter), parameter=parameter)


# ── Der Graph bis zum Modell ─────────────────────────────────────────────────────────────

def test_die_variante_kommt_ohne_grundbild_und_ohne_start_beim_modell_an(tmp_path,
                                                                         pillow_attrappe):
    """Der gemessene Fall von 334-336, ohne GPU nachgestellt: Steuerbild ja, Start nein."""
    pipeline = _ZImageControlNetSignatur()
    erg = _variante(tmp_path, pipeline)
    assert pipeline.gesehen["control_image"] is not None, "die Tiefe fuehrt"
    assert pipeline.gesehen["latents"] is None, "kein Start aus dem Grundbild: reines Rauschen"
    assert erg["modus_bestellt"] == render.MODUS_IMAGE_EDIT
    assert erg["modus_gerechnet"] == render.MODUS_TXT2IMG
    hinweise = " ".join(erg["hinweise"])
    assert "'strength' (0.6)" in hinweise and "GERECHNET WURDE 'txt2img'" in hinweise


def test_der_vermerk_nennt_txt2img_denoise_eins_und_warnt(tmp_path, pillow_attrappe):
    erg = _variante(tmp_path, _ZImageControlNetSignatur())
    ki = abholer.ki_vermerk(erg)
    assert ki["modus"] == abholer.KI_TXT2IMG
    assert ki["denoise"] == 1.0, "aus Rauschen heisst: alles neu gemalt"
    assert ki["denoise_bestellt"] == 0.6
    assert ki["rueckfall"] is True and ki["grundbild_im_haus"] is False
    assert ki["grundbild_ausserhalb"] is False
    assert ki["steuerung"] == backbone.KOND_DEPTH_CONTROLNET and ki["steuerstaerke"] == 1.0
    assert ki["warnung"].startswith(abholer.SATZ_KI_RUECKFALL)
    assert "im ganzen Bild" in ki["warnung"]


def test_mit_umriss_im_lauf_sagt_die_warnung_im_haus(tmp_path, pillow_attrappe):
    erg = _variante(tmp_path, _ZImageControlNetSignatur())
    satz = kosmo_szene.modus_satz("sSE", abholer.modus_vermerk(erg), "z-image-turbo",
                                  umriss_im_lauf=True)
    ki = abholer.ki_vermerk(erg, umriss_im_lauf=True, modus_satz=satz)
    assert ki["grundbild_ausserhalb"] is True and ki["grundbild_im_haus"] is False
    assert "im Haus" in ki["warnung"]
    assert kosmo_szene.SATZ_OHNE_GRUNDLAGENBILD in ki["warnung"], "der lange Satz haengt an"


def test_mit_bildeingang_heisst_es_img2img_mit_der_staerke():
    erg = {"modus_bestellt": "bild_und_tiefe", "modus_gerechnet": "bild_und_tiefe",
           "parameter": {"bildeingang_staerke": 0.55, "denoise": 0.6,
                         "controlnet_staerke": 1.0}}
    ki = abholer.ki_vermerk(erg, bildeingang_staerke=0.55)
    assert ki["modus"] == abholer.KI_IMG2IMG and ki["denoise"] == 0.55
    assert ki["rueckfall"] is False and ki["warnung"] is None
    assert ki["grundbild_im_haus"] is True and ki["grundbild_ausserhalb"] is True


def test_bildeingang_bestellt_aber_verworfen_ist_ein_rueckfall():
    erg = {"modus_bestellt": "bild_und_tiefe", "modus_gerechnet": "txt2img",
           "parameter": {"bildeingang_staerke": 0.5}}
    ki = abholer.ki_vermerk(erg, bildeingang_staerke=0.5)
    assert ki["rueckfall"] is True and ki["denoise_bestellt"] == 0.5 and ki["denoise"] == 1.0


def test_nichts_gemeldet_ist_unbekannt_und_kein_rueckfall():
    ki = abholer.ki_vermerk({"modus_bestellt": "image_edit", "modus_gerechnet": None})
    assert ki["modus"] is None and ki["denoise"] is None and ki["rueckfall"] is False
    assert ki["grundbild_im_haus"] is None
    assert abholer.ki_vermerk({"bild_png": "x"}) is None, "ohne Bestellung kein Vermerk"


# ── Ins Ergebnis ─────────────────────────────────────────────────────────────────────────

def test_angewandt_traegt_ki_oben_und_je_kamera():
    roh = {"modus_bestellt": "image_edit", "modus_gerechnet": "txt2img",
           "parameter": {"denoise": 0.6}}
    urteile = [{"kamera": "sSE", abholer.URTEIL_KI: abholer.ki_vermerk(roh)},
               {"kamera": "nNW", abholer.URTEIL_KI: abholer.ki_vermerk(roh)}]
    aus = abholer.angewandt_mit_messschaltern({"environment": {"preset": "mittag"}}, urteile)
    assert aus["environment"] == {"preset": "mittag"}, "additiv"
    ki = aus["ki"]
    assert ki["modus"] == "txt2img" and ki["denoise"] == 1.0 and ki["rueckfall"] is True
    assert len(ki["warnungen"]) == 1, "derselbe Satz einmal, nicht je Kamera"
    assert set(ki["kameras"]) == {"sSE", "nNW"}
    assert ki["kameras"]["sSE"]["denoise_bestellt"] == 0.6


def test_ohne_ki_vermerk_fehlt_das_feld():
    assert "ki" not in abholer.angewandt_mit_messschaltern({"x": 1}, [{"kamera": "sSE"}])


# ── Was Vorgabe ist, bleibt sichtbar ─────────────────────────────────────────────────────

def test_die_vorgabe_geht_seit_entscheid_138_vom_grundbild_aus():
    """BEWUSST UMGESTELLT (Entscheid 138, Owner ueber die Zentrale, 22.10.2026, auf Grund der
    Messung auf-20261022-337): Bis dahin hiess diese Probe «die Vorgabe rechnet im Haus weiter
    ohne Grundbild» und verlangte, dass ``bildeingang`` NICHT in der Vorgabe steht (117a/126).
    Seither ist er Vorgabe 0,5 fuer Varianten. Wer das wieder aendert, braucht den Owner."""
    assert kosmo_szene.VARIANTEN_VORGABE["bildeingang"] == 0.5
    assert kosmo_szene.BILDEINGANG_VORGABE == 0.5
    eintrag = backbone.hole("z-image-turbo")
    assert eintrag.bildeingang_traegt is False
    assert eintrag.bildeingang_weg, "der Weg mit dem Grundbild als Start ist vorbereitet"
    assert eintrag.controlnet_lizenz == "Apache-2.0"
    assert kosmo_szene.BILDEINGANG_SPANNE == (0.05, 1.0)
