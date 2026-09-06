#!/usr/bin/env python3
"""ANTWORT — eine Antwort im Klartext als Ergebnisdatei ablegen.

Wozu es dieses Werkzeug gibt
----------------------------
Antworten von `cloud` und `ui` kommen seit dem 06.09.2026 als **Text** zurück: Der Owner
trägt den Block hinüber und die Antwort zurück. Bis hierher hätte ich daraus von Hand
eine JSON-Datei geschrieben — und genau dabei sind am 23.08. und 26.08. zwei Ergebnisse
mit einem Status entstanden, den der Vertrag nicht kennt (`teilweise`, `erledigt`). Sie
galten als beantwortet und waren es nicht; aufgefallen ist es erst am 02.09.

*Was von Hand geschrieben wird, wird irgendwann falsch geschrieben.* Dieses Werkzeug geht
durch `auftrag.baue_ergebnis`, und das kennt nur vier Status.

Was es NICHT tut
----------------
**Es beurteilt nicht.** Ob eine Antwort die Frage wirklich beantwortet, entscheidet ein
Mensch — hier wird abgelegt, was gekommen ist. Ein Werkzeug, das «vollständig» von
«ausweichend» unterscheiden wollte, träfe diese Entscheidung still und falsch.

**Es erfindet keine Zahlen.** Der Text landet unter ``urteil.antwort_text``, nicht unter
``messwerte`` — eine Antwort in Prosa ist kein Messwert, und sie in einen zu verwandeln
hiesse, ihr eine Genauigkeit anzudichten.

Beispiele
---------
    python tools/antwort.py auf-20260823-37 --datei antwort.txt
    echo "Kam an am 07.09." | python tools/antwort.py auf-20260903-74
    python tools/antwort.py auf-20260827-63 --status abgelehnt --datei nein.txt
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aiimaging import auftrag  # noqa: E402

#: Woher eine so abgelegte Antwort kam. **Steht in der Datei und nicht nur im Kopf des
#: Ablegenden:** Eine Antwort über einen Menschen ist anders belegt als eine, die als
#: Datei ankam — wer sie später liest, soll den Unterschied sehen können.
HERKUNFT_STANDARD = "Block, vom Owner von Hand uebergeben und zurueckgetragen"


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("auftrag", help="Kennung, z.B. auf-20260823-37")
    p.add_argument("--datei", help="Datei mit dem Antworttext. Ohne sie wird von der "
                                   "Standardeingabe gelesen.")
    p.add_argument("--status", default="ok", choices=sorted(auftrag.STATUS_BEKANNT),
                   help="Vorgabe: ok — auch fuer ein begruendetes Nein: Die Frage ist "
                        "dann beantwortet. `abgelehnt` ist fuer einen LAUF, den die "
                        "Maschine nicht gerechnet hat, und zaehlt als unbeantwortet.")
    p.add_argument("--herkunft", default=HERKUNFT_STANDARD)
    p.add_argument("--repo", default=".", help="Wurzel des Repos (Vorgabe: hier)")
    p.add_argument("--trocken", action="store_true",
                   help="nur zeigen, was geschrieben wuerde")
    a = p.parse_args(argv)

    wurzel = Path(a.repo)
    if not (wurzel / "auftraege" / "offen" / f"{a.auftrag}.json").exists():
        # ABBRECHEN STATT ANLEGEN. Eine Ergebnisdatei ohne Auftrag ist eine Waise: Sie
        # steht in keiner Zaehlung, weil gegen die OFFENEN Auftraege gezaehlt wird — und
        # faellt darum niemandem auf. Ein Tippfehler in der Kennung erzeugte sie still.
        print(f"FEHLER: {a.auftrag} liegt nicht unter auftraege/offen/. Tippfehler? "
              f"Eine Ergebnisdatei ohne Auftrag wird von keiner Zaehlung gesehen.",
              file=sys.stderr)
        return 2

    # `abgelehnt` HEISST BEI EINER FRAGE ETWAS ANDERES ALS BEI EINEM LAUF, und der
    # Unterschied kostet die Antwort.
    #
    # Bei einem Lauf sagt es: die Maschine hat nicht gerechnet — `zustand` fuehrt den
    # Auftrag darum weiter als UNBEANTWORTET, und das ist richtig, denn es ist noch
    # nichts da.
    #
    # Bei einer Frage ist ein begruendetes Nein die VOLLSTAENDIGE Antwort. Genau das
    # steht so in jedem Block, den wir hinausgeben: «Ein 'machen wir nicht' ist eine
    # verwertbare Antwort, Schweigen ist keine.» Mit `abgelehnt` abgelegt, zaehlte sie
    # trotzdem weiter als offen — wir wuerden nachfragen, was uns laengst beantwortet
    # wurde, und der Adressat saehe seine Antwort ignoriert.
    #
    # Der Status beschreibt, ob die AUFGABE erfuellt ist, nicht ob die Antwort gefaellt.
    satz_auftrag = json.loads(
        (wurzel / "auftraege" / "offen" / f"{a.auftrag}.json").read_text(encoding="utf-8"))
    if a.status == "abgelehnt" and satz_auftrag.get("art") == auftrag.ART_FRAGE:
        print(f"FEHLER: {a.auftrag} ist eine Frage, und ein begruendetes Nein ist ihre "
              f"vollstaendige Antwort — nimm --status ok und schreib das Nein in den "
              f"Text.\n"
              f"Mit `abgelehnt` zaehlt der Auftrag weiter als OFFEN: Wir wuerden "
              f"nachfragen, was uns beantwortet wurde.\n"
              f"(`abgelehnt` ist fuer einen LAUF gedacht, den die Maschine nicht "
              f"gerechnet hat — da ist wirklich noch nichts da.)", file=sys.stderr)
        return 2

    text = Path(a.datei).read_text(encoding="utf-8") if a.datei else sys.stdin.read()
    text = text.strip()
    if not text:
        print("FEHLER: Der Antworttext ist leer. Eine leere Antwort ist keine.",
              file=sys.stderr)
        return 2

    satz = auftrag.baue_ergebnis(
        auftrag_id=a.auftrag,
        status=a.status,
        urteil={"antwort_text": text, "herkunft": a.herkunft},
    )
    if a.trocken:
        print(f"WUERDE SCHREIBEN: auftraege/ergebnisse/{a.auftrag}.json "
              f"(status={a.status}, {len(text)} Zeichen)")
        return 0

    ziel = auftrag.schreibe_ergebnis(satz, wurzel)
    print(f"geschrieben: {ziel.relative_to(wurzel) if ziel.is_relative_to(wurzel) else ziel}")
    print(f"Der Auftrag gilt jetzt als beantwortet. Naechster Schritt: pruefen, ob die "
          f"Antwort einen EINBAU verlangt — geliefert ist nicht eingebaut.")
    return 0


if __name__ == "__main__":                                   # pragma: no cover
    raise SystemExit(main())
