// @vitest-environment jsdom
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { execute, History, KosmoDoc, rechnetOhneFreigabe, type VisGraph } from '@kosmo/kernel';
import { useProject } from '../../kosmo-orbit/src/state/project-store';
import { useVisRuntime } from '../../kosmo-orbit/src/modules/vis/vis-runtime';
import { behandle, leereKiZustand } from '../../kosmo-orbit/src/modules/vis/ki-werkzeuge';
// Die Laufzeit der Varianten meldet im Original den Stand-Leser an — hier mitgeladen, damit die Probe
// sieht, dass sie KEINEN Freigabe-Leser anmeldet.
import '../../kosmo-orbit/src/modules/vis/varianten';
import { setzeCoopZurueck, setzeModusVonApp, useKosmoCoop } from '../../kosmo-orbit/src/state/kosmo-coop';

/**
 * Geräteprobe R57 (23.10.2026): In der Vollautomatik von KosmoOrbit sagen die Bestellsätze jetzt
 * «ohne Freigabe», sobald die App dort einen Leser anmeldet (`setzeOhneFreigabeLeser`). In Visbox gibt
 * immer ein Mensch die Grafikkarte frei (Entscheide 106b/134; «Voll» ohne Klick erst nach der Demo) —
 * darum meldet hier niemand einen Leser an, und auch mit der Selbständigkeit «Voll» bleibt jede
 * Bestellung eine Karte mit dem alten Satz. Namen erfunden.
 */

let graphId = '';
let renderId = '';
let variantenId = '';

function neuesDokument(): KosmoDoc {
  const doc = new KosmoDoc();
  graphId = (execute(doc, 'vis.graphErstellen', { name: 'Probe' }).patches[0] as { id: string }).id;
  execute(doc, 'vis.nodeSetzen', { graphId, typ: 'render', x: 0, y: 0 });
  execute(doc, 'vis.nodeSetzen', { graphId, typ: 'varianten', x: 300, y: 0 });
  [renderId, variantenId] = doc.get<VisGraph>(graphId)!.nodes.map((n) => n.id) as [string, string];
  execute(doc, 'vis.verbinden', { graphId, from: renderId, fromPort: 'bild', to: variantenId, toPort: 'render' });
  return doc;
}

beforeEach(() => {
  leereKiZustand();
  setzeCoopZurueck();
  useProject.setState({ doc: neuesDokument(), history: new History(), journal: [], revision: 0, activeStoreyId: null, selection: [] } as never);
  useVisRuntime.setState({ aktiverGraphId: graphId, laeufe: {} });
  setzeModusVonApp('voll');
});

afterEach(() => {
  leereKiZustand();
  setzeCoopZurueck();
});

describe('Visbox in der Selbständigkeit «Voll»: Bestellen bleibt eine Karte mit «Freigabe»', () => {
  it('kein Freigabe-Leser angemeldet, obwohl «Voll» an ist', () => {
    expect(useKosmoCoop.getState().vollautomatik).toBe(true);
    expect(rechnetOhneFreigabe()).toBe(false);
  });

  it('vis_render: Karte «Freigabe durch den Architekten», nicht «ohne Freigabe»', () => {
    const a = behandle({ kennung: 'F-1', werkzeug: 'vis_render', argumente: { graphId, nodeId: renderId, kameraWahl: 'auto', guete: 'vorschau' } }, 'voll');
    expect('karte' in a).toBe(true);
    const satz = 'karte' in a ? a.karte.zusammenfassung : '';
    expect(satz).toBe('Vorschau rechnen am Render-Knoten (Freigabe durch den Architekten)');
    expect(satz).not.toContain('ohne Freigabe');
  });

  it('vis_varianten: Karte «jeder wartet auf Freigabe»', () => {
    const a = behandle({ kennung: 'F-2', werkzeug: 'vis_varianten', argumente: { nodeId: variantenId, stimmungen: ['abend'] } }, 'voll');
    expect('karte' in a).toBe(true);
    const satz = 'karte' in a ? a.karte.zusammenfassung : '';
    expect(satz).toContain(`jeder wartet auf Freigabe am Knoten «Varianten» (${variantenId}).`);
    expect(satz).not.toContain('ohne Freigabe');
  });
});
