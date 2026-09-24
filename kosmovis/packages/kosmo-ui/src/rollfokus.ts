import { useCallback, useRef, useState, type KeyboardEvent as ReactKeyboardEvent } from 'react';

/**
 * `useRollfokus` (P-g / Tastatur-Rückgrat, `docs/UI-UX-2026-09-08-TASTATUR-
 * RUECKGRAT.md`) — der «roving tabindex»-Vertrag, der im ganzen Repo fehlte
 * (Gegenprobe, englisch UND deutsch, `roving`/`rollfokus`: null Treffer vor
 * diesem Paket). Eine Gruppe gleichrangiger Elemente (Tabs, Werkzeug-Knöpfe,
 * Menü-Einträge) bekommt damit EIN Standard-Tastaturverhalten statt fünf
 * verschiedenen Halblösungen je Konsument.
 *
 * ## Warum "roving tabindex" statt fünf `tabIndex={0}`
 *
 * Fünf Elemente mit `tabIndex={0}` bedeuten fünf Tab-Stopps — die Gruppe
 * frisst so viele Tab-Drücke wie sie Mitglieder hat, bevor der Fokus
 * weiterwandert. Der Standard-Vertrag für Button-/Tab-/Menü-Gruppen
 * (WAI-ARIA APG, "roving tabindex") ist der umgekehrte: GENAU EIN Mitglied
 * trägt `tabIndex={0}` (das zuletzt aktive, initial das erste), alle
 * anderen `tabIndex={-1}` — die Gruppe ist EIN Tab-Stopp von aussen, und
 * INNERHALB der Gruppe bewegen die Pfeiltasten den Fokus (und damit, welches
 * Mitglied die `0` trägt).
 *
 * ## API
 *
 * ```ts
 * const rf = useRollfokus(anzahl, {
 *   ausrichtung?: 'waagrecht' | 'senkrecht'; // Default 'waagrecht'
 *   umlaufend?: boolean;                     // Default false
 *   anfangsIndex?: number;                   // Default 0 — nur beim ERSTEN Render gelesen
 * });
 *
 * rf.aktiverIndex        // number — welcher Index gerade tabIndex=0 trägt
 * rf.tabIndexFuer(i)     // 0 | -1 — direkt ins tabIndex-Attribut
 * rf.onKeyDown(e, i)     // KeyboardEventHandler, i = Index DIESES Elements
 * rf.setzeAktivenIndex(i) // manuell setzen (z.B. nach einem Klick)
 * ```
 *
 * `ausrichtung` bestimmt, welches Tastenpaar bewegt:
 * - `'waagrecht'` (Default, für Tabs/Toolbars): `ArrowRight`/`ArrowLeft`.
 * - `'senkrecht'` (für Menüs/Listen): `ArrowDown`/`ArrowUp`.
 *
 * `Home`/`End` springen unabhängig von der Ausrichtung immer zum ersten/
 * letzten Element. `umlaufend: true` lässt ein `ArrowRight`/`ArrowDown` am
 * letzten Element zum ersten springen (und umgekehrt); ohne diese Option
 * bleibt der Fokus am Rand stehen (Default — die meisten Bestandsmuster im
 * Repo, z.B. `KSelect`s ↑/↓, laufen NICHT um).
 *
 * `rf.onKeyDown` ruft `e.preventDefault()` NUR, wenn die Taste tatsächlich
 * eine Bewegung auslöst (Pfeil in eine gültige Richtung, oder Home/End) —
 * andere Tasten (Enter, Space, Tab, Escape, …) laufen unverändert zum
 * Aufrufer durch, der sie wie bisher selbst behandelt (Klick-Handler,
 * Overlay-Schluss, …). Der Hook führt selbst KEINEN `.focus()`-DOM-Aufruf
 * aus — er berechnet nur den neuen `aktiverIndex` und meldet ihn über den
 * Rückgabewert; das Fokussieren des zugehörigen DOM-Knotens bleibt Sache
 * des Konsumenten (der `ref`/`id` je Element ohnehin schon kennt). Diese
 * Trennung hält den Hook frei von jeder DOM-Kenntnis — er ist mit
 * `renderToStaticMarkup` prüfbar wie jeder reine Hook.
 *
 * ## Dynamisch wechselnde Anzahl
 *
 * `anzahl` darf sich zwischen Renders ändern (Filter, bedingtes Rendern
 * einzelner Einträge, ein KMenu, dessen `items` sich zur Laufzeit ändern).
 * Wird `aktiverIndex` durch eine kleinere `anzahl` ungültig (z.B. Element 4
 * verschwindet, `aktiverIndex` war 4), klemmt der Hook ihn beim NÄCHSTEN
 * Zugriff auf `anzahl - 1` — nie negativ, nie ausserhalb. Bei `anzahl === 0`
 * bleibt `aktiverIndex` bei `0`, aber `tabIndexFuer` wird für eine leere
 * Gruppe ohnehin nie aufgerufen (keine Elemente zum Rendern).
 *
 * ## Die EINE-`tabIndex=0`-Garantie
 *
 * Für jede `anzahl > 0` gilt nach JEDEM Aufruf von `onKeyDown` (und initial):
 * GENAU EIN `i` mit `tabIndexFuer(i) === 0`, alle übrigen `-1`. Das ist die
 * Eigenschaft, die `test/rollfokus.test.ts` nach JEDEM simulierten
 * Tastendruck erneut prüft (nicht nur am Ende) — der falsifizierbare
 * Fehlerfall dieses Bausteins: zwei gleichzeitige `tabIndex=0` wären ein
 * gebrochener Vertrag (zwei Tab-Stopps statt einem), kein kosmetischer
 * Fehler.
 *
 * ## SSR-/jsdom-Sicherheit
 *
 * Der Hook fasst weder `document` noch `window` an — er rechnet
 * ausschliesslich mit `KeyboardEvent.key`/`.preventDefault()`, die auch das
 * SYNTHETISCHE React-`KeyboardEvent` trägt. Er ist damit ohne jede
 * SSR-/jsdom-Fallunterscheidung sicher: `renderToStaticMarkup` kann die
 * `tabIndex`-Attribute ohne DOM prüfen, und ein simuliertes
 * `new KeyboardEvent('keydown', {...})`, per `dispatchEvent` auf ein
 * gemountetes Element geschickt, durchläuft denselben Code wie ein echter
 * Tastendruck (React bindet `onKeyDown` als nativen `keydown`-Listener auf
 * das Element).
 *
 * ## Rollout-Pflicht — wer diesen Hook wie braucht
 *
 * Diese Datei deckt NUR die API ab; die Verdrahtung in den einzelnen
 * Konsumenten gehört den jeweiligen Datei-Eigentümern (Dateikreis-Zusage
 * dieses Pakets, `docs/UI-UX-2026-09-08-TASTATUR-RUECKGRAT.md` §Dateikreis)
 * — KEINE der folgenden Dateien wird von P-g angefasst:
 *
 * - **`tabs.tsx:26-48` (`KTabs`)** — rendert heute jeden Tab-Button ohne
 *   `tabIndex`-Steuerung (jeder Tab ist ein eigener Tab-Stopp, unabhängig
 *   davon, ob er `aria-selected` trägt). Rollout: `ausrichtung: 'waagrecht'`,
 *   `anzahl = items.length`, `aktiverIndex` mit dem Index von `aktiv`
 *   synchronisiert (kontrollierte Komponente — Klick UND Pfeiltaste ändern
 *   `aktiv` über `onChange`, nicht nur einen internen Hook-State).
 * - **`field.tsx:146` (`KToolbar`) / `field.tsx:156` (`KToolGruppe`)** —
 *   reine Container ohne Kenntnis ihrer Kinder; der Rollfokus gehört auf
 *   Ebene der KONKRETEN Werkzeug-Knopf-Liste innerhalb einer Gruppe (deren
 *   Aufrufer die Knopfzahl kennt), nicht auf `KToolbar`/`KToolGruppe`
 *   selbst, die beliebige Kinder rendern.
 * - **`overlay.tsx:147` (`KMenu`-Einträge)** — trägt heute pauschal
 *   `tabIndex={offen ? 0 : -1}` an JEDEM Menüpunkt: eine Halblösung, die
 *   zwar verhindert, dass geschlossene Menüs Tab-Stopps hinterlassen, aber
 *   innerhalb eines OFFENEN Menüs weiterhin so viele Tab-Stopps erzeugt wie
 *   es Einträge gibt (kein Pfeiltasten-Wandern). Rollout: `ausrichtung:
 *   'senkrecht'`, `anzahl` = Zahl der NICHT-Trenner-Einträge, kombiniert mit
 *   der bereits vorhandenen Fokus-Falle (`fokusfalle.ts`) — die Falle hält
 *   den Fokus im Menü, der Rollfokus bewegt ihn zwischen den Einträgen.
 *
 * Für spätere Wellen (nicht in dieser Datei behandelt, nur benannt): die
 * Zeichenflächen-Werkzeugleiste, der Knotengraph und die mausgebundene
 * Station aus der Bestandsaufnahme sind KEINE reinen Button-/Tab-Gruppen
 * (2D-Canvas-Pan, Node-Editor-Kanten) — sie brauchen eigene
 * Tastatur-Verträge, für die `useRollfokus` höchstens ein TEILBAUSTEIN ist
 * (z.B. für eine Werkzeug-Palette darin), nicht die Gesamtlösung.
 */
export interface UseRollfokusOptionen {
  /** Welches Pfeiltasten-Paar bewegt. Default `'waagrecht'`. */
  ausrichtung?: 'waagrecht' | 'senkrecht';
  /** Pfeil am letzten/ersten Element springt zum anderen Ende. Default `false`. */
  umlaufend?: boolean;
  /** Initialer aktiver Index. Default `0`. */
  anfangsIndex?: number;
}

export interface Rollfokus {
  /** Index des Mitglieds, das gerade `tabIndex=0` trägt. */
  aktiverIndex: number;
  /** `0` für den aktiven Index, sonst `-1` — direkt ins `tabIndex`-Attribut. */
  tabIndexFuer: (index: number) => 0 | -1;
  /** An `onKeyDown` jedes Gruppenmitglieds binden, mit dessen eigenem Index. */
  onKeyDown: (e: ReactKeyboardEvent<HTMLElement>, index: number) => void;
  /** Aktiven Index von aussen setzen (z.B. nach einem Maus-/Touch-Klick). */
  setzeAktivenIndex: (index: number) => void;
}

/**
 * Roving-tabindex-Hook für eine Gruppe von `anzahl` gleichrangigen
 * Elementen. Siehe Datei-Kopfkommentar für die volle API-/Rollout-Doku.
 */
export function useRollfokus(anzahl: number, optionen: UseRollfokusOptionen = {}): Rollfokus {
  const { ausrichtung = 'waagrecht', umlaufend = false, anfangsIndex = 0 } = optionen;
  const [aktiverIndexRoh, setAktiverIndexRoh] = useState(anfangsIndex);

  // Klemmt gegen die AKTUELLE `anzahl` — deckt sowohl eine schrumpfende
  // Gruppe (Element verschwunden) als auch `anzahl === 0` ab, ohne dass der
  // Hook selbst einen Effect für den Fall bräuchte.
  const maxIndex = Math.max(0, anzahl - 1);
  const aktiverIndex = Math.min(Math.max(0, aktiverIndexRoh), maxIndex);

  // Stabile Referenz auf die aktuelle `anzahl`/`ausrichtung`/`umlaufend`, damit
  // `onKeyDown` unten nicht bei jedem Render neu erzeugt werden muss (die
  // Werte ändern sich selten, ein `useCallback` mit ihnen als Deps würde bei
  // JEDER Elternkomponenten-Aktualisierung neu binden, sobald `anzahl` als
  // Inline-Ausdruck übergeben wird).
  const anzahlRef = useRef(anzahl);
  anzahlRef.current = anzahl;
  const ausrichtungRef = useRef(ausrichtung);
  ausrichtungRef.current = ausrichtung;
  const umlaufendRef = useRef(umlaufend);
  umlaufendRef.current = umlaufend;

  const tabIndexFuer = useCallback((index: number): 0 | -1 => (index === aktiverIndex ? 0 : -1), [aktiverIndex]);

  const setzeAktivenIndex = useCallback((index: number) => {
    setAktiverIndexRoh(index);
  }, []);

  const onKeyDown = useCallback((e: ReactKeyboardEvent<HTMLElement>, index: number) => {
    const n = anzahlRef.current;
    if (n === 0) return;
    const letzter = n - 1;
    const vorwaerts = ausrichtungRef.current === 'waagrecht' ? 'ArrowRight' : 'ArrowDown';
    const rueckwaerts = ausrichtungRef.current === 'waagrecht' ? 'ArrowLeft' : 'ArrowUp';
    const uml = umlaufendRef.current;

    let ziel: number | undefined;
    if (e.key === vorwaerts) {
      ziel = index < letzter ? index + 1 : uml ? 0 : undefined;
    } else if (e.key === rueckwaerts) {
      ziel = index > 0 ? index - 1 : uml ? letzter : undefined;
    } else if (e.key === 'Home') {
      ziel = 0;
    } else if (e.key === 'End') {
      ziel = letzter;
    }

    if (ziel !== undefined) {
      e.preventDefault();
      setAktiverIndexRoh(ziel);
    }
  }, []);

  return { aktiverIndex, tabIndexFuer, onKeyDown, setzeAktivenIndex };
}
