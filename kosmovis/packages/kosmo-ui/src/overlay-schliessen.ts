import { useEffect, useRef, type RefObject } from 'react';

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
 *   esc?: boolean;              // Default true  — Escape (global keydown) schliesst
 *   aussenklick?: boolean;      // Default true  — Klick ausserhalb ref (global mousedown) schliesst
 *   hoverRueckklappMs?: number; // Default aus   — Pointer-Verlassen von ref startet einen
 *                               //                 Rückklapp-Timer dieser Länge; Pointer-Wiedereintritt
 *                               //                 storniert ihn (kein Timer ohne dieses Feld).
 * });
 * ```
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
  const { esc = true, aussenklick = true, hoverRueckklappMs } = optionen;

  // `onClose` bleibt für die Effects unten eine stabile Referenz (kein
  // Re-Attach der DOM-Listener bei jedem Render, selbst wenn der Aufrufer
  // eine Inline-Funktion übergibt) — dasselbe Bedürfnis wie überall im
  // Bestand, wo Callback-Props nicht zwingend memoisiert ankommen.
  const onCloseRef = useRef(onClose);
  onCloseRef.current = onClose;

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
      if (el && !el.contains(ziel)) onCloseRef.current();
    };
    const schliesseEsc = (e: KeyboardEvent) => {
      if (!esc) return;
      if (e.key === 'Escape') onCloseRef.current();
    };

    document.addEventListener('mousedown', schliesseAussen);
    document.addEventListener('keydown', schliesseEsc);
    return () => {
      document.removeEventListener('mousedown', schliesseAussen);
      document.removeEventListener('keydown', schliesseEsc);
    };
  }, [ref, esc, aussenklick]);

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
