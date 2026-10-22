"""Materialien je Bauteil-Art — Heim-PC-Teil der Knoten «Material» und der Materialwahl (H3).

**Anlass:** Entscheide 107, 111 und 113 (20.10.2026, Blätter 31–33 der Entwurfsfläche). Der
Render-Knoten bestellt ``render.materialien {fassade?, dach?, fenster?, boden?, uebrige?}`` —
je Art eine **MaterialWahl** ``{id, massstab_m?, drehungGrad?, relief?, toenung?}``. Die
Texturen sind CC0 (ambientCG), liegen am Heim-PC und nie im Repo (Regel 1, Präzisierung
Texturen und Himmelsbilder; Regel 3).

Was hier steht — alles ohne Blender prüfbar (Regel 2, Regel 4):

* :data:`BIBLIOTHEK` — die elf Materialien mit Asset der HomeStation (Herkunft), Bezeichnung
  und Satz für den Prompt (deutsch/englisch wie :mod:`aiimaging.prompts`), dazu
  Eigenschaften, die der Runner braucht (``fugen`` für die Holzlattung).
* :func:`texturen` — die Karten einer id am Rechner: ``$AIIMAGING_MATERIAL_ORDNER/<id>__*_<1K|2K>-JPG_<Karte>.jpg``.
  Der Asset-Name wird **nicht** erwartet, sondern gesucht — ein späterer Tausch des Assets
  braucht keine Codeänderung.
* :func:`art_von` — **welche Art ein Bauteil ist** (fassade, dach, fenster, boden, uebrige
  oder gelaende), aus ``extras.kind`` der KosmoOrbit-glb, sonst aus dem Präfix unserer
  IFC-Knotennamen. Die Tabellen :data:`KIND_ZU_ART` und :data:`IFC_ZU_ART` sind die, die
  KosmoOrbits ``bauteil-arten.ts`` später abbildet. Der Runner fragt diese Funktion, statt
  eine eigene Liste zu führen. Seit N5 (22.10.2026) zuletzt aus einem Wort im Namen
  (:data:`NAME_ZU_ART`), und ein Bauteil ohne jede Angabe behält sein benanntes Material
  (:func:`art_und_herkunft`, :func:`ist_benanntes_material`).
"""
from __future__ import annotations

import os
import re
from pathlib import Path

__all__ = ["MATERIAL_ORDNER_ENV", "ARTEN", "ART_GELAENDE", "ART_UEBRIGE", "BIBLIOTHEK",
           "ID_MUSTER", "FARB_MUSTER", "KARTEN", "KARTEN_PFLICHT", "HERKUNFT",
           "KIND_ZU_ART", "IFC_ZU_ART", "art_von", "art_und_herkunft", "NAME_ZU_ART",
           "ist_benanntes_material", "groesse_fuer", "material_ordner",
           "texturen", "prompt_satz", "VORGABE_MASSSTAB_M", "VORGABE_DREHUNG_GRAD",
           "VORGABE_RELIEF"]

#: Die Umgebungsvariable mit dem Ordner der Texturen — der Wert steht nur am Heim-PC.
MATERIAL_ORDNER_ENV = "AIIMAGING_MATERIAL_ORDNER"

#: Die fünf Arten der Materialwahl — wörtlich die Schlüssel des Vertrags.
ARTEN = ("fassade", "dach", "fenster", "boden", "uebrige")
ART_UEBRIGE = "uebrige"
#: Gelände bekommt nie ein gewähltes Material — es ist Grundlage, kein Entwurf.
ART_GELAENDE = "gelaende"

ID_MUSTER = re.compile(r"^[a-z0-9-]{1,48}$")
FARB_MUSTER = re.compile(r"^#[0-9a-fA-F]{6}$")

#: Die Vorgaben des Heim-PC, wenn ein Feld fehlt (der Vertrag hat keine).
VORGABE_MASSSTAB_M = 1.0
VORGABE_DREHUNG_GRAD = 0.0
VORGABE_RELIEF = 0.6

#: Die Karten eines ambientCG-Assets. Pflicht sind Farbe, Rauheit und Höhe (für das Relief);
#: ``NormalGL`` liegt dabei, wird aber nicht gebraucht (Bump aus der Höhe, weil die
#: Box-Projektion keine Tangenten hat), ``AmbientOcclusion`` fehlt bei vier Assets.
KARTEN = ("Color", "Roughness", "NormalGL", "Displacement", "AmbientOcclusion")
KARTEN_PFLICHT = ("Color", "Roughness", "Displacement")

HERKUNFT = {"quelle": "ambientCG", "lizenz": "CC0-1.0", "adresse": "https://ambientcg.com",
            "vermerk": "nicht ausgeliefert, am Heim-PC abgelegt, unverändert"}

#: Die elf Materialien (Tabelle der HomeStation, 20.10.2026).
#:
#: ``asset`` ist das, was die HomeStation abgelegt hat — Herkunft, nicht Suchschlüssel
#: (gesucht wird über das Muster, siehe :func:`texturen`). ``prompt_en`` ist der Stoff, ohne
#: Bauteilwort; die Art kommt in :func:`prompt_satz` dazu. ``fugen`` (nur die Holzlattung):
#: Das Asset Planks021 ist eine geschlossene Bretterschalung — der Runner schneidet Fugen
#: hinein, Lattenbreite und Fuge in Metern, die Fuge dunkel und im Relief vertieft.
BIBLIOTHEK = {
    "sichtbeton-sandgestrahlt": {
        "label": "Sichtbeton, sandgestrahlt", "asset": "Concrete037",
        "prompt_de": "sandgestrahlter Sichtbeton", "prompt_en": "sandblasted exposed concrete"},
    "sichtbeton-schalungsglatt": {
        "label": "Sichtbeton, schalungsglatt", "asset": "Concrete002",
        "prompt_de": "schalungsglatter Sichtbeton",
        "prompt_en": "smooth fair-faced concrete"},
    "fichte": {
        "label": "Fichte", "asset": "Wood096",
        "prompt_de": "Fichtenholz", "prompt_en": "spruce wood"},
    "backstein": {
        "label": "Backstein", "asset": "Bricks101",
        "prompt_de": "Backstein", "prompt_en": "red brick masonry"},
    "klinker": {
        "label": "Klinker", "asset": "Bricks054",
        "prompt_de": "Klinker", "prompt_en": "dark clinker brick"},
    "sandstein": {
        "label": "Sandstein", "asset": "Rock004",
        "prompt_de": "Sandstein", "prompt_en": "sandstone"},
    "stampflehm": {
        "label": "Stampflehm", "asset": "Ground104",
        "prompt_de": "Stampflehm", "prompt_en": "rammed earth"},
    "verputz-weiss-glatt": {
        "label": "Verputz weiss, glatt", "asset": "Plaster002",
        "prompt_de": "weisser Glattputz", "prompt_en": "smooth white render"},
    "verputz-weiss-rau": {
        "label": "Verputz weiss, rau", "asset": "Plaster003",
        "prompt_de": "weisser Rauputz", "prompt_en": "rough white render"},
    "holzlattung-fichte": {
        "label": "Holzlattung Fichte", "asset": "Planks021",
        "prompt_de": "Holzlattung aus Fichte", "prompt_en": "spruce timber battens",
        "fugen": {"latte_m": 0.05, "fuge_m": 0.02, "dunkel": 0.25}},
    "dreischichtplatte": {
        "label": "Dreischichtplatte", "asset": "Wood090A",
        "prompt_de": "Dreischichtplatte", "prompt_en": "three-layer timber panels"},
}

#: Die Art als Wort für den Prompt — ohne Bauteilwörter (``prompts.BAUTEILWOERTER``): Der
#: Satz wird nach dem Bauteilwächter angefügt und soll kein Bauteil bestellen.
ART_IM_SATZ = {"fassade": "exterior surfaces", "dach": "upper surfaces",
               "fenster": "frames", "boden": "ground surfaces", "uebrige": "other surfaces"}

#: ``extras.kind`` der KosmoOrbit-glb (``gltf.ts``) → Art. ``None``: unbestimmt, weiter mit
#: dem Namen. Türen gehören zu «uebrige» (Entscheid 113).
KIND_ZU_ART = {
    "wall": "fassade",
    "roof": "dach",
    "dachfenster": "fenster",
    "opening": "fenster",          # openingType 'tuer' → uebrige, siehe art_von
    "slab": "boden",               # PredefinedType ROOF → dach, siehe art_von
    "ramp": "boden",
    "terrain": ART_GELAENDE,
    "gelaendeflaeche": ART_GELAENDE,
    "stair": "uebrige", "column": "uebrige", "beam": "uebrige", "gelaender": "uebrige",
    "furniture": "uebrige", "lift": "uebrige", "zonentuer": "uebrige",
    "leuchte": "uebrige", "assembly": "uebrige",
    "freemesh": None,
}

#: Präfix unserer IFC-Knotennamen (``IfcWall_<Name>_<GUID>``) → Art.
IFC_ZU_ART = {
    "IfcWall": "fassade", "IfcWallStandardCase": "fassade", "IfcCurtainWall": "fassade",
    "IfcPlate": "fassade",
    "IfcRoof": "dach",
    "IfcSlab": "boden",            # PredefinedType ROOF → dach
    "IfcWindow": "fenster",
    "IfcDoor": "uebrige",
    "IfcCovering": "uebrige",      # PredefinedType ROOFING → dach
    "IfcStair": "uebrige", "IfcStairFlight": "uebrige", "IfcRamp": "boden",
    "IfcRampFlight": "boden", "IfcRailing": "uebrige", "IfcColumn": "uebrige",
    "IfcBeam": "uebrige", "IfcMember": "uebrige", "IfcFooting": "uebrige",
    "IfcFurnishingElement": "uebrige", "IfcBuildingElementProxy": "uebrige",
    "IfcSite": ART_GELAENDE, "IfcGeographicElement": ART_GELAENDE,
}

_IFC_PRAEFIX = re.compile(r"^(Ifc[A-Z][A-Za-z0-9]*)_")
#: Vordefinierte Typen, die ein Bauteil zum Dach machen bzw. zum Boden lassen.
DACH_TYPEN = ("ROOF", "ROOFING")


#: N5 (Mac-Demolauf 22.10.2026): Wörter im NAMEN eines Objekts (oder eines Elternteils), das
#: weder ``extras.kind`` noch ein ``Ifc*``-Präfix trägt — eine glb aus einem anderen Programm.
#: Bis dahin war ein solches Objekt immer «uebrige». In dieser Reihenfolge geprüft, als Teil
#: eines Worts (deutsche Zusammensetzungen: «Aussenwand», «Satteldach»). Bewusst NICHT aus dem
#: Materialnamen: ein Objekt «Haus» mit den Materialien Beton und Glas ist kein Fenster.
#: Nicht in der Liste (Absicht): Terrasse, Baum, Möbel — sie behalten ihr Material.
NAME_ZU_ART = (
    ("fenster", ("fenster", "window", "verglasung", "glazing")),
    ("dach", ("dach", "roof")),
    ("fassade", ("fassade", "facade", "wand", "wall")),
    ("boden", ("bodenplatte", "geschossdecke", "floor", "slab")),
)
#: Woher eine Art kommt — :func:`art_und_herkunft`.
HERKUNFT_GELAENDE = "gelaende"
HERKUNFT_KIND = "kind"
HERKUNFT_IFC = "ifc"
HERKUNFT_NAME = "name"
#: Keine Angabe in der Datei: «uebrige» — die Wahl für «uebrige» trifft dann nur Flächen ohne
#: benanntes Material (:func:`ist_benanntes_material`).
HERKUNFT_UNBESTIMMT = "unbestimmt"

#: Materialnamen, die nichts sagen — Vorgaben der Autorenprogramme und des glTF-Imports.
_NAMENLOS = re.compile(
    r"^(?:|material|mat|default\w*|standard\w*|lambert\d*|blinn\d*|phong\d*|none|"
    r"untitled|unnamed|ohne[ _-]?name|kein[ _-]?material|white|weiss|grey|gray|grau)"
    r"(?:[ ._#-]*\d+)?$", re.IGNORECASE)


def ist_benanntes_material(name) -> bool:
    """Trägt ein Material einen Namen, der etwas sagt («Beton», «Baum», «Terrasse_Holz»)?

    ``False`` für leere und Vorgabenamen («Material.001», «Default», «lambert1»). Der Name
    kommt aus der Datei; was er sagt, deutet hier niemand — er wird nur nicht überschrieben.
    """
    return not _NAMENLOS.match(str(name or "").strip())


def _art_aus_namen(namen) -> str | None:
    for art, woerter in NAME_ZU_ART:
        for n in namen:
            text = str(n or "").lower()
            if any(w in text for w in woerter):
                return art
    return None


def art_und_herkunft(name, *, kind=None, predefined=None, opening_type=None,
                     ist_gelaende: bool = False, namen=()) -> tuple[str, str]:
    """``(art, herkunft)`` — :func:`art_von`, dazu woher die Art kommt.

    ``namen`` sind weitere Objektnamen (Elternteile), für die Namensregel (:data:`NAME_ZU_ART`).
    ``herkunft`` ist :data:`HERKUNFT_UNBESTIMMT`, wenn die Datei nichts über das Bauteil sagt —
    dann behält es im Runner sein benanntes Material, auch wenn «uebrige» gewählt ist (N5).
    """
    if ist_gelaende:
        return ART_GELAENDE, HERKUNFT_GELAENDE
    vordef = str(predefined or "").upper()
    if isinstance(kind, str) and kind:
        art = KIND_ZU_ART.get(kind.lower())
        if art is not None:
            if kind.lower() == "slab" and vordef in DACH_TYPEN:
                return "dach", HERKUNFT_KIND
            if kind.lower() == "opening" and str(opening_type or "").lower() in ("tuer", "door"):
                return ART_UEBRIGE, HERKUNFT_KIND
            return art, HERKUNFT_KIND
    treffer = _IFC_PRAEFIX.match(str(name or ""))
    if treffer and treffer.group(1) in IFC_ZU_ART:
        klasse = treffer.group(1)
        if klasse in ("IfcSlab", "IfcCovering") and vordef in DACH_TYPEN:
            return "dach", HERKUNFT_IFC
        return IFC_ZU_ART[klasse], HERKUNFT_IFC
    if isinstance(kind, str) and kind:
        # Eine Art, die KosmoOrbit kennt, aber keiner Wahl zuordnet (`freemesh`): wie bisher
        # «uebrige» — sie kommt aus der Datei und ist nicht unbestimmt.
        return ART_UEBRIGE, HERKUNFT_KIND
    aus_namen = _art_aus_namen([name, *namen])
    if aus_namen is not None:
        return aus_namen, HERKUNFT_NAME
    return ART_UEBRIGE, HERKUNFT_UNBESTIMMT


def art_von(name, *, kind=None, predefined=None, opening_type=None,
            ist_gelaende: bool = False) -> str:
    """Die Art eines Bauteils — ``fassade``, ``dach``, ``fenster``, ``boden``, ``uebrige``
    oder ``gelaende``.

    Reihenfolge: **zuerst** ``ist_gelaende`` (die Geländeregel von :mod:`aiimaging.maske`,
    vom Aufrufer gefragt), dann ``kind`` (KosmoOrbit-glb, ``extras.kind``), dann das
    ``Ifc*``-Präfix des Namens (unsere IFC-Umwandlung), sonst ``uebrige``. ``predefined``
    (``PredefinedType``) macht eine Decke mit ``ROOF`` zum Dach; ``opening_type`` ``tuer``
    eine Öffnung zu «uebrige» (Entscheid 113).

    **Gelände zuerst (Befund B3 aus auf-20261020-292):** Bis dahin stand ``ist_gelaende``
    hinter dem Präfix. Die Geländeplatte heisst ``IfcSlab_Gelaende_…`` — das Präfix
    ``IfcSlab`` machte sie zu «boden», und sie bekam Stampflehm, während die Bauwerksmaske
    dieselbe Platte als Gelände führt. Zwei Stellen, zwei Urteile über dasselbe Objekt;
    jetzt entscheidet die eine Geländeregel, und Gelände ist **immer** ausgenommen.
    """
    return art_und_herkunft(name, kind=kind, predefined=predefined,
                            opening_type=opening_type, ist_gelaende=ist_gelaende)[0]


def groesse_fuer(guete) -> str:
    """``'1K'`` bei ``guete: 'vorschau'`` (Entscheid 104), sonst ``'2K'``."""
    return "1K" if guete == "vorschau" else "2K"


def material_ordner(umgebung=None) -> Path | None:
    wert = (umgebung if umgebung is not None else os.environ).get(MATERIAL_ORDNER_ENV)
    return Path(wert) if wert else None


def texturen(material_id: str, *, guete=None, ordner=None) -> dict:
    """Die Karten einer Bibliotheks-id am Rechner — ``{karten, groesse, asset, satz}``.

    ``karten`` ist ``{Color: Path, Roughness: Path, Displacement: Path, NormalGL?: Path,
    AmbientOcclusion?: Path}``; ``satz`` ist ``None`` oder sagt mit Namen, was fehlt (Entscheid
    113), ohne Pfad. Gesucht wird ``<id>__*_<Grösse>-JPG_<Karte>.jpg``; liegen zwei Assets für
    dieselbe id, gilt das erste nach Namen, und der Satz bleibt leer.
    """
    groesse = groesse_fuer(guete)
    wurzel = Path(ordner) if ordner is not None else material_ordner()
    antwort = {"karten": {}, "groesse": groesse, "asset": None, "satz": None}
    if wurzel is None:
        antwort["satz"] = (f"Textur '{material_id}' ({groesse}) fehlt am Rechner: Der Ordner "
                           f"der Texturen ist nicht eingestellt ({MATERIAL_ORDNER_ENV}).")
        return antwort
    assets = sorted({p.name.split("__", 1)[1].rsplit(f"_{groesse}-JPG_", 1)[0]
                     for p in wurzel.glob(f"{material_id}__*_{groesse}-JPG_*.jpg")})
    for asset in assets:
        karten = {}
        for karte in KARTEN:
            pfad = wurzel / f"{material_id}__{asset}_{groesse}-JPG_{karte}.jpg"
            if pfad.is_file():
                karten[karte] = pfad
        if all(k in karten for k in KARTEN_PFLICHT):
            antwort.update(karten=karten, asset=asset)
            return antwort
    fehlend = KARTEN_PFLICHT if not assets else [
        k for k in KARTEN_PFLICHT
        if not (wurzel / f"{material_id}__{assets[0]}_{groesse}-JPG_{k}.jpg").is_file()]
    antwort["satz"] = (f"Textur '{material_id}' ({groesse}, {', '.join(fehlend)}) fehlt am "
                       f"Rechner.")
    return antwort


def prompt_satz(art: str, material_id: str, prompt_en: str) -> tuple[str | None, bool]:
    """``(satz, schon_da)`` — «exterior surfaces of sandblasted exposed concrete», wenn der
    (übersetzte) Prompt den Stoff noch nicht nennt."""
    stoff = BIBLIOTHEK[material_id]["prompt_en"]
    if stoff.lower() in (prompt_en or "").lower():
        return None, True
    return f"{ART_IM_SATZ[art]} of {stoff}", False
