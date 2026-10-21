import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';
import { RenderResult } from '../src';

/**
 * Video-Befund L4-1 (Knoten-Vertrag v0.1.10, Int 1 angenommen 21.10.2026): `qa_je_kamera[].deckung` — Kanten-IoU 0..1
 * des KI-Bilds gegen das Grundbild der Kamera. Optional, kein Tor; ein kaputter Wert faellt still weg.
 */
const echt = JSON.parse(
  readFileSync(fileURLToPath(new URL('./fixtures/kv-deckung.json', import.meta.url)), 'utf8'),
) as { result: Record<string, unknown> };

describe('L4-1 · Deckung je Kamera', () => {
  it('Ergebnis aus dem Heim-PC-Kern: zwei gemessene Kameras, eine ohne Feld', () => {
    const r = RenderResult.parse(echt.result);
    expect(r.qa_je_kamera?.map((k) => [k.kamera, k.deckung])).toEqual([
      ['s', 0.42],
      ['nNW', 0.18],
      ['oSO', undefined],
    ]);
  });

  it('ein Wert ausserhalb 0..1 oder kein Wert lehnt das Ergebnis nicht ab', () => {
    const je = (echt.result['qa_je_kamera'] as Record<string, unknown>[]).map((k, i) =>
      i === 0 ? { ...k, deckung: 1.7 } : i === 1 ? { ...k, deckung: 'hoch' } : k,
    );
    const r = RenderResult.parse({ ...echt.result, qa_je_kamera: je });
    expect(r.qa_je_kamera?.map((k) => k.deckung)).toEqual([undefined, undefined, undefined]);
  });
});
