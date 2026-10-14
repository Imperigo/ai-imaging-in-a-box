// @vitest-environment jsdom
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';
import { glasOhneWeichzeichner, ladeAnzeige } from '../src/anzeige';

/**
 * Welle E3 · C14 (Home-PC-Worker, Abnahme 06.10.2026): am Heimrechner (die
 * Desktop-App läuft in WebKitGTK) sind Einstellungsfenster und Listen
 * halbdurchsichtig, aber OHNE Unschärfe — der Inhalt dahinter ist scharf
 * lesbar. Das Glas (`--k-glass-fill`, 62 % deckend) ist auf den Weichzeichner
 * angewiesen; fehlt er, wird es deckend.
 *
 * Drei Wege erkennen «kein Weichzeichner»:
 *  1. die Engine kennt `backdrop-filter` gar nicht (`@supports not`);
 *  2. WebKit ohne beschleunigtes Zeichnen (`-webkit-transform-3d` falsch) —
 *     dort wird `backdrop-filter` gelesen, aber nicht gezeichnet;
 *  3. WebKitGTK (die Desktop-App unter Linux) — `data-glas="deckend"` an
 *     <html>, gesetzt beim Start (`ladeAnzeige`). Die CSS-Wege allein greifen
 *     dort nicht sicher: WebKitGTK liest `backdrop-filter`, zeichnet ihn aber
 *     je nach Version und Grafiktreiber nicht.
 */

const aura = readFileSync(resolve(__dirname, '../src/aura.css'), 'utf8');

const WEBKITGTK = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/605.1.15 (KHTML, like Gecko)';
const CHROMIUM_LINUX = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36';
const SAFARI_MAC = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Safari/605.1.15';
const IPAD = 'Mozilla/5.0 (iPad; CPU OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148';
const ANDROID = 'Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0 Mobile Safari/537.36';
const FIREFOX = 'Mozilla/5.0 (X11; Linux x86_64; rv:131.0) Gecko/20100101 Firefox/131.0';

/** Alle Blöcke, deren Kopf `kopf` enthält, je bis zur passenden schliessenden Klammer. */
function block(kopf: string): string {
  let aus = '';
  for (let i = aura.indexOf(kopf); i >= 0; i = aura.indexOf(kopf, i + 1)) {
    let tiefe = 0;
    for (let j = aura.indexOf('{', i); j < aura.length; j++) {
      if (aura[j] === '{') tiefe++;
      else if (aura[j] === '}' && --tiefe === 0) {
        aus += aura.slice(aura.lastIndexOf('\n', i) + 1, j + 1);
        break;
      }
    }
  }
  return aus;
}

describe('C14 · welche Engine zeichnet kein Glas', () => {
  it('WebKitGTK (Desktop-App unter Linux): ja', () => {
    expect(glasOhneWeichzeichner(WEBKITGTK)).toBe(true);
  });
  it('Chromium, Safari am Mac, iPad, Android, Firefox: nein — dort bleibt das Glas', () => {
    for (const ua of [CHROMIUM_LINUX, SAFARI_MAC, IPAD, ANDROID, FIREFOX]) expect(glasOhneWeichzeichner(ua), ua).toBe(false);
  });
  it('ladeAnzeige setzt data-glas an <html> nur dort', () => {
    const ua = Object.getOwnPropertyDescriptor(window.navigator, 'userAgent');
    try {
      Object.defineProperty(window.navigator, 'userAgent', { value: WEBKITGTK, configurable: true });
      ladeAnzeige();
      expect(document.documentElement.dataset.glas).toBe('deckend');
      Object.defineProperty(window.navigator, 'userAgent', { value: CHROMIUM_LINUX, configurable: true });
      ladeAnzeige();
      expect(document.documentElement.dataset.glas).toBeUndefined();
    } finally {
      if (ua) Object.defineProperty(window.navigator, 'userAgent', ua);
      else delete (window.navigator as unknown as Record<string, unknown>).userAgent;
    }
  });
});

describe('C14 · ohne Weichzeichner wird das Glas deckend (aura.css)', () => {
  const faelle = [
    ['data-glas', block("[data-glas='deckend'] {")],
    ['@supports not', block('@supports not ((backdrop-filter: blur(1px)) or (-webkit-backdrop-filter: blur(1px))) {\n  :root')],
    ['-webkit-transform-3d', block('@media not all and (-webkit-transform-3d)')],
  ] as const;
  for (const [name, b] of faelle) {
    it(`${name}: Glas der Fenster/Listen (--k-glass-fill) und Insel-Papierglas deckend`, () => {
      expect(b, `Block «${name}» fehlt`).not.toBe('');
      // `--k-glass-fill` nur im dunklen Thema (Papier kennt kein Glas).
      expect(b).toMatch(/\[data-theme='orbit'\][^{]*\{\s*--k-glass-fill:\s*var\(--k-glas-deckend\)/);
      expect(b).toMatch(/--k-insel-glas-papier:\s*var\(--k-glas-deckend\)/);
    });
  }
  it('--k-glas-deckend: aus der Fläche gemischt (keine neue Farbe), mindestens 94 % deckend', () => {
    const m = /--k-glas-deckend:\s*color-mix\(in srgb, var\(--k-surface\) (\d+)%, transparent\)/.exec(aura);
    expect(m, '--k-glas-deckend fehlt').not.toBeNull();
    expect(Number(m![1])).toBeGreaterThanOrEqual(94);
  });
});
