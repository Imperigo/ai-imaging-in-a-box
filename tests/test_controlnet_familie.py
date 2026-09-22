"""Welche ControlNet-Klasse der Ladeweg fuer welchen Eintrag anfordert — 22.09.2026.

BEFUND (`auf-20260922-138`, HomeStation): `render._lade_mit_controlnet` nahm fuer JEDEN
Registereintrag mit getrenntem Tiefen-ControlNet die Z-Image-Klassen. `qwen-image-2512`
waere damit mit dem Bauplan einer fremden Familie geladen worden.

Geprueft wird hier die WIRKUNG, nicht der Quelltext: Ein untergeschobenes `diffusers`
(per `sys.modules`) schreibt mit, welche Klasse angefordert wird. Ohne GPU und ohne
installierte Bibliothek — und darum pruefen diese Tests NICHT, ob die Qwen-Klassennamen
in der echten Bibliothek stimmen. Das ist am Geraet unbestaetigt.
"""

from __future__ import annotations

import sys
import types
from dataclasses import replace

import pytest

from aiimaging import render
from aiimaging.backbone import BACKBONES


class _Halt(Exception):
    """Bricht den Produktweg nach dem Laden ab — weiter reicht die Attrappe nicht."""


def _attrappe(monkeypatch, *, halt_nach_pipeline=False, ohne=()):
    """Ein `diffusers`, das mitschreibt, welche Klasse wie angefordert wird."""
    protokoll: list[tuple[str, str]] = []
    modul = types.ModuleType("diffusers")

    def _klasse(name):
        class _K:
            @classmethod
            def from_single_file(cls, *a, **k):
                protokoll.append((name, "from_single_file"))
                return cls()

            @classmethod
            def from_pretrained(cls, *a, **k):
                protokoll.append((name, "from_pretrained"))
                if halt_nach_pipeline:
                    raise _Halt(name)
                return cls()
        _K.__name__ = name
        return _K

    def __getattr__(name):
        if name.startswith("__") or name in ohne:
            raise AttributeError(name)
        return _klasse(name)

    modul.__getattr__ = __getattr__
    monkeypatch.setitem(sys.modules, "diffusers", modul)
    return protokoll


def _mit_gewichten(tmp_path, eintrag):
    """Ein ControlNet-Ordner mit (leerer) Einzeldatei neben der Modellwurzel."""
    (tmp_path / "cn").mkdir()
    (tmp_path / "cn" / "gewichte.safetensors").write_bytes(b"")
    return replace(eintrag, controlnet_ordner="cn")


_TORCH = types.SimpleNamespace(bfloat16="bf16")


def test_z_image_bekommt_weiter_die_z_image_klassen(tmp_path, monkeypatch):
    protokoll = _attrappe(monkeypatch)
    e = _mit_gewichten(tmp_path, BACKBONES["z-image-turbo"])
    _, weg = render._lade_mit_controlnet(e, tmp_path / "basis", _TORCH)
    assert protokoll == [("ZImageControlNetModel", "from_single_file"),
                         ("ZImageControlNetPipeline", "from_pretrained")]
    assert weg.startswith("ZImageControlNetPipeline")


def test_qwen_image_2512_bekommt_nicht_die_z_image_klassen(tmp_path, monkeypatch):
    """Der Kern des Befunds: eine andere Familie, also eine andere Klasse."""
    protokoll = _attrappe(monkeypatch)
    e = _mit_gewichten(tmp_path, BACKBONES["qwen-image-2512"])
    _, weg = render._lade_mit_controlnet(e, tmp_path / "basis", _TORCH)
    angefordert = [name for name, _ in protokoll]
    assert not any(name.startswith("ZImage") for name in angefordert), angefordert
    # Welcher Name es ist, legt die Tabelle fest — am Geraet unbestaetigt.
    assert angefordert == ["QwenImageControlNetModel", "QwenImageControlNetPipeline"]
    assert weg.startswith("QwenImageControlNetPipeline")


def test_unbekannte_familie_wird_mit_begruendung_abgewiesen(tmp_path, monkeypatch):
    protokoll = _attrappe(monkeypatch)
    e = _mit_gewichten(tmp_path, BACKBONES["z-image-turbo"])
    for familie in ("gibt-es-nicht", None):
        with pytest.raises(render.RenderError) as fehler:
            render._lade_mit_controlnet(replace(e, controlnet_familie=familie),
                                        tmp_path / "basis", _TORCH)
        text = str(fehler.value)
        assert "keine Pipeline-Klasse bekannt" in text
        assert "anderen Familie" in text          # der Grund, nicht nur der Umstand
    assert protokoll == [], "bei unbekannter Familie darf KEINE Klasse angefordert werden"


def test_fehlende_klasse_in_diffusers_wird_abgewiesen(tmp_path, monkeypatch):
    """Kennt die installierte Fassung die Klasse nicht, kommt ein Satz statt eines Absturzes."""
    protokoll = _attrappe(monkeypatch, ohne=("QwenImageControlNetPipeline",))
    e = _mit_gewichten(tmp_path, BACKBONES["qwen-image-2512"])
    with pytest.raises(render.RenderError) as fehler:
        render._lade_mit_controlnet(e, tmp_path / "basis", _TORCH)
    assert "QwenImageControlNetPipeline" in str(fehler.value)
    assert protokoll == []


def test_produktweg_ueber_lade_modell_waehlt_die_familie(tmp_path, monkeypatch):
    """Nicht nur der direkte Aufrufer: `lade_modell` — der Weg des Produkts — kommt an."""
    protokoll = _attrappe(monkeypatch, halt_nach_pipeline=True)
    monkeypatch.setitem(sys.modules, "torch", _TORCH)
    wurzel = tmp_path / "basis"
    for teil in ("transformer", "vae", "text_encoder", "tokenizer"):
        (wurzel / teil).mkdir(parents=True)
    (wurzel / "model_index.json").write_text("{}")
    e = _mit_gewichten(tmp_path, BACKBONES["qwen-image-2512"])
    monkeypatch.setitem(BACKBONES, "qwen-image-2512", e)
    with pytest.raises(_Halt) as halt:
        render.lade_modell("qwen-image-2512", modell_wurzel=wurzel)
    assert str(halt.value) == "QwenImageControlNetPipeline"
    assert ("ZImageControlNetPipeline", "from_pretrained") not in protokoll


def test_jeder_zugelassene_controlnet_eintrag_hat_eine_bekannte_familie():
    """Ein zugelassener Eintrag mit getrenntem ControlNet, dessen Familie fehlt, waere
    auf dem Produktweg nicht ladbar — und das fiele erst am Geraet auf."""
    from aiimaging.backbone import KOND_DEPTH_CONTROLNET, pruefe_lizenz
    for name, e in BACKBONES.items():
        if (e.konditionierung == KOND_DEPTH_CONTROLNET and e.controlnet_id
                and pruefe_lizenz(name)["zulaessig"]):
            assert e.controlnet_familie in render.CONTROLNET_KLASSEN, name


def test_der_unveraenderte_qwen_eintrag_bricht_am_fehlenden_ordner_ab(tmp_path, monkeypatch):
    """Die Zusage im Kommentar des Registers, bis zur Durchsicht vom 22.09.2026 ohne Wächter.

    Der Eintrag ``qwen-image-2512`` nennt ein ControlNet, aber keinen Ordner. Bis der
    Ordnername am Gerät gemessen ist, muss der Ladeweg genau dort abbrechen — mit einem
    Satz, und **bevor** diffusers auch nur eine Klasse abverlangt wird.
    """
    protokoll = _attrappe(monkeypatch)
    with pytest.raises(render.RenderError) as fehler:
        render._lade_mit_controlnet(BACKBONES["qwen-image-2512"], tmp_path / "basis", _TORCH)
    assert "keinen Ordner" in str(fehler.value)
    assert protokoll == [], "vor der Ordnerprüfung wurde schon eine Klasse geladen"


def test_die_familie_wird_vor_dem_ordner_geprueft(tmp_path, monkeypatch):
    """Die Reihenfolge, die der Kommentar zusagt: erst die Familie, dann der Ordner.

    Ohne Familie **und** ohne Ordner muss der Satz die Familie nennen. Sonst trägt jemand
    den Ordner nach und steht danach vor dem nächsten Hindernis, das man ihm hätte zuerst
    sagen können.
    """
    _attrappe(monkeypatch)
    ohne_beides = replace(BACKBONES["qwen-image-2512"], controlnet_familie=None,
                          controlnet_ordner=None)
    with pytest.raises(render.RenderError) as fehler:
        render._lade_mit_controlnet(ohne_beides, tmp_path / "basis", _TORCH)
    assert "keine Pipeline-Klasse bekannt" in str(fehler.value)
