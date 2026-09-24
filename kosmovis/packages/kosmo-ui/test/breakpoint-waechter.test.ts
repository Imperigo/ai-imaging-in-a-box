import { readFileSync, readdirSync, statSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';
import { breakpoint } from '../src/tokens';

/**
 * Breakpoint-Wächter (D-6, E-3 `docs/design/GESTALTUNGS-ENTSCHEIDE-2026-08-10.md`)
 * — die Kanon-Skala kennt genau drei Breiten-Grenzen (`schmal`/`mittel`/
 * `weit` = 700/1100/1500px, `tokens.ts` `breakpoint`). Media-Queries können
 * kein `var()`, darum keine CSS-Token-Wache wie bei Farben/Radien/Sperrwerten
 * — dieser Test übernimmt dieselbe Rolle mechanisch für `@media`-Breiten:
 * er liest per `fs` alle `.css`-Dateien unter `apps/kosmo-orbit/src` und
 * `packages/kosmo-ui/src` (Lese-Muster wie `apps/kosmo-orbit/test/
 * css-var-konsistenz.test.ts`) und bricht, sobald ein `min-width`/
 * `max-width`-Wert ausserhalb {700, 1100, 1500} auftaucht — PLUS 701, der
 * einzig zulässigen `min-width`-Kehrseite von 700 im E-3-Zwischenband
 * (s. Kommentar bei `ERLAUBTE_BREITEN` unten).
 *
 * Ausgenommen (E-3, wörtlich): `prefers-*`, `print`, `pointer`, `hover` —
 * keine dieser Query-Formen trägt eine px-Breite, die von der Skala
 * betroffen wäre; die Ausnahme ist eine Sicherheitsmarge, kein Freibrief
 * (der Test prüft sie unten selbst gegen, s. «beweist, dass …»).
 */

const HIER = dirname(fileURLToPath(import.meta.url));
const APP_SRC = resolve(HIER, '../../../apps/kosmo-orbit/src');
const UI_SRC = resolve(HIER, '../src');

/** Die drei Kanon-Grenzen, direkt aus dem TS-Spiegel — keine zweite Zahlen-
 * Quelle — PLUS 701: E-3 verlangt das Zwischenband ausdrücklich als
 * `(min-width: 701px) and (max-width: 1100px)` (nicht `701`, um die
 * Doppel-Abdeckung von exakt 700px mit dem `max-width: 700px`-Nachbarn zu
 * vermeiden) — 701 ist darum kein viertes Mass, sondern die einzig
 * zulässige `min-width`-Kehrseite von `schmal` (700). */
const ERLAUBTE_BREITEN: ReadonlySet<number> = new Set([...Object.values(breakpoint), 701]);

/** Query-Formen, die E-3 ausdrücklich von der Breiten-Skala ausnimmt. */
const AUSNAHME_MUSTER = /prefers-|print|pointer|hover/;

/** Entfernt CSS-Block-Kommentare (mit Leerzeichen überschrieben, Zeilen-
 * nummern bleiben stabil) — sonst zählt eine Erklärung wie «war 860px» in
 * Prosa als echter Fund. CSS kennt nur Block-Kommentare, keine
 * Zeilenkommentare — ein einziges Muster genügt. */
function ohneKommentare(css: string): string {
  return css.replace(/\/\*[\s\S]*?\*\//g, (m) => m.replace(/[^\n]/g, ' '));
}

const MEDIA_REGEL = /@media\s+([^{]+)\{/g;
const BREITEN_PX = /(?:min|max)-width\s*:\s*(\d+)px/g;

export interface OffScaleBreakpoint {
  datei: string;
  zeile: number;
  bedingung: string;
  breite: number;
}

/**
 * Der eigentliche Prüfkern — reine Funktion auf bereits eingelesenen
 * Quelltexten (kein Dateisystemzugriff), darum ohne echte Dateien testbar
 * (Muster `findeUngedeckteVarAufrufe` in `css-var-konsistenz.test.ts`).
 */
export function findeOffScaleBreakpoints(
  quellDateien: readonly { datei: string; inhalt: string }[],
): OffScaleBreakpoint[] {
  const treffer: OffScaleBreakpoint[] = [];
  for (const { datei, inhalt } of quellDateien) {
    const ohneKomm = ohneKommentare(inhalt);
    for (const m of ohneKomm.matchAll(MEDIA_REGEL)) {
      const bedingung = m[1]!.trim();
      if (AUSNAHME_MUSTER.test(bedingung)) continue;
      const index = m.index ?? 0;
      const zeile = ohneKomm.slice(0, index).split('\n').length;
      for (const bm of bedingung.matchAll(BREITEN_PX)) {
        const breite = Number(bm[1]);
        if (!ERLAUBTE_BREITEN.has(breite)) {
          treffer.push({ datei, zeile, bedingung, breite });
        }
      }
    }
  }
  return treffer;
}

function alleCssDateien(dir: string): string[] {
  const treffer: string[] = [];
  for (const eintrag of readdirSync(dir)) {
    const pfad = join(dir, eintrag);
    const stat = statSync(pfad);
    if (stat.isDirectory()) treffer.push(...alleCssDateien(pfad));
    else if (eintrag.endsWith('.css')) treffer.push(pfad);
  }
  return treffer;
}

function quellenLesen(dir: string): { datei: string; inhalt: string }[] {
  return alleCssDateien(dir).map((pfad) => ({ datei: pfad, inhalt: readFileSync(pfad, 'utf8') }));
}

describe('Breakpoint-Wächter (D-6, E-3) — @media-Breiten bleiben auf {700, 1100, 1500}', () => {
  it('keine CSS-Datei unter apps/kosmo-orbit/src oder packages/kosmo-ui/src verlässt die Kanon-Skala', () => {
    const quellen = [...quellenLesen(APP_SRC), ...quellenLesen(UI_SRC)];
    const treffer = findeOffScaleBreakpoints(quellen);
    const meldung = treffer
      .map((t) => `${t.datei}:${t.zeile}: @media ${t.bedingung} — ${t.breite}px ausserhalb {700, 701, 1100, 1500}`)
      .join('\n');
    expect(treffer, `Off-Scale-Breakpoints:\n${meldung}`).toEqual([]);
  });

  it('der Sammelkreis umfasst tatsächlich beide Quellbäume (kein leerer Scan als Fehlalarm-Freispruch)', () => {
    expect(alleCssDateien(APP_SRC).length).toBeGreaterThan(0);
    expect(alleCssDateien(UI_SRC).length).toBeGreaterThan(0);
  });

  it('die Kanon-Skala selbst besteht aus genau den drei erwarteten Werten', () => {
    expect(new Set(Object.values(breakpoint))).toEqual(new Set([700, 1100, 1500]));
  });
});

describe('findeOffScaleBreakpoints — beweist, dass die Prüfung selbst anschlägt', () => {
  it('eine Breite ausserhalb der Skala macht den Test ROT (synthetische Fixtures, keine echten Dateien)', () => {
    const dateien = [{ datei: 'fake.css', inhalt: '@media (max-width: 860px) { .x { color: red; } }' }];
    expect(findeOffScaleBreakpoints(dateien)).toEqual([
      { datei: 'fake.css', zeile: 1, bedingung: '(max-width: 860px)', breite: 860 },
    ]);
  });

  it('die Kanon-Breiten (700/701/1100/1500, inkl. der sanktionierten Zwischenband-Form) erzeugen keinen Fehlalarm', () => {
    const dateien = [
      {
        datei: 'fake.css',
        inhalt:
          '@media (max-width: 700px) { .a {} }\n' +
          '@media (min-width: 701px) and (max-width: 1100px) { .b {} }\n' +
          '@media (max-width: 1500px) { .c {} }\n',
      },
    ];
    expect(findeOffScaleBreakpoints(dateien)).toEqual([]);
  });

  it('prefers-reduced-motion/print/pointer/hover bleiben unberührt, auch mit einer fremden px-Zahl', () => {
    const dateien = [
      {
        datei: 'fake.css',
        inhalt:
          '@media (prefers-reduced-motion: reduce) { .a {} }\n' +
          '@media print { .b {} }\n' +
          '@media (pointer: coarse) { .c { width: 999px; } }\n' +
          '@media (hover: none) { .d {} }\n',
      },
    ];
    expect(findeOffScaleBreakpoints(dateien)).toEqual([]);
  });

  it('ein Off-Scale-Beispiel in einem Blockkommentar zählt nicht als Fund', () => {
    const dateien = [
      {
        datei: 'fake.css',
        inhalt: '/* Beispiel: @media (max-width: 860px) { … } */\n.x { color: red; }',
      },
    ];
    expect(findeOffScaleBreakpoints(dateien)).toEqual([]);
  });

  it('die gemeldete Zeilennummer stimmt trotz entfernter Blockkommentare', () => {
    const dateien = [
      {
        datei: 'fake.css',
        inhalt: '/* Zeile 1\n   Zeile 2 */\n@media (max-width: 640px) { .a {} }\n',
      },
    ];
    expect(findeOffScaleBreakpoints(dateien)).toEqual([
      { datei: 'fake.css', zeile: 3, bedingung: '(max-width: 640px)', breite: 640 },
    ]);
  });

  it('ein Zwischenband mit zwei Off-Scale-Grenzen meldet BEIDE Zahlen', () => {
    const dateien = [
      { datei: 'fake.css', inhalt: '@media (min-width: 861px) and (max-width: 1150px) { .a {} }\n' },
    ];
    expect(findeOffScaleBreakpoints(dateien)).toEqual([
      { datei: 'fake.css', zeile: 1, bedingung: '(min-width: 861px) and (max-width: 1150px)', breite: 861 },
      { datei: 'fake.css', zeile: 1, bedingung: '(min-width: 861px) and (max-width: 1150px)', breite: 1150 },
    ]);
  });

  it('die sanktionierte 701-Grenze allein (ohne Partner-700) wäre trotzdem kein Fehlalarm', () => {
    // Gegenprobe zur ERLAUBTE_BREITEN-Erweiterung: 701 ist generell erlaubt,
    // nicht nur im Zwischenband-Kontext — dieselbe Zahl in einer anderen
    // Bedingung darf den Test nicht fälschlich rot machen.
    const dateien = [{ datei: 'fake.css', inhalt: '@media (min-width: 701px) { .a {} }\n' }];
    expect(findeOffScaleBreakpoints(dateien)).toEqual([]);
  });
});
