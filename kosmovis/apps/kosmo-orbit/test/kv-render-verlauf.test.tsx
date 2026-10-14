// @vitest-environment jsdom
import { readFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { evaluiereGraph, type Sheet, type VisGraph } from '@kosmo/kernel';
import { basisNodeHoehe, groessteNodeHoehe, NodeCanvas, RENDER_ZEILEN, VERLAUF_ZEILE_H, zeilenHoehe } from '../src/modules/vis/NodeCanvas';
import {
  laufGrund,
  laufUrteil,
  treueText,
  uhrzeitText,
  verlaufReihe,
  verlaufSichtbar,
  VERLAUF_ZAHL,
  zeitpunktText,
} from '../src/modules/vis/render-verlauf';
import type { JobQa } from '../src/modules/vis/vis-jobs';
import { memoKey, useVisRuntime, VERLAUF_BEHALTEN, type NodeLauf } from '../src/modules/vis/vis-runtime';
import { useProject } from '../src/state/project-store';

// Verlauf-Nachgang: der Verlauf zeigt Ortszeit. Die Probe legt die Zone fest,
// damit sie auf jedem Rechner dasselbe liest (07.10.2026: UTC+2).
process.env['TZ'] = 'Europe/Zurich';

/**
 * Entscheid 68 / E174 (Owner, 07.10.2026) — der Verlauf am Render-Knoten,
 * gebaut nach dem Entwurfsblatt «15 · Verlauf am Render-Knoten».
 *
 * Der Befund, gegen den gebaut wurde: `setzeLauf` ersetzte den Lauf eines
 * Knotens einfach, und ein neues «Ausführen» liess das vorige Ergebnis fuer
 * die Oberflaeche verschwinden. Jetzt wandert ein abgeloester fertiger Lauf
 * in den `verlauf`, und der Knoten zeigt die letzten vier als Reihe.
 *
 * Geprueft wird, was die Vorlage verspricht: neuestes links, hoechstens vier,
 * unter vier keine Platzhalter, ein Punkt je Urteil, ein Klick zeigt gross und
 * laesst Hauptbild, Blatt und Auswahl in Ruhe, vor/zurueck/Escape, die Marke
 * «Lizenz offen» in der grossen Ansicht, und nichts wird geloescht.
 */

class StubResizeObserver {
  observe(): void {}
  unobserve(): void {}
  disconnect(): void {}
}
(globalThis as unknown as { ResizeObserver: typeof StubResizeObserver }).ResizeObserver = StubResizeObserver;
(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;
if (!('createObjectURL' in URL)) {
  Object.assign(URL, { createObjectURL: () => 'blob:stub', revokeObjectURL: () => undefined });
}

const QA_OK: JobQa = { verdict: { passed: true } };
const QA_FEHL: JobQa = {
  verdict: { passed: false, reason: 'Das Bild zeigt einen zusätzlichen Anbau rechts, den die Geometrie nicht hat.' },
  geometry: { rho_maske: 0.41, threshold: 0.65, passed: false, method: 'depthanything-v2-redepth' },
};
const QA_NICHT_ZUSTAENDIG: JobQa = {
  verdict: { passed: true },
  geometry: { status: 'not_applicable', threshold: 0.65, passed: true, method: 'depthanything-v2-redepth' },
};

let root: Root | null = null;
let container: HTMLDivElement | null = null;
let graphId = '';
let nodeId = '';
let schluessel = '';

function stubBridge(): void {
  vi.stubGlobal('fetch', (async (url: unknown) => {
    const href = String(url);
    if (href.includes('/artifacts/')) {
      return { ok: true, status: 200, blob: async () => new Blob(['x'], { type: 'image/png' }) } as Response;
    }
    return { ok: false, status: 404, json: async () => ({}) } as Response;
  }) as unknown as typeof fetch);
}

/** Ein fertiger Lauf mit Bild, wie ihn der Poll hinterlaesst. */
function fertig(nr: number, extra: Partial<NodeLauf> = {}): NodeLauf {
  return {
    status: 'fertig',
    jobId: `job-${nr}`,
    bild: `bild-${nr}.png`,
    qa: QA_OK,
    memoKey: schluessel,
    gestartetUm: Date.UTC(2026, 9, 7, 16, nr * 10),
    fertigUm: Date.UTC(2026, 9, 7, 16, nr * 10 + 2),
    worker: 'fake-worker',
    engineUsed: 'z-image-turbo',
    ...extra,
  };
}

function laeufe(...l: NodeLauf[]): void {
  for (const lauf of l) act(() => useVisRuntime.getState().setzeLauf(nodeId, lauf));
}

function montiere(): void {
  container = document.createElement('div');
  document.body.appendChild(container);
  root = createRoot(container);
  act(() => root!.render(<NodeCanvas graphId={graphId} />));
}

const q = <T extends Element = HTMLElement>(sel: string, im: ParentNode = document): T | null => im.querySelector<T>(sel);
const qa = (sel: string, im: ParentNode = document): HTMLElement[] => [...im.querySelectorAll<HTMLElement>(sel)];
const daumen = (): HTMLElement[] => qa('[data-testid="render-verlauf-bild"]', container!);
const knotenHoehe = (): number =>
  Number.parseFloat(q<HTMLElement>('[data-testid="vis-node-render"]', container!)!.style.height);
const gross = (): HTMLElement | null => q('[data-testid="render-verlauf-gross"]');
const titel = (): string => q('[data-testid="render-verlauf-gross-titel"]')!.textContent ?? '';

function klick(el: Element): void {
  act(() => {
    el.dispatchEvent(new MouseEvent('click', { bubbles: true }));
  });
}
function taste(el: Element, key: string): KeyboardEvent {
  const e = new KeyboardEvent('keydown', { key, bubbles: true, cancelable: true });
  act(() => {
    el.dispatchEvent(e);
  });
  return e;
}

beforeEach(() => {
  stubBridge();
  useVisRuntime.setState({ laeufe: {}, verlauf: {}, laufZaehler: {} });
  const { runCommand, doc } = useProject.getState();
  graphId = (runCommand('vis.graphErstellen', { name: `Verlauf-${Math.random()}` }).patches[0] as { id: string }).id;
  runCommand('vis.nodeSetzen', { graphId, typ: 'render', x: 40, y: 20 });
  const graph = doc.get<VisGraph>(graphId)!;
  nodeId = graph.nodes.at(-1)!.id;
  schluessel = memoKey(evaluiereGraph(doc, graph).renderAuftraege.get(nodeId)!);
});

afterEach(() => {
  if (root) act(() => root!.unmount());
  container?.remove();
  root = null;
  container = null;
  vi.unstubAllGlobals();
});

describe('Verlauf am Render-Knoten — die Ablösung im Laufzeit-Zustand', () => {
  it('ein neuer Lauf schiebt den fertigen alten in den Verlauf, neuester zuerst, höchstens vier', () => {
    laeufe(fertig(1), fertig(2), fertig(3));
    const s = useVisRuntime.getState();
    expect(s.laeufe[nodeId]!.jobId).toBe('job-3');
    expect(s.verlauf[nodeId]!.map((l) => l.jobId)).toEqual(['job-2', 'job-1']);

    laeufe(fertig(4), fertig(5), fertig(6), fertig(7));
    expect(useVisRuntime.getState().verlauf[nodeId]!.map((l) => l.jobId)).toEqual(['job-6', 'job-5', 'job-4', 'job-3']);
    expect(VERLAUF_BEHALTEN).toBe(4);
  });

  it('kein Eintrag für einen Lauf ohne Bild, und derselbe Auftrag zählt nicht als Ablösung', () => {
    laeufe(fertig(1));
    // Ein neuer Auftrag geht ab: der fertige alte wandert in den Verlauf …
    laeufe({ status: 'gesendet', memoKey: schluessel, gestartetUm: Date.now() });
    expect(useVisRuntime.getState().verlauf[nodeId]!.map((l) => l.jobId)).toEqual(['job-1']);
    // … ein abgebrochener oder fehlgeschlagener Lauf dagegen nicht.
    laeufe({ status: 'fehler', fehler: 'x', memoKey: schluessel }, fertig(2));
    expect(useVisRuntime.getState().verlauf[nodeId]!.map((l) => l.jobId)).toEqual(['job-1']);
    // Derselbe Auftrag noch einmal gesetzt (z. B. aus Kosmo): keine Ablösung.
    laeufe(fertig(2));
    expect(useVisRuntime.getState().verlauf[nodeId]!.map((l) => l.jobId)).toEqual(['job-1']);
  });

  it('verlaufReihe: der aktuelle Lauf vorne, dann die abgelösten; ohne Bild nichts, doppelt einmal, höchstens vier', () => {
    const r = verlaufReihe(fertig(5), [fertig(4), fertig(3), fertig(4), fertig(2), fertig(1)]);
    expect(r.map((e) => e.jobId)).toEqual(['job-5', 'job-4', 'job-3', 'job-2']);
    expect(VERLAUF_ZAHL).toBe(4);
    const laufend = verlaufReihe({ status: 'rendert', memoKey: 'x', jobId: 'job-9' }, [fertig(2), fertig(1)]);
    expect(laufend.map((e) => e.jobId)).toEqual(['job-2', 'job-1']);
    expect(verlaufSichtbar(verlaufReihe(fertig(1), undefined))).toBe(false);
    expect(verlaufSichtbar(verlaufReihe(fertig(2), [fertig(1)]))).toBe(true);
  });
});

describe('Verlauf am Render-Knoten — die Reihe am Knoten', () => {
  it('nach dem ersten Lauf gibt es noch keinen Verlauf; danach wächst die Reihe ohne Platzhalter bis vier', () => {
    montiere();
    laeufe(fertig(1));
    expect(q('[data-testid="render-verlauf"]', container!)).toBeNull();
    const ohne = knotenHoehe();

    laeufe(fertig(2));
    expect(daumen()).toHaveLength(2);
    expect(q('[data-testid="render-verlauf"]', container!)!.textContent).toContain('die letzten 2 Läufe · neuester links');
    expect(knotenHoehe(), 'der Knoten wächst um genau die Reihe').toBe(ohne + VERLAUF_ZEILE_H);

    laeufe(fertig(3));
    expect(daumen()).toHaveLength(3);
    laeufe(fertig(4), fertig(5));
    expect(daumen()).toHaveLength(4);
    expect(knotenHoehe(), 'die Reihe ist bei vier so hoch wie bei zwei').toBe(ohne + VERLAUF_ZEILE_H);
  });

  it('das neueste steht links und ist das Hauptbild; die Uhrzeit steht darunter', () => {
    montiere();
    laeufe(fertig(1), fertig(2), fertig(3), fertig(4), fertig(5));
    expect(daumen().map((d) => d.dataset['job'])).toEqual(['job-5', 'job-4', 'job-3', 'job-2']);
    expect(daumen()[0]!.classList.contains('vis-verlauf-knopf--haupt')).toBe(true);
    expect(daumen().slice(1).some((d) => d.classList.contains('vis-verlauf-knopf--haupt'))).toBe(false);
    // Owner-Entscheid 71: keine Uhrzeitzeile mehr unter dem Daumenbild — die
    // Zeit steht im Vorleser-Label (und im Laufschild, in der grossen Ansicht).
    expect(q('.vis-verlauf-zeit', container!)).toBeNull();
    expect(daumen()[0]!.textContent).not.toMatch(/\d\d:\d\d/);
    expect(daumen()[0]!.getAttribute('aria-label')).toBe('Lauf 5 von 18:52, bestanden, gross anzeigen');
    expect(daumen()[3]!.getAttribute('aria-label')).toBe('Lauf 2 von 18:22, bestanden, gross anzeigen');
  });

  // HomeStation 266/267: das Urteil kommt allein aus dem Verdikt, wie an der
  // Kachel (`qaUrteil`); «nicht zustaendig» betrifft nur Zahl und Sterne.
  it('jedes Daumenbild trägt den Punkt seines Urteils: bestanden, durchgefallen, ohne QA', () => {
    montiere();
    laeufe(
      fertig(1, { qa: QA_NICHT_ZUSTAENDIG }),
      fertig(2, { qa: undefined }),
      fertig(3, { qa: QA_FEHL }),
      fertig(4, { qa: QA_OK }),
    );
    expect(daumen().map((d) => d.dataset['urteil'])).toEqual(['bestanden', 'durchgefallen', 'ohne-qa', 'bestanden']);
    const punkte = qa('[data-testid="render-verlauf-punkt"]', container!);
    expect(punkte.map((p) => [...p.classList].find((k) => k.startsWith('vis-verlauf-punkt--')))).toEqual([
      'vis-verlauf-punkt--bestanden',
      'vis-verlauf-punkt--durchgefallen',
      'vis-verlauf-punkt--ohne-qa',
      'vis-verlauf-punkt--bestanden',
    ]);
  });

  it('während ein neuer Lauf rechnet, zeigt die Reihe die abgelösten Läufe weiter', () => {
    montiere();
    laeufe(fertig(1), fertig(2), fertig(3), { status: 'rendert', jobId: 'job-9', memoKey: schluessel, gestartetUm: Date.now() });
    expect(daumen().map((d) => d.dataset['job'])).toEqual(['job-3', 'job-2', 'job-1']);
    expect(daumen().some((d) => d.classList.contains('vis-verlauf-knopf--haupt'))).toBe(false);
  });

  it('nichts wird gelöscht: kein Knopf dafür, und der Verlauf hält die abgelösten Läufe', () => {
    montiere();
    laeufe(fertig(1), fertig(2), fertig(3));
    const reihe = q('[data-testid="render-verlauf"]', container!)!;
    expect(reihe.querySelectorAll('button')).toHaveLength(3);
    const knopfText = (b: HTMLElement): string =>
      `${b.textContent ?? ''} ${b.getAttribute('aria-label') ?? ''} ${b.dataset['testid'] ?? ''}`;
    expect(qa('button', reihe).map(knopfText).filter((t) => /lösch|loesch|entfern/i.test(t))).toEqual([]);
    klick(daumen()[2]!);
    expect(qa('button', gross()!).map(knopfText).filter((t) => /lösch|loesch|entfern/i.test(t))).toEqual([]);
    expect(qa('button', gross()!).map((b) => b.getAttribute('aria-label'))).toEqual(['Vorheriger Lauf', 'Nächster Lauf', 'Schliessen']);
    expect(useVisRuntime.getState().verlauf[nodeId]!.map((l) => l.jobId)).toEqual(['job-2', 'job-1']);
  });

  it('die Reihe ist in der Stilvorlage genau so hoch, wie der Knoten für sie wächst', () => {
    const css = readFileSync(
      path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../src/modules/vis/vis-visual.css'),
      'utf8',
    );
    const block = /\n\.vis-verlauf \{([^}]*)\}/.exec(css)?.[1] ?? '';
    expect(block).toContain(`height: ${VERLAUF_ZEILE_H}px;`);
    // Abstand 2 + Kopf 26 + Daumenbild 32 — Owner-Entscheid 71: ohne die
    // Uhrzeitzeile (2 + 12) 14 px niedriger als zuvor (84); WebKitGTK-
    // Geraeteprobe (1440 x 900): die Abstaende 8 -> 2 und 4 -> 0, noch
    // einmal 10 px niedriger (70 -> 60).
    expect(block).toContain('grid-template-rows: 26px 32px;');
    expect(block).toContain('padding-top: var(--k-s1);');
    expect(block).toContain('row-gap: 0;');
    expect(2 + 26 + 0 + 32).toBe(VERLAUF_ZEILE_H);
    expect(VERLAUF_ZEILE_H).toBe(60);
    expect(css).not.toContain('.vis-verlauf-zeit');
    // Die Platzsuche rechnet mit derselben Zahl: groesste Hoehe = Basis +
    // Laufzuschlag + Reihe.
    const laufZuschlag = zeilenHoehe(RENDER_ZEILEN, true) - zeilenHoehe(RENDER_ZEILEN);
    expect(groessteNodeHoehe('render')).toBe(basisNodeHoehe('render') + laufZuschlag + VERLAUF_ZEILE_H);
  });
});

describe('Verlauf am Render-Knoten — Abzeichen im Hauptbild (Nachtrag 4)', () => {
  const abzeichenLauf = (): HTMLElement | null => q('[data-testid="render-hauptbild-lauf"]', container!);
  const abzeichenUrteil = (): HTMLElement | null => q('[data-testid="render-hauptbild-urteil"]', container!);

  it('wie die Vorlage: erst wenn die Reihe steht, dann «LAUF n · hh:mm» und das Urteil des neuesten Laufs', () => {
    montiere();
    laeufe(fertig(1));
    expect(q('[data-testid="render-bild"], [data-testid="render-bild-laedt"]', container!)).not.toBeNull();
    expect(abzeichenLauf(), 'nach dem ersten Lauf zeigt die Vorlage keinen Verlauf und keine Nummer').toBeNull();

    laeufe(fertig(2), fertig(3, { qa: QA_FEHL }));
    expect(abzeichenLauf()!.textContent).toBe('LAUF 3 · 18:32');
    expect(abzeichenUrteil()!.dataset['urteil']).toBe('durchgefallen');
    expect(abzeichenUrteil()!.textContent).toBe('durchgefallen');
    expect(abzeichenUrteil()!.dataset['urteil'], 'dieselbe Logik wie der Punkt am Daumenbild').toBe(daumen()[0]!.dataset['urteil']);
    expect(q('.vis-verlauf-punkt--durchgefallen', abzeichenUrteil()!)).not.toBeNull();

    laeufe(fertig(4), fertig(5, { qa: undefined }));
    expect(abzeichenLauf()!.textContent).toBe('LAUF 5 · 18:52');
    expect(abzeichenUrteil()!.textContent).toBe('ohne QA');
  });

  it('die Nummer ist dieselbe wie in der grossen Ansicht', () => {
    montiere();
    laeufe(fertig(1), fertig(2), fertig(3));
    klick(daumen()[0]!);
    expect(titel()).toBe('LAUF 3');
    expect(abzeichenLauf()!.textContent).toMatch(/^LAUF 3 · /);
  });

  it('liegt im Bild: ohne Knotenhöhe, ohne Zeiger, und verschwindet, während ein neuer Lauf rechnet', () => {
    montiere();
    laeufe(fertig(1), fertig(2));
    const mitAbzeichen = knotenHoehe();
    const huelle = abzeichenLauf()!.parentElement!;
    expect(huelle.classList.contains('vis-hauptbild-abzeichen')).toBe(true);
    expect(huelle.parentElement!.dataset['testid']).toBe('render-hauptbild');
    expect(huelle.getAttribute('aria-hidden')).toBe('true');
    expect(huelle.closest('[data-zeile]')!.getAttribute('data-zeile'), 'keine eigene Zeile im Register').toBe('bild');
    const css = readFileSync(
      path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../src/modules/vis/vis-visual.css'),
      'utf8',
    );
    const block = /\n\.vis-hauptbild-abzeichen \{([^}]*)\}/.exec(css)?.[1] ?? '';
    expect(block).toContain('position: absolute;');
    expect(block).toContain('pointer-events: none;');
    // Der Rahmen um das Bild hat keine eigene Hoehe.
    const rahmen = /\n\.vis-hauptbild \{([^}]*)\}/.exec(css)?.[1] ?? '';
    expect(rahmen).not.toMatch(/height|padding|margin-block|border/);

    laeufe(fertig(3));
    expect(knotenHoehe(), 'drei Laeufe, dieselbe Hoehe wie zwei').toBe(mitAbzeichen);
    laeufe({ status: 'rendert', jobId: 'job-9', memoKey: schluessel, gestartetUm: Date.now() });
    expect(abzeichenLauf()).toBeNull();
  });
});

describe('Verlauf am Render-Knoten — ein Klick zeigt gross', () => {
  it('der Klick öffnet die grosse Ansicht ausserhalb der Leinwand, mit Urteil, Grund, Treue, Bildwerkzeug und Herkunft', () => {
    montiere();
    laeufe(fertig(1), fertig(2), fertig(3, { qa: QA_FEHL, engineUsed: 'qwen-image-2.1', worker: 'abholer-2' }), fertig(4));
    klick(daumen()[1]!);
    const g = gross()!;
    expect(g).not.toBeNull();
    expect(container!.contains(g), 'die Ansicht liegt nicht in der verschobenen Knotenebene').toBe(false);
    expect(g.closest('.k-dialog-scrim')!.parentElement).toBe(document.body);
    expect(g.getAttribute('aria-label')).toBe('Lauf 3 gross');
    expect(titel()).toBe('LAUF 3');
    expect(q('[data-testid="render-verlauf-gross-stelle"]')!.textContent).toBe('2 von 4 im Verlauf');
    expect(g.textContent).toContain('07.10.2026 · 18:32');
    expect(g.textContent).not.toContain('UTC');
    const urteil = q('[data-testid="render-verlauf-gross-urteil"]')!;
    expect(urteil.dataset['urteil']).toBe('durchgefallen');
    expect(urteil.textContent).toBe('durchgefallen');
    expect(q('[data-testid="render-verlauf-gross-grund"]')!.textContent).toBe(
      'Das Bild zeigt einen zusätzlichen Anbau rechts, den die Geometrie nicht hat.',
    );
    expect(q('[data-testid="render-verlauf-gross-treue"]')!.textContent).toBe('0,41 / 0,80');
    expect(q('[data-testid="render-verlauf-gross-werkzeug"]')!.textContent).toBe('qwen-image-2.1');
    expect(q('[data-testid="render-verlauf-gross-herkunft"]')!.textContent).toBe('abholer-2');
    expect(q('[data-testid="render-verlauf-gross-fuss"]')!.textContent).toContain('Am Knoten bleibt Lauf 4 das Hauptbild. Hier wird nur angesehen.');
    expect(q('[data-testid="render-verlauf-gross-bild"]') ?? q('[data-testid="render-verlauf-gross-bild-laedt"]')).not.toBeNull();
  });

  it('der Klick ändert das Hauptbild nicht, legt nichts aufs Blatt und wählt nichts aus', () => {
    montiere();
    laeufe(fertig(1), fertig(2), fertig(3));
    const lauf = useVisRuntime.getState().laeufe[nodeId];
    const verlauf = useVisRuntime.getState().verlauf[nodeId];
    const hauptVorher = q('[data-testid="render-bild"], [data-testid="render-bild-laedt"]', container!);
    const { revision, selection } = useProject.getState();
    const blattBilder = (): number =>
      useProject
        .getState()
        .doc.byKind<Sheet>('sheet')
        .reduce((s, b) => s + (b.bilder ?? []).length, 0);
    const bilderVorher = blattBilder();
    const knoten = q<HTMLElement>('[data-testid="vis-node-render"]', container!)!;

    klick(daumen()[2]!);
    expect(gross()).not.toBeNull();
    expect(useVisRuntime.getState().laeufe[nodeId], 'der Lauf des Knotens ist unberührt').toBe(lauf);
    expect(useVisRuntime.getState().verlauf[nodeId]).toBe(verlauf);
    expect(q('[data-testid="render-bild"], [data-testid="render-bild-laedt"]', container!), 'das Hauptbild bleibt dasselbe Element').toBe(hauptVorher);
    expect(useProject.getState().revision, 'kein Befehl am Projekt').toBe(revision);
    expect(useProject.getState().selection).toEqual(selection);
    expect(blattBilder()).toBe(bilderVorher);
    expect(knoten.getAttribute('aria-pressed'), 'der Knoten ist nicht ausgewählt').toBe('false');
    expect(knoten.style.left).toBe('40px');
    expect(knoten.style.top).toBe('20px');
  });

  it('vor und zurück wandern durch die Reihe, Pfeiltasten ebenso; an den Enden ist der Knopf gesperrt', () => {
    montiere();
    laeufe(fertig(1), fertig(2), fertig(3), fertig(4));
    klick(daumen()[0]!);
    expect(titel()).toBe('LAUF 4');
    const vor = q<HTMLButtonElement>('[data-testid="render-verlauf-vor"]')!;
    const zurueck = q<HTMLButtonElement>('[data-testid="render-verlauf-zurueck"]')!;
    expect(vor.disabled).toBe(true);
    klick(zurueck);
    expect(titel()).toBe('LAUF 3');
    expect(gross()!.dataset['job']).toBe('job-3');
    taste(gross()!, 'ArrowLeft');
    taste(gross()!, 'ArrowLeft');
    expect(titel()).toBe('LAUF 1');
    expect(q<HTMLButtonElement>('[data-testid="render-verlauf-zurueck"]')!.disabled).toBe(true);
    taste(gross()!, 'ArrowRight');
    expect(titel()).toBe('LAUF 2');
    klick(q('[data-testid="render-verlauf-vor"]')!);
    expect(titel()).toBe('LAUF 3');
    // Das Hauptbild wechselt bei alledem nicht.
    expect(useVisRuntime.getState().laeufe[nodeId]!.jobId).toBe('job-4');
  });

  it('Escape schliesst — und endet in der Ansicht, statt die Auswahl der Leinwand zu leeren; Schliessen und Schleier ebenso', () => {
    montiere();
    laeufe(fertig(1), fertig(2));
    const fenster = vi.fn();
    window.addEventListener('keydown', fenster);
    try {
      klick(daumen()[1]!);
      expect(gross()).not.toBeNull();
      expect(document.activeElement?.getAttribute('data-testid')).toBe('render-verlauf-schliessen');
      const e = taste(document.activeElement!, 'Escape');
      expect(gross()).toBeNull();
      expect(e.defaultPrevented).toBe(true);
      expect(fenster, 'Escape erreicht den Fenster-Horcher der Leinwand nicht').not.toHaveBeenCalled();
    } finally {
      window.removeEventListener('keydown', fenster);
    }
    klick(daumen()[1]!);
    klick(q('[data-testid="render-verlauf-schliessen"]')!);
    expect(gross()).toBeNull();
    klick(daumen()[0]!);
    klick(q('[data-testid="render-verlauf-gross-scrim"]')!);
    expect(gross()).toBeNull();
  });

  it('«Lizenz offen» steht in der grossen Ansicht bei einem Lauf mit offener Lizenz, sonst nicht', () => {
    montiere();
    laeufe(
      fertig(1, { lizenzOffen: true, engineUsed: 'qwen-image-2.1', engineLicense: 'Qwen Research License Agreement' }),
      fertig(2),
    );
    klick(daumen()[1]!);
    const marke = q('[data-testid="render-verlauf-gross-lizenz-offen"]')!;
    expect(marke.textContent).toBe('⚠ Lizenz offen');
    expect(marke.closest('.k-tooltip')!.textContent).toContain(
      'Gerechnet mit qwen-image-2.1 (Qwen Research License Agreement). Die Lizenz ist vor einer Veröffentlichung zu klären.',
    );
    taste(gross()!, 'ArrowRight');
    expect(titel()).toBe('LAUF 2');
    expect(q('[data-testid="render-verlauf-gross-lizenz-offen"]')).toBeNull();
  });
});

describe('Verlauf-Nachgang (HomeStation 08.10.2026) — Nummer, Treue, Glas', () => {
  it('die Nummer zählt fortlaufend am Knoten, auch wenn ältere Läufe aus der Reihe fallen', () => {
    montiere();
    laeufe(fertig(1), fertig(2), fertig(3), fertig(4), fertig(5), fertig(6));
    expect(q('[data-testid="render-hauptbild-lauf"]', container!)!.textContent).toMatch(/^LAUF 6 · /);
    expect(daumen().map((d) => d.getAttribute('aria-label')!.split(' von ')[0])).toEqual(['Lauf 6', 'Lauf 5', 'Lauf 4', 'Lauf 3']);
    klick(daumen()[3]!);
    expect(titel()).toBe('LAUF 3');
    expect(q('[data-testid="render-verlauf-gross-stelle"]')!.textContent).toBe('4 von 4 im Verlauf');
    expect(q('[data-testid="render-verlauf-gross-fuss"]')!.textContent).toContain('Am Knoten bleibt Lauf 6 das Hauptbild.');
    expect(useVisRuntime.getState().laufZaehler[nodeId]).toBe(6);
  });

  it('gezählt werden fertige Läufe mit Bild — auch der Weg über den Poll; Fehler und Abbrüche nicht', () => {
    laeufe(fertig(1));
    // Der echte Weg: abgesendet ohne Bild, der Poll macht ihn fertig.
    laeufe({ status: 'gesendet', memoKey: schluessel, gestartetUm: Date.now() });
    act(() => useVisRuntime.getState().patchLauf(nodeId, { jobId: 'job-2' }));
    expect(useVisRuntime.getState().laeufe[nodeId]!.laufNummer).toBeUndefined();
    act(() => useVisRuntime.getState().patchLauf(nodeId, { status: 'fertig', bild: 'b.png', qa: QA_OK }));
    expect(useVisRuntime.getState().laeufe[nodeId]!.laufNummer).toBe(2);
    // Ein weiterer Poll auf demselben Lauf vergibt keine neue Nummer.
    act(() => useVisRuntime.getState().patchLauf(nodeId, { worker: 'fake-worker' }));
    expect(useVisRuntime.getState().laeufe[nodeId]!.laufNummer).toBe(2);
    laeufe({ status: 'fehler', fehler: 'x', memoKey: schluessel }, { status: 'abgebrochen', memoKey: schluessel }, fertig(3));
    expect(useVisRuntime.getState().laeufe[nodeId]!.laufNummer).toBe(3);
    // Derselbe Auftrag noch einmal gesetzt behaelt seine Nummer.
    laeufe(fertig(3));
    expect(useVisRuntime.getState().laeufe[nodeId]!.laufNummer).toBe(3);
    expect(useVisRuntime.getState().verlauf[nodeId]!.map((l) => l.laufNummer)).toEqual([2, 1]);
  });

  it('Innenansicht: das Verdikt bleibt (wie an der Kachel), die Treue sagt «nicht anwendbar»; der Satz bleibt wörtlich', () => {
    const innen: JobQa = {
      verdict: { passed: true, reason: 'Geometrie 0.979 — für Innenansichten nicht aussagekräftig.' },
      geometry: { status: 'not_applicable', geometry_fidelity: 0.979, threshold: 0.65, passed: true, method: 'm' },
    };
    montiere();
    laeufe(fertig(1, { qa: innen }), fertig(2, { qa: innen }));
    klick(daumen()[0]!);
    expect(daumen()[0]!.dataset['urteil']).toBe('bestanden');
    expect(q('[data-testid="render-verlauf-gross-urteil"]')!.textContent).toBe('bestanden');
    expect(q('[data-testid="render-verlauf-gross-treue"]')!.textContent).toBe('nicht anwendbar — Ansicht nicht zuständig');
    expect(q('[data-testid="render-verlauf-gross-grund"]')!.textContent).toBe('Geometrie 0.979 — für Innenansichten nicht aussagekräftig.');
    expect(q('[data-testid="render-verlauf-gross-treue"]')!.textContent).not.toContain('nicht gemessen');
  });

  it('die grosse Ansicht ist undurchsichtig — kein Glas, das ohne Weichzeichner durchscheint', () => {
    const css = readFileSync(
      path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../src/modules/vis/vis-visual.css'),
      'utf8',
    );
    const block = /\n\.k-dialog-box\.vis-verlauf-gross \{([^}]*)\}/.exec(css)?.[1] ?? '';
    expect(block).toContain('background: var(--k-surface);');
    expect(block).toContain('backdrop-filter: none;');
    expect(block).toContain('-webkit-backdrop-filter: none;');
    montiere();
    laeufe(fertig(1), fertig(2));
    klick(daumen()[0]!);
    expect(gross()!.classList.contains('k-dialog-box')).toBe(true);
    expect(gross()!.classList.contains('vis-verlauf-gross')).toBe(true);
  });
});

describe('Verlauf am Render-Knoten — Urteil, Grund, Treue und Zeit als Rechnung', () => {
  it('laufUrteil: vier Zustände, allein aus dem Verdikt', () => {
    expect(laufUrteil(QA_OK)).toBe('bestanden');
    expect(laufUrteil(QA_FEHL)).toBe('durchgefallen');
    expect(laufUrteil(undefined)).toBe('ohne-qa');
    expect(laufUrteil(QA_NICHT_ZUSTAENDIG)).toBe('bestanden');
    const nurAlt: JobQa = {
      verdict: { passed: true },
      geometry: { geom_iou: 0.97, threshold: 0.65, passed: true, method: 'depthanything-v2-redepth' },
    };
    expect(laufUrteil(nurAlt), 'widerrufen betrifft nur Zahlen und Sterne').toBe('bestanden');
  });

  it('laufGrund: der Satz des Absenders zuerst, sonst der Satz des Inspektors, nichts erfunden', () => {
    expect(laufGrund(QA_FEHL)).toBe('Das Bild zeigt einen zusätzlichen Anbau rechts, den die Geometrie nicht hat.');
    expect(laufGrund(undefined)).toBe('Keine QA-Bewertung vorhanden.');
    expect(laufGrund(QA_NICHT_ZUSTAENDIG)).toContain('Hier war nichts zu messen');
    expect(laufGrund({ verdict: { passed: true, hinweise: ['', 'Himmel leicht überstrahlt'] } })).toBe('Himmel leicht überstrahlt');
    expect(laufGrund(QA_OK)).toBe('Ohne Begründung geliefert.');
  });

  it('treueText: rho_maske gegen die geeichte Schwelle; ohne Zahl drei verschiedene Sätze', () => {
    expect(treueText(QA_FEHL)).toBe('0,41 / 0,80');
    expect(treueText(undefined), 'nur wenn wirklich keine QA kam').toBe('nicht gemessen');
    expect(treueText(QA_NICHT_ZUSTAENDIG)).toBe('nicht anwendbar — Ansicht nicht zuständig');
    expect(
      treueText({ verdict: { passed: false }, geometry: { rho_maske: null, threshold: 0.65, passed: false, method: 'm' } }),
    ).toBe('keine Gebäude-Zahl geliefert');
    expect(treueText(QA_OK)).toBe('keine Gebäude-Zahl geliefert');
  });

  it('Zeit in Ortszeit, 24 Stunden, ohne «UTC»', () => {
    const t = Date.UTC(2026, 9, 7, 16, 58);
    expect(uhrzeitText(t)).toBe('18:58');
    expect(zeitpunktText(t)).toBe('07.10.2026 · 18:58');
    // Winterzeit und Datumswechsel: 23:30 UTC ist in Zuerich schon der naechste Tag.
    const winter = Date.UTC(2026, 0, 5, 23, 30);
    expect(uhrzeitText(winter)).toBe('00:30');
    expect(zeitpunktText(winter)).toBe('06.01.2026 · 00:30');
    expect(uhrzeitText(undefined)).toBe('—');
  });
});
