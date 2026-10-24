// @vitest-environment jsdom
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { act } from 'react';
import { createRoot } from 'react-dom/client';
import { beforeEach, describe, expect, it } from 'vitest';
import { bewegungJetzt, ladeAnzeige, setzeBewegung, setzeSchrift, useBewegung } from '../src/anzeige';

/**
 * U14, Owner B6/B18 (01.10.2026): Schrift einstellbar (klein · normal ·
 * gross) und Bewegung «wie das Gerät» plus eigener Schalter (voll · ruhig ·
 * aus). Die Wahl wirkt sofort auf die ganze App über zwei Attribute an
 * <html>, und sie bleibt nach einem Neustart.
 *
 * Rot vor gruen: vorher gibt es `anzeige` nicht.
 */

(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;
let geraetReduziert = false;
beforeEach(() => {
  localStorage.clear();
  geraetReduziert = false;
  window.matchMedia = ((q: string) => ({ matches: geraetReduziert, media: q, addEventListener() {}, removeEventListener() {} })) as unknown as typeof window.matchMedia;
  setzeSchrift('normal');
  setzeBewegung('geraet');
});

const aura = readFileSync(resolve(__dirname, '../src/aura.css'), 'utf8');

describe('Schrift einstellbar (B6)', () => {
  it('setzt das Attribut an <html> und merkt sich die Wahl', () => {
    setzeSchrift('gross');
    expect(document.documentElement.dataset.schrift).toBe('gross');
    expect(JSON.parse(localStorage.getItem('kosmo.anzeige')!).schrift).toBe('gross');
    document.documentElement.removeAttribute('data-schrift');
    ladeAnzeige();
    expect(document.documentElement.dataset.schrift).toBe('gross');
  });

  it('aura.css skaliert jede Schriftstufe für klein und gross', () => {
    for (const stufe of ['klein', 'gross']) {
      const block = aura.match(new RegExp(`:root\\[data-schrift='${stufe}'\\](?:,\\s*:root\\[data-praesentation='an'\\])?\\s*\\{([^}]*)\\}`))?.[1] ?? '';
      for (const t of ['xxs', 'xs', 'sm', 'md', 'lg', 'plakat', 'h3', 'h2', 'anzeige', 'h1', 'display', 'code', 'micro']) {
        expect(block, `${stufe}: --k-t-${t}`).toMatch(new RegExp(`--k-t-${t}:\\s*[\\d.]+px`));
      }
    }
  });
});

describe('Bewegung: wie das Gerät, voll, ruhig, aus (B18)', () => {
  it('«wie das Gerät» folgt der Systemeinstellung', () => {
    expect(bewegungJetzt()).toBe('voll');
    geraetReduziert = true;
    expect(bewegungJetzt()).toBe('aus');
  });

  it('der eigene Schalter gewinnt über das Gerät', () => {
    geraetReduziert = true;
    setzeBewegung('voll');
    expect(bewegungJetzt()).toBe('voll');
    setzeBewegung('ruhig');
    expect(bewegungJetzt()).toBe('ruhig');
    expect(document.documentElement.dataset.bewegung).toBe('ruhig');
  });

  it('useBewegung meldet einen Wechsel sofort', () => {
    const halter = document.createElement('div');
    const root = createRoot(halter);
    let gesehen = '';
    function Sonde() {
      gesehen = useBewegung();
      return null;
    }
    act(() => root.render(<Sonde />));
    expect(gesehen).toBe('voll');
    act(() => setzeBewegung('aus'));
    expect(gesehen).toBe('aus');
    act(() => root.unmount());
  });

  it('aura.css: «aus» wirkt wie der Riegel des Geräts, «ruhig» hält Schleifen an', () => {
    const aus = aura.match(/:root\[data-bewegung='aus'\][^{]*\{([^}]*)\}/)?.[1] ?? '';
    expect(aus).toMatch(/animation-duration:\s*0\.01ms\s*!important/);
    expect(aus).toMatch(/transition-duration:\s*0s\s*!important/);
    // Eine Endlosschleife liefe mit 0,01 ms weiter und flackerte (Fund Helfer F).
    expect(aus).toMatch(/animation-iteration-count:\s*1\s*!important/);
    const ruhig = aura.match(/:root\[data-bewegung='ruhig'\][^{]*\{([^}]*)\}/)?.[1] ?? '';
    expect(ruhig).toMatch(/animation-iteration-count:\s*1\s*!important/);
  });
});
