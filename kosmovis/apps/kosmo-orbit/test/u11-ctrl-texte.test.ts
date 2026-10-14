import { afterEach, describe, expect, it, vi } from 'vitest';

/**
 * U11 (Owner B6): Wer auf dem Mac arbeitet, liest «⌘», nicht «Ctrl». Helfer F
 * fand zwei feste Texte, die der Nutzer sieht: den Titel des Einfügen-Knopfs in
 * KosmoDesign und den Hinweis «Kein Render ohne Geometrie» in KosmoVis.
 * Rot vor gruen: beide nannten «Ctrl» fest.
 */
afterEach(() => {
  vi.unstubAllGlobals();
  vi.resetModules();
});

describe('U11 · sichtbare Tastentexte folgen dem Gerät', () => {
  it('KosmoVis: der Geometrie-Hinweis nennt auf dem Mac ⌘K', async () => {
    vi.stubGlobal('navigator', { platform: 'MacIntel', userAgent: 'Macintosh', maxTouchPoints: 0 });
    vi.resetModules();
    const { KEINE_GEOMETRIE_HINWEIS } = await import('../src/modules/vis/vis-jobs');
    expect(KEINE_GEOMETRIE_HINWEIS).toContain('⌘K');
    expect(KEINE_GEOMETRIE_HINWEIS).not.toMatch(/Ctrl/);
  });

  it('KosmoVis: sonst heisst es Strg+K', async () => {
    vi.stubGlobal('navigator', { platform: 'Win32', userAgent: 'Windows', maxTouchPoints: 0 });
    vi.resetModules();
    const { KEINE_GEOMETRIE_HINWEIS } = await import('../src/modules/vis/vis-jobs');
    expect(KEINE_GEOMETRIE_HINWEIS).toContain('Strg+K');
  });

  // U25 Phase 6: der Einfügen-Knopf der alten Werkzeugleiste (KosmoDesign) ist mit ihr entfallen; Einfügen geht
  // über die Tastatur (Kurzbefehl) und Kosmo.
});
