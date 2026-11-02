"""A0093 (d) · «flux-krea» wird schon beim Annehmen an der Brücke abgewiesen.

Owner-Entscheid 31.10.2026 «Immer vom Render»; KosmoOrbit sperrt seit A0061 jedes Bildwerkzeug ohne
belegten Start vom Beauty-Render, darunter ``flux-krea``. Bei uns hat ``flux-krea`` keinen
Registereintrag (FLUX-Ableger, unter Regel 1 ausgeschlossen, :data:`kosmo_szene.BACKBONE_VON_FREMD`).
Bis A0093 blieb eine solche Bestellung darum mit dem nicht endgültigen Mangel «keine Entsprechung»
liegen: :func:`kosmo_szene.widersprueche_beim_annehmen` lieferte ``[]``, die Brücke nahm den Auftrag
an, und erst der Abholer sagte ab. Jetzt endet sie sofort mit 400 und Satz — wie die übrigen
gesperrten Bildwerkzeuge (qwen, qwen-image-2.1, sdxl, flux2-klein) seit A0051b.

Gegen den Stand vor A0093 rot. Ohne GPU, ohne Blender, alles synthetisch (Regel 3).
"""
from __future__ import annotations

import pytest

from aiimaging import knotenweg, kosmo_szene

_SZENE = {"vis": {"backbone": "flux-krea"}, "geometry": {"path": "modell.glb", "format": "glb"}}


def test_flux_krea_steht_im_fremden_vertrag_aber_nicht_bei_uns():
    assert "flux-krea" in kosmo_szene.FREMDE_BACKBONES
    assert "flux-krea" not in kosmo_szene.BACKBONE_VON_FREMD


def test_flux_krea_wird_beim_annehmen_abgewiesen():
    saetze = kosmo_szene.widersprueche_beim_annehmen(_SZENE)
    assert saetze, "flux-krea beim Annehmen nicht abgewiesen"
    assert any("'flux-krea'" in s and "Regel 1" in s for s in saetze)
    assert any("Immer vom Render" in s or "vom Beauty-Render" in s for s in saetze)


def test_flux_krea_ist_im_lauf_ein_endgueltiger_mangel():
    gelesen = kosmo_szene.lies_szene(_SZENE, streng=False)
    assert any("'flux-krea'" in s for s in gelesen["maengel_endgueltig"])
    # Der bisherige Mangel bleibt stehen (test_kosmo_szene liest ihn).
    assert any("keine Entsprechung" in m for m in gelesen["maengel"])


def test_flux_krea_an_der_bruecke_400_ohne_auftragsordner(tmp_path):
    with pytest.raises(knotenweg.KnotenwegError) as fehler:
        knotenweg.lege_an(tmp_path, dict(_SZENE), b"glTF-bytes", "model.glb",
                          kennung="vis-1790000000-0a0093")
    assert fehler.value.code == 400
    assert "'flux-krea'" in str(fehler.value)
    assert not (tmp_path / "vis-1790000000-0a0093").exists()


@pytest.mark.parametrize("bb", ["qwen", "qwen-image-2.1", "sdxl", "flux2-klein", "flux-krea"])
def test_alle_gesperrten_bildwerkzeuge_beim_annehmen_abgewiesen(bb):
    """Die Liste von KosmoOrbit A0061 (``BILDWERKZEUG_BEAUTY_EINGANG``, Status «gesperrt»)."""
    szene = dict(_SZENE, vis={"backbone": bb})
    assert kosmo_szene.widersprueche_beim_annehmen(szene), bb


def test_vorgabe_und_unbekanntes_kuerzel_unveraendert():
    """Z-Image Turbo wird angenommen; ein Kürzel, das auch im fremden Vertrag nicht steht, bleibt
    beim bisherigen, nicht endgültigen Mangel (A0093 erfindet dort keine neue Regel)."""
    assert kosmo_szene.widersprueche_beim_annehmen(dict(_SZENE, vis={"backbone": "z-image-turbo"})) == []
    assert kosmo_szene.widersprueche_beim_annehmen(dict(_SZENE, vis={"backbone": "gibts-nicht"})) == []
