import { useEffect, useRef } from 'react';
import type { KIconName } from './icons';
import { KIcon } from './icons';
import { useRollfokus } from './rollfokus';

/**
 * KTabs (W0, UI-KONZEPT-065 §3) — `role=tab`-Buttons, Label bleibt
 * sichtbarer TEXT (`toHaveText`-Verträge), Icon additiv. Aktiv: 2px-Akzent-
 * Unterstrich, KEINE Füllfläche.
 *
 * ## Rollfokus (P-TASTATUR-LUECKEN, 09.09.2026)
 *
 * Bis hierher trug **jeder** Reiter einen eigenen Tab-Stopp: eine Leiste mit
 * neun Reitern kostete neun Tabulator-Anschläge, bevor man am Inhalt war, und
 * die Pfeiltasten taten nichts. Das ist genau der Fall, für den
 * `useRollfokus` gebaut wurde — der Rollout-Kommentar dort nennt `KTabs`
 * ausdrücklich als ersten Ort, und dieser Baustein war der einzige, der ihn
 * noch nicht benutzt hat.
 *
 * **Manuelle Aktivierung, nicht automatische.** Die Pfeiltasten bewegen den
 * FOKUS; ausgewählt wird mit Enter/Leertaste (der native Knopf tut das von
 * selbst). Beides ist nach WAI-ARIA erlaubt, und die manuelle Form ist hier
 * die richtige: ein Reiterwechsel in dieser App tauscht ganze Inhalte aus
 * (Insel-Inhalte, Panel-Stufen). Wer mit dem Pfeil an fünf Reitern
 * vorbeiwandert, um zum sechsten zu kommen, würde bei automatischer
 * Aktivierung fünf Inhalte laden — sichtbar, spürbar und ungewollt.
 *
 * **Der Tab-Stopp folgt der Auswahl.** Wechselt `aktiv` von aussen (Klick,
 * Programm), wandert der Rollfokus mit: wer danach in die Leiste tabuliert,
 * landet auf dem ausgewählten Reiter, nicht auf dem zuletzt bepfeilten.
 *
 * **Fokus wird nur nach einem Tastendruck gesetzt**, nie beim Rendern. Ein
 * Effekt, der beim Mounten `focus()` ruft, reisst den Fokus aus dem Formular,
 * in dem gerade jemand tippt — deshalb das Merkzeichen `tasteWarZuletzt`.
 */
export interface KTabItem {
  id: string;
  label: string;
  icon?: KIconName;
  disabled?: boolean;
  /** Optionales `data-testid` je Tab-Knopf. */
  testid?: string;
}

export interface KTabsProps {
  items: readonly KTabItem[];
  aktiv: string;
  onChange: (id: string) => void;
  size?: 'sm' | 'md';
  'data-testid'?: string;
}

export function KTabs({ items, aktiv, onChange, size = 'md', ...rest }: KTabsProps) {
  const aktivIndex = items.findIndex((i) => i.id === aktiv);
  const rollfokus = useRollfokus(items.length, {
    ausrichtung: 'waagrecht',
    umlaufend: true,
    anfangsIndex: Math.max(0, aktivIndex),
  });
  const knoepfe = useRef<(HTMLButtonElement | null)[]>([]);
  const tasteWarZuletzt = useRef(false);
  const { setzeAktivenIndex, aktiverIndex } = rollfokus;

  // Der Tab-Stopp folgt der Auswahl — aber NUR, wenn sie sich wirklich
  // geändert hat. Ohne die Bedingung setzte jeder Render den Rollfokus auf
  // den ausgewählten Reiter zurück und die Pfeiltasten hätten keine Wirkung
  // mehr, sobald die Elternkomponente aus einem anderen Grund neu rendert.
  const letzterAktiv = useRef(aktiv);
  useEffect(() => {
    if (letzterAktiv.current === aktiv) return;
    letzterAktiv.current = aktiv;
    const i = items.findIndex((it) => it.id === aktiv);
    if (i >= 0) setzeAktivenIndex(i);
  }, [aktiv, items, setzeAktivenIndex]);

  // Den Fokus dem Rollfokus nachführen — ausschliesslich nach einem
  // Tastendruck, s. Kopfkommentar.
  useEffect(() => {
    if (!tasteWarZuletzt.current) return;
    tasteWarZuletzt.current = false;
    knoepfe.current[aktiverIndex]?.focus();
  }, [aktiverIndex]);

  return (
    <div role="tablist" className={`k-tabs k-tabs--${size}`} {...rest}>
      {items.map((item, index) => {
        const gewaehlt = item.id === aktiv;
        return (
          <button
            key={item.id}
            ref={(el) => {
              knoepfe.current[index] = el;
            }}
            type="button"
            role="tab"
            aria-selected={gewaehlt}
            tabIndex={rollfokus.tabIndexFuer(index)}
            disabled={item.disabled ?? false}
            className={`k-tab${gewaehlt ? ' k-tab--aktiv' : ''} k-uebergang-schnell`}
            onClick={() => {
              // Beides, und in dieser Reihenfolge: der Rollfokus muss dem
              // Klick folgen, sonst zeigt der Tab-Stopp danach auf einen
              // anderen Reiter als die Auswahl.
              setzeAktivenIndex(index);
              onChange(item.id);
            }}
            onKeyDown={(e) => {
              tasteWarZuletzt.current = true;
              rollfokus.onKeyDown(e, index);
            }}
            {...(item.testid !== undefined ? { 'data-testid': item.testid } : {})}
          >
            {item.icon !== undefined && <KIcon name={item.icon} size={14} />}
            <span>{item.label}</span>
          </button>
        );
      })}
    </div>
  );
}
