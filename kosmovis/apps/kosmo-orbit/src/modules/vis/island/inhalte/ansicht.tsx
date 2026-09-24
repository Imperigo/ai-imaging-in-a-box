import { KButton, KIcon } from '@kosmo/ui';
import { useVisRuntime } from '../../vis-runtime';
import { visInhaltsRegistry } from './registry';
import '../vis-island.css';

/**
 * ANSICHT-Insel (PC1, `docs/V084-SPEZ.md` §5 W2, C-15) — Zoom/Fit als
 * Stufe-2-Popup (Raster-Snap/Routing sind `hatPopup:false`-Sofort-Toggles,
 * s. `vis-island-katalog.ts`, kein Registry-Eintrag nötig). Das Popup ist
 * ein reiner Fernauslöser (`sendeCanvasBefehl`) — die eigentliche Rechnung/
 * Darstellung bleibt in `NodeCanvas.tsx` (s. dortiger Kommentar zu
 * `canvasBefehl`).
 *
 * K35 (Owner-Korrekturen 2026-07, S.14 «diese übersicht raus, die bringt
 * nichts»): das «Minimap»-Werkzeug (`MinimapStufe2`, Registry-Eintrag
 * 'minimap') ist mitsamt der Minimap ERSATZLOS entfernt.
 */

function ZoomStufe2() {
  const sendeCanvasBefehl = useVisRuntime((s) => s.sendeCanvasBefehl);
  return (
    <div className="visisl-stufe2" data-testid="island-zoom-stufe2" onClick={(e) => e.stopPropagation()}>
      <div className="visisl-reihe">
        <KButton size="touch" tone="ghost" data-testid="island-zoom-minus" title="Kleiner" onClick={() => sendeCanvasBefehl('zoom-out')}>
          <KIcon name="zoom-minus" size={16} title="Kleiner" />
        </KButton>
        <KButton size="touch" tone="ghost" data-testid="island-zoom-fit" title="Einpassen" onClick={() => sendeCanvasBefehl('zoom-fit')}>
          <KIcon name="fit" size={16} title="Einpassen" />
        </KButton>
        <KButton size="touch" tone="ghost" data-testid="island-zoom-plus" title="Grösser" onClick={() => sendeCanvasBefehl('zoom-in')}>
          <KIcon name="zoom-plus" size={16} title="Grösser" />
        </KButton>
      </div>
    </div>
  );
}

visInhaltsRegistry.registriere('zoom', { Stufe2: ZoomStufe2, Stufe3: ZoomStufe2 });
