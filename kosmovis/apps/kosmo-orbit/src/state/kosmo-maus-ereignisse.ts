/**
 * KosmoMaus — die synthetischen Ereignisse (Owner-Entscheid E157).
 *
 * Owner wörtlich: «nicht fernsteuerung meiner maus sondern einer eigenen
 * innerhalb der software die mich nicht tangiert». Darum geht hier ALLES über
 * `dispatchEvent` im Dokument der App:
 *
 *  - kein Betriebssystem-Zeiger, kein `ydotool`/`xdotool`, keine Tauri-
 *    Fensterfunktion, kein `requestPointerLock`;
 *  - der echte Zeiger des Architekten bleibt, wo er ist; sein Klick geht
 *    weiter an dieselben Elemente;
 *  - jedes Ereignis trägt `isTrusted === false` — daran erkennt die App, dass
 *    es nicht vom Menschen kam (Esc beendet nur der echte Druck, der
 *    Freigabe-Schalter nimmt nur echte Klicks).
 *
 * Eigene Zeiger-Kennung (`AGENT_POINTER_ID`): Zieh-Handler rufen gern
 * `setPointerCapture(e.pointerId)`. Für eine Kennung, die der Browser nicht
 * kennt, wirft das. Während einer Agenten-Handlung fängt
 * `mitEigenemCapture` genau diese Kennung ab und merkt sich das Ziel —
 * folgende Bewegungen gehen dann an dieses Element, wie bei einem echten
 * Capture. Alle anderen Kennungen (der echte Zeiger) laufen unverändert durch.
 */

export const AGENT_POINTER_ID = 9157;

let captureZiel: Element | null = null;
let captureTiefe = 0;
type CaptureProto = {
  setPointerCapture: ((id: number) => void) | undefined;
  releasePointerCapture: ((id: number) => void) | undefined;
  hasPointerCapture: ((id: number) => boolean) | undefined;
};
let captureAlt: { setzen: CaptureProto['setPointerCapture']; loesen: CaptureProto['releasePointerCapture']; hat: CaptureProto['hasPointerCapture'] } | null = null;

function captureAn(): void {
  if (captureTiefe++ > 0) return;
  const proto = Element.prototype as unknown as CaptureProto;
  const alt = { setzen: proto.setPointerCapture, loesen: proto.releasePointerCapture, hat: proto.hasPointerCapture };
  captureAlt = alt;
  proto.setPointerCapture = function (this: Element, id: number) {
    if (id === AGENT_POINTER_ID) {
      captureZiel = this;
      return;
    }
    return alt.setzen?.call(this, id);
  };
  proto.releasePointerCapture = function (this: Element, id: number) {
    if (id === AGENT_POINTER_ID) {
      if (captureZiel === this) captureZiel = null;
      return;
    }
    return alt.loesen?.call(this, id);
  };
  proto.hasPointerCapture = function (this: Element, id: number) {
    if (id === AGENT_POINTER_ID) return captureZiel === this;
    return alt.hat ? alt.hat.call(this, id) : false;
  };
}

function captureAus(): void {
  if (--captureTiefe > 0 || !captureAlt) return;
  const proto = Element.prototype as unknown as CaptureProto;
  proto.setPointerCapture = captureAlt.setzen;
  proto.releasePointerCapture = captureAlt.loesen;
  proto.hasPointerCapture = captureAlt.hat;
  captureAlt = null;
}

/** Führt `f` aus, während `setPointerCapture` für die Agenten-Kennung abgefangen ist. */
export function mitEigenemCapture<T>(f: () => T): T {
  captureAn();
  try {
    return f();
  } finally {
    captureAus();
  }
}

/** Wie `mitEigenemCapture`, aber über Pausen hinweg (Drücken … Loslassen). */
export async function mitEigenemCaptureUeberPausen<T>(f: () => Promise<T>): Promise<T> {
  captureAn();
  try {
    return await f();
  } finally {
    captureAus();
  }
}

export function vergissCapture(): void {
  captureZiel = null;
}

interface Punkt {
  x: number;
  y: number;
}

export interface Tasten {
  ctrlKey?: boolean;
  shiftKey?: boolean;
  altKey?: boolean;
  metaKey?: boolean;
}

function mausInit(p: Punkt, button: number, buttons: number, t: Tasten = {}, detail = 0): MouseEventInit {
  return {
    bubbles: true,
    cancelable: true,
    composed: true,
    clientX: p.x,
    clientY: p.y,
    screenX: p.x,
    screenY: p.y,
    button,
    buttons,
    detail,
    ...t,
  };
}

/** Zusätze für Über-/Verlassen-Ereignisse: woher bzw. wohin, und ob sie aufsteigen (enter/leave nicht). */
interface Wechsel {
  relatedTarget?: Element | null;
  bubbles?: boolean;
}

function zeigerEreignis(typ: string, p: Punkt, button: number, buttons: number, t?: Tasten, w: Wechsel = {}): Event {
  const init = {
    ...mausInit(p, button, buttons, t),
    ...wechselInit(w),
    pointerId: AGENT_POINTER_ID,
    pointerType: 'mouse',
    isPrimary: true,
    width: 1,
    height: 1,
    pressure: buttons ? 0.5 : 0,
  };
  // jsdom kennt `PointerEvent` je nach Fassung nicht; dann trägt ein
  // MouseEvent desselben Namens die Daten (React liest nur Typ und Koordinaten).
  if (typeof PointerEvent === 'function') return new PointerEvent(typ, init);
  const e = new MouseEvent(typ, init);
  Object.defineProperty(e, 'pointerId', { value: AGENT_POINTER_ID });
  Object.defineProperty(e, 'pointerType', { value: 'mouse' });
  Object.defineProperty(e, 'isPrimary', { value: true });
  return e;
}

function wechselInit(w: Wechsel): MouseEventInit {
  return {
    ...(w.relatedTarget !== undefined ? { relatedTarget: w.relatedTarget } : {}),
    ...(w.bubbles === false ? { bubbles: false, cancelable: false } : {}),
  };
}

function mausEreignis(typ: string, p: Punkt, t: Tasten = {}, w: Wechsel = {}): MouseEvent {
  return new MouseEvent(typ, { ...mausInit(p, 0, 0, t), ...wechselInit(w) });
}

// ---------------------------------------------------------------------------
// Schweben: wo der Zeiger der KosmoMaus gerade steht (lw-kosmomaus-schweben)
// ---------------------------------------------------------------------------

/**
 * lw-kosmomaus-schweben (14.10.2026): Hover-Menüs (Fächer der Kugeln in der
 * Zentrale) gingen mit der KosmoMaus nicht. `klick` schickte nur `over` und
 * `move` ans Ziel, nie ein Verlassen am vorigen; `ziehen` gar kein `mouseover`.
 * Jetzt merkt sich die KosmoMaus das Element, über dem ihr Zeiger steht. Jede
 * Bewegung an ein anderes Element schickt, in der Reihenfolge eines Browsers,
 * `pointerout`/`pointerleave` und `mouseout`/`mouseleave` am bisherigen und
 * `pointerover`/`pointerenter` und `mouseover`/`mouseenter` am neuen (die
 * enter/leave je Vorfahre, der nur auf einer Seite liegt). `relatedTarget`
 * trägt die andere Seite — so erkennt React (`onMouseEnter`/`-Leave`), ob der
 * Zeiger einen Knoten wirklich verlässt.
 */
let schwebeZiel: Element | null = null;

/** Das Element, über dem der Zeiger der KosmoMaus zuletzt stand (oder `null`). */
export function zuletztGeschwebt(): Element | null {
  return schwebeZiel?.isConnected ? schwebeZiel : null;
}

/** Nur für Proben: der Zeiger steht nirgends (ohne Ereignisse). */
export function vergissSchweben(): void {
  schwebeZiel = null;
}

function vorfahren(el: Element): Element[] {
  const liste: Element[] = [];
  for (let e: Element | null = el; e; e = e.parentElement) liste.push(e);
  return liste;
}

/** Zeiger von seinem bisherigen Element auf `neu`: Verlassen dort, Betreten hier. */
function wechsleSchwebeZiel(neu: Element, p: Punkt, t: Tasten = {}): void {
  const alt = zuletztGeschwebt();
  schwebeZiel = neu;
  if (alt === neu) return;
  const neuKette = vorfahren(neu);
  const altKette = alt ? vorfahren(alt) : [];
  // Ohne bisheriges Element kommt der Zeiger «von aussen» (relatedTarget null) — wie bisher.
  const verlassen = altKette.filter((e) => !neuKette.includes(e));
  const betreten = neuKette.filter((e) => !altKette.includes(e)).reverse();
  if (alt) {
    alt.dispatchEvent(zeigerEreignis('pointerout', p, 0, 0, t, { relatedTarget: neu }));
    for (const e of verlassen) e.dispatchEvent(zeigerEreignis('pointerleave', p, 0, 0, t, { relatedTarget: neu, bubbles: false }));
  }
  neu.dispatchEvent(zeigerEreignis('pointerover', p, 0, 0, t, { relatedTarget: alt }));
  for (const e of betreten) e.dispatchEvent(zeigerEreignis('pointerenter', p, 0, 0, t, { relatedTarget: alt, bubbles: false }));
  if (alt) {
    alt.dispatchEvent(mausEreignis('mouseout', p, t, { relatedTarget: neu }));
    for (const e of verlassen) e.dispatchEvent(mausEreignis('mouseleave', p, t, { relatedTarget: neu, bubbles: false }));
  }
  neu.dispatchEvent(mausEreignis('mouseover', p, t, { relatedTarget: alt }));
  for (const e of betreten) e.dispatchEvent(mausEreignis('mouseenter', p, t, { relatedTarget: alt, bubbles: false }));
}

/** Ziel einer Bewegung: das Capture-Element, sonst was unter dem Punkt liegt. */
function zielAm(p: Punkt, rueckfall: Element): Element {
  if (captureZiel && captureZiel.isConnected) return captureZiel;
  const unten = typeof document.elementFromPoint === 'function' ? document.elementFromPoint(p.x, p.y) : null;
  return unten ?? rueckfall;
}

function fokussiere(el: Element): void {
  const f = (el as HTMLElement).closest?.(
    'input, textarea, select, button, a[href], [tabindex], [contenteditable="true"]',
  ) as HTMLElement | null;
  f?.focus({ preventScroll: true });
}

/**
 * kosmo-maus-4 (Geräteprobe 1745, Befund 4): ein KosmoMaus-Klick in den
 * Grundriss bei bestehender Auswahl wurde zweimal zur Karte «Verschieben um
 * …», der Betrag = Weg vom VORIGEN zum neuen Klickpunkt.
 *
 * URSACHE: Drücken und Loslassen kamen in EINER Aufgabe, ohne Pause. Der
 * Grundriss (PlanView → DesignWorkspace) merkt sich beim Drücken den
 * Startpunkt im React-Zustand (`setDragEntity`) und liest ihn beim Loslassen
 * aus seinen Handlern (`handlersRef`, beim Zeichnen neu gesetzt). React
 * verarbeitet den Druck aber erst nach der laufenden Aufgabe. Beim
 * Loslassen galten darum noch die Handler von VORHER: der Startpunkt war der
 * des vorigen Klicks (dort nie aufgeräumt, weil auch jenes Loslassen die
 * alten Handler sah). Ergebnis: ein Zug vom alten zum neuen Punkt.
 * Die Ereignisfolge selbst war richtig (Bewegung ohne Taste, `buttons` 0,
 * dann Drücken, Loslassen, `click` am selben Punkt).
 *
 * LÖSUNG: wie eine echte Maus mit kurzer Pause nach der Bewegung und
 * zwischen Drücken und Loslassen (`DRUCK_PAUSE_MS`). Dann hat die App den
 * Druck verarbeitet, bevor losgelassen wird.
 */
export const DRUCK_PAUSE_MS = 30;
/** Pause zwischen zwei Zwischenschritten beim Ziehen. */
export const ZIEH_SCHRITT_MS = 16;

function pause(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/** Zeiger an den Punkt, ohne gedrückte Taste (`buttons` 0). */
function hinZu(el: Element, p: Punkt, t: Tasten = {}): void {
  wechsleSchwebeZiel(el, p, t);
  el.dispatchEvent(zeigerEreignis('pointermove', p, 0, 0, t));
  el.dispatchEvent(new MouseEvent('mousemove', mausInit(p, 0, 0, t)));
}

function druecken(el: Element, p: Punkt, t: Tasten, detail: number): void {
  const runter = el.dispatchEvent(zeigerEreignis('pointerdown', p, 0, 1, t));
  const mausRunter = el.dispatchEvent(new MouseEvent('mousedown', mausInit(p, 0, 1, t, detail)));
  if (runter && mausRunter) fokussiere(el);
}

function loslassen(el: Element, p: Punkt, t: Tasten, detail: number): void {
  const hoch = zielAm(p, el);
  hoch.dispatchEvent(zeigerEreignis('pointerup', p, 0, 0, t));
  hoch.dispatchEvent(new MouseEvent('mouseup', mausInit(p, 0, 0, t, detail)));
  vergissCapture();
  el.dispatchEvent(new MouseEvent('click', mausInit(p, 0, 0, t, detail)));
}

/**
 * Ein Klick in EINER Aufgabe (ohne Pause). Nur noch für `fangeDateiwahl`:
 * dort muss `input.click()` im selben Zug abgefangen werden. Alles andere
 * nimmt `klickMitPause`.
 */
export function klick(el: Element, p: Punkt, t: Tasten = {}, detail = 1): void {
  mitEigenemCapture(() => {
    hinZu(el, p, t);
    druecken(el, p, t, detail);
    loslassen(el, p, t, detail);
  });
}

/** Ein Klick wie von einer Maus: Zeiger hin, Pause, drücken, Pause, loslassen, `click`. */
export async function klickMitPause(el: Element, p: Punkt, t: Tasten = {}, detail = 1): Promise<void> {
  await mitEigenemCaptureUeberPausen(async () => {
    hinZu(el, p, t);
    await pause(DRUCK_PAUSE_MS);
    druecken(el, p, t, detail);
    await pause(DRUCK_PAUSE_MS);
    loslassen(el, p, t, detail);
  });
}

/** Schweben: der Zeiger fährt an den Punkt über `el`, ohne zu drücken (Hover). */
export function schweben(el: Element, p: Punkt): void {
  hinZu(el, p);
}

export async function doppelklick(el: Element, p: Punkt, t: Tasten = {}): Promise<void> {
  await klickMitPause(el, p, t, 1);
  await klickMitPause(el, p, t, 2);
  el.dispatchEvent(new MouseEvent('dblclick', mausInit(p, 0, 0, t, 2)));
}

export async function rechtsklick(el: Element, p: Punkt, t: Tasten = {}): Promise<void> {
  await mitEigenemCaptureUeberPausen(async () => {
    hinZu(el, p, t);
    await pause(DRUCK_PAUSE_MS);
    el.dispatchEvent(zeigerEreignis('pointerdown', p, 2, 2, t));
    el.dispatchEvent(new MouseEvent('mousedown', mausInit(p, 2, 2, t)));
    await pause(DRUCK_PAUSE_MS);
    el.dispatchEvent(zeigerEreignis('pointerup', p, 2, 0, t));
    el.dispatchEvent(new MouseEvent('mouseup', mausInit(p, 2, 0, t)));
    vergissCapture();
    el.dispatchEvent(new MouseEvent('contextmenu', mausInit(p, 2, 0, t)));
  });
}

/** Ziehen von `a` nach `b` in `schritte` Zwischenschritten, mit Pausen wie eine Hand. `t`: gehaltene Umschalter (lw-kosmomaus-tasten). */
export async function ziehen(el: Element, a: Punkt, b: Punkt, t: Tasten = {}, schritte = 8): Promise<void> {
  await mitEigenemCaptureUeberPausen(async () => {
    hinZu(el, a, t);
    await pause(DRUCK_PAUSE_MS);
    el.dispatchEvent(zeigerEreignis('pointerdown', a, 0, 1, t));
    el.dispatchEvent(new MouseEvent('mousedown', mausInit(a, 0, 1, t)));
    await pause(DRUCK_PAUSE_MS);
    for (let i = 1; i <= schritte; i++) {
      const p = { x: a.x + ((b.x - a.x) * i) / schritte, y: a.y + ((b.y - a.y) * i) / schritte };
      const z = zielAm(p, el);
      z.dispatchEvent(zeigerEreignis('pointermove', p, 0, 1, t));
      z.dispatchEvent(new MouseEvent('mousemove', mausInit(p, 0, 1, t)));
      await pause(ZIEH_SCHRITT_MS);
    }
    await pause(DRUCK_PAUSE_MS);
    const z = zielAm(b, el);
    z.dispatchEvent(zeigerEreignis('pointerup', b, 0, 0, t));
    z.dispatchEvent(new MouseEvent('mouseup', mausInit(b, 0, 0, t)));
    vergissCapture();
    // Nach dem Loslassen steht der Zeiger über dem, was am Endpunkt liegt.
    wechsleSchwebeZiel(zielAm(b, z), b, t);
  });
}

/**
 * lw-maus-rad-vollbild (Gerät-Nachprobe, Owner-App WebKitGTK): «rad» scrollte
 * nicht. URSACHE: ein künstliches `WheelEvent` (`isTrusted === false`) löst
 * im Browser kein Default-Scrollen aus — nur Handler der App sehen es.
 *
 * LÖSUNG: zuerst das Ereignis schicken. Ruft ein Element `preventDefault`
 * (3D-Viewport-Zoom, Plan-Zoom …), hat es das Rad selbst behandelt — dabei
 * bleibt es. Sonst scrollt die KosmoMaus wie der Browser: den nächsten
 * Vorfahren ab dem Ziel, der in diese Richtung noch scrollen kann
 * (`overflow` auto/scroll/overlay und Inhalt grösser als die Fläche; das
 * Dokument selbst über `document.scrollingElement`). Zeilen-Modus = Zeilenhöhe,
 * Seiten-Modus = sichtbare Höhe/Breite des Containers.
 */
export type RadErgebnis =
  | { art: 'app' }
  | { art: 'gescrollt'; kennung: string; vorher: Punkt; nachher: Punkt }
  | { art: 'nichts' };

const RAD_ZEILE_RUECKFALL_PX = 16;

function kannScrollen(el: Element, achse: 'x' | 'y', richtung: number): boolean {
  if (richtung === 0) return false;
  const istDokument = el === document.scrollingElement || el === document.documentElement;
  if (!istDokument) {
    const s = getComputedStyle(el);
    const ov = achse === 'y' ? s.overflowY || s.overflow : s.overflowX || s.overflow;
    if (!/(auto|scroll|overlay)/.test(ov)) return false;
  }
  const max = achse === 'y' ? el.scrollHeight - el.clientHeight : el.scrollWidth - el.clientWidth;
  if (max <= 0) return false;
  const jetzt = achse === 'y' ? el.scrollTop : el.scrollLeft;
  return richtung > 0 ? jetzt < max : jetzt > 0;
}

function zeilenHoehe(el: Element): number {
  const s = getComputedStyle(el);
  const lh = parseFloat(s.lineHeight);
  if (Number.isFinite(lh) && lh > 0) return lh;
  const fs = parseFloat(s.fontSize);
  return Number.isFinite(fs) && fs > 0 ? fs * 1.2 : RAD_ZEILE_RUECKFALL_PX;
}

function inPixel(el: Element, delta: number, modus: number, achse: 'x' | 'y'): number {
  if (modus === 1) return delta * zeilenHoehe(el);
  if (modus === 2) return delta * (achse === 'y' ? el.clientHeight : el.clientWidth);
  return delta;
}

/** Kurze Kennung eines Elements für die Antwort an den Agenten. */
export function elementKennung(el: Element): string {
  const testid = el.getAttribute('data-testid');
  if (testid) return `[${testid}]`;
  if (el.id) return `#${el.id}`;
  if (el === document.scrollingElement || el === document.documentElement) return 'Dokument';
  const klasse = typeof el.className === 'string' ? el.className.trim().split(/\s+/)[0] : '';
  return `${el.tagName.toLowerCase()}${klasse ? `.${klasse}` : ''}`;
}

function scrollZiel(el: Element, dx: number, dy: number): Element | null {
  for (let e: Element | null = el; e; e = e.parentElement) {
    if (kannScrollen(e, 'y', dy) || kannScrollen(e, 'x', dx)) return e;
  }
  const doc = document.scrollingElement;
  if (doc && (kannScrollen(doc, 'y', dy) || kannScrollen(doc, 'x', dx))) return doc;
  return null;
}

function begrenzt(wert: number, max: number): number {
  return Math.max(0, Math.min(Math.max(0, max), wert));
}

export function rad(el: Element, p: Punkt, dx: number, dy: number, t: Tasten = {}, modus = 0): RadErgebnis {
  const ereignis = new WheelEvent('wheel', { ...mausInit(p, 0, 0, t), deltaX: dx, deltaY: dy, deltaZ: 0, deltaMode: modus });
  const durch = el.dispatchEvent(ereignis);
  if (!durch || ereignis.defaultPrevented) return { art: 'app' };
  const ziel = scrollZiel(el, dx, dy);
  if (!ziel) return { art: 'nichts' };
  const vorher = { x: ziel.scrollLeft, y: ziel.scrollTop };
  if (dy !== 0) ziel.scrollTop = begrenzt(vorher.y + inPixel(ziel, dy, modus, 'y'), ziel.scrollHeight - ziel.clientHeight);
  if (dx !== 0) ziel.scrollLeft = begrenzt(vorher.x + inPixel(ziel, dx, modus, 'x'), ziel.scrollWidth - ziel.clientWidth);
  return { art: 'gescrollt', kennung: elementKennung(ziel), vorher, nachher: { x: ziel.scrollLeft, y: ziel.scrollTop } };
}

/** «Control+Shift+z» → Taste und Umschalter. */
export function zerlegeTaste(kombination: string): { key: string; tasten: Tasten } {
  const teile = kombination.split('+').map((s) => s.trim()).filter(Boolean);
  const key = teile.pop() ?? '';
  const tasten: Tasten = {};
  for (const t of teile.map((s) => s.toLowerCase())) {
    if (t === 'control' || t === 'ctrl' || t === 'strg') tasten.ctrlKey = true;
    else if (t === 'shift' || t === 'umschalt') tasten.shiftKey = true;
    else if (t === 'alt') tasten.altKey = true;
    else if (t === 'meta' || t === 'cmd' || t === 'command') tasten.metaKey = true;
  }
  return { key, tasten };
}

function codeFuer(key: string): string {
  if (/^[a-z]$/i.test(key)) return `Key${key.toUpperCase()}`;
  if (/^[0-9]$/.test(key)) return `Digit${key}`;
  if (key === ' ') return 'Space';
  return key;
}

export function taste(el: Element, kombination: string): { key: string; tasten: Tasten } {
  const z = zerlegeTaste(kombination);
  const init: KeyboardEventInit = { key: z.key, code: codeFuer(z.key), bubbles: true, cancelable: true, composed: true, ...z.tasten };
  el.dispatchEvent(new KeyboardEvent('keydown', init));
  el.dispatchEvent(new KeyboardEvent('keyup', init));
  return z;
}

/**
 * Text eingeben. React hört auf `input` und vergleicht mit dem zuletzt
 * gesehenen Wert — darum der Wert über den Setter des Prototyps, nicht über
 * die Instanz (sonst merkt React keine Änderung).
 */
/**
 * L23 (Demo 01, Lauf 2): Felder, die einen Zwischenstand nicht halten. Ein Zahlenfeld verwirft «3.» (kein gültiger
 * Wert) — Zeichen für Zeichen getippt wurde aus «3.8» eine 8 und aus «1968» eine 5; ein Datumsfeld nimmt nur einen
 * ganzen Tag, jeder Teil davon war leer (und das Sonnenfenster rechnete mit einem leeren Datum: «i.toArray is not a
 * function»). Diese Felder bekommen den ganzen Wert auf einmal, geprüft und in ihre Form gebracht.
 */
const GANZER_WERT = new Set(['number', 'date', 'time', 'datetime-local', 'month', 'week', 'range', 'color']);

/** Der Wert, wie ihn ein Feld dieses Typs annimmt — oder ein Fehler mit Satz statt eines still leeren Felds. */
export function feldWert(typ: string, text: string): string {
  const t = text.trim();
  if (typ === 'number' || typ === 'range') {
    const z = t.replace(/[’'\s]/g, '').replace(',', '.');
    if (!/^-?(\d+(\.\d*)?|\.\d+)$/.test(z)) throw new Error(`Zahlenfeld: «${text}» ist keine Zahl (z. B. 3.8 oder 3,8).`);
    return String(Number(z));
  }
  if (typ === 'date') {
    if (/^\d{4}-\d{2}-\d{2}$/.test(t)) return t;
    const m = /^(\d{1,2})\.(\d{1,2})\.(\d{4})$/.exec(t);
    if (m) return `${m[3]}-${m[2]!.padStart(2, '0')}-${m[1]!.padStart(2, '0')}`;
    throw new Error(`Datumsfeld: «${text}» ist kein Datum (z. B. 21.03.2026 oder 2026-03-21).`);
  }
  if (typ === 'time') {
    const m = /^(\d{1,2})[:.](\d{2})$/.exec(t);
    if (m) return `${m[1]!.padStart(2, '0')}:${m[2]}`;
    throw new Error(`Zeitfeld: «${text}» ist keine Uhrzeit (z. B. 10:00).`);
  }
  return t;
}

export function tippen(el: Element, text: string): void {
  if (el instanceof HTMLInputElement && GANZER_WERT.has(el.type)) {
    const wert = feldWert(el.type, text);
    el.focus({ preventScroll: true });
    const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')?.set;
    for (const zeichen of text) el.dispatchEvent(new KeyboardEvent('keydown', { key: zeichen, bubbles: true, cancelable: true, composed: true }));
    setter?.call(el, wert);
    if (el.value === '' && wert !== '') throw new Error(`Das Feld nimmt «${text}» nicht an (Grenzen oder Form des Felds).`);
    el.dispatchEvent(new InputEvent('input', { bubbles: true, data: wert, inputType: 'insertText' }));
    for (const zeichen of text) el.dispatchEvent(new KeyboardEvent('keyup', { key: zeichen, bubbles: true, cancelable: true, composed: true }));
    el.dispatchEvent(new Event('change', { bubbles: true }));
    return;
  }
  if (el instanceof HTMLInputElement || el instanceof HTMLTextAreaElement) {
    el.focus({ preventScroll: true });
    const proto = el instanceof HTMLInputElement ? HTMLInputElement.prototype : HTMLTextAreaElement.prototype;
    const setter = Object.getOwnPropertyDescriptor(proto, 'value')?.set;
    let start = el.value.length;
    let ende = el.value.length;
    try {
      start = el.selectionStart ?? start;
      ende = el.selectionEnd ?? ende;
    } catch {
      /* type=number u.a. kennen keine Auswahl */
    }
    for (const zeichen of text) {
      const init: KeyboardEventInit = { key: zeichen, bubbles: true, cancelable: true, composed: true };
      el.dispatchEvent(new KeyboardEvent('keydown', init));
      const neu = el.value.slice(0, start) + zeichen + el.value.slice(ende);
      setter?.call(el, neu);
      start += zeichen.length;
      ende = start;
      try {
        el.setSelectionRange(start, ende);
      } catch {
        /* siehe oben */
      }
      el.dispatchEvent(new InputEvent('input', { bubbles: true, data: zeichen, inputType: 'insertText' }));
      el.dispatchEvent(new KeyboardEvent('keyup', init));
    }
    el.dispatchEvent(new Event('change', { bubbles: true }));
    return;
  }
  if (el instanceof HTMLElement && el.isContentEditable) {
    el.focus({ preventScroll: true });
    // eslint-disable-next-line @typescript-eslint/no-deprecated -- der einzige Weg, der Undo und Auswahl im Editierfeld mitnimmt
    if (!document.execCommand?.('insertText', false, text)) el.textContent = (el.textContent ?? '') + text;
    el.dispatchEvent(new InputEvent('input', { bubbles: true, data: text, inputType: 'insertText' }));
    return;
  }
  throw new Error('Das Ziel ist kein Eingabefeld.');
}

/** Satz, wenn das Ziel keine Auswahl ist (kosmo-maus-1, unverändert). */
export const KEINE_AUSWAHLLISTE = 'Das Ziel ist keine Auswahlliste.';
/** So lange wartet `waehlen`, bis die Liste nach dem Öffnen da ist. */
export const LISTE_WARTEN_MS = 600;

const EIGENE_LISTE = '[role="combobox"], [role="listbox"], [role="radiogroup"]';

function mitteVon(el: Element): Punkt {
  const r = el.getBoundingClientRect();
  return { x: r.left + r.width / 2, y: r.top + r.height / 2 };
}

function optionText(o: Element): string {
  return (o.getAttribute('aria-label') ?? o.textContent ?? '').replace(/\s+/g, ' ').trim();
}

function findeOption(optionen: readonly Element[], wert: string): Element | undefined {
  const w = wert.trim();
  const klein = w.toLowerCase();
  return (
    optionen.find((o) => o.getAttribute('data-value') === w || (o as HTMLInputElement).value === w) ??
    optionen.find((o) => optionText(o) === w) ??
    optionen.find((o) => optionText(o).toLowerCase() === klein)
  );
}

/** Die Liste eines Combobox-Knopfs: über `aria-controls`, sonst `${testid}-popup`. */
function listeVon(combobox: Element): Element | null {
  const id = combobox.getAttribute('aria-controls');
  const perId = id ? document.getElementById(id) : null;
  if (perId) return perId;
  const testid = combobox.getAttribute('data-testid');
  return testid ? document.querySelector(`[data-testid="${testid}-popup"]`) : null;
}

async function warteAufListe(combobox: Element): Promise<Element | null> {
  const bis = Date.now() + LISTE_WARTEN_MS;
  for (;;) {
    const l = listeVon(combobox);
    if (l) return l;
    if (Date.now() > bis) return null;
    await pause(DRUCK_PAUSE_MS);
  }
}

/**
 * Eine Auswahl auf einen Wert oder eine Beschriftung setzen.
 *
 *  - `<select>`: Wert über den Setter, dann `input`/`change` (wie bisher);
 *  - kosmo-maus-4 (Geräteprobe 1745, e): eigene Auswahllisten — der
 *    Inspector-Umschalter «Vom Geschoss»/«Fix» ist ein `KSelect` aus
 *    `@kosmo/ui` (Knopf `role="combobox"`, Liste `role="listbox"` mit
 *    `role="option"`-Knöpfen als Portal). Auch `role="listbox"` und
 *    `role="radiogroup"` (`role="radio"`) direkt. Die Option wird wie von
 *    Hand gewählt: Knopf klicken (falls zu), Liste abwarten, Option klicken.
 *    Gesucht wird nach `data-value`, dann nach dem Text.
 *  - sonst: «Das Ziel ist keine Auswahlliste.»
 */
export async function waehlen(el: Element, wert: string): Promise<string> {
  if (el instanceof HTMLSelectElement) {
    const option = [...el.options].find((o) => o.value === wert) ?? [...el.options].find((o) => o.textContent?.trim() === wert);
    if (!option) throw new Error(`Die Auswahl hat keinen Eintrag «${wert}». Vorhanden: ${[...el.options].map((o) => o.textContent?.trim()).join(', ')}`);
    Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype, 'value')?.set?.call(el, option.value);
    el.dispatchEvent(new Event('input', { bubbles: true }));
    el.dispatchEvent(new Event('change', { bubbles: true }));
    return option.textContent?.trim() ?? option.value;
  }
  const auswahl = el.closest(EIGENE_LISTE) ?? el.querySelector(EIGENE_LISTE);
  if (!auswahl) throw new Error(KEINE_AUSWAHLLISTE);
  const rolle = auswahl.getAttribute('role');
  let liste: Element | null = auswahl;
  let geoeffnet = false;
  if (rolle === 'combobox') {
    liste = auswahl.getAttribute('aria-expanded') === 'true' ? listeVon(auswahl) : null;
    if (!liste) {
      if ((auswahl as HTMLButtonElement).disabled || auswahl.getAttribute('aria-disabled') === 'true') {
        throw new Error('Die Auswahl ist gesperrt (aus) — nichts gewählt.');
      }
      await klickMitPause(auswahl, mitteVon(auswahl));
      geoeffnet = true;
      liste = await warteAufListe(auswahl);
    }
    if (!liste) throw new Error(`Die Auswahl ging nicht auf (keine Liste nach ${LISTE_WARTEN_MS} ms) — nichts gewählt.`);
  }
  const optionen = [...liste.querySelectorAll(rolle === 'radiogroup' ? '[role="radio"]' : '[role="option"]')];
  const option = findeOption(optionen, wert);
  if (!option) {
    if (geoeffnet) await klickMitPause(auswahl, mitteVon(auswahl)); // wieder zu, wie vorher
    throw new Error(`Die Auswahl hat keinen Eintrag «${wert}». Vorhanden: ${optionen.map(optionText).join(', ')}`);
  }
  if ((option as HTMLButtonElement).disabled || option.getAttribute('aria-disabled') === 'true') {
    if (geoeffnet) await klickMitPause(auswahl, mitteVon(auswahl));
    throw new Error(`Der Eintrag «${optionText(option)}» ist gesperrt (aus) — nichts gewählt.`);
  }
  const text = optionText(option);
  await klickMitPause(option, mitteVon(option));
  return text;
}

/** Eine Datei an ein Dateifeld oder eine Ablagefläche geben. */
export function dateiGeben(el: Element, datei: File | readonly File[], p: Punkt): 'feld' | 'ablage' {
  const dt = new DataTransfer();
  // kosmo-maus-3: mehrere Dateien landen in EINER FileList (wie eine Mehrfachwahl im Dialog).
  for (const d of Array.isArray(datei) ? datei : [datei as File]) dt.items.add(d);
  if (el instanceof HTMLInputElement && el.type === 'file') {
    el.files = dt.files;
    el.dispatchEvent(new Event('input', { bubbles: true }));
    el.dispatchEvent(new Event('change', { bubbles: true }));
    return 'feld';
  }
  for (const typ of ['dragenter', 'dragover', 'drop']) {
    el.dispatchEvent(new DragEvent(typ, { ...mausInit(p, 0, 0), dataTransfer: dt }));
  }
  return 'ablage';
}
