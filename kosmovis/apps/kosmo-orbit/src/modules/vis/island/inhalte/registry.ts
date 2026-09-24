import { InhaltsRegistry } from '../../../design/island/inhalte/registry';

/**
 * PC1 (`docs/V084-SPEZ.md` §5 W2, C-15/E1) — die vis-Station bekommt eine
 * EIGENE `InhaltsRegistry`-Instanz (Klasse aus `design/island/inhalte/
 * registry.ts`, nur importiert — dieselbe Naht, die PC0 W1 dafür gebaut hat).
 * Eigener Namensraum `'vis'`: Werkzeug-Ids wie `'export'`/`'import'` könnten
 * sonst mit design/AUSTAUSCH kollidieren, sobald eine zweite Station denselben
 * Bestand registriert — mit einer eigenen Instanz ist das strukturell
 * ausgeschlossen (kein globaler Singleton mehr, s. `registry.ts`-Kopfkommentar).
 */
export const visInhaltsRegistry = new InhaltsRegistry('vis');
