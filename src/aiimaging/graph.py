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

    rumpf = {
        "verfahren": HASH_SCHEMA_ID,
        "art": knoten.art,
        "params": knoten.params,
        "vorgaenger": vorgaenger,
        "dateien": [_datei_hash(p) for p in dateien],
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
        """
        pfad = self._pfad(schluessel)
        if not pfad.is_file():
            return None
        try:
            return json.loads(pfad.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as fehler:
            raise GraphError(
                f"Cache-Eintrag {pfad} ist unlesbar ({fehler}). lege_ab schreibt atomar, "
                f"eine halbe Datei kann hier nicht entstehen — der Eintrag stammt also "
                f"nicht von uns. Löschen oder leere() aufrufen."
            ) from fehler

    def lege_ab(self, schluessel: str, ergebnis: dict) -> Path:
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
        """
        if not isinstance(ergebnis, dict):
            raise GraphError(
                f"Cache speichert Knoten-Berichte als Objekt, bekam "
                f"{type(ergebnis).__name__}."
            )
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
    "GRAPH_SCHEMA_ID",
    "Graph",
    "GraphError",
    "HASH_SCHEMA_ID",
    "Knoten",
    "ZyklusError",
    "inhalts_hash",
]
