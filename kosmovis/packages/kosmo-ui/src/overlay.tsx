import {
  cloneElement,
  useRef,
  useState,
  type MouseEvent as ReactMouseEvent,
  type ReactElement,
  type ReactNode,
} from 'react';
import type { KIconName } from './icons';
import { KIcon } from './icons';
import { useFokusFalle } from './fokusfalle';
import { useOverlaySchliessen } from './overlay-schliessen';
import { useHerkunft } from './herkunft';
import { zEbeneLeiter } from './tokens';

/**
 * KMenu + KDialog (W0, UI-KONZEPT-065 §3) — die zwei Overlay-Bausteine.
 * KMenu ersetzt Link-Reihen (ANSICHT/EXPORT/EBENEN) durch Dropdowns; KDialog
 * ersetzt Ad-hoc-Popups. Beide teilen sich Esc-/Aussenklick-Verhalten.
 *
 * `useFokusFalle` (Tab-Zyklus innerhalb eines offenen Overlays) ist seit
 * P-g / Tastatur-Rückgrat nach `fokusfalle.ts` ausgelagert und von dort
 * exportiert (byte-gleicher Umzug, s. dortiger Kopfkommentar) — hier nur
 * noch importiert.
 *
 * **Schichtung 20a (21.09.2026):** Es gibt EIN Haus-Gesetz fürs Schliessen,
 * `useOverlaySchliessen`. Beide Bausteine hier hielten bis heute eine eigene
 * Abschrift davon (je ein `document`-`keydown`/`mousedown`-Paar) — genau die
 * vier «eigener Handler statt gemeinsames Gesetz»-Fälle aus Frage 20. Sie
 * rufen jetzt das Gesetz. `KDialog` bestellt es als `modal: true`, bekommt
 * damit Escape, Fokusfalle und Fokusrückgabe in einem und trägt sich in den
 * Modal-Stapel ein (Escape schliesst nur die oberste Fläche, Entscheid 24a).
 */

// ── KMenu ───────────────────────────────────────────────────────────

export type KMenuItem =
  | 'trenner'
  | {
      id: string;
      label: string;
      icon?: KIconName;
      /** Kurztaste, rechtsbündig in Mono dargestellt (z.B. "⌘K"). */
      kuerzel?: string;
      /** Rot markiert (destruktive Aktion). */
      gefahr?: boolean;
      disabled?: boolean;
      testid?: string;
    };

interface KMenuTriggerProps {
  onClick?: (e: ReactMouseEvent<HTMLElement>) => void;
  'aria-haspopup'?: boolean | 'menu';
  'aria-expanded'?: boolean;
}

export interface KMenuProps {
  /** Der Bedienknopf — bekommt aria-haspopup/-expanded und einen Klick-
   * Handler per `cloneElement` angeklont (kein Wrapper-Element nötig). */
  trigger: ReactElement<KMenuTriggerProps>;
  items: readonly KMenuItem[];
  onSelect: (id: string) => void;
  'data-testid'?: string;
}

export function KMenu({ trigger, items, onSelect, ...rest }: KMenuProps) {
  const [offen, setOffen] = useState(false);
  const wrapRef = useRef<HTMLDivElement | null>(null);
  const menuRef = useRef<HTMLDivElement | null>(null);
  useFokusFalle(menuRef, offen);

  // Das Haus-Gesetz statt der eigenen Abschrift. `esc`/`aussenklick` an
  // `offen` gebunden — exakt die bisherige Lebensdauer der beiden Horcher.
  // KEIN `modal`: ein Menü ist keine modale Fläche, es dunkelt nichts ab und
  // gehört nicht in den Stapel, der Escape auf die oberste Fläche begrenzt.
  useOverlaySchliessen(wrapRef, () => setOffen(false), { esc: offen, aussenklick: offen });

  // `trigger` ist beliebig (KButton, ein natives <button>, …) — dessen
  // konkreter Props-Typ ist mit `cloneElement` nicht variantensicher zu
  // vereinen (das generische `onClick` kollidiert kontravariant mit
  // spezifischeren Handlern wie `MouseEventHandler<HTMLButtonElement>`).
  // Der Cast ist bewusst auf diese eine Stelle begrenzt; die ÖFFENTLICHE
  // Prop bleibt oben sauber typisiert (`ReactElement<KMenuTriggerProps>`).
  const triggerProps = trigger.props as KMenuTriggerProps;
  const geklonterTrigger = cloneElement(trigger as ReactElement<Record<string, unknown>>, {
    'aria-haspopup': 'menu',
    'aria-expanded': offen,
    onClick: (e: ReactMouseEvent<HTMLElement>) => {
      triggerProps.onClick?.(e);
      setOffen((o) => !o);
    },
  });

  return (
    <div className="k-menu-wrap" ref={wrapRef} {...rest}>
      {geklonterTrigger}
      <div
        role="menu"
        ref={menuRef}
        className={`k-menu k-uebergang-schnell${offen ? ' offen' : ''}`}
        aria-hidden={!offen}
      >
        {items.map((item, i) =>
          item === 'trenner' ? (
            // Trenner tragen keine eigene Identität — der Index ist hier der Schlüssel.
            <div key={`trenner-${i}`} role="separator" className="k-menu-trenner" />
          ) : (
            <button
              key={item.id}
              type="button"
              role="menuitem"
              disabled={item.disabled ?? false}
              tabIndex={offen ? 0 : -1}
              className={`k-menu-item${item.gefahr ? ' k-menu-item--gefahr' : ''}`}
              onClick={() => {
                onSelect(item.id);
                setOffen(false);
              }}
              {...(item.testid !== undefined ? { 'data-testid': item.testid } : {})}
            >
              {item.icon !== undefined && <KIcon name={item.icon} size={14} />}
              <span className="k-menu-item-label">{item.label}</span>
              {item.kuerzel !== undefined && <span className="k-menu-item-kuerzel">{item.kuerzel}</span>}
            </button>
          ),
        )}
      </div>
    </div>
  );
}

// ── KDialog ─────────────────────────────────────────────────────────

export interface KDialogProps {
  titel: string;
  onClose: () => void;
  children: ReactNode;
  /** Rechtsbündige Aktionen, z.B. Abbrechen/Bestätigen-Knöpfe. */
  fusszeile?: ReactNode;
  breite?: number;
  /** Überschreibt den Default-Stapelwert (215) — z.B. wenn ein Aufrufer über
   *  einem ANDEREN, bereits gestapelten Overlay dieser App sitzen muss (s.
   *  Kopfkommentar). */
  zIndex?: number;
  'data-testid'?: string;
}

/** Gestalteter Dialog — Kopf in Plakat-Versalien + Schliessen-KIcon +
 * Hairline; Scrim (`.k-dialog-scrim`, bestehend) + Höhen-/Umbruch-Regeln
 * (`.k-dialog`, bestehend) werden wiederverwendet, nicht neu erfunden.
 * Esc + Scrim-Klick schliessen. KEINE 45°-Ecke (die gehört den Karteikarten).
 *
 * **`zIndex` (Default 215)**: `.k-dialog-scrim` selbst trägt bewusst KEIN
 * `z-index` (aura.css) — jeder bisherige Scrim-Konsument in dieser App setzt
 * es von Hand inline, in einer gewachsenen Stapel-Reihenfolge (`Kurzbefehle`
 * 205 < `WerkzeugSetup` 220 < `AppDeinstallieren` 230 < `Einstellungen` 250
 * < `meldungen`/`KBestaetigung` 900). `KDialog` war bisher der
 * EINZIGE Scrim-Konsument OHNE eigenes `z-index` — von einer tief
 * verschachtelten Stelle aus gerendert (z.B. `DockRegeln.tsx`, selbst über
 * `createPortal` nach `document.body`), verlor sein Scrim gegen JEDES
 * andere `z-index>0`-Element der App (Dock-Panels z14+, Boden-Dock z108,
 * …) — sichtbar unsichtbar: `getBoundingClientRect()`/`toBeVisible()`
 * meldeten eine volle Viewport-Box, aber im Screenshot war nichts zu sehen.
 * 215 reiht sich zwischen `Kurzbefehle` und `WerkzeugSetup` ein.
 *
 * **Berichtigung 26.08.2026** (`docs/BEFUND-KOMMENTARDRIFT-2026-08-26.md`):
 * hier stand bis heute `Kurzbefehle` 205 < `meldungen`/`KBestaetigung`
 * **210** < `WerkzeugSetup` 220 < …, und der letzte Satz «215 reiht sich
 * zwischen `meldungen` und `WerkzeugSetup` ein». Das war beim Schreiben
 * dieses Kommentars (14.07.2026, Commit `87c3e658`) richtig — reine
 * DRIFT: `meldungen.tsx`s Scrim wurde in `f8f041e0` (21.07.2026, E-K5)
 * auf **900** angehoben (dortiger Kommentar, `meldungen.tsx:155-178`: ein
 * höheres `z-index` allein löste einen `#root`-Stacking-Bug NICHT, `900`
 * blieb als Sicherheitsmarge stehen), ohne dass diese Stelle je
 * nachgezogen wurde. `meldungen`/`KBestaetigung` steht damit NICHT mehr
 * zwischen `Kurzbefehle` und `WerkzeugSetup`, sondern über der ganzen
 * übrigen Familie — s. korrigierte Reihenfolge und der letzte Satz oben. */
export function KDialog({ titel, onClose, children, fusszeile, breite = 560, zIndex = zEbeneLeiter.modal + 20, ...rest }: KDialogProps) {
  const boxRef = useRef<HTMLDivElement | null>(null);
  // KDialog ist immer "offen", solange gemountet (kein internes offen/zu wie
  // KMenu) — Escape, Falle und Fokusrückgabe sind darum durchgehend aktiv,
  // gebunden an die Lebensdauer der Komponente. `aussenklick: false`: der
  // Klick daneben läuft hier über den Scrim (`onClick={onClose}` unten, ein
  // ECHTES `click` auf einer echten Fläche), nicht über einen globalen
  // `mousedown`-Horcher — sonst schlösse ein Mausdruck, der in der Box
  // beginnt und ausserhalb endet, den Dialog mit.
  useOverlaySchliessen(boxRef, onClose, { modal: true, aussenklick: false });
  // Owner C5 (01.10.2026): das Fenster wächst aus dem Knopf, der es geöffnet hat.
  useHerkunft(boxRef);

  return (
    <div
      role="dialog"
      aria-modal
      aria-label={titel}
      className="k-dialog-scrim"
      onClick={() => onClose()}
      style={{ zIndex }}
      {...rest}
    >
      <div
        ref={boxRef}
        className="k-dialog-box k-dialog k-aus-ausloeser"
        onClick={(e) => e.stopPropagation()}
        style={{ width: `min(${breite}px, calc(100vw - 48px))` }}
      >
        <div className="k-dialog-kopf">
          <span className="k-titel k-dialog-kopf-titel">{titel}</span>
          <button
            type="button"
            aria-label="Schliessen"
            className="k-dialog-kopf-schliessen"
            onClick={() => onClose()}
          >
            <KIcon name="schliessen" size={16} />
          </button>
        </div>
        <div className="k-dialog-koerper">{children}</div>
        {fusszeile !== undefined && <div className="k-dialog-fuss">{fusszeile}</div>}
      </div>
    </div>
  );
}
