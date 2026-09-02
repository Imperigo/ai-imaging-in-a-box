"""MODELLSTAND — liegt dieses Modell hinter seinem eigenen Erzeuger zurück?

Der Anlass
----------
Drei Demoläufe hintereinander (01.–02.09.2026) sind mit einer glb gefahren, die **null
Materialien** trug, obwohl der Export sie seit dem 01.09.2026 schreibt, und mit einem IFC
ohne eine einzige Tür, obwohl der Erzeuger 20/26/151 Türen je Blatt misst. Beides war
gebaut, beides war belegt — und die Kette hat beides nicht bemerkt, weil **nichts prüft,
ob das Modell trägt, was gebaut wurde**. Der Lauf war grün; er hat ein anderes Haus
gezeichnet.

Die Frage, die dieses Modul beantwortet, ist darum nicht «ist diese Geometrie in Ordnung»
(das tut :mod:`aiimaging.torwaechter` an der Hüllbox) und auch nicht «woher kommt sie»
(das tut :mod:`aiimaging.herkunft` am Dateikopf), sondern:

    **Trägt diese Datei, was ihr Erzeuger schreiben kann?**

Die drei Zustände — und warum es drei sind und nicht zwei
----------------------------------------------------------
:data:`TRAEGT`, :data:`ZURUECK`, :data:`UNGEPRUEFT`.

Der dritte ist der wichtige. Eine Prüfung, die «alles gut» sagt, weil sie nichts kennt,
ist schlimmer als keine: Sie erzeugt genau das grüne Abzeichen, das niemanden mehr
nachsehen lässt. Dieselbe Falle ist diesem Projekt am 02.09.2026 zweimal begegnet — eine
Wache, die beim ersten Treffer grün gab, und ein Füllgrad, der immer 0.700 meldete.

:data:`UNGEPRUEFT` ist deshalb **kein Bestehen**. :func:`bestanden` gibt nur bei
:data:`TRAEGT` ``True`` zurück, und der Befund nennt jedes Mal, **was gefehlt hat**, um zu
einem Urteil zu kommen.

Was ohne Herkunftsvermerk trotzdem entschieden werden kann
-----------------------------------------------------------
Sonst wäre der dritte Zustand eine Ausrede. Genau **eine** Feststellung braucht keinen
Vermerk und keinen bekannten Erzeuger, weil sie an der Datei selbst messbar ist:

    **Eine glb mit Geometrie und ganz ohne Materialblock liegt zurück.**

glTF 2.0 hat den ``materials``-Block seit der ersten Fassung; jeder Erzeuger im Ökosystem
schreibt ihn, seit KosmoDraw es am 01.09.2026 als letzter nachgezogen hat. Eine Datei ohne
ihn ist entweder älter als dieser Stand oder von einem Erzeuger, der keine Materialien
kennt — in beiden Fällen wird sie grau gerendert, und ein durchsichtiges Fenster ist
unmöglich, egal was im Modell steht. Das ist der Befund, der an
``kosmo-lauf16/ergebnis/lauf16.glb`` greift: 4 Netze, 4 Primitive, **0 Materialien**.

Die Gegenprobe dazu gehört dazu und steht in den Tests: Dieselbe Datei **mit** Materialien
(``lauf16-mit-material.glb``: 3 Materialien, 7 Primitive) darf nicht beanstandet werden.
Eine Regel, die beide Fassungen gleich beurteilt, misst nicht.

Türen: verdächtig ist nicht dasselbe wie falsch
------------------------------------------------
Null Türen in einem Modell, dessen Erzeuger Türen bauen kann, ist ein **Verdacht** und
kein Mangel — ein Plan ohne Türen ist denkbar (ein Volumenmodell, ein Massing, ein
Geländeschnitt). Der Verdacht wird darum als Warnung gemeldet und hält nichts auf. Er ist
aber überhaupt nur formulierbar, wenn die Datei ihre Bauteilklassen mitbringt: **Eine glb
kennt Dreiecke, keine Türen.** Genau dafür trägt der Herkunftsvermerk sie mit.

Abhängigkeiten: stdlib und :mod:`aiimaging.glbbox` (der glb-Kopfleser). Kein ``bpy``, kein
``ifcopenshell``, keine GPU — überall prüfbar (Regel 4).
"""
from __future__ import annotations

from . import glbbox

#: Gemessen: Die Datei trägt, was ihr Erzeuger schreibt.
TRAEGT = "traegt"

#: Gemessen: Sie liegt hinter ihm zurück. Ein benannter Mangel, kein Verdacht.
ZURUECK = "zurueck"

#: **Nicht entscheidbar** — und das ist kein Bestehen. Der Befund nennt, was fehlt.
UNGEPRUEFT = "ungeprueft"

#: Die Vertragskennung des Herkunftsvermerks, den ``KosmoDraw/code/tools/glb_export_runner.py``
#: seit dem 02.09.2026 in ``asset.extras.kosmo_modellstand`` schreibt.
#:
#: Sie wird **wörtlich** verglichen. Eine andere Kennung heisst nicht «kaputt», sondern
#: «kenne ich nicht» — und führt zu :data:`UNGEPRUEFT`, nicht zu einer geratenen Deutung.
#: Ein Feldname, den man errät, erzeugt in diesem Ökosystem keine Fehlermeldung, sondern
#: eine tote Kante (siehe :mod:`aiimaging.kosmo_naht`).
VERMERK_SCHEMA = "kosmo.modellstand/v1"

#: Der Schlüssel, unter dem der Vermerk in ``asset.extras`` steht.
VERMERK_SCHLUESSEL = "kosmo_modellstand"

#: Merkmal aus dem Vermerk → wie es an der DATEI nachgemessen wird.
#:
#: Der Aufbau ist der Punkt: Links steht, was der Erzeuger von sich behauptet, rechts eine
#: Messung an der Ausgabe. Ein Merkmal ohne Messvorschrift wäre eine Behauptung, die sich
#: selbst bestätigt — und genau davon hatte dieses Projekt schon genug.
#:
#: Jeder Eintrag: ``(Feld im Vermerk unter "traegt", Klartext)``. Der Mangel entsteht,
#: wenn das Merkmal geführt wird und die gemessene Zahl 0 ist.
MERKMAL_MESSUNG: dict[str, tuple[str, str]] = {
    "materialien": ("n_materialien",
                    "Der Erzeuger schreibt Materialien, die Datei trägt keinen einzigen "
                    "Materialblock. Im Bild wird dann alles gleich grau, und eine "
                    "durchsichtige Scheibe ist unmöglich."),
    # Nachgemessen wird die Zahl der glTF-Nodes. Das ist bei einem beliebigen glTF NICHT
    # dasselbe wie «Disziplin-Layer» — hier aber schon, weil nur ein Erzeuger geprüft wird,
    # der dieses Merkmal führt, und der schreibt genau einen Node je Layer und sonst keinen.
    "disziplin_layer": ("n_disziplin_layer",
                        "Der Erzeuger schreibt einen Node je Disziplin, die Datei trägt "
                        "keinen. Der Viewer kann dann nichts ein- und ausblenden."),
}

#: Bauteilklassen, deren Fehlen ein **Verdacht** ist — nicht mehr.
#:
#: ``IfcDoor`` steht hier und ``IfcWindow`` nicht, und der Unterschied ist gemessen: Ein
#: Bau ohne Fenster ist als Zwischenstand alltäglich (ein Rohbau, ein Massing), ein
#: bewohntes Geschoss ohne eine einzige Tür ist es nicht. Wer diese Liste erweitert,
#: erzeugt Warnungen auf Vorrat — und eine Warnung, die bei jedem Auftrag steht, bedeutet
#: nichts.
VERDAECHTIG_LEER: dict[str, str] = {
    "IfcDoor": ("Das Modell trägt keine einzige Tür. Der Erzeuger kann sie aus dem Plan "
                "messen (Türblatt und Öffnungsbogen). Ein Plan ohne Türen ist denkbar — "
                "darum eine Warnung und kein Mangel."),
}


def _messe_glb(pfad) -> dict:
    """Was diese glb an nachprüfbaren Zahlen trägt. Ohne jeden Vermerk, rein gezählt."""
    js = glbbox.lies_gltf_json(pfad)
    meshes = js.get("meshes") or []
    primitive = [p for m in meshes for p in (m.get("primitives") or [])]
    asset = js.get("asset") or {}
    return {
        "n_netze": len(meshes),
        "n_primitive": len(primitive),
        "n_primitive_mit_material": sum(1 for p in primitive if p.get("material") is not None),
        "n_materialien": len(js.get("materials") or []),
        "n_disziplin_layer": len(js.get("nodes") or []),
        "generator": asset.get("generator"),
        "extras": asset.get("extras") or {},
    }


def _vermerk_aus(gemessen: dict) -> tuple[dict | None, str]:
    """Der Herkunftsvermerk aus ``asset.extras`` — oder ``None`` samt Grund."""
    roh = gemessen["extras"].get(VERMERK_SCHLUESSEL)
    if roh is None:
        return None, (
            f"Die Datei trägt keinen Herkunftsvermerk "
            f"(`asset.extras.{VERMERK_SCHLUESSEL}`). Sie sagt damit nicht, von welchem "
            f"Erzeuger sie stammt und was der schreiben kann — der Erzeuger steht nur als "
            f"`asset.generator` = {gemessen['generator']!r} da, und das ist bei einer "
            f"unmarkierten Datei der Name der BIBLIOTHEK, nicht des Werkzeugs.")
    if not isinstance(roh, dict):
        return None, f"`{VERMERK_SCHLUESSEL}` ist kein Wörterbuch, sondern {type(roh).__name__}."
    kennung = roh.get("schema")
    if kennung != VERMERK_SCHEMA:
        return None, (
            f"Der Vermerk trägt die Kennung {kennung!r}; gelesen wird "
            f"{VERMERK_SCHEMA!r}. Eine unbekannte Fassung wird NICHT geraten — die "
            f"Feldnamen könnten sich verschoben haben, und das fiele nicht auf.")
    return roh, ""


def pruefe(pfad) -> dict:
    """Liegt die glb unter ``pfad`` hinter ihrem Erzeuger zurück?

    Returns:
        ``{urteil, erzeuger, vermerk, maengel, warnungen, offen, gemessen, quelle,
        begruendung}``

        * ``urteil`` — :data:`TRAEGT`, :data:`ZURUECK` oder :data:`UNGEPRUEFT`.
        * ``maengel`` — benannte, an der Datei gemessene Rückstände. Nicht leer ⇒
          :data:`ZURUECK`.
        * ``warnungen`` — Verdachtsmomente (leere Bauteilklassen). Halten nichts auf.
        * ``offen`` — was fehlte, um weiter zu prüfen. Nicht leer und ohne Mangel ⇒
          :data:`UNGEPRUEFT`.
        * ``quelle`` — Fingerabdruck der Datei, aus der die glb entstand (Name, Bytes,
          SHA-256), sofern der Vermerk ihn trägt. Damit ist «welches Modell fährt hier
          eigentlich» erstmals beantwortbar.

    Raises:
        aiimaging.glbbox.GlbError: Die Datei ist keine lesbare glb. Das ist **kein**
            Modellstands-Befund, sondern ein Befund über die Datei — und gehört darum
            nicht in ein Urteil, das «trägt / liegt zurück» heisst.
    """
    gemessen = _messe_glb(pfad)
    maengel: list[str] = []
    warnungen: list[str] = []
    offen: list[str] = []

    # ── Die eine Feststellung ohne Vermerk ───────────────────────────────────────────
    # Sie steht VOR der Vermerkslesung, und das ist Absicht: Eine Datei ohne Vermerk soll
    # nicht deswegen ungeprüft durchgehen. Ohne diese Zeile wäre das Modul genau die
    # Prüfung, die «alles gut» sagt, weil sie nichts kennt.
    #: Felder, über die schon ein Mangel geschrieben wurde. Ohne diese Buchführung stünde
    #: derselbe Befund zweimal im Ergebnis — einmal ohne Vermerk gemessen, einmal gegen die
    #: Merkmalsliste. Zwei Zeilen für eine Tatsache lassen einen Lauf schlimmer aussehen,
    #: als er ist, und das ist dieselbe Sorte Unehrlichkeit wie zu wenig zu melden.
    schon_gemeldet: set[str] = set()

    if gemessen["n_primitive"] == 0:
        offen.append(
            "Die Datei trägt kein einziges Primitiv. Über den Stand eines Modells ohne "
            "Geometrie ist nichts auszusagen — und «keine Geometrie» ist kein Bestehen.")
    elif gemessen["n_materialien"] == 0:
        schon_gemeldet.add("n_materialien")
        maengel.append(
            f"Kein Materialblock: {gemessen['n_primitive']} Primitiv(e) in "
            f"{gemessen['n_netze']} Netz(en), 0 Materialien. Seit dem 01.09.2026 schreibt "
            f"der Export sie; eine glb ganz ohne ist entweder älter als dieser Stand oder "
            f"von einem Erzeuger, der keine kennt. Gerendert wird sie in beiden Fällen "
            f"gleich grau.")

    vermerk, grund = _vermerk_aus(gemessen)
    if vermerk is None:
        offen.append(grund)
        erzeuger = None
        quelle = None
    else:
        erzeuger = vermerk.get("erzeuger")
        quelle = vermerk.get("quelle")
        merkmale = vermerk.get("merkmale") or {}
        traegt = vermerk.get("traegt") or {}
        if not isinstance(merkmale, dict) or not isinstance(traegt, dict):
            offen.append("Der Vermerk führt `merkmale`/`traegt` nicht als Wörterbuch — "
                         "gelesen wird er nicht, geraten erst recht nicht.")
        else:
            # Behauptung gegen Messung, Merkmal für Merkmal.
            for name, seit in sorted(merkmale.items()):
                messung = MERKMAL_MESSUNG.get(name)
                if messung is None:
                    # Ein Merkmal, das wir nicht nachmessen können, wird NICHT als
                    # bestanden verbucht. Sonst wüchse die Zahl der «geprüften» Merkmale
                    # mit jeder Fassung des Erzeugers, ohne dass eine Messung dazukäme.
                    offen.append(
                        f"Merkmal {name!r} (seit {seit}) wird vom Erzeuger geführt, hat "
                        f"hier aber keine Messvorschrift — es bleibt ungeprüft.")
                    continue
                feld, klartext = messung
                if feld in schon_gemeldet:
                    continue                      # dieselbe Tatsache, schon benannt
                if gemessen.get(feld) == 0:
                    schon_gemeldet.add(feld)
                    maengel.append(f"{klartext} (Merkmal {name!r} seit {seit}, "
                                   f"gemessen {feld} = 0)")

            # Was die QUELLE trug — nur aus dem Vermerk, eine glb weiss es nicht selbst.
            klassen = traegt.get("ifc_klassen")
            if not isinstance(klassen, dict):
                offen.append("Der Vermerk nennt keine Bauteilklassen der Quelle. Ob "
                             "Türen fehlen, ist an einer glb sonst nicht feststellbar.")
            else:
                for klasse, text in sorted(VERDAECHTIG_LEER.items()):
                    # **Ein fehlender Schlüssel und eine Null sind zweierlei.** Die Null
                    # ist eine Messung («dieses Modell hat keine Tür»), das Fehlen keine
                    # («dieser Erzeuger zählt Türen nicht»). Beide gleich zu behandeln
                    # hiesse, aus Schweigen einen Befund zu machen — egal in welche
                    # Richtung, und die eine Richtung ist das grüne Abzeichen.
                    if klasse not in klassen:
                        offen.append(
                            f"Die Quelle zählt `{klasse}` nicht mit. Ob dieses Modell "
                            f"keine hat oder der Erzeuger sie nur nicht zählt, ist aus "
                            f"der Datei nicht zu entscheiden.")
                    elif int(klassen[klasse] or 0) == 0:
                        warnungen.append(f"{text} (`{klasse}` = 0, ausdrücklich gezählt)")

    urteil = ZURUECK if maengel else (UNGEPRUEFT if offen else TRAEGT)
    if maengel:
        begruendung = f"{len(maengel)} Rückstand/Rückstände gemessen: " + " | ".join(maengel)
    elif offen:
        begruendung = ("Nicht entscheidbar — und das zählt NICHT als bestanden: "
                       + " | ".join(offen))
    else:
        begruendung = (f"Die Datei trägt, was ihr Erzeuger ({erzeuger}) schreibt: "
                       f"{gemessen['n_materialien']} Material(ien), "
                       f"{gemessen['n_primitive_mit_material']} von "
                       f"{gemessen['n_primitive']} Primitiven materialisiert.")
    return {
        "urteil": urteil,
        "erzeuger": erzeuger,
        "vermerk": vermerk is not None,
        "maengel": maengel,
        "warnungen": warnungen,
        "offen": offen,
        "gemessen": {k: v for k, v in gemessen.items() if k != "extras"},
        "quelle": quelle,
        "begruendung": begruendung,
    }


def bestanden(befund: dict) -> bool:
    """``True`` nur bei :data:`TRAEGT`.

    Die Funktion ist eine Zeile lang und steht trotzdem hier, damit sie an **einer** Stelle
    steht: Wer ``urteil != ZURUECK`` schreibt, hat :data:`UNGEPRUEFT` stillschweigend zu
    einem Bestehen gemacht — und damit den dritten Zustand wieder abgeschafft.
    """
    return isinstance(befund, dict) and befund.get("urteil") == TRAEGT
