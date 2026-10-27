// @vitest-environment jsdom
import { afterEach, describe, expect, it } from 'vitest';
import { klickVollUrteil } from '../../kosmo-orbit/src/modules/vis/vis-jobs';
import { setzeCoopZurueck, setzeModusVonApp } from '../../kosmo-orbit/src/state/kosmo-coop';
import { haengeVollAn, klickUrteil } from '../src/voll-render';

/**
 * Entscheid 155 (Owner über die Zentrale, 27.10.2026): in «Voll» ist der Klick des Architekten in der Knotenansicht
 * die Freigabe. Die Visbox meldet dafür den Wirt an (`voll-render.ts`): in «Voll» frei, ausser ein Bildmodell mit
 * offener Lizenz ohne Skizze (E153); die Grenze von 5 je Stunde setzt der Heim-PC durch (der Auftrag wartet dann mit
 * seinem Satz). Ausserhalb von «Voll» kein Urteil — alles wie bisher. Gegen den alten Stand rot: es gab keinen Wirt.
 */

let ab: () => void = () => undefined;
afterEach(() => {
  ab();
  ab = () => undefined;
  setzeCoopZurueck();
});

describe('E155 — der Klick in «Voll»', () => {
  it('frei in «Voll»; ausserhalb kein Urteil (wie bisher)', () => {
    expect(klickUrteil({ backbone: 'z-image-turbo', mitSkizze: false }, 'voll')).toEqual({ frei: true });
    expect(klickUrteil({ backbone: null, mitSkizze: false }, 'voll'), 'Grundlage rendern (nur Blender)').toEqual({ frei: true });
    expect(klickUrteil({ backbone: 'z-image-turbo', mitSkizze: false }, 'coop')).toBeNull();
    expect(klickUrteil({ backbone: 'z-image-turbo', mitSkizze: false }, 'karte')).toBeNull();
  });

  it('Qwen-Image ohne Skizze bleibt beim «Freigeben»; aus einer Skizze frei (E153)', () => {
    const u = klickUrteil({ backbone: 'qwen-image-2.1', mitSkizze: false }, 'voll');
    expect(u && u.frei === false && u.grund).toContain('qwen-image-2.1');
    expect(klickUrteil({ backbone: 'qwen-image-2.1', mitSkizze: true }, 'voll')).toEqual({ frei: true });
    expect(klickUrteil({ backbone: 'flux-krea', mitSkizze: true }, 'voll')?.frei).toBe(false);
  });

  it('der Wirt ist am Werkzeug angemeldet und folgt dem Modus der App', () => {
    ab = haengeVollAn();
    setzeModusVonApp('voll');
    expect(klickVollUrteil({ backbone: 'z-image-turbo', mitSkizze: false })).toEqual({ frei: true });
    setzeModusVonApp('coop');
    expect(klickVollUrteil({ backbone: 'z-image-turbo', mitSkizze: false })).toBeNull();
    ab();
    ab = () => undefined;
    setzeModusVonApp('voll');
    expect(klickVollUrteil({ backbone: 'z-image-turbo', mitSkizze: false }), 'ohne Wirt: kein Urteil').toBeNull();
  });
});
