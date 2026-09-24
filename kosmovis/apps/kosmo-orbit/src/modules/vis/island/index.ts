/**
 * PC1 (`docs/V084-SPEZ.md` §5 W2, C-15) — EIN Einstiegspunkt für den
 * Vis-Island-Katalog: `VisWorkspace.tsx` importiert nur diese Datei (Muster
 * `design/island/IslandShell.tsx`s Kopfimporte der vier `inhalte/*.tsx`-
 * Dateien) — die Registrierung der Stufe-2/3-Inhalte läuft als
 * Import-Seiteneffekt, GENAU EINMAL.
 */
export { VIS_INSELN, type VisIslandId } from './vis-island-katalog';
export { visInhaltsRegistry } from './inhalte/registry';

import './inhalte/graph';
import './inhalte/ansicht';
import './inhalte/stimmung';
import './inhalte/austausch';
// v0.8.9 §9 E11 (PBL2, `docs/V089-SPEZ.md`) — SONNE-Insel (Sonnenstunden-
// Client), Registrierung als Import-Seiteneffekt wie die vier Bestands-Inseln.
import './inhalte/sonne';
// v0.8.11 P-B1/E4 (`docs/V0811-SPEZ.md` §2 E4) — die zwei neuen ANSICHT-
// Insel-Inhalte (Gespeicherte Ansichten/Legende), Registrierung als
// Import-Seiteneffekt wie alle übrigen `inhalte/*.tsx`-Dateien.
import './inhalte/ansichten';
import './inhalte/legende';
