import { readdirSync, readFileSync, statSync } from 'node:fs';
import path from 'node:path';

/**
 * Gemeinsames Zählwerk der drei Leiter-Wächter (Rundung, Dauer, Ebene) —
 * Owner-Entscheide 21.09.2026.
 *
 * Warum überhaupt eine geteilte Datei: alle drei Wächter müssen dieselbe
 * Frage stellen — «wie viele Stellen im Haus tun X?» — und alle drei müssen
 * sie GLEICH stellen. Drei eigene Datei-Wanderungen wären drei Gelegenheiten,
 * denselben Geltungsbereich um eine Kleinigkeit verschieden zu schneiden;
 * dann zählen zwei Wächter dasselbe und meinen Verschiedenes.
 *
 * Der Geltungsbereich ist derselbe wie in `tools/token-drift-gate.mjs` und
 * `tools/bewegungsdauer-gate.mjs`: die zwei Wurzeln `apps/kosmo-orbit/src`
 * und `packages/kosmo-ui/src`. Das ist der Bereich, den die Messungen der
 * Entscheidblätter vom 21.09.2026 gemessen haben.
 */

/** Repo-Wurzel (`kosmo-orbit/`), von `packages/kosmo-ui/test/` aus. */
export const repoWurzel = path.resolve(__dirname, '../../..');

const UEBERSPRINGEN = new Set([
  'node_modules',
  '.git',
  'dist',
  'dev-dist',
  'build',
  'test-results',
  'playwright-report',
  'e2e-results',
]);

export const GELTUNGS_WURZELN = ['apps/kosmo-orbit/src', 'packages/kosmo-ui/src', 'packages/kosmo-insel/src'] as const;

function sammle(dir: string, endungen: readonly string[], out: string[]): void {
  let eintraege;
  try {
    eintraege = readdirSync(dir, { withFileTypes: true });
  } catch {
    return;
  }
  for (const e of eintraege) {
    if (e.isDirectory()) {
      if (UEBERSPRINGEN.has(e.name)) continue;
      sammle(path.join(dir, e.name), endungen, out);
    } else if (e.isFile() && endungen.some((x) => e.name.endsWith(x))) {
      out.push(path.join(dir, e.name));
    }
  }
}

/** Alle Quelldateien unter den Geltungswurzeln. */
export function quelldateien(endungen: readonly string[] = ['.css', '.ts', '.tsx']): string[] {
  const out: string[] = [];
  for (const wurzel of GELTUNGS_WURZELN) {
    const abs = path.join(repoWurzel, wurzel);
    try {
      if (!statSync(abs).isDirectory()) continue;
    } catch {
      continue;
    }
    sammle(abs, endungen, out);
  }
  if (out.length === 0) {
    // Die Leerlauf-Falle: ein Wächter, der nichts findet, meldet grün und
    // hat nichts geprüft. Dieselbe Auflage wie in `bewegungsdauer-gate.mjs`.
    throw new Error(
      `leiter-bestand: keine Quelldatei unter ${GELTUNGS_WURZELN.join(', ')} gefunden ` +
        `(Wurzel: ${repoWurzel}) — der Wächter hätte grün gemeldet, ohne etwas zu sehen.`,
    );
  }
  return out.sort();
}

/** Zählt alle Treffer eines Musters über die Geltungswurzeln, mit Fundstellen.
 *
 * KOMMENTARE ZÄHLEN NICHT. Das ist keine Feinheit, sondern die Lehre aus
 * P-WACHEN-KLARSICHT (03.09.2026): eine reine Textsuche liest Kommentartext
 * wie Code, und genau so kam die Dauer-Messung dreimal auf 54 statt 53.
 * Diese Wächter beschreiben ihre eigenen Token in Prosa — ohne diesen Schritt
 * zählt jeder von ihnen zuerst seine eigene Dokumentation. */
export function zaehle(
  muster: RegExp,
  endungen: readonly string[] = ['.css', '.ts', '.tsx'],
): { anzahl: number; stellen: { datei: string; zeile: number; text: string }[] } {
  const stellen: { datei: string; zeile: number; text: string }[] = [];
  let anzahl = 0;
  const global = new RegExp(muster.source, muster.flags.includes('g') ? muster.flags : `${muster.flags}g`);
  for (const abs of quelldateien(endungen)) {
    const rel = path.relative(repoWurzel, abs).split(path.sep).join('/');
    const zeilen = ohneKommentare(readFileSync(abs, 'utf8')).split('\n');
    zeilen.forEach((zeile, i) => {
      global.lastIndex = 0;
      const treffer = zeile.match(global);
      if (!treffer) return;
      anzahl += treffer.length;
      stellen.push({ datei: rel, zeile: i + 1, text: zeile.trim() });
    });
  }
  return { anzahl, stellen };
}

/** Leert Blockkommentare (`/* … *\/`, und damit auch JSDoc) zeichenweise;
 * die Zeilenzahl bleibt erhalten — genau die Eigenschaft, die die
 * `datei:zeile`-Meldungen der Wächter brauchen. Dieselbe Funktion und
 * derselbe Grund wie in `tools/doppelstamm-gate.mjs`.
 *
 * Zeilenkommentare werden NUR geleert, wenn die Zeile mit `//` oder `*`
 * beginnt. Ein `//` mitten in einer Zeile könnte in einer Zeichenkette
 * stehen (`'https://…'`); dort abzuschneiden würde echten Code verstecken,
 * und eine Wache, die zu wenig sieht, ist schlimmer als eine, die zu viel
 * meldet. */
export function ohneKommentare(quelle: string): string {
  let out = '';
  let i = 0;
  while (i < quelle.length) {
    if (quelle.startsWith('/*', i)) {
      const ende = quelle.indexOf('*/', i + 2);
      const bis = ende === -1 ? quelle.length : ende + 2;
      for (let k = i; k < bis; k++) out += quelle.charAt(k) === '\n' ? '\n' : ' ';
      i = bis;
      continue;
    }
    out += quelle.charAt(i);
    i++;
  }
  return out
    .split('\n')
    .map((zeile) => (/^\s*(\/\/|\*)/.test(zeile) ? '' : zeile))
    .join('\n');
}

/** Liest `--name: WERT;` aus einem CSS-Text und löst reine `var(--x)`-
 * Verweise auf (mit Zyklus-Riegel) — dieselbe Auflösung wie in
 * `token-spiegel.test.ts`, damit beide Wächter dasselbe lesen. */
export function tokenWert(css: string, name: string): string {
  const gesehen = new Set<string>();
  let aktuell = name;
  for (;;) {
    if (gesehen.has(aktuell)) throw new Error(`leiter-bestand: Verweis-Zyklus über "${aktuell}".`);
    gesehen.add(aktuell);
    const m = css.match(new RegExp(`${aktuell}:\\s*([^;]+);`));
    const roh = m?.[1];
    if (roh === undefined) throw new Error(`leiter-bestand: Token "${aktuell}" steht nicht in aura.css.`);
    const wert = roh.replace(/\/\*[\s\S]*?\*\//g, '').trim();
    const ziel = wert.match(/^var\((--[a-z0-9-]+)\)$/)?.[1];
    if (ziel === undefined) return wert;
    aktuell = ziel;
  }
}

export const auraCssPfad = path.join(repoWurzel, 'packages/kosmo-ui/src/aura.css');
export const auraCss = (): string => readFileSync(auraCssPfad, 'utf8');

/** Der spätere, theme-unabhängige `:root { … }`-Block aus aura.css — der,
 * in dem Radien, Bewegung und Ebenen stehen. Dieselbe Nadel wie in
 * `token-spiegel.test.ts` (die schliessende Klammer gehört dazu, sonst
 * trifft `[data-theme='paper'] .k-select {` mit).
 *
 * WARUM DIE WÄCHTER HIERAUS LESEN UND NICHT AUS DER GANZEN DATEI: eine
 * Deklaration, die aus ihrem Block herausrutscht, steht immer noch im Text.
 * Ein Wächter, der die Datei als Text durchsucht, findet sie und meldet
 * grün — während jsdoms CSS-Engine dieselbe Zeile in den Selektor der ERSTEN
 * Regel schluckt und `:root, [data-theme='paper']` wirkungslos macht. Genau
 * das ist beim Bau dieser Leitern passiert: drei Wächter grün, eine fremde
 * Wache (`akzent-theme-waechter.test.ts`) rot. */
export function rootBlock(css: string): string {
  const nadel = ':root {';
  const start = css.indexOf(nadel);
  if (start === -1) throw new Error('leiter-bestand: der :root-Block steht nicht in aura.css.');
  const auf = css.indexOf('{', start);
  let tiefe = 0;
  let i = auf;
  for (; i < css.length; i++) {
    const z = css.charAt(i);
    if (z === '{') tiefe++;
    else if (z === '}') {
      tiefe--;
      if (tiefe === 0) break;
    }
  }
  return css.slice(auf, i + 1);
}
