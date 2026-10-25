// @vitest-environment jsdom
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { History, KosmoDoc } from '@kosmo/kernel';
import { useProject } from '../../kosmo-orbit/src/state/project-store';
import { modellStand } from '../../kosmo-orbit/src/modules/vis/grundlage';
import {
  ladeMappe,
  nimmFertigesLadenAn,
  SATZ_NICHT_IN_DER_MAPPE_AM_MAC,
  verfolge,
  zustandNachDemHolen,
  type LadeStand,
  type MappeAntwort,
} from '../src/mappe';

/**
 * Befund «Andere Datei» (Mac-Probe Visbox 0.3.67, Mappe «haus-am-hang», 25.10.2026): «Andere Datei …» in
 * einer BESTEHENDEN Mappe am Mac ersetzte das Modell nicht. Am Heim-PC kam die neue Fassung an (38 Bauteile),
 * am Knoten stand diese Zahl — aus dem Stand des Heim-PC —, aber `modell.glb` und `mappe.json` am Mac blieben
 * beim alten Stand (30). Die Seite las jede 404 der App als «keine Mappe am Mac» und meldete nichts.
 *
 * Hier spielt eine kleine Mac-App mit: eine Mappe am Mac (`./mappe` aus «mappe.json»), die auf
 * `./mappe-holen` das Modell übernimmt — oder es, wie im Befund, nicht tut.
 */
const HUELLE_ALT: MappeAntwort['huellbox_m'] = [[0, 0, 0], [12, 8, 7]];
const HUELLE_NEU: MappeAntwort['huellbox_m'] = [[0, 0, 0], [14, 9, 7.5]];

interface Macmappe {
  heimMappe: string | null;
  bauteile: number;
  fassung: number;
  huelle: MappeAntwort['huellbox_m'];
}

function antwort(m: Macmappe): MappeAntwort {
  return {
    name: 'haus-am-hang', mappe: 'haus-am-hang', glb: true, huellbox_m: m.huelle, hochachse: 'z', grund: '',
    huellbox_vermerk: '', herkunft: 'IFC', bauteile: m.bauteile, fassung: m.fassung, am_mac: true,
    heim_mappe: m.heimMappe,
  };
}

/** Die Mac-App: `holt` sagt, was sie auf `./mappe-holen` tut. */
function macApp(m: Macmappe, holt: 'uebernimmt' | '404' | 'still') {
  const anfragen: string[] = [];
  const holen = vi.fn(async (eingabe: RequestInfo | URL, init?: RequestInit) => {
    const weg = String(eingabe);
    anfragen.push(`${init?.method ?? 'GET'} ${weg}`);
    if (weg.startsWith('./mappe-holen')) {
      if (holt === '404') return new Response('{"fehler":"Keine Mappe am Mac offen."}', { status: 404 });
      if (holt === 'uebernimmt') {
        const { mappe } = JSON.parse(String(init?.body)) as { mappe: string };
        Object.assign(m, { heimMappe: mappe, bauteile: 38, fassung: 2, huelle: HUELLE_NEU });
      }
      return new Response(JSON.stringify({ mappe: 'haus-am-hang' }), { status: 200 });
    }
    if (weg.startsWith('./mappe')) return new Response(JSON.stringify(antwort(m)), { status: 200 });
    if (weg.startsWith('./modell.glb')) return new Response(new ArrayBuffer(8), { status: 200 });
    return new Response('{}', { status: 200 });
  });
  return { holen, anfragen };
}

/** Der Stand des Heim-PC, als die neue Fassung im Zwilling fertig war (aus `_lade_modell_im_hintergrund`). */
const FERTIG: LadeStand = {
  kennung: 'k38', stand: 'geladen', datei: 'haus-am-hang.ifc', satz: 'Neue Fassung 2 in der Mappe «haus-am-hang»',
  schritt: null, seit_s: 4, mappe: 'haus-am-hang', herkunft: 'IFC', fassung: 2, bauteile: 38, ersetzt: true,
  am_mac: 'haus-am-hang',
};

let ursprung: PropertyDescriptor | undefined;

beforeEach(() => {
  useProject.setState({ doc: new KosmoDoc(), history: new History(), revision: 0 } as never);
  ursprung = Object.getOwnPropertyDescriptor(window, 'location');
  // Die Seite läuft in der Mac-App: eigenes Adressschema.
  Object.defineProperty(window, 'location', {
    configurable: true,
    value: { ...window.location, protocol: 'visbox:', search: '', pathname: '/knoten/', href: 'visbox://app/knoten/' },
  });
});

afterEach(() => {
  if (ursprung) Object.defineProperty(window, 'location', ursprung);
  vi.unstubAllGlobals();
});

describe('«Andere Datei …» in einer bestehenden Mappe am Mac (Befund 0.3.67)', () => {
  it('die Mac-App übernimmt: der Knoten zeigt die Zahl AUS DER MAPPE AM MAC, und die Grundlage veraltet', async () => {
    const m: Macmappe = { heimMappe: 'haus-am-hang', bauteile: 30, fassung: 1, huelle: HUELLE_ALT };
    const { holen, anfragen } = macApp(m, 'uebernimmt');
    vi.stubGlobal('fetch', holen);
    await ladeMappe();
    const standVorher = modellStand(useProject.getState().doc);
    const ende = await verfolge(FERTIG, () => {});
    expect(anfragen).toContain('POST ./mappe-holen');
    expect(ende).toMatchObject({ stand: 'geladen', bauteile: 38, fassung: 2, mappe: 'haus-am-hang' });
    // Ein neues Modell ist ein neuer Modellstand — die Grundlage am Render-Knoten heisst danach «veraltet».
    expect(modellStand(useProject.getState().doc)).not.toBe(standVorher);
  });

  it('die App antwortet 404, obwohl das Laden aus der Mappe am Mac kam: Fehler mit Satz statt «38 Bauteile»', async () => {
    const m: Macmappe = { heimMappe: 'haus-am-hang', bauteile: 30, fassung: 1, huelle: HUELLE_ALT };
    vi.stubGlobal('fetch', macApp(m, '404').holen);
    await ladeMappe();
    const ende = await verfolge(FERTIG, () => {});
    expect(ende.stand).toBe('fehler');
    expect(ende.stand === 'fehler' && ende.satz).toContain(SATZ_NICHT_IN_DER_MAPPE_AM_MAC);
  });

  it('die App sagt «fertig», die Mappe am Mac hat aber weiter 30: Fehler, das alte Modell gilt weiter', async () => {
    const m: Macmappe = { heimMappe: 'haus-am-hang', bauteile: 30, fassung: 1, huelle: HUELLE_ALT };
    vi.stubGlobal('fetch', macApp(m, 'still').holen);
    await ladeMappe();
    const ende = await verfolge(FERTIG, () => {});
    expect(ende).toMatchObject({ stand: 'fehler', noch: { bauteile: 30 } });
    expect(ende.stand === 'fehler' && ende.satz).toContain('Am Heim-PC 38 Bauteile, in der Mappe am Mac weiter 30');
  });

  it('ein anderer Zwilling (der Heim-PC legte «haus-am-hang-2» an): erst übernommen, wenn die Mappe am Mac ihn nennt', () => {
    const neu = { ...FERTIG, mappe: 'haus-am-hang-2', fassung: 1 };
    const alt = antwort({ heimMappe: 'haus-am-hang', bauteile: 38, fassung: 1, huelle: HUELLE_NEU });
    expect(zustandNachDemHolen(neu, alt).stand).toBe('fehler');
    expect(zustandNachDemHolen(neu, { ...alt, heim_mappe: 'haus-am-hang-2' }).stand).toBe('geladen');
  });

  it('beim Öffnen: ein fertiges Laden dieser Mappe am Mac, das nicht ankam, wird nachgeholt — einmal', async () => {
    const m: Macmappe = { heimMappe: 'haus-am-hang', bauteile: 30, fassung: 1, huelle: HUELLE_ALT };
    const { holen, anfragen } = macApp(m, 'uebernimmt');
    vi.stubGlobal('fetch', holen);
    await ladeMappe();
    const zustand = await nimmFertigesLadenAn(FERTIG, holen as unknown as typeof fetch);
    expect(zustand).toMatchObject({ stand: 'geladen', bauteile: 38 });
    expect(anfragen.filter((a) => a === 'POST ./mappe-holen')).toHaveLength(1);
    // Schon da: nichts mehr zu tun.
    expect(await nimmFertigesLadenAn(FERTIG, holen as unknown as typeof fetch)).toBeNull();
    expect(anfragen.filter((a) => a === 'POST ./mappe-holen')).toHaveLength(1);
  });

  it('beim Öffnen: ein Laden einer ANDEREN Mappe am Mac oder ohne Mappe am Mac wird nicht angefasst', async () => {
    const m: Macmappe = { heimMappe: 'haus-am-hang', bauteile: 30, fassung: 1, huelle: HUELLE_ALT };
    const { holen, anfragen } = macApp(m, 'uebernimmt');
    vi.stubGlobal('fetch', holen);
    await ladeMappe();
    expect(await nimmFertigesLadenAn({ ...FERTIG, am_mac: 'anderes-haus' }, holen as unknown as typeof fetch)).toBeNull();
    const ohneMac: LadeStand = { ...FERTIG };
    delete ohneMac.am_mac;
    expect(await nimmFertigesLadenAn(ohneMac, holen as unknown as typeof fetch)).toBeNull();
    expect(await nimmFertigesLadenAn({ ...FERTIG, stand: 'laeuft' }, holen as unknown as typeof fetch)).toBeNull();
    expect(anfragen).not.toContain('POST ./mappe-holen');
  });
});
