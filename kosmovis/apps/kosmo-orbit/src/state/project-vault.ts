/**
 * STELLVERTRETER (Visbox) (Kopfteile, Entscheide 115/116, 20.10.2026) fuer `state/project-vault.ts`
 * von KosmoOrbit (den Projekt-Tresor).
 *
 * Den Tresor gibt es in Visbox nicht: Das Dokument lebt in der Knotenansicht, der Render-Graph wird
 * bei jedem Schritt auf dem Heim-PC gesichert (`apps/visbox-knoten/src/graph-sichern.ts`). Was die
 * woertlichen Kopfteile hier lesen, ist nur die Form der Autosave-Lage — wortgleich.
 */
export interface AutosaveLage {
  readonly stand: 'sichert' | 'gesichert' | 'fehler';
  /** Zeitpunkt des letzten GEGLUECKTEN Speicherns, `null` = noch keins. */
  readonly iso: string | null;
  /** Nur bei `stand: 'fehler'` — der Grund, so wie ihn der Browser nennt. */
  readonly grund?: string;
}

/**
 * KI-Bedienung Stufe 6 (21.10.2026): KosmoBlick nennt die Kennung des offenen Projekts, und die
 * KosmoMaus verwirft beim Projektwechsel offene Karten (`state/kosmo-maus.ts`, woertlich). In Visbox
 * ist das «Projekt» die Mappe in der Knotenansicht; ihre Kennung haelt der Wirt nicht — darum leer.
 * Einen Wechsel meldet der Wirt (`meldeProjektWechsel`), wenn ein neues Dokument geladen wird
 * (`ki-wirt.ts`, `verwirf`), damit die Maus-Karten wie die KI-Karten mitgehen.
 */
export function aktivesProjektId(): string {
  return '';
}

type ProjektWechselHoerer = () => void;
const projektWechselHoerer = new Set<ProjektWechselHoerer>();

/** Wie dort: wer wissen muss, dass das Projekt wechselte. Liefert das Abmelden. */
export function beiProjektWechsel(cb: ProjektWechselHoerer): () => void {
  projektWechselHoerer.add(cb);
  return () => void projektWechselHoerer.delete(cb);
}

/** Visbox: der Wirt meldet ein neues Dokument (andere Mappe). */
export function meldeProjektWechsel(): void {
  for (const cb of [...projektWechselHoerer]) cb();
}
