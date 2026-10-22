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
           "VORGABE_RELIEF", "FAMILIE", "STOFF_WUNSCH", "WORTE_FASSADE",
           "WORTE_NICHT_WAND", "stoff_wunsch"]

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
#: Öffnungen am NAMEN (Ergebnis auf-20261022-333): Ohne ``extras.kind`` fielen die 164
#: Öffnungen der KosmoDraw-glb («Oeffnung …») auf «uebrige» statt auf «fenster». Diese Wörter
#: machen ein Objekt zum Fenster — aber nicht, wenn der Name zugleich eine Tür nennt
#: (:data:`NAME_TUER`): Eine Türöffnung ist «uebrige» wie ``openingType: tuer`` (Entscheid 113),
#: und die Namensregel sagt dann gar nichts (das Objekt behält sein Material, N5).
NAME_OEFFNUNG = ("öffnung", "oeffnung", "opening")
NAME_TUER = ("tür", "tuer", "door")
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
            if (art == "fenster" and any(w in text for w in NAME_OEFFNUNG)
                    and not any(w in text for w in NAME_TUER)):
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


# ============================================================ der Stoffwunsch einer Variante
#
# **Anlass (Ergebnis auf-20261022-337, Befund 337):** Die Variante «Fassade aus Sichtbeton»
# kam in keinem Lauf — weder ohne Grundbild (txt2img) noch mit Bildeingang 0,65. Der Prompt
# begann mit «monolithic spruce timber battens building …»: Der Satz «Material vorne»
# (Entscheid 126) nimmt den Stoff der MATERIALWAHL (Fassade Holzlattung, aus der Grundlage
# mitbestellt), nicht den des Wunschs, und die Grundlage trug die Holztextur im Cycles-Bild.
# Die HomeStation: «Für eine Stoff-Variante muss sich die Materialwahl ändern, nicht nur der
# Prompt.» — :func:`stoff_wunsch` findet den Wunsch, ``kosmo_szene.material_der_variante``
# ersetzt damit die Wahl der Fassade.

#: Die Familie jedes Materials der Bibliothek — ein Wunsch derselben Familie ist erfüllt
#: («Holz» bei gewählter Holzlattung ersetzt nichts).
FAMILIE = {
    "sichtbeton-sandgestrahlt": "beton", "sichtbeton-schalungsglatt": "beton",
    "fichte": "holz", "holzlattung-fichte": "holz", "dreischichtplatte": "holz",
    "backstein": "backstein", "klinker": "backstein",
    "sandstein": "stein", "stampflehm": "lehm",
    "verputz-weiss-glatt": "putz", "verputz-weiss-rau": "putz",
}

#: Stoffwörter im (übersetzten) Prompt → ``(familie, id oder None, nur_mit_fassade)``.
#: Die Wörter sind die des Glossars (``sprache``, Abschnitt «Material und Oberfläche»), der
#: Bibliothek (``prompt_en``) und von ``kosmo_szene.STOFFE_IM_PROMPT``. ``id`` None: kein
#: Material der Bibliothek (Glas, Metall) — dann kann nur der Prompt folgen, nicht Blender.
#: ``nur_mit_fassade``: ein Wort, das ohne Fassadenwort daneben anderes meint («render» ist
#: auch «ein Rendering», «glass» meist die Fenster).
STOFF_WUNSCH = {
    "sandblasted exposed concrete": ("beton", "sichtbeton-sandgestrahlt", False),
    "smooth fair-faced concrete": ("beton", "sichtbeton-schalungsglatt", False),
    "board-formed concrete": ("beton", "sichtbeton-schalungsglatt", False),
    "fair-faced concrete": ("beton", "sichtbeton-schalungsglatt", False),
    "exposed concrete": ("beton", "sichtbeton-schalungsglatt", False),
    "concrete": ("beton", "sichtbeton-schalungsglatt", False),
    "exposed fair-faced brick": ("backstein", "backstein", False),
    "red brick masonry": ("backstein", "backstein", False),
    "dark clinker brick": ("backstein", "klinker", False),
    "facing brick": ("backstein", "klinker", False),
    "clinker brick": ("backstein", "klinker", False),
    "clinker": ("backstein", "klinker", False),
    "red brick": ("backstein", "backstein", False),
    "brick": ("backstein", "backstein", False),
    "masonry": ("backstein", "backstein", False),
    "natural stone": ("stein", "sandstein", False),
    "sandstone": ("stein", "sandstein", False),
    "stone": ("stein", "sandstein", False),
    "rammed earth": ("lehm", "stampflehm", False),
    "rough white render": ("putz", "verputz-weiss-rau", False),
    "smooth white render": ("putz", "verputz-weiss-glatt", False),
    "white plaster": ("putz", "verputz-weiss-glatt", False),
    "plaster": ("putz", "verputz-weiss-glatt", False),
    "render": ("putz", "verputz-weiss-glatt", True),
    "rendered": ("putz", "verputz-weiss-glatt", True),
    "three-layer timber panels": ("holz", "dreischichtplatte", False),
    "spruce timber battens": ("holz", "holzlattung-fichte", False),
    "timber battens": ("holz", "holzlattung-fichte", False),
    "timber cladding": ("holz", "holzlattung-fichte", False),
    "spruce wood": ("holz", "holzlattung-fichte", False),
    "timber": ("holz", "holzlattung-fichte", False),
    "wood": ("holz", "holzlattung-fichte", False),
    "wooden": ("holz", "holzlattung-fichte", False),
    "glass": ("glas", None, True),
    "glazed": ("glas", None, True),
    "glazing": ("glas", None, True),
    "sheet metal": ("metall", None, True),
    "metal": ("metall", None, True),
    "steel": ("metall", None, True),
    "aluminium": ("metall", None, True),
    "copper": ("metall", None, True),
    "zinc": ("metall", None, True),
}

#: Wörter, die die Fassade nennen — steht eines nah beim Stoff, ist er der Fassade gemeint.
WORTE_FASSADE = ("facade", "facades", "façade", "façades", "cladding", "wall", "walls",
                 "exterior", "envelope", "elevation", "elevations", "fassade", "wand")
#: Wörter für Bauteile, die NICHT Wand sind — der Stoff davor oder dahinter gehört ihnen
#: («wood window», «zinc roof», «roof of zinc»), nicht der Fassade.
WORTE_NICHT_WAND = (
    "window", "windows", "roof", "roofs", "rooftop", "roofing", "door", "doors", "frame",
    "frames", "balcony", "balconies", "railing", "railings", "balustrade", "terrace",
    "floor", "floors", "ground", "terrain", "path", "paving", "pavement", "stair", "stairs",
    "staircase", "canopy", "pergola", "shutters", "chimney", "dormer", "skylight", "gutter",
    "plinth", "fence", "furniture", "interior", "interiors", "fenster", "dach", "boden",
    "tür", "sockel")

_WORT = re.compile(r"[^\W\d_]+(?:-[^\W\d_]+)*")


def stoff_wunsch(prompt_en: str) -> list[dict]:
    """Die Stoffe, die der (übersetzte) Prompt für die **Fassade** nennt — in Reihenfolge.

    Je Treffer ``{wort, familie, id}``. Gesucht wird je Abschnitt (zwischen Komma, Strichpunkt
    und Punkt), längere Wörter zuerst. Ein Stoff zählt nicht, wenn direkt danach ein Bauteil
    steht, das nicht Wand ist (:data:`WORTE_NICHT_WAND`: «wood window»); er zählt, wenn bis
    drei Wörter davor oder zwei danach ein Fassadenwort steht («facade of exposed concrete»);
    sonst zählt er nicht, wenn davor ein Nicht-Wand-Bauteil steht («roof of zinc»), und ohne
    jeden Bezug nur, wenn das Wort eindeutig ein Wandstoff ist (nicht «render», «glass»).
    """
    phrasen = sorted(STOFF_WUNSCH, key=lambda p: (-len(p.split()), -len(p)))
    treffer: list[tuple[int, int, dict]] = []
    for nr, abschnitt in enumerate(re.split(r"[,;.:\n]", (prompt_en or "").lower())):
        woerter = _WORT.findall(abschnitt)
        belegt = [False] * len(woerter)
        for phrase in phrasen:
            teile = phrase.split()
            n = len(teile)
            for i in range(len(woerter) - n + 1):
                if woerter[i:i + n] != teile or any(belegt[i:i + n]):
                    continue
                for k in range(i, i + n):
                    belegt[k] = True
                familie, kennung, nur_mit_fassade = STOFF_WUNSCH[phrase]
                danach = woerter[i + n:i + n + 2]
                davor = woerter[max(0, i - 3):i]
                if any(w in WORTE_NICHT_WAND for w in danach):
                    continue
                if not any(w in WORTE_FASSADE for w in davor + danach):
                    if any(w in WORTE_NICHT_WAND for w in davor) or nur_mit_fassade:
                        continue
                treffer.append((nr, i, {"wort": phrase, "familie": familie, "id": kennung}))
    return [t for _, _, t in sorted(treffer, key=lambda t: (t[0], t[1]))]
