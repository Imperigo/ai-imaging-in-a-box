// @vitest-environment jsdom
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { History, KosmoDoc } from '@kosmo/kernel';
import { useProject } from '../../kosmo-orbit/src/state/project-store';
import { ladeGesichertenGraph, leseWeg, setzeGraphMappe, sicherWeg } from '../src/graph-sichern';
import { ladeMappe } from '../src/mappe';

/**
 * A0830 «Knoten bleiben in ihrer Mappe» (externes Audit 24.11.2026, Befund V1): Die Visbox-Seite öffnet die
 * Knotenansicht mit `?ordner=<A>`. `ladeMappe` und `modell.glb` lasen A, der Graph aber kam aus `./graph`
 * ohne Angabe, also aus der Mappe, die ein anderes Fenster oder Gerät zuletzt geöffnet hatte (B), und das
 * nächste Sichern ging mit der Kennung von B dorthin. Abgeleitet aus der Audit-Probe `audit-local.test.ts`,
 * umgestellt auf den richtigen Vertrag: dieselbe Mappenangabe für Mappe, Modell und Graph.
 */
const A = '/synthetisch/Alpha';

function ordnerIn(weg: string): string | null {
  const frage = weg.includes('?') ? weg.slice(weg.indexOf('?') + 1) : '';
  return new URLSearchParams(frage).get('ordner');
}

function mappeIn(weg: string): string | null {
  const frage = weg.includes('?') ? weg.slice(weg.indexOf('?') + 1) : '';
  return new URLSearchParams(frage).get('mappe');
}

beforeEach(() => {
  useProject.setState({ doc: new KosmoDoc(), history: new History(), revision: 0 } as never);
  setzeGraphMappe(null);
});
afterEach(() => {
  vi.unstubAllGlobals();
  history.replaceState(null, '', '/');
});

describe('A0830: der Graph kommt aus der Mappe der Adresse', () => {
  it('mit ?ordner=<A> fragen Mappe, Modell und Graph dieselbe Mappe, und gesichert wird mit der Kennung von A', async () => {
    history.replaceState(null, '', `/knoten/?ordner=${encodeURIComponent(A)}`);
    const wege: string[] = [];
    vi.stubGlobal('fetch', async (eingabe: string) => {
      wege.push(String(eingabe));
      if (String(eingabe).startsWith('./mappe')) {
        return new Response(
          JSON.stringify({ name: 'Alpha', mappe: 'Alpha', glb: true, huellbox_m: null, hochachse: null, grund: '', huellbox_vermerk: '' }),
          { status: 200 },
        );
      }
      if (String(eingabe).startsWith('./modell.glb')) return new Response(new ArrayBuffer(8), { status: 200 });
      return new Response('{}', { status: 200 });
    });
    await ladeMappe();
    const holen = vi.fn(async (_weg: string) => new Response(JSON.stringify({ mappe: 'Alpha', stand: 's1', graphen: [] }), { status: 200 }));
    await ladeGesichertenGraph(holen as unknown as typeof fetch);

    const mappeWeg = wege.find((w) => w.startsWith('./mappe'))!;
    const modellWeg = wege.find((w) => w.startsWith('./modell.glb'))!;
    const graphWeg = holen.mock.calls[0]![0];
    expect(ordnerIn(mappeWeg)).toBe(A);
    expect(ordnerIn(modellWeg)).toBe(A);
    expect(graphWeg, 'nie ./graph ohne Angabe').not.toBe('./graph');
    expect(ordnerIn(graphWeg), 'der Graph mit derselben Mappenangabe wie Mappe und Modell').toBe(A);
    expect(sicherWeg()).toBe('./graph?mappe=Alpha&stand=s1');
  });

  it('ohne lesbare Antwort sichert die Seite trotzdem nur in A (die Kennung ist der Ordnername), nie in die zuletzt geöffnete', async () => {
    await ladeGesichertenGraph(async () => new Response(null, { status: 503 }), `?ordner=${encodeURIComponent(A)}`);
    expect(sicherWeg()).toBe('./graph?mappe=Alpha');
  });

  it('bleibt: mit ?mappe=<Kennung> (Entscheid 129) und ganz ohne Angabe (Entscheid 85 B) wie bisher', () => {
    expect(leseWeg('?mappe=Alpha')).toBe('./graph?mappe=Alpha');
    expect(leseWeg('')).toBe('./graph');
    // Nennt die Adresse beides, gilt die Kennung, wie am Heim-PC (`_knoten_ordner`).
    const beides = leseWeg(`?ordner=${encodeURIComponent(A)}&mappe=Alpha`);
    expect(mappeIn(beides)).toBe('Alpha');
    expect(ordnerIn(beides)).toBeNull();
  });
});
