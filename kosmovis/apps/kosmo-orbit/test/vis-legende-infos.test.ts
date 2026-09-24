import { describe, expect, it } from 'vitest';
import { VIS_NODE_KATALOG } from '@kosmo/kernel';
import {
  NODE_PARAMETER_INFOS,
  nodeParameterInfos,
  nodeZweck,
} from '../src/modules/vis/island/inhalte/legende-infos';

/**
 * K36 (Owner-Korrekturen 2026-07, S.14: «legende ist gut, erweitere sie an
 * infos und was der jeweilige node alles kann (infos)») — Invarianten der
 * neuen Fähigkeits-Infos (`island/inhalte/legende-infos.ts`) GEGEN den
 * Kernel-Katalog (`VIS_NODE_KATALOG`, `derive/visgraph.ts`, TABU — nur
 * gelesen): kein Node-Typ ohne Info-Eintrag, keine Karteileiche, und die
 * dokumentierten Parameter-Namen sind echte `defaults`-Schlüssel bzw. die
 * zwei im Code belegten Laufzeit-Params des Render-Nodes.
 */

describe('vis-legende-infos — Deckung gegen VIS_NODE_KATALOG (K36)', () => {
  it('JEDER Katalog-Typ hat einen Parameter-Info-Eintrag (ggf. bewusst leer)', () => {
    const katalogTypen = Object.keys(VIS_NODE_KATALOG).sort();
    const infoTypen = Object.keys(NODE_PARAMETER_INFOS).sort();
    expect(infoTypen).toEqual(katalogTypen);
  });

  it('kein Eintrag zeigt auf einen katalogfremden Typ, kein Info-Satz ist leer', () => {
    for (const [typ, infos] of Object.entries(NODE_PARAMETER_INFOS)) {
      expect(VIS_NODE_KATALOG[typ], `Karteileiche: ${typ}`).toBeDefined();
      for (const p of infos) {
        expect(p.name.length, `${typ}.${p.name}`).toBeGreaterThan(0);
        expect(p.info.length, `${typ}.${p.name}`).toBeGreaterThan(0);
      }
    }
  });

  it('dokumentierte Parameter-Namen sind echte defaults-Schlüssel — Ausnahme render: preset/nurCycles (Laufzeit-Params aus evaluiereGraph/vis-jobs.ts)', () => {
    // `evaluiereGraph` (derive/visgraph.ts) liest am Render-Node `params['preset']`
    // + `params['nurCycles']`, obwohl `defaults` leer ist (K20/A10 bzw. HS5) —
    // gesetzt über `vis.nodeParametrieren`. Alle anderen Infos müssen auf
    // einen `defaults`-Schlüssel zeigen.
    const RENDER_LAUFZEIT_PARAMS = ['preset', 'nurCycles'];
    for (const [typ, infos] of Object.entries(NODE_PARAMETER_INFOS)) {
      const defaults = Object.keys(VIS_NODE_KATALOG[typ]!.defaults);
      for (const p of infos) {
        const erlaubt = typ === 'render' ? [...defaults, ...RENDER_LAUFZEIT_PARAMS] : defaults;
        expect(erlaubt, `${typ}.${p.name} ist kein echter Parameter`).toContain(p.name);
      }
    }
  });

  it('nodeParameterInfos(): leer statt undefined für katalogfremde Typen', () => {
    expect(nodeParameterInfos('gibt-es-nicht')).toEqual([]);
    expect(nodeParameterInfos('render').map((p) => p.name)).toEqual(['preset', 'nurCycles']);
  });

  it('nodeZweck(): heute tragen alle 12 Typen eine Katalog-hilfe — der Fallback bleibt ehrlich', () => {
    for (const [typ, k] of Object.entries(VIS_NODE_KATALOG)) {
      expect(k.hilfe.length, typ).toBeGreaterThan(0);
      expect(nodeZweck(typ)).toBe(k.hilfe);
    }
    expect(nodeZweck('gibt-es-nicht')).toBe('Unbekannter Node-Typ — nicht im Katalog.');
  });
});
