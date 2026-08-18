"""Der Phase-0-Befund, in Tests festgehalten: ein Feldname, zwei Up-Achsen.

Zwei Werkzeuge im Ökosystem schreiben beide ein Feld ``glb_path``, meinen damit aber
verschieden orientierte Geometrie:

  * KosmoDraw liefert das blosse ``"Z"``   — rohe IFC-Koordinaten
  * KosmoVis  liefert einen ganzen Satz     — ``"Y (glTF-2.0-Standard; …)"``

Blender importiert strikt Y-up. Eine Z-up-glb landet dort **liegend auf der Seite**, und
zwar ohne Fehlermeldung: Tiefenkarte, Kameraableitung und Geometrie-QA wären still
verdreht. Genau deshalb ist ``up_axis`` Pflichtfeld und kein Vorgabewert. Die Tests hier
bewachen diese Entscheidung.

Alle Tests laufen ohne Blender, ohne GPU und ohne Netz — ``contracts`` ist reine stdlib.
"""
from __future__ import annotations

import copy

import pytest

from aiimaging.contracts import (
    SCHEMA_ID,
    ContractError,
    needs_rotation,
    normalize_up_axis,
    validate_render_scene,
)

#: Wortlaut, wie ihn KosmoDraw schreibt (rohe IFC-Koordinaten, Z-up).
KOSMODRAW_UP = "Z"

#: Wortlaut, wie ihn KosmoVis schreibt — ein beschreibender Satz, kein Kürzel.
KOSMOVIS_UP = "Y (glTF-2.0-Standard; Blender-Import → Z-up/aufrecht)"


def szene(**geometrie) -> dict:
    """Minimale, gültige render-scene mit der übergebenen Geometrie — synthetisch (Regel 3)."""
    return {"geometry": dict(geometrie), "out_dir": "build/depth"}


# --------------------------------------------------------------------------------------
# normalize_up_axis — die beiden realen Schreibweisen
# --------------------------------------------------------------------------------------

def test_kosmodraw_kuerzel_wird_zu_z():
    """Bewacht den Phase-0-Befund: KosmoDraws blosses ``"Z"`` bleibt Z."""
    assert normalize_up_axis(KOSMODRAW_UP) == "Z"


def test_kosmovis_beschreibender_satz_wird_zu_y():
    """Bewacht den Phase-0-Befund: KosmoVis' ganzer Satz wird auf ``"Y"`` verkürzt."""
    assert normalize_up_axis(KOSMOVIS_UP) == "Y"


@pytest.mark.parametrize("eingabe, erwartet", [
    ("z", "Z"),
    ("y", "Y"),
    ("  Z  ", "Z"),
    ("Z-up (rohe IFC-Koordinaten)", "Z"),
    ("Y-up", "Y"),
])
def test_schreibweisen_werden_toleriert(eingabe, erwartet):
    """Toleranz bei Gross-/Kleinschreibung und Beiwerk — die Erzeuger formulieren frei."""
    assert normalize_up_axis(eingabe) == erwartet


def test_fehlende_up_achse_wird_abgelehnt():
    """Kein Default bei ``None``: ein geratener Wert wäre eine stille Verdrehung."""
    with pytest.raises(ContractError, match="up_axis"):
        normalize_up_axis(None)


@pytest.mark.parametrize("leer", ["", "   ", "\n\t"])
def test_leere_up_achse_wird_abgelehnt(leer):
    """Eine leere Angabe ist keine Angabe — sie wird abgelehnt statt als Y gedeutet."""
    with pytest.raises(ContractError):
        normalize_up_axis(leer)


@pytest.mark.parametrize("unklar", ["X", "up", "42", "unbekannt", "-Z"])
def test_undeutbare_up_achse_wird_abgelehnt(unklar):
    """Was sich nicht als Y oder Z lesen lässt, wird laut abgelehnt statt geraten."""
    with pytest.raises(ContractError, match="nicht als Y oder Z deutbar"):
        normalize_up_axis(unklar)


# --------------------------------------------------------------------------------------
# needs_rotation — die Antwort, an der die Bildkette hängt
# --------------------------------------------------------------------------------------

def test_rotation_noetig_bei_kosmodraw():
    """Z-up muss vor dem Blender-Import gedreht werden, sonst liegt der Bau auf der Seite."""
    assert needs_rotation(KOSMODRAW_UP) is True


def test_keine_rotation_bei_kosmovis():
    """Bereits glTF-konformes Y-up darf NICHT gedreht werden — sonst kippt es andersherum."""
    assert needs_rotation(KOSMOVIS_UP) is False


def test_rotationsfrage_ohne_up_achse_ist_ein_fehler():
    """``needs_rotation`` antwortet nie mit ``False`` ins Blaue — ohne Angabe wirft es."""
    with pytest.raises(ContractError):
        needs_rotation(None)


# --------------------------------------------------------------------------------------
# validate_render_scene — genau eine Geometriequelle, Pflichtfelder, keine Mutation
# --------------------------------------------------------------------------------------

def test_szene_muss_ein_objekt_sein():
    """Eine render-scene ist ein Objekt; alles andere wird als Vertragsbruch gemeldet."""
    with pytest.raises(ContractError, match="Objekt"):
        validate_render_scene(["kein", "objekt"])


def test_fehlende_geometrie_wird_abgelehnt():
    """Ohne ``geometry`` gibt es nichts zu rendern — Pflichtfeld, kein Default."""
    with pytest.raises(ContractError, match="geometry"):
        validate_render_scene({"out_dir": "build/depth"})


def test_geometrie_ohne_quelle_wird_abgelehnt():
    """Weder ``ifc_path`` noch ``glb_path``: unbrauchbar, also laut abgelehnt."""
    with pytest.raises(ContractError, match="ifc_path oder glb_path"):
        validate_render_scene(szene())


def test_beide_quellen_zugleich_werden_abgelehnt():
    """``ifc_path`` UND ``glb_path`` ist mehrdeutig — es bliebe offen, welche Geometrie gilt."""
    with pytest.raises(ContractError, match="mehrdeutig"):
        validate_render_scene(szene(ifc_path="build/testbau.ifc",
                                    glb_path="build/testbau.glb",
                                    up_axis=KOSMODRAW_UP))


def test_fehlendes_ausgabeverzeichnis_wird_abgelehnt():
    """``out_dir`` ist Pflicht: ohne Ziel schreibt die Tiefenkarte irgendwohin oder nirgends."""
    with pytest.raises(ContractError, match="out_dir"):
        validate_render_scene({"geometry": {"ifc_path": "build/testbau.ifc"}})


def test_glb_von_kosmodraw_wird_zur_drehung_markiert():
    """Der Befund im Vollzug: KosmoDraws Z-up-glb wird als drehbedürftig durchgereicht."""
    out = validate_render_scene(szene(glb_path="build/testbau.glb", up_axis=KOSMODRAW_UP))
    assert out["geometry"]["up_axis"] == "Z"
    assert out["geometry"]["needs_rotation"] is True
    assert out["schema"] == SCHEMA_ID


def test_glb_von_kosmovis_bleibt_ungedreht():
    """Gegenprobe: KosmoVis' Y-up-glb wird nicht gedreht, obwohl das Feld gleich heisst."""
    out = validate_render_scene(szene(glb_path="build/testbau.glb", up_axis=KOSMOVIS_UP))
    assert out["geometry"]["up_axis"] == "Y"
    assert out["geometry"]["needs_rotation"] is False


def test_glb_ohne_up_achse_wird_abgelehnt():
    """Kern des Befunds: glb ohne ``up_axis`` ist nicht verwertbar, ein Default wäre Raten."""
    with pytest.raises(ContractError, match="up_axis"):
        validate_render_scene(szene(glb_path="build/testbau.glb"))


@pytest.mark.parametrize("kaputt", ["", "   ", "X"])
def test_glb_mit_unbrauchbarer_up_achse_wird_abgelehnt(kaputt):
    """Leer oder undeutbar zählt wie fehlend — die Ablehnung ist die einzige sichere Antwort."""
    with pytest.raises(ContractError):
        validate_render_scene(szene(glb_path="build/testbau.glb", up_axis=kaputt))


def test_eigener_ifc_pfad_setzt_y_up():
    """Regel 4, eigener Pfad: Der Kern erzeugt glTF-konformes Y-up, also steht ``"Y"`` fest."""
    out = validate_render_scene(szene(ifc_path="build/testbau.ifc"))
    assert out["geometry"]["up_axis"] == "Y"
    assert out["geometry"]["needs_rotation"] is False


def test_eigener_ifc_pfad_braucht_keine_up_angabe():
    """Beim eigenen IFC-Pfad ist ``up_axis`` kein Pflichtfeld — die Orientierung ist bekannt."""
    validate_render_scene(szene(ifc_path="build/testbau.ifc"))  # wirft nicht


def test_eingabe_wird_nicht_mutiert():
    """Die Prüfung liefert eine Kopie: Wer eine Szene weiterreicht, bekommt sie unverändert zurück."""
    eingang = szene(glb_path="build/testbau.glb", up_axis=KOSMODRAW_UP)
    vorher = copy.deepcopy(eingang)

    out = validate_render_scene(eingang)

    assert eingang == vorher, "validate_render_scene hat die Eingabe verändert"
    assert "needs_rotation" not in eingang["geometry"]
    assert "schema" not in eingang

    out["geometry"]["glb_path"] = "verändert.glb"       # Kopie ist wirklich tief
    assert eingang["geometry"]["glb_path"] == "build/testbau.glb"


# ── Regressionen aus Sitzung 03 ────────────────────────────────────────────────
# Drei Befunde aus dem Testschreiben, hier festgenagelt, damit sie nicht wiederkehren.

def test_pfadobjekt_als_geometrie_ist_kein_typfehler(tmp_path):
    """Ein `Path` als ifc_path ist beim programmatischen Bauen naheliegend.

    Vorher lief die Tiefkopie ueber `json.dumps` und warf darauf einen TypeError — ein
    Fehler, der nichts mit dem Vertrag zu tun hat und den Aufrufer in die Irre fuehrt.
    """
    from pathlib import Path as P
    szene = {"geometry": {"ifc_path": P("bau.ifc")}, "out_dir": str(tmp_path)}

    geprueft = validate_render_scene(szene)

    assert geprueft["geometry"]["ifc_path"] == "bau.ifc"
    assert isinstance(geprueft["geometry"]["ifc_path"], str)


def test_widersprechende_up_achse_am_ifc_pfad_wird_gemeldet(tmp_path):
    """Beim eigenen IFC-Pfad erzeugt der Runner Y-up. Ein mitgegebenes "Z" ist ein Irrtum
    des Aufrufers und wird laut gemeldet, statt stillschweigend ueberschrieben zu werden —
    genau die Linie, deretwegen dieses Modul existiert."""
    szene = {"geometry": {"ifc_path": "bau.ifc", "up_axis": "Z"}, "out_dir": str(tmp_path)}

    with pytest.raises(ContractError, match="widerspricht"):
        validate_render_scene(szene)


def test_uebereinstimmende_up_achse_am_ifc_pfad_ist_zulaessig(tmp_path):
    """Gegenprobe: ein mitgegebenes "Y" widerspricht nicht und darf durchgehen."""
    szene = {"geometry": {"ifc_path": "bau.ifc", "up_axis": "Y"}, "out_dir": str(tmp_path)}

    assert validate_render_scene(szene)["geometry"]["up_axis"] == "Y"


def test_fehlendes_out_dir_wird_vor_der_up_achse_gemeldet():
    """Fehlen mehrere Pflichtfelder, soll der Aufrufer nicht erst den einen Fehler sehen
    und nach dessen Behebung den naechsten."""
    szene = {"geometry": {"glb_path": "bau.glb"}}          # weder out_dir noch up_axis

    with pytest.raises(ContractError, match="out_dir"):
        validate_render_scene(szene)
