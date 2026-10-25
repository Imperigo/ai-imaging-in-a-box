"""Ergebnis 368 (Heim-PC, 25.10.2026, Visbox 0.3.68) — vier Nachbesserungen am Weg «Bild aus Skizze».

(2) Alle Skizzenbilder kamen in 512 x 512: Die Mappe im Auftrag trug nur die Hochachse, die Vorgabe der
    Kette ist quadratisch, und die 1600 x 1000 grosse Unterlage wurde hineingestaucht — Striche und Haus
    lagen neben der Tiefe. Jetzt: lange Seite aus der Bestellung, Seitenverhältnis aus der Unterlage,
    Tiefe und Bild im selben Format (z-image-turbo als Startbild und Qwen gleich).
(3) Ein Lauf mit offener Lizenz (Qwen-Image 2.1, E153) trug ``engine_license_open``, aber der Satz
    «LIZENZ OFFEN …» fehlte in ``qa.verdict.hinweise``.
(4) Die Freigabe-Marke nannte Entscheid 146, ``visbox_voll`` 153 — jetzt beide 153.
(5) Eine Unterlage vom Heim-PC ging nur mit ``render.passes 'alle'`` (sonst kein Schönbild, 400) — jetzt
    ein anderes Bild derselben Kamera, sonst ein genauer Satz.

Regel 3: synthetisch, Attrappen wie ``test_skizze_fuehrt``.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from aiimaging import abholer, arbeitsgang, bildschreiben, kette, knotenweg, kosmo_szene
from aiimaging.kette import ART_MULTIPASS

from test_skizze_fuehrt import BLAU, ROT, _Modell, _einfarbig, _ergebnis, _rgba_png, _tabelle
from test_skizze_reist_mit import GRUNDBILD_AUFTRAG, KENNUNG, UEBER, _lege_an, glb  # noqa: F401
from test_voll_skizze_e153 import _Uhr, _lege
from test_mappenpaket import _mappe


# ------------------------------------------------------------------ (2) das Format

@pytest.mark.parametrize("b,h,lang,erwartet", [
    (1600, 1000, 1600, (1536, 960)),     # genau 1,6
    (1000, 1600, 1600, (960, 1536)),     # hochkant
    (1600, 900, 1600, (1536, 864)),       # 16:9 genau
    (4, 4, 512, (512, 512)),
    (1600, 1000, 512, (512, 320)),
])
def test_das_format_der_skizze(b, h, lang, erwartet):
    bb, hh = arbeitsgang.skizzen_format(b, h, lang)
    assert (bb, hh) == erwartet
    assert bb % 16 == 0 and hh % 16 == 0 and max(bb, hh) <= lang
    assert abs(bb / hh - b / h) / (b / h) <= arbeitsgang.SKIZZE_VERHAELTNIS_TOLERANZ


def test_ohne_masse_bleibt_alles():
    args = {"aufloesung": 512}
    assert arbeitsgang.format_der_skizze(args, None, None) == args
    assert arbeitsgang.format_der_skizze({"aufloesung": 1600, "hoehe": 1000}, 1600, 1000) == {
        "aufloesung": 1536, "hoehe": 960}


def _tabelle_mit_format(modell, gesehen: list):
    """Wie ``test_skizze_fuehrt._tabelle``, aber der Multipass schreibt die Tiefe im bestellten
    Format (verkleinert um 16, damit die Probe klein bleibt) und merkt sich die Parameter."""
    tabelle = _tabelle(modell)

    def multipass(*, knoten, eingaben, out_dir):
        b, h = int(knoten.params["aufloesung"]), int(knoten.params.get("hoehe") or
                                                    knoten.params["aufloesung"])
        gesehen.append((b, h))
        tiefe = bildschreiben.schreibe_graustufen_png(Path(out_dir) / "tiefe_norm.png",
                                                      [0.5] * ((b // 16) * (h // 16)),
                                                      b // 16, h // 16)
        return {"status": "ok", "depth_png": str(tiefe),
                "beauty_png": str(_einfarbig(Path(out_dir) / "beauty.png", b // 16, h // 16,
                                             (5, 5, 5)))}
    return {**tabelle, ART_MULTIPASS: multipass}


def _unterlage_1600(tmp_path) -> bytes:
    return _einfarbig(tmp_path / "bytes" / "u1600.png", 1600, 1000, BLAU).read_bytes()


def _skizze_1600(tmp_path) -> bytes:
    return _rgba_png(tmp_path / "bytes" / "s1600.png", 1600, 1000,
                     {(800, 500): (*ROT, 255)}).read_bytes()


def _rechne(tmp_path, glb, anlage, modell, gesehen, **mehr):  # noqa: F811
    zettel = _lege_an(tmp_path, glb, anlage, **mehr)
    if zettel["status"] != "queued":
        knotenweg.freigeben(tmp_path / "ablage", KENNUNG, zettel["approval_token"])
    ordner = tmp_path / "ablage" / KENNUNG
    antwort = abholer.hole_einen(
        ordner, verarbeite=abholer.verarbeiter(
            _skizzen_ausfuehrer=_tabelle_mit_format(modell, gesehen)),
        darf_rechnen=lambda: (True, "frei"))
    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort["grund"]
    return ordner, zettel


def test_unterlage_1600x1000_gibt_tiefe_und_bild_im_verhaeltnis_1_6(tmp_path, glb):  # noqa: F811
    """Der Befund aus 368: 512 x 512. Jetzt 1536 x 960 — Tiefe, Startbild und Ergebnis gleich."""
    modell, gesehen = _Modell(), []
    anlage = {"png": _skizze_1600(tmp_path), "unterlage": _unterlage_1600(tmp_path),
              "ueber": UEBER, "bemerkung": "ein Vordach"}
    _rechne(tmp_path, glb, anlage, modell, gesehen)
    (b, h), = gesehen
    assert (b, h) == (1536, 960) and b / h == pytest.approx(1.6)
    tb, th = bildschreiben.png_masse(modell.auftraege[-1]["depth_png"])
    assert tb / th == pytest.approx(1.6)
    # Das Startbild (Skizze auf Unterlage) hat dasselbe Seitenverhältnis — nichts wird gestaucht.
    sb, sh = bildschreiben.png_masse(modell.auftraege[-1]["beauty_png"])
    assert sb / sh == pytest.approx(1.6)


def test_die_aufloesung_der_bestellung_gilt(tmp_path):
    ordner = tmp_path / "auftrag"
    ordner.mkdir()
    assert knotenweg.aufloesung_der_bestellung(ordner) == {"aufloesung": 1600, "hoehe": 1000}
    (ordner / "render-scene.json").write_text(json.dumps({"render": {"resolution": [1200, 900]}}))
    assert knotenweg.aufloesung_der_bestellung(ordner) == {"aufloesung": 1200, "hoehe": 900}
    (ordner / "render-scene.json").write_text(json.dumps({"render": {"resolution": [99999, 1]}}))
    assert knotenweg.aufloesung_der_bestellung(ordner) == {"aufloesung": 1600, "hoehe": 1000}


def test_dasselbe_format_auf_qwen(tmp_path, glb):  # noqa: F811
    modell, gesehen = _Modell(), []
    from test_skizze_fuehrt import _szene
    anlage = {"png": _skizze_1600(tmp_path), "unterlage": _unterlage_1600(tmp_path),
              "ueber": UEBER, "bemerkung": "ein Vordach"}
    ordner, _ = _rechne(tmp_path, glb, anlage, modell, gesehen,
                        szene=_szene(name="ipad/skizze-20261025-122953-50b5.png",
                                     backbone="qwen-image-2.1"))
    assert gesehen == [(1536, 960)]
    # (3) DER LIZENZSATZ in den Hinweisen, die Marke am Ergebnis.
    ergebnis = _ergebnis(ordner)
    assert ergebnis["engine_license_open"] is True
    assert any(h.startswith("LIZENZ OFFEN") for h in ergebnis["qa"]["verdict"]["hinweise"]), \
        ergebnis["qa"]["verdict"]["hinweise"]


# ------------------------------------------------------------------ (4) ein Entscheid

def test_die_freigabe_einer_skizze_mit_qwen_nennt_153(tmp_path):
    uhr, mappe = _Uhr(), _mappe(tmp_path, "Hof")
    z = _lege(tmp_path / "ablage", uhr, mappe, backbone="qwen-image-2.1")
    assert z[knotenweg.FELD_FREIGABE]["durch"] == knotenweg.FREIGABE_DURCH_VOLL_SKIZZE
    assert "153" in z[knotenweg.FELD_FREIGABE]["durch"] and "146" not in z[knotenweg.FELD_FREIGABE]["durch"]
    assert z[knotenweg.FELD_VOLL]["entscheid"] == "153"
    # Jeder andere Lauf ohne Klick nennt weiter 146.
    anders = _lege(tmp_path / "ablage", uhr, mappe, n=1, skizze=False, backbone="z-image-turbo")
    assert anders[knotenweg.FELD_FREIGABE]["durch"] == knotenweg.FREIGABE_DURCH_VOLL
    # Der Abholer zählt beide als Lauf ohne Klick.
    assert knotenweg.voll_stand(tmp_path / "ablage", _uhr=uhr)["laeufe"] == 2


# ------------------------------------------------------------------ (5) Unterlage ohne Schönbild

def _grundbild(tmp_path, dateien: dict, images=None) -> Path:
    grund = tmp_path / "ablage" / GRUNDBILD_AUFTRAG
    grund.mkdir(parents=True)
    (grund / "job.json").write_text("{}", encoding="utf-8")
    for name, daten in dateien.items():
        (grund / name).write_bytes(daten)
    if images is not None:
        (grund / "render-result.json").write_text(json.dumps({"images": images}), encoding="utf-8")
    return grund


def test_ohne_schoenbild_nimmt_der_heim_pc_ein_bild_derselben_kamera(tmp_path, glb):  # noqa: F811
    blau = _einfarbig(tmp_path / "bytes" / "b.png", 4, 4, BLAU).read_bytes()
    _grundbild(tmp_path, {"sSW__tiefe.png": b"\x89PNG-tiefe", "sSW__vorschau.png": blau})
    zettel = _lege_an(tmp_path, glb, {"png": _rgba_png(tmp_path / "bytes" / "s.png", 4, 4, {}).read_bytes(),
                                      "unterlage": None, "ueber": UEBER, "bemerkung": "ein Vordach"})
    mit = zettel["skizze_mitgereist"]
    assert mit["unterlage_von"] == "heim-pc" and mit["unterlage_ersatz"] == "sSW__vorschau.png"


def test_ohne_schoenbild_auch_das_bild_aus_dem_ergebnis(tmp_path, glb):  # noqa: F811
    blau = _einfarbig(tmp_path / "bytes" / "b.png", 4, 4, BLAU).read_bytes()
    _grundbild(tmp_path, {"bild-sSW.png": blau}, images=["bild-sSW.png"])
    zettel = _lege_an(tmp_path, glb, {"png": _rgba_png(tmp_path / "bytes" / "s.png", 4, 4, {}).read_bytes(),
                                      "unterlage": None, "ueber": UEBER, "bemerkung": "ein Vordach"})
    assert zettel["skizze_mitgereist"]["unterlage_ersatz"] == "bild-sSW.png"


def test_kein_bild_der_kamera_sagt_genau_was_fehlt(tmp_path, glb):  # noqa: F811
    _grundbild(tmp_path, {"sSE__schoenbild.png": b"x", "sSW__tiefe.png": b"x"})
    with pytest.raises(knotenweg.KnotenwegError) as fehler:
        _lege_an(tmp_path, glb, {"png": _rgba_png(tmp_path / "bytes" / "s.png", 4, 4, {}).read_bytes(),
                                 "unterlage": None, "ueber": UEBER, "bemerkung": "ein Vordach"})
    satz = str(fehler.value)
    assert "Der Auftrag liegt auf dem Heim-PC" in satz and "'sSW__schoenbild.png' fehlt" in satz
    assert "sSE__schoenbild.png" in satz and str(tmp_path) not in satz
    assert not (tmp_path / "ablage" / KENNUNG).exists()


def test_die_lizenzsaetze_stehen_auch_im_vertrag():
    assert kosmo_szene.LIZENZ_SATZ_ANFAENGE == ("LIZENZ OFFEN", "NUR FORSCHUNG")
    assert kette.HINWEIS_SKIZZE_EIGENER_START.startswith(kosmo_szene.SKIZZE_EIGENER_START_ANFANG)
