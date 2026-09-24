import {
  cloneElement,
  isValidElement,
  useEffect,
  useId,
  useRef,
  useState,
  type FocusEvent as ReactFocusEvent,
  type HTMLAttributes,
  type MouseEvent as ReactMouseEvent,
  type PointerEvent as ReactPointerEvent,
  type ReactElement,
} from 'react';
import { useOverlaySchliessen } from './overlay-schliessen';
import { istTouchArtig } from './zeiger';

/**
 * KTooltip (P-f, Bausteine-Nachtrag) — Ersatz für natives `title=`, das
 * `docs/UI-KONZEPT-065.md:74` bereits als «CSS-only, ~400ms Verzögerung»
 * spezifiziert, aber nie gebaut hat.
 *
 * **ZWEIMAL BERICHTIGT AM 09.09.2026 — und die zweite Berichtigung nimmt die
 * erste zurueck. Beide bleiben hier stehen, weil der Fehler dazwischen
 * lehrreicher ist als die richtige Zahl.**
 *
 * Urspruenglich stand hier «**239** rohe `title=`-Stellen … netto rund 211».
 * Am Vormittag habe ich das auf «157, netto 129» korrigiert — mit einem
 * Suchmuster, das nur `title="` traf und damit **jede Stelle mit einem
 * Ausdruck (`title={...}`) uebersah**. Die Korrektur war der Fehler, nicht
 * die Zahl.
 *
 * Gemessen mit beiden Schreibweisen, Kommentare vorher entfernt
 * (`tools/kurzhilfe-gate.mjs` faehrt genau diese Zaehlung):
 *
 *     title="…"                              158
 *     title={…}                                85
 *     zusammen, ohne Kommentare               241
 *     davon auf einer `KIcon`-Zeile            28
 *     → netto                                 213
 *
 * Die 28 sind legitim: `title` auf `KIcon` selbst ist das native
 * SVG-`<title>`, das dieser Baustein nicht ersetzt.
 *
 * **Die Lehre steht ueber der Zahl:** eine Zahl ohne ihren Befehl ist eine
 * Behauptung — und ein Befehl, der die halbe Schreibweise nicht kennt, ist
 * eine schlechtere Behauptung als gar keine, weil er wie ein Beleg
 * aussieht.
 *
 * Natives `title` erscheint auf Touch-Geräten (iPad, E-8-Kanon) **nie** —
 * kein Ereignis löst es dort aus. Ein reines CSS-`:hover` wäre exakt derselbe
 * Fehler in neuem Gewand: auch `:hover` bleibt auf Touch stumm, weil ein
 * Finger nie "hovert". KTooltip ist deshalb bewusst NICHT CSS-only, sondern
 * ereignisgesteuert über den zentralen Helfer `istTouchArtig` (`zeiger.ts`,
 * D-8/E-8 B):
 *
 * - Maus (`!istTouchArtig`): `pointerenter` startet eine ~400ms-Verzögerung
 *   (Spec-Wortlaut), `pointerleave` bricht sie ab/schliesst sofort. Fokus
 *   (Tastatur/Screenreader) zeigt/verbirgt ohne Verzögerung — dieselbe
 *   Sofort-Regel wie bei jedem anderen fokussierbaren Element im Bestand.
 * - Touch/Pen (`istTouchArtig`): ein Tippen auf das Kind SCHALTET die Blase
 *   um (kein Hover möglich — E-8 C verbietet ausdrücklich, dafür einen
 *   Long-press einzuführen, `island/IslandShell.tsx:1253-1259`). Ein
 *   zweiter Tipp aufs Kind oder ein Tipp ausserhalb (`useOverlaySchliessen`,
 *   Aussenklick+Esc, nur aktiv registriert solange die Blase offen ist)
 *   schliesst wieder.
 *
 * Der Zeigertyp fürs nachfolgende `click` wird — wie in `IslandShell.tsx`
 * vorgemacht — aus dem VORAUSGEHENDEN `pointerdown` gelesen: ein `click`
 * trägt in jsdom/älteren Engines keinen `pointerType`.
 *
 * Die Blase braucht eine schwebende Fläche → `--k-glas-mittel` (neue
 * Materialleiter, s. Auftrag): leichter als `--k-glas-dicht` (KMenu/KDialog,
 * dauerhaft geöffnete Karten), kräftiger als `--k-glas-duenn` (kleine
 * permanente Badges wie `.k-variantenkarte-id`) — ein Tooltip ist
 * transienter als beides, die mittlere Stufe passt seinem Gewicht.
 *
 * API: GENAU EIN Kind wird geklont (Muster: Radix/Floating-UI-Tooltips) und
 * trägt danach die Zeiger-/Fokus-Handler + `aria-describedby` auf die Blase,
 * bestehende Handler des Kindes bleiben erhalten (werden nach den eigenen
 * aufgerufen). `text` ersetzt `title=` wörtlich; `kuerzel` deckt den
 * zweiten Spec-Satz («zeigt Name + Kurztaste») ab.
 */

const VERZOEGERUNG_MS = 400;

export interface KTooltipProps extends Omit<HTMLAttributes<HTMLSpanElement>, 'children' | 'title'> {
  /** Der Tooltip-Text — ersetzt `title=`. */
  text: string;
  /** Sichtbarer Tastenkürzel-Zusatz, z.B. "⌘K" (UI-KONZEPT-065 §3). */
  kuerzel?: string;
  /** Seite, an der die Blase erscheint. Default 'oben'. */
  lage?: 'oben' | 'unten' | 'links' | 'rechts';
  /** GENAU EIN Kind — wird geklont, s. Kopfkommentar. */
  children: ReactElement;
  'data-testid'?: string;
}

type Handler<E> = ((e: E) => void) | undefined;

export function KTooltip({
  text,
  kuerzel,
  lage = 'oben',
  children,
  className,
  'data-testid': testid,
  ...rest
}: KTooltipProps) {
  const [offen, setOffen] = useState(false);
  const id = useId();
  const wrapRef = useRef<HTMLSpanElement | null>(null);
  const zeitgeber = useRef<ReturnType<typeof setTimeout> | null>(null);
  const zeigerWarTouch = useRef(false);

  const abbrechenZeitgeber = () => {
    if (zeitgeber.current !== null) {
      clearTimeout(zeitgeber.current);
      zeitgeber.current = null;
    }
  };

  // Aufräumen bei Unmount — ein hängender Zeitgeber darf keinen setState
  // auf ein bereits entferntes Element auslösen.
  useEffect(() => abbrechenZeitgeber, []);

  // Touch: Tippen ausserhalb ODER Esc schliesst — nur registriert, solange
  // die Blase wirklich offen ist (kein Leerlauf-Listener bei jedem Render).
  useOverlaySchliessen(wrapRef, () => setOffen(false), { esc: offen, aussenklick: offen });

  if (!isValidElement(children)) return children;

  const kindProps = children.props as Record<string, unknown>;
  const vorhandenBeschriftet = kindProps['aria-describedby'] as string | undefined;

  // `ReactElement` (ohne Generic) hat in den aktuellen React-19-Typen
  // `props: unknown` — `cloneElement` verweigert damit JEDE zusätzliche
  // Prop, auch bei echten React-Elementen. Der Cast ist lokal auf genau
  // diesen Aufruf begrenzt (kein `any` im Props-Vertrag von aussen): das
  // Kind bleibt für Aufrufer ein gewöhnliches `ReactElement`.
  const kind = cloneElement(children as ReactElement<Record<string, unknown>>, {
    // P-KURZHILFE-LESBAR (09.09.2026): `aria-describedby` zeigt IMMER auf den
    // Text, nicht nur waehrend die Blase offen ist. Begruendung unten beim
    // stillen Textknoten.
    'aria-describedby': vorhandenBeschriftet !== undefined ? `${vorhandenBeschriftet} ${id}` : id,
    onPointerDown: (e: ReactPointerEvent) => {
      zeigerWarTouch.current = istTouchArtig(e);
      (kindProps.onPointerDown as Handler<ReactPointerEvent>)?.(e);
    },
    onPointerEnter: (e: ReactPointerEvent) => {
      if (!istTouchArtig(e)) {
        abbrechenZeitgeber();
        zeitgeber.current = setTimeout(() => setOffen(true), VERZOEGERUNG_MS);
      }
      (kindProps.onPointerEnter as Handler<ReactPointerEvent>)?.(e);
    },
    onPointerLeave: (e: ReactPointerEvent) => {
      abbrechenZeitgeber();
      if (!istTouchArtig(e)) setOffen(false);
      (kindProps.onPointerLeave as Handler<ReactPointerEvent>)?.(e);
    },
    onFocus: (e: ReactFocusEvent) => {
      setOffen(true);
      (kindProps.onFocus as Handler<ReactFocusEvent>)?.(e);
    },
    onBlur: (e: ReactFocusEvent) => {
      setOffen(false);
      (kindProps.onBlur as Handler<ReactFocusEvent>)?.(e);
    },
    onClick: (e: ReactMouseEvent) => {
      // Nur Touch/Pen schaltet per Klick um — Maus hat die Blase längst
      // per Hover offen, ein zusätzliches Klick-Toggle würde sie sofort
      // wieder zuklappen, bevor der Klick des Kindes ausgewertet ist.
      if (zeigerWarTouch.current) setOffen((o) => !o);
      (kindProps.onClick as Handler<ReactMouseEvent>)?.(e);
    },
  });

  const klassen = ['k-tooltip', className].filter(Boolean).join(' ');

  return (
    <span
      ref={wrapRef}
      className={klassen}
      {...(testid !== undefined ? { 'data-testid': testid } : {})}
      {...rest}
    >
      {kind}
      {/* P-KURZHILFE-LESBAR (09.09.2026) — DER TEXT STEHT IMMER IM BAUM.

          Der Befund kam beim ersten echten Einsatz dieses Bausteins (B74,
          der technische IFC-Name an der Klassenliste): vorher stand dort ein
          natives `title=`, und der Austausch machte die Auskunft fuer
          Hilfstechnik SCHLECHTER, nicht besser. Ein natives `title` liegt
          dauerhaft im Zugaenglichkeitsbaum; diese Blase gab es erst her,
          wenn jemand mit der Maus darauf zeigte — eine Sprachausgabe zeigt
          nicht.

          Damit war der Baustein, der das native Feld ersetzen soll, in
          genau einer Hinsicht schlechter als das, was er ersetzt. Das ist
          fuer 212 geplante Austausche der falsche Ausgangspunkt.

          Behoben mit dem Mittel, das seit heute dafuer da ist: ein
          `.k-nur-sr`-Knoten traegt den Text dauerhaft — fuer das Auge
          unsichtbar, fuer die Sprachausgabe da —, und `aria-describedby`
          zeigt IMMER darauf. Die sichtbare Blase bleibt, was sie war: die
          Zugabe fuer Auge und Finger. */}
      <span id={id} className="k-nur-sr">
        {text}
        {kuerzel !== undefined ? ` ${kuerzel}` : ''}
      </span>
      {offen && (
        <span role="tooltip" aria-hidden="true" className={`k-tooltip-blase k-tooltip-blase--${lage} k-einblenden`}>
          {text}
          {kuerzel !== undefined && <span className="k-tooltip-kuerzel">{kuerzel}</span>}
        </span>
      )}
    </span>
  );
}
