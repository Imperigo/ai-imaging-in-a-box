/**
 * STELLVERTRETER für `apps/kosmo-orbit/src/modules/design/splat-render-kontext.ts`
 * (KosmoOrbit, 183 Zeilen).
 *
 * Runde 26 (14.10.2026): Im Original baut diese Datei aus der Splat-Ebene des Projekts den
 * `context` einer Render-Bestellung (Pfad der .ply, Verortung, 4×4-Abbildung). In Visbox
 * gibt es keine Splat-Ebene (s. Stellvertreter `state/splat-ebene.ts`), also nie einen
 * Kontext. `SPLAT_CONTEXT_IM_VERTRAG` und `szeneMitSplatKontext` sind wörtlich — die eine
 * Stelle, die entscheidet, ob ein Kontext mitgeht; `splatRenderKontext` sagt hier nur, dass
 * keine Ebene da ist, mit dem Satz des Originals.
 */
import { RenderScene } from '@kosmo/contracts';

export interface SplatRenderContext {
  kind: 'splat';
  ply: string;
  verortung: string | null;
  /** 4×4 zeilenweise: Translation an den Indizes 3, 7, 11. glTF-Welt (m, y oben) = Welt des model.glb. */
  transform: number[];
  fit: 'behelf' | 'passpunkte';
  crs_note: string;
}

export type SplatRenderKontext = { ok: true; context: SplatRenderContext } | { ok: false; grund: string };

export const SPLAT_CONTEXT_IM_VERTRAG: boolean = 'context' in RenderScene.shape;

export function splatRenderKontext(_zustand: { ebene: null; handLage: unknown }): SplatRenderKontext {
  return { ok: false, grund: 'keine Splat-Ebene im Projekt' };
}

export function szeneMitSplatKontext<T extends object>(
  szene: T,
  kontext: SplatRenderKontext | null,
  imVertrag: boolean = SPLAT_CONTEXT_IM_VERTRAG,
): { szene: T | (T & { context: SplatRenderContext }); hinweis: string | null } {
  if (kontext === null) return { szene, hinweis: null };
  if (!kontext.ok) return { szene, hinweis: kontext.grund };
  if (!imVertrag) {
    return {
      szene,
      hinweis: 'Splat geht noch nicht als Umgebung mit — der Render-Vertrag (render-scene/v1) kennt das Feld «context» noch nicht',
    };
  }
  return { szene: { ...szene, context: kontext.context }, hinweis: null };
}
