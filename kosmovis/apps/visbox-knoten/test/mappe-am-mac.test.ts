import { describe, expect, it, vi } from 'vitest';
import { holeInDieMappeAmMac, WEG_MODELL_HOLEN } from '../src/mappe';
import { zielDerPalette } from '../src/kopf';

/**
 * VISBOX-EIGEN («Visbox eigenständig», Schritt 3, 21.10.2026, Blatt 36): Die Mappe liegt am Mac.
 * Nach «Datei laden …» holt die App das Modell der neuen Mappe am Heim-PC in die offene Mappe am
 * Mac; ohne Mappe am Mac (404) bleibt alles wie bisher.
 */
describe('Mappe am Mac', () => {
  it('fragt nach «Datei laden …» die App, das Modell zu holen', async () => {
    const holen = vi.fn(async (_e: RequestInfo | URL, _i?: RequestInit) => new Response('{"mappe":"Hof"}'));
    expect(await holeInDieMappeAmMac('Hof', holen as unknown as typeof fetch, 'visbox:')).toBeNull();
    expect(holen).toHaveBeenCalledTimes(1);
    const [weg, init] = holen.mock.calls[0]!;
    expect(weg).toBe(WEG_MODELL_HOLEN);
    expect(init?.method).toBe('POST');
    expect(JSON.parse(String(init?.body))).toEqual({ mappe: 'Hof' });
  });

  it('am Heim-PC im Browser und ohne Namen: nichts zu tun', async () => {
    const holen = vi.fn();
    expect(await holeInDieMappeAmMac('Hof', holen as unknown as typeof fetch, 'https:')).toBeNull();
    expect(await holeInDieMappeAmMac(null, holen as unknown as typeof fetch, 'visbox:')).toBeNull();
    expect(holen).not.toHaveBeenCalled();
  });

  it('ohne Mappe am Mac (404) wie bisher, sonst der Satz der App', async () => {
    const ohne = vi.fn(async () => new Response('{"fehler":"Unbekannter Weg"}', { status: 404 }));
    expect(await holeInDieMappeAmMac('Hof', ohne as unknown as typeof fetch, 'visbox:')).toBeNull();
    const fehlt = vi.fn(async () => new Response('{"fehler":"Das Modell kam nicht an den Mac: x"}', { status: 502 }));
    expect(await holeInDieMappeAmMac('Hof', fehlt as unknown as typeof fetch, 'visbox:')).toBe(
      'Das Modell kam nicht an den Mac: x',
    );
  });

  it('die Palette führt zu «Mappen …», Unbekanntes zur Startansicht', () => {
    expect(zielDerPalette('mappen')).toBe('mappen');
    expect(zielDerPalette('visbox-seite')).toBe('visbox-seite');
    expect(zielDerPalette('anderes')).toBe('startansicht');
  });
});
