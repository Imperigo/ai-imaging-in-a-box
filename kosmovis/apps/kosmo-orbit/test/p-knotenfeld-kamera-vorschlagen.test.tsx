// @vitest-environment jsdom
import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { execute, KosmoDoc, type VisGraph } from '@kosmo/kernel';
import { useProject } from '../src/state/project-store';
import { useVisRuntime } from '../src/modules/vis/vis-runtime';
import { VisWorkspace } from '../src/modules/vis/VisWorkspace';

/**
 * P-KNOTENFELD Posten 9 (`auftraege/von-homestation/auf-orbit-20260825-07.md`
 * Abschnitt 4, Punkt 2: «"Kamera vorschlagen" setzt ungefragt einen Knoten
 * und lässt einen stillen Modus stehen, den Escape nicht beendet»).
 *
 * **Messung vor dem Bau, über den echten Bedienweg** (AUSTAUSCH-Insel-Pille
 * öffnen → echten `island-werkzeug-kamera-vorschlagen`-Knopf klicken —
 * dieselbe `IslandBuehne`/`aufWerkzeugKlick`-Verdrahtung, die `VisWorkspace`
 * produktiv rendert, keine Stub-Nachbildung): Der Klick läuft über
 * `IslandShell.tsx`s `hatPopup:false`-Zweig — Toast zeigen (self-timeout),
 * `kameraVorschlagenAktion()` ausführen, **fertig**. `stufe`/
 * `aktivesWerkzeugId` werden dabei NICHT angefasst (`aufWerkzeugKlick`
 * kehrt für `!w.hatPopup` sofort zurück, VOR jedem `setStufe`/
 * `setAktivesWerkzeugId`) — es gibt kein Popup, kein Fenster, keinen
 * `aria-pressed`-Wechsel, nichts, das Escape beenden müsste.
 *
 * **Gegenprobe, dass diese Fehlerklasse in diesem Insel-Verbund real ist —
 * nur nicht hier:** der UNMITTELBAR benachbarte `hatPopup:false`-Knopf
 * derselben Insel, «Report», hatte GENAU diesen Fehler (P-RAND-Nebenbefund,
 * v0.9.29, Kommentar `VisReportDossier.tsx:48-69`: ein ganzflächiger Scrim
 * ohne Escape, 491 abgefangene Zeiger-Events im Sondenprotokoll) — und ist
 * seither behoben UND regressionsgetestet
 * (`test/vis-ansichten-ui.test.tsx`: «Escape schliesst den Bogen ebenfalls»).
 * Die naheliegendste Erklärung für den Auftragstext: eine Verwechslung der
 * beiden direkt benachbarten AUSTAUSCH-Knöpfe («Kamera vorschlagen» /
 * «Report», `vis-island-katalog.ts` Reihenfolge) im HomeStation-Bericht,
 * nicht ein zweiter, unabhängiger Fund. Für «Kamera vorschlagen» SELBST ist
 * unter dem heutigen Code **nichts** zu reproduzieren — mit echtem
 * Bedienweg gemessen, nicht angenommen.
 *
 * Bleibt als Vertrags-Riegel stehen: ein künftiger Umbau, der
 * `kameraVorschlagenAktion` hinter ein Popup/Fenster/einen Scrim hängt,
 * ohne dafür `useOverlaySchliessen`/Escape zu verdrahten, wird hier rot.
 */

(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;
class StubResizeObserver {
  observe(): void {}
  unobserve(): void {}
  disconnect(): void {}
}
(globalThis as unknown as { ResizeObserver: typeof StubResizeObserver }).ResizeObserver = StubResizeObserver;
if (!('setPointerCapture' in Element.prototype)) {
  Object.assign(Element.prototype, {
    setPointerCapture(): void {},
    releasePointerCapture(): void {},
    hasPointerCapture(): boolean {
      return false;
    },
  });
}

let container: HTMLDivElement | null = null;
let root: Root | null = null;

function q(testid: string): HTMLElement | null {
  return document.body.querySelector(`[data-testid="${testid}"]`);
}

afterEach(() => {
  if (root) {
    act(() => root!.unmount());
    root = null;
  }
  if (container) {
    container.remove();
    container = null;
  }
});

describe('P-KNOTENFELD Posten 9 — "Kamera vorschlagen" hinterlässt keinen stillen Modus (Vertrags-Riegel, mit Gegenprobe)', () => {
  beforeEach(() => {
    const doc = new KosmoDoc();
    const graphId = (execute(doc, 'vis.graphErstellen', { name: 'M9' }).patches[0] as { id: string }).id;
    execute(doc, 'vis.nodeSetzen', { graphId, typ: 'render', x: 400, y: 100 });
    useProject.setState({ doc, journal: [], revision: 0, activeStoreyId: null, selection: [] });
    useVisRuntime.setState({
      aktiverGraphId: graphId,
      aufnahmen: {},
      gespeicherteAnsichten: {},
      reviewPins: {},
      laeufe: {},
    });
  });

  it('Klick über den echten Bedienweg: kein Popup/Fenster, aria-pressed bleibt aus — nur der Kernel-Effekt + ein selbstauflösender Toast', () => {
    container = document.createElement('div');
    document.body.appendChild(container);
    root = createRoot(container);
    act(() => {
      root!.render(<VisWorkspace />);
    });

    const pill = q('island-austausch-pill') as HTMLButtonElement;
    expect(pill, 'AUSTAUSCH-Pille im DOM').not.toBeNull();
    act(() => pill.click());

    const knopf = q('island-werkzeug-kamera-vorschlagen') as HTMLButtonElement;
    expect(knopf, '"Kamera vorschlagen"-Knopf sichtbar').not.toBeNull();

    // VORHER: nichts offen.
    expect(q('island-kamera-vorschlagen-popup')).toBeNull();
    expect(q('island-kamera-vorschlagen-fenster')).toBeNull();
    expect(knopf.getAttribute('aria-pressed')).toBe('false');

    act(() => knopf.click());

    // NACHHER: der Kernel-Effekt lief (Camera-Node + Kante) …
    const graph = useProject.getState().doc.get<VisGraph>(useVisRuntime.getState().aktiverGraphId!)!;
    expect(graph.nodes.some((n) => n.typ === 'kamera')).toBe(true);
    expect(graph.edges).toHaveLength(1);

    // … der Toast bestätigt sichtbar («AKTIV», wie jedes hatPopup:false-Werkzeug) …
    expect(q('island-toast')?.textContent).toBe('KAMERA VORSCHLAGEN AKTIV');

    // … aber NICHTS, das Escape bräuchte: kein Popup, kein Fenster, kein
    // dauerhafter "aktiv"-Zustand des Knopfes selbst.
    expect(q('island-kamera-vorschlagen-popup')).toBeNull();
    expect(q('island-kamera-vorschlagen-fenster')).toBeNull();
    expect(knopf.getAttribute('aria-pressed')).toBe('false');

    // Escape ändert an alledem nichts — es gibt nichts zu schliessen.
    act(() => {
      window.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }));
    });
    expect(q('island-kamera-vorschlagen-popup')).toBeNull();
    expect(knopf.getAttribute('aria-pressed')).toBe('false');
  });

  // Die Gegenprobe, dass diese Fehlerklasse in der AUSTAUSCH-Insel real ist
  // (nur nicht bei diesem Knopf), lebt bewusst NICHT hier verdoppelt — sie
  // ist bereits ein eigener, grüner Test: `vis-ansichten-ui.test.tsx`
  // «VisReportDossier … Escape schliesst den Bogen ebenfalls» (P-RAND,
  // v0.9.29). Siehe Datei-Kopfkommentar oben für den Zusammenhang.
});
