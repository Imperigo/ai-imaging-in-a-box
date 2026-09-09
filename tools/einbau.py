#!/usr/bin/env python3
"""EINBAU-STAND — was fehlt noch, und bei wem liegt es?

Die dünne Schicht über :mod:`aiimaging.einbau`. Sie rechnet nichts; sie zeigt.

**Wozu es sie gibt** (Owner-Auftrag 26.08.2026): Der Einbau in KosmoOrbit ist das Ziel,
nicht der Bau. Verantwortung für etwas, das anderswo geschieht, lässt sich nur führen,
wenn der Rückstand zählbar ist — und was von Hand gezählt wird, wird irgendwann nicht mehr
gezählt.

    python tools/einbau.py              # der Stand in einem Blick
    python tools/einbau.py --json       # dasselbe für ein Werkzeug
    python tools/einbau.py --worker ui  # nur ein Adressat

Rückgabewert **1** in zwei Fällen — beides Zustände, für die ich hafte, und beide sollen
ein Skript scheitern lassen können:

1. **Ein offener Posten hat keinen Adressaten.** Er wird nie eingebaut, und es fällt
   niemandem auf.
2. **Eine erledigte Zeile sagt nicht, worauf ihr Beleg ruht** — im Repo oder am Gerät.
   Seit dem 27.08.2026, nachdem `B8` sechs Tage als erledigt geführt worden war, während
   auf dem Gerät eine Fassung vom 20.08. lief. *Eine Datei im Repo belegt, was jemand
   geschrieben hat, nicht was auf dem Gerät läuft.*

Ein blosser Rückstand ist **kein** Fehler: Ein Auftrag, der bei einem Worker liegt, ist
verteilt.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aiimaging import auftrag, einbau  # noqa: E402


def _zeilen(bericht: dict, nur: str | None) -> list[str]:
    aus: list[str] = []
    # NICHT AUSGELIEFERT STEHT GANZ OBEN, und das ist kein Geschmack: Es ist der einzige
    # Rueckstand, den wir SELBST sofort beheben koennen. Alle Zahlen darunter messen, wie
    # lange jemand anders braucht; diese misst, was bei uns liegen geblieben ist.
    #
    # Am 03.09.2026 lagen zwei Auftraege an `ui` zwei bzw. einen Tag im Repo und waren nie
    # hinausgegangen. Sie zaehlten als Rueckstand beim Adressaten und waren einer beim
    # Absender — und sahen in dieser Liste aus wie jeder andere.
    nicht_raus = bericht.get("unzugestellt") or []
    if nicht_raus:
        aus.append(f"NICHT AUSGELIEFERT: {len(nicht_raus)} Auftrag/Auftraege liegen nur "
                   f"bei UNS — kein Block ist je hinausgegangen.")
        aus.append("      Abhilfe: tools/auftragspost.py <worker> --nach <verzeichnis>")
        for e in nicht_raus:
            aus.append(f"      {e['auftrag_id']:<22} an {e['worker']:<6} "
                       f"seit {str(e['erstellt'])[:10]}")
        aus.append("")
    r = bericht["rueckstand"]
    aus.append(f"RUECKSTAND: {r['n']} Auftraege ohne Antwort"
               + (f", aeltester {r['aelteste_tage']} Tage" if r["aelteste_tage"] is not None
                  else ""))
    verhalten = bericht.get("antwortverhalten") or {}
    for worker, anzahl in r["je_worker"].items():
        if nur and worker != nur:
            continue
        # DIE ANTWORTZEILE STEHT BEI DER ZAHL UND NICHT IN EINER ZWEITEN TABELLE. «Sieben
        # offen» und «sieben offen, keine Antwort in unserer Ablage» sind zwei
        # verschiedene Lagen, und die zweite verlangt keine Geduld, sondern eine Frage
        # nach dem Zustellweg.
        #
        # DER TEXT HAT AM 06.09.2026 SEINE BEHAUPTUNG VERKLEINERT, und der Anlass war
        # peinlich. Er hiess «NIE GEANTWORTET» — eine Aussage ueber MENSCHEN. Gemessen
        # werden kann aber nur eine Aussage ueber unsere ABLAGE. Der Home-PC-Worker fand
        # am selben Tag 15 Antworten von `cloud` und `ui`, datiert auf den 03.09., in
        # einem Verzeichnis, in das wir nie sehen. Zu diesem Zeitpunkt hatte der Owner
        # bereits zwei Bloecke von Hand hinuebergetragen, in denen woertlich stand: «Auf
        # keinen davon kam je eine Antwort.»
        #
        # *Ein Werkzeug, das aus dem eigenen Nichtwissen einen Vorwurf macht, ist keine
        # Messung mehr.* Was hier steht, muss ohne Kenntnis fremder Verzeichnisse wahr
        # bleiben — und «bei uns liegt keine» ist es.
        v = verhalten.get(worker) or {}
        if anzahl and v.get("n_antworten") == 0:
            zusatz = "  KEINE ANTWORT IN UNSERER ABLAGE"
            if v.get("n_weitergereicht"):
                zusatz += f" ({v['n_weitergereicht']} weitergereicht)"
        elif v.get("letzte_antwort"):
            zusatz = f"  letzte Antwort {v['letzte_antwort'][:10]}"
        else:
            zusatz = ""
        aus.append(f"  {worker:<6} {anzahl}{zusatz}")
        for e in r["eintraege"]:
            if e["worker"] != worker:
                continue
            alter = "?" if e["tage"] is None else f"{e['tage']}d"
            aus.append(f"      {e['auftrag_id']:<22} {alter:>4}  {e['beschreibung'][:70]}")
    # DER DECKEL MELDET, ER SPERRT NICHT. Er steht bei den Zahlen, zu denen er gehoert,
    # und nicht als Ausnahme beim Schreiben — dort greift er nur bei dem, der ihn
    # eingefuehrt hat, und alle anderen laufen still vorbei (gemessen von drei Lanes am
    # 06.09.2026).
    ueber = bericht.get("ueber_deckel") or {}
    if ueber and not nur:
        aus.append("")
        for worker, anzahl in sorted(ueber.items()):
            aus.append(f"UEBER DEM DECKEL: {worker} traegt {anzahl}, der Deckel liegt bei "
                       f"{auftrag.DECKEL_JE_WORKER}.")

    # DIE VERGABESTELLE STEHT DORT, WO OHNEHIN GEZAEHLT WIRD (09.09.2026).
    #
    # Der Anlass ist an einem Abend zweimal angefallen: Eine fremde Lane nahm erst einen
    # belegten Rang, eine Stunde spaeter Rang UND Laufnummer — beide Male wurde `main`
    # rot, und aufgeraeumt hat der, der zuletzt pushte. `tests/test_auftraege.py`
    # VERLANGT eine lueckenlose Reihe je Adressat und sagte niemandem, welcher Rang frei
    # ist.
    #
    # *Eine Vorschrift ohne Vergabestelle verlagert die Arbeit auf den, der zuletzt
    # kommt.* Die Auskunft gehoert darum in die Zeile, die man ohnehin liest, bevor man
    # einen Auftrag schreibt — und nicht in eine Funktion, die man kennen muesste.
    vergabe = bericht.get("vergabe") or {}
    if vergabe:
        aus.append("")
        aus.append(f"FREI ZU VERGEBEN: Laufnummer {vergabe['laufnummer']:02d} "
                   f"(auf-<JJJJMMTT>-{vergabe['laufnummer']:02d}), "
                   + ", ".join(f"Rang {r} bei {w}"
                               for w, r in sorted(vergabe["raenge"].items())))
        aus.append("      Gezaehlt ueber offen UND ergebnisse, datumsuebergreifend. "
                   "Vier Lanes schreiben hier hinein.")

    # ANTWORTEN, DIE NIEMAND AUFGESCHRIEBEN HAT (09.09.2026). Sie stehen VOR dem
    # Einbau-Stand, weil eine ungelesene Antwort die teuerste Sorte offener Posten ist:
    # Sie sieht in jeder Zaehlung erledigt aus.
    unverarbeitet = bericht.get("unverarbeitet") or []
    if unverarbeitet and not nur:
        aus.append("")
        aus.append(f"BEANTWORTET, ABER NIRGENDS AUFGESCHRIEBEN: {len(unverarbeitet)} "
                   f"Antwort(en) — keine Kennung davon steht in docs/:")
        for e in unverarbeitet:
            aus.append(f"      {e['kennung']:<22} beendet {e['beendet'][:10] or '?'}")
        aus.append("      Der Rueckstand meldet sie nicht: Er zaehlt Auftraege OHNE "
                   "Antwort, und diese haben eine.")

    unbekannt = bericht.get("unbekannter_status") or []
    if unbekannt:
        aus.append("")
        aus.append(f"STATUS, DEN DER VERTRAG NICHT KENNT: {len(unbekannt)} Ergebnis(se) "
                   f"— sie gelten als OFFEN, nicht als beantwortet:")
        for e in unbekannt:
            aus.append(f"      {e['auftrag_id']:<22} status={e['status']!r}")
            if e["art"]:
                aus.append(f"          {e['art']}")

    aus.append("")
    offen = bericht["offene_posten"]
    aus.append(f"EINBAU-STAND: {len(offen)} von {bericht['n_posten']} Posten noch nicht "
               f"in der Software")
    for p in offen:
        aus.append(f"  {p['kennung']:<4} {p['zustand']:<30} {p['posten'][:60]}")
    aus.append("")
    if bericht["ohne_adressat"]:
        aus.append("OHNE ADRESSATEN — diese Posten treibt niemand:")
        for p in bericht["ohne_adressat"]:
            aus.append(f"  {p['kennung']:<4} {p['posten'][:70]}")
    else:
        aus.append("ADRESSATEN: vollstaendig — jeder offene Posten hat einen.")

    if bericht["ohne_geraetebeweis"]:
        aus.append("")
        aus.append("ERLEDIGT, ABER OHNE ANGABE, WORAUF DER BELEG RUHT:")
        for p in bericht["ohne_geraetebeweis"]:
            aus.append(f"  {p['kennung']:<4} {p['mangel']:<24} {p['posten'][:44]}")
            aus.append(f"       {p['grund'][:100]}")
    else:
        aus.append("BELEGE: jede erledigte Zeile sagt, ob sie im Repo oder am Geraet ruht.")
    return aus


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--repo", default=".", help="Wurzel des Repos (Vorgabe: hier)")
    ap.add_argument("--json", action="store_true", help="maschinenlesbar ausgeben")
    # DIE LISTE KOMMT AUS DEM VERTRAG UND STEHT NICHT NOCH EINMAL HIER.
    #
    # Sie stand hier: `("local", "cloud", "ui")`. Seit dem 28.08.2026 gibt es einen
    # vierten Adressaten (`kern`), und `--worker kern` wurde seither mit «invalid choice»
    # abgewiesen — eine doppelte Vorgabe, die an einer Stelle nachgezogen wurde und an
    # der anderen nicht. Gefunden am 01.09.2026 von `tools/schalterprobe.py`: Der
    # Schalter kam in keiner einzigen Probe vor.
    ap.add_argument("--worker", choices=sorted(auftrag.WORKER),
                    help="nur den Rueckstand eines Adressaten zeigen")
    a = ap.parse_args(argv)

    bericht = einbau.bericht(a.repo)
    if a.json:
        print(json.dumps(bericht, ensure_ascii=False, indent=1))
    else:
        print("\n".join(_zeilen(bericht, a.worker)))
    return 0 if bericht["bereit"] else 1


if __name__ == "__main__":                                   # pragma: no cover
    raise SystemExit(main())
