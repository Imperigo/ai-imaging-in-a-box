/**
 * STELLVERTRETER für `packages/kosmo-ai` (KosmoOrbit). Das Vis-Werkzeug braucht davon nur die
 * Vorgabeadresse der Brücke (`vis-jobs.ts`, `GpuStatus.tsx`). Wörtlich aus
 * `packages/kosmo-ai/src/betrieb.ts` im Original.
 */
export const STANDARD_BRIDGE_URL = 'http://localhost:8600';

/**
 * KI-Bedienung Stufe 6 (21.10.2026): `state/kosmo-maus.ts` (woertlich) liefert seine zwei Werkzeuge
 * fuer Kosmos Chat als `ReadTool[]` (`kosmoMausReadTools`). In Visbox ruft sie niemand so — der
 * Assistent geht ueber die Mac-App —, der Typ muss aber da sein. Form wie `chat.ts` im Original.
 */
export interface ToolDefinition {
  name: string;
  description: string;
  parameters: unknown;
}
export interface ReadTool extends ToolDefinition {
  execute(args: unknown): string | Promise<string>;
}
