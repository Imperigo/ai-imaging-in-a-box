import { useEffect, useId, useRef, useState, type CSSProperties } from 'react';
import type {
  Ansicht,
  Blickvorschau,
  ModellVorschau3d as KernFenster,
  VorschauKamera,
} from './modell-vorschau-3d-kern';
import './modell-vorschau-3d.css';

/**
 * **Kleines 3D-Fenster — die React-Hülle** (gemeinsamer Baustein des Bauplans «Neue Knoten»
 * vom 20.10.2026; Entscheid 109 A: klein fest im Modell-Knoten, Doppelklick öffnet gross).
 *
 * Läuft unverändert in beiden Programmen: die Eingabe ist **glb-Bytes** oder eine Funktion, die
 * sie liefert — in KosmoOrbit `exportGlb(doc)` aus dem Kern, in Visbox derselbe Name im
 * Stellvertreter, der die Bytes des geladenen Modells zurückgibt. Die Funktion wird einmal je
 * Identität gerufen; wer sie inline schreibt, exportiert bei jedem Zeichnen neu (darum beim
 * Aufrufer `useCallback`/`useMemo`).
 *
 * Was die Hülle zusätzlich zum Kern tut:
 *  - **lädt den Kern erst bei Bedarf** (`import()`, eigener Teil des Baus);
 *  - **Eingaben bleiben im Fenster**: Zeiger, Rad und Trackpad-Geste werden am Fenster
 *    angehalten (`stopPropagation` an einem echten Hörer, nicht an Reacts Ereignis — der
 *    Knotengraph hört mit `addEventListener` an seiner Knotenebene, s. `NodeCanvas.tsx` und
 *    `shell/trackpad-geste.ts`; ein React-Stopp käme dort zu spät). Das gilt nur, solange das
 *    Fenster wirklich 3D zeigt; über dem Rückfall-Satz zoomt und schiebt der Graph wie sonst;
 *  - **Kontextgrenze**: höchstens `HOECHSTENS_KONTEXTE` Fenster zeichnen gleichzeitig (Browser
 *    verwerfen ab etwa 16 WebGL-Kontexten den ältesten). Ein Fenster ausserhalb des Bildschirms
 *    hält an und gibt seinen Platz als Erstes her;
 *  - **Rückfall** ohne WebGL: «Kein 3D in diesem Fenster»;
 *  - **Doppelklick**: `onGross` (grosse Ansicht, `modell-vorschau-3d-gross.tsx`); ohne
 *    `onGross` rahmt er neu.
 */

type KernModul = typeof import('./modell-vorschau-3d-kern');

/** glb-Bytes oder wer sie liefert (`exportGlb(doc)`). */
export type GlbQuelle = ArrayBuffer | (() => ArrayBuffer | Promise<ArrayBuffer>);

/** Höchstens so viele 3D-Fenster zeichnen gleichzeitig. */
export const HOECHSTENS_KONTEXTE = 4;

export const SAETZE_3D = {
  keinWebgl: 'Kein 3D in diesem Fenster',
  leer: 'Kein Modell geladen',
  laedt: '3D wird geladen …',
  ruht: '3D ruht – zu viele 3D-Fenster offen',
  fehler: 'Modell nicht lesbar',
  unterbrochen: '3D unterbrochen – wird neu aufgebaut',
} as const;

/** Bedienung in einem Satz (für Vorleser; die grosse Ansicht zeigt ihre eigene Hilfezeile). */
export const HILFE_3D_KLEIN = 'Modell in 3D. Ziehen: drehen · Rad: näher · Doppelklick: gross';
export const HILFE_3D_OHNE_GROSS = 'Modell in 3D. Ziehen: drehen · Rad: näher · Doppelklick: neu rahmen';

export type Stand3d = 'leer' | 'kein-webgl' | 'ruht' | 'laedt' | 'bereit' | 'fehler' | 'unterbrochen';

// ─────────────────────────────────────────────────────────────────────────────
// Kontextgrenze
// ─────────────────────────────────────────────────────────────────────────────

export interface KontextRueckruf {
  /** Der Platz ist da: jetzt darf ein Zeichner angelegt werden. */
  zuteilen(): void;
  /** Der Platz wird gebraucht: Zeichner entsorgen. Das Fenster steht danach wieder an. */
  abgeben(): void;
}

interface Eintrag {
  readonly id: string;
  readonly rueckruf: KontextRueckruf;
  readonly vorrang: boolean;
  ruht: boolean;
}

/**
 * Wer zeichnen darf. Rein, ohne DOM — die Proben fahren sie direkt.
 *
 * Regeln:
 *  1. Ist ein Platz frei, bekommt ihn, wer anfragt.
 *  2. Sonst gibt das **älteste ruhende** Fenster (ausserhalb des Bildschirms) seinen Platz her.
 *  3. Fragt ein Fenster **mit Vorrang** (die grosse Ansicht) und ruht keines, gibt das älteste
 *     ohne Vorrang her.
 *  4. Wer hergibt, steht danach vorne in der Warteschlange; sobald ein Platz frei wird, bekommt
 *     ihn das erste **nicht ruhende** wartende Fenster.
 *  5. Geht ein zeichnendes Fenster aus dem Bild, während ein sichtbares wartet, gibt es seinen
 *     Platz sofort her.
 *
 * `anfragen` ist wiederholbar: wer schon zeichnet oder wartet, bleibt, wo er ist.
 */
export class KontextGrenze {
  private halter: Eintrag[] = [];
  private warten: Eintrag[] = [];

  constructor(readonly hoechstens = HOECHSTENS_KONTEXTE) {}

  anfragen(id: string, rueckruf: KontextRueckruf, vorrang = false): 'zugeteilt' | 'wartet' {
    if (!this.halter.some((e) => e.id === id)) {
      const wartend = this.warten.find((e) => e.id === id);
      if (wartend) {
        wartend.ruht = false;
      } else {
        this.warten.push({ id, rueckruf, vorrang, ruht: false });
      }
      this.verteile();
      // Regel 3: Vorrang drängt das älteste Fenster ohne Vorrang vor.
      const nochWartend = this.warten.find((e) => e.id === id);
      if (nochWartend?.vorrang) {
        const opfer = this.halter.find((e) => !e.vorrang);
        if (opfer) {
          this.gibAb(opfer);
          this.teileZu(nochWartend);
        }
      }
    }
    return this.halter.some((e) => e.id === id) ? 'zugeteilt' : 'wartet';
  }

  /** Fenster ist ausserhalb des Bildschirms (`true`) oder wieder sichtbar. */
  ruhe(id: string, ruht: boolean): void {
    const e = this.halter.find((x) => x.id === id) ?? this.warten.find((x) => x.id === id);
    if (!e) return;
    e.ruht = ruht;
    this.verteile();
  }

  freigeben(id: string): void {
    const vorher = this.halter.length;
    this.halter = this.halter.filter((e) => e.id !== id);
    this.warten = this.warten.filter((e) => e.id !== id);
    if (this.halter.length < vorher) this.verteile();
  }

  /** Wie viele Fenster zeichnen gerade. */
  belegt(): number {
    return this.halter.length;
  }

  /** Wer wartet (für die Proben). */
  wartende(): string[] {
    return this.warten.map((e) => e.id);
  }

  /** Regeln 1, 2, 4 und 5: wer sichtbar wartet, bekommt einen freien oder einen ruhenden Platz. */
  private verteile(): void {
    for (;;) {
      const naechster = this.warten.find((e) => !e.ruht);
      if (!naechster) return;
      if (this.halter.length >= this.hoechstens) {
        const ruhender = this.halter.find((e) => e.ruht);
        if (!ruhender) return;
        this.gibAb(ruhender);
      }
      this.teileZu(naechster);
    }
  }

  private gibAb(e: Eintrag): void {
    this.halter = this.halter.filter((x) => x !== e);
    this.warten.unshift(e);
    e.rueckruf.abgeben();
  }

  private teileZu(e: Eintrag): void {
    this.warten = this.warten.filter((x) => x !== e);
    this.halter.push(e);
    e.rueckruf.zuteilen();
  }
}

/** Die eine Grenze aller 3D-Fenster dieser Seite. */
export const vorschauKontexte = new KontextGrenze(HOECHSTENS_KONTEXTE);

// ─────────────────────────────────────────────────────────────────────────────
// Eingaben anhalten
// ─────────────────────────────────────────────────────────────────────────────

/** Ereignisse, die am Fenster enden und den Knotengraph nicht erreichen. */
export const ANGEHALTENE_EREIGNISSE = [
  'pointerdown',
  'mousedown',
  'touchstart',
  'wheel',
  'contextmenu',
  'gesturestart',
  'gesturechange',
  'gestureend',
] as const;

/**
 * Hängt die Hörer an, die Eingaben im Fenster halten. Die WebKit-Pinch-Geste (Mac-App) kommt
 * nicht als Rad; sie wird hier zusätzlich als Zoom an den Kern gegeben (`onPinch`), sonst täte
 * ein Pinch über dem Fenster gar nichts. Gibt eine Funktion zum Abhängen zurück.
 */
export function halteEingabenAn(el: HTMLElement, onPinch?: (faktor: number) => void): () => void {
  let letzte = 1;
  const anhalten = (e: Event) => {
    e.stopPropagation();
    if (e.type.startsWith('gesture')) {
      e.preventDefault();
      const scale = (e as Event & { scale?: number }).scale;
      if (e.type === 'gesturestart') letzte = 1;
      else if (e.type === 'gesturechange' && typeof scale === 'number' && scale > 0 && Number.isFinite(scale)) {
        const faktor = scale / letzte;
        letzte = scale;
        if (faktor !== 1) onPinch?.(faktor);
      }
    }
  };
  for (const typ of ANGEHALTENE_EREIGNISSE) el.addEventListener(typ, anhalten, { passive: false });
  return () => {
    for (const typ of ANGEHALTENE_EREIGNISSE) el.removeEventListener(typ, anhalten);
  };
}

// ─────────────────────────────────────────────────────────────────────────────
// Kern laden
// ─────────────────────────────────────────────────────────────────────────────

let kernVersprechen: Promise<KernModul> | null = null;

/** Lädt den Kern einmal je Seite — als eigener Teil des Baus. */
export function ladeVorschauKern(): Promise<KernModul> {
  kernVersprechen ??= import('./modell-vorschau-3d-kern').catch((e: unknown) => {
    kernVersprechen = null;
    throw e;
  });
  return kernVersprechen;
}

// ─────────────────────────────────────────────────────────────────────────────
// Die Hülle
// ─────────────────────────────────────────────────────────────────────────────

export interface ModellVorschau3dProps {
  /** `null` = kein Modell («Kein Modell geladen»). */
  readonly glb: GlbQuelle | null;
  /** Kameras als Kegel (glTF-Achsen, `fov` waagrecht in Grad). */
  readonly kameras?: readonly VorschauKamera[];
  /** CSS-Skalierung des Knotengraphs; geht in die Pixeldichte ein. */
  readonly knotenZoom?: number;
  /** Doppelklick: grosse Ansicht öffnen. Fehlt es, rahmt der Doppelklick neu. */
  readonly onGross?: () => void;
  /** Die grosse Ansicht drängt kleine Fenster vor, wenn alle Plätze belegt sind. */
  readonly vorrang?: boolean;
  /** Kleine Bilder aus jeder Kamera, nach jedem Laden und jeder neuen Kameraliste. */
  readonly onBlickvorschau?: (bilder: readonly (Blickvorschau | null)[]) => void;
  readonly blickvorschauGroesse?: { readonly breite: number; readonly hoehe: number };
  readonly breite?: CSSProperties['width'];
  readonly hoehe?: CSSProperties['height'];
  readonly className?: string;
  readonly 'data-testid'?: string;
  /** Für die Proben: eigene Grenze bzw. eigener Kern-Lader. */
  readonly grenze?: KontextGrenze;
  readonly ladeKern?: () => Promise<KernModul>;
}

interface BytesMerk {
  readonly quelle: GlbQuelle;
  readonly bytes: Promise<ArrayBuffer>;
}

function holeBytes(merk: { current: BytesMerk | null }, quelle: GlbQuelle): Promise<ArrayBuffer> {
  if (merk.current && merk.current.quelle === quelle) return merk.current.bytes;
  const bytes =
    typeof quelle === 'function'
      ? new Promise<ArrayBuffer>((ok, fehler) => {
          try {
            Promise.resolve(quelle()).then(ok, fehler);
          } catch (e) {
            fehler(e instanceof Error ? e : new Error(String(e)));
          }
        })
      : Promise.resolve(quelle);
  merk.current = { quelle, bytes };
  return bytes;
}

interface Aktuell {
  readonly onGross: (() => void) | undefined;
  readonly onBlickvorschau: ModellVorschau3dProps['onBlickvorschau'];
  readonly kameras: readonly VorschauKamera[] | undefined;
  readonly blickvorschauGroesse: ModellVorschau3dProps['blickvorschauGroesse'];
  readonly knotenZoom: number;
}

function meldeBlickvorschau(k: KernFenster, a: Aktuell): void {
  if (!a.onBlickvorschau) return;
  const g = a.blickvorschauGroesse;
  a.onBlickvorschau((a.kameras ?? []).map((_, i) => k.blickvorschau(i, g?.breite, g?.hoehe)));
}

function geraetePixel(): number {
  return typeof window !== 'undefined' && window.devicePixelRatio > 0 ? window.devicePixelRatio : 1;
}

export function ModellVorschau3d({
  glb,
  kameras,
  knotenZoom = 1,
  onGross,
  vorrang = false,
  onBlickvorschau,
  blickvorschauGroesse,
  breite,
  hoehe,
  className,
  'data-testid': testId = 'modell-3d',
  grenze = vorschauKontexte,
  ladeKern = ladeVorschauKern,
}: ModellVorschau3dProps) {
  const id = useId();
  const huelle = useRef<HTMLDivElement>(null);
  const leinwand = useRef<HTMLCanvasElement>(null);
  const kern = useRef<KernFenster | null>(null);
  const modul = useRef<KernModul | null>(null);
  const ansichtMerk = useRef<Ansicht | null>(null);
  const bytesMerk = useRef<BytesMerk | null>(null);
  const keinWebgl = useRef(false);

  const [sichtbar, setSichtbar] = useState(true);
  const [platz, setPlatz] = useState(false);
  const [stand, setStand] = useState<Stand3d>('laedt');
  // Neue Leinwand nach jedem Entsorgen: ein entzogener Kontext kommt auf derselben
  // Leinwand nicht wieder.
  const [leinwandNr, setLeinwandNr] = useState(0);
  // Zählt die angelegten Zeichner; die Folge-Effekte hängen daran.
  const [kernNr, setKernNr] = useState(0);

  const hatGlb = glb !== null;
  const zeichnet = hatGlb && platz && !keinWebgl.current;

  // Neueste Werte ohne Effekt-Neustart.
  const aktuell = useRef<Aktuell>({ onGross, onBlickvorschau, kameras, blickvorschauGroesse, knotenZoom });
  aktuell.current = { onGross, onBlickvorschau, kameras, blickvorschauGroesse, knotenZoom };
  const geladen = useRef(false);

  // Sichtbarkeit: ausserhalb des Bildschirms anhalten.
  useEffect(() => {
    const el = huelle.current;
    if (!el || typeof IntersectionObserver === 'undefined') return;
    const io = new IntersectionObserver((eintraege) => {
      const letzter = eintraege[eintraege.length - 1];
      if (letzter) setSichtbar(letzter.isIntersecting);
    });
    io.observe(el);
    return () => io.disconnect();
  }, []);

  // Platz an der Grenze: anfragen, solange ein Modell da ist; beim Aushängen zurückgeben.
  useEffect(() => {
    if (!hatGlb) return;
    return () => {
      grenze.freigeben(id);
      setPlatz(false);
    };
  }, [hatGlb, grenze, id]);

  useEffect(() => {
    if (!hatGlb || keinWebgl.current) return;
    if (sichtbar) {
      grenze.anfragen(id, { zuteilen: () => setPlatz(true), abgeben: () => setPlatz(false) }, vorrang);
      grenze.ruhe(id, false);
    } else {
      grenze.ruhe(id, true);
    }
  }, [hatGlb, sichtbar, grenze, id, vorrang]);

  // Zeichner anlegen, solange der Platz da ist.
  useEffect(() => {
    if (!zeichnet) return;
    let abgebrochen = false;
    setStand('laedt');
    ladeKern()
      .then((m) => {
        const canvas = leinwand.current;
        const el = huelle.current;
        if (abgebrochen || !canvas || !el) return;
        modul.current = m;
        const fenster = m.erzeugeModellVorschau3d({
          canvas,
          pixeldichte: m.pixeldichte(geraetePixel(), aktuell.current.knotenZoom),
          breite: el.clientWidth || 1,
          hoehe: el.clientHeight || 1,
          onKontextVerloren: () => setStand('unterbrochen'),
          onKontextZurueck: () => setStand('bereit'),
        });
        if (!fenster) {
          keinWebgl.current = true;
          grenze.freigeben(id);
          setPlatz(false);
          setStand('kein-webgl');
          return;
        }
        kern.current = fenster;
        setKernNr((n) => n + 1);
      })
      .catch(() => {
        if (!abgebrochen) setStand('fehler');
      });
    return () => {
      abgebrochen = true;
      const k = kern.current;
      if (k) {
        ansichtMerk.current = k.ansicht();
        k.dispose();
        kern.current = null;
        setLeinwandNr((n) => n + 1);
      }
    };
  }, [zeichnet, ladeKern, grenze, id]);

  // Modell laden (und bei neuer Quelle neu laden).
  useEffect(() => {
    const k = kern.current;
    if (!k || glb === null) return;
    let abgebrochen = false;
    geladen.current = false;
    setStand('laedt');
    holeBytes(bytesMerk, glb)
      .then((bytes) => (abgebrochen ? undefined : k.ladeGlb(bytes)))
      .then(() => {
        if (abgebrochen || kern.current !== k) return;
        const merk = ansichtMerk.current;
        if (merk) {
          k.setzeAnsicht(merk);
          ansichtMerk.current = null;
        }
        geladen.current = true;
        setStand('bereit');
        meldeBlickvorschau(k, aktuell.current);
      })
      .catch(() => {
        if (!abgebrochen) setStand('fehler');
      });
    return () => {
      abgebrochen = true;
    };
  }, [glb, kernNr]);

  // Kameras als Kegel.
  useEffect(() => {
    const k = kern.current;
    if (!k) return;
    k.setzeKameras(kameras ?? []);
    if (geladen.current) meldeBlickvorschau(k, aktuell.current);
  }, [kameras, kernNr]);

  // Pixeldichte = Bildschirmdichte × Knotenzoom, begrenzt.
  useEffect(() => {
    const k = kern.current;
    const m = modul.current;
    if (k && m) k.setzePixeldichte(m.pixeldichte(geraetePixel(), knotenZoom));
  }, [knotenZoom, kernNr]);

  // Ausserhalb des Bildschirms: anhalten.
  useEffect(() => {
    const k = kern.current;
    if (!k) return;
    if (sichtbar) k.fortsetzen();
    else k.pausiere();
  }, [sichtbar, kernNr]);

  // Grösse folgt dem Fenster.
  useEffect(() => {
    const el = huelle.current;
    if (!el || !kern.current || typeof ResizeObserver === 'undefined') return;
    const ro = new ResizeObserver((eintraege) => {
      const r = eintraege[eintraege.length - 1]?.contentRect;
      if (r && r.width > 0 && r.height > 0) kern.current?.setzeGroesse(r.width, r.height);
    });
    ro.observe(el);
    return () => ro.disconnect();
  }, [kernNr]);

  // Eingaben bleiben im Fenster, solange es 3D zeigt.
  const aktiv = stand === 'bereit' && zeichnet;
  useEffect(() => {
    const el = huelle.current;
    if (!el || !aktiv) return;
    return halteEingabenAn(el, (faktor) => kern.current?.zoome(faktor));
  }, [aktiv]);

  // Doppelklick: gross öffnen oder neu rahmen.
  useEffect(() => {
    const el = huelle.current;
    if (!el) return;
    const beiDoppelklick = (e: MouseEvent) => {
      e.stopPropagation();
      e.preventDefault();
      const gross = aktuell.current.onGross;
      if (gross) gross();
      else kern.current?.rahmen();
    };
    el.addEventListener('dblclick', beiDoppelklick);
    return () => el.removeEventListener('dblclick', beiDoppelklick);
  }, []);

  const gezeigt: Stand3d = !hatGlb
    ? 'leer'
    : keinWebgl.current
      ? 'kein-webgl'
      : !platz
        ? 'ruht'
        : stand;
  const satz =
    gezeigt === 'bereit'
      ? null
      : gezeigt === 'kein-webgl'
        ? SAETZE_3D.keinWebgl
        : SAETZE_3D[gezeigt];

  const stil: CSSProperties = {
    ...(breite !== undefined ? { width: breite } : {}),
    ...(hoehe !== undefined ? { height: hoehe } : {}),
  };

  return (
    <div
      ref={huelle}
      className={className ? `vis-modell-3d ${className}` : 'vis-modell-3d'}
      data-testid={testId}
      data-stand={gezeigt}
      style={stil}
      role="group"
      aria-label={onGross ? HILFE_3D_KLEIN : HILFE_3D_OHNE_GROSS}
    >
      <canvas key={leinwandNr} ref={leinwand} className="vis-modell-3d-leinwand" aria-hidden />
      {satz !== null ? (
        <div className="vis-modell-3d-satz" role="status" data-testid={`${testId}-satz`}>
          {satz}
        </div>
      ) : null}
    </div>
  );
}
