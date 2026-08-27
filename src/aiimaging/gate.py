"""DAS DOPPEL-GATE — bestanden nur, wenn Geometrie UND Stil bestehen.

Der belegte Anlass
------------------
Im Vorläufer KosmoVis lief eine Zeit lang nur das Stil-Gate. Bei einem Lauf an echter
Geometrie meldete es ``bestanden`` mit einem Stil-Score von **0.42** — auf einen Render,
dessen **Kubatur halluziniert** war. Das Bild sah aus wie ein Haus des Büros; es war nur
nicht das Haus, das im Modell stand.

Das ist kein Ausrutscher, sondern die Blindstelle der Methode: Ein Stil-Score misst
Bildstatistik. Ein plausibel aussehendes, frei erfundenes Gebäude erreicht dort mühelos
hohe Werte — je überzeugender die Halluzination, desto besser der Stil-Score. Wer allein
danach urteilt, belohnt genau den Fehler, den er finden müsste.

Die Geometrie-QA schliesst diese Lücke, und nur zusammen ergeben die beiden ein Urteil:

* **Geometrie ohne Stil** — richtiges Haus, falsches Bild. Unbrauchbar für die Abgabe.
* **Stil ohne Geometrie** — schönes Bild, falsches Haus. Der gefährlichere Fall, weil er
  niemandem auffällt.

Darum **UND**, nicht ODER. Ein ODER wäre kein Gate, sondern eine Einladung: Jeder Render
fände irgendein Kriterium, an dem er besteht.

Warum dieses Modul keine der beiden QAs importiert
--------------------------------------------------
:func:`gesamturteil` nimmt zwei Wörterbücher entgegen und liest daraus ``bestanden``.
Mehr nicht. Damit hängt das Doppel-Gate an keiner der beiden Messmethoden, beide bleiben
einzeln austauschbar, und dieses Modul ist prüfbar, ohne dass eine von beiden existiert
oder lauffähig ist.

Fail-closed
-----------
Fehlt ``bestanden`` oder ist es kein ``bool``, gilt das Urteil als **nicht bestanden**
und der Mangel wird benannt. Kein Fehler wird geworfen: Eine Ausnahme kann jemand fangen
und weiterlaufen — ein ``bestanden: False`` kann niemand mit einem Durchlass verwechseln.
Und geprüft wird auf ``bool``, nicht auf Wahrheitswert: Ein ``{"bestanden": "nein"}``
wäre truthy und käme durch. Genau so entstehen die Fehler, die dieses Modul verhindern
soll.

Abhängigkeiten: keine. Reine stdlib, kein Import aus ``aiimaging``.
"""
from __future__ import annotations

#: Das Feld, an dem beide QA-Module ihr Urteil tragen. Die einzige Kopplung zwischen
#: Geometrie-QA, Stil-QA und diesem Modul — bewusst so schmal wie möglich.
FELD_BESTANDEN = "bestanden"


def _lies_urteil(urteil, bezeichnung: str) -> tuple[bool | None, str | None]:
    """Ein Teilurteil → ``(bestanden, mangel)``. Bei einem Mangel ist ``bestanden`` False.

    Der Mangel ist ein Satz für Menschen: Wer in einem Protokoll ein ``False`` findet,
    soll nicht raten müssen, ob gemessen und verfehlt wurde oder ob die Messung fehlte.

    **Drei Werte, nicht zwei — seit dem 26.08.2026.** ``bestanden`` darf ``None`` sein,
    und das ist **kein Mangel**: Es heisst *nicht beurteilbar*. Ein Teilurteil kann das
    ausdrücken, ohne dass die Messung gescheitert wäre — die Geometrie-QA tut es, wenn
    der Maskenweg nicht lief (Owner-Entscheid: zweites Tor, nicht Zusatzmessung).

    Der Unterschied zu einem Mangel ist der Handgriff, der folgt: Ein Mangel heisst
    *repariere die Naht*, ein ``None`` heisst *hole die fehlende Messung nach*. Beides
    unter ``False`` zusammenzufassen hiesse, den zweiten Fall wie einen Fehler aussehen
    zu lassen — und genau das war er nicht.
    """
    if not isinstance(urteil, dict):
        return False, (
            f"{bezeichnung}-Urteil ist kein Wörterbuch, sondern "
            f"{type(urteil).__name__} — es hat keine Messung stattgefunden."
        )
    if FELD_BESTANDEN not in urteil:
        return False, (
            f"{bezeichnung}-Urteil trägt kein Feld '{FELD_BESTANDEN}'. Vorhanden: "
            f"{sorted(urteil)}. Ohne Urteil wird nicht durchgelassen."
        )
    wert = urteil[FELD_BESTANDEN]
    if wert is None:
        return None, None                     # nicht beurteilbar — und kein Mangel
    if not isinstance(wert, bool):
        return False, (
            f"{bezeichnung}-Urteil trägt '{FELD_BESTANDEN}' als "
            f"{type(wert).__name__} ({wert!r}), nicht als bool. Ein Wahrheitswert-Test "
            f"liesse hier Text und Zahlen durchrutschen."
        )
    return wert, None


#: Zustandswörter, die KosmoVis' `kosmovis_query_qa_verdict` je Teil-Gate erwartet.
STATUS_OK = "ok"
STATUS_FEHLT = "fehlt"
STATUS_DEGENERIERT = "degeneriert"


def als_kosmovis_verdikt(gesamt: dict) -> dict:
    """Unser Doppel-Gate in die Feldnamen übersetzen, die das Ökosystem tatsächlich liest.

    **Der Befund, aus dem das entstand (18.08.2026, Ökosystem-Durchsicht):** KosmoVis hat
    unsere Landestelle längst gebaut. `integrations/odysseus/kosmovis_mcp_server.py`
    führt ein Werkzeug `kosmovis_query_qa_verdict`, das aus einer `render-result.json`
    genau ein Doppel-Gate liest — und es erwartet diese Namen::

        released, passed, style_status, geometry_status, fail_reasons,
        style_score, geometry_fidelity, style_threshold, geometry_threshold

    Unser :func:`gesamturteil` liefert dieselbe Sache unter `bestanden`, `score`,
    `schwelle`, `maengel`. **Dieselbe Sache, andere Namen — und KosmoOrbit verdrahtet
    über Feldnamen-Gleichheit, ohne Fehlermeldung.** Das ist der Phase-0-Befund in seiner
    teuersten Ausprägung: eine tote Kante, die niemand meldet.

    Warum eine Übersetzung und keine Umbenennung
    ---------------------------------------------
    Unsere Felder heissen deutsch und bleiben es. Die Begriffe dieses Projekts sind Teil
    der Arbeit, und eine Registry umzubenennen, weil ein Nachbarsystem andere Wörter
    benutzt, verlöre die Begründungen, die an ihnen hängen. Übersetzt wird **an der
    Naht** — genau wie in :mod:`aiimaging.mcp_schemas`, wo die Verträge nach aussen auch
    englisch heissen.

    Drei Zustände, nicht zwei
    --------------------------
    Das fremde Werkzeug kennt je Gate `ok`, `fehlt` und `degeneriert`. Diese Dreiteilung
    ist **besser als unsere** und trifft genau den Fall, den die Schwellenstudie
    interessant macht: ein Score von ``None`` heisst „nicht messbar", nicht „durchgefallen".
    Bisher ging das in `maengel` unter; hier bekommt es einen eigenen Zustand.

    * ``fehlt`` — kein Teilurteil vorhanden oder unlesbar.
    * ``degeneriert`` — Urteil da, aber ``score`` ist ``None``: nicht messbar.
    * ``ok`` — gemessen.

    ``released`` ist wie drüben **fail-closed und nie ``None``**: Nur wenn beide Gates
    ``ok`` sind und beide bestehen. ``passed`` bleibt dreiwertig — ``None``, wenn gar
    nicht beurteilt werden konnte, denn ein Freispruch aus Mangel an Messung wäre die
    teuerste Sorte Urteil.
    """
    def _teil(urteil, score_feld: str) -> tuple[str, float | None, float | None, bool]:
        if not isinstance(urteil, dict):
            return STATUS_FEHLT, None, None, False
        if "bestanden" not in urteil:
            return STATUS_FEHLT, None, None, False
        score = urteil.get("score")
        schwelle = urteil.get("schwelle")
        if score is None:
            return STATUS_DEGENERIERT, None, schwelle, False
        if urteil.get("bestanden") is None:
            # Gemessen, aber nicht beurteilbar: Der Score steht da und bleibt lesbar, das
            # Urteil fehlt. `degeneriert` ist drüben genau dafür da — und die Zahl reist
            # mit, damit niemand sie fuer nicht vorhanden hält.
            return STATUS_DEGENERIERT, score, schwelle, False
        return STATUS_OK, score, schwelle, bool(urteil.get("bestanden"))

    geo = gesamt.get("geometrie")
    stil = gesamt.get("stil")
    geo_status, geo_score, geo_schwelle, geo_ok = _teil(geo, "score")
    stil_status, stil_score, stil_schwelle, stil_ok = _teil(stil, "score")

    gruende: list[str] = []
    for name, status, ok in (("geometry", geo_status, geo_ok),
                             ("style", stil_status, stil_ok)):
        if status == STATUS_FEHLT:
            gruende.append(f"{name}_gate_fehlt")
        elif status == STATUS_DEGENERIERT:
            gruende.append(f"{name}_nicht_messbar")
        elif not ok:
            gruende.append(f"{name}_unter_schwelle")

    beide_messbar = geo_status == STATUS_OK and stil_status == STATUS_OK
    return {
        "released": bool(beide_messbar and geo_ok and stil_ok),
        # Dreiwertig: None heisst „nicht beurteilbar", nicht „durchgefallen".
        "passed": (geo_ok and stil_ok) if beide_messbar else None,
        "geometry_status": geo_status,
        "style_status": stil_status,
        "geometry_fidelity": geo_score,
        "geometry_threshold": geo_schwelle,
        "style_score": stil_score,
        "style_threshold": stil_schwelle,
        "fail_reasons": gruende,
    }


def gesamturteil(geometrie_urteil: dict, stil_urteil: dict) -> dict:
    """Doppel-Gate: bestanden **nur**, wenn beide Teilurteile bestanden sind.

    Args:
        geometrie_urteil: Antwort von ``geometrie_qa.geometrie_gate(...)`` — gelesen wird
            allein ``bestanden``.
        stil_urteil: Antwort von ``stil_qa.stil_gate(...)`` — ebenso.

    Returns:
        ``{bestanden, geometrie, stil, maengel, begruendung}``.

        ``geometrie`` und ``stil`` sind die unveränderten Teilurteile, durchgereicht,
        damit ein einziges Wörterbuch das vollständige Protokoll trägt: Wer später fragt,
        *warum* etwas durchfiel, findet Score und Schwelle beider Seiten an einer Stelle.

        ``maengel`` ist leer, wenn beide Teilurteile lesbar waren, und benennt sonst, was
        fehlte. Ein Mangel führt immer zu ``bestanden: False``.

    Die übergebenen Wörterbücher werden nur gelesen, nie verändert.

    Der Kern in einer Zeile: ``geometrie["bestanden"] and stil["bestanden"]``. Der Rest
    dieser Funktion ist die Sorgfalt, mit der ein fehlendes Urteil von einem verfehlten
    unterschieden wird — denn nur eines von beidem ist ein Messergebnis.
    """
    geometrie_ok, mangel_geo = _lies_urteil(geometrie_urteil, "Geometrie")
    stil_ok, mangel_stil = _lies_urteil(stil_urteil, "Stil")
    maengel = tuple(m for m in (mangel_geo, mangel_stil) if m)

    # DREIWERTIGES UND (Kleene), seit dem 26.08.2026.
    #
    #   False UND unbekannt  = False   — ein gerissenes Tor entscheidet allein.
    #   True  UND unbekannt  = None    — ein Freispruch aus Mangel an Messung wäre die
    #                                    teuerste Sorte Urteil.
    #
    # `and` allein täte das nicht: `None and True` ergibt `None`, `True and None` auch,
    # aber `False and None` ergibt `False` — richtig — und `None and False` ergibt
    # `None` — falsch. Darum ausgeschrieben statt abgekürzt.
    if geometrie_ok is False or stil_ok is False:
        bestanden: bool | None = False
    elif geometrie_ok is None or stil_ok is None:
        bestanden = None
    else:
        bestanden = True

    if maengel:
        begruendung = (
            "Nicht bestanden — ein Teilurteil war nicht lesbar. " + " ".join(maengel)
        )
    elif bestanden is None:
        offen = [name for name, wert in (("Geometrie", geometrie_ok), ("Stil", stil_ok))
                 if wert is None]
        begruendung = (
            f"NICHT BEURTEILBAR: {' und '.join(offen)} liegt kein Urteil vor — gemessen "
            f"wurde, aber eine nötige Teilprüfung ist nicht gelaufen. Das ist weder "
            f"bestanden noch durchgefallen. Was fehlt, steht im jeweiligen Teilurteil; "
            f"bei der Geometrie ist es in aller Regel der Maskenweg, und der braucht "
            f"einen Material-ID-Pass."
        )
    elif bestanden:
        begruendung = (
            "Bestanden: Geometrie UND Stil. Der Render folgt der Geometrie und trifft "
            "den Hausstil."
        )
    elif geometrie_ok and not stil_ok:
        begruendung = (
            "Nicht bestanden: Geometrie ja, Stil nein. Das richtige Gebäude im falschen "
            "Bild — Beleuchtung, Material oder Bildsprache treffen den Hausstil nicht. "
            "Neu rendern, Geometrie kann bleiben."
        )
    elif stil_ok and not geometrie_ok:
        begruendung = (
            "Nicht bestanden: Stil ja, Geometrie nein. Das ist der gefährliche Fall — "
            "ein überzeugend aussehender Render, der der Geometrie nicht folgt. Genau "
            "hier meldete ein reines Stil-Gate einmal 'bestanden' (0.42) auf eine "
            "halluzinierte Kubatur. Der hohe Stil-Score ist kein Trost, sondern das "
            "Warnzeichen: Die Halluzination war überzeugend."
        )
    else:
        begruendung = (
            "Nicht bestanden: weder Geometrie noch Stil. Vor dem nächsten Versuch prüfen, "
            "ob Konditionierung und Tiefenkarte überhaupt beim Modell ankamen — beide "
            "Gates gleichzeitig zu verfehlen deutet eher auf einen Kettenfehler als auf "
            "einen misslungenen Render."
        )

    return {
        "bestanden": bestanden,
        "geometrie": geometrie_urteil,
        "stil": stil_urteil,
        "maengel": maengel,
        "begruendung": begruendung,
    }
