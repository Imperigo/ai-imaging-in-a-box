import type { ReactNode } from 'react';
import { KIcon } from './icons';
import { KTabs, type KTabItem } from './tabs';
import { KTooltip } from './tooltip';

/**
 * KPanelZweiStufen (v0.8.1 Welle 4 / Paket P5b — «Zwei-Stufen-Popups»,
 * `docs/V081-SPEZ.md` §2.1 «C» / §2.2 / §8 Sanktion 5) — die neue kosmo-ui-
 * Komponente, die die zwei bisherigen Halbmuster ersetzt: KennzahlenPanel
 * (Kopf-immer + faltbarer Körper, `kp-kopf-knopf`) und DrawPanel
 * (KButton-Tabs, `draw-tab-*`). Anatomie exakt nach §2.2:
 *
 *   Kopf (IMMER sichtbar) — Titel (Mono 12px/600/.14em/uppercase, wie
 *   `DockPanel.tsx`s `.k-dock-panel-titel`) + GENAU EINE Kernkennzahl (nie
 *   mehr, Gesetz 2 «eine Hauptthese pro View») + ein Umschalt-Knopf
 *   (kompakt ↔ offen).
 *
 *   KTabs-Durchklick-Menü — nur sichtbar in der Stufe `'offen'`, nur
 *   gerendert, wenn mehr als ein Tab existiert (ein einzelner Tab wäre ein
 *   bedeutungsloser Ein-Punkt-Umschalter, s. `KennzahlenPanel.tsx`, das
 *   bewusst mit EINEM Tab migriert — Architektur bleibt trotzdem vorhanden,
 *   nur ungenutzt).
 *
 *   Körper — der Inhalt des aktuell gewählten Tabs, nur in Stufe `'offen'`.
 *
 * **Nie-Scroll-Gebot (§2.3, bindend für DIESE Komponente selbst)**: keine
 * Zeile hier setzt `overflow:auto`/`overflow:scroll` — weder auf dem
 * Kopf/Tabs-Streifen noch auf `.k-panel-zwei-koerper` (s. `aura.css`). Passt
 * ein Tab-Inhalt nicht in eine Stufe, ist die Antwort laut Spec eine WEITERE
 * Tab-Seite, nicht ein Scroll-Container innerhalb dieser Komponente (der
 * äussere `.k-dock-panel-inhalt`/`dp-dialog--scroll`-Rahmen bleibt
 * unverändert — Abbau dort ist P5c-Scope, s. Abschlussbericht).
 *
 * Zwei Stufen (`PanelOverride.stufe` aus `dock-kern.ts`, P5a-Fundament):
 *   - `'kompakt'` — nur der Kopf (Kernkennzahl reicht als Information).
 *   - `'offen'`   — Kopf + Tabs + Körper (Viertelflächen-Ziel, `dock-kern.ts`
 *                   `zielKompakt()`).
 * Diese Komponente selbst kennt den Dock-Solver NICHT — sie ist reine
 * Präsentation (wie `KTabs`/`KKeyValue`); die Verdrahtung zum Store lebt in
 * `apps/kosmo-orbit/src/state/dock-zustand.ts` (`stufeUmschalten()`-Helfer)
 * und in den migrierten Panels selbst.
 */

export interface KPanelZweiStufenTab extends KTabItem {
  /** Inhalt dieser Tab-Seite — nur gerendert, solange sie aktiv ist UND die
   *  Stufe `'offen'` ist (kein Doppel-Mount aller Tabs gleichzeitig). */
  inhalt: ReactNode;
}

export type KPanelZweiStufenStufe = 'kompakt' | 'offen';

export interface KPanelZweiStufenProps {
  /** Panel-Titel (Kopf, Mono-Uppercase-Rezept — s. Kopfkommentar). */
  titel: string;
  /** GENAU EINE Kernkennzahl (§2.2) — nie ein zweites Zahlen-/Text-Element
   *  daneben stopfen, dafür ist die Kopfzeile nicht gedacht. */
  kernkennzahl: ReactNode;
  stufe: KPanelZweiStufenStufe;
  /** Klick auf den Kopf (ausserhalb der Tab-Leiste) schaltet die Stufe um —
   *  die Komponente selbst entscheidet NICHT, wie herum (kompakt→offen oder
   *  umgekehrt), das macht der Aufrufer (s. `stufeUmschalten()`). */
  onStufeUmschalten: () => void;
  tabs: readonly KPanelZweiStufenTab[];
  aktiverTab: string;
  onTabWechseln: (id: string) => void;
  className?: string;
  'data-testid'?: string;
}

export function KPanelZweiStufen({
  titel,
  kernkennzahl,
  stufe,
  onStufeUmschalten,
  tabs,
  aktiverTab,
  onTabWechseln,
  className,
  ...rest
}: KPanelZweiStufenProps) {
  const offen = stufe === 'offen';
  const aktiverEintrag = tabs.find((t) => t.id === aktiverTab) ?? tabs[0];
  const testid = rest['data-testid'];
  const klassen = ['k-panel-zwei', `k-panel-zwei--${stufe}`, className].filter(Boolean).join(' ');

  return (
    <div className={klassen} {...rest}>
      {/* P-KURZHILFE-EINZUG (09.09.2026): hier stand ein natives `title=`.
          Das Designsystem war damit die einzige Stelle, die den Baustein
          vorschreibt, den es selbst nicht benutzte — und eine Regel, die ihr
          eigener Urheber bricht, ist keine Regel. Die erste eingezogene
          Stelle ist darum diese. */}
      <KTooltip text={offen ? 'Kompakt anzeigen' : 'Aufklappen'}>
        <button
          type="button"
          className="k-panel-zwei-kopf"
          onClick={onStufeUmschalten}
          aria-expanded={offen}
          {...(testid !== undefined ? { 'data-testid': `${testid}-umschalten` } : {})}
        >
          <span className="k-panel-zwei-titel">{titel}</span>
          <span className="k-panel-zwei-kernkennzahl">{kernkennzahl}</span>
          <span className="k-panel-zwei-fuell" />
          <KIcon name={offen ? 'minus' : 'plus'} size={14} className="k-panel-zwei-toggle-icon" />
        </button>
      </KTooltip>
      {offen && aktiverEintrag !== undefined && (
        <>
          {tabs.length > 1 && (
            <div className="k-panel-zwei-tabreihe">
              <KTabs
                items={tabs}
                aktiv={aktiverTab}
                onChange={onTabWechseln}
                size="sm"
                {...(testid !== undefined ? { 'data-testid': `${testid}-tabs` } : {})}
              />
            </div>
          )}
          <div className="k-panel-zwei-koerper">{aktiverEintrag.inhalt}</div>
        </>
      )}
    </div>
  );
}
