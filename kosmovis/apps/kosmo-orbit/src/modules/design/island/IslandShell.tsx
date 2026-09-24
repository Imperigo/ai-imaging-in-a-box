import {
  forwardRef,
  useEffect,
  useImperativeHandle,
  useLayoutEffect,
  useRef,
  useState,
  type ComponentType,
} from 'react';
// P-RUHE (v0.9.33): die Ruhe-Regel je Stufe steht als reine Funktion in
// `insel-ruhe.ts` — dort auch die Begruendung, warum ein Fenster ausgenommen ist.
import { ruheVerzoegerung } from './insel-ruhe';
import {
  DESIGN_INSELN,
  designInselKonfig,
  type InselKonfig,
  type IslandId,
  type IslandWerkzeug,
} from './island-katalog';
import { ISLAND_PILL_GLYPHEN } from './island-glyphen';
import { istTouchArtig, KTooltip, motion, useOverlaySchliessen } from '@kosmo/ui';
import { bevorzugtReduzierteBewegung } from '../../../state/cursor-zustand';
import { useProject } from '../../../state/project-store';
import { touchUndoGesteAktiv } from '../../../state/touch-undo';
import { werkzeugInPhaseSichtbar } from '../../../state/phasen-matrix';
import { designInhaltsRegistry, type InhaltsRegistry } from './inhalte/registry';
import { InselStufeContext } from './insel-stufe';
// Registrierung der Stufe-2/3-Inhalte als Import-Seiteneffekt (Fable-Naht
// für PD3a ‖ PD3b — s. `inhalte/registry.ts`-Kopfkommentar).
import './inhalte/zeichnen';
import './inhalte/ansicht';
import './inhalte/projekt';
import './inhalte/austausch';
// v0.9.2 P-P2 (`docs/V092-SPEZ.md` §P-P2): Profil-Manager — additiver
// fünfter Import, registriert das neue PROJEKT-Werkzeug `profil` (eigene
// Datei statt `inhalte/projekt.tsx`, um deren Dateikreis nicht anzufassen).
import './inhalte/profile';
import './island.css';

/**
 * IslandShell (PD1 Fundament, `docs/ISLAND-UI-SPEZ.md` §4.1/§4.2/§4.3).
 *
 * Zustandsmaschine EINER Island: `pill` ↔ `leiste` ↔ `popup` ↔ `fenster`.
 * PD1 rendert Pill+Leiste vollständig; Popup/Fenster sind bewusst minimale,
 * leere Rahmen mit korrekter Animation/testid — Inhalte kommen erst PD3
 * (§7-Tabelle, PD1-Zeile: «Stufen 0–1 mit statischem Werkzeug-Katalog»).
 *
 * Ablageort app-lokal (Fable-Entscheid, kein zweiter Ort in `packages/kosmo-ui`
 * — Promotion erst, wenn eine zweite Station die Island-UI braucht).
 *
 * **App-lokal statt `state/ui-zustand.ts`:** dieser Automat ist reiner
 * Präsentations-/UI-Zustand einer einzelnen Insel (Stufe, aktives Werkzeug,
 * Toast) — kein Store-Feld, das Kosmo/E2E/Persistenz brauchen (anders als
 * `tool`/`viewMode`). Die echte `ToolId`-Verdrahtung (PD2) wird DIESEN
 * lokalen Zustand mit dem bestehenden `useUiZustand`-Store verbinden, ihn
 * aber nicht ersetzen — «Stufe» ist nirgends heute im Store abgebildet.
 */

/** Toast-Anzeigedauer für Werkzeuge ohne Popup (§4.2, Prototyp `pickTool`). */
const TOAST_MS = 1700;
/** PB2 (Bauauftrag Punkt 2): Verzögerung, bevor der Lang-Hover-Tooltip am
 *  Werkzeugknopf erscheint. */
const TOOLTIP_VERZOEGERUNG_MS = 600;
/** D-8 (E-8 C, `docs/design/GESTALTUNGS-ENTSCHEIDE-2026-08-10.md`): der Lang-Hover-
 *  Tooltip ist auf Touch unsichtbar (kein Hover; der Tap feuert zwar
 *  `pointerenter`, aber `pointerleave` folgt beim Fingerheben lange vor den
 *  600ms). Tooltip-Ersatz ist das EINE Muster «Label bei Aktivierung»:
 *  aktiviert Touch/Pen ein Popup-Werkzeug, erscheint sein Label 1.5s als
 *  Badge an der Insel (Eintritt `--k-motion-settle`, Austritt
 *  `--k-motion-fast`, island.css). Werkzeuge OHNE Popup zeigen ihr Label
 *  bereits über den bestehenden Toast (jeder Zeigertyp, s. `zeigeToast`) —
 *  dort braucht es kein zweites Schild. KEIN Long-press (E-8, iPadOS-
 *  Kollision). */
const TOUCH_BADGE_MS = 1500;
/** Austrittsdauer des Badges = `--k-motion-fast` (120ms) — aus dem
 *  tokens.ts-Spiegel gelesen statt als zweite Zahlenquelle hart kodiert. */
const TOUCH_BADGE_AUSTRITT_MS = Number.parseInt(motion.fast, 10);

/**
 * P-EINGABE (v0.9.35, O-T2) — Messung: der manuelle Schliessen-Weg (X-Knopf/
 * Esc/Aussenklick, `schliessePopupOderFenster` unten) entfernt Popup/Leiste/
 * Fenster SYNCHRON aus dem DOM — mehrere E2E-Specs pruefen dort
 * `toHaveCount(0)` UNMITTELBAR nach dem Klick, ohne Wartefenster
 * (`island.css`s Kopfkommentar bei «Schliessen»: «BEWUSST NICHT umgesetzt
 * als echte Austrittsanimation»). Der AUTOMATISCHE P-RUHE-Weg
 * (`aufPointerLeave` unten) traegt exakt dieselbe React-Mechanik (`setStufe`)
 * und darum exakt dieselbe Luecke — der Owner-Befund woertlich: «beim
 * automatischen Schliessen (P-RUHE) gar keine Animation».
 *
 * Der manuelle Weg bleibt HIER unangetastet (kein bestehender Test bewegt
 * sich). Der automatische Weg bekommt ein ECHO: kurz bevor `setStufe` das
 * echte Element entfernt, wird eine rein visuelle Kopie (`cloneNode`, ohne
 * Handler, `pointer-events:none`) exakt an ihrer letzten Bildschirmstelle
 * (`getBoundingClientRect`) AUSSERHALB des React-Baums (direkt an
 * `document.body`) eingehaengt, spielt die Schliessen-Animation und raeumt
 * sich danach selbst weg. Das ECHTE Element verschwindet weiterhin EXAKT
 * zur bisherigen Zeit — `setStufe` selbst bleibt unveraendert synchron, der
 * bestehende 1000ms-Rueckklapp-Test (`island-shell.test.tsx`) bewegt sich
 * darum keine Millisekunde. In jsdom liefert `getBoundingClientRect` ohne
 * Stub ein 0×0-Rechteck (kein Layout-Engine) — das Echo ist dort ein reiner
 * No-op, s. `test/island-schliess-echo.test.tsx` fuer den gestellten
 * Nachweis mit gestubbtem Rechteck.
 *
 * Ausgenommen: `prefers-reduced-motion` (kein Echo, sofortiges Verschwinden
 * wie bisher) und `navigator.webdriver` (dieselbe Hartvertrags-Konvention
 * wie `state/abspiel-ebene.ts`/`shell/CursorEbene.tsx` — kein zusaetzliches
 * DOM-Element, das eine der ~40 direkt klickenden Specs je zu Gesicht
 * bekaeme).
 */
const SCHLIESS_ECHO_MS = 160;

function spieleSchliessEcho(original: HTMLElement | null): void {
  if (!original) return;
  if (typeof window === 'undefined' || typeof document === 'undefined' || typeof navigator === 'undefined') return;
  if (navigator.webdriver === true) return;
  if (typeof window.matchMedia === 'function' && window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    return;
  }
  const rect = original.getBoundingClientRect();
  if (rect.width < 1 || rect.height < 1) return;

  const klon = original.cloneNode(true) as HTMLElement;
  // Keine Testid darf doppelt im Dokument landen — das Echo lebt ausserhalb
  // von `container` in jedem Test, aber sicher ist sicher (globale Queries).
  klon.removeAttribute('data-testid');
  for (const el of Array.from(klon.querySelectorAll<HTMLElement>('[data-testid]'))) el.removeAttribute('data-testid');
  // Die Oeffnen-Animation nicht erneut abspielen (frisches Element = frische
  // Animation) — nur das Echo selbst animiert (unten).
  klon.classList.remove('isl-anim-islIn', 'isl-anim-popIn', 'isl-anim-winIn');
  // Die Original-Positionsregeln (`.isl-popup`/`.isl-leiste`, teils
  // ahnenabhaengig ueber `.isl-rand-*`) gelten hier nicht mehr — der Klon
  // haengt ausserhalb von `.isl-root`. Inline-Stile gewinnen gegen die
  // Klassen-Regeln und fuellen stattdessen exakt die Huelle unten.
  klon.style.position = 'absolute';
  klon.style.inset = '0';
  klon.style.margin = '0';
  klon.style.transform = 'none';

  const huelle = document.createElement('div');
  huelle.className = 'isl-echo';
  huelle.style.left = `${rect.left}px`;
  huelle.style.top = `${rect.top}px`;
  huelle.style.width = `${rect.width}px`;
  huelle.style.height = `${rect.height}px`;
  huelle.appendChild(klon);
  document.body.appendChild(huelle);

  let entfernt = false;
  const raeumen = () => {
    if (entfernt) return;
    entfernt = true;
    huelle.remove();
  };
  huelle.addEventListener('animationend', raeumen);
  // Sicherheitsnetz (Muster `KosmoZeichnet.tsx`s `puls()`): ein verschlucktes
  // `animationend` (reduced-motion-Riegel greift theoretisch schon vorher,
  // aber sicher ist sicher) darf das Echo nie dauerhaft im DOM lassen.
  setTimeout(raeumen, SCHLIESS_ECHO_MS + 300);
}

/**
 * PB2 (`docs/V084-SPEZ.md` §7 Sanktion 3, E8): rendert eine Katalog-`glyphe`
 * — ein echtes Icon (`ComponentType`) gewinnt, ein `string` bleibt der
 * Text-Kürzel-Fallback (aktuell nur `skizze`, s. `island-katalog.ts`-
 * Kopfkommentar; auch künftige Stations-Konfigs ohne Icon-Zuordnung fallen
 * hierauf zurück, statt zu crashen).
 */
function WerkzeugGlyphe({ glyphe, size }: { glyphe: string | ComponentType<{ size?: number }>; size: number }) {
  if (typeof glyphe === 'string') return <>{glyphe}</>;
  const Icon = glyphe;
  return <Icon size={size} />;
}

/**
 * PB2 (Bauauftrag Punkt 4, D15-Folgefund): drei Insel-Werkzeuge committen
 * ihre eigentliche Handlung über einen Klick AUSSERHALB der Insel (Plan-/
 * Viewport-Canvas) WÄHREND ihr Popup/Fenster offen bleibt — Öffnung (Klick
 * auf eine Wand), Messen (Klickkette bis Doppelklick/Esc) und Kommentar
 * (Klick setzt den Punkt, das Formular erscheint danach IM selben Popup,
 * `e2e/masskette-kommentar.spec.ts`). Ein generisches App-weites
 * Aussenklick-Schliessen (§1.1) würde ihr Popup schon beim ERSTEN
 * Arbeits-Klick wegreissen, bevor der Nutzer fertig ist — bewiesen durch
 * genau diese Spec (»Kommentar: Klick setzt NUR den Punkt … das Formular
 * erscheint jetzt«, prüft `island-kommentar-text` NACH einem Canvas-Klick
 * bei weiterhin offenem Popup). Diese drei bleiben darum von der neuen
 * Aussenklick-Regel ausgenommen; Esc schliesst sie trotzdem (kollidiert mit
 * keinem bestehenden Test, s. Bauagenten-Bericht).
 *
 * v0.9.4 P-KV (664-Bericht): die drei Mass-Werkzeuge aus P-PB Teil 2
 * (Höhenkote/Winkelmass/Radialmass, `DesignWorkspace.tsx`s `tool===…`-Zweige)
 * committen fachlich nach demselben Muster — ein bzw. mehrere Klicks IM Plan
 * bei offenem Popup/Fenster (Winkelmass/Radialmass sammeln erst eine
 * Klickkette wie Messen, Höhenkote committet mit dem ersten Klick wie
 * Stütze). Ohne Ausnahme fiel das Popup nach dem ersten Arbeits-Klick auf
 * «Leiste» zurück — kein Kettenbruch (die Punkte kamen trotzdem an), aber ein
 * Bedien-Rückschritt (Vorgabe-Felder verschwinden mitten in der Eingabe).
 */
/**
 * B140 — in welche Richtung die Leiste verschwindet, je Randlage.
 *
 * Erster Wert: die Glyphe zum Einklappen (zeigt dorthin, wo die Leiste
 * hingeht). Zweiter Wert: die zum Ausklappen (zeigt, wo sie wieder
 * herauskommt).
 *
 * **Der Schluessel ist die Randklasse, nicht der Stationsname.** Die
 * Randklasse steht schon in der Insel-Konfig und entscheidet die Lage — eine
 * zweite Tabelle ueber Stationen daneben waere die naechste, die veraltet,
 * sobald eine Insel umzieht. Dieselbe Familie wie das `▾` am Werkzeug mit
 * Einstellungen, damit kein zweiter Symbolsatz entsteht.
 */
const EINKLAPP_GLYPHEN: Readonly<Record<string, readonly [string, string]>> = {
  'isl-rand-links': ['◂', '▸'],
  'isl-rand-rechts': ['▸', '◂'],
  'isl-rand-oben': ['▴', '▾'],
  'isl-rand-unten': ['▾', '▴'],
};

const AUSSENKLICK_AUSNAHME = new Set([
  'oeffnung',
  'messen',
  'kommentare',
  'hoehenkote',
  'winkelmass',
  'radialmass',
]);

export type IslandStufe = 'pill' | 'leiste' | 'popup' | 'fenster';

// PC0 v0.8.4: die Rand-Klassen leben jetzt in der `InselKonfig`
// (`island-katalog.ts`s `DESIGN_INSELN` für design) — die Shell liest nur
// noch `konfig.randKlasse` und ist damit stationsagnostisch (V084-SPEZ E1).

/**
 * Liest `prefers-reduced-motion: reduce` initial UND hält es über die
 * Lebensdauer der Komponente aktuell (MediaQueryList-`change`-Event) — anders
 * als der einmalige Lese-Helfer `bevorzugtReduzierteBewegung()` selbst
 * (`state/cursor-zustand.ts`, wiederverwendet statt eines zweiten
 * `matchMedia`-Aufrufmusters).
 */
/**
 * Exportiert (PD4-Ergänzung, additiv): `island/KosmoOrb.tsx` braucht
 * denselben Live-`prefers-reduced-motion`-Zustand für seinen Puls-Ring
 * (`orbPulse`, §4.3-Tabelle) — ein zweiter, unabhängiger `matchMedia`-Aufruf
 * wäre unnötige Duplikation desselben Musters. Verhalten/Signatur bleiben
 * exakt wie zuvor, nur die Sichtbarkeit ändert sich (`function` → `export
 * function`).
 */
export function useReduzierteBewegung(): boolean {
  const [reduziert, setReduziert] = useState(() => bevorzugtReduzierteBewegung());

  useEffect(() => {
    if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') return;
    const mql = window.matchMedia('(prefers-reduced-motion: reduce)');
    const aufAenderung = () => setReduziert(mql.matches);
    mql.addEventListener('change', aufAenderung);
    return () => mql.removeEventListener('change', aufAenderung);
  }, []);

  return reduziert;
}

/**
 * §10.1 (`docs/V083-SPEZ.md`, Bounding-Box-Clamping analog `design.css:186-
 * 198`s `.dw-dropdown`-Präzedenzfall «Scroll statt Überlapp»): stösst ein
 * Popup/Fenster, dessen `getBoundingClientRect()` den Viewport verlässt,
 * über zwei additive CSS-Custom-Properties (`--isl-clamp-x`/`-y`, `island.
 * css`) wieder zurück in die sichtbare Fläche. Die Properties wirken additiv
 * ZUR bestehenden `translateX(-50%)`-Zentrierung jeder Insel-Rand-Position
 * (`island.css`s vier `.isl-rand-*`-Anker bleiben unverändert) — kein
 * Eingriff in die Anker-Logik selbst, nur ein nachträglicher Korrekturvektor
 * je gerendertem Popup/Fenster. IMMER zuerst auf `0px` zurückgesetzt, bevor
 * neu gemessen wird — sonst würde ein bereits angewandter alter Offset die
 * neue Messung verfälschen (kumulative Fehlrechnung bei mehrfachem Aufruf,
 * z. B. durch den ResizeObserver unten).
 */
const ISL_VIEWPORT_RAND_PX = 8;
/** Abstand Popup↔Leiste nach einer Kollisions-Ausweichung (s. u.). */
const ISL_LEISTE_ABSTAND_PX = 6;
/** Derselbe Randabstand, wiederverwendet als Luft zwischen einem Fenster/
 *  Popup und einer Sperrzone (Kopf/fremde Pille, s. `ermittleSperrzonenRand`
 *  unten) — kein zweiter Zahlenwert für dieselbe Idee. */
const ISL_SPERRZONE_ABSTAND_PX = ISL_VIEWPORT_RAND_PX;

/**
 * Der Kasten, den ein Element **in Ruhe** einnimmt — ohne die gerade
 * laufende Eintritts-Animation.
 *
 * **Der Befund, der diese Funktion nötig macht** (P-RAND, `docs/V0929-SPEZ.md`
 * §1; Sonde 2 des ersten Sondenlaufs, `docs/SICHTPRUEFUNG.md`): die Klammer
 * misst im `useLayoutEffect`, also VOR dem ersten Paint — und dort steht
 * `popIn`/`winIn` (island.css) noch auf seinem 0%-Keyframe
 * (`translateY(+4px) scale(0.9)`). `getBoundingClientRect()` bezieht laufende
 * Transformationen mit ein; die Klammer rechnete darum mit einem Kasten, der
 * ein Zehntel zu kurz und 4px zu tief steht, und korrigierte um genau
 * `0.1 · Höhe − 4px` **zu wenig**. Genau dieser Betrag steht in den sechs
 * Rotfällen — nachgerechnet, nicht vermutet:
 *  · KosmoVis, Popup «sonnenstunden» (Höhe 123.1): `0.1·123.1 − 4 = 8.3` →
 *    gemeldete Unterkante **900.3** statt 892 im 900er-Fenster, **800.3**
 *    statt 792, **768.3** statt 760. Derselbe Betrag in jedem Fenster.
 *  · KosmoPublish, Popup «dossier» (Höhe 554.4): `0.1·554.4 − 4 = 51.4` →
 *    gemeldete Oberkante **289.0** statt 237.6 (Fenster 800) und **257.0**
 *    statt 205.6 (Fenster 768).
 * Ein Fehlbetrag, der nicht mit der Fenstergrösse wandert, ist die Signatur
 * einer **Rechnung**, nicht einer Platznot — darum wird hier die Rechnung
 * geheilt und keine Fläche verkleinert (E-10: eine Insel scrollt nicht, und
 * sie wirft auch keine Werkzeuge weg).
 *
 * Die Antwort ist bewusst **kein zweiter Messzeitpunkt nach der Animation**
 * (das wäre ein sichtbares Nachrücken um bis zu 51px), sondern: die
 * endlichen Animationen des Elements werden für die Dauer der Messung an ihr
 * **Ende** gestellt — dort tragen sie mangels `fill: forwards` nichts mehr
 * bei, das Element steht also in seiner Ruhelage — und unmittelbar danach
 * exakt auf ihre alte Laufzeit zurückgesetzt. Zwischen beiden Zuweisungen
 * liegt kein Paint: die Animation läuft unverändert weiter, nur die MESSUNG
 * sieht die Ruhelage. Damit stimmt schon der erste Paint.
 *
 * Unendliche Animationen (Puls-Ringe) bleiben unangetastet — sie haben kein
 * Ende, und ihr Kasten IST ihre Ruhelage. `Element.getAnimations` fehlt in
 * jsdom: dort fällt die Funktion auf die reine Messung zurück, jeder
 * Bestandstest misst weiter wie bisher (s. `test/island-shell.test.tsx`s
 * Klammer-Fälle, die `getBoundingClientRect` stubben).
 */
export function ruheKasten(el: HTMLElement): DOMRect {
  const mitAnimationen = el as HTMLElement & { getAnimations?: () => Animation[] };
  if (typeof mitAnimationen.getAnimations !== 'function') return el.getBoundingClientRect();
  const gemerkt: Array<{ animation: Animation; zeit: CSSNumberish }> = [];
  try {
    for (const animation of mitAnimationen.getAnimations()) {
      const zeit = animation.currentTime;
      const ende = animation.effect?.getComputedTiming().endTime;
      // `zeit === null` = noch nie gelaufen (nichts anzuwenden, und ein
      // Zurücksetzen auf `null` wäre laut Spec ein Fehler); `endTime` ohne
      // endliche Zahl = eine unendliche Animation.
      if (zeit === null || typeof ende !== 'number' || !Number.isFinite(ende)) continue;
      gemerkt.push({ animation, zeit });
      animation.currentTime = ende;
    }
    return el.getBoundingClientRect();
  } finally {
    for (const g of gemerkt) g.animation.currentTime = g.zeit;
  }
}

/**
 * G4/G1 (`ROADMAP` 1246-Nachfolge, ein Tag nach P-VOLLBILD 1259): die
 * Viewport-Klammer kannte bislang nur ZWEI Sperrflächen — den Viewport-Rand
 * selbst (oben) und die EIGENE `.isl-leiste` (unten) — nicht aber die zwei
 * Flächen, die AUSSERHALB jeder `.isl-root` liegen und trotzdem fix auf dem
 * Bildschirm stehen: den globalen Kopf (`.isl-kopf-zweitgruppe`, immer oben
 * rechts, trägt u. a. `starter-guide-start`) und die PILLEN der gerade
 * GESCHLOSSENEN Nachbarinseln (`.isl-pill` — die eigene Insel zeigt while
 * offen nie ihre eigene Pille, jeder gefundene Treffer gehört also einer
 * anderen Insel). Ein an den Viewport geklammertes PROJEKT-Fenster kann bei
 * schmalem/kurzem Fenster beide Flächen decken: den Kopf am oberen Rand
 * (G1, alle drei Grössen) UND — bei 1024×768 zusätzlich, weil das Fenster
 * dort auch horizontal bis in die Pillen-Spalte reicht — ANSICHT/AUSTAUSCH
 * (G4, 13 Funde NUR bei 1024×768). Der Klick auf diese Flächen ist dabei
 * kein "kollidiert, aber ein zweiter Mechanismus rettet" wie beim ✕-Knopf
 * (G1: der Aussenklick schliesst trotzdem) — er ist ein STUMMER Totklick,
 * weil der Punkt auf dem Fenster selbst landet, nicht ausserhalb davon.
 *
 * **B116-Nachtrag** (`docs/UI-UX-2026-09-05-B112-RENDER-SENDEN.md` §3–§4,
 * Fund: 1 unentschuldigt, vis @ 1024×768, Insel «sonne», Fenster
 * `sonnenstunden` unter `island-sonnenstunden-stufe2`): dieselben zwei
 * Sperrflächen deckten eine dritte Lage NICHT ab — eine **offene** Leiste
 * einer fremden Insel (`.isl-leiste`, `island.css:235`). Eine geschlossene
 * Nachbarinsel zeigt `.isl-pill` und stand seit G4 in der Liste; eine
 * offene zeigt stattdessen `.isl-leiste` und stand in KEINER der beiden
 * Sorten — der Zeiger ruhte auf `austausch`, ihre Leiste war offen, und das
 * Fenster von `sonne` rechnete, als wäre dort nichts. Anders als bei
 * `.isl-pill` gilt die Ausnahme «nicht die eigene Insel» hier zwingend: die
 * eigene Insel zeigt ihre eigene `.isl-leiste` WÄHREND offen sehr wohl (s.
 * die JSX-Verzweigung unten im Rückgabewert der Komponente, `stufe ===
 * 'pill' ? …Pille… : …Leiste…`) — ohne den Ausschluss würde jedes offene
 * PROJEKT-/KosmoVis-Fenster vor der eigenen, gerade sichtbaren Werkzeug-
 * leiste zurückweichen, obwohl beide zur selben `.isl-root` gehören und
 * einander gar nicht stören. Die eigene Insel-Wurzel (`eigeneWurzel`,
 * `el.closest('.isl-root')` in `klammereInViewport`) wird darum durch-
 * gereicht und jede `.isl-leiste`, die `eigeneWurzel.contains(...)` liefert,
 * bleibt aussen vor — der Rest der Funktion (horizontale Überschneidung,
 * Kantenzuordnung) ist unverändert.
 *
 * Ermittelt für EINE Achse (oben ODER unten), wie weit die Klammer von
 * dieser Kante zurückweichen muss, um jede Sperrzone zu meiden, deren
 * horizontale Lage die (bereits x-geklammerte) Kandidatenfläche
 * tatsächlich überschneidet — kein blindes Pauschal-Polster: ein Fenster,
 * das den Kopf/eine Pille horizontal gar nicht erreicht (die drei anderen
 * PROJEKT-Werkzeuge bei 1180×820/1400×900 oder jede andere Insel), bekommt
 * exakt denselben `ISL_VIEWPORT_RAND_PX`-Rand wie bisher.
 */
function ermittleSperrzonenRand(
  kandidatLinks: number,
  kandidatRechts: number,
  vh: number,
  eigeneWurzel: Element | null,
): { oben: number; unten: number } {
  if (typeof document === 'undefined') return { oben: ISL_VIEWPORT_RAND_PX, unten: ISL_VIEWPORT_RAND_PX };
  const zonen: HTMLElement[] = [];
  const kopf = document.querySelector<HTMLElement>('.isl-kopf-zweitgruppe');
  if (kopf) zonen.push(kopf);
  zonen.push(...Array.from(document.querySelectorAll<HTMLElement>('.isl-pill')));
  // B116: offene Leisten FREMDER Inseln sind dieselbe Art Sperrfläche wie
  // geschlossene Pillen (s. Kopfkommentar) — die eigene wird ausgeschlossen,
  // weil sie (anders als `.isl-pill`) während offen sehr wohl die eigene ist.
  for (const leiste of Array.from(document.querySelectorAll<HTMLElement>('.isl-leiste'))) {
    if (eigeneWurzel && eigeneWurzel.contains(leiste)) continue;
    zonen.push(leiste);
  }

  let oben = ISL_VIEWPORT_RAND_PX;
  let unten = ISL_VIEWPORT_RAND_PX;
  for (const zone of zonen) {
    const z = zone.getBoundingClientRect();
    if (z.width < 1 || z.height < 1) continue;
    const ueberschneidetX = kandidatLinks < z.right && kandidatRechts > z.left;
    if (!ueberschneidetX) continue;
    // Näher an der Ober- als an der Unterkante? Dann ist es eine "obere"
    // Sperrzone (Kopf, ANSICHT-Pille), sonst eine "untere" (AUSTAUSCH-
    // Pille). Eine seitliche Pille (ZEICHNEN links, vertikal mittig) landet
    // damit in einer der beiden Gruppen, überschneidet aber nach der obigen
    // X-Prüfung ohnehin so gut wie nie ein PROJEKT-Fenster.
    if (z.top < vh - z.bottom) oben = Math.max(oben, z.bottom + ISL_SPERRZONE_ABSTAND_PX);
    else unten = Math.max(unten, vh - z.top + ISL_SPERRZONE_ABSTAND_PX);
  }
  return { oben, unten };
}

function klammereInViewport(el: HTMLElement): void {
  if (typeof window === 'undefined') return;
  el.style.setProperty('--isl-clamp-x', '0px');
  el.style.setProperty('--isl-clamp-y', '0px');
  // Zurücksetzen VOR der ersten Messung — sonst würde eine aus einem
  // früheren Aufruf stehengebliebene kleinere Deckelung (s. u.) die
  // natürliche Höhe hier bereits künstlich klein messen (dieselbe Lehre wie
  // beim `--isl-clamp-x/-y`-Reset zwei Zeilen darüber).
  el.style.removeProperty('--isl-clamp-max-height');
  let r = ruheKasten(el);
  const vw = window.innerWidth;
  const vh = window.innerHeight;
  let dx = 0;
  if (r.left < ISL_VIEWPORT_RAND_PX) dx = ISL_VIEWPORT_RAND_PX - r.left;
  else if (r.right > vw - ISL_VIEWPORT_RAND_PX) dx = vw - ISL_VIEWPORT_RAND_PX - r.right;

  // B116: vorgezogen (stand vorher erst bei der Quer-Ausweichung unten) —
  // `ermittleSperrzonenRand` braucht die eigene Insel-Wurzel, um ihre eigene
  // (während offen sehr wohl sichtbare) `.isl-leiste` auszuschliessen.
  const wurzel = el.closest('.isl-root');
  let { oben: reserviertOben, unten: reserviertUnten } = ermittleSperrzonenRand(r.left + dx, r.right + dx, vh, wurzel);

  // P04-WURZEL (ROADMAP 1475, V015-SPEZ P04, Abnahme berichtigt am
  // 16.09.2026): `ermittleSperrzonenRand` lässt die EIGENE Leiste bewusst
  // aussen vor (B116, s. Kopfkommentar dort) — richtig für den REIN
  // POSITIONELLEN Zwang (eine ruhende eigene Leiste verlangt für sich allein
  // keinen Rückzug), aber falsch für die HÖHE: bei sehr hohem Inhalt bindet
  // die eigene Leiste UND eine fremde Sperrzone GLEICHZEITIG denselben Rand
  // (oben bei `isl-rand-oben`, unten bei `isl-rand-unten`), und `sichereHoehe`
  // kannte bislang nur die Sperrzone. Die Folge: die Quergate-Ausweichung
  // sechs Zeilen weiter unten überschrieb den aus der Sperrzone gerechneten
  // Rückzug vollständig mit einem Wert, der NUR die eigene Leiste kennt (live
  // gemessen: `--isl-clamp-y` landete bei -2px statt der für die Sperrzone
  // rechnerisch nötigen rund -98px, KosmoPrepare/WISSEN/Werkbank-FENSTER
  // @1400×900 — die -98px waren allerdings NUR gegen die Pille gerechnet,
  // nie gegen die Kombination mit der eigenen Leiste, s. u.).
  //
  // Der Fix hier behebt die WURZEL für Stufe 3 (Fenster), nicht das Symptom:
  // die eigene Leiste wird — NUR für horizontal verankerte Inseln
  // (`isl-rand-oben`/`isl-rand-unten`, deren Popup/Fenster in GENAU derselben
  // Achse wächst wie die Leiste selbst liegt) — direkt in die
  // Höhen-Reservierung aufgenommen, bevor `sichereHoehe` rechnet. Ein zu
  // hohes Fenster (E-10 AUSNAHME 1, `.isl-fenster` scrollt bereits
  // sanktioniert) schrumpft damit auf eine Höhe, die BEIDE Zwänge gleichzeitig
  // respektiert — die anschliessende Quergate-Prüfung findet dann gar keine
  // Überdeckung der eigenen Leiste mehr vor, die sie überschreiben müsste.
  // GEMESSEN (KosmoPrepare/WISSEN/Werkbank-Fenster @1400×900, gebauter
  // Preview-Build): Höhe sinkt von 832px auf 678px, neue Lage 114–793px —
  // klar VOR der Sperrzone (844px) UND VOR der eigenen Leiste (106px)
  // zugleich, 0 Überdeckung. `--isl-clamp-y` selbst bleibt dabei klein
  // (~-2px, nicht -98px): die Reparatur wirkt über eine kleinere Höhe, nicht
  // über eine grössere Verschiebung — die -98px waren nie erreichbar, ohne
  // die eigene Leiste zu verdecken.
  //
  // Vertikale Inseln (`isl-vertikal`, Leiste seitlich) bleiben unangetastet —
  // ihre Quergate-Ausweichung verschiebt `dx`, nicht `dy`, und war nie das
  // Terrain dieses Funds (bestehender Unit-Test „W2-Quergate-Fund: … vertikale
  // Insel" bleibt unverändert grün).
  //
  // DOKUMENTIERTE GRENZE, NICHT BEHOBEN — Stufe 2 (Popup) derselben Werkbank:
  // `.isl-popup` referenziert `--isl-clamp-max-height` bewusst NICHT (E-10
  // O-12, „Stufe 2 scrollt nie" — s. Kommentar bei `sichereHoehe` unten),
  // sein gemessener Inhalt ist mit **1139,6px** bereits GRÖSSER als der ganze
  // Viewport (**900px** bei 1400×900): selbst OHNE jede Sperrzone bräuchte es
  // **-404px** Verschiebung, was das Popup grossteils über den oberen Rand
  // schöbe. Zwei Verbote schliessen eine Reparatur hier: Stufe 2 scrollen zu
  // lassen widerspricht E-10 O-12 UND macht `e2e/v014-p4-prepare-werkbank-
  // insel.spec.ts` rot (verlangt wörtlich alle drei KosmoPrepare-Knöpfe beim
  // ERSTEN Klick sichtbar/aktivierbar); Werkbank-Inhalt kürzen ist in
  // V015-SPEZ P04 ausdrücklich verboten. Der AUSNAHMEN-Eintrag
  // `island-austausch-pill`/`werkbank` in `tools/insel-ueberdeckungs-gate.mjs`
  // bleibt darum GEZIELT auf `popup:werkbank` verengt (nicht mehr auf
  // `fenster:werkbank`) — das ist keine Wiederholung des alten Fundes,
  // sondern eine dokumentierte, gerechnete Grenze.
  if (wurzel && !wurzel.classList.contains('isl-vertikal')) {
    const eigeneLeiste = wurzel.querySelector('.isl-leiste');
    if (eigeneLeiste) {
      const l = ruheKasten(eigeneLeiste as HTMLElement);
      if (wurzel.classList.contains('isl-rand-oben')) {
        reserviertOben = Math.max(reserviertOben, l.bottom + ISL_LEISTE_ABSTAND_PX);
      } else if (wurzel.classList.contains('isl-rand-unten')) {
        reserviertUnten = Math.max(reserviertUnten, vh - l.top + ISL_LEISTE_ABSTAND_PX);
      }
    }
  }

  // Reicht die bisherige (an `ISL_VIEWPORT_RAND_PX` gedeckelte) Höhe nicht
  // in die jetzt schmalere sichere Zone, MUSS das Fenster schrumpfen —
  // reine Verschiebung kann eine Fläche, die fast die volle Fensterhöhe
  // belegt (`.isl-fenster`s `max-height`, `island.css`), nicht gleichzeitig
  // von oben UND unten fernhalten (nachgerechnet: bei 1024×768 bräuchte das
  // PROJEKT-Fenster ohne diese Deckelung mehr Höhe, als zwischen Kopf und
  // AUSTAUSCH-Pille überhaupt frei ist). `.isl-fenster` ist E-10 AUSNAHME 1
  // — die EINE sanktionierte Scrollfläche der Insel-UI — darum ist ein
  // engerer Deckel hier kein neuer Verzicht, nur eine genauere Zahl für die
  // bereits vorhandene `overflow-y:auto`. `.isl-popup`/der Tooltip
  // referenzieren `--isl-clamp-max-height` gar nicht (E-10 O-12: Stufe 2
  // scrollt nie) — das Setzen hier ist für sie folgenlos.
  const sichereHoehe = Math.max(120, vh - reserviertOben - reserviertUnten);
  if (r.height > sichereHoehe) {
    el.style.setProperty('--isl-clamp-max-height', `${sichereHoehe}px`);
    r = ruheKasten(el);
  }

  let dy = 0;
  if (r.top < reserviertOben) dy = reserviertOben - r.top;
  else if (r.bottom > vh - reserviertUnten) dy = vh - reserviertUnten - r.bottom;

  // W2-Quergate-Fund (18.07.2026): die reine Viewport-Klammer kann das Popup
  // ÜBER die eigene Werkzeug-Leiste schieben (hohe ZEICHNEN-Insel @1024×768:
  // Clamp-Y -81px legte das Messen-Popup auf den Messen-Knopf — der zweite
  // Klick zur Stufe-3-Eskalation war abgefangen, elementFromPoint-bewiesen).
  // Darum: überdeckt das geklammerte Popup die Leiste, weicht es QUER zur
  // Insel-Orientierung aus (vertikale Leiste → seitlich, horizontale →
  // darüber/darunter), auf die Seite mit mehr Platz. Interaktion schlägt
  // Randabstand: die Ausweichung wird nur weich nachgeklammert, nie zurück
  // in die Überdeckung.
  const leiste = wurzel?.querySelector('.isl-leiste');
  if (leiste) {
    // Auch die Leiste trägt beim Öffnen eine Animation (`islIn`, scale 0.86)
    // — ihr laufender Kasten ist 14% zu klein und hätte die Ausweichung
    // ebenso falsch bemessen wie oben die Klammer.
    const l = ruheKasten(leiste as HTMLElement);
    const g = { left: r.left + dx, right: r.right + dx, top: r.top + dy, bottom: r.bottom + dy };
    const ueberdeckt = g.left < l.right && g.right > l.left && g.top < l.bottom && g.bottom > l.top;
    if (ueberdeckt) {
      if (wurzel!.classList.contains('isl-vertikal')) {
        const platzRechts = vw - ISL_VIEWPORT_RAND_PX - l.right;
        const platzLinks = l.left - ISL_VIEWPORT_RAND_PX;
        dx =
          platzRechts >= r.width || platzRechts >= platzLinks
            ? l.right + ISL_LEISTE_ABSTAND_PX - r.left
            : l.left - ISL_LEISTE_ABSTAND_PX - r.right;
      } else {
        const platzUnten = vh - ISL_VIEWPORT_RAND_PX - l.bottom;
        const platzOben = l.top - ISL_VIEWPORT_RAND_PX;
        dy =
          platzUnten >= r.height || platzUnten >= platzOben
            ? l.bottom + ISL_LEISTE_ABSTAND_PX - r.top
            : l.top - ISL_LEISTE_ABSTAND_PX - r.bottom;
      }
    }
  }

  el.style.setProperty('--isl-clamp-x', `${dx}px`);
  el.style.setProperty('--isl-clamp-y', `${dy}px`);
}

/**
 * P-VIERTER-AUSLOESER (`docs/UI-UX-2026-09-06-B116-GEGENPROBE.md`,
 * Owner-Entscheid «Springen ist besser als verdeckt», Weg 1 des
 * UI-Workers): B116 fragte die Sperrzonen-Klammer (`ermittleSperrzonenRand`
 * oben, selbst unveraendert) nur zu DREI Zeitpunkten neu ab — Oeffnen,
 * `window.resize`, eigener `ResizeObserver` (`useViewportKlammer` unten).
 * Der Befund der Gegenprobe: ruht der Zeiger einfach, waehrend eine FREMDE
 * Insel ihre Leiste erst DANACH aufklappt, feuert KEINER der drei — das
 * eigene Fenster ueberdeckt die fremde Leiste, ohne es je zu merken.
 *
 * Der Owner-Entscheid ist Weg 1: neu rechnen, sobald irgendeine Insel ihre
 * Stufe wechselt. Der Zustand (`stufe`, weiter unten `useState<IslandStufe>`)
 * existiert je Insel bereits — nur weiss heute keine andere Insel davon. Der
 * Melder hier ist genau das: eine Menge von Rueckrufen
 * (`stufenHoerer`) — kein Kontext, kein globales Fensterobjekt, kein neues
 * Paket. Jede `IslandShell`-Instanz meldet JEDEN eigenen Stufenwechsel
 * (`meldeStufenWechsel`, unten im Komponentenkoerper); jede Instanz mit einem
 * offenen Fenster/Popup/Tooltip (`useViewportKlammer`, `aktiv===true`) hoert
 * zu und klammert neu.
 *
 * **Falle 1 (kein Kreis):** die Klammer setzt `--isl-clamp-x/-y` auf das
 * EIGENE Fenster — dessen `ResizeObserver` (unten) feuert deshalb ohnehin bei
 * jeder eigenen Neurechnung. Eine eigene Stufenaenderung wuerde sich sonst
 * SELBST melden und ein zweites Mal (unnoetig, im Extremfall zyklisch) neu
 * rechnen lassen. Darum traegt jede Meldung ihre eigene Insel-Wurzel
 * (`quelle`) mit, und `useViewportKlammer` unten ueberspringt jede Meldung,
 * deren Quelle die EIGENE `.isl-root` ist — exakt dieselbe Ausschluss-Idee
 * wie `ermittleSperrzonenRand`s `eigeneWurzel.contains(...)`, nur auf der
 * Melder-Seite statt der Geometrie-Seite.
 *
 * **Falle 2 (kein Leck):** der Rueckruf wird im selben `useLayoutEffect`
 * abgemeldet, der ihn anmeldet (Aufraeumfunktion unten) — geschlossen/
 * unmontiert heisst abgemeldet, kein Zombie-Rueckruf haelt eine entfernte
 * Insel am Leben.
 *
 * **Falle 3 (keine Rechnung im Ruhezustand):** eine geschlossene Insel
 * (`stufe==='pill'`) haelt gar kein Fenster — `useViewportKlammer` wird fuer
 * sie nie mit `aktiv===true` aufgerufen, meldet sich also gar nie als
 * Hoerer an und rechnet folglich auch nichts, wenn irgendwo sonst eine Stufe
 * wechselt.
 */
type StufenMelder = (quelle: Element | null) => void;
const stufenHoerer = new Set<StufenMelder>();

function meldeStufenWechsel(quelle: Element | null): void {
  for (const hoerer of stufenHoerer) hoerer(quelle);
}

/**
 * Misst+klammert das übergebene Element sofort nach dem Mount/Stufenwechsel
 * (`useLayoutEffect` — läuft VOR dem ersten Paint, kein sichtbares
 * Nachrücken), erneut bei jeder Grössenänderung des Elements selbst
 * (`ResizeObserver`, z. B. wenn ein Stufe-3-Inhalt seinen Aufbau-Katalog
 * aufklappt), bei jeder Viewport-Grössenänderung (iPad-Drehung) — und, seit
 * P-VIERTER-AUSLOESER (Kopfkommentar oben), wenn eine FREMDE Insel ihre
 * Stufe wechselt (`stufenHoerer`). `ResizeObserver` existiert in jsdom
 * nicht — defensiv übersprungen, die Erstmessung greift trotzdem (Unit-Tests
 * bleiben unberührt).
 */
function useViewportKlammer(ref: { current: HTMLElement | null }, aktiv: boolean): void {
  useLayoutEffect(() => {
    const el = ref.current;
    if (!aktiv || !el) return;
    klammereInViewport(el);
    const aufResize = () => klammereInViewport(el);
    window.addEventListener('resize', aufResize);
    let ro: ResizeObserver | undefined;
    if (typeof ResizeObserver !== 'undefined') {
      ro = new ResizeObserver(aufResize);
      ro.observe(el);
    }
    // P-VIERTER-AUSLOESER: die eigene Insel-Wurzel wird HIER (nicht erst in
    // `klammereInViewport`) ermittelt, weil der Vergleich rein auf der
    // Melder-Seite passiert — Falle 1, s. Kopfkommentar oben.
    const eigeneWurzel = el.closest('.isl-root');
    const aufFremdeStufe: StufenMelder = (quelle) => {
      if (quelle && eigeneWurzel && eigeneWurzel.contains(quelle)) return;
      klammereInViewport(el);
    };
    stufenHoerer.add(aufFremdeStufe);
    return () => {
      window.removeEventListener('resize', aufResize);
      ro?.disconnect();
      stufenHoerer.delete(aufFremdeStufe); // Falle 2: kein Leck über Schliessen/Unmount hinweg.
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [aktiv]);
}

/* ── E-10 · die Leiste, die nicht scrollt, sondern in Spalten wächst ───────
 * (`docs/design/GESTALTUNGS-ENTSCHEIDE-2026-08-10.md` E-10, Owner-Befunde O-12 +
 * O-3 vom 11.08.2026.)
 *
 * Bis zum Owner-Befund vom 11.08.2026 bekam die vertikale Leiste
 * `max-height: calc(100dvh - 208px)`
 * + `overflow-y: auto` (island.css) — bei 23 ZEICHNEN-Werkzeugen war das
 * eine Scrollfläche auf JEDEM üblichen Fenster, und sobald man darin
 * scrollte, verschwand ihr eigener Kopf («ZEICHNEN») nach oben aus dem Bild:
 * exakt Owner-Befund O-3. E-10 Antwort (c): die Leiste wächst quer zur
 * eigenen Achse. `leistenZeilen()` sagt, wie viele Werkzeuge übereinander
 * Platz haben; das CSS-Grid (`--isl-zeilen`) bricht den Rest in die nächste
 * Spalte um.
 *
 * Die drei Konstanten sind die CSS-Masse dieser Datei-Nachbarn, nicht
 * geraten:
 *  · 56px  = die REAL gerenderte Höhe eines `.isl-werkzeug` (Icon 16px + 2px
 *            `gap` + Beschriftungszeile + `padding` oben/unten), NICHT dessen
 *            `min-height` (E-8 A Trefferfläche, 44px — das ist eine
 *            CSS-UNTERGRENZE für die Trefferfläche, kein Höhenversprechen:
 *            Icon+Beschriftung SPRENGEN sie bereits im Ruhezustand). Live in
 *            einem echten Chromium nachgemessen (Playwright, `w5-klickfalle-
 *            messung.mjs`): 48.8–54.8px, je nachdem, welches Nachbarwerkzeug
 *            in derselben Grid-Zeile (`grid-auto-flow:column`) die Zeile
 *            mitstreckt — 56 rundet grosszügig nach oben, statt die knappste
 *            beobachtete Zeile als Obergrenze zu nehmen (W-4 fügt mit
 *            «Schnitt» ein 24. Werkzeug hinzu, das diese Paarungen
 *            verschiebt — die Marge muss das VOR der eigenen Messung
 *            überleben, nicht nur den heutigen Bestand).
 *  ·  2px  = `.isl-leiste-werkzeuge`s `gap: var(--k-s1)` (aura.css: 2px,
 *            unverändert korrekt — nur die Zeilenhöhe war falsch, nicht der
 *            Abstand).
 *  · 56px  = Kopfzeile + Leisten-`gap` (`--k-s2`, 4px) + Polster oben/unten
 *            (`--k-s3`, 2 × 8px) + Rand (2 × 1px), aufgerundet.
 *            **B140 (11.09.2026) hat diesen Wert von 36 auf 56 gehoben, und
 *            zwar NOTWENDIG, nicht vorsorglich:** der Kopf ist seit B140 der
 *            Einklapp-Schalter und damit `min-height: 32px` statt der 12px
 *            der reinen Textzeile (9px × 1.3). 32 + 4 + 16 + 2 = 54, auf 56
 *            aufgerundet — dieselbe Rundungsregel wie vorher (lieber eine
 *            Zeile zu wenig als eine zu viel). Wer den Wert bei 36 liesse,
 *            bekaeme eine 20px höhere Leiste, die die Formel nicht kennt:
 *            bei mittiger Verankerung sind das 10px weniger Luft am oberen
 *            Rand, und die garantierte Distanz zur Geschoss-Pille faellt von
 *            120px auf 110px — genau der W-5-Befund unten, wieder eingebaut.
 *            Gegengerechnet, dass die Erhöhung NICHTS verbreitert: bei
 *            720/768/820/900/1080 ergeben 36 und 56 dieselbe Spaltenzahl
 *            (4/3/3/3/2). Ein Kopf von 44px (die Groesse der Fenster-Chrome)
 *            haette bei 768 aus drei Spalten vier gemacht.
 *  · 120px = `ISL_GESCHOSS_PILLE_UNTERKANTE_PX` (unten) — die Unterkante der
 *            Geschoss-Pille (`.isl-geschoss-pille` `top:66px` +
 *            `.isl-geschoss-pille-label` `min-height:54px`, `island.css`).
 *  · 240px = `ISL_LEISTE_RESERVE_PX` = 2 × 120px, NICHT 120px selbst. Der
 *            alte Wert (208) hatte genau diesen Faktor vergessen: die Leiste
 *            ist NICHT am oberen Rand verankert, sondern vertikal MITTIG
 *            (`.isl-rand-links`, `top:50%; transform:translateY(-50%)`).
 *            Bei einer zentrierten Box liegt ihre schlechteste (kleinste)
 *            Distanz zur oberen Kante bei `(fensterHöhe − Leistenhöhe) / 2`
 *            — jedes Pixel, um das die Leiste niedriger wird, gewinnt am
 *            oberen Rand nur ein HALBES Pixel Luft (das andere halbe Pixel
 *            verpufft unten, wo nichts im Weg steht). Um die Distanz ≥ 120px
 *            zu garantieren, muss die Leistenhöhe also ≤ fensterHöhe − 240px
 *            bleiben, nicht ≤ fensterHöhe − 120px.
 *
 * **W-5-Befund (Fable-Bericht 18.08.2026, `docs/BERICHT-FABLE-UI-2026-08-18.md`):**
 * EIN gemeinsamer Fehler in genau dieser Formel erzeugte zwei Symptome
 * unterschiedlicher Schwere — «Klickfalle» bei 1400×900 (die Leisten-FLÄCHE
 * überlappte die Pille knapp, das oberste Werkzeug selbst blieb knapp
 * frei), «Vollüberlappung» bei 1180×820 (die Pille lag über dem obersten
 * Werkzeug selbst, `elementFromPoint` traf `geschoss-pille-root` statt
 * `island-werkzeug-auswahl`) — UND ein zweiter, bis hierhin unbenannter
 * Anteil desselben Fehlers: die 44px-Zeilenhöhe war selbst schon zu klein
 * (der wirkliche Grund, warum schon `leistenZeilen()`s eigene Rechnung zu
 * WENIGE Spalten wählte, bevor der Zentrierungs-Faktor überhaupt zum Tragen
 * kam). Beide Anteile leben in derselben Formel — behoben an einer Stelle,
 * nicht an den zwei Fenstergrössen einzeln.
 *
 * Bewusst eine reine Funktion über `window.innerHeight` statt einer
 * `getBoundingClientRect`-Messung: sie ist ohne Layout-Engine prüfbar (jsdom
 * misst keine Höhe, s. `test/insel-scroll-e10.test.tsx`) und kann nicht in eine
 * Mess-/Setz-Rückkopplung geraten wie eine Beobachtung der eigenen Grösse.
 */
export const ISL_GESCHOSS_PILLE_UNTERKANTE_PX = 120;
export const ISL_WERKZEUG_HOEHE_PX = 56;
export const ISL_WERKZEUG_ABSTAND_PX = 2;
export const ISL_LEISTE_RAHMEN_PX = 56;
export const ISL_LEISTE_RESERVE_PX = 2 * ISL_GESCHOSS_PILLE_UNTERKANTE_PX;

/**
 * Wie viele Werkzeuge stehen bei dieser Fensterhöhe übereinander, damit
 * `anzahl` Werkzeuge OHNE Scrollen in möglichst wenige, gleich hohe Spalten
 * passen? Ergebnis ≥ 1 und ≤ `anzahl` (eine Spalte ist das Bestandsverhalten
 * hoher Fenster — dort ändert E-10 kein Pixel).
 */
export function leistenZeilen(anzahl: number, fensterHoehe: number): number {
  if (anzahl <= 1) return Math.max(1, anzahl);
  const nutzbar = fensterHoehe - ISL_LEISTE_RESERVE_PX - ISL_LEISTE_RAHMEN_PX;
  const proSpalte = Math.floor(nutzbar / (ISL_WERKZEUG_HOEHE_PX + ISL_WERKZEUG_ABSTAND_PX));
  if (proSpalte >= anzahl) return anzahl;
  // Spalten erst zählen, dann gleichmässig füllen: 23 Werkzeuge bei 11
  // möglichen Zeilen ergeben 3 Spalten à 8 statt 11/11/1 — gleich hohe
  // Spalten stehen ruhiger und sind schneller zu überfliegen.
  const spalten = Math.max(1, Math.ceil(anzahl / Math.max(1, proSpalte)));
  return Math.ceil(anzahl / spalten);
}

/**
 * Hält `--isl-zeilen` auf der Leiste aktuell — beim Mount und bei jeder
 * Fenster-Grössenänderung (iPad-Drehung, geteilter Bildschirm). Wie
 * `useViewportKlammer` ein `useLayoutEffect`: die Spaltenzahl steht vor dem
 * ersten Paint, es gibt kein sichtbares Umspringen.
 */
function useLeistenSpalten(ref: { current: HTMLElement | null }, anzahl: number, aktiv: boolean): void {
  useLayoutEffect(() => {
    const el = ref.current;
    if (!aktiv || !el) return;
    const setzen = () => {
      const hoehe = typeof window === 'undefined' ? 0 : window.innerHeight;
      el.style.setProperty('--isl-zeilen', String(leistenZeilen(anzahl, hoehe)));
    };
    setzen();
    if (typeof window === 'undefined') return;
    window.addEventListener('resize', setzen);
    return () => window.removeEventListener('resize', setzen);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [aktiv, anzahl]);
}

/**
 * §10.2 (`docs/V083-SPEZ.md`, `docs/ISLAND-UI-SPEZ.md` §8 Punkt 1 bleibt
 * OWNER-OFFEN): Zwei-Finger-Doppeltipp auf dem Viewport löst `history.undo()`
 * aus — NUR wenn `kosmo.touch-undo-geste` aktiv ist (Default aus,
 * `state/touch-undo.ts`, Schalter in `Einstellungen.tsx` Sektion «Bewegung &
 * Klang»). Rein additiv: `{ passive: true }`, nie `preventDefault`/
 * `stopPropagation` — kein bestehender Touch-Handler (Pinch/Pan/Zeichnen in
 * `Viewport3D.tsx`/`PlanView.tsx`) wird berührt oder unterdrückt, dieser
 * Listener liest nur zusätzlich mit. Ein Bewegungs- und Zeit-Schwellwert
 * unterscheidet den Tap von einem Pinch/Pan-Zoom mit zwei Fingern (dieselben
 * zwei Finger, die sonst die Kamera steuern).
 */
const ZWEI_FINGER_TAP_MAX_MS = 300;
const ZWEI_FINGER_DOPPELTIPP_MS = 400;
const ZWEI_FINGER_BEWEGUNG_PX = 24;

interface ZweiFingerPunkt {
  x: number;
  y: number;
  zeit: number;
}

function useZweiFingerUndoGeste(): void {
  const start = useRef<Map<number, ZweiFingerPunkt> | null>(null);
  const letzterTap = useRef(0);

  useEffect(() => {
    if (typeof window === 'undefined') return;

    function aufTouchStart(e: TouchEvent): void {
      if (e.touches.length !== 2) {
        start.current = null;
        return;
      }
      const punkte = new Map<number, ZweiFingerPunkt>();
      const zeit = performance.now();
      for (const t of Array.from(e.touches)) punkte.set(t.identifier, { x: t.clientX, y: t.clientY, zeit });
      start.current = punkte;
    }

    function aufTouchEnd(e: TouchEvent): void {
      const startPunkte = start.current;
      // Beide Finger müssen zusammen losgelassen werden (letzter Finger oben)
      // — ein noch aufliegender Finger ist kein sauberer Zwei-Finger-Tap.
      if (!startPunkte || startPunkte.size !== 2 || e.touches.length !== 0) {
        start.current = null;
        return;
      }
      start.current = null;

      let treffer = 0;
      let ungueltig = false;
      for (const t of Array.from(e.changedTouches)) {
        const s = startPunkte.get(t.identifier);
        if (!s) continue;
        treffer += 1;
        if (Math.hypot(t.clientX - s.x, t.clientY - s.y) > ZWEI_FINGER_BEWEGUNG_PX) ungueltig = true;
        if (performance.now() - s.zeit > ZWEI_FINGER_TAP_MAX_MS) ungueltig = true;
      }
      if (treffer < 2 || ungueltig) return;

      const jetzt = performance.now();
      if (jetzt - letzterTap.current < ZWEI_FINGER_DOPPELTIPP_MS) {
        letzterTap.current = 0;
        if (touchUndoGesteAktiv()) useProject.getState().undo();
      } else {
        letzterTap.current = jetzt;
      }
    }

    window.addEventListener('touchstart', aufTouchStart, { passive: true });
    window.addEventListener('touchend', aufTouchEnd, { passive: true });
    return () => {
      window.removeEventListener('touchstart', aufTouchStart);
      window.removeEventListener('touchend', aufTouchEnd);
    };
  }, []);
}

/**
 * P1 (v0.9.36, Owner-Entscheid 18.08.2026, ROADMAP 961 — Taste «T» Lesart
 * (a) «Einstellungen des aktiven Werkzeugs aufklappen»): der fehlende Weg,
 * von AUSSEN Stufe 2 (Popup) zu öffnen — bis hierhin war `stufe`/
 * `aktivesWerkzeugId` reiner interner `useState`-Automat ohne Prop (s.
 * ehemaliger Beleg in `kurztasten.ts`s Kopfkommentar §T, jetzt aktualisiert).
 *
 * **Prop vs. Imperativ-Handle:** ein Imperativ-Handle statt eines simplen
 * Props (`oeffneWerkzeugId?: string`), weil «T auf demselben Werkzeug
 * zweimal hintereinander» erneut öffnen soll, selbst wenn sich der Wert gar
 * nicht ändert (ein reiner Prop bräuchte einen künstlichen Zähler daneben,
 * um jeden Tastendruck als eigenes Ereignis zu erkennen — ein Imperativ-
 * Aufruf IST das Ereignis). `DesignWorkspace.tsx` hat ohnehin schon einen
 * `keydown`-Handler ausserhalb von React (kein deklarativer Datenfluss),
 * ein `ref.current.oeffnePopupFuerWerkzeug(id)`-Aufruf von dort passt zu
 * diesem bestehenden imperativen Stil, statt eine neue Prop-Change-Erkennung
 * einzuführen. `IslandBuehne` (unten) reicht das Handle an die vier Inseln
 * durch und probiert sie der Reihe nach — nur EINE davon führt das gerade
 * aktive Zeichenwerkzeug, alle anderen liefern `false` (kein Fehler, kein
 * Owner-sichtbares Verhalten).
 */
export interface IslandShellHandle {
  /**
   * Öffnet Stufe 2 (Popup) für `werkzeugId`, sofern DIESE Insel das
   * Werkzeug führt (`sichtbareWerkzeuge`) UND es ein Popup hat
   * (`hatPopup===true`) — sonst No-Op. Liefert `true` bei Erfolg, `false`
   * sonst (falsches Werkzeug für diese Insel, unbekanntes Werkzeug, oder
   * ein Werkzeug ohne Popup wie Achsen/Manuell) — der Rückgabewert ist die
   * einzige Möglichkeit für `IslandBuehne`, die richtige der vier Inseln zu
   * finden, ohne den Werkzeug-Katalog selbst zu kennen.
   */
  oeffnePopupFuerWerkzeug(werkzeugId: string): boolean;
  /**
   * B144 (12.09.2026) — dasselbe eine Stufe weiter: Stufe 3 (Fenster).
   *
   * **Gebraucht, nicht vorsorglich gebaut.** Die Leerzustaende von KosmoVis
   * und KosmoPublish erreichen ihren ersten Schritt in Stufe 2 (dort steht
   * «+ Graph erstellen» bzw. «+ Blatt»). Bei KosmoSpez steht der erste
   * Schritt («erfassen») in Stufe 3 — ein Aufruf von
   * `oeffnePopupFuerWerkzeug` landete gemessen im Popup mit Datum und
   * Sonnenzeiten, und der Knopf, der die Leere beendet, blieb eine Stufe
   * weiter. Dieselbe Bedingung wie oben (`hatPopup`), nur die Zielstufe
   * unterscheidet sich.
   */
  oeffneFensterFuerWerkzeug(werkzeugId: string): boolean;
}

export interface IslandShellProps {
  /**
   * PC0 v0.8.4: `string` statt der design-`IslandId`-Union. OHNE `konfig`
   * wird die Id gegen die design-Defaults (`DESIGN_INSELN`) aufgelöst —
   * jeder Bestands-Aufrufer (`<IslandShell island="zeichnen"/>`, Unit-Tests,
   * IslandBuehne) verhält sich byte-gleich weiter.
   */
  island: string;
  /** Stations-Konfig (V084-SPEZ E1) — andere Stationen übergeben sie explizit. */
  konfig?: InselKonfig;
  /** Inhalts-Registry der Station — Default: die design-Registry. */
  registry?: InhaltsRegistry;
  /**
   * PD2 (`docs/ISLAND-UI-SPEZ.md` §7 PD2-Zeile, Bullet 1 «Klick... aktiviert
   * das ECHTE Werkzeug»): optionaler Aufruf bei JEDER Erst-Aktivierung eines
   * Werkzeugs (einmal pro Übergang zu einem neuen `w.id`, s. `aufWerkzeugKlick`
   * unten) — der eigentliche Command-/Store-Aufruf lebt beim Aufrufer
   * (`DesignWorkspace.tsx`s `aktiviereIslandWerkzeug()`), NICHT hier (dieser
   * Automat bleibt reiner Präsentationszustand, s. Datei-Kopfkommentar).
   * Optional, damit der PD1-Unit-Test (`island-shell.test.tsx`, rendert
   * `IslandShell` STANDALONE ohne dieses Prop) unverändert grün bleibt.
   */
  onWerkzeugAktion?: (werkzeug: IslandWerkzeug) => void;
  /**
   * P-WERKZEUGLEISTE (v0.9.35, O-T5/O-T6): die STORE-Wahrheit eines
   * Werkzeugs («ist Achsen wirklich an?») — geliefert von der Station, die
   * sie kennt. `true`/`false` steuern `aria-pressed` + die sichtbare
   * `isl-werkzeug--an`-Klasse; `undefined` heisst «dieses Werkzeug hat
   * keinen An/Aus-Zustand» und faellt auf das Bestandsverhalten
   * («zuletzt geklickt») zurueck. Ohne das Prop ist die Shell byte-gleich
   * zu vorher — sie ist stationsuebergreifend geteilt.
   */
  istWerkzeugAktiv?: (werkzeugId: string) => boolean | undefined;
}

/** Eine einzelne Island — Zustandsmaschine + Rendering für Pill/Leiste/Popup/Fenster. */
export const IslandShell = forwardRef<IslandShellHandle, IslandShellProps>(function IslandShell(
  { island, konfig, registry, onWerkzeugAktion, istWerkzeugAktiv }: IslandShellProps,
  handleRef,
) {
  const inselKonfig = konfig ?? designInselKonfig(island as IslandId);
  const inhalte = registry ?? designInhaltsRegistry;
  const werkzeuge = inselKonfig.werkzeuge;
  const orientierung = inselKonfig.orientierung;
  const reduziert = useReduzierteBewegung();

  /**
   * V0812-SPEZ E-M (P-M) — Konsum von `PHASEN_MATRIX`/`werkzeugInPhaseSichtbar`:
   * harte Ausblendung ausserhalb der aktiven `doc.settings.siaPhase` (kein
   * Dimmen). `IslandShell` ist stationsübergreifend geteilte Infrastruktur
   * (Kopfkommentar oben) — die 19er-Register-Domäne kennt heute nur die 8
   * Stations-Ids + die 11 ZEICHNEN-Ids; `werkzeugInPhaseSichtbar()` ist für
   * jede andere Id (ANSICHT/PROJEKT/AUSTAUSCH sowie vis-/publish-/prepare-
   * Inseln) defensiv `true` — diese Zeile beschneidet darum NUR die
   * ZEICHNEN-Insel-Leiste sichtbar, alle übrigen Inseln bleiben byte-gleich.
   */
  const siaPhase = useProject((s) => s.doc.settings.siaPhase);
  const sichtbareWerkzeuge = werkzeuge.filter((w) => werkzeugInPhaseSichtbar(w.id, siaPhase));

  // P-TRENNUNG (v0.9.35): eine Insel mit `fixeStufe` startet offen und
  // faellt nie darunter (s. `aufPointerLeave`) — sonst wie bisher 'pill'.
  const [stufe, setStufe] = useState<IslandStufe>(inselKonfig.fixeStufe ?? 'pill');
  /**
   * B140 (11.09.2026, Owner-Entscheid «Leiste einklappbar») — die Leiste ist
   * weggeklappt, WaEHREND ihr Fenster offen bleibt.
   *
   * ## Warum es das braucht
   *
   * Leiste und Werkzeugfenster sind an jeder Fenstergroesse gleich gross. Ihr
   * Anteil an der Stationsflaeche waechst darum, je kleiner der Bildschirm
   * ist: beim Werkzeug «Messen» gemessen **28,05 Prozent von 1024x768**,
   * allein die ZEICHNEN-Leiste 192x470 = 90 179 Bildpunkte. Beim Zeichnen ist
   * das gerade die Seite, auf die man schaut
   * (`docs/UI-UX-2026-09-10-B132-DAS-KAESTCHEN-UND-SEINE-BESCHRIFTUNG.md` §5).
   *
   * Die Leiste war schon vorher wegklappbar — aber nur, indem man das
   * Werkzeug schloss: `aufPointerLeave` nimmt das Fenster ausdruecklich aus,
   * weil es halb getippte Eingaben traegt. Wer Platz wollte, musste also
   * seine Arbeit schliessen. Diese Stufe trennt die beiden.
   *
   * ## Warum der Schalter am KOPF DER LEISTE sitzt und nicht am Fenster
   *
   * Der erste Bau setzte ihn in die Ecke des Werkzeugfensters, neben
   * `.isl-schliessen`. **Die Messung hat ihn verworfen.** Geprueft wurden alle
   * 44 Werkzeugfenster der vier design-Inseln, je mit
   * `document.elementFromPoint` unter dem durchlaessig geschalteten Knopf:
   *
   * ```
   * oben rechts, zweiter Platz : 1 von 44 Fenstern mit einem Bedienelement darunter
   * unten rechts               : 3 von 44
   * unten links                : 4 von 44
   * ```
   *
   * Der eine Fall ist `draw-panel-koerper-umschalten` im PROJEKT-Fenster:
   * 25 x 31 Bildpunkte eines echten Knopfes lagen unter dem neuen. Und die
   * Ursache ist strukturell, nicht zufaellig — **im Fenster reserviert
   * niemand die Chrome-Ecke**: gemessen hat `.isl-fenster` rundum 16px
   * Polster, und der bestehende Schliessen-Knopf ragt schon heute 32px in den
   * Inhaltskasten; dass dort nichts liegt, ist Glueck, keine Zusage. Ein
   * zweiter Knopf verlaengert dieses Glueck um 44px, und bei einem von 44
   * Fenstern reicht es nicht mehr. Genau die Klasse Fund, die B135/B139
   * gerade beseitigt haben.
   *
   * Der Kopf der Leiste hat dieses Problem nicht: er ist die volle Breite der
   * Leiste und traegt nichts als seine Beschriftung.
   *
   * **Die Leiste waechst dadurch 20px in der Hoehe, und das musste gerechnet
   * werden:** `leistenZeilen()` (oben) teilt die Werkzeuge in Spalten, und ein
   * hoeherer Kopf bedeutet weniger Zeilen je Spalte — also MEHR Spalten, also
   * eine BREITERE Leiste. Nachgerechnet mit `ISL_LEISTE_RAHMEN_PX` 36 gegen
   * 56, bei den vier gefahrenen Fensterhoehen: 720/768/820/900 ergeben in
   * beiden Faellen dieselbe Spaltenzahl. Ein Kopf von 44px (die Groesse der
   * Fenster-Chrome) haette bei 768 aus drei Spalten vier gemacht und die
   * Leiste um rund 64px verbreitert — der Schalter haette die Flaeche
   * vergroessert, die er wegklappen soll.
   *
   * ## Zurueck kommt die Leiste ueber die Pille
   *
   * Eingeklappt ist der Schalter selbst mit verschwunden; der Weg zurueck ist
   * die Pille der Insel — dieselbe, die sie auch sonst oeffnet, an derselben
   * Stelle wie immer. Ein zweiter, schwebender Ausklapp-Knopf waere eine
   * zweite Flaeche auf der Buehne, also das Gegenteil dieses Pakets.
   *
   * ## Warum kein klemmender Zustand moeglich ist
   *
   * Dieser Schalter ist der EINZIGE Weg hinein, aber nicht der einzige Weg
   * hinaus: das Fenster schliesst ueber den eigenen Knopf, ueber Esc, ueber
   * einen Aussenklick und ueber den Ruhe-Timer der darunterliegenden Stufen.
   * Statt an jeder dieser Stellen einzeln zurueckzusetzen, setzt ein Effekt
   * weiter unten das Merkmal zurueck, sobald die Stufe `fenster` verlassen
   * wird — eine Stelle statt fuenf, und keine, die beim naechsten neuen
   * Schliessweg vergessen werden kann.
   */
  const [leisteEingeklappt, setLeisteEingeklappt] = useState(false);
  /** Die Leiste ist wirklich weg (und nicht bloss das Merkmal gesetzt). */
  const leisteVerborgen = leisteEingeklappt && (stufe === 'popup' || stufe === 'fenster');
  const [aktivesWerkzeugId, setAktivesWerkzeugId] = useState<string | null>(null);
  const [toast, setToast] = useState<string | null>(null);

  // P1 (v0.9.36, Owner-Entscheid 18.08.2026, ROADMAP 961, s. `IslandShellHandle`-
  // Kommentar oben): der einzige Schreibzugriff von AUSSEN auf den sonst rein
  // internen Stufen-Automaten — dieselben zwei Setter, die `aufWerkzeugKlick`
  // unten bei einem echten Klick benutzt, nur ohne dessen Toast-/Touch-Badge-
  // Nebeneffekte (ein Tastendruck ist kein Zeigergerät). `sichtbareWerkzeuge`
  // statt `werkzeuge` — ein per SIA-Phase ausgeblendetes Werkzeug lässt sich
  // per T ebenso wenig öffnen wie per Klick.
  useImperativeHandle(
    handleRef,
    () => ({
      oeffnePopupFuerWerkzeug(werkzeugId: string): boolean {
        const ziel = sichtbareWerkzeuge.find((w) => w.id === werkzeugId);
        if (!ziel || !ziel.hatPopup) return false;
        setAktivesWerkzeugId(ziel.id);
        setStufe('popup');
        return true;
      },
      oeffneFensterFuerWerkzeug(werkzeugId: string): boolean {
        const ziel = sichtbareWerkzeuge.find((w) => w.id === werkzeugId);
        if (!ziel || !ziel.hatPopup) return false;
        setAktivesWerkzeugId(ziel.id);
        setStufe('fenster');
        return true;
      },
    }),
    [sichtbareWerkzeuge],
  );
  /** PB2 (Bauauftrag Punkt 2): welches Werkzeug gerade seinen Lang-Hover-
   *  Tooltip zeigt (`null` = keiner) — unabhängig von `stufe`. */
  const [tooltipWerkzeugId, setTooltipWerkzeugId] = useState<string | null>(null);
  /** D-8 (E-8 C): 1.5s-Badge «Label bei Aktivierung» für Touch/Pen —
   *  `austritt` schaltet auf die `--k-motion-fast`-Ausblendphase, bevor der
   *  Timer das Element ganz entfernt (s. Konstanten-Kommentar oben). */
  const [touchBadge, setTouchBadge] = useState<{ text: string; austritt: boolean } | null>(null);

  const rueckklappTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const toastTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const tooltipTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const badgeTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const badgeAustrittTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  /** D-8 (E-8 B): Zeigertyp der letzten Pointer-Geste auf einem Werkzeugknopf.
   *  `onClick` trägt in jsdom/älteren Engines keinen `pointerType` — darum
   *  merkt ihn das `pointerdown` davor (zentraler Helfer `istTouchArtig`,
   *  kosmo-ui). Nach jedem Klick zurückgesetzt, damit eine spätere
   *  Tastatur-Aktivierung (Klick OHNE pointerdown) als Maus-/Tastaturweg
   *  zählt und kein abgestandenes «Touch» erbt. */
  const zeigerWarTouch = useRef(false);

  // §10.1 Viewport-Klammer (s. `useViewportKlammer`-Kopfkommentar oben) — je
  // ein Ref für Popup/Fenster, nur AKTIV, solange die jeweilige Stufe wirklich
  // gerendert ist (sonst zeigt der Ref ins Leere).
  const popupRef = useRef<HTMLDivElement | null>(null);
  const fensterRef = useRef<HTMLDivElement | null>(null);
  useViewportKlammer(popupRef, stufe === 'popup');
  useViewportKlammer(fensterRef, stufe === 'fenster');
  /** PB2 (Bauauftrag Punkt 2): derselbe Klammer-Mechanismus für den
   *  Werkzeug-Tooltip — «nie abgeschnitten», wiederverwendet statt neu
   *  erfunden. */
  const tooltipRef = useRef<HTMLDivElement | null>(null);
  useViewportKlammer(tooltipRef, tooltipWerkzeugId !== null);

  // PB2 (Bauauftrag Punkt 4, E3): der Insel-Wurzelknoten ist der `ref` für
  // BEIDE `useOverlaySchliessen`-Aufrufe unten (Popup/Fenster-Schliessen +
  // Tooltip-Esc) — dieselbe Empfehlung wie `overlay-schliessen.ts`s
  // Rollout-Kommentar («ref = der Insel-Wurzelknoten»).
  const wurzelRef = useRef<HTMLDivElement | null>(null);

  // P-VIERTER-AUSLOESER (s. Kopfkommentar bei `useViewportKlammer` oben):
  // JEDER eigene Stufenwechsel wird gemeldet — `useLayoutEffect` statt
  // `useEffect`, damit die Meldung noch VOR dem Paint bei jedem Hoerer mit
  // offenem Fenster ankommt (kein sichtbares Nachrücken). Die eigene
  // Insel-Wurzel geht als `quelle` mit, damit Hoerer die eigene Meldung
  // erkennen und überspringen können (Falle 1). Kein Aufräumen nötig — diese
  // Funktion MELDET nur, sie meldet sich nirgends AN.
  useLayoutEffect(() => {
    meldeStufenWechsel(wurzelRef.current);
  }, [stufe]);

  // B140, der Riegel gegen den klemmenden Zustand (s. `leisteEingeklappt`
  // oben): wer die Stufe `fenster` verlaesst — egal auf welchem der fuenf
  // Wege — bekommt seine Leiste zurueck. Ohne diese Zeile waere die Insel
  // nach einem eingeklappten, dann geschlossenen Fenster eine Pille, die auf
  // Hover nichts mehr oeffnet.
  useEffect(() => {
    if (stufe !== 'popup' && stufe !== 'fenster') setLeisteEingeklappt(false);
  }, [stufe]);

  // E-10 (s. `leistenZeilen`-Kommentar oben): die Werkzeug-Fläche der Leiste
  // bekommt ihre Zeilenzahl, sobald sie gerendert ist (`stufe !== 'pill'`).
  // Nur vertikale Inseln rechnen — die horizontalen brechen per `flex-wrap`
  // um (island.css), dort gibt es nichts zu zählen.
  const werkzeugeRef = useRef<HTMLDivElement | null>(null);
  // B140: `!leisteVerborgen` — eine eingeklappte Leiste hat kein Element,
  // ihre Spaltenzahl zu rechnen waere eine Messung am leeren Ref.
  useLeistenSpalten(
    werkzeugeRef,
    sichtbareWerkzeuge.length,
    orientierung === 'vertikal' && stufe !== 'pill' && !leisteVerborgen,
  );

  // Timer beim Unmount räumen — kein Leck über Test-/Panel-Wechsel hinweg.
  useEffect(
    () => () => {
      if (rueckklappTimer.current) clearTimeout(rueckklappTimer.current);
      if (toastTimer.current) clearTimeout(toastTimer.current);
      if (tooltipTimer.current) clearTimeout(tooltipTimer.current);
      if (badgeTimer.current) clearTimeout(badgeTimer.current);
      if (badgeAustrittTimer.current) clearTimeout(badgeAustrittTimer.current);
    },
    [],
  );

  function raeumeRueckklappTimer(): void {
    if (rueckklappTimer.current) {
      clearTimeout(rueckklappTimer.current);
      rueckklappTimer.current = null;
    }
  }

  /** Hover/Tap öffnet die Leiste (§4.1 Stufe 1, §4.2 iPad-Regel: erster Tap = Hover). */
  function oeffneLeiste(): void {
    raeumeRueckklappTimer();
    // B140: die Pille ist der zweite Weg zurueck — wer sie anklickt, will die
    // Leiste sehen, auch wenn ein Fenster offen steht (dann bleibt die Stufe
    // `fenster` und nur das Merkmal faellt).
    setLeisteEingeklappt(false);
    setStufe((s) => (s === 'pill' ? 'leiste' : s));
  }

  /**
   * B140 — die Leiste weglegen, ohne das Werkzeug anzufassen.
   *
   * Steht gar kein Werkzeug offen, ist das ein schlichtes Zuklappen auf die
   * Pille: das Merkmal zu setzen waere dort wirkungslos (es gilt nur in
   * Popup/Fenster) und die Leiste blieb stehen — ein Knopf, der nichts tut.
   */
  function schalteLeiste(): void {
    raeumeRueckklappTimer();
    if (stufe === 'popup' || stufe === 'fenster') {
      setLeisteEingeklappt(true);
      return;
    }
    setStufe(inselKonfig.fixeStufe ?? 'pill');
  }

  /** Pointer betritt die Insel wieder — der Rückklapp-Timer wird storniert. */
  function aufPointerEnter(): void {
    raeumeRueckklappTimer();
    if (stufe === 'pill') setStufe('leiste');
  }

  /**
   * Pointer verlässt die Insel — die Stufe entscheidet, wie lange sie noch
   * steht (`insel-ruhe.ts`).
   *
   * P-RUHE (v0.9.33, Owner-Entscheid 12.08.: «grundsätzlich sollte sie
   * verschwinden nach einer zeit»): bis hierher hielt ein offenes Popup
   * die Insel unbegrenzt offen — genau daraus entstand B43 §3, zwei
   * Inseln gleichzeitig offen über der Bühne. Jetzt räumt sich auch das
   * Popup weg, mit deutlich mehr Luft als die Leiste, weil es Inhalt zum
   * Lesen trägt.
   *
   * **Das Fenster bleibt ausgenommen** — es trägt halb getippte
   * Kommentare, gesetzte Filter, einen Profil-Manager. Etwas unter den
   * Händen des Architekten zu schliessen wäre schlimmer als ein liegen
   * gebliebenes Fenster.
   *
   * Die Zeit läuft erst NACH dem Verlassen, und jede Rückkehr stellt sie
   * zurück (`raeumeRueckklappTimer` in `aufPointerEnter`) — ein Timer, der
   * beim Lesen mitläuft, wäre ein Ärgernis statt einer Hilfe.
   */
  function aufPointerLeave(): void {
    raeumeRueckklappTimer();
    // P-TRENNUNG: eine fixe Insel steht auf ihrer Stufe — nichts zu klappen;
    // ein offenes Popup klappt auf die FIXE Stufe zurueck statt zur Pille.
    if (stufe === inselKonfig.fixeStufe) return;
    const verzoegerung = ruheVerzoegerung(stufe);
    if (verzoegerung === null) return;
    // P-EINGABE (O-T2): welche Stufe hier tatsaechlich zuklappt, steht schon
    // JETZT fest (Closure) — die Selektor-Wahl unten braucht keinen zweiten
    // Blick auf `stufe` nach Ablauf des Timers.
    const schliessendeStufe = stufe;
    rueckklappTimer.current = setTimeout(() => {
      // Echo GREIFEN, waehrend das echte Element noch im DOM steht — danach
      // unveraendert derselbe synchrone Wechsel wie bisher (Kopfkommentar
      // `spieleSchliessEcho`).
      const selektor = schliessendeStufe === 'popup' ? '.isl-popup' : '.isl-leiste';
      spieleSchliessEcho(wurzelRef.current?.querySelector<HTMLElement>(selektor) ?? null);
      setStufe(inselKonfig.fixeStufe ?? 'pill');
      setAktivesWerkzeugId(null);
    }, verzoegerung);
  }

  function raeumeBadgeTimer(): void {
    if (badgeTimer.current) {
      clearTimeout(badgeTimer.current);
      badgeTimer.current = null;
    }
    if (badgeAustrittTimer.current) {
      clearTimeout(badgeAustrittTimer.current);
      badgeAustrittTimer.current = null;
    }
  }

  function zeigeToast(werkzeugName: string): void {
    if (toastTimer.current) clearTimeout(toastTimer.current);
    // D-8: Toast und Touch-Badge teilen die Ankerposition unter der Insel —
    // nie beide gleichzeitig (das jüngere Schild gewinnt).
    raeumeBadgeTimer();
    setTouchBadge(null);
    setToast(`${werkzeugName.toUpperCase()} AKTIV`);
    toastTimer.current = setTimeout(() => setToast(null), TOAST_MS);
  }

  /** D-8 (E-8 C): zeigt das Werkzeug-Label 1.5s als Badge an der Insel —
   *  dieselbe Wortform wie der Toast («NAME AKTIV»), EIN Muster, zwei
   *  Auslösewege. Nach `TOUCH_BADGE_MS` folgt die kurze Austrittsphase
   *  (`--k-motion-fast`), dann räumt der zweite Timer das Element weg. */
  function zeigeTouchBadge(werkzeugName: string): void {
    if (toastTimer.current) clearTimeout(toastTimer.current);
    setToast(null);
    raeumeBadgeTimer();
    setTouchBadge({ text: `${werkzeugName.toUpperCase()} AKTIV`, austritt: false });
    badgeTimer.current = setTimeout(() => {
      setTouchBadge((b) => (b ? { ...b, austritt: true } : b));
      badgeAustrittTimer.current = setTimeout(() => setTouchBadge(null), TOUCH_BADGE_AUSTRITT_MS);
    }, TOUCH_BADGE_MS);
  }

  /**
   * Klick auf ein Werkzeug in der Leiste (§4.1 Stufe 2, §4.2 Toast-Regel).
   * Ohne Popup (`hatPopup===false`): Toast, Stufe bleibt `leiste`. Mit
   * Popup: erster Klick → `popup`; zweiter Klick auf DASSELBE Werkzeug
   * (Symbol oder Popup-Fläche) → `fenster` (§4.1 Stufe 3).
   */
  function aufWerkzeugKlick(w: IslandWerkzeug): void {
    // D-8 (E-8 B/C): den beim `pointerdown` gemerkten Zeigertyp EINMAL
    // konsumieren und zurücksetzen (s. `zeigerWarTouch`-Kommentar oben).
    const warTouch = zeigerWarTouch.current;
    zeigerWarTouch.current = false;
    if (!w.hatPopup) {
      // Der Toast IST hier bereits das «Label bei Aktivierung» — für jeden
      // Zeigertyp (D-8: kein zweites Schild nötig).
      zeigeToast(w.name);
      // Sofort-Umschaltung (Achsen-Toggle/Manuell, §4.4) — Erst-Aktivierung,
      // exakt EIN Aufruf, wie beim Popup-Pfad unten.
      onWerkzeugAktion?.(w);
      return;
    }
    if (stufe === 'popup' && aktivesWerkzeugId === w.id) {
      setStufe('fenster');
      return;
    }
    // Erst-Aktivierung dieses Werkzeugs (Wechsel auf eine neue/andere Id) —
    // die Eskalation Popup→Fenster (Zweig oben) ruft NICHT erneut auf,
    // dasselbe Werkzeug ist bereits aktiv.
    if (aktivesWerkzeugId !== w.id) {
      onWerkzeugAktion?.(w);
      // D-8 (E-8 C): Touch/Pen sieht den Lang-Hover-Tooltip nie — das Badge
      // bestätigt die Wahl stattdessen NACH der Aktivierung (Werkzeugwahl
      // ist reiner Moduswechsel, nie destruktiv — Ausprobieren ist billig).
      if (warTouch) zeigeTouchBadge(w.name);
    }
    setAktivesWerkzeugId(w.id);
    setStufe('popup');
  }

  /**
   * Zweiter Klick auf die offene Popup-FLÄCHE selbst (Hintergrund/Ränder)
   * eskaliert zum Fenster. Fable-Gate-Fix PD3: NUR wenn der Klick wirklich
   * die Fläche trifft (`target === currentTarget`) — Klicks auf die
   * Stufe-2-Schnelleinstellungen (Selects/Knöpfe der `inhalte/`-Module)
   * bedienen das Werkzeug und dürfen NICHT eskalieren. Der zweite Klick aufs
   * Werkzeug-SYMBOL eskaliert weiterhin über `aufWerkzeugKlick`.
   */
  function aufPopupKlick(e: { target: EventTarget; currentTarget: EventTarget }): void {
    if (e.target !== e.currentTarget) return;
    setStufe('fenster');
  }

  /** `icX`-Schliessen-Knopf (§4.1 Stufe 3) — geht zurück auf `leiste`, nicht auf `pill`. */
  function schliessePopupOderFenster(): void {
    setStufe('leiste');
    setAktivesWerkzeugId(null);
  }

  // PB2 (Bauauftrag Punkt 4, E3 «Insel-Popups/Fenster adoptieren
  // useOverlaySchliessen»): Esc + Aussenklick schliessen ein offenes
  // Popup/Fenster zurück auf `leiste` — der `icX`-Knopf (`schliessePopup
  // OderFenster` oben) bleibt unverändert ein zweiter, direkter Weg. Esc ist
  // IMMER aktiv (kollidiert mit keinem bestehenden Escape-Handler, s.
  // Bauagenten-Bericht); Aussenklick ist es NUR ausserhalb der drei
  // Canvas-Klickketten-Werkzeuge (`AUSSENKLICK_AUSNAHME` oben).
  const popupOderFensterOffen = stufe === 'popup' || stufe === 'fenster';
  useOverlaySchliessen(wurzelRef, schliessePopupOderFenster, {
    esc: popupOderFensterOffen,
    aussenklick: popupOderFensterOffen && !(aktivesWerkzeugId !== null && AUSSENKLICK_AUSNAHME.has(aktivesWerkzeugId)),
  });

  // PB2 (Bauauftrag Punkt 2): derselbe Hook schliesst den Lang-Hover-
  // Tooltip auf Esc — Aussenklick bleibt aus (der Tooltip klappt sowieso
  // schon beim Weg-Hover zu, s. `aufWerkzeugTooltipLeave` unten).
  useOverlaySchliessen(wurzelRef, () => setTooltipWerkzeugId(null), {
    esc: tooltipWerkzeugId !== null,
    aussenklick: false,
  });

  function raeumeTooltipTimer(): void {
    if (tooltipTimer.current) {
      clearTimeout(tooltipTimer.current);
      tooltipTimer.current = null;
    }
  }

  /** Lang-Hover startet den Tooltip-Timer (§Bauauftrag Punkt 2, ~600ms). */
  function aufWerkzeugTooltipEnter(werkzeugId: string): void {
    raeumeTooltipTimer();
    tooltipTimer.current = setTimeout(() => setTooltipWerkzeugId(werkzeugId), TOOLTIP_VERZOEGERUNG_MS);
  }

  /** Weg-Hover storniert den Timer UND schliesst einen bereits gezeigten Tooltip sofort. */
  function aufWerkzeugTooltipLeave(): void {
    raeumeTooltipTimer();
    setTooltipWerkzeugId(null);
  }

  const aktivesWerkzeug = aktivesWerkzeugId ? werkzeuge.find((w) => w.id === aktivesWerkzeugId) : undefined;
  const label = inselKonfig.label;
  /** PB2 (Bauauftrag Punkt 1): Icon für die Pille dieser Insel — `undefined`
   *  bei Stationen ohne Eintrag (Text-Fallback unten, `label.slice(0,2)`). */
  const PillIcon = ISLAND_PILL_GLYPHEN[island];

  /**
   * v0.9.2 Nachtrag (Owner-Befund 23.07., wörtlich «wenn ich im kosmodesign
   * oben die ansichtinsel öffne und darstellung klicke kommt menü hinter
   * allen anderen auf»): JEDE `IslandShell`-Instanz trägt ihren EIGENEN
   * Stacking-Kontext (`.isl-root` ist `position:fixed` + `z-index:40`,
   * `island.css`). Ein `z-index` auf einem TIEFER verschachtelten Kind (z. B.
   * `KSelect`s `.k-menu` bei `z-index:100`, `aura.css`) bleibt darum in DIESEM
   * Kontext gefangen — er kann nie gegen eine ANDERE Insel antreten, deren
   * eigener Stacking-Kontext ebenfalls bei `z-index:40` startet. Bei
   * gleichem `z-index` gewinnt die im DOM SPÄTERE Insel (`ISLAND_REIHENFOLGE`
   * = zeichnen→ansicht→projekt→austausch, `island-katalog.ts`) jeden
   * visuellen Übertritt — genau das Owner-Beispiel (ANSICHT vor PROJEKT/
   * AUSTAUSCH in der Reihenfolge, ihr Darstellung-Dropdown kann darum unter
   * einer der beiden späteren Inseln verschwinden, sobald sie sich räumlich
   * überschneiden). Fix (Fable-Vorentscheid «aktive Insel bekommt eigene
   * Klasse mit dem höchsten z-index der Insel-Schicht», hier umgesetzt statt
   * eines `createPortal`-Wegs — der Bug ist ein reiner Geschwister-Stacking-
   * Konflikt zwischen `.isl-root`-Instanzen, kein verschachtelter
   * `overflow`/Transform-Käfig, den ein Portal zusätzlich lösen müsste):
   * JEDE Insel, die gerade NICHT `pill` ist (Leiste/Popup/Fenster offen),
   * bekommt `isl-root--offen` (`island.css`, `z-index:100` > alle übrigen
   * Inseln UND den Bühnenkopf) — Hover-/Fokus-/Rückklapp-Logik bleibt
   * unangetastet, nur die CSS-Stapelreihenfolge ändert sich. Sind zufällig
   * ZWEI Inseln gleichzeitig offen (möglich: Hover auf Insel B, während
   * Insel A noch ihren 1000ms-Rückklapp-Timer laufen hat), teilen sie sich
   * denselben erhöhten Wert — die DOM-Reihenfolge entscheidet dann wie
   * zuvor zwischen den beiden, aber BEIDE liegen sicher über jeder
   * geschlossenen (Pill-)Insel. */
  const offen = stufe !== 'pill';

  return (
    <div
      ref={wurzelRef}
      className={`isl-root isl-${orientierung} ${inselKonfig.randKlasse}${offen ? ' isl-root--offen' : ''}`}
      data-testid={`island-${island}-root`}
      data-reduziert={reduziert ? 'true' : 'false'}
      onMouseEnter={aufPointerEnter}
      onMouseLeave={aufPointerLeave}
    >
      {stufe === 'pill' || leisteVerborgen ? (
        <button
          type="button"
          className="isl-pill"
          data-testid={`island-${island}-pill`}
          aria-label={`${label} öffnen`}
          onClick={oeffneLeiste}
        >
          {/* PB2 (Bauauftrag Punkt 1, C-13): die Pille zeigt NUR noch das
              Icon — der Text-Zweiletter-Fallback bleibt für Stationen ohne
              `ISLAND_PILL_GLYPHEN`-Eintrag (E1-Generalisierung, künftige
              PC-Konfigs). */}
          <span className="isl-pill-glyphe" aria-hidden="true">
            {PillIcon ? <PillIcon size={20} /> : label.slice(0, 2)}
          </span>
        </button>
      ) : (
        <div
          className={`isl-leiste${reduziert ? '' : ' isl-anim-islIn'}`}
          data-testid={`island-${island}-leiste`}
        >
          {/* B140 (11.09.2026, Owner-Entscheid «Leiste einklappbar»): der Kopf
              IST der Schalter. Die drei naheliegenderen Plaetze sind gemessen
              und verworfen — s. `leisteEingeklappt` oben.

              ZWEI Bedingungen, beide an der Konfig und keine an einem
              Stationsnamen: `einklappbar` traegt nur, wessen Leistenkopf in
              jedem Zustand erreichbar GEMESSEN ist (Begruendung am Feld in
              `island-katalog.ts` — in KosmoVis ist er es nicht), und eine Insel
              mit `fixeStufe` behaelt den reinen Text, weil sie auf
              Owner-Entscheid dauerhaft offen steht (O-T29). */}
          {inselKonfig.einklappbar === true && inselKonfig.fixeStufe === undefined ? (
            <KTooltip text="Leiste einklappen">
              <button
                type="button"
                className="isl-leiste-kopf isl-leiste-kopf--schalter k-label"
                data-testid={`island-${island}-leiste-einklappen`}
                aria-label={`${label}-Leiste einklappen`}
                onClick={schalteLeiste}
              >
                <span className="isl-leiste-kopf-text">{label}</span>
                <span className="isl-leiste-kopf-glyphe" aria-hidden="true">
                  {EINKLAPP_GLYPHEN[inselKonfig.randKlasse]?.[0] ?? '◂'}
                </span>
              </button>
            </KTooltip>
          ) : (
            <div className="isl-leiste-kopf k-label">{label}</div>
          )}
          {/* E-10: `--isl-zeilen` (von `useLeistenSpalten` oben gesetzt)
              steuert die Spalten dieser Fläche — die Leiste scrollt nie,
              sie wächst in die Breite. `data-werkzeug-anzahl` macht die
              Rechnung im Test nachprüfbar, ohne eine Höhe messen zu müssen. */}
          <div
            ref={werkzeugeRef}
            className="isl-leiste-werkzeuge"
            data-testid={`island-${island}-werkzeuge`}
            data-werkzeug-anzahl={sichtbareWerkzeuge.length}
          >
            {sichtbareWerkzeuge.map((w) => (
              <button
                key={w.id}
                type="button"
                // P-WERKZEUGLEISTE (O-T5): echte Wahrheit vor «zuletzt
                // geklickt» — s. istWerkzeugAktiv-Prop-Kommentar oben.
                className={`isl-werkzeug${istWerkzeugAktiv?.(w.id) === true ? ' isl-werkzeug--an' : ''}`}
                data-testid={`island-werkzeug-${w.id}`}
                aria-pressed={istWerkzeugAktiv?.(w.id) ?? aktivesWerkzeugId === w.id}
                onClick={() => aufWerkzeugKlick(w)}
                // D-8 (E-8 B): Zeigertyp fürs folgende `onClick` merken —
                // ereignisbasiert über den zentralen Helfer, kein Geräteraten.
                onPointerDown={(e) => {
                  zeigerWarTouch.current = istTouchArtig(e);
                }}
                // D-8 (E-8 C): der 600ms-Tooltip bleibt der MAUS vorbehalten —
                // auf Touch würde erst ein gedrückt gehaltener Finger ihn
                // erreichen, also ein Long-press, den E-8 ausdrücklich NICHT
                // einführt; Touch bekommt stattdessen das Aktivierungs-Badge.
                onPointerEnter={(e) => {
                  if (!istTouchArtig(e)) aufWerkzeugTooltipEnter(w.id);
                }}
                onPointerLeave={aufWerkzeugTooltipLeave}
              >
                <span className="isl-werkzeug-glyphe" aria-hidden="true">
                  <WerkzeugGlyphe glyphe={w.glyphe} size={20} />
                </span>
                {/* Der Werkzeug-NAME bleibt als Textzeile unter dem Icon in
                    der Leiste (Bauauftrag Punkt 1) — nur die Pille oben
                    zeigt ausschliesslich das Icon.
                    P3 (PLH-STATUS-2): `status` war bis hierhin nirgends in
                    dieser Datei gelesen — Werkzeuge mit `status!=='vorhanden'`
                    sahen ununterscheidbar aus wie fertige. Gleiches Muster
                    wie `SpezWorkspace.tsx`s «Öffnen (Platzhalter)» (einzige
                    andere Lesestelle von `w.status` in der App): derselbe
                    Suffix, hier am Werkzeugtitel statt am Knopftext. */}
                <span className="isl-werkzeug-titel">
                  {w.name}
                  {w.status === 'vorhanden' ? '' : ' (Platzhalter)'}
                </span>
                {/* P-WERKZEUGLEISTE (O-T6): Werkzeuge MIT Einstellungen
                    (hatPopup) tragen den Pfeil sichtbar — vorher war
                    hatPopup reines Verhalten ohne Indikator. */}
                {w.hatPopup && (
                  <span className="isl-werkzeug-pfeil" aria-hidden="true">
                    ▾
                  </span>
                )}
                {/* PB2 (Bauauftrag Punkt 2, D15): Lang-Hover-Tooltip ersetzt
                    den früheren Popup-Hinweisblock — viewport-geklammert
                    (`useViewportKlammer`, dieselbe Technik wie Popup/
                    Fenster), schliesst über Weg-Hover ODER Esc
                    (`useOverlaySchliessen` oben). */}
                {tooltipWerkzeugId === w.id ? (
                  <div
                    ref={tooltipRef}
                    className="isl-werkzeug-tooltip"
                    role="tooltip"
                    data-testid={`island-werkzeug-${w.id}-tooltip`}
                  >
                    {w.name}
                    {w.hinweis ? ` — ${w.hinweis}` : ''}
                  </div>
                ) : null}
              </button>
            ))}
          </div>
        </div>
      )}

      {stufe === 'popup' && aktivesWerkzeug ? (
        <div
          ref={popupRef}
          className={`isl-popup${reduziert ? '' : ' isl-anim-popIn'}`}
          data-testid={`island-${aktivesWerkzeug.id}-popup`}
          onClick={aufPopupKlick}
        >
          {/* P-STUFE (v0.9.33, B44 W5 aus B43 §1): der Weg von der
              Schnellansicht ins volle Fenster existierte seit PD3 — er war
              nur unentdeckbar. Er ging ausschliesslich über einen ZWEITEN
              Klick aufs Werkzeugsymbol oder auf die freie Popup-Fläche;
              nichts zeigte das an. Der Home-PC-Worker ist als simulierter
              Nutzer selbst darauf hereingefallen und hat daraus geschlossen,
              das Gewissen sei stumm — der empirische Beleg, dass es echten
              Nutzern genauso geht.

              Ein Knopf statt eines Hinweistexts, aus zwei Gründen: der
              frühere feste Hinweis («NOCHMALS KLICKEN → ALLE EINSTELLUNGEN»)
              wurde in PB2/D15 ausgebaut, weil er am unteren Bildschirmrand
              abschnitt — ein Text an derselben Stelle wäre derselbe Fehler.
              Und eine Fläche, die man anfassen kann, ist eine Affordance;
              ein Satz, den man lesen muss, ist eine Bitte.

              Er sitzt LINKS vom Schliessen-Knopf und teilt dessen
              Trefferfläche (44 px, D-8) — dieselbe Ecke, in der Menschen
              Fenster-Bedienung suchen. */}
          <button
            type="button"
            className="isl-vergroessern"
            data-testid={`island-${aktivesWerkzeug.id}-popup-vergroessern`}
            aria-label="Fenster öffnen"
            title="Fenster öffnen — alle Einstellungen"
            onClick={(e) => {
              e.stopPropagation();
              setStufe('fenster');
            }}
          >
            ⤢
          </button>
          <button
            type="button"
            className="isl-schliessen"
            data-testid={`island-${aktivesWerkzeug.id}-popup-schliessen`}
            aria-label="Schliessen"
            onClick={(e) => {
              e.stopPropagation();
              schliessePopupOderFenster();
            }}
          >
            ✕
          </button>
          {/* PB2 (D15, Bauauftrag Punkt 2): der frühere Katalog-Hinweisblock
              («PD2-Hinweis») + die feste «NOCHMALS KLICKEN → ALLE
              EINSTELLUNGEN»-Zeile sind RAUS — beide sassen im geklammerten
              Popup und konnten am unteren linken Bildschirmrand abgeschnitten
              werden (D15-Fundstelle). Der Hinweistext lebt jetzt im
              Lang-Hover-Tooltip am Werkzeugknopf (s. Leiste oben); der
              «nochmals klicken»-Hinweis war ohnehin nur ein statischer
              Bedienhinweis, kein Werkzeug-Inhalt — das Popup zeigt seither
              NUR noch den echten Stufe-2-Inhalt aus `inhalte/`. */}
          {/* E-10 (`insel-stufe.tsx`): der Inhalt erfährt hier, dass er in
              Stufe 2 steht — projektlange Listen kappen sich darauf selbst
              (`useListenKappung`), statt eine Scrollleiste zu bekommen. */}
          <InselStufeContext.Provider value="popup">
            {(() => {
              const Inhalt = inhalte.inhaltFuer(aktivesWerkzeug.id)?.Stufe2;
              return Inhalt ? <Inhalt /> : null;
            })()}
          </InselStufeContext.Provider>
        </div>
      ) : null}

      {stufe === 'fenster' && aktivesWerkzeug ? (
        <div
          ref={fensterRef}
          className={`isl-fenster${reduziert ? '' : ' isl-anim-winIn'}`}
          data-testid={`island-${aktivesWerkzeug.id}-fenster`}
        >
          <button
            type="button"
            className="isl-schliessen"
            data-testid={`island-${aktivesWerkzeug.id}-fenster-schliessen`}
            aria-label="Schliessen"
            onClick={schliessePopupOderFenster}
          >
            ✕
          </button>
          {/* PD3-Registry zuerst (Stufe-3-Inhalt aus `inhalte/`); sonst der
              PD2-Hinweis bzw. PD1-Rahmen.
              E-10: Stufe 3 ist das Fenster — hier zeigt jede Liste alles
              (`InselStufeContext`-Default, hier ausdrücklich gesetzt, weil
              fast alle Registries DIESELBE Komponente für Stufe 2 und 3
              eintragen und der Provider oben sonst nachwirken könnte). */}
          <InselStufeContext.Provider value="fenster">
            {(() => {
              const Inhalt = inhalte.inhaltFuer(aktivesWerkzeug.id)?.Stufe3;
              return Inhalt ? <Inhalt /> : null;
            })()}
          </InselStufeContext.Provider>
          {!inhalte.inhaltFuer(aktivesWerkzeug.id)?.Stufe3 && aktivesWerkzeug.hinweis ? (
            <p className="isl-popup-hinweis k-label k-label-eng" data-testid={`island-${aktivesWerkzeug.id}-fenster-hinweis`}>
              {aktivesWerkzeug.hinweis}
            </p>
          ) : null}
        </div>
      ) : null}

      {toast ? (
        <div className="isl-toast" data-testid="island-toast" role="status">
          {toast}
        </div>
      ) : null}

      {/* D-8 (E-8 C): Touch-Badge «Label bei Aktivierung» — dieselbe
          Toast-Anatomie (Position/Fläche, island.css), eigene Motion:
          Eintritt `--k-motion-settle`, Austritt `--k-motion-fast`. Bei
          `prefers-reduced-motion` entfallen die Animationsklassen wie bei
          allen `isl-anim-*` (das Badge steht dann hart und verschwindet
          hart — die Fristen bleiben dieselben). */}
      {touchBadge ? (
        <div
          className={`isl-toast isl-touch-badge${reduziert ? '' : touchBadge.austritt ? ' isl-anim-badgeAus' : ' isl-anim-badgeIn'}`}
          data-testid="island-touch-badge"
          role="status"
        >
          {touchBadge.text}
        </div>
      ) : null}
    </div>
  );
});

export interface IslandBuehneProps {
  /** PD2: durchgereicht an jede der vier `IslandShell`-Instanzen, s. dortigen Kommentar. */
  onWerkzeugAktion?: (werkzeug: IslandWerkzeug) => void;
  /**
   * PC0 v0.8.4 (V084-SPEZ E1): Insel-Konfigs der Station — Default sind die
   * vier design-Inseln (`DESIGN_INSELN`), byte-gleiches Bestandsverhalten.
   * Andere Stationen (PC1/PC3/PC4/PC5) übergeben hier ihren eigenen Satz.
   */
  inseln?: readonly InselKonfig[];
  /** P-WERKZEUGLEISTE (v0.9.35): durchgereicht an jede Shell — s. IslandShellProps. */
  istWerkzeugAktiv?: (werkzeugId: string) => boolean | undefined;
  /** Inhalts-Registry der Station — Default: die design-Registry. */
  registry?: InhaltsRegistry;
}

/**
 * P1 (v0.9.36, Owner-Entscheid 18.08.2026, ROADMAP 961): dasselbe Handle wie
 * `IslandShellHandle`, nur an der Bühne statt an einer einzelnen Insel —
 * `DesignWorkspace.tsx` kennt die vier Insel-Instanzen nicht einzeln (sie
 * entstehen aus `inseln.map(...)` unten), darum reicht EIN Ruf hier durch
 * alle vier, bis eine sie annimmt.
 */
export interface IslandBuehneHandle {
  oeffnePopupFuerWerkzeug(werkzeugId: string): boolean;
  /** B144 — s. `IslandShellHandle`. */
  oeffneFensterFuerWerkzeug(werkzeugId: string): boolean;
}

/**
 * Alle vier Islands an ihren Rändern (§1/§2) — der PD2-Einbindungspunkt in
 * `DesignWorkspace.tsx` (Default-Flip, nur im Island-Modus gerendert).
 *
 * §10.2 (P8): `useZweiFingerUndoGeste()` hängt hier (nicht in jeder einzelnen
 * `IslandShell`) — EIN Listener-Paar auf `window` für den ganzen Viewport,
 * genau einmal gemountet/entfernt mit der Bühne selbst, kein Vervierfachen
 * über die vier Insel-Instanzen.
 */
export const IslandBuehne = forwardRef<IslandBuehneHandle, IslandBuehneProps>(function IslandBuehne(
  { onWerkzeugAktion, inseln = DESIGN_INSELN, registry, istWerkzeugAktiv }: IslandBuehneProps = {},
  handleRef,
) {
  useZweiFingerUndoGeste();
  // P1: eine Map statt eines Array-Refs — `inseln` ist stationsabhängig
  // unterschiedlich lang (design: 4, andere Stationen ggf. weniger/mehr),
  // Ids sind stabil (React-`key` s.u.), ein `Map`-Set-per-Callback-Ref
  // bleibt darum korrekt, auch wenn eine Insel zwischen Renders verschwindet.
  const shellRefs = useRef<Map<string, IslandShellHandle | null>>(new Map());
  useImperativeHandle(
    handleRef,
    () => ({
      oeffnePopupFuerWerkzeug(werkzeugId: string): boolean {
        for (const konfig of inseln) {
          if (shellRefs.current.get(konfig.id)?.oeffnePopupFuerWerkzeug(werkzeugId)) return true;
        }
        return false;
      },
      oeffneFensterFuerWerkzeug(werkzeugId: string): boolean {
        for (const konfig of inseln) {
          if (shellRefs.current.get(konfig.id)?.oeffneFensterFuerWerkzeug(werkzeugId)) return true;
        }
        return false;
      },
    }),
    [inseln],
  );
  return (
    <>
      {inseln.map((konfig) => (
        <IslandShell
          key={konfig.id}
          ref={(el) => {
            shellRefs.current.set(konfig.id, el);
          }}
          island={konfig.id}
          konfig={konfig}
          {...(registry ? { registry } : {})}
          {...(onWerkzeugAktion ? { onWerkzeugAktion } : {})}
          {...(istWerkzeugAktiv ? { istWerkzeugAktiv } : {})}
        />
      ))}
    </>
  );
});
