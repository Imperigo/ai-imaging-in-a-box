import { useEffect, useRef, useState, type ComponentProps } from 'react';
import { KButton, KIcon, KTooltip } from '@kosmo/ui';
import { kuerzel } from './tastennamen';
import './NaviInsel.css';

/**
 * **Die Navi-Insel** — U25 Phase 5a, Owner-Entscheid I1 vom 01.10.2026
 * (`docs/U25-NUR-INSEL-SPEZ.md` §1): *«Sichtbare Knöpfe Zoom, Einpassen,
 * Vollbild → kleine Navi-Insel unten rechts: −, %, +, Einpassen, Vollbild»*.
 *
 * **Wozu.** Für das iPad ohne Tastatur und für Menschen ohne Maus: Mausrad,
 * `+`/`-` und `Home` gehen weiter, aber wer sie nicht hat, brauchte bisher die
 * klassische Oberfläche («manuell»). Diese Insel steht in der 3D-Ansicht und im
 * Grundriss, immer — sie hängt nicht an `designOberflaeche`.
 *
 * **Was sie ersetzt.** Die Zoom-Leiste unten mittig (`ViewportChrome.tsx`) und
 * die Nav-Leiste mit Orbit/Pan/Zoom/Einpassen (`NavLeiste.tsx`), beide gelöscht.
 * Die Kennungen ziehen mit um (`viewport-zoom-minus|plus|prozent`,
 * `viewport-vollbild`, `nav-fit`). **Orbit/Pan/Zoom als Umschalter für die linke
 * Maustaste entfallen** — I1 nennt sie nicht, die Gesten bleiben (Maustasten,
 * Leertaste, zwei Finger).
 *
 * **Warum innerhalb der Fläche und nicht als fixe Insel am Fensterrand.** Zwei
 * Gründe, beide gemessen: In der Doppelansicht hat jede Fläche ihren eigenen
 * Zoom — eine einzige Insel müsste raten, welche gemeint ist. Und «Vollbild»
 * zeigt nur diese Fläche (`requestFullscreen` auf ihr): Alles ausserhalb
 * verschwindet, die Insel muss also IN der Fläche stehen, sonst gäbe es keinen
 * Weg zurück.
 *
 * **Wo sie steht.** 44 px über dem unteren Rand (über der Statusleiste von «manuell»,
 * die 12..42 px belegt; die AUSTAUSCH-Pille liegt ohnehin mittig und damit weit
 * links vom Platz dieser Insel) und 88 px vom rechten (links neben dem Eck-Orb von
 * Kosmo, 14..74 px). Gemessen bei 1400×900 und 1024×768, Kosmo-Panel offen und
 * geschlossen: keine Überschneidung mit einem Bedienelement oder dem Panel
 * (`e2e/v-navi-insel.spec.ts`).
 *
 * Rein darstellend: Zoom, Einpassen und Vollbild-Wunsch kommen als Funktionen
 * von aussen — in 3D aus `Viewport3D.tsx` (camera-controls), im Plan aus
 * `PlanView.tsx` (der Gleiter, `plan-bedienung/zoom-gleiter.ts`). Kein zweiter
 * Rechenweg.
 */

export type NaviAnsicht = '3d' | '2d';

/** Zoom-Prozent der 3D-Ansicht relativ zur beim Mount gespeicherten
 *  Ausgangsdistanz (100 % = Ausgangslage). `distanzAktuell`/`distanzStart`
 *  sind camera-controls-Distanzen (Meter) — kleiner werdende Distanz = grösserer
 *  Prozentwert. Ungültige Distanzen fallen ehrlich auf 100 %, nicht auf NaN. */
export function zoomProzent(distanzAktuell: number, distanzStart: number): number {
  if (!(distanzAktuell > 0) || !(distanzStart > 0)) return 100;
  return Math.round((distanzStart / distanzAktuell) * 100);
}

/** Zoom-Prozent des Grundrisses: Massstab (px je mm) im Verhältnis zum Massstab
 *  des letzten Einpassens (100 % = so, wie eingepasst). */
export function planZoomProzent(massstab: number, bezugMassstab: number): number {
  if (!(massstab > 0) || !(bezugMassstab > 0)) return 100;
  return Math.round((massstab / bezugMassstab) * 100);
}

export interface NaviInselProps {
  /** Welche Fläche — bestimmt Kennung, Sprechtext und die Hilfe an den Knöpfen. */
  readonly ansicht: NaviAnsicht;
  /** Zoom in Prozent, bezogen auf die Ausgangslage dieser Fläche (100 = so, wie sie geöffnet/eingepasst wurde). */
  readonly prozent: number;
  readonly onKleiner: () => void;
  readonly onGroesser: () => void;
  readonly onEinpassen: () => void;
  readonly onVollbild: () => void;
  readonly vollbildAktiv: boolean;
}

/** Eine Zeile Hilfe je Fläche: was der Mensch mit Maus/Tastatur stattdessen täte. */
const HILFE: Record<NaviAnsicht, { kleiner: string; groesser: string; einpassen: string }> = {
  '3d': {
    kleiner: 'Verkleinern — die Kamera rückt weg (Mausrad rückwärts, zwei Finger zusammen)',
    groesser: 'Vergrössern — die Kamera rückt näher (Mausrad vorwärts, zwei Finger auseinander)',
    einpassen: 'Einpassen — das Modell ins Bild holen',
  },
  '2d': {
    kleiner: 'Verkleinern — der Plan rückt weg',
    groesser: 'Vergrössern — der Plan rückt näher',
    einpassen: 'Einpassen — den Grundriss ins Bild holen',
  },
};

/** Ein Knopf der Insel: 44 px (Berührgrösse `touch`), Kreis, ruhig — die einzige Stelle mit der Berührgrösse in dieser Datei. */
function NaviKnopf(props: Omit<ComponentProps<typeof KButton>, 'size' | 'tone' | 'className'>) {
  return <KButton {...props} size="touch" tone="ghost" className="navi-insel-knopf" />;
}

export function NaviInsel({ ansicht, prozent, onKleiner, onGroesser, onEinpassen, onVollbild, vollbildAktiv }: NaviInselProps) {
  const hilfe = HILFE[ansicht];
  const imPlan = ansicht === '2d';
  // Ohne Vollbild-Schnittstelle (z. B. iPhone) gibt es nichts zu versprechen —
  // der Knopf fehlt dann ehrlich, statt ohne Wirkung dazustehen.
  const vollbildMoeglich = typeof document === 'undefined' || document.fullscreenEnabled !== false;
  return (
    <div
      className="navi-insel"
      role="toolbar"
      aria-label={imPlan ? 'Navigation im Grundriss' : 'Navigation in der 3D-Ansicht'}
      data-testid={`navi-insel-${ansicht}`}
    >
      <KTooltip text={hilfe.kleiner} {...(imPlan ? { kuerzel: kuerzel('-') } : {})}>
        <NaviKnopf
                    aria-label="Verkleinern"
          data-testid="viewport-zoom-minus"
          onClick={onKleiner}
        >
          <KIcon name="minus" size={16} />
        </NaviKnopf>
      </KTooltip>
      <span className="navi-insel-prozent" data-testid="viewport-zoom-prozent" aria-label={`Zoom ${prozent} Prozent`}>
        {prozent}%
      </span>
      <KTooltip text={hilfe.groesser} {...(imPlan ? { kuerzel: kuerzel('+') } : {})}>
        <NaviKnopf
                    aria-label="Vergrössern"
          data-testid="viewport-zoom-plus"
          onClick={onGroesser}
        >
          <KIcon name="plus" size={16} />
        </NaviKnopf>
      </KTooltip>
      <span className="navi-insel-trenner" aria-hidden="true" />
      <KTooltip text={hilfe.einpassen} {...(imPlan ? { kuerzel: kuerzel('Home') } : {})}>
        <NaviKnopf
                    aria-label="Einpassen"
          data-testid="nav-fit"
          onClick={onEinpassen}
        >
          <KIcon name="fit" size={16} />
        </NaviKnopf>
      </KTooltip>
      {vollbildMoeglich && (
        <KTooltip text={vollbildAktiv ? 'Vollbild verlassen' : 'Vollbild — nur diese Fläche, ohne den Rest der Oberfläche'}>
          <NaviKnopf
                        aria-label={vollbildAktiv ? 'Vollbild verlassen' : 'Vollbild'}
            aria-pressed={vollbildAktiv}
            data-testid="viewport-vollbild"
            onClick={onVollbild}
          >
            <VollbildZeichen verlassen={vollbildAktiv} />
          </NaviKnopf>
        </KTooltip>
      )}
    </div>
  );
}

/**
 * Das Zeichen für Vollbild — zwei Pfeile nach aussen, im Vollbild nach innen.
 * Die Sammlung (`KIcon`) kennt kein Vollbild-Zeichen; dieses hier folgt ihrer
 * Bildsprache (16er-Raster, Strich 1.75, runde Kappen, `currentColor`), damit
 * es neben `fit` (Einpassen) nicht wie ein Fremdkörper steht — und sich von
 * ihm unterscheidet: `fit` ist ein Rahmen, dieses sind Pfeile.
 */
function VollbildZeichen({ verlassen }: { verlassen: boolean }) {
  return (
    <svg
      viewBox="0 0 16 16"
      width={16}
      height={16}
      fill="none"
      stroke="currentColor"
      strokeWidth={1.75}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {verlassen ? (
        <path d="M6.5 2v4.5H2M9.5 14V9.5H14M6.5 6.5 2 2M9.5 9.5 14 14" />
      ) : (
        <path d="M9.5 2H14v4.5M6.5 14H2V9.5M14 2 9.5 6.5M2 14l4.5-4.5" />
      )}
    </svg>
  );
}

/**
 * Vollbild genau dieser Fläche — nicht «irgendein Element ist im Vollbild».
 * In der Doppelansicht (3D + Plan) fragt jede Fläche nach SICH: Steht die
 * andere im Vollbild, zeigt diese nicht «verlassen».
 *
 * `holeElement` darf bei jedem Render eine neue Funktion sein (sie wird über
 * einen Ref gelesen) und liefert das Element, das ins Vollbild geht.
 */
export function useVollbild(holeElement: () => HTMLElement | null): { aktiv: boolean; umschalten: () => void } {
  const [aktiv, setAktiv] = useState(false);
  const holeRef = useRef(holeElement);
  holeRef.current = holeElement;
  useEffect(() => {
    const abgleich = () => {
      const el = holeRef.current();
      setAktiv(el !== null && document.fullscreenElement === el);
    };
    document.addEventListener('fullscreenchange', abgleich);
    return () => document.removeEventListener('fullscreenchange', abgleich);
  }, []);
  const umschalten = () => {
    const el = holeRef.current();
    if (!el) return;
    if (document.fullscreenElement === el) {
      void document.exitFullscreen().catch(() => undefined);
    } else {
      // Verweigert der Browser (keine Nutzergeste, Richtlinie), bleibt alles
      // wie es war — der Zustand folgt allein dem `fullscreenchange`-Ereignis,
      // nie dem Klick. Kein Vollbild vortäuschen.
      void el.requestFullscreen().catch(() => undefined);
    }
  };
  return { aktiv, umschalten };
}
