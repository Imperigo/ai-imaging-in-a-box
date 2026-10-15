// @vitest-environment jsdom
import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { evaluiereGraph, VIS_NODE_KATALOG, type VisGraph } from '@kosmo/kernel';
import { basisNodeHoehe, NodeCanvas } from '../src/modules/vis/NodeCanvas';
import {
  aktualisiereSkizzen,
  holeSkizzenBild,
  registriereSkizzenQuelle,
  SKIZZE_IPAD_TYP,
  SKIZZE_LEER_SATZ,
  SKIZZE_NEUESTE,
  SKIZZE_OHNE_WIRT_SATZ,
  skizzenName,
  skizzenStand,
  waehleSkizze,
  type Skizze,
  type SkizzenQuelle,
} from '../src/modules/vis/skizze-quelle';
import { useProject } from '../src/state/project-store';

/**
 * KV-SKIZZE-VOM-IPAD (Owner-Entscheide 95/95a der Visbox, 14.10.2026, Blatt 25): Der Knoten
 * «Skizze vom iPad» holt die Skizzen der Mappe in die Knotenansicht — aber nur, wenn der WIRT
 * eine Skizzen-Quelle anmeldet.
 *
 *  - Mit Wirt (Visbox): von selbst die neueste, eine ältere am Knoten wählbar (rückgängig
 *    machbar), Daumenbild, leere Mappe mit Satz.
 *  - Ohne Wirt (KosmoOrbit): ein ruhiger Satz; der Knoten steht trotzdem im Katalog.
 *  - Der Ausgang geht in Bildvergleich und «Aufs Blatt». Seit Entscheid 96 (15.10.2026) auch an
 *    den Eingang «Skizze» des Render-Knotens (`kv-skizze-fuehrt.test.tsx`); an jedem anderen
 *    Render-Eingang wird er abgewiesen, und ohne diese Kante bleibt die Bestellung Zeichen für
 *    Zeichen wie ohne Skizzen-Knoten.
 *  - «Aufs Blatt» mit der Beschriftung «Skizze (iPad)» prüft `kv-skizze-vom-ipad-blatt.test.tsx`
 *    (eigene Datei, weil Visbox keine Blätter hat und die Kopie dort ohne sie läuft).
 */
class StubResizeObserver {
  observe(): void {}
  unobserve(): void {}
  disconnect(): void {}
}
(globalThis as unknown as { ResizeObserver: typeof StubResizeObserver }).ResizeObserver = StubResizeObserver;
(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

const SKIZZEN: Skizze[] = [
  { name: 'skizze-20261014-0912.png', titel: 'Fassade Süd', erzeugt: '2026-10-14T09:12:00', ueber: null, stand: 'abgelegt' },
  { name: 'skizze-20261013-1730.png', titel: '', erzeugt: '2026-10-13T17:30:00', ueber: 'bild-1.png', stand: 'abgelegt' },
];

/** Bild-Bytes je Adresse — der Abruf der Attrappe. */
const PNG = new Uint8Array([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]);

function wirt(liste: Skizze[] = SKIZZEN): SkizzenQuelle & { gelesen: number } {
  const q = {
    gelesen: 0,
    async liste() {
      q.gelesen += 1;
      return liste;
    },
    bildUrl: (name: string) => `./skizze?name=${encodeURIComponent(name)}`,
  };
  return q;
}

let root: Root | null = null;
let container: HTMLDivElement | null = null;
const abrufe: string[] = [];

beforeEach(() => {
  abrufe.length = 0;
  vi.stubGlobal('fetch', async (url: string) => {
    abrufe.push(String(url));
    return { ok: true, blob: async () => new Blob([PNG], { type: 'image/png' }) };
  });
});

afterEach(() => {
  if (root) act(() => root!.unmount());
  container?.remove();
  root = null;
  container = null;
  registriereSkizzenQuelle(null);
  vi.unstubAllGlobals();
});

/** Ein Graph mit einem Skizzen-Knoten (und auf Wunsch einem Ziel), gezeigt im Canvas. */
function montiere(ziel?: 'vergleich' | 'blatt'): { graphId: string; skizzeId: string; zielId?: string } {
  const { runCommand, doc } = useProject.getState();
  const res = runCommand('vis.graphErstellen', { name: `KV-SKIZZE-${Math.random()}` });
  const graphId = (res.patches[0] as { id: string }).id;
  runCommand('vis.nodeSetzen', { graphId, typ: SKIZZE_IPAD_TYP, x: 40, y: 40 });
  const skizzeId = doc.get<VisGraph>(graphId)!.nodes[0]!.id;
  let zielId: string | undefined;
  if (ziel) {
    runCommand('vis.nodeSetzen', { graphId, typ: ziel, x: 320, y: 40 });
    zielId = doc.get<VisGraph>(graphId)!.nodes[1]!.id;
    runCommand('vis.verbinden', {
      graphId,
      from: skizzeId,
      fromPort: 'bild',
      to: zielId,
      toPort: ziel === 'vergleich' ? 'bild1' : 'bild',
    });
  }
  container = document.createElement('div');
  document.body.appendChild(container);
  root = createRoot(container);
  act(() => root!.render(<NodeCanvas graphId={graphId} />));
  return { graphId, skizzeId, ...(zielId ? { zielId } : {}) };
}

const q = (id: string) => container!.querySelector(`[data-testid="${id}"]`);

/** Bis die Liste gelesen und die Bilder geholt sind (alles Versprechen der Attrappe). */
async function warteAufWirt(): Promise<void> {
  await act(async () => {
    for (let i = 0; i < 6; i += 1) await new Promise((r) => setTimeout(r, 0));
  });
}

function waehle(testid: string, wert: string): void {
  const trigger = q(testid) as HTMLButtonElement | null;
  expect(trigger, testid).not.toBeNull();
  act(() => {
    trigger!.dispatchEvent(new MouseEvent('click', { bubbles: true }));
  });
  const option = document.querySelector<HTMLButtonElement>(`[data-testid="${testid}-popup"] button[data-value="${wert}"]`);
  expect(option, `${testid}-popup [data-value="${wert}"]`).not.toBeNull();
  act(() => {
    option!.dispatchEvent(new MouseEvent('click', { bubbles: true }));
  });
}

describe('KV-SKIZZE-VOM-IPAD · Katalog', () => {
  it('ein Quell-Knoten mit einem Bild-Ausgang, Vorgabe «neueste»', () => {
    const kat = VIS_NODE_KATALOG[SKIZZE_IPAD_TYP]!;
    expect(kat.label).toBe('Skizze vom iPad');
    expect(kat.kategorie).toBe('quelle');
    expect(kat.inputs).toEqual([]);
    expect(kat.outputs).toEqual([{ name: 'bild', typ: 'bild', label: 'Bild' }]);
    expect(kat.defaults).toEqual({ skizze: SKIZZE_NEUESTE });
  });

  it('eine Hoehe fuer alle Zustaende — mit und ohne Wirt dieselbe', () => {
    const ohne = basisNodeHoehe(SKIZZE_IPAD_TYP);
    registriereSkizzenQuelle(wirt());
    expect(basisNodeHoehe(SKIZZE_IPAD_TYP)).toBe(ohne);
    // Kopf 26 + 8 + ein Ausgang 20 + Koerper 116 + 10.
    expect(ohne).toBe(180);
  });
});

describe('KV-SKIZZE-VOM-IPAD · ohne Wirt (KosmoOrbit)', () => {
  it('ein ruhiger Satz, keine Auswahl, kein Bild — und kein Abruf', async () => {
    montiere();
    await warteAufWirt();
    expect(q('skizze-knoten')?.getAttribute('data-stand')).toBe('ohne-wirt');
    expect(q('skizze-satz')?.textContent).toBe(SKIZZE_OHNE_WIRT_SATZ);
    expect(q('skizze-wahl')).toBeNull();
    expect(q('skizze-bild')).toBeNull();
    expect(abrufe).toEqual([]);
  });

  it('am Bildvergleich bleibt es leer', async () => {
    montiere('vergleich');
    await warteAufWirt();
    expect(container!.querySelector('.vis-vergleich-leer')).not.toBeNull();
  });
});

describe('KV-SKIZZE-VOM-IPAD · mit Wirt (Visbox)', () => {
  it('nimmt von selbst die neueste: Auswahl «neueste — …» und ihr Daumenbild', async () => {
    registriereSkizzenQuelle(wirt());
    montiere();
    await warteAufWirt();
    expect(q('skizze-knoten')?.getAttribute('data-stand')).toBe('da');
    const trigger = q('skizze-wahl') as HTMLElement;
    expect(trigger.getAttribute('data-value')).toBe(SKIZZE_NEUESTE);
    expect(trigger.textContent).toBe(`neueste — ${skizzenName(SKIZZEN[0]!)}`);
    expect(trigger.textContent).toMatch(/^neueste — Fassade Süd · 14\.10\. 09:12$/);
    expect((q('skizze-bild') as HTMLImageElement).getAttribute('src')).toBe('./skizze?name=skizze-20261014-0912.png');
  });

  it('eine aeltere waehlen: Parameter gespeichert, Bild gewechselt, ein Strg+Z zurueck auf «neueste»', async () => {
    registriereSkizzenQuelle(wirt());
    const { graphId, skizzeId } = montiere();
    await warteAufWirt();
    const aeltere = SKIZZEN[1]!.name;
    waehle('skizze-wahl', aeltere);
    const knoten = () => useProject.getState().doc.get<VisGraph>(graphId)!.nodes.find((n) => n.id === skizzeId)!;
    expect(knoten().params['skizze']).toBe(aeltere);
    expect((q('skizze-bild') as HTMLImageElement).getAttribute('src')).toBe(`./skizze?name=${aeltere}`);
    // Ohne Titel heisst sie nach ihrer Datei.
    expect(q('skizze-wahl')?.textContent).toMatch(/^skizze-20261013-1730\.png · 13\.10\. 17:30$/);
    act(() => useProject.getState().undo());
    expect(knoten().params['skizze']).toBe(SKIZZE_NEUESTE);
    expect((q('skizze-bild') as HTMLImageElement).getAttribute('src')).toBe(`./skizze?name=${SKIZZEN[0]!.name}`);
  });

  it('eine neue Skizze in der Mappe: «neueste» springt mit, eine feste Wahl bleibt', async () => {
    const liste = [...SKIZZEN];
    const quelle = wirt(liste);
    registriereSkizzenQuelle(quelle);
    montiere();
    await warteAufWirt();
    liste.unshift({ name: 'skizze-20261014-1100.png', titel: 'Eingang', erzeugt: '2026-10-14T11:00:00', stand: 'abgelegt' });
    await act(async () => {
      await aktualisiereSkizzen();
    });
    expect((q('skizze-bild') as HTMLImageElement).getAttribute('src')).toBe('./skizze?name=skizze-20261014-1100.png');
    expect(waehleSkizze(skizzenStand().liste, SKIZZEN[1]!.name)?.name).toBe(SKIZZEN[1]!.name);
  });

  it('das Fenster kommt wieder nach vorne: die Liste wird neu gelesen', async () => {
    const quelle = wirt();
    registriereSkizzenQuelle(quelle);
    montiere();
    await warteAufWirt();
    const vorher = quelle.gelesen;
    await act(async () => {
      window.dispatchEvent(new Event('focus'));
      await aktualisiereSkizzen();
    });
    expect(quelle.gelesen).toBeGreaterThan(vorher);
  });

  it('eine gewaehlte Skizze, die nicht mehr in der Mappe liegt: Satz statt Bild, Wahl sichtbar', async () => {
    registriereSkizzenQuelle(wirt());
    const { graphId, skizzeId } = montiere();
    act(() => {
      useProject.getState().runCommand('vis.nodeParametrieren', { graphId, nodeId: skizzeId, params: { skizze: 'weg.png' } });
    });
    await warteAufWirt();
    expect(q('skizze-knoten')?.getAttribute('data-stand')).toBe('fehlt');
    expect(q('skizze-bild')).toBeNull();
    expect(q('skizze-satz')?.textContent).toMatch(/liegt nicht mehr in der Mappe/);
    expect(q('skizze-wahl')?.textContent).toBe('weg.png (nicht mehr in der Mappe)');
  });

  it('leere Mappe: der Satz zum iPad', async () => {
    registriereSkizzenQuelle(wirt([]));
    montiere();
    await warteAufWirt();
    expect(q('skizze-knoten')?.getAttribute('data-stand')).toBe('leer');
    expect(q('skizze-satz')?.textContent).toBe(SKIZZE_LEER_SATZ);
    expect(SKIZZE_LEER_SATZ).toBe('Noch keine Skizze in der Mappe — am iPad zeichnen und «In die Mappe legen».');
    expect(q('skizze-wahl')).toBeNull();
  });

  it('wirft der Wirt beim Lesen, steht sein Grund am Knoten', async () => {
    registriereSkizzenQuelle({
      liste: async () => {
        throw new Error('Der Heim-PC antwortet nicht.');
      },
      bildUrl: (n) => n,
    });
    montiere();
    await warteAufWirt();
    expect(q('skizze-knoten')?.getAttribute('data-stand')).toBe('fehler');
    expect(q('skizze-satz')?.textContent).toBe('Die Skizzen liessen sich nicht lesen: Der Heim-PC antwortet nicht.');
    expect(q('skizze-satz')?.getAttribute('role')).toBe('alert');
  });

  it('das Bild wird je Name nur einmal geholt', async () => {
    registriereSkizzenQuelle(wirt());
    await act(async () => {
      await Promise.all([holeSkizzenBild('a.png'), holeSkizzenBild('a.png')]);
      await holeSkizzenBild('a.png');
    });
    expect(abrufe).toEqual(['./skizze?name=a.png']);
    expect(skizzenStand().bilder['a.png']).toMatch(/^data:image\/png;base64,/);
  });
});

describe('KV-SKIZZE-VOM-IPAD · wohin das Bild geht', () => {
  // Entscheid 96 (15.10.2026): seither hat der Render-Knoten genau EINEN Bild-Eingang, «Skizze»
  // (nur von diesem Knoten) — die uebrigen fuenf weisen die Skizze weiter ab. Die Skizze fuehrt
  // dort das Bild; geprueft in `kv-skizze-fuehrt.test.tsx`.
  it('der Render-Knoten nimmt die Skizze nur am Eingang «Skizze» — jeder andere Eingang weist sie ab', () => {
    const render = VIS_NODE_KATALOG['render']!;
    expect(render.inputs.filter((p) => p.typ === 'bild').map((p) => p.name)).toEqual(['skizze']);
    const { runCommand, doc } = useProject.getState();
    const graphId = (runCommand('vis.graphErstellen', { name: 'KV-SKIZZE-RENDER' }).patches[0] as { id: string }).id;
    runCommand('vis.nodeSetzen', { graphId, typ: SKIZZE_IPAD_TYP, x: 0, y: 0 });
    runCommand('vis.nodeSetzen', { graphId, typ: 'render', x: 300, y: 0 });
    const [skizze, rnd] = doc.get<VisGraph>(graphId)!.nodes;
    for (const port of render.inputs.filter((p) => p.name !== 'skizze')) {
      expect(() =>
        runCommand('vis.verbinden', { graphId, from: skizze!.id, fromPort: 'bild', to: rnd!.id, toPort: port.name }),
      ).toThrow(/Port-Typen passen nicht/);
    }
  });

  it('die Bestellung bleibt mit Skizzen-Knoten (am Bildvergleich, nicht am Render) Zeichen fuer Zeichen wie ohne', () => {
    const { runCommand, doc } = useProject.getState();
    const graphId = (runCommand('vis.graphErstellen', { name: 'KV-SKIZZE-AUFTRAG' }).patches[0] as { id: string }).id;
    runCommand('vis.nodeSetzen', { graphId, typ: 'modell', x: 0, y: 0 });
    runCommand('vis.nodeSetzen', { graphId, typ: 'render', x: 300, y: 0 });
    const [modell, rnd] = doc.get<VisGraph>(graphId)!.nodes;
    runCommand('vis.verbinden', { graphId, from: modell!.id, fromPort: 'szene', to: rnd!.id, toPort: 'szene' });
    const ohne = evaluiereGraph(doc, doc.get<VisGraph>(graphId)!).renderAuftraege.get(rnd!.id);
    runCommand('vis.nodeSetzen', { graphId, typ: SKIZZE_IPAD_TYP, x: 0, y: 200 });
    runCommand('vis.nodeSetzen', { graphId, typ: 'vergleich', x: 300, y: 200 });
    const g = doc.get<VisGraph>(graphId)!;
    runCommand('vis.verbinden', { graphId, from: g.nodes[2]!.id, fromPort: 'bild', to: g.nodes[3]!.id, toPort: 'bild1' });
    const mit = evaluiereGraph(doc, doc.get<VisGraph>(graphId)!).renderAuftraege.get(rnd!.id);
    expect(JSON.stringify(mit)).toBe(JSON.stringify(ohne));
  });

  it('am Bildvergleich steht die Skizze als Bild, sobald sie geholt ist', async () => {
    registriereSkizzenQuelle(wirt());
    montiere('vergleich');
    await warteAufWirt();
    const bild = container!.querySelector('.vis-vergleich-bilder img') as HTMLImageElement | null;
    expect(bild?.getAttribute('src')).toMatch(/^data:image\/png;base64,/);
    expect(abrufe).toContain('./skizze?name=skizze-20261014-0912.png');
  });
});
