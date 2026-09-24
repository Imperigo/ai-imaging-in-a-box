import { z } from 'zod';

/**
 * kosmo.bake-job/v1 — Eingabevertrag für einen Textur-Bake (Smart-UV-Unwrap +
 * AO-Bake) auf der HomeStation (v0.8.9 §9 E9, Owner-Shortlist «Bake-
 * Rückweg»). Getrennt vom Simulations-Vertrag (blender-sim.ts), weil hier
 * eine ANDERE, aber genauso harte Ehrlichkeitsgrenze gilt: Bake/Decimate ist
 * eine GEOMETRIE-Klasse mit OPTIMIERUNGS-BEHAUPTUNG — ein unverändertes GLB,
 * das als «gebackt» ausgeliefert wird, behauptet einen Rechenschritt, der nie
 * stattgefunden hat. Anders als ein Platzhalter-BILD (sichtbar markiert) wäre
 * das unsichtbar falsch: die Geometrie sähe exakt so aus wie vorher, nur mit
 * einem Etikett, das eine Optimierung vortäuscht. Darum endet dieser Job im
 * Fake-/Container-Betrieb IMMER auf `kein-blender-worker` — NIE als
 * Pass-Through, der das Eingangs-GLB kommentarlos als `baked_glb`
 * zurückreicht (Sanktion 12, siehe tools/homestation-bridge/kosmo_bridge/
 * main.py `_fake_worker_step`).
 */

export const BakeJobScene = z.object({
  schema: z.literal('kosmo.bake-job/v1').default('kosmo.bake-job/v1'),
  geometry: z.object({
    path: z.string(),
    /**
     * v0.9.42 (Y3-Nachtrag): `ifc` kam dazu, weil der Auftragsbau seit
     * diesem Paket IFC schicken KANN (`bake-auftrag.ts`) — und ein Vertrag,
     * der es dann abweist, macht die neue Faehigkeit unerreichbar. Y3 hat
     * diesen Anschluss selbst gemeldet statt ihn still zu lassen; er lag
     * ausserhalb seines Dateikreises.
     *
     * `glb` bleibt die Vorgabe: der Bestandsweg ist der Normalfall, IFC
     * braucht nur, wer Raeume lesen will (Innenansichten).
     */
    format: z.enum(['glb', 'ifc']).default('glb'),
  }),
  params: z.object({
    textureSize: z.number().int().positive().optional(),
    /** Smart-UV ist die einzig unterstützte Unwrap-Strategie in 0.8.9 —
     * literal statt enum, damit ein künftiger zweiter Wert additiv bleibt. */
    unwrap: z.literal('smart-uv').default('smart-uv'),
    decimateRatio: z.number().min(0).max(1).optional(),
  }),
  out: z.string(),
});
export type BakeJobScene = z.infer<typeof BakeJobScene>;

/** Status wortgleich zu BlenderSimJobStatus — inkl. `kein-blender-worker`,
 * derselben Ehrlichkeitsgrenze wie bei den Simulationen (nur die Behauptung
 * ist hier «optimierte Geometrie/Textur» statt «Physikzahl»). */
export const BakeJobStatus = z.enum([
  'awaiting_approval',
  'queued',
  'running',
  'done',
  'error',
  'cancelled',
  'kein-blender-worker',
]);
export type BakeJobStatus = z.infer<typeof BakeJobStatus>;

/**
 * kosmo.bake-result/v1 — Ergebnis eines Bake-Jobs. `triangles_before`/
 * `triangles_after` sind nur gesetzt, wenn tatsächlich decimiert wurde —
 * ein echter Worker liefert sie, der Fake-Worker liefert das Ergebnis nie
 * (siehe Ehrlichkeitsregel oben).
 */
export const BakeResult = z.object({
  schema: z.literal('kosmo.bake-result/v1').default('kosmo.bake-result/v1'),
  baked_glb: z.string(),
  method: z.string(),
  triangles_before: z.number().int().nonnegative().optional(),
  triangles_after: z.number().int().nonnegative().optional(),
});
export type BakeResult = z.infer<typeof BakeResult>;

export const BakeJob = z.object({
  job_id: z.string().regex(/^bake-\d+-[0-9a-f]{6}$/),
  status: BakeJobStatus,
  kind: z.literal('bake').default('bake'),
  scene: z.string().describe('Pfad zur bake-job.json'),
  /** Freigabe-Token bei aktiver Freigabe-Pflicht (Symmetrie zu RenderJob/
   * BlenderSimJob) — Präfix CONFIRMED_BAKE_. */
  approval_token: z.string().startsWith('CONFIRMED_BAKE_').optional(),
  created_at: z.string(),
  updated_at: z.string().optional(),
  error: z.string().optional(),
  /** Ehrliche Begründung, v. a. bei `kein-blender-worker`. */
  message: z.string().optional(),
  worker: z.string().optional(),
  result: BakeResult.optional(),
});
export type BakeJob = z.infer<typeof BakeJob>;
