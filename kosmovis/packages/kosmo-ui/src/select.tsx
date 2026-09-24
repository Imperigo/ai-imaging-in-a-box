import {
  Children,
  isValidElement,
  useEffect,
  useId,
  useMemo,
  useRef,
  useState,
  type ChangeEvent,
  type CSSProperties,
  type KeyboardEvent as ReactKeyboardEvent,
  type OptionHTMLAttributes,
  type ReactNode,
  type SelectHTMLAttributes,
} from 'react';
import { createPortal } from 'react-dom';

/**
 * KSelect (v0.6.9) — ECHTES Custom-Dropdown im Werkplan-Stil.
 *
 * Der historische Vertrag «bleibt ein natives <select>, E2E bedient es per
 * `selectOption`» ist mit v0.6.9 bewusst und als EIN kohärenter Schnitt
 * gebrochen. Der NEUE Vertrag:
 *
 * - Der Trigger ist ein `<button>` mit den bisherigen `.k-select`-Klassen
 *   (1px-Tusche-Rahmen, `--k-radius-sm`, SVG-Chevron über `background-image`
 *   — die Akzent×Theme-Varianten in aura.css gelten unverändert). KEINE
 *   45°-Ecke: die gehört den Karteikarten (gleiches Prinzip wie KDialog).
 * - `data-testid` sitzt auf dem TRIGGER; der Trigger trägt zusätzlich
 *   `data-value` mit dem aktuellen Wert (E2E-Ersatz für `toHaveValue`).
 * - Das Popup (nur offen gemountet, `.k-menu`-Karte wie KMenu) trägt
 *   `data-testid="${testid}-popup"`, `role="listbox"`; jede Option ist ein
 *   Button mit `role="option"`, `aria-selected` und `data-value`.
 * - E2E bedient KSelect über `e2e/helfer/waehleOption.ts` (Trigger klicken →
 *   Popup abwarten → `[data-value="…"]` klicken), NICHT mehr `selectOption`.
 * - Tastatur: ↑/↓ (überspringt disabled), Home/End, Enter/Space wählt,
 *   Esc schliesst, Type-ahead auf Label-Anfangsbuchstaben. Fokus bleibt auf
 *   dem Trigger (`aria-activedescendant`-Muster), darum keine Fokus-Falle.
 * - Aussenklick schliesst (mousedown-Muster von KMenu, touch-tauglich).
 * - Bewegung: Popup öffnet mit `.k-einblenden` (aura.css) — der globale
 *   `prefers-reduced-motion`-Killswitch dämpft das automatisch, kein
 *   Sonderfall hier.
 *
 * API bleibt DROP-IN-kompatibel zur nativen Ära: `value`/`defaultValue`/
 * `onChange` + `<option>`-CHILDREN (Entscheid: children-Parsing statt
 * options-Prop, weil ALLE ~36 Verwendungsstellen bereits `<option>`-Kinder
 * übergeben, teils konditional gerendert). `onChange` erhält ein
 * synthetisches Event, dessen `target.value`/`currentTarget.value` gesetzt
 * sind — mehr liest keine Verwendungsstelle. Ein `onChange` feuert (nativ-
 * treu) nur bei tatsächlichem Wertwechsel. `multiple`/`<optgroup>` werden im
 * Custom-Modus nicht unterstützt — dafür (und für andere Sonderfälle, in
 * denen das Betriebssystem-Popup zwingend ist) gibt es die `nativ`-Prop.
 *
 * `style` wird deterministisch GESPLITTET: Layout-Schlüssel (width/flex/
 * position/margin/…) wandern auf den Wrapper (der die Layout-Rolle des
 * früheren `<select>` übernimmt), alle übrigen (padding/font/color/…) auf
 * den Trigger. Damit bleiben `style={{ width: '100%' }}`-Verwender pixel-
 * kompatibel.
 */
export interface KSelectProps extends Omit<SelectHTMLAttributes<HTMLSelectElement>, 'size'> {
  size?: 'sm' | 'md';
  /** true → natives `<select>` wie vor v0.6.9 (Sonderfälle). Default: custom. */
  nativ?: boolean;
  'data-testid'?: string;
}

interface OptionEintrag {
  value: string;
  label: string;
  disabled: boolean;
}

/** Flacht die `<option>`-children eines Labels zu reinem Text (Labels wie
 * `{name} ({masse})` kommen als Arrays aus Strings/Zahlen an). */
function textVon(knoten: ReactNode): string {
  if (knoten === null || knoten === undefined || typeof knoten === 'boolean') return '';
  if (typeof knoten === 'string' || typeof knoten === 'number') return String(knoten);
  if (Array.isArray(knoten)) return knoten.map(textVon).join('');
  if (isValidElement(knoten)) return textVon((knoten.props as { children?: ReactNode }).children);
  return '';
}

/** Liest die `<option>`-Kinder in eine flache Options-Liste (nur direkte
 * `<option>`-Elemente — kein `<optgroup>` im Bestand, s. Doc-Kommentar). */
function leseOptionen(children: ReactNode): OptionEintrag[] {
  const liste: OptionEintrag[] = [];
  Children.forEach(children, (kind) => {
    if (!isValidElement(kind) || kind.type !== 'option') return;
    const p = kind.props as OptionHTMLAttributes<HTMLOptionElement>;
    const label = textVon(p.children);
    const value = p.value !== undefined ? String(p.value) : label;
    liste.push({ value, label, disabled: p.disabled === true });
  });
  return liste;
}

/** Layout-Schlüssel → Wrapper; Rest (Optik) → Trigger. S. Doc-Kommentar. */
const WRAP_STYLE_KEYS = new Set([
  'display', 'width', 'minWidth', 'maxWidth', 'flex', 'flexGrow', 'flexShrink',
  'flexBasis', 'alignSelf', 'justifySelf', 'gridColumn', 'gridRow', 'order',
  'position', 'top', 'right', 'bottom', 'left', 'zIndex',
  'margin', 'marginTop', 'marginRight', 'marginBottom', 'marginLeft',
]);

function splitStyle(style: CSSProperties | undefined): { wrap: CSSProperties; trigger: CSSProperties } {
  const wrap: Record<string, unknown> = {};
  const trigger: Record<string, unknown> = {};
  if (style) {
    for (const [k, v] of Object.entries(style)) {
      if (WRAP_STYLE_KEYS.has(k)) wrap[k] = v;
      else trigger[k] = v;
    }
  }
  return { wrap: wrap as CSSProperties, trigger: trigger as CSSProperties };
}

function syntheticChange(value: string): ChangeEvent<HTMLSelectElement> {
  const ziel = { value } as unknown as EventTarget & HTMLSelectElement;
  return { target: ziel, currentTarget: ziel, type: 'change' } as unknown as ChangeEvent<HTMLSelectElement>;
}

/**
 * P-ANKER (W5′, Urteil `docs/URTEIL-SCHLIESS-WACHE-2026-08-23.md`): Lage der
 * portalierten Listbox aus dem aktuellen Trigger-Rechteck — dieselbe
 * Rechnung wie in `oeffne()` beim ersten Öffnen, jetzt auch für jede
 * Neuberechnung bei Scroll/Resize (s. `schliesseScroll` unten).
 */
/**
 * Zwei echte Formen statt eines Objekts mit zwei optionalen Feldern: die
 * Nach-oben-Form trägt `top: 'auto'` MIT, statt es dem Aufrufer zu
 * überlassen. Grund (Befund `docs/BEFUND-KSELECT-AUFKLAPPEN-2026-08-26.md`):
 * `.k-menu` in `aura.css` trägt aus ihrer `position:absolute`-Zeit noch ein
 * eigenes `top: calc(100% + var(--k-s2))`. Bei `position:fixed` löst `100%`
 * gegen die Fensterhöhe auf, nicht gegen den früheren Elternkasten — ohne
 * ein explizites `top: 'auto'` im Inline-Style gewinnt diese CSS-Regel und
 * das korrekt berechnete `bottom` wird wirkungslos. Das Inline-`style` unten
 * setzt `top` darum IMMER (nie mehr bedingt durch `'top' in popupLage`).
 */
type PopupLage =
  | { left: number; breite: number; top: number }
  | { left: number; breite: number; top: 'auto'; bottom: number };

function berechnePopupLage(triggerRect: DOMRect): PopupLage {
  const platzUnten = window.innerHeight - triggerRect.bottom;
  const nachOben = platzUnten < 292 && triggerRect.top > platzUnten;
  return nachOben
    ? {
        left: triggerRect.left,
        top: 'auto',
        bottom: window.innerHeight - triggerRect.top + 2,
        breite: triggerRect.width,
      }
    : { left: triggerRect.left, top: triggerRect.bottom + 2, breite: triggerRect.width };
}

/**
 * P-ANKER: das Sichtbarkeits-Prädikat der harten Kante aus dem Urteil.
 * Kandidat «Rechteck-Schnitt mit allen Clip-Vorfahren» — GEMESSEN gegen den
 * Alternativ-Kandidaten `elementFromPoint(trigger-Zentrum)` an den drei
 * echten Behältern `.kp-einstellungen`/`.isl-fenster`/Viewport-Clip
 * (`.isl-popup` selbst clippt nicht, s. E-10-Kommentar in `island.css`) mit
 * teilweise geklipptem Trigger — Messprotokoll im Bau-Bericht. Ergebnis:
 * der Rechteck-Schnitt traf in 86 von 86 Stichproben exakt die geometrische
 * Grundwahrheit (Trigger-Rechteck ∩ Sichtfenster-Rest). `elementFromPoint`
 * am Zentrum irrte 5×, IMMER als falsches Negativ genau dort, wo der Trigger
 * real noch zu ~6–27% sichtbar war (das Zentrum lag im geklippten Teil,
 * während ein Rand noch sichtbar blieb) — exakt der «zu eng»-Fehler, den das
 * Urteil als Rückfall in den heutigen Bug benennt. Der Rechteck-Schnitt
 * schliesst darum NUR, wenn das Trigger-Rechteck VOLLSTÄNDIG aus allen
 * Clip-Vorfahren (jeder Vorfahre mit `overflow-x`/`-y` ≠ `visible`) UND dem
 * Viewport heraus ist — deckungsgleich mit Abnahme 4 des Urteils
 * («weiterscrollen, bis der Trigger den Clip verlässt»).
 */
function triggerSichtbar(trigger: HTMLElement): boolean {
  const rect = trigger.getBoundingClientRect();
  if (rect.width <= 0 || rect.height <= 0) return false;
  let links = 0;
  let oben = 0;
  let rechts = window.innerWidth;
  let unten = window.innerHeight;
  let knoten: HTMLElement | null = trigger.parentElement;
  while (knoten && knoten !== document.body && knoten !== document.documentElement) {
    const stil = window.getComputedStyle(knoten);
    // '' (leer) ≠ 'visible', tritt aber in jsdom (Unit-Tests) für JEDES
    // Element ohne explizite overflow-Regel auf — ein echter Browser löst
    // das immer auf einen konkreten Wert auf ('visible' ist die
    // Initialeinstellung). Ein leerer String wird darum wie 'visible'
    // behandelt: die sichere Richtung ist "nicht klippen", nicht "alles
    // klippen" (sonst würde diese Wache in genau der Umgebung falsch
    // schliessen, in der sie getestet wird).
    const klipptX = stil.overflowX !== 'visible' && stil.overflowX !== '';
    const klipptY = stil.overflowY !== 'visible' && stil.overflowY !== '';
    if (klipptX || klipptY) {
      const r = knoten.getBoundingClientRect();
      if (klipptX) {
        links = Math.max(links, r.left);
        rechts = Math.min(rechts, r.right);
      }
      if (klipptY) {
        oben = Math.max(oben, r.top);
        unten = Math.min(unten, r.bottom);
      }
    }
    knoten = knoten.parentElement;
  }
  const l = Math.max(rect.left, links);
  const o = Math.max(rect.top, oben);
  const re = Math.min(rect.right, rechts);
  const u = Math.min(rect.bottom, unten);
  return re > l && u > o;
}

export function KSelect(props: KSelectProps) {
  const {
    size = 'md',
    nativ = false,
    className,
    style,
    children,
    value,
    defaultValue,
    onChange,
    disabled,
    'data-testid': testid,
    ...rest
  } = props;
  const klassen = ['k-select', `k-select--${size}`, className].filter(Boolean).join(' ');

  const [offen, setOffen] = useState(false);
  const [aktivIndex, setAktivIndex] = useState(0);
  // P-F6 (v0.9.2): fixe Lage der portalierten Listbox, berechnet beim
  // Öffnen aus dem Trigger-Rechteck (`oeffne()`); top-Variante = normal
  // nach unten, bottom-Variante = nach oben geklappt (Platzmangel).
  const [popupLage, setPopupLage] = useState<PopupLage | null>(null);
  const [intern, setIntern] = useState<string | undefined>(() =>
    defaultValue !== undefined ? String(defaultValue) : undefined,
  );
  const wrapRef = useRef<HTMLSpanElement | null>(null);
  const triggerRef = useRef<HTMLButtonElement | null>(null);
  const listeRef = useRef<HTMLDivElement | null>(null);
  const typeahead = useRef<{ puffer: string; zeit: number }>({ puffer: '', zeit: 0 });
  // P-ANKER: rAF-Drosselung für schliesseScroll — je Scroll-/Resize-Sequenz
  // höchstens ein angemeldeter Frame, statt getBoundingClientRect +
  // Zustandssetzung bei JEDEM Ereignis (Layout-Thrash, Urteil-Preis 3).
  const rafHandle = useRef<number | null>(null);
  const id = useId();

  const optionen = useMemo(() => leseOptionen(children), [children]);
  const gesteuert = value !== undefined;
  const wert = gesteuert ? String(value) : (intern ?? optionen[0]?.value ?? '');
  const gewaehlt = optionen.find((o) => o.value === wert);
  // Nativ-treu: kennt das select den Wert nicht, zeigt es die erste Option.
  const anzeige = gewaehlt?.label ?? optionen[0]?.label ?? '';

  // Aussenklick + Escape schliessen — exakt das KMenu-Muster (overlay.tsx).
  // P-F6 (v0.9.2): die Liste hängt seit dem Portal-Umbau an document.body —
  // der Aussenklick-Test muss BEIDE Wurzeln kennen (Trigger-Span UND
  // portaliertes Listbox-Div), sonst schlösse jeder Optionsklick sofort.
  useEffect(() => {
    if (!offen) return undefined;
    const schliesseAussen = (e: MouseEvent) => {
      const ziel = e.target as Node;
      const imTrigger = wrapRef.current?.contains(ziel) ?? false;
      const inListe = listeRef.current?.contains(ziel) ?? false;
      if (!imTrigger && !inListe) setOffen(false);
    };
    const schliesseEsc = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setOffen(false);
    };
    // P-ANKER (W5′, 23.08.2026, Urteil `docs/URTEIL-SCHLIESS-WACHE-2026-08-23.md`):
    // die Liste ist position:fixed — beim Scrollen/Resize irgendeines
    // Containers würde sie am alten Fleck schweben. Der frühere Vertrag hier
    // lautete «schliessen ist das ehrliche Standardverhalten — natives
    // <select> macht dasselbe»; DAS STIMMT AB HIER NICHT MEHR. Die tragende
    // Invariante der Wache war nie «schliessen bei Scroll», sondern «die
    // Liste darf nie losgelöst vom Trigger schweben» — Schliessen war nur
    // EINE Implementierung davon, und eine falsche: der Befund vom 23.08.
    // (`docs/BEFUND-SELECT-SCHLIESST-SICH-SELBST.md`) zeigte, dass ein
    // scrollbarer Vorfahre (z.B. `.kp-einstellungen`) beim blossen
    // Fokussieren des Triggers scrollt — KEIN Nutzer-Scroll, und das Popup
    // schloss sich mit seinem eigenen Öffnen. Ab hier gilt: bei Scroll/Resize
    // wird die Popup-Lage aus dem AKTUELLEN Trigger-Rechteck neu berechnet
    // (rAF-gedrosselt, `berechnePopupLage`) statt geschlossen. Geschlossen
    // wird nur noch, wenn der Trigger nach `triggerSichtbar` effektiv nicht
    // mehr sichtbar ist (vollständig aus allen Clip-Vorfahren UND dem
    // Viewport heraus — s. dortigen Kommentar für die Messung, die diese
    // Definition trägt). Damit ist die dokumentierte Divergenz zum nativen
    // `<select>` bewusst: Wheel/Touch FÜHRT DIE LISTE MIT, solange der
    // Trigger sichtbar bleibt — das Verhalten moderner Referenz-Dropdowns
    // (Radix/Floating UI u.ä.), kein Bugfix, ein Stilentscheid des Owners.
    // capture:true fängt auch Scrolls in inneren Overflow-Containern
    // (.isl-popup/.isl-fenster), die nie bis window bubbeln.
    const schliesseScroll = (e: Event) => {
      if (listeRef.current && e.target instanceof Node && listeRef.current.contains(e.target)) return;
      // Gemessener Befund (19.08.2026, Auftrag «zwei rote Journey-Stellen»,
      // Befund 1): steht der KSelect-Trigger in einem SVG-`<foreignObject>`
      // (NodeCanvas.tsx — Render-Formular, Stimmung-Preset, …), feuert der
      // Browser beim Fokussieren des Triggers (jeder Öffnen-Klick fokussiert
      // ihn) ein natives `scroll`-Ereignis AUF DEM foreignObject selbst —
      // ohne dass sich real irgendetwas verschiebt (Pan/Zoom in NodeCanvas
      // läuft ausschliesslich über die SVG-`viewBox`, nie über echtes
      // Scrollen/Overflow, s. NodeCanvas.tsx). Ein `SVGForeignObjectElement`
      // ist nie der Overflow-Container, den diese Wache eigentlich meint
      // (das sind `.isl-popup`/`.isl-fenster`, echte HTML-Elemente) — darum
      // hier gezielt ausgenommen, nicht die ganze Wache abgeschwächt.
      // P-ANKER (23.08.2026): bleibt VORERST stehen, auch nachdem Schliessen
      // durch Neuberechnen ersetzt wurde — Abnahme 5 (Regression 19.08., die
      // `foreignObject`-Fälle) wurde nicht ohne diese Ausnahme gegengeprüft
      // (offener Punkt, s. Bau-Bericht). Unter W5′ wäre ein Phantom-Scroll
      // vermutlich ein No-op (dasselbe Trigger-Rechteck), aber das ist eine
      // Vermutung, keine Messung — darum bleibt die Ausnahme, statt sie auf
      // Verdacht zu entfernen.
      if (typeof SVGForeignObjectElement !== 'undefined' && e.target instanceof SVGForeignObjectElement) return;
      if (rafHandle.current !== null) return; // schon ein Frame angemeldet
      rafHandle.current = window.requestAnimationFrame(() => {
        rafHandle.current = null;
        const trigger = triggerRef.current;
        if (!trigger) return;
        if (!triggerSichtbar(trigger)) {
          setOffen(false);
          return;
        }
        setPopupLage(berechnePopupLage(trigger.getBoundingClientRect()));
      });
    };
    document.addEventListener('mousedown', schliesseAussen);
    document.addEventListener('keydown', schliesseEsc);
    window.addEventListener('scroll', schliesseScroll, { capture: true, passive: true });
    window.addEventListener('resize', schliesseScroll);
    return () => {
      document.removeEventListener('mousedown', schliesseAussen);
      document.removeEventListener('keydown', schliesseEsc);
      window.removeEventListener('scroll', schliesseScroll, { capture: true } as EventListenerOptions);
      window.removeEventListener('resize', schliesseScroll);
      if (rafHandle.current !== null) {
        window.cancelAnimationFrame(rafHandle.current);
        rafHandle.current = null;
      }
    };
  }, [offen]);

  // Aktive Option in Sicht halten (Listbox scrollt ab maxHeight).
  // Gemessener Befund (23.08.2026, `docs/BEFUND-SELECT-SCHLIESST-SICH-SELBST.md`):
  // `scrollIntoView({ block: 'nearest' })` scrollt NICHT nur die Listbox,
  // sondern JEDEN scrollbaren Vorfahren, der die Option nicht schon zeigt —
  // steht der Trigger in einem scrollbaren Behälter (z.B. `.kp-einstellungen`),
  // scrollt der Browser diesen mit. Dessen `scroll`-Ereignis passiert
  // `schliesseScroll` oben (keine der beiden Ausnahmen dort trifft zu) und
  // schliesst das Popup — mit seinem eigenen Öffnen-Effekt. Reparatur: die
  // Absicht direkt schreiben (die Listbox scrollt "ab maxHeight", s.
  // Kommentar) statt sie `scrollIntoView` raten zu lassen — nur
  // `liste.scrollTop` anfassen, nie einen Vorfahren. Deckt dieselben drei
  // Fälle wie `nearest` ab: Option oberhalb → an den oberen Rand holen;
  // Option unterhalb → an den unteren Rand holen; Option schon sichtbar →
  // keine der beiden Bedingungen trifft, `scrollTop` bleibt unangetastet.
  useEffect(() => {
    if (!offen) return;
    const liste = listeRef.current;
    const el = liste?.querySelector<HTMLElement>(`[data-index="${aktivIndex}"]`);
    if (!liste || !el) return;
    const elOben = el.offsetTop;
    const elUnten = elOben + el.offsetHeight;
    const sichtOben = liste.scrollTop;
    const sichtUnten = sichtOben + liste.clientHeight;
    if (elOben < sichtOben) {
      liste.scrollTop = elOben;
    } else if (elUnten > sichtUnten) {
      liste.scrollTop = elUnten - liste.clientHeight;
    }
    // sonst: Option ist bereits vollständig sichtbar — nichts bewegt sich
    // (das ist die Bedeutung von "nearest").
  }, [offen, aktivIndex]);

  if (nativ) {
    return (
      <select
        {...rest}
        {...(testid !== undefined ? { 'data-testid': testid } : {})}
        {...(value !== undefined ? { value } : {})}
        {...(defaultValue !== undefined ? { defaultValue } : {})}
        {...(onChange !== undefined ? { onChange } : {})}
        {...(disabled !== undefined ? { disabled } : {})}
        {...(style !== undefined ? { style } : {})}
        className={klassen}
      >
        {children}
      </select>
    );
  }

  const naechsterWaehlbare = (start: number, richtung: 1 | -1): number => {
    let i = start;
    while (i >= 0 && i < optionen.length) {
      if (!optionen[i]!.disabled) return i;
      i += richtung;
    }
    return -1;
  };

  const oeffne = (zielIndex?: number) => {
    const startIndex =
      zielIndex ?? Math.max(0, optionen.findIndex((o) => o.value === wert));
    setAktivIndex(startIndex);
    // P-F6 (v0.9.2, Owner-Feedback/P-F4-Fund): Lage der portalierten Liste
    // aus dem Trigger-Rechteck — position:fixed entkommt jedem
    // overflow:auto-Vorfahren (die Insel-Popups .isl-popup/.isl-fenster
    // klippten den absoluten Dropdown, island.css §Stufe 3). Unten öffnen
    // ist der Normalfall; reicht der Platz unter dem Trigger nicht für die
    // maxHeight (280) UND ist oben mehr Luft, klappt die Liste nach oben
    // (bottom-verankert — die tatsächliche Listenhöhe ist vor dem Render
    // nicht bekannt, der Anker braucht sie nicht). P-ANKER (23.08.2026): die
    // Rechnung steht jetzt EINMAL in `berechnePopupLage` — dieselbe Funktion
    // trägt auch die Neupositionierung bei Scroll/Resize (s. oben).
    const r = triggerRef.current?.getBoundingClientRect();
    setPopupLage(r ? berechnePopupLage(r) : null);
    setOffen(true);
  };

  const waehle = (v: string) => {
    setOffen(false);
    triggerRef.current?.focus();
    if (!gesteuert) setIntern(v);
    if (v !== wert) onChange?.(syntheticChange(v));
  };

  const tastatur = (e: ReactKeyboardEvent<HTMLButtonElement>) => {
    if (!offen) {
      if (e.key === 'ArrowDown' || e.key === 'ArrowUp' || e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        oeffne();
      } else if (e.key === 'Home') {
        e.preventDefault();
        oeffne(Math.max(0, naechsterWaehlbare(0, 1)));
      } else if (e.key === 'End') {
        e.preventDefault();
        oeffne(Math.max(0, naechsterWaehlbare(optionen.length - 1, -1)));
      }
      return;
    }
    if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
      e.preventDefault();
      const richtung: 1 | -1 = e.key === 'ArrowDown' ? 1 : -1;
      const neu = naechsterWaehlbare(aktivIndex + richtung, richtung);
      if (neu >= 0) setAktivIndex(neu);
    } else if (e.key === 'Home') {
      e.preventDefault();
      const neu = naechsterWaehlbare(0, 1);
      if (neu >= 0) setAktivIndex(neu);
    } else if (e.key === 'End') {
      e.preventDefault();
      const neu = naechsterWaehlbare(optionen.length - 1, -1);
      if (neu >= 0) setAktivIndex(neu);
    } else if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      const o = optionen[aktivIndex];
      if (o && !o.disabled) waehle(o.value);
    } else if (e.key === 'Escape') {
      // Der document-Listener oben schliesst ebenfalls — hier zusätzlich
      // stoppen, damit kein umgebendes Overlay (Dialog/Menü) mitschliesst.
      e.stopPropagation();
      setOffen(false);
    } else if (e.key === 'Tab') {
      setOffen(false);
    } else if (e.key.length === 1 && !e.ctrlKey && !e.metaKey && !e.altKey) {
      // Type-ahead: Anfangsbuchstaben sammeln (500ms-Fenster).
      const jetzt = Date.now();
      const t = typeahead.current;
      t.puffer = jetzt - t.zeit > 500 ? e.key.toLowerCase() : t.puffer + e.key.toLowerCase();
      t.zeit = jetzt;
      const treffer = optionen.findIndex(
        (o) => !o.disabled && o.label.toLowerCase().startsWith(t.puffer),
      );
      if (treffer >= 0) setAktivIndex(treffer);
    }
  };

  const { wrap: wrapStyle, trigger: triggerStyle } = splitStyle(style);
  const popupId = `${id}-listbox`;

  return (
    <span ref={wrapRef} style={{ position: 'relative', display: 'inline-block', ...wrapStyle }}>
      <button
        {...(rest as Record<string, unknown>)}
        ref={triggerRef}
        type="button"
        className={klassen}
        role="combobox"
        aria-haspopup="listbox"
        aria-expanded={offen}
        aria-controls={popupId}
        {...(offen ? { 'aria-activedescendant': `${id}-opt-${aktivIndex}` } : {})}
        {...(testid !== undefined ? { 'data-testid': testid } : {})}
        data-value={wert}
        disabled={disabled ?? false}
        // Gemessener Befund (23.08.2026, `docs/BEFUND-SELECT-SCHLIESST-SICH-SELBST.md`,
        // hier per Diagnose-Sonde WEITER eingegrenzt): die eigentliche Ursache
        // der 252px-Fremdverschiebung ist NICHT der «Option in Sicht
        // halten»-Effekt oben (der trifft nach der Reparatur nie mehr einen
        // Vorfahren) — sie ist der BROWSER-EIGENE Standard-Scroll beim
        // Fokussieren: steht dieser Trigger tief in einem scrollbaren
        // Behälter (z.B. `.kp-einstellungen`, «Modell» ist dort das letzte
        // Feld), scrollt Chromium den Behälter beim Fokuswechsel automatisch
        // an — auch bei einem simplen Mausklick, VÖLLIG unabhängig davon, ob
        // überhaupt ein Popup öffnet (reproduziert mit `trigger.focus()`
        // allein, ohne jeden Klick: derselbe Scroll, dieselben ~260ms
        // Verzögerung, derselbe Wert). Dieses Scroll-Ereignis passiert
        // `schliesseScroll` (keine der beiden dortigen Ausnahmen trifft zu)
        // und schliesst das Popup mit dem eigenen Öffnen. Der Browser bietet
        // dafür einen echten Schalter: `preventDefault()` auf `mousedown`
        // unterdrückt NUR den impliziten Fokus-mit-Scroll (keine Wirkung auf
        // den nachfolgenden `click`); `focus({ preventScroll: true })` holt
        // den Fokus danach gezielt OHNE die Scroll-Nebenwirkung nach. Damit
        // scrollt beim Öffnen weder ein Vorfahre noch die Listbox unnötig —
        // keine weitere Ausnahme in `schliesseScroll` nötig.
        onMouseDown={(e) => {
          e.preventDefault();
          triggerRef.current?.focus({ preventScroll: true });
        }}
        onClick={() => (offen ? setOffen(false) : oeffne())}
        onKeyDown={tastatur}
        style={{
          font: 'inherit',
          textAlign: 'left',
          display: 'block',
          width: '100%',
          boxSizing: 'border-box',
          whiteSpace: 'nowrap',
          overflow: 'hidden',
          textOverflow: 'ellipsis',
          ...triggerStyle,
        }}
      >
        {anzeige === '' ? ' ' : anzeige}
      </button>
      {offen &&
        // P-F6 (v0.9.2): Listbox als body-Portal mit fixer Lage aus dem
        // Trigger-Rechteck — entkommt den overflow-Klippen der Insel-Popups
        // (P-F4-Fund, island.css:410/446 ↔ vorher position:absolute hier).
        // z-index unter der CursorEbene (2147483000), über allen Fenstern.
        createPortal(
        <div
          ref={listeRef}
          id={popupId}
          role="listbox"
          // Marker für fremde Aussenklick-Gesetze (useOverlaySchliessen):
          // die Listbox liegt als body-Portal AUSSERHALB jedes Overlay-DOMs —
          // ohne diesen Anker würde ein mousedown auf eine Option das
          // umgebende Overlay (Insel-Popup, Orb-Karte, …) schliessen und den
          // KSelect mitten in der Wahl unmounten (E2E-Befund island-leer,
          // Trace-Ziel: Wahl verpuffte, Insel klappte zu).
          data-kselect-portal=""
          {...(testid !== undefined ? { 'data-testid': `${testid}-popup` } : {})}
          className="k-menu offen k-einblenden"
          style={{
            position: 'fixed',
            zIndex: 2147482000,
            ...(popupLage
              ? {
                  left: popupLage.left,
                  minWidth: popupLage.breite,
                  // `top` wird IMMER gesetzt (auch 'auto' im Flip-Fall) —
                  // das überschreibt das `top: calc(100% + …)` aus
                  // `.k-menu` (aura.css), das bei `position:fixed` sonst
                  // gegen die Fensterhöhe auflöst und `bottom` wirkungslos
                  // macht. S. Befund-Dok im Kommentar bei `berechnePopupLage`.
                  top: popupLage.top,
                  ...(popupLage.top === 'auto' ? { bottom: popupLage.bottom } : {}),
                }
              : { minWidth: '100%' }),
            maxWidth: 'min(420px, 80vw)',
            maxHeight: 280,
            overflowY: 'auto',
            overflowX: 'hidden',
          }}
        >
          {optionen.map((o, i) => (
            <button
              // Werte dürfen doppelt/leer sein — Index gehört zur Identität.
              key={`${o.value}-${i}`}
              id={`${id}-opt-${i}`}
              type="button"
              role="option"
              aria-selected={o.value === wert}
              data-value={o.value}
              data-index={i}
              disabled={o.disabled}
              tabIndex={-1}
              className="k-menu-item"
              onMouseEnter={() => setAktivIndex(i)}
              // D-8 (Touch/Fokus-Fallback, Fund D8-MOUSEENTER): ohne
              // `onFocus` blieb `aktivIndex` bei Tastatur-Fokus dieses
              // konkreten Buttons (z.B. programmatischer Fokus) an
              // `onMouseEnter` allein hängen — Pfeiltasten am Listbox-
              // Container (`tastatur`, oben) setzen `aktivIndex` bereits
              // unabhängig, dieser Fallback deckt den verbleibenden Fall ab.
              onFocus={() => setAktivIndex(i)}
              onClick={(e) => {
                // Steckt das KSelect in einem <label> (verbreitet: «Phase»,
                // «Verbindung», …), löst der Browser als Default-Action des
                // Klicks einen synthetischen Klick aufs Label-Control (den
                // Trigger) aus, sobald die geklickte Option nach dem React-
                // Commit nicht mehr im DOM hängt — das Popup ginge sofort
                // wieder auf. preventDefault unterbindet genau das.
                e.preventDefault();
                waehle(o.value);
              }}
              style={{
                fontSize: size === 'sm' ? 'var(--k-t-sm)' : 'var(--k-t-md)',
                whiteSpace: 'nowrap',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                display: 'block',
                textAlign: 'left',
                ...(i === aktivIndex ? { background: 'var(--k-surface)' } : {}),
                ...(o.value === wert ? { fontWeight: 'var(--k-gewicht-stark)' } : {}),
              }}
            >
              {o.label === '' ? ' ' : o.label}
            </button>
          ))}
        </div>,
          document.body,
        )}
    </span>
  );
}
