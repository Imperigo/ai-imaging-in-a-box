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


def _lies_urteil(urteil, bezeichnung: str) -> tuple[bool, str | None]:
    """Ein Teilurteil → ``(bestanden, mangel)``. Bei einem Mangel ist ``bestanden`` False.

    Der Mangel ist ein Satz für Menschen: Wer in einem Protokoll ein ``False`` findet,
    soll nicht raten müssen, ob gemessen und verfehlt wurde oder ob die Messung fehlte.
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
    if not isinstance(wert, bool):
        return False, (
            f"{bezeichnung}-Urteil trägt '{FELD_BESTANDEN}' als "
            f"{type(wert).__name__} ({wert!r}), nicht als bool. Ein Wahrheitswert-Test "
            f"liesse hier Text und Zahlen durchrutschen."
        )
    return wert, None


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

    bestanden = geometrie_ok and stil_ok

    if maengel:
        begruendung = (
            "Nicht bestanden — ein Teilurteil war nicht lesbar. " + " ".join(maengel)
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
