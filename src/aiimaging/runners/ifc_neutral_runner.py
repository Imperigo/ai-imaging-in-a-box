#!/usr/bin/env python3
"""RUNNER — eine IFC neutralisieren: Texte schwärzen, Namen tilgen, Georeferenz entfernen.

Läuft im `.venv-ifc`, nie im Produkt-Environment — dieselbe Grenze wie
``ifc_to_glb_runner.py`` (ifcopenshell ist LGPL, das Wheel bindet GPL-CGAL statisch ein).
**Dieses Modul darf aus `aiimaging` heraus niemals importiert werden**
(`tests/test_prozessgrenze.py`). Die Teile ohne ifcopenshell (Wortlisten, Namensregeln,
die Prüfung auf neutrale Werte) stehen oben und sind ohne Bibliothek prüfbar; ifcopenshell
wird erst in :func:`neutralisieren` geladen.

Wozu (Auftrag 354, 24.10.2026)
------------------------------
Der Owner will für den Vorführlauf ein echtes Wettbewerbsmodell statt des synthetischen
Demohauses. Ein solches Modell trägt Namen: im Dateikopf, in Personen und Firmen, in
Projekt-, Parzellen- und Bauteilnamen, in Eigenschaften, Klassifikationen und — sichtbar
im Bild — in Beschriftungen. Regel 3 verbietet jeden dieser Namen im Repo; für das Bild
verlangt der Owner, dass sie geschwärzt sind.

Was bleibt, ist, was das Bild trägt: die Geometrie (unverschoben), die IFC-Klasse, der
``PredefinedType``, Öffnungen, Materialien und Stile mit ihren Farben. Materialnamen bleiben
nur, soweit sie aus allgemeinen Stoffwörtern bestehen («Beton», «Glas»); Bauteilnamen
behalten nur Rollenwörter («dach», «gelaende»), weil die Gelände- und Materialregeln des
Kerns am Namen lesen.

**Was diese Neutralisierung nicht leistet — und das ist die schlechte Nachricht:** Sie
tilgt Texte, nicht die Form. Ein echtes Grundstück lässt sich an seiner Gestalt
wiedererkennen; liegen die Koordinaten in Landeskoordinaten, verrät die Geometrie die Lage
selbst (der Bericht warnt dann, ohne Werte zu nennen).

Der Bericht nennt **nur Zahlen und Klassen**, nie einen ursprünglichen Text — er könnte
einen Namen enthalten.

Aufruf:
    .venv-ifc/bin/python ifc_neutral_runner.py <ein.ifc> <aus.ifc> [--report r.json]
"""
from __future__ import annotations

import argparse
import json
import re
import sys

# ======================================================================================
# Die Wortlisten — ohne ifcopenshell, prüfbar überall
# ======================================================================================

#: Stoffwörter, die ein Materialname behalten darf. Sie stammen aus der Materialbibliothek
#: (``aiimaging.materialwahl.BIBLIOTHEK``/``FAMILIE``/``STOFF_WUNSCH``) und den üblichen
#: deutschen und englischen Stoffnamen. Hier steht eine Kopie und kein Import — die
#: Prozessgrenze; ``tests/test_ifc_neutral.py`` prüft, dass die Familien der Bibliothek
#: darin vorkommen. Klein geschrieben, Umlaute als ae/oe/ue/ss.
MATERIALWOERTER = (
    "sichtbeton", "stahlbeton", "ortbeton", "beton", "zement", "estrich", "unterlagsboden",
    "glas", "verglasung", "isolierglas",
    "holz", "fichte", "tanne", "laerche", "eiche", "buche", "dreischichtplatte",
    "holzlattung", "lattung", "schalung", "brett",
    "stahl", "metall", "aluminium", "kupfer", "zink", "blech", "chromstahl",
    "backstein", "klinker", "ziegel", "mauerwerk", "kalksandstein",
    "naturstein", "sandstein", "kalkstein", "granit", "stein", "kies", "schotter",
    "putz", "verputz", "glattputz", "rauputz", "gips", "lehm", "stampflehm",
    "daemmung", "waermedaemmung",
    "erde", "gras", "rasen", "asphalt", "pflaster", "wasser", "kunststoff",
    "concrete", "glass", "wood", "timber", "spruce", "steel", "metal", "aluminum",
    "copper", "zinc", "brick", "masonry", "stone", "sandstone", "plaster", "render",
    "earth", "grass", "gravel", "insulation",
    "weiss", "grau", "schwarz", "rot", "gruen", "blau", "braun", "gelb",
    "white", "grey", "gray", "black", "red", "green", "blue", "brown",
    "hell", "dunkel", "glatt", "rau", "sandgestrahlt", "schalungsglatt",
)

#: Rollenwörter, die ein Bauteilname behalten darf, weil der Kern am Namen liest:
#: ``materialwahl.NAME_ZU_ART``/``NAME_OEFFNUNG``/``NAME_TUER`` und die Wortregel für
#: Gelände (``maske.GELAENDE_WOERTER``, ``ifc_to_glb_runner.GELAENDE_OBJEKTWOERTER``).
#: Sie werden als **Teil eines Worts** gefunden («Aussenwand» → «wand») und als blosses
#: Rollenwort ausgegeben — ein Name, der das Wort enthält, gelangt so nie in die Kopie.
#: ``site`` fehlt mit Absicht: Es ist Teil von «Composite» und machte eine Wand zu Gelände.
ROLLENWOERTER = (
    "fenster", "window", "verglasung", "glazing", "dachfenster",
    "dach", "roof", "fassade", "facade", "wand", "wall",
    "bodenplatte", "geschossdecke", "decke", "floor", "slab", "boden",
    "oeffnung", "opening", "tuer", "door",
    "treppe", "stair", "stuetze", "column", "balkon", "balcony", "gelaender", "railing",
    "baum", "tree", "strasse", "street", "weg", "platz", "mauer", "sockel",
)

#: Geländewörter — sie zählen nur als **ganzes Wort**: «Gelaender» (ein Handlauf) enthält
#: «gelaende» und wäre sonst Gelände. Dieselbe Regel wie ``maske.GELAENDE_WOERTER`` (dort
#: zusätzlich ``site``, siehe oben).
GELAENDE_GANZWORT = ("gelaende", "gelaendeflaeche", "terrain", "toposolid")

#: Wörter, an denen ein Bauteil als **Beschriftung** erkannt und entfernt wird (Schild,
#: Logo, Schriftzug). Ganze Wörter; dazu :data:`BESCHRIFTUNG_TEIL` als Wortteil.
BESCHRIFTUNG_GANZWORT = (
    "text", "texte", "schrift", "label", "labels", "logo", "logos", "signet", "signage",
    "sign", "schild", "lettering", "legende", "planstempel", "stempel", "plannr",
)
BESCHRIFTUNG_TEIL = ("beschriftung", "schriftzug", "plannummer", "planbeschrift")

#: IFC-Klassen, die immer entfernt werden: sichtbarer Text und seine Stile, Verweise auf
#: Dokumente, Klassifikationen, Bibliotheken, Adressen. Fehlt eine im Schema, wird sie
#: übergangen.
ENTFERNEN_KLASSEN = (
    "IfcAnnotation", "IfcSign",
    "IfcTextLiteral", "IfcTextLiteralWithExtent", "IfcAnnotationTextOccurrence",
    "IfcTextStyle", "IfcTextStyleForDefinedFont", "IfcTextStyleTextModel",
    "IfcTextStyleFontModel", "IfcTextStyleWithBoxCharacteristics",
    "IfcDraughtingPreDefinedTextFont", "IfcExternallyDefinedTextFont",
    "IfcRelAssociatesClassification", "IfcClassificationReference", "IfcClassification",
    "IfcClassificationNotation", "IfcClassificationNotationFacet", "IfcClassificationItem",
    "IfcClassificationItemRelationship",
    "IfcRelAssociatesDocument", "IfcDocumentReference", "IfcDocumentInformation",
    "IfcDocumentInformationRelationship", "IfcDocumentElectronicFormat",
    "IfcRelAssociatesLibrary", "IfcLibraryReference", "IfcLibraryInformation",
    "IfcExternalReferenceRelationship", "IfcExternallyDefinedSurfaceStyle",
    "IfcExternallyDefinedHatchStyle",
    "IfcPostalAddress", "IfcTelecomAddress", "IfcActorRole",
)

#: Wertarten einer Eigenschaft, die Text tragen — eine solche Eigenschaft wird entfernt.
TEXTWERTE = ("IfcLabel", "IfcText", "IfcIdentifier", "IfcDescriptiveMeasure", "IfcDate",
             "IfcDateTime", "IfcTime", "IfcDuration", "IfcURIReference")

#: Eigenschaftssätze, die die Lage tragen (IFC2X3 kennt kein IfcMapConversion und schreibt
#: sie als Zahlen in einen Satz) — als ganzer Satz entfernt, auch mit Zahlenwerten.
GEOREF_SATZWOERTER = ("mapconversion", "projectedcrs", "georef", "georeferenz",
                      "coordinatereferencesystem")

#: Die neutralen Festwerte.
NEUTRAL_PROGRAMM = "Visbox"
NEUTRAL_DATEINAME = "modell.ifc"
NEUTRAL_ZEIT = "2000-01-01T00:00:00"
NEUTRAL_ZEITSTEMPEL = 946684800
NEUTRAL_KONSTANTEN = frozenset({
    "", NEUTRAL_PROGRAMM, NEUTRAL_DATEINAME, NEUTRAL_ZEIT, "Projekt", "Grundstück", "Lokal",
    "0", "benutzerdefiniert", "2;1", "ViewDefinition [CoordinationView]",
})

#: Namen mit Zähler: «Gebäude 1», «Material 3», «gelaende IfcSlab 2».
_ZAEHLNAME = re.compile(
    r"^(?:(?P<rollen>[a-z]+(?: [a-z]+){0,2}) )?"
    r"(?:Gebäude|Geschoss|Raum|Material|Ebene|Wert|Eigenschaften|Einheit|Ifc[A-Za-z0-9]+)"
    r" \d+$")

#: Standardsätze von buildingSMART — ihr Name und die Namen ihrer Eigenschaften bleiben.
#:
#: **Eng mit Absicht.** ``Pset_`` allein genügt nicht: Autorenprogramme und Büros legen
#: eigene Sätze als ``Pset_<Firmenname>`` an (die Probe trägt darum ``Pset_MusterAG``).
#: Erkannt werden nur die beiden Formen der Norm, die in jedem Export vorkommen — die
#: ``…Common``-Sätze und die Mengensätze. Alle anderen heissen danach «Eigenschaften N».
_NORMSATZ = re.compile(
    r"^Pset_[A-Z][A-Za-z]*Common$|^Qto_[A-Z][A-Za-z]*(?:BaseQuantities|Quantities)$"
    r"|^BaseQuantities$")
_NORMEIGENSCHAFT = re.compile(r"^[A-Z][A-Za-z0-9]{0,47}$")
_SICHT = re.compile(r"^ViewDefinition \[[A-Za-z0-9_.,; -]{1,80}\]$")

#: Das Vokabular der Darstellungen — Wörter der Norm, keine Namen. Was nicht darin steht,
#: wird geleert (die Attribute sind optional).
DARSTELLUNG_VOKABULAR = frozenset({
    "model", "plan", "design", "sketch", "outline", "notdefined",
    "body", "axis", "box", "footprint", "annotation", "profile", "surface", "clearance",
    "cog", "lighting", "reference", "facetation", "body-fallback", "plan-annotation",
    "sweptsolid", "advancedsweptsolid", "brep", "advancedbrep", "surfacemodel",
    "tessellation", "mappedrepresentation", "clipping", "csg", "boundingbox", "curve",
    "curve2d", "curve3d", "geometricset", "geometriccurveset", "point", "pointcloud",
    "sectionedspine", "annotation2d", "fillarea", "segment", "lightsource", "solidmodel",
    "surface2d", "surface3d", "text",
})
DARSTELLUNG_ATTRIBUTE = ("ContextType", "ContextIdentifier", "RepresentationIdentifier",
                         "RepresentationType", "TargetView")

#: Einheitennamen der Norm (IfcConversionBasedUnit) — keine Namen von Menschen.
EINHEITEN_VOKABULAR = frozenset({
    "degree", "grad", "foot", "inch", "yard", "mile", "square foot", "square inch",
    "square yard", "acre", "square mile", "cubic foot", "cubic inch", "cubic yard",
    "litre", "liter", "gallon", "pound", "ounce", "ton", "kip", "minute", "hour", "day",
    "fluid ounce uk", "fluid ounce us", "pint uk", "pint us", "gallon uk", "gallon us",
    "us survey foot", "gon", "radian", "kilonewton", "btu",
})

_UMLAUTE = str.maketrans({"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss", "é": "e", "è": "e",
                          "à": "a"})


def normalwort(text) -> str:
    """Klein, Umlaute ausgeschrieben."""
    return str(text or "").lower().translate(_UMLAUTE)


def woerter(text) -> list[str]:
    """Ein Text in Wörter zerlegt — an allem, was kein Buchstabe ist."""
    return [w for w in re.split(r"[^a-z]+", normalwort(text)) if w]


def behaltene_woerter(*texte, liste=ROLLENWOERTER + MATERIALWOERTER,
                      ganzwort=GELAENDE_GANZWORT, hoechstens: int = 3) -> list[str]:
    """Die Wörter aus ``liste``/``ganzwort``, die in den Texten vorkommen — **nur diese**.

    Ausgegeben wird das Listenwort, nie das Wort aus dem Text: «Musterwand» ergibt «wand».
    So kann kein Name über diese Funktion in die Kopie gelangen. Längere Listenwörter
    zuerst («dachfenster» vor «dach»).
    """
    nach_laenge = sorted(liste, key=len, reverse=True)
    raus: list[str] = []
    for text in texte:
        for wort in woerter(text):
            treffer = wort if wort in ganzwort else next(
                (w for w in nach_laenge if w in wort), None)
            if treffer and treffer not in raus:
                raus.append(treffer)
    return raus[:hoechstens]


def ist_beschriftung(*texte) -> bool:
    """Nennt ein Bauteil sich Schild, Logo, Schriftzug? (Name oder ObjectType.)"""
    for text in texte:
        ws = woerter(text)
        if any(w in BESCHRIFTUNG_GANZWORT for w in ws):
            return True
        if any(t in w for w in ws for t in BESCHRIFTUNG_TEIL):
            return True
        if "plan" in ws and ("nr" in ws or "nummer" in ws):
            return True
    return False


def bauteilname(klasse: str, n: int, *texte) -> str:
    """«gelaende IfcSlab 3» — Rollenwörter **vorn**: Der glb-Knotenname kürzt den Namen
    nach 24 Zeichen (``ifc_to_glb_runner.NAME_HOECHSTENS``), und das Rollenwort ist das,
    was die Gelände- und Materialregeln lesen; der Zähler darf abgeschnitten werden."""
    rollen = behaltene_woerter(*texte)
    return " ".join(rollen + [f"{klasse} {n}"])


def materialname(name, n: int) -> str:
    """Nur Stoffwörter bleiben («Sichtbeton Muster» → «Sichtbeton»), sonst «Material N».

    «Material N» gilt in ``materialwahl.ist_benanntes_material`` als **unbenannt** — ein
    getilgter Name soll keine Wahl auslösen, die nur ein echter Stoffname auslösen darf.
    """
    behalten = behaltene_woerter(name, liste=MATERIALWOERTER, ganzwort=(), hoechstens=3)
    if behalten:
        return " ".join(w.capitalize() for w in behalten)
    return f"Material {n}"


def _nur_listenwoerter(wert: str) -> bool:
    teile = wert.split(" ")
    erlaubt = set(MATERIALWOERTER) | set(ROLLENWOERTER) | set(GELAENDE_GANZWORT)
    return bool(teile) and len(teile) <= 3 and all(normalwort(t) in erlaubt for t in teile)


def ist_neutral(klasse: str, attribut: str, wert, *, normsatz: bool = False) -> bool:
    """Ist dieser Textwert neutral — einer, den die Neutralisierung selbst schreibt oder der
    nur aus Wörtern der Norm und der Listen besteht?

    Die Restprüfung fragt das für **jeden** Text der fertigen Datei. Was hier nicht
    durchgeht, ist ein Resttext — gemeldet mit Klasse und Attribut, nie mit dem Wert.
    """
    if wert is None:
        return True
    wert = str(wert)
    if wert in NEUTRAL_KONSTANTEN:
        return True
    if (m := _ZAEHLNAME.match(wert)):
        rollen = (m.group("rollen") or "").split()
        return all(r in ROLLENWOERTER or r in MATERIALWOERTER or r in GELAENDE_GANZWORT
                   for r in rollen)
    if _nur_listenwoerter(wert):
        return True
    if attribut in DARSTELLUNG_ATTRIBUTE and wert.lower() in DARSTELLUNG_VOKABULAR:
        return True
    if klasse in ("IfcConversionBasedUnit", "IfcContextDependentUnit",
                  "IfcConversionBasedUnitWithOffset") and wert.lower() in EINHEITEN_VOKABULAR:
        return True
    if klasse in ("IfcPropertySet", "IfcElementQuantity") and attribut == "Name" \
            and _NORMSATZ.match(wert):
        return True
    if normsatz and attribut == "Name" and _NORMEIGENSCHAFT.match(wert):
        return True
    if attribut == "description" and _SICHT.match(wert):
        return True
    return False


def ist_normsatzname(name) -> bool:
    return bool(_NORMSATZ.match(str(name or "")))


def ist_georef_satz(name) -> bool:
    n = normalwort(name).replace("_", "").replace(" ", "")
    return any(w in n for w in GEOREF_SATZWOERTER)


def resttexte_zusammenfassen(funde) -> dict:
    """``[(klasse, attribut), …]`` → ``{"anzahl": n, "stellen": [{klasse, attribut, anzahl}]}``.

    Die Werte selbst kommen hier gar nicht erst an.
    """
    zaehler: dict[tuple[str, str], int] = {}
    for klasse, attribut in funde:
        zaehler[(klasse, attribut)] = zaehler.get((klasse, attribut), 0) + 1
    return {"anzahl": sum(zaehler.values()),
            "stellen": [{"klasse": k, "attribut": a, "anzahl": n}
                        for (k, a), n in sorted(zaehler.items())]}


#: Ab wieviel Metern vom Ursprung eine Koordinate als «Landeskoordinate» gilt: Dann
#: verrät die Geometrie die Lage selbst, auch ohne Georeferenz.
GROSSE_KOORDINATE_M = 10_000.0


# ======================================================================================
# Ab hier mit ifcopenshell — nur in diesem Prozess
# ======================================================================================

def _klassen(modell, name):
    try:
        return list(modell.by_type(name))
    except Exception:                                 # noqa: BLE001 — nicht im Schema
        return []


def _zaehlung(modell) -> dict[str, int]:
    z: dict[str, int] = {}
    for e in modell:
        z[e.is_a()] = z.get(e.is_a(), 0) + 1
    return z


def _ist_bauteil(e) -> bool:
    return (e.is_a("IfcElement") and not e.is_a("IfcFeatureElement")
            and not e.is_a("IfcVirtualElement") and bool(getattr(e, "Representation", None)))


def _n_bauteile(modell) -> int:
    return sum(1 for e in _klassen(modell, "IfcElement") if _ist_bauteil(e))


class _Schema:
    """Je Klasse: welche Attribute Text tragen können, und ob sie optional sind."""

    def __init__(self, modell):
        import ifcopenshell.ifcopenshell_wrapper as wrapper  # noqa: PLC0415
        self._schema = wrapper.schema_by_name(modell.schema)
        self._cache: dict[str, list] = {}

    def textattribute(self, klasse: str) -> list[tuple[int, str, bool, str]]:
        """``[(index, name, optional, art)]`` mit art ``text``/``liste``/``auswahl``."""
        if klasse in self._cache:
            return self._cache[klasse]
        raus = []
        for i, a in enumerate(self._schema.declaration_by_name(klasse).all_attributes()):
            typ = str(a.type_of_attribute())
            if a.name() == "GlobalId" or "IfcGloballyUniqueId" in typ \
                    or typ.startswith("<enumeration"):
                continue
            if typ.startswith(("<list", "<set", "<array", "<bag")):
                if "<select" in typ:
                    raus.append((i, a.name(), a.optional(), "auswahl"))
                elif "<string>" in typ and "<enumeration" not in typ:
                    raus.append((i, a.name(), a.optional(), "liste"))
            elif typ.startswith("<select"):
                raus.append((i, a.name(), a.optional(), "auswahl"))
            elif "<string>" in typ:
                raus.append((i, a.name(), a.optional(), "text"))
        self._cache[klasse] = raus
        return raus

    def optional(self, klasse: str, attribut: str) -> bool:
        for a in self._schema.declaration_by_name(klasse).all_attributes():
            if a.name() == attribut:
                return a.optional()
        return True


def _texte_im_wert(wert):
    """Alle Texte in einem Attributwert — auch in eingebetteten Typwerten (IfcLabel)."""
    if isinstance(wert, str):
        yield wert
    elif isinstance(wert, (tuple, list)):
        for w in wert:
            yield from _texte_im_wert(w)
    elif wert is not None and hasattr(wert, "is_a") and hasattr(wert, "id") and wert.id() == 0:
        inner = getattr(wert, "wrappedValue", None)
        if isinstance(inner, str):
            yield inner


def _normsatz_eigenschaft(modell, e) -> bool:
    """Steht diese Eigenschaft (nur) in Standardsätzen?"""
    saetze = [i for i in modell.get_inverse(e)
              if i.is_a("IfcPropertySet") or i.is_a("IfcElementQuantity")]
    return bool(saetze) and all(ist_normsatzname(s.Name) for s in saetze)


def restpruefung(modell) -> list[tuple[str, str]]:
    """Jeder Text der Datei, der nicht neutral ist — als ``(klasse, attribut)``."""
    schema = _Schema(modell)
    funde: list[tuple[str, str]] = []
    kopf = modell.header
    for attribut, werte in (
            ("name", [kopf.file_name.name]), ("time_stamp", [kopf.file_name.time_stamp]),
            ("author", list(kopf.file_name.author)),
            ("organization", list(kopf.file_name.organization)),
            ("preprocessor_version", [kopf.file_name.preprocessor_version]),
            ("originating_system", [kopf.file_name.originating_system]),
            ("authorization", [kopf.file_name.authorization]),
            ("description", list(kopf.file_description.description)),
            ("implementation_level", [kopf.file_description.implementation_level])):
        for w in werte:
            if not ist_neutral("HEADER", attribut, w):
                funde.append(("HEADER", attribut))
    for e in modell:
        klasse = e.is_a()
        attribute = schema.textattribute(klasse)
        if not attribute:
            continue
        normsatz = None
        for i, name, _opt, _art in attribute:
            for text in _texte_im_wert(e[i]):
                if ist_neutral(klasse, name, text):
                    continue
                if name == "Name" and (e.is_a("IfcProperty") or e.is_a("IfcPhysicalQuantity")):
                    if normsatz is None:
                        normsatz = _normsatz_eigenschaft(modell, e)
                    if ist_neutral(klasse, name, text, normsatz=normsatz):
                        continue
                funde.append((klasse, name))
    return funde


class _Entferner:
    """Entfernt Entitäten und merkt sich, wer auf sie zeigte.

    Nur diese «Betroffenen» können danach leer oder ungültig sein — :meth:`aufraeumen`
    prüft darum sie und nicht jede Entität der Datei. Ein Geländemodell hat Hunderttausende
    Punkte, und keiner davon zeigte je auf eine Beschriftung.
    """

    def __init__(self, modell, schema):
        self.modell = modell
        self.schema = schema
        self.betroffen: set[int] = set()

    def entfernen(self, e) -> None:
        try:
            for i in self.modell.get_inverse(e):
                self.betroffen.add(i.id())
            self.modell.remove(e)
        except Exception:                             # noqa: BLE001 — schon weg
            pass

    def produkt(self, produkt) -> None:
        """Ein Produkt samt Darstellung und Beziehungen entfernen (über die API)."""
        try:
            for i in self.modell.get_inverse(produkt):
                self.betroffen.add(i.id())
        except Exception:                             # noqa: BLE001
            pass
        try:
            import ifcopenshell.api.root  # noqa: PLC0415
            ifcopenshell.api.root.remove_product(self.modell, product=produkt)
            return
        except Exception:                             # noqa: BLE001 — älteres ifcopenshell
            pass
        try:
            import ifcopenshell.api  # noqa: PLC0415
            ifcopenshell.api.run("root.remove_product", self.modell, product=produkt)
        except Exception:                             # noqa: BLE001
            self.entfernen(produkt)

    def _leer(self, e) -> bool:
        """Ist eine Entität durch das Entfernen sinnlos geworden?"""
        if e.is_a("IfcRelationship"):
            for i in range(len(e)):
                name = e.attribute_name(i)
                if not name.startswith(("Related", "Relating")) or name.endswith("Priorities"):
                    continue
                wert = e[i]
                if wert is None and not self.schema.optional(e.is_a(), name):
                    return True
                if isinstance(wert, tuple) and not wert:
                    return True
            return False
        for klasse, attribut in (("IfcPropertySet", "HasProperties"),
                                 ("IfcComplexProperty", "HasProperties"),
                                 ("IfcElementQuantity", "Quantities"),
                                 ("IfcStyledItem", "Styles"),
                                 ("IfcPresentationStyleAssignment", "Styles"),
                                 ("IfcRepresentation", "Items"),
                                 ("IfcProductRepresentation", "Representations"),
                                 ("IfcPresentationLayerAssignment", "AssignedItems")):
            if e.is_a(klasse):
                return not getattr(e, attribut, None)
        return False

    def aufraeumen(self) -> None:
        while self.betroffen:
            ids, self.betroffen = self.betroffen, set()
            for nr in ids:
                try:
                    e = self.modell.by_id(nr)
                except Exception:                     # noqa: BLE001 — inzwischen entfernt
                    continue
                if self._leer(e):
                    if e.is_a("IfcPropertySetDefinition"):
                        for rel in [r for r in self.modell.get_inverse(e)
                                    if r.is_a("IfcRelDefinesByProperties")]:
                            self.entfernen(rel)
                    self.entfernen(e)
                    continue
                # Leere optionale Listen → $ (eine leere Liste ist in STEP ungültig).
                for i in range(len(e)):
                    wert = e[i]
                    if isinstance(wert, tuple) and not wert and self.schema.optional(
                            e.is_a(), e.attribute_name(i)):
                        e[i] = None
        for p in _klassen(self.modell, "IfcPropertyEnumeration"):
            if not self.modell.get_inverse(p):
                self.entfernen(p)


def _ist_textwert(wert) -> bool:
    for w in (wert if isinstance(wert, (tuple, list)) else (wert,)):
        if w is not None and hasattr(w, "is_a") and w.is_a() in TEXTWERTE:
            return True
    return False


def _eigenschaft_traegt_text(p) -> bool:
    if p.is_a("IfcPropertyReferenceValue"):
        return True
    for attribut in ("NominalValue", "EnumerationValues", "ListValues", "UpperBoundValue",
                     "LowerBoundValue", "SetPointValue", "DefiningValues", "DefinedValues"):
        if _ist_textwert(getattr(p, attribut, None)):
            return True
    return False


def _laengen_skala(modell) -> float:
    try:
        import ifcopenshell.util.unit  # noqa: PLC0415
        return float(ifcopenshell.util.unit.calculate_unit_scale(modell))
    except Exception:                                 # noqa: BLE001
        return 1.0


def neutralisieren(ein: str, aus: str) -> dict:
    import ifcopenshell            # noqa: PLC0415 — bewusst lokal: nur in diesem Prozess
    import ifcopenshell.guid       # noqa: PLC0415

    modell = ifcopenshell.open(ein)
    schema = _Schema(modell)
    vorher = _zaehlung(modell)
    n_bauteile_vorher = _n_bauteile(modell)
    warnungen: list[str] = []
    n_umbenannt = 0
    weg = _Entferner(modell, schema)

    # ── 1 · Beschriftung: Anmerkungen und Bauteile, die sich Schild/Logo/Text nennen.
    beschriftung: list[str] = []
    zaehler_b: dict[str, int] = {}
    for e in _klassen(modell, "IfcElement") + _klassen(modell, "IfcProxy"):
        if e.is_a("IfcFeatureElement"):
            continue
        if ist_beschriftung(getattr(e, "Name", None), getattr(e, "ObjectType", None)):
            zaehler_b[e.is_a()] = zaehler_b.get(e.is_a(), 0) + 1
            beschriftung.append(f"{e.is_a()} {zaehler_b[e.is_a()]}")
            weg.produkt(e)
    for klasse in ("IfcAnnotation", "IfcSign"):
        for e in _klassen(modell, klasse):
            weg.produkt(e)

    # ── 2 · Georeferenz. Die Geometrie bleibt, wo sie ist.
    georef = False
    for site in _klassen(modell, "IfcSite"):
        for attribut in ("RefLatitude", "RefLongitude", "RefElevation", "LandTitleNumber"):
            if getattr(site, attribut, None) is not None:
                setattr(site, attribut, None)
                georef = True
    for e in _klassen(modell, "IfcCoordinateOperation"):
        for attribut in ("Eastings", "Northings", "OrthogonalHeight"):
            if getattr(e, attribut, None) not in (None, 0, 0.0):
                setattr(e, attribut, 0.0)
                georef = True
    for crs in _klassen(modell, "IfcCoordinateReferenceSystem"):
        georef = True
        if crs.Name is not None or not schema.optional(crs.is_a(), "Name"):
            crs.Name = "Lokal"
        for attribut in ("Description", "GeodeticDatum", "VerticalDatum", "MapProjection",
                         "MapZone"):
            if getattr(crs, attribut, None) is not None:
                setattr(crs, attribut, None)
    for satz in _klassen(modell, "IfcPropertySet"):
        if ist_georef_satz(satz.Name):
            georef = True
            for p in list(satz.HasProperties or ()):
                weg.entfernen(p)
            for rel in [r for r in modell.get_inverse(satz)
                        if r.is_a("IfcRelDefinesByProperties")]:
                weg.entfernen(rel)
            weg.entfernen(satz)

    # ── 3 · Text, Verweise, Adressen: als Klasse entfernt.
    for klasse in ENTFERNEN_KLASSEN:
        for e in _klassen(modell, klasse):
            weg.entfernen(e)

    # ── 4 · Eigenschaften mit Text.
    for p in _klassen(modell, "IfcProperty"):
        if _eigenschaft_traegt_text(p):
            weg.entfernen(p)
    weg.aufraeumen()

    # ── 5 · Namen. Jede Zuweisung zählt als Umbenennung.
    def setze(e, attribut, wert):
        nonlocal n_umbenannt
        if getattr(e, attribut, None) != wert:
            setattr(e, attribut, wert)
            n_umbenannt += 1

    zaehler: dict[str, int] = {}

    def naechste(schluessel: str) -> int:
        zaehler[schluessel] = zaehler.get(schluessel, 0) + 1
        return zaehler[schluessel]

    for e in _klassen(modell, "IfcProject"):
        setze(e, "Name", "Projekt")
    for e in _klassen(modell, "IfcSite"):
        setze(e, "Name", "Grundstück")
    for e in _klassen(modell, "IfcBuilding"):
        setze(e, "Name", f"Gebäude {naechste('Gebäude')}")
    for e in sorted(_klassen(modell, "IfcBuildingStorey"),
                    key=lambda s: (s.Elevation if s.Elevation is not None else 0.0, s.id())):
        setze(e, "Name", f"Geschoss {naechste('Geschoss') - 1}")
    for e in _klassen(modell, "IfcSpace"):
        setze(e, "Name", f"Raum {naechste('Raum')}")
    for e in _klassen(modell, "IfcObjectDefinition"):
        if e.is_a("IfcProject") or e.is_a("IfcSite") or e.is_a("IfcBuilding") \
                or e.is_a("IfcBuildingStorey") or e.is_a("IfcSpace"):
            continue
        texte = (getattr(e, "Name", None), getattr(e, "ObjectType", None))
        if e.is_a("IfcElement") or e.is_a("IfcTypeProduct"):
            neu = bauteilname(e.is_a(), naechste(e.is_a()), *texte)
        else:
            neu = f"{e.is_a()} {naechste(e.is_a())}"
        setze(e, "Name", neu)
        if hasattr(e, "ObjectType"):
            rollen = behaltene_woerter(*texte)
            vordef = str(getattr(e, "PredefinedType", "") or "").upper()
            if rollen:
                setze(e, "ObjectType", " ".join(rollen))
            elif vordef == "USERDEFINED":
                setze(e, "ObjectType", "benutzerdefiniert")
            else:
                setze(e, "ObjectType", None)
    for e in _klassen(modell, "IfcPropertySetDefinition"):
        if hasattr(e, "Name") and not ist_normsatzname(e.Name):
            setze(e, "Name", f"Eigenschaften {naechste('Eigenschaften')}")
    for p in _klassen(modell, "IfcProperty") + _klassen(modell, "IfcPhysicalQuantity"):
        if not (_normsatz_eigenschaft(modell, p) and _NORMEIGENSCHAFT.match(p.Name or "")):
            setze(p, "Name", f"Wert {naechste('Wert')}")
    for klasse, attribut in (("IfcMaterial", "Name"), ("IfcMaterialLayerSet", "LayerSetName"),
                             ("IfcMaterialLayer", "Name"), ("IfcMaterialProfileSet", "Name"),
                             ("IfcMaterialProfile", "Name"),
                             ("IfcMaterialConstituentSet", "Name"),
                             ("IfcMaterialConstituent", "Name"),
                             ("IfcPresentationStyle", "Name")):
        for e in _klassen(modell, klasse):
            alt = getattr(e, attribut, None)
            if alt is None and schema.optional(e.is_a(), attribut):
                continue
            setze(e, attribut, materialname(alt, naechste("Material")))
    for e in _klassen(modell, "IfcPresentationLayerAssignment"):
        setze(e, "Name", f"Ebene {naechste('Ebene')}")
    for e in _klassen(modell, "IfcPerson"):
        setze(e, "FamilyName", NEUTRAL_PROGRAMM)
        setze(e, "GivenName", None)
    for e in _klassen(modell, "IfcOrganization"):
        setze(e, "Name", NEUTRAL_PROGRAMM)
    for e in _klassen(modell, "IfcApplication"):
        setze(e, "ApplicationFullName", NEUTRAL_PROGRAMM)
        setze(e, "ApplicationIdentifier", NEUTRAL_PROGRAMM)
        setze(e, "Version", "0")
    for e in _klassen(modell, "IfcOwnerHistory"):
        setze(e, "CreationDate", NEUTRAL_ZEITSTEMPEL)
        setze(e, "LastModifiedDate", None)
    # Nur die umgerechneten Einheiten: Bei IfcSIUnit ist «Name» eine Aufzählung (METRE).
    for e in (_klassen(modell, "IfcConversionBasedUnit")
              + _klassen(modell, "IfcContextDependentUnit")):
        name = getattr(e, "Name", None)
        if isinstance(name, str) and not ist_neutral(e.is_a(), "Name", name):
            setze(e, "Name", f"Einheit {naechste('Einheit')}")

    # ── 6 · Alles übrige: jeder Text, der nicht neutral ist — optional geleert, Pflicht
    #       mit einem Zählnamen bzw. leer. Hier fällt auch, was keine Regel oben kennt.
    for e in list(modell):
        klasse = e.is_a()
        for i, name, optional, art in schema.textattribute(klasse):
            wert = e[i]
            texte = list(_texte_im_wert(wert))
            if not texte:
                continue
            if all(ist_neutral(klasse, name, t) for t in texte):
                continue
            if name == "Name" and (e.is_a("IfcProperty") or e.is_a("IfcPhysicalQuantity")) \
                    and all(ist_neutral(klasse, name, t, normsatz=_normsatz_eigenschaft(
                        modell, e)) for t in texte):
                continue
            if optional:
                e[i] = None
            elif art == "text":
                e[i] = f"{klasse} {naechste(klasse)}" if name == "Name" else ""
            elif art == "liste":
                e[i] = ("",)
            else:
                # Pflicht-Auswahl mit Text (selten): ein leeres Label an seiner Stelle.
                e[i] = modell.create_entity("IfcLabel", "")
            n_umbenannt += 1

    # ── 7 · GlobalIds neu: Die Kopie lässt sich nicht über die Kennung zuordnen.
    n_guid = 0
    for e in _klassen(modell, "IfcRoot"):
        e.GlobalId = ifcopenshell.guid.new()
        n_guid += 1

    # ── 8 · Der Dateikopf.
    kopf = modell.header
    kopf.file_name.name = NEUTRAL_DATEINAME
    kopf.file_name.time_stamp = NEUTRAL_ZEIT
    kopf.file_name.author = ("",)
    kopf.file_name.organization = ("",)
    kopf.file_name.preprocessor_version = NEUTRAL_PROGRAMM
    kopf.file_name.originating_system = NEUTRAL_PROGRAMM
    kopf.file_name.authorization = ""
    sichten = [d for d in kopf.file_description.description if _SICHT.match(str(d))]
    kopf.file_description.description = tuple(sichten) or ("ViewDefinition [CoordinationView]",)

    # ── 9 · Lage in der Geometrie selbst? Nur gewarnt, nicht verschoben.
    skala = _laengen_skala(modell)
    weit = 0.0
    for p in _klassen(modell, "IfcCartesianPoint"):
        for k in p.Coordinates or ():
            weit = max(weit, abs(float(k)) * skala)
    if weit > GROSSE_KOORDINATE_M:
        warnungen.append(
            f"Koordinaten liegen über {int(GROSSE_KOORDINATE_M / 1000)} km vom Ursprung "
            "entfernt — wohl Landeskoordinaten. Die Lage folgt dann aus der Geometrie "
            "selbst; die Neutralisierung verschiebt nichts.")
    if beschriftung:
        warnungen.append(f"{len(beschriftung)} Bauteil(e) als Beschriftung entfernt "
                         "(Name oder Objekttyp nannte Schild, Logo, Text o. ä.).")

    modell.write(aus)

    # ── 10 · Die Restprüfung an der GESCHRIEBENEN Datei, nicht am Speicherstand.
    geschrieben = ifcopenshell.open(aus)
    rest = resttexte_zusammenfassen(restpruefung(geschrieben))
    nachher = _zaehlung(geschrieben)
    entfernt = {k: n - nachher.get(k, 0) for k, n in sorted(vorher.items())
                if n - nachher.get(k, 0) > 0}
    return {
        "status": "ok",
        "schema": modell.schema,
        "n_entfernt": entfernt,
        "n_entfernt_summe": sum(entfernt.values()),
        "n_umbenannt": n_umbenannt,
        "n_globalid_neu": n_guid,
        "georeferenz_entfernt": georef,
        # Liegt die Geometrie selbst in Landeskoordinaten? Dann verrät sie die Lage.
        "landeskoordinaten": weit > GROSSE_KOORDINATE_M,
        "beschriftung_entfernt": beschriftung,
        "resttexte": rest,
        "n_bauteile": {"vorher": n_bauteile_vorher, "nachher": _n_bauteile(geschrieben)},
        "n_entitaeten": {"vorher": sum(vorher.values()), "nachher": sum(nachher.values())},
        "warnungen": warnungen,
        "hinweis": ("Der Bericht nennt nur Zahlen und Klassen, nie einen ursprünglichen "
                    "Text. Die Form eines echten Orts bleibt erkennbar."),
        "error": None,
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="IFC neutralisieren. Läuft im .venv-ifc.")
    ap.add_argument("ein")
    ap.add_argument("aus")
    ap.add_argument("--report", default=None)
    a = ap.parse_args(argv)
    try:
        rep = neutralisieren(a.ein, a.aus)
    except Exception as e:                            # noqa: BLE001 — Fehler als Report
        # NUR DIE ART DES FEHLERS: Eine Meldung von ifcopenshell kann einen Wert aus der
        # Datei zitieren, und ein Wert kann ein Name sein.
        rep = {"status": "error", "error": f"{type(e).__name__} beim Neutralisieren"}
    text = json.dumps(rep, indent=2, ensure_ascii=False)
    if a.report:
        with open(a.report, "w", encoding="utf-8") as fh:
            fh.write(text)
    print(text)
    return 0 if rep["status"] == "ok" else 1


if __name__ == "__main__":
    sys.exit(main())
