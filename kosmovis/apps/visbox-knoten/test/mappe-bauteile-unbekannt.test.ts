import { describe, expect, it } from 'vitest';
import { zustandAusMappe, type MappeAntwort } from '../src/mappe';
import { szeneZeile } from '../../kosmo-orbit/src/modules/vis/modell-laden';

/**
 * A0261 (G-A0063b Runde 2, Befund 1): Weiss die Mappe die Bauteilzahl nicht (`bauteile: null`, die
 * glb war nicht lesbar), sagt der Modell-Knoten «unbekannt» — nie «0 Bauteile», das wie eine leere
 * Szene aussieht und eine Zahl behauptet, die niemand gerechnet hat.
 */
const antwort = (teile: number | null): MappeAntwort =>
  ({ glb: true, bauteile: teile, herkunft: 'IFC', mappe: 'haus-am-hang' }) as unknown as MappeAntwort;

describe('Bauteile unbekannt statt 0', () => {
  it('bauteile null: die Zeile heisst «Szene: Bauteile unbekannt»', () => {
    const z = zustandAusMappe(antwort(null));
    if (z.stand !== 'geladen') throw new Error('geladen erwartet');
    expect(z.bauteile).toBeNull();
    expect(szeneZeile(z.bauteile, z.herkunft)).toContain('Szene: Bauteile unbekannt');
    expect(szeneZeile(z.bauteile, z.herkunft)).not.toMatch(/\b0 Bauteile/);
  });

  it('eine echte Zahl bleibt, auch die Null einer wirklich leeren Szene', () => {
    const z38 = zustandAusMappe(antwort(38));
    const z0 = zustandAusMappe(antwort(0));
    if (z38.stand !== 'geladen' || z0.stand !== 'geladen') throw new Error('geladen erwartet');
    expect(szeneZeile(z38.bauteile, z38.herkunft)).toBe('Szene: 38 Bauteile (aus IFC)');
    expect(z0.bauteile).toBe(0);
  });
});
