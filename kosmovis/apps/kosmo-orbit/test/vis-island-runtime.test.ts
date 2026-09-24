import { beforeEach, describe, expect, it } from 'vitest';
import { useVisRuntime } from '../src/modules/vis/vis-runtime';

/**
 * PC1 (`docs/V084-SPEZ.md` §5 W2, C-15) — die additiven Island-UI-Felder in
 * `vis-runtime.ts` (Zoom-Fernauslöser/Snap/Routing/
 * aktiver Graph/Auswahlgrösse/Report/Stimmungs-Preset). Reine Store-Logik,
 * keine NodeCanvas-Abhängigkeit.
 */

beforeEach(() => {
  useVisRuntime.setState({
    aktiverGraphId: null,
    canvasSnapAktiv: true,
    canvasRoutingModus: 'kurve',
    canvasAuswahlGroesse: 0,
    canvasBefehl: null,
    reportOffen: false,
    renderStimmungPreset: null,
  });
});

describe('vis-runtime — PC1 Island-UI-Felder', () => {
  it('aktiverGraphId: Default null, setzbar', () => {
    expect(useVisRuntime.getState().aktiverGraphId).toBeNull();
    useVisRuntime.getState().setAktiverGraphId('vg-1');
    expect(useVisRuntime.getState().aktiverGraphId).toBe('vg-1');
  });

  it('canvasSnapAktiv: Default true (wie das bisherige NodeCanvas-lokale useState), togglebar', () => {
    expect(useVisRuntime.getState().canvasSnapAktiv).toBe(true);
    useVisRuntime.getState().toggleCanvasSnap();
    expect(useVisRuntime.getState().canvasSnapAktiv).toBe(false);
    useVisRuntime.getState().toggleCanvasSnap();
    expect(useVisRuntime.getState().canvasSnapAktiv).toBe(true);
  });

  it('canvasRoutingModus: Default "kurve", togglebar zwischen ortho/kurve', () => {
    expect(useVisRuntime.getState().canvasRoutingModus).toBe('kurve');
    useVisRuntime.getState().toggleCanvasRouting();
    expect(useVisRuntime.getState().canvasRoutingModus).toBe('ortho');
    useVisRuntime.getState().toggleCanvasRouting();
    expect(useVisRuntime.getState().canvasRoutingModus).toBe('kurve');
  });

  // K35 (Owner-Korrekturen 2026-07, S.14): `canvasMinimapManuell` ist mitsamt
  // der Minimap aus `vis-runtime.ts` entfernt — der frühere Testfall dazu
  // entfällt mit dem Feld.

  it('canvasAuswahlGroesse: reiner Zähler, setzbar', () => {
    useVisRuntime.getState().setCanvasAuswahlGroesse(3);
    expect(useVisRuntime.getState().canvasAuswahlGroesse).toBe(3);
  });

  it('canvasBefehl: sendeCanvasBefehl erhöht die Nonce bei JEDEM Aufruf, auch bei identischem Typ hintereinander', () => {
    expect(useVisRuntime.getState().canvasBefehl).toBeNull();
    useVisRuntime.getState().sendeCanvasBefehl('zoom-in');
    const erster = useVisRuntime.getState().canvasBefehl;
    expect(erster?.typ).toBe('zoom-in');
    expect(erster?.nonce).toBe(1);
    useVisRuntime.getState().sendeCanvasBefehl('zoom-in');
    const zweiter = useVisRuntime.getState().canvasBefehl;
    // NEUES Objekt UND höhere Nonce — ein Effekt mit `[canvasBefehl]`-Deps
    // (Objekt-Referenz-Vergleich) feuert darum bei jedem Klick erneut.
    expect(zweiter).not.toBe(erster);
    expect(zweiter?.nonce).toBe(2);
  });

  it('reportOffen: Default false, setzbar (unabhängig vom Manuell-Modus-useState in VisWorkspace.tsx)', () => {
    expect(useVisRuntime.getState().reportOffen).toBe(false);
    useVisRuntime.getState().setReportOffen(true);
    expect(useVisRuntime.getState().reportOffen).toBe(true);
  });

  it('renderStimmungPreset: Default null (kein environment-Feld im Job ohne Auswahl), setzbar auf morgen/abend/weiss', () => {
    expect(useVisRuntime.getState().renderStimmungPreset).toBeNull();
    useVisRuntime.getState().setRenderStimmungPreset('abend');
    expect(useVisRuntime.getState().renderStimmungPreset).toBe('abend');
    useVisRuntime.getState().setRenderStimmungPreset(null);
    expect(useVisRuntime.getState().renderStimmungPreset).toBeNull();
  });
});
