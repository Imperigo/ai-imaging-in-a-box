import { KDialog } from '@kosmo/ui';
import type { VorschauKamera } from './modell-vorschau-3d-kern';
import { ModellVorschau3d, type GlbQuelle, type KontextGrenze } from './modell-vorschau-3d';

/**
 * **Grosse Ansicht des 3D-Fensters** (Entscheid 109 A: «Doppelklick gross»). Dasselbe Fenster
 * wie im Knoten, im gemeinsamen Dialog (`KDialog`, Escape und Klick daneben schliessen).
 *
 * Es fragt **mit Vorrang** nach einem Zeichenplatz: sind alle belegt, ruht das älteste kleine
 * Fenster, solange die grosse Ansicht offen ist, und zeichnet danach wieder. Der Doppelklick
 * rahmt hier neu (es gibt nichts Grösseres mehr).
 */
export interface ModellVorschau3dGrossProps {
  readonly glb: GlbQuelle | null;
  readonly kameras?: readonly VorschauKamera[];
  readonly titel?: string;
  readonly onClose: () => void;
  /** Für die Proben. */
  readonly grenze?: KontextGrenze;
}

export const HILFE_3D_GROSS =
  'Ziehen: drehen · Rechte Taste oder Umschalt-Ziehen: schieben · Rad: näher · Doppelklick: neu rahmen';

export function ModellVorschau3dGross({ glb, kameras, titel = 'Modell in 3D', onClose, grenze }: ModellVorschau3dGrossProps) {
  return (
    <KDialog titel={titel} onClose={onClose} breite={1040} data-testid="modell-3d-gross">
      <ModellVorschau3d
        glb={glb}
        {...(kameras !== undefined ? { kameras } : {})}
        {...(grenze !== undefined ? { grenze } : {})}
        vorrang
        className="vis-modell-3d--gross"
        data-testid="modell-3d-gross-fenster"
      />
      <p className="vis-modell-3d-hilfe">{HILFE_3D_GROSS}</p>
    </KDialog>
  );
}
