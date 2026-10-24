/**
 * Teil C · Claude und Kosmo als Figuren (Owner 07.10.2026, wörtlich: «gib
 * denen auch die gleichen funktionen und animationen wie die kosmoorbit maus
 * selbst und gib ihnen mehr leben und charakter, sie sind eigenständige
 * agenten … sie sind interaktiv und morphen viel»). Entwurf: Fläche
 * «KosmoOrbit Coop-Modus», Blätter C1–C3.
 *
 * Vier Teile:
 *  - **Spitze**: genau die Form der KosmoOrbit-Maus an dieser Stelle (Pfeil,
 *    Hand, Fadenkreuz, Kante, Spalte …, `zeiger-bilder.ts` `formZeichnung`),
 *    in der Farbe des Agenten; im Textfeld ein Schreibstrich. Beim Wechsel
 *    morpht sie (Ein-Animation je Form).
 *  - **Körper**: Claude ein Funke in Gold, Kosmo sein Orb mit Umlaufbahn und
 *    Mond. Er folgt der Spitze federnd, streckt sich in Fahrtrichtung, atmet
 *    in Ruhe, drückt sich beim Klick zusammen, dreht schneller beim Denken.
 *  - **Blick**: ein Punkt im Körper — schaut dorthin, wohin die Figur fährt,
 *    und zu deinem Zeiger, wenn er näher als 160 px kommt.
 *  - **Schild**: was der Agent gerade tut; beim Darüberfahren faltet es sich
 *    zur Karte mit den letzten Schritten und «Stopp» auf.
 *
 * Charakter über die Feder: Claude gleitet kritisch gedämpft (kein
 * Überschwingen, ruhig), Kosmo federt unterdämpft (schiesst los, schwingt
 * über, federt zurück). Dein Zeiger hat Vorrang: kommt er an den Körper
 * heran, weicht der Körper aus; die Spitze bleibt auf ihrem Ziel.
 *
 * Bei «weniger Bewegung»: keine Feder (die Figur steht sofort am Ziel), keine
 * Dauer-Animationen; Form, Zustand und Schild wechseln weiter.
 *
 * Die Figur liegt in der Sperrzone der KosmoMaus (`eigen()` an der Ebene):
 * ein Agent kann sie nicht anklicken, «Stopp» nimmt nur echte Klicks.
 */

import { useEffect, useMemo, useRef, useState } from 'react';
import { KButton } from '@kosmo/ui';
import {
  stoppeBedienen,
  URHEBER_NAME,
  useKosmoMaus,
  type AgentZeiger,
  type JournalEintrag,
  type Urheber,
} from '../../state/kosmo-maus-freigabe';
import { bevorzugtReduzierteBewegung, formVonComputedCursor, type CursorZustand } from '../../state/cursor-zustand';
import { formZeichnung } from '../zeiger-bilder';
import { DURCHLAESSIG_ATTR } from '../../state/kosmo-blick-live';

export type FigurForm = CursorZustand | 'text';
export type FigurZustand = 'ruhe' | 'klickt' | 'tippt' | 'zieht' | 'rollt' | 'denkt' | 'geht';

/** Charakter je Agent: Federhärte und Dämpfung (Spitze), Körper weicher. */
export const FEDER: Record<Urheber, { k: number; d: number; kKoerper: number; dKoerper: number }> = {
  // kritisch gedämpft: d = 2·√k — ruhig, ohne Überschwingen
  claude: { k: 140, d: 2 * Math.sqrt(140), kKoerper: 90, dKoerper: 2 * Math.sqrt(90) * 0.9 },
  // unterdämpft (≈ 0.5): schiesst los, schwingt über, federt zurück
  kosmo: { k: 260, d: 2 * Math.sqrt(260) * 0.5, kKoerper: 150, dKoerper: 2 * Math.sqrt(150) * 0.55 },
};

/** Versatz des Körpers zur Spitze (unten rechts, wie das Schild am eigenen Zeiger). */
export const KOERPER_VERSATZ = { x: 22, y: 26 };
/** Näher als so viel am rechten Rand: Körper und Schild öffnen nach links. */
export const RAND_LINKS_PX = 320;

/** Auf welcher Seite der Spitze stehen Körper und Schild? */
export function seiteFuer(x: number, breite: number): 'rechts' | 'links' {
  return x > breite - RAND_LINKS_PX ? 'links' : 'rechts';
}
/** Näher als so viel am unteren Rand: das Schild steht über der Spitze statt darunter. */
export const RAND_UNTEN_PX = 110;

/**
 * Wo steht das Schild? Unter dem Ziel, damit es den Eintrag nicht deckt, auf den die Spitze zeigt (Karten bis 48 px
 * Höhe, Abstand 4 px); nahe der Unterkante des Fensters gespiegelt darüber.
 */
export function schildLageFuer(y: number, hoehe: number): 'unten' | 'oben' {
  return y > hoehe - RAND_UNTEN_PX ? 'oben' : 'unten';
}
/** Näher als so viel schaut der Blick zu deinem Zeiger. */
export const BLICK_RADIUS_PX = 160;
/** Zeigst du näher als so viel an die Spitze (dorthin, wo der Agent arbeitet), weicht der Körper aus … */
export const AUSWEICH_RADIUS_PX = 30;
/** … um höchstens so viel. Fährst du direkt auf den Körper, bleibt er stehen und öffnet sich. */
export const AUSWEICH_HOECHSTENS_PX = 22;

/** C3 «Beide zugleich»: kommen sich Claude und Kosmo näher als das, halten ihre Körper Abstand. */
export const ABSTAND_PX = 64;
/** So weit schiebt der Abstand einen Körper höchstens beiseite (je Figur, beide weichen). */
export const ABSTOSS_HOECHSTENS_PX = 32;

/**
 * C3: Versatz, um den der eigene Körper vom Körper des anderen Agenten wegrückt. Null, wenn der andere
 * fehlt oder weiter weg ist als `ABSTAND_PX`; bei genau gleicher Lage nach rechts unten (eindeutig).
 * Beide Figuren rechnen dasselbe gegeneinander — so weichen beide je zur Hälfte.
 */
export function abstossVon(eigen: { x: number; y: number }, andere: { x: number; y: number } | null): { x: number; y: number } {
  if (!andere) return { x: 0, y: 0 };
  let dx = eigen.x - andere.x;
  let dy = eigen.y - andere.y;
  const abst = Math.hypot(dx, dy);
  if (abst >= ABSTAND_PX) return { x: 0, y: 0 };
  if (abst < 0.01) {
    dx = 1;
    dy = 1;
  }
  const l = Math.hypot(dx, dy);
  const stoss = ABSTOSS_HOECHSTENS_PX * (1 - abst / ABSTAND_PX);
  return { x: (dx / l) * stoss, y: (dy / l) * stoss };
}

/** Wo die Körper gerade stehen — je Urheber, damit die andere Figur Abstand halten kann. */
const koerperLagen = new Map<Urheber, { x: number; y: number }>();
const ANDERER: Record<Urheber, Urheber> = { claude: 'kosmo', kosmo: 'claude' };
/** Wie lange ein Zustand (Klicken, Tippen …) nach der Handlung sichtbar bleibt. */
export const ZUSTAND_MS: Record<Exclude<FigurZustand, 'ruhe' | 'geht'>, number> = {
  klickt: 700,
  tippt: 1600,
  zieht: 1200,
  rollt: 900,
  denkt: 4000,
};

const KLICK_AKTIONEN = new Set(['klick', 'doppelklick', 'rechtsklick', 'waehlen', 'datei']);

/** Welche Form trägt die Spitze? Handlung zuerst, sonst die Form der Stelle — wie deine Maus. */
export function formFuerAktion(aktion: string | undefined, zone: CursorZustand | null, istText: boolean): FigurForm {
  if (aktion === 'tippen' || aktion === 'taste') return 'text';
  if (aktion === 'ziehen') return 'greift';
  if (aktion === 'rad') return 'zeile';
  if (istText) return 'text';
  return zone ?? 'default';
}

/** Zustand der Figur aus dem jüngsten Journal-Eintrag dieses Agenten. */
export function zustandAusJournal(e: JournalEintrag | undefined, jetzt: number): FigurZustand {
  if (!e) return 'ruhe';
  const roh = jetzt - Date.parse(e.zeit);
  if (Number.isNaN(roh)) return 'ruhe';
  // Kleine negative Werte: Eintrag und Uhr im selben Augenblick — gilt als «jetzt».
  const alter = Math.max(0, roh);
  if (e.werkzeug === 'blick') return alter < ZUSTAND_MS.denkt ? 'denkt' : 'ruhe';
  if (e.werkzeug !== 'maus') return 'ruhe';
  if (e.aktion === 'tippen' || e.aktion === 'taste') return alter < ZUSTAND_MS.tippt ? 'tippt' : 'ruhe';
  if (e.aktion === 'ziehen') return alter < ZUSTAND_MS.zieht ? 'zieht' : 'ruhe';
  if (e.aktion === 'rad') return alter < ZUSTAND_MS.rollt ? 'rollt' : 'ruhe';
  if (KLICK_AKTIONEN.has(e.aktion)) return alter < ZUSTAND_MS.klickt ? 'klickt' : 'ruhe';
  return 'ruhe';
}

const VERB: Record<string, string> = {
  klick: 'klickt',
  doppelklick: 'doppelklickt',
  rechtsklick: 'öffnet das Menü',
  tippen: 'tippt',
  taste: 'drückt',
  ziehen: 'zieht',
  rad: 'rollt',
  waehlen: 'wählt',
  datei: 'lädt eine Datei',
  schweben: 'zeigt auf',
  bild: 'schaut hin',
  text: 'schaut hin',
  'text+bild': 'schaut hin',
};

/** Ein Ziel in Worten: Name des Elements, sonst sein Text, sonst die Kennung. */
export function zielInWorten(roh: string | undefined): string {
  if (!roh) return '';
  // Das Journal schreibt das Ziel als «[kennung]» (so wie die KosmoMaus es findet).
  const ziel = /^\[(.+)\]$/.exec(roh.trim())?.[1] ?? roh.trim();
  let el: Element | null = null;
  try {
    const sicher =
      typeof CSS !== 'undefined' && typeof CSS.escape === 'function' ? CSS.escape(ziel) : ziel.replace(/["\\]/g, '\\$&');
    el = document.querySelector(`[data-testid="${sicher}"]`);
  } catch {
    el = null;
  }
  const name = el?.getAttribute('aria-label')?.trim() || el?.textContent?.replace(/\s+/g, ' ').trim() || ziel;
  return name.length > 28 ? `${name.slice(0, 27)}…` : name;
}

/** «klickt «Speichern»» — was der Agent tut, in einem Satz. */
export function satzFuer(e: JournalEintrag | undefined): string {
  if (!e) return '';
  const verb = VERB[e.aktion] ?? e.aktion;
  if (e.werkzeug === 'blick') return verb;
  const ziel = zielInWorten(e.ziel);
  return ziel ? `${verb} «${ziel}»` : verb;
}

function istTextFeld(el: Element | null): boolean {
  if (!el) return false;
  if (el.tagName === 'TEXTAREA') return true;
  if (el.tagName === 'INPUT') return !['range', 'checkbox', 'radio', 'color', 'button', 'submit', 'reset', 'image', 'file'].includes((el as HTMLInputElement).type);
  return (el as HTMLElement).isContentEditable === true;
}

/** Form der Stelle wie bei deiner Maus: `--k-zeiger` oder `cursor` des Elements. */
function zonenFormBei(x: number, y: number): { zone: CursorZustand | null; istText: boolean } {
  if (typeof document.elementFromPoint !== 'function') return { zone: null, istText: false };
  const el = document.elementFromPoint(x, y);
  if (!el) return { zone: null, istText: false };
  let wert = '';
  try {
    const stil = getComputedStyle(el);
    wert = stil.getPropertyValue('--k-zeiger').trim() || stil.cursor;
  } catch {
    wert = '';
  }
  return { zone: formVonComputedCursor(wert), istText: istTextFeld(el) };
}

/** Spitze: die Form der KosmoOrbit-Maus als SVG, in der Farbe des Agenten. */
function Spitze({ form }: { form: FigurForm }) {
  if (form === 'text') {
    return (
      <svg className="agent-spitze-svg" width="32" height="32" viewBox="0 0 32 32" aria-hidden="true">
        <path d="M12 -6 h8 M16 -6 v20 M12 14 h8" transform="translate(0 6)" className="agent-strich" />
      </svg>
    );
  }
  const { zeichnung, drehungGrad } = formZeichnung(form);
  return (
    <svg className="agent-spitze-svg" width="32" height="32" viewBox="0 0 32 32" aria-hidden="true">
      <g transform={`translate(16 4)${drehungGrad ? ` rotate(${drehungGrad})` : ''} translate(-16 -4)`}>
        {zeichnung.striche.map((s, i) => (
          <path key={i} d={s.d} className="agent-strich" strokeWidth={s.breite + 0.25} />
        ))}
        {zeichnung.fuellungPfad && <path d={zeichnung.fuellungPfad} className="agent-fuellung" transform="rotate(-22.25 16 4)" />}
        {(zeichnung.punkte ?? []).map((p, i) => (
          <circle key={i} cx={p.cx} cy={p.cy} r={p.r} className="agent-punkt" />
        ))}
      </g>
    </svg>
  );
}

/** Körper: Claudes Funke oder Kosmos Orb mit Umlaufbahn und Mond. */
function Koerper({ urheber }: { urheber: Urheber }) {
  if (urheber === 'claude') {
    return (
      <svg className="agent-koerper-svg agent-funke" width="40" height="40" viewBox="0 0 72 72" aria-hidden="true">
        <path d="M36 4 C39 26 46 33 68 36 C46 39 39 46 36 68 C33 46 26 39 4 36 C26 33 33 26 36 4 Z" className="agent-koerper-flaeche" />
        <path d="M36 16 C38 30 42 34 56 36 C42 38 38 42 36 56 C34 42 30 38 16 36 C30 34 34 30 36 16 Z" className="agent-koerper-licht" transform="rotate(45 36 36)" />
      </svg>
    );
  }
  return (
    <span className="agent-orb" aria-hidden="true">
      <span className="agent-orb-kern" />
      <svg className="agent-koerper-svg agent-bahn" width="40" height="40" viewBox="0 0 72 72">
        <ellipse cx="36" cy="36" rx="33" ry="14" className="agent-bahn-linie" transform="rotate(-20 36 36)" />
        <circle cx="68" cy="30" r="4" className="agent-mond" />
      </svg>
    </span>
  );
}

interface Feder {
  x: number;
  y: number;
  vx: number;
  vy: number;
}

export function AgentFigur({ zeiger, gehend = false }: { zeiger: AgentZeiger; gehend?: boolean }) {
  const { urheber, x, y } = zeiger;
  const journal = useKosmoMaus((z) => z.journal);
  const eigene = useMemo(() => journal.filter((e) => e.urheber === urheber && (e.werkzeug === 'maus' || e.werkzeug === 'blick')), [journal, urheber]);
  const letzter = eigene[eigene.length - 1];
  const [jetzt, setJetzt] = useState(() => Date.now());
  const [offen, setOffen] = useState(false);
  const [form, setForm] = useState<FigurForm>('default');
  const reduziert = useMemo(() => bevorzugtReduzierteBewegung(), []);

  const spitzeRef = useRef<HTMLDivElement | null>(null);
  const koerperRef = useRef<HTMLDivElement | null>(null);
  const blickRef = useRef<HTMLSpanElement | null>(null);
  const zielRef = useRef({ x, y });
  zielRef.current = { x, y };
  const seite = seiteFuer(x, typeof window !== 'undefined' ? window.innerWidth : 1600);
  const schildLage = schildLageFuer(y, typeof window !== 'undefined' ? window.innerHeight : 900);
  const versatz = useRef(KOERPER_VERSATZ);
  versatz.current = { x: seite === 'links' ? -KOERPER_VERSATZ.x : KOERPER_VERSATZ.x, y: KOERPER_VERSATZ.y };
  // Die Figur kommt von oben links herein (C2 «Gleiten»), nicht aus dem Nichts.
  const spitze = useRef<Feder>({ x: reduziert ? x : x - 70, y: reduziert ? y : y - 50, vx: 0, vy: 0 });
  const koerper = useRef<Feder>({ x: spitze.current.x + KOERPER_VERSATZ.x, y: spitze.current.y + KOERPER_VERSATZ.y, vx: 0, vy: 0 });
  const dein = useRef<{ x: number; y: number } | null>(null);
  const offenRef = useRef(false);
  offenRef.current = offen;
  const schliessen = useRef<number | null>(null);
  const koerperInnen = useRef<HTMLDivElement | null>(null);
  const oeffne = (e: React.PointerEvent) => {
    if (!e.isTrusted) return;
    if (schliessen.current) window.clearTimeout(schliessen.current);
    schliessen.current = null;
    setOffen(true);
  };
  // Kurze Pause vor dem Schliessen: ein Zucken der Maus klappt die Karte nicht zu.
  const schliesse = () => {
    if (schliessen.current) window.clearTimeout(schliessen.current);
    schliessen.current = window.setTimeout(() => setOffen(false), 220);
  };
  useEffect(() => () => {
    if (schliessen.current) window.clearTimeout(schliessen.current);
  }, []);

  // Form der Stelle — nach der Handlung, wie deine Maus sie dort hätte.
  useEffect(() => {
    const { zone, istText } = zonenFormBei(x, y);
    setForm(formFuerAktion(letzter?.werkzeug === 'maus' ? letzter.aktion : undefined, zone, istText));
  }, [x, y, zeiger.zeit, letzter]);

  // Zeitlich begrenzte Zustände (Klicken, Tippen, Denken …) laufen von selbst ab.
  useEffect(() => {
    const t = window.setTimeout(() => setJetzt(Date.now()), 250);
    return () => window.clearTimeout(t);
  }, [jetzt, letzter]);

  // Dein Zeiger: nur echte Bewegungen.
  useEffect(() => {
    const merke = (e: PointerEvent) => {
      if (e.isTrusted) dein.current = { x: e.clientX, y: e.clientY };
    };
    window.addEventListener('pointermove', merke, { passive: true });
    return () => window.removeEventListener('pointermove', merke);
  }, []);

  // Die Feder: Spitze zum Ziel, Körper hinterher; Blick und Ausweichen.
  useEffect(() => {
    const f = FEDER[urheber];
    let vorher = performance.now();
    let rahmen = 0;
    const schritt = (nun: number) => {
      const dt = Math.min(1 / 30, Math.max(0, (nun - vorher) / 1000));
      vorher = nun;
      const ziel = zielRef.current;
      const s = spitze.current;
      const k = koerper.current;
      if (reduziert) {
        s.x = ziel.x;
        s.y = ziel.y;
        s.vx = s.vy = 0;
      } else {
        s.vx += (f.k * (ziel.x - s.x) - f.d * s.vx) * dt;
        s.vy += (f.k * (ziel.y - s.y) - f.d * s.vy) * dt;
        s.x += s.vx * dt;
        s.y += s.vy * dt;
      }
      // Körperziel: unten rechts der Spitze, weicht deinem Zeiger aus.
      const v = versatz.current;
      let kzx = s.x + v.x;
      let kzy = s.y + v.y;
      const d = dein.current;
      if (d && !offenRef.current) {
        // Nur nahe der Spitze: dort willst du etwas treffen, der Körper soll es nicht verdecken.
        const zurSpitze = Math.hypot(d.x - s.x, d.y - s.y);
        if (zurSpitze < AUSWEICH_RADIUS_PX) {
          const dx = kzx - d.x;
          const dy = kzy - d.y;
          const abst = Math.max(0.01, Math.hypot(dx, dy));
          const stoss = AUSWEICH_HOECHSTENS_PX * (1 - zurSpitze / AUSWEICH_RADIUS_PX);
          kzx += (dx / abst) * stoss;
          kzy += (dy / abst) * stoss;
        }
      }
      // C3: vom anderen Agenten wegrücken, wenn er zu nahe steht (beide weichen je zur Hälfte).
      const andere = koerperLagen.get(ANDERER[urheber]) ?? null;
      const ab = abstossVon({ x: kzx, y: kzy }, andere);
      kzx += ab.x;
      kzy += ab.y;
      if (reduziert) {
        k.x = kzx;
        k.y = kzy;
        k.vx = k.vy = 0;
      } else {
        k.vx += (f.kKoerper * (kzx - k.x) - f.dKoerper * k.vx) * dt;
        k.vy += (f.kKoerper * (kzy - k.y) - f.dKoerper * k.vy) * dt;
        k.x += k.vx * dt;
        k.y += k.vy * dt;
      }
      koerperLagen.set(urheber, { x: k.x, y: k.y });
      if (spitzeRef.current) spitzeRef.current.style.transform = `translate(${s.x - ziel.x}px, ${s.y - ziel.y}px)`;
      if (koerperRef.current) {
        const tempo = Math.hypot(k.vx, k.vy);
        const dehn = reduziert ? 0 : Math.min(0.28, tempo / 2400);
        const winkel = (Math.atan2(k.vy, k.vx) * 180) / Math.PI;
        koerperRef.current.style.transform =
          `translate(${k.x - ziel.x - v.x}px, ${k.y - ziel.y - v.y}px)` +
          (dehn > 0.01 ? ` rotate(${winkel}deg) scale(${1 + dehn}, ${1 - dehn * 0.6}) rotate(${-winkel}deg)` : '');
        koerperRef.current.dataset.bewegt = tempo > 40 ? 'ja' : 'nein';
      }
      // Blick: zu deinem Zeiger, wenn nah; sonst in Fahrtrichtung.
      if (blickRef.current) {
        let bx = s.vx;
        let by = s.vy;
        if (d && Math.hypot(d.x - k.x, d.y - k.y) < BLICK_RADIUS_PX) {
          bx = d.x - k.x;
          by = d.y - k.y;
        } else if (andere && Math.hypot(andere.x - k.x, andere.y - k.y) < ABSTAND_PX * 1.5) {
          // C3: nah beieinander schauen sie sich an — dein Zeiger geht vor.
          bx = andere.x - k.x;
          by = andere.y - k.y;
        }
        const l = Math.hypot(bx, by);
        const fx = l > 1 ? (bx / l) * 3.5 : 0;
        const fy = l > 1 ? (by / l) * 3.5 : 0;
        blickRef.current.style.setProperty('--blick-x', `${fx.toFixed(2)}px`);
        blickRef.current.style.setProperty('--blick-y', `${fy.toFixed(2)}px`);
      }
      rahmen = requestAnimationFrame(schritt);
    };
    if (typeof requestAnimationFrame !== 'function') return undefined;
    rahmen = requestAnimationFrame(schritt);
    return () => {
      cancelAnimationFrame(rahmen);
      koerperLagen.delete(urheber);
    };
  }, [urheber, reduziert]);

  const zustand: FigurZustand = gehend ? 'geht' : zustandAusJournal(letzter, jetzt);

  // Klick (C2 «Klickt»): der Körper drückt sich zusammen und federt zurück.
  // Per Web Animations statt Neuaufbau — sonst verschwände das Element unter
  // deinem Zeiger und die offene Karte klappte zu.
  const klickZeit = zustand === 'klickt' && letzter ? letzter.zeit : null;
  useEffect(() => {
    const el = koerperInnen.current;
    if (!klickZeit || !el || reduziert || typeof el.animate !== 'function') return;
    el.animate(
      [
        { transform: 'scale(1)' },
        { transform: 'scale(0.78, 0.86)', offset: 0.3 },
        { transform: 'scale(1.1)', offset: 0.65 },
        { transform: 'scale(1)' },
      ],
      { duration: 440, easing: 'cubic-bezier(0.4, 0, 0.2, 1)' },
    );
  }, [klickZeit, reduziert]);
  const name = URHEBER_NAME[urheber];
  const satz = satzFuer(letzter);
  // Die Karte nennt nur, was wirklich geschah (abgelehnte Versuche stehen im Verlauf in den Einstellungen).
  const letzteDrei = eigene.filter((e) => e.werkzeug === 'maus' && e.ergebnis === 'ok').slice(-3).reverse();

  return (
    <div
      className="agent-figur kosmo-maus-zeiger"
      data-testid={gehend ? 'kosmo-maus-zeiger-geht' : 'kosmo-maus-zeiger'}
      data-urheber={urheber}
      data-form={form}
      data-zustand={zustand}
      data-seite={seite}
      data-schild={schildLage}
      // lw-maus-sperrzone-esc: die Figur zeigt nur; die KosmoMaus zielt durch sie hindurch
      // (`elementAmPunkt` in state/kosmo-maus.ts). Erst beim Zeichnen gelesen (Ladereihenfolge, wie `eigen()`).
      {...{ [DURCHLAESSIG_ATTR]: '' }}
      style={{ left: x, top: y }}
    >
      {/* `key` = Zeitpunkt der Handlung: jede neue Handlung leuchtet neu auf (C17 A). */}
      {!gehend && <span key={zeiger.zeit} className="kosmo-maus-leuchten" data-testid="kosmo-maus-leuchten" aria-hidden="true" />}
      <div ref={spitzeRef} className="agent-spitze" aria-hidden="true">
        <div key={form} className="agent-spitze-form">
          <Spitze form={form} />
        </div>
      </div>
      <div
        ref={koerperRef}
        className="agent-koerper-lage"
        onPointerEnter={oeffne}
        onPointerLeave={schliesse}
      >
        <div className="agent-koerper" ref={koerperInnen}>
          <div className="agent-atem">
            <Koerper urheber={urheber} />
            <span ref={blickRef} className="agent-blick" />
          </div>
        </div>
        <div className={`agent-schild${offen ? ' agent-schild--offen' : ''}`} data-testid="kosmo-maus-figur-schild">
          <span className="kosmo-maus-zeiger-name">{name}</span>
          {zustand === 'tippt' ? (
            <span className="agent-tippt" aria-label="tippt">
              <span />
              <span />
              <span />
            </span>
          ) : satz ? (
            <span className="agent-satz">· {satz}</span>
          ) : null}
          {offen && (
            <div className="agent-karte" data-testid="kosmo-maus-figur-karte">
              {letzteDrei.length > 1 && (
                <ol className="agent-karte-vorher">
                  {letzteDrei.slice(1).map((e) => (
                    <li key={e.zeit + e.aktion}>{satzFuer(e)}</li>
                  ))}
                </ol>
              )}
              <KButton
                size="sm"
                tone="ghost"
                data-testid="kosmo-maus-figur-stopp"
                aria-label={`${name}: Bedienen beenden`}
                onClick={(ev) => ev.nativeEvent.isTrusted && stoppeBedienen('stopp')}
              >
                Stopp
              </KButton>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
