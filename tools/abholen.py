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

**Frage 4 — welche Ablage?** Seit dem 26.08. gibt es zwei. Die Bruecke (``--store``)
traegt, was die Vis-Oberflaeche bestellt; unsere eigene Ablage (``--eigener-store``),
was ueber den MCP-Einlass aus KosmoOrbit hereinkommt. Bis dahin las **niemand** die
zweite: Ein Knoten im Cockpit konnte einen Render bestellen, der Auftrag ging auf
``queued``, und dort blieb er.

Beide werden nacheinander abgegangen, jede mit ihrer eigenen Quelle — und **welche gerade
dran ist, steht in der Ausgabe**. Ein Auftrag, der auf dem einen Weg liegen bleibt, waere
sonst von einem auf dem anderen nicht zu unterscheiden.

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

from aiimaging import (abholer, bruecke, eigene_quelle, fortschritt,  # noqa: E402
                        render, tiefenschaetzer)

#: Ab welcher Auslastung die Karte als BESCHAEFTIGT gilt. Nicht 0 %: `nvidia-smi` meldet
#: auch im Leerlauf gelegentlich 1-2 %, und ein Abholer, der darauf wartet, laeuft nie.
#:
#: **Diese Zahl entscheidet seit dem 01.09.2026 nichts mehr allein** — sie steht in der
#: Begruendung und nicht mehr im Riegel. Warum, steht in `karte_auskunft`.
LAST_GRENZE_PROZENT = 10
#: Ab wie viel belegtem Speicher wir jemanden anderen am Werk vermuten. Der Desktop
#: allein braucht rund 1 GiB; ein geladenes Sprachmodell mehr als 15.
SPEICHER_GRENZE_MIB = 4096


def karte_auskunft() -> tuple[bool, str]:
    """(darf_rechnen, Begruendung) aus ``nvidia-smi`` — fail-closed.

    **Was am 01.09.2026 gemessen wurde, und warum die Auslastung ihren Riegel verlor.**

    Demolauf 12 blieb 24 Durchgaenge lang an dieser Funktion stehen, woertlich
    *«Karte: NICHT frei — Auslastung 12 % (Grenze 10 %)»*. Die Last kam von der
    Oberflaeche, die den Auftrag gestellt hatte. Danach nachgemessen, alles auf dieser
    Maschine, `nvidia-smi` als Instrument:

    ======================================================  ==========  ==============
    Zustand                                                 Auslastung  belegt
    ======================================================  ==========  ==============
    Schreibtisch, kein Browser (20 Proben)                  0-4 %       1077 MiB
    Messbrowser auf der Startseite (16 Proben)              1 %         +9 MiB
    Messbrowser, 3D-Ansicht mit 11515 Meshen (40 Proben)    3-4 %       +10..20 MiB
    dieselbe Ansicht, waehrend sie gedreht wird             9-16 %      +10..20 MiB
    ein laufender Render (Demolauf 10, gemessen)            bis 100 %   29676 MiB
    ======================================================  ==========  ==============

    **Die Auslastung trennt nicht, was getrennt werden muss.** Ein Fenster, das gemalt
    wird, und ein Modell, das rechnet, stehen bei ihr im selben Band — 12 % kann beides
    sein. Der Speicher trennt sauber: Malen kostet **zehn bis zwanzig MiB**, Rechnen
    **Gigabyte**. Und der Speicher ist auch das, worum der Render wirklich konkurriert;
    er braucht 23,4 GiB am Stueck (`render.GERAETE_ZUSCHLAG`, Registry-Zahl), Rechenzeit
    teilt er sich klaglos.

    Der Beleg aus derselben Reihe, an dem sich das entscheidet: Lauf 11 kam durch dieses
    Tor (5 % Auslastung) und starb danach am **Speicher**; Lauf 12 wurde von diesem Tor
    gestoppt, obwohl der Speicher reichte (+102 MiB Kopf). Das Tor lag zweimal falsch,
    und zwar in beide Richtungen.

    Darum entscheidet hier der **Speicher**, und die Auslastung wird gemessen, genannt
    und nicht mehr zum Riegel gemacht.

    **Was diese Fassung ausdruecklich NICHT faengt** — damit es niemand fuer gefangen
    haelt: eine fremde Arbeit, die die Karte auslastet und dabei **wenig** Speicher
    haelt (ein Videoencoder etwa). Sie wuerde hier durchgelassen. Gemessen wurde ein
    solcher Fall auf dieser Maschine nicht; er steht hier als bekannte Luecke und nicht
    als Vermutung, dass es sie nicht gibt.
    """
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
    if speicher >= SPEICHER_GRENZE_MIB:
        return False, (f"{speicher} MiB belegt (Grenze {SPEICHER_GRENZE_MIB}) — es haelt "
                       f"jemand Gewichte auf der Karte. Auslastung dabei {last} %.")
    if last >= LAST_GRENZE_PROZENT:
        # Kein Riegel mehr, aber auch nicht verschwiegen: Wer das Journal liest, soll
        # sehen, dass die Karte beschaeftigt war UND warum das hier nichts aendert.
        return True, (f"Auslastung {last} % (ueber {LAST_GRENZE_PROZENT} %), aber nur "
                      f"{speicher} MiB belegt (Grenze {SPEICHER_GRENZE_MIB}) — "
                      f"beschaeftigt, nicht belegt. Es wird gerechnet.")
    return True, f"Auslastung {last} %, {speicher} MiB belegt."


class EinmalGeladen:
    """Ein Modell je Name — beim ersten Gebrauch geladen, danach **behalten**.

    **Der Befund, aus dem das entstand (01.09.2026, an dieser Maschine gemessen).**
    :func:`aiimaging.render.rendere` laedt sein Modell, wenn ihm keines uebergeben wird —
    und der Betrieb hat ihm nie eines uebergeben. Also lud es **je Aufruf** neu, und ein
    Auftrag ist viele Aufrufe: je Kamera einer, je Seed einer. Was dabei herauskommt,
    steht in zwei Zeilen einer Messung mit ``torch.cuda.mem_get_info()``::

        Runde 1: weg=cuda                     frei vorher  30476 -> nachher   7464 MiB
        Runde 2: weg=cuda+schichtauslagerung  frei vorher   7464 -> nachher   7465 MiB

    Der zweite Ladevorgang findet eine Karte vor, die der **erste** noch haelt. Er
    entscheidet sich darum gegen den vollen Weg und fuer die Auslagerung — und die
    Auslagerung ist der Weg, auf dem seit dem 25.08.2026 *«Expected all tensors to be on
    the same device»* steht. Genau dieser Fehler beendete Demolauf 11 (Kamera ``s``) und
    den Nachlauf von Demolauf 12 (Kamera ``sSE``, nachdem Kamera ``s`` ihr Bild
    geschrieben hatte).

    **Der Renderer konkurrierte also mit sich selbst.** Nicht mit dem Messbrowser (der
    haelt gemessene 10 bis 20 MiB), nicht mit dem Schreibtisch (rund 1 GiB) — mit der
    Kamera davor. Ein VRAM-Kopf von +1436 MiB (Lauf 10), -266 MiB (Lauf 11) oder
    +102 MiB (Lauf 12) entscheidet nur, ob schon der **erste** Ladevorgang faellt; der
    zweite faellt so oder so.

    **Warum hier und nicht in der Bibliothek.** Wie lange ein Prozess 23 GiB Gewichte
    festhaelt, ist eine Betriebsfrage — dieselbe Art Frage wie *«gilt die fremde
    Freigabe»* und *«ist die Karte frei»*. Eine Bibliothek, die von sich aus ein Modell
    in einer Modulvariablen behaelt, nimmt jedem Aufrufer diese Entscheidung ab, ohne
    ihn zu fragen. Die Naht dafuer gibt es laengst (``_render_modell``,
    ``_tiefen_modell`` in :func:`aiimaging.abholer.verarbeiter`) — sie war nur nie
    bedient.

    Args:
        lader: ``(name, wurzel) -> modell``, also :func:`aiimaging.render.lade_modell`
            oder :func:`aiimaging.tiefenschaetzer.lade_modell`.
        name_schluessel: unter welchem Schluessel der Modellname im Parametersatz steht
            (``backbone`` beim Bildmodell, ``schaetzer`` beim Tiefenschaetzer).
        wurzel_schluessel: wo die Gewichte liegen, falls der Parametersatz es sagt.
            ``None`` heisst: immer die Vorgabe des Laders.

    Die Angaben ueber den Geraeteweg (``geraet``, ``ladeweg``, ``entflechtung``) werden
    vom zuletzt benutzten Modell **uebernommen**, weil :func:`render._geraeteweg` sie am
    uebergebenen Objekt abliest. Ohne das stuende im Protokoll *«fuehrt keine
    Geraeteangabe»* — und das hiesse UNBEKANNT, wo etwas Bekanntes dasteht.
    """

    def __init__(self, lader, name_schluessel: str, wurzel_schluessel: str | None = None):
        self._lader = lader
        self._name_schluessel = name_schluessel
        self._wurzel_schluessel = wurzel_schluessel
        self._modelle: dict = {}
        #: Wie oft wirklich geladen wurde. Steht im Bericht — eine Zahl groesser als die
        #: Zahl der Backbones waere der Rueckfall in genau den Fehler oben.
        self.ladungen = 0
        self.geraet = None
        self.ladeweg = None
        self.entflechtung = None

    def __call__(self, parameter: dict):
        name = parameter.get(self._name_schluessel)
        wurzel = parameter.get(self._wurzel_schluessel) if self._wurzel_schluessel else None
        schluessel = (name, str(wurzel) if wurzel else None)
        modell = self._modelle.get(schluessel)
        if modell is None:
            modell = self._lader(name, wurzel)
            self._modelle[schluessel] = modell
            self.ladungen += 1
        # Vom zuletzt benutzten Modell uebernehmen, nicht vom ersten: Bei zwei Backbones
        # in einem Lauf gehoerte sonst der Weg des einen zum Bild des anderen.
        self.geraet = getattr(modell, "geraet", None)
        self.ladeweg = getattr(modell, "ladeweg", None)
        self.entflechtung = getattr(modell, "entflechtung", None)
        return modell(parameter)


#: Wieviel Text eine Zeile traegt, bevor gekuerzt wird.
GEKUERZT_AUF = 160


def _gekuerzt(text: str, laenge: int = GEKUERZT_AUF) -> str:
    """Auf ganze Woerter kuerzen und das Kuerzen sichtbar machen.

    **Der Anlass ist eine Beobachtung am eigenen Ausgabetext** (HomeStation,
    `auf-vis-20260824-12`): Die Zeilen wurden bei 150 Zeichen **mitten im Wort**
    abgeschnitten — bei 15 von 15 Kameras. Ein abgeschnittenes Wort sieht wie ein Fehler
    aus, und das Fehlen des Restes sieht nach gar nichts aus.
    """
    text = str(text).strip()
    if len(text) <= laenge:
        return text
    schnitt = text[:laenge].rsplit(" ", 1)[0].rstrip(" ,;:-")
    return f"{schnitt} … (+{len(text) - len(schnitt)} Zeichen)"


def main(argv=None) -> int:
    """Der Einstieg — und ``argv`` ist seit dem 01.09.2026 ein Parameter.

    **Es war keiner, und das ist der Grund, warum drei Schalter nie geprüft wurden.**
    ``--stil``, ``--seeds`` und ``--ohne-nullprobe`` kamen in keiner einzigen Probe vor
    (`tools/schalterprobe.py`), und sie konnten es nicht: Ohne ``argv`` liest
    ``parse_args()`` die Kommandozeile des Testlaufs, und die trägt die Schalter von
    pytest. Jedes andere Werkzeug hier nimmt ``argv`` entgegen.

    *Ein Einstieg, den keine Probe aufrufen kann, hat keine ungeprüften Schalter — er ist
    selbst einer.* Die Vorgabe ``None`` ändert am Dienstbetrieb nichts.
    """
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--store", default="/tmp/kosmo-jobs",
                    help="Ablageort der Auftraege der BRUECKE (Vorgabe: /tmp/kosmo-jobs)")
    ap.add_argument("--out-wurzel", dest="out_wurzel", default=None,
                    help="Wohin die BILDER geschrieben werden — ein Ordner je Auftrag darunter, "
                         "benannt wie der Auftrag. Ohne Angabe schreibt der Lauf dorthin, wo der "
                         "Auftrag liegt. ANLASS (01.09.2026): am 28.08. lief die Kette zum ersten "
                         "Mal ganz durch und schrieb drei Bilder — nach /tmp/kosmo-jobs, weil die "
                         "Bruecke auf Port 8600 bewusst dort ablegt. Der naechste Neustart nahm sie "
                         "mit. Zehn Laeufe bis zum ersten Bild, und es ueberlebte den Tag nicht. "
                         "Der Weg dahinter war schon gebaut und getestet (abholer.verarbeiter), "
                         "nur nicht bedienbar.")
    ap.add_argument("--eigener-store", dest="eigener_store", default=None,
                    help="Zusaetzlich unsere EIGENE Ablage abgehen — dorthin schreibt "
                         "der MCP-Einlass (werkzeuge.enqueue_render), also ein Knoten in "
                         "KosmoOrbit. Vorgabe: AUS. Ohne Angabe bleibt ein so "
                         "bestellter Render liegen, und bis zum 26.08.2026 war das der "
                         "einzige Zustand, den es gab. Ueblich: "
                         "/tmp/aiimaging-jobs (oder $AIIMAGING_JOB_DIR).")
    ap.add_argument("--fremde-freigabe", action="store_true",
                    help="Die Freigabe der fremden Bruecke gelten lassen. Betreiber-Entscheid.")
    ap.add_argument("--hoechstens", type=int, default=None,
                    help="Hoechstens so viele Auftraege in diesem Durchgang.")
    ap.add_argument("--stil", default=None, help="Stil fuer die Belichtungspruefung.")
    ap.add_argument("--seeds",
                    default=",".join(str(s) for s in abholer.VORGABE_SEEDS),
                    help="Kommagetrennte Seeds. Mehr als einer heisst: alle rendern und "
                         "den besten nach 'gerichtet' behalten (Polaritaet x rho ueber "
                         "der Bauwerksmaske). Ohne Maske wird NICHT ausgewaehlt. "
                         "Voreinstellung aus abholer.VORGABE_SEEDS — abgeschrieben "
                         "waere sie an einer der beiden Stellen bereits falsch.")
    ap.add_argument("--gelaende-z", dest="gelaende_z", type=float, default=None,
                    help="Hoehe des Gelaendes im Weltsystem, in Metern. OHNE Angabe "
                         "rechnet die Kamera mit der Huellbox-Unterkante — bei einem "
                         "Bauwerk mit Untergeschoss steht sie damit im Keller, und die "
                         "Kompositionspruefung meldet den unzuverlaessigen Bezugspunkt "
                         "bei jeder Kamera. Aus einer glb ist der Stand nicht zu "
                         "erfahren; wer ihn kennt, sagt ihn hier.")
    ap.add_argument("--kein-gelaende", dest="kein_gelaende", action="store_true",
                    help="Diese Szene enthaelt gar kein Gelaende. Ein reines "
                         "Gebaeude-IFC bringt keines mit — der eine IfcSite darin traegt "
                         "keine Geometrie und taucht in der Ausgabe nicht auf (an neun "
                         "echten Dateien gemessen, BEFUND_2026-08-24_IFC-LESER.md). Ohne "
                         "diesen Schalter meldet die Maske 'kein Gelaende erkannt', und "
                         "das ist dann ein FEHLALARM: Es fehlt nichts, es war nie welches "
                         "da. Mit dem Schalter erklaert der Aufrufer die Lage, statt dass "
                         "die Maske raet.")
    ap.add_argument("--ohne-nullprobe", action="store_true",
                    help="Die Kontrollanker weglassen. Nicht empfohlen — siehe auf-21.")
    ap.add_argument("--stillstand-frist-s", type=float, default=fortschritt.FRIST_S,
                    help=("Sekunden ohne neue Datei im Ausgabeordner, ab denen ein "
                          "Stillstand berichtet wird. Bricht NICHTS ab. Voreinstellung "
                          "ist uebernommen, nicht gemessen."))
    ap.add_argument("--ohne-wache", action="store_true",
                    help=("Ohne Fortschrittsbeobachtung laufen. Der Bericht sagt dann "
                          "'nicht gemessen' und nicht 'lief durch'."))
    ap.add_argument("--zeitdeckel-s", dest="zeitdeckel_s", type=int, default=None,
                    help="Nach wie vielen Sekunden ein Blender-Lauf abgebrochen wird. "
                         "Ohne Angabe 900 s wie bisher. Gemessen am 26.08.2026 (CPU, "
                         "synthetischer Testbau): Samples kosten fast nichts — bei 400 px "
                         "sind 1 bis 256 Samples flach innerhalb 1 %%, waehrend sich die "
                         "Pixel jedes Mal aendern. Die AUFLOESUNG dominiert (400->1600 px "
                         "ist 4,37->27,80 s), und was daraus auf einer GPU wird, ist "
                         "ungemessen (auf-20260826-54).")
    ap.add_argument("--zwischenspeicher", dest="zwischenspeicher", default=None,
                    help="Ordner fuer den Multipass-Zwischenspeicher. OHNE Angabe AUS — "
                         "ein Gedaechtnis, das niemand bestellt hat, ist die "
                         "unangenehmste Art von Ueberraschung. Mit Angabe wird die "
                         "Geometriestufe je Kamera nur einmal gerechnet, solange glb, "
                         "Kameraeinstellungen und Blender-Fassung gleich bleiben. "
                         "Gemessen am 26.08.2026: 27,7 s -> 0,00 s bei Vertragsvorgaben. "
                         "Der Bericht sagt bei JEDER Kamera, ob sie gerechnet oder "
                         "geholt wurde. NICHT ins Repo legen — die Eintraege tragen "
                         "absolute Pfade (Regel 3).")
    ap.add_argument("--probe", action="store_true",
                    help="Nur berichten, was anlaege: Karte pruefen, offene Auftraege zaehlen.")
    a = ap.parse_args(argv)

    darf, warum = karte_auskunft()
    print(f"Karte: {'frei' if darf else 'NICHT frei'} — {warum}")

    # Die Ablagen dieses Laufs, in der Reihenfolge, in der sie abgegangen werden.
    # Die Bruecke zuerst, weil sie den laengeren Betrieb hinter sich hat.
    ablagen = [("Bruecke", Path(a.store), bruecke)]
    if a.eigener_store:
        ablagen.append(("eigene Ablage (MCP-Einlass)", Path(a.eigener_store), eigene_quelle))

    fehlend = [name for name, pfad, _ in ablagen if not pfad.is_dir()]
    if fehlend:
        # NUR wenn ALLE fehlen ist es ein Abbruch. Eine von zweien fehlt regelmaessig —
        # wer den MCP-Einlass nicht benutzt, hat den Ordner nie angelegt.
        if len(fehlend) == len(ablagen):
            print("Ablageort fehlt: " + ", ".join(str(p) for _, p, _ in ablagen))
            return 2
        for name in fehlend:
            print(f"Ablage '{name}' fehlt — uebersprungen.")
        ablagen = [e for e in ablagen if e[1].is_dir()]

    # REGEL 3: Die Eintraege tragen absolute Pfade. Ein Zwischenspeicher IM Repo landete
    # damit im naechsten Commit — der Waechter `tests/test_regel3_kennungen.py` faende
    # ihn, aber erst danach. Hier faellt es vorher auf.
    speicher = None
    if a.zwischenspeicher:
        ziel = Path(a.zwischenspeicher).resolve()
        repo = Path(__file__).resolve().parent.parent
        if ziel == repo or repo in ziel.parents:
            print(f"Der Zwischenspeicher darf nicht im Repo liegen: {ziel.name} — seine "
                  f"Eintraege tragen absolute Pfade (Regel 3).")
            return 2
        from aiimaging import graph
        speicher = graph.ArtefaktCache(ziel)
        print(f"Zwischenspeicher: {ziel.name} ({len(list(ziel.glob('*.json')))} Eintraege)")

    if a.probe:
        for name, pfad, quelle in ablagen:
            offen = quelle.offene_auftraege(pfad)
            print(f"Offene Auftraege [{name}]: {len(offen)}")
            for o in offen:
                print(f"  {Path(o).name}")
        print(f"Fremde Freigabe gilt: {'ja' if a.fremde_freigabe else 'NEIN — nichts wird gerechnet'}")
        return 0

    seeds = tuple(int(x) for x in a.seeds.split(",") if x.strip())

    # EIN Modell je Prozess statt eines je Bild — siehe `EinmalGeladen`. Beide Nähte
    # werden bedient, weil beide dieselbe Bauform und denselben Fehler haben: Der
    # Tiefenschaetzer wird je Kamera vier- bis fuenfmal gerufen (Bild, drei Nullanker),
    # das Bildmodell je Kamera und Seed.
    render_modell = EinmalGeladen(render.lade_modell, "backbone", "modell_wurzel")
    tiefen_modell = EinmalGeladen(tiefenschaetzer.lade_modell, "schaetzer")

    verarbeite = abholer.verarbeiter(out_wurzel=a.out_wurzel,
                                     stil=a.stil, nullprobe=not a.ohne_nullprobe,
                                     gelaende_z=a.gelaende_z,
                                     gelaende_erwartet=not a.kein_gelaende,
                                     zwischenspeicher=speicher,
                                     zeitdeckel_s=a.zeitdeckel_s,
                                     seeds=seeds or abholer.VORGABE_SEEDS,
                                     _render_modell=render_modell,
                                     _tiefen_modell=tiefen_modell)

    def wache_bauen(auftrag):
        """Eine Wache auf den Ausgabeordner DIESES Auftrags.

        Eine neue Datei dort ist ein **belegtes** Fortschrittszeichen: Sie taucht auf,
        weil etwas fertig geworden ist, und nicht, weil jemand `running` sagt. Der Ordner
        wird gleich angelegt — sonst faende der erste Blick nichts vor und die Uhr liefe
        ab Beginn statt ab dem ersten Zeichen.
        """
        # DIESELBE Rechnung wie der Schreiber — `abholer.ausgabeort` ist die eine Stelle,
        # die sie kennt. Stuende sie hier ein zweites Mal, bewachte die Wache bei gesetztem
        # `--out-wurzel` einen anderen, leeren Ordner als den beschriebenen und meldete
        # Stillstand, waehrend die Bilder daneben entstehen.
        ziel = abholer.ausgabeort(auftrag, a.out_wurzel)
        ziel.mkdir(parents=True, exist_ok=True)
        return fortschritt.wache_fuer_verzeichnis(
            ziel, frist_s=a.stillstand_frist_s,
            name=f"Auftrag {auftrag.get('job_id') or ziel.parent.name}")

    for name, pfad, quelle in ablagen:
        print(f"\n=== Ablage: {name} ===")
        bericht = abholer.durchgang(pfad, verarbeite=verarbeite,
                                    fremde_freigabe_gilt=a.fremde_freigabe,
                                    darf_rechnen=karte_auskunft,
                                    hoechstens=a.hoechstens,
                                    wache_bauen=None if a.ohne_wache else wache_bauen,
                                    quelle=quelle)
        _berichte(bericht)

    # Eine Zahl, die es vorher nicht gab: Wie oft in diesem Durchgang wirklich geladen
    # wurde. Ein Auftrag mit drei Kameras und einem Backbone muss hier 1 stehen haben.
    print(f"\nGeladen: Bildmodell {render_modell.ladungen}x, "
          f"Tiefenschaetzer {tiefen_modell.ladungen}x "
          f"(je Backbone einmal — mehr waere der Rueckfall, s. EinmalGeladen).")
    if render_modell.geraet is not None:
        print(f"Geraeteweg: {render_modell.geraet}"
              + (f", Ladeweg {render_modell.ladeweg}" if render_modell.ladeweg else "")
              + (", Entflechtung noetig" if render_modell.entflechtung else ""))
    return 0


def _berichte(bericht: dict) -> None:
    """Einen Durchgang ausgeben — je Ablage einmal.

    Herausgeloest, als es zwei Ablagen wurden. Zwei Ausgabewege fuer dieselbe Sache
    liefen auseinander, sobald einer gepflegt wird; das ist derselbe Grund, aus dem der
    Abholer eine zweite QUELLE bekam und keinen zweiten Ausfuehrer.
    """
    schlank = {k: v for k, v in bericht.items() if k != "ergebnisse"}
    print(json.dumps(schlank, ensure_ascii=False, indent=1))
    for e in bericht.get("ergebnisse", []):
        kennung = e.get("job_id") or e.get("auftrag") or "?"
        # `tat` UND NICHT `status`. Hier stand `e.get("status", "?")`, und
        # `hole_einen` liefert diesen Schluessel nicht — es liefert `tat`. Jede Zeile
        # dieses Berichts trug darum ein Fragezeichen, seit es ihn gibt; im Journal von
        # Demolauf 12 steht 24 Mal «vis-…: ? — Der Auftrag traegt 'idle_window_only'».
        # Der Grund stand da, der Zustand nicht, und der Vorgabewert des `get` hat den
        # fehlenden Schluessel als Auskunft verkleidet.
        print(f"  {kennung}: {e.get('tat', '?')} — {str(e.get('grund') or e.get('begruendung') or '')[:160]}")
        if e.get("grund_vermerkt") not in (True, None):
            print(f"    Grund NICHT am Auftrag vermerkt: {e['grund_vermerkt']}")
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

        # Der Befund, den der Lauf neben das Vertragsergebnis gelegt hat.
        #
        # GELESEN und nicht bloss geschrieben: Eine Datei, die niemand liest, ist die
        # tote Kante in ihrer geduldigsten Form — sie faellt nie auf, und wenn eines
        # Tages jemand hinsieht, steht seit Monaten Unsinn darin. Hier steht sie zwischen
        # dem Lauf und dem Menschen davor, und damit traegt sie.
        for zeile in abholer.befund_kurz(abholer.lies_befund(e.get("verzeichnis") or "")):
            print(f"    {zeile}")
        # KEIN Deckel mehr. Bis zum 26.08.2026 stand hier `[:3]`, und genau drei
        # Hinweise aus `kosmo_szene.lies_szene` feuerten bei jedem gewoehnlichen Auftrag
        # — sie fuellten alle drei Plaetze. Eine echte, auftragsspezifische Warnung, die
        # im Code SPAETER steht, war damit unsichtbar. Der Deckel hat nicht die
        # Geschwaetzigkeit begrenzt, sondern die Auskunft geloescht.
        #
        # Die drei stehen jetzt als `vertragsvorgaben` woanders (siehe unten), und was
        # hier uebrig bleibt, betrifft wirklich DIESEN Auftrag. Gekuerzt wird die
        # einzelne Zeile, nicht die Liste.
        for warnung in (e.get("warnungen") or ()):
            print(f"    ! {_gekuerzt(str(warnung), GEKUERZT_AUF)}")

    # Was JEDEN Auftrag gleich trifft — einmal pro Lauf und nicht je Auftrag.
    #
    # Eine Zeile, die bei jedem Auftrag wiederkehrt, wird nach dem dritten Mal
    # ueberflogen; dann uebersieht man auch die eine, die zaehlt. Sie verschwindet
    # deshalb nicht — sie steht einmal da, und zwar am Ende, wo sie nichts verdeckt.
    vorgaben = []
    for e in bericht.get("ergebnisse", []):
        for zeile in (e.get("vertragsvorgaben") or ()):
            if zeile not in vorgaben:
                vorgaben.append(zeile)
    if vorgaben:
        print(f"\n  Vertragsvorgaben (betreffen JEDEN Auftrag gleich, {len(vorgaben)}):")
        for zeile in vorgaben:
            print(f"    · {_gekuerzt(str(zeile), GEKUERZT_AUF)}")


if __name__ == "__main__":
    raise SystemExit(main())
