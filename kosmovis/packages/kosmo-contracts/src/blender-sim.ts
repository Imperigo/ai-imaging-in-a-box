import { z } from 'zod';

/**
 * kosmo.blender-sim/v1 — Eingabevertrag für eine Blender-Simulation auf der
 * HomeStation (Wind / Sonnenstunden / Gebäude-Energie). Getrennt vom
 * Render-Vertrag, weil hier eine HARTE Ehrlichkeitsgrenze gilt: ein
 * Platzhalter-BILD ist sichtbar ein Platzhalter (markiert), eine
 * Platzhalter-SIMULATIONSZAHL sähe aus wie ein Analyseergebnis und könnte
 * eine Bau-Entscheidung verseuchen. Darum wird Physik NIE gefakt — ohne
 * Blender-Worker endet der Job beweisbar als `kein-blender-worker`
 * (siehe `BlenderSimJobStatus` + tools/homestation-bridge).
 */

export const BlenderSimArt = z.enum(['wind', 'sonnenstunden', 'gebaeude-energie']);
export type BlenderSimArt = z.infer<typeof BlenderSimArt>;

export const BlenderSimScene = z.object({
  schema: z.literal('kosmo.blender-sim/v1').default('kosmo.blender-sim/v1'),
  art: BlenderSimArt,
  geometry: z.object({
    path: z.string(),
    format: z.literal('glb').default('glb'),
  }),
  /** Art-spezifische Parameter (z. B. Windrichtung, Datum/Ort). Generisch,
   * damit neue Simulationsarten ohne Schema-Bruch andocken.
   *
   * Schlüssel für `art: 'sonnenstunden'` (v0.8.9 §9 E9/E11, Sampling-
   * Konvention siehe README «Sonnenstunden»):
   *   lat: number               — Breitengrad (WGS84).
   *   lon: number                — Längengrad (WGS84).
   *   datum: string              — ISO-Datum (z. B. "2026-12-21"), kein
   *                                 Doc-Feld (Laufzeit ≠ Modell, PA2-Grenze).
   *   kriteriumStunden?: number  — Schwellwert für `kriteriumErfuellt` im
   *                                 Ergebnis; optional, Default 3.
   */
  params: z.record(z.string(), z.unknown()).default({}),
  out: z.string(),
});
export type BlenderSimScene = z.infer<typeof BlenderSimScene>;

/**
 * kosmo.sonnenstunden-result/v1 — Ergebnis einer Sonnenstunden-Simulation
 * (art: 'sonnenstunden'). Additiv zu BlenderSimJob.result, analog dem
 * render-result-Einbettungsmuster von RenderJob. Wie bei jeder Blender-
 * Simulation gilt die harte Ehrlichkeitsgrenze dieser Datei: dieses Ergebnis
 * existiert NUR nach einem echten Blender-Worker-Lauf — der Fake-Worker
 * erzeugt es nie (er endet auf `kein-blender-worker`).
 */
export const SonnenstundenResult = z.object({
  schema: z.literal('kosmo.sonnenstunden-result/v1').default('kosmo.sonnenstunden-result/v1'),
  stunden: z.number(),
  kriteriumErfuellt: z.boolean(),
  methode: z.string(),
});
export type SonnenstundenResult = z.infer<typeof SonnenstundenResult>;

/**
 * Job-Record der Blender-Simulation. Eigenes Präfix `bsim-` (die `vis-`-Regex
 * von RenderJob bleibt unangetastet). `kein-blender-worker` ist die ehrliche
 * Grenze im Container/ohne HomeStation — kein vorgetäuschtes Ergebnis.
 */
export const BlenderSimJobStatus = z.enum([
  // `awaiting_approval` (additiv, HS3-Nachbesserung/Fable-Auflage 4): auch eine
  // Blender-Simulation ist teuer — bei aktiver Freigabe-Pflicht wartet sie auf
  // ein explizites /approve, bevor ein echter Worker sie rechnet.
  'awaiting_approval',
  'queued',
  'running',
  'done',
  'error',
  'cancelled',
  'kein-blender-worker',
]);
export type BlenderSimJobStatus = z.infer<typeof BlenderSimJobStatus>;

export const BlenderSimJob = z.object({
  job_id: z.string().regex(/^bsim-\d+-[0-9a-f]{6}$/),
  status: BlenderSimJobStatus,
  /** Job-Art-Marker; der Fake-Worker dispatcht über `kind` (Symmetrie zu
   * VideoSplatJob, Fable-Review-1). */
  kind: z.literal('blender-sim').default('blender-sim'),
  art: BlenderSimArt,
  scene: z.string().describe('Pfad zur blender-sim.json'),
  /** Freigabe-Token bei aktiver Freigabe-Pflicht (Symmetrie zu RenderJob). */
  approval_token: z.string().optional(),
  created_at: z.string(),
  updated_at: z.string().optional(),
  error: z.string().optional(),
  /** Ehrliche Begründung, v. a. bei `kein-blender-worker`. */
  message: z.string().optional(),
  worker: z.string().optional(),
  /** Das eingebettete Ergebnis, sobald `done` — nur für `art:
   * 'sonnenstunden'` befüllt (weitere Arten bekommen ihr eigenes Result-
   * Schema erst, wenn sie es brauchen). Ohne dieses Feld würde
   * `BlenderSimJob.parse()` es stumm strippen (Fable-Review-1-Muster). */
  result: SonnenstundenResult.optional(),
});
export type BlenderSimJob = z.infer<typeof BlenderSimJob>;
