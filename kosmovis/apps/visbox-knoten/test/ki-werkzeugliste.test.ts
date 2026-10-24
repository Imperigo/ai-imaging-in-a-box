// @vitest-environment jsdom
import { readFileSync, writeFileSync, existsSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';
import { visWerkzeuge } from '../../kosmo-orbit/src/modules/vis/ki-werkzeuge';
import { blickMausWerkzeuge } from '../src/ki-wirt';

/**
 * VISBOX-EIGEN (KI-Bedienung Stufe 3): Die Werkzeugliste der Knotenansicht liegt auch als Datei im
 * Bau (`dist/ki-werkzeugliste.json`), damit die Mac-App sie Claude nennen kann, bevor die
 * Knotenansicht offen ist — `tools/list` fragt Claude nur einmal je Sitzung (`listChanged: false`).
 * Ist die Knotenansicht nicht offen, antwortet jedes dieser Werkzeuge mit einem Satz.
 *
 * `tools/knoten_bau.py` schreibt die Datei nach dem Bau (`VISBOX_KI_LISTE_SCHREIBEN=1`); sonst
 * prueft diese Probe, dass sie zur Quelle passt.
 */
// Die Probe laeuft im Ordner der Wirtsseite (`npm test` je Arbeitsbereich, `knoten_bau.py`).
const DATEI = resolve(process.cwd(), 'dist/ki-werkzeugliste.json');

describe('Werkzeugliste im Bau', () => {
  it('passt zur Quelle', () => {
    // Seit Stufe 6 (21.10.2026) dazu Blick und Maus — dieselbe Liste wie `visboxKi.werkzeuge()` plus
    // `visboxKi.blickMausWerkzeuge()`.
    const liste = { format: 'visbox.ki-werkzeugliste/v1', werkzeuge: [...visWerkzeuge(), ...blickMausWerkzeuge()] };
    const text = `${JSON.stringify(liste, null, 1)}\n`;
    if (process.env['VISBOX_KI_LISTE_SCHREIBEN'] === '1') writeFileSync(DATEI, text, 'utf-8');
    expect(existsSync(DATEI), 'dist/ki-werkzeugliste.json fehlt — python3 tools/knoten_bau.py').toBe(true);
    expect(readFileSync(DATEI, 'utf-8'), 'veraltet — python3 tools/knoten_bau.py').toBe(text);
    expect(liste.werkzeuge.map((w) => w.name)).toEqual(expect.arrayContaining(['graph_lesen', 'vis_paket', 'vis_render', 'vis_grundlage', 'vis_nodeLoeschen', 'visbox_blick', 'visbox_maus']));
  });
});
