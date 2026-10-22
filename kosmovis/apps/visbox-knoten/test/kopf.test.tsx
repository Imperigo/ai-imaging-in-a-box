// @vitest-environment jsdom
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { execute, History, KosmoDoc, type VisGraph } from '@kosmo/kernel';
import { useProject } from '../../kosmo-orbit/src/state/project-store';
import { useVisRuntime } from '../../kosmo-orbit/src/modules/vis/vis-runtime';
import { leereKiZustand } from '../../kosmo-orbit/src/modules/vis/ki-werkzeuge';
import { registrierePalettenQuelle } from '../../kosmo-orbit/src/shell/werkzeug-palette/werkzeug-palette';
import { haengeAnWerkzeugsatz, useClaudeAnschluss } from '../../kosmo-orbit/src/state/claude-anschluss';
import { haengeAnKiVerlauf, setzeCoop, setzeCoopZurueck, useKosmoCoop } from '../../kosmo-orbit/src/state/kosmo-coop';
import { leereTaetigkeiten } from '../../kosmo-orbit/src/state/claude-taetigkeit';
import { haengeKiAn, type VisboxKi } from '../src/ki-wirt';
import { haengeWirtAn, liesLage, meldeSichern, useWirt, type VisboxWirt } from '../src/wirt-bruecke';
import { legeThema, THEMA_SCHLUESSEL } from '../src/thema';
import { meldePaletteAn, VisboxClaude, VisboxKopf } from '../src/kopf';
import { sichereBeiAenderung, legeGraphen } from '../src/graph-sichern';
import { schliesseEinstellungen } from '../src/einstellungen';

/**
 * VISBOX-EIGEN (Plan UI-Gleichheit S1/S2, Entscheide 115/116, 20.10.2026): Die Knotenansicht zeigt
 * die Kopfteile von KosmoOrbit — mit denselben Kennungen wie dort — und spricht über die zweite
 * Brücke `visboxWirt` mit der Mac-App. Das Heim-PC-Kennwort läuft dabei nie durch die Seite.
 */

(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

let root: Root | null = null;
let halter: HTMLDivElement | null = null;
let wirtGesendet: Record<string, unknown>[] = [];
let kiGesendet: Record<string, unknown>[] = [];
let ab: (() => void)[] = [];
let graphId = '';
let modellId = '';

const q = (id: string) => document.querySelector<HTMLElement>(`[data-testid="${id}"]`);
const wirt = () => (window as unknown as { visboxWirt: VisboxWirt }).visboxWirt;
const ki = () => (window as unknown as { visboxKi: VisboxKi }).visboxKi;
const wirtBote = { postMessage: (n: unknown) => void wirtGesendet.push(n as Record<string, unknown>) };
const kiBote = { postMessage: (n: unknown) => void kiGesendet.push(n as Record<string, unknown>) };

function neuesDokument(): KosmoDoc {
  const doc = new KosmoDoc();
  graphId = (execute(doc, 'vis.graphErstellen', { name: 'Probe' }).patches[0] as { id: string }).id;
  execute(doc, 'vis.nodeSetzen', { graphId, typ: 'modell', x: 0, y: 0 });
  modellId = doc.get<VisGraph>(graphId)!.nodes[0]!.id;
  return doc;
}

function zeichne(): void {
  halter = document.createElement('div');
  document.body.appendChild(halter);
  root = createRoot(halter);
  act(() =>
    root!.render(
      <>
        <div className="app-wurzel" data-station="vis">
          <VisboxKopf />
        </div>
        <VisboxClaude />
      </>,
    ),
  );
}

beforeEach(() => {
  leereKiZustand();
  leereTaetigkeiten();
  setzeCoopZurueck();
  useProject.setState({ doc: neuesDokument(), history: new History(), journal: [], revision: 0, activeStoreyId: null, selection: [] } as never);
  useVisRuntime.setState({ aktiverGraphId: graphId, laeufe: {} });
  useClaudeAnschluss.setState({ verbunden: false, vorschlaege: [], internet: false, zuletztAktiv: null });
  useWirt.setState({ rechner: null, version: null, leitung: null, sperre: null, sichern: { stand: 'gesichert', iso: null } });
  try {
    localStorage.removeItem(THEMA_SCHLUESSEL);
  } catch {
    /* ohne Speicher */
  }
  wirtGesendet = [];
  kiGesendet = [];
  meldePaletteAn();
  ab = [haengeKiAn(window, kiBote), haengeAnWerkzeugsatz(), haengeAnKiVerlauf(), haengeWirtAn(window, wirtBote)];
});

afterEach(() => {
  if (root) act(() => root!.unmount());
  root = null;
  halter?.remove();
  halter = null;
  for (const f of ab.reverse()) f();
  ab = [];
  registrierePalettenQuelle(null);
  leereKiZustand();
  schliesseEinstellungen();
});

describe('S1 · die Kopfteile stehen mit den Kennungen von KosmoOrbit', () => {
  it('«zu schmal», Palette, Einstellungs-Kreis, Speichern-Kreis, Zweitgruppe', () => {
    zeichne();
    for (const id of [
      'schmal-hinweis',
      'werkzeug-palette',
      'werkzeug-palette-logo',
      'werkzeug-palette-haupt-knoten',
      'werkzeug-palette-haupt-visbox-seite',
      'werkzeug-palette-haupt-mappen',
      'island-einstellungen-kreis',
      'speichern-kreis',
      'island-kopf-zweitgruppe',
      'heimpc-chip',
      'island-undo',
      'island-redo',
      'app-version',
    ]) {
      expect(q(id), id).not.toBeNull();
    }
    // Ausnahmen (UI_AUSNAHMEN.json): kein Sync, kein Rundgang.
    expect(q('sync-toggle')).toBeNull();
    expect(q('starter-guide-start')).toBeNull();
    expect(q('werkzeug-palette-logo')!.getAttribute('aria-label')).toBe('Zur Startansicht');
    expect(q('werkzeug-palette-haupt-knoten')!.getAttribute('aria-current')).toBe('page');
  });

  it('das Thema ist dunkel wie KosmoOrbit und von der App umschaltbar', () => {
    expect(legeThema()).toBe('orbit');
    expect(document.documentElement.dataset.theme).toBe('orbit');
    expect(document.documentElement.dataset.akzent).toBe('tusche');
    wirt().lage({ thema: 'paper' });
    expect(document.documentElement.dataset.theme).toBe('paper');
    expect(legeThema()).toBe('paper');
    wirt().lage({ thema: 'orbit' });
    expect(document.documentElement.dataset.theme).toBe('orbit');
  });

  it('die Knöpfe sagen der App, was sie wollen', () => {
    zeichne();
    expect(wirtGesendet[0]).toEqual({ art: 'bereit' });
    act(() => q('island-einstellungen-kreis')!.click());
    act(() => q('heimpc-chip')!.click());
    act(() => q('werkzeug-palette-haupt-visbox-seite')!.click());
    act(() => q('werkzeug-palette-haupt-mappen')!.click());
    act(() => q('werkzeug-palette-logo')!.click());
    // Seit S4 öffnen Einstellungs-Kreis und Heim-PC-Chip die Einstellungs-Insel in der Seite —
    // kein Wunsch an die App mehr (Probe `assistent-einstellungen.test.tsx`).
    expect(wirtGesendet.slice(1)).toEqual([
      { art: 'oeffne', ziel: 'visbox-seite' },
      // Schritt 3 (21.10.2026, Blatt 36): «Mappen …» öffnet das Fenster der App.
      { art: 'oeffne', ziel: 'mappen' },
      { art: 'oeffne', ziel: 'startansicht' },
    ]);
  });

  it('Fassung und Heim-PC-Chip kommen von der App', () => {
    zeichne();
    expect(q('heimpc-chip')!.textContent).toBe('Heim-PC · …');
    act(() => wirt().lage({ version: 'v0.4.0', rechner: { text: 'Heim-PC · bereit', ton: 'gut' } }));
    expect(q('app-version')!.textContent).toBe('v0.4.0');
    expect(q('heimpc-chip')!.textContent).toBe('Heim-PC · bereit');
  });

  it('Rückgängig der Zweitgruppe nimmt den eigenen Schritt zurück', () => {
    zeichne();
    act(() => void useProject.getState().runCommand('vis.nodeSchieben', { graphId, nodeId: modellId, x: 3, y: 3 }));
    act(() => q('island-undo')!.click());
    expect(useProject.getState().doc.get<VisGraph>(graphId)!.nodes[0]).toMatchObject({ x: 0, y: 0 });
  });

  it('der Speichern-Kreis zeigt die Lage des Sicherns — ohne Handgriffe («Öffnen» ist Ausnahme)', () => {
    zeichne();
    act(() => meldeSichern({ stand: 'fehler', iso: null, grund: 'Kein Heim-PC eingerichtet.' }));
    expect(q('speichern-kreis-punkt')!.dataset.stand).toBe('fehler');
    expect(q('speichern-kreis-meldung')!.textContent).toContain('Kein Heim-PC eingerichtet.');
    act(() => q('speichern-kreis')!.click());
    expect(q('speichern-kreis-karte')).not.toBeNull();
    expect(q('speichern-kreis-oeffnen')).toBeNull();
    expect(q('speichern-kreis-sichern')).toBeNull();
  });
});

describe('graph-sichern meldet seine Lage', () => {
  it('eine abweisende Antwort heisst «NICHT gesichert», mit dem Satz des Heim-PC', async () => {
    vi.useFakeTimers();
    const lagen: string[] = [];
    const senden = vi.fn(async () => ({ ok: false, status: 503, text: async () => 'Ohne Heim-PC wird nichts gesichert.' }));
    const weg = sichereBeiAenderung(senden, 10, (l) => lagen.push(`${l.stand}${l.grund ? `:${l.grund}` : ''}`));
    legeGraphen([{ id: 'visgraph_neu', kind: 'visgraph', name: 'Neu', nodes: [], edges: [] } as unknown as VisGraph]);
    await vi.advanceTimersByTimeAsync(20);
    expect(lagen).toEqual(['sichert', 'fehler:Ohne Heim-PC wird nichts gesichert.']);
    weg();
    vi.useRealTimers();
  });
});

describe('S2 · Claude-Marke, Karten, Erzählzeile, Selbständigkeit', () => {
  it('die Marke steht, sobald die App «verbunden» sagt, und trägt die Selbständigkeit', () => {
    zeichne();
    expect(q('claude-verbunden')).toBeNull();
    act(() => wirt().lage({ claude: { verbunden: true } }));
    act(() => q('claude-verbunden')!.click());
    expect(q('kosmo-maus-schalter')!.getAttribute('aria-label')).toBe('Mitschauen und Bedienen');
    expect(q('kosmo-maus-freigabe-claude-coop')).not.toBeNull();
    expect(q('kosmo-einstellungen-vollautomatik')).not.toBeNull();
    // Seit Stufe 6 (21.10.2026): die Schalter «Mitschauen»/«Bedienen» je Agent, wortgleich.
    for (const u of ['claude', 'kosmo']) {
      for (const art of ['mitschauen', 'bedienen', 'coop']) expect(q(`kosmo-maus-freigabe-${u}-${art}`), `${u}-${art}`).not.toBeNull();
    }
    expect(q('visbox-modus')!.dataset.modus).toBe('karte');
  });

  it('ein Schalter wünscht den Modus bei der App, die App bestätigt ihn', () => {
    zeichne();
    act(() => setzeCoop('claude', true));
    expect(wirtGesendet.at(-1)).toEqual({ art: 'modus', modus: 'coop' });
    act(() => wirt().lage({ claude: { verbunden: true }, modus: 'voll' }));
    expect(useKosmoCoop.getState().vollautomatik).toBe(true);
    act(() => q('claude-verbunden')!.click());
    expect(q('visbox-modus')!.dataset.modus).toBe('voll');
    expect(q('claude-fenster-rahmen')).not.toBeNull();
    expect(q('kosmo-vollautomatik-anzeige')).not.toBeNull();
    act(() => q('kosmo-vollautomatik-anhalten')!.click());
    // Nur echte Klicks halten an (wie in KosmoOrbit) — die Probe klickt nicht echt.
    expect(useKosmoCoop.getState().vollautomatik).toBe(true);
  });

  it('eine Karte von Claude steht an der Marke und in der Erzählzeile; «Anwenden» entscheidet im Werkzeugsatz', () => {
    zeichne();
    act(() => wirt().lage({ claude: { verbunden: true } }));
    act(() => void ki().rufe({ kennung: 'K-1', werkzeug: 'vis_nodeSchieben', argumente: { graphId, nodeId: modellId, x: 8, y: 8 } }, 'karte'));
    expect(q('claude-vorschlag')).not.toBeNull();
    expect(q('erzaehl-zeile')!.dataset.art).toBe('wartet');
    expect(q('claude-karten-zaehler')!.textContent).toBe('1 offen');
    kiGesendet = [];
    act(() => q('claude-vorschlag-anwenden')!.click());
    expect(q('claude-vorschlag')).toBeNull();
    expect(kiGesendet.find((n) => n['art'] === 'entschieden')).toMatchObject({ kennung: 'K-1', angewendet: true });
    expect(useProject.getState().doc.get<VisGraph>(graphId)!.nodes[0]).toMatchObject({ x: 8, y: 8 });
  });

  it('K-10 (Entscheid 131): entschieden wird nur an der Karte unten links — oben keine Knöpfe, unten beide', () => {
    zeichne();
    act(() => wirt().lage({ claude: { verbunden: true } }));
    act(() => void ki().rufe({ kennung: 'K-3', werkzeug: 'vis_nodeSchieben', argumente: { graphId, nodeId: modellId, x: 8, y: 8 } }, 'karte'));
    act(() => void ki().rufe({ kennung: 'K-4', werkzeug: 'vis_nodeSchieben', argumente: { graphId, nodeId: modellId, x: 9, y: 9 } }, 'karte'));
    // Jede offene Karte trägt ihre eigenen Knöpfe (Mehrfach-Karten); die Zeile oben zeigt nur den Satz.
    expect(document.querySelectorAll('[data-testid="claude-vorschlag-anwenden"]')).toHaveLength(2);
    expect(document.querySelectorAll('[data-testid="claude-vorschlag-ablehnen"]')).toHaveLength(2);
    expect(q('claude-vorschlag-text')!.textContent).toBe('Knoten «Modell» verschieben');
    const css = readFileSync(resolve(process.cwd(), 'src/visbox.css'), 'utf8');
    expect(css).toMatch(/\.erzaehl-zeile-knoepfe\s*\{\s*display:\s*none;\s*\}/);
    // Die Knöpfe der Karte sind echte Knöpfe (Tab erreicht sie, Enter/Leertaste lösen aus).
    expect(q('claude-vorschlag-anwenden')!.tagName).toBe('BUTTON');
    act(() => q('claude-vorschlag-ablehnen')!.click());
    expect(document.querySelectorAll('[data-testid="claude-vorschlag"]')).toHaveLength(1);
  });

  it('ein Schritt ohne Karte steht als Coop-Schritt da und lässt sich dort zurücknehmen (Entscheid 114)', () => {
    act(() => wirt().lage({ claude: { verbunden: true }, modus: 'coop' }));
    act(() => void ki().rufe({ kennung: 'K-2', werkzeug: 'vis_nodeSchieben', argumente: { graphId, nodeId: modellId, x: 4, y: 4 } }, 'coop'));
    expect(useKosmoCoop.getState().gruppen.map((g) => g.kennung)).toEqual(['K-2']);
    zeichne();
    expect(q('kosmo-coop-praesenz')).not.toBeNull();
    act(() => q('kosmo-coop-praesenz')!.click());
    expect(q('kosmo-coop-verlauf')).not.toBeNull();
    expect(q('kosmo-coop-schritt')!.dataset.kennung).toBe('K-2');
    // Strg+Z des Architekten trifft Claudes Schritt nicht (getrennte Verläufe).
    expect(useProject.getState().undo()).toBe(false);
  });
});

describe('die zweite Brücke trägt kein Kennwort', () => {
  it('liesLage nimmt nur die genannten Felder', () => {
    const lage = liesLage({ kennwort: 'geheim', anmeldung: { benutzer: 'a', kennwort: 'geheim' }, rechner: { text: 'Heim-PC · bereit', ton: 'gut', kennwort: 'geheim' }, claude: { verbunden: true, token: 'geheim' }, modus: 'weiss-nicht', thema: 'neon' });
    expect(JSON.stringify(lage)).not.toContain('geheim');
    expect(lage).toEqual({ rechner: { text: 'Heim-PC · bereit', ton: 'gut' }, claude: { verbunden: true } });
    wirt().lage({ kennwort: 'geheim' });
    expect(JSON.stringify(useWirt.getState())).not.toContain('geheim');
  });

  it('ohne App geht kein Wunsch hinaus', () => {
    for (const f of ab.splice(3)) f();
    ab.push(haengeWirtAn(window, null));
    zeichne();
    wirtGesendet = [];
    act(() => q('werkzeug-palette-logo')!.click());
    expect(wirtGesendet).toEqual([]);
  });
});
