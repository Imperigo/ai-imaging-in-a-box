#!/usr/bin/env python3
"""ABHOLEN — der Betriebs-Einstieg zu :mod:`aiimaging.abholer`.

**Warum diese Datei entsteht.** Am 19.08.2026 lagen zwei vollstaendige Auftraege in
``/tmp/kosmo-jobs/``, einer seit elf Stunden, beide auf ``queued``. Die fremde Oberflaeche
meldete *"wartet auf GPU-Leerlauf"* — bei 0 % Last und 15,5 W. Sie wartete nicht auf die
Karte, sondern auf jemanden, der abholt.

:mod:`aiimaging.abholer` konnte das an jenem Tag bereits vollstaendig: ``verarbeiter()``
baut die Kette, ``durchgang()`` geht den Ablageort ab. **Nur rief es niemand.** Ein Modul,
das nie laeuft, ist von einem fehlenden Modul nicht zu unterscheiden — das ist die Lehre
aus dem kopflosen Scout, der 25 Laeufe lang blind war, und aus den MCP-Schemata, die
stillschweigend verworfen wurden.

Diese Datei ist darum bewusst duenn: Sie trifft **keine** Entscheidung, die der Abholer
schon trifft. Sie beantwortet nur die zwei Fragen, die eine Bibliothek nicht beantworten
darf.

**Frage 1 — gilt die fremde Freigabe?** Die Bruecke praegt ihren ``approval_token``
selbst; er sieht aus wie unserer und bedeutet etwas anderes. Ob er gilt, entscheidet der
Betreiber. Darum ``--fremde-freigabe`` als ausdrueckliches Flag, voreingestellt AUS. Ohne
es bleibt der Auftrag liegen, und der Bericht sagt warum.

**Frage 2 — ist die Karte frei?** ``idle_window_only`` verlangt eine Auskunft ueber die
Grafikkarte. Die kommt hier aus ``nvidia-smi`` — und wenn ``nvidia-smi`` fehlt, schweigt
oder etwas Unlesbares liefert, lautet die Antwort **nein**, nicht "vermutlich schon".
Ungeprueft ist nicht in Ordnung.

**Frage 3 — wo bewegt sich etwas?** Seit dem 21.08. haengt eine Fortschrittswache am
Abholer, aber sie braucht einen Pfad, an dem sich waehrend des Laufs etwas tut. Den kennt
der Betrieb und nicht die Bibliothek: Er haengt daran, wohin dieser Aufruf schreiben
laesst. Darum wird sie hier gebaut, auf den Ausgabeordner des jeweiligen Auftrags.

Sie **bricht nichts ab.** Der erste vollstaendige Lauf am 19.08. brauchte 292,2 s fuer
drei Kameras; eine Frist, die kuerzer waere als ein einzelner Cycles-Lauf, riefe bei
jedem gesunden Auftrag Alarm. Die Voreinstellung von 300 s ist aus dem Altbestand
uebernommen und ausdruecklich **nicht gemessen** — sie steht als Schalter da, damit sie
sich aendern laesst, sobald jemand die laengste Pause zwischen zwei neuen Dateien
wirklich gemessen hat.

REGEL 3: Der Bericht nennt Auftrags-IDs und Dateinamen, keine Benutzerpfade.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from aiimaging import abholer, fortschritt  # noqa: E402

#: Ab welcher Auslastung die Karte als belegt gilt. Nicht 0 %: `nvidia-smi` meldet auch
#: im Leerlauf gelegentlich 1-2 %, und ein Abholer, der darauf wartet, laeuft nie.
LAST_GRENZE_PROZENT = 10
#: Ab wie viel belegtem Speicher wir jemanden anderen am Werk vermuten. Der Desktop
#: allein braucht rund 1 GiB; ein geladenes Sprachmodell mehr als 15.
SPEICHER_GRENZE_MIB = 4096


def karte_auskunft() -> tuple[bool, str]:
    """(darf_rechnen, Begruendung) aus ``nvidia-smi`` — fail-closed."""
    werkzeug = shutil.which("nvidia-smi")
    if not werkzeug:
        return False, "nvidia-smi ist nicht vorhanden — der Zustand der Karte ist unbekannt."
    try:
        roh = subprocess.run(
            [werkzeug, "--query-gpu=utilization.gpu,memory.used", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=15, check=True).stdout.strip()
    except (subprocess.SubprocessError, OSError) as fehler:
        return False, f"nvidia-smi antwortet nicht ({type(fehler).__name__}) — Zustand unbekannt."
    zeile = roh.splitlines()[0] if roh else ""
    teile = [t.strip() for t in zeile.split(",")]
    if len(teile) < 2:
        return False, f"nvidia-smi lieferte nichts Lesbares ({zeile!r}) — Zustand unbekannt."
    try:
        last, speicher = int(teile[0]), int(teile[1])
    except ValueError:
        return False, f"nvidia-smi lieferte keine Zahlen ({zeile!r}) — Zustand unbekannt."
    if last >= LAST_GRENZE_PROZENT:
        return False, f"Auslastung {last} % (Grenze {LAST_GRENZE_PROZENT} %)."
    if speicher >= SPEICHER_GRENZE_MIB:
        return False, (f"{speicher} MiB belegt (Grenze {SPEICHER_GRENZE_MIB}) — es haelt "
                       f"jemand Gewichte auf der Karte.")
    return True, f"Auslastung {last} %, {speicher} MiB belegt."


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--store", default="/tmp/kosmo-jobs",
                    help="Ablageort der Auftraege (Vorgabe: /tmp/kosmo-jobs)")
    ap.add_argument("--fremde-freigabe", action="store_true",
                    help="Die Freigabe der fremden Bruecke gelten lassen. Betreiber-Entscheid.")
    ap.add_argument("--hoechstens", type=int, default=None,
                    help="Hoechstens so viele Auftraege in diesem Durchgang.")
    ap.add_argument("--stil", default=None, help="Stil fuer die Belichtungspruefung.")
    ap.add_argument("--seeds", default="0",
                    help="Kommagetrennte Seeds. Mehr als einer heisst: alle rendern und "
                         "den besten nach 'gerichtet' behalten (Polaritaet x rho ueber "
                         "der Bauwerksmaske). Ohne Maske wird NICHT ausgewaehlt.")
    ap.add_argument("--ohne-nullprobe", action="store_true",
                    help="Die Kontrollanker weglassen. Nicht empfohlen — siehe auf-21.")
    ap.add_argument("--stillstand-frist-s", type=float, default=fortschritt.FRIST_S,
                    help=("Sekunden ohne neue Datei im Ausgabeordner, ab denen ein "
                          "Stillstand berichtet wird. Bricht NICHTS ab. Voreinstellung "
                          "ist uebernommen, nicht gemessen."))
    ap.add_argument("--ohne-wache", action="store_true",
                    help=("Ohne Fortschrittsbeobachtung laufen. Der Bericht sagt dann "
                          "'nicht gemessen' und nicht 'lief durch'."))
    ap.add_argument("--probe", action="store_true",
                    help="Nur berichten, was anlaege: Karte pruefen, offene Auftraege zaehlen.")
    a = ap.parse_args()

    darf, warum = karte_auskunft()
    print(f"Karte: {'frei' if darf else 'NICHT frei'} — {warum}")

    store = Path(a.store)
    if not store.is_dir():
        print(f"Ablageort fehlt: {a.store}")
        return 2

    if a.probe:
        from aiimaging import bruecke
        offen = bruecke.offene_auftraege(store)
        print(f"Offene Auftraege: {len(offen)}")
        for o in offen:
            print(f"  {Path(o).name}")
        print(f"Fremde Freigabe gilt: {'ja' if a.fremde_freigabe else 'NEIN — nichts wird gerechnet'}")
        return 0

    seeds = tuple(int(x) for x in a.seeds.split(",") if x.strip())
    verarbeite = abholer.verarbeiter(stil=a.stil, nullprobe=not a.ohne_nullprobe,
                                     seeds=seeds or (0,))

    def wache_bauen(auftrag):
        """Eine Wache auf den Ausgabeordner DIESES Auftrags.

        Eine neue Datei dort ist ein **belegtes** Fortschrittszeichen: Sie taucht auf,
        weil etwas fertig geworden ist, und nicht, weil jemand `running` sagt. Der Ordner
        wird gleich angelegt — sonst faende der erste Blick nichts vor und die Uhr liefe
        ab Beginn statt ab dem ersten Zeichen.
        """
        ziel = Path(auftrag["ausgabe"])
        ziel.mkdir(parents=True, exist_ok=True)
        return fortschritt.wache_fuer_verzeichnis(
            ziel, frist_s=a.stillstand_frist_s,
            name=f"Auftrag {auftrag.get('job_id') or ziel.parent.name}")

    bericht = abholer.durchgang(store, verarbeite=verarbeite,
                                fremde_freigabe_gilt=a.fremde_freigabe,
                                darf_rechnen=karte_auskunft,
                                hoechstens=a.hoechstens,
                                wache_bauen=None if a.ohne_wache else wache_bauen)
    schlank = {k: v for k, v in bericht.items() if k != "ergebnisse"}
    print(json.dumps(schlank, ensure_ascii=False, indent=1))
    for e in bericht.get("ergebnisse", []):
        kennung = e.get("job_id") or e.get("auftrag") or "?"
        print(f"  {kennung}: {e.get('status', '?')} — {str(e.get('grund') or e.get('begruendung') or '')[:160]}")
        w = e.get("wache")
        if w is None:
            print("    Wache: nicht beobachtet")
        elif not w.get("gemessen"):
            print(f"    Wache: NICHT GEMESSEN — {w.get('detail', '')[:140]}")
        elif w.get("gestanden"):
            print(f"    Wache: STILLSTAND, laengste Pause {w['laengster_stillstand_s']:.0f} s "
                  f"({w['blicke']} Blicke)")
        else:
            print(f"    Wache: kein Stillstand ({w['blicke']} Blicke, laengste Pause "
                  f"{w['laengster_stillstand_s']:.0f} s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
