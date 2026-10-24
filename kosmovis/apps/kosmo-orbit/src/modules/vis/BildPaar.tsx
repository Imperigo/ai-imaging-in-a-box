import type { KeyboardEvent as ReactKeyboardEvent, SyntheticEvent } from 'react';
import { createPortal } from 'react-dom';
import { KCheckbox, KDialog, KTabs, KTooltip } from '@kosmo/ui';
import { BildAblageZeile, type AblageLauf } from './BildAblageZeile';
import { BridgeBild } from './BridgeBild';
import { GueteMarke, type MitGuete } from './GueteMarke';
import { ModusMarke } from './ModusMarke';
import { FreiesBildMarke } from './FreiesBildMarke';
import {
  ANSICHT_KURZHILFE,
  ANSICHT_NAME,
  ANSICHTEN,
  GRUNDBILD_NAME,
  KI_BILD_NAME,
  type BildAnsicht,
} from './nebeneinander';
import { GROSS_BEI_FERTIG_HILFE, GROSS_BEI_FERTIG_NAME, GROSS_BREITE } from './grossansicht';
import type { GrossSchalter } from './RenderVerlauf';
import './vis-visual.css';
import './vis-grossansicht.css';

/**
 * Entscheid 117a (Blatt 35) — KI-Bild und Grundbild gross. Geoeffnet mit einem Klick auf das Bild am Render-Knoten,
 * wenn der Lauf ein Grundbild mitgebracht hat. Hier steht der Umschalter «nebeneinander · nur KI · nur Grundbild»
 * (`KTabs`, Vorgabe nebeneinander); die Wahl ist der Knoten-Parameter `bildAnsicht` und gilt damit auch fuer das Bild
 * am Knoten.
 *
 * WARUM DER UMSCHALTER HIER UND NICHT IM KNOTEN: eine Reiterzeile mit drei Reitern bricht im Koerper um und liesse
 * den Knoten wachsen (Vorgaben des UI-Workers, Probe kv-b5). Seit Entscheid 119 ist der Koerper des Render-Knotens
 * 196 px breit (vorher 184): «nebeneinander» steht damit schon am Knoten, je Bild 96 px (`wirksameAnsicht`); bei
 * 184 px fiel es auf das KI-Bild zurueck. Gross stehen beide gleich gross nebeneinander, und diese Ansicht bleibt.
 *
 * L4-14 (Blatt «Grossansicht und Vergleich» A): so breit, wie das Fenster erlaubt (`GROSS_BREITE`), jedes Bild
 * hoechstens so hoch wie das Fenster — vorher 960 px fuer beide zusammen.
 *
 * Das Gitter waechst nicht unter 96 px je Bild: in einem sehr schmalen Fenster rueckt das Grundbild unter das KI-Bild,
 * statt beide zu stauchen. Per Portal an `document.body` wie die grosse Ansicht des Verlaufs — ausserhalb der
 * gezoomten Knotenebene.
 */

function halte(e: SyntheticEvent): void {
  e.stopPropagation();
}

export function BildPaarGross({
  lauf,
  ablage,
  jobId,
  ki,
  grundbild,
  ansicht,
  onAnsicht,
  onClose,
  schalter,
}: {
  /** Fuer die Vorschau-Marke am KI-Bild (Entscheid 104a). */
  lauf: MitGuete;
  /** L4-16/L3-A4: «Aufs Blatt» und «Exportieren» fuer das KI-Bild dieses Laufs; fehlt es, keine Zeile. */
  ablage?: AblageLauf;
  jobId: string;
  ki: string;
  grundbild: string;
  ansicht: BildAnsicht;
  onAnsicht: (a: BildAnsicht) => void;
  onClose: () => void;
  /** L4-14 B: «bei fertig gross oeffnen» (Knoten-Parameter `grossBeiFertig`). */
  schalter?: GrossSchalter;
}) {
  if (typeof document === 'undefined') return null;
  const zeigeKi = ansicht !== 'nur-grundbild';
  const zeigeGrund = ansicht !== 'nur-ki';
  return createPortal(
    <div
      onPointerDown={halte}
      onClick={halte}
      onKeyDown={(e: ReactKeyboardEvent) => {
        // Die Taste endet hier (sonst liefe sie bis zur Leinwand); Escape schliesst darum hier selbst —
        // der Horcher des Dialogs am `document` bekaeme sie nicht mehr.
        e.stopPropagation();
        if (e.key === 'Escape') {
          e.preventDefault();
          onClose();
        }
      }}
    >
      <KDialog titel="KI-Bild und Grundbild" onClose={onClose} breite={GROSS_BREITE} data-testid="render-bildpaar-gross">
        <KTooltip text={ANSICHT_KURZHILFE} lage="unten">
          <span className="vis-bildpaar-umschalter">
            <KTabs
              size="sm"
              items={ANSICHTEN.map((a) => ({ id: a, label: ANSICHT_NAME[a], testid: `render-ansicht-${a}` }))}
              aktiv={ansicht}
              onChange={(id) => onAnsicht(id as BildAnsicht)}
              data-testid="render-ansicht"
            />
          </span>
        </KTooltip>
        {schalter && (
          <KTooltip text={GROSS_BEI_FERTIG_HILFE} lage="unten">
            <span className="vis-gross-schalter vis-bildpaar-schalter">
              <KCheckbox
                size="sm"
                label={GROSS_BEI_FERTIG_NAME}
                checked={schalter.an}
                onChange={(ev) => schalter.setzen(ev.currentTarget.checked)}
                data-testid="render-gross-bei-fertig"
              />
            </span>
          </KTooltip>
        )}
        <div className="vis-bildpaar-gitter vis-gross-bild-hoch" data-testid="render-bildpaar" data-ansicht={ansicht}>
          {zeigeKi && (
            <figure className="vis-bildpaar-kachel" data-testid="render-bildpaar-ki">
              <span className="vis-bildpaar-bild">
                <BridgeBild jobId={jobId} imageName={ki} alt={KI_BILD_NAME} className="vis-img-full" />
                {/* Die Vorschau-Marke gehoert nur zum KI-Bild — das Grundbild rechnet Blender voll. */}
                <div className="vis-marken-leiste">
                  <GueteMarke lauf={lauf} testid="render-bildpaar-guete-marke" />
                  <ModusMarke lauf={lauf} testid="render-bildpaar-modus-marke" />
                  <FreiesBildMarke lauf={lauf} testid="render-bildpaar-freies-bild-marke" />
                </div>
              </span>
              <figcaption className="vis-bildpaar-text">
                <strong>{KI_BILD_NAME}</strong> · Entwurf
              </figcaption>
            </figure>
          )}
          {zeigeGrund && (
            <figure className="vis-bildpaar-kachel" data-testid="render-bildpaar-grundbild">
              <span className="vis-bildpaar-bild">
                <BridgeBild jobId={jobId} imageName={grundbild} alt={GRUNDBILD_NAME} className="vis-img-full" />
              </span>
              <figcaption className="vis-bildpaar-text">
                <strong>{GRUNDBILD_NAME}</strong> · gerendert, Sonne und Schatten echt
              </figcaption>
            </figure>
          )}
        </div>
        {ablage && <BildAblageZeile lauf={ablage} testid="render-bildpaar-gross" />}
      </KDialog>
    </div>,
    document.body,
  );
}
