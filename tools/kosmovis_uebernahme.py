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
    python tools/kosmovis_uebernahme.py --abgleich <pfad-zu/kosmo-orbit> [--ref <git-ref>] [--holen]

``--pruefen`` endet mit 1, sobald eine wörtliche Kopie vom festgehaltenen Abdruck abweicht.
Eine Änderung an einer Kopie ist erlaubt — aber dann gehört die Datei aus :data:`WOERTLICH`
in die Liste ``geaendert`` von ``HERKUNFT.json``, mit Grund. *Eine stille Änderung an einer
Kopie ist genau das, was die Rückkehr im Februar unmöglich macht.*

``--abgleich`` (Plan UI-Gleichheit S5, 21.10.2026) fragt das Gegenteil: nicht «stimmt die Kopie
mit ihrem Abdruck?», sondern «stimmt sie mit dem **aktuellen** KosmoOrbit?». Gelesen wird über
``git`` (``ls-tree``/``show``), ohne Checkout: Vorgabe ist der Integrator-Zweig, zusätzlich zählen
die eigenen Zweige ``claude/kosmovis-*`` — eine Datei, die dort geändert und bei Int 1 noch nicht
eingespielt ist, ist kein Abweichen, sondern ein angemeldeter Weg. Endet mit 1, sobald eine Datei
abweicht, dort fehlt oder hier fehlt. *Ein Wächter, der nur gegen den eigenen Abdruck prüft, sieht
nie, dass das Original weitergegangen ist.*
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import shutil
import subprocess
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
    # Runde 26 (14.10.2026): was die neue Fassung zusätzlich braucht und in sich geschlossen
    # ist — die Trackpad-Geste (E152: zwei Finger schieben, Pinch zoomt, auch in WebKit),
    # die Tastennamen und die Bausteine der Insel-Bühne (Kreismenü, Gruppenschiene).
    f"{APP}/shell/trackpad-geste.ts",
    f"{APP}/modules/design/navigation-geste.ts",
    f"{APP}/shell/tastennamen.ts",
    f"{APP}/modules/design/hinweis-lage.ts",
    # Die Hülle, in der jede Station steht: Stationsfarbe an `.app-wurzel`, die Schriften
    f"{APP}/app.css",
    f"{APP}/fonts.css",
    "apps/kosmo-orbit/public/fonts/*.woff2",
    "apps/kosmo-orbit/public/fonts/README.md",
    # Schritt W (Bauplan «Neue Knoten», 21.10.2026): die Vorschaubilder der Himmel und Materialien
    # (CC0, verkleinert, mit quellen.json) — Vite nimmt `publicDir: '../kosmo-orbit/public'`.
    "apps/kosmo-orbit/public/vis/**",
    # Die Insel-Bühne, auf der das Vis-Werkzeug steht (ohne die Inhalte des Design-Moduls)
    f"{APP}/modules/design/island/IslandShell.tsx",
    f"{APP}/modules/design/island/island.css",
    f"{APP}/modules/design/island/insel-ruhe.ts",
    f"{APP}/modules/design/island/insel-stufe.tsx",
    f"{APP}/modules/design/island/island-katalog.ts",
    f"{APP}/modules/design/island/island-glyphen.tsx",
    f"{APP}/modules/design/island/inhalte/registry.ts",
    f"{APP}/modules/design/island/leiste-lage.ts",
    f"{APP}/modules/design/island/kreismenue.tsx",
    f"{APP}/modules/design/island/gruppenschiene-haeufigkeit.ts",
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
    # K-10 (Owner-Entscheid 22.10.2026): die Kartenzeile «Werte statt Feldnamen» der Vis-Befehle —
    # in sich geschlossen (nur visgraph, varianten, render-presets).
    "packages/kosmo-kernel/src/derive/vis-kartenzeile.ts",
    # Knoten «Umfeld» (24.10.2026, eigener Zweig claude/kosmovis-ausstattung): Kategorien, Wunsch, Katalog-Kopie
    # des Heim-PC (tests/test_umfeld_katalog.py hält beide gleich) — in sich geschlossen (nur Datenmodell-Typen).
    "packages/kosmo-kernel/src/derive/umfeld.ts",
    "packages/kosmo-kernel/src/derive/render-presets.ts",
    "packages/kosmo-kernel/src/derive/renderprompt.ts",
    "packages/kosmo-kernel/src/bild/farbangleich.ts",
    "packages/kosmo-kernel/src/bild/nachbearbeitung.ts",
    "packages/kosmo-kernel/src/bild/belichtung.ts",
    "packages/kosmo-kernel/src/bild/uebernahme.ts",
    # Runde 26: Fundstellen (Typ im Datenmodell) und die Texturkacheln der Textur-Insel,
    # samt dem Materialkatalog, aus dem sie ihre Rezepte nimmt.
    "packages/kosmo-kernel/src/fundstelle.ts",
    "packages/kosmo-kernel/src/derive/textur.ts",
    # Bild aufs Blatt (21.10.2026): Pixelgroesse aus dem Dateikopf, fuer die Druckaufloesung (Stellvertreter derive/sheet.ts).
    "packages/kosmo-kernel/src/derive/bildgroesse.ts",
    # Bild aufs Blatt: Wiederfinden eines abgelegten Bilds ueber seine Herkunft (abgelegtesBild).
    "packages/kosmo-kernel/src/derive/bildherkunft.ts",
    "packages/kosmo-data/src/materialkatalog.ts",
    "packages/kosmo-data/tsconfig.json",
    # Runde 29 (14.10.2026): Knoten «Kamera aus 3D-Ansicht». Die Rechnung im Kern (Blickfeld
    # horizontal, Bestellformat) und der Store der 3D-Ansicht — beide in sich geschlossen (nur
    # `derive/kamera` bzw. zustand). In Visbox meldet nie eine 3D-Ansicht eine Kamera; der Knoten
    # sagt dann «Keine 3D-Ansicht offen».
    "packages/kosmo-kernel/src/derive/kamera-aus-3d.ts",
    f"{APP}/state/viewport-kamera.ts",
    # L24 Bildweg Varianten (E246, Owner-Entscheide 92/92a/92b, 15.10.2026): die Rechnung der
    # drei Achsen und der Ebenenfilter fuer «Entwurf = Ebenenkombination» — beide in sich
    # geschlossen (nur Modell, Kamera-Stellvertreter und `kamera-aus-3d`). In Visbox gibt es
    # keine Ebenenkombinationen; der Entwurf ist dort immer «Aktuelles Modell».
    "packages/kosmo-kernel/src/derive/varianten.ts",
    "packages/kosmo-kernel/src/derive/ebenen.ts",
    # Nr. 85 Paket 2 auf R36/R37 (20.10.2026): was die kopierten Dateien seither zusaetzlich
    # lesen — alle vier in sich geschlossen (nur Typen aus dem Datenmodell bzw. zustand): der
    # Ableitungs-Cache je Bauteil (R35, `ebenen.ts`), die Bestandsmarke (`ebenen.ts`), der
    # Liftschutz (`commands/core.ts`) und die Punktanfrage der Splat-Ebene (`IslandShell.tsx`).
    "packages/kosmo-kernel/src/derive/ableitungs-cache.ts",
    "packages/kosmo-kernel/src/derive/bestand-marke.ts",
    "packages/kosmo-kernel/src/model/lift-schutz.ts",
    f"{APP}/state/splat-punkt-anfrage.ts",
    # R37: der Store merkt Skizzen, die ein Agent anlegt (`project-store.ts`) — ohne Import.
    f"{APP}/state/agent-skizzen.ts",
    # KOPFTEILE (Entscheide 115/116, Plan UI-Gleichheit S1/S2, 20.10.2026): was in KosmoOrbit am
    # Programm-Wirt (`App.tsx` unter `bodenDockAusgeblendet`, `main.tsx`) ueber der Vis-Station
    # steht. Die Nahtstellen fuer Visbox liegen in KosmoOrbit (Zweig `claude/kosmovis-kopf`:
    # `registrierePalettenQuelle`, wahlfreie Handgriffe, `chip`, `ausklapper`); was die Dateien
    # darueber hinaus aus dem Programm lesen, sind Stellvertreter (HERKUNFT.json).
    f"{APP}/shell/werkzeug-palette/WerkzeugPalette.tsx",
    f"{APP}/shell/werkzeug-palette/werkzeug-palette.ts",
    f"{APP}/shell/werkzeug-palette/werkzeug-palette.css",
    f"{APP}/shell/speichern-kreis/SpeichernKreis.tsx",
    f"{APP}/shell/speichern-kreis/speichern-kreis.css",
    f"{APP}/modules/design/island/InselKopf.tsx",
    f"{APP}/state/autosave-text.ts",
    f"{APP}/shell/tauri-desktop.ts",
    # S2: Claude-Marke mit Karten, Erzaehlzeile, Fensterrahmen der Vollautomatik und die Coop-Teile
    # (Modus-Schalter, «Im Projekt», Verlauf). Den Zustand fuettert in Visbox die Mac-App
    # (`window.visboxWirt.lage`) und der KI-Werkzeugsatz der Seite — Stellvertreter
    # `state/claude-anschluss.ts`, `state/kosmo-coop.ts`.
    f"{APP}/shell/claude-anschluss/ClaudeAnschluss.tsx",
    f"{APP}/shell/claude-anschluss/ClaudeFensterRahmen.tsx",
    f"{APP}/shell/claude-anschluss/ErzaehlZeile.tsx",
    f"{APP}/shell/claude-anschluss/erzaehl-zeile.ts",
    f"{APP}/shell/claude-anschluss/fusszone.ts",
    f"{APP}/shell/claude-anschluss/claude-anschluss.css",
    f"{APP}/shell/kosmo-maus/KosmoCoop.tsx",
    f"{APP}/shell/kosmo-maus/kosmo-maus.css",
    f"{APP}/state/claude-taetigkeit.ts",
    f"{APP}/state/kosmo-maus-freigabe.ts",
    f"{APP}/state/coop-marke.ts",
    # S3 (Plan UI-Gleichheit, Entscheide 115/116 (2), 20.10.2026): die Kugel der Insel-Stationen und
    # der Kopf des Gespraechsfelds — wortgleich bis auf den Namen, den der Wirt ueber die Nahtstelle
    # `registriereKosmoName` anmeldet («Assistent», `state/kosmo-name.ts`, Zweig `claude/kosmovis-kopf`).
    # Den Rumpf des Felds (`KosmoPanel.tsx`, 10 000 Zeilen mit Kosmos Motor) traegt ein Stellvertreter
    # mit derselben Anatomie (`.kp-panel`), der mit dem Visbox-Assistenten spricht.
    f"{APP}/modules/design/island/KosmoOrb.tsx",
    f"{APP}/shell/kosmo-eck-orb/**",
    f"{APP}/shell/kosmo-fenster/KosmoKopfOrb.tsx",
    f"{APP}/shell/kosmo-fenster/kosmo-fenster.css",
    f"{APP}/shell/kosmo-fenster/orb-ursprung.ts",
    f"{APP}/shell/kosmo-panel.css",
    f"{APP}/shell/chat/KosmoMarke.tsx",
    f"{APP}/shell/chat/kosmo-c0-kopf.css",
    f"{APP}/shell/chat/use-seitenfenster-breit.ts",
    f"{APP}/modules/prepare/baum/KosmoFragtKarte.tsx",
    f"{APP}/modules/prepare/baum/kosmo-fragt.css",
    f"{APP}/state/kosmo-status.ts",
    f"{APP}/state/kosmo-name.ts",
    # S4: die Einstellungs-Insel — Schale, «Darstellung», «Anzeige», der Rahmen von «Bewegung &
    # Klang» und der Rueckgaengig-Schalter (`einstellungen-teile.tsx`, Nahtstelle auf
    # `claude/kosmovis-kopf`), ihr CSS und die Akzente. Die Abschnitte, die es nur in Visbox gibt
    # (Heim-PC, «Wer rechnet?», Claude ueber MCP), stehen im Wirt (`apps/visbox-knoten`).
    f"{APP}/shell/einstellungen-teile.tsx",
    f"{APP}/shell/einstellungen.css",
    f"{APP}/shell/orbit-065.css",
    f"{APP}/shell/akzente.ts",
    # KI-BEDIENUNG STUFE 6 (Plan `docs/PLAN_KI_BEDIENUNG_2026-10-20.md`, 21.10.2026): Blick und Maus
    # — KosmoBlick (Lagebild als Text, fuer Claude mit Bild) und KosmoMaus (eine eigene Maus der KI,
    # mit Sperrzonen), samt Figur, Leiste, Schaltern «Mitschauen»/«Bedienen». Die Nahtstellen
    # (`registriereSperrzone`, `registriereAppName`, Sperrzonen fuer Varianten-Freigabe, Loeschen und
    # Kennwoerter) liegen auf `claude/kosmovis-kopf`. Was die Dateien darueber hinaus aus dem Programm
    # lesen (Coop-Wache, Projektwechsel, Station, Dateien von der Platte, Modus-Satz), sind
    # Stellvertreter (HERKUNFT.json).
    f"{APP}/state/kosmo-maus.ts",
    f"{APP}/state/kosmo-maus-ereignisse.ts",
    f"{APP}/state/kosmo-blick-live.ts",
    f"{APP}/state/normansicht.ts",
    f"{APP}/state/harmlose-fensterhinweise.ts",
    f"{APP}/state/maus-karten-im-panel.ts",
    f"{APP}/shell/kosmo-maus/KosmoMausEbene.tsx",
    f"{APP}/shell/kosmo-maus/KosmoMausSchalter.tsx",
    f"{APP}/shell/kosmo-maus/AgentFigur.tsx",
    f"{APP}/shell/kosmo-maus/agent-figur.css",
    f"{APP}/shell/zeiger-bilder.ts",
    f"{APP}/shell/werkzeug-glyphen.tsx",
    f"{APP}/shell/stations-werkzeuge.ts",
    # Nachzug auf Int 1 R63 (24.10.2026, Protokoll 74): Int 1 hat die Insel-Bausteine ohne App-Stores in ein
    # eigenes Paket gezogen («gemeinsame Quelle fuer KosmoOrbit und Visbox» — Navi-Insel, Erzaehlzeile,
    # Tastennamen, Kosmo-Name; nur React und @kosmo/ui), und `state/kosmo-maus.ts` liest die Lauf-Schritt-Marke
    # (in sich geschlossen, ohne Import).
    "packages/kosmo-insel/**",
    f"{APP}/state/lauf-schritt-marke.ts",
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
    "apps/kosmo-orbit/test/kv-deckung-schwelle.test.ts",
    "apps/kosmo-orbit/test/kv-kartenzeile.test.ts",
    "apps/kosmo-orbit/test/kv-letzter-lauf.test.tsx",
    "apps/kosmo-orbit/test/kv-r56-etikett-leerlauf.test.tsx",
    "apps/kosmo-orbit/test/kv-freigabe-voll.test.ts",
    "apps/kosmo-orbit/test/kv-vorschau-vorbehalt.test.tsx",
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
    # Runde 26 (14.10.2026), nach derselben Regel: nennt das Vis-Werkzeug (oder die
    # Trackpad-Geste), die Importe gehen in der Kopie auf, und sie ist hier grün.
    "apps/kosmo-orbit/test/bridge-bescheid-cors.test.ts",
    "apps/kosmo-orbit/test/fortschritt-render-knoten.test.tsx",
    "apps/kosmo-orbit/test/fortschritt-sonne.test.tsx",
    "apps/kosmo-orbit/test/fortschritt-vis-bild.test.tsx",
    "apps/kosmo-orbit/test/kv-b5-nachgang.test.tsx",
    "apps/kosmo-orbit/test/kv-b5-render-knoten-html-ebene.test.tsx",
    # Mac-Demolauf 0.3.33 (22.10.2026): «Freigeben» sagt am Knoten, warum es nicht geht, und ein
    # wartender Auftrag sperrt «Grundlage rendern» nicht.
    "apps/kosmo-orbit/test/kv-freigabe-ohne-grundlage.test.tsx",
    "apps/kosmo-orbit/test/kv-lieferstatus-null.test.tsx",
    "apps/kosmo-orbit/test/kv-nicht-beurteilbar.test.tsx",
    "apps/kosmo-orbit/test/kv-qa-hinweise.test.tsx",
    "apps/kosmo-orbit/test/kv-qa-status.test.ts",
    "apps/kosmo-orbit/test/kv-render-verlauf.test.tsx",
    "apps/kosmo-orbit/test/kv-saetze-am-bild.test.tsx",
    "apps/kosmo-orbit/test/kv-urteil-echt.test.tsx",
    "apps/kosmo-orbit/test/kv-vergleich-schmal.test.tsx",
    # Owner-Fund 22.10.2026 (Mac 0.3.33): Knotenschrift schrumpft beim Rauszoomen mit (R1.2).
    "apps/kosmo-orbit/test/kv-zoom-schrift.test.ts",
    "apps/kosmo-orbit/test/p11-b6-fehlergrund-sichtbar.test.tsx",
    "apps/kosmo-orbit/test/trackpad-geste.test.ts",
    "apps/kosmo-orbit/test/u11-ctrl-texte.test.ts",
    "apps/kosmo-orbit/test/vis-belichten-oberflaeche.test.tsx",
    "apps/kosmo-orbit/test/vis-farbangleich-oberflaeche.test.tsx",
    "apps/kosmo-orbit/test/vis-island-textur.test.tsx",
    "apps/kosmo-orbit/test/vis-textur-bild.test.ts",
    "apps/kosmo-orbit/test/vis-textur-material.test.ts",
    # Entscheid 90 (14.10.2026): der Modell-Knoten mit Lade-Faehigkeit des Wirts.
    "apps/kosmo-orbit/test/kv-modell-laden.test.tsx",
    # Entscheid 91/92 (14.10.2026): der fertige Anfang, Bild-Referenz im Vergleich,
    # Samples-Vorrang, «Noch geladen», Standpunkte des Heim-PCs an der Auto-Kamera.
    "apps/kosmo-orbit/test/kv-startgraph.test.tsx",
    # Entscheide 95/95a (14.10.2026): der Knoten «Skizze vom iPad» mit Skizzen-Quelle des Wirts.
    "apps/kosmo-orbit/test/kv-skizze-vom-ipad.test.tsx",
    # Entscheid 96 (15.10.2026): die Skizze fuehrt das Bild — Eingang und Zeile «Skizze» am Knoten.
    "apps/kosmo-orbit/test/kv-skizze-fuehrt-knoten.test.tsx",
    # Nr. 85 Paket 2 (20.10.2026): vis.render traegt Grundlage und Startwert — nur Vis-Befehle.
    "packages/kosmo-kernel/test/kv-grundlage-vis-render.test.ts",
    # Fehler-Nachgang 20.10.2026 (Owner am Mac): Fokus im eigenen Rand der Felder im Knotenkoerper.
    # (`kv-variante-ohne-modell` bleibt drueben: es baut Waende mit `design.*`-Befehlen, die die
    # Kopie nicht traegt — wie `kv-grundlage-auftrag`.)
    "apps/kosmo-orbit/test/kv-fehler-fokusring.test.ts",
    # F1 (Entscheid 109 A, 20.10.2026): das kleine 3D-Fenster (Kern und Huelle) und sein Einbau
    # in den Modell-Knoten. three kommt dafuer als Abhaengigkeit des Stellvertreters mit.
    "apps/kosmo-orbit/test/kv-modell-3d-kern.test.ts",
    "apps/kosmo-orbit/test/kv-modell-3d-fenster.test.tsx",
    "apps/kosmo-orbit/test/kv-modell-knoten-3d.test.tsx",
    # Owner-Befund am Mac (20.10.2026): gesicherte Graphen beim Laden einmal entzerren, nur bei
    # echter Ueberlappung (`modules/vis/knoten-entzerren.ts`, gerufen von `graph-sichern.ts`).
    "apps/kosmo-orbit/test/kv-knoten-entzerren.test.ts",
    # KI-Bedienung Stufe 3 (Entscheide 105–106f, 108, 114, 20.10.2026): der KI-Werkzeugsatz der
    # Knotenansicht (`modules/vis/ki-werkzeuge.ts`, kommt mit `modules/vis/**`) — Liste, Karte,
    # Paket, graph_lesen und der eigene KI-Verlauf. Nur Vis-Befehle, darum hier grün.
    "apps/kosmo-orbit/test/kv-ki-werkzeuge.test.ts",
    # Entscheid 146 (24.10.2026): Rendern ohne Karte in «Voll», wenn der Wirt es erlaubt.
    "apps/kosmo-orbit/test/kv-ki-voll-render.test.ts",
    # S3/S4 (20.10.2026): die Nahtstellen fuer den Namen und die Einstellungs-Teile — je der
    # Visbox-Fall und der Gegenbeleg «ohne Wirt wie bisher».
    "apps/kosmo-orbit/test/kv-kopf-s3s4-nahtstellen.test.tsx",
    # Entscheid 117a (W-4, 21.10.2026): Grundbild neben dem KI-Bild — Regeln, Poll, Knoten und grosse Ansicht.
    # (`kv-nebeneinander` mit der Bestellung bleibt drueben: es baut Waende mit `design.*`.)
    "apps/kosmo-orbit/test/kv-nebeneinander-knoten.test.tsx",
    # R45 (Entscheid 104a, 21.10.2026): der Vermerk «Vorschau» auch an Kuratier-Karte, Vergleich,
    # Inspektor, Bildkachel und Blatt-Knoten — nur Vis-Teile, darum hier gruen.
    "apps/kosmo-orbit/test/guete-marke-kuratier.test.tsx",
    # KI-Bedienung Stufe 6 (21.10.2026): die Sperrzonen der KosmoMaus im Vis-Werkzeug (Render- und
    # Varianten-Freigabe, Loeschen, Kennwoerter), die Nahtstellen und die sichtbaren Sperrzonen.
    "apps/kosmo-orbit/test/kv-maus-sperrzonen.test.tsx",
    # Bauplan «Neue Knoten» (21.10.2026, Schritte C/D/E): die Koerper von Stimmung, Kamera,
    # Oberflaeche, Material und Farbpalette und was sie bestellen — nur Vis-Teile und der Vertrag.
    "apps/kosmo-orbit/test/kv-knoten-neu.test.tsx",
    # Blatt 36 (21.10.2026): die Bildzeile des Varianten-Knotens (Daumen, Blaettern, gross, waehlen)
    # und die gleiche Kartenhoehe in jedem Zustand — nur Vis-Befehle, darum hier gruen.
    "apps/kosmo-orbit/test/kv-varianten-daumen.test.tsx",
    # Nachzug auf Int 1 R63 (24.10.2026): «1 Bild» (eigener Zweig claude/kosmovis-einzahl) und die Proben, die Int 1
    # seit dem letzten Nachzug am Vis-Werkzeug dazugelegt hat (Modus-Marke, «Graph entfernt» aus R62).
    "apps/kosmo-orbit/test/kv-einzahl.test.ts",
    "apps/kosmo-orbit/test/modus-marke.test.ts",
    "apps/kosmo-orbit/test/modus-marke-einbau.test.tsx",
    "apps/kosmo-orbit/test/modus-marke-gross.test.tsx",
    "apps/kosmo-orbit/test/vis-graph-entfernt.test.tsx",
    # Ebene ueber der Leinwand (24.10.2026, eigener Zweig claude/kosmovis-overlay-ebene): Legende, Kuratier-Knopf
    # und -Flaeche liegen ausserhalb der gezoomten Welt in einem eigenen Stapel — der Bau, ohne Zeichnen (jsdom).
    # Die Trefferprobe mit elementFromPoint fuer Visbox steht in tools/ueber_leinwand_probe.py.
    "apps/kosmo-orbit/test/kv-ueber-leinwand.test.tsx",
    # Knoten «Umfeld» (24.10.2026, eigener Zweig claude/kosmovis-ausstattung): Katalog, Wunsch, vis.umfeldSetzen,
    # Grundlage-Stand, KI-Einteilung, Körper; das Senden braucht den Entwurf (hier sichtbar übersprungen).
    "apps/kosmo-orbit/test/kv-umfeld.test.tsx",
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
        # Runde 26: zählen Verbraucher der Dauer- und Ebenen-Tokens über ALLE Stationen
        "bewegung-dauer-leiter.test.ts", "ebenen-leiter.test.ts",
    )),
    # REGEL 3 (14.10.2026): traegt Pfade unter /home/<name>/ als Beispiel — ein Benutzername
    # in einem Pfad darf hier nicht stehen (tests/test_regel3_kennungen.py).
    "packages/kosmo-contracts/test/kv-splat-context.test.ts",
    # Runde 29: vergleichen das JSON-Schema fuer Prepare Zeichen fuer Zeichen mit der Ausgabe
    # von zod — und die haengt an der zod-Fassung (s. NICHT_UEBERTRAGEN).
    "packages/kosmo-contracts/test/bestand-aus-netz.test.ts",
    "packages/kosmo-contracts/test/punktwolke.test.ts",
)

#: Was im Arbeitsbereich entsteht und nie verbucht wird.
NIE_VERBUCHT = ("HERKUNFT.json", "package-lock.json")

#: Proben, die bewusst NICHT mitkommen — mit Grund. Wird in ``HERKUNFT.json`` festgehalten,
#: damit die Rückkehr im Februar weiss, welche Prüfung hier fehlte.
NICHT_UEBERTRAGEN = {
    "packages/kosmo-contracts/test/kv-splat-context.test.ts":
        "Regel 3: Die Probe schreibt Beispielpfade unter /home/<name>/ aus — in Visbox steht kein "
        "Benutzername in einem Pfad. Dem Integrator gemeldet (14.10.2026).",
    "packages/kosmo-ui/test/{fokusring-token,insel-scroll-waechter,plangrafik-papier-waechter,"
    "schriftgrad-waechter,skizze-geladen,zeilenhoehe-skala}.test.ts":
        "Wächter über die ganze KosmoOrbit-App (lesen Dateien wie PlanView.tsx, main.tsx, "
        "Companion.tsx) — die gibt es in der Kopie nicht.",
    "packages/kosmo-ui/test/{bewegung-dauer-leiter,ebenen-leiter}.test.ts":
        "Runde 26: zählen, wie oft die Dauer- und Ebenen-Tokens im CSS der ganzen App gelesen "
        "werden (Untergrenzen wie «mehr als 20 Stellen»). Die Kopie hat nur das CSS des "
        "Vis-Werkzeugs; die Zahl fällt dort unter die Grenze, ohne dass etwas fehlt.",
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
    "apps/kosmo-orbit/test/{kv-blattbild-platz,kv-publish-schritt2,kv-nachgang3,"
    "kv-lizenzmarke-hinweis}.test.ts(x)":
        "Runde 26: legen ein Render-Bild auf ein Blatt (KosmoPublish). Blätter gibt es in "
        "Visbox nicht — der Stellvertreter publish.ts sagt es, statt still nichts zu tun.",
    "apps/kosmo-orbit/test/{kv-k1-felder,kv-nachprobe-230}.test.ts(x)":
        "Runde 26: bauen eine Wand im KosmoOrbit-Kern und erwarten daraus ein glb — wie die "
        "Gruppe oben, deren Modell in Visbox aus der Mappe kommt.",
    "apps/kosmo-orbit/test/kv-e123-ai-variant-parsejob.test.ts":
        "Runde 26: liest localStorage in der Node-Umgebung ohne jsdom-Kopf; in der Kopie "
        "ohne Browserspeicher rot, ohne dass am Vis-Werkzeug etwas anders ist.",
    "packages/kosmo-contracts/test/{bestand-aus-netz,punktwolke}.test.ts":
        "Runde 29: vergleichen die eingecheckten JSON-Schemata fuer Prepare Zeichen fuer Zeichen "
        "mit z.toJSONSchema. Visbox rechnet mit zod 4.6.5, KosmoOrbit mit 4.4.3; die neuere "
        "Fassung schreibt Tupel ohne items/minItems/maxItems. Die Vertraege selbst sind gleich, "
        "die Schemata gehoeren zu Prepare in KosmoOrbit, nicht zum Vis-Werkzeug.",
    "apps/kosmo-orbit/test/kv-skizze-fuehrt.test.ts":
        "Entscheid 96: prueft die Bestellung mit einem Quader aus dem Architekturkern (wie die "
        "Gruppe «Bauen ein Gebäude im KosmoOrbit-Kern»). Den Visbox-Weg prueft "
        "apps/visbox-knoten/test/skizze-fuehrt.test.tsx mit dem glb der Mappe, die Bibliothek "
        "tests/test_skizze_fuehrt.py.",
    "apps/kosmo-orbit/test/kv-bild-aufs-blatt.test.tsx":
        "Bild aufs Blatt (21.10.2026): ein Teil der Proben legt ab und auf ein Blatt (publish.bildAblegen, "
        "KosmoPublish) — beides gibt es in Visbox nicht, der Stellvertreter publish.ts sagt es. Gruen drueben auf "
        "claude/kosmovis-bild-aufs-blatt; den Visbox-Teil (Export, Ausnahme, Sichern-Dialog) prueft "
        "tests/test_bild_aufs_blatt.py.",
    "apps/kosmo-orbit/test/kv-skizze-anweisung.test.ts":
        "Befund F4 (Demolauf 24.10.2026): prueft die Bestellung mit einem Quader aus dem Architekturkern (wie "
        "kv-skizze-fuehrt). Den Visbox-Weg prueft apps/visbox-knoten/test/skizze-anweisung.test.tsx mit dem glb "
        "der Mappe, die Bibliothek tests/test_skizze_anweisung_f4.py.",
    "apps/kosmo-orbit/test/kv-skizze-vom-ipad-blatt.test.tsx":
        "Entscheide 95/95a: legt die Skizze aufs Blatt (KosmoPublish). Blätter gibt es in Visbox "
        "nicht — wie kv-blattbild-platz; der Rest des Knotens kommt mit kv-skizze-vom-ipad.",
    "apps/kosmo-orbit/test/kv-kamera-aus-3d.test.tsx":
        "Runde 29: 16 von 21 Proben laufen hier, fünf nicht — eine lädt eine Splat-Ebene (in "
        "Visbox fest leer, Stellvertreter state/splat-ebene.ts), vier bauen ein Geschoss im "
        "Architekturkern. Den Visbox-Fall (keine 3D-Ansicht, «Keine 3D-Ansicht offen») prüft "
        "apps/visbox-knoten/test/kamera-ohne-3d.test.tsx.",
    "apps/kosmo-orbit/test/viewport-kamera.test.ts":
        "Runde 29: liest die Kamera aus three.js (modules/design/3d/kamera-lesen.ts) — die "
        "3D-Ansicht gibt es in Visbox nicht.",
    "apps/kosmo-orbit/test/kv-grundlage-{auftrag,ergebnis,knoten}.test.ts(x)":
        "Nr. 85 Paket 2 (20.10.2026): bauen eine Wand bzw. das Demohaus im Architekturkern und "
        "erwarten daraus ein glb und einen Modellstand — wie die Gruppe «Bauen ein Gebäude im "
        "KosmoOrbit-Kern». Den Vertrag prueft kv-grundlage.test.ts (Vertraege), den Befehl "
        "kv-grundlage-vis-render.test.ts (Kern); beide laufen hier. Dass ein voller Auftrag seine "
        "neue Grundlage merkt (Mac-Prüfliste 0.3.35), prueft apps/visbox-knoten/test/"
        "grundlage-voller-auftrag.test.ts mit dem glb der Mappe.",
    "apps/kosmo-orbit/test/kv-ki-werkzeuge-schema.test.ts":
        "KI-Bedienung Stufe 3 (20.10.2026): vergleicht die Schemas des KI-Werkzeugsatzes mit "
        "commandTools aus @kosmo/ai — das ist in Visbox ein Stellvertreter. Die Gleichheit ist "
        "drüben belegt (Meldeblatt kosmovis-ki); hier prüft kv-ki-werkzeuge.test.ts die Form "
        "für MCP und die Claude-API.",
    "apps/kosmo-orbit/test/{kv-kopf-nahtstellen,werkzeug-palette,speichern-kreis,inselkopf-erreichbarkeit,"
    "insel-kopf-sync-chip,claude-anschluss,erzaehl-zeile,l71-erzaehl-taetigkeit}.test.ts(x)":
        "Kopfteile (Entscheide 115/116, 20.10.2026): pruefen die Teile mit den Stationen, dem Sync, der "
        "KosmoMaus und dem MCP-Anschluss von KosmoOrbit — in Visbox Stellvertreter. Gruen drueben auf "
        "`claude/kosmovis-kopf`; den Visbox-Einsatz prueft apps/visbox-knoten/test/kopf.test.tsx, die "
        "Abdeckung tests/test_kosmovis_ui_gleichheit.py.",
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


#: Der Stand, gegen den ``--abgleich`` ohne ``--ref`` prüft: der Zweig von KosmoOrbit Int 1.
INTEGRATOR_REF = "origin/claude/kosmo-orbit-v1-build-pzxkbj"
#: Die eigenen Zweige im KosmoOrbit-Repo (Owner-Entscheid 65): Was dort geändert ist und bei Int 1
#: noch nicht, darf die Kopie schon tragen.
EIGENE_REFS = "refs/remotes/origin/claude/kosmovis-*"


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True,
                          text=True).stdout


def _baum(repo: Path, ref: str, praefix: str) -> dict[str, str]:
    """Pfad (relativ zu ``kosmo-orbit/``) → Blob-Kennung, für alle Dateien von ``ref``."""
    roh = subprocess.run(["git", "-C", str(repo), "ls-tree", "-r", "-z", "--full-tree", ref,
                          "--", praefix or "."], check=True, capture_output=True).stdout
    baum = {}
    for zeile in roh.decode("utf-8").split("\0"):
        if not zeile:
            continue
        kopf, pfad = zeile.split("\t", 1)
        art, blob = kopf.split()[1:3]
        if art == "blob" and pfad.startswith(praefix):
            baum[pfad[len(praefix):]] = blob
    return baum


def _blob_kennung(datei: Path) -> str:
    """Die Kennung, die git dem Inhalt gäbe — so vergleicht sich die Kopie mit ``ls-tree``."""
    inhalt = datei.read_bytes()
    return hashlib.sha1(b"blob %d\0" % len(inhalt) + inhalt).hexdigest()


def _ist_probe(rel: str) -> bool:
    return "/test/" in f"/{rel}"


def abgleich(quelle: Path, ref: str | None = None, eigene: bool = True,
             ziel: Path | None = None) -> dict:
    """Die wörtliche Kopie gegen einen KosmoOrbit-Stand aus git (Plan UI-Gleichheit S5).

    Zurück kommt ein Bericht: ``abweichend`` (Inhalt anders, mit Grund), ``fehlt_dort`` (die
    Kopie führt die Datei, der Stand nicht), ``fehlt_hier`` (ein Muster aus :data:`WOERTLICH`
    oder eine Probe aus :data:`PROBEN` trifft dort eine Datei, die die Kopie nicht führt) — alle
    drei lassen ``--abgleich`` mit 1 enden. Dazu, nur zur Kenntnis: ``eigen`` (auf einem eigenen
    Zweig geändert, bei Int 1 noch nicht), ``vermerkt`` (unter ``geaendert`` mit Grund) und
    ``neu_dort`` (seit dem Quell-Commit der Kopie neu, in einem Ordner, aus dem die Kopie
    wörtlich führt, oder eine neue Probe, die das Vis-Werkzeug nennt)."""
    ziel = ZIEL if ziel is None else Path(ziel)
    herkunft = json.loads((ziel / "HERKUNFT.json").read_text(encoding="utf-8"))
    quelle = Path(quelle).resolve()
    repo = Path(_git(quelle, "rev-parse", "--show-toplevel").strip())
    praefix = _git(quelle, "rev-parse", "--show-prefix").strip()
    ref = ref or INTEGRATOR_REF
    stand = _git(repo, "rev-parse", f"{ref}^{{commit}}").strip()
    t_ref = _baum(repo, stand, praefix)

    # EIGENE ZWEIGE: Als «eigen» gilt eine Datei nur, wenn ein Commit des Zweigs sie anfasst, der
    # weder im geprüften Stand noch beim Integrator liegt. Sonst hiesse jede Integrator-Änderung,
    # die ein Hilfszweig nur nachgezogen hat, beim Abgleich gegen einen älteren Stand «eigen».
    nicht = [stand]
    try:
        nicht.append(_git(repo, "rev-parse", "--verify", "--quiet",
                          f"{INTEGRATOR_REF}^{{commit}}").strip())
    except subprocess.CalledProcessError:
        pass
    zweige = []                         # (Name, Baum des Zweigs, Baum der Gabelung, eigene Pfade)
    if eigene:
        for name in _git(repo, "for-each-ref", "--format=%(refname:short)", EIGENE_REFS).split():
            try:
                gabel = _git(repo, "merge-base", stand, name).strip()
            except subprocess.CalledProcessError:
                continue
            angefasst = {z[len(praefix):] for z in _git(
                repo, "log", "--format=", "--name-only", name, "--not", *nicht, "--",
                praefix or ".").splitlines() if z.startswith(praefix) and z}
            if angefasst:
                zweige.append((name, _baum(repo, name, praefix), _baum(repo, gabel, praefix),
                               angefasst))

    woertlich = herkunft["woertlich"]
    geaendert = herkunft.get("geaendert", {})
    bericht = {"ref": ref, "commit": stand, "gleich": 0, "abweichend": [], "fehlt_dort": [],
               "fehlt_hier": [], "eigen": [], "vermerkt": [], "neu_dort": []}
    for rel in woertlich:
        if rel in geaendert:
            bericht["vermerkt"].append(rel)
            continue
        datei = ziel / rel
        if not datei.is_file():
            bericht["abweichend"].append((rel, "fehlt in der Kopie (s. --pruefen)"))
            continue
        hier, dort = _blob_kennung(datei), t_ref.get(rel)
        if hier == dort:
            bericht["gleich"] += 1
            continue
        eigen = beidseitig = None
        for name, t_zweig, t_gabel, angefasst in zweige:
            z, g = t_zweig.get(rel), t_gabel.get(rel)
            if hier == z and rel in angefasst:    # der eigene Zweig hat genau das geändert
                if dort == g:
                    eigen = name
                    break
                beidseitig = beidseitig or name
        if eigen:
            bericht["eigen"].append((rel, eigen))
        elif beidseitig:
            bericht["abweichend"].append((rel, f"auf {beidseitig} und dort geändert"))
        elif dort is None:
            bericht["fehlt_dort"].append(rel)
        else:
            bericht["abweichend"].append((rel, "Inhalt anders"))

    gefuehrt = {*woertlich, *herkunft.get("stellvertreter", {}), *geaendert}
    eigen_muster = tuple(herkunft.get("eigen", {}))
    for rel in sorted(t_ref):
        if rel in gefuehrt or any(_passt(rel, m) for m in (*AUSGESCHLOSSEN, *eigen_muster)):
            continue
        if rel in PROBEN or any(_passt(rel, m) for m in WOERTLICH):
            bericht["fehlt_hier"].append(rel)

    # NEU DORT: nur, was seit dem Quell-Commit der Kopie dazukam — sonst stünde hier jede Datei,
    # die bewusst nicht mitkommt (der Rest der KosmoOrbit-App liegt in denselben Ordnern).
    seit = herkunft.get("quelle", {}).get("commit", "")
    try:
        t_seit = _baum(repo, seit, praefix) if seit else None
    except subprocess.CalledProcessError:
        t_seit = None
    if t_seit is None:
        bericht["neu_dort_ohne_bezug"] = True
    else:
        ordner = {rel.rsplit("/", 1)[0] for rel in woertlich if "/" in rel and not _ist_probe(rel)}
        for rel in sorted(set(t_ref) - set(t_seit)):
            if rel in gefuehrt or rel in bericht["fehlt_hier"]:
                continue
            if _ist_probe(rel):
                text = _git(repo, "show", f"{stand}:{praefix}{rel}")
                if "modules/vis" in text:
                    bericht["neu_dort"].append((rel, "neue Probe, nennt modules/vis"))
            elif "/" in rel and rel.rsplit("/", 1)[0] in ordner:
                bericht["neu_dort"].append((rel, "neu in einem Ordner der Kopie"))
    return bericht


def abgleich_befunde(bericht: dict) -> int:
    """Wie viele Befunde den Abgleich rot machen."""
    return len(bericht["abweichend"]) + len(bericht["fehlt_dort"]) + len(bericht["fehlt_hier"])


def holen(quelle: Path) -> None:
    """Die Zweige, gegen die abgeglichen wird, frisch holen — ein Klon, der nur den
    Integrator-Zweig holt (``remote.origin.fetch`` eng), hätte sonst alte eigene Zweige."""
    _git(Path(quelle), "fetch", "--quiet", "origin",
         f"+refs/heads/{INTEGRATOR_REF.removeprefix('origin/')}:refs/remotes/{INTEGRATOR_REF}",
         "+refs/heads/claude/kosmovis-*:refs/remotes/origin/claude/kosmovis-*")


def drucke_abgleich(bericht: dict) -> None:
    print(f"Abgleich gegen {bericht['ref']} ({bericht['commit'][:9]}): "
          f"{bericht['gleich']} gleich, {len(bericht['eigen'])} auf eigenem Zweig, "
          f"{len(bericht['vermerkt'])} vermerkt geändert.")
    for rel, grund in bericht["abweichend"]:
        print(f"abweichend: {rel} — {grund}")
    for rel in bericht["fehlt_dort"]:
        print(f"fehlt dort: {rel}")
    for rel in bericht["fehlt_hier"]:
        print(f"fehlt hier: {rel}")
    for rel, zweig in bericht["eigen"]:
        print(f"eigener Zweig: {rel} — {zweig}")
    for rel, grund in bericht["neu_dort"]:
        print(f"neu dort: {rel} — {grund}")
    if bericht.get("neu_dort_ohne_bezug"):
        print("neu dort: nicht bestimmt — der Quell-Commit der Kopie fehlt in diesem Klon.")
    n = abgleich_befunde(bericht)
    print("Die Kopie stimmt mit dem Stand." if not n else f"{n} Abweichungen gegen den Stand.")


def main(argv=None) -> int:
    teil = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    teil.add_argument("quelle", nargs="?", help="Pfad zu kosmo-orbit/ im Original")
    teil.add_argument("--commit", help="Commit des Originals, aus dem kopiert wird")
    teil.add_argument("--pruefen", action="store_true")
    teil.add_argument("--abgleich", metavar="KOSMO_ORBIT",
                      help="die Kopie gegen einen KosmoOrbit-Stand aus git vergleichen")
    teil.add_argument("--ref", help=f"Stand für --abgleich (Vorgabe {INTEGRATOR_REF})")
    teil.add_argument("--ohne-eigene", action="store_true",
                      help="eigene Zweige claude/kosmovis-* beim Abgleich nicht gelten lassen")
    teil.add_argument("--holen", action="store_true", help="vor dem Abgleich git fetch")
    a = teil.parse_args(argv)
    if a.abgleich:
        if a.holen:
            holen(Path(a.abgleich))
        bericht = abgleich(Path(a.abgleich), a.ref, eigene=not a.ohne_eigene)
        drucke_abgleich(bericht)
        return 1 if abgleich_befunde(bericht) else 0
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
