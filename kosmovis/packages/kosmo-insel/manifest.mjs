#!/usr/bin/env node
/**
 * **Manifest von `@kosmo/insel`** — Pfad → sha256 je Datei des Pakets.
 *
 * Owner-Entscheid E269 (20.10.2026): das Paket bleibt in KosmoOrbit privat; in das
 * öffentliche Visbox-Repo darf es als **unveränderte Kopie** mit diesem Manifest.
 * Das Manifest macht «die Kopie weicht ab» in beiden Richtungen sichtbar:
 *
 *  - KosmoOrbit (`tools/insel-manifest-gate.mjs`): rot, wenn sich das Paket ändert
 *    und das Manifest nicht nachgezogen ist (`node packages/kosmo-insel/manifest.mjs --schreiben`).
 *  - Visbox: dieselbe Datei liegt in der Kopie; `node <kopie>/manifest.mjs` prüft die
 *    Kopie gegen ihr Manifest und wird rot bei jeder Abweichung.
 *
 * Gezählt werden alle Dateien des Paketordners ausser `node_modules/`, `.vite/` und
 * dem Manifest selbst. Den KosmoOrbit-Kopf trägt das Manifest bewusst nicht (es läge
 * im Commit, den es benennen müsste); den Kopf hält der Bezieher bei der Übernahme fest.
 * Nur Node-Bordmittel, damit die Kopie ohne Abhängigkeiten prüfbar ist.
 */
import { createHash } from 'node:crypto';
import { readFileSync, readdirSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

export const MANIFEST_DATEI = 'kosmo-insel.manifest.json';
export const SCHEMA = 'kosmo.insel-manifest/v1';
const AUSGELASSEN = new Set(['node_modules', '.vite', MANIFEST_DATEI]);

/** Alle gezählten Dateien, relativ zum Paketordner, mit `/`, sortiert. */
export function sammle(ordner) {
  const out = [];
  const lauf = (dir) => {
    for (const e of readdirSync(dir, { withFileTypes: true })) {
      if (AUSGELASSEN.has(e.name)) continue;
      const abs = path.join(dir, e.name);
      if (e.isDirectory()) lauf(abs);
      else if (e.isFile()) out.push(path.relative(ordner, abs).split(path.sep).join('/'));
    }
  };
  lauf(ordner);
  return out.sort();
}

/** Das Manifest, wie es für den Ordner jetzt stimmen würde. */
export function erzeuge(ordner) {
  const dateien = {};
  for (const rel of sammle(ordner)) {
    dateien[rel] = createHash('sha256').update(readFileSync(path.join(ordner, rel))).digest('hex');
  }
  return { schema: SCHEMA, paket: '@kosmo/insel', dateien };
}

/** Unterschied zwischen einem gespeicherten und dem jetzigen Manifest. */
export function vergleiche(gespeichert, jetzt) {
  const alt = gespeichert?.dateien ?? {};
  const neu = jetzt.dateien;
  return {
    fehlt: Object.keys(alt).filter((p) => !(p in neu)).sort(),
    hinzu: Object.keys(neu).filter((p) => !(p in alt)).sort(),
    geaendert: Object.keys(neu).filter((p) => p in alt && alt[p] !== neu[p]).sort(),
  };
}

export function text(manifest) {
  return `${JSON.stringify(manifest, null, 2)}\n`;
}

/** Prüft `ordner` gegen sein Manifest; `schreiben` zieht es nach. Gibt den Exit-Code zurück. */
export function lauf(ordner, { schreiben = false, name = 'insel-manifest' } = {}) {
  const jetzt = erzeuge(ordner);
  const ziel = path.join(ordner, MANIFEST_DATEI);
  if (schreiben) {
    writeFileSync(ziel, text(jetzt));
    console.log(`${MANIFEST_DATEI}: ${Object.keys(jetzt.dateien).length} Datei(en) geschrieben.`);
    console.log(`URTEIL ${name}: GRUEN (exit 0)`);
    return 0;
  }
  let gespeichert = null;
  try {
    gespeichert = JSON.parse(readFileSync(ziel, 'utf8'));
  } catch {
    console.error(`ROT — ${MANIFEST_DATEI} fehlt oder ist kein JSON.`);
    console.error(`URTEIL ${name}: ROT (exit 1)`);
    return 1;
  }
  const d = vergleiche(gespeichert, jetzt);
  const zahl = d.fehlt.length + d.hinzu.length + d.geaendert.length;
  const schemaFalsch = gespeichert.schema !== SCHEMA;
  if (zahl === 0 && !schemaFalsch) {
    console.log(`GRUEN — ${Object.keys(jetzt.dateien).length} Datei(en) stimmen mit ${MANIFEST_DATEI} überein.`);
    console.log(`URTEIL ${name}: GRUEN (exit 0)`);
    return 0;
  }
  console.error(`ROT — ${zahl} Abweichung(en) gegen ${MANIFEST_DATEI}:`);
  if (schemaFalsch) console.error(`  - Schema ist «${gespeichert.schema}», erwartet «${SCHEMA}».`);
  for (const p of d.geaendert) console.error(`  - geändert: ${p}`);
  for (const p of d.hinzu) console.error(`  - neu, nicht im Manifest: ${p}`);
  for (const p of d.fehlt) console.error(`  - fehlt, steht im Manifest: ${p}`);
  console.error('In KosmoOrbit nach einer gewollten Änderung: node packages/kosmo-insel/manifest.mjs --schreiben. In einer Kopie: die Kopie ist nicht mehr unverändert.');
  console.error(`URTEIL ${name}: ROT (exit 1)`);
  return 1;
}

if (import.meta.url === pathToFileURL(process.argv[1] ?? '').href) {
  const ordner = path.dirname(fileURLToPath(import.meta.url));
  process.exitCode = lauf(ordner, { schreiben: process.argv.includes('--schreiben') });
}
