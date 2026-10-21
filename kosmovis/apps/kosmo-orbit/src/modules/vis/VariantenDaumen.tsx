import { useState, type KeyboardEvent as ReactKeyboardEvent, type SyntheticEvent } from 'react';
import { createPortal } from 'react-dom';
import { type VisGraph, type VisNode } from '@kosmo/kernel';
import { KButton, KDialog, KIcon, KTooltip, KWarteOrt } from '@kosmo/ui';
import { BridgeBild } from './BridgeBild';
import { GueteMarke, gueteZusatz } from './GueteMarke';
import { LizenzOffenMarke } from './LizenzMarke';
import { useVisRuntime } from './vis-runtime';
import {
  gewaehlteZelle,
  useVariantenBestellung,
  varianteWaehlen,
  variantenZellen,
  zellenSchluessel,
  zellenTitel,
  type VariantenZelle,
} from './varianten';
import { GROSS_BREITE } from './grossansicht';
import './varianten-daumen.css';
import './vis-grossansicht.css';

/**
 * Die Bildzeile des Varianten-Knotens (Blatt 36 «Varianten-Daumen», Owner-Wunsch «Varianten-Node
 * sollte Bildvorschauen zeigen»; Empfehlungen A–C nach dem Blatt gebaut).
 *
 * EIN Daumen (96 × 60 px), daneben Stimmung · Standpunkt, «n von N» und Blaettern ‹ ›. Zwei Daumen
 * zu 96 px passen nicht in die 184 px der Karte, und ein Streifen zum Wischen stritte mit dem Rad,
 * das die Knotenansicht zoomt. Die Zeile ist in jedem Zustand gleich hoch (`KOERPER_H.varianten`):
 * leer, wartet/rechnet, fehlgeschlagen und fertig stehen in derselben Box — die Karte springt nicht.
 *
 * Gezeigt wird nur das KI-Bild (Entscheid 117a C): das Grundbild gilt fuer alle Varianten gleich
 * und steht am Render-Knoten. «Vorschau» und «Lizenz offen» stehen am Daumen wie am Render-Bild.
 *
 * Ein Klick auf einen fertigen Daumen zeigt ihn gross; dort wird geblaettert und gewaehlt. Die Wahl
 * ist ein `vis.nodeParametrieren` (ein Rueckgaengig-Schritt) und steht im Stand fuer Kosmo und Claude.
 */
export function VariantenDaumen({ graph, node }: { graph: VisGraph; node: VisNode }) {
  const bestellung = useVariantenBestellung((s) => s.bestellungen[node.id]);
  const laeufe = useVisRuntime((s) => s.laeufe);
  const [index, setIndex] = useState<number | null>(null);
  const [gross, setGross] = useState<number | null>(null);

  if (!bestellung) {
    return (
      <div className="vis-vdaumen" data-testid="varianten-daumen" data-zustand="leer">
        <div className="vis-vdaumen-bild vis-vdaumen-bild--leer" data-testid="varianten-daumen-leer">
          Noch keine Bilder
        </div>
        <div className="vis-vdaumen-seite">
          <span className="vis-vdaumen-titel">Nach dem Bestellen hier</span>
          <span className="vis-vdaumen-zahl" />
          <Blaettern weiter={null} zurueck={null} />
        </div>
      </div>
    );
  }

  const zellen = variantenZellen(bestellung, laeufe);
  const wahl = gewaehlteZelle(node.params, bestellung, zellen);
  const wahlSchluessel = wahl ? zellenSchluessel(bestellung.nr, wahl) : '';
  const istGewaehlt = (z: VariantenZelle) => wahlSchluessel !== '' && zellenSchluessel(bestellung.nr, z) === wahlSchluessel;
  const start = wahl
    ? zellen.indexOf(wahl)
    : Math.max(
        0,
        zellen.findIndex((z) => z.zustand === 'fertig'),
      );
  const i = index !== null && index < zellen.length ? index : start;
  const z = zellen[i];
  if (!z) return null;

  const fertige = zellen.map((c, n) => (c.zustand === 'fertig' && c.jobId && c.bild ? n : -1)).filter((n) => n >= 0);
  const grossZelle = gross !== null ? zellen[gross] : undefined;
  const grossPos = gross !== null ? fertige.indexOf(gross) : -1;
  const titel = zellenTitel(z, bestellung);

  return (
    <div className="vis-vdaumen" data-testid="varianten-daumen" data-zustand={z.zustand} data-index={i}>
      <Daumen zelle={z} titel={titel} gewaehlt={istGewaehlt(z)} onGross={() => setGross(i)} />
      <div className="vis-vdaumen-seite">
        <KTooltip text={`${titel} — ${z.satz}`} lage="unten">
          <span tabIndex={0} className="vis-vdaumen-titel" data-testid="varianten-daumen-titel">
            {titel}
          </span>
        </KTooltip>
        <span className="vis-vdaumen-zahl" data-testid="varianten-daumen-zahl">
          {i + 1} von {zellen.length}
          {istGewaehlt(z) ? ' · gewählt' : ''}
        </span>
        <Blaettern zurueck={i > 0 ? () => setIndex(i - 1) : null} weiter={i < zellen.length - 1 ? () => setIndex(i + 1) : null} />
      </div>

      {grossZelle &&
        grossZelle.jobId &&
        grossZelle.bild &&
        typeof document !== 'undefined' &&
        createPortal(
          /* Per Portal an `document.body`, wie die grosse Ansicht des Verlaufs (`RenderVerlauf.tsx`): in der
           gezoomten Knotenebene richtete sich der Dialog nach der Ebene statt nach dem Fenster und lag
           ausserhalb des Bildschirms (e2e kv-varianten-daumen). Ereignisse bleiben im Dialog (`halte`). */
          <div
            onKeyDown={(e) => halteTaste(e, () => setGross(null))}
            onPointerDown={halte}
            onClick={halte}
            onDoubleClick={halte}
            onWheel={halte}
          >
            <KDialog
              titel={zellenTitel(grossZelle, bestellung)}
              onClose={() => setGross(null)}
              breite={GROSS_BREITE}
              data-testid="varianten-daumen-gross"
              fusszeile={
                <div className="vis-vdaumen-gross-knoepfe">
                  <KButton
                    size="sm"
                    tone="ghost"
                    data-testid="varianten-daumen-gross-zurueck"
                    disabled={grossPos <= 0}
                    onClick={() => {
                      const n = fertige[grossPos - 1]!;
                      setGross(n);
                      setIndex(n);
                    }}
                  >
                    ‹ Vorherige
                  </KButton>
                  <KButton
                    size="sm"
                    tone="ghost"
                    data-testid="varianten-daumen-gross-weiter"
                    disabled={grossPos < 0 || grossPos >= fertige.length - 1}
                    onClick={() => {
                      const n = fertige[grossPos + 1]!;
                      setGross(n);
                      setIndex(n);
                    }}
                  >
                    Nächste ›
                  </KButton>
                  <span className="vis-vdaumen-gross-luft" />
                  <KButton
                    size="sm"
                    data-testid="varianten-daumen-waehlen"
                    onClick={() =>
                      varianteWaehlen(graph.id, node.id, istGewaehlt(grossZelle) ? '' : zellenSchluessel(bestellung.nr, grossZelle))
                    }
                  >
                    {istGewaehlt(grossZelle) ? 'Auswahl aufheben' : 'Diese Variante wählen'}
                  </KButton>
                </div>
              }
            >
              {/* L4-14 A: so breit wie das Fenster, hoechstens so hoch wie das Fenster. */}
              <span className="vis-gross-bild-hoch vis-gross-bild-block">
                <BridgeBild
                  jobId={grossZelle.jobId}
                  imageName={grossZelle.bild}
                  alt={`${zellenTitel(grossZelle, bestellung)}${gueteZusatz(grossZelle)}`}
                  className="vis-img-full"
                />
              </span>
              <GueteMarke lauf={grossZelle} testid="varianten-daumen-gross-guete" form="zeile" />
              <LizenzOffenMarke lizenz={grossZelle.lizenz} testid="varianten-daumen-gross-lizenz-offen" />
              <p className="vis-vdaumen-gross-satz">
                Nur das KI-Bild. Das Grundbild mit Licht steht am Render-Knoten — es gilt für alle Varianten gleich.
              </p>
            </KDialog>
          </div>,
          document.body,
        )}
    </div>
  );
}

/** Ereignisse aus der grossen Ansicht gehoeren ihr — sonst liefen Tasten und Zeiger durch den React-Baum
 *  bis zum Knoten (Pfeiltasten, Auswahl) und zur Leinwand (Zoom). */
function halte(e: SyntheticEvent): void {
  e.stopPropagation();
}
/** Escape schliesst hier selbst: der Riegel oben haelt das Ereignis auch vom Horcher des Dialogs fern. */
function halteTaste(e: ReactKeyboardEvent, schliessen: () => void): void {
  e.stopPropagation();
  if (e.key === 'Escape') {
    e.preventDefault();
    schliessen();
  }
}

function Daumen({ zelle, titel, gewaehlt, onGross }: { zelle: VariantenZelle; titel: string; gewaehlt: boolean; onGross: () => void }) {
  if (zelle.zustand === 'fertig' && zelle.jobId && zelle.bild) {
    return (
      <KTooltip text={`${titel}${gueteZusatz(zelle)} — Klick zeigt das Bild gross`} lage="oben">
        <button
          type="button"
          className={`vis-vdaumen-bild vis-vdaumen-bild--fertig${gewaehlt ? ' vis-vdaumen-bild--gewaehlt' : ''}`}
          data-testid="varianten-daumen-bild"
          data-gewaehlt={gewaehlt ? 'ja' : 'nein'}
          onClick={onGross}
        >
          <BridgeBild jobId={zelle.jobId} imageName={zelle.bild} alt={`${titel}${gueteZusatz(zelle)}`} className="vis-vdaumen-img" />
          <GueteMarke lauf={zelle} testid="varianten-daumen-guete" />
          {gewaehlt && (
            <span className="vis-vdaumen-haken" data-testid="varianten-daumen-haken" aria-hidden="true">
              ✓
            </span>
          )}
          <LizenzOffenMarke lizenz={zelle.lizenz} testid="varianten-daumen-lizenz-offen" abzeichen="rechts" />
        </button>
      </KTooltip>
    );
  }
  const fehl = zelle.zustand === 'fehlgeschlagen' || zelle.zustand === 'nicht-gesendet';
  return (
    <KTooltip text={zelle.satz} lage="oben">
      <span
        tabIndex={0}
        className={`vis-vdaumen-bild vis-vdaumen-bild--leer${fehl ? ' vis-vdaumen-bild--fehl' : ''}`}
        data-testid="varianten-daumen-platz"
        data-zustand={zelle.zustand}
      >
        {fehl ? (
          zelle.zustand === 'nicht-gesendet' ? (
            'nicht gesendet'
          ) : (
            'fehlgeschlagen'
          )
        ) : (
          <KWarteOrt form="leiste" text={zelle.zustand === 'wartet' ? 'wartet' : 'rechnet'} className="vis-vdaumen-warten" />
        )}
      </span>
    </KTooltip>
  );
}

function Blaettern({ zurueck, weiter }: { zurueck: (() => void) | null; weiter: (() => void) | null }) {
  return (
    <span className="vis-vdaumen-blaettern">
      <KTooltip text="Vorherige Variante" lage="unten">
        <KButton
          size="sm"
          tone="ghost"
          aria-label="Vorherige Variante"
          data-testid="varianten-daumen-zurueck"
          disabled={!zurueck}
          onClick={() => zurueck?.()}
        >
          <KIcon name="pfeil-links" size={14} />
        </KButton>
      </KTooltip>
      <KTooltip text="Nächste Variante" lage="unten">
        <KButton
          size="sm"
          tone="ghost"
          aria-label="Nächste Variante"
          data-testid="varianten-daumen-weiter"
          disabled={!weiter}
          onClick={() => weiter?.()}
        >
          <KIcon name="pfeil-rechts" size={14} />
        </KButton>
      </KTooltip>
    </span>
  );
}
