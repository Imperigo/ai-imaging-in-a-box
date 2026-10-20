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
