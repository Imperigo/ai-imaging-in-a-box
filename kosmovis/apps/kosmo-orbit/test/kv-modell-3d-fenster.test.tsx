// @vitest-environment jsdom
import { readdirSync, readFileSync, statSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { act, type ReactNode } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import type { ModellVorschau3d as KernFenster } from '../src/modules/vis/modell-vorschau-3d-kern';
import {
  ANGEHALTENE_EREIGNISSE,
  HOECHSTENS_KONTEXTE,
  KontextGrenze,
  ModellVorschau3d,
  SAETZE_3D,
  halteEingabenAn,
  type ModellVorschau3dProps,
} from '../src/modules/vis/modell-vorschau-3d';
import { HILFE_3D_GROSS, ModellVorschau3dGross } from '../src/modules/vis/modell-vorschau-3d-gross';

/**
 * Kleines 3D-Fenster, die Hülle (Bauplan «Neue Knoten» 20.10.2026; Entscheid 109 A: klein fest
 * im Modell-Knoten, Doppelklick gross). Noch ohne Einbau in den Modell-Knoten — der kommt mit F1.
 *
 * Geprüft: Rückfall-Satz ohne WebGL (mit dem echten Kern), Kontextgrenze (rein und an der
 * Hülle), Anhalten ausserhalb des Bildschirms, Eingaben bleiben im Fenster, Doppelklick, grosse
 * Ansicht — und dass der Kern nur über `import()` geladen wird (eigener Teil des Baus).
 */

(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

const HIER = path.dirname(fileURLToPath(import.meta.url));
const GLB = new ArrayBuffer(8);

type KernModul = typeof import('../src/modules/vis/modell-vorschau-3d-kern');

interface Attrappe extends KernFenster {
  readonly aufrufe: string[];
}

function attrappe(): Attrappe {
  const aufrufe: string[] = [];
  const merke = (n: string) => () => {
    aufrufe.push(n);
  };
  return {
    aufrufe,
    ladeGlb: () => {
      aufrufe.push('ladeGlb');
      return Promise.resolve();
    },
    setzeKameras: merke('setzeKameras'),
    setzeGroesse: merke('setzeGroesse'),
    setzePixeldichte: merke('setzePixeldichte'),
    zoome: (f: number) => {
      aufrufe.push(`zoome:${f.toFixed(2)}`);
    },
    rahmen: merke('rahmen'),
    ansicht: () => ({ position: [1, 2, 3], target: [0, 0, 0], near: 0.1, far: 100 }),
    setzeAnsicht: merke('setzeAnsicht'),
    blickvorschau: () => null,
    pausiere: merke('pausiere'),
    fortsetzen: merke('fortsetzen'),
    zeichne: merke('zeichne'),
    dispose: merke('dispose'),
  };
}

/** Kern-Lader mit Attrappe statt WebGL; `fenster` sammelt jedes angelegte Fenster. */
function attrappenKern(fenster: Attrappe[], ohneWebgl = false): () => Promise<KernModul> {
  const modul = {
    pixeldichte: (dpr: number, zoom = 1) => Math.min(2, dpr * zoom),
    erzeugeModellVorschau3d: () => {
      if (ohneWebgl) return null;
      const a = attrappe();
      fenster.push(a);
      return a;
    },
  } as unknown as KernModul;
  return () => Promise.resolve(modul);
}

// IntersectionObserver-Attrappe: die Probe sagt, was sichtbar ist.
class IOAttrappe {
  static alle: IOAttrappe[] = [];
  el: Element | null = null;
  constructor(readonly cb: (e: Array<{ isIntersecting: boolean }>) => void) {
    IOAttrappe.alle.push(this);
  }
  observe(el: Element): void {
    this.el = el;
  }
  unobserve(): void {}
  disconnect(): void {}
  melde(sichtbar: boolean): void {
    this.cb([{ isIntersecting: sichtbar }]);
  }
}

let root: Root | null = null;
let container: HTMLDivElement | null = null;

beforeEach(() => {
  IOAttrappe.alle = [];
});
afterEach(() => {
  if (root) act(() => root!.unmount());
  container?.remove();
  root = null;
  container = null;
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

function zeige(el: ReactNode): void {
  container = document.createElement('div');
  document.body.appendChild(container);
  root = createRoot(container);
  act(() => root!.render(el));
}

async function warte(): Promise<void> {
  for (let i = 0; i < 6; i++) {
    await act(async () => {
      await Promise.resolve();
    });
  }
}

const alleFenster = () => Array.from(container!.querySelectorAll<HTMLElement>('.vis-modell-3d'));

function fensterProps(extra: Partial<ModellVorschau3dProps> = {}): ModellVorschau3dProps {
  return { glb: GLB, ...extra };
}

describe('Rückfall ohne WebGL', () => {
  it('mit dem echten Kern (jsdom hat kein WebGL): «Kein 3D in diesem Fenster»', async () => {
    // jsdom meldet «getContext not implemented» auf die Konsole; das ist hier der Prüfgegenstand.
    vi.spyOn(console, 'error').mockImplementation(() => undefined);
    zeige(<ModellVorschau3d glb={GLB} grenze={new KontextGrenze()} />);
    // Der echte Kern kommt über import(); das dauert in der Probe etwas länger.
    await vi.waitFor(
      async () => {
        await warte();
        expect(container!.textContent).toContain(SAETZE_3D.keinWebgl);
      },
      { timeout: 15_000 },
    );
    expect(alleFenster()[0]!.dataset.stand).toBe('kein-webgl');
  });

  it('ohne WebGL gibt das Fenster seinen Platz an der Grenze zurück', async () => {
    const grenze = new KontextGrenze(1);
    zeige(<ModellVorschau3d {...fensterProps({ grenze, ladeKern: attrappenKern([], true) })} />);
    await warte();
    expect(container!.textContent).toBe(SAETZE_3D.keinWebgl);
    expect(grenze.belegt()).toBe(0);
  });

  it('ohne Modell: «Kein Modell geladen», kein Platz belegt', async () => {
    const grenze = new KontextGrenze();
    zeige(<ModellVorschau3d glb={null} grenze={grenze} ladeKern={attrappenKern([])} />);
    await warte();
    expect(container!.textContent).toBe(SAETZE_3D.leer);
    expect(grenze.belegt()).toBe(0);
  });
});

describe('Kontextgrenze (rein)', () => {
  const rr = (log: string[], id: string) => ({
    zuteilen: () => log.push(`+${id}`),
    abgeben: () => log.push(`-${id}`),
  });

  it(`höchstens ${HOECHSTENS_KONTEXTE} zeichnen, das fünfte wartet`, () => {
    const g = new KontextGrenze();
    const log: string[] = [];
    for (const id of ['a', 'b', 'c', 'd']) expect(g.anfragen(id, rr(log, id))).toBe('zugeteilt');
    expect(g.anfragen('e', rr(log, 'e'))).toBe('wartet');
    expect(g.belegt()).toBe(4);
    expect(g.wartende()).toEqual(['e']);
    g.freigeben('b');
    expect(log.at(-1)).toBe('+e');
    expect(g.belegt()).toBe(4);
  });

  it('ein ruhendes Fenster gibt seinen Platz her und steht danach an', () => {
    const g = new KontextGrenze(2);
    const log: string[] = [];
    g.anfragen('a', rr(log, 'a'));
    g.anfragen('b', rr(log, 'b'));
    g.ruhe('a', true);
    expect(g.anfragen('c', rr(log, 'c'))).toBe('zugeteilt');
    expect(log).toEqual(['+a', '+b', '-a', '+c']);
    expect(g.wartende()).toEqual(['a']);
    // a bleibt ausserhalb: ein frei werdender Platz geht nicht an ein ruhendes Fenster.
    g.freigeben('b');
    expect(log.at(-1)).toBe('+c');
    expect(g.belegt()).toBe(1);
    // … erst wenn es wieder sichtbar ist.
    g.ruhe('a', false);
    expect(log.at(-1)).toBe('+a');
  });

  it('Vorrang (grosse Ansicht) drängt das älteste kleine Fenster vor, auch wenn keines ruht', () => {
    const g = new KontextGrenze(2);
    const log: string[] = [];
    g.anfragen('a', rr(log, 'a'));
    g.anfragen('b', rr(log, 'b'));
    expect(g.anfragen('gross', rr(log, 'gross'), true)).toBe('zugeteilt');
    expect(log).toEqual(['+a', '+b', '-a', '+gross']);
    g.freigeben('gross');
    expect(log.at(-1)).toBe('+a');
  });

  it('geht ein zeichnendes Fenster aus dem Bild, bekommt das wartende sofort den Platz', () => {
    const g = new KontextGrenze(1);
    const log: string[] = [];
    g.anfragen('a', rr(log, 'a'));
    expect(g.anfragen('b', rr(log, 'b'))).toBe('wartet');
    g.ruhe('a', true);
    expect(log).toEqual(['+a', '-a', '+b']);
    expect(g.wartende()).toEqual(['a']);
  });

  it('wiederholtes Anfragen ändert nichts', () => {
    const g = new KontextGrenze(1);
    const log: string[] = [];
    g.anfragen('a', rr(log, 'a'));
    expect(g.anfragen('a', rr(log, 'a'))).toBe('zugeteilt');
    expect(log).toEqual(['+a']);
  });
});

describe('Kontextgrenze an der Hülle', () => {
  it('von fünf Fenstern zeichnen vier, das fünfte sagt, dass es ruht', async () => {
    const fenster: Attrappe[] = [];
    const grenze = new KontextGrenze();
    const ladeKern = attrappenKern(fenster);
    zeige(
      <div>
        {[0, 1, 2, 3, 4].map((i) => (
          <ModellVorschau3d key={i} glb={GLB} grenze={grenze} ladeKern={ladeKern} data-testid={`f${i}`} />
        ))}
      </div>,
    );
    await warte();
    const staende = alleFenster().map((el) => el.dataset.stand);
    expect(staende.filter((s) => s === 'bereit')).toHaveLength(4);
    expect(staende.filter((s) => s === 'ruht')).toHaveLength(1);
    expect(container!.textContent).toContain(SAETZE_3D.ruht);
    expect(fenster).toHaveLength(4);
  });

  it('beim Aushängen wird entsorgt und der Platz frei', async () => {
    const fenster: Attrappe[] = [];
    const grenze = new KontextGrenze();
    zeige(<ModellVorschau3d glb={GLB} grenze={grenze} ladeKern={attrappenKern(fenster)} />);
    await warte();
    expect(grenze.belegt()).toBe(1);
    act(() => root!.unmount());
    root = null;
    expect(fenster[0]!.aufrufe).toContain('dispose');
    expect(grenze.belegt()).toBe(0);
  });

  it('die Funktion, die das glb liefert, wird einmal gerufen', async () => {
    const liefere = vi.fn(() => GLB);
    const fenster: Attrappe[] = [];
    zeige(<ModellVorschau3d glb={liefere} grenze={new KontextGrenze()} ladeKern={attrappenKern(fenster)} />);
    await warte();
    expect(liefere).toHaveBeenCalledTimes(1);
    expect(fenster[0]!.aufrufe).toContain('ladeGlb');
  });

  it('liefert die Funktion nichts Lesbares: «Modell nicht lesbar»', async () => {
    const kaputt = () => {
      throw new Error('kein glb');
    };
    zeige(<ModellVorschau3d glb={kaputt} grenze={new KontextGrenze()} ladeKern={attrappenKern([])} />);
    await warte();
    expect(container!.textContent).toBe(SAETZE_3D.fehler);
  });
});

describe('Ausserhalb des Bildschirms', () => {
  it('hält an und macht weiter, sobald es wieder sichtbar ist', async () => {
    vi.stubGlobal('IntersectionObserver', IOAttrappe);
    const fenster: Attrappe[] = [];
    const grenze = new KontextGrenze();
    zeige(<ModellVorschau3d glb={GLB} grenze={grenze} ladeKern={attrappenKern(fenster)} />);
    await warte();
    const io = IOAttrappe.alle[0]!;
    act(() => io.melde(false));
    expect(fenster[0]!.aufrufe.at(-1)).toBe('pausiere');
    act(() => io.melde(true));
    expect(fenster[0]!.aufrufe.at(-1)).toBe('fortsetzen');
  });

  it('ein ruhendes Fenster wird für ein neues entsorgt und baut sich beim Zurückkommen neu auf', async () => {
    vi.stubGlobal('IntersectionObserver', IOAttrappe);
    const fenster: Attrappe[] = [];
    const grenze = new KontextGrenze(1);
    const ladeKern = attrappenKern(fenster);
    zeige(
      <div>
        <ModellVorschau3d glb={GLB} grenze={grenze} ladeKern={ladeKern} data-testid="a" />
        <ModellVorschau3d glb={GLB} grenze={grenze} ladeKern={ladeKern} data-testid="b" />
      </div>,
    );
    await warte();
    const [ioA, ioB] = IOAttrappe.alle;
    expect(alleFenster().map((e) => e.dataset.stand)).toEqual(['bereit', 'ruht']);
    // a verlässt den Bildschirm → b bekommt den Platz, a wird entsorgt (Ansicht gemerkt).
    act(() => ioA!.melde(false));
    await warte();
    expect(fenster[0]!.aufrufe).toContain('dispose');
    expect(alleFenster()[1]!.dataset.stand).toBe('bereit');
    // b geht, a kommt zurück: neues Fenster, Ansicht wiederhergestellt.
    act(() => ioB!.melde(false));
    act(() => ioA!.melde(true));
    await warte();
    expect(alleFenster()[0]!.dataset.stand).toBe('bereit');
    expect(fenster).toHaveLength(3);
    expect(fenster[2]!.aufrufe).toContain('setzeAnsicht');
  });
});

describe('Eingaben bleiben im Fenster', () => {
  it('Zeiger, Rad und Geste erreichen den Knotengraph nicht, solange 3D zeigt', async () => {
    const fenster: Attrappe[] = [];
    zeige(<ModellVorschau3d glb={GLB} grenze={new KontextGrenze()} ladeKern={attrappenKern(fenster)} />);
    await warte();
    // Der Knotengraph hört mit addEventListener an einem Vorfahren (Knotenebene).
    const gesehen: string[] = [];
    for (const typ of ANGEHALTENE_EREIGNISSE) container!.addEventListener(typ, () => gesehen.push(typ));
    const canvas = container!.querySelector('canvas')!;
    for (const typ of ANGEHALTENE_EREIGNISSE) canvas.dispatchEvent(new Event(typ, { bubbles: true, cancelable: true }));
    expect(gesehen).toEqual([]);
  });

  it('über dem Rückfall-Satz zoomt und schiebt der Knotengraph wie sonst', async () => {
    zeige(<ModellVorschau3d glb={GLB} grenze={new KontextGrenze()} ladeKern={attrappenKern([], true)} />);
    await warte();
    const gesehen: string[] = [];
    container!.addEventListener('wheel', () => gesehen.push('wheel'));
    container!.addEventListener('pointerdown', () => gesehen.push('pointerdown'));
    const el = alleFenster()[0]!;
    el.dispatchEvent(new Event('wheel', { bubbles: true }));
    el.dispatchEvent(new Event('pointerdown', { bubbles: true }));
    expect(gesehen).toEqual(['wheel', 'pointerdown']);
  });

  it('der WebKit-Pinch geht als Zoom an den Kern und nicht an die Seite', () => {
    const el = document.createElement('div');
    const faktoren: number[] = [];
    const ab = halteEingabenAn(el, (f) => faktoren.push(f));
    const geste = (typ: string, scale: number) => {
      const e = new Event(typ, { bubbles: true, cancelable: true }) as Event & { scale: number };
      Object.defineProperty(e, 'scale', { value: scale });
      el.dispatchEvent(e);
      return e;
    };
    geste('gesturestart', 1);
    const e1 = geste('gesturechange', 1.5);
    geste('gesturechange', 3);
    expect(e1.defaultPrevented).toBe(true);
    expect(faktoren).toEqual([1.5, 2]);
    ab();
    geste('gesturechange', 6);
    expect(faktoren).toHaveLength(2);
  });
});

describe('Doppelklick', () => {
  it('öffnet die grosse Ansicht und läuft nicht weiter', async () => {
    const onGross = vi.fn();
    zeige(<ModellVorschau3d glb={GLB} onGross={onGross} grenze={new KontextGrenze()} ladeKern={attrappenKern([])} />);
    await warte();
    const weiter = vi.fn();
    container!.addEventListener('dblclick', weiter);
    alleFenster()[0]!.dispatchEvent(new MouseEvent('dblclick', { bubbles: true }));
    expect(onGross).toHaveBeenCalledTimes(1);
    expect(weiter).not.toHaveBeenCalled();
  });

  it('ohne onGross rahmt er neu', async () => {
    const fenster: Attrappe[] = [];
    zeige(<ModellVorschau3d glb={GLB} grenze={new KontextGrenze()} ladeKern={attrappenKern(fenster)} />);
    await warte();
    alleFenster()[0]!.dispatchEvent(new MouseEvent('dblclick', { bubbles: true }));
    expect(fenster[0]!.aufrufe.at(-1)).toBe('rahmen');
  });
});

describe('Grosse Ansicht', () => {
  it('steht im Dialog mit Hilfezeile und schliesst mit Escape', async () => {
    const zu = vi.fn();
    zeige(<ModellVorschau3dGross glb={null} onClose={zu} grenze={new KontextGrenze()} />);
    await warte();
    const dialog = document.querySelector('[role="dialog"]')!;
    expect(dialog.getAttribute('aria-label')).toBe('Modell in 3D');
    expect(dialog.textContent).toContain(HILFE_3D_GROSS);
    act(() => {
      document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }));
    });
    expect(zu).toHaveBeenCalled();
  });
});

describe('Bau: der Kern ist ein eigener Teil', () => {
  it('kein Quelltext lädt den Kern statisch (nur import() oder import type)', () => {
    const src = path.resolve(HIER, '../src');
    const dateien: string[] = [];
    const gehe = (d: string) => {
      for (const n of readdirSync(d)) {
        const p = path.join(d, n);
        if (statSync(p).isDirectory()) gehe(p);
        else if (/\.(ts|tsx)$/.test(n)) dateien.push(p);
      }
    };
    gehe(src);
    const statisch = dateien.filter((p) => {
      const t = readFileSync(p, 'utf8');
      return /^\s*import\s+(?!type\b)[^;]*from\s+['"][^'"]*modell-vorschau-3d-kern['"]/m.test(t);
    });
    expect(statisch).toEqual([]);
    const huelle = readFileSync(path.join(src, 'modules/vis/modell-vorschau-3d.tsx'), 'utf8');
    expect(huelle).toContain("import('./modell-vorschau-3d-kern')");
  });
});
