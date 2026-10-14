/**
 * STELLVERTRETER für `packages/kosmo-data/src/index.ts` (KosmoOrbit, 10 Zeilen).
 *
 * Runde 26 (14.10.2026): Das Vis-Werkzeug fragt KosmoData nur nach dem Materialkatalog —
 * die Textur-Insel (`textur-material.ts`) und die Texturkacheln (`derive/textur.ts`).
 * Bauteilkatalog, Referenzprojekte, Erfassungsschleife und Detailkatalog bleiben drüben;
 * sie hängen am Architekturkern und an `wissen/`, die nicht mitkommen.
 */
export * from './materialkatalog';
