import { useState, type KeyboardEvent as ReactKeyboardEvent, type SyntheticEvent } from 'react';
import { createPortal } from 'react-dom';
import { VIS_STIMMUNGEN } from '@kosmo/kernel';
import { KDialog, KTabs, KTooltip } from '@kosmo/ui';
import { BridgeBild } from './BridgeBild';
import { useVisRuntime } from './vis-runtime';
import { useVariantenBestellung, variantenZellen, type VariantenZelle } from './varianten';
import type { QaUrteil } from './varianten-diff';

/**
 * Das RASTER im Bildvergleich (Owner-Entscheid 92, Blatt 23; L24 Bildweg Varianten, E246):
 * Zeilen Standpunkte, Spalten Stimmungen, je Entwurf ein Reiter. Jede Zelle traegt ihr Bild und
 * das Pruefurteil als Punkt; ein Klick zeigt sie gross. Eine leere Zelle sagt mit einem Satz, was
 * los ist: «wartet auf Freigabe», «rechnet», «fehlgeschlagen — …».
 *
 * Steht im Koerper des Bildvergleichs (feste Hoehe, `KOERPER_H.vergleich`): die Zellen teilen
 * sich die Hoehe, das Bild passt sich ein. Hat der Varianten-Knoten noch nichts bestellt, sagt
 * das Raster genau das.
 */
const PUNKT_KLASSE: Record<QaUrteil, string> = {
  bestanden: 'vis-raster-punkt--ok',
  durchgefallen: 'vis-raster-punkt--fehl',
  'nicht-beurteilbar': 'vis-raster-punkt--neutral',
  'ohne-qa': 'vis-raster-punkt--leer',
};
const URTEIL_TEXT: Record<QaUrteil, string> = {
  bestanden: 'Prüfung bestanden',
  durchgefallen: 'Prüfung durchgefallen',
  'nicht-beurteilbar': 'nicht beurteilbar',
  'ohne-qa': 'ohne Prüfurteil',
};

export function VariantenRaster({ variantenId }: { variantenId: string }) {
  const bestellung = useVariantenBestellung((s) => s.bestellungen[variantenId]);
  const laeufe = useVisRuntime((s) => s.laeufe);
  const [reiter, setReiter] = useState<string | null>(null);
  const [gross, setGross] = useState<VariantenZelle | null>(null);

  if (!bestellung) {
    return (
      <div className="vis-raster-leer" data-testid="varianten-raster-leer">
        Noch keine Varianten bestellt — am Knoten «Varianten» bestellen.
      </div>
    );
  }
  const zellen = variantenZellen(bestellung, laeufe);
  const entwurf = reiter && bestellung.entwuerfe.some((e) => e.id === reiter) ? reiter : bestellung.entwuerfe[0]?.id ?? '';
  const zelle = (standpunkt: string, stimmung: string) =>
    zellen.find((z) => z.standpunkt === standpunkt && z.stimmung === stimmung && z.entwurf === entwurf);
  const spalten = bestellung.stimmungen.length;

  return (
    <div className="vis-raster" data-testid="varianten-raster" onPointerDown={(e) => e.stopPropagation()}>
      {bestellung.entwuerfe.length > 1 && (
        <KTabs
          size="sm"
          items={bestellung.entwuerfe.map((e) => ({ id: e.id, label: e.name, testid: `varianten-raster-reiter-${e.id}` }))}
          aktiv={entwurf}
          onChange={setReiter}
          data-testid="varianten-raster-reiter"
        />
      )}
      <div
        className="vis-raster-gitter"
        style={{ gridTemplateColumns: `minmax(0, 0.8fr) repeat(${spalten}, minmax(0, 1fr))`, gridTemplateRows: `auto repeat(${bestellung.zeilen.length}, minmax(0, 1fr))` }}
      >
        <span />
        {bestellung.stimmungen.map((m) => (
          <span key={m} className="vis-raster-kopf">
            {VIS_STIMMUNGEN[m]?.label ?? m}
          </span>
        ))}
        {bestellung.zeilen.map((standpunkt) => (
          <Zeile key={standpunkt} standpunkt={standpunkt} stimmungen={bestellung.stimmungen} zelle={zelle} onGross={setGross} />
        ))}
      </div>
      {/* Blatt 36 (Nachgang): per Portal an `document.body` wie die grosse Ansicht des Verlaufs — in der
          gezoomten Knotenebene lag der Dialog sonst nach der Ebene statt nach dem Fenster. */}
      {gross &&
        gross.jobId &&
        gross.bild &&
        typeof document !== 'undefined' &&
        createPortal(
          <div onKeyDown={(e) => halteTaste(e, () => setGross(null))} onPointerDown={halte} onClick={halte} onDoubleClick={halte} onWheel={halte}>
            <KDialog
              titel={`${gross.standpunkt} · ${VIS_STIMMUNGEN[gross.stimmung]?.label ?? gross.stimmung} · ${bestellung.entwuerfe.find((e) => e.id === gross.entwurf)?.name ?? gross.entwurf}`}
              onClose={() => setGross(null)}
              breite={900}
              data-testid="varianten-raster-gross"
            >
              <BridgeBild jobId={gross.jobId} imageName={gross.bild} alt={gross.standpunkt} className="vis-img-full" />
              {gross.urteil && <p className="vis-raster-gross-urteil">{URTEIL_TEXT[gross.urteil]}</p>}
            </KDialog>
          </div>,
          document.body,
        )}
    </div>
  );
}

/** Ereignisse aus der grossen Ansicht gehoeren ihr (nicht dem Knoten, nicht der Leinwand). */
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

function Zeile({
  standpunkt,
  stimmungen,
  zelle,
  onGross,
}: {
  standpunkt: string;
  stimmungen: readonly string[];
  zelle: (standpunkt: string, stimmung: string) => VariantenZelle | undefined;
  onGross: (z: VariantenZelle) => void;
}) {
  return (
    <>
      <KTooltip text={standpunkt} lage="unten">
        <span tabIndex={0} className="vis-raster-zeilenkopf">
          {standpunkt}
        </span>
      </KTooltip>
      {stimmungen.map((m) => {
        const z = zelle(standpunkt, m);
        const testid = `varianten-zelle-${standpunkt}-${m}`;
        if (!z) return <span key={m} className="vis-raster-zelle" data-testid={testid} />;
        if (z.zustand === 'fertig' && z.jobId && z.bild) {
          return (
            <KTooltip key={m} text={`${standpunkt} · ${VIS_STIMMUNGEN[m]?.label ?? m}: ${z.urteil ? URTEIL_TEXT[z.urteil] : 'fertig'} — Klick vergrössert`} lage="unten">
              <button type="button" className="vis-raster-zelle vis-raster-zelle--bild" data-testid={testid} data-zustand="fertig" onClick={() => onGross(z)}>
                <BridgeBild jobId={z.jobId} imageName={z.bild} alt={`${standpunkt}, ${m}`} className="vis-raster-bild" />
                {z.urteil && <span className={`vis-raster-punkt ${PUNKT_KLASSE[z.urteil]}`} data-testid={`${testid}-urteil`} data-urteil={z.urteil} />}
              </button>
            </KTooltip>
          );
        }
        return (
          <KTooltip key={m} text={z.satz} lage="unten">
            <span
              tabIndex={0}
              className={`vis-raster-zelle vis-raster-zelle--leer${z.zustand === 'fehlgeschlagen' || z.zustand === 'nicht-gesendet' ? ' vis-raster-zelle--fehl' : ''}`}
              data-testid={testid}
              data-zustand={z.zustand}
            >
              {z.zustand === 'wartet' ? 'wartet' : z.zustand === 'rechnet' ? 'rechnet' : z.zustand === 'nicht-gesendet' ? 'nicht gesendet' : 'fehlgeschlagen'}
            </span>
          </KTooltip>
        );
      })}
    </>
  );
}
