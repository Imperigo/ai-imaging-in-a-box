"""Der Graph-Kern der Bildkette: Reihenfolge, Datenfluss, Zwischenspeicher.

Warum eigener Bau statt ComfyUI
-------------------------------
ComfyUI ist der De-facto-Standard für knotenbasierte Bildketten — und steht unter
**GPL-3.0**. Als Kern des ausgelieferten Produkts ist es damit ausgeschlossen (Regel 1),
und zwar nicht knapp: Ein Graph-Kern ist keine Komponente, die man hinter eine
Prozessgrenze schieben könnte, er ist die Mitte des Programms. Also bauen wir ihn selbst.

Was dieses Modul **nicht** ist
------------------------------
Es ist kein Nachbau von ComfyUIs Knoten-Zoo. Hier steht ausschliesslich Ablaufsteuerung:
in welcher Reihenfolge gerechnet wird, welche Ergebnisse wohin fliessen, und was
wiederverwendet werden darf. Was ein Knoten *tut*, weiss dieses Modul nicht — die Arbeit
liegt später in ``diffusers`` und jenseits der Prozessgrenzen in ``aiimaging.seams``.
Klein zu bleiben ist hier eine Anforderung, kein Zwischenstand.

Innen und aussen
----------------
Von aussen ist unsere ganze Bildkette **ein** Knoten in KosmoOrbits Pipeline; innen ist
sie selbst ein Graph. Dieser hier ist der innere. Die beiden Ebenen dürfen nicht
verwechselt werden: KosmoOrbit verdrahtet über Feldnamen-Gleichheit (siehe
``contracts.py``), hier drinnen wird über Knoten-IDs verdrahtet.

Reproduzierbarkeit ist der Zweck
--------------------------------
Zwei Läufe mit gleicher Eingabe müssen dieselbe Reihenfolge und dieselben Hashes
ergeben, sonst ist die spätere Geometrie-QA nicht vergleichbar und der Cache liefert
mal Treffer, mal nicht. Darum: sortierte Auswahl bei gleichrangigen Knoten,
``sort_keys`` beim Serialisieren, Dateien über ihren Inhalt statt über Pfad und mtime.

Abhängigkeiten: keine. Reine stdlib — dieselbe Zusage wie in ``contracts.py``, und aus
demselben Grund: Der Kern muss überall prüfbar sein, auch ohne GPU, Netz und Blender.
"""
from __future__ import annotations

import copy
import hashlib
import heapq
import json
import os
import re
import tempfile
from collections import deque
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType

#: Kennung des serialisierten Graph-Formats. Wandert mit, damit ein später geändertes
#: Format nicht stillschweigend als altes gelesen wird.
GRAPH_SCHEMA_ID = "aiimaging.graph/v1"

#: Kennung des Hash-Verfahrens. Fliesst in **jeden** Inhalts-Hash ein: Ändert sich die
#: Berechnung, ändern sich alle Hashes, und alte Cache-Einträge werden nicht mehr als
#: Treffer gelesen. Ohne diese Kennung würde ein geändertes Verfahren alte Artefakte
#: still als gültig ausgeben — der teuerste Fehler, den ein Cache machen kann.
HASH_SCHEMA_ID = "aiimaging.inhalts-hash/v1"

#: Erlaubte Gestalt eines Cache-Schlüssels. Der Schlüssel wird zum Dateinamen, also darf
#: er weder Pfadtrenner noch ``..`` enthalten — sonst schriebe ``lege_ab`` ausserhalb der
#: Cache-Wurzel.
_SCHLUESSEL_MUSTER = re.compile(r"[0-9a-zA-Z][0-9a-zA-Z_.-]{0,127}")

#: Lesepuffer beim Datei-Hashen. glb- und EXR-Dateien sind gross genug, dass sie nicht
#: am Stück in den Speicher gehören.
_BLOCK = 1 << 20

#: Was in den gehashten Parametern anstelle eines Dateipfades steht. Siehe
#: ``inhalts_hash``, Argument ``param_dateien``.
PFAD_MARKE = "<inhalt>"

#: Unter diesem Schlüssel vermerkt ein Cache-Eintrag die Dateien, die er zusagt. Der
#: führende Unterstrich sagt: Das schreibt der Cache selbst, nicht der Aufrufer.
ZUSAGEN_FELD = "_zusagen"


class GraphError(ValueError):
    """Der Graph ist nicht schlüssig gebaut oder wird falsch benutzt.

    Bewusst laut statt stillschweigend repariert — dieselbe Linie wie ``ContractError``.
    Ein Graph, der sich selbst zurechtbiegt, rechnet später etwas anderes als das,
    was jemand aufgeschrieben hat.
    """


class ZyklusError(GraphError):
    """Der Graph enthält einen Kreis und hat damit keine Rechenreihenfolge.

    Erbt von ``GraphError``, weil ein Kreis ein Sonderfall eines unschlüssigen Graphen
    ist: Wer alle Graph-Fehler fangen will, soll nicht zwei Klassen nennen müssen. Wer
    nur den Kreis meint, fängt weiterhin ``ZyklusError``.
    """


@dataclass(frozen=True)
class Knoten:
    """Ein Arbeitsschritt der Bildkette.

    ``frozen``, damit ein Knoten nach dem Hashen nicht unbemerkt verändert werden kann:
    Der Inhalts-Hash entscheidet über Cache-Treffer; eine nachträgliche Änderung an
    ``params`` würde einen fremden Cache-Eintrag als eigenen ausgeben.

    ``frozen`` schützt allerdings nur die Zuweisung, nicht den Inhalt eines dict. Darum
    wird ``params`` beim Anlegen über eine JSON-Runde kopiert **und** geprüft:

    * Der Aufrufer kann sein übergebenes dict danach nicht mehr in den Knoten hinein
      verändern.
    * Was nicht JSON-fähig ist, fällt sofort auf — nicht erst beim Serialisieren oder
      Hashen, wo die Fehlermeldung nichts mehr mit der Ursache zu tun hätte.
    * Was die JSON-Runde nicht verlustfrei übersteht (Tupel, nicht-String-Schlüssel),
      wird abgelehnt statt umgeschrieben. Sonst hiesse ein Rundlauf über ``to_dict`` /
      ``from_dict`` „gleicher Graph“, obwohl sich die Parameter geändert hätten.

    Attribute:
        id: Eindeutig im Graphen. Ein Name, kein Inhalt — er fliesst **nicht** in den
            Inhalts-Hash ein (siehe ``inhalts_hash``).
        art: Was zu tun ist, z.B. ``"ifc_zu_glb"``, ``"tiefenkarte"``, ``"render"``.
            Dieses Modul kennt keine einzige Art; die Zuordnung Art → Code liegt
            bewusst ausserhalb, sonst wüchse hier der Knoten-Zoo.
        params: Knoteneigene Einstellungen, JSON-fähig.
        eingaenge: IDs der Vorgänger. **Die Reihenfolge ist bedeutsam** — ein Knoten mit
            zwei Bildeingängen unterscheidet Vordergrund und Hintergrund über die
            Position. Wiederholungen sind erlaubt (derselbe Vorgänger in zwei Slots).

    Nicht hashbar im Python-Sinn: ``params`` ist ein dict, ``hash(knoten)`` scheitert
    darum. Das ist kein Mangel — Pythons ``hash`` ist zwischen zwei Prozessen nicht
    stabil und für einen Cache ohnehin unbrauchbar. Der stabile Hash ist
    ``inhalts_hash``.
    """

    id: str
    art: str
    params: dict = field(default_factory=dict)
    eingaenge: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for feld, wert in (("id", self.id), ("art", self.art)):
            if not isinstance(wert, str) or not wert.strip():
                raise GraphError(
                    f"Knoten.{feld} muss ein nicht-leerer String sein, war {wert!r}."
                )

        if isinstance(self.eingaenge, (str, bytes)):
            # Ein blosser String ist iterierbar und würde zu einer Kette einzelner
            # Zeichen zerfallen — lautlos, und der Graph hätte danach Eingänge namens
            # "a", "b", "c". Genau die Sorte stiller Falschmeldung, gegen die dieses
            # Projekt antritt.
            raise GraphError(
                f"Knoten.eingaenge ist eine Folge von IDs, kein einzelner String: "
                f"{self.eingaenge!r}. Gemeint war vermutlich ({self.eingaenge!r},)."
            )
        try:
            eingaenge = tuple(self.eingaenge)
        except TypeError as fehler:
            raise GraphError(
                f"Knoten.eingaenge ist nicht iterierbar: {self.eingaenge!r}"
            ) from fehler
        for eingang in eingaenge:
            if not isinstance(eingang, str) or not eingang.strip():
                raise GraphError(
                    f"Knoten {self.id!r}: Eingang muss eine Knoten-ID sein, war {eingang!r}."
                )
        object.__setattr__(self, "eingaenge", eingaenge)

        if not isinstance(self.params, dict):
            raise GraphError(
                f"Knoten {self.id!r}: params muss ein dict sein, war "
                f"{type(self.params).__name__}."
            )
        try:
            kopie = json.loads(json.dumps(self.params, sort_keys=True, allow_nan=False))
        except (TypeError, ValueError) as fehler:
            raise GraphError(
                f"Knoten {self.id!r}: params ist nicht JSON-fähig ({fehler}). Pfade "
                f"gehören als str hinein, NaN/Infinity gar nicht — sonst wäre weder der "
                f"Inhalts-Hash noch die Serialisierung möglich."
            ) from fehler
        if kopie != self.params:
            raise GraphError(
                f"Knoten {self.id!r}: params übersteht die JSON-Runde nicht verlustfrei "
                f"(z.B. Tupel statt Liste oder nicht-String-Schlüssel). Wird nicht "
                f"stillschweigend umgeschrieben, weil sonst ein Rundlauf über to_dict/"
                f"from_dict andere Parameter ergäbe als der Knoten im Speicher."
            )
        object.__setattr__(self, "params", kopie)


class Graph:
    """Ein gerichteter, kreisfreier Ablauf aus ``Knoten``.

    Der Konstruktor prüft, was ohne Rechnen prüfbar ist: eindeutige IDs und vorhandene
    Eingänge. Die Kreisfreiheit prüft er **nicht** — sie fällt in
    ``topologische_reihenfolge`` an, wo sie hingehört. Grund: Ein Graph wird auch zum
    Anschauen, Serialisieren und Reparieren gebaut; ein Kreis soll dabei untersuchbar
    bleiben und nicht schon das Anlegen des Objekts verhindern. Gerechnet wird er nie,
    denn jede Ausführung geht über ``topologische_reihenfolge``.
    """

    def __init__(self, knoten: Iterable[Knoten]):
        liste = list(knoten)

        self._knoten: dict[str, Knoten] = {}
        for k in liste:
            if not isinstance(k, Knoten):
                raise GraphError(
                    f"Graph nimmt Knoten-Objekte, bekam {type(k).__name__}. "
                    f"Ein dict wird über Graph.from_dict gelesen."
                )
            if k.id in self._knoten:
                raise GraphError(
                    f"Knoten-ID doppelt vergeben: {k.id!r}. IDs sind die einzige "
                    f"Verdrahtung im Graphen — bei zwei gleichen Namen wäre nicht "
                    f"entscheidbar, welcher Knoten gemeint ist."
                )
            self._knoten[k.id] = k

        # Erst nach dem vollständigen Einlesen prüfen, sonst wäre die Reihenfolge der
        # Aufzählung bedeutsam: Ein Knoten darf einen Vorgänger nennen, der später in
        # der Liste steht.
        for k in liste:
            for eingang in k.eingaenge:
                if eingang not in self._knoten:
                    raise GraphError(
                        f"Knoten {k.id!r} nennt den Eingang {eingang!r}, den es im "
                        f"Graphen nicht gibt. Tippfehler werden hier gemeldet und nicht "
                        f"als wurzelloser Knoten weggerechnet."
                    )

        # Rückwärtsrichtung einmal aufbauen: Sie wird von der topologischen Sortierung
        # und von nachfolger_transitiv gebraucht, beide oft. Sortiert, damit jede
        # Ausgabe reproduzierbar ist. `dict.fromkeys` entfernt Wiederholungen unter
        # Beibehaltung der Reihenfolge — ein Vorgänger, der zweimal in `eingaenge`
        # steht, ist trotzdem nur EINE Kante, sonst käme die Eingangsgradzählung der
        # topologischen Sortierung nie auf null.
        self._nachfolger: dict[str, list[str]] = {kid: [] for kid in self._knoten}
        for k in liste:
            for eingang in dict.fromkeys(k.eingaenge):
                self._nachfolger[eingang].append(k.id)
        for liste_nachfolger in self._nachfolger.values():
            liste_nachfolger.sort()

    # -- Zugriff -----------------------------------------------------------------------

    @property
    def knoten(self) -> MappingProxyType:
        """Die Knoten nach ID, schreibgeschützt.

        Ein ``MappingProxyType`` statt des dict selbst: Wer einen Knoten nachträglich
        einhängt, umginge sämtliche Prüfungen des Konstruktors.
        """
        return MappingProxyType(self._knoten)

    def __contains__(self, id: str) -> bool:
        return id in self._knoten

    def __len__(self) -> int:
        return len(self._knoten)

    def __eq__(self, other: object) -> bool:
        """Zwei Graphen sind gleich, wenn sie dieselben Knoten tragen.

        Gebraucht für den Rundlauf ``to_dict`` → ``from_dict``: „derselbe Graph“ soll
        eine Zusicherung sein, die man hinschreiben kann. Die Aufzählungsreihenfolge
        zählt dabei nicht mit — sie ist Darstellung, nicht Inhalt; die Rechenreihenfolge
        kommt aus ``topologische_reihenfolge``.
        """
        if not isinstance(other, Graph):
            return NotImplemented
        return self._knoten == other._knoten

    __hash__ = None   # veränderliche params im Knoten; siehe Knoten-Docstring

    def __repr__(self) -> str:
        return f"Graph({len(self._knoten)} Knoten: {', '.join(sorted(self._knoten))})"

    def _pruefe_bekannt(self, id: str) -> None:
        if id not in self._knoten:
            raise GraphError(
                f"Unbekannte Knoten-ID {id!r}. Bekannt: {sorted(self._knoten) or '—'}"
            )

    # -- Ablauf ------------------------------------------------------------------------

    def topologische_reihenfolge(self) -> list[str]:
        """Rechenreihenfolge: jeder Knoten nach allen seinen Vorgängern.

        Verfahren nach Kahn: wiederholt einen Knoten ohne offene Vorgänger entnehmen.
        Unter den gleichrangigen Knoten wird **immer der kleinste ID-Name zuerst**
        gewählt (Halde statt Menge). Das ist der Unterschied zwischen einem Lauf, den
        man wiederholen kann, und einem, den man nur beschreiben kann: Ohne feste Wahl
        hinge die Reihenfolge an Einfügereihenfolge und Hash-Zufall, und zwei Läufe
        derselben Datei ergäben verschiedene Protokolle, Log-Zeilen und
        Fehlerreihenfolgen.

        Raises:
            ZyklusError: Der Graph enthält einen Kreis — auch eine Selbstkante
                (ein Knoten, der sich selbst als Eingang nennt) ist einer.
        """
        offen = {kid: len(set(k.eingaenge)) for kid, k in self._knoten.items()}
        bereit = [kid for kid, grad in offen.items() if grad == 0]
        heapq.heapify(bereit)

        reihenfolge: list[str] = []
        while bereit:
            kid = heapq.heappop(bereit)
            reihenfolge.append(kid)
            for nachfolger in self._nachfolger[kid]:
                offen[nachfolger] -= 1
                if offen[nachfolger] == 0:
                    heapq.heappush(bereit, nachfolger)

        if len(reihenfolge) != len(self._knoten):
            # Was übrig bleibt, liegt auf oder hinter dem Kreis. Beides nennen wäre
            # genauer, aber die Menge selbst ist der brauchbare Hinweis für die Suche.
            rest = sorted(set(self._knoten) - set(reihenfolge))
            raise ZyklusError(
                f"Kreis im Graphen: {rest} haben keine Reihenfolge. Betroffen sind die "
                f"Knoten auf dem Kreis und alles dahinter."
            )
        return reihenfolge

    def vorgaenger(self, id: str) -> list[str]:
        """Die direkten Vorgänger eines Knotens, **in der Reihenfolge seiner Eingänge**.

        Nicht sortiert und nicht entdoppelt: Die Position ist Bedeutung (Slot 0, Slot 1),
        und derselbe Vorgänger darf in zwei Slots stehen. Wer die Menge braucht, bildet
        selbst ein ``set``.
        """
        self._pruefe_bekannt(id)
        return list(self._knoten[id].eingaenge)

    def nachfolger_transitiv(self, ids: Iterable[str]) -> set[str]:
        """Alles, was von ``ids`` abhängt — direkt oder über Zwischenschritte.

        Zweck ist das Überspringen nach einem Fehler (skip-on-error): Scheitert ein
        Knoten, ist jedes Ergebnis flussabwärts entweder unmöglich oder wertlos. Es
        trotzdem zu rechnen kostet Zeit und erzeugt schlimmstenfalls ein Bild, das
        plausibel aussieht und auf halber Eingabe beruht.

        Die übergebenen IDs selbst sind **nicht** enthalten: Der gescheiterte Knoten
        gilt als gescheitert, nicht als übersprungen — die beiden Zustände in einem
        Protokoll zu vermischen, verschleiert die Ursache. Nur wenn ein Kreis einen
        Startknoten tatsächlich zu seinem eigenen Nachfolger macht, taucht er auf; das
        ist dann eine wahre Aussage über einen kaputten Graphen.

        Raises:
            GraphError: eine der IDs gibt es nicht.
        """
        if isinstance(ids, (str, bytes)):
            raise GraphError(
                f"nachfolger_transitiv nimmt eine Folge von IDs, kein einzelnes "
                f"{type(ids).__name__}: {ids!r}. Gemeint war vermutlich [{ids!r}]."
            )
        start = list(ids)
        for kid in start:
            self._pruefe_bekannt(kid)

        getroffen: set[str] = set()
        rand = deque()
        for kid in start:
            rand.extend(self._nachfolger[kid])
        while rand:
            kid = rand.popleft()
            if kid in getroffen:
                continue
            getroffen.add(kid)
            rand.extend(self._nachfolger[kid])
        return getroffen

    # -- Serialisierung ----------------------------------------------------------------

    def to_dict(self) -> dict:
        """Der Graph als JSON-fähiges dict.

        Die Knoten stehen in der Reihenfolge, in der sie angelegt wurden — nicht
        sortiert. Eine von Hand geschriebene Kette bleibt so lesbar, wie sie geschrieben
        wurde; für das Rechnen ist die Reihenfolge ohnehin ohne Belang.

        ``params`` wird kopiert: Sonst könnte der Aufrufer über das zurückgegebene dict
        in den ``frozen`` Knoten hineingreifen.
        """
        return {
            "schema": GRAPH_SCHEMA_ID,
            "knoten": [
                {
                    "id": k.id,
                    "art": k.art,
                    "params": copy.deepcopy(k.params),
                    "eingaenge": list(k.eingaenge),
                }
                for k in self._knoten.values()
            ],
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Graph":
        """Graph aus einem dict lesen — mit denselben Prüfungen wie der Konstruktor.

        Streng, und zwar an drei Stellen:

        * Die ``schema``-Kennung muss stimmen. Ein Format aus einer anderen Version
          würde sonst irgendwie gelesen und irgendetwas rechnen.
        * Unbekannte Schlüssel in einem Knoten werden abgelehnt. Ein ``"eingang"`` statt
          ``"eingaenge"`` ergäbe sonst lautlos einen wurzellosen Knoten, der zuerst
          gerechnet wird — ein Fehler, der als vertauschte Reihenfolge auffällt und
          nicht als Tippfehler. (Für **MCP-Eingabeschemas** gilt das Gegenteil, siehe
          ``PLAN.md``: dort ist ``additionalProperties: false`` ausdrücklich unerwünscht,
          weil dort ein fremdes System schreibt. Hier schreiben wir selbst.)
        * ``eingaenge`` muss eine Liste sein, nicht irgendetwas Iterierbares.

        Raises:
            GraphError: bei jedem Verstoss.
        """
        if not isinstance(d, dict):
            raise GraphError(f"Graph-Beschreibung muss ein Objekt sein, war {type(d).__name__}.")

        schema = d.get("schema")
        if schema != GRAPH_SCHEMA_ID:
            raise GraphError(
                f"Unbekanntes Graph-Format {schema!r}, erwartet {GRAPH_SCHEMA_ID!r}."
            )

        roh = d.get("knoten")
        if not isinstance(roh, list):
            raise GraphError("Feld 'knoten' fehlt oder ist keine Liste.")

        erlaubt = {"id", "art", "params", "eingaenge"}
        knoten = []
        for eintrag in roh:
            if not isinstance(eintrag, dict):
                raise GraphError(f"Knoten muss ein Objekt sein, war {type(eintrag).__name__}.")
            unbekannt = sorted(set(eintrag) - erlaubt)
            if unbekannt:
                raise GraphError(
                    f"Knoten {eintrag.get('id')!r} trägt unbekannte Felder {unbekannt}. "
                    f"Erlaubt: {sorted(erlaubt)}. Ein Tippfehler soll auffallen, statt "
                    f"als fehlende Verdrahtung durchzulaufen."
                )
            eingaenge = eintrag.get("eingaenge", [])
            if not isinstance(eingaenge, list):
                raise GraphError(
                    f"Knoten {eintrag.get('id')!r}: 'eingaenge' muss eine Liste sein, war "
                    f"{type(eingaenge).__name__}."
                )
            knoten.append(Knoten(
                id=eintrag.get("id"),
                art=eintrag.get("art"),
                params=eintrag.get("params", {}),
                eingaenge=tuple(eingaenge),
            ))
        return cls(knoten)


# --------------------------------------------------------------------------------------
# Bedarf — was eine Knotenart braucht und was sie zusagt
# --------------------------------------------------------------------------------------
#
# Warum es diesen Begriff gibt, und warum erst jetzt
# --------------------------------------------------
# Ein Knoten wusste bis hierher nicht, was er *braucht*. Zwei Folgen, beide gemessen:
#
# 1. Es gab keine Entwurfszeit-Prüfung. KosmoOrbit hat dafür `pipelineReadiness`: Es
#    meldet tote Kanten und fehlende Pflichtfelder, **bevor** irgendetwas läuft
#    (`docs/EINBINDUNG_KOSMOORBIT_2026-08-14.md`, Kap. 2/3). Für die äussere Naht ist
#    dieselbe Prüfung in `mcp_schemas.pruefe_verdrahtbarkeit` nachgebaut; im inneren
#    Graphen fehlte sie. Ein falsch verdrahteter Graph fiel erst auf, nachdem Blender
#    und GPU gelaufen waren.
# 2. Der Cache kannte die Dateien nicht, die er zusagt. Sitzung 07 hat den Preis dafür
#    bezahlt: Ein Multipass-Knoten galt als `ok`, obwohl seine normalisierte Tiefenkarte
#    `None` war, wanderte in den Zwischenspeicher — und wurde nie wieder gerechnet, auch
#    nicht, nachdem die Ursache behoben war. Drei Läufe, ein einziger Blender-Start.
#
# Beides ist dieselbe fehlende Angabe, darum steht hier **eine** Deklaration.
#
# Warum je Knotenart und nicht je Knoten: Was ein Knoten braucht, hängt an dem, was er
# tut, nicht an seinem Namen. Ein zusätzliches Feld im `Knoten` wäre ausserdem
# hash-relevant geworden — zwei gleich eingestellte Knoten mit verschieden geschriebener
# Deklaration dürften sich sonst keinen Cache-Eintrag mehr teilen.


def _ist_leer(wert) -> bool:
    """Zählt ein Wert als „nicht geliefert“?

    ``None`` und leere Behälter ja; ``False`` und ``0`` **nein**. Das ist kein Detail:
    Die QA gibt ``bestanden=False`` zurück, und ein durchgefallenes Urteil ist ein
    Ergebnis und kein fehlendes Feld — genau die Unterscheidung, die
    ``kette.qa_ausfuehrer`` im Docstring festhält.
    """
    if wert is None:
        return True
    if isinstance(wert, (str, bytes, list, tuple, dict, set, frozenset)):
        return len(wert) == 0
    return False


def _feldnamen(namen, wo: str) -> tuple[str, ...]:
    """Eine Folge von Feldnamen einlesen — und einen einzelnen String ablehnen.

    Dieselbe Falle wie bei ``Knoten.eingaenge``: Ein blosser String ist iterierbar und
    zerfiele lautlos in einzelne Zeichen.
    """
    if isinstance(namen, (str, bytes)):
        raise GraphError(
            f"{wo} ist eine Folge von Feldnamen, kein einzelner String: {namen!r}. "
            f"Gemeint war vermutlich ({namen!r},)."
        )
    try:
        werte = tuple(namen)
    except TypeError as fehler:
        raise GraphError(f"{wo} ist nicht iterierbar: {namen!r}") from fehler
    for wert in werte:
        if not isinstance(wert, str) or not wert.strip():
            raise GraphError(f"{wo}: Feldname muss ein nicht-leerer String sein, war {wert!r}.")
    return werte


@dataclass(frozen=True)
class Bedarf:
    """Was eine Knotenart von ihren Vorgängern braucht und was sie selbst zusagt.

    Attribute:
        braucht: **Je Eingangsslot** die Feldnamen, die dort erwartet werden. Eine Folge
            von Folgen, weil die Eingänge im inneren Graphen nach Position unterschieden
            werden und nicht verschmolzen wie in KosmoOrbits ``mergeInputs``: Slot 0 der
            QA ist das Soll, Slot 1 das Ist. Ein flaches ``required`` wie im äusseren
            Vertrag könnte das nicht ausdrücken.
        liefert: Felder, die ein **gelungener** Lauf dieser Art immer trägt. Sie sind die
            Pflichtseite: Ist eines davon leer, ist das Ergebnis unbrauchbar, egal was
            der ``status`` behauptet.
        dateien: Felder, deren Wert ein Dateipfad ist. Sie werden geprüft, **wenn** sie
            gesetzt sind — ein Feld darf hier stehen und trotzdem wahlweise sein (der
            Beauty-Pass lässt sich abschalten). Wer eine Datei zur Pflicht machen will,
            nennt sie zusätzlich in ``liefert``.

    ``dateien`` wird ausdrücklich **aufgezählt** statt an der Endung des Feldnamens
    erraten. Das Erraten gibt es weiterhin als zweites Netz in ``kette``, aber es war
    genau die Stelle, an der der vergiftete Eintrag durchschlüpfte: ``depth_png`` war
    ``None``, und ein ``None`` sieht keiner Endung ähnlich.
    """

    braucht: tuple[tuple[str, ...], ...] = ()
    liefert: tuple[str, ...] = ()
    dateien: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        slots = []
        if isinstance(self.braucht, (str, bytes)):
            raise GraphError(
                f"Bedarf.braucht ist eine Folge **je Slot**, kein einzelner String: "
                f"{self.braucht!r}. Gemeint war vermutlich (({self.braucht!r},),)."
            )
        for slot in self.braucht:
            slots.append(_feldnamen(slot, "Bedarf.braucht[i]"))
        object.__setattr__(self, "braucht", tuple(slots))
        object.__setattr__(self, "liefert", _feldnamen(self.liefert, "Bedarf.liefert"))
        object.__setattr__(self, "dateien", _feldnamen(self.dateien, "Bedarf.dateien"))

    def zugesagte_dateien(self, ausgaben) -> list[str]:
        """Die Dateien, die diese Ausgabe verspricht — für ``ArtefaktCache.lege_ab``.

        In der Reihenfolge von ``dateien``, ohne die nicht gesetzten. Nicht gesetzt heisst
        nicht zugesagt; ob das erlaubt ist, entscheidet ``liefert`` und nicht diese Liste.
        """
        pfade = []
        for feld in self.dateien:
            wert = ausgaben.get(feld) if hasattr(ausgaben, "get") else None
            if isinstance(wert, str) and wert:
                pfade.append(wert)
        return pfade

    def maengel(self, ausgaben) -> list[str]:
        """Was an dieser Ausgabe die Zusage bricht. **Leer heisst brauchbar.**

        Zwei Sorten Mangel, und die erste ist die, die Sitzung 07 gekostet hat:

        * ein Pflichtfeld aus ``liefert`` fehlt oder ist leer,
        * eine Datei aus ``dateien`` ist genannt, liegt aber nicht mehr da.

        Gedacht als **Verwerfungs**-Bedingung für einen Cache-Treffer. Umgekehrt gilt
        weiter, was dieses Projekt mehrfach bezahlt hat: Die Existenz einer Datei ist kein
        Beleg für ihren Inhalt. Der Beleg für den Inhalt kommt aus dem Hash.
        """
        if not hasattr(ausgaben, "get"):
            return [f"Ausgaben sind kein Objekt, sondern {type(ausgaben).__name__}."]
        maengel: list[str] = []
        for feld in self.liefert:
            if _ist_leer(ausgaben.get(feld)):
                maengel.append(
                    f"Pflichtfeld {feld!r} fehlt oder ist leer "
                    f"({ausgaben.get(feld)!r}) — die Art sagt es zu."
                )
        for feld in self.dateien:
            wert = ausgaben.get(feld)
            if _ist_leer(wert):
                continue
            if not isinstance(wert, str):
                maengel.append(f"Feld {feld!r} sollte ein Dateipfad sein, war {wert!r}.")
            elif not Path(wert).exists():
                maengel.append(f"Zugesagte Datei fehlt: {feld}={wert!r}.")
        return maengel


def pruefe_bedarf(graph: Graph, bedarf) -> list[dict]:
    """Prüft einen Graphen **ohne ihn auszuführen** und meldet, was nicht zusammenpasst.

    Das Gegenstück zu KosmoOrbits ``pipelineReadiness`` für den inneren Graphen, gebaut
    nach demselben Muster wie ``mcp_schemas.pruefe_verdrahtbarkeit`` für die äussere Naht.
    Der Zweck ist die Reihenfolge: Ein Graph, dessen Verdrahtung nicht trägt, soll das
    sagen, bevor Blender startet und die GPU eine Stunde rechnet — nicht danach.

    Args:
        graph: der zu prüfende Graph.
        bedarf: Abbildung Knotenart → ``Bedarf``. Arten, die nicht darin stehen, sind
            nicht prüfbar und werden als ``warn`` gemeldet statt stillschweigend für
            richtig gehalten.

    Returns:
        Liste von Befunden ``{knoten, art, befund, schwere, detail}``, nach Knoten-ID
        sortiert. **Leer heisst verdrahtet.** ``schwere`` ist ``"error"`` (der Lauf kann
        so nicht gelingen) oder ``"warn"`` (auffällig, aber kein Beweis).

    Befundarten:

    * ``fehlender-eingang`` — der Knoten erwartet einen Slot, den es nicht gibt. Der
      Fall der QA mit nur einem Vorgänger: Sie hätte kein Ist zum Vergleichen.
    * ``fehlendes-feld`` — der Vorgänger an diesem Slot sagt das erwartete Feld nicht zu.
      Das ist die tote Kante des inneren Graphen: Sie existiert, trägt aber nichts.
    * ``unbenutzter-eingang`` — ein Eingang, für den keine Erwartung deklariert ist. Nur
      ``warn``: Eine Kante darf auch bloss eine Reihenfolge erzwingen.
    * ``unbekannte-art`` — für diese Art gibt es keine Deklaration, also ist an ihr und
      an den Kanten in sie hinein nichts prüfbar.

    Der Graph wird **nicht** topologisch sortiert: Auch ein Graph mit Kreis soll sich
    prüfen lassen, sonst verdeckte der eine Fehler den anderen. Die Ausgabe ist nach
    Knoten-ID sortiert und damit zwischen zwei Läufen gleich.
    """
    if not isinstance(graph, Graph):
        raise GraphError(f"pruefe_bedarf erwartet einen Graph, bekam {type(graph).__name__}.")
    if not hasattr(bedarf, "get"):
        raise GraphError(
            f"pruefe_bedarf erwartet eine Abbildung Knotenart → Bedarf, bekam "
            f"{type(bedarf).__name__}."
        )

    befunde: list[dict] = []
    for kid in sorted(graph.knoten):
        knoten = graph.knoten[kid]
        eigen = bedarf.get(knoten.art)
        if eigen is None:
            befunde.append({
                "knoten": kid, "art": knoten.art, "befund": "unbekannte-art",
                "schwere": "warn",
                "detail": (f"Für die Art {knoten.art!r} ist kein Bedarf deklariert — was "
                           f"dieser Knoten braucht, ist nicht prüfbar."),
            })
            continue
        if not isinstance(eigen, Bedarf):
            raise GraphError(
                f"Bedarf für die Art {knoten.art!r} ist kein Bedarf-Objekt, sondern "
                f"{type(eigen).__name__}."
            )

        for slot, felder in enumerate(eigen.braucht):
            if slot >= len(knoten.eingaenge):
                befunde.append({
                    "knoten": kid, "art": knoten.art, "befund": "fehlender-eingang",
                    "schwere": "error",
                    "detail": (f"Slot {slot} fehlt: Der Knoten erwartet dort "
                               f"{', '.join(felder) or '—'}, hat aber nur "
                               f"{len(knoten.eingaenge)} Eingang/Eingänge."),
                })
                continue
            vorgaenger = knoten.eingaenge[slot]
            liefernd = bedarf.get(graph.knoten[vorgaenger].art)
            if liefernd is None:
                continue          # schon als unbekannte-art gemeldet, wenn er drankommt
            for feld in felder:
                if feld not in liefernd.liefert:
                    befunde.append({
                        "knoten": kid, "art": knoten.art, "befund": "fehlendes-feld",
                        "schwere": "error",
                        "detail": (f"Slot {slot} ({vorgaenger!r}, Art "
                                   f"{graph.knoten[vorgaenger].art!r}) sagt {feld!r} nicht "
                                   f"zu. Zugesagt: {', '.join(liefernd.liefert) or '—'}."),
                    })

        for slot in range(len(eigen.braucht), len(knoten.eingaenge)):
            befunde.append({
                "knoten": kid, "art": knoten.art, "befund": "unbenutzter-eingang",
                "schwere": "warn",
                "detail": (f"Slot {slot} ({knoten.eingaenge[slot]!r}) ist verdrahtet, aber "
                           f"die Art {knoten.art!r} erwartet dort nichts."),
            })
    return befunde


# --------------------------------------------------------------------------------------
# Inhalts-Hash
# --------------------------------------------------------------------------------------

def _datei_hash(pfad: str | Path) -> str:
    """sha256 über den **Inhalt** einer Datei, blockweise gelesen.

    Blockweise, weil hier glb- und EXR-Dateien durchlaufen; ``read()`` am Stück wäre bei
    einer grösseren Szene ein Speicherproblem ohne Not.
    """
    p = Path(pfad)
    if not p.exists():
        raise GraphError(
            f"Datei für den Inhalts-Hash fehlt: {p}. Wird nicht als leer behandelt — ein "
            f"fehlendes Eingangsartefakt ergäbe sonst denselben Hash wie ein leeres und "
            f"damit einen falschen Cache-Treffer."
        )
    if p.is_dir():
        raise GraphError(f"Für den Inhalts-Hash wird eine Datei erwartet, {p} ist ein Verzeichnis.")

    hasher = hashlib.sha256()
    with p.open("rb") as datei:
        while (block := datei.read(_BLOCK)):
            hasher.update(block)
    return hasher.hexdigest()


def inhalts_hash(
    knoten: Knoten,
    vorgaenger_hashes: Sequence[str],
    dateien: Sequence[str | Path] = (),
    *,
    param_dateien: Sequence[str] = (),
) -> str:
    """Stabiler Hash aus Knotenart, Parametern, Vorgänger-Hashes und Dateiinhalten.

    Der Hash ist der Schlüssel des Artefakt-Caches. Er muss deshalb genau eine Frage
    beantworten: *Würde dieselbe Rechnung dasselbe Ergebnis liefern?*

    Was einfliesst — und warum:

    * ``art`` und ``params`` — was gerechnet wird. Die Parameter gehen über
      ``json.dumps(..., sort_keys=True)`` ein: Ohne ``sort_keys`` hinge der Hash an der
      Einfügereihenfolge des dict, und ein von Hand umsortiertes JSON verwürfe den ganzen
      Cache, obwohl sich nichts geändert hat.
    * ``vorgaenger_hashes`` in der übergebenen Reihenfolge — was hineinfliesst. Die
      Reihenfolge zählt mit, weil sie beim Knoten bedeutsam ist (Slot 0 ≠ Slot 1).
    * ``dateien`` über ihren **Inhalt** (sha256), nicht über Pfad oder mtime. Eine
      umbenannte oder kopierte, inhaltlich gleiche Datei ergibt denselben Hash; ein bloss
      neu geschriebenes, gleiches File erzwingt keine Neuberechnung. Über mtime zu gehen
      wäre bequemer und in einer Kette aus Subprozessen fast immer falsch.
    * ``HASH_SCHEMA_ID`` — damit ein geändertes Verfahren alte Einträge nicht
      weiterverwendet.

    Was **nicht** einfliesst:

    * ``knoten.id`` — der Name. Zwei gleich eingestellte Knoten in verschiedenen Graphen
      sollen sich einen Cache-Eintrag teilen; ein umbenannter Knoten soll nicht neu
      rechnen.
    * ``knoten.eingaenge`` — ebenfalls Namen. Was von dort kommt, steckt bereits in
      ``vorgaenger_hashes``.

    Die Ausnahmeliste ``param_dateien``
    -----------------------------------
    Ein Parameter, der einen **Dateipfad** trägt, ist ein Sonderfall: Sein Wert soll
    nicht mitzählen, sein Inhalt schon. Ohne diese Liste hinge der Schlüssel am
    Dateinamen, und ein blosses Verschieben des Projektordners verwürfe den ganzen
    Zwischenspeicher, obwohl sich an der Geometrie nichts geändert hat. Die Kette hat
    sich das bis Sitzung 07 mit einer eigenen Hashvorbereitung selbst gebaut; hier
    gehört es hin.

    ``param_dateien`` nennt die Parameternamen. Für jeden, der gesetzt ist, wird der
    **Inhalt** der Datei gehasht (angehängt hinter ``dateien``, in der genannten
    Reihenfolge), und im Parameter steht stattdessen ``PFAD_MARKE``.

    **Ersetzt, nicht gelöscht.** Der Name des Feldes trägt sehr wohl Bedeutung —
    ``ifc_path`` heisst „konvertiere“, ``glb_path`` heisst „reiche durch“. Würde der
    Schlüssel ganz entfernt, ergäben dieselben Bytes einmal als IFC und einmal als glb
    denselben Hash und damit einen falschen Treffer.

    Welche Parameter Pfade sind, weiss dieses Modul weiterhin nicht — es bekommt die
    Liste gesagt. Der Knoten-Zoo bleibt draussen.

    Raises:
        GraphError: Argumente falscher Gestalt oder eine fehlende Datei.
    """
    if not isinstance(knoten, Knoten):
        raise GraphError(f"inhalts_hash erwartet einen Knoten, bekam {type(knoten).__name__}.")

    if isinstance(vorgaenger_hashes, (str, bytes)):
        raise GraphError(
            f"vorgaenger_hashes ist eine Folge von Hashes, kein einzelner String: "
            f"{vorgaenger_hashes!r}"
        )
    vorgaenger = list(vorgaenger_hashes)
    for h in vorgaenger:
        if not isinstance(h, str) or not h:
            raise GraphError(f"Vorgänger-Hash muss ein nicht-leerer String sein, war {h!r}.")

    if isinstance(dateien, (str, os.PathLike, bytes)):
        raise GraphError(
            f"dateien ist eine Folge von Pfaden, kein einzelner Pfad: {dateien!r}. "
            f"Gemeint war vermutlich [{dateien!r}]."
        )

    felder = _feldnamen(param_dateien, "param_dateien")
    gesetzt = [feld for feld in felder if knoten.params.get(feld)]
    params = knoten.params
    if gesetzt:
        for feld in gesetzt:
            if not isinstance(knoten.params[feld], (str, os.PathLike)):
                raise GraphError(
                    f"param_dateien nennt {feld!r}, dort steht aber kein Pfad, sondern "
                    f"{knoten.params[feld]!r}."
                )
        params = {**knoten.params, **{feld: PFAD_MARKE for feld in gesetzt}}

    rumpf = {
        "verfahren": HASH_SCHEMA_ID,
        "art": knoten.art,
        "params": params,
        "vorgaenger": vorgaenger,
        "dateien": [_datei_hash(p) for p in list(dateien) + [knoten.params[f] for f in gesetzt]],
    }
    # `separators` und `ensure_ascii`: feste, von den Vorgabewerten unabhängige
    # Textform. `sort_keys` wirkt rekursiv, auch auf verschachtelte params.
    text = json.dumps(
        rumpf, sort_keys=True, ensure_ascii=True, allow_nan=False, separators=(",", ":")
    )
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# --------------------------------------------------------------------------------------
# Artefakt-Cache
# --------------------------------------------------------------------------------------

class ArtefaktCache:
    """Ergebnisse unter ihrem Inhalts-Hash ablegen und wiederfinden.

    Gespeichert wird nicht das Bild, sondern der **Bericht** eines Knotens: ein dict mit
    Pfaden, Massen und Kennzahlen, wie ihn die Runner in ``seams.py`` schon heute
    zurückgeben. Die schweren Dateien bleiben, wo sie entstanden sind — sie hier
    hineinzukopieren würde einen zweiten Ort der Wahrheit schaffen.

    Ein Eintrag ist eine JSON-Datei ``<wurzel>/<schluessel>.json``. Flach, ohne
    Unterverzeichnisse: Ein Prototyp mit ein paar tausend Einträgen braucht keine
    Verzweigung, und ein Verzeichnis, dessen Inhalt man auflisten kann, ist bei der
    Fehlersuche mehr wert als eine gesparte Zeile Code.
    """

    def __init__(self, wurzel: str | Path):
        self.wurzel = Path(wurzel)
        self.wurzel.mkdir(parents=True, exist_ok=True)

    def __repr__(self) -> str:
        return f"ArtefaktCache({str(self.wurzel)!r})"

    def _pfad(self, schluessel: str) -> Path:
        """Schlüssel → Dateipfad, mit Prüfung.

        Der Schlüssel wird zum Dateinamen. Ohne Prüfung schriebe ein Schlüssel wie
        ``"../../etc/x"`` ausserhalb der Cache-Wurzel — ein Cache darf nur seinen
        eigenen Ordner anfassen.
        """
        if not isinstance(schluessel, str) or not _SCHLUESSEL_MUSTER.fullmatch(schluessel):
            raise GraphError(
                f"Unzulässiger Cache-Schlüssel {schluessel!r}. Erlaubt sind 1–128 "
                f"Zeichen aus [A-Za-z0-9._-], beginnend alphanumerisch — der Schlüssel "
                f"wird zum Dateinamen und darf die Cache-Wurzel nicht verlassen."
            )
        return self.wurzel / f"{schluessel}.json"

    def hat(self, schluessel: str) -> bool:
        """Gibt es zu diesem Schlüssel einen Eintrag?

        Nur eine Existenzprüfung, ohne Lesen. Zwischen ``hat`` und ``hole`` kann der
        Eintrag verschwinden; wer das Ergebnis wirklich braucht, ruft direkt ``hole``
        und prüft auf ``None``.
        """
        return self._pfad(schluessel).is_file()

    def hole(self, schluessel: str) -> dict | None:
        """Eintrag lesen, oder ``None`` bei Fehltreffer.

        Ein Fehltreffer ist der Normalfall und darum kein Fehler. Ein **unlesbarer**
        Eintrag dagegen schon: Weil ``lege_ab`` atomar schreibt, kann es keine halb
        geschriebene Datei geben — kaputtes JSON heisst also, dass etwas anderes in den
        Cache geschrieben hat. Das wird gemeldet und nicht als Fehltreffer verkleidet.

        **Ein Eintrag, dessen zugesagte Datei fehlt, ist kein Treffer.** Was ``lege_ab``
        unter ``zusagen`` bekommen hat, wird hier geprüft; fehlt eine der Dateien, gibt
        es ``None`` wie bei einem Fehltreffer, und der Aufrufer rechnet neu. Der Eintrag
        selbst bleibt liegen — er wird beim nächsten Ablegen überschrieben, und ein
        Cache, der beim Lesen löscht, wäre bei zwei gleichzeitigen Läufen ein Rennen.

        Der Grund ist gemessen: Ein Eintrag zeigt auf Dateien, die ausserhalb des Caches
        liegen (bewusst — sonst gäbe es zwei Orte der Wahrheit). Ein aufgeräumtes
        ``/tmp`` genügt, und die Zusage geht ins Leere.
        """
        pfad = self._pfad(schluessel)
        if not pfad.is_file():
            return None
        try:
            eintrag = json.loads(pfad.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as fehler:
            raise GraphError(
                f"Cache-Eintrag {pfad} ist unlesbar ({fehler}). lege_ab schreibt atomar, "
                f"eine halbe Datei kann hier nicht entstehen — der Eintrag stammt also "
                f"nicht von uns. Löschen oder leere() aufrufen."
            ) from fehler
        if isinstance(eintrag, dict):
            for datei in eintrag.get(ZUSAGEN_FELD) or ():
                if not isinstance(datei, str) or not Path(datei).exists():
                    return None
        return eintrag

    def lege_ab(self, schluessel: str, ergebnis: dict,
                *, zusagen: Sequence[str | Path] = ()) -> Path:
        """Ergebnis ablegen und den Pfad des Eintrags zurückgeben.

        **Atomar**, in zwei Schritten: erst eine temporäre Datei im selben Verzeichnis,
        dann ``os.replace``. ``os.replace`` ist auf einem Dateisystem unteilbar — es gibt
        den Eintrag entweder ganz oder gar nicht. Direkt an den Zielort zu schreiben
        hiesse: Ein abgebrochener Lauf (Strom weg, Ctrl-C, OOM beim Rendern) hinterlässt
        eine halbe Datei, die beim nächsten Lauf als gültiger Treffer gilt. Ein Cache,
        der falsche Treffer liefert, ist schlimmer als keiner — der Fehler taucht erst
        im fertigen Bild auf.

        Die temporäre Datei liegt bewusst **im selben Verzeichnis**: ``os.replace`` über
        eine Dateisystemgrenze hinweg scheitert, und ``/tmp`` liegt oft auf einem anderen.

        Serialisiert wird **vor** dem Anlegen der temporären Datei. Sonst bliebe bei
        einem nicht JSON-fähigen Ergebnis ein Rest liegen.

        Args:
            zusagen: Die Dateien, die dieser Eintrag verspricht. Sie werden im Eintrag
                unter ``ZUSAGEN_FELD`` vermerkt, und ``hole`` prüft sie bei jedem
                Zugriff. Ohne diesen Vermerk weiss ein Eintrag nicht, wovon er redet: Er
                speichert Pfade, nicht Bilder, und ein Pfad allein ist eine Behauptung.
                Leer heisst „verspricht keine Datei“ — dann bleibt der Eintrag so, wie er
                übergeben wurde.
        """
        if not isinstance(ergebnis, dict):
            raise GraphError(
                f"Cache speichert Knoten-Berichte als Objekt, bekam "
                f"{type(ergebnis).__name__}."
            )
        if isinstance(zusagen, (str, os.PathLike, bytes)):
            raise GraphError(
                f"zusagen ist eine Folge von Pfaden, kein einzelner Pfad: {zusagen!r}. "
                f"Gemeint war vermutlich [{zusagen!r}]."
            )
        versprochen = [str(p) for p in zusagen]
        if versprochen:
            ergebnis = {**ergebnis, ZUSAGEN_FELD: versprochen}
        ziel = self._pfad(schluessel)
        try:
            text = json.dumps(ergebnis, indent=2, sort_keys=True, ensure_ascii=False,
                              allow_nan=False)
        except (TypeError, ValueError) as fehler:
            raise GraphError(
                f"Ergebnis für {schluessel!r} ist nicht JSON-fähig ({fehler}). Pfade "
                f"gehören als str hinein."
            ) from fehler

        deskriptor, temporaer = tempfile.mkstemp(
            dir=str(self.wurzel), prefix=f".{schluessel}.", suffix=".tmp"
        )
        try:
            with os.fdopen(deskriptor, "w", encoding="utf-8") as datei:
                datei.write(text)
                datei.flush()
                # fsync, bevor umbenannt wird: Ohne das kann das Dateisystem den
                # Namenswechsel vor dem Inhalt festschreiben — nach einem Stromausfall
                # läge dann ein gültig benannter, leerer Eintrag da.
                os.fsync(datei.fileno())
            os.replace(temporaer, ziel)
        except BaseException:
            # Auch bei KeyboardInterrupt aufräumen: Ein liegengebliebenes .tmp ist kein
            # gültiger Eintrag, aber Müll, der sich still ansammelt.
            Path(temporaer).unlink(missing_ok=True)
            raise
        return ziel

    def schluessel(self) -> list[str]:
        """Alle Schlüssel im Cache, sortiert.

        Damit sich überhaupt etwas gezielt verwerfen **lässt**: Wer nur ``hat`` und
        ``hole`` hat, muss den Schlüssel schon kennen. Sortiert, weil jede Ausgabe dieses
        Moduls zwischen zwei Läufen gleich sein soll.
        """
        if not self.wurzel.is_dir():
            return []
        return sorted(p.stem for p in self.wurzel.glob("*.json") if p.is_file())

    def verwirf(self, schluessel: str) -> bool:
        """Einen einzelnen Eintrag löschen. ``True``, wenn es ihn gab.

        Bis Sitzung 07 gab es nur ``leere()`` — und in der Praxis ``rm -rf`` auf dem
        ganzen Ausgabeordner. Das ist die falsche Antwort auf die häufigste Frage: Ein
        Eintrag ist verdächtig (die Umgebung hat gelogen, ein Runner war fehlerhaft), die
        teuren Nachbarn daneben sind es nicht. Wer nur den ganzen Cache wegwerfen kann,
        wirft am Ende die Geometriestufe mit weg, um einen Render zu wiederholen.

        Den Schlüssel liefert ein Lauf selbst mit: ``kette.fuehre_aus`` gibt ihn je Knoten
        im Feld ``hash`` zurück. Verworfen wird damit **genau ein** Knoten; alles davor
        bleibt im Cache, und alles dahinter behält seinen Schlüssel, weil sich am Inhalt
        nichts geändert hat.

        Es wird **nicht** kaskadiert. Ein Nachfolger hängt über seinen Vorgänger-Hash am
        Ergebnis, nicht am Cache-Eintrag: Rechnet der verworfene Knoten dasselbe noch
        einmal, sind die Nachfolger weiterhin gültig — und das ist richtig so. Wer eine
        andere Rechnung will, ändert Parameter oder Eingabe, und dann ändern sich die
        Schlüssel von selbst (siehe ``kette``, Modul-Docstring: es gibt hier keine
        programmierte Invalidierung).
        """
        pfad = self._pfad(schluessel)
        if not pfad.is_file():
            return False
        pfad.unlink()
        return True

    def leere(self) -> int:
        """Alle Einträge löschen; gibt deren Anzahl zurück.

        Fasst nur ``*.json`` in der Wurzel an, keine Unterverzeichnisse und keine
        fremden Dateien: Der Cache räumt seinen eigenen Ordner auf, nicht den Rechner.
        Liegengebliebene ``.tmp``-Dateien werden mitgenommen, aber nicht mitgezählt —
        gezählt werden Einträge, nicht Trümmer.
        """
        if not self.wurzel.is_dir():
            return 0
        anzahl = 0
        for pfad in sorted(self.wurzel.glob("*.json")):
            if pfad.is_file():
                pfad.unlink()
                anzahl += 1
        for rest in self.wurzel.glob(".*.tmp"):
            rest.unlink(missing_ok=True)
        return anzahl


__all__ = [
    "ArtefaktCache",
    "Bedarf",
    "GRAPH_SCHEMA_ID",
    "Graph",
    "GraphError",
    "HASH_SCHEMA_ID",
    "Knoten",
    "PFAD_MARKE",
    "ZUSAGEN_FELD",
    "ZyklusError",
    "inhalts_hash",
    "pruefe_bedarf",
]
