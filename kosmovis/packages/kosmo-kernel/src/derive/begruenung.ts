/**
 * STELLVERTRETER für `packages/kosmo-kernel/src/derive/begruenung.ts` (KosmoOrbit) — nur,
 * was `model/entities.ts` zum Übersetzen braucht. Wörtlich aus dem Original.
 */
export const BLUETEN_ARTEN = ['rot', 'gelb', 'violett', 'orangerot', 'weiss', 'rosa'] as const;
export type BluetenArt = (typeof BLUETEN_ARTEN)[number];
