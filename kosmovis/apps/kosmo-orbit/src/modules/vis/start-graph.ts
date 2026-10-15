import { meldeFehler } from '@kosmo/ui';
import type { KosmoDoc, VisGraph } from '@kosmo/kernel';
import { useProject } from '../../state/project-store';
import { groessteNodeHoehe, NODE_W } from './NodeCanvas';
import { useVisRuntime } from './vis-runtime';

/**
 * DER FERTIGE ANFANG (Owner-Entscheid 91/91a/91b der Visbox, 14.10.2026, Blatt 22;
 * Nachtrag 92: die Grundlage fuer «Varianten mit einem Klick»).
 *
 * Bis hierhin stand ohne Render-Graph nur «Noch kein Render-Graph» — und ohne Graph gibt es
 * keinen Modell-Knoten, also auch kein «Datei laden …». Der Anfang legt einen gewoehnlichen
 * Graphen an, wie man ihn von Hand bauen wuerde:
 *
 *     Stimmung ─┐
 *               ├─ Prompt-Kombinierer ─┐
 *     Prompt ───┘                      │
 *     Modell ──────────────────────────┼─ Render ── Varianten ── Bildvergleich
 *     Auto-Kamera ─────────────────────┘
 *
 * **Varianten** (L24 Bildweg Varianten, E246; Owner-Wunsch 14.10.: «direkt bereit zum
 * Ein-Klick-Render von Varianten»): der Knoten steht hinter dem Render-Knoten mit der Vorgabe
 * 3 Standpunkte × Abend × aktuelles Modell (92a), und der Bildvergleich zeigt sein Raster. Ein
 * Klick auf «3 Bilder bestellen» und einer auf «Alle freigeben» — mehr braucht es nicht.
 *
 * **Warum ein Kombinierer dabei ist:** Der Render-Knoten hat EINEN Prompt-Eingang
 * (`VIS_NODE_KATALOG.render`). Stimmung und eigener Text kommen darum ueber den Kombinierer
 * zusammen — derselbe Weg wie «Drei Stimmungen» (`vis-graph-aktionen.ts`).
 *
 * **Warum keine Linie Modell → Auto-Kamera:** Die Auto-Kamera hat im Katalog keinen Eingang;
 * sie liest das Modell aus dem Dokument. Eine Linie dorthin waere Schmuck, der etwas
 * verspricht, das sie nicht traegt. Sie steht darum direkt unter dem Modell.
 *
 * **Nichts rechnet:** Der Anfang setzt nur Knoten und Linien. Gerechnet wird erst auf
 * «Ausfuehren» und «Freigeben» am Render-Knoten, wie bei jedem Graphen.
 *
 * **Eine Rueckgaengig-Klammer:** alles in `history.beginGroup()`/`endGroup()`, wie
 * «Drei Stimmungen» — ein Strg+Z nimmt den ganzen Anfang zurueck.
 */
export function startGraphAnlegen(): string | undefined {
  const { doc, runCommand, history } = useProject.getState();
  try {
    history.beginGroup();
    try {
      const graphen = doc.byKind<VisGraph>('visgraph');
      const res = runCommand('vis.graphErstellen', { name: `Graph ${graphen.length + 1}` });
      const gid = (res.patches[0] as { id: string }).id;
      const setze = (typ: string, x: number, y: number) => {
        runCommand('vis.nodeSetzen', { graphId: gid, typ, x, y });
        const g = doc.get<VisGraph>(gid)!;
        return g.nodes[g.nodes.length - 1]!.id;
      };
      const verbinde = (from: string, fromPort: string, to: string, toPort: string) =>
        runCommand('vis.verbinden', { graphId: gid, from, fromPort, to, toPort });

      const lage = startGraphLage();
      const stimmung = setze('stimmung', lage.stimmung.x, lage.stimmung.y);
      const prompt = setze('prompt', lage.prompt.x, lage.prompt.y);
      const modell = setze('modell', lage.modell.x, lage.modell.y);
      const kamera = setze('kamera', lage.kamera.x, lage.kamera.y);
      const komb = setze('kombinierer', lage.kombinierer.x, lage.kombinierer.y);
      const render = setze('render', lage.render.x, lage.render.y);
      const varianten = setze('varianten', lage.varianten.x, lage.varianten.y);
      const vergleich = setze('vergleich', lage.vergleich.x, lage.vergleich.y);

      verbinde(stimmung, 'prompt', komb, 'stimmung');
      verbinde(prompt, 'prompt', komb, 'stil');
      verbinde(komb, 'prompt', render, 'prompt');
      verbinde(modell, 'szene', render, 'szene');
      verbinde(kamera, 'kameras', render, 'kameras');
      verbinde(render, 'bild', varianten, 'render');
      verbinde(varianten, 'bilder', vergleich, 'bild1');

      useVisRuntime.getState().setAktiverGraphId(gid);
      return gid;
    } finally {
      history.endGroup();
    }
  } catch (err) {
    meldeFehler(err);
    return undefined;
  }
}

/** Wo die acht Knoten des Anfangs liegen (linke obere Ecke, Welt-Pixel). Fuenf Spalten;
 *  die Zeilen der ersten Spalte mit der GROESSTEN Hoehe jedes Knotens (aufgeklappt), damit
 *  nichts ueberlappt, wenn man einen Knoten aufklappt. Exportiert fuer die Probe. */
export function startGraphLage(): Record<
  'stimmung' | 'prompt' | 'modell' | 'kamera' | 'kombinierer' | 'render' | 'varianten' | 'vergleich',
  { x: number; y: number }
> {
  const abstand = 32;
  const spalte = NODE_W + 80;
  const x0 = 40;
  const y0 = 40;
  const yPrompt = y0 + groessteNodeHoehe('stimmung') + abstand;
  const yModell = yPrompt + groessteNodeHoehe('prompt') + abstand;
  const yKamera = yModell + groessteNodeHoehe('modell') + abstand;
  return {
    stimmung: { x: x0, y: y0 },
    prompt: { x: x0, y: yPrompt },
    modell: { x: x0, y: yModell },
    kamera: { x: x0, y: yKamera },
    kombinierer: { x: x0 + spalte, y: y0 },
    render: { x: x0 + 2 * spalte, y: y0 },
    varianten: { x: x0 + 3 * spalte, y: y0 },
    vergleich: { x: x0 + 4 * spalte, y: y0 },
  };
}

/*
 * WANN DER ANFANG VON SELBST ENTSTEHT — je Wirt, nicht fuer alle (Begruendung im Blatt
 * `kosmo-orbit/docs/auftraege-kosmovis/meldung-20261014-kosmovis-startgraph.md`).
 *
 * In KosmoOrbit ist ein Projekt ein gespeichertes, geteiltes Dokument: Jeder `runCommand`
 * zaehlt die Revision hoch (der Tresor sichert dann «Auto-gesichert», `project-vault.ts`),
 * landet im Rueckgaengig-Stapel des Architekten und geht als Patch an die Mitarbeitenden
 * (`patchListener`). Ein Anfang, der beim blossen OEFFNEN der Vis-Station geschrieben wuerde,
 * aenderte also ein Projekt, das nur angesehen wurde, legte einen Schritt in fremde
 * Rueckgaengig-Ketten — und zwei gleichzeitig offene Geraete legten ZWEI Graphen an. Darum
 * zeigt KosmoOrbit den Anfang als Vorschlag mit einem Knopf («Fertigen Anfang anlegen»),
 * eine Bedienung, ein Undo-Schritt.
 *
 * In Visbox lebt das Dokument nur in der Seite (kein Tresor, keine Mitarbeitenden): Die
 * Knotenansicht beginnt jedes Mal leer. Dort ruft der Wirt `legeAnfangBeimOeffnen(true)`,
 * und der Anfang entsteht beim ersten Bild — mit «Datei laden …» im Modell-Knoten.
 */
let beimOeffnen = false;
const schonAngelegt = new WeakSet<KosmoDoc>();

/** Der Wirt bestimmt, ob ein leeres Dokument den Anfang von selbst bekommt (Visbox: ja). */
export function legeAnfangBeimOeffnen(an: boolean): void {
  beimOeffnen = an;
}

export function anfangBeimOeffnen(): boolean {
  return beimOeffnen;
}

/**
 * Legt den Anfang an, wenn der Wirt es so will, das Dokument keinen Graphen hat und es
 * fuer DIESES Dokument noch nicht geschehen ist. Das «noch nicht» haelt zweierlei: React
 * ruft Effekte im Strict Mode doppelt, und wer den Anfang mit Strg+Z zuruecknimmt, will ihn
 * nicht sofort wiederhaben — dann bleibt der Vorschlag mit seinem Knopf stehen.
 */
export function anfangFallsLeer(): string | undefined {
  const { doc } = useProject.getState();
  if (!beimOeffnen || schonAngelegt.has(doc)) return undefined;
  if (doc.byKind<VisGraph>('visgraph').length > 0) return undefined;
  schonAngelegt.add(doc);
  return startGraphAnlegen();
}
