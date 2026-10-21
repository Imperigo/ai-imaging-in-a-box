// @vitest-environment jsdom
import { describe, expect, it } from 'vitest';
import { z } from 'zod';
import { History, KosmoDoc, newId, registerCommand, type ImageAsset } from '@kosmo/kernel';
import { ABLEGEN_BEFEHL, ablegenWeg, projektBild, sichereImProjekt, vergissZuordnung } from '../src/modules/vis/bild-ablage-kern';
import { useProject } from '../src/state/project-store';

/**
 * Naht mit Prepare (21.10.2026): abgelegt wird ueber `publish.bildAblegen({ name, dataUrl }) → Asset-Kennung`
 * (Zweig `claude/kosmo-pubprep-bild-ablegen`, noch nicht eingespielt). Diese Probe stellt den Befehl nach dem
 * Vertrag nach und prueft, dass KosmoVis ihn nimmt, sobald es ihn gibt — und nur mit `{ name, dataUrl }`.
 * Ohne ihn gilt der Stellvertreter `vis.bildSichern` (Probe `kv-bild-aufs-blatt`).
 */
const PNG =
  'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==';

describe('kv-bild-ablegen-naht', () => {
  it('ohne publish.bildAblegen der Stellvertreter, mit ihm genau dieser Aufruf', () => {
    useProject.setState({ doc: new KosmoDoc(), history: new History(), journal: [], revision: 0 });
    vergissZuordnung();
    expect(ablegenWeg()).toBe('stellvertreter');
    const gesehen: unknown[] = [];
    registerCommand({
      id: ABLEGEN_BEFEHL,
      title: 'Bild ablegen (Attrappe nach Vertrag)',
      description: 'Probe: legt ein Bild ins Projekt, ohne es zu platzieren.',
      params: z.object({ name: z.string(), dataUrl: z.string() }).strict(),
      summarize: () => 'Bild abgelegt',
      run: (_doc, p) => {
        gesehen.push(p);
        const asset: ImageAsset = { id: newId('bild'), kind: 'imageasset', name: p.name, mime: 'image/png', data: p.dataUrl.split(',')[1]!, width: 1, height: 1 };
        return [{ id: asset.id, before: null, after: asset }];
      },
    });
    expect(ablegenWeg()).toBe('bildAblegen');
    const stand = sichereImProjekt('vis-1-aaaaaa', 'K1.png', 'echter Render', PNG);
    expect(stand.zustand).toBe('gesichert');
    expect(gesehen).toEqual([{ name: 'echter Render', dataUrl: PNG }]);
    const a = projektBild('vis-1-aaaaaa', 'K1.png')!;
    expect(a.name).toBe('echter Render');
    expect(a.visHerkunft).toBeUndefined();
    // Ein Bild, ein Eintrag — auch ueber diesen Weg.
    sichereImProjekt('vis-1-aaaaaa', 'K1.png', 'echter Render', PNG);
    expect(gesehen).toHaveLength(1);
  });
});
