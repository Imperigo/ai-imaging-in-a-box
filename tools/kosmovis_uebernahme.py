"""KOSMOVIS-ÜBERNAHME — das Vis-Werkzeug von KosmoOrbit, unverändert herüberkopiert.

Owner-Entscheid E26 (24.09.2026, ``docs/ENTSCHEIDE_VISBOX_2026-09-18.md``): Das Vis-Werkzeug
kommt als **Kopie** herüber, wird bis Februar hier weiterbearbeitet und geht dann nahtlos
zurück. *Nahtlos* heisst: Man kann jederzeit sagen, was anders ist als im Original.

Darum kopiert dieses Werkzeug **nur**, was in :data:`WOERTLICH` steht, an **denselben Pfad**
unter ``kosmovis/`` wie unter ``kosmo-orbit/`` im Original, und schreibt je Datei den
SHA-256 in ``kosmovis/HERKUNFT.json``. Alles, was ausserhalb des Vis-Werkzeugs liegt und
gebraucht wird, ist ein **Stellvertreter** — von Hand geschrieben, in
``kosmovis/HERKUNFT.json`` unter ``stellvertreter`` geführt, und nie von hier überschrieben.

Gebrauch::

    python tools/kosmovis_uebernahme.py <pfad-zu/kosmo-orbit> --commit <sha>
    python tools/kosmovis_uebernahme.py --pruefen      # stimmt jede Kopie noch?

``--pruefen`` endet mit 1, sobald eine wörtliche Kopie vom festgehaltenen Abdruck abweicht.
Eine Änderung an einer Kopie ist erlaubt — aber dann gehört die Datei aus :data:`WOERTLICH`
in die Liste ``geaendert`` von ``HERKUNFT.json``, mit Grund. *Eine stille Änderung an einer
Kopie ist genau das, was die Rückkehr im Februar unmöglich macht.*
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ZIEL = REPO / "kosmovis"
HERKUNFT = ZIEL / "HERKUNFT.json"
QUELLE_REPO = "Imperigo/Architektur-Cosmos"
QUELLE_WURZEL = "kosmo-orbit"

APP = "apps/kosmo-orbit/src"

#: Was wörtlich herüberkommt — Pfade und Muster relativ zu ``kosmo-orbit/``. Der Schnitt ist
#: am 24.09.2026 bestimmt (Protokoll 71 §6): das Vis-Werkzeug, was nur ihm dient, und was
#: in sich geschlossen ist und darum nicht nachgebaut werden muss.
WOERTLICH = (
    # Das Vis-Werkzeug selbst
    f"{APP}/modules/vis/**",
    # Was nur dem Vis-Werkzeug dient oder ohne weitere Abhängigkeit mitkommt
    f"{APP}/shell/governance-speicher.ts",
    f"{APP}/state/research-profil.ts",
    f"{APP}/state/project-store.ts",
    f"{APP}/state/fremd-aenderung.ts",
    f"{APP}/state/cursor-zustand.ts",
    f"{APP}/state/touch-undo.ts",
    f"{APP}/zod-jitless.ts",
    # Die Hülle, in der jede Station steht: Stationsfarbe an `.app-wurzel`, die Schriften
    f"{APP}/app.css",
    f"{APP}/fonts.css",
    "apps/kosmo-orbit/public/fonts/*.woff2",
    "apps/kosmo-orbit/public/fonts/README.md",
    # Die Insel-Bühne, auf der das Vis-Werkzeug steht (ohne die Inhalte des Design-Moduls)
    f"{APP}/modules/design/island/IslandShell.tsx",
    f"{APP}/modules/design/island/island.css",
    f"{APP}/modules/design/island/insel-ruhe.ts",
    f"{APP}/modules/design/island/insel-stufe.tsx",
    f"{APP}/modules/design/island/island-katalog.ts",
    f"{APP}/modules/design/island/island-glyphen.tsx",
    f"{APP}/modules/design/island/inhalte/registry.ts",
    f"{APP}/modules/design/werkzeug-icons.tsx",
    # Die gemeinsamen Einstellungen des TypeScript-Übersetzers
    "tsconfig.base.json",
    "packages/kosmo-kernel/tsconfig.json",
    "apps/kosmo-orbit/tsconfig.json",
    # Die Bausteine der Oberfläche und die Verträge — ganz, beide nur mit React bzw. zod
    "packages/kosmo-ui/**",
    "packages/kosmo-contracts/**",
    # Der dünne Kern: Datenmodell, Befehle, der Vis-Graph, Bildnachbearbeitung
    "packages/kosmo-kernel/src/model/doc.ts",
    "packages/kosmo-kernel/src/model/entities.ts",
    "packages/kosmo-kernel/src/model/ids.ts",
    "packages/kosmo-kernel/src/model/units.ts",
    "packages/kosmo-kernel/src/commands/core.ts",
    "packages/kosmo-kernel/src/commands/vis.ts",
    "packages/kosmo-kernel/src/derive/visgraph.ts",
    "packages/kosmo-kernel/src/derive/render-presets.ts",
    "packages/kosmo-kernel/src/derive/renderprompt.ts",
    "packages/kosmo-kernel/src/bild/farbangleich.ts",
    "packages/kosmo-kernel/src/bild/nachbearbeitung.ts",
    "packages/kosmo-kernel/src/bild/belichtung.ts",
    "packages/kosmo-kernel/src/bild/uebernahme.ts",
)

#: Die Proben des Originals, die das Vis-Werkzeug prüfen und hier unverändert laufen
#: (ausgewählt am 24.09.2026: jede Probe, die das Vis-Werkzeug nennt, deren Importe in der
#: Kopie aufgehen und die hier grün ist). Sie laufen mit ``npm test`` in ``kosmovis/``.
PROBEN = (
    "apps/kosmo-orbit/test/a10-uebernahme-oberflaeche.test.tsx",
    "apps/kosmo-orbit/test/a15-fremdnaht-bild.test.ts",
    "apps/kosmo-orbit/test/a15-render-knotenhoehe.test.tsx",
    "apps/kosmo-orbit/test/a21-knotenplatz-ganz-im-bild.test.ts",
    "apps/kosmo-orbit/test/auf-20260827-62-qa-vorbehalt.test.tsx",
    "apps/kosmo-orbit/test/auf-20260901-70-wartet-grund.test.tsx",
    "apps/kosmo-orbit/test/b148-zahl-traegt-ihre-bedingung.test.tsx",
    "apps/kosmo-orbit/test/backbone-eine-liste.test.ts",
    "apps/kosmo-orbit/test/befundsicht-rho-maske-kante.test.ts",
    "apps/kosmo-orbit/test/blender-label.test.ts",
    "apps/kosmo-orbit/test/g5-graph-palette-streifen-deckel.test.ts",
    "apps/kosmo-orbit/test/knoten-zoom.test.ts",
    "apps/kosmo-orbit/test/n2-qa-je-kamera.test.ts",
    "apps/kosmo-orbit/test/n3-status-und-nullprobe.test.ts",
    "apps/kosmo-orbit/test/n4-qa-je-kamera-zuleitung.test.ts",
    "apps/kosmo-orbit/test/node-canvas-pan.test.tsx",
    "apps/kosmo-orbit/test/node-canvas-pointer-cancel.test.tsx",
    "apps/kosmo-orbit/test/node-canvas-render-done.test.tsx",
    "apps/kosmo-orbit/test/node-canvas-tastatur-auswahl.test.tsx",
    "apps/kosmo-orbit/test/node-canvas-tastatur-rollfokus.test.tsx",
    "apps/kosmo-orbit/test/p-b69-knotenplatz-ausserhalb-hinweis.test.tsx",
    "apps/kosmo-orbit/test/p-bescheid-bridge.test.ts",
    "apps/kosmo-orbit/test/p-bilddeckel-meldung.test.ts",
    "apps/kosmo-orbit/test/p-graphstart-leerer-graph.test.tsx",
    "apps/kosmo-orbit/test/p-kamera-vorschlagen-sagt-es.test.tsx",
    "apps/kosmo-orbit/test/p-knotenfeld-kamera-vorschlagen.test.tsx",
    "apps/kosmo-orbit/test/p-knotenfeld-knotenplatz.test.ts",
    "apps/kosmo-orbit/test/p-knotenfeld-zweitkante-meldung.test.tsx",
    "apps/kosmo-orbit/test/p-zweitkante-zwei-kanten-ein-durchgang.test.tsx",
    "apps/kosmo-orbit/test/p16-beiblatt-im-fenster.test.ts",
    "apps/kosmo-orbit/test/p3-nicht-zustaendig-inspektor.test.tsx",
    "apps/kosmo-orbit/test/p3-quelle-aus-lauf.test.ts",
    "apps/kosmo-orbit/test/varianten-diff.test.ts",
    "apps/kosmo-orbit/test/vis-ansichten-ui.test.tsx",
    "apps/kosmo-orbit/test/vis-glyphen.test.tsx",
    "apps/kosmo-orbit/test/vis-graph-loeschen-bedienweg.test.tsx",
    "apps/kosmo-orbit/test/vis-island-katalog.test.ts",
    "apps/kosmo-orbit/test/vis-island-registry.test.ts",
    "apps/kosmo-orbit/test/vis-island-runtime.test.ts",
    "apps/kosmo-orbit/test/vis-legende-infos.test.ts",
    "apps/kosmo-orbit/test/vis-node-canvas-hooks-ordnung.test.tsx",
    "apps/kosmo-orbit/test/vis-runtime-ansichten.test.ts",
    "apps/kosmo-orbit/test/w2-belichtung-ueberlebt.test.tsx",
    "packages/kosmo-kernel/test/a10-uebernahme.test.ts",
    "packages/kosmo-kernel/test/b-belichtung-leeres-bild.test.ts",
    "packages/kosmo-kernel/test/vis-render.test.ts",
)

#: Was trotz Muster NICHT herüberkommt.
AUSGESCHLOSSEN = (
    "**/node_modules/**",
    "**/dist/**",
    "**/*.tsbuildinfo",
    *(f"packages/kosmo-ui/test/{n}" for n in (
        "fokusring-token.test.ts", "insel-scroll-waechter.test.ts",
        "plangrafik-papier-waechter.test.ts", "schriftgrad-waechter.test.ts",
        "skizze-geladen.test.ts", "zeilenhoehe-skala.test.ts",
    )),
)

#: Was im Arbeitsbereich entsteht und nie verbucht wird.
NIE_VERBUCHT = ("HERKUNFT.json", "package-lock.json")

#: Proben, die bewusst NICHT mitkommen — mit Grund. Wird in ``HERKUNFT.json`` festgehalten,
#: damit die Rückkehr im Februar weiss, welche Prüfung hier fehlte.
NICHT_UEBERTRAGEN = {
    "packages/kosmo-ui/test/{fokusring-token,insel-scroll-waechter,plangrafik-papier-waechter,"
    "schriftgrad-waechter,skizze-geladen,zeilenhoehe-skala}.test.ts":
        "Wächter über die ganze KosmoOrbit-App (lesen Dateien wie PlanView.tsx, main.tsx, "
        "Companion.tsx) — die gibt es in der Kopie nicht.",
    "apps/kosmo-orbit/test/{a2-vis-bedienung,b117-weg-b-uebergangshinweis,"
    "e76-unbekannte-felder-parsejob,n1-vis-jobs-referenzpunkt,p-b117-schritt2-interior-transport,"
    "p-dreistandpunkte,p-leerszene-render-sperre,p5b-bridge-toast-bescheid,"
    "pc2-vis-render-executor,vis-preset-job}.test.ts":
        "Bauen ein Gebäude im KosmoOrbit-Kern und erwarten daraus ein glb. Der Stellvertreter "
        "exportGlb liefert nur das glb der offenen Mappe — ohne Mappe sagt er es, statt ein "
        "leeres Modell zu senden. Kommt mit der Mappen-Anbindung als eigene Visbox-Probe.",
    "apps/kosmo-orbit/test/{research-profil-wache,kernmodule-angeschlossen,css-var-konsistenz,"
    "insel-scroll-e10,pb2-laufplaene,p-geometriezaehlung}.test.ts(x)":
        "Prüfen Stellen ausserhalb des Vis-Werkzeugs (Einstellungen, Kosmo-Werkzeuge, "
        "Bauteil-Szene, Laufpläne der ganzen App).",
    "packages/kosmo-kernel/test/bild-farbe.test.ts":
        "Vorlagen sind Ausschnitte aus einem Renderbild unbekannter Herkunft — Regel 3.",
    "packages/kosmo-kernel/test/kamera3ds-uebernahme.test.ts":
        "Vorlage ist ein Ausschnitt aus einem Projektmodell — Regel 3.",
    "packages/kosmo-kernel/test/{kamera-und-presets,linienfarben-zaehlung,oereb-auszug,"
    "p-elementkopie-artenabdeckung,standort-setzen}.test.ts":
        "Prüfen den Architekturkern von KosmoOrbit (Kameras aus Bauteilen, Planlinien, "
        "Standort), der nicht mitkommt.",
}


def _passt(pfad: str, muster: str) -> bool:
    if muster.startswith("**/") and muster.endswith("/**"):
        return f"/{muster[3:-3]}/" in f"/{pfad}"
    if muster.endswith("/**"):
        return pfad.startswith(muster[:-3] + "/")
    return fnmatch.fnmatch(pfad, muster)


def _abdruck(datei: Path) -> str:
    return hashlib.sha256(datei.read_bytes()).hexdigest()


def auswahl(quelle: Path) -> list[str]:
    """Alle Dateien unter ``quelle``, die :data:`WOERTLICH` trifft — sortiert."""
    treffer = []
    for datei in sorted(quelle.rglob("*")):
        if not datei.is_file():
            continue
        rel = datei.relative_to(quelle).as_posix()
        if any(_passt(rel, m) for m in AUSGESCHLOSSEN):
            continue
        if any(_passt(rel, m) for m in WOERTLICH) or rel in PROBEN:
            treffer.append(rel)
    return treffer


def kopiere(quelle: Path, commit: str) -> dict:
    quelle = quelle.resolve()
    dateien = auswahl(quelle)
    fehlend = [m for m in (*WOERTLICH, *PROBEN) if not any(_passt(d, m) for d in dateien)]
    if fehlend:
        raise SystemExit(f"Nicht gefunden in der Quelle: {fehlend}")
    alt = json.loads(HERKUNFT.read_text(encoding="utf-8")) if HERKUNFT.exists() else {}
    abdruecke = {}
    for rel in dateien:
        ziel = ZIEL / rel
        ziel.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(quelle / rel, ziel)
        abdruecke[rel] = _abdruck(ziel)
    herkunft = {
        "quelle": {"repo": QUELLE_REPO, "wurzel": QUELLE_WURZEL, "commit": commit},
        "entscheid": "E26, docs/ENTSCHEIDE_VISBOX_2026-09-18.md",
        "woertlich": abdruecke,
        "geaendert": alt.get("geaendert", {}),
        "stellvertreter": alt.get("stellvertreter", {}),
        "eigen": alt.get("eigen", {}),
        "nicht_uebertragen": NICHT_UEBERTRAGEN,
    }
    HERKUNFT.write_text(json.dumps(herkunft, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8")
    return herkunft


def pruefe() -> list[str]:
    """Jede wörtliche Kopie gegen ihren Abdruck — zurück kommen die Abweichungen."""
    herkunft = json.loads(HERKUNFT.read_text(encoding="utf-8"))
    befunde = []
    for rel, abdruck in herkunft["woertlich"].items():
        datei = ZIEL / rel
        if not datei.is_file():
            befunde.append(f"{rel}: fehlt")
        elif rel not in herkunft.get("geaendert", {}) and _abdruck(datei) != abdruck:
            befunde.append(f"{rel}: weicht vom Original ab, steht aber nicht unter 'geaendert'")
    for rel in herkunft.get("stellvertreter", {}):
        if not (ZIEL / rel).is_file():
            befunde.append(f"{rel}: Stellvertreter fehlt")
    # Umgekehrt: keine Datei ohne Herkunft. Eine unverbuchte Datei ist beim Zurückführen
    # weder Original noch Stellvertreter — genau die Lücke, die still bleibt.
    bekannt = {*herkunft["woertlich"], *herkunft.get("stellvertreter", {}),
               *herkunft.get("geaendert", {})}
    eigen = tuple(herkunft.get("eigen", {}))
    for datei in sorted(ZIEL.rglob("*")):
        rel = datei.relative_to(ZIEL).as_posix()
        if (not datei.is_file() or rel in bekannt or rel in NIE_VERBUCHT
                or any(_passt(rel, m) for m in (*eigen, *AUSGESCHLOSSEN))):
            continue
        befunde.append(f"{rel}: ohne Herkunft (weder wörtlich, Stellvertreter noch eigen)")
    return befunde


def main(argv=None) -> int:
    teil = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    teil.add_argument("quelle", nargs="?", help="Pfad zu kosmo-orbit/ im Original")
    teil.add_argument("--commit", help="Commit des Originals, aus dem kopiert wird")
    teil.add_argument("--pruefen", action="store_true")
    a = teil.parse_args(argv)
    if a.pruefen:
        befunde = pruefe()
        for b in befunde:
            print(b)
        print("Alle Kopien stimmen." if not befunde else f"{len(befunde)} Abweichungen.")
        return 1 if befunde else 0
    if not a.quelle or not a.commit:
        teil.error("Quelle und --commit sind nötig (oder --pruefen).")
    h = kopiere(Path(a.quelle), a.commit)
    print(f"{len(h['woertlich'])} Dateien wörtlich kopiert aus {QUELLE_REPO}@{a.commit[:9]}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
