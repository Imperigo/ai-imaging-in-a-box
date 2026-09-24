#!/usr/bin/env node
/**
 * W7-3 — «Kommt der Klick auf den Schalter an?» (Nachlauf zu ROADMAP 990,
 * `docs/W6-2-KLASSEN-BCD-MESSUNG.md` Klasse D — Wurzelursache jetzt am
 * Ursprung behoben, nicht mehr nur an einer einzelnen Insel umgangen).
 *
 * WARUM EIN EIGENSTÄNDIGES SKRIPT UND KEIN VITEST-FALL (dieselbe Ehrlichkeits-
 * klausel wie `apps/kosmo-orbit/test/w5-geschoss-pille-klickfalle.test.ts` /
 * `w5-elementfrompoint-messung.mjs`, `apps/kosmo-orbit/test/insel-scroll-
 * e10.test.tsx`): jsdom hat KEINE Layout-Engine — `getBoundingClientRect()`
 * liefert überall Nullen, `document.elementFromPoint` kennt jsdom nicht
 * einmal dem Namen nach. Der hier zu prüfende Fehler IST eine Aussage über
 * die Mal-Schicht/Trefferordnung eines ECHTEN Browsers (CSS 2.1 Anhang E,
 * Stufe 8) — eine jsdom-Nachstellung würde unsere eigene Erwartung an das
 * Ergebnis codieren, nicht den Browser messen. Darum: echtes Chromium
 * (Playwright), echtes `switch.tsx` (per esbuild direkt aus der Quelldatei
 * kompiliert — KEINE Handabschrift der Komponente, kein Drift-Risiko), das
 * ECHTE `aura.css` unverändert eingebettet.
 *
 * WAS GEMESSEN WIRD (zwei unabhängige Belege für denselben Handgriff):
 *  1. `document.elementFromPoint` auf der Mitte der sichtbaren Schalter-
 *     Strecke (`.k-switch-strecke`) — dieselbe Methode wie
 *     `e2e/w5-1-insel-ueberdeckung.spec.ts`/`tools/insel-ueberdeckungs-
 *     gate.mjs` im ganzen Repo als Definition von «der Klick kommt an»
 *     benutzen. Soll: das `<input>` (oder ein Vorfahre, der es enthält).
 *  2. Ein ECHTER `page.mouse.click(cx, cy)` auf denselben Punkt — kein
 *     `page.check()`/`page.click(selector)` mit eigener Aktionierbarkeits-
 *     Vorprüfung, sondern ein rohes Maus-Klickereignis an Koordinaten, exakt
 *     wie ein echter Zeiger. Soll: die Checkbox schaltet um (`checked`
 *     wechselt von false auf true).
 *
 * AUFRUF
 * ------
 *   PLAYWRIGHT_CHROMIUM_PATH=/opt/pw-browsers/chromium node \
 *     packages/kosmo-ui/test/k-switch-treffer-messung.mjs
 *
 * Exit 0 = beide Belege grün. Exit 1 = mindestens einer rot, mit wörtlicher
 * Fehlermeldung, die den Handgriff beschreibt («der Klick … kommt nicht
 * an»), nicht unsere Lösung.
 */
import { chromium } from 'playwright';
import esbuild from 'esbuild';
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const uiRoot = path.resolve(here, '..');
const switchSrcPath = path.join(uiRoot, 'src', 'switch.tsx');
const auraCssPath = path.join(uiRoot, 'src', 'aura.css');

/** Kompiliert die ECHTE `switch.tsx` (kein Abschrieb) zu ESM und liefert das
 *  Modul via dynamischem Import — Muster: temporäre Datei INNERHALB des
 *  Workspaces, damit `react`/`react/jsx-runtime` über die normale
 *  node_modules-Suche nach oben auflösen. */
async function ladeEchtenKSwitch() {
  const quelle = readFileSync(switchSrcPath, 'utf8');
  const { code } = esbuild.transformSync(quelle, {
    loader: 'tsx',
    format: 'esm',
    jsx: 'automatic',
    jsxImportSource: 'react',
  });
  const tempDir = mkdtempSync(path.join(uiRoot, 'test', '.tmp-k-switch-'));
  const tempDatei = path.join(tempDir, 'switch.kompiliert.mjs');
  writeFileSync(tempDatei, code);
  try {
    const modul = await import(pathToFileURL(tempDatei).href);
    return modul.KSwitch;
  } finally {
    rmSync(tempDir, { recursive: true, force: true });
  }
}

async function main() {
  const { renderToStaticMarkup } = await import('react-dom/server');
  const { createElement } = await import('react');
  const KSwitch = await ladeEchtenKSwitch();

  const markup = renderToStaticMarkup(
    createElement(KSwitch, { label: 'Bemassung', 'data-testid': 'mess-schalter' }),
  );
  const auraCss = readFileSync(auraCssPath, 'utf8');

  const html = `<!doctype html><html><head><meta charset="utf-8" />
<style>html,body{margin:0;padding:40px;background:#111;}${auraCss}</style>
</head><body>${markup}</body></html>`;

  const executablePath =
    process.env.PLAYWRIGHT_CHROMIUM_PATH && !process.env.PLAYWRIGHT_CHROMIUM_PATH.endsWith('/chromium')
      ? process.env.PLAYWRIGHT_CHROMIUM_PATH
      : process.env.PLAYWRIGHT_CHROMIUM_PATH;
  const browser = await chromium.launch(executablePath ? { executablePath } : {});
  let fehler = 0;
  try {
    const page = await browser.newPage();
    await page.setContent(html);
    await page.waitForTimeout(50); // ein Rahmen Settle, kein `checked`-Übergang zu erwarten

    const box = await page.locator('.k-switch-strecke').boundingBox();
    if (!box) {
      console.error('ROT: `.k-switch-strecke` hat keine BoundingBox — die Strecke ist gar nicht sichtbar gerendert.');
      process.exit(1);
    }
    const cx = box.x + box.width / 2;
    const cy = box.y + box.height / 2;

    // Beleg 1: elementFromPoint auf der Streckenmitte.
    const treffer = await page.evaluate(
      ({ cx, cy }) => {
        const input = document.querySelector('input[data-testid="mess-schalter"]');
        const el = document.elementFromPoint(cx, cy);
        const trifftInput = !!el && !!input && (el === input || input.contains(el) || el.contains(input));
        return {
          trifftInput,
          tag: el ? el.tagName : null,
          klasse: el ? el.className : null,
        };
      },
      { cx, cy },
    );

    if (!treffer.trifftInput) {
      fehler += 1;
      console.error(
        `ROT (Beleg 1): der Klick auf die Mitte des Schalters (${cx.toFixed(1)}, ${cy.toFixed(1)}) kommt ` +
          `nicht beim <input> an — elementFromPoint liefert stattdessen <${treffer.tag} class="${treffer.klasse}">.`,
      );
    } else {
      console.log(`GRÜN (Beleg 1): elementFromPoint auf der Streckenmitte trifft das <input>.`);
    }

    // Beleg 2: ein echter Maus-Klick an denselben Koordinaten — kein
    // `page.check()`, keine Aktionierbarkeits-Vorprüfung, exakt wie ein
    // echter Zeiger.
    const vorher = await page.evaluate(
      () => document.querySelector('input[data-testid="mess-schalter"]').checked,
    );
    await page.mouse.click(cx, cy);
    const nachher = await page.evaluate(
      () => document.querySelector('input[data-testid="mess-schalter"]').checked,
    );

    if (vorher !== false || nachher !== true) {
      fehler += 1;
      console.error(
        `ROT (Beleg 2): der Klick auf den Schalter kommt nicht an — vor dem Klick checked=${vorher}, ` +
          `nach dem Klick checked=${nachher} (erwartet: false → true).`,
      );
    } else {
      console.log('GRÜN (Beleg 2): ein echter Klick auf die Streckenmitte schaltet die Checkbox um.');
    }
  } finally {
    await browser.close();
  }

  if (fehler > 0) {
    console.error(`\n${fehler} von 2 Belegen rot.`);
    process.exit(1);
  }
  console.log('\nBeide Belege grün: der Klick auf den Schalter kommt beim <input> an.');
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
