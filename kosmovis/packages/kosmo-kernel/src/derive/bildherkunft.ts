import type { KosmoDoc } from '../model/doc';
import type { BildHerkunft, ImageAsset, Sheet } from '../model/entities';

/**
 * Strang «Bild aufs Blatt» (Video-Demolauf 20.10.2026, L4-16; Absprache mit KosmoVis 21.10.2026):
 * ein fertiges Rendering liegt zuerst im Projekt (`publish.bildAblegen`) und kommt danach per
 * assetId aufs Blatt. Diese Datei beantwortet die zwei Fragen, die dabei EINE Antwort brauchen:
 * welches Bild ist schon abgelegt, und welches Bild gehoert dem Projekt.
 */

/** Dasselbe Bild desselben Laufs in derselben Guete — gleich, wann es abgelegt wurde. */
export function abgelegtesBild(doc: KosmoDoc, h: { jobId: string; bild: string; guete?: BildHerkunft['guete'] | undefined }): ImageAsset | undefined {
  return doc
    .byKind<ImageAsset>('imageasset')
    .find((a) => a.herkunft && a.herkunft.jobId === h.jobId && a.herkunft.bild === h.bild && (a.herkunft.guete ?? null) === (h.guete ?? null));
}

/** Ein abgelegtes Bild gehoert dem Projekt und wird nicht mit seinem letzten Feld geloescht. */
export function gehoertDemProjekt(asset: ImageAsset | undefined): boolean {
  return !!asset?.herkunft;
}

/**
 * Welches Bild «Blatt füllen» nimmt, wenn das Blatt noch keines traegt. Bis zum 21.10.2026 war es
 * schlicht das zuletzt eingebettete — auch das Büro-Logo oder eine Vorschau. Jetzt:
 * - nie das Büro-Logo, nie ein Bild in Vorschau-Guete;
 * - zuerst eines, das noch auf keinem Blatt steht (ein Bild steht nicht doppelt da, solange es
 *   ein anderes gibt);
 * - unter gleichen das zuletzt abgelegte.
 * Gibt es keines, bleibt der Platzhalter.
 */
export function renderFuerBlatt(doc: KosmoDoc): ImageAsset | undefined {
  const logo = doc.settings.buero?.logoAssetId;
  const kandidaten = doc
    .byKind<ImageAsset>('imageasset')
    .filter((a) => a.id !== logo && a.herkunft?.guete !== 'vorschau');
  const belegt = new Set<string>();
  for (const s of doc.byKind<Sheet>('sheet')) for (const b of s.bilder ?? []) if (b.assetId) belegt.add(b.assetId);
  const frei = kandidaten.filter((a) => !belegt.has(a.id));
  const wahl = frei.length > 0 ? frei : kandidaten;
  return wahl[wahl.length - 1];
}
