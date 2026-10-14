import {
  useLayoutEffect,
  useRef,
  useState,
  useSyncExternalStore,
  type ReactNode,
  type RefObject,
} from 'react';
import { createPortal } from 'react-dom';

/**
 * **Fokus-Schleier** (Owner-Wunsch 13.10.2026, Entwurf `docs/entwuerfe/fokus-schleier/`).
 *
 * Was sich über die Arbeitsfläche legt und eine Antwort will, bekommt das Auge: dahinter wird alles leicht unscharf
 * und getönt, die Fläche selbst steht scharf darüber. Dieser Baustein ist die Art 1, «Wählen» (Rad, Menüs,
 * Rechtsklick). Dialoge (Art 2/3) brauchen ihn nicht: Sie haben ihren Scrim schon, und `aura.css` gibt jedem
 * `.k-dialog-scrim` die Unschärfe direkt.
 *
 * Was der Haken tut, solange `offen`:
 *  1. Er sucht die **äusserste feste Hülle** der Fläche (das letzte `position: fixed` bis hinauf vor `#root`) und
 *     hebt sie auf den Zwischenrang «schwebend + 90» (`data-k-fokus='gehoben'`). Sonst bliebe scharf, was zufällig gleich hoch liegt.
 *  2. Er legt den Schleier **in dieselbe Stapelebene** wie die Hülle, als ihr Geschwister. Ganz oben im Dokument läge
 *     er über der Fläche selbst, weil die App-Hülle eine eigene Stapelebene bildet. Gemessen in der Entwurfsaufnahme:
 *     dort verwischte das Rad sich selbst.
 *  3. **Ein Klick auf den Schleier schliesst nur** (Owner-Entscheid 3): Er wählt nichts im Modell und geht nicht durch.
 *  4. **Nur ein Schleier** (Schichtung Nr. 12): Sind zwei Flächen zugleich offen, zeigt nur die zuletzt geöffnete
 *     einen.
 *
 * Die Stärke steht in `aura.css` (`--k-fokus-*`); am Linux-Gerät ohne Weichzeichner (`data-glas='deckend'`) bleibt
 * nur die Tönung.
 */

let stapel: readonly object[] = [];
const hoerer = new Set<() => void>();
const melde = () => hoerer.forEach((h) => h());
const abonniere = (h: () => void) => {
  hoerer.add(h);
  return () => {
    hoerer.delete(h);
  };
};

/** Die äusserste feste Hülle einer Fläche: das letzte `position: fixed` auf dem Weg nach oben, vor `#root`. */
export function fokusHuelle(el: HTMLElement): HTMLElement {
  let aussen = el;
  for (
    let e: HTMLElement | null = el;
    e && e !== document.body && e.id !== 'root';
    e = e.parentElement
  ) {
    if (getComputedStyle(e).position === 'fixed') aussen = e;
  }
  return aussen;
}

export interface FokusSchleierOptionen {
  offen: boolean;
  /** Schliesst die Fläche; ein Klick auf den Schleier ruft es. */
  onSchliessen: () => void;
}

/**
 * Meldet eine Fläche der Art «Wählen» an. Gibt den Schleier zurück; der Aufrufer rendert ihn irgendwo in seinem
 * Baum (er landet per Portal neben der Hülle).
 */
export function useFokusSchleier(
  ref: RefObject<HTMLElement | null>,
  { offen, onSchliessen }: FokusSchleierOptionen,
): ReactNode {
  const marke = useRef<object>({}).current;
  const schliessen = useRef(onSchliessen);
  schliessen.current = onSchliessen;
  const [huelle, setHuelle] = useState<HTMLElement | null>(null);
  const oben = useSyncExternalStore(
    abonniere,
    () => stapel[stapel.length - 1] === marke,
    () => false,
  );

  useLayoutEffect(() => {
    const el = ref.current;
    if (!offen || !el) {
      setHuelle(null);
      return undefined;
    }
    const h = fokusHuelle(el);
    h.setAttribute('data-k-fokus', 'gehoben');
    stapel = [...stapel, marke];
    melde();
    setHuelle(h);
    return () => {
      h.removeAttribute('data-k-fokus');
      stapel = stapel.filter((m) => m !== marke);
      melde();
    };
  }, [offen, ref, marke]);

  const ziel = huelle?.parentElement;
  if (!offen || !oben || !ziel) return null;
  return createPortal(
    <div
      className='k-fokus-schleier'
      data-testid='k-fokus-schleier'
      aria-hidden='true'
      // Nur schliessen, und erst beim KLICK: verschwände der Schleier schon beim Drücken, träfe das Loslassen das
      // Modell darunter und wählte dort aus (gemessen, `e2e/fokus-schleier.spec.ts`). Druck und Mausdruck enden
      // darum hier, damit auch die Aussenklick-Horcher der Fläche nicht vorzeitig schliessen.
      onPointerDown={(e) => {
        e.preventDefault();
        e.stopPropagation();
      }}
      onMouseDown={(e) => {
        e.preventDefault();
        e.stopPropagation();
      }}
      onClick={(e) => {
        e.stopPropagation();
        schliessen.current();
      }}
    />,
    ziel,
  );
}
