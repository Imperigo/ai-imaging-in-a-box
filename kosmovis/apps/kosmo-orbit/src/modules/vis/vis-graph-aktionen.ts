import { bestaetigen, melde, meldeFehler } from '@kosmo/ui';
import type { VisGraph } from '@kosmo/kernel';
import { useProject } from '../../state/project-store';
import { basisNodeHoehe, NODE_W } from './NodeCanvas';
import { useVisRuntime } from './vis-runtime';

/**
 * PC1 (`docs/V084-SPEZ.md` §5 W2, C-15) — Extraktion der vier Graph-Aktionen,
 * die bisher als React-Closures in `VisWorkspace.tsx` lebten (`neuerGraph`/
 * `dreiStimmungen`/`kameraVorschlagen`/`nodeHinzu`). Verhalten UNVERÄNDERT
 * (dieselbe Spiral-Platzsuche/Undo-Gruppierung/Koordinaten-Rechnung) — nur
 * ortsneutral gemacht: `VisWorkspace.tsx`s Manuell-Chrome (Bestandsschutz)
 * UND die neuen GRAPH-/STIMMUNG-/AUSTAUSCH-Insel-Inhalte (`island/inhalte/
 * *.tsx`) rufen jetzt dieselben Funktionen, statt die Logik zweimal zu
 * schreiben (Owner-Auftrag «Bestehende Panels/Funktionen wiederverwenden,
 * nichts nachbauen»). Jede Funktion nutzt `useProject.getState()`/
 * `useVisRuntime.getState()` direkt (kein Hook) — aufrufbar aus JEDER
 * Komponente, auch den Registry-Inhalten, die selbst keine Props bekommen.
 */

/** Legt einen neuen, leeren Render-Graphen an und macht ihn zum aktiven —
 *  identisch zum bisherigen `VisWorkspace.tsx`s `neuerGraph()`. */
export function neuerGraphErstellen(): string | undefined {
  const { doc, runCommand } = useProject.getState();
  const graphen = doc.byKind<VisGraph>('visgraph');
  try {
    const res = runCommand('vis.graphErstellen', { name: `Graph ${graphen.length + 1}` });
    const id = (res.patches[0] as { id: string }).id;
    useVisRuntime.getState().setAktiverGraphId(id);
    return id;
  } catch (err) {
    meldeFehler(err);
    return undefined;
  }
}

/**
 * U-7 (`docs/BERICHT-FABLE-CODE-2026-08-18.md` B-3) — löscht einen ganzen
 * Render-Graphen. `vis.graphLoeschen` war Kernel-seitig fertig (Schema +
 * Undo + Test) UND bewusst aus `KOSMO_AUSGESCHLOSSENE_COMMANDS`
 * (`state/kosmo-ui-werkzeuge.ts`, Begründung «Abriss bleibt Handgriff»)
 * ausgeschlossen — deren Begründung SETZT einen UI-Handgriff voraus, den es
 * bislang nur für `vis.nodeLoeschen`/`design.loeschen`/
 * `design.meshVertexSchieben` gab, nicht für diesen Command: 0 `runCommand`-
 * Aufrufer im App-Code, also kein Weg, ihn je auszulösen — «gebaut,
 * getestet, unverdrahtet».
 *
 * Muster identisch zu `NodeCanvas.tsx`s `vis.nodeLoeschen`-Handgriff (ein
 * Klick, `runCommand` direkt) — MIT EINER Erweiterung: ein ganzer Graph
 * verschwindet, nicht nur ein Node, darum zusätzlich `bestaetigen()`
 * (`@kosmo/ui`, ersetzt `confirm()`) davor, Muster
 * `DataWorkspace.tsx#materialLoeschen`/`Inspector.tsx`-Lösch-Pfade: erst
 * nach «Löschen» im Dialog läuft der Command. Undo bleibt über den
 * Patch-Weg erreichbar (der Command selbst ist unverändert, nur der
 * Aufrufer ist neu) — die Rückfrage schützt nur den unbeabsichtigten Klick,
 * nicht die Rückgängig-Fähigkeit.
 */
export async function graphLoeschen(graphId: string): Promise<void> {
  const { doc, runCommand } = useProject.getState();
  const graph = doc.get<VisGraph>(graphId);
  if (!graph) return;
  const ok = await bestaetigen({
    titel: `Render-Graph «${graph.name}» löschen?`,
    text: 'Alle Nodes und Verbindungen dieses Graphen gehen verloren (rückgängig machbar über Undo).',
    gefaehrlich: true,
    bestaetigen: 'Löschen',
  });
  if (!ok) return;
  try {
    runCommand('vis.graphLoeschen', { graphId });
    if (useVisRuntime.getState().aktiverGraphId === graphId) {
      useVisRuntime.getState().setAktiverGraphId(null);
    }
  } catch (err) {
    meldeFehler(err);
  }
}

/**
 * «Drei Stimmungen» — dieselbe fertige Teilgraph-Kette wie bisher
 * (`VisWorkspace.tsx`s `dreiStimmungen()`), EIN Undo-Schritt. Legt bei Bedarf
 * selbst einen Graphen an (wie das Vorbild).
 */
export function dreiStimmungenEinfuegen(graphIdVorgabe?: string): void {
  const { doc, runCommand, history } = useProject.getState();
  try {
    history.beginGroup();
    try {
      let gid = graphIdVorgabe;
      if (!gid || !doc.get<VisGraph>(gid)) {
        gid = neuerGraphErstellen();
        if (!gid) return;
      }
      const setze = (typ: string, x: number, y: number, params?: Record<string, string | number | boolean>) => {
        runCommand('vis.nodeSetzen', { graphId: gid!, typ, x, y, ...(params ? { params } : {}) });
        const g = doc.get<VisGraph>(gid!)!;
        return g.nodes[g.nodes.length - 1]!.id;
      };
      const verbinde = (from: string, fromPort: string, to: string, toPort: string) =>
        runCommand('vis.verbinden', { graphId: gid!, from, fromPort, to, toPort });
      const zeilenAbstand = Math.max(basisNodeHoehe('stimmung'), basisNodeHoehe('kombinierer'), basisNodeHoehe('render')) + 40;
      const spaltenAbstand = NODE_W + 80;
      const stimmungX = 320;
      const kombX = stimmungX + spaltenAbstand;
      const renderX = kombX + spaltenAbstand;
      const vergleichX = renderX + spaltenAbstand;
      const bestehend = doc.get<VisGraph>(gid)?.nodes ?? [];
      const basisY = bestehend.length === 0 ? 0 : Math.max(0, ...bestehend.map((n) => n.y + basisNodeHoehe(n.typ))) + 40;
      const modell = setze('modell', 40, basisY + 260);
      const material = setze('material', 40, basisY + 420);
      const vergleich = setze('vergleich', vergleichX, basisY + zeilenAbstand + 40);
      (['morgen', 'abend', 'weiss'] as const).forEach((preset, i) => {
        const y = basisY + 40 + i * zeilenAbstand;
        const stimmung = setze('stimmung', stimmungX, y, { preset });
        const komb = setze('kombinierer', kombX, y);
        const render = setze('render', renderX, y);
        verbinde(stimmung, 'prompt', komb, 'stimmung');
        verbinde(material, 'material', komb, 'material');
        verbinde(modell, 'szene', render, 'szene');
        verbinde(komb, 'prompt', render, 'prompt');
        verbinde(render, 'bild', vergleich, `bild${i + 1}`);
      });
    } finally {
      history.endGroup();
    }
  } catch (err) {
    meldeFehler(err);
  }
}

/** «Kamera vorschlagen» — identisch zu `VisWorkspace.tsx`s bisherigem
 *  `kameraVorschlagen()`, seit Posten 6 (28.08.2026) mit EINER Ergaenzung:
 *  legt die Aktion mangels `kamera`-Node selbst einen an, sagt sie es auch
 *  (Begruendung der Wegwahl im Kommentar an der Stelle;
 *  `test/p-kamera-vorschlagen-sagt-es.test.tsx`). */
export function kameraVorschlagenAktion(graphIdVorgabe?: string): void {
  const { doc, runCommand, history } = useProject.getState();
  try {
    history.beginGroup();
    try {
      let gid = graphIdVorgabe;
      if (!gid || !doc.get<VisGraph>(gid)) {
        gid = neuerGraphErstellen();
        if (!gid) return;
      }
      let graph = doc.get<VisGraph>(gid)!;
      let kameraNode = graph.nodes.find((n) => n.typ === 'kamera');
      if (!kameraNode) {
        runCommand('vis.nodeSetzen', { graphId: gid, typ: 'kamera', x: 40, y: 40 });
        graph = doc.get<VisGraph>(gid)!;
        kameraNode = graph.nodes[graph.nodes.length - 1]!;
        // Posten 6 (`auftraege/von-homestation/auf-orbit-20260828-16.md`,
        // Block A) — bis hierhin setzte ein Knopf namens «vorschlagen»
        // stillschweigend einen Knoten: ohne zu fragen und ohne es zu sagen.
        // Der Auftrag laesst beide Wege zu («entweder fragen, oder sagen,
        // dass es geschehen ist»); gewaehlt ist SAGEN, aus drei Gruenden:
        //
        // 1. Hausmuster. `bestaetigen()` ist in diesem Modul dem
        //    UNWIDERRUFLICHEN vorbehalten — es steht genau einmal, beim
        //    Loeschen eines ganzen Graphen (`graphLoeschenAktion`, Kommentar
        //    dort). Eine ausgefuehrte, ruecknehmbare Nebenwirkung meldet die
        //    App dagegen ueberall mit `melde(..., { ton: 'erfolg' })` —
        //    «Fensterband gesetzt.» (`design/CurtainWallPanel.tsx`),
        //    «Volumen in FreeMesh umgewandelt.» (`design/Inspector.tsx`),
        //    «Variante uebernommen … — 1 Undo-Schritt.»
        //    (`design/VariantenPanel.tsx`). Genau dieser Fall.
        // 2. Ruecknehmbar in EINEM Schritt. Die ganze Aktion laeuft in einer
        //    `history.beginGroup()`/`endGroup()`-Klammer — der gesetzte
        //    Knoten UND die Kanten verschwinden mit einem einzigen Undo.
        //    Wer etwas mit einem Griff zurueckrollen kann, dem eine Frage
        //    vorzuschalten, kostet einen Klick und bringt nichts.
        // 3. Kein asynchroner Bruch. `bestaetigen()` gibt ein Promise
        //    zurueck; ein `await` hier wuerde die Undo-Gruppe ueber einen
        //    Tick aufreissen und jeden Aufrufer (`island/inhalte/
        //    austausch.tsx`, `VisWorkspace.tsx`) auf async umstellen —
        //    ein Umbau ohne Gegenwert.
        //
        // Gemeldet wird SOFORT an der Stelle, an der es geschieht: schlaegt
        // ein spaeteres `vis.verbinden` fehl, sieht der Nutzer beides — die
        // gesetzte Kamera und den Fehler — statt nur den Fehler.
        melde('Kein Kamera-Node im Graph — einer wurde gesetzt und angeschlossen (1 Undo-Schritt).', {
          ton: 'erfolg',
        });
      }
      const renderOhneKamera = graph.nodes.filter(
        (n) => n.typ === 'render' && !graph.edges.some((e) => e.to === n.id && e.toPort === 'kameras'),
      );
      for (const render of renderOhneKamera) {
        runCommand('vis.verbinden', { graphId: gid, from: kameraNode.id, fromPort: 'kameras', to: render.id, toPort: 'kameras' });
      }
    } finally {
      history.endGroup();
    }
  } catch (err) {
    meldeFehler(err);
  }
}

/** Node per Spiral-Platzsuche einfügen — identisch zu `VisWorkspace.tsx`s bisherigem `nodeHinzu()`. */
export function nodeHinzufuegen(graphId: string, typ: string): void {
  if (!graphId) return;
  const { doc, runCommand } = useProject.getState();
  try {
    const bestehend = doc.get<VisGraph>(graphId)?.nodes ?? [];
    const eigeneHoehe = basisNodeHoehe(typ);
    const ABSTAND = 24;
    const passtHier = (x: number, y: number) =>
      !bestehend.some((n) => {
        const nHoehe = basisNodeHoehe(n.typ);
        return (
          x < n.x + NODE_W + ABSTAND && x + NODE_W + ABSTAND > n.x && y < n.y + nHoehe + ABSTAND && y + eigeneHoehe + ABSTAND > n.y
        );
      });
    // W3-a (`docs/ENTSCHEID-KNOTENPLATZ-2026-08-26.md` Weg c) — bis hierhin
    // stand ein FESTER Welt-Anker (START_X=100, START_Y=60), der bei der
    // Standard-Pan/Zoom-Lage zufällig genau auf die Bildschirmecke abbildet,
    // in der die Node-Palette-Insel lebt (`.isl-rand-sonne`), sodass ein neu
    // eingefügter Knoten dort verdeckt landete. Ersetzt durch den aktuellen
    // Sicht-Mittelpunkt (`view.cx/cy`, gespiegelt in `vis-runtime.ts` als
    // `canvasSichtMitte`) — die SVG-viewBox bildet diesen Punkt IMMER exakt
    // auf die Bildschirmmitte ab, eine fensterrandverankerte Insel kann sie
    // strukturell nicht erreichen. Fallback `{x:560,y:300}`, der heutige
    // `useState`-Default in `NodeCanvas.tsx`, falls der Store das Feld noch
    // nicht kennt (kein NodeCanvas gemountet). Die Spiral-Kollisionslogik
    // (`passtHier`) bleibt unverändert — nur ihr Startpunkt wandert.
    const anker = useVisRuntime.getState().canvasSichtMitte ?? { x: 560, y: 300 };
    // A21 (17.09.2026), Posten 1 + 16 aus `docs/RENDERPROJEKT-2026-09-10/
    // 73-BEFUNDE-OHNE-BESITZER.md` — DER STRUKTURFEHLER, den A15 gefunden und
    // bewusst stehen gelassen hat: bis hierhin war der Anker die LINKE OBERE
    // ECKE des neuen Knotens. Die viewBox bildet `canvasSichtMitte` auf die
    // Bildschirmmitte ab, also begann der Knoten in der Bildmitte und wuchs
    // von dort nach UNTEN — ihm stand nur die halbe Fensterhöhe zur
    // Verfügung. Ein Knoten, der höher ist als die halbe Leinwand, konnte so
    // NIE ganz sichtbar sein, egal wie gut er gebaut ist.
    //
    // Am laufenden Bild gemessen (eigener Bau, eigener kopfloser Chromium,
    // CDP 9251, frischer Render-Knoten, Knotenhöhe 580 px — die A15 bereits
    // von 1016 auf 580 gedrückt hatte):
    //
    //   Fenster      Karte lag          ragte unten hinaus   Elemente draussen
    //   1400×900     y 450 … 1030       130 px               4 von 20
    //   1600×900     y 450 … 1030       130 px               4 von 20
    //   1280×800     y 400 …  980       180 px               6 von 20
    //   1366×768     y 384 …  964       196 px               7 von 20
    //   1920×1080    y 540 … 1120        40 px               0 von 20
    //
    // Bei KEINER der fünf Grössen lag die Karte ganz im Fenster. Die
    // Abnahme von Welle 2 («alle sechs Bedienelemente sichtbar») stimmte —
    // sie war nur nicht die ganze Frage: der Knoten trägt 20 Bedien- und
    // Anzeige-Elemente, nicht sechs.
    //
    // GEWÄHLTER WEG: die MITTE des Knotens sitzt auf der Sichtmitte, nicht
    // seine Ecke. Ein Knoten, der überhaupt in den Ausschnitt passt, liegt
    // damit ganz darin — ohne Sonderfall, ohne Fenstergrössen-Tabelle.
    //
    // VERWORFEN: den gefundenen Platz nachträglich in das sichtbare Rechteck
    // zu KLEMMEN. Nachgerechnet (`passtHier` in echter Menge): bei acht
    // gleichartigen Knoten ist die Bandbreite, die ein 580 px hoher Knoten im
    // Ausschnitt lässt, nach vier Knoten erschöpft; die Klemme drückte den
    // fünften auf einen belegten Platz — genau die Überlappung, gegen die
    // `test/p-knotenfeld-knotenplatz.test.ts` steht. Eine Klemme, die den
    // Ausweg über den Rand verbietet, kann nur noch stapeln.
    //
    // NICHT GEBAUT (unverändert gegenüber dem B69-Entscheid unten): eine
    // obere Klemme oder ein automatisches Mitführen der Leinwand. Beides
    // bleibt draussen — der Mensch behält den Ausschnitt, den er gewählt hat.
    // Der Unterschied zu heute ist ausschliesslich, WO der Knoten relativ zum
    // Anker beginnt; die Spirale, ihre Reichweite und ihre Kollisionsprüfung
    // sind Zeile für Zeile dieselben.
    //
    // ZWEI Dinge, über die sonst der Nächste stolpert:
    // 1. Beim Standard-Blick (`{cx:560, cy:300}`) liegt der Sollwert für Y bei
    //    300 − 290 = 10 und wird von der Randklemme unten auf 20 gehoben. Der
    //    erste Render-Knoten sitzt deshalb 10 px unter der rechnerischen
    //    Mitte — gemessen: Karte y 170 … 750 bei einem 900 px hohen Fenster.
    //    Das ist kein Fehler, sondern die Weltklemme; wer nach exakter
    //    Zentrierung sucht, findet sie überall dort, wo die Klemme nicht
    //    greift (`test/a21-knotenplatz-ganz-im-bild.test.ts`, Fall 2).
    // 2. `eigeneHoehe` ist heute bei JEDER Knotenart gerade (44 + 20·Ports +
    //    gerader Körper), `START_Y` also ganzzahlig. Wer eine Körperzeile mit
    //    ungerader Höhe einträgt, bekommt halbe Weltkoordinaten — harmlos im
    //    Bild, aber es erklärt eine spätere .5 in einer Positionsprobe.
    const START_X = anker.x - NODE_W / 2;
    const START_Y = anker.y - eigeneHoehe / 2;
    // P-KNOTENPLATZ-KLEMME (27.08.2026): die Randklemme gehoert VOR die
    // Kollisionspruefung, nicht dahinter. Bis hierhin stand sie erst im
    // `runCommand`-Aufruf (`Math.max(20, x)`) — die Spirale laeuft vom
    // Sicht-Mittelpunkt aus in ALLE Richtungen, also auch ins Negative, und
    // ein dort gefundener freier Platz wurde anschliessend still auf den
    // Rand geschoben: auf eine Stelle, die nie geprueft worden ist.
    // Gemessen an acht gleichartigen Knoten hintereinander (der eigene
    // Vertrags-Riegel `test/p-knotenfeld-knotenplatz.test.ts`):
    // «Node 4 und 6 ueberlappen». Bei fuenf Knoten trat es nicht auf —
    // darum galt der Fall zuvor als «nicht reproduzierbar».
    // `klemme` wird jetzt auf JEDEN Kandidaten angewendet, bevor `passtHier`
    // ihn beurteilt, und der Rueckgabewert geht ungeklemmt weiter — die
    // Pruefung sieht damit genau die Koordinaten, die auch geschrieben werden.
    const klemme = (x: number, y: number) => ({ x: Math.max(20, x), y: Math.max(20, y) });
    const findeSpiralPlatz = (): { x: number; y: number } => {
      const SCHRITT = 60;
      const WINKEL_JE_UMLAUF = 12;
      for (let radius = 1; radius <= 40; radius++) {
        for (let schritt = 0; schritt < WINKEL_JE_UMLAUF; schritt++) {
          const winkel = (schritt / WINKEL_JE_UMLAUF) * Math.PI * 2;
          const kand = klemme(
            Math.round(START_X + radius * SCHRITT * Math.cos(winkel)),
            Math.round(START_Y + radius * SCHRITT * Math.sin(winkel) * 0.6),
          );
          if (passtHier(kand.x, kand.y)) return kand;
        }
      }
      // Letzter Ausweg: unter allen bestehenden Knoten anhaengen. Auch hier
      // geklemmt, damit der Rueckgabewert dieselbe Zusicherung traegt.
      const maxY = bestehend.reduce((m, n) => Math.max(m, n.y + basisNodeHoehe(n.typ)), START_Y);
      return klemme(START_X, maxY + ABSTAND);
    };
    const start = klemme(START_X, START_Y);
    const { x, y } = passtHier(start.x, start.y) ? start : findeSpiralPlatz();
    runCommand('vis.nodeSetzen', { graphId, typ, x, y });
    // A21 — WAS DER MITTEN-ANKER FUER DIE B69-MELDUNG UNTEN KOSTET, offen
    // gesagt, weil es in die unerwartete Richtung geht. Gemessen (acht
    // Render-Knoten nacheinander ueber denselben Palette-Klick, Meldungen per
    // MutationObserver eingesammelt statt abgefragt):
    //
    //   Fenster      B69-Meldungen        Knoten GANZ im Fenster
    //   1400×900     3 → 4                0 von 8 → 4 von 8
    //   1600×900     3 → 3                0 von 8 → 4 von 8
    //   1280×800     3 → 4                0 von 8 → 4 von 8
    //   1920×1080    2 → 2                0 von 8 → 5 von 8
    //   1366×768     3 → 4                0 von 8 → 4 von 8
    //
    // Bei EINEM Knoten — dem Fall, den ein Mensch wirklich ausloest — sind es
    // vorher wie nachher NULL Meldungen an allen fuenf Groessen, und der
    // Knoten liegt neu ganz im Bild statt an keiner einzigen Groesse.
    //
    // Warum die Acht-Knoten-Zahl an drei Groessen um EINS steigt: die
    // Randklemme oben. Der Anker liegt 290 px hoeher, fast alle Kandidaten mit
    // negativem Y-Versatz fallen damit unter y=20 und werden auf dieselbe
    // Zeile geklemmt; die Reihe waechst darum frueher nach rechts aus dem
    // Fenster. Jede dieser zusaetzlichen Meldungen ist WAHR — der Knoten liegt
    // wirklich draussen. Wer sie wegbekommen will, muss an die Randklemme,
    // nicht an den Anker; das ist ein eigener Entscheid mit eigener Messung.

    // B69 (`docs/UI-UX-2026-09-07-B69-ENTSCHEID-HINWEIS.md`) — Owner-Entscheid
    // woertlich «b69 hinweis anzeigen»: die Spirale laeuft vom Sicht-
    // Mittelpunkt aus in ALLE Richtungen und darf beliebig weit nach rechts/
    // unten wandern (keine obere Klemme, s. Kommentar oben) — ein Knoten kann
    // also ausserhalb des sichtbaren Ausschnitts landen. `elementFromPoint`
    // faende dort NICHTS (kein deckendes Element), darum kann der bestehende
    // Ueberdeckungs-Waechter diesen Fall nicht fangen. AUSDRUECKLICH NICHT
    // gebaut: eine obere Klemme oder ein automatisches Mitfuehren der
    // Leinwand — beides schoebe den Knoten auf eine von `passtHier` nie
    // geprüfte Stelle bzw. entzöge dem Menschen den Ausschnitt, den er sich
    // selbst gewählt hat. Stattdessen: der Knoten bleibt genau dort, wo die
    // Spirale ihn gefunden hat, und der Mensch erfährt es — über denselben
    // Meldeweg wie `kameraVorschlagenAktion` oben (`melde(..., { ton })`,
    // kein neuer Mechanismus). Geprüft wird gegen `canvasSichtRechteck`
    // (`vis-runtime.ts`, hier neu gespiegelt) — `null`, solange kein
    // `NodeCanvas` gemountet hat (z. B. Unit-Tests ohne UI): dann bleibt die
    // Prüfung aus, statt aus einer geratenen Fenstergrösse einen falschen
    // Hinweis zu geben.
    const rechteck = useVisRuntime.getState().canvasSichtRechteck;
    if (rechteck) {
      const mitteX = x + NODE_W / 2;
      const mitteY = y + eigeneHoehe / 2;
      const ausserhalb =
        mitteX < rechteck.x || mitteX > rechteck.x + rechteck.b || mitteY < rechteck.y || mitteY > rechteck.y + rechteck.h;
      if (ausserhalb) {
        // Ton 'info' (der neutrale Ton in `@kosmo/ui`s `Meldung['ton']` —
        // 'hinweis' existiert dort nicht): nichts ist schiefgegangen, der
        // Knoten ist angelegt. Wortlaut an die tatsächliche Insel angepasst
        // (`island/inhalte/ansicht.tsx:27`, Knopf-Titel «Einpassen», nicht
        // «Alles einpassen» wie im Auftragsblatt-Vorschlag) — ein Hinweis,
        // der einen Knopf falsch benennt, waere schlimmer als keiner.
        melde('Der Knoten ist angelegt, liegt aber ausserhalb des sichtbaren Ausschnitts — «Einpassen» zeigt ihn.', {
          ton: 'info',
        });
      }
    }
  } catch (err) {
    meldeFehler(err);
  }
}
