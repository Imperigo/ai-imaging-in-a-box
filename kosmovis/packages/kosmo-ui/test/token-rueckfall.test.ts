import { describe, expect, it } from 'vitest';
import { readFileSync, readdirSync, statSync } from 'node:fs';
import { dirname, join, relative, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

/**
 * **P-c (08.09.2026) — ein Token, das es nur in einem Thema gibt, darf nicht
 * ohne Rueckfall verbraucht werden.**
 *
 * `aura.css` fuehrt siebzehn Tokens, die ausschliesslich unter
 * `[data-theme='orbit']` definiert sind. Wer eines davon im hellen Thema
 * liest, bekommt **nichts** — kein Fehler, keine Meldung, die Eigenschaft
 * faellt einfach aus. Eine Trennlinie verschwindet, eine Flaeche wird
 * durchsichtig, und weil ausgeliefert das dunkle Thema wird, faellt es
 * niemandem auf.
 *
 * Gemessen waren es acht Fundstellen — und die Nachpruefung hat die Zahl auf
 * **sechs** gesenkt: zwei standen SELBST in einem `[data-theme='orbit']`-Block,
 * und dort waere ein Rueckfall unerreichbarer Code. Genau diese Unterscheidung
 * muss die Wache treffen, sonst erzwingt sie zwei sinnlose Aenderungen.
 *
 * Behoben wurde nicht an den Aufrufstellen, sondern an der Leiter: `--k-line-subtil`
 * und `--k-sunken` haben jetzt eine Papier-Sprosse. Nur die Glas-Tokens bleiben
 * bewusst orbit-only — Papier kennt kein Glas — und bekommen einen Rueckfall
 * am Aufrufort.
 */

const HIER = dirname(fileURLToPath(import.meta.url));
const UI_SRC = resolve(HIER, '../src');
const APP_SRC = resolve(HIER, '../../../apps/kosmo-orbit/src');
const AURA = readFileSync(join(UI_SRC, 'aura.css'), 'utf8');

function ohneKommentare(text: string): string {
  return text.replace(/\/\*[\s\S]*?\*\//g, '').replace(/^[ \t]*\/\/.*$/gm, '');
}

function dateien(wurzel: string, endungen: string[]): string[] {
  const raus: string[] = [];
  const lauf = (d: string): void => {
    for (const n of readdirSync(d)) {
      const p = join(d, n);
      if (statSync(p).isDirectory()) lauf(p);
      else if (endungen.some((e) => n.endsWith(e))) raus.push(p);
    }
  };
  lauf(wurzel);
  return raus;
}

/**
 * Ein zeilenweiser Durchgang statt einer Block-Zerlegung — und das ist eine
 * Korrektur an meinem eigenen ersten Versuch: der zaehlte Klammern ab dem
 * `:root,`-Selektor und brach mitten im Block ab, worauf die Wache zwanzig
 * Tokens als «nur orbit» meldete, die in beiden Themen stehen. Ein Parser,
 * der zu frueh aufhoert, erzeugt Befunde statt sie zu finden.
 *
 * Hier wird stattdessen mitgefuehrt, ob die aktuelle Zeile unterhalb eines
 * `[data-theme='orbit']`-Selektors liegt. «Nur orbit» heisst dann: irgendwo
 * unter orbit definiert UND nirgends ausserhalb.
 */
const CSS = ohneKommentare(AURA);

function themenLage(css: string): { nurOrbit: string[]; ueberall: Set<string> } {
  const unterOrbit = new Set<string>();
  const ausserhalb = new Set<string>();
  let tiefe = 0;
  let orbitAb = -1;
  for (const zeile of css.split('\n')) {
    if (orbitAb < 0 && /\[data-theme=['"]orbit['"]\]/.test(zeile)) orbitAb = tiefe;
    for (const m of zeile.matchAll(/^\s*(--[a-z0-9-]+)\s*:/g)) {
      (orbitAb >= 0 ? unterOrbit : ausserhalb).add(m[1]!);
    }
    tiefe += (zeile.match(/\{/g) ?? []).length - (zeile.match(/\}/g) ?? []).length;
    if (orbitAb >= 0 && tiefe <= orbitAb) orbitAb = -1;
  }
  return { nurOrbit: [...unterOrbit].filter((t) => !ausserhalb.has(t)).sort(), ueberall: ausserhalb };
}

const { nurOrbit: NUR_ORBIT, ueberall: IN_ROOT } = themenLage(CSS);

describe('P-c — kein orbit-only Token ohne Rueckfall', () => {
  it('die Wache hat ueberhaupt etwas zu bewachen', () => {
    // Gegenprobe gegen eine leere Messung: faende der Parser nichts, waere
    // jede Null unten wertlos.
    expect(IN_ROOT.size, 'ausserhalb von orbit keine Tokens gefunden — Parser kaputt').toBeGreaterThan(30);
    expect(NUR_ORBIT.length, 'keine orbit-only Tokens gefunden — Parser kaputt').toBeGreaterThan(5);
  });

  it('`--k-line-subtil` und `--k-sunken` sind KEINE orbit-only Tokens mehr', () => {
    expect(NUR_ORBIT, '--k-line-subtil fehlt im hellen Thema').not.toContain('--k-line-subtil');
    expect(NUR_ORBIT, '--k-sunken fehlt im hellen Thema').not.toContain('--k-sunken');
  });

  it('die Glas-Tokens bleiben bewusst orbit-only — Papier kennt kein Glas', () => {
    // Kein Versehen, sondern Kanon (`GESTALTUNGSKONZEPT.md` §05). Faende die
    // Wache sie im hellen Thema, waere das der Fehler.
    expect(NUR_ORBIT).toContain('--k-glass-fill');
    expect(NUR_ORBIT).toContain('--k-glass-stroke');
  });

  it('keine Fundstelle verbraucht ein orbit-only Token ohne Rueckfall', () => {
    const funde: string[] = [];
    const pruefe = (datei: string, istCss: boolean): void => {
      const text = ohneKommentare(readFileSync(datei, 'utf8'));
      // In CSS zaehlt der Selektor-Zusammenhang: steht die Regel selbst
      // unter `[data-theme='orbit']`, waere ein Rueckfall toter Code.
      const zeilen = text.split('\n');
      let orbitTiefe = -1;
      let tiefe = 0;
      zeilen.forEach((zeile, nr) => {
        if (istCss && orbitTiefe < 0 && /\[data-theme=['"]orbit['"]\]/.test(zeile)) orbitTiefe = tiefe;
        for (const t of NUR_ORBIT) {
          const re = new RegExp(`var\\(\\s*${t}\\s*\\)`);
          if (re.test(zeile) && !(istCss && orbitTiefe >= 0)) {
            funde.push(`${relative(resolve(HIER, '../../..'), datei)}:${nr + 1} — ${t}`);
          }
        }
        tiefe += (zeile.match(/\{/g) ?? []).length - (zeile.match(/\}/g) ?? []).length;
        if (istCss && orbitTiefe >= 0 && tiefe <= orbitTiefe) orbitTiefe = -1;
      });
    };
    for (const f of dateien(UI_SRC, ['.css'])) pruefe(f, true);
    for (const f of dateien(APP_SRC, ['.css'])) pruefe(f, true);
    for (const f of dateien(APP_SRC, ['.tsx', '.ts'])) pruefe(f, false);
    expect(funde, `orbit-only Token ohne Rueckfall:\n${funde.join('\n')}`).toEqual([]);
  });
});
