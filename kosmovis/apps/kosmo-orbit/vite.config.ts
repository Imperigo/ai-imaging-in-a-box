/**
 * STELLVERTRETER (Visbox) (KI-Bedienung Stufe 6, 21.10.2026) fuer `apps/kosmo-orbit/vite.config.ts`
 * von KosmoOrbit.
 *
 * In Visbox baut die Wirtsseite (`apps/visbox-knoten`), nicht diese App — die Datei baut nichts. Sie
 * steht da, weil `tsconfig.json` (woertlich) sie einschliesst und weil sie dort die Node-Typen in die
 * Typpruefung bringt: `shell/zeiger-bilder.ts` (woertlich) nennt `Buffer` als Rueckfall ohne `btoa`.
 */
/// <reference types="node" />
export default {};
