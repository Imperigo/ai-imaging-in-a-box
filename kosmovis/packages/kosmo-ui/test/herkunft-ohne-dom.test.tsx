// @vitest-environment node
import { renderToString } from 'react-dom/server';
import { useRef } from 'react';
import { describe, expect, it } from 'vitest';
import { useHerkunft } from '../src/herkunft';

/**
 * Fund Helfer F (01.10.2026): `useHerkunft` las beim ersten Rendern
 * `HTMLElement`. Ohne DOM (Node, Server-Rendern) warf das einen
 * ReferenceError — darum musste `app-deinstallieren.test.tsx` auf jsdom.
 * Rot vor gruen: ohne die Abfrage auf `typeof HTMLElement` wirft dieser Fall.
 */
function Box() {
  const ref = useRef<HTMLDivElement>(null);
  useHerkunft(ref);
  return <div ref={ref}>x</div>;
}

describe('useHerkunft ohne DOM', () => {
  it('rendert in Node, ohne zu werfen', () => {
    const g = globalThis as unknown as { document?: unknown };
    const vorher = g.document;
    g.document = { activeElement: null, body: null };
    try {
      expect(renderToString(<Box />)).toContain('x');
    } finally {
      g.document = vorher;
    }
  });
});
