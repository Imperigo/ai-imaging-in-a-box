import { readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';

/**
 * **P-FOKUS-OHNE-GLUEHEN — drei Bausteine hatten im hellen Thema kein
 * sichtbares Fokuszeichen.**
 *
 * ## Wie der Befund entstand
 *
 * Auf der Tafel «Offener Stand» stand: «Fuenfzehn verschiedene Arten, einen
 * Fokus zu zeigen — gezaehlt, aber nicht beurteilt.» Das Urteil ist jetzt
 * gefaellt, und es faellt in zwei Teile.
 *
 * **Der grosse Teil ist Entwarnung.** Von 32 `:focus-visible`-Regeln sind die
 * allermeisten `:hover, :focus-visible`-Paare: sie geben der Tastatur
 * dieselbe Behandlung wie der Maus. Das ist richtig und kein Wildwuchs. Der
 * eigentliche Fokusring kommt aus EINER globalen Regel mit den
 * `--k-fokusring-*`-Tokens.
 *
 * **Der kleine Teil ist der Fund.** Drei Bausteine hingen fuer ihr
 * Fokuszeichen ausschliesslich an `--k-glow-cyan-sm`, und dieses Token ist
 * **orbit-only** — eine bewusste Entscheidung («Papier kennt kein Glas, keine
 * Glow», Spec §1 B-24), die niemand falsch getroffen hat. Uebersehen wurde
 * ihre Folge:
 *
 *  - `.k-switch input` und `.k-checkbox input` sind `opacity: 0` — der
 *    globale Ring liegt auf einem unsichtbaren Element, das Gluehen auf dem
 *    Geschwister war das einzige Zeichen.
 *  - `.k-slider:focus-visible` schaltete den globalen Ring mit
 *    `outline: none` AUSDRUECKLICH ab.
 *
 * Auf Papier faellt das Gluehen auf `none` zurueck. Ergebnis: **kein
 * Fokuszeichen.** Und die drei sind ausgerechnet Bausteine vom 08.09.2026 —
 * aus meiner eigenen Welle.
 *
 * ## Was diese Probe leistet und was nicht
 *
 * Sie liest die ausgelieferte Regel und verlangt, dass jedes der drei ein
 * Zeichen traegt, das **NICHT** an einem themenabhaengigen Token haengt. Sie
 * kann nicht sagen, ob der Ring gut aussieht — das entscheidet ein Blick.
 * Sie verhindert die Rueckkehr der Ursache.
 */

const HIER = dirname(fileURLToPath(import.meta.url));
const AURA = readFileSync(resolve(HIER, '../src/aura.css'), 'utf8');

function ohneKommentare(css: string): string {
  return css.replace(/\/\*[\s\S]*?\*\//g, '');
}
const CSS = ohneKommentare(AURA);

function regelBlock(selektor: string): string {
  const i = CSS.indexOf(`${selektor} {`);
  expect(i, `Selektor ${selektor} nicht gefunden`).toBeGreaterThanOrEqual(0);
  const start = CSS.indexOf('{', i) + 1;
  return CSS.slice(start, CSS.indexOf('}', start));
}

/** Der Block, in dem ein Token definiert ist — `:root` heisst «beide Themen». */
function nurInOrbit(token: string): boolean {
  const rootBlock = CSS.slice(CSS.search(/^:root,/m), CSS.search(/^\[data-theme='orbit'\]/m));
  return !rootBlock.includes(`${token}:`);
}

const BAUSTEINE: readonly { name: string; selektor: string }[] = [
  { name: 'Schalter', selektor: '.k-switch input:focus-visible + .k-switch-strecke' },
  { name: 'Haken', selektor: '.k-checkbox input:focus-visible + .k-checkbox-box' },
  { name: 'Schieber', selektor: '.k-slider:focus-visible' },
];

describe('Fokuszeichen, das in BEIDEN Themen traegt', () => {
  it('KONTROLLFALL: `--k-glow-cyan-sm` ist wirklich orbit-only — sonst gaebe es den Befund gar nicht', () => {
    // Bleibt in beiden Laeufen gruen. Ohne ihn koennte die Probe unten auch
    // gruen sein, weil das Gluehen ueberall gilt — dann waere sie ueberfluessig
    // statt bestanden.
    expect(nurInOrbit('--k-glow-cyan-sm'), 'das Gluehen gilt inzwischen in beiden Themen').toBe(true);
  });

  it('KONTROLLFALL: die Fokusring-Tokens gelten dagegen in BEIDEN Themen', () => {
    expect(nurInOrbit('--k-fokusring-aussen')).toBe(false);
    expect(nurInOrbit('--k-fokusring-breite')).toBe(false);
  });

  for (const b of BAUSTEINE) {
    it(`${b.name}: traegt einen Fokusring aus den themenunabhaengigen Tokens`, () => {
      const regel = regelBlock(b.selektor);
      expect(regel, `${b.name} hat kein outline`).toMatch(/outline:\s*var\(--k-fokusring-breite\)\s+solid\s+var\(--k-fokusring-aussen\)/);
      expect(regel).toMatch(/outline-offset:\s*var\(--k-fokusring-versatz\)/);
    });

    it(`${b.name}: sein Fokuszeichen haengt NICHT allein am Gluehen`, () => {
      // Der falsifizierbare Kern. Genau das war der Zustand vorher.
      const regel = regelBlock(b.selektor);
      const nurGluehen = /^\s*box-shadow:\s*var\(--k-glow-cyan-sm[^;]*\);\s*$/.test(regel);
      expect(nurGluehen, `${b.name} zeigt auf Papier nichts an`).toBe(false);
    });
  }

  it('der Schieber schaltet den Ring NICHT mehr ab', () => {
    // `outline: none` war die ausdrueckliche Abschaltung — sie darf nicht
    // zurueckkommen, auch nicht als vermeintliche Aufraeumarbeit.
    expect(regelBlock('.k-slider:focus-visible')).not.toMatch(/outline:\s*none/);
  });

  it('das Gluehen bleibt erhalten, wo es war — der Zusatz wird nicht gegen den Ring getauscht', () => {
    // Gegenprobe in die andere Richtung: eine Reparatur, die das Gluehen
    // entfernt, macht das dunkle Thema aermer, ohne dass eine Zahl faellt.
    expect(regelBlock(BAUSTEINE[0]!.selektor)).toMatch(/box-shadow:\s*var\(--k-glow-cyan-sm/);
    expect(regelBlock(BAUSTEINE[1]!.selektor)).toMatch(/box-shadow:\s*var\(--k-glow-cyan-sm/);
    expect(regelBlock('.k-slider:focus-visible::-webkit-slider-thumb')).toMatch(/box-shadow:\s*var\(--k-glow-cyan-sm/);
  });
});
