import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import {
  execute,
  KosmoDoc,
  OHNE_FREIGABE_RENDER,
  OHNE_FREIGABE_VARIANTEN,
  rechnetOhneFreigabe,
  renderZeile,
  setzeOhneFreigabeLeser,
  type VisGraph,
} from '@kosmo/kernel';

/**
 * Geräteprobe R57 (23.10.2026): In der Vollautomatik sagten die Bestellsätze von `vis.render` und
 * `vis.varianten` «Freigabe durch den Architekten» bzw. «jeder wartet auf Freigabe», die Aufträge
 * rechneten aber sofort. Der Satz folgt jetzt dem, was die App meldet (`setzeOhneFreigabeLeser`);
 * ohne Meldung — Kern allein, Visbox — bleibt er wie bisher. Nur der Wortlaut, kein Verhalten.
 * Nur Kern-Befehle (kein Bauteil), damit die Probe auch im dünnen Kern der Visbox-Kopie läuft.
 */

let doc: KosmoDoc;
let graphId = '';
let renderId = '';
let variantenId = '';

beforeEach(() => {
  setzeOhneFreigabeLeser(null);
  doc = new KosmoDoc();
  graphId = (execute(doc, 'vis.graphErstellen', { name: 'Probe' }).patches[0] as { id: string }).id;
  execute(doc, 'vis.nodeSetzen', { graphId, typ: 'render', x: 0, y: 0 });
  execute(doc, 'vis.nodeSetzen', { graphId, typ: 'varianten', x: 300, y: 0 });
  [renderId, variantenId] = doc.get<VisGraph>(graphId)!.nodes.map((n) => n.id) as [string, string];
  execute(doc, 'vis.verbinden', { graphId, from: renderId, fromPort: 'bild', to: variantenId, toPort: 'render' });
});

afterEach(() => setzeOhneFreigabeLeser(null));

function sichereBlick(): void {
  doc.settings = {
    ...doc.settings,
    gespeicherteBlicke: [{ id: 'blick-1', name: 'Gartenblick', position: [20, 1.6, -15], ziel: [5, 1.5, -3], fovGrad: 55 }],
  };
}

describe('ohne Meldung der App (Kern allein, Visbox): der Satz wie bisher', () => {
  it('Render-Auftrag: Freigabe durch den Architekten', () => {
    expect(rechnetOhneFreigabe()).toBe(false);
    const r = execute(doc, 'vis.render', { graphId, nodeId: renderId, kameraWahl: 'auto', guete: 'vorschau' });
    expect(r.summary).toBe('Vorschau rechnen am Render-Knoten (Freigabe durch den Architekten)');
  });

  it('Varianten: jeder wartet auf Freigabe — mit und ohne eigene Standpunkte', () => {
    const ohne = execute(doc, 'vis.varianten', { nodeId: variantenId, stimmungen: ['abend'] });
    expect(ohne.summary).toContain(`jeder wartet auf Freigabe am Knoten «Varianten» (${variantenId}).`);
    sichereBlick();
    const mit = execute(doc, 'vis.varianten', { nodeId: variantenId, stimmungen: ['abend'] });
    expect(mit.summary).toContain(`; jeder wartet auf Freigabe am Knoten «Varianten» (${variantenId}).`);
  });

  it('eine Meldung «nein» oder ein scheiternder Leser ändert nichts', () => {
    setzeOhneFreigabeLeser(() => false);
    expect(renderZeile({ kameraWahl: 'auto', guete: 'vorschau' })).toContain('(Freigabe durch den Architekten)');
    setzeOhneFreigabeLeser(() => {
      throw new Error('App weg');
    });
    expect(rechnetOhneFreigabe()).toBe(false);
    expect(renderZeile({ kameraWahl: 'auto', guete: 'vorschau' })).toContain('(Freigabe durch den Architekten)');
  });
});

describe('die App meldet «rechnet ohne Freigabe» (KosmoOrbit: Vollautomatik an)', () => {
  beforeEach(() => setzeOhneFreigabeLeser(() => true));

  it('Render-Auftrag: sagt, dass er ohne Freigabe rechnet — und nicht mehr «durch den Architekten»', () => {
    const r = execute(doc, 'vis.render', { graphId, nodeId: renderId, kameraWahl: 'auto', guete: 'vorschau', stimmungPreset: 'abend' });
    expect(r.summary).toBe(`Vorschau rechnen am Render-Knoten (${OHNE_FREIGABE_RENDER}) · Stimmung: Abendstimmung`);
    expect(r.summary).toBe('Vorschau rechnen am Render-Knoten (rechnet ohne Freigabe, Vollautomatik) · Stimmung: Abendstimmung');
    expect(r.summary).not.toContain('Freigabe durch den Architekten');
  });

  it('Varianten: jeder startet ohne Freigabe — keiner «wartet»', () => {
    const ohne = execute(doc, 'vis.varianten', { nodeId: variantenId, stimmungen: ['abend'] });
    expect(ohne.summary).toContain(`${OHNE_FREIGABE_VARIANTEN} am Knoten «Varianten» (${variantenId}).`);
    sichereBlick();
    const mit = execute(doc, 'vis.varianten', { nodeId: variantenId, stimmungen: ['abend'] });
    expect(mit.summary).toContain(`; jeder startet ohne Freigabe (Vollautomatik) am Knoten «Varianten» (${variantenId}).`);
    for (const s of [ohne.summary, mit.summary]) expect(s).not.toContain('wartet auf Freigabe');
  });

  it('der Leser wird bei jedem Satz neu gefragt (Vollautomatik aus → wieder der alte Satz)', () => {
    let voll = true;
    setzeOhneFreigabeLeser(() => voll);
    expect(renderZeile({ kameraWahl: 'auto', guete: 'voll' })).toBe(`Bild in voller Güte rechnen am Render-Knoten (${OHNE_FREIGABE_RENDER})`);
    voll = false;
    expect(renderZeile({ kameraWahl: 'auto', guete: 'voll' })).toBe('Bild in voller Güte rechnen am Render-Knoten (Freigabe durch den Architekten)');
  });
});
