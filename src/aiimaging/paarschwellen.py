"""Aus benannten Fällen eine Schwelle ableiten — mit **beiden** Fehlerzahlen.

Warum es dieses Modul gibt
--------------------------
Zwei Zahlen im Paarurteil sind **abgelesen und nicht kalibriert**, und sie tragen den
Vorbehalt seit dem ersten Tag im Quelltext:

``geometrie_qa.PAAR_RHO_SCHWELLE = 0.80``
    Abgelesen an **sieben** Fällen aus **einer** Szene (`auf-20260821-27`).

``geometrie_qa.PAAR_KANTENANTEIL_SCHWELLE = 0.20``
    Liegt beim Vierfachen des Zufalls (5 %) und bei einem knappen Viertel des perfekten
    Bildes (87,4 %) — also sehr viel näher am Zufall als am Richtigen (`auf-20260822-30`).

Solange das so ist, darf das Paarurteil nichts sperren. Der Owner hat am 26.08.2026 aus
drei Wegen genau diesen gewählt: **erst kalibrieren, dann sperren.** Bis dahin steht der
Widerspruch nur da (`abholer.befund_kurz`, `kosmo_szene`).

Was hier gerechnet wird — und was ausdrücklich nicht
-----------------------------------------------------
Gerechnet wird die **Trennkurve**: Für jede Kandidatenschwelle beide Fehlerarten, jede
mit ihrem eigenen Namen.

* ``falsch_bestanden`` — ein schlechter Fall geht durch. **Der teure Fehler.** Er kostet
  ein Bild, dem jemand vertraut, obwohl es nicht stimmt.
* ``falsch_gesperrt`` — ein guter Fall wird abgewiesen. Er kostet einen weiteren Render.

**Nicht** gerechnet wird eine Empfehlung. Welche der beiden Fehlerarten wie schwer wiegt,
ist keine Messung, sondern eine Entscheidung — und sie gehört dem Owner. Dieses Modul
liefert ihm die Vorlage; es nimmt sie ihm nicht ab. *Eine Schwelle ohne ihre beiden
Fehlerzahlen ist wieder eine abgelesene, nur mit mehr Stellen hinter dem Komma.*

Die dritte Antwort gilt auch hier
----------------------------------
Drei Lagen ergeben **kein** Urteil, und in allen dreien ist das Ergebnis ``None`` und
nicht ``False``:

1. Eine Gruppe ist leer. Ohne schlechte Fälle sperrt jede Schwelle richtig; ohne gute
   lässt jede zu Recht durch. Beides sieht in der Tabelle nach perfekter Trennung aus.
2. Kein Fall ist messbar — jeder Wert ``None``.
3. Der Umfang reicht nicht. Sieben Fälle aus einer Szene sind genau das Problem, das
   dieses Modul lösen soll; es wird nicht gegen zwölf getauscht.

Lage 1 ist der Grund, warum hier nirgends ein blankes ``max()`` oder ``all()`` über eine
womöglich leere Sammlung steht: Beides antwortet dort mit einem Fehler oder mit einem
freundlichen ``True``, und keines von beidem ist die Wahrheit.
"""

from __future__ import annotations

from collections.abc import Sequence

# --------------------------------------------------------------------------------------
# Kandidatenreihen
# --------------------------------------------------------------------------------------

#: Kandidatenschwellen für die gerichtete Rangkorrelation über der Maske.
#:
#: Von 0,00 bis 0,95 in Schritten von 0,05. Die Reihe beginnt bei **null** und nicht bei
#: der heutigen 0,80: Wo die Trennung liegt, ist die Frage — sie zu umzingeln hiesse, die
#: Antwort schon zu kennen.
KANDIDATEN_RHO: tuple[float, ...] = tuple(round(0.05 * k, 2) for k in range(0, 20))

#: Kandidatenschwellen für den Anteil der Maskengrenze mit Tiefenkante (0,00 bis 0,90).
#:
#: Endet früher als die ρ-Reihe, weil selbst das perfekte Bild nur 87,4 % erreicht
#: (`auf-20260822-30`). Eine Schwelle darüber wäre kein Massstab, sondern ein Verbot.
KANDIDATEN_KANTENANTEIL: tuple[float, ...] = tuple(round(0.05 * k, 2) for k in range(0, 19))

#: Mindestumfang, unter dem die Kurve zwar gerechnet, aber **nicht** als Kalibrierung
#: ausgegeben wird. Die Zahlen stammen aus `auf-20260827-61` und sind eine Setzung, keine
#: Messung — sie stehen deshalb im Ergebnis, damit niemand sie für ein Naturgesetz hält.
MINDEST_GUT = 20
MINDEST_SCHLECHT = 20
MINDEST_SZENEN = 3
MINDEST_KAMERAS = 2


class PaarschwellenError(ValueError):
    """Ein Fall, der nicht sagt, ob er gut oder schlecht ist — das ist kein Datenmangel."""


# --------------------------------------------------------------------------------------
# Die Rechnung
# --------------------------------------------------------------------------------------

def _pruefe_faelle(faelle: Sequence[dict]) -> None:
    """Jeder Fall muss seine Kennung und sein Etikett tragen.

    **Warum das ein Fehler ist und keine übersprungene Zeile:** Ein Fall ohne Etikett
    gehört in keine der beiden Gruppen — er würde die Tabelle stillschweigend um eine
    Zeile kürzen, und niemandem fiele auf, welche. Ein fehlender *Messwert* ist etwas
    anderes: Der ist die dritte Antwort und wird benannt mitgeführt.
    """
    for i, fall in enumerate(faelle):
        if not fall.get("fall_id"):
            raise PaarschwellenError(
                f"Fall {i} hat keine Kennung. Ohne sie lässt sich eine auffällige Zeile "
                f"später nicht wiederfinden, und die Tabelle wird unbelegbar.")
        if not isinstance(fall.get("gut"), bool):
            raise PaarschwellenError(
                f"Fall {fall['fall_id']!r} sagt nicht, ob er gut oder schlecht ist "
                f"('gut' fehlt oder ist kein Wahrheitswert). Ein Fall ohne Etikett "
                f"gehört in keine Gruppe — er würde die Tabelle unbemerkt kürzen.")


def trennkurve(faelle: Sequence[dict], kandidaten: Sequence[float] = KANDIDATEN_RHO, *,
               groesse: str = "rho_maske_gerichtet") -> dict:
    """Für jede Kandidatenschwelle beide Fehlerzahlen — die Vorlage für den Entscheid.

    Args:
        faelle: Je Fall ein Satz mit ``fall_id`` (Pflicht), ``gut`` (Pflicht,
            Wahrheitswert), ``wert`` (die Messgrösse; ``None`` heisst *nicht messbar*)
            und wahlweise ``szene`` und ``kamera``.
        kandidaten: Die zu prüfenden Schwellen.
        groesse: Der Name der Messgrösse — er steht im Ergebnis, weil dieselbe Rechnung
            für ρ und für den Kantenanteil gilt und die Tabellen sonst verwechselbar sind.

    Returns:
        Ein Satz mit ``punkte`` (je Kandidat die vier Zahlen), ``trennt_sauber``
        (dreiwertig: ``True``, ``False`` oder ``None``), ``sauber_zwischen``,
        ``nicht_messbar`` und ``vorbehalte``.

    Die Regel ist überall dieselbe: Ein Fall **besteht**, wenn ``wert >= schwelle``. Ein
    nicht messbarer Fall besteht nicht und fällt auch nicht durch — er wird gezählt und
    benannt, aber nirgends eingerechnet.
    """
    _pruefe_faelle(faelle)

    gut_werte = [f["wert"] for f in faelle if f["gut"] and f.get("wert") is not None]
    schlecht_werte = [f["wert"] for f in faelle
                      if not f["gut"] and f.get("wert") is not None]
    nicht_messbar = [f["fall_id"] for f in faelle if f.get("wert") is None]

    punkte = []
    for schwelle in kandidaten:
        falsch_bestanden = sum(1 for w in schlecht_werte if w >= schwelle)
        falsch_gesperrt = sum(1 for w in gut_werte if w < schwelle)
        punkte.append({
            "schwelle": schwelle,
            "falsch_bestanden": falsch_bestanden,
            "falsch_gesperrt": falsch_gesperrt,
            "richtig_gesperrt": len(schlecht_werte) - falsch_bestanden,
            "richtig_bestanden": len(gut_werte) - falsch_gesperrt,
        })

    # DIE TRENNFRAGE — und hier entscheidet sich, ob die Tabelle überhaupt etwas sagt.
    #
    # `max(schlecht) < min(gut)` ist die saubere Trennung. Beide Aufrufe brauchen eine
    # nichtleere Sammlung, und genau darum steht die Leerprüfung VOR ihnen und nicht als
    # Ausnahmebehandlung dahinter: Eine leere Gruppe ist kein Sonderfall der Rechnung,
    # sondern das Ende der Auskunft.
    vorbehalte: list[str] = []
    if not gut_werte:
        vorbehalte.append(
            "KEIN EINZIGER MESSBARER GUTER FALL. Ohne sie sperrt jede Schwelle nur "
            "richtig — die Tabelle sieht perfekt aus und sagt nichts.")
    if not schlecht_werte:
        vorbehalte.append(
            "KEIN EINZIGER MESSBARER SCHLECHTER FALL. Ohne sie lässt jede Schwelle nur "
            "zu Recht durch — die Tabelle sieht perfekt aus und sagt nichts.")

    if gut_werte and schlecht_werte:
        hoechster_schlechter = max(schlecht_werte)
        niedrigster_guter = min(gut_werte)
        trennt_sauber = hoechster_schlechter < niedrigster_guter
        sauber_zwischen = ((hoechster_schlechter, niedrigster_guter)
                           if trennt_sauber else None)
    else:
        hoechster_schlechter = None
        niedrigster_guter = None
        trennt_sauber = None
        sauber_zwischen = None

    szenen = {f.get("szene") for f in faelle if f.get("szene")}
    kameras = {f.get("kamera") for f in faelle if f.get("kamera")}
    n_gut = sum(1 for f in faelle if f["gut"])
    n_schlecht = sum(1 for f in faelle if not f["gut"])

    if n_gut < MINDEST_GUT or n_schlecht < MINDEST_SCHLECHT:
        vorbehalte.append(
            f"UMFANG UNTER DEM MINDESTMASS: {n_gut} gute (mindestens {MINDEST_GUT}), "
            f"{n_schlecht} schlechte (mindestens {MINDEST_SCHLECHT}). Die Kurve ist "
            f"gerechnet, aber sie ist keine Kalibrierung — eine Schwelle auf wenigen "
            f"Fällen ist wieder eine abgelesene.")
    if len(szenen) < MINDEST_SZENEN or len(kameras) < MINDEST_KAMERAS:
        vorbehalte.append(
            f"ZU WENIG STREUUNG: {len(szenen)} Szene(n) (mindestens {MINDEST_SZENEN}), "
            f"{len(kameras)} Kamera(s) (mindestens {MINDEST_KAMERAS}). Beide Masse "
            f"hängen an der Maskenlage — eine Schwelle aus einer Szene gilt in der "
            f"nächsten nicht.")
    if nicht_messbar:
        vorbehalte.append(
            f"NICHT MESSBAR: {len(nicht_messbar)} von {len(faelle)} Fällen "
            f"({', '.join(str(k) for k in nicht_messbar[:5])}"
            f"{' …' if len(nicht_messbar) > 5 else ''}). Sie sind weder bestanden noch "
            f"durchgefallen und stehen in keiner Spalte der Tabelle.")

    return {
        "groesse": groesse,
        "n_gut": n_gut,
        "n_schlecht": n_schlecht,
        "n_gut_messbar": len(gut_werte),
        "n_schlecht_messbar": len(schlecht_werte),
        "nicht_messbar": nicht_messbar,
        "szenen": sorted(szenen),
        "kameras": sorted(kameras),
        "punkte": punkte,
        "trennt_sauber": trennt_sauber,
        "sauber_zwischen": sauber_zwischen,
        "hoechster_schlechter": hoechster_schlechter,
        "niedrigster_guter": niedrigster_guter,
        "vorbehalte": vorbehalte,
        "genuegt_als_kalibrierung": not vorbehalte,
    }


def bericht(kurve: dict) -> str:
    """Die Trennkurve als Text — für die Vorlage an den Owner.

    Die Vorbehalte stehen **oben**, nicht unten. Eine Tabelle, deren Einschränkung erst
    nach den Zahlen kommt, wird ohne sie gelesen.
    """
    zeilen: list[str] = [f"TRENNKURVE · {kurve['groesse']}"]

    for v in kurve["vorbehalte"]:
        zeilen.append(f"  ! {v}")

    if kurve["trennt_sauber"] is None:
        zeilen.append("  Trennung: NICHT BEURTEILBAR — eine der beiden Gruppen ist leer.")
    elif kurve["trennt_sauber"]:
        a, b = kurve["sauber_zwischen"]
        zeilen.append(f"  Trennung: SAUBER. Jede Schwelle über {a:.4f} und bis {b:.4f} "
                      f"trennt die vorliegenden Fälle fehlerfrei.")
    else:
        zeilen.append(
            f"  Trennung: ÜBERLAPPEND. Der schlechteste gute Fall liegt bei "
            f"{kurve['niedrigster_guter']:.4f}, der beste schlechte bei "
            f"{kurve['hoechster_schlechter']:.4f} — es gibt keine fehlerfreie Schwelle.")

    zeilen.append(f"  Fälle: {kurve['n_gut']} gut ({kurve['n_gut_messbar']} messbar), "
                  f"{kurve['n_schlecht']} schlecht ({kurve['n_schlecht_messbar']} messbar)"
                  f" · {len(kurve['szenen'])} Szenen · {len(kurve['kameras'])} Kameras")
    zeilen.append("")
    zeilen.append("  Schwelle | falsch bestanden | falsch gesperrt")
    for p in kurve["punkte"]:
        zeilen.append(f"     {p['schwelle']:5.2f} | {p['falsch_bestanden']:16d} | "
                      f"{p['falsch_gesperrt']:15d}")
    zeilen.append("")
    zeilen.append("  KEINE EMPFEHLUNG. Welcher der beiden Fehler schwerer wiegt, ist "
                  "eine Entscheidung und keine Messung.")
    return "\n".join(zeilen)
