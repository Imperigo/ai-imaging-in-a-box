// @vitest-environment jsdom
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { act, createElement } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { execute, History, KosmoDoc, type VisGraph } from '@kosmo/kernel';
import { useProject } from '../../kosmo-orbit/src/state/project-store';
import { useVisRuntime } from '../../kosmo-orbit/src/modules/vis/vis-runtime';
import { leereKiZustand, offeneVorschlaege } from '../../kosmo-orbit/src/modules/vis/ki-werkzeuge';
import { setzeKosmoMausZurueck } from '../../kosmo-orbit/src/state/kosmo-maus-freigabe';
import { beendeNachlauf, KARTEN_SELEKTOR, sperrGrund } from '../../kosmo-orbit/src/state/kosmo-maus';
import { setzeCoopZurueck } from '../../kosmo-orbit/src/state/kosmo-coop';
import { registriereKosmoName } from '../../kosmo-orbit/src/state/kosmo-name';
import { haengeAnWerkzeugsatz, setzeClaudeLage } from '../../kosmo-orbit/src/state/claude-anschluss';
import { ErzaehlZeile } from '../../kosmo-orbit/src/shell/claude-anschluss/ErzaehlZeile';
import { haengeKiAn, type VisboxKi } from '../src/ki-wirt';

/**
 * FUND E des Mac-Demolaufs «Skizze vom iPad bis zum Bild» (Visbox 0.3.34, 22.10.2026): ein
 * `vis_render` kam ueber MCP als «ANGEWENDET vom Architekten» zurueck, obwohl der Modus «Karte» war
 * und der Architekt keine Karte angewendet hatte. «ANGEWENDET vom Architekten» schreibt NUR
 * `anwenden` (Knopf «Anwenden» einer Karte). Zwei Knoepfe tragen ihn: die Karte unten links
 * (`claude-anschluss`, gesperrt) — und die Erzaehlzeile oben in der Mitte, die im Zustand «wartet»
 * Anwenden/Ablehnen selbst traegt. DIE war fuer die eigene Maus der KI (`visbox_maus`) offen:
 * Claude konnte seinen eigenen Render-Vorschlag anwenden, und der Auftrag ging an die Bruecke.
 *
 * Gegen den alten Stand rot (die Maus klickte, die Karte war weg, `visRenderAuftrag` stand im
 * Dokument); seit dem Fix gruen.
 */

let graphId = '';
let renderId = '';
let ab: (() => void)[] = [];
let root: Root | null = null;
const ki = () => (window as unknown as { visboxKi: VisboxKi }).visboxKi;
const q = (id: string) => document.querySelector<HTMLElement>(`[data-testid="${id}"]`);

function neuesDokument(): KosmoDoc {
  const doc = new KosmoDoc();
  graphId = (execute(doc, 'vis.graphErstellen', { name: 'Probe' }).patches[0] as { id: string }).id;
  execute(doc, 'vis.nodeSetzen', { graphId, typ: 'modell', x: 0, y: 0 });
  execute(doc, 'vis.nodeSetzen', { graphId, typ: 'render', x: 300, y: 0 });
  renderId = doc.get<VisGraph>(graphId)!.nodes[1]!.id;
  return doc;
}

beforeEach(() => {
  vi.spyOn(Element.prototype, 'getBoundingClientRect').mockImplementation(function (this: Element) {
    const i = [...document.querySelectorAll('*')].indexOf(this);
    return { left: 10, top: 10 + i * 30, width: 100, height: 20, right: 110, bottom: 30 + i * 30, x: 10, y: 10 + i * 30, toJSON: () => ({}) } as DOMRect;
  });
  (globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;
  leereKiZustand();
  setzeKosmoMausZurueck();
  setzeCoopZurueck();
  beendeNachlauf();
  registriereKosmoName('Assistent');
  useProject.setState({ doc: neuesDokument(), history: new History(), journal: [], revision: 0, activeStoreyId: null, selection: [] } as never);
  useVisRuntime.setState({ aktiverGraphId: graphId, laeufe: {} });
  ab = [haengeKiAn(window, null), haengeAnWerkzeugsatz()];
  setzeClaudeLage({ verbunden: true });
  const halter = document.createElement('div');
  document.body.appendChild(halter);
  root = createRoot(halter);
  act(() => root!.render(createElement(ErzaehlZeile)));
});

afterEach(() => {
  if (root) act(() => root!.unmount());
  root = null;
  for (const f of ab) f();
  leereKiZustand();
  registriereKosmoName(null);
  document.body.innerHTML = '';
  vi.restoreAllMocks();
});

describe('Fund E: vis_render ueber MCP im Modus Karte', () => {
  it('legt eine Karte; die Erzaehlzeile traegt «Anwenden» — und die Maus der KI darf es nicht druecken', async () => {
    let r: ReturnType<VisboxKi['rufe']> | null = null;
    act(() => void (r = ki().rufe({ kennung: 'K-1', werkzeug: 'vis_render', argumente: { graphId, nodeId: renderId, kameraWahl: 'auto', backbone: 'z-image-turbo', guete: 'vorschau' } }, 'karte')));
    expect(r && 'karte' in r).toBe(true);
    expect(q('erzaehl-zeile')?.dataset.art).toBe('wartet');
    const anwenden = q('erzaehl-zeile-anwenden')!;
    expect(anwenden).not.toBeNull();
    // Die Regel an EINER Stelle: beide Knoepfe der Erzaehlzeile sind Kartenknoepfe.
    expect(anwenden.closest(KARTEN_SELEKTOR)).not.toBeNull();
    expect(sperrGrund(q('erzaehl-zeile-ablehnen')!)).toMatch(/nur der Architekt/);

    let m = { text: '' };
    await act(async () => void (m = await ki().maus('claude', { aktion: 'klick', testid: 'erzaehl-zeile-anwenden' })));
    expect(m.text).toMatch(/^VERWEIGERT/);
    // Die Karte liegt weiter, nichts ist bestellt.
    expect(offeneVorschlaege().map((v) => [v.kennung, v.art])).toEqual([['K-1', 'rendern']]);
    expect(useProject.getState().doc.settings.visRenderAuftrag ?? null).toBeNull();
  });

  it('auch «Ablehnen» in der Erzaehlzeile bleibt beim Architekten', async () => {
    act(() => void ki().rufe({ kennung: 'K-2', werkzeug: 'vis_render', argumente: { graphId, nodeId: renderId } }, 'karte'));
    let m = { text: '' };
    await act(async () => void (m = await ki().maus('assistent', { aktion: 'klick', testid: 'erzaehl-zeile-ablehnen' })));
    expect(m.text).toMatch(/^VERWEIGERT/);
    expect(offeneVorschlaege().map((v) => v.kennung)).toEqual(['K-2']);
  });

  it('der Architekt selbst wendet in der Erzaehlzeile an wie bisher', () => {
    act(() => void ki().rufe({ kennung: 'K-3', werkzeug: 'vis_render', argumente: { graphId, nodeId: renderId } }, 'karte'));
    act(() => q('erzaehl-zeile-anwenden')!.click());
    expect(offeneVorschlaege()).toHaveLength(0);
    expect(useProject.getState().doc.settings.visRenderAuftrag).toMatchObject({ graphId, nodeId: renderId });
  });
});
