import { describe, expect, it } from 'vitest';
import { VIS_WERKZEUG_KATALOG } from '../src/modules/vis/island/vis-island-katalog';
// Import-Seiteneffekt: registriert alle Stufe-2/3-Inhalte (Muster
// `design/island/IslandShell.tsx`s Kopfimporte der vier `inhalte/*.tsx`).
import { visInhaltsRegistry } from '../src/modules/vis/island';

/**
 * PC1 (`docs/V084-SPEZ.md` §5 W2, C-15) — jedes `hatPopup:true`-Werkzeug MUSS
 * einen echten Registry-Inhalt haben (sonst zeigt IslandShell nur den PD1-
 * Leerrahmen) — dasselbe Gate wie design's `registrierteWerkzeugIds()`-Test
 * («kein Werkzeug endet bei Stufe 1»), hier für den eigenen `'vis'`-
 * Namensraum.
 */

describe('vis-island — Registry (eigener Namensraum "vis")', () => {
  it('jedes hatPopup:true-Werkzeug hat einen registrierten Stufe2-Inhalt', () => {
    for (const w of VIS_WERKZEUG_KATALOG.filter((x) => x.hatPopup)) {
      const inhalt = visInhaltsRegistry.inhaltFuer(w.id);
      expect(inhalt?.Stufe2, `Werkzeug "${w.id}" hat keinen Stufe2-Inhalt`).toBeDefined();
    }
  });

  it('registrierteIds() deckt exakt die 10 hatPopup:true-Werkzeuge (v0.8.11 P-B1/E4: +ansichten/+legende, keine Karteileiche, kein Fehlender)', () => {
    const erwartete = VIS_WERKZEUG_KATALOG.filter((x) => x.hatPopup)
      .map((w) => w.id)
      .sort();
    expect(visInhaltsRegistry.registrierteIds().slice().sort()).toEqual(erwartete);
  });

  it('hatPopup:false-Werkzeuge sind NICHT registriert (ihre Aktion läuft über onWerkzeugAktion, kein Popup)', () => {
    // v0.8.10 E3-Nachtrag: 'manuell' ist kein Katalog-Werkzeug mehr (raus aus
    // dieser Liste) — der Zugang läuft über den Einstellungs-Schalter.
    for (const id of ['raster', 'routing', 'kamera-vorschlagen', 'report']) {
      expect(visInhaltsRegistry.inhaltFuer(id)).toBeUndefined();
    }
  });

  it('doppelte Registrierung wirft (Programmierfehler-Schutz, Muster design InhaltsRegistry)', () => {
    expect(() => visInhaltsRegistry.registriere('palette', {})).toThrow();
  });
});
