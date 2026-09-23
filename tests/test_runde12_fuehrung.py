"""Runde 12 · Die Führung über den Regler, der wirkt — Befund vom 23.09.2026.

Was die HomeStation nachgelesen hat (``auftraege/ergebnisse/auf-20260923-157.json``)
------------------------------------------------------------------------------------
``qwen-image-edit-2511`` läuft über ``QwenImageEditPlusPipeline`` (diffusers 0.39.0).
Deren wirksamer Führungsregler heisst ``true_cfg_scale`` (Signaturvorgabe 4.0);
``guidance_scale`` ist bei diesen Gewichten wirkungslos (``transformer/config.json``:
``"guidance_embeds": false``). Die klassifikatorfreie Führung rechnet NUR, wenn
``true_cfg_scale > 1`` UND ``negative_prompt`` nicht ``None`` ist (Pipeline Z.708/719).
``render.py`` schickte ``parameter["negativ_prompt"] or None`` — ein leerer
Negativprompt wurde ``None``, und jeder Lauf ohne eigenen Negativprompt rechnete ganz
OHNE Führung. Die Modellkarte bei den Gewichten (README Z.53-62) schickt
``true_cfg_scale`` 4.0 und ``negative_prompt`` ``" "``.

Was diese Datei bewacht, und zwar über den Produktweg
-----------------------------------------------------
Geprüft wird, was **bei der Pipeline ankommt**: ``render.rendere`` mit dem ECHTEN
Adapter (``render._pipeline_adapter``) über Pipeline-Attrappen, deren Signatur die
Weiche ``genommen/verworfen`` liest. Dazu je ein Lauf über den Homeworker
(``tools/homeworker.py``) und über den Abholer (``abholer.hole_einen``) — die beiden
Wege, auf denen die HomeStation dieses Modell heute wählt.

1. ``qwen-image-edit-2511`` ohne Negativprompt: ``true_cfg_scale`` 4.0 und
   ``negative_prompt`` ``" "`` kommen an. Mit eigenem Negativprompt: dieser, unverändert.
2. Eine Pipeline ohne ``true_cfg_scale`` in der Signatur bekommt NICHTS davon — auch
   nicht den Leerprompt —, und ein Satz sagt es.
3. ``z-image-turbo`` und alle übrigen Einträge: Aufrufargumente BITGLEICH zum Stand vor
   dieser Runde (Schnappschuss, gezogen am 23.09.2026 vor der Änderung).
4. ``negativ_wirksam`` urteilt für ``qwen-image-edit-2511`` über ``true_cfg_scale`` und
   stimmt mit der Regel der Pipeline (Z.719) überein, die die Attrappe nachrechnet.
5. Die Hinweistexte: kein «fremde Entscheidung» mehr, wo guidance_scale belegt
   wirkungslos ist.

Regel 3: Alles synthetisch — Prompt, Bilder, Szene.
"""
from __future__ import annotations

import dataclasses
import sys
import types
from pathlib import Path

import pytest

from aiimaging import abholer, backbone, kosmo_szene, render

from test_abholer import _auftrag, _kette

QWEN_EDIT = "qwen-image-edit-2511"


# --------------------------------------------------------------------------------------
# Attrappen: Pillow, torch, Pipelines
# --------------------------------------------------------------------------------------

class _Bild:
    """Ein Bild, das nur sagt, woher es kommt — Tiefenkarte, Anker, umgedreht."""
    height = width = 64

    def __init__(self, art):
        self.art = art

    def convert(self, _modus):
        return self

    def save(self, ziel):
        Path(ziel).write_bytes(b"\x89PNG\r\n\x1a\n")


@pytest.fixture
def pil(monkeypatch):
    """Ein Pillow-Ersatz, der Tiefenkarte, Anker und Umkehrung unterscheidbar macht.

    Unterscheidbar, weil der Schnappschuss unten auch sagen soll, WELCHES Bild an
    ``control_image`` ankam — bei ``z-image-turbo`` das umgedrehte.
    """
    modul = types.ModuleType("PIL")
    bild = types.ModuleType("PIL.Image")
    ops = types.ModuleType("PIL.ImageOps")
    bild.open = lambda pfad: _Bild("ANKER" if "beauty" in Path(str(pfad)).name
                                   else "TIEFE")
    ops.invert = lambda b: _Bild(b.art + "_INV")
    modul.Image, modul.ImageOps = bild, ops
    for name, m in (("PIL", modul), ("PIL.Image", bild), ("PIL.ImageOps", ops)):
        monkeypatch.setitem(sys.modules, name, m)
    return modul


class _Torch:
    class cuda:                                            # noqa: N801 — wie torch
        @staticmethod
        def is_available():
            return False

    class Generator:
        def __init__(self, device=None):
            self.device = device

        def manual_seed(self, seed):
            self.seed = seed
            return self


def _aus():
    return type("Aus", (), {"images": [_Bild("ERGEBNIS")]})()


def _do_true_cfg(kw) -> bool:
    """Die Regel der Pipeline, nachgerechnet (pipeline_qwenimage_edit_plus.py Z.708/719,
    diffusers 0.39.0, gelesen in auf-20260923-157)::

        has_neg_prompt = negative_prompt is not None or negative_prompt_embeds is not None
        do_true_cfg = true_cfg_scale > 1 and has_neg_prompt
    """
    return (kw.get("true_cfg_scale", 4.0) > 1
            and (kw.get("negative_prompt") is not None
                 or kw.get("negative_prompt_embeds") is not None))


class QwenEditPlus:
    """Die Signatur von ``QwenImageEditPlusPipeline.__call__`` (diffusers 0.39.0), so weit
    unser Adapter sie anfasst: ``image``, ``true_cfg_scale``, ``guidance_scale``, kein
    ``control_image``, kein ``strength``. Die Vorgabe 4.0 ist die der Signatur (Q1)."""

    def __init__(self):
        self.aufrufe = []

    def __call__(self, *, prompt=None, negative_prompt=None, true_cfg_scale=4.0,
                 image=None, num_inference_steps=50, guidance_scale=None, generator=None,
                 height=None, width=None, callback_on_step_end=None):
        kw = {"prompt": prompt, "negative_prompt": negative_prompt,
              "true_cfg_scale": true_cfg_scale, "image": image,
              "guidance_scale": guidance_scale}
        kw["do_true_cfg"] = _do_true_cfg(kw)
        self.aufrufe.append(kw)
        return _aus()


class OhneTrueCfg:
    """Eine Pipeline mit einem Bildeingang, aber ohne ``true_cfg_scale`` in der Signatur —
    so sähe eine andere Fassung oder eine fremde Klasse unter demselben Eintrag aus."""

    def __init__(self):
        self.aufrufe = []

    def __call__(self, *, prompt=None, negative_prompt=None, image=None,
                 num_inference_steps=None, guidance_scale=None, generator=None,
                 height=None, width=None, callback_on_step_end=None):
        self.aufrufe.append({"negative_prompt": negative_prompt, "image": image,
                             "guidance_scale": guidance_scale})
        return _aus()


class NimmtAlles:
    """``**kwargs``: Die Weiche verwirft nichts — die Attrappe sieht jedes Argument, das
    der Adapter baut. Die schärfste Probe für «bitgleich»: Auch ein zusätzliches
    ``true_cfg_scale`` fiele hier auf."""

    def __init__(self):
        self.gesehen = None

    def __call__(self, **kw):
        self.gesehen = kw
        return _aus()


def _lader(pipeline):
    return lambda name, wurzel: render._pipeline_adapter(pipeline, backbone.hole(name),
                                                         _Torch())


def _dateien(tmp_path):
    (tmp_path / "tiefe.png").write_bytes(b"\x89PNG")
    (tmp_path / "beauty.png").write_bytes(b"\x89PNG")
    return tmp_path


def _auftrag_fuer(tmp_path, name, **extra):
    return render.RenderAuftrag(depth_png=str(tmp_path / "tiefe.png"), prompt="a house",
                                backbone=name, schritte=3, seed=7,
                                ausgabe_png=str(tmp_path / "b.png"), **extra)


# ======================================================================================
# 1 · qwen-image-edit-2511 rechnet MIT Führung — über den Produktweg
# ======================================================================================

def test_qwen_edit_ohne_negativprompt_bekommt_true_cfg_und_den_kartenleerprompt(
        tmp_path, pil):
    """**Der Befund, hier als Probe.** Bis zum 23.09.2026 kam ``negative_prompt=None``
    an, und die Pipeline rechnete ohne Führung."""
    _dateien(tmp_path)
    pipeline = QwenEditPlus()

    ergebnis = render.rendere(_auftrag_fuer(tmp_path, QWEN_EDIT), _lader=_lader(pipeline))

    assert ergebnis["status"] == render.STATUS_OK, ergebnis["error"]
    [kw] = pipeline.aufrufe
    assert kw["true_cfg_scale"] == 4.0
    assert kw["negative_prompt"] == " "
    assert kw["do_true_cfg"] is True, "die Führung muss nach der Regel der Pipeline laufen"
    p = ergebnis["parameter"]
    assert p["fuehrung_regler"] == "true_cfg_scale"
    assert p["fuehrung_regler_wert"] == 4.0
    assert p["negativ_prompt_karte"] == " "
    assert p["negativ_prompt"] == "", "die Bestellung wird nicht umgeschrieben"


@pytest.mark.parametrize("eigener", ["blurry, distorted", "  "])
def test_ein_ausdruecklich_gesetzter_negativprompt_geht_unveraendert_hin(
        tmp_path, pil, eigener):
    """Auch ein Negativprompt aus Leerzeichen ist eine Bestellung, keine Lücke."""
    _dateien(tmp_path)
    pipeline = QwenEditPlus()

    ergebnis = render.rendere(_auftrag_fuer(tmp_path, QWEN_EDIT, negativ_prompt=eigener),
                              _lader=_lader(pipeline))

    [kw] = pipeline.aufrufe
    assert kw["negative_prompt"] == eigener
    assert kw["true_cfg_scale"] == 4.0
    assert kw["do_true_cfg"] is True
    assert ergebnis["parameter"]["negativ_prompt_karte"] is None
    assert any("unverändert hin" in h for h in ergebnis["hinweise"])


def test_qwen_edit_im_bildbearbeitungsmodus_fuehrt_ebenso(tmp_path, pil):
    """Mit Anker (der Weg des Abholers und des Homeworkers mit ``mit_beauty``)."""
    _dateien(tmp_path)
    pipeline = QwenEditPlus()

    render.rendere(_auftrag_fuer(tmp_path, QWEN_EDIT,
                                 beauty_png=str(tmp_path / "beauty.png")),
                   _lader=_lader(pipeline))

    [kw] = pipeline.aufrufe
    assert (kw["true_cfg_scale"], kw["negative_prompt"], kw["do_true_cfg"]) == (4.0, " ",
                                                                               True)


# ======================================================================================
# 2 · Eine Pipeline ohne true_cfg_scale bekommt nichts davon — und es steht da
# ======================================================================================

def test_ohne_true_cfg_in_der_signatur_geht_weder_regler_noch_leerprompt_hin(
        tmp_path, pil):
    _dateien(tmp_path)
    pipeline = OhneTrueCfg()

    ergebnis = render.rendere(_auftrag_fuer(tmp_path, QWEN_EDIT), _lader=_lader(pipeline))

    assert ergebnis["status"] == render.STATUS_OK, ergebnis["error"]
    [kw] = pipeline.aufrufe
    assert "true_cfg_scale" not in kw
    assert kw["negative_prompt"] is None, (
        "der Leerprompt ist nur dazu da, die Führung über den Regler einzuschalten")
    satz = [h for h in ergebnis["hinweise"] if "'true_cfg_scale' (4.0) kennt diese "
                                               "Pipeline nicht" in h]
    assert len(satz) == 1, ergebnis["hinweise"]
    assert "UNBEKANNT" in satz[0] and "auf-20260923-157" in satz[0]
    assert not any(h.startswith("Nicht übergeben, weil unbekannt") and "true_cfg" in h
                   for h in ergebnis["hinweise"]), "ein Satz, nicht zwei"


def test_ohne_true_cfg_bleibt_ein_eigener_negativprompt_stehen(tmp_path, pil):
    _dateien(tmp_path)
    pipeline = OhneTrueCfg()

    render.rendere(_auftrag_fuer(tmp_path, QWEN_EDIT, negativ_prompt="blurry"),
                   _lader=_lader(pipeline))

    assert pipeline.aufrufe[0]["negative_prompt"] == "blurry"


# ======================================================================================
# 3 · Alle übrigen Einträge: bitgleich zum Stand vor dieser Runde
# ======================================================================================
#
# Gezogen am 23.09.2026 VOR der Änderung, mit denselben Attrappen wie hier
# (`NimmtAlles`, `_pipeline_adapter` über `_baue_parameter`). Bilder als ihre Herkunft,
# der Generator als (Gerät, Startwert), der Rückruf als Marke.

_HEUTE = {
    "callback_on_step_end": "RUECKRUF", "control_image": "TIEFE",
    "controlnet_conditioning_scale": 0.8, "generator": ("generator", "cpu", 7),
    "guidance_scale": None, "height": 64, "negative_prompt": None,
    "num_inference_steps": 3, "prompt": "a house", "width": 64,
}
_HEUTE_JE_FALL = {
    "leer": {},
    "negativ": {"negative_prompt": "blurry"},
    "anker": {"image": "ANKER", "strength": 0.6},
}
_HEUTE_JE_EINTRAG = {
    "z-image-turbo": {"control_image": "TIEFE_INV", "guidance_scale": 0.0},
    "qwen-image-2512": {}, "sdxl-juggernaut": {}, "sd35-large": {},
    "flux2-klein-4b": {}, "flux1-dev": {}, "flux2-dev": {},
}


def _schnappschuss(kw: dict) -> dict:
    aus = {}
    for k, v in kw.items():
        if isinstance(v, _Bild):
            aus[k] = v.art
        elif isinstance(v, _Torch.Generator):
            aus[k] = ("generator", v.device, v.seed)
        elif callable(v):
            aus[k] = "RUECKRUF"
        else:
            aus[k] = v
    return aus


_FAELLE = {"leer": {}, "negativ": {"negativ_prompt": "blurry"}, "anker": "ANKER"}


def _extra(tmp_path, fall):
    return ({"beauty_png": str(tmp_path / "beauty.png")} if fall == "anker"
            else dict(_FAELLE[fall]))


def test_der_schnappschuss_deckt_alle_eintraege_ausser_qwen_edit():
    """Kommt ein Eintrag dazu, muss er hier eingetragen werden — sonst wäre «alle
    übrigen» eine Behauptung über eine Liste, die niemand nachgeführt hat."""
    assert set(_HEUTE_JE_EINTRAG) == set(backbone.BACKBONES) - {QWEN_EDIT}
    mit_regler = [n for n, e in backbone.BACKBONES.items() if e.fuehrung_regler]
    assert mit_regler == [QWEN_EDIT]


@pytest.mark.parametrize("fall", sorted(_HEUTE_JE_FALL))
@pytest.mark.parametrize("name", sorted(_HEUTE_JE_EINTRAG))
def test_die_aufrufargumente_der_uebrigen_eintraege_sind_bitgleich(tmp_path, pil, name,
                                                                   fall):
    """Am Adapter über ``_baue_parameter`` — auch für die unter Regel 1 abgelehnten
    Einträge, die ``rendere`` gar nicht bis zur Pipeline lässt."""
    _dateien(tmp_path)
    pipeline = NimmtAlles()
    eintrag = backbone.hole(name)
    a = _auftrag_fuer(tmp_path, name, **_extra(tmp_path, fall))

    render._pipeline_adapter(pipeline, eintrag, _Torch())(render._baue_parameter(a, eintrag))

    erwartet = {**_HEUTE, **_HEUTE_JE_FALL[fall], **_HEUTE_JE_EINTRAG[name]}
    assert _schnappschuss(pipeline.gesehen) == erwartet


@pytest.mark.parametrize("fall", sorted(_HEUTE_JE_FALL))
def test_z_image_turbo_ist_ueber_rendere_bitgleich(tmp_path, pil, fall):
    """Der Vorgabe-Backbone über den ganzen Produktweg ``rendere``, ausgeschrieben."""
    _dateien(tmp_path)
    pipeline = NimmtAlles()

    ergebnis = render.rendere(
        _auftrag_fuer(tmp_path, render.VORGABE_BACKBONE, **_extra(tmp_path, fall)),
        _lader=_lader(pipeline))

    assert ergebnis["status"] == render.STATUS_OK, ergebnis["error"]
    erwartet = {
        "callback_on_step_end": "RUECKRUF", "control_image": "TIEFE_INV",
        "controlnet_conditioning_scale": 0.8, "generator": ("generator", "cpu", 7),
        "guidance_scale": 0.0, "height": 64, "negative_prompt": None,
        "num_inference_steps": 3, "prompt": "a house", "width": 64,
        **_HEUTE_JE_FALL[fall]}
    assert _schnappschuss(pipeline.gesehen) == erwartet
    p = ergebnis["parameter"]
    assert (p["fuehrung_regler"], p["fuehrung_regler_wert"], p["negativ_prompt_karte"]) \
        == (None, None, None), "nicht bestimmt — die dritte Antwort, nicht 0 oder ''"


def test_qwen_edit_ist_der_einzige_eintrag_der_sich_aendert(tmp_path, pil):
    """Die Gegenprobe zum Schnappschuss: Er ist nicht so weit, dass er alles durchliesse."""
    _dateien(tmp_path)
    pipeline = NimmtAlles()
    eintrag = backbone.hole(QWEN_EDIT)
    a = _auftrag_fuer(tmp_path, QWEN_EDIT)

    render._pipeline_adapter(pipeline, eintrag, _Torch())(render._baue_parameter(a, eintrag))

    assert _schnappschuss(pipeline.gesehen) == {**_HEUTE, "true_cfg_scale": 4.0,
                                                "negative_prompt": " "}


# ======================================================================================
# 4 · negativ_wirksam urteilt über den Regler, der wirkt
# ======================================================================================

_FORM = {"wirksam", "fuehrung", "mindestens", "backbone", "grund"}


@pytest.mark.parametrize("eigener", ["", "blurry"])
def test_negativ_wirksam_stimmt_mit_der_regel_der_pipeline_ueberein(tmp_path, pil,
                                                                    eigener):
    """Ohne und mit Negativprompt: Die Führung läuft (Attrappe rechnet Z.719 nach), und
    ``negativ_wirksam`` sagt dasselbe. Bis zum 23.09.2026 sagte es «UNBEKANNT» — über
    guidance_scale, das hier nichts schaltet."""
    _dateien(tmp_path)
    pipeline = QwenEditPlus()
    render.rendere(_auftrag_fuer(tmp_path, QWEN_EDIT, negativ_prompt=eigener),
                   _lader=_lader(pipeline))

    urteil = render.negativ_wirksam(QWEN_EDIT)

    assert set(urteil) == _FORM, "die Rückgabeform bleibt"
    assert urteil["wirksam"] is pipeline.aufrufe[0]["do_true_cfg"] is True
    assert urteil["fuehrung"] == 4.0
    assert "true_cfg_scale" in urteil["grund"] and "auf-20260923-157" in urteil["grund"]


def test_eine_mitgegebene_fuehrung_aendert_das_urteil_bei_qwen_edit_nicht():
    """guidance_scale ist dort belegt wirkungslos — 0.0 schaltet nichts ab."""
    urteil = render.negativ_wirksam(QWEN_EDIT, fuehrung=0.0)

    assert urteil["wirksam"] is True
    assert "WIRKUNGSLOS" in urteil["grund"] and "guidance_embeds" in urteil["grund"]


def test_negativ_wirksam_der_uebrigen_bleibt():
    """Vorgabe-Backbone weiter False, ein unbestimmter weiter None — nicht still True."""
    assert render.negativ_wirksam(render.VORGABE_BACKBONE)["wirksam"] is False
    assert render.negativ_wirksam("qwen-image-2512")["wirksam"] is None


def test_die_negativlage_des_abholers_sagt_fuer_qwen_edit_wuerde_wirken():
    """Der Aufrufer im Abholer: Die Kurzzeile sagte bei qwen-edit «UNBEKANNT»."""
    lage = abholer.negativ_lage("kosmo_standard", QWEN_EDIT)
    zeile = [z for z in abholer.befund_kurz({"kameras": [], "negativ_lage": lage})
             if "Negativ-Prompt" in z][0]

    assert lage["waere_wirksam"] is True
    assert "wuerde er wirken" in zeile


# ======================================================================================
# 5 · Die Hinweistexte
# ======================================================================================

def test_der_hinweis_nennt_regler_wert_quelle_und_leerprompt(tmp_path, pil):
    _dateien(tmp_path)
    ergebnis = render.rendere(_auftrag_fuer(tmp_path, QWEN_EDIT),
                              _lader=_lader(QwenEditPlus()))

    satz = [h for h in ergebnis["hinweise"] if h.startswith("FÜHRUNG über")]
    assert len(satz) == 1, ergebnis["hinweise"]
    for teil in ("'true_cfg_scale' = 4.0", "README Z.53-62", "auf-20260923-157", "' '",
                 "zwei Transformer-Durchgänge"):
        assert teil in satz[0], teil


def test_keine_fremde_entscheidung_wo_guidance_scale_belegt_wirkungslos_ist(tmp_path,
                                                                             pil):
    """Bis zum 23.09.2026 stand hier «keine Führung (guidance_scale) bestimmt … eine
    fremde Entscheidung» — über einen Regler, den diese Gewichte nicht lesen."""
    _dateien(tmp_path)
    ergebnis = render.rendere(_auftrag_fuer(tmp_path, QWEN_EDIT),
                              _lader=_lader(QwenEditPlus()))

    text = " ".join(ergebnis["hinweise"])
    assert "fremde Entscheidung, keine eigene" not in text
    assert "keine Führung (guidance_scale) bestimmt" not in text
    assert any("guidance_scale ist bei den Gewichten" in h and "WIRKUNGSLOS" in h
               and "guidance_embeds" in h for h in ergebnis["hinweise"])


def test_eine_gesetzte_fuehrung_mit_negativprompt_heisst_bei_qwen_edit_nicht_wirkungslos(
        tmp_path, pil):
    """fuehrung=0.5 schaltet dort NICHTS ab — der alte Satz «bleibt damit WIRKUNGSLOS»
    wäre das Gegenteil des Befunds."""
    _dateien(tmp_path)
    pipeline = QwenEditPlus()
    ergebnis = render.rendere(_auftrag_fuer(tmp_path, QWEN_EDIT, fuehrung=0.5,
                                            negativ_prompt="blurry"),
                              _lader=_lader(pipeline))

    assert pipeline.aufrufe[0]["do_true_cfg"] is True
    assert not any("bleibt damit WIRKUNGSLOS" in h for h in ergebnis["hinweise"])
    assert any("fuehrung=0.5 geht zwar als guidance_scale hin" in h
               for h in ergebnis["hinweise"])


def test_mit_eigenem_regler_urteilt_guidance_scale_nicht_ueber_den_negativprompt(
        tmp_path, pil, monkeypatch):
    """Ein Eintrag mit eigenem Regler, bei dem guidance_scale NICHT als wirkungslos belegt
    ist: Der alte Satz «fuehrung=0.5 … bleibt damit WIRKUNGSLOS» wäre eine Behauptung
    über einen Regler, der dort nicht schaltet — die Führung läuft über den eigenen."""
    probe = dataclasses.replace(backbone.BACKBONES[QWEN_EDIT], name="probe-regler",
                                guidance_scale_wirkungslos=None, guidance_scale_beleg=None)
    monkeypatch.setitem(backbone.BACKBONES, "probe-regler", probe)
    _dateien(tmp_path)
    pipeline = QwenEditPlus()
    ergebnis = render.rendere(_auftrag_fuer(tmp_path, "probe-regler", fuehrung=0.5,
                                            negativ_prompt="blurry"),
                              _lader=_lader(pipeline))

    assert ergebnis["status"] == render.STATUS_OK, ergebnis["error"]
    assert pipeline.aufrufe[0]["do_true_cfg"] is True
    assert not any("bleibt damit WIRKUNGSLOS" in h for h in ergebnis["hinweise"])


def test_die_uebrigen_behalten_ihren_satz(tmp_path, pil):
    """Wo nichts belegt ist, bleibt die fremde Entscheidung eine fremde Entscheidung."""
    _dateien(tmp_path)
    ergebnis = render.rendere(_auftrag_fuer(tmp_path, "qwen-image-2512"),
                              _lader=_lader(NimmtAlles()))

    assert any("keine Führung (guidance_scale) bestimmt" in h
               for h in ergebnis["hinweise"])
    assert not any(h.startswith("FÜHRUNG über") for h in ergebnis["hinweise"])


# ======================================================================================
# 6 · Das Register nimmt nur belegte Angaben
# ======================================================================================

@pytest.mark.parametrize("aenderung", [
    {"fuehrung_regler_beleg": None},                           # ohne Beleg
    {"fuehrung_regler_beleg": "Modellkarte"},                  # ohne Auftragskennung
    {"fuehrung_regler_wert": None},                            # Regler ohne Wert
    {"fuehrung_regler": None},                                 # Wert ohne Regler
    {"fuehrung_regler": "guidance_scale"},                     # gehört in `fuehrung`
    {"guidance_scale_beleg": None},                            # Urteil ohne Beleg
    {"guidance_scale_wirkungslos": None},                      # Beleg ohne Urteil
    {"fuehrung_regler": None, "fuehrung_regler_wert": None,    # Beleg ohne Regler
     "leer_negativ_prompt": None},
])
def test_eine_unbelegte_fuehrungsangabe_kommt_nicht_ins_register(monkeypatch, aenderung):
    # Eine eigene Tabelle: Liefe eine Probe durch, stünde die Kopie sonst für alle
    # folgenden Tests im Register.
    monkeypatch.setattr(backbone, "BACKBONES", dict(backbone.BACKBONES))
    kopie = dataclasses.replace(backbone.BACKBONES[QWEN_EDIT], name="probe-kopie",
                                **aenderung)
    with pytest.raises(backbone.BackboneError):
        backbone._eintrag(kopie)
    assert "probe-kopie" not in backbone.BACKBONES


def test_die_belegte_angabe_selbst_kommt_ins_register(monkeypatch):
    """Gegenprobe: Der Riegel weist nicht einfach jede Kopie ab."""
    monkeypatch.setattr(backbone, "BACKBONES", dict(backbone.BACKBONES))
    backbone._eintrag(dataclasses.replace(backbone.BACKBONES[QWEN_EDIT],
                                          name="probe-kopie"))
    assert "probe-kopie" in backbone.BACKBONES


def test_ein_leerprompt_ohne_regler_kommt_nicht_ins_register(monkeypatch):
    monkeypatch.setattr(backbone, "BACKBONES", dict(backbone.BACKBONES))
    kopie = dataclasses.replace(backbone.BACKBONES[QWEN_EDIT], name="probe-kopie",
                                fuehrung_regler=None, fuehrung_regler_wert=None,
                                fuehrung_regler_beleg=None)
    with pytest.raises(backbone.BackboneError, match="leer_negativ_prompt"):
        backbone._eintrag(kopie)


# ======================================================================================
# 7 · Die beiden Wege der HomeStation: Homeworker und Abholer
# ======================================================================================

def test_der_abholer_waehlt_qwen_edit_ohne_backbone_angabe_und_fuehrt(tmp_path, pil):
    """**Warum diese Änderung die HomeStation im Alltag trifft:** Eine Bestellung aus
    KosmoOrbit ohne ``vis.backbone`` gilt als ``"qwen"`` (``kosmo_szene``), und ``"qwen"``
    ist ``qwen-image-edit-2511``. Der Abholer schickt nie einen Negativprompt — also rechnete
    bis zum 23.09.2026 jeder dieser Läufe ohne Führung, und ab jetzt jeder mit."""
    szene = {"schema": kosmo_szene.SCHEMA_SZENE,
             "geometry": {"path": "model.glb", "format": "glb"}, "cameras": "auto",
             "render": {"resolution": [512, 512], "samples": 64, "faithful": 0.8},
             "style": {"prompt": "ein Haus", "mode": "none"}}
    ordner = _auftrag(tmp_path, szene=szene)
    protokoll, attrappen = _kette()
    pipeline = QwenEditPlus()

    def rendere(a, **kw):
        protokoll["render"].append(a)
        return render.rendere(a, _lader=_lader(pipeline))

    attrappen["_rendere"] = rendere
    abholer.hole_einen(ordner, fremde_freigabe_gilt=True,
                       verarbeite=abholer.verarbeiter(out_wurzel=tmp_path / "aus",
                                                      nullprobe=False, **attrappen))

    assert protokoll["render"], "es wurde gar nicht gerendert"
    assert {a.backbone for a in protokoll["render"]} == {QWEN_EDIT}
    assert pipeline.aufrufe and all(
        (kw["true_cfg_scale"], kw["negative_prompt"], kw["do_true_cfg"]) == (4.0, " ", True)
        for kw in pipeline.aufrufe)


@pytest.mark.filterwarnings("ignore::aiimaging.bildlesen.SilhouettenVerlust")
def test_der_homeworker_reicht_backbone_und_negativprompt_durch_und_fuehrt(tmp_path, pil):
    """Der Homeworker wählt das Modell aus ``params['backbone']`` (so lief
    ``auf-20260921-134``). Ohne Negativprompt geht der Leerprompt hin, und der
    Parametersatz im Ergebnis sagt es."""
    import test_homeworker as th
    from aiimaging import bildschreiben

    # Der Blender-Bericht wie in `test_homeworker.bericht` — synthetisch, ohne Blender.
    grau, normalisierung = bildschreiben.normalisiere_tiefe(th._soll_meter())
    bildschreiben.schreibe_graustufen_png(tmp_path / "tiefe_norm.png", grau, th.BREITE,
                                          th.HOEHE)
    (tmp_path / "beauty.png").write_bytes(th.PNG_PLATZHALTER)
    bildschreiben.schreibe_farb_png(tmp_path / "material_id.png", th._material_id_bild(),
                                    th.BREITE, th.HOEHE)
    bericht = {
        "depth_exr": None, "depth_png": str(tmp_path / "tiefe_norm.png"),
        "depth_normalisierung": normalisierung, "depth_png_fehler": None,
        "beauty_png": str(tmp_path / "beauty.png"),
        "material_id_png": str(tmp_path / "material_id.png"),
        "material_id_tabelle": [
            {"index": 0, "name": "Boden_Platte", "farbe_srgb_8bit": list(th.MI_BODEN),
             "quelle": "material"},
            {"index": 1, "name": "Wand", "farbe_srgb_8bit": list(th.MI_WAND),
             "quelle": "material"}],
        "bbox_size_m": [8.0, 5.0, 3.0], "n_meshes": 7,
    }
    pipeline = QwenEditPlus()
    ergebnis = th.rufe_render_und_qa(
        bericht, tmp_path, {"prompt": "a house", "backbone": QWEN_EDIT},
        render_modell=render._pipeline_adapter(pipeline, backbone.hole(QWEN_EDIT),
                                               _Torch()),
        tiefen_modell=th.Tiefenattrappe(th.treue_ist_karte(bericht)))

    parameter = ergebnis["messwerte"]["render"]["parameter"]
    assert parameter["negativ_prompt_karte"] == " "
    assert parameter["fuehrung_regler"] == "true_cfg_scale"
    [kw] = pipeline.aufrufe
    assert (kw["true_cfg_scale"], kw["negative_prompt"], kw["do_true_cfg"]) == (4.0, " ",
                                                                               True)


# ── Durchsicht Runde 12: was ankam, die Schwelle, und ein Wert, der nicht die Vorgabe ist ──

def test_der_parametersatz_sagt_ob_der_regler_ankam(tmp_path, pil):
    """Der Parametersatz nennt die Bestellung; ``fuehrung_regler_angekommen`` das
    Gerechnete — dieselbe Unterscheidung wie ``modus_bestellt``/``modus_gerechnet``."""
    _dateien(tmp_path)
    mit = render.rendere(_auftrag_fuer(tmp_path, QWEN_EDIT), _lader=_lader(QwenEditPlus()))
    assert mit["parameter"]["fuehrung_regler_angekommen"] is True
    ohne = render.rendere(_auftrag_fuer(tmp_path, QWEN_EDIT), _lader=_lader(OhneTrueCfg()))
    assert ohne["parameter"]["fuehrung_regler_angekommen"] is False
    assert ohne["parameter"]["negativ_prompt_karte"] == " ", "die Bestellung bleibt"


def test_ohne_bestellten_regler_ist_die_ankunft_nicht_bestimmt(tmp_path, pil):
    _dateien(tmp_path)
    ergebnis = render.rendere(_auftrag_fuer(tmp_path, "z-image-turbo"),
                              _lader=_lader(NimmtAlles()))
    assert ergebnis["parameter"]["fuehrung_regler_angekommen"] is None


def _eintrag_mit_wert(monkeypatch, wert):
    alt = backbone.BACKBONES[QWEN_EDIT]
    monkeypatch.setitem(backbone.BACKBONES, QWEN_EDIT,
                        dataclasses.replace(alt, fuehrung_regler_wert=wert))


def test_der_wert_des_registers_kommt_an_nicht_die_vorgabe_der_pipeline(
        tmp_path, pil, monkeypatch):
    """Die Attrappe hat 4.0 als Vorgabe — ein Wert, der NICHT 4.0 ist, zeigt, dass
    übergeben und nicht bloss vorgegeben wurde (Durchsicht: Scheinprüfung)."""
    _eintrag_mit_wert(monkeypatch, 6.5)
    _dateien(tmp_path)
    pipeline = QwenEditPlus()
    render.rendere(_auftrag_fuer(tmp_path, QWEN_EDIT), _lader=_lader(pipeline))
    [kw] = pipeline.aufrufe
    assert kw["true_cfg_scale"] == 6.5


@pytest.mark.parametrize("wert, wirksam", [(1.0, False), (1.0001, True)])
def test_an_der_schwelle_urteilt_negativ_wirksam_wie_die_pipeline(monkeypatch, wert,
                                                                   wirksam):
    """Die Pipeline führt erst bei ``true_cfg_scale > 1`` — genau 1.0 führt nicht."""
    _eintrag_mit_wert(monkeypatch, wert)
    assert render.negativ_wirksam(QWEN_EDIT)["wirksam"] is wirksam
