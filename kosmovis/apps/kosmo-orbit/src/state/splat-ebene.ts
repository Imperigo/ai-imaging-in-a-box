/**
 * STELLVERTRETER für `apps/kosmo-orbit/src/state/splat-ebene.ts` (KosmoOrbit, 628 Zeilen).
 *
 * Runde 26 (14.10.2026): Das Vis-Werkzeug liest beim Bestellen eines Renders, ob eine
 * sichtbare Splat-Ebene als Umgebung mitreisen soll (`vis-jobs.ts`, lw-splat-context).
 * In Visbox gibt es keine Splat-Ebene im Dokument — die Mappe bringt ihr Modell als glb.
 * Darum ist der Zustand hier fest leer: `ebene` und `handLage` sind `null`, und der Render
 * geht ohne `context` hinaus, wie im Original ohne geladenen Splat.
 */
import { create } from 'zustand';
import type { SplatHandLage } from '@kosmo/kernel';

/** Nur der Teil des Originals, den das Vis-Werkzeug liest. */
export interface SplatEbeneZustand {
  /**
   * Die Splat-Ebene des Projekts — in Visbox nie gesetzt. Runde 29 (14.10.2026): der Typ nennt
   * den Namen, weil «Kamera aus 3D-Ansicht» (`kamera-aus-3d.ts`) ihn nach der Prüfung auf `null`
   * liest; mit `null` allein bliebe dort ein Typ ohne Wert (`never`). Der Wert bleibt `null`.
   */
  ebene: { readonly name: string } | null;
  handLage: { id: string; lage: SplatHandLage } | null;
}

export const useSplatEbene = create<SplatEbeneZustand>(() => ({
  ebene: null,
  handLage: null,
}));
