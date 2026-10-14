import { describe, expect, it } from 'vitest';
import { materialTextur } from '@kosmo/kernel';
import { kachelBlobUrl } from '../src/modules/vis/textur-bild';

/**
 * P16 — der Textur-Knopf zeigt die Kacheln aus `derive/textur.ts` als
 * `<img>`/Download-Link. `alsPng()` liefert reine PNG-Bytes (kein Canvas,
 * kein DOM noetig, s. Kopfkommentar `derive/textur.ts`) — diese Datei macht
 * daraus NUR eine `blob:`-URL, keine zweite Kodierung.
 */
describe('kachelBlobUrl — Kachel als blob:-URL, ohne zweite PNG-Kodierung', () => {
  it('liefert eine blob:-URL', () => {
    const karten = materialTextur('beton');
    expect(karten).not.toBeNull();
    const url = kachelBlobUrl(karten!.farbe);
    expect(url.startsWith('blob:')).toBe(true);
  });

  it('zwei Aufrufe liefern zwei verschiedene URLs (kein stiller Cache)', () => {
    const karten = materialTextur('beton')!;
    const a = kachelBlobUrl(karten.farbe);
    const b = kachelBlobUrl(karten.farbe);
    expect(a).not.toBe(b);
  });
});
