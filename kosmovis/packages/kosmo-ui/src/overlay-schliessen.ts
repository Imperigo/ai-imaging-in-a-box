import { useEffect, useRef, type RefObject } from 'react';
import { useFokusFalle } from './fokusfalle';

/**
 * `useOverlaySchliessen` (v0.8.4 PA4, `docs/V084-SPEZ.md` §3 E3) — die
 * Verallgemeinerung der KMenu-Schliesslogik (`overlay.tsx:96-110`: globaler
 * `mousedown` mit `contains()`-Prüfung + globaler `keydown`-Escape) als
 * eigenständiger Hook, damit jedes künftige Overlay dasselbe Gesetz teilt,
 * statt die drei Handler je Konsument neu abzuschreiben.
 *
 * ## API
 *
 * ```ts
 * useOverlaySchliessen(ref, onClose, {
 *   modal?: boolean;            // Default false — EIN Wort für das ganze Gesetz (s. unten)
 *   esc?: boolean;              // Default true  — Escape (global keydown) schliesst
 *   aussenklick?: boolean;      // Default true  — Klick ausserhalb ref (global mousedown) schliesst
 *   fokusfalle?: boolean;       // Default `modal` — Tab zykliert INNERHALB von ref
 *   fokusRueckgabe?: boolean;   // Default `modal` — beim Abbau kehrt der Fokus zum Öffner zurück
 *   fokusAnker?: () => HTMLElement | null; // Ersatzziel, wenn der Öffner verschwunden ist
 *   hoverRueckklappMs?: number; // Default aus   — Pointer-Verlassen von ref startet einen
 *                               //                 Rückklapp-Timer dieser Länge; Pointer-Wiedereintritt
 *                               //                 storniert ihn (kein Timer ohne dieses Feld).
 * });
 * ```
 *
 * ## `modal: true` — ein Wort für das ganze Gesetz (Schichtung 20a/24a/37a/38b/39a)
 *
 * Bis zum 21.09.2026 konnte eine Fläche sich die HÄLFTE des Gesetzes holen,
 * und sieben von elf taten genau das: Escape hier, Aussenklick da, die
 * Fokusfalle (`fokusfalle.ts`) lag daneben und wurde an genau ZWEI Stellen
 * gerufen (beide in `overlay.tsx`), eine Fokusrückgabe gab es im ganzen Repo
 * nicht (gemessen: 17 `.focus()`-Aufrufe, null gemerkte Vorgänger). Drei
 * Flächen trugen `aria-modal`, ohne die Falle zu halten — eine Zusage an ein
 * Vorlesegerät, die die Tastatur sofort widerlegt.
 *
 * `modal: true` schaltet Escape, Falle und Rückgabe GEMEINSAM ein. Wer eine
 * davon einzeln abwählen will, kann es (`fokusfalle: false`, …) — aber
 * ausdrücklich und sichtbar, nicht aus Versehen.
 *
 * **Stapel-Regel (Entscheid 24a):** Escape schliesst die OBERSTE modale
 * Fläche, nicht alle auf einmal. Alle `modal`-Flächen tragen sich darum in
 * einen Modul-Stapel ein; auf Escape antwortet nur die oberste. «Oben» ist
 * zuerst die VERSCHACHTELUNG (liegt A im DOM innerhalb von B, ist A oben —
 * so liegt `WerkzeugSetup` über `Einstellungen`, das es rendert), dann die
 * Reihenfolge der Montage. Ohne diese Regel hätte der Rollout des Gesetzes
 * einen NEUEN Fehler gebaut: ein Escape hätte Werkzeug-Dialog UND
 * Einstellungen zugleich weggeräumt. Nicht-modale Konsumenten (Tooltip,
 * Insel-Popups, `KMenu`) bleiben aussen vor — für sie ändert sich nichts.
 *
 * **Fokusrückgabe (Entscheid 39a):** gemerkt wird das Element, das beim
 * ÖFFNEN den Fokus hatte. Beim Schliessen bekommt es ihn zurück. Ist es
 * inzwischen verschwunden (Menü abgebaut, Liste neu geladen), geht der Fokus
 * an einen Anker — `fokusAnker()`, sonst der beim Öffnen gemerkte
 * `[data-fokus-anker]`/`main`/`[role=main]`/`#root`-Vorfahre des Öffners.
 * `document.body` ist KEIN Ziel: dort landet der Fokus, wenn niemand ihn
 * setzt, und genau das ist der Zustand, den dieser Entscheid abschafft.
 * Hat der Mensch während der offenen Fläche bewusst etwas anderes
 * ausserhalb fokussiert, bleibt das stehen — die Rückgabe stiehlt nicht.
 *
 * `ref` ist das Element, dessen AUSSENSEITE über Aussenklick/Hover-Verlassen
 * entscheidet — bei einer Popup/Trigger-Kombination also der gemeinsame
 * Wrapper (Trigger UND Popup als Kinder), nicht nur der Popup-Körper selbst:
 * ein Klick/Hover auf den Trigger darf das eigene Overlay nicht als
 * "aussen" missverstehen (dasselbe Prinzip wie `KMenu`s `wrapRef`,
 * `overlay.tsx:92/99`).
 *
 * `onClose` wird IMMER als stabile Referenz über ein internes Ref gehalten
 * (kein `useCallback`-Zwang beim Aufrufer nötig) — der Hook selbst bleibt
 * per `esc`/`aussenklick`/`hoverRueckklappMs` re-registriert, `onClose`
 * selbst löst kein Re-Attach der Listener aus.
 *
 * Der Hook ist absichtlich EIGENSCHAFTS-idempotent: er weiss nichts über
 * einen "offen"-Zustand des Aufrufers und ruft `onClose` bei jedem
 * passenden Ereignis auf, auch wenn das Overlay gerade schon zu ist. Jeder
 * bisherige Konsument (KMenu, KDialog) verhält sich exakt so (Esc auf ein
 * bereits geschlossenes `KDialog` ruft `onClose` ebenfalls unbedingt auf,
 * `overlay.tsx:206-212`) — ein zweiter `onClose()`-Ruf auf einen bereits
 * geschlossenen Zustand ist im gesamten Bestand harmlos (State-Setter sind
 * idempotent). Wer das vermeiden will, mountet das Overlay-Element (und
 * damit den Hook-Aufruf) nur, solange es offen ist — wie `KDialog` es tut.
 *
 * ## SSR-/jsdom-Sicherheit
 *
 * Die Hook-FUNKTION selbst fasst `document`/`window` nur innerhalb von
 * `useEffect`-Bodies an (React führt Effects nie während SSR/
 * `renderToString` aus) — zusätzlich prüft jeder Effect `typeof document
 * === 'undefined'`/`typeof window === 'undefined'` defensiv, falls der Hook
 * je aus einem Nicht-DOM-Testkontext (kein `@vitest-environment jsdom`)
 * aufgerufen wird. `ref.current === null` (Element noch nicht gemountet,
 * oder bereits unmountet) lässt den jeweiligen Effect früh und
 * geräuschlos aussteigen.
 *
 * ## Rollout-Pflicht (E3) — wer diesen Hook wie braucht
 *
 * Diese Datei deckt NUR die API ab; die Verdrahtung in den einzelnen
 * Konsumenten gehört den jeweiligen Datei-Eigentümern (Hotspot-Matrix
 * `V084-SPEZ.md` §5) — W1 verdrahtet ausschliesslich `KosmoSymbol.tsx`
 * (s. unten). Für die übrigen Pflicht-Konsumenten (spätere Wellen) gilt
 * dieselbe API, mit unterschiedlicher `ref`-Wahl:
 *
 * - **island-Popups/-Fenster** (`island/IslandShell.tsx`, PB2/PB3/PB4…):
 *   `ref` = der Insel-Wurzelknoten (Pille + Leiste + Popup/Fenster als
 *   Kinder), `hoverRueckklappMs` ersetzt den lokalen
 *   `RUECKKLAPP_MS`/`rueckklappTimer`-Handbau NUR dort, wo §4.2 wörtlich
 *   "Pointer verlässt die Insel" meint — die eigene Popup-/Fenster-
 *   Sonderregel ("bleibt offen, solange Popup/Fenster aktiv", `IslandShell
 *   .tsx:334`) bleibt Sache des Konsumenten (z.B. `aussenklick`/
 *   `hoverRueckklappMs` bedingt aktivieren, je nach `stufe`).
 * - **Orb-Karte** (`shell/KosmoOrb.tsx`-Konversationskarte, Muster
 *   `island/KosmoOrb.tsx:115-184`, E2-Tabelle): `ref` = die Karte selbst;
 *   `esc`+`aussenklick`, kein `hoverRueckklappMs` (Karte schliesst nur
 *   aktiv, nicht durch Weg-Hover — E2-Tabelle kennt dafür Einfachklick).
 * - **StationenOrb** (`shell/StationenOrb.tsx`): `ref` = der Orb-Wrapper;
 *   `esc`+`aussenklick`+`hoverRueckklappMs` je nach dortiger Popup-Stufe.
 * - **OrbitStart-Fächer** (Untertool-Karten der Hauptkacheln): `ref` = der
 *   Fächer-Wrapper der jeweiligen Hauptkachel; `hoverRueckklappMs` bildet
 *   das App-weite "~1s nach Weg-Hover"-Mandat (§1.1) nach.
 *
 * Keine dieser Dateien wird von diesem Paket angefasst (Datei-Kreis-Zusage,
 * `V084-SPEZ.md` §5/§7 Sanktion 2) — die obige Liste ist reine
 * Schnittstellen-Dokumentation für die künftigen Eigentümer.
 */

export interface UseOverlaySchliessenOptionen {
  /**
   * EIN Wort für das ganze Gesetz: Escape + Fokusfalle + Fokusrückgabe, und
   * die Stapel-Regel (nur die oberste modale Fläche antwortet auf Escape).
   * Default `false` — die bestehenden, nicht-modalen Konsumenten (Tooltip,
   * Insel-Popups, `KMenu`) verhalten sich unverändert.
   */
  modal?: boolean;
  /** Escape-Taste (globaler `keydown`) schliesst. Default `true`. */
  esc?: boolean;
  /** Klick ausserhalb von `ref` (globaler `mousedown`) schliesst. Default `true`. */
  aussenklick?: boolean;
  /**
   * Wenn gesetzt: `pointerleave` von `ref.current` startet einen Rückklapp-
   * Timer dieser Länge (ms); ein `pointerenter` VOR Ablauf storniert ihn
   * restlos (kein `onClose`-Ruf). Ohne dieses Feld läuft KEIN Hover-Timer
   * (Default: deaktiviert, nicht 0 — 0 wäre ein gültiger, sofortiger
   * Rückklapp und darf nicht mit "aus" verwechselt werden).
   */
  hoverRueckklappMs?: number;
  /**
   * Tab/Shift+Tab zykliert innerhalb von `ref` (`useFokusFalle`). Default:
   * der Wert von `modal`.
   */
  fokusfalle?: boolean;
  /**
   * Beim Abbau kehrt der Fokus zu dem Element zurück, das ihn vor dem
   * Öffnen hatte. Default: der Wert von `modal`.
   */
  fokusRueckgabe?: boolean;
  /**
   * Ersatzziel für die Rückgabe, wenn der Öffner inzwischen verschwunden
   * ist. Wird nur dann gerufen. Gibt sie `null` zurück, greift der beim
   * Öffnen gemerkte Anker-Vorfahre.
   */
  fokusAnker?: () => HTMLElement | null;
  /**
   * Für NICHT-modale Flächen, die trotzdem auf Escape hören: solange
   * irgendeine modale Fläche offen ist, schweigt diese hier. Default
   * `false` — die bestehenden Konsumenten (Tooltip, Insel-Popups, KMenu)
   * bleiben unverändert.
   *
   * Gebaut für Starter-Guide und Dock-Tour: beide sind bewusst nicht modal
   * (kein Scrim, die Oberfläche darunter bleibt bedienbar), sollen aber seit
   * Entscheid 22b auf Escape enden. Ohne diesen Riegel beendete EIN Escape,
   * das den Einstellungen-Dialog schliessen soll, den Rundgang gleich mit —
   * genau der Verlust, den Entscheid 24a verbietet.
   */
  escWeichtModalen?: boolean;
}

/**
 * Anker-Kandidaten für die Fokusrückgabe, wenn der Öffner weg ist — vom
 * Genauesten zum Allgemeinsten. `document.body` steht bewusst NICHT hier:
 * er ist der Zustand, den Entscheid 39a abschafft, kein Ziel.
 */
const FOKUS_ANKER_AUSWAHL = '[data-fokus-anker], main, [role="main"], #root';

function istBrauchbar(el: Element | null | undefined): el is HTMLElement {
  return el instanceof HTMLElement && el.isConnected && el !== document.body;
}

/**
 * Setzt den Fokus, auch auf ein Element, das von sich aus keinen annimmt
 * (ein `<main>` etwa). `tabindex="-1"` macht es fokussierbar, OHNE es in die
 * Tab-Reihenfolge zu heben — der Anker bleibt für die Tastatur unsichtbar,
 * ist aber ein ehrlicher Landeplatz.
 */
function fokussiere(el: HTMLElement): void {
  if (!el.hasAttribute('tabindex') && el.tabIndex < 0) el.setAttribute('tabindex', '-1');
  el.focus();
}

/** Ein eingetragener modaler Konsument (s. Stapel-Regel im Kopfkommentar). */
interface ModalEintrag {
  nummer: number;
  ref: RefObject<HTMLElement | null>;
}

const modalStapel: ModalEintrag[] = [];
let modalZaehler = 0;

/** «a liegt über b» — erst Verschachtelung, dann Montage-Reihenfolge. */
function liegtUeber(a: ModalEintrag, b: ModalEintrag): boolean {
  const ea = a.ref.current;
  const eb = b.ref.current;
  if (ea !== null && eb !== null && ea !== eb) {
    if (eb.contains(ea)) return true;
    if (ea.contains(eb)) return false;
  }
  return a.nummer > b.nummer;
}

function obersterModal(): ModalEintrag | null {
  let bester: ModalEintrag | null = null;
  for (const eintrag of modalStapel) {
    if (bester === null || liegtUeber(eintrag, bester)) bester = eintrag;
  }
  return bester;
}

/**
 * Registriert Esc-/Aussenklick-/Hover-Rückklapp-Schliessverhalten für ein
 * Overlay. Siehe Datei-Kopfkommentar für die volle API-/Rollout-Doku.
 */
export function useOverlaySchliessen(
  ref: RefObject<HTMLElement | null>,
  onClose: () => void,
  optionen: UseOverlaySchliessenOptionen = {},
): void {
  const {
    modal = false,
    esc = true,
    aussenklick = true,
    hoverRueckklappMs,
    fokusfalle = modal,
    fokusRueckgabe = modal,
    fokusAnker,
    escWeichtModalen = false,
  } = optionen;

  // `onClose` bleibt für die Effects unten eine stabile Referenz (kein
  // Re-Attach der DOM-Listener bei jedem Render, selbst wenn der Aufrufer
  // eine Inline-Funktion übergibt) — dasselbe Bedürfnis wie überall im
  // Bestand, wo Callback-Props nicht zwingend memoisiert ankommen.
  const onCloseRef = useRef(onClose);
  onCloseRef.current = onClose;

  const fokusAnkerRef = useRef(fokusAnker);
  fokusAnkerRef.current = fokusAnker;

  // Die Identität DIESER Fläche im Modal-Stapel — einmal je Hook-Instanz
  // vergeben (Lazy-Ref-Muster), `ref` selbst ist stabil.
  const meinEintrag = useRef<ModalEintrag | null>(null);
  if (meinEintrag.current === null) {
    modalZaehler += 1;
    meinEintrag.current = { nummer: modalZaehler, ref };
  }

  // Ein- und Austragen in den Modal-Stapel (Entscheid 24a). Steht VOR dem
  // Escape-Effect, damit die Eintragung beim Montieren schon steht, wenn der
  // Escape-Horcher sie das erste Mal befragt.
  useEffect(() => {
    if (!modal) return undefined;
    const eintrag = meinEintrag.current!;
    modalStapel.push(eintrag);
    return () => {
      const i = modalStapel.indexOf(eintrag);
      if (i >= 0) modalStapel.splice(i, 1);
    };
  }, [modal]);

  // Fokusfalle (Entscheid 37a) — dasselbe Haus-Gesetz, derselbe Haken: wer
  // `modal` bestellt, bekommt sie mit, statt sie zu vergessen.
  useFokusFalle(ref, fokusfalle);

  // Fokusrückgabe (Entscheid 39a). Der Effect merkt beim Öffnen, WER den
  // Fokus hatte, und gibt ihn beim Abbau zurück.
  useEffect(() => {
    if (!fokusRueckgabe) return undefined;
    if (typeof document === 'undefined') return undefined;
    const oeffner = document.activeElement;
    const gemerkterAnker = oeffner instanceof Element ? oeffner.closest<HTMLElement>(FOKUS_ANKER_AUSWAHL) : null;
    // Der Behälter wird HIER festgehalten, nicht erst im Aufräumen: React
    // löst `ref.current` beim Abbau vor den Effect-Aufräumern, und ein
    // `null` dort würde "der Fokus lag in der Fläche" fälschlich als
    // "der Mensch hat anderswohin geklickt" lesen.
    const behaelter = ref.current;
    return () => {
      const aktiv = document.activeElement;
      const fokusIstFremd =
        istBrauchbar(aktiv) && (behaelter === null || !behaelter.contains(aktiv));
      if (fokusIstFremd) return; // der Mensch ist schon woanders — nicht stehlen
      if (istBrauchbar(oeffner)) {
        fokussiere(oeffner);
        return;
      }
      const ersatz = fokusAnkerRef.current?.() ?? null;
      if (istBrauchbar(ersatz)) {
        fokussiere(ersatz);
        return;
      }
      if (istBrauchbar(gemerkterAnker)) {
        fokussiere(gemerkterAnker);
        return;
      }
      const haus = document.querySelector<HTMLElement>(FOKUS_ANKER_AUSWAHL);
      if (istBrauchbar(haus)) fokussiere(haus);
      // Bleibt nichts übrig, wird NICHTS gesetzt — ein erzwungener
      // `document.body`-Fokus wäre genau der Zustand, den 39a abschafft.
    };
  }, [fokusRueckgabe, ref]);

  // Esc + Aussenklick — 1:1 die KMenu-Logik (`overlay.tsx:96-110`), nur
  // generalisiert auf ein beliebiges `ref`-Element statt des internen
  // `wrapRef`.
  useEffect(() => {
    if (typeof document === 'undefined') return undefined;
    if (!esc && !aussenklick) return undefined;

    const schliesseAussen = (e: MouseEvent) => {
      if (!aussenklick) return;
      const el = ref.current;
      const ziel = e.target as Node;
      // Seit P-F6 (v0.9.2) rendert `KSelect` seine Listbox als
      // `document.body`-Portal — sie liegt damit IMMER ausserhalb von `ref`,
      // obwohl sie logisch zum Overlay-Inhalt gehört. Ein mousedown auf eine
      // Option darf das umgebende Overlay nicht schliessen (sonst unmountet
      // der KSelect vor dem `click` und die Wahl verpufft — E2E-Befund
      // island-leer, Trace-Ziel). `[data-kselect-portal]` markiert genau
      // diese Listbox (`select.tsx`).
      if (ziel instanceof Element && ziel.closest('[data-kselect-portal]') !== null) return;
      // U25 Phase 6 (Welle D4): «Rückgängig»/«Wiederholen» im Inselkopf wirken auf das Modell, das ein offenes
      // Fenster gerade zeigt (KV, Mängel …). Ein Klick darauf ist kein «weg von hier» — sonst schliesst der
      // Undo das Fenster, dessen Wirkung man sehen will. `[data-aussenklick-frei]` markiert solche Knöpfe.
      if (ziel instanceof Element && ziel.closest('[data-aussenklick-frei]') !== null) return;
      if (el && !el.contains(ziel)) onCloseRef.current();
    };
    const schliesseEsc = (e: KeyboardEvent) => {
      if (!esc) return;
      if (e.key !== 'Escape') return;
      // Entscheid 24a: von mehreren modalen Flächen antwortet nur die
      // oberste. Nicht-modale Konsumenten überspringen diese Prüfung —
      // für sie bleibt alles wie bisher.
      if (modal && obersterModal() !== meinEintrag.current) return;
      // Nicht-modale Flächen, die ausdrücklich zurücktreten (Starter-Guide,
      // Dock-Tour): solange eine modale Fläche offen ist, gehört Escape ihr.
      if (!modal && escWeichtModalen && obersterModal() !== null) return;
      onCloseRef.current();
    };

    document.addEventListener('mousedown', schliesseAussen);
    document.addEventListener('keydown', schliesseEsc);
    return () => {
      document.removeEventListener('mousedown', schliesseAussen);
      document.removeEventListener('keydown', schliesseEsc);
    };
  }, [ref, esc, aussenklick, modal, escWeichtModalen]);

  // Hover-Rückklapp — eigener Effect (eigene Lebensdauer, eigener Timer),
  // nur aktiv, wenn `hoverRueckklappMs` gesetzt ist.
  useEffect(() => {
    if (typeof window === 'undefined') return undefined;
    if (hoverRueckklappMs === undefined) return undefined;
    const el = ref.current;
    if (!el) return undefined;

    let timer: ReturnType<typeof setTimeout> | null = null;
    const storniere = () => {
      if (timer !== null) {
        clearTimeout(timer);
        timer = null;
      }
    };
    const aufLeave = () => {
      storniere();
      timer = setTimeout(() => {
        timer = null;
        onCloseRef.current();
      }, hoverRueckklappMs);
    };
    const aufEnter = () => {
      storniere();
    };

    el.addEventListener('pointerleave', aufLeave);
    el.addEventListener('pointerenter', aufEnter);
    return () => {
      storniere();
      el.removeEventListener('pointerleave', aufLeave);
      el.removeEventListener('pointerenter', aufEnter);
    };
  }, [ref, hoverRueckklappMs]);
}
