// @vitest-environment jsdom
import { readFileSync, readdirSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { ErzaehlZeile, NaviInsel, erzaehlungAus, registriereKosmoName, type ErzaehlQuelle } from '../src';

(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

/**
 * Schnitt 1 von `@kosmo/insel`: die Bausteine laufen ohne KosmoOrbit. Der Wirt
 * (KosmoOrbit oder Visbox) gibt, was sie brauchen, über Props und `ErzaehlQuelle`.
 */

const SRC = resolve(dirname(fileURLToPath(import.meta.url)), '../src');

describe('ohne App-Stores', () => {
  it('kein Import verlässt das Paket ausser react und @kosmo/ui', () => {
    const fremd: string[] = [];
    for (const datei of readdirSync(SRC)) {
      if (!/\.(ts|tsx)$/.test(datei)) continue;
      const text = readFileSync(join(SRC, datei), 'utf8');
      for (const m of text.matchAll(/from\s+'([^']+)'/g)) {
        const ziel = m[1]!;
        if (ziel.startsWith('./') || ziel === 'react' || ziel === 'react-dom' || ziel === '@kosmo/ui') continue;
        fremd.push(`${datei}: ${ziel}`);
      }
    }
    expect(fremd).toEqual([]);
  });
});

let root: Root | null = null;
let host: HTMLDivElement | null = null;
const zeige = (el: React.ReactElement) => {
  host = document.createElement('div');
  document.body.appendChild(host);
  root = createRoot(host);
  act(() => root!.render(el));
  return host;
};
afterEach(() => {
  if (root) act(() => root!.unmount());
  root = null;
  host?.remove();
  host = null;
});

const leer: ErzaehlQuelle = {
  verbunden: true,
  offeneKarten: [],
  letzterSchritt: null,
  zuletztAktiv: null,
  taetigkeit: null,
};

describe('Erzählzeile aus einer fremden Quelle', () => {
  it('ohne Erzählung zeichnet sie nichts', () => {
    const h = zeige(<ErzaehlZeile quelle={leer} />);
    expect(h.querySelector('[data-testid="erzaehl-zeile"]')).toBeNull();
  });
  it('eine laufende Tätigkeit nennt ihr Werkzeug', () => {
    const quelle = { ...leer, taetigkeit: { id: 'a-1', werkzeug: 'vis_knotenVerbinden', beginn: Date.now() } };
    const h = zeige(<ErzaehlZeile quelle={quelle} />);
    expect(h.querySelector('[data-testid="erzaehl-zeile"]')!.textContent).toContain('Claude · knoten verbinden …');
  });
  it('eine offene Karte: kein Anwenden/Ablehnen in der Zeile, ein Klick ruft zeigeKarten des Wirts', () => {
    const zeigeKarten = vi.fn();
    const quelle = { ...leer, offeneKarten: [{ kennung: 'k-7', zusammenfassung: 'Knoten anlegen' }], zeigeKarten };
    const h = zeige(<ErzaehlZeile quelle={quelle} />);
    expect(h.querySelector('[data-testid="erzaehl-zeile-anwenden"]')).toBeNull();
    expect(h.querySelector('[data-testid="erzaehl-zeile-ablehnen"]')).toBeNull();
    expect(h.querySelector('[data-testid="erzaehl-zeile-hinweis"]')!.textContent).toBe('unten links entscheiden');
    act(() => (h.querySelector('[data-testid="erzaehl-zeile-karten"]') as HTMLButtonElement).click());
    expect(zeigeKarten).toHaveBeenCalledTimes(1);
  });
  it('ohne zeigeKarten ist die Zeile nur Text', () => {
    const quelle = { ...leer, offeneKarten: [{ kennung: 'k-7', zusammenfassung: 'Knoten anlegen' }] };
    const h = zeige(<ErzaehlZeile quelle={quelle} />);
    expect(h.querySelector('[data-testid="erzaehl-zeile-text"]')!.textContent).toBe('Claude wartet auf dich');
    expect(h.querySelector('button')).toBeNull();
  });
});

describe('Navi-Insel', () => {
  it('zeigt den Zoom und ruft die Handgriffe des Wirts', () => {
    const onGroesser = vi.fn();
    const h = zeige(
      <NaviInsel
        ansicht="2d"
        prozent={100}
        onKleiner={() => {}}
        onGroesser={onGroesser}
        onEinpassen={() => {}}
        onVollbild={() => {}}
        vollbildAktiv={false}
      />,
    );
    expect(h.textContent).toContain('100');
    const knoepfe = Array.from(h.querySelectorAll('button'));
    expect(knoepfe.length).toBeGreaterThanOrEqual(3);
    act(() => knoepfe[1]!.click());
    expect(onGroesser).toHaveBeenCalledTimes(1);
  });
});

describe('Name des Assistenten (Nahtstelle des Wirts)', () => {
  it('ohne Anmeldung «Kosmo», mit Anmeldung der Name des Wirts, null stellt zurück', () => {
    const e = () =>
      erzaehlungAus({
        jetzt: 1_000,
        offeneKarten: [],
        letzterSchritt: { urheber: 'kosmo', zusammenfassung: 'Knoten 2', zeit: 900, zurueckgenommen: false },
        zuletztAktiv: null,
      })?.text;
    expect(e()).toBe('Kosmo · Knoten 2');
    registriereKosmoName('Assistent');
    expect(e()).toBe('Assistent · Knoten 2');
    registriereKosmoName(null);
    expect(e()).toBe('Kosmo · Knoten 2');
  });
});
