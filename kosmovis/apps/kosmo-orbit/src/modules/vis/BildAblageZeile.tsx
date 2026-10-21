import { useEffect } from 'react';
import { KButton, melde } from '@kosmo/ui';
import { useProject } from '../../state/project-store';
import { ablageSatz, ablageSchluessel, istBlattDa, masseVon, projektBild, useBildAblage } from './bild-ablage-kern';
import { exportiereMitMeldung, sichereLauf } from './bild-ablage';
import { lizenzAblageZusatz, LIZENZ_MELDUNG_MS, type LizenzAngabe } from './varianten-diff';
import { bescheideBridgeCatch, bildAufsBlatt } from './vis-jobs';
import './vis-visual.css';

/**
 * Video-Befunde L4-16 / L3-A4 (Demolauf 16.10.2026; Blatt «Bild aufs Blatt», Teil 1): «Aufs
 * Blatt» und «Exportieren» an jedem Lauf, in der grossen Ansicht. Beide nehmen das Bild im
 * ORIGINAL — aus dem Projekt, wenn es dort gesichert ist, sonst vom Heim-PC —, nie einen
 * Bildschirmausschnitt. Darunter der Stand: wie gross, und ob es im Projekt liegt.
 *
 * Ein Bild ohne fertiges Ergebnis (Teilbild nach Abbruch, Zwischenbild) traegt `grund`: dann
 * sind beide Knoepfe aus, und der Satz sagt warum. In Visbox gibt es kein Blatt (Wirt,
 * `setzeBlattDa(false)`): dort steht nur «Exportieren».
 */
export interface AblageLauf extends LizenzAngabe {
  jobId: string;
  bild: string;
  laufNummer?: number | undefined;
  guete?: 'vorschau' | 'voll' | undefined;
}

export function BildAblageZeile({
  lauf,
  grund,
  testid,
  titel = 'Visualisierung',
  fuss = false,
}: {
  lauf: AblageLauf;
  /** Warum dieses Bild nicht aufs Blatt und nicht zum Export kann; fehlt es, geht beides. */
  grund?: string | undefined;
  /** Vorsilbe der Kennungen (`<testid>-aufs-blatt`, `-exportieren`, `-ablage-satz`). */
  testid: string;
  titel?: string;
  /** Als Fusszeile einer grossen Ansicht: Knoepfe und Satz in einer Reihe. */
  fuss?: boolean;
}) {
  const schluessel = ablageSchluessel(lauf.jobId, lauf.bild);
  const stand = useBildAblage((s) => s.stand[schluessel]);
  // Neu lesen, wenn sich das Projekt aendert (ein Bild kam dazu oder fiel weg).
  useProject((s) => s.revision);
  const imProjekt = projektBild(lauf.jobId, lauf.bild);
  const blattDa = istBlattDa();
  // Liegt es schon im Projekt (geladen, aus einer frueheren Sitzung), sagt die Zeile das, ohne
  // den Heim-PC zu fragen. Sonst holt sie es hier nach, sobald die Ansicht offen ist.
  useEffect(() => {
    if (grund || !blattDa) return;
    if (!stand && !imProjekt) void sichereLauf(lauf.jobId, lauf.bild, lauf.guete);
  }, [grund, blattDa, stand, imProjekt, lauf.jobId, lauf.bild, lauf.guete]);

  const satz = grund
    ? grund
    : imProjekt
      ? ablageSatz({ zustand: 'gesichert', assetId: imProjekt.id, masse: masseVon(imProjekt) })
      : blattDa
        ? ablageSatz(stand)
        : 'Im Original vom Heim-PC — so, wie es gerechnet ist.';

  const aufsBlatt = () => {
    const zusatz = lizenzAblageZusatz(lauf);
    void bildAufsBlatt(lauf.jobId, lauf.bild, titel, lauf)
      .then((name) =>
        melde(`Render liegt auf «${name}» — im KosmoPublish weiterschieben${zusatz}`, {
          ton: 'erfolg',
          ...(zusatz ? { dauerMs: LIZENZ_MELDUNG_MS } : {}),
        }),
      )
      .catch(bescheideBridgeCatch);
  };

  return (
    <div className={`vis-ablage-zeile${fuss ? ' vis-ablage-zeile--fuss' : ''}`} data-testid={`${testid}-ablage`}>
      <div className="vis-ablage-knoepfe">
        {blattDa && (
          <KButton size="sm" tone="accent" data-testid={`${testid}-aufs-blatt`} disabled={!!grund} onClick={aufsBlatt}>
            Aufs Blatt
          </KButton>
        )}
        <KButton
          size="sm"
          tone="quiet"
          data-testid={`${testid}-exportieren`}
          disabled={!!grund}
          onClick={() => exportiereMitMeldung(lauf.jobId, lauf.bild, lauf.laufNummer)}
        >
          Exportieren
        </KButton>
      </div>
      <div className="vis-ablage-satz" data-testid={`${testid}-ablage-satz`} data-stand={grund ? 'nicht-waehlbar' : imProjekt ? 'gesichert' : (stand?.zustand ?? 'offen')}>
        {satz}
      </div>
    </div>
  );
}
