/**
 * KosmoBlick (Owner-Entscheid E157, 06.10.2026) — was Claude und Kosmo von
 * der laufenden App sehen, wenn «Mitschauen» an ist. Owner wörtlich: «bau
 * ein dass du live mitschauen kannst in der app das ich dir das nicht immer
 * erzählen muss».
 *
 * Nicht zu verwechseln mit `state/kosmo-blick.ts` (v0.6.8, «Kosmo sieht
 * mit»): dort holt Kosmo je Station EIN Fachbild (3D-Frame, Plan-SVG) für
 * seinen Chat. Hier geht es um die ganze Oberfläche — Text-Lagebild und ein
 * Bildschirmbild der App selbst —, damit ein Agent sie bedienen kann.
 *
 * Zwei Teile:
 *  1. **Text** (`sammleBlick`/`formatiereBlick`): Projekt, Bereich, Dialoge,
 *     Meldungen, Fehler, sichtbare Bedienelemente mit testid und Rechteck
 *     (gedeckelt), Fokus, Auswahl, offene Karten. Rein aus DOM und Stores,
 *     ohne Netz.
 *  2. **Bild** (`nimmBlickBild`): die App als JPEG, längste Seite höchstens
 *     1280 px, samt WebGL-Inhalt.
 *
 * **Normansichten** (Owner-Antwort zu E157, «Normansichten ausblenden»):
 * Flächen mit Normtext (SIA, VKF … — urheberrechtlich geschützter
 * Wortlaut) werden für Claude im Bild schwarz überdeckt und im Text durch
 * «[Normansicht]» ersetzt. Kosmo läuft lokal und sieht alles. Was als
 * Normansicht gilt, steht in `NORMANSICHT_SELEKTOR` — mit Fundstellen.
 *
 * **Bildweg — gewählt und begründet:** `html-to-image` (MIT, keine eigenen
 * Abhängigkeiten). Es zeichnet die DOM-Oberfläche über SVG-`foreignObject`
 * in ein Canvas, also mit der echten Darstellung des Browsers (alle
 * CSS-Farben, auch `oklch`, an denen `html2canvas` scheitert). Der Weg
 * über einen WebKit-Schnappschuss der Tauri-Ansicht hätte Rust je
 * Betriebssystem gebraucht (WebKitGTK, WKWebView, WebView2 sind drei
 * verschiedene Schnittstellen), wäre im Browser nicht da und kollidierte mit
 * dem Rust-Umbau des Integrators (I7a). WebGL-Flächen liest `html-to-image`
 * mit `toDataURL` — ohne `preserveDrawingBuffer` ist der Puffer nach dem
 * Darstellen leer. Darum werden alle Canvas-Flächen VORHER in einem
 * Bildtakt gelesen (`leseCanvasImBildtakt`), der 3D-Viewport zusätzlich
 * über seinen bestehenden Haken `__kosmoViewport.captureFrame()` frisch
 * gerendert. Eingesetzt werden diese Momentaufnahmen NICHT durch
 * `html-to-image` (WebKit zeichnet ein neues `data:`-Bild im
 * `foreignObject` nicht, kosmo-maus-4), sondern danach mit `drawImage`
 * (`setzeFlaecheEin`).
 */

import { useProject } from './project-store';
import { aktivesProjektId } from './project-vault';
import { erkenneAktiveStation } from './kosmo-blick';
import { useClaudeAnschluss } from './claude-anschluss';
import { useKosmoMaus, type Urheber } from './kosmo-maus-freigabe';
import { NORMANSICHT_SELEKTOR } from './normansicht';

// ---------------------------------------------------------------------------
// Normansicht
// ---------------------------------------------------------------------------

export { NORMANSICHT_SELEKTOR, istNormTreffer } from './normansicht';

/** Schwärzen gilt für alles, was das Haus verlässt — heute: Claude. */
export function schwaerzenFuer(fuer: Urheber): boolean {
  return fuer === 'claude';
}

// ---------------------------------------------------------------------------
// Text
// ---------------------------------------------------------------------------

/** Deckel der Bedienelemente-Liste: mehr hilft keinem Modell, es kostet nur Kontext. */
export const BLICK_MAX_ELEMENTE = 120;
/** Längster Beschriftungstext je Element. */
export const BLICK_MAX_TEXT = 60;

/** Marke für die eigene Ebene (Zeiger, Leiste, Schalter): taucht im Blick nicht auf. */
export const EIGENE_EBENE_ATTR = 'data-kosmo-maus-eigen';

/**
 * Marke für Teile der eigenen Ebene, die nur zeigen (die Figur des Agenten,
 * lw-maus-sperrzone-esc): sie liegen über der App und nehmen Zeigerereignisse
 * nur fürs Aufklappen ihrer Karte. Die KosmoMaus zielt durch sie hindurch —
 * ausser auf ein Bedienteil darin (der «Stopp» der Karte bleibt gesperrt).
 */
export const DURCHLAESSIG_ATTR = 'data-kosmo-maus-durchlaessig';

const INTERAKTIV = [
  'button',
  'a[href]',
  'input:not([type="hidden"])',
  'select',
  'textarea',
  'summary',
  '[role="button"]',
  '[role="tab"]',
  '[role="menuitem"]',
  '[role="option"]',
  '[role="checkbox"]',
  '[role="switch"]',
  '[role="radio"]',
  '[role="slider"]',
  '[contenteditable="true"]',
  'canvas',
].join(', ');

export interface BlickRechteck {
  x: number;
  y: number;
  b: number;
  h: number;
}

export interface BlickElement {
  testid?: string;
  art: string;
  text: string;
  rechteck: BlickRechteck;
  aus?: true;
  verdeckt?: true;
  gewaehlt?: true;
}

export interface BlickLage {
  fuer: Urheber;
  projekt: { name: string; id: string | null };
  bereich: string;
  fenster: { breite: number; hoehe: number };
  dialoge: string[];
  meldungen: { ton: string; text: string }[];
  fehler: string[];
  elemente: BlickElement[];
  weitereElemente: number;
  fokus: string | null;
  auswahl: string[];
  karten: string[];
  normansichten: BlickRechteck[];
  normansichtenGeschwaerzt: boolean;
  /** Runde 34 (Nr. 69/77): Karten-Modus, Bedienen, Mitschauen (`agent-lage.ts`) — setzt `fuehreBlickAus`. */
  modus?: string;
}

function kurz(text: string, max = BLICK_MAX_TEXT): string {
  const t = text.replace(/\s+/g, ' ').trim();
  return t.length > max ? `${t.slice(0, max - 1)}…` : t;
}

function rechteck(el: Element): BlickRechteck {
  const r = el.getBoundingClientRect();
  return { x: Math.round(r.left), y: Math.round(r.top), b: Math.round(r.width), h: Math.round(r.height) };
}

function istEigen(el: Element): boolean {
  return el.closest(`[${EIGENE_EBENE_ATTR}]`) !== null;
}

/** Sichtbar heisst: Fläche > 0, im Fenster, nicht versteckt. */
export function istSichtbar(el: Element): boolean {
  const r = el.getBoundingClientRect();
  if (r.width <= 0 || r.height <= 0) return false;
  if (r.right <= 0 || r.bottom <= 0 || r.left >= window.innerWidth || r.top >= window.innerHeight) return false;
  const cv = (el as Element & { checkVisibility?: (o?: object) => boolean }).checkVisibility;
  if (typeof cv === 'function' && !cv.call(el, { visibilityProperty: true, opacityProperty: false })) return false;
  return el.closest('[inert], [aria-hidden="true"]') === null;
}

export function istNormansicht(el: Element): boolean {
  return el.closest(NORMANSICHT_SELEKTOR) !== null;
}

/** Beschriftung eines Elements, so wie ein Mensch sie liest. Kennwörter nie. */
export function beschriftung(el: Element): string {
  const aria = el.getAttribute('aria-label');
  if (aria) return kurz(aria);
  if (el instanceof HTMLInputElement) {
    if (el.type === 'password') return '(Kennwortfeld)';
    if (el.type === 'checkbox' || el.type === 'radio') {
      const label = el.labels?.[0]?.textContent ?? el.name;
      return kurz(`${label ?? ''} ${el.checked ? '[x]' : '[ ]'}`);
    }
    return kurz(el.value ? `${el.placeholder || el.name || 'Feld'}: ${el.value}` : el.placeholder || el.name || 'Feld');
  }
  if (el instanceof HTMLTextAreaElement) return kurz(el.value || el.placeholder || 'Textfeld');
  if (el instanceof HTMLSelectElement) return kurz(`Auswahl: ${el.selectedOptions[0]?.textContent ?? ''}`);
  if (el instanceof HTMLCanvasElement) return 'Zeichenfläche';
  return kurz(sichtbarerText(el));
}

/**
 * Demolauf 16.10.2026, Nr. 4: «Fokus liegt auf Element ‹Bildschirm zu schmal — …›» bei 2186 px Breite. Der
 * Fokus lag auf einem Behälter; `textContent` liest auch Kinder mit `display:none` und begann darum mit dem
 * versteckten Schmal-Hinweis (`App.tsx`). `innerText` liest, was zu sehen ist; ohne Layout (jsdom) bleibt es
 * bei `textContent`.
 */
function sichtbarerText(el: Element): string {
  const innen = el instanceof HTMLElement ? (el as HTMLElement & { innerText?: unknown }).innerText : undefined;
  return typeof innen === 'string' ? innen : (el.textContent ?? '');
}

function art(el: Element): string {
  const rolle = el.getAttribute('role');
  if (rolle) return rolle;
  if (el instanceof HTMLInputElement) return `input:${el.type}`;
  return el.tagName.toLowerCase();
}

/** Liegt an der Mitte des Elements etwas anderes darüber? */
function istVerdeckt(el: Element, r: BlickRechteck): boolean {
  if (typeof document.elementFromPoint !== 'function') return false;
  const oben = document.elementFromPoint(r.x + r.b / 2, r.y + r.h / 2);
  if (!oben) return false;
  return !(oben === el || el.contains(oben) || oben.contains(el) || istEigen(oben));
}

/** Die letzten Fehlermeldungen (Toasts mit Ton «fehler»), auch wenn sie schon weg sind. */
const letzteFehler: { zeit: number; text: string }[] = [];
let fehlerHoererAn = false;
export function hoereAufFehler(): void {
  if (fehlerHoererAn || typeof window === 'undefined') return;
  fehlerHoererAn = true;
  window.addEventListener('kosmo-fehlermeldung', (e) => {
    const text = String((e as CustomEvent<{ text?: string }>).detail?.text ?? '');
    letzteFehler.push({ zeit: Date.now(), text });
    if (letzteFehler.length > 5) letzteFehler.shift();
  });
}

/** Das Lagebild als Daten. `fuer` entscheidet über das Schwärzen. */
export function sammleBlick(fuer: Urheber): BlickLage {
  const schwaerzen = schwaerzenFuer(fuer);
  const st = useProject.getState();
  const text = (el: Element, t: string) => (schwaerzen && istNormansicht(el) ? '[Normansicht]' : t);

  const dialoge = [...document.querySelectorAll('[role="dialog"], [role="alertdialog"], dialog[open]')]
    .filter((d) => istSichtbar(d) && !istEigen(d))
    .map((d) => {
      const titel =
        d.getAttribute('aria-label') ??
        d.querySelector('h1, h2, h3, .k-titel, [class*="titel"]')?.textContent ??
        d.textContent ??
        '';
      const testid = d.getAttribute('data-testid');
      return `${testid ? `[${testid}] ` : ''}${text(d, kurz(titel, 120))}`;
    });

  const meldungen = [...document.querySelectorAll('.k-meldung-karte')]
    .filter((m) => !m.classList.contains('k-meldung--aus'))
    .map((m) => ({
      ton: (m.getAttribute('data-testid') ?? 'meldung-info').replace(/^meldung-/, ''),
      text: kurz(m.querySelector('.k-meldung-text')?.textContent ?? m.textContent ?? '', 200),
    }));

  const fehler = [
    ...[...document.querySelectorAll('[role="alert"]')]
      .filter((a) => istSichtbar(a) && !istEigen(a))
      .map((a) => text(a, kurz(a.textContent ?? '', 200))),
    ...letzteFehler.filter((f) => Date.now() - f.zeit < 60_000).map((f) => kurz(f.text, 200)),
  ].filter((t, i, alle) => t && alle.indexOf(t) === i);

  const alle = [...document.querySelectorAll(INTERAKTIV)].filter((el) => !istEigen(el) && istSichtbar(el));
  const elemente: BlickElement[] = alle.slice(0, BLICK_MAX_ELEMENTE).map((el) => {
    const r = rechteck(el);
    const e: BlickElement = {
      art: art(el),
      text: text(el, beschriftung(el)),
      rechteck: r,
    };
    const testid = el.getAttribute('data-testid') ?? el.closest('[data-testid]')?.getAttribute('data-testid');
    if (testid) e.testid = testid;
    if ((el as HTMLButtonElement).disabled || el.getAttribute('aria-disabled') === 'true') e.aus = true;
    if (el.getAttribute('aria-pressed') === 'true' || el.getAttribute('aria-selected') === 'true') e.gewaehlt = true;
    if (istVerdeckt(el, r)) e.verdeckt = true;
    return e;
  });

  const fokusEl = document.activeElement;
  const fokus =
    fokusEl && fokusEl !== document.body && !istEigen(fokusEl)
      ? `${art(fokusEl)}${fokusEl.getAttribute('data-testid') ? ` [${fokusEl.getAttribute('data-testid')}]` : ''} «${text(fokusEl, beschriftung(fokusEl))}»${istSichtbar(fokusEl) ? '' : ' (nicht sichtbar)'}`
      : null;

  const karten = [
    ...useClaudeAnschluss.getState().vorschlaege.map((v) => `Claude-Vorschlag ${v.kennung}: ${v.zusammenfassung}`),
    ...useKosmoMaus.getState().vorschlaege.map((v) => `Maus-Vorschlag ${v.kennung} (${v.urheber}): ${v.zusammenfassung}`),
    ...[...document.querySelectorAll('[data-testid="proposal-card"], [data-testid="paket-card"]')]
      .filter(istSichtbar)
      .map((k) => `Kosmo-Karte: ${kurz(k.textContent ?? '', 120)}`),
  ];

  const normansichten = [...document.querySelectorAll(NORMANSICHT_SELEKTOR)].filter(istSichtbar).map(rechteck);

  return {
    fuer,
    projekt: { name: st.doc.settings.projectName ?? '', id: aktivesProjektId() },
    bereich: erkenneAktiveStation().titel,
    fenster: { breite: window.innerWidth, hoehe: window.innerHeight },
    dialoge,
    meldungen,
    fehler,
    elemente,
    weitereElemente: Math.max(0, alle.length - elemente.length),
    fokus,
    auswahl: [...st.selection],
    karten,
    normansichten,
    normansichtenGeschwaerzt: schwaerzen && normansichten.length > 0,
  };
}

function r2s(r: BlickRechteck): string {
  return `${r.x},${r.y} ${r.b}×${r.h}`;
}

/** Das Lagebild als kurzer Text für ein Sprachmodell. */
export function formatiereBlick(l: BlickLage): string {
  const z: string[] = [];
  z.push(`PROJEKT: «${l.projekt.name || 'ohne Namen'}»${l.projekt.id ? ` (${l.projekt.id})` : ''}`);
  z.push(`BEREICH: ${l.bereich}`);
  if (l.modus) z.push(l.modus.replace(/^Modus: /, 'MODUS: '));
  z.push(`FENSTER: ${l.fenster.breite}×${l.fenster.hoehe} px (Koordinaten unten in diesen CSS-Pixeln, Ursprung oben links)`);
  if (l.dialoge.length) z.push(`DIALOGE: ${l.dialoge.join(' | ')}`);
  if (l.meldungen.length) z.push(`MELDUNGEN: ${l.meldungen.map((m) => `${m.ton}: ${m.text}`).join(' | ')}`);
  if (l.fehler.length) z.push(`FEHLER: ${l.fehler.join(' | ')}`);
  z.push(`FOKUS: ${l.fokus ?? 'keiner'}`);
  z.push(`AUSWAHL: ${l.auswahl.length ? l.auswahl.join(', ') : 'nichts gewählt'}`);
  if (l.karten.length) z.push(`OFFENE KARTEN: ${l.karten.join(' | ')}`);
  if (l.normansichten.length) {
    z.push(
      l.normansichtenGeschwaerzt
        ? `NORMANSICHTEN: ${l.normansichten.length} Fläche(n) mit Normtext — für Claude geschwärzt (Owner-Entscheid E157): ${l.normansichten.map(r2s).join('; ')}`
        : `NORMANSICHTEN: ${l.normansichten.length} Fläche(n) mit Normtext: ${l.normansichten.map(r2s).join('; ')}`,
    );
  }
  z.push(`BEDIENELEMENTE (${l.elemente.length}${l.weitereElemente ? `, ${l.weitereElemente} weitere nicht gelistet` : ''}):`);
  for (const e of l.elemente) {
    const marken = [e.aus ? 'aus' : '', e.gewaehlt ? 'gewählt' : '', e.verdeckt ? 'verdeckt' : ''].filter(Boolean).join(',');
    z.push(`- ${e.testid ? `[${e.testid}] ` : ''}${e.art} «${e.text}» @${r2s(e.rechteck)}${marken ? ` (${marken})` : ''}`);
  }
  return z.join('\n');
}

// ---------------------------------------------------------------------------
// Bild
// ---------------------------------------------------------------------------

/** Längste Bildseite (Auftrag E157). */
export const BLICK_BILD_MAX_SEITE = 1280;
export const BLICK_BILD_QUALITAET = 0.82;

/** Skalierung, damit die längste Seite höchstens `max` px misst (nie vergrössern). */
export function bildMassstab(breite: number, hoehe: number, max = BLICK_BILD_MAX_SEITE): number {
  const l = Math.max(breite, hoehe, 1);
  return l <= max ? 1 : max / l;
}

/**
 * Schwärzt Rechtecke (CSS-Pixel) auf einem Canvas-Kontext im Massstab `m`.
 * Rein, damit sie ohne echtes Canvas geprüft werden kann.
 */
export function schwaerzeRechtecke(
  ctx: Pick<CanvasRenderingContext2D, 'fillRect' | 'fillText'> & { fillStyle: unknown; font: string },
  rechtecke: readonly BlickRechteck[],
  m: number,
): number {
  for (const r of rechtecke) {
    ctx.fillStyle = '#000000';
    ctx.fillRect(Math.floor(r.x * m), Math.floor(r.y * m), Math.ceil(r.b * m) + 1, Math.ceil(r.h * m) + 1);
    if (r.b * m > 90 && r.h * m > 16) {
      ctx.fillStyle = '#ffffff';
      ctx.font = '12px sans-serif';
      ctx.fillText('Normansicht', Math.floor(r.x * m) + 6, Math.floor(r.y * m) + 14);
    }
  }
  return rechtecke.length;
}

/** Die bestehenden Haken des 3D-Viewports (`Viewport3D.tsx`, `__kosmoViewport`), die der Blick braucht. */
interface ViewportHaken {
  captureFrame?: () => string | null;
  invalidate?: () => void;
  frameCount?: () => number;
}

/** So viele Bildtakte wartet der Blick höchstens auf einen frisch gerenderten 3D-Frame. */
export const BLICK_3D_MAX_TAKTE = 12;

/**
 * Liest alle Canvas-Flächen in EINEM Bildtakt: nach dem Rendern des
 * laufenden Takts ist der WebGL-Puffer noch gefüllt. Der 3D-Viewport wird
 * zusätzlich frisch gerendert (er rendert nur bei Bedarf).
 *
 * kosmo-maus-2 (Owner-Abnahme 07.10.2026, Desktop-App mit GPU): die
 * 3D-Fläche war im Bild IMMER schwarz, der Plan daneben voll. URSACHE:
 * `captureFrame()` ruft `renderFrame()`, und das hat ein Render-Tor — mit
 * «Rendern bei Bedarf» (Standard für Nutzer, in den E2E-Proben aus) zeichnet
 * es nur, wenn etwas `invalidate()` gesagt hat, und höchstens 30-mal je
 * Sekunde. Im Leerlauf zeichnete es also nicht, und `toDataURL()` las den
 * schon gezeigten, geleerten Puffer (kein `preserveDrawingBuffer`). Darum
 * jetzt über die BESTEHENDEN Haken, ohne Änderung an `Viewport3D.tsx`:
 * `invalidate()` vor `captureFrame()`, und `frameCount()` sagt, ob wirklich
 * gezeichnet wurde. Wenn nicht (FPS-Deckel), im nächsten Takt noch einmal,
 * höchstens `BLICK_3D_MAX_TAKTE`-mal. Das Bild des Viewports ist dann die
 * Rückgabe von `captureFrame()` (gelesen im selben Zug wie das Zeichnen).
 *
 * kosmo-maus-3 (Geräteprobe 575264bdf, 08.10.2026): mit geladenem Splat und
 * kurz nach jeder Änderung (Kamerafahrt, Kippen, Aufbau) war die 3D-Fläche
 * trotzdem schwarz. Dann zeichnet der Viewport in JEDEM Takt selbst;
 * `captureFrame()` zeichnet nicht (FPS-Deckel: die Schleife zeichnete eben),
 * und der frühere Zweig «die Schleife hat in diesem Takt schon gezeichnet →
 * direkt aus dem Canvas» las in einem ANDEREN Rückruf als dem Zeichnen. In
 * WebKitGTK ist der Puffer dort schon leer (gemessen: über 30 Bilder fast alle
 * schwarz). Darum liest der Blick jetzt in DERSELBEN Aufgabe wie das Zeichnen
 * der eigenen Schleife: für die Dauer des Blicks (höchstens
 * `BLICK_3D_MAX_TAKTE` Takte) wird jeder Bildtakt-Rückruf umhüllt; steigt
 * `frameCount()` in einem Rückruf, wird gleich danach — noch im selben
 * Rückruf — `toDataURL()` gelesen. Danach ist `requestAnimationFrame` wieder
 * das ursprüngliche. `Viewport3D.tsx` bleibt unverändert: die Schleife
 * schlägt `requestAnimationFrame` bei jedem Takt neu nach.
 */
export function leseCanvasImBildtakt(
  maxTakte = BLICK_3D_MAX_TAKTE,
  wurzel: ParentNode = document,
): Promise<Map<HTMLCanvasElement, string>> {
  const haken = () => (window as unknown as { __kosmoViewport?: ViewportHaken }).__kosmoViewport;
  const zaehle = (): number | undefined => {
    try {
      return haken()?.frameCount?.();
    } catch {
      return undefined;
    }
  };
  const viewportCanvas = () => document.querySelector<HTMLCanvasElement>('[data-testid="viewport3d"] canvas');
  const g = globalThis as { requestAnimationFrame: typeof requestAnimationFrame };
  const rafAlt = g.requestAnimationFrame;
  return new Promise((resolve) => {
    let takte = 0;
    let fertig = false;
    // Gelesen direkt nach einem Zeichnen der eigenen Schleife (selbe Aufgabe).
    let gefangen: string | null = null;
    const umhuellt: typeof requestAnimationFrame = (cb) =>
      rafAlt.call(globalThis, (zeit: number) => {
        const vor = fertig || gefangen !== null ? undefined : zaehle();
        try {
          cb(zeit);
        } finally {
          if (vor !== undefined && !fertig && gefangen === null) {
            const nach = zaehle();
            if (nach !== undefined && nach > vor) {
              try {
                const url = viewportCanvas()?.toDataURL('image/png');
                if (url && url !== 'data:,') gefangen = url;
              } catch {
                /* fremd verschmutzt: dann eben nicht */
              }
            }
          }
        }
      });
    if (haken()?.captureFrame) g.requestAnimationFrame = umhuellt;
    const ende = (bilder: Map<HTMLCanvasElement, string>) => {
      fertig = true;
      if (g.requestAnimationFrame === umhuellt) g.requestAnimationFrame = rafAlt;
      resolve(bilder);
    };
    const takt = () => {
      takte++;
      const viewport = haken();
      let frisch: string | null = gefangen;
      let gezeichnet = true;
      if (frisch === null) {
        try {
          if (viewport?.captureFrame) {
            const jetzt = viewport.frameCount?.();
            viewport.invalidate?.();
            const url = viewport.captureFrame();
            const nachher = viewport.frameCount?.();
            gezeichnet = jetzt === undefined || nachher === undefined || nachher > jetzt;
            if (gezeichnet && url && url !== 'data:,') frisch = url;
          }
        } catch {
          /* kein 3D gemountet: dann eben ohne */
          gezeichnet = true;
        }
      }
      if (!gezeichnet && takte < maxTakte) {
        rafAlt.call(globalThis, takt);
        return;
      }
      frisch ??= gefangen;
      const vc = frisch ? viewportCanvas() : null;
      const bilder = new Map<HTMLCanvasElement, string>();
      for (const c of wurzel.querySelectorAll('canvas')) {
        if (istEigen(c) || c.width === 0 || c.height === 0) continue;
        if (c === vc && frisch) {
          bilder.set(c, frisch);
          continue;
        }
        try {
          bilder.set(c, c.toDataURL('image/png'));
        } catch {
          /* fremd verschmutztes Canvas: bleibt leer */
        }
      }
      ende(bilder);
    };
    rafAlt.call(globalThis, takt);
  });
}

/** 1×1 durchsichtig: steht für ein Bild der Oberfläche, das sich nicht laden lässt. */
const LEERES_BILD = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=';

/** Ein Fehler beim Zeichnen in Worten — `html-to-image` wirft bei einem Bild, das nicht lädt, ein nacktes `Event`. */
export function blickFehlerText(e: unknown): string {
  if (e instanceof Error) return e.message;
  if (typeof Event !== 'undefined' && e instanceof Event) {
    const quelle = (e.target as { src?: unknown } | null)?.src;
    return `ein Bild der Oberfläche liess sich nicht laden (${e.type}${typeof quelle === 'string' && quelle ? `: ${quelle.slice(0, 80)}` : ''})`;
  }
  return String(e);
}

export interface BlickBildErgebnis {
  mimeType: 'image/jpeg';
  data: string;
  breite: number;
  hoehe: number;
  massstab: number;
  geschwaerzt: number;
}

/**
 * kosmo-maus-4 (Geräteprobe 1745, 08.10.2026, echte Owner-App, WebKitGTK):
 * die 3D-Fläche war mit Splat in über 40 Bildern IMMER schwarz (Mittel 14.1 =
 * nur der Hintergrund), ohne Splat die ersten 1–2 Bilder nach 2D→3D.
 *
 * URSACHE (nachgestellt in echtem WebKitGTK 2.48 unter Xvfb, siehe Lieferblatt
 * kosmo-maus-4): nicht der WebGL-Puffer — der war in jedem gemessenen Fall
 * voll, im selben wie im nächsten Bildtakt. Schwarz macht `html-to-image`:
 * es legt jede Canvas-Fläche als `<img src="data:…">` in ein SVG mit
 * `foreignObject`. WebKit zeichnet ein solches eingebettetes Bild nur, wenn es
 * dieselbe `data:`-Adresse schon einmal gezeichnet hat. Ein NEUES Bild bleibt
 * leer, das gleiche beim zweiten Mal erscheint. Darum ohne Splat «die ersten
 * 1–2 schwarz, dann gut» (im Leerlauf ist jedes Bild gleich), mit Splat
 * «immer schwarz» (jeder Takt zeichnet ein anderes Bild).
 *
 * LÖSUNG: Canvas-Flächen gehen gar nicht mehr als Bild durch `html-to-image`.
 * Die Oberfläche wird ZWEIMAL gezeichnet, jede Canvas-Fläche dabei leer mit
 * schwarzem bzw. weissem CSS-Hintergrund (`toDataURL` sagt `data:,`, dann
 * klont `html-to-image` ein leeres Canvas). Aus den beiden Durchgängen folgt
 * je Bildpunkt, wie viel von der Fläche durchscheint (`setzeFlaecheEin`); die
 * Momentaufnahme wird mit `drawImage` im Hauptdokument genau dort
 * eingesetzt. Was über dem 3D liegt (Pillen, Glas, Hinweise), bleibt darüber
 * und mischt sich wie am Bildschirm.
 */
export const BLICK_SCHLUESSEL_SCHWARZ = '#000000';
export const BLICK_SCHLUESSEL_WEISS = '#ffffff';

/**
 * Setzt eine Canvas-Momentaufnahme in die Oberfläche ein (RGBA, gleich gross).
 * `schwarz`/`weiss`: dieselbe Fläche aus den zwei Durchgängen; `bild`: die
 * Momentaufnahme. Je Kanal ist `durch = (weiss − schwarz) / 255` der Anteil,
 * der von der Fläche durchscheint (0 = ganz verdeckt, 1 = frei), und das
 * Ergebnis `schwarz + durch · bild` — Alpha-Mischung wie im Browser. Schreibt
 * in `schwarz`.
 */
export function setzeFlaecheEin(schwarz: Uint8ClampedArray, weiss: Uint8ClampedArray, bild: Uint8ClampedArray): void {
  const n = Math.min(schwarz.length, weiss.length, bild.length);
  for (let i = 0; i < n; i += 4) {
    for (let k = 0; k < 3; k++) {
      const s = schwarz[i + k]!;
      const durch = Math.max(0, Math.min(1, (weiss[i + k]! - s) / 255));
      schwarz[i + k] = s + durch * bild[i + k]!;
    }
    schwarz[i + 3] = 255;
  }
}

/** Ein `data:`-Bild im Hauptdokument laden (nicht im SVG). `null` nach `ms` oder bei Fehler. */
function ladeBild(url: string, ms = 3000): Promise<HTMLImageElement | null> {
  return new Promise((resolve) => {
    if (typeof Image !== 'function') {
      resolve(null);
      return;
    }
    const img = new Image();
    const t = setTimeout(() => resolve(null), ms);
    img.onload = () => {
      clearTimeout(t);
      resolve(img);
    };
    img.onerror = () => {
      clearTimeout(t);
      resolve(null);
    };
    img.src = url;
  });
}

interface Einsatz {
  canvas: HTMLCanvasElement;
  url: string;
  rechteck: DOMRect;
}

/** Die Momentaufnahmen in die Oberfläche setzen (siehe oben). */
async function setzeCanvasFlaechenEin(
  ziel: HTMLCanvasElement,
  weiss: HTMLCanvasElement,
  einsaetze: readonly Einsatz[],
  m: number,
): Promise<void> {
  const ctx = ziel.getContext('2d');
  const ctxWeiss = weiss.getContext('2d');
  if (!ctx || !ctxWeiss) return;
  for (const e of einsaetze) {
    const r = e.rechteck;
    // sichtbarer Teil der Fläche im Zielbild
    const x0 = Math.max(0, Math.round(r.left * m));
    const y0 = Math.max(0, Math.round(r.top * m));
    const x1 = Math.min(ziel.width, Math.round(r.right * m));
    const y1 = Math.min(ziel.height, Math.round(r.bottom * m));
    const b = x1 - x0;
    const h = y1 - y0;
    if (b <= 0 || h <= 0 || r.width <= 0 || r.height <= 0) continue;
    const img = await ladeBild(e.url);
    if (!img) continue;
    const zwischen = document.createElement('canvas');
    zwischen.width = b;
    zwischen.height = h;
    const zctx = zwischen.getContext('2d');
    if (!zctx) continue;
    // Ausschnitt der Momentaufnahme, der zum sichtbaren Teil gehört.
    const sx = ((x0 / m - r.left) / r.width) * img.naturalWidth;
    const sy = ((y0 / m - r.top) / r.height) * img.naturalHeight;
    const sb = (b / m / r.width) * img.naturalWidth;
    const sh = (h / m / r.height) * img.naturalHeight;
    zctx.drawImage(img, sx, sy, sb, sh, 0, 0, b, h);
    const unten = ctx.getImageData(x0, y0, b, h);
    setzeFlaecheEin(unten.data, ctxWeiss.getImageData(x0, y0, b, h).data, zctx.getImageData(0, 0, b, h).data);
    ctx.putImageData(unten, x0, y0);
  }
}

// ---------------------------------------------------------------------------
// Scrollstand
// ---------------------------------------------------------------------------

/**
 * kosmo-blick-live (Gerät-Nachprobe 08.10.2026, Owner-App): nach dem
 * Scrollen eines Panels zeigte das Bild den ALTEN Stand, die Liste der
 * Bedienelemente (Rechtecke aus `getBoundingClientRect`) schon den neuen.
 *
 * URSACHE: `html-to-image` (1.11.13) klont den DOM mit `cloneNode` und
 * überträgt keinen Scrollstand — ein Klon hat `scrollTop = 0`, und im
 * SVG-`foreignObject` lässt sich auch nichts scrollen. Jeder gescrollte
 * Container erschien im Bild also oben (bzw. links) angeschlagen.
 *
 * LÖSUNG: der Scrollstand wird im Klon nachgebildet. Für die Dauer des
 * Bildes bekommt jeder gescrollte Container eine eigene `cloneNode`-Fassung
 * (gleiches Muster wie `toDataURL` oben, danach wieder weg); deren Klon
 * verschiebt jedes eingehängte Kind um (−scrollLeft, −scrollTop):
 * Blockkinder per vorangestelltem `translate(…)` (verschiebt im
 * Koordinatenraum des Containers, unabhängig von einer eigenen
 * Transformation und deren Ursprung), Inline-Kinder und lose Textzeilen per
 * `position: relative` (Inline-Kästen kennen keine Transformation). Der
 * Container selbst schneidet mit seinem `overflow` ab wie am Bildschirm.
 * Ausnahmen: `fixed` und `sticky` bleiben stehen (die scrollen am Bildschirm
 * nicht mit). Die Live-Oberfläche wird nicht verändert.
 *
 * Gleicher Moment: `fuehreBlickAus` wartet zuerst, bis kein Container mehr
 * scrollt (`warteAufScrollRuhe`), liest dann Liste UND Scrollstand und gibt
 * genau diesen Scrollstand ans Bild weiter.
 */
export interface ScrollStand {
  x: number;
  y: number;
}

/** Markiert die Hülle loser Textzeilen im Klon (nur im Bild, nie live). */
export const BLICK_SCROLL_HUELLE_ATTR = 'data-kosmo-blick-scroll';

/** Alle gescrollten Container unter `wurzel` (Dokumentreihenfolge). */
export function sammleScrollStaende(wurzel: ParentNode = document.body): Map<Element, ScrollStand> {
  const staende = new Map<Element, ScrollStand>();
  for (const el of wurzel.querySelectorAll('*')) {
    const x = el.scrollLeft || 0;
    const y = el.scrollTop || 0;
    if (x !== 0 || y !== 0) staende.set(el, { x, y });
  }
  return staende;
}

function gleicheStaende(a: Map<Element, ScrollStand>, b: Map<Element, ScrollStand>): boolean {
  if (a.size !== b.size) return false;
  for (const [el, s] of a) {
    const t = b.get(el);
    if (!t || t.x !== s.x || t.y !== s.y) return false;
  }
  return true;
}

/** So viele Takte wartet der Blick höchstens, bis ein weiches Scrollen steht. */
export const BLICK_SCROLL_MAX_TAKTE = 12;

/**
 * Wartet, bis zwei aufeinanderfolgende Takte denselben Scrollstand zeigen,
 * höchstens `maxTakte`; gibt diesen Stand zurück.
 */
export async function warteAufScrollRuhe(
  maxTakte = BLICK_SCROLL_MAX_TAKTE,
  takt: () => Promise<void> = naechsterBildtakt,
): Promise<Map<Element, ScrollStand>> {
  let vorher = sammleScrollStaende();
  for (let i = 0; i < maxTakte; i++) {
    await takt();
    const jetzt = sammleScrollStaende();
    if (gleicheStaende(vorher, jetzt)) return jetzt;
    vorher = jetzt;
  }
  return vorher;
}

function naechsterBildtakt(): Promise<void> {
  return new Promise((resolve) => {
    const t = setTimeout(resolve, 50); // im Hintergrund ruht der Bildtakt
    if (typeof requestAnimationFrame === 'function') {
      requestAnimationFrame(() => {
        clearTimeout(t);
        resolve();
      });
    }
  });
}

function px(wert: string): number {
  const n = parseFloat(wert);
  return Number.isFinite(n) ? n : 0;
}

/** Ein geklontes Kind eines gescrollten Containers um (−x, −y) verschieben. */
function verschiebeKlonKind(kind: Node, x: number, y: number): Node {
  if (kind.nodeType === 3 /* Text */) {
    if (!(kind.textContent ?? '').trim()) return kind;
    const huelle = document.createElement('span');
    huelle.setAttribute(BLICK_SCROLL_HUELLE_ATTR, '');
    huelle.style.setProperty('position', 'relative');
    huelle.style.setProperty('left', `${-x}px`);
    huelle.style.setProperty('top', `${-y}px`);
    huelle.appendChild(kind);
    return huelle;
  }
  const style = (kind as HTMLElement).style as CSSStyleDeclaration | undefined;
  if (kind.nodeType !== 1 || !style) return kind;
  const position = style.getPropertyValue('position');
  if (position === 'fixed' || position === 'sticky') return kind;
  const display = style.getPropertyValue('display');
  if (display === 'none') return kind;
  if (display === 'inline' || display === 'contents') {
    if (display === 'contents') return kind;
    if (position === '' || position === 'static') {
      style.setProperty('position', 'relative');
      style.setProperty('left', `${-x}px`);
      style.setProperty('top', `${-y}px`);
    } else if (position === 'relative') {
      style.setProperty('left', `${px(style.getPropertyValue('left')) - x}px`);
      style.setProperty('top', `${px(style.getPropertyValue('top')) - y}px`);
    }
    return kind;
  }
  const alt = style.getPropertyValue('transform');
  const verschiebung = `translate(${-x}px, ${-y}px)`;
  style.setProperty(
    'transform',
    alt && alt !== 'none' ? `${verschiebung} ${alt}` : verschiebung,
    style.getPropertyPriority('transform'),
  );
  return kind;
}

/**
 * Führt `zeichne` (einen `html-to-image`-Aufruf) so aus, dass die Klone der
 * Container in `staende` ihren Scrollstand zeigen. Danach ist alles wie
 * vorher.
 */
export async function mitScrollstand<T>(staende: ReadonlyMap<Element, ScrollStand>, zeichne: () => Promise<T>): Promise<T> {
  const zurueck: (() => void)[] = [];
  for (const [el, { x, y }] of staende) {
    if (!el.isConnected || (x === 0 && y === 0)) continue;
    const eigene = Object.getOwnPropertyDescriptor(el, 'cloneNode');
    const original = el.cloneNode;
    Object.defineProperty(el, 'cloneNode', {
      configurable: true,
      writable: true,
      value(this: Element, tief?: boolean) {
        const klon = original.call(this, tief) as Element;
        if (tief) return klon;
        const anhaengen = klon.appendChild;
        Object.defineProperty(klon, 'appendChild', {
          configurable: true,
          writable: true,
          value<N extends Node>(this: Element, kind: N): N {
            anhaengen.call(this, verschiebeKlonKind(kind, x, y));
            return kind;
          },
        });
        return klon;
      },
    });
    zurueck.push(() => {
      if (eigene) Object.defineProperty(el, 'cloneNode', eigene);
      else delete (el as unknown as Record<string, unknown>)['cloneNode'];
    });
  }
  try {
    return await zeichne();
  } finally {
    for (const f of zurueck) f();
  }
}

/**
 * Die App als Bild. Für Claude mit geschwärzten Normansichten.
 * `scrollStaende`: der Scrollstand, den das Bild zeigen soll — `fuehreBlickAus`
 * gibt den Stand aus dem Moment der Liste mit (siehe «Scrollstand»).
 */
/**
 * lw-maus-rad-vollbild (Gerät-Nachprobe, Owner-App WebKitGTK): im Vollbild
 * (`requestFullscreen` auf einer Fläche, z.B. Rundgang 2560×1440) zeigte das
 * Blick-Bild die normale Ansicht.
 *
 * URSACHE: das Bild klonte immer `document.body`. Am Bildschirm liegt das
 * Vollbild-Element in der obersten Ebene (top layer) und deckt alles andere;
 * im Klon gibt es keine oberste Ebene. Dort gilt wieder das normale Layout:
 * ein Vorfahr mit `transform`/`filter`/`backdrop-filter`/`contain` (Liquid
 * Glass) macht aus `position: fixed` eine Lage relativ zu sich und schneidet
 * mit seinem `overflow` ab, die übrige Oberfläche malt darüber — das Bild
 * zeigte also die normale Ansicht. Zusätzlich setzte `setzeCanvasFlaechenEin`
 * auch Canvas-Flächen ausserhalb des Vollbilds ein (dort unsichtbar).
 *
 * LÖSUNG: im Vollbild ist `document.fullscreenElement` die Wurzel des Bildes,
 * auf die Fensterfläche gesetzt (links oben, Fensterbreite × -höhe); Canvas-
 * Flächen und Normansichten zählen nur innerhalb dieser Wurzel.
 */
export function blickWurzel(): HTMLElement {
  const voll = typeof document !== 'undefined' ? document.fullscreenElement : null;
  return voll instanceof HTMLElement && voll.isConnected ? voll : document.body;
}

export async function nimmBlickBild(
  fuer: Urheber,
  maxSeite = BLICK_BILD_MAX_SEITE,
  scrollStaende: ReadonlyMap<Element, ScrollStand> = sammleScrollStaende(),
): Promise<BlickBildErgebnis> {
  const { toCanvas } = await import('html-to-image');
  const breite = window.innerWidth;
  const hoehe = window.innerHeight;
  const m = bildMassstab(breite, hoehe, maxSeite);
  const wurzel = blickWurzel();
  const imVollbild = wurzel !== document.body;
  const momentaufnahmen = await leseCanvasImBildtakt(BLICK_3D_MAX_TAKTE, imVollbild ? wurzel : document);
  // Im Vollbild liegt hinter der Fläche der schwarze `::backdrop`, nicht der Seitenhintergrund.
  const eigenerGrund = getComputedStyle(wurzel).backgroundColor;
  const hintergrund = imVollbild
    ? eigenerGrund && !/^(transparent|rgba\(0, 0, 0, 0\))$/.test(eigenerGrund) ? eigenerGrund : '#000000'
    : getComputedStyle(document.body).backgroundColor || '#ffffff';
  const einsaetze: Einsatz[] = [...momentaufnahmen].map(([canvas, url]) => ({
    canvas,
    url,
    rechteck: canvas.getBoundingClientRect(),
  }));
  const zeichne = async (schluessel: string | null): Promise<HTMLCanvasElement> => {
    // WARUM die Instanz-Überschreibung: `html-to-image` ruft beim Klonen
    // `canvas.toDataURL()`. «data:,» heisst dort «leer» — es klont ein leeres
    // Canvas, das nur seinen CSS-Hintergrund zeigt (hier die Schlüsselfarbe).
    // Danach ist alles wieder wie vorher. Am Bildschirm ändert der
    // Hintergrund nichts: die WebGL-Fläche ist undurchsichtig (`alpha: false`).
    const zurueck: (() => void)[] = [];
    if (schluessel) {
      for (const { canvas } of einsaetze) {
        const eigene = Object.getOwnPropertyDescriptor(canvas, 'toDataURL');
        Object.defineProperty(canvas, 'toDataURL', { value: () => 'data:,', configurable: true, writable: true });
        const wert = canvas.style.getPropertyValue('background-color');
        const prio = canvas.style.getPropertyPriority('background-color');
        canvas.style.setProperty('background-color', schluessel, 'important');
        zurueck.push(() => {
          if (eigene) Object.defineProperty(canvas, 'toDataURL', eigene);
          else delete (canvas as unknown as Record<string, unknown>)['toDataURL'];
          if (wert) canvas.style.setProperty('background-color', wert, prio);
          else canvas.style.removeProperty('background-color');
        });
      }
    }
    try {
      return await mitScrollstand(scrollStaende, () => toCanvas(wurzel, {
        width: breite,
        height: hoehe,
        ...(imVollbild
          ? {
              style: {
                position: 'fixed',
                left: '0px',
                top: '0px',
                right: 'auto',
                bottom: 'auto',
                margin: '0px',
                transform: 'none',
                width: `${breite}px`,
                height: `${hoehe}px`,
              },
            }
          : {}),
        canvasWidth: Math.round(breite * m),
        canvasHeight: Math.round(hoehe * m),
        pixelRatio: 1,
        backgroundColor: hintergrund,
        // Schriften werden nicht neu eingebettet: kostet Sekunden und ändert für
        // ein Lagebild nichts Wesentliches.
        skipFonts: true,
        // Owner-Abnahme 07.10.: «BILD: nicht möglich ([object Event])» — ein
        // einzelnes Bild, das nicht lädt, nimmt nicht mehr das ganze Bild mit.
        imagePlaceholder: LEERES_BILD,
        filter: (n) => !(n instanceof Element && n.hasAttribute(EIGENE_EBENE_ATTR)),
      }));
    } finally {
      for (const f of zurueck) f();
    }
  };
  let canvas: HTMLCanvasElement;
  if (einsaetze.length === 0) {
    canvas = await zeichne(null);
  } else {
    canvas = await zeichne(BLICK_SCHLUESSEL_SCHWARZ);
    const weiss = await zeichne(BLICK_SCHLUESSEL_WEISS);
    await setzeCanvasFlaechenEin(canvas, weiss, einsaetze, canvas.width / breite);
  }
  let geschwaerzt = 0;
  if (schwaerzenFuer(fuer)) {
    const ctx = canvas.getContext('2d');
    const flaechen = [...(wurzel.matches(NORMANSICHT_SELEKTOR) ? [wurzel] : []), ...wurzel.querySelectorAll(NORMANSICHT_SELEKTOR)]
      .filter(istSichtbar)
      .map(rechteck);
    if (ctx) geschwaerzt = schwaerzeRechtecke(ctx, flaechen, canvas.width / breite);
    else if (flaechen.length) throw new Error('Normansicht sichtbar, aber das Bild lässt sich nicht schwärzen — kein Bild gesendet.');
  }
  const url = canvas.toDataURL('image/jpeg', BLICK_BILD_QUALITAET);
  return {
    mimeType: 'image/jpeg',
    data: url.slice(url.indexOf(',') + 1),
    breite: canvas.width,
    hoehe: canvas.height,
    massstab: canvas.width / breite,
    geschwaerzt,
  };
}
