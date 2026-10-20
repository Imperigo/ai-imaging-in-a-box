/**
 * STELLVERTRETER (Visbox) (Kopfteile, Entscheide 115/116, 20.10.2026) fuer `state/kopplung.ts` von
 * KosmoOrbit (Kopplung mit dem Sync-Server).
 *
 * Die Zweitgruppe (`InselKopf.tsx`, woertlich) liest hier den Text des Sync-Chips. In Visbox steht
 * an seiner Stelle der Heim-PC-Chip (`chip`), der Text wird darum nie gezeigt. `syncChipText` und
 * `WaechterLage` stehen hier wortgleich, damit die Datei aufgeht.
 */
import type { SyncStatus } from './project-sync';

export type WaechterLage = 'ruht' | 'angeboten';

/** Text des bestehenden Sync-Chips — wortgleich wie dort. */
export function syncChipText(status: SyncStatus, peers: number, lage: WaechterLage): string {
  switch (status) {
    case 'live':
      return `Sync live · ${peers}`;
    case 'aus':
      return lage === 'angeboten' ? 'Sync aus · bereit' : 'Sync aus';
    case 'verbinde':
      return 'Sync verbindet …';
    case 'getrennt':
      return 'Sync getrennt · verbindet neu';
    case 'abgelehnt':
      return 'Sync abgelehnt · Token prüfen';
  }
}
