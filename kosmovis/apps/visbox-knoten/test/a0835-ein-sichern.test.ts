// @vitest-environment jsdom
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { History, KosmoDoc, type VisGraph } from '@kosmo/kernel';
import { useProject } from '../../kosmo-orbit/src/state/project-store';
import type { AutosaveLage } from '../../kosmo-orbit/src/state/project-vault';
import { graphDerNeuenMappe, graphStand, legeGraphen, renderGraphen, sichereBeiAenderung, setzeGraphMappe } from '../src/graph-sichern';

/**
 * A0835 «Ein Sichern zur Zeit» (Audit 24.11.2026, Befund V3): Antwortete der Heim-PC langsam, startete
 * jede weitere Änderung einen eigenen Sicher-Aufruf gegen denselben Stand — der zweite lief in den
 * 409 des ersten, obwohl kein anderes Gerät dazwischen gesichert hatte. Jetzt hat die Seite je Mappe
 * höchstens einen offenen Aufruf; den neuesten Stand dazwischen schickt sie nach der Bestätigung mit
 * dem neuen Stand nach. Eine späte Antwort einer früheren Mappe ändert an der jetzigen nichts.
 */
const GRAPH: VisGraph = { id: 'visgraph_probe', kind: 'visgraph', name: 'eins', nodes: [], edges: [] } as VisGraph;
const VERZUG_MS = 3000;

function aendere(name: string): void {
  const { doc } = useProject.getState();
  const alt = doc.get(GRAPH.id) as VisGraph;
  doc.apply([{ id: GRAPH.id, before: alt, after: { ...alt, name } }]);
  useProject.setState((s) => ({ revision: s.revision + 1 }));
}

type Aufruf = { url: string; rumpf: string };

/** Ein Heim-PC, der jede Sicherung erst nach `VERZUG_MS` bestätigt, mit einem neuen Stand je Mappe. */
function langsamerHeimPc(antwort: (url: string, n: number) => Response | null) {
  const aufrufe: Aufruf[] = [];
  let offen = 0;
  let hoechstens = 0;
  vi.stubGlobal('fetch', (url: string, init?: RequestInit) => {
    aufrufe.push({ url: String(url), rumpf: String(init?.body ?? '') });
    offen += 1;
    hoechstens = Math.max(hoechstens, offen);
    const n = aufrufe.length;
    return new Promise<Response>((fertig) => {
      setTimeout(() => {
        const r = antwort(String(url), n);
        if (r === null) return; // antwortet nie
        offen -= 1;
        fertig(r);
      }, VERZUG_MS);
    });
  });
  return { aufrufe, hoechstens: () => hoechstens };
}

function json(wert: unknown, status = 200): Response {
  return new Response(JSON.stringify(wert), { status, headers: { 'Content-Type': 'application/json' } });
}

beforeEach(() => {
  vi.useFakeTimers();
  useProject.setState({ doc: new KosmoDoc(), history: new History(), revision: 0 } as never);
});
afterEach(() => {
  vi.unstubAllGlobals();
  vi.useRealTimers();
  setzeGraphMappe(null);
});

describe('A0835: ein Sichern zur Zeit', () => {
  it('Antwort 3 s verzögert, dreimal geändert: nie mehr als ein offener Aufruf, danach genau einer mit neuem Stand und jüngster Fassung', async () => {
    setzeGraphMappe('alpha', 'abc');
    const heimPc = langsamerHeimPc((_url, n) => json({ gesichert: true, stand: n === 1 ? 'def' : 'ghi' }));
    const lagen: AutosaveLage[] = [];
    const ab = sichereBeiAenderung(undefined, 1000, (l) => lagen.push(l));
    try {
      legeGraphen([GRAPH]); // Änderung 1
      await vi.advanceTimersByTimeAsync(1000);
      expect(heimPc.aufrufe).toHaveLength(1);
      aendere('zwei'); // Änderung 2, während der erste Aufruf offen ist
      await vi.advanceTimersByTimeAsync(1000);
      aendere('drei'); // Änderung 3, noch immer offen
      await vi.advanceTimersByTimeAsync(1000);
      expect(heimPc.aufrufe, 'solange der erste offen ist, startet kein zweiter').toHaveLength(1);
      // Die Bestätigung des ersten kommt (3 s nach seinem Start).
      await vi.advanceTimersByTimeAsync(VERZUG_MS);
      expect(heimPc.aufrufe, 'nach der Bestätigung genau ein weiterer').toHaveLength(2);
      expect(heimPc.aufrufe[0]!.url).toContain('stand=abc');
      expect(heimPc.aufrufe[1]!.url, 'der weitere mit dem neuen Stand').toContain('stand=def');
      expect(heimPc.aufrufe[1]!.url).not.toContain('stand=abc');
      expect(JSON.parse(heimPc.aufrufe[1]!.rumpf).graphen[0].name, 'mit der jüngsten Fassung').toBe('drei');
      await vi.advanceTimersByTimeAsync(VERZUG_MS + 1000);
      expect(heimPc.aufrufe, 'danach nichts mehr').toHaveLength(2);
      expect(heimPc.hoechstens(), 'offene Aufrufe je Mappe').toBeLessThanOrEqual(1);
      expect(graphStand()).toBe('ghi');
      expect(lagen.at(-1)?.stand).toBe('gesichert');
      expect(lagen.some((l) => l.stand === 'fehler')).toBe(false);
    } finally {
      ab();
    }
  });

  it('eine einzelne Änderung sichert nach 1 s wie bisher, ein unverändertes Dokument gar nicht', async () => {
    setzeGraphMappe('alpha', 'abc');
    const heimPc = langsamerHeimPc(() => json({ gesichert: true, stand: 'def' }));
    const ab = sichereBeiAenderung(undefined, 1000);
    try {
      legeGraphen([GRAPH]);
      await vi.advanceTimersByTimeAsync(999);
      expect(heimPc.aufrufe).toHaveLength(0);
      await vi.advanceTimersByTimeAsync(1);
      expect(heimPc.aufrufe).toHaveLength(1);
      await vi.advanceTimersByTimeAsync(VERZUG_MS);
      useProject.setState((s) => ({ revision: s.revision + 1 })); // Revision ohne Inhalt
      await vi.advanceTimersByTimeAsync(VERZUG_MS + 1000);
      expect(heimPc.aufrufe).toHaveLength(1);
    } finally {
      ab();
    }
  });

  it('eine verspätete Antwort aus Mappe A nach dem Wechsel zu B ändert weder Speicherkreis noch Stand von B', async () => {
    setzeGraphMappe('A', 'a1');
    // A bestätigt spät mit einem neuen Stand; B antwortet in dieser Probe nie.
    const heimPc = langsamerHeimPc((url) => (url.includes('mappe=A') ? json({ gesichert: true, stand: 'a2' }) : null));
    const lagen: AutosaveLage[] = [];
    const ab = sichereBeiAenderung(undefined, 1000, (l) => lagen.push(l));
    try {
      legeGraphen([GRAPH]);
      await vi.advanceTimersByTimeAsync(1000);
      expect(heimPc.aufrufe).toHaveLength(1);
      expect(heimPc.aufrufe[0]!.url).toContain('mappe=A');
      // «Datei laden …»: Mappe B mit ihrem Graph und Stand.
      const holen = vi.fn(async () => json({ graphen: [{ ...GRAPH, id: 'visgraph_b', name: 'B' }], mappe: 'B', stand: 'b1' }));
      await graphDerNeuenMappe(holen as unknown as typeof fetch);
      expect(graphStand()).toBe('b1');
      const vorher = lagen.length;
      // Die Antwort aus A kommt an.
      await vi.advanceTimersByTimeAsync(VERZUG_MS);
      expect(graphStand(), 'der Stand von B bleibt').toBe('b1');
      expect(lagen.slice(vorher).filter((l) => l.stand !== 'sichert'), 'kein «gesichert» und kein Fehler aus A').toEqual([]);
      expect(lagen.some((l) => l.stand === 'gesichert')).toBe(false);
      // Der Graph von B wird in B gesichert, nicht in A.
      const nachB = heimPc.aufrufe.slice(1);
      expect(nachB.every((a) => a.url.includes('mappe=B') && a.url.includes('stand=b1'))).toBe(true);
    } finally {
      ab();
    }
  });

  it('eine echte 409 lässt den eigenen Entwurf im Dokument und meldet «fehler»', async () => {
    setzeGraphMappe('alpha', 'abc');
    const satz = 'Ein anderes Gerät hat inzwischen gesichert. Bitte neu laden.';
    langsamerHeimPc(() => json({ fehler: satz }, 409));
    const lagen: AutosaveLage[] = [];
    const ab = sichereBeiAenderung(undefined, 1000, (l) => lagen.push(l));
    try {
      legeGraphen([GRAPH]);
      aendere('entwurf');
      await vi.advanceTimersByTimeAsync(1000 + VERZUG_MS);
      const letzte = lagen.at(-1)!;
      expect(letzte.stand).toBe('fehler');
      expect((letzte as { grund?: string }).grund).toBe(satz);
      expect(renderGraphen().map((g) => g.name), 'der eigene Entwurf bleibt').toEqual(['entwurf']);
      expect(graphStand(), 'der Stand bleibt der gelesene').toBe('abc');
    } finally {
      ab();
    }
  });
});
